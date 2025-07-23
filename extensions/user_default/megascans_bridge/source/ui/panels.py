import os
import platform
from math import ceil
from typing import Dict, List

import bpy
from bpy.types import Panel

from ...qbpy.blender import ui_scale
from ..utils.addon import package, preferences, version, version_str
from ..utils.icon import icons


def _get_draw_width(context) -> float:
    padding = 30 * ui_scale()  # Combined padding (15 for panel + 15 for sidebar)

    # Extra padding for Mac on Blender 3.0+
    if ("mac" in platform.platform() or "darwin" in platform.platform()) and bpy.app.version >= (3, 0, 0):
        padding += 17 * ui_scale()

    width = max(1, context.region.width - padding)
    return width


def _grid(context, layout: bpy.types.UILayout, size_factor: float, items: List[Dict]) -> bpy.types.UILayout:
    # Calculate thumb width
    thumb_width = ceil(170 * size_factor)
    thumb_width *= ui_scale()
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


def is_library_valid(prefs):
    """Check if the megascans library path exists and contains assetsData.json."""
    return prefs.megascans_library_path and os.path.isfile(
        os.path.join(bpy.path.abspath(prefs.megascans_library_path), "assetsData.json")
    )


class MBRIDGE_PT_Base:
    """Base class for all M-Bridge panels."""

    bl_category = "M-Bridge"

    def draw_list(self, layout, listtype_name, dataptr, propname, active_propname, rows=4):
        row = layout.row()
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
        return row.column(align=True)

    def setup_layout(self, layout):
        """Setup common layout properties."""
        layout.use_property_decorate = False
        layout.use_property_split = True
        return layout

    def draw_asset_panel(self, context, property_name):
        """Draw common panel content for assets."""
        layout = self.setup_layout(self.layout)
        mbridge = context.scene.mbridge
        getattr(mbridge, property_name).draw(context, layout)

    def draw_category(self, context, layout, property_name):
        """Draw common panel content for assets."""
        layout = self.setup_layout(layout)
        mbridge = context.scene.mbridge
        getattr(mbridge, property_name).draw_category(context, layout)

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
            left.operator("mbridge.navigate", icon="TRIA_LEFT", text="").page = current_page - 1

        # First page button
        if current_page > num_pages_max // 2 + 1:
            first_left = row.row()
            first_left.operator("mbridge.navigate", text="1...", depress=current_page == 1).page = 1

        # Page buttons
        subrow = row.row()
        middle = subrow.row(align=True)
        for i in range(start, end):
            middle.operator("mbridge.navigate", text=str(i), depress=i == current_page).page = i

        # Last page button
        first_right = row.row()
        if current_page < total_pages - num_pages_max // 2 and total_pages > num_pages_max:
            first_right.operator(
                "mbridge.navigate", text=f"...{str(total_pages)}", depress=current_page == total_pages
            ).page = total_pages

        # Right arrow
        if total_pages > 1:
            right = row.row()
            right.enabled = current_page < total_pages
            right.operator("mbridge.navigate", icon="TRIA_RIGHT", text="").page = current_page + 1

    def draw_asset_thumbnail(self, context, col, asset):
        """Draw common asset thumbnail with info button."""
        # Draw thumbnail with action buttons
        row = col.row(align=True)
        row.emboss = "NONE"
        row.label(text="")
        row.template_icon(icon_value=asset.preview, scale=self.prefs.preview_scale)

        # Info button
        subcol = row.column()
        info_icon = "INFO_LARGE" if bpy.app.version >= (4, 3, 0) else "INFO"
        subcol.operator("mbridge.detail", icon=info_icon, text="").asset_id = asset.id

        # Show asset name if enabled
        if self.prefs.show_asset_name:
            name_row = col.row()
            name_row.label(text=asset.name)
            name_row.scale_y = 0.8
            name_row.alignment = "CENTER"
            name_row.enabled = False

    def get_asset_grid(self, context, layout, assets):
        """Get grid layout for assets with pagination."""
        if not assets:
            return None, 0, 0, False

        start_idx = (self.props.page - 1) * self.prefs.preview_limit
        end_idx = min(start_idx + self.prefs.preview_limit, len(assets))

        self.draw_pagination(context, layout, assets)
        layout.separator()

        grid = _grid(context, layout, 1.0, assets[start_idx:end_idx])

        if len(assets) > self.prefs.preview_limit:
            has_pagination = True
        else:
            has_pagination = False

        return grid, start_idx, end_idx, has_pagination

    def init_panel_props(self, context):
        """Initialize common panel properties."""
        self.width = context.region.width
        self.ui_scale = context.preferences.system.ui_scale
        self.prefs = preferences()
        self.props = context.scene.mbridge

    def draw_search_bar(self, layout, placeholder=None):
        """Draw search bar with clear button."""
        row = layout.row(align=True)
        if bpy.app.version >= (4, 2, 0):
            row.prop(
                self.props,
                "search",
                icon="VIEWZOOM",
                text="",
                placeholder=placeholder or "Search",
            )
        else:
            row.prop(self.props, "search", icon="VIEWZOOM", text="")
        if self.props.search:
            row.operator("mbridge.search_clear", icon="X", text="")

    def get_assets_for_type(self, context, asset_type):
        """Get assets based on the current asset type."""
        return getattr(self.props, asset_type.lower()).get_assets(context)

    def draw_assets_grid(self, context, layout, assets, draw_asset_func):
        """Draw a grid of assets with pagination."""
        layout.alignment = "CENTER"

        grid, start_idx, end_idx, has_pagination = self.get_asset_grid(context, layout, assets)
        if not grid:
            return

        for asset in assets[start_idx:end_idx]:
            draw_asset_func(context, grid, asset)

        if has_pagination:
            self.draw_pagination(context, layout, assets)


