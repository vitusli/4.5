import bpy
from ..ui_main_common import *


# アイテムのメニュー
def draw_light_l_item(self, context, layout, item, is_compactmode_top):
	props = context.scene.am_list

	index = bpy.data.objects.find(item.name)
	item_data = item.data

	main_col = layout.row(align = True)
	factor_val = 0.95


	main_sp = main_col.split(align=True,factor=factor_val)
	row = main_sp.row(align=True)

	##########################################
	# 選択ハイライトの設定
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
	if props.light_l_uidetail_toggle:
		no_users = (item.use_fake_user and item.users == 1)
		row.prop(item.am_list,"uidetail_toggle",text="",icon="TRIA_DOWN" if item.am_list.uidetail_toggle else "TRIA_RIGHT",emboss=emboss_hlt)





	##########################################
	rows = row.row(align=True)
	rows.scale_x = 1.2
	sel = rows.operator("am_list.mat_select",text="" ,icon=icon_sel,emboss=emboss_hlt)
	sel.data_type = "OBJECT"
	sel.item_name = item.name

	##########################################
	if props.light_l_ui_hide_select:
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
		hideset.type = "light_l"
	else:
		hideset = row.operator("am_list.item_hide_set", text="", icon="HIDE_OFF", emboss=emboss_hlt)
		hideset.item_name = item.name
		hideset.type = "light_l"



	if props.light_l_ui_hide_viewport:
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
	# オブジェクトタイプによるアイコンを設定
	try:
		if item_data.type == 'POINT':
			icon_val = "LIGHT_POINT"
		elif item_data.type == 'SPOT':
			icon_val = "LIGHT_SPOT"
		elif item_data.type == 'SUN':
			icon_val = "LIGHT_SUN"
		elif item_data.type == 'AREA':
			icon_val = "LIGHT_AREA"
		elif item_data.type == 'HEMI':
			icon_val = "LIGHT_HEMI"
	except:
		icon_val = "BLANK1"
	rows = row.row(align=True)

	rows.prop(item_data, "type",icon=icon_val,icon_only=True)

	# 名前
	sp = row.split(align=True,factor=1)
	sp.ui_units_x = props.light_l_width
	sp.prop(item,"name",text="")

	if is_compactmode_top:
		return
	row.separator()

	###########################################
	# 各プロパティ
	if props.light_l_color or props.light_l_power or props.light_l_specular or props.light_l_size:
		rowwih = row.row(align=True)
		rowwih.ui_units_x = .15
		rowwih.prop(props,"light_l_width")

	row.separator()



	rows = row.row(align=True)
	rows.scale_x = .5

	if props.light_l_color:
		rowcollor = rows.row()
		rowcollor.scale_x = .4
		rowcollor.prop(item_data, "color",text="")
	if props.light_l_power:
		rows.prop(item_data, "energy",text="",emboss=emboss_hlt)
		col = rows.column(align=True)
		col.scale_x=1.3
		col.scale_y=0.5
		et = col.operator("am_list.energy_twice",text="",icon="LAYER_ACTIVE")
		et.twice = True
		et.item_name = item.name
		et = col.operator("am_list.energy_twice",text="",icon="LAYER_USED")
		et.twice = False
		et.item_name = item.name
	if props.light_l_specular:
		rows.prop(item_data, "specular_factor", text="",emboss=emboss_hlt)



	if props.light_l_size:
		if item_data.type in {'POINT'}:
			rows.prop(item_data, "shadow_soft_size", text="",emboss=emboss_hlt)
			if props.light_l_other_option:
				rows.label(text="",icon="NONE")
				rows.label(text="",icon="NONE")

		if item_data.type in {'SPOT'}:
			rows.prop(item_data, "shadow_soft_size", text="",emboss=emboss_hlt)
			if props.light_l_other_option:
				rows.prop(item_data, "spot_size", text="",emboss=emboss_hlt)
				rows.prop(item_data, "spot_blend", text="", slider=True,emboss=emboss_hlt)
			# row.prop(item_data, "show_cone")

		elif item_data.type == 'SUN':
			rows.prop(item_data, "angle",emboss=emboss_hlt)
			if props.light_l_other_option:
				rows.label(text="",icon="NONE")
				rows.label(text="",icon="NONE")

		elif item_data.type == 'AREA':

			if item_data.shape in {'SQUARE', 'DISK'}:
				rows.prop(item_data, "size")
				if props.light_l_other_option:
					rows.label(text="",icon="NONE")
			elif item_data.shape in {'RECTANGLE', 'ELLIPSE'}:
				if props.light_l_other_option:
					rows.prop(item_data, "size", text="Size X",emboss=emboss_hlt)
					rows.prop(item_data, "size_y", text="Y",emboss=emboss_hlt)
				else:
					rows.label(text="",icon="NONE")


			if props.light_l_other_option:
				rows.prop(item_data, "shape",text="",emboss=emboss_hlt)

	if props.light_l_shadow:
		if item_data.use_shadow:
			row.prop(item_data, "use_shadow", text="",icon="GHOST_ENABLED",emboss=emboss_hlt)
		else:
			row.prop(item_data, "use_shadow", text="",icon="GHOST_DISABLED",emboss=emboss_hlt)




	###########################################
	# オブジェクトの可視設定
	row = main_sp.row(align=True)
	row.alignment="RIGHT"

	row.separator()

	# 削除ボタン
	item_del = row.operator("am_list.item_delete",text="" ,icon="X",emboss=emboss_hlt)
	item_del.item_name = item.name
	item_del.type = "obj"
