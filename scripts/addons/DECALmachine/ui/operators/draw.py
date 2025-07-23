import bpy
from bpy.props import FloatProperty, StringProperty, FloatVectorProperty, BoolProperty
from ... utils.draw import draw_label
from ... utils.material import get_legacy_materials
from ... utils.ui import init_timer_modal, set_countdown, get_timer_progress

class DrawDecalLabel(bpy.types.Operator):
    bl_idname = "machin3.draw_decal_label"
    bl_label = "MACHIN3: Draw Decal Label"
    bl_description = ""
    bl_options = {'INTERNAL'}

    text: StringProperty(name="Text to draw the HUD", default='Text')
    coords: FloatVectorProperty(name='Screen Coordinates', size=2, default=(100, 100))
    center: BoolProperty(name='Center', default=True)
    color: FloatVectorProperty(name='Screen Coordinates', size=3, default=(1, 1, 1))
    time: FloatProperty(name="", default=1, min=0.1)
    alpha: FloatProperty(name="Alpha", default=0.5, min=0.1, max=1)
    cancel: StringProperty()

    @classmethod
    def poll(cls, context):
        return context.space_data.type == 'VIEW_3D'

    def draw_HUD(self, context):
        try:
            if context.area == self.area:
                alpha = get_timer_progress(self) * self.alpha
                draw_label(context, title=self.text, coords=self.coords, center=self.center, color=self.color, alpha=alpha)

        except ReferenceError:
            pass

    def modal(self, context, event):
        if context.area:
            context.area.tag_redraw()

        else:
            self.finish(context)
            return {'FINISHED'}

        if self.cancel:
            if self.cancel == 'LEGACY_MATERIALS':
                legacy_materials = get_legacy_materials(force=False)

                if not legacy_materials['DECAL'] and not legacy_materials['TRIM']:
                    self.finish(context)
                    return {'FINISHED'}

        if self.countdown < 0:
            self.finish(context)
            return {'FINISHED'}

        if event.type == 'TIMER':
            set_countdown(self)

        return {'PASS_THROUGH'}

    def finish(self, context):
        context.window_manager.event_timer_remove(self.TIMER)
        bpy.types.SpaceView3D.draw_handler_remove(self.HUD, 'WINDOW')

    def execute(self, context):
        init_timer_modal(self)

        self.area = context.area
        self.HUD = bpy.types.SpaceView3D.draw_handler_add(self.draw_HUD, (context, ), 'WINDOW', 'POST_PIXEL')
        self.TIMER = context.window_manager.event_timer_add(0.1, window=context.window)

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
