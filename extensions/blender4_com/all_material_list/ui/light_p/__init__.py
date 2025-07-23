import bpy

# if "bpy" in locals():
#     import importlib
#     reloadable_modules = [
#         "ui_main_light_p_item",
#         "ui_main_light_p_uidetail",
#         "ui_main_light_p_root",
#         "ui_uilist_light_p",
#         ]
#     for module in reloadable_modules:
#         if module in locals():
#             importlib.reload(locals()[module])

from .ui_main_light_p_item import *
from .ui_main_light_p_uidetail import *
from .ui_main_light_p_root import *
from .ui_uilist_light_p import *

classes = (
AMLIST_UL_light_p,
)


def register():
	for cls in classes:
		bpy.utils.register_class(cls)


def unregister():
	for cls in reversed(classes):
		bpy.utils.unregister_class(cls)
