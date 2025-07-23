import bpy
from typing import Tuple, Union
from mathutils import Vector
import rna_keymap_ui
from bl_ui.space_statusbar import STATUSBAR_HT_header as statusbar
from bpy_extras.view3d_utils import region_2d_to_location_3d, location_3d_to_region_2d

from . import ui
from . registration import get_prefs
from . system import printd
from .. import preferences as prefs
from .. import bl_info

from .. colors import green, yellow, red
from .. items import number_mappings

from time import time

def get_icon(name):
    from .. import HyperCursorManager as HC

    if icon := HC.icons.get(name, None):
        return icon.icon_id
    else:
        return 42

def get_icon_from_event(event_type):
    if 'WHEEL' in event_type:
        if bpy.app.version >= (4, 3, 0):
            return 'MOUSE_MMB_SCROLL'
        else:
            return 'MOUSE_MMB'

    elif 'MOUSE' in event_type:
        return 'MOUSE_LMB' if 'LEFT' in event_type else 'MOUSE_RMB' if 'RIGHT' in event_type else 'MOUSE_MMB'

    else:
        return f'EVENT_{event_type}'

def get_icon_from_key(key):
    if key in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]:
        numbers = {v:k for k, v in number_mappings.items()}
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

class Mouse:

    _mouse_data = {'region': Vector((0, 0)),
                   'region_int': Vector((0, 0)),
                   'window': Vector((0, 0)),
                   'window_int': Vector((0, 0))}

    def capture_mouse(self, event):
        self._mouse_data['region'] = Vector((event.mouse_region_x, event.mouse_region_y))
        self._mouse_data['region_int'] = (int(event.mouse_region_x), int(event.mouse_region_y))

        self._mouse_data['window'] = Vector((event.mouse_x, event.mouse_y))
        self._mouse_data['window_int'] = (int(event.mouse_x), int(event.mouse_y))

    def get_mouse(self):
        return self._mouse_data['region']

    def get_mouse_window(self):
        return self._mouse_data['window']

    def get_mouse_int(self):
        return self._mouse_data['region_int']

    def get_mouse_window_int(self):
        return self._mouse_data['window_int']

def get_mouse_pos(self, context, event, window=False, init_offset=False, hud=True, hud_offset=(20, 20)):
    self.mouse_pos = Vector((event.mouse_region_x, event.mouse_region_y))

    if window:
        self.mouse_pos_window = Vector((event.mouse_x, event.mouse_y))

    if init_offset:
        self.mouse_offset = self.mouse_pos - Mouse().get_mouse()

    if hud:
        ui_scale = get_scale(context)

        self.HUD_x = self.mouse_pos.x + hud_offset[0] * ui_scale
        self.HUD_y = self.mouse_pos.y + hud_offset[1] * ui_scale

def wrap_mouse(self, context, x=False, y=False, wrap_hud=True):
    width = context.region.width
    height = context.region.height

    mouse_pos = self.mouse_pos.copy()

    if x:
        if mouse_pos.x <= 0:
            mouse_pos.x = width - 10

        elif mouse_pos.x >= width - 1:  # the -1 is required for full screen, where the max region width is never passed
            mouse_pos.x = 10

    if y and mouse_pos == self.mouse_pos:
        if mouse_pos.y <= 0:
            mouse_pos.y = height - 10

        elif mouse_pos.y >= height - 1:
            mouse_pos.y = 10

    if mouse_pos != self.mouse_pos:
        warp_mouse(self, context, mouse_pos, warp_hud=wrap_hud)

def warp_mouse(self, context, co2d=Vector(), region=True, warp_hud=True, hud_offset=(20, 20)):
    coords = get_window_space_co2d(context, co2d) if region else co2d

    context.window.cursor_warp(int(coords.x), int(coords.y))

    self.mouse_pos = co2d if region else get_region_space_co2d(context, co2d)

    if getattr(self, 'last_mouse', None):
        self.last_mouse = self.mouse_pos

    if warp_hud and getattr(self, 'HUD_x', None):
        ui_scale = get_scale(context)

        self.HUD_x = self.mouse_pos.x + hud_offset[0] * ui_scale
        self.HUD_y = self.mouse_pos.y + hud_offset[1] * ui_scale

