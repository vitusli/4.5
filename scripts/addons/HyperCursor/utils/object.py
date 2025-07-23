from math import degrees
import bpy
import bmesh

from bpy.types import Macro
from mathutils import Matrix, Vector

from typing import Union
from uuid import uuid4
import numpy as np

from . bmesh import ensure_edge_glayer
from . math import average_locations, create_coords_bbox, flatten_matrix, get_loc_matrix, get_sca_matrix
from . mesh import get_bbox, get_coords_from_mesh, get_eval_mesh, join, unhide_deselect
from . modifier import add_displace, get_mod_obj, is_mod_obj, remove_mod
from . registration import get_prefs
from . system import printd
from . ui import get_scale, get_zoom_factor
from . view import ensure_visibility, restore_visibility, visible_get
from . workspace import get_3dview_space_from_context

def remove_obj(obj):
    if not obj.data:
        bpy.data.objects.remove(obj, do_unlink=True)

    elif obj.data.users > 1:
        bpy.data.objects.remove(obj, do_unlink=True)

    elif obj.type == 'MESH':
        bpy.data.meshes.remove(obj.data, do_unlink=True)

    else:
        bpy.data.objects.remove(obj, do_unlink=True)

def is_removable(obj, ignore_users=[], mods=True, children=True, debug=False):
    if debug:
        print(f"\nchecking if object {obj.name} can/should be removed")

    if children:
        if obj.children:
            if debug:
                print(f" object has {len(obj.children)} children, and so can't be removed")
            return False

    if mods:
        for ob in bpy.data.objects:
            for mod in ob.modifiers:

                if mod in ignore_users:
                    if debug:
                        print(f" ignoring {mod.name} as a potential user")
                    continue

                if get_mod_obj(mod) == obj:
                    if debug:
                        print(f" object is used by mod '{mod.name}' of '{mod.id_data.name}', and so can't be removed")
                    return False

    if debug:
        print(" object does not seem to be used, and so can be removed")
    return True

def flatten(obj, depsgraph=None, preserve_data_layers=False, keep_mods=[]):
    if not depsgraph:
        depsgraph = bpy.context.evaluated_depsgraph_get()

    oldmesh = obj.data

    if preserve_data_layers:
        obj.data = bpy.data.meshes.new_from_object(obj.evaluated_get(depsgraph), preserve_all_data_layers=True, depsgraph=depsgraph)
    else:
        obj.data = bpy.data.meshes.new_from_object(obj.evaluated_get(depsgraph))

    if keep_mods:
        for mod in obj.modifiers:
            if mod not in keep_mods:
                obj.modifiers.remove(mod)

    else:
        obj.modifiers.clear()

    if not oldmesh.users:
        bpy.data.meshes.remove(oldmesh, do_unlink=True)

def meshcut(context, obj, operands):
    dg = context.evaluated_depsgraph_get()

    unhide_deselect(obj.data)

    for cutter in operands:

        unhide_deselect(cutter.data)

        if cutter.modifiers:
            flatten(cutter, dg)

        cutter.data.materials.clear()

    join(obj, operands, select=[i + 1 for i in range(len(operands))])

    bpy.ops.object.select_all(action='DESELECT')
    context.view_layer.objects.active = obj
    obj.select_set(True)

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.intersect(separate_mode='ALL')
    bpy.ops.object.mode_set(mode='OBJECT')

    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.normal_update()
    bm.verts.ensure_lookup_table()

    select_layer = bm.faces.layers.int.get('Machin3FaceSelect')
    edge_glayer = ensure_edge_glayer(bm)

    cutter_faces = [f for f in bm.faces if f[select_layer] > 0]

    if cutter_faces:
        bmesh.ops.delete(bm, geom=cutter_faces, context='FACES')

    non_manifold = [e for e in bm.edges if not e.is_manifold]

    verts = set()

    for e in non_manifold:
        e[edge_glayer] = 1

        verts.update(e.verts)

    bmesh.ops.remove_doubles(bm, verts=list({v for e in non_manifold for v in e.verts}), dist=0.0001)

    straight_edged = []

    for v in verts:
        if v.is_valid and len(v.link_edges) == 2:
            e1 = v.link_edges[0]
            e2 = v.link_edges[1]

            vector1 = e1.other_vert(v).co - v.co
            vector2 = e2.other_vert(v).co - v.co

            angle = degrees(vector1.angle(vector2))

            if 179 <= angle <= 181:
                straight_edged.append(v)

    bmesh.ops.dissolve_verts(bm, verts=straight_edged)

    bm.faces.layers.int.remove(select_layer)

    bm.to_mesh(obj.data)
    bm.free()

