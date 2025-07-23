import bpy
import re #正規表現
import bmesh
import random # オブジェクトカラー・マテリアルビューポートカラーのランダムカラーに必要
import os, numpy, urllib, math, shutil # ファイル名取得に必要

from bpy.props import *
from bpy.types import Operator


# 特定のマテリアルの割り当てを、一括して別のマテリアルに置き換える
class AMLIST_OT_mat_replace(Operator):
	bl_idname = "am_list.mat_replace"
	bl_label = "Replace Material"
	bl_description = "Replace specific material assignments with different materials at once"
	bl_options = {'REGISTER', 'UNDO'}

	old_name: StringProperty(name = "Old Name")
	new_name: StringProperty(name = "New Name")
	only_selected_objects : BoolProperty(default=True, name = "Only Selected Objects")

	def invoke(self, context, event):
		if not bpy.context.view_layer.objects.active == None:
			self.old_name = bpy.context.object.active_material.name

		dpi_value = bpy.context.preferences.system.dpi
		return context.window_manager.invoke_props_dialog(self, width=dpi_value*3)

	def draw(self, context):
		layout = self.layout
		layout.prop_search( self, "old_name", bpy.data, "materials", text="Old")
		layout.prop_search( self, "new_name", bpy.data, "materials", text="New")
		layout.prop( self, "only_selected_objects")

	def execute(self, context):
		old = bpy.data.materials[self.old_name]
		new = bpy.data.materials[self.new_name]

		if self.only_selected_objects:
			data_list = bpy.context.selected_objects
		else:
			data_list = bpy.data.objects

		for o in data_list: #オブジェクトを対象に
			for m in o.material_slots: #マテリアルスロットを対象に
				if self.only_selected_objects:
					bpy.context.view_layer.objects.active = o

				if m.material == old:
					m.material = new

		return {'FINISHED'}


class AMLIST_OT_mat_assign_obj_list(Operator):
	bl_idname = "am_list.mat_assign_obj_list"
	bl_label = "Display Assign Objects List"
	bl_description = "Displays a list of objects that have materials assigned"
	bl_options = {'REGISTER', 'UNDO'}

	mat_name: StringProperty(name = "Mat Name")
	no_selected : BoolProperty(default=True, name = "Exclude selected objects from list")

	def invoke(self, context, event):
		if not len(context.selected_objects) == 0:
			self.old_name = bpy.context.object.active_material.name

		dpi_value = bpy.context.preferences.system.dpi
		return context.window_manager.invoke_props_dialog(self, width=dpi_value*3)

	def draw(self, context):
		layout = self.layout
		layout.prop_search( self, "mat_name", bpy.data, "materials", text="Name")
		layout.prop( self, "no_selected")


		id = self.mat_name
		mat = bpy.data.materials[id]
		obj_set = set()
		for o in bpy.context.view_layer.objects:
			for m in o.material_slots:
				if m.material == mat:
					if self.no_selected:
						if not o.name in [o.name for o in bpy.context.selected_objects]:
							layout.label(text=o.name,icon="NONE")
					else:
						layout.label(text=o.name,icon="NONE")
						# layout.label(text="No assignment object",icon="NONE")
						# layout.prop(bpy.data.objects, o.name)

	def execute(self, context):

		id = bpy.data.materials.find(self.mat_name)
		bpy.ops.am_list.mat_select(mat_id_name = id,select_image_node_name = "")

		return {'FINISHED'}


