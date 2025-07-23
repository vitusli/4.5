import bpy
from .. import __package__ as addon_id
########################################
# ビューポートカラー
def draw_panel_vcol_menu(self, context,is_compactmode):
	layout = self.layout
	prefs = bpy.context.preferences.addons[addon_id].preferences
	props = context.scene.am_list
	wm = bpy.context.scene.am_list_wm

	########################################
	# コンパクトモード
	if not prefs.usepanel_vcol or is_compactmode:
		sp = layout.split(align=True)
		rows = sp.row(align=True)
		rows.alignment = 'LEFT'
		rows.prop(wm, "toggle_vcol",text="",icon="TRIA_DOWN" if wm.toggle_vcol else "TRIA_RIGHT", emboss=False)
		rows.prop(wm, "toggle_vcol",text="Viewport Color",icon="COLOR",emboss=False)

	open = wm.toggle_vcol
	if prefs.usepanel_vcol:
		if is_compactmode:
			open = wm.toggle_vcol
		else:
			open = True
	if open:
		########################################
		# メイン
		obj = bpy.context.active_object
		if bpy.context.view_layer.objects.active:
			obj_type = obj.type
			is_geometry = (obj_type in {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT', 'VOLUME'})
			is_wire = (obj_type in {'CAMERA', 'EMPTY'})
			is_empty_image = (obj_type == 'EMPTY' and obj.empty_display_type == 'IMAGE')
			is_dupli = (obj.instance_type != 'NONE')
			is_gpencil = (obj_type == 'GPENCIL')


		view = bpy.context.space_data
		if view.type == 'VIEW_3D':
			shading  = view.shading
		else:
			shading = context.scene.display.shading


		if not bpy.context.view_layer.objects.active == None:
			if is_geometry or is_dupli or is_empty_image or is_gpencil:
				layout.prop(shading, "color_type",text="Mode", expand=False)
				box = layout.box()
				if shading.color_type == 'SINGLE':
					box.row().prop(shading, "single_color", text="")
				else:
					if shading.color_type == 'OBJECT':
						col = box.column()
						split = col.split(factor=0.9,align=True)
						split.prop(obj, "color",text="")
						split.operator("am_list.obj_color_clear",text="",icon="X")

					else:
						if not obj.active_material == None:
							mat = obj.active_material
							col = box.column()
							split = col.split(factor=0.9,align=True)
							split.prop(mat, "diffuse_color",text="")
							clear = split.operator("am_list.obj_color_clear",text="",icon="X")
							clear.mat_color = True
							clear.metallic = False
							clear.roughness = False

							split = col.split(factor=0.9,align=True)
							split.prop(mat, "metallic")
							clear = split.operator("am_list.obj_color_clear",text="",icon="X")
							clear.mat_color = False
							clear.metallic = True
							clear.roughness = False

							split = col.split(factor=0.9,align=True)
							split.prop(mat, "roughness")
							clear = split.operator("am_list.obj_color_clear",text="",icon="X")
							clear.mat_color = False
							clear.metallic = False
							clear.roughness = True

						else:
							box.active=False
							box.label(text="No Material",icon="NONE")

					layout.separator()

					box = layout.box()

					row = box.row(align=True)
					row.scale_x = 1.3
					row.label(text="Preset:",icon="NONE")
					row.operator("am_list.obj_color_red",text="",icon="COLORSET_01_VEC")
					row.operator("am_list.obj_color_orange",text="",icon="COLORSET_02_VEC")
					row.operator("am_list.obj_color_green",text="",icon="COLORSET_03_VEC")
					row.operator("am_list.obj_color_light_blue",text="",icon="COLORSET_04_VEC")
					row.operator("am_list.obj_color_blue",text="",icon="COLORSET_04_VEC")
					row.operator("am_list.obj_color_purple",text="",icon="COLORSET_11_VEC")
					row.operator("am_list.obj_color_pink",text="",icon="COLORSET_05_VEC")

					row = box.row(align=True)
					row.scale_y = 1.2
					row.operator("am_list.obj_random_color",text="Random",icon="SHADING_TEXTURE")
					row.operator("am_list.obj_white_to_random_color",text="",icon="SHADING_SOLID")
					clear = row.operator("am_list.obj_color_clear",text="",icon="X")
					clear.mat_color = True
					clear.metallic = True
					clear.roughness = True


					box = box.box()
					if shading.color_type == 'OBJECT':
						box.operator("am_list.viewport_color_to_mat_color",text="Material Color → Object Color",icon="MATERIAL")
						box.prop(props, "to_color_diffuse_mode")
					else:
						box.operator("am_list.viewport_color_to_mat_color",text="Material Color → Viewport Color",icon="MATERIAL")
						box.prop(props, "to_color_diffuse_mode")

			else:
				box = layout.box()
				box.active=False
				box.label(text="No Geometry Object",icon="NONE")


		else:

			layout.prop(shading, "color_type",text="Mode", expand=False)
			# layout.grid_flow(columns=3, align=True).prop(shading, "color_type", expand=True)
			if shading.color_type == 'SINGLE':
				layout.row().prop(shading, "single_color", text="")
			box = layout.box()
			box.active=False
			box.label(text="No Geometry Object",icon="NONE")
