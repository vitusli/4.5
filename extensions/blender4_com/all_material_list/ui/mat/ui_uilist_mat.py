import bpy, re
from bpy.props import *
from bpy.types import UIList

from .ui_main_mat_index import *
from .ui_main_mat_index_item import *
from .ui_main_mat_index_create_list import create_list, light_m_filter


# material
class AMLIST_UL_mat(UIList):
	def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
		col = layout.column(align=True)
		draw_panel_matindex_item(self, context, item, col, node_view_mode="", is_popup=False)

		if item.am_list.uidetail_node_toggle:
			node_draw(col, item, 'OUTPUT_MATERIAL', "Surface")
		if item.am_list.uidetail_toggle:
			no_users = (item.use_fake_user and item.users == 1)
			if item.users and not no_users:
				uidetail_for(self, context,col,item)
				col.separator()


	def draw_filter(self, context, layout):
		mat_uilist_draw_filter(self, context, layout)


	def filter_items(self, context, data, propname):
		filtered,ordered = mat_uilist_filter_items(self, context, data, propname)
		return filtered,ordered


# ポップアップとパネルメニューでの使い分けをするために同じUIリストを2つ用意
class AMLIST_UL_mat_popup(UIList):
	def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
		col = layout.column(align=True)
		draw_panel_matindex_item(self, context, item, col, node_view_mode="", is_popup=True)

		# if item.am_list.uidetail_node_toggle:
		# 	node_draw(col, item, 'OUTPUT_MATERIAL', "Surface")
		# if item.am_list.uidetail_toggle:
		# 	no_users = (item.use_fake_user and item.users == 1)
		# 	if item.users and not no_users:
		# 		uidetail_for(self, context,col,item)
		# 		col.separator()


	def draw_filter(self, context, layout):
		mat_uilist_draw_filter(self, context, layout)


	def filter_items(self, context, data, propname):
		filtered,ordered = mat_uilist_filter_items(self, context, data, propname)
		return filtered,ordered


def mat_uilist_draw_filter(self, context, layout):
# 	"""UI code for the filtering/sorting/search area."""
	props = context.scene.am_list
	layout.separator()
	col_main = layout.column(align=True)

	row = col_main.row(align=True)
	row.prop(props, 'mat_filter', text='', icon='VIEWZOOM')
	row.prop(self, 'use_filter_invert', text='', icon='ZOOM_IN')
	row.separator()
	row.prop(props, 'mat_filter_reverse', text='', icon='SORT_DESC' if props.mat_filter_reverse else "SORT_ASC")


def mat_uilist_filter_items(self, context, data, propname):
	"""Filter and order items in the list."""
	props = context.scene.am_list

	# We initialize filtered and ordered as empty lists. Notice that
	# if all sorting and filtering is disabled, we will return
	# these empty.

	filtered = []
	ordered = []
	items = getattr(data, propname)
	helper_funcs = bpy.types.UI_UL_list


	# Initialize with all items visible
	filtered = [self.bitflag_filter_item] * len(items)


	# ソート反転はselfのものでなければいけないため、propsからselfに設定
	self.use_filter_sort_reverse = props.mat_filter_reverse


	# 並び順を変更
	if props.mat_filter_sort_type == "NAME":
		ordered = helper_funcs.sort_items_by_name(items, "name")
	elif props.mat_filter_sort_type == "USERS":
		_sort = [(idx, getattr(it, "users", "")) for idx, it in enumerate(items)]
		ordered = helper_funcs.sort_items_helper(_sort, lambda e: e[1])
	elif props.mat_filter_sort_type == "PASS_INDEX":
		_sort = [(idx, getattr(it, "pass_index", "")) for idx, it in enumerate(items)]
		ordered = helper_funcs.sort_items_helper(_sort, lambda e: e[1])
	elif props.mat_filter_sort_type == "NUMBER_OF_NODES":
		_sort = [(idx,  len(it.node_tree.nodes)) if it.node_tree else (idx,  0) for idx, it in enumerate(items) ]

		ordered = helper_funcs.sort_items_helper(_sort, lambda e: e[1])


	filtered_items = get_props_filtered_items(self)

	# 検索対象以外を除去
	for i, item in enumerate(items):
		if not item in filtered_items:
			filtered[i] &= ~self.bitflag_filter_item


	return filtered,ordered


def get_props_filtered_items(self):
	props = bpy.context.scene.am_list

	filtered_items = []
	# オブジェクトリストのタイプ
	if props.mat_filter_type=="Selected":
		filtered_items =[m.material for o in bpy.context.selected_objects for m in o.material_slots if m.name != '']
	elif props.mat_filter_type=="Scene":
		filtered_items = [m.material for o in bpy.context.scene.objects for m in o.material_slots if m.name != '']
	elif props.mat_filter_type=="All_Data":
		filtered_items = [m for m in bpy.data.materials]
	elif props.mat_filter_type=="View_Layer":
		filtered_items = [m.material for o in bpy.context.view_layer.objects for m in o.material_slots if m.name != '']
	elif props.mat_filter_type=="Slot":
		filtered_items = [m.material for m in bpy.context.object.material_slots if m.name != '']

	# 文字検索
	if props.mat_filter:
		if props.mat_filter_use_regex_src:
			if props.mat_filter_match_case:
				filtered_items = [o for o in filtered_items if re.findall(props.mat_filter,o.name)]
			else:
				filtered_items = [o for o in filtered_items if re.findall(props.mat_filter.lower(),o.name.lower())]
		else:
			if props.mat_filter_match_case:
				filtered_items = [o for o in filtered_items if not o.name.find(props.mat_filter) == -1]
			else:
				filtered_items = [o for o in filtered_items if not o.name.lower().find(props.mat_filter.lower()) == -1]

	if props.mat_light_m_toggle:
		filtered_items = light_m_filter(filtered_items)

	return filtered_items
