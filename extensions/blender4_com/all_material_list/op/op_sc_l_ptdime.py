import bpy
from bpy.props import *
from bpy.types import Operator


class AMLIST_OT_ptdime_apply_percentage(Operator):
   bl_idname = "am_list.apply_resolution_percentage"
   bl_label = "Apply Resolution Percentage"
   bl_description = "Apply Resolution Percentage"

   scn_name : StringProperty(name="Scene Name")

   def execute(self, context):
	   scn = bpy.data.scenes[self.scn_name]

	   old_per = scn.render.resolution_percentage * 0.01

	   scn.render.resolution_x = int(scn.render.resolution_x * old_per)
	   scn.render.resolution_y = int(scn.render.resolution_y * old_per)

	   scn.render.resolution_percentage = 100

	   return {'FINISHED'}


class AMLIST_OT_ptdime_set_f(Operator):
   bl_idname = "am_list.set_f"
   bl_label = "set_f"
   bl_description = "Change the number of sheets"
   def execute(self, context):

	   scn = context.scene

	   set_f = scn.frame_start + scn.floatSample
	   scn.frame_end = set_f

	   return {'FINISHED'}


class AMLIST_OT_ptdime_now_f(Operator):
   bl_idname = "am_list.now_f"
   bl_label = "now_f"
   bl_description = "Current number of sheets"

   def execute(self, context):

	   scn = context.scene

	   scn.floatSample = scn.frame_end - scn.frame_start


	   return {'FINISHED'}


class AMLIST_OT_ptdime_render_cycleslots(Operator):
	bl_idname = "am_list.render_cycleslots"
	bl_label = "render_cycleslots"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Slots change every time rendering"

	def execute(self, context):
		old_editor_type = bpy.context.area.type

		slots = bpy.data.images['Render Result'].render_slots
		slots.active_index=(slots.active_index+1)%8
		# bpy.ops.render.render('EXECUTION_CONTEXT')
		bpy.ops.render.render('INVOKE_DEFAULT')
		bpy.ops.render.render('EXEC_DEFAULT')
		bpy.context.area.type = "NODE_EDITOR"
		bpy.ops.node.select_all(action='SELECT')
		bpy.ops.node.mute_toggle()
		bpy.ops.node.mute_toggle()
		bpy.context.space_data.tree_type = 'ShaderNodeTree'
		bpy.context.space_data.tree_type = 'CompositorNodeTree'



		bpy.ops.node.nw_reset_nodes() #Viewer Nodeの更新
		bpy.context.area.type = old_editor_type

		return {'FINISHED'}


class AMLIST_OT_ptdime_x_y_change(Operator):
	bl_idname = "am_list.x_y_change"
	bl_description = "Change Resolution X/Y"
	bl_label = "X-Y"
	scn_name : StringProperty(name="Scene Name")

	def execute(self, context):
		scn = bpy.data.scenes[self.scn_name]
		old_x = scn.render.resolution_x
		old_y = scn.render.resolution_y
		scn.render.resolution_x = old_y
		scn.render.resolution_y = old_x

		return {'FINISHED'}
