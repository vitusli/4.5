import bpy

from ... import HyperCursorManager as HC
from ... utils.registration import get_addon_prefs

class Reflect(bpy.types.Operator):
    bl_idname = "machin3.reflect"
    bl_label = "MACHIN3: Reflect"
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    @classmethod
    def description(cls, context, properties):
        machin3tools = HC.get_addon('MACHIN3tools')
        meshmachine = HC.get_addon('MESHmachine')

        if machin3tools:
            m3prefs = get_addon_prefs('MACHIN3tools')

            if not m3prefs.activate_mirror:
                m3prefs.activate_mirror = True

        if machin3tools and meshmachine and context.active_object.type == 'MESH':
            return "Symmetrize\nALT: Mirror"

        elif machin3tools:
            return "Mirror"

        elif meshmachine and context.active_object.type == 'MESH':
            return "Symmetrize"

    def invoke(self, context, event):
        machin3tools = HC.get_addon('MACHIN3tools')
        meshmachine = HC.get_addon('MESHmachine')

        active = context.active_object

        if machin3tools:
            m3prefs = get_addon_prefs('MACHIN3tools')

            if not m3prefs.activate_mirror:
                m3prefs.activate_mirror = True

        if machin3tools and (meshmachine and active.type == 'MESH'):
            if event.alt:
                bpy.ops.machin3.mirror('INVOKE_DEFAULT', flick=True, remove=False)
            else:
                bpy.ops.machin3.symmetrize('INVOKE_DEFAULT', objmode=True, partial=False, remove=False)

        elif machin3tools:
            bpy.ops.machin3.mirror('INVOKE_DEFAULT', flick=True, remove=False)

        elif meshmachine and active.type == 'MESH':
            bpy.ops.machin3.symmetrize('INVOKE_DEFAULT', objmode=True, partial=False, remove=False)

        return {'FINISHED'}
