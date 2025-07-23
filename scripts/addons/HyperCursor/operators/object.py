import bpy
from bpy.props import StringProperty, BoolProperty, FloatProperty, IntProperty, EnumProperty
from bpy_extras.view3d_utils import location_3d_to_region_2d

from mathutils import Vector
from mathutils.geometry import intersect_line_plane
import bmesh

from math import degrees, sqrt

from .. import HyperCursorManager as HC

from .. utils.application import delay_execution
from .. utils.bmesh import ensure_gizmo_layers, get_face_angle
from .. utils.collection import get_scene_collections, get_wires_collection
from .. utils.draw import draw_circle, draw_init, draw_label, draw_batch, draw_point, draw_vector, draw_fading_label, get_text_dimensions
from .. utils.gizmo import hide_gizmos, restore_gizmos, setup_geo_gizmos
from .. utils.math import average_locations
from .. utils.mesh import get_bbox
from .. utils.modifier import is_array, remote_radial_array_poll, remote_mirror_poll, remove_mod, apply_mod, add_boolean, get_mod_obj, is_mod_obj, sort_modifiers
from .. utils.object import duplicate_objects, get_batch_from_matrix, get_batch_from_obj, get_eval_bbox, is_group_anchor, is_group_empty, is_plug_handle, parent, remove_obj, get_object_tree, is_wire_object, unparent
from .. utils.operator import Settings
from .. utils.property import get_ordinal
from .. utils.raycast import get_closest
from .. utils.registration import get_prefs
from .. utils.ui import finish_modal_handlers, force_obj_gizmo_update, get_mouse_pos, gizmo_selection_passthrough, ignore_events, init_modal_handlers, navigation_passthrough, init_status, finish_status, popup_message, force_ui_update, get_scale, draw_status_item, update_mod_keys
from .. utils.view import ensure_visibility, get_location_2d, restore_visibility, visible_get

from .. colors import white, yellow, green, red, blue, normal, orange
from .. items import merge_object_preset_items, alt

class Hype(bpy.types.Operator):
    bl_idname = "machin3.hype"
    bl_label = "MACHIN3: Hype"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            return [obj for obj in context.selected_objects if obj.type == 'MESH' and not obj.HC.ishyper and not (obj.library or (obj.data and obj.data.library))]

    @classmethod
    def description(cls, context, properties):
        unhyped = [obj for obj in context.selected_objects if obj.type == 'MESH' and not obj.HC.ishyper]

        return f"Turn Select{'ion' if len(unhyped) > 1 else 'ed'} into Hyper Object{'s' if len(unhyped) > 1 else ''}"

    def execute(self, context):
        unhyped =  [obj for obj in context.selected_objects if obj.type == 'MESH' and not obj.HC.ishyper]

        hyped = []
        nosort = []
        skipped_hyper = []
        skipped_gizmos = []

        for obj in unhyped:

            if len(obj.data.polygons) > 1000000:
                skipped_hyper.append(obj)

            else:
                obj.HC.ishyper = True

                if obj.HC.objtype == 'NONE':
                    obj.HC.objtype = 'CUBE'

                if (msg := setup_geo_gizmos(context, obj)) is True:
                    hyped.append(obj)

                    if not obj.HC.geometry_gizmos_show:
                        obj.HC.geometry_gizmos_show = True

                    if obj.HC.geometry_gizmos_edit_mode == 'SCALE':
                        obj.HC.geometry_gizmos_edit_mode = 'EDIT'

                else:
                    if 'Hyper Bevel' in msg:
                        continue

                    skipped_gizmos.append(obj)

            sorted = sort_modifiers(obj, preview=True, debug=False)

            if sorted == list(obj.modifiers):
                obj.HC.ismodsort = True

            else:
                obj.HC.ismodsort = False

                nosort.append(obj)

        force_obj_gizmo_update(context)

        if hyped or nosort or skipped_hyper or skipped_gizmos:
            text = []
            color = []

            time = 2

            if hyped:
                if len(hyped) == 1:
                    text.append(f"Hyped {hyped[0].name}")
                else:
                    text.append(f"Hyped {len(hyped)} objects")

                color.append(green)
                time += 1

            if skipped_gizmos:
                if len(skipped_gizmos) == 1:
                    text.append(f"Hyped {skipped_gizmos[0].name}")
                else:
                    text.append(f"Hyped {len(skipped_gizmos)} objects")

                text[-1] += ", but without geometry gizmos, as the face count is too high"
                color.append(yellow)
                time += 2

            if skipped_hyper:
                if len(skipped_hyper) == 1:
                    text.append(f"Hyping {skipped_hyper[0].name} was skipped")
                else:
                    text.append(f"Hyping {len(skipped_hyper)} objects was skipped")

                text[-1] += ", as the face count is way too high"
                color.append(red)
                time += 2

            if nosort:
                if len(hyped) == 1:
                    text.append(f"{nosort[0].name} will not be mod sorted by HyperCursor, unless manually enabled")
                else:
                    text.append(f"{len(nosort)} objects will not be mod sorted by HyperCursor, unless manually enabled")

                color.append(orange)
                time += 1

            draw_fading_label(context, text, color=color, alpha=1, move_y=time * 10, time=time)

        return {'FINISHED'}

class Unhype(bpy.types.Operator):
    bl_idname = "machin3.unhype"
    bl_label = "MACHIN3: Unhype"
    bl_description = "Turn Active into regular Object"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            active = context.active_object
            return active and active.HC.ishyper and not (active.library or active.data.library)

    def execute(self, context):
        active = context.active_object
        active.HC.ishyper = False

        force_obj_gizmo_update(context)

        draw_fading_label(context, f"Unhyped {active.name}", color=red, alpha=1, move_y=30, time=3)
        return {'FINISHED'}

class Parent(bpy.types.Operator):
    bl_idname = "machin3.parent"
    bl_label = "MACHIN3: Parent"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            return context.active_object in (sel := context.selected_objects) and len(sel) > 1

    @classmethod
    def description(cls, context, properties):
        if active := context.active_object:
            sel = [obj for obj in context.selected_objects if obj != context.active_object]
            desc = f"Parent the following objects to {active.name}"

            for obj in sel:
                desc += "\n • " + obj.name

            return desc

    def execute(self, context):
        sel = [obj for obj in context.selected_objects if obj != context.active_object]
        active = context.active_object

        if active.parent in sel:
            unparent(active)

        for obj in sel:
            parent(obj, active)

            obj.select_set(False)

        return {'FINISHED'}

class UnParent(bpy.types.Operator):
    bl_idname = "machin3.unparent"
    bl_label = "MACHIN3: Unparent"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            active = context.active_object
            return active and context.active_object.parent

    @classmethod
    def description(cls, context, properties):
        if active := context.active_object:
            desc = f"Unparent {active.name}"
            desc += f"\n\nALT: Reveal Parent Object {active.parent.name}"
            return desc

    def invoke(self, context, event):
        active = context.active_object

        if event.alt:
            bpy.ops.object.select_all(action='DESELECT')
            ensure_visibility(context, active.parent, select=True)

            context.view_layer.objects.active = active.parent
        else:
            unparent(active)
        return {'FINISHED'}

class Sort(bpy.types.Operator):
    bl_idname = "machin3.hyper_sort"
    bl_label = "MACHIN3: Hyper Sort"
    bl_description = "Sort Modifiers based on HyperCursor's principles and tools"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            active = context.active_object
            return active and active.HC.ishyper and active.HC.ismodsort

    def execute(self, context):
        active = context.active_object

        sort_modifiers(active)

        bpy.types.MACHIN3_OT_hyper_cursor_object.isunsorted = False
        return {'FINISHED'}

