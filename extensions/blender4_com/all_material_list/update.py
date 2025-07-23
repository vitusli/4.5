import bpy
from bpy.app.handlers import persistent # マテリアル更新に必要
from .property import *
from . import __package__ as addon_id

# マテリアル
def mat_list_update(self, context):
	context.scene.am_list.id_mat = -1

# シーン
def sc_l_list_update(self, context):
	# bpy.context.scene.am_list.id_sc_l = -1
	prefs = bpy.context.preferences.addons[addon_id].preferences

	bpy.context.window.scene = bpy.data.scenes[prefs.id_sc_l]

# ビューレイヤー
def vl_list_update(self, context):
	sc = bpy.context.scene
	props = sc.save_cam_other
	try:
		bpy.context.window.view_layer = sc.view_layers[props.viewlayers_update]
	except: pass


# イメージ
def update_active_img(self, context):
	try:
		if bpy.context.area.type == "IMAGE_EDITOR":
			id = bpy.context.scene.am_list.id_img
			if id < len(bpy.data.images):
				img = bpy.data.images[id]
				bpy.context.space_data.image = img
				bpy.ops.image.view_all(fit_view=True)
		else:
			id = bpy.context.scene.am_list.id_img
			img = bpy.data.images[id]
			for area in bpy.context.screen.areas:
				if area.type == 'IMAGE_EDITOR':
					space = area.spaces.active
					space.image = img

					# if bpy.app.version >= (4,0,0):
					# 	with bpy.context.temp_override(area=area):
					# 		bpy.ops.image.view_all(fit_view=True)
					# else:
					# 	w_m = bpy.context.window_manager
					# 	win = w_m.windows[0]
					# 	override = bpy.context.copy()
					# 	override['window'] = win
					# 	override['screen'] = win.screen
					# 	override['area'] = area
					# 	bpy.ops.image.view_all(override,fit_view=True)

					break
	except: pass

# ワールド
def update_active_wld(self, context):
	try:
		id = bpy.context.scene.am_list.id_wld
		if id < len(bpy.data.worlds):
			world = bpy.data.worlds[id]
			bpy.context.scene.world = world
	except:
		pass
