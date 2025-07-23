import bpy

# if "bpy" in locals():
# 	import importlib
# 	reloadable_modules = [
# 		"ui_list",
# 		"ui_main_common",
# 		"ui_main_img",
# 		"ui_main_slot",
# 		"ui_main_vcol",
# 		"ui_main_wld",
# 		"ui_main",
# 		"ui_menu_other",
# 		"ui_panel",
# 		"ui_popup",
# 		"ui_preferences",
# 		"ui_hide",
# 		"ui_uilist_img",
#
# 		"action",
# 		"cam",
# 		"light_l",
# 		"light_p",
# 		"mat",
# 		"sc_l",
# 		]
# 	for module in reloadable_modules:
# 		if module in locals():
# 			importlib.reload(locals()[module])

from .regi_panel import *
from .ui_list import *
from .ui_main import *
from .ui_main_common import *
from .ui_main_img import *
from .ui_main_slot import *
from .ui_main_vcol import *
from .ui_main_wld import *
from .ui_menu_other import *
from .ui_panel import *
from .ui_popup import *
from .ui_preferences import *
from .ui_hide import *
from .ui_uilist_img import *
from .. import __package__ as addon_id

from . import(
	action,
	cam,
	light_l,
	light_p,
	mat,
)



classes = (
# AMLIST_PT_view3d,
AMLIST_MT_filter_menu_action,
AMLIST_MT_filter_menu_cam,
AMLIST_MT_filter_menu_light_l,
AMLIST_MT_filter_menu_light_p,
AMLIST_MT_filter_menu_mat,
AMLIST_MT_filter_menu_img,
AMLIST_MT_filter_menu_sc_l,
AMLIST_MT_other_action,
AMLIST_MT_other_cam,
AMLIST_MT_other_img,
AMLIST_MT_other_light_l,
AMLIST_MT_other_light_p,
AMLIST_MT_other_mat,
AMLIST_MT_other_sc_l,
AMLIST_OT_Popup,
AMLIST_PT_action_dopesheet,
AMLIST_PT_action_graph,
AMLIST_PT_image,
AMLIST_UL_image,
AMLIST_UL_sc_l,
AMLIST_UL_viewlayers,
AMLIST_UL_world,
)


list_panels = (
		AMLIST_PT_mat_index,
		AMLIST_PT_vcol,
		AMLIST_PT_light_l,
		AMLIST_PT_sc_l,
		AMLIST_PT_action,
		# AMLIST_PT_light_m,
		AMLIST_PT_light_p,
		AMLIST_PT_cam,
		AMLIST_PT_wld,
		AMLIST_PT_img,
		)

##########################################################
def register():
	for cls in classes:
		bpy.utils.register_class(cls)

	for cls in list_panels:
		bpy.utils.register_class(cls)

	mat.register()
	light_l.register()
	light_p.register()
	cam.register()
	action.register()

	prefs =bpy.context.preferences.addons[addon_id].preferences
	# update_regipanel_action_dopesheet
	# update_regipanel_action_graph

	regi_panel(prefs.usepanel_action,AMLIST_PT_action)
	regi_panel(prefs.usepanel_mat_index,AMLIST_PT_mat_index)
	regi_panel(prefs.usepanel_vcol,AMLIST_PT_vcol)
	regi_panel(prefs.usepanel_sc_l,AMLIST_PT_sc_l)
	regi_panel(prefs.usepanel_light_l,AMLIST_PT_light_l)
	regi_panel(prefs.usepanel_light_p,AMLIST_PT_light_p)
	regi_panel(prefs.usepanel_cam,AMLIST_PT_cam)
	regi_panel(prefs.usepanel_img,AMLIST_PT_img)
	regi_panel(prefs.usepanel_wld,AMLIST_PT_wld)

	update_panel(None, bpy.context)  # パネル表示が有効の場合、AMLIST_PT_view3dのみになる


	bpy.types.MATERIAL_MT_context_menu.append(AMLIST_MT_clean_menu) # Menu

def unregister():
	if "bl_rna" in AMLIST_PT_view3d.__dict__:
		bpy.types.AMLIST_PT_view3d.remove(draw_panel_img_menu)
	bpy.types.MATERIAL_MT_context_menu.remove(AMLIST_MT_clean_menu)

	mat.unregister()
	light_l.unregister()
	light_p.unregister()
	cam.unregister()
	action.unregister()


	try:
		bpy.utils.unregister_class(AMLIST_PT_action)
	except: pass
	try:
		bpy.utils.unregister_class(AMLIST_PT_sc_l)
	except: pass

	try:
		bpy.utils.unregister_class(AMLIST_PT_wld)
	except: pass

	try:
		bpy.utils.unregister_class(AMLIST_PT_vcol)
	except: pass

	try:
		bpy.utils.unregister_class(AMLIST_PT_mat_index)
	except: pass

	try:
		bpy.utils.unregister_class(AMLIST_PT_light_p)
	except: pass

	try:
		bpy.utils.unregister_class(AMLIST_PT_light_m)
	except: pass

	try:
		bpy.utils.unregister_class(AMLIST_PT_light_l)
	except: pass

	try:
		bpy.utils.unregister_class(AMLIST_PT_img)
	except: pass

	try:
		bpy.utils.unregister_class(AMLIST_PT_cam)
	except: pass
	try:
		bpy.utils.unregister_class(AMLIST_PT_view3d)
	except: pass



	for cls in reversed(classes):
		bpy.utils.unregister_class(cls)