class PickObjectTreeGizmoManager:
    operator_data = {}

    gizmo_props = {}
    gizmo_data = {}

    def gizmo_poll(self, context):
        if context.mode == 'OBJECT':
            props = self.gizmo_props
            return props.get('area_pointer') == str(context.area.as_pointer()) and props.get('show')

    def gizmo_group_init(self, context):
        self.operator_data.clear()
        self.gizmo_props.clear()
        self.gizmo_data.clear()

        self.operator_data['active'] = self.active
        self.operator_data['affect_all_visible_only'] = self.affect_all_visible_only
        self.operator_data['select_finish'] = False

        self.gizmo_props['show'] = True
        self.gizmo_props['area_pointer'] = str(context.area.as_pointer())
        self.gizmo_props['warp_mouse'] = None

        self.gizmo_data['objects'] = []

        for idx, obj in enumerate(self.wire_children):
            mod = self.mod_map[obj] if obj in self.mod_map else None

            if obj.type == 'MESH' and [mod for mod in obj.modifiers if mod.type in ['MIRROR'] or is_array(mod)]:
                bbox = get_bbox(obj.data)[0]
            else:
                bbox = get_eval_bbox(obj)

            co = obj.matrix_world @ average_locations(bbox)
            co2d = get_location_2d(context, co, default='OFF_SCREEN')
            o = {'co': co,
                 'co2d': co2d,

                 'index': idx,

                 'objname': obj.name,
                 'modname': mod.name if mod else '',
                 'modhostobjname': mod.id_data.name if mod else '',

                 'select': False,
                 'remove': False,

                 'is_highlight': False,
                 'show': False,

                 'avoid_repulsion': False}

            o['show'] = self.is_obj_show(o)

            self.gizmo_data['objects'].append(o)

        context.window_manager.gizmo_group_type_ensure('MACHIN3_GGT_pick_object_tree')

    def gizmo_group_finish(self, context):
        self.operator_data.clear()
        self.gizmo_props.clear()
        self.gizmo_data.clear()

        context.window_manager.gizmo_group_type_unlink_delayed('MACHIN3_GGT_pick_object_tree')

def draw_pick_object_tree_status(op):
    def draw(self, context):
        layout = self.layout

        row = layout.row(align=True)
        row.label(text="Pick Object from Object Tree")

        if not op.highlighted:
            draw_status_item(row, key='LMB', text="Finish")

        draw_status_item(row, key='RMB', text="Cancel")

        row.separator(factor=10)

        draw_status_item(row, active=op.is_alt, key='ALT', text="Affect all")

        if op.is_alt:
            draw_status_item(row, active=op.affect_all_visible_only, key='V', text="Visible only", gap=1)

        row.separator(factor=2)

        if op.highlighted:
            row.label(text="", icon="RESTRICT_SELECT_OFF")
            row.label(text=op.highlighted['objname'])

            draw_status_item(row, key='F', text="Focus", gap=1)

        else:
            draw_status_item(row, key='F', text="Center Pick" if op.is_alt else "Focus on Active")

        if op.highlighted or op.is_alt:
            draw_status_item(row, key='S', text="Select + Finish", gap=2)

            select_entries, state = op.get_affected_gizmo_manager_entries('select')
            text = "Select" if state else "Hide"

            draw_status_item(row, key=['SHIFT', 'S'], text=text, gap=1)

            draw_status_item(row, key='D', text="Toggle Modifier", gap=2)
            draw_status_item(row, key='X', text="Remove", gap=2)

        draw_status_item(row, text="Show", gap=2)

        draw_status_item(row, active=op.show_names, key='N', text="Names", gap=1)

        if op.has_any_hypercut:
            draw_status_item(row, active=op.show_hypercut, key='C', text="Hyper Cuts", gap=1)

        if op.has_any_hyperbevel:
            draw_status_item(row, active=op.show_hyperbevel, key='B', text="Hyper Bevels", gap=1)

        if op.has_any_other:
            draw_status_item(row, active=op.show_other, key='O', text="Others", gap=1)

        if op.has_any_nonmodobjs:
            draw_status_item(row, active=op.show_nonmodobjs, key='M', text="Non-Mod Objects", gap=1)

        if op.has_any_alt_mod_host_obj:
            draw_status_item(row, active=op.show_alt_mod_host_obj, key='H', text="alt. Mod Hosts", gap=1)

        if op.highlighted and op.highlighted['modname']:
            draw_status_item(row, key='TAB', text="Switch to Hyper Mod", gap=2)

    return draw