def get_window_space_co2d(context, co2d=Vector(), region=None):
    region = region if region else context.region
    return co2d + Vector((region.x, region.y))

def get_region_space_co2d(context, co2d=Vector(), region=None):
    region = region if region else context.region
    return co2d - Vector((region.x, region.y))

def get_zoom_factor(context, depth_location, scale:float=10, ignore_obj_scale=False, debug=False):
    center = Vector((context.region.width / 2, context.region.height / 2))
    offset = center + Vector((10, 0))

    try:
        center_3d = region_2d_to_location_3d(context.region, context.region_data, center, depth_location)
        offset_3d = region_2d_to_location_3d(context.region, context.region_data, offset, depth_location)

    except:
        return 1

    if center_3d and offset_3d:

        zoom_factor = (center_3d - offset_3d).length * (scale / 10)

        if context.active_object and not ignore_obj_scale:
            mx = context.active_object.matrix_world.to_3x3()

            zoom_vector = mx.inverted_safe() @ Vector((zoom_factor, 0, 0))
            zoom_factor = zoom_vector.length * (scale / 10)

        if debug:
            from . draw import draw_point

            draw_point(depth_location, color=yellow, modal=False)
            draw_point(center_3d, color=green, modal=False)
            draw_point(offset_3d, color=red, modal=False)

            print("zoom factor:", zoom_factor)
        return zoom_factor
    return 1

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

        if isinstance(message, list):
            print(" »", ", ".join(message))
        else:
            print(" »", message)

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

def draw_keymap_item(layout, kc, km, kmi, label=''):
    box = layout.box()
    column = box.column(align=True)

    if label:
        row = column.split(align=True, factor=0.25)
        row.label(text=label)

    else:
        row = column.row(align=True)

    rna_keymap_ui.draw_kmi(["ADDON", "USER", "DEFAULT"], kc, km, kmi, row, 0)

    return column

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

                    if len(keylist) == 1:
                        label = name.title().replace("_", " ")

                    else:
                        if idx == 0:
                            if name:
                                layout.label(text=name.title().replace("_", " "))

                        label = f"   {item.get('label')}" if item.get('label') else ''

                    row = layout.row(align=True)
                    column = draw_keymap_item(row, kc, km, kmi, label)

                    info = item.get("info", '')

                    if info:
                        row = column.row(align=True)
                        row.alignment = 'LEFT'
                        row.active = False
                        row.label(text=f"     ↖ {info}", icon="NONE")

                    isdrawn = True
                    idx += 1

        drawn.append(isdrawn)

    return any(d for d in drawn)

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

def get_pretty_keymap_item_name(kmi):
    name = kmi.name.replace('MACHIN3: ', '').replace(' Macro', '')

    if kmi.idname == 'machin3.call_hyper_cursor_pie':
        if kmi.properties.idname == 'MACHIN3_MT_add_object_at_cursor':
            return "Add Object at Cursor"

    elif kmi.idname == 'machin3.transform_cursor':
        if kmi.properties.mode == 'DRAG':
            return name + ' (Drag Mode)'

    elif kmi.idname == 'machin3.point_cursor':
        if kmi.properties.instant:
            return name + ' Z instantly'

    elif kmi.idname == 'machin3.cycle_cursor_history':
        if kmi.properties.backwards:
            return name + ' ↑ (previous)'
        else:
            return name + ' ↓ (next)'

    elif kmi.idname == 'machin3.hyper_modifier':
        return name + f" ({kmi.properties.mode.title()})"

    elif kmi.idname == 'machin3.extract_face':
        return "Extract Evaluated Faces"

    return name

