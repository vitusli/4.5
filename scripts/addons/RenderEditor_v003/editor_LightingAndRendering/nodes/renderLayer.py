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
import os

import bpy

from . import utilityFunctions
from .. import editorPaths


class AOVLabelProperty(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="AOV Label")


class RenderingLightingRenderLayerNode(bpy.types.Node):
    """
    A node for setting render Layer Output
    """
    bl_idname = "RenderingLightingRenderLayerNode"
    bl_label = "Render"
    bl_icon = "MOD_DECIM"
    nodeType = "Render"

    layerName: bpy.props.StringProperty(
        name="Layer Name",
        description="Enter the name of the RenderLayer",
        default="",
        update=lambda self, context: self.executeViewportCook()
    )

    version: bpy.props.StringProperty(
        name="Version",
        description="The path version",
        default="v001",
    )

    AOVLabels: bpy.props.CollectionProperty(type=AOVLabelProperty)

    def init(self, context):
        """
        Initialize node sockets
        """
        self.width = 400
        self.inputs.new("NodeSocketCollection", "Scene_Input")
        checkedAovs = utilityFunctions.getEnabledAovs()
        for aov in checkedAovs:
            new_label = self.AOVLabels.add()
            new_label.name = aov
        
    def draw_buttons(self, context, layout):
        """
        Draw the node layout and update labels dynamically
        """
        layout.alignment = 'CENTER'
        layout.prop(self, "layerName", text="Layer Name")
        for aov in self.AOVLabels:
            layout.label(text=aov.name+".####.exr")

        layout.operator("node.cook_scene_from_node", text = "Cook Scene", icon="FILE_REFRESH")
    
    def getOutputLocation(self):
        scene = bpy.context.scene
        outputLocation = os.path.join(scene.outputParentLocation, self.layerName)
        outputLocation = outputLocation.replace("\\","/")
        return outputLocation

    def update_labels(self):
        """
        Update AOV labels when outputLocation changes
        """
        checkedAovs = utilityFunctions.getEnabledAovs()
        self.AOVLabels.clear()
        outputLocation = self.getOutputLocation()

        for aov in checkedAovs:
            newLabel = self.AOVLabels.add()
            newLabel.name = os.path.join(outputLocation, self.version, self.layerName+"_"+aov.split("_")[-1]).replace("\\","/")

    def setNodeFilePathVersion(self):
        """
        Used to determine the version of the filepath
        """
        outputClass = editorPaths.FilePathHelper(self.getOutputLocation()+"/v001/")
        
        if not outputClass.exists:
            outputFile = outputClass.filePath+self.layerName+"_####"
            utilityFunctions.setLatestOutputPath(outputFile)
            return
        
        latestOnDiskVersion = editorPaths.FilePathHelper(outputClass.getLatestVersion())

        outputFile = latestOnDiskVersion.versionUp()+self.layerName+"_####"
        nextVersion = editorPaths.FilePathHelper(outputFile)
        utilityFunctions.setLatestOutputPath(nextVersion.filePath)

        self.version = nextVersion.extractVersion()

    def update(self):
        """
        Triggers when node is updated
        """
        self.update_labels()

    def executeNodeCookFunctions(self):
        utilityFunctions.setViewedNode(self)
        self.setNodeFilePathVersion()
        self.update_labels()
        self.updateLayerName()

    def executeViewportCook(self):
        """
        Leaving the below code here just in case. The render node should always update itself
            regardless of whether it's the viewed node
            
        viewedNode = utilityFunctions.getViewedNode()
        if self != viewedNode:
            return
        """
        self.executeNodeCookFunctions()

    def updateLayerName(self):
        self.name = self.layerName
        self.label = self.layerName


class NODE_OT_AddRenderLayerNode(bpy.types.Operator):
    """
    Add a Render Layer to the Custom Node Tree
    """
    bl_idname = "node.add_renderlayer_node"
    bl_label = "Add Render Layer Node"
    nodeType = "RenderingLightingRenderLayerNode"
    
    def execute(self, context):
        space = context.space_data
        if space and space.node_tree:
            newNode = space.node_tree.nodes.new(type=self.nodeType)
            newNode.location = (200, 200)
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "No active node tree found!")
            return {'CANCELLED'}

    def invoke(self, context, event):
        space = context.space_data
        nodes = space.node_tree.nodes

        bpy.ops.node.select_all(action='DESELECT')

        node = nodes.new(self.nodeType)
        node.select = True
        node.location = utilityFunctions.get_current_loc(context, event, context.preferences.system.ui_scale)

        bpy.ops.node.translate_attach_remove_on_cancel("INVOKE_DEFAULT")

        return {"FINISHED"}