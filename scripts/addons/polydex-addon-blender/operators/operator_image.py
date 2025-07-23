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
from typing import List

from bpy.types import Operator
from bpy.props import (
    BoolProperty,
    IntProperty)
import bpy

from ..modules.poliigon_core.assets import TextureMap
from ..modules.poliigon_core.multilingual import _t
from ..build import PREFIX_OP
from ..toolbox import get_context
from .. import reporting
from ..utils import load_image


class POLIIGON_OT_image(Operator):
    bl_idname = f"{PREFIX_OP}.poliigon_image"
    bl_label = _t("Image Import")
    bl_description = _t("Import Polydex image as a plane or datablock.")
    bl_options = {"GRAB_CURSOR", "BLOCKING", "REGISTER", "INTERNAL", "UNDO"}

    asset_id: IntProperty(options={"HIDDEN"})  # noqa: F821
    do_as_planes: BoolProperty(options={"HIDDEN"}, default=False)  # noqa: F821

    def __init__(self, *args, **kwargs):
        """Runs once per operator call before drawing occurs."""
        super().__init__(*args, **kwargs)

        # Note: During property update handlers (like e.g.
        #       _update_displacement_options()) we can not rely on these
        #       members to be defined!
        self.exec_count = 0

    @staticmethod
    def init_context(addon_version: str) -> None:
        """Called from operators.py to init global addon context."""

        global cTB
        cTB = get_context(addon_version)

    @classmethod
    def description(cls, context, properties):
        return cls.bl_description

    def load_as_data_blocks(self, tex_maps: List[TextureMap]) -> None:
        for _tex_map in tex_maps:
            path_img = _tex_map.get_path()
            img = load_image(
                _tex_map.filename,
                path_img,
                hidden=False,
                do_set_colorspace=False,
                do_remove_alpha=False,
                force=True)
            if img is None:
                print(f"Failed to load {path_img}")

    def load_as_planes(self, tex_maps: List[TextureMap]) -> None:
        files = []
        for _tex_map in tex_maps:
            path_img = _tex_map.get_path()
            path_img = os.path.normpath(path_img)
            filename = _tex_map.filename

            # NOTE: It was not my idea, to have two "name" keys.
            #       That's what Blender gave me in its Info panel
            #       for this operator...
            img_entry = {"name": filename, "name": path_img}  # noqa: F601
            files.append(img_entry)

        bpy.ops.image.import_as_mesh_planes(
            relative=False,
            filepath="",
            files=files,
            directory="")

    def signal_import(self) -> None:
        if self.exec_count == 0:
            if self.do_as_planes:
                method = "plane"
            else:
                method = "datablock"
            cTB.signal_import_asset(asset_id=self.asset_id, method=method)
        self.exec_count += 1

    @reporting.handle_operator()
    def execute(self, context):
        asset_data = cTB._asset_index.get_asset(self.asset_id)
        if asset_data is None:
            return {'CANCELLED'}

        asset_type_data = asset_data.get_type_data()

        workflow = asset_type_data.get_workflow(get_local=True)
        size = asset_type_data.get_size(
            size="1K",
            local_only=True,
            addon_convention=cTB.addon_convention,
            local_convention=0)

        tex_maps = asset_type_data.get_maps(
            workflow=workflow,
            size=size,
            lod=None,
            prefer_16_bit=True,
            variant=None,
            effective=True,
            map_preferences=None
        )

        if self.do_as_planes:
            self.load_as_planes(tex_maps)
        else:
            self.load_as_data_blocks(tex_maps)

        self.signal_import()

        return {'FINISHED'}
