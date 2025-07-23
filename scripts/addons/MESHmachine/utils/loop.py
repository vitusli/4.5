import bpy
import math
import mathutils
from . math import get_angle_between_edges, get_center_between_verts, get_distance_between_points, average_normals, check_ngon
from . draw import draw_point, draw_line, draw_vector, vert_debug_print

def get_loops(bm, bw, faces, sweeps, force_projected=False, debug=False):

    for sweep in sweeps:
        for idx, v in enumerate(sweep["verts"]):
            vert_debug_print(debug, v, "\n" + str(v.index), end=" • ")

            ccount = len(sweep["loop_candidates"][idx])
            vert_debug_print(debug, v, "\nloop count: " + str(ccount))

            if ccount == 0 or force_projected:
                loop_tuple = projected_loop(v, sweep["edges"][0], bw, debug=debug)
                sweep["loops"].append(loop_tuple)

            elif ccount == 1:
                loop_candidate = sweep["loop_candidates"][idx][0]
                edge = sweep["edges"][0]
                link_edges = [e for e in v.link_edges]

                if not edge.is_manifold:
                        vert_debug_print(debug, v, "topo loop next to an open boundary")

                elif check_ngon(edge):
                    if check_ngon(loop_candidate):
                        vert_debug_print(debug, v, "topo loop next to an ngon")

                elif check_ngon(loop_candidate) and len(link_edges) == 3:
                    if 89 < math.degrees(edge.calc_face_angle()) < 91:
                        vert_debug_print(debug, v, "topo loop next to face angled at 90 degrees")

                    else:
                        vert_debug_print(debug, v, "projected loop redirect")
                        loop_tuple = projected_loop(v, sweep["edges"][0], bw, debug=debug)
                        sweep["loops"].append(loop_tuple)
                        continue
                else:
                    vert_debug_print(debug, v, "normal topo loop")

                loop_tuple = topo_loop(v, sweep["loop_candidates"][idx], bw, debug=debug)
                sweep["loops"].append(loop_tuple)

            else:
                loop_tuple = biggest_angle_loop(v, sweep["edges"][0], sweep["loop_candidates"][idx], bw, debug=debug)

                if loop_tuple:
                    loop_type, _, loop_edge_idx, angle, _, _ = loop_tuple
                    vert_debug_print(debug, v, "angle: " + str(angle))

                    if 89 <= angle <= 91:  # NOTE: this may need to be dialed in
                        vert_debug_print(debug, v, "topo loop redirect after biggest angle returned a 90 degrees angle")
                        loop2_tuple = topo_loop(v, sweep["loop_candidates"][idx], bw, debug=debug)
                        loop2_type, _, loop2_edge_idx, _, _, _ = loop2_tuple

                        if loop_edge_idx == loop2_edge_idx:
                            vert_debug_print(debug, v, "projected loop redirect after topo loop returned the same loop as the biggest angle loop")

                            loop_tuple = projected_loop(v, sweep["edges"][0], bw, debug=debug)
                            sweep["loops"].append(loop_tuple)

                        else:
                            sweep["loops"].append(loop2_tuple)
                    else:
                        sweep["loops"].append(loop_tuple)
                else:
                    vert_debug_print(debug, v, "projected loop after biggest angle loop found no definitive result")
                    loop_tuple = projected_loop(v, sweep["edges"][0], bw, debug=debug)
                    sweep["loops"].append(loop_tuple)

def get_tri_corner_loops(bm, bw, faces, sweeps, debug=False):
    if debug:
        print()

    for sweep in sweeps:
        for idx, v in enumerate(sweep["verts"]):
            vert_debug_print(debug, v, "\n" + str(v.index), end=" • ")

            ccount = len(sweep["loop_candidates"][idx])
            vert_debug_print(debug, v, "\nloop count: " + str(ccount))

            loop_tuple = topo_loop(v, sweep["loop_candidates"][idx], bw, debug=debug)
            sweep["loops"].append(loop_tuple)

