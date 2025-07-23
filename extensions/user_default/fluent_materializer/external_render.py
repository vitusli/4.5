import os
import bpy

previous_settings = {}
bake_settings = {}
images = {}
size = None
objects = None
highpoly_objects = None
selected_to_active = False


def create_img(obj, size, map, is_data, is_float, use_udim, udim_count, path_texture):
    img = bpy.data.images.new(obj.name + '_' + str(size) + 'px_' + map, width=size, height=size, tiled=use_udim, is_data=is_data, float_buffer=is_float)
    if use_udim:
        img.name = img.name+'.<UDIM>.'
        previous_area_ui_type = bpy.context.area.ui_type
        bpy.context.area.ui_type = 'IMAGE_EDITOR'
        for i in range(udim_count-1):
            tile = img.tiles.new(tile_number=1001+1+i)
            img.tiles.active = tile
            bpy.context.space_data.image = img
            bpy.ops.image.tile_fill(color=(0, 0, 0, 1), width=size, height=size, float=is_float)
        bpy.context.area.ui_type = previous_area_ui_type

    img.file_format = bake_settings['bake_image_format']
    if bake_settings['bake_image_format'] == 'PNG' or map in ['Normal', 'NDirectX']:
        img.filepath_raw = os.path.join(path_texture, img.name + '.png')
    elif bake_settings['bake_image_format'] == 'JPEG':
        img.filepath_raw = os.path.join(path_texture, img.name + '.jpg')

    return img


def find_image(root_name, map):
    for img in bpy.data.images:
        nomenclature = img.name.split('_')
        nomenclature[-1] = nomenclature[-1].split('.')[0]
        if nomenclature[0] == root_name and map in nomenclature:
            return img
    return None


def get_image_texture_image(image_name_root):
    file_path = bpy.data.filepath
    file_name = os.path.basename(file_path)
    path = file_path.split(file_name)[0]

    textures_path = os.path.join(path, 'Textures')
    dir_list = os.listdir(textures_path)

    textures_found = []
    for file in dir_list:
        if image_name_root not in file:
            continue

        textures_found.append(file)

    sorted_images = sorted(textures_found)
    image_path = os.path.join(textures_path, sorted_images.pop())

    return bpy.data.images.load(filepath=image_path, check_existing=False)


def get_node_tree(material):
    return material.node_tree


def get_nodes(material):
    return get_node_tree(material).nodes


def link(material, from_node, from_slot_name, to_node, to_slot_name):
    try:
        input = to_node.inputs[to_slot_name]
        output = from_node.outputs[from_slot_name]
        material.node_tree.links.new(input, output)
    except:pass


def get_material_output(nodes):
    for n in nodes:
        if n.type == 'OUTPUT_MATERIAL':
            return n
    print('--- no output material')


def get_principlebsdf(nodes):
    for n in nodes:
        if n.type == 'BSDF_PRINCIPLED':
            return n
    print('--- no Principled BSDF')


def link_socket_to_materials_outputs(type):
    global highpoly_objects, objects
    # for material in selected_objects_material.values() :
    if highpoly_objects:
        objs = highpoly_objects
    else:
        objs = objects
    for obj in objs:
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
                    log_errors('Type "' + type + '" not supported.')

                link(material, node, socket, material_output, 0)


def restore_materials_outputs(specific_object=None):
    global objects
    if highpoly_objects:
        objs = highpoly_objects
    else:
        objs = objects

    if specific_object is not None:
        objs = [specific_object]

    for obj in objs:
        for slot in obj.material_slots:
            material = slot.material
            nodes = get_nodes(material)
            material_output = get_material_output(nodes)
            PS = get_principlebsdf(nodes)
            for node in nodes:
                if '#temp' in node.name:
                    nodes.remove(node)
            link(material, PS, 0, material_output, 0)


def log_errors(error):
    log_file = open(os.path.dirname(os.path.realpath(__file__))+"/log_errors.txt", "a")
    log_file.write(error+'\n\r')
    log_file.close()


