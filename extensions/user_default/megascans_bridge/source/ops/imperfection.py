import os

import bpy
from bpy.props import StringProperty
from bpy.types import Operator

from ...qbpy.node_trees import ShaderNodeTree
from ..utils.addon import preferences


class MBRIDGE_OT_imperfection_group_add(Operator):
    bl_label = "Import"
    bl_idname = "mbridge.imperfection_group_add"
    bl_options = {"REGISTER", "INTERNAL"}

    asset_id: StringProperty(options={"SKIP_SAVE", "HIDDEN"})

    @classmethod
    def poll(cls, context):
        return (
            context.space_data
            and context.space_data.type == "NODE_EDITOR"
            and bool(getattr(context.space_data, "edit_tree", None))
        )

    @classmethod
    def description(cls, context, properties):
        props = context.scene.mbridge
        assets = props.imperfections.get_assets(context)
        asset = next((a for a in assets if a.id == properties.asset_id), None)

        if not asset:
            return "Cannot import - asset not found"

        current_tree = getattr(context.space_data, "edit_tree", None)
        if not current_tree:
            return "Cannot import - no node tree found"
        elif current_tree and current_tree.name == asset.path.lower().replace(" ", "_"):
            return "Cannot import in the same node tree"

        return "Import the imperfection as a node group"

    def invoke(self, context, event):
        self.prefs = preferences()
        self.props = context.scene.mbridge

        assets = self.props.imperfections.get_assets(context)
        self.asset = next((a for a in assets if a.id == self.asset_id), None)
        if self.asset:
            self.node_name = f"{self.asset.name.lower().replace(' ', '_')}_{self.asset.id}"
            node_tree = self.prepare_node_tree(context, self.node_name)

            return bpy.ops.node.add_node(
                "INVOKE_DEFAULT",
                use_transform=True,
                settings=[
                    {"name": "node_tree", "value": f"bpy.data.node_groups['{node_tree.name}']"},
                    {"name": "show_options", "value": "False"},
                ],
                type="ShaderNodeGroup",
            )

        return {"CANCELLED"}

    def prepare_node_tree(self, context, name: str) -> bpy.types.ShaderNodeTree:
        node_group = ShaderNodeTree(name)

        input_node = node_group.group_input(position=(-880, 220))
        input_node.socket(name="Vector", socket_type="NodeSocketVector")

        tex_roughness_node = node_group.image_texture(name="roughness", position=(-620, 240))
        tex_gloss_node = node_group.image_texture(name="gloss", position=(-620, 200))
        tex_mask_node = node_group.image_texture(name="mask", position=(-620, 160))

        output_node = node_group.group_output(position=(0, 260))
        output_node.socket(name="Roughness", socket_type="NodeSocketFloat", default_value=0.5)
        output_node.socket(name="Gloss", socket_type="NodeSocketFloat", default_value=1.0)
        output_node.socket(name="Mask", socket_type="NodeSocketFloat", default_value=1.0)

        # links
        node_group.node_tree.links.new(input_node.outputs["Vector"], tex_roughness_node.inputs["Vector"])
        node_group.node_tree.links.new(input_node.outputs["Vector"], tex_gloss_node.inputs["Vector"])
        node_group.node_tree.links.new(input_node.outputs["Vector"], tex_mask_node.inputs["Vector"])

        node_group.node_tree.links.new(tex_roughness_node.outputs["Color"], output_node.inputs["Roughness"])
        node_group.node_tree.links.new(tex_gloss_node.outputs["Color"], output_node.inputs["Gloss"])
        node_group.node_tree.links.new(tex_mask_node.outputs["Color"], output_node.inputs["Mask"])

        self.node_tree_setup(context, node_group.node_tree)
        return node_group.node_tree

    def node_tree_setup(self, context, node_tree: bpy.types.ShaderNodeTree):
        # Define the mapping of node names to texture suffixes
        node_suffixes = {
            "roughness": "Roughness",
            "gloss": "Gloss",
            "mask": "Mask",
        }

        # Construct the node_to_image dictionary dynamically
        node_to_image = {
            node: self.find_image_in_path(self.asset.path, self.prefs.megascans_size, suffix)
            for node, suffix in node_suffixes.items()
        }

        for node in node_tree.nodes:
            if node.type == "TEX_IMAGE" and node.name in node_to_image:
                self.load_images(node, self.asset.path, node_to_image[node.name])

    def find_image_in_path(self, path: str, size: str, suffix: str) -> str | None:
        sizes = ["8K", "4K", "2K", "1K"]

        if size in sizes:
            sizes.remove(size)
            sizes.insert(0, size)

        for size in sizes:
            for root, _, files in os.walk(path):
                for file in files:
                    if f"{size}_{suffix}" in file:
                        return os.path.splitext(file)[0]

        # If no matching file is found, return None
        return None

    def load_images(self, node: bpy.types.ShaderNode, path: str, filename: str):
        image = self.load_image(path, filename)
        node.image = image
        node.hide = True
        node.mute = image is None

        colorspaces = {
            "roughness": "Non-Color",
            "gloss": "Non-Color",
            "mask": "Non-Color",
        }

        if image and node.name in colorspaces:
            colorspace = colorspaces[node.name]
            if colorspace and bpy.context.scene.view_settings.view_transform in {
                "Standard",
                "Khronos PBR Neutral",
                "AgX",
                "Filmic",
                "Filmic Log",
                "False Color",
                "Raw",
            }:
                image.colorspace_settings.name = colorspace

    def load_image(self, path: str, filename: str) -> bpy.types.Image:
        paths_to_check = [
            os.path.join(path, ""),  # Check in the path first
            os.path.join(path, "Thumbs", "4k"),  # Check in Thumbs/4k
            os.path.join(path, "Thumbs", "2k"),  # Check in Thumbs/2k
            os.path.join(path, "Thumbs", "1k"),  # Check in Thumbs/1k
        ]

        def find_file_in_paths(paths: list, filename: str) -> str:
            """Function to find the file in the defined paths"""
            for path in paths:
                full_path = os.path.join(path, filename)
                if os.path.isfile(full_path):
                    return full_path
            return os.path.join(path, filename)

        def load_image_by_extension(extension: str) -> bpy.types.Image:
            image_name = f"{filename}.{extension}"
            if image_name in bpy.data.images:
                return bpy.data.images[image_name]
            try:
                return bpy.data.images.load(find_file_in_paths(paths_to_check, image_name))
            except RuntimeError:
                return None

        # Try to load .exr first, then .jpg
        return load_image_by_extension("exr") or load_image_by_extension("jpg")


classes = (MBRIDGE_OT_imperfection_group_add,)


register, unregister = bpy.utils.register_classes_factory(classes)
