import bpy

class ToggleSmartKeymaps(bpy.types.Operator):
    bl_idname = "machin3.toggle_smart_keymaps"
    bl_label = "Toggle Smart Keymaps"
    bl_description = "Toggle Smart Keymaps"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        wm = context.window_manager
        kc = wm.keyconfigs.user
        km = kc.keymaps['Mesh']

        kmis = []

        for kmi in km.keymap_items:
            if kmi.idname in ['machin3.smart_vert', 'machin3.smart_edge', 'machin3.smart_face']:
                kmis.append(kmi)

        if kmis:
            state = not kmis[0].active

            for kmi in kmis:
                kmi.active = state

        return {'FINISHED'}
