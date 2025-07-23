import bpy
from bpy.props import BoolProperty, FloatProperty, EnumProperty, IntProperty, StringProperty
from mathutils import Vector

from .. utils.asset import get_pretty_assetpath
from .. utils.cursor import set_cursor
from .. utils.draw import draw_fading_label, draw_line, draw_lines, draw_point, draw_points
from .. utils.history import add_history_entry, prettify_history
from .. utils.math import compare_matrix
from .. utils.property import rotate_list, step_collection
from .. utils.registration import get_prefs
from .. utils.ui import finish_modal_handlers, init_modal_handlers, popup_message, get_zoom_factor, set_countdown, get_timer_progress, force_ui_update
from .. utils.view import ensure_visibility, focus_on_cursor, visible_get

from .. colors import red, blue, green, yellow, white, orange
from .. items import change_history_mode_items

class DrawCursorHistory(bpy.types.Operator):
    bl_idname = "machin3.draw_cursor_history"
    bl_label = "MACHIN3: Draw Cursor History"
    bl_description = "Draw Cursor History"
    bl_options = {'INTERNAL'}

    time: FloatProperty(name="Time", default=2)
    alpha: FloatProperty(name="Alpha", default=0.5, min=0.1, max=1)
    @classmethod
    def poll(cls, context):
        return context.scene.HC.historyCOL

    def draw_VIEW3D(self, context):
        try:
            if context.area == self.area:
                alpha = get_timer_progress(self) * self.alpha

                draw_line(self.locations, width=1, alpha=alpha / 3)

                draw_point(self.locations[0], size=4, color=green, alpha=alpha * 2)
                draw_point(self.locations[-1], size=4, color=red, alpha=alpha * 2)

                draw_points(self.locations[1:-1], size=3, alpha=alpha / 2)

                for axis, color in self.axes:

                    size = 1
                    coords = []

                    for origin, orientation in zip(self.locations, self.orientations):
                        factor = get_zoom_factor(context, origin, scale=20, ignore_obj_scale=True)

                        coords.append(origin + (orientation @ axis).normalized() * size * factor * 0.1)
                        coords.append(origin + (orientation @ axis).normalized() * size * factor)

                    if coords:
                        draw_lines(coords, color=color, width=2, alpha=alpha / 1.5)
        except:
            pass

    def modal(self, context, event):
        if not context.area:
            return {'CANCELLED'}

        context.area.tag_redraw()

        if self.TIMER_countdown < 0:
            self.finish(context)
            return {'FINISHED'}

        if event.type == 'TIMER':
            set_countdown(self)

        return {'PASS_THROUGH'}

    def finish(self, context):
        finish_modal_handlers(self)

    def execute(self, context):
        hc = context.scene.HC
        history = hc.historyCOL

        self.locations = [h.location for h in history]
        self.orientations = [h.rotation for h in history]

        self.matrices = [h.mx for h in history]
        self.axes = [(Vector((1, 0, 0)), red), (Vector((0, 1, 0)), green), (Vector((0, 0, 1)), blue)]

        self.idx = hc.historyIDX

        init_modal_handlers(self, context, view3d=True, timer=True)
        return {'RUNNING_MODAL'}

class CycleCursorHistory(bpy.types.Operator):
    bl_idname = "machin3.cycle_cursor_history"
    bl_label = "MACHIN3: Cycle Cursor History"
    bl_description = "Cycle through all stored Cursor States"
    bl_options = {'REGISTER', 'UNDO'}

    backwards: BoolProperty(name="Cycle backwards", default=True)
    @classmethod
    def poll(cls, context):
        return context.scene.HC.historyCOL

    def execute(self, context):
        hc = context.scene.HC
        history = hc.historyCOL

        if hc.use_world:
            hc.avoid_update = True
            hc.use_world = False

        cmx = context.scene.cursor.matrix

        current = history[hc.historyIDX]

        is_at_active_entry = compare_matrix(cmx, current.mx)

        if is_at_active_entry:
            h = step_collection(hc, current, "historyCOL", "historyIDX", -1 if self.backwards else 1)

        else:
            h = current

        if h != current or not is_at_active_entry:
            set_cursor(matrix=h.mx)

            if hc.focus_cycle:
                bpy.ops.view3d.view_center_cursor('INVOKE_DEFAULT' if hc.focus_mode == 'SOFT' else 'EXEC_DEFAULT')

            if not hc.draw_history:
                bpy.ops.machin3.draw_cursor_history(time=1)

        else:
            if h.index == 0:
                draw_fading_label(context, text="You've reached the START of the Cursor History", color=green, move_y=40, time=4)

            else:
                draw_fading_label(context, text="You've reached the END of the Cursor History", color=red, move_y=40, time=4)

        return {'FINISHED'}