def compensate_children(obj, oldmx, newmx):
    deltamx = newmx.inverted_safe() @ oldmx
    children = [c for c in obj.children]

    for c in children:
        pmx = c.matrix_parent_inverse
        c.matrix_parent_inverse = deltamx @ pmx

def set_obj_origin(obj, mx, bm=None, decalmachine=False, meshmachine=False, force_quat_mode=False):

    if force_quat_mode:
        obj.rotation_mode = 'QUATERNION'

    omx = obj.matrix_world.copy()

    children = [c for c in obj.children]
    compensate_children(obj, omx, mx)

    deltamx = mx.inverted_safe() @ obj.matrix_world

    obj.matrix_world = mx

    if bm:
        bmesh.ops.transform(bm, verts=bm.verts, matrix=deltamx)
        bmesh.update_edit_mesh(obj.data)
    else:
        obj.data.transform(deltamx)

    if obj.type == 'MESH':
        obj.data.update()

    if decalmachine and children:

        for c in [c for c in children if c.DM.isdecal and c.DM.decalbackup]:
            backup = c.DM.decalbackup
            backup.DM.backupmx = flatten_matrix(deltamx @ backup.DM.backupmx)

    if meshmachine:

        for stash in obj.MM.stashes:

            if stash.obj:

                if getattr(stash, 'version', False) and float('.'.join([v for v in stash.version.split('.')[:2]])) >= 0.7:
                    stashdeltamx = stash.obj.MM.stashdeltamx

                    if stash.self_stash:
                        if stash.obj.users > 2:
                            print(f"INFO: Duplicating {stash.name}'s stashobj {stash.obj.name} as it's used by multiple stashes")

                            dup = stash.obj.copy()
                            dup.data = stash.obj.data.copy()
                            stash.obj = dup

                    stash.obj.MM.stashdeltamx = flatten_matrix(deltamx @ stashdeltamx)
                    stash.obj.MM.stashorphanmx = flatten_matrix(mx)

                    stash.self_stash = False

                else:
                    stashdeltamx = stash.obj.MM.stashtargetmx.inverted_safe() @ stash.obj.MM.stashmx

                    stash.obj.MM.stashmx = flatten_matrix(omx @ stashdeltamx)
                    stash.obj.MM.stashtargetmx = flatten_matrix(mx)

                stash.obj.data.transform(deltamx)
                stash.obj.matrix_world = mx

def is_uniform_scale(obj):
    return all([round(s, 6) == round(obj.scale[0], 6) for s in obj.scale])

def has_bbox(obj):
    return obj.bound_box and not all(Vector(co) == Vector() for co in obj.bound_box)

