# SPDX-FileCopyrightText: 2010-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

# Author: DreamPainter

import bpy
from math import sqrt
from mathutils import Vector
from functools import reduce
from bpy.props import (
        FloatProperty,
        EnumProperty,
        BoolProperty,
        )
from bpy_extras.object_utils import object_data_add


# function to make the reduce function work as a workaround to sum a list of vectors

def vSum(list):
    return reduce(lambda a, b: a + b, list)


# Get a copy of the input faces, but with the normals flipped by reversing the order of the vertex indices of each face.
def flippedFaceNormals(faces):
    return [list(reversed(vertexIndices)) for vertexIndices in faces]


# creates the 5 platonic solids as a base for the rest
#  plato: should be one of {"4","6","8","12","20"}. decides what solid the
#         outcome will be.
#  returns a list of vertices and faces

def source(plato):
    verts = []
    faces = []

    # Tetrahedron
    if plato == "4":
        # Calculate the necessary constants
        s = sqrt(2) / 3.0
        t = -1 / 3
        u = sqrt(6) / 3

        # create the vertices and faces
        v = [(0, 0, 1), (2 * s, 0, t), (-s, u, t), (-s, -u, t)]
        faces = [[0, 1, 2], [0, 2, 3], [0, 3, 1], [1, 3, 2]]

    # Hexahedron (cube)
    elif plato == "6":
        # Calculate the necessary constants
        s = 1 / sqrt(3)

        # create the vertices and faces
        v = [(-s, -s, -s), (s, -s, -s), (s, s, -s), (-s, s, -s), (-s, -s, s), (s, -s, s), (s, s, s), (-s, s, s)]
        faces = [[0, 3, 2, 1], [0, 1, 5, 4], [0, 4, 7, 3], [6, 5, 1, 2], [6, 2, 3, 7], [6, 7, 4, 5]]

    # Octahedron
    elif plato == "8":
        # create the vertices and faces
        v = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]
        faces = [[4, 0, 2], [4, 2, 1], [4, 1, 3], [4, 3, 0], [5, 2, 0], [5, 1, 2], [5, 3, 1], [5, 0, 3]]

    # Dodecahedron
    elif plato == "12":
        # Calculate the necessary constants
        s = 1 / sqrt(3)
        t = sqrt((3 - sqrt(5)) / 6)
        u = sqrt((3 + sqrt(5)) / 6)

        # create the vertices and faces
        v = [(s, s, s), (s, s, -s), (s, -s, s), (s, -s, -s), (-s, s, s), (-s, s, -s), (-s, -s, s), (-s, -s, -s),
             (t, u, 0), (-t, u, 0), (t, -u, 0), (-t, -u, 0), (u, 0, t), (u, 0, -t), (-u, 0, t), (-u, 0, -t), (0, t, u),
             (0, -t, u), (0, t, -u), (0, -t, -u)]
        faces = [[0, 8, 9, 4, 16], [0, 12, 13, 1, 8], [0, 16, 17, 2, 12], [8, 1, 18, 5, 9], [12, 2, 10, 3, 13],
                 [16, 4, 14, 6, 17], [9, 5, 15, 14, 4], [6, 11, 10, 2, 17], [3, 19, 18, 1, 13], [7, 15, 5, 18, 19],
                 [7, 11, 6, 14, 15], [7, 19, 3, 10, 11]]

    # Icosahedron
    elif plato == "20":
        # Calculate the necessary constants
        s = (1 + sqrt(5)) / 2
        t = sqrt(1 + s * s)
        s = s / t
        t = 1 / t

        # create the vertices and faces
        v = [(s, t, 0), (-s, t, 0), (s, -t, 0), (-s, -t, 0), (t, 0, s), (t, 0, -s), (-t, 0, s), (-t, 0, -s),
             (0, s, t), (0, -s, t), (0, s, -t), (0, -s, -t)]
        faces = [[0, 8, 4], [0, 5, 10], [2, 4, 9], [2, 11, 5], [1, 6, 8], [1, 10, 7], [3, 9, 6], [3, 7, 11],
                 [0, 10, 8], [1, 8, 10], [2, 9, 11], [3, 11, 9], [4, 2, 0], [5, 0, 2], [6, 1, 3], [7, 3, 1],
                 [8, 6, 4], [9, 4, 6], [10, 5, 7], [11, 7, 5]]

    # convert the tuples to Vectors
    verts = [Vector(i) for i in v]

    return verts, faces


