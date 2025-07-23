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

from ..preferences import get_prefs
from ..utilities.settings import get_settings
from ..utilities.presets import copy_default_presets, refresh_presets, remove_preset, save_preset, blank_preset


class SetPresetDirectory(bpy.types.Operator):
    bl_label = 'Set Presets Folder'
    bl_idname = "render.render_raw_set_preset_directory"
    bl_options = {'REGISTER'}

    directory: bpy.props.StringProperty(
        name = 'Path'
    )
    filter_folder: bpy.props.BoolProperty(
        default = True,
        options={"HIDDEN"}
    )

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        PREFS = get_prefs(context)
        PREFS.preset_path = self.directory
        copy_default_presets(context)
        return{'FINISHED'}


class SavePreset(bpy.types.Operator):
    bl_label = 'Save Preset'
    bl_idname = "render.render_raw_save_preset"
    bl_description = (
        "Save the current Render Raw settings as a preset which can be used in any other project. "
        "A preset folder must be specified in the add-on preferences for this to be enabled"
    )

    preset_name: bpy.props.StringProperty(
        name = 'Name',
        default = 'My Preset'
    )
    include_exposure: bpy.props.BoolProperty(
        name = 'Exposure',
        default = True
    )
    include_gamma: bpy.props.BoolProperty(
        name = 'Gamma',
        default = True
    )

    @classmethod
    def poll(self, context):
        PREFS = get_prefs(context)
        prefs_path = PREFS.preset_path
        return (
            hasattr(context.scene, 'render_raw') and
            prefs_path and
            os.path.isdir(prefs_path)
        )

    def draw(self, context):
        col = self.layout.column()
        col.use_property_split = True
        col.prop(self, 'preset_name')
        # col.separator()
        # col = self.layout.column(heading='Include')
        # col.use_property_split = True
        # col.prop(self, 'include_exposure')
        # col.prop(self, 'include_gamma')

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        save_preset(self, context)
        return {'FINISHED'}


class RemovePreset(bpy.types.Operator):
    bl_label = 'Remove Render Raw Preset'
    bl_idname = 'render.render_raw_remove_preset'
    bl_description = (
        'Deletes the current preset. '
        'A preset folder must be specified in the add-on preferences for this to be enabled'
    )

    @classmethod
    def poll(self, context):
        RR = get_settings(context)
        PREFS = get_prefs(context)
        return (
            RR.props_pre.preset != blank_preset and
            PREFS.preset_path and os.path.isdir(PREFS.preset_path)
        )

    def draw(self, context):
        RR = get_settings(context)
        row = self.layout.row()
        row.label(text=f'Permanently delete {RR.props_pre.preset}?', icon='QUESTION')

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        remove_preset(context)
        refresh_presets(context)
        return {'FINISHED'}


class RefreshPresets(bpy.types.Operator):
    bl_label = 'Refresh Render Raw Presets'
    bl_idname = 'render.render_raw_refresh_presets'
    bl_description = (
        'Updates all presets. '
        'A preset folder must be specified in the add-on preferences for this to be enabled'
    )

    @classmethod
    def poll(self, context):
        prefs = get_prefs(context)
        prefs_path = prefs.preset_path

        return prefs_path and os.path.isdir(prefs_path)

    def execute(self, context):
        refresh_presets(context)
        return {'FINISHED'}


classes = [SavePreset, RemovePreset, RefreshPresets, SetPresetDirectory]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)