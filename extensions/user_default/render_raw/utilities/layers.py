import bpy
from typing import Literal
from .nodes import make_subs_single_user, mix_all_outputs
from .append import append_group
from .cache import RR_cache, cacheless


def is_layer_used(RR):
    return (
        RR.props_pre.use_layer and
        RR.props_pre.layer_factor != 0
    )


def is_layer_group(group):
    return (
        'Pre Layer Input' in [x.name for x in group.nodes] or
        'Post Layer Input' in [x.name for x in group.nodes]
    )


def is_layer_node(node):
    return (
        node.bl_idname == 'CompositorNodeGroup' and
        node.node_tree and
        is_layer_group(node.node_tree)
    )


def get_position(node):
    if 'Pre' in node.node_tree.name:
        return 'Pre'
    elif 'Post' in node.node_tree.name:
        return 'Post'
    else:
        return None


@RR_cache(0.1)
def get_layer_nodes(RR_group, reverse=False, use_cache=True):
    pre_node = RR_group.nodes['Pre Layer Input']
    layers = {
        'Pre': [],
        'Post': []
    }
    pre_stop = False
    while not pre_stop:
        try:
            next_node = pre_node.outputs[0].links[0].to_node
            if is_layer_node(next_node):
                layers['Pre'].append(next_node)
                pre_node = next_node
            else:
                pre_stop = True
        except:
            pre_stop = True

    post_node = RR_group.nodes['Post Layer Input']
    post_stop = False
    while not post_stop:
        try:
            next_node = post_node.outputs[0].links[0].to_node
            if is_layer_node(next_node):
                layers['Post'].append(next_node)
                post_node = next_node
            else:
                post_stop = True
        except:
            post_stop = True

    if reverse:
        layers['Pre'] = list(reversed(layers['Pre']))
        layers['Post'] = list(reversed(layers['Post']))

    return layers


def get_layer_names(RR_group, reverse=False):
    layer_nodes = get_layer_nodes(RR_group, reverse=reverse)
    return [node.node_tree.render_raw.layer_name for node in layer_nodes['Pre']]



def get_layer_node(RR_group, index, position: Literal['Pre', 'Post']):
    layer_nodes = get_layer_nodes(RR_group)
    return layer_nodes[position][index]



def get_layer_settings(RR_group, index, position: Literal['Pre', 'Post']):
    return get_layer_node(RR_group, index, position).node_tree.render_raw


def organize_layers(RR_group):
    layers = get_layer_nodes(RR_group, use_cache=False)
    for idx, node in enumerate(layers['Pre']):
        node.location[0] = 275
        node.location[1] = idx * 56
    for idx, node in enumerate(layers['Post']):
        node.location[0] = 1075
        node.location[1] = idx * 56


def connect_layer_outputs(RR_group):
    nodes = RR_group.nodes
    links = RR_group.links
    layers = get_layer_nodes(RR_group)

    # Remove all connections
    for node in nodes:
        if 'Add Glare' in node.name:
            nodes.remove(node)

    # Create them fresh
    glare_convert = nodes['Convert Colorspace Glare']
    glare_outputs = [x.outputs[1] for x in layers['Pre']]
    location = [550, -200]
    add = mix_all_outputs(glare_outputs, 'Add Glare', 'ADD', location)
    if add:
        links.new(add, glare_convert.inputs[0])
    elif glare_outputs:
        links.new(layers['Pre'][0].outputs[1], glare_convert.inputs[0])


# The correct nodes are already made single user, so no need to link after
'''
def link_layer_subgroups(RR_group):
    layers = get_layer_nodes(RR_group)
    for layer_node in layers['Pre'] + layers['Post']:
        group_nodes = get_group_nodes_recursively(layer_node.node_tree.nodes)
        for group in group_nodes:
            if group.node_tree:
                original_name = '.' + group.node_tree.name.split('.')[1]
                if (
                    original_name in multiuser_subgroups and
                    group.node_tree.name != original_name and
                    original_name in [x.name for x in bpy.data.node_groups]
                ):
                    #TODO: Consider appending original node group if it's not in file instead of skipping
                    prev_group = group.node_tree
                    group.node_tree = bpy.data.node_groups[original_name]
                    if prev_group.users == 0:
                        bpy.data.node_groups.remove(prev_group)'
'''


