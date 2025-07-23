import bpy

# if "bpy" in locals():
#     import importlib
#     reloadable_modules = [
#         "ui_main_cam_item",
#         "ui_main_cam_uidetail",
#         "ui_main_cam_root",
#         "ui_uilist_cam",
#         ]
#     for module in reloadable_modules:
#         if module in locals():
#             importlib.reload(locals()[module])

from .ui_main_cam_item import *
from .ui_main_cam_uidetail import *
from .ui_main_cam_root import *
from .ui_uilist_cam import *


classes = (
AMLIST_UL_cam,
)


def register():
	for cls in classes:
		bpy.utils.register_class(cls)


def unregister():
	for cls in reversed(classes):
		bpy.utils.unregister_class(cls)
