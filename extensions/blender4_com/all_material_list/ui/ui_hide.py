import bpy
from .. import __package__ as addon_id

def hide_panel(self,context,layout):
	hide_item(self,context,layout,"usepanel_mat_index", "MATERIAL")
	hide_item(self,context,layout,"usepanel_vcol", "COLOR")
	hide_item(self,context,layout,"usepanel_light_l", "LIGHT_DATA")
	hide_item(self,context,layout,"usepanel_light_p", "OUTLINER_OB_LIGHTPROBE")
	hide_item(self,context,layout,"usepanel_cam", "CAMERA_DATA")
	hide_item(self,context,layout,"usepanel_wld", "WORLD")
	hide_item(self,context,layout,"usepanel_img", "IMAGE_DATA")
	hide_item(self,context,layout,"usepanel_sc_l", "SCENE_DATA")
	hide_item(self,context,layout,"usepanel_action", "ACTION")
	hide_item(self,context,layout,"usepanel_action_dopesheet", "ACTION")
	hide_item(self,context,layout,"usepanel_action_graph", "ACTION")


def hide_compact(self,context,layout):
	hide_item(self,context,layout,"usepanel_mainmenu_in_prop", "PROPERTIES")
	layout.separator()
	hide_item(self,context,layout,"hide_slot", "SORTSIZE")
	layout.separator()
	hide_item(self,context,layout,"hide_mat_index", "MATERIAL")
	hide_item(self,context,layout,"hide_vcol", "COLOR")
	hide_item(self,context,layout,"hide_light_l", "LIGHT_DATA")
	hide_item(self,context,layout,"hide_light_p", "OUTLINER_OB_LIGHTPROBE")
	hide_item(self,context,layout,"hide_cam", "CAMERA_DATA")
	hide_item(self,context,layout,"hide_wld", "WORLD")
	hide_item(self,context,layout,"hide_img", "IMAGE_DATA")
	hide_item(self,context,layout,"hide_sc_l", "SCENE_DATA")
	hide_item(self,context,layout,"hide_action", "ACTION")


def hide_item(self,context,layout,prop_name, icon_val):
	prefs = bpy.context.preferences.addons[addon_id].preferences

	row = layout.row(align=True)
	row.alignment = "LEFT"
	row.ui_units_x =6
	rows = row.row(align=True)
	rows.scale_x = 1.5
	rows.prop(prefs,prop_name,icon=icon_val,text="")
	row.prop(prefs,prop_name,emboss=False)
