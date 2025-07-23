import bpy
from ..keymap import addon_keymaps
import rna_keymap_ui # キーマップリストに必要
import addon_utils
from .ui_hide import *
from .. import __package__ as addon_id

def pref_menu(self, context):
	prefs = bpy.context.preferences.addons[addon_id].preferences
	layout = prefs.layout


	row = layout.row(align=True)
	row.prop(prefs, "tab_addon_menu", expand = True)

	################################################
	if prefs.tab_addon_menu == "Option":
		box = layout.box()
		row = box.row()
		row.label(text="Tab Category:")
		row.prop(prefs, "category", text="")

		box.label(text="3D View > Side Menu(N key) > \""+ prefs.category +  "\" > All Material List",icon="DOT")
		box.label(text="Property > Material > All Material List",icon="DOT")
		box.label(text="Image Editor > Side Menu(N key) > Tools > All Material List",icon="DOT")
		box.label(text="Dopesheet > Side Menu(N key) > Action",icon="DOT")
		box.label(text="Graph Editor > Side Menu(N key) > MatList > Action",icon="DOT")
		col = box.column(align=True)
		col.label(text="Popup Menu (Ctrl + Alt + R)",icon="DOT")
		col.use_property_split = True
		col.prop(prefs, "popup_menu_width")

	################################################
	if prefs.tab_addon_menu == "Display":
		spmain = layout.split()

		colmain = spmain.column(align=True)

		colmain.label(text="Display in panel menu mode",icon="HIDE_OFF")
		box = colmain.box()
		colsub = box.column(align=True)
		colsub.separator()
		hide_item(self,context,colsub,"usepanel_mainmenu_view3d", "VIEW3D")
		colsub.label(text="",icon="NONE")
		colsub.separator()

		hide_panel(self,context,colsub)


		colmain = spmain.column(align=True)
		colmain.label(text="Hide With Compact Menu",icon="HIDE_ON")
		box = colmain.box()
		colsub = box.column(align=True)
		hide_compact(self,context,colsub)
		colsub.label(text="",icon="NONE")
		colsub.label(text="",icon="NONE")


	################################################
	if prefs.tab_addon_menu == "Keymap":
		box = layout.box()
		col = box.column()
		row = col.row(align=True)
		row.label(text="Keymap List:",icon="KEYINGSET")
		# row.operator("am_list.add_hotkey",icon="ADD")

		wm = bpy.context.window_manager
		kc = wm.keyconfigs.user
		for km_add, kmi_add in addon_keymaps:
			for km_con in kc.keymaps:
				if km_add.name == km_con.name:
					km = km_con

			for kmi_con in km.keymap_items:
				if kmi_add.name == kmi_con.name:
					kmi = kmi_con
			try:
				col.label(text=str(km.name),icon="DOT")
				col.context_pointer_set("keymap", km)
				rna_keymap_ui.draw_kmi([], kc, km, kmi, col, 0)
				col.separator()
			except: pass


	################################################
	if prefs.tab_addon_menu == "Link":
		box = layout.box()
		box.label(text="Store",icon="NONE")
		row = box.row()
		row.operator("wm.url_open", text="gumroad", icon="URL").url = "https://gum.co/EiLxR"
		row.operator("wm.url_open", text="Blender Market", icon="URL").url = "https://blendermarket.com/products/all-material-list"
		row.operator("wm.url_open", text="BOOTH", icon="URL").url = "https://bookyakuno.booth.pm/items/1936569"

		box = layout.box()
		box.label(text="Description",icon="NONE")
		row = box.row()
		row.operator("wm.url_open", text="BlenderArtists", icon="URL").url = "https://blenderartists.org/t/all-material-list/1162012"
		row.operator("wm.url_open", text="Documents", icon="URL").url = "https://bookyakuno.com/all-material-list/"
		row.label(text="",icon="NONE")