def get_eval_bbox(obj, advanced=False) -> Union[list, tuple]:
    if icol := is_instance_collection(obj):
        bbox, centers, dimensions = get_instance_collection_bbox(obj, icol)

        if not bbox:
            bbox, centers, dimensions = get_instance_collection_bbox(obj, icol, exclude_wire_objects=False)

        if advanced:
            return bbox, centers, dimensions

        else:
            return bbox

    else:
        bbox = [Vector(obj.bound_box[0]),
                Vector(obj.bound_box[4]),
                Vector(obj.bound_box[7]),
                Vector(obj.bound_box[3]),
                Vector(obj.bound_box[1]),
                Vector(obj.bound_box[5]),
                Vector(obj.bound_box[6]),
                Vector(obj.bound_box[2])]

        if advanced:
            centers = [average_locations([bbox[0], bbox[3], bbox[4], bbox[7]]),
                    average_locations([bbox[1], bbox[2], bbox[5], bbox[6]]),
                    average_locations([bbox[0], bbox[1], bbox[4], bbox[5]]),
                    average_locations([bbox[2], bbox[3], bbox[6], bbox[7]]),
                    average_locations([bbox[0], bbox[1], bbox[2], bbox[3]]),
                    average_locations([bbox[4], bbox[5], bbox[6], bbox[7]])]

            return bbox, centers, obj.dimensions

        else:
            return bbox

def get_instance_collection_bbox(empty, col, exclude_wire_objects=True):
    def get_instance_collection_bbox_recursively(col_coords, obj, col, mx):
        offsetmx = get_loc_matrix(col.instance_offset)
        instance_mx = mx @ obj.matrix_world @ offsetmx.inverted_safe()

        for ob in col.objects:
            if ((exclude_wire_objects and ob.display_type not in ['WIRE', 'BOUNDS']) or not exclude_wire_objects) and has_bbox(ob):
                bbox = [instance_mx @ ob.matrix_world @ co for co in get_eval_bbox(ob)]
                col_coords.extend(bbox)

            elif icol := is_instance_collection(ob):
                get_instance_collection_bbox_recursively(col_coords, ob, icol, instance_mx)

    coords = []

    get_instance_collection_bbox_recursively(coords, empty, col, empty.matrix_world.inverted_safe())

    if coords:
        bbox, centers, dimensions = create_coords_bbox(coords)
        return bbox, centers, get_sca_matrix(empty.matrix_world.decompose()[2]) @ dimensions

    return [], [], Vector()

def get_min_dim(obj, world_space=True):
    dims = [d for d in get_bbox(obj.data)[2] if d]

    if world_space:
        mx = obj.matrix_world
        scale_mx = get_sca_matrix(mx.decompose()[2])
        return min(scale_mx @ Vector(dims).resized(3))

    else:
        return min(dims)

def duplicate_objects(context, objects, linked=False, debug=False):
    from .. import HyperCursorManager as HC

    bpy.ops.object.select_all(action='DESELECT')

    originals = {str(uuid4()): (obj, visible_get(obj), obj.use_fake_user) for obj in objects}

    for dup_hash, (ob, vis, fake_user) in originals.items():
        if debug:
            print(ob.name, dup_hash, ", is visible:", vis['visible'], ", meta:", vis['meta'], ", fake user:", fake_user)

        ob.M3.dup_hash = dup_hash
        ensure_visibility(context, ob, select=True)

    bpy.ops.object.duplicate(linked=linked)

    duplicates = {}

    for dup in context.selected_objects:
        orig, vis, fake_user = originals[dup.M3.dup_hash]

        if debug:
            print(orig.name, "-", dup.name, ", was visible:", vis['visible'], ", was in local view:", vis['meta'], ", was fake user:", fake_user)

        duplicates[dup] = {
            'original': orig,
            'vis': vis,
            'fake_user': fake_user,
        }

        for ob in [orig, dup]:
            restore_visibility(ob, vis)

            ob.use_fake_user = fake_user

            ob.M3.dup_hash = ''

        if HC.get_addon('MACHIN3tools'):
            M3 = HC.addons['machin3tools']['module']

            if dup.M3.is_group_empty:
                M3.utils.group.ensure_internal_index_group_name(dup)

    if debug:
        printd(duplicates)

    return duplicates

def is_wire_object(obj, wire=True, bounds=True, empty=True, instance_collection=False, curve=True):
    if wire and obj.display_type == 'WIRE':
        return True

    elif bounds and obj.display_type == 'BOUNDS':
        return True

    elif empty and obj.type == 'EMPTY':

        if obj.instance_collection:
            return instance_collection

        else:
            return not obj.empty_display_type == 'IMAGE'

    elif curve and obj.type == 'CURVE' and obj.data.bevel_depth == 0 and obj.data.extrude == 0:
        return True

