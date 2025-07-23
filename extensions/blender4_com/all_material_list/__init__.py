from . import download
download.downloading()

bl_info = {
	"name": "All Material List",
	"author": "Bookyakuno",
	"category": "Material",
	"description": "Display Material / Image / Light / Camera / World / Scene in a list",
	"location": "3D View > Property Shelf(N Key) > Tools > All Material List",
	"version": (2, 7, 7),
	"blender": (4, 2, 0)
}

import bpy
import os, csv, codecs #辞書

from bpy.types import AddonPreferences
from bpy.props import *

addon_id = __package__


# ファイルの読み込み
if 'bpy' in locals():
    from importlib import reload
    import sys
    for k, v in list(sys.modules.items()):
        if k.startswith(__package__+"."):
            reload(v)

from .ui.regi_panel import *
from .ui.ui_preferences import *
from .ui import *

from . import (
	ui,
	op,
)

from .utils.utils import *
from .keymap import *
from .property import *
from .update import *
from .import translate


##################################################
# アドオン設定
class AMLIST_MT_AddonPreferences(AddonPreferences):
	bl_idname = __package__

	use_list_highlight        : BoolProperty(name="Use List Highlight",default=True,description="Highlight active simple materials and worlds in the list")
	category                  : StringProperty(name="Tab Category", description="The tab category name of the panel to add to the side menu of the 3D view.\nIf you empty the text, it will not add the panel to the side menu", default="Mat List", update=update_panel)
	hide_mat_new              : BoolProperty(default=True, name="Material New Button")
	hide_slot                 : BoolProperty(default=True, name="Slot")
	hide_mat                  : BoolProperty(default=True, name="Material")
	hide_sc_l                  : BoolProperty(default=True, name="Scene")
	hide_mat_index            : BoolProperty(default=True, name="Material")
	hide_vcol                 : BoolProperty(default=True, name="Viewport Color")
	hide_light_l                : BoolProperty(default=True, name="Light")
	hide_light_m                : BoolProperty(default=True, name="Emission Material")
	hide_light_p                : BoolProperty(default=True, name="Light Probe")
	hide_cam                  : BoolProperty(default=True, name="Camera")
	hide_wld                  : BoolProperty(default=True, name="World")
	hide_img                  : BoolProperty(default=True, name="Image")
	hide_action                  : BoolProperty(default=True, name="Action")


	usepanel_mat_index            : BoolProperty(default=True, name="Material",update=update_regipanel_mat_index)
	usepanel_vcol                 : BoolProperty(default=True, name="Viewport Color",update=update_regipanel_vcol)
	usepanel_sc_l                : BoolProperty(default=True, name="Scene",update=update_regipanel_sc_l)
	usepanel_light_l                : BoolProperty(default=True, name="Light",update=update_regipanel_light_l)
	# usepanel_light_m                : BoolProperty(default=True, name="Emission Material",update=update_regipanel_light_m)
	usepanel_light_p                : BoolProperty(default=True, name="Light Probe",update=update_regipanel_light_p)
	usepanel_cam                  : BoolProperty(default=True, name="Camera",update=update_regipanel_cam)
	usepanel_wld                  : BoolProperty(default=True, name="World",update=update_regipanel_wld)
	usepanel_img                  : BoolProperty(default=True, name="Image",update=update_regipanel_img)
	usepanel_action                  : BoolProperty(default=True, name="Action",update=update_regipanel_action)
	usepanel_action_graph                  : BoolProperty(default=True, name="Action (Graph Editor)",update=update_regipanel_action_graph)
	usepanel_action_dopesheet                  : BoolProperty(default=True, name="Action (DopeSheet Editor)",update=update_regipanel_action_dopesheet)

	usepanel_mainmenu_view3d                  : BoolProperty(default=True, name="Main Manu (3D View > Side bar(N) )",update=update_regipanel_mainmenu_view3d)
	usepanel_mainmenu_in_prop                  : BoolProperty(default=True, name="Main Manu (Property Editor > Material)",update=update_regipanel_mainmenu_in_prop)


	tab_addon_menu            : EnumProperty(name="Tab", description="", items=[('Option', "Option", ""), ('Display', "Display", ""), ('Keymap', "Keymap", ""), ('Link', "Link", "")], default='Option')

	popup_menu_width         : IntProperty(default=300, name = "Poppup Menu Width", description = "Width setting when menu layout is broken",min = 0)

	id_sc_l                       : IntProperty(default=-1,update=sc_l_list_update)


	def draw(self, context):
		pref_menu(self, context)


############################################
classes = (
	AMLIST_MT_AddonPreferences,
	AMLIST_PR_WindowManager,
	AMLIST_PR_colle_mat,
	AMLIST_PR_mat_other,
	AMLIST_PR_obj_other,
	AMLIST_PR_action_other,
	AMLIST_PR_light_l_other,
	AMLIST_PR_other,
	AMLIST_PR_img,
	AMLIST_OT_Add_Hotkey,
)



############################################
def register():
	for cls in classes:
		try:
			bpy.utils.register_class(cls)
		except ValueError: pass


	op.register()
	ui.register()

	################################################
	# プロパティ
	bpy.types.Scene.am_list           = PointerProperty(type=AMLIST_PR_other)
	bpy.types.Scene.am_list_wm        = PointerProperty(type=AMLIST_PR_WindowManager)
	bpy.types.Object.am_list          = PointerProperty(type=AMLIST_PR_obj_other)
	bpy.types.Action.am_list          = PointerProperty(type=AMLIST_PR_action_other)
	bpy.types.Material.am_list        = PointerProperty(type=AMLIST_PR_mat_other)
	bpy.types.Image.am_list        = PointerProperty(type=AMLIST_PR_img)
	bpy.types.Scene.am_list_colle_mat = CollectionProperty(type=AMLIST_PR_colle_mat)

	################################################
	# その他
	add_hotkey() # Keymap

	################################################
	# 翻訳
	translate.register()


############################################
def unregister():

	op.unregister()
	ui.unregister()

	# その他
	remove_hotkey()

	# クラスの削除は上のremoveより下にある必要がある
	for cls in reversed(classes):
		bpy.utils.unregister_class(cls)

	# 翻訳


	# プロパティ
	del bpy.types.Scene.am_list
	del bpy.types.Scene.am_list_wm
	del bpy.types.Object.am_list
	del bpy.types.Material.am_list
	del bpy.types.Image.am_list
	del bpy.types.Scene.am_list_colle_mat
	translate.unregister()

if __name__ == "__main__":
	register()
