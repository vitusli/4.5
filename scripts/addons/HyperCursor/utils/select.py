import bmesh
from math import radians, degrees

from . math import get_angle_between_edges
from . ui import force_geo_gizmo_update

def get_selected_vert_sequences(verts, debug=False):
    sequences = []

    noncyclicstartverts = [v for v in verts if len([e for e in v.link_edges if e.select]) == 1]

    if noncyclicstartverts:
        v = noncyclicstartverts[0]

    else:
        v = verts[0]

    seq = []

    while verts:
        seq.append(v)

        verts.remove(v)
        if v in noncyclicstartverts:
            noncyclicstartverts.remove(v)

        nextv = [e.other_vert(v) for e in v.link_edges if e.select and e.other_vert(v) not in seq]

        if nextv:
            v = nextv[0]

        else:
            cyclic = True if len([e for e in v.link_edges if e.select]) == 2 else False

            sequences.append((seq, cyclic))

            if verts:
                if noncyclicstartverts:
                    v = noncyclicstartverts[0]
                else:
                    v = verts[0]

                seq = []

    if debug:
        for seq, cyclic in sequences:
            print(cyclic, [v.index for v in seq])

    return sequences

def get_edges_as_vert_sequences(edges, debug=False):
    def get_start_vert(edges):
        verts = set(v for e in edges for v in e.verts)

        if endverts := [v for v in verts if len([e for e in v.link_edges if e in edges]) == 1]:
            return endverts[0]

        else:
            non_t_verts = [v for edge in edges for v in edge.verts if len([e for e in v.link_edges if e in edges]) < 3]

            if non_t_verts:
                return non_t_verts[0]

            else:
                return edges[0].verts[0]

    edges = edges.copy()

    sequences = []

    v = get_start_vert(edges)

    seq = [v]

    while edges:
        paths = [e for e in v.link_edges if e in edges]

        if paths:
            edge = paths[0]
            next_v = edge.other_vert(v)
            seq.append(next_v)

            edges.remove(edge)

            v = next_v

        if not paths or not edges:

            cyclic = seq[0] == seq[-1]

            sequences.append((seq[:-1] if cyclic else seq, cyclic))

            if edges:

                v = get_start_vert(edges)

                seq = [v]

    if debug:
        print()
        print("sequences:", len(sequences))

        for seq, cyclic in sequences:
            print(cyclic, [v.index for v in seq])

    return sequences

def get_edges_vert_sequences(verts, edges, debug=False):
    sequences = []

    noncyclicstartverts = [v for v in verts if len([e for e in v.link_edges if e in edges]) == 1]

    if noncyclicstartverts:
        v = noncyclicstartverts[0]

    else:
        v = verts[0]

    seq = []

    while verts:
        seq.append(v)

        if v in noncyclicstartverts:
            noncyclicstartverts.remove(v)

        if v in verts:
            verts.remove(v)

            nextv = [other_v for e in v.link_edges if e in edges and (other_v := e.other_vert(v)) not in seq]

            if nextv and nextv[0] not in verts:

                seq.append(nextv[0])
                nextv = None

        else:
            print("WARNING: unexpected vert found in get_edges_vert_sequences():", v.index)
            print("         this should not happen")
            nextv = None

        if nextv:
            v = nextv[0]

        else:

            cyclic = len(seq) > 2 and bool([e for e in v.link_edges if e in edges and e.other_vert(v := seq[0]) == seq[-1]])

            sequences.append((seq, cyclic))

            if verts:
                if noncyclicstartverts:
                    v = noncyclicstartverts[0]
                else:
                    v = verts[0]

                seq = []

    if debug:
        print()
        print("sequences:", len(sequences))

        for verts, cyclic in sequences:
            print(cyclic, [v.index for v in verts])

    return sequences

