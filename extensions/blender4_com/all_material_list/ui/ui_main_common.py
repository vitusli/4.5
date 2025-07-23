import bpy

def base_status_02(row, item, index, obj_data, emboss_hlt, icon_sel):
	if obj_data.hide_select:
		rows = row.row(align=True)
		rows.active=False
		rows.prop(obj_data,"hide_select",text="",icon="RESTRICT_SELECT_OFF", emboss=emboss_hlt)
	else:
		row.prop(obj_data,"hide_select",text="",icon="RESTRICT_SELECT_OFF", emboss=emboss_hlt)

	if obj_data.hide_viewport:
		rows = row.row(align=True)
		rows.active=False
		rows.prop(obj_data,"hide_viewport",text="",icon="RESTRICT_VIEW_OFF", emboss=emboss_hlt)
	else:
		row.prop(obj_data,"hide_viewport",text="",icon="RESTRICT_VIEW_OFF", emboss=emboss_hlt)


def base_status(row, item, index, obj_data, emboss_hlt, icon_sel):
	##########################################
	rows = row.row(align=True)
	rows.scale_x = 1.2
	sel = rows.operator("am_list.mat_select",text="" ,icon=icon_sel,emboss=emboss_hlt)
	sel.data_type = "OBJECT"
	sel.item_name = item.name

	##########################################
	if obj_data.hide_get():
		row.active = False
		row.operator("am_list.item_hide_set", text="", icon="HIDE_ON", emboss=emboss_hlt).item_name = item.name
	else:
		row.operator("am_list.item_hide_set", text="", icon="HIDE_OFF", emboss=emboss_hlt).item_name = item.name

	if obj_data.hide_render:
		rows = row.row(align=True)
		rows.active=False
		rows.prop(obj_data,"hide_render",text="",icon="RESTRICT_RENDER_OFF", emboss=emboss_hlt)
	else:
		row.prop(obj_data,"hide_render",text="",icon="RESTRICT_RENDER_OFF", emboss=emboss_hlt)

	row.separator()
