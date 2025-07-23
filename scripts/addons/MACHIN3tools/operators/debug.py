import bpy
from bpy.props import StringProperty

class MACHIN3toolsDebug(bpy.types.Operator):
    bl_idname = "machin3.machin3tools_debug"
    bl_label = "MACHIN3: MACHIN3tools Debug"
    bl_description = "MACHIN3tools Debug"
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return False

    def execute(self, context):
        return {'FINISHED'}

class Dummy(bpy.types.Operator):
    bl_idname = "machin3.dummy"
    bl_label = "Dummy"
    bl_options = {'INTERNAL'}

    desc: StringProperty(name="Description", default="None")
    @classmethod
    def description(cls, context, properties):
        if properties:
            return properties.desc
        else:
            return "Invalid Context"

    @classmethod
    def poll(cls, context):
        return False

    def execute(self, context):
        return {'CANCELLED'}