# processes the raw data from source

def createSolid(plato, vtrunc, etrunc, dual, snub):
    # the duals from each platonic solid
    dualSource = {"4": "4",
                  "6": "8",
                  "8": "6",
                  "12": "20",
                  "20": "12"}

    # constants saving space and readability
    vtrunc *= 0.5
    etrunc *= 0.5
    supposedSize = 0
    noSnub = (snub == "None") or (etrunc == 0.5) or (etrunc == 0)
    lSnub = (snub == "Left") and (0 < etrunc < 0.5)
    rSnub = (snub == "Right") and (0 < etrunc < 0.5)

    # no truncation
    if vtrunc == 0:
        if dual:  # dual is as simple as another, but mirrored platonic solid
            vInput, fInput = source(dualSource[plato])
            supposedSize = vSum(vInput[i] for i in fInput[0]).length / len(fInput[0])
            vInput = [-i * supposedSize for i in vInput]            # mirror it
            # Inverting vInput turns the mesh inside-out, so normals need to be flipped.
            return vInput, flippedFaceNormals(fInput)
        return source(plato)
    elif 0 < vtrunc <= 0.5:  # simple truncation of the source
        vInput, fInput = source(plato)
    else:
        # truncation is now equal to simple truncation of the dual of the source
        vInput, fInput = source(dualSource[plato])
        supposedSize = vSum(vInput[i] for i in fInput[0]).length / len(fInput[0])
        vtrunc = 1 - vtrunc  # account for the source being a dual
        if vtrunc == 0:    # no truncation needed
            if dual:
                vInput, fInput = source(plato)
            vInput = [-i * supposedSize for i in vInput]
            # Inverting vInput turns the mesh inside-out, so normals need to be flipped.
            return vInput, flippedFaceNormals(fInput)

    # generate connection database
    vDict = [{} for i in vInput]
    # for every face, store what vertex comes after and before the current vertex
    for x in range(len(fInput)):
        i = fInput[x]
        for j in range(len(i)):
            vDict[i[j - 1]][i[j]] = [i[j - 2], x]
            if len(vDict[i[j - 1]]) == 1:
                vDict[i[j - 1]][-1] = i[j]

    # the actual connection database: exists out of:
    # [vtrunc pos, etrunc pos, connected vert IDs, connected face IDs]
    vData = [[[], [], [], []] for i in vInput]
    fvOutput = []      # faces created from truncated vertices
    feOutput = []      # faces created from truncated edges
    vOutput = []       # newly created vertices
    for x in range(len(vInput)):
        i = vDict[x]   # lookup the current vertex
        current = i[-1]
        while True:    # follow the chain to get a ccw order of connected verts and faces
            vData[x][2].append(i[current][0])
            vData[x][3].append(i[current][1])
            # create truncated vertices
            vData[x][0].append((1 - vtrunc) * vInput[x] + vtrunc * vInput[vData[x][2][-1]])
            current = i[current][0]
            if current == i[-1]:
                break                   # if we're back at the first: stop the loop
        fvOutput.append([])             # new face from truncated vert
        fOffset = x * (len(i) - 1)      # where to start off counting faceVerts
        # only create one vert where one is needed (v1 todo: done)
        if etrunc == 0.5:
            for j in range(len(i) - 1):
                vOutput.append((vData[x][0][j] + vData[x][0][j - 1]) * etrunc)  # create vert
                fvOutput[x].append(fOffset + j)                                 # add to face
            fvOutput[x] = fvOutput[x][1:] + [fvOutput[x][0]]                    # rotate face for ease later on
            # create faces from truncated edges.
            for j in range(len(i) - 1):
                if x > vData[x][2][j]:     # only create when other vertex has been added
                    index = vData[vData[x][2][j]][2].index(x)
                    feOutput.append([fvOutput[x][j], fvOutput[x][j - 1],
                                     fvOutput[vData[x][2][j]][index],
                                     fvOutput[vData[x][2][j]][index - 1]])
        # edge truncation between none and full
        elif etrunc > 0:
            for j in range(len(i) - 1):
                # create snubs from selecting verts from rectified meshes
                if rSnub:
                    vOutput.append(etrunc * vData[x][0][j] + (1 - etrunc) * vData[x][0][j - 1])
                    fvOutput[x].append(fOffset + j)
                elif lSnub:
                    vOutput.append((1 - etrunc) * vData[x][0][j] + etrunc * vData[x][0][j - 1])
                    fvOutput[x].append(fOffset + j)
                else:   # noSnub,  select both verts from rectified mesh
                    vOutput.append(etrunc * vData[x][0][j] + (1 - etrunc) * vData[x][0][j - 1])
                    vOutput.append((1 - etrunc) * vData[x][0][j] + etrunc * vData[x][0][j - 1])
                    fvOutput[x].append(2 * fOffset + 2 * j)
                    fvOutput[x].append(2 * fOffset + 2 * j + 1)
            # rotate face for ease later on
            if noSnub:
                fvOutput[x] = fvOutput[x][2:] + fvOutput[x][:2]
            else:
                fvOutput[x] = fvOutput[x][1:] + [fvOutput[x][0]]
            # create single face for each edge
            if noSnub:
                for j in range(len(i) - 1):
                    if x > vData[x][2][j]:
                        index = vData[vData[x][2][j]][2].index(x)
                        feOutput.append([fvOutput[x][j * 2], fvOutput[x][2 * j - 1],
                                         fvOutput[vData[x][2][j]][2 * index],
                                         fvOutput[vData[x][2][j]][2 * index - 1]])
            # create 2 tri's for each edge for the snubs
            elif rSnub:
                for j in range(len(i) - 1):
                    if x > vData[x][2][j]:
                        index = vData[vData[x][2][j]][2].index(x)
                        feOutput.append([fvOutput[x][j], fvOutput[x][j - 1],
                                         fvOutput[vData[x][2][j]][index]])
                        feOutput.append([fvOutput[x][j], fvOutput[vData[x][2][j]][index],
                                         fvOutput[vData[x][2][j]][index - 1]])
            elif lSnub:
                for j in range(len(i) - 1):
                    if x > vData[x][2][j]:
                        index = vData[vData[x][2][j]][2].index(x)
                        feOutput.append([fvOutput[x][j], fvOutput[x][j - 1],
                                         fvOutput[vData[x][2][j]][index - 1]])
                        feOutput.append([fvOutput[x][j - 1], fvOutput[vData[x][2][j]][index],
                                         fvOutput[vData[x][2][j]][index - 1]])
        # special rules for birectified mesh (v1 todo: done)
        elif vtrunc == 0.5:
            for j in range(len(i) - 1):
                if x < vData[x][2][j]:  # use current vert,  since other one has not passed yet
                    vOutput.append(vData[x][0][j])
                    fvOutput[x].append(len(vOutput) - 1)
                else:
                    # search for other edge to avoid duplicity
                    connectee = vData[x][2][j]
                    fvOutput[x].append(fvOutput[connectee][vData[connectee][2].index(x)])
        else:   # vert truncation only
            vOutput.extend(vData[x][0])   # use generated verts from way above
            for j in range(len(i) - 1):   # create face from them
                fvOutput[x].append(fOffset + j)

    # calculate supposed vertex length to ensure continuity
    if supposedSize and not dual:                    # this to make the vtrunc > 1 work
        supposedSize *= len(fvOutput[0]) / vSum(vOutput[i] for i in fvOutput[0]).length
        vOutput = [-i * supposedSize for i in vOutput]
        # Inverting vOutput turns the mesh inside-out, so normals need to be flipped.
        flipNormals = True
    else:
        flipNormals = False

    # create new faces by replacing old vert IDs by newly generated verts
    ffOutput = [[] for i in fInput]
    for x in range(len(fInput)):
        # only one generated vert per vertex,  so choose accordingly
        if etrunc == 0.5 or (etrunc == 0 and vtrunc == 0.5) or lSnub or rSnub:
            ffOutput[x] = [fvOutput[i][vData[i][3].index(x) - 1] for i in fInput[x]]
        # two generated verts per vertex
        elif etrunc > 0:
            for i in fInput[x]:
                ffOutput[x].append(fvOutput[i][2 * vData[i][3].index(x) - 1])
                ffOutput[x].append(fvOutput[i][2 * vData[i][3].index(x) - 2])
        else:   # cutting off corners also makes 2 verts
            for i in fInput[x]:
                ffOutput[x].append(fvOutput[i][vData[i][3].index(x)])
                ffOutput[x].append(fvOutput[i][vData[i][3].index(x) - 1])

    if not dual:
        fOutput = fvOutput + feOutput + ffOutput
        if flipNormals:
            fOutput = flippedFaceNormals(fOutput)
        return vOutput, fOutput
    else:
        # do the same procedure as above,  only now on the generated mesh
        # generate connection database
        vDict = [{} for i in vOutput]
        dvOutput = [0 for i in fvOutput + feOutput + ffOutput]
        dfOutput = []

        for x in range(len(dvOutput)):               # for every face
            i = (fvOutput + feOutput + ffOutput)[x]  # choose face to work with
            # find vertex from face
            normal = (vOutput[i[0]] - vOutput[i[1]]).cross(vOutput[i[2]] - vOutput[i[1]]).normalized()
            dvOutput[x] = normal / (normal.dot(vOutput[i[0]]))
            for j in range(len(i)):  # create vert chain
                vDict[i[j - 1]][i[j]] = [i[j - 2], x]
                if len(vDict[i[j - 1]]) == 1:
                    vDict[i[j - 1]][-1] = i[j]

        # calculate supposed size for continuity
        supposedSize = vSum([vInput[i] for i in fInput[0]]).length / len(fInput[0])
        supposedSize /= dvOutput[-1].length
        dvOutput = [i * supposedSize for i in dvOutput]

        # use chains to create faces
        for x in range(len(vOutput)):
            i = vDict[x]
            current = i[-1]
            face = []
            while True:
                face.append(i[current][1])
                current = i[current][0]
                if current == i[-1]:
                    break
            dfOutput.append(face)

        return dvOutput, dfOutput