def is_valid_object(obj):
    return obj and ' invalid>' not in str(obj)

def is_decalmachine_object(obj):
    return getattr(obj, 'DM', False) and any(getattr(obj.DM, attr, False) for attr in ['isdecal', 'istrimsheet', 'isatlas', 'isatlasdummy'])

def is_group_empty(obj):
    return getattr(obj, 'M3', False) and getattr(obj.M3, 'is_group_empty', False)

def is_group_anchor(obj):
    return getattr(obj, 'M3', False) and getattr(obj.M3, 'is_group_anchor', False)

def is_plug_handle(obj):
    return getattr(obj, 'MM', False) and getattr(obj.MM, 'isplughandle', False)

def is_instance_collection(obj):
    if obj.type == 'EMPTY' and obj.instance_type == 'COLLECTION' and obj.instance_collection:
        return obj.instance_collection

def parent(obj, parentobj):
    if obj.parent:
        unparent(obj)

    obj.parent = parentobj
    obj.matrix_parent_inverse = parentobj.matrix_world.inverted_safe()

def unparent(obj):
    if obj.parent:
        omx = obj.matrix_world.copy()
        obj.parent = None
        obj.matrix_world = omx

def get_object_tree(obj, obj_tree, mod_objects=True, mod_dict=None, mod_type_ignore=[], depth=0, find_disabled_mods=False, include_hidden=(), debug=False):
    depthstr = " " * depth

    if debug:
        print()
        print("depth:", depth, "tree:", [obj.name for obj in obj_tree])
        print(f"{depthstr}{obj.name}")

    for child in obj.children:
        vis = visible_get(child)

        hidden = vis['meta'].replace('HIDDEN_', '') if vis['meta'] in ['SCENE', 'VIEWLAYER', 'HIDDEN_COLLECTION'] else None

        if debug:
            print(f" {depthstr}child: {child.name}", "hidden meta:", hidden)

        if child not in obj_tree:
            if hidden and hidden not in include_hidden:
                if debug:
                    print(f"  {depthstr}! ignoring child '{child.name}' due to severe hidden state {hidden}")
                continue

            obj_tree.append(child)

            get_object_tree(child, obj_tree, mod_objects=mod_objects, mod_dict=mod_dict, mod_type_ignore=mod_type_ignore, depth=depth + 1, find_disabled_mods=find_disabled_mods, include_hidden=include_hidden, debug=debug)

    if mod_objects:
        for mod in obj.modifiers:

            if mod.type not in mod_type_ignore and (mod.show_viewport or find_disabled_mods):

                if mod_obj := get_mod_obj(mod):
                    vis = visible_get(mod_obj)

                    hidden = vis['meta'].replace('HIDDEN_', '') if vis['meta'] in ['SCENE', 'VIEWLAYER', 'HIDDEN_COLLECTION'] else None

                    if debug:
                        print(f" {depthstr}mod: {mod.name} | obj: {mod_obj.name}", "hidden meta:", hidden)

                    if mod_obj:
                        if hidden and hidden not in include_hidden:
                            if debug:
                                print(f"  {depthstr}! ignoring child '{mod_obj.name}' due to severe hidden state {hidden}")
                            continue

                        if mod_dict is not None:
                            if mod_obj in mod_dict:
                                mod_dict[mod_obj].append(mod)
                            else:
                                mod_dict[mod_obj] = [mod]

                        if mod_obj not in obj_tree:
                            obj_tree.append(mod_obj)

                            get_object_tree(mod_obj, obj_tree, mod_objects=mod_objects, mod_dict=mod_dict, mod_type_ignore=mod_type_ignore, depth=depth + 1, find_disabled_mods=find_disabled_mods, include_hidden=include_hidden, debug=debug)

                else:
                    if debug:
                        print(f" {depthstr}mod: {mod.name} | obj: None")

