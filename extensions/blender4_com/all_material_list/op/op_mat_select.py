import bpy, bmesh
from bpy.props import *
from bpy.types import Operator
from ..ui.mat.ui_main_mat_index_create_list import *
from ..utils.utils import set_data_list


class AMLIST_OT_item_select(Operator):
	bl_idname = "am_list.mat_select"
	bl_label = "Select"
	bl_description = "Select Object.\nShift : Extend Select \nAlt : Deselect"
	bl_options = {"REGISTER","UNDO"}

	# tgt_index : IntProperty(default=0, name = "Index")
	item_name : StringProperty(name = "Name")

	items = [
	("MATERIAL","Material",""),
	("OBJECT","Object",""),
	("SCENE","Scene",""),
	("ACTION","Action",""),
	]
	data_type : EnumProperty(default="MATERIAL",name="Type",items= items)
	select_image_node_name : StringProperty()

	def invoke(self, context, event):
		if self.data_type == "MATERIAL":
			select_mat_main(self, event)

		elif self.data_type == "OBJECT":
			select_obj(self, event)

		elif self.data_type == "ACTION":
			select_action(self, event)

		elif self.data_type == "SCENE":
			bpy.context.window.scene = bpy.data.scenes[self.item_name]

		return{'FINISHED'}


# オブジェクト
def select_obj(self, event):
	obj = bpy.data.objects[self.item_name]
	if event.shift:
		obj.select_set(True)
	elif event.alt:
		obj.select_set(False)

	elif not event.shift and not event.alt:
		for o in bpy.context.selected_objects:
			o.select_set(False)
		obj.select_set(True)

	else:
		obj.select_set(True)


	try: bpy.context.view_layer.objects.active = bpy.context.selected_objects[-1]
	except: self.report({'INFO'}, "Could not select")


# アクション
def select_action(self, event):
	# ユーザー数をカウント
	if bpy.data.actions[self.item_name].use_fake_user:
		user_count = bpy.data.actions[self.item_name].users - 1
	else:
		user_count = bpy.data.actions[self.item_name].users


	# 拡張選択
	if not event.shift and not event.alt:
		for o in bpy.context.selected_objects:
			o.select_set(False)

	# 選択
	obj_count = len(bpy.context.selected_objects)
	filter_type = [obj for obj in bpy.context.scene.collection.all_objects if obj.animation_data and obj.animation_data.action == bpy.data.actions[self.item_name]]
	for obj in filter_type:
		if event.alt:
			obj.select_set(False)
		else:
			obj.select_set(True)

	# アクティブ選択
	if not len(bpy.context.selected_objects)==0:
		bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]



	# 選択数を表示
	if len(bpy.context.selected_objects) - obj_count < user_count or len(bpy.context.selected_objects) == 0: #選択数よりユーザー数が多い場合
		# (選択数 - 古い選択数)  / ユーザー数
		self.report({'INFO'}, "Select " + str(len(bpy.context.selected_objects) - obj_count) + '/' + str(user_count))


# マテリアル
def select_mat_main(self, event):
	if bpy.context.object:
		if bpy.context.object.mode == "EDIT":
			select_mat_edit(self, event)

		else:
			select_mat_objmode(self, event)
	else:
		select_mat_objmode(self, event)


	# 画像リストからマテリアル選択した場合、対象の画像ノードをノード内で選択する
	if self.select_image_node_name:
		tgt_mat = bpy.data.materials[self.item_name]
		tgt_img = bpy.data.images[self.select_image_node_name]
		for nd in tgt_mat.node_tree.nodes:
			nd.select = False
			if nd.type in {"TEX_IMAGE","TEX_ENVIRONMENT"}:
				if nd.image == tgt_img:
					nd.select = True
					tgt_mat.node_tree.nodes.active = nd





def select_mat_objmode(self, event):
	tgt_item = bpy.data.materials[self.item_name]

	# 事前に選択解除
	if not event.shift:
		for o in bpy.context.selected_objects:
			o.select_set(False)


	obj_count = len(bpy.context.selected_objects)
	# オブジェクトの中の
	for o in bpy.context.view_layer.objects:
		# マテリアルスロットの
		for i,slot in enumerate(o.material_slots):
			# マテリアルが同じ
			if slot.material == tgt_item:
				  o.select_set(True)
				  o.active_material_index = i

	# アクティブ選択
	if bpy.context.selected_objects:
		bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]


	# 選択数を表示
	# レイヤーやオブジェクトが隠されていると、選択出来ない場合があるので、警告する
	if tgt_item.use_fake_user:
		user_count = tgt_item.users - 1
	else:
		user_count = tgt_item.users
	sel_count = len(bpy.context.selected_objects)
	if sel_count - obj_count < user_count or sel_count == 0: #選択数よりユーザー数が多い場合
		# (選択数 - 古い選択数)  / ユーザー数
		self.report({'INFO'}, "Select " + str(sel_count - obj_count) + '/' + str(user_count))


# 編集モード
def select_mat_edit(self, event):
	tgt_item = bpy.data.materials[self.item_name]
	obj = bpy.context.object

	faces_mat_c1 = []
	bm = bmesh.from_edit_mesh(obj.data)
	# 対象マテリアルと、オブジェクトの持つマテリアルのIDが一致するものをリストにする
	mat_id_list = [id for id, mat in enumerate(obj.data.materials) if mat == tgt_item]

	# 面のマテリアルインデックスと一致するものを選択
	for face in bm.faces:
		if face.material_index in mat_id_list:
			faces_mat_c1.append(face)
			if event.alt:
				face.select = False
			else:
				face.select = True
	if not faces_mat_c1:
		self.report({'WARNING'}, "No Assgined material")
		return {'CANCELLED'}

	bmesh.update_edit_mesh(obj.data)
