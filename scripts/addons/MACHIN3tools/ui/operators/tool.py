import bpy
from bpy.props import BoolProperty, FloatProperty, FloatVectorProperty, StringProperty, IntProperty

from mathutils import Matrix, Vector

import os

from ... utils.collection import get_active_collection
from ... utils.draw import draw_fading_label, draw_image, draw_init, draw_label, draw_line, draw_point, draw_tris, draw_vector, get_text_dimensions
from ... utils.math import average_locations, create_rotation_matrix_from_vectors, get_loc_matrix, get_sca_matrix
from ... utils.object import is_instance_collection, parent
from ... utils.oiio import create_png_from_icon_data, read_dat_file
from ... utils.raycast import cast_scene_ray_from_mouse, get_closest
from ... utils.registration import get_path, get_prefs, get_addon_prefs
from ... utils.system import load_json, printd, save_json, abspath
from ... utils.tools import get_active_tool, get_next_switch_tool, get_tool_options, get_tools_from_context
from ... utils.ui import draw_status_item, finish_modal_handlers, finish_status, force_ui_update, get_mouse_pos, get_scale, get_zoom_factor, ignore_events, init_modal_handlers, init_status, navigation_passthrough, popup_message, scroll, scroll_up, warp_mouse
from ... utils.view import update_local_view
from ... utils.workspace import is_3dview

from ... colors import blue, green, orange, white, yellow, black
from ... items import  annotate_inputs, letters, numbers, numbers_map, special, specials_map

from ... import MACHIN3toolsManager as M3

def draw_pick_tool_status(op):
    def draw(self, context):
        layout = self.layout
        row = layout.row()

        draw_status_item(row, key='MOVE', text=f"Select Tool: {op.hover['label'] if op.hover else 'None'}")

        if op.hover:
            draw_status_item(row, key='LMB', text="Finish")

        draw_status_item(row, key='RMB', text="Cancel")

        row.separator(factor=10)

        if not op.have_pngs_loaded:
            row.label(text="loading icons...")

    return draw

