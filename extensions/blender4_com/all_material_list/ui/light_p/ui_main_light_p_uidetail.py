import bpy

# 個別アイテムの詳細メニュー
def uidetail_menu(self, context,layout,act_item):
	props = bpy.context.scene.am_list
	probe = act_item.data

	layout = layout.box()

	# row = layout.row(align=True)
	# row.prop(light, "type", expand=True)


	layout.use_property_split = True
	layout.use_property_decorate = False


	if probe.type == 'GRID':
		col = layout.column()
		col.prop(probe, "influence_distance", text="Distance")
		col.prop(probe, "falloff")
		col.prop(probe, "intensity")

		sub = col.column(align=True)
		sub.prop(probe, "grid_resolution_x", text="Resolution X")
		sub.prop(probe, "grid_resolution_y", text="Y")
		sub.prop(probe, "grid_resolution_z", text="Z")

	elif probe.type == 'PLANAR':
		col = layout.column()
		col.prop(probe, "influence_distance", text="Distance")
		col.prop(probe, "falloff")
	else:
		col = layout.column()
		col.prop(probe, "influence_type")

		if probe.influence_type == 'ELIPSOID':
			col.prop(probe, "influence_distance", text="Radius")
		else:
			col.prop(probe, "influence_distance", text="Size")

		col.prop(probe, "falloff")
		col.prop(probe, "intensity")

	sub = col.column(align=True)
	if probe.type != 'PLANAR':
		sub.prop(probe, "clip_start", text="Clipping Start")
	else:
		sub.prop(probe, "clip_start", text="Clipping Offset")

	if probe.type != 'PLANAR':
		sub.prop(probe, "clip_end", text="End")
