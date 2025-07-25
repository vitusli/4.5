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

from bpy.types import Operator

from ..modules.poliigon_core.multilingual import _t
from ..build import PREFIX_OP
from ..toolbox import get_context
from .. import reporting


class POLIIGON_OT_check_update(Operator):
    bl_idname = f"{PREFIX_OP}.check_update"
    bl_label = _t("Check for update")
    bl_description = _t("Check for any addon updates")
    bl_options = {"INTERNAL"}

    @staticmethod
    def init_context(addon_version: str) -> None:
        """Called from operators.py to init global addon context."""

        global cTB
        cTB = get_context(addon_version)

    @reporting.handle_operator(silent=True)
    def execute(self, context):
        cTB.logger.debug("Started check for update with "
                         f"{cTB._updater.addon_version} "
                         f"{cTB._updater.software_version}")
        cTB._updater.async_check_for_update(
            callback=cTB.check_update_callback, create_notifications=True)
        cTB.logger.debug("Update ready? "
                         f"{cTB._updater.update_ready}"
                         f"{cTB._updater.update_data}")
        return {'FINISHED'}