def init_bake_settings():
    # sauvegarde les paramètres rendu de l'utilisateur
    previous_settings['engine'] = bpy.context.scene.render.engine
    previous_settings['preview_samples'] = bpy.context.scene.cycles.preview_samples
    previous_settings['render_samples'] = bpy.context.scene.cycles.samples
    previous_settings['use_adaptive_sampling'] = bpy.context.scene.cycles.use_adaptive_sampling
    previous_settings['use_denoising'] = bpy.context.scene.cycles.use_denoising
    previous_settings['baking_use_selected_to_active'] = bpy.context.scene.render.bake.use_selected_to_active
    previous_settings['bake_use_cage'] = bpy.context.scene.render.bake.use_cage
    previous_settings['bake_cage_object'] = bpy.context.scene.render.bake.cage_object
    previous_settings['color_space'] = bpy.context.scene.view_settings.view_transform
    # configure le moteur de rendu pour le baking
    bpy.context.scene.render.bake.margin = bake_settings['bake_margin']
    bpy.context.scene.cycles.samples = bake_settings['bake_sample']
    bpy.context.scene.render.engine = 'CYCLES'
    if not bake_settings['bake_custom_colorspace']:
        bpy.context.scene.view_settings.view_transform = 'Standard'
    bpy.context.scene.render.bake.use_clear = False

    bpy.context.scene.render.bake.use_selected_to_active = bake_settings['bake_make_selected_to_active']
    bpy.context.scene.render.bake.cage_extrusion = bake_settings['bake_make_selected_to_active_extrusion']
    bpy.context.scene.render.bake.use_cage = bake_settings['bake_use_cage']


def restore_settings():
    bpy.context.scene.view_settings.view_transform = previous_settings['color_space']
    bpy.context.scene.render.engine = previous_settings['engine']
    bpy.context.scene.cycles.preview_samples = previous_settings['preview_samples']
    bpy.context.scene.cycles.use_adaptive_sampling = previous_settings['use_adaptive_sampling']
    bpy.context.scene.cycles.use_denoising = previous_settings['use_denoising']
    bpy.context.scene.cycles.samples = previous_settings['render_samples']
    bpy.context.scene.render.bake.use_selected_to_active = previous_settings['baking_use_selected_to_active']
    bpy.context.scene.render.bake.use_cage = previous_settings['bake_use_cage']
    bpy.context.scene.render.bake.cage_object = previous_settings['bake_cage_object']


def bake_map(obj, image_name_root, img_nodes, path_texture, bake_type, is_data):
    global size
    img = None
    if bake_settings['bake_in_image']:
        img = find_image(image_name_root, bake_type)
    if not img:
        # créer l'image Color vide
        img = create_img(obj, size, bake_type, is_data, False, bake_settings['udim_baking'],
                         bake_settings['udim_count'], path_texture)

    # Connecte la Color qui rentre dans le PS à la sortie du shader

    if bake_type != 'AO':
        link_socket_to_materials_outputs(bake_type)
    # Assign l'image recevant le bake à la node image de chaque materiaux
    for i in img_nodes:
        i[1].image = img
        i[0].active = i[1]

    if bake_type == 'AO':
        bpy.ops.object.bake(type='AO')
    else:
        bpy.ops.object.bake(type='EMIT')

    restore_materials_outputs()
    try:
        img.save()
    except Exception as e:
        log_errors(repr(e))

    return img


def bake_normal_map(obj, image_name_root, img_nodes, path_texture, bake_type):
    global size
    normal_img = None

    if bake_settings['bake_in_image']:
        normal_img = find_image(image_name_root, bake_type)
    if not normal_img:
        # créer l'image normal vide
        normal_img = create_img(obj, size, bake_type, True, False, bake_settings['udim_baking'], bake_settings['udim_count'], path_texture)

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
    restore_materials_outputs()

    try:
        normal_img.save()
    except:
        log_errors("Save normal manually. 16bit recommended")

    return normal_img


