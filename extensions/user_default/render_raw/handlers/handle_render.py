import bpy
from bpy.app.handlers import persistent

from ..preferences import get_prefs
from ..utilities.view_transforms import view_transforms_disable, view_transforms_enable
from ..utilities.viewport import enable_viewport_compositing, disable_viewport_compositing
from ..utilities.settings import get_settings

realtime_engines = ['BLENDER_WORKBENCH', 'BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE']

@persistent
def RR_pre_render(scene):
    RR = get_settings(bpy.context)
    PREFS = get_prefs(bpy.context)

    if (
        scene.render_raw_scene.enable_RR and
        not scene.render.engine in realtime_engines and
        PREFS.transform_during_render
    ):
        scene.view_settings.view_transform = view_transforms_disable[RR.props_group.view_transform]
        disable_viewport_compositing(bpy.context, 'ALL')


@persistent
def RR_post_render(scene):
    RR = get_settings(bpy.context)
    PREFS = get_prefs(bpy.context)

    if (
        scene.render_raw_scene.enable_RR and
        not scene.render.engine in realtime_engines and
        PREFS.transform_during_render
    ):
        if RR.props_group.view_transform == 'False Color':
            scene.view_settings.view_transform = 'False Color'
        else:
            scene.view_settings.view_transform = 'Raw'
        enable_viewport_compositing(bpy.context, 'SAVED')


def register():
    # Post render handler is currently broken in Blender 4.4
    #if bpy.app.version < (4, 4, 0):
        bpy.app.handlers.render_pre.append(RR_pre_render)
        bpy.app.handlers.render_post.append(RR_post_render)

def unregister():
    # Post render handler is currently broken in Blender 4.4
    #if bpy.app.version < (4, 4, 0):
        bpy.app.handlers.render_pre.remove(RR_pre_render)
        bpy.app.handlers.render_post.remove(RR_post_render)
