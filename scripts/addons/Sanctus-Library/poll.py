import bpy

from collections.abc import Iterable


def _check_object_type(context, types):
    obj = context.object
    if isinstance(types, str):
        types = {types, }

    if obj is None:
        return False
    else:
        return obj.type in types


def is_object_type(types):
    return lambda c: _check_object_type(c, types=types)
