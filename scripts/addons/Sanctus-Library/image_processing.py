'''
This module contains a lot of functions to operate on image pixels as numpy arrays. This is used to procedurally add icons to the thumbnails of assets shown in the UI
when for example a user sets an asset instance as a favorite. Because this is run on the CPU, these functions are quite slow and therefore run in a separate thread.
This is why it might take a while for dynamic thumbnail updates to be visible because they are sceduled in regular intervals and take some time to process.
'''

from enum import Enum, auto
import numpy as np
from numpy import ndarray
from .auto_load.common import *

class InvalidImageError(Exception):
    pass

def clamp(value, minimum, maximum):
    if maximum < minimum:
        minimum, maximum = maximum, minimum
    return min(max(minimum, value), maximum)

BaseShape = tuple[int, int]
Coord = tuple[int, int]

Color4 = tuple[float, float, float, float]
Color3 = tuple[float, float, float]
Color = typing.Union[
    tuple[float],
    tuple[float, float],
    Color3,
    Color4,
]

Pixels = ndarray
PixelArray = ndarray
ImageArray = ndarray
Coords = ndarray

class Direction(Enum):

    HORIZONTAL = auto()
    VERTICAL = auto()

class SampleMode(Enum):

    CLOSEST = auto()
    BILINEAR = auto()

class Rounding(Enum):

    ROUND = 'round'
    FLOOR = 'floor'
    CEIL = 'ceil'

class Anchor(Enum):

    CENTER = auto()
    LEFT = auto()
    RIGHT = auto()
    TOP = auto()
    BOTTOM = auto()

    TOP_LEFT = auto()
    TOP_RIGHT = auto()
    BOTTOM_LEFT = auto()
    BOTTOM_RIGHT = auto()
    

class _bpy_prop_array:

    def foreach_get(self, sequence):
        ...
    def foreach_set(self, sequence):
        ...

def read_pixels(pixel_collection: _bpy_prop_array) -> Pixels:
    b: Pixels = np.zeros(len(pixel_collection), dtype='float32')
    pixel_collection.foreach_get(b)
    return b


def read_image(image: bt.Image) -> ImageArray:
    x, y = image.size
    p = read_pixels(image.pixels)
    return p.reshape([x, y, 4]).swapaxes(0, 1)

def set_image(image: bt.Image, image_array: ImageArray):
    set_pixels(image.pixels, image_array.swapaxes(0,1).flatten())

def set_pixels(pixel_collection: _bpy_prop_array, pixels: Pixels):
    pixel_collection.foreach_set(pixels)

def get_image_from_preview(preview: bt.ImagePreview):
    b = read_pixels(preview.image_pixels_float)
    image: ImageArray = b.reshape([preview.image_size[1], preview.image_size[0], 4]).swapaxes(0,1)
    return image

def set_preview_image(preview: bt.ImagePreview, image: ImageArray):
    preview.image_size = bs(image)
    set_pixels(preview.image_pixels_float, image.swapaxes(0,1).flatten())

# get base shape
def bs(image: ImageArray) -> BaseShape:
    '''Get the base shape of an image array'''
    return image.shape[:2]

# flip base shape
def flip_bs(bs: BaseShape) -> BaseShape:
    '''Flip the base shape, reversing the tuples elements'''
    return (bs[1], bs[0])

def channels(image: ImageArray):
    '''Get the amounts of channels an ImageArray has. Assumes valid ImageArray'''
    return image.shape[2]

def is_valid_image(image: ImageArray) -> bool:
    return len(image.shape) == 3 and image.shape[2] in [1, 2, 3, 4]

def unravel(image: ImageArray) -> PixelArray:
    if not is_valid_image(image):
        raise InvalidImageError()
    new_shape = [
        image.shape[0] * image.shape[1],
        image.shape[2]
    ]
    return image.reshape(new_shape)

def format(image: PixelArray, base_shape: BaseShape) -> ImageArray:
    new_shape = [
        base_shape[0],
        base_shape[1],
        image.shape[1],
    ]
    return image.reshape(new_shape)

def are_images_compatible(image_1: ImageArray, image_2: ImageArray, close_match: bool = True) -> bool:
    if close_match:
        return image_1.shape == image_2.shape
    else:
        return bs(image_1) == bs(image_2)


def overlay_image(background: ImageArray, foreground: ImageArray):

    if bs(background) != bs(foreground):
        raise InvalidImageError()

    b = unravel(background)
    alpha_b = b[:, [3]]
    f = unravel(foreground)
    alpha_f = f[:, [3]]

    alpha = alpha_f + alpha_b * (1.0 - alpha_f)
    combined = (f * alpha_f) + (b * alpha_b * (1.0 - alpha_f))
    combined = np.divide(combined, alpha, out=np.zeros_like(b), where=alpha != 0)
    combined[:,[3]] = alpha
    return format(combined, bs(background))