def get_loop_edges(min_angle, edges, edge, vert, prefer_center_of_three=True, prefer_center_90_of_three=True, ensure_gizmo=False, ensure_manifold=False, debug=False):
    if debug:
        print()
        print("first edge:", edge.index)
        print("first vert:", vert.index)

    while True:
        other_vert = edge.other_vert(vert)

        if debug:
            print("other vert:", other_vert.index if other_vert else None)

        next_edges = [(get_angle_between_edges(edge, e), e) for e in other_vert.link_edges if e != edge]

        if edge_gizmo_layer := ensure_gizmo:
            next_edges = [(angle, e) for angle, e in next_edges if e[edge_gizmo_layer]]

        if ensure_manifold:
            next_edges = [(angle, e) for angle, e in next_edges if e.is_manifold]

        if next_edges:
            if len(next_edges) == 3 and prefer_center_of_three and all(e[1].is_manifold for e in next_edges):
                if debug:
                    print("special case: 3 edges, preferring the center edge")

                loop = [l for l in edge.link_loops if l.vert == other_vert][0]
                next_loop = loop.link_loop_prev.link_loop_radial_next.link_loop_prev

                edge = next_loop.edge

                if debug:
                    print("next edge:", edge.index)
                    print("next vert:", other_vert.index)

                if edge not in edges:
                    vert = other_vert
                    edges.append(edge)
                    continue

            elif len(next_edges) == 3 and prefer_center_90_of_three and all(round(degrees(angle), 3) == 90 and e.is_manifold for angle, e in next_edges):
                if debug:
                    print("special case: 3 edges, all at 90 degrees, preferring center edge")

                loop = [l for l in edge.link_loops if l.vert == other_vert][0]
                next_loop = loop.link_loop_prev.link_loop_radial_next.link_loop_prev

                edge = next_loop.edge

                if debug:
                    print("next edge:", edge.index)
                    print("next vert:", other_vert.index)

                if edge not in edges:
                    vert = other_vert
                    edges.append(edge)
                    continue

            else:
                if debug:
                    print("normal case: purely angle based")
                best_fit = max(next_edges, key=lambda x: x[0])

                angle = best_fit[0]
                edge = best_fit[1]

                if debug:
                    print("next edge:", edge.index)
                    print("next vert:", other_vert.index)

                if edge not in edges and angle > radians(min_angle):
                    vert = other_vert

                    edges.append(edge)
                    continue
        break
    return edges

def get_ring_edges(edges, edge, loop, ring_ngons=True, debug=False):

    if debug:
        print()
        print("first edge:", edge.index)

    while True:
        face = loop.face

        if len(face.verts) == 4:
            if debug:
                print("found quad")

            next_loop = loop.link_loop_next.link_loop_next
            next_edge = next_loop.edge

        elif ring_ngons and len(face.verts) < 9:
            if debug:
                print("found ngon")

            loop_edge_dir = (loop.vert.co - loop.edge.other_vert(loop.vert).co).normalized()

            next_edges = sorted([((lo.vert.co - lo.edge.other_vert(lo.vert).co).normalized().dot(loop_edge_dir), lo.edge) for lo in loop.face.loops if lo != loop], key=lambda x: x[0])

            same_dot_edges = [e for dot, e in next_edges if dot == next_edges[0][0]]

            if len(same_dot_edges) > 1:
                break

            next_edge = next_edges[0][1]
            next_loop = [l for l in next_edge.link_loops if l.face == face][0]

        else:
            break

        if debug:
            print("next edge:", next_edge.index)

        if next_edge not in edges:
            edges.append(next_edge)

            next_edge.select_set(True)

            if len(next_edge.link_loops) > 1:
                loop = next_loop.link_loop_radial_next
                continue

        break

    return edges

def get_edges(edge, loop=False, loop_min_angle=120, loop_prefer_center_of_three=True, loop_ensure_gizmo=False, ring=False, ring_ngons=True):
    if loop:

        vert = edge.verts[0]
        edges = get_loop_edges(loop_min_angle, [edge], edge, vert, prefer_center_of_three=loop_prefer_center_of_three, ensure_gizmo=loop_ensure_gizmo)

        vert = edge.other_vert(vert)
        edges = get_loop_edges(loop_min_angle, edges, edge, vert, prefer_center_of_three=loop_prefer_center_of_three, ensure_gizmo=loop_ensure_gizmo)

    elif ring:
        loops = edge.link_loops

        for idx, loop in enumerate(loops):

            if idx == 0:
                edges = get_ring_edges([edge], edge, loop, ring_ngons=ring_ngons, debug=False)

            else:
                edges = get_ring_edges(edges, edge, loop, ring_ngons=ring_ngons, debug=False)

    else:
        edges = [edge]
    return edges

