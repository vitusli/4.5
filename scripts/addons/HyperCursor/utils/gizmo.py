import bpy
import bmesh

from mathutils import Vector, Matrix

from . bmesh import ensure_gizmo_layers, get_face_angle
from . cursor import get_cursor_2d
from . modifier import source_poll
from . object import is_decalmachine_object, is_plug_handle, is_valid_object
from . system import printd
from . ui import force_geo_gizmo_update
from . view import get_view_origin_and_dir

def print_shape():
    active = bpy.context.active_object

    if active:
        active.data.calc_loop_triangles()

        coords = [tuple(active.data.vertices[idx].co) for tri in active.data.loop_triangles for idx in tri.vertices]
        print(coords)
        print(len(coords))

def is_modal(self):
    return any(gzm.is_modal for gzm in self.gizmos)

def geometry_gizmo_poll(context, mode='EDIT'):
    active = context.active_object
    sel = context.selected_objects
    hc = context.scene.HC

    if hc.draw_HUD:

        if active and active.HC.ishyper:

            if active.select_get() and len(sel) == 1:

                if active.visible_get() and active.type == 'MESH' and not active.data.library:

                    if not source_poll(context, active):

                        if active.HC.geometry_gizmos_show and active.HC.geometry_gizmos_edit_mode == mode:

                            if active.HC.ishyperbevel:
                                return True

                            if mode == 'EDIT':
                                if facecount := len(active.data.polygons):
                                    if active.HC.objtype == 'CUBE':
                                        return facecount <= active.HC.geometry_gizmos_show_cube_limit

                                    elif active.HC.objtype == 'CYLINDER':
                                        return len(active.data.edges) <= active.HC.geometry_gizmos_show_cylinder_limit

                            elif mode == 'SCALE':
                                return len(active.data.polygons) <= active.HC.geometry_gizmos_show_limit

    return False

def object_gizmo_poll(context):
    hc = context.scene.HC

    if hc.draw_HUD and hc.show_object_gizmos:
        active = context.active_object
        sel = context.selected_objects

        return active and active.HC.ishyper and not (is_decalmachine_object(active) or is_plug_handle(active)) and active.visible_get() and active.select_get() and len(sel) == 1

def objects_gizmo_poll(context):
    hc = context.scene.HC

    if hc.draw_HUD and hc.show_object_gizmos:
        sel = [obj for obj in context.selected_objects if obj.visible_get() and not (is_decalmachine_object(obj) or is_plug_handle(obj)) and not (obj.library or (obj.data and obj.data.library))]

        return len(sel) >= 1

def create_button_gizmo(self, context, operator='', args={}, icon='MESH_CYLINDER', location='CURSOR', scale=0.13, offset=(0, 0)):
    gzm = self.gizmos.new("GIZMO_GT_button_2d")

    op = gzm.target_set_operator(operator)
    for prop, value in args.items():
        setattr(op, prop, value)

    gzm.icon = icon

    if location == 'CURSOR':
        gzm.matrix_basis = context.scene.cursor.matrix

    else:
        gzm.matrix_basis.translation = location

    gzm.scale_basis = scale

    if offset != (0, 0):
        offset_button_gizmo(context, gzm, Vector(offset))

    return gzm

def setup_geo_gizmos(context, obj, setup_gizmos=True, clear_gizmos=False, edges=True, faces=True, angle=20,  remove_redundant_edges=False, skip_cylinder_quad_faces=True, skip_incomplete_faces=True):
    if len(obj.data.polygons) > obj.HC.geometry_gizmos_show_limit:
        msg = f"'{obj.name}' face count is too high for geometry gizmos."
        print(f"WARNING: {msg}")
        return msg

    elif obj.HC.ishyperbevel:
        msg = f"'{obj.name}' is a Hyper Bevel, skipping angle based geo gizmo setup."
        print(f"WARNING: {msg}")
        return msg

    if context.mode == 'EDIT_MESH':
        bm = bmesh.from_edit_mesh(obj.data)
        bm.normal_update()
        bm.verts.ensure_lookup_table()

    else:
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bm.normal_update()
        bm.verts.ensure_lookup_table()

    edge_glayer, face_glayer = ensure_gizmo_layers(bm)

    if clear_gizmos:
        if edges:
            for e in bm.edges:
                e[edge_glayer] = 0

        if faces:
            for f in bm.faces:
                f[face_glayer] = 0

    elif setup_gizmos:
        if remove_redundant_edges:
            redundant = [e for e in bm.edges if len(e.link_faces) == 2 and round(get_face_angle(e), 2) == 0]

            if redundant:
                bmesh.ops.dissolve_edges(bm, edges=redundant, use_verts=True)

        if edges:
            for e in bm.edges:

                if len(e.link_faces) == 2:
                    edge_angle = get_face_angle(e)

                    e[edge_glayer] = edge_angle >= angle

                else:
                    e[edge_glayer] = 1

        if faces:
            for f in bm.faces:

                if obj.HC.objtype == 'CYLINDER' and skip_cylinder_quad_faces and len(f.edges) == 4:
                    f[face_glayer] = 0

                elif skip_incomplete_faces and not all(e[edge_glayer] for e in f.edges):
                    f[face_glayer] = 0

                else:
                    f[face_glayer] = any([get_face_angle(e, fallback=0) >= angle for e in f.edges])

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    if context.mode == 'EDIT_MESH':
        bmesh.update_edit_mesh(obj.data)

    else:
        bm.to_mesh(obj.data)
        bm.free()

    force_geo_gizmo_update(context)

    return True

