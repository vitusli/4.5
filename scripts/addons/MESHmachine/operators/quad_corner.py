import bpy
from bpy.props import FloatProperty, BoolProperty, EnumProperty

import bmesh

from .. utils.bmesh import ensure_default_data_layers
from .. utils.developer import output_traceback
from .. utils.graph import build_mesh_graph
from .. utils.handle import create_tri_corner_handles
from .. utils.loop import get_tri_corner_loops
from .. utils.math import average_locations
from .. utils.property import step_enum
from .. utils.selection import get_3_sides_from_tri_corner, get_2_rails_from_tri_corner
from .. utils.sweep import init_sweeps
from .. utils.tool import fuse_surface, create_splines, get_tri_corner_sharps_and_bweights, spread_tri_corner, set_tri_corner_sharps_and_bweights, rebuild_corner_faces
from .. utils.ui import draw_init, draw_title, draw_prop, init_cursor, navigation_passthrough, scroll, scroll_up, wrap_cursor, get_zoom_factor, update_HUD_location
from .. utils.ui import init_status, finish_status

from .. items import turn_items, tension_preset_items

class QuadCorner(bpy.types.Operator):
    bl_idname = "machin3.quad_corner"
    bl_label = "MACHIN3: Quad Corner"
    bl_description = "Convert a triangular Bevel Corner to Quad Corner"
    bl_options = {'REGISTER', 'UNDO'}

    width: FloatProperty(name="Width", default=0.01, min=0.0001, max=1, precision=2, step=0.1)
    tension: FloatProperty(name="Tension", default=0.55, min=0.01, max=2, step=0.1)
    tension_preset: EnumProperty(name="Tension Presets", items=tension_preset_items, default="CUSTOM")
    turn: EnumProperty(name="Turn", items=turn_items, default="1")
    single: BoolProperty(name="Single", default=False)
    passthrough: BoolProperty(default=False)
    allowmodalwidth: BoolProperty(default=True)
    allowmodaltension: BoolProperty(default=False)
    def draw(self, context):
        layout = self.layout
        column = layout.column()

        column.prop(self, "width")

        if not self.single:
            column.prop(self, "tension")
            row = column.row()
            row.prop(self, "tension_preset", expand=True)

        column.separator()

        row = column.row()
        row.label(text="Corner")
        row.prop(self, "turn", expand=True)

    def draw_HUD(self, context):
        if context.area == self.area:
            draw_init(self)

            draw_title(self, "Quad Corner")

            draw_prop(self, "Turn", self.turn, hint="scroll UP/DOwn")
            self.offset += 10

            draw_prop(self, "Width", self.width, active=self.allowmodalwidth, offset=18, hint="move LEFT/RIGHT, toggle W")

            if not self.single:
                draw_prop(self, "Tension", self.tension, offset=18, decimal=2, active=self.allowmodaltension, hint="move UP/DOWN, toggle T, presets Z/Y, X, C, V")

    @classmethod
    def poll(cls, context):
        if context.mode == 'EDIT_MESH':
            bm = bmesh.from_edit_mesh(context.active_object.data)
            return len([f for f in bm.faces if f.select]) >=1

    def modal(self, context, event):
        context.area.tag_redraw()

        if event.type == "MOUSEMOVE":
            wrap_cursor(self, context, event)
            update_HUD_location(self, event)

        events = ['Y', 'Z', 'X', 'C', 'V']

        if any([self.allowmodalwidth, self.allowmodaltension]):
            events.append('MOUSEMOVE')

        if event.type in events or scroll(event):

            if event.type == 'MOUSEMOVE':
                if self.passthrough:
                    self.passthrough = False

                else:
                    if self.allowmodalwidth:
                        divisor = 100 if event.shift else 1 if event.ctrl else 10

                        delta_x = event.mouse_x - self.last_mouse_x
                        delta_width = delta_x / divisor * self.factor

                        self.width += delta_width

                    if self.allowmodaltension:
                        divisor = 1000 if event.shift else 10 if event.ctrl else 100

                        delta_y = event.mouse_y - self.last_mouse_y
                        delta_tension = delta_y / divisor

                        self.tension_preset = "CUSTOM"
                        self.tension += delta_tension

            elif scroll(event):

                if scroll_up(event):
                    self.turn = step_enum(self.turn, turn_items, 1)

                else:
                    self.turn = step_enum(self.turn, turn_items, -1)

            elif (event.type == 'Y' or event.type == 'Z') and event.value == "PRESS":
                self.tension_preset = "0.55"

            elif event.type == 'X' and event.value == "PRESS":
                self.tension_preset = "0.7"

            elif event.type == 'C' and event.value == "PRESS":
                self.tension_preset = "1"

            elif event.type == 'V' and event.value == "PRESS":
                self.tension_preset = "1.33"

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

        elif event.type == 'T' and event.value == "PRESS":
            self.allowmodaltension = not self.allowmodaltension

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

        self.active.update_from_editmode()

        self.initbm = bmesh.new()
        self.initbm.from_mesh(self.active.data)

        self.matindex = 0

        self.factor = get_zoom_factor(context, self.active.matrix_world @ average_locations([v.co for v in self.initbm.verts if v.select]))

        init_cursor(self, event)

        if not self.allowmodalwidth:
            try:
                ret = self.main(self.active)

                if not ret:
                    return {'FINISHED'}
            except Exception as e:
                output_traceback(self, e)
                return {'FINISHED'}

        init_status(self, context, 'Quad Corner')

        self.area = context.area
        self.HUD = bpy.types.SpaceView3D.draw_handler_add(self.draw_HUD, (context, ), 'WINDOW', 'POST_PIXEL')
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        active = context.active_object

        try:
            self.main(active)
        except Exception as e:
            output_traceback(self, e)

        return {'FINISHED'}

    def main(self, active, modal=False, init=False):
        if self.tension_preset != "CUSTOM":
            self.tension = float(self.tension_preset)

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
        edges = [e for e in bm.edges if e.select]
        faces = [f for f in bm.faces if f.select]

        matindices = [f.material_index for f in faces]
        self.matindex = max(set(matindices), key=matindices.count)

        if len(faces) == 1:
            self.single = True
        else:
            self.single = False

        ret = get_3_sides_from_tri_corner(bm, mg, verts, edges, faces, self.turn, debug=debug)

        if ret:
            sides, corners = ret

            smooth, sidesharps, cornersharps, sidebweights, cornerbweights = get_tri_corner_sharps_and_bweights(bm, bw, faces, sides, corners, debug=debug)

            rails, other_vs = get_2_rails_from_tri_corner(bm, faces, sides, self.width, debug=debug)

            sweeps = init_sweeps(bm, active, rails, edges=False, freestyle=False, avg_face_normals=False, debug=debug)

            get_tri_corner_loops(bm, bw, faces, sweeps, debug=debug)

            spread_tri_corner(sweeps, self.width)
            create_tri_corner_handles(bm, sweeps, tension=self.tension, debug=debug)

            spline_sweeps = create_splines(bm, sweeps, segments=len(sides[2]) - 1, debug=debug)
            self.clean_up(bm, sweeps, faces, debug=debug)

            spline_sweeps.append(sides[1])
            spline_sweeps[-1].append(sides[2][0])

            fuse_faces, _ = fuse_surface(bm, spline_sweeps, smooth, self.matindex, capholes=False, select=False, debug=debug)

            set_tri_corner_sharps_and_bweights(bm, bw, spline_sweeps, sidesharps, cornersharps, sidebweights, cornerbweights, fuse_faces)

            rebuild_corner_faces(bm, sides, rails, spline_sweeps, self.single, smooth, debug=debug)

        bm.to_mesh(active.data)

        bpy.ops.object.mode_set(mode='EDIT')

        if ret:
            return True
        else:
            return False

    def clean_up(self, bm, sweeps, faces, debug=False):
        if debug:
            print()
            print("Removing faces:", ", ".join(str(f.index) for f in faces))

        bmesh.ops.delete(bm, geom=faces, context='FACES')
