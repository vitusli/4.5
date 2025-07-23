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


class RenderingLightingCyclesAovSelection(bpy.types.Node):
    """
    A node for setting renderable AOVs 
    """
    bl_idname = "RenderingLightingCyclesAovSelection"
    bl_label = "CyclesAovSelection"
    bl_icon = "MOD_DECIM"

    combined: bpy.props.BoolProperty(
        name="Combined",
        description="Enable the bty AOV",
        default=False,
        update=lambda self, context: self.executeViewportCook()
    )

    z: bpy.props.BoolProperty(
        name="Z",
        description="Enable the z AOV",
        default=False,
        update=lambda self, context: self.executeViewportCook()
    )

    mist: bpy.props.BoolProperty(
        name="Mist",
        description="Enable the Mist AOV",
        default=False,
        update=lambda self, context: self.executeViewportCook()
    )

    position: bpy.props.BoolProperty(
        name="Position",
        description="Enable the Position AOV",
        default=False,
        update=lambda self, context: self.executeViewportCook()
    )

    normal: bpy.props.BoolProperty(
        name="Normal",
        description="Enable the Normal AOV",
        default=False,
        update=lambda self, context: self.executeViewportCook()
    )

    vector: bpy.props.BoolProperty(
        name="Vector",
        description="Enable the Vector AOV",
        default=False,
        update=lambda self, context: self.executeViewportCook()
    )

    uv: bpy.props.BoolProperty(
        name="UV",
        description="Enable the UV AOV",
        default=False,
        update=lambda self, context: self.executeViewportCook()
    )

    objectIndex: bpy.props.BoolProperty(
        name="Object Index",
        description="Enable the Object Index AOV",
        default=False,
        update=lambda self, context: self.executeViewportCook()
    )

    materialIndex: bpy.props.BoolProperty(
        name="Material Index",
        description="Enable the Material Index AOV",
        default=False,
        update=lambda self, context: self.executeViewportCook()
    )

    diffuseDirect: bpy.props.BoolProperty(
        name="Diffuse Direct",
        description="Enable the Diffuse Direct AOV",
        default=False,
        update=lambda self, context: self.executeViewportCook()
    )

    diffuseInDirect: bpy.props.BoolProperty(
        name="Diffuse Indirect",
        description="Enable the Diffuse Indirect AOV",
        default=False,
        update=lambda self, context: self.executeViewportCook()
    )

    diffuseAlbedo: bpy.props.BoolProperty(
        name="Diffuse Albedo",
        description="Enable the Diffuse Albedo AOV",
        default=False,
        update=lambda self, context: self.executeViewportCook()
    )

    specularDirect: bpy.props.BoolProperty(
        name="Specular Direct",
        description="Enable the Specular Direct AOV",
        default=False,
        update=lambda self, context: self.executeViewportCook()
    )

    specularInDirect: bpy.props.BoolProperty(
        name="Specular Indirect",
        description="Enable the Specular Indirect AOV",
        default=False,
        update=lambda self, context: self.executeViewportCook()
    )

    specularAlbedo: bpy.props.BoolProperty(
        name="Specular Albedo",
        description="Enable the Specular Albedo AOV",
        default=False,
        update=lambda self, context: self.executeViewportCook()
    )

    transmissionDirect: bpy.props.BoolProperty(
        name="Transmission Direct",
        description="Enable the Transmission Direct AOV",
        default=False,
        update=lambda self, context: self.executeViewportCook()
    )

    transmissionInDirect: bpy.props.BoolProperty(
        name="Transmission Indirect",
        description="Enable the Transmission Indirect AOV",
        default=False,
        update=lambda self, context: self.executeViewportCook()
    )

    transmissionAlbedo: bpy.props.BoolProperty(
        name="Transmission Albedo",
        description="Enable the Transmission Albedo AOV",
        default=False,
        update=lambda self, context: self.executeViewportCook()
    )

    volumeDirect: bpy.props.BoolProperty(
        name="Volume Direct",
        description="Enable the Volume Direct AOV",
        default=False,
        update=lambda self, context: self.executeViewportCook()
    )

    volumeIndirect: bpy.props.BoolProperty(
        name="Volume Indirect",
        description="Enable the Volume Indirect AOV",
        default=False,
        update=lambda self, context: self.executeViewportCook()
    )

    emission: bpy.props.BoolProperty(
        name="Emission",
        description="Enable the Emission AOV",
        default=False,
        update=lambda self, context: self.executeViewportCook()
    )

    environment: bpy.props.BoolProperty(
        name="Environment",
        description="Enable the Environment AOV",
        default=False,
        update=lambda self, context: self.executeViewportCook()
    )

    ambientOcclusion: bpy.props.BoolProperty(
        name="Ambient Occlusion",
        description="Enable the Ambient Occlusion AOV",
        default=False,
        update=lambda self, context: self.executeViewportCook()
    )

    shadowCatcher: bpy.props.BoolProperty(
        name="Shadow Catcher",
        description="Enable the Shadow Catcher AOV",
        default=False,
        update=lambda self, context: self.executeViewportCook()
    )

    object: bpy.props.BoolProperty(
        name="Object",
        description="Enable the Object AOV",
        default=False,
        update=lambda self, context: self.executeViewportCook()
    )

    material: bpy.props.BoolProperty(
        name="Material",
        description="Enable the Material AOV",
        default=False,
        update=lambda self, context: self.executeViewportCook()
    )

    asset: bpy.props.BoolProperty(
        name="Asset",
        description="Enable the Asset AOV",
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
        layout.label(text="Data AOVs")
        layout.prop(self, "combined", text="Combined")
        layout.prop(self, "z", text="Z")
        layout.prop(self, "mist", text="Mist")
        layout.prop(self, "position", text="Position")
        layout.prop(self, "normal", text="Normal")
        layout.prop(self, "vector", text="Vector")
        layout.prop(self, "uv", text="UV")
        layout.prop(self, "objectIndex", text="Object Index")
        layout.prop(self, "materialIndex", text="Material Index")

        layout.separator()
        layout.label(text="Light AOVs")
        layout.prop(self, "diffuseDirect", text="Diffuse Direct")
        layout.prop(self, "diffuseInDirect", text="Diffuse InDirect")
        layout.prop(self, "diffuseAlbedo", text="Diffuse Albedo")
        layout.prop(self, "specularDirect", text="Specular Direct")
        layout.prop(self, "specularInDirect", text="Specular InDirect")
        layout.prop(self, "specularAlbedo", text="Specular Albedo")
        layout.prop(self, "transmissionDirect", text="Transmission Direct")
        layout.prop(self, "transmissionInDirect", text="Transmission Indirect")
        layout.prop(self, "transmissionAlbedo", text="Transmission Albedo")
        layout.prop(self, "volumeDirect", text="Volume Direct")
        layout.prop(self, "volumeIndirect", text="Volume Indirect")
        layout.prop(self, "emission", text="Emission")
        layout.prop(self, "environment", text="Environment")
        layout.prop(self, "ambientOcclusion", text="Ambient Occlusion")
        layout.prop(self, "shadowCatcher", text="Shadow Catcher")

        layout.separator()
        layout.label(text="Crypto")
        layout.prop(self, "object", text="Object")
        layout.prop(self, "material", text="Material")
        layout.prop(self, "asset", text="Asset")

        # Cook node Button
        layout.operator("node.cook_scene_from_node", text = "Cook Scene", icon="FILE_REFRESH")

    def executeNodeCookFunctions(self):
        utilityFunctions.setViewedNode(self)
        self.updateLayerAttributes()

    def executeViewportCook(self):
        viewedNode = utilityFunctions.getViewedNode()
        if self != viewedNode:
            return

        self.executeNodeCookFunctions()

    def updateLayerAttributes(self):
        viewLayer = bpy.context.view_layer

        bpy.context.view_layer.use_pass_combined = self.combined
        bpy.context.view_layer.use_pass_z = self.z
        bpy.context.view_layer.use_pass_mist = self.mist
        bpy.context.view_layer.use_pass_position = self.position
        bpy.context.view_layer.use_pass_normal = self.normal
        bpy.context.view_layer.use_pass_vector = self.vector
        bpy.context.view_layer.use_pass_uv = self.uv
        bpy.context.view_layer.use_pass_object_index = self.objectIndex
        bpy.context.view_layer.use_pass_material_index = self.materialIndex

        bpy.context.view_layer.use_pass_diffuse_direct = self.diffuseDirect
        bpy.context.view_layer.use_pass_diffuse_indirect = self.diffuseInDirect
        bpy.context.view_layer.use_pass_diffuse_color = self.diffuseAlbedo
        bpy.context.view_layer.use_pass_glossy_direct = self.specularDirect
        bpy.context.view_layer.use_pass_glossy_indirect = self.specularInDirect
        bpy.context.view_layer.use_pass_glossy_color = self.specularAlbedo
        bpy.context.view_layer.use_pass_transmission_direct = self.transmissionDirect
        bpy.context.view_layer.use_pass_transmission_indirect = self.transmissionInDirect
        bpy.context.view_layer.use_pass_transmission_color = self.transmissionAlbedo
        bpy.context.view_layer.cycles.use_pass_volume_direct = self.volumeDirect
        bpy.context.view_layer.cycles.use_pass_volume_indirect = self.volumeIndirect
        bpy.context.view_layer.use_pass_emit = self.emission
        bpy.context.view_layer.use_pass_environment = self.environment
        bpy.context.view_layer.use_pass_ambient_occlusion = self.ambientOcclusion
        bpy.context.view_layer.cycles.use_pass_shadow_catcher = self.shadowCatcher

        bpy.context.view_layer.use_pass_cryptomatte_object = self.object
        bpy.context.view_layer.use_pass_cryptomatte_material = self.material
        bpy.context.view_layer.use_pass_cryptomatte_asset = self.asset
        

class NODE_OT_AddAovSelection(bpy.types.Operator):
    """
    Add a Render Layer to the Custom Node Tree
    """
    bl_idname = "node.add_aov_selection_node"
    bl_label = "Add AOV Selection Node"
    nodeType = "RenderingLightingCyclesAovSelection"
    
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