class AMLIST_OT_mat_merge(Operator):
	bl_idname = "am_list.mat_merge"
	bl_label = "Merge Duplicate Materials (001,002...)"
	bl_description = "Merge materials with duplicate names such as 001,002 ... \nBased on materials that do not have numbers such as 001,002...  at the end of the line"
	bl_options = {'REGISTER', 'UNDO'}

	mat_name: StringProperty(name = "Mat Name")
	partition : StringProperty(default=".", name = "Partition Character")
	all_material : BoolProperty(default=False, name = "All Material")

	def invoke(self, context, event):
		if not len(context.selected_objects) == 0:
			self.old_name = bpy.context.object.active_material.name

		dpi_value = bpy.context.preferences.system.dpi
		return context.window_manager.invoke_props_dialog(self, width=dpi_value*3)

	def draw(self, context):
		layout = self.layout
		layout.prop( self, "all_material")
		if not self.all_material:
			layout.prop_search( self, "mat_name", bpy.data, "materials", text="Name")
		layout.prop( self, "partition")


	def execute(self, context):
		mats = bpy.data.materials

		# 番号のない主の名前にする
		id = self.mat_name
		# (base, sep, ext) = id.rpartition(self.partition)
		# id = base


		if not self.all_material:
			for obj in bpy.data.objects:
				for slot in obj.material_slots:
					if slot.name.startswith(id):
						(base, sep, ext) = slot.name.rpartition(self.partition)
						if ext.isnumeric():
							if id in mats:
								self.report({'INFO'}, "For object '%s' replace '%s' with '%s'" % (obj.name, slot.name, id))
								slot.material = mats.get(id)

		else:
			for obj in bpy.data.objects: # 全オブジェクトの
				for slot in obj.material_slots: # マテリアルスロットの中の
					(base, sep, ext) = slot.name.rpartition(self.partition) # rpartitionにより、文字列を分割し、[前の部分, 分割文字列, 後の部分]という形の変数を用意
					if ext.isnumeric(): # isnumericにより、数値かどうかを判定する
						if base in mats: # マテリアルの中の、ベースの名前に該当するものを検索する
							self.report({'INFO'}, "For object '%s' replace '%s' with '%s'" % (obj.name, slot.name, base))
							slot.material = mats.get(base)  # ベースに置き換える

		return {'FINISHED'}


class AMLIST_OT_mat_cleanup_slot(Operator):
	# 選択オブジェクトの未使用のマテリアルと、空のスロットと削除する
	bl_idname = "am_list.mat_cleanup_slot"
	bl_label = "Cleanup Material Slot"
	bl_description = "Removes unused materials and empty slots from selected objects"
	bl_options = {"REGISTER","UNDO"}


	def execute(self, context):
		tgt_obj_l = bpy.context.selected_objects
		old_mode = bpy.context.object.mode
		old_act_obj = bpy.context.view_layer.objects.active
		bpy.ops.object.mode_set(mode="OBJECT")

		for obj in bpy.context.selected_objects:
			if obj.type in {"MESH", "CURVE", "SURFACE", "META", "FONT","GPENCIL","VOLUME"}:
				if obj.data.materials:
					bpy.context.view_layer.objects.active = obj
					bpy.ops.object.material_slot_remove_unused()

		# 	override = bpy.context.copy()
		# 	override["selected_objects"] = list(tgt_obj_l)
		# 	# override["area"] = [a for a in bpy.context.screen.areas if a.type == "VIEW_3D"][0]
		# 	with context.temp_override(**override):
		# 		bpy.ops.object.material_slot_remove_unused()



		# tgt_l = bpy.context.selected_objects
		# # if not old_act_obj in tgt_l:
		# # 	tgt_l += [old_act_obj]
		#
		# for obj in tgt_l:
		# 	bpy.context.view_layer.objects.active = obj
		#
		# 	if obj.type in {"CURVE", "SURFACE", "META", "FONT"}:
		# 		for i,mat in reversed([(i,m) for i,m in enumerate(obj.data.materials)]):
		# 			if mat == None:
		# 				obj.active_material_index = i
		# 				bpy.ops.object.material_slot_remove()
		# 		continue
		#
		#
		# 	elif obj.type == 'MESH':
		# 		mesh = obj.data
		# 		faces = mesh.polygons
		# 		slots = obj.material_slots
		#
		# 		# get material index per face
		# 		face_len = len (faces)
		# 		used_material_indices = [0 for n in range (face_len)]
		# 		faces.foreach_get ('material_index', used_material_indices)
		#
		# 		# one index should only be once in the list
		# 		used_material_indices = set (used_material_indices)
		#
		# 		# list unused material slots
		# 		slot_len = len (slots)
		# 		all_material_slot_indices = set (n for n in range (slot_len))
		# 		unused_slot_indices = all_material_slot_indices - used_material_indices
		#
		# 		unused_slot_indices = list (unused_slot_indices)
		# 		unused_slot_indices.sort (reverse=True)
		#
		#
		# 		# delete unused slots
		# 		for slot_index in unused_slot_indices:
		# 			obj.active_material_index = slot_index
		# 			bpy.ops.object.material_slot_remove()
		#
		#
		# 		# 1つだけ空のマテリアルが残ってしまうので、それが存在する場合は削除
		# 		if len(obj.material_slots) == 1:
		# 			if obj.material_slots[0].material == None:
		# 				bpy.ops.object.material_slot_remove() # スロットを除去する
		#
		#
		bpy.context.view_layer.objects.active = old_act_obj
		bpy.ops.object.mode_set(mode=old_mode)

		return{'FINISHED'}


