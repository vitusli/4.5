import bpy
from bpy.props import FloatProperty, StringProperty, FloatVectorProperty, BoolProperty, IntProperty
from mathutils import Vector

from ... utils.object import get_batch_from_obj
from ... utils.draw import draw_label, draw_batch
from ... utils.ui import finish_modal_handlers, init_modal_handlers, set_countdown, get_timer_progress, get_scale
from ... utils.workspace import is_3dview

from ... colors import blue

class DrawLabel(bpy.types.Operator):
    bl_idname = "machin3.draw_hyper_cursor_label"
    bl_label = "MACHIN3: Draw Label"
    bl_description = ""
    bl_options = {'INTERNAL'}

    text: StringProperty(name="Text to draw the HUD", default='Text')
    size: FloatProperty(name="Text Size", default=12)
    coords: FloatVectorProperty(name='Screen Coordinates', size=2, default=(100, 100))
    center: BoolProperty(name='Center', default=True)
    color: FloatVectorProperty(name='Text Color', size=3, default=(1, 1, 1))
    alpha: FloatProperty(name="Alpha", default=0.5, min=0.1, max=1)
    move_y: IntProperty(name="Move Up or Down", default=0)
    time: FloatProperty(name="", default=1, min=0.1)
    cancel: StringProperty()

    @classmethod
    def poll(cls, context):
        return is_3dview(context)

    def draw_HUD(self, context):
        try:
            if context.area == self.area:
                prog = get_timer_progress(self)
                alpha = prog * self.alpha

                coords = Vector(self.coords)

                if self.move_y:
                    coords += Vector((0, self.move_y * (1 - prog) * get_scale(context)))

                draw_label(context, title=self.text, coords=coords, center=self.center, size=self.size, color=self.color, alpha=alpha)

        except ReferenceError:
            pass

    def modal(self, context, event):
        if not context.area:
            self.finish(context)
            return {'CANCELLED'}

        context.area.tag_redraw()

        if self.cancel:
            pass

        if self.TIMER_countdown < 0:
            self.finish(context)
            return {'FINISHED'}

        if event.type == 'TIMER':
            set_countdown(self)

        return {'PASS_THROUGH'}

    def finish(self, context):
        finish_modal_handlers(self)

    def execute(self, context):
        init_modal_handlers(self, context, hud=True, timer=True, time_step=0.01 if self.move_y else 0.1)
        return {'RUNNING_MODAL'}

class DrawActiveObject(bpy.types.Operator):
    bl_idname = "machin3.draw_active_object"
    bl_label = "MACHIN3: Draw Active Object"

    time: FloatProperty(name="Time (s)", default=2)
    alpha: FloatProperty(name="Alpha", default=0.7, min=0.1, max=1)
    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            return context.active_object

    def draw_VIEW3D(self, context):
        try:
            if context.area == self.area:
                alpha = get_timer_progress(self) * self.alpha

                draw_batch(self.batch, color=blue, width=2, alpha=alpha)
        except:
            pass

    def modal(self, context, event):
        if not context.area:
            self.finish(context)
            return {'CANCELLED'}

        context.area.tag_redraw()

        if self.TIMER_countdown < 0:
            self.finish(context)

            return {'FINISHED'}

        if event.type == 'TIMER':
            set_countdown(self)

        return {'PASS_THROUGH'}

    def finish(self, context):
        finish_modal_handlers(self)

    def execute(self, context):
        dg = context.evaluated_depsgraph_get()
        active = context.active_object

        self.batch = get_batch_from_obj(dg, active)

        init_modal_handlers(self, context, view3d=True, timer=True)
        return {'RUNNING_MODAL'}
