import bpy
from bpy.props import *


def draw_matnew_menu(self, context,is_compactmode):
	layout = self.layout
	props = bpy.context.scene.am_list

	###########################################
	# New Mat
	row = layout.row(align=True)
	split = row.split(factor=.1,align=True)

	if  len (context.selected_objects ) == 0 or bpy.context.view_layer.objects.active == None:
		split.label(text="",icon="NONE")
	else:
		if bpy.context.active_object.mode == "EDIT":

			mode = bpy.context.tool_settings.mesh_select_mode[:]
			if (mode[2]):
				simi = split.operator("mesh.select_similar",text="",icon="RESTRICT_SELECT_ON")
				if bpy.app.version >= (4,0,0):
					simi.type='FACE_MATERIAL'
				else:
					simi.type='MATERIAL'
			else:
				cols = split.column(align=True)
				cols.enabled = False
				simi = cols.operator("mesh.select_similar",text="",icon="RESTRICT_SELECT_ON")


		else:
			if bpy.context.active_object.active_material is not None:
				linked = split.operator("object.select_linked",text="",icon="RESTRICT_SELECT_ON")
				linked.type='MATERIAL'
			else:
				split.label(text="",icon="VIS_SEL_00")

	split_z = split.split(factor=.1,align=True)
	split_z.prop(props, "new_mat_color",text="",icon="BLANK1")

	split_z.operator("am_list.mat_new_create_one_mat",text="Assign",icon="IMPORT")

	split_z = split_z.row(align=True)
	split_z.scale_x = 1.5
	split_z.operator("am_list.mat_new_create_not_assign",text="",icon="ADD")
	split_z.operator("am_list.mat_new_create_multi_mat",text="",icon="ZOOM_IN").random_color = False
	split_z.operator("am_list.mat_new_create_multi_mat",text="",icon="PLUS").random_color = True
	split_z.separator()
	split_z.operator("am_list.mat_copy_material_slot",text="",icon="COPYDOWN")

	###########################################
	split_z.separator()
	split_z.operator("am_list.mat_delete_slot",text="",icon="X")

	row_z = row.row()
	row_z.alignment ="RIGHT"
	if is_compactmode:
		row_z.operator("am_list.popup_hide_compact",text="",icon="DOWNARROW_HLT")
	else:
		row_z.operator("am_list.popup_hide_panel",text="",icon="DOWNARROW_HLT")