class VIEW_3D_Panel(MBRIDGE_PT_Base):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    @classmethod
    def poll(cls, context):
        return is_library_valid(preferences()) and context.mode == "OBJECT"


class NODE_EDITOR_Panel(MBRIDGE_PT_Base):
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"

    @classmethod
    def poll(cls, context):
        return is_library_valid(preferences()) and context.space_data.tree_type == "ShaderNodeTree"


class MBRIDGE_PT_Missing_Base(MBRIDGE_PT_Base):
    bl_label = "Missing"

    @classmethod
    def poll(cls, context):
        prefs = preferences()
        return not prefs.megascans_library_path or not os.path.isfile(
            os.path.join(bpy.path.abspath(prefs.megascans_library_path), "assetsData.json")
        )

    def draw_header_preset(self, context):
        self.layout.operator("preferences.addon_show", icon="PREFERENCES", emboss=False).module = package

    def draw(self, context):
        layout = self.setup_layout(self.layout)
        col = layout.column(align=True)
        col.label(text="Megascans library path is not set properly.")
        col.label(text="Please set the Megascans library path in the preferences.")
        col.label(text="Download some assets to get the Downloaded folder with assetsData.json.")


class MBRIDGE_PT_view3d_missing(Panel, MBRIDGE_PT_Missing_Base, VIEW_3D_Panel):
    pass


class MBRIDGE_PT_node_missing(Panel, MBRIDGE_PT_Missing_Base, NODE_EDITOR_Panel):
    pass


class MBRIDGE_PT_view3d_main(Panel, VIEW_3D_Panel):
    bl_label = "Megascans Bridge"

    def draw_header_preset(self, context):
        self.layout.operator("preferences.addon_enable", text="", icon="FILE_REFRESH", emboss=False).module = package

    def draw(self, context):
        layout = self.layout
        self.init_panel_props(context)

        # Draw asset type
        row = layout.row(align=True)
        row.prop_enum(self.props, "asset_type", "ASSETS")
        row.prop_enum(self.props, "asset_type", "PLANTS")
        row.prop_enum(self.props, "asset_type", "SURFACES")

        if self.props.asset_type not in {"ASSETS", "PLANTS", "SURFACES"}:
            return

        # Draw categories
        asset_type = self.props.asset_type.lower()
        getattr(self.props, asset_type).draw(context, layout)
        assets = self.get_assets_for_type(context, asset_type)

        # Draw search
        self.draw_search_bar(layout, f"Search for {asset_type}")

        if not assets:
            layout.separator()
            row = layout.row(align=True)
            row.alignment = "CENTER"
            row.label(text=f"No {asset_type} found.")
            layout.separator()
            return

        # Draw assets
        self.draw_assets_grid(context, layout, assets, self.draw_asset)

    def draw_asset(self, context, grid, asset):
        if not asset:
            return

        cell = grid.column(align=True)
        col = cell.box().column()

        # Draw common thumbnail and info
        self.draw_asset_thumbnail(context, col, asset)

        # Action area (import and options)
        col = cell.column(align=True)
        row = col.row(align=True)

        # Map asset types to operators
        operators = {
            "ASSETS": "mbridge.asset_add",
            "PLANTS": "mbridge.plant_add",
            "SURFACES": "mbridge.surface_add",
        }

        op = row.operator(operators.get(self.props.asset_type, "mbridge.asset_add"), icon="IMPORT")
        if op:
            op.asset_id = asset.id
        row.operator("mbridge.options", text="", icon="THREE_DOTS").asset_id = asset.id

        cell.separator()


class MBRIDGE_PT_view3d_brushes(Panel, VIEW_3D_Panel):
    bl_label = "Megascans Bridge"

    @classmethod
    def poll(cls, context):
        prefs = preferences()
        if not prefs.megascans_library_path or context.mode != "PAINT_TEXTURE":
            return False
        json_path = os.path.join(bpy.path.abspath(prefs.megascans_library_path), "assetsData.json")
        return os.path.isfile(json_path)

    def draw_header_preset(self, context):
        self.layout.operator("preferences.addon_enable", text="", icon="FILE_REFRESH", emboss=False).module = package

    def draw(self, context):
        layout = self.layout
        self.init_panel_props(context)

        # Draw categories
        getattr(self.props, "brushes").draw(context, layout)
        assets = self.props.brushes.get_assets(context)

        # Draw search
        self.draw_search_bar(layout, "Search for brushes")

        # Draw assets
        self.draw_assets_grid(context, layout, assets, self.draw_asset)

    def draw_asset(self, context, grid, asset):
        if not asset:
            return

        cell = grid.column(align=True)
        col = cell.box().column()

        # Draw common thumbnail and info
        self.draw_asset_thumbnail(context, col, asset)

        # Action area (import and options)
        col = cell.column(align=True)
        row = col.row(align=True)
        row.operator("mbridge.brush_add", icon="IMPORT").asset_id = asset.id
        row.operator("mbridge.options", text="", icon="THREE_DOTS").asset_id = asset.id

        cell.separator()


