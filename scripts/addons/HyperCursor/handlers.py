import bpy
from bpy.app.handlers import persistent

from . utils.application import delay_execution, set_prop_safe
from . utils.math import compare_matrix
from . utils.history import add_history_entry
from . utils.object import get_active_object
from . utils.draw import draw_hyper_cursor_HUD, draw_cursor_history, draw_cursor_history_names, draw_fading_label
from . utils.registration import get_prefs
from . utils.workspace import get_3dview, get_assetbrowser_area, get_window_region_from_area
from . utils.gizmo import restore_gizmos
from . utils.tools import active_tool_is_hypercursor
from . colors import red, yellow, green
from time import time

global_debug = False

def ensure_gizmo_and_HUD_drawing():
    global global_debug

    debug = global_debug

    if debug:
        print("  gizmo and HUD drawing")

    scene = getattr(bpy.context, 'scene', None)

    if scene:
        hc = scene.HC

        if not hc.show_object_gizmos:
            hc.show_object_gizmos = True

        if not hc.draw_HUD:
            hc.draw_HUD = True

hypercursorHUD = None
hypercursorVIEW3D = None
cursorhistoryVIEW3D = None
cursorhistoryHUD = None

def manage_HUD_and_VIEW3D_drawing():
    global global_debug, hypercursorHUD, hypercursorVIEW3D, cursorhistoryVIEW3D, cursorhistoryHUD

    debug = global_debug

    if debug:
        print("  HUD and VIEW3D drawing")

    scene = getattr(bpy.context, 'scene', None)

    if scene:
        hc = scene.HC

        if hypercursorHUD and "RNA_HANDLE_REMOVED" in str(hypercursorHUD):
            hypercursorHUD = None

        if hc.historyCOL or hc.use_world or hc.draw_pipe_HUD:
            if not hypercursorHUD:
                if debug:
                    print("   adding new cursor HUD handler")

                hypercursorHUD = bpy.types.SpaceView3D.draw_handler_add(draw_hyper_cursor_HUD, (bpy.context,), 'WINDOW', 'POST_PIXEL')

        elif hypercursorHUD:
            if debug:
                print("   removing old cursor HUD handler")

            bpy.types.SpaceView3D.draw_handler_remove(hypercursorHUD, 'WINDOW')
            hypercursorHUD = None

        if hc.draw_pipe_HUD:
            from . operators.add import PipeGizmoManager

            if not PipeGizmoManager.gizmo_data:
                if hidden := hc.get('hidden_gizmos'):
                    if debug:
                        print("   restoring HC gizmo settings, after undoing Pipe Creation")

                else:
                    print("WARNING: Restoring HC gizmo settings, after undoing Pipe Creation")

                restore_gizmos(dict(hidden))

        if cursorhistoryVIEW3D and "RNA_HANDLE_REMOVED" in str(cursorhistoryVIEW3D):
            cursorhistoryVIEW3D = None

        if cursorhistoryHUD and "RNA_HANDLE_REMOVED" in str(cursorhistoryHUD):
            cursorhistoryHUD = None

        if hc.historyCOL and hc.draw_history:
            if not cursorhistoryVIEW3D:
                if debug:
                    print("   adding new history lines VIEW3D handler")

                cursorhistoryVIEW3D = bpy.types.SpaceView3D.draw_handler_add(draw_cursor_history, (bpy.context,), 'WINDOW', 'POST_VIEW')

            if not cursorhistoryHUD:
                if debug:
                    print("   adding new history lines HUD handler")

                cursorhistoryHUD = bpy.types.SpaceView3D.draw_handler_add(draw_cursor_history_names, (bpy.context,), 'WINDOW', 'POST_PIXEL')

        else:
            if cursorhistoryVIEW3D:
                if debug:
                    print("   removing old history lines VIEW3D handler")

                bpy.types.SpaceView3D.draw_handler_remove(cursorhistoryVIEW3D, 'WINDOW')
                cursorhistoryVIEW3D = None

            if cursorhistoryHUD:
                if debug:
                    print("   removing old history lines HUD handler")

                bpy.types.SpaceView3D.draw_handler_remove(cursorhistoryHUD, 'WINDOW')
                cursorhistoryHUD = None

def manage_legacy_updates():
    global global_debug

    debug = global_debug

    if debug:
        print("  legacy updates")

def manage_auto_history():
    global global_debug

    debug = global_debug

    if debug:
        print("  auto history")

    scene = getattr(bpy.context, 'scene', None)

    if scene:
        hc = scene.HC

        if hc.auto_history and hc.track_history:

            hmx = hc.historyCOL[hc.historyIDX].mx if hc.historyCOL else None
            cmx = scene.cursor.matrix

            if hmx is None or not compare_matrix(cmx, hmx, 4):
                add_history_entry(debug=debug)