def scale_base_shape(template: ImageArray, scale_x: float = 1.0, scale_y: float = 1.0) -> BaseShape:

    tbs = bs(template)
    new_shape = (
        int(tbs[0] * scale_x),
        int(tbs[1] * scale_y)
    )
    return new_shape

def get_relative_size(template: ImageArray, target: ImageArray, ratio: float, axis: Direction = Direction.VERTICAL):

    tbs = bs(template)
    obs = bs(target)

    if axis == Direction.HORIZONTAL:
        new_x = round(tbs[0] * ratio)
        ratio_to_original = new_x / obs[0]
        return (new_x, round(obs[1] * ratio_to_original))
    else:
        new_y = round(tbs[1] * ratio)
        ratio_to_original = new_y / obs[1]
        return (new_y, round(obs[0] * ratio_to_original))

def anchor_image(background: ImageArray, foreground: ImageArray, anchor: Anchor = Anchor.BOTTOM_LEFT, padding_x: int = 0, padding_y: int = 0):
    bbs = bs(background)
    fbs = bs(foreground)

    if anchor == Anchor.CENTER:
        start_x = int(bbs[0]/2 - fbs[0]/2)
        start_y = int(bbs[1]/2 - fbs[1]/2)
    if anchor == Anchor.LEFT:
        start_x = 0
        start_y = int(bbs[1]/2 - fbs[1]/2)
    if anchor == Anchor.RIGHT:
        padding_x = - padding_x
        start_x = bbs[0] - fbs[0]
        start_y = int(bbs[1]/2 - fbs[1]/2)
    if anchor == Anchor.BOTTOM:
        start_x = int(bbs[0]/2 - fbs[0]/2)
        start_y = 0
    if anchor == Anchor.TOP:
        padding_y = - padding_y
        start_x = int(bbs[0]/2 - fbs[0]/2)
        start_y = bbs[1] - fbs[1]
    if anchor == Anchor.BOTTOM_LEFT:
        start_x, start_y = 0, 0
    elif anchor == Anchor.TOP_LEFT:
        padding_x = - padding_x
        start_x = bbs[0] - fbs[0]
        start_y = 0
    elif anchor == Anchor.BOTTOM_RIGHT:
        padding_y = - padding_y
        start_x = 0
        start_y = bbs[1] - fbs[1]
    elif anchor == Anchor.TOP_RIGHT:
        padding_x, padding_y = - padding_x, - padding_y
        start_x = bbs[0] - fbs[0]
        start_y = bbs[1] - fbs[1]

    start_x = max(0, start_x + padding_x)
    start_y = max(0, start_y + padding_y)

    c = get_coords(bbs)
    c[:,:] -= (start_x, start_y)
    return sample_image(foreground, c)

def bw_to_alpha(image: ImageArray):
    base_shape = bs(image)
    new_unravel = np.repeat(1.0, base_shape[0] * base_shape[1] * 4).reshape([base_shape[0] * base_shape[1], 4])
    new_unravel[:, 3] = unravel(image)[:, 0]
    return format(new_unravel, base_shape)


def tint_image(image: ImageArray, uniform_color: Color3):
    i = unravel(image)
    i[:] = i[:] * np.array([*uniform_color, 1.0], dtype='float32')
    return format(i, bs(image))


def empty_image(base_shape: BaseShape, channels: int = 4):
    image: ImageArray = np.zeros([int(base_shape[0]), int(base_shape[1]), channels], dtype='float32')
    return image

def square_image(image: ImageArray):

    shape = bs(image)
    larger_dimension = max(shape[0], shape[1])
    new_shape = (larger_dimension, larger_dimension)
    offset = ((new_shape[0] - shape[0])/2, (new_shape[1] - shape[1])/2)
    coords = get_coords(new_shape) - offset
    return sample_image(image, coords, clip=True)

def fill_image(base_shape: BaseShape, color: Color4):
    image: ImageArray = empty_image(base_shape)
    image[:,:] = (color[0], color[1], color[2], color[3])
    return image

def get_coords(base_shape: BaseShape, dtype='int16') -> Coords:
    y_dim, x_dim = base_shape
    row = np.resize(np.arange(x_dim, dtype=dtype), [y_dim, x_dim])
    column = np.resize(np.arange(y_dim, dtype=dtype), [x_dim, y_dim]).swapaxes(0, 1)
    coords = np.zeros([y_dim, x_dim, 2], dtype=dtype)
    coords[:, :, 1] = row
    coords[:, :, 0] = column
    return coords


def sample_image(image: ImageArray, coords: Coords, mode: Rounding = Rounding.ROUND, clip: bool = False) -> ImageArray:
    s = bs(image)
    round_func = getattr(np, mode.value)
    c = np.int16(round_func(coords))
    sampled_image = image[
        np.clip(c[:, :, 0], 0, s[0] - 1),
        np.clip(c[:, :, 1], 0, s[1] - 1)
    ]
    if clip:
        x_valid = c[:,:,[0]] >= 0
        x_valid *= c[:,:,[0]] < s[0]
        y_valid = c[:,:,[1]] >= 0
        y_valid *= c[:,:,[1]] < s[1]
        valid = (x_valid * y_valid)[:,:,[0,0,0,0]]
        sampled_image = np.where(valid, sampled_image, empty_image(bs(sampled_image)))
    return sampled_image