def get_modified_keymap_items(context):
    from .. registration import keys

    wm = context.window_manager
    kc = wm.keyconfigs.user

    keymaps_dict = {}
    modified_kmis = []
    missing_kmis = []

    for tool, mappings in keys.items():

        if tool == 'HYPERCURSOR':
            keymaps_dict["3D View Tool: Object, Hyper Cursor"] = {tool: mappings}

        elif tool == 'HYPERCURSOREDIT':
            keymaps_dict["3D View Tool: Edit Mesh, Hyper Cursor"] = {tool: mappings}

        elif tool in ['TOOLBAR', 'CUT', 'BEVEL', 'BEND', 'OBJECT']:
            for mapping in mappings:
                kmname = mapping['keymap']

                if kmname in keymaps_dict:
                    if tool in keymaps_dict[kmname]:
                        keymaps_dict[kmname][tool].append(mapping)
                    else:
                        keymaps_dict[kmname][tool] = [mapping]
                else:
                    keymaps_dict[kmname] = {tool: [mapping]}

        else:
            continue

    for keymap_name, km_data in keymaps_dict.items():
        km = kc.keymaps.get(keymap_name, None)

        if km:

            if km.is_user_modified:

                for tool, mappings in km_data.items():
                    for mapping in mappings:

                        if tool in ['HYPERCURSOR', 'HYPERCURSOREDIT']:
                            idname = mapping[0]
                            properties = mapping[2].get('properties', None) if mapping[2] else None

                        else:
                            idname = mapping.get('idname', None)
                            properties = mapping.get('properties', None)

                        kmi = find_kmi_from_idname(km, idname, properties, debug=False)

                        if kmi:
                            if kmi.is_user_modified:
                                modified_kmis.append((km, kmi))

                        else:
                            missing_kmis.append((keymap_name, tool, mapping))
        else:
            print(f"WARNING: keymap {keymap_name} NOT FOUND!!")

    return modified_kmis, missing_kmis

def get_panel_fold(layout, idname, text='', icon='NONE', custom_icon=None, align=True, default_closed=True):
    header, panel = layout.panel(idname=idname, default_closed=default_closed)
    header.active = bool(panel)

    if custom_icon:
        header.label(text=text, icon_value=get_icon(custom_icon))
    else:
        header.label(text=text, icon=icon)

    return panel.column(align=align) if panel else None

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

def draw_status_item_precision(layout, fine=None, coarse=None, fine_key='SHIFT', coarse_key='CTRL', gap=10):
    if fine is not None:
        draw_status_item(layout, active=fine, key=fine_key, gap=gap)

    if coarse is not None:
        draw_status_item(layout, active=coarse, key=coarse_key, gap=gap if fine is None else None)

    if fine is not None and coarse is not None:
        draw_status_item(layout, active=fine or coarse, text="Precision", prop="fine" if fine else "coarse" if coarse else None)

    elif fine is not None:
        draw_status_item(layout, active=fine, text="Precision", prop="fine" if fine else None)

    elif coarse is not None:
        draw_status_item(layout, active=coarse, text="Precision", prop="coarse" if coarse else None)

def draw_status_item_numeric(self, layout, period=True, invert=False, default_remove='Most', gap=10):
    keys = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

    if period:
        keys.insert(0, 'PERIOD')

    if self.is_numeric_input_marked:
        draw_status_item(layout, active=self.is_alt, key='ALT', text="Special", gap=gap)
        draw_status_item(layout, key='BACKSPACE', text=f"Remove {'Last Only' if self.is_alt else default_remove}", gap=1)
    else:
        draw_status_item(layout, key='BACKSPACE', text="Backspace", gap=gap)

    draw_status_item(layout, alert=self.is_numeric_input_marked, key=keys, text="Replace Highlighted" if self.is_numeric_input_marked else "", gap=2)

    if invert:
        draw_status_item(layout, key="MINUS", text="Negate", gap=2)

def finish_status(self):
    statusbar.draw = self.bar_orig

generic_gizmo = None

def draw_enable_gizmos_warning(context, layout, tool):
    wm = context.window_manager
    kc = wm.keyconfigs.user

    mode = context.mode

    keymap = prefs.tool_keymaps_mapping[(tool.idname, mode)]
    km = kc.keymaps.get(keymap)

    if km:
        kmi = km.keymap_items.get('machin3.toggle_hyper_cursor_gizmos')

        if kmi and kmi.active:
            row = layout.row(align=True)
            row.separator(factor=2)

            row.label(text='Reveal Hyper Cursor Gizmos via', icon="ERROR")

            if kmi.shift:
                row.label(text="", icon='EVENT_SHIFT')
            if kmi.alt:
                row.label(text="", icon='EVENT_ALT')
            if kmi.ctrl:
                row.label(text="", icon='EVENT_CTRL')

            row.label(text="", icon=get_icon_from_event(kmi.type))

