import bpy
from typing import Literal
from ..nodes.active_group import get_active_group
from ..utilities.settings import get_settings
from ..utilities.cache import cacheless
from ..utilities.layers import (
    refresh_layers, add_layer, remove_layer, move_layer
)
from ..nodes.update_RR import update_all


class AddLayer(bpy.types.Operator):
    bl_label = 'Add Layer'
    bl_idname = 'render.render_raw_add_layer'
    bl_description = ('Adds a layer inside the active Render Raw node')
    bl_options = {'UNDO'}

    @classmethod
    def poll(self, context):
        RR_SCENE = context.scene.render_raw_scene
        return RR_SCENE.enable_RR

    def execute(self, context):
        RR = get_settings(context, use_cache=False)
        add_layer(RR.group)
        return {'FINISHED'}


class RemoveLayer(bpy.types.Operator):
    bl_label = 'Remove Layer'
    bl_idname = 'render.render_raw_remove_layer'
    bl_description = ('Removes the active layer inside the active Render Raw node')
    bl_options = {'UNDO'}

    @classmethod
    def poll(self, context):
        RR_SCENE = context.scene.render_raw_scene
        return RR_SCENE.enable_RR

    def execute(self, context):
        RR = get_settings(context, use_cache=False)
        remove_layer(RR.group)
        return {'FINISHED'}


class MoveLayer(bpy.types.Operator):
    bl_label = 'Move Layer'
    bl_idname = 'render.render_raw_move_layer'
    bl_description = ('Moves the active layer up or down in the stack')
    bl_options = {'UNDO'}

    direction: bpy.props.EnumProperty(
        name = 'Direction',
        items = [
            ('UP', 'Up', 'Moves the layer up one in the stack'),
            ('DOWN', 'Down', 'Moves the layer down one in the stack'),
        ],
        default = 'UP'
    )

    @classmethod
    def poll(self, context):
        RR_SCENE = context.scene.render_raw_scene
        return RR_SCENE.enable_RR

    def execute(self, context):
        RR = get_settings(context, use_cache=False)
        move_layer(RR.group, RR.props_group.active_layer_index, self.direction)
        return {'FINISHED'}


class RefreshLayers(bpy.types.Operator):
    bl_label = 'Refresh Layers'
    bl_idname = 'render.render_raw_refresh_layers'
    bl_description = ('Syncs the layers UI list with the underlying nodes. Only useful if an error has occured')
    bl_options = {'UNDO'}

    @classmethod
    def poll(self, context):
        RR_SCENE = context.scene.render_raw_scene
        return RR_SCENE.enable_RR

    def execute(self, context):
        RR_GROUP = get_active_group(context)
        refresh_layers(RR_GROUP)
        return {'FINISHED'}


class ToggleLayer(bpy.types.Operator):
    bl_label = 'Toggle Layer'
    bl_idname = 'render.render_raw_toggle_layer'
    bl_description = ('Syncs the layers UI list with the underlying nodes. Only useful if an error has occured')
    bl_options = {'UNDO'}

    index: bpy.props.IntProperty(
        name = 'Layer Index'
    )

    @classmethod
    def poll(self, context):
        RR_SCENE = context.scene.render_raw_scene
        return RR_SCENE.enable_RR

    def execute(self, context):
        RR = get_settings(context, layer_index=self.index, use_cache=False)
        RR.props_pre.use_layer = not RR.props_pre.use_layer
        update_all(self, context, layer_index=self.index)
        return {'FINISHED'}


classes = [AddLayer, RemoveLayer, MoveLayer, RefreshLayers, ToggleLayer]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)