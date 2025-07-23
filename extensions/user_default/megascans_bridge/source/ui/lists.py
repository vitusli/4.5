import bpy
from bpy.types import UIList


class MBRIDGE_UL_layers(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        pass


classes = (MBRIDGE_UL_layers,)


register, unregister = bpy.utils.register_classes_factory(classes)