def offset_button_gizmo(context, gzm, offset=(0, 0), loc2d=None):
    if not loc2d:
        loc2d = get_cursor_2d(context)

    loc2d_offset = loc2d + Vector(offset) * context.preferences.system.ui_scale

    view_origin, view_dir = get_view_origin_and_dir(context, loc2d_offset)

    button_3d = view_origin + view_dir * context.space_data.clip_start * 1.5

    gzm.matrix_basis = Matrix.Translation(button_3d)

def hide_gizmos(self, context, hypercursor=True, buttons=[], object=True, geometry=True, hud=True, debug=False):

    self.hidden_gizmos = {}

    if any([hypercursor, buttons, object, hud]):
        self.hidden_gizmos['SCENE'] = context.scene

    if any([geometry]):
        active = context.active_object

        if active and active.select_get() and active.HC.ishyper:
            self.hidden_gizmos['OBJECT'] = context.active_object

    if scene := self.hidden_gizmos.get('SCENE', None):
        hc = scene.HC

        if hypercursor:
            self.hidden_gizmos['show_gizmos'] = hc.show_gizmos
            hc.show_gizmos = False

        for button in buttons:
            prop =f"show_button_{button.lower()}"

            self.hidden_gizmos[prop] = getattr(hc, prop)
            setattr(hc, prop, False)

        if object:
            self.hidden_gizmos['show_object_gizmos'] = hc.show_object_gizmos
            hc.show_object_gizmos = False

        if hud:
            self.hidden_gizmos['draw_HUD'] = hc.draw_HUD
            hc.draw_HUD = False

    if obj := self.hidden_gizmos.get('OBJECT', None):
        hc = obj.HC

        if geometry and obj.type == 'MESH':
            self.hidden_gizmos['geometry_gizmos_show'] = hc.geometry_gizmos_show
            hc.geometry_gizmos_show = False

    if debug:
        printd(self.hidden_gizmos, name="hiding gizmos")

def restore_gizmos(self, debug=False):

    hidden = self if type(self) is dict else getattr(self, 'hidden_gizmos', None)

    if debug:
        printd(hidden, name="restoring gizmos")

    if hidden:
        if scene := hidden.get('SCENE', None):
            hc = scene.HC

            if 'show_gizmos' in hidden:
                hc.show_gizmos = hidden['show_gizmos']

            for button in ['HISTORY',  'FOCUS', 'SETTINGS', 'CAST', 'OBJECT']:
                prop =f"show_button_{button.lower()}"

                if prop in hidden:
                    setattr(hc, prop, hidden[prop])

            if 'show_object_gizmos' in hidden:
                hc.show_object_gizmos = hidden['show_object_gizmos']

            if 'draw_HUD' in hidden:
                hc.draw_HUD = hidden['draw_HUD']

            if 'draw_pipe_HUD' in hidden:
                hc.draw_pipe_HUD = hidden['draw_pipe_HUD']

        if obj := hidden.get('OBJECT', None):
            if is_valid_object(obj):
                hc = obj.HC

                if 'geometry_gizmos_show' in hidden:
                    hc.geometry_gizmos_show = hidden['geometry_gizmos_show']

            else:
                print("WARNING: Object has become invalid, can't restore geometry gizmos")