class MBRIDGE_PT_node_main(Panel, NODE_EDITOR_Panel):
    bl_label = "Megascans Bridge"

    # Node type to operator mapping
    NODE_OPERATORS = {
        "SURFACES": "mbridge.surface_group_add",
        "DECALS": "mbridge.decal_group_add",
        "ATLASES": "mbridge.atlas_group_add",
        "IMPERFECTIONS": "mbridge.imperfection_group_add",
        "DISPLACEMENTS": "mbridge.displacement_group_add",
    }

    def draw_header_preset(self, context):
        self.layout.operator("preferences.addon_enable", text="", icon="FILE_REFRESH", emboss=False).module = package

    def draw(self, context):
        layout = self.layout
        self.init_panel_props(context)

        # Draw asset type
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop_enum(self.props, "asset_type", "SURFACES")
        row.prop_enum(self.props, "asset_type", "DECALS")
        row.prop_enum(self.props, "asset_type", "ATLASES")
        row = col.row(align=True)
        row.prop_enum(self.props, "asset_type", "IMPERFECTIONS")
        row.prop_enum(self.props, "asset_type", "DISPLACEMENTS")

        if self.props.asset_type in {"ASSETS", "PLANTS"}:
            return

        # Draw categories
        asset_type = self.props.asset_type.lower()
        getattr(self.props, asset_type).draw(context, layout)
        assets = self.get_assets_for_type(context, asset_type)

        # Draw search
        self.draw_search_bar(layout, f"Search for {asset_type}")

        if not assets:
            layout.separator()
            row = layout.row(align=True)
            row.alignment = "CENTER"
            row.label(text=f"No {asset_type} found.")
            layout.separator()
            return

        # Draw assets
        self.draw_assets_grid(context, layout, assets, self.draw_asset)

    def draw_asset(self, context, grid, asset):
        if not asset:
            return

        cell = grid.column(align=True)
        col = cell.box().column()

        # Draw common thumbnail and info
        self.draw_asset_thumbnail(context, col, asset)

        # Action area (import and options)
        col = cell.column(align=True)
        row = col.row(align=True)

        # Check if asset already exists in current tree
        current_tree = getattr(context.space_data, "edit_tree", None)
        enabled = not bool(current_tree and asset.id in current_tree.name)

        subrow = row.row(align=True)
        subrow.enabled = enabled
        # Get operator based on node type
        op = subrow.operator(
            self.NODE_OPERATORS.get(self.props.asset_type, "mbridge.surface_group_add"), icon="NODETREE"
        )
        if op:
            op.asset_id = asset.id

        subrow = row.row(align=True)
        subrow.operator("mbridge.options", text="", icon="THREE_DOTS").asset_id = asset.id

        cell.separator()


class MBRIDGE_PT_help:
    bl_label = f"Help - v{version_str}"
    bl_category = "M-Bridge"
    bl_options = {"DEFAULT_CLOSED"}

    def draw_header_preset(self, context):
        self.layout.operator("preferences.addon_show", icon="PREFERENCES", emboss=False).module = package

    def draw(self, context):
        layout = self.layout
        layout.scale_y = 1.2

        col = layout.column()
        if version >= (1, 0, 1):
            col.operator("mbridge.changelog", icon="RECOVER_LAST")
        col.operator(
            "wm.url_open", text="Documentation", icon="HELP"
        ).url = "https://superhivemarket.com/products/megascans-bridge/docs"
        col.operator("wm.url_open", text="Report a Bug", icon="URL").url = "https://discord.gg/sdnHHZpWbT"
        col.operator(
            "wm.url_open", text="Superhive", icon_value=icons["SUPERHIVE"]
        ).url = "https://superhivemarket.com/products/megascans-bridge"
        col.operator(
            "wm.url_open", text="Gumroad", icon_value=icons["GUMROAD"]
        ).url = "https://b3dhub.gumroad.com/l/megascans-bridge"


class MBRIDGE_PT_view3d_help(Panel, VIEW_3D_Panel, MBRIDGE_PT_help):
    pass


class MBRIDGE_PT_node_help(Panel, NODE_EDITOR_Panel, MBRIDGE_PT_help):
    pass


classes = (
    MBRIDGE_PT_view3d_missing,
    MBRIDGE_PT_node_missing,
    MBRIDGE_PT_view3d_main,
    MBRIDGE_PT_view3d_brushes,
    MBRIDGE_PT_node_main,
    MBRIDGE_PT_view3d_help,
    MBRIDGE_PT_node_help,
)


register, unregister = bpy.utils.register_classes_factory(classes)
