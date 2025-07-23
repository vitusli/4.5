import bpy
import random # オブジェクトカラー・マテリアルビューポートカラーのランダムカラーに必要
from bpy.props import *
from bpy.types import Operator



def get_shading(context):
	# Get settings from 3D viewport or OpenGL render engine
	view = context.space_data
	if view.type == 'VIEW_3D':
		return view.shading
	else:
		return context.scene.display.shading


class AMLIST_OT_obj_color_white_to_random(Operator):
	# 未設定の選択オブジェクトのカラーをランダムに設定する
	bl_idname = "am_list.obj_white_to_random_color"
	bl_label = "White To Random Object Color"
	bl_description = "White To Randam Selected Objects Color"
	bl_options = {"REGISTER","UNDO"}

	@classmethod
	def poll(cls, context):
		return len(bpy.context.selected_objects)

	def execute(self, context):
		props = bpy.context.scene.am_list
		shading = get_shading(context)

		for obj in bpy.context.selected_objects:
			if shading.color_type == 'OBJECT':
				if obj.color[0] == 1 and obj.color[1] == 1 and obj.color[2] == 1:
					r = random.random()
					g = random.random()
					b = random.random()

					obj.color = (r,g,b,True)

			else:
				if obj.active_material:
					if obj.active_material.diffuse_color[0] == 0.800000011920929 and obj.active_material.diffuse_color[1] == 0.800000011920929 and obj.active_material.diffuse_color[2] == 0.800000011920929:
						r = random.random()
						g = random.random()
						b = random.random()

						obj.active_material.diffuse_color = (r,g,b,True)
		return{'FINISHED'}


