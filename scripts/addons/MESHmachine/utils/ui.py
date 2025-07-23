from typing import Union
import bpy
from bpy_extras.view3d_utils import region_2d_to_location_3d

import blf
import rna_keymap_ui
from bl_ui.space_statusbar import STATUSBAR_HT_header as statusbar

from mathutils import Vector

from . registration import get_prefs
from .. colors import red, green, yellow
from .. items import numbers_map

from time import time

icons = None

def get_icon(name):
    global icons

    if not icons:
        from .. import icons

    return icons[name].icon_id

def get_icon_from_key(key):
    if key in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]:
        numbers = {v:k for k, v in numbers_map.items()}
        return f"EVENT_{numbers[key]}KEY"

    elif key in ['LMB', 'MMB', 'RMB', 'LMB_DRAG', 'LMB_2X', 'MMB_DRAG', 'MMB_SCROLL', 'RMB_DRAG', 'MOVE']:

        if bpy.app.version < (4, 3, 0):
            if key == 'MMB_SCROLL':
                key = 'MMB'

        return f"MOUSE_{key}"

    elif key in ['COMMAND', 'CONTROL', 'EMPTY1', 'EMPTY2', 'EMPTY3', 'MENU', 'RING', 'OPTION', 'WINDOWS']:
        return f"KEY_{key}"

    elif key in ['SPACE']:
        return f"EVENT_{key}KEY"

    else:
        return f"EVENT_{key}"

def draw_key_icons(layout, key: Union[list, str]):
    keys = [key] if isinstance(key, str) else key

    for icon in keys:

        layout.label(text='', icon=icon)

        if bpy.app.version >= (4, 3, 0):
            if icon in ['KEY_EMPTY2', 'EVENT_CTRL', 'EVENT_ALT', 'EVENT_OS', 'EVENT_F10', 'EVENT_F11', 'EVENT_F12', 'EVENT_ESC', 'EVENT_PAUSE', 'EVENT_INSERT', 'EVENT_HOME', 'EVENT_END', 'EVENT_APP', 'EVENT_BACKSPACE', 'EVENT_DEL']:
                layout.separator(factor=1.5)

            elif icon in ['KEY_EMPTY3', 'EVENT_SPACEKEY']:
                layout.separator(factor=3)

def init_cursor(self, event, offsetx=0, offsety=20):
    self.last_mouse_x = event.mouse_x
    self.last_mouse_y = event.mouse_y

    self.region_offset_x = event.mouse_x - event.mouse_region_x
    self.region_offset_y = event.mouse_y - event.mouse_region_y

    self.HUD_x = event.mouse_x - self.region_offset_x + offsetx
    self.HUD_y = event.mouse_y - self.region_offset_y + offsety

def wrap_cursor(self, context, event):

    if event.mouse_region_x <= 0:
        context.window.cursor_warp(context.region.width + self.region_offset_x - 10, event.mouse_y)

    if event.mouse_region_x >= context.region.width - 1:  # the -1 is required for full screen, where the max region width is never passed
        context.window.cursor_warp(self.region_offset_x + 10, event.mouse_y)

    if event.mouse_region_y <= 0:
        context.window.cursor_warp(event.mouse_x, context.region.height + self.region_offset_y - 10)

    if event.mouse_region_y >= context.region.height - 1:
        context.window.cursor_warp(event.mouse_x, self.region_offset_y + 100)

def get_zoom_factor(context, depth_location, scale=10, ignore_obj_scale=False, debug=False):
    center = Vector((context.region.width / 2, context.region.height / 2))
    offset = center + Vector((scale, 0))

    center_3d = region_2d_to_location_3d(context.region, context.region_data, center, depth_location)
    offset_3d = region_2d_to_location_3d(context.region, context.region_data, offset, depth_location)

    zoom_factor = (center_3d - offset_3d).length

    if context.active_object and not ignore_obj_scale:
        mx = context.active_object.matrix_world.to_3x3()

        zoom_vector = mx.inverted_safe() @ Vector((zoom_factor, 0, 0))
        zoom_factor = zoom_vector.length

    if debug:
        from . draw import draw_point

        draw_point(depth_location, color=yellow, modal=False)
        draw_point(center_3d, color=green, modal=False)
        draw_point(offset_3d, color=red, modal=False)

        print("zoom factor:", zoom_factor)
    return zoom_factor

