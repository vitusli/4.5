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

import bpy
import typing
import logging

logger = logging.getLogger(f"polygoniq.{__name__}")

if typing.TYPE_CHECKING:
    # TYPE_CHECKING is always False at runtime, so this block will never be executed
    # This import is used only for type hinting
    from . import preferences


OCTANE_KERNELS_WITH_SAMPLES_NAMES = {
    "Direct lighting kernel",
    "Path tracing kernel",
    "PMC kernel",
    "Info channels kernel",
    "Photon tracing kernel",
}


class RenderAction:
    CURRENT = "current"
    ALL = "all"


def set_all_opened_viewports_to_solid_shading() -> None:
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type != 'VIEW_3D':
                continue
            for space in area.spaces:
                if space.type != 'VIEW_3D':
                    continue
                space.shading.type = 'SOLID'


def free_memory_for_persistent_data(context: bpy.types.Context) -> None:
    if context.scene.render.use_persistent_data:
        # toggle to False and then back to True to free memory
        context.scene.render.use_persistent_data = False
        context.scene.render.use_persistent_data = True


def get_render_samples(context: bpy.types.Context) -> int:
    """Getter for render sample rate for various render engines.

    Since each engine has a slightly different way to access render samples. In case of Octane, only
    some kernel nodes allow user to change render samples.
    """

    if (
        context.scene.render.engine == 'BLENDER_EEVEE'
        or context.scene.render.engine == 'BLENDER_EEVEE_NEXT'
    ):
        return context.scene.eevee.taa_render_samples
    elif context.scene.render.engine == 'CYCLES':
        return context.scene.cycles.samples
    elif context.scene.render.engine == 'octane':
        kernel_node = next(
            (
                node.name
                for node in bpy.data.node_groups["Octane Kernel"].nodes
                if node.name in OCTANE_KERNELS_WITH_SAMPLES_NAMES
            ),
            None,
        )
        if kernel_node is None:
            raise ValueError("No valid Octane kernel node found.")
        return bpy.data.node_groups["Octane Kernel"].nodes[kernel_node].inputs[1].default_value
    else:
        raise ValueError(f"Failed to get samples for render engine: {context.scene.render.engine}")


def set_render_samples(context: bpy.types.Context, samples: int) -> None:
    """Setter for render sample rate for various render engines.

    Since each engine has a slightly different way to access render samples. In case of Octane, only
    some kernel nodes allow user to change render samples.
    """

    if (
        context.scene.render.engine == 'BLENDER_EEVEE'
        or context.scene.render.engine == 'BLENDER_EEVEE_NEXT'
    ):
        context.scene.eevee.taa_render_samples = samples
    elif context.scene.render.engine == 'CYCLES':
        context.scene.cycles.samples = samples
    elif context.scene.render.engine == 'octane':
        kernel_node = next(
            (
                node.name
                for node in bpy.data.node_groups["Octane Kernel"].nodes
                if node.name in OCTANE_KERNELS_WITH_SAMPLES_NAMES
            ),
            None,
        )
        if kernel_node is None:
            raise ValueError("No valid Octane kernel node found.")

        bpy.data.node_groups["Octane Kernel"].nodes[kernel_node].inputs[1].default_value = samples
    else:
        raise ValueError(f"Failed to set samples for render engine: {context.scene.render.engine}")


def get_preferences(context: bpy.types.Context) -> "preferences.Preferences":
    return context.preferences.addons[__package__].preferences
