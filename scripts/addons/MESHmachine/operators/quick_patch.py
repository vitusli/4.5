import bpy
from bpy.props import IntProperty, BoolProperty, FloatProperty

import bmesh

from .. utils.draw import draw_points, draw_vector, draw_mesh_wire
from .. utils.math import average_locations, dynamic_format
from .. utils.mesh import get_coords
from .. utils.raycast import cast_obj_ray_from_mouse, cast_obj_ray_from_point
from .. utils.ui import draw_status_item, force_ui_update, init_cursor, draw_init, draw_title, draw_prop, get_zoom_factor, navigation_passthrough, scroll, scroll_up, update_HUD_location
from .. utils.ui import init_status, finish_status

from .. colors import white, green

def draw_quick_patch(op):
    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)

        row.label(text='Quick Patch')

        draw_status_item(row, key='SPACE', text='Finish')
        draw_status_item(row, key='MMB', text='Vewport')
        draw_status_item(row, key='RMB', text='Cancel')

        draw_status_item(row, key='LMB' if len(op.draw_coords) < 4 else [], text=f"{'Place ' if len(op.draw_coords) < 4 else ''}Points {len(op.draw_coords)}/4", gap=10)

        if op.draw_coords:
            draw_status_item(row, key='F1', text="Undo", gap=2)

        if op.undos:
            draw_status_item(row, key='F2', text="Redo", gap=1 if op.draw_coords else 2)

        if len(op.draw_coords) == 4:
            draw_status_item(row, key='MMB_SCROLL', text="Subdivisions:", prop=op.subdivisions, gap=2)

            draw_status_item(row, active=op.allowmodaloffsetpatch, key='W', text=f"Offset{':' if op.offset_patch and not op.allowmodaloffsetpatch else ''}", gap=2)

            if op.offset_patch or op.allowmodaloffsetpatch:
                draw_status_item(row, active=op.allowmodaloffsetpatch, key='MOVE' if op.allowmodaloffsetpatch else [], prop=dynamic_format(op.offset_patch, decimal_offset=2))

            if op.offset_patch:
                draw_status_item(row, key=['ALT', 'W'], text="Reset", gap=1)

    return draw