def duplicate_obj_recursively(context, dg, obj, keep_selection=False, debug=False):

    sel = [obj for obj in context.selected_objects]
    active = context.active_object
    view = get_3dview_space_from_context(context)
    dup_map = {}

    if view:
        bpy.ops.object.select_all(action='DESELECT')

        children = {str(uuid4()): (ob, visible_get(ob)) for ob in obj.children_recursive}

        if debug:
            print()
            print("children")

        for dup_hash, (ob, vis) in children.items():
            if debug:
                print(ob.name, dup_hash, ", is visible:", vis['visible'], ", meta:", vis['meta'])

            ob.HC.dup_hash = dup_hash
            ensure_visibility(context, ob, select=True)

        context.view_layer.objects.active = obj
        obj.select_set(True)

        bpy.ops.object.duplicate(linked=False)

        obj_dup = context.active_object

        dup_map[obj] = obj_dup

        dup_children = [ob for ob in obj_dup.children_recursive]

        if debug:
            print()
            print("duplicated children")

        for dup in dup_children:
            orig, vis = children[dup.HC.dup_hash]

            if debug:
                print(orig.name, "-", dup.name, ", was visible:", vis['visible'], ", was in local view:", vis['meta'])

            for ob in [orig, dup]:
                restore_visibility(ob, vis)

                ob.HC.dup_hash = ''

            dup_map[orig] = dup

        bpy.ops.object.select_all(action='DESELECT')

        if keep_selection:
            for ob in sel + [active]:
                ob.select_set(True)

            context.view_layer.objects.active = active

        else:
            obj_dup.select_set(True)
            context.view_layer.objects.active = obj_dup

        return dup_map

def remove_unused_children(context, obj, depsgraph=None, debug=False):
    if debug:
        print("\nremoving unused children of", obj.name)

    if depsgraph:
        depsgraph.update()

    children = [ob for ob in obj.children_recursive if ob.name in context.scene.objects]
    removable = []

    for ob in children:
        if debug:
            print(ob.name)

        if ob.hide_render or is_wire_object(ob, curve=False):
            if debug:
                print("  is a candidate")

            mods = is_mod_obj(ob)

            if debug:
                print("    mods:", [(mod.name, "on", mod.id_data) for mod in mods])

            if not mods:
                removable.append(ob)

                if debug:
                    print("    not used by any, remove!")

        else:
            if debug:
                print("  should be kept")

    for ob in removable:
        for c in ob.children_recursive:
            if c not in removable:
                if debug:
                    print(" re-parenting", ob.name, "child object", c.name, "to obj")
                parent(c, obj)

    if removable:
        bpy.data.batch_remove(removable)

def setup_split_boolean(context, mod, instance_cutter=True, avoid_non_mod_children=True, avoid_mods=None):
    def filter_avoid_mods(tree):
        def _filter(obj):
            return obj not in [mo.object for mo in avoid_mods if mo.object]
        return list(filter(_filter, tree))

    def filter_avoid_non_mod_children(tree):
        def _filter(obj):
            return obj in [modobj for mo in host.modifiers if (modobj := get_mod_obj(mo))]

        return list(filter(_filter, tree))

    bpy.ops.object.select_all(action='DESELECT')

    if not mod.show_viewport:
        mod.show_viewport = True

    cutter = mod.object

    host = mod.id_data
    host.select_set(True)

    if context.active_object != host:
        context.view_layer.objects.active = host

    if cutter.parent != host:
        parent(cutter, host)

    tree = []

    get_object_tree(host, tree, mod_objects=False, include_hidden=('VIEWLAYER', 'COLLECTION'))

    if avoid_mods:
        tree = filter_avoid_mods(tree)

    children = {str(uuid4()): (obj, visible_get(obj)) for obj in tree}

    for dup_hash, (obj, vis) in children.items():
        obj.HC.dup_hash = dup_hash

        ensure_visibility(context, obj, select=True)

    bpy.ops.object.duplicate(linked=False)

    host_dup = context.active_object

    if avoid_mods:
        for mo in avoid_mods:
            av_mod = host_dup.modifiers.get(mo.name)

            if av_mod:
                remove_mod(av_mod)

    mod_dup = host_dup.modifiers.get(mod.name)
    mod_dup.operation = 'INTERSECT'
    mod_dup.name ='Split (Intersect)'

    children_dup = [obj for obj in host_dup.children_recursive]

    dup_map = {host: host_dup}

    for dup in children_dup:
        orig, vis = children[dup.HC.dup_hash]

        dup_map[orig] = dup

        if orig == cutter:

            if instance_cutter:
                dupmesh = dup.data
                dup.data = orig.data
                bpy.data.meshes.remove(dupmesh, do_unlink=False)

            add_displace(dup, name="Displace (Split)", mid_level=0, strength=-0.005)

            cutter_dup = dup

        for ob in [orig, dup]:
            restore_visibility(ob, vis)

            ob.HC.dup_hash = ''

    d = {'orig': {'mod': mod,
                  'host': host,
                  'cutter': cutter},

         'dup': {'mod': mod_dup,
                 'host': host_dup,
                 'cutter': cutter_dup},

         'map': dup_map}

    return d

