import bpy
from bpy.types import Menu


class MBRIDGE_MT_preset_menu(Menu):
    """Presets"""

    bl_label = "Presets"
    preset_subdir = "Preset Location"
    preset_operator = "script.execute_preset"
    preset_operator_defaults = {"menu_idname": "MBRIDGE_MT_preset_menu"}
    draw = Menu.draw_preset


classes = (MBRIDGE_MT_preset_menu,)


register, unregister = bpy.utils.register_classes_factory(classes)