def bake_emission(obj, image_name_root, img_nodes, path_texture):
    global size

    emission_color_img = None
    if bake_settings['bake_in_image']:
        emission_color_img = find_image(image_name_root, 'EmissionColor')
    if not emission_color_img:
        # créer l'image Emission Color vide ###################################
        emission_color_img = create_img(obj, size, 'EmissionColor', False, False,
                                        bake_settings['udim_baking'],
                                        bake_settings['udim_count'], path_texture)


    # Connecte la Color qui rentre dans le PS à la sortie du shader
    link_socket_to_materials_outputs('Emission')

    # Assign l'image recevant le bake à la node image de chaque materiaux
    for i in img_nodes:
        i[1].image = emission_color_img
        i[0].active = i[1]

    bpy.ops.object.bake(type='EMIT')
    restore_materials_outputs()

    try:
        emission_color_img.save()
    except:
        log_errors("Blender fails to save the files on your system. Save it manually.")

    emission_strength_img = None
    if bake_settings['bake_in_image']:
        emission_strength_img = find_image(image_name_root, 'EmissionStrength')
    if not emission_strength_img:
        # créer l'image Emission Strength vide ###################################
        emission_strength_img = create_img(obj, size, 'EmissionStrength', True, False,
                                           bake_settings['udim_baking'],
                                           bake_settings['udim_count'], path_texture)

    # Connecte la Color qui rentre dans le PS à la sortie du shader
    link_socket_to_materials_outputs('emission strength')

    # Assign l'image recevant le bake à la node image de chaque materiaux
    for i in img_nodes:
        i[1].image = emission_strength_img
        i[0].active = i[1]

    bpy.ops.object.bake(type='COMBINED')
    restore_materials_outputs()

    try:
        emission_strength_img.save()
    except:
        log_errors("Blender fails to save the files on your system. Save it manually.")


def bake_combined(obj, image_name_root, path_texture):
    global size, images

    combine_img = None
    selected_maps = []
    if bake_settings['bake_red_channel'] != 'none':
        selected_maps.append('R-' + bake_settings['bake_red_channel'])
    if bake_settings['bake_green_channel'] != 'none':
        selected_maps.append('G-' + bake_settings['bake_green_channel'])
    if bake_settings['bake_blue_channel'] != 'none':
        selected_maps.append('B-' + bake_settings['bake_blue_channel'])

    combine_img_name = '-'.join(selected_maps)
    if bake_settings['bake_in_image']:
        combine_img = find_image(image_name_root, combine_img_name)
        print('--- combine_img :', combine_img)
    if not combine_img:
        combine_img = create_img(obj, size, combine_img_name, True, False, bake_settings['udim_baking'], bake_settings['udim_count'], path_texture)

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

        if bake_settings['bake_red_channel'] != 'none':
            img_R_node.image = images[bake_settings['bake_red_channel']]
            link(mat, img_R_node, img_R_node.outputs[0].name, combine_node, combine_node.inputs[0].name)

        if bake_settings['bake_green_channel'] != 'none':
            img_G_node.image = images[bake_settings['bake_green_channel']]
            link(mat, img_G_node, img_G_node.outputs[0].name, combine_node, combine_node.inputs[1].name)

        if bake_settings['bake_blue_channel'] != 'none':
            img_B_node.image = images[bake_settings['bake_blue_channel']]
            link(mat, img_B_node, img_B_node.outputs[0].name, combine_node, combine_node.inputs[2].name)

        link(mat, combine_node, combine_node.outputs[0].name, material_output, 0)

        img_COMBINED_node = nodes.new(type='ShaderNodeTexImage')
        img_COMBINED_node.name = '#imgtemp'
        img_COMBINED_node.image = combine_img
        nodes.active = img_COMBINED_node

    bpy.ops.object.bake(type='EMIT', use_selected_to_active=False)
    restore_materials_outputs()
    try:
        combine_img.save()
    except:
        log_errors("Blender fails to save the files on your system. Save it manually.")


