import bpy
import re #正規表現
import bmesh
import random # オブジェクトカラー・マテリアルビューポートカラーのランダムカラーに必要
import os, numpy, urllib, math, shutil # ファイル名取得に必要
import rna_keymap_ui # キーマップリストに必要
from pathlib import Path

from bpy.props import *
from bpy.types import Menu, Operator, Panel, UIList, Scene, PropertyGroup, Object,  UIList
from bpy.app.handlers import persistent # マテリアル更新に必要
from ..ui.ui_uilist_img import AMLIST_UL_image



class AMLIST_OT_img_merge(Operator):
	bl_idname = "am_list.img_merge"
	bl_label = "Merge Duplicate Image (001,002...)"
	bl_description = "Merge images with duplicate names such as 001,002 ...\nBased on materials that do not have numbers such as 001,002 ... at the end of the line.\n(Only to Material nodes)"
	bl_options = {'REGISTER', 'UNDO'}


	img_name: StringProperty(default="", name = "Image Name")
	partition : StringProperty(default=".", name = "Partition Character")
	all_image : BoolProperty(default=False, name = "All Image")

	def invoke(self, context, event):
		if not len(context.selected_objects) == 0:
			self.old_name = bpy.context.object.active_material.name

		dpi_value = bpy.context.preferences.system.dpi
		return context.window_manager.invoke_props_dialog(self, width=dpi_value*3)

	def draw(self, context):
		layout = self.layout
		layout.prop( self, "all_image")
		if not self.all_image:
			layout.prop_search( self, "img_name", bpy.data, "images", text="Name")
		layout.prop( self, "partition")


	def execute(self, context):
		id = self.img_name # 番号のない主の名前にする

		if not self.all_image:
			for mat in bpy.data.materials:
				if mat.node_tree:
					for n in mat.node_tree.nodes:
						if n.type == 'TEX_IMAGE': # ノードの場合
							if n.image is None:
								print(mat.name,'has an image node with no image')

							else:
								if n.image.name.startswith(id):
									(base, sep, ext) = n.image.name.rpartition(self.partition) # rpartitionにより、文字列を分割し、[前の部分, 分割文字列, 後の部分]という形の変数を用意
									if ext.isnumeric(): # isnumericにより、数値かどうかを判定する
										if id in bpy.data.images: # マテリアルの中の、ベースの名前に該当するものを検索する
											# self.report({'INFO'}, "For object '%s' replace '%s' with '%s'" % (obj.name, n.image.name, base))
											n.image = bpy.data.images.get(id)  # ベースに置き換える
											# self.report({'INFO'}, base)


		else:
			for mat in bpy.data.materials:
				if mat.node_tree:
					for n in mat.node_tree.nodes:
						if n.type == 'TEX_IMAGE': # ノードの場合
							if n.image is None:
								print(mat.name,'has an image node with no image')
							# elif n.image.name[-3:].isdigit(): # スライスで、後ろから3つが数字の場合を取り出す
							# 	n.image = bpy.data.images[n.image.name[:-4]]
							else:
								(base, sep, ext) = n.image.name.rpartition(self.partition) # rpartitionにより、文字列を分割し、[前の部分, 分割文字列, 後の部分]という形の変数を用意
								if ext.isnumeric(): # isnumericにより、数値かどうかを判定する
									if base in bpy.data.images: # マテリアルの中の、ベースの名前に該当するものを検索する
										# self.report({'INFO'}, "For object '%s' replace '%s' with '%s'" % (obj.name, n.image.name, base))
										n.image = bpy.data.images.get(base)  # ベースに置き換える
										# self.report({'INFO'}, base)

								# for imgs in bpy.data.images:
								# 	if not base == None:
								# 		if imgs.name.startswith(base):
								# 			if imgs.name[-3:].isdigit():
								# 				print(imgs.name)
								# 				self.report({'INFO'}, imgs.name)
								# 				imgs.user_clear()


										# for imgs in bpy.data.images:
										# 	if imgs.name[-3:].isdigit():
										# 		print(imgs.name)
										# 		imgs.user_clear()


		return {'FINISHED'}


