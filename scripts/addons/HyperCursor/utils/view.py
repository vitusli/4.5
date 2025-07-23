from math import sqrt
import bpy
import bmesh
from typing import Tuple
from mathutils import Vector
from bpy_extras.view3d_utils import location_3d_to_region_2d, region_2d_to_origin_3d, region_2d_to_vector_3d
from typing import Union

from . import ui

from . collection import is_collection_visible
from . math import get_loc_matrix, get_sca_matrix

cache = {}

def focus_on_cursor(focusmode='SOFT', ignore_selection=False, cache_bm=False):
    scene = bpy.context.scene
    mode = bpy.context.mode

    if mode == 'OBJECT':

        if ignore_selection:
            sel = [obj for obj in bpy.context.selected_objects]

            for obj in sel:
                obj.select_set(False)

        empty = bpy.data.objects.new(name="focus", object_data=None)
        scene.collection.objects.link(empty)
        empty.select_set(True)

        empty.matrix_world = scene.cursor.matrix
        empty.scale *= scene.HC.focus_proximity

        bpy.ops.view3d.view_selected('INVOKE_DEFAULT' if focusmode == 'SOFT' else 'EXEC_DEFAULT')

        bpy.data.objects.remove(empty, do_unlink=True)

        if ignore_selection:
            for obj in sel:
                obj.select_set(True)

    elif mode == 'EDIT_MESH':
        global cache

        active = bpy.context.active_object
        mxi = active.matrix_world.inverted_safe()

        scale = scene.HC.focus_proximity
        loc = mxi @ scene.cursor.location

        if cache_bm and active.name in cache:
            bm = cache[active.name]

        else:
            bm = bmesh.from_edit_mesh(active.data)
            bm.normal_update()
            bm.verts.ensure_lookup_table()

        if cache_bm:
            cache[active.name] = bm

        sel_verts = [v for v in bm.verts if v.select]
        sel_edges = [e for e in bm.edges if e.select]
        sel_faces = [f for f in bm.faces if f.select]

        if ignore_selection:
            for v in sel_verts:
                v.select_set(False)

            bm.select_flush(False)

        coords = (Vector((-1, 1, -1)), Vector((1, 1, -1)), Vector((1, -1, -1)), Vector((-1, -1, -1)),
                  Vector((-1, 1, 1)), Vector((1, 1, 1)), Vector((1, -1, 1)), Vector((-1, -1, 1)))

        verts = []

        for co in coords:
            v = bm.verts.new(get_loc_matrix(loc) @ get_sca_matrix(scale * mxi.to_scale()) @ co)
            v.select_set(True)
            verts.append(v)

        indices = [(0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7), (7, 4), (0, 4), (1, 5), (2, 6), (3, 7)]

        for ids in indices:
            e = bm.edges.new([verts[i] for i in ids])
            e.select_set(True)

        indices = [(0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0), (0, 1, 2, 3), (4, 7, 6, 5)]

        for ids in indices:
            f = bm.faces.new([verts[i] for i in ids])
            f.select_set(True)

        bpy.ops.view3d.view_selected('INVOKE_DEFAULT' if focusmode == 'SOFT' else 'EXEC_DEFAULT')

        for v in verts:
            bm.verts.remove(v)

        if ignore_selection:
            for v in sel_verts:
                v.select_set(True)

            for e in sel_edges:
                e.select_set(True)

            for f in sel_faces:
                f.select_set(True)

def clear_focus_cache():
    global cache

    cache = {}

def get_view_bbox(context, bbox, border_gap=200):
    ui_scale = ui.get_scale(context)
    gap = border_gap * sqrt(ui_scale)

    coords = []

    for co in bbox:
        coords.append(get_location_2d(context, co, default=Vector((context.region.width / 2, context.region.height / 2))))
    xmin = round(min(context.region.width - gap, max(gap, min(coords, key=lambda x: x[0])[0])))
    xmax = round(min(context.region.width - gap, max(gap, max(coords, key=lambda x: x[0])[0])))

    ymin = round(min(context.region.height - gap, max(gap, min(coords, key=lambda x: x[1])[1])))
    ymax = round(min(context.region.height - gap, max(gap, max(coords, key=lambda x: x[1])[1])))

    return [Vector((xmin, ymin)), Vector((xmax, ymin)), Vector((xmax, ymax)), Vector((xmin, ymax))]

def get_view_origin_and_dir(context, coord=None) -> Tuple[Vector, Vector]:
    if not coord:
        coord = Vector((context.region.width / 2, context.region.height / 2))

    clamp = 1000 if context.region_data.view_perspective == 'ORTHO' else None

    view_origin = region_2d_to_origin_3d(context.region, context.region_data, coord, clamp=clamp)
    view_dir = region_2d_to_vector_3d(context.region, context.region_data, coord)

    return view_origin, view_dir

def is_local_view():
    view = bpy.context.space_data

    if view and view.type == 'VIEW_3D':
        return bool(view.local_view)

def is_object_in_local_view(dg, obj):
    view = bpy.context.space_data

    if view and view.type == 'VIEW_3D':
        return bool(view.local_view) and obj.evaluated_get(dg).local_view_get(view)

def add_obj_to_local_view(obj:Union[bpy.types.Object, list, set]):
    view = bpy.context.space_data

    if view and view.type == 'VIEW_3D' and view.local_view:
        objects = obj if type(obj) in [list, set] else [obj]

        for obj in objects:
            obj.local_view_set(view, True)

def remove_obj_from_local_view(obj:Union[bpy.types.Object, list, set]):
    view = bpy.context.space_data

    if view and view.type == 'VIEW_3D' and view.local_view:
        objects = obj if type(obj) in [list, set] else [obj]

        for obj in objects:
            obj.local_view_set(view, False)

