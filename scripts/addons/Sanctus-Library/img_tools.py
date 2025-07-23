'''
This module implments image_processing on a higher level. This is mainly used to process previews to add dynamic icons to them.
Some additional functionality on handling images in Blender can be found here as well 
'''

import bpy
import bpy.types as bt
import numpy as np
from numpy import ndarray
from pathlib import Path

from . import image_processing as ip


BLENDER_PREVIEW_SIZE: tuple[int, int] = (128, 128)

def make_icon_favorite(base_icon: bt.ImagePreview, star_icon: bt.ImagePreview):

    star_image = ip.get_image_from_preview(star_icon)
    base_image = ip.get_image_from_preview(base_icon)

    if ip.bs(base_image) != ip.bs(star_image):
        base_image = ip.square_image(base_image)
        base_image = ip.resize_image(base_image, ip.bs(star_image), bilinear=False)
    
    new_image = ip.overlay_image(base_image, star_image)
    ip.set_preview_image(base_icon, new_image)


def overlay_images(base: bt.ImagePreview, overlay: bt.ImagePreview):

    base_image = ip.get_image_from_preview(base)
    overlay_image = ip.get_image_from_preview(overlay)

    if ip.bs(base_image) != ip.bs(overlay_image):
        base_image = ip.square_image(base_image)
        base_image = ip.resize_image(base_image, ip.bs(overlay_image), bilinear=False)
    
    new_image = ip.overlay_image(base_image, overlay_image)
    ip.set_preview_image(base, new_image)


def ensure_previews():
    bpy.ops.wm.previews_clear('EXEC_DEFAULT', id_type={'MATERIAL'})
    bpy.ops.wm.previews_ensure('EXEC_DEFAULT')


def capture_material_preview(mat: bt.Material) -> ndarray:
    ensure_previews()
    pixels: np.ndarray = np.zeros(len(mat.preview_ensure().image_pixels_float), dtype='float32')
    mat.preview_ensure().image_pixels_float.foreach_get(pixels)

    return pixels.reshape([*BLENDER_PREVIEW_SIZE, 4])


def save_pixels_as_image(pixels: ndarray, file: Path):
    temp_image = bpy.data.images.new('.temp_sanctus_preview_image', width=pixels.shape[1], height=pixels.shape[0], alpha=True)
    temp_image.pixels.foreach_set(pixels.flatten())
    temp_image.pixels.update()
    temp_image.update()
    temp_image.filepath_raw = str(file)
    temp_image.file_format = 'PNG'
    temp_image.save()
    bpy.data.images.remove(temp_image)


def convert_linear_to_srgb(image: bt.Image) -> None:
    buffer = ip.read_image(image)
    ip.set_image(image, ip.linear_to_srgb(buffer))
    image.pixels.update()

def convert_srgb_to_linear(image: bt.Image) -> None:
    buffer = ip.read_image(image)
    ip.set_image(image, ip.srgb_to_linear(buffer))
    image.pixels.update()

def un_premul_alpha(image: bt.Image):
    buffer = ip.read_image(image)
    buffer = ip.divide_by_alpha(buffer)
    ip.set_image(image, buffer)
    image.pixels.update()

def replace_image(old: bt.Image, new: bt.Image):
    old_name = old.name
    old.user_remap(new)
    bpy.data.images.remove(old)
    new.name = old_name


class PreviewEditor:
    
    _preview: bt.ImagePreview
    _image: ip.ImageArray = None
    _has_edits: bool = False

    @property
    def image(self):
        if self._image is None:
            self._image = ip.get_image_from_preview(self._preview)
        return self._image
    
    @image.setter
    def image(self, new: ip.ImageArray):
        self._has_edits = True
        self._image = new
    

    def __init__(self, preview: bt.ImagePreview):
        self._preview = preview
        self._image = None

    def __enter__(self):
        return self
    
    def __exit__(self, type, value, traceback):
        if(self._has_edits):
            ip.set_preview_image(self._preview, self.image)

    def overlay(self, foreground: ip.ImageArray):
        self.image = ip.overlay_image(self.image, foreground)

class LazyPreviewImage:

    _preview: bt.ImagePreview
    _image: ip.ImageArray = None

    @property
    def image(self):
        if self._image is None:
            self._image = ip.get_image_from_preview(self._preview)
        return self._image

    def __init__(self, preview: bt.ImagePreview):
        self._preview = preview
        self._image = None
