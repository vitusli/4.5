import bpy
from bpy.props import *
from bpy.types import Operator
from bpy_extras.io_utils import (
		ImportHelper,
		)

from ..ui.mat.ui_main_mat_mini_socket import get_output_linked_shader_node


# 画像テクスチャをセットアップ(新規画像読み込み)
class AMLIST_OT_setup_one_tex_new_img(Operator, ImportHelper):
	bl_idname = "am_list.setup_one_tex_new_img"
	bl_label = "One Texture Setup"
	bl_description = "Load an image, create a material and set the image as a texture"
	bl_options = {'REGISTER', 'UNDO'}

	use_filter : BoolProperty(default=True, options={'HIDDEN'},)
	use_filter_image : BoolProperty(default=True, options={'HIDDEN'},)

	filename_ext = ".png"
	filter_glob : StringProperty( default="*.bmp;*.rgb;*.png;*.jpg;*.jp2;*.tga;*.cin;*.dpx;*.exr;*.hdr;*.ti;", options={'HIDDEN'}, )


	items = [
	("Base Color","Base Color",""),
	("Metallic","Metallic",""),
	("Roughness","Roughness",""),
	("Normal","Normal",""),
	]
	pri_socket_type : EnumProperty(default="Base Color",name = "Soket Type", items= items)

	items = [
	("ShaderNodeTexImage","Image",""),
	("ShaderNodeTexNoise","Noise",""),
	("ShaderNodeTexWave","Wave",""),
	("ShaderNodeTexVoronoi","Voronoi",""),
	("ShaderNodeTexMusgrave","Musgrave",""),
	("ShaderNodeTexGradient","Gradient",""),
	("ShaderNodeTexMagic","Magic",""),
	("ShaderNodeTexChecker","Checker",""),
	("ShaderNodeTexBrick","Brick",""),
	]
	node_type : EnumProperty(default="ShaderNodeTexImage",name = "Node Type", items= items)
	mat_name : StringProperty(name="Material Name")

	# @classmethod
	# def poll(cls, context):
	# 	if bpy.context.view_layer.objects.active:
	# 		obj = bpy.context.view_layer.objects.active
	# 		if obj.type in {"MESH", "CURVE", "SURFACE", "META", "FONT", "VOLUME"}:
	# 			return True


	def execute(self, context):
		obj = bpy.context.object
		# old_edit = False
		# if obj.mode == "EDIT":
		# 	bpy.ops.object.mode_set(mode="OBJECT")
		# 	old_edit = True

		mat = add_mat(self,obj)
		loc_y = get_socket_location(self)
		setup_node(self, obj, mat, loc_y, None)

		# if old_edit:
		# 	bpy.ops.object.mode_set(mode="EDIT")
		return{'FINISHED'}


# マテリアルを追加
def add_mat(self, obj):
	# # 編集モードの場合
	# if len(obj.data.materials) and obj.mode == "EDIT":
	# 	bpy.ops.object.material_slot_add()
	# 	mat = bpy.data.materials.new(name="mat")
	# 	obj.active_material = mat
	# 	bpy.ops.object.material_slot_assign()
	# 	mat.use_nodes = True


	# オブジェクトのマテリアルでない場合
	if not self.mat_name in obj.data.materials:
		mat = bpy.data.materials[self.mat_name]

	# オブジェクトのマテリアルスロットにマテリアルがある場合
	elif self.mat_name in obj.data.materials:
		mat = obj.data.materials[self.mat_name]

	# マテリアルがある場合・空スロットでない場合
	elif len(obj.data.materials) and not obj.data.materials[obj.active_material_index] == None:
		mat = obj.data.materials[obj.active_material_index]

	# 空のマテリアルスロット
	elif len(obj.data.materials) and obj.data.materials[obj.active_material_index] == None:
		mat = bpy.data.materials.new(name="mat")
		mat.use_nodes = True
		obj.data.materials[obj.active_material_index] = mat

	# マテリアル未所持
	else:
		mat = bpy.data.materials.new(name="mat")
		mat.use_nodes = True
		obj.data.materials.append(mat)

	return mat


# ソケットタイプを取得
def get_socket_location(self):
	if self.pri_socket_type == "Base Color":
		loc_y = 400
	elif self.pri_socket_type == "Metallic":
		loc_y = 100
	elif self.pri_socket_type == "Roughness":
		loc_y = -200
	elif self.pri_socket_type == "Normal":
		loc_y = -400
	# elif self.pri_socket_type == "OTHER":
	# 	loc_y = -600

	return loc_y


