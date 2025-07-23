import bpy
import bmesh

from typing import Union
from mathutils import Vector
import numpy as np

from . math import transform_coords

def get_bbox(mesh=None, coords=None):
    vert_count = len(mesh.vertices)
    coords = np.empty((vert_count, 3), float)
    mesh.vertices.foreach_get('co', np.reshape(coords, vert_count * 3))

    xmin = np.min(coords[:, 0])
    xmax = np.max(coords[:, 0])
    ymin = np.min(coords[:, 1])
    ymax = np.max(coords[:, 1])
    zmin = np.min(coords[:, 2])
    zmax = np.max(coords[:, 2])

    bbox = [Vector((xmin, ymin, zmin)),
            Vector((xmax, ymin, zmin)),
            Vector((xmax, ymax, zmin)),
            Vector((xmin, ymax, zmin)),
            Vector((xmin, ymin, zmax)),
            Vector((xmax, ymin, zmax)),
            Vector((xmax, ymax, zmax)),
            Vector((xmin, ymax, zmax))]

    xcenter = (xmin + xmax) / 2
    ycenter = (ymin + ymax) / 2
    zcenter = (zmin + zmax) / 2

    centers = [Vector((xmin, ycenter, zcenter)),
               Vector((xmax, ycenter, zcenter)),
               Vector((xcenter, ymin, zcenter)),
               Vector((xcenter, ymax, zcenter)),
               Vector((xcenter, ycenter, zmin)),
               Vector((xcenter, ycenter, zmax))]

    xdim = (bbox[1] - bbox[0]).length
    ydim = (bbox[2] - bbox[1]).length
    zdim = (bbox[4] - bbox[0]).length

    dimensions = Vector((xdim, ydim, zdim))

    return bbox, centers, dimensions

def get_coords_from_mesh(mesh, mx=None, offset=0, edge_indices=False) -> Union[list, tuple]:
    verts = mesh.vertices
    vert_count = len(verts)

    coords = np.empty((vert_count, 3), float)
    mesh.vertices.foreach_get('co', np.reshape(coords, vert_count * 3))

    if offset:
        normals = np.empty((vert_count, 3), float)
        mesh.vertices.foreach_get('normal', np.reshape(normals, vert_count * 3))

        coords = coords + normals * offset

    if mx:
        coords = transform_coords(coords, mx)

    else:
        coords = np.float32(coords)

    if edge_indices:
        edges = mesh.edges
        edge_count = len(edges)

        indices = np.empty((edge_count, 2), 'i')
        edges.foreach_get('vertices', np.reshape(indices, edge_count * 2))

        return coords, indices

    return coords

def unhide_deselect(mesh):
    polygons = len(mesh.polygons)
    edges = len(mesh.edges)
    vertices = len(mesh.vertices)

    mesh.polygons.foreach_set('hide', [False] * polygons)
    mesh.edges.foreach_set('hide', [False] * edges)
    mesh.vertices.foreach_set('hide', [False] * vertices)

    mesh.polygons.foreach_set('select', [False] * polygons)
    mesh.edges.foreach_set('select', [False] * edges)
    mesh.vertices.foreach_set('select', [False] * vertices)

    mesh.update()

def get_mesh_user_count(mesh):
    count = mesh.users

    if mesh.use_fake_user:
        count -= 1

    return count

def shade(mesh, smooth=True):
    mesh.polygons.foreach_set('use_smooth', [smooth] * len(mesh.polygons))
    mesh.update()

def get_eval_mesh(dg, obj, data_block=True):
    if data_block:
        eval_mesh = obj.evaluated_get(dg).to_mesh().copy()       # this will get you a mesh from curve objects too
    else:
        eval_mesh = obj.evaluated_get(dg).to_mesh()              # this will get you a mesh from curve objects too, even those without any thickness or extrusion!

    return eval_mesh

def join(target, objects, select=[]):
    mxi = target.matrix_world.inverted_safe()

    bm = bmesh.new()
    bm.from_mesh(target.data)
    bm.normal_update()
    bm.verts.ensure_lookup_table()

    select_layer = bm.faces.layers.int.get('Machin3FaceSelect')

    if not select_layer:
        select_layer = bm.faces.layers.int.new('Machin3FaceSelect')

    for idx, obj in enumerate(objects):
        mesh = obj.data
        mx = obj.matrix_world
        mesh.transform(mxi @ mx)

        bmm = bmesh.new()
        bmm.from_mesh(mesh)
        bmm.normal_update()
        bmm.verts.ensure_lookup_table()

        obj_select_layer = bmm.faces.layers.int.get('Machin3FaceSelect')

        if not obj_select_layer:
            obj_select_layer = bmm.faces.layers.int.new('Machin3FaceSelect')

        for f in bmm.faces:
            f[obj_select_layer] = idx + 1

        bmm.to_mesh(mesh)
        bmm.free()

        bm.from_mesh(mesh)

        bpy.data.meshes.remove(mesh, do_unlink=True)

    if select:
        for f in bm.faces:
            if f[select_layer] in select:
                f.select_set(True)

    bm.to_mesh(target.data)
    bm.free()
