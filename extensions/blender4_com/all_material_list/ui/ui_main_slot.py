import bpy
from bpy.props import *
from .mat.ui_main_mat_mini_socket import *


def draw_matslot_menu(self, context):
	layout = self.layout
	props = bpy.context.scene.am_list
	wm = bpy.context.scene.am_list_wm
	obj = bpy.context.active_object
	if obj:
		if obj.material_slots:
			sp_factor = 0.4
		else:
			sp_factor = 0.8
	else:
		sp_factor = 0.8

	sp = layout.split(factor=sp_factor,align=True)
	rows = sp.row(align=True)
	rows.alignment = 'LEFT'
	rows.prop(wm, "toggle_mat_slot", icon="TRIA_DOWN" if wm.toggle_mat_slot else "TRIA_RIGHT", icon_only=True, emboss=False)
	rows.prop(wm, "toggle_mat_slot",text="Slot",icon="SORTSIZE",emboss=False)

	if obj:
		if obj.material_slots:

			if obj.active_material:
				row = sp
				mat = obj.active_material
				view_nml = False
				node_compact_parameter(mat,row,view_nml,"SLOT")



	if wm.toggle_mat_slot:
		if obj:
			ob = obj

			if ob:
				is_sortable = len(ob.material_slots) > 1
				rows = 2
				if is_sortable:
					rows = 2
				row = layout.row()
				row.template_list("MATERIAL_UL_matslots", "", ob, "material_slots", ob, "active_material_index", rows=rows)
				if is_sortable:
					col = row.column(align=True)
					col.operator("object.material_slot_move", icon='TRIA_UP', text="").direction = 'UP'
					col.operator("object.material_slot_move", icon='TRIA_DOWN', text="").direction = 'DOWN'
					col.separator()

				col = row.column(align=True)
				col.operator("object.material_slot_add", icon='ADD', text="")
				col.operator("object.material_slot_remove", icon='REMOVE', text="")
				col.menu("MATERIAL_MT_context_menu", icon='DOWNARROW_HLT', text="")

				if ob.mode == 'EDIT':
					split = layout.split(factor=0.5,align=True)
					if ob:
						split.template_ID(ob, "active_material", new="material.new")

					# row = layout.row(align=True)
					split.operator("object.material_slot_assign", text="",icon="ADD")
					split.operator("object.material_slot_select", text="",icon="RESTRICT_SELECT_OFF")
					split.operator("object.material_slot_deselect", text="",icon="RESTRICT_SELECT_ON")

				else:
					split = layout.split(factor=0.65)
					if ob:
						split.template_ID(ob, "active_material", new="material.new")
						row = split.row()
		else:
			box = layout.box()
			box.label(text="No Active Object",icon="NONE")
