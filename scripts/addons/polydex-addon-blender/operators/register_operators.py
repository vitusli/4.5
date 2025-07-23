# #### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import bpy.utils.previews

from .operator_active import POLIIGON_OT_active
from .operator_add_converter_node import POLIIGON_OT_add_converter_node
from .operator_apply import POLIIGON_OT_apply
from .operator_cancel_download import POLIIGON_OT_cancel_download
from .operator_category import POLIIGON_OT_category
from .operator_check_update import POLIIGON_OT_check_update
from .operator_close_notification import POLIIGON_OT_close_notification
from .operator_detail import POLIIGON_OT_detail
from .operator_detail_view import (
    POLIIGON_OT_detail_view,
    POLIIGON_OT_detail_view_open,
    POLIIGON_OT_detail_view_select)
from .operator_directory import POLIIGON_OT_directory
from .operator_download import (
    POLIIGON_OT_download,
    POLIIGON_OT_popup_purchase)
from .operator_folder import POLIIGON_OT_folder
from .operator_hdri import POLIIGON_OT_hdri
from .operator_image import POLIIGON_OT_image
from .operator_library import POLIIGON_OT_library
from .operator_link import POLIIGON_OT_link
from .operator_local_asset_sync import POLIIGON_OT_get_local_asset_sync
from .operator_load_asset_from_list import (
    POLIIGON_OT_load_asset_size_from_list)
from .operator_material import POLIIGON_OT_material
from .operator_model import POLIIGON_OT_model
from .operator_model_invoker import POLIIGON_OT_model_invoker
from .operator_open_polydex import POLIIGON_OT_open_polydex_app
from .operator_options import POLIIGON_OT_options
from .operator_notice import POLIIGON_OT_notice_operator
from .operator_popup_download_limit import POLIIGON_OT_popup_download_limit
from .operator_popup_message import POLIIGON_OT_popup_message
from .operator_popups_onboarding import (
    POLIIGON_OT_popup_welcome,
    POLIIGON_OT_popup_first_download)
from .operator_preview import (
    POLIIGON_OT_popup_first_preview,
    POLIIGON_OT_preview)
from .operator_refresh_data import POLIIGON_OT_refresh_data
from .operator_report_error import POLIIGON_OT_report_error
from .operator_reset_map_prefs import POLIIGON_OT_reset_map_prefs
from .operator_show_preferences import POLIIGON_OT_show_preferences
from .operator_select import POLIIGON_OT_select
from .operator_setting import POLIIGON_OT_setting
from .operator_show_quick_menu import POLIIGON_OT_show_quick_menu
try:
    from .operator_unit_test_helper import (
        get_unit_test_helper_window_manager_props,
        POLIIGON_OT_unit_test_helper,
        UnitTestProperties)
    HAVE_UNIT_TEST_HELPER = True
except ImportError:
    # It is fine, to not have this. We only use it in uit tests.
    HAVE_UNIT_TEST_HELPER = False
from .operator_unsupported_convention import POLIIGON_OT_unsupported_convention
from .operator_user import POLIIGON_OT_user
from .operator_view_thumbnail import POLIIGON_OT_view_thumbnail
from ..build import (
    BUILD_OPTION_P4B,
    BUILD_OPTION_BOB)
from ..toolbox import get_context


