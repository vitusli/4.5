import bpy
from bpy.types import Operator
from bpy.props import *
import re
from .ui_main import *
from .mat.ui_main_mat_mini_socket import *
from .action.ui_main_action_root import draw_action_menu_root
from .light_l.ui_main_light_l_item import draw_light_l_item
from .light_l.ui_main_light_l_root import draw_light_l_menu_root
from .cam.ui_main_cam_root import draw_cam_menu_root
from .light_l import ui_main_light_l_uidetail
from .. import __package__ as addon_id

class AMLIST_OT_Popup(Operator):
	bl_idname = "am_list.popup"
	bl_label = "All Material List"
	bl_description = ""
	bl_options = {'REGISTER','UNDO'}

	def invoke(self, context, event):
		prefs = bpy.context.preferences.addons[addon_id].preferences
		return context.window_manager.invoke_props_dialog(self, width=prefs.popup_menu_width)

	def draw(self, context):
		draw_panel_popup_menu(self,context)


	def execute(self, context):
		return {'FINISHED'}


def draw_panel_popup_menu(self,context):
	layout = self.layout
	props = bpy.context.scene.am_list

	layout.prop(props,"tab_popup", expand=True)

	if props.tab_popup == "COMPACT":
		if bpy.context.object:
			obj = bpy.context.object

			if obj.type == "ARMATURE":
				draw_action_menu_root(self, context,False,"3dview")
				return

			elif obj.type == "LIGHT":
				draw_menu_light(self,context,layout,obj)
				return

			elif obj.type == "CAMERA":
				draw_menu_camera(self,context,layout,obj)
				return

			elif obj.type == "EMPTY":
				draw_menu_empty(self,context,layout,obj)
				return

			# elif obj.type == "CURVE":
			# 	layout.prop(obj.data,"bevel_depth")
			# 	layout.prop(obj.data,"resolution_u")

			# elif obj.type == "FONT":
			# elif obj.mode == "POSE":
			# elif obj.mode == "SCULPT":
			# elif obj.mode == "PAINT_GPENCIL":


		layout.separator()
		draw_add_materiarl(self,context,layout)


		if len(bpy.context.object.data.materials):
			mat = bpy.context.object.active_material
			col = layout.column(align=True)
			col.scale_y = 1.2

			view_nml = False
			node_compact_parameter(mat,col,view_nml,"POPUP")

		else:
			layout.label(text="No material assigned",icon="NONE")

		if not len(bpy.context.object.data.materials) > 1:
			layout.separator()
		draw_mat_menu_root(self, context,is_popup=True,is_compactmode=False)


		if bpy.context.object:
			if obj.type == "CURVE":
				obj = bpy.context.object
				layout.separator()
				layout.prop(obj.data,"bevel_depth")
				layout.prop(obj.data,"bevel_resolution")
				layout.prop(obj.data,"resolution_u")

	else:
		draw_main_menu(self,context,True)


def draw_add_materiarl(self,context,layout):

	# マテリアル追加
	row = layout.row(align = True)
	row.scale_y = 1.2

	row.operator("am_list.mat_new_create_one_mat",text="Assign",icon="IMPORT")
	row.operator("am_list.mat_new_create_not_assign",text="",icon="ADD")
	row.operator("am_list.mat_new_create_multi_mat",text="",icon="ZOOM_IN").random_color = False
	row.operator("am_list.mat_new_create_multi_mat",text="",icon="PLUS").random_color = True
	row.separator()
	row.operator("am_list.mat_copy_material_slot",text="",icon="COPYDOWN")
	row.separator()
	row.operator("am_list.mat_delete_slot",text="",icon="X")


def draw_menu_empty(self,context,layout,item):
	layout.prop(item, "empty_display_type", text="Display As")
	layout.prop(item, "empty_display_size", text="Size")
	if item.empty_display_type == 'IMAGE':

		col = layout.column()
		col.prop(item, "use_empty_image_alpha")
		cols = col.column()
		cols.active = item.use_empty_image_alpha
		cols.prop(item, "color", text="Transparency", index=3, slider=True)
		# layout.separator()
		# layout.template_ID(obj, "data", open="image.open", unlink="object.unlink_data")


