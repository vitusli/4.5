import bpy
from bpy.types import UILayout, UIList


class IMESHH_UL_custom_path(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)
        row.prop(item, "name", text="", icon_value=UILayout.enum_item_icon(item, "type", item.type), emboss=False)
        row.prop(item, "type", text="", expand=True)


classes = (IMESHH_UL_custom_path,)


register, unregister = bpy.utils.register_classes_factory(classes)
