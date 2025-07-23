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



'''
These panels mimic the originals and are drawn when Render Raw is enabled as an add-on 
but not enabled in the UI. 
'''


from .draw_originals import (
    draw_original_curves,
    draw_original_display,
    draw_original_white_balance
)

class OriginalCurvePanel(bpy.types.Panel):
    bl_label = "Use Curves"
    bl_idname = 'RENDER_PT_render_raw_original_curves'
    bl_parent_id = "RENDER_PT_render_raw"
    bl_options = {'DEFAULT_CLOSED'}
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    COMPAT_ENGINES = {
        'BLENDER_RENDER',
        'BLENDER_EEVEE',
        'BLENDER_EEVEE_NEXT',
        'BLENDER_WORKBENCH',
    }

    @classmethod
    def poll(self, context):
        return not context.scene.render_raw_scene.enable_RR

    def draw_header(self, context):
        scene = context.scene
        view = scene.view_settings
        self.layout.prop(view, "use_curve_mapping", text="")

    def draw(self, context):
        draw_original_curves(self, context)

class OriginalDisplayPanel(bpy.types.Panel):
    bl_label = "Display"
    bl_idname = 'RENDER_PT_render_raw_original_display'
    bl_parent_id = "RENDER_PT_render_raw"
    bl_options = {'DEFAULT_CLOSED'}
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    COMPAT_ENGINES = {
        'BLENDER_RENDER',
        'BLENDER_EEVEE',
        'BLENDER_EEVEE_NEXT',
        'BLENDER_WORKBENCH',
    }

    @classmethod
    def poll(self, context):
        return not context.scene.render_raw_scene.enable_RR

    def draw(self, context):
        draw_original_display(self, context)

class OriginalWhiteBalancePanel(bpy.types.Panel):
    bl_label = "White Balance"
    bl_idname = 'RENDER_PT_render_raw_original_white_balance'
    bl_parent_id = "RENDER_PT_render_raw"
    bl_options = {'DEFAULT_CLOSED'}
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    COMPAT_ENGINES = {
        'BLENDER_RENDER',
        'BLENDER_EEVEE',
        'BLENDER_EEVEE_NEXT',
        'BLENDER_WORKBENCH',
    }

    @classmethod
    def poll(self, context):
        return not context.scene.render_raw_scene.enable_RR and bpy.app.version >= (4, 3, 0)

    def draw_header(self, context):
        self.layout.prop(context.scene.view_settings, "use_white_balance", text="")

    def draw_header_preset(self, context):
        layout = self.layout

        bpy.types.RENDER_PT_color_management_white_balance_presets.draw_panel_header(layout)

        eye = layout.operator("ui.eyedropper_color", text="", icon='EYEDROPPER')
        eye.prop_data_path = "scene.view_settings.white_balance_whitepoint"

    def draw(self, context):
        draw_original_white_balance(self, context)


''' 3D View Sidebar Panels '''


class OriginalCurvePanel3DView(bpy.types.Panel):
    bl_label = "Use Curves"
    bl_idname = 'RENDER_PT_render_raw_original_curves_3d_view'
    bl_parent_id = "RENDER_PT_render_raw_color_management_3d_view"
    bl_options = {'DEFAULT_CLOSED'}
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Render'
    COMPAT_ENGINES = {
        'BLENDER_RENDER',
        'BLENDER_EEVEE',
        'BLENDER_EEVEE_NEXT',
        'BLENDER_WORKBENCH',
    }

    @classmethod
    def poll(self, context):
        return not context.scene.render_raw_scene.enable_RR

    def draw_header(self, context):
        scene = context.scene
        view = scene.view_settings
        self.layout.prop(view, "use_curve_mapping", text="")

    def draw(self, context):
        draw_original_curves(self, context)

class OriginalDisplayPanel3DView(bpy.types.Panel):
    bl_label = "Display"
    bl_idname = 'RENDER_PT_render_raw_original_display_3d_view'
    bl_parent_id = "RENDER_PT_render_raw_color_management_3d_view"
    bl_options = {'DEFAULT_CLOSED'}
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Render'
    COMPAT_ENGINES = {
        'BLENDER_RENDER',
        'BLENDER_EEVEE',
        'BLENDER_EEVEE_NEXT',
        'BLENDER_WORKBENCH',
    }

    @classmethod
    def poll(self, context):
        return not context.scene.render_raw_scene.enable_RR

    def draw(self, context):
        draw_original_display(self, context)

class OriginalWhiteBalancePanel3DView(bpy.types.Panel):
    bl_label = "White Balance"
    bl_idname = 'RENDER_PT_render_raw_original_white_balance_3d_view'
    bl_parent_id = "RENDER_PT_render_raw_color_management_3d_view"
    bl_options = {'DEFAULT_CLOSED'}
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Render'
    COMPAT_ENGINES = {
        'BLENDER_RENDER',
        'BLENDER_EEVEE',
        'BLENDER_EEVEE_NEXT',
        'BLENDER_WORKBENCH',
    }

    @classmethod
    def poll(self, context):
        return not context.scene.render_raw_scene.enable_RR and bpy.app.version >= (4, 3, 0)

    def draw_header(self, context):
        self.layout.prop(context.scene.view_settings, "use_white_balance", text="")

    def draw_header_preset(self, context):
        layout = self.layout

        bpy.types.RENDER_PT_color_management_white_balance_presets.draw_panel_header(layout)

        eye = layout.operator("ui.eyedropper_color", text="", icon='EYEDROPPER')
        eye.prop_data_path = "scene.view_settings.white_balance_whitepoint"

    def draw(self, context):
        draw_original_white_balance(self, context)


viewport_panels = [
    OriginalWhiteBalancePanel3DView, OriginalDisplayPanel3DView, OriginalCurvePanel3DView,
]

classes = [
    OriginalWhiteBalancePanel, OriginalDisplayPanel, OriginalCurvePanel,
    OriginalWhiteBalancePanel3DView, OriginalDisplayPanel3DView, OriginalCurvePanel3DView,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    if hasattr(bpy.types, 'RENDER_PT_color_management_curves'):
        bpy.utils.unregister_class(bpy.types.RENDER_PT_color_management_curves)
    if hasattr(bpy.types, 'RENDER_PT_color_management_display_settings'):
        bpy.utils.unregister_class(bpy.types.RENDER_PT_color_management_display_settings)
    if hasattr(bpy.types, 'RENDER_PT_color_management_white_balance'):
        bpy.utils.unregister_class(bpy.types.RENDER_PT_color_management_white_balance)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