def popup_message(message, title="Info", icon="INFO", terminal=True):
    def draw_message(self, context):
        if isinstance(message, list):
            for m in message:
                self.layout.label(text=m)
        else:
            self.layout.label(text=message)
    bpy.context.window_manager.popup_menu(draw_message, title=title, icon=icon)

    if terminal:
        if icon == "FILE_TICK":
            icon = "ENABLE"
        elif icon == "CANCEL":
            icon = "DISABLE"
        print(icon, title)
        print(" • ", message)

def get_panel_fold(layout, idname, text='', icon='NONE', custom_icon=None, align=True, default_closed=True):
    header, panel = layout.panel(idname=idname, default_closed=default_closed)
    header.active = bool(panel)

    if custom_icon:
        header.label(text=text, icon_value=get_icon(custom_icon))
    else:
        header.label(text=text, icon=icon)

    return panel.column(align=align) if panel else None

def update_HUD_location(self, event, offsetx=0, offsety=20):
    if get_prefs().modal_hud_follow_mouse:
        self.HUD_x = event.mouse_x - self.region_offset_x + offsetx
        self.HUD_y = event.mouse_y - self.region_offset_y + offsety

def draw_init(self):
    self.font_id = 1
    self.offset = 0

def draw_title(self, title, subtitle=None, subtitleoffset=125, HUDcolor=None, HUDalpha=0.5, shadow=True):
    if not HUDcolor:
        HUDcolor = get_prefs().modal_hud_color
    shadow = (0, 0, 0)

    scale = bpy.context.preferences.system.ui_scale * get_prefs().modal_hud_scale

    if shadow:
        blf.color(self.font_id, *shadow, HUDalpha * 0.7)
        blf.position(self.font_id, self.HUD_x - 7 + 1, self.HUD_y - 1, 0)
        blf.size(self.font_id, int(20 * scale))
        blf.draw(self.font_id, "• " + title)

    blf.color(self.font_id, *HUDcolor, HUDalpha)
    blf.position(self.font_id, self.HUD_x - 7, self.HUD_y, 0)
    blf.size(self.font_id, int(20 * scale))
    blf.draw(self.font_id, f"» {title}")

    if subtitle:
        if shadow:
            blf.color(self.font_id, *shadow, HUDalpha / 2 * 0.7)
            blf.position(self.font_id, self.HUD_x - 7 + int(subtitleoffset * scale), self.HUD_y, 0)
            blf.size(self.font_id, int(15 * scale))
            blf.draw(self.font_id, subtitle)

        blf.color(self.font_id, *HUDcolor, HUDalpha / 2)
        blf.position(self.font_id, self.HUD_x - 7 + int(subtitleoffset * scale), self.HUD_y, 0)
        blf.size(self.font_id, int(15 * scale))
        blf.draw(self.font_id, subtitle)

