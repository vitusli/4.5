'''
Copyright (C) 2024 Orange Turbine
https://orangeturbine.com
orangeturbine@cgcookie.com

This file is part of the Render Raw add-on, created by Jonathan Lampel for Orange Turbine.

All code distributed with this add-on is open source as described below.

Render Raw is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 3
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, see <https://www.gnu.org/licenses/>.
'''

import bpy
from ..constants import RR_node_group_name
from ..utilities.append import append_group
from ..utilities.nodes import is_RR_node, get_groups_recursively, get_RR_groups, make_subs_single_user
from ..utilities.settings import get_settings
from ..utilities.presets import get_active_props_from_key, preset_settings_to_skip, get_group_preset, apply_group_preset
from ..utilities.version import set_RR_node_version
from ..utilities.cache import cacheless
from .active_group import get_active_group, set_active_group

from .update_alpha import update_alpha
from .update_colors import update_color_panel
from .update_details import update_details_panel
from .update_effects import update_effects_panel
from .update_values import update_value_panel


def update_all(self, context, RR_group=None, layer_index=None):
    update_value_panel(self, context, RR_group, layer_index)
    update_color_panel(self, context, RR_group, layer_index)
    update_details_panel(self, context, RR_group, layer_index)
    update_effects_panel(self, context, RR_group, layer_index)
    update_alpha(self, context, RR_group)


@cacheless
def reset_RR(context):
    if hasattr(context.scene, 'render_raw'):
        RR = get_settings(context)
        settings_keys = (
            [x for x in RR.props_group.keys()] +
            [x for x in RR.props_pre.keys()] +
            [x for x in RR.props_post.keys()]
        )

        for key in settings_keys:
            PROPS = get_active_props_from_key(RR, key)
            if key not in preset_settings_to_skip and key in PROPS.bl_rna.properties.keys():
                if PROPS.bl_rna.properties[key].subtype in ['COLOR', 'COLOR_GAMMA']:
                    PROPS[key] = PROPS.bl_rna.properties[key].default_array
                elif PROPS.bl_rna.properties[key].type == 'ENUM':
                    default = PROPS.bl_rna.properties[key].default
                    PROPS[key] = PROPS.bl_rna.properties[key].enum_items.get(default).value
                else:
                    PROPS[key] = PROPS.bl_rna.properties[key].default

        from ..utilities.curves import RGB_curve_default, set_curve_node
        set_curve_node(RR.nodes_post['Curves'], RGB_curve_default)
        CB_NODES = RR.nodes_post['Color Balance'].node_tree.nodes
        CB_NODES['Highlight Color'].blend_type = 'SOFT_LIGHT'
        CB_NODES['Midtone Color'].blend_type = 'SOFT_LIGHT'
        CB_NODES['Shadow Color'].blend_type = 'SOFT_LIGHT'


def toggle_RR(self, context):
    from .enable_RR import enable_RR
    from .disable_RR import disable_RR
    if context.scene.render_raw_scene.enable_RR:
        enable_RR(context)
    else:
        disable_RR(self, context)


@cacheless
def refresh_RR_nodes(context):
    NODES = context.scene.node_tree.nodes
    GROUPS = bpy.data.node_groups
    active_group_name = get_active_group(context).name

    groups_presets = {}

    RR_groups = get_RR_groups(context)
    for group in RR_groups:
        groups_presets[group.name] = get_group_preset(group)

    default_RR = append_group(RR_node_group_name)
    set_RR_node_version(default_RR)

    nodes_to_replace = {} #Format {Group 1: [Node 1, Node 2, Node 3], Group 2: [Node 4, Node 5]}
    nodes_to_search = set(NODES)
    for group in get_groups_recursively(NODES):
        nodes_to_search.update(group.nodes)
    for node in nodes_to_search:
        if is_RR_node(node, include_legacy=True):
            if node.node_tree.name not in nodes_to_replace.keys():
                nodes_to_replace[node.node_tree.name] = []
            nodes_to_replace[node.node_tree.name].append(node)
    print(nodes_to_replace)
    for group_name in nodes_to_replace.keys():
        prev_group = GROUPS[group_name]
        active_layer_index = prev_group.render_raw.active_layer_index
        new_group = default_RR.copy()
        for node in nodes_to_replace[group_name]:
            node.node_tree = new_group
        make_subs_single_user(new_group.nodes)
        set_active_group(context, new_group)
        apply_group_preset(new_group, groups_presets[prev_group.name])
        GROUPS.remove(GROUPS[group_name])
        new_group.name = group_name
        new_group.render_raw.active_layer_index = active_layer_index

    set_active_group(context, GROUPS[active_group_name])

    #TODO: Remove all unused subgroups
