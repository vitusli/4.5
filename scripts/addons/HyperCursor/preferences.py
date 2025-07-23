import bpy
from bpy.props import BoolProperty, EnumProperty, StringProperty, FloatProperty, IntProperty
import os

from . import bl_info

from . utils import ui
from . utils.draw import draw_split_row
from . utils.registration import get_path, get_name
from . utils.system import get_bl_info_from_file, remove_folder, get_update_files

from . items import prefs_tab_items, keymap_folds
from . registration import keys as keysdict

tool_keymaps = [
    '3D View Tool: Object, Hyper Cursor',
    '3D View Tool: Edit Mesh, Hyper Cursor',
]

tool_keymaps_mapping = {
    ('machin3.tool_hyper_cursor', 'OBJECT'): tool_keymaps[0],
    ('machin3.tool_hyper_cursor', 'EDIT_MESH'): tool_keymaps[1],
}

hud_shadow_items = [
    ('0', '0', "Don't Blur Shadow"),
    ('3', '3', 'Shadow Blur Level 3'),
    ('5', '5', 'Shadow Blur level 5')
]

class HyperCursorPreferences(bpy.types.AddonPreferences):
    path = get_path()
    bl_idname = get_name()

    def update_update_path(self, context):
        if self.avoid_update:
            self.avoid_update = False
            return

        if self.update_path:
            if os.path.exists(self.update_path):
                filename = os.path.basename(self.update_path)

                if filename.endswith('.zip'):
                    split = filename.split('_')

                    if len(split) == 2:
                        addon_name, tail = split

                        if addon_name == bl_info['name']:
                            split = tail.split('.')

                            if len(split) >= 3:
                                dst = os.path.join(self.path, '_update')

                                from zipfile import ZipFile

                                with ZipFile(self.update_path, mode="r") as z:
                                    print(f"INFO: extracting {addon_name} update to {dst}")
                                    z.extractall(path=dst)

                                blinfo = get_bl_info_from_file(os.path.join(dst, addon_name, '__init__.py'))

                                if blinfo:
                                    self.update_msg = f"{blinfo['name']} {'.'.join(str(v) for v in blinfo['version'])} is ready to be installed."

                                else:
                                    remove_folder(dst)

            self.avoid_update = True
            self.update_path = ''

    update_path: StringProperty(name="Update File Path", subtype="FILE_PATH", update=update_update_path)
    update_msg: StringProperty(name="Update Message")

    registration_debug: BoolProperty(name="Addon Terminal Registration Output", default=True)

    def update_boolean_method(self, context):
        if self.avoid_update:
            self.avoid_update = False
            return

        if not any([self.boolean_method_difference, self.boolean_method_union, self.boolean_method_intersect, self.boolean_method_split, self.boolean_method_gap, self.boolean_method_meshcut]):
            self.avoid_update = True
            self.boolean_method_difference = True

    def update_set_transform(self, context):
        if self.transform_cursor_default_drag_snap_set_transform_machin3tools and self.transform_cursor_default_drag_snap_set_transform:
            self.transform_cursor_default_drag_snap_set_transform = False
    transform_cursor_default_show_absolute_coords: BoolProperty(name="Show Absolute Coords", default=False)
    transform_cursor_default_always_drag_snap: BoolProperty(name="Always Snap when dragging the Cursor", default=False)
    transform_cursor_default_drag_snap_set_transform: BoolProperty(name="Set Transform Pivot and Orientation to Cursor, when drag-snapping", default=False, update=update_set_transform)
    transform_cursor_default_drag_snap_set_transform_machin3tools: BoolProperty(name="Only when invoked from MACHIN3tools' Cursor Pie", description="Only set the Transform Pivot and Orientation to Cursor when invoked from the MACHIN3tools Cursor Pie, while Addon's Transform Preset preference is enabled too.", default=False, update=update_set_transform)
    point_cursor_default_set_transform_orientation: BoolProperty(name="Set Transform Orientation to Cursor when pointing the Cursor", default=False)
    add_cube_store_cursor: BoolProperty(name="Store the Cursor when creat a Cube", default=False)
    add_cylinder_store_cursor: BoolProperty(name="Store the Cursor when adding a Cylinder", default=True)
    add_asset_store_cursor: BoolProperty(name="Store the Cursor when adding a Asset", default=False)
    boolean_method_difference: BoolProperty(name="Boolean Method: Difference", description="Expose Boolean Difference Operation", default=True, update=update_boolean_method)
    boolean_method_union: BoolProperty(name="Boolean Method: Union", description="Expose Boolean Union Operation", default=True, update=update_boolean_method)
    boolean_method_intersect: BoolProperty(name="Boolean Method: Intersect", description="Expose Boolean Intersect Operation", default=True, update=update_boolean_method)
    boolean_method_split: BoolProperty(name="Boolean Method: Split", description="Expose Boolean Split Operation", default=True, update=update_boolean_method)
    boolean_method_gap: BoolProperty(name="Boolean Method: Gap", description="Expose Boolean Gap Operation", default=True, update=update_boolean_method)
    boolean_method_meshcut: BoolProperty(name="Boolean Method: MeshCut", description="Expose Boolean MeshCut Operation", default=True, update=update_boolean_method)
    boolean_ray_vis_hide_cutters: BoolProperty(name="Hide Boolean Objects using Ray Visibility Properties", description="If this is disabled, Boolean Objects such as those created by HyperCursor or HyperBevel, may still appear when Viewport Rendering with Cycles, despite being hidden from Rendering", default=True)
    hyperbevel_geometry_mode_switch: BoolProperty(name="Simplify and recreate HyperBevel geometry, when switching between Edit and Object modes", default=True)
    avoid_all_toggling_autosmooth: BoolProperty(name="Avoid all-toggling AutoSmooth in HyperMod", default=True)
    hide_pick_object_tree: BoolProperty(name="Hide Wire Object Children, when invoking Pick Object Tree", default=True)
    hide_wire_collection_sort: BoolProperty(name="Sort Wire Object into dedicated Collection", default=True)
    blendulate_segment_count: IntProperty(name="Blendulate default Segment Count", description="Use this many Segments, when invoking Blendulate with a single Point selection", default=6, min=0)

    cast_flick_distance: IntProperty(name="Flick Distance", description="Flick Distance used by Boolean and Cursor Cast tools", default=75, min=20, max=1000)
    show_sidebar_panel: BoolProperty(name="Show Sidebar Panel", default=True)
    show_mod_panel: BoolProperty(name="Show HyperCursor Modifier Buttons in Blender's Modifier Panel", default=True)

    modal_hud_scale: FloatProperty(name="HUD Scale", default=1, min=0.5, max=10)
    modal_hud_timeout: FloatProperty(name="HUD Timeout", default=1, min=0.1, max=10)
    modal_hud_shadow: BoolProperty(name="HUD Shadow", description="HUD Shadow", default=False)
    modal_hud_shadow_blur: EnumProperty(name="HUD Shadow Blur", items=hud_shadow_items, default='3')
    modal_hud_shadow_offset: IntProperty(name="HUD Shadow Offset", default=1, min=0)

    preferred_default_catalog: StringProperty(name="Preferred Default Catalog", default="Insets")
    preferred_default_catalog_curve: StringProperty(name="Preferred Default Catalog for Curves", default="Profiles (Bevel)")

    geometry_gizmos_scale: FloatProperty(name="Global Geometry Gizmos Scale", default=1, min=0.5, max=10)
    show_generic_gizmo_details: BoolProperty(name="Show Generic Gizmo Keymap Details", default=False)
    show_hypermod_gizmo: BoolProperty(name="Show HyperMod Gizmo", default=True)
    show_machin3tools_mirror_gizmo: BoolProperty(name="Show MACHIN3tools Mirror Gizmo", default=False)
    show_meshmachine_symmetrize_gizmo: BoolProperty(name="Show MESHmachine Symmetrize Gizmo", default=True)

    show_world_mode: BoolProperty(name="Show World Mode", description="Show World Mode Toggle", default=True)
    show_hints: BoolProperty(name="Show Hints", description="Show Hint when Gizmo is disabled or when in Pipe Mode", default=True)
    show_help: BoolProperty(name="Show Help", description="Show Help Menu Button", default=True)
    show_update_available: BoolProperty(name="Show Update Available", description="Show Update Available", default=True)

    update_available: BoolProperty(name="Update is available", default=False)

    def update_show_update(self, context):
        if self.show_update:
            get_update_files(force=True)

    show_update: BoolProperty(default=False, update=update_show_update)
    avoid_update: BoolProperty(default=False)
    tabs: EnumProperty(name="Tabs", items=prefs_tab_items, default="SETTINGS")
    fold_addon: BoolProperty(name="Fold Addon Settings", default=False)
    fold_addon_defaults: BoolProperty(name="Fold Addon Defaults Settings", default=True)
    fold_interface: BoolProperty(name="Fold Interface Settings", default=False)
    fold_interface_tool_header: BoolProperty(name="Fold Interface Tool Header Settings", default=True)
    fold_interface_HUD: BoolProperty(name="Fold Interface HUD Settings", default=True)
    fold_interface_gizmos: BoolProperty(name="Fold Interface Gizmos Settings", default=False)
    fold_assets: BoolProperty(name="Fold Asset Settings", default=False)
    fold_assets_import: BoolProperty(name="Fold Asset Import Settings", default=True)
    fold_assets_creation: BoolProperty(name="Fold Asset Creation Settings", default=True)
    fold_keymaps_tool: BoolProperty(name="Fold Tool Keymaps", default=False)
    fold_keymaps_toolbar: BoolProperty(name="Fold Toolbar Keymaps", default=False)
    fold_object_mode_tool_keymaps: BoolProperty(name="Fold Object Mode Tool Keymaps", default=False)
    fold_edit_mode_tool_keymaps: BoolProperty(name="Fold Object Mode Tool Keymaps", default=False)
    fold_keymaps_tool_object_1: BoolProperty(name="Fold Keymaps", default=True)
    fold_keymaps_tool_object_4: BoolProperty(name="Fold Keymaps", default=False)
    fold_keymaps_tool_object_9: BoolProperty(name="Fold Keymaps", default=True)
    fold_keymaps_tool_object_11: BoolProperty(name="Fold Keymaps", default=True)
    fold_keymaps_tool_object_13: BoolProperty(name="Fold Keymaps", default=True)
    fold_keymaps_tool_object_17: BoolProperty(name="Fold Keymaps", default=True)
    fold_keymaps_tool_object_18: BoolProperty(name="Fold Keymaps", default=True)
    fold_keymaps_tool_object_21: BoolProperty(name="Fold Keymaps", default=True)
    fold_keymaps_tool_object_26: BoolProperty(name="Fold Keymaps", default=True)
    fold_keymaps_tool_object_28: BoolProperty(name="Fold Keymaps", default=True)
    fold_keymaps_tool_edit_mesh_1: BoolProperty(name="Fold Keymaps", default=True)
    fold_keymaps_tool_edit_mesh_4: BoolProperty(name="Fold Keymaps", default=True)
    fold_keymaps_tool_edit_mesh_6: BoolProperty(name="Fold Keymaps", default=True)
    fold_keymaps_tool_edit_mesh_8: BoolProperty(name="Fold Keymaps", default=True)
    fold_keymaps_tool_edit_mesh_10: BoolProperty(name="Fold Keymaps", default=True)
    fold_keymaps_tool_edit_mesh_14: BoolProperty(name="Fold Keymaps", default=True)
    def draw(self, context):
        layout = self.layout

        wm = context.window_manager
        kc = wm.keyconfigs.user

        self.draw_update(layout)

        self.draw_support(layout)

        column = layout.column()

        column.separator()

        row = column.row(align=True)
        row.prop(self, 'tabs', expand=True)

        if self.tabs == 'SETTINGS':

            panel = ui.get_panel_fold(column, idname='fold_addon', text='Addon', align=False, default_closed=False)
            if panel:
                box = panel.box()
                col = box.column(align=True)

                self.draw_addon(col)

                sub_panel = ui.get_panel_fold(col, idname='fold_addon_defaults', text='Tool Defaults', align=False, default_closed=True)
                if sub_panel:
                    sub_box = sub_panel.box()
                    sub_col = sub_box.column(align=True)

                    self.draw_tool_defaults(kc, sub_col)

            panel = ui.get_panel_fold(column, idname='fold_interface', text='Interface', align=False, default_closed=False)
            if panel:
                box = panel.box()
                col = box.column(align=True)

                self.draw_properties_panel(col)

                sub_panel = ui.get_panel_fold(col, idname='fold_interface_tool_header', text='Tool Header', align=False, default_closed=True)
                if sub_panel:
                    sub_box = sub_panel.box()
                    sub_col = sub_box.column(align=True)

                    self.draw_tool_header(sub_col)

                sub_panel = ui.get_panel_fold(col, idname='fold_interface_HUD', text='HUD', align=False, default_closed=True)
                if sub_panel:
                    sub_box = sub_panel.box()
                    sub_col = sub_box.column(align=True)

                    self.draw_HUD(sub_col)

                sub_panel = ui.get_panel_fold(col, idname='fold_interface_gizmos', text='Gizmos', align=False, default_closed=False)
                if sub_panel:
                    sub_box = sub_panel.box()
                    sub_col = sub_box.column(align=True)

                    self.draw_gizmos(sub_col, kc)

            panel = ui.get_panel_fold(column, idname='fold_assets', text='Assets', align=False, default_closed=False)
            if panel:
                box = panel.box()
                col = box.column(align=True)

                sub_panel = ui.get_panel_fold(col, idname='fold_assets_examples', text='Example Assets', align=False, default_closed=False)
                if sub_panel:
                    sub_box = sub_panel.box()
                    sub_col = sub_box.column(align=True)

                    self.draw_example_assets(context, sub_col)

                sub_panel = ui.get_panel_fold(col, idname='fold_interface_asset_creation', text='Asset Creation', align=False, default_closed=True)
                if sub_panel:
                    sub_box = sub_panel.box()
                    sub_col = sub_box.column(align=True)

                    self.draw_asset_creation(sub_col)

        elif self.tabs == 'KEYMAPS':

            km = kc.keymaps.get('3D View')

            if km:
                place_cursor_kmi = ui.get_keymap_item('3D View', 'view3d.cursor3d')

                if place_cursor_kmi:
                    panel = ui.get_panel_fold(column, idname='fold_keymaps_native', text='Blender Native Keymaps', align=False, default_closed=False)
                    if panel:
                        self.draw_place_cursor_keymap(kc, km, place_cursor_kmi, panel)

            panel = ui.get_panel_fold(column, idname='fold_keymaps_tool', text='HyperCursor Tool Keymaps', align=False, default_closed=False)
            if panel:
                box = panel.box()
                col = box.column(align=True)

                self.draw_tool_keymaps(col, kc)

            panel = ui.get_panel_fold(column, idname='fold_keymaps_outside', text='Regular Keymaps (Outside the HyperCursor Tool)', align=False, default_closed=True)
            if panel:
                box = panel.box()
                col = box.column(align=True)

                self.draw_regular_keymaps(col, kc)

            panel = ui.get_panel_fold(column, idname='fold_keymaps_toolbar', text='Toolbar Popup Keymaps', align=False, default_closed=True)
            if panel:
                box = panel.box()
                col = box.column(align=True)

                self.draw_toolbar_keymaps(col, kc)

            self.draw_keymap_reset(context, column, kc)

    def draw_update(self, layout):

        if self.update_available:
            layout.separator(factor=1)

            row = layout.row()
            row.scale_y = 1.2
            row.alignment = "CENTER"
            row.label(text="An Update is Available", icon_value=ui.get_icon("refresh_green"))
            row.operator("wm.url_open", text="What's new?").url = f"https://machin3.io/{bl_info['name']}/docs/whatsnew"

            layout.separator(factor=1)

        row = layout.row()
        row.scale_y = 1.25
        row.prop(self, 'show_update', text="Install HyperCursor Update", icon='TRIA_DOWN' if self.show_update else 'TRIA_RIGHT')

        if self.show_update:
            update_files = get_update_files()

            box = layout.box()
            box.separator()

            if self.update_msg:
                row = box.row()
                row.scale_y = 1.5

                split = row.split(factor=0.4, align=True)
                split.label(text=self.update_msg, icon_value=ui.get_icon('refresh_green'))

                s = split.split(factor=0.3, align=True)
                s.operator('machin3.remove_hypercursor_update', text='Remove Update', icon='CANCEL')
                s.operator('wm.quit_blender', text='Quit Blender + Install Update', icon='FILE_REFRESH')

            else:
                b = box.box()
                col = b.column(align=True)

                row = col.row()
                row.alignment = 'LEFT'

                if update_files:
                    row.label(text="Found the following Updates in your home and/or Downloads folder: ")
                    row.operator('machin3.rescan_hypercursor_updates', text="Re-Scan", icon='FILE_REFRESH')

                    col.separator()

                    for path, tail, _ in update_files:
                        row = col.row()
                        row.alignment = 'LEFT'

                        r = row.row()
                        r.active = False

                        r.alignment = 'LEFT'
                        r.label(text="found")

                        op = row.operator('machin3.use_hypercursor_update', text=f"HyperCursor {tail}")
                        op.path = path
                        op.tail = tail

                        r = row.row()
                        r.active = False
                        r.alignment = 'LEFT'
                        r.label(text=path)

                else:
                    row.label(text="No Update was found. Neither in your Home directory, nor in your Downloads folder.")
                    row.operator('machin3.rescan_hypercursor_updates', text="Re-Scan", icon='FILE_REFRESH')

                row = box.row()

                split = row.split(factor=0.4, align=True)
                split.prop(self, 'update_path', text='')

                text = "Select HyperCursor_x.x.x.zip file"

                if update_files:
                    if len(update_files) > 1:
                        text += " or pick one from above"

                    else:
                        text += " or pick the one above"

                split.label(text=text)

            box.separator()

    def draw_support(self, layout):
        box = layout.box()
        row = box.row()
        row.label(text="Support")
        r = row.row()
        r.alignment = 'RIGHT'
        r.label(text="", icon='INFO')
        r = row.row()
        r.alignment = 'RIGHT'
        r.active = False
        r.label(text="Click this Support Button and send me the files it creates, if you ever need Product Support")

        column = box.column()
        row = column.row()
        row.scale_y = 1.5
        row.alert = True
        row.operator('machin3.get_hypercursor_support', text='Get Support', icon='GREASEPENCIL')

    def draw_addon(self, layout):
        column = layout.column(align=True)

        draw_split_row(self, column, prop='registration_debug', label='Print Addon Registration Output in System Console')
        draw_split_row(self, column, 'show_sidebar_panel', label='Show Addon Sidebar Panel in 3D View', factor=0.202, info="Under the MACHIN3 tab!")

    def draw_tool_defaults(self, kc, layout):

        panel = ui.get_panel_fold(layout, idname='fold_addon_defaults_tool_transform_cursor', text='Transform Cursor', align=True, default_closed=True)
        if panel:
            from . import HyperCursorManager as HC

            draw_split_row(self, panel, 'transform_cursor_default_show_absolute_coords', label='Show Absolute Coords')
            panel.separator()
            draw_split_row(self, panel, 'transform_cursor_default_always_drag_snap', label='Always Snap when Dragging')
            draw_split_row(self, panel, 'transform_cursor_default_drag_snap_set_transform', label='Set Transform Pivot and Orientation to CURSOR when drag snapping')
            if HC.get_addon('MACHIN3tools') and getattr(bpy.types, "MACHIN3_OT_cursor_to_selected"):
                draw_split_row(self, panel, 'transform_cursor_default_drag_snap_set_transform_machin3tools', label="Set Transform Pivot and Orientation to CURSOR when drag snapping, but only when invoked from MACHIN3tools's Cursor and Origin pie")

        panel = ui.get_panel_fold(layout, idname='fold_addon_defaults_tool_point_cursor', text='Point Cursor', align=True, default_closed=True)
        if panel:
            draw_split_row(self, panel, 'point_cursor_default_set_transform_orientation', label='Set Transform Orientation to CURSOR')

        panel = ui.get_panel_fold(layout, idname='fold_addon_defaults_tool_add_object', text='Add Object at Cursor', align=True, default_closed=True)
        if panel:
            split = panel.split(factor=0.2, align=True)

            row = split.row(align=True)
            row.prop(self, 'add_cube_store_cursor', text='Cube', toggle=True)
            row.prop(self, 'add_cylinder_store_cursor', text='Cylinder', toggle=True)
            row.prop(self, 'add_asset_store_cursor', text='Asset', toggle=True)

            row = split.row(align=True)
            row.label(text="Automatically store Cursor in History when adding Object")

        panel = ui.get_panel_fold(layout, idname='fold_addon_defaults_tool_boolean', text='Boolean', align=True, default_closed=True)
        if panel:
            split = panel.split(factor=0.2, align=True)
            row = split.row(align=True)
            row.prop(self, 'boolean_method_difference', text='Difference', toggle=True)
            row.prop(self, 'boolean_method_union', text='Union', toggle=True)
            row.prop(self, 'boolean_method_split', text='Split', toggle=True)

            row = split.row(align=True)
            row.label(text="Boolean Methods")

            split = panel.split(factor=0.2, align=True)
            row = split.row(align=True)
            row.prop(self, 'boolean_method_intersect', text='Intersect', toggle=True)
            row.prop(self, 'boolean_method_gap', text='Gap', toggle=True)
            row.prop(self, 'boolean_method_meshcut', text='MeshCut', toggle=True)

            row = split.row(align=True)
            row.label(text="Disabled options, won't be available in the Boolean tool")

            panel.separator()

            draw_split_row(self, panel, 'boolean_ray_vis_hide_cutters', label='Hide Boolean Operand Objects for Viewport Rendering using Cycles Ray Visibility properties')

        panel = ui.get_panel_fold(layout, idname='fold_addon_defaults_tool_hyper_cut', text='Hyper Cut', align=True, default_closed=True)
        if panel:
            kmi = ui.get_keymap_item('Object Mode', 'machin3.hyper_cut')

            if kmi:
                draw_split_row(kmi, panel, prop='active', text='Enabled' if kmi.active else 'Disabled', label="Activate HyperCut's 'Outside' Keymap Item")

                if kmi.active:
                    km = kc.keymaps.get('Object Mode')

                    if km:
                        ui.draw_keymap_item(panel, kc, km, kmi)

        panel = ui.get_panel_fold(layout, idname='fold_addon_defaults_tool_hyper_bevel', text='Hyper Bevel', align=True, default_closed=True)
        if panel:
            draw_split_row(self, panel, 'hyperbevel_geometry_mode_switch', label='Simplify and recreate HyperBevel geometry, when switching between Edit and Object modes')

            kmi = ui.get_keymap_item('Object Mode', 'machin3.hyper_bevel')

            if kmi:
                draw_split_row(kmi, panel, prop='active', text='Enabled' if kmi.active else 'Disabled', label="Activate HyperBevel's 'Outside' Keymap Item")

                if kmi.active:
                    km = kc.keymaps.get('Object Mode')

                    if km:
                        ui.draw_keymap_item(panel, kc, km, kmi)

            kmi = ui.get_keymap_item('Object Mode', 'machin3.pick_hyper_bevel')

            if kmi:
                draw_split_row(kmi, panel, prop='active', text='Enabled' if kmi.active else 'Disabled', label="Activate PickHyperBevel's 'Outside' Keymap Item")

                if kmi.active:
                    km = kc.keymaps.get('Object Mode')

                    if km:
                        ui.draw_keymap_item(panel, kc, km, kmi)

        panel = ui.get_panel_fold(layout, idname='fold_addon_defaults_tool_hyper_bend', text='Hyper Bend', align=True, default_closed=True)
        if panel:
            kmi = ui.get_keymap_item('Object Mode', 'machin3.hyper_bend')

            if kmi:
                draw_split_row(kmi, panel, prop='active', text='Enabled' if kmi.active else 'Disabled', label="Activate HyperBend's 'Outside' Keymap Item")

                if kmi.active:
                    km = kc.keymaps.get('Object Mode')

                    if km:
                        ui.draw_keymap_item(panel, kc, km, kmi)

        panel = ui.get_panel_fold(layout, idname='fold_addon_defaults_tool_hyper_mod', text='Hyper Mod', align=True, default_closed=True)
        if panel:
            draw_split_row(self, panel, 'avoid_all_toggling_autosmooth', label='In HyperMod, avoid toggling AutoSmooth mod, when toggling all mods via A key')

        panel = ui.get_panel_fold(layout, idname='fold_addon_defaults_tool_pick_object_tree', text='Pick Object Tree', align=True, default_closed=True)
        if panel:
            draw_split_row(self, panel, 'hide_pick_object_tree', label='Hide Wire Objects in Tree of Active Object, when invoking PickObjectTree tool')

            kmi = ui.get_keymap_item('Object Mode', 'machin3.pick_object_tree')

            if kmi:
                draw_split_row(kmi, panel, prop='active', text='Enabled' if kmi.active else 'Disabled', label="Activate PickObjectTree's 'Outside' Keymap Item")

                if kmi.active:
                    km = kc.keymaps.get('Object Mode')

                    if km:
                        ui.draw_keymap_item(panel, kc, km, kmi)

        panel = ui.get_panel_fold(layout, idname='fold_addon_defaults_tool_hide_wire_objects', text='Hide Wire Objects', align=True, default_closed=True)
        if panel:
            draw_split_row(self, panel, 'hide_wire_collection_sort', label="Sort Wire Objects into '_Wires' collection, when running HideWireObjects tool")

        panel = ui.get_panel_fold(layout, idname='fold_addon_defaults_tool_blendulate', text='Blendulate', align=True, default_closed=True)
        if panel:
            draw_split_row(self, panel, 'blendulate_segment_count', label='Blendulate Default Segment Count')

    def draw_properties_panel(self, layout):
        draw_split_row(self, layout, 'show_mod_panel', label="Show HyperCursor Modifier Buttons in Blender's Modifier Panel")

    def draw_tool_header(self, layout):
        column = layout.column(align=True)

        draw_split_row(self, column, 'show_world_mode', label="Show World Mode Toggle")
        draw_split_row(self, column, 'show_hints', label="Show Hints when Gizmo is disabled or when in Pipe Mode")
        draw_split_row(self, column, 'show_help', label="Show Help Menu Button")
        draw_split_row(self, column, 'show_update_available', label="Show Update Available Note")

    def draw_HUD(self, layout):
        column = layout.column(align=True)

        draw_split_row(self, column, 'modal_hud_scale', label='Scale')
        draw_split_row(self, column, 'modal_hud_timeout', label='Timeout', factor=0.202, info='Modulate Duration of Fading HUDs')
        draw_split_row(self, column, 'modal_hud_shadow', label='Shadow')

        if self.modal_hud_shadow:
            row = column.split(factor=0.2, align=True)
            row.separator()
            s = row.split(factor=0.5)
            rs = s.row()
            rs.prop(self, "modal_hud_shadow_blur", expand=True)
            rs.label(text="Blur")
            rs.prop(self, "modal_hud_shadow_offset", text='')
            rs.label(text="Offset")

        draw_split_row(self, column, 'cast_flick_distance', label='Flick Distance')

    def draw_gizmos(self, layout, kc):
        from . import HyperCursorManager as HC

        machin3tools = HC.get_addon('MACHIN3tools')
        meshmachine = HC.get_addon('MESHmachine')

        column = layout.column(align=True)

        panel = ui.get_panel_fold(column, "generic_gizmo_keymap", text="Generic Gizmo Keymap", default_closed=False)
        if panel:
            if (km := kc.keymaps.get('Generic Gizmo')) and (generic_gizmo_kmi := ui.get_keymap_item('Generic Gizmo', 'gizmogroup.gizmo_tweak')):
                if generic_gizmo_kmi.any:
                    row = panel.row()
                    row.alignment = 'CENTER'
                    row.label(text="Generic Gizmo is properly set up to accept modifier keys", icon_value=ui.get_icon('save'))
                    panel.separator()

                if not generic_gizmo_kmi.any:
                    ui.draw_keymap_item(panel, kc, km, generic_gizmo_kmi)

                    panel.separator(factor=2)

                    box = panel.box()
                    box.alert = True
                    split = box.split()

                    col = split.column()
                    col.label(text="Blender 3.0 introduced a change, making it impossible to ALT click Gizmos by default.")
                    col.label(text="HyperCursor makes heavy use of modifier keys for gizmos, including the ALT key.")
                    col.label(text="To take advantage of all features, the Generic Gizmo Keymap has to be adjusted.")
                    col.label(text="See this commit and discussion for details about that change in Blender behavior:")

                    row = col.row(align=True)
                    row.operator('wm.url_open', text='Commit', icon='URL').url = 'https://developer.blender.org/rB83975965a797642eb0aece30c6a887061b34978d'
                    row.operator('wm.url_open', text='Discussion', icon='URL').url = 'https://developer.blender.org/T93699'

                    col = split.column()
                    col.separator(factor=2.5)
                    col.scale_y = 2
                    col.operator('machin3.setup_generic_gizmo_keymap', text='Setup Generic Gizmo', icon='EVENT_ALT')

                    panel.separator(factor=2)

            else:
                column = panel.column()
                column.alert = True

                row = column.row()
                row.alignment = 'CENTER'
                row.label(text="Blender's Generic Gizmo Keymap could not found. This should never happen.", icon_value=ui.get_icon('error'))

        panel = ui.get_panel_fold(column, "gizmo_settings", text="Gizmo Settings", default_closed=True)
        if panel:
            draw_split_row(self, panel, 'geometry_gizmos_scale', label='Global Geometry Gizmos Scale')

            panel.separator()
            draw_split_row(self, panel, 'show_hypermod_gizmo', label="Show HyperMod Object Gizmo", factor=0.202, info="It can alternatively be invoked purely via Keymaps too")

            if meshmachine:
                draw_split_row(self, panel, 'show_meshmachine_symmetrize_gizmo', label="Show MESHmachine Symmetrize Object Gizmo", factor=0.202, info="Allows for Mesh Symmetrizing from Object Mode!")

            if machin3tools:
                draw_split_row(self, panel, 'show_machin3tools_mirror_gizmo', label="Show MACHIN3tools Mirror Object Gizmo", factor=0.202, info="Usually it's called via Keymap, so I prefer having this disabled")

    def draw_example_assets(self, context, layout):
        column = layout.column(align=True)

        asset_path = os.path.join(self.path, 'assets')
        asset_libraries = [data.path for data in context.preferences.filepaths.asset_libraries.values()]

        if asset_path in asset_libraries:

            row = column.row()
            row.alignment = 'CENTER'
            row.label(text="HyperCursor Example Assets are ready to use!", icon_value=ui.get_icon('save'))

            if context.preferences.is_dirty and not context.preferences.use_preferences_save:
                row = column.row()
                row.alignment = 'CENTER'
                row.label(text="Save your preferences!", icon='INFO')

        else:
            split = column.split()

            col = split.column()
            col.label(text="HyperCursor supplies a few Example Assets, such as Insets and Profiles for Bevels and Pipes.")
            col.label(text="To use them, add their location (in the HyperCursor's addon folder) to your list of libraries.")

            col = split.column()
            col.scale_y = 2
            col.operator('machin3.add_hyper_cursor_assets_path', text='Add HyperCursor Example Assts to Library', icon='MONKEY')

    def draw_asset_creation(self, layout):
        column = layout.column(align=True)

        draw_split_row(self, column, 'preferred_default_catalog', label="Preferred Default Catalog", info="must exist already")
        draw_split_row(self, column, 'preferred_default_catalog_curve', label="Preferred Default Catalog for Curves", info="👆")

    def draw_place_cursor_keymap(self, kc, km, place_cursor_kmi, layout):
        ui.draw_keymap_item(layout, kc, km, place_cursor_kmi)

        point_object_mode_kmi = ui.get_keymap_item('3D View Tool: Object, Hyper Cursor', 'machin3.point_cursor')
        point_edit_mode_kmi = ui.get_keymap_item('3D View Tool: Edit Mesh, Hyper Cursor', 'machin3.point_cursor')

        if (point_object_mode_kmi and point_object_mode_kmi.compare(place_cursor_kmi)) or (point_edit_mode_kmi and point_edit_mode_kmi.compare(place_cursor_kmi)):
            box = layout.box()

            column = box.column(align=True)
            row = column.row(align=True)
            r = row.row()
            r.alert = True
            r.label(text="Point Cursor Conflict", icon="ERROR")

            r = row.row()
            r.alignment = 'RIGHT'
            r.label(text="The Blender native 'Set Cursor' Keymap right now conflicts with HyperCursor's 'Point Cursor' Keymap(s). Use a different mod key for either one.", icon='INFO')

            column = box.column(align=True)

            if point_object_mode_kmi and point_object_mode_kmi.compare(place_cursor_kmi):
                ui.draw_keymap_item(column, kc, km, point_object_mode_kmi)

            if point_edit_mode_kmi and point_edit_mode_kmi.compare(place_cursor_kmi):
                ui.draw_keymap_item(column, kc, km, point_edit_mode_kmi)

        transform_object_mode_kmi = ui.get_keymap_item('3D View Tool: Object, Hyper Cursor', 'machin3.transform_cursor')
        transform_edit_mode_kmi = ui.get_keymap_item('3D View Tool: Edit Mesh, Hyper Cursor', 'machin3.transform_cursor')

        if (transform_object_mode_kmi and transform_object_mode_kmi.compare(place_cursor_kmi)) or (transform_edit_mode_kmi and transform_edit_mode_kmi.compare(place_cursor_kmi)):
            box = layout.box()

            column = box.column(align=True)
            row = column.row(align=True)
            r = row.row()
            r.alert = True
            r.label(text="Transform Cursor Conflict", icon="ERROR")

            r = row.row()
            r.alignment = 'RIGHT'
            r.label(text="The Blender native 'Set Cursor' Keymap right now conflicts with HyperCursor's 'Transform Cursor' Keymap(s). Use a different mod key for either one.", icon='INFO')

            column = box.column(align=True)

            if transform_object_mode_kmi and transform_object_mode_kmi.compare(place_cursor_kmi):
                ui.draw_keymap_item(column, kc, km, transform_object_mode_kmi)

            if transform_edit_mode_kmi and transform_edit_mode_kmi.compare(place_cursor_kmi):
                ui.draw_keymap_item(column, kc, km, transform_edit_mode_kmi)

    def draw_tool_keymaps(self, layout, kc):
        column = layout.column(align=True)

        column.separator(factor=2)
        row = column.row()
        row.alignment = 'CENTER'
        row.label(text="Tool Keymaps only work, when the HyperCursor Tool is active!", icon='INFO')
        column.separator(factor=2)

        for keymap in tool_keymaps:
            km = kc.keymaps.get(keymap)
            prop, mode, mode_pretty = ('fold_object_mode_tool_keymaps', 'OBJECT', 'Object Mode') if keymap == '3D View Tool: Object, Hyper Cursor' else ('fold_edit_mode_tool_keymaps', 'EDIT_MESH', 'Edit Mesh Mode') if '3D View Tool: Edit Mesh, Hyper Cursor' else None

            if km and prop:
                panel = ui.get_panel_fold(layout, idname=prop, text=mode_pretty, align=False, default_closed=False)
                if panel:
                    box = panel.box()
                    col = box.column(align=True)

                    sub_panel = None

                    for kmi in reversed(km.keymap_items):

                        if text := keymap_folds[mode].get(kmi.id, None):
                            sub_panel = ui.get_panel_fold(col, idname=f"fold_keymaps_tool_{mode.lower()}_{kmi.id}", text=text, align=True, default_closed=not (kmi.id == 4 and mode == 'OBJECT'))
                        if sub_panel:
                            ui.draw_keymap_item(sub_panel, kc, km, kmi)

    def draw_regular_keymaps(self, layout, kc):
        column = layout.column(align=True)

        column.separator(factor=2)
        row = column.row()
        row.alignment = 'CENTER'
        row.label(text="These Keymaps work even when the HyperCursor Tool is not active, but are all disabled by default!", icon='INFO')
        column.separator(factor=2)

        names = {'CUT': 'Hyper Cut',
                 'BEVEL': 'Hyper Bevel',
                 'BEND': 'Hyper Bend',
                 'OBJECT': 'Pick Object Tree'}

        for keylist_name in ['CUT', 'BEVEL', 'BEND', 'OBJECT']:
            keylist = keysdict[keylist_name]

            panel = ui.get_panel_fold(column, idname=f"fold_{names[keylist_name].lower().replace(' ', '_')}", text=names[keylist_name], align=True, default_closed=True)
            if panel:
                ui.draw_keymap_items(kc, "", keylist, panel)

    def draw_toolbar_keymaps(self, layout, kc):
        column = layout.column(align=True)
        keylist = keysdict['TOOLBAR']

        column.separator(factor=2)
        row = column.row()
        row.alignment = 'CENTER'
        row.label(text="Toolbar Popup Keymaps only work, with the Toolbar Popup open!", icon='INFO')
        column.separator(factor=2)

        ui.draw_keymap_items(kc, "", keylist, column)

    def draw_keymap_reset(self, context, layout, kc):
        modified_kmis, missing_kmis = ui.get_modified_keymap_items(context)

        if modified_kmis or missing_kmis:
            column = layout.column(align=True)
            row = column.row(align=True)
            row.scale_y = 1.5
            row.alert = True

            if modified_kmis:
                row.operator('machin3.reset_hyper_cursor_keymaps', text='Reset Keymaps to Default')

            if missing_kmis:
                row.operator('machin3.restore_hyper_cursor_keymaps', text='Add Missing Keymaps')
