import bpy
from bpy.props import FloatProperty, BoolProperty, EnumProperty

import bmesh

from .. utils.graph import build_mesh_graph
from .. utils.bmesh import ensure_default_data_layers, get_custom_data_layers
from .. utils.selection import get_2_rails_from_chamfer, get_sweeps_from_fillet
from .. utils.sweep import init_sweeps
from .. utils.loop import get_loops
from .. utils.handle import create_loop_intersection_handles, create_face_intersection_handles
from .. utils.tool import unfuse, unchamfer_loop_intersection, unchamfer_face_intersection, set_sharps_and_bweights
from .. utils.draw import debug_draw_sweeps, draw_lines
from .. utils.developer import output_traceback
from .. utils.ui import navigation_passthrough, popup_message, draw_init, draw_title, draw_prop, init_cursor, scroll, scroll_up, wrap_cursor, update_HUD_location
from .. utils.ui import init_status, finish_status
from .. utils.property import step_enum
from .. utils.registration import get_addon

from .. items import handle_method_items

decalmachine = None
hypercursor = None

class Unbevel(bpy.types.Operator):
    bl_idname = "machin3.unbevel"
    bl_label = "MACHIN3: Unbevel"
    bl_description = "Reconstruct hard edge from Bevel by using Unfuse + Unchamfer in sequence"
    bl_options = {'REGISTER', 'UNDO'}

    handlemethod: EnumProperty(name="Unchamfer Method", items=handle_method_items, default="FACE")
    slide: FloatProperty(name="Slide", default=0, min=-1, max=1)
    reverse: BoolProperty(name="Reverse", default=False)
    sharps: BoolProperty(name="Set Sharps", default=True)
    bweights: BoolProperty(name="Set Bevel Weights", default=False)
    bweight: FloatProperty(name="Weight", default=1, min=0, max=1)
    cyclic: BoolProperty(name="Cyclic", default=False)
    single: BoolProperty(name="Single", default=False)
    passthrough: BoolProperty(default=False)
    allowmodalslide: BoolProperty(default=False)
    @classmethod
    def poll(cls, context):
        if context.mode == 'EDIT_MESH':
            bm = bmesh.from_edit_mesh(context.active_object.data)
            return len([f for f in bm.faces if f.select]) >= 1 or len([e for e in bm.edges if e.select]) >= 1

    def draw(self, context):
        layout = self.layout
        column = layout.column()

        row = column.row()
        row.prop(self, "handlemethod", expand=True)

        if self.handlemethod == "FACE":
            column.prop(self, "slide")

        column.prop(self, "sharps")

        row = column.row()
        row.prop(self, "bweights")
        row.prop(self, "bweight")

        if self.single:
            column.prop(self, "reverse")

    def draw_HUD(self, context):
        if context.area == self.area:
            draw_init(self)

            draw_title(self, "Unbevel")

            draw_prop(self, "Handles", self.handlemethod, hint="scroll UP/Down")
            self.offset += 10

            if self.handlemethod == "FACE":
                draw_prop(self, "Slide", self.slide, offset=18, decimal=2, active=self.allowmodalslide, hint="move LEFT/RIGHT, toggle W, reset ALT + W")
                self.offset += 10

            draw_prop(self, "Set Sharps", self.sharps, offset=18, hint="toggle S")
            draw_prop(self, "Set BWeights", self.bweights, offset=18, hint="toggle B")
            if self.bweights:
                draw_prop(self, "BWeight", self.bweight, offset=18, hint="ALT scroll UP/DOWN")
            self.offset += 10

            if self.single:
                draw_prop(self, "Reverse", self.reverse, offset=18, hint="toggle R")

    def draw_VIEW3D(self, context):
        if context.scene.MM.debug:
            if context.area == self.area:
                if self.loops:
                    draw_lines(self.loops, mx=self.active.matrix_world, color=(0.4, 0.8, 1))

                if self.handles:
                    draw_lines(self.handles, mx=self.active.matrix_world, color=(1, 0.8, 0.4))

    def modal(self, context, event):
        context.area.tag_redraw()

        if event.type == "MOUSEMOVE":
            wrap_cursor(self, context, event)
            update_HUD_location(self, event)

        events = ['S', 'B', 'W', 'R']

        if self.allowmodalslide:
            events.append('MOUSEMOVE')

        if event.type in events or scroll(event):

            if event.type == 'MOUSEMOVE':
                if self.passthrough:
                    self.passthrough = False

                else:
                    if self.allowmodalslide:
                        divisor = 1000 if event.shift else 10 if event.ctrl else 100

                        delta_x = event.mouse_x - self.last_mouse_x
                        delta_slice = delta_x / divisor

                        self.slide += delta_slice

            elif scroll(event):
                if scroll_up(event):
                    if event.alt:
                        self.bweight += 0.1
                    else:
                        self.handlemethod = step_enum(self.handlemethod, handle_method_items, 1)

                else:
                    if event.alt:
                        self.bweight -= 0.1
                    else:
                        self.handlemethod = step_enum(self.handlemethod, handle_method_items, -1)

            elif event.type == 'S' and event.value == "PRESS":
                self.sharps = not self.sharps

            elif event.type == 'B' and event.value == "PRESS":
                self.bweights = not self.bweights

            elif event.type == 'R' and event.value == "PRESS":
                self.reverse = not self.reverse

            elif event.type == 'W' and event.value == "PRESS":
                if event.alt:
                    self.allowmodalslide = False
                    self.slide = 0
                else:
                    self.allowmodalslide = not self.allowmodalslide

            try:
                ret = self.main(self.active, modal=True)

                if not ret:
                    self.finish()
                    return {'FINISHED'}
            except Exception as e:
                self.finish()

                if bpy.context.mode == 'OBJECT':
                    bpy.ops.object.mode_set(mode='EDIT')

                output_traceback(self, e)
                return {'FINISHED'}

        elif navigation_passthrough(event, alt=True, wheel=False):
            self.passthrough = True
            return {'PASS_THROUGH'}

        elif event.type in {'LEFTMOUSE', 'SPACE'} and event.value == 'PRESS':
            self.finish()

            if self.hypercursor:
                bpy.ops.machin3.geogzm_setup('INVOKE_DEFAULT')

            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            self.cancel_modal()
            return {'CANCELLED'}

        self.last_mouse_x = event.mouse_x
        self.last_mouse_y = event.mouse_y

        return {'RUNNING_MODAL'}

    def finish(self):
        bpy.types.SpaceView3D.draw_handler_remove(self.HUD, 'WINDOW')
        bpy.types.SpaceView3D.draw_handler_remove(self.VIEW3D, 'WINDOW')

        finish_status(self)

    def cancel_modal(self, removeHUD=True):
        if removeHUD:
            self.finish()

        bpy.ops.object.mode_set(mode='OBJECT')
        self.initbm.to_mesh(self.active.data)
        bpy.ops.object.mode_set(mode='EDIT')

    def invoke(self, context, event):
        global decalmachine, hypercursor

        if decalmachine is None:
            decalmachine = get_addon("DECALmachine")[0]

        if hypercursor is None:
            hypercursor = get_addon("HyperCursor")[0]

        self.active = context.active_object

        self.active.update_from_editmode()

        self.slide = 0
        self.allowmodalslide = False
        self.init = True
        self.loops = []
        self.handles = []

        self.decalmachine = decalmachine and self.active.DM.decaltype == "PANEL"
        self.hypercursor = hypercursor and self.active.HC.ishyper

        self.initbm = bmesh.new()
        self.initbm.from_mesh(self.active.data)

        init_cursor(self, event)

        try:
            ret = self.main(self.active, modal=True)

            if not ret:
                self.cancel_modal(removeHUD=False)
                return {'FINISHED'}
        except Exception as e:
            if bpy.context.mode == 'OBJECT':
                bpy.ops.object.mode_set(mode='EDIT')

            output_traceback(self, e)
            return {'FINISHED'}

        init_status(self, context, 'Unbevel')

        self.area = context.area
        self.HUD = bpy.types.SpaceView3D.draw_handler_add(self.draw_HUD, (context, ), 'WINDOW', 'POST_PIXEL')
        self.VIEW3D = bpy.types.SpaceView3D.draw_handler_add(self.draw_VIEW3D, (context, ), 'WINDOW', 'POST_VIEW')

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        active = context.active_object
        success = False

        try:
            success = self.main(active)
        except Exception as e:
            output_traceback(self, e)

        if success and self.hypercursor:
            bpy.ops.machin3.geogzm_setup('INVOKE_DEFAULT')

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
        edge_layers = [bw] + get_custom_data_layers(bm)[0]

        initial_mg = build_mesh_graph(bm, debug=debug)
        initial_verts = [v for v in bm.verts if v.select]
        initial_faces = [f for f in bm.faces if f.select]

        initial_sweeps = get_sweeps_from_fillet(bm, initial_mg, initial_verts, initial_faces, debug=debug)

        if initial_sweeps:
            faces = unfuse(bm, initial_faces, initial_sweeps, debug=debug)

            if faces:
                if len(faces) == 1:
                    self.single = True
                else:
                    self.single = False

                if self.init:
                    self.init = False

                    self.sharps = any(f.smooth for f in faces)

                    if self.single and self.decalmachine:
                        self.init_panel_decal(active)

                verts = [v for v in bm.verts if v.select]
                mg = build_mesh_graph(bm, debug=debug)

                ret = get_2_rails_from_chamfer(bm, mg, verts, faces, reverse=self.reverse, debug=debug)
                if ret:
                    rails, self.cyclic = ret

                    sweeps = init_sweeps(bm, active, rails, debug=debug)

                    if bpy.context.scene.MM.debug:
                        initial_locations = [v.co.copy() for sweep in sweeps for v in sweep["verts"]]

                    get_loops(bm, edge_layers, faces, sweeps, debug=debug)

                    if self.handlemethod == "FACE":
                        create_face_intersection_handles(bm, sweeps, tension=1, debug=debug)
                        double_verts = unchamfer_face_intersection(bm, sweeps, slide=self.slide, debug=debug)

                    elif self.handlemethod == "LOOP":
                        create_loop_intersection_handles(bm, sweeps, tension=1, debug=debug)
                        double_verts = unchamfer_loop_intersection(bm, sweeps, debug=debug)

                    if bpy.context.scene.MM.debug:
                        self.handles = [co for ico, v in zip(initial_locations, double_verts) for co in [ico, v.co.copy()]]
                        debug_draw_sweeps(self, sweeps, draw_loops=True)

                    self.clean_up(bm, sweeps, faces, double_verts, debug=debug)

                    if double_verts:
                        set_sharps_and_bweights([e for e in bm.edges if e.select], bw, self.sharps, self.bweights, self.bweight)

                        bm.to_mesh(active.data)

                        bpy.ops.object.mode_set(mode='EDIT')
                        return True

                    else:
                        if self.single:
                            popup_message(["Loop edges don't intersect. You can't unbevel in this direction!", "Try toggling Reverse."])
                        else:
                            popup_message(["Loop edges don't intersect."])
                else:
                    bm.to_mesh(active.data)

                    bpy.ops.object.mode_set(mode='EDIT')
                    return True

        bpy.ops.object.mode_set(mode='EDIT')

        return False

    def init_panel_decal(self, active):
        self.handlemethod = "LOOP"
        self.reverse = True
        self.sharps = False
        self.bweights = False

    def clean_up(self, bm, sweeps, faces, double_verts=None, debug=False):
        if debug:
            print()
            print("Removing faces:", ", ".join(str(f.index) for f in faces))

        bmesh.ops.delete(bm, geom=faces, context='FACES')

        if double_verts:
            bmesh.ops.remove_doubles(bm, verts=double_verts, dist=0.00001)

            two_edged_verts = [v for v in double_verts if v.is_valid and len(v.link_edges) == 2]

            bmesh.ops.dissolve_verts(bm, verts=two_edged_verts)
