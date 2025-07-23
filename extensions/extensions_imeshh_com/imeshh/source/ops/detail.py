import os
import threading
from datetime import datetime, timedelta

import bpy
from bpy.props import IntProperty, StringProperty
from bpy.types import Operator
from t3dn_bip import previews

from ..utils.addon import icon_value, preferences
from ..utils.auth import PATH_IMAGES, get_message
from ..utils.product import download_image, get_license_type, get_products, get_version

# Global state
CURRENT_PRODUCT = None
INDEX = 0

class IMESHH_OT_message_close(Operator):
    """Close the message"""
    bl_label = "Close Message"
    bl_idname = "imeshh.message_close"
    bl_options = {"REGISTER", "INTERNAL"}

    def execute(self, context):
        data = get_message()
        if not data:
            return {"CANCELLED"}

        cooldown = data.get("cool_down", {})
        delta = timedelta(
            weeks=int(cooldown.get("weeks", 0)),
            days=int(cooldown.get("days", 0)),
            hours=int(cooldown.get("hours", 0)),
            minutes=int(cooldown.get("minutes", 0)),
            seconds=int(cooldown.get("seconds", 0)),
        )

        preferences().message_cooldown = int((datetime.now() + delta).timestamp())
        return {"FINISHED"}
        
class IMESHH_OT_dummy_refresh_tip(Operator):
    """Blender’s refresh may not always work automatically.\nWiggling your mouse over buttons can force a UI update.\nOpen to Developer ideas here..."""
    bl_idname = "imeshh.dummy_refresh_tip"
    bl_label = "Mouse Wiggle Tip"

    def execute(self, context):
        return {"FINISHED"}


class IMESHH_OT_preview(Operator):
    bl_label = "Preview"
    bl_idname = "imeshh.preview"
    bl_options = {"REGISTER", "INTERNAL"}

    index: IntProperty(min=0, max=6)
    filepath: StringProperty(subtype="FILE_PATH")

    @classmethod
    def description(cls, context, properties):
        return "Change the preview image\n\nShift + Click - Open the image in the image viewer"

    def invoke(self, context, event):
        global INDEX
        INDEX = self.index

        if event.shift:
            bpy.ops.wm.path_open(filepath=self.filepath)
            return {"FINISHED"}

        # Download image on preview change
        if CURRENT_PRODUCT and 0 <= INDEX < len(CURRENT_PRODUCT.get("images", [])):
            def download_and_redraw(image):
                download_image(image)
                bpy.context.scene.imeshh.redraw_tick += 1

            threading.Thread(
                target=download_and_redraw,
                args=(CURRENT_PRODUCT["images"][INDEX],),
                daemon=True
            ).start()

        return {"FINISHED"}


