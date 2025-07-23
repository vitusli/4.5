import os
import re
from dataclasses import dataclass
from typing import List, Tuple
import time

import bpy

from . import constants
from .addon import preferences


@dataclass
class Asset:
    file_path: str = ""
    img_path: str = ""
    variant_type: str = ""


def without_ext(file: str) -> str:
    """Return filename without extension."""
    return os.path.splitext(file)[0]


def get_dir_content(parent_dir: str) -> Tuple[List[str], List[str]]:
    """Return directories and files contained in parent_dir."""
    dirs, files = [], []
    with os.scandir(parent_dir) as entries:
        for entry in entries:
            (dirs if entry.is_dir() else files).append(entry.path)
    return dirs, files


def make_asset_from_afolder(context, dir_path, files):
    """Create assets from a folder with images and blend files."""
    global _variant_map
    prefs = preferences()
    curr_tab = prefs.local.asset_type
    if not files or curr_tab not in ["MODEL", "MATERIAL", "GEONODE", "FX"]:
        return None

    assets = []
    img_paths = [os.path.join(dir_path, f) for f in files if f.lower().endswith((".png", ".jpg"))]
    blend_paths = [os.path.join(dir_path, f) for f in files if f.lower().endswith(constants.EXT[curr_tab])]

    map = {}
    for blend_path in blend_paths:
        # When assume that folder is group.
        base_name = os.path.basename(os.path.dirname(blend_path))
        # Make a group of variants
        match = re.search(r'^(.*)_var-(.+)$', blend_path)
        if match:
            # base_name = match.group(1)
            variant_type = match.group(2)
        else:
            # base_name = os.path.splitext(blend_path)[0]
            variant_type = None
        
        img_path = img_paths.pop(0) if img_paths else blend_path
        # img_path = blend_path[:-6] + ".png"
        # if not os.path.exists(img_path):
        #     img_path = blend_path[:-6] + ".jpg"
        #     if not os.path.exists(img_path):
        #         img_path = blend_path

        if match:
            base_name = match.group(1)
            if not _variant_map.get(base_name):
                _variant_map[base_name] = []
                _active_number[base_name] = 0

            if not any(asset.file_path == blend_path for asset in _variant_map[base_name]):
                _variant_map[base_name].append(Asset(file_path=blend_path, img_path=img_path))
        else:
            base_name = os.path.basename(blend_path)[:-6]
            _variant_map[base_name] = []
            _active_number[base_name] = 0
            _variant_map[base_name].append(Asset(file_path=blend_path, img_path=img_path))

        if not map.get(base_name):
            assets.append(Asset(file_path=blend_path, img_path=img_path, variant_type=variant_type))
        map[base_name] = True

    return assets


