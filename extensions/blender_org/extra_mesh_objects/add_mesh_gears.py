# SPDX-FileCopyrightText: 2009-2010 Michel J. Anders (varkenvarken)
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from bpy.types import Operator
from math import (
        atan, asin, cos,
        sin, tan, pi,
        radians,
        )
from bpy.props import (
        FloatProperty,
        IntProperty,
        BoolProperty,
        StringProperty,
        FloatVectorProperty
        )
from mathutils import (
        Vector,
        Matrix,
        )
from bpy_extras import object_utils
from .interface import draw_transform_props

# A very simple "bridge" tool.
# Connects two equally long vertex rows with faces.
# Returns a list of the new faces (list of  lists)
#
# vertIdx1 ... First vertex list (list of vertex indices)
# vertIdx2 ... Second vertex list (list of vertex indices)
# closed ... Creates a loop (first & last are closed)
# flipped ... Invert the normal of the face(s)
#
# Note: You can set vertIdx1 to a single vertex index to create
#       a fan/star of faces
# Note: If both vertex idx list are the same length they have
#       to have at least 2 vertices

def createFaces(vertIdx1, vertIdx2, closed=False, flipped=False):
    faces = []

    if not vertIdx1 or not vertIdx2:
        return None

    if len(vertIdx1) < 2 and len(vertIdx2) < 2:
        return None

    fan = False
    if (len(vertIdx1) != len(vertIdx2)):
        if (len(vertIdx1) == 1 and len(vertIdx2) > 1):
            fan = True
        else:
            return None

    total = len(vertIdx2)

    if closed:
        # Bridge the start with the end.
        if flipped:
            face = [
                vertIdx1[0],
                vertIdx2[0],
                vertIdx2[total - 1]]
            if not fan:
                face.append(vertIdx1[total - 1])
            faces.append(face)

        else:
            face = [vertIdx2[0], vertIdx1[0]]
            if not fan:
                face.append(vertIdx1[total - 1])
            face.append(vertIdx2[total - 1])
            faces.append(face)

    # Bridge the rest of the faces.
    for num in range(total - 1):
        if flipped:
            if fan:
                face = [vertIdx2[num], vertIdx1[0], vertIdx2[num + 1]]
            else:
                face = [vertIdx2[num], vertIdx1[num],
                    vertIdx1[num + 1], vertIdx2[num + 1]]
            faces.append(face)
        else:
            if fan:
                face = [vertIdx1[0], vertIdx2[num], vertIdx2[num + 1]]
            else:
                face = [vertIdx1[num], vertIdx2[num],
                    vertIdx2[num + 1], vertIdx1[num + 1]]
            faces.append(face)

    return faces


# Calculate the vertex coordinates for a single
# section of a gear tooth.
# Returns 4 lists of vertex coords (list of tuples):
#  *-*---*---*  (1.) verts_inner_base
#  | |   |   |
#  *-*---*---*  (2.) verts_outer_base
#    |   |   |
#    *---*---*  (3.) verts_middle_tooth
#     \  |  /
#      *-*-*    (4.) verts_tip_tooth
#
# a
# t
# d
# radius
# Ad
# De
# base
# p_angle
# rack
# crown

def add_tooth(a, t, d, radius, Ad, De, base, p_angle, rack=0, crown=0.0):
    A = [a, a + t / 4, a + t / 2, a + 3 * t / 4]
    C = [cos(i) for i in A]
    S = [sin(i) for i in A]

    Ra = radius + Ad
    Rd = radius - De
    Rb = Rd - base

    # Pressure angle calc
    O = Ad * tan(p_angle)
    if Ra != 0:
        p_angle = atan(O / Ra)
    else:
        p_angle = atan(O)

    if radius < 0:
        p_angle = -p_angle

    if rack:
        S = [sin(t / 4) * I for I in range(-2, 3)]
        Sp = [0, sin(-t / 4 + p_angle), 0, sin(t / 4 - p_angle)]

        verts_inner_base = [(Rb, radius * S[I], d) for I in range(4)]
        verts_outer_base = [(Rd, radius * S[I], d) for I in range(4)]
        verts_middle_tooth = [(radius, radius * S[I], d) for I in range(1, 4)]
        verts_tip_tooth = [(Ra, radius * Sp[I], d) for I in range(1, 4)]

    else:
        Cp = [
            0,
            cos(a + t / 4 + p_angle),
            cos(a + t / 2),
            cos(a + 3 * t / 4 - p_angle)]
        Sp = [0,
            sin(a + t / 4 + p_angle),
            sin(a + t / 2),
            sin(a + 3 * t / 4 - p_angle)]

        verts_inner_base = [(Rb * C[I], Rb * S[I], d)
            for I in range(4)]
        verts_outer_base = [(Rd * C[I], Rd * S[I], d)
            for I in range(4)]
        verts_middle_tooth = [(radius * C[I], radius * S[I], d + crown / 3)
            for I in range(1, 4)]
        verts_tip_tooth = [(Ra * Cp[I], Ra * Sp[I], d + crown)
            for I in range(1, 4)]

    return (verts_inner_base, verts_outer_base,
        verts_middle_tooth, verts_tip_tooth)


