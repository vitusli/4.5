import bpy

from ...qbpy import GeometryNodeTree, Modifier, Object


def prepare_lod_group(context, name: str, collection: bpy.types.Collection, lods: list) -> bpy.types.GeometryNodeTree:
    node_group = GeometryNodeTree(name=name)

    # group input node and sockets
    group_input = node_group.group_input(name="Group Input", position=(-2340, 0))
    group_input.socket(name="Geometry", socket_type="NodeSocketGeometry")

    for i in range(1, 9):
        group_input.socket(
            name=f"LOD{i} Distance",
            socket_type="NodeSocketFloat",
            subtype="DISTANCE",
            default_value=5 * i,
            min_value=0,
            max_value=100,
            hide_in_modifier=True,
            force_non_field=True,
        )

    # Add nodes to the node_group
    active_camera = node_group.active_camera(name="Active Camera", position=(-2160, 160))
    camera_info = node_group.object_info(name="Camera Info", position=(-1980, 160))

    self_object = node_group.self_object(name="Self Object", position=(-2160, -60))
    LOD0_info = node_group.object_info(name="LOD0 Info", position=(-1980, -60))

    # Create LOD info, compare, and switch nodes dynamically
    lod_info_nodes = {}
    lod_compare_nodes = {}
    lod_switch_nodes = {}

    for i, r in enumerate(reversed(range(1, 9)), start=1):
        offset = -180 * r  # offset the nodes from left to right

        lod_compare_nodes[i] = node_group.compare(name=f"Compare LOD{i}", position=(offset - 180, 160))
        lod_switch_nodes[i] = node_group.switch(name=f"Switch LOD{i}", position=(offset, 0))
        lod_info_nodes[i] = node_group.object_info(name=f"LOD{i} Info", position=(offset - 180, -160))

    vector_math = node_group.vector_math(name="Vector Math", operation="DISTANCE", position=(-1800, 160))

    # Group output node and sockets
    group_output = node_group.group_output(name="Group Output")
    group_output.socket(name="Geometry", socket_type="NodeSocketGeometry")

    # Link nodes

    # Link group input to LOD switches and compares
    for i in range(1, 9):
        node_group.node_tree.links.new(group_input.outputs["Geometry"], lod_switch_nodes[i].inputs["False"])
        node_group.node_tree.links.new(group_input.outputs[f"LOD{i} Distance"], lod_compare_nodes[i].inputs["B"])

    # Link active camera and self object
    node_group.node_tree.links.new(active_camera.outputs["Active Camera"], camera_info.inputs["Object"])
    node_group.node_tree.links.new(self_object.outputs["Self Object"], LOD0_info.inputs["Object"])

    # Link camera info and LOD0 info to vector math
    node_group.node_tree.links.new(camera_info.outputs["Location"], vector_math.inputs[0])
    node_group.node_tree.links.new(LOD0_info.outputs["Location"], vector_math.inputs[1])

    # Link LOD info to LOD switches
    for i in range(1, 9):
        node_group.node_tree.links.new(lod_info_nodes[i].outputs["Geometry"], lod_switch_nodes[i].inputs["True"])

    # Link vector math to LOD compares
    for i in range(1, 9):
        node_group.node_tree.links.new(vector_math.outputs["Value"], lod_compare_nodes[i].inputs["A"])

    # Link LOD compares to LOD switches
    for i in range(1, 9):
        node_group.node_tree.links.new(lod_compare_nodes[i].outputs["Result"], lod_switch_nodes[i].inputs["Switch"])

    # Link LOD switches in sequence
    for i in range(1, 8):
        node_group.node_tree.links.new(lod_switch_nodes[i].outputs["Output"], lod_switch_nodes[i + 1].inputs["False"])

    # Sort objects by their names to ensure consistent LOD ordering
    sorted_objects = sorted(collection.objects, key=lambda obj: obj.name.lower())

    for i, obj in enumerate(sorted_objects):
        if lods[0].lower() in obj.name.lower():
            Modifier.geometry_node(
                obj, name=node_group.node_tree.name, node_group=node_group.node_tree, show_in_editmode=False
            )
        elif i > 0:
            group_input.socket(name=f"LOD{i} Distance", hide_in_modifier=False, force_non_field=True)
            # add the obj to the LOD info node and hide it
            if LOD_info := next((node for node in node_group.node_tree.nodes if node.name == f"LOD{i} Info"), None):
                LOD_info.inputs["Object"].default_value = obj
                obj.hide_set(True)
                obj.hide_viewport = True
                obj.hide_render = True
            # remove the geometry node modifier if it already exists
            if geo_mod := next(
                (
                    mod
                    for mod in obj.modifiers
                    if mod.type == "GEOMETRY_NODES" and mod.node_group == node_group.node_tree
                ),
                None,
            ):
                Modifier.remove(obj, geo_mod)

            if switch_node := next(
                (node for node in node_group.node_tree.nodes if node.name == f"Switch LOD{i}"), None
            ):
                node_group.node_tree.links.new(switch_node.outputs["Output"], group_output.inputs["Geometry"])

    # Find LOD0 object
    lod_0 = next((obj for obj in collection.objects if lods[0].lower() in obj.name.lower()), None)
    if lod_0:
        for obj in collection.objects:
            if obj == lod_0:
                continue
            # Parent other objects to LOD0
            Object.parent_object(lod_0, obj)
            # Remove non-LOD objects
            if not any(lod.lower() in obj.name.lower() for lod in lods):
                Object.remove_object(obj)