def reset_layer_settings(RR_group, active_layer_index=None):
    from ..utilities.curves import RGB_curve_default, set_curve_node
    from ..utilities.presets import preset_settings_to_skip
    from ..nodes.update_RR import update_all

    if active_layer_index == None:
        active_layer_index = RR_group.render_raw.active_layer_index
    layer_pre = get_layer_node(RR_group, active_layer_index, 'Pre')
    layer_post = get_layer_node(RR_group, active_layer_index, 'Post')
    nodes_post = layer_post.node_tree.nodes

    for layer_node in [layer_pre, layer_post]:
        PROPS = layer_node.node_tree.render_raw
        RNA_PROPS = PROPS.bl_rna.properties
        for key in PROPS.keys():
            if key not in preset_settings_to_skip and key in RNA_PROPS.keys():
                if RNA_PROPS[key].subtype in ['COLOR', 'COLOR_GAMMA']:
                    PROPS[key] = RNA_PROPS[key].default_array
                elif RNA_PROPS[key].type == 'ENUM':
                    default = RNA_PROPS[key].default
                    PROPS[key] = RNA_PROPS[key].enum_items.get(default).value
                else:
                    PROPS[key] = RNA_PROPS[key].default

    set_curve_node(nodes_post['Curves'], RGB_curve_default)
    COLOR_BLENDING = nodes_post['Color Blending'].node_tree.nodes
    COLOR_BLENDING['Highlight Color'].blend_type = 'SOFT_LIGHT'
    COLOR_BLENDING['Midtone Color'].blend_type = 'SOFT_LIGHT'
    COLOR_BLENDING['Shadow Color'].blend_type = 'SOFT_LIGHT'
    #TODO: Update this to not need context and to work on the non-active layer
    update_all(self=None, context=bpy.context)


def refresh_layers(RR_group):
    # print('refreshing layers')
    organize_layers(RR_group)
    connect_layer_outputs(RR_group)
    prev_active_idx = RR_group.render_raw.active_layer_index
    prev_layer_count = len(RR_group.render_raw_layers.keys())
    current_layer_names = get_layer_names(RR_group)

    # It's hard to keep track of the right index while removing,
    # so it's easier to just clear the entire list and build it again
    for idx in range(prev_layer_count):
        RR_group.render_raw_layers.remove(0)

    for idx, layer_name in enumerate(current_layer_names):
        new_ui_layer = RR_group.render_raw_layers.add()
        new_ui_layer.name = layer_name
        RR_group.render_raw.active_layer_index = idx
        layer_pre = get_layer_node(RR_group, idx, 'Pre')
        layer_pre.node_tree.render_raw.layer_name = layer_name
        layer_pre.label = layer_name
        layer_post = get_layer_node(RR_group, idx, 'Post')
        layer_post.label = layer_name

    if prev_layer_count:
        RR_group.render_raw.active_layer_index = prev_active_idx


