import bpy
import io
from pathlib import Path
from zlib import decompress
from array import array
from .formats import BIP_FORMATS, MAGIC_LENGTH
from . import settings
from OpenImageIO import ImageBuf, ImageBufAlgo, ROI
import OpenImageIO as oiio
import numpy as np


def can_load(filepath: str) -> bool:
    """Return whether an image can be loaded."""

    # Perform a magic check if configured.
    if settings.USE_MAGIC:
        with open(filepath, "rb") as file:
            magic = file.read(MAGIC_LENGTH)

        # We support BIP (currently only BIP2).
        for spec in BIP_FORMATS.values():
            if magic.startswith(spec.magic):
                return True

    # Perform a file extension check otherwise.
    ext = Path(filepath).suffix.lower()

    # We can't check the extention if the file doesn't have one.
    if not ext:
        return False

    # We support BIP (currently only BIP2).
    for spec in BIP_FORMATS.values():
        if ext in spec.exts:
            return True

    # Attempt to open using OpenImageIO.
    if ext.startswith("."):
        ext = ext[1:]
    if ext == "jpg":
        ext = "jpeg"
    elif ext == "exr":
        ext = "openexr"
    return oiio.is_imageio_format_name(ext)


def load_file(filepath: str, max_size: tuple) -> dict:
    """Load image preview data from file.

    Args:
        filepath: The input file path.
        max_size: Scale images above this size down.

    Returns:
        A dictionary with icon_size, icon_pixels, image_size, image_pixels.

    Raises:
        AssertionError: If pixel data type is not 32 bit.
        AssertionError: If pixel count does not match size.
    """
    with open(filepath, "rb") as bip:
        magic = bip.read(MAGIC_LENGTH)

        if magic.startswith(BIP_FORMATS["BIP2"].magic):
            bip.seek(len(BIP_FORMATS["BIP2"].magic), io.SEEK_SET)

            count = int.from_bytes(bip.read(1), "big")
            assert count > 0, "the file contains no images"

            icon_size = [int.from_bytes(bip.read(2), "big") for _ in range(2)]
            icon_length = int.from_bytes(bip.read(4), "big")
            bip.seek(8 * (count - 2), io.SEEK_CUR)
            image_size = [int.from_bytes(bip.read(2), "big") for _ in range(2)]
            image_length = int.from_bytes(bip.read(4), "big")

            icon_content = decompress(bip.read(icon_length))
            bip.seek(-image_length, io.SEEK_END)
            image_content = decompress(bip.read(image_length))

            if _should_resize(image_size, max_size):
                pxs = np.frombuffer(image_content, dtype=np.uint8).reshape([image_size[1], image_size[0], 4])
                buf = ImageBuf(pxs)
                if buf.has_error:
                    raise RuntimeError(buf.geterror())
                image: ImageBuf = ImageBufAlgo.resize(buf, roi=ROI(0, image_size[0], 0, image_size[1]), nthreads=1)
                s = image.spec()
                image_size = s.width, s.height
                image_content = image.get_pixels(format=oiio.UINT8).reshape([s.height * s.width, s.nchannels]).tobytes()

            icon_pixels = array("i", icon_content)
            assert icon_pixels.itemsize == 4, "unexpected bytes per pixel"
            length = icon_size[0] * icon_size[1]
            assert len(icon_pixels) == length, "unexpected amount of pixels"

            image_pixels = array("i", image_content)
            assert image_pixels.itemsize == 4, "unexpected bytes per pixel"
            length = image_size[0] * image_size[1]
            assert len(image_pixels) == length, "unexpected amount of pixels"

            return {
                "icon_size": icon_size,
                "icon_pixels": icon_pixels,
                "image_size": image_size,
                "image_pixels": image_pixels,
                "image_content": image_content,
            }

    # Use OpenImageIO
    buf = ImageBuf(filepath)
    if buf.has_error:
        raise RuntimeError(buf.geterror())
    spec = buf.spec()
    img_size = (spec.width, spec.height)

    # flip top to bottom
    buf: ImageBuf = ImageBufAlgo.flip(buf)

    # Ensure Alpha Channel
    if buf.spec().alpha_channel == -1:
        buf = ImageBufAlgo.channels(buf, ("R", "G", "B", 1.0), ("R", "G", "B", "A"))

    if _should_resize(img_size, max_size):
        buf = _resize_image(buf, max_size)
        spec = buf.spec()
        img_size = (spec.width, spec.height)

    image_pixels = array("i", buf.get_pixels(format=oiio.UINT8).tobytes())
    assert image_pixels.itemsize == 4, f"unexpected bytes per pixel: {image_pixels.itemsize} != 4: {filepath}"
    length = img_size[0] * img_size[1]
    assert (
        len(image_pixels) == length
    ), f"unexpected amount of pixels: {len(image_pixels)} != {img_size[0]} * {img_size[1]} OR {length}: {filepath}"

    if _should_resize(img_size, (32, 32)):
        icon_buf: ImageBuf = ImageBufAlgo.resize(buf, roi=ROI(0, 32, 0, 32, 0, 1, 0, 3))

        # icon_pixels_a = icon_buf.get_pixels(format=oiio.INT8).astype(np.int0)
        # icon_pixels_b = icon_buf.get_pixels(format=oiio.INT8).tobytes()
        # icon_pixels = icon_buf.get_pixels(format=oiio.INT8).tolist()
        icon_pixels = array("i", icon_buf.get_pixels(format=oiio.INT8).tobytes())
        spec = icon_buf.spec()
        icon_size = (spec.width, spec.height)
        assert icon_pixels.itemsize == 4, "unexpected bytes per pixel"
        length = icon_size[0] * icon_size[1]
        assert len(icon_pixels) == length, "unexpected amount of pixels"
    else:
        icon_size = img_size
        icon_pixels = image_pixels

    return {
        "image_size": img_size,
        "image_pixels": image_pixels,
        "icon_size": icon_size,
        "icon_pixels": icon_pixels,
    }


def _should_resize(size: tuple, max_size: tuple) -> bool:
    """Check whether width or height is greater than maximum."""
    if max_size[0] and size[0] > max_size[0]:
        return True

    return bool(max_size[1] and size[1] > max_size[1])


def _resize_image(image: ImageBuf, max_size: tuple) -> "ImageBuf":
    """Resize image to fit inside maximum."""
    s = image.spec()
    scale = min(
        max_size[0] / s.width if max_size[0] else 1,
        max_size[1] / s.height if max_size[1] else 1,
    )

    size = [int(n * scale) for n in (s.width, s.height)]
    return ImageBufAlgo.resize(image, roi=ROI(0, size[0], 0, size[1]))


def tag_redraw():
    """Redraw every region in Blender."""
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            for region in area.regions:
                region.tag_redraw()
