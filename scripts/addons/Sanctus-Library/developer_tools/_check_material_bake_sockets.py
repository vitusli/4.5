import bpy
from pathlib import Path
import bpy.types as bt

def main():
    path = Path(bpy.data.filepath)
    material: bt.Material = next(x for x in bpy.data.materials if x.name.startswith(path.stem))
    mat_nt: bt.ShaderNodeTree = material.node_tree
    output_node: bt.ShaderNodeOutputMaterial = mat_nt.get_output_node("ALL")
    if output_node is None:
        output_node = mat_nt.get_output_node("CYCLES")
    if output_node is None:
        output_node = mat_nt.get_output_node("EEVEE")
    
    group_node = output_node.inputs["Surface"].links[0].from_node
    if not isinstance(group_node, bt.ShaderNodeGroup):
        print("No group node found that's connected to the material output")
    node_tree: bt.ShaderNodeTree = group_node.node_tree

    bake_outputs_found = 0
    for output in node_tree.interface.items_tree:
        if not isinstance(output, bt.NodeTreeInterfaceSocket):
            continue
        if(output.name.endswith(" Bake")):
            bake_outputs_found += 1

    if bake_outputs_found:
        print(f"{path.stem}: {bake_outputs_found} Bake Outputs Found")

main()