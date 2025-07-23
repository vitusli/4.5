import bpy
from ..ui_main_common import *

def draw_action_item(self, context,layout, item):
	props = context.scene.am_list

	index = bpy.data.actions.find(item.name)

	main_col = layout.row(align = True)
	main_sp = main_col.split(align=True,factor=0.9)
	row = main_sp.row(align=True)

	# ##########################################
	icon_sel = "RESTRICT_SELECT_ON"
	emboss_hlt = False

	try:
		sel_l = [obj.animation_data.action for obj in bpy.context.selected_objects if obj.animation_data]

		for i in sel_l:
			if item == i:
				icon_sel = "PMARKER_SEL"
				emboss_hlt = True

		if bpy.context.active_object.animation_data:
			if item == bpy.context.active_object.animation_data.action:
				icon_sel = "RESTRICT_SELECT_OFF"
	except: pass



	##########################################
	# 個別アイテムの詳細メニューボタン
	if props.action_uidetail_toggle:
		no_users = (item.use_fake_user and item.users == 1)
		if item.users and not no_users:
			row.prop(item.am_list,"uidetail_toggle",text="",icon="TRIA_DOWN" if item.am_list.uidetail_toggle else "TRIA_RIGHT",emboss=emboss_hlt)

		else:
			rowobj = row.row(align=True)
			rowobj.label(text="",icon="BLANK1")



	##########################################
	no_users = (item.use_fake_user and item.users == 1)
	if item.users and not no_users:

		rows = row.row(align=True)
		rows.scale_x = 1.2
		sel = rows.operator("am_list.mat_select",text="" ,icon=icon_sel,emboss=emboss_hlt)
		sel.data_type = "ACTION"
		sel.item_name = item.name

	else:
		rowobj = row.row(align=True)
		rowobj.scale_x = 1.2
		rowobj.label(text="",icon="BLANK1")



	##########################################

	row_asin = row.row(align=True)
	# row_asin.scale_x = 1.3
	if item.id_root == "OBJECT":
		if not bpy.context.view_layer.objects.active:
			row_asin.active = False
		op = row_asin.operator("am_list.action_assign",text="",icon="IMPORT",emboss=emboss_hlt)
		op.name = item.name
		op.duplicate = False
	else:
		try:
			rows = row.row(align=True)
			rows.enabled = False
			# rows.ui_units_x = .7
			if item.id_root == "KEY":
				rows.label(text="",icon="SHAPEKEY_DATA")
			else:
				rows.label(text="",icon=item.id_root + "_DATA")
		except:
			row_asin.label(text="",icon="BLANK1")

	# rows = row.row(align=True)
	# rows.enabled = False
	# rows.ui_units_x = .7
	# rows.prop(item,"id_root",text="")


	row.separator()

	sp = row.split(align=True,factor=1)
	sp.ui_units_x = props.action_width
	###########################################
	# 名前
	sp.prop(item,"name",text="")
	row.separator()

	if props.action_toggle_frame_range:
		rows = row.row(align=True)
		rows.alignment = "RIGHT"
		srt = str(int(item.frame_range[0])).zfill(4)
		end = str(int(item.frame_range[1])).zfill(4)
		rows.label(text="%s - %s" % (srt,end))


	###########################################
	#フェイクユーザー
	obj_on = False
	user_minus = 0
	zero_fill_text = ""
	if item.users < 10:
		zero_fill_text = "  "

	rowf = row.row(align = True)
	rowf.alignment = 'RIGHT'
	if item.use_fake_user:
		rowf.prop(item,"use_fake_user",text=zero_fill_text + str(item.users - 1 + user_minus),icon_only=True,emboss=emboss_hlt)

	elif item.users > 0:
		rowf.prop(item,"use_fake_user",text=zero_fill_text + str(item.users + user_minus),icon_only=True,emboss=emboss_hlt)
	else:
		if item.users == 0:
			rowf.alert = True
			rowf.prop(item,"use_fake_user",text=zero_fill_text + str(item.users + user_minus),icon_only=True,emboss=emboss_hlt)



	item_del = main_sp.operator("am_list.item_delete",text="" ,icon="X",emboss=emboss_hlt)
	item_del.item_name = item.name
	item_del.type = "action"
