import bpy

from .ui_sc_l_render_setting import draw_sc_l_render_setting


# 個別アイテムの詳細メニュー
def draw_sc_l_uidetail(self, context,layout,act_item):
	props = act_item.am_list

	if bpy.context.scene.am_list.sc_l_uidetail_toggle_render:
		draw_sc_l_render_setting(self,context,layout,act_item,False)

	if bpy.context.scene.am_list.sc_l_uidetail_toggle_act:
		draw_sc_l_view_layer(self, context,layout,act_item)


def draw_sc_l_view_layer(self, context,layout,act_item):
	props = act_item.am_list
	sc = act_item
	sp = layout.split(align=True,factor=0.9)
	sp.template_list("AMLIST_UL_viewlayers", "", sc, "view_layers", props, "sc_l_viewlayers_index", rows=2)

	col = sp.column()
	sub = col.column(align=True)
	sub.scale_y = 1.2
	if act_item.name == bpy.context.scene.name:
		sub.operator("scene.view_layer_add", icon='ADD', text="")
		sub.operator("scene.view_layer_remove", icon='REMOVE', text="")
		sub.separator()
		sub.operator("am_list.viewlayer_duplicate", icon='DUPLICATE', text="")
		sub.prop(act_item.render, "use_single_layer", icon_only=True,icon="PINNED")

	else:
		sub.operator("am_list.viewlayer_new", icon='ADD', text="").scene_name = act_item.name
		sub.separator()
		sub.prop(act_item.render, "use_single_layer", icon_only=True,icon="PINNED")
