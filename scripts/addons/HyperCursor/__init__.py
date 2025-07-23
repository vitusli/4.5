bl_info = {
    "name": "HyperCursor",
    "author": "MACHIN3",
    "version": (0, 9, 18, "patch", 5),
    "blender": (4, 2, 0),
    "location": "3D View Toolbar + Sidebar",
    "revision": "3243774fb60b716a5f5ebaf2ae81ae9b457dba87",
    "description": "A toolset surrounding and elevating Blender's Cursor to facilitate smart and efficient Object Creation and Blocking in 3D Space.",
    "warning": "",
    "doc_url": "https://machin3.io/HyperCursor/docs",
    "category": "3D View"}

import bpy
from bpy.utils import previews
from bpy.props import PointerProperty, EnumProperty

from mathutils import Vector

from typing import Tuple
import os
import importlib

from . handlers import depsgraph_update_post, load_post, undo_and_redo_post
from . properties import HCSceneProperties, HCObjectProperties, HCNodeGroupProperties
from . ui.menus import asset_browser_import_method_warning, modifier_buttons, mesh_context_menu
from . utils.registration import get_addon, get_core, get_tools, get_ops, get_macros, get_prefs, get_path
from . utils.registration import register_classes, unregister_classes, register_tools, unregister_tools, register_macros, unregister_macros, register_keymaps, unregister_keymaps
from . utils.system import printd, verify_update, install_update

from time import time

def update_check():
    def get_version_as_string():
        return '.'.join(str(v) for v in bl_info['version'])

    def get_version_as_semver_string():
        version = [v for v in bl_info['version']]

        if len(version) == 3:
            return ".".join([str(v) for v in version])

        else:
            sign = "-" if any(version[3] == rt for rt in ['alpha', 'beta', 'rc']) else "+"
            basever = ".".join([str(v) for v in version[:3]]) + f"{sign}{version[3]}"

            if version[4:]:
                tailver = ".".join(str(v) for v in version[4:])
                return f"{basever}.{tailver}"

            else:
                return basever

    def hook(resp, *args, **kwargs):
        if resp:
            if resp.text == 'true':
                get_prefs().update_available = True

            else:
                get_prefs().update_available = False

            if debug:
                print(" received response:", resp.text)

            write_update_check(update_path, time(), debug=debug)

    def init_update_check(debug=False):
        if debug:
            print()
            print("initiating update check for version", get_version_as_string(), "semver:", get_version_as_semver_string())

        import platform
        import hashlib
        from . modules.requests_futures.sessions import FuturesSession

        machine = hashlib.sha1(platform.node().encode('utf-8')).hexdigest()[0:7]

        headers = {'User-Agent': f"{bl_info['name']}/{get_version_as_semver_string()} Blender/{'.'.join([str(v) for v in bpy.app.version])} ({platform.uname()[0]}; {platform.uname()[2]}; {platform.uname()[4]}; {machine})"}
        session = FuturesSession()

        try:
            if debug:
                print(" sending update request")

            session.post("https://drum.machin3.io/update", data={'revision': bl_info['revision']}, headers=headers, hooks={'response': hook})
        except:
            pass

    def write_update_check(update_path, update_time, debug=False):
        if debug:
            print()
            print("writing update check data")

        update_available = get_prefs().update_available

        msg = [f"version: {get_version_as_string()}",
               f"update time: {update_time}",
               f"update available: {update_available}\n"]

        with open(update_path, mode='w') as f:
            f.write('\n'.join(m for m in msg))

        if debug:
            print(" written to", update_path)

        return update_time, update_available

    def read_update_check(update_path, debug=False) -> Tuple[bool, str, float, bool]:
        if debug:
            print()
            print(f"reading {bl_info['name']} update check data")

        with open(update_path) as f:
            lines = [l[:-1] for l in f.readlines()]

        if len(lines) == 3:
            version = lines[0].replace('version: ', '')
            update_time_str = lines[1].replace('update time: ', '')
            update_available_str = lines[2].replace('update available: ', '')

            if debug:
                print(" fetched version:", version)
                print(" fetched update available:", update_available_str)
                print(" fetched update time:", update_time_str)

            try:
                update_time = float(update_time_str)
            except:
                update_time = None

            try:
                update_available = True if update_available_str == 'True' else False if update_available_str == 'False' else None
            except:
                update_available = None

            if version is not None and update_time is not None and update_available is not None:
                return True, version, update_time, update_available

        return False, None, None, None

    debug = False

    update_path = os.path.join(get_path(), 'update_check')

    if not os.path.exists(update_path):
        if debug:
            print(f"init {bl_info['name']} update check as file does not exist")

        init_update_check(debug=debug)

    else:
        valid, version, update_time, update_available = read_update_check(update_path, debug=debug)

        if valid:

            if debug:
                print(f" comparing stored {bl_info['name']} version:", version, "with bl_info['version']:", get_version_as_string())

            if version != get_version_as_string():
                if debug:
                    print(f"init {bl_info['name']} update check, as the versions differ due to user updating the addon since the last update check")

                init_update_check(debug=debug)
                return

            now = time()
            delta_time = now - update_time

            if debug:
                print(" comparing", now, "and", update_time)
                print("  delta time:", delta_time)

            if delta_time > 72000:
                if debug:
                    print(f"init {bl_info['name']} update check, as it has been over 20 hours since the last one")

                init_update_check(debug=debug)
                return

            if debug:
                print(f"no {bl_info['name']} update check required, setting update available prefs from stored file")

            get_prefs().update_available = update_available

        else:
            if debug:
                print(f"init {bl_info['name']} update check as fetched file is invalid")

            init_update_check(debug=debug)