class PickObjectTree(bpy.types.Operator, Settings, PickObjectTreeGizmoManager):
    bl_idname = "machin3.pick_object_tree"
    bl_label = "MACHIN3: Pick Object Tree"
    bl_description = "Pick Object from Object Tree"
    bl_options = {'REGISTER', 'UNDO'}

    show_names: BoolProperty(name="Show Names", default=True)
    show_alt_mod_host_obj: BoolProperty(name="Show Objects on alternative (non-active) Mod Host Objects", default=True)
    show_hyperbevel: BoolProperty(name="Show Hyper Bevels", default=False)
    show_hypercut: BoolProperty(name="Show Hyper Cuts", default=True)
    show_other: BoolProperty(name="Show Others Mod Objects", default=True)   # non hypercut and hyperbevel booeleans, but also mirror empties, etc
    show_nonmodobjs: BoolProperty(name="Show Non-Mod Objects", default=True)
    affect_all_visible_only: BoolProperty(name="Affect All Visible (only)", default=True)
    passthrough = None

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            active = context.active_object
            return active

    def draw_HUD(self, context):
        if context.area == self.area:
            if self.gizmo_props['show']:

                draw_init(self)

                if not self.highlighted:
                    dims = draw_label(context, title="Pick Object ", coords=Vector((self.HUD_x, self.HUD_y)), center=False, color=white, alpha=1)
                    dims += draw_label(context, title="in ", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, color=white, alpha=0.5)
                    dims += draw_label(context, title="Object Tree ", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, color=white, alpha=1)

                    if self.is_alt:
                        dims += draw_label(context, title="Affect All ", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, size=10, color=blue, alpha=1)

                        if self.affect_all_visible_only:
                            draw_label(context, title="Visible Only", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, size=10, color=white, alpha=0.5)

                    filters, on = self.get_filter_names()

                    if filters:
                        self.offset += 18

                        dims = draw_label(context, title="Show ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, size=10, color=white, alpha=0.5)
                        dims += draw_label(context, title=filters, coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, size=10, color=white, alpha=1)
                        dims += draw_label(context, title=" on ", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, size=10, color=white, alpha=0.5)
                        draw_label(context, title=on, coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, size=10, color=yellow, alpha=1)

                ui_system_scale, gizmo_size = get_scale(context, modal_HUD=False, gizmo_size=True)
                ui_modal_scale = get_scale(context, system_scale=False, modal_HUD=True, gizmo_size=False)

                for o in self.gizmo_data['objects']:
                    if o['show'] or (self.is_alt and not self.affect_all_visible_only) or o['remove']:
                        color, alpha = (red, 0.5) if o['remove'] else (white, 0.3)

                        if self.highlighted and o['is_highlight']:
                            obj = bpy.data.objects[o['objname']]

                            coords = o['co2d'] + Vector((-4.5, 4.5)) * gizmo_size * ui_system_scale * 1.25    # offset left and up based on gizmo size
                            coords += Vector((0, 12))                                                         # offset up to move into the row above the gizmos

                            dims = draw_label(context, title=f"{obj.name} ", coords=coords, center=False, size=12, color=color, alpha=1)

                            if not obj.visible_get() and (meta := self.obj_visibility_map[obj]['meta']) in ['SCENE', 'VIEWLAYER', 'HIDDEN_COLLECTION']:
                                if meta == 'SCENE':
                                    title = 'not in Scene '
                                elif meta == 'VIEWLAYER':
                                    title = 'not on View Layer '
                                else:
                                    title = 'in hidden Collection '

                                dims += draw_label(context, title=title, coords=coords + Vector((dims.x, 0)), center=False, size=10, color=orange, alpha=1)

                            if self.is_alt:
                                dims += draw_label(context, title="Affect All ", coords=coords + Vector((dims.x, 0)), center=False, size=10, color=blue, alpha=1)

                                if self.affect_all_visible_only:
                                    draw_label(context, title="Visible Only", coords=coords + Vector((dims.x, 0)), center=False, size=10, color=white, alpha=0.5)

                            if o['modhostobjname']:
                                coords = o['co2d'] + Vector((43, -3)) * gizmo_size * ui_system_scale          # offset to the right, next to the gizmos
                                size = 12 * (gizmo_size / ui_modal_scale)                                     # text in this row of the gizmo needs to adapt to discrepancies in gizmo_size vs modal_hud_scale, because there is text above it, which you shouldn't overlap!

                                mod = bpy.data.objects[o['modhostobjname']].modifiers[o['modname']]

                                dims = draw_label(context, title=" of ", coords=coords, center=False, size=size, color=white, alpha=0.5)
                                draw_label(context, title=o['modname'], coords=coords + Vector((dims.x, 0)), center=False, size=size, color=yellow, alpha=1 if mod.show_viewport else 0.3)

                                if o['modhostobjname'] != self.active.name:
                                    dims = get_text_dimensions(context, o['modname'], size=size)
                                    coords -= Vector((0, dims.y)) * 1.2                                      # offset down based on the text height, to move into row below gizmos

                                    dims = draw_label(context, title=" on ", coords=coords, center=False, size=size, color=white, alpha=0.5)
                                    draw_label(context, title=o['modhostobjname'], coords=coords + Vector((dims.x, 0)), center=False, size=size, color=normal, alpha=1)

                            if self.highlighted and o['objname'] in self.parenting_map:
                                lvl = self.parenting_map[o['objname']]
                                color = green if lvl == 1 else yellow
                                alpha = 1 if lvl == 1 else max(0.25, 1 - (0.25 * (lvl - 2)))                  # NOTE: lower the alpha down to the 5th level child, beyond that it will no longer be lowered

                                size = 12 * (gizmo_size / ui_modal_scale)                                     # text in this row of the gizmo, needs to adapt to discrepancies in gizmo_size vs modal_hud_scale, because there is text above it, which you shouldn't overlap! in effect, this removes influence of modal_HUD_scale, and gets the text size exclusively from the gizmo size
                                coords = o['co2d'] + Vector((-4.5, -3)) * gizmo_size * ui_system_scale        # offset to the left, next to the gizmos

                                text = f"{get_ordinal(self.parenting_map[o['objname']])} degree child"
                                dims = get_text_dimensions(context, f"{text} ", size=size)
                                coords -= Vector((dims.x, 0))                                                # offset to the left, based on text width

                                draw_label(context, title=text, coords=coords, center=False, size=size, color=color, alpha=alpha)

                        elif not self.highlighted:

                            coords = o['co2d'] + Vector((-4.5, 4.5)) * gizmo_size * ui_system_scale           # offset left and up based on gizmo size
                            coords += Vector((0, 10))                                                         # offset up to move into the row above the gizmos

                            if self.show_names or o['remove']:
                                draw_label(context, title=o['objname'], coords=coords, center=False, size=10, color=color, alpha=alpha)

                            if o['objname'] in self.parenting_map:
                                lvl = self.parenting_map[o['objname']]
                                size, color, alpha = (10, green, 1) if lvl == 1 else (9, yellow, max(0.25, 1 - (0.25 * (lvl - 2))))  # NOTE: lower the alpha down to the 5th level child, beyond that it will no longer be lowered

                                size *= (gizmo_size / ui_modal_scale)                                         # again text in this row of the gizmo needs to adapt to descrepancnies in gizmo_size vs modal_hud_scale
                                coords = o['co2d'] + Vector((-4.5, -3)) * gizmo_size * ui_system_scale        # offset to the left, next to the gizmos

                                text = str(lvl)
                                dims = get_text_dimensions(context, f"{text} ", size=size)
                                coords -= Vector((dims.x, 0))                                                # offset to the left, based on text width

                                draw_label(context, title=text, coords=coords, center=False, size=size, color=color, alpha=alpha)

                        batch = self.batches[o['objname']]

                        if '_CROSS' in batch[2]:
                            _, _, _, co2d, ui_scale = batch

                            if o['show']:
                                if o['is_highlight'] or self.is_alt:
                                    color = red if o['remove'] else blue

                                    if o['modhostobjname']:
                                        mod = bpy.data.objects[o['modhostobjname']].modifiers[o['modname']]
                                    else:
                                        mod = None

                                    if mod and mod.show_viewport or not mod:
                                        alpha = 1 if o['is_highlight'] else 0.2
                                    else:
                                        alpha = 0.2

                                    draw_circle(co2d, radius=10 * ui_scale, width=2 * ui_scale, color=color, alpha=alpha)

                            elif self.is_alt and not self.affect_all_visible_only:
                                color, alpha = (red, 0.1) if o['remove'] else (white, 0.05)

                                draw_circle(co2d, radius=10 * ui_scale, width=2 * ui_scale, color=color, alpha=alpha)

    def draw_VIEW3D(self, context):
        if context.area == self.area:

            if self.gizmo_props['show']:

                if self.highlighted or self.is_alt:
                    for o in self.gizmo_data['objects']:
                        if o['show']:
                            if o['is_highlight'] or self.is_alt:
                                batch = self.batches[o['objname']]

                                color = red if o['remove'] else blue

                                if len(batch) == 5:
                                    draw_batch(batch, color=color, width=2 * batch[4], alpha=0.2, xray=True)

                                else:
                                    draw_batch(batch, color=color, alpha=0.2, xray=True)

                                if o['is_highlight']:
                                    if o['modhostobjname']:
                                        mod = bpy.data.objects[o['modhostobjname']].modifiers[o['modname']]
                                    else:
                                        mod = None

                                    if mod and mod.show_viewport or not mod:
                                        if len(batch) == 5:
                                            draw_batch(batch, color=color, width=2 * batch[4], alpha=1, xray=True)
                                        else:
                                            draw_batch(batch, color=color, alpha=1, xray=False)

                                    if o['modhostobjname']!= self.active.name:
                                        if o['modhostobjname'] in self.batches:
                                            batch = self.batches[o['modhostobjname']]

                                            draw_batch(batch, color=normal, alpha=0.2 if mod and mod.show_viewport else 0.05, xray=True)

                            else:
                                color, alpha = (red, 0.5) if o['remove'] else (white, 0.3)
                                draw_point(o['co'], color=color, size=3, alpha=alpha)

                        elif self.is_alt and not (self.is_alt and self.affect_all_visible_only):
                                batch = self.batches[o['objname']]

                                color, alpha = (red, 0.1) if o['remove'] else (white, 0.05)

                                if len(batch) == 5:
                                    draw_batch(batch, color=color, width=2 * batch[4], alpha=alpha, xray=True)

                                else:
                                    draw_batch(batch, color=color, alpha=alpha, xray=True)

                for o in self.gizmo_data['objects']:
                    if not o['show'] and o['remove']:
                        draw_point(o['co'], color=red, size=3, alpha=0.5)

            else:
                for o in self.gizmo_data['objects']:
                    if o['show'] or o['remove']:
                        color, alpha = (red, 0.5) if o['remove'] else (white, 0.3)
                        draw_point(o['co'], color=color, size=3, alpha=alpha)

    def modal(self, context, event):
        if ignore_events(event):
            return {'RUNNING_MODAL'}

        context.area.tag_redraw()

        if self.operator_data['select_finish']:
            self.finish(context)
            self.save_settings()
            return {'FINISHED'}

        if self.is_alt_locked:
            if event.type in alt and event.value == 'PRESS':
                self.is_alt_locked = False

        if not self.is_alt_locked:
            update_mod_keys(self, event, shift=False, ctrl=False)

        update_mod_keys(self, event, ctrl=False, alt=False)

        events = ['MOUSEMOVE', 'F', 'N']

        if self.has_any_hyperbevel:
            events.append('B')

        if self.has_any_hypercut:
            events.append('C')

        if self.has_any_nonmodobjs:
            events.append('M')

        if self.has_any_other:
            events.append('O')

        if self.has_any_alt_mod_host_obj:
            events.append('H')

        if self.is_alt:
            events.append('V')

        self.highlighted = self.get_highlighted(context)

        if self.highlighted or self.is_alt:
            events.extend(['S', 'X'])

            if (self.highlighted and self.highlighted['modname']) or self.is_alt:
                events.append('D')

            if (self.highlighted and self.highlighted['modname']):
                events.append('TAB')

        if event.type in events:
            if event.type == 'MOUSEMOVE':
                if self.passthrough:
                    self.passthrough = False

                    for o in self.gizmo_data['objects']:
                        o['co2d'] = get_location_2d(context, o['co'], default='OFF_SCREEN')
                    self.repulse_2d_coords(context)

                    for objname, batch in self.batches.items():
                        if '_CROSS' in (batchtype := batch[2]):
                            obj = bpy.data.objects[objname]
                            mx = obj.matrix_world

                            batch = get_batch_from_matrix(mx, screen_space=50)

                            co2d = get_location_2d(context, mx.to_translation(), default='OFF_SCREEN')
                            self.batches[objname] = (*batch, batchtype, co2d, get_scale(context))

                    self.gizmo_props['show'] = True

                get_mouse_pos(self, context, event)

            elif event.type == 'N' and event.value == 'PRESS':
                self.show_names = not self.show_names

                force_ui_update(context)

            elif event.type == 'S' and event.value == 'PRESS':

                select_entries, state = self.get_affected_gizmo_manager_entries('select')

                if select_entries:
                    self.active.select_set(False)

                    if event.shift:

                        for o in select_entries:
                            o['select'] = state

                            obj = bpy.data.objects[o['objname']]

                            if state:
                                ensure_visibility(context, obj, select=True)

                            else:
                                restore_visibility(obj, self.obj_visibility_map[obj])

                                if obj.visible_get():
                                    obj.hide_set(True)

                        if state:

                            if self.highlighted:
                                context.view_layer.objects.active = bpy.data.objects[self.highlighted['objname']]

                            elif self.is_alt:
                                context.view_layer.objects.active = bpy.data.objects[select_entries[0]['objname']]

                        elif self.is_alt or not any(o['select'] for o in self.gizmo_data['objects']):

                            self.active.select_set(True)
                            context.view_layer.objects.active = self.active

                        if self.highlighted:
                            self.gizmo_props['warp_mouse'] = Vector((event.mouse_x, event.mouse_y))

                    else:
                        objects = [bpy.data.objects[o['objname']] for o in select_entries]
                        ensure_visibility(context, objects, select=True)

                        context.view_layer.objects.active = objects[0]

                        self.finish(context)
                        self.save_settings()
                        return {'FINISHED'}

            elif event.type == 'D' and event.value == 'PRESS':
                mod_entries, state = self.get_affected_gizmo_manager_entries('show_viewport')

                if mod_entries:
                    mods = [bpy.data.objects[o['modhostobjname']].modifiers[o['modname']] for o in mod_entries if o['modhostobjname']]

                    if mods:
                        state = not mods[0].show_viewport

                        for mod in mods:
                            mod.show_viewport = state

                    if self.highlighted:
                        self.gizmo_props['warp_mouse'] = Vector((event.mouse_x, event.mouse_y))

                    return {'RUNNING_MODAL'}

            elif event.type == 'X' and event.value == 'PRESS':
                delete_entries, state = self.get_affected_gizmo_manager_entries('remove')

                if delete_entries:

                    for o in delete_entries:
                        o['remove'] = state

                        if o['modhostobjname']:
                            mod_host_obj = bpy.data.objects[o['modhostobjname']]
                            mod = mod_host_obj.modifiers[o['modname']]

                            mod.show_viewport = not state

                    if self.highlighted:
                        self.gizmo_props['warp_mouse'] = Vector((event.mouse_x, event.mouse_y))

                return {'RUNNING_MODAL'}

            elif event.type == 'F' and event.value == 'PRESS':

                if event.alt:
                     bpy.ops.view3d.view_center_pick('INVOKE_DEFAULT')

                else:

                    if self.highlighted:
                        obj = bpy.data.objects[self.highlighted['objname']]

                        vis = visible_get(obj)

                        bpy.ops.object.select_all(action='DESELECT')
                        ensure_visibility(context, obj, select=True)

                        bpy.ops.view3d.view_selected('INVOKE_DEFAULT' if context.scene.HC.focus_mode == 'SOFT' else 'EXEC_DEFAULT')

                        restore_visibility(obj, vis)

                        self.active.select_set(True)

                    else:
                        bpy.ops.object.select_all(action='DESELECT')
                        self.active.select_set(True)
                        bpy.ops.view3d.view_selected('INVOKE_DEFAULT' if context.scene.HC.focus_mode == 'SOFT' else 'EXEC_DEFAULT')

                self.passthrough = True

                delay_execution(self.update_2d_coords, delay=0.2)
                return {'RUNNING_MODAL'}

            elif event.type == 'C' and event.value == 'PRESS':

                if event.shift:
                    self.show_hypercut = True
                    self.show_hyperbevel = False
                    self.show_other = False
                    self.show_nonmodobjs = False

                else:
                    self.show_hypercut = not self.show_hypercut

                for o in self.gizmo_data['objects']:
                    o['show'] = self.is_obj_show(o)

                force_ui_update(context)
                return {'RUNNING_MODAL'}

            elif event.type == 'B' and event.value == 'PRESS':

                if event.shift:
                    self.show_hypercut = False
                    self.show_hyperbevel = True
                    self.show_other = False
                    self.show_nonmodobjs = False

                else:
                    self.show_hyperbevel = not self.show_hyperbevel

                for o in self.gizmo_data['objects']:
                    o['show'] = self.is_obj_show(o)

                force_ui_update(context)
                return {'RUNNING_MODAL'}

            elif event.type == 'O' and event.value == 'PRESS':

                if event.shift:
                    self.show_hypercut = False
                    self.show_hyperbevel = False
                    self.show_other = True
                    self.show_nonmodobjs = False

                else:
                    self.show_other = not self.show_other

                for o in self.gizmo_data['objects']:
                    o['show'] = self.is_obj_show(o)

                force_ui_update(context)
                return {'RUNNING_MODAL'}

            elif event.type == 'M' and event.value == 'PRESS':

                if event.shift:
                    self.show_hypercut = False
                    self.show_hyperbevel = False
                    self.show_other = False
                    self.show_nonmodobjs = True

                else:
                    self.show_nonmodobjs = not self.show_nonmodobjs

                for o in self.gizmo_data['objects']:
                    o['show'] = self.is_obj_show(o)

                force_ui_update(context)
                return {'RUNNING_MODAL'}

            elif event.type == 'H' and event.value == 'PRESS':
                self.show_alt_mod_host_obj = not self.show_alt_mod_host_obj

                for o in self.gizmo_data['objects']:
                    o['show'] = self.is_obj_show(o)

                force_ui_update(context)
                return {'RUNNING_MODAL'}

            elif event.type == 'V' and event.value == 'PRESS':
                self.affect_all_visible_only = not self.affect_all_visible_only

                self.operator_data['affect_all_visible_only'] = self.affect_all_visible_only

                force_ui_update(context)
                return {'RUNNING_MODAL'}

            elif event.type == 'TAB' and event.value == 'PRESS':

                mod_host_obj = bpy.data.objects[self.highlighted['modhostobjname']]

                if mod_host_obj:
                    bpy.ops.object.select_all(action='DESELECT')

                    ensure_visibility(context, mod_host_obj, select=True)
                    context.view_layer.objects.active = mod_host_obj

                    self.finish(context)

                    self.save_settings()

                    bpy.ops.machin3.hyper_modifier('INVOKE_DEFAULT', is_gizmo_invocation=False, is_button_invocation=False, mode='PICK')
                    return {'FINISHED'}

        if navigation_passthrough(event, alt=False, wheel=True) and not event.alt:
            self.passthrough = True

            self.gizmo_props['show'] = False
            return {'PASS_THROUGH'}

        finish_events = ['SPACE']

        if not self.highlighted:
            finish_events.append('LEFTMOUSE')

        if event.type in finish_events and event.value == 'PRESS':

            if get_prefs().hide_pick_object_tree:
                for o in self.gizmo_data['objects']:
                    obj = bpy.data.objects[o['objname']]

                    if not o['select']:
                        if obj in self.hidden_wire_objects:
                            obj.hide_set(False)  # nothing fancy here, just hide_set() as was done in self.hide_wire_objects()

            self.remove_objects_and_mods_marked_for_deletion(debug=False)

            self.finish(context)
            self.save_settings()
            return {'FINISHED'}

        elif event.type in ['RIGHTMOUSE', 'ESC'] and event.value == 'PRESS':
            self.finish(context)

            for obj, vis in self.obj_visibility_map.items():
                restore_visibility(obj, vis)

            for mod, state in self.mod_show_viewport_map.items():
                mod.show_viewport = state

            self.active.select_set(True)
            context.view_layer.objects.active = self.active

            return {'CANCELLED'}

        if gizmo_selection_passthrough(self, event):
            return {'PASS_THROUGH'}

        return {'RUNNING_MODAL'}

    def finish(self, context):
        finish_modal_handlers(self)

        finish_status(self)

        restore_gizmos(self)

        self.gizmo_group_finish(context)

    def invoke(self, context, event):
        self.active = context.active_object

        self.dg = context.evaluated_depsgraph_get()

        self.wire_children, self.mod_map = self.get_wire_children(context, self.active, debug=False)

        if self.wire_children:
            self.init_settings(props=['show_names', 'affect_all_visible_only'])
            self.load_settings()

            self.area = context.area
            self.region = context.region
            self.region_data = context.region_data

            self.gizmo_group_init(context)

            self.init_batches_states_and_filters(context)

            self.repulse_2d_coords(context)

            self.hide_wire_objects()

            self.highlighted = None
            self.last_highlighted = None

            update_mod_keys(self)
            self.is_alt_locked = event.alt

            update_mod_keys(self)

            get_mouse_pos(self, context, event)

            hide_gizmos(self, context)

            init_status(self, context, func=draw_pick_object_tree_status(self))

            init_modal_handlers(self, context, area=False, hud=True, view3d=True)
            return {'RUNNING_MODAL'}

        else:
            draw_fading_label(context, text="Object Tree is Empty", y=120, color=red, alpha=1, move_y=20, time=2)
            return {'CANCELLED'}

        return {'FINISHED'}

    def get_wire_children(self, context, active, debug=False):
        obj_tree = []
        mod_dict = {}

        get_object_tree(active, obj_tree, mod_objects=True, mod_dict=mod_dict, find_disabled_mods=True, include_hidden=('SCENE', 'VIEWLAYER', 'COLLECTION'), debug=False)

        wire_children = []

        for obj in obj_tree:

            if is_wire_object(obj):

                if obj in active.children_recursive:
                    wire_children.append(obj)

                elif not obj.parent:
                    wire_children.append(obj)

                elif obj in mod_dict and any(mod.id_data == active for mod in mod_dict[obj]):
                    wire_children.append(obj)

        if active.type == 'CURVE' and (profile := active.data.bevel_object) and profile not in wire_children:
            wire_children.append(profile)

        if debug:
            print("\nwire children on", active.name)

            for obj in wire_children:
                print(obj.name)

        if debug:
            print("\nmod dict")

            for obj, mods in mod_dict.items():
                print(obj.name, [(mod.name, "on", mod.id_data) for mod in mods])

        mod_map = {}

        for obj, mods in mod_dict.items():
            if debug:
                print(obj.name, [mod.name for mod in mods])

            if len(mods) > 1:
                keep = sorted([mod for mod in mods if mod.id_data == active], key=lambda x: list(active.modifiers).index(x))

                if keep:
                    mod = keep[0]

                else:
                    mod = mods[0]

            else:
                mod = mods[0]

            mod_map[obj] = mod

        if debug:
            print("\nre-sorting wire children by index in mod stack of active")

        idx = 0

        for mod in active.modifiers:
            modobj = get_mod_obj(mod)

            if modobj and modobj in wire_children:
                current_index = wire_children.index(modobj)

                if debug:
                    print(mod.name, "with", modobj.name, "is", current_index)

                if idx != current_index:
                    if debug:
                        print("  index mismatch, moving to", idx)

                    wire_children.insert(idx, wire_children.pop(current_index))

                idx += 1

        if debug:
            print("\nsorted wire children")

            for obj in wire_children:
                mod = mod_map[obj] if obj in mod_map else None

                if mod:
                    print(obj.name, mod.name, "on", mod.id_data.name)
                else:
                    print(obj.name, None)

        return wire_children, mod_map

    def init_batches_states_and_filters(self, context):
        self.batches = {}

        self.mod_show_viewport_map = {}
        self.parenting_map = {}
        self.obj_visibility_map = {obj: visible_get(obj) for obj in self.wire_children}

        self.has_any_alt_mod_host_obj = False
        self.has_any_hyperbevel = False
        self.has_any_hypercut = False
        self.has_any_other = False
        self.has_any_nonmodobjs = False

        for idx, obj in enumerate(self.wire_children):
            mod = self.mod_map[obj] if obj in self.mod_map else None

            objname = obj.name
            modname = mod.name if mod else ''
            modhostobjname = mod.id_data.name if mod else ''

            if modname:
                if modhostobjname != self.active.name:
                    self.has_any_alt_mod_host_obj = True

                if 'Hyper Bevel' in modname:
                    self.has_any_hyperbevel = True

                elif 'Hyper Cut' in modname:
                    self.has_any_hypercut = True

                else:
                    self.has_any_other = True

                self.mod_show_viewport_map[mod] = mod.show_viewport

            else:
                self.has_any_nonmodobjs = True

            batch = get_batch_from_obj(self.dg, obj, cross_in_screen_space=50)

            if '_CROSS' in batch[2]:

                co2d = get_location_2d(context, obj.matrix_world.to_translation(), default='OFF_SCREEN')
                ui_scale = get_scale(context)

                self.batches[obj.name] = (*batch, co2d, ui_scale)

            else:
                self.batches[obj.name] = batch

            if obj.parent:
                parent = obj.parent

                if parent == self.active and not obj.children:
                    continue

                if parent not in [self.active] + self.active.children_recursive:
                    continue

                lvl = 0

                while True:
                    lvl +=1

                    if parent == self.active or not parent:
                        self.parenting_map[objname] = lvl
                        break

                    else:
                        obj = parent
                        parent = obj.parent

    def repulse_2d_coords(self, context, debug=False):
        def repulse(distance=50, debug=False):
            overlapping_points = {}

            for o in self.gizmo_data['objects']:

                repulse_from_list = []

                for o2 in self.gizmo_data['objects']:
                    if o != o2:

                        co_dir = o2['co2d'] - o['co2d']

                        if co_dir.length < distance - 1:
                            repulse_from_list.append(o2['co2d'])

                if repulse_from_list and not o['avoid_repulsion']:
                    overlapping_points[o['index']] = repulse_from_list
                    color = red

                else:
                    color = white

                if debug:
                    draw_circle(o['co2d'], radius=distance / 2, color=color, alpha=0.5, screen=True, modal=False)

            if overlapping_points:
                for idx, coords in overlapping_points.items():
                    o = self.gizmo_data['objects'][idx]

                    move_dir = Vector((0, 0))

                    for co in coords:
                        repulse_dir = o['co2d'] - co
                        move_dir += repulse_dir.normalized() * (distance - repulse_dir.length)

                    move_dir = move_dir / sqrt((len(coords) + 2.5))

                    if debug:
                        draw_vector(move_dir.resized(3), origin=o['co2d'].resized(3), fade=True, screen=True, modal=False)

                    repulse_co = o['co2d'] + move_dir

                    if debug:
                        draw_point(repulse_co.resized(3), color=green, size=2, screen=True, modal=False)
                        draw_circle(repulse_co.resized(3), radius=distance / 2, color=green, alpha=0.5, screen=True, modal=False)

                    o['co2d'] = repulse_co

                return True
            return False

        def avoid_perfect_overlap(debug=False):
            identical_2d_coords = {}

            for o in self.gizmo_data['objects']:
                co2d = tuple(o['co2d'])

                if co2d in identical_2d_coords:
                    identical_2d_coords[co2d].append(o)

                else:
                    identical_2d_coords[co2d] = [o]

            for os in identical_2d_coords.values():
                if len(os) > 1:
                    for idx, o in enumerate(os[1:]):
                        o['co2d'].y += 1 + idx

                        if debug:
                            print("avoiding perfect overlap for", o['objname'], "with", os[0]['objname'])

        if debug:
            print()
            print("repulsing 2d coords")

            from time import time
            start = time()

        iterations = 30

        ui_scale = get_scale(context)
        distance = 40 * ui_scale

        avoid_perfect_overlap(debug=False)

        for i in range(iterations):
            if debug:
                print("\niteration:", i)

            repulsed = repulse(distance=distance, debug=False)

            if not repulsed:
                if debug:
                    print(f" finished repulsing early after {i} iterations")

                break

        if debug:
            print(f"repulsion took {time() - start} seconds")

    def hide_wire_objects(self):
        self.hidden_wire_objects = []

        if get_prefs().hide_pick_object_tree:
            for obj in self.wire_children:

                if obj.visible_get():
                    obj.hide_set(True)
                    self.hidden_wire_objects.append(obj)

    def is_obj_show(self, o):
        if o['modname']:

            if o['modhostobjname'] != self.active.name:

                if not self.show_alt_mod_host_obj:
                    return False

            if 'Hyper Bevel' in o['modname']:
                return self.show_hyperbevel

            elif 'Hyper Cut' in o['modname']:
                return self.show_hypercut

            else:
                return self.show_other

        else:
            return self.show_nonmodobjs

    def get_highlighted(self, context):
        for o in self.gizmo_data['objects']:
            if o['show'] and o['is_highlight']:

                if o['modhostobjname']:
                    mod_host_obj = bpy.data.objects[o['modhostobjname']]
                    mod = mod_host_obj.modifiers[o['modname']]
                    mod_host_obj.modifiers.active = mod

                if o != self.last_highlighted:
                    self.last_highlighted = o
                    force_ui_update(context)

                return o

        if self.last_highlighted:
            self.last_highlighted = None
            force_ui_update(context)

    def update_2d_coords(self):
        for o in self.gizmo_data['objects']:
            o['co2d'] = Vector(round(i) for i in location_3d_to_region_2d(self.region, self.region_data, o['co'], default=Vector((-1000, -1000))))
        self.active.select_set(True)

    def get_affected_gizmo_manager_entries(self, prop):
        if self.highlighted:
            state_o = self.highlighted

        elif self.is_alt:
            if self.affect_all_visible_only:
                state_o = None

                for o in self.gizmo_data['objects']:
                    if o['show']:
                        state_o = o
                        break

                if not state_o:
                    return None, None

            else:
                state_o = self.gizmo_data['objects'][0]

        else:
            return None, None

        if self.is_alt:
            if self.affect_all_visible_only:
                entries = [o for o in self.gizmo_data['objects'] if o['show']]

            else:
                entries = [o for o in self.gizmo_data['objects']]
        else:
            entries = [state_o]

        if prop == 'show_viewport':
            if state_o['modname']:
                state = bpy.data.objects[state_o['modhostobjname']].modifiers.get(state_o['modname']).show_viewport
            else:
                state = False
        else:
            state = state_o.get(prop, False)

        return entries, not state

    def get_filter_names(self):
        filters = ''
        on = 'Active'

        if self.has_any_alt_mod_host_obj and self.show_alt_mod_host_obj:
            on += ' + alt. Mod Host Objs'

        if self.has_any_hypercut and self.show_hypercut:
            filters += 'Hyper Cuts'

        if self.has_any_hyperbevel and self.show_hyperbevel:
            filters += ' + Hyper Bevels'

        if self.has_any_other and self.show_other:
            filters += ' + Others'

        if self.has_any_nonmodobjs and self.show_nonmodobjs:
            filters += ' + Non-Mod Objects'

        if filters.startswith(' + '):
            filters = filters[3:]

        return filters, on

    def remove_objects_and_mods_marked_for_deletion(self, debug=False):
        if debug:
            print()
            print("deleting:")

        objects = set()

        for o in self.gizmo_data['objects']:
            if o['remove']:
                objects.add(bpy.data.objects[o['objname']])

        if objects:

            for obj in list(objects):
                objects.update(obj.children_recursive)

            for obj in objects:
                mods = is_mod_obj(obj)

                for mod in mods:
                    if debug:
                        print("removing mod", mod.name, "on", mod.id_data.name)

                    remove_mod(mod)

                if debug:
                    print("removing obj", obj.name)

                remove_obj(obj)

        else:
            if debug:
                print("no objects marked for deletion")

class TogglePickObjectTree(bpy.types.Operator, PickObjectTreeGizmoManager):
    bl_idname = "machin3.toggle_pick_object_tree"
    bl_label = "MACHIN3: Toggle Pick Object Tree"
    bl_options = {'REGISTER', 'UNDO'}

    index: IntProperty()
    mode: StringProperty()

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            return bool(PickObjectTreeGizmoManager().gizmo_data)

    @classmethod
    def description(cls, context, properties):
        if properties:
            o = PickObjectTreeGizmoManager.gizmo_data['objects'][properties.index]

            if properties.mode == 'SELECT':
                action = 'Select/Unhide'
                desc = f"{action} Object '{o['objname']}' and finish"
                desc += f"\nSHIFT: {action} Object '{o['objname']}' without finishing"
                desc += "\nALT: Affect All"

                desc += "\n\nShortcut: S and SHIFT + S"

            elif properties.mode == 'TOGGLE':
                if o['modhostobjname']:
                    mod_host_obj = bpy.data.objects[o['modhostobjname']]
                    mod = mod_host_obj.modifiers[o['modname']]

                    if mod:
                        action = 'Disable' if mod.show_viewport else 'Enable'
                        desc = f"{action} Modifier '{o['modname']}' on Object '{o['modhostobjname']}'"
                        desc += "\nALT: Affect All"

                        desc += "\n\nShortcut: D"

            elif properties.mode == 'REMOVE':
                action = "Keep" if o['remove'] else "Remove"
                desc = f"{action} Object '{o['objname']}' and all Modifiers using it"
                desc += "\nALT: Affect All"

                desc += "\n\nShortcut: X"

            return desc
        return "Invalid Context"

    def invoke(self, context, event):
        self.mouse_pos = Vector((event.mouse_x, event.mouse_y))
        self.gizmo_props['warp_mouse'] = self.mouse_pos

        update_mod_keys(self, event)

        return self.execute(context)

    def execute(self, context):
        opd = self.operator_data
        gd = self.gizmo_data

        self.highlighted = gd['objects'][self.index]

        if self.highlighted:
            if self.mode == 'SELECT':
                select_entries, state = self.get_affected_gizmo_manager_entries('select')

                if select_entries:
                    bpy.ops.object.select_all(action='DESELECT')

                    for o in select_entries:
                        o['select'] = state

                    for o in gd['objects']:
                        obj = bpy.data.objects[o['objname']]

                        obj.hide_set(not o['select'])

                        if o['select']:
                            obj.select_set(True)

                            if o == select_entries[0]:
                                context.view_layer.objects.active = obj

                    if not any(o['select'] for o in gd['objects']):
                        active = opd['active']
                        active.select_set(True)
                        context.view_layer.objects.active = active

                    if not self.is_shift and state:
                        opd['select_finish'] = True

                    return {'FINISHED'}

            elif self.mode == 'TOGGLE':
                mod_entries, state = self.get_affected_gizmo_manager_entries('show_viewport')

                mods = [bpy.data.objects[o['modhostobjname']].modifiers[o['modname']] for o in mod_entries if o['modhostobjname']]

                if mods:
                    for mod in mods:
                        mod.show_viewport = state

                    return {'FINISHED'}

            elif self.mode == 'REMOVE':
                delete_entries, state = self.get_affected_gizmo_manager_entries('remove')

                if delete_entries:
                    for o in delete_entries:
                        o['remove'] = state

                        if o['modhostobjname']:
                            mod_host_obj = bpy.data.objects[o['modhostobjname']]
                            mod = mod_host_obj.modifiers[o['modname']]

                            mod.show_viewport = not state

                    return {'FINISHED'}
        return {'CANCELLED'}

    def get_affected_gizmo_manager_entries(self, prop):
        opd = self.operator_data
        gd = self.gizmo_data

        state_o = self.highlighted

        if self.is_alt:
            if opd['affect_all_visible_only']:
                entries = [o for o in gd['objects'] if o['show']]

            else:
                entries = [o for o in gd['objects']]

        else:
            entries = [state_o]

        if prop == 'show_viewport':
            state = bpy.data.objects[state_o['modhostobjname']].modifiers.get(state_o['modname'], False).show_viewport

        else:
            state = state_o.get(prop, False)

        return entries, not state

class MergeObject(bpy.types.Operator):
    bl_idname = "machin3.merge_object"
    bl_label = "MACHIN3: merge_object"
    bl_options = {'REGISTER', 'UNDO'}

    index: IntProperty(name="Face Index")

    def update_merge_presets(self, context):
        if self.merge_presets == '11':
            self.merge_factor = 1
            self.cleanup_factor = 1
        elif self.merge_presets == '12':
            self.merge_factor = 1
            self.cleanup_factor = 2
        elif self.merge_presets == '1020':
            self.merge_factor = 10
            self.cleanup_factor = 20

    merge_presets: EnumProperty(name="Merge Presets", items=merge_object_preset_items, default='1020', update=update_merge_presets)
    merge_factor: FloatProperty(name="Merge Factor", default=10)
    cleanup_factor: FloatProperty(name="Cleanup Factor", default=20)
    redundant_edges: BoolProperty(name="Remove Redundant Edges", default=True)
    @classmethod
    def description(cls, context, properties):
        active = context.active_object

        desc = "Merge Object at chosen Face Gizmo"

        if active:
            if active.modifiers:
                desc += "\n\nNOTE: Object should not have modifiers, but currently has, preventing the merge"

            targets = [obj for obj in context.visible_objects if obj.type == 'MESH' and obj != active and obj.display_type not in ['WIRE', 'BOUNDS'] and not obj.modifiers]

            if not targets:
                desc += "\n\nNOTE: No viable Mesh Objects (without modifiers) closeby, merge not possible"

        return desc

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            active = context.active_object

            if active and not active.modifiers:
                return [obj for obj in context.visible_objects if obj.type == 'MESH' and obj != active and obj.display_type not in ['WIRE', 'BOUNDS'] and not obj.modifiers]

    def draw(self, context):
        layout = self.layout

        column = layout.column(align=True)

        row = column.split(factor=0.2, align=True)
        row.label(text='Presets')
        r = row.row(align=True)
        r.prop(self, 'merge_presets', expand=True)

        row = column.split(factor=0.21, align=True)
        row.label(text='Factor')
        row.prop(self, 'merge_factor', text='Merge')
        row.prop(self, 'cleanup_factor', text='Cleanup')

        row = column.split(factor=0.2, align=True)
        row.label(text='Remove')
        row.prop(self, 'redundant_edges', text='Redundant Edges', toggle=True)

    def execute(self, context):
        active = context.active_object

        if context.visible_objects:
            dg = context.evaluated_depsgraph_get()

            targets = [obj for obj in context.visible_objects if obj.type == 'MESH' and obj != active and obj.display_type not in ['WIRE', 'BOUNDS'] and not obj.modifiers]

            if targets:
                mx = active.matrix_world.copy()

                bm = bmesh.new()
                bm.from_mesh(active.data)
                bm.faces.ensure_lookup_table()

                face = bm.faces[self.index]

                face_origin = mx @ face.calc_center_median()

                merge_obj, _, hitco, hitno, _, distance = get_closest(dg, targets=targets, origin=face_origin, debug=False)

                if merge_obj and distance < 0.01:
                    merge_obj.select_set(True)

                    merge_depth = distance * self.merge_factor

                    corners = {v: None for v in face.verts}

                    face_edges = [e for e in face.edges]

                    for v in corners:

                        corner_edges = [(e, face.normal.dot((v.co - e.other_vert(v).co).normalized())) for e in v.link_edges if e not in face_edges]

                        if corner_edges:
                            best_edge = max(corner_edges, key=lambda x: x[1])[0]

                            corners[v] = (v.co - best_edge.other_vert(v).co).normalized()

                    local_hitco = mx.inverted_safe() @ hitco
                    local_hitno = mx.inverted_safe().to_3x3() @ hitno

                    for v, vdir in corners.items():
                        i = intersect_line_plane(v.co, v.co + vdir, local_hitco, local_hitno)

                        if i:
                            v.co = i

                    for v, vdir in corners.items():

                        v.co += vdir * merge_depth

                    bm.to_mesh(active.data)
                    bm.free()

                    mod = add_boolean(merge_obj, active, method='UNION', solver='EXACT')

                    context.view_layer.objects.active = merge_obj
                    apply_mod(mod)

                    remove_obj(active)

                    bm = bmesh.new()
                    bm.from_mesh(merge_obj.data)

                    cleanup_distance = distance * self.cleanup_factor

                    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=cleanup_distance)
                    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=cleanup_distance)

                    self.dissolve_redundant_geometry(bm, verts=True, edges=self.redundant_edges, redundant_angle=179.999)

                    edge_glayer, face_glayer = ensure_gizmo_layers(bm)

                    gangle = 20

                    for e in bm.edges:
                        if len(e.link_faces) == 2:
                            angle = get_face_angle(e)
                            e[edge_glayer] = angle >= gangle
                        else:
                            e[edge_glayer] = 1

                    for f in bm.faces:
                        if merge_obj.HC.objtype == 'CYLINDER' and len(f.edges) == 4:
                            f[face_glayer] = 0
                        elif not all(e[edge_glayer] for e in f.edges):
                            f[face_glayer] = 0
                        else:
                            f[face_glayer] = any([get_face_angle(e, fallback=0) >= gangle for e in f.edges])

                    bm.to_mesh(merge_obj.data)
                    bm.free()

                    context.area.tag_redraw()

                    bpy.ops.machin3.draw_active_object(time=2, alpha=0.7)
                    return {'FINISHED'}

                else:
                    popup_message(["No viable merge object found!", "Note, that both objects should not have any modifiers."])

        return {'CANCELLED'}

    def dissolve_redundant_geometry(self, bm, verts=True, edges=True, redundant_angle=179.999):
        if edges:
            manifold_edges = [e for e in bm.edges if e.is_manifold]

            redundant_edges = []

            for e in manifold_edges:
                angle = get_face_angle(e, fallback=0)

                if angle < 180 - redundant_angle:
                    redundant_edges.append(e)

            bmesh.ops.dissolve_edges(bm, edges=redundant_edges, use_verts=False)

            two_edged_verts = {v for e in redundant_edges if e.is_valid for v in e.verts if len(v.link_edges) == 2}
            bmesh.ops.dissolve_verts(bm, verts=list(two_edged_verts))

        if verts:
            two_edged_verts = [v for v in bm.verts if len(v.link_edges) == 2]

            redundant_verts = []

            for v in two_edged_verts:
                e1 = v.link_edges[0]
                e2 = v.link_edges[1]

                vector1 = e1.other_vert(v).co - v.co
                vector2 = e2.other_vert(v).co - v.co

                angle = min(degrees(vector1.angle(vector2)), 180)

                if redundant_angle < angle:
                    redundant_verts.append(v)

            bmesh.ops.dissolve_verts(bm, verts=redundant_verts)

