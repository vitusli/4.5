import bpy
from bpy.props import IntProperty, FloatProperty, BoolProperty

import bmesh
from mathutils import Vector, Matrix, Quaternion

from math import degrees, radians

from .. utils.draw import draw_fading_label, draw_point, draw_vector
from .. utils.geometry import calculate_thread
from .. utils.math import average_locations
from .. utils.modifier import add_auto_smooth, get_auto_smooth
from .. utils.selection import get_boundary_edges, get_edges_vert_sequences
from .. utils.ui import get_mouse_pos

from .. colors import green, red, yellow

class Thread(bpy.types.Operator):
    bl_idname = "machin3.add_thread"
    bl_label = "MACHIN3: Add Thread"
    bl_description = "Create Thread from Cylindrical Face Selection"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    radius: FloatProperty(name="Radius", min=0, default=1)
    segments: IntProperty(name="Segments", min=5, default=32)
    loops: IntProperty(name="Threads", min=1, default=4)
    depth: FloatProperty(name="Depth", description="Depth in Percentage of minor Diameter", min=0, max=100, default=5, subtype='PERCENTAGE')
    fade: FloatProperty(name="Fade", description="Percentage of Segments fading into inner Diameter", min=1, max=100, default=15, subtype='PERCENTAGE')
    h1: FloatProperty(name="Bottom Flank", min=0, default=0.2, step=0.1)
    h2: FloatProperty(name="Crest", min=0, default=0.05, step=0.1)
    h3: FloatProperty(name="Top Flank", min=0, default=0.2, step=0.1)
    h4: FloatProperty(name="Root", min=0, default=0.05, step=0.1)
    flip: BoolProperty(name="Flip", default=False)
    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def draw(self, context):
        layout = self.layout

        column = layout.column(align=True)
        column.separator()

        row = column.row(align=True)
        row.prop(self, 'loops')
        row.prop(self, 'depth')
        row.prop(self, 'fade')

        row = column.row(align=True)
        row.prop(self, 'h1', text='')
        row.prop(self, 'h3', text='')
        row.prop(self, 'h2', text='')
        row.prop(self, 'h4', text='')

        r = row.row(align=True)
        r.active = True if self.h4 else False
        r.prop(self, 'flip', toggle=True)

    def invoke(self, context, event):
        get_mouse_pos(self, context, event)
        return self.execute(context)

    def execute(self, context):
        debug = True
        debug = False

        active = context.active_object
        mx = active.matrix_world

        bm = bmesh.from_edit_mesh(active.data)
        bm.normal_update()

        selverts = [v for v in bm.verts if v.select]
        selfaces = [f for f in bm.faces if f.select]

        if selfaces:

            if all(len(f.verts) == 4 for f in selfaces):
                boundary = get_boundary_edges(selfaces)
                sequences = get_edges_vert_sequences(selverts, boundary, debug=False)

                if len(sequences) == 2:
                    seq1, seq2 = sequences

                    verts1, cyclic1 = seq1
                    verts2, cyclic2 = seq2

                    if self.flip:
                        verts1, verts2 = verts2, verts1
                        cyclic1, cyclic2 = cyclic2, cyclic1

                    if cyclic1 == cyclic2 and cyclic1 is True and len(verts1) == len(verts2) and len(verts1) >= 5:
                        smooth = selfaces[0].smooth

                        if smooth:
                            if not get_auto_smooth(active):
                                add_auto_smooth(active)

                        for v in verts1 + verts2:
                            v.select_set(False)

                        bm.select_flush(False)

                        self.segments = len(verts1)

                        center1 = average_locations([v.co for v in verts1])
                        center2 = average_locations([v.co for v in verts2])

                        if debug:
                            draw_point(center1, color=green, mx=mx, modal=False)
                            draw_point(center2, color=red, mx=mx, modal=False)

                        radius1 = (center1 - verts1[0].co).length
                        radius2 = (center2 - verts2[0].co).length
                        self.radius = (radius1 + radius2) / 2

                        depth = self.depth / 100 * self.radius

                        thread, bottom, top, height = calculate_thread(segments=self.segments, loops=self.loops, radius=self.radius, depth=depth, h1=self.h1, h2=self.h2, h3=self.h3, h4=self.h4, fade=self.fade / 100)

                        if height != 0:

                            verts, faces = self.build_faces(bm, thread, bottom, top, smooth=smooth)

                            selheight = (center1 - center2).length
                            bmesh.ops.scale(bm, vec=Vector((1, 1, selheight / height)), space=Matrix(), verts=verts)

                            bmesh.ops.translate(bm, vec=center1, space=Matrix(), verts=verts)

                            selup = (center2 - center1).normalized()

                            if debug:
                                draw_vector(selup, origin=center1, mx=mx, modal=False)

                            selrot = Vector((0, 0, 1)).rotation_difference(selup)

                            if debug:
                                print(selrot.axis, degrees(selrot.angle))

                            bmesh.ops.rotate(bm, cent=center1, matrix=selrot.to_matrix(), verts=verts, space=Matrix())

                            if bm.faces.active and bm.faces.active in selfaces:
                                active_loops = [loop for v in bm.faces.active.verts if v in verts1 for loop in v.link_loops if loop.face == bm.faces.active]

                                if active_loops[0].link_loop_next.vert == active_loops[1].vert:
                                    v1 = active_loops[1].vert
                                else:
                                    v1 = active_loops[0].vert
                            else:
                                v1 = verts1[0]

                            threadvec = (verts[0].co - center1).normalized()
                            selvec = (v1.co - center1).normalized()

                            if debug:
                                draw_vector(threadvec, origin=center1, mx=mx, color=green, modal=False)
                                draw_vector(selvec, origin=center1, mx=mx, color=red, modal=False)

                            dot = threadvec.dot(selvec)

                            if round(dot, 6) == -1:
                                print("WARNING: using manual 180 selup quat")
                                matchrot = Quaternion(selup, radians(180))

                            else:
                                matchrot = threadvec.rotation_difference(selvec)

                            if debug:
                                print(matchrot.axis, degrees(matchrot.angle))

                            bmesh.ops.rotate(bm, cent=center1, matrix=matchrot.to_matrix(), verts=verts, space=Matrix())

                            bmesh.ops.remove_doubles(bm, verts=verts + verts1 + verts2, dist=0.00001)

                            bmesh.ops.delete(bm, geom=selfaces, context='FACES')

                            bmesh.ops.recalc_face_normals(bm, faces=[f for f in faces if f.is_valid])

                            bmesh.update_edit_mesh(active.data)
                        return {'FINISHED'}

                draw_fading_label(context, "Make a cyclic, cylindrical Face Selection!", x=self.HUD_x, y=self.HUD_y, color=yellow, move_y=30, time=3)
            else:
                draw_fading_label(context, "Make a cyclic, cylindrical Face Selection consisting of all quad faces only!", x=self.HUD_x, y=self.HUD_y, color=yellow, move_y=30, time=3)

        return {'CANCELLED'}

    def build_faces(self, bm, thread, bottom, top, smooth=False):
        verts = []

        for co in thread[0]:
            v = bm.verts.new(co)
            verts.append(v)

        faces = []

        for ids in thread[1]:
            f = bm.faces.new([verts[idx] for idx in ids])
            f.smooth = smooth
            faces.append(f)

            if smooth:
                f.edges[0].smooth = False
                f.edges[-2].smooth = False

        bottom_verts = []

        for co in bottom[0]:
            v = bm.verts.new(co)
            bottom_verts.append(v)

        bottom_faces = []

        for ids in bottom[1]:
            f = bm.faces.new([bottom_verts[idx] for idx in ids])
            f.smooth = smooth
            bottom_faces.append(f)

            if smooth:
                if len(ids) == 4:
                    f.edges[-2].smooth = False
                    f.edges[0].smooth = False
                else:
                    f.edges[-1].smooth = False
                    f.edges[1].smooth = False

        top_verts = []

        for co in top[0]:
            v = bm.verts.new(co)
            top_verts.append(v)

        top_faces = []

        for ids in top[1]:
            f = bm.faces.new([top_verts[idx] for idx in ids])
            f.smooth = smooth
            top_faces.append(f)

            if smooth:
                if len(ids) == 4:
                    f.edges[-2].smooth = False
                    f.edges[0].smooth = False
                else:
                    f.edges[-1].smooth = False
                    f.edges[1].smooth = False

        return [v for v in verts + bottom_verts + top_verts if v.is_valid], faces + bottom_faces + top_faces
