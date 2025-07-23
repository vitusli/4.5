import bpy


# 個別アイテムの詳細メニュー
def uidetail_menu(self, context,layout,act_item):
	props = bpy.context.scene.am_list

	# オブジェクトリストのタイプ
	if props.mat_filter_type=="All_Data":
		filter_type = [obj for obj in bpy.data.objects if obj.animation_data if obj.animation_data.action == act_item]
	else:
		filter_type = [obj for obj in bpy.context.scene.objects if obj.animation_data if obj.animation_data.action == act_item]

	filter_type = sorted(filter_type, key=lambda p: p.name)
	# Menu
	box = layout.box()
	col = box.column(align=True)
	if filter_type:
		for obj in filter_type:
			uidetail_list_menu(self, context,col,obj,act_item)
	else:
		col.alignment="CENTER"
		col.label(text="No Object",icon="NONE")


def uidetail_list_menu(self, context,layout,itemobj,item):
	props = bpy.context.scene.am_list

	row = layout.row(align=True)

	icon_sel = "RESTRICT_SELECT_ON"
	emboss_hlt = False
	objicon = "OBJECT_DATA"
	item_active = True
	item_enabled = True

	# select
	try:
		for sel_o in bpy.context.selected_objects:
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
	objicon = "DOT"
	try:
		if itemobj.type == "EMPTY":
			if itemobj.empty_display_type == "PLAIN_AXES":
			    objicon = "EMPTY_AXIS"
			elif itemobj.empty_display_type == "ARROWS":
			    objicon = "EMPTY_ARROWS"
			elif itemobj.empty_display_type == "SINGLE_ARROW":
			    objicon = "EMPTY_SINGLE_ARROW"
			elif itemobj.empty_display_type == "CIRCLE":
			    objicon = "MESH_CIRCLE"
			elif itemobj.empty_display_type == "CUBE":
			    objicon = "MESH_CUBE"
			elif itemobj.empty_display_type == "SPHERE":
			    objicon = "MESH_UVSPHERE"
			elif itemobj.empty_display_type == "CONE":
			    objicon = "CONE"
			elif itemobj.empty_display_type == "IMAGE":
			    objicon = "IMAGE_DATA"
		elif itemobj.type == "MESH":
		    objicon = 'OUTLINER_DATA_MESH'
		elif itemobj.type == "CURVE":
		    objicon = 'OUTLINER_DATA_CURVE'
		elif itemobj.type == "LATTICE":
		    objicon = 'OUTLINER_DATA_LATTICE'
		elif itemobj.type == "META":
		    objicon = 'OUTLINER_DATA_META'
		elif itemobj.type == "LIGHT":
		    objicon = 'OUTLINER_DATA_LIGHT'
		elif itemobj.type == "CAMERA":
		    objicon = 'OUTLINER_DATA_CAMERA'
		elif itemobj.type == "ARMATURE":
		    objicon = 'OUTLINER_DATA_ARMATURE'
		elif itemobj.type == "FONT":
		    objicon = 'OUTLINER_DATA_FONT'
		elif itemobj.type == "SURFACE":
		    objicon = 'OUTLINER_DATA_SURFACE'
		elif itemobj.type == "VOLUME":
		    objicon = 'OUTLINER_DATA_VOLUME'
		elif itemobj.type == "SPEAKER":
		    objicon = 'OUTLINER_DATA_SPEAKER'
		elif itemobj.type == "LIGHT_PROBE":
		    objicon = 'OUTLINER_DATA_LIGHTPROBE'
		elif itemobj.type == "GP_LAYER":
		    objicon = 'OUTLINER_DATA_GP_LAYER'
		elif itemobj.type == "GREASEPENCIL":
		    objicon = 'OUTLINER_DATA_GREASEPENCIL'
	except: pass

	# Hide is no active
	try:
		if not itemobj in [obj for vl in bpy.context.scene.view_layers for obj in vl.objects]:
			if props.action_uidetail_nameedit:
				item_active = False
			else:
				item_enabled = False

		sc_obj = bpy.context.scene.objects[itemobj.name]
		if sc_obj.hide_get() or sc_obj.hide_viewport:
			item_active=False
	except: pass


	######################################
	# menu
	row.active = item_active
	row.enabled = item_enabled


	row.label(text="",icon="BLANK1")

	if item.use_fake_user and item.users == 0 and item.users == 1:
		row.label(text="",icon="BLANK1")
	else:
		row.operator("am_list.asobj_select",text="" ,icon=icon_sel,emboss=emboss_hlt).item_name=itemobj.name


	if props.action_uidetail_nameedit:
		row.prop(itemobj,"name",text="")
	else:
		row.operator("am_list.asobj_select",text=itemobj.name ,icon=objicon,emboss=emboss_hlt).item_name=itemobj.name
