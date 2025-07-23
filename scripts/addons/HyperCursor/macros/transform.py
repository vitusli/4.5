import bpy

from .. utils.object import is_wire_object
from .. utils.tools import active_tool_is_hypercursor

class Translate(bpy.types.Macro):
    bl_idname = "machin3.macro_hyper_cursor_translate"
    bl_label = "MACHIN3: Translate Macro"
    bl_options = {'INTERNAL'}

    def init():
        Translate.define('TRANSFORM_OT_translate')
        Translate.define('WM_OT_context_toggle')

class Rotate(bpy.types.Macro):
    bl_idname = "machin3.macro_hyper_cursor_rotate"
    bl_label = "MACHIN3: Rotate Macro"
    bl_options = {'INTERNAL'}

    def init():
        Rotate.define('TRANSFORM_OT_rotate')
        Rotate.define('WM_OT_context_toggle')

class BooleanTranslate(bpy.types.Macro):
    bl_idname = "machin3.macro_hyper_cursor_boolean_translate"
    bl_label = "MACHIN3: Boolean Translate Macro"
    bl_description = "Translate a Boolean Operand Object and its children.\nSupport surface snapping and transferring the operand to another host object"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT' and active_tool_is_hypercursor(context):
            active = context.active_object
            sel = context.selected_objects
            is_wire = is_wire_object(active)

            if active and active.parent and is_wire and active in sel and len(sel) == 1:

                booleans = [mod for mod in active.parent.modifiers if mod.type == 'BOOLEAN' and mod.object == active]
                return booleans

    def init():
        BooleanTranslate.define('MACHIN3_OT_init_boolean_translate_on_parent').properties.duplicate = False
        BooleanTranslate.define('TRANSFORM_OT_translate')
        BooleanTranslate.define('MACHIN3_OT_restore_boolean_on_parent')

class BooleanDuplicateTranslate(bpy.types.Macro):
    bl_idname = "machin3.macro_hyper_cursor_boolean_duplicate_translate"
    bl_label = "MACHIN3: Boolean Duplicate Macro"
    bl_description = "Duplicate-Translate a Boolean Operand Object and its children.\nSupport surface snapping and transferring the operand to another host object"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT' and active_tool_is_hypercursor(context):
            active = context.active_object
            sel = context.selected_objects
            is_wire = is_wire_object(active, empty=False, instance_collection=False, curve=False)

            if active and active.parent and is_wire and active in sel and len(sel) == 1:

                booleans = [mod for mod in active.parent.modifiers if mod.type == 'BOOLEAN' and mod.object == active]
                return booleans

    def init():
        BooleanDuplicateTranslate.define('MACHIN3_OT_init_boolean_translate_on_parent').properties.duplicate = True
        BooleanDuplicateTranslate.define('TRANSFORM_OT_translate')
        BooleanDuplicateTranslate.define('MACHIN3_OT_restore_boolean_on_parent')
