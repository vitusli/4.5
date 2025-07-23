import os
import platform
import re
import threading
from datetime import datetime, timezone
from math import ceil
from typing import Dict, List

import bpy
from bpy.types import Panel
from t3dn_bip import previews

from ..utils import icon_value, icons, package, preferences, version, version_str
from ..utils.local import Asset
from ..utils.auth import (
    PATH_PRODUCTS_FILE,
    PATH_THUMBS,
    get_auth_token,
    get_message,
    get_subs_info,
    get_token_expiry,
)
from ..utils.local import _cache_assets, _variant_map, _active_number, get_local_assets, get_all_local_assets
from ..utils.product import (
    download_thumbnail,
    get_asset_path,
    get_favourites,
    get_products,
)


def get_ui_scale():
    return bpy.context.preferences.system.ui_scale


def _get_draw_width(context) -> float:
    ui_scale = get_ui_scale()
    padding = 30 * ui_scale  # Combined padding (15 for panel + 15 for sidebar)

    # Extra padding for Mac on Blender 3.0+
    if ("mac" in platform.platform() or "darwin" in platform.platform()) and bpy.app.version >= (3, 0, 0):
        padding += 17 * ui_scale

    width = max(1, context.region.width - padding)
    return width


def _grid(context, layout: bpy.types.UILayout, size_factor: float, items: List[Dict]) -> bpy.types.UILayout:
    # Calculate thumb width
    thumb_width = ceil(170 * size_factor)
    thumb_width *= get_ui_scale()
    draw_width = _get_draw_width(context)

    # Calculate number of columns
    columns = int(draw_width / thumb_width)
    columns = max(columns, 1)
    columns = min(columns, len(items))

    # Calculate padding
    padding = (draw_width - (columns * thumb_width)) / 2
    if padding < 1.0 and columns > 1:
        columns -= 1
        padding = (draw_width - (columns * thumb_width)) / 2

    # Build grid layout
    split_right = None
    if padding >= 1.0 or thumb_width + 1 <= draw_width:
        # Typical case, fit rows and columns
        factor = padding / draw_width
        split_left = layout.split(factor=factor)
        split_left.separator()

        factor = 1.0 - factor
        split_right = split_left.split(factor=factor)
        container_grid = split_right
    else:
        # Panel is narrower than a single preview width, single col
        container_grid = layout

    grid = container_grid.grid_flow(
        row_major=True,
        columns=columns,
        even_columns=True,
        even_rows=True,
        align=False,
    )

    if split_right is not None:
        split_right.separator()

    return grid


class Imeshh:
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "iMeshh"

    def draw_list(self, layout, listtype_name, dataptr, propname, active_propname, rows=4):
        row = layout.row()
        row.scale_y = 1.2
        row.template_list(
            listtype_name,
            "",
            dataptr=dataptr,
            active_dataptr=dataptr,
            propname=propname,
            active_propname=active_propname,
            rows=rows,
            sort_lock=True,
        )
        col = row.column(align=True)
        col.scale_x = 1.1
        return col

def generate_variant_map(base_name: str, asset_path: str, thumb_path: str):
    if not _variant_map.get(base_name):
        _variant_map[base_name] = []
    else:
        return
    if not _active_number.get(base_name):
        _active_number[base_name] = 0
    
    files = [f for f in os.listdir(asset_path) if f.endswith(".blend")]
    images = [f for f in os.listdir(asset_path) if f.endswith(".png")]

    files.sort()
    images.sort()
    
    # for i, file in enumerate(files):
    #     file_name_without_ex = os.path.splitext(file)[0]
    #     match = re.search(r'^(.*)_var-(.+)$', file_name_without_ex)
    #     variant_type = None
    #     if match:
    #         variant_type = match.group(2)
    #     _variant_map[base_name].append(Asset(file_path=os.path.join(asset_path, file), img_path=os.path.join(asset_path, images[i]), variant_type=variant_type))

    for i, file in enumerate(files):
        file_name_without_ex = os.path.splitext(file)[0]
        match = re.search(r'^(.*)_var-(.+)$', file_name_without_ex)
        variant_type = match.group(2) if match else None

        try:
            image = images[i]
        except IndexError:
            image = None  # Optional fallback; or you can use `continue` to skip
        
        _variant_map[base_name].append(
            Asset(
                file_path=os.path.join(asset_path, file),
                img_path=os.path.join(asset_path, image) if image else thumb_path,
                variant_type=variant_type
            )
        )

    if len(_variant_map[base_name]) == 1:
        _variant_map[base_name][0].img_path = thumb_path
    return


