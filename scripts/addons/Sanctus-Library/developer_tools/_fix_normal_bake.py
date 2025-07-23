import bpy
import typing

T = typing.TypeVar('T', bound='bpy.types.Node')

def get_connected_node(input: bpy.types.NodeSocket) -> bpy.types.Node:
    return input.links[0].from_node

def new_node(node_tree: bpy.types.NodeTree, node_type: type[T]) -> T:
    n = node_tree.nodes.new(node_type.__name__)
    return n

def main():

    file_changed = False

    for nt in [x for x in bpy.data.node_groups if x.name.startswith('normal_bake') and isinstance(x, bpy.types.ShaderNodeTree)]:
        output = next(x for x in nt.nodes if isinstance(x, bpy.types.NodeGroupOutput))
        add_node = get_connected_node(output.inputs[0])
        scale_node = get_connected_node(add_node.inputs[0])

        combine_node = get_connected_node(scale_node.inputs[0])
        if not isinstance(combine_node, bpy.types.ShaderNodeCombineXYZ):
            raise RuntimeError(f'Node was expected to be CombineXYZ, not "{type(combine_node).__name__}"')
        y_input = combine_node.inputs[1]
        prev_node = get_connected_node(y_input)
        if isinstance(prev_node, bpy.types.ShaderNodeMath):
            print(f'Node Group "{nt.name}" is already correct.')
            continue
        if not isinstance(prev_node, bpy.types.ShaderNodeVectorMath):
            raise RuntimeError(f'Node before Combine node was expected to be Vector Math, not "{type(prev_node).__name__}"')

        prev_socket: bpy.types.NodeSocket = combine_node.inputs[1].links[0].from_socket
        invert_node = new_node(nt, bpy.types.ShaderNodeMath)
        file_changed = True
        invert_node.name = invert_node.label = 'sanctus_correct_normal_y'
        invert_node.operation = 'MULTIPLY'
        invert_node.inputs[1].default_value = -1
        nt.links.new(prev_socket, invert_node.inputs[0])
        nt.links.new(invert_node.outputs[0], y_input)

    if file_changed:
        print('Saving File...')
        fp = bpy.context.preferences.filepaths
        old_save_versions = fp.save_version
        fp.save_version = 0
        bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
        fp.save_version = old_save_versions

main()