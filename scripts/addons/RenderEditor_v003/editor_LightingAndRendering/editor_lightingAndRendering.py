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

import bpy

from . import addNodesToMenu
from .nodes import cyclesAovSelection, cyclesGlobalSettings, cyclesRenderSettings, cyclesObjectSettings, prune, renderLayer, sceneIn, lightGroupCreate, denoise, backdrop, eeveeAovSelection, eeveeObjectSettings, eeveeGlobalSettings, utilityFunctions


class RenderingLightingNodeTree(bpy.types.NodeTree):
    """A custom node tree type for the Rendering and Lighting Editor"""
    bl_idname = "RenderingLightingNodeTree"
    bl_label = "Rendering"
    bl_icon = "NODETREE"

    viewedNode = None

    def setViewedNode(self, node):
        self.viewedNode = node
        
    def getViewedNode(self):
        return self.viewedNode

    def setOutputPath(self, outputPath):
        """
        A Function added for pipeline devs to help them integrate this addon into their pipelines
        """
        self.viewedNode.outputLocation = outputPath
        


nodeClasses = [
    utilityFunctions.NODE_UTIL_CookSceneFromNode,
    
    prune.RenderingLightingPruneNode,
    prune.NODE_OT_AddPruneNode,
    
    renderLayer.AOVLabelProperty,
    renderLayer.RenderingLightingRenderLayerNode,
    renderLayer.NODE_OT_AddRenderLayerNode,
    
    sceneIn.RenderingLightingSceneInput,
    sceneIn.NODE_OT_AddSceneInput,
    
    cyclesGlobalSettings.RenderingLightingGlobalSettings,
    cyclesGlobalSettings.NODE_OT_AddGlobalSettings,
    
    cyclesObjectSettings.CyclesLightingObjectsSettings,
    cyclesObjectSettings.NODE_OT_AddObjectSettings,

    cyclesRenderSettings.CyclesLightingRenderSettings,
    cyclesRenderSettings.NODE_OT_AddRenderSettings,
    
    lightGroupCreate.RenderingLightingLightGroupNode,
    lightGroupCreate.NODE_OT_AddLightGroupNode,
    
    cyclesAovSelection.RenderingLightingCyclesAovSelection,
    cyclesAovSelection.NODE_OT_AddAovSelection,

    denoise.RenderingLightingDenoise,
    denoise.NODE_OT_AddDenoise,

    backdrop.NODE_OT_AddFrameNode,
    
    eeveeAovSelection.RenderingLightingEeveeAovSelection,
    eeveeAovSelection.NODE_OT_AddEeveeAovSelection,

    eeveeObjectSettings.EeveeLightingObjectsSettings,
    eeveeObjectSettings.NODE_OT_AddEeveeObjectSettings,

    eeveeGlobalSettings.RenderingLightingEeveeGlobalSettings,
    eeveeGlobalSettings.NODE_OT_AddEeveeGlobalSettings,

    utilityFunctions.NODE_UTIL_ResolveCelStatement,
]

nodeTree = RenderingLightingNodeTree


def addNodesMenu(self, context):
    self.layout.menu("RLE_MT_add_render_settings_nodes_menu", icon="NODETREE")
    self.layout.menu("RLE_MT_add_object_settings_nodes_menu", icon="NODETREE")
    self.layout.menu("RLE_MT_add_aov_settings_nodes_menu", icon="NODETREE")
    self.layout.menu("RLE_MT_add_scene_nodes_menu", icon="NODETREE")
    self.layout.menu("RLE_MT_add_ui_nodes_menu", icon="NODETREE")


def register():
    registeredTree = bpy.utils.register_class(nodeTree)

    for cls in nodeClasses:
        bpy.utils.register_class(cls)

    bpy.utils.register_class(addNodesToMenu.RLE_MT_AddRenderSettingsNodesMenu)
    bpy.utils.register_class(addNodesToMenu.RLE_MT_AddObjectSettingsNodesMenu)
    bpy.utils.register_class(addNodesToMenu.RLE_MT_AddAOVNodesMenu)
    bpy.utils.register_class(addNodesToMenu.RLE_MT_AddSceneNodesMenu)
    bpy.utils.register_class(addNodesToMenu.RLE_MT_AddUiNodes)
    bpy.types.NODE_MT_add.append(addNodesMenu)
    
    #bpy.types.NODE_MT_add.append(addNodesToMenu.addRenderLayerNode)
    #bpy.types.NODE_MT_add.append(addNodesToMenu.addSceneInputNode)
    #bpy.types.NODE_MT_add.append(addNodesToMenu.addBlenderGlobalSettingsNode)
    #bpy.types.NODE_MT_add.append(addNodesToMenu.addBlenderObjectSettingsNode)
    #bpy.types.NODE_MT_add.append(addNodesToMenu.addBlenderRenderSettingsNode)
    #bpy.types.NODE_MT_add.append(addNodesToMenu.addLightGroupNode)
    #bpy.types.NODE_MT_add.append(addNodesToMenu.addAOVSelectionNode)
    #bpy.types.NODE_MT_add.append(addNodesToMenu.addDenoiseNode)

    return nodeTree


def unregister():
    bpy.utils.unregister_class(nodeTree)

    for cls in nodeClasses:
        bpy.utils.unregister_class(cls)

    #bpy.types.NODE_MT_add.remove(addNodesToMenu.addPruneNode)
    #bpy.types.NODE_MT_add.remove(addNodesToMenu.addRenderLayerNode)
    #bpy.types.NODE_MT_add.remove(addNodesToMenu.addSceneInputNode)
    #bpy.types.NODE_MT_add.remove(addNodesToMenu.addBlenderGlobalSettingsNode)
    #bpy.types.NODE_MT_add.remove(addNodesToMenu.addBlenderObjectSettingsNode)
    #bpy.types.NODE_MT_add.remove(addNodesToMenu.addBlenderRenderSettingsNode)
    #bpy.types.NODE_MT_add.remove(addNodesToMenu.addLightGroupNode)
    #bpy.types.NODE_MT_add.remove(addNodesToMenu.addAOVSelectionNode)
    #bpy.types.NODE_MT_add.remove(addNodesToMenu.addDenoiseNode)

