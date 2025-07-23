import bpy
from ..ui_main_common import *


# アイテムのメニュー
def draw_sc_l_item(self, context, layout, item):
	act_sc = bpy.context.scene
	props = act_sc.am_list

	index = bpy.data.scenes.find(item.name)
	main_col = layout.row(align = True)
	factor_val = 0.75
	if props.sc_l_filter_object:
		factor_val -= 0.1

	main_sp = main_col.split(align=True,factor=factor_val)
	row = main_sp.row(align=True)


	##########################################
	# 選択ハイライトの設定
	icon_sel = "RESTRICT_SELECT_ON"
	emboss_hlt = False

	try:
		if item.name == act_sc.name:
			emboss_hlt = True
			icon_sel = "RESTRICT_SELECT_OFF"
	except: pass

	##########################################
	# 個別アイテムの詳細メニューボタン
	if props.sc_l_uidetail_toggle:
		no_users = (item.use_fake_user and item.users == 1)
		row.prop(item.am_list,"uidetail_toggle",text="",icon="TRIA_DOWN" if item.am_list.uidetail_toggle else "TRIA_RIGHT",emboss=emboss_hlt)


	##########################################
	rows = row.row(align=True)
	rows.scale_x = 1.2
	sel = rows.operator("am_list.mat_select",text="" ,icon=icon_sel,emboss=emboss_hlt)
	sel.data_type = "SCENE"
	sel.item_name = item.name


	# 名前
	sp = row.split(align=True,factor=1)
	sp.prop(item,"name",text="",emboss=False)
	row.separator()


	###########################################
	# オブジェクトの可視設定
	row_status = main_sp.row(align=True)
	row_status.alignment="RIGHT"
	row_status.label(text="",icon="RENDERLAYERS")
	row = row_status.row(align=True)
	row.ui_units_x = 1.2
	row.alignment="RIGHT"
	row.label(text=str(len(item.view_layers)))
	if props.sc_l_filter_object:
		row_status.label(text="",icon="OBJECT_DATA")
		row_obj = row_status.row(align=True)
		row_obj.ui_units_x = 1.7
		row_obj.alignment="RIGHT"
		row_obj.label(text=str(len(item.objects)))


	row_status.separator()

	# 削除ボタン
	item_del = row_status.operator("am_list.item_delete",text="",icon="X",emboss=emboss_hlt)
	item_del.item_name = item.name
	item_del.type = "sc_l"
