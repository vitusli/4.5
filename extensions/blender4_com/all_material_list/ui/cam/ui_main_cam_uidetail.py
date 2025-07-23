import bpy

# 個別アイテムの詳細メニュー
def uidetail_menu(self, context,layout,act_item):
	props = bpy.context.scene.am_list
	cam = act_item.data

	layout = layout.box()


	layout.use_property_split = True
	layout.use_property_decorate = False

	col = layout.column()

	row = col.row(align=True)
	row.prop(cam, "type")
	col.separator()
	if cam.type == 'PERSP':
		col = layout.column()
		if cam.lens_unit == 'MILLIMETERS':
			col.prop(cam, "lens")
		elif cam.lens_unit == 'FOV':
			col.prop(cam, "angle")
		col.prop(cam, "lens_unit")

	elif cam.type == 'ORTHO':
		col.prop(cam, "ortho_scale")

	elif cam.type == 'PANO':
		engine = context.engine
		if engine == 'CYCLES':
			ccam = cam.cycles
			col.prop(ccam, "panorama_type")
			if ccam.panorama_type == 'FISHEYE_EQUIDISTANT':
				col.prop(ccam, "fisheye_fov")
			elif ccam.panorama_type == 'FISHEYE_EQUISOLID':
				col.prop(ccam, "fisheye_lens", text="Lens")
				col.prop(ccam, "fisheye_fov")
			elif ccam.panorama_type == 'EQUIRECTANGULAR':
				sub = col.column(align=True)
				sub.prop(ccam, "latitude_min", text="Latitude Min")
				sub.prop(ccam, "latitude_max", text="Max")
				sub = col.column(align=True)
				sub.prop(ccam, "longitude_min", text="Longitude Min")
				sub.prop(ccam, "longitude_max", text="Max")
		elif engine in {'BLENDER_RENDER', 'BLENDER_EEVEE', 'BLENDER_WORKBENCH'}:
			if cam.lens_unit == 'MILLIMETERS':
				col.prop(cam, "lens")
			elif cam.lens_unit == 'FOV':
				col.prop(cam, "angle")
			col.prop(cam, "lens_unit")

	col = layout.column()
	col.separator()

	sub = col.column(align=True)
	sub.prop(cam, "shift_x", text="Shift X")
	sub.prop(cam, "shift_y", text="Y")

	col.separator()
	sub = col.column(align=True)
	sub.prop(cam, "clip_start", text="Clip Start")
	sub.prop(cam, "clip_end", text="End")

	# dof
	layout.prop(cam.dof, "use_dof")
	if cam.dof.use_dof:
		dof = cam.dof
		# layout.active = dof.use_dof

		col = layout.column()
		col.prop(dof, "focus_object", text="Focus on Object")
		sub = col.column()
		sub.active = (dof.focus_object is None)
		sub.prop(dof, "focus_distance", text="Focus Distance")


		col = layout.column()
		col.prop(dof, "aperture_fstop")

		col = layout.column()
		col.prop(dof, "aperture_blades")
		col.prop(dof, "aperture_rotation")
		col.prop(dof, "aperture_ratio")
