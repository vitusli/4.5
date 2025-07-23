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


class RenderingLightingSceneInput(bpy.types.Node):
    """
    A node for bringing in the blender scene
    """
    bl_idname = "RenderingLightingSceneInput"
    bl_label = "SceneInput"
    bl_icon = "MOD_DECIM"

    def init(self, context):
        """
        Initialize node sockets
        """
        self.width = 200
        self.collection = None
        self.inputs.new("NodeSocketCollection", "SceneInput")
        self.outputs.new("NodeSocketCollection", "SceneInput")
        bpy.data.scenes["Scene"].render.engine = "CYCLES"
        bpy.data.scenes["Scene"].render.image_settings.file_format = "OPEN_EXR_MULTILAYER"

    def draw_buttons(self, context, layout):
        """
        Draw the node layout and place sockets
        """
        layout.operator("node.cook_scene_from_node", text = "Cook Scene", icon="FILE_REFRESH")

    def executeNodeCookFunctions(self):
        """
        The function the cook Scene Button calls from utilFunctions
        """
        utilityFunctions.setViewedNode(self)
        self.update()
        self.setDefaultAttributes()

    def update(self):
        """
        This is where the node processing would happen
        """
        self.collection = self.inputs[0].default_value

    def setDefaultAttributes(self):
        scene = bpy.context.scene
        viewLayer =bpy.context.view_layer

        if not self.collection:
            print("No scene Collection set")
            return

        # Default objectSettings
        sceneMeshes = utilityFunctions.searchSceneObjectsRecursive("*", self.collection)
        for mesh in sceneMeshes:
            mesh.hide_viewport = False
            mesh.hide_render = False
            mesh.is_shadow_catcher = False
            mesh.is_holdout = False

            mesh.visible_camera = True
            mesh.visible_diffuse = True
            mesh.visible_glossy = True
            mesh.visible_transmission = True
            mesh.visible_volume_scatter = True
            mesh.visible_shadow = True

        # Default Light groups
        sceneLights = utilityFunctions.searchSceneObjectsRecursive("* AND type=='LIGHT'", self.collection)
        for light in sceneLights:
            light.lightgroup = ""
        
        bpy.ops.scene.view_layer_remove_unused_lightgroups()

        # Default AOVS
        viewLayer.use_pass_combined = False
        viewLayer.use_pass_z = False
        viewLayer.use_pass_mist = False
        viewLayer.use_pass_position = False
        viewLayer.use_pass_normal = False
        viewLayer.use_pass_vector = False
        viewLayer.use_pass_uv = False
        viewLayer.use_pass_object_index = False
        viewLayer.use_pass_material_index = False

        viewLayer.use_pass_diffuse_direct = False
        viewLayer.use_pass_diffuse_indirect = False
        viewLayer.use_pass_diffuse_color = False
        viewLayer.use_pass_glossy_direct = False
        viewLayer.use_pass_glossy_indirect = False
        viewLayer.use_pass_glossy_color = False
        viewLayer.use_pass_transmission_direct = False
        viewLayer.use_pass_transmission_indirect = False
        viewLayer.use_pass_transmission_color = False
        viewLayer.cycles.use_pass_volume_direct = False
        viewLayer.cycles.use_pass_volume_indirect = False
        viewLayer.use_pass_emit = False
        viewLayer.use_pass_environment = False
        viewLayer.use_pass_ambient_occlusion = False
        viewLayer.cycles.use_pass_shadow_catcher = False

        viewLayer.use_pass_cryptomatte_object = False
        viewLayer.use_pass_cryptomatte_material = False
        viewLayer.use_pass_cryptomatte_asset = False

        # Default Global Settings
        scene.cycles.adaptive_threshold = 0.05
        scene.cycles.samples = 1024
        scene.cycles.adaptive_min_samples = 0
        
        scene.cycles.time_limit = 0

        scene.cycles.use_light_tree = True

        scene.cycles.max_bounces = 12
        scene.cycles.diffuse_bounces = 4
        scene.cycles.glossy_bounces = 4
        scene.cycles.transmission_bounces = 12
        scene.cycles.volume_bounces = 0
        scene.cycles.transparent_max_bounces = 8

        scene.cycles.sample_clamp_direct = 0.0
        scene.cycles.sample_clamp_indirect = 10.00

        scene.cycles.blur_glossy = 1.00
        scene.cycles.caustics_reflective = True
        scene.cycles.caustics_refractive = True

        scene.cycles.use_fast_gi = False
        scene.cycles.fast_gi_method = "REPLACE"

        scene.cycles.volume_step_rate = 1.0
        scene.render.use_motion_blur = True
        scene.render.film_transparent = True
        scene.cycles.film_transparent_glass = True

        # Default Render Settings
        scene.render.resolution_x = 1920
        scene.render.resolution_y = 1080
        scene.render.resolution_percentage = 100
        scene.camera = None
        scene.render.use_compositing = False
        scene.render.use_sequencer =False

        #Default denoise settings
        scene.cycles.use_denoising = False
        scene.cycles.denoiser = "OPENIMAGEDENOISE"
        scene.cycles.denoising_input_paths = "ALBEDO_NORMAL"
        bpy.context.view_layer.cycles.denoising_store_passes = False

        # Eevee renderDefaults
        scene.eevee.taa_render_samples =64
        scene.eevee.taa_samples = 16
        scene.eevee.use_taa_reprojection = True

        scene.eevee.use_gtao = False
        scene.eevee.gtao_distance = 0.2
        scene.eevee.gtao_factor = 1.0
        scene.eevee.gtao_quality = 0.25
        scene.eevee.use_gtao_bent_normals = True
        scene.eevee.use_gtao_bounce = True

        scene.eevee.use_bloom = False
        scene.eevee.bloom_threshold = .8
        scene.eevee.bloom_knee = 0.5
        scene.eevee.bloom_radius = 6.5
        scene.eevee.bloom_color = (1.0, 1.0, 1.0)
        scene.eevee.bloom_intensity = .050
        scene.eevee.bloom_clamp = 0.0

        scene.eevee.bokeh_max_size = 100
        scene.eevee.bokeh_threshold = 1.0
        scene.eevee.bokeh_neighbor_max = 10.0
        scene.eevee.bokeh_denoise_fac = .75
        scene.eevee.use_bokeh_high_quality_slight_defocus = False
        scene.eevee.use_bokeh_jittered = False
        scene.eevee.bokeh_overblur = 5.0

        scene.eevee.sss_samples = 7
        scene.eevee.sss_jitter_threshold = 0.3

        scene.eevee.use_ssr = False
        scene.eevee.use_ssr_refraction = False
        scene.eevee.use_ssr_halfres = False
        scene.eevee.ssr_quality = 0.250
        scene.eevee.ssr_max_roughness = 0.5
        scene.eevee.ssr_thickness = 0.2
        scene.eevee.ssr_border_fade = 0.075
        scene.eevee.ssr_firefly_fac = 10.0

        scene.eevee.use_motion_blur = False
        scene.eevee.motion_blur_position = "CENTER"
        scene.eevee.motion_blur_shutter = 0.5
        scene.eevee.motion_blur_depth_scale = 100.0
        scene.eevee.motion_blur_max = 32
        scene.eevee.motion_blur_steps = 16

        scene.eevee.volumetric_start = 0.0
        scene.eevee.volumetric_end = 100
        scene.eevee.volumetric_tile_size = "8"
        scene.eevee.volumetric_samples = 64
        scene.eevee.volumetric_sample_distribution = 0.8
        scene.eevee.use_volumetric_lights = True
        scene.eevee.volumetric_light_clamp = 10.0
        scene.eevee.use_volumetric_shadows = False
        scene.eevee.volumetric_shadow_samples = 16

        scene.render.use_high_quality_normals = False

        scene.render.hair_type = "STRAND"
        scene.render.hair_subdiv = 0

        scene.eevee.shadow_cube_size = '512'
        scene.eevee.shadow_cascade_size = '1024'
        scene.eevee.use_shadow_high_bitdepth = False
        scene.eevee.use_soft_shadows = True
        scene.eevee.light_threshold = 0.01

        scene.render.filter_size = 1.50
        scene.render.film_transparent = True
        scene.eevee.use_overscan = False
        scene.eevee.overscan_size = 3.00

        scene.render.use_simplify = False
        scene.render.simplify_subdivision = 6
        scene.render.simplify_child_particles = 1.0
        scene.render.simplify_volumes = 1.0
        scene.render.simplify_shadows = 1.0
        scene.render.use_simplify_normals = False
        scene.render.simplify_subdivision_render = 6
        scene.render.simplify_child_particles_render = 1.0
        scene.render.simplify_shadows_render = 1.0

    def getOutputScene(self):
        self.update()
        return self.collection


class NODE_OT_AddSceneInput(bpy.types.Operator):
    """
    Add a Render Layer to the Custom Node Tree
    """
    bl_idname = "node.add_sceneinput_node"
    bl_label = "Add Scene Input Node"
    nodeType = "RenderingLightingSceneInput"

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