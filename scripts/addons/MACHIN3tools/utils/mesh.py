import bpy
import bmesh
from mathutils import Vector
import numpy as np

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

def get_coords(mesh, mx=None, offset=0, indices=False):
    verts = mesh.vertices

    if verts:
        vert_count = len(verts)

        coords = np.empty((vert_count, 3), float)
        mesh.vertices.foreach_get('co', np.reshape(coords, vert_count * 3))

        if offset:
            normals = np.empty((vert_count, 3), float)
            mesh.vertices.foreach_get('normal', np.reshape(normals, vert_count * 3))

            coords = coords + normals * offset

        if mx:
            coords_4d = np.ones((vert_count, 4), dtype=float)
            coords_4d[:, :-1] = coords

            coords = np.einsum('ij,aj->ai', mx, coords_4d)[:, :-1]

        coords = np.float32(coords)

        if indices:
            edges = mesh.edges
            edge_count = len(edges)

            indices = np.empty((edge_count, 2), 'i')
            edges.foreach_get('vertices', np.reshape(indices, edge_count * 2))

            return coords, indices

        return coords

    if indices:
        return [], []
    return []

def hide(mesh):
    mesh.polygons.foreach_set('hide', [True] * len(mesh.polygons))
    mesh.edges.foreach_set('hide', [True] * len(mesh.edges))
    mesh.vertices.foreach_set('hide', [True] * len(mesh.vertices))

    mesh.update()

def unhide(mesh):
    mesh.polygons.foreach_set('hide', [False] * len(mesh.polygons))
    mesh.edges.foreach_set('hide', [False] * len(mesh.edges))
    mesh.vertices.foreach_set('hide', [False] * len(mesh.vertices))

    mesh.update()

def unhide_select(mesh):
    polygons = len(mesh.polygons)
    edges = len(mesh.edges)
    vertices = len(mesh.vertices)

    mesh.polygons.foreach_set('hide', [False] * polygons)
    mesh.edges.foreach_set('hide', [False] * edges)
    mesh.vertices.foreach_set('hide', [False] * vertices)

    mesh.polygons.foreach_set('select', [True] * polygons)
    mesh.edges.foreach_set('select', [True] * edges)
    mesh.vertices.foreach_set('select', [True] * vertices)

    mesh.update()

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

def select(mesh):
    mesh.polygons.foreach_set('select', [True] * len(mesh.polygons))
    mesh.edges.foreach_set('select', [True] * len(mesh.edges))
    mesh.vertices.foreach_set('select', [True] * len(mesh.vertices))

    mesh.update()

def deselect(mesh):
    mesh.polygons.foreach_set('select', [False] * len(mesh.polygons))
    mesh.edges.foreach_set('select', [False] * len(mesh.edges))
    mesh.vertices.foreach_set('select', [False] * len(mesh.vertices))

    mesh.update()

def get_eval_mesh(dg, obj, data_block=True):
    if data_block:
        eval_mesh = obj.evaluated_get(dg).to_mesh().copy()       # this will get you a mesh from curve objects too

    else:
        eval_mesh = obj.evaluated_get(dg).to_mesh()              # this will get you a mesh from curve objects too
    return eval_mesh

def blast(mesh, prop, type):
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.normal_update()
    bm.verts.ensure_lookup_table()

    if prop == "hidden":
        faces = [f for f in bm.faces if f.hide]

    elif prop == "visible":
        faces = [f for f in bm.faces if not f.hide]

    elif prop == "selected":
        faces = [f for f in bm.faces if f.select]

    bmesh.ops.delete(bm, geom=faces, context=type)

    bm.to_mesh(mesh)
    bm.clear()

def smooth(mesh, smooth=True):
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.normal_update()
    bm.verts.ensure_lookup_table()

    for f in bm.faces:
        f.smooth = smooth

    bm.to_mesh(mesh)
    bm.free()

def flip_normals(mesh):
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.normal_update()

    bmesh.ops.reverse_faces(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()

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