# EXPERIMENTAL Calculate the vertex coordinates for a single
# section of a gearspoke.
# Returns them as a list of tuples
#
# a
# t
# d
# radius
# De
# base
# s
# w
# l
# gap
# width
#
# @todo Finish this.

def add_spoke(a, t, d, radius, De, base, s, w, l, gap=0, width=19):
    Rd = radius - De
    Rb = Rd - base

    verts = []
    edgefaces = []
    edgefaces2 = []
    sf = []

    if not gap:
        for N in range(width, 1, -2):
            edgefaces.append(len(verts))
            ts = t / 4
            tm = a + 2 * ts
            te = asin(w / Rb)
            td = te - ts
            t4 = ts + td * (width - N) / (width - 3.0)
            A = [tm + (i - int(N / 2)) * t4 for i in range(N)]
            C = [cos(i) for i in A]
            S = [sin(i) for i in A]

            verts.extend((Rb * I, Rb * J, d) for (I, J) in zip(C, S))
            edgefaces2.append(len(verts) - 1)

            Rb = Rb - s

        n = 0
        for N in range(width, 3, -2):
            sf.extend([(i + n, i + 1 + n, i + 2 + n, i + N + n)
                for i in range(0, N - 1, 2)])
            sf.extend([(i + 2 + n, i + N + n, i + N + 1 + n, i + N + 2 + n)
                for i in range(0, N - 3, 2)])

            n = n + N

    return verts, edgefaces, edgefaces2, sf


# Create gear geometry.
# Returns:
# * A list of vertices (list of tuples)
# * A list of faces (list of lists)
# * A list (group) of vertices of the tip (list of vertex indices)
# * A list (group) of vertices of the valley (list of vertex indices)
#
# teethNum ... Number of teeth on the gear
# radius ... Radius of the gear, negative for crown gear
# Ad ... Addendum, extent of tooth above radius
# De ... Dedendum, extent of tooth below radius
# base ... Base, extent of gear below radius
# p_angle ... Pressure angle. Skewness of tooth tip. (radiant)
# width ... Width, thickness of gear
# skew ... Skew of teeth. (radiant)
# conangle ... Conical angle of gear. (radiant)
# rack
# crown ... Inward pointing extend of crown teeth
#
# inner radius = radius - (De + base)

