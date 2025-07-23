bl_info = {
    "name": "iMeshh",
    "description": "iMeshh Assets Library",
    "blender": (4, 2, 0),
    "version": (1, 2, 4),
    "category": "Assets",
    "location": "3D Viewport > Sidebar(N-Panel) > iMeshh",
    "author": "iMeshh, Karan @b3dhub, @hustor",
    "support": "COMMUNITY",
    "warning": "",
    "doc_url": "",
    "tracker_url": "https://imeshh.com",
}


import bpy

from . import source

# import debugpy
# debugpy.listen(("localhost", 5678))
# print("✅ Waiting for debugger attach...")

def register():
    source.register()


def unregister():
    if hasattr(bpy.context.window_manager, "imeshh"):
        bpy.context.window_manager.imeshh.download_list.clear()

    source.unregister()
