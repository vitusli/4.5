import bpy
import bmesh
from .. utils.mesh import get_eval_mesh, hide, unhide, clear_uvs
from .. utils.object import intersect, flatten, parent, update_local_view
from .. utils.decal import get_panel_width, create_panel_uvs, change_panel_width, sort_panel_geometry, create_float_slice_geometry, finish_panel_decal
from .. utils.raycast import find_nearest_normals
from .. utils.raycast import find_nearest, shrinkwrap
from .. utils.ui import popup_message
from .. utils.collection import sort_into_collections

class Slice(bpy.types.Operator):
    bl_idname = "machin3.slice_decal"
    bl_label = "MACHIN3: Slice Decal"
    bl_description = "Create Panel Decal at Intersection of Two Objects.\nALT: Topo Slice, use target object's topology\nSHIFT: Create Smoothed Panel Decal\nCTRL: Create Subdivided and Smoothed Panel Decal"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        nondecals = [obj for obj in context.selected_objects if not obj.DM.isdecal and obj.type in ['MESH', 'CURVE', 'SURFACE', 'META']]
        return len(nondecals) == 2 and context.active_object in nondecals

    def invoke(self, context, event):
        self.dg = context.evaluated_depsgraph_get()

        nondecals = [obj for obj in context.selected_objects if not obj.DM.isdecal]

        target = context.active_object
        nondecals.remove(target)
        cutter = nondecals[0]

        sliced = self.slice(context, event, target, cutter)

        if not sliced:
            msg = ["Slicing failed!"]

            msg.append("Try re-positioning the cutter, make sure it intersects the object you want to slice.")
            msg.append("Also, make sure you aren't using Topo-Slice (ALT pressed) on geometry that's unsuited for it.")

            popup_message(msg)

        return {'FINISHED'}

    def slice(self, context, event, target, cutter):
        parent(cutter, target)

        self.dg.update()

        panel = self.create_slice_base_object(context, cutter, target)

        smooth = panel.data.polygons[0].use_smooth

        hide(panel.data)
        unhide(cutter.data)

        if event.alt:
            panel = self.topo_slice(context, panel, cutter, smooth=smooth)

        else:
            panel = self.float_slice(context, event, panel, cutter, smooth=smooth)

        if panel:
            panel.name = 'Panel Decal'
            panel.data.name = 'Panel Decal'

            finish_panel_decal(self.dg, context, panel, target, cutter, smooth=smooth)

            sort_into_collections(context, panel)

            target.select_set(False)
            panel.select_set(True)
            context.view_layer.objects.active = panel

            update_local_view(context.space_data, [(panel, True)])

            if panel.data.has_custom_normals:
                with context.temp_override(object=panel):
                    bpy.ops.mesh.customdata_custom_splitnormals_clear()

            return True

        return

    def create_slice_base_object(self, context, cutter, target):
        mesh = get_eval_mesh(self.dg, target, data_block=True)

        mesh.materials.clear()

        panel = bpy.data.objects.new(f"{cutter.name}_sliced", object_data=mesh)

        panel.matrix_world = target.matrix_world

        context.scene.collection.objects.link(panel)

        return panel

    def topo_slice(self, context, panel, cutter, smooth=True):
        def create_topo_slice_geometry(count, obj, flat_target):
            def get_dirty_panel_ends(bm):
                boundary_edges = [e for e in bm.edges if not e.is_manifold]

                if len(boundary_edges) == 4 * len(bm.faces) and all(len(f.verts) == 4 for f in bm.faces):
                    ends = []

                    for f in bm.faces:
                        edge_lengths = sorted([(e, e.calc_length()) for e in f.edges], key=lambda x: x[1])
                        for e, _ in edge_lengths[0:2]:
                            ends.append(e)

                else:

                    bmesh.ops.triangulate(bm, faces=bm.faces, quad_method='BEAUTY', ngon_method='BEAUTY')

                    end_verts = [v for v in bm.verts if len(v.link_edges) == 2 and sum(not e.is_manifold for e in v.link_edges) == 2]

                    ends = []
                    for v in end_verts:
                        for e in v.link_edges:
                            otherv = e.other_vert(v)

                            if len(otherv.link_edges) == 3 and sum(not e.is_manifold for e in otherv.link_edges) == 2:
                                ends.append(e)

                return ends

            def create_quad_panel_geometry(bm, ends):
                sequences = []
                ends_seen = ends.copy()

                faces = [f for f in bm.faces]
                rail_edges = [e for e in bm.edges if e.is_manifold] + ends

                edge = ends[0] if ends else rail_edges[0]
                loop = edge.link_loops[0]
                face = loop.face

                seq = [(face, edge, [e for e in face.edges if not e.is_manifold and e not in rail_edges])]

                while faces:

                    if face in faces and edge in rail_edges:
                        faces.remove(face)
                        rail_edges.remove(edge)

                    else:
                        return []

                    if edge in ends_seen:
                        ends_seen.remove(edge)

                    while True:
                        loop = loop.link_loop_next

                        if loop.edge in ends_seen or loop.edge == seq[0][1]:

                            if loop.edge in ends_seen:
                                cyclic = False
                                ends_seen.remove(loop.edge)

                            elif loop.edge == seq[0][1]:
                                cyclic = True

                            sequences.append((seq, cyclic))

                            if faces:
                                edge = ends_seen[0] if ends_seen else rail_edges[0]
                                loop = edge.link_loops[0]
                                face = loop.face

                                seq = [(face, edge, [e for e in face.edges if not e.is_manifold and e not in rail_edges])]

                            break

                        elif loop.edge.is_manifold:
                            loop = loop.link_loop_radial_next
                            edge = loop.edge
                            face = loop.face

                            seq.append((face, edge, [e for e in face.edges if not e.is_manifold and e not in rail_edges]))
                            break

                bmesh.ops.delete(bm, geom=bm.faces, context="FACES_KEEP_BOUNDARY")

                bmesh.ops.delete(bm, geom=ends, context="EDGES")

                geo_sequences = []

                for seq, cyclic in sequences:
                    bounds = [edge for _, _, bounds in seq for edge in bounds]

                    try:
                        geo = bmesh.ops.bridge_loops(bm, edges=bounds)
                    except:
                        return []

                    geo_sequences.append(geo)

                return geo_sequences

            bm = bmesh.new()
            bm.from_mesh(obj.data)

            blastfaces = [f for f in bm.faces if not f.hide]
            bmesh.ops.delete(bm, geom=blastfaces, context="FACES_KEEP_BOUNDARY")

            if not bm.faces:
                return

            v3s = [v for v in bm.verts if sum(e.is_manifold for e in v.link_edges) > 1]

            if not v3s:
                f3s = [f for f in bm.faces if len(f.verts) == 3]

                if not f3s:
                    ends = get_dirty_panel_ends(bm)

                    geo_sequences = create_quad_panel_geometry(bm, ends)

                    for geo in geo_sequences:
                        mxw = obj.matrix_world
                        face = geo['faces'][0]
                        origin = mxw @ face.calc_center_median()
                        normal = mxw.to_3x3() @ face.normal

                        _, _, target_normal, _, _ = find_nearest([flat_target], origin)

                        if normal.dot(target_normal) < 0:
                            bmesh.ops.reverse_faces(bm, faces=geo['faces'])

                    if not any(len(f.verts) == 3 for f in bm.faces):

                        if count > 0:
                            change_panel_width(bm, pow(2, count))

                        return bm

            bm.clear()

        flat_target = panel.copy()
        flat_target.data = panel.data.copy()

        width = get_panel_width(cutter, context.scene)

        solidify = cutter.modifiers.new(name="Solidify", type="SOLIDIFY")
        solidify.offset = 0
        solidify.use_even_offset = True
        solidify.thickness = width

        intersect(panel, cutter)

        c = 0
        while True:

            candidate = panel.copy()
            candidate.data = panel.data.copy()
            context.scene.collection.objects.link(candidate)
            flatten(candidate)

            clear_uvs(candidate.data)

            bm = create_topo_slice_geometry(c, candidate, flat_target)

            if bm:
                bpy.data.meshes.remove(panel.data, do_unlink=True)
                panel = candidate

                cutter.modifiers.remove(solidify)
                break

            elif bm is False or c > 10:
                bpy.data.meshes.remove(candidate.data, do_unlink=True)
                bpy.data.meshes.remove(panel.data, do_unlink=True)

                cutter.modifiers.remove(solidify)
                return

            else:
                bpy.data.meshes.remove(candidate.data, do_unlink=True)

                c += 1
                solidify.thickness /= 2

        bpy.data.meshes.remove(flat_target.data, do_unlink=True)

        geo = sort_panel_geometry(bm, smooth=smooth)

        create_panel_uvs(bm, geo, panel, width)
        return panel

    def float_slice(self, context, event, panel, cutter, smooth=True):
        def check_cutter(cutter):
            bm = bmesh.new()
            bm.from_mesh(cutter.data)

            ismanifold = True
            for e in bm.edges:
                if not e.is_manifold:
                    ismanifold = False
                    break

            if not ismanifold:
                for f in bm.faces:
                    f.select = True

                bmesh.ops.solidify(bm, geom=bm.faces, thickness=0.0001)
                bm.to_mesh(cutter.data)

            bm.free()
            return ismanifold

        def recreate_cutter(cutter):
            bm = bmesh.new()
            bm.from_mesh(cutter.data)

            faces = [f for f in bm.faces if not f.select]
            bmesh.ops.delete(bm, geom=faces, context="FACES")

            bm.to_mesh(cutter.data)
            bm.clear()

        def get_intersection_edge_loop(obj, ismanifold):
            bm = bmesh.new()
            bm.from_mesh(obj.data)
            bm.normal_update()
            bm.verts.ensure_lookup_table()

            if ismanifold:
                faces = [f for f in bm.faces if not f.hide]
                bmesh.ops.delete(bm, geom=faces, context="FACES_KEEP_BOUNDARY")

                faces = [f for f in bm.faces if f.hide]
                bmesh.ops.delete(bm, geom=faces, context="FACES_KEEP_BOUNDARY")

            else:
                faces = [f for f in bm.faces if not f.hide or f.select]
                bmesh.ops.delete(bm, geom=faces, context="FACES")

                verts = [v for v in bm.verts if not v.select]
                bmesh.ops.delete(bm, geom=verts, context="VERTS")

            if len(bm.edges) == 0:
                return False

            return bm

        def sort_vertex_sequences(bm):
            verts = [v for v in bm.verts]
            intersection = verts.copy()
            sequences = []

            noncyclicstartverts = [v for v in verts if len(v.link_edges) == 1]

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

                nextv = [e.other_vert(v) for e in v.link_edges if e.other_vert(v) not in seq]

                if nextv:
                    v = nextv[0]

                else:
                    cyclic = True if len(v.link_edges) == 2 else False

                    sequences.append((seq, cyclic))

                    if verts:
                        if noncyclicstartverts:
                            v = noncyclicstartverts[0]
                        else:
                            v = verts[0]

                        seq = []

            return sequences, intersection

        flat_target = panel.copy()
        flat_target.data = panel.data.copy()

        ismanifold = check_cutter(cutter)

        intersect(panel, cutter)

        self.dg.update()
        flatten(panel, self.dg)

        clear_uvs(panel.data)

        if not ismanifold:
            recreate_cutter(cutter)

        bm = get_intersection_edge_loop(panel, ismanifold)

        if not bm:
            bpy.data.meshes.remove(panel.data, do_unlink=True)
            return False

        if len(bm.verts) > 2:

            if event.shift:
                bmesh.ops.smooth_vert(bm, verts=bm.verts, factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)

            elif event.ctrl:
                bmesh.ops.subdivide_edges(bm, edges=bm.edges, cuts=1)

                for i in range(4):
                    bmesh.ops.smooth_vert(bm, verts=bm.verts, factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)

        normals, bmt = find_nearest_normals(bm, flat_target.data)

        bpy.data.meshes.remove(flat_target.data, do_unlink=True)

        sequences, intersection = sort_vertex_sequences(bm)

        width = get_panel_width(panel, context.scene)

        geo = create_float_slice_geometry(bm, panel.matrix_world, sequences, normals, width=width, smooth=smooth)

        bmesh.ops.delete(bm, geom=intersection, context="VERTS")

        shrinkwrap(bm, bmt)

        create_panel_uvs(bm, geo, panel, width=width)

        return panel
