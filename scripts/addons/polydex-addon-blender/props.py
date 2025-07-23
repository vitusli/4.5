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
from .build import (
    BUILD_OPTION_P4B,
    BUILD_OPTION_BOB)
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


classes_p4b = (
    PoliigonImageProps,
    PoliigonMaterialProps,
    PoliigonObjectProps,
    PoliigonWorldProps,
    PoliigonUserProps,
)

if BUILD_OPTION_P4B:
    classes = classes_p4b
elif BUILD_OPTION_BOB:
    BOBImageProps = PoliigonImageProps
    BOBMaterialProps = PoliigonMaterialProps
    BOBObjectProps = PoliigonObjectProps
    BOBWorldProps = PoliigonWorldProps
    BOBUserProps = PoliigonUserProps

    classes_bob = (
        BOBImageProps,
        BOBMaterialProps,
        BOBObjectProps,
        BOBWorldProps,
        BOBUserProps,
    )

    classes = classes_bob


def register_p4b():
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

    # TODO(Andreas): Neither vEditText nor vDispDetail seems in use...
    bpy.types.Scene.vEditText = StringProperty(default="")
    bpy.types.Scene.vDispDetail = FloatProperty(default=1.0, min=0.1, max=10.0)
    # TODO(Andreas): We should get rid of these in favor of PoliigonMaterialProps...
    bpy.types.Scene.vEditMatName = StringProperty(default="")

    # TODO(Andreas): ...and we should get rid of these as well.
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


def register_bob():
    bpy.types.WindowManager.bob_props = PointerProperty(
        type=BOBUserProps
    )
    bpy.types.Material.bob_props = PointerProperty(
        type=BOBMaterialProps
    )
    bpy.types.Object.bob_props = PointerProperty(
        type=BOBObjectProps
    )
    bpy.types.World.bob_props = PointerProperty(
        type=BOBWorldProps
    )
    bpy.types.Image.bob_props = PointerProperty(
        type=BOBImageProps
    )

    bpy.context.window_manager.bob_props.search_poliigon = ""
    bpy.context.window_manager.bob_props.search_my_assets = ""
    bpy.context.window_manager.bob_props.search_imported = ""


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    if BUILD_OPTION_P4B:
        register_p4b()
    elif BUILD_OPTION_BOB:
        register_bob()


def unregister_p4b():
    del bpy.types.Scene.vDispDetail
    del bpy.types.Scene.vEditText
    del bpy.types.Scene.vEditMatName

    del bpy.types.Image.poliigon_props
    del bpy.types.World.poliigon_props
    del bpy.types.Object.poliigon_props
    del bpy.types.Material.poliigon_props
    del bpy.types.WindowManager.poliigon_props


def unregister_bob():
    del bpy.types.Image.bob_props
    del bpy.types.World.bob_props
    del bpy.types.Object.bob_props
    del bpy.types.Material.bob_props
    del bpy.types.WindowManager.bob_props


def unregister():
    if BUILD_OPTION_P4B:
        unregister_p4b()
    elif BUILD_OPTION_BOB:
        unregister_bob()

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
