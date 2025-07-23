import bpy
from .mat.ui_main_mat import *
from .mat.ui_main_mat_index import *
from .mat.ui_main_mat_new import *
from .ui_main_slot import *
from .ui_main_vcol import *
from .ui_main_wld import *
from .cam.ui_main_cam_root import *
from .ui_main_img import *
from .light_l.ui_main_light_l_root import *
from .light_p.ui_main_light_p_root import *
from .sc_l.ui_sc_l_main import *
from .action.ui_main_action_root import *
from .. import __package__ as addon_id


def draw_main_menu(self, context,is_compactmode):
	layout = self.layout
	prefs = bpy.context.preferences.addons[addon_id].preferences
	wm = bpy.context.scene.am_list_wm

	# Mat New
	if prefs.hide_mat_new:
		draw_matnew_menu(self, context, is_compactmode)


	# Slot
	if prefs.hide_slot:
		draw_matslot_menu(self, context)


	# mat
	if prefs.hide_mat_index:
		if not prefs.usepanel_mat_index or is_compactmode:
			draw_mat_menu_root(self, context, is_popup=False, is_compactmode=is_compactmode)


	# Viewport Color
	if prefs.hide_vcol:
		if not prefs.usepanel_vcol or is_compactmode:
			draw_panel_vcol_menu(self, context, is_compactmode=is_compactmode)


	# Light List
	if prefs.hide_light_l:
		if not prefs.usepanel_light_l or is_compactmode:
			draw_light_l_menu_root(self, context, is_compactmode=is_compactmode)


	# Light Probe List
	if prefs.hide_light_p:
		if not prefs.usepanel_light_p or is_compactmode:
			draw_light_p_menu_root(self, context, is_compactmode=is_compactmode)


	# Light List
	# if prefs.hide_light_m:
	# 	if not prefs.usepanel_light_m or is_compactmode:
	# 			draw_panel_light_m_menu(self, context,is_compactmode=is_compactmode)



	# Camera List
	if prefs.hide_cam:
		if not prefs.usepanel_cam or is_compactmode:
			draw_cam_menu_root(self, context, is_compactmode=is_compactmode)


	# World List
	if prefs.hide_wld:
		if not prefs.usepanel_wld or is_compactmode:
			draw_panel_wld_menu(self, context,is_compactmode=is_compactmode)


	# Image List
	if prefs.hide_img:
		if not prefs.usepanel_img or is_compactmode:
			draw_panel_img_menu(self, context,is_compactmode=is_compactmode)

	if prefs.hide_sc_l:
		if not prefs.usepanel_sc_l or is_compactmode:
			draw_sc_l_menu_root(self, context,is_compactmode=is_compactmode)

	if prefs.hide_action:
		if not prefs.usepanel_action or is_compactmode:
			draw_action_menu_root(self, context ,is_compactmode=is_compactmode,editor_type="3dview")

	return {'FINISHED'}