class IMESHH_OT_detail(Operator):
    bl_label = "Details"
    bl_idname = "imeshh.detail"
    bl_options = {"REGISTER", "INTERNAL"}

    product_id: IntProperty(options={"SKIP_SAVE", "HIDDEN"})

    @classmethod
    def description(cls, context, properties):
        return "Preview the asset"

    def draw(self, context):
        global INDEX
        layout = self.layout

        image = self.product.get("images", [])[min(INDEX, len(self.product.get("images", [])) - 1)]
        image_name = f'{image.get("name", "")}_{image.get("date_modified", "").replace(":", "-")}'
        self.path = os.path.join(PATH_IMAGES, f"{image_name}.png")
        self.num_images = len(self.product.get("images"))

        row = layout.row(align=True)
        row.label(text="Asset Details", icon="INFO_LARGE" if bpy.app.version >= (4, 3, 0) else "INFO")
        row.operator("wm.path_open", icon="IMAGE_BACKGROUND", text="", emboss=False).filepath = self.path
        row.operator("imeshh.dummy_refresh_tip", text="", icon="RECOVER_LAST")
        self.draw_images(layout)
        self.draw_info(layout)

    def draw_images(self, layout):
        global INDEX

        row = layout.row(align=True)

        col_left = row.column(align=True)
        col_left.scale_y = 20 * self.prefs.popup_scale
        col_left.alignment = "LEFT"
        op = col_left.operator("imeshh.preview", icon="TRIA_LEFT", text="", emboss=False)
        op.index = (INDEX - 1) % self.num_images
        op.filepath = self.path

        col = row.column(align=True)
        col.scale_y = 1.2

        if os.path.exists(self.path):
            if not image_previews.get(self.path):
                preview = image_previews.load_safe(self.path, self.path, "IMAGE")
                bpy.context.area.tag_redraw()
            else:
                preview = image_previews[self.path]

            col.template_icon(icon_value=preview.icon_id, scale=18 * self.prefs.popup_scale)
        else:
            col.template_icon(
                icon_value=icon_value("TEMP") if bpy.app.version >= (4, 2, 0) else icon_value("FILE_REFRESH"),
                scale=18 * self.prefs.popup_scale,
            )

        self.draw_nav(col)

        col_right = row.column(align=True)
        col_right.scale_y = 20 * self.prefs.popup_scale
        col_right.alignment = "RIGHT"
        op = col_right.operator("imeshh.preview", icon="TRIA_RIGHT", text="", emboss=False)
        op.index = (INDEX + 1) % self.num_images
        op.filepath = self.path

    def draw_nav(self, layout):
        global INDEX

        row = layout.row(align=True)
        row.alignment = "CENTER"

        for i in range(self.num_images):
            op = row.operator(
                "imeshh.preview",
                icon="RADIOBUT_ON" if i == INDEX else "RADIOBUT_OFF",
                text="",
                emboss=False,
                depress=i == INDEX,
            )
            op.index = i
            op.filepath = self.path

    def draw_info(self, layout):
        box = layout.box()
        box.scale_y = 0.8
        split = box.split(factor=0.3, align=True)

        col = split.column(align=True)
        col.alignment = "RIGHT"
        col.enabled = False
        col.label(text="Name")
        col.label(text="ID")
        col.separator()
        col.label(text="Blender")
        col.label(text="Polygon Count")
        col.label(text="Dimensions")
        col.label(text="Subdividable")
        col.label(text="License Type")
        col.label(text="Category")

        col = split.column(align=True)
        col.label(text=f'{self.product.get("name")}')
        col.label(text=f'{self.product.get("id")}')
        col.separator()
        col.label(text=f'{get_version(self.product.get("blender_version"))}')
        col.label(text=f'{self.product.get("polygon_count") or "N/A"}')
        col.label(text=f'{self.product.get("dimensions") or "N/A"}')
        col.label(text=f'{self.product.get("subdividable") or "N/A"}')
        col.label(text=f'{get_license_type(self.product.get("license-type"))}')
        col.label(
            text=f'{self.product.get("asset_type").title()} / {self.product.get("categories").get("name")} / {self.product.get("sub-categories")[0].get("name")}'
        )

        layout.operator("wm.url_open", icon="URL", text="View Online").url = self.product.get("permalink")

    def execute(self, context):
        global INDEX
        INDEX = 0
        self.prefs = preferences()
        props = context.scene.imeshh

        products = get_products(props)
        global CURRENT_PRODUCT
        self.product = next((p for p in products if p.get("id") == self.product_id), None)
        CURRENT_PRODUCT = self.product

        if self.product:
            def download_and_redraw(image):
                download_image(image)
                bpy.context.scene.imeshh.redraw_tick += 1  # Trigger UI update

            # Only download the first image initially
            if self.product.get("images"):
                threading.Thread(target=download_and_redraw, args=(self.product["images"][0],), daemon=True).start()

            return context.window_manager.invoke_popup(self, width=int(450 * self.prefs.popup_scale))

        return {"FINISHED"}


# Registration
classes = (
    IMESHH_OT_message_close,
    IMESHH_OT_preview,
    IMESHH_OT_detail,
    IMESHH_OT_dummy_refresh_tip,
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
