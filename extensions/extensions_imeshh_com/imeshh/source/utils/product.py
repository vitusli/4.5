import json
import os
import re
import threading

import bpy
import requests

from .addon import preferences
from .auth import (
    HEADERS,
    PATH_CATEGORIES_FILE,
    PATH_FAVOURITES_FILE,
    PATH_IMAGES,
    PATH_PRODUCTS_FILE,
    PATH_STATUS_FILE,
    PATH_THUMBS,
    URL_CATEGORIES,
    URL_FX_ASSETS_CAT,
    URL_GEO_NODES_ASSETS_CAT,
    URL_MAT_ASSETS_CAT,
    URL_MODEL_ASSETS_CAT,
    URL_PRODUCTS,
    get_status_data,
    save_status_data,
)

MAX_WORKERS = min(os.cpu_count() // 2, 16)


def get_version(version: str) -> str:
    versions = {"1": "v3.0+", "2": "v3.3+", "3": "v3.5+", "4": "v3.6+", "5": "v4.1+", "6": "v4.2+", "7": "v4.3+"}
    return versions.get(version, "v3.0+")


def get_license_type(license_type: str) -> str:
    licenses = {"1": "Royalty Free", "2": "Editorial"}
    return licenses.get(license_type, "Royalty Free")


def get_assets_path(context) -> str:
    prefs = preferences()
    props = context.scene.imeshh

    if props.asset_type == "material":
        return prefs.materials_path
    elif props.asset_type == "geonode":
        return prefs.geonodes_path
    elif props.asset_type == "fx":
        return prefs.fxs_path
    else:
        return prefs.models_path


def save_categories_data():
    """Fetch categories and save them to file."""

    def worker():
        try:
            print("INFO: Fetching latest categories...")
            response = requests.get(URL_CATEGORIES, headers=HEADERS)
            if response is not None and response.status_code == 200:
                categories = response.json()
                with open(PATH_CATEGORIES_FILE, "w", encoding="utf-8") as file:
                    json.dump(categories, file)
                print("SUCCESS: Categories data fetched successfully!")
            elif response is None:
                print("ERROR: No response received. Check if the authentication token exists.")
            else:
                print(f"ERROR: Failed to fetch latest categories. HTTP Status: {response.status_code}")
        except Exception as e:
            print(f"EXCEPTION: An error occurred while fetching latest categories: {e}")

    threading.Thread(target=worker, daemon=True).start()


def save_products_data():
    """Fetch products and save them to file."""

    def worker():
        try:
            print("INFO: Fetching latest products...")
            response = requests.get(URL_PRODUCTS, headers=HEADERS)
            if response is not None and response.status_code == 200:
                products = response.json()
                with open(PATH_PRODUCTS_FILE, "w", encoding="utf-8") as file:
                    json.dump(products, file)
                print("SUCCESS: Products data fetched successfully!")
            elif response is None:
                print("ERROR: No response received. Check if the authentication token exists.")
            else:
                print(f"ERROR: Failed to fetch latest products. HTTP Status: {response.status_code}")
        except Exception as e:
            print(f"EXCEPTION: An error occurred while fetching latest products: {e}")

    threading.Thread(target=worker, daemon=True).start()


def save_assets_cat_data(index: int = None):
    prefs = preferences()

    tasks = [
        (URL_MODEL_ASSETS_CAT, os.path.join(prefs.models_path, "iMeshh-Models", "blender_assets.cats.txt")),
        (URL_MAT_ASSETS_CAT, os.path.join(prefs.materials_path, "iMeshh-Materials", "blender_assets.cats.txt")),
        (URL_GEO_NODES_ASSETS_CAT, os.path.join(prefs.geonodes_path, "iMeshh-Geo-Nodes", "blender_assets.cats.txt")),
        (URL_FX_ASSETS_CAT, os.path.join(prefs.fxs_path, "iMeshh-Effects", "blender_assets.cats.txt")),
    ]

    tasks = [tasks[index]] if index is not None else tasks

    def worker(url, file_path):
        try:
            print(f"INFO: Fetching latest assets cat data... {'/'.join(url.split('/')[-2:])}")
            response = requests.get(url, headers=HEADERS)
            if response is not None and response.status_code == 200:
                with open(file_path, "wb") as file:
                    file.write(response.content)
                print("SUCCESS: Assets cat data fetched successfully!")
            elif response is None:
                print("ERROR: No response received. Check if the authentication token exists.")
            else:
                print(f"ERROR: Failed to fetch assets cat data from {url}. HTTP Status: {response.status_code}")
        except Exception as e:
            print(f"EXCEPTION: An error occurred while fetching assets cat data from {url}: {e}")

    for url, file_path in tasks:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        threading.Thread(target=worker, args=(url, file_path), daemon=True).start()


def download_thumbnail(product: dict):
    """Download thumbnail if it doesn't exist."""
    os.makedirs(PATH_THUMBS, exist_ok=True)

    thumbnail_name = (
        f'{product.get("thumbnail_name", "")}_{product.get("thumbnail_date_modified", "").replace(":", "-")}'
    )
    thumbnail_src = product.get("thumbnail_src")

    if not thumbnail_name or not thumbnail_src:
        return

    thumbnail_path = os.path.join(PATH_THUMBS, f"{thumbnail_name}.png")
    if os.path.exists(thumbnail_path):
        return

    try:
        response = requests.get(thumbnail_src, headers=HEADERS)
        if response.status_code == 200:
            with open(thumbnail_path, "wb") as file:
                file.write(response.content)
        else:
            print(f"Failed to download thumbnail: HTTP {response.status_code}")
    except Exception as e:
        print(f"Error downloading thumbnail for {thumbnail_name}: {e}")


def download_image(image: dict):
    """Download images if it doesn't exist."""
    os.makedirs(PATH_IMAGES, exist_ok=True)

    image_name = f'{image.get("name", "")}_{image.get("date_modified", "").replace(":", "-")}'
    image_src = image.get("src").replace(".png", "-1024x1024.png")

    if not image_name or not image_src:
        return

    image_path = os.path.join(PATH_IMAGES, f"{image_name}.png")
    if os.path.exists(image_path):
        return

    try:
        response = requests.get(image_src, headers=HEADERS)
        if response.status_code == 200:
            with open(image_path, "wb") as file:
                file.write(response.content)
        else:
            print(f"Failed to download images: HTTP {response.status_code}")
    except Exception as e:
        print(f"Error downloading images for {image_name}: {e}")


# Cache for categories data
_cached_categories = None
_categories_mtime = None


def get_categories() -> dict:
    global _cached_categories, _categories_mtime

    if not os.path.exists(PATH_CATEGORIES_FILE):
        return None

    mtime = os.path.getmtime(PATH_CATEGORIES_FILE)
    if _cached_categories is not None and _categories_mtime == mtime:
        return _cached_categories

    with open(PATH_CATEGORIES_FILE, "r", encoding="utf-8") as file:
        _cached_categories = json.load(file)
        _categories_mtime = mtime
        return _cached_categories


def get_asset_path(product: dict) -> str:
    """Get the path of the asset in the default folder"""
    if not product.get("categories") or not product.get("sub-categories"):
        return ""

    prefs = preferences()

    # Map asset types to their base paths
    base_paths = {
        "model": os.path.join(prefs.models_path, "iMeshh-Models"),
        "material": os.path.join(prefs.materials_path, "iMeshh-Materials"),
        "geonode": os.path.join(prefs.geonodes_path, "iMeshh-Geo-Nodes"),
        "fx": os.path.join(prefs.fxs_path, "iMeshh-Effects"),
    }

    # Get base path or default to models
    asset_type = product.get("asset_type", "model")
    base_path = base_paths.get(asset_type, base_paths["model"])

    # Format file name with date
    # date_modified = product.get("date_modified").replace(":", "-")
    # download_name = f'{product.get("downloads")[0].get("name", product.get("thumbnail_name", ""))}_{date_modified}'

    download_name = f'{product.get("downloads")[0].get("name", product.get("thumbnail_name", ""))}'

    # Clean filename by removing common suffixes
    clean_name = re.sub(r"(?i)(?:_blender|gltf|(?:_?(?:124|4|8|16|32)k)|1[+\-]2[+\-]4k|\.zip)", "", download_name)

    asset_path = os.path.join(
        base_path,
        product.get("categories", {}).get("name", ""),
        product.get("sub-categories", [{}])[0].get("name", ""),
        clean_name,
    )

    return asset_path


# Cache for products data and filtered results
_cached_products = {
    "raw_data": None,
    "filtered_results": {},
}


def get_products(props: bpy.types.PropertyGroup, cache: bool = True) -> list:
    """Get and filter products with caching for better performance."""
    if not os.path.exists(PATH_PRODUCTS_FILE):
        print("WARNING: Products data file not found. Please reload the addon.")
        return []

    # Add product file modification time tracking
    products_mtime = os.path.getmtime(PATH_PRODUCTS_FILE) if os.path.exists(PATH_PRODUCTS_FILE) else None

    # Load raw data if cache is empty or file has been modified
    if _cached_products["raw_data"] is None or (_cached_products.get("last_mtime") != products_mtime):
        try:
            with open(PATH_PRODUCTS_FILE, "r", encoding="utf-8") as file:
                _cached_products["raw_data"] = [
                    p
                    for p in json.load(file)
                    if p.get("status", "") == "publish"
                    and p.get("id")
                    and p.get("asset_type")
                    and p.get("categories")
                    and p.get("sub-categories")
                    and p.get("downloads", [])
                ]
                _cached_products["last_mtime"] = products_mtime
                _cached_products["filtered_results"].clear()  # Clear filtered results cache when raw data changes
        except json.JSONDecodeError:
            print("ERROR: Products file is corrupted. Please reload the addon.")
            _cached_products["raw_data"] = []

    # Create cache key based on filter parameters
    cache_key = f"{props.asset_source}_{props.asset_type}_{props.category}_{props.subcategory}_{props.search}_{props.use_filter_search}_{props.filter_search_type}"

    # Return cached filtered results if available
    if cache and cache_key in _cached_products["filtered_results"]:
        return _cached_products["filtered_results"][cache_key]

    products = _cached_products["raw_data"]

    if props.asset_source == "DOWNLOADED":

        def is_downloaded(p):
            item = next(
                (item for item in bpy.context.window_manager.imeshh.download_list if item.product_id == p.get("id")),
                None,
            )
            return os.path.exists(get_asset_path(p)) or (item is not None and item.progress >= 0)

        products = [p for p in products if is_downloaded(p)]
    elif props.asset_source == "FAVOURITE":
        products = [p for p in products if p.get("id") in get_favourites()]

    # Apply filters
    if props.asset_type:
        products = [p for p in products if props.asset_type == p.get("asset_type", "")]

        if props.category == "FREE":
            products = [p for p in products if p.get("is_freebie", False)]
        elif props.category and props.category != "ALL":
            products = [
                p for p in products if p.get("categories") and p.get("categories", {}).get("slug", "") == props.category
            ]
            if props.subcategory and props.subcategory != "ALL":
                products = [
                    p
                    for p in products
                    if p.get("sub-categories") and p.get("sub-categories", [])[0].get("slug", "") == props.subcategory
                ]

    if props.search:
        product_list = products if props.asset_source in {"DOWNLOADED", "FAVOURITE"} else _cached_products["raw_data"]
        search_term = props.search.lower()
        products = [
            p
            for p in product_list
            if any(
                [
                    re.search(search_term, p.get("name", "").lower()),
                    re.search(search_term, p.get("categories", {}).get("slug", "").lower()),
                    p.get("sub-categories")
                    and re.search(search_term, p.get("sub-categories", [])[0].get("slug", "").lower()),
                ]
            )
        ]

        if props.use_filter_search:
            products = [p for p in products if props.filter_search_type == p.get("asset_type")]

    _cached_products["filtered_results"][cache_key] = products
    return products


# Cache for favourites data
_cached_favourites = None
_favourites_last_modified = 0


def get_favourites():
    global _cached_favourites, _favourites_last_modified

    if not os.path.exists(PATH_FAVOURITES_FILE):
        return []

    # Check if file has been modified
    try:
        current_mtime = os.path.getmtime(PATH_FAVOURITES_FILE)
        if current_mtime > _favourites_last_modified or _cached_favourites is None:
            with open(PATH_FAVOURITES_FILE, "r", encoding="utf-8") as file:
                _cached_favourites = json.load(file)
                _favourites_last_modified = current_mtime
                # Invalidate the filtered products cache when favorites change
                _cached_products["filtered_results"].clear()
    except json.JSONDecodeError:
        print("ERROR: Favourites file is corrupted. Please reload the addon.")
        return []

    return _cached_favourites.get("product_ids", [])


# @bpy.app.handlers.persistent
def _load_post_update_data_files(_):
    def worker():
        new_status = get_status_data()
        need_update = (
            not os.path.exists(PATH_STATUS_FILE)
            or not os.path.exists(PATH_CATEGORIES_FILE)
            or not os.path.exists(PATH_PRODUCTS_FILE)
        )

        if not need_update:
            with open(PATH_STATUS_FILE, "r", encoding="utf-8") as f:
                stored_status = json.load(f)
            need_update = new_status and new_status.get("last_updated") != stored_status.get("last_updated")

        if need_update:
            save_products_data()
            save_categories_data()
            save_assets_cat_data()
            save_status_data(new_status)

    threading.Thread(target=worker, daemon=True).start()

    if hasattr(bpy.context.scene, "imeshh"):
        bpy.context.scene.imeshh.page = 1

    if hasattr(bpy.context.window_manager, "imeshh"):
        bpy.context.window_manager.imeshh.download_list.clear()


latest_version = None


# @bpy.app.handlers.persistent
def _load_post_update_addon(_):
    global latest_version
    try:
        response = requests.get("https://extensions.imeshh.com/wp-json/imeshh-api/v1/extension")
        data = response.json()
        latest_version_str = data["data"][0]["version"]
        # Convert string version (e.g., "1.2.0") to tuple (e.g., (1, 2, 0))
        latest_version = tuple(map(int, latest_version_str.split(".")))
    except Exception as e:
        print(f"Error checking for updates: {e}")
        pass


def register():
    bpy.app.handlers.load_post.append(_load_post_update_data_files)
    bpy.app.handlers.load_post.append(_load_post_update_addon)


def unregister():
    if _load_post_update_data_files in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_load_post_update_data_files)

    if _load_post_update_addon in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_load_post_update_addon)
