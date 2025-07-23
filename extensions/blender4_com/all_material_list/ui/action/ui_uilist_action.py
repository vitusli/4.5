import bpy, re
from bpy.props import *
from bpy.types import UIList

from .ui_main_action_item import *
from .ui_main_action_uidetail import *


# action
class AMLIST_UL_action(UIList):
	def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
		col = layout.column(align=True)
		draw_action_item(self, context, col, item)

		if item.am_list.uidetail_toggle:
			uidetail_menu(self, context,col,item)
			col.separator()


	def draw_filter(self, context, layout):
		props = context.scene.am_list
		layout.separator()
		col_main = layout.column(align=True)

		row = col_main.row(align=True)
		row.prop(props, 'action_filter', text='', icon='VIEWZOOM')
		row.prop(self, 'use_filter_invert', text='', icon='ZOOM_IN')
		row.separator()
		row.prop(props, 'action_filter_reverse', text='', icon='SORT_DESC' if props.action_filter_reverse else "SORT_ASC")


	def filter_items(self, context, data, propname):
		props = bpy.context.scene.am_list

		filtered = []
		ordered = []
		items = getattr(data, propname)
		helper_funcs = bpy.types.UI_UL_list


		# Initialize with all items visible
		filtered = [self.bitflag_filter_item] * len(items)


		# ソート反転はselfのものでなければいけないため、propsからselfに設定
		self.use_filter_sort_reverse = props.action_filter_reverse


		# 並び順を変更
		# if props.action_filter_sort_type == "NAME":
		# 	ordered = helper_funcs.sort_items_by_name(items, "name")


		filtered_items = self.get_props_filtered_items()


		# 検索対象以外を除去
		for i, item in enumerate(items):
			if not item in filtered_items:
				filtered[i] &= ~self.bitflag_filter_item

		return filtered,ordered


	def get_props_filtered_items(self):
		props = bpy.context.scene.am_list
		filtered_items = []

		# アイテムのタイプ
		if props.action_filter_type=="Selected":
			filtered_items = [obj.animation_data.action for obj in bpy.context.selected_objects if obj.animation_data]
		elif props.action_filter_type=="Scene":
			filtered_items = [obj.animation_data.action for obj in bpy.context.scene.collection.all_objects if obj.animation_data]
		elif props.action_filter_type=="All_Data":
			filtered_items = bpy.data.actions
		elif props.action_filter_type=="View_Layer":
			filtered_items = [obj.animation_data.action for obj in bpy.context.view_layer.objects if obj.animation_data]
		elif props.action_filter_type=="Collection":
			colle = props.action_filter_colle
			if colle:
				filtered_items = [obj.animation_data.action for obj in colle.objects if obj.animation_data]
		elif props.action_filter_type=="ActiveObject":
			if bpy.context.object:
				obj = bpy.context.object
				filtered_items = [item for item in bpy.data.actions if re.match(obj.name,item.name)]

		# 文字検索
		if props.action_filter:
			if props.action_filter_use_regex_src:
				if props.action_filter_match_case:
					filtered_items = [o for o in filtered_items if re.findall(props.action_filter,o.name)]
				else:
					filtered_items = [o for o in filtered_items if re.findall(props.action_filter.lower(),o.name.lower())]
			else:
				if props.action_filter_match_case:
					filtered_items = [o for o in filtered_items if not o.name.find(props.action_filter) == -1]
				else:
					filtered_items = [o for o in filtered_items if not o.name.lower().find(props.action_filter.lower()) == -1]

		filtered_items = list(filtered_items)
		return filtered_items
