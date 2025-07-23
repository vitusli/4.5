import bpy, re
from bpy.props import *
from bpy.types import UIList

from .ui_main_light_l_item import *
from .ui_main_light_l_uidetail import *


# light_l
class AMLIST_UL_light_l(UIList):
	def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
		col = layout.column(align=True)
		draw_light_l_item(self, context, col, item, is_compactmode_top=False)

		if item.am_list.uidetail_toggle:
			uidetail_menu(self, context,col,item)
			col.separator()


	def draw_filter(self, context, layout):
		props = context.scene.am_list
		layout.separator()
		col_main = layout.column(align=True)

		row = col_main.row(align=True)
		row.prop(props, 'light_l_filter', text='', icon='VIEWZOOM')
		row.prop(self, 'use_filter_invert', text='', icon='ZOOM_IN')
		row.separator()
		row.prop(props, 'light_l_filter_reverse', text='', icon='SORT_DESC' if props.light_l_filter_reverse else "SORT_ASC")


	def filter_items(self, context, data, propname):
		props = bpy.context.scene.am_list

		filtered = []
		ordered = []
		items = getattr(data, propname)
		helper_funcs = bpy.types.UI_UL_list


		# Initialize with all items visible
		filtered = [self.bitflag_filter_item] * len(items)


		# ソート反転はselfのものでなければいけないため、propsからselfに設定
		self.use_filter_sort_reverse = props.light_l_filter_reverse


		# 並び順を変更
		if props.light_l_filter_sort_type == "NAME":
			ordered = helper_funcs.sort_items_by_name(items, "name")
		if props.light_l_filter_sort_type == "TYPE":
			light_type_dic= { 'POINT':0, 'SUN':1, 'SPOT':2, 'AREA':3, }
			_sort = [(idx, light_type_dic[it.data.type]) if it.type=='LIGHT' else (idx,  0)  for idx, it in enumerate(items)]
			ordered = helper_funcs.sort_items_helper(_sort, lambda e: e[1])
		elif props.light_l_filter_sort_type == "ENERGY":
			_sort = [(idx, it.data.energy) if it.type=='LIGHT' else (idx,  0)  for idx, it in enumerate(items)]
			ordered = helper_funcs.sort_items_helper(_sort, lambda e: e[1])
		elif props.light_l_filter_sort_type == "DIFFUSE_FACTOR":
			_sort = [(idx, it.data.diffuse_factor) if it.type=='LIGHT' else (idx,  0)  for idx, it in enumerate(items)]
			ordered = helper_funcs.sort_items_helper(_sort, lambda e: e[1])
		elif props.light_l_filter_sort_type == "SPECULAR_FACTOR":
			_sort = [(idx, it.data.specular_factor) if it.type=='LIGHT' else (idx,  0)  for idx, it in enumerate(items)]
			ordered = helper_funcs.sort_items_helper(_sort, lambda e: e[1])
		elif props.light_l_filter_sort_type == "VOLUME_FACTOR":
			_sort = [(idx, it.data.volume_factor) if it.type=='LIGHT' else (idx,  0)  for idx, it in enumerate(items)]
			ordered = helper_funcs.sort_items_helper(_sort, lambda e: e[1])
		elif props.light_l_filter_sort_type == "ANGLE":
			_sort = [(idx, it.data.angle) if it.type=='LIGHT' and it.type == "SUN" else (idx,  0)  for idx, it in enumerate(items)]
			ordered = helper_funcs.sort_items_helper(_sort, lambda e: e[1])



		filtered_items = self.get_props_filtered_items()


		# 検索対象以外を除去
		for i, item in enumerate(items):
			if not item in filtered_items:
				filtered[i] &= ~self.bitflag_filter_item

		return filtered,ordered


	def get_props_filtered_items(self):
		props = bpy.context.scene.am_list
		filtered_items = []
		# オブジェクトリストのタイプ
		if props.light_l_filter_type=="Selected":
			filtered_items =[o for o in bpy.context.selected_objects if o.type=='LIGHT']
		elif props.light_l_filter_type=="Scene":
			filtered_items = [o for o in bpy.context.scene.objects if o.type=='LIGHT']
		elif props.light_l_filter_type=="All_Data":
			filtered_items = [o for o in bpy.data.objects if o.type == 'LIGHT']
		elif props.light_l_filter_type=="Collection":
			colle = props.light_l_filter_colle
			if colle:
				filtered_items = [o for o in colle.objects if o.type == 'LIGHT']
		elif props.light_l_filter_type=="View_Layer":
			filtered_items = [o for o in bpy.context.view_layer.objects if o.type=='LIGHT']


		# 文字検索
		if props.light_l_filter:
			if props.light_l_filter_use_regex_src:
				if props.light_l_filter_match_case:
					filtered_items = [o for o in filtered_items if re.findall(props.light_l_filter,o.name)]
				else:
					filtered_items = [o for o in filtered_items if re.findall(props.light_l_filter.lower(),o.name.lower())]
			else:
				if props.light_l_filter_match_case:
					filtered_items = [o for o in filtered_items if not o.name.find(props.light_l_filter) == -1]
				else:
					filtered_items = [o for o in filtered_items if not o.name.lower().find(props.light_l_filter.lower()) == -1]

		return filtered_items
