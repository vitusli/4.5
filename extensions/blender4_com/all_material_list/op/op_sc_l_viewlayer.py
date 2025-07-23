import bpy
import re #正規表現

from bpy.props import *
from bpy.types import Operator


class AMLIST_OT_viewlayer_remove(Operator):
	bl_idname = "am_list.viewlayer_remove"
	bl_label = "Remove Viewlayer"
	bl_description = "Remove Viewlayer"
	bl_options = {"REGISTER","UNDO"}

	scene_name : StringProperty(name="Scene")
	viewlayer_name : StringProperty(name="View layer")

	def execute(self, context):
		sc = bpy.data.scenes[self.scene_name]
		vl = sc.view_layers[self.viewlayer_name]
		sc.view_layers.remove(vl)

		return{'FINISHED'}


class AMLIST_OT_viewlayer_new(Operator):
	bl_idname = "am_list.viewlayer_new"
	bl_label = "New Viewlayer"
	bl_description = "New Viewlayer"
	bl_options = {"REGISTER","UNDO"}

	scene_name : StringProperty(name="Scene")

	def execute(self, context):
		bpy.data.scenes[self.scene_name].view_layers.new("View Layer")

		return{'FINISHED'}


class AMLIST_OT_viewlayer_duplicate(Operator):
	bl_idname = "am_list.viewlayer_duplicate"
	bl_label = "Duplicate Viewlayer"
	bl_description = "Duplicate the current view layer"
	bl_options = {"REGISTER","UNDO"}

	def execute(self, context):
		old_layer = bpy.context.window.view_layer
		new_layer = bpy.context.scene.view_layers.new(old_layer.name)
		collection = old_layer.layer_collection
		new_collection = new_layer.layer_collection

		for prop in dir(new_layer):
			try:
				attr = getattr(old_layer,prop)
				setattr(new_layer, prop, attr)
			except:
				pass

		cycles = old_layer.cycles
		new_cycles = new_layer.cycles
		for prop in dir(new_cycles):
			try:
				attr = getattr(cycles,prop)
				setattr(new_cycles, prop, attr)
			except:
				pass

		recursive_attributes(collection, new_collection)
		bpy.context.window.view_layer = new_layer

		return{'FINISHED'}


def recursive_attributes(collection, new_collection):
	new_collection.exclude = collection.exclude
	new_collection.holdout = collection.holdout
	new_collection.indirect_only = collection.indirect_only
	new_collection.hide_viewport = collection.hide_viewport

	for i, _ in enumerate(new_collection.children):
		old_child = collection.children[i]
		new_child = new_collection.children[i]
		recursive_attributes(old_child, new_child)

	for i, _ in enumerate(new_collection.collection.objects):
		tmp = collection.collection.objects[i].hide_get()
		new_collection.collection.objects[i].hide_set(tmp)

	return 0


class AMLIST_OT_viewlayer_set(Operator):
	bl_idname = "am_list.viewlayer_set"
	bl_label = "Move Active View Layer"
	bl_description = "Move Active View Layer"
	bl_options = {'REGISTER', 'UNDO'}

	name : StringProperty(name="Name")

	def execute(self, context):
		bpy.context.window.view_layer = bpy.context.scene.view_layers[self.name]
		return{'FINISHED'}
