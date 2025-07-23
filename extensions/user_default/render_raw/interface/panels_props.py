'''
Copyright (C) 2024 Orange Turbine
https://orangeturbine.com
orangeturbine@cgcookie.com

This file is part of the Render Raw add-on, created by Jonathan Lampel for Orange Turbine.

All code distributed with this add-on is open source as described below.

Render Raw is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 3
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, see <https://www.gnu.org/licenses/>.
'''

import bpy
import time
from ..utilities.nodes import is_RR_node
from ..utilities.settings import get_settings
from ..preferences import get_prefs
from .headers_props import (
    draw_layers_header, draw_layers_header_preset,
    draw_values_header, draw_values_header_preset,
    draw_colors_header, draw_colors_header_preset,
    draw_effects_header, draw_effects_header_preset
)
from .draw_props import (
    draw_color_management,
    draw_layers,
    draw_values,
    draw_colors,
    draw_effects,
    draw_utilities,
)


''' Properties Editor Color Management Panels '''


class RenderRawPanel(bpy.types.Panel):
    bl_idname = "RENDER_PT_render_raw"
    bl_label = "Color Management"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'render'

    def draw(self, context):
        col = self.layout.column()
        col.use_property_split = True
        col.use_property_decorate = False
        col.prop(context.scene.display_settings, 'display_device')
        col.prop(context.scene.sequencer_colorspace_settings, 'name', text='Sequencer')
        col.separator()
        draw_color_management(self, context, get_settings(context))


class LayersPanel(bpy.types.Panel):
    bl_idname = "RENDER_PT_render_raw_layers"
    bl_parent_id = "RENDER_PT_render_raw"
    bl_label = "Layers"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'render'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(self, context):
        RR = get_settings(context)
        PREFS = get_prefs(context)
        return RR.enabled and PREFS.enable_layers and RR.in_scene and not RR.is_legacy

    def draw_header(self, context):
        draw_layers_header(self, context, get_settings(context))

    def draw_header_preset(self, context):
        draw_layers_header_preset(self, context, get_settings(context))

    def draw(self, context):
        draw_layers(self, get_settings(context))


class ValuesPanel(bpy.types.Panel):
    bl_idname = "RENDER_PT_render_raw_values"
    bl_parent_id = "RENDER_PT_render_raw"
    bl_label = "Values"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'render'

    @classmethod
    def poll(self, context):
        try:
            RR = get_settings(context)
            return RR.enabled and RR.nodes_pre and RR.nodes_post and RR.in_scene and not RR.is_legacy 
        except:
            return False

    def draw_header(self, context):
        draw_values_header(self, context, get_settings(context))

    def draw_header_preset(self, context):
        draw_values_header_preset(self, context, get_settings(context))

    def draw(self, context):
        draw_values(self, context, get_settings(context))


class ColorsPanel(bpy.types.Panel):
    bl_idname = "RENDER_PT_render_raw_colors"
    bl_parent_id = "RENDER_PT_render_raw"
    bl_label = "Colors"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'render'
    # bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(self, context):
        try:
            RR = get_settings(context)
            return RR.enabled and RR.in_scene and RR.nodes_pre and RR.nodes_post and not RR.is_legacy 
        except:
            return False

    def draw_header(self, context):
        draw_colors_header(self, context, get_settings(context))

    def draw_header_preset(self, context):
        draw_colors_header_preset(self, context, get_settings(context))

    def draw(self, context):
        draw_colors(self, get_settings(context))


class EffectsPanel(bpy.types.Panel):
    bl_idname = "RENDER_PT_render_raw_effects"
    bl_parent_id = "RENDER_PT_render_raw"
    bl_label = "Effects"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'render'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(self, context):
        try:
            RR = get_settings(context)
            return RR.enabled and RR.in_scene and RR.nodes_pre and RR.nodes_post and not RR.is_legacy 
        except:
            return False

    def draw_header(self, context):
        draw_effects_header(self, context, get_settings(context))

    def draw_header_preset(self, context):
        draw_effects_header_preset(self, context, get_settings(context))

    def draw(self, context):
        draw_effects(self, get_settings(context))


class UtilitiesPanel(bpy.types.Panel):
    bl_idname = "RENDER_PT_render_raw_utilities"
    bl_parent_id = "RENDER_PT_render_raw"
    bl_label = ""
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'render'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(self, context):
        try:
            RR = get_settings(context)
            return RR.enabled and RR.in_scene and RR.nodes_pre and RR.nodes_post and not RR.is_legacy 
        except:
            return False

    def draw_header(self, context):
        self.layout.label(text="Utilities")

    def draw(self, context):
        draw_utilities(self, context, get_settings(context))


