import typing
import re
import bpy.types as bt
import bpy
from . import config

T = typing.TypeVar('T')

SNAKE_CASE_PATTERN = re.compile(r'(?<!^)(?=[A-Z])')

def to_snake_case(s: str):
    return SNAKE_CASE_PATTERN.sub('_', s).lower()


AutoFill = typing.Union[T, None]

TypeSequence = typing.Union[T, list[T]]

PropertyGroupType = typing.Type[typing.Union[bt.PropertyGroup, T]]

JSONSerializable = typing.Union[dict[str, 'JSONSerializable'], list['JSONSerializable'], str, int, float, bool, None]

def swizzle_to_indices(key: str):
    xyz_keys = ['x', 'y', 'z', 'w']
    rgb_keys = ['r', 'g', 'b', 'a']
    if not isinstance(key, str):
        return []
    if all(x in xyz_keys for x in key):
        return [xyz_keys.index(x) for x in key]
    elif all(x in rgb_keys for x in key):
        return [rgb_keys.index(x) for x in key]
    return []

class BObject(typing.Generic[T], bt.Object):
    """A generic type annotation for the bpy.types.Object class with defined data type."""
    data: T

class BContext(typing.Generic[T], bt.Context):
    """A generic type annotation for the bpy.types.Context class with definied space_data type."""
    space_data: T

def remove_duplicates(l: list):

    new = []
    for i in l:
        if not i in new:
            new.append(i)
    return new

def get_wm():
    return bpy.context.window_manager

def debug(*items, sep: str = ' ', end: str = '\n'):
    if config.DEBUG:
        print(*items, sep=sep, end=end)

def get_addon_module():
    import sys
    return sys.modules[config.ADDON_PACKAGE]

def name_numbering(name: str) -> tuple[bool, int]:
    if len(name) < 5:
        return (False, 0)
    if not name[-3:].isnumeric():
        return (False, 0)
    if not name[-4] == '.':
        return (False, 0)
    return (True, int(name[-3:]))

def resolve_unique_naming(candidate: str, pool: list[str], count_up: bool = False):
    if candidate not in pool:
        return candidate
    has_numbering, index = name_numbering(candidate)
    stem = candidate[:-4] if has_numbering else candidate
    if has_numbering and stem not in pool:
        return stem
    if count_up:
        return resolve_unique_naming(f'{stem}.{index+1:03}', pool, count_up=True)
    return resolve_unique_naming(f'{stem}.001', pool, count_up=True)


class BL_INFO(typing.TypedDict):
    name: str
    description: str
    author: str
    version: str
    blender: tuple[int, int, int]
    location: str
    warning: str
    doc_url: str
    tracker_url: str
    support: typing.Literal['OFFICIAL', 'COMMUNITY']
    category:  typing.Literal[
        '3D View', 'Add Mesh', 'Add Curve', 'Animation', 'Compositing', 'Development',
        'Game Engine', 'Import-Export', 'Lighting', 'Material', 'Mesh', 'Node',
        'Object', 'Paint', 'Physics', 'Render', 'Rigging', 'Scene',
        'Sequencer', 'System', 'Text Editor', 'UV', 'User Interface'
    ]
    show_expanded: bool


def get_adddon_bl_info() -> BL_INFO:
    return get_addon_module().bl_info
