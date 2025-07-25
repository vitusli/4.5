# SPDX-FileCopyrightText: 2012-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

# Author: Kayo Phoenix

import bpy
from bpy_extras import object_utils
from math import (
        pi, sin,
        cos,
        )
from bpy.props import (
        IntProperty,
        BoolProperty,
        BoolVectorProperty,
        FloatProperty,
        FloatVectorProperty,
        StringProperty,
        )
from .interface import draw_transform_props


class honeycomb_geometry():
    def __init__(self, rows, cols, D, E):
        self.rows = rows
        self.cols = cols
        self.D = D
        self.E = E

        self.hE = 0.5 * self.E
        self.R = 0.5 * self.D

        self.a = sin(pi / 3)

        self.d = self.a * self.D
        self.hd = 0.5 * self.d
        self.e = self.hE / self.a
        self.he = 0.5 * self.e
        self.r = self.R - self.e
        self.hr = 0.5 * self.r

        self.H = self.R * (1.5 * self.rows + 0.5) + self.e
        if self.rows > 1:
            self.W = self.d * (self.cols + 0.5) + self.E
        else:
            self.W = self.d * self.cols + self.E

        self.hH = 0.5 * self.H
        self.hW = 0.5 * self.W

        self.sy = -self.hH + self.he + self.R
        self.sx = -self.hW + self.hE + self.hd

        self.gx = self.hd

        self.dy = 1.5 * self.R
        self.dx = self.d

    def vert(self, row, col):
        # full cell
        if row >= 0 and row < self.rows and col >= 0 and col < self.cols:
            return [0, 1, 2, 3, 4, 5]
        # right down corner
        if row == -1 and col == self.cols - 1:
            return [1, 2]
        if row == 0 and self.rows > 1 and col == self.cols:
            return [1, 2, 3]
        # left down corner
        if row == -1 and col == -1:
            return [0, 1]
        if self.rows % 2:
            # left up corner
            if row == self.rows and col == -1:
                return [4, 5]
            # right up corner
            if row == self.rows and col == self.cols - 1:
                return [3, 4]
            if row == self.rows - 1 and self.rows > 1 and col == self.cols:
                return [2, 3, 4]
        else:
            # left up corner
            if row == self.rows and col == 0:
                return [4, 5]
            if row == self.rows - 1 and self.rows > 1 and col == -1:
                return [0, 4, 5]
            # right up corner
            if row == self.rows and col == self.cols:
                return [3, 4]
        # horizontal lines
        if col >= 0 and col < self.cols:
            if row == -1:
                return [0, 1, 2]
            if row == self.rows:
                return [3, 4, 5]
        # vertical lines
        if row >= 0 and row < self.rows:
            if col == -1:
                if row % 2:
                    return [0, 1, 4, 5]
                else:
                    return [0, 5]
            if col == self.cols:
                if row % 2 or self.rows == 1:
                    return [2, 3]
                else:
                    return [1, 2, 3, 4]
        return []

    def cell(self, row, col, idx):
        cp = [self.sx + self.dx * col, self.sy + self.dy * row, 0]  # central point
        if row % 2:
            cp[0] += self.gx
        co = []  # vertices coords
        vi = self.vert(row, col)
        ap = {}

        for i in vi:
            a = pi / 6 + i * pi / 3  # angle
            ap[i] = idx + len(co)
            co.append((cp[0] + cos(a) * self.r, cp[1] + sin(a) * self.r, cp[2]))
        return co, ap

    def generate(self):
        ar = 1
        ac = 1

        cells = []
        verts = []
        faces = []

        for row in range(-ar, self.rows + ar):
            level = []
            for col in range(-ac, self.cols + ac):
                co, ap = self.cell(row, col, len(verts))
                verts += co
                level.append(ap)
            cells.append(level)

        # bottom row
        row = 0
        for col in range(1, len(cells[row]) - 1):
            s = cells[row][col]
            l = cells[row][col - 1]
            u = cells[row + 1][col]

            faces.append((s[1], u[5], u[4], s[2]))
            faces.append((s[2], u[4], l[0]))

        # top row
        row = len(cells) - 1
        cs = 0
        if row % 2:
            cs += 1
        for col in range(1 + cs, len(cells[row]) - 1):
            s = cells[row][col]
            l = cells[row][col - 1]
            d = cells[row - 1][col - cs]
            faces.append((s[3], l[5], d[1]))
            faces.append([s[3], d[1], d[0], s[4]])

        # middle rows
        for row in range(1, len(cells) - 1):
            cs = 0
            if row % 2:
                cs += 1
            for col in range(1, len(cells[row]) - 1):
                s = cells[row][col]
                l = cells[row][col - 1]
                u = cells[row + 1][col - cs]
                d = cells[row - 1][col - cs]

                faces.append((s[1], u[5], u[4], s[2]))
                faces.append((s[2], u[4], l[0]))
                faces.append([s[2], l[0], l[5], s[3]])
                faces.append((s[3], l[5], d[1]))
                faces.append([s[3], d[1], d[0], s[4]])

        # right column
        row = 0
        col = len(cells[row]) - 1
        for row in range(1, len(cells) - 1):
            cs = 0
            if row % 2:
                cs += 1

            s = cells[row][col]
            l = cells[row][col - 1]
            u = cells[row + 1][col - cs]
            d = cells[row - 1][col - cs]

            if row % 2 and row < len(cells) - 2:
                faces.append((s[1], u[5], u[4], s[2]))
            faces.append((s[2], u[4], l[0]))
            faces.append([s[2], l[0], l[5], s[3]])
            faces.append((s[3], l[5], d[1]))
            if row % 2 and row > 1:
                faces.append([s[3], d[1], d[0], s[4]])

        # final fix
        if not self.rows % 2:
            row = len(cells) - 1
            s = cells[row][col]
            l = cells[row][col - 1]
            d = cells[row - 1][col - 1]
            faces.append((s[3], l[5], d[1]))
            faces.append([s[3], d[1], d[0], s[4]])

        return verts, faces


