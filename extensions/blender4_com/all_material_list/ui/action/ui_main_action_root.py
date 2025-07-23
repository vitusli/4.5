import bpy

from .ui_main_action_uidetail import *
from .ui_uilist_action import AMLIST_UL_action
# from ...import __package__ as addon_id
from ... import __package__ as addon_id
## メインメニュー
def draw_action_menu_root(self, context, is_compactmode, editor_type):
	layout = self.layout
	props = context.scene.am_list
	prefs = bpy.context.preferences.addons[addon_id].preferences
	wm = bpy.context.scene.am_list_wm

	# header
	draw_compactmode_header(self, context, layout, is_compactmode, editor_type=editor_type)

	open = wm.toggle_action
	if prefs.usepanel_action:
		if is_compactmode:
			open = wm.toggle_action
		else:
			open = True
	if not open:
		return

	# option menu
	list_option_menu(self, context, layout)


	all_data_l = [o for o in bpy.data.actions]
	if len(all_data_l) >= props.action_scroll_num:
		l_height = props.action_scroll_num
	elif len(all_data_l) <= 3:
		l_height = 3
	else:
		l_height = len(all_data_l)

	layout.template_list(
		"AMLIST_UL_action","",
		bpy.data, "actions",
		props, "id_mat",
		rows = l_height
	)


	# アクティブ
	# if props.action_uidetail_toggle_act:
	# 	if bpy.context.object:
	# 		if bpy.context.object.type == "ACTION":
	# 				obj = bpy.context.object
	# 				uidetail_menu(self, context, layout, obj)
	# 		else:
	# 			box = layout.box()
	# 			box.label(text="No Active Light Probe Object")
	# 	else:
	# 		box = layout.box()
	# 		box.label(text="No Active Object")


# ヘッダー
def draw_compactmode_header(self, context, layout, is_compactmode, editor_type):
	props = context.scene.am_list
	prefs = bpy.context.preferences.addons[addon_id].preferences
	wm = bpy.context.scene.am_list_wm

	if editor_type == "3dview":
		prefs_editor_type = prefs.usepanel_action
	elif editor_type == "dopesheet":
		prefs_editor_type = prefs.usepanel_action_dopesheet
	elif editor_type == "graph":
		prefs_editor_type = prefs.usepanel_action_graph


	if not prefs_editor_type or is_compactmode:
		sp = layout.split(align=True,factor=0.7)
		rows = sp.row(align=True)
		rows.alignment = 'LEFT'
		rows.prop(wm, "toggle_action",text="",icon="TRIA_DOWN" if wm.toggle_action else "TRIA_RIGHT", emboss=False)
		rows.prop(wm, "toggle_action",icon="ACTION",emboss=False)
		row = sp.row(align=True)
		row.alignment = 'RIGHT'
		all_obj = [o for o in bpy.data.objects if o.type =='ACTION']
		row.label(text=": " + str(len(all_obj)))
		row.label(text="",icon="BLANK1")
		row.menu("AMLIST_MT_other_action", icon='DOWNARROW_HLT', text="")


# リスト上のオプションメニュー
def list_option_menu(self, context, layout):
	props = context.scene.am_list


	box = layout.box()
	col_main = box.column(align=True)

	rows = col_main.row(align=True)
	rows.prop(props,"action_filter_type",text="",expand=True)
	if props.action_filter_type=="Collection":
		row_colle = rows.row(align=True)
		if not props.action_filter_colle:
			row_colle.alert =True
		row_colle.prop(props,"action_filter_colle",text="",expand=True)
	rows.separator()

	rows.prop(props,"action_assign_type",text="",expand=True)
	rows.separator()


	rows.prop(props, "action_uidetail_toggle_act",text="",icon="OBJECT_DATA")
	rows.prop(props, "action_uidetail_toggle",text="",icon="STICKY_UVS_DISABLE")
	rows.separator()
	if props.action_uidetail_toggle:
		uidetail = rows.operator("am_list.uidetail_toggle_all",text="" ,icon="FULLSCREEN_ENTER")
		uidetail.type="action"
		uidetail.open=props.action_uidetail_toggle_status

	if props.action_uidetail_toggle_act or props.action_uidetail_toggle:
		rows.prop(props,"action_uidetail_nameedit",text="" ,icon="SORTALPHA")


	rowx = rows.row(align=True)
	rowx.alignment="RIGHT"
	# rowx.operator("action.new",text="",icon="ADD")
	rowx.operator("am_list.action_add",text="",icon="ADD")


	col_main.separator()
	row = col_main.row(align = True)
	row.prop(props,"action_filter",text="",icon="VIEWZOOM")
	row.prop(props, "action_filter_use_regex_src",text="", icon='SORTBYEXT')
	row.menu("AMLIST_MT_filter_menu_action", icon='DOWNARROW_HLT', text="")
	row.separator()
	rows = row.row(align=True)
	rows.scale_x = .3
	# rows.prop(props, "action_filter_sort_type",text="")
	rows.label(text="",icon="NONE")
	row.prop(props, "action_filter_reverse",text="", icon='SORT_DESC' if props.action_filter_reverse else "SORT_ASC")
