import time

from .. import auto_load as al
from ..auto_load.common import *

from .. import base_ops
from .. import override_handler

from . import queue
from . import texture_sets
from . import ui
from . import utils
from . import setup

class SanctusBakeOp(base_ops.SanctusOperator):

    @staticmethod
    def get_bake_manager(context: bt.Context):
        return texture_sets.TextureSetManager.get_from(context.scene)
    
    @staticmethod
    def get_baking_queue(context: bt.Context):
        return queue.BakingQueue.get_from(context.object)

    @classmethod
    def get_default_format_prop(cls):
        prefs = al.get_prefs()
        return prefs.baking().default_image_export_format
    
    @classmethod
    def get_default_format(cls):
        return cls.get_default_format_prop()()


@al.register_operator
class SaveBakeTexture(SanctusBakeOp):
    bl_label = 'Save Texture'
    bl_description = 'Save the baked texture to the disk'
    image = al.ContextProperty[bt.Image]()
    
    def run(self, context: bt.Context):
        image = self.image()
        format = self.get_default_format()()
        image.file_format = format #TODO does not actually set the file format right away
        with context.temp_override(edit_image=image):
            bo.image.save_as(al.BOperatorContext.INVOKE_DEFAULT(), save_as_render=False, relative_path=False)

@al.register_operator
class SaveTextureSet(base_ops.SanctusFolderOperator, SanctusBakeOp):
    bl_label = 'Save All'
    bl_description = 'Save all baked textures from the set'

    texture_set = al.ContextProperty[texture_sets.TextureSet]()
    bulk_filename = al.StringProperty(name='Bulk Filename')

    wildcard_map = [
        ('$(MAT)', 'Material Name'),
        ('$(RES)', 'Result Name'),
        ('$(IND)', 'Index')
    ]

    def set_defaults(self, context: bt.Context, event: bt.Event):
        self.bulk_filename.value = f'$(RES)'

    def get_final_filename(self, texture: texture_sets.BakeTexture, index: int):
        filename: str = self.bulk_filename()
        filename = filename.replace('$(MAT)', self.texture_set().set_name())
        filename = filename.replace('$(RES)', texture.texture().name)
        filename = filename.replace('$(IND)', f'{index:02}')
        filename = filename + '.' + self.get_default_format().extension
        return filename

    def draw(self, context: bt.Context) -> None:
        l = self.layout
        col = al.UI.column(l, align=True)

        for tag, description in self.wildcard_map:
            al.UI.even_split(
                col,
                lambda l: al.UI.label(l, f'{tag} = ', alignment=al.UIAlignment.RIGHT),
                lambda l: al.UI.label(l, description, alignment=al.UIAlignment.LEFT),
                align=True
            )

        col.separator()

        al.UI.label(col, 'Bulk Naming:')
        al.UI.weighted_split(
            col,
            (lambda l: self.bulk_filename.draw_ui(l, al.UIOptionsProp(text='')), 3),
            (lambda l: self.get_default_format_prop().draw_ui(l, al.UIOptionsProp(text='')), 1),
            align=True
        )

        preview_col = l.box().column(align=True)
        space: bt.SpaceFileBrowser = context.space_data
        directory = Path(space.params.directory.decode())
        for i, tex in enumerate(self.texture_set().get_valid_textures()):
            final_filename = self.get_final_filename(tex, i)
            al.UI.label(preview_col, text=final_filename, alert=directory.joinpath(final_filename).exists())

    def run(self, context: bt.Context):
        directory = Path(self.Directory)
        temp_scene = bpy.data.scenes.new('sanctus_temp_scene')
        temp_scene.render.image_settings.file_format = self.get_default_format()()
        temp_scene.view_settings.view_transform = 'Standard'
        try:
            for i, tex in enumerate(self.texture_set().get_valid_textures()):
                image = tex.texture()
                final_path = directory.joinpath(self.get_final_filename(tex, i))
                image.save_render(filepath=str(final_path), scene=temp_scene)
        except Exception as e:
            raise e
        finally:
            bpy.data.scenes.remove(temp_scene)


