
import bmesh
import math

from .. import auto_load as al
from ..auto_load.common import *
from ..auto_load import geo

from .. import base_ops
from . import modals

from .. import decals
from .. import node_utils
from .. import asset
from .. import poll


def _create_decal(context: bt.Context, target: bt.Object, image: bt.Image, sticker_material: bt.Material, gn_group: bt.GeometryNodeTree):

    sticker_material.name = image.name + ' SL Material'
    img_node: bt.ShaderNodeTexImage = sticker_material.node_tree.nodes[decals.MATERIAL_IMAGE_NODE_NAME]
    img_node.image = image

    new_mesh = bpy.data.meshes.new('SL Empty Sticker Mesh')
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5, calc_uvs=True)
    bm.to_mesh(new_mesh)
    if bpy.app.version < (4,1,0):
        new_mesh.use_auto_smooth = True
        new_mesh.auto_smooth_angle = math.pi / 6
    else:
        new_mesh.shade_smooth()
    obj = bpy.data.objects.new(image.name + ' Projector', new_mesh)
    obj.visible_shadow = False

    scene_collection = context.scene.collection
    coll = next((x for x in scene_collection.children_recursive if x.name == decals.DECAL_COLLECTION_NAME), None)
    if coll is None:
        coll = bpy.data.collections.new(decals.DECAL_COLLECTION_NAME)
        scene_collection.children.link(coll)

    base_ops.link_and_select_object(context, obj, coll)

    gn_mod: bt.NodesModifier = obj.modifiers.new(decals.DECAL_MODIFIER_NAME, al.BObjectModifierType.NODES())
    gn_mod.node_group = gn_group

    transfer_mod: bt.DataTransferModifier = obj.modifiers.new(decals.TRANSFER_MODIFIER_NAME, al.BObjectModifierType.DATA_TRANSFER())
    transfer_mod.use_loop_data = True
    transfer_mod.data_types_loops = {'CUSTOM_NORMAL'}
    transfer_mod.loop_mapping = 'POLYINTERP_LNORPROJ'

    decal_settings = decals.SanctusDecalSettings.get_from(obj)
    decal_settings.is_decal.value = True
    decal_settings.set_references(sticker_material, target, image)

    return obj



