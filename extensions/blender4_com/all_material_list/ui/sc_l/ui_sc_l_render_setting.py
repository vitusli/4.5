import bpy, math
if bpy.app.version >= (3,0,0):
	from bl_ui.properties_output import RENDER_PT_format
	dime_cls = RENDER_PT_format
else:
	from bl_ui.properties_output import RENDER_PT_dimensions
	dime_cls = RENDER_PT_dimensions


def draw_sc_l_render_setting(self, context, layout, scene, ptdime):
	props = scene.am_list
	sc = scene
	rd = scene.render
	row = layout.row(align=True)

	if ptdime:
		box = layout
	else:
		box = layout.box()
	cols = box.column(align=True)

	row = cols.row(align=True)

	rows = row.row(align=True)
	if not sc.camera:
		rows.alert=True

	rows.prop(sc, "camera",icon="CAMERA_DATA")
	cam = sc.camera
	if cam:
		if cam.hide_render:
			rows = row.row(align=True)
			row.active=False
			rows.prop(cam,"hide_render",text="",icon="RESTRICT_RENDER_OFF", emboss=False)
		else:
			row.prop(cam,"hide_render",text="",icon="RESTRICT_RENDER_OFF", emboss=False)
	else:
		row.label(text="",icon="BLANK1")

	row = cols.row(align=True)
	if sc.render.filepath in { "/","//" , "","/tmp/"}:
		row.alert=True

	row.prop(sc.render,"filepath",text="",icon="FILE_TICK")
	cols.separator()


	################################################
	sp = cols.split(align=True,factor=0.5)
	rows = sp.row(align=True)
	rows.alignment = 'LEFT'
	if ptdime:
		rows.prop(props, "sc_l_ptdime_toggle_resolution",text="",icon="TRIA_DOWN" if props.sc_l_ptdime_toggle_resolution else "TRIA_RIGHT",emboss=False)
		rows.prop(props, "sc_l_ptdime_toggle_resolution",icon="SHADING_BBOX",emboss=False)
		toggle_menu = props.sc_l_ptdime_toggle_resolution
	else:
		rows.prop(props, "sc_l_render_s_toggle_resolution",text="",icon="TRIA_DOWN" if props.sc_l_render_s_toggle_resolution else "TRIA_RIGHT",emboss=False)
		rows.prop(props, "sc_l_render_s_toggle_resolution",icon="SHADING_BBOX",emboss=False)
		toggle_menu = props.sc_l_render_s_toggle_resolution

	row = sp.row(align=True)
	row.alignment = 'RIGHT'
	# 最終解像度
	rowx = row.row(align=True)
	rowx.alignment="RIGHT"
	final_res_x = int(rd.resolution_x * (rd.resolution_percentage / 100))
	final_res_y = int(rd.resolution_y * (rd.resolution_percentage / 100))
	if rd.use_border:
		final_res_x_border = int(final_res_x * (rd.border_max_x - rd.border_min_x))
		final_res_y_border = int(final_res_y * (rd.border_max_y - rd.border_min_y))
		rowx.label(text="{} x {} [B:{} x {}]".format(
		str(final_res_x), str(final_res_y),
		str(final_res_x_border), str(final_res_y_border)))
	else:
		rowx.label(text="{} x {}".format(
		str(final_res_x), str(final_res_y)))


	if toggle_menu:
		render_setting_resolution_menu(self,context,cols,scene)


	################################################
	sp = cols.split(align=True,factor=0.5)
	rows = sp.row(align=True)
	rows.alignment = 'LEFT'
	if ptdime:
		rows.prop(props, "sc_l_ptdime_toggle_frame",text="",icon="TRIA_DOWN" if props.sc_l_ptdime_toggle_frame else "TRIA_RIGHT",emboss=False)
		rows.prop(props, "sc_l_ptdime_toggle_frame",icon="DECORATE_KEYFRAME",emboss=False)
		toggle_menu = props.sc_l_ptdime_toggle_frame
	else:
		rows.prop(props, "sc_l_render_s_toggle_frame",text="",icon="TRIA_DOWN" if props.sc_l_render_s_toggle_frame else "TRIA_RIGHT",emboss=False)
		rows.prop(props, "sc_l_render_s_toggle_frame",icon="DECORATE_KEYFRAME",emboss=False)
		toggle_menu = props.sc_l_render_s_toggle_frame

	row = sp.row(align=True)
	row.alignment = 'RIGHT'
	ren_frame_count = scene.frame_end - scene.frame_start + 1
	# row.prop(scene, "frame_current",text="",emboss=False)
	frame_s_to_e = str(scene.frame_start)+" - " +str(scene.frame_end)
	row.label(text=frame_s_to_e+"  ("+str(ren_frame_count)+")",icon="NONE")

	if toggle_menu:
		render_setting_frame_menu(self,context,cols,scene)

	################################################
	sp = cols.split(align=True,factor=0.5)
	rows = sp.row(align=True)
	rows.alignment = 'LEFT'
	if ptdime:
		rows.prop(props, "sc_l_ptdime_toggle_sample",text="",icon="TRIA_DOWN" if props.sc_l_ptdime_toggle_sample else "TRIA_RIGHT",emboss=False)
		rows.prop(props, "sc_l_ptdime_toggle_sample",icon="IPO_QUAD",emboss=False)
		toggle_menu = props.sc_l_ptdime_toggle_sample
	else:
		rows.prop(props, "sc_l_render_s_toggle_sample",text="",icon="TRIA_DOWN" if props.sc_l_render_s_toggle_sample else "TRIA_RIGHT",emboss=False)
		rows.prop(props, "sc_l_render_s_toggle_sample",icon="IPO_QUAD",emboss=False)
		toggle_menu = props.sc_l_render_s_toggle_sample

	row = sp.row(align=True)
	row.alignment = 'RIGHT'
	if scene.render.engine == 'BLENDER_EEVEE':
		cscene = scene.eevee
		row.prop(cscene, "taa_render_samples", text="",emboss=False)
	else:
		cscene = scene.cycles
		row.prop(cscene, "samples", text="",emboss=False)

		row.prop(context.view_layer.cycles, "use_denoising",text="",icon="ALIGN_FLUSH")

	if toggle_menu:
		render_setting_sample_menu(self,context,cols,scene)


	################################################
	sp = cols.split(align=True,factor=0.5)
	rows = sp.row(align=True)
	rows.alignment = 'LEFT'
	if ptdime:
		rows.prop(props, "sc_l_ptdime_toggle_file",text="",icon="TRIA_DOWN" if props.sc_l_ptdime_toggle_file else "TRIA_RIGHT",emboss=False)
		rows.prop(props, "sc_l_ptdime_toggle_file",icon="DOT",emboss=False)
		toggle_menu = props.sc_l_ptdime_toggle_file
	else:
		rows.prop(props, "sc_l_render_s_toggle_file",text="",icon="TRIA_DOWN" if props.sc_l_render_s_toggle_file else "TRIA_RIGHT",emboss=False)
		rows.prop(props, "sc_l_render_s_toggle_file",icon="DOT",emboss=False)
		toggle_menu = props.sc_l_render_s_toggle_file

	row = sp.row(align=True)
	row.alignment = 'RIGHT'
	rows = row.row(align=True)
	rows.scale_x = .65
	rows.prop(rd.image_settings, "file_format",text="",emboss=False)
	row.prop(rd, "use_overwrite",text="",icon="FILE_TICK")

	if toggle_menu:
		render_setting_file_menu(self,context,cols,scene)

