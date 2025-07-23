import glob
import os

import bpy
from bpy.props import StringProperty
from bpy.types import Operator

from ..utils.addon import preferences


class MBRIDGE_OT_brush_add(Operator):
    bl_label = "Import"
    bl_idname = "mbridge.brush_add"
    bl_options = {"REGISTER", "INTERNAL"}

    asset_id: StringProperty(options={"SKIP_SAVE", "HIDDEN"})

    @classmethod
    def description(cls, context, properties):
        return "Import the brush as a texture mask"

    def execute(self, context):
        self.prefs = preferences()
        self.props = context.scene.mbridge

        assets = self.props.brushes.get_assets(context)
        self.asset = next((a for a in assets if a.id == self.asset_id), None)
        if not self.asset:
            return {"FINISHED"}

        # Create texture name
        self.tex_name = f"{self.asset.name.lower().replace(' ', '_')}_{self.asset.id}"
        texture = bpy.data.textures.get(self.tex_name) or bpy.data.textures.new(self.tex_name, "IMAGE")

        # Load image directly
        if image := self.load_brush_image(self.asset.path):
            texture.image = image

        # Apply texture to brush if needed
        if self.props.brushes.use_tex_mask and context.tool_settings.image_paint.brush:
            context.tool_settings.image_paint.brush.mask_texture = texture

        context.area.tag_redraw()
        return {"FINISHED"}

    def load_brush_image(self, path: str) -> bpy.types.Image:
        """Find and load the brush image with appropriate resolution"""
        sizes = ["8K", "4K", "2K", "1K"]
        preferred_size = self.prefs.megascans_size

        # Prioritize the preferred size
        if preferred_size in sizes:
            sizes.remove(preferred_size)
            sizes.insert(0, preferred_size)

        # Search paths
        search_paths = [
            path,
            os.path.join(path, "Thumbs", "4k"),
            os.path.join(path, "Thumbs", "2k"),
            os.path.join(path, "Thumbs", "1k"),
        ]

        # Try to find and load image
        for size in sizes:
            for search_path in search_paths:
                # Try jpg first
                jpg_pattern = os.path.join(search_path, f"*{size}_Brush*.jpg")
                jpg_files = glob.glob(jpg_pattern)
                if jpg_files:
                    img_path = jpg_files[0]
                    img_name = os.path.basename(img_path)
                    return bpy.data.images.get(img_name) or bpy.data.images.load(img_path)

                # Then try exr
                exr_pattern = os.path.join(search_path, f"*{size}_Brush*.exr")
                exr_files = glob.glob(exr_pattern)
                if exr_files:
                    img_path = exr_files[0]
                    img_name = os.path.basename(img_path)
                    return bpy.data.images.get(img_name) or bpy.data.images.load(img_path)

        return None


classes = (MBRIDGE_OT_brush_add,)


register, unregister = bpy.utils.register_classes_factory(classes)