def bake_process():
    global selected_to_active, images, objects

    init_bake_settings()

    try:
        file_path = bpy.data.filepath
        file_name = os.path.basename(file_path)
        path = file_path.split(file_name)[0]
        path_texture = os.path.join(os.path.dirname(bpy.data.filepath), 'Textures')
        if not os.path.exists(path_texture):
            os.makedirs(path_texture)
    except:
        raise Exception('Error while creating the texture folder')

    objects_to_bake = objects
    if bake_settings['bake_make_selected_to_active']:
        objects_to_bake = [active_object('GET')]

    for obj in objects_to_bake:
        # ajoute une node image dans chaque matériau
        img_nodes = []
        for m in obj.material_slots:
            nodes = get_nodes(m.material)
            img_node = nodes.new(type='ShaderNodeTexImage')
            img_node.name = '#imgtemp'
            img_nodes.append([nodes, img_node])

        image_name_root = None
        if bake_settings['bake_in_image'] is not None:
            image_name_root = bake_settings['bake_in_image']
            bpy.context.scene.render.bake.use_clear = False
        else:
            bpy.context.scene.render.bake.use_clear = True

        if bake_settings['bake_make_color']:
            bake_map(obj, image_name_root, img_nodes, path_texture, 'Color', False)

        if bake_settings['bake_make_roughness']:
            roughness_img = bake_map(obj, image_name_root, img_nodes, path_texture, 'Roughness', True)
            images['roughness'] = roughness_img

        if bake_settings['bake_make_metallic']:
            metallic_img = bake_map(obj, image_name_root, img_nodes, path_texture, 'Metallic', True)
            images['metallic'] = metallic_img

        if bake_settings['bake_make_alpha']:
            alpha_img = bake_map(obj, image_name_root, img_nodes, path_texture, 'Alpha', True)
            images['alpha'] = alpha_img

        if bake_settings['bake_make_normal']:
            bake_normal_map(obj, image_name_root, img_nodes, path_texture, 'Normal')

        if bake_settings['bake_normal_directx']:
            bake_normal_map(obj, image_name_root, img_nodes, path_texture, 'NDirectX')

        if bake_settings['bake_make_ao']:
            ao_img = bake_map(obj, image_name_root, img_nodes, path_texture, 'AO', True)
            images['ao'] = ao_img

        if bake_settings['bake_make_emission']:
            bake_emission(obj, image_name_root, img_nodes, path_texture)

        if bake_settings['bake_combine_channels'] and not (
                bake_settings['bake_red_channel'] == 'none' and bake_settings['bake_green_channel'] == 'none' and bake_settings['bake_blue_channel'] == 'none'):
            bake_combined(obj, image_name_root, path_texture)

        # Il faut aussi clean le low poly dans le cas d'un bake high to low poly
        if selected_to_active:
            restore_materials_outputs(specific_object=obj)

        # supprime toutes les nodes images utilisées pour le bake
        for m in obj.material_slots:
            nodes = get_nodes(m.material)
            for node in nodes:
                if '#imgtemp' in node.name:
                    nodes.remove(node)

    restore_settings()


def active_object(obj=None, action='GET', solo=False):
    if solo:
        bpy.ops.object.select_all(action="DESELECT")
    if action == 'SET':
        if obj is not None:
            obj.hide_set(False)
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
        return obj
    elif action == 'GET':
        return bpy.context.active_object


def get_setting_from_split(setting_name, bake_settings_split, special_cast = None):
    for setting in bake_settings_split:
        setting_data = setting.split(':')
        setting_value = setting_data[1]
        if setting_data[0] != setting_name:
            continue

        if setting_value == 'None':
            return None
        if setting_value == 'True':
            return True
        if setting_value == 'False':
            return False

        if special_cast == 'STRING':
            return setting_value
        if special_cast == 'INT':
            return int(setting_value)
        if special_cast == 'FLOAT':
            return float(setting_value)

    raise Exception(f'setting "{setting_name}" not found in split')


def extract_bake_settings(bake_settings_string):
    bake_settings_split = bake_settings_string.split(';')

    bake_settings['map_size'] = get_setting_from_split('map_size', bake_settings_split, special_cast='INT')
    bake_settings['bake_in_image'] = get_setting_from_split('bake_in_image', bake_settings_split, special_cast='STRING')
    bake_settings['bake_margin'] = get_setting_from_split('bake_margin', bake_settings_split, special_cast='INT')
    bake_settings['bake_sample'] = get_setting_from_split('bake_sample', bake_settings_split, special_cast='INT')

    bake_settings['bake_custom_colorspace'] = get_setting_from_split('bake_custom_colorspace', bake_settings_split)
    bake_settings['bake_make_selected_to_active'] = get_setting_from_split('bake_make_selected_to_active', bake_settings_split)
    bake_settings['bake_make_selected_to_active_extrusion'] = get_setting_from_split('bake_make_selected_to_active_extrusion', bake_settings_split, special_cast='FLOAT')
    bake_settings['bake_use_cage'] = get_setting_from_split('bake_use_cage', bake_settings_split)

    bake_settings['bake_make_color'] = get_setting_from_split('bake_make_color', bake_settings_split)
    bake_settings['bake_make_roughness'] = get_setting_from_split('bake_make_roughness', bake_settings_split)
    bake_settings['bake_make_metallic'] = get_setting_from_split('bake_make_metallic', bake_settings_split)
    bake_settings['bake_make_alpha'] = get_setting_from_split('bake_make_alpha', bake_settings_split)
    bake_settings['bake_make_normal'] = get_setting_from_split('bake_make_normal', bake_settings_split)
    bake_settings['bake_normal_directx'] = get_setting_from_split('bake_normal_directx', bake_settings_split)
    bake_settings['bake_make_ao'] = get_setting_from_split('bake_make_ao', bake_settings_split)
    bake_settings['bake_make_emission'] = get_setting_from_split('bake_make_emission', bake_settings_split)

    bake_settings['bake_combine_channels'] = get_setting_from_split('bake_combine_channels', bake_settings_split)
    bake_settings['bake_red_channel'] = get_setting_from_split('bake_red_channel', bake_settings_split, special_cast='STRING')
    bake_settings['bake_green_channel'] = get_setting_from_split('bake_green_channel', bake_settings_split, special_cast='STRING')
    bake_settings['bake_blue_channel'] = get_setting_from_split('bake_blue_channel', bake_settings_split, special_cast='STRING')

    bake_settings['udim_baking'] = get_setting_from_split('udim_baking', bake_settings_split)
    bake_settings['udim_count'] = get_setting_from_split('udim_count', bake_settings_split, special_cast='INT')

    bake_settings['bake_image_format'] = get_setting_from_split('bake_image_format', bake_settings_split, special_cast='STRING')


