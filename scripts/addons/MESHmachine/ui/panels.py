import bpy
import os

from .. utils.ui import get_icon, get_panel_fold
from .. utils.registration import get_path, get_prefs, get_pretty_version

from .. import bl_info

class PanelMESHmachine(bpy.types.Panel):
    bl_idname = "MACHIN3_PT_mesh_machine"
    bl_label = f"MESHmachine {get_pretty_version(bl_info['version'])}"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MACHIN3"
    bl_order = 10

    @classmethod
    def poll(cls, context):
        return get_prefs().show_sidebar_panel

    def draw_header(self, context):
        layout = self.layout

        mm = context.scene.MM

        if get_prefs().update_available:
            layout.label(text="", icon_value=get_icon("refresh_green"))

        row = layout.row(align=True)
        row.prop(mm, "register_panel_help", text="", icon="QUESTION")

    def draw(self, context):
        layout = self.layout
        column = layout.column()

        mm = context.scene.MM
        active = context.active_object
        can_sweep = [obj for obj in context.scene.objects if obj.MM.isstashobj]

        if get_prefs().update_available:
            column.separator()

            row = column.row()
            row.scale_y = 1.2
            row.label(text="An Update is Available", icon_value=get_icon("refresh_green"))
            row.operator("wm.url_open", text="What's new?").url = 'https://machin3.io/MESHmachine/docs/whatsnew'

            column.separator()

        if can_sweep:
            row = column.row(align=True)
            row.alignment = 'CENTER'
            row.label(text="Stashes have been linked to the Scene.")

            row = column.row()
            row.scale_y = 1.2
            row.alert = True
            row.operator('machin3.sweep_stashes', text='Sweep Stashes', icon='BRUSH_DATA')

        if panel := get_panel_fold(column, "plugs", "Plug Placement", icon="PLUGIN", default_closed=False):
            row = panel.split(factor=0.33)
            row.label(text="Plug Align")
            r = row.row()
            r.prop(mm, "align_mode", expand=True)

        if active and active.MM.stashes:
            if panel := get_panel_fold(column, "stashes", f"{active.name}'s Stashes", default_closed=False):
                box = panel.box()
                column = box.column()
                column.label(text=f"{active.name} {'(' + active.MM.stashname + ')' if active.MM.stashname else ''}")

                column.template_list("MACHIN3_UL_stashes", "", active.MM, "stashes", active.MM, "active_stash_idx", rows=max(len(active.MM.stashes), 1))

        if bpy.ops.machin3.meshmachine_debug.poll():
            column.separator()

            column.scale_y = 2
            column.operator('machin3.meshmachine_debug', text='Button')

class PanelHelp(bpy.types.Panel):
    bl_idname = "MACHIN3_PT_help_mesh_machine"
    bl_label = "MESHmachine Help"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MACHIN3"
    bl_order = 11

    @classmethod
    def poll(cls, context):
        return get_prefs().show_sidebar_panel and context.scene.MM.register_panel_help

    def draw(self, context):
        layout = self.layout

        resources_path = os.path.join(get_path(), "resources")
        example_tutorial_path = os.path.join(resources_path, "Example_Tutorial.blend")
        example_plugged_path = os.path.join(resources_path, "Example_Plugged.blend")

        column = layout.column(align=True)
        column.alert = True

        if panel := get_panel_fold(column, "support", "Support", icon="GREASEPENCIL", default_closed=False):
            row = column.row()
            row.scale_y = 1.5
            row.operator("machin3.get_meshmachine_support", text="Get Support", icon='GREASEPENCIL')

        if panel := get_panel_fold(layout, "documentation", "Documentation", icon="INFO", default_closed=False):
            row = panel.row(align=True)
            row.scale_y = 1.2
            row.operator("wm.url_open", text="Local", icon='FILE_BACKUP').url = "file://" + os.path.join(get_path(), "docs", "index.html")
            row.operator("wm.url_open", text="Online", icon='FILE_BLEND').url = "https://machin3.io/MESHmachine/docs"

            row = panel.row(align=True)
            row.scale_y = 1.2
            row.operator("wm.url_open", text="FAQ", icon='QUESTION').url = "https://machin3.io/MESHmachine/docs/faq"
            row.operator("wm.url_open", text="Youtube", icon='FILE_MOVIE').url = "https://www.youtube.com/watch?v=i68jOGMEUV8&list=PLcEiZ9GDvSdXR9kd4O6cdQN_6i0LOe5lw"

        if panel := get_panel_fold(layout, "plug_packs", "3rd Party Plug Packs", icon="PLUGIN", default_closed=True):
            row = panel.row()
            row.scale_y = 1.2
            row.operator("wm.url_open", text="Plug Packs", icon='PLUGIN').url = "https://machin3.io/MESHmachine/docs/plug_resources"

        if panel := get_panel_fold(layout, "examples", "Examples", icon="BLENDER", default_closed=True):
            if bpy.data.is_dirty:
                column = panel.column(align=True)
                column.alert = True
                row = column.row(align=True)
                row.alignment = 'CENTER'
                row.label(text="Your current file is not saved!", icon="ERROR")
                row = column.row(align=True)
                row.alignment = 'CENTER'
                row.label(text="Unsaved changes will be lost,", icon="BLANK1")
                row = column.row(align=True)
                row.alignment = 'CENTER'
                row.label(text="if you load the following examples.", icon="BLANK1")

            row = panel.row(align=True)
            row.operator_context = 'EXEC_DEFAULT'
            row.scale_y = 1.5

            op = row.operator("wm.open_mainfile", text="Tutorial", icon="FILE_BLEND")
            op.filepath=example_tutorial_path
            op.load_ui = True

            op = row.operator("wm.open_mainfile", text="Plugged", icon="FILE_BLEND")
            op.filepath=example_plugged_path
            op.load_ui = True

        if panel := get_panel_fold(layout, "discuss", "Discuss", icon="COMMUNITY", default_closed=True):
            row = panel.row(align=True)
            row.scale_y = 1.2
            row.operator("wm.url_open", text="Blender Artists", icon="COMMUNITY").url = "https://blenderartists.org/t/meshmachine/1102529"

        if panel := get_panel_fold(layout, "follow_dev", "Follow Development", icon="USER", default_closed=True):
            column = panel.column()
            column.label(text='Twitter')

            row = column.row(align=True)
            row.scale_y = 1.2
            row.operator("wm.url_open", text="@machin3io").url = "https://twitter.com/machin3io"
            row.operator("wm.url_open", text="#MESHmachine").url = "https://twitter.com/search?q=(%23MESHmachine)%20(from%3Amachin3io)&src=typed_query&f=live"

            column.label(text='Youtube')
            row = column.row()
            row.scale_y = 1.2
            row.operator("wm.url_open", text="MACHIN3").url = "https://www.youtube.com/c/MACHIN3"
