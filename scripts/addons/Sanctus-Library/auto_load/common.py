import bpy
import bpy.types as bt
import bpy.ops as bo

import sys
import enum

import typing
from typing import Any, Union, Generic, Generator, Callable
from mathutils import Vector, Matrix, Euler, Quaternion

from pathlib import Path

_T = typing.TypeVar("_T")
Optional = Union[_T, None]
OrNone = Union[_T, None]