def get_loop_faces(faces, face, edge, debug=False):
    loop = [l for l in face.loops if l.edge == edge][0]

    if debug:
        print("first face:", face.index)
        print("first edge:", edge.index)
        print("first loop:", loop)

    while True:
        next_radial_loop = loop.link_loop_radial_next
        next_face = next_radial_loop.face

        if debug:
            print("next radial loop", next_face.index)
            print("next face", next_face.index)

        if next_face not in faces and len(next_face.verts) == 4:
            faces.append(next_face)
            loop = next_radial_loop.link_loop_next.link_loop_next

            if debug:
                print("next loop:", loop)

            continue
        break

    return faces

def get_faces(face, edge, loop=False):
    if loop:
        faces = get_loop_faces([face], face, edge, debug=False)

        edge = [l.link_loop_next.link_loop_next.edge for l in face.loops if l.edge == edge][0]
        faces = get_loop_faces(faces, face, edge, debug=False)

    else:
        faces = [face]

    return faces

def clear_hyper_edge_selection(context, obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)

    slayer = bm.edges.layers.int.get('HyperEdgeSelect')

    if slayer:
        bm.edges.layers.int.remove(slayer)
        bm.to_mesh(obj.data)

    bm.free()

    force_geo_gizmo_update(context)

def invert_hyper_edge_selection(context, obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)

    slayer = bm.edges.layers.int.get('HyperEdgeSelect')

    if not slayer:
        slayer = bm.edges.layers.int.new('HyperEdgeSelect')

    if slayer:
        for e in bm.edges:
            e[slayer] = 0 if e[slayer] == 1 else 1

        bm.to_mesh(obj.data)
        bm.free()

    force_geo_gizmo_update(context)

def get_hyper_edge_selection(bm, debug=False):
    slayer = bm.edges.layers.int.get('HyperEdgeSelect')

    edges = []

    if slayer:
        edges = [e for e in bm.edges if e[slayer] == 1]

    if debug:
        print("hyper selected edges:", [e.index for e in edges])

    return edges

def get_selected_edges(bm, index=None, loop=False, loop_min_angle=120, loop_prefer_center_of_three=True, loop_ensure_gizmo=False, ring=False, ring_ngons=True):
    index_edge = [bm.edges[index]] if index is not None else []

    hyper_selected = get_hyper_edge_selection(bm, debug=False)

    selected = []

    for e in index_edge + hyper_selected:
        if loop:
            selected.extend(get_edges(e, loop=True, loop_min_angle=loop_min_angle, loop_prefer_center_of_three=loop_prefer_center_of_three, loop_ensure_gizmo=loop_ensure_gizmo))
        elif ring:
            selected.extend(get_edges(e, ring=True, ring_ngons=ring_ngons))
        else:
            selected.extend(get_edges(e))

    return list(set(selected))

def clear_hyper_face_selection(context, obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)

    slayer = bm.faces.layers.int.get('HyperFaceSelect')

    if slayer:
        bm.faces.layers.int.remove(slayer)
        bm.to_mesh(obj.data)

    bm.free()

    force_geo_gizmo_update(context)

def invert_hyper_face_selection(context, obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)

    slayer = bm.faces.layers.int.get('HyperFaceSelect')

    if not slayer:
        slayer = bm.faces.layers.int.new('HyperFaceSelect')

    if slayer:
        for f in bm.faces:
            f[slayer] = 0 if f[slayer] == 1 else 1

        bm.to_mesh(obj.data)
        bm.free()

    force_geo_gizmo_update(context)

def get_hyper_face_selection(bm, debug=False):
    slayer = bm.faces.layers.int.get('HyperFaceSelect')

    faces = []

    if slayer:
        faces = [f for f in bm.faces if f[slayer] == 1]

    if debug:
        print("hyper selected faces:", [f.index for f in faces])

    return faces

def get_selected_faces(bm, index=None):
    index_face = [bm.faces[index]] if index is not None else []

    hyper_selected = get_hyper_face_selection(bm, debug=False)

    return list(set(index_face + hyper_selected))