def edge_max(diam):
    return diam * sin(pi / 3)


class add_mesh_honeycomb(bpy.types.Operator, object_utils.AddObjectHelper):
    bl_idname = "mesh.honeycomb_add"
    bl_label = "Add Honeycomb"
    bl_description = "Simple honeycomb mesh generator"
    bl_options = {'REGISTER', 'UNDO'}

    def fix_edge(self, context):
        m = edge_max(self.diam)
        if self.edge > m:
            self.edge = m

    HoneyComb : BoolProperty(name = "HoneyComb",
                default = True,
                description = "HoneyComb")
    change : BoolProperty(name = "Change",
                default = False,
                description = "change HoneyComb")

    rows: IntProperty(
            name="Rows",
            default=2,
            min=1, max=100,
            description='Number of the rows'
            )
    cols: IntProperty(
            name='Columns',
            default=2,
            min=1, max=100,
            description='Number of the columns'
            )
    diam: FloatProperty(
            name='Cell Diameter',
            default=1.0,
            min=0.0, update=fix_edge,
            description='Diameter of the cell'
            )
    edge: FloatProperty(
            name='Edge Width',
            default=0.1,
            min=0.0, update=fix_edge,
            description='Width of the edge'
            )

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.prop(self, 'rows', expand=True)
        layout.prop(self, 'cols', expand=True)
        layout.prop(self, 'diam', expand=True)
        layout.prop(self, 'edge', expand=True)

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
                (context.active_object.data is not None) and ('HoneyComb' in context.active_object.data.keys()) and \
                (self.change == True):
                obj = context.active_object
                oldmesh = obj.data
                oldmeshname = obj.data.name
                comb = honeycomb_geometry(self.rows, self.cols, self.diam, self.edge)
                verts, faces = comb.generate()
                mesh = bpy.data.meshes.new('HoneyComb')
                mesh.from_pydata(verts, [], faces)
                obj.data = mesh
                for material in oldmesh.materials:
                    obj.data.materials.append(material)
                bpy.data.meshes.remove(oldmesh)
                obj.data.name = oldmeshname
            else:
                comb = honeycomb_geometry(self.rows, self.cols, self.diam, self.edge)
                verts, faces = comb.generate()
                mesh = bpy.data.meshes.new('HoneyComb')
                mesh.from_pydata(verts, [], faces)
                obj = object_utils.object_data_add(context, mesh, operator=self)

            obj.data["HoneyComb"] = True
            obj.data["change"] = False
            for prm in HoneyCombParameters():
                obj.data[prm] = getattr(self, prm)

        if bpy.context.mode == "EDIT_MESH":
            active_object = context.active_object
            name_active_object = active_object.name
            bpy.ops.object.mode_set(mode='OBJECT')
            comb = honeycomb_geometry(self.rows, self.cols, self.diam, self.edge)
            verts, faces = comb.generate()
            mesh = bpy.data.meshes.new('HoneyComb')
            mesh.from_pydata(verts, [], faces)
            obj = object_utils.object_data_add(context, mesh, operator=self)
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

def HoneyCombParameters():
    HoneyCombParameters = [
        "rows",
        "cols",
        "diam",
        "edge",
        ]
    return HoneyCombParameters