def draw_prop(self, name, value, offset=0, decimal=2, active=True, HUDcolor=None, prop_offset=120, hint="", hint_offset=200, shadow=True):
    if not HUDcolor:
        HUDcolor = get_prefs().modal_hud_color
    shadow = (0, 0, 0)

    if active:
        alpha = 1
    else:
        alpha = 0.4

    scale = bpy.context.preferences.system.ui_scale * get_prefs().modal_hud_scale

    offset = self.offset + int(offset * scale)
    self.offset = offset

    if shadow:
        blf.color(self.font_id, *shadow, alpha * 0.7)
        blf.position(self.font_id, self.HUD_x + int(20 * scale) + 1, self.HUD_y - int(20 * scale) - offset - 1, 0)
        blf.size(self.font_id, int(11 * scale))
        blf.draw(self.font_id, name)

    blf.color(self.font_id, *HUDcolor, alpha)
    blf.position(self.font_id, self.HUD_x + int(20 * scale), self.HUD_y - int(20 * scale) - offset, 0)
    blf.size(self.font_id, int(11 * scale))
    blf.draw(self.font_id, name)

    if type(value) is str:
        if shadow:
            blf.color(self.font_id, *shadow, alpha * 0.7)
            blf.position(self.font_id, self.HUD_x + int(prop_offset * scale) + 1, self.HUD_y - int(20 * scale) - offset - 1, 0)
            blf.size(self.font_id, int(14 * scale))
            blf.draw(self.font_id, value)

        blf.color(self.font_id, *HUDcolor, alpha)
        blf.position(self.font_id, self.HUD_x + int(prop_offset * scale), self.HUD_y - int(20 * scale) - offset, 0)
        blf.size(self.font_id, int(14 * scale))
        blf.draw(self.font_id, value)

    elif type(value) is bool:
        if shadow:
            blf.color(self.font_id, *shadow, alpha * 0.7)
            blf.position(self.font_id, self.HUD_x + int(prop_offset * scale) + 1, self.HUD_y - int(20 * scale) - offset - 1, 0)
            blf.size(self.font_id, int(14 * scale))
            blf.draw(self.font_id, str(value))

        if value:
            blf.color(self.font_id, 0.5, 1, 0.5, alpha)
        else:
            blf.color(self.font_id, 1, 0.3, 0.3, alpha)

        blf.position(self.font_id, self.HUD_x + int(prop_offset * scale), self.HUD_y - int(20 * scale) - offset, 0)
        blf.size(self.font_id, int(14 * scale))
        blf.draw(self.font_id, str(value))

    elif type(value) is int:
        if shadow:
            blf.color(self.font_id, *shadow, alpha * 0.7)
            blf.position(self.font_id, self.HUD_x + int(prop_offset * scale) + 1, self.HUD_y - int(20 * scale) - offset - 1, 0)
            blf.size(self.font_id, int(20 * scale))
            blf.draw(self.font_id, "%d" % (value))

        blf.color(self.font_id, *HUDcolor, alpha)
        blf.position(self.font_id, self.HUD_x + int(prop_offset * scale), self.HUD_y - int(20 * scale) - offset, 0)
        blf.size(self.font_id, int(20 * scale))
        blf.draw(self.font_id, "%d" % (value))

    elif type(value) is float:
        if shadow:
            blf.color(self.font_id, *shadow, alpha * 0.7)
            blf.position(self.font_id, self.HUD_x + int(prop_offset * scale) + 1, self.HUD_y - int(20 * scale) - offset - 1, 0)
            blf.size(self.font_id, int(16 * scale))
            blf.draw(self.font_id, "%.*f" % (decimal, value))

        blf.color(self.font_id, *HUDcolor, alpha)
        blf.position(self.font_id, self.HUD_x + int(prop_offset * scale), self.HUD_y - int(20 * scale) - offset, 0)
        blf.size(self.font_id, int(16 * scale))
        blf.draw(self.font_id, "%.*f" % (decimal, value))

    if get_prefs().modal_hud_hints and hint:
        if shadow:
            blf.color(self.font_id, *shadow, 0.6 * 0.7)
            blf.position(self.font_id, self.HUD_x + int(hint_offset * scale) + 1, self.HUD_y - int(20 * scale) - offset - 1, 0)
            blf.size(self.font_id, int(11 * scale))
            blf.draw(self.font_id, "%s" % (hint))

        blf.color(self.font_id, *HUDcolor, 0.6)
        blf.position(self.font_id, self.HUD_x + int(hint_offset * scale), self.HUD_y - int(20 * scale) - offset, 0)
        blf.size(self.font_id, int(11 * scale))
        blf.draw(self.font_id, "%s" % (hint))

