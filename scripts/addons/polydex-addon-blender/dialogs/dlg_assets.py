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

from math import ceil
from typing import Dict, List, Optional, Tuple
import os

import bpy

from ..modules.poliigon_core.assets import (
    AssetData,
    AssetType,
    find_closest_size,
    ModelType)
from ..modules.poliigon_core.api_remote_control_params import (
    CATEGORY_ALL,
    KEY_TAB_IMPORTED,
    KEY_TAB_MY_ASSETS,
    KEY_TAB_ONLINE,
    IDX_PAGE_ACCUMULATED,
    PAGE_SIZE_ACCUMULATED)
from ..modules.poliigon_core.multilingual import _t
from .utils_dlg import (
    check_convention,
    check_dpi,
    get_model_op_details,
    get_ui_scale,
    safe_size_apply,
    wrapped_label)
from ..operators.operator_material import set_op_mat_disp_strength
from ..build import (
    BUILD_OPTION_BOB,
    BUILD_OPTION_P4B,
    PREFIX_ICON,
    PREFIX_OP)
from ..toolbox import DisplayError
from ..utils import get_entity_props


THUMB_SIZE_FACTOR = {"Tiny": 0.5,
                     "Small": 0.75,
                     "Medium": 1.0,
                     "Large": 1.5,
                     "Huge": 2.0}
W_THUMB_BASE = 170


def _get_imported_material(asset_id: int) -> Optional[bpy.types.Material]:
    """Returns the imported material belonging to given assetID (if any)."""

    mat_asset = None
    for _mat in bpy.data.materials:
        try:
            props_mat = get_entity_props(_mat)
            asset_id_mat = props_mat.asset_id
            if asset_id_mat != asset_id:
                continue
            mat_asset = _mat
            break
        except Exception:  # TODO(Andreas): correct exception for missing prop
            continue
    return mat_asset


def _build_assets_no_assets(cTB, area: str, category: str) -> None:
    box_not_found = cTB.vBase.box()

    if BUILD_OPTION_P4B:
        category = f"Poliigon {category}"
    elif BUILD_OPTION_BOB:
        if category != CATEGORY_ALL:
            # P4B encodes the asset type in a second "word"
            cats = category.split(" ")

            path_entry = cTB.bo_listener.bo_libraries.get_path_entry_by_key(
                cats[0])
            if path_entry is not None:
                category = path_entry.name
            else:
                category = cats[0]
    else:
        print("_build_assets_no_assets: UNKNOWN BUILD OPTION")

    label = _t("No {0} found in Library").format(category)
    if cTB.vSearch[area] != "":
        label = _t(
            "No results found."
            " Please try changing your filter or search term."
        )
    elif area == KEY_TAB_IMPORTED:
        label = _t("No {0} found in the Scene").format(category)
    elif area == KEY_TAB_ONLINE:
        label = _t("No {0} found Online").format(category)

    width = cTB.width_draw_ui - 20 * get_ui_scale(cTB)
    wrapped_label(cTB, width, label, box_not_found, add_padding=True)

    return box_not_found


def _determine_thumb_width(cTB, thumb_size_factor: float) -> float:
    thumb_width = ceil(W_THUMB_BASE * thumb_size_factor)
    thumb_width *= get_ui_scale(cTB)
    return thumb_width


def _determine_num_thumb_columns(
    cTB,
    thumb_width: float,
    sorted_assets: List[Dict]
) -> int:
    num_columns = int(cTB.width_draw_ui / thumb_width)
    num_columns = max(num_columns, 1)
    num_columns = min(num_columns, len(sorted_assets))
    return num_columns


def _determine_grid_padding(
        cTB,
        num_columns: int,
        thumb_width: float) -> float:
    padding = (cTB.width_draw_ui - (num_columns * thumb_width)) / 2
    if padding < 1.0 and num_columns > 1:
        num_columns -= 1
        padding = (cTB.width_draw_ui - (num_columns * thumb_width)) / 2
    return padding


def _build_assets_prepare_grid(cTB,
                               thumb_size_factor: float,
                               sorted_assets: List[Dict]
                               ) -> Tuple[bpy.types.UILayout, float, int]:
    thumb_width = _determine_thumb_width(cTB, thumb_size_factor)
    num_columns = _determine_num_thumb_columns(cTB, thumb_width, sorted_assets)
    padding = _determine_grid_padding(cTB, num_columns, thumb_width)

    split_right = None
    if padding >= 1.0 or thumb_width + 1 <= cTB.width_draw_ui:
        # Typical case, fit rows and columns.
        factor = padding / cTB.width_draw_ui
        split_left = cTB.vBase.split(factor=factor)

        split_left.separator()

        factor = 1.0 - factor
        split_right = split_left.split(factor=factor)

        container_grid = split_right
    else:
        # Panel is narrower than a single preview width, single col.
        container_grid = cTB.vBase

    grid = container_grid.grid_flow(
        row_major=True, columns=num_columns,
        even_columns=True, even_rows=True, align=False
    )

    if split_right is not None:
        split_right.separator()

    return grid, thumb_width, num_columns


def _determine_in_scene_sizes(cTB,
                              asset_data: AssetData,
                              size_default: str
                              ) -> Tuple[List[str], str]:
    asset_id = asset_data.asset_id

    query_key = cTB.get_accumulated_query_cache_key(tab=KEY_TAB_IMPORTED)
    if query_key not in cTB._asset_index.cached_queries:
        return [], size_default
    asset_ids_imported = cTB._asset_index.cached_queries[query_key]

    sizes_in_scene = []
    if asset_id not in asset_ids_imported:
        return sizes_in_scene, size_default

    asset_ids_no_longer_in_scene = asset_ids_imported.copy()

    # TODO(Andreas): Why is this cleanup happening in here???
    for _entities in [bpy.data.objects, bpy.data.materials, bpy.data.images]:
        for _entity in _entities:
            try:
                props_entity = get_entity_props(_entity)
                asset_id_entity = props_entity.asset_id

                if asset_id_entity in asset_ids_no_longer_in_scene:
                    asset_ids_no_longer_in_scene.remove(asset_id_entity)

                if asset_id_entity != asset_id:
                    continue
                sizes_in_scene.append(props_entity.size)
            except Exception:
                cTB.logger_ui.exception("Unexpected exception")

    for _asset_id in asset_ids_no_longer_in_scene:
        asset_ids_imported.remove(_asset_id)

    if sizes_in_scene and size_default not in sizes_in_scene and sizes_in_scene[0]:
        size_default = sizes_in_scene[0]

    return sizes_in_scene, size_default


