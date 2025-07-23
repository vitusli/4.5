import bpy
from bpy.props import *
from bpy.types import Operator
from ..ui.ui_popup import *
from ..ui.ui_hide import *


class AMLIST_OT_Popup_hide_compact(Operator):
	bl_idname = "am_list.popup_hide_compact"
	bl_label = "Hide With Compact Menu"
	bl_options = {'REGISTER','UNDO'}

	def invoke(self, context, event):
		dpi_value = bpy.context.preferences.system.dpi
		return context.window_manager.invoke_props_dialog(self, width=dpi_value*2)

	def draw(self, context):
		layout = self.layout
		hide_compact(self,context,layout)

	def execute(self, context):
		return {'FINISHED'}


class AMLIST_OT_Popup_hide_panel(Operator):
	bl_idname = "am_list.popup_hide_panel"
	bl_label = "Display in panel menu mode"
	bl_options = {'REGISTER','UNDO'}

	def invoke(self, context, event):
		dpi_value = bpy.context.preferences.system.dpi
		return context.window_manager.invoke_props_dialog(self, width=dpi_value*2)

	def draw(self, context):
		layout = self.layout
		hide_panel(self,context,layout)

	def execute(self, context):
		return {'FINISHED'}


class AMLIST_OT_filter_exclusion(Operator):
	bl_idname = "am_list.filter_exclusion"
	bl_label = "Exclusion '^(?!.*TEST).+$'"
	bl_description = "Exclude what the 'TEST' string contains"
	bl_options = {'REGISTER', 'UNDO'}

	type:StringProperty(default="",name="Type")

	def execute(self, context):
		props = bpy.context.scene.am_list



		exec_text = "props."+self.type+"_filter = \"^(?!.*\" + props."+self.type+"_filter + \").+$\""
		exec(exec_text)

		return {'FINISHED'}


class AMLIST_OT_filter_first_match(Operator):
	bl_idname = "am_list.first_match"
	bl_label = "First match '^TEST~'"
	bl_description = "First match '^TEST~'"
	bl_options = {'REGISTER', 'UNDO'}

	type:StringProperty(default="",name="Type")

	def execute(self, context):
		props = bpy.context.scene.am_list

		exec_text = "props."+self.type+"_filter = \"^\" + props."+self.type+"_filter"

		exec(exec_text)

		return {'FINISHED'}


class AMLIST_OT_filter_trailing_match(Operator):
	bl_idname = "am_list.trailing_match"
	bl_label = "Trailing match '~TEST$'"
	bl_description = "Trailing match '~TEST$'"
	bl_options = {'REGISTER', 'UNDO'}

	type:StringProperty(default="",name="Type")

	def execute(self, context):
		props = bpy.context.scene.am_list


		exec_text = "props."+self.type+"_filter = props."+self.type+"_filter + \"$\""

		exec(exec_text)

		return {'FINISHED'}


class AMLIST_OT_filter_dot_match(Operator):
	bl_idname = "am_list.dot_match"
	bl_label = "Dot match '\.'"
	bl_description = "Dot match '\.'"
	bl_options = {'REGISTER', 'UNDO'}

	type:StringProperty(default="",name="Type")

	def execute(self, context):
		props = bpy.context.scene.am_list


		exec_text = "props."+self.type+"_filter = \"\.\""

		exec(exec_text)

		return {'FINISHED'}


class AMLIST_OT_world_assign(Operator):
	bl_idname = "am_list.world_assign"
	bl_label = "Assign World"
	bl_options = {"REGISTER","UNDO"}

	mat_id_name : IntProperty(default=0, name = "mat name", description = "mat name")

	def execute(self, context):
		props = bpy.context.scene.am_list
		id = self.mat_id_name

		# id = bpy.context.scene.extra_material_list.world_id
		if id < len(bpy.data.worlds):
			world = bpy.data.worlds[id]
			bpy.context.scene.world = world

		return{'FINISHED'}


class AMLIST_OT_cam_set_view(Operator):
	bl_idname = "am_list.cam_set_view"
	bl_label = "Set View"
	bl_options = {"REGISTER","UNDO"}

	item_name : StringProperty(name = "Name")

	def execute(self, context):

		props = bpy.context.scene.am_list

		for o in bpy.context.selected_objects:
			o.select_set(False)
		bpy.data.objects[self.item_name].select_set(True)
		try: bpy.context.view_layer.objects.active = bpy.context.selected_objects[-1]
		except:
			self.report({'INFO'}, "Could not select")
			return{'FINISHED'}

		bpy.ops.view3d.object_as_camera()

		return{'FINISHED'}


