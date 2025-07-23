bl_info = {
    "name": "Megascans Bridge",
    "description": "Import Megascans assets directly from Blender",
    "author": "Karan @b3dhub",
    "blender": (4, 2, 0),
    "version": (2, 1, 0),
    "category": "Import-Export",
    "location": "3D Viewport | Shader Editor > Sidebar(N-Panel) > M-Bridge",
    "support": "COMMUNITY",
    "warning": "",
    "doc_url": "https://superhivemarket.com/products/megascans-bridge",
    "tracker_url": "https://discord.gg/sdnHHZpWbT",
}

import bpy

from . import source


def register():
    source.register()


def unregister():
    source.unregister()