class DuplicateObjectTree(bpy.types.Operator):
    bl_idname = "machin3.duplicate_object_tree"
    bl_label = "MACHIN3: Duplicate Object Tree"
    bl_options = {'REGISTER', 'UNDO'}

    instance: BoolProperty(name="Instance", default=False)
    include_mirrors: BoolProperty(name="Include Mirrors", default=False)
    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            return context.active_object and context.active_object.select_get()

    @classmethod
    def description(cls, context, properties):
        desc = "Duplicate Object with its entire Object Tree\nThe Object Tree includes all recursive Children and all recursive Modifier Objects"

        desc += "\n\nALT: Instance instead of Duplicate"
        desc += "\nSHIFT: Include Mirror Objects"
        return desc

    def draw(self, context):
        layout = self.layout
        column = layout.column()

        column.prop(self, 'instance', toggle=True)

    def invoke(self, context, event):
        self.instance = event.alt
        self.include_mirrors = event.shift
        return self.execute(context)

    def execute(self, context):
        active = context.active_object

        obj_tree = [active]

        get_object_tree(active, obj_tree, mod_objects=True, mod_type_ignore=[] if self.include_mirrors else ['MIRROR'], include_hidden=('VIEWLAYER', 'COLLECTION'), debug=False)

        duplicate_objects(context, obj_tree, linked=self.instance, debug=False)

        action = "Instanced" if self.instance else "Duplicated"
        draw_fading_label(context, text=[f"{action} {len(obj_tree)} Objects", "You can move them now"], color=[yellow if self.instance else green, white], alpha=[1, 0.5], move_y=40, time=4)
        return {'FINISHED'}