class SetTool(bpy.types.Operator):
    bl_idname = "machin3.set_tool"
    bl_label = "MACHIN3: Set Tool"
    bl_description = "Set Tool"
    bl_options = {'INTERNAL'}

    switch: BoolProperty(name="Alternate between two configured tools", default=False)
    pick: BoolProperty(name="Directly invoke into modal mode switch (from Keymap)", default=False)
    name: StringProperty(name="Tool name/ID")

    icon_progress: IntProperty()

    @classmethod
    def poll(cls, context):
        return is_3dview(context)

    @classmethod
    def description(cls, context, properties):
        if properties:
            if properties.switch:
                _, label, _ = get_next_switch_tool(context)
                desc = f"Set Tool: {label}"

                if not properties.pick:
                    desc += "\n\nALT: Pick any tool"
            else:
                desc = f"Set Tool: {properties.name}"
            return desc
        return "Invalid Context"

    def draw_HUD(self, context):
        if context.area == self.area:

            for tools in self.tools.values():

                for tool in tools:
                    coords = tool['box_coords']
                    is_hover = tool['hover']
                    is_active = tool['active']
                    shading_type = context.space_data.shading.type

                    if self.show_background:
                        draw_line(coords + [coords[0]], width=2, color=black, alpha=0.25)

                        draw_tris(coords[:3] + [coords[0]] + coords[2:], color=self.HUD_bgcolor, alpha=0.9 if shading_type in ['SOLID', 'WIREFRAME'] else 0.7)

                        if is_hover:
                            draw_tris(coords[:3] + [coords[0]] + coords[2:], color=white, alpha=0.05)

                        elif is_active:
                            draw_tris(coords[:3] + [coords[0]] + coords[2:], color=self.HUD_selcolor, alpha=0.3)

                    if self.show_labels:
                        alpha = 1 if is_active else 0.6 if is_hover else 0.3
                        size = 13 if is_hover else 12
                        draw_label(context, title=tool['label'], coords=(tool['label_center'].x, tool['label_center'].y - 6), size=size, alpha=alpha)

                    if self.show_icons and tool['png_path']:
                        factor = 1.2 if is_hover else 1
                        draw_image(context, tool['png_path'], co=tool['icon_center'].resized(2), size=tool['box_height'] * factor, center=True)

            if not self.show_labels and self.hover:
                draw_label(context, title=self.hover['label'], coords=Vector((self.HUD_x, self.HUD_y)), center=False, alpha=0.75)

    def modal(self, context, event):
        if ignore_events(event):
            return {'RUNNING_MODAL'}

        context.area.tag_redraw()

        if not self.have_pngs_loaded:
            self.create_png_icons()

        if event.type in ['MOUSEMOVE']:
            get_mouse_pos(self, context, event)
            self.update_hover(context)

        elif navigation_passthrough(event, alt=True, wheel=True):
            return {'PASS_THROUGH'}

        elif event.type in ['LEFTMOUSE', 'SPACE']:
            self.finish(context)

            if self.hover:
                bpy.ops.wm.tool_set_by_id(name=self.hover['name'])

                size, color = (16, green) if 'machin3.tool_hyper_cursor' in self.hover['name'] else (12, white)
                draw_fading_label(context, text=self.hover['label'], time=get_prefs().HUD_fade_tools_pie, size=size, color=color, move_y=10)

            return {'FINISHED'}

        elif event.type in ['RIGHTMOUSE', 'ESC']:
            self.finish(context)
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def finish(self, context):
        finish_modal_handlers(self)

        finish_status(self)
        force_ui_update(context)

    def invoke(self, context, event):
        active_tool = get_active_tool(context).idname
        tools = get_tools_from_context(context)

        if active_tool == 'machin3.tool_hyper_cursor_simple':
            context.space_data.overlay.show_cursor = True

        if self.switch or self.pick:

            if event.alt or self.pick:

                self.show_icons = get_prefs().tools_pick_show_icons
                self.show_labels = get_prefs().tools_pick_show_labels
                self.show_background = get_prefs().tools_pick_show_button_background

                self.have_pngs_loaded = False

                tools = get_tools_from_context(context)

                self.tools = self.get_grouped_tools(tools)

                get_mouse_pos(self, context, event)
                self.init_mouse_pos = self.mouse_pos.copy()

                self.create_HUD_coords(context)

                if self.show_background:
                    self.HUD_bgcolor = context.preferences.themes['Default'].view_3d.space.gradients.high_gradient if context.space_data.shading.type in ['SOLID', 'WIREFRAME'] else black
                    self.HUD_selcolor = context.preferences.themes['Default'].user_interface.wcol_regular.inner_sel[:3]

                if get_prefs().tools_pick_warp_mouse:
                    active_box = [tool for tools in self.tools.values() for tool in tools if tool['active']]

                    if active_box:
                        warp_mouse(self, context, co2d=active_box[0]['box_center'].resized(2))

                else:
                    warp_mouse(self, context, co2d=self.mouse_pos)

                self.update_hover(context, init=True)

                init_status(self, context, func=draw_pick_tool_status(self))
                force_ui_update(context)
                context.area.tag_redraw()

                init_modal_handlers(self, context, hud=True)
                return {'RUNNING_MODAL'}

            else:
                name, label, _ = get_next_switch_tool(context, active_tool=active_tool, tools=tools)

        elif self.name and self.name in tools:
            name = self.name
            label = tools[name]['label']

        else:
            return {'CANCELLED'}

        bpy.ops.wm.tool_set_by_id(name=name)

        size, color = (16, green) if 'machin3.tool_hyper_cursor' in name else (12, white)
        draw_fading_label(context, text=label, time=get_prefs().HUD_fade_tools_pie, size=size, color=color, move_y=10)
        return {'FINISHED'}

    def get_grouped_tools(self, tools):
        grouped_tools = {}

        for tool in tools.values():
            if tool['idx'] in grouped_tools:
                grouped_tools[tool['idx']].append(tool)

            else:
                grouped_tools[tool['idx']] = [tool]

            tool['hover'] = False

        icons_path = os.path.join(bpy.utils.resource_path('LOCAL'), 'datafiles', 'icons')
        native_icons = [f[:-4] for f in os.listdir(icons_path) if f.endswith('.dat')]

        for tools in grouped_tools.values():
            for tool in tools:
                if tool['icon'] in native_icons:
                    tool['icon_path'] = os.path.join(icons_path, f"{tool['icon']}.dat")

                else:
                    tool['icon_path'] = f"{abspath(tool['icon'])}.dat"

                tool['png_path'] = os.path.join(get_path(), 'icons', 'tools', "loading.png")

        return grouped_tools

    def create_png_icons(self):
        for tools in self.tools.values():
            for tool in tools:

                png_path = os.path.join(get_path(), 'icons', 'tools', f"{os.path.basename(tool['icon'])}.png")

                if os.path.exists(png_path):
                    tool['png_path'] = png_path

                else:

                    icon_data = read_dat_file(tool['icon_path'])

                    if icon_data:
                        create_png_from_icon_data(icon_data, png_path)
                        print("INFO: Created", png_path)

                        tool['png_path'] = png_path

                    else:
                        print(f"WARNING: Could not fetch icon data from {tool['icon_path']}")

        self.have_pngs_loaded = True

    def create_HUD_coords(self, context, debug=False):
        def get_box_width(tool):
            if self.show_labels and (self.show_icons and tool['png_path']):
                return box_height + (gap / 4) + get_text_dimensions(context, tool['label'], size=size).x

            elif self.show_labels:
                return get_text_dimensions(context, tool['label'], size=size).x

            elif (self.show_icons and tool['png_path']):
                return box_height

            return box_height

        region_width = context.region.width
        region_height = context.region.height

        gap = 15
        size = 15

        box_height = get_text_dimensions(context, "Test", size=size).y + (gap * 2)
        total_height = len(self.tools) * box_height
        height_ratio = total_height / region_height

        factor = 0.7 / height_ratio if height_ratio > 0.7 else 1

        for idx, (group_idx, tools) in enumerate(reversed(self.tools.items())):
            if debug:
                print(idx, group_idx, [tool['name'] for tool in tools])

            start_x = 0
            start_y = idx * box_height
            center_offset_x = 0

            for tool_idx, tool in enumerate(tools):
                if debug:
                    print("", tool['label'], "<" if tool['active_within_group'] else '')

                box_width = get_box_width(tool)

                box_coords = [Vector((start_x, start_y, 0)) * factor,
                              Vector((start_x + box_width + gap * 2, start_y, 0)) * factor,
                              Vector((start_x + box_width + gap * 2, start_y + box_height, 0)) * factor,
                              Vector((start_x, start_y + box_height, 0)) * factor]

                tool['box_coords'] = box_coords

                tool['box_center'] = average_locations(box_coords)

                tool['box_height'] = box_height * factor

                if self.show_icons and self.show_labels:
                    tool['icon_center'] = Vector((start_x + gap + box_height / 2, tool['box_center'].y, 0))
                    tool['label_center'] = Vector((tool['box_center'].x + (box_height / 2), tool['box_center'].y, 0))

                else:
                    tool['icon_center'] = tool['box_center'].copy()
                    tool['label_center'] = tool['box_center'].copy()

                if tool['is_grouped']:
                    if tool['active_within_group']:
                        center_offset_x = tool['box_center'].x
                else:
                    center_offset_x = tool['box_center'].x

                start_x += box_width + gap * 2

            for tool in tools:
                for co in tool['box_coords'] + [tool['box_center'], tool['icon_center'], tool['label_center']]:
                    co -= Vector((center_offset_x, 0, 0))

        for tools in self.tools.values():
            for tool in tools:
                for co in tool['box_coords'] + [tool['box_center'], tool['icon_center'], tool['label_center']]:

                    if get_prefs().tools_pick_center_mode == 'VIEW':
                        co += Vector((region_width / 2, (region_height / 2) - ((total_height * factor) / 2), 0))

                    elif get_prefs().tools_pick_center_mode == 'MOUSE_X':
                        co += Vector((self.mouse_pos.x, (region_height / 2) - ((total_height * factor) / 2), 0))

        if debug:
            for tools in self.tools.values():

                for tool in tools:
                    coords = tool['box_coords']
                    draw_line(coords + [coords[0]], screen=True, modal=False)

                    draw_point(tool['box_center'], screen=True, modal=False)

                    draw_point(tool['icon_center'], screen=True, modal=False)

            context.area.tag_redraw()

    def update_hover(self, context, init=False):
        self.hover = None

        if init:
            self.previous_hover = None

        for tools in self.tools.values():
            for tool in tools:
                coords = tool['box_coords']

                if coords[0].x <= self.mouse_pos.x <= coords[1].x:
                    if coords[0].y <= self.mouse_pos.y <= coords[2].y:
                        tool['hover'] = True

                        self.hover = tool
                        continue

                tool['hover'] = False

        if self.previous_hover != self.hover:
            force_ui_update(bpy.context)
            self.previous_hover = self.hover

