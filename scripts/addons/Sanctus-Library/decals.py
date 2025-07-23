'''
Decal settings exist on all instance of bpy.types.Object but is_decal is only True for objects added as decals by the addon.
The module contains some utility functions and constants for doing operations with decals and the SanctusDecalSettings property group
can be used to access the decal's specific modifier stack and materials
'''

from . import auto_load as al
from .auto_load.common import *
from . import node_utils

GN_TARGET_OBJECT_ID = 'Target Object'
GN_IMAGE_ID = 'Image'
GN_MATERIAL_ID = 'Material'
DECAL_MODIFIER_NAME = 'SL Decal'
TRANSFER_MODIFIER_NAME = 'SL Normal Transfer'
MATERIAL_IMAGE_NODE_NAME = 'sl_sticker_texture'
DECAL_COLLECTION_NAME = 'SL Decals'

DECAL_GROUP_ASSET_NAME = 'sl_decal_tool'
DECAL_MATERIAL_PATH = Path('decal_utils/sl_decal_texture')

NODES_MODIFIER_REQUIRED_INPUTS = (
    GN_TARGET_OBJECT_ID,
    GN_IMAGE_ID,
    GN_MATERIAL_ID
)

def get_decal_group_path():
    from . import library_manager
    sub_hierarchy = library_manager.MANAGER.runtime_library.search_hierarchy(Path('decal_utils'))
    return next(v.path for k, v in sub_hierarchy.items() if k.startswith(DECAL_GROUP_ASSET_NAME))

def is_decal_modifier(m: bt.Modifier):
    if not isinstance(m, bt.NodesModifier):
        return False
    if not m.name.startswith(DECAL_MODIFIER_NAME):
        return False
    if m.node_group is None:
        return False

    return all(x in node_utils.get_node_tree_input_keys(m.node_group) for x in NODES_MODIFIER_REQUIRED_INPUTS)


def is_transfer_modifier(m: bt.Modifier):
    return isinstance(m, bt.DataTransferModifier)


def is_decal_image_node(n: bt.Node):
    return n.name == MATERIAL_IMAGE_NODE_NAME and hasattr(n, 'image')


@al.register_property_group(bt.Object)
class SanctusDecalSettings(al.PropertyGroup[bt.Object]):

    @property
    def obj(self) -> bt.Object:
        return self.id_data

    is_decal = al.BoolProperty()

    def get_decal_nodes_modifier(self) -> OrNone[bt.NodesModifier]:
        return next((m for m in self.obj.modifiers if is_decal_modifier(m)), None)

    def get_decal_image_node(self) -> OrNone[bt.ShaderNodeTexImage]:
        return next((n for n in self.obj.active_material.node_tree.nodes if is_decal_image_node(n)), None)

    def get_decal_normals_modifier(self) -> OrNone[bt.DataTransferModifier]:
        return next((m for m in self.obj.modifiers if is_transfer_modifier(m)), None)

    def can_set_image(self) -> bool:
        return all(x is not None for x in (self.get_decal_image_node(), self.get_decal_nodes_modifier()))

    def set_image(self, image: bt.Image) -> bool:
        m = self.get_decal_nodes_modifier()
        n = self.get_decal_image_node()
        if any(x is None for x in (m, n)):
            return False
        m[node_utils.gn_input_identifier(m.node_group, GN_IMAGE_ID)] = image
        n.image = image
        return True

    def set_target(self, target: bt.Object) -> bool:
        decal_mod = self.get_decal_nodes_modifier()
        normals_mod = self.get_decal_normals_modifier()
        if any(x is None for x in (decal_mod, normals_mod)):
            return False
        decal_mod[node_utils.gn_input_identifier(decal_mod.node_group, GN_TARGET_OBJECT_ID)] = target
        normals_mod.object = target
        return True

    def get_target(self) -> OrNone[bt.Object]:
        m = self.get_decal_nodes_modifier()
        if m is None:
            return None
        return m[node_utils.gn_input_identifier(m.node_group, GN_TARGET_OBJECT_ID)]

    def set_material(self, material: bt.Material) -> bool:
        self.obj.active_material = material
        m = self.get_decal_nodes_modifier()
        if m is None:
            return False
        m[node_utils.gn_input_identifier(m.node_group, GN_MATERIAL_ID)] = material
        return True

    def set_references(self, material: bt.Material, target: bt.Object, image: bt.Image) -> tuple[bool, bool, bool]:
        s0 = self.set_target(target)
        s1 = self.set_material(material)
        s2 = self.set_image(image)
        return (s0, s1, s2)


def get_decal_children(obj: bt.Object) -> list[bt.Object]:
    return [x for x in bpy.data.objects if (s := SanctusDecalSettings.get_from(x)).is_decal and s.get_target() == obj]
