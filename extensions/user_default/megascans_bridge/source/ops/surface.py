import os

import bpy
from bpy.props import StringProperty
from bpy.types import Operator

from ...qbpy import Material, ShaderNode
from ...qbpy.node_trees import ShaderNodeTree
from ..utils.addon import preferences


class MBRIDGE_OT_surface_base:
    """Base class for surface operators with common functionality"""

    asset_id: StringProperty(options={"SKIP_SAVE", "HIDDEN"})

    def get_asset(self, context):
        self.prefs = preferences()
        self.props = context.scene.mbridge
        assets = self.props.surfaces.get_assets(context)
        self.asset = next((a for a in assets if a.id == self.asset_id), None)

        if self.asset:
            self.mat_name = f"{self.asset.name.lower().replace(' ', '_')}_{self.asset.id}"
            return True
        return False

    def node_tree_setup(self, context, node_tree: bpy.types.ShaderNodeTree):
        node_suffixes = {
            "albedo": "Albedo",
            "ao": "AO",
            "roughness": "Roughness",
            "opacity": "Opacity",
            "normal": "Normal",
            "displacement": "Displacement",
        }

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
            os.path.join(path, ""),
            os.path.join(path, "Thumbs", "4k"),
            os.path.join(path, "Thumbs", "2k"),
            os.path.join(path, "Thumbs", "1k"),
        ]

        def find_file_in_paths(paths: list, filename: str) -> str:
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


class MBRIDGE_OT_surface_add(Operator, MBRIDGE_OT_surface_base):
    bl_label = "Import"
    bl_idname = "mbridge.surface_add"
    bl_options = {"REGISTER", "INTERNAL"}

    @classmethod
    def description(cls, context, properties):
        return "Import the surface as a material\n\nShift  •  Add the material to the material list"

    def invoke(self, context, event):
        if not self.get_asset(context):
            return {"CANCELLED"}

        material = Material.get_material(self.mat_name)
        self.prepare_material(context, material)

        if self.props.surfaces.apply_material:
            for obj in context.selected_objects:
                if obj.type == "MESH":
                    Material.set_material(obj, material, index=-1 if event.shift else 0)

        # Mark as asset if needed
        if self.props.surfaces.mark_asset:
            material.asset_mark()
            override = context.copy()
            override["id"] = material

            if preview := next((f for f in os.listdir(self.asset.path) if "Preview.png" in f), None):
                with context.temp_override(**override):
                    bpy.ops.ed.lib_id_load_custom_preview(filepath=os.path.join(self.asset.path, preview))

        return {"FINISHED"}

    def prepare_material(self, context, material: bpy.types.Material) -> bpy.types.Material:
        node_tree = material.node_tree

        principled_node = next((node for node in node_tree.nodes if node.type == "BSDF_PRINCIPLED"), None)
        material_output_node = next((node for node in node_tree.nodes if node.type == "OUTPUT_MATERIAL"), None)

        if not principled_node or not material_output_node:
            return

        # nodes
        texture_coordinate_node = ShaderNode.texture_coordinate(node_tree, "Texture Coordinates", position=(-1340, 280))
        mapping_node = ShaderNode.mapping(node_tree, "Mapping", position=(-1080, 280))

        tex_albedo_node = ShaderNode.image_texture(node_tree, "albedo", position=(-880, 280))
        tex_ao_node = ShaderNode.image_texture(node_tree, "ao", position=(-880, 240))
        tex_roughness_node = ShaderNode.image_texture(node_tree, "roughness", position=(-880, 200))
        tex_opacity_node = ShaderNode.image_texture(node_tree, name="opacity", position=(-880, 160))
        tex_normal_node = ShaderNode.image_texture(node_tree, "normal", position=(-880, 120))
        tex_displacement_node = ShaderNode.image_texture(node_tree, "displacement", position=(-880, 80))

        gamma_node = ShaderNode.gamma(node_tree, "gamma", position=(-520, 340))

        mix_node = ShaderNode.mix(
            node_tree,
            "Mix Color",
            data_type="RGBA",
            blend_type="MULTIPLY",
            factor=1.0,
            color_b=(1, 1, 1, 1),
            position=(-260, 440),
        )
        normal_map_node = ShaderNode.normal_map(node_tree, "Normal Map", position=(-260, 140))
        displacement_node = ShaderNode.displacement(node_tree, "Displacement", position=(-260, -20))

        # links
        node_tree.links.new(texture_coordinate_node.outputs["UV"], mapping_node.inputs["Vector"])

        node_tree.links.new(mapping_node.outputs["Vector"], tex_albedo_node.inputs["Vector"])
        node_tree.links.new(mapping_node.outputs["Vector"], tex_ao_node.inputs["Vector"])
        node_tree.links.new(mapping_node.outputs["Vector"], tex_roughness_node.inputs["Vector"])
        node_tree.links.new(mapping_node.outputs["Vector"], tex_opacity_node.inputs["Vector"])
        node_tree.links.new(mapping_node.outputs["Vector"], tex_normal_node.inputs["Vector"])
        node_tree.links.new(mapping_node.outputs["Vector"], tex_displacement_node.inputs["Vector"])

        node_tree.links.new(tex_albedo_node.outputs["Color"], gamma_node.inputs["Color"])
        node_tree.links.new(gamma_node.outputs["Color"], mix_node.inputs["A"])
        node_tree.links.new(tex_ao_node.outputs["Color"], mix_node.inputs["B"])

        node_tree.links.new(mix_node.outputs["Result"], principled_node.inputs["Base Color"])
        node_tree.links.new(tex_roughness_node.outputs["Color"], principled_node.inputs["Roughness"])
        node_tree.links.new(tex_opacity_node.outputs["Color"], principled_node.inputs["Alpha"])
        node_tree.links.new(tex_normal_node.outputs["Color"], normal_map_node.inputs["Color"])
        node_tree.links.new(normal_map_node.outputs["Normal"], principled_node.inputs["Normal"])
        node_tree.links.new(tex_displacement_node.outputs["Color"], displacement_node.inputs["Height"])
        node_tree.links.new(displacement_node.outputs["Displacement"], material_output_node.inputs["Displacement"])

        self.node_tree_setup(context, node_tree)
        return material