class SetBCPreset(bpy.types.Operator):
    bl_idname = "machin3.set_boxcutter_preset"
    bl_label = "MACHIN3: Set BoxCutter Preset"
    bl_description = "Quickly enable/switch BC tool in/to various modes"
    bl_options = {'REGISTER', 'UNDO'}

    mode: StringProperty()
    shape_type: StringProperty()
    set_origin: StringProperty(default='MOUSE')
    @classmethod
    def poll(cls, context):
        if M3.get_addon("BoxCutter"):
            return M3.addons['boxcutter']['foldername'] in get_tools_from_context(context)

    def execute(self, context):
        tools = get_tools_from_context(context)
        bcprefs = get_addon_prefs('BoxCutter')

        bc = M3.addons['boxcutter']['foldername']

        if not tools[bc]['active']:
            bpy.ops.wm.tool_set_by_id(name=bc)

        options = get_tool_options(context, bc, 'bc.shape_draw')

        if options:
            options.mode = self.mode
            options.shape_type = self.shape_type

            bcprefs.behavior.set_origin = self.set_origin
            bcprefs.snap.enable = True
        return {'FINISHED'}

class ToggleAnnotation(bpy.types.Operator):
    bl_idname = "machin3.toggle_annotation"
    bl_label = "MACHIN3: Toggle Annotation"
    bl_description = "Toggle Annotation Visibility"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if bpy.app.version < (4, 3, 0):
            return context.annotation_data
        else:
            note_gps = [obj for obj in context.visible_objects if obj.type == 'GREASEPENCIL' and 'Annotation' in obj.name]
            return context.annotation_data or note_gps

    def execute(self, context):

        if bpy.app.version < (4, 3, 0):
            is_visible = any(not layer.hide for layer in context.annotation_data.layers)

            if is_visible:
                self.hide_legacy_annotations(context)

            else:
                self.show_legacy_annotations(context)

        else:
            is_annotation_visible = any(not layer.annotation_hide for layer in context.annotation_data.layers) if context.annotation_data else False

            note_gps = [obj for obj in context.visible_objects if obj.type == 'GREASEPENCIL' and 'Annotation' in obj.name]
            is_gp_visible = any([not layer.hide for obj in note_gps for layer in obj.data.layers])

            is_either_visible = is_annotation_visible or is_gp_visible

            if is_either_visible:
                self.hide_annotations(context)

            else:
                self.show_annotations(context)

        return {'FINISHED'}

    def hide_annotations(self, context):
        data = context.annotation_data

        is_annotation_visible = any(not layer.annotation_hide for layer in context.annotation_data.layers) if context.annotation_data else False

        note_gps = [obj for obj in context.visible_objects if obj.type == 'GREASEPENCIL' and 'Annotation' in obj.name]
        is_gp_visible = any([not layer.hide for obj in note_gps for layer in obj.data.layers])

        if is_annotation_visible:
            vis = {}

            for layer in data.layers:
                if len(data.layers) > 1:
                    vis[layer.info] = not layer.annotation_hide

                layer.annotation_hide = True

            context.scene.M3['annotation_visibility'] = vis

        if is_gp_visible:
            for obj in note_gps:
                gpd = obj.data

                vis = {}

                for layer in gpd.layers:

                    if len(gpd.layers) > 1:
                        vis[layer.name] = not layer.hide

                    layer.hide = True

                obj.M3['annotation_visibility'] = vis

    def show_annotations(self, context, force_active=False):
        data = context.annotation_data
        note_gps = [obj for obj in context.visible_objects if obj.type == 'GREASEPENCIL' and 'Annotation' in obj.name]

        if data:
            vis = context.scene.M3.get('annotation_visibility', None)

            for layer in data.layers:
                layer.annotation_hide = not vis[layer.info] if vis and layer.info in vis else False

        if note_gps:
            for obj in note_gps:
                gpd = obj.data
                vis = obj.M3.get('annotation_visibility', None)

                for layer in gpd.layers:
                    layer.hide = not vis[layer.name] if vis and layer.name in vis else False

                if force_active and gpd.layers.active and gpd.layers.active.hide:
                    gpd.layers.active.hide = False

        if not context.space_data.overlay.show_overlays:
            context.space_data.overlay.show_overlays = True

    def hide_legacy_annotations(self, context):
        data = context.annotation_data

        vis = {}

        for layer in data.layers:
            if len(data.layers) > 1:
                vis[layer.info] = not layer.hide

            layer.hide = True

        context.scene.M3['annotation_visibility'] = vis

    def show_legacy_annotations(self, context, force_active=False):
        data = context.annotation_data

        vis = context.scene.M3.get('annotation_visibility', None)

        for layer in data.layers:
            layer.hide = not vis[layer.info] if vis and layer.info in vis else False

        if force_active and context.active_annotation_layer and context.active_annotation_layer.hide:
            context.active_annotation_layer.hide = False

        if not context.space_data.overlay.show_overlays:
            context.space_data.overlay.show_overlays = True

