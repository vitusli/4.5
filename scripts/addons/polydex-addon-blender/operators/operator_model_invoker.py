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
from bpy.props import (
    IntProperty,
    StringProperty,
)
from ..build import PREFIX_OP
from ..modules.poliigon_core.multilingual import _t
from ..toolbox import get_context
from .. import reporting
from ..modules.poliigon_core.assets import ModelType


class POLIIGON_OT_model_invoker(Operator):
    bl_idname = f"{PREFIX_OP}.model_invoker"
    bl_label = _t("Import model")
    bl_description = _t("Imports a model of any supported file extension by invoking the native importer")
    bl_options = {"REGISTER", "INTERNAL"}

    asset_id: IntProperty(options={"HIDDEN"})  # noqa: F821
    tooltip: StringProperty(options={"HIDDEN"})  # noqa: F821
    filepath: StringProperty()  # noqa: F821
    model_type: IntProperty()  # noqa: F821

    @classmethod
    def description(cls, context, properties):
        return cls.bl_description

    @staticmethod
    def init_context(addon_version: str) -> None:
        """Called from operators.py to init global addon context."""

        global cTB
        cTB = get_context(addon_version)

    @reporting.handle_operator()
    def execute(self, context):
        model_enum = ModelType(self.model_type)
        print(f"For {self.asset_id}, got {self.filepath} with type {model_enum}")

        args = ['INVOKE_DEFAULT']
        kwargs = {}
        oper = ""

        if model_enum == ModelType.BLEND:
            oper = "wm.append"
            kwargs["filepath"] = self.filepath
        elif model_enum == ModelType.FBX:
            print("FBX model")
            oper = "import_scene.fbx"
            kwargs["filepath"] = self.filepath
        elif model_enum == ModelType.GLTF:
            oper = "import_scene.gltf"
            kwargs["filepath"] = self.filepath
        elif model_enum == ModelType.OBJ:
            oper = "wm.obj_import"
            kwargs["filepath"] = self.filepath
        elif model_enum == ModelType.STL:
            oper = "wm.stl_import"
            kwargs["filepath"] = self.filepath
        elif model_enum == ModelType.USD:
            oper = "wm.usd_import"
            kwargs["filepath"] = self.filepath

        # Apply to the operator itself, and call
        base, oprs = oper.split(".")
        oper_func = getattr(getattr(bpy.ops, base), oprs)

        # May invoke popup, modal likely lasts past this operator's execution.
        # Pass both invoke and parameter values.
        oper_func(*args, **kwargs)

        cTB.signal_import_asset(self.asset_id, method="object")
        return {'FINISHED'}
