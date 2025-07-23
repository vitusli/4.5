import bpy

# 個別アイテムの詳細メニュー
def uidetail_menu(self, context,layout,act_item):
	props = bpy.context.scene.am_list
	light = act_item.data

	layout = layout.box()

	row = layout.row(align=True)
	row.prop(light, "type", expand=True)


	layout.use_property_split = True
	layout.use_property_decorate = False

	col = layout.column()
	col.prop(light, "color")
	col.prop(light, "energy")
	col.prop(light, "specular_factor", text="Specular")

	col.separator()

	if light.type in {'POINT', 'SPOT'}:
		col.prop(light, "shadow_soft_size", text="Radius")
	elif light.type == 'SUN':
		col.prop(light, "angle")
	elif light.type == 'AREA':
		col.prop(light, "shape")

		sub = col.column(align=True)

		if light.shape in {'SQUARE', 'DISK'}:
			sub.prop(light, "size")
		elif light.shape in {'RECTANGLE', 'ELLIPSE'}:
			sub.prop(light, "size", text="Size X")
			sub.prop(light, "size_y", text="Y")


	#########################
	col = layout.column(align=True)
	col.prop(light, "use_shadow", text="Shadow")

	row = col.row(align=True)
	row.active = light.use_shadow
	row.prop(light, "use_custom_distance", text="Custom Distance")
	if light.use_custom_distance:
		cols = col.column(align=True)
		cols.prop(light, "cutoff_distance", text="Distance")
