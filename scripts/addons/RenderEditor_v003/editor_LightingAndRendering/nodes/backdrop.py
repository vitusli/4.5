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


class NODE_OT_AddFrameNode(bpy.types.Operator):
    """Add a Frame Node for Organization"""
    bl_idname = "node.add_frame_node"
    bl_label = "Add Frame Node"
    bl_options = {'REGISTER', 'UNDO'}
    nodeType = "NodeFrame"

    def execute(self, context):
        space = context.space_data

        if not space or not space.node_tree:
            self.report({'WARNING'}, "No active node tree found")
            return {'CANCELLED'}

        # Create a frame node
        frame_node = space.node_tree.nodes.new(type=self.nodeType)
        frame_node.label = "New Frame"
        frame_node.color = (0.2, 0.2, 0.3)  # Slightly darker color for organization

        return {'FINISHED'}
    
    def invoke(self, context, event):
        space = context.space_data
        nodes = space.node_tree.nodes

        bpy.ops.node.select_all(action='DESELECT')

        node = nodes.new(self.nodeType)
        node.select = True
        node.location = utilityFunctions.get_current_loc(context, event, context.preferences.system.ui_scale)

        bpy.ops.node.translate_attach_remove_on_cancel("INVOKE_DEFAULT")

        return {"FINISHED"}