class AMLIST_OT_img_replace(Operator):
	bl_idname = "am_list.img_replace"
	bl_label = "Replace Image Node"
	bl_description = "Replace  image of a material Image node with another image "
	bl_options = {'REGISTER', 'UNDO'}

	old_name: StringProperty(default="", name = "Old Name")
	new_name: StringProperty(default="", name = "New Name")
	only_active_material_slot : BoolProperty(default=True, name = "Only Active Material Slot")

	def invoke(self, context, event):
		props = bpy.context.scene.am_list
		self.old_name = bpy.data.images[props.id_img].name

		dpi_value = bpy.context.preferences.system.dpi
		return context.window_manager.invoke_props_dialog(self, width=dpi_value*3)

	def draw(self, context):
		layout = self.layout
		layout.prop_search( self, "old_name", bpy.data, "images", text="Old")
		layout.prop_search( self, "new_name", bpy.data, "images", text="New")
		# if not bpy.context.view_layer.objects.active ==  None:
		layout.prop( self, "only_active_material_slot")
		# else:
		# 	layout.label(text="No Active Object",icon="NONE")

	def execute(self, context):
		old = bpy.data.images[self.old_name]
		new = bpy.data.images[self.new_name]

		if self.only_active_material_slot:
			for n in bpy.context.object.active_material.node_tree.nodes:
				if n.type == 'TEX_IMAGE':
					if n.image is None:
						self.report({'INFO'}, mat.name + 'has an image node with no image')
					else:
						if n.image == old:
							n.image = new

		else:
			for mat in bpy.data.materials:
				if mat.node_tree:
					for n in mat.node_tree.nodes:
						if n.type == 'TEX_IMAGE':
							if n.image is None:
								self.report({'INFO'}, mat.name + 'has an image node with no image')
							else:
								if n.image == old:
									n.image = new

		return {'FINISHED'}


class AMLIST_OT_img_move_folder_to_folder(Operator):
	bl_idname = "am_list.image_move_folder_to_folder"
	bl_label = "Move from a 'Target folder' → 'Another folder'"
	bl_description = "You can move to the specified folder from the 'Target' folder generated by Unpacking"
	bl_options = {'REGISTER'}

	target_folder_name : StringProperty(default="textures",name="Target Folder Name")
	folder_name : StringProperty(default="tex",name="Folder Name")

	# 本当に実行するかポップアップで聞く
	def invoke(self, context, event):
		wm = context.window_manager
		return wm.invoke_props_dialog(self)

	@classmethod
	def poll(cls, context):
		path = context.blend_data.filepath
		if (context.blend_data.filepath == ""):
			return False
		dir = os.path.dirname(path)
		# if (not os.path.isdir( os.path.join(dir, self.target_folder_name) )):
		# 	return False
		for img in bpy.data.images:
			if (img.filepath != ""):
				return True
		return False

	def execute(self, context):
		names = []
		for img in context.blend_data.images:
			if (img.filepath != ""):
				names.append(bpy.path.basename(img.filepath))
		tex_dir = os.path.join( os.path.dirname(context.blend_data.filepath), self.target_folder_name)
		backup_dir = os.path.join(os.path.dirname(context.blend_data.filepath), self.folder_name)
		if (not os.path.isdir(backup_dir)):
			os.mkdir(backup_dir)
		for name in os.listdir(tex_dir):
			path = os.path.join(tex_dir, name)
			if (not os.path.isdir(path)):
				if (names):
				# if (name not in names):
					src = path
					dst = os.path.join(path, backup_dir, name)
					shutil.move(src, dst)
					#パスが外れるので、 ファイルを探す
					bpy.ops.file.find_missing_files(find_all=False, directory=backup_dir,filter_image=True)
					# 画像を全リロード
					bpy.ops.am_list.reload_all_image()

					self.report(type={'INFO'}, message=name+"Isolate")
		return {'FINISHED'}


class AMLIST_OT_img_collect_all(Operator):
	bl_idname = "am_list.resave_all_image"
	bl_label = "Collect files to 'Textures' folder"
	bl_description = "All external files referenced by image data to resave textures folder"
	bl_options = {'REGISTER'}

	# 本当に実行するかポップアップで聞く
	def invoke(self, context, event):
		return context.window_manager.invoke_confirm(self, event)

	@classmethod
	def poll(cls, context):
		if (context.blend_data.filepath == ""):
			return False
		for img in bpy.data.images:
			if (img.filepath != ""):
				return True
		return False
	def execute(self, context):
		for img in context.blend_data.images:
			if (img.filepath != ""):
				try:
					img.pack()
					img.unpack()
				except RuntimeError:
					pass
		self.report(type={"INFO"}, message="fixed and stored in textures folder")
		return {'FINISHED'}


class AMLIST_OT_img_reload_all(Operator):
	bl_idname = "am_list.reload_all_image"
	bl_label = "Reload All Images"
	bl_description = "Reloads all image data referring to external file"
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		if (len(bpy.data.images) <= 0):
			return False
		for img in bpy.data.images:
			if (img.filepath != ""):
				return True
		return False

	def execute(self, context):
		for img in bpy.data.images:
			if (img.filepath != ""):
				img.reload()
				try:
					img.update()
				except RuntimeError:
					pass
		for area in context.screen.areas:
			area.tag_redraw()
		return {'FINISHED'}


