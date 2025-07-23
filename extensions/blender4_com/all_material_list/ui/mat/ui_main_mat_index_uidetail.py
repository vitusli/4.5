import bpy

# オブジェクト
def asobj_act(self, context):
	props = bpy.context.scene.am_list
	layout = self.layout



	box = layout.box()
	box.label(text="Assigned Object",icon="NONE")

	if bpy.context.object:
		obj = bpy.context.object
		if obj.active_material:

			# Filter Type
			if props.mat_filter_type=="All_Data":
				filter_type = bpy.data.objects
			else:
				filter_type = bpy.context.scene.objects

			filter_type = sorted(filter_type, key=lambda p: p.name)
			# Menu
			col = box.column(align=True)

			actmat = obj.active_material
			for obj in filter_type:
				if obj.type in {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT', 'GPENCIL', 'VOLUME'} and actmat.name in obj.material_slots:
					uidetail_list_menu(self, context,col,obj,actmat)

		else:
			box.label(text="No Active Material",icon="NONE")
	else:
		box.label(text="No Active Object",icon="NONE")


def uidetail_for(self, context,layout,actmat):
	props = bpy.context.scene.am_list
	if not props.mat_uidetail_toggle:
		return

	box = layout.box()
	col = box.column(align=True)

	# Filter Type
	filter_type = []
	if props.mat_filter_type=="All_Data":
		filter_type = [obj for obj in bpy.data.objects]
	else:
		filter_type = [obj for obj in bpy.context.scene.objects]

	filter_type = sorted(filter_type, key=lambda p: p.name)

	# オブジェクトデータ内の、全マテリアルの一致する
	# for
	for obj in filter_type:
		if obj.type in {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT', 'GPENCIL', 'VOLUME'} and actmat.name in obj.material_slots:
			uidetail_list_menu(self, context,col,obj,actmat)


def uidetail_list_menu(self, context,layout,itemobj,amat):
	props = bpy.context.scene.am_list
	wm = bpy.context.scene.am_list_wm
	item = amat
	index = bpy.data.materials.find(item.name)

	row = layout.row(align=True)

	icon_sel = "RESTRICT_SELECT_ON"
	emboss_hlt = False
	objicon = "OBJECT_DATA"
	item_active = True

	# select
	try:
		for sel_o in bpy.context.selected_objects:
			if sel_o.type in {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT', 'GPENCIL', 'VOLUME'}:
				if itemobj == sel_o:
					icon_sel = "PMARKER_SEL"
					emboss_hlt = True
		if itemobj == bpy.context.object:
			if bpy.context.object:
				obj = bpy.context.object
				icon_sel = "RESTRICT_SELECT_OFF"
				emboss_hlt = True
	except: pass


	# obj type
	try:
		if itemobj.type == 'MESH':
			objicon = "OUTLINER_OB_MESH"
		elif itemobj.type == 'CURVE':
			objicon = "OUTLINER_OB_CURVE"
		elif itemobj.type == 'SURFACE':
			objicon = "OUTLINER_OB_SURFACE"
		elif itemobj.type == 'META':
			objicon = "OUTLINER_OB_META"
		elif itemobj.type == 'FONT':
			objicon = "OUTLINER_OB_FONT"
		elif itemobj.type == 'GPENCIL':
			objicon = "OUTLINER_OB_GREASEPENCIL"
		elif itemobj.type == 'VOLUME':
			objicon = "OUTLINER_DATA_VOLUME"
	except: pass



	# Hide is no active
	try:
		sc_obj = bpy.context.scene.objects[itemobj.name]
		if sc_obj.hide_get() or sc_obj.hide_viewport:
			item_active=False
	except: pass


	######################################
	# menu
	row_l = row.row(align=True)
	row_l.active = item_active
	row_l.separator()
	row_l.label(text="",icon="BLANK1")

	if item.use_fake_user and item.users == 0 and item.users == 1:
		row_l.label(text="",icon="BLANK1")
	else:
		op = row_l.operator("am_list.asobj_select",text="" ,icon=icon_sel,emboss=emboss_hlt)
		op.item_name=itemobj.name
		op.mat_name = item.name

	if props.mat_uidetail_nameedit:
		row_l.prop(itemobj,"name",text="")
	else:
		rows = row_l.row(align=True)
		rows.alignment="LEFT"
		op = rows.operator("am_list.asobj_select",text=itemobj.name ,icon=objicon,emboss=emboss_hlt,translate=False)
		op.item_name=itemobj.name
		op.mat_name=item.name


	rows = row.row(align=True)
	rows.alignment="RIGHT"
	op = rows.operator("am_list.mat_remove_assignment_from_obj",text="",icon="X",emboss=False)
	op.obj_name = itemobj.name
	op.mat_name = item.name
