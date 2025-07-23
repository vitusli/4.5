import os

import bpy
from bpy.props import (
    BoolProperty,
    EnumProperty,
    FloatProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)
from bpy.types import AddonPreferences, PropertyGroup

from .addon import package


class MBRIDGE_AP_model(PropertyGroup):
    format: EnumProperty(
        name="Format",
        description="Format of the model to import",
        items=(
            ("fbx", "FBX", "Import as FBX"),
            ("abc", "ABC", "Import as ABC"),
        ),
        default="fbx",
    )

    import_all_lods: BoolProperty(
        name="Import all LODs",
        description="Import all levels of detail",
        default=False,
    )

    lods: EnumProperty(
        name="LODs",
        description="Level of detail",
        items=(
            ("LOD0", "LOD 0", ""),
            ("LOD1", "LOD 1", ""),
            ("LOD2", "LOD 2", ""),
            ("LOD3", "LOD 3", ""),
            ("LOD4", "LOD 4", ""),
            ("LOD5", "LOD 5", ""),
            ("LOD6", "LOD 6", ""),
            ("LOD7", "LOD 7", ""),
            ("LOD8", "LOD 8", ""),
        ),
        options={"ENUM_FLAG"},
        default={"LOD0", "LOD2", "LOD4", "LOD6"},
    )


class MBRIDGE_AP_preferences(AddonPreferences):
    bl_idname = package

    tabs: EnumProperty(
        name="Tabs",
        items=(
            ("LIBRARY", "Library", ""),
            ("MODEL", "Models", ""),
            ("PREVIEW", "Preview", ""),
        ),
    )

    def update_megascans_library_path(self, context):
        if self.megascans_library_path:
            json_file_path = os.path.join(bpy.path.abspath(self.megascans_library_path), "assetsData.json")
            if not os.path.isfile(json_file_path):
                print(f"Warning: {json_file_path} does not exist")

    megascans_library_path: StringProperty(
        name="Path",
        description="Path to the megascans library",
        subtype="DIR_PATH",
        update=update_megascans_library_path,
        default=os.path.join(os.path.expanduser("~"), "Documents", "Megascans Library", "Downloaded", ""),
    )

    megascans_size: EnumProperty(
        name="Size",
        description="Megascans assets size to import",
        items=(
            ("1K", "1K Resolution", "1024x1024"),
            ("2K", "2K Resolution", "2048x2048"),
            ("4K", "4K Resolution", "4096x4096"),
            ("8K", "8K Resolution", "8192x8192"),
        ),
        default="4K",
    )

    model: PointerProperty(type=MBRIDGE_AP_model)

    preview_limit: IntProperty(
        name="Limit",
        description="Limit of assets to show in the preview",
        min=1,
        soft_min=5,
        soft_max=25,
        max=36,
        default=16,
    )

    preview_scale: FloatProperty(
        name="Scale",
        description="Scale of the asset preview",
        min=3,
        soft_max=6,
        max=100,
        default=6,
    )

    popup_scale: FloatProperty(
        name="Popup",
        description="Popup scale of the asset preview",
        min=0.5,
        soft_max=1.5,
        max=2,
        default=1,
    )

    show_asset_name: BoolProperty(
        name="Show Names",
        description="Show asset names",
        default=True,
    )

    def draw(self, context):
        layout = self.layout
        layout.use_property_decorate = False

        row = layout.row()
        row.prop(self, "tabs", expand=True)

        if self.tabs == "LIBRARY":
            box = layout.box()
            box.label(text="Megascans Library")

            col = box.column(align=True)
            col.enabled = False
            col.label(text="Select: path/to/Megascans Library/Downloaded/")
            col.label(text="Make sure to have 'assetsData.json' in that folder.")

            col = box.column()
            col.prop(self, "megascans_library_path")
            col.prop(self, "megascans_size")

        elif self.tabs == "MODEL":
            col = layout.column()
            col.use_property_split = True
            col.prop(self.model, "format")
            col.separator()
            col.prop(self.model, "import_all_lods")
            col.active = not self.model.import_all_lods
            col.prop(self.model, "lods")

        elif self.tabs == "PREVIEW":
            col = layout.column()
            col.use_property_split = True
            col.prop(self, "preview_limit")
            col.prop(self, "preview_scale")
            col.prop(self, "popup_scale")
            col.prop(self, "show_asset_name")


classes = (
    MBRIDGE_AP_model,
    MBRIDGE_AP_preferences,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