def make_assets_from_files(context, parent_dir, files: List[str]):
    """Make assets by matching blend files with images of the same name."""
    assets = []
    prefs = preferences()
    curr_tab = prefs.local.asset_type

    if not files:
        return assets

    if curr_tab in ["MODEL", "MATERIAL", "GEONODE", "FX"]:
        ext_not_dot = constants.EXT[curr_tab][0].replace(".", "")
        blend_files = [without_ext(f) for f in files if f.lower().endswith(constants.EXT[curr_tab])]

        # Remove blend files from original list
        for b_file in blend_files:
            files.remove(f"{b_file}.{ext_not_dot}")

        map = {}
        # Match images with blend files
        for f in files[:]:
            if not f.lower().endswith((".png", ".jpg")):
                continue

            no_ext_f = without_ext(f)
            if no_ext_f in blend_files:
                blend_files.remove(no_ext_f)
                file_path=os.path.join(parent_dir, f"{no_ext_f}.{ext_not_dot}")
                img_path=os.path.join(parent_dir, f)
                # assets.append(
                #     Asset(
                #         file_path=file_path,
                #         img_path=img_path,
                #     )
                # )
                

                base_name = os.path.basename(os.path.dirname(file_path))
                # Make a group of variants
                match = re.search(r'^(.*)_var-(.+)$', file_path)
                if match:
                    # base_name = match.group(1)
                    variant_type = match.group(2)
                else:
                    # base_name = os.path.splitext(blend_path)[0]
                    variant_type = None
                if match:
                    base_name = match.group(1)
                    if not _variant_map.get(base_name):
                        _variant_map[base_name] = []
                        _active_number[base_name] = 0

                    if not any(asset.file_path == file_path for asset in _variant_map[base_name]):
                        _variant_map[base_name].append(Asset(file_path=file_path, img_path=img_path))
                else:
                    base_name = os.path.basename(file_path)[:-6]
                    _variant_map[base_name] = []
                    _active_number[base_name] = 0
                    _variant_map[base_name].append(Asset(file_path=file_path, img_path=img_path))

                if not map.get(base_name):
                    assets.append(Asset(file_path=file_path, img_path=img_path, variant_type=variant_type))
                map[base_name] = True

        # Handle remaining blend files with no matched image
        for b_file in blend_files:
            f_path = os.path.join(parent_dir, f"{b_file}.{ext_not_dot}")
            # assets.append(Asset(file_path=f_path, img_path=f_path))
            base_name = os.path.basename(os.path.dirname(f_path))
            # Make a group of variants
            match = re.search(r'^(.*)_var-(.+)$', f_path)
            if match:
                # base_name = match.group(1)
                variant_type = match.group(2)
            else:
                # base_name = os.path.splitext(blend_path)[0]
                variant_type = None
            if match:
                base_name = match.group(1)
                if not _variant_map.get(base_name):
                    _variant_map[base_name] = []
                    _active_number[base_name] = 0

                if not any(asset.file_path == f_path for asset in _variant_map[base_name]):
                    _variant_map[base_name].append(Asset(file_path=f_path, img_path=f_path))
            else:
                base_name = os.path.basename(f_path)[:-6]
                _variant_map[base_name] = []
                _active_number[base_name] = 0
                _variant_map[base_name].append(Asset(file_path=f_path, img_path=f_path))

            if not map.get(base_name):
                assets.append(Asset(file_path=f_path, img_path=f_path, variant_type=variant_type))
            map[base_name] = True

    elif curr_tab == "HDRI":
        # for f in files:
        #     base_name = os.path.basename(f))
        #     _variant_map[base_name] = []
        #     _active_number[base_name] = 0
        #     _variant_map[base_name].append(Asset(file_path=os.path.join(parent_dir, f), img_path=os.path.join(parent_dir, f), variant_type=None))
        assets = [
            Asset(file_path=os.path.join(parent_dir, f), img_path=os.path.join(parent_dir, f))
            for f in files
            if f.lower().endswith(constants.EXT[curr_tab])
        ]

    return assets


def get_dir_assets(context, dir_path, files):
    """Return assets contained in files depending on dirtype."""
    return (
        make_asset_from_afolder(context, dir_path, files)
        if is_asset_dir(context, dir_path)
        else make_assets_from_files(context, dir_path, files)
    )


def get_all_sub_assets(context, parent_dir: str) -> List[Asset]:
    """Return all assets found below parent_dir in the file hierarchy."""
    all_assets = []
    to_explore = [parent_dir]

    while to_explore:
        curr_dir = to_explore.pop(0)
        dirs, files = get_dir_content(curr_dir)

        if assets := get_dir_assets(context, curr_dir, files):
            all_assets.extend(assets)

        to_explore.extend(dirs)

    return all_assets


def load_preview(img_path: str, pcoll):
    """Load preview if needed and return its id."""
    if img_path in pcoll:
        return pcoll[img_path].icon_id

    img_type = "BLEND" if img_path.endswith(".blend") else "IMAGE"
    return pcoll.load(img_path, img_path, img_type).icon_id


def contains_blend(file_list):
    """Check if any file in the list is a blend file."""
    return any(f.lower().endswith(".blend") for f in file_list)


def contains_filetype(file_list, ext: str) -> bool:
    """Check if any file in the list has the given extension."""
    return any(f.lower().endswith(ext) for f in file_list)


def is_asset_dir(context, directory):
    """Check if directory contains assets and follows structure rules."""
    prefs = preferences()

    dirs, files = get_dir_content(directory)
    curr_tab = prefs.local.asset_type

    # Must contain at least one target file
    if not contains_filetype(files, constants.EXT[curr_tab]):
        return False

    # For MODEL/MATERIAL check sub_dir don't have target files or sub_dir
    if curr_tab in ["MODEL", "MATERIAL", "GEONODE", "FX"]:
        for dir in dirs:
            sub_dirs, sub_files = get_dir_content(dir)
            if contains_filetype(sub_files, constants.EXT[curr_tab]) or sub_dirs:
                return False
    elif curr_tab == "HDRI":
        return False

    return True


