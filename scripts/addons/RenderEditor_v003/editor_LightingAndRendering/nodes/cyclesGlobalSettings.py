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


class RenderingLightingGlobalSettings(bpy.types.Node):
    """
    A node for setting Global Render Settings
    """
    bl_idname = "RenderingLightingGlobalSettings"
    bl_label = "CyclesGlobalSettings"
    bl_icon = "MOD_DECIM"

    noiseThreshold: bpy.props.FloatProperty(
        name="Noise Threshold",
        description="The variance between bucket passes to which adaptive sampling will cease to render the bucket",
        default=0.05,
        min=0.0,
        max=1.0,
        update=lambda self, context: self.executeViewportCook()
    )

    maxSamples: bpy.props.IntProperty(
        name="Max Samples",
        description="The upper limit of samples when rendering",
        default=2048,
        update=lambda self, context: self.executeViewportCook()
    )

    minSamples: bpy.props.IntProperty(
        name="Min Samples",
        description="The lower limit of samples when rendering",
        default=0,
        update=lambda self, context: self.executeViewportCook()
    )

    timeLimit: bpy.props.FloatProperty(
        name="Time Limit",
        description="The time for which blender will stop rendering",
        default=0.00,
        update=lambda self, context: self.executeViewportCook()
    )

    lightTree: bpy.props.BoolProperty(
        name="Light Tree",
        description="Whether to create a light tree to determine light contribution and cease sampling of non contributing lights",
        default=True,
        update=lambda self, context: self.executeViewportCook()
    )

    totalBounces: bpy.props.IntProperty(
        name="Total Bounces",
        description="Total number of light bounces",
        default=12,
        min=0,
        update=lambda self, context: self.executeViewportCook()
    )

    diffuseBounces: bpy.props.IntProperty(
        name="Diffuse Bounces",
        description="Total number of Diffuse bounces",
        default=4,
        min=0,
        update=lambda self, context: self.executeViewportCook()
    )

    glossyBounces: bpy.props.IntProperty(
        name="Glossy Bounces",
        description="Total number of Glossy bounces",
        default=4,
        min=0,
        update=lambda self, context: self.executeViewportCook()
    )

    transmissionBounces: bpy.props.IntProperty(
        name="Transmission Bounces",
        description="Total number of Transmission bounces",
        default=12,
        min=0,
        update=lambda self, context: self.executeViewportCook()
    )

    volumeBounces: bpy.props.IntProperty(
        name="Volume Bounces",
        description="Total number of Volume bounces",
        default=0,
        min=0,
        update=lambda self, context: self.executeViewportCook()
    )

    transparentBounces: bpy.props.IntProperty(
        name="transparent Bounces",
        description="Total number of transparent bounces",
        default=8,
        min=0,
        update=lambda self, context: self.executeViewportCook()
    )

    directLightClamp: bpy.props.FloatProperty(
        name="Direct Light Clamp",
        description="The max value for a direct rays pixel",
        default=0.0,
        min=0.0,
        update=lambda self, context: self.executeViewportCook()
    )

    indirectLightClamp: bpy.props.FloatProperty(
        name="Indirect Light Clamp",
        description="The max value for an indirect rays pixel",
        default=10.00,
        min=0.0,
        update=lambda self, context: self.executeViewportCook()
    )

    filterGlossy: bpy.props.FloatProperty(
        name="Filter Glossy",
        description="Amount to blur glossy pixels",
        default=1.0,
        min=0.0,
        update=lambda self, context: self.executeViewportCook()
    )

    reflectiveCaustics: bpy.props.BoolProperty(
        name="Reflective Caustics",
        description="Calculate Reflective Caustics",
        default=True,
        update=lambda self, context: self.executeViewportCook()
    )

    refractiveCaustics: bpy.props.BoolProperty(
        name="Refractive Caustics",
        description="Calculate Refractive Caustics",
        default=True,
        update=lambda self, context: self.executeViewportCook()
    )

    fastGiApproximation: bpy.props.BoolProperty(
        name="Fast GI Approximation",
        description="Speed up renders by losing accuracy and estimating GI using some AO stuff",
        default=False,
        update=lambda self, context: self.executeViewportCook()
    )

    fgaMethod: bpy.props.EnumProperty(
        name="Method",
        description="Method of FGA To use",
        items=[("REPLACE", "Replace",""), ("ADD", "Add", "")],
        default="REPLACE",
        update=lambda self, context: self.executeViewportCook()
    )

    fgaBounces: bpy.props.IntProperty(
        name="Bounces",
        description="Amount of AO bounces to use",
        default=1,
        update=lambda self, context: self.executeViewportCook()
    )

    volumeStepSize: bpy.props.FloatProperty(
        name="Volume Step Size",
        description="Higher values decrease detail in volumes but dramaticallly reduce render time",
        default=1.0,
        update=lambda self, context: self.executeViewportCook()
    )

    motionBlur: bpy.props.BoolProperty(
        name="Motion Blur",
        description="Enable Motion Blur",
        default=True,
        update=lambda self, context: self.executeViewportCook()
    )

    enableAlphaImages: bpy.props.BoolProperty(
        name="Allow Alphad Images",
        description="Allows images to contain an alpha channel",
        default=True,
        update=lambda self, context: self.executeViewportCook()
    )

    transparentGlassInAlpha: bpy.props.BoolProperty(
        name="Transparent Glass In Alpha",
        description="Allow glass to rendered with transparency for comping over plates",
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
        layout.alignment = 'CENTER'
        layout.label(text="Sampling")
        layout.prop(self, "noiseThreshold", text="Noise Threshold")
        layout.prop(self, "maxSamples", text="Max Samples")
        layout.prop(self, "minSamples", text="Min Samples")
        layout.prop(self, "timeLimit", text="Time Limit")

        layout.separator()
        layout.label(text="Lights")
        layout.prop(self, "lightTree", text="Light Tree")

        layout.separator()
        layout.label(text="Light Paths")
        layout.label(text="Light Bounces")
        layout.prop(self, "totalBounces", text="Total Bounces")
        layout.prop(self, "diffuseBounces", text="Diffuse Bounces")
        layout.prop(self, "glossyBounces", text="Glossy Bounces")
        layout.prop(self, "transmissionBounces", text="Transmission Bounces")
        layout.prop(self, "volumeBounces", text="Volume Bounces")
        layout.prop(self, "transparentBounces", text="Transparent Bounces")

        layout.label(text="Clamping")
        layout.prop(self, "directLightClamp", text="Direct Light Clamp")
        layout.prop(self, "indirectLightClamp", text="Indirect Light Clamp")

        layout.label(text="Caustics")
        layout.prop(self, "filterGlossy", text="Filter Glossy")
        layout.prop(self, "reflectiveCaustics", text="Reflective Caustics")
        layout.prop(self, "refractiveCaustics", text="Refractive Caustics")

        layout.label(text="Fast GI Approximation")
        layout.prop(self, "fastGiApproximation", text="Fast Gi Approximation")
        layout.prop(self, "fgaMethod", text="Method")
        layout.separator()
        layout.prop(self, "volumeStepSize", text="Volume Step Size")
        layout.prop(self, "motionBlur", text="Motion Blur")
        layout.prop(self, "enableAlphaImages", text="Enable Alpha Channel")
        layout.prop(self, "transparentGlassInAlpha", text="Transparent Glass In Alpha")
        
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
        scene.cycles.adaptive_threshold = self.noiseThreshold
        scene.cycles.samples = self.maxSamples
        scene.cycles.adaptive_min_samples = self.minSamples
        
        scene.cycles.time_limit = self.timeLimit

        scene.cycles.use_light_tree = self.lightTree

        scene.cycles.max_bounces = self.totalBounces
        scene.cycles.diffuse_bounces = self.diffuseBounces
        scene.cycles.glossy_bounces = self.glossyBounces
        scene.cycles.transmission_bounces = self.transmissionBounces
        scene.cycles.volume_bounces = self.volumeBounces
        scene.cycles.transparent_max_bounces = self.transparentBounces

        scene.cycles.sample_clamp_direct = self.directLightClamp
        scene.cycles.sample_clamp_indirect = self.indirectLightClamp

        scene.cycles.blur_glossy = self.filterGlossy
        scene.cycles.caustics_reflective = self.reflectiveCaustics
        scene.cycles.caustics_refractive = self.refractiveCaustics

        scene.cycles.use_fast_gi = self.fastGiApproximation
        scene.cycles.fast_gi_method = self.fgaMethod

        scene.cycles.volume_step_rate = self.volumeStepSize
        scene.render.use_motion_blur = self.motionBlur
        scene.render.film_transparent = self.enableAlphaImages
        scene.cycles.film_transparent_glass = self.transparentGlassInAlpha


class NODE_OT_AddGlobalSettings(bpy.types.Operator):
    """
    Add a Render Layer to the Custom Node Tree
    """
    bl_idname = "node.add_global_settings_node"
    bl_label = "Add Global Settings Node"
    nodeType = "RenderingLightingGlobalSettings"
    
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