import bpy

from bpy.props import *
from bpy.types import Menu


def AMLIST_MT_clean_menu(self, context):
	layout = self.layout

	layout.separator()
	layout.separator()
	layout.separator()
	layout.operator("am_list.mat_cleanup_slot", icon="DRIVER_TRANSFORM")
	layout.operator("am_list.mat_delete_slot",icon="X")



class AMLIST_MT_other_action(Menu):
	bl_label = "Other Menu"

	def draw(self, context):
		layout = self.layout
		props = bpy.context.scene.am_list

		# layout.separator(factor=1)
		zero_del = layout.operator("am_list.del_0_mat",icon="DRIVER_TRANSFORM")
		zero_del.type = "action"
		layout.prop(props,"action_toggle_frame_range")
		layout.separator()
		layout.prop(props,"action_scroll_num")


class AMLIST_MT_other_sc_l(Menu):
	bl_label = "Other Menu"

	def draw(self, context):
		layout = self.layout
		props = bpy.context.scene.am_list

		layout.prop(props,"sc_l_uidetail_toggle")
		col = layout.column()
		if not props.sc_l_uidetail_toggle:
			col.active =False

		col.prop(props,"sc_l_uidetail_toggle_render")
		col.prop(props,"sc_l_uidetail_toggle_act")
		col.prop(props,"sc_l_filter_object")
		layout.separator()
		layout.prop(props,"sc_l_scroll_num")


class AMLIST_MT_other_img(Menu):
	bl_label = "Other Menu"

	def draw(self, context):
		layout = self.layout
		props = bpy.context.scene.am_list

		layout.separator(factor=1)
		zero_del = layout.operator("am_list.del_0_mat",icon="DRIVER_TRANSFORM")
		zero_del.type = "img"
		layout.operator("am_list.rename_image_file_name", icon="FILE_FONT")
		layout.operator("am_list.resave_all_image", icon="PACKAGE")
		layout.operator("am_list.image_move_folder_to_folder", icon="TRACKING_FORWARDS_SINGLE")
		layout.operator("file.find_missing_files",icon="VIEWZOOM")
		layout.operator("am_list.img_replace", icon="FILE_REFRESH")
		layout.operator("am_list.img_merge", icon="FULLSCREEN_EXIT")
		# layout.operator("am_list.image_change_path_abs_rel", icon="SORTSIZE")

		layout.separator(factor=1)
		layout.prop(props,"img_show_size")
		layout.prop(props,"img_show_filepath")
		if props.img_show_filepath:
			layout.prop(props,"img_width")


		layout.prop(props, "img_hide_render_result")
		layout.prop(props, "img_list_rows")

		prefs = context.preferences
		view = prefs.view
		system = prefs.system
		layout.prop(system, "use_region_overlap")


class AMLIST_MT_other_light_l(Menu):
	bl_label = "Light Menu"

	def draw(self, context):
		layout = self.layout
		props = bpy.context.scene.am_list

		# layout.prop(props,"light_l_coll_sort",icon="GROUP")
		# layout.separator(factor=1)
		layout.prop(props,"light_l_color",icon="COLOR")
		layout.prop(props,"light_l_power",icon="MOD_VERTEX_WEIGHT")
		layout.prop(props,"light_l_specular",icon="NODE_MATERIAL")
		layout.prop(props,"light_l_size",icon="EMPTY_SINGLE_ARROW")
		layout.prop(props,"light_l_other_option",icon="PRESET")
		layout.prop(props,"light_l_shadow",icon="GHOST_ENABLED")
		layout.prop(props,"light_l_ui_hide_select",icon="RESTRICT_SELECT_OFF")
		layout.prop(props,"light_l_ui_hide_viewport",icon="RESTRICT_VIEW_OFF")
		layout.separator()
		layout.prop(props,"light_l_only_hide_darken_world",icon="WORLD")
		layout.separator()
		layout.prop(props,"light_l_scroll_num")


class AMLIST_MT_other_light_p(Menu):
	bl_label = "Light Menu"

	def draw(self, context):
		layout = self.layout
		props = bpy.context.scene.am_list

		# layout.prop(props,"light_p_coll_sort",icon="GROUP")
		# layout.separator(factor=1)
		layout.prop(props,"light_p_ui_distance",icon="DRIVER_DISTANCE")
		layout.prop(props,"light_p_ui_falloff",icon="SHAPEKEY_DATA")
		layout.prop(props,"light_p_ui_intensity",icon="LIGHT_POINT")
		layout.prop(props,"light_p_ui_resolution",icon="ORIENTATION_VIEW")
		layout.prop(props,"light_p_ui_influence_type",icon="SNAP_VERTEX")
		layout.prop(props,"light_p_ui_hide_select",icon="RESTRICT_SELECT_OFF")
		layout.prop(props,"light_p_ui_hide_viewport",icon="RESTRICT_VIEW_OFF")
		layout.separator()
		layout.prop(props,"light_p_scroll_num")