class Solids(bpy.types.Operator):
    """Add one of the (regular) solids (mesh)"""
    bl_idname = "mesh.primitive_solid_add"
    bl_label = "Add Regular Solid"
    bl_description = "Add one of the Platonic, Archimedean or Catalan solids"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    source: EnumProperty(
                    items=(("4", "Tetrahedron", ""),
                            ("6", "Hexahedron", ""),
                            ("8", "Octahedron", ""),
                            ("12", "Dodecahedron", ""),
                            ("20", "Icosahedron", "")),
                    name="Source",
                    description="Starting point of your solid"
                    )
    size: FloatProperty(
                    name="Size",
                    description="Radius of the sphere through the vertices",
                    min=0.01,
                    soft_min=0.01,
                    max=100,
                    soft_max=100,
                    default=1.0
                    )
    vTrunc: FloatProperty(
                    name="Vertex Truncation",
                    description="Amount of vertex truncation",
                    min=0.0,
                    soft_min=0.0,
                    max=2.0,
                    soft_max=2.0,
                    default=0.0,
                    precision=3,
                    step=0.5
                    )
    eTrunc: FloatProperty(
                    name="Edge Truncation",
                    description="Amount of edge truncation",
                    min=0.0,
                    soft_min=0.0,
                    max=1.0,
                    soft_max=1.0,
                    default=0.0,
                    precision=3,
                    step=0.2
                    )
    snub: EnumProperty(
                    items=(("None", "No Snub", ""),
                           ("Left", "Left Snub", ""),
                           ("Right", "Right Snub", "")),
                    name="Snub",
                    description="Create the snub version"
                    )
    dual: BoolProperty(
                    name="Dual",
                    description="Create the dual of the current solid",
                    default=False
                    )
    keepSize: BoolProperty(
                    name="Keep Size",
                    description="Keep the whole solid at a constant size",
                    default=False
                    )

    def execute(self, context):
        # generate mesh
        verts, faces = createSolid(self.source,
                                   self.vTrunc,
                                   self.eTrunc,
                                   self.dual,
                                   self.snub
                                   )

        # resize to normal size, or if keepSize, make sure all verts are of length 'size'
        if self.keepSize:
            rad = self.size / verts[-1 if self.dual else 0].length
        else:
            rad = self.size
        verts = [i * rad for i in verts]

        # generate object
        # Create new mesh
        mesh = bpy.data.meshes.new("Solid")

        # Make a mesh from a list of verts/edges/faces.
        mesh.from_pydata(verts, [], faces)

        # Update mesh geometry after adding stuff.
        mesh.update()

        object_data_add(context, mesh, operator=None)
        # object generation done

        return {'FINISHED'}