# @staticmethod
def draw_framerate(layout, sub, rd):
	if dime_cls._preset_class is None:
		dime_cls._preset_class = bpy.types.RENDER_MT_framerate_presets

	args = rd.fps, rd.fps_base, dime_cls._preset_class.bl_label
	fps_label_text, show_framerate = dime_cls._draw_framerate_label(*args)

	sub.menu("RENDER_MT_framerate_presets", text=fps_label_text)

	if show_framerate:
		col = layout.column(align=True)
		col.prop(rd, "fps")
		col.prop(rd, "fps_base", text="Base")


def render_setting_resolution_menu(self,context,layout,scene):
	props = context.scene.am_list
	rd = scene.render
	box = layout.box()
	box.use_property_split = True
	box.use_property_decorate = False

	# sp = box.split(align=True,factor=0.5)
	# sp.use_property_split = False
	# sp.alignment="RIGHT"

	# 最終解像度
	# sp.label(text="Final")
	# row = sp.row(align=True)
	# final_res_x = (rd.resolution_x * rd.resolution_percentage) / 100
	# final_res_y = (rd.resolution_y * rd.resolution_percentage) / 100
	# if rd.use_border:
	# 	final_res_x_border = round( (final_res_x * (rd.border_max_x - rd.border_min_x)))
	# 	final_res_y_border = round( (final_res_y * (rd.border_max_y - rd.border_min_y)))
	# 	row.label(text="{} x {} [B:{} x {}]".format(
	# 	str(final_res_x)[:-2], str(final_res_y)[:-2],
	# 	str(final_res_x_border), str(final_res_y_border)))
	# else:
	# 	row.label(text="{} x {}".format(
	# 	str(final_res_x)[:-2], str(final_res_y)[:-2]))

	# XY入れ替え

	################################################
	col = box.column(align=True)
	row = col.row(align=True)
	row.prop(rd, "resolution_x", text="Resolution X")
	row.operator("am_list.x_y_change", text="", icon="FILE_REFRESH").scn_name=scene.name
	row = col.row(align=True)
	row.prop(rd, "resolution_y", text="Y")
	row.label(text="",icon="BLANK1")
	row = col.row()
	row.prop(rd, "resolution_percentage", text="%")
	row.operator("am_list.apply_resolution_percentage",text="", icon='FILE_TICK').scn_name=scene.name




	# 比率
	# sp = box.split(align=True,factor=0.5)
	# sp.use_property_split = False
	# sp.alignment="RIGHT"
	# sp.label(text="Ratio")
	# a = rd.resolution_x
	# b = rd.resolution_y
	# yakusuu = math.gcd(a, b)
	# yaku_x = a/yakusuu
	# yaku_y = b/yakusuu
	# sp.label(text="{} : {}".format(
	# str(yaku_x)[:-2], str(yaku_y)[:-2]))


	sp = box.split(align=True,factor=0.5)
	sp.use_property_split = False
	sp.alignment="RIGHT"
	sp.label(text="Render Region",icon="NONE")
	sp.prop(rd, "use_border",text="", icon="BORDERMOVE")
	sub = sp.column(align=True)
	sub.active = rd.use_border
	sub.prop(rd, "use_crop_to_border", text="",icon="STICKY_UVS_LOC")
	box.separator()