def add_gear(teethNum, radius, Ad, De, base, p_angle,
             width=1, skew=0, conangle=0, rack=0, crown=0.0):

    if teethNum < 2:
        return None, None, None, None

    t = 2 * pi / teethNum

    if rack:
        teethNum = 1

    #print(radius, width, conangle)
    if radius != 0:
        scale = (radius - 2 * width * tan(conangle)) / radius
    else:
        scale = radius - 2 * width * tan(conangle)

    verts = []
    faces = []
    vgroup_top = []  # Vertex group of top/tip? vertices.
    vgroup_valley = []  # Vertex group of valley vertices

    verts_bridge_prev = []
    for toothCnt in range(teethNum):
        a = toothCnt * t

        verts_bridge_start = []
        verts_bridge_end = []

        verts_outside_top = []
        verts_outside_bottom = []
        for (s, d, c, top) \
           in [(0, -width, 1, True), (skew, width, scale, False)]:

            verts1, verts2, verts3, verts4 = add_tooth(a + s, t, d,
                radius * c, Ad * c, De * c, base * c, p_angle,
                rack, crown)

            vertsIdx1 = list(range(len(verts), len(verts) + len(verts1)))
            verts.extend(verts1)
            vertsIdx2 = list(range(len(verts), len(verts) + len(verts2)))
            verts.extend(verts2)
            vertsIdx3 = list(range(len(verts), len(verts) + len(verts3)))
            verts.extend(verts3)
            vertsIdx4 = list(range(len(verts), len(verts) + len(verts4)))
            verts.extend(verts4)

            verts_outside = []
            verts_outside.extend(vertsIdx2[:2])
            verts_outside.append(vertsIdx3[0])
            verts_outside.extend(vertsIdx4)
            verts_outside.append(vertsIdx3[-1])
            verts_outside.append(vertsIdx2[-1])

            if top:
                # verts_inside_top = vertsIdx1
                verts_outside_top = verts_outside

                verts_bridge_start.append(vertsIdx1[0])
                verts_bridge_start.append(vertsIdx2[0])
                verts_bridge_end.append(vertsIdx1[-1])
                verts_bridge_end.append(vertsIdx2[-1])

            else:
                # verts_inside_bottom = vertsIdx1
                verts_outside_bottom = verts_outside

                verts_bridge_start.append(vertsIdx2[0])
                verts_bridge_start.append(vertsIdx1[0])
                verts_bridge_end.append(vertsIdx2[-1])
                verts_bridge_end.append(vertsIdx1[-1])

            # Valley = first 2 vertices of outer base:
            vgroup_valley.extend(vertsIdx2[:1])
            # Top/tip vertices:
            vgroup_top.extend(vertsIdx4)

            faces_tooth_middle_top = createFaces(vertsIdx2[1:], vertsIdx3,
                flipped=top)
            faces_tooth_outer_top = createFaces(vertsIdx3, vertsIdx4,
                flipped=top)

            faces_base_top = createFaces(vertsIdx1, vertsIdx2, flipped=top)
            faces.extend(faces_base_top)

            faces.extend(faces_tooth_middle_top)
            faces.extend(faces_tooth_outer_top)

        # faces_inside = createFaces(verts_inside_top, verts_inside_bottom)
        # faces.extend(faces_inside)

        faces_outside = createFaces(verts_outside_top, verts_outside_bottom,
            flipped=True)
        faces.extend(faces_outside)

        if toothCnt == 0:
            verts_bridge_first = verts_bridge_start

        # Bridge one tooth to the next
        if verts_bridge_prev:
            faces_bridge = createFaces(verts_bridge_prev, verts_bridge_start)
            faces.extend(faces_bridge)

        # Remember "end" vertices for next tooth.
        verts_bridge_prev = verts_bridge_end

    # Bridge the first to the last tooth.
    faces_bridge_f_l = createFaces(verts_bridge_prev, verts_bridge_first)
    faces.extend(faces_bridge_f_l)

    return verts, faces, vgroup_top, vgroup_valley


# Create spokes geometry
# Returns:
# * A list of vertices (list of tuples)
# * A list of faces (list of lists)
#
# teethNum ... Number of teeth on the gear.
# radius ... Radius of the gear, negative for crown gear
# De ... Dedendum, extent of tooth below radius
# base ... Base, extent of gear below radius
# width ... Width, thickness of gear
# conangle ... Conical angle of gear. (radiant)
# rack
# spoke
# spbevel
# spwidth
# splength
# spresol
#
# @todo Finish this
# @todo Create a function that takes a "Gear" and creates a
#       matching "Gear Spokes" object

