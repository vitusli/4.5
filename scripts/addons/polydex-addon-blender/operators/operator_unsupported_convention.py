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

from bpy.props import StringProperty, BoolProperty
from bpy.types import Operator

from ..modules.poliigon_core.multilingual import _t
from ..build import PREFIX_OP
from ..toolbox import get_context
from ..dialogs.dlg_popup import open_popup
from .. import reporting


class POLIIGON_OT_unsupported_convention(Operator):
    bl_idname = f"{PREFIX_OP}.unsupported_convention"
    bl_label = _t("Unsupported")
    bl_description = _t(
        "Addon does not support asset convention, try updating the addon")
    bl_options = {'REGISTER', 'INTERNAL'}

    tooltip: StringProperty(options={"HIDDEN"})  # noqa: F821
    suggest_update: BoolProperty(default=True, options={"HIDDEN"})  # noqa: F821

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
        # TODO(Andreas): Does this work for translation?
        if self.suggest_update:
            msg = _t(
                "Asset not supported, please update plugin. "
                "This asset is published with newer conventions to improve "
                "render outputs."
            )
        else:
            msg = _t(
                "Asset type not yet supported, "
                "but may be supported in the near future. Share you feedback "
                "to help let us know!"
            )
        title = _t("Addon Update Needed") if self.suggest_update else _t("Asset not yet supported")
        commands = ["check_update", "open_p4b_url"] if self.suggest_update else ["open_p4b_url"]
        open_popup(
            cTB,
            title=title,
            msg=msg,
            buttons=[_t("OK"), _t("Update")],
            commands=commands,
            mode=None,
            w_limit=210)
        return {"FINISHED"}
