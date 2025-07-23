import bpy
from bpy.props import IntProperty, FloatProperty, BoolProperty, EnumProperty

import bmesh

import math

from .. utils.draw import draw_point, draw_vector, draw_line
from .. utils.math import get_angle_between_edges
from .. utils.property import step_enum
from .. utils.ui import draw_init, draw_title, draw_prop, init_cursor, navigation_passthrough, scroll, scroll_up, wrap_cursor

from .. items import fuse_method_items, handle_method_items, tension_preset_items

class MESHmachineDebug(bpy.types.Operator):
    bl_idname = "machin3.meshmachine_debug"
    bl_label = "MACHIN3: MESHmachine Debug"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return False

    def invoke(self, context, event):
        return {'FINISHED'}

class MESHmachineDebugToggle(bpy.types.Operator):
    bl_idname = "machin3.meshmachine_debug_toggle"
    bl_label = "MACHIN3: Debug MESHmachine"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        mm = context.scene.MM
        mm.debug = not mm.debug

        return {'FINISHED'}

class GetAngle(bpy.types.Operator):
    bl_idname = "machin3.get_angle"
    bl_label = "MACHIN3: Get Angle"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        active = context.active_object
        mesh = active.data

        bpy.ops.object.mode_set(mode='OBJECT')

        bm = bmesh.new()
        bm.from_mesh(mesh)
        bm.normal_update()

        edges = [e for e in bm.edges if e.select]

        if len(edges) == 1:
            e = edges[0]

            angle = math.degrees(e.calc_face_angle())
            print("angle between two faces:", angle)

        elif len(edges) == 2:
            e1 = edges[0]
            e2 = edges[1]

            angle = get_angle_between_edges(e1, e2, radians=False)
            print("angle between two faces:", angle)

        bm.to_mesh(mesh)

        bpy.ops.object.mode_set(mode='EDIT')

        return {'FINISHED'}

class GetLength(bpy.types.Operator):
    bl_idname = "machin3.get_length"
    bl_label = "MACHIN3: Get Length"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
            active = context.active_object
            mesh = active.data

            bpy.ops.object.mode_set(mode='OBJECT')

            bm = bmesh.new()
            bm.from_mesh(mesh)
            bm.normal_update()

            edges = [e for e in bm.edges if e.select]

            for edge in edges:
                print("edge:", edge.index, "length:", edge.calc_length())

            bm.to_mesh(mesh)

            bpy.ops.object.mode_set(mode='EDIT')

            return {'FINISHED'}

class DrawDebug(bpy.types.Operator):
    bl_idname = "machin3.draw_debug"
    bl_label = "MACHIN3: Draw Debug"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        active = context.active_object
        mxw = active.matrix_world

        bm = bmesh.from_edit_mesh(active.data)
        bm.normal_update()
        bm.verts.ensure_lookup_table()

        faces = [f for f in bm.faces if f.select]

        for f in faces:
            center = f.calc_center_median()
            draw_point(center, mx=mxw, modal=False)

            draw_vector(f.normal, origin=center, mx=mxw, color=(1, 0, 0), modal=False)

            co = f.verts[0].co
            coords = [center, co]

            draw_line(coords, mx=mxw, color=(1, 1, 0), modal=False)

        context.area.tag_redraw()

        return {'FINISHED'}

