# SPDX-FileCopyrightText: 2010-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

# Original by Buerbaum Martin (Pontiac), Elod Csirmaz

import bpy
import math
import numpy
from mathutils import *
from math import *
from bpy.types import Operator
from bpy.props import (
        StringProperty,
        IntProperty,
        FloatProperty,
        BoolProperty,
        )


# List of safe functions for eval()
safe_list = ['acos', 'asin', 'atan', 'atan2', 'ceil', 'cos', 'cosh',
    'degrees', 'e', 'exp', 'fabs', 'floor', 'fmod', 'frexp', 'hypot',
    'ldexp', 'log', 'log10', 'modf', 'pi', 'pow', 'radians',
    'sin', 'sinh', 'sqrt', 'tan', 'tanh', 'gcd']

# Use the list to filter the local namespace
safe_dict = dict((k, globals().get(k, None)) for k in safe_list)
safe_dict['math'] = math
safe_dict['numpy'] = safe_dict['np'] = numpy
safe_dict['lcm'] = numpy.lcm
safe_dict['max'] = max
safe_dict['min'] = min


# Stores the values of a list of properties and the
# operator id in a property group ('recall_op') inside the object
# Could (in theory) be used for non-objects.
# Note: Replaces any existing property group with the same name!
# ob ... Object to store the properties in
# op ... The operator that should be used
# op_args ... A dictionary with valid Blender
#             properties (operator arguments/parameters)


# Create a new mesh (object) from verts/edges/faces
# verts/edges/faces ... List of vertices/edges/faces for the
#                       new mesh (as used in from_pydata)
# name ... Name of the new mesh (& object)

def create_mesh_object(context, verts, edges, faces, name):

    # Create new mesh
    mesh = bpy.data.meshes.new(name)

    # Make a mesh from a list of verts/edges/faces
    mesh.from_pydata(verts, edges, faces)

    # Update mesh geometry after adding stuff
    mesh.update()

    from bpy_extras import object_utils
    return object_utils.object_data_add(context, mesh, operator=None)


# A very simple "bridge" tool

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
        # Bridge the start with the end
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

    # Bridge the rest of the faces
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


class AddZFunctionSurface(Operator):
    bl_idname = "mesh.primitive_z_function_surface"
    bl_label = "Add Z Function Surface"
    bl_description = "Add a surface defined defined by a function z=f(x,y)"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    equation: StringProperty(
                name="Z Equation",
                description="Equation for z=f(x,y)",
                default="1 - ( x**2 + y**2 )"
                )
    div_x: IntProperty(
                name="X Subdivisions",
                description="Number of vertices in x direction",
                default=16,
                min=3,
                max=256
                )
    div_y: IntProperty(
                name="Y Subdivisions",
                description="Number of vertices in y direction",
                default=16,
                min=3,
                max=256
                )
    size_x: FloatProperty(
                name="X Size",
                description="Size of the x axis",
                default=2.0,
                min=0.01,
                max=100.0,
                unit="LENGTH"
                )
    size_y: FloatProperty(
                name="Y Size",
                description="Size of the y axis",
                default=2.0,
                min=0.01,
                max=100.0,
                unit="LENGTH"
                )

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.separator()
        layout.prop(self, 'equation')
        col = layout.column(align=True)
        col.prop(self, 'div_x', text='Subdivisions X')
        col.prop(self, 'div_y', text='Y')
        col = layout.column(align=True)
        col.prop(self, 'size_x', text='Size X')
        col.prop(self, 'size_y', text='Y')

    def execute(self, context):
        equation = self.equation
        div_x = self.div_x
        div_y = self.div_y
        size_x = self.size_x
        size_y = self.size_y

        verts = []
        faces = []

        delta_x = size_x / (div_x - 1)
        delta_y = size_y / (div_y - 1)
        start_x = -(size_x / 2.0)
        start_y = -(size_y / 2.0)

        edgeloop_prev = []

        if equation:
            try:
                expr_args = (
                    compile(equation, __file__, 'eval'),
                    {"__builtins__": None},
                    safe_dict)
            except:
                import traceback
                # WARNING is used to prevent the constant pop-up spam
                self.report({'WARNING'},
                            "Error parsing expression: {} "
                            "(Check the console for more info)".format(equation))
                print("\n[Add Z Function Surface]:\n\n", traceback.format_exc(limit=1))

                return {'CANCELLED'}

            for row_x in range(div_x):
                edgeloop_cur = []
                x = start_x + row_x * delta_x

                for row_y in range(div_y):
                    y = start_y + row_y * delta_y
                    z = 0.0

                    safe_dict['x'] = x
                    safe_dict['y'] = y

                    # Try to evaluate the equation.
                    try:
                        z = float(eval(*expr_args))
                    except:
                        import traceback
                        self.report({'WARNING'},
                                    "Error evaluating expression: {} "
                                    "(Check the console for more info)".format(equation))
                        print("\n[Add Z Function Surface]:\n\n", traceback.format_exc(limit=1))

                        return {'CANCELLED'}

                    edgeloop_cur.append(len(verts))
                    verts.append((x, y, z))

                if len(edgeloop_prev) > 0:
                    faces_row = createFaces(edgeloop_prev, edgeloop_cur)
                    faces.extend(faces_row)

                edgeloop_prev = edgeloop_cur

            base = create_mesh_object(context, verts, [], faces, "Z Function")
        else:
            self.report({'WARNING'}, "Z Equation - No expression is given")

            return {'CANCELLED'}

        return {'FINISHED'}


