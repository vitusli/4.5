import bpy, os

def append_group(node_tree_name, copy=False):
    if bpy.app.version >= (4, 5, 0):
        node_file = 'render_raw_nodes_4-5.blend'
    else:
        node_file = 'render_raw_nodes.blend'
    path = bpy.path.native_pathsep(os.path.join(
        os.path.dirname(os.path.abspath(__file__)), '..', 'assets', f'{node_file}\\NodeTree\\'
    ))

    initial_nodetrees = set(bpy.data.node_groups)

    try:
        bpy.ops.wm.append(filename=node_tree_name, directory=path)
    except:
        message = 'Render Raw nodes not detected. Please download from the Blender Market and install again.'
        bpy.ops.render.render_raw_report(message_type="ERROR", message=message)
        message = f'{node_tree_name} could not be appended from {path}'
        bpy.ops.render.render_raw_report(message_type="ERROR", message=message)
        return

    appended_nodetrees = set(bpy.data.node_groups) - initial_nodetrees
    appended_names = [x.name for x in appended_nodetrees]

    node_tree = list(appended_nodetrees)[0]
    if node_tree_name in appended_names:
        node_tree = bpy.data.node_groups[node_tree_name]
    else:
        search_limit = 500
        iteration = 1
        while iteration < search_limit:
            search_name = f'{node_tree_name}.{iteration:03}'
            if search_name in appended_names:
                node_tree = bpy.data.node_groups[search_name]
                break
            else:
                iteration += 1

    if copy: node_tree = node_tree.copy()

    print(f'Render Raw appended group: {node_tree.name}')
    return node_tree


def append_node(nodes, node_tree_name, copy=False):
    group_node = nodes.new('CompositorNodeGroup')
    group_node.node_tree = append_group(node_tree_name, copy)
    return group_node