class ChangeCursorHistory(bpy.types.Operator):
    bl_idname = "machin3.change_cursor_history"
    bl_label = "MACHIN3: Change Cursor History"
    bl_options = {'REGISTER', 'UNDO'}

    mode: EnumProperty(name="Add or Remove History Entry", items=change_history_mode_items, default='ADD')
    index: IntProperty(name="History Index", description="used to remove specific entry, not the current one", default=-1)
    time: FloatProperty(default=2)
    alpha: FloatProperty(name="Alpha", default=0.5, min=0.1, max=1)
    @classmethod
    def description(cls, context, properties):
        if properties:
            if properties.mode == 'ADD':
                return "Add current Cursor State to History"
            elif properties.mode == 'REMOVE':
                if properties.index == -1:
                    return "Remove current Cursor State from History"
                history = context.scene.HC.historyCOL
                entry = history[properties.index]
                return f"Remove {entry.name} entry from History"
        return "Invalid Context"

    def draw_VIEW3D(self, context):
        try:
            if context.area == self.area:
                alpha = get_timer_progress(self) * self.alpha

                if self.mode == 'REMOVE':
                    if self.red_locs:
                        draw_line(self.red_locs, color=(1, 0, 0), width=2, alpha=alpha)

                    if self.white_locs:
                        draw_line(self.white_locs, color=(1, 1, 1), width=2, alpha=alpha / 2)

                elif self.mode == 'ADD':
                    draw_line(self.green_locs, color=(0, 1, 0), width=2, alpha=alpha)

                draw_line(self.all_locs, color=(1, 1, 1), width=1, alpha=alpha / 2)
        except:
            pass

    def modal(self, context, event):
        if not context.area:
            return {'CANCELLED'}

        context.area.tag_redraw()

        if self.TIMER_countdown < 0:
            self.finish(context)
            return {'FINISHED'}

        if event.type == 'TIMER':
            set_countdown(self)

        return {'PASS_THROUGH'}

    def finish(self, context):
        finish_modal_handlers(self)

    def execute(self, context):
        hc = context.scene.HC

        if self.mode == 'ADD':

            self.all_locs = [entry.location.copy() for entry in hc.historyCOL.values()]

            add_history_entry()

            force_ui_update(context)

            if len(hc.historyCOL) > 1:
                idx = hc.historyIDX

                locations = [entry.location for entry in hc.historyCOL.values()]

                if idx == len(hc.historyCOL) - 1:
                    self.green_locs = [locations[-2], locations[-1]]
                else:
                    self.green_locs = [locations[idx - 1], locations[idx], locations[idx + 1]]

                init_modal_handlers(self, context, view3d=True, timer=True)
                return {'RUNNING_MODAL'}

        elif self.mode == 'REMOVE':

            if hc.historyCOL:
                cmx = context.scene.cursor.matrix

                current = hc.historyCOL[hc.historyIDX]

                if (self.index == -1 and compare_matrix(cmx, current.mx)) or self.index > -1:

                    locations = [(name, entry.location) for name, entry in hc.historyCOL.items()]

                    removeidx = current.index if self.index == -1 else self.index

                    if len(hc.historyCOL) > 2:

                        if removeidx == 0:
                            self.red_locs = [locations[0][1].copy(), locations[1][1].copy()]
                            self.white_locs = []

                        elif removeidx == len(hc.historyCOL) - 1:
                            self.red_locs = [locations[-2][1].copy(), locations[-1][1].copy()]
                            self.white_locs = []

                        else:
                            self.red_locs = [locations[removeidx - 1][1].copy(), locations[removeidx][1].copy(), locations[removeidx + 1][1].copy()]
                            self.white_locs = [locations[removeidx - 1][1].copy(), locations[removeidx + 1][1].copy()]

                    locations.pop(removeidx)

                    self.all_locs = [loc.copy() for _, loc in locations]

                    hc.historyCOL.remove(removeidx)

                    prettify_history(context)

                    if (hc.historyIDX != 0 or not hc.historyCOL) and (self.index == -1 or removeidx <= hc.historyIDX):
                        hc.historyIDX -= 1

                    if hc.auto_history and hc.historyIDX >= 0 and hc.historyCOL:
                        set_cursor(matrix=hc.historyCOL[hc.historyIDX].mx)

                        if hc.focus_cycle:
                            bpy.ops.view3d.view_center_cursor('INVOKE_DEFAULT' if hc.focus_mode == 'SOFT' else 'EXEC_DEFAULT')

                    force_ui_update(context)

                    if len(self.all_locs) > 1:

                        init_modal_handlers(self, context, view3d=True, timer=True)
                        return {'RUNNING_MODAL'}

                else:
                    popup_message(["The current stored history entry doesn't match the current cursor location.", "Enable Auto-History, cycle to another entry, or manually store the current cursor!"], title="Could not remove Cursor History Entry")
            else:
                popup_message("No cursor history stored yet.", title="Could not remove Cursor History Entry")

        elif self.mode in ['MOVEUP', 'MOVEDOWN']:

            if self.mode == 'MOVEUP' and self.index > 0:

                hc.historyCOL.move(self.index, self.index - 1)
                hc.historyIDX = self.index - 1

            elif self.mode == 'MOVEDOWN' and self.index < len(hc.historyCOL) - 1:

                hc.historyCOL.move(self.index, self.index + 1)
                hc.historyIDX = self.index + 1

            prettify_history(context)

            force_ui_update(context)

        return {'FINISHED'}

