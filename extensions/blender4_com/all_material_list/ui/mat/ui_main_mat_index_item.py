import bpy
from .ui_main_mat_mini_socket import *


# マテリアルインデックス
def draw_panel_matindex_item(self, context, item, layout,node_view_mode,is_popup):
	props = bpy.context.scene.am_list
	wm = bpy.context.scene.am_list_wm
	index = bpy.data.materials.find(item.name)
	have_users = (item.use_fake_user and item.users == 1)
	mat_icon = item.preview.icon_id

	emboss_hlt = False
	try:
		if index == bpy.data.materials.find(bpy.context.object.active_material.name):
			emboss_hlt = True
	except: pass


	###########################################
	# 選択
	icon_sel = "RESTRICT_SELECT_ON"
	emboss_hlt = False
	try:
		for sel_o in bpy.context.selected_objects:
			if sel_o.type in {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT', 'GPENCIL', 'VOLUME'}:
				if sel_o.active_material.name == item.name:
					icon_sel = "PMARKER_SEL"
					emboss_hlt = True

				if bpy.context.object:
					obj = bpy.context.object
					if obj.active_material:
						if index == bpy.data.materials.find(obj.active_material.name):
							icon_sel = "RESTRICT_SELECT_OFF"
							emboss_hlt = True
	except: pass



	#########################################################################
	# ディティールメニュー
	# split の左右のサイズを、オプションの数によって調整する
	fac = 0.8
	if is_popup == False:
		if props.mat_index_show:
			fac -= 0.1
		if props.mat_number_of_nodes_show:
			fac -= 0.1

	sp = layout.split(align=True,factor=fac)
	row = sp.row(align = True)
	row.scale_x = 1.2

	if is_popup == False:
		if props.mat_uidetail_node_toggle:
			if item.users and not have_users:
				rownode = row.row(align=True)
				rownode.prop(item.am_list,"uidetail_node_toggle",text="",icon="TRIA_DOWN" if item.am_list.uidetail_node_toggle else "TRIA_RIGHT",emboss=emboss_hlt)
			else:
				rownode = row.row(align=True)
				rownode.label(text="",icon="BLANK1")

		if props.mat_uidetail_toggle:
			if item.users and not have_users:
				rowobj = row.row(align=True)
				rowdot = rowobj.row(align=True)
				rowdot.active = False
				rowdot.scale_x = .3
				rowdot.scale_y = .3
				rowdot.label(text="",icon="DOT")

				rowobj.prop(item.am_list,"uidetail_toggle",text="",icon="TRIA_DOWN" if item.am_list.uidetail_toggle else "TRIA_RIGHT",emboss=emboss_hlt)


			else:
				rowobj = row.row(align=True)
				rowdot = rowobj.row(align=True)
				rowdot.active = False
				rowdot.scale_x = .3
				rowdot.scale_y = .3
				rowdot.label(text="",icon="BLANK1")
				rowobj.label(text="",icon="BLANK1")


	if item.users and not have_users:
		op = row.operator("am_list.mat_select",text="" ,icon=icon_sel,emboss=emboss_hlt)
		op.item_name = item.name
		op.data_type = "MATERIAL"
		op.select_image_node_name = ""

	else:
		row.label(text="",icon="BLANK1")


	###########################################
	#  割り当て
	if is_popup:
		ap_mat = row.operator("am_list.assign_material", text=item.name, icon_value=mat_icon)
		ap_mat.mat_name = item.name
		ap_mat.duplicate = False
	else:

		ap_mat = row.operator("am_list.assign_material", text="", icon="IMPORT",emboss=emboss_hlt)
		ap_mat.mat_name = item.name
		ap_mat.duplicate = False

		###########################################
		# name

		sps = row.split(align=True,factor=1)
		rowname = sps.row(align=True)
		rowname.prop(item,"name",text="",icon_value=mat_icon)


		rowname.separator()

		if node_view_mode == "emi":
			if props.mat_emi_ui_node:
				view_nml = True
				node_compact_parameter(item,row,view_nml,"PANEL")
		else:
			if props.mat_ui_node:
				view_nml = True
				node_compact_parameter(item,row,view_nml,"PANEL")

	if item.grease_pencil:
		row.label(text="",icon="OUTLINER_OB_GREASEPENCIL")



	###########################################
	row = sp.row(align = True)

	###########################################
	#フェイクユーザー
	zero_fill_text = ""
	if item.users < 10:
		zero_fill_text = "  "

	rowf = row.row(align = True)
	rowf.alignment = 'RIGHT'
	if item.use_fake_user:
		rowf.prop(item,"use_fake_user",text=zero_fill_text + str(item.users - 1),icon_only=True,emboss=emboss_hlt)

	elif item.users > 0:
		rowf.prop(item,"use_fake_user",text= zero_fill_text +str(item.users),icon_only=True,emboss=emboss_hlt)
	else:
		if item.users == 0:
			rowf.alert = True
			rowf.prop(item,"use_fake_user",text=zero_fill_text +str(item.users),icon_only=True,emboss=emboss_hlt)


	###########################################
	# パスインデックス
	if not is_popup:
		if props.mat_index_show:
			rowpi = row.row(align = True)
			rowpi.alignment = 'RIGHT'
			rowpi.prop(item,"pass_index",text="",icon="LAYER_ACTIVE",emboss=emboss_hlt)

	###########################################
	# ノード数
	if not is_popup:
		if props.mat_number_of_nodes_show:
			rowpi = row.row(align = True)
			rowpi.alignment = 'RIGHT'
			if item.node_tree:
				node_count = str(len(item.node_tree.nodes))
			else:
				node_count = "0"

			rowpi.label(text=node_count,icon="NODE")


	###########################################
	# 削除
	item_del = row.operator("am_list.item_delete",text="" ,icon="X",emboss=emboss_hlt)
	item_del.item_name = item.name
	item_del.type = "mat"
