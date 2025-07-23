import bpy
from mathutils import Vector, Quaternion
import bmesh

from . math import get_center_between_verts, create_rotation_matrix_from_edge, create_rotation_matrix_from_face
from . view import get_location_2d

def set_cursor(matrix=None, location=Vector(), rotation=Quaternion()):
    cursor = bpy.context.scene.cursor

    if matrix:
        cursor.location = matrix.to_translation()
        cursor.rotation_quaternion = matrix.to_quaternion()
        cursor.rotation_mode = 'QUATERNION'

    else:
        cursor.location = location

        if cursor.rotation_mode == 'QUATERNION':
            cursor.rotation_quaternion = rotation

        elif cursor.rotation_mode == 'AXIS_ANGLE':
            cursor.rotation_axis_angle = rotation.to_axis_angle()

        else:
            cursor.rotation_euler = rotation.to_euler(cursor.rotation_mode)

def set_cursor_to_geo(context, obj, edgeidx=None, faceidx=None):
    bm = bmesh.new()
    bm.from_mesh(obj.data)

    mx = obj.matrix_world

    if edgeidx is not None:

        bm.edges.ensure_lookup_table()
        edge = bm.edges[edgeidx]

        loc = mx @ get_center_between_verts(*edge.verts)
        rot = create_rotation_matrix_from_edge(context, mx, edge)

        set_cursor(location=loc, rotation=rot.to_quaternion())

    elif faceidx is not None:

        bm.faces.ensure_lookup_table()
        face = bm.faces[faceidx]

        loc = mx @ face.calc_center_median()
        rot = create_rotation_matrix_from_face(context, mx, face)

        set_cursor(location=loc, rotation=rot.to_quaternion())

def set_cursor_2d(context):
    from .. import HyperCursorManager as HC

    loc2d = get_location_2d(context, context.scene.cursor.location, default='OFF_SCREEN')
    HC.props['cursor_2d'] = loc2d
    return loc2d

def get_cursor_2d(context):
    from .. import HyperCursorManager as HC

    if context.scene.HC.show_gizmos:
        return HC.props['cursor_2d']

    else:
        return set_cursor_2d(context)