if BUILD_OPTION_BOB:
    BOB_OT_active = POLIIGON_OT_active
    BOB_OT_add_converter_node = POLIIGON_OT_add_converter_node
    BOB_OT_apply = POLIIGON_OT_apply
    BOB_OT_cancel_download = POLIIGON_OT_cancel_download
    BOB_OT_category = POLIIGON_OT_category
    BOB_OT_check_update = POLIIGON_OT_check_update
    BOB_OT_close_notification = POLIIGON_OT_close_notification
    BOB_OT_detail = POLIIGON_OT_detail
    BOB_OT_directory = POLIIGON_OT_directory
    BOB_OT_detail_view = POLIIGON_OT_detail_view
    BOB_OT_detail_view_open = POLIIGON_OT_detail_view_open
    BOB_OT_detail_view_select = POLIIGON_OT_detail_view_select
    BOB_OT_download = POLIIGON_OT_download
    BOB_OT_folder = POLIIGON_OT_folder
    BOB_OT_get_local_asset_sync = POLIIGON_OT_get_local_asset_sync
    BOB_OT_hdri = POLIIGON_OT_hdri
    BOB_OT_image = POLIIGON_OT_image
    BOB_OT_library = POLIIGON_OT_library
    BOB_OT_link = POLIIGON_OT_link
    BOB_OT_load_asset_size_from_list = POLIIGON_OT_load_asset_size_from_list
    BOB_OT_material = POLIIGON_OT_material
    BOB_OT_model = POLIIGON_OT_model
    BOB_OT_model_invoker = POLIIGON_OT_model_invoker
    BOB_OT_notice_operator = POLIIGON_OT_notice_operator
    BOB_OT_open_polydex_app = POLIIGON_OT_open_polydex_app
    BOB_OT_options = POLIIGON_OT_options
    BOB_OT_popup_download_limit = POLIIGON_OT_popup_download_limit
    BOB_OT_popup_first_download = POLIIGON_OT_popup_first_download
    BOB_OT_popup_first_preview = POLIIGON_OT_popup_first_preview
    BOB_OT_popup_message = POLIIGON_OT_popup_message
    BOB_OT_popup_purchase = POLIIGON_OT_popup_purchase
    BOB_OT_popup_welcome = POLIIGON_OT_popup_welcome
    BOB_OT_preview = POLIIGON_OT_preview
    BOB_OT_refresh_data = POLIIGON_OT_refresh_data
    BOB_OT_report_error = POLIIGON_OT_report_error
    BOB_OT_reset_map_prefs = POLIIGON_OT_reset_map_prefs
    BOB_OT_select = POLIIGON_OT_select
    BOB_OT_setting = POLIIGON_OT_setting
    BOB_OT_show_preferences = POLIIGON_OT_show_preferences
    BOB_OT_show_quick_menu = POLIIGON_OT_show_quick_menu
    BOB_OT_unsupported_convention = POLIIGON_OT_unsupported_convention
    BOB_OT_user = POLIIGON_OT_user
    BOB_OT_view_thumbnail = POLIIGON_OT_view_thumbnail

    classes = (
        BOB_OT_active,
        BOB_OT_add_converter_node,
        BOB_OT_apply,
        BOB_OT_cancel_download,
        BOB_OT_category,
        BOB_OT_check_update,
        BOB_OT_close_notification,
        BOB_OT_detail,
        BOB_OT_directory,
        BOB_OT_detail_view,
        BOB_OT_detail_view_open,
        BOB_OT_detail_view_select,
        BOB_OT_download,
        BOB_OT_folder,
        BOB_OT_get_local_asset_sync,
        BOB_OT_hdri,
        BOB_OT_image,
        BOB_OT_library,
        BOB_OT_link,
        BOB_OT_load_asset_size_from_list,
        BOB_OT_material,
        BOB_OT_model,
        BOB_OT_model_invoker,
        BOB_OT_notice_operator,
        BOB_OT_open_polydex_app,
        BOB_OT_options,
        BOB_OT_popup_download_limit,
        BOB_OT_popup_first_download,
        BOB_OT_popup_first_preview,
        BOB_OT_popup_message,
        BOB_OT_popup_purchase,
        BOB_OT_popup_welcome,
        BOB_OT_preview,
        BOB_OT_refresh_data,
        BOB_OT_report_error,
        BOB_OT_reset_map_prefs,
        BOB_OT_select,
        BOB_OT_setting,
        BOB_OT_show_preferences,
        BOB_OT_show_quick_menu,
        BOB_OT_unsupported_convention,
        BOB_OT_user,
        BOB_OT_view_thumbnail
    )

    if HAVE_UNIT_TEST_HELPER:
        BOB_OT_unit_test_helper = POLIIGON_OT_unit_test_helper
else:
    classes = (
        POLIIGON_OT_active,
        POLIIGON_OT_add_converter_node,
        POLIIGON_OT_apply,
        POLIIGON_OT_cancel_download,
        POLIIGON_OT_category,
        POLIIGON_OT_check_update,
        POLIIGON_OT_close_notification,
        POLIIGON_OT_detail,
        POLIIGON_OT_detail_view,
        POLIIGON_OT_detail_view_open,
        POLIIGON_OT_detail_view_select,
        POLIIGON_OT_directory,
        POLIIGON_OT_download,
        POLIIGON_OT_folder,
        POLIIGON_OT_get_local_asset_sync,
        POLIIGON_OT_hdri,
        POLIIGON_OT_image,
        POLIIGON_OT_library,
        POLIIGON_OT_link,
        POLIIGON_OT_load_asset_size_from_list,
        POLIIGON_OT_material,
        POLIIGON_OT_model,
        POLIIGON_OT_notice_operator,
        POLIIGON_OT_open_polydex_app,
        POLIIGON_OT_options,
        POLIIGON_OT_popup_download_limit,
        POLIIGON_OT_popup_first_download,
        POLIIGON_OT_popup_first_preview,
        POLIIGON_OT_popup_message,
        POLIIGON_OT_popup_purchase,
        POLIIGON_OT_popup_welcome,
        POLIIGON_OT_preview,
        POLIIGON_OT_refresh_data,
        POLIIGON_OT_report_error,
        POLIIGON_OT_reset_map_prefs,
        POLIIGON_OT_select,
        POLIIGON_OT_setting,
        POLIIGON_OT_show_preferences,
        POLIIGON_OT_show_quick_menu,
        POLIIGON_OT_unsupported_convention,
        POLIIGON_OT_user,
        POLIIGON_OT_view_thumbnail
    )


cTB = None


def register_unit_test_helper() -> None:
    global classes

    if not HAVE_UNIT_TEST_HELPER:
        return

    if BUILD_OPTION_P4B and POLIIGON_OT_unit_test_helper not in classes:
        # Have operator un-/registered like all others
        classes = (*classes, POLIIGON_OT_unit_test_helper)

    if BUILD_OPTION_BOB and BOB_OT_unit_test_helper not in classes:
        # Have operator un-/registered like all others
        classes = (*classes, BOB_OT_unit_test_helper)

    bpy.utils.register_class(UnitTestProperties)
    if BUILD_OPTION_BOB:
        bpy.types.WindowManager.bob_unit_test = bpy.props.PointerProperty(
            type=UnitTestProperties)
    else:
        bpy.types.WindowManager.polligon_unit_test = bpy.props.PointerProperty(
            type=UnitTestProperties)


def unregister_unit_test_helper() -> None:
    if not HAVE_UNIT_TEST_HELPER:
        return

    props_unit_test_helper = get_unit_test_helper_window_manager_props()
    del props_unit_test_helper
    bpy.utils.unregister_class(UnitTestProperties)


def register(addon_version: str) -> None:
    global cTB

    register_unit_test_helper()

    cTB = get_context(addon_version)

    for cls in classes:
        bpy.utils.register_class(cls)
        cls.init_context(addon_version)


def unregister() -> None:
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    unregister_unit_test_helper()