def visible_get(obj, depsgraph=None, ray_visibility=False, debug=False) -> dict:
    vis = {'visible': obj.visible_get(),

           'scene': is_obj_in_scene(obj),
           'viewlayer': is_obj_on_viewlayer(obj),
           'visible_collection': is_obj_in_visible_collection(obj),

           'local_view': None if not is_local_view() else is_object_in_local_view(depsgraph, obj) if depsgraph else False,   # None if local view is not used, otherwise check if obj is in local view IF the dg is passed in, otherwise set to False - the distinction beteed None and False is useful
           'hide': obj.hide_get(),                                                                                           # but could still be useful for debugging (when dg would be passed in)
           'hide_viewport': obj.hide_viewport,
           'hide_render': obj.hide_render,                                                                                   # NOTE: hide_render is only relevant for camera rendering, not for viewport rendering, nor basic viewport display

           'select': obj.select_get(),                                                                                       # get the selection state too actually, while at it, useful for restore_visibility()

           'meta': None}

    if ray_visibility:                                                                                                       # NOTE: ray visibility on the other hand, does affect viewport rendering, even eevee/material shading
        vis['visible_ray'] = {'visible_camera': obj.visible_camera,
                              'visible_diffuse': obj.visible_diffuse,
                              'visible_glossy': obj.visible_glossy,
                              'visible_transmission': obj.visible_transmission,
                              'visible_volume_scatter': obj.visible_volume_scatter,
                              'visible_shadow': obj.visible_shadow}

    if not vis['visible']:
        if vis['scene']:
            if vis['viewlayer']:
                if vis['visible_collection']:

                    if vis['local_view'] in [True, None]:

                        if not vis['hide_viewport']:

                            if vis['hide']:
                                vis['meta'] = 'HIDE'

                        else:
                            vis['meta'] = 'HIDE_VIEWPORT'

                    else:
                        vis['meta'] = 'LOCAL_VIEW'

                else:
                    vis['meta'] = 'HIDDEN_COLLECTION'

            else:
                vis['meta'] = 'VIEWLAYER'

        else:
            vis['meta'] = 'SCENE'

    if debug:
        print("", obj.name, "✔" if vis['visible'] else "❌", vis['meta'] if not vis['visible'] else '')

    return vis

def is_obj_in_scene(obj):
    return obj.name in bpy.context.scene.objects

def is_obj_on_viewlayer(obj):
    return obj.name in bpy.context.view_layer.objects

def is_obj_in_visible_collection(obj):
    return any(is_collection_visible(col) for col in obj.users_collection)

def ensure_visibility(context, obj: Union[bpy.types.Object, list[bpy.types.Object]], scene=True, viewlayer=True, hidden_collection=True, local_view=True, unhide=True, unhide_viewport=True, select=False, debug=False):

    objects = obj if type(obj) in [list, set] else [obj]

    if debug:
        print()

        for obj in objects:
            vis = visible_get(obj, debug=False)
            print(obj.name, "✔" if vis['visible'] else "❌", vis['meta'] if not vis['visible'] else '')

    for obj in objects:

        is_in_scene = is_obj_in_scene(obj)
        is_on_viewlayer = is_obj_on_viewlayer(obj)
        is_in_visible_collection = is_obj_in_visible_collection(obj)

        if scene and not is_in_scene:
            context.scene.collection.objects.link(obj)
            obj.select_set(False)

            is_in_scene = True
            is_on_viewlayer = True
            is_in_visible_collection = True#

            if debug:
                print(" added", obj.name, "to scene")

        if viewlayer and is_in_scene and not is_on_viewlayer:
            context.scene.collection.objects.link(obj)
            obj.select_set(False)

            is_in_scene = True
            is_on_viewlayer = True
            is_in_visible_collection = True

            if debug:
                print(" added", obj.name, "to viewlayer")

        if hidden_collection and is_in_scene and is_on_viewlayer and not is_in_visible_collection:
            context.scene.collection.objects.link(obj)
            obj.select_set(False)

            is_in_scene = True
            is_on_viewlayer = True
            is_in_visible_collection = True

            if debug:
                print(" added", obj.name, "to visible collection")

        if local_view:
            add_obj_to_local_view(objects)

            if debug and is_local_view():
                print(" ensured", obj.name, "is in local view")

        if unhide:
            if obj.hide_get():
                obj.hide_set(False)

        if unhide_viewport:
            if obj.hide_viewport:
                obj.hide_viewport = False

        if select:
            if obj.visible_get():
                obj.select_set(True)

def restore_visibility(obj, data:dict):
    if is_obj_on_viewlayer(obj):

        if (state := data.get('select')) and state != obj.select_get():
            obj.select_set(state)

        if (state := data.get('hide')) and state != obj.hide_get():
            obj.hide_set(state)

    if (state := data.get('hide_viewport')) and state != obj.hide_viewport:
        obj.hide_viewport = state

    if is_local_view() and (state := data.get('local_view')) is not None:
        if state:
            remove_obj_from_local_view(obj)
        else:
            add_obj_to_local_view(obj)

    if (meta := data.get('meta')) and meta in ['SCENE', 'VIEWLAYER', 'HIDDEN_COLLECTION']:
        mcol = bpy.context.scene.collection

        if obj.name in mcol.objects:
            mcol.objects.unlink(obj)

def get_location_2d(context, co3d, default=(0, 0), debug=False):
    if default == 'OFF_SCREEN':
        default = Vector((-1000, -1000))
    co2d = Vector(round(i) for i in location_3d_to_region_2d(context.region, context.region_data, co3d, default=default))
    if debug:
        print(tuple(co3d), "is", tuple(co2d))

    return co2d