def render_logic(compute_device_type, enabled_devices, bake_settings_string):
    global size, objects, highpoly_objects, selected_to_active
    try:
        extract_bake_settings(bake_settings_string)
        size = bake_settings['map_size']
        highpoly_objects = None
        selected_to_active = bake_settings['bake_make_selected_to_active']

        objects = bpy.context.selected_objects
        if selected_to_active:
            objects = [active_object('GET')]

        prefs = bpy.context.preferences
        cprefs = prefs.addons['cycles'].preferences
        cprefs.compute_device_type = compute_device_type
        bpy.context.scene.render.engine = 'CYCLES'
        bpy.context.scene.cycles.device = 'GPU'

        # get_devices() to let Blender detects GPU device
        bpy.context.preferences.addons["cycles"].preferences.get_devices()
        for device in cprefs.devices:
            if device.id in enabled_devices:
                device.use = True

        # Vérification
        if not objects or len(bpy.context.selected_objects) == 0:
            log_errors('No active object.')
            return {'FINISHED'}

        for obj in objects:
            if obj.type != 'MESH':
                log_errors('You try to bake a non mesh thing.')
                return {'FINISHED'}

            if not len(obj.data.materials):
                log_errors('No material for the object.')
                return {'FINISHED'}

            if not len(obj.data.uv_layers):
                log_errors('No UV map detected. : Unwrap the model before to bake.')
                return {'FINISHED'}

        if selected_to_active and len(bpy.context.selected_objects) < 2:
            log_errors('Select to active option but less than 2 objects selected.')
            return {'FINISHED'}

        if selected_to_active:
            highpoly_objects = [o for o in bpy.context.selected_objects if o != bpy.context.active_object and o.type == 'MESH']

        bake_process()
    except Exception as ex:
        log_errors(repr(ex))


def main():
    import sys  # to get command line args
    import argparse  # to parse options for us and print a nice help message

    # get the args passed to blender after "--", all of which are ignored by
    # blender so scripts may receive their own arguments
    argv = sys.argv

    if "--" not in argv:
        argv = []  # as if no args are passed
    else:
        argv = argv[argv.index("--") + 1:]  # get all args after "--"

    # When --help or no args are given, print this help
    usage_text = (
            "Run blender in background mode with this script:"
            "  blender --background --python " + __file__ + " -- [options]"
    )

    parser = argparse.ArgumentParser(description=usage_text)

    parser.add_argument(
        "-c", "--computedevicetype", dest="compute_device_type",
        help="Blender compute type",
    )

    parser.add_argument(
        "-e", "--enableddevices", dest="enabled_devices",
        help="Blender render enabled devices",
    )

    parser.add_argument(
        "-s", "--bakesettings", dest="bake_settings_string",
        help="Bake settings",
    )

    args = parser.parse_args(argv)

    if not argv:
        parser.print_help()
        return

    render_logic(args.compute_device_type, args.enabled_devices, args.bake_settings_string)

    print("batch job finished, exiting")


if __name__ == "__main__":
    main()
