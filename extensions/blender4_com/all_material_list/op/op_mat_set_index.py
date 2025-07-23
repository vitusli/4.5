import bpy
from bpy.props import *
from bpy.types import Operator

class AMLIST_OT_mat_set_index_batch(Operator):
	bl_idname = "am_list.mat_set_index_batch"
	bl_label = "Batch Setting Pass Index"
	bl_description = "Batch setting of path indexes for materials or objects"
	bl_options = {'REGISTER','UNDO'}

	through_set_num_already : BoolProperty(default=True,name = "Ignore already set",description="Exclude materials with a non-zero path index.")
	starting_number : IntProperty(default=1,name = "Starting Number",min=0)
	fixed_num : IntProperty(default=0,name = "All set to ",min=0)

	obj_filter_type              : EnumProperty(default="Selected",name="Type", items= [ ("Selected","Selected","Selected","RESTRICT_SELECT_OFF",0),("Scene","Scene","Scene","SCENE_DATA",1), ("All_Data","All Data","All Data","FILE",2),])
	only_geometry_obj : BoolProperty(default=True,name = "Only Geometry Object",description="only object type in 'MESH', 'CURVE', 'SURFACE', 'META', 'FONT', 'VOLUME', 'VOLUME'")

	mat_filter_type              : EnumProperty(default="Selected",name="Type", items= [ ("Slot","Slot","Slot","SORTSIZE",0),("Selected","Selected","Selected","RESTRICT_SELECT_OFF",1),("Scene","Scene","Scene","SCENE_DATA",2), ("All_Data","All Data","All Data","FILE",3), ])
	type              : EnumProperty(default="Material",name="Type", items= [ ("Material","Material","Material","MATERIAL",0),("Object","Object","Object","OBJECT_DATA",1),])
	set_mode              : EnumProperty(default="Individually",name="Type", items= [ ("Individually","Individually Value","Individually Value","PRESET",0),("Fixed","Specified Value","Specified Value","DOT",1),])

	def invoke(self, context, event):
		wm = context.window_manager
		return wm.invoke_props_dialog(self,width=400)

	def draw(self, context):
		layout = self.layout
		props = context.scene.am_list
		row = layout.row(align=True)
		row.prop(self, 'type',expand=True)
		if self.type == "Material":
			row = layout.row(align=True)
			row.prop(self, 'mat_filter_type',expand=True)
		else:
			row = layout.row(align=True)
			row.prop(self, 'obj_filter_type',expand=True)


		layout.separator()

		row = layout.row(align=True)
		row.prop(self, 'set_mode',expand=True)
		layout.separator()
		if self.type == "Object":
			col = layout.column(align=True)
			col.use_property_split =True

			col.prop(self, 'only_geometry_obj')


		if self.set_mode == "Individually":
			col = layout.column(align=True)
			col.use_property_split =True
			col.prop(self, 'through_set_num_already')
			col.prop(self, 'starting_number')

		else:
			rows = layout.row(align=True)
			rows.use_property_split =True
			rows.prop(self, 'fixed_num')

		if self.mat_filter_type == "All_Data":
			col = layout.column(align=True)
			col.label(text="Target is 'All Material Data'",icon="ERROR")
			col.label(text="Are you sure you're OK?",icon="NONE")

		if self.obj_filter_type == "All_Data":
			col = layout.column(align=True)
			col.label(text="Target is 'All Object Data'",icon="ERROR")
			col.label(text="Are you sure you're OK?",icon="NONE")

	def execute(self, context):
		if self.type == "Object":
			self.set_index_obj(context)

		else:
			self.set_index_mat(context)


		return {'FINISHED'}

	def set_index_obj(self,context):
		if self.obj_filter_type=="Selected":
			filter_type = bpy.context.selected_objects
		elif self.obj_filter_type=="Scene":
			filter_type = bpy.context.scene.collection.all_objects
		elif self.obj_filter_type=="All_Data":
			filter_type = bpy.data.objects
		# elif self.obj_filter_type=="Collection":
		# 	colle = self.cam_filter_colle
		# 	if colle:
		# 		filter_type = colle.objects

		if self.only_geometry_obj:
			filter_type = [obj for obj in filter_type if obj.type in {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT', 'VOLUME'}]

		l_items = list(set(filter_type))

		if self.set_mode == "Fixed": # 指定数値に設定
			for item in l_items:
				item.pass_index = self.fixed_num

			self.report({'INFO'}, "Set to [ " + str(self.fixed_num) + " ]" + " ('" + str(len(l_items)) + "'item)")

		else:
			for i,item in enumerate(l_items):
				if self.through_set_num_already: # 設定済みをスルーする
					if not item.pass_index == 0:
						continue
				item.pass_index = i + self.starting_number

			self.report({'INFO'}, "Set to [ "  + str(self.starting_number)  + " - " + str(i) + " ] in " + self.obj_filter_type + " ('" + str(len(l_items)) + "'item)")

		return {'FINISHED'}



	def set_index_mat(self,context):
		if self.mat_filter_type=="Selected":
			filter_type =[m.material for o in bpy.context.selected_objects for m in o.material_slots if m.name != '']
			l_items = list(set(filter_type))

		elif self.mat_filter_type=="Scene":
			filter_type = [m.material for o in bpy.context.scene.objects for m in o.material_slots if m.name != '']
			l_items = list(set(filter_type))

		elif self.mat_filter_type=="All_Data":
			filter_type = [m for m in bpy.data.materials]
			l_items = list(set(filter_type))

		elif self.mat_filter_type=="Slot":
			if bpy.context.view_layer.objects.active:
				obj = bpy.context.view_layer.objects.active
				if obj.material_slots:
					l_items = [m.material for m in obj.material_slots if m.name != '']
				else:
					self.report({'INFO'}, "No Malerial Slot")
					return {'CHANNELLED'}
			else:
				self.report({'INFO'}, "No Active Object")
				return {'CHANNELLED'}


		if self.set_mode == "Fixed": # 指定数値に設定
			for item in l_items:
				item.pass_index = self.fixed_num

			self.report({'INFO'}, "Set to [ " + str(self.fixed_num) + " ]" + " ('" + str(len(l_items)) + "'item)")

		else:
			i = 0
			for i,item in enumerate(l_items):
				if self.through_set_num_already: # 設定済みをスルーする
					if not item.pass_index == 0:
						continue
				item.pass_index = i + self.starting_number

			self.report({'INFO'}, "Set to [ "  + str(self.starting_number)  + " - " + str(i) + " ] in " + self.mat_filter_type + " ('" + str(len(l_items)) + "'item)")


		return {'FINISHED'}
