import bpy
from typing import Literal
from ..utilities.nodes import get_RR_nodes, is_RR_node, get_group_nodes_recursively, make_subs_single_user
from ..utilities.version import set_RR_node_version
from ..utilities.append import append_node
from ..utilities.cache import cacheless
from ..constants import RR_node_group_name


def get_active_group(context):
    SCENE = context.scene
    RR_SCENE = SCENE.render_raw_scene
    NAME = RR_SCENE.active_RR_group_name

    # TODO: Create new RR group if none is active

    if (
        SCENE.use_nodes and
        SCENE.node_tree.nodes and
        is_RR_node(SCENE.node_tree.nodes.active, include_legacy=True)
    ):
        return SCENE.node_tree.nodes.active.node_tree

    for group in bpy.data.node_groups:
        if group.name == NAME:
            return group

    scene_RR_nodes = get_RR_nodes(context)
    if scene_RR_nodes:
        return scene_RR_nodes[0].node_tree

    print('No active Render Raw group found')
    return None


def get_active_node(context):
    SCENE = context.scene
    RR_GROUP = get_active_group(context)
    NODES = context.scene.node_tree.nodes

    if (
        SCENE.use_nodes and
        SCENE.node_tree.nodes and
        is_RR_node(SCENE.node_tree.nodes.active)
    ):
        return SCENE.node_tree.nodes.active

    group_nodes = get_group_nodes_recursively(NODES)
    for node in group_nodes:
        if node.node_tree == RR_GROUP:
            return node

    return None


def get_active_group_settings(context):
    RR_GROUP  = get_active_group(context)
    if RR_GROUP:
        return RR_GROUP.render_raw
    # Fallback to scene values just so interface doesn't error out
    return context.scene.render_raw


@cacheless
def set_active_group(context, group=None):
    SCENE = context.scene
    RR_SCENE = SCENE.render_raw_scene
    RR_nodes = get_RR_nodes(context)
    active_node = SCENE.node_tree.nodes.active

    if group != None:
        RR_SCENE.active_RR_group_name = group.name
        for node in RR_nodes:
            if node.node_tree == group:
                node.id_data.nodes.active = node
    elif is_RR_node(active_node):
        RR_SCENE.active_RR_group_name = active_node.node_tree.name
    elif RR_SCENE.active_RR_group_name in [node.node_tree.name for node in RR_nodes]:
        pass
    elif RR_nodes:
        RR_SCENE.active_RR_group_name = RR_nodes[0].node_tree.name

    return bpy.data.node_groups[RR_SCENE.active_RR_group_name]


def apply_active_group(self, context):
    RR_SCENE = context.scene.render_raw_scene
    group = bpy.data.node_groups[RR_SCENE.active_group]
    set_active_group(context, group=group)


@cacheless
def rename_active_group(context, name):
    RR_SCENE = context.scene.render_raw_scene
    GROUP = get_active_group(context)
    GROUP.name = name
    RR_SCENE.active_RR_group_name = name


def active_group_items(self, context):
    RR_nodes = get_RR_nodes(context)
    if RR_nodes:
        groups = set()
        for node in RR_nodes:
            groups.add((node.node_tree.name, node.node_tree.name, ''))
        return list(groups)
    else:
        return [('NONE', 'None', '')]


@cacheless
def duplicate_active_group(context):
    RR_SCENE = context.scene.render_raw_scene
    GROUP = get_active_group(context)
    PREV_NODE = get_active_node(context)
    NODES = PREV_NODE.id_data.nodes

    if RR_node_group_name in [x.name for x in bpy.data.node_groups]:
        RR_node = NODES.new("CompositorNodeGroup")
        RR_node.node_tree = GROUP.copy()
    else:
        RR_node = append_node(NODES, RR_node_group_name, copy=True)

    RR_node.location = [PREV_NODE.location[0], PREV_NODE.location[1] - 250]
    RR_node.width = 175

    make_subs_single_user(RR_node.node_tree.nodes)
    set_RR_node_version(RR_node.node_tree)

    return RR_node