class ClearCursorHistory(bpy.types.Operator):
    bl_idname = "machin3.clear_cursor_history"
    bl_label = "MACHIN3: Clear Cursor History"
    bl_description = "Clear All Cursor History"
    bl_options = {'REGISTER', 'UNDO'}

    alpha: FloatProperty(name="Alpha", default=0.5, min=0.1, max=1)
    time: FloatProperty(default=2)
    @classmethod
    def poll(cls, context):
        return context.scene.HC.historyCOL

    def draw_VIEW3D(self, context):
        try:
            if context.area == self.area:
                alpha = get_timer_progress(self) * self.alpha

                if len(self.all_locs) > 1:
                    draw_line(self.all_locs, color=(1, 0, 0), width=2, alpha=alpha)

                else:
                    draw_point(self.all_locs[0], color=(1, 0, 0), size=10, alpha=alpha)
        except:
            pass

    def modal(self, context, event):
        if not context.area:
            return {'CANCELLED'}

        context.area.tag_redraw()

        if self.TIMER_countdown < 0:

            self.finish(context)
            return {'FINISHED'}

        if event.type == 'TIMER':
            set_countdown(self)

        return {'PASS_THROUGH'}

    def finish(self, context):
        finish_modal_handlers(self)

    def execute(self, context):
        hc = context.scene.HC

        self.all_locs = [h.mx.to_translation() for _, h in hc.historyCOL.items()]

        hc.historyCOL.clear()
        hc.historyIDX = -1

        init_modal_handlers(self, context, view3d=True, timer=True)
        return {'RUNNING_MODAL'}

class SelectCursorHistory(bpy.types.Operator):
    bl_idname = "machin3.select_cursor_history"
    bl_label = "MACHIN3: Select Cursor History Entry"
    bl_description = "Set Cursor to History Entry\nALT: Avoid Focusing on Cursor and making it the Active Entry"
    bl_options = {'REGISTER', 'UNDO'}

    index: IntProperty(name="History Index")

    def invoke(self, context, event):
        scene = context.scene
        hc = scene.HC
        history = hc.historyCOL

        if self.index < len(history):

            entry = history[self.index]

            set_cursor(matrix=entry.mx)

            if not event.alt:
                hc.historyIDX = self.index
                focus_on_cursor(focusmode=hc.focus_mode, ignore_selection=True)

        return {'FINISHED'}