''' 3D View Sidebar Panels '''


class RenderRawPanel3DView(bpy.types.Panel):
    bl_label = "Color Management"
    bl_idname = 'RENDER_PT_render_raw_color_management_3d_view'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Render'

    @classmethod
    def poll(self, context):
        PREFS = get_prefs(context)
        return PREFS.enable_3d_view_sidebar

    def draw(self, context):
        draw_color_management(self, context, get_settings(context))


class LayersPanel3DView(bpy.types.Panel):
    bl_label = "Layers"
    bl_idname = 'RENDER_PT_render_raw_layers_3d_view'
    bl_parent_id = "RENDER_PT_render_raw_color_management_3d_view"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Render'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(self, context):
        try:
            RR = get_settings(context)
            PREFS = get_prefs(context)
            return (
                RR.enabled and
                RR.in_scene and 
                not RR.is_legacy and
                PREFS.enable_layers and
                PREFS.enable_3d_view_sidebar
            )
        except:
            return False

    def draw_header(self, context):
        draw_layers_header(self, context, get_settings(context))

    def draw_header_preset(self, context):
        draw_layers_header_preset(self, context, get_settings(context))

    def draw(self, context):
        draw_layers(self, get_settings(context))


class ValuesPanel3DView(bpy.types.Panel):
    bl_label = "Values"
    bl_idname = 'RENDER_PT_render_raw_values_3d_view'
    bl_parent_id = "RENDER_PT_render_raw_color_management_3d_view"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Render'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(self, context):
        try:
            RR = get_settings(context)
            PREFS = get_prefs(context)
            return (
                RR.enabled and
                RR.in_scene and 
                PREFS.enable_3d_view_sidebar and
                RR.nodes_pre and RR.nodes_post and 
                not RR.is_legacy 
            )
        except:
            return False

    def draw_header(self, context):
        draw_values_header(self, context, get_settings(context))

    def draw_header_preset(self, context):
        draw_values_header_preset(self, context, get_settings(context))

    def draw(self, context):
        draw_values(self, context, get_settings(context))


class ColorsPanel3DView(bpy.types.Panel):
    bl_label = "Colors"
    bl_idname = 'RENDER_PT_render_raw_colors_3d_view'
    bl_parent_id = "RENDER_PT_render_raw_color_management_3d_view"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Render'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(self, context):
        try:
            RR = get_settings(context)
            PREFS = get_prefs(context)
            return (
                RR.enabled and
                RR.in_scene and 
                PREFS.enable_3d_view_sidebar and
                RR.nodes_pre and RR.nodes_post and 
                not RR.is_legacy 
            )
        except:
            return False

    def draw_header(self, context):
        draw_colors_header(self, context, get_settings(context))

    def draw_header_preset(self, context):
        draw_colors_header_preset(self, context, get_settings(context))

    def draw(self, context):
        draw_colors(self, get_settings(context))


class EffectsPanel3DView(bpy.types.Panel):
    bl_idname = "RENDER_PT_render_raw_effects_3d_view"
    bl_parent_id = "RENDER_PT_render_raw_color_management_3d_view"
    bl_label = "Effects"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Render'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(self, context):
        try:
            RR = get_settings(context)
            PREFS = get_prefs(context)
            return (
                RR.enabled and
                RR.in_scene and 
                PREFS.enable_3d_view_sidebar and
                RR.nodes_pre and RR.nodes_post and 
                not RR.is_legacy 
            )
        except:
            return False

    def draw_header(self, context):
        draw_effects_header(self, context, get_settings(context))

    def draw_header_preset(self, context):
        draw_effects_header_preset(self, context, get_settings(context))

    def draw(self, context):
        draw_effects(self, get_settings(context))


class UtilitiesPanel3DView(bpy.types.Panel):
    bl_idname = "RENDER_PT_render_raw_utilities_3d_view"
    bl_parent_id = "RENDER_PT_render_raw_color_management_3d_view"
    bl_label = "Utilities"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Render'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(self, context):
        try:
            RR = get_settings(context)
            PREFS = get_prefs(context)
            return (
                RR.enabled and
                RR.in_scene and 
                PREFS.enable_3d_view_sidebar and
                RR.nodes_pre and RR.nodes_post and 
                not RR.is_legacy 
            )
        except:
            return False

    def draw(self, context):
        draw_utilities(self, context, get_settings(context))


''' Node Editor Panels '''


class RenderRawPanelNode(bpy.types.Panel):
    bl_label = "Render Raw"
    bl_idname = 'RENDER_PT_render_raw_color_management_node'
    bl_parent_id = "NODE_PT_active_node_properties"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        draw_color_management(self, context, get_settings(context))


