'''
Copyright (C) 2024 Orange Turbine
https://orangeturbine.com
orangeturbine@cgcookie.com

This file is part of the Render Raw add-on, created by Jonathan Lampel for Orange Turbine.

All code distributed with this add-on is open source as described below.

Render Raw is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 3
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, see <https://www.gnu.org/licenses/>.
'''

import bpy
from ..nodes.update_RR import refresh_RR_nodes
from ..nodes.enable_RR import enable_RR
from ..nodes.disable_RR import disable_RR
from ..nodes.active_group import set_active_group, rename_active_group, duplicate_active_group
from ..utilities.settings import get_settings
from ..utilities.nodes import make_subs_single_user
from ..utilities.version import upgrade_all_nodes


class UpgradeNodes(bpy.types.Operator):
    bl_label = 'Upgrade Nodes'
    bl_idname = "render.render_raw_upgrade_nodes"
    bl_description = "Updates Render Raw nodes to be compatible with the latest version. Once upgraded, you will not be able to use the nodes with the previous version of Render Raw. Save a backup before performing this action"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        RR_SCENE = context.scene.render_raw_scene
        return RR_SCENE.enable_RR or context.scene.render_raw.enable_RR

    def execute(self, context):
        upgrade_all_nodes(context)
        refresh_RR_nodes(context)
        context.scene.render_raw_scene.enable_RR = True
        return{'FINISHED'}


class RefreshNodeTree(bpy.types.Operator):
    bl_label = 'Refresh Render Raw Nodes'
    bl_idname = "render.render_raw_refresh_nodes"
    bl_description = 'Removes all Render Raw nodes and imports them again. Useful for when switching a project from one version of the addon to another'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        RR_SCENE = context.scene.render_raw_scene
        return RR_SCENE.enable_RR

    def execute(self, context):
        upgrade_all_nodes(context)
        refresh_RR_nodes(context)
        return{'FINISHED'}


class RefreshActiveGroup(bpy.types.Operator):
    bl_label = 'Refresh Active Node Tree'
    bl_idname = "render.render_raw_refresh_active"
    bl_description = ''
    bl_options = {'REGISTER', 'UNDO'}

    active_group: bpy.props.StringProperty(
        default=''
    )

    @classmethod
    def poll(self, context):
        RR_SCENE = context.scene.render_raw_scene
        return RR_SCENE.enable_RR

    def execute(self, context):
        GROUPS = bpy.data.node_groups

        if self.active_group and self.active_group in GROUPS:
            group = GROUPS[self.active_group]
        else:
            group = None

        set_active_group(context, group)

        return{'FINISHED'}


class RenameActiveGroup(bpy.types.Operator):
    bl_label = 'Rename Active Render Raw Node Group'
    bl_idname = "render.render_raw_rename_active"
    bl_description = 'Rename the active Render Raw Node Group'
    bl_options = {'REGISTER', 'UNDO'}

    Name: bpy.props.StringProperty()

    @classmethod
    def poll(self, context):
        RR_SCENE = context.scene.render_raw_scene
        return RR_SCENE.enable_RR

    def draw(self, context):
        col = self.layout.column()
        col.use_property_split = True
        col.prop(self, 'Name')

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        rename_active_group(context, self.Name)
        return{'FINISHED'}


class DuplicateActiveGroup(bpy.types.Operator):
    bl_label = 'Duplicate Render Raw Node'
    bl_idname = "render.render_raw_duplicate_active"
    bl_description = 'Duplicate the active Render Raw Node in the node editor. This must be used instead of a regular duplicate so that the sub groups inside the node do not remain linked together'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        RR_SCENE = context.scene.render_raw_scene
        return RR_SCENE.enable_RR

    def execute(self, context):
        duplicate_active_group(context)
        return{'FINISHED'}


class UnlinkActiveGroup(bpy.types.Operator):
    bl_label = 'Unlink Render Raw Node'
    bl_idname = "render.render_raw_unlink_active"
    bl_description = 'If you did duplicate a Render Raw node without using the Render Raw duplicate, you can use this to make sure that all necissary subgroups are unique'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        RR_SCENE = context.scene.render_raw_scene
        return RR_SCENE.enable_RR

    def execute(self, context):
        RR = get_settings(context, use_cache=False)
        make_subs_single_user(RR.nodes_group)
        return{'FINISHED'}


classes = [UpgradeNodes, RefreshNodeTree, RefreshActiveGroup, RenameActiveGroup, DuplicateActiveGroup, UnlinkActiveGroup]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
