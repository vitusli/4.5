import bpy

from .ui_main_light_l_uidetail import *
from .ui_uilist_light_l import AMLIST_UL_light_l
from ... import __package__ as addon_id
# メインメニュー
def draw_light_l_menu_root(self, context,is_compactmode):
	layout = self.layout
	props = context.scene.am_list
	prefs = bpy.context.preferences.addons[addon_id].preferences
	wm = bpy.context.scene.am_list_wm


	# header
	draw_compactmode_header(self, context, layout, is_compactmode)

	open = wm.toggle_light_l
	if prefs.usepanel_light_l:
		if is_compactmode:
			open = wm.toggle_light_l
		else:
			open = True
	if not open:
		return

	# option menu
	list_option_menu(self, context, layout)

	all_data_l = [o for o in bpy.data.objects if o.type == "LIGHT"]
	if len(all_data_l) >= props.light_l_scroll_num:
		l_height = props.light_l_scroll_num
	elif len(all_data_l) <= 3:
		l_height = 3
	else:
		l_height = len(all_data_l)

	layout.template_list(
		"AMLIST_UL_light_l","",
		bpy.data, "objects",
		props, "id_mat",
		rows = l_height
	)


	# アクティブ
	if props.light_l_uidetail_toggle_act:
		if bpy.context.object:
			if bpy.context.object.type == "LIGHT":
					obj = bpy.context.object
					uidetail_menu(self, context, layout, obj)
			else:
				box = layout.box()
				box.label(text="No Active Light Object")
		else:
			box = layout.box()
			box.label(text="No Active Object")


# ヘッダー
def draw_compactmode_header(self, context, layout, is_compactmode):
	props = context.scene.am_list
	prefs = bpy.context.preferences.addons[addon_id].preferences
	wm = bpy.context.scene.am_list_wm
	if not prefs.usepanel_light_l or is_compactmode:
		sp = layout.split(align=True,factor=0.7)
		rows = sp.row(align=True)
		rows.alignment = 'LEFT'
		rows.prop(wm, "toggle_light_l",text="",icon="TRIA_DOWN" if wm.toggle_light_l else "TRIA_RIGHT", emboss=False)
		rows.prop(wm, "toggle_light_l",icon="LIGHT",emboss=False)
		row = sp.row(align=True)
		row.alignment = 'RIGHT'
		filter_obj = list(AMLIST_UL_light_l.get_props_filtered_items(None))
		all_obj = [o for o in bpy.data.objects if o.type =='LIGHT']
		row.label(text=str(len(filter_obj))+" : " + str(len(all_obj)))
		row.label(text="",icon="BLANK1")
		row.menu("AMLIST_MT_other_light_l", icon='DOWNARROW_HLT', text="")


# リスト上のオプションメニュー
def list_option_menu(self, context, layout):
	props = context.scene.am_list

	box_main = layout.box()
	col_main = box_main.column(align=True)
	rows = col_main.row(align=True)
	rows.prop(props,"light_l_filter_type",text="",expand=True)
	if props.light_l_filter_type=="Collection":
		row_colle = rows.row(align=True)
		row_colle.alert = bool(not props.light_l_filter_colle )
		row_colle.prop(props,"light_l_filter_colle",text="")

	rows.separator()


	rows.prop(props, "light_l_uidetail_toggle_act",text="",icon="OBJECT_DATA")
	rows.prop(props, "light_l_uidetail_toggle",text="",icon="STICKY_UVS_DISABLE")
	rows.separator()

	if props.light_l_uidetail_toggle:
		uidetail = rows.operator("am_list.uidetail_toggle_all",text="" ,icon="FULLSCREEN_ENTER")
		uidetail.type="light_l"
		uidetail.open=props.light_l_uidetail_toggle_status


	rowss = rows.row(align=True)
	rowss.alignment="RIGHT"

	if bpy.context.scene.render.engine == 'BLENDER_EEVEE':
		rowss.operator("scene.light_cache_bake", text="", icon='RENDER_STILL')
		if bpy.app.version >= (4,1,0):
			icon_val = "LIGHTPROBE_VOLUME"
		else:
			icon_val = "LIGHTPROBE_CUBEMAP"
		rowss.operator("scene.light_cache_bake", text="", icon=icon_val).subset = 'CUBEMAPS'
		rowss.operator("scene.light_cache_free", text="",icon="X")
		rowss.separator()
		rowss.separator()

	rowss.menu("VIEW3D_MT_light_add",text="",icon="ADD")
	rowss.separator()
	rowss.menu("AMLIST_MT_other_light_l", icon='DOWNARROW_HLT', text="")


	col_main.separator()
	row = col_main.row(align = True)
	row.prop(props,"light_l_filter",text="",icon="VIEWZOOM")
	row.prop(props, "light_l_filter_use_regex_src",text="", icon='SORTBYEXT')
	row.menu("AMLIST_MT_filter_menu_light_l", icon='DOWNARROW_HLT', text="")
	row.separator()
	rows = row.row(align=True)
	rows.scale_x = .4
	rows.prop(props, "light_l_filter_sort_type",text="")
	row.prop(props, "light_l_filter_reverse",text="", icon='SORT_DESC' if props.light_l_filter_reverse else "SORT_ASC")