def add_spokes(teethNum, radius, De, base, width=1, conangle=0, rack=0,
               spoke=3, spbevel=0.1, spwidth=0.2, splength=1.0, spresol=9):

    if teethNum < 2:
        return None, None, None, None

    if spoke < 2:
        return None, None, None, None

    t = 2 * pi / teethNum

    if rack:
        teethNum = 1

    scale = (radius - 2 * width * tan(conangle)) / radius

    verts = []
    faces = []

    c = scale   # debug

    fl = len(verts)
    for toothCnt in range(teethNum):
        a = toothCnt * t
        s = 0       # For test

        if toothCnt % spoke == 0:
            for d in (-width, width):
                sv, edgefaces, edgefaces2, sf = add_spoke(a + s, t, d,
                    radius * c, De * c, base * c,
                    spbevel, spwidth, splength, 0, spresol)
                verts.extend(sv)
                faces.extend([j + fl for j in i] for i in sf)
                fl += len(sv)

            d1 = fl - len(sv)
            d2 = fl - 2 * len(sv)

            faces.extend([(i + d2, j + d2, j + d1, i + d1)
                for (i, j) in zip(edgefaces[:-1], edgefaces[1:])])
            faces.extend([(i + d2, j + d2, j + d1, i + d1)
                for (i, j) in zip(edgefaces2[:-1], edgefaces2[1:])])

        else:
            for d in (-width, width):
                sv, edgefaces, edgefaces2, sf = add_spoke(a + s, t, d,
                    radius * c, De * c, base * c,
                    spbevel, spwidth, splength, 1, spresol)

                verts.extend(sv)
                fl += len(sv)

            d1 = fl - len(sv)
            d2 = fl - 2 * len(sv)

            faces.extend([[i + d2, i + 1 + d2, i + 1 + d1, i + d1]
                for (i) in range(0, 3)])
            faces.extend([[i + d2, i + 1 + d2, i + 1 + d1, i + d1]
                for (i) in range(5, 8)])

    return verts, faces


# Create worm geometry.
# Returns:
# * A list of vertices
# * A list of faces
# * A list (group) of vertices of the tip
# * A list (group) of vertices of the valley
#
# teethNum ... Number of teeth on the worm
# radius ... Radius of the gear, negative for crown gear
# Ad ... Addendum, extent of tooth above radius
# De ... Dedendum, extent of tooth below radius
# p_angle ... Pressure angle. Skewness of tooth tip. (radiant)
# width ... Width, thickness of gear
# crown ... Inward pointing extend of crown teeth
#
# @todo: Fix teethNum. Some numbers are not possible yet
# @todo: Create start & end geometry (closing faces)

def add_worm(teethNum, rowNum, radius, Ad, De, p_angle,
             width=1, skew=radians(11.25), crown=0.0):

    worm = teethNum
    teethNum = 24

    t = 2 * pi / teethNum

    verts = []
    faces = []
    vgroup_top = []  # Vertex group of top/tip? vertices.
    vgroup_valley = []  # Vertex group of valley vertices

    # width = width / 2.0

    edgeloop_prev = []
    for Row in range(rowNum):
        edgeloop = []

        for toothCnt in range(teethNum):
            a = toothCnt * t

            s = Row * skew
            d = Row * width
            c = 1

            isTooth = False
            if toothCnt % (teethNum / worm) != 0:
                # Flat
                verts1, verts2, verts3, verts4 = add_tooth(a + s, t, d,
                    radius - De, 0.0, 0.0, 0, p_angle)

                # Ignore other verts than the "other base".
                verts1 = verts3 = verts4 = []

            else:
                # Tooth
                isTooth = True
                verts1, verts2, verts3, verts4 = add_tooth(a + s, t, d,
                    radius * c, Ad * c, De * c, 0 * c, p_angle, 0, crown)

                # Remove various unneeded verts (if we are "inside" the tooth)
                del(verts2[2])  # Central vertex in the base of the tooth.
                del(verts3[1])  # Central vertex in the middle of the tooth.

            vertsIdx2 = list(range(len(verts), len(verts) + len(verts2)))
            verts.extend(verts2)
            vertsIdx3 = list(range(len(verts), len(verts) + len(verts3)))
            verts.extend(verts3)
            vertsIdx4 = list(range(len(verts), len(verts) + len(verts4)))
            verts.extend(verts4)

            if isTooth:
                verts_current = []
                verts_current.extend(vertsIdx2[:2])
                verts_current.append(vertsIdx3[0])
                verts_current.extend(vertsIdx4)
                verts_current.append(vertsIdx3[-1])
                verts_current.append(vertsIdx2[-1])

                # Valley = first 2 vertices of outer base:
                vgroup_valley.extend(vertsIdx2[:1])
                # Top/tip vertices:
                vgroup_top.extend(vertsIdx4)

            else:
                # Flat
                verts_current = vertsIdx2

                # Valley - all of them.
                vgroup_valley.extend(vertsIdx2)

            edgeloop.extend(verts_current)

        # Create faces between rings/rows.
        if edgeloop_prev:
            faces_row = createFaces(edgeloop, edgeloop_prev, closed=True)
            faces.extend(faces_row)

        # Remember last ring/row of vertices for next ring/row iteration.
        edgeloop_prev = edgeloop

    return verts, faces, vgroup_top, vgroup_valley

