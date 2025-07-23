import bpy

from .ui_main_mat_index_create_list import *
from .ui_main_mat_index_uidetail import *
from .ui_main_mat_index_item import *
from .ui_panel_node_draw import *
from .ui_main_mat import *
from ... import __package__ as addon_id

# マテリアルインデックス
def draw_mat_menu_root(self, context, is_popup, is_compactmode):
	layout = self.layout
	prefs = bpy.context.preferences.addons[addon_id].preferences
	props = context.scene.am_list
	wm = bpy.context.scene.am_list_wm


	if not prefs.usepanel_mat_index or is_compactmode:
		sp = layout.split(align=True,factor=0.7)
		rows = sp.row(align=True)
		rows.alignment = 'LEFT'
		rows.prop(wm, "toggle_mat_index",text="",icon="TRIA_DOWN" if wm.toggle_mat_index else "TRIA_RIGHT", emboss=False)
		rows.prop(wm, "toggle_mat_index",icon="MATERIAL",emboss=False)

		row = sp.row(align=True)
		row.alignment = 'RIGHT'
		matcount = len(bpy.data.materials)
		slot_count = "0"
		if bpy.context.object and bpy.context.object.material_slots:
			slot_count = str(len(bpy.context.object.material_slots))

		row.label(text=slot_count + " : " + str(matcount))
		row.label(text="",icon="BLANK1")
		row.menu("AMLIST_MT_other_mat", icon='DOWNARROW_HLT', text="")


	open_bool = wm.toggle_mat_index
	if prefs.usepanel_mat_index:
		if is_compactmode:
			open_bool = wm.toggle_mat_index
		else:
			open_bool = True
	if open_bool:
		if wm.use_mat_ullist:
			list_option_menu(self, context, layout, is_popup, False, None)
			draw_mat_uilist_layout(self, context, is_compactmode=False, is_popup = is_popup)

		else:
			draw_mat_iteration_list(self, context,is_popup = is_popup)


# 自作のfor文リスト
def draw_mat_iteration_list(self, context, is_popup):
	layout = self.layout
	props = context.scene.am_list
	wm = bpy.context.scene.am_list_wm

	# リストの作成
	l_items = create_list(True)
	if is_popup:
		if bpy.context.object:
			obj = bpy.context.object
			if obj.type == "GPENCIL":
				l_items = [i for i in l_items if i.grease_pencil]
			else:
				l_items = [i for i in l_items if not i.grease_pencil]

	# スクロール
	list_count = len(l_items)
	scroll_num = props.mat_scroll
	current_num = props.mat_scroll_num
	s_min = scroll_num
	s_max = scroll_num + current_num
	if list_count > current_num:
		if scroll_num > (list_count - current_num):
			s_min = list_count - current_num
			s_max = list_count

	l_items = l_items[s_min:s_max]



	##################################
	# menu
	list_option_menu(self,context,layout,is_popup,True,list_count)

	box = layout.box()
	box = box.column(align=True)
	box.scale_y = 1.1

	if l_items:
		for item in l_items:
			if props.mat_display_mat_type == "DEFULT_MAT":
				if item.grease_pencil:
					continue
			elif props.mat_display_mat_type == "GREASE_PENCIL":
				if not item.grease_pencil:
					continue

			draw_panel_matindex_item(self, context, item, box,node_view_mode="", is_popup=is_popup)

			if not is_popup:
				if item.am_list.uidetail_node_toggle:
					node_draw(box, item, 'OUTPUT_MATERIAL', "Surface")

				if item.am_list.uidetail_toggle:
					no_users = (item.use_fake_user and item.users == 1)
					if item.users and not no_users:
						uidetail_for(self, context,box,item)
						box.separator()


	else:
		box.active=False
		box.label(text="No Material",icon="NONE")

	if list_count > props.mat_scroll_num:
		row = box.row(align=True)
		box = row.box()
		box = box.row(align=True)
		box.label(text="",icon="UV_SYNC_SELECT")
		if list_count <= props.mat_scroll:
			rows = box.row(align=True)
			rows.alert=True
			rows.prop(props, "mat_scroll",text="",emboss=False)
		else:
			box.prop(props, "mat_scroll",text="",emboss=False)


		rows = row.row(align=True)
		rows.scale_x=0.7
		rows.prop(props, "mat_scroll_num",text="",emboss=False)
		row.label(text="/ "+str(list_count))


	if not is_popup:
		if props.mat_uidetail_node_toggle_act:
			obj = bpy.context.object
			node_draw(layout, obj.active_material, 'OUTPUT_MATERIAL', "Surface")

		if props.mat_uidetail_toggle_act:
			asobj_act(self, context)


# リスト上のオプションメニュー
def list_option_menu(self, context, layout, is_popup, is_iteration_list, list_count):

	props = context.scene.am_list
	box_main = layout.box()
	col_main = box_main.column(align=True)
	rows = col_main.row(align=True)
	rows.prop(props,"mat_filter_type",text="",expand=True)

	if not is_popup:
		rows.separator()
		rows.prop(props, "mat_uidetail_node_toggle_act",text="",icon="NODETREE")
		rows.prop(props, "mat_uidetail_node_toggle",text="",icon="STICKY_UVS_DISABLE")
		rows.separator()

		if props.mat_uidetail_node_toggle:
			uidetail = rows.operator("am_list.uidetail_toggle_all",text="" ,icon="FULLSCREEN_ENTER")
			uidetail.type="mat"

			rows.separator()

		rows.prop(props, "mat_uidetail_toggle_act",text="",icon="OBJECT_DATA")
		rows.prop(props, "mat_uidetail_toggle",text="",icon="STICKY_UVS_DISABLE")
		rows.separator()

		if props.mat_uidetail_toggle:
			uidetail = rows.operator("am_list.uidetail_toggle_all",text="" ,icon="FULLSCREEN_ENTER")
			uidetail.type="mat_assigned_obj"


		if props.mat_uidetail_toggle_act or props.mat_uidetail_toggle:
			rows.prop(props,"mat_uidetail_nameedit",text="" ,icon="SORTALPHA")

	if is_popup:
		rowss = rows.row(align=True)
		rowss.alignment="RIGHT"
		rowss.menu("AMLIST_MT_other_mat", icon='DOWNARROW_HLT', text="")



	if is_iteration_list:
		box = rows.box()
		box = box.row(align=True)
		box.label(text="",icon="UV_SYNC_SELECT")
		box.scale_x = .6
		box.alignment="RIGHT"
		if list_count <= props.mat_scroll:
			rowss = box.row(align=True)
			rowss.alert=True
			rowss.prop(props, "mat_scroll",text="",emboss=False)
		else:
			box.prop(props, "mat_scroll",text="",emboss=False)


		box.separator(factor=2)
		rows = box.row(align=True)
		rows.scale_x=0.7
		rows.prop(props, "mat_scroll_num",text="",emboss=False)
		box.label(text="/   "+str(list_count))

	col_main.separator()
	row = col_main.row(align = True)
	row.prop(props,"mat_filter",text="",icon="VIEWZOOM")
	row.prop(props, "mat_filter_use_regex_src",text="", icon='SORTBYEXT')
	row.menu("AMLIST_MT_filter_menu_mat", icon='DOWNARROW_HLT', text="")
	row.separator()
	rows = row.row(align=True)
	rows.scale_x = .4
	rows.prop(props, "mat_filter_sort_type",text="")
	row.prop(props, "mat_filter_reverse",text="", icon='SORT_DESC' if props.mat_filter_reverse else "SORT_ASC")
