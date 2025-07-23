import bpy
from ..ui_main_common import *

def draw_cam_item(self, context, layout, item):
	props = context.scene.am_list

	index = bpy.data.objects.find(item.name)
	item_data = item.data
	main_col = layout.row(align = True)
	main_sp = main_col.split(align=True,factor=0.8)
	row = main_sp.row(align=True)

	##########################################
	icon_sel = "RESTRICT_SELECT_ON"
	emboss_hlt = False

	try:
		if item.select_get():
			emboss_hlt = True
			if item.name == bpy.context.active_object.name:
					icon_sel = "RESTRICT_SELECT_OFF"
			else:
				icon_sel = "PMARKER_SEL"
	except: pass

	##########################################
	# 個別アイテムの詳細メニューボタン
	if props.cam_uidetail_toggle:
		no_users = (item.use_fake_user and item.users == 1)
		row.prop(item.am_list,"uidetail_toggle",text="",icon="TRIA_DOWN" if item.am_list.uidetail_toggle else "TRIA_RIGHT",emboss=emboss_hlt)

	##########################################
	rows = row.row(align=True)
	rows.scale_x = 1.2
	sel = rows.operator("am_list.mat_select",text="" ,icon=icon_sel,emboss=emboss_hlt)
	sel.data_type = "OBJECT"
	sel.item_name = item.name

	##########################################
	if props.cam_ui_hide_select:
		row.separator()
		if item.hide_select:
			rows = row.row(align=True)
			rows.active=False
			rows.prop(item,"hide_select",text="",icon="RESTRICT_SELECT_OFF", emboss=emboss_hlt)
		else:
			row.prop(item,"hide_select",text="",icon="RESTRICT_SELECT_OFF", emboss=emboss_hlt)

	if item.hide_get():
		row.active = False
		hideset = row.operator("am_list.item_hide_set", text="", icon="HIDE_ON", emboss=emboss_hlt)
		hideset.item_name = item.name
		hideset.type = "cam"
	else:
		hideset = row.operator("am_list.item_hide_set", text="", icon="HIDE_OFF", emboss=emboss_hlt)
		hideset.item_name = item.name
		hideset.type = "cam"


	if props.cam_ui_hide_viewport:
		if item.hide_viewport:
			rows = row.row(align=True)
			rows.active=False
			rows.prop(item,"hide_viewport",text="",icon="RESTRICT_VIEW_OFF", emboss=emboss_hlt)
		else:
			row.prop(item,"hide_viewport",text="",icon="RESTRICT_VIEW_OFF", emboss=emboss_hlt)




	if item.hide_render:
		rows = row.row(align=True)
		rows.active=False
		rows.prop(item,"hide_render",text="",icon="RESTRICT_RENDER_OFF", emboss=emboss_hlt)
	else:
		row.prop(item,"hide_render",text="",icon="RESTRICT_RENDER_OFF", emboss=emboss_hlt)

	row.separator()


	###########################################
	if item == bpy.context.scene.camera:
		icon_val = "VIEW_CAMERA"
	else: icon_val = "CAMERA_DATA"

	set = row.operator("am_list.cam_set_view",text="",icon=icon_val,emboss=emboss_hlt)
	set.item_name = item.name

	###########################################
	# 名前
	sp = row.split(align=True,factor=1)
	sp.ui_units_x = props.cam_width
	# rowname.alignment = "LEFT"
	sp.prop(item,"name",text="",icon="NONE")
	row.separator()

	###########################################
	if props.cam_ui_data_type or props.cam_ui_lens:
		rowwih = row.row(align=True)
		rowwih.ui_units_x = .15
		rowwih.prop(props,"cam_width")

	row.separator()

	###########################################
	if props.cam_ui_lens:
		rows = row.row(align=True)
		rows.scale_x = .5
		if item.data.lens_unit == 'MILLIMETERS':
			rows.prop(item.data, "lens",text="",emboss=emboss_hlt)
		elif item.data.lens_unit == 'FOV':
			rows.prop(item.data, "angle",text="")


	###########################################
	if props.cam_ui_data_type:
		rowtype = row.row(align=True)
		rowtype.scale_x = .5
		rowtype.prop(item_data, "type",text="")


	###########################################
	row = main_sp.row(align=True)
	row.alignment="RIGHT"
	row.separator()

	try:
		m_frame = bpy.context.scene.timeline_markers[item.name].frame
		c_frame = context.scene.frame_current

		if m_frame == c_frame:
			icon_marker = "MARKER_HLT"
	except:
		icon_marker = "MARKER"

	set = row.operator("am_list.cam_set_marker",text="",icon=icon_marker,emboss=emboss_hlt)
	set.item_name = item.name


	row.separator()


	item_del = row.operator("am_list.item_delete",text="" ,icon="X",emboss=emboss_hlt)
	item_del.item_name = item.name
	item_del.type = "obj"