class PlaceDecal(base_ops.SanctusAssetImportOperator):
    bl_description = 'Add decal to the scene'
    asset_type = asset.Type.IMAGES
    use_reimport_prompt = False

    decal_size_rate = 0.1
    decal_rotation_rate = math.pi / 20

    custom_image_path = al.StringProperty()
    replace_existing_decal = False
    target_is_valid = False
    objects_to_hide = set()

    al_asserts = [modals.GIZMO_RUNNING_ASSERT]

    def set_decal_size_change_rate(self):
        self.decal_size_rate = max(self.decal_scale * 0.2, 0.01)

    def get_non_local_view_objects(self, context):
        space_view_3d = context.space_data

        if type(space_view_3d) != bt.SpaceView3D: # will crash if space_view_3d is None
            raise TypeError(f'The context is incorrect. For context.space_data expected a SpaceView3D type, not {type(space_view_3d)}')
        
        depsgraph = context.evaluated_depsgraph_get()
        objects = context.scene.objects

        local_objects = {obj for obj in objects if obj.evaluated_get(depsgraph).visible_in_viewport_get(space_view_3d)}

        objects_to_hide = set(obj for obj in context.scene.objects if 
            (obj not in local_objects) and not (obj.hide_viewport))
    
        return objects_to_hide

    def hide_non_local_objects(self):
        for obj in self.objects_to_hide:
            obj.hide_viewport = True

    def show_non_local_objects(self):
        for obj in self.objects_to_hide:
            obj.hide_viewport = False

    def invoke(self, context: bt.Context, event: bt.Context) -> set[str]:
        from .. import preferences
        
        modals.SET_GIZMO_RUNNING(True)

        self.raycast_hit = geo.FAILED_RAYHIT
        self.loaded_image = None
        self.decal_scale = 0.5
        self.decal_angle: float = 0.0
        self.set_decal_size_change_rate()
        self._current_obj = context.object
        if self.replace_existing_decal:
            mod = decals.SanctusDecalSettings.get_from(self._current_obj).get_decal_nodes_modifier()
            self.decal_scale = mod[node_utils.gn_input_identifier(mod.node_group, 'Scale')]
            self.loaded_image = mod[node_utils.gn_input_identifier(mod.node_group, 'Image')]
            self.decal_angle = mod[node_utils.gn_input_identifier(mod.node_group, 'Rotation')] * math.pi
        if self.loaded_image is None:
            self.loaded_image = self.load_image()
        imgs = self.loaded_image.size
        self.aspect_ratio = Vector((1, imgs[1]/imgs[0]))
        self.objects_to_hide = self.get_non_local_view_objects(context)

        prefs = al.get_prefs()
        if prefs.interface().center_mouse_on_gizmos():
            geo.center_mouse_in_window(context)

        modals.ModalHelper.add_draw_handler_view(self, self.draw_gpu, (context,))
        bt.WindowManager.modal_handler_add(self)

        self.hide_non_local_objects()
        return {'RUNNING_MODAL'}

    def modal(self, context: bt.Context, event: bt.Event) -> set[str]:
        try:
            context.area.tag_redraw()
            if modals.ModalHelper.is_event_cancel(event):
                self.raycast_hit = geo.FAILED_RAYHIT
                return self.execute(context)

            self.raycast_hit = geo.raycast_scene_view(context, context.evaluated_depsgraph_get(), geo.mouse_vector_from_event(event))
            self.target_is_valid = self.raycast_hit.is_hit
            if self.replace_existing_decal and self.raycast_hit.obj == self._current_obj:
                self.target_is_valid = False
            if modals.ModalHelper.is_event_confirm(event) and self.target_is_valid:
                return self.execute(context)
            
            if modals.ModalHelper.is_event_shift_release(event):
                self.set_decal_size_change_rate()

            if modals.ModalHelper.is_event_shift_pressed(event):
                if self.raycast_hit.is_hit and (change := modals.ModalHelper.get_event_scroll(event)) != 0:
                    self.decal_scale+= change * self.decal_size_rate
                    self.decal_scale = max(0, self.decal_scale)
                    return {'RUNNING_MODAL'}
            
            if modals.ModalHelper.is_event_ctrl_pressed(event):
                if self.raycast_hit.is_hit and (change := modals.ModalHelper.get_event_scroll(event)) != 0:
                    self.decal_angle += change * self.decal_rotation_rate
                    return {'RUNNING_MODAL'}
            
            return {'PASS_THROUGH'}
        
        except Exception:
            self.cancel(context)
            return {'CANCELLED'}

    def cancel(self, context: bt.Context):
        self.report({'INFO'}, f'Context was changed, cancelled execution of "{self.bl_label}" operator.')
        modals.ModalHelper.remove_draw_handler_view(self)
        modals.SET_GIZMO_RUNNING(False)

    def draw_gpu(self, context: bt.Context):
        import numpy as np
        from numpy import array as ar
        import blf

        p = bpy.context.preferences
        fid = 0

        blf.position(fid, 20, 20, 0)
        blf.color(fid, 1, 1, 1, 1)
        blf.size(fid, 15)
        
        blf.draw(fid, 'Confirm Decal: [Left Click]      Cancel Placement: [Esc]     Resize Decal: [Shift + Mouse Wheel]     Rotate Decal: [Ctrl + Mouse Wheel]')

        hit = self.raycast_hit
        if not hit.is_hit:
            return
        
        lookat = Matrix(geo.lookat_matrix(hit.normal))
        hit_loc_2D = geo.loc3D_to_2D(hit.location, context)
        hit_end_2D = geo.loc3D_to_2D(hit.location + hit.normal * 0.5, context)

        pivot_color = (1, 1, 0.8, 1)
        normal_color = (0.4, 1, 0.6, 1)
        wire_color = (0.3, 0.8, 0.3, 1)

        if not self.target_is_valid:
            pivot_color = (1, 0.9, 0.3, 1)
            normal_color = (1, 0.6, 0.4, 1)
            wire_color = (0.8, 0.3, 0.3, 1)

        data = geo.GeoBuffer.empty(2)

        
        if self.decal_scale > 0:
            # borders
            corners = [Vector((-.5, -.5)), Vector((.5, -.5)), Vector((.5, .5)), Vector((-.5, .5))]
            corners: list[Vector] = [x * self.decal_scale * self.aspect_ratio for x in corners]
            corners = [geo.rotation2d(-self.decal_angle) @ x for x in corners] # temporarily change vectors to numpy arrays
            corners = [Vector((v[0], v[1], 0)) for v in corners]
            corners2D = [geo.loc3D_to_2D(hit.location + (lookat @ offset), context) for offset in corners]

            data += geo.Shape2D.polygon_wire(corners2D, line_width=3, circle_radius=1.5, circle_segments=12, color=wire_color)

            # triangle
            triangle_offsets = [Vector((-.2, .2)), Vector((.2, .2)), Vector((0, .4))]
            triangle_offsets = [geo.rotation2d(-self.decal_angle) @ x for x in triangle_offsets]
            triangle_offsets = [Vector((v[0], v[1], 0)) for v in triangle_offsets]
            triangle_offsets = [x * self.decal_scale for x in triangle_offsets]
            triangle2D = [geo.loc3D_to_2D(hit.location + (lookat @ offset), context) for offset in triangle_offsets]
            data += geo.Shape2D.polygon_wire(triangle2D, line_width=3, circle_radius=1.5, circle_segments=12, color=wire_color)

        # normal
        normal_line = geo.Shape2D.rect_line(hit_loc_2D, hit_end_2D, 3, color=normal_color)
        normal_line.set_colors(lambda uv, i, pos: geo.lerp(ar(pivot_color), ar(normal_color), uv[1]))
        data += normal_line
        data += geo.Shape2D.circle(hit_end_2D, radius=5, segments=10, color=normal_color)

        # center point
        data += geo.Shape2D.circle(hit_loc_2D, radius=5, segments=12, color=pivot_color)

        geo.render_vcol(data)

    def run(self, context: bt.Context):
        self.show_non_local_objects()

        modals.ModalHelper.remove_draw_handler_view(self)

        modals.SET_GIZMO_RUNNING(False)

        hit = self.raycast_hit
        if not hit.is_hit:
            return {al.BOperatorReturn.CANCELLED()}

        target = hit.obj
        if not self.replace_existing_decal:
            gn_importer = asset.ImportManager(decals.get_decal_group_path(), asset.Type.NODE_GROUPS)
            gn_group = gn_importer.get_asset(reimport=False)
            material_importer = asset.ImportManager(decals.DECAL_MATERIAL_PATH, asset.Type.MATERIALS)
            sticker_mat = material_importer.get_asset(reimport=True)

            obj = _create_decal(context, target, self.loaded_image, sticker_mat, gn_group)
        else:
            obj = self._current_obj
            if obj == target:
                return {"CANCELLED"}
            

        decal_settings = decals.SanctusDecalSettings.get_from(obj)
        mod = decal_settings.get_decal_nodes_modifier()

        if self.replace_existing_decal:
            decal_settings.set_target(target)
            decal_settings.set_image(self.loaded_image) # ensure that the image is there in case its missing

        mod[node_utils.gn_input_identifier(mod.node_group, 'Scale')] = float(self.decal_scale)
        mod[node_utils.gn_input_identifier(mod.node_group, 'Rotation')] = float(self.decal_angle) / math.pi
        obj.parent = target
        geo.set_location_and_direction(obj, hit.location, hit.normal)

    def load_image(self):
        if self.custom_image_path() != '':
            image = bpy.data.images.load(self.custom_image_path(), check_existing=True)
        else:
            image: bt.Image = self.get_importer().get_asset(self.reimport_asset())
        return image