def get_tab_main_dirs(self, context):
    """Return as enum items all main directories of the current tab."""
    prefs = preferences()
    return [
        (bpy.path.abspath(dir.path), dir.name, dir.path, "NONE", idx)
        for idx, dir in enumerate(preferences().custom_paths)
        if dir.type == prefs.local.asset_type
    ]


def remove_higher(self, context):
    prefs = preferences()
    remove_indices = []
    found = False

    for idx, f_list in enumerate(prefs.local.folder_list):
        if found:
            remove_indices.append(idx)
        if f_list == self:
            found = True

    # Remove from highest index to lowest to avoid reindexing issues
    for idx in sorted(remove_indices, reverse=True):
        prefs.local.folder_list.remove(idx)


def get_name(filepath: str, context) -> str:
    """Return cleaned file name from given filepath."""
    prefs = preferences()
    name = os.path.basename(filepath)

    for ext in constants.EXT[prefs.local.asset_type]:
        name = name.replace(ext, "")

    return name.replace(" ", "-")


def update_preview(self, context):
    """Update previews list and set to first item if available."""
    prefs = preferences()
    previews = get_local_assets(self, context)
    if previews:
        prefs.local.asset_previews = previews[0][0]


def select(obj):
    obj.select_set(True) if is_2_80() else setattr(obj, "select", True)


def get_selected_file(context):
    prefs = preferences()
    return prefs.local.asset_previews


def is_2_80():
    return bpy.app.version >= (2, 80, 0)


def get_data_colls():
    return bpy.data.collections if hasattr(bpy.data, "collections") else bpy.data.groups


def create_instance_collection(collection, parent_collection):
    empty = bpy.data.objects.new(name=collection.name, object_data=None)
    empty.instance_collection = collection
    empty.instance_type = "COLLECTION"
    parent_collection.objects.link(empty)
    return empty


def select_coll_to_import(collection_names):
    """Select which collection to import based on file type and preferences."""
    # No collections available
    if not collection_names:
        return None

    # Import all collections if specified
    if bpy.prefs.local.asset_manager_collection_import:
        return collection_names

    # Prefer "Collection" if available
    if "Collection" in collection_names:
        return ["Collection"]

    # Look for collections starting with "collection"
    collection_matches = [col for col in collection_names if re.match(r"(^collection)", col, re.IGNORECASE)]
    return collection_matches if collection_matches else collection_names


def link_collections(blend_file, parent_col):
    """Import collections from blend file as instances."""
    objects_linked = False

    # Load collections or objects
    with bpy.data.libraries.load(blend_file, link=True) as (data_from, data_to):
        data_to.collections = select_coll_to_import(data_from.collections)
        if data_to.collections is None:
            objects_linked = True
            data_to.objects = data_from.objects

    # Fix color space if needed
    for img in bpy.data.images:
        if img.colorspace_settings.name == "":
            possible_values = img.colorspace_settings.bl_rna.properties["name"].enum_items.keys()
            if "sRGB" in possible_values:
                img.colorspace_settings.name = "sRGB"

    # Handle objects if no collections were found
    if objects_linked:
        for obj in data_to.objects:
            if bpy.prefs.local.asset_manager_ignore_camera and obj.type == "CAMERA":
                continue
            ov = obj.override_create()
            parent_col.objects.link(ov)
            select(ov)
    else:
        # Check if collections have objects
        sub_objects = sum((list(col.objects) for col in data_to.collections), [])

        # If no objects in collections, link objects directly
        if not sub_objects:
            with bpy.data.libraries.load(blend_file, link=True) as (data_from, data_to):
                data_to.objects = data_from.objects

            for obj in data_to.objects:
                if bpy.prefs.local.asset_manager_ignore_camera and obj.type == "CAMERA":
                    continue
                ov = obj.override_create()
                parent_col.objects.link(ov)
                select(ov)
        else:
            # Create instances for collections
            for col in data_to.collections:
                instance = create_instance_collection(col, parent_col)

                # Auto-rename if needed
                if (
                    re.match(r"(^collection)", instance.name, re.IGNORECASE)
                    and bpy.prefs.local.asset_manager_auto_rename
                ):
                    instance.name = parent_col.name

                select(instance)