class SocketOperator(SanctusBakeOp):

    @classmethod
    def get_asserts(cls, context: bt.Context):
        yield from utils.assert_bake_socket_context(context)
    
    bake_queue: queue.BakingQueue
    socket_selector = al.BoolVectorProperty(name='Socket Selection', size=utils.MAX_SOCKETS_IN_SELECTOR, default=tuple([False]*utils.MAX_SOCKETS_IN_SELECTOR))

    def invoke(self, context: bt.Context, event: bt.Event):
        self.bake_queue = queue.BakingQueue.get_from(context.object)
        self.socket_map_matches = utils.assign_sockets_to_map_types(context.active_node.outputs)
        for i in range(len(self.socket_map_matches)):
            t, s = self.socket_map_matches[i]
            self.pre_filter_socket(i, t, s)
        return al.get_wm().invoke_props_dialog(self)
    
    def pre_filter_socket(self, index: int, map_type: utils.MapType, socket: bt.NodeSocket):
        enabled_default = type in utils.MapType.explicit() and self.bake_queue.is_map_available(map_type)
        self.socket_selector.set_value_at(index, enabled_default)

    def draw_line(self, layout: bt.UILayout, index: int, map_type: utils.MapType, socket: bt.NodeSocket):
        self.socket_selector.draw_ui(layout, options=al.UIOptionsProp(text=f'{utils.get_socket_display_name(socket)} -> {map_type.name}', index=index, toggle=1)) 

    def draw(self, context: bt.Context):
        col = al.UI.column(self.layout, align=True)
        for i, (type, socket) in enumerate(self.socket_map_matches):
            self.draw_line(al.UI.row(col), i, type, socket)


@al.register_operator
class SelectSocketsForBaking(SocketOperator):

    def draw_line(self, layout: bt.UILayout, index: int, map_type: utils.MapType, socket: bt.NodeSocket):
        layout.enabled = self.bake_queue.is_map_available(map_type)
        super().draw_line(layout, index, map_type, socket)
    
    def run(self, context: bt.Context):
        
        obj = context.object
        baking_queue = queue.BakingQueue.get_from(obj)
        for i in range(len(self.socket_map_matches)):
            if not self.socket_selector()[i]:
                continue
            type, socket = self.socket_map_matches[i]
            baking_queue.add_map(type, socket, socket.name)

        al.Window.redraw_all_regions()



@al.register_operator
class AddNewEmptyMaps(SanctusBakeOp):
    
    selection = al.BoolVectorProperty(size=len(utils.MapType), default=tuple([False] * len(utils.MapType)))
    available_maps: list[utils.MapType]

    def invoke(self, context: bt.Context, event: bt.Event):
        self.available_maps = [x for x in utils.MapType if self.get_baking_queue(context).is_map_available(x)]
        return al.get_wm().invoke_props_dialog(self)
    
    def draw(self, context: bt.Context):
        col = al.UI.column(self.layout)
        for i, map_type in enumerate(self.available_maps):
            self.selection.draw_ui(col, al.UIOptionsProp(text=map_type.name, index=i, toggle=1))

    def run(self, context: bt.Context):
        q = self.get_baking_queue(context)
        for new_map_type in (x for i, x in enumerate(self.available_maps) if self.selection()[i]):
            q.add_map(new_map_type, socket=None)

        al.Window.redraw_all_regions()

def get_socket_items(self, context: bt.Context):
    outputs = context.active_node.outputs
    outputs = [x for x in outputs if not type(x) in utils.INVALID_SOCKET_TYPES]
    return [(x.identifier, x.name, x.name) for x in outputs]


@al.register_operator
class AddSocketToMap(SanctusBakeOp):

    @classmethod
    def get_asserts(cls, context: bt.Context):
        yield from utils.assert_bake_socket_context(context)
    
    bake_map = al.ContextProperty[queue.BakeMap]()

    selection = al.BoolVectorProperty(size=utils.MAX_SOCKETS_IN_SELECTOR)

    valid_sockets: list[bt.NodeSocket]

    def invoke(self, context: bt.Context, event: bt.Event):
        self.valid_sockets = [x for x in context.active_node.outputs if utils.filter_baking_socket(x)]
        self.selection.set_value([False] * utils.MAX_SOCKETS_IN_SELECTOR)
        return al.get_wm().invoke_props_dialog(self)
    
    def draw(self, context: bt.Context):
        col = al.UI.column(self.layout)
        for i, socket in enumerate(self.valid_sockets):
            self.selection.draw_ui(col, al.UIOptionsProp(text=utils.get_socket_display_name(socket), index=i, toggle=1))
        
        if len([x for x in self.selection() if x]) > 1:
            al.UI.label(al.UI.alert(col), "Only 1 Socket can be added from one material", icon=al.BIcon.ERROR)

    def run(self, context: bt.Context):
        for i, socket in enumerate(self.valid_sockets):
            if self.selection()[i]:
                self.bake_map().add_socket_path(socket)
                break


        al.Window.redraw_all_regions()


