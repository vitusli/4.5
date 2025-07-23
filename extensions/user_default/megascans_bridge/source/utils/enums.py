import json
import os
from typing import Dict, List, Tuple

import bpy

from .addon import preferences

# Global cache
CACHE = {"mod_time": None, "categories": {}, "subcategories": {}}

ASSET_TYPES = {
    "3D asset": "assets",
    "3D plant": "plants",
    "surface": "surfaces",
    "decal": "decals",
    "atlas": "atlases",
    "imperfection": "imperfections",
    "brush": "brushes",
}


def get_megascans_data(asset_type: str) -> Tuple[List, Dict]:
    """Get categories and subcategories for a specific asset type."""
    global CACHE

    prefs = preferences()
    json_file_path = os.path.join(bpy.path.abspath(prefs.megascans_library_path), "assetsData.json")

    # Check if file exists
    if not os.path.isfile(json_file_path):
        print(f"Warning: {json_file_path} does not exist")
        return [], {}

    # Check cache validity
    mod_time = os.path.getmtime(json_file_path)
    if CACHE["mod_time"] == mod_time and asset_type in CACHE["categories"]:
        return CACHE["categories"][asset_type], CACHE["subcategories"][asset_type]

    # Read JSON file if cache is invalid or missing
    try:
        with open(json_file_path, "r") as file:
            json_data = json.load(file)
    except FileNotFoundError:
        print(f"Warning: {json_file_path} not found")
        return [], {}

    # Process data
    category_set = set()
    subcategory_dict = {}

    for data in json_data:
        asset_category = data["assetCategories"]
        for key, value in asset_category.items():
            if key == asset_type:
                if not os.path.exists(os.path.join(data["parentDir"], *data["preview"])):
                    continue
                # Process categories
                category_set.update(value.keys())
                # Process subcategories
                for category, subcategories in value.items():
                    if category not in subcategory_dict:
                        subcategory_dict[category] = set()
                    subcategory_dict[category].update(subcategories.keys())

    # Sort categories
    sorted_categories = [("ALL", "All", "All Category"), None] + [
        (name, name.title(), "") for name in sorted(category_set)
    ]

    # Sort subcategories
    sorted_subcategories = {category: sorted(subcats) for category, subcats in subcategory_dict.items()}

    # Update cache
    CACHE["mod_time"] = mod_time
    CACHE["categories"][asset_type] = sorted_categories
    CACHE["subcategories"][asset_type] = sorted_subcategories

    return sorted_categories, sorted_subcategories


# Generate enum functions for each asset type
def create_enum_function(asset_type: str, func_type: str):
    def enum_categories(self, context):
        categories, _ = get_megascans_data(asset_type)
        return categories

    def enum_subcategories(self, context):
        _, subcategories = get_megascans_data(asset_type)
        return subcategories

    return enum_categories if func_type == "categories" else enum_subcategories


# Create all the enum functions dynamically
for raw_type, name in ASSET_TYPES.items():
    globals()[f"enum_{name}_categories"] = create_enum_function(raw_type, "categories")
    globals()[f"enum_{name}_subcategories"] = create_enum_function(raw_type, "subcategories")
