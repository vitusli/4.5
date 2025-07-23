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


class CyclesLightingObjectsSettings(bpy.types.Node):
    """
    A node for setting Obect flags
    """
    bl_idname = "CyclesLightingObjectSettings"
    bl_label = "CyclesObjectSettings"
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

    shadowCatcher: bpy.props.BoolProperty(
        name="Shadow Catcher",
        description="Whether the mesh is a shadowCatcher",
        default=False,
        update=lambda self, context: self.executeViewportCook()
    )

    holdout: bpy.props.BoolProperty(
        name="Holdout",
        description="Whether the mesh is a holdout",
        default=False,
        update=lambda self, context: self.executeViewportCook()
    )

    rayCamera: bpy.props.BoolProperty(
        name="Camera Rays",
        description="Whether the mesh is visible to Camera Rays",
        default=True,
        update=lambda self, context: self.executeViewportCook()
    )

    rayDiffuse: bpy.props.BoolProperty(
        name="Diffuse Rays",
        description="Whether the mesh is visible to Diffuse Rays",
        default=True,
        update=lambda self, context: self.executeViewportCook()
    )

    rayGlossy: bpy.props.BoolProperty(
        name="Glossy Rays",
        description="Whether the mesh is visible to Glossy Rays",
        default=True,
        update=lambda self, context: self.executeViewportCook()
    )

    rayTransmission: bpy.props.BoolProperty(
        name="Transmission Rays",
        description="Whether the mesh is visible to Transmission Rays",
        default=True,
        update=lambda self, context: self.executeViewportCook()
    )

    rayVolumeScatter: bpy.props.BoolProperty(
        name="Volume Scatter Rays",
        description="Whether the mesh is visible to Volume Scatter Rays",
        default=True,
        update=lambda self, context: self.executeViewportCook()
    )

    rayShadow: bpy.props.BoolProperty(
        name="Shadow Rays",
        description="Whether the mesh is visible to Volume Shadow Rays",
        default=True,
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
        layout.prop(self, "shadowCatcher", text="Shadow Catcher")
        layout.prop(self, "holdout", text="Holdout")
        layout.separator()
        layout.prop(self, "rayCamera", text="Camera Rays")
        layout.prop(self, "rayDiffuse", text="Diffuse Rays")
        layout.prop(self, "rayGlossy", text="Glossy Rays")
        layout.prop(self, "rayTransmission", text="Transmission Rays")
        layout.prop(self, "rayVolumeScatter", text="Volume Scatter Rays")
        layout.prop(self, "rayShadow", text="Shadow Rays")
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

        mesh.is_shadow_catcher = self.shadowCatcher
        mesh.is_holdout = self.holdout

        mesh.visible_camera = self.rayCamera
        mesh.visible_diffuse = self.rayDiffuse
        mesh.visible_glossy = self.rayGlossy
        mesh.visible_transmission = self.rayTransmission
        mesh.visible_volume_scatter = self.rayVolumeScatter
        mesh.visible_shadow = self.rayShadow


class NODE_OT_AddObjectSettings(bpy.types.Operator):
    """
    Add a Blender Object Settings to the Custom Node Tree
    """
    bl_idname = "node.add_blender_object_settings_node"
    bl_label = "Add Blender Object Settings Node"
    nodeType = "CyclesLightingObjectSettings"
    
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