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

import os

import bpy
from bpy.types import Operator
from bpy.props import BoolProperty

from ..modules.poliigon_core.multilingual import _t
from ..dialogs.utils_dlg import get_ui_scale, wrapped_label
from ..build import PREFIX_OP
from ..constants import (
    POPUP_WIDTH_LABEL,
    POPUP_WIDTH_NARROW,
    POPUP_WIDTH_LABEL_NARROW)
from ..toolbox import get_context
from ..toolbox_settings import save_settings
from ..utils import load_image
from .. import reporting


class POLIIGON_OT_popup_welcome(Operator):
    bl_idname = f"{PREFIX_OP}.popup_welcome"
    bl_label = _t("Welcome to the Poliigon Addon")
    bl_options = {"INTERNAL", "REGISTER", "UNDO"}

    force: BoolProperty(options={"HIDDEN"}, default=False)  # noqa: F821

    @staticmethod
    def init_context(addon_version: str) -> None:
        """Called from operators.py to init global addon context."""

        global cTB
        cTB = get_context(addon_version)

    def _load_images(self) -> None:
        path = os.path.join(cTB.dir_script, "onboarding_welcome.png")
        self.img_welcome = load_image("POPUP_welcome", path)

    def invoke(self, context, event):
        if cTB.is_unlimited_user():
            return {'FINISHED'}
        if cTB.settings["popup_welcome"] and not self.force:
            return {'FINISHED'}

        self._load_images()
        cTB.settings["popup_welcome"] = 1
        save_settings(cTB)
        return context.window_manager.invoke_props_dialog(
            self, width=POPUP_WIDTH_NARROW)

    @reporting.handle_draw()
    def draw(self, context):
        label_width = POPUP_WIDTH_LABEL_NARROW * get_ui_scale(cTB)
        # Accounting for the left+right border columns (eyeballing):
        if bpy.app.version >= (4, 0):
            label_width -= 10.0
        elif bpy.app.version >= (3, 0):
            # TODO(Andreas): Scale for other versions and in other popups, too?
            label_width -= 25.0 * get_ui_scale(cTB)
        else:
            label_width -= 10.0

        col_content = self.layout.column()

        col_image = col_content.column()
        col_image.scale_y = 0.5
        col_image.template_icon(
            icon_value=self.img_welcome.preview.icon_id,
            scale=18.0)

        row_text = col_content.row()
        if bpy.app.version >= (3, 0):
            col_left_gap = row_text.column()
            col_left_gap.alignment = "LEFT"
            col_left_gap.label(text=" ")
            col_text = row_text.column()
            col_right_gap = row_text.column()
            col_right_gap.alignment = "RIGHT"
            col_right_gap.label(text=" ")
        else:
            col_left_gap = row_text.column()
            col_left_gap.alignment = "LEFT"
            # Note, here no label in left column. Otherwise we'd end up with a
            # way too larger border gap.
            col_text = row_text.column()
            col_text.alignment = "CENTER"

        wrapped_label(
            cTB,
            width=label_width,
            text=_t('Preview any texture by clicking the "eye" icon.'),
            container=col_text,
            add_padding=True)
        wrapped_label(
            cTB,
            width=label_width,
            text=_t("Download, import and apply in just two clicks."),
            container=col_text,
            add_padding_bottom=True)

    @reporting.handle_operator(silent=True)
    def execute(self, context):
        cTB.refresh_ui()
        return {'FINISHED'}


class POLIIGON_OT_popup_first_download(Operator):
    bl_idname = f"{PREFIX_OP}.popup_first_download"
    bl_label = _t("Purchased, download started")
    bl_options = {"INTERNAL", "REGISTER", "UNDO"}

    force: BoolProperty(options={"HIDDEN"}, default=False)  # noqa: F821

    @staticmethod
    def init_context(addon_version: str) -> None:
        """Called from operators.py to init global addon context."""

        global cTB
        cTB = get_context(addon_version)

    def invoke(self, context, event):
        if cTB.is_unlimited_user():
            return {'FINISHED'}
        if cTB.settings["popup_download"] and not self.force:
            return {'FINISHED'}

        cTB.settings["popup_download"] = 1
        cTB.signal_popup(popup="ONBOARD_PURCHASE")
        save_settings(cTB)
        return context.window_manager.invoke_props_popup(self, event)

    @reporting.handle_draw()
    def draw(self, context):
        label_width = POPUP_WIDTH_LABEL * get_ui_scale(cTB)

        col_content = self.layout.column()
        wrapped_label(
            cTB,
            width=label_width,
            text=_t("Thanks for purchasing your first Poliigon Asset!"),
            container=col_content)
        wrapped_label(
            cTB,
            width=label_width,
            text=_t("By default Show Purchase Confirmation is disabled. You "
                    "can adjust this as well as your default download "
                    "settings in preferences."),
            container=col_content,
            add_padding=True)

        op = col_content.operator(
            f"{PREFIX_OP}.open_preferences",
            text="View Preferences"
        )
        op.set_focus = "show_default_prefs"

    @reporting.handle_operator(silent=True)
    def execute(self, context):
        cTB.refresh_ui()
        return {'FINISHED'}
