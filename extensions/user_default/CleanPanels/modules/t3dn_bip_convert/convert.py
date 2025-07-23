import io
import math
from pathlib import Path
from typing import Union
from zlib import compress, decompress

import numpy as np
import OpenImageIO as oiio
from OpenImageIO import ROI, ImageBuf, ImageBufAlgo

_BIP2_MAGIC = b"BIP2"


def convert_file(src: Union[str, Path], dst: Union[str, Path] = None):
    """Convert between BIP and various image formats."""
    src = Path(src).resolve()
    src_bip = src.suffix.lower() == ".bip"

    if dst is not None:
        dst = Path(dst).resolve()
        dst_bip = dst.suffix.lower() == ".bip"
    else:
        dst = src.with_suffix(".png" if src_bip else ".bip")
        dst_bip = not src_bip

    if not src_bip and dst_bip:
        _image_to_bip(src, dst)
    elif src_bip and not dst_bip:
        _bip_to_image(src, dst)
    else:
        raise ValueError("exactly one file must be in BIP format")


def _image_to_bip(src: Union[str, Path], dst: Union[str, Path]):
    """Convert various image formats to BIP."""
    # Open the input image file
    buf = ImageBuf(str(src))
    if buf.has_error:
        raise RuntimeError(buf.geterror())
    spec = buf.spec()
    width, height = spec.width, spec.height

    # flip top to bottom
    ImageBufAlgo.flip(buf, buf)

    # Ensure Alpha Channel
    if buf.spec().alpha_channel == -1:
        buf = ImageBufAlgo.channels(buf, ("R", "G", "B", 1.0), ("R", "G", "B", "A"))

    # Convert to RGBa
    buf = ImageBufAlgo.channels(buf, ("R", "G", "B", "A"))

    # Resize if necessary
    if width == 32 and height == 32:
        buffs = [buf]
    else:
        icon_buf: ImageBuf = ImageBufAlgo.resize(buf, roi=ROI(0, 32, 0, 32, 0, 1, 0, 3))
        if icon_buf.has_error:
            raise RuntimeError(icon_buf.geterror())
        buffs: list[ImageBuf] = [icon_buf, buf]
    contents = []
    for buf in buffs:
        s = buf.spec()
        contents.append(
            compress(buf.get_pixels(format=oiio.UINT8).reshape([s.height * s.width, s.nchannels]).tobytes())
        )

    # Compress images and write to output
    with open(dst, "wb") as output:
        output.write(_BIP2_MAGIC)
        output.write(len(buffs).to_bytes(1, "big"))  # num of images

        for buf, content in zip(buffs, contents):
            for number in (buf.spec().width, buf.spec().height):
                output.write(number.to_bytes(2, "big"))  # icon_size
            output.write(len(content).to_bytes(4, "big"))  # icon_length

        for content in contents:
            output.write(content)


def _bip_to_image(src: Union[str, Path], dst: Union[str, Path]):
    """Convert BIP to various image formats."""
    with open(src, "rb") as bip:
        if bip.read(4) != _BIP2_MAGIC:
            raise ValueError("input is not a supported file format")

        count = int.from_bytes(bip.read(1), "big")
        assert count > 0, "the file contains no images"
        bip.seek(8 * (count - 1), io.SEEK_CUR)

        size = [int.from_bytes(bip.read(2), "big") for _ in range(2)]
        length = int.from_bytes(bip.read(4), "big")

        bip.seek(-length, io.SEEK_END)
        content = decompress(bip.read(length))

        icon_pixels = np.frombuffer(content, dtype=np.uint8)
        roi = ROI(0, size[0], 0, size[1], 0, 1, 0, 4)
        spec = oiio.ImageSpec(roi, oiio.UINT8)
        image = ImageBuf(spec)
        image.set_pixels(roi, icon_pixels)
        if image.has_error:
            d = int(math.sqrt(len(icon_pixels) // 4))
            print(f"Wrong Dimensions: {d}, {d}, 4")
            raise RuntimeError(image.geterror())
        image = ImageBufAlgo.channels(image, ("R", "G", "B", "A"))

        image: ImageBuf = ImageBufAlgo.flip(image)

        if not image.has_error:
            image.write(str(dst))
        if image.has_error:
            raise RuntimeError(image.geterror())
