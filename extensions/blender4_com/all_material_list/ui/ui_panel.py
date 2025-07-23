import bpy
from bpy.props import *
from bpy.types import Panel

from .action.ui_main_action_root import *
from .cam.ui_main_cam_root import *
from .light_l.ui_main_light_l_root import *
from .light_p.ui_main_light_p_root import *
from .mat.ui_main_mat import *
from .mat.ui_main_mat_index import *
from .mat import ui_main_mat_index_create_list
from .mat.ui_main_mat_new import *
from .sc_l.ui_sc_l_main import *
from .ui_main import *
from .ui_main_img import *
from .ui_main_slot import *
from .ui_main_vcol import *
from .ui_main_wld import *
from .ui_menu_other import *

from .light_l.ui_uilist_light_l import AMLIST_UL_light_l
from .light_p.ui_uilist_light_p import AMLIST_UL_light_p
from .action.ui_uilist_action import AMLIST_UL_action
from .ui_uilist_img import AMLIST_UL_image
from .cam.ui_uilist_cam import AMLIST_UL_cam
from .. import __package__ as addon_id

class AMLIST_PT_view3d(Panel):
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'Mat List'
	bl_label = "All Material List"

	def draw(self, context):
		layout = self.layout
		prefs = bpy.context.preferences.addons[addon_id].preferences

		# Mat New
		draw_main_menu(self,context,False)


class AMLIST_PT_image(Panel):
	bl_space_type = 'IMAGE_EDITOR'
	bl_region_type = 'UI'
	bl_category = 'Mat List'
	bl_label = "All Material List"

	def draw_header_preset(self, context):
		layout = self.layout
		imgcount = len(bpy.data.images)

		row = layout.row(align=True)
		row.alignment="RIGHT"
		row.label(text=" : %s" % str(imgcount))
		row.separator()
		row.menu("AMLIST_MT_other_img",text="",icon="DOWNARROW_HLT")

	def draw(self, context):
		draw_panel_img_menu(self, context,is_compactmode=False)


class AMLIST_PT_property(Panel):
	bl_space_type = "PROPERTIES"
	bl_region_type = "WINDOW"
	bl_context = "material"
	bl_label = "All Material List"
	bl_options = {'DEFAULT_CLOSED'}

	def draw_header_preset(self, context):
		layout = self.layout
		row = layout.row()
		if bpy.context.object:
			slot_count = len(bpy.context.object.material_slots)
			if not len(bpy.context.object.material_slots) == 0:
				row.label(text="" + str(slot_count))
			else:
				row.label(text="0")
		else:
			row.label(text="-")


		item_count = len(bpy.data.materials)
		row.label(text=": " + str(item_count))

	def draw(self, context):
		layout = self.layout
		draw_main_menu(self,context,True)


class AMLIST_PT_slot(Panel):
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'Mat List'
	bl_label = "Slot"
	bl_parent_id = "AMLIST_PT_view3d"
	bl_options = {'DEFAULT_CLOSED'}

	def draw_header(self, context):
		layout = self.layout
		layout.label(text="",icon="SORTSIZE")


	def draw_header_preset(self, context):
		layout = self.layout
		if bpy.context.object == None or bpy.context.object.material_slots:
			sp_factor = 0.4
		else:
			sp_factor = 0.8

		sp = layout.split(factor=sp_factor,align=True)
		rows = sp.row(align=True)

		if bpy.context.object:
			if bpy.context.object.material_slots:
				if bpy.context.object.active_material:
					mat = bpy.context.object.active_material
					node_compact_parameter(mat,sp,"SLOT")


	def draw(self, context):
		draw_matslot_menu(self, context)


class AMLIST_PT_mat_index(Panel):
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'Mat List'
	bl_label = "Material"
	bl_options = {'DEFAULT_CLOSED'}

	def draw_header(self, context):
		layout = self.layout
		layout.label(text="",icon="MATERIAL")


	def draw_header_preset(self, context):
		layout = self.layout

		row = layout.row(align=True)
		row.alignment="RIGHT"
		item_count = len(bpy.data.materials)
		slot_count = len(ui_main_mat_index_create_list.create_list(True))
		if slot_count == item_count:
			slot_count = ""
		row.label(text="%s : %s" % (slot_count,item_count))
		row.menu("AMLIST_MT_other_mat", icon='DOWNARROW_HLT', text="")


	def draw(self, context):
		layout = self.layout

		draw_mat_menu_root(self, context,is_popup=False,is_compactmode=False)


class AMLIST_PT_sc_l(Panel):
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'Mat List'
	bl_label = "Scene"
	bl_options = {'DEFAULT_CLOSED'}

	def draw_header(self, context):
		layout = self.layout
		layout.label(text="",icon="SCENE_DATA")


	def draw_header_preset(self, context):
		layout = self.layout

		row = layout.row(align=True)
		row.alignment="RIGHT"
		item_count = len(bpy.data.scenes)
		row.label(text=" : " + str(item_count))
		row.separator()
		row.menu("AMLIST_MT_other_sc_l",text="",icon="DOWNARROW_HLT")


	def draw(self, context):
		wm = bpy.context.scene.am_list_wm

		draw_sc_l_menu_root(self, context,is_compactmode=False)


class AMLIST_PT_action(Panel):
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'Mat List'
	bl_label = "Action"
	bl_options = {'DEFAULT_CLOSED'}

	def draw_header(self, context):
		layout = self.layout
		layout.label(text="",icon="ACTION")

	def draw_header_preset(self, context):
		draw_header_preset_template(self,context,
			bpy.data.actions,
			AMLIST_UL_action.get_props_filtered_items(None),
			bpy.context.scene.am_list.action_filter,
			"AMLIST_MT_other_action",
			)


	def draw(self, context):
		draw_action_menu_root(self, context, is_compactmode=False, editor_type="3dview")


