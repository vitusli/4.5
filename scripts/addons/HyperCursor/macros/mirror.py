import bpy

class MirrorHide(bpy.types.Macro):
    bl_idname = "machin3.macro_mirror_hide"
    bl_label = "MACHIN3: Mirror Hide Macro"
    bl_options = {'INTERNAL'}    # NOTE: using internal here avoids Blender crash when deactivating Mirror tool in MACHIN3tools and then opening the operator search menu afterwords, it's not clear why I commented this out before and then eneabled REGISTER and REDO, it's only operator called anyway

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            return getattr(bpy.types, 'MACHIN3_OT_mirror', False)

    def init():
        if getattr(bpy.types, 'MACHIN3_OT_mirror', False):
            op = MirrorHide.define('MACHIN3_OT_mirror')
            op.properties.flick = True
            op.properties.remove = False

        MirrorHide.define('MACHIN3_OT_hide_mirror_obj')