@al.register_operator
class AddDecal(PlaceDecal):
    pass

@al.register_operator
class RepositionDecal(PlaceDecal):

    replace_existing_decal = True

    @classmethod
    def get_asserts(cls, context: bt.Context):
        yield from super().get_asserts(context)
        yield al.OperatorAssert(lambda c: c.object is not None, 'No active object selected.')
        decal_settings = decals.SanctusDecalSettings.get_from(context.object)
        yield al.OperatorAssert(lambda c: decal_settings.is_decal(), 'Object is not a decal.')

@al.register_operator
class AddCustomDecal(base_ops.SanctusFilepathOperator):
    bl_label = 'Add Custom'
    bl_description = 'Add decal to the scene with a custom image'

    al_asserts = [modals.GIZMO_RUNNING_ASSERT]
        
    def set_defaults(self, context: bt.Context, event: bt.Event):
        self.filter_image = True
        self.filter_folder = True
        self.check_existing = False
        self.Filepath = context.preferences.filepaths.texture_directory

    def run(self, context: bt.Context):
        op = AddDecal(custom_image_path=self.Filepath)
        op.call(context)

    def draw(self, context: bt.Context) -> None:
        self.layout.label(text='Select an image as a custom decal.')


@al.register_operator
class SwapDecalImage(base_ops.SanctusAssetImportOperator):
    bl_label = 'Swap Image'
    bl_description = 'Swap out the image on the current decal'
    asset_type = asset.Type.IMAGES
    use_reimport_prompt = False
    al_asserts = [
        al.OperatorAssert(poll.is_object_type(types='MESH'), 'Active object is not of type “MESH”.'),
        al.OperatorAssert(lambda c: c.object in c.selected_objects, 'No active object selected.'),
        al.OperatorAssert(lambda c: c.object.active_material is not None, 'Object has no active material.'),
        
        al.OperatorAssert(lambda c: decals.SanctusDecalSettings.get_from(c.object).is_decal(), 'Object is not a decal.'),
        al.OperatorAssert(lambda c: decals.SanctusDecalSettings.get_from(c.object).can_set_image(), 'Decal image is not modifiable.'),
    ]

    def run(self, context: bt.Context):

        obj = context.object
        decal_settings = decals.SanctusDecalSettings.get_from(obj)
        mod = decal_settings.get_decal_nodes_modifier()
        img: bt.Image = self.get_importer().get_asset(self.reimport_asset())
        decal_settings.set_image(img)
        # Update depsgraph to register changes in GN
        mod.show_viewport = False
        context.view_layer.update()
        mod.show_viewport = True
        
@al.register_operator
class ToggleDecalNormals(base_ops.SanctusOperator):

    bl_label = 'Toggle Normal Edit'
    bl_description = 'Toggle Normal Edit to check which one has better shading'
    al_asserts = [
        al.OperatorAssert(poll.is_object_type(types='MESH'), 'Active object is not of type “MESH”.'),
        al.OperatorAssert(lambda c: c.object in c.selected_objects, 'No active object selected.'),
        al.OperatorAssert(lambda c: c.object.active_material is not None, 'Object has no active material.'),
        al.OperatorAssert(lambda c: decals.SanctusDecalSettings.get_from(c.object).is_decal(), 'Object is not a decal.'),
    ]
    
    def run(self, context: bt.Context):
        
        obj = context.object
        settings = decals.SanctusDecalSettings.get_from(obj)
        normals_modifier = settings.get_decal_normals_modifier()
        if normals_modifier is None:
            self.report({"WARNING"}, "Decal Normal Transfer Modifier not found.")
            return
        
        was_activated = normals_modifier.show_viewport
        normals_modifier.show_viewport = not was_activated
        normals_modifier.show_render = not was_activated

