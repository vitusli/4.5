import bpy
from ..nodes.update_RR import toggle_RR
from ..nodes.active_group import active_group_items, apply_active_group
from ..nodes.update_values import update_scene_exposure, update_scene_gamma


class RenderRawSceneSettings(bpy.types.PropertyGroup):
    enable_RR: bpy.props.BoolProperty(
        name = 'Enable Render Raw',
        description = 'Swaps out the default color management for a compositing setup that offers greater control over colors',
        default = False,
        update = toggle_RR
    )
    active_group: bpy.props.EnumProperty(
        name = 'Active Render Raw Group',
        description = 'Switch which Render Raw node tree is being edited',
        items = active_group_items,
        default = None,
        update = apply_active_group
    )
    active_RR_group: bpy.props.PointerProperty(
        name = 'Active Node Group',
        type = bpy.types.NodeTree
    )
    active_RR_group_name: bpy.props.StringProperty()

    exposure: bpy.props.FloatProperty(
        name = 'Exposure',
        description = 'Sets the global exposure for the scene',
        default = 0,
        min = -10,
        max = 10,
        precision = 3,
        update = update_scene_exposure
    )
    gamma: bpy.props.FloatProperty(
        name = 'Gamma',
        description = 'Sets the global gamma for the scene',
        default = 1,
        min = 0,
        max = 5,
        precision = 3,
        update = update_scene_gamma
    )
    use_cache: bpy.props.BoolProperty(
        default = True
    )


    # Previous values
    prev_look: bpy.props.StringProperty()
    prev_use_curves: bpy.props.BoolProperty()
    prev_exposure: bpy.props.FloatProperty()
    prev_use_white_balance: bpy.props.BoolProperty()
    prev_temperature: bpy.props.FloatProperty()
    prev_tint: bpy.props.FloatProperty()


def register():
    bpy.utils.register_class(RenderRawSceneSettings)
    bpy.types.Scene.render_raw_scene = bpy.props.PointerProperty(type=RenderRawSceneSettings)

def unregister():
    bpy.utils.unregister_class(RenderRawSceneSettings)