class DebugHUD(bpy.types.Operator):
    bl_idname = "machin3.debug_hud"
    bl_label = "MACHIN3: Debug HUD"
    bl_options = {'REGISTER', 'UNDO'}

    method: EnumProperty(name="Method", items=fuse_method_items, default="FUSE")
    handlemethod: EnumProperty(name="Unchamfer Method", items=handle_method_items, default="FACE")
    segments: IntProperty(name="Segments", default=6, min=0, max=30)
    tension: FloatProperty(name="Tension", default=0.7, min=0.01, max=4, step=0.1)
    tension_preset: EnumProperty(name="Tension Presets", items=tension_preset_items, default="CUSTOM")
    average: BoolProperty(name="Average Tension", default=False)
    force_projected_loop: BoolProperty(name="Force Projected Loop", default=False)
    width: FloatProperty(name="Width (experimental)", default=0.0, step=0.1)
    passthrough: BoolProperty(default=False)
    allowmodalwidth: BoolProperty(default=False)
    allowmodaltension: BoolProperty(default=False)
    def draw(self, context):
        layout = self.layout
        column = layout.column()

        row = column.row()
        row.prop(self, "method", expand=True)
        column.separator()

        if self.method == "Debug HUDE":
            row = column.row()
            row.prop(self, "handlemethod", expand=True)
            column.separator()

        column.prop(self, "segments")
        column.prop(self, "tension")
        row = column.row()
        row.prop(self, "tension_preset", expand=True)

        if self.method == "FUSE":
            column.prop(self, "force_projected_loop")

            column.separator()
            column.prop(self, "width")

    def draw_HUD(self, context):
        if context.area == self.area:

            draw_init(self)

            draw_title(self, "Debug HUD")

            draw_prop(self, "Method", self.method, offset=0, hint="SHIFT scroll UP/DOWN,")
            if self.method == "FUSE":
                draw_prop(self, "Handles", self.handlemethod, offset=18, hint="CTRL scroll UP/DOWN")
            self.offset += 10

            draw_prop(self, "Segments", self.segments, offset=18, hint="scroll UP/DOWN")
            draw_prop(self, "Tension", self.tension, offset=18, decimal=2, active=self.allowmodaltension, hint="move UP/DOWN, toggle T, presets Z/Y, X, C, V")

            if self.method == "FUSE":
                draw_prop(self, "Projected Loops", self.force_projected_loop, offset=18, hint="toggle P")

                self.offset += 10

                draw_prop(self, "Width", self.width, offset=18, decimal=3, active=self.allowmodalwidth, hint="move LEFT/RIGHT, toggle W, reset ALT + W")
                self.offset += 10

    def modal(self, context, event):
        context.area.tag_redraw()

        if event.type == "MOUSEMOVE":
            wrap_cursor(self, context, event)

        events = ['R', 'S', 'F', 'Y', 'Z', 'X', 'C', 'V', 'W', 'T', 'A', 'P']

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
                        delta_width = delta_x / divisor

                        self.width += delta_width

                    if self.allowmodaltension:
                        divisor = 1000 if event.shift else 10 if event.ctrl else 100

                        delta_y = event.mouse_y - self.last_mouse_y
                        delta_tension = delta_y / divisor

                        self.tension_preset = "CUSTOM"
                        self.tension += delta_tension

            if scroll(event):
                if scroll_up(event):
                    if event.shift:
                        self.method = step_enum(self.method, fuse_method_items, 1)
                    elif event.ctrl:
                        self.handlemethod = step_enum(self.handlemethod, handle_method_items, 1)
                    else:
                        self.segments += 1

                else:
                    if event.shift:
                        self.method = step_enum(self.method, fuse_method_items, -1)
                    elif event.ctrl:
                        self.handlemethod = step_enum(self.handlemethod, handle_method_items, -1)
                    else:
                        self.segments -= 1

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

            elif event.type == 'P' and event.value == "PRESS":
                self.force_projected_loop = not self.force_projected_loop

        elif navigation_passthrough(event, alt=False, wheel=False):
            self.passthrough = True
            return {'PASS_THROUGH'}

        elif event.type in {'LEFTMOUSE', 'SPACE'} and event.value == 'PRESS':
            bpy.types.SpaceView3D.draw_handler_remove(self.HUD, 'WINDOW')
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            self.cancel_modal()
            return {'CANCELLED'}

        self.last_mouse_x = event.mouse_x
        self.last_mouse_y = event.mouse_y

        return {'RUNNING_MODAL'}

    def cancel_modal(self, removeHUD=True):
        if removeHUD:
            bpy.types.SpaceView3D.draw_handler_remove(self.HUD, 'WINDOW')

    def invoke(self, context, event):
        init_cursor(self, event)

        self.area = context.area
        self.HUD = bpy.types.SpaceView3D.draw_handler_add(self.draw_HUD, (context, ), 'WINDOW', 'POST_PIXEL')

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
