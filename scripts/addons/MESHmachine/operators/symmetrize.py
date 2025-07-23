import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty
from bpy_extras.view3d_utils import region_2d_to_location_3d, region_2d_to_origin_3d, region_2d_to_vector_3d
import bmesh
from mathutils import Vector
from .. utils.symmetrize import symmetrize
from .. utils.draw import draw_point, draw_vector, draw_circle, draw_label
from .. utils.ui import draw_status_item, get_zoom_factor, init_status, finish_status, navigation_passthrough
from .. utils.tool import get_flick_direction
from .. utils.registration import get_prefs, get_addon
from .. items import axis_items, direction_items, custom_normal_mirror_method_items, fix_center_method_items
from .. colors import red, green, blue, white

vert_ids = []
custom_normals = None
remove = False

hypercursor = None

def draw_symmetrize(op):
    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)

        row.label(text='Symmetrize')

        draw_status_item(row, key='MOVE', text='Pick Axis')
        draw_status_item(row, key='LMB', text='Finish')
        draw_status_item(row, key='RMB', text='Cancel')

        draw_status_item(row, active=op.partial, key='S', text='Selected only', gap=10)

        draw_status_item(row, active=op.remove, key='X', text='Remove', gap=1)

    return draw

class Symmetrize(bpy.types.Operator):
    bl_idname = "machin3.symmetrize"
    bl_label = "MACHIN3: Symmetrize"
    bl_description = "Symmetrize a mesh incl. its custom normals"
    bl_options = {'REGISTER', 'UNDO'}

    objmode: BoolProperty(name="Object Mode", default=False)
    flick: BoolProperty(name="Flick", default=True)
    axis: EnumProperty(name="Axis", items=axis_items, default="X")
    direction: EnumProperty(name="Direction", items=direction_items, default="POSITIVE")
    threshold: FloatProperty(name="Threshold", default=0.0001)
    partial: BoolProperty(name="Partial", description="Full or Partial(selected only) Symmetrize", default=False)
    remove: BoolProperty(name="Remove", description="Symmetrize or Remove", default=False)
    remove_redundant_center: BoolProperty(name="Remove Redundant Center", description="Remove Redundant Center Edges created through the Symmetrize Operation", default=True)
    redundant_threshold: FloatProperty(name="Redundant Threshold Angle", description="Threshold Angle, that determines if Center Edges are Redundant", default=0.05, min=0, max=1, step=0.1)
    is_custom_normal: BoolProperty(default=False)
    mirror_custom_normals: BoolProperty(name="Mirror Custom Normals", default=True)
    custom_normal_method: EnumProperty(name="Custom Normal Mirror Method", items=custom_normal_mirror_method_items, default="INDEX")
    has_vertex_groups: BoolProperty(default=False)
    mirror_vertex_groups: BoolProperty(default=False)
    fix_center: BoolProperty(name="Fix Center Seam", default=False)
    fix_center_method: EnumProperty(name="Fix Center Method", items=fix_center_method_items, default="CLEAR")
    clear_sharps: BoolProperty(name="Clear Center Sharps", default=True)
    passthrough = None

    @classmethod
    def poll(cls, context):
        return context.mode in ['EDIT_MESH', 'OBJECT']

    def draw(self, context):
        layout = self.layout

        column = layout.column()

        row = column.row(align=True)
        row.prop(self, 'partial', text='Selected' if self.partial else 'All', toggle=True)
        row.prop(self, 'remove', text='Remove' if self.remove else 'Symmetrize', toggle=True)

        row = column.row()
        row.prop(self, "axis", expand=True)
        row.prop(self, "direction", expand=True)

        if not self.remove and not self.partial:
            if self.is_custom_normal:
                column.separator()
                column.prop(self, "mirror_custom_normals")

                if self.mirror_custom_normals:
                    box = column.box()
                    box.label(text="Custom Normal Pairing Method")
                    row = box.row()
                    row.prop(self, "custom_normal_method", expand=True)

                    column.separator()
                    column.prop(self, "fix_center")

                    if self.fix_center:
                        box = column.box()

                        row = box.row()
                        row.label(text="Fix Center Method")
                        row.prop(self, "clear_sharps")

                        row = box.row()
                        row.prop(self, "fix_center_method", expand=True)

            else:
                column.separator()

                row = column.split(factor=0.6, align=True)
                row.prop(self, "remove_redundant_center", toggle=True)

                r = row.row(align=True)
                r.active = self.remove_redundant_center
                r.prop(self, "redundant_threshold", text='Threshold', slider=True)

            if self.has_vertex_groups and not (self.is_custom_normal and self.mirror_custom_normals):
                column.separator()
                column.prop(self, "mirror_vertex_groups", text="Mirror Vertex Groups", toggle=True)

    def draw_HUD(self, context):
        if context.area == self.area:
            if not self.passthrough:

                draw_vector(self.flick_vector, origin=self.init_mouse, alpha=0.99)

                color = red if self.remove else white
                alpha = 0.2 if self.remove else 0.02
                draw_circle(self.init_mouse, radius=self.flick_distance, width=3, color=color, alpha=alpha)

                if self.partial:
                    draw_label(context, title='Selected', coords=(self.init_mouse[0], self.init_mouse[1] + self.flick_distance - (15 * self.scale)), center=True, color=color, alpha=1.0)

                title = 'Remove' if self.remove else 'Symmetrize'
                alpha = 1 if self.remove else 0.8
                draw_label(context, title=title, coords=(self.init_mouse[0], self.init_mouse[1] + self.flick_distance - (15 * self.scale * (2 if self.partial else 1))), center=True, color=color, alpha=alpha)

                draw_label(context, title=self.flick_direction.replace('_', ' ').title(), coords=(self.init_mouse[0], self.init_mouse[1] - self.flick_distance + (15 * self.scale)), center=True, alpha=0.4)

    def draw_VIEW3D(self, context):
        if context.area == self.area:
            for direction, axis, color in zip(self.axes.keys(), self.axes.values(), self.colors):
                positive = 'POSITIVE' in direction

                draw_vector(axis * self.zoom / 2, origin=self.init_mouse_3d, color=color, width=2 if positive else 1, alpha=0.99 if positive else 0.3)

            draw_point(self.init_mouse_3d + self.axes[self.flick_direction] * self.zoom / 2 * 1.2, size=5, alpha=0.8)

    def modal(self, context, event):
        context.area.tag_redraw()

        self.mousepos = Vector((event.mouse_region_x, event.mouse_region_y, 0))

        events = ['MOUSEMOVE', 'X', 'D', 'S', 'P']

        if event.type in events:

            if self.passthrough:
                self.passthrough = False
                self.init_mouse = self.mousepos
                self.init_mouse_3d = region_2d_to_location_3d(context.region, context.region_data, self.init_mouse, self.origin)
                self.zoom = get_zoom_factor(context, depth_location=self.origin, scale=self.flick_distance, ignore_obj_scale=True)

            self.flick_vector = self.mousepos - self.init_mouse

            if self.flick_vector.length:
                self.flick_direction = get_flick_direction(self, context)

                self.direction, self.axis = self.get_symmetrize_direction()

            if self.flick_vector.length > self.flick_distance:
                self.finish()

                self.execute(context)
                return {'FINISHED'}

        if navigation_passthrough(event, alt=True, wheel=False):
            self.passthrough = True
            return {'PASS_THROUGH'}

        elif event.type in {'X', 'D'} and event.value == 'PRESS':
            self.remove = not self.remove
            context.active_object.select_set(True)

        elif event.type in {'S', 'P'} and event.value == 'PRESS':
            self.partial = not self.partial
            context.active_object.select_set(True)

        elif event.type in {'LEFTMOUSE', 'SPACE'} and event.value == 'PRESS':
                self.finish()

                self.direction, self.axis = self.get_symmetrize_direction()

                self.execute(context)
                return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            self.finish()

            context.active_object.select_set(True)

            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def finish(self):
        bpy.types.SpaceView3D.draw_handler_remove(self.HUD, 'WINDOW')
        bpy.types.SpaceView3D.draw_handler_remove(self.VIEW3D, 'WINDOW')

        finish_status(self)

    def invoke(self, context, event):
        active = context.active_object

        if self.partial:
            bm = bmesh.from_edit_mesh(active.data)
            selected = [v for v in bm.verts if v.select]

            if not selected:
                self.partial = False

        if self.flick:
            mx = active.matrix_world

            self.scale = context.preferences.system.ui_scale * get_prefs().modal_hud_scale
            self.flick_distance = get_prefs().symmetrize_flick_distance * self.scale

            self.mousepos = Vector((event.mouse_region_x, event.mouse_region_y, 0))

            view_origin = region_2d_to_origin_3d(context.region, context.region_data, self.mousepos)
            view_dir = region_2d_to_vector_3d(context.region, context.region_data, self.mousepos)

            self.origin = view_origin + view_dir * 10

            self.zoom = get_zoom_factor(context, depth_location=self.origin, scale=self.flick_distance, ignore_obj_scale=True)

            self.init_mouse = self.mousepos
            self.init_mouse_3d = region_2d_to_location_3d(context.region, context.region_data, self.init_mouse, self.origin)

            self.flick_vector = self.mousepos - self.init_mouse
            self.flick_direction = 'NEGATIVE_X'

            self.axes = {'POSITIVE_X': mx.to_quaternion() @ Vector((1, 0, 0)),
                         'NEGATIVE_X': mx.to_quaternion() @ Vector((-1, 0, 0)),
                         'POSITIVE_Y': mx.to_quaternion() @ Vector((0, 1, 0)),
                         'NEGATIVE_Y': mx.to_quaternion() @ Vector((0, -1, 0)),
                         'POSITIVE_Z': mx.to_quaternion() @ Vector((0, 0, 1)),
                         'NEGATIVE_Z': mx.to_quaternion() @ Vector((0, 0, -1))}

            self.colors = [red, red, green, green, blue, blue]

            init_status(self, context, func=draw_symmetrize(self))
            context.active_object.select_set(True)

            self.area = context.area
            self.HUD = bpy.types.SpaceView3D.draw_handler_add(self.draw_HUD, (context, ), 'WINDOW', 'POST_PIXEL')
            self.VIEW3D = bpy.types.SpaceView3D.draw_handler_add(self.draw_VIEW3D, (context, ), 'WINDOW', 'POST_VIEW')

            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}

        else:
            self.execute(context)
            return {'FINISHED'}

    def execute(self, context):
        global custom_normals, vert_ids, remove, hypercursor

        if self.objmode:

            if hypercursor is None:
                hypercursor = get_addon('HyperCursor')[0]

            bpy.ops.object.mode_set(mode='EDIT')

            for obj in context.selected_objects:
                if obj != context.active_object:
                    obj.select_set(False)

        active = context.active_object
        active.update_from_editmode()

        self.is_custom_normal = active.data.has_custom_normals
        direction = f"{self.direction}_{self.axis}"

        self.has_vertex_groups = bool(active.vertex_groups)

        ret = symmetrize(active, direction, threshold=self.threshold, partial=self.partial, remove=self.remove, remove_redundant_center=self.remove_redundant_center, redundant_threshold=self.redundant_threshold, mirror_vertex_groups=bool(self.has_vertex_groups and self.mirror_vertex_groups), mirror_custom_normals=self.mirror_custom_normals, custom_normal_method=self.custom_normal_method, fix_center=self.fix_center, fix_center_method=self.fix_center_method, clear_sharps=self.clear_sharps, debug=False)

        if self.objmode:
            bpy.ops.object.mode_set(mode='OBJECT')

            if hypercursor:
                from HyperCursor.utils.ui import force_geo_gizmo_update

                force_geo_gizmo_update(context)

        custom_normals = ret['custom_normal']

        vert_ids = ret['center'] if self.remove else ret['mirror'] + ret['center']

        remove = self.remove

        if vert_ids:
            bpy.ops.machin3.draw_symmetrize()

        return {'FINISHED'}

    def get_symmetrize_direction(self):
        direction, axis = self.flick_direction.split('_')
        return 'POSITIVE' if direction == 'NEGATIVE' else 'NEGATIVE', axis
