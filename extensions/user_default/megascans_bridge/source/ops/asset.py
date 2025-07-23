import os
import re

import bpy
from bpy.props import StringProperty
from bpy.types import Operator

from ...qbpy import Collection, Import, Material, Object, ShaderNode
from ...qbpy.node_trees import edit_node_tree
from ..utils.addon import preferences
from ..utils.node_group import prepare_lod_group


class MBRIDGE_OT_asset_add(Operator):
    bl_label = "Import"
    bl_idname = "mbridge.asset_add"
    bl_options = {"REGISTER", "INTERNAL"}

    asset_id: StringProperty(options={"SKIP_SAVE", "HIDDEN"})

    @classmethod
    def description(cls, context, properties):
        return "Import the asset"

    def invoke(self, context, event):
        self.prefs = preferences()
        self.props = context.scene.mbridge

        assets = self.props.assets.get_assets(context)
        self.asset = next((a for a in assets if a.id == self.asset_id), None)
        if not self.asset:
            return {"FINISHED"}

        # Create and link collection
        self.col_name = f"{self.asset.name.lower().replace(' ', '_')}_{self.asset.id}"
        self.collection = Collection.get_collection(self.col_name)
        Collection.link_collection(self.collection)

        # Handle LOD imports if enabled
        if self.props.assets.import_lods:
            # Determine which LODs to import
            if self.prefs.model.import_all_lods:
                self.lods = [f"LOD{i}" for i in range(9)]  # LOD0 through LOD8
            else:
                self.lods = sorted(self.prefs.model.lods, key=lambda x: int(x[3:]))

            # Find all existing LOD files
            self.files = []
            for lod in self.lods:
                filename = f"{self.asset.id}_{lod}.{self.prefs.model.format}"
                for root, _, files in os.walk(self.asset.path):
                    if matching_file := next((f for f in files if filename in f), None):
                        self.files.append(os.path.join(root, matching_file))
                        break

            self.import_lods(context)
        else:
            return self.execute(context)

        return {"FINISHED"}

    def execute(self, context):
        # Find the LOD0 file in the asset path
        filename = f"{self.asset.id}_LOD0.{self.prefs.model.format}"
        filepath = None

        for root, _, files in os.walk(self.asset.path):
            if matching_file := next((f for f in files if filename in f), None):
                filepath = os.path.join(root, matching_file)
                break

        if not filepath:
            self.report({"WARNING"}, f"{filename} doesn't exist. Please re-download the asset.")
            return {"CANCELLED"}

        # check if the object already exists
        if mesh := next((mesh for mesh in bpy.data.meshes if self.asset.id in mesh.name), None):
            self.report({"WARNING"}, f"{mesh.name} already exists. Please purge unused data.")
            return {"CANCELLED"}

        # import the asset
        Import.import_alembic(filepath, scale=0.01) if self.prefs.model.format == "abc" else Import.import_fbx(filepath)
        # process the selected objects
        self.process_selected_objects(context)
        # apply the material
        self.apply_material(context)

        return {"FINISHED"}

    def import_lods(self, context):
        if not self.files:
            self.report({"WARNING"}, "LODs doesn't exist. Please re-download the asset.")
            return {"CANCELLED"}

        for filepath in self.files:
            # check if the object already exists
            filename = os.path.splitext(os.path.basename(filepath))[0]
            if any(
                self.asset.id in mesh.name and filename.lower().split("_")[-1] in mesh.name.lower()
                for mesh in bpy.data.meshes
            ):
                self.report({"WARNING"}, f"{filename} already exists. Please purge unused data.")
                continue

            # import the asset
            Import.import_alembic(filepath, scale=0.01) if self.prefs.model.format == "abc" else Import.import_fbx(
                filepath
            )
            # process the selected objects
            self.process_selected_objects(context)
            # apply the material
            self.apply_material(context)

        if self.props.assets.create_lod_group:
            collections = self.collection.children if self.collection.children else [self.collection]
            for col in collections:
                name_suffix = col.name.split(self.asset.id, 1)[1]
                prepare_lod_group(
                    context, name=f".{self.asset.id}{name_suffix}_LodGroup", collection=col, lods=self.lods
                )

        return {"FINISHED"}

    def process_selected_objects(self, context):
        if len(context.selected_objects) > 1:
            for obj in context.selected_objects:
                if obj.type != "MESH":
                    continue

                # hide the material with '.'
                for mat in obj.data.materials:
                    mat.name = f".{mat.name}" if mat else None

                # ensure the object is parented to the collection
                if obj.parent:
                    obj.matrix_world = obj.parent.matrix_world @ obj.matrix_world
                    Object.unlink_object(obj.parent)
                    obj.parent = None

                # ensure the collection is linked
                col_name = f"{self.col_name}{obj.name.split(self.asset.id, 1)[1]}"
                col = Collection.get_collection(re.sub(r"(?i)_lod\d+$", "", col_name))
                Collection.link_collection(col, self.collection)

                # ensure the object is linked to the collection
                Object.link_object(obj, col)
                Object.rename_object(obj, col_name)
                obj.location = context.scene.cursor.location
        else:
            for obj in context.selected_objects:
                if obj.type != "MESH":
                    continue

                # hide the material with '.'
                for mat in obj.data.materials:
                    mat.name = f".{mat.name}" if mat else None

                Object.link_object(obj, self.collection)
                Object.rename_object(obj, f"{self.col_name}{obj.name.split(self.asset.id, 1)[1]}")
                obj.location = context.scene.cursor.location

    def apply_material(self, context):
        material = Material.get_material(self.col_name)
        self.prepare_material(context, material)

        for obj in context.selected_objects:
            if obj.type != "MESH":
                continue
            Material.set_material(obj, material, index=0)

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
        tex_normal_node = ShaderNode.image_texture(node_tree, "normal", position=(-880, 160))
        tex_displacement_node = ShaderNode.image_texture(node_tree, "displacement", position=(-880, 120))

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
        normal_map_node = ShaderNode.normal_map(node_tree, "Normal Map", position=(-260, 180))
        displacement_node = ShaderNode.displacement(node_tree, "Displacement", position=(-260, 20))

        # links
        node_tree.links.new(texture_coordinate_node.outputs["UV"], mapping_node.inputs["Vector"])

        node_tree.links.new(mapping_node.outputs["Vector"], tex_albedo_node.inputs["Vector"])
        node_tree.links.new(mapping_node.outputs["Vector"], tex_ao_node.inputs["Vector"])
        node_tree.links.new(mapping_node.outputs["Vector"], tex_roughness_node.inputs["Vector"])
        node_tree.links.new(mapping_node.outputs["Vector"], tex_normal_node.inputs["Vector"])
        node_tree.links.new(mapping_node.outputs["Vector"], tex_displacement_node.inputs["Vector"])

        node_tree.links.new(tex_albedo_node.outputs["Color"], gamma_node.inputs["Color"])
        node_tree.links.new(gamma_node.outputs["Color"], mix_node.inputs["A"])
        node_tree.links.new(tex_ao_node.outputs["Color"], mix_node.inputs["B"])
        node_tree.links.new(mix_node.outputs["Result"], principled_node.inputs["Base Color"])
        node_tree.links.new(tex_roughness_node.outputs["Color"], principled_node.inputs["Roughness"])
        node_tree.links.new(tex_normal_node.outputs["Color"], normal_map_node.inputs["Color"])
        node_tree.links.new(normal_map_node.outputs["Normal"], principled_node.inputs["Normal"])
        node_tree.links.new(tex_displacement_node.outputs["Color"], displacement_node.inputs["Height"])
        node_tree.links.new(displacement_node.outputs["Displacement"], material_output_node.inputs["Displacement"])

        self.node_tree_setup(context, node_tree)
        return material

    def node_tree_setup(self, context, node_tree: bpy.types.ShaderNodeTree):
        # Define the mapping of node names to texture suffixes
        node_suffixes = {
            "albedo": "Albedo",
            "ao": "AO",
            "roughness": "Roughness",
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


class MBRIDGE_OT_material_edit(Operator):
    bl_label = "Edit Material"
    bl_idname = "mbridge.material_edit"
    bl_options = {"REGISTER", "INTERNAL"}

    asset_id: StringProperty(options={"SKIP_SAVE", "HIDDEN"})

    @classmethod
    def description(cls, context, properties):
        return "Edit the material in a new window"

    def execute(self, context):
        self.props = context.scene.mbridge

        assets = self.props.get_assets(context)
        self.asset = next((a for a in assets if a.id == self.asset_id), None)
        if self.asset:
            mat_name = f"{self.asset.name.lower().replace(' ', '_')}_{self.asset.id}"

            if material := bpy.data.materials.get(mat_name):
                edit_node_tree(material.node_tree)
            else:
                self.report({"WARNING"}, f"{mat_name} doesn't exist. Please re-import the asset.")

        return {"FINISHED"}


classes = (
    MBRIDGE_OT_asset_add,
    MBRIDGE_OT_material_edit,
)


register, unregister = bpy.utils.register_classes_factory(classes)
