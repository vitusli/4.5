import bpy, re
from bpy.props import *
from bpy.types import UIList

# image
class AMLIST_UL_image(UIList):
	def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
		props = bpy.context.scene.am_list

		main_col = layout.column(align=True)
		main_row = main_col.row(align=True)
		row = main_row.row(align = True)
		row.scale_x = 1.2


		if item.source == 'MOVIE':
			row.label(text="",icon="FILE_MOVIE")
		elif item.source == 'SEQUENCE':
			row.label(text="",icon="RENDERLAYERS")
		elif item.source == 'VIEWER':
			row.label(text="",icon="RESTRICT_RENDER_ON")
		elif item.source == 'GENERATED':
			row.label(text="",icon="SELECT_SET")

		else:
			row.label(text="",icon="BLANK1")


		if (item.source == 'VIEWER' or (item.source == 'GENERATED' and item.type == "RENDER_RESULT")):
			row.label(text="",icon="BLANK1")
		else:
			row.prop(item.am_list,"uidetail_toggle",text="",icon="TRIA_DOWN" if item.am_list.uidetail_toggle else "TRIA_RIGHT",emboss=False)
		###########################################
		# 名前
		row = main_row.row(align = True)
		row.scale_x = props.img_width

		row.prop(item, "name", text="", icon_value=icon)


		row = main_row.row(align = True)
		###########################################
		# パス
		if props.img_show_filepath:
			if item.source in {'VIEWER', 'GENERATED'}:
				pass
				# row.label(text="",icon="NONE")
			else:
				rows = row.row(align=True)
				rows.ui_units_x = .5
				rows.prop(props, "img_width", text="")
				row.prop(item, "filepath", text="")

		###########################################
		row = main_row.row(align = True)
		row.alignment = 'RIGHT'


		###########################################

		# サイズ
		if props.img_show_size:
			row_size = row.row(align=True)
			row_size.ui_units_x = 3.4
			row_size.alignment="RIGHT"
			if not item.source in {'VIEWER', 'GENERATED'} and item.has_data:
				row_size.label(text="" + "%d x %d" % (item.size[0], item.size[1]))
			else:
				row_size.label(text="",icon="NONE")

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



		if item.packed_file:
			row.operator("image.unpack", text="", icon='PACKAGE', emboss=False)
		else:
			row.operator("image.pack", text="", icon='UGLYPACKAGE', emboss=False)


		###########################################
		# 削除
		item_del = row.operator("am_list.item_delete",text="" ,icon="X",emboss=False)
		item_del.item_name = item.name
		item_del.type = "img"


		self.draw_uidetailed(main_col, item)


	def draw_filter(self, context, layout):
		props = context.scene.am_list
		layout.separator()
		col_main = layout.column(align=True)

		row = col_main.row(align=True)
		row.prop(props, 'img_filter', text='', icon='VIEWZOOM')
		row.prop(self, 'use_filter_invert', text='', icon='ZOOM_IN')
		row.separator()
		row.prop(props, 'img_filter_reverse', text='', icon='SORT_DESC' if props.img_filter_reverse else "SORT_ASC")


	def filter_items(self, context, data, propname):
		props = bpy.context.scene.am_list

		filtered = []
		ordered = []
		items = getattr(data, propname)
		helper_funcs = bpy.types.UI_UL_list


		# Initialize with all items visible
		filtered = [self.bitflag_filter_item] * len(items)


		# ソート反転はselfのものでなければいけないため、propsからselfに設定
		self.use_filter_sort_reverse = props.img_filter_reverse


		# 並び順を変更
		if props.img_filter_sort_type == "NAME":
			ordered = helper_funcs.sort_items_by_name(items, "name")
		elif props.img_filter_sort_type == "USERS":
			_sort = [(idx, getattr(it, "users", "")) for idx, it in enumerate(items)]
			ordered = helper_funcs.sort_items_helper(_sort, lambda e: e[1])
		elif props.img_filter_sort_type == "FILEPATH":
			_sort = [(idx, it.filepath) for idx, it in enumerate(items)]
			ordered = helper_funcs.sort_items_helper(_sort, lambda e: e[1])
		elif props.img_filter_sort_type == "SIZE":
			_sort = [(idx, it.size[0]*it.size[1]) if not it.source in {'VIEWER', 'GENERATED'} and it.has_data else (idx,(0)) for idx, it in enumerate(items)]
			ordered = helper_funcs.sort_items_helper(_sort, lambda e: e[1])



		filtered_items = self.get_props_filtered_items()


		# 検索対象以外を除去
		for i, item in enumerate(items):
			if not item in filtered_items:
				filtered[i] &= ~self.bitflag_filter_item

		return filtered,ordered



	def get_props_filtered_items(self):
		props = bpy.context.scene.am_list
		filtered_items = list(bpy.data.images)

		if props.img_hide_render_result:
			filtered_items = [o for o in filtered_items if not (o.source == 'VIEWER' or (o.source == 'GENERATED' and o.type == "RENDER_RESULT"))]
			
		# 文字検索
		if props.img_filter:
			if props.img_filter_use_regex_src:
				if props.img_filter_match_case:
					filtered_items = [o for o in filtered_items if re.findall(props.img_filter,o.name)]
				else:
					filtered_items = [o for o in filtered_items if re.findall(props.img_filter.lower(),o.name.lower())]
			else:
				if props.img_filter_match_case:
					filtered_items = [o for o in filtered_items if not o.name.find(props.img_filter) == -1]
				else:
					filtered_items = [o for o in filtered_items if not o.name.lower().find(props.img_filter.lower()) == -1]

		return filtered_items


	def draw_uidetailed(self, layout, item):
		props = bpy.context.scene.am_list

		if not item.am_list.uidetail_toggle:
			return
		if item.source == 'VIEWER' or (item.source == 'GENERATED' and item.type == "RENDER_RESULT"):
			return


		row = layout.row(align=True)
		row.label(text="",icon="BLANK1")
		row.label(text="",icon="BLANK1")
		box = row.box()
		col = box.column(align=True)
		nd_list = [("node_groups",None,nt) for nt in bpy.data.node_groups]
		nd_list = nd_list + [("mat", mat,  mat.node_tree) for mat in bpy.data.materials if mat.node_tree]
		nd_list = nd_list + [("world", wd, wd.node_tree) for wd in bpy.data.worlds if wd.node_tree]

		for type, mat, node_tree in nd_list:
			for nd in node_tree.nodes:
				if nd.type in {"TEX_IMAGE","TEX_ENVIRONMENT"}:
					if nd.image == item:
						row = col.row(align=True)
						row.alignment="LEFT"
						if type == "mat":
							mat_icon = mat.preview.icon_id
							op = row.operator("am_list.mat_select",text="" ,icon="RESTRICT_SELECT_OFF")
							op.item_name = mat.name
							op.data_type = "MATERIAL"
							op.select_image_node_name = item.name
							op = row.operator("am_list.mat_select",text=mat.name ,icon_value=mat_icon)
							op.item_name = mat.name
							op.data_type = "MATERIAL"
							op.select_image_node_name = item.name
						if type == "world":
							row.label(text="",icon="BLANK1")
							row.label(text=mat.name,icon="WORLD")
						if type == "node_groups":
							row.label(text="",icon="BLANK1")
							row.label(text=node_tree.name,icon="NODETREE")

						break
