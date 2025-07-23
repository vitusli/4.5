#!/usr/bin/python3
# copyright (c) 2018- polygoniq xyz s.r.o.

# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# Utility module for renderset contexts utilities to avoid circular imports

import bpy
import typing
import logging

logger = logging.getLogger(f"polygoniq.{__name__}")

if typing.TYPE_CHECKING:
    # TYPE_CHECKING is always False at runtime, so this block will never be executed
    # This import is used only for type hinting
    from . import renderset_context


# Don't allow more than 1000 render contexts in a .blend
# This is an arbitrary limit to give us some assurances for unique names.
MAX_RENDER_CONTEXTS = 1000
SKIP_RENDER_CONTEXT_SYNC = False
SKIP_RENDER_CONTEXT_APPLY = False


def is_valid_renderset_context_index(context: bpy.types.Context, index: int) -> bool:
    if index < 0:
        return False
    if index >= len(context.scene.renderset_contexts):
        return False
    return True


def get_active_renderset_context(
    context: bpy.types.Context,
) -> typing.Optional["renderset_context.RendersetContext"]:
    index = context.scene.renderset_context_index
    if not is_valid_renderset_context_index(context, index):
        return None
    return context.scene.renderset_contexts[index]


def get_active_renderset_context_index(context: bpy.types.Context) -> typing.Optional[int]:
    index = context.scene.renderset_context_index
    if not is_valid_renderset_context_index(context, index):
        return None
    return index


def get_all_renderset_contexts(
    context: bpy.types.Context,
) -> typing.Iterable["renderset_context.RendersetContext"]:
    return context.scene.renderset_contexts


def get_included_renderset_contexts_count(context: bpy.types.Context) -> int:
    return sum(rs_ctx.include_in_render_all for rs_ctx in context.scene.renderset_contexts)


def renderset_context_list_ensure_valid_index(context: bpy.types.Context) -> None:
    min_index = 0
    max_index = len(context.scene.renderset_contexts) - 1

    # This has caused errors when accessing to the context.scene after install
    if max_index == -1:
        return

    index = context.scene.renderset_context_index
    if index < min_index:
        context.scene.renderset_context_index = min_index
    elif index > max_index:
        context.scene.renderset_context_index = max_index