class AMLIST_OT_light_energy_twice(Operator):
	bl_idname = "am_list.energy_twice"
	bl_label = "*2 or 1/2 energy"
	bl_description = "Increase or decrease the intensity of the light or make fine adjustments.\nshift : *1.5 or 3/4\nalt : *1.1 or *0.9\nctrl : Round energy value"
	bl_options = {"REGISTER","UNDO"}

	twice : BoolProperty(default=True,name = "Twice")
	item_name : StringProperty(name="Name")
	digits : IntProperty(name="Round digits")

	def invoke(self, context,event):
		props = bpy.context.scene.am_list
		obj_data = bpy.data.objects[self.item_name].data

		if not event.alt and not event.shift and event.ctrl:
			obj_data.energy = round(obj_data.energy,self.digits)
			return{'FINISHED'}

		if self.twice:
			if event.alt and not event.shift and not event.ctrl:
				obj_data.energy *= 1.1
			elif not event.alt and event.shift and not event.ctrl:
				obj_data.energy *= 1.5
			else:
				obj_data.energy *= 2
		else:
			if event.alt and not event.shift and not event.ctrl:
				obj_data.energy *= .9
			elif not event.alt and event.shift and not event.ctrl:
				obj_data.energy *= .75
			else:
				obj_data.energy *= .5

		return{'FINISHED'}
	def execute(self,context):
		return{'FINISHED'}


class AMLIST_OT_mat_remove_assignment_from_obj(Operator):
	bl_idname = 'am_list.mat_remove_assignment_from_obj'
	bl_label = 'Remove Material Assignment from Object'
	bl_description = ""
	bl_options = {"REGISTER","UNDO"}

	mat_name : StringProperty()
	obj_name : StringProperty()

	def execute(self,context):
		tgt_obj = bpy.data.objects[self.obj_name]
		tgt_mat = bpy.data.materials[self.mat_name]
		for i, mat in reversed(list(enumerate(tgt_obj.data.materials))):
			if mat == tgt_mat:
				tgt_obj.data.materials.pop(index=i)
		return{'FINISHED'}


class AMLIST_OT_cam_set_marker(Operator):
	bl_idname = 'am_list.cam_set_marker'
	bl_label = 'Set Marker'
	bl_description = "Bind camera to marker at current frame"
	bl_options = {"REGISTER","UNDO"}

	item_name : StringProperty()

	def execute(self,context):

		c_marker = False
		c_frame = bpy.context.scene.frame_current
		try:
			m_frame = bpy.context.scene.timeline_markers[self.item_name].frame
			if m_frame == c_frame:
				c_marker = True
		except: pass

		if c_marker:
			# bpy.context.scene.timeline_markers.remove(bpy.context.scene.timeline_markers[self.item_name])

			old_editor = bpy.context.area.ui_type

			bpy.context.area.ui_type = 'DOPESHEET'

			# 選択の保存
			old_sel = []
			for m in bpy.context.scene.timeline_markers:
				if m.select:
					old_sel.append(m)
				m.select = False

			act_marker = bpy.context.scene.timeline_markers[self.item_name]
			if act_marker.frame == c_frame:
				act_marker.select = True

			bpy.ops.marker.delete() # 削除

			#再度選択
			for m in old_sel:
				m.select = True

			bpy.context.area.ui_type = old_editor

			self.report({'INFO'}, "Delete Current Marker")

			return{'FINISHED'}

		else:
			tm = bpy.context.scene.timeline_markers
			cur_frame = context.scene.frame_current

			frame_markers = [marker for marker in tm if marker.frame == cur_frame]

			if len(frame_markers) == 0:
				new_marker = tm.new(self.item_name, frame = cur_frame)
				new_marker.camera = bpy.data.objects[self.item_name]
			elif len(frame_markers) == 1:
				frame_markers[0].camera = bpy.data.objects[self.item_name]
			elif len(frame_markers) >= 2:
				frame_markers[0].camera = bpy.data.objects[self.item_name]

			self.report({'INFO'}, "Set Marker")


		return{'FINISHED'}