class LayersPanelNode(bpy.types.Panel):
    bl_label = "Layers"
    bl_idname = 'NODE_PT_render_raw_layers_node'
    bl_parent_id = "NODE_PT_active_node_properties"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(self, context):
        try:
            RR = get_settings(context)
            PREFS = get_prefs(context)
            return (
                RR.enabled and
                not RR.is_legacy and
                PREFS.enable_layers and
                is_RR_node(context.scene.node_tree.nodes.active)
            )
        except:
            return False

    def draw_header(self, context):
        draw_layers_header(self, context, get_settings(context))

    def draw_header_preset(self, context):
        draw_layers_header_preset(self, context, get_settings(context))

    def draw(self, context):
        draw_layers(self, get_settings(context))


class ValuesPanelNode(bpy.types.Panel):
    bl_label = "Values"
    bl_idname = 'NODE_PT_render_raw_values_node'
    bl_parent_id = "NODE_PT_active_node_properties"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(self, context):
        try:
            RR = get_settings(context)
            return (
                RR.enabled and
                RR.nodes_pre and RR.nodes_post and
                is_RR_node(context.scene.node_tree.nodes.active) and 
                not RR.is_legacy 
            )
        except:
            return False

    def draw_header(self, context):
        draw_values_header(self, context, get_settings(context))

    def draw_header_preset(self, context):
        draw_values_header_preset(self, context, get_settings(context))

    def draw(self, context):
        draw_values(self, context, get_settings(context))


class ColorPanelNode(bpy.types.Panel):
    bl_label = "Colors"
    bl_idname = 'NODE_PT_render_raw_colors_node'
    bl_parent_id = "NODE_PT_active_node_properties"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(self, context):
        try:
            RR = get_settings(context)
            return (
                RR.enabled and
                RR.nodes_pre and RR.nodes_post and
                is_RR_node(context.scene.node_tree.nodes.active) and 
                not RR.is_legacy 
            )
        except:
            return False

    def draw_header(self, context):
        draw_colors_header(self, context, get_settings(context))

    def draw_header_preset(self, context):
        draw_colors_header_preset(self, context, get_settings(context))

    def draw(self, context):
        draw_colors(self, get_settings(context))


class EffectsPanelNode(bpy.types.Panel):
    bl_label = "Effects"
    bl_idname = 'NODE_PT_render_raw_effects_node'
    bl_parent_id = "NODE_PT_active_node_properties"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(self, context):
        try:
            RR = get_settings(context)
            return (
                RR.enabled and
                RR.nodes_pre and RR.nodes_post and
                is_RR_node(context.scene.node_tree.nodes.active) and 
                not RR.is_legacy 
            )
        except:
            return False

    def draw_header(self, context):
        draw_effects_header(self, context, get_settings(context))

    def draw_header_preset(self, context):
        draw_effects_header_preset(self, context, get_settings(context))

    def draw(self, context):
        draw_effects(self, get_settings(context))


class UtilitiesPanelNode(bpy.types.Panel):
    bl_idname = "RENDER_PT_render_raw_utilities_node"
    bl_parent_id = "NODE_PT_active_node_properties"
    bl_label = "Utilities"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(self, context):
        try:
            RR = get_settings(context)
            return (
                RR.enabled and
                RR.nodes_pre and RR.nodes_post and
                is_RR_node(context.scene.node_tree.nodes.active) and 
                not RR.is_legacy 
            )
        except:
            return False

    def draw(self, context):
        draw_utilities(self, context, get_settings(context))


''' Image Editor Panels '''
# TODO


viewport_panels = [
    RenderRawPanel3DView,
    LayersPanel3DView,
    ValuesPanel3DView,
    ColorsPanel3DView,
    EffectsPanel3DView,
    UtilitiesPanel3DView,
]

classes = [
    RenderRawPanel,
    LayersPanel,
    ValuesPanel,
    ColorsPanel,
    EffectsPanel,
    UtilitiesPanel,

    RenderRawPanel3DView,
    LayersPanel3DView,
    ValuesPanel3DView,
    ColorsPanel3DView,
    EffectsPanel3DView,
    UtilitiesPanel3DView,


    RenderRawPanelNode,
    LayersPanelNode,
    ValuesPanelNode,
    ColorPanelNode,
    EffectsPanelNode,
    UtilitiesPanelNode,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    if hasattr(bpy.types, 'RENDER_PT_color_management'):
        bpy.utils.unregister_class(bpy.types.RENDER_PT_color_management)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
