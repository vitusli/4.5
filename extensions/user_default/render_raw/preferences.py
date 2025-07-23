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

import bpy, os
from .interface.sidebar import update_sidebar_category

def get_prefs(context):
    return context.preferences.addons[__package__].preferences

class render_raw_preferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    """ Presets """

    preset_path: bpy.props.StringProperty(
        name = 'Folder',
        description = 'The location custom presets will be saved to. This must be set before saving presets',
        default = ''
    )

    """ Interface """

    enable_3d_view_sidebar: bpy.props.BoolProperty(
        name = 'Enable in 3D View Sidebar',
        default = True
    )
    enable_compositing_sidebar: bpy.props.BoolProperty(
        name = 'Enable in Compositor Sidebar',
        default = True
    )
    enable_image_sidebar: bpy.props.BoolProperty(
        name = 'Enable in Image Editor Sidebar',
        default = True
    )
    sidebar_category: bpy.props.StringProperty(
        name = 'Sidebar Category',
        description = 'Which tab in the sidebar the Render Raw panels will be added to',
        default = 'Render',
        update = update_sidebar_category
    )
    enable_layers: bpy.props.BoolProperty(
        name = 'Enable Layers Panel',
        description = 'Layer based editing in Render Raw! This feature is off by default because it is still under development',
        default = False
    )

    """ Compositing """

    enable_compositing: bpy.props.EnumProperty(
        name = 'Auto Enable Viewport Compositing',
        description = 'Turn on Viewport Compositing for all 3D viewports when Render Raw is enabled, which is needed for the viewport colors to look correct',
        items = [
            ('ALL', 'In All 3D Viewports', 'Enables the viewport compositor in all 3d viewports in all workspaces'),
            ('SCREEN', 'In Active Workspace Viewports', 'Enables the viewport compositor in all 3d viewports in the active workspace'),
            ('NONE', 'In No Viewports', 'Does not enable viewport compositing when enabling Render Raw. This will cause the rendered view to look incorrect'),
        ],
        default = 'ALL'
    )
    transform_during_render: bpy.props.BoolProperty(
        name = 'Transform During Render',
        description = (
            'Switch from Raw to your chosen view transform while rendering. '
            'Enabling this causes less flicker and may be slightly faster, but makes the render in progress harder to see'
        ),
        default = False
    )
    animated_values: bpy.props.BoolProperty(
        name = 'Allow Animated Values (experimental)',
        description = (
            'Enables you to animate Render Raw values, but it is currently very slow during viewport playback. '
            'Performance can be improved by not using layers and by using the 3D View sidebar menu to adjust values '
            'while keeping the Properties Editor Color Management panel closed.'
        ),
        default = False
    )
    #Legacy option for old compositor
    enable_OpenCL: bpy.props.BoolProperty(
        name = 'Enable OpenCL Compositing',
        description = 'Generally, this should be enabled unless your hardware does not have good OpenCL support',
        default = True
    )
    #Legacy option for old compositor
    enable_buffer_groups: bpy.props.BoolProperty(
        name = 'Enable in 3D View Sidebar',
        description = 'Speeds up re-rendering at the cost of increased memory',
        default = True
    )

    def draw(self, context):
        col = self.layout.column()
        col.use_property_split = True

        col.label(text='Presets')
        row = col.row()
        row.prop(self, 'preset_path')
        row.operator("render.render_raw_set_preset_directory", icon='FILE_FOLDER', text='')
        if self.preset_path == '' or not os.path.isdir(self.preset_path):
            split = col.split(factor=0.4)
            col1 = split.column(align=True)
            col1.alignment = 'RIGHT'
            col2 = split.column(align=True)
            col2.label(text='Folder must be set before saving presets', icon='ERROR')
        col.separator()

        col.label(text='Interface')
        interface = col.column(heading='Show Panels In')
        interface.prop(self, 'enable_3d_view_sidebar', text='3D View Sidebar')
        category = col.column()
        category.enabled = self.enable_3d_view_sidebar
        category.prop(self, 'sidebar_category')
        col.separator()
        layers = col.column(heading='Enable')
        layers.prop(self, 'enable_layers', text='Layers Panel (Experimental)')
        # interface.prop(self, 'enable_compositing_sidebar', text='Compositor Sidebar')
        # interface.prop(self, 'enable_image_sidebar', text='Image Editor Sidebar')
        col.separator()

        col.label(text='Compositing')
        col.prop(self, 'enable_compositing', text='Auto Enable')
        col.separator()
        if bpy.app.version < (4, 2, 0):
            render = col.column(heading='Auto Enable')
            render.prop(self, 'enable_OpenCL', text='OpenCL')
            render.prop(self, 'enable_buffer_groups', text='Buffer Groups')
            col.separator()

        #if bpy.app.version < (4, 4, 0):
        col.row(heading='Enable').prop(self, 'transform_during_render', text='Transform During Render (Experimental)')
        col.prop(self, 'animated_values', text='Animated Values (Experimental)')


def register():
    bpy.utils.register_class(render_raw_preferences)

def unregister():
    bpy.utils.unregister_class(render_raw_preferences)
