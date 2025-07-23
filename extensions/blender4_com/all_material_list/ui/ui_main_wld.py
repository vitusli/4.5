import bpy
from bpy.props import *
from .. import __package__ as addon_id

########################################
def draw_panel_wld_menu(self, context,is_compactmode):
	layout = self.layout
	prefs = bpy.context.preferences.addons[addon_id].preferences
	props = context.scene.am_list
	wm = bpy.context.scene.am_list_wm

	if not prefs.usepanel_wld or is_compactmode:
		sp = layout.split(align=True)
		rows = sp.row(align=True)
		rows.alignment = 'LEFT'
		rows.prop(wm, "toggle_wld",text="",icon="TRIA_DOWN" if wm.toggle_wld else "TRIA_RIGHT", emboss=False)
		rows.prop(wm, "toggle_wld",icon="WORLD",emboss=False)

		row = sp.row(align=True)
		row.alignment = 'RIGHT'
		wldcount = len(bpy.data.worlds)
		row.label(text=": " + str(wldcount))
		row.label(text="",icon="BLANK1")
		row.operator("world.new",text="",icon="ADD",emboss=False)

	open = wm.toggle_wld
	if prefs.usepanel_wld:
		if is_compactmode:
			open = wm.toggle_wld
		else:
			open = True
	if open:
		layout.template_list(
		"AMLIST_UL_world", "",
		bpy.data, "worlds",
		props, "id_wld",
		rows = len(bpy.data.worlds)
		)