def render_setting_frame_menu(self,context,layout,scene):
	row = layout.row(align =True)
	box = row.box()
	box.use_property_split = True
	box.use_property_decorate = False

	scn = context.scene

	sp = box.split(align=True,factor=0.5)
	sp.use_property_split = False
	sp.alignment="RIGHT"
	sp.label(text="Current",icon="NONE")
	row = sp.row(align=True)
	# tt = scn.frame_end - scn.frame_start
	# sp.prop(props,"frame_count")
	# row.label(text=str(tt),icon="NONE")
	row.prop(scene, "frame_current",text="")


	col = box.column(align=True)
	col.prop(scene, "frame_start", text="Frame Start")
	col.prop(scene, "frame_end", text="End")
	col.prop(scene, "frame_step", text="Step")

	col = box.split()
	col.alignment = 'RIGHT'
	col.label(text="Frame Rate")
	rd = scene.render
	draw_framerate(box, col, rd)
	box.separator()


def render_setting_sample_menu(self,context,layout,scene):
	props = context.scene.am_list

	box = layout.box()
	box.use_property_split = True
	box.use_property_decorate = False
	if scene.render.engine == 'BLENDER_EEVEE':
		csnene = scene.eevee

		col = box.column(align=True)
		col.prop(csnene, "taa_render_samples", text="Render")
		col.prop(csnene, "taa_samples", text="Viewport")

		col = box.column()
		col.prop(csnene, "use_taa_reprojection")

	else:
		cscene = scene.cycles
		# if not use_optix(context):
		# 	box.prop(cscene, "progressive")

		if cscene.progressive == 'PATH' or use_branched_path(context) is False:
			col = box.column(align=True)
			col.prop(cscene, "samples", text="Render")
			col.prop(cscene, "preview_samples", text="Viewport")
			row = col.row(align=True)
			# rows = row.row(align=True)
			# rows.label(text="")
			row.label(text="",icon="IPO_QUAD")
			row.prop(cscene, "use_square_samples")

		else:
			col = box.column(align=True)
			col.prop(cscene, "aa_samples", text="Render")
			col.prop(cscene, "preview_aa_samples", text="Viewport")

		row = box.row(align=True)
		# rows = row.row(align=True)
		# rows.label(text="")
		row.label(text="",icon="ALIGN_FLUSH")

		row.prop(context.view_layer.cycles, "use_denoising")



	box.separator()


def render_setting_file_menu(self,context,layout,scene):
	props = context.scene.am_list
	box = layout.box()
	col = box.column(align=True)
	col.use_property_split = False
	col.use_property_decorate = False

	rd = scene.render
	image_settings = rd.image_settings

	col.use_property_split = True

	flow = col.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=False, align=False)

	col = flow.column()
	col.active = not rd.is_movie_format
	col.prop(rd, "use_overwrite")
	col = flow.column()
	col.active = not rd.is_movie_format
	col.prop(rd, "use_placeholder")
	col = flow.column()
	col.prop(rd, "use_file_extension")
	col = flow.column()
	col.prop(rd, "use_render_cache")
	box.separator()
	box.template_image_settings(image_settings, color_management=False)
	box.separator()
