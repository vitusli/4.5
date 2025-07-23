import os
import re
import subprocess

import bpy
from bpy.props import IntProperty, StringProperty
from bpy.types import Operator

from ..utils.addon import package, preferences
from ..utils.product import get_asset_path, get_products


class IMESHH_OT_blend_open(Operator):

    bl_label = "Open Blend File"
    bl_idname = "imeshh.blend_open"
    bl_options = {"REGISTER", "INTERNAL"}

    filepath: StringProperty(subtype="FILE_PATH", options={"SKIP_SAVE"})

    @classmethod
    def description(cls, context, properties):
        return "Open the blend file"

    def execute(self, context):
        if not os.path.exists(self.filepath):
            self.report({"ERROR"}, f"File not found: {self.filepath}")
            return {"CANCELLED"}

        subprocess.Popen([bpy.app.binary_path, "--factory-startup", self.filepath])
        return {"FINISHED"}


class IMESHH_OT_options(Operator):

    bl_label = "Show Options"
    bl_idname = "imeshh.options"
    bl_options = {"REGISTER", "INTERNAL"}

    product_id: IntProperty(options={"SKIP_SAVE"})
    filepath: StringProperty(subtype="FILE_PATH", options={"SKIP_SAVE"})

    @classmethod
    def description(cls, context, properties):
        return "Show options of the asset"

    def show_options(self, context, product_id, filepath):
        def draw(self, context, filepath=filepath):
            layout = self.layout
            prefs = preferences()
            props = context.scene.imeshh

            products = get_products(props)
            if product := next((p for p in products if p.get("id") == product_id), None):
                if filepath is not None:
                    asset_path = os.path.dirname(filepath)
                else:
                    asset_path = get_asset_path(product)
                
                blend_files = (
                    [file for file in os.listdir(asset_path) if file.endswith(".blend")]
                    if os.path.exists(asset_path)
                    else []
                )

                if product.get("asset_type") in "material":
                    # Apply options for existing blend files
                    # Sort files by resolution (1k, 2k, 4k, 8k, 16k)
                    def get_resolution(filename):
                        match = re.search(r"_(\d+)k\.blend$", filename.lower())
                        return int(match.group(1)) if match else 0

                    for file in sorted(blend_files, key=get_resolution):
                        label = file.split("_")[-1].replace(".blend", "").title()
                        layout.operator("imeshh.apply", text=f"Apply {label}", icon="MATERIAL").filepath = os.path.join(
                            asset_path, file
                        )

                    # Download options for missing files
                    downloads = product.get("downloads", [])
                    if len(downloads) > 1:
                        layout.separator()
                        for download in downloads:
                            size = download.get("name", "").split("_")[-1].replace(".zip", "").lower()

                            # Skip if this size already exists in blend files
                            if re.search(r"124k|1[+-]2[+-]4k", size) and any(
                                re.search(r"(?:1|2|4)k", f.lower()) for f in blend_files
                            ):
                                continue
                            elif size.lower() in " ".join(blend_files).lower():
                                continue

                            op = layout.operator(
                                "imeshh.download", text=f"Download {size.replace('.zip', '').title()}", icon="IMPORT"
                            )
                            op.product_id = product.get("id")
                            op.download_id = download.get("id")

                    # File operations if asset exists
                    if blend_files:
                        layout.separator()
                        blend_file = next((f for f in blend_files if prefs.apply_size.lower() in f.lower()), None)
                        if blend_file:
                            layout.operator("imeshh.blend_open", icon="FILE_BLEND", text="Open Blend File").filepath = (
                                os.path.join(asset_path, blend_file)
                            )
                        layout.operator("wm.path_open", icon="FILEBROWSER", text="Open Folder").filepath = asset_path

                elif product.get("asset_type") in {"geonode", "fx"}:
                    for file in blend_files:
                        filepath = os.path.join(asset_path, file)
                        label = file.split("_")[-1].replace(".blend", "").title()
                        layout.operator(
                            "imeshh.append",
                            icon="LINK_BLEND" if prefs.linked else "APPEND_BLEND",
                            text=f"{'Link' if prefs.linked else 'Append'} {label}",
                        ).filepath = filepath

                    if blend_files:
                        layout.separator()
                        layout.operator("wm.path_open", icon="FILEBROWSER", text="Open Folder").filepath = asset_path
                else:
                    if blend_files:
                        layout.separator()
                        # Extract basename and remove date pattern
                        basename = os.path.basename(asset_path)
                        basename_without_date = re.sub(r"_\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}", "", basename)
                        if filepath is not None:
                            blend_file = filepath;
                        else:
                            blend_file = os.path.join(asset_path, f"{basename_without_date}.blend")
                        if os.path.exists(blend_file):
                            layout.operator("imeshh.blend_open", icon="FILE_BLEND", text="Open Blend File").filepath = (
                                blend_file
                            )

                        layout.operator("wm.path_open", icon="FILEBROWSER", text="Open Folder").filepath = asset_path

                layout.separator()
                layout.operator("wm.url_open", icon="URL", text="View Online").url = product.get("permalink")
                layout.operator("preferences.addon_show", icon="PREFERENCES", text="Preferences").module = package

        context.window_manager.popup_menu(draw, title="Options", icon="QUESTION")

    def execute(self, context):
        self.show_options(context, self.product_id, filepath=self.filepath)
        return {"FINISHED"}


