import bpy

# if "bpy" in locals():
#     import importlib
#     reloadable_modules = [
#         "op_action",
#         "op_image",
#         "op_item",
#         "op_mat_new",
#         "op_mat_node",
#         "op_mat_select",
#         "op_mat_set_index",
#         "op_mat",
#         "op_other",
#         "op_sc_l_ptdime",
#         "op_sc_l_viewlayer",
#         "op_viewport_color",
#         ]
#     for module in reloadable_modules:
#         if module in locals():
#             importlib.reload(locals()[module])

from .op_action import *
from .op_image import *
from .op_item import *
from .op_mat import *
from .op_mat_new import *
from .op_mat_node import *
from .op_mat_select import *
from .op_mat_set_index import *
from .op_other import *
from .op_sc_l_ptdime import *
from .op_sc_l_viewlayer import *
from .op_viewport_color import *


classes = (
AMLIST_OT_action_add,
AMLIST_OT_action_assign,
AMLIST_OT_cam_set_marker,
AMLIST_OT_cam_set_view,
AMLIST_OT_filter_dot_match,
AMLIST_OT_filter_exclusion,
AMLIST_OT_filter_first_match,
AMLIST_OT_filter_trailing_match,
AMLIST_OT_img_collect_all,
AMLIST_OT_img_merge,
AMLIST_OT_img_move_folder_to_folder,
AMLIST_OT_img_move_active_id,
AMLIST_OT_img_reload_all,
AMLIST_OT_img_rename_filename,
AMLIST_OT_img_replace,
AMLIST_OT_item_asobj_select,
AMLIST_OT_item_delete_0,
AMLIST_OT_item_delete,
AMLIST_OT_item_hide_render,
AMLIST_OT_item_hide_select,
AMLIST_OT_item_hide_set,
AMLIST_OT_item_hide_viewport,
AMLIST_OT_item_rename,
AMLIST_OT_item_select,
AMLIST_OT_item_toggle_fake_user,
AMLIST_OT_light_energy_twice,
AMLIST_OT_mat_assign_mat,
AMLIST_OT_mat_assign_obj_list,
AMLIST_OT_mat_assign,
AMLIST_OT_mat_cleanup_slot,
AMLIST_OT_mat_copy_material_slot,
AMLIST_OT_mat_delete_slot,
AMLIST_OT_mat_merge,
AMLIST_OT_mat_move_index_index_list,
AMLIST_OT_mat_move_index,
AMLIST_OT_mat_new_create_multi_mat,
AMLIST_OT_mat_new_create_not_assign,
AMLIST_OT_mat_new_create_one_mat,
AMLIST_OT_mat_rename_obj_name,
AMLIST_OT_mat_replace,
AMLIST_OT_mat_select_index,
AMLIST_OT_mat_set_active_index,
AMLIST_OT_mat_set_index_batch,
AMLIST_OT_mat_set_index,
AMLIST_OT_mat_remove_assignment_from_obj,
AMLIST_OT_node_remove,
AMLIST_OT_obj_color_blue,
AMLIST_OT_obj_color_clear,
AMLIST_OT_obj_color_green,
AMLIST_OT_obj_color_light_blue,
AMLIST_OT_obj_color_orange,
AMLIST_OT_obj_color_pink,
AMLIST_OT_obj_color_purple,
AMLIST_OT_obj_color_random,
AMLIST_OT_obj_color_red,
AMLIST_OT_obj_color_viewport_to_mat,
AMLIST_OT_obj_color_white_to_random,
AMLIST_OT_Popup_hide_compact,
AMLIST_OT_Popup_hide_panel,
AMLIST_OT_ptdime_apply_percentage,
AMLIST_OT_ptdime_now_f,
AMLIST_OT_ptdime_render_cycleslots,
AMLIST_OT_ptdime_set_f,
AMLIST_OT_ptdime_x_y_change,
AMLIST_OT_setup_one_tex_new_img,
AMLIST_OT_uidetail_toggle_all,
AMLIST_OT_uidetail_toggle,
AMLIST_OT_viewlayer_duplicate,
AMLIST_OT_viewlayer_new,
AMLIST_OT_viewlayer_remove,
AMLIST_OT_viewlayer_set,
AMLIST_OT_world_assign,
AMLIST_OT_img_change_path_abs_rel,
)


def register():
	for cls in classes:
		bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        try:
        	bpy.utils.unregister_class(cls)
        except RuntimeError: pass