def draw_text(self, text, size, offset=0, offsetx=0, HUDcolor=None, HUDalpha=0.5, shadow=True):
    if not HUDcolor:
        HUDcolor = get_prefs().modal_hud_color
    shadow = (0, 0, 0)

    scale = bpy.context.preferences.system.ui_scale * get_prefs().modal_hud_scale

    offset = self.offset + int(offset * scale)
    self.offset = offset

    if shadow:
        blf.color(self.font_id, *shadow, HUDalpha * 0.7)
        blf.position(self.font_id, self.HUD_x + int(20 * scale) + offsetx + 1, self.HUD_y - int(20 * scale) - offset - 1, 0)
        blf.size(self.font_id, int(size * scale))
        blf.draw(self.font_id, text)

    blf.color(self.font_id, *HUDcolor, HUDalpha)
    blf.position(self.font_id, self.HUD_x + int(20 * scale) + offsetx, self.HUD_y - int(20 * scale) - offset, 0)
    blf.size(self.font_id, int(size * scale))
    blf.draw(self.font_id, text)

def draw_keymap_items_old(kc, name, keylist, layout):
    drawn = []

    idx = 0

    for item in keylist:
        keymap = item.get("keymap")
        isdrawn = False

        if keymap:
            km = kc.keymaps.get(keymap)

            kmi = None
            if km:
                idname = item.get("idname")

                for kmitem in km.keymap_items:
                    if kmitem.idname == idname:
                        properties = item.get("properties")

                        if properties:
                            if all([getattr(kmitem.properties, name, None) == value for name, value in properties]):
                                kmi = kmitem
                                break

                        else:
                            kmi = kmitem
                            break

            if kmi:
                if idx == 0:
                    box = layout.box()

                label = item.get("label", None)

                if not label:
                    label = name.title().replace("_", " ")

                if len(keylist) > 1:
                    if idx == 0:
                        box.label(text=name.title().replace("_", " "))

                row = box.split(factor=0.15)
                row.label(text=label)

                rna_keymap_ui.draw_kmi(["ADDON", "USER", "DEFAULT"], kc, km, kmi, row, 0)

                infos = item.get("info", [])
                for text in infos:
                    row = box.split(factor=0.15)
                    row.separator()
                    row.label(text=text, icon="INFO")

                isdrawn = True
                idx += 1

        drawn.append(isdrawn)
    return drawn

def kmi_to_string(kmi, compact=False, docs_mode=False):
    if compact:
        if bool(props := dict(kmi.properties)):
            if kmi.idname == 'machin3.assetbrowser_bookmark':
                props_str = str(props).replace("'", '').replace('{', '').replace('}', '')
            else:
                props_str = str(props).replace("'", '').replace('{', '').replace('}', '').replace('0', 'False').replace('1', 'True')

            kmi_str = f"{kmi.idname}, {kmi.to_string()}, properties: {props_str}"
        else:
            kmi_str = f"{kmi.idname}, {kmi.to_string()}"

    else:
        kmi_str = f"{kmi.idname}, name: {kmi.name}, active: {kmi.active}, map type: {kmi.map_type}, type: {kmi.type}, value: {kmi.value}, alt: {kmi.alt}, ctrl: {kmi.ctrl}, shift: {kmi.shift}, properties: {str(dict(kmi.properties))}"

    if docs_mode:
        return f"`{kmi_str}`"
    else:
        return kmi_str

