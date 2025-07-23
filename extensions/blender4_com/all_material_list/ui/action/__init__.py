import bpy
# if "bpy" in locals():
# 	import importlib
# 	reloadable_modules = [
# 		"ui_main_action_item",
# 		"ui_main_action_uidetail",
# 		"ui_main_action_root",
# 		]
# 	for module in reloadable_modules:
# 		if module in locals():
# 			importlib.reload(locals()[module])

from .ui_main_action_item import *
from .ui_main_action_uidetail import *
from .ui_main_action_root import *


classes = (
AMLIST_UL_action,
)


def register():
	for cls in classes:
		try:
			bpy.utils.register_class(cls)
		except ValueError: pass


def unregister():
	for cls in reversed(classes):
		bpy.utils.unregister_class(cls)
