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

from enum import IntEnum
from typing import Tuple

from bpy.types import Operator
import bpy.utils.previews

from ..modules.poliigon_core.api_remote_control_params import (
    CATEGORY_FREE,
    KEY_TAB_IMPORTED,
    KEY_TAB_MY_ASSETS,
    KEY_TAB_ONLINE)
from ..modules.poliigon_core.multilingual import _t
from ..asset_browser.asset_browser import create_poliigon_library
from ..dialogs.utils_dlg import get_ui_scale
from ..build import PREFIX_OP
from ..constants import HDRI_RESOLUTIONS
from ..toolbox import get_context
from ..toolbox_settings import save_settings
from ..utils import (
    f_MDir,
    get_op_base,
    get_window_manager_props)
from .. import reporting
from .operator_detail_view import check_and_report_detail_view_not_opening


class ModeUpdate(IntEnum):
    NO_UPDATE = 0
    # Any update includes UI refresh
    IMPORTED_AND_GET_ASSETS_AND_PAGE_1 = 1
    IMPORTED_AND_GET_ASSETS = 2
    IMPORTED_ONLY = 3


class POLIIGON_OT_setting(Operator):
    bl_idname = f"{PREFIX_OP}.poliigon_setting"
    bl_label = ""
    bl_description = _t("Edit Poliigon Addon Settings")
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"REGISTER", "INTERNAL"}

    tooltip: bpy.props.StringProperty(default="", options={"HIDDEN"})  # noqa: F722, F821
    mode: bpy.props.StringProperty(default="", options={"HIDDEN"})  # noqa: F722, F821

    @staticmethod
    def init_context(addon_version: str) -> None:
        """Called from operators.py to init global addon context."""

        global cTB
        cTB = get_context(addon_version)

    @classmethod
    def description(cls, context, properties):
        return properties.tooltip

    @staticmethod
    def _set_library() -> int:
        path_library_new = cTB.settings["set_library"]
        path_library_old = cTB.get_library_path(primary=True)
        f_MDir(path_library_new)

        cTB.replace_library_path(
            path_library_old,
            path_library_new,
            primary=True,
            update_local_assets=True)

        if bpy.app.version >= (3, 0):
            create_poliigon_library(force=True)

        cTB.signal_popup(popup="ONBOARD_WELCOME")
        op_base = get_op_base()
        op_base.popup_welcome("INVOKE_DEFAULT")

        # do_update: update and switch to page 1
        return ModeUpdate.IMPORTED_AND_GET_ASSETS_AND_PAGE_1

    def _set_area(self) -> int:
        with cTB.lock_thumbs:
            cTB.thumbs.clear()
        area = self.mode.replace("area_", "")
        cTB.settings["area"] = area

        # This caused a delay when switching between Poliigon/My Assets
        # vClearCache = 1

        cTB.settings["show_settings"] = 0
        cTB.settings["show_user"] = 0
        cTB.vActiveAsset = None

        cTB.track_screen_from_area()
        check_and_report_detail_view_not_opening()
        # do_update: update, but skip switching to page 1 and getting assets
        return ModeUpdate.IMPORTED_ONLY

    @staticmethod
    def _show_my_account() -> None:
        cTB.settings["show_settings"] = 0
        cTB.settings["show_user"] = 1
        cTB.vActiveAsset = None
        cTB.refresh_ui()
        check_and_report_detail_view_not_opening()

    @staticmethod
    def _show_settings() -> None:
        # TODO(Andreas): Does this code still have a purpose?
        cTB.settings["show_settings"] = 1
        cTB.settings["show_user"] = 0
        cTB.vActiveAsset = None
        cTB.refresh_ui()

    def _set_category(self) -> int:
        props = get_window_manager_props()
        area = cTB.settings["area"]

        mode_parts = self.mode.split("_")
        idx_category = int(mode_parts[1])
        button = mode_parts[2]
        if idx_category < len(cTB.settings["category"][area]):
            cTB.settings["category"][area][idx_category] = button
        else:
            cTB.settings["category"][area].append(button)
        cTB.settings["category"][area] = cTB.settings[
            "category"][area][: idx_category + 1]

        categories = cTB.settings["category"][area]
        if len(categories) > 1 and categories[-1].startswith("All "):
            categories = categories[:-1]
        cTB.settings["category"][area] = categories

        cTB.vActiveAsset = None
        cTB.vActiveMat = None
        cTB.vActiveMode = None
        # Do we want to clear searches when switching between areas?
        cTB.vSearch[KEY_TAB_ONLINE] = props.search_poliigon
        cTB.vSearch[KEY_TAB_MY_ASSETS] = props.search_my_assets
        cTB.vSearch[KEY_TAB_IMPORTED] = props.search_imported

        cTB.search_free = False

        check_and_report_detail_view_not_opening()

        # do_update: update and switch to page 1
        return ModeUpdate.IMPORTED_AND_GET_ASSETS_AND_PAGE_1

    def _set_free_search(self) -> int:
        cTB.search_free = True
        cTB.settings["category"][KEY_TAB_ONLINE] = [CATEGORY_FREE]
        cTB.vActiveAsset = None
        cTB.vActiveMat = None
        cTB.vActiveMode = None
        return ModeUpdate.IMPORTED_AND_GET_ASSETS_AND_PAGE_1

    def _set_page(self) -> int:
        with cTB.lock_thumbs:
            cTB.thumbs.clear()

        area = cTB.settings["area"]
        idx_page = self.mode.split("_")[-1]

        if cTB.vPage[area] == idx_page:
            return {"FINISHED"}
        elif idx_page == "-":
            if cTB.vPage[area] > 0:
                cTB.vPage[area] -= 1
        elif idx_page == "+":
            if cTB.vPage[area] < cTB.vPages[area]:
                cTB.vPage[area] += 1
        else:
            cTB.vPage[area] = int(idx_page)

        check_and_report_detail_view_not_opening()

        # do_update: update, but skip switching to page 1 and getting assets
        return ModeUpdate.IMPORTED_ONLY

    def _set_page_size(self) -> Tuple[int, bool]:
        per_page = int(self.mode.split("@")[1])
        if cTB.settings["page"] == per_page:
            return 0, False

        cTB.settings["page"] = per_page
        # do_update and clear_cache
        # do_update: update and switch to page 1
        return ModeUpdate.IMPORTED_AND_GET_ASSETS_AND_PAGE_1, True

    def _clear_search(self) -> None:
        props = get_window_manager_props()
        if self.mode.endswith(KEY_TAB_ONLINE):
            props.search_poliigon = ""
        elif self.mode.endswith(KEY_TAB_MY_ASSETS):
            props.search_my_assets = ""
        elif self.mode.endswith(KEY_TAB_IMPORTED):
            props.search_imported = ""
        cTB.flush_thumb_prefetch_queue()

        check_and_report_detail_view_not_opening()

    @staticmethod
    def _clear_email() -> None:
        props = get_window_manager_props()
        props.vEmail = ""

    @staticmethod
    def _clear_password() -> None:
        props = get_window_manager_props()
        props.vPassHide = ""
        props.vPassShow = ""

    @staticmethod
    def _show_password() -> None:
        # Can be removed if we're not going use the "show password" button
        props = get_window_manager_props()
        # TODO(Andreas): strange toggle logic?
        if cTB.settings["show_pass"]:
            props.vPassHide = (props.vPassShow)
        else:
            props.vPassShow = (props.vPassHide)
        cTB.settings["show_pass"] = not cTB.settings["show_pass"]

    def _set_thumb_size(self) -> None:
        size = self.mode.split("@")[1]
        if cTB.settings["thumbsize"] == size:
            return
        cTB.settings["thumbsize"] = size
        cTB.refresh_ui()

    def _set_mode(self) -> int:
        cTB.settings[self.mode] = not cTB.settings[self.mode]

        # Update the session reference of this setting too.
        do_update = ModeUpdate.NO_UPDATE
        if self.mode == "download_link_blend":
            cTB.link_blend_session = cTB.settings[self.mode]
        elif self.mode == "download_prefer_blend":
            cTB._asset_index.flush_is_local()
            cTB._asset_index.update_all_local_assets(
                library_dirs=cTB.get_library_paths())
            cTB.refresh_ui()
        elif self.mode == "hdri_use_jpg_bg":
            # do_update: update, but skip switching to page 1
            do_update = ModeUpdate.IMPORTED_AND_GET_ASSETS
        return do_update

    def _set_default(self) -> int:
        key = self.mode.split("_")[1]
        value = self.mode.split("_")[2]
        cTB.settings[key] = value

        if not self.mode.startswith("default_hdri"):
            cTB.refresh_ui()
            return 0  # do_update: no update

        idx_size_exr = HDRI_RESOLUTIONS.index(
            cTB.settings["hdri"])
        idx_size_jpg = HDRI_RESOLUTIONS.index(
            cTB.settings["hdrib"])
        if idx_size_jpg <= idx_size_exr:
            idx_size_jpg_new = min(idx_size_exr + 1,
                                   len(HDRI_RESOLUTIONS) - 1)
            cTB.settings["hdrib"] = HDRI_RESOLUTIONS[idx_size_jpg_new]
        # do_update: update, but skip switching to page 1
        return ModeUpdate.IMPORTED_AND_GET_ASSETS

    def _disable_library_directory(self) -> None:
        directory = self.mode.replace("disable_dir_", "")
        if directory in cTB.settings["disabled_dirs"]:
            cTB.settings["disabled_dirs"].remove(directory)
            cTB.logger.info(f"Enabled directory: {directory}")
            cTB.add_library_path(
                directory, primary=False, update_local_assets=True)
        else:
            cTB.settings["disabled_dirs"].append(directory)
            cTB.logger.info(f"Disabled directory: {directory}")
            cTB.remove_library_path(
                directory, update_local_assets=True)
        cTB.refresh_ui()

    def _forget_library_directory(self) -> None:
        directory = self.mode.replace("del_dir_", "")
        cTB.remove_library_path(
            directory, update_local_assets=True)
        cTB.refresh_ui()

    def _toggle_material_property(self) -> None:
        prop = self.mode.split("@")[1]
        if prop in cTB.settings["mat_props"]:
            cTB.settings["mat_props"].remove(prop)
        else:
            cTB.settings["mat_props"].append(prop)

    @staticmethod
    def _view_more() -> int:
        props = get_window_manager_props()
        area = cTB.settings["area"]

        prev_area = area
        area = KEY_TAB_ONLINE

        cTB.settings["area"] = area
        cat_area = cTB.settings["category"][prev_area]
        cTB.settings["category"][area] = cat_area
        cTB.settings["show_settings"] = 0
        cTB.settings["show_user"] = 0
        cTB.vSearch[KEY_TAB_ONLINE] = cTB.vSearch[prev_area]
        props.search_poliigon = cTB.vSearch[prev_area]
        cTB.vActiveAsset = None
        # do_update: update, but skip switching to page 1
        return ModeUpdate.IMPORTED_AND_GET_ASSETS

    @staticmethod
    def _do_clear_cache(clear_cache: bool) -> None:
        if not clear_cache:
            return
        # TODO(Andreas): I assume somebody planned some cTB.thumbs refresh
        #                or something?

    @staticmethod
    def _do_update(do_update: int) -> None:
        if not do_update:
            return

        area = cTB.settings["area"]
        cTB.flush_thumb_prefetch_queue()

        if do_update == ModeUpdate.IMPORTED_AND_GET_ASSETS_AND_PAGE_1:
            cTB.vPage[area] = 0
            cTB.vPages[area] = 1

        # Not setting cursor as it can lead to being stuck on "wait".
        # bpy.context.window.cursor_set("WAIT")

        # TODO(SOFT-762): refactor to cache raw API request, also validate
        # if this needs re-requesting (has calls to f_GetCategoryChildren).

        # TODO(Andreas): disabled, when going addon-core
        # cTB.f_GetCategories()

        # TODO(Andreas): redundant?
        cTB.f_GetSceneAssets()

        if do_update < ModeUpdate.IMPORTED_ONLY:
            if area in [KEY_TAB_ONLINE, KEY_TAB_MY_ASSETS, KEY_TAB_IMPORTED]:
                cTB.f_GetAssets(area=area)

        cTB.refresh_ui()

    @reporting.handle_operator()
    def execute(self, context):
        cTB.logger.debug(f"POLIIGON_OT_setting: mode='{self.mode}'")

        get_ui_scale(cTB)  # Force update DPI check for scale.
        do_update = ModeUpdate.NO_UPDATE
        clear_cache = False

        if self.mode in ["none", ""]:
            return {"FINISHED"}
        elif self.mode == "set_library":
            do_update = self._set_library()
        elif self.mode.startswith("area_"):
            do_update = self._set_area()
        elif self.mode == "my_account":
            self._show_my_account()
            return {"FINISHED"}
        elif self.mode == "settings":
            self._show_settings()
            return {"FINISHED"}
        elif self.mode.startswith("category_"):
            do_update = self._set_category()
        elif self.mode.startswith("page_"):
            do_update = self._set_page()
        elif self.mode.startswith("page@"):
            do_update, clear_cache = self._set_page_size()
        elif self.mode.startswith("clear_search_"):
            self._clear_search()
        elif self.mode == "clear_email":
            self._clear_email()
        elif self.mode == "clear_pass":
            self._clear_password()
        elif self.mode == "show_pass":
            self._show_password()
        elif self.mode.startswith("thumbsize@"):
            self._set_thumb_size()
        elif self.mode in [
            "apply_subdiv",
            "auto_download",
            "download_lods",
            "download_prefer_blend",
            "download_link_blend",
            "hdri_use_jpg_bg",
            "mat_props_edit",
            "new_top",
            "one_click_purchase",
            "show_active",
            "show_add_dir",
            "show_asset_info",
            "show_credits",
            "show_default_prefs",
            "show_display_prefs",
            "show_import_prefs",
            "show_asset_browser_prefs",
            "show_mat_ops",
            "show_mat_props",
            "show_mat_texs",
            "show_plan",
            "show_feedback",
            "show_settings",
            "show_user",
            "use_16"
        ]:
            do_update = self._set_mode()
        elif self.mode.startswith("default_"):
            do_update = self._set_default()
        elif self.mode.startswith("disable_dir_"):
            self._disable_library_directory()
        elif self.mode.startswith("del_dir_"):
            self._forget_library_directory()
        elif self.mode.startswith("prop@"):
            self._toggle_material_property()
        elif self.mode == "view_more":
            do_update = self._view_more()
        elif self.mode == "search_free":
            do_update = self._set_free_search()
        else:
            reporting.capture_message("invalid_setting_mode", self.mode)
            self.report(
                {"WARNING"}, _t("Invalid setting mode {0}").format(self.mode))
            return {'CANCELLED'}

        self._do_clear_cache(clear_cache)
        self._do_update(do_update)
        save_settings(cTB)
        return {"FINISHED"}
