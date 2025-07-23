import bpy
from bpy.props import FloatProperty, IntProperty, BoolProperty, EnumProperty

import bmesh

from .. items import tension_preset_items

from .. utils.developer import output_traceback
from .. utils.math import average_locations
from .. utils.selection import get_selected_vert_sequences, propagate_edge_loops
from .. utils.tool import align_vert_sequence_to_spline
from .. utils.ui import draw_init, draw_title, draw_prop, init_cursor, navigation_passthrough, scroll, scroll_up, wrap_cursor, get_zoom_factor, update_HUD_location
from .. utils.ui import init_status, finish_status

class Unfuck(bpy.types.Operator):
    bl_idname = "machin3.unfuck"
    bl_label = "MACHIN3: Unf*ck"
    bl_description = "Align non-cyclic edge loop along bezier"
    bl_options = {'REGISTER', 'UNDO'}

    width: FloatProperty(name="Width", default=0, step=0.1)
    width2: FloatProperty(name="Width 2", default=0, step=0.1)
    widthlinked: BoolProperty(name="Width Linked", default=True)
    tension: FloatProperty(name="Tension", default=0.7, min=0.01, max=10, step=0.1)
    tension_preset: EnumProperty(name="Tension Presets", items=tension_preset_items, default="CUSTOM")
    tension2: FloatProperty(name="Tension 2", default=0.7, min=0.01, max=10, step=0.1)
    tension2_preset: EnumProperty(name="Tension Presets", items=tension_preset_items, default="CUSTOM")
    tensionlinked: BoolProperty(name="Tension Linked", default=True)
    propagate: IntProperty(name="Propagate", default=0, min=0)
    fade: FloatProperty(name="Fade", default=1, min=0, max=1, step=0.1)
    merge: BoolProperty(name="Merge", default=False)
    advanced: BoolProperty(name="Advanced Mode", default=False)
    passthrough: BoolProperty(default=False)
    allowmodalwidth: BoolProperty(default=True)
    allowmodaltension: BoolProperty(default=False)
    @classmethod
    def poll(cls, context):
        if context.mode == 'EDIT_MESH':
            mode = bpy.context.scene.tool_settings.mesh_select_mode
            bm = bmesh.from_edit_mesh(context.active_object.data)
            return len([e for e in bm.edges if e.select]) >= 2 and (mode[0] or mode[1])

    def draw(self, context):
        layout = self.layout
        column = layout.column()

        column.prop(self, "merge", toggle=True)

        if not self.merge:
            if self.advanced:
                row = column.row().split(factor=0.2)
                row.prop(self, "widthlinked", icon="LINKED", text="Linked")
                row.prop(self, "width")
                r = row.row()
                r.active = not self.widthlinked
                r.prop(self, "width2")

                row = column.row().split(factor=0.2)
                row.prop(self, "tensionlinked", icon="LINKED", text="Linked")
                row.prop(self, "tension")
                r = row.row()
                r.active = not self.tensionlinked
                r.prop(self, "tension2")
                row = column.row()
                row.prop(self, "tension_preset", expand=True)
                row.prop(self, "tension2_preset", expand=True)
            else:
                column.prop(self, "width")
                column.prop(self, "tension")
                row = column.row()
                row.prop(self, "tension_preset", expand=True)

        if self.can_propagate:
            column.separator()
            row = column.row().split(factor=0.6)
            row.prop(self, "propagate")

            if not self.merge:
                row.prop(self, "fade")

                column.separator()
                column.prop(self, "advanced")

    def draw_HUD(self, context):
        if context.area == self.area:
            draw_init(self)

            draw_title(self, "Unf*ck")

            draw_prop(self, "Merge", self.merge, hint="toggle M")
            self.offset += 10

            if not self.merge:
                draw_prop(self, "Width", self.width, offset=18, decimal=3, active=self.allowmodalwidth, hint="move LEFT/RIGHT, toggle W, reset ALT + W")
                draw_prop(self, "Tension", self.tension, offset=18, decimal=2, active=self.allowmodaltension, hint="move UP/DOWN, toggle T, presets Z/Y, X, C, V")
                self.offset += 10

            if self.can_propagate:
                draw_prop(self, "Propagate", self.propagate, offset=18, hint="scroll UP/DOWN")

                if self.propagate > 0 and not self.merge:
                    draw_prop(self, "Fade", self.fade, offset=18, decimal=1, hint="ALT scroll  UP/DOWN")

    def modal(self, context, event):
        context.area.tag_redraw()

        if event.type == "MOUSEMOVE":
            wrap_cursor(self, context, event)
            update_HUD_location(self, event)

        events = ['Y', 'Z', 'X', 'C', 'V', 'W', 'T', 'M']

        if any([self.allowmodalwidth, self.allowmodaltension]):
            events.append('MOUSEMOVE')

        if event.type in events or (self.can_propagate and scroll(event)):

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

            elif event.type == 'M' and event.value == "PRESS":
                self.merge = not self.merge

            elif scroll(event):
                if scroll_up(event):
                    if event.alt:
                        self.fade += 0.1
                    else:
                        self.propagate += 1

                else:
                    if event.alt:
                        self.fade -= 0.1
                    else:
                        self.propagate -= 1

            elif (event.type == 'Y' or event.type == 'Z') and event.value == "PRESS":
                self.tension_preset = "0.55"

            elif event.type == 'X' and event.value == "PRESS":
                self.tension_preset = "0.7"

            elif event.type == 'C' and event.value == "PRESS":
                self.tension_preset = "1"

            elif event.type == 'V' and event.value == "PRESS":
                self.tension_preset = "1.33"

            elif event.type == 'W' and event.value == "PRESS":
                if event.alt:
                    self.allowmodalwidth = False
                    self.width = 0
                else:
                    self.allowmodalwidth = not self.allowmodalwidth

            elif event.type == 'T' and event.value == "PRESS":
                self.allowmodaltension = not self.allowmodaltension

            try:
                ret = self.unfuck(self.active, modal=True)

                if not ret:
                    self.finish()
                    return {'FINISHED'}
            except Exception as e:
                output_traceback(self, e)

                self.finish()

                self.merge = False
                return {'FINISHED'}

        elif navigation_passthrough(event, alt=True, wheel=False):
            self.passthrough = True
            return {'PASS_THROUGH'}

        elif event.type in {'LEFTMOUSE', 'SPACE'} and event.value == 'PRESS':
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

        finish_status(self)

    def invoke(self, context, event):
        self.active = context.active_object

        self.active.update_from_editmode()

        self.width = 0
        self.propagate = 0

        self.initbm = bmesh.new()
        self.initbm.from_mesh(self.active.data)

        self.can_propagate = self.analyse_selection()

        self.factor = get_zoom_factor(context, self.active.matrix_world @ average_locations([v.co for v in self.initbm.verts if v.select]))

        init_cursor(self, event)

        self.init_tension = self.tension

        init_status(self, context, 'Unf*ck')

        self.area = context.area
        self.HUD = bpy.types.SpaceView3D.draw_handler_add(self.draw_HUD, (context, ), 'WINDOW', 'POST_PIXEL')

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        active = context.active_object

        try:
            self.unfuck(active)
        except Exception as e:
            output_traceback(self, e)

        return {'FINISHED'}

    def analyse_selection(self):
        edges = [e for e in self.initbm.edges if e.select]

        can_propagate = False

        ends = []

        for edge in edges:
            for v in edge.verts:
                if len([e for e in v.link_edges if e in edges]) == 1:
                    ends.append((edge, v))

        for edge, v in ends:
            loops = [l for l in edge.link_loops if l.vert == v]

            if len(loops) == 1:
                if can_propagate is False:
                    can_propagate = 'ONE'
                else:
                    can_propagate = 'BOTH'

        return can_propagate

    def unfuck(self, active, modal=False):
        if self.tension_preset != "CUSTOM":
            self.tension = float(self.tension_preset)

        if self.tension2_preset != "CUSTOM":
            self.tension2 = float(self.tension2_preset)

        debug = False

        bpy.ops.object.mode_set(mode='OBJECT')

        if modal:
            self.initbm.to_mesh(active.data)

        bm = bmesh.new()
        bm.from_mesh(active.data)
        bm.normal_update()
        bm.verts.ensure_lookup_table()

        verts = [v for v in bm.verts if v.select]

        sequences = get_selected_vert_sequences(verts, debug=False)

        non_cyclic_seqs = [seq for seq, cyclic in sequences if not cyclic and len(seq) > 3]

        if self.can_propagate and len(non_cyclic_seqs) > 1:
            self.can_propagate = False

        for seq in non_cyclic_seqs:
            merge_verts = []

            align_vert_sequence_to_spline(bm, seq, self.width, self.width2, self.tension, self.tension2, 0, self.merge, merge_verts, False, self.widthlinked, self.tensionlinked, self.advanced, debug=debug)

            if self.can_propagate and self.propagate:
                propagate_edge_loops(bm, seq, self.propagate, self.width, self.width2, self.tension, self.tension2, self.fade, self.merge, merge_verts, self.widthlinked, self.tensionlinked, self.advanced, debug=debug)

            if self.merge:
                for mvs in merge_verts:
                    bmesh.ops.remove_doubles(bm, verts=mvs, dist=0.00001)

        bm.to_mesh(active.data)
        bpy.ops.object.mode_set(mode='EDIT')

        return bool(non_cyclic_seqs)