@al.register_draw_function(bt.NODE_MT_context_menu)
def draw_new_socket_select_menu(self: bt.Menu, context: bt.Context):
    from .. import library_manager
    self.layout.operator_context = al.BOperatorContext.INVOKE_DEFAULT()
    SelectSocketsForBaking().draw_ui(self.layout, al.UIOptionsOperator(icon=library_manager.MANAGER.icon_id(Path('icons/icon'))))


@al.register_operator
class Bake(al.Operator):

    result_map: list[tuple[queue.BakeMap, bt.Image]]
    bake_queue: queue.BakingQueue
    oh: override_handler.OverrideHandler

    @classmethod
    def get_asserts(cls, context: bt.Context):
        yield from utils.assert_baking_context(context)
        yield al.OperatorAssert(lambda: ui.SanctusIsBaking.get(al.get_wm()).value == False, 
            'Waiting for current bake to finish. (If no bake is in progress, please restart Blender)')
        bake_queue = queue.BakingQueue.get_from(context.object)
        yield al.OperatorAssert(lambda: bake_queue.is_valid(), "Invalid bake maps. (Maps cannot have type overlap or invalid socket paths)")

    def invoke(self, context: bt.Context, _event):
        ui.SanctusIsBaking.get(al.get_wm()).value = True
        context.area.tag_redraw()
        al.get_wm().modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        return self.execute(context)


    def run(self, context: bt.Context):
        
        self.result_map = []
        self.bake_queue = queue.BakingQueue.get_from(context.object)
        self.oh = override_handler.OverrideHandler()

        self.oh.override(context.scene.cycles, 'samples', 1)
        self.bake_materials(context)
        if self.bake_queue.settings().bake_decals():
            self.bake_decals(context)
        
        self.oh.restore()
        ui.SanctusIsBaking.get(al.get_wm()).value = False

        from . import texture_sets

        override_sets = self.bake_queue.settings().override_sets()

        texture_set_manager = texture_sets.TextureSetManager.get_from(context.scene)
        set_data = [(m.map_type(), f'{context.object.name}_{m.get_map_name()}', image) for m, image in self.result_map]
        texture_set_manager.add_set(context.object, set_data, override_sets=override_sets)

        al.Window.redraw_all_regions()

        
    def bake_materials(self, context: bt.Context):
        
        queue_settings = self.bake_queue.settings()
        resolution = queue_settings.get_resolution()
    
        for bake_map in self.bake_queue.get_valid_maps():
            image = utils.create_new_image("_" + bake_map.get_map_name(), resolution, override=False)

            bake_setups: list[setup.BakeSetup] = []

            bake_map_default_value = bake_map.map_type().get_default_value()
            for material in (x.material for x in context.object.material_slots if x is not None):
                socket = bake_map.get_socket_for_material(material)
                if socket is not None:
                    bake_setups.append(setup.BakeSetup(material, image, socket))
                else:
                    s = setup.BakeSetup(material, image, None)
                    s.connect_default_value(bake_map_default_value)
                    bake_setups.append(s)

            self.oh.override(context.scene.cycles, 'samples', bake_map.samples())

            try:
                bake_args = utils.get_texture_bake_args(self.oh, context.scene.render.bake, margin=queue_settings.margin())
                if(queue_settings.use_auto_margin()):
                    utils.set_bake_args_auto_margin(bake_args, resolution)
                
                utils.bake(bake_args)
            except Exception as e:
                bpy.data.images.remove(image)
                raise e
            finally:
                for s in bake_setups: s.clean_up()
            
            utils.finalize_bake_texture(image, bake_map.get_map_colorspace())
            self.result_map.append((bake_map, image))

    def bake_decals(self, context: bt.Context):
        from .. import decals, image_processing as ip, img_tools, node_utils

        obj = context.object    
        bake = context.scene.render.bake
        decal_children = decals.get_decal_children(context.object)
        if len(decal_children) < 1:
            return
        
        max_decal_offset = -9999999

        bake_queue_settings = self.bake_queue.settings()
        decal_distance = bake_queue_settings.ray_distance()
        if bake_queue_settings.use_auto_bake_settings():
            for dec in decal_children:
                decal_settings = decals.SanctusDecalSettings.get_from(dec)
                mod = decal_settings.get_decal_nodes_modifier()
                offset = node_utils.get_gn_parameter(mod, "Offset") / 100
                max_decal_offset = max(max_decal_offset, offset)
            decal_distance = 0.02
        
        bake_max_ray_distance = decal_distance * context.object.scale.length
        bake_cage_extrusion = decal_distance * 1.2
        
        old_objects = [x for x in bpy.data.objects.values()]
        with utils.selected_objs_context(context, decal_children):
            bo.object.duplicate()
        duplicates = [x for x in bpy.data.objects if not x in old_objects]
        with utils.selected_objs_context(context, duplicates):
            bo.object.convert(target="MESH")
        with utils.selected_objs_context(context, duplicates):
            bo.object.join()
        
        temp_decal_bake_object = next(x for x in bpy.data.objects.values() if not x in old_objects)
        
        materials = [x.material for x in obj.material_slots if x.material is not None]
        bake_setups = [setup.BakeSetup(x, None, None) for x in materials]

        for bake_map, image in self.result_map:
            map_type = bake_map.map_type()
            if not map_type in utils.MapType.explicit():
                continue
            
            try:
                for d in decal_children: utils.set_decal_bake_link(d, map_type)
            except utils.BakeSetupError as e:
                print(f'Could not setup bake links for map type "{map_type.name}". Error Message:', str(e), sep='\n')
                continue
            
            temp_img = utils.create_new_image(f'{image.name}_DECAL', tuple(image.size), override=False)

            # SETUP
            for s in bake_setups: s.set_image(temp_img)
            
            
            self.oh.override(context.scene.cycles, 'samples', bake_map.samples())

            # BAKE
            try:
                with utils.decal_bake_context(context, obj, [temp_decal_bake_object]):
                    bake_args = utils.get_decal_bake_args(self.oh, bake, bake_max_ray_distance, bake_cage_extrusion)
                    utils.bake(bake_args)
            except Exception as e:
                bpy.data.images.remove(temp_img)
                raise e
            
            # FINALIZE DECAL BAKE
            img_tools.un_premul_alpha(temp_img)
            utils.finalize_bake_texture(temp_img, map_type.get_colorspace())

            # BLEND
            background = ip.read_image(image)
            foreground = ip.read_image(temp_img)
            result = ip.overlay_image(background, foreground)
            if map_type.get_colorspace() == utils.ColorSpace.SRGB:
                result = ip.linear_to_srgb(result)
            ip.set_image(image, result)
            
            # FINALIZE RESULT
            utils.finalize_bake_texture(image, map_type.get_colorspace(), skip_conversion=True)
            bpy.data.images.remove(temp_img)
    
        # CLEAN UP
        for d in decal_children: utils.reset_decal_bake_link(d)
        for s in bake_setups: s.clean_up()
        bpy.data.objects.remove(temp_decal_bake_object)
        

