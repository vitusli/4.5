import os

import bpy
from bpy.props import StringProperty
from bpy.types import Operator

from ...qbpy.node_trees import ShaderNodeTree
from ..utils.addon import preferences


class MBRIDGE_OT_decal_group_add(Operator):
    bl_label = "Import"
    bl_idname = "mbridge.decal_group_add"
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
        assets = props.decals.get_assets(context)
        asset = next((a for a in assets if a.id == properties.asset_id), None)

        if not asset:
            return "Cannot import - asset not found"

        current_tree = getattr(context.space_data, "edit_tree", None)
        if not current_tree:
            return "Cannot import - no node tree found"
        elif current_tree and current_tree.name == asset.path.lower().replace(" ", "_"):
            return "Cannot import in the same node tree"

        return "Import the decal as a node group"

    def invoke(self, context, event):
        self.prefs = preferences()
        self.props = context.scene.mbridge

        assets = self.props.decals.get_assets(context)
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

        return {"FINISHED"}

    def prepare_node_tree(self, context, name: str) -> bpy.types.ShaderNodeTree:
        node_group = ShaderNodeTree(name)

        # Create input node with all sockets
        input_node = node_group.group_input(position=(-1080, 260))
        input_sockets = [
            ("Vector", "NodeSocketVector", None, None, None),
            ("Normal Strength", "NodeSocketFloat", 0.0, 10.0, 1.0),
            ("Displacement Midlevel", "NodeSocketFloat", 0.0, 1000.0, 0.5),
            ("Displacement Scale", "NodeSocketFloat", 0.0, 1000.0, 0.025),
        ]
        for name, socket_type, min_value, max_value, default_value in input_sockets:
            input_node.socket(
                name=name,
                socket_type=socket_type,
                min_value=min_value,
                max_value=max_value,
                default_value=default_value,
            )

        # Create texture nodes
        texture_configs = {
            "albedo": {"position": (-880, 280)},
            "ao": {"position": (-880, 240)},
            "roughness": {"position": (-880, 180)},
            "opacity": {"position": (-880, 140)},
            "normal": {"position": (-880, 80)},
            "displacement": {"position": (-880, 40)},
        }

        texture_nodes = {}
        for name, config in texture_configs.items():
            texture_nodes[name] = node_group.image_texture(name=name, position=config["position"])
            # Connect Vector input to all texture nodes
            node_group.node_tree.links.new(input_node.outputs["Vector"], texture_nodes[name].inputs["Vector"])

        gamma_node = node_group.gamma(name="gamma", position=(-520, 340))

        # Create processing nodes
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

        # Create output node with all sockets
        output_node = node_group.group_output(position=(0, 260))
        output_sockets = [
            ("Base Color", "NodeSocketColor", (0.8, 0.8, 0.8, 1.0)),
            ("Roughness", "NodeSocketFloat", 0.5),
            ("Alpha", "NodeSocketFloat", 1.0),
            ("Normal", "NodeSocketVector", None),
            ("Displacement", "NodeSocketVector", None),
        ]
        for name, socket_type, default_value in output_sockets:
            output_node.socket(name=name, socket_type=socket_type, default_value=default_value)

        # Connect processing nodes
        node_group.node_tree.links.new(input_node.outputs["Normal Strength"], normal_map_node.inputs["Strength"])
        node_group.node_tree.links.new(
            input_node.outputs["Displacement Midlevel"], displacement_node.inputs["Midlevel"]
        )
        node_group.node_tree.links.new(input_node.outputs["Displacement Scale"], displacement_node.inputs["Scale"])

        # Connect texture nodes to processing nodes
        node_group.node_tree.links.new(texture_nodes["albedo"].outputs["Color"], gamma_node.inputs["Color"])
        node_group.node_tree.links.new(gamma_node.outputs["Color"], mix_node.inputs["A"])
        node_group.node_tree.links.new(texture_nodes["ao"].outputs["Color"], mix_node.inputs["B"])
        node_group.node_tree.links.new(texture_nodes["normal"].outputs["Color"], normal_map_node.inputs["Color"])
        node_group.node_tree.links.new(
            texture_nodes["displacement"].outputs["Color"], displacement_node.inputs["Height"]
        )

        # Connect to outputs
        output_connections = [
            (mix_node.outputs["Result"], "Base Color"),
            (texture_nodes["roughness"].outputs["Color"], "Roughness"),
            (texture_nodes["opacity"].outputs["Color"], "Alpha"),
            (normal_map_node.outputs["Normal"], "Normal"),
            (displacement_node.outputs["Displacement"], "Displacement"),
        ]
        for source, target in output_connections:
            node_group.node_tree.links.new(source, output_node.inputs[target])

        self.node_tree_setup(context, node_group.node_tree)
        return node_group.node_tree

    def node_tree_setup(self, context, node_tree: bpy.types.ShaderNodeTree):
        # Define texture node configurations
        texture_config = {
            "albedo": {"suffix": "Albedo", "colorspace": None},
            "ao": {"suffix": "AO", "colorspace": "Non-Color"},
            "roughness": {"suffix": "Roughness", "colorspace": "Non-Color"},
            "opacity": {"suffix": "Opacity", "colorspace": "Non-Color"},
            "normal": {"suffix": "Normal", "colorspace": "Non-Color"},
            "displacement": {"suffix": "Displacement", "colorspace": "Non-Color"},
        }

        # Load images for each texture node
        for node in node_tree.nodes:
            if node.type == "TEX_IMAGE" and node.name in texture_config:
                config = texture_config[node.name]
                image_name = self.find_image_in_path(self.asset.path, self.prefs.megascans_size, config["suffix"])
                image = self.load_image(self.asset.path, image_name)

                node.image = image
                node.hide = True
                node.mute = image is None

                # Set colorspace if image exists and colorspace is specified
                if image and config["colorspace"] and self.should_set_colorspace(context):
                    image.colorspace_settings.name = config["colorspace"]

    def should_set_colorspace(self, context):
        return context.scene.view_settings.view_transform in {
            "Standard",
            "Khronos PBR Neutral",
            "Agx",
            "Filmic",
            "Filmic Log",
            "False Color",
            "Raw",
        }

    def find_image_in_path(self, path: str, preferred_size: str, suffix: str) -> str | None:
        sizes = ["8K", "4K", "2K", "1K"]

        # Prioritize preferred size
        if preferred_size in sizes:
            sizes.remove(preferred_size)
            sizes.insert(0, preferred_size)

        for size in sizes:
            for root, _, files in os.walk(path):
                for file in files:
                    if f"{size}_{suffix}" in file:
                        return os.path.splitext(file)[0]
        return None

    def load_image(self, path: str, filename: str) -> bpy.types.Image:
        if not filename:
            return None

        # Check for the image in these directories
        search_paths = [
            path,
            os.path.join(path, "Thumbs", "4k"),
            os.path.join(path, "Thumbs", "2k"),
            os.path.join(path, "Thumbs", "1k"),
        ]

        # Try to load JPG first, then EXR
        for ext in ["jpg", "exr"]:
            image_name = f"{filename}.{ext}"
            if image_name in bpy.data.images:
                return bpy.data.images[image_name]

            for search_path in search_paths:
                full_path = os.path.join(search_path, image_name)
                if os.path.isfile(full_path):
                    try:
                        return bpy.data.images.load(full_path)
                    except RuntimeError:
                        continue

        return None


classes = (MBRIDGE_OT_decal_group_add,)


register, unregister = bpy.utils.register_classes_factory(classes)