def add_layer(RR_group, name=None):

    def create_layer_name():
        name='New Layer'
        layer_names = get_layer_names(RR_group)
        suffix = 0
        name_found = False
        iteration = 0
        while not name_found and iteration < 100:
            pattern = f'{name} {suffix}' # Blender's pattern is f'{name}.{suffix:03}'
            if not suffix and name in layer_names:
                suffix += 1
            elif suffix and pattern in layer_names:
                suffix += 1
            else:
                name_found = True
            iteration += 1
        if suffix:
            return pattern
        else:
            return name

    def set_node_display(node):
        node.use_custom_color = True
        node.color = (0.5, 0.15, 0.6)
        node.hide = True

    def create_layer_node(name, position: Literal['Pre', 'Post']):
        nodes = RR_group.nodes
        links = RR_group.links
        group_name = f'.Layer {position}'
        new_layer = nodes.new("CompositorNodeGroup")
        if group_name not in [x.name for x in bpy.data.node_groups]:
            appended_group = append_group(f'.RR_{position}')
            new_layer.node_tree = appended_group.copy()
        else:
            new_layer.node_tree = bpy.data.node_groups[group_name].copy()
        new_layer.node_tree.render_raw.layer_name = name
        links.new(nodes[f'{position} Layer Input'].outputs[0], new_layer.inputs[0])
        links.new(new_layer.outputs[0], nodes[f'{position} Layer Output'].inputs[0])
        make_subs_single_user(new_layer.node_tree.nodes)
        set_node_display(new_layer)
        return new_layer

    def copy_layer_node(active_layer, name):
            nodes = RR_group.nodes
            links = RR_group.links
            new_layer = nodes.new("CompositorNodeGroup")
            new_layer.node_tree = active_layer.node_tree.copy()
            new_layer.node_tree.render_raw.layer_name = name
            links.new(active_layer.outputs[0], new_layer.inputs[0])
            links.new(new_layer.outputs[0], active_layer.outputs[0].links[0].to_socket)
            make_subs_single_user(new_layer.node_tree.nodes)
            set_node_display(new_layer)
            return new_layer

    def shift_index():
        layer_count = len(RR_group.render_raw_layers.keys())
        if layer_count <= 1:
            RR_group.render_raw.active_layer_index = 0
        else:
            RR_group.render_raw.active_layer_index += 1


    new_name = create_layer_name() if name == None else name

    layer_count = len(RR_group.render_raw_layers.keys())
    if layer_count:
        index = RR_group.render_raw.active_layer_index
        layer_pre = get_layer_node(RR_group, index, 'Pre')
        layer_post = get_layer_node(RR_group, index, 'Post')
        new_pre_node = copy_layer_node(layer_pre, new_name)
        new_post_node = copy_layer_node(layer_post, new_name)
    else:
        new_pre_node = create_layer_node(new_name, 'Pre')
        new_post_node = create_layer_node(new_name, 'Post')

    RR_group.links.new(RR_group.nodes['sRGB'].outputs[0], new_post_node.inputs['sRGB'])
    
    refresh_layers(RR_group)
    shift_index()
    reset_layer_settings(RR_group)

    return {'Pre': new_pre_node, 'Post': new_post_node}


def remove_layer(RR_group):

    def remove_layer_node(node, RR_group):
        from_socket = node.inputs[0].links[0].from_socket
        to_socket = node.outputs[0].links[0].to_socket
        RR_group.links.new(from_socket, to_socket)
        RR_group.nodes.remove(node)

    def shift_index(active_layer_index):
        layer_count = len(RR_group.render_raw_layers.keys())
        if layer_count > 1 and active_layer_index == layer_count - 1:
            RR_group.render_raw.active_layer_index -= 1

    active_layer_index = RR_group.render_raw.active_layer_index
    layer_pre = get_layer_node(RR_group, active_layer_index, 'Pre')
    layer_post = get_layer_node(RR_group, active_layer_index, 'Post')
    for node in [layer_pre, layer_post]:
        remove_layer_node(node, RR_group)

    shift_index(active_layer_index)
    refresh_layers(RR_group)


def remove_all_layers(RR_group):
    for layer_name in RR_group.render_raw_layers.keys():
        remove_layer(RR_group)


def move_layer(RR_group, layer_index, direction: Literal['UP', 'DOWN']):
    layer_pre = get_layer_node(RR_group, layer_index, 'Pre')
    layer_post = get_layer_node(RR_group, layer_index, 'Post')

    def swap_layer_nodes(node1, node2):
        name1 = node1.name
        name2 = node2.name
        group1 = node1.node_tree
        group2 = node2.node_tree
        label1 = node1.label
        label2 = node2.label

        node1.node_tree = group2
        node1.label = label2
        node1.name = name2
        node2.node_tree = group1
        node2.label = label1
        node2.name = name1

    def move_layer_nodes():
        for layer_node in [layer_pre, layer_post]:
            prev_node = layer_node.inputs[0].links[0].from_node
            next_node = layer_node.outputs[0].links[0].to_node

            if direction == 'DOWN' and is_layer_node(prev_node):
                swap_layer_nodes(layer_node, prev_node)
            elif direction == 'UP' and is_layer_node(next_node):
                swap_layer_nodes(layer_node, next_node)

    def shift_index():
        current_index = RR_group.render_raw.active_layer_index
        layer_count = len(RR_group.render_raw_layers.keys())

        if direction == 'UP' and current_index != layer_count - 1:
            RR_group.render_raw.active_layer_index +=1
        elif direction == 'DOWN' and current_index != 0:
            RR_group.render_raw.active_layer_index -=1

    move_layer_nodes()
    shift_index()
    refresh_layers(RR_group)