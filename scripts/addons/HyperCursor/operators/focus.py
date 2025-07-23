import bpy
from bpy.props import BoolProperty, FloatProperty
from mathutils import Vector

from math import log10

from .. import HyperCursorManager as HC

from .. utils.draw import draw_fading_label, draw_init, draw_label, draw_lines, get_active_tool
from .. utils.math import dynamic_format
from .. utils.operator import Settings
from .. utils.ui import finish_modal_handlers, get_mouse_pos, get_zoom_factor, ignore_events, init_modal_handlers, navigation_passthrough, update_mod_keys, wrap_mouse, init_status, finish_status, force_ui_update, get_scale, draw_status_item
from .. utils.view import focus_on_cursor, clear_focus_cache
from .. utils.workspace import is_3dview

from .. colors import white, yellow, blue, red, green

class FocusCursor(bpy.types.Operator):
    bl_idname = "machin3.focus_cursor"
    bl_label = "MACHIN3: Focus on Cursor"
    bl_description = "Focus on the Cursor"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return is_3dview(context)

    def execute(self, context):
        focus_on_cursor(focusmode=context.scene.HC.focus_mode, ignore_selection=True)

        if context.space_data.lock_cursor:
            draw_fading_label(context, text="NOTE: With the View locked to the Cursor, you can only Zoom on the Cursor, not Focus it properly!", color=yellow, move_y=50, time=5)

        return {'FINISHED'}

def draw_proximity_status(op):
    def draw(self, context):
        layout = self.layout

        row = layout.row(align=True)

        row.label(text=f"Focus Proximity: {dynamic_format(context.scene.HC.focus_proximity, decimal_offset=2)}")
        row.label(text=f"Clip Start: {dynamic_format(op.clip_start)}")

        draw_status_item(row, key='LMB', text="Finish")

        row.separator(factor=10)

        draw_status_item(row, active=op.adjust_clip_start, key=['A', 'C'], text="Adjust Clip Start", gap=2)

        row.separator(factor=5)

        row.label(text="Proximity Presets via")
        draw_status_item(row, key=[1, 2, 3, 4], text="keys")

        row.separator(factor=2)
        row.label(text="Optionally combine")
        draw_status_item(row, key=[2, 3, 4], text="with")
        draw_status_item(row, key='ALT')

    return draw

