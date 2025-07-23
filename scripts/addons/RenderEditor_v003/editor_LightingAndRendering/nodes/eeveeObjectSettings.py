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


class EeveeLightingObjectsSettings(bpy.types.Node):
    """
    A node for setting Obect flags
    """
    bl_idname = "EeveeLightingObjectSettings"
    bl_label = "EeveeObjectSettings"
    bl_icon = "MOD_DECIM"

    matchStatement: bpy.props.StringProperty(
        name="Match Statement",
        description="Enter a Match statement",
        default="",
        update=lambda self, context: self.executeViewportCook()
    )

    viewPortVisibility: bpy.props.BoolProperty(
        name="Viewport Visiblty",
        description="Whether the mesh is visible in the viewport",
        default=True,
        update=lambda self, context: self.executeViewportCook()
    )

    renderVisibility: bpy.props.BoolProperty(
        name="Render Visiblty",
        description="Whether the mesh is visible in the Render",
        default=True,
        update=lambda self, context: self.executeViewportCook()
    )

    holdout: bpy.props.BoolProperty(
        name="Holdout",
        description="Whether the mesh is a holdout",
        default=False,
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
        Draw the node layout and update labels dynamically
        """
        # Cel statement
        layout.alignment = 'CENTER'
        row = layout.row()
        row.scale_x = 2.0
        row.alignment = 'LEFT'
        row.prop(self, "matchStatement", text="Match Statement")

        layout.separator()
        # flag checkboxes
        layout.prop(self, "viewPortVisibility", text="Viewport Visibility")
        layout.prop(self, "renderVisibility", text="Render Visibility")
        layout.separator()
        layout.prop(self, "holdout", text="Holdout")
        layout.separator()
        # Cook button
        layout.operator("node.cook_scene_from_node", text = "Cook Scene", icon="FILE_REFRESH")

    def executeNodeCookFunctions(self):
        utilityFunctions.setViewedNode(self)
        collection = utilityFunctions.getCollection(self)
        matchedObjects = self.resolveCelStatement()

        if not matchedObjects:
            return
        
        for mesh in matchedObjects:
            self.setAttributes(mesh)

    def executeViewportCook(self):
        viewedNode = utilityFunctions.getViewedNode()
        if self != viewedNode:
            return

        self.executeNodeCookFunctions()

    def resolveCelStatement(self):
        scene = utilityFunctions.getCollection(self)
        cel = self.matchStatement.strip()
        matchedObjects = utilityFunctions.searchSceneObjectsRecursive(cel, scene)

        if not matchedObjects:
            return None
        
        return matchedObjects
        
    def setAttributes(self, mesh):
        mesh.hide_viewport = not self.viewPortVisibility
        mesh.hide_render = not self.renderVisibility

        mesh.is_holdout = self.holdout


class NODE_OT_AddEeveeObjectSettings(bpy.types.Operator):
    """
    Add a Blender Object Settings to the Custom Node Tree
    """
    bl_idname = "node.add_eevee_object_settings_node"
    bl_label = "Add Eevee Object Settings Node"
    nodeType = "EeveeLightingObjectSettings"
    
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