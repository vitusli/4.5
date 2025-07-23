import bpy
import random # オブジェクトカラー・マテリアルビューポートカラーのランダムカラーに必要
from bpy.props import *
from bpy.types import Operator


# 1マテリアル作成、割り当てなし
class AMLIST_OT_mat_new_create_not_assign(Operator):
	bl_idname = "am_list.mat_new_create_not_assign"
	bl_label = "Create New Material (Not assign)"
	bl_description = "Create New Material (Not assign)"
	bl_options = {"REGISTER","UNDO"}

	random_color : BoolProperty(name="Random Color",description="")


	def draw(self, context):
		layout = self.layout
		row = layout.row(align=True)
		row.label(text="",icon="COLORSET_02_VEC")
		row.prop(self,"random_color")


	def execute(self, context):
		# 割当しないで新規作成
		mat = create_mat(self, None)
		self.report({'INFO'}, "Create [" + mat.name + "]")
		return{'FINISHED'}


# 1マテリアル作成
class AMLIST_OT_mat_new_create_one_mat(Operator):
	bl_idname = "am_list.mat_new_create_one_mat"
	bl_label = "Create New Material (One Material)"
	bl_description = "Assign One new material to select obj"
	bl_options = {"REGISTER","UNDO"}


	remove_slot : BoolProperty(name="Remove Old Slot",description="Remove all Material slots before assigning materials")
	random_color : BoolProperty(name="Random Color",description="")
	rename_mat_to_obj_name    : BoolProperty(name = "Rename to Object Name", description="Use Rename New Material Name to Object Name")


	@classmethod
	def poll(cls, context):
		return bpy.context.selected_objects


	def draw(self, context):
		layout = self.layout
		draw_mat_new_option_menu(self,layout)

	def execute(self, context):

		# 編集モードの場合
		fini = edit_mode_mat_assign(self)
		if fini:
			return{'FINISHED'}

		# 事前にスロットを削除
		if self.remove_slot:
			bpy.ops.am_list.mat_delete_slot()

		obj = bpy.context.view_layer.objects.active
		mat = create_mat(self, obj)
		if bpy.context.view_layer.objects.active.type in {'GPENCIL'}:
			bpy.data.materials.create_gpencil_data(mat)
			mat.grease_pencil.color = random_color(self.random_color)


		assign_count = 0
		for obj in bpy.context.selected_objects:
			if obj.type in {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT', 'VOLUME','GPENCIL'}:
				if not len(obj.data.materials): # 割り当てマテリアルがない
					obj.data.materials.append(mat)
					assign_count += 1

					if self.rename_mat_to_obj_name:
						mat.name = obj.name


		self.report({'INFO'}, "Create [ " + mat.name + " ] , Assigned to [ " +  str(assign_count) + " ] Objects")

		return{'FINISHED'}


# 複数マテリアル作成
class AMLIST_OT_mat_new_create_multi_mat(Operator):
	bl_idname = "am_list.mat_new_create_multi_mat"
	bl_label = "Create New Material (for each object)"
	bl_description = "Assign Multi new material to each select obj.\n(and Romdom Color Option)"
	bl_options = {"REGISTER","UNDO"}

	remove_slot : BoolProperty(name="Remove Old Slot",description="Remove all Material slots before assigning materials")
	random_color : BoolProperty(name="Random Color", default=True,description="")
	rename_mat_to_obj_name    : BoolProperty(name = "Rename to Object Name", description="Use Rename New Material Name to Object Name")

	@classmethod
	def poll(cls, context):
		return bpy.context.selected_objects


	def draw(self, context):
		layout = self.layout
		draw_mat_new_option_menu(self,layout)


	def execute(self, context):
		assign_count = 0

		# 編集モードの場合
		fini = edit_mode_mat_assign(self)
		if fini:
			return{'FINISHED'}

		# 事前にスロットを削除
		if self.remove_slot:
			bpy.ops.am_list.mat_delete_slot()


		old_actobj = bpy.context.view_layer.objects.active
		for obj in bpy.context.selected_objects:
			if obj.type in {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT', 'VOLUME','GPENCIL'}:
				if not len(obj.data.materials): # 割り当てマテリアルがない
					bpy.context.view_layer.objects.active = obj
					mat = create_mat(self, obj)

					if obj.type in {'GPENCIL'}:
						bpy.data.materials.create_gpencil_data(mat)
						col = random_color(self.random_color)
						mat.grease_pencil.color = col

					obj.data.materials.append(mat)
					assign_count += 1

					if self.rename_mat_to_obj_name:
						mat.name = obj.name

		bpy.context.view_layer.objects.active = old_actobj


		self.report({'INFO'}, "Create and Assigned to [ " +  str(assign_count) + " ] Items")
		return{'FINISHED'}


# 編集モードの場合は面に割り当て
def edit_mode_mat_assign(self):
	if not bpy.context.view_layer.objects.active:
		return
	obj = bpy.context.view_layer.objects.active
	if not obj.type in {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT', 'GPENCIL'}:
		return
	if not obj.mode == "EDIT": # 編集モードの場合は、割り当て
		return

	mat = create_mat(self, obj) # マテリアル作, obj成

	obj.data.materials.append(mat)
	obj.active_material_index = len(obj.material_slots) -1 # 最後のマテリアルスロットを選択
	if self.rename_mat_to_obj_name: # マテリアル名をオブジェクト名に変更
	  mat.name = bpy.context.view_layer.objects.active.name

	bpy.ops.object.material_slot_assign() # マテリアルを面に割り当て

	self.report({'INFO'}, "Create [ " + mat.name + " ] and Assigned to Face" )

	return {'FINISHED'}


# オプションメニュー
def draw_mat_new_option_menu(self,layout):
	row = layout.row(align=True)
	row.label(text="",icon="DRIVER_TRANSFORM")
	row.prop(self,"remove_slot")

	row = layout.row(align=True)
	row.label(text="",icon="COLORSET_02_VEC")
	row.prop(self,"random_color")

	row = layout.row(align=True)
	row.label(text="",icon="SORTALPHA")
	row.prop(self,"rename_mat_to_obj_name")


# マテリアル作成
def create_mat(self, obj):
	mat = bpy.data.materials.new(name="Material")
	mat.use_nodes=True

	random_col = random_color(self.random_color)

	if "Principled Volume" in mat.node_tree.nodes:
		tgt_nd = mat.node_tree.nodes["Principled Volume"]
		tgt_nd.inputs[0].default_value = random_col
		mat.diffuse_color = random_col

	elif "Principled BSDF" in mat.node_tree.nodes:
		tgt_nd = mat.node_tree.nodes["Principled BSDF"]
		tgt_nd.inputs[0].default_value = random_col
		mat.diffuse_color = random_col

	return mat


# ランダムカラー
def random_color(use_ramdom):
	props = bpy.context.scene.am_list

	if use_ramdom:
		r = random.random()
		g = random.random()
		b = random.random()
		mat_col = (r,g,b,True)

	else:
		mat_col = props.new_mat_color

	return mat_col