class AMLIST_OT_mat_delete_slot(Operator):
	bl_idname = "am_list.mat_delete_slot"
	bl_label = "Delete Material Slot"
	bl_description = "Deletes all material slots of all selected objects"
	bl_options = {"REGISTER","UNDO"}

	def execute(self, context):
		for obj in bpy.context.selected_objects:
			if obj.type in { 'MESH' , 'CURVE' , 'SURFACE' , 'META' , 'FONT' ,'GPENCIL', 'VOLUME'}:
				obj.data.materials.clear()
			# obj.active_material_index = 0
			# for i in range(len(obj.material_slots)):
			# 	bpy.ops.object.material_slot_remove({'object': obj})

		return{'FINISHED'}


class AMLIST_OT_mat_move_index(Operator):
	bl_idname = "am_list.move_index"
	bl_label = "Set Index Material"
	bl_options = {"REGISTER","UNDO"}

	mat_id_name : IntProperty(name = "mat name", description = "mat name")

	def execute(self, context):
		props = bpy.context.scene.am_list
		id = self.mat_id_name

		mat = bpy.data.materials[id]
		mat.pass_index = props.view_mat_index

		return{'FINISHED'}


class AMLIST_OT_mat_move_index_index_list(Operator):
	bl_idname = "am_list.move_index_index_list"
	bl_label = "Set Index Material"
	bl_description = "index Number. Click to Set Index Material"
	bl_options = {"REGISTER","UNDO"}

	mat_id_name : IntProperty(name = "mat name", description = "mat name")

	def execute(self, context):
		props = bpy.context.scene.am_list
		id = self.mat_id_name

		mat = bpy.data.materials[id]
		mat.pass_index = props.move_index

		return{'FINISHED'}


class AMLIST_OT_mat_assign(Operator):
	bl_idname = "am_list.mat_assign"
	bl_label = "Assign Material"
	bl_options = {"REGISTER","UNDO"}

	mat_id_name : IntProperty(name = "mat name", description = "mat name")

	def execute(self, context):
		props = bpy.context.scene.am_list
		id = self.mat_id_name
		obj = bpy.context.object
		mat = bpy.data.materials[id]

		self.report({'INFO'}, "hoge")
		if not obj.mode in {"EDIT", "EDIT_GPENCIL"}:
			if len(obj.material_slots):
				obj.material_slots[obj.active_material_index] = mat
			else:
				obj.active_material = mat
				self.report({'INFO'}, "!!!!")
			return{'FINISHED'}

		return{'FINISHED'}


class AMLIST_OT_mat_rename_obj_name(Operator):
	bl_idname = "am_list.mat_rename_obj_name"
	bl_label = "Rename Material Name → Object Name"
	bl_description = "Rename the active material of the selected object to the name of the selected object."
	bl_options = {"REGISTER","UNDO"}


	def execute(self, context):
		props = bpy.context.scene.am_list

		# id = bpy.context.scene.am_list.material_id_main
		# mat = bpy.data.materials[id]

		for obj in bpy.context.selected_objects:
			bpy.context.view_layer.objects.active = obj
			if obj.type in { 'MESH' , 'CURVE' , 'SURFACE' , 'META' , 'FONT' , 'VOLUME'}:
				if not bpy.context.object.active_material == None: # 割り当てマテリアルがない
					bpy.context.object.active_material.name = obj.name




		return{'FINISHED'}


