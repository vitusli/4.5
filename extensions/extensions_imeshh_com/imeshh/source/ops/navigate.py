import bpy
from bpy.props import IntProperty, StringProperty
from bpy.types import Operator

from ..utils.local import _variant_map, _active_number


class IMESHH_OT_search_clear(Operator):

    bl_label = "Clear Search"
    bl_idname = "imeshh.search_clear"
    bl_options = {"REGISTER", "INTERNAL"}

    @classmethod
    def description(cls, context, properties):
        return "Clear the search input"

    def execute(self, context):
        props = context.scene.imeshh
        props.search = ""
        return {"FINISHED"}


class IMESHH_OT_navigate(Operator):

    bl_label = "Navigate"
    bl_idname = "imeshh.navigate"
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
        props = context.scene.imeshh
        props.page = self.page
        return {"FINISHED"}

class IMESHH_OT_navigate_asset(Operator):
    bl_label = "Navigate Asset"
    bl_idname = "imeshh.navigate_asset"
    bl_options = {"REGISTER", "INTERNAL"}

    direction: StringProperty(
        name="Direction",
        description="Direction to navigate (PREV or NEXT)",
    )

    base_name: StringProperty(
        name="Group's Name",
        description="The group path",
    )

    current_file: StringProperty(
        name="Current File",
        description="The current asset file path",
    )

    def execute(self, context):
        for i, asset in enumerate(_variant_map[self.base_name]):
            if self.current_file == asset.file_path:
                current_index = i
                break
        
        variants_count = len(_variant_map[self.base_name])
        # Calculate the index of the next variant
        if self.direction == "NEXT":
            next_index = (current_index + 1) % variants_count
        elif self.direction == "PREV":
            next_index = (current_index - 1 + variants_count) % variants_count
        else:
            print(f"Invalid direction: {self.direction}")
            return {'CANCELLED'}
        
        _active_number[self.base_name] = next_index

        if next_index != current_index:
            context.area.tag_redraw()
        else:
            print(f"Error: Asset index out of bounds.")
            return {'CANCELLED'}

        return {'FINISHED'}



classes = (
    IMESHH_OT_search_clear,
    IMESHH_OT_navigate,
    IMESHH_OT_navigate_asset
)


register, unregister = bpy.utils.register_classes_factory(classes)
