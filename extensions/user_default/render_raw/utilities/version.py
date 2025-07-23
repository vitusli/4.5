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

import bpy, addon_utils
from ..constants import RR_node_group_name, RR_node_name
from .append import append_node
from .nodes import get_groups_recursively, get_group_nodes_recursively, get_RR_nodes
from .cache import RR_cache, cacheless


minimum_version = '(1, 2, 10)'


def prettify_version(version):
    return version.replace('(', '').replace(')', '').replace(',', '.').replace(' ', '')


@RR_cache(0.1)
def get_addon_version(eval=False, pretty=False, use_cache=True):
    version = str(
        [
            addon.bl_info.get("version", (-1, -1, -1))
            for addon in addon_utils.modules()
            if addon.bl_info["name"] == 'Render Raw'
        ][0]
    )

    if eval: return eval(version)
    elif pretty: return prettify_version(version)
    else: return version


def set_RR_node_version(RR_group):
    #TODO: Do this for all RR nodes
    try:
        RR_group.nodes['Version'].label = get_addon_version()
    except:
        print('Addon version could not be saved in the node tree')


@RR_cache(0.1)
def get_RR_node_version(RR_group, evaluate=False, pretty=False, use_cache=True):
    """  """
    if 'Version' in [x.name for x in RR_group.nodes]:
        version = RR_group.nodes['Version'].label
    else:
        version = str((-1, -1, -1))

    if evaluate: 
        return eval(version)
    elif pretty: 
        if eval(version) > (0, 0, 0):
            return prettify_version(version)
        else: return ' Unknown'
    else: return version 


@RR_cache(0.1)
def is_legacy_group(RR_group, use_cache=True):
    RR_node_version = get_RR_node_version(RR_group, evaluate=True)
    # addon_version = eval(get_addon_version())
    # return RR_node_version < addon_version
    return RR_node_version < eval(minimum_version)


@cacheless
def upgrade_nodes(context, RR_node):
    from ..utilities.presets import preset_settings_to_skip, create_curve_preset

    addon_version = eval(get_addon_version())
    RR_node_version = eval(get_RR_node_version(RR_node.node_tree))

    if addon_version == RR_node_version:
        return RR_node
    elif addon_version < RR_node_version:
        print('WARNING: Render Raw may not function properly when using nodes saved with a future version of the add-on')
        return RR_node
    
    new_RR = None

    if RR_node_version != 0 and RR_node_version < (1, 2, 0) and addon_version >= (1, 2, 0):
        # 0 indicates that the nodes are freshly imported and the version has not been set yet
        print(f"Upgrading Render Raw nodes from version {RR_node_version} to {addon_version}")
        from .presets import apply_layer_preset

        # Get all settings from the scene in preset format
        preset = {}

        # Before 1.2, all props were stored in the scene
        props =  context.scene.render_raw
        props.enable_RR = False # This needs to be off so the scene doesn't get flagged as legacy
        for key in props.keys():
            if (key not in preset_settings_to_skip):
                if (
                    hasattr(props.bl_rna.properties, key) and
                    props.bl_rna.properties[key].subtype == 'COLOR'
                ):
                    preset[key] = [props[key][0], props[key][1], props[key][2]]
                else:
                    preset[key] = props[key]

        # Some settings were referenced directly rather than saved through props
        nodes = RR_node.node_tree.nodes
        try:
            preset['value_curves'] = create_curve_preset(nodes['Curves'])
        except:
            print('Value Curve preset could not be created while upgrading')
        try:
            COLOR_BALANCE = nodes['Color Balance'].node_tree.nodes
            preset['highlight_blending'] = COLOR_BALANCE['Highlight Color'].blend_type
            preset['midtone_blending'] = COLOR_BALANCE['Midtone Color'].blend_type
            preset['shadow_blending'] = COLOR_BALANCE['Shadow Color'].blend_type
        except:
            print('Color Balance preset could not be created while upgrading')

        preset['version'] = get_addon_version()

        # Delete all nodes and import fresh
        original_group = RR_node.node_tree
        for group in get_groups_recursively(original_group.nodes):
            bpy.data.node_groups.remove(group)

        nodes = context.scene.node_tree.nodes
        links  = context.scene.node_tree.links

        new_RR = append_node(nodes, RR_node_group_name, copy=True)
        new_RR.location = RR_node.location
        for link in RR_node.inputs[0].links:
            links.new(link.from_socket, new_RR.inputs[0])
        for link in RR_node.outputs[0].links:
            links.new(new_RR.outputs[0], link.to_socket)
        new_RR.name = RR_node_name
        new_RR.label = RR_node_name
        new_RR.width = 175
        set_RR_node_version(new_RR.node_tree)

        group_nodes = get_group_nodes_recursively(context.scene.node_tree.nodes)
        other_users = [x for x in group_nodes if x != new_RR and x.node_tree == RR_node.node_tree]
        for node in other_users:
            node.node_tree = new_RR.node_tree

        bpy.data.node_groups.remove(original_group)
        nodes.remove(RR_node)

        apply_layer_preset(new_RR.node_tree, 0, preset)

    return new_RR if new_RR else RR_node


@cacheless
def upgrade_all_nodes(context):
    for node in get_RR_nodes(context):
        upgrade_nodes(context, node)