class IMESHH_PT_main(Panel, Imeshh):
    bl_label = "iMeshh"

    message = None
    url = None

    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT"

    def draw_header_preset(self, context):
        from ..utils.product import latest_version

        if latest_version and version != latest_version:
            op = self.layout.operator("screen.userpref_show", text="Update", icon="IMPORT")
            op.section = "EXTENSIONS"

    def draw(self, context):
        layout = self.layout
        layout.use_property_decorate = False

        self.ui_scale = context.preferences.system.ui_scale
        self.width = context.region.width

        self.prefs = preferences()
        self.props = context.scene.imeshh

        self.draw_message(context, layout)

        layout.prop(self.props, "asset_library", expand=True)

        if self.props.asset_library == "IMESHH":
            self.draw_imeshh(context, layout)
        elif self.props.asset_library == "LOCAL":
            self.draw_local(context, layout)

    def draw_message(self, context, layout):
        # layout.prop(self.prefs, "message_cooldown")  # debug

        token = get_auth_token()
        subs = get_subs_info()
        subs_status = subs.get("status") if subs else None
        message = get_message()

        if not message:
            return

        schema_version = message.get("schema_version")

        if schema_version == "1.0.0":
            message_status = message.get("status")

            if message_status == "none":
                return
            elif (message_status == "active" and (not token or subs_status != "active")) or (
                message_status == "inactive" and subs_status == "active"
            ):
                return

        if message and int(datetime.now().timestamp()) > self.prefs.message_cooldown:
            box = layout.box()

            text = message.get("message")
            links = message.get("links", [])

            if text:
                split = box.split(factor=0.9, align=True)

                row = split.row(align=True)
                col = row.column(align=True)
                col.scale_y = 0.8
                for line in text.split("\n"):
                    col.label(text=line)

                row_right = split.row(align=True)
                row_right.alignment = "RIGHT"
                row_right.operator("imeshh.message_close", text="", icon="X", emboss=False)

            if links:
                col = box.column()
                for link in links:
                    col.operator("wm.url_open", text=link.get("text")).url = link.get("url")

    def draw_imeshh(self, context, layout):
        # get_all_local_assets(self, context)
        row = layout.row(align=True)

        row_left = row.row()
        row_left.alignment = "LEFT"
        row_left.prop(self.props, "asset_source", icon_only=True, expand=True)

        row_center = row.row()
        row_center.alignment = "CENTER"
        row_center.prop(
            self.props, "asset_type", icon_only=False if self.width > (480 * self.ui_scale) else True, expand=True
        )

        row_right = row.row(align=True)
        # row_right.alignment = "RIGHT"
        row_right.operator("imeshh.reload", text="", icon="FILE_REFRESH")
        row_right.operator("preferences.addon_show", icon="PREFERENCES").module = package

        row = layout.row()
        col = row.column()
        col.prop(self.props, "category", text="")
        subcol = col.column()
        subcol.enabled = self.props.category not in {"ALL", "FREE"}
        subcol.prop(self.props, "subcategory", text="")

        row = layout.row(align=True)
        if bpy.app.version >= (4, 2, 0):
            row.prop(self.props, "search", icon="VIEWZOOM", text="", placeholder="Search for assets")
        else:
            row.prop(self.props, "search", icon="VIEWZOOM", text="")
        if self.props.search:
            row.operator("imeshh.search_clear", icon="X", text="")
        row.prop(self.props, "use_filter_search", icon="FILTER", text="", icon_only=True)
        row.prop(self.props, "filter_search_type", text="", icon_only=True)

        if not os.path.exists(PATH_PRODUCTS_FILE):
            layout.separator()

            row = layout.row()
            row.scale_y = 1.4
            row.alignment = "CENTER"

            col = row.column(align=True)
            col.scale_y = 0.6
            col.alignment = "CENTER"
            col.label(text="Fetching...")
            col.separator()
            col.separator()
            col.label(text="This may take several seconds.")
            col.separator()
            col.separator()
            col.label(text="Try reloading the add-on")
            col.label(text="or restart Blender if it gets stuck.")

            return

        self.draw_products(context, layout)

    def draw_products(self, context, layout):
        layout.alignment = "CENTER"

        products = get_products(self.props)
        if products:
            start_idx = (self.props.page - 1) * self.prefs.preview_limit
            end_idx = min(start_idx + self.prefs.preview_limit, len(products))

            self.draw_pagination(context, layout, products)

            grid = _grid(context, layout, 1.0, products[start_idx:end_idx])

            for product in products[start_idx:end_idx]:
                self.draw_product(context, grid, product)

            if len(products) >= 5:
                self.draw_pagination(context, layout, products)
        else:
            layout.separator()
            layout.label(text=f"{self.props.asset_source.title()} {self.props.asset_type.lower()} assets not found.")

    def draw_product(self, context, grid, product):
        if not product:
            return

        cell = grid.column(align=True)
        col = cell.box().column()

        # Get product info
        product_id = product.get("id")
        thumbnail_name = (
            f'{product.get("thumbnail_name", "")}_{product.get("thumbnail_date_modified", "").replace(":", "-")}'
        )
        thumb_path = os.path.join(PATH_THUMBS, f"{thumbnail_name}.png")
        asset_path = get_asset_path(product)
        filepath_parameter = None
        if os.path.exists(thumb_path):
            # Load preview if needed
            if thumb_path not in thumbs:
                preview = thumbs.load_safe(thumb_path, thumb_path, "IMAGE")
                context.area.tag_redraw()
            else:
                preview = thumbs[thumb_path]

            # Draw thumbnail with action buttons
            if os.path.exists(asset_path) is False:
                row = col.row(align=True)
                row.emboss = "NONE"
                row.label(text="")
                row.template_icon(icon_value=preview.icon_id, scale=self.prefs.preview_scale)

            else: 
                
                base_name = os.path.basename(asset_path)
                preview_path = os.path.join(asset_path, base_name + ".png")
                filepath_parameter = os.path.join(asset_path, base_name + ".blend")
                if not os.path.exists(preview_path):
                    if not product.get("asset_type") in "material":
                        generate_variant_map(base_name, asset_path, thumb_path)
                    else:
                        if not os.path.exists(preview_path):
                            preview_path = thumb_path

                if _variant_map.get(base_name):
                    preview_path = _variant_map[base_name][_active_number[base_name]].img_path
                    filepath = _variant_map[base_name][_active_number[base_name]].file_path
                    filepath_parameter = filepath
                
                # Only load preview if not already loaded
                if not thumbs.get(preview_path):
                    preview = thumbs.load_safe(preview_path, preview_path, "IMAGE")
                else:
                    preview = thumbs[preview_path]

                # Bottom row with navigation and thumbnail
                bottom_row = col.row(align=True)
                bottom_row.emboss = "NONE"
                bottom_row.alignment = "CENTER"

                # Only show navigation buttons if there are multiple variants
                if _variant_map.get(base_name) and len(_variant_map[base_name]) > 1 and product.get("asset_type") in 'model':
                    # Previous button
                    prev_col = bottom_row.row(align=True)
                    prev_col.scale_y = 1.0  
                    prev_col.alignment = "CENTER"            
                    prev_op = prev_col.operator("imeshh.navigate_asset", icon="TRIA_LEFT", text="", emboss=False)
                    if prev_op:
                        prev_op.direction = "PREV"
                        prev_op.base_name = base_name
                        prev_op.current_file = filepath # Pass the currently displayed file path

                # Thumbnail
                thumbs_col = bottom_row.row(align=True)
                thumbs_col.template_icon(icon_value=preview.icon_id, scale=self.prefs.preview_scale)
                
                # Only show navigation buttons if there are multiple variants
                if _variant_map.get(base_name) and len(_variant_map[base_name]) > 1 and product.get("asset_type") in 'model':
                    # Next button
                    next_col = bottom_row.row(align=True)
                    next_col.scale_y = 1.0  
                    next_col.alignment = "CENTER"
                    next_op = next_col.operator("imeshh.navigate_asset", icon="TRIA_RIGHT", text="", emboss=False)
                    if next_op:
                        next_op.direction = "NEXT"
                        next_op.base_name = base_name
                        next_op.current_file = filepath # Pass the currently displayed file path

            # Info and favorite buttons
            if os.path.exists(asset_path) is False:
                subcol = row.column()
            else:
                subcol = bottom_row.column()
            info_icon = "INFO_LARGE" if bpy.app.version >= (4, 3, 0) else "INFO"
            heart_icon = "FUND" if product_id in get_favourites() else "HEART"
            subcol.operator("imeshh.detail", icon=info_icon, text="").product_id = product_id
            subcol.operator("imeshh.favourite", icon=heart_icon, text="").product_id = product_id

            label_text = product.get("name")
            if filepath_parameter:
                match = re.search(r'^(.*)_var-(.+)$', os.path.basename(filepath_parameter))
                if match:
                    label_text = product.get("name") + "-" + match.group(2)[:-6]
                    
            # Show asset name if enabled
            if self.prefs.show_asset_name:
                name_row = col.row()
                name_row.label(text=label_text)
                name_row.scale_y = 0.8
                name_row.alignment = "CENTER"
                name_row.enabled = False

            # Action area (download progress or buttons)
            col = cell.column(align=True)
            download_item = next(
                (item for item in context.window_manager.imeshh.download_list if item.product_id == product_id), None
            )

            if download_item and download_item.progress >= 0:
                col.progress(
                    text=f"{download_item.status} {download_item.progress * 100:.1f}%", factor=download_item.progress
                )
            elif os.path.exists(asset_path):
                # Find first blend file
                blend_path = next(
                    (
                        entry.path
                        for entry in os.scandir(asset_path)
                        if entry.is_file() and entry.name.endswith(".blend")
                    ),
                    None,
                )

                if blend_path:
                    # Check if update is available
                    # Convert local timestamp to UTC for proper comparison
                    local_mod_time = datetime.fromtimestamp(os.path.getmtime(blend_path))
                    utc_mod_time = local_mod_time.astimezone(timezone.utc)
                    formatted_date = utc_mod_time.strftime("%Y-%m-%dT%H:%M:%S")

                    if product.get("date_modified") > formatted_date:
                        self.draw_download_operator(col, product, label="Update")
                    elif product.get("asset_type") == "material":
                        self.draw_apply_operator(col, product, asset_path, filepath_parameter)
                    else:
                        self.draw_append_operator(col, product, asset_path, filepath_parameter)
            else:
                self.draw_download_operator(col, product)
        else:
            # Loading state
            self.draw_loading(col)
            if self.props.asset_type == "model" and self.props.page == 1:
                thread_name = f"iMeshh_Downloader_{product_id}"
                if not any(t.name == thread_name for t in threading.enumerate()):
                    threading.Thread(target=download_thumbnail, args=(product,), name=thread_name, daemon=True).start()

        cell.separator()

    def draw_download_operator(self, layout, product, label: str = "Download"):
        row = layout.row(align=True)
        now_ts = int(datetime.now().timestamp())
        token = get_auth_token()
        expiry = get_token_expiry()
        subs = get_subs_info()

        # If not logged in or token expired, show login button
        if not token or not expiry or expiry < now_ts:
            op = layout.operator("preferences.addon_show", icon="USER", text="Login")
            op.module = package

        # If product is free, show free download button
        elif product.get("is_freebie"):
            op = row.operator("imeshh.download", icon="IMPORT", text="Free")
            op.product_id = product.get("id")
            row.operator("imeshh.options", icon="TRIA_DOWN", text="").product_id = product.get("id")

        # If not subscribed, show subscribe button
        elif not subs or subs.get("status") != "active":
            op = layout.operator("wm.url_open", icon_value=icons["IMESHH"], text="Subscribe")
            op.url = "https://shop.imeshh.com/pricing"

        # Otherwise, show download/update button
        else:
            op = row.operator("imeshh.download", icon="IMPORT", text=label)
            op.product_id = product.get("id")
            row.operator("imeshh.options", icon="TRIA_DOWN", text="").product_id = product.get("id")

    def draw_append_operator(self, layout, product, asset_path, filepath_parameter):
        if not asset_path:
            return

        row = layout.row(align=True)

        if product.get("asset_type") in {"model"}:
            # Show both Append and Link buttons side by side
            append_op = row.operator(
                "imeshh.append",
                icon="APPEND_BLEND",
                text="Append",
                depress=True,
            )
            append_op.product_id = product.get("id")
            if filepath_parameter is not None:
                append_op.filepath = filepath_parameter
            append_op.link_mode = False
            
            link_op = row.operator(
                "imeshh.append",
                icon="LINK_BLEND", 
                text="Link",
                depress=True,
            )
            link_op.product_id = product.get("id")
            if filepath_parameter is not None:
                link_op.filepath = filepath_parameter
            link_op.link_mode = True
            
            if filepath_parameter is None:
                row.operator("imeshh.options", icon="TRIA_DOWN", text="", depress=True).product_id = product.get("id")
            else:
                op = row.operator("imeshh.options", icon="TRIA_DOWN", text="", depress=True)
                op.product_id = product.get("id")
                op.filepath = filepath_parameter
        else:
            # For geonodes and fx, show options menu
            op = row.operator(
                "imeshh.options",
                icon="APPEND_BLEND",
                text="Append...",
                depress=True,
            )
            op.product_id = product.get("id")
            op.filepath = filepath_parameter

    def draw_apply_operator(self, layout, product, asset_path, filepath_parameter):
        row = layout.row(align=True)

        files = [f for f in os.listdir(asset_path) if f.endswith(".blend")]
        # Try to find exact match for prefs.apply_size
        target_file = next((f for f in files if self.prefs.apply_size.lower() in f.lower()), None)

        if target_file:
            # Use exact match
            row.operator(
                "imeshh.apply", icon="MATERIAL", text=f"Apply {self.prefs.apply_size}", depress=True
            ).product_id = product.get("id")
        else:
            # Try to find size match
            size_pattern = re.compile(r"(\d+)k", re.IGNORECASE)
            target_size = (
                int(size_pattern.search(self.prefs.apply_size).group(1))
                if size_pattern.search(self.prefs.apply_size)
                else 0
            )

            available_sizes = []
            for f in files:
                match = size_pattern.search(f)
                if match:
                    size = int(match.group(1))
                    available_sizes.append((size, f))

            if available_sizes:
                # Sort by size
                available_sizes.sort()
                # First try to find bigger size
                bigger_match = next(((s, f) for s, f in available_sizes if s >= target_size), None)
                # If no bigger size found, get closest lower size
                if not bigger_match:
                    bigger_match = available_sizes[-1]

                best_size, best_file = bigger_match
                row.operator("imeshh.apply", icon="MATERIAL", text=f"Apply {best_size}K", depress=True).product_id = (
                    product.get("id")
                )
            else:
                # Fallback to first file
                row.operator("imeshh.apply", icon="MATERIAL", depress=True).product_id = product.get("id")

        op = row.operator("imeshh.options", icon="TRIA_DOWN", text="", depress=True)
        if op:
            op.product_id = product.get("id")
            op.filepath = filepath_parameter

    def draw_loading(self, layout):
        layout.enabled = False

        if self.prefs.show_asset_name:
            row = layout.row()
            row.label(text="")
            row.scale_y = 0.4

        layout.template_icon(
            icon_value=icon_value("TEMP") if bpy.app.version >= (4, 2, 0) else icon_value("FILE_REFRESH"),
            scale=self.prefs.preview_scale,
        )

        if self.prefs.show_asset_name:
            row = layout.row()
            row.label(text="")
            row.scale_y = 0.4

        row = layout.row()
        row.label(text="Loading...")
        row.alignment = "CENTER"

    def draw_pagination(self, context, layout, products):
        # Determine max pages based on width
        width_thresholds = [(960, 12), (800, 10), (640, 8), (520, 7), (480, 6), (440, 5), (400, 4), (360, 3), (320, 2)]
        num_pages_max = next((pages for w, pages in width_thresholds if self.width > w), 2)

        total_pages = (len(products) + self.prefs.preview_limit - 1) // self.prefs.preview_limit
        if total_pages <= 1:
            return

        current_page = min(max(1, self.props.page), total_pages)

        # Page numbers
        if total_pages > num_pages_max:
            half = num_pages_max // 2
            start = max(1, current_page - half)
            end = min(total_pages + 1, start + num_pages_max)
            start = max(1, end - num_pages_max)
        else:
            start = 1
            end = total_pages + 1

        row = layout.row(align=True)

        # Left arrow
        if total_pages > 1:
            left = row.row()
            left.enabled = current_page > 1
            left.operator("imeshh.navigate", icon="TRIA_LEFT", text="").page = current_page - 1

        # First page button
        if current_page > num_pages_max // 2 + 1:
            first_left = row.row()
            first_left.operator("imeshh.navigate", text="1...", depress=current_page == 1).page = 1

        # Page buttons
        subrow = row.row()
        middle = subrow.row(align=True)
        for i in range(start, end):
            middle.operator("imeshh.navigate", text=str(i), depress=i == current_page).page = i

        # Last page button
        first_right = row.row()
        if current_page < total_pages - num_pages_max // 2 and total_pages > num_pages_max:
            first_right.operator(
                "imeshh.navigate", text=f"...{str(total_pages)}", depress=current_page == total_pages
            ).page = total_pages

        # Right arrow
        if total_pages > 1:
            right = row.row()
            right.enabled = current_page < total_pages
            right.operator("imeshh.navigate", icon="TRIA_RIGHT", text="").page = current_page + 1

    def draw_local(self, context, layout):

        row = layout.row(align=True)
        row.alignment = "CENTER"

        for asset_type, title in {
            "MODEL": "Models",
            "MATERIAL": "Materials",
            "GEONODE": "Geo Nodes",
            "FX": "Effects",
            "HDRI": "HDRIs",
        }.items():
            subrow = row.row(align=True)
            subrow.enabled = any(item.type == asset_type for item in reversed(self.prefs.custom_paths))
            subrow.prop_enum(
                self.prefs.local,
                "asset_type",
                value=asset_type,
                text=title if self.width > 500 * self.ui_scale else "",
            )

        row.separator()
        subrow = row.row(align=True)
        subrow.alignment = "RIGHT"
        subrow.operator("preferences.addon_enable", text="", icon="FILE_REFRESH").module = package
        subrow.operator("preferences.addon_show", icon="PREFERENCES").module = package

        if not self.prefs.local.folder_list:
            layout.label(text="Add local path in the preferences.")
            return

        col = layout.column()
        col.prop(self.prefs.local, "root_dir", text="")
        for elem in self.prefs.local.folder_list:
            col.prop(elem, "sub_dir", text="")

        row = layout.row(align=True)
        if bpy.app.version >= (4, 2, 0):
            row.prop(self.props, "search", icon="VIEWZOOM", text="", placeholder="Search for assets")
        else:
            row.prop(self.props, "search", icon="VIEWZOOM", text="")
        if self.props.search:
            row.operator("imeshh.search_clear", icon="X", text="")

        self.draw_assets(context, layout)

    def draw_assets(self, context, layout):
        prefs = preferences()
        layout.alignment = "CENTER"

        assets = get_local_assets(self, context)

        if assets:
            start_idx = (self.props.page - 1) * self.prefs.preview_limit
            end_idx = min(start_idx + self.prefs.preview_limit, len(assets))

            # draw top pagination
            self.draw_pagination(context, layout, assets)

            grid = _grid(context, layout, 1.0, assets[start_idx:end_idx])

            seen_paths = {}
            for asset in assets[start_idx:end_idx]:
                if prefs.local.asset_type == "HDRI":
                    self.draw_asset(context, grid, asset)
                else:
                    # Remove resolution suffix like _1k.blend, _2K.blend, etc.
                    base_path = re.sub(r'_[1-9][0-9]*[kK]\.blend$', '', asset.file_path)

                    # Skip if we've already handled this base path
                    if seen_paths.get(base_path):
                        continue

                    # Mark base path as seen
                    seen_paths[base_path] = True

                    match = re.search(r'^(.*)_var-(.+)$', asset.file_path)

                    if match:
                        base_name = match.group(1)
                    else:
                        base_name = os.path.basename(asset.file_path)[:-6]
                    self.draw_asset(context, grid, _variant_map[base_name][_active_number[base_name]])

            # draw bottom pagination
            if len(assets) >= 5:
                self.draw_pagination(context, layout, assets)
        else:
            layout.label(text=f"{self.props.asset_type.title()} assets not found.")

    def draw_asset(self, context, grid, asset):
        prefs = preferences()
        if not asset:
            return

        cell = grid.column(align=True)
        col = cell.box().column()

        filepath = asset.file_path
        preview_path = asset.img_path
        preview = None

        if os.path.exists(filepath) and os.path.exists(preview_path):
            # Only load preview if not already loaded
            if not thumbs.get(preview_path):
                preview = thumbs.load_safe(preview_path, preview_path, "IMAGE")
            else:
                preview = thumbs[preview_path]

            # Only load preview if not already loaded
            if not thumbs.get(preview_path):
                preview = thumbs.load_safe(preview_path, preview_path, "IMAGE")
            else:
                preview = thumbs[preview_path]

            # asset preview
            # Top row with background icon
            top_row = col.row(align=True)
            top_row.emboss = "NONE"
            top_row.alignment = "RIGHT"
            top_row.operator("wm.path_open", icon="IMAGE_BACKGROUND", text="", emboss=False).filepath = preview_path

            # Bottom row with navigation and thumbnail
            bottom_row = col.row(align=True)
            bottom_row.emboss = "NONE"
            bottom_row.alignment = "CENTER"

            # When assume that folder is group.
            base_name = os.path.basename(os.path.dirname(filepath))

            match = re.search(r'^(.*)_var-(.+)$', filepath)
            if match:
                base_name = match.group(1)
                variant_type = match.group(2)
            else:
                base_name = os.path.basename(asset.file_path)[:-6]
                variant_type = None

            # Only show navigation buttons if there are multiple variants
            if  (len(_variant_map[base_name]) > 1 if prefs.local.asset_type != "HDRI" else False) and prefs.local.asset_type == "MODEL":
                # Previous button
                prev_col = bottom_row.row(align=True)
                prev_col.scale_y = 1.0  
                prev_col.alignment = "CENTER"            
                prev_op = prev_col.operator("imeshh.navigate_asset", icon="TRIA_LEFT", text="", emboss=False)
                if prev_op:
                    prev_op.direction = "PREV"
                    prev_op.base_name = base_name
                    prev_op.current_file = filepath # Pass the currently displayed file path

            # Thumbnail
            thumbs_col = bottom_row.row(align=True)
            thumbs_col.template_icon(icon_value=preview.icon_id, scale=self.prefs.preview_scale)
            
            # Only show navigation buttons if there are multiple variants
            if (len(_variant_map[base_name]) > 1 if prefs.local.asset_type != "HDRI" else False) and prefs.local.asset_type == "MODEL":
                # Next button
                next_col = bottom_row.row(align=True)
                next_col.scale_y = 1.0  
                next_col.alignment = "CENTER"
                next_op = next_col.operator("imeshh.navigate_asset", icon="TRIA_RIGHT", text="", emboss=False)
                if next_op:
                    next_op.direction = "NEXT"
                    next_op.base_name = base_name
                    next_op.current_file = filepath # Pass the currently displayed file path

            # asset name
            if self.prefs.show_asset_name:
                subrow = col.row()
                asset_name_without_ex = re.sub(r'_[1-9][0-9]*[kK]$', '', os.path.splitext(os.path.basename(filepath))[0])
                match = re.search(r'^(.*)_var-(.+)$', asset_name_without_ex)
                if match:
                    asset_group_name = match.group(1)
                    suffix = match.group(2)
                    label_text = asset_group_name + '-' + suffix
                else:
                    label_text = asset_name_without_ex

                if prefs.local.asset_type == 'HDRI':
                    label_text = os.path.splitext(os.path.basename(filepath))[0]
                subrow.label(text=label_text)
                subrow.scale_y = 0.8
                subrow.alignment = "CENTER"
                subrow.enabled = False

            col = cell.column(align=True)
            if self.prefs.local.asset_type == "MATERIAL":
                self.draw_local_apply_operator(col, asset, filepath)
            elif self.prefs.local.asset_type == "HDRI":
                self.draw_local_hdri_operator(context, col, asset, filepath)
            else:
                self.draw_local_append_operator(col, asset, filepath)

        cell.separator()

    def draw_local_apply_operator(self, layout, asset, filepath):
        row = layout.row(align=True)
        row.operator("imeshh.apply_local", icon="MATERIAL", depress=True).filepath = filepath
        row.operator("imeshh.options_local", icon="TRIA_DOWN", text="", depress=True).filepath = filepath

    def draw_local_hdri_operator(self, context, layout, asset, filepath):
        row = layout.row(align=True)
        row.operator("imeshh.hdri", icon="WORLD", depress=True).filepath = filepath

        if context.scene.world.node_tree and any(
            (
                node.name in {"imeshh_ground_projection", "imeshh_hdri_nodes"}
                for node in context.scene.world.node_tree.nodes
            )
        ):
            row.operator("imeshh.hdri_properties", icon="PROPERTIES", text="", depress=True)

    def draw_local_append_operator(self, layout, asset, filepath):
        row = layout.row(align=True)
        
        # Show both Append and Link buttons for local assets too
        append_op = row.operator(
            "imeshh.append",
            icon="APPEND_BLEND",
            text="Append",
            depress=True,
        )
        append_op.filepath = filepath
        append_op.link_mode = False
        
        link_op = row.operator(
            "imeshh.append", 
            icon="LINK_BLEND",
            text="Link",
            depress=True,
        )
        link_op.filepath = filepath
        link_op.link_mode = True
        
        row.operator("imeshh.options_local", icon="TRIA_DOWN", text="", depress=True).filepath = filepath


class IMESHH_PT_help(Panel, Imeshh):
    bl_label = f"Help - v{version_str}"
    bl_options = {"DEFAULT_CLOSED"}

    def draw_header_preset(self, context):
        layout = self.layout
        layout.operator("preferences.addon_show", icon="PREFERENCES", emboss=False).module = package

    def draw(self, context):
        layout = self.layout
        layout.scale_y = 1.2

        col = layout.column_flow(columns=0, align=False)
        col.operator("wm.url_open", text="Website", icon_value=icons["IMESHH"]).url = "https://shop.imeshh.com/boi4"
        col.operator("wm.url_open", text="Report a Bug", icon="URL").url = "https://imeshh.com/index.php/faq/"
        col.operator("wm.url_open", text="Support", icon="COMMUNITY").url = "https://imeshh.com/index.php/faq/"


classes = (
    IMESHH_PT_main,
    IMESHH_PT_help,
)

# Preview collection created in the register function.
thumbs = None


def register():
    global thumbs
    thumbs = previews.new(max_size=(300, 300))

    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    global thumbs, _cache_assets
    bpy.utils.previews.remove(thumbs)
    _cache_assets.clear()
    _variant_map.clear()
    _active_number.clear()
