import bpy, bmesh
from bpy.props import *
from bpy.types import Operator
from ..ui.mat.ui_main_mat_index_create_list import *
from ..utils.utils import set_data_list


class AMLIST_OT_item_asobj_select(Operator):
	bl_idname = "am_list.asobj_select"
	bl_label = "Select"
	bl_description = "Select Object.\nShift : Extend Select \nAlt : Deselect"
	bl_options = {"REGISTER","UNDO"}

	item_name : StringProperty(name = "Name")
	mat_name : StringProperty()


	def invoke(self, context, event):
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


		try:
			bpy.context.view_layer.objects.active = bpy.context.selected_objects[-1]

			# set active mat slot
			if self.mat_name:
				act_obj = bpy.context.view_layer.objects.active
				tgt_mat = bpy.data.materials[self.mat_name]
				for i,ms in enumerate(act_obj.material_slots):
					if ms.material == tgt_mat:
						act_obj.active_material_index = i

		except:
			self.report({'INFO'}, "Could not select")


		return{'FINISHED'}


class AMLIST_OT_item_rename(Operator):
	bl_idname = "am_list.item_rename"
	bl_label = "Rename Item"
	bl_description = ""
	bl_options = {'REGISTER','UNDO'}

	item_name : StringProperty(name = "Before Name")
	item_after_name : StringProperty(name = "After Name")
	type : StringProperty(name = "Type")

	@classmethod
	def poll(self, context):
		return True

	def invoke(self, context, event):
		wm = context.window_manager
		self.item_after_name = self.item_name
		return wm.invoke_props_dialog(self,width=200)

	def draw(self, context):
		layout = self.layout
		layout.prop(self, 'item_after_name', text="")

	def execute(self, context):
		if self.type == "mat":
			bpy.data.materials[self.item_name].name = self.item_after_name
		else:
			bpy.data.objects[self.item_name].name = self.item_after_name

		return {'FINISHED'}


class AMLIST_OT_item_delete(Operator):
	bl_idname = "am_list.item_delete"
	bl_label = "Item Delete"
	bl_description = "Delete the item from within project file.\nThis deletion does not involve the fake user and is immediate"
	bl_options = {"REGISTER","UNDO"}

	type : StringProperty(name = "Type")
	item_name : StringProperty(name = "Type")

	def execute(self, context):
		props = bpy.context.scene.am_list

		data_list = set_data_list(self)

		item = data_list[self.item_name]
		if item:
			data_list.remove(item, do_unlink=True)

		if self.type == "img":
			if len(bpy.data.images):
				props.id_img = -1
			if props.id_img + 1 > len(bpy.data.images):
				props.id_img = len(bpy.data.images) -1

		return{'FINISHED'}


class AMLIST_OT_item_delete_0(Operator):
	bl_idname = "am_list.del_0_mat"
	bl_label = "Delete 0 User Item"
	bl_description = "Clean 0 user Item in Project"
	bl_options = {"REGISTER","UNDO"}

	type : StringProperty(name = "Type")

	# 本当に実行するかポップアップで聞く
	def invoke(self, context, event):
		return context.window_manager.invoke_confirm(self, event)

	def execute(self, context):
		data_list = set_data_list(self)

		for item in data_list:
			if not item.users:
				data_list.remove(item)

		return {'FINISHED'}


class AMLIST_OT_item_toggle_fake_user(Operator):
	bl_idname = "am_list.toggle_fake_user"
	bl_label = "Toggle Fake User"
	bl_options = {"REGISTER","UNDO"}

	mat_id_name : IntProperty(default=0, name = "mat name", description = "mat name")
	type : IntProperty(default=1, name = "Type")

	def execute(self, context):
		props = bpy.context.scene.am_list
		id = self.mat_id_name


		if self.type == 1:
			mat = bpy.data.materials[id]
		if self.type == 2:
			mat = bpy.data.worlds[id]
		if self.type == 3:
			mat = bpy.data.images[id]

		if mat.use_fake_user:
			mat.use_fake_user = False
		else:
			mat.use_fake_user = True



		return{'FINISHED'}


class AMLIST_OT_item_hide_render(Operator):
	bl_idname = "am_list.item_render"
	bl_label = "Render Item"
	bl_description = ""
	bl_options = {'REGISTER','UNDO'}

	item_name : StringProperty(name = "Item Name")

	def execute(self, context):
		obj = bpy.data.objects[self.item_name]

		if obj.hide_render:
			obj.hide_render = False
		else:
			obj.hide_render = True

		return {'FINISHED'}


