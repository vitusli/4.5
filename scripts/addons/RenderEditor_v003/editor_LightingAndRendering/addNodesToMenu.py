
"""
*
* The foo application.
*
* Copyright (C) 2025 Yarrawonga VIC woodvisualizations@gmail.com
*
* This program is free software: you can redistribute it and/or modify
* it under the terms of the GNU General Public License as published by
* the Free Software Foundation, either version 3 of the License, or
* (at your option) any later version.
*
* This program is distributed in the hope that it will be useful,
* but WITHOUT ANY WARRANTY; without even the implied warranty of
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
* GNU General Public License for more details.
*
* You should have received a copy of the GNU General Public License
* along with this program.  If not, see <https://www.gnu.org/licenses/gpl-3.0.html>.
*
"""
import bpy


class RLE_MT_AddRenderSettingsNodesMenu(bpy.types.Menu):
    """
    Custom Submenu for Adding Nodes
    """
    bl_label = "Render Settings"
    bl_idname = "RLE_MT_add_render_settings_nodes_menu"

    def draw(self, context):
        layout = self.layout
        layout.operator("node.add_global_settings_node", text="Cycles Global Settings", icon="MOD_DECIM")
        layout.operator("node.add_eevee_global_settings_node", text="Eevee Global Settings", icon="MOD_DECIM")
        layout.operator("node.add_blender_render_settings_node", text="Blender Render Settings", icon="MOD_DECIM")


class RLE_MT_AddObjectSettingsNodesMenu(bpy.types.Menu):
    """
    Custom Submenu for Adding Nodes
    """
    bl_label = "Object Settings"
    bl_idname = "RLE_MT_add_object_settings_nodes_menu"

    def draw(self, context):
        layout = self.layout
        layout.operator("node.add_prune_node", text="Visibility", icon="MOD_DECIM")
        layout.operator("node.add_blender_object_settings_node", text="Cycles Object Settings", icon="MOD_DECIM")
        layout.operator("node.add_eevee_object_settings_node", text="Eevee Object Settings", icon="MOD_DECIM")


class RLE_MT_AddAOVNodesMenu(bpy.types.Menu):
    """
    Custom Submenu for Adding Nodes
    """
    bl_label = "AOV Settings"
    bl_idname = "RLE_MT_add_aov_settings_nodes_menu"

    def draw(self, context):
        layout = self.layout
        layout.operator("node.add_light_group_node", text="LightGroup Create", icon="MOD_DECIM")
        layout.operator("node.add_aov_selection_node", text="Cycles AOV Selection", icon="MOD_DECIM")
        layout.operator("node.add_eevee_aov_selection_node", text="Eevee AOV Selection", icon="MOD_DECIM")
        layout.operator("node.add_blender_denoise_node", text="Denoise", icon="MOD_DECIM")


class RLE_MT_AddSceneNodesMenu(bpy.types.Menu):
    """
    Custom Submenu for Adding Nodes
    """
    bl_label = "Scene Nodes"
    bl_idname = "RLE_MT_add_scene_nodes_menu"

    def draw(self, context):
        layout = self.layout
        layout.operator("node.add_sceneinput_node", text="Scene Input", icon="MOD_DECIM")
        layout.operator("node.add_renderlayer_node", text="Render Layer", icon="MOD_DECIM")


class RLE_MT_AddUiNodes(bpy.types.Menu):
    """
    Custom Submenu for Adding Nodes
    """
    bl_label = "Ui Nodes"
    bl_idname = "RLE_MT_add_ui_nodes_menu"

    def draw(self, context):
        layout = self.layout
        layout.operator("node.add_frame_node", text="Backdrop", icon="MOD_DECIM")
