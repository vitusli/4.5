import os

import bpy
from bpy.props import StringProperty
from bpy.types import Operator

from ...qbpy.node_trees import ShaderNodeTree
from ..utils.addon import preferences


class MBRIDGE_OT_atlas_group_add(Operator):
    bl_label = "Import"
    bl_idname = "mbridge.atlas_group_add"
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
        assets = props.atlases.get_assets(context)
        asset = next((a for a in assets if a.id == properties.asset_id), None)

        if not asset:
            return "Cannot import - asset not found"

        current_tree = getattr(context.space_data, "edit_tree", None)
        if not current_tree:
            return "Cannot import - no node tree found"
        elif current_tree and current_tree.name == asset.path.lower().replace(" ", "_"):
            return "Cannot import in the same node tree"

        return "Import the atlases as a node group"

    def invoke(self, context, event):
        self.prefs = preferences()
        self.props = context.scene.mbridge

        assets = self.props.atlases.get_assets(context)
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

        input_node = node_group.group_input(position=(-1080, 260))
        input_node.socket(name="Vector", socket_type="NodeSocketVector")
        input_node.socket(
            name="Normal Strength", socket_type="NodeSocketFloat", min_value=0.0, max_value=10.0, default_value=1.0
        )
        input_node.socket(
            name="Displacement Midlevel",
            socket_type="NodeSocketFloat",
            min_value=0.0,
            max_value=1000.0,
            default_value=0.5,
        )
        input_node.socket(
            name="Displacement Scale",
            socket_type="NodeSocketFloat",
            min_value=0.0,
            max_value=1000.0,
            default_value=0.025,
        )

        tex_albedo_node = node_group.image_texture(name="albedo", position=(-880, 280))
        tex_ao_node = node_group.image_texture(name="ao", position=(-880, 240))
        tex_roughness_node = node_group.image_texture(name="roughness", position=(-880, 200))
        tex_opacity_node = node_group.image_texture(name="opacity", position=(-880, 160))
        tex_translucency_node = node_group.image_texture(name="translucency", position=(-880, 120))
        tex_normal_node = node_group.image_texture(name="normal", position=(-880, 80))
        tex_displacement_node = node_group.image_texture(name="displacement", position=(-880, 40))

        gamma_node = node_group.gamma(name="gamma", position=(-520, 340))

        mix_node = node_group.mix(
            name="mix_color",
            data_type="RGBA",
            blend_type="MULTIPLY",
            factor=1.0,
            color_b=(1, 1, 1, 1),
            position=(-260, 440),
        )
        normal_map_node = node_group.normal_map(name="normal_map", position=(-260, 140))
        displacement_node = node_group.displacement(name="Displacement", scale=0.025, position=(-260, -20))

        output_node = node_group.group_output(position=(0, 260))
        output_node.socket(name="Base Color", socket_type="NodeSocketColor", default_value=(0.8, 0.8, 0.8, 1.0))
        output_node.socket(name="Roughness", socket_type="NodeSocketFloat", default_value=0.5)
        output_node.socket(name="Alpha", socket_type="NodeSocketFloat", default_value=1.0)
        output_node.socket(name="Translucency", socket_type="NodeSocketColor", default_value=(0.8, 0.8, 0.8, 1.0))
        output_node.socket(name="Normal", socket_type="NodeSocketVector")
        output_node.socket(name="Displacement", socket_type="NodeSocketVector")

        # links
        node_group.node_tree.links.new(input_node.outputs["Vector"], tex_albedo_node.inputs["Vector"])
        node_group.node_tree.links.new(input_node.outputs["Vector"], tex_ao_node.inputs["Vector"])
        node_group.node_tree.links.new(input_node.outputs["Vector"], tex_roughness_node.inputs["Vector"])
        node_group.node_tree.links.new(input_node.outputs["Vector"], tex_opacity_node.inputs["Vector"])
        node_group.node_tree.links.new(input_node.outputs["Vector"], tex_translucency_node.inputs["Vector"])
        node_group.node_tree.links.new(input_node.outputs["Vector"], tex_normal_node.inputs["Vector"])
        node_group.node_tree.links.new(input_node.outputs["Vector"], tex_displacement_node.inputs["Vector"])
        node_group.node_tree.links.new(input_node.outputs["Normal Strength"], normal_map_node.inputs["Strength"])
        node_group.node_tree.links.new(
            input_node.outputs["Displacement Midlevel"], displacement_node.inputs["Midlevel"]
        )
        node_group.node_tree.links.new(input_node.outputs["Displacement Scale"], displacement_node.inputs["Scale"])

        node_group.node_tree.links.new(tex_albedo_node.outputs["Color"], gamma_node.inputs["Color"])
        node_group.node_tree.links.new(gamma_node.outputs["Color"], mix_node.inputs["A"])
        node_group.node_tree.links.new(tex_ao_node.outputs["Color"], mix_node.inputs["B"])
        node_group.node_tree.links.new(tex_normal_node.outputs["Color"], normal_map_node.inputs["Color"])
        node_group.node_tree.links.new(tex_displacement_node.outputs["Color"], displacement_node.inputs["Height"])

        node_group.node_tree.links.new(mix_node.outputs["Result"], output_node.inputs["Base Color"])
        node_group.node_tree.links.new(tex_roughness_node.outputs["Color"], output_node.inputs["Roughness"])
        node_group.node_tree.links.new(tex_opacity_node.outputs["Color"], output_node.inputs["Alpha"])
        node_group.node_tree.links.new(tex_translucency_node.outputs["Color"], output_node.inputs["Translucency"])
        node_group.node_tree.links.new(normal_map_node.outputs["Normal"], output_node.inputs["Normal"])
        node_group.node_tree.links.new(displacement_node.outputs["Displacement"], output_node.inputs["Displacement"])

        self.node_tree_setup(context, node_group.node_tree)
        return node_group.node_tree

    def node_tree_setup(self, context, node_tree: bpy.types.ShaderNodeTree):
        # Define the mapping of node names to texture suffixes
        node_suffixes = {
            "albedo": "Albedo",
            "ao": "AO",
            "roughness": "Roughness",
            "opacity": "Opacity",
            "translucency": "Translucency",
            "normal": "Normal",
            "displacement": "Displacement",
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
            "albedo": None,
            "ao": "Non-Color",
            "roughness": "Non-Color",
            "opacity": "Non-Color",
            "translucency": None,
            "normal": "Non-Color",
            "displacement": "Non-Color",
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


classes = (MBRIDGE_OT_atlas_group_add,)


register, unregister = bpy.utils.register_classes_factory(classes)
