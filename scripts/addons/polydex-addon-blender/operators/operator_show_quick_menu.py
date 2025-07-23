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

import bpy
from bpy.types import Operator
from bpy.props import (BoolProperty,
                       IntProperty,
                       StringProperty)
import bpy.utils.previews

from ..modules.poliigon_core.multilingual import _t
from ..dialogs.dlg_quickmenu import show_quick_menu
from ..build import PREFIX_OP
from ..toolbox import get_context
from .. import reporting
from .operator_detail_view import check_and_report_detail_view_not_opening


class POLIIGON_OT_show_quick_menu(Operator):
    bl_idname = f"{PREFIX_OP}.show_quick_menu"
    bl_label = ""
    bl_description = _t("Show quick menu")

    asset_id: IntProperty(options={"HIDDEN"})  # noqa: F821
    hide_detail_view: BoolProperty(options={"HIDDEN"}, default=False)  # noqa: F821
    tooltip: StringProperty(options={"HIDDEN"})  # noqa: F821

    @staticmethod
    def init_context(addon_version: str) -> None:
        """Called from operators.py to init global addon context."""

        global cTB
        cTB = get_context(addon_version)

    @classmethod
    def description(cls, context, properties):
        return properties.tooltip

    @reporting.handle_operator()
    def execute(self, context):
        if bpy.app.background:
            return {'CANCELLED'}  # Don't popup menus when running headless.

        check_and_report_detail_view_not_opening()

        asset_data = cTB._asset_index.get_asset(self.asset_id)
        show_quick_menu(
            cTB, asset_data=asset_data, hide_detail_view=self.hide_detail_view)
        return {'FINISHED'}