def topo_loop(vert, loop_candidates, bw, debug=False):

    layers = bw if isinstance(bw, list) else [bw]

    loop_edge = loop_candidates[0]
    remote_co = loop_edge.other_vert(vert).co.copy()

    if debug:
        mx = bpy.context.active_object.matrix_world
        if type(debug) is list:
            if vert.index in debug:
                print("topo loop:", loop_edge.index)
                draw_line([vert.co.copy(), remote_co], mx=mx, color=(1, 1, 1), modal=False)
        else:
            print("topo loop:", loop_edge.index)
            draw_line([vert.co.copy(), remote_co], mx=mx, color=(1, 1, 1), modal=False)

    return "TOPO", remote_co, loop_edge.index, None, loop_edge.smooth, [(loop_edge[layer], layer.name) for layer in layers]

def biggest_angle_loop(vert, edge, loop_candidates, bw, debug=False):

    layers = bw if isinstance(bw, list) else [bw]

    angles = []
    for e in loop_candidates:
        a = int(get_angle_between_edges(edge, e, radians=False))
        angles.append((a, e))

    angles = sorted(angles, key=lambda a: a[0], reverse=True)

    a1 = angles[0][0]
    a2 = angles[1][0]

    if abs(a1 - a2) < 10:
        if debug:
            print("angles (almost) the same")
        return

    angle, loop_edge = angles[0]
    remote_co = loop_edge.other_vert(vert).co.copy()

    if debug:
        mx = bpy.context.active_object.matrix_world
        if type(debug) is list:
            if vert.index in debug:
                print("biggest angle loop:", loop_edge.index)
                draw_line([vert.co.copy(), remote_co], mx=mx, color=(1, 1, 1), modal=False)

        else:
            print("biggest angle loop:", loop_edge.index)
            draw_line([vert.co.copy(), remote_co], mx=mx, color=(1, 1, 1), modal=False)

    return "BIGGEST_ANGLE", remote_co, loop_edge.index, angle, loop_edge.smooth, [(loop_edge[layer], layer.name) for layer in layers]

def projected_loop(vert, edge, bw, debug=False):

    layers = bw if isinstance(bw, list) else [bw]

    face = [f for f in vert.link_faces if not f.select and f not in edge.link_faces][0]

    v1 = vert
    v2 = edge.other_vert(v1)

    normals = [f.normal.normalized() for f in edge.link_faces if f.select]

    avg_edge_normal = average_normals(normals) * 0.1

    if debug:
        mx = bpy.context.active_object.matrix_world
        draw_vector(avg_edge_normal, origin=v1.co.copy(), mx=mx, color=(0.5, 0.5, 1), modal=False)

    avg_edge_face_normals = average_normals([avg_edge_normal, face.normal])
    v1_v2_dir = v2.co - v1.co

    dot = v1_v2_dir.dot(avg_edge_face_normals)

    if dot < 0:
        v1co_offset = v1.co - avg_edge_normal
        if debug:
            print("Offsetting in a negative direction")
            draw_point(v1co_offset, mx=mx, color=(1, 0, 0), modal=False)
    else:
        v1co_offset = v1.co + avg_edge_normal
        if debug:
            print("Offsetting in a positive direction")
            draw_point(v1co_offset, mx=mx, color=(1, 0, 0), modal=False)

    edge_dir = v1.co - v2.co
    ext_edgeco = v1co_offset + edge_dir

    if debug:
        if type(debug) is list:
            if vert.index in debug:
                draw_line([v1co_offset, ext_edgeco], mx=mx, color=(0, 1, 0), modal=False)
        else:
            draw_line([v1co_offset, ext_edgeco], mx=mx, color=(0, 1, 0), modal=False)

    perpco = ext_edgeco - face.normal

    if debug:
        if type(debug) is list:
            if vert.index in debug:
                draw_line([ext_edgeco, perpco], mx=mx, color=(0, 0, 1), modal=False)
        else:
            draw_line([ext_edgeco, perpco], mx=mx, color=(0, 0, 1), modal=False)

    ico = mathutils.geometry.intersect_line_plane(ext_edgeco, perpco, v1.co, face.normal)

    if debug:
        draw_point(ico, mx=mx, color=(1, 1, 1), modal=False)

    if debug:
        if type(debug) is list:
            if vert.index in debug:
                draw_line([vert.co.copy(), ico], mx=mx, color=(1, 1, 1), modal=False)
        else:
            draw_line([vert.co.copy(), ico], mx=mx, color=(1, 1, 1), modal=False)

    return "PROJECTED", ico, None, None, True, [(0, layer.name) for layer in layers]

