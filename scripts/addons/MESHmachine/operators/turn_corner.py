import bpy
from bpy.props import FloatProperty, BoolProperty

import bmesh

from ..utils.bmesh import ensure_default_data_layers
from ..utils.developer import output_traceback
from ..utils.math import average_locations
from ..utils.tool import turn_corner
from ..utils.ui import draw_init, draw_title, draw_prop, init_cursor, navigation_passthrough, scroll, scroll_up, wrap_cursor, get_zoom_factor, update_HUD_location
from ..utils.ui import init_status, finish_status

class TurnCorner(bpy.types.Operator):
    bl_idname = "machin3.turn_corner"
    bl_label = "MACHIN3: Turn Corner"
    bl_description = "Redirect Chamfer Flow by turning a corner where 3 Chamfers meet"
    bl_options = {'REGISTER', 'UNDO'}

    width: FloatProperty(name="Width", default=0.1, min=0.01, step=0.1)
    sharps: BoolProperty(name="Set Sharps", default=False)
    bweights: BoolProperty(name="Set Bevel Weights", default=False)
    bweight: FloatProperty(name="Weight", default=1, min=0, max=1)
    passthrough: BoolProperty(default=False)
    allowmodalwidth: BoolProperty(default=True)
    def draw(self, context):
        layout = self.layout
        column = layout.column()

        column.prop(self, "width")

        column.prop(self, "sharps")

        row = column.row()
        row.prop(self, "bweights")
        row.prop(self, "bweight")

    def draw_HUD(self, context):
        if context.area == self.area:
            draw_init(self)

            draw_title(self, "Turn Corner")

            draw_prop(self, "Turn", self.count, hint="scroll UP/DOWN")
            self.offset += 10

            draw_prop(self, "Width", self.width, active=self.allowmodalwidth, offset=18, hint="move LEFT/RIGHT, toggle W")

            self.offset += 10

            draw_prop(self, "Set Sharps", self.sharps, offset=18, hint="toggle S")
            draw_prop(self, "Set BWeights", self.bweights, offset=18, hint="toggle B")

            if self.bweights:
                draw_prop(self, "BWeight", self.bweight, offset=18, decimal=1, hint="ALT scroll UP/DOWN")

    @classmethod
    def poll(cls, context):
        if context.mode == 'EDIT_MESH':
            bm = bmesh.from_edit_mesh(context.active_object.data)
            faces = [f for f in bm.faces if f.select]
            verts = [v for v in bm.verts if v.select]

            if len(faces) == 1 and len(verts) == 4:
                v3s = [v for v in verts if len(v.link_edges) == 3]
                v4s = [v for v in verts if len(v.link_edges) == 4]
                return len(v3s) == len(v4s) == 2

    def modal(self, context, event):
        context.area.tag_redraw()

        if event.type == "MOUSEMOVE":
            wrap_cursor(self, context, event)
            update_HUD_location(self, event)

        events = ['S', 'B']

        if self.allowmodalwidth:
            events.append('MOUSEMOVE')

        if event.type in events or scroll(event):

            if event.type == 'MOUSEMOVE':
                if self.passthrough:
                    self.passthrough = False

                else:
                    divisor = 100 if event.shift else 1 if event.ctrl else 10

                    delta_x = event.mouse_x - self.last_mouse_x
                    delta_width = delta_x / divisor * self.factor

                    self.width += delta_width

            elif scroll(event):
                if scroll_up(event):
                    if event.alt:
                        self.bweight += 0.1
                    else:
                        self.count += 1
                        if self.count > 2:
                            self.count = 1

                else:
                    if event.alt:
                        self.bweight -= 0.1
                    else:
                        self.count -= 1
                        if self.count < 1:
                            self.count = 2

            elif event.type == 'S' and event.value == "PRESS":
                self.sharps = not self.sharps

            elif event.type == 'B' and event.value == "PRESS":
                self.bweights = not self.bweights

            try:
                ret = self.main(self.active, modal=True)

                if not ret:
                    self.finish()
                    return {'FINISHED'}

            except Exception as e:
                self.finish()

                output_traceback(self, e)
                return {'FINISHED'}

        elif event.type == 'W' and event.value == "PRESS":
            self.allowmodalwidth = not self.allowmodalwidth

        elif navigation_passthrough(event, alt=True, wheel=False):
            self.passthrough = True
            return {'PASS_THROUGH'}

        elif event.type in {'LEFTMOUSE', 'SPACE'} and event.value == 'PRESS':
            self.finish()
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            self.cancel_modal()
            return {'CANCELLED'}

        self.last_mouse_x = event.mouse_x
        self.last_mouse_y = event.mouse_y

        return {'RUNNING_MODAL'}

    def finish(self):
        bpy.types.SpaceView3D.draw_handler_remove(self.HUD, 'WINDOW')

        finish_status(self)

    def cancel_modal(self):
        self.finish()

        bpy.ops.object.mode_set(mode='OBJECT')
        self.initbm.to_mesh(self.active.data)
        bpy.ops.object.mode_set(mode='EDIT')

    def invoke(self, context, event):
        self.active = context.active_object

        context.object.update_from_editmode()

        self.count = 1

        self.initbm = bmesh.new()
        self.initbm.from_mesh(context.object.data)

        self.factor = get_zoom_factor(context, self.active.matrix_world @ average_locations([v.co for v in self.initbm.verts if v.select]))

        init_cursor(self, event)

        if not self.allowmodalwidth:
            try:
                ret = self.main(self.active, modal=True)

                if not ret:
                    return {'FINISHED'}

            except Exception as e:
                output_traceback(self, e)
                return {'FINISHED'}

        init_status(self, context, 'Turn Corner')

        self.area = context.area
        self.HUD = bpy.types.SpaceView3D.draw_handler_add(self.draw_HUD, (context, ), 'WINDOW', 'POST_PIXEL')

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        self.count = 1
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

        for i in range(self.count):
            bm = bmesh.new()
            bm.from_mesh(active.data)
            bm.normal_update()
            bm.verts.ensure_lookup_table()

            bw = ensure_default_data_layers(bm)[1]
            verts = [v for v in bm.verts if v.select]
            faces = [f for f in bm.faces if f.select]

            new_edges = turn_corner(bm, verts, faces, self.width, debug=debug)

            if any([self.sharps, self.bweights]):
                if self.sharps:
                    bpy.context.space_data.overlay.show_edge_sharp = True
                if self.bweights:
                    bpy.context.space_data.overlay.show_edge_bevel_weight = True

                for e in new_edges:
                    if self.sharps:
                        e.smooth = False
                    if self.bweights:
                        e[bw] = self.bweight

            bm.to_mesh(active.data)

        bpy.ops.object.mode_set(mode='EDIT')

        if new_edges:
            return True

        return False
