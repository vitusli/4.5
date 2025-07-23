
from .. import auto_load as al
from ..auto_load.common import *

from .. import base_ops
from . import modals

from .. import meta_data as md
from .. import node_utils
from .. import asset
from .. import poll


@al.register_operator
class GNAddNew(base_ops.SanctusAssetImportOperator):
    bl_label = md.GeometryNodeAssetType.ADD_NEW.get_name()
    bl_description = md.GeometryNodeAssetType.ADD_NEW.get_description()
    asset_type = asset.Type.OBJECTS
    use_reimport_prompt = False

    def run(self, context: bt.Context):
        obj = self.get_importer().get_asset(reimport=True)
        base_ops.link_and_select_object(context, obj)


@al.register_operator
class GNApplyMesh(base_ops.SanctusAssetImportOperator):
    bl_label = md.GeometryNodeAssetType.APPLY_MESH.get_name()
    bl_description = md.GeometryNodeAssetType.APPLY_MESH.get_description()
    asset_type = asset.Type.NODE_GROUPS
    use_reimport_prompt = False
    al_asserts: list[al.OperatorAssert] = [
        al.OperatorAssert(lambda c: c.active_object in c.selected_objects, 'No active object selected.', strict=False),
        al.OperatorAssert(poll.is_object_type(types='MESH'), 'Active object is not of type “MESH”.'),
    ]

    def run(self, context: bt.Context):
        nt: bt.GeometryNodeTree = self.get_importer().get_asset(self.reimport_asset())
        obj: bt.Object = context.object
        mod: bt.NodesModifier = obj.modifiers.new(nt.name, 'NODES')
        mod.node_group = nt

@al.register_operator
class GNApplyCurve(base_ops.SanctusAssetImportOperator):
    bl_label = md.GeometryNodeAssetType.APPLY_CURVE.get_name()
    bl_description = md.GeometryNodeAssetType.APPLY_CURVE.get_description()
    asset_type = asset.Type.NODE_GROUPS
    use_reimport_prompt = False
    al_asserts: list[al.OperatorAssert] = [
        al.OperatorAssert(lambda c: c.active_object in c.selected_objects, 'No active object selected.', strict=False),
        al.OperatorAssert(poll.is_object_type(types='CURVE'), 'Active object is not of type “CURVE”.'),
    ]

    def run(self, context: bt.Context):
        nt: bt.GeometryNodeTree = self.get_importer().get_asset(self.reimport_asset())
        obj: bt.Object = context.object
        mod: bt.NodesModifier = obj.modifiers.new(nt.name, 'NODES')
        mod.node_group = nt

