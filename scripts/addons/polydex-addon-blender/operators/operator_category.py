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

from typing import List

import bpy

from bpy.types import Operator
from bpy.props import StringProperty

from ..modules.poliigon_core.api_remote_control_params import (
    CATEGORY_ALL,
    KEY_TAB_ONLINE)
from ..modules.poliigon_core.multilingual import _t
from ..build import (
    BUILD_OPTION_BOB,
    PREFIX_OP)
from ..toolbox import get_context
from .. import reporting


class POLIIGON_OT_category(Operator):
    bl_idname = f"{PREFIX_OP}.poliigon_category"
    bl_label = _t("Select a Category")
    bl_description = _t("Select a Category")
    bl_options = {"REGISTER", "INTERNAL"}

    tooltip: StringProperty(options={"HIDDEN"})  # noqa: F821
    data: StringProperty(options={"HIDDEN"})  # noqa: F821

    @staticmethod
    def init_context(addon_version: str) -> None:
        """Called from operators.py to init global addon context."""

        global cTB
        cTB = get_context(addon_version)

    @classmethod
    def description(cls, context, properties):
        return properties.tooltip

    @staticmethod
    def _show_categories_menu(cTB, categories: List[str], index: str) -> None:
        """Generates the popup menu to display category selection options."""

        @reporting.handle_draw()
        def draw(self, context):
            layout = self.layout
            row = layout.row()
            col = row.column(align=True)

            for idx_category in range(len(categories)):
                if idx_category > 0 and idx_category % 15 == 0:
                    col = row.column(align=True)

                button = categories[idx_category]
                if BUILD_OPTION_BOB:
                    if button != CATEGORY_ALL:
                        bo_libraries = cTB.bo_listener.bo_libraries
                        path_entry = bo_libraries.get_path_entry_by_key(button)
                        is_library_enabled = path_entry.library.enabled
                        button_label = path_entry.name
                    else:
                        is_library_enabled = True
                        button_label = button
                else:
                    button_label = button
                row_op = col.row()
                op = row_op.operator(
                    f"{PREFIX_OP}.poliigon_setting", text=button_label)
                op.mode = f"category_{index}_{button}"
                op.tooltip = _t("Select {0}").format(button_label)
                row_op.enabled = is_library_enabled

                if idx_category == 0:
                    col.separator()

            area = cTB.settings["area"]
            if area == KEY_TAB_ONLINE and index == "0":
                col.separator()

                tooltip = _t("Search for Free Assets")
                op = col.operator(f"{PREFIX_OP}.poliigon_setting", text=_t("Free"))
                op.mode = "search_free"
                op.tooltip = tooltip

        bpy.context.window_manager.popup_menu(draw)

    def execute(self, context):
        idx = self.data.split("@")[0]
        categories = self.data.split("@")[1:]

        self._show_categories_menu(
            cTB,
            categories=categories,
            index=idx
        )

        return {"FINISHED"}
