import os

import bpy
from bpy.props import StringProperty
from bpy.types import Operator


class IMESHH_OT_hdri(Operator):
    bl_label = "Apply"
    bl_idname = "imeshh.hdri"
    bl_options = {"REGISTER", "INTERNAL"}

    filepath: StringProperty(subtype="FILE_PATH", options={"SKIP_SAVE"})

    @classmethod
    def description(cls, context, properties):
        return "Import HDRI"

    def execute(self, context):
        if not self.filepath or not os.path.exists(self.filepath):
            self.report({"WARNING"}, "HDRI File not found")
            return {"CANCELLED"}

        self.import_hdri(context)
        return {"FINISHED"}

    def get_or_create_node(self, node_tree: bpy.types.ShaderNodeTree, node_type: str, node_name: str = None):
        """Helper to find a node or create it if it doesn't exist"""
        node = next(
            (
                node
                for node in node_tree.nodes
                if (node_name and node.name == node_name) or (not node_name and node.type == node_type)
            ),
            None,
        )
        if node:
            return node

        node = node_tree.nodes.new(node_type)
        if node_name:
            node.name = node_name
        return node

    def import_hdri(self, context):
        world = context.scene.world
        world.use_nodes = True
        node_tree = world.node_tree

        # Load node groups if needed
        hdri_nodes_blend_filepath = os.path.join(os.path.dirname(__file__), "../utils/hdri_nodes.blend")
        if "imeshh_ground_projection" not in bpy.data.node_groups or "imeshh_hdri_nodes" not in bpy.data.node_groups:
            with bpy.data.libraries.load(hdri_nodes_blend_filepath, link=False) as (data_from, data_to):
                data_to.node_groups = data_from.node_groups

        # Get or create nodes
        world_output = self.get_or_create_node(node_tree, "ShaderNodeOutputWorld", "World Output")
        world_output.location = (300, 300)
        world_output.select = True
        node_tree.nodes.active = world_output

        hdri_group = self.get_or_create_node(node_tree, "ShaderNodeGroup", "imeshh_hdri_nodes")
        hdri_group.node_tree = bpy.data.node_groups.get("imeshh_hdri_nodes")

        ground_projection = self.get_or_create_node(node_tree, "ShaderNodeGroup", "imeshh_ground_projection")
        ground_projection.node_tree = bpy.data.node_groups.get("imeshh_ground_projection")

        env_tex_node = self.get_or_create_node(node_tree, "ShaderNodeTexEnvironment", "imeshh_env_tex")

        # Position nodes
        nodes = [hdri_group, env_tex_node, ground_projection]  # order is important for positioning
        x = world_output.location.x
        for node in nodes:
            x -= node.width + 80
            node.location = (x, world_output.location.y)

        # Link nodes
        node_tree.links.new(ground_projection.outputs["Color"], env_tex_node.inputs["Vector"])
        node_tree.links.new(env_tex_node.outputs["Color"], hdri_group.inputs["HDRI"])
        node_tree.links.new(hdri_group.outputs["Shader"], world_output.inputs["Surface"])

        # Load HDR image
        hdr_image = bpy.data.images.get(os.path.basename(self.filepath)) or bpy.data.images.load(self.filepath)
        env_tex_node.image = hdr_image


class IMESHH_OT_hdri_properties(Operator):

    bl_label = "HDRI Properties"
    bl_idname = "imeshh.hdri_properties"
    bl_options = {"REGISTER", "INTERNAL"}

    @classmethod
    def description(cls, context, properties):
        return "Show HDRI properties"

    def draw(self, context):
        layout = self.layout
        node_tree = context.scene.world.node_tree

        # Display properties for both node groups
        for node_name, heading in [("imeshh_ground_projection", "Ground Projection"), ("imeshh_hdri_nodes", "HDRI")]:
            if node := next((n for n in node_tree.nodes if n.name == node_name), None):
                col = layout.column(heading=heading)
                for input in node.inputs:
                    if not input.is_linked:
                        col.prop(input, "default_value", text=input.name)

    def execute(self, context):
        return context.window_manager.invoke_popup(self, width=200)


classes = (
    IMESHH_OT_hdri,
    IMESHH_OT_hdri_properties,
)


register, unregister = bpy.utils.register_classes_factory(classes)