def filter_non_child_objects(objects):
    def is_child_of_objects(obj):
        parent = obj.parent

        while parent:
            if parent in objects:
                return True

            parent = parent.parent
        return False

    return [obj for obj in objects if not is_child_of_objects(obj)]

def hide_render(objects, state):
    if isinstance(objects, bpy.types.Object):
        objects = [objects]

    if isinstance(objects, list):
        ray_vis_hide = get_prefs().boolean_ray_vis_hide_cutters

        for obj in objects:
            obj.hide_render = state

            if ray_vis_hide:
                obj.visible_camera = not state
                obj.visible_diffuse = not state
                obj.visible_glossy = not state
                obj.visible_transmission = not state
                obj.visible_volume_scatter = not state
                obj.visible_shadow = not state

def get_active_object(context) -> Union[bpy.types.Object, None]:
    objects = getattr(context.view_layer, 'objects', None)

    if objects:
        return getattr(objects, 'active', None)

def get_selected_objects(context) -> list[bpy.types.Object]:
    objects = getattr(context.view_layer, 'objects', None)

    if objects:
        return getattr(objects, 'selected', [])

    return []

def get_visible_objects(context, local_view=False) -> list[bpy.types.Object]:
    view_layer = context.view_layer
    objects = getattr(view_layer, 'objects', [])

    return [obj for obj in objects if obj.visible_get(view_layer=view_layer)]

def get_batch_from_matrix(mx, size:float=1, screen_space:Union[bool, float]=False):
    if screen_space:
        zoom_factor = get_zoom_factor(bpy.context, depth_location=mx.to_translation(), scale=screen_space, ignore_obj_scale=True)
        ui_scale = get_scale(bpy.context)
        size = zoom_factor * ui_scale

    x = Vector((0.5, 0, 0)) * size
    y = Vector((0, 0.5, 0)) * size
    z = Vector((0, 0, 0.5)) * size

    coords = [mx @ (sign * co) for co in [x, y, z] for sign in [-1, 1]]
    indices = [(0, 1), (2, 3), (4, 5)]

    return coords, indices

def get_batch_from_lattice(lat, mx=None):
    u_count = lat.points_u
    points_v = lat.points_v
    points_w = lat.points_w

    if mx:
        coords = [mx @ p.co for p in lat.points]
    else:
        coords = [p.co for p in lat.points]

    indices = []

    for w in range(points_w):
        for v in range(points_v):
            for u in range(u_count - 1):
                start = u + v * u_count + w * u_count * points_v
                end = start + 1
                indices.append((start, end))

    for w in range(points_w):
        for v in range(points_v - 1):
            for u in range(u_count):
                start = u + v * u_count + w * u_count * points_v
                end = start + u_count
                indices.append((start, end))

    for w in range(points_w - 1):
        for v in range(points_v):
            for u in range(u_count):
                start = u + v * u_count + w * u_count * points_v
                end = start + u_count * points_v
                indices.append((start, end))

    return coords, indices

