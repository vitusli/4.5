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


class RenderingLightingEeveeGlobalSettings(bpy.types.Node):
    """
    A node for setting Global Render Settings
    """
    bl_idname = "RenderingLightingEeveeGlobalSettings"
    bl_label = "EeveeGlobalSettings"
    bl_icon = "MOD_DECIM"

    renderSamples: bpy.props.IntProperty(
        name="Render Samples",
        description="The upper limit of samples when rendering",
        default=64,
        update=lambda self, context: self.executeViewportCook()
    )
    
    viewportSamples: bpy.props.IntProperty(
        name="Render Samples",
        description="The upper limit of samples when rendering in the viewport",
        default=16,
        update=lambda self, context: self.executeViewportCook()
    )

    viewportDenoising: bpy.props.BoolProperty(
        name="Viewport Denoising",
        description="Whether to denoise while rendering in the viewport",
        default=True,
        update=lambda self, context: self.executeViewportCook()
    )

    ao: bpy.props.BoolProperty(
        name="Amient Occlussion",
        description="Whether to enable AO or not",
        default=False,
        update=lambda self, context: self.executeViewportCook()
    )

    distance: bpy.props.FloatProperty(
        name="AO Distance",
        description="The distance of AO to Use",
        default=0.2,
        min=0.0,
        max=5,
        update=lambda self, context: self.executeViewportCook()
    )

    factor: bpy.props.FloatProperty(
        name="AO Factor",
        description="The FActor of AO",
        default=1.0,
        min=0.0,
        max=1.0,
        update=lambda self, context: self.executeViewportCook()
    )

    tracePrecission: bpy.props.FloatProperty(
        name="Trace Precission",
        description="Precission of the trace",
        default=.25,
        min=0.0,
        max=1.0,
        update=lambda self, context: self.executeViewportCook()
    )

    bentNormals: bpy.props.BoolProperty(
        name="Bent Normals",
        description="Whether we should bend the normals",
        default=True,
        update=lambda self, context: self.executeViewportCook()
    )

    bouncesApproximation: bpy.props.BoolProperty(
        name="Bounces Approximation",
        description="Whether we approximate bounces",
        default=True,
        update=lambda self, context: self.executeViewportCook()
    )

    bloom: bpy.props.BoolProperty(
        name="Bloom",
        description="Use bloom",
        default=False,
        update=lambda self, context: self.executeViewportCook()
    )

    bloom_threshold: bpy.props.FloatProperty(
        name="Bloom Threshold",
        default=.8,
        min=0.0,
        max=10.0,
        update=lambda self, context: self.executeViewportCook()
    )

    bloom_knee: bpy.props.FloatProperty(
        name="Knee",
        default=.5,
        min=0.0,
        max=1.0,
        update=lambda self, context: self.executeViewportCook()
    )

    bloom_radius: bpy.props.FloatProperty(
        name="Radius",
        default=6.5,
        min=0.0,
        max=10.0,
        update=lambda self, context: self.executeViewportCook()
    )

    bloom_color: bpy.props.FloatVectorProperty(
        name="Bloom Color", 
        subtype='COLOR', 
        default=(1.0, 1.0, 1.0), 
        size=3, 
        min=0.0, max=1.0,
        update=lambda self, context: self.executeViewportCook()
    )

    bloom_intensity: bpy.props.FloatProperty(
        name="Bloom Intensity",
        default=.050,
        min=0.0,
        max=.1,
        update=lambda self, context: self.executeViewportCook()
    )

    bloom_clamp: bpy.props.FloatProperty(
        name="Bloom Clamp",
        default=0.0,
        min=0.0,
        max=1000,
        update=lambda self, context: self.executeViewportCook()
    )

    dof_maxSize: bpy.props.IntProperty(
        name="DOF Max Size",
        default=100,
        min=0,
        max=200,
        update=lambda self, context: self.executeViewportCook()
    )

    dof_spirteThreshold: bpy.props.FloatProperty(
        name="DOF Sprite Threshold",
        default=1.0,
        min=0.0,
        max=10.0,
        update=lambda self, context: self.executeViewportCook()
    )

    dof_neighbourRejection: bpy.props.FloatProperty(
        name="DOF Neighbour Rejection",
        default=10.0,
        min=0.0,
        max=40.0,
        update=lambda self, context: self.executeViewportCook()
    )

    dof_denoiseAmount: bpy.props.FloatProperty(
        name="DOF Denoise Amount",
        default=.75,
        min=0.0,
        max=1.0,
        update=lambda self, context: self.executeViewportCook()
    )

    dof_highQualitySlightDefocus: bpy.props.BoolProperty(
        name="DOF High Quality Defocus",
        default=False,
        update=lambda self, context: self.executeViewportCook()
    )

    dof_jitterCamera: bpy.props.BoolProperty(
        name="DOF Jitter Camera",
        default=False,
        update=lambda self, context: self.executeViewportCook()
    )

    dof_overBlur: bpy.props.FloatProperty(
        name="DOF Over Blur",
        default=5.0,
        min=0.0,
        max=20.0,
        update=lambda self, context: self.executeViewportCook()
    )

    sss_samples: bpy.props.IntProperty(
        name="SSS Samples",
        default=7,
        min=1,
        max=32,
        update=lambda self, context: self.executeViewportCook()
    )

    sss_jitterThreshold: bpy.props.FloatProperty(
        name="SSS Jitter Threshold",
        default=0.3,
        min=0.0,
        max=1.0,
        update=lambda self, context: self.executeViewportCook()
    )

    ssr_enable: bpy.props.BoolProperty(
        name="SSR Enable",
        default=False,
        update=lambda self, context: self.executeViewportCook()
    )

    ssr_Refraction: bpy.props.BoolProperty(
        name="SSR Refraction",
        default=False,
        update=lambda self, context: self.executeViewportCook()
    )

    ssr_halfResTrace: bpy.props.BoolProperty(
        name="SSR Half Res Trace",
        default=True,
        update=lambda self, context: self.executeViewportCook()
    )

    ssr_tracePrecission: bpy.props.FloatProperty(
        name="SSR Trace Precission",
        default=0.250,
        min=0.0,
        max=1.0,
        update=lambda self, context: self.executeViewportCook()
    )

    ssr_maxRoughness: bpy.props.FloatProperty(
        name="SSR Max Roughness",
        default=0.5,
        min=0.0,
        max=1.0,
        update=lambda self, context: self.executeViewportCook()
    )

    ssr_Thickness: bpy.props.FloatProperty(
        name="SSR Thickness",
        default=0.2,
        min=0.0,
        max=1.0,
        update=lambda self, context: self.executeViewportCook()
    )

    ssr_edgeFading: bpy.props.FloatProperty(
        name="SSR Edge Fading",
        default=0.075,
        min=0.0,
        max=0.5,
        update=lambda self, context: self.executeViewportCook()
    )

    ssr_clamp: bpy.props.FloatProperty(
        name="SSR Clamp",
        default=10.0,
        min=0.0,
        max=10000,
        update=lambda self, context: self.executeViewportCook()
    )

    mb_enable: bpy.props.BoolProperty(
        name="MB Enable",
        default=False,
        update=lambda self, context: self.executeViewportCook()
    )

    mb_shutter: bpy.props.FloatProperty(
        name="MB Shutter", 
        default=0.5, 
        min=0.0, 
        max=1.0, 
        update=lambda self, context: self.executeViewportCook()
    )

    mb_position: bpy.props.EnumProperty(
        name="MB Position", 
        items=[("START", "Start", "Start"), ("CENTER", "Center", "Center"), ("END", "End", "End")], 
        default="CENTER", 
        update=lambda self, context: self.executeViewportCook()
    )

    mb_backgroundSeparation: bpy.props.FloatProperty(
        name="MB Background Separation", 
        default=100.0, 
        min=0.0, 
        max=10000.0, 
        update=lambda self, context: self.executeViewportCook()
    )

    mb_maxBlur: bpy.props.IntProperty(
        name="MB Max Blur", 
        default=32, 
        min=1, 
        max=512,
        update=lambda self, context: self.executeViewportCook()
    )

    mb_steps: bpy.props.IntProperty(
        name="MB Max Steps", 
        default=16, 
        min=1, 
        max=64, 
        update=lambda self, context: self.executeViewportCook()
    )

    vol_start: bpy.props.FloatProperty(name="Volumetric Start", default=0.1, min=0.0, max=100.0, update=lambda self, context: self.executeViewportCook())
    vol_end: bpy.props.FloatProperty(name="Volumetric End", default=100.0, min=0.0, max=1000.0, update=lambda self, context: self.executeViewportCook())
    vol_tile_size: bpy.props.EnumProperty(
        name="Volumetric Tile Size",
        items=[('1', "1", "Tile size 1"),
            ('2', "2", "Tile size 2"),
            ('4', "4", "Tile size 4"),
            ('8', "8", "Tile size 8"),
            ('16', "16", "Tile size 16"),
        ],
        default="8",
        update=lambda self, context: self.executeViewportCook()
    )
    vol_samples: bpy.props.IntProperty(name="Volumetric Samples", default=64, min=1, max=256, update=lambda self, context: self.executeViewportCook())
    vol_distribution: bpy.props.FloatProperty(name="Volumetric Distribution", default=0.8, min=0.0, max=1.0, update=lambda self, context: self.executeViewportCook())
    vol_lighting: bpy.props.BoolProperty(name="Volumetric Lighting", default=True, update=lambda self, context: self.executeViewportCook())
    vol_light_clamp: bpy.props.FloatProperty(name="Light Clamping", default=10.0, min=0.0, max=100.0, update=lambda self, context: self.executeViewportCook())
    vol_shadow: bpy.props.BoolProperty(name="Volumetric Shadows", default=False, update=lambda self, context: self.executeViewportCook())
    vol_shadow_samples: bpy.props.IntProperty(name="Volumetric Shadow Samples", default=16, min=1, max=128, update=lambda self, context: self.executeViewportCook())

    performance_highQualNormals: bpy.props.BoolProperty(name="Performance High Quality Normals", default=False, update=lambda self, context: self.executeViewportCook())

    curves_shape: bpy.props.EnumProperty(
        name="Curves Hair Type",
        description="Select the hair type for rendering",
        items=[
            ('STRAND', "Strand", "Render hair as individual strands"),
            ('STRIP', "Strip", "Render hair as a Strip"),
        ],
        default='STRAND',
        update=lambda self, context: self.executeViewportCook()
    )
    curves_additionalSubdivision: bpy.props.IntProperty(name="Curves Additional Subdivision", default=0, min=0, max=3, update=lambda self, context: self.executeViewportCook())

    shadows_cubeSize: bpy.props.EnumProperty(
        name="Shadow Cube Size",
        description="Select the cube size for shadow maps",
        items=[
            ('64', "64", "Shadow cube size 64"),
            ('128', "128", "Shadow cube size 128"),
            ('256', "256", "Shadow cube size 256"),
            ('512', "512", "Shadow cube size 512"),
            ('1024', "1024", "Shadow cube size 1024")
        ],
        default='512',
        update=lambda self, context: self.executeViewportCook()
    )
    shadows_cascadeSize: bpy.props.EnumProperty(
        name="Shadow Cascade Size",
        description="Select the cascade size for shadow mapping",
        items=[
            ('512', "512", "Shadow cascade size 512"),
            ('1024', "1024", "Shadow cascade size 1024"),
            ('2048', "2048", "Shadow cascade size 2048"),
            ('4096', "4096", "Shadow cascade size 4096")
        ],
        default='1024',
        update=lambda self, context: self.executeViewportCook()
    )
    shadow_highBitDepth: bpy.props.BoolProperty(name="High Bit Depth", default=False, update=lambda self, context: self.executeViewportCook())
    shadow_softShadows: bpy.props.BoolProperty(name="Soft Shadows", default=True, update=lambda self, context: self.executeViewportCook())
    shadow_lightThreshold: bpy.props.FloatProperty(name="Light threshold", default=0.010, min=0.0, max=1.0, update=lambda self, context: self.executeViewportCook())

    film_filterSize: bpy.props.FloatProperty(name="Film Filter Size", default=1.50, min=0.01, max=10.0, update=lambda self, context: self.executeViewportCook())
    film_transparent: bpy.props.BoolProperty(name="Film Transparent", default=True, update=lambda self, context: self.executeViewportCook())
    film_overscan: bpy.props.BoolProperty(name="Film Overscan", default=False, update=lambda self, context: self.executeViewportCook())
    film_overScanAmount: bpy.props.FloatProperty(name="Film Overscan Amount", default=3.00, min=0.00, max=10.0, update=lambda self, context: self.executeViewportCook())

    simplify_enable: bpy.props.BoolProperty(
        name="Simplify Enable",
        description="Enable Simplify settings",
        default=False,
        update=lambda self, context: self.executeViewportCook()
    )
    simplify_max_subdivision: bpy.props.IntProperty(
        name="Max Subdivision",
        description="Set the maximum subdivision level for the viewport",
        default=6,
        min=0,
        max=6,
        update=lambda self, context: self.executeViewportCook()
    )
    simplify_max_child_particles: bpy.props.FloatProperty(
        name="Max Child Particles",
        description="Set the maximum number of child particles for the viewport",
        default=1.0,
        min=0.0,
        max=1.0,
        update=lambda self, context: self.executeViewportCook()
    )
    simplify_volume_resolution: bpy.props.FloatProperty(
        name="Volume Resolution",
        description="Set the volume resolution for the viewport",
        default=1.0,
        min=0.0,
        max=1.0,
        update=lambda self, context: self.executeViewportCook()
    )
    simplify_shadow_resolution: bpy.props.FloatProperty(
        name="Shadow Resolution",
        description="Set the shadow resolution for the viewport",
        default=1.0,
        min=0.0,
        max=1.0,
        update=lambda self, context: self.executeViewportCook()
    )
    simplify_normals: bpy.props.BoolProperty(
        name="Simplify Normals",
        description="Simplify normals in the viewport",
        default=False,
        update=lambda self, context: self.executeViewportCook()
    )
    simplify_render_max_subdivision: bpy.props.IntProperty(
        name="Max Subdivision (Render)",
        description="Set the maximum subdivision level for rendering",
        default=6,
        min=0,
        max=6,
        update=lambda self, context: self.executeViewportCook()
    )
    simplify_render_max_child_particles: bpy.props.FloatProperty(
        name="Max Child Particles (Render)",
        description="Set the maximum number of child particles for rendering",
        default=1.0,
        min=0.0,
        max=1.0,
        update=lambda self, context: self.executeViewportCook()
    )
    simplify_render_shadow_resolution: bpy.props.FloatProperty(
        name="Shadow Resolution (Render)",
        description="Set the shadow resolution for rendering",
        default=1.0,
        min=0.0,
        max=1.0,
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
        scene = bpy.context.scene
        layout.alignment = 'CENTER'
        layout.label(text="Sampling")
        layout.prop(self, "renderSamples", text="Render Samples")
        layout.prop(self, "viewportSamples", text="Viewport Samples")
        layout.prop(self, "viewportDenoising", text="Viewport Denoising")
        
        layout.separator()
        layout.label(text="AO")
        layout.prop(self, "ao", text="Enable AO")
        layout.prop(self, "distance", text="Distance")
        layout.prop(self, "factor", text="Factor")
        layout.prop(self, "tracePrecission", text="Trace Precission")
        layout.prop(self, "bentNormals", text="Bent Normals")
        layout.prop(self, "bouncesApproximation", text="Bounces Approximation")

        layout.separator()
        layout.label(text="Bloom")
        layout.prop(self, "bloom", text="Enable Bloom")
        layout.prop(self, "bloom_threshold", text="Threshold")
        layout.prop(self, "bloom_knee", text="Knee")
        layout.prop(self, "bloom_radius", text="Radius")
        layout.prop(self, "bloom_color", text="Color")
        layout.prop(self, "bloom_intensity", text="Intensity")
        layout.prop(self, "bloom_clamp", text="Clamp")

        layout.separator()
        layout.label(text="DOF")
        layout.prop(self, "mb_enable", text="Max Size")
        layout.prop(self, "dof_spirteThreshold", text="Sprite Threshold")
        layout.prop(self, "dof_neighbourRejection", text="Neighbour Rejection")
        layout.prop(self, "dof_denoiseAmount", text="Denoise Amount")
        layout.prop(self, "dof_highQualitySlightDefocus", text="High Quality Slight Defocus")
        layout.prop(self, "dof_jitterCamera", text="Jitter Camera")
        layout.prop(self, "dof_overBlur", text="Over Blur")

        layout.separator()
        layout.label(text="SSS")
        layout.prop(self, "sss_samples", text="SSS Samples")
        layout.prop(self, "sss_jitterThreshold", text="SSS Jitter Threshold")

        layout.separator()
        layout.label(text="Screen Space Reflections")
        layout.prop(self, "ssr_enable", text="Enable SSR")
        layout.prop(self, "ssr_Refraction", text="Refraction")
        layout.prop(self, "ssr_halfResTrace", text="Half Res Trace")
        layout.prop(self, "ssr_tracePrecission", text="Trace Precission")
        layout.prop(self, "ssr_maxRoughness", text="Max Roughness")
        layout.prop(self, "ssr_Thickness", text="Thickness")
        layout.prop(self, "ssr_edgeFading", text="EdgeFading")
        layout.prop(self, "ssr_clamp", text="clamp")

        layout.separator()
        layout.label(text="Motion Blur")
        layout.prop(self, "mb_enable", text="Enable Motion Blur")
        layout.prop(self, "mb_position", text="Position")
        layout.prop(self, "mb_shutter", text="Shutter")
        layout.prop(self, "mb_backgroundSeparation", text="Background Seperation")
        layout.prop(self, "mb_maxBlur", text="Max Blur")
        layout.prop(self, "mb_steps", text="Steps")

        layout.separator()
        layout.label(text="Volumetrics")
        layout.prop(self, "vol_start", text="Start")
        layout.prop(self, "vol_end", text="End")
        layout.prop(self, "vol_tile_size", text="Tile Size")
        layout.prop(self, "vol_samples", text="Samples")
        layout.prop(self, "vol_distribution", text="Distribution")
        layout.prop(self, "vol_lighting", text="Volumetric Lighting")
        layout.prop(self, "vol_light_clamp", text="Light Clamping")
        layout.prop(self, "vol_shadow", text="Volumetric Shadows")
        layout.prop(self, "vol_shadow_samples", text="Samples")

        layout.separator()
        layout.label(text="Performance")
        layout.prop(self, "performance_highQualNormals", text="High Quality Normals")

        layout.separator()
        layout.label(text="Curves")
        layout.prop(self, "curves_shape", text="Shape")
        layout.prop(self, "curves_additionalSubdivision", text="Additional Subdivision")

        layout.separator()
        layout.label(text="Shadows")
        layout.prop(self, "shadows_cubeSize", text="Cube Size")
        layout.prop(self, "shadows_cascadeSize", text="Cascade Size")
        layout.prop(self, "shadow_highBitDepth", text="High Bit Depth")
        layout.prop(self, "shadow_softShadows", text="Soft Shadows")
        layout.prop(self, "shadow_lightThreshold", text="Light Threshold")

        layout.separator()
        layout.label(text="Film")
        layout.prop(self, "film_filterSize", text="Film Filter Size")
        layout.prop(self, "film_transparent", text="Film Transparent")
        layout.prop(self, "film_overscan", text="High Film OverScan")
        layout.prop(self, "film_overScanAmount", text="Film OverScan Amount")

        # Viewport simplify settings
        layout.label(text="Simplify")
        layout.prop(self, "simplify_enable", text="Simplify Enable")
        layout.label(text="Viewport Simplify:")
        layout.prop(self, "simplify_max_subdivision", text="Max Subdivision")
        layout.prop(self, "simplify_max_child_particles", text="Max Child Particles")
        layout.prop(self, "simplify_volume_resolution", text="Volume Resolution")
        layout.prop(self, "simplify_shadow_resolution", text="Shadow Resolution")
        layout.prop(self, "simplify_normals", text="normals")

        # Render simplify settings
        layout.label(text="Render Simplify:")
        layout.prop(self, "simplify_render_max_subdivision", text="Max Subdivision")
        layout.prop(self, "simplify_render_max_child_particles", text="Max Child Particles")
        layout.prop(self, "simplify_render_shadow_resolution", text="Shadow Resolution")

        # Cook node Button
        layout.separator()
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
        scene.eevee.taa_render_samples = self.renderSamples
        scene.eevee.taa_samples = self.viewportSamples
        scene.eevee.use_taa_reprojection = self.viewportDenoising

        scene.eevee.use_gtao = self.ao
        scene.eevee.gtao_distance = self.distance
        scene.eevee.gtao_factor = self.factor
        scene.eevee.gtao_quality = self.tracePrecission
        scene.eevee.use_gtao_bent_normals = self.bentNormals
        scene.eevee.use_gtao_bounce = self.bouncesApproximation

        scene.eevee.use_bloom = self.bloom
        scene.eevee.bloom_threshold = self.bloom_threshold
        scene.eevee.bloom_knee = self.bloom_knee
        scene.eevee.bloom_radius = self.bloom_radius
        scene.eevee.bloom_color = self.bloom_color
        scene.eevee.bloom_intensity = self.bloom_intensity
        scene.eevee.bloom_clamp = self.bloom_clamp

        scene.eevee.bokeh_max_size = self.dof_maxSize
        scene.eevee.bokeh_threshold = self.dof_spirteThreshold
        scene.eevee.bokeh_neighbor_max = self.dof_neighbourRejection
        scene.eevee.bokeh_denoise_fac = self.dof_denoiseAmount
        scene.eevee.use_bokeh_high_quality_slight_defocus = self.dof_highQualitySlightDefocus
        scene.eevee.use_bokeh_jittered = self.dof_jitterCamera
        scene.eevee.bokeh_overblur = self.dof_overBlur

        scene.eevee.sss_samples = self.sss_samples
        scene.eevee.sss_jitter_threshold = self.sss_jitterThreshold

        scene.eevee.use_ssr = self.ssr_enable
        scene.eevee.use_ssr_refraction = self.ssr_Refraction
        scene.eevee.use_ssr_halfres = self.ssr_halfResTrace
        scene.eevee.ssr_quality = self.ssr_tracePrecission
        scene.eevee.ssr_max_roughness = self.ssr_maxRoughness
        scene.eevee.ssr_thickness = self.ssr_Thickness
        scene.eevee.ssr_border_fade = self.ssr_edgeFading
        scene.eevee.ssr_firefly_fac = self.ssr_clamp

        scene.eevee.use_motion_blur = self.mb_enable
        scene.eevee.motion_blur_position = self.mb_position
        scene.eevee.motion_blur_shutter = self.mb_shutter
        scene.eevee.motion_blur_depth_scale = self.mb_backgroundSeparation
        scene.eevee.motion_blur_max = self.mb_maxBlur
        scene.eevee.motion_blur_steps = self.mb_steps

        scene.eevee.volumetric_start = self.vol_start
        scene.eevee.volumetric_end = self.vol_end
        scene.eevee.volumetric_tile_size = self.vol_tile_size
        scene.eevee.volumetric_samples = self.vol_samples
        scene.eevee.volumetric_sample_distribution = self.vol_distribution
        scene.eevee.use_volumetric_lights = self.vol_lighting
        scene.eevee.volumetric_light_clamp = self.vol_light_clamp
        scene.eevee.use_volumetric_shadows = self.vol_shadow
        scene.eevee.volumetric_shadow_samples = self.vol_shadow_samples

        scene.render.use_high_quality_normals = self.performance_highQualNormals

        scene.render.hair_type = self.curves_shape
        scene.render.hair_subdiv = self.curves_additionalSubdivision

        scene.eevee.shadow_cube_size = self.shadows_cubeSize
        scene.eevee.shadow_cascade_size = self.shadows_cascadeSize
        scene.eevee.use_shadow_high_bitdepth = self.shadow_highBitDepth
        scene.eevee.use_soft_shadows = self.shadow_softShadows
        scene.eevee.light_threshold = self.shadow_lightThreshold

        scene.render.filter_size = self.film_filterSize
        scene.render.film_transparent = self.film_transparent
        scene.eevee.use_overscan = self.film_overscan
        scene.eevee.overscan_size = self.film_overScanAmount

        scene.render.use_simplify = self.simplify_enable
        scene.render.simplify_subdivision = self.simplify_max_subdivision
        scene.render.simplify_child_particles = self.simplify_max_child_particles
        scene.render.simplify_volumes = self.simplify_volume_resolution
        scene.render.simplify_shadows = self.simplify_shadow_resolution
        scene.render.use_simplify_normals = self.simplify_normals
        scene.render.simplify_subdivision_render = self.simplify_render_max_subdivision
        scene.render.simplify_child_particles_render = self.simplify_render_max_child_particles
        scene.render.simplify_shadows_render = self.simplify_render_shadow_resolution

class NODE_OT_AddEeveeGlobalSettings(bpy.types.Operator):
    """
    Add a Render Layer to the Custom Node Tree
    """
    bl_idname = "node.add_eevee_global_settings_node"
    bl_label = "Add Eevee Global Settings Node"
    nodeType = "RenderingLightingEeveeGlobalSettings"
    
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