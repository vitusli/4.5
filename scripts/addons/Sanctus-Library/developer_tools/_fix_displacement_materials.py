import bpy, sys
import bpy.types as bt

from pathlib import Path

CORRECTION_NODE_NAME = 'sanctus_displacement_shift'
DISPLACEMENT_BAKE = 'Displacement Bake'
HEIGHT_BAKE = 'Height Bake'
DISPLACEMENT = 'Displacement'

class NoSocketLinkFoundError(Exception):
    pass

def get_connected_socket(input: bt.NodeSocket):

    def _from_socket(s: bt.NodeSocket) -> bt.NodeSocket:
        if not s.is_linked:
            raise NoSocketLinkFoundError(s)
        return s.links[0].from_socket
    
    c = _from_socket(input)
    while isinstance(c.node, bt.NodeReroute):
        c = _from_socket(c.node.inputs[0])
    
    return c

def adjust_node_group(nt: bt.NodeTree, top_level_group: bt.NodeTree):
    displacement_bake_output = top_level_group.interface.items_tree.get(DISPLACEMENT_BAKE, None)
    if displacement_bake_output is not None and displacement_bake_output.in_out == 'OUTPUT':
        print('Displacement setup is already fixed. Abort!')
        return

    output = next(x for x in nt.nodes if isinstance(x, bt.NodeGroupOutput))
    height_output = output.inputs.get(HEIGHT_BAKE, None)
    has_height_bake = height_output is not None

    displacement_output = output.inputs.get(DISPLACEMENT, None)
    if displacement_output is None:
        print('Material group does not have "Displacement" output. Either misspelled or asset meta data wrongly has "use_displacement" enabled.')
        print('Please change the original file. Failed!')
        return

    displace_node_output = get_connected_socket(displacement_output)
    displace_node = displace_node_output.node
    
    if isinstance(displace_node, bt.ShaderNodeGroup):
        print(f'Nested Group found. Adjustment being attempted on nested group "{displace_node.node_tree.name}".')
        return adjust_node_group(displace_node.node_tree, top_level_group) #RECURSION STEP
    
    if not isinstance(displace_node, bt.ShaderNodeDisplacement):
        print(f'Expected Displacement Node connected to "Displacement" output. Instead "{type(displace_node).__name__}". Failed!')
        return

    if displace_node.inputs['Midlevel'].default_value == 0.5:
        print('Displacement node has midlevel set to 0.5 -> Setup is already fixed. Abort!')
        return
    displace_node.inputs['Midlevel'].default_value = 0.5

    displace_height_input = displace_node.inputs['Height']
    displace_connect_socket = get_connected_socket(displace_height_input)

    if has_height_bake:
        height_connect_socket = get_connected_socket(height_output)
        if displace_connect_socket != height_connect_socket:
            print(f'Expected Displacement Height input to match "Height Bake" input node. Instead: {displace_connect_socket.path_from_id()}.')
            print('Please change the original file. Failed!')
            return
        
    correction_node: bt.ShaderNodeMath = nt.nodes.new(bt.ShaderNodeMath.__name__)
    correction_node.location = (displace_connect_socket.node.location + displace_node.location) / 2
    correction_node.name = CORRECTION_NODE_NAME
    correction_node.label = correction_node.name
    correction_node.operation = 'ADD'
    correction_node.inputs[1].default_value = 0.5

    nt.links.new(displace_connect_socket, correction_node.inputs[0])
    nt.links.new(correction_node.outputs[0], displace_height_input)
    if has_height_bake:
        nt.links.new(correction_node.outputs[0], height_output)
        top_level_group.interface.items_tree[HEIGHT_BAKE].name = DISPLACEMENT_BAKE

    return True

def main():

    path = Path(bpy.data.filepath)
    material = bpy.data.materials[path.stem]
    material_tree: bt.ShaderNodeTree = material.node_tree
    output_node = material_tree.get_output_node('CYCLES')
    if output_node is None:
        output_node = material_tree.get_output_node('ALL')
    group: bt.ShaderNodeGroup = output_node.inputs['Surface'].links[0].from_node
    if not isinstance(group, bt.ShaderNodeGroup):
        print(f'Node after shader output is not a Group Node. Failed!')
        return
    
    nt: bt.ShaderNodeTree = group.node_tree

    if adjust_node_group(nt, nt) is True:
        print('Saving File...')
        fp = bpy.context.preferences.filepaths
        old_save_versions = fp.save_version
        fp.save_version = 0
        bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
        fp.save_version = old_save_versions

main()