class IMESHH_OT_options_local(Operator):

    bl_label = "Show Options"
    bl_idname = "imeshh.options_local"
    bl_options = {"REGISTER", "INTERNAL"}

    filepath: StringProperty(subtype="FILE_PATH", options={"SKIP_SAVE"})

    @classmethod
    def description(cls, context, properties):
        return "Show options of the asset"

    def show_options(self, context, filepath):
        def draw(self, context):
            layout = self.layout

            if os.path.exists(filepath):
                asset_dir = os.path.dirname(filepath)
                blend_files = [f for f in os.listdir(asset_dir) if f.endswith(".blend")]

                # Group files by base name (excluding resolution suffix)
                material_groups = {}
                resolution_pattern = re.compile(r"_(\d+k)\.blend$", re.IGNORECASE)

                for file in blend_files:
                    match = resolution_pattern.search(file)
                    base_name = resolution_pattern.sub("", file).replace(".blend", "") # Remove resolution and .blend
                    if base_name not in material_groups:
                        material_groups[base_name] = []
                    material_groups[base_name].append(file)

                # Sort resolutions and create apply buttons
                def get_resolution_value(filename):
                     match = resolution_pattern.search(filename)
                     if match:
                         size_str = match.group(1).lower().replace("k", "")
                         try:
                             return int(size_str) if size_str else 0
                         except ValueError:
                             return 0
                     return 0
                for base_name, files in material_groups.items():
                    if resolution_pattern.sub("", os.path.basename(filepath)).replace(".blend", "") != base_name:
                        continue
                    # Sort files by resolution
                    sorted_files = sorted(files, key=get_resolution_value)
                    if sorted_files:
                        if preferences().local.asset_type == "MATERIAL":
                            layout.label(text=base_name.replace("_", " ")) # Display base name as a label
                            for file in sorted_files:
                                print(file)
                                match = resolution_pattern.search(file)
                                resolution_label = match.group(1).upper() if match else "01"
                                op = layout.operator("imeshh.apply_local", text=f"Apply {resolution_label}", icon="MATERIAL")
                                op.filepath = os.path.join(asset_dir, file)

                # Add separator if there were any blend files processed
                if blend_files:
                    layout.separator()

                # Always show Open Blend File and Open Folder for the initially selected file
                if os.path.exists(filepath):
                    layout.operator("imeshh.blend_open", icon="FILE_BLEND", text="Open Blend File").filepath = filepath
                    layout.operator("wm.path_open", icon="FILEBROWSER", text="Open Folder").filepath = os.path.dirname(
                        filepath
                    )

        context.window_manager.popup_menu(draw, title="Options", icon="QUESTION")

    def execute(self, context):
        self.show_options(context, self.filepath)
        return {"FINISHED"}


classes = (
    IMESHH_OT_blend_open,
    IMESHH_OT_options,
    IMESHH_OT_options_local,
)


register, unregister = bpy.utils.register_classes_factory(classes)