def draw_tool_header(context, layout, tool):
    global generic_gizmo

    def get_generic_gizmo_idname(generic_gizmo):
        if generic_gizmo:
            try:
                return generic_gizmo.bl_idname
            except:
                pass

    p = get_prefs()
    version = '.'.join([str(i) for i in bl_info['version']])
    hc = context.scene.HC

    toolbar = getattr(context.space_data, 'show_region_toolbar', False)

    if toolbar:
        layout.label(text=f"Hyper Cursor {version}", icon_value=get_icon('hypercursor'))
    else:
        layout.label(text=f"Hyper Cursor {version}")

    if tool.idname == "machin3.tool_hyper_cursor_simple":
        row = layout.row()
        row.active = False
        row.label(text="The Simple Hyper Cursor tool is being phased out")
        return

    if generic_gizmo is None or get_generic_gizmo_idname(generic_gizmo) != 'gizmogroup.gizmo_tweak':
        generic_gizmo = ui.get_keymap_item('Generic Gizmo', 'gizmogroup.gizmo_tweak')

    if generic_gizmo and not generic_gizmo.any:
        layout.operator("machin3.setup_generic_gizmo_keymap", text='  Setup Generic Gizmo', icon='EVENT_ALT')

    if p.show_world_mode:
        layout.prop(context.scene.HC, 'use_world', text="World", icon='WORLD', toggle=True)

    if p.show_hints:

        if hc.draw_pipe_HUD and not hc.show_gizmos:
            layout.separator(factor=2)

            row = layout.row()
            row.alert = True
            row.label(text="You are in Pipe Mode, with the HyperCursor Gizmo hidden!", icon='ERROR')

        elif not hc.show_gizmos or not hc.draw_HUD:
            draw_enable_gizmos_warning(context, layout, tool)

    if p.show_help:
        layout.separator(factor=2)
        layout.operator("machin3.hyper_cursor_help", text='Help', icon='INFO')

    if p.show_update_available and p.update_available:
        layout.separator(factor=2)
        layout.label(text="A HyperCursor Update is available!", icon_value=get_icon('refresh_green'))

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

def gizmo_selection_passthrough(self, event) -> bool:
    return event.type == 'MOUSEMOVE' or (getattr(self, 'highlighted', False) and event.type == 'LEFTMOUSE' and event.value == 'PRESS')

def scroll(event, wheel=True, pad=True, key=False):
    return scroll_up(event, wheel=wheel, pad=pad, key=key) or scroll_down(event, wheel=wheel, pad=pad, key=key)

def scroll_up(event, wheel=True, pad=True, key=False):

    if pad and event.type == 'TRACKPADPAN' and event.mouse_y > event.mouse_prev_y and event.mouse_y - event.mouse_prev_y >= 5:
        return True

    elif event.value == 'PRESS':

        if wheel and event.type == 'WHEELUPMOUSE':
            return True

        if key and event.type in ['ONE', 'UP_ARROW', 'PLUS', 'NUMPAD_PLUS']:
            return True

    return False

def scroll_down(event, wheel=True, pad=True, key=False):

    if pad and event.type == 'TRACKPADPAN' and event.mouse_y < event.mouse_prev_y and event.mouse_prev_y - event.mouse_y >= 5:
        return True

    elif event.value == 'PRESS':

        if wheel and event.type == 'WHEELDOWNMOUSE':
            return True

        if key and event.type in ['TWO', 'DOWN_ARROW', 'MINUS', 'NUMPAD_MINUS']:
            return True

    return False

def get_mousemove_divisor(event, normal:float=10, shift:float=50, ctrl:float=2, sensitivity:float=1):
    divisor = ctrl if event.ctrl else shift if event.shift else normal
    ui_scale = bpy.context.preferences.system.ui_scale

    return divisor * ui_scale * sensitivity