def register():
    global classes, tools, macros, keymaps

    core_classlists, core_keylists = get_core()
    core_classes = register_classes(core_classlists)

    bpy.types.Scene.HC = PointerProperty(type=HCSceneProperties)
    bpy.types.Object.HC = PointerProperty(type=HCObjectProperties)
    bpy.types.NodeTree.HC = PointerProperty(type=HCNodeGroupProperties)

    bpy.types.WindowManager.HC_asset_catalogs = EnumProperty(items=[])

    ops_classlists, ops_keylists = get_ops()

    classes = register_classes(ops_classlists) + core_classes

    tools = register_tools(get_tools())

    macros = register_macros(get_macros())

    keymaps = register_keymaps(core_keylists + ops_keylists)

    bpy.types.DATA_PT_modifiers.prepend(modifier_buttons)
    bpy.types.VIEW3D_MT_edit_mesh_context_menu.prepend(mesh_context_menu)
    bpy.types.ASSETBROWSER_MT_editor_menus.append(asset_browser_import_method_warning)

    HyperCursorManager.register_icons()

    bpy.app.handlers.depsgraph_update_post.append(depsgraph_update_post)
    bpy.app.handlers.load_post.append(load_post)

    bpy.app.handlers.undo_post.append(undo_and_redo_post)
    bpy.app.handlers.redo_post.append(undo_and_redo_post)

    HyperCursorManager.clear_addons()

    if get_prefs().registration_debug:
        print(f"Registered {bl_info['name']} {'.'.join([str(i) for i in bl_info['version']])}")

    update_check()

    verify_update()