@al.register_operator
class GNApplyParentedCurve(base_ops.SanctusAssetImportOperator):
    bl_label = "Apply"
    bl_description = md.GeometryNodeAssetType.APPLY_PARENTED_CURVE.get_description()
    asset_type = asset.Type.NODE_GROUPS
    use_reimport_prompt = False
    al_asserts: list[al.OperatorAssert] = [
        al.OperatorAssert(lambda c: c.active_object in c.selected_objects, 'No active object selected.', strict=False),
        al.OperatorAssert(poll.is_object_type(types='MESH'), 'Active object is not of type “MESH”.'),
    ]

    TARGET_SUFFIX = "_target"

    @staticmethod
    def get_hair_modifiers(obj):
        for modifier in obj.modifiers:
            tree = getattr(modifier, "node_group", None)

            if getattr(tree, "bpe_prop_sanctus_is_hair_asset", False):
                yield modifier
        
    def get_hair_children(self, obj):
        for child in obj.children:
            modifiers = tuple(self.get_hair_modifiers(child))
            if len(modifiers) > 0:
                yield child

    def has_hair_asset(self, obj):
        modifiers = tuple(self.get_hair_modifiers(obj))
        children = tuple(self.get_hair_children(obj))

        if len(modifiers) + len(children) >0:
            return True
    
    def clear_hair_asset(self, context, obj):
        hair_modifiers = tuple(self.get_hair_modifiers(obj))
        children = tuple(self.get_hair_children(obj))

        objects = context.blend_data.objects
        modifiers = obj.modifiers

        for child in children:
            objects.remove(child)

        for hair_modifier in hair_modifiers:
            modifiers.remove(modifiers[hair_modifier.name])

    def draw(self, context):
        col = self.layout.column(align=True)
        col.label(text="There's already a hair asset applied.")
        col.label(text="Do you want to replace it?")

    def run(self, context: bt.Context):
        importer = self.get_importer()
        asset_name = importer.asset_instance.name
        obj: bt.Object = context.object
        
        match_materials = importer.asset_instance.asset.meta.match_materials

        if self.has_hair_asset(obj):
            self.clear_hair_asset(context, obj)
        
        curve_tree: bt.GeometryNodeTree = importer.get_asset(self.reimport_asset())
        curve_mat: bt.Material = importer.load_buddy_asset(asset_name, asset.Type.MATERIALS, make_unique=True)
        target_tree: bt.GeometryNodeTree = importer.load_buddy_asset(f"{asset_name}{self.TARGET_SUFFIX}", asset.Type.NODE_GROUPS)
        target_mat: bt.Material = curve_mat if match_materials else importer.load_buddy_asset(f"{asset_name}{self.TARGET_SUFFIX}", asset.Type.MATERIALS, make_unique=True)

        bpy.ops.object.curves_empty_hair_add(align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
        curve : bt.HairCurve = context.object

        modifiers = curve.modifiers
        modifiers.clear()
        
        curve_mod = modifiers.new(curve_tree.name, 'NODES')
        curve_mod.node_group = curve_tree
        curve_tree.sanctus_is_hair_asset.value = True
        _try_assign_gn_properties(curve_mod, ('Target Object', obj))
        _try_assign_gn_properties(curve_mod, ('Curves Material', curve_mat))

        if target_tree is not None:
            obj_modifiers = obj.modifiers
            target_mod = obj_modifiers.new(target_tree.name, 'NODES')
            target_mod.node_group = target_tree
            target_tree.sanctus_is_hair_asset.value = True

            # Move modifier to top
            obj_modifiers.move(len(obj_modifiers) - 1, 0)
            
        if curve_mat is not None:
            curve.active_material = curve_mat

        if target_mat is not None:
            obj.active_material = target_mat

    def invoke(self, context, _event):
        if self.has_hair_asset(context.object):
            return context.window_manager.invoke_props_dialog(self,
                title="",
                confirm_text="Replace",
                width=250
                )
        else:
            return self.execute(context) 


def _create_new_object(context: bt.Context, name: str, data: bt.ID):

    obj = bpy.data.objects.new(name, data)
    obj.matrix_world = context.scene.cursor.matrix
    base_ops.link_and_select_object(context, obj)
    return obj

def _create_new_gn_curve_object(context: bt.Context, nt: bt.GeometryNodeTree, name: str):
    
    new_curve = bpy.data.curves.new(name, al.BObjectTypeCurve.CURVE())
    obj = _create_new_object(context, name, new_curve)
    mod: bt.NodesModifier = obj.modifiers.new(nt.name, 'NODES')
    mod.node_group = nt
    return (obj, mod)

def _try_assign_gn_properties(modifier: bt.NodesModifier, *parameters: tuple[tuple[str, Any]]):
        
    for attr, value in parameters:
        try:
            identifier = node_utils.gn_input_identifier(modifier.node_group, attr)
            modifier[identifier] = value
        except StopIteration:
            pass

@al.register_operator
class GNDrawFree(base_ops.SanctusAssetImportOperator):
    bl_label = md.GeometryNodeAssetType.DRAW_FREE.get_name()
    bl_description = md.GeometryNodeAssetType.DRAW_FREE.get_description()
    asset_type = asset.Type.OBJECTS
    use_reimport_prompt = False

    def run(self, context: bt.Context):
        importer = self.get_importer()
        new_name = f'{importer.asset_instance.display_name} Drawing'
        obj: bt.Object = importer.get_asset(reimport=True)
        base_ops.link_and_select_object(context, obj)
        obj.name = new_name
        obj.data.name = new_name
        
        context.scene.tool_settings.curve_paint_settings.depth_mode = 'CURSOR'
        bo.object.mode_set(mode='EDIT')
        bo.wm.tool_set_by_id(name='builtin.draw')

@al.register_operator
class GNDrawSurface(base_ops.SanctusAssetImportOperator):
    bl_label = md.GeometryNodeAssetType.DRAW_SURFACE.get_name()
    bl_description = md.GeometryNodeAssetType.DRAW_SURFACE.get_description()
    asset_type = asset.Type.OBJECTS
    use_reimport_prompt = False

    al_asserts = [
        al.OperatorAssert(lambda c: c.active_object in c.selected_objects, 'No active object selected.', strict=False)
    ]

    def run(self, context: bt.Context):
        active_obj = context.active_object

        importer = self.get_importer()
        new_name = f'{importer.asset_instance.display_name} Drawing'
        obj: bt.Object = importer.get_asset(reimport=True)
        obj.name = new_name
        obj.data.name = new_name
        base_ops.link_and_select_object(context, obj)
        mod: bt.NodesModifier = obj.modifiers[0]

        obj.parent = active_obj
        
        _try_assign_gn_properties(mod, ('Target Object', active_obj))
        
        context.scene.tool_settings.curve_paint_settings.depth_mode = 'SURFACE'
        bo.object.mode_set(mode='EDIT')
        bo.wm.tool_set_by_id(name='builtin.draw')


class GNPlaceAsset(base_ops.SanctusAssetImportOperator):
    bl_label = md.GeometryNodeAssetType.PLACE_SURFACE.get_name()
    bl_description = md.GeometryNodeAssetType.PLACE_SURFACE.get_description()
    bl_options = {'UNDO'}
    asset_type = asset.Type.OBJECTS
    use_reimport_prompt = False


    def invoke(self, context: bt.Context, event: bt.Event):
        from .. import preferences

        self.new_parent = context.object

        modals.SET_GIZMO_RUNNING(True)

        importer = self.get_importer()
        obj: bt.Object = importer.get_asset(reimport=True)
        base_ops.link_and_select_object(context, obj)
        obj.scale = Vector((0,0,0))
        mod = next(x for x in obj.modifiers if isinstance(x, bt.NodesModifier))

        self.asset_object = obj
        self.modifier = mod
        self.raycast_hit = al.geo.FAILED_RAYHIT
        self.target_is_valid = False

        prefs = al.get_prefs()
        if prefs.interface().center_mouse_on_gizmos():
            al.geo.center_mouse_in_window(context)
        
        bt.WindowManager.modal_handler_add(self)

        return {al.BOperatorReturn.RUNNING_MODAL()}
    
    def modal(self, context: bt.Context, event: bt.Event):
        context.area.tag_redraw()
        if modals.ModalHelper.is_event_cancel(event):
            self.raycast_hit = al.geo.FAILED_RAYHIT
            self.target_is_valid = False
            return self.execute(context)
        
        self.raycast_hit = al.geo.raycast_scene_view(context, context.evaluated_depsgraph_get(), al.geo.mouse_vector_from_event(event))
        self.target_is_valid = self.raycast_hit.is_hit
        # if(self.raycast_hit.obj == self.asset_object):
        #     self.target_is_valid = False

        if self.target_is_valid:
            
            self.asset_object.parent = self.new_parent

            _try_assign_gn_properties(self.modifier, ('Target Object', self.new_parent))

            self.asset_object.matrix_world = al.geo.trs_matrix(self.raycast_hit.location, self.raycast_hit.normal)
        else:
            self.asset_object.scale = Vector((0,0,0))

        if modals.ModalHelper.is_event_confirm(event):
            if self.target_is_valid:
                return self.execute(context)
            else:
                self.report({'WARNING'}, 'Asset has to be placed on the surface of an object. [ESC] to cancel placement.')
                {al.BOperatorReturn.RUNNING_MODAL()}
        
        return {'PASS_THROUGH'}
    
    def run(self, context: bt.Context):
        modals.SET_GIZMO_RUNNING(False)
        if not self.target_is_valid:
            bpy.data.objects.remove(self.asset_object)
            return {al.BOperatorReturn.CANCELLED()}


@al.register_operator
class GNPlaceSurface(GNPlaceAsset):
    
    al_asserts = [
        modals.GIZMO_RUNNING_ASSERT,
        al.OperatorAssert(lambda c: c.object in c.selected_objects, 'No active object selected.', strict=False),
        al.OperatorAssert(poll.is_object_type(types='MESH'), 'Active object is not of type “MESH”.')
    ]


@al.register_property(bt.NodeTree)
class SanctusIsHairAsset(al.BoolProperty):

    def __init__(self):
        return super().__init__(
            name='Is Hair Asset',
            default=False
        )
    
    @classmethod
    def get(cls, parent: bt.NodeTree, attr_name: str = None):
        return super().get(parent, attr_name)