class AMLIST_OT_obj_color_random(Operator):
	# 選択オブジェクトのカラーをランダムに設定する
	bl_idname = "am_list.obj_random_color"
	bl_label = "Random Object Color"
	bl_description = "Sets the selected object's viewport color to a random color. \nIf the shaded display color setting of the viewport is material, set the viewport color of the assigned material to a random color"
	bl_options = {"REGISTER","UNDO"}

	@classmethod
	def poll(cls, context):
		return len(bpy.context.selected_objects)

	def execute(self, context):
		shading = get_shading(context)


		if shading.color_type == 'OBJECT':
			for obj in bpy.context.selected_objects:
					r = random.random()
					g = random.random()
					b = random.random()

					obj.color = (r,g,b,True)

		else:
			# 全ての選択オブジェクトの全てのマテリアル
			mat_l = [m for obj in bpy.context.selected_objects if obj.type in {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT', 'VOLUME'} if obj.data.materials for m in obj.data.materials if m]
			if not mat_l:
				self.report({'WARNING'}, "No Materials!")
				return{'FINISHED'}

			mat_l = sorted(set(mat_l), key=mat_l.index)

			for mat in mat_l:
				r = random.random()
				g = random.random()
				b = random.random()

				mat.diffuse_color = (r,g,b,True)
		return{'FINISHED'}


class AMLIST_OT_obj_color_viewport_to_mat(Operator):
	bl_idname = "am_list.viewport_color_to_mat_color"
	bl_label = "Material Color → Viewport Color"
	bl_description = "Set the viewport color based on the material color.\nIt supports only simple node structure and 'Principled BSDF'"
	bl_options = {"REGISTER","UNDO"}

	@classmethod
	def poll(cls, context):
		return len(bpy.context.selected_objects)

	def execute(self, context):
		props = bpy.context.scene.am_list
		shading = get_shading(context)
		failed_item = []

		# オブジェクトカラー
		if shading.color_type == 'OBJECT':
			for obj in bpy.context.selected_objects:
				if obj.type in {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT', 'VOLUME'}:
					if obj.active_material:
						for slots in obj.material_slots:
							if slots.material:
								slots_item = bpy.data.materials[slots.name]
								if props.to_color_diffuse_mode:
									try:
										obj.color = slots_item.node_tree.nodes["Diffuse BSDF"].inputs[0].default_value
									except: failed_item.append(slots_item.name)
								else:
									try:
										obj.color = slots_item.node_tree.nodes["Principled BSDF"].inputs[0].default_value
									except: failed_item.append(slots_item.name)


		# マテリアルカラー
		else:
			for obj in bpy.context.selected_objects:
				if obj.type in {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT', 'VOLUME'}:
					if obj.active_material:
						for slots in obj.material_slots:
							if slots.material:

								slots_item = bpy.data.materials[slots.name]

								if props.to_color_diffuse_mode:
									try:
										slots_item.diffuse_color = slots_item.node_tree.nodes["Diffuse BSDF"].inputs[0].default_value
									except: failed_item.append(slots_item.name)
								else:
									try:
										slots_item.diffuse_color = slots_item.node_tree.nodes["Principled BSDF"].inputs[0].default_value
										slots_item.metallic = slots_item.node_tree.nodes["Principled BSDF"].inputs[4].default_value
										slots_item.roughness = slots_item.node_tree.nodes["Principled BSDF"].inputs[7].default_value
									except: failed_item.append(slots_item.name)
		if failed_item:
			failed_item = list(set(failed_item))
			failed_item = sorted(failed_item, key=lambda p: p)

			self.report({'INFO'}, "The Following Material Could Not Set Color " + str(len(failed_item)) +" " +  str(failed_item))


		return{'FINISHED'}


# 基本色をベースに、ランダムに少し違う色を設定する
def set_color(self,context,use_random,col,random_val,color_range):
	# (例 random_val が 25)
	ramdom_min = (100 - (random_val))*0.01 # ランダム浮動小数点の最小値(例 0.75)
	ramdom_max = (100 + (random_val))*0.01 # ランダム浮動小数点の最大値(例 1.25)

	for obj in bpy.context.selected_objects:
		if use_random:
			random_val = random.uniform(ramdom_min, ramdom_max)
			random_val_R = random.uniform(ramdom_min * color_range[0], ramdom_max * color_range[0])
			random_val_G = random.uniform(ramdom_min * color_range[1], ramdom_max * color_range[1]) # グリーンに誤差を少し足す
			random_val_B = random.uniform(ramdom_min * color_range[2], ramdom_max * color_range[2]) # ブルーに誤差を少し足す

			col = [ # RGB それぞれの値にランダム数値をかける
			col[0] * random_val * random_val_R,
			col[1] * random_val * random_val_G,
			col[2] * random_val * random_val_B,
			1.000000
			]

		shading = get_shading(context)
		if shading.color_type == 'OBJECT':
			obj.color = col
		else:
			if obj.active_material:
				obj.active_material.diffuse_color = col

def set_color_undo_menu(self,context):
	layout = self.layout
	layout.use_property_split =True

	layout.prop(self,"color_base")
	box = layout.box()
	box.active = self.random
	box.label(text="Random",icon="NONE")
	box.prop(self,"random_val")
	box.prop(self,"color_range")

class AMLIST_OT_obj_color_red(Operator):
	bl_idname = "am_list.obj_color_red"
	bl_label = "Object Color to Red"
	bl_description = "shift: Set a random color close to the basic color"
	bl_options = {"REGISTER","UNDO"}

	color_base : FloatVectorProperty(name="Base Color", default=(0.679543, 0.102242, 0.102242, 1.000000), size=4, subtype="COLOR", min=0, max=1)
	random_val : IntProperty(default=25,name="Random Value",min=0,max=100,subtype="PERCENTAGE",description="Range of random values ​​to be applied to the basic color \ n For example : if the setting value is 25, the value of 0.75-1.25 * base color.")
	color_range : FloatVectorProperty(name="Color Range", default=(1, 0.5, 0.2, 1.000000), size=4, subtype="COLOR", min=0, max=1,description="Multiply each RGB value by the result to make a color difference")

	@classmethod
	def poll(cls, context):
		return len(bpy.context.selected_objects)

	def draw(self, context):
		set_color_undo_menu(self,context)

	def invoke(self, context,event):
		if event.shift:
			self.random = True
		else:
			self.random = False

		return self.execute(context)

	def execute(self, context):
		set_color(self,context,self.random,self.color_base,self.random_val,self.color_range)
		return{'FINISHED'}


class AMLIST_OT_obj_color_orange(Operator):
	bl_idname = "am_list.obj_color_orange"
	bl_label = "Object Color to Orange"
	bl_description = "shift: Set a random color close to the basic color"
	bl_options = {"REGISTER","UNDO"}

	color_base : FloatVectorProperty(name="Base Color", default=(0.686685, 0.337164, 0.107023, 1.000000), size=4, subtype="COLOR", min=0, max=1)
	random_val : IntProperty(default=25,name="Random Value",min=0,max=100,subtype="PERCENTAGE",description="Range of random values ​​to be applied to the basic color \ n For example : if the setting value is 25, the value of 0.75-1.25 * base color.")
	color_range : FloatVectorProperty(name="Color Range", default=(1, 0.9, 0.6, 1.000000), size=4, subtype="COLOR", min=0, max=1,description="Multiply each RGB value by the result to make a color difference")

	@classmethod
	def poll(cls, context):
		return len(bpy.context.selected_objects)

	def draw(self, context):
		set_color_undo_menu(self,context)

	def invoke(self, context,event):
		if event.shift:
			self.random = True
		else:
			self.random = False

		return self.execute(context)

	def execute(self, context):
		set_color(self,context,self.random,self.color_base,self.random_val,self.color_range)
		return{'FINISHED'}


class AMLIST_OT_obj_color_green(Operator):
	bl_idname = "am_list.obj_color_green"
	bl_label = "Object Color to Green"
	bl_description = "shift: Set a random color close to the basic color"
	bl_options = {"REGISTER","UNDO"}

	color_base : FloatVectorProperty(name="Base Color", default=(0.107023, 0.686685, 0.107023, 1.000000), size=4, subtype="COLOR", min=0, max=1)
	random_val : IntProperty(default=25,name="Random Value",min=0,max=100,subtype="PERCENTAGE",description="Range of random values ​​to be applied to the basic color \ n For example : if the setting value is 25, the value of 0.75-1.25 * base color.")
	color_range : FloatVectorProperty(name="Color Range", default=(0.9, 1, 1, 1.000000), size=4, subtype="COLOR", min=0, max=1,description="Multiply each RGB value by the result to make a color difference")

	@classmethod
	def poll(cls, context):
		return len(bpy.context.selected_objects)

	def draw(self, context):
		set_color_undo_menu(self,context)

	def invoke(self, context,event):
		if event.shift:
			self.random = True
		else:
			self.random = False

		return self.execute(context)

	def execute(self, context):
		set_color(self,context,self.random,self.color_base,self.random_val,self.color_range)
		return{'FINISHED'}


class AMLIST_OT_obj_color_light_blue(Operator):
	bl_idname = "am_list.obj_color_light_blue"
	bl_label = "Object Color to Light_blue"
	bl_description = "shift: Set a random color close to the basic color"
	bl_options = {"REGISTER","UNDO"}

	color_base : FloatVectorProperty(name="Base Color", default=(0.109462, 0.577581, 0.686685, 1.000000), size=4, subtype="COLOR", min=0, max=1)
	random_val : IntProperty(default=25,name="Random Value",min=0,max=100,subtype="PERCENTAGE",description="Range of random values ​​to be applied to the basic color \ n For example : if the setting value is 25, the value of 0.75-1.25 * base color.")
	color_range : FloatVectorProperty(name="Color Range", default=(.98, 0.95, 1.05, 1.000000), size=4, subtype="COLOR", min=0, max=1,description="Multiply each RGB value by the result to make a color difference")

	@classmethod
	def poll(cls, context):
		return len(bpy.context.selected_objects)

	def draw(self, context):
		set_color_undo_menu(self,context)

	def invoke(self, context,event):
		if event.shift:
			self.random = True
		else:
			self.random = False

		return self.execute(context)

	def execute(self, context):
		set_color(self,context,self.random,self.color_base,self.random_val,self.color_range)
		return{'FINISHED'}


class AMLIST_OT_obj_color_blue(Operator):
	bl_idname = "am_list.obj_color_blue"
	bl_label = "Object Color to Blue"
	bl_description = "shift: Set a random color close to the basic color"
	bl_options = {"REGISTER","UNDO"}

	color_base : FloatVectorProperty(name="Base Color", default=(0.109462, 0.109462, 0.686685, 1.000000), size=4, subtype="COLOR", min=0, max=1)
	random_val : IntProperty(default=25,name="Random Value",min=0,max=100,subtype="PERCENTAGE",description="Range of random values ​​to be applied to the basic color \ n For example : if the setting value is 25, the value of 0.75-1.25 * base color.")
	color_range : FloatVectorProperty(name="Color Range", default=(0.9, 0.9, 1, 1.000000), size=4, subtype="COLOR", min=0, max=1,description="Multiply each RGB value by the result to make a color difference")

	@classmethod
	def poll(cls, context):
		return len(bpy.context.selected_objects)

	def draw(self, context):
		set_color_undo_menu(self,context)

	def invoke(self, context,event):
		if event.shift:
			self.random = True
		else:
			self.random = False

		return self.execute(context)

	def execute(self, context):
		set_color(self,context,self.random,self.color_base,self.random_val,self.color_range)
		return{'FINISHED'}


class AMLIST_OT_obj_color_purple(Operator):
	bl_idname = "am_list.obj_color_purple"
	bl_label = "Object Color to Purple"
	bl_description = "shift: Set a random color close to the basic color"
	bl_options = {"REGISTER","UNDO"}

	color_base : FloatVectorProperty(name="Base Color", default=(0.558341, 0.109462, 0.686685, 1.000000), size=4, subtype="COLOR", min=0, max=1)
	random_val : IntProperty(default=25,name="Random Value",min=0,max=100,subtype="PERCENTAGE",description="Range of random values ​​to be applied to the basic color \ n For example : if the setting value is 25, the value of 0.75-1.25 * base color.")
	color_range : FloatVectorProperty(name="Color Range", default=(.98, 0.6, 1, 1.000000), size=4, subtype="COLOR", min=0, max=1,description="Multiply each RGB value by the result to make a color difference")

	@classmethod
	def poll(cls, context):
		return len(bpy.context.selected_objects)

	def draw(self, context):
		set_color_undo_menu(self,context)

	def invoke(self, context,event):
		if event.shift:
			self.random = True
		else:
			self.random = False

		return self.execute(context)

	def execute(self, context):
		set_color(self,context,self.random,self.color_base,self.random_val,self.color_range)
		return{'FINISHED'}


class AMLIST_OT_obj_color_pink(Operator):
	bl_idname = "am_list.obj_color_pink"
	bl_label = "Object Color to Pink"
	bl_description = "shift: Set a random color close to the basic color"
	bl_options = {"REGISTER","UNDO"}

	color_base : FloatVectorProperty(name="Base Color", default=(0.879623, 0.332452, 0.552011, 1.000000), size=4, subtype="COLOR", min=0, max=1)
	random_val : IntProperty(default=25,name="Random Value",min=0,max=100,subtype="PERCENTAGE",description="Range of random values ​​to be applied to the basic color \ n For example : if the setting value is 25, the value of 0.75-1.25 * base color.")
	color_range : FloatVectorProperty(name="Color Range", default=(1, 0.7, 1, 1.000000), size=4, subtype="COLOR", min=0, max=1,description="Multiply each RGB value by the result to make a color difference")

	@classmethod
	def poll(cls, context):
		return len(bpy.context.selected_objects)

	def draw(self, context):
		set_color_undo_menu(self,context)

	def invoke(self, context,event):
		if event.shift:
			self.random = True
		else:
			self.random = False

		return self.execute(context)

	def execute(self, context):
		set_color(self,context,self.random,self.color_base,self.random_val,self.color_range)
		return{'FINISHED'}


class AMLIST_OT_obj_color_clear(Operator):
	# 白
	bl_idname = "am_list.obj_color_clear"
	bl_label = "Object Color to Clear"
	bl_description = "shift: Set a random color close to the basic color"
	bl_options = {"REGISTER","UNDO"}

	mat_color : bpy.props.BoolProperty(default=True, name = "color", description = "")
	metallic : bpy.props.BoolProperty(default=True, name = "metallic", description = "")
	roughness : bpy.props.BoolProperty(default=True, name = "roughness", description = "")

	@classmethod
	def poll(cls, context):
		return len(bpy.context.selected_objects)


	def execute(self, context):
		props = bpy.context.scene.am_list
		shading = get_shading(context)

		for obj in bpy.context.selected_objects:
			if shading.color_type == 'OBJECT':
				obj.color = [1,1,1,1]

			else:
				if obj.active_material:
					mat_col = obj.active_material
					if self.mat_color:
						mat_col.diffuse_color = [0.800000011920929,0.800000011920929,0.800000011920929,1]
					if self.metallic:
						mat_col.metallic = 0
					if self.roughness:
						mat_col.roughness = 0.4

							# mat_col.diffuse_color = [0.800000011920929,0.800000011920929,0.800000011920929,1]
							# mat_col.metallic = 0
							# mat_col.roughness = 0.4
		return{'FINISHED'}