def draw_annotate_status(op):
    def draw(self, context):
        layout = self.layout

        row = layout.row(align=True)

        row.label(text="Annotate")

        draw_status_item(row, key='LMB', text="Finish")
        draw_status_item(row, key='RMB', text="Cancel")

        row.separator(factor=10)

        draw_status_item(row, text="Type...", gap=10)

        draw_status_item(row, text="Note", prop=op.text.replace('~', ' | '), gap=2)

        draw_status_item(row, key='MMB_SCROLL', text="Size", prop=round(op.size, 1), gap=2)

        draw_status_item(row, key='BACKSPACE', text="Clear All" if op.is_ctrl else "Backspace", gap=2)

        if not op.is_ctrl:
            draw_status_item(row, key=['SHIFT', 'RETURN'], text="New Line", gap=1)

        draw_status_item(row, active=op.is_ctrl, key='CTRL', text="Special", gap=2)

        if op.is_ctrl:
            draw_status_item(row, active=not op.screen_align, key='C', text="Cursor Align", gap=2)

            draw_status_item(row, key='W', text="Remove Last Word", gap=1)

            if bpy.app.version >= (4, 3, 0):
                draw_status_item(row, key='B', text="Blend Mode", prop=op.frame.id_data.layers.active.blend_mode.title(), gap=1)

            draw_status_item(row, key='RETURN', text="Finish", gap=1)

    return draw