def init_timer_modal(self, debug=False):
    self.TIMER_start = time()

    self.TIMER_countdown = self.time * get_prefs().modal_hud_timeout

    if debug:
        print(f"initiating timer with a countdown of {self.time}s ({self.time * get_prefs().modal_hud_timeout}s)")

def set_countdown(self, debug=False):
    self.TIMER_countdown = self.time * get_prefs().modal_hud_timeout - (time() - self.TIMER_start)

    if debug:
        print("countdown:", self.TIMER_countdown)

def get_timer_progress(self, debug=False):
    progress =  self.TIMER_countdown / (self.time * get_prefs().modal_hud_timeout)

    if debug:
        print("progress:", progress)

    return progress

def ignore_events(event, none=True, timer=True, timer_report=True):
    ignore = ['INBETWEEN_MOUSEMOVE', 'WINDOW_DEACTIVATE']

    if none:
        ignore.append('NONE')

    if timer:
        ignore.extend(['TIMER', 'TIMER1', 'TIMER2', 'TIMER3'])

    if timer_report:
        ignore.append('TIMER_REPORT')

    return event.type in ignore

def is_key(self, event, key, onpress=None, onrelease=None, debug=False):
    keystr = f'is_{key.lower()}'

    if getattr(self, keystr, None) is None:
        setattr(self, keystr, False)

    if event.type == key:
        if event.value == 'PRESS':
            if not getattr(self, keystr):
                setattr(self, keystr, True)

                if onpress:
                    onpress()

        elif event.value == 'RELEASE':
            if getattr(self, keystr):
                setattr(self, keystr, False)

                if onrelease:
                    onrelease()

    if debug:
        print()
        print(f"is {key.capitalize()}:", getattr(self, keystr))

    return getattr(self, keystr)

def update_mod_keys(self, event=None, shift=True, ctrl=True, alt=True):
    if shift:
        self.is_shift = event.shift if event else False

    if ctrl:
        self.is_ctrl = event.ctrl if event else False

    if alt:
        self.is_alt = event.alt if event else False

def get_flick_direction(context, mouse_loc_3d, flick_vector, axes):
    origin_2d = location_3d_to_region_2d(context.region, context.region_data, mouse_loc_3d, default=Vector((context.region.width / 2, context.region.height / 2)))
    axes_2d = {}

    for direction, axis in axes.items():

        axis_2d = location_3d_to_region_2d(context.region, context.region_data, mouse_loc_3d + axis, default=origin_2d)
        if (axis_2d - origin_2d).length:
            axes_2d[direction] = (axis_2d - origin_2d).normalized()

    return min([(d, abs(flick_vector.xy.angle_signed(a))) for d, a in axes_2d.items()], key=lambda x: x[1])[0]

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

    elif context.mode == 'EDIT_CURVE':
        curve = context.active_object.data

        for spline in curve.splines:
            for point in spline.points:
                if not point.hide:
                    point.co = point.co
                    return

def force_obj_gizmo_update(context):
    from .. ui import gizmos
    gizmos.force_obj_gizmo_update = True
    gizmos.force_objs_gizmo_update = True

    force_ui_update(context)

def force_geo_gizmo_update(context):
    from .. ui import gizmos
    gizmos.force_geo_gizmo_update = True

    force_ui_update(context)

def force_pick_hyper_bevels_gizmo_update(context):
    from .. ui import gizmos
    gizmos.force_pick_hyper_bevels_gizmo_update = True

    force_ui_update(context)

def get_scale(context, system_scale=True, modal_HUD=True, gizmo_size=False) -> Union[Tuple[float, float], float]:
    if gizmo_size:
        gizmo_size = context.preferences.view.gizmo_size / 75

    ui_scale = 1

    if system_scale:
        ui_scale *= context.preferences.system.ui_scale

    if modal_HUD:
        ui_scale *= get_prefs().modal_hud_scale

    if gizmo_size:
        return ui_scale, gizmo_size
    else:
        return ui_scale

def is_on_screen(context, co2d):
    if 0 <= co2d[0] <= context.region.width:
        if 0 <= co2d[1] <= context.region.height:
            return True
    return False
