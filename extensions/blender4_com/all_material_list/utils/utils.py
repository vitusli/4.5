import bpy
import addon_utils

def set_data_list(self):
	if self.type == "mat":
		data_list = bpy.data.materials
	if self.type == "wld":
		data_list = bpy.data.worlds
	if self.type == "img":
		data_list = bpy.data.images
	if self.type == "obj":
		data_list = bpy.data.objects
	if self.type == "sc_l":
		data_list = bpy.data.scenes
	if self.type == "action":
		data_list = bpy.data.actions

	return data_list