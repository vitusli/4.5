import bpy
from bpy.props import FloatProperty, BoolProperty

import bmesh

from ..utils.bmesh import ensure_default_data_layers
from ..utils.developer import output_traceback
from ..utils.draw import draw_lines, debug_draw_sweeps
from ..utils.graph import build_mesh_graph
from ..utils.loop import get_loops
from ..utils.math import average_locations
from ..utils.selection import get_2_rails_from_chamfer
from ..utils.sweep import init_sweeps
from ..utils.tool import change_width
from ..utils.ui import init_status, finish_status, navigation_passthrough
from ..utils.ui import popup_message, draw_title, draw_prop, draw_init, init_cursor, wrap_cursor, get_zoom_factor, update_HUD_location

class ChangeWidth(bpy.types.Operator):
    bl_idname = "machin3.change_width"
    bl_label = "MACHIN3: Change Width"
    bl_description = "Change the width of Chamfers(flat Bevels)"
    bl_options = {'REGISTER', 'UNDO'}

    width: FloatProperty(name="Width", default=0.0, step=0.1)
    reverse: BoolProperty(name="Reverse", default=False)
    taper: BoolProperty(name="Taper", default=False)
    taperflip: BoolProperty(name="Taper Flip", default=False)
    single: BoolProperty(name="Single", default=False)
    cyclic: BoolProperty(name="Cyclic", default=False)
    passthrough: BoolProperty(default=False)
    def draw(self, context):
        layout = self.layout
        column = layout.column()

        column.prop(self, "width")

        if self.single:
            column.prop(self, "reverse")

        if not self.cyclic:
            row = column.row()
            row.prop(self, "taper")
            row.prop(self, "taperflip")

    def draw_HUD(self, context):
        if context.area == self.area:
            draw_init(self)

            draw_title(self, "Change Width")

            draw_prop(self, "Width", self.width, decimal=3, hint="move LEFT/RIGHT")

            if self.single:
                draw_prop(self, "Reverse", self.reverse, offset=18, hint="toggle R")

            if not self.cyclic:
                draw_prop(self, "Taper", self.taper, offset=18, hint="toggle T")

                if self.taper:
                    draw_prop(self, "Taper Flip", self.taperflip, offset=18, hint="toggle F")

    def draw_VIEW3D(self, context):
        if context.scene.MM.debug:
            if context.area == self.area:
                if self.loops:
                    draw_lines(self.loops, mx=self.active.matrix_world, color=(0.4, 0.8, 1))

    @classmethod
    def poll(cls, context):
        if context.mode == 'EDIT_MESH':
            bm = bmesh.from_edit_mesh(context.active_object.data)
            return len([f for f in bm.faces if f.select]) >= 1

    def modal(self, context, event):
        context.area.tag_redraw()

        if event.type == "MOUSEMOVE":
            wrap_cursor(self, context, event)
            update_HUD_location(self, event)

        if event.type in ['MOUSEMOVE', 'R', 'T', 'F']:

            if event.type == 'MOUSEMOVE':
                if self.passthrough:
                    self.passthrough = False

                else:
                    divisor = 100 if event.shift else 1 if event.ctrl else 10

                    delta_x = event.mouse_x - self.last_mouse_x
                    delta_width = delta_x / divisor * self.factor

                    self.width += delta_width

            elif event.type == 'R' and event.value == "PRESS":
                self.reverse = not self.reverse

            elif event.type == 'T' and event.value == "PRESS":
                if not self.cyclic:
                    self.taper = not self.taper

            elif event.type == 'F' and event.value == "PRESS":
                if not self.cyclic:
                    self.taperflip = not self.taperflip

            try:
                ret = self.main(self.active, modal=True)

                if ret is False:
                    self.finish()
                    return {'FINISHED'}
            except Exception as e:
                self.finish()

                if context.mode == 'OBJECT':
                    bpy.ops.object.mode_set(mode='EDIT')

                output_traceback(self, e)
                return {'FINISHED'}

        elif navigation_passthrough(event, alt=True, wheel=False):
            self.passthrough = True
            return {'PASS_THROUGH'}

        elif event.type in ['LEFTMOUSE', 'SPACE'] and event.value == 'PRESS':
            self.finish()
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            self.finish()

            bpy.ops.object.mode_set(mode='OBJECT')
            self.initbm.to_mesh(self.active.data)
            bpy.ops.object.mode_set(mode='EDIT')

            return {'CANCELLED'}

        self.last_mouse_x = event.mouse_x
        self.last_mouse_y = event.mouse_y

        return {'RUNNING_MODAL'}

    def finish(self):
        bpy.types.SpaceView3D.draw_handler_remove(self.HUD, 'WINDOW')
        bpy.types.SpaceView3D.draw_handler_remove(self.VIEW3D, 'WINDOW')

        finish_status(self)

    def invoke(self, context, event):
        self.active = context.active_object

        self.active.update_from_editmode()

        self.width = 0
        self.reverse = False
        self.loops = []

        self.initbm = bmesh.new()
        self.initbm.from_mesh(self.active.data)

        self.factor = get_zoom_factor(context, self.active.matrix_world @ average_locations([v.co for v in self.initbm.verts if v.select]))

        init_cursor(self, event)

        init_status(self, context, "Change Width")

        self.area = context.area
        self.HUD = bpy.types.SpaceView3D.draw_handler_add(self.draw_HUD, (context, ), 'WINDOW', 'POST_PIXEL')
        self.VIEW3D = bpy.types.SpaceView3D.draw_handler_add(self.draw_VIEW3D, (context, ), 'WINDOW', 'POST_VIEW')

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        active = context.active_object

        try:
            self.main(active)
        except Exception as e:
            output_traceback(self, e)

        return {'FINISHED'}

    def main(self, active, modal=False):
        debug = True
        debug = False

        bpy.ops.object.mode_set(mode='OBJECT')

        if modal:
            self.initbm.to_mesh(active.data)

        bm = bmesh.new()
        bm.from_mesh(active.data)

        bm.normal_update()
        bm.verts.ensure_lookup_table()

        bw = ensure_default_data_layers(bm)[1]
        mg = build_mesh_graph(bm, debug=debug)
        verts = [v for v in bm.verts if v.select]
        faces = [f for f in bm.faces if f.select]

        if len(faces) == 1:
            self.single = True
        else:
            self.single = False

        ret = get_2_rails_from_chamfer(bm, mg, verts, faces, self.reverse, debug=debug)

        if ret:
            rails, self.cyclic = ret

            if not self.cyclic:
                if self.taper and self.taperflip:
                    r1, r2 = rails

                    r1.reverse()
                    r2.reverse()

                    rails = (r1, r2)

            sweeps = init_sweeps(bm, active, rails, debug=debug)

            get_loops(bm, bw, faces, sweeps, debug=debug)

            if bpy.context.scene.MM.debug:
                debug_draw_sweeps(self, sweeps, draw_loops=True)

            changed_width = change_width(bm, sweeps, self.width, taper=self.taper, debug=debug)

            if changed_width:
                bm.to_mesh(active.data)
            else:
                popup_message("Something went wrong, likely not a valid chamfer selection.", title="Chamfer Width")

        bpy.ops.object.mode_set(mode='EDIT')

        if ret:
            if changed_width:
                return True

        return False