def draw_menu_camera(self,context,layout,item):
	cam = item.data


	row = layout.row(align=True)
	row_lock = row.row(align=True)
	row_lock.alignment="RIGHT"
	row_lock.scale_x = 1.5
	row_lock.prop(bpy.context.space_data,"lock_camera",text="",icon="LOCKED")
	row.separator()
	row.prop(cam, "lens",icon="CAMERA_DATA")

	row = layout.row(align=True)
	row.prop(cam, "show_passepartout")
	col = row.column(align=True)
	col.use_property_split = True
	col.active = cam.show_passepartout
	col.prop(cam, "passepartout_alpha", text="Opacity", slider=True)
	row = layout.row(align=True)
	if cam.background_images:
		row.prop(cam.background_images[0], "show_background_image")
		rows = row.row(align=True)
		rows.active = cam.background_images[0].show_background_image
		rows.prop(cam.background_images[0], "alpha", slider=True)


def draw_menu_light(self,context,layout,item):
	props = bpy.context.scene.am_list
	draw_light_l_item(self, context,layout, item,True)
	item_data = item.data
	emboss_hlt = True
	row = layout


	rows = row.row(align=True)
	rows.scale_x = .5

	if props.light_l_color:
		rowcollor = rows.row()
		rowcollor.scale_x = .4
		rowcollor.prop(item_data, "color",text="")

	if props.light_l_power:
		rows.prop(item_data, "energy",text="",emboss=emboss_hlt)
		row_en = rows.row(align=True)
		# col = rows.column(align=True)
		row_en.scale_x=2
		# col.scale_y=0.5
		et = row_en.operator("am_list.energy_twice",text="",icon="SORT_ASC")
		et.twice = False
		et.item_name = item.name
		et = row_en.operator("am_list.energy_twice",text="",icon="SORT_DESC")
		et.twice = True
		et.item_name = item.name

	if props.light_l_specular:
		rows.prop(item_data, "specular_factor", text="",emboss=emboss_hlt)


	if props.light_l_size:
		if item_data.type in {'POINT'}:
			rows.prop(item_data, "shadow_soft_size", text="",emboss=emboss_hlt)
			if props.light_l_other_option:
				rows.label(text="",icon="NONE")
				rows.label(text="",icon="NONE")

		if item_data.type in {'SPOT'}:
			rows.prop(item_data, "shadow_soft_size", text="",emboss=emboss_hlt)
			if props.light_l_other_option:
				rows.prop(item_data, "spot_size", text="",emboss=emboss_hlt)
				rows.prop(item_data, "spot_blend", text="", slider=True,emboss=emboss_hlt)
			# row.prop(item_data, "show_cone")

		elif item_data.type == 'SUN':
			rows.prop(item_data, "angle",emboss=emboss_hlt)
			if props.light_l_other_option:
				rows.label(text="",icon="NONE")
				rows.label(text="",icon="NONE")

		elif item_data.type == 'AREA':

			if item_data.shape in {'SQUARE', 'DISK'}:
				rows.prop(item_data, "size")
				if props.light_l_other_option:
					rows.label(text="",icon="NONE")
			elif item_data.shape in {'RECTANGLE', 'ELLIPSE'}:
				if props.light_l_other_option:
					rows.prop(item_data, "size", text="Size X",emboss=emboss_hlt)
					rows.prop(item_data, "size_y", text="Y",emboss=emboss_hlt)
				else:
					rows.label(text="",icon="NONE")


			if props.light_l_other_option:
				rows.prop(item_data, "shape",text="",emboss=emboss_hlt)

	if props.light_l_shadow:
		if item_data.use_shadow:
			row.prop(item_data, "use_shadow", text="",icon="GHOST_ENABLED",emboss=emboss_hlt)
		else:
			row.prop(item_data, "use_shadow", text="",icon="GHOST_DISABLED",emboss=emboss_hlt)



	if item.am_list.uidetail_toggle:
		ui_main_light_l_uidetail.uidetail_menu(self, context,layout,item)

	layout.separator()

	draw_light_l_menu_root(self, context,False)