def get_batch_from_bbox(bbox, corners:float=0):
    if corners:
        length = corners

        coords = [bbox[0], bbox[0] + (bbox[1] - bbox[0]) * length, bbox[0] + (bbox[3] - bbox[0]) * length, bbox[0] + (bbox[4] - bbox[0]) * length,
                  bbox[1], bbox[1] + (bbox[0] - bbox[1]) * length, bbox[1] + (bbox[2] - bbox[1]) * length, bbox[1] + (bbox[5] - bbox[1]) * length,
                  bbox[2], bbox[2] + (bbox[1] - bbox[2]) * length, bbox[2] + (bbox[3] - bbox[2]) * length, bbox[2] + (bbox[6] - bbox[2]) * length,
                  bbox[3], bbox[3] + (bbox[0] - bbox[3]) * length, bbox[3] + (bbox[2] - bbox[3]) * length, bbox[3] + (bbox[7] - bbox[3]) * length,
                  bbox[4], bbox[4] + (bbox[0] - bbox[4]) * length, bbox[4] + (bbox[5] - bbox[4]) * length, bbox[4] + (bbox[7] - bbox[4]) * length,
                  bbox[5], bbox[5] + (bbox[1] - bbox[5]) * length, bbox[5] + (bbox[4] - bbox[5]) * length, bbox[5] + (bbox[6] - bbox[5]) * length,
                  bbox[6], bbox[6] + (bbox[2] - bbox[6]) * length, bbox[6] + (bbox[5] - bbox[6]) * length, bbox[6] + (bbox[7] - bbox[6]) * length,
                  bbox[7], bbox[7] + (bbox[3] - bbox[7]) * length, bbox[7] + (bbox[4] - bbox[7]) * length, bbox[7] + (bbox[6] - bbox[7]) * length]

        indices = [(0, 1), (0, 2), (0, 3),
                   (4, 5), (4, 6), (4, 7),
                   (8, 9), (8, 10), (8, 11),
                   (12, 13), (12, 14), (12, 15),
                   (16, 17), (16, 18), (16, 19),
                   (20, 21), (20, 22), (20, 23),
                   (24, 25), (24, 26), (24, 27),
                   (28, 29), (28, 30), (28, 31)]

    else:
        coords = bbox
        indices = [(0, 1), (1, 2), (2, 3), (3, 0),
                   (4, 5), (5, 6), (6, 7), (7, 4),
                   (0, 4), (1, 5), (2, 6), (3, 7)]

    return coords, indices

def get_batch_from_icol(dg, icol, mx=None, single_batch=True):
    def get_instance_collection_batch_recursively(dg, batches, coords, indices, col, mx, single_batch=True):
        offsetmx = get_loc_matrix(col.instance_offset)
        instance_mx = mx @ offsetmx.inverted_safe()

        for obj in col.objects:
            if obj.display_type not in ['WIRE', 'BOUNDS'] and obj.type in ['MESH', 'CURVE', 'SURFACE', 'META', 'TEXT']:
                mesh_eval = get_eval_mesh(dg, obj, data_block=False)

                if mesh_eval.edges:
                    obj_coords, obj_indices = get_batch_from_mesh(mesh_eval, instance_mx @ obj.matrix_world)

                    if single_batch:
                        index_offset = len(coords)

                        adjusted_indices = np.array(obj_indices) + index_offset

                        coords.extend(obj_coords)
                        indices.extend(adjusted_indices)

                    else:
                        batches.append((obj_coords, obj_indices))

            elif icol := is_instance_collection(obj):
                get_instance_collection_batch_recursively(dg, batches, coords, indices, icol, instance_mx @ obj.matrix_world, single_batch=single_batch)

    if mx is None:
        mx = Matrix()

    batches = []
    coords = []
    indices = []

    get_instance_collection_batch_recursively(dg, batches, coords, indices, icol, mx, single_batch=single_batch)

    if single_batch:
        return coords, indices

    else:
        return batches

