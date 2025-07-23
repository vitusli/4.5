import bpy
from bpy.props import *
from bpy.types import Operator


class AMLIST_OT_action_add(Operator):
	bl_idname = "am_list.action_add"
	bl_label = "Add  Action"
	bl_description = ""
	bl_options = {"REGISTER","UNDO"}

	def execute(self, context):
		bpy.data.actions.new(name="Action")

		return{'FINISHED'}


class AMLIST_OT_action_assign(Operator):
	bl_idname = "am_list.action_assign"
	bl_label = "Assign Action"
	bl_description = "Shift: Duplicate the item"

	bl_options = {"REGISTER","UNDO"}

	name : StringProperty(name = "Name")
	duplicate: BoolProperty(name = "Duplicate")

	def invoke(self, context, event):
		if event.shift:
			self.duplicate = True

		return self.execute(context)



	def execute(self, context):
		if self.duplicate:
			new_item = bpy.data.actions[self.name].copy()
			self.report({'INFO'}, "Duplicate [" + new_item.name + "]")
			return {'FINISHED'}

		props = bpy.context.scene.am_list

		act = bpy.data.actions[self.name]
		sc = bpy.context.scene

		for obj in bpy.context.selected_objects:
			if not obj.animation_data:
				try:
					obj.animation_data_create()
				except:
					self.report({'INFO'}, "Could not be set for [" + obj.name + "]")
					continue
			obj.animation_data.action = act

			if props.action_assign_type in {"Preview", "SceneRange_Preview"}:
				sc.use_preview_range = True
				sc.frame_preview_start = int(act.frame_range[0])
				sc.frame_preview_end = int(act.frame_range[1])
				sc.frame_current = int(act.frame_range[0])


			if props.action_assign_type in {"SceneRange", "SceneRange_Preview"}:
				sc.use_preview_range = False
				sc.frame_start = int(act.frame_range[0])
				sc.frame_end = int(act.frame_range[1])
				sc.frame_current = int(act.frame_range[0])

		return{'FINISHED'}