def get_selected_blend(context):
    return get_selected_file(context)


def get_asset_col_name():
    return f"Imeshh_Assets_{bpy.context.scene.name}"


def append_blend(blend_file, link=False):
    coll_name = os.path.splitext(os.path.basename(blend_file))[0].title()
    obj_coll = get_data_colls().new(coll_name)

    # Link to asset collection in 2.80+
    if is_2_80():
        asset_coll = get_data_colls()[get_asset_col_name()]
        asset_coll.children.link(obj_coll)

    # Import objects
    if not link:
        with bpy.data.libraries.load(blend_file, link=link) as (data_from, data_to):
            data_to.objects = data_from.objects

        # Fix color space issues
        for img in bpy.data.images:
            if img.colorspace_settings.name == "":
                possible_values = img.colorspace_settings.bl_rna.properties["name"].enum_items.keys()
                if "sRGB" in possible_values:
                    img.colorspace_settings.name = "sRGB"

        # Link objects to collection
        for obj in data_to.objects:
            if bpy.prefs.local.asset_manager_ignore_camera and obj.type == "CAMERA":
                continue

            obj_coll.objects.link(obj)
            select(obj)
    else:
        link_collections(blend_file, obj_coll)

    bpy.ops.view3d.snap_selected_to_cursor(use_offset=True)


def import_object(context, link):
    # Deselect all objects
    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode="OBJECT", toggle=False)
    bpy.ops.object.select_all(action="DESELECT")

    # Create asset collection if needed
    if is_2_80():
        asset_col_name = get_asset_col_name()
        if asset_col_name not in bpy.context.scene.collection.children.keys():
            asset_coll = bpy.data.collections.new(asset_col_name)
            context.scene.collection.children.link(asset_coll)

    # Import the blend file
    blend = get_selected_blend(context)
    if blend:
        append_blend(blend, link)


def import_material(context, link):
    active_ob = context.active_object

    # Enter object mode and deselect all
    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode="OBJECT", toggle=False)
    bpy.ops.object.select_all(action="DESELECT")

    # Import material
    blend = get_selected_blend(context)
    if not blend:
        return

    # Set up files to import
    with bpy.data.libraries.load(blend) as (data_from, data_to):
        files = [{"name": name} for name in data_from.materials]

    # Do the import
    action = bpy.ops.wm.link if link else bpy.ops.wm.append
    action(directory=f"{blend}/Material/", files=files)

    # Apply materials to active object
    if active_ob is not None:
        for file in files:
            mat = bpy.data.materials[file["name"]]
            active_ob.data.materials.append(mat)
            select(active_ob)


# Cache dictionary to store previews based on parameters
_cache_assets = {}
_variant_map = {}
_active_number = {}

def get_local_assets(self, context):
    """Return items of the preview panel."""
    global _cache_assets
    global _variant_map
    global _active_number
    prefs = preferences()
    props = context.scene.imeshh

    
    if not prefs.local.folder_list:
        return []
    
    if len(prefs.custom_paths) == 0:
        return []

    # Get current directory and search term
    curr_dir = prefs.local.folder_list[-1].name
    search_term = props.search.lower()

    # Create cache key
    cache_key = f"{curr_dir}_{search_term}" if search_term else curr_dir

    # Return cached results if available
    if cache_key in _cache_assets:
        return _cache_assets[cache_key]

    # Get assets and filter by search term
    assets = []
    if os.path.exists(curr_dir):
        assets = get_all_sub_assets(context, curr_dir)

        if search_term:
            assets = [asset for asset in assets if re.search(search_term, os.path.basename(asset.file_path).lower())]

    # Cache and return results
    _cache_assets[cache_key] = assets
    return assets

def get_all_local_assets(self, context):
    """Return items of the preview panel."""
    global _cache_assets
    global _variant_map
    global _active_number
    prefs = preferences()
    props = context.scene.imeshh
    assets = []
    for custom_path in prefs.custom_paths:

        # Get current directory and search term
        curr_dir = custom_path.path

        # Get assets and filter by search term
        if os.path.exists(curr_dir):
            assets = get_all_sub_assets(context, curr_dir)

    return assets