class AMLIST_OT_item_hide_select(Operator):
	bl_idname = "am_list.item_hide_select"
	bl_label = "Toggle Select Item"
	bl_description = ""
	bl_options = {'REGISTER','UNDO'}

	item_name : StringProperty(name = "Item Name")

	def execute(self, context):
		obj = bpy.data.objects[self.item_name]

		if obj.hide_select:
			obj.hide_select = False
		else:
			obj.hide_select = True

		return {'FINISHED'}


class AMLIST_OT_item_hide_set(Operator):
	bl_idname = "am_list.item_hide_set"
	bl_label = "Toggle Hide Item"
	bl_description = "ctrl: Disable render other than specified item\nalt: Hide viewport setting except specified item"
	bl_options = {'REGISTER','UNDO'}

	item_name : StringProperty(name = "Item Name")
	type : StringProperty(name="Type")

	def invoke(self, context,event):
		sc = bpy.context.scene
		props = bpy.context.scene.am_list
		item_obj = bpy.data.objects[self.item_name]

		if self.type in {"light_l", "light_p", "cam"}:
			if event.alt or event.ctrl:
				filter_type = []
				if self.type == "cam":
					if props.cam_filter_type=="Selected":
						filter_type = bpy.context.selected_objects
					elif props.cam_filter_type=="Scene":
						filter_type = bpy.context.scene.collection.all_objects
					elif props.cam_filter_type=="All_Data":
						filter_type = bpy.data.objects
						self.report({'INFO'}, "Processing has been performed on 'all objcet data'")
					elif props.cam_filter_type=="Collection":
						colle = props.cam_filter_colle
						if colle:
							filter_type = colle.objects

					data_list = [obj for obj in filter_type if not obj.name == self.item_name if obj.type == "CAMERA"]

				if self.type == "light_l":
					if props.light_l_filter_type=="Selected":
						filter_type = bpy.context.selected_objects
					elif props.light_l_filter_type=="Scene":
						filter_type = bpy.context.scene.collection.all_objects
					elif props.light_l_filter_type=="All_Data":
						filter_type = bpy.data.objects
						self.report({'INFO'}, "Processing has been performed on 'all objcet data'")
					elif props.light_l_filter_type=="Collection":
						colle = props.light_l_filter_colle
						if colle:
							filter_type = colle.objects

					data_list = [obj for obj in filter_type if not obj.name == self.item_name if obj.type == "LIGHT"]

				if self.type == "light_p":
					if props.light_p_filter_type=="Selected":
						filter_type = bpy.context.selected_objects
					elif props.light_p_filter_type=="Scene":
						filter_type = bpy.context.scene.collection.all_objects
					elif props.light_p_filter_type=="All_Data":
						filter_type = bpy.data.objects
						self.report({'INFO'}, "Processing has been performed on 'all objcet data'")
					elif props.light_p_filter_type=="Collection":
						colle = props.light_p_filter_colle
						if colle:
							filter_type = colle.objects

					data_list = [obj for obj in filter_type if not obj.name == self.item_name if obj.type == "LIGHT_PROBE"]

				view = [obj for obj in data_list if not obj.hide_viewport]
				ren = [obj for obj in data_list if not obj.hide_render]

				#####################################
				if event.alt:
					if any(view): # 1つ以上Trueならば普通に実行
						for obj in data_list:
							obj.hide_viewport = True

						item_obj.hide_viewport = False


						if self.type == "light_l":
							if props.light_l_only_hide_darken_world:
								sc.world.color = (0,0,0)
								sc.world.use_nodes = False
						self.report({'INFO'}, "Only Viewport")
					else:
						for obj in data_list:
								obj.hide_viewport = False

						if self.type == "light_l":
							if props.light_l_only_hide_darken_world:
								sc.world.color = (0.5,0.5,0.5)
								sc.world.use_nodes = True


						self.report({'INFO'}, "Only Viewport")
				#####################################
				if event.ctrl:
					if any(ren): # 1つ以上Trueならば普通に実行
						for obj in data_list:
							obj.hide_render = True

						item_obj.hide_render = False

						self.report({'INFO'}, "Only Render")
					else:
						for obj in data_list:
								obj.hide_render = False

						self.report({'INFO'}, "Only Render")



			else:
				#####################################
				if item_obj.hide_get():
					item_obj.hide_set(False)
				else:
					item_obj.hide_set(True)

		else:
			#####################################
			if item_obj.hide_get():
				item_obj.hide_set(False)
			else:
				item_obj.hide_set(True)

		return {'FINISHED'}


class AMLIST_OT_item_hide_viewport(Operator):
	bl_idname = "am_list.item_hide_viewport"
	bl_label = "Toggle Viewport Item"
	bl_description = ""
	bl_options = {'REGISTER','UNDO'}

	item_name : StringProperty(name = "Item Name")

	def execute(self, context):

		if bpy.data.objects[self.item_name].hide_viewport:
			bpy.data.objects[self.item_name].hide_viewport = False
		else:
			bpy.data.objects[self.item_name].hide_viewport = True

		return {'FINISHED'}