def xyz_function_surface_faces(self, x_eq, y_eq, z_eq,
            range_u_min, range_u_max, range_u_step, wrap_u,
            range_v_min, range_v_max, range_v_step, wrap_v,
            a_eq, b_eq, c_eq, f_eq, g_eq, h_eq, n, close_v):

    verts = []
    faces = []

    # Distance of each step in Blender Units
    uStep = (range_u_max - range_u_min) / range_u_step
    vStep = (range_v_max - range_v_min) / range_v_step

    # Number of steps in the vertex creation loops.
    # Number of steps is the number of faces
    #   => Number of points is +1 unless wrapped.
    uRange = range_u_step + 1
    vRange = range_v_step + 1

    if wrap_u:
        uRange = uRange - 1

    if wrap_v:
        vRange = vRange - 1

    try:
        expr_args_x = (
            compile(x_eq, __file__.replace(".py", "_x.py"), 'eval'),
            {"__builtins__": None},
            safe_dict)
        expr_args_y = (
            compile(y_eq, __file__.replace(".py", "_y.py"), 'eval'),
            {"__builtins__": None},
            safe_dict)
        expr_args_z = (
            compile(z_eq, __file__.replace(".py", "_z.py"), 'eval'),
            {"__builtins__": None},
            safe_dict)
        expr_args_a = (
            compile(a_eq, __file__.replace(".py", "_a.py"), 'eval'),
            {"__builtins__": None},
            safe_dict)
        expr_args_b = (
            compile(b_eq, __file__.replace(".py", "_b.py"), 'eval'),
            {"__builtins__": None},
            safe_dict)
        expr_args_c = (
            compile(c_eq, __file__.replace(".py", "_c.py"), 'eval'),
            {"__builtins__": None},
            safe_dict)
        expr_args_f = (
            compile(f_eq, __file__.replace(".py", "_f.py"), 'eval'),
            {"__builtins__": None},
            safe_dict)
        expr_args_g = (
            compile(g_eq, __file__.replace(".py", "_g.py"), 'eval'),
            {"__builtins__": None},
            safe_dict)
        expr_args_h = (
            compile(h_eq, __file__.replace(".py", "_h.py"), 'eval'),
            {"__builtins__": None},
            safe_dict)
    except:
        import traceback
        self.report({'WARNING'}, "Error parsing expression(s) - "
                    "Check the console for more info")
        print("\n[Add X, Y, Z Function Surface]:\n\n", traceback.format_exc(limit=1))
        return [], []

    for vN in range(vRange):
        v = range_v_min + (vN * vStep)

        for uN in range(uRange):
            u = range_u_min + (uN * uStep)

            safe_dict['u'] = u
            safe_dict['v'] = v

            safe_dict['n'] = n

            # Try to evaluate the equations.
            try:
                safe_dict['a'] = float(eval(*expr_args_a))
                safe_dict['b'] = float(eval(*expr_args_b))
                safe_dict['c'] = float(eval(*expr_args_c))
                safe_dict['f'] = float(eval(*expr_args_f))
                safe_dict['g'] = float(eval(*expr_args_g))
                safe_dict['h'] = float(eval(*expr_args_h))

                verts.append((
                    float(eval(*expr_args_x)),
                    float(eval(*expr_args_y)),
                    float(eval(*expr_args_z))))
            except:
                import traceback
                self.report({'WARNING'}, "Error evaluating expression(s) - "
                             "Check the console for more info")
                print("\n[Add X, Y, Z Function Surface]:\n\n", traceback.format_exc(limit=1))
                return [], []

    for vN in range(range_v_step):
        vNext = vN + 1

        if wrap_v and (vNext >= vRange):
            vNext = 0

        for uN in range(range_u_step):
            uNext = uN + 1

            if wrap_u and (uNext >= uRange):
                uNext = 0

            faces.append([(vNext * uRange) + uNext,
                (vNext * uRange) + uN,
                (vN * uRange) + uN,
                (vN * uRange) + uNext])

    if close_v and wrap_u and (not wrap_v):
        for uN in range(1, range_u_step - 1):
            faces.append([
                range_u_step - 1,
                range_u_step - 1 - uN,
                range_u_step - 2 - uN])
            faces.append([
                range_v_step * uRange,
                range_v_step * uRange + uN,
                range_v_step * uRange + uN + 1])

    return verts, faces