def unregister():
    global classes, tools, macros, keymaps

    debug = get_prefs().registration_debug

    from . handlers import hypercursorHUD, hypercursorVIEW3D, cursorhistoryVIEW3D, cursorhistoryHUD

    if hypercursorHUD and "RNA_HANDLE_REMOVED" not in str(hypercursorHUD):
        bpy.types.SpaceView3D.draw_handler_remove(hypercursorHUD, 'WINDOW')

    if hypercursorVIEW3D and "RNA_HANDLE_REMOVED" not in str(hypercursorVIEW3D):
        bpy.types.SpaceView3D.draw_handler_remove(hypercursorVIEW3D, 'WINDOW')

    if cursorhistoryVIEW3D and "RNA_HANDLE_REMOVED" not in str(cursorhistoryVIEW3D):
        bpy.types.SpaceView3D.draw_handler_remove(cursorhistoryVIEW3D, 'WINDOW')

    if cursorhistoryHUD and "RNA_HANDLE_REMOVED" not in str(cursorhistoryHUD):
        bpy.types.SpaceView3D.draw_handler_remove(cursorhistoryHUD, 'WINDOW')

    bpy.app.handlers.depsgraph_update_post.remove(depsgraph_update_post)
    bpy.app.handlers.load_post.remove(load_post)

    bpy.app.handlers.undo_post.remove(undo_and_redo_post)
    bpy.app.handlers.redo_post.remove(undo_and_redo_post)

    unregister_tools(tools)

    unregister_classes(classes)
    unregister_keymaps(keymaps)
    unregister_macros(macros)

    bpy.types.DATA_PT_modifiers.remove(modifier_buttons)
    bpy.types.VIEW3D_MT_edit_mesh_context_menu.remove(mesh_context_menu)
    bpy.types.ASSETBROWSER_MT_editor_menus.remove(asset_browser_import_method_warning)

    del bpy.types.Scene.HC
    del bpy.types.Object.HC

    del bpy.types.WindowManager.HC_asset_catalogs

    HyperCursorManager.unregister_icons()

    if debug:
        print(f"Unregistered {bl_info['name']} {'.'.join([str(i) for i in bl_info['version']])}")

    install_update()

class HyperCursorManager:

    props = {
        'cursor_2d': Vector((0, 0)),      # Cursor's 2d location
        'HUD_offset': {                   # HUD offsets from the above location
            'left': Vector((0, 0)),       # pipe mode on the left
            'right': Vector((0, 0)),      # cursor history on the right, and always above the top button gizmo row
            'top': Vector((0, 0)),        # world alignment goes on top
        },
        'gizmo_scale': 0.1
    }

    addons = {}

    @classmethod
    def get_addon(cls, name='SomeAddon', version=False, debug=False):

        addon = cls.addons.setdefault(name.lower(), {'enabled': None, 'version': None, 'foldername': '', 'path': '', 'module': None})
        if addon['enabled'] is None:
            addon['enabled'],  addon['foldername'],  addon['version'],  addon['path'] = get_addon(name)

            if addon['enabled']:
                addon['module'] = importlib.import_module(addon['foldername'])

            if debug:
                printd(addon, name)

        return (addon['enabled'], addon['version']) if version else addon['enabled']

    @classmethod
    def clear_addons(cls):
        cls.addons.clear()

    @classmethod
    def register_icons(cls):
        path = os.path.join(get_prefs().path, "icons")
        cls.icons = previews.new()

        for i in sorted(os.listdir(path)):
            if i.endswith(".png"):
                iconname = i[:-4]
                filepath = os.path.join(path, i)

                cls.icons.load(iconname, filepath, 'IMAGE')

    @classmethod
    def unregister_icons(cls):
        previews.remove(cls.icons)
        del cls.icons

    defaults = []
    @classmethod
    def init_operator_defaults(cls, bl_idname, properties, include=None, skip=None, debug=False):
        if bl_idname not in cls.defaults:
            if debug:
                print("\ngetting defaults for", bl_idname, "from addon prefs")
            cls.defaults.append(bl_idname)
            ignore = [
                "__doc__",
                "__module__",
                "__slots__",
                "bl_rna",
                "rna_type",
            ]

            if include:
                props = [prop for prop in include]

            elif skip:
                props = [prop for prop in dir(properties) if prop not in ignore and prop not in skip]

            else:
                props = [prop for prop in dir(properties) if prop not in ignore]

            op = bl_idname.replace('MACHIN3_OT_', '')

            for prop in props:
                if debug:
                    print(" prop:", prop)

                if (default := getattr(get_prefs(), f"{op}_default_{prop}", None)) is not None:
                    if debug:
                        print("  prefs default:", default)
                        print("  op default:", getattr(properties, prop))
                    if default != getattr(properties, prop):
                        setattr(properties, prop, default)
        else:
            if debug:
                print("\ndefaults already set for", bl_idname)