def _draw_thumbnail(cTB,
                    asset_data: AssetData,
                    thumb_size_factor: float,
                    layout_box: bpy.types.UILayout) -> None:
    asset_name = asset_data.asset_name
    thumb_scale = cTB.settings["preview_size"] * thumb_size_factor

    # TODO(Andreas): If we used ThumbCache, instead of lines below
    # id_bmp, is_real = cTB.thumb_cache.get_thumb_bitmap(
    #     asset_id, cTB.callback_asset_update_ui)
    # layout_box.template_icon(
    #     icon_value=id_bmp,
    #     scale=thumb_scale
    # )

    with cTB.lock_thumbs:
        if asset_name == "dummy":
            layout_box.template_icon(
                icon_value=cTB.ui_icons[f"{PREFIX_ICON}ICON_get_preview"].icon_id,
                scale=thumb_scale
            )
        elif asset_name in cTB.thumbs.keys():
            layout_box.template_icon(
                icon_value=cTB.thumbs[asset_name].icon_id,
                scale=thumb_scale
            )
            asset_data.runtime.set_thumb_downloading(is_downloading=False)
        else:
            if asset_data.runtime.get_thumb_downloading():
                layout_box.template_icon(
                    icon_value=cTB.ui_icons[f"{PREFIX_ICON}ICON_get_preview"].icon_id,
                    scale=thumb_scale
                )

            else:
                layout_box.template_icon(
                    icon_value=cTB.ui_icons[f"{PREFIX_ICON}ICON_no_preview"].icon_id,
                    scale=thumb_scale
                )


def _draw_thumb_state_asset_dummy(layout_row: bpy.types.UILayout) -> None:
    op = layout_row.operator(f"{PREFIX_OP}.poliigon_setting", text="  ")
    op.mode = "none"


def _draw_thumb_state_asset_purchasing(
        layout_row: bpy.types.UILayout, asset_data: AssetData) -> None:
    credits = 0 if asset_data.credits is None else asset_data.credits
    is_free = credits == 0
    if is_free:
        label = _t("Starting...")
    else:
        label = _t("Purchasing...")

    row = layout_row.row()
    row.enabled = False
    op = row.operator(
        f"{PREFIX_OP}.poliigon_setting",
        text=label,
        emboss=1,
        depress=1,
    )
    op.mode = "none"
    op.tooltip = label


def _draw_thumb_state_asset_downloading(layout_row: bpy.types.UILayout,
                                        asset_data: AssetData,
                                        thumb_width: float
                                        ) -> None:
    asset_id = asset_data.asset_id
    asset_name = asset_data.asset_name

    progress = asset_data.state.dl.get_progress()
    progress = max(0.001, progress)

    layout_row.label(text="", icon="IMPORT")

    col = layout_row.column()
    col_cancel = layout_row.column()
    # Display cancel button instead of time remaining.
    ops = col_cancel.operator(f"{PREFIX_OP}.cancel_download",
                              emboss=False, text="", icon="X")
    ops.asset_id = asset_id

    spacer = col.row()
    spacer.scale_y = 0.2
    spacer.label(text="")

    row_progress = col.row()
    row_progress.scale_y = 0.4

    split_progress = row_progress.split(factor=progress, align=True)
    pcent = round(progress * 100, 1)
    # tooltip = f"Downloading ({pcent}%)\n{asset_name} @ {download_data['size']}..."
    # TODO(Andreas): AssetData does not have the size info during download, only after, atm...
    tooltip = _t("Downloading ({0}%)\n{1}...").format(pcent, asset_name)

    op = split_progress.operator(
        f"{PREFIX_OP}.poliigon_setting", text="", emboss=1, depress=1
    )
    op.mode = "none"
    op.tooltip = tooltip

    op = split_progress.operator(
        f"{PREFIX_OP}.poliigon_setting", text="", emboss=1, depress=0
    )
    op.mode = "none"
    op.tooltip = tooltip

    layout_row.separator()


def _draw_thumb_state_cancelling_download(
        layout_row: bpy.types.UILayout, asset_data: AssetData) -> None:
    label = _t("Cancelling...")

    row = layout_row.row()
    row.enabled = False
    op = row.operator(
        f"{PREFIX_OP}.poliigon_setting",
        text=label,
        emboss=1,
        depress=0,
    )
    op.mode = "none"
    op.tooltip = label


def _draw_button_quick_preview(
    cTB,
    layout_row: bpy.types.UILayout,
    asset_data: AssetData,
    is_selection: bool,
    have_text_label: bool = False
) -> None:
    if cTB.is_unlimited_user():
        return
    if not check_convention(asset_data):
        return

    asset_type_data = asset_data.get_type_data()
    asset_name = asset_data.asset_name
    asset_type = asset_data.asset_type
    if asset_type != AssetType.TEXTURE:
        return

    credits = 0 if asset_data.credits is None else asset_data.credits
    is_free = credits == 0
    is_backplate = asset_data.is_backplate()

    do_show = False
    # TODO(Andreas): confused about backplate handling...
    has_thumb_urls = len(asset_data.thumb_urls) > 0
    has_cf_thumb_urls = len(asset_data.cloudflare_thumb_urls) > 0
    if is_backplate and (has_thumb_urls or has_cf_thumb_urls):
        do_show = True
    elif len(asset_type_data.get_watermark_preview_url_list()):
        do_show = True

    if not do_show:
        return

    col_preview = layout_row.column(align=True)
    # Quick preview button gets disabled on free assets as they
    # don't need to be purchased (and their Purchase button was
    # changed into 'Download' woth an implicit auto-download)
    col_preview.enabled = not is_free

    popup_preview = cTB.settings["popup_preview"]
    if not popup_preview:
        name_op = f"{PREFIX_OP}.popup_first_preview"
    else:
        name_op = f"{PREFIX_OP}.poliigon_preview"

    if have_text_label:
        label = _t("Texture Preview")
    else:
        label = ""

    op = col_preview.operator(
        name_op,
        text=label,
        icon="HIDE_OFF",
        emboss=1,
    )
    op.asset_id = asset_data.asset_id
    if is_free:
        op.tooltip = _t(
            "{0} is free, just download and use it right away").format(
            asset_name)
    elif is_selection:
        op.tooltip = _t("Preview {0} on selected object(s)").format(asset_name)
    else:
        op.tooltip = _t(
            "Preview {0} on a plane created during import").format(asset_name)