class ChangeAddObjHistory(bpy.types.Operator):
    bl_idname = "machin3.change_add_obj_history"
    bl_label = "MACHIN3: Change Add Object History"
    bl_options = {'REGISTER', 'UNDO'}

    index: IntProperty(name="Index in Redo Add Object Collection")
    mode: StringProperty(name="Mode", default='REMOVE')
    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            return context.scene.HC.redoaddobjCOL

    @classmethod
    def description(cls, context, properties):
        if properties:
            if properties.mode == 'SELECT':
                return "Select/Cycle through objects"

            elif properties.mode == 'FETCHSIZE':
                return "Set Size from Active Object"

            elif properties.mode == 'REMOVE':
                if properties.index == -1:
                    return "Clear All History Entries"
                elif properties.index == -2:
                    return "Clear Unused History Entries"
                else:
                    return "Remove History Entry"
        return "Invalid Context"

    def execute(self, context):
        redoCOL = context.scene.HC.redoaddobjCOL
        active = context.active_object

        if self.mode == 'SELECT':
            dg = context.evaluated_depsgraph_get()

            debug = False

            entry = redoCOL[self.index]
            if debug:
                print()
                print(get_pretty_assetpath(entry))

            if entry.name not in ['CUBE', 'CYLINDER']:
                active = active if (active := context.active_object) and active.select_get() else None

                objects = [(obj, visible_get(obj, dg)) for obj in bpy.data.objects if obj.HC.assetpath == entry.name]

                index_objects = [obj for obj, _ in objects]

                if active and active.HC.assetpath == entry.name and active in index_objects:
                    rotate_list(objects, index_objects.index(active) + 1)

                if debug:
                    print(" active:", active.name if active else None)
                    print(" candidates:")

                    for obj, vis in objects:
                        print(" ", obj.name, "✔" if vis['visible'] else "❌", vis['meta'] if vis['meta'] else '')

                if objects:

                    is_sorting = get_prefs().hide_wire_collection_sort

                    if is_sorting:
                        exclude_hidden = ['SCENE']
                    else:
                        exclude_hidden = ['SCENE', 'VIEWLAYER', 'HIDDEN_COLLECTION']

                    bpy.ops.object.select_all(action='DESELECT')

                    not_in_scene = []
                    not_on_view_layer = []
                    in_hidden_collection = []

                    has_selected = False

                    for obj, vis in objects:

                        if (meta := vis['meta']) in exclude_hidden:
                            if meta == 'SCENE':
                                not_in_scene.append(obj)

                            elif meta == 'VIEWLAYER':
                                not_on_view_layer.append(obj)

                            elif meta == 'HIDDEN_COLLECTION':
                                in_hidden_collection.append(obj)

                        else:

                            ensure_visibility(context, obj, viewlayer=is_sorting, hidden_collection=is_sorting, select=True)

                            context.view_layer.objects.active = obj

                            bpy.ops.view3d.view_selected('INVOKE_DEFAULT')

                            has_selected = True
                            break

                    msg = []
                    color = []

                    if has_selected:
                        if len(objects) > 1:
                            msg.append(get_pretty_assetpath(entry))
                            color.append(white)

                            msg.append(f"{index_objects.index(context.active_object) + 1} of {len(objects)} selected!")
                            color.append(green)

                    else:
                        msg.append(get_pretty_assetpath(entry))
                        color.append(orange)

                        msg.append(f"Could not select any of {len(objects)} objects!")
                        color.append(red)

                    if not_in_scene:
                        msg.append(f"Skipped {len(not_in_scene)} objects, that aren't in the scene")
                        color.append(yellow)

                    if not_on_view_layer:
                        msg.append(f"Skipped {len(not_on_view_layer)} objects, that aren't on the view layer")
                        color.append(yellow)

                    if in_hidden_collection:
                        msg.append(f"Skipped {len(in_hidden_collection)} objects, that are in hidden collections")
                        color.append(yellow)

                    if msg:
                        draw_fading_label(context, text=msg, color=color, move_y=len(msg) * 20, time=len(msg) * 2)

                    if has_selected:
                        entry.selectable = True
                        return {'FINISHED'}

                    entry.selectable = False
                    return {'CANCELLED'}

                else:
                    msg = []
                    color = []

                    msg.append(get_pretty_assetpath(entry))
                    color.append(orange)

                    msg.append("No objects found for this entry")
                    color.append(red)

                    draw_fading_label(context, text=msg, color=color, move_y=20, time=2)

                    entry.selectable = False
                    return {'CANCELLED'}

        elif self.mode == 'FETCHSIZE' and active:
            entry = redoCOL[self.index]

            entry.size = max(active.dimensions)

        elif self.mode == 'REMOVE':

            if self.index == -1:
                redoCOL.clear()

            elif self.index == -2:
                remove = []

                for entry in redoCOL:
                    assetpath = entry.name

                    if assetpath in ['CUBE', 'CYLINDER']:
                        objects = [obj for obj in context.scene.objects if obj.HC.ishyper and obj.HC.objtype == assetpath and not obj.parent and obj.display_type not in ['WIRE', 'BOUNDS']]

                        if not objects:
                            remove.append(assetpath)

                    else:
                        objects = [obj for obj in context.scene.objects if obj.HC.assetpath == assetpath]

                        if not objects:
                            remove.append(assetpath)

                for assetpath in remove:
                    index = list(redoCOL).index(redoCOL[assetpath])
                    redoCOL.remove(index)

            else:
                redoCOL.remove(self.index)

        return {'FINISHED'}
