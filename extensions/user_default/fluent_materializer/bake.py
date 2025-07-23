import threading

import bpy
from bpy_types import Operator

from . import tasks_queue
from .Tools.helper import *


class FLUENT_OT_BakeMaps(Operator):
    "Bake your PBR maps\nCTRL+SHIFT+ALT for help"
    bl_idname = "fluent.bakepbrmaps"
    bl_label = "Bake PBR maps"
    bl_options = {'REGISTER', 'UNDO'}

    _th = None
    objects = None

    @classmethod
    def poll(cls, context):
        props = bpy.context.scene.FluentShaderProps

        if not props.bake_make_selected_to_active and not bpy.context.active_object:
            cls.poll_message_set("No object selected")
            return False

        if props.bake_make_selected_to_active and len(context.selected_objects) < 2:
            cls.poll_message_set("Baking high to low requires at least two selected objects")
            return False

        if not len(bpy.context.active_object.data.materials):
            cls.poll_message_set("The active object must have a material")
            return False

        if props.bake_in_image and '_' in bpy.context.active_object.name:
            cls.poll_message_set("The object name contains underscore. Please, remove it.")
            return False

        if props.bake_combine_channels:
            missing_bake_channel_name = checkMissingCombineChannel()
            if missing_bake_channel_name is not None:
                cls.poll_message_set(
                    "You selected combine RGB, but map '%s' is not enabled" % missing_bake_channel_name)
                return False

        return True

    def invoke(self, context, event):
        if event.ctrl and event.shift and event.alt:
            bpy.context.window_manager.popup_menu(
                make_oops(['This function bakes what you designed with Fluent Materializer.',
                           'The baking function bakes what is connected to the principled BSDF, which is connected to the material output.',
                           'Be sure the principled BSDF is connected to the material output, then select your object and bake.',
                           'The program will try to save the images in a folder called "Textures" next to the blend file,',
                           'if it can\'t, you have to save your files manualy',
                           'The image name follows this pattern : ObjectName_MAP']), title="About PBR baking",
                icon='INFO')
            return {'FINISHED'}

        self.objects = bpy.context.selected_objects
        props = context.scene.FluentShaderProps
        selected_to_active = props.bake_make_selected_to_active
        # Vérification
        if not self.objects or len(bpy.context.selected_objects) == 0:
            bpy.context.window_manager.popup_menu(
                make_oops(['No active object.']),
                title="Problem detected",
                icon='INFO'
            )

            return {'FINISHED'}

        for obj in self.objects:
            if obj.type != 'MESH':
                bpy.context.window_manager.popup_menu(
                    make_oops(['You try to bake a non mesh thing.']),
                    title="Problem detected",
                    icon='INFO'
                )
                return {'FINISHED'}

            if not len(obj.data.materials):
                bpy.context.window_manager.popup_menu(
                    make_oops(['No material for the object.']),
                    title="Problem detected",
                    icon='INFO'
                )

            if not len(obj.data.uv_layers):
                bpy.context.window_manager.popup_menu(
                    make_oops(['No UV map detected.', 'Unwrap the model before to bake.']),
                    title="Problem detected",
                    icon='INFO'
                )
                return {'FINISHED'}

        # bake high to low
        if selected_to_active and len(bpy.context.selected_objects) < 2:
            bpy.context.window_manager.popup_menu(
                make_oops(['Select to active option but less than 2 objects selected.']),
                title="Problem detected",
                icon='INFO'
            )

            return {'FINISHED'}

        try:
            bpy.ops.wm.save_mainfile()
        except:
            bpy.context.window_manager.popup_menu(
                make_oops(["Please save your Blender file before baking"]),
                icon="ERROR",
                title="Save your Blender file"
            )
            return {'FINISHED'}

        self._th = threading.Thread(
            target=self.execute_bake_process,
            args=(
                context,
            )
        )

        props.baking_error = ""
        props.is_baking = True
        self._th.start()

        return {'FINISHED'}

    def execute_bake_process(self, context):
        script_file = os.path.dirname(os.path.realpath(__file__)) + '/external_render.py'
        current_blend_file = bpy.data.filepath

        prefs = bpy.context.preferences
        cprefs = prefs.addons['cycles'].preferences
        compute_device_type = cprefs.compute_device_type
        enabled_devices = []
        for device in cprefs.devices:
            if device.use:
                enabled_devices.append(device.id)

        enabled_devices_string = ';'.join(enabled_devices)

        properties = bpy.context.scene.FluentShaderProps
        bake_settings = []
        bake_settings.append(build_string_setting('map_size'))

        bake_image_name = 'None'
        if properties.bake_in_image:
            # Need to print to prevent Blender violation crash ??!! ....
            print('s')
            bake_image_name = properties.bake_in_image.name.split('_')[0]
            properties.bake_in_image_path = properties.bake_in_image.filepath_raw
            # properties.bake_in_image.pack()
            all_maps = find_all_maps_by_image(properties.bake_in_image.name)
            for m in all_maps:
                m.pack()

        bake_settings.append('bake_in_image:'+bake_image_name)
        bake_settings.append(build_string_setting('bake_margin'))
        bake_settings.append(build_string_setting('bake_sample'))
        bake_settings.append(build_string_setting('bake_custom_colorspace'))
        bake_settings.append(build_string_setting('bake_make_selected_to_active'))
        bake_settings.append(build_string_setting('bake_make_selected_to_active_extrusion'))
        bake_settings.append(build_string_setting('bake_use_cage'))

        bake_settings.append(build_string_setting('bake_make_color'))
        bake_settings.append(build_string_setting('bake_make_roughness'))
        bake_settings.append(build_string_setting('bake_make_metallic'))
        bake_settings.append(build_string_setting('bake_make_alpha'))
        bake_settings.append(build_string_setting('bake_make_normal'))
        bake_settings.append(build_string_setting('bake_normal_directx'))
        bake_settings.append(build_string_setting('bake_make_ao'))
        bake_settings.append(build_string_setting('bake_make_emission'))

        bake_settings.append(build_string_setting('bake_combine_channels'))
        bake_settings.append(build_string_setting('bake_red_channel'))
        bake_settings.append(build_string_setting('bake_green_channel'))
        bake_settings.append(build_string_setting('bake_blue_channel'))

        bake_settings.append(build_string_setting('udim_baking'))
        bake_settings.append(build_string_setting('udim_count'))

        bake_settings.append(build_string_setting('bake_image_format'))
        bake_settings_string = ';'.join(bake_settings)

        completed_process = subprocess.run(
            f'"{bpy.app.binary_path}" "{current_blend_file}" -b --factory-startup --python-exit-code 1 --python "{script_file}" -- --computedevicetype "{compute_device_type}" --enableddevices "{enabled_devices_string}" --bakesettings "{bake_settings_string}"',
            shell=platform.system() != 'Windows'
        )

        if completed_process.returncode == 0:
            tasks_queue.add_task((after_bake_task, (context, self.objects)))
            return

        tasks_queue.add_task((update_error_baking, (context, "Check the console")))
        tasks_queue.add_task((update_is_baking, (context, False)))


