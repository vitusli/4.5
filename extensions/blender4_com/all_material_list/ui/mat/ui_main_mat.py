import bpy
from bpy.props import *
from .ui_panel_node_draw import *
from .ui_main_mat_index_uidetail import *
from ... import __package__ as addon_id
def draw_mat_uilist_layout(self, context, is_compactmode, is_popup):
	layout = self.layout
	prefs = bpy.context.preferences.addons[addon_id].preferences
	props = context.scene.am_list
	wm = bpy.context.scene.am_list_wm


	all_data_l = [o for o in bpy.data.materials]
	if len(all_data_l) >= props.mat_scroll_num:
		l_height = props.mat_scroll_num
	elif len(all_data_l) <= 3:
		l_height = 3
	else:
		l_height = len(all_data_l)


	if is_popup:
		layout.template_list(
		"AMLIST_UL_mat_popup","",
		bpy.data, "materials",
		props, "id_mat",
		rows = l_height
		)
	else:
		layout.template_list(
			"AMLIST_UL_mat","",
			bpy.data, "materials",
			props, "id_mat",
			rows = l_height
		)


		if props.mat_uidetail_node_toggle_act:
			if bpy.context.object:
				obj = bpy.context.object
				if obj.type in {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT', 'VOLUME'}:
					if obj.active_material:
							node_draw(layout, obj.active_material, 'OUTPUT_MATERIAL', "Surface")


	if props.mat_uidetail_toggle_act:
		asobj_act(self, context)
