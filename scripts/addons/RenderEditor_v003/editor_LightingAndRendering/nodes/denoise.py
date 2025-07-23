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


class RenderingLightingDenoise(bpy.types.Node):
    """
    A node for setting the denoise settings
    """
    bl_idname = "RenderingLightingDenoise"
    bl_label = "Denoise"
    bl_icon = "MOD_DECIM"

    enableDenoise: bpy.props.BoolProperty(
        name="enableDenoise",
        description="Whether to denoise the rendered image",
        default=True,
        update=lambda self, context: self.executeViewportCook()
    )

    denoiseMethod: bpy.props.EnumProperty(
        name="Denoise Method",
        description="Select the denoising method",
        items=[
            ("OPTIX", "OptiX", "NVIDIA OptiX AI denoiser"),
            ("OPENIMAGEDENOISE", "OpenImageDenoise", "Intel OpenImageDenoise"),
        ],
        default="OPENIMAGEDENOISE"
    )

    denoisePasses: bpy.props.EnumProperty(
        name="Denoise Passes",
        description="Select the denoising data to use",
        items=[
            ("NONE", "None", "Disable denoising"),
            ("ALBEDO", "Albedo", "Use albedo for denoising"),
            ("ALBEDO_NORMAL", "Albedo and Normal", "Use albedo and normal data for denoising"),
        ],
        default="ALBEDO_NORMAL"
    )

    enableDenoiseAOVS: bpy.props.BoolProperty(
        name="Enable Denoise AOVS",
        description="Store the AOVs required for denoising",
        default=True
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
        layout.label(text="Sampling")
        layout.prop(self, "enableDenoise", text="Enable Denoise")
        layout.prop(self, "denoiseMethod", text="Denoise Method")
        layout.prop(self, "denoisePasses", text="Denoise Passes")
        layout.prop(self, "enableDenoiseAOVS", text = "Enable denoise AOVs")

        # Cook node Button
        layout.operator("node.cook_scene_from_node", text = "Cook Scene", icon="FILE_REFRESH")

    def executeNodeCookFunctions(self):
        utilityFunctions.setViewedNode(self)
        self.updateRenderAttributes()

    def executeViewportCook(self):
        viewedNode = utilityFunctions.getViewedNode()
        if self != viewedNode:
            return

        self.executeNodeCookFunctions()

    def updateRenderAttributes(self):
        scene = bpy.context.scene

        scene.cycles.use_denoising = self.enableDenoise
        scene.cycles.denoiser = self.denoiseMethod
        scene.cycles.denoising_input_paths = self.denoisePasses
        bpy.context.view_layer.cycles.denoising_store_passes = self.enableDenoiseAOVS

            
class NODE_OT_AddDenoise(bpy.types.Operator):
    """
    Add a Render Layer to the Custom Node Tree
    """
    bl_idname = "node.add_blender_denoise_node"
    bl_label = "Add Denoise Node"
    nodeType = "RenderingLightingDenoise"
    
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