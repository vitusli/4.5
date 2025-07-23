import bpy
from ..nodes.active_group import get_active_group
from ..utilities.layers import get_layer_nodes
from ..utilities.nodes import get_RR_groups, get_RR_nodes
from ..utilities.version import is_legacy_group, get_addon_version, get_RR_node_version
from .cache import cacheless


def get_settings(context=bpy.context, RR_group=None, layer_index=None, use_cache=True):
    return Settings(context, RR_group, layer_index, use_cache)
        
    
class Settings():
    def __init__(self, context=bpy.context, RR_group=None, layer_index=None, use_cache=True):
        self.context = context
        self.RR_group = RR_group
        self.layer_index = layer_index
        self.use_cache = use_cache

    # Common

    @property
    def groups(self):
        return get_RR_groups(self.context, use_cache=self.use_cache)

    @property
    def group(self):
        if self.RR_group == None:
            return get_active_group(self.context)
        else:
            return self.RR_group

    @property
    def layers(self):
        return self.group.render_raw_layers

    @property
    def layer(self):
        if self.layer_index == None:
            return self.layers[self.active_layer_index]
        else:
            return self.layers[self.layer_index]

    @property
    def layer_pre(self):
        if self.layer_index == None:
            return self.nodes_layers['Pre'][self.active_layer_index]
        else:
            return self.nodes_layers['Pre'][self.layer_index]

    @property
    def layer_post(self):
        if self.layer_index == None:
            return self.nodes_layers['Post'][self.active_layer_index]
        else:
            return self.nodes_layers['Post'][self.layer_index]

    # Nodes

    @property
    def nodes(self):
        return get_RR_nodes(self.context, use_cache=self.use_cache)

    @property
    def nodes_with_group(self):
        return [x for x in self.nodes if x.node_tree == self.group]

    @property
    def nodes_group(self):
        return self.group.nodes

    @property
    def nodes_layers(self):
        return get_layer_nodes(self.group, reverse=False, use_cache=self.use_cache)

    @property
    def nodes_pre(self):
        return self.layer_pre.node_tree.nodes

    @property
    def nodes_post(self):
        return self.layer_post.node_tree.nodes

    # Props

    @property
    def props_scene(self):
        return self.context.scene.render_raw_scene

    @property
    def props_group(self):
        return self.group.render_raw

    @property
    def props_layers(self):
        return self.group.render_raw_layers

    @property
    def props_pre(self):
        return self.layer_pre.node_tree.render_raw

    @property
    def props_post(self):
        return self.layer_post.node_tree.render_raw

    # Misc. Settings

    @property
    def enabled(self):
        return self.props_scene.enable_RR

    @property
    def use_values(self):
        return self.props_pre.use_values

    @property
    def use_colors(self):
        return self.props_pre.use_colors

    @property
    def use_effects(self):
        return self.props_pre.use_effects

    @property
    def preset_layer(self):
        return self.props_pre.preset

    @property
    def active_layer_index(self):
        return self.props_group.active_layer_index

    @property
    def is_legacy(self):
        return is_legacy_group(self.group, use_cache=self.use_cache)
    
    @property
    def in_scene(self):
        scene = self.context.scene
        return(
            scene.node_tree.nodes and
            self.group in [x.node_tree for x in scene.node_tree.nodes if x.bl_idname == 'CompositorNodeGroup']
        )
    
    @property
    def node_version(self, evaluate=False, pretty=False):
        return get_RR_node_version(self.group, evaluate, pretty, use_cache=self.use_cache)
    
    @property
    def version(self, eval=False, pretty=False):
        return get_addon_version(eval, pretty, use_cache=self.use_cache)


def is_default(RR_settings, key):
    prop_rna = RR_settings.bl_rna.properties[key]
    if prop_rna.subtype == 'COLOR':
        return(
            RR_settings[key] == prop_rna.default_array
        )
    elif prop_rna.type == 'ENUM':
        return(
            RR_settings[key] == prop_rna.enum_items.get(prop_rna.default).value
        )
    else:
        return(
            RR_settings[key] == prop_rna.default
        )