mode_history = ()
event_history = ()
last_mode = None

def manage_mode_history():
    global global_debug, mode_history, last_mode

    debug = global_debug

    if debug:
        print("  mode history")

    if C := bpy.context:
        if debug:
            print("   mode:", C.mode)

        if (mode_history and mode_history[-1][0] != C.mode) or not mode_history:
            history = list(mode_history)
            history.append((C.mode, time()))

            if len(history) > 3:
                history = history[-3:]

            mode_history = history

        if debug:
            print("   history:", [h for h in mode_history])

        if get_prefs().hyperbevel_geometry_mode_switch:
            if mode_history and mode_history[-1] != last_mode:
                last_mode = mode_history[-1]

                if debug:
                    print(" mode has changed to", last_mode)

                if (mode := last_mode[0]) in ['EDIT_MESH', 'OBJECT'] and mode == C.mode:
                    active = get_active_object(C)

                    if active and active.HC.ishyper and active.HC.ishyperbevel:

                        if mode == 'OBJECT' and not active.HC.isfinishedhyperbevel:
                            from . operators.bevel import HyperBevel
                            msg = HyperBevel.create_finished_cutter(None, C, init=True, handler_invocation=True)

                            area, region, region_data, _ = get_3dview(C)

                            if area:
                                region, region_data = get_window_region_from_area(area)

                                with C.temp_override(area=area, region=region, region_data=region_data):
                                    if msg:
                                        text = ["ℹℹ Finished HyperBevel could not be created ℹℹ"] + msg
                                        draw_fading_label(C, text=text, y=100, color=[red, yellow], alpha=1, move_y=50, time=5)

                                    else:
                                        draw_fading_label(C, text="Finished HyperBevel Geometry + Modifier Setup", y=100, color=green, alpha=1, move_y=50, time=5)

                        elif mode == 'EDIT_MESH' and active.HC.isfinishedhyperbevel:
                            from . operators.bevel import HyperBevel

                            area, region, region_data, _ = get_3dview(C)

                            if area:
                                msgs = []
                                colors = []

                                for obj in C.objects_in_mode:
                                    msg = HyperBevel.recreate_base_cutter(None, cutter=obj)

                                    if debug:
                                        print("EDIT MODE, message:", msg)

                                    if msg:
                                        msgs.extend([f"ℹℹ HyperBevel Base Geometry could not be re-created for {obj.name}ℹℹ"] + msg)
                                        colors.extend([red, yellow])

                                    else:
                                        msgs.append(f"Re-created HyperBevel Base Geometry for {obj.name}")
                                        colors.append(green)

                                if msgs:
                                    with C.temp_override(area=area, region=region, region_data=region_data):
                                        draw_fading_label(C, text=msgs, y=100, color=colors, alpha=1, move_y=20 + 10 * len(msgs), time=2 + len(msgs))

def manage_undo_redo_history():
    global global_debug, event_history

    debug = global_debug

    if debug:
        print("  event history")

    history = list(event_history)
    history.append(('UNDO/REDO', time()))

    if len(history) > 3:
        history = history[-3:]

    event_history = tuple(history)

prev_active = None

def manage_redoCOL_selection_sync():
    global global_debug, prev_active

    debug = global_debug

    if debug:
        print("  redoCOL selection sync")

    scene = getattr(bpy.context, 'scene', None)

    if scene:
        hc = scene.HC
        active = get_active_object(bpy.context)

        if active and active != prev_active:
            prev_active = active

            if active.HC.assetpath:
                redoCOL = hc.redoaddobjCOL

                if active.HC.assetpath in redoCOL:
                    index = list(redoCOL).index(redoCOL[active.HC.assetpath])

                    if debug:
                        print("   new active is", active.name)
                        print("   index is:", index)

                    if hc.redoaddobjIDX != index:
                        hc.redoaddobjIDX = index

def manage_geo_gizmos():
    global global_debug

    debug = global_debug

    if debug:
       print("  geo gizmos")

    active = get_active_object(bpy.context)

    if active and active.mode == 'OBJECT' and active.type == 'MESH' and active.HC.ishyper:

        if active.HC.ishyperbevel:
            return

        elif active.library or (active.data and active.data.library):
            return

        if len(active.data.polygons) > active.HC.geometry_gizmos_show_limit:
            set_prop_safe(active.HC, 'geometry_gizmos_show', False)

        elif active.HC.geometry_gizmos_edit_mode == 'EDIT':
            if active.HC.objtype == 'CUBE' and len(active.data.polygons) > active.HC.geometry_gizmos_show_cube_limit:
                set_prop_safe(active.HC, 'geometry_gizmos_edit_mode', 'SCALE')

            elif active.HC.objtype == 'CYLINDER' and len(active.data.edges) > active.HC.geometry_gizmos_show_cylinder_limit:
                set_prop_safe(active.HC, 'geometry_gizmos_edit_mode', 'SCALE')

        if dm := getattr(active, 'DM', None):
            if dm.isdecal:
                set_prop_safe(active.HC, 'ishyper', False)