class HideWireObjects(bpy.types.Operator):
    bl_idname = "machin3.hide_wire_objects"
    bl_label = "MACHIN3: Hide Wire Objects"
    bl_description = "Hide all visible Wire Objects"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def execute(self, context):
        dg = context.evaluated_depsgraph_get()

        active = active if (active := context.active_object) and active.select_get() else None

        self.hidden_count = 0
        self.sorted_count = 0

        if wire_objects := self.get_wire_objects(context):

            if get_prefs().hide_wire_collection_sort:

                scene_collections = get_scene_collections(context, debug=False)
                mcol = context.scene.collection

                mcol_objects = [obj for obj in wire_objects if mcol in obj.users_collection]

                for obj in mcol_objects:
                    if obj.select_get():
                        obj.select_set(False)

                dg.update()

                for obj in mcol_objects:
                    mcol.objects.unlink(obj)

                    if not any(col in scene_collections for col in obj.users_collection):
                        self.wcol = get_wires_collection(context)
                        self.wcol.objects.link(obj)

                        self.sorted_count += 1

                for obj in wire_objects:
                    if obj.visible_get():
                        obj.hide_set(True)

                        self.hidden_count += 1

            else:

                for obj in wire_objects:
                    obj.hide_set(True)

                self.hidden_count = len(wire_objects)

        if active in wire_objects:

            if active.parent:
                parent = active.parent

                while parent:
                    if parent.visible_get():
                        parent.select_set(True)
                        context.view_layer.objects.active = parent
                        self.draw_summary(context)
                        return {'FINISHED'}

                    parent = parent.parent

            else:
                arrays = remote_radial_array_poll(context, active)

                for obj in arrays:
                    if obj.visible_get():
                        obj.select_set(True)
                        context.view_layer.objects.active = obj
                        self.draw_summary(context)
                        return {'FINISHED'}

                mirrors = remote_mirror_poll(context, active)

                for obj in mirrors:
                    if obj.visible_get():
                        obj.select_set(True)
                        context.view_layer.objects.active = obj
                        self.draw_summary(context)
                        return {'FINISHED'}

        self.draw_summary(context)

        return {'FINISHED'}

    def draw_summary(self, context):
        msg = []
        color = []
        alpha = []

        if self.sorted_count:
            msg.append(f"Sorted {self.sorted_count} Objects into {self.wcol.name} Collection")
            color.append(green)
            alpha.append(1)

        if self.hidden_count:
            msg.append(f"Hidden {self.hidden_count} Objects")
            color.append(white)
            alpha.append(0.5)

        if msg:
            draw_fading_label(context, msg, color=color, alpha=alpha, move_y=len(msg) * 2 * 10, time=len(msg) * 2)

    def get_wire_objects(self, context):
        if get_prefs().hide_wire_collection_sort:
            wire_objects = [obj for obj in context.scene.objects if is_wire_object(obj)]

        else:
            wire_objects = [obj for obj in context.visible_objects if is_wire_object(obj)]

        if HC.get_addon('MACHIN3tools'):
            wire_objects = [obj for obj in wire_objects if not (obj.type == 'EMPTY' and (is_group_empty(obj)) or is_group_anchor(obj))]

        if HC.get_addon('MESHmachine'):
            wire_objects = [obj for obj in wire_objects if not (obj.type == 'MESH' and is_plug_handle(obj))]

        return wire_objects

class HideMirrorObj(bpy.types.Operator):
    bl_idname = "machin3.hide_mirror_obj"
    bl_label = "MACHIN3: (Un)Hide Mirror"
    bl_description = ""
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        active = context.active_object

        data = active.HC.get('hyperbevelmirror')

        if data:
            name = data.get('name')
            vis = data.get('visible')

            if cutter := bpy.data.objects.get(name):
                restore_visibility(cutter, vis)

                del active.HC['hyperbevelmirror']

                return {'FINISHED'}
        return {'CANCELLED'}