class MBRIDGE_OT_surface_group_add(Operator, MBRIDGE_OT_surface_base):
    bl_label = "Import"
    bl_idname = "mbridge.surface_group_add"
    bl_options = {"REGISTER", "INTERNAL"}

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
        assets = props.surfaces.get_assets(context)
        asset = next((a for a in assets if a.id == properties.asset_id), None)

        if not asset:
            return "Cannot import - asset not found"

        current_tree = getattr(context.space_data, "edit_tree", None)
        if not current_tree:
            return "Cannot import - no node tree found"
        elif current_tree and asset.id in current_tree.name:
            return "Cannot import in the same node tree"

        return "Import the surface as a node group"

    def invoke(self, context, event):
        if not self.get_asset(context):
            return {"CANCELLED"}

        self.props = context.scene.mbridge
        node_tree = self.prepare_node_tree(context, self.mat_name)

        # Add node to current node editor
        return bpy.ops.node.add_node(
            "INVOKE_DEFAULT",
            use_transform=True,
            settings=[
                {"name": "node_tree", "value": f"bpy.data.node_groups['{node_tree.name}']"},
                {"name": "show_options", "value": "False"},
            ],
            type="ShaderNodeGroup",
        )

    def prepare_node_tree(self, context, name: str) -> bpy.types.ShaderNodeTree:
        node_group = ShaderNodeTree(name)

        input_node = node_group.group_input(position=(-1080, 260))
        input_node.socket(name="Vector", socket_type="NodeSocketVector")
        input_node.socket(
            name="Metallic",
            socket_type="NodeSocketFloat",
            subtype="FACTOR",
            min_value=0.0,
            max_value=1.0,
            default_value=0.0,
        )
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
        tex_roughness_node = node_group.image_texture(name="roughness", position=(-880, 180))
        tex_opacity_node = node_group.image_texture(name="opacity", position=(-880, 140))
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
        output_node.socket(name="Metallic", socket_type="NodeSocketFloat", hide_value=False)
        output_node.socket(name="Roughness", socket_type="NodeSocketFloat", default_value=0.5)
        output_node.socket(name="Alpha", socket_type="NodeSocketFloat", default_value=1.0)
        output_node.socket(name="Normal", socket_type="NodeSocketVector")
        output_node.socket(name="Displacement", socket_type="NodeSocketVector")

        # links
        node_group.node_tree.links.new(input_node.outputs["Vector"], tex_albedo_node.inputs["Vector"])
        node_group.node_tree.links.new(input_node.outputs["Vector"], tex_ao_node.inputs["Vector"])
        node_group.node_tree.links.new(input_node.outputs["Vector"], tex_roughness_node.inputs["Vector"])
        node_group.node_tree.links.new(input_node.outputs["Vector"], tex_opacity_node.inputs["Vector"])
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
        node_group.node_tree.links.new(input_node.outputs["Metallic"], output_node.inputs["Metallic"])
        node_group.node_tree.links.new(tex_roughness_node.outputs["Color"], output_node.inputs["Roughness"])
        node_group.node_tree.links.new(tex_opacity_node.outputs["Color"], output_node.inputs["Alpha"])
        node_group.node_tree.links.new(normal_map_node.outputs["Normal"], output_node.inputs["Normal"])
        node_group.node_tree.links.new(displacement_node.outputs["Displacement"], output_node.inputs["Displacement"])

        self.node_tree_setup(context, node_group.node_tree)
        return node_group.node_tree


classes = (
    MBRIDGE_OT_surface_add,
    MBRIDGE_OT_surface_group_add,
)


register, unregister = bpy.utils.register_classes_factory(classes)