class QuickPatch(bpy.types.Operator):
    bl_idname = "machin3.quick_patch"
    bl_label = "MACHIN3: Quick Patch"
    bl_description = "Create a surface confirming polygon patch by drawing 4 corner points."
    bl_options = {'REGISTER', 'UNDO'}

    subdivisions: IntProperty(name="Subdivisions", default=3, min=3)
    offset_patch: FloatProperty(name="Offset", default=0)
    passthrough: BoolProperty(default=False)
    allowmodaloffsetpatch: BoolProperty(default=False)
    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and context.active_object and context.active_object.type == 'MESH'

    def draw_HUD(self, context):
        if context.area == self.area:
            draw_init(self)

            draw_title(self, "Quick Patch")

            draw_prop(self, "Points", len(self.draw_coords), hint="LMB to place, F1 to undo, F2 to redo")

            if len(self.draw_coords) == 4:
                self.offset += 10
                draw_prop(self, "Subdivisions", self.subdivisions, offset=18, hint="scroll UP/DOWN")
                draw_prop(self, "Offset Patch", self.offset_patch, offset=18, decimal=3, active=self.allowmodaloffsetpatch, hint="move LEFT/RIGHT, toggle W, reset ALT + W")

    def draw_VIEW3D(self, context):
        if context.area == self.area:
            if len(self.draw_coords) < 4:
                draw_points(self.draw_coords, color=white, size=6, alpha=1, xray=True)

            else:
                if self.mesh_corner_coords:
                    draw_points(self.mesh_corner_coords, color=green, size=8, alpha=1, xray=False)

                if self.mesh_subd_coords:
                    draw_points(self.mesh_subd_coords, color=white, size=6, alpha=0.5, xray=False)

                if self.batch:
                    draw_mesh_wire(self.batch, width=2, alpha=0.1, xray=False)

    def modal(self, context, event):
        context.area.tag_redraw()

        if event.type == 'MOUSEMOVE':
            update_HUD_location(self, event)

        events = ['LEFTMOUSE', 'F1', 'F2', 'W', 'S']

        if self.allowmodaloffsetpatch:
            events.append('MOUSEMOVE')

        if event.type in events or scroll(event):

            if event.type == 'MOUSEMOVE':
                if self.passthrough:
                    self.passthrough = False

                else:
                    if self.allowmodaloffsetpatch and self.factor:
                        divisor = 100 if event.shift else 1 if event.ctrl else 10

                        delta_x = event.mouse_x - self.last_mouse_x
                        delta_offset = delta_x / divisor * self.factor

                        self.offset_patch += delta_offset

                        force_ui_update(context, self.active)

            elif scroll(event):

                if scroll_up(event):
                    self.subdivisions += 1
                    force_ui_update(context, self.active)

                else:
                    self.subdivisions -= 1
                    force_ui_update(context, self.active)

            elif event.type == 'LEFTMOUSE' and event.value == "PRESS" and not event.alt:
                if len(self.draw_coords) < 4:
                    mousepos = (event.mouse_region_x, event.mouse_region_y)

                    _, location, _, _, _ = cast_obj_ray_from_mouse(mousepos, candidates=[self.active], debug=False)

                    if location:
                        self.draw_coords.append(location)

                        self.undos = []

                        force_ui_update(context, self.active)

            elif event.type == "F1" and event.value == 'PRESS':
                if self.draw_coords:
                    self.undos.append(self.draw_coords[-1])
                    self.draw_coords = self.draw_coords[:-1]

                    force_ui_update(context, self.active)

            elif event.type == "F2" and event.value == 'PRESS':
                if self.undos:
                    self.draw_coords.append(self.undos[-1])
                    self.undos = self.undos[:-1]

                    force_ui_update(context, self.active)

            elif event.type == 'W' and event.value == "PRESS":
                if event.alt:
                    self.allowmodaloffsetpatch = False
                    self.offset_patch = 0
                else:
                    self.allowmodaloffsetpatch = not self.allowmodaloffsetpatch

                force_ui_update(context, self.active)

            if len(self.draw_coords) == 4:
                self.factor, self.mesh_corner_coords, self.mesh_subd_coords = self.create_patch_mesh(context, self.subdivisions, self.offset_patch)
                self.batch = get_coords(self.mesh, indices=True)

            else:
                self.factor = None
                self.allowmodaloffsetpatch = False

        if navigation_passthrough(event, alt=True, wheel=False):
            self.passthrough = True
            return {'PASS_THROUGH'}

        elif event.type in {'SPACE'}:
            self.finish(context)

            if self.mesh:
                self.create_patch_object(context)

            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'} and not event.alt:
            self.finish(context)

            return {'CANCELLED'}

        self.last_mouse_x = event.mouse_x
        self.last_mouse_y = event.mouse_y

        return {'RUNNING_MODAL'}

    def finish(self, context):
        bpy.types.SpaceView3D.draw_handler_remove(self.HUD, 'WINDOW')
        bpy.types.SpaceView3D.draw_handler_remove(self.VIEW3D, 'WINDOW')

        finish_status(self)

        context.window.cursor_set('DEFAULT')

        force_ui_update(context)

    def invoke(self, context, event):
        self.active = context.active_object
        self.dg = context.evaluated_depsgraph_get()

        self.draw_coords = []
        self.mesh_corner_coords = []
        self.mesh_subd_coords = []
        self.batch = None
        self.undos = []
        self.mesh = None
        self.factor = None
        self.allowmodaloffset = False

        init_cursor(self, event)
        context.window.cursor_set('CROSSHAIR')

        init_status(self, context, func=draw_quick_patch(self))

        force_ui_update(context)

        self.area = context.area
        self.VIEW3D = bpy.types.SpaceView3D.draw_handler_add(self.draw_VIEW3D, (context, ), 'WINDOW', 'POST_VIEW')
        self.HUD = bpy.types.SpaceView3D.draw_handler_add(self.draw_HUD, (context, ), 'WINDOW', 'POST_PIXEL')

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def create_patch_object(self, context):
        quickpatch = bpy.data.objects.new(name="QuickPatch", object_data=self.mesh)
        quickpatch.matrix_world = self.active.matrix_world
        self.mesh.transform(self.active.matrix_world.inverted_safe())
        self.mesh.update()
        context.collection.objects.link(quickpatch)

        bpy.ops.object.select_all(action='DESELECT')
        quickpatch.select_set(True)
        context.view_layer.objects.active = quickpatch

    def create_patch_mesh(self, context, subdivisions, offset_patch=0, debug=False):
        if not self.mesh:
            self.mesh = bpy.data.meshes.new(name="QuickPatch")

        bmt = bmesh.new()
        bmt.from_mesh(self.active.evaluated_get(self.dg).to_mesh())

        bm = bmesh.new()
        bm.normal_update()
        bm.verts.ensure_lookup_table()

        for co in self.draw_coords:
            v = bm.verts.new()
            v.co = co

        face = bm.faces.new(bm.verts)

        face.normal_update()
        normal = face.normal.copy()

        if debug:
            origin = face.calc_center_median()
            draw_vector(normal, origin=origin, modal=False)

        factor = get_zoom_factor(context, average_locations([v.co.copy() for v in bm.verts]))

        if subdivisions:
            bmesh.ops.subdivide_edges(bm, edges=bm.edges, cuts=subdivisions, use_grid_fill=True)

        verts = [v for v in bm.verts if len(v.link_edges) > 2]

        for v in verts:
            _, hitlocation, _, _, _ = cast_obj_ray_from_point(v.co, direction=normal, candidates=[self.active], debug=False)

            if hitlocation:
                v.co = hitlocation

        if self.offset_patch:
            for v in bm.verts:
                avg_normal = (normal.normalized() + v.normal.normalized()) / 2

                v.co = v.co + avg_normal * self.offset_patch

        self.grid_fill(bm)

        for f in bm.faces:
            f.smooth = True

        corner_coords = []
        subd_coords = []

        for v in bm.verts:
            if len(v.link_edges) == 2:
                corner_coords.append(v.co.copy())
            else:
                subd_coords.append(v.co.copy())

        bm.to_mesh(self.mesh)
        bm.clear()
        bm.free()

        bmt.free()

        return factor, corner_coords, subd_coords

    def grid_fill(self, bm):
        border_edges = [e for e in bm.edges if not e.is_manifold]
        border_faces = [f for f in bm.faces if any(e in border_edges for e in f.edges)]

        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f not in border_faces], context='FACES')

        fill_edges = [e for e in bm.edges if not e.is_manifold and e not in border_edges]
        fill_verts = {v for e in fill_edges for v in e.verts}
        corner_verts = [v for v in fill_verts if len(v.link_edges) == 4]

        v = corner_verts[0]

        seq = []
        edge_seq = []

        while fill_verts:
            seq.append(v)
            fill_verts.remove(v)

            nextv = [e.other_vert(v) for e in v.link_edges if e in fill_edges and e.other_vert(v) not in seq]

            if nextv:
                edge_seq.append(bm.edges.get((v, nextv[0])))
                v = nextv[0]

            else:
                edge_seq.append(bm.edges.get((v, seq[0])))

        segments = int(len(edge_seq) / 4)

        seg1 = edge_seq[0:segments]
        seg3 = edge_seq[segments * 2: segments * 3]

        bmesh.ops.grid_fill(bm, edges=seg1 + seg3, use_interp_simple=False)
