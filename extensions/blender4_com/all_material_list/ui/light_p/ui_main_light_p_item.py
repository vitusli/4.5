import bpy
from ..ui_main_common import *
# from .ui_main_light_p_create_list import *
from .ui_main_light_p_uidetail import *

def draw_light_p_item(self, context, layout, item):
	props = context.scene.am_list

	index = bpy.data.objects.find(item.name)
	obj_data = bpy.data.objects[item.name]
	item_data = item.data
	main_col = layout.row(align = True)
	factor_val = 0.95

	main_sp = main_col.split(align=True,factor=factor_val)
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
	if props.light_p_uidetail_toggle:
		no_users = (item.use_fake_user and item.users == 1)
		row.prop(item.am_list,"uidetail_toggle",text="",icon="TRIA_DOWN" if item.am_list.uidetail_toggle else "TRIA_RIGHT",emboss=emboss_hlt)

	##########################################
	rows = row.row(align=True)
	rows.scale_x = 1.2
	sel = rows.operator("am_list.mat_select",text="" ,icon=icon_sel,emboss=emboss_hlt)
	sel.data_type = "OBJECT"
	sel.item_name = item.name

	##########################################
	row.separator()
	if props.light_p_ui_hide_select:
		if obj_data.hide_select:
			rows = row.row(align=True)
			rows.active=False
			rows.prop(obj_data,"hide_select",text="",icon="RESTRICT_SELECT_OFF", emboss=emboss_hlt)
		else:
			row.prop(obj_data,"hide_select",text="",icon="RESTRICT_SELECT_OFF", emboss=emboss_hlt)


	if item.hide_get():
		row.active = False
		hideset = row.operator("am_list.item_hide_set", text="", icon="HIDE_ON", emboss=emboss_hlt)
		hideset.item_name = item.name
		hideset.type = "light_p"
	else:
		hideset = row.operator("am_list.item_hide_set", text="", icon="HIDE_OFF", emboss=emboss_hlt)
		hideset.item_name = item.name
		hideset.type = "light_p"

	if props.light_p_ui_hide_viewport:
		if obj_data.hide_viewport:
			rows = row.row(align=True)
			rows.active=False
			rows.prop(obj_data,"hide_viewport",text="",icon="RESTRICT_VIEW_OFF", emboss=emboss_hlt)
		else:
			row.prop(obj_data,"hide_viewport",text="",icon="RESTRICT_VIEW_OFF", emboss=emboss_hlt)

	if item.hide_render:
		rows = row.row(align=True)
		rows.active=False
		rows.prop(item,"hide_render",text="",icon="RESTRICT_RENDER_OFF", emboss=emboss_hlt)
	else:
		row.prop(item,"hide_render",text="",icon="RESTRICT_RENDER_OFF", emboss=emboss_hlt)

	row.separator()



	###########################################

	try:
		if item_data.type in {'GRID'}:
			icon_val = "LIGHTPROBE_GRID"
		if item_data.type in {'PLANAR'}:
			icon_val = "LIGHTPROBE_PLANAR"
		if item_data.type in {'CUBEMAP'}:
			icon_val = "LIGHTPROBE_CUBEMAP"
	except: icon_val = "BLANK1"
	rows = row.row(align=True)
	rows.label(text="",icon=icon_val)

	# 名前
	sp = row.split(align=True,factor=1)
	sp.ui_units_x = props.light_p_width
	sp.prop(obj_data,"name",text="")
	row.separator()

	###########################################
	if props.light_p_ui_distance or props.light_p_ui_falloff or props.light_p_ui_intensity or props.light_p_ui_resolution:
		rowwih = row.row(align=True)
		rowwih.ui_units_x = .15
		rowwih.prop(props,"light_p_width")

	row.separator()


	if item_data.type == 'GRID':
		if props.light_p_ui_distance:
			row.prop(item_data, "influence_distance", text="",emboss=emboss_hlt)
		if props.light_p_ui_falloff:
			row.prop(item_data, "falloff", text="",emboss=emboss_hlt)
		if props.light_p_ui_intensity:
			row.prop(item_data, "intensity", text="",emboss=emboss_hlt)
		row.separator()
		if props.light_p_ui_resolution:
			row.prop(item_data, "grid_resolution_x", text="",emboss=emboss_hlt)
			row.prop(item_data, "grid_resolution_y", text="",emboss=emboss_hlt)
			row.prop(item_data, "grid_resolution_z", text="",emboss=emboss_hlt)

	elif item_data.type == 'PLANAR':
		if props.light_p_ui_distance:
			if props.light_p_ui_distance:
				row.prop(item_data, "influence_distance", text="",emboss=emboss_hlt)
		if props.light_p_ui_falloff:
			row.prop(item_data, "falloff", text="",emboss=emboss_hlt)
		if props.light_p_ui_intensity:
			row.label(text=" ",icon="BLANK1")
		if props.light_p_ui_resolution:
			row.label(text=" ",icon="BLANK1")
			row.label(text=" ",icon="BLANK1")
			row.label(text=" ",icon="BLANK1")


	else:

		if props.light_p_ui_distance:
			row.prop(item_data, "influence_distance", text="",emboss=emboss_hlt)
		if props.light_p_ui_falloff:
			row.prop(item_data, "falloff", text="",emboss=emboss_hlt)
		if props.light_p_ui_intensity:
			row.prop(item_data, "intensity", text="",emboss=emboss_hlt)

		if not item_data.influence_type == 'ELIPSOID':
			row.separator()
			row.label(text="",icon="NONE")
			row.label(text="",icon="NONE")


		if props.light_p_ui_influence_type:
			row.prop(item_data, "influence_type",text="",emboss=emboss_hlt)





	###########################################
	row = main_sp.row(align=True)
	row.alignment="RIGHT"

	row.separator()

	item_del = row.operator("am_list.item_delete",text="" ,icon="X",emboss=emboss_hlt)
	item_del.item_name = item.name
	item_del.type = "obj"
