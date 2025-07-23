import bpy
from .. import __package__ as addon_id
#########################################
# イメージ
def draw_panel_img_menu(self, context,is_compactmode):
	layout = self.layout
	prefs = bpy.context.preferences.addons[addon_id].preferences
	props = context.scene.am_list
	wm = bpy.context.scene.am_list_wm

	if not prefs.usepanel_img:
		sp = layout.split(align=True,factor=0.7)
		rows = sp.row(align=True)
		rows.alignment = 'LEFT'
		rows.prop(wm, "toggle_img",text="",icon="TRIA_DOWN" if wm.toggle_img else "TRIA_RIGHT", emboss=False)
		rows.prop(wm, "toggle_img",text="Image",icon="IMAGE_DATA",emboss=False)
		row = sp.row(align=True)
		row.alignment = 'RIGHT'
		imgcount = len(bpy.data.images)
		row.label(text=": " + str(imgcount))
		row.menu("AMLIST_MT_other_img",text="",icon="DOWNARROW_HLT")

	open = wm.toggle_img
	if prefs.usepanel_img:
		if is_compactmode:
			open = wm.toggle_img
		else:
			open = True
	if not open:
		return

	#######################################################
	# アクティブなアイテム
	try:
		img = bpy.data.images[props.id_img]
	except:
		img = None

	row = layout.row(align = True)
	# col = row.column(align=True)
	# col.operator("am_list.image_move_active_id",text="",icon="TRIA_UP").direction = "UP"
	# col.operator("am_list.image_move_active_id",text="",icon="TRIA_DOWN").direction = "DOWN"

	col = row.column(align = True)

	if img.source in {'VIEWER', 'GENERATED'}:
		if img.type == "UV_TEST":
			col.label(text = img.source + " : " + img.name)
		else:
			col.label(text = img.source + " : " + img.type)
	elif img:
		col.prop(img, "filepath", text="")
	else:
		col.label(text="",icon="NONE")

	row = col.row(align = True)

	if img.source == 'VIEWER' or (img.source == 'GENERATED' and img.type == "RENDER_RESULT"):
		row.label(text="",icon="NONE")
	elif img:
		row.label(text=" " + "%d x %d" % (img.size[0], img.size[1]), icon='TEXTURE')
	else:
		row.label(text="Can't load image file", icon='ERROR')


	# row.prop(props,"img_uidetail_toggle",text="",icon="STICKY_UVS_DISABLE")
	# if props.img_uidetail_toggle:
	uidetail = row.operator("am_list.uidetail_toggle_all",text="" ,icon="FULLSCREEN_ENTER")
	uidetail.type="img"
	# else:
	# 	row.label(text="",icon="BLANK1")
	row.separator()

	row.prop(props,"img_show_size",text="",icon="CON_SIZELIMIT")
	row.prop(props,"img_show_filepath",text="",icon="SORTSIZE")
	row.separator()
	rows = row.row(align=True)
	rows.scale_x = 1.2
	rows.operator("image.save_all_modified", text="", icon='FILE_TICK')
	rows.operator("am_list.reload_all_image", text="", icon="FILE_REFRESH")
	row.separator()
	row.operator("image.new",text="",icon="ADD")
	row.operator("image.open",text="",icon="FILE_FOLDER")

	# 検索
	row = layout.row(align = True)
	row.prop(props,"img_filter",text="",icon="VIEWZOOM")
	row.prop(props, "img_filter_use_regex_src",text="", icon='SORTBYEXT')
	row.menu("AMLIST_MT_filter_menu_img", icon='DOWNARROW_HLT', text="")
	row.separator()
	rows = row.row(align=True)
	rows.scale_x = .4
	rows.prop(props, "img_filter_sort_type",text="")
	row.prop(props, "img_filter_reverse",text="", icon='SORT_DESC' if props.img_filter_reverse else "SORT_ASC")


	all_data_l = [o for o in bpy.data.images]
	if len(all_data_l) >= props.img_list_rows:
		l_height = props.img_list_rows
	elif len(all_data_l) <= 3:
		l_height = 3
	else:
		l_height = len(all_data_l)

	# メインのリスト
	layout.template_list(
	"AMLIST_UL_image", "",
	bpy.data, "images",
	props, "id_img",
	rows = l_height
	)
