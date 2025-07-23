"""
*
* The foo application.
*
* Copyright (C) 2025 Yarrawonga VIC woodvisualizations@gmail.com
*
* This program is free software: you can redistribute it and/or modify
* it under the terms of the GNU General Public License as published by
* the Free Software Foundation, either version 3 of the License, or
* (at your option) any later version.
*
* This program is distributed in the hope that it will be useful,
* but WITHOUT ANY WARRANTY; without even the implied warranty of
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
* GNU General Public License for more details.
*
* You should have received a copy of the GNU General Public License
* along with this program.  If not, see <https://www.gnu.org/licenses/gpl-3.0.html>.
*
"""

import sys
import os

import bpy
from bpy.app.handlers import persistent

# Get the directory of the current file (your add-on root)
addon_directory = os.path.dirname(__file__)

# Add it to sys.path so Python recognizes it
if addon_directory not in sys.path:
    sys.path.append(addon_directory)

from .editor_LightingAndRendering import editor_lightingAndRendering
from .editor_LightingAndRendering import bntPanel
from .editor_LightingAndRendering.nodes import utilityFunctions


bl_info = {
    "name": "Render Editor",
    "author": "Julian Wood",
    "version": (1, 1, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > My Add-on",
    "description": "A node-based Render Layer workflow",
    "warning": "",
    "category": "Render",
}

count = 0

# Get the custom render layer argument
def getRenderLayerArgument():
    args = sys.argv
    if "--renderLayer" in args:
        index = args.index("--renderLayer") + 1
        if index < len(args):
            return args[index]
    return None


@persistent
def cookRenderNode(dummy1, dummy2):
    # Fetch the specified render layer
    renderLayerName = getRenderLayerArgument()
    if renderLayerName:
        sceneCooked = utilityFunctions.cookRenderNodeFromName(renderLayerName)
        if not sceneCooked:
            sys.exit()


@persistent
def setFileVersionsOnSave(dummy1, dummy2):
    nodeTree = bpy.data.node_groups.get("Rendering")

    for node in nodeTree.nodes:
        if node.bl_idname == "RenderingLightingRenderLayerNode":
            node.setNodeFilePathVersion()


def register():
    editor_lightingAndRendering.register()
    bntPanel.register()
    bpy.app.handlers.load_post.append(cookRenderNode)

#register()