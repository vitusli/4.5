import bpy

from .ui_main_cam_uidetail import *
from .ui_uilist_cam import AMLIST_UL_cam
from ... import __package__ as addon_id
# from ... import __package__ as addon_id
# メインメニュー
def draw_cam_menu_root(self, context, is_compactmode):
	layout = self.layout
	props = context.scene.am_list
	prefs = bpy.context.preferences.addons[addon_id].preferences
	wm = bpy.context.scene.am_list_wm


	# header
	draw_compactmode_header(self, context, layout, is_compactmode)

	open = wm.toggle_cam
	if prefs.usepanel_cam:
		if is_compactmode:
			open = wm.toggle_cam
		else:
			open = True
	if not open:
		return

	# option menu
	list_option_menu(self, context, layout)


	all_data_l = [o for o in bpy.data.objects if o.type == "LIGHT_PROBE"]
	if len(all_data_l) >= props.cam_scroll_num:
		l_height = props.cam_scroll_num
	elif len(all_data_l) <= 3:
		l_height = 3
	else:
		l_height = len(all_data_l)

	layout.template_list(
		"AMLIST_UL_cam","",
		bpy.data, "objects",
		props, "id_mat",
		rows = l_height
	)


	# アクティブ
	if props.cam_uidetail_toggle_act:
		if bpy.context.object:
			if bpy.context.object.type == "LIGHT_PROBE":
					obj = bpy.context.object
					uidetail_menu(self, context, layout, obj)
			else:
				box = layout.box()
				box.label(text="No Active Light Probe Object")
		else:
			box = layout.box()
			box.label(text="No Active Object")


# ヘッダー
def draw_compactmode_header(self, context, layout, is_compactmode):
	props = context.scene.am_list
	prefs = bpy.context.preferences.addons[addon_id].preferences
	wm = bpy.context.scene.am_list_wm
	if not prefs.usepanel_cam or is_compactmode:
		sp = layout.split(align=True,factor=0.7)
		rows = sp.row(align=True)
		rows.alignment = 'LEFT'
		rows.prop(wm, "toggle_cam",text="",icon="TRIA_DOWN" if wm.toggle_cam else "TRIA_RIGHT", emboss=False)
		rows.prop(wm, "toggle_cam",icon="CAMERA_DATA",emboss=False)
		row = sp.row(align=True)
		row.alignment = 'RIGHT'
		filter_obj = list(AMLIST_UL_cam.get_props_filtered_items(None))
		all_obj = [o for o in bpy.data.objects if o.type =='CAMERA']
		row.label(text=str(len(filter_obj))+" : " + str(len(all_obj)))
		row.label(text="",icon="BLANK1")
		row.menu("AMLIST_MT_other_cam", icon='DOWNARROW_HLT', text="")


# リスト上のオプションメニュー
def list_option_menu(self, context, layout):
	props = context.scene.am_list

	box_main = layout.box()
	col_main = box_main.column(align=True)
	rows = col_main.row(align=True)
	rows.prop(props,"cam_filter_type",text="",expand=True)
	if props.cam_filter_type=="Collection":
		row_colle = rows.row(align=True)
		row_colle.alert = bool(not props.cam_filter_colle )
		row_colle.prop(props,"cam_filter_colle",text="")

	rows.separator()


	rows.prop(props, "cam_uidetail_toggle_act",text="",icon="OBJECT_DATA")
	rows.prop(props, "cam_uidetail_toggle",text="",icon="STICKY_UVS_DISABLE")
	rows.separator()

	if props.cam_uidetail_toggle:
		uidetail = rows.operator("am_list.uidetail_toggle_all",text="" ,icon="FULLSCREEN_ENTER")
		uidetail.type="cam"
		uidetail.open=props.cam_uidetail_toggle_status


	rowss = rows.row(align=True)
	rowss.alignment="RIGHT"


	rowss.operator("object.camera_add",text="",icon="ADD")
	rowss.separator()
	rowss.menu("AMLIST_MT_other_cam", icon='DOWNARROW_HLT', text="")


	col_main.separator()
	row = col_main.row(align = True)
	row.prop(props,"cam_filter",text="",icon="VIEWZOOM")
	row.prop(props, "cam_filter_use_regex_src",text="", icon='SORTBYEXT')
	row.menu("AMLIST_MT_filter_menu_cam", icon='DOWNARROW_HLT', text="")
	row.separator()
	rows = row.row(align=True)
	rows.scale_x = .3
	# rows.prop(props, "cam_filter_sort_type",text="")
	rows.label(text="",icon="NONE")
	row.prop(props, "cam_filter_reverse",text="", icon='SORT_DESC' if props.cam_filter_reverse else "SORT_ASC")