def draw_keymap_items(kc, name, keylist, layout):
    drawn = []

    idx = 0

    for item in keylist:
        keymap = item.get("keymap")
        isdrawn = False

        if keymap:
            km = kc.keymaps.get(keymap)

            if km:
                idname = item.get("idname")
                properties = item.get("properties", None)
                kmi = find_kmi_from_idname(km, idname, properties)

                if kmi:
                    if idx == 0:
                        box = layout.box()
                        column = box.column(align=True)

                    if len(keylist) == 1:
                        label = name.title().replace("_", " ")

                    else:
                        if idx == 0:
                            column.label(text=name.title().replace("_", " "))

                        label = f"   {item.get('label')}"

                    row = column.split(align=True, factor=0.25)

                    r = row.row(align=True)
                    r.active = len(keylist) == 1
                    r.label(text=label)

                    rna_keymap_ui.draw_kmi(["ADDON", "USER", "DEFAULT"], kc, km, kmi, row, 0)

                    info = item.get("info", '')

                    if info:
                        if type(info) is list:
                            for idx, i in enumerate(info):
                                row = column.row(align=True)
                                row.alignment = 'LEFT'
                                row.alert = True
                                row.label(text=f"  {'ℹ' if idx == 0 else '     '} {i}", icon="NONE")

                        elif type(info) is str:
                            row = column.row(align=True)
                            row.alignment = 'LEFT'
                            row.alert = True
                            row.label(text=f"  ℹ {info}", icon="NONE")

                    isdrawn = True
                    idx += 1

        drawn.append(isdrawn)

    return any(d for d in drawn)

def find_kmi_from_idname(km, idname, properties=None, debug=False):
    for kmi in km.keymap_items:
        if kmi.idname == idname:

            if properties:
                if all(getattr(kmi.properties, name, None) == value for name, value in properties):
                    if debug:
                        print(f"  keymap: {km.name} kmi:", kmi_to_string(kmi, compact=True))
                    return kmi

            else:
                if debug:
                    print(f"  keymap: {km.name} kmi:", kmi_to_string(kmi, compact=True))
                return kmi

    if debug:
        print(f"  keymap: {km.name} kmi: NONE")

def init_status(self, context, title='', func=None):
    self.bar_orig = statusbar.draw

    if func:
        statusbar.draw = func
    else:
        statusbar.draw = draw_basic_status(self, context, title)

def draw_basic_status(self, context, title):
    def draw(self, context):
        layout = self.layout

        row = layout.row(align=True)
        row.label(text=title)

        row.label(text="", icon='MOUSE_LMB')
        row.label(text="Finish")

        if context.window_manager.keyconfigs.active.name.startswith('blender'):
            row.label(text="", icon='MOUSE_MMB')
            row.label(text="Viewport")

        row.label(text="", icon='MOUSE_RMB')
        row.label(text="Cancel")

    return draw

def draw_status_item(layout, active=True, alert=False, key: Union[list, str] = [], text="", prop=None, gap=None):
    row = layout.row(align=True)
    row.active = active
    row.alert = alert

    keys = [key] if isinstance(key, str) or isinstance(key, int) else key

    if gap:
        row.separator(factor=gap)

    draw_key_icons(row, [get_icon_from_key(key) for key in keys])

    if prop is not None:
        if text:
            row.label(text=f"{text}: {prop}")
        else:
            row.label(text=f"{prop}")
    elif text:
        row.label(text=text)

def finish_status(self):
    statusbar.draw = self.bar_orig

def get_keymap_item(name, idname, key=None, alt=False, ctrl=False, shift=False, properties=[]):
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.user

    km = kc.keymaps.get(name)

    alt = int(alt)
    ctrl = int(ctrl)
    shift = int(shift)

    if km:
        kmi = km.keymap_items.get(idname)

        if kmi:
            found = True if key is None else all([kmi.type == key and kmi.alt is alt and kmi.ctrl is ctrl and kmi.shift is shift])

            if found:
                if properties:
                    if all([getattr(kmi.properties, name, False) == prop for name, prop in properties]):
                        return kmi
                else:
                    return kmi

