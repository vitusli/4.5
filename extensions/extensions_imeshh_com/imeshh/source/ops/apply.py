import os
import re
from typing import Union

import bpy
from bpy.props import IntProperty, StringProperty
from bpy.types import Operator

from ..utils.addon import preferences
from ..utils.product import get_asset_path, get_products


def set_material(obj: bpy.types.Object, material: Union[bpy.types.Material, str], index: int = -1):
    """Set material to object.

    Args:
        obj (bpy.types.Object): Object to set material to.
        material (Union[bpy.types.Material, str]): Material to set.
        index (int): Index of material slot. Defaults to -1.
    """
    if obj.type != "MESH":
        return

    if isinstance(material, str):
        material = bpy.data.materials.get(material)

    if 0 <= index < len(obj.data.materials):
        obj.data.materials[index] = material
    elif material not in obj.data.materials[:]:
        obj.data.materials.append(material)


class IMESHH_OT_apply(Operator):

    bl_label = "Apply"
    bl_idname = "imeshh.apply"
    bl_options = {"REGISTER", "INTERNAL"}

    product_id: IntProperty(options={"SKIP_SAVE"})
    filepath: StringProperty(subtype="FILE_PATH", options={"SKIP_SAVE"})

    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT"

    @classmethod
    def description(cls, context, properties):
        return "Apply the material to the selected objects"

    def execute(self, context):
        prefs = preferences()
        props = context.scene.imeshh

        if not self.filepath:
            products = get_products(props)
            product = next((p for p in products if p.get("id") == self.product_id), None)

            if not product:
                self.report({"WARNING"}, "Asset not found in product list")
                return {"CANCELLED"}

            # Get directory name and list .blend files
            asset_path = get_asset_path(product)
            if not os.path.exists(asset_path):
                self.report({"WARNING"}, f"Asset directory not found: {asset_path}")
                return {"CANCELLED"}

            files = [f for f in os.listdir(asset_path) if f.endswith(".blend")]

            # Handle no files case
            if not files:
                self.report({"WARNING"}, f"No .blend files found in {asset_path}")
                return {"CANCELLED"}

            # Handle file selection
            # Try to find exact match for prefs.apply_size
            target_file = next((f for f in files if prefs.apply_size.lower() in f.lower()), None)

            if target_file:
                # Use exact match
                self.filepath = os.path.join(asset_path, target_file)
            else:
                # Try to find size match
                size_pattern = re.compile(r"(\d+)k", re.IGNORECASE)
                target_size = (
                    int(size_pattern.search(prefs.apply_size).group(1)) if size_pattern.search(prefs.apply_size) else 0
                )

                available_sizes = []
                for f in files:
                    match = size_pattern.search(f)
                    if match:
                        size = int(match.group(1))
                        available_sizes.append((size, f))

                if available_sizes:
                    # Sort by size
                    available_sizes.sort()
                    # First try to find bigger size
                    bigger_match = next(((s, f) for s, f in available_sizes if s >= target_size), None)
                    # If no bigger size found, get closest lower size
                    if not bigger_match:
                        bigger_match = available_sizes[-1]

                    best_size, best_file = bigger_match
                    self.filepath = os.path.join(asset_path, best_file)
                else:
                    # Fallback to first file
                    self.filepath = os.path.join(asset_path, files[0])

            # Validate final path
            if not os.path.exists(self.filepath):
                self.report({"WARNING"}, f"Blend file does not exist: {self.filepath}")
                return {"CANCELLED"}

        # Extract material name from file name
        mat_name = os.path.basename(self.filepath).replace(".blend", "")
        material = bpy.data.materials.get(mat_name)

        # Load material if not found in scene
        if not material:
            try:
                with bpy.data.libraries.load(self.filepath, link=prefs.linked) as (data_from, data_to):
                    data_to.materials = [name for name in data_from.materials if name == mat_name]

                if not data_to.materials:
                    self.report({"WARNING"}, f"Material '{mat_name}' not found in {os.path.basename(self.filepath)}")
                    return {"CANCELLED"}

                material = data_to.materials[0]
            except Exception as e:
                self.report({"ERROR"}, f"Failed to load material: {str(e)}")
                print(f"ERROR: Loading material: {str(e)}")
                return {"CANCELLED"}

        # Apply to selected objects
        applied_count = 0
        for obj in context.selected_objects:
            if obj.type != "MESH":
                continue
            set_material(obj, material)
            applied_count += 1

        # Report results
        if applied_count == 0:
            self.report({"WARNING"}, "No mesh objects selected to apply material to")
        else:
            self.report({"INFO"}, f"Applied '{material.name}' to {applied_count} object(s)")

        context.area.tag_redraw()
        return {"FINISHED"}


class IMESHH_OT_apply_local(Operator):

    bl_label = "Apply"
    bl_idname = "imeshh.apply_local"
    bl_options = {"REGISTER", "INTERNAL"}

    filepath: StringProperty(subtype="FILE_PATH", options={"SKIP_SAVE"})

    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT"

    @classmethod
    def description(cls, context, properties):
        return "Apply the material to the selected objects"

    def execute(self, context):
        prefs = preferences()

        if not self.filepath or not os.path.exists(self.filepath):
            self.report({"WARNING"}, "Invalid file path")
            return {"CANCELLED"}

        try:
            # Get available materials from the blend file
            with bpy.data.libraries.load(self.filepath) as (data_from, data_to):
                available_material_names = data_from.materials

            if not available_material_names:
                self.report({"WARNING"}, f"No materials found in {os.path.basename(self.filepath)}")
                return {"CANCELLED"}

            # Import new materials
            imported_count = 0
            existing_materials = set(bpy.data.materials.keys())
            to_import = [name for name in available_material_names if name not in existing_materials]

            if to_import:
                with bpy.data.libraries.load(self.filepath, link=prefs.linked) as (data_from, data_to):
                    data_to.materials = to_import
                imported_count = len(data_to.materials)

            # Collect all materials to apply (excluding grease pencil materials)
            materials_to_apply = []
            for name in available_material_names:
                mat = bpy.data.materials.get(name)
                if mat and not getattr(mat, "is_grease_pencil", False):
                    materials_to_apply.append(mat)

            if not materials_to_apply:
                self.report({"WARNING"}, "No applicable materials found")
                return {"CANCELLED"}

            # Apply materials to selected mesh objects
            applied_count = 0
            for obj in context.selected_objects:
                if obj.type == "MESH":
                    for material in materials_to_apply:
                        set_material(obj, material)
                    applied_count += 1

            if applied_count == 0:
                self.report({"WARNING"}, "No mesh objects selected to apply material to")
                return {"FINISHED"}

            # Create readable material list for the report
            material_info = ""
            if len(materials_to_apply) <= 3:
                material_info = f"({', '.join(mat.name for mat in materials_to_apply)})"

            self.report(
                {"INFO"}, f"Applied {len(materials_to_apply)} material(s) {material_info} to {applied_count} object(s)"
            )

            context.area.tag_redraw()
            return {"FINISHED"}

        except Exception as e:
            self.report({"ERROR"}, f"Failed: {str(e)}")
            print(f"ERROR: {str(e)}")
            return {"CANCELLED"}


classes = (
    IMESHH_OT_apply,
    IMESHH_OT_apply_local,
)


register, unregister = bpy.utils.register_classes_factory(classes)
