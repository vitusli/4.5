import bpy
from bpy.props import BoolProperty

from .. panels import draw_help_panel, draw_hyper_cursor_panel, draw_object_panel
from ... utils.draw import draw_fading_label
from ... utils.modifier import sort_modifiers
from ... utils.ui import finish_modal_handlers, finish_status, force_obj_gizmo_update

from ... colors import yellow, green, orange

class HyperCursorSettings(bpy.types.Operator):
    bl_idname = "machin3.hyper_cursor_settings"
    bl_label = "MACHIN3: HyperCursor Settings"
    bl_description = "⚙ Hyper Cursor Settings"
    bl_options = {'INTERNAL'}

    def draw(self, context):
        draw_hyper_cursor_panel(self, context, draw_grip=True)

    def execute(self, context):
        return context.window_manager.invoke_popup(self, width=300)

class HyperCursorHelp(bpy.types.Operator):
    bl_idname = "machin3.hyper_cursor_help"
    bl_label = "MACHIN3: HyperCursor Help"
    bl_description = "ℹ Hyper Cursor Help\n\nKeymaps, Documentation and Support"
    bl_options = {'INTERNAL'}

    def draw(self, context):
        draw_help_panel(self, context)

    def execute(self, context):
        return context.window_manager.invoke_popup(self, width=250)

class HyperCursorObject(bpy.types.Operator):
    bl_idname = "machin3.hyper_cursor_object"
    bl_label = "MACHIN3: HyperCursor Object"
    bl_options = {'REGISTER', 'UNDO'}

    hide_all_visible_wire_objs: BoolProperty(name="Hide all visible Wire Objects", description="Hide all visible Wire Objects and Empties", default=False)
    sort_modifiers: BoolProperty(name="Sort Modifiers", default=False)
    cycle_object_tree: BoolProperty(name="Cycle Object Tree", description="Toggle Visibility of Wire/Bounds/Empty Objects in the Object Tree", default=False)
    include_mod_objects: BoolProperty(name="Include Mod Objects", description="Include Mod Objects, that aren't parented in the Object Tree", default=True)
    last = None
    unsorted = False

    @classmethod
    def description(cls, context, properties):
        desc = "Hyper Cursor Object Menu"

        desc += "\n\nCTRL: Manually force Modifier Sorting + Object Gizmo Update"

        desc += "\n\nALT: Hide all visible Wire Objects and Empties"
        desc += "\nShortcut: Alt + ESC"

        return desc

    def draw(self, context):
        if self.is_panel:
            draw_object_panel(self, context)

    def finish(self, context):
        finish_modal_handlers(self)

        finish_status(self)

        context.scene.HC.show_object_gizmos = True

        context.active_object.select_set(True)

    def invoke(self, context, event):
        self.sort_modifiers = event.ctrl
        self.hide_all_visible_wire_objs = event.alt

        self.is_panel = False

        if self.hide_all_visible_wire_objs:
            bpy.ops.machin3.hide_wire_objects()
            return {'FINISHED'}

        elif self.sort_modifiers:
            active = context.active_object

            if context.active_object.HC.ismodsort:
                current = list(active.modifiers)
                sorted = sort_modifiers(obj=context.active_object, debug=False)

                if current == sorted:
                    draw_fading_label(context, "✔ Stack is already sorted", color=yellow, move_y=30, alpha=0.5, time=3)
                else:
                    draw_fading_label(context, "✔ Re-Sorted Mod Stack", color=green, move_y=30, time=3)

            else:
                draw_fading_label(context, "Skipping Mod Sorting, as it's currently disabled on this Object", color=orange, move_y=30, time=3)

            force_obj_gizmo_update(context)
            return {'FINISHED'}

        else:
            self.is_panel = True
            return self.execute(context)

    def execute(self, context):
        bpy.types.MACHIN3_OT_hyper_cursor_object.last = None

        active = context.active_object

        bpy.types.MACHIN3_OT_hyper_cursor_object.isunsorted = False

        if active and active.modifiers:
            sorted = sort_modifiers(active, preview = True)

            if sorted != list(active.modifiers):
                bpy.types.MACHIN3_OT_hyper_cursor_object.isunsorted = True

        return context.window_manager.invoke_popup(self, width=280)