# ソート順に変化したインデックスの並び方がいまいちわからんのでボツ
class AMLIST_OT_img_move_active_id(Operator):
	bl_idname = "am_list.image_move_active_id"
	bl_label = "Move Active Index"
	bl_description = ""
	bl_options = {"REGISTER","UNDO"}

	items = [
	("UP","Up",""),
	("DOWN","Down",""),
	]
	direction : EnumProperty(default="UP",name="Type",items= items)

	def execute(self, context):
		props = bpy.context.scene.am_list
		print()
		print()
		print()
		filtered_list = AMLIST_UL_image.get_props_filtered_items(None)
		if props.img_filter_sort_type == "NAME":
			ordered = [(idx, it) for idx, it in enumerate(filtered_list)]
		elif props.img_filter_sort_type == "USERS":
			_sort = [(idx, it) for idx, it in enumerate(filtered_list)]
			ordered = sorted(_sort, key=lambda x:x[1].users)
		elif props.img_filter_sort_type == "FILEPATH":
			_sort = [(idx, it) for idx, it in enumerate(filtered_list)]
			ordered = sorted(_sort, key=lambda x:x[1].filepath)
		elif props.img_filter_sort_type == "SIZE":
			_sort = [(idx, it) for idx, it in enumerate(filtered_list)]
			ordered = sorted(_sort, key=lambda x:x[1].size[0]*x[1].size[1])

		for i in ordered:
			print(333333333,i)


		next = False
		for id,(idx,item) in enumerate(ordered):
			if next:
				print("next__________",id,(idx,item))
				if 0 < idx < len(bpy.data.images) - 1:
					if self.direction == "UP":
						props.id_img = idx - 1
					else:
						props.id_img = idx + 1
				break
			if props.id_img == bpy.data.images.find(item.name):
				next = True
				print("now__________",id,(idx,item))
				continue


		return {'FINISHED'}



# ボツ
class AMLIST_OT_img_change_path_abs_rel(Operator):
	bl_idname = "am_list.image_change_path_abs_rel"
	bl_label = "Switch between absolute and relative paths"
	bl_description = ""
	bl_options = {"REGISTER","UNDO"}

	items = [
	("ABSOLUTE","Absolute",""),
	("RELATIVE","Relative",""),
	]
	type : EnumProperty(default="ABSOLUTE",name="Type",items= items)

	def invoke(self, context, event):
		dpi_value = bpy.context.preferences.system.dpi
		return context.window_manager.invoke_props_dialog(self, width=dpi_value*3)

	def draw(self, context):
		layout = self.layout
		row = layout.row(align=True)
		row.prop(self, "type",expand=True)
		num =  len([img for img in bpy.data.images if img.am_list.select])
		layout.label(text="Select Count : "+str(num),icon="NONE")


	def execute(self, context):
		props = bpy.context.scene.am_list
		for img in bpy.data.images:
			if img.am_list.select:
				p_data = Path(img.filepath).resolve()
				# if p_abs.is_absolute():
				if self.type == "ABSOLUTE":
					# img.filepath = (p_data.absolute())
					img.filepath = bpy.path.abspath(img.filepath)
				elif self.type == "RELATIVE":
					# img.filepath = p_data.relative_to(os.path.dirname(bpy.data.filepath))
					img.filepath = bpy.path.relpath(img.filepath)

		return {'FINISHED'}


class AMLIST_OT_img_rename_filename(Operator):
	bl_idname = "am_list.rename_image_file_name"
	bl_label = "Rename Image name → File name"
	bl_description = "Rename the image name to the reference image file name"
	bl_options = {'REGISTER', 'UNDO'}

	img_all : BoolProperty(name="All Image")
	isExt : BoolProperty(name="Include Extension", default=True)

	# @classmethod
	# def poll(self, context):
	# 	props = bpy.context.scene.am_list
	# 	if self.img_all:
	# 		if (len(bpy.data.images) <= 0):
	# 			return False
	# 		for img in bpy.data.images:
	# 			if (img.filepath != ""):
	# 				return True
	# 		return False
	#
	#
	# 	else:
	# 		img = bpy.data.images[props.id_img]
	#
	# 		if (not img):
	# 			return False
	# 		if (img.filepath == ""):
	# 			return False
	# 		return True

	def invoke(self, context, event):
		wm = context.window_manager
		return wm.invoke_props_dialog(self)

	def execute(self, context):
		props = bpy.context.scene.am_list

		if self.img_all:
			img = bpy.data.images

			for img in  bpy.data.images:
				if img.source == 'FILE':
					name = bpy.path.basename(img.filepath_raw)
					if (not self.isExt):
						name, ext = os.path.splitext(name)
					try:
						img.name = name
					except: pass

		else:
			img = bpy.data.images[props.id_img]
			if img.source == 'RENDER_RESULT':
				img.name = 'Render Result'
				return {'FINISHED'}

			# img = context.edit_image
			name = bpy.path.basename(img.filepath_raw)
			if (not self.isExt):
				name, ext = os.path.splitext(name)
			try:
				img.name = name
			except: pass
		return {'FINISHED'}