class FLUENT_OT_BakeMapsForeground(Operator):
    "Bake your PBR maps\nCTRL+SHIFT+ALT for help"
    bl_idname = "fluent.bakepbrmapsforeground"
    bl_label = "Bake PBR maps"
    bl_options = {'REGISTER', 'UNDO'}

    size = None
    objects = None
    highpoly_objects = None
    previous_settings = {}
    props = None
    images = {}

    @classmethod
    def poll(cls, context):
        props = bpy.context.scene.FluentShaderProps

        if not props.bake_make_selected_to_active and not bpy.context.active_object:
            cls.poll_message_set("No object selected")
            return False

        if props.bake_make_selected_to_active and len(context.selected_objects) < 2:
            cls.poll_message_set("Baking high to low requires at least two selected objects")
            return False

        if not len(bpy.context.active_object.data.materials):
            cls.poll_message_set("The active object must have a material")
            return False

        if props.bake_in_image and '_' in bpy.context.active_object.name:
            cls.poll_message_set("The object name contains underscore. Please, remove it.")
            return False

        if props.bake_combine_channels:
            missing_bake_channel_name = checkMissingCombineChannel()
            if missing_bake_channel_name is not None:
                cls.poll_message_set(
                    "You selected combine RGB, but map '%s' is not enabled" % missing_bake_channel_name)
                return False

        if not bpy.data.filepath:
            cls.poll_message_set("Save the blend file before to bake")
            return False

        return True

    def invoke(self, context, event):
        self.props = bpy.context.scene.FluentShaderProps
        if event.ctrl and event.shift and event.alt:
            bpy.context.window_manager.popup_menu(
                make_oops(['This function bakes what you designed with Fluent Materializer.',
                           'The baking function bakes what is connected to the principled BSDF, which is connected to the material output.',
                           'Be sure the principled BSDF is connected to the material output, then select your object and bake.',
                           'The program will try to save the images in a folder called "Textures" next to the blend file,',
                           'if it can\'t, you have to save your files manualy',
                           'The image name follows this pattern : ObjectName_MAP']), title="About PBR baking",
                icon='INFO')
            return {'FINISHED'}

        self.objects = bpy.context.selected_objects
        selected_to_active = self.props.bake_make_selected_to_active
        # Vérification
        if not self.objects or len(bpy.context.selected_objects) == 0:
            bpy.context.window_manager.popup_menu(
                make_oops(['No active object.']),
                title="Problem detected",
                icon='INFO'
            )

            return {'FINISHED'}

        for obj in self.objects:
            if obj.type != 'MESH':
                bpy.context.window_manager.popup_menu(
                    make_oops(['You try to bake a non mesh thing.']),
                    title="Problem detected",
                    icon='INFO'
                )
                return {'FINISHED'}

            if not len(obj.data.materials):
                bpy.context.window_manager.popup_menu(
                    make_oops(['No material for the object.']),
                    title="Problem detected",
                    icon='INFO'
                )

            if not len(obj.data.uv_layers):
                bpy.context.window_manager.popup_menu(
                    make_oops(['No UV map detected.', 'Unwrap the model before to bake.']),
                    title="Problem detected",
                    icon='INFO'
                )
                return {'FINISHED'}

        # bake high to low
        if selected_to_active and len(bpy.context.selected_objects) < 2:
            bpy.context.window_manager.popup_menu(
                make_oops(['Select to active option but less than 2 objects selected.']),
                title="Problem detected",
                icon='INFO'
            )

            return {'FINISHED'}

        self.render_logic(context)

        return {'FINISHED'}

    def render_logic(self, context):
        selected_to_active = self.props.bake_make_selected_to_active
        # try:
        # Vérification
        if not self.objects or len(bpy.context.selected_objects) == 0:
            self.log_errors('No active object.')
            return {'FINISHED'}

        for obj in self.objects:
            if obj.type != 'MESH':
                self.log_errors('You try to bake a non mesh thing.')
                return {'FINISHED'}

            if not len(obj.data.materials):
                self.log_errors('No material for the object.')
                return {'FINISHED'}

            if not len(obj.data.uv_layers):
                self.log_errors('No UV map detected. : Unwrap the model before to bake.')
                return {'FINISHED'}

        if selected_to_active and len(bpy.context.selected_objects) < 2:
            self.log_errors('Select to active option but less than 2 objects selected.')
            return {'FINISHED'}

        if selected_to_active:
            self.highpoly_objects = [o for o in bpy.context.selected_objects if o != bpy.context.active_object and o.type == 'MESH']

        self.bake_process()

        for obj in self.objects:
            set_baked_material(context, obj)

        area = next((area for area in bpy.context.screen.areas if area.type == 'VIEW_3D'))
        with bpy.context.temp_override(area=area):
            bpy.ops.wm.context_toggle(data_path='space_data.show_region_ui')
            bpy.ops.wm.context_toggle(data_path='space_data.show_region_ui')
        # except Exception as ex:
        #     self.log_errors(repr(ex))

    def bake_process(self):
        self.init_bake_settings()

        try:
            file_path = bpy.data.filepath
            file_name = os.path.basename(file_path)
            path = file_path.split(file_name)[0]
            path_texture = os.path.join(os.path.dirname(bpy.data.filepath), 'Textures')
            if not os.path.exists(path_texture):
                os.makedirs(path_texture)
        except:
            raise Exception('Error while creating the texture folder')

        objects = self.objects
        if self.props.bake_make_selected_to_active:
            objects = [active_object('GET')]
        for obj in objects:
            # ajoute une node image dans chaque matériau
            img_nodes = []
            for m in obj.material_slots:
                nodes = get_nodes(m.material)
                img_node = nodes.new(type='ShaderNodeTexImage')
                img_node.name = '#imgtemp'
                img_nodes.append([nodes, img_node])

            image_name_root = None
            if self.props.bake_in_image is not None:
                image_name_root = self.props.bake_in_image.name.split('_')[0]
                bpy.context.scene.render.bake.use_clear = False
            else:
                bpy.context.scene.render.bake.use_clear = True

            if self.props.bake_make_color:
                self.bake_map(obj, image_name_root, img_nodes, path_texture, 'Color', False)

            if self.props.bake_make_roughness:
                roughness_img = self.bake_map(obj, image_name_root, img_nodes, path_texture, 'Roughness', True)
                self.images['roughness'] = roughness_img

            if self.props.bake_make_metallic:
                metallic_img = self.bake_map(obj, image_name_root, img_nodes, path_texture, 'Metallic', True)
                self.images['metallic'] = metallic_img

            if self.props.bake_make_alpha:
                alpha_img = self.bake_map(obj, image_name_root, img_nodes, path_texture, 'Alpha', True)
                self.images['alpha'] = alpha_img

            if self.props.bake_make_normal:
                self.bake_normal_map(obj, image_name_root, img_nodes, path_texture, 'Normal')

            if self.props.bake_normal_directx:
                self.bake_normal_map(obj, image_name_root, img_nodes, path_texture, 'NDirectX')

            if self.props.bake_make_ao:
                ao_img = self.bake_map(obj, image_name_root, img_nodes, path_texture, 'AO', True)
                self.images['ao'] = ao_img

            if self.props.bake_make_emission:
                self.bake_emission(obj, image_name_root, img_nodes, path_texture)

            if self.props.bake_combine_channels and not (
                    self.props.bake_red_channel == 'none' and self.props.bake_green_channel == 'none' and self.props.bake_blue_channel == 'none'):
                self.bake_combined(obj, image_name_root, path_texture)

            # Il faut aussi clean le low poly dans le cas d'un bake high to low poly
            if self.props.bake_make_selected_to_active:
                self.restore_materials_outputs(specific_object=obj)

            # supprime toutes les nodes images utilisées pour le bake
            for m in obj.material_slots:
                nodes = get_nodes(m.material)
                for node in nodes:
                    if '#imgtemp' in node.name:
                        nodes.remove(node)

        self.restore_settings()

    def log_errors(self, error):
        log_file = open(os.path.dirname(os.path.realpath(__file__)) + "/log_errors.txt", "a")
        log_file.write(error + '\n\r')
        log_file.close()

    def restore_settings(self):
        bpy.context.scene.view_settings.view_transform = self.previous_settings['color_space']
        bpy.context.scene.render.engine = self.previous_settings['engine']
        bpy.context.scene.cycles.preview_samples = self.previous_settings['preview_samples']
        bpy.context.scene.cycles.use_adaptive_sampling = self.previous_settings['use_adaptive_sampling']
        bpy.context.scene.cycles.use_denoising = self.previous_settings['use_denoising']
        bpy.context.scene.cycles.samples = self.previous_settings['render_samples']
        bpy.context.scene.render.bake.use_selected_to_active = self.previous_settings['baking_use_selected_to_active']
        bpy.context.scene.render.bake.use_cage = self.previous_settings['bake_use_cage']
        bpy.context.scene.render.bake.cage_object = self.previous_settings['bake_cage_object']

    def init_bake_settings(self):
        # sauvegarde les paramètres rendu de l'utilisateur
        self.previous_settings['engine'] = bpy.context.scene.render.engine
        self.previous_settings['preview_samples'] = bpy.context.scene.cycles.preview_samples
        self.previous_settings['render_samples'] = bpy.context.scene.cycles.samples
        self.previous_settings['use_adaptive_sampling'] = bpy.context.scene.cycles.use_adaptive_sampling
        self.previous_settings['use_denoising'] = bpy.context.scene.cycles.use_denoising
        self.previous_settings['baking_use_selected_to_active'] = bpy.context.scene.render.bake.use_selected_to_active
        self.previous_settings['bake_use_cage'] = bpy.context.scene.render.bake.use_cage
        self.previous_settings['bake_cage_object'] = bpy.context.scene.render.bake.cage_object
        self.previous_settings['color_space'] = bpy.context.scene.view_settings.view_transform
        # configure le moteur de rendu pour le baking
        bpy.context.scene.render.bake.margin = self.props.bake_margin
        bpy.context.scene.cycles.samples = int(self.props.bake_sample)
        bpy.context.scene.render.engine = 'CYCLES'
        if not self.props.bake_custom_colorspace:
            bpy.context.scene.view_settings.view_transform = 'Standard'
        bpy.context.scene.render.bake.use_clear = False

        bpy.context.scene.render.bake.use_selected_to_active = self.props.bake_make_selected_to_active
        bpy.context.scene.render.bake.cage_extrusion = self.props.bake_make_selected_to_active_extrusion
        bpy.context.scene.render.bake.use_cage = self.props.bake_use_cage

    def bake_map(self, obj: Object, image_name_root, img_nodes, path_texture, bake_type, is_data):
        size = self.props.map_size
        img = None
        if self.props.bake_in_image:
            img = self.find_image(image_name_root, bake_type)
        if not img:
            # créer l'image Color vide
            img = self.create_img(obj, size, bake_type, is_data, False, self.props.udim_baking,
                             self.props.udim_count, path_texture)

        # Connecte la Color qui rentre dans le PS à la sortie du shader

        if bake_type != 'AO':
            self.link_socket_to_materials_outputs(bake_type)
        # Assign l'image recevant le bake à la node image de chaque materiaux
        for i in img_nodes:
            i[1].image = img
            i[0].active = i[1]

        if bake_type == 'AO':
            bpy.ops.object.bake(type='AO')
        else:
            bpy.ops.object.bake(type='EMIT')

        self.restore_materials_outputs()
        try:
            img.save()
        except Exception as e:
            self.log_errors(repr(e))

        return img

    def bake_normal_map(self, obj: Object, image_name_root, img_nodes, path_texture, bake_type):
        size = self.props.map_size
        normal_img = None

        if self.props.bake_in_image:
            normal_img = self.find_image(image_name_root, bake_type)
        if not normal_img:
            # créer l'image normal vide
            normal_img = self.create_img(obj, size, bake_type, True, False, self.props.udim_baking, self.props.udim_count, path_texture)

        # Assign l'image recevant le bake à la node image de chaque materiaux
        for i in img_nodes:
            i[1].image = normal_img
            i[0].active = i[1]

        bpy.context.scene.render.bake.normal_r = 'POS_X'
        bpy.context.scene.render.bake.normal_g = 'POS_Y'
        bpy.context.scene.render.bake.normal_b = 'POS_Z'

        if bake_type == 'NDirectX':
            bpy.context.scene.render.bake.normal_g = 'NEG_Y'

        bpy.ops.object.bake(type='NORMAL')
        bpy.context.scene.render.bake.normal_g = 'POS_Y'
        self.restore_materials_outputs()

        try:
            normal_img.save()
        except:
            self.log_errors("Save normal manually. 16bit recommended")

        return normal_img

    def bake_emission(self, obj: Object, image_name_root, img_nodes, path_texture):
        size = self.props.map_size

        emission_color_img = None
        if self.props.bake_in_image:
            emission_color_img = self.find_image(image_name_root, 'EmissionColor')
        if not emission_color_img:
            # créer l'image Emission Color vide ###################################
            emission_color_img = self.create_img(obj, size, 'EmissionColor', False, False,
                                            self.props.udim_baking,
                                            self.props.udim_count, path_texture)

        # Connecte la Color qui rentre dans le PS à la sortie du shader
        self.link_socket_to_materials_outputs('Emission')

        # Assign l'image recevant le bake à la node image de chaque materiaux
        for i in img_nodes:
            i[1].image = emission_color_img
            i[0].active = i[1]

        bpy.ops.object.bake(type='EMIT')
        self.restore_materials_outputs()

        try:
            emission_color_img.save()
        except:
            self.log_errors("Blender fails to save the files on your system. Save it manually.")

        emission_strength_img = None
        if self.props.bake_in_image:
            emission_strength_img = self.find_image(image_name_root, 'EmissionStrength')
        if not emission_strength_img:
            # créer l'image Emission Strength vide ###################################
            emission_strength_img = self.create_img(obj, size, 'EmissionStrength', True, False,
                                               self.props.udim_baking,
                                               self.props.udim_count, path_texture)

        # Connecte la Color qui rentre dans le PS à la sortie du shader
        self.link_socket_to_materials_outputs('emission strength')

        # Assign l'image recevant le bake à la node image de chaque materiaux
        for i in img_nodes:
            i[1].image = emission_strength_img
            i[0].active = i[1]

        bpy.ops.object.bake(type='COMBINED')
        self.restore_materials_outputs()

        try:
            emission_strength_img.save()
        except:
            self.log_errors("Blender fails to save the files on your system. Save it manually.")

    def bake_combined(self, obj: Object, image_name_root, path_texture):
        size = self.props.map_size
        images = self.images

        combine_img = None
        selected_maps = []
        if self.props.bake_red_channel != 'none':
            selected_maps.append('R-' + self.props.bake_red_channel)
        if self.props.bake_green_channel != 'none':
            selected_maps.append('G-' + self.props.bake_green_channel)
        if self.props.bake_blue_channel != 'none':
            selected_maps.append('B-' + self.props.bake_blue_channel)

        combine_img_name = '-'.join(selected_maps)
        if self.props.bake_in_image:
            combine_img = self.find_image(image_name_root, combine_img_name)
            print('--- combine_img :', combine_img)
        if not combine_img:
            combine_img = self.create_img(obj, size, combine_img_name, True, False, self.props.udim_baking, self.props.udim_count, path_texture)

        for slot in obj.material_slots:
            mat = slot.material
            nodes = get_nodes(mat)
            material_output = get_material_output(nodes)
            img_R_node = nodes.new(type='ShaderNodeTexImage')
            img_R_node.name = '#imgtemp'
            img_G_node = nodes.new(type='ShaderNodeTexImage')
            img_G_node.name = '#imgtemp'
            img_B_node = nodes.new(type='ShaderNodeTexImage')
            img_B_node.name = '#imgtemp'

            if bpy.app.version >= (4, 0, 0):
                combine_node = nodes.new(type='ShaderNodeCombineColor')
            else:
                combine_node = nodes.new(type='ShaderNodeCombineRGB')
            combine_node.name = '#imgtemp'

            if self.props.bake_red_channel != 'none':
                img_R_node.image = images[self.props.bake_red_channel]
                link(mat, img_R_node, img_R_node.outputs[0].name, combine_node, combine_node.inputs[0].name)

            if self.props.bake_green_channel != 'none':
                img_G_node.image = images[self.props.bake_green_channel]
                link(mat, img_G_node, img_G_node.outputs[0].name, combine_node, combine_node.inputs[1].name)

            if self.props.bake_blue_channel != 'none':
                img_B_node.image = images[self.props.bake_blue_channel]
                link(mat, img_B_node, img_B_node.outputs[0].name, combine_node, combine_node.inputs[2].name)

            link(mat, combine_node, combine_node.outputs[0].name, material_output, 0)

            img_COMBINED_node = nodes.new(type='ShaderNodeTexImage')
            img_COMBINED_node.name = '#imgtemp'
            img_COMBINED_node.image = combine_img
            nodes.active = img_COMBINED_node

        bpy.ops.object.bake(type='EMIT', use_selected_to_active=False)
        self.restore_materials_outputs()
        try:
            combine_img.save()
        except:
            self.log_errors("Blender fails to save the files on your system. Save it manually.")

    def find_image(self, root_name, map):
        for img in bpy.data.images:
            nomenclature = img.name.split('_')
            nomenclature[-1] = nomenclature[-1].split('.')[0]
            if nomenclature[0] == root_name and map in nomenclature:
                return img
        return None

    def restore_materials_outputs(self, specific_object=None):
        if self.highpoly_objects:
            objects = self.highpoly_objects
        else:
            objects = self.objects

        if specific_object is not None:
            objects = [specific_object]

        for obj in objects:
            for slot in obj.material_slots:
                material = slot.material
                nodes = get_nodes(material)
                material_output = get_material_output(nodes)
                PS = get_principlebsdf(nodes)
                for node in nodes:
                    if '#temp' in node.name:
                        nodes.remove(node)
                link(material, PS, 0, material_output, 0)

    def link_socket_to_materials_outputs(self, type):
        # for material in selected_objects_material.values() :
        if self.highpoly_objects:
            objects = self.highpoly_objects
        else:
            objects = self.objects
        for obj in objects:
            for slot in obj.material_slots:
                material = slot.material
                nodes = get_nodes(material)

                # trouve le principled shader
                material_output = get_material_output(nodes)
                PS = get_principlebsdf(nodes)

                if PS and PS.outputs['BSDF'].links and PS.outputs['BSDF'].links[0].to_node == material_output:
                    socket = node = None

                    if type == 'Color':
                        # trouve ce qui est connecté à l'entrée Color
                        try:
                            socket = PS.inputs['Base Color'].links[0].from_socket.name
                            node = PS.inputs['Base Color'].links[0].from_node
                        except:
                            node = nodes.new(type='ShaderNodeRGB')
                            node.name = '#temp_color'
                            node.outputs[0].default_value = PS.inputs['Base Color'].default_value
                            socket = node.outputs[0].name

                    if type == 'Roughness':
                        # trouve ce qui est connecté à l'entrée Roughness
                        try:
                            socket = PS.inputs['Roughness'].links[0].from_socket.name
                            node = PS.inputs['Roughness'].links[0].from_node
                        except:
                            node = nodes.new(type='ShaderNodeValue')
                            node.name = '#temp_roughness'
                            node.outputs[0].default_value = PS.inputs['Roughness'].default_value
                            socket = node.outputs[0].name

                    if type == 'Metallic':
                        # trouve ce qui est connecté à l'entrée Metallic
                        try:
                            socket = PS.inputs['Metallic'].links[0].from_socket.name
                            node = PS.inputs['Metallic'].links[0].from_node
                        except:
                            node = nodes.new(type='ShaderNodeValue')
                            node.name = '#temp_metallic'
                            node.outputs[0].default_value = PS.inputs['Metallic'].default_value
                            socket = node.outputs[0].name

                    if type == 'Alpha':
                        # trouve ce qui est connecté à l'entrée Alpha
                        try:
                            socket = PS.inputs['Alpha'].links[0].from_socket.name
                            node = PS.inputs['Alpha'].links[0].from_node
                        except:
                            node = nodes.new(type='ShaderNodeValue')
                            node.name = '#temp_alpha'
                            node.outputs[0].default_value = PS.inputs['Alpha'].default_value
                            socket = node.outputs[0].name

                    if type == 'Emission':
                        # trouve ce qui est connecté à l'entrée Emission
                        try:
                            socket = PS.inputs['Emission Color'].links[0].from_socket.name
                            node = PS.inputs['Emission Color'].links[0].from_node
                        except:
                            node = nodes.new(type='ShaderNodeRGB')
                            node.name = '#temp_emission_color'
                            node.outputs[0].default_value = PS.inputs['Emission Color'].default_value
                            socket = node.outputs[0].name

                    if type == 'emission strength':
                        # trouve ce qui est connecté à l'entrée Emission Strength
                        try:
                            socket = PS.inputs['Emission Strength'].links[0].from_socket.name
                            node = PS.inputs['Emission Strength'].links[0].from_node
                        except:
                            node = nodes.new(type='ShaderNodeValue')
                            node.name = '#temp_emission_strength'
                            node.outputs[0].default_value = PS.inputs['Emission Strength'].default_value
                            socket = node.outputs[0].name

                    if node == None or socket == None:
                        self.log_errors('Type "' + type + '" not supported.')

                    link(material, node, socket, material_output, 0)

    def create_img(self, object, size, map, is_data, is_float, use_udim, udim_count, path_texture):
        img_name = object.name + '_' + str(size) + 'px_' + map
        # Si l'image existe déjà retourner l'image
        for i in bpy.data.images:
            if img_name == i.name:
                return i

        img = bpy.data.images.new(object.name + '_' + str(size) + 'px_' + map, width=int(size), height=int(size), tiled=use_udim, is_data=is_data, float_buffer=is_float)
        if use_udim:
            img.name = img.name + '.<UDIM>.'
            previous_area_ui_type = bpy.context.area.ui_type
            bpy.context.area.ui_type = 'IMAGE_EDITOR'
            for i in range(udim_count - 1):
                tile = img.tiles.new(tile_number=1001 + 1 + i)
                img.tiles.active = tile
                bpy.context.space_data.image = img
                bpy.ops.image.tile_fill(color=(0, 0, 0, 1), width=size, height=size, float=is_float)
            bpy.context.area.ui_type = previous_area_ui_type

        img.file_format = self.props.bake_image_format
        if self.props.bake_image_format == 'PNG' or map in ['Normal', 'NDirectX']:
            img.filepath_raw = os.path.join(path_texture, img.name + '.png')
        elif self.props.bake_image_format == 'JPEG':
            img.filepath_raw = os.path.join(path_texture, img.name + '.jpg')

        return img


