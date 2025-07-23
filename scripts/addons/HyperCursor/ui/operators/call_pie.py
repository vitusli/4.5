import bpy
from bpy.props import StringProperty, IntProperty

from ... utils.cursor import set_cursor_to_geo
from ... utils.ui import Mouse

class CallHyperCursorPie(bpy.types.Operator, Mouse):
    bl_idname = "machin3.call_hyper_cursor_pie"
    bl_label = "MACHIN3: Call Hyper Cursor Pie"
    bl_options = {'INTERNAL'}

    idname: StringProperty()
    index: IntProperty()

    @classmethod
    def description(cls, context, properties):
        if properties:
            if properties.idname in ['MACHIN3_MT_edit_edge', 'MACHIN3_MT_edit_face']:
                geom = 'Edge' if properties.idname == 'MACHIN3_MT_edit_edge' else 'Face'

                desc = f"Call Edit {geom} Pie Menu"
                desc += f"\nALT: Set Cursor to {geom} {properties.index}"
                desc += f"\nCTRL: Hyper Select {geom} {properties.index}"
                desc += f"\nSHIFT: Hyper Loop Select {geom} {properties.index}"
                desc += f"\nSHIFT + CTRL: Hyper Ring Select {geom} {properties.index}"
                return desc

            elif properties.idname == 'MACHIN3_MT_add_object_at_cursor':
                return "Call Add Object Pie Menu"
        return "Invalid Context"

    def invoke(self, context, event):

        if self.idname == 'MACHIN3_MT_add_object_at_cursor':
            bpy.ops.wm.call_menu_pie(name=self.idname)

        elif self.idname == 'MACHIN3_MT_edit_edge':
            self.capture_mouse(event)

            if event.alt:
                set_cursor_to_geo(context, context.active_object, edgeidx=self.index)

            elif event.shift and event.ctrl:
                bpy.ops.machin3.select_edge(index=self.index, loop=False, ring=True)

            elif event.shift:
                bpy.ops.machin3.select_edge(index=self.index, loop=True, ring=False)

            elif event.ctrl:
                bpy.ops.machin3.select_edge(index=self.index, loop=False, ring=False)

            else:

                bpy.types.MACHIN3_MT_edit_edge.index = self.index

                bpy.ops.wm.call_menu_pie(name=self.idname)

        elif self.idname == 'MACHIN3_MT_edit_face':
            self.capture_mouse(event)

            if event.alt:
                set_cursor_to_geo(context, context.active_object, faceidx=self.index)

            elif event.shift:
                bpy.ops.machin3.select_face(index=self.index, loop=True)

            elif event.ctrl:
                bpy.ops.machin3.select_face(index=self.index, loop=False)

            else:

                bpy.types.MACHIN3_MT_edit_face.index = self.index

                bpy.ops.wm.call_menu_pie(name=self.idname)

        else:
            bpy.ops.wm.call_menu_pie(name=self.idname)

        return {'FINISHED'}