class FocusProximity(bpy.types.Operator, Settings):
    bl_idname = "machin3.focus_proximity"
    bl_label = "MACHIN3: Focus Proximity"
    bl_options = {'REGISTER', 'UNDO'}

    proximity: FloatProperty(name="Proximity", default=1, min=0.000000001)
    adjust_clip_start: BoolProperty(name="Set the view's clip_start value, based on the cursor proximity, for fluid zooming", default=True)
    cache: BoolProperty(default=True)
    is_button_invocation: BoolProperty(name="Invoke operator from Sidebar Button", default=False)
    gizmoinvoke: BoolProperty(name="Invoke operator from Gizmo", default=False)
    @classmethod
    def poll(cls, context):
        return context.mode in ['OBJECT', 'EDIT_MESH']

    @classmethod
    def description(cls, context, properties):
        if properties:
            if properties.gizmoinvoke:
                desc = "Focus on the Cursor"
                desc += "\nDRAG: Adjust the Proximity"
                desc += "\nALT: Toggle Cursor"

            elif properties.is_button_invocation:
                desc = "Focus on the Cursor at specific Distance"
                desc += "\nShortcut: Shift Alt F"

            else:
                desc = "Focus on the Cursor"

            return desc
        return "Invalid Context"

    def draw_HUD(self, context):
        if context.area == self.area:
            if self.show_HUD:

                draw_init(self)

                dims = draw_label(context, title="Adjust Cursor Focus Proximity", coords=Vector((self.HUD_x, self.HUD_y)), center=False)

                if self.is_shift:
                    draw_label(context, title=" a little", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, size=10, color=white, alpha=0.5)

                elif self.is_ctrl:
                    draw_label(context, title=" a lot", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, size=10, color=white, alpha=0.5)

                self.offset += 18

                dims = draw_label(context, title="Proximity: ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, alpha=0.5)
                draw_label(context, title=dynamic_format(self.proximity, decimal_offset=2), coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False)

                self.offset += 18

                dims = draw_label(context, title="Clip Start: ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, alpha=0.5 if self.adjust_clip_start else 0.25)
                dims += draw_label(context, title=dynamic_format(self.clip_start, decimal_offset=2), coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, alpha=1 if self.adjust_clip_start else 0.25)

                if self.adjust_clip_start:
                    draw_label(context, title=" Auto", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=blue, alpha=1)

                if context.space_data.region_3d.view_perspective == 'PERSP':
                    if not self.adjust_clip_start:
                        self.offset += 18

                        draw_label(context, title="NOTE: Without setting Clip Start based on Proxmity, zooming is limited,", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=yellow, alpha=1)

                        self.offset += 18
                        draw_label(context, title="and clipping may occur in Perspective Views", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=yellow, alpha=1)

    def draw_VIEW3D(self, context):
        if context.area == self.area:
            if self.show_HUD and not self.is_cursor_shown:
                cmx = self.cursor.matrix
                loc, rot, _ = cmx.decompose()

                ui_scale = get_scale(context)
                factor = get_zoom_factor(context, loc, scale=300, ignore_obj_scale=True)
                size = 0.1

                axes = [(Vector((1, 0, 0)), red), (Vector((0, 1, 0)), green), (Vector((0, 0, 1)), blue)]

                for axis, color in axes:
                    coords = []

                    coords.append(loc + (rot @ axis).normalized() * factor * size * ui_scale * 0.9)
                    coords.append(loc + (rot @ axis).normalized() * factor * size * ui_scale)

                    coords.append(loc + (rot @ axis).normalized() * factor * size * ui_scale * 0.1)
                    coords.append(loc + (rot @ axis).normalized() * factor * size * ui_scale * 0.7)

                    if coords:
                        draw_lines(coords, indices=None, width=2, color=color)

    def modal(self, context, event):
        if ignore_events(event):
            return {'RUNNING_MODAL'}

        context.area.tag_redraw()

        update_mod_keys(self, event)

        events = ['MOUSEMOVE', 'ONE', 'TWO', 'THREE', 'FOUR', 'C', 'A']

        if event.type in events:

            if event.type == 'MOUSEMOVE':
                get_mouse_pos(self, context, event)
                wrap_mouse(self, context, x=True)

                if context.scene.HC.focus_proximity != 0:

                    lg10 = log10(context.scene.HC.focus_proximity)
                    dynamic_divisor = pow(10, -lg10)

                    delta_x = self.mouse_pos.x - self.last_mouse.x
                    delta_prox = delta_x / 333 / dynamic_divisor

                    precision = 0.1 if self.is_shift else 10 if self.is_ctrl else 1

                    self.proximity = context.scene.HC.focus_proximity - (delta_prox * precision)

                    self.set_proximity(context)

            elif event.type in ['ONE', 'TWO', 'THREE', 'FOUR'] and event.value == 'PRESS':

                if event.type == 'ONE':
                    self.proximity = 1

                elif event.type == 'TWO' and event.value == 'PRESS':
                    self.proximity = 5 if event.alt else 0.5

                elif event.type == 'THREE' and event.value == 'PRESS':
                    self.proximity = 10 if event.alt else 0.1

                elif event.type == 'FOUR' and event.value == 'PRESS':
                    self.proximity = 100 if event.alt else 0.01

                self.set_proximity(context)

            elif event.type in ['A', 'C'] and event.value == 'PRESS':
                self.adjust_clip_start = not self.adjust_clip_start

                force_ui_update(context)

                self.set_clip_start(context)

            if self.last_focus_proximity != self.proximity:
                self.last_focus_proximity = self.proximity

                if not self.show_HUD:
                    self.show_HUD = True

                    context.window.cursor_set('SCROLL_X')

                focus_on_cursor(focusmode='SOFT', ignore_selection=context.mode == 'EDIT_MESH', cache_bm=self.cache)

                if context.mode == 'EDIT_MESH':
                    force_ui_update(context)

        elif navigation_passthrough(event, alt=False, wheel=False):
            return {'PASS_THROUGH'}

        elif event.type in ['LEFTMOUSE', 'SPACE']:
            self.finish(context)

            self.save_settings()

            if round(context.scene.HC.focus_proximity, 8) == 0:
                print("WARNING: Avoiding setting focus proximity to 0")

                context.space_data.clip_start = 0.00001
                context.scene.HC.focus_proximity = context.space_data.clip_start * 3

            return {'FINISHED'}

        elif event.type in ['ESC', 'RIGHTMOUSE']:
            self.finish(context)

            context.scene.HC.focus_proximity = self.init_focus_proximity
            context.space_data.clip_start = self.init_clip_start

            focus_on_cursor(focusmode='SOFT', ignore_selection=True)

            return {'CANCELLED'}

        self.last_mouse = self.mouse_pos

        return {'RUNNING_MODAL'}

    def finish(self, context):
        finish_modal_handlers(self)

        finish_status(self)

        context.window.cursor_set('DEFAULT')

        for obj in self.sel:
            obj.select_set(True)

        context.scene.HC.draw_HUD = True

        clear_focus_cache()

    def invoke(self, context, event):
        self.init_settings(props=['adjust_clip_start'])
        self.load_settings()

        if self.gizmoinvoke:
            if event.alt:
                context.space_data.overlay.show_cursor = not context.space_data.overlay.show_cursor
                return {'FINISHED'}

        else:
            context.window.cursor_set('SCROLL_X')

        self.sel = [obj for obj in context.selected_objects]

        for obj in self.sel:
            obj.select_set(False)

        self.is_cursor_shown = self.get_cursor_shown(context, debug=False)

        self.init_focus_proximity = context.scene.HC.focus_proximity
        self.init_clip_start = context.space_data.clip_start

        self.proximity = self.init_focus_proximity
        self.clip_start = self.init_clip_start

        self.last_focus_proximity = self.init_focus_proximity

        update_mod_keys(self)

        self.show_HUD = not self.gizmoinvoke

        focus_on_cursor(focusmode='SOFT', ignore_selection=context.mode == 'EDIT_MESH', cache_bm=self.cache)

        context.scene.HC.draw_HUD = False

        self.cursor = context.scene.cursor

        get_mouse_pos(self, context, event)

        self.last_mouse = self.mouse_pos

        if context.space_data.lock_cursor:
            draw_fading_label(context, text="NOTE: With the View locked to the Cursor, you can only Zoom on the Cursor, not Focus it properly!", color=yellow, move_y=50, time=5)

        init_status(self, context, func=draw_proximity_status(self))

        init_modal_handlers(self, context, hud=True, view3d=True)
        return {'RUNNING_MODAL'}

    def get_cursor_shown(self, context, debug=False):
        view = context.space_data

        m3_draw_cursor_axes = context.scene.M3.draw_cursor_axes if HC.get_addon('MACHIN3tools') else False
        hc_show_gizmos = get_active_tool(context).idname in ['machin3.tool_hyper_cursor'] and context.scene.HC.show_gizmos

        is_cursor_shown = view.overlay.show_cursor or (m3_draw_cursor_axes and not hc_show_gizmos)

        if debug:
            print("b3d show_cursor:", view.overlay.show_cursor)
            print("m3 draw_cursor_axes:", m3_draw_cursor_axes)
            print("hc show_gizmos:", hc_show_gizmos)
            print("is cursor shown?:", is_cursor_shown)

        return is_cursor_shown

    def set_proximity(self, context):

        context.scene.HC.focus_proximity = self.proximity

        self.set_clip_start(context)

    def set_clip_start(self, context):
        if self.adjust_clip_start:
            self.clip_start = 0.05 if self.proximity == 1 else self.proximity / 3

            if self.clip_start != context.space_data.clip_start:
                context.space_data.clip_start = self.clip_start

        else:
            if context.space_data.clip_start != self.init_clip_start:
                self.clip_start = self.init_clip_start
                context.space_data.clip_start = self.init_clip_start

class ResetFocusProximity(bpy.types.Operator):
    bl_idname = "machin3.reset_focus_proximity"
    bl_label = "MACHIN3: Reset Focus Proximity"
    bl_description = "Reset Focus Proximity to 1 and clip_start to 0.05"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        context.scene.HC.focus_proximity = 1
        context.space_data.clip_start = 0.05

        focus_on_cursor(focusmode=context.scene.HC.focus_mode, ignore_selection=True)

        return {'FINISHED'}