class AMLIST_OT_uidetail_toggle(Operator):
	bl_idname = "am_list.uidetail_toggle"
	bl_label = "asobj_toggle"

	item : StringProperty(name="Name")
	type : StringProperty(name="Type")

	def execute(self, context):
		if self.type =="mat":
			target_item = bpy.data.materials[self.item]

		elif self.type =="light_l":
			target_item = bpy.data.objects[self.item]

		elif self.type =="light_p":
			target_item = bpy.data.objects[self.item]

		elif self.type =="cam":
			target_item = bpy.data.objects[self.item]
		elif self.type =="sc_l":
			target_item = bpy.data.scenes[self.item]
		elif self.type =="action":
			target_item = bpy.data.actions[self.item]


		if target_item.am_list.uidetail_toggle:
			target_item.am_list.uidetail_toggle = False
		else:
			target_item.am_list.uidetail_toggle = True


		return{'FINISHED'}

gl_open = False

class AMLIST_OT_uidetail_toggle_all(Operator):
	bl_idname = "am_list.uidetail_toggle_all"
	bl_label = "All Open / Close"
	bl_description = "All Open / Close advanced options"

	type : StringProperty(name="Type")
	open : BoolProperty(name="Open")

	def execute(self, context):
		global gl_open
		self.open = gl_open
		gl_open = not self.open

		props = bpy.context.scene.am_list
		if self.type in ("mat","mat_assigned_obj"):
			data_list = create_list(True)


		elif self.type =="light_l":
			filter_type = []
			props.light_l_uidetail_toggle_status = not self.open

			if props.light_l_filter_type=="Selected":
				filter_type = bpy.context.selected_objects
			elif props.light_l_filter_type=="Scene":
				filter_type = bpy.context.scene.collection.all_objects
			elif props.light_l_filter_type=="All_Data":
				filter_type = bpy.data.objects
			elif props.light_l_filter_type=="View_Layer":
				filter_type = bpy.context.view_layer.objects
			elif props.light_l_filter_type=="Collection":
				colle = props.light_l_filter_colle
				if colle:
					filter_type = colle.objects

			data_list = [obj for obj in filter_type if obj.type == "LIGHT"]


		elif self.type =="light_p":
			filter_type = []
			props.action_uidetail_toggle_status = not self.open

			if props.light_p_filter_type=="Selected":
				filter_type = bpy.context.selected_objects
			elif props.light_p_filter_type=="Scene":
				filter_type = bpy.context.scene.collection.all_objects
			elif props.light_p_filter_type=="All_Data":
				filter_type = bpy.data.objects
			elif props.light_p_filter_type=="Collection":
				colle = props.light_l_filter_colle
				if colle:
					filter_type = colle.objects

			data_list = [obj for obj in filter_type if obj.type == "LIGHT_PROBE"]


		elif self.type =="cam":
			filter_type = []
			props.cam_uidetail_toggle_status = not self.open

			if props.cam_filter_type=="Selected":
				filter_type = bpy.context.selected_objects
			elif props.cam_filter_type=="Scene":
				filter_type = bpy.context.scene.collection.all_objects
			elif props.cam_filter_type=="All_Data":
				filter_type = bpy.data.objects
			elif props.light_l_filter_type=="View_Layer":
				filter_type = bpy.context.view_layer.objects
			elif props.cam_filter_type=="Collection":
				colle = props.light_l_filter_colle
				if colle:
					filter_type = colle.objects

			data_list = [obj for obj in filter_type if obj.type == "CAMERA"]

		elif self.type =="sc_l":
			data_list = [sc for sc in bpy.data.scenes]
		elif self.type =="action":
			data_list = [sc for sc in bpy.data.actions]
			props.action_uidetail_toggle_status = not self.open


		if self.type == "mat":
			for i in data_list:
				if self.open:
					i.am_list.uidetail_node_toggle = True
				else:
					i.am_list.uidetail_node_toggle = False
		if self.type == "img":
			for i in bpy.data.images:
				if self.open:
					i.am_list.uidetail_toggle = True
				else:
					i.am_list.uidetail_toggle = False


		elif self.type == "mat_assigned_obj":
			for i in data_list:
				if self.open:
					i.am_list.uidetail_toggle = True
				else:
					i.am_list.uidetail_toggle = False


		else:
			for i in data_list:
				if self.open:
					i.am_list.uidetail_toggle = True
				else:
					i.am_list.uidetail_toggle = False



		return{'FINISHED'}