last_op_global = None

def manage_asset_drop_takeover():
    global global_debug, last_op_global, was_asset_drop_takeover_executed

    debug = global_debug

    if debug:
        print("  asset drop takeover")

    C = bpy.context

    if C.mode == 'OBJECT':

        operators = C.window_manager.operators
        active = active if (active := get_active_object(C)) and (active.HC.ishyperasset or active.type == 'CURVE') else None

        if active and operators:
            last_op = operators[-1]

            if last_op != last_op_global:
                last_op_global = last_op

                if last_op.bl_idname in ["OBJECT_OT_transform_to_mouse", "OBJECT_OT_add_named"]:

                    if debug:
                        print(f"   initiating takevoer, as last op is {last_op.bl_idname}")

                    areaAB = get_assetbrowser_area(C)
                    screen_areas = [area for area in C.screen.areas]

                    area3D, region, region_data, _ = get_3dview(C)

                    with C.temp_override(area=area3D):
                        is_HC_active = active_tool_is_hypercursor(C)

                    if areaAB and areaAB in screen_areas and area3D and area3D in screen_areas:
                        if is_HC_active:

                            if active.HC.ishyperasset:
                                if debug:
                                    print("    setting asset drop props")

                                with C.temp_override(area=areaAB):
                                    bpy.ops.machin3.get_object_asset(is_drop=True)

                                if debug:
                                    print("    AddObjectAtCursor() takeover")

                                with C.temp_override(area=area3D, region=region, region_data=region_data):
                                    if active_tool_is_hypercursor(C):
                                        bpy.ops.machin3.add_object_at_cursor('INVOKE_DEFAULT', is_drop=True, type='ASSET')

                            elif active.type == 'CURVE':
                                if debug:
                                    print("    AddCurveAsset() takeover")

                                with C.temp_override(area=area3D, region=region, region_data=region_data):
                                    if active_tool_is_hypercursor(C):
                                        bpy.ops.machin3.add_curve_asset('INVOKE_DEFAULT')

                    else:
                        if debug:
                            print("    second Blender Window is open, preventing the HyperCursor takeover")

                        else:
                            from . utils.ui import popup_message
                            popup_message("Close this Blender Window, or HyperCursor can't take over after the asset drop")

was_asset_drop_cleanup_executed = False

def manage_asset_drop_cleanup():
    global global_debug, was_asset_drop_cleanup_executed

    debug = global_debug

    if debug:
        print("  HC asset drop cleanup")

    if was_asset_drop_cleanup_executed:
        if debug:
            print("   skipping second (duplicate) run")

        was_asset_drop_cleanup_executed = False
        return

    if debug:
        print("   checking for asset drop cleanup")

    C = bpy.context

    if C.mode == 'OBJECT':
        operators = C.window_manager.operators
        active = active if (active := get_active_object(C)) and active.type == 'EMPTY' and active.instance_collection and active.instance_type == 'COLLECTION' else None

        if active and operators:
            _lastop = operators[-1]

            was_asset_drop_cleanup_executed = True

@persistent
def undo_and_redo_post(scene):
    global global_debug

    if global_debug:
        print()
        print("HyperCursor undo/redo post handler:")
        print(" managing event history")

    delay_execution(manage_undo_redo_history)

    if global_debug:
        print(" ensure gizmo and HUD can be drawn")

    delay_execution(ensure_gizmo_and_HUD_drawing)

@persistent
def load_post(scene):
    global global_debug

    if global_debug:
        print()
        print("HyperCursor load post:")

    if global_debug:
        print(" ensure gizmo and HUD can be drawn")

    delay_execution(ensure_gizmo_and_HUD_drawing)

    if global_debug:
        print(" manage legacy updates")

    delay_execution(manage_legacy_updates)

@persistent
def depsgraph_update_post(scene):
    global global_debug

    if global_debug:
        print()
        print("HyperCursor depsgraph update post handler:")

    if global_debug:
        print(" managing HUD and VIEW3D drawing")

    delay_execution(manage_HUD_and_VIEW3D_drawing)

    if global_debug:
        print(" managing auto history")

    delay_execution(manage_auto_history)

    if global_debug:
        print(" managing mode history")

    delay_execution(manage_mode_history)

    if global_debug:
        print(" managing redoCOL selection sync")

    delay_execution(manage_redoCOL_selection_sync)

    if global_debug:
        print(" managing geo gizmos")

    delay_execution(manage_geo_gizmos)

    if global_debug:
        print(" managing asset drop takeover")

    delay_execution(manage_asset_drop_takeover)