class AMLIST_OT_mat_select_index(Operator):
	bl_idname = "am_list.mat_select_index"
	bl_label = "Select Material Index"
	bl_options = {"REGISTER","UNDO"}

	mat_id_name : IntProperty(name = "mat name", description = "mat name")

	# def execute(self, context):
	def invoke(self, context, event):
		props = bpy.context.scene.am_list

		# id = self.mat_id_name



		# if not props.select_extend:
		# 	bpy.ops.object.select_all(action='DESELECT')
		if not event.shift:
			for o in bpy.context.selected_objects:
				o.select_set(False)

		if id < len(bpy.data.materials):
			# mat = bpy.data.materials[id]
			obj_set = set()
			# # オブジェクトの中の
			for o in bpy.context.view_layer.objects:
				# マテリアルスロットの
				for m in o.material_slots:
					# 	# マテリアル名が同じ名前の
					if m.material.pass_index == props.view_mat_index:
						  o.select_set(True)

		# アクティブ選択
		if not len(bpy.context.selected_objects)==0:
			bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]


		return{'FINISHED'}


class AMLIST_OT_mat_assign_mat(Operator):
	bl_idname = "am_list.assign_material"
	bl_label = "Assign Material"
	des_01 = "Assign a material to the selected object.\n"
	des_02 = "If in edit mode, assign to the selected face.\n"
	des_03 = "Shift: Duplicate the material"
	destext = des_01 + des_02 + des_03
	bl_description = destext
	bl_options = {"REGISTER","UNDO"}

	mat_name: StringProperty(name = "Mat Name")
	duplicate: BoolProperty(name = "Duplicate")

	@classmethod
	def poll(cls, context):
		if len(bpy.context.selected_objects) == 1:
			obj = bpy.context.selected_objects[0]
			if not obj.type in {"MESH", "CURVE", "SURFACE", "META", "FONT"}:
				return False
		return bpy.context.selected_objects

	def invoke(self, context, event):
		if event.shift:
			self.duplicate = True
		else:
			self.duplicate = False


		return self.execute(context)


	def execute(self, context):
		if self.duplicate:
			new_item = bpy.data.materials[self.mat_name].copy()
			self.report({'INFO'}, "Duplicate [" + new_item.name + "]")
			return {'FINISHED'}


		#########################################
		obj = bpy.context.object
		#########################################
		if obj.mode == 'EDIT_GPENCIL':
			bpy.ops.gpencil.stroke_change_color()
			return {'FINISHED'}

		if obj.mode == 'EDIT':
			bm = bmesh.from_edit_mesh(obj.data)
			selected_face = [f for f in bm.faces if f.select] # 選択面
			mat_name = [mat.name for mat in obj.material_slots if len(obj.material_slots)]

			if self.mat_name in mat_name:
				obj.active_material_index = mat_name.index(self.mat_name)
				bpy.ops.object.material_slot_assign()

			else:
				bpy.ops.object.material_slot_add()
				obj.active_material = bpy.data.materials[self.mat_name]
				bpy.ops.object.material_slot_assign()

			return {'FINISHED'}

		#########################################
		elif obj.mode == 'OBJECT':

			obj_list = [obj for obj in context.selected_objects if obj.type in {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT', 'VOLUME'}]
			old_act = bpy.context.view_layer.objects.active
			for o in bpy.context.selected_objects:
				o.select_set(False)

			for obj in obj_list:
				obj.select_set(True)
				bpy.context.view_layer.objects.active = obj

				if self.mat_name == bpy.data.materials:
					obj.active_material = bpy.data.materials[mat_name]

				else:
					if not len(obj.material_slots):
						bpy.ops.object.material_slot_add()

					obj.active_material = bpy.data.materials[self.mat_name]

			for obj in obj_list:
				obj.select_set(True)

			bpy.context.view_layer.objects.active = old_act


		return {'FINISHED'}


class AMLIST_OT_mat_copy_material_slot(Operator):
	bl_idname = "am_list.mat_copy_material_slot"
	bl_label = "Copy Material Slot"
	bl_description = "Copies the material slot of the active object to another selected object"
	bl_options = {"REGISTER","UNDO"}


	@classmethod
	def poll(cls, context):
		return len(bpy.context.selected_objects) > 1 and bpy.context.active_object

	def execute(self, context):
		old_mode = None
		if not bpy.context.mode == "OBJECT":
			bpy.ops.object.mode_set(mode="OBJECT")
			old_mode = bpy.context.active_object.mode

		act_obj = bpy.context.active_object
		for obj in bpy.context.selected_objects:
			if obj == act_obj:
				continue
			obj.data.materials.clear()

		bpy.ops.object.make_links_data(type='MATERIAL')

		if old_mode:
			bpy.ops.object.mode_set(mode=old_mode)
		return {'FINISHED'}


class AMLIST_OT_mat_set_index(Operator):
	bl_idname = "am_list.mat_set_index"
	bl_label = "Set Index"
	bl_description = ""
	bl_options = {'REGISTER','UNDO'}

	item_name : StringProperty(name = "Material Name")
	item_index : IntProperty(name = "Before Index")
	item_after_index : IntProperty(name = "After Index")


	@classmethod
	def poll(self, context):
		return True

	def invoke(self, context, event):
		wm = context.window_manager
		self.item_after_index = self.item_index
		return wm.invoke_props_dialog(self, width=200)

	def draw(self, context):
		layout = self.layout
		props = context.scene.am_list

		if self.item_after_index == -1:
			layout.label(text="All Material")
		elif self.item_after_index == 0:
			layout.prop(props, "mat_gp_name00",text="")
		elif self.item_after_index == 1:
			layout.prop(props, "mat_gp_name01",text="")
		elif self.item_after_index == 2:
			layout.prop(props, "mat_gp_name02",text="")
		elif self.item_after_index == 3:
			layout.prop(props, "mat_gp_name03",text="")
		elif self.item_after_index == 4:
			layout.prop(props, "mat_gp_name04",text="")
		elif self.item_after_index == 5:
			layout.prop(props, "mat_gp_name05",text="")
		elif self.item_after_index == 6:
			layout.prop(props, "mat_gp_name06",text="")
		elif self.item_after_index == 7:
			layout.prop(props, "mat_gp_name07",text="")
		elif self.item_after_index == 8:
			layout.prop(props, "mat_gp_name08",text="")
		elif self.item_after_index == 9:
			layout.prop(props, "mat_gp_name09",text="")
		elif self.item_after_index == 10:
			layout.prop(props, "mat_gp_name10",text="")
		elif self.item_after_index == 11:
			layout.prop(props, "mat_gp_name11",text="")
		elif self.item_after_index == 12:
			layout.prop(props, "mat_gp_name12",text="")
		elif self.item_after_index == 13:
			layout.prop(props, "mat_gp_name13",text="")
		elif self.item_after_index == 14:
			layout.prop(props, "mat_gp_name14",text="")
		elif self.item_after_index == 15:
			layout.prop(props, "mat_gp_name15",text="")
		elif self.item_after_index == 16:
			layout.prop(props, "mat_gp_name16",text="")
		elif self.item_after_index == 17:
			layout.prop(props, "mat_gp_name17",text="")
		elif self.item_after_index == 18:
			layout.prop(props, "mat_gp_name18",text="")
		elif self.item_after_index == 19:
			layout.prop(props, "mat_gp_name19",text="")
		elif self.item_after_index == 20:
			layout.prop(props, "mat_gp_name20",text="")
		else:
			layout.label(text="Pass_Index_xx")



		layout.prop(self, 'item_after_index', text="")

	def execute(self, context):
		bpy.data.materials[self.item_name].pass_index = self.item_after_index

		return {'FINISHED'}


# アクティブマテリアルを設定
class AMLIST_OT_mat_set_active_index(Operator):
	bl_idname = "amlist.mat_set_active_index"
	bl_label = "Set Active Material"
	bl_description = ""
	bl_options = {'REGISTER', 'UNDO'}

	index : IntProperty()

	@classmethod
	def poll(cls, context):
		if bpy.context.view_layer.objects.active:
			obj = bpy.context.active_object
			if obj.type in {"MESH", "CURVE", "SURFACE", "META", "FONT","VOLUME","GPENCIL"}:
				if len(obj.data.materials):
					return True


	def invoke(self, context,event):
		obj = bpy.context.object
		if event.ctrl and ("EDIT" in bpy.context.mode):
			obj.active_material_index = self.index
			# obj.update_tag()
			bpy.ops.object.material_slot_assign()
			self.report({'INFO'}, "Assign Material to Select")
		else:
			obj.active_material_index = self.index
		return{'FINISHED'}
