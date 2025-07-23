import os

from t3dn_bip import previews

from .auth import PATH_THUMBS

preview_collections = {}
thumbs = {}


def load_thumbs_from_dir(pcoll, directory):
    for entry in os.scandir(directory):
        if entry.is_file() and entry.name.endswith(".png"):
            pcoll.load_safe(os.path.splitext(entry.name)[0], entry.path, "IMAGE")
        elif entry.is_dir():
            load_thumbs_from_dir(pcoll, entry.path)


def register():
    if "thumbs" in preview_collections:
        unregister()

    if not os.path.exists(PATH_THUMBS):
        os.makedirs(PATH_THUMBS, exist_ok=True)

    pcoll = previews.new()
    preview_collections["thumbs"] = pcoll
    load_thumbs_from_dir(pcoll, PATH_THUMBS)
    thumbs.update({key: value.icon_id for key, value in pcoll.items()})


def unregister():
    for pcoll in preview_collections.values():
        previews.remove(pcoll)

    preview_collections.clear()
    thumbs.clear()