class FLUENT_OT_BakeMask(Operator):
    "Bake edge and cavity mask of the node trees\nCTRL+SHIFT+ALT for help"
    bl_idname = "fluent.bakemask"
    bl_label = "Bake PBR maps"
    bl_options = {'REGISTER', 'UNDO'}

    choice: bpy.props.StringProperty()

    @classmethod
    def poll(cls, context):
        if active_object('GET'):
            return True
        else:
            return False

    def bake_process(self):
        PS = None
        obj_name = None
        mask_nodes = []
        # trouve le principled shader
        node_tree = get_node_tree(self.baked_material)
        nodes = get_nodes(self.baked_material)
        if self.choice == 'ALL':
            mask_nodes = [node for node in nodes if
                          node.type == 'GROUP' and (node.node_tree.name in ['Edges', 'All edges', 'Cavity'])]
        elif self.choice == 'EDGES':
            mask_nodes = [node for node in nodes if
                          node.type == 'GROUP' and node.node_tree.name in ['Edges', 'All edges']]
        elif self.choice == 'CAVITY':
            mask_nodes = [node for node in nodes if node.type == 'GROUP' and 'Cavity' in node.node_tree.name]
        elif self.choice == 'SELECTED':
            mask_nodes = [node for node in nodes if node.select and node.type == 'GROUP' and (
                        node.node_tree.name in ['Edges', 'All edges', 'Cavity'])]
        # On récupère le nom de l'objet sélectionné
        obj = bpy.context.active_object

        if mask_nodes and obj:
            # sauvgarde les paramètres rendu de l'utilisateur
            self.previous_settings['engine'] = bpy.context.scene.render.engine
            self.previous_settings['preview_samples'] = bpy.context.scene.cycles.preview_samples
            self.previous_settings['render_samples'] = bpy.context.scene.cycles.samples
            self.previous_settings['shading_type'] = bpy.context.space_data.shading.type
            # configure le moteur de rendu pour le baking
            bpy.context.scene.render.bake.margin = bpy.context.scene.FluentShaderProps.bake_margin
            bpy.context.scene.cycles.samples = int(bpy.context.scene.FluentShaderProps.bake_sample)
            bpy.context.scene.render.engine = 'CYCLES'
            bpy.context.scene.view_settings.view_transform = 'Standard'

            # Ajout une node emission et la connect à la sortie du matériau
            material_output = get_material_output(nodes)

            try:
                file_path = bpy.data.filepath
                file_name = os.path.basename(file_path)
                path = file_path.split(file_name)[0]
                path_texture = os.path.join(os.path.dirname(bpy.data.filepath), 'Textures')
                if not os.path.exists(path_texture):
                    os.makedirs(path_texture)
                folder_made = True
            except:
                folder_made = False
                self.report({'INFO'}, "The blend file must be saved for automatic image saving.")

            for mask_node in mask_nodes:
                # mute le mask mixer
                for n in mask_node.node_tree.nodes:
                    if n.bl_idname == 'ShaderNodeGroup' and 'Mask Texture Mixer' in n.node_tree.name:
                        n.mute = True

                # ajoute une node image
                img_node = nodes.new(type='ShaderNodeTexImage')

                # créer l'image Mask vide
                mask_img = create_img(self.object, self.size, 'Mask', False, False,
                                      bpy.context.scene.FluentShaderProps.udim_baking,
                                      bpy.context.scene.FluentShaderProps.udim_count)
                if folder_made:
                    mask_img.filepath_raw = os.path.join(path_texture, mask_img.name + '.png')
                mask_img.file_format = 'PNG'

                # Node image utilise l'image Mask
                img_node.image = mask_img

                # Connecte le mask à l'entrée Color de l'émission
                link(self.baked_material, mask_node, 'Mask', material_output, 0)
                # Node image utilise l'image Mask
                img_node.image = mask_img
                # Bake
                # bpy.context.scene.sequencer_colorspace_settings.name = 'sRGB'
                active_object(obj=obj, action='SET', solo=True)
                node_tree.nodes.active = img_node
                bpy.ops.object.bake(type='EMIT')
                # Enregistre l'image
                if folder_made:
                    try:
                        mask_img.save()
                    except:
                        self.report({'INFO'}, "Blender fails to save the files on your system. Save it manually.")
                # Réactive le mask mixer
                # mute le mask mixer
                # for n in mask_node.node_tree.nodes:
                #     if n.bl_idname == 'ShaderNodeGroup' and 'Mask Texture Mixer' in n.node_tree.name:
                #         n.mute = False
                # Ajoute la node bake dans l'arbre
                new_group = import_node_group('Baked')
                original = new_group.node_tree
                single = original.copy()
                new_group.node_tree = single
                new_group.label = 'Baked ' + mask_node.name
                img_node_baked = new_group.node_tree.nodes.get('Image Texture')
                img_node_baked.image = mask_img

                nodes.remove(img_node)

            bpy.context.scene.view_settings.view_transform = 'Filmic'
            bpy.context.scene.render.engine = self.previous_settings['engine']
            bpy.context.scene.cycles.preview_samples = self.previous_settings['preview_samples']
            bpy.context.scene.cycles.samples = self.previous_settings['render_samples']
            bpy.context.space_data.shading.type = self.previous_settings['shading_type']



        else:
            self.report({'ERROR'}, 'No selected object.')

        return {'FINISHED'}

    def invoke(self, context, event):
        if event.ctrl and event.shift and event.alt:
            bpy.context.window_manager.popup_menu(
                make_oops(['This function bake edge and cavity masks from Fluent MC.',
                           'The program searchs and uses the edge and cavity masks from Fluent MC in the node tree.',
                           'The program will try to save the images in a folder called "Textures" next to the blend file if it saved.',
                           'The image name follows this pattern : ObjectName_MaterialName_Mask_NodeName']),
                title="About masks baking", icon='INFO')
            return {'FINISHED'}
        self.previous_settings = {}
        self.size = int(context.scene.FluentShaderProps.map_size)
        self.baked_material = active_object('GET').active_material
        self.object = active_object('GET')

        if not len(active_object('GET').data.uv_layers):
            bpy.context.window_manager.popup_menu(
                make_oops(['No UV map detected.', 'Unwrap the model before to bake.']),
                title="Problem detected",
                icon='INFO'
            )
            return {'FINISHED'}

        self.bake_process()

        return {'FINISHED'}