def _draw_checkmark_purchased(cTB, layout_row: bpy.types.UILayout) -> None:
    col_checkmark = layout_row.column(align=True)
    col_checkmark.enabled = False
    icon_val = cTB.ui_icons[f"{PREFIX_ICON}ICON_acquired_check"].icon_id
    op = col_checkmark.operator(
        f"{PREFIX_OP}.poliigon_setting",
        text="",
        icon_value=icon_val,
        depress=False,
        emboss=True
    )
    op.tooltip = _t("Asset already acquired")


def _draw_checkmark_unlimited(cTB, layout_row: bpy.types.UILayout) -> None:
    col_checkmark = layout_row.column(align=True)
    col_checkmark.enabled = False
    icon_val = cTB.ui_icons[f"{PREFIX_ICON}ICON_unlimited_local"].icon_id
    op = col_checkmark.operator(
        f"{PREFIX_OP}.poliigon_setting",
        text="",
        icon_value=icon_val,
        depress=False,
        emboss=True
    )
    op.tooltip = _t("Asset found locally")


def _draw_button_model_local(cTB,
                             layout_row: bpy.types.UILayout,
                             asset_data: AssetData,
                             error: DisplayError
                             ) -> None:
    asset_type_data = asset_data.get_type_data()
    asset_id = asset_data.asset_id
    asset_name = asset_data.asset_name
    asset_type = asset_data.asset_type

    if BUILD_OPTION_P4B:
        size_desired = asset_data.runtime.get_current_size()
        if size_desired is None:
            size_desired = cTB.get_pref_size(asset_type)
        size = asset_type_data.get_size(
            size_desired,
            local_only=True,
            addon_convention=cTB._asset_index.addon_convention,
            local_convention=asset_data.get_convention(local=True))
    else:
        size = None

    if error:
        icon = "ERROR"
        label = error.button_label
        lod = "NONE"
        tip = error.description
    elif BUILD_OPTION_BOB:
        icon = "TRACKING_REFINE_BACKWARDS"
        tip = "{0} (import)".format(asset_data.asset_name)
    else:
        lod, label, tip = get_model_op_details(cTB, asset_data, size)
        if lod != "" and lod != "NONE":
            label = _t("Import {0}, {1}").format(size, lod)
        else:
            label = _t("Import {0}").format(size)
        icon = "TRACKING_REFINE_BACKWARDS"

    if BUILD_OPTION_BOB:
        src_file = ""
        model_type = ""
        if asset_data.model:
            for _model in asset_data.model.meshes:
                src_file = os.path.join(_model.directory, _model.filename)
                model_type = _model.model_type
                break

        if not src_file:
            op = layout_row.operator(
                f"{PREFIX_OP}.poliigon_model",
                text="Not supported",
                icon="ERROR",
            ).tooltip = "This model type is not currently supported"
            return

        ext = os.path.splitext(src_file)[-1][1:]
        label = _t("Import {0}").format(ext.upper())
        op = layout_row.operator(
            f"{PREFIX_OP}.model_invoker",
            text=label,
            icon=icon,
        )
        op.asset_id = asset_id
        op.tooltip = tip
        op.filepath = src_file
        op.model_type = int(model_type)
        return

    op = layout_row.operator(
        f"{PREFIX_OP}.poliigon_model",
        text=label,
        icon=icon,
    )
    op.asset_id = asset_id
    op.tooltip = tip
    try:
        op.lod = lod if len(lod) > 0 else "NONE"
    except TypeError:
        # TODO(Andreas): Exception handling can likely be removed again.
        #                Was needed to find another issue...
        msg = (f"{asset_name}: {lod} not found\n"
               f"{asset_data.get_type_data().get_lod_list()}\n")
        cTB.logger_ui.exception(msg)
        op.lod = "NONE"
    safe_size_apply(cTB, op, size, asset_name)


def _draw_button_texture_local(cTB,
                               layout_row: bpy.types.UILayout,
                               asset_data: AssetData,
                               error: DisplayError,
                               sizes_in_scene,
                               size_default: str,
                               is_selection: bool
                               ) -> None:
    asset_id = asset_data.asset_id
    asset_name = asset_data.asset_name

    row_button = layout_row.row(align=True)

    if not asset_data.runtime.get_is_polydex_image():
        label = _t("Import {0}").format(size_default)
    else:
        label = _t("Import Material")

    icon = "TRACKING_REFINE_BACKWARDS"
    tooltip = _t("{0}\n(Import Material)").format(asset_name)

    if len(sizes_in_scene):
        row_button.enabled = is_selection
        label = _t("Apply {0}").format(size_default)
        icon = "TRACKING_REFINE_BACKWARDS"
        tooltip = _t("{0}\n(Apply Material)").format(asset_name)
    elif is_selection:
        label = _t("Apply {0}").format(size_default)
        icon = "TRACKING_REFINE_BACKWARDS"
        tooltip = _t("{0}\n(Import + Apply Material)").format(asset_name)

    if asset_data.runtime.get_is_polydex_image():
        if asset_data.runtime.get_is_polydex_stack():
            label_img = _t("Import Images")
        else:
            label_img = _t("Import Image")

        op = row_button.operator(
            f"{PREFIX_OP}.poliigon_image",
            text=label_img,
            icon="TRACKING_REFINE_BACKWARDS",
        )
        op.asset_id = asset_id
        op.do_as_planes = True
        return
    elif error:
        op = row_button.operator(
            f"{PREFIX_OP}.poliigon_material",
            text=error.button_label,
            icon="ERROR",
        )
        op.tooltip = error.description
    else:
        op = row_button.operator(
            f"{PREFIX_OP}.poliigon_material",
            text=label,
            icon=icon,
        )
        op.tooltip = tooltip

    op.asset_id = asset_id
    safe_size_apply(cTB, op, size_default, asset_name)
    op.mapping = "UV"
    op.scale = 1.0
    op.use_16bit = cTB.settings["use_16"]
    op.reuse_material = True
    set_op_mat_disp_strength(op, asset_name, op.mode_disp)