# Original Script "Parametric.py" by Ed Mackey.
# -> http://www.blinken.com/blender-plugins.php
# Partly converted for Blender 2.5 by tuga3d.
#
# Sphere:
# x = sin(2*pi*u)*sin(pi*v)
# y = cos(2*pi*u)*sin(pi*v)
# z = cos(pi*v)
# u_min = v_min = 0
# u_max = v_max = 1
#
# "Snail shell"
# x = 1.2**v*(sin(u)**2 *sin(v))
# y = 1.2**v*(sin(u)*cos(u))
# z = 1.2**v*(sin(u)**2 *cos(v))
# u_min = 0
# u_max = pi
# v_min = -pi/4,
# v max = 5*pi/2

class AddXYZFunctionSurface(Operator):
    bl_idname = "mesh.primitive_xyz_function_surface"
    bl_label = "Add XYZ Function Surface"
    bl_description = ("Add a surface defined defined by 3 functions:\n"
                      "x=F1(u,v), y=F2(u,v) and z=F3(u,v)")
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    x_eq: StringProperty(
                name="X Equation",
                description="Equation for x=F(u,v). "
                            "Also available: n, a, b, c, f, g, h",
                default="cos(v)*(1+cos(u))*sin(v/8)"
                )
    y_eq: StringProperty(
                name="Y Equation",
                description="Equation for y=F(u,v). "
                            "Also available: n, a, b, c, f, g, h",
                default="sin(u)*sin(v/8)+cos(v/8)*1.5"
                )
    z_eq: StringProperty(
                name="Z Equation",
                description="Equation for z=F(u,v). "
                            "Also available: n, a, b, c, f, g, h",
                default="sin(v)*(1+cos(u))*sin(v/8)"
                )
    range_u_min: FloatProperty(
                name="U Min",
                description="Minimum U value. Lower boundary of U range",
                min=-100.00,
                max=0.00,
                default=0.00
                )
    range_u_max: FloatProperty(
                name="U Max",
                description="Maximum U value. Upper boundary of U range",
                min=0.00,
                max=100.00,
                default=2 * pi
                )
    range_u_step: IntProperty(
                name="U Step",
                description="U Subdivisions",
                min=1,
                max=1024,
                default=32
                )
    wrap_u: BoolProperty(
                name="U Wrap",
                description="U Wrap around",
                default=True
                )
    range_v_min: FloatProperty(
                name="V Min",
                description="Minimum V value. Lower boundary of V range",
                min=-100.00,
                max=0.00,
                default=0.00
                )
    range_v_max: FloatProperty(
                name="V Max",
                description="Maximum V value. Upper boundary of V range",
                min=0.00,
                max=100.00,
                default=4 * pi
                )
    range_v_step: IntProperty(
                name="V Step",
                description="V Subdivisions",
                min=1,
                max=1024,
                default=128
                )
    wrap_v: BoolProperty(
                name="V Wrap",
                description="V Wrap around",
                default=False
                )
    close_v: BoolProperty(
                name="Close V",
                description="Create faces for first and last "
                            "V values (only if U is wrapped)",
                default=False
                )
    n_eq: IntProperty(
                name="Number of Objects (n=0..N-1)",
                description="The parameter n will be the index "
                            "of the current object, 0 to N-1",
                min=1,
                max=100,
                default=1
                )
    a_eq: StringProperty(
                name="A Helper Function",
                description="Equation for a=F(u,v). Also available: n",
                default="0"
                )
    b_eq: StringProperty(
                name="B Helper Function",
                description="Equation for b=F(u,v). Also available: n",
                default="0"
                )
    c_eq: StringProperty(
                name="C Helper Function",
                description="Equation for c=F(u,v). Also available: n",
                default="0"
                )
    f_eq: StringProperty(
                name="F Helper Function",
                description="Equation for f=F(u,v). Also available: n, a, b, c",
                default="0"
                )
    g_eq: StringProperty(
                name="G Helper Function",
                description="Equation for g=F(u,v). Also available: n, a, b, c",
                default="0"
                )
    h_eq: StringProperty(
                name="H Helper Function",
                description="Equation for h=F(u,v). Also available: n, a, b, c",
                default="0"
                )
    show_wire : BoolProperty(
            name="Show Wireframe",
            default=True,
            description="Add the object’s wireframe over solid drawing"
            )
    edit_mode : BoolProperty(
            name="Show in Edit Mode",
            default=True,
            description="Show in Edit Mode"
            )

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.separator()
        col = layout.column()
        col.prop(self, 'x_eq', text='Equation X')
        col.prop(self, 'y_eq', text='Y')
        col.prop(self, 'z_eq', text='Z')
        layout.separator()
        col = layout.column(align=True)
        col.prop(self, 'range_u_min', text='U Min')
        col.prop(self, 'range_u_max', text='Max')
        col.prop(self, 'range_u_step', text='Step')
        col.prop(self, 'wrap_u', text='Wrap')
        layout.separator()
        col = layout.column(align=True)
        col.prop(self, 'range_v_min', text='V Min')
        col.prop(self, 'range_v_max', text='Max')
        col.prop(self, 'range_v_step', text='Step')
        col.prop(self, 'wrap_v', text='Wrap')
        col.prop(self, 'close_v', text='Close')
        layout.separator()
        col = layout.column()
        col.prop(self, 'n_eq', text='Objects')
        col.prop(self, 'a_eq', text='Helper Function A')
        col.prop(self, 'b_eq', text='B')
        col.prop(self, 'c_eq', text='C')
        col.prop(self, 'f_eq', text='F')
        col.prop(self, 'g_eq', text='G')
        col.prop(self, 'h_eq', text='H')
        layout.separator()
        row = layout.row(heading='Show')
        row.prop(self, 'show_wire', text='Wireframe')
        layout.prop(self, 'edit_mode', text='In Edit Mode')

    def execute(self, context):
        for n in range(0, self.n_eq):
            verts, faces = xyz_function_surface_faces(
                                self,
                                self.x_eq,
                                self.y_eq,
                                self.z_eq,
                                self.range_u_min,
                                self.range_u_max,
                                self.range_u_step,
                                self.wrap_u,
                                self.range_v_min,
                                self.range_v_max,
                                self.range_v_step,
                                self.wrap_v,
                                self.a_eq,
                                self.b_eq,
                                self.c_eq,
                                self.f_eq,
                                self.g_eq,
                                self.h_eq,
                                n,
                                self.close_v
                                )
            if not verts:
                return {'CANCELLED'}

            obj = create_mesh_object(context, verts, [], faces, "XYZ Function")

        if self.show_wire:
            context.active_object.show_wire = True
        else:
            context.active_object.show_wire = False

        if self.edit_mode:
            bpy.ops.object.mode_set(mode = 'EDIT')
        else:
            bpy.ops.object.mode_set(mode = 'OBJECT')

        return {'FINISHED'}
