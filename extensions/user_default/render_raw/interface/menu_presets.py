import bpy, os

from ..preferences import get_prefs

class PresetsMenu(bpy.types.Menu):
    bl_label = 'Render Raw Presets'
    bl_idname = 'RENDER_MT_render_raw_preset_options'

    def draw(self, context):
        col = self.layout.column()

        prefs = get_prefs(context)
        path = prefs.preset_path
        if path == '' or not os.path.isdir(path):
            col.label(text='Set folder in preferences', icon='ERROR')
            col.separator()

        col.operator('render.render_raw_save_preset', text='Save Preset', icon='FILE_TICK')
        col.operator('render.render_raw_refresh_presets', text='Refresh Presets', icon='FILE_REFRESH')
        col.operator('render.render_raw_remove_preset', text='Remove Preset', icon='TRASH')

def register():
    bpy.utils.register_class(PresetsMenu)

def unregister():
    bpy.utils.unregister_class(PresetsMenu)