def get_batch_from_mesh(mesh, mx=None, offset=0):
    return get_coords_from_mesh(mesh, mx=mx, offset=offset, edge_indices=True)

def get_batch_from_obj(dg, obj, world_space=True, single_icol_batch=True, cross_in_screen_space:Union[bool, float]=False):
    mx = obj.matrix_world if world_space else None

    if obj.type == 'EMPTY':

        if icol := obj.instance_collection:
            if single_icol_batch:
                coords, indices = get_batch_from_icol(dg, icol, mx, single_batch=True)

                if coords:
                    return coords, indices, "INSTANCE_COLLECTION_MESH_EVAL"
            else:
                batches = get_batch_from_icol(dg, icol, mx, single_batch=False)

                if batches and batches[0]:
                    return batches, None, "INSTANCE_COLLECTION_MULTI_MESH_EVAL"

        coords, indices = get_batch_from_matrix(mx if mx else Matrix(), size=obj.empty_display_size * 2, screen_space=cross_in_screen_space)

        return coords, indices, "EMPTY_CROSS"

    elif obj.type in ['VOLUME', 'ARMATURE', 'GREASEPENCIL']:

        if has_bbox(obj):
            bbox = [mx @ Vector(co) for co in obj.bound_box] if mx else [Vector(co) for co in obj.bound_box]
            coords, indices = get_batch_from_bbox(bbox, corners=0.2)
            return coords, indices, f"{obj.type}_BBOX"

        else:
            if obj.type == 'VOLUME':
                coords, indices = get_batch_from_matrix(mx if mx else Matrix(), size=1, screen_space=cross_in_screen_space)
                return coords, indices, f"{obj.type}_CROSS"

            elif obj.type == 'ARMATURE':
                coords, indices = get_batch_from_matrix(mx if mx else Matrix(), size=1, screen_space=cross_in_screen_space)
                return coords, indices, f"{obj.type}_CROSS"

            elif obj.type == 'GREASEPENCIL':
                coords, indices = get_batch_from_matrix(mx if mx else Matrix(), size=1, screen_space=cross_in_screen_space)
                return coords, indices, f"{obj.type}_CROSS"

    elif obj.type == 'LATTICE':

        coords, indices = get_batch_from_lattice(obj.data, mx)
        return coords, indices, "LATTICE"

    elif obj.type in ['LIGHT', 'CAMERA']:

        if obj.type == 'LIGHT':

            if obj.data.type in ['POINT', 'SPOT']:
                size = obj.data.shadow_soft_size * 2
            elif obj.data.type == 'AREA':
                size = obj.data.size
            else:
                size = 1

            coords, indices = get_batch_from_matrix(mx if mx else Matrix(), size=size, screen_space=cross_in_screen_space)
            return coords, indices, f"{obj.type}_CROSS"

        elif obj.type == 'CAMERA':
            coords, indices = get_batch_from_matrix(mx if mx else Matrix(), size=1, screen_space=cross_in_screen_space)
            return coords, indices, f"{obj.type}_CROSS"

    else:
        mesh_eval = get_eval_mesh(dg, obj, data_block=False)

        if mesh_eval.edges:
            coords, indices = get_batch_from_mesh(mesh_eval, mx)
            return coords, indices, f"{obj.type}_MESH_EVAL"

        elif has_bbox(obj):
            bbox = [mx @ Vector(co) for co in obj.bound_box] if mx else [Vector(co) for co in obj.bound_box]
            coords, indices = get_batch_from_bbox(bbox, corners=0.2)
            return coords, indices, f"{obj.type}_BBOX"

        else:
            coords, indices = get_batch_from_matrix(mx if mx else Matrix(), size=1, screen_space=cross_in_screen_space)
            return coords, indices, f"{obj.type}_CROSS"

    return [], [], "NONE"
