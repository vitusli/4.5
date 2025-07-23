import os

import bpy
from bpy.props import IntProperty, StringProperty
from bpy.types import Operator

from ...t3dn_bip import previews
from ..utils.addon import preferences

INDEX = 0


class MBRIDGE_OT_preview(Operator):
    bl_label = "Preview"
    bl_idname = "mbridge.preview"
    bl_options = {"REGISTER", "INTERNAL"}

    index: IntProperty(min=0)
    filepath: StringProperty(subtype="FILE_PATH")

    @classmethod
    def description(cls, context, properties):
        return "Change the preview image\n\nShift + Click - Open the image in the image viewer"

    def invoke(self, context, event):
        global INDEX

        if event.shift:
            bpy.ops.wm.path_open(filepath=self.filepath)
            return {"FINISHED"}

        INDEX = self.index
        return {"FINISHED"}


class MBRIDGE_OT_detail(Operator):
    bl_label = "Details"
    bl_idname = "mbridge.detail"
    bl_options = {"REGISTER", "INTERNAL"}

    asset_id: StringProperty(options={"SKIP_SAVE", "HIDDEN"})

    @classmethod
    def description(cls, context, properties):
        return "Preview the asset"

    def draw(self, context):
        global INDEX
        layout = self.layout

        # self.image = ""
        self.image = self.images[min(INDEX, len(self.images) - 1)]
        self.num_images = len(self.images)

        row = layout.row(align=True)
        row.label(text="Details", icon="INFO_LARGE" if bpy.app.version >= (4, 3, 0) else "INFO")

        self.draw_images(layout)
        self.draw_info(context, layout)

    def draw_images(self, layout):
        global INDEX

        row = layout.row(align=True)

        col_left = row.column(align=True)
        col_left.scale_y = 16 * self.prefs.popup_scale
        col_left.alignment = "LEFT"
        op = col_left.operator("mbridge.preview", icon="TRIA_LEFT", text="", emboss=False)
        op.index = (INDEX - 1) % self.num_images
        op.filepath = self.image

        col = row.column(align=True)

        if os.path.exists(self.image):
            if not image_previews.get(self.image):
                preview = image_previews.load_safe(self.image, self.image, "IMAGE")
                bpy.context.area.tag_redraw()
            else:
                preview = image_previews[self.image]

            col.template_icon(icon_value=preview.icon_id, scale=16 * self.prefs.popup_scale)
        else:
            col.template_icon(icon_value=self.asset.preview, scale=16 * self.prefs.popup_scale)

        self.draw_nav(col)

        col_right = row.column(align=True)
        col_right.scale_y = 16 * self.prefs.popup_scale
        col_right.alignment = "RIGHT"
        op = col_right.operator("mbridge.preview", icon="TRIA_RIGHT", text="", emboss=False)
        op.index = (INDEX + 1) % self.num_images
        op.filepath = self.image

    def draw_nav(self, layout):
        global INDEX

        row = layout.row(align=True)
        row.alignment = "CENTER"
        row.label(text=os.path.splitext(os.path.basename(self.image))[0].split("_")[-1])

        row = layout.row(align=True)
        row.alignment = "CENTER"

        for i in range(self.num_images):
            op = row.operator(
                "mbridge.preview",
                icon="RADIOBUT_ON" if i == INDEX else "RADIOBUT_OFF",
                text="",
                emboss=False,
                depress=i == INDEX,
            )
            op.index = i
            op.filepath = self.image

    def draw_info(self, context, layout):
        box = layout.box()
        split = box.split(factor=0.3)

        split.column(align=True)

        col = split.column(align=True)
        col.label(text=self.asset.name)

        row = col.row()
        row.enabled = False
        row.alignment = "LEFT"
        length = next((item["value"] for item in self.asset.meta if item.get("key") == "length"), None)
        width = next((item["value"] for item in self.asset.meta if item.get("key") == "width"), None)
        height = next((item["value"] for item in self.asset.meta if item.get("key") == "height"), None)
        if length and width and height:
            row.label(text=f"{length} x {width} x {height}")
        # row.label(text=self.asset.semanticTags.get("3d_mesh", ""))
        if tiling_directions := next(
            (item["value"] for item in self.asset.meta if item.get("key") == "tiling_directions"), None
        ):
            row.label(text=f"Tile {''.join(tiling_directions).upper()}")
        if scanArea := next((item["value"] for item in self.asset.meta if item.get("key") == "scanArea"), None):
            row.label(text=scanArea.replace(" ", ""))

        row = layout.row()
        row.prop(self.prefs, "megascans_size", text="")
        row.operator("mbridge.options", text="", icon="OPTIONS", emboss=False).asset_id = self.asset.id

        if context.area.type == "VIEW_3D":
            if context.mode == "OBJECT":
                if self.props.asset_type == "ASSETS":
                    row.operator("mbridge.asset_add", icon="IMPORT").asset_id = self.asset.id
                elif self.props.asset_type == "PLANTS":
                    row.operator("mbridge.plant_add", icon="IMPORT").asset_id = self.asset.id
                elif self.props.asset_type == "SURFACES":
                    row.operator("mbridge.surface_add", icon="IMPORT").asset_id = self.asset.id
            elif context.mode == "PAINT_TEXTURE":
                row.operator("mbridge.brush_add", icon="IMPORT").asset_id = self.asset.id
        elif context.area.type == "NODE_EDITOR":
            subrow = row.row(align=True)
            current_tree = getattr(context.space_data, "edit_tree", None)
            subrow.enabled = bool(current_tree and self.asset.id not in current_tree.name)

            if self.props.asset_type == "SURFACES":
                subrow.operator("mbridge.surface_group_add", icon="NODETREE").asset_id = self.asset.id
            elif self.props.asset_type == "DECALS":
                subrow.operator("mbridge.decal_group_add", icon="NODETREE").asset_id = self.asset.id
            elif self.props.asset_type == "ATLASES":
                subrow.operator("mbridge.atlas_group_add", icon="NODETREE").asset_id = self.asset.id
            elif self.props.asset_type == "IMPERFECTIONS":
                subrow.operator("mbridge.imperfection_group_add", icon="NODETREE").asset_id = self.asset.id
            elif self.props.asset_type == "DISPLACEMENTS":
                subrow.operator("mbridge.displacement_group_add", icon="NODETREE").asset_id = self.asset.id

    def execute(self, context):
        global INDEX
        INDEX = 0
        self.prefs = preferences()
        self.props = context.scene.mbridge

        assets = self.props.get_assets(context)
        self.asset = next((a for a in assets if a.id == self.asset_id), None)
        if self.asset:
            self.images = [self.asset.thumb]
            keywords = [
                "Popup",
                "1K_Albedo",
                "1K_AO",
                "1K_Displacement",
                "1K_Normal",
                "1K_Opacity",
                "1K_Roughness",
                "1K_Translucency",
                "1K_Brush",
            ]

            for root, dirs, files in os.walk(self.asset.path):
                for file in files:
                    file_path = os.path.join(root, file)
                    if (
                        file_path not in self.images
                        and (file.endswith(".png") or file.endswith(".jpg"))
                        and "_LOD" not in file
                    ):
                        if any(keyword in file for keyword in keywords):
                            self.images.append(file_path)

            return context.window_manager.invoke_popup(self, width=int(360 * self.prefs.popup_scale))

        return {"FINISHED"}


classes = (
    MBRIDGE_OT_preview,
    MBRIDGE_OT_detail,
)


image_previews = None


def register():
    global image_previews
    image_previews = previews.new(max_size=(512, 512))

    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    global image_previews
    bpy.utils.previews.remove(image_previews)