# ノードをセットアップ
def setup_node(self, obj, mat, loc_y, img_name):
	# ノードセットアップ
	nodes = mat.node_tree.nodes
	links = mat.node_tree.links
	loc_x = -250


	main_shader_nd, error_text, is_volume = get_output_linked_shader_node(mat)
	if error_text:
		self.report({'WARNING'}, error_text)
		return


	# image
	nd_tex = nodes.new(self.node_type)
	nd = nd_tex
	if self.node_type == "ShaderNodeTexImage":
		if img_name:
			img =  bpy.data.images[img_name]
		else:
			img = bpy.data.images.load(self.filepath, check_existing=False)
		nd.image = img

		if self.pri_socket_type == "Base Color":
			if self.pri_socket_type in main_shader_nd.inputs:
				pri_socket_type = self.pri_socket_type
			else:
				pri_socket_type = "Color"
		else:
			if self.pri_socket_type in main_shader_nd.inputs:
				pri_socket_type = self.pri_socket_type
			else:
				self.report({'WARNING'}, "Not found Socket Name [%s]" % self.pri_socket_type)


	nd.location.x = loc_x + -50
	nd.location.y = loc_y
	if pri_socket_type == "Normal":
		if self.node_type == "ShaderNodeTexImage":
			nd_tex.image.colorspace_settings.is_data = True # Non-Color
			nml_nd = nodes.new(type='ShaderNodeNormalMap')
			links.new(nd_tex.outputs[0], nml_nd.inputs[1])
			links.new(nml_nd.outputs[0], main_shader_nd.inputs[pri_socket_type])
		else:
			nml_nd = nodes.new(type='ShaderNodeBump')
			links.new(nd_tex.outputs[0], nml_nd.inputs[2])
			links.new(nml_nd.outputs[0], main_shader_nd.inputs[pri_socket_type])

		nml_nd.location.x = loc_x + -50
		nml_nd.location.y = loc_y - 300

	else:
		links.new(nd.outputs[0], main_shader_nd.inputs[pri_socket_type])


	# mapping
	n_l = [n for n in nodes if n.type == "MAPPING"]
	if n_l:
		nd_map = n_l[0]
	else:
		nd_map = nodes.new("ShaderNodeMapping")
		nd = nd_map
		nd.location.x = loc_x * 2
		nd.location.y = loc_y

	links.new(nd_map.outputs[0], nd_tex.inputs[0])


	# TexCoord
	if not n_l:
		nd_coord = nodes.new("ShaderNodeTexCoord")
		nd = nd_coord
		nd.location.x = loc_x * 3
		nd.location.y = loc_y
		if is_volume:
			links.new(nd_coord.outputs[0], nd_map.inputs[0])
		else:
			links.new(nd_coord.outputs[2], nd_map.inputs[0])


# ノードを削除(再リンク)
class AMLIST_OT_node_remove(Operator):
	bl_idname = "amlist.node_remove"
	bl_label = "Remove Node"
	bl_description = ""
	bl_options = {'REGISTER', 'UNDO'}

	input_socket : StringProperty()
	node_name : StringProperty()
	reconnect : BoolProperty(name="Reconnect")
	mat_name : StringProperty(name="Material Name")

	# @classmethod
	# def poll(cls, context):
	# 	if bpy.context.view_layer.objects.active:
	# 		obj = bpy.context.view_layer.objects.active
	# 		if obj.type in {"MESH", "CURVE", "SURFACE", "META", "FONT","VOLUME"}:
	# 			if len(obj.data.materials):
	# 				return obj.data.materials[obj.active_material_index].use_nodes


	def execute(self, context):
		mat = bpy.data.materials[self.mat_name]
		nodes = mat.node_tree.nodes
		links = mat.node_tree.links


		tgt_nd = nodes[self.node_name]
		del_node_name = tgt_nd.name

		if self.reconnect:
			to_links = [
				l for l in links
				if l.to_node == tgt_nd]
			from_links = [
				l for l in links
				if l.from_node == tgt_nd]

			if to_links and from_links:
				links.new(to_links[0].from_socket, from_links[0].to_socket)

		nodes.remove(tgt_nd) # 削除
		self.report({'INFO'}, "Remove [%s]" % del_node_name)
		return{'FINISHED'}