def _draw_button_model_imported(layout_row: bpy.types.UILayout,
                                asset_data: AssetData
                                ) -> None:
    asset_name = asset_data.asset_name

    op = layout_row.operator(
        f"{PREFIX_OP}.poliigon_select",
        text=_t("Select"),
        icon="RESTRICT_SELECT_OFF",
    )
    op.mode = "model"
    op.data = asset_name
    op.tooltip = _t("{0}\n(Select all instances)").format(asset_name)


def _draw_button_texture_imported(layout_row: bpy.types.UILayout,
                                  asset_data: AssetData
                                  ) -> None:
    asset_id = asset_data.asset_id
    asset_name = asset_data.asset_name

    op = layout_row.operator(
        f"{PREFIX_OP}.poliigon_apply",
        text=_t("Apply"),
        icon="TRACKING_REFINE_BACKWARDS",
    )
    op.asset_id = asset_id
    mat = _get_imported_material(asset_id)
    if mat is not None:
        op.name_material = mat.name
    else:
        op.name_material = "Deleted Material"  # Should not appear in UI!
    op.tooltip = _t("{0}\n(Apply to selected models)").format(asset_name)


def determine_hdri_sizes(asset_data: AssetData,
                         size_light_default: str,
                         size_bg_default: str,
                         use_jpg_bg: bool,
                         addon_convention: int
                         ) -> Tuple[str, str]:
    # TODO(Andreas): Will probably want this in operators fill_size_drop_down
    #                as well.
    #                Refactor following code into function.
    #                Maybe have this in AssetData

    asset_type_data = asset_data.get_type_data()

    sizes_local = asset_type_data.get_size_list(
        local_only=True,
        addon_convention=addon_convention,
        local_convention=asset_data.local_convention)

    sizes_jpg = []
    sizes_exr = []
    for _size in sizes_local:
        tex_maps_jpg = asset_type_data.get_maps(
            size=_size, suffix_list=[".jpg"])
        if len(tex_maps_jpg) > 0:
            sizes_jpg.append(_size)
        tex_maps_exr = asset_type_data.get_maps(
            size=_size, suffix_list=[".exr"])
        if len(tex_maps_exr) > 0:
            sizes_exr.append(_size)

    if len(sizes_exr) > 0:
        size_light = find_closest_size(size_light_default, sizes_exr)
    elif len(sizes_jpg) > 0:
        size_light = find_closest_size(size_light_default, sizes_jpg)
    else:
        # Just get any best fit
        size_light = asset_type_data.get_size(
            size=size_light_default,
            local_only=True,
            addon_convention=addon_convention,
            local_convention=asset_data.get_convention(local=True))

    size_bg = size_bg_default
    if not use_jpg_bg:
        size_bg = f"{size_light}_EXR"
    elif len(sizes_jpg) > 0:
        size_bg = find_closest_size(size_bg_default, sizes_jpg)
        size_bg = f"{size_bg}_JPG"
    elif len(sizes_exr) > 0:
        size_bg = find_closest_size(size_bg_default, sizes_exr)
        size_bg = f"{size_bg}_EXR"
    # TODO(Andreas): fallback
    # else:
    #     tex_maps = asset_type_data.get_maps(size=size_light)
    #     # determine suffix to be used...
    return size_light, size_bg


def _draw_button_hdri_local(cTB,
                            layout_row: bpy.types.UILayout,
                            asset_data: AssetData,
                            error: DisplayError,
                            size_default: str
                            ) -> None:
    asset_id = asset_data.asset_id
    asset_name = asset_data.asset_name

    if error:
        op = layout_row.operator(
            f"{PREFIX_OP}.poliigon_hdri",
            text=error.button_label,
            icon="ERROR",
        )
        op.tooltip = error.description
    else:
        op = layout_row.operator(
            f"{PREFIX_OP}.poliigon_hdri",
            text=_t("Import {0}").format(size_default),
            icon="TRACKING_REFINE_BACKWARDS",
        )
        op.tooltip = _t("{0}\n(Import HDRI)").format(asset_name)
    op.asset_id = asset_id

    size_light, size_bg = determine_hdri_sizes(
        asset_data,
        size_light_default=size_default,
        size_bg_default=cTB.settings["hdrib"],
        use_jpg_bg=cTB.settings["hdri_use_jpg_bg"],
        addon_convention=cTB.addon_convention)
    safe_size_apply(cTB, op, size_light, asset_name)
    if BUILD_OPTION_P4B:
        op.size_bg = size_bg


def _draw_button_hdri_imported(cTB,
                               layout_row: bpy.types.UILayout,
                               asset_data: AssetData
                               ) -> None:
    asset_id = asset_data.asset_id
    asset_name = asset_data.asset_name

    op = layout_row.operator(
        f"{PREFIX_OP}.poliigon_hdri",
        text=_t("Apply"),
        icon="TRACKING_REFINE_BACKWARDS",
    )
    op.asset_id = asset_id
    # NOTE: Size values will not be used, due to do_apply being set.
    #       Nevertheless the values need to exist in the size enums.
    hdri_size = cTB.settings["hdri"]
    safe_size_apply(cTB, op, hdri_size, asset_name)
    try:
        op.size_bg = f"{hdri_size}_EXR"
    except TypeError:
        msg = f"Failed to assign bg {hdri_size} for asset {asset_name})"
        cTB.logger_ui.exception(msg)
    op.do_apply = True
    op.tooltip = _t("{0}\n(Apply to Scene)").format(asset_name)


def _draw_button_download(cTB,
                          layout_row: bpy.types.UILayout,
                          asset_data: AssetData,
                          error: DisplayError,
                          size_default: str
                          ) -> None:
    if BUILD_OPTION_BOB:
        # TODO(Andreas): Band aid, only.
        #                Need a real unsupported type, but as there should
        #                only be Textures coming from BarnOwl, maybe we will
        #                not need anything here. As supported assets should
        #                always be local.
        _draw_button_bob_empty_asset(layout_row)
        return

    asset_id = asset_data.asset_id
    asset_name = asset_data.asset_name

    if error:
        op = layout_row.operator(
            f"{PREFIX_OP}.poliigon_download",
            text=error.button_label,
            icon="ERROR",
        )
        op.tooltip = error.description
    else:
        op = layout_row.operator(
            f"{PREFIX_OP}.poliigon_download",
            text=_t("Download {0}").format(size_default),
        )
        op.tooltip = _t("{0}\nDownload Default").format(asset_name)
        layout_row.enabled = not asset_data.state.dl.is_cancelled()

    op.mode = "download"
    op.asset_id = asset_id
    safe_size_apply(cTB, op, size_default, asset_name)