class AMLIST_PT_action_dopesheet(Panel):
	bl_space_type = 'DOPESHEET_EDITOR'
	bl_region_type = 'UI'
	bl_category = 'Mat List'
	bl_label = "Action"
	bl_options = {'DEFAULT_CLOSED'}

	def draw_header(self, context):
		layout = self.layout
		layout.label(text="",icon="ACTION")

	def draw_header_preset(self, context):
		draw_header_preset_template(self,context,
			bpy.data.actions,
			AMLIST_UL_action.get_props_filtered_items(None),
			bpy.context.scene.am_list.action_filter,
			"AMLIST_MT_other_action",
			)

	def draw(self, context):
		draw_action_menu_root(self, context, is_compactmode=False, editor_type="dopesheet")


class AMLIST_PT_action_graph(Panel):
	bl_space_type = 'GRAPH_EDITOR'
	bl_region_type = 'UI'
	bl_category = 'Mat List'
	bl_label = "Action"
	bl_options = {'DEFAULT_CLOSED'}

	def draw_header(self, context):
		layout = self.layout
		layout.label(text="",icon="ACTION")

	def draw_header_preset(self, context):
		draw_header_preset_template(self,context,
			bpy.data.actions,
			AMLIST_UL_action.get_props_filtered_items(None),
			bpy.context.scene.am_list.action_filter,
			"AMLIST_MT_other_action",
			)

	def draw(self, context):
		draw_action_menu_root(self, context, is_compactmode=False, editor_type="graph")


class AMLIST_PT_vcol(Panel):
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'Mat List'
	bl_label = "Viewport Color"
	bl_options = {'DEFAULT_CLOSED'}

	def draw_header(self, context):
		layout = self.layout
		layout.label(text="",icon="COLOR")


	def draw(self, context):
		draw_panel_vcol_menu(self, context,is_compactmode=False)


class AMLIST_PT_light_l(Panel):
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'Mat List'
	bl_label = "Light"
	bl_options = {'DEFAULT_CLOSED'}

	def draw_header(self, context):
		layout = self.layout
		layout.label(text="",icon="LIGHT")

	def draw_header_preset(self, context):
		draw_header_preset_template(self,context,
			[o for o in bpy.data.objects if o.type =='LIGHT'],
			AMLIST_UL_light_l.get_props_filtered_items(None),
			bpy.context.scene.am_list.light_l_filter,
			"AMLIST_MT_other_light_l",
			)

	def draw(self, context):
		draw_light_l_menu_root(self, context,is_compactmode=False)



class AMLIST_PT_light_p(Panel):
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'Mat List'
	bl_label = "Light Probe"
	bl_options = {'DEFAULT_CLOSED'}

	def draw_header(self, context):
		layout = self.layout
		layout.label(text="",icon="OUTLINER_OB_LIGHTPROBE")

	def draw_header_preset(self, context):
		draw_header_preset_template(self,context,
			[o for o in bpy.data.objects if o.type =='LIGHT_PROBE'],
			AMLIST_UL_light_p.get_props_filtered_items(None),
			bpy.context.scene.am_list.light_p_filter,
			"AMLIST_MT_other_light_p",
			)

	def draw(self, context):
		draw_light_p_menu_root(self, context,is_compactmode=False)


class AMLIST_PT_cam(Panel):
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'Mat List'
	bl_label = "Camera"
	bl_options = {'DEFAULT_CLOSED'}

	def draw_header(self, context):
		layout = self.layout
		layout.label(text="",icon="CAMERA_DATA")

	def draw_header_preset(self, context):
		draw_header_preset_template(self,context,
			[o for o in bpy.data.objects if o.type =='CAMERA'],
			AMLIST_UL_cam.get_props_filtered_items(None),
			bpy.context.scene.am_list.cam_filter,
			"AMLIST_MT_other_cam",
			)

	def draw(self, context):
		draw_cam_menu_root(self, context,is_compactmode=False)


class AMLIST_PT_wld(Panel):
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'Mat List'
	bl_label = "World"
	bl_options = {'DEFAULT_CLOSED'}

	def draw_header(self, context):
		layout = self.layout
		layout.label(text="",icon="WORLD")

	def draw_header_preset(self, context):
		layout = self.layout
		wldcount = len(bpy.data.worlds)

		row = layout.row(align=True)
		row.label(text="   : " + str(wldcount))
		row.separator()
		row.operator("world.new",text="",icon="ADD",emboss=False)

	def draw(self, context):
		draw_panel_wld_menu(self, context,is_compactmode=False)


class AMLIST_PT_img(Panel):
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'Mat List'
	bl_label = "Image"
	bl_options = {'DEFAULT_CLOSED'}

	def draw_header(self, context):
		layout = self.layout
		layout.label(text="",icon="IMAGE")

	def draw_header_preset(self, context):
		draw_header_preset_template(self,context,
			bpy.data.images,
			AMLIST_UL_image.get_props_filtered_items(None),
			bpy.context.scene.am_list.img_filter,
			"AMLIST_MT_other_img",
			)

	def draw(self, context):
		draw_panel_img_menu(self, context,is_compactmode=False)



def draw_header_preset_template(self, context, all_data_list, filter_list, filter_prop, menu_class):
	layout = self.layout
	if filter_prop:
		filter_count = len(list(filter_list))
	else:
		filter_count = ""

	row = layout.row(align=True)
	row.alignment="RIGHT"
	row.label(text="%s : %s" % (filter_count, len(all_data_list)))
	row.separator()
	row.menu(menu_class, icon='DOWNARROW_HLT', text="")