class AMLIST_MT_other_cam(Menu):
	bl_label = "Light Menu"

	def draw(self, context):
		layout = self.layout
		props = bpy.context.scene.am_list

		# layout.prop(props,"cam_coll_sort",icon="GROUP")
		# layout.separator(factor=1)
		# layout.prop(props,"toggle_cam_coll_sort",icon="GROUP")
		# layout.separator(factor=1)
		layout.prop(props,"cam_ui_data_type",icon="ADD")
		layout.prop(props,"cam_ui_hide_select",icon="RESTRICT_SELECT_OFF")
		layout.prop(props,"cam_ui_hide_viewport",icon="RESTRICT_VIEW_OFF")
		layout.separator()
		layout.prop(props,"cam_scroll_num")


class AMLIST_MT_other_mat(Menu):
	bl_label = "Other Menu"

	def draw(self, context):
		layout = self.layout
		props = bpy.context.scene.am_list
		wm = bpy.context.scene.am_list_wm

		layout.separator()
		layout.separator()
		zero_del = layout.operator("am_list.del_0_mat",icon="DRIVER_TRANSFORM")
		zero_del.type = "mat"
		layout.operator("am_list.mat_rename_obj_name", icon="SORTALPHA")
		# layout.operator("am_list.mat_assign_obj_list", icon="SORTSIZE")
		layout.operator("am_list.mat_replace", icon="FILE_REFRESH")
		layout.operator("am_list.mat_merge", icon="FULLSCREEN_EXIT")
		layout.operator("am_list.mat_cleanup_slot", icon="DRIVER_TRANSFORM")
		layout.operator("am_list.mat_set_index_batch", icon="LINENUMBERS_ON")

		layout.separator(factor=1)
		layout.prop(props, "mat_uidetail_toggle")
		layout.prop(props, "mat_uidetail_toggle_act")
		layout.separator(factor=1)
		layout.prop(props, "mat_uidetail_node_toggle")
		layout.prop(props, "mat_uidetail_node_toggle_act")
		layout.separator(factor=1)
		layout.prop(props, "mat_ui_node")
		layout.prop(props, "mat_index_show")
		layout.prop(props, "mat_number_of_nodes_show")
		layout.separator(factor=1)
		layout.label(text="Display Material Type")
		layout.prop(props, "mat_display_mat_type",text="")
		layout.separator(factor=1)
		layout.prop(wm, "use_mat_ullist")
		layout.prop(props, "mat_scroll_num")
		layout.prop(props, "mat_light_m_toggle")
		layout.prop(props, "mat_filter_sort_type",text="")


class AMLIST_MT_filter_menu_mat(Menu):
	bl_label = "Filter Menu"
	def draw(self, context):
		draw_filter_other_menu(self, "mat")


class AMLIST_MT_filter_menu_img(Menu):
	bl_label = "Filter Menu"
	def draw(self, context):
		draw_filter_other_menu(self, "img")


class AMLIST_MT_filter_menu_sc_l(Menu):
	bl_label = "Filter Menu"
	def draw(self, context):
		draw_filter_other_menu(self, "sc_l")


class AMLIST_MT_filter_menu_cam(Menu):
	bl_label = "Filter Menu"
	def draw(self, context):
		draw_filter_other_menu(self, "cam")


class AMLIST_MT_filter_menu_action(Menu):
	bl_label = "Filter Menu"
	def draw(self, context):
		draw_filter_other_menu(self, "action")


class AMLIST_MT_filter_menu_light_l(Menu):
	bl_label = "Filter Menu"
	def draw(self, context):
		draw_filter_other_menu(self, "light_l")


class AMLIST_MT_filter_menu_light_p(Menu):
	bl_label = "Filter Menu"
	def draw(self, context):
		draw_filter_other_menu(self, "light_p")


def draw_filter_other_menu(self,f_type):
	layout = self.layout
	props = bpy.context.scene.am_list
	layout.prop(props, f_type + "_filter_match_case")
	layout.separator(factor=1)
	col = layout.column(align=True)
	col.active = getattr(props, f_type + "_filter_use_regex_src")
	layout.operator("am_list.first_match",icon="REW").type =f_type
	layout.operator("am_list.trailing_match",icon="FF").type =f_type
	layout.operator("am_list.dot_match",icon="DOT").type =f_type
	layout.operator("am_list.filter_exclusion",icon="REMOVE").type =f_type