def _draw_button_purchase(cTB,
                          layout_row: bpy.types.UILayout,
                          asset_data: AssetData,
                          error: DisplayError,
                          size_default: str
                          ) -> None:
    asset_id = asset_data.asset_id
    asset_name = asset_data.asset_name
    num_credits = asset_data.credits
    is_free = num_credits == 0

    thumb_size = THUMB_SIZE_FACTOR[cTB.settings["thumbsize"]]

    if error:
        label = error.button_label
    elif is_free or cTB.is_unlimited_user():
        # While it will still be a purchase button,
        # for free assets it will lead to an implicit auto-download
        label = _t("Download {0}").format(size_default)
    elif thumb_size >= 0.75:
        label = _t("Purchase")
    else:
        label = _t("Buy")
    name_op = f"{PREFIX_OP}.poliigon_download"
    mode_purchase = "purchase"
    tooltip = _t("Purchase {0}").format(asset_name)
    if not is_free:
        if cTB.is_free_user():
            name_op = f"{PREFIX_OP}.poliigon_setting"
            mode_purchase = "my_account"
            label = _t("Learn More")
            tooltip = _t("Switch to your account overview.")
        elif cTB.is_unlimited_user():
            mode_purchase = "download"
            tooltip = _t("Download {0}").format(asset_name)
        elif not cTB.settings["one_click_purchase"]:
            name_op = f"{PREFIX_OP}.popup_purchase"
    else:
        tooltip = _t("Download {0}").format(asset_name)

    icon = "ERROR" if error else "NONE"

    if error and error.goto_account is True:
        op = layout_row.operator(
            f"{PREFIX_OP}.poliigon_setting",
            text=label,
            icon=icon
        )
        op.mode = "my_account"
        op.tooltip = error.description
    else:
        op = layout_row.operator(
            name_op, text=label,
            icon=icon
        )
        op.mode = mode_purchase
        if mode_purchase == "purchase" or mode_purchase == "download":
            op.asset_id = asset_id
            safe_size_apply(cTB, op, size_default, asset_name)
        if error:
            op.tooltip = error.description
        else:
            op.tooltip = tooltip


def _draw_button_quick_menu(layout_row: bpy.types.UILayout,
                            asset_data: AssetData,
                            hide_detail_view: bool = False
                            ) -> None:
    asset_id = asset_data.asset_id
    asset_name = asset_data.asset_name
    is_downloaded = asset_data.is_local

    quick_subtitle = _t("(options)") if is_downloaded else _t("See More")

    op = layout_row.operator(
        f"{PREFIX_OP}.show_quick_menu",
        text="",
        icon="TRIA_DOWN",
    )
    op.asset_id = asset_id
    op.hide_detail_view = hide_detail_view
    op.tooltip = f"{asset_name}\n{quick_subtitle}"


