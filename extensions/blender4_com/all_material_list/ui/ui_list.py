import bpy, re
from bpy.props import *
from bpy.types import UIList

from .sc_l.ui_sc_l_main import *
from .sc_l.ui_sc_l_uidetail import draw_sc_l_uidetail
from .sc_l.ui_sc_l_item import draw_sc_l_item


# view layer
class AMLIST_UL_viewlayers(UIList):
	def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
		sc = item.id_data
		layout.use_property_decorate = False
		row = layout.row(align=True)
		if not item.use:
			active=False
		emboss_hlt = False

		if sc.name == bpy.context.scene.name:
			try:
				if bpy.context.window.view_layer.name == item.name:
					emboss_hlt = True
			except: pass

			rows = row.row(align=True)
			rows.scale_x = 1.2
			set = rows.operator("am_list.viewlayer_set",text="",icon="RENDERLAYERS",emboss=emboss_hlt)
			set.name= item.name
		else:
			row.label(text="",icon="RENDERLAYERS")


		row.prop(item, "name", text="", icon="NONE")
		row.prop(item, "use", text="")


		ren = row.operator("render.render", text="",icon="RENDER_STILL")
		ren.scene=sc.name
		ren.layer=item.name

		op = row.operator("am_list.viewlayer_remove", text="",icon="X",emboss=False)
		op.scene_name = sc.name
		op.viewlayer_name = item.name


# world
class AMLIST_UL_world(UIList):
	def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
		props = bpy.context.scene.am_list


		row = layout.row(align = True)
		row.scale_x = 1.2

		###########################################
		row.label(text="",icon="BLANK1")

		###########################################
		# アサイン
		row.operator("am_list.world_assign",text="" ,icon="ADD",emboss=False).mat_id_name=index

		###########################################
		# 名前
		row.prop(item, "name", text="", icon_value=icon)



		###########################################
		row = layout.row(align = True)
		row.alignment = 'RIGHT'
		###########################################
		#フェイクユーザー
		zero_fill_text = ""
		if item.users < 10:
			zero_fill_text = "  "

		rowf = row.row(align = True)
		rowf.alignment = 'RIGHT'
		if item.use_fake_user:
			rowf.prop(item,"use_fake_user",text=zero_fill_text +  str(item.users - 1),icon_only=True,emboss=False)

		elif item.users > 0:
			rowf.prop(item,"use_fake_user",text=zero_fill_text +  str(item.users),icon_only=True,emboss=False)
		else:
			if item.users == 0:
				rowf.alert = True
				rowf.prop(item,"use_fake_user",text=zero_fill_text +  str(item.users),icon_only=True,emboss=False)


		# 削除
		item_del = row.operator("am_list.item_delete",text="" ,icon="X",emboss=False)
		item_del.item_name = item.name
		item_del.type = "wld"


# scene
class AMLIST_UL_sc_l(UIList):
	def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):

		col = layout.column(align=True)
		draw_sc_l_item(self, context,col, item)

		if item.am_list.uidetail_toggle:
			draw_sc_l_uidetail(self, context, col, item)


	def draw_filter(self, context, layout):
		props = context.scene.am_list
		layout.separator()
		col_main = layout.column(align=True)

		row = col_main.row(align=True)
		row.prop(props, 'sc_l_filter', text='', icon='VIEWZOOM')
		row.prop(self, 'use_filter_invert', text='', icon='ZOOM_IN')
		row.separator()
		row.prop(props, 'sc_l_filter_reverse', text='', icon='SORT_DESC' if props.sc_l_filter_reverse else "SORT_ASC")


	def filter_items(self, context, data, propname):
		props = context.scene.am_list

		filtered = []
		ordered = []
		items = getattr(data, propname)
		helper_funcs = bpy.types.UI_UL_list


		# Initialize with all items visible
		filtered = [self.bitflag_filter_item] * len(items)


		# ソート反転はselfのものでなければいけないため、propsからselfに設定
		self.use_filter_sort_reverse = props.sc_l_filter_reverse


		# 並び順を変更
		if props.sc_l_filter_sort_type == "NAME":
			ordered = helper_funcs.sort_items_by_name(items, "name")
		elif props.sc_l_filter_sort_type == "OBJECT":
			_sort = [(idx, len(it.objects)) for idx, it in enumerate(items)]
			ordered = helper_funcs.sort_items_helper(_sort, lambda e: e[1])
		elif props.sc_l_filter_sort_type == "PASS_INDEX":
			_sort = [(idx, len(it.view_layers)) for idx, it in enumerate(items)]
			ordered = helper_funcs.sort_items_helper(_sort, lambda e: e[1])


		filter_type = list(bpy.data.scenes)

		# 文字検索
		if props.sc_l_filter:
			if props.sc_l_filter_use_regex_src:
				if props.sc_l_filter_match_case:
					filter_type = [o for o in filter_type if re.findall(props.sc_l_filter,o.name)]
				else:
					filter_type = [o for o in filter_type if re.findall(props.sc_l_filter.lower(),o.name.lower())]
			else:
				if props.sc_l_filter_match_case:
					filter_type = [o for o in filter_type if not o.name.find(props.sc_l_filter) == -1]
				else:
					filter_type = [o for o in filter_type if not o.name.lower().find(props.sc_l_filter.lower()) == -1]


		# 検索対象以外を除去
		for i, item in enumerate(items):
			if not item in filter_type:
				filtered[i] &= ~self.bitflag_filter_item

		return filtered, ordered
