import bpy

# if "bpy" in locals():
#     import importlib
#     reloadable_modules = [
#         "ui_main_mat_mini_socket",
#         "ui_main_mat_index_item",
#         "ui_main_mat_index_uidetail",
#         "ui_main_mat_index",
#         "ui_main_mat_new",
#         "ui_main_mat",
#         "ui_panel_node_draw",
#         "ui_uilist_mat",
#         ]
#     for module in reloadable_modules:
#         if module in locals():
#             importlib.reload(locals()[module])


from .ui_main_mat_mini_socket import *
from .ui_main_mat import *
from .ui_main_mat_index import *
from .ui_main_mat_index_item import *
from .ui_main_mat_index_uidetail import *
from .ui_main_mat_new import *
from .ui_panel_node_draw import *
from .ui_uilist_mat import *


classes = (
AMLIST_UL_mat_popup,
AMLIST_UL_mat,
)


def register():
	for cls in classes:
		bpy.utils.register_class(cls)


def unregister():
	for cls in reversed(classes):
		bpy.utils.unregister_class(cls)


# 構造解説
'''
AMLIST_OT_Popup(Operator) # ポップアップ
AMLIST_PT_mat_index(Panel) # パネル
    draw_mat_menu_root() # マテリアルリスト機能がまとまった関数
        draw_mat_uilist_layout() # UIリストを表示するレイアウト
            class AMLIST_UL_mat(UIList): # UIリスト
            class AMLIST_UL_mat_popup(UIList): # ポップアップ用と2つ同じものを用意する(メニューを少し変えるため)
                draw_panel_matindex_item() # 各リストアイテム
        draw_mat_iteration_list() # 自作のfor文によるリスト
'''