def _draw_missing_grid_dummies(cTB,
                               layout_grid: bpy.types.UILayout,
                               sorted_assets: List[Dict],
                               num_columns: int,
                               thumb_width: float
                               ) -> None:
    # Fill rest of grid with empty cells, if needed
    if len(sorted_assets) >= cTB.settings["page"]:
        return
    if num_columns == len(sorted_assets):
        num_cols_normal = ceil(cTB.width_draw_ui / thumb_width)
        num_cols_normal = max(1, num_cols_normal)
        num_empty_rows = (cTB.settings["page"] // num_cols_normal) - 1
        for _ in range(num_empty_rows):
            layout_grid.column(align=1)
    else:
        for _ in range(len(sorted_assets), cTB.settings["page"]):
            layout_grid.column(align=1)


def _draw_view_more_my_assets(
        cTB, layout_box_not_found: bpy.types.UILayout) -> None:
    if layout_box_not_found is None:
        return
    if BUILD_OPTION_BOB:
        return

    row = layout_box_not_found.row(align=True)
    row.scale_y = 1.5

    label = _t("View more online")
    use_padding = 500

    if cTB.width_draw_ui >= use_padding * get_ui_scale(cTB):
        row.label(text="")

    op = row.operator(
        f"{PREFIX_OP}.poliigon_setting",
        text=label,
        icon_value=cTB.ui_icons[f"{PREFIX_ICON}ICON_poliigon"].icon_id
    )
    op.mode = "view_more"

    if cTB.width_draw_ui >= use_padding * get_ui_scale(cTB):
        row.label(text="")


def _draw_view_more_imported(cTB, sorted_assets: List[Dict]) -> None:
    if len(sorted_assets) != 0:
        return

    cTB.vBase.separator()
    cTB.vBase.separator()

    asset_ids_my_assets = cTB._asset_index.query(
        "my_assets/All Assets",
        chunk=IDX_PAGE_ACCUMULATED,
        chunk_size=PAGE_SIZE_ACCUMULATED)
    if asset_ids_my_assets is not None and len(asset_ids_my_assets) > 0:
        row = cTB.vBase.row(align=True)
        op = row.operator(
            f"{PREFIX_OP}.poliigon_setting",
            text=_t("Explore Your Assets"),
            icon_value=cTB.ui_icons[f"{PREFIX_ICON}ICON_myassets"].icon_id,
        )
        op.mode = "area_my_assets"
        op.tooltip = _t("Show My Assets")
    else:
        row = cTB.vBase.row(align=True)
        op = row.operator(
            f"{PREFIX_OP}.poliigon_setting",
            text=_t("Explore Poliigon Assets"),
            icon_value=cTB.ui_icons[f"{PREFIX_ICON}ICON_poliigon"].icon_id,
        )
        op.mode = "area_poliigon"
        op.tooltip = _t("Show Poliigon Assets")


def _draw_button_unsupported_convention(row: bpy.types.UILayout) -> None:
    _ = row.operator(
        f"{PREFIX_OP}.unsupported_convention",
        text=_t("Update Needed"),
        icon="ERROR",
    )


def _draw_button_bob_empty_asset(row: bpy.types.UILayout) -> None:
    #print("No data message for BOB")
    ops = row.operator(
        f"{PREFIX_OP}.unsupported_convention",
        text=_t("No Data"),
        icon="ERROR",
    )
    ops.tooltip = "Asset type not yet supported"
    ops.suggest_update = False


def _draw_page_buttons(
        cTB, area: str, idx_page_current: int, at_top: bool = False) -> None:
    num_pages = cTB.vPages[area]

    if num_pages <= 1:
        return

    if not at_top:
        cTB.vBase.separator()

    row = cTB.vBase.row(align=False)

    idx_page_start = 0
    idx_page_end = num_pages

    num_pages_max = int((cTB.width_draw_ui / (30 * get_ui_scale(cTB))) - 5)
    if num_pages > num_pages_max:
        idx_page_start = idx_page_current - int(num_pages_max / 2)
        idx_page_end = idx_page_current + int(num_pages_max / 2)
        if idx_page_start < 0:
            idx_page_start = 0
            idx_page_end = num_pages_max
        elif idx_page_end >= num_pages:
            idx_page_start = num_pages - num_pages_max
            idx_page_end = num_pages

    row_left = row.row(align=True)
    row_left.enabled = idx_page_current != 0

    op = row_left.operator(
        f"{PREFIX_OP}.poliigon_setting", text="", icon="TRIA_LEFT"
    )
    op.mode = "page_-"
    op.tooltip = _t("Go to Previous Page")

    row_middle = row.row(align=True)

    op = row_middle.operator(
        f"{PREFIX_OP}.poliigon_setting", text="1", depress=(idx_page_current == 0)
    )
    op.mode = "page_0"
    op.tooltip = _t("Go to Page 1")

    if idx_page_start > 1:
        row_middle.label(
            text="",
            icon_value=cTB.ui_icons[f"{PREFIX_ICON}ICON_dots"].icon_id,
        )

    for idx_page in range(idx_page_start, idx_page_end):
        if idx_page in [0, num_pages - 1]:
            continue

        op = row_middle.operator(
            f"{PREFIX_OP}.poliigon_setting",
            text=str(idx_page + 1),
            depress=(idx_page == idx_page_current),
        )
        op.mode = "page_" + str(idx_page)
        op.tooltip = _t("Go to Page {0}").format(str(idx_page + 1))

        # Buttons get drawn twice, we want to prefetch thumbs only once
        if not at_top:
            continue

        # Make sure we have data for this page
        # TODO(Andreas): If we have no data here, we have messed up elsewhere.
        #                Yet, thumb prefetching not working as expected.
        #                So, we'll see, if doing another server request might
        #                help us here.
        # cTB.f_GetAssets(area=area, page=idx_page)

        #  NOT A GOOD IDEA: Chokes Blender almost completely
        #  # Schedule thumb prefretching
        #  asset_ids_prefetch, _ = cTB.f_GetPageAssets(idx_page)
        #  asset_data_prefetch = cTB._asset_index.get_asset_data_list(
        #      asset_ids_prefetch)
        #  for _asset_data in asset_data_prefetch:
        #      path_thumb, url_thumb = cTB._asset_index.get_cf_thumbnail_info(
        #          _asset_data.asset_id)
        #      cTB.f_QueuePreview(
        #          _asset_data, path_thumb, url_thumb, thumbnail_index=0)

    if idx_page_end < num_pages - 1:
        row_middle.label(text="", icon_value=cTB.ui_icons[f"{PREFIX_ICON}ICON_dots"].icon_id)

    col = row_middle.column(align=True)

    categories = cTB.settings["category"][area]
    search = cTB.vSearch[area]
    key_fetch = (tuple(categories), search)
    enabled = key_fetch not in cTB.fetching_asset_data[area]

    col.enabled = enabled
    if enabled:
        text = str(num_pages)
    else:
        text = "..."
    op = col.operator(
        f"{PREFIX_OP}.poliigon_setting",
        text=text,
        depress=(idx_page_current == (num_pages - 1)),
    )
    op.mode = "page_" + str(num_pages - 1)
    op.tooltip = _t("Go to Page {0}").format(str(num_pages))

    row_right = row.row(align=True)
    row_right.enabled = idx_page_current != (num_pages - 1)

    op = row_right.operator(
        f"{PREFIX_OP}.poliigon_setting", text="", icon="TRIA_RIGHT"
    )
    op.mode = "page_+"
    op.tooltip = _t("Go to Next Page")

    if at_top:
        cTB.vBase.separator()


def _build_unlimited_banner(cTB, layout: bpy.types.UILayout) -> None:
    if not cTB.is_unlimited_user():
        return
    area = cTB.settings["area"]
    if area != KEY_TAB_MY_ASSETS:
        return

    col_grid = layout.column()

    box_unlimited = col_grid.box()
    box_unlimited.alignment = "CENTER"

    col_unlimited = box_unlimited.column()
    col_unlimited.alignment = "CENTER"

    text_info = _t("Unlimited Downloads - "
                   "Assets downloaded on an unlimited plan won’t show up in "
                   "My Assets.")
    # 20 seems a good value, determined by trial and error
    w_info = cTB.width_draw_ui - 20 * get_ui_scale(cTB)
    wrapped_label(cTB, w_info, text_info, col_unlimited, add_padding=False)

    col_link = col_unlimited.column()
    col_link.alignment = "LEFT"
    icon_value = cTB.ui_icons[f"{PREFIX_ICON}LOGO_unlimited"].icon_id
    op_link = col_link.operator(
        f"{PREFIX_OP}.poliigon_link", text=_t("Learn More"), emboss=True, icon_value=icon_value)
    op_link.tooltip = _t("Learn more online about unlimited plans")
    op_link.mode = "unlimited"


def _build_tab_title(cTB) -> None:
    row = cTB.vBase.row()

    area = cTB.settings["area"]

    categories = cTB.vActiveCat
    search = cTB.vSearch[area]
    has_search = len(search) > 0
    is_category_all = categories == [CATEGORY_ALL]

    is_all = is_category_all and not has_search
    path_entry = None
    if is_all and area != KEY_TAB_IMPORTED:
        num_assets = cTB.num_assets[area]
    else:
        num_assets = cTB.num_assets_current_query
    # BOB gets its num_assets a bit further down

    # We do not want the "All" removed, if search comes from our
    # virtual "free category" (which only exists on Online tab), alone.
    # TODO(Andreas): This will change again, once we do the "virtual free"
    #                category via API RC.
    if area == KEY_TAB_ONLINE:
        if has_search and cTB.vSearch[area] != "free ":
            prefix_top_level = ""
        else:
            # Leads to deliberately replacing "All " with "All " (-> no change)
            prefix_top_level = "All "
    elif has_search:
        prefix_top_level = ""
    elif area == KEY_TAB_MY_ASSETS:
        prefix_top_level = "My "
    elif area == KEY_TAB_IMPORTED:
        prefix_top_level = "Imported "

    if cTB.settings["show_settings"]:
        area_title = _t("Settings")
    elif cTB.settings["show_user"]:
        area_title = _t("My Account")
    elif len(categories) == 1:
        category = categories[0]
        if BUILD_OPTION_BOB:
            if category != CATEGORY_ALL:
                path_entry = cTB.bo_listener.bo_libraries.get_path_entry_by_key(
                    category)
                category = path_entry.name
        elif category in ["HDRIs", "Models", "Textures"]:
            category = f"{prefix_top_level}{category}"
        elif category == "All Assets" and area == KEY_TAB_ONLINE:
            if "free" in cTB.vSearch[area]:
                category = "All Free Assets"
        category = category.replace("All ", prefix_top_level)

        area_title = category
    elif BUILD_OPTION_BOB:
        category_last = categories[-1]
        if category_last != CATEGORY_ALL:
            path_entry = cTB.bo_listener.bo_libraries.get_path_entry_by_key(
                category_last)
            area_title = path_entry.name
    else:
        area_title = categories[-1].title()

    if area_title == KEY_TAB_ONLINE:
        area_title = _t("Online")

    if BUILD_OPTION_BOB:
        num_per_page = cTB.settings["page"]
        idx_page = cTB.vPage[area]
        key = path_entry.asset_index_key if path_entry is not None else CATEGORY_ALL
        query_tuple = (
            KEY_TAB_MY_ASSETS,
            None,
            key,
            search if search != "" else None,
            idx_page,
            num_per_page)

        if query_tuple in cTB.bo_asset_counts:
            num_assets = cTB.bo_asset_counts[query_tuple]
        else:
            num_assets = 0

    area_title = f"{area_title} ({num_assets})"

    row.label(text=area_title)

    row_right = row.row()
    row_right.alignment = "RIGHT"

    row_right.separator()

    col = row_right.column()
    is_fetching_my_assets = len(cTB.fetching_asset_data[KEY_TAB_MY_ASSETS]) > 0
    is_fetching_online = len(cTB.fetching_asset_data[KEY_TAB_ONLINE]) > 0
    is_fetching = is_fetching_my_assets or is_fetching_online
    op = col.operator(
        f"{PREFIX_OP}.refresh_data",
        text="",
        icon="FILE_REFRESH"
    )
    if is_fetching:
        op.tooltip = _t("Fetching of asset data in progress")
    col.enabled = not is_fetching


def _asset_is_local(cTB, asset_data: AssetData) -> bool:
    """Checks if asset is local, taking renderer into account for Models."""

    asset_id = asset_data.asset_id
    if asset_data.asset_type != AssetType.MODEL:
        return cTB._asset_index.check_asset_is_local(asset_id)

    desired_model_type = ModelType.BLEND
    prefer_blend = cTB.settings["download_prefer_blend"]
    if prefer_blend:
        desired_model_type = ModelType.BLEND
        native_only = True
    else:
        desired_model_type = ModelType.FBX
        native_only = False

    is_local = cTB._asset_index.check_asset_is_local(
        asset_id,
        model_type=desired_model_type,
        native_only=native_only,
        renderer=None  # None is for legacy cycles models w/o engine name
    )
    return is_local


def _draw_bob_stack_icon(cTB, row: bpy.types.UILayout, asset_data: AssetData):
    if not BUILD_OPTION_BOB:
        return
    if not asset_data.runtime.get_is_polydex_stack():
        return
    col_button = row.column()
    col_button.enabled = False
    op = col_button.operator(
        f"{PREFIX_OP}.poliigon_setting",
        text="",
        icon_value=cTB.ui_icons[f"{PREFIX_ICON}ICON_stack"].icon_id
    )
    op.mode = "none"
    op.tooltip = _t("Asset consists of multiple image files")


# @timer
def build_assets(cTB):
    cTB.logger_ui.debug("build_assets")

    check_dpi(cTB, force=False)

    area = cTB.settings["area"]
    idx_page_current = cTB.vPage[area]

    sorted_assets = cTB.f_GetAssetsSorted(idx_page_current)
    cTB.logger_ui.debug(f"build_assets: sorted_assets {len(sorted_assets)}")

    _draw_page_buttons(cTB, area, idx_page_current, at_top=True)

    if cTB.is_unlimited_user():
        row = cTB.vBase.row(align=False)
        _build_unlimited_banner(cTB, row)

    _build_tab_title(cTB)

    thumb_size_factor = THUMB_SIZE_FACTOR[cTB.settings["thumbsize"]]

    category = cTB.vActiveCat[0].replace("All ", "")
    if len(cTB.vActiveCat) > 1:
        category = f"{cTB.vActiveCat[-1]} {category}"

    box_not_found = None
    if len(sorted_assets) == 0:
        box_not_found = _build_assets_no_assets(cTB, area, category)
    else:
        grid, thumb_width, num_columns = _build_assets_prepare_grid(
            cTB, thumb_size_factor, sorted_assets)

        is_selection = len(bpy.context.selected_objects) > 0

        # Build Asset Grid ...
        for _asset_id in sorted_assets:
            if _asset_id != 0:
                asset_data = cTB._asset_index.get_asset(_asset_id)
            else:
                asset_data = AssetData(
                    0, AssetType.TEXTURE, "dummy", api_convention=0)
            if asset_data is None:
                continue
            asset_type_data = asset_data.get_type_data()
            asset_name = asset_data.asset_name
            asset_name_display = asset_data.display_name
            asset_type = asset_data.asset_type
            api_convention = asset_data.get_convention()

            # See if there's any errors associated with this asset,
            # such as after or during download failure.
            # TODO(Andreas): ui errors will be replaced by AssetData states
            errs = [
                err
                for err in cTB.ui_errors
                if _asset_id and err.asset_id == _asset_id
            ]
            error = errs[0] if errs else None
            del errs

            cTB.f_GetPreview(asset_data)

            # How is this ever not downlaoded if polydex?
            if BUILD_OPTION_P4B:
                is_downloaded = _asset_is_local(cTB, asset_data)
            else:
                is_downloaded = True

            size_pref = cTB.get_pref_size(asset_type)
            if asset_type_data is not None:  # may happen for dummies
                try:
                    size_default = asset_type_data.get_size(
                        size_pref,
                        local_only=is_downloaded,
                        addon_convention=cTB._asset_index.addon_convention,
                        local_convention=asset_data.local_convention)
                except KeyError:
                    # AssetData's size list seems to be empty
                    # This should actually never be the case.
                    # Use an arbitrary default, instead.

                    # TODO(Andreas): reporting
                    size_default = "2K"
            else:
                size_default = "DUMMY SIZE"

            sizes_in_scene, size_default = _determine_in_scene_sizes(
                cTB, asset_data, size_default)
            if cTB.settings["download_prefer_blend"]:
                model_type = ModelType.BLEND
            else:
                model_type = ModelType.FBX
            native_only = model_type == ModelType.BLEND

            if BUILD_OPTION_BOB:
                # Always local in this case
                is_local = True
                is_downloaded = True
            else:
                is_local = cTB._asset_index.check_asset_is_local(
                    _asset_id,
                    model_type=model_type,
                    native_only=native_only,
                    renderer=None
                )

            size_default = asset_data.get_current_size(
                size_default,
                local_only=is_local,
                addon_convention=cTB.addon_convention)
            # TODO: Bob override

            if BUILD_OPTION_P4B:
                if asset_type == AssetType.TEXTURE and api_convention >= 1:
                    map_prefs = cTB.user.map_preferences
                    is_downloaded = asset_type_data.all_expected_maps_local(
                        map_prefs, size=size_default)

            cell = grid.column(align=True)
            box_thumb = cell.box().column()

            if BUILD_OPTION_P4B or "dummy" in asset_name.lower():
                header_icon = "NONE"
            elif asset_type == AssetType.TEXTURE:
                header_icon = "MATERIAL"
            elif asset_type == AssetType.MODEL:
                header_icon = "OBJECT_DATA"
            elif asset_type == AssetType.HDRI:
                header_icon = "WORLD"
            elif asset_type == AssetType.IMAGE:
                header_icon = "IMAGE_DATA"
            else:
                header_icon = "NONE"

            name_row = box_thumb.row(align=True)
            ui_label = "" if "dummy" in asset_name.lower() else asset_name_display
            
            name_row.label(text=ui_label, icon=header_icon)
            name_row.scale_y = 0.8
            name_row.alignment = "CENTER"
            name_row.enabled = False  # To fade label for less contrast.

            _draw_thumbnail(cTB, asset_data, thumb_size_factor, box_thumb)

            row = cell.row(align=True)

            if asset_name == "dummy":
                _draw_thumb_state_asset_dummy(row)
            elif asset_data.state.purchase.is_in_progress():
                _draw_thumb_state_asset_purchasing(row, asset_data)
            elif asset_data.state.dl.is_cancelled():
                _draw_thumb_state_cancelling_download(row, asset_data)
            elif asset_data.state.dl.is_in_progress():
                _draw_thumb_state_asset_downloading(
                    row, asset_data, thumb_width)
            elif area in [KEY_TAB_ONLINE, KEY_TAB_MY_ASSETS]:
                is_tex = asset_type == AssetType.TEXTURE
                is_purchased = asset_data.is_purchased
                is_local = asset_data.is_local
                if cTB.is_unlimited_user() and is_local:
                    _draw_checkmark_unlimited(cTB, row)
                elif cTB.is_unlimited_user():
                    # No need for green checkmark or wm preview if unlimited
                    pass
                elif is_tex and not is_purchased:
                    _draw_button_quick_preview(
                        cTB, row, asset_data, is_selection)
                elif is_purchased and area == KEY_TAB_ONLINE:
                    _draw_checkmark_purchased(cTB, row)

                _draw_bob_stack_icon(cTB, row, asset_data)

                if is_purchased or cTB.is_unlimited_user():
                    if is_downloaded:
                        if asset_type == AssetType.MODEL:
                            _draw_button_model_local(
                                cTB, row, asset_data, error)
                        elif asset_type == AssetType.TEXTURE:
                            _draw_button_texture_local(
                                cTB,
                                row,
                                asset_data,
                                error,
                                sizes_in_scene,
                                size_default,
                                is_selection)
                        elif asset_type == AssetType.HDRI:
                            _draw_button_hdri_local(
                                cTB, row, asset_data, error, size_default)
                    else:
                        if not check_convention(asset_data):
                            _draw_button_unsupported_convention(row)
                        else:
                            _draw_button_download(
                                cTB, row, asset_data, error, size_default)
                else:
                    if not check_convention(asset_data):
                        _draw_button_unsupported_convention(row)
                    else:
                        _draw_button_purchase(
                            cTB, row, asset_data, error, size_default)

                if BUILD_OPTION_P4B:
                    if is_downloaded or check_convention(asset_data):
                        _draw_button_quick_menu(row, asset_data)
                elif BUILD_OPTION_BOB:
                    if is_downloaded:
                        _draw_button_quick_menu(row, asset_data)

            elif area == KEY_TAB_IMPORTED:
                if asset_name == "dummy":
                    _draw_thumb_state_asset_dummy(row)
                elif asset_type == AssetType.MODEL:
                    _draw_button_model_local(
                        cTB, row, asset_data, error)
                elif asset_type == AssetType.TEXTURE:
                    _draw_button_texture_local(
                        cTB,
                        row,
                        asset_data,
                        error,
                        sizes_in_scene,
                        size_default,
                        is_selection)
                elif asset_type == AssetType.HDRI:
                    _draw_button_hdri_local(
                        cTB, row, asset_data, error, size_default)

                _draw_button_quick_menu(row, asset_data)

            cell.separator()

        _draw_missing_grid_dummies(
            cTB, grid, sorted_assets, num_columns, thumb_width)

        _draw_page_buttons(cTB, area, idx_page_current)

    if area == KEY_TAB_MY_ASSETS:
        _draw_view_more_my_assets(cTB, box_not_found)
    elif area == KEY_TAB_IMPORTED:
        _draw_view_more_imported(cTB, sorted_assets)