def AddGearMesh(self, context):

    verts, faces, verts_tip, verts_valley = add_gear(
            self.number_of_teeth,
            self.radius,
            self.addendum,
            self.dedendum,
            self.base,
            self.angle,
            width=self.width,
            skew=self.skew,
            conangle=self.conangle,
            crown=self.crown
            )

    mesh = bpy.data.meshes.new("Gear")
    mesh.from_pydata(verts, [], faces)

    return mesh, verts_tip, verts_valley


class AddGear(Operator, object_utils.AddObjectHelper):
    bl_idname = "mesh.primitive_gear"
    bl_label = "Add Gear"
    bl_description = "Construct a gear mesh"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    Gear : BoolProperty(name = "Gear",
                default = True,
                description = "Gear")

    #### change properties
    name : StringProperty(name = "Name",
                    description = "Name")

    change : BoolProperty(name = "Change",
                default = False,
                description = "change Gear")

    number_of_teeth: IntProperty(name="Teeth",
            description="Number of teeth on the gear",
            min=2,
            soft_max=1000,
            default=12
            )
    radius: FloatProperty(name="Radius",
            description="Radius of the gear, negative for crown gear",
            soft_min=-1000.0,
            soft_max=1000.0,
            unit='LENGTH',
            default=1.0
            )
    addendum: FloatProperty(name="Addendum",
            description="Addendum, extent of tooth above radius",
            soft_min=-1000.0,
            soft_max=1000.0,
            unit='LENGTH',
            default=0.1
            )
    dedendum: FloatProperty(name="Dedendum",
            description="Dedendum, extent of tooth below radius",
            soft_min=-1000.0,
            soft_max=1000.0,
            unit='LENGTH',
            default=0.1
            )
    angle: FloatProperty(name="Pressure Angle",
            description="Pressure angle, skewness of tooth tip",
            soft_min=radians(-45.0),
            soft_max=radians(45.0),
            unit='ROTATION',
            default=radians(20.0)
            )
    base: FloatProperty(name="Base",
            description="Base, extent of gear below radius",
            soft_min=-1000.0,
            soft_max=1000.0,
            unit='LENGTH',
            default=0.2
            )
    width: FloatProperty(name="Width",
            description="Width, thickness of gear",
            soft_min=-1000.0,
            soft_max=1000.0,
            unit='LENGTH',
            default=0.2
            )
    skew: FloatProperty(name="Skewness",
            description="Skew of teeth",
            soft_min=radians(-360.0),
            soft_max=radians(360.0),
            unit='ROTATION',
            default=radians(0.0)
            )
    conangle: FloatProperty(name="Conical Angle",
            description="Conical angle of gear",
            soft_min=radians(-360.0),
            soft_max=radians(360.0),
            unit='ROTATION',
            default=radians(0.0)
            )
    crown: FloatProperty(name="Crown",
            description="Inward pointing extend of crown teeth",
            soft_min=-1000.0,
            soft_max=1000.0,
            unit='LENGTH',
            default=0.0
            )

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.separator()
        layout.prop(self, 'number_of_teeth')
        layout.separator()
        layout.prop(self, 'radius')
        layout.prop(self, 'width')
        layout.prop(self, 'base')
        layout.separator()
        layout.prop(self, 'dedendum')
        layout.prop(self, 'addendum')
        layout.separator()
        layout.prop(self, 'angle')
        layout.prop(self, 'skew')
        layout.prop(self, 'conangle')
        layout.prop(self, 'crown')

        if self.change == False:
            layout.separator()
            draw_transform_props(self, layout)

    @classmethod
    def poll(cls, context):
        return context.scene is not None

    def execute(self, context):
        # turn off 'Enter Edit Mode'
        use_enter_edit_mode = bpy.context.preferences.edit.use_enter_edit_mode
        bpy.context.preferences.edit.use_enter_edit_mode = False

        if bpy.context.mode == "OBJECT":
            if context.selected_objects != [] and context.active_object and \
                (context.active_object.data is not None) and ('Gear' in context.active_object.data.keys()) and \
                (self.change == True):
                obj = context.active_object
                oldmesh = obj.data
                oldmeshname = obj.data.name
                mesh, verts_tip, verts_valley = AddGearMesh(self, context)
                obj.data = mesh
                try:
                    bpy.ops.object.vertex_group_remove(all=True)
                except:
                    pass

                for material in oldmesh.materials:
                    obj.data.materials.append(material)

                bpy.data.meshes.remove(oldmesh)
                obj.data.name = oldmeshname
            else:
                mesh, verts_tip, verts_valley = AddGearMesh(self, context)
                obj = object_utils.object_data_add(context, mesh, operator=self)

            # Create vertex groups from stored vertices.
            tipGroup = obj.vertex_groups.new(name='Tips')
            tipGroup.add(verts_tip, 1.0, 'ADD')

            valleyGroup = obj.vertex_groups.new(name='Valleys')
            valleyGroup.add(verts_valley, 1.0, 'ADD')

            obj.data["Gear"] = True
            obj.data["change"] = False
            for prm in GearParameters():
                obj.data[prm] = getattr(self, prm)

        if bpy.context.mode == "EDIT_MESH":
            active_object = context.active_object
            name_active_object = active_object.name
            bpy.ops.object.mode_set(mode='OBJECT')
            mesh, verts_tip, verts_valley = AddGearMesh(self, context)
            obj = object_utils.object_data_add(context, mesh, operator=self)

            # Create vertex groups from stored vertices.
            tipGroup = obj.vertex_groups.new(name='Tips')
            tipGroup.add(verts_tip, 1.0, 'ADD')

            valleyGroup = obj.vertex_groups.new(name='Valleys')
            valleyGroup.add(verts_valley, 1.0, 'ADD')

            obj.select_set(True)
            active_object.select_set(True)
            bpy.context.view_layer.objects.active = active_object
            bpy.ops.object.join()
            context.active_object.name = name_active_object
            bpy.ops.object.mode_set(mode='EDIT')

        if use_enter_edit_mode:
            bpy.ops.object.mode_set(mode = 'EDIT')

        # restore pre operator state
        bpy.context.preferences.edit.use_enter_edit_mode = use_enter_edit_mode

        return {'FINISHED'}

    def invoke(self, context, event):
        self.execute(context)

        return {'FINISHED'}