@al.register_operator
class PopupImage(al.Operator):
    bl_label = 'Show Image'
    bl_description = 'Open the image in a new Blender Window'

    image = al.ContextProperty[bt.Image]()

    def run(self, context: bt.Context):
        image = self.image()
        if image is None:
            self.report({'ERROR'}, f'Operator requires an Image to be passed')
            return {al.BOperatorReturn.CANCELLED()}
        if not isinstance(image, bt.Image):
            self.report({'ERROR'}, f'Object passed: {image} is not an image')
            return {al.BOperatorReturn.CANCELLED()}
        wm = al.get_wm()
        old_windows = list(wm.windows.values())
        bpy.ops.wm.window_new()
        new_window: bt.Window = next(x for x in wm.windows.values() if not x in old_windows)
        area = new_window.screen.areas[0]
        area.ui_type = 'IMAGE_EDITOR'
        s: bt.SpaceImageEditor = area.spaces[0]
        s.image = image


class InstantiateOperator(base_ops.SanctusOperator):

    al_asserts = [
        utils.assert_shader_context(),
    ]

    def run(self, context: bt.Context):

        space: bt.SpaceNodeEditor = context.space_data
        self.node_tree: bt.ShaderNodeTree = space.edit_tree
        self.cursor_loc = space.cursor_location
        self.nodes: list[bt.Node] = []

        self.add_nodes(context)

        for n in self.node_tree.nodes:
            n: bt.Node
            n.select = n in self.nodes
        
        bo.transform.translate('INVOKE_DEFAULT')

    def add_nodes(self, context: bt.Context):
        pass

