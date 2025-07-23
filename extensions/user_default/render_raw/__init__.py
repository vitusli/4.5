'''
Copyright (C) 2024 Orange Turbine
https://orangeturbine.com
orangeturbine@cgcookie.com

This file is part of the Render Raw add-on, created by Jonathan Lampel for Orange Turbine.

All code distributed with this add-on is open source as described below.

Render Raw is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 3
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, see <https://www.gnu.org/licenses/>.
'''

bl_info = {
    "name": "Render Raw",
    "author": "Jonathan Lampel",
    "version": (1, 2, 10), # Be sure to set minimum version in version.py if nodes have changed!
    "blender": (4, 1, 0),
    "location": "Properties > Render > Color Management",
    "description": "Tools for easy color correction",
    "wiki_url": "",
    "category": "Render",
}

import bpy, sys
from .preferences import get_prefs

from . import preferences
from .properties import node_props, scene_props, preset_props
from .handlers import handle_animation
from .handlers import handle_render
from .interface import menu_groups, menu_presets, menu_clipping, panels_dummy, panels_original, panels_props, sidebar, list_layers
from .operators import op_nodes, op_presets, op_report, op_scene_settings, op_layers, op_tabs

files = [
    preferences,
    scene_props, preset_props, node_props,
    handle_animation, handle_render,
    menu_presets, menu_groups, menu_clipping, list_layers,
    panels_dummy, panels_props, panels_original,
    op_report, op_presets, op_nodes, op_scene_settings, op_layers, op_tabs
]

def cleanse_modules():
    # Based on https://devtalk.blender.org/t/plugin-hot-reload-by-cleaning-sys-modules/20040
    for module_name in sorted(sys.modules.keys()):
        if module_name.startswith(__name__):
            del sys.modules[module_name]

def register():
    for f in files:
        f.register()

    prefs = get_prefs(bpy.context)
    sidebar.update_sidebar_category(prefs, bpy.context)

def unregister():
    for f in files:
        f.unregister()
    cleanse_modules()

if __name__ == "__main__":
    register()