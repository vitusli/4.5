import threading
from concurrent.futures import ThreadPoolExecutor

import bpy
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    EnumProperty,
    FloatProperty,
    IntProperty,
    StringProperty,
)
from bpy.types import PropertyGroup
from bpy.utils import previews

from .addon import preferences
from .icon import icons
from .product import MAX_WORKERS, download_thumbnail, get_categories, get_products


class SCENE_PG_imeshh(PropertyGroup):

    def _item_asset_library(self, context):
        return (
            ("IMESHH", "iMeshh", "iMeshh assets", icons["IMESHH"], 0),
            ("LOCAL", "Local", "User assets", "FAKE_USER_ON", 1),
        )

    def _update_asset_library(self, context):
        self.category = "ALL"
        self.search = ""
        self.page = 1

    asset_library: EnumProperty(
        name="Asset Source",
        description="Select asset source",
        items=_item_asset_library,
        update=_update_asset_library,
    )

    def _item_asset_source(self, context):
        return (
            ("ONLINE", "Online", "iMeshh", "URL", 0),
            ("DOWNLOADED", "Downloaded", "Downloaded", "IMPORT", 1),
            ("FAVOURITE", "Favourites", "Favourites", "FUND", 2),
        )

    def _update_asset_source(self, context):
        if self.asset_source == "DOWNLOADED":
            get_products(self, cache=False)
        self.page = 1

    asset_source: EnumProperty(
        name="Asset Source",
        description="Select asset source",
        items=_item_asset_source,
        update=_update_asset_source,
    )

    def _item_asset_type(self, context):
        return (
            ("model", "Models", "Models", "OBJECT_DATA", 0),
            ("material", "Materials", "Materials", "MATERIAL", 1),
            ("geonode", "Geo Nodes", "Geometry Nodes", "GEOMETRY_NODES", 2),
            ("fx", "Effects", "Effects", "SHADERFX", 3),
        )

    def _update_asset_type(self, context):
        self.category = "ALL"
        self.search = ""
        self.page = 1

    asset_type: EnumProperty(
        name="Asset Type",
        description="Filter by asset type",
        items=_item_asset_type,
        update=_update_asset_type,
    )

    def _category_items(self, context):
        categories = get_categories()
        if not categories:
            return [("ALL", "All Categories", "", 0)]

        return [("ALL", "All Categories", "", 0), ("FREE", "Free", "", 1), None] + [
            (cat["slug"], cat["name"].replace("&amp;", "&"), cat["description"], cat["id"])
            for cat in categories.get(self.asset_type, [])
        ]

    def _update_category(self, context):
        self.subcategory = "ALL"
        self.search = ""
        self.page = 1

    category: EnumProperty(
        name="Category",
        description="Filter by category",
        items=_category_items,
        update=_update_category,
    )

    def _subcategory_items(self, context):
        categories = get_categories()
        if not categories:
            return [("ALL", "All Sub Categories", "", 0)]

        subcategories = []
        for cat in categories.get(self.asset_type, []):
            if cat["slug"] == self.category:
                subcategories = cat["subcategories"]
                break

        return [("ALL", "All Sub Categories", "", 0), None] + [
            (sub_cat["slug"], sub_cat["name"].replace("&amp;", "&"), sub_cat["description"], sub_cat["id"])
            for sub_cat in subcategories
        ]

    def _update_subcategory(self, context):
        self.search = ""
        self.page = 1

    subcategory: EnumProperty(
        name="Sub Category",
        description="Filter by sub category",
        items=_subcategory_items,
        update=_update_subcategory,
    )

    def _update_products(self, context):
        prefs = preferences()

        if self.asset_type == "model" and self.page == 1:
            return

        products = get_products(self)
        if products:
            start_idx = (self.page - 1) * prefs.preview_limit
            end_idx = min(start_idx + prefs.preview_limit, len(products))

            batch = products[start_idx:end_idx]

            def background_download():
                with ThreadPoolExecutor(MAX_WORKERS, thread_name_prefix="iMeshh_Executor") as executor:
                    executor.map(download_thumbnail, batch)
                for window in bpy.context.window_manager.windows:
                    for area in window.screen.areas:
                        area.tag_redraw()

            if not any(t.name == "iMeshh_Downloader" for t in threading.enumerate()):
                threading.Thread(target=background_download, name="iMeshh_Downloader", daemon=True).start()

    page: IntProperty(
        name="Page",
        description="Navigate to page",
        default=1,
        update=_update_products,
    )

    def _update_search(self, context):
        if not self.search:
            return

        self.page = 1

    search: StringProperty(
        name="Search",
        description="Search for assets",
        default="",
        update=_update_search,
    )

    use_filter_search: BoolProperty(
        name="Filter Search",
        description="Filter search by asset type",
        default=False,
        update=_update_products,
    )

    def _item_search_asset_type(self, context):
        return (
            ("model", "Models", "Models", "OBJECT_DATA", 0),
            ("material", "Materials", "Materials", "MATERIAL", 1),
            ("geonode", "Geo Nodes", "Geometry Nodes", "GEOMETRY_NODES", 2),
            ("fx", "Effects", "Effects", "SHADERFX", 3),
        )

    filter_search_type: EnumProperty(
        name="Filter by Type",
        description="Filter search by asset type",
        items=_item_search_asset_type,
        update=_update_products,
    )


class IMESHH_PG_download_list(PropertyGroup):

    product_id: IntProperty()
    status: StringProperty()
    progress: FloatProperty(default=-1)


class WM_PG_imeshh(PropertyGroup):

    download_list: CollectionProperty(type=IMESHH_PG_download_list)


classes = (
    SCENE_PG_imeshh,
    IMESHH_PG_download_list,
    WM_PG_imeshh,
)

preview_collections = {}


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.imeshh = bpy.props.PointerProperty(type=SCENE_PG_imeshh)
    bpy.types.WindowManager.imeshh = bpy.props.PointerProperty(type=WM_PG_imeshh)

    preview_coll = previews.new()
    preview_collections["asset_previews"] = preview_coll


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.imeshh
    del bpy.types.WindowManager.imeshh

    for preview_coll in preview_collections.values():
        previews.remove(preview_coll)

    preview_collections.clear()