@al.register_operator
class InstantiateImages(InstantiateOperator):
    bl_description = 'Add images as nodes in active shader node tree'

    images = al.ContextListProperty[bt.Image]()

    def add_nodes(self, context: bt.Context):

        images = self.images()

        for i, image in enumerate(images):
            n: bt.ShaderNodeTexImage = self.node_tree.nodes.new('ShaderNodeTexImage')
            n.image = image
            n.hide = True
            n.location = self.cursor_loc - Vector((0, 40 * i))
            self.nodes.append(n)


@al.register_operator
class InstantiatePBRSetup(InstantiateOperator):
    bl_description = 'Add images as PBR setup in active shader node tree'

    texture_set = al.ContextProperty[texture_sets.TextureSet]()

    def add_nodes(self, context: bt.Context):

        pbr_node: bt.ShaderNodeBsdfPrincipled = self.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
        pbr_node.inputs['Emission Strength'].default_value = 1
        pbr_node.inputs['Emission Color'].default_value = (0,0,0,1)
        pbr_node.location = self.cursor_loc + Vector((150, 0))
        self.nodes.append(pbr_node)

        pbr_textures = [x for x in self.texture_set().textures() if x.map_type() in utils.MapType.explicit()]
        for i, tex in enumerate(pbr_textures):
            n: bt.ShaderNodeTexImage = self.node_tree.nodes.new('ShaderNodeTexImage')
            n.image = tex.texture()
            n.hide = True
            n.location = self.cursor_loc + Vector((-150, -40 * i))

            self.connect_nodes(n, tex.map_type(), pbr_node)

            self.nodes.append(n)

    def connect_nodes(self, image_node: bt.ShaderNodeTexImage, map_type: utils.MapType, pbr_node: bt.ShaderNodeBsdfPrincipled):
        input_name = utils.map_type_to_pbr_socket_name(map_type)
        
        links = self.node_tree.links

        if map_type == utils.MapType.NORMAL:
            normal_map_node: bt.ShaderNodeNormalMap = self.node_tree.nodes.new('ShaderNodeNormalMap')
            self.nodes.append(normal_map_node)
            normal_map_node.hide = True
            normal_map_node.location = pbr_node.location + Vector((0, -330))
            links.new(image_node.outputs[0], normal_map_node.inputs['Color'])
            links.new(normal_map_node.outputs[0], pbr_node.inputs[input_name])
            return
        elif map_type == utils.MapType.DISPLACEMENT:
            displace_node: bt.ShaderNodeDisplacement = self.node_tree.nodes.new('ShaderNodeDisplacement')
            self.nodes.append(displace_node)
            displace_node.hide = True
            displace_node.location = pbr_node.location + Vector((0, -370))
            links.new(image_node.outputs[0], displace_node.inputs['Height'])
            return
        
        if input_name in pbr_node.inputs.keys():
            links.new(image_node.outputs[0], pbr_node.inputs[input_name])


@al.register_operator
class ClearBakingQueue(SanctusBakeOp):
    bl_description = 'Remove all the current bake sockets from the baking queue'

    def invoke(self, context: bt.Context, event: bt.Event):
        return al.get_wm().invoke_confirm(self, event)

    def run(self, context: bt.Context):
        self.get_baking_queue(context).bake_maps.clear()
        al.Window.redraw_all_regions()
        ui.SanctusIsBaking.get(al.get_wm()).value = False