def GearParameters():
    GearParameters = [
        "number_of_teeth",
        "radius",
        "addendum",
        "dedendum",
        "base",
        "angle",
        "width",
        "skew",
        "conangle",
        "crown",
        ]
    return GearParameters

def AddWormGearMesh(self, context):

    verts, faces, verts_tip, verts_valley = add_worm(
            self.number_of_teeth,
            self.number_of_rows,
            self.radius,
            self.addendum,
            self.dedendum,
            self.angle,
            width=self.row_height,
            skew=self.skew,
            crown=self.crown
            )

    mesh = bpy.data.meshes.new("Worm Gear")
    mesh.from_pydata(verts, [], faces)

    return mesh, verts_tip, verts_valley


class AddWormGear(Operator, object_utils.AddObjectHelper):
    bl_idname = "mesh.primitive_worm_gear"
    bl_label = "Add Worm Gear"
    bl_description = "Construct a worm gear mesh"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    WormGear : BoolProperty(name = "WormGear",
                default = True,
                description = "WormGear")

    #### change properties
    name : StringProperty(name = "Name",
                    description = "Name")

    change : BoolProperty(name = "Change",
                default = False,
                description = "change WormGear")

    number_of_teeth: IntProperty(
            name="Teeth",
            description="Number of teeth on the gear",
            min=1,
            soft_max=1000,
            default=12
            )
    number_of_rows: IntProperty(
            name="Rows",
            description="Number of rows on the worm gear",
            min=0,
            soft_max=1000,
            default=32
            )
    radius: FloatProperty(
            name="Radius",
            description="Radius of the gear, negative for crown gear",
            soft_min=-1000.0,
            soft_max=1000.0,
            unit='LENGTH',
            default=1.0
            )
    addendum: FloatProperty(
            name="Addendum",
            description="Addendum, extent of tooth above radius",
            soft_min=-1000.0,
            soft_max=1000.0,
            unit='LENGTH',
            default=0.1
            )
    dedendum: FloatProperty(
            name="Dedendum",
            description="Dedendum, extent of tooth below radius",
            soft_min=-1000.0,
            soft_max=1000.0,
            unit='LENGTH',
            default=0.1
            )
    angle: FloatProperty(
            name="Pressure Angle",
            description="Pressure angle, skewness of tooth tip",
            soft_min=radians(-45.0),
            soft_max=radians(45.0),
            default=radians(20.0),
            unit='ROTATION'
            )
    row_height: FloatProperty(
            name="Row Height",
            description="Height of each Row",
            soft_min=-1000.0,
            soft_max=1000.0,
            unit='LENGTH',
            default=0.2
            )
    skew: FloatProperty(
            name="Skewness per Row",
            description="Skew of each row",
            soft_min=radians(-360.0),
            soft_max=radians(360.0),
            default=radians(11.25),
            unit='ROTATION'
            )
    crown: FloatProperty(
            name="Crown",
            description="Inward pointing extend of crown teeth",
            soft_min=-1000.0,
            soft_max=1000.0,
            unit='LENGTH',
            default=0.0
            )

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.separator()
        layout.prop(self, "number_of_teeth")
        layout.prop(self, "number_of_rows")
        layout.separator()
        layout.prop(self, "radius")
        layout.prop(self, "row_height")
        layout.separator()
        layout.prop(self, "addendum")
        layout.prop(self, "dedendum")
        layout.separator()
        layout.prop(self, "angle")
        layout.prop(self, "skew")
        layout.prop(self, "crown")

        if self.change == False:
            layout.separator()
            draw_transform_props(self, layout)

    def execute(self, context):
        # turn off 'Enter Edit Mode'
        use_enter_edit_mode = bpy.context.preferences.edit.use_enter_edit_mode
        bpy.context.preferences.edit.use_enter_edit_mode = False

        if bpy.context.mode == "OBJECT":
            if context.selected_objects != [] and context.active_object and \
                (context.active_object.data is not None) and ('WormGear' in context.active_object.data.keys()) and \
                (self.change == True):
                obj = context.active_object
                oldmesh = obj.data
                oldmeshname = obj.data.name

                mesh, verts_tip, verts_valley = AddWormGearMesh(self, context)
                obj.data = mesh
                try:
                    bpy.ops.object.vertex_group_remove(all=True)
                except:
                    pass

                for material in oldmesh.materials:
                    obj.data.materials.append(material)

                bpy.data.meshes.remove(oldmesh)
                obj.data.name = oldmeshname
            else:
                mesh, verts_tip, verts_valley = AddWormGearMesh(self, context)
                obj = object_utils.object_data_add(context, mesh, operator=self)

            # Create vertex groups from stored vertices.
            tipGroup = obj.vertex_groups.new(name = 'Tips')
            tipGroup.add(verts_tip, 1.0, 'ADD')

            valleyGroup = obj.vertex_groups.new(name = 'Valleys')
            valleyGroup.add(verts_valley, 1.0, 'ADD')

            obj.data["WormGear"] = True
            obj.data["change"] = False
            for prm in WormGearParameters():
                obj.data[prm] = getattr(self, prm)

        if bpy.context.mode == "EDIT_MESH":
            active_object = context.active_object
            name_active_object = active_object.name
            bpy.ops.object.mode_set(mode='OBJECT')
            mesh, verts_tip, verts_valley = AddWormGearMesh(self, context)
            obj = object_utils.object_data_add(context, mesh, operator=self)

            # Create vertex groups from stored vertices.
            tipGroup = obj.vertex_groups.new(name = 'Tips')
            tipGroup.add(verts_tip, 1.0, 'ADD')

            valleyGroup = obj.vertex_groups.new(name = 'Valleys')
            valleyGroup.add(verts_valley, 1.0, 'ADD')

            obj.select_set(True)
            active_object.select_set(True)
            bpy.context.view_layer.objects.active = active_object
            bpy.ops.object.join()
            context.active_object.name = name_active_object
            bpy.ops.object.mode_set(mode='EDIT')

        if use_enter_edit_mode:
            bpy.ops.object.mode_set(mode = 'EDIT')

        # restore pre operator state
        bpy.context.preferences.edit.use_enter_edit_mode = use_enter_edit_mode

        return {'FINISHED'}

def WormGearParameters():
    WormGearParameters = [
        "number_of_teeth",
        "number_of_rows",
        "radius",
        "addendum",
        "dedendum",
        "angle",
        "row_height",
        "skew",
        "crown",
        ]
    return WormGearParameters