def magic_loop(bm, vert, edge, connected, strict, debug=False):
    face = [f for f in vert.link_faces if not f.select and f not in edge.link_faces][0]

    f1 = edge.link_faces[0]
    f2 = edge.link_faces[1]

    m1co = f1.calc_center_median()  # NOTE: there's also calc_center_median_weighted()
    m2co = f2.calc_center_median()

    if strict:
        medgeco = get_center_between_verts(vert, edge.other_vert(vert))

        d1 = get_distance_between_points(medgeco, m1co)
        d2 = get_distance_between_points(medgeco, m2co)

        if d1 < d2:
            m2dir = m2co - medgeco
            m2co = medgeco + m2dir.normalized() * d1

        if d2 < d1:
            m1dir = m1co - medgeco
            m1co = medgeco + m1dir.normalized() * d2

    if debug:
        if type(debug) is list:
            if vert.index in debug:

                m1 = bm.verts.new()
                m1.co = m1co

                m2 = bm.verts.new()
                m2.co = m2co
        else:

            m1 = bm.verts.new()
            m1.co = m1co

            m2 = bm.verts.new()
            m2.co = m2co

    i1co = mathutils.geometry.intersect_line_plane(m1co, m1co + f1.normal, vert.co, face.normal)
    i2co = mathutils.geometry.intersect_line_plane(m2co, m2co + f2.normal, vert.co, face.normal)

    if not all([i1co, i2co]):
        print("aborting magic loop, \"the face\" could not be interesected")
        return

    if debug:
        if type(debug) is list:
            if vert.index in debug:
                i1 = bm.verts.new()
                i1.co = i1co

                i2 = bm.verts.new()
                i2.co = i2co

                bm.edges.new((m1, i1))
                bm.edges.new((m2, i2))
        else:
            i1 = bm.verts.new()
            i1.co = i1co

            i2 = bm.verts.new()
            i2.co = i2co

            bm.edges.new((m1, i1))
            bm.edges.new((m2, i2))

    crossv1co = vert.co + (vert.co - i1co)
    crossv2co = vert.co + (vert.co - i2co)

    if debug:
        if type(debug) is list:
            if vert.index in debug:
                crossv1 = bm.verts.new()
                crossv1.co = crossv1co

                crossv2 = bm.verts.new()
                crossv2.co = crossv2co

                bm.edges.new((crossv1, i1))
                bm.edges.new((crossv2, i2))

                bm.edges.new((crossv1, crossv2))
        else:
            crossv1 = bm.verts.new()
            crossv1.co = crossv1co

            crossv2 = bm.verts.new()
            crossv2.co = crossv2co

            bm.edges.new((crossv1, i1))
            bm.edges.new((crossv2, i2))

            bm.edges.new((crossv1, crossv2))

    crossvco, distance = mathutils.geometry.intersect_point_line(vert.co, crossv1co, crossv2co)

    vert_crossv = crossvco - vert.co
    othervert_vert = vert.co - edge.other_vert(vert).co

    dot = vert_crossv.dot(othervert_vert)

    if dot < 0:
        newdir = vert.co - crossvco
        crossvco = vert.co + newdir
        if debug:
            if type(debug) is list:
                if vert.index in debug:
                    print("flipping the magic loop edge")
            else:
                print("flipping the magic loop edge")

    crossv = bm.verts.new()
    crossv.co = crossvco

    loop = bm.edges.new((vert, crossv))
    bm.edges.index_update()

    if debug:
        if type(debug) is list:
            if vert.index in debug:
                bm.edges.index_update()
                print("magic loop:", loop.index)
                loop.select = True
        else:
            bm.edges.index_update()
            print("magic loop:", loop.index)
            loop.select = True
    return loop

def ngon_loop(ngon, edge, vert, debug=False):
    for e in ngon.edges:
        if e != edge and vert in e.verts:
            if debug:
                print("ngon loop")

            return e

def angle_loop(bm, vert, connected, debug=False):
    vert1 = connected[0].other_vert(vert)
    vert2 = connected[1].other_vert(vert)

    v = bm.verts.new()
    v.co = get_center_between_verts(vert1, vert2)

    loop = bm.edges.new((vert, v))

    if debug:
        print("angle loop")
    return loop
