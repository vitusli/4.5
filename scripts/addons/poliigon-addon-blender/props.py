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


from bpy.props import (
    FloatProperty,
    PointerProperty,
    StringProperty,
)
import bpy.utils.previews

from .modules.poliigon_core.multilingual import _t
from .preferences_map_prefs import MapPrefProperties


class PoliigonUserProps(bpy.types.PropertyGroup):
    vEmail: StringProperty(
        name="",  # noqa: F722
        description=_t("Your Email"),  # noqa: F722
        options={"SKIP_SAVE"}  # noqa: F821
    )
    vPassShow: StringProperty(
        name="",  # noqa: F722
        description=_t("Your Password"),  # noqa: F722
        options={"SKIP_SAVE"}  # noqa: F821
    )
    vPassHide: StringProperty(
        name="",  # noqa: F722
        description=_t("Your Password"),  # noqa: F722
        options={"HIDDEN", "SKIP_SAVE"},  # noqa: F821
        subtype="PASSWORD",  # noqa: F821
    )
    search_poliigon: StringProperty(
        name="",  # noqa: F722
        default="",  # noqa: F722
        description=_t("Search Poliigon Assets"),  # noqa: F722
        options={"SKIP_SAVE"},  # noqa: F821
    )
    search_my_assets: StringProperty(
        name="",  # noqa: F722
        default="",  # noqa: F722
        description=_t("Search My Assets"),  # noqa: F722
        options={"SKIP_SAVE"},  # noqa: F821
    )
    search_imported: StringProperty(
        name="",  # noqa: F722
        default="",  # noqa: F722
        description=_t("Search Imported Assets"),  # noqa: F722
        options={"SKIP_SAVE"},  # noqa: F821
    )


# TODO(Andreas): Only HDRI imports or tex as well?
class PoliigonImageProps(bpy.types.PropertyGroup):
    """Properties saved to an individual image"""

    # Properties common to all asset types
    asset_name: bpy.props.StringProperty()
    asset_id: bpy.props.IntProperty(default=-1)
    asset_type: bpy.props.StringProperty()

    # Image specific properties
    size: bpy.props.StringProperty()
    size_bg: bpy.props.StringProperty()
    hdr_strength: FloatProperty()
    rotation: FloatProperty()


class PoliigonMaterialProps(bpy.types.PropertyGroup):
    """Properties saved to an individual material"""

    # Properties common to all asset types
    asset_name: bpy.props.StringProperty()
    asset_id: bpy.props.IntProperty(default=-1)
    asset_type: bpy.props.StringProperty()

    # Material specific properties
    size: bpy.props.StringProperty()  # resolution, but kept size name to stay consistent
    mapping: bpy.props.StringProperty()
    scale: bpy.props.FloatProperty()
    displacement: bpy.props.FloatProperty()
    use_16bit: bpy.props.BoolProperty(default=False)
    mode_disp: bpy.props.StringProperty()
    is_backplate: bpy.props.BoolProperty(default=False)
    map_prefs: bpy.props.PointerProperty(type=MapPrefProperties)


class PoliigonObjectProps(bpy.types.PropertyGroup):
    """Properties saved to an individual object"""

    # Properties common to all asset types
    asset_name: bpy.props.StringProperty()
    asset_id: bpy.props.IntProperty(default=-1)
    asset_type: bpy.props.StringProperty()

    # Model/object specific properties
    # TODO(Andreas): Added this as I felt it missing
    size: bpy.props.StringProperty()
    lod: bpy.props.StringProperty()
    use_collection: bpy.props.BoolProperty(default=False)
    link_blend: bpy.props.BoolProperty(default=False)


class PoliigonWorldProps(bpy.types.PropertyGroup):
    """Properties saved to an individual world shader"""

    # Properties common to all asset types
    asset_name: bpy.props.StringProperty()
    asset_id: bpy.props.IntProperty(default=-1)
    asset_type: bpy.props.StringProperty()

    # HDRI specific properties
    size: bpy.props.StringProperty()
    size_bg: bpy.props.StringProperty()
    hdr_strength: FloatProperty()
    rotation: FloatProperty()


classes = (
    PoliigonImageProps,
    PoliigonMaterialProps,
    PoliigonObjectProps,
    PoliigonWorldProps,
    PoliigonUserProps,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.WindowManager.poliigon_props = PointerProperty(
        type=PoliigonUserProps
    )
    bpy.types.Material.poliigon_props = PointerProperty(
        type=PoliigonMaterialProps
    )
    bpy.types.Object.poliigon_props = PointerProperty(
        type=PoliigonObjectProps
    )
    bpy.types.World.poliigon_props = PointerProperty(
        type=PoliigonWorldProps
    )
    bpy.types.Image.poliigon_props = PointerProperty(
        type=PoliigonImageProps
    )

    bpy.types.Scene.vEditText = StringProperty(default="")
    bpy.types.Scene.vEditMatName = StringProperty(default="")
    bpy.types.Scene.vDispDetail = FloatProperty(default=1.0, min=0.1, max=10.0)

    bpy.types.Material.poliigon = StringProperty(default="", options={"HIDDEN"})
    bpy.types.Object.poliigon = StringProperty(default="", options={"HIDDEN"})
    bpy.types.Object.poliigon_lod = StringProperty(default="", options={"HIDDEN"})
    bpy.types.Image.poliigon = StringProperty(default="", options={"HIDDEN"})

    bpy.context.window_manager.poliigon_props.vEmail = ""
    bpy.context.window_manager.poliigon_props.vPassShow = ""
    bpy.context.window_manager.poliigon_props.vPassHide = ""
    bpy.context.window_manager.poliigon_props.search_poliigon = ""
    bpy.context.window_manager.poliigon_props.search_my_assets = ""
    bpy.context.window_manager.poliigon_props.search_imported = ""


def unregister():
    del bpy.types.Scene.vDispDetail
    del bpy.types.Scene.vEditMatName
    del bpy.types.Scene.vEditText

    del bpy.types.Image.poliigon_props
    del bpy.types.World.poliigon_props
    del bpy.types.Object.poliigon_props
    del bpy.types.Material.poliigon_props
    del bpy.types.WindowManager.poliigon_props

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
