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

class RenderingLightingPruneNode(bpy.types.Node):
    """
    A node for pruning scenegraph locations
    """
    bl_idname = "RenderingLightingPruneNode"
    bl_label = "Visibility"
    bl_icon = "MOD_DECIM"
    
    celStatement: bpy.props.StringProperty(
        name="Cel Statement",
        description="Enter a CEL statement",
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
        """Draw the node layout and place sockets"""
        row = layout.row()
        row.alignment = 'CENTER'
        row.prop(self, "celStatement", text="Match Statement")

        # Cook node Button
        layout.operator("node.cook_scene_from_node", text = "Cook Scene", icon="FILE_REFRESH")

    def update(self):
        """
        This is where the node processing would happen
        """
        self.pruneItems()

    def executeNodeCookFunctions(self):
        """
        The function the cook Scene Button calls from utilFunctions
        """
        utilityFunctions.setViewedNode(self)
        self.pruneItems()

    def executeViewportCook(self):
        viewedNode = utilityFunctions.getViewedNode()
        if self != viewedNode:
            return

        self.executeNodeCookFunctions()

    def pruneItems(self):
        # Make sure the collection socket is properly assigned before accessing it

        scene = utilityFunctions.getCollection(self)
        cel = self.celStatement.strip()
        matchedObjects = utilityFunctions.searchSceneObjectsRecursive(cel, scene)
        self.pruneObjects(matchedObjects)

    def pruneObjects(self, meshes):
        for mesh in meshes:
            mesh.hide_viewport = True
            mesh.hide_render = True

    def draw(self, context):
        """
        Custom socket positioning
        """
        layout = self.layout

        # Draw input socket at the top
        if self.inputs:
            row = layout.row()
            row.alignment = 'CENTER'
            row.label(text="Scenegraph Path")
            row.prop(self, "prune_path", text="")  # Keep input field

        # Draw output socket at the bottom
        if self.outputs:
            row = layout.row()
            row.alignment = 'CENTER'
            row.label(text="Pruned Output")


class NODE_OT_AddPruneNode(bpy.types.Operator):
    """
    Add a Prune Node to the Custom Node Tree
    """
    bl_idname = "node.add_prune_node"
    bl_label = "Add Prune Node"
    nodeType = "RenderingLightingPruneNode"

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