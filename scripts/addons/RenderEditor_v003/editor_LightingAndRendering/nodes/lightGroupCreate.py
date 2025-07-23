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
import bpy

from . import utilityFunctions

class RenderingLightingLightGroupNode(bpy.types.Node):
    """
    A node for pruning scenegraph locations
    """
    bl_idname = "RenderingLightingLightGroupNode"
    bl_label = "Light Group Create"
    bl_icon = "MOD_DECIM"
    
    celStatement: bpy.props.StringProperty(
        name="Match Statement",
        description="Enter a Match statement",
        default="",
        update=lambda self, context: self.executeViewportCook()
    )

    lightGroupName: bpy.props.StringProperty(
        name="Light group Name",
        description="Enter the name of the light group",
        default="",
        update=lambda self, context: self.executeViewportCook()
    )

    def init(self, context):
        """
        Initialize node sockets
        """
        self.width = 200
        self.inputs.new("NodeSocketCollection", "SceneInput")
        self.outputs.new("NodeSocketCollection", "SceneOutput")

    def draw_buttons(self, context, layout):
        """
        Draw the node layout and place sockets
        """
        layout.alignment = 'CENTER'
        row = layout.row()
        row.scale_x = 2.0
        row.alignment = 'LEFT'
        row.prop(self, "celStatement", text="Match Statement", expand=True)

        layout.prop(self, "lightGroupName", text="LightGroup Name")
        # Cook node Button
        layout.operator("node.cook_scene_from_node", text = "Cook Scene", icon="FILE_REFRESH")

    def update(self):
        """
        This is where the node processing would happen
        """
        self.assignLightGroupsStart()

    def executeNodeCookFunctions(self):
        """
        The function the cook Scene Button calls from utilFunctions,
        
        This function can return a True if the node fails. The util function will then set it red 
        Returns:
        None/False: If the node succeeds it returns this value
        True: If the node fails return this value

        """
        utilityFunctions.setViewedNode(self)
        failed = self.assignLightGroupsStart()
        return failed

    def executeViewportCook(self):
        viewedNode = utilityFunctions.getViewedNode()
        if self != viewedNode:
            return

        self.executeNodeCookFunctions()

    def assignLightGroupsStart(self):
        # Make sure the collection socket is properly assigned before accessing it

        scene = utilityFunctions.getCollection(self)
        cel = self.celStatement.strip()
        matchedLights = utilityFunctions.searchSceneObjectsRecursive(cel, scene)
        if matchedLights == []:
            return
        
        if matchedLights == False:
            return True

        bpy.ops.scene.view_layer_add_lightgroup(name=self.lightGroupName.strip())
        self.assignLightGroup(matchedLights)

    def assignLightGroup(self, lights):
        for light in lights:
            light.lightgroup = self.lightGroupName.strip()


class NODE_OT_AddLightGroupNode(bpy.types.Operator):
    """
    Add a Light Group to the Custom Node Tree
    """
    bl_idname = "node.add_light_group_node"
    bl_label = "Add Light Group Node"
    nodeType = "RenderingLightingLightGroupNode"
    
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