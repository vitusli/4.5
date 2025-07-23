# copyright (c) 2018- polygoniq xyz s.r.o.

import bpy
import os
import json
import re
import typing

BLENDER_VERSION_RE = re.compile(r"^(\d+)\.(\d+)$")

BLENDER_CONFIG_DIR = bpy.utils.user_resource('CONFIG')
CONFIG_EXT = "json"


def get_config_dir(addon_name: str, create: bool = False) -> str:
    directory = os.path.join(BLENDER_CONFIG_DIR, addon_name)
    if create and not os.path.exists(directory):
        os.makedirs(directory)
    return directory


def get_config_file_name(config_name: str) -> str:
    return f"{config_name}.{CONFIG_EXT}"


def save_config(addon_name: str, config_name: str, data: typing.Dict) -> None:
    directory = get_config_dir(addon_name, create=True)
    path = os.path.join(directory, get_config_file_name(config_name))

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def has_config(addon_name: str, config_name: str) -> bool:
    directory = get_config_dir(addon_name)
    path = os.path.join(directory, get_config_file_name(config_name))
    return os.path.isfile(path)


def load_config(addon_name: str, config_name: str) -> typing.Dict:
    directory = get_config_dir(addon_name)
    path = os.path.join(directory, get_config_file_name(config_name))

    if not os.path.isfile(path):
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path, encoding="utf-8") as f:
        return json.load(f)


def delete_config_dir(addon_name: str) -> None:
    """Delete the directory containing all configs for the addon"""
    directory = get_config_dir(addon_name)
    if os.path.exists(directory):
        os.rmdir(directory)


def list_versions_with_config(
    addon_name: str, config_name: str
) -> typing.Iterator[typing.Tuple[str, str]]:
    """Look for blender versions with specified config file

    Attempts to find the config file in other versions of Blender.
    Works only for the standard Blender user resources path.

    Returns a list of all Blender versions where the config file was found
    in the format (version, path_to_config_file).
    """
    # By default, this will be .../[bB]lender/"version"/config on all platforms
    # We need to go up to the 'blender' dir and check all versions
    blender_appdata_path = os.path.dirname(os.path.dirname(BLENDER_CONFIG_DIR))
    if os.path.basename(blender_appdata_path).lower() != "blender":
        # This is not a standard path, we can't find other versions
        current_config_path = os.path.join(
            BLENDER_CONFIG_DIR, addon_name, get_config_file_name(config_name)
        )
        if os.path.isfile(current_config_path):
            yield (f"{bpy.app.version[0]}.{bpy.app.version[1]}", current_config_path)
        return

    for version in os.listdir(blender_appdata_path):
        if not re.match(BLENDER_VERSION_RE, version):  # Check if folder is in format number.number
            continue
        config_path = os.path.join(
            blender_appdata_path, version, "config", addon_name, get_config_file_name(config_name)
        )
        if os.path.isfile(config_path):
            yield (version, config_path)
