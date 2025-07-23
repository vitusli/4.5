import bpy
from bpy.props import IntProperty
from bpy.types import Operator


class MBRIDGE_OT_search_clear(Operator):
    bl_label = "Clear Search"
    bl_idname = "mbridge.search_clear"
    bl_options = {"REGISTER", "INTERNAL"}

    @classmethod
    def description(cls, context, properties):
        return "Clear the search input"

    def execute(self, context):
        props = context.scene.mbridge
        props.search = ""
        return {"FINISHED"}


class MBRIDGE_OT_navigate(Operator):
    bl_label = "Navigate"
    bl_idname = "mbridge.navigate"
    bl_options = {"REGISTER", "INTERNAL"}
    bl_property = "page"

    page: IntProperty(
        name="Page",
        description="Page number",
        min=1,
        default=1,
    )

    @classmethod
    def description(cls, context, properties):
        return f"Navigate to page {properties.page}\n\nShift + Click - Navigate to a specific page"

    def invoke(self, context, event):
        if event.shift:
            return context.window_manager.invoke_props_dialog(self)
        return self.execute(context)

    def execute(self, context):
        props = context.scene.mbridge
        props.page = self.page
        context.area.tag_redraw()
        return {"FINISHED"}


classes = (
    MBRIDGE_OT_search_clear,
    MBRIDGE_OT_navigate,
)


register, unregister = bpy.utils.register_classes_factory(classes)