def init_modal_handlers(self, context, area=True, hud=False, view3d=False, timer=False, time_step=0.05, modal=True):
    if area:
        self.area = context.area

    if hud:
        self.HUD = bpy.types.SpaceView3D.draw_handler_add(self.draw_HUD, (context, ), 'WINDOW', 'POST_PIXEL')

    if view3d:
        self.VIEW3D = bpy.types.SpaceView3D.draw_handler_add(self.draw_VIEW3D, (context, ), 'WINDOW', 'POST_VIEW')

    if timer:

        if getattr(self, 'time', None):
            init_timer_modal(self)

        self.TIMER = context.window_manager.event_timer_add(time_step, window=context.window)

    if modal:
        context.window_manager.modal_handler_add(self)

def finish_modal_handlers(self):
    if getattr(self, 'HUD', None):
        bpy.types.SpaceView3D.draw_handler_remove(self.HUD, 'WINDOW')

    if getattr(self, 'VIEW3D', None):
        bpy.types.SpaceView3D.draw_handler_remove(self.VIEW3D, 'WINDOW')

    if getattr(self, 'TIMER', None):
        bpy.context.window_manager.event_timer_remove(self.TIMER)

def navigation_passthrough(event, alt=True, wheel=False) -> bool:
    if alt and wheel:
        return event.type in {'MIDDLEMOUSE'} or event.type.startswith('NDOF') or (event.alt and event.type in {'LEFTMOUSE', 'RIGHTMOUSE'} and event.value == 'PRESS') or event.type in {'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}
    elif alt:
        return event.type in {'MIDDLEMOUSE'} or event.type.startswith('NDOF') or (event.alt and event.type in {'LEFTMOUSE', 'RIGHTMOUSE'} and event.value == 'PRESS')
    elif wheel:
        return event.type in {'MIDDLEMOUSE'} or event.type.startswith('NDOF') or event.type in {'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}
    else:
        return event.type in {'MIDDLEMOUSE'} or event.type.startswith('NDOF')

def scroll(event, wheel=True, pad=True, key=True):
    return scroll_up(event, wheel=wheel, pad=pad, key=key) or scroll_down(event, wheel=wheel, pad=pad, key=key)

def scroll_up(event, wheel=True, pad=True, key=True):

    if pad and event.type == 'TRACKPADPAN' and event.mouse_y > event.mouse_prev_y and event.mouse_y - event.mouse_prev_y >= 5:
        return True

    elif event.value == 'PRESS':

        if wheel and event.type == 'WHEELUPMOUSE':
            return True

        if key and event.type in ['ONE', 'UP_ARROW', 'PLUS', 'NUMPAD_PLUS']:
            return True

    return False

def scroll_down(event, wheel=True, pad=True, key=True):

    if pad and event.type == 'TRACKPADPAN' and event.mouse_y < event.mouse_prev_y and event.mouse_prev_y - event.mouse_y >= 5:
        return True

    elif event.value == 'PRESS':

        if wheel and event.type == 'WHEELDOWNMOUSE':
            return True

        if key and event.type in ['TWO', 'DOWN_ARROW', 'MINUS', 'NUMPAD_MINUS']:
            return True

    return False

def init_timer_modal(self, debug=False):
    self.start = time()

    self.countdown = self.time * get_prefs().modal_hud_timeout

    if debug:
        print(f"initiating timer with a countdown of {self.time}s ({self.time * get_prefs().modal_hud_timeout}s)")

def set_countdown(self, debug=False):
    self.countdown = self.time * get_prefs().modal_hud_timeout - (time() - self.start)

    if debug:
        print("countdown:", self.countdown)

def get_timer_progress(self, debug=False):
    progress =  self.countdown / (self.time * get_prefs().modal_hud_timeout)

    if debug:
        print("progress:", progress)

    return progress

def force_ui_update(context, active=None):
    if context.mode == 'OBJECT':
        if active:
            active.select_set(True)

        else:
            if active := context.active_object:
                active.select_set(active.select_get())

            if visible := context.visible_objects:
                visible[0].select_set(visible[0].select_get())

    elif context.mode == 'EDIT_MESH':
        context.active_object.select_set(True)

def get_scale(context):
    return context.preferences.system.ui_scale * get_prefs().modal_hud_scale
