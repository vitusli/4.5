import bpy


addon_keymaps = []
def add_hotkey():
	wm = bpy.context.window_manager
	kc = wm.keyconfigs.addon
	if kc:
		km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
		# km = kc.keymaps.new(name="3D View Generic", space_type='VIEW_3D', region_type='WINDOW')
		kmi = km.keymap_items.new("am_list.popup",'R', 'PRESS', alt=True, ctrl=True)
		addon_keymaps.append((km, kmi))


class AMLIST_OT_Add_Hotkey(bpy.types.Operator):
	''' Add hotkey entry '''
	bl_idname = "am_list.add_hotkey"
	bl_label = "Add Keymap"
	bl_options = {'REGISTER', 'INTERNAL'}

	def execute(self, context):
		add_hotkey()

		# self.report({'INFO'}, "Hotkey added in Preferences -> Keymap")
		self.report({'INFO'}, "Hotkey added")
		return {'FINISHED'}


def remove_hotkey():
	''' clears all addon level keymap hotkeys stored in addon_keymaps '''
	wm = bpy.context.window_manager

	for km, kmi in addon_keymaps:
		km.keymap_items.remove(kmi)
		# wm.keyconfigs.addon.keymaps.remove(km)
	addon_keymaps.clear()
