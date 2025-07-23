import bpy
from .ui_sc_l_uidetail import *
from .ui_sc_l_item import *
from ... import __package__ as addon_id

# メインメニュー
def draw_sc_l_menu_root(self, context,is_compactmode):
	layout = self.layout
	props = context.scene.am_list
	prefs = bpy.context.preferences.addons[addon_id].preferences
	wm = bpy.context.scene.am_list_wm


	# header
	draw_compactmode_header(self, context, layout, is_compactmode)


	open = wm.toggle_sc_l
	if prefs.usepanel_sc_l:
		if is_compactmode:
			open = wm.toggle_sc_l
		else:
			open = True
	if not open:
		return

	# コンパクトモード
	draw_sc_l_option_menu(self, context, layout)

	all_data_l = [o for o in bpy.data.scenes]
	if len(all_data_l) >= props.sc_l_scroll_num:
		l_height = props.sc_l_scroll_num
	else:
		l_height = len(all_data_l)

	layout.template_list(
		"AMLIST_UL_sc_l","",
		bpy.data, "scenes",
		prefs, "id_sc_l",
		rows = l_height
	)

	if props.sc_l_uidetail_toggle_act:
		draw_sc_l_view_layer(self, context,layout,bpy.context.scene)


# ヘッダー
def draw_compactmode_header(self, context, layout, is_compactmode):
	props = context.scene.am_list
	prefs = bpy.context.preferences.addons[addon_id].preferences
	wm = bpy.context.scene.am_list_wm
	if not prefs.usepanel_sc_l or is_compactmode:
		sp = layout.split(align=True,factor=0.7)
		rows = sp.row(align=True)
		rows.alignment = 'LEFT'
		rows.prop(wm, "toggle_sc_l",text="",icon="TRIA_DOWN" if wm.toggle_sc_l else "TRIA_RIGHT",emboss=False)
		rows.prop(wm, "toggle_sc_l",icon="SCENE_DATA",emboss=False)

		row = sp.row(align=True)
		row.alignment = 'RIGHT'
		item_count = len(bpy.data.scenes)
		row.label(text=" : " + str(item_count))
		row.label(text="",icon="BLANK1")
		row.menu("AMLIST_MT_other_sc_l",text="",icon="DOWNARROW_HLT")


# リスト上のオプションメニュー
def draw_sc_l_option_menu(self, context, layout):
	props = context.scene.am_list
	box_main = layout.box()
	col_main = box_main.column(align=True)
	rows = col_main.row(align=True)

	rows.separator()

	rows.prop(props, "sc_l_uidetail_toggle_act",text="",icon="RENDERLAYERS")
	rows.prop(props, "sc_l_uidetail_toggle",text="",icon="STICKY_UVS_DISABLE")
	rows.separator()

	if props.sc_l_uidetail_toggle:
		open = True
		open_check_l = [i for i in bpy.data.scenes if i.am_list.uidetail_toggle]
		if len(open_check_l):
			open = False

		uidetail = rows.operator("am_list.uidetail_toggle_all",text="" ,icon="FULLSCREEN_ENTER")
		uidetail.type="sc_l"
		uidetail.open=open


	# if props.sc_l_uidetail_toggle_act or props.sc_l_uidetail_toggle:
	# 	rows.prop(props,"sc_l_uidetail_nameedit",text="" ,icon="SORTALPHA")

	# add
	row_add = rows.row(align=True)
	row_add.scale_x = 1.3
	row_add.alignment = "RIGHT"
	row_add.operator("scene.new",text="",icon="ADD")
	row_add.separator()

	col_main.separator()
	row = col_main.row(align = True)
	row.prop(props,"sc_l_filter",text="",icon="VIEWZOOM")
	row.prop(props, "sc_l_filter_use_regex_src",text="", icon='SORTBYEXT')
	row.menu("AMLIST_MT_filter_menu_sc_l", icon='DOWNARROW_HLT', text="")
	row.separator()
	rows = row.row(align=True)
	rows.scale_x = .4
	rows.prop(props, "sc_l_filter_sort_type",text="")
	row.prop(props, "sc_l_filter_reverse",text="", icon='SORT_DESC' if props.sc_l_filter_reverse else "SORT_ASC")
