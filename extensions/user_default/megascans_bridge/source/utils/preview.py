import json
import os
from collections import defaultdict
from dataclasses import dataclass

import bpy

from ...t3dn_bip import previews
from .addon import preferences


@dataclass
class Asset:
    id: str = ""
    name: str = ""
    type: str = ""
    path: str = ""
    searchStr: str = ""
    preview: str = ""
    thumb: str = ""
    assetCategories: list = None
    tags: list = None
    semanticTags: list = None
    meta: list = None


def load_json_data(json_file_path):
    try:
        with open(json_file_path, "rb") as file:
            return json.loads(file.read())
    except FileNotFoundError:
        print(f"Warning: {json_file_path} not found")
        return None


def generate_asset(pcoll, data) -> Asset:
    """Create an Asset object from JSON data"""
    id = data["id"]
    filepath = os.path.join(data["parentDir"], *data["preview"])
    preview = pcoll.get(id) or pcoll.load_safe(id, filepath, "IMAGE")

    return Asset(
        id=id,
        name=data.get("name") or os.path.basename(os.path.dirname(filepath)).replace(f"_{id}", ""),
        type=data["type"],
        path=os.path.dirname(filepath),
        searchStr=data["searchStr"],
        preview=preview.icon_id,
        thumb=os.path.join(data["parentDir"], *data["preview"]),
        assetCategories=data.get("assetCategories", []),
        tags=data.get("tags", []),
        semanticTags=data.get("semanticTags", []),
        meta=data.get("meta", []),
    )


def process_asset_dict(json_data, pcoll, asset_type, displacement_mode=False):
    """Process asset data based on asset type and mode"""
    # Filter data for the requested asset type
    asset_data = [data for data in json_data if asset_type in data["assetCategories"]]

    if displacement_mode:
        # Simple list for displacement assets
        return [
            generate_asset(pcoll, data)
            for data in asset_data
            if os.path.exists(os.path.join(data["parentDir"], *data["preview"]))
        ]

    # Otherwise build hierarchical structure
    assets_dict = defaultdict(lambda: defaultdict(list))
    assets_dict["ALL"] = []

    for data in asset_data:
        preview_path = os.path.join(data["parentDir"], *data["preview"])
        if not os.path.exists(preview_path):
            continue

        asset = generate_asset(pcoll, data)
        assets_dict["ALL"].append(asset)

        # Process categories and subcategories
        categories = data["assetCategories"][asset_type]
        for key, category_items in categories.items():
            assets_dict[key]["ALL"].append(asset)

            if category_items:
                for subcategory in category_items:
                    assets_dict[key][subcategory].append(asset)

    return assets_dict


def get_asset_data(preview_key, asset_type, displacement_mode=False):
    """Unified function to get previews for any asset type"""
    prefs = preferences()
    json_file_path = os.path.join(bpy.path.abspath(prefs.megascans_library_path), "assetsData.json")
    pcoll = preview_collections[preview_key]

    # Return empty collection if file doesn't exist
    if not os.path.isfile(json_file_path):
        print(f"Warning: {json_file_path} does not exist")
        return [] if displacement_mode else defaultdict(lambda: defaultdict(list))

    # Return cached previews if file hasn't changed
    if json_file_path == pcoll.previews_dir and os.path.getmtime(json_file_path) <= pcoll.mod_time:
        return pcoll.previews

    # Generate new previews
    if json_data := load_json_data(json_file_path):
        pcoll.previews = process_asset_dict(json_data, pcoll, asset_type, displacement_mode)
        pcoll.previews_dir = json_file_path
        pcoll.mod_time = os.path.getmtime(json_file_path)
        return pcoll.previews

    # Return empty collection if JSON loading failed
    return [] if displacement_mode else defaultdict(lambda: defaultdict(list))


# Asset getter functions
def get_assets():
    return get_asset_data("megascans_assets_previews", "3D asset")


def get_plants():
    return get_asset_data("megascans_plants_previews", "3D plant")


def get_surfaces():
    return get_asset_data("megascans_surfaces_previews", "surface")


def get_decals():
    return get_asset_data("megascans_decals_previews", "decal")


def get_atlases():
    return get_asset_data("megascans_atlases_previews", "atlas")


def get_imperfections():
    return get_asset_data("megascans_imperfections_previews", "imperfection")


def get_displacements():
    return get_asset_data("megascans_displacements_previews", "displacement", True)


def get_brushes():
    return get_asset_data("megascans_brushes_previews", "brush")


# We can store multiple preview collections here
preview_collections = {}
collections = [
    "megascans_assets_previews",
    "megascans_plants_previews",
    "megascans_surfaces_previews",
    "megascans_decals_previews",
    "megascans_atlases_previews",
    "megascans_imperfections_previews",
    "megascans_displacements_previews",
    "megascans_brushes_previews",
]


def create_preview_collection(name):
    pcoll = previews.new()
    pcoll.previews = ()
    pcoll.previews_dir = ""
    pcoll.mod_time = 0
    preview_collections[name] = pcoll


def register():
    for collection in collections:
        create_preview_collection(collection)


def unregister():
    for pcoll in preview_collections.values():
        previews.remove(pcoll)
    preview_collections.clear()
