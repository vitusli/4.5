import bpy
from .ui_panel import *
from .. import  __package__ as addon_id

# 起動時に実行。パネルが有効の場合は読み込み
# アドオン設定のパネルメニュー切り替えをした時に実行
def regi_panel(prop_name,class_name):
	prefs = bpy.context.preferences.addons[addon_id].preferences

	try:
		if prefs.category:
			if "bl_rna" in class_name.__dict__:
				bpy.utils.unregister_class(class_name)

			class_name.bl_category = prefs.category
			if prop_name: # パネル表示設定が有効の場合
				bpy.utils.register_class(class_name)
		else:
			bpy.utils.unregister_class(class_name)


	except Exception as e:
		print("\n[{}]\n{}\n\nError:\n{}".format(__name__,"  !!  NO  !!  "  + str(class_name), e))
		pass


def update_regipanel_action_dopesheet(self,context):
	prefs = bpy.context.preferences.addons[addon_id].preferences
	regi_panel(prefs.usepanel_action_dopesheet,AMLIST_PT_action_dopesheet)


def update_regipanel_action_graph(self,context):
	prefs = bpy.context.preferences.addons[addon_id].preferences
	regi_panel(prefs.usepanel_action_graph,AMLIST_PT_action_graph)


def update_regipanel_action(self,context):
	prefs = bpy.context.preferences.addons[addon_id].preferences
	regi_panel(prefs.usepanel_action,AMLIST_PT_action)


def update_regipanel_cam(self,context):
	prefs = bpy.context.preferences.addons[addon_id].preferences
	regi_panel(prefs.usepanel_cam,AMLIST_PT_cam)


def update_regipanel_sc_l(self,context):
	prefs = bpy.context.preferences.addons[addon_id].preferences
	regi_panel(prefs.usepanel_sc_l,AMLIST_PT_sc_l)


def update_regipanel_img(self,context):
	prefs = bpy.context.preferences.addons[addon_id].preferences
	regi_panel(prefs.usepanel_img,AMLIST_PT_img)


def update_regipanel_light_l(self,context):
	prefs = bpy.context.preferences.addons[addon_id].preferences
	regi_panel(prefs.usepanel_light_l,AMLIST_PT_light_l)


# def update_regipanel_light_m(self,context):
# 	prefs = bpy.context.preferences.addons[addon_id].preferences
# 	regi_panel(prefs.usepanel_light_m,AMLIST_PT_light_m)


def update_regipanel_light_p(self,context):
	prefs = bpy.context.preferences.addons[addon_id].preferences
	regi_panel(prefs.usepanel_light_p,AMLIST_PT_light_p)


def update_regipanel_mat_index(self,context):
	prefs = bpy.context.preferences.addons[addon_id].preferences
	regi_panel(prefs.usepanel_mat_index,AMLIST_PT_mat_index)


def update_regipanel_vcol(self,context):
	prefs = bpy.context.preferences.addons[addon_id].preferences
	regi_panel(prefs.usepanel_vcol,AMLIST_PT_vcol)


def update_regipanel_wld(self,context):
	prefs = bpy.context.preferences.addons[addon_id].preferences
	regi_panel(prefs.usepanel_wld,AMLIST_PT_wld)


def update_regipanel_mainmenu_view3d(self,context):
	prefs = bpy.context.preferences.addons[addon_id].preferences
	regi_panel(prefs.usepanel_mainmenu_view3d,AMLIST_PT_view3d)


def update_regipanel_mainmenu_in_prop(self,context):
	prefs = bpy.context.preferences.addons[addon_id].preferences
	regi_panel(prefs.usepanel_mainmenu_in_prop,AMLIST_PT_property)


def update_panel(self, context):
	prefs = bpy.context.preferences.addons[addon_id].preferences
	cate = prefs.category
	message = ": Updating Panel locations has failed"

	for panel in panels:
		try:
			if panel == AMLIST_PT_property:
				if not prefs.usepanel_mainmenu_in_prop:
					continue

				if "bl_rna" in panel.__dict__:
					bpy.utils.unregister_class(panel)

				panel.bl_category = cate
				bpy.utils.register_class(panel)

			else:
				try:
					bpy.utils.unregister_class(panel)
				except RuntimeError: pass

		except Exception as e:
			print("\n[{}]\n{}\n\nError:\n{}".format(__name__.partition('.')[0], message, e))
			pass


		try:
			if cate:
				if panel == AMLIST_PT_view3d:
					if not prefs.usepanel_mainmenu_view3d:
						continue

				# パネルが無効の場合は再登録から無視する
				if panel == AMLIST_PT_mat_index:
					if not prefs.usepanel_mat_index:
						continue
				if panel == AMLIST_PT_action:
					if not prefs.usepanel_action:
						continue
				if panel == AMLIST_PT_cam:
					if not prefs.usepanel_cam:
						continue
				if panel == AMLIST_PT_vcol:
					if not prefs.usepanel_vcol:
						continue
				if panel == AMLIST_PT_light_l:
					if not prefs.usepanel_light_l:
						continue
				if panel == AMLIST_PT_light_p:
					if not prefs.usepanel_light_p:
						continue
				# if panel == AMLIST_PT_light_m:
				# 	if not prefs.usepanel_light_m:
				# 		continue
				if panel == AMLIST_PT_wld:
					if not prefs.usepanel_wld:
						continue
				if panel == AMLIST_PT_img:
					if not prefs.usepanel_img:
						continue
				if panel == AMLIST_PT_sc_l:
					if not prefs.usepanel_img:
						continue

				if "bl_rna" in panel.__dict__:
					bpy.utils.unregister_class(panel)

				panel.bl_category = cate
				bpy.utils.register_class(panel)

			else:
				try:
					bpy.utils.unregister_class(panel)
				except RuntimeError: pass

		except Exception as e:
			print("\n[{}]\n{}\n\nError:\n{}".format(__name__.partition('.')[0], message, e))
			pass


panels = ( # ここの順番でパネルが読み込まれる
		AMLIST_PT_view3d,
		AMLIST_PT_mat_index,
		AMLIST_PT_vcol,
		AMLIST_PT_light_l,
		AMLIST_PT_light_p,
		AMLIST_PT_cam,
		AMLIST_PT_action,
		AMLIST_PT_img,
		AMLIST_PT_wld,
		AMLIST_PT_sc_l,
		# AMLIST_PT_light_m,

		AMLIST_PT_property,

		)

list_panels = (
		# AMLIST_PT_light_m,
		AMLIST_PT_action,
		AMLIST_PT_cam,
		AMLIST_PT_img,
		AMLIST_PT_light_l,
		AMLIST_PT_light_p,
		AMLIST_PT_mat_index,
		AMLIST_PT_sc_l,
		AMLIST_PT_vcol,
		AMLIST_PT_wld,
		)