def resize_image(image: ImageArray, base_shape: BaseShape, bilinear: bool = False) -> ImageArray:
    original_size = bs(image)
    if original_size == base_shape:
        return image
    
    ratio = (original_size[0] / base_shape[0], original_size[1] / base_shape[1])
    coords = get_coords(base_shape, dtype='float16')
    coords[:, :, 0] *= ratio[0]
    coords[:, :, 1] *= ratio[1]

    if not bilinear:
        return sample_image(image, coords, mode=Rounding.ROUND)
    
    def nfloor(x): return np.int16(np.floor(x))
    def nceil(x, y): return np.clip(np.int16(np.ceil(x)), 0, y - 1)

    frac = np.mod(coords, 1.0)
    fxc = frac[:, :, [0]]
    fxf = 1.0 - fxc
    p1f = image[
        nfloor(coords[:, :, 0]),
        nfloor(coords[:, :, 1]),
    ]
    p1c = image[
        nceil(coords[:, :, 0], original_size[0]),
        nfloor(coords[:, :, 1])
    ]
    p1 = p1c * fxc + p1f * fxf

    p2f = image[
        nfloor(coords[:, :, 0]),
        nceil(coords[:, :, 1], original_size[1])
    ]
    p2c = image[
        nceil(coords[:, :, 0], original_size[0]),
        nceil(coords[:, :, 1], original_size[1])
    ]
    p2 = p2c * fxc + p2f * fxf
    fyc = frac[:, :, [1]]
    p = p2 * fyc + p1 * (1.0 - fyc)

    return p


def add_margin(image: ImageArray, margin: int):
    
    def len_sq(coord: Coord):
        return float(coord[0]**2 + coord[1]**2)
    
    def len_sq_arr(coords: Coords):
        return coords[:,:,[0]]**2 + coords[:,:,[1]]**2

    x,y = dims = bs(image)
    base_grid = get_coords(dims)
    result = image
    closest_offset = np.zeros([x,y,2])
    closest_offset[:,:] = (99999, 99999)
    for j in range(-margin, margin + 1):
        for i in range(-margin, margin + 1):
            offset = (j, i)
            uv = base_grid - offset
            if (j*j + i*i)**0.5 > margin:
                continue
            sample = sample_image(image, uv)
            higher_alpha = sample[:,:,[3]] > image[:,:,[3]]
            offset_is_closer = len_sq(offset) < len_sq_arr(closest_offset)
            override = offset_is_closer * higher_alpha
            result = np.where(override, sample, result)
            closest_offset = np.where(override, offset, closest_offset)
    return result

def gradient(
        base_shape: BaseShape,
        color_1: Color4,
        color_2: Color4,
        direction: Direction) -> ImageArray:
    coords = get_coords(base_shape, dtype='float16')

    if direction == Direction.HORIZONTAL:
        gradient = coords[:, :, [1]] / base_shape[1]
    else:
        gradient = coords[:, :, [0]] / base_shape[0]

    return np.float32(color_2 * gradient + color_1 * (1.0 - gradient))


def average_color(image: ImageArray) -> ndarray:
    return np.average(unravel(image), axis=0)

def divide(a: ImageArray, b: ImageArray) -> ImageArray:
    return np.divide(a, b, out=np.zeros_like(a), where=b!=0)

def divide_by_alpha(pixels: Pixels):
    pixels[:,:,[0,1,2]] = divide(pixels[:,:,[0,1,2]], pixels[:,:,[3]])
    return pixels

def linear_to_srgb(pixels: Pixels) -> Pixels:
    pixels = np.maximum(pixels, 0)
    is_below_threshold = pixels < 0.0031308
    return np.where(
        is_below_threshold,
        pixels * 12.92,
        1.055 * (pixels ** (1.0 / 2.4)) - 0.055
    )

def srgb_to_linear(pixels: Pixels) -> Pixels:
    pixels = np.maximum(pixels, 0)
    is_below_threshold = pixels < 0.04045
    return np.where(
        is_below_threshold,
        pixels / 12.92,
        ((pixels + 0.055) / 1.055) ** 2.4
    )

def debug_image(image: ImageArray, channel: int = 0):
    image = np.flip(image, axis=0)
    shape = bs(image)
    print('=' * (shape[0] * 3 + 2))
    for x in range(shape[0]):
        print('|', end='')
        for y in range(shape[1]):
            v = round(image[x,y, channel] * 10)
            print(f' {"+" if v > 0 else "-"}{abs(v):02}', end='')
        print('|')
        print()
    print('=' * (shape[0] * 3 + 2))
