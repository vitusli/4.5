import bpy
from bpy.app.handlers import persistent
from ..preferences import get_prefs
from ..nodes.update_RR import update_all
from ..utilities.settings import get_settings

@persistent
def frame_change(scene):
    prefs = get_prefs(bpy.context)
    if prefs.animated_values:
        RR = get_settings(bpy.context)
        groups = RR.groups
        for group in groups:
            for idx, layer in enumerate(RR.layers):
                update_all(None, bpy.context, group, idx)


def register():
    bpy.app.handlers.frame_change_post.append(frame_change)
    bpy.app.handlers.render_pre.append(frame_change)

def unregister():
    bpy.app.handlers.frame_change_post.remove(frame_change)
    bpy.app.handlers.render_pre.remove(frame_change)