class Annotate(bpy.types.Operator):
    bl_idname = "machin3.annotate"
    bl_label = "MACHIN3: Annotate"
    bl_description = "Annotate"
    bl_options = {'REGISTER', 'UNDO'}

    screen_align: BoolProperty(name="Screen Align Note", default=True)
    multiply: BoolProperty(name="Multiply", default=False)
    size: FloatProperty(name="Size", default=1, min=0.1, max=10)
    @classmethod
    def poll(cls, context):
        return context.space_data and context.space_data.type == 'VIEW_3D'

    def draw(self, context):
        layout = self.layout
        _column = layout.column(align=True)

    def draw_HUD(self, context):
        if self.area == context.area:
            draw_init(self)

            dims = draw_label(context, title="Add Note...", coords=Vector((self.HUD_x, self.HUD_y)), center=False)

            self.offset += 18

            dims = draw_label(context, title="Size: ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, alpha=0.5)
            draw_label(context, title=str(round(self.size, 1)), coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=yellow)

            if bpy.app.version >= (4, 3, 0):
                self.offset += 18

                layer = self.frame.id_data.layers.active

                dims = draw_label(context, title="Blend Mode: ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, alpha=0.5)

                color, alpha = (yellow, 1) if layer.blend_mode == 'MULTIPLY' else (white, 0.5)
                draw_label(context, title=layer.blend_mode.title(), coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=color, alpha=alpha)

            self.offset += 18

            if self.screen_align:
                draw_label(context, title="Screen Aligned", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=blue)

            else:
                draw_label(context, title="Cursor Aligned", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=green)

            self.offset += 18

            text = self.text.split('~')

            for t in text:
                self.offset += 15

                draw_label(context, title=t, coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, alpha=0.5)

    def draw_VIEW3D(self, context):
        if context.area == self.area:

            if self.is_prompt_show:
                mx = self.get_annotation_matrix(prompt=True)

                draw_vector(Vector((0.2, 1, 0)), mx=mx, width=3, color=orange if self.is_ctrl else white, alpha=0.5)

    def modal(self, context, event):
        if ignore_events(event, timer=False):
            return {'RUNNING_MODAL'}

        context.area.tag_redraw()

        self.is_ctrl = event.ctrl

        if event.type == 'TIMER':
            self.is_prompt_show = not self.is_prompt_show

        elif event.type == 'MOUSEMOVE':
            get_mouse_pos(self, context, event)

        elif scroll(event, key=False):
            if scroll_up(event, key=True):
                self.size += 0.1

            else:
                self.size -= 0.1

            self.refresh_annotation(context)

        elif event.ctrl and event.type in ['S', 'C'] and event.value == 'PRESS':
            self.screen_align = not self.screen_align

            self.refresh_annotation(context)

            force_ui_update(context)

        elif bpy.app.version >= (4, 3, 0) and event.ctrl and event.type in ['B', 'M'] and event.value == 'PRESS':
            if self.frame.id_data.layers.active.blend_mode == 'MULTIPLY':
                self.frame.id_data.layers.active.blend_mode = 'REGULAR'
                self.multiply = False
            else:
                self.frame.id_data.layers.active.blend_mode = 'MULTIPLY'
                self.multiply = True

            force_ui_update(context)

        elif event.type == "LEFTMOUSE" or (event.ctrl and event.type == 'RET'):
            self.finish(context)

            return {'FINISHED'}

        elif event.type in ['RIGHTMOUSE', 'ESC']:
            self.finish(context)

            self.remove_entire_note()
            return {'CANCELLED'}

        elif event.type in annotate_inputs and event.value == 'PRESS':

            char = self.get_char_from_event(event)

            if not char:

                if event.type == "RET":
                    self.add_line_break()

                elif event.type == 'BACK_SPACE':
                    if self.text:

                        if event.ctrl:
                            self.remove_entire_note()

                        else:
                            self.remove_last_annotation_character()

                elif event.ctrl and event.type == 'U':
                    self.remove_entire_note()

                elif event.ctrl and event.type == 'W':
                    if self.text:
                        self.remove_last_annotation_word()

            elif char in self.font:
                self.add_annotation_char(context, char)

            force_ui_update(context)

        return {'RUNNING_MODAL'}

    def finish(self, context):
        finish_modal_handlers(self)

        context.window.cursor_set('DEFAULT')

        finish_status(self)

    def invoke(self, context, event):
        fontpath = os.path.join(get_path(), "resources", "annotate", "square_italic.json")

        self.font = self.load_annotate_font(fontpath)

        if self.font:
            self.text = ""

            self.tracking = 0.06
            self.character_offset = Vector((0, 0))

            self.is_prompt_show = True

            self.is_ctrl = False

            self.loc, self.locobj = self.get_depth_location(context)

            self.factor = get_zoom_factor(context, depth_location=self.loc, scale=20 * get_scale(context), ignore_obj_scale=True)

            get_mouse_pos(self, context, event)
            context.window.cursor_set('TEXT')

            self.cmx, self.smx = self.get_alignment_matrices(context)

            self.size = 1

            self.frame = self.get_frame(context)

            init_status(self, context, func=draw_annotate_status(self))

            init_modal_handlers(self, context, hud=True, view3d=True, timer=True, time_step=0.4)
            return {'RUNNING_MODAL'}

        else:
            popup_message("Couldn't find Annotate font", title="Font not found")

        return {'CANCELLED'}

    def load_annotate_font(self, fontpath):
        if os.path.exists(fontpath):
            fontdata = load_json(fontpath)

            for letter, data in fontdata.items():
                data['strokes'] = [[Vector(co) for co in stroke] for stroke in data['strokes']]
                data['dimensions'] = Vector(data['dimensions'])

            return fontdata

    def get_depth_location(self, context):#
        pie_pos = getattr(bpy.types.MACHIN3_MT_tools_pie, "mouse_pos_region", None)
        hitlocation = None
        cache = {}

        if pie_pos:
            _, hitobj, _, hitlocation, _, _ = cast_scene_ray_from_mouse(pie_pos, depsgraph=context.evaluated_depsgraph_get(), exclude_wire=True, cache=cache, debug=False)

            if hitobj and not hitobj.users_scene:

                empty_candidates = []

                for obj in context.visible_objects:
                    if col := is_instance_collection(obj):

                        if col in hitobj.users_collection:
                            empty_candidates.append((obj, col))

                if empty_candidates:

                    if len(empty_candidates) == 1:
                        hitobj = empty_candidates[0][0]

                    else:
                        distances = []

                        for obj, col in empty_candidates:
                            loc = obj.matrix_world @ get_loc_matrix(col.instance_offset) @ hitobj.matrix_world.decompose()[0]

                            distances.append(((loc - hitlocation).length, obj))

                        hitobj = min(distances)[1]

                else:
                    print("WARNING: Could not associate hitlocation with instance collection empty")
                    print("         Nested collection instances? Get in touch with support@machin3.io if you ever see this.")
                    return context.scene.cursor.location, None

        if hitlocation:
            return hitlocation, hitobj

        else:
            return context.scene.cursor.location, None

    def get_alignment_matrices(self, context):
        viewmx = context.space_data.region_3d.view_matrix

        x_dir = Vector((1, 0, 0)) @ viewmx
        y_dir = Vector((0, 1, 0)) @ viewmx
        z_dir = Vector((0, 0, 1)) @ viewmx

        cursor_mx = get_loc_matrix(self.loc) @ context.scene.cursor.rotation_quaternion.to_matrix().to_4x4()
        screen_mx = get_loc_matrix(self.loc) @ create_rotation_matrix_from_vectors(x_dir, y_dir, z_dir)

        return cursor_mx, screen_mx

    def get_annotation_matrix(self, prompt=False):
        extra_offset = self.tracking if prompt else 0

        offsetmx = get_loc_matrix(Vector((self.character_offset.x + extra_offset, self.character_offset.y, 0)))

        if self.screen_align:

            if bpy.app.version < (4, 3, 0) or prompt:
                return self.smx @ get_sca_matrix(Vector.Fill(3, self.factor * self.size)) @ offsetmx
            else:
                return self.gpmx.inverted_safe() @ self.smx @ get_sca_matrix(Vector.Fill(3, self.factor * self.size)) @ offsetmx

        else:
            if bpy.app.version < (4, 3, 0) or prompt:
                return self.cmx @ get_sca_matrix(Vector.Fill(3, self.factor * self.size)) @ offsetmx
            else:
                return self.gpmx.inverted_safe() @ self.cmx @ get_sca_matrix(Vector.Fill(3, self.factor * self.size)) @ offsetmx

    def get_char_from_event(self, event):
        char = None

        if event.ctrl:
            return

        if event.type in letters:
            if event.shift:
                char = event.type

            else:
                char = event.type.lower()

        elif event.type in numbers:

            if event.shift and event.type == "ONE":
                char = "!"

            elif event.shift and event.type == "TWO":
                char = '"'

            elif event.shift and event.type == "THREE":
                char = "?"

            elif event.shift and event.type == "ZERO":
                char = "="

            elif event.shift and event.type == "QUOTE":
                char = "'"

            else:
                char = str(numbers_map[event.type])

        elif event.type in special:

            if event.shift and event.type == "SLASH":
                char = "?"

            elif event.shift and event.type == "PERIOD":
                char = ":"

            elif event.shift and event.type == "PLUS":
                char = "*"

            elif event.type == "LEFT_BRACKET":
                char = "("

            elif event.type == "RIGHT_BRACKET":
                char = ")"

            else:
                char = specials_map[event.type]

        return char

    def get_frame(self, context):
        if bpy.app.version < (4, 3, 0):

            if not context.active_annotation_layer:
                bpy.ops.gpencil.annotation_add()

            layer = context.active_annotation_layer

            ToggleAnnotation.show_legacy_annotations(self, context, force_active=True)

            if not layer.frames or not layer.active_frame:
                return layer.frames.new(context.scene.frame_current)

            else:
                return layer.active_frame

        else:
            active = context.active_object if context.active_object and context.active_object.select_get() else None
            mcol = context.scene.collection
            view = context.space_data

            gp = self.get_annotation_object(context, active, mcol, view)
            gpd = gp.data

            self.gpmx = gp.matrix_world

            if gp.data.layers:
                layer = gpd.layers.active
                self.multiply = layer.blend_mode == 'MULTIPLY'

            else:
                layer = gpd.layers.new(name="Note")

                layer.tint_color = Vector(gp.color).resized(3)
                layer.tint_factor = 1

                if self.multiply:
                    layer.blend_mode = 'MULTIPLY'

            ToggleAnnotation.show_annotations(self, context, force_active=True)

            if layer.current_frame():
                return layer.current_frame()

            else:
                return layer.frames.new(0)

    def add_annotation_char(self, context, char):
        mx = self.get_annotation_matrix()

        for coords in self.font[char]['strokes']:

            if bpy.app.version < (4, 3, 0):
                stroke = self.frame.strokes.new()
                stroke.points.add(len(coords))

                for point, co in zip(stroke.points, coords):
                    point.co = mx @ co.resized(3)

            else:
                drawing = self.frame.drawing
                drawing.add_strokes([len(coords)])

                stroke = drawing.strokes[-1]
                stroke.cyclic = False     # note sure if it helps, but sometimes strokes get cyclic when going into edit mode and selecting all? hard to reproruce, so setting it to False explicitely for now

                radius = 0.05 * self.factor * self.size

                for point, co in zip(stroke.points, coords):
                    point.position = mx @ co.resized(3)

                    point.radius = radius

        self.character_offset.x += self.font[char]['dimensions'].x + self.tracking

        self.text += char

    def add_line_break(self):
        self.text += "~"

        self.character_offset.x = 0
        self.character_offset.y -= 1.3

    def remove_last_annotation_character(self):
        last_char = self.text[-1]

        if last_char == '~':
            prev_line = self.text[:-1].split('~')[-1]

            self.character_offset.x = sum([self.font[char]['dimensions'].x + self.tracking for char in prev_line])
            self.character_offset.y += 1.3

        else:

            for i in range(len(self.font[last_char]['strokes'])):
                if bpy.app.version < (4, 3, 0):
                    self.frame.strokes.remove(self.frame.strokes[-1])

                else:
                    drawing = self.frame.drawing
                    idx = len(drawing.strokes) - 1          # NOTE: -1 does not work here for some reason
                    drawing.remove_strokes(indices=[idx])

            self.character_offset.x -= self.font[last_char]['dimensions'].x + self.tracking

        self.text = self.text[:-1]

    def remove_last_annotation_word(self):
        last_word = ""

        for char in reversed(self.text):
            if char == " ":

                if last_word.strip():
                    break

                else:
                    last_word += char

            elif char == '~':

                if last_word:
                    break

                else:
                    self.remove_last_annotation_character()

            else:
                last_word += char

        for char in last_word:
            self.remove_last_annotation_character()

    def remove_entire_note(self):
        strokecount = 0

        for char in self.text:

            if char == '~':
                continue

            strokecount += len(self.font[char]['strokes'])

        for i in range(strokecount):
            if bpy.app.version < (4, 3, 0):
                self.frame.strokes.remove(self.frame.strokes[-1])
            else:
                drawing = self.frame.drawing
                idx = len(drawing.strokes) - 1            # NOTE: -1 does not work here for some reason
                drawing.remove_strokes(indices=[idx])

        self.character_offset = Vector((0, 0))

        self.text = ""

    def refresh_annotation(self, context):
        text = self.text

        self.remove_entire_note()

        for char in text:

            if char == '~':
                self.add_line_break()

            else:
                self.add_annotation_char(context, char)

    def add_grease_pencil_annotation_object(self, active, col, view):
        name = f"{active.name}_Annotation" if active else "Scene_Annotation"

        gpd = bpy.data.grease_pencils_v3.new(name)
        gp = bpy.data.objects.new(name, gpd)

        gp.show_in_front = True

        gp.color = (0.12, 0.33, 0.57, 1)

        blues = [mat for mat in bpy.data.materials if mat.name == 'NoteMaterial' and mat.is_grease_pencil]
        mat = blues[0] if blues else bpy.data.materials.new(name='NoteMaterial')

        bpy.data.materials.create_gpencil_data(mat)
        gp.data.materials.append(mat)

        mat.grease_pencil.color = gp.color

        col.objects.link(gp)

        if active:

            loc, rot, _ = active.matrix_world.decompose()
            gp.matrix_world = Matrix.LocRotScale(loc, rot, Vector((1, 1, 1)))

            parent(gp, active)

        update_local_view(view, [(gp, True)])

        return gp

    def get_annotation_object(self, context, active, mcol, view):
        if self.locobj:
            active = self.locobj

        if active:

            if active.type == "GREASEPENCIL" and "_Annotation" in active.name:
                gp = active

            else:
                annotations = [obj for obj in active.children if obj.type == "GREASEPENCIL" and "_Annotation" in obj.name]

                if annotations:
                    gp = annotations[0]

                else:
                    gp = self.add_grease_pencil_annotation_object(active, mcol, view)

        else:
            annotations = [obj for obj in context.scene.objects if obj.type == "GREASEPENCIL" and "_Annotation" in obj.name and not obj.parent]

            if annotations:
                gp = annotations[0]

            else:
                gp = self.add_grease_pencil_annotation_object(None, mcol, view)

        return gp

class PrepareAnnotateFont(bpy.types.Operator):
    bl_idname = "machin3.prepare_annotate_font"
    bl_label = "MACHIN3: Prepare Annotate Font"
    bl_description = "Prepare Annotate Font from imported svg letter set"
    bl_options = {'REGISTER', 'UNDO'}

    origin_offset: FloatVectorProperty(name="Origin Offset", default=Vector((-0.137, -1.318, 0)), step=0.1)
    scale_offset: FloatProperty(name="Scale Offset", default=47, step=0.1)
    tracking: FloatProperty(name="Tracking", default=0.06, step=0.1)
    @classmethod
    def poll(cls, context):
        return False

    def draw(self, context):
        layout = self.layout
        column = layout.column(align=True)

        row = column.row()
        row.prop(self, "origin_offset", text="")

        row = column.row()
        row.prop(self, "scale_offset")

        row = column.row()
        row.prop(self, "tracking")

    def execute(self, context):
        dg = context.evaluated_depsgraph_get()
        col = get_active_collection(context)

        if col:

            bpy.ops.object.select_all(action='DESELECT')

            for idx, obj in enumerate(col.objects):
                if obj.type != 'MESH':
                    obj.select_set(True)

                if idx:
                    obj.matrix_world = col.objects[0].matrix_world

            if context.selected_objects:
                bpy.ops.object.convert(target='MESH')
                bpy.ops.object.convert(target='CURVE')

            for obj in col.objects:
                obj.data.transform(get_loc_matrix(self.origin_offset) @ get_sca_matrix(Vector((self.scale_offset, self.scale_offset, self.scale_offset))))

            dg.update()

            offset_x = 0

            for obj in col.objects:
                obj.location.x += offset_x
                offset_x += obj.dimensions.x + self.tracking

        else:
            popup_message("Ensure there is an active collection containing a set of importeded svg letter objects", title="Select a Collection")

        return {'FINISHED'}

class CreateAnnotateFont(bpy.types.Operator):
    bl_idname = "machin3.create_annotate_font"
    bl_label = "MACHIN3: Create Annotate Font"
    bl_description = "Create Annotate Font from prepared mesh letter set"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return False

    def draw(self, context):
        layout = self.layout
        _column = layout.column(align=True)

    def execute(self, context):
        col = get_active_collection(context)

        letter_dict = {}

        if col:

            bpy.ops.object.select_all(action='DESELECT')

            for idx, obj in enumerate(col.objects):
                if obj.type == 'CURVE' and all(spline.type == 'POLY' for spline in obj.data.splines):
                    print("found letter:", obj.name)

                    obj.select_set(True)

                    letter_dict[obj.name] = {'strokes': [[(point.co.x, point.co.y) for point in spline.points] for spline in obj.data.splines],
                                             'dimensions': (obj.dimensions.x, obj.dimensions.y)}

            printd(letter_dict)

            path = bpy.data.filepath.replace('.blend', '.json')
            save_json(letter_dict, path)

            print("saved to:", path)
        else:
            popup_message("Ensure there is an active collection containing a set of importeded svg letter objects", title="Select a Collection")

        return {'FINISHED'}

class SurfaceDraw(bpy.types.Operator):
    bl_idname = "machin3.surface_draw"
    bl_label = "MACHIN3: Surface Draw"
    bl_description = "Surface Draw, create parented, empty GreasePencil object and enter DRAW mode.\nSHIFT: Select the Line tool."
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT" and context.active_object

    def invoke(self, context, event):
        bpy.ops.object.mode_set(mode='OBJECT')

        scene = context.scene
        ts = scene.tool_settings
        mcol = context.scene.collection
        view = context.space_data
        active = context.active_object

        existing_gps = [obj for obj in active.children if obj.type == ("GPENCIL" if bpy.app.version < (4, 3, 0) else "GREASEPENCIL") and "_SurfaceDrawing" in obj.name]

        if existing_gps:
            gp = existing_gps[0]

        else:
            name = f"{active.name}_SurfaceDrawing"
            gpd = bpy.data.grease_pencils.new(name) if bpy.app.version < (4, 3, 0) else bpy.data.grease_pencils_v3.new(name)
            gp = bpy.data.objects.new(name, gpd)

            mcol.objects.link(gp)

            gp.matrix_world = active.matrix_world
            parent(gp, active)

        update_local_view(view, [(gp, True)])

        layer = gp.data.layers.new(name="SurfaceLayer")
        layer.blend_mode = 'MULTIPLY'

        if not layer.frames:
            layer.frames.new(0)

        context.view_layer.objects.active = gp
        active.select_set(False)
        gp.select_set(True)

        gp.color = (0, 0, 0, 1)

        blacks = [mat for mat in bpy.data.materials if mat.name == 'Black' and mat.is_grease_pencil]
        mat = blacks[0] if blacks else bpy.data.materials.new(name='Black')

        bpy.data.materials.create_gpencil_data(mat)
        gp.data.materials.append(mat)

        ts.gpencil_stroke_placement_view3d = 'SURFACE'

        if not view.show_region_toolbar:
            view.show_region_toolbar = True

        if bpy.app.version < (4, 3, 0):

            bpy.ops.object.mode_set(mode='PAINT_GPENCIL')

            gp.data.zdepth_offset = 0.01

            ts.gpencil_paint.brush.gpencil_settings.pen_strength = 1

            opacity = gp.grease_pencil_modifiers.new(name="Opacity", type="GP_OPACITY")
            opacity.show_expanded = False
            thickness = gp.grease_pencil_modifiers.new(name="Thickness", type="GP_THICK")
            thickness.show_expanded = False

            if event.shift:
                bpy.ops.wm.tool_set_by_id(name="builtin.line")

                props = get_tool_options(context, 'builtin.line', "GPENCIL_OT_primitive_line")

                if props.subdivision <= 10:
                    props.subdivision = 50

            else:
                bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")

        else:

            bpy.ops.object.mode_set(mode='PAINT_GREASE_PENCIL')

            ts.gpencil_surface_offset = 0.01

            ts.gpencil_paint.brush.strength = 1

            opacity = gp.modifiers.new(name="Opacity", type="GREASE_PENCIL_OPACITY")
            opacity.show_expanded = False
            thickness = gp.modifiers.new(name="Thickness", type="GREASE_PENCIL_THICKNESS")
            thickness.show_expanded = False

            if event.shift:
                bpy.ops.wm.tool_set_by_id(name="builtin.line")

                props = get_tool_options(context, 'builtin.line', "GREASE_PENCIL_OT_primitive_line")

                if props.subdivision <= 10:
                    props.subdivision = 50

            else:
                bpy.ops.wm.tool_set_by_id(name="builtin.brush")

        return {'FINISHED'}

class ShrinkwrapGreasePencil(bpy.types.Operator):
    bl_idname = "machin3.shrinkwrap_grease_pencil"
    bl_label = "MACHIN3: ShrinkWrap Grease Pencil"
    bl_description = "Shrinkwrap current Grease Pencil Layer to closest mesh surface based on Surface Offset value"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        active = context.active_object
        if active and active.type in ['GPENCIL', 'GREASEPENCIL']:
            return active.data.layers.active

    def execute(self, context):
        dg = context.evaluated_depsgraph_get()

        ts = context.scene.tool_settings
        gp = context.active_object
        mx = gp.matrix_world

        layer = gp.data.layers.active

        if bpy.app.version < (4, 3, 0):
            offset = gp.data.zdepth_offset
            frame = layer.active_frame

            for stroke in frame.strokes:
                for idx, point in enumerate(stroke.points):
                    closest, _, co, no, _, _ = get_closest(mx @ point.co, depsgraph=dg, debug=False)

                    if closest:
                        point.co = mx.inverted_safe() @ (co + no * offset)

        else:
            offset = ts.gpencil_surface_offset
            drawing = layer.current_frame().drawing

            if False:
                for att in drawing.attributes:
                    if att.domain == 'POINT' and att.name == 'position':

                        for a in att.data:
                            closest, _, co, no, _, _ = get_closest(mx @ a.vector, depsgraph=dg, debug=False)

                            if closest:
                                a.vector = mx.inverted_safe() @ (co + no * offset)

                        break

            else:
                for stroke in drawing.strokes:
                    for point in stroke.points:
                        closest, _, co, no, _, _ = get_closest(mx @ point.position, depsgraph=dg, debug=False)

                        if closest:
                            point.position = mx.inverted_safe() @ (co + no * offset)

        return {'FINISHED'}
