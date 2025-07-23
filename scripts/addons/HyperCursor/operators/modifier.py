import bpy
from bpy.props import EnumProperty, StringProperty, BoolProperty, IntProperty, FloatProperty
from bpy_extras.view3d_utils import location_3d_to_region_2d

import bmesh
from mathutils import Vector

from math import degrees, radians, cos, sin
from uuid import uuid4

from .. import HyperCursorManager as HC

from .. utils.application import delay_execution
from .. utils.bmesh import ensure_default_data_layers, ensure_edge_glayer, ensure_gizmo_layers, get_face_angle
from .. utils.draw import draw_circle, draw_batch, draw_point, draw_init, draw_label, draw_line, draw_fading_label, draw_vector, draw_pie_circle, get_text_dimensions
from .. utils.gizmo import hide_gizmos, restore_gizmos
from .. utils.math import average_locations, dynamic_format
from .. utils.mesh import join, unhide_deselect
from .. utils.modifier import add_displace, add_solidify, add_source, add_subdivision, add_weld, get_boolean_solver_string, get_edges_from_edge_bevel_mod_vgroup, get_edges_from_edge_bevel_mod_weight, get_mod_input, get_previous_mod, is_array, is_edge_bevel, is_radial_array, is_source, remove_mod, add_boolean, move_mod, remote_boolean_poll, get_mod_obj, set_boolean_solver, set_mod_input, set_mod_prefix, sort_modifiers, is_remote_mod_obj, get_new_mod_name, get_prefix_from_mod, get_mod_base_name, is_auto_smooth, is_hyper_array
from .. utils.object import duplicate_obj_recursively, flatten, get_batch_from_matrix, get_batch_from_obj, get_bbox, get_min_dim, hide_render, is_valid_object, is_wire_object, meshcut, parent, remove_obj, unparent, get_eval_bbox, get_object_tree, remove_unused_children, setup_split_boolean
from .. utils.operator import Settings
from .. utils.property import step_list
from .. utils.raycast import get_closest
from .. utils.registration import get_prefs
from .. utils.select import get_edges_as_vert_sequences
from .. utils.ui import draw_status_item_precision, finish_modal_handlers, force_obj_gizmo_update, get_mouse_pos, get_mousemove_divisor, get_zoom_factor, gizmo_selection_passthrough, ignore_events, init_modal_handlers, navigation_passthrough, popup_message, init_status, finish_status, scroll, scroll_up, scroll_down, force_ui_update, get_scale, is_key, update_mod_keys, warp_mouse, wrap_mouse, draw_status_item
from .. utils.vgroup import get_vgroup_index
from .. utils.view import ensure_visibility, get_location_2d, restore_visibility, visible_get
from .. utils.workspace import get_3dview_space_from_context

from .. items import alt, boolean_method_items, extended_boolean_solver_items, boolean_color_mappings
from .. colors import yellow, red, white, green, blue, normal, grey, orange

def draw_add_boolean_status(op):
    def draw(self, context):
        layout = self.layout

        row = layout.row(align=True)

        if op.is_adjusting:
            row.label(text="Adjust Boolean Gap")

            row.separator(factor=10)

            draw_status_item_precision(row, fine=op.is_shift, coarse=op.is_ctrl, gap=10)

            precision = 2 if op.is_shift else 0 if op.is_ctrl else 1
            draw_status_item(row, key='T', text="Gap", prop=dynamic_format(op.gap_strength, decimal_offset=precision), gap=1)

        else:
            row.label(text="Add Boolean")

            draw_status_item(row, key='LMB', text="Finish")
            draw_status_item(row, key='MMB', text="Viewport")
            draw_status_item(row, key='RMB', text="Cancel")

            row.separator(factor=10)

            draw_status_item(row, key='MMB_SCROLL', text="Active", prop=op.active.name)

            draw_status_item(row, key='MOVE', text="Operation", prop=op.method.title(), gap=2)

            if op.method not in ['NONE', 'MESHCUT']:
                draw_status_item(row, key='E', text="Solver", prop=op.solver_HUD, gap=2)

            if op.method == 'GAP':
                precision = 2 if op.is_shift else 0 if op.is_ctrl else 1
                draw_status_item(row, key='T', text="Gap", prop=dynamic_format(op.gap_strength, decimal_offset=precision), gap=2)

            draw_status_item(row, active=op.wireframe, key='W', text="Wireframe", gap=2)

            if op.method not in ['NONE', 'MESHCUT']:
                draw_status_item(row, key='TAB', text="Finish + Invoke HyperMod", gap=2)

    return draw

class AddBoolean(bpy.types.Operator):
    bl_idname = "machin3.add_boolean"
    bl_label = "MACHIN3: Add Boolean"
    bl_options = {'REGISTER', 'UNDO'}

    method: EnumProperty(name="Method", items=boolean_method_items, default="NONE")
    solver: EnumProperty(name="Solver", items=extended_boolean_solver_items, default="MANIFOLD" if bpy.app.version >= (4, 5, 0) else "FAST")
    gap_strength: FloatProperty(name="Gap", description="Displace Strength used on Gap Objects")

    wireframe: BoolProperty(name="Wireframe", default=True)
    passthrough = None
    is_button_invocation: BoolProperty(name="Invoke operator from Sidebar Button", default=False)
    is_sidebar_invocation: BoolProperty(name="Invoke operator from Popup Panel Button", default=False)
    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            sel = [obj for obj in context.selected_objects if obj.type == 'MESH']
            return len(sel) >= 2

    @classmethod
    def description(cls, context, properties):
        sel = [obj for obj in context.selected_objects if obj.type == 'MESH']
        desc = f"Add Boolean Mod{'s' if {len(sel) > 2} else ''}"
        return desc

    def draw_HUD(self, context):
        if context.area == self.area:
            draw_init(self)

            if self.passthrough:
                return

            if self.is_adjusting:
                dims = draw_label(context, title="Adjust ", coords=Vector((self.HUD_x, self.HUD_y)), center=False, color=orange, alpha=1)
                dims += draw_label(context, title="Gap ", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, color=white, alpha=1)

                if self.is_shift or self.is_ctrl:
                    title = "a little" if self.is_shift else "a lot"
                    draw_label(context, title=title, coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, size=10, center=False, alpha=0.5)

                precision = 2 if self.is_shift else 0 if self.is_ctrl else 1

                self.offset += 18

                dims = draw_label(context, title="Strength: ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=0.5)
                draw_label(context, title=dynamic_format(self.gap_strength, decimal_offset=precision), coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=yellow, alpha=1)

            else:

                dims = draw_label(context, title="Boolean ", coords=Vector((self.HUD_x, self.HUD_y)), center=False, color=white, alpha=1)
                dims += draw_label(context, title=self.method.title(), coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, color=boolean_color_mappings[self.method], alpha=0.5 if self.method == 'NONE' else 1)

                dims += draw_label(context, title=" on ", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, size=10, color=white, alpha=0.3)
                draw_label(context, title=self.active.name, coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, color=white, alpha=0.5)

                if self.method not in ['NONE', 'MESHCUT']:
                    self.offset += 18

                    dims = draw_label(context, title="Solver: ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=0.5)
                    draw_label(context, title=self.solver_HUD, coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=yellow, alpha=1)

                if self.wireframe:
                    self.offset += 18

                    draw_label(context, title="Wireframe", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=blue, alpha=1)

                init_mouse = self.init_mouse.resized(3)

                draw_vector(self.flick_vector.resized(3), origin=init_mouse, fade=True, alpha=1)

                pies = len(self.methods)
                active, active_color = (self.methods.index(self.method), boolean_color_mappings[self.method])if self.method in self.methods else (-1, white)

                draw_pie_circle(init_mouse, radius=self.flick_distance, pies=pies, active=active, rot_offset=180, width=3, color=white, active_color=active_color, gap=self.flick_gap, alpha=0.05, active_alpha=0.5)

    def draw_VIEW3D(self, context):
        if context.area == self.area:

            if self.wireframe:
                color = boolean_color_mappings[self.method]

                if self.method == 'NONE':
                    if self.active in self.batches:
                        batch = self.batches[self.active]
                        factor = self.get_alpha_factor(len(batch[0]))

                        draw_batch(batch, color=color, alpha=0.1 * factor, xray=True)
                        draw_batch(batch, width=2, color=color, alpha=0.3 * factor, xray=False)

                else:
                    for obj in self.operands:
                        if obj in self.batches:
                            batch = self.batches[obj]
                            factor = self.get_alpha_factor(len(batch[0]))

                            draw_batch(batch, color=color, alpha=0.1 * factor, xray=True)
                            draw_batch(batch, width=2, color=color, alpha=0.3 * factor, xray=False)

    def modal(self, context, event):
        if ignore_events(event):
            return {'RUNNING_MODAL'}

        context.area.tag_redraw()

        if event.type == 'MOUSEMOVE':
            if self.passthrough:
                self.passthrough = False

                self.factor = get_zoom_factor(context, depth_location=self.active.location, scale=1, ignore_obj_scale=False)

                warp_mouse(self, context, self.stored_mouse, warp_hud=False)
                return {'RUNNING_MODAL'}

            get_mouse_pos(self, context, event, hud=False)    # NOTE: HUD_x and HUD_y are only initiated once in invoke(), not in the modal, as the HUD is static in this tool

        if self.method == 'GAP':

            self.update_adjust_mode(context, event, 'T')

            if self.is_adjusting:
                wrap_mouse(self, context, x=True, wrap_hud=False)

                update_mod_keys(self, event)

                delta_x = self.mouse_pos.x - self.last_mouse.x
                divisor = get_mousemove_divisor(event, normal=1, shift=20, ctrl=0.1, sensitivity=1)

                self.gap_strength += delta_x * (self.factor / divisor)

                for obj in self.operands:
                    gap = self.booleans[obj]['gap']

                    if gap and (displace := gap.modifiers.get('Displace (Gap)')):
                        displace.strength = self.gap_strength

                self.last_mouse = self.mouse_pos

                if not self.has_gap_strength_been_adjusted:
                    self.has_gap_strength_been_adjusted = True

                return {'RUNNING_MODAL'}

        events = ['MOUSEMOVE', 'W']

        if self.method not in ['NONE', 'MESHCUT']:
            events.extend(['E', 'TAB'])

        if event.type in events or scroll(event, key=True):

            if event.type == 'MOUSEMOVE':

                self.flick_vector = self.mouse_pos - self.init_mouse

                method = self.get_flick_method()

                if method != self.method:
                    self.method = method

                    self.setup_booleans()

                if self.flick_vector.length > self.flick_distance:
                    self.finish(context)

                    active, cutters = self.finish_booleans(context)

                    bpy.ops.object.select_all(action='DESELECT')

                    for obj in cutters:
                        obj.hide_set(True)

                    context.view_layer.objects.active = active
                    active.select_set(True)
                    return {'FINISHED'}

            elif event.type == 'TAB' and event.value == 'PRESS':
                self.finish(context)

                _, cutters = self.finish_booleans(context)

                bpy.ops.object.select_all(action='DESELECT')

                for obj in cutters:
                    obj.hide_set(True)

                context.view_layer.objects.active = self.active
                self.active.select_set(True)

                bpy.ops.machin3.hyper_modifier('INVOKE_DEFAULT', is_gizmo_invocation=False, is_button_invocation=False, mode='PICK')

                return {'FINISHED'}

            elif scroll(event, key=True):
                if scroll_down(event, key=True):
                    new_active = step_list(self.active, self.sel, step=1, loop=True)

                else:
                    new_active = step_list(self.active, self.sel, step=-1, loop=True)

                self.active = new_active
                self.operands = [obj for obj in self.sel if obj != new_active]

                context.view_layer.objects.active = new_active

                self.setup_booleans(clear=True)

                self.factor = get_zoom_factor(context, depth_location=self.active.location, scale=1, ignore_obj_scale=False)

            elif  event.type == 'E' and event.value == 'PRESS':
                self.solver = step_list(self.solver, [s[0] for s  in extended_boolean_solver_items], step=-1 if event.shift else 1)

                for solver, description, _ in extended_boolean_solver_items:
                    if solver == self.solver:
                        self.solver_HUD = description
                        break

                for obj, data in self.booleans.items():
                    mod = data.get('mod')

                    if mod:
                        set_boolean_solver(mod, self.solver)

            elif event.type == 'W' and event.value == 'PRESS':
                self.wireframe = not self.wireframe

                force_ui_update(context)

        if navigation_passthrough(event):
            self.passthrough = True

            self.stored_mouse = self.mouse_pos

            return {'PASS_THROUGH'}

        elif event.type in ['LEFTMOUSE', 'SPACE']:
            self.finish(context)

            active, cutters = self.finish_booleans(context)

            if self.method not in ['NONE', 'MESHCUT']:

                bpy.ops.object.select_all(action='DESELECT')

                if event.type == 'LEFTMOUSE':
                    context.view_layer.objects.active = cutters[0]
                    cutters[0].select_set(True)

                else:
                    for obj in cutters:
                        obj.hide_set(True)

                    context.view_layer.objects.active = active
                    active.select_set(True)

            return {'FINISHED'}

        elif event.type in ['RIGHTMOUSE', 'ESC'] and event.value == 'PRESS':
            self.finish(context)

            self.undo_booleans(context)

            return {'CANCELLED'}

        self.last_mouse = self.mouse_pos

        return {'RUNNING_MODAL'}

    def finish(self, context):
        finish_modal_handlers(self)

        finish_status(self)

        restore_gizmos(self)

    def invoke(self, context, event):
        self.dg = context.evaluated_depsgraph_get()

        get_mouse_pos(self, context, event)

        if self.is_button_invocation:
            self.warp_mouse_out_of_panel(context)

        self.get_selection(context)

        self.get_initial_states()

        self.populate_batches()

        self.method = 'NONE'

        self.get_available_boolean_methods()

        self.solver = 'MANIFOLD' if bpy.app.version >= (4, 5) else 'FAST'
        self.solver_HUD = self.solver.title()

        self.booleans = {}

        self.ui_scale = get_scale(context)
        self.flick_distance = get_prefs().cast_flick_distance * self.ui_scale
        self.flick_gap = 0.25

        self.HUD_x += get_prefs().cast_flick_distance * 1.1
        self.HUD_y += get_prefs().cast_flick_distance

        self.init_mouse = self.mouse_pos
        self.stored_mouse = self.mouse_pos

        self.last_mouse = self.mouse_pos

        self.flick_vector = self.mouse_pos - self.init_mouse

        self.factor = get_zoom_factor(context, depth_location=self.active.location, scale=1, ignore_obj_scale=False)

        update_mod_keys(self)

        self.is_adjusting = False

        self.has_gap_strength_been_adjusted = False

        hide_gizmos(self, context)

        init_status(self, context, func=draw_add_boolean_status(self))

        force_ui_update(context)

        init_modal_handlers(self, context, hud=True, view3d=True)
        return {'RUNNING_MODAL'}

    def warp_mouse_out_of_panel(self, context):
        distance = None

        HUD_width = get_text_dimensions(context, "Boolean Difference on Cube", size=12).x

        if self.is_sidebar_invocation:
            for region in context.area.regions:
                if region.type == 'UI':
                    distance = - (region.width - (context.region.width - self.mouse_pos.x) + (get_prefs().cast_flick_distance * get_scale(context)) + HUD_width)

        else:
            if self.mouse_pos.x < context.region.width / 2:
                distance = (300 * get_scale(context)) + (get_prefs().cast_flick_distance * get_scale(context))

            else:
                distance = - ((150 * get_scale(context)) + (get_prefs().cast_flick_distance * get_scale(context)) + HUD_width)

        if distance:
            warp_mouse(self, context, Vector((self.mouse_pos.x + distance, self.mouse_pos.y)))

    def get_selection(self, context):
        self.active = context.active_object if context.active_object and context.active_object.type == 'MESH' else None
        self.sel = [obj for obj in context.selected_objects if obj.type == 'MESH']

        if self.active and self.active not in self.sel or self.active is None:
            context.view_layer.objects.active = self.sel[0]
            self.active = context.active_object

        self.operands = [obj for obj in self.sel if obj != self.active]

    def get_initial_states(self):
        self.initial = {}

        for obj in self.sel:
            self.initial[obj] = {'is_active': obj == self.active,
                                 'display_type': obj.display_type}

    def populate_batches(self):
        self.batches = {}

        for obj in self.sel:
            self.batches[obj] = get_batch_from_obj(self.dg, obj)

    def get_available_boolean_methods(self):
        prefs = get_prefs()

        self.methods = []

        if prefs.boolean_method_difference:
            self.methods.append('DIFFERENCE')

        if prefs.boolean_method_split:
            self.methods.append('SPLIT')

        if prefs.boolean_method_intersect:
            self.methods.append('INTERSECT')

        if prefs.boolean_method_union:
            self.methods.append('UNION')

        if prefs.boolean_method_gap:
            self.methods.append('GAP')

        if prefs.boolean_method_meshcut:
            self.methods.append('MESHCUT')

    def get_flick_method(self):
        if self.flick_vector.length > self.flick_distance * self.flick_gap:
            flick = self.flick_vector.normalized()

            left_dir = Vector((-1, 0))

            methods = []

            for idx, method in enumerate(self.methods):

                x, y = left_dir
                theta = radians(idx * (360 / len(self.methods)))

                x_rot = x * cos(theta) - y * sin(theta)
                y_rot = x * sin(theta) + y * cos(theta)

                method_dir = Vector((x_rot, y_rot))

                dot = flick.dot(method_dir)

                methods.append((dot, method))

            return max(methods, key=lambda d: d[0])[1]

        else:
            return 'NONE'

    def get_alpha_factor(self, vert_count, debug=False):
        factor = 1

        if vert_count < 50:
            factor /= 1

        elif vert_count < 500:
            factor /= 2

        elif vert_count < 500:
            factor /= 4

        elif vert_count < 5000:
            factor /= 6

        elif vert_count < 50000:
            factor /= 8

        else:
            factor /= 10

        if debug:
            print("vert count:", vert_count, " > ", factor)

        return factor

    def update_adjust_mode(self, context, event, key):
        is_key(self, event, key, debug=False)

        if event.type == key:
            if event.value == 'PRESS' and not self.is_adjusting:
                context.window.cursor_set('SCROLL_X')

                self.stored_mouse = self.mouse_pos

                force_ui_update(context)

            elif event.value == 'RELEASE':
                context.window.cursor_set('DEFAULT')

                warp_mouse(self, context, self.stored_mouse, warp_hud=False)

                force_ui_update(context)

        self.is_adjusting = getattr(self, f"is_{key.lower()}")

    def setup_booleans(self, clear=False):
        def setup_difference(obj):
            data = self.booleans.get(obj)

            if data:
                mod = data.get('mod')
                gap = data.get('gap')

                if not mod:
                    mod = add_boolean(self.active, obj, method=self.method, solver=self.solver)
                    data['mod'] = mod

            else:

                mod = add_boolean(self.active, obj, method=self.method, solver=self.solver)
                gap = None

                data = {'mod': mod,
                        'gap': gap}

                self.booleans[obj] = data

            mod.name = 'Difference'

            if not mod.show_viewport:
                mod.show_viewport = True

            if mod.operation != 'DIFFERENCE':
                mod.operation = 'DIFFERENCE'

            if mod.object != obj:
                mod.object = obj

            if obj.display_type != 'WIRE':
                obj.display_type = 'WIRE'

            if not obj.visible_get():
                obj.hide_set(False)
                obj.select_set(True)

            if gap and gap.visible_get():
                gap.hide_set(True)

        def setup_union(obj):
            data = self.booleans.get(obj)

            if data:
                mod = data.get('mod')
                gap = data.get('gap')

                if not mod:
                    mod = add_boolean(self.active, obj, method=self.method, solver=self.solver)
                    data['mod'] = mod

            else:

                mod = add_boolean(self.active, obj, method=self.method, solver=self.solver)
                gap = None

                data = {'mod': mod,
                        'gap': gap}

                self.booleans[obj] = data

            mod.name = 'Union'

            if not mod.show_viewport:
                mod.show_viewport = True

            if mod.operation != 'UNION':
                mod.operation = 'UNION'

            if mod.object != obj:
                mod.object = obj

            if obj.display_type != 'WIRE':
                obj.display_type = 'WIRE'

            if obj.visible_get():
                obj.hide_set(True)

            if gap and gap.visible_get():
                gap.hide_set(True)

        def setup_intersect(obj):
            data = self.booleans.get(obj)

            if data:
                mod = data.get('mod')
                gap = data.get('gap')

                if not mod:
                    mod = add_boolean(self.active, obj, method=self.method, solver=self.solver)
                    data['mod'] = mod

            else:

                mod = add_boolean(self.active, obj, method=self.method, solver=self.solver)
                gap = None

                data = {'mod': mod,
                        'gap': gap}

                self.booleans[obj] = data

            mod.name = 'Insersect'

            if not mod.show_viewport:
                mod.show_viewport = True

            if mod.operation != 'INTERSECT':
                mod.operation = 'INTERSECT'

            if mod.object != obj:
                mod.object = obj

            if obj.display_type != 'WIRE':
                obj.display_type = 'WIRE'

            if not obj.visible_get():
                obj.hide_set(False)
                obj.select_set(True)

            if gap and gap.visible_get():
                gap.hide_set(True)

        def setup_split(obj):
            data = self.booleans.get(obj)

            if data:
                mod = data.get('mod')
                gap = data.get('gap')

                if not mod:
                    mod = add_boolean(self.active, obj, method=self.method, solver=self.solver)
                    data['mod'] = mod

            else:

                mod = add_boolean(self.active, obj, method=self.method, solver=self.solver)
                gap = None

                data = {'mod': mod,
                        'gap': gap}

                self.booleans[obj] = data

            mod.name = 'Split (Difference)'

            if mod.show_viewport:
                mod.show_viewport = False

            if mod.operation != 'DIFFERENCE':
                mod.operation = 'DIFFERENCE'

            if mod.object != obj:
                mod.object = obj

            if obj.display_type != 'WIRE':
                obj.display_type = 'WIRE'

            if not obj.visible_get():
                obj.hide_set(False)
                obj.select_set(True)

            if gap and gap.visible_get():
                gap.hide_set(True)

        def setup_gap(obj):
            def create_gap_object(obj):
                gap = obj.copy()
                gap.name = f"{obj.name}_gap"
                gap.display_type = 'WIRE'

                gap.modifiers.clear()

                add_source(gap, obj)

                add_displace(gap, name="Displace (Gap)", mid_level=0, strength=self.gap_strength)

                for col in obj.users_collection:
                    col.objects.link(gap)
                    gap.select_set(False)

                return gap

            data = self.booleans.get(obj)

            if data:
                mod = data.get('mod')
                gap = data.get('gap')

                if not gap:
                    gap = create_gap_object(obj)
                    data['gap'] = gap

                if not mod:
                    mod = add_boolean(self.active, gap, method=self.method, solver=self.solver)
                    data['mod'] = mod

            else:

                gap = create_gap_object(obj)

                mod = add_boolean(self.active, gap, method=self.method, solver=self.solver)

                data = {'mod': mod,
                        'gap': gap}

                self.booleans[obj] = data

            mod.name = 'Gap (Difference)'

            if not mod.show_viewport:
                mod.show_viewport = True

            if mod.operation != 'DIFFERENCE':
                mod.operation = 'DIFFERENCE'

            if mod.object != gap:
                mod.object = gap

            if obj.display_type != (init := self.initial[obj]['display_type']):
                obj.display_type = init

            if not obj.visible_get():
                obj.hide_set(False)
                obj.select_set(True)

            if gap and not gap.visible_get():
                gap.hide_set(False)
                gap.select_set(False)

        def setup_meshcut(obj):
            if obj.display_type != 'WIRE':
                obj.display_type = 'WIRE'

            data = self.booleans.get(obj)

            if data:
                mod = data.get('mod')
                gap = data.get('gap')

                if mod and mod.show_viewport:
                    mod.show_viewport = False

                if gap and gap.visible_get():
                    gap.hide_set(True)

                if not obj.visible_get():
                    obj.hide_set(False)
                    obj.select_set(True)

        def setup_none(obj):
            if obj.display_type != (init := self.initial[obj]['display_type']):
                obj.display_type = init

            data = self.booleans.get(obj)

            if data:
                mod = data.get('mod')
                gap = data.get('gap')

                if mod and mod.show_viewport:
                    mod.show_viewport = False

                if not obj.visible_get():
                    obj.hide_set(False)
                    obj.select_set(True)

                if gap and gap.visible_get():
                    gap.hide_set(True)

        if clear:

            if self.active.display_type != (init := self.initial[self.active]['display_type']):
                self.active.display_type = init

            if not self.active.visible_get():
                self.active.hide_set(False)

            if self.booleans:
                for obj, data in self.booleans.items():
                    mod = data.get('mod')

                    if mod:
                        remove_mod(mod)
                        data['mod'] = None

                    gap = data.get('gap')

                    if gap and gap.visible_get():
                        gap.hide_set(True)

        if not self.active.select_get():
            self.active.select_set(True)

        if self.method == 'GAP' and not self.has_gap_strength_been_adjusted:

            averaged = sum([sum([d for d in get_bbox(obj.data)[2] if d]) / 3 for obj in self.operands]) / len(self.operands)

            self.gap_strength = averaged / 20

        for obj in self.operands:
            if self.method == 'DIFFERENCE':
                setup_difference(obj)

            elif self.method == 'UNION':
                setup_union(obj)

            elif self.method == 'INTERSECT':
                setup_intersect(obj)

            elif self.method == 'SPLIT':
                setup_split(obj)

            elif self.method == 'GAP':
                setup_gap(obj)

            elif self.method == 'MESHCUT':
                setup_meshcut(obj)

            elif self.method == 'NONE':
                setup_none(obj)

    def finish_booleans(self, context):
        active = None
        cutters = []

        if self.method == 'NONE':
            self.undo_booleans(context)
            return active, cutters

        if self.method == 'MESHCUT':
            self.undo_booleans(context)

            meshcut(context, self.active, self.operands)
            return active if active else self.active, cutters

        elif self.method == 'SPLIT':

            for obj, data in self.booleans.items():
                if obj in self.operands:
                    mod = data.get('mod')

                    if mod:

                        avoid_mods = [mo for ob in self.operands if ob != obj and (mo := self.booleans[ob].get('mod'))] if len(self.operands) > 1 else None

                        split = setup_split_boolean(context, mod, avoid_mods=avoid_mods)

                        cutters.append(split['dup']['cutter'])  # NOTE, we add the dup cutter first, as this is the one we may select, just like when hyper cut splitting
                        cutters.append(split['orig']['cutter'])

                        if active is None:
                            active = split['dup']['host']

                        sort_modifiers(split['dup']['host'])

                gap = data.get('gap')

                if gap:
                    remove_obj(gap)

        elif self.method == 'GAP':
            for obj, data in self.booleans.items():
                gap = data.get('gap')

                if obj in self.operands:
                    parent(obj, self.active)

                    if gap:
                        parent(gap, obj)

                        cutters.append(gap)

                else:
                    remove_obj(gap)

        else:
            for obj, data in self.booleans.items():

                if obj in self.operands:
                    parent(obj, self.active)

                gap = data.get('gap')

                if gap:
                    remove_obj(gap)

            cutters = self.operands

            if self.method == 'UNION':
                for obj in cutters:
                    obj.hide_set(False)

        hide_render(cutters, True)

        sort_modifiers(self.active)

        return active if active else self.active, cutters

    def undo_booleans(self, context):
        for obj in self.sel:
            if obj.display_type != (init := self.initial[obj]['display_type']):
                obj.display_type = init

            if not obj.visible_get():
                obj.hide_set(False)

            if self.method != 'MESHCUT':
                if self.initial[obj]['is_active']:
                    if self.active != obj:
                        context.view_layer.objects.active = obj

        for obj, data in self.booleans.items():
            mod = data.get('mod')

            if mod:
                remove_mod(mod)

            gap = data.get('gap')

            if gap:
                remove_obj(gap)

class CollapseBooleans(bpy.types.Operator):
    bl_idname = "machin3.collapse_booleans"
    bl_label = "MACHIN3: Collapse Booleans"
    bl_description = "Collapse Booleans"
    bl_options = {'REGISTER', 'UNDO'}

    index: IntProperty(name="Index")

    @classmethod
    def poll(cls, context):
        return False

    def execute(self, context):
        active = context.active_object

        mods = list(active.modifiers)

        stacks = []
        stack = []

        for idx, mod in enumerate(mods):

            if mod.type in ['BOOLEAN', 'WELD']:

                moddict = {'type': mod.type,
                           'name': mod.name,
                           'index': idx,
                           'hide': not mod.show_viewport}

                if not stack:
                    moddict['previous'] = get_previous_mod(mod)

                if mod.type == 'BOOLEAN':
                    moddict['object'] = mod.object
                    moddict['operation'] = mod.operation
                    moddict['solver'] = mod.solver

                    if mod.solver == 'EXACT':
                        moddict['use_self'] = mod.use_self
                        moddict['use_hole_tolerant'] = mod.use_hole_tolerant

                elif mod.type == 'WELD':
                    moddict['mode'] = mod.mode
                    moddict['merge_threshold'] = mod.merge_threshold

                stack.append(moddict)
                remove_mod(mod)

            elif stack:
                stacks.append(stack)
                stack = []

        if stack:
            stacks.append(stack)

        for idx, mods in enumerate(stacks):
            print(idx)

            mod = active.modifiers.new(name="Collapsed Boolean", type="NODES")

            prev = mods[0]['previous']

            if prev:
                index = list(active.modifiers).index(prev) + 1
                move_mod(mod, index=index)

            else:
                move_mod(mod, index=0)

            tree = bpy.data.node_groups.new('Collapsed Boolean', type='GeometryNodeTree')
            tree.interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
            tree.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

            input = tree.nodes.new(type='NodeGroupInput')

            prev = input

            for moddict in mods:

                if moddict['type'] == 'BOOLEAN':
                    node = tree.nodes.new(type='GeometryNodeMeshBoolean')
                    node.operation = moddict['operation']

                    is_exact = moddict['solver'] == 'EXACT'

                    if is_exact:
                        node.solver = 'EXACT'

                        node.inputs[2].default_value = moddict['use_self']
                        node.inputs[3].default_value = moddict['use_hole_tolerant']
                    objnode = tree.nodes.new(type='GeometryNodeObjectInfo')
                    objnode.transform_space = 'RELATIVE'
                    objnode.inputs[0].default_value = moddict['object']
                    objnode.location = prev.location - Vector((0, 230))

                    tree.links.new(objnode.outputs[4], node.inputs[1])
                    tree.links.new(prev.outputs[0], node.inputs[0 if node.operation == 'DIFFERENCE' else 1])

                elif moddict['type'] == 'WELD':
                    node = tree.nodes.new(type='GeometryNodeMergeByDistance')
                    node.mode = moddict['mode']
                    node.inputs[2].default_value = moddict['merge_threshold']
                    tree.links.new(prev.outputs[0], node.inputs[0])

                node.label = moddict['name']
                node.location = prev.location + Vector((300, 0))
                prev = node

            output = tree.nodes.new(type='NodeGroupOutput')
            output.location = prev.location + Vector((300, 0))

            tree.links.new(prev.outputs[0], output.inputs[0])

            mod.node_group = tree

        return {'FINISHED'}

class MacroBooleanManager:
    selection = {}
    booleans = {}
    snapping = {}

    def boolean_poll(self):
        return self.selection and self.booleans and self.snapping

    def boolean_init(self, context, duplicate=False):
        self.selection.clear()
        self.booleans.clear()
        self.snapping.clear()

        active = context.active_object
        parent = active.parent

        children = [obj for obj in active.children_recursive]

        self.selection['is_duplicate'] = duplicate
        self.selection['active'] = active
        self.selection['parent'] = parent
        self.selection['children'] = children
        self.selection['dup_map'] = []

        parent_mods = list(parent.modifiers)
        booleans = [mod for mod in parent.modifiers if mod.type == 'BOOLEAN' and mod.object in [active] + children]

        for mod in booleans:
            self.booleans[mod.name] = {'object': mod.object,

                                       'index': parent_mods.index(mod),
                                       'operation': mod.operation,
                                       'solver': mod.solver,

                                       'use_self': mod.use_self,
                                       'use_hole_tolerant': mod.use_hole_tolerant,
                                       'double_threshold': mod.double_threshold,

                                       'show_in_editmode': mod.show_in_editmode,
                                       'show_viewport': mod.show_viewport,
                                       'show_render': mod.show_render}

        ts = context.scene.tool_settings
        self.snapping['snap_elements'] = ts.snap_elements
        self.snapping['snap_target'] = ts.snap_target
        self.snapping['use_snap_backface_culling'] = ts.use_snap_backface_culling
        self.snapping['use_snap_align_rotation'] = ts.use_snap_align_rotation
        self.snapping['use_snap_peel_object'] = ts.use_snap_peel_object
        self.snapping['use_snap_grid_absolute'] = ts.use_snap_grid_absolute
        self.snapping['use_snap_translate'] = ts.use_snap_translate
        self.snapping['use_snap_rotate'] = ts.use_snap_rotate
        self.snapping['use_snap_scale'] = ts.use_snap_scale

    def boolean_finish(self, context):
        self.selection.clear()
        self.booleans.clear()
        self.snapping.clear()

class InitBooleanTranslateOnParent(bpy.types.Operator, MacroBooleanManager):
    bl_idname = "machin3.init_boolean_translate_on_parent"
    bl_label = "MACHIN3: Init Boolean Translate on Parent"
    bl_description = "Initialize translation of boolean operand object, so it can be surface snapped, before actually moving it (via Macro)"
    bl_options = {'INTERNAL'}

    duplicate: BoolProperty(name="Duplicate", description="Duplicate-Translate instead of just Translating", default=False)
    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            active = context.active_object

            if active:
                is_wire = is_wire_object(active, empty=False, instance_collection=False, curve=False)
                sel = context.selected_objects

                if active.parent and is_wire and active in sel and len(sel) == 1:

                    booleans = [mod for mod in active.parent.modifiers if mod.type == 'BOOLEAN' and mod.object == active]
                    return booleans

    def execute(self, context):
        self.boolean_init(context, duplicate=self.duplicate)

        if self.duplicate:
            dg = context.evaluated_depsgraph_get()
            self.selection['dup_map'] = duplicate_obj_recursively(context, dg, context.active_object)

        else:
            for modname in self.booleans:
                mod = self.selection['parent'].modifiers.get(modname)

                if mod:
                    remove_mod(mod)

        self.setup_surface_snapping(context)

        return {'FINISHED'}

    def setup_surface_snapping(self, context):
        ts = context.scene.tool_settings

        ts.snap_elements = {'FACE'}
        ts.snap_target = 'MEDIAN'

        ts.use_snap_backface_culling = False
        ts.use_snap_align_rotation = True
        ts.use_snap_peel_object = False

        ts.use_snap_translate = True
        ts.use_snap_rotate = False
        ts.use_snap_scale = False

class RestoreBooleanOnParent(bpy.types.Operator, MacroBooleanManager):
    bl_idname = "machin3.restore_boolean_on_parent"
    bl_label = "MACHIN3: Restore Boolean on Parent"
    bl_description = "Restore Boolean Modifiers, after the boolean operand object has been moved"
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and context.active_object

    def execute(self, context):
        if self.boolean_poll():
            active = context.active_object
            parent_obj= self.selection['parent']

            has_parent_changed = False

            if context.visible_objects:
                dg = context.evaluated_depsgraph_get()

                exclude_objs = [active] + list(active.children_recursive)

                if self.selection['is_duplicate']:
                    active_orig = self.selection['active']
                    exclude_objs.extend([active_orig] + list(active_orig.children_recursive))

                targets = [obj for obj in context.visible_objects if obj.type == 'MESH' and not is_wire_object(obj) and obj not in exclude_objs]
                closest, _, _, _, _, _ = get_closest(dg, targets=targets, origin=active.matrix_world.to_translation(), debug=False)

                if closest and closest != parent_obj:
                    parent_obj = closest
                    has_parent_changed = True

            self.restore_booleans(parent_obj, has_parent_changed)

            if has_parent_changed:
                parent(active, parent_obj)

                for obj_orig in [self.selection['active']] + self.selection['children']:
                    obj = self.selection['dup_map'][obj_orig] if self.selection['is_duplicate'] else obj_orig

                    mirrors = [mod for mod in obj.modifiers if get_mod_obj(mod) == self.selection['parent']]

                    for mod in mirrors:
                        remove_mod(mod)

            self.restore_snapping(context)

            self.boolean_finish(context)
            return {'FINISHED'}

        else:
            print("WARNING: Boolean Macro could not restore boolean mods")
            self.boolean_finish(context)
            return {'CANCELLED'}

    def restore_booleans(self, parent_obj, has_parent_changed=False):
        is_duplicate = self.selection['is_duplicate']
        dup_map = self.selection['dup_map']

        for name, data in self.booleans.items():

            operand_obj = dup_map[data['object']] if is_duplicate else data['object']

            mod = add_boolean(parent_obj, operand_obj, method=data['operation'], solver=data['solver'])
            mod.name = name

            mod.use_self = data['use_self']
            mod.use_hole_tolerant = data['use_hole_tolerant']
            mod.double_threshold = data['double_threshold']

            mod.show_in_editmode = data['show_in_editmode']
            mod.show_viewport = data['show_viewport']
            mod.show_render = data['show_render']

            if has_parent_changed:
                sort_modifiers(parent_obj)

            else:
                index = data['index']

                if is_duplicate:
                    index += len(self.booleans)

                move_mod(mod, index)

    def restore_snapping(self, context):
        ts = context.scene.tool_settings

        for prop, data in self.snapping.items():
            setattr(ts, prop, data)

def draw_hyper_mod_status(op):
    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)

        mode = op.mode

        mod = op.mod
        modtype = mod.type.replace('SOLIDIFY', 'SHELL').title()

        show_mod = mod.show_viewport
        modobj = get_mod_obj(mod)
        prefix = get_prefix_from_mod(mod)

        mods = list(op.active.modifiers)
        modidx = mods.index(mod)

        is_moving = op.is_moving

        is_d = op.is_d
        is_adjusting = op.is_adjusting

        action = "Add" if mode == 'ADD' else "Move" if is_moving else "Enable" if is_d and show_mod else "Disable" if is_d and not show_mod else "Adjust" if is_adjusting else "Pick"
        row.label(text=f"{action} Modifier")

        if is_adjusting:
            row.separator(factor=10)
            row.label(text=mod.name)

            if mod.type == 'SUBSURF':
                draw_status_item(row, key='T', text="Levels", prop=mod.levels, gap=2)
                draw_status_item(row, active=op.subd_affect_render, key='B', text="Affect Both, Levels + Render Levels", gap=2)

            else:
                draw_status_item_precision(row, fine=op.is_shift, coarse=op.is_ctrl, gap=2)

                precision = 2 if op.is_shift else 0 if op.is_ctrl else 1

                if mod.type == 'WELD':
                    draw_status_item(row, key='T', text="Threshold", prop=dynamic_format(mod.merge_threshold, decimal_offset=precision), gap=2)

                elif mod.type == 'DISPLACE':
                    draw_status_item(row, key='T', text="Strength", prop=dynamic_format(mod.strength, decimal_offset=precision), gap=2)

                elif mod.type == 'SOLIDIFY':
                    draw_status_item(row, key='T', text="Thickness", prop=dynamic_format(mod.thickness, decimal_offset=precision), gap=2)

                elif is_auto_smooth(mod):
                    angle = degrees(get_mod_input(mod, 'Angle'))
                    draw_status_item(row, key='T', text="Angle", prop=dynamic_format(angle, decimal_offset=precision), gap=2)

        else:

            if mode == 'ADD' and len(mods) > len(op.cancel_remove_mods):
                draw_status_item(row, key='LMB', text="Continue in Pick Mode")
                draw_status_item(row, key='SPACE', text="Finish")

            else:
                draw_status_item(row, key='LMB', text="Finish")

            draw_status_item(row, key='MMB', text="Viewport")
            draw_status_item(row, key='RMB', text="Cancel")

            row.separator(factor=10)

            draw_status_item(row, key='MMB_SCROLL' if mode == 'ADD' or is_moving else 'ALT', text="Move in Stack", gap=2)

            if not (mode == 'ADD' or is_moving):
                draw_status_item(row, key='MMB_SCROLL', text="Select Mod", gap=2)

            if mode == 'ADD':
                if op.active.HC.ismodsort:
                    draw_status_item(row, active=bool(prefix), key='Q', text="Use Prefix", gap=2)

                draw_status_item(row, text=f"Adding {modtype}", gap=4)

                if mod.type == 'WELD':
                    draw_status_item(row, active=False, key='D', text="Displace")
                    draw_status_item(row, active=False, key='S', text="Shell")

                elif mod.type == 'DISPLACE':
                    draw_status_item(row, active=False, key='W', text="Weld")
                    draw_status_item(row, active=False, key='S', text="Shell")

                elif mod.type == 'SOLIDIFY':
                    draw_status_item(row, active=False, key='W', text="Weld")
                    draw_status_item(row, active=False, key='D', text="Displace")
                    draw_status_item(row, active=bool(op.preceding_mods and len(op.preceding_mods) == 2), key='S', text="Preceding SubDs")

                    if modidx > 0:
                        draw_status_item(row, active=bool(op.preceding_mods and len(op.preceding_mods) == 1), key=['SHIFT', 'W'], text="Preceding Weld")

                draw_status_item(row, text="Jump to", gap=4)
                draw_status_item(row, key='G', text="Top in Stack")
                draw_status_item(row, key=['SHIFT', 'G'], text="Bottom in Stack", gap=1)

            if mode == 'PICK':
                if op.active.HC.ismodsort:
                    draw_status_item(row, active=bool(prefix), key='Q', text="Cycle Prefix", prop=prefix, gap=2)

                if prefix:
                    draw_status_item(row, key=['SHIFT', 'Q'], text="Remove Prefix", gap=2)

                if not is_d:
                    draw_status_item(row, active=show_mod, key='D', text='Disable' if show_mod else 'Enable', gap=2)

                draw_status_item(row, active=mods[0].show_viewport, key='A', text='Disable All' if mods[0].show_viewport else 'Enable All', gap=2)

                action = 'Un-Delete' if mod in op.deleted else 'Delete'
                draw_status_item(row, active=mod not in op.deleted, key='X', text=action, gap=2)

                if op.wire_mod_objects:
                    action = 'Hide' if op.wire_mod_objects[0].visible_get() else 'Unhide'
                    draw_status_item(row, key=['SHIFT', 'A'], text=f"{action} Wire Mod Objs", gap=1)

                if op.can_apply_mods:
                    text = "Apply All (visible) Mods"
                    if not op.has_disabled_mods:
                        text += ' + Finish'

                    draw_status_item(row, key=['CTRL', 'A'], text=text, gap=1)

                if modobj:
                    draw_status_item(row, key='S', text="Select Mod Object", gap=2)
                    draw_status_item(row, key=['SHIFT', 'S'], text="Select Mod Object (keep active selected)", gap=1)

                    draw_status_item(row, key='F', text="Focus on Mod Object", gap=2)
                    draw_status_item(row, key=['SHIFT', 'F'], text="Focus on Active Object", gap=1)

                if (smooth := is_auto_smooth(mod)) or mod.type in ['WELD', 'DISPLACE', 'SOLIDIFY', 'BOOLEAN', 'SUBSURF']:
                    modtype = 'Auto Smooth' if smooth else mod.type.title().replace('Solidify', 'Shell')

                    draw_status_item(row, text=f"{modtype}:", gap=4)

                    if mod.type == 'WELD':
                        draw_status_item(row, key='C', text="Mode", prop=mod.mode.title(), gap=1)
                        draw_status_item(row, key='T', text="Threshold", prop=dynamic_format(mod.merge_threshold), gap=1)

                    elif mod.type == 'DISPLACE':
                        draw_status_item(row, key='T', text="Strength", prop=dynamic_format(mod.strength), gap=1)

                    elif mod.type == 'SOLIDIFY':
                        draw_status_item(row, active=mod.use_even_offset, key='E', text="Even", gap=1)
                        draw_status_item(row, key='T', text="Thickness", prop=dynamic_format(mod.thickness), gap=1)

                    elif mod.type == 'BOOLEAN':
                        solver = mod.solver.title()

                        if mod.use_self:
                            solver += ", Self Intersection"

                        if mod.use_hole_tolerant:
                            solver += f"{' + ' if mod.use_self else ', '}Hole Tolerant"

                        draw_status_item(row, key='E', text="Solver", prop=solver, gap=1)

                        if 'Hyper Bevel' in mod.name:
                            draw_status_item(row, key=['ALT', 'E'], text="Extend", gap=1)

                    elif mod.type == 'SUBSURF':
                        draw_status_item(row, key='T', text="Levels", prop=mod.levels, gap=1)
                        draw_status_item(row, active=False, text="Render", prop=mod.render_levels, gap=1)

                        if mod.subdivision_type == 'CATMULL_CLARK':
                            draw_status_item(row, active=mod.boundary_smooth == 'PRESERVE_CORNERS', key='C', text="Keep Corners", gap=2)

                    elif is_auto_smooth(mod):
                        angle = degrees(get_mod_input(mod, 'Angle'))
                        draw_status_item(row, key='T', text="Angle", prop=dynamic_format(angle, decimal_offset=1), gap=1)

                if mod.use_pin_to_last:
                    draw_status_item(row, key='P', text="Unpin", gap=2)

                if op.can_tab_finish:

                    if is_edge_bevel(mod):
                        action = "Edit Edge Bevel"

                    elif 'Hyper Bevel' in mod.name:
                        action = "Edit Hyper Bevel"

                    elif mod.type == 'BOOLEAN':
                        action = "Pick Object Tree"

                    elif mod.type == 'SOLIDIFY':
                        action = "Adjust Shell"

                    elif mod.type == 'DISPLACE':
                        action = "Adjust Displace"

                    elif is_array(mod):
                        action = "Adjust Array"

                    draw_status_item(row, key='TAB', text=f"Switch to {action}", gap=2)

    return draw

class HyperMod(bpy.types.Operator, Settings):
    bl_idname = "machin3.hyper_modifier"
    bl_label = "MACHIN3: Hyper Mod"
    bl_options = {'REGISTER', 'UNDO'}

    mode: StringProperty(name="Mode", default='ADD')
    is_moving: BoolProperty(name="Move the picked Modifier", default=False)
    is_double_subd: BoolProperty(name="Add Double SubD before Shell mod", default=False)
    subd_affect_render: BoolProperty(name="Affect Render Levels too", default=True)
    is_gizmo_invocation: BoolProperty(name="Invoke operator from Gizmo", default=False)
    is_button_invocation: BoolProperty(name="Invoke operator from Sidebar Button", default=False)
    is_sidebar_invocation: BoolProperty(name="Invoke operator from Popup Panel Button", default=False)
    passthrough = None

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            active = context.active_object
            return active and active.type == 'MESH' and active.select_get() and active.HC.ishyper

    @classmethod
    def description(cls, context, properties):
        if properties:
            if properties.is_gizmo_invocation:
                desc = "Pick any modifier, and Move it to a different place in the stack"
                desc += "\nShortcut: ALT + W"

                desc += "\n\nSHIFT: Add Weld/Solidify/Displace Modifier at specific place in the stack"
                desc += "\nShortcut: ALT + SHIFT + W"

                desc += "\n\nALT: Pick HyperBevel"
                desc += "\nShortcut: ALT + B"

                desc += "\n\nCTRL: Pick Wire/Bounds/Empty Object in Object Tree"
                desc += "\nShortcut: ALT + Q"

                desc += "\n\nALT + CTRL: Look for and remove unused Boolean Modifiers and their Mod Objects"
                desc += "\nShortcut: ALT + X"
                return desc

            elif properties.is_button_invocation:
                if properties.mode == 'ADD':
                    return "Add Weld/Solidify/Displace Modifier at specific place in the stack"
                elif properties.mode == 'PICK':
                    return "Pick any modifier, and Move it to a different place in the stack"

            return "HyperMod"
        return "Invalid Context"

    def draw_HUD(self, context):
        if context.area == self.area:
            ui_scale = get_scale(context)

            mode = self.mode

            mod = self.mod
            show_mod = mod.show_viewport
            modobj = get_mod_obj(mod)

            mods = self.active.modifiers

            is_moving = self.is_moving

            is_d = self.is_d
            is_adjusting = self.is_adjusting

            self.offset = self.get_compensated_offset(context)

            action = "Add" if mode == 'ADD' else "Move" if is_moving else "Enable" if is_d and show_mod else "Disable" if is_d and not show_mod else "Adjust" if is_adjusting else "Pick"
            action_color = green if mode == 'ADD' else yellow if is_moving else white if is_d and show_mod else grey if is_d and not show_mod else orange if is_adjusting else blue

            dims = draw_label(context, title=action, coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=action_color)
            dims += draw_label(context, title=" Modifier: ", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=white)
            dims += draw_label(context, title=f"{mod.name} ", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=action_color)

            if mode == 'ADD' and mod.type == 'SOLIDIFY' and self.preceding_mods:
                title = '+ Weld' if len(self.preceding_mods) == 1 else '+ Double SubD'
                draw_label(context, title=title, coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, size=10, color=action_color)

            elif mod in self.deleted:
                dims += draw_label(context, title="to be deleted ", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, size=10, color=red)

            elif not show_mod:
                dims += draw_label(context, title="disabled ", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, size=10, color=white, alpha=0.2)

            if (mod.type == 'BOOLEAN' and not modobj) or (is_edge_bevel(mod) and mod not in self.batches):
                draw_label(context, title="INVALID", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, size=10, color=red, alpha=1)

            elif modobj and modobj in self.wire_mod_objects and not modobj.visible_get() and (meta := self.mod_objects[modobj]['visible']['meta']) in ['SCENE', 'VIEWLAYER', 'HIDDEN_COLLECTION']:
                if meta == 'SCENE':
                    title = 'not in Scene '
                elif meta == 'VIEWLAYER':
                    title = 'not on View Layer '
                else:
                    title = 'in hidden Collection '

                draw_label(context, title=title, coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, size=10, color=orange, alpha=1)

            if mod.type == 'WELD':
                precision = 1

                if is_adjusting and (self.is_shift or self.is_ctrl):
                    title = "a little" if self.is_shift else "a lot"
                    draw_label(context, title=title, coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, size=10, center=False, alpha=0.5)

                    if self.is_shift:
                        precision += 1
                    else:
                        precision -= 1

                self.offset += 18

                dims = draw_label(context, title="Threshold: ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, alpha=0.5)
                dims += draw_label(context, title=f"{dynamic_format(mod.merge_threshold, decimal_offset=precision)} ", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=yellow if is_adjusting else white)

                if not is_adjusting:
                    draw_label(context, title=mod.mode.title(), coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=yellow)

            elif mod.type == 'DISPLACE':
                precision = 1

                if is_adjusting and (self.is_shift or self.is_ctrl):
                    title = "a little" if self.is_shift else "a lot"
                    draw_label(context, title=title, coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, size=10, center=False, alpha=0.5)

                    if self.is_shift:
                        precision += 1
                    else:
                        precision -= 1

                self.offset += 18

                dims = draw_label(context, title="Strength: ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, alpha=0.5)
                dims += draw_label(context, title=f"{dynamic_format(mod.strength, decimal_offset=precision)} ", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=yellow if self.is_t else white)

                if '(Split)' in self.modname and is_adjusting:
                    draw_label(context, title="reversed", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=0.3)

            elif mod.type == 'SOLIDIFY':
                precision = 1

                if is_adjusting and (self.is_shift or self.is_ctrl):
                    title = "a little" if self.is_shift else "a lot"
                    draw_label(context, title=title, coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, size=10, center=False, alpha=0.5)

                    if self.is_shift:
                        precision += 1
                    else:
                        precision -= 1

                self.offset += 18

                dims = draw_label(context, title="Thickness: ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, alpha=0.5)
                dims += draw_label(context, title=f"{dynamic_format(mod.thickness, decimal_offset=precision)} ", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=yellow if is_adjusting else white)

                if mod.use_even_offset and not is_adjusting:
                    draw_label(context, title="Even", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=blue)

            elif mod.type == 'BOOLEAN':
                self.offset += 18

                op = mod.operation
                solver = mod.solver

                dims = draw_label(context, title=f"{solver.title()} ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, alpha=1)

                color = blue if op == 'UNION' else red if op == 'DIFFERENCE' else normal
                draw_label(context, title=mod.operation.title(), coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=color, alpha=1)

                if solver == 'EXACT' and (mod.use_self or mod.use_hole_tolerant):
                    self.offset += 18

                    title = "Self Intersection" if mod.use_self else "Hole Tolerant"

                    if mod.use_self and mod.use_hole_tolerant:
                        title += " + Hole Tolerant"

                    draw_label(context, title=title, coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=yellow)

            elif mod.type == 'SUBSURF':
                self.offset += 18

                dims = draw_label(context, title="Levels: ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, alpha=0.5)
                dims += draw_label(context, title=f"{mod.levels} ", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=orange if is_adjusting else white, alpha=1)

                if is_adjusting:
                    dims += draw_label(context, title="Render: ", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, alpha=0.5)

                dims += draw_label(context, title=f"{mod.render_levels} ", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=orange if is_adjusting and self.subd_affect_render else white, alpha=0.5)

                if is_adjusting:
                    if self.subd_affect_render:
                        draw_label(context, title="Affect Both", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=yellow, alpha=1)
                else:
                    subd_type = mod.subdivision_type.title().replace('_', '-')
                    dims += draw_label(context, title=subd_type, coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=yellow, alpha=1)

                    if self.mod.boundary_smooth == 'PRESERVE_CORNERS':
                        draw_label(context, title=" Keep Corners", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=green, alpha=1)

            elif is_auto_smooth(mod):
                precision = 1

                if is_adjusting and (self.is_shift or self.is_ctrl):
                    title = "a little" if self.is_shift else "a lot"
                    draw_label(context, title=title, coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, size=10, center=False, alpha=0.5)

                    if self.is_shift:
                        precision += 1

                    elif self.is_ctrl:
                        precision -= 1

                self.offset += 18

                angle = degrees(get_mod_input(mod, 'Angle'))

                if angle is not None:
                    dims = draw_label(context, title="Angle: ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, alpha=0.5)
                    dims += draw_label(context, title=f"{dynamic_format(angle, decimal_offset=precision)}°", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=yellow if self.is_t else white)

                else:
                    draw_label(context, title="INVALID", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=red, alpha=1)

            elif is_source(mod):
                self.offset += 18

                dims = draw_label(context, title="Object: ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, alpha=0.5)

                srcobj = get_mod_input(mod, 'Source')
                title, color = (srcobj.name, normal) if srcobj else ('None', red)
                draw_label(context, title=title, coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=color)

            if self.warn_indices:
                self.offset += 6

            if self.has_multiple_solidify:
                self.offset += 18
                draw_label(context, title="Multiple SOLIDIFY mods in the stack!", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=red)

            if self.has_multiple_displace:
                self.offset += 18
                draw_label(context, title="Multiple DISPLACE mods in the stack!", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=red)

            if self.is_unsorted:
                self.offset += 18
                draw_label(context, title="Mod Sorting Mismatch!", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=red)

            elif not self.active.HC.ismodsort:
                self.offset += 25
                draw_label(context, title="NOTE: Mod Sorting Disabled!", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=0.25)

            if is_adjusting:
                return

            ref_idx, ref_type = self.get_reference_mod_index_from_prefix()

            self.offset += 24

            stack_dims = draw_label(context, title="Stack: ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=0.5)

            for idx, mod in enumerate(mods):
                is_sel = mod == self.mod
                is_profile_bevel = is_edge_bevel(mod) and mod.profile_type == 'CUSTOM'

                if idx:
                    self.offset += 18

                if is_sel:
                    size, color, alpha = (12, action_color, 1)

                    if len(mods) > 1:
                        coords = [Vector((self.HUD_x + stack_dims.x - (5 * ui_scale), self.HUD_y - (self.offset * ui_scale), 0)), Vector((self.HUD_x + stack_dims.x - (5 * ui_scale), self.HUD_y - (self.offset * ui_scale) + (10 * ui_scale), 0))]
                        draw_line(coords, color=red if mod in self.deleted else action_color, width=2 * ui_scale, screen=True)

                elif idx == ref_idx:
                    size, color, alpha = (10, action_color, 0.6 if is_moving else 0.4)

                else:
                    size, color, alpha = (10, white, 0.4)

                dims = draw_label(context, title=mod.name, coords=Vector((self.HUD_x + stack_dims.x, self.HUD_y)), offset=self.offset, center=False, size=size, color=red if mod in self.deleted else color, alpha=0.5 if mod in self.deleted else alpha if mod.show_viewport else 0.15)

                if mod.use_pin_to_last:
                    dims += draw_label(context, title=" 📍", coords=Vector((self.HUD_x + stack_dims.x + dims.x, self.HUD_y)), offset=self.offset, center=False, size=size, color=white, alpha=1)

                if is_profile_bevel:
                    dims += draw_label(context, title=" 🌠" , coords=Vector((self.HUD_x + stack_dims.x + dims.x, self.HUD_y)), offset=self.offset, center=False, size=size, color=blue, alpha=alpha)

                else:
                    if idx in self.warn_indices:
                        dims += draw_label(context, title=" *" , coords=Vector((self.HUD_x + stack_dims.x + dims.x, self.HUD_y)), offset=self.offset, center=False, size=size, color=red, alpha=1)

                if is_sel and ref_type:
                    draw_label(context, title=ref_type , coords=Vector((self.HUD_x + stack_dims.x + dims.x, self.HUD_y)), offset=self.offset, center=False, size=10, color=white, alpha=1 if self.is_moving else 0.3)

            if not self.passthrough:
                if (is_radial_array(self.mod) or self.mod.type == 'MIRROR') and self.mod in self.batches:
                    batch = self.batches[self.mod]

                    if len(batch) == 5:
                        _, _, _, co2d, ui_scale = self.batches[self.mod]
                        color  = red if self.mod in self.deleted else yellow if self.is_moving else blue

                        draw_circle(co2d, radius=10 * ui_scale, width=2 * ui_scale, color=color, alpha=1)

    def draw_VIEW3D(self, context):
        if context.area == self.area:
            if self.mode == 'PICK' and self.mod in self.batches:

                if self.mod.type == 'BOOLEAN':
                    batch = self.batches[self.mod]
                    color = red if self.mod in self.deleted else yellow if self.is_moving else blue

                    draw_batch(batch, color=color, width=1, alpha=0.2, xray=True)

                    if self.mod.show_viewport:
                        draw_batch(batch, color=color, width=1, alpha=1, xray=False)

                elif self.mod.type == 'BEVEL':
                    color = red if self.mod in self.deleted else yellow if self.is_moving else blue

                    for coords in self.batches[self.mod]:
                        draw_line(coords, width=2, color=color, alpha=0.5, xray=True)

                        if self.mod.show_viewport:
                            draw_line(coords, width=3, color=color, alpha=1, xray=False)

                elif is_radial_array(self.mod) or self.mod.type == 'MIRROR':
                    batch = self.batches[self.mod]
                    color = red if self.mod in self.deleted else yellow if self.is_moving else blue

                    if len(batch) == 5:

                        if self.passthrough:
                            draw_point(average_locations(batch[0][:2]), color=blue, size=4, xray=True)

                        else:
                            draw_batch(batch, color=color, width=2 * batch[4], alpha=1, xray=True)

                    else:
                        draw_batch(batch, color=color, width=1, alpha=0.2, xray=True)

                        if self.mod.show_viewport:
                            draw_batch(batch, color=color, width=1, alpha=1, xray=False)

                elif is_source(self.mod):
                    batch = self.batches[self.mod]
                    color = red if self.mod in self.deleted else yellow if self.is_moving else normal

                    draw_batch(batch, color=color, width=1, alpha=0.2, xray=True)

                    if self.mod.show_viewport:
                        draw_batch(batch, color=color, width=1, alpha=1, xray=False)

    def modal(self, context, event):
        if ignore_events(event):
            return {'RUNNING_MODAL'}

        context.area.tag_redraw()

        if self.is_tab_locked:
            if event.type == 'TAB' and event.value == 'RELEASE':
                self.is_tab_locked = False
                self.check_tab_finish()

        if self.is_alt_locked:
            if event.type in alt and event.value == 'PRESS':
                self.is_alt_locked = False

        if event.type == 'MOUSEMOVE':
            get_mouse_pos(self, context, event)

            if self.passthrough:
                self.passthrough = False

                self.factor = get_zoom_factor(context, depth_location=self.loc, scale=1, ignore_obj_scale=False)

                for mod, batch in self.batches.items():
                    if is_radial_array(mod) or mod.type == 'MIRROR':
                        if '_CROSS' in (batchtype := batch[2]):
                            modobj = get_mod_obj(mod)
                            mx = modobj.matrix_world

                            batch = get_batch_from_matrix(mx, screen_space=50)

                            co2d = get_location_2d(context, mx.to_translation(), default='OFF_SCREEN')
                            self.batches[mod] = (*batch, batchtype, co2d, get_scale(context))

        if self.mode == 'PICK' and not self.is_alt_locked:
            self.is_moving = event.alt

        if event.type in [*alt, 'D', 'T']:
            force_ui_update(context, self.active)

        if self.is_adjusting:
            wrap_mouse(self, context, x=True)

            update_mod_keys(self, event)

            delta_x = self.mouse_pos.x - self.last_mouse.x

            if self.mod.type == 'WELD':
                divisor = get_mousemove_divisor(event, sensitivity=1000)
                self.mod.merge_threshold += delta_x / divisor

            elif self.mod.type == 'SOLIDIFY':
                divisor = get_mousemove_divisor(event, normal=1, shift=20, ctrl=0.1, sensitivity=1)

                self.mod.thickness += delta_x * (self.factor / divisor)

            elif self.mod.type == 'DISPLACE':
                divisor = get_mousemove_divisor(event, normal=1, shift=20, ctrl=0.1, sensitivity=1)

                self.mod.strength += delta_x * (self.factor / divisor) * (-1 if '(Split)' in self.mod.name else 1)

            elif self.mod.type == 'SUBSURF':

                if event.type in ['B', 'R'] and event.value == 'PRESS':
                    self.subd_affect_render = not self.subd_affect_render
                    force_ui_update(context)

                divisor = get_mousemove_divisor(event, normal=1, shift=1, ctrl=1, sensitivity=0.01)  # we use this, even though mod keys have no effect, because it considers the ui scaling

                self.subd_levels += delta_x * (self.factor / divisor)
                self.subd_levels = max(self.subd_levels, 0)

                self.mod.levels = round(self.subd_levels)

                if self.subd_affect_render:
                    self.mod.render_levels = self.mod.levels

            elif is_auto_smooth(self.mod):
                angle = degrees(get_mod_input(self.mod, 'Angle'))

                if angle:
                    divisor = get_mousemove_divisor(event, normal=1, shift=5, ctrl=0.5, sensitivity=30)
                    set_mod_input(self.mod, 'Angle', radians(angle + (delta_x / divisor)))
                    self.active.update_tag()

        else:

            events = ['G']

            if self.active.HC.ismodsort:
                events.append('Q')

            if self.mod.use_pin_to_last:
                events.append('P')

            if self.mode == 'ADD':

                if self.mod.type == 'WELD':
                    events.extend(['D', 'S'])

                elif self.mod.type == 'DISPLACE':
                    events.extend(['W', 'S'])

                elif self.mod.type == 'SOLIDIFY':
                    events.extend(['W', 'D', 'S'])

            elif self.mode == 'PICK':

                events.extend(['A', 'D', 'X', 'F', 'S'])

                if self.can_tab_finish:
                    events.append('TAB')

                if self.mod.type == 'WELD':
                    events.extend(['C'])

                elif self.mod.type == 'SOLIDIFY':
                    events.extend(['E'])

                elif self.mod.type == 'BOOLEAN':
                    events.extend(['E'])

                if self.mod.type == 'SUBSURF' and self.mod.subdivision_type == 'CATMULL_CLARK':
                    events.append('C')

            if event.type in events or scroll(event, key=True):
                mods, mods_len, current_idx = self.get_mods_and_indices(debug=False)

                if mods_len > 1 and (scroll(event, key=True) or (event.type == 'G' and event.value == 'PRESS')):

                    if self.mode == 'ADD':
                        self.remove_preceding_mods()

                        mods, mods_len, current_idx = self.get_mods_and_indices(debug=False)

                    if scroll_up(event, key=True):
                        new_index = current_idx - 1

                        if new_index < 0:
                            new_index = mods_len -1

                    elif scroll_down(event, key=True):
                        new_index = current_idx + 1

                        if new_index >= mods_len:
                            new_index = 0

                    elif event.type == 'G':
                        new_index = mods_len - 1 if event.shift else 0

                    if self.is_moving:

                        if (pinned := mods[new_index]).use_pin_to_last:
                            print(f"WARNING: Unpinning modifier {pinned.name} to allow for custom sorting")
                            pinned.use_pin_to_last = False

                            if not pinned.name.startswith('+ '):
                                set_mod_prefix(pinned, '+')

                        move_mod(self.mod, index=new_index)

                        self.ensure_prefix()

                        self.verify_sorting()

                    else:
                        self.pick_mod(context, index=new_index)

                        if self.is_d:
                            self.mod.show_viewport = self.visibility_state

                    self.check_multiple_warning(debug=False)

                    self.verify_can_apply_mods()

                elif event.type == 'P' and event.value == 'PRESS':
                    self.mod.use_pin_to_last = False

                    self.verify_sorting()

                elif event.type == 'Q' and event.value == 'PRESS':
                    prefix = get_prefix_from_mod(self.mod)

                    if self.is_moving:
                        if prefix == '+':
                            set_mod_prefix(self.mod, '-', self.modname)

                        elif prefix == '-':
                            set_mod_prefix(self.mod, '+', self.modname)

                        if self.mode == 'ADD':
                            self.remove_preceding_mods()

                        self.ensure_prefix()

                        if self.mode == 'ADD' and prefix:
                            self.mod.name = get_mod_base_name(self.mod)

                    else:
                        if prefix:

                            if event.shift or self.mode == 'ADD':
                                self.mod.name = get_mod_base_name(self.mod)

                            else:
                                if prefix == '+':
                                    set_mod_prefix(self.mod, '-', self.modname)

                                elif prefix == '-':
                                    self.mod.name = get_mod_base_name(self.mod)

                        elif not event.shift:
                            set_mod_prefix(self.mod, '+', self.modname)

                    self.verify_sorting()

                if self.mod.type == 'WELD':

                    if event.type in ['C'] and event.value == 'PRESS':

                        if self.mod.mode == 'ALL':
                            self.mod.mode = 'CONNECTED'

                        elif self.mod.mode == 'CONNECTED':
                            self.mod.mode = 'ALL'

                    if self.mode == 'ADD':

                        if event.type in ['D'] and event.value == 'PRESS':

                            self.add_mod(modtype='DISPLACE')

                        elif event.type in ['S'] and event.value == 'PRESS':

                            self.add_mod(modtype='SOLIDIFY')

                elif self.mod.type == 'DISPLACE':

                    if self.mode == 'ADD':

                        if event.type in ['W'] and event.value == 'PRESS':

                            self.add_mod(modtype='WELD')

                        elif event.type in ['S'] and event.value == 'PRESS':

                            self.add_mod(modtype='SOLIDIFY')

                elif self.mod.type == 'SOLIDIFY':

                    if event.type in ['E'] and event.value == 'PRESS':
                        self.mod.use_even_offset = not self.mod.use_even_offset

                    if self.mode == 'ADD':

                        if event.type in ['S'] and event.value == 'PRESS':

                            if self.preceding_mods:

                                if len(self.preceding_mods) == 1:
                                    self.remove_preceding_mods()

                                    current_idx = list(self.active.modifiers).index(self.mod)

                                elif len(self.preceding_mods) == 2:
                                    self.remove_preceding_mods()
                                    return {'RUNNING_MODAL'}

                            self.preceding_mods = self.add_double_subd(current_idx)

                        elif event.type in ['W'] and event.value == 'PRESS':

                            if event.shift:

                                if self.preceding_mods:

                                    if len(self.preceding_mods) == 1:
                                        self.remove_preceding_mods()
                                        return {'RUNNING_MODAL'}

                                    elif len(self.preceding_mods) == 2:
                                        self.remove_preceding_mods()

                                        current_idx = list(self.active.modifiers).index(self.mod)

                                if current_idx > 0:
                                    modname = get_new_mod_name(self.active, modtype='WELD')
                                    prefix = get_prefix_from_mod(self.mod)

                                    if prefix:
                                        modname = f"{prefix} {modname}"

                                    self.preceding_mods = add_weld(self.active, name=modname),

                                    for mod in self.preceding_mods:
                                        move_mod(mod, current_idx)

                                    self.cancel_remove_mods.update(self.preceding_mods)

                                self.check_multiple_warning()

                            else:

                                self.add_mod(modtype='WELD')

                        elif event.type in ['D'] and event.value == 'PRESS':

                            self.add_mod(modtype='DISPLACE')

                elif self.mod.type == 'BOOLEAN':

                    if event.type in ['E'] and event.value == 'PRESS':
                        modobj = get_mod_obj(self.mod)

                        if event.alt:
                            if "Hyper Bevel" in self.mod.name and modobj:

                                self.finish(context)
                                self.save_settings()

                                bpy.ops.machin3.extend_hyper_bevel('INVOKE_DEFAULT', objname=modobj.name, modname=self.mod.name, is_hypermod_invocation=True)

                                return {'FINISHED'}

                        else:
                            solver = step_list(get_boolean_solver_string(self.mod), [s[0] for s in extended_boolean_solver_items], step=-1 if event.shift else 1, loop=True)

                            set_boolean_solver(self.mod, solver)

                elif self.mod.type == 'SUBSURF':

                    if event.type in ['C'] and event.value == 'PRESS':
                        if self.mod.boundary_smooth == 'ALL':
                            self.mod.boundary_smooth = 'PRESERVE_CORNERS'
                        else:
                            self.mod.boundary_smooth = 'ALL'

                if self.mode == 'PICK':

                    if event.type in ['D'] and event.value == 'PRESS' and not self.is_d:

                        if event.shift:
                            mods, _, current_idx = self.get_mods_and_indices()
                            slice = mods[current_idx:]

                            state = not self.mod.show_viewport

                            for mod in slice:

                                if mod not in self.deleted:
                                    mod.show_viewport = state

                        else:
                            if self.mod not in self.deleted:
                                self.mod.show_viewport = not self.mod.show_viewport

                        self.verify_can_apply_mods()

                    elif event.type in ['A'] and event.value == 'PRESS':

                        if self.can_apply_mods and event.ctrl:
                            self.finish(context)
                            self.save_settings()

                            meshmachine = bool(HC.get_addon('MESHmachine'))
                            bpy.ops.machin3.apply_all_modifiers(backup=True, duplicate=False, stash_original=meshmachine, stash_cutters=meshmachine)

                            if self.has_disabled_mods:
                                bpy.ops.machin3.hyper_modifier('INVOKE_DEFAULT', is_gizmo_invocation=False, mode='PICK')

                            return {'FINISHED'}

                        else:
                            mods, _, _ = self.get_mods_and_indices()

                            if event.shift:
                                if self.wire_mod_objects:

                                    state = not self.wire_mod_objects[0].visible_get()

                                    if state:
                                        ensure_visibility(context, self.wire_mod_objects)

                                    else:
                                        for obj in self.wire_mod_objects:
                                            restore_visibility(obj, self.mod_objects[obj]['visible'])

                            else:
                                state = not mods[0].show_viewport

                                for mod in mods:
                                    if mod not in self.deleted:
                                        if self.avoid_all_toggling_autosmooth(mod):
                                            continue

                                        mod.show_viewport = state

                            self.verify_can_apply_mods()

                    elif event.type in ['S'] and event.value == 'PRESS':

                        if modobj := get_mod_obj(self.mod):
                            self.finish(context)
                            self.save_settings()

                            ensure_visibility(context, modobj)

                            if not event.shift:
                                bpy.ops.object.select_all(action='DESELECT')

                            modobj.select_set(True)
                            context.view_layer.objects.active = modobj

                            return {'FINISHED'}

                    elif event.type in ['F'] and event.value == 'PRESS':

                        if event.shift:
                            bpy.ops.view3d.view_selected('INVOKE_DEFAULT' if context.scene.HC.focus_mode == 'SOFT' else 'EXEC_DEFAULT')

                        elif modobj := get_mod_obj(self.mod):

                            vis = visible_get(modobj)

                            bpy.ops.object.select_all(action='DESELECT')
                            ensure_visibility(context, modobj, select=True)

                            bpy.ops.view3d.view_selected('INVOKE_DEFAULT' if context.scene.HC.focus_mode == 'SOFT' else 'EXEC_DEFAULT')

                            restore_visibility(modobj, vis)

                            self.active.select_set(True)

                        self.passthrough = True
                        return {'RUNNING_MODAL'}

                    elif event.type in ['X'] and event.value == 'PRESS':

                        if event.shift:
                            mods, _, current_idx = self.get_mods_and_indices()
                            slice = mods[current_idx:]

                            state = self.mod in self.deleted

                            for mod in slice:

                                if state and mod in self.deleted:
                                    mod.show_viewport = self.deleted[mod]
                                    del self.deleted[mod]

                                elif not state and mod not in self.deleted:
                                    self.deleted[mod] = mod.show_viewport
                                    mod.show_viewport = False

                        else:

                            if self.mod in self.deleted:
                                self.mod.show_viewport = self.deleted[self.mod]

                                del self.deleted[self.mod]

                            else:

                                self.deleted[self.mod] = self.mod.show_viewport

                                self.mod.show_viewport = False

                        self.verify_can_apply_mods()

                    elif event.type == 'TAB' and event.value == 'PRESS':
                        self.finish(context)
                        self.save_settings()

                        if is_edge_bevel(self.mod):
                            bpy.ops.machin3.bevel_edge('INVOKE_DEFAULT', index=-1, is_hypermod_invocation=True)
                            return {'FINISHED'}

                        elif 'Hyper Bevel' in self.mod.name:
                            bpy.ops.machin3.edit_hyper_bevel('INVOKE_DEFAULT', objname=self.active.name, modname=self.mod.name, is_hypermod_invocation=True)
                            return {'FINISHED'}

                        elif self.mod.type == 'BOOLEAN':
                            bpy.ops.machin3.pick_object_tree('INVOKE_DEFAULT')
                            return {'FINISHED'}

                        elif self.mod.type == 'SOLIDIFY':
                            bpy.ops.machin3.adjust_shell('INVOKE_DEFAULT', is_hypermod_invocation=True)
                            return {'FINISHED'}

                        elif self.mod.type == 'DISPLACE':
                            bpy.ops.machin3.adjust_displace('INVOKE_DEFAULT', is_hypermod_invocation=True, modname=self.mod.name)
                            return {'FINISHED'}

                        elif is_array(self.mod):
                            bpy.ops.machin3.adjust_array('INVOKE_DEFAULT', is_hypermod_invocation=True)
                            return {'FINISHED'}

            elif navigation_passthrough(event, alt=False, wheel=False):
                self.passthrough = True
                return {'PASS_THROUGH'}

            elif event.type in ['LEFTMOUSE', 'SPACE'] and event.value == 'PRESS':
                mods, mods_len, _ = self.get_mods_and_indices()

                if mods_len > 1 and event.type == 'LEFTMOUSE' and self.mode == 'ADD':
                    self.mode = 'PICK'

                    self.is_moving = False

                    self.verify_can_apply_mods()

                    self.check_tab_finish()

                    force_ui_update(context)
                    return {'RUNNING_MODAL'}

                else:
                    self.finish(context)
                    self.save_settings()

                    if self.deleted:
                        for mod in self.deleted:
                            if mod.type == 'BEVEL':

                                if mod.limit_method == 'VGROUP' and (vgname := mod.vertex_group):
                                    vgroup = self.active.vertex_groups.get(vgname, None)

                                    if vgroup:
                                        self.active.vertex_groups.remove(vgroup)

                                elif mod.limit_method == 'WEIGHT' and (weightname := mod.edge_weight):
                                    if weightname != 'bevel_weight_edge':
                                        if bw := self.active.data.attributes.get(weightname, None):
                                            self.active.data.attributes.remove(bw)

                            remove_mod(mod)

                    force_obj_gizmo_update(context)
                    return {'FINISHED'}

            elif event.type in ['RIGHTMOUSE', 'ESC'] and event.value == 'PRESS':
                self.finish(context)

                for mod in self.cancel_remove_mods:
                    remove_mod(mod)

                if self.mode == 'PICK':
                    mods = list(self.active.modifiers)

                    for idx, mod in enumerate(mods):
                        init = self.initial[mod]
                        modtype = 'AUTOSMOOTH' if is_auto_smooth(mod) else mod.type

                        if idx != init['index']:
                            move_mod(mod, init['index'])

                        if mod.show_viewport != init['show_viewport']:
                            mod.show_viewport = init['show_viewport']

                        if mod.name != init['name']:
                            mod.name = init['name']

                        if modtype in init:
                            for name, value in init[modtype].items():

                                if modtype == 'AUTOSMOOTH':
                                    if (angle := get_mod_input(mod, 'Angle')) != init['AUTOSMOOTH']['angle']:
                                        print(f"    {modtype}'s Angle prop has changed from {degrees(angle)} to {degrees(value)}")
                                        set_mod_input(mod, 'Angle', value)

                                elif getattr(mod, name) != value:
                                    setattr(mod, name, value)

                for obj in self.wire_mod_objects:
                    restore_visibility(obj, self.mod_objects[obj]['visible'])

                return {'CANCELLED'}

        if self.mode == 'PICK':
            is_key(self, event, 'D', debug=False)
            is_key(self, event, 'T', debug=False)

            if event.type == 'D' and event.value == 'PRESS':
                self.visibility_state = self.mod.show_viewport

            if event.type == 'T' and (self.mod.type in ['WELD', 'SOLIDIFY', 'DISPLACE', 'SUBSURF'] or is_auto_smooth(self.mod)):
                if event.value == 'PRESS' and not self.is_adjusting:   # NOTE: only set it once, by checking for self.is_adjusting (set below)
                    context.window.cursor_set('SCROLL_X')

                elif event.value == 'RELEASE':
                    context.window.cursor_set('DEFAULT')

                if self.mod.type in ['WELD', 'SUBSURF']:
                    if event.value == 'PRESS' and not self.is_adjusting:   # NOTE: only set it once, by checking for self.is_adjusting (set below)
                        self.active.show_wire = True

                        if self.mod.type == 'SUBSURF':
                            self.subd_levels = self.mod.levels
                            self.subd_render_levels = self.mod.render_levels

                    elif event.value == 'RELEASE':
                        self.active.show_wire = False

                if event.value == 'PRESS':
                    self.is_adjusting = True
                elif event.value == 'RELEASE':
                    self.is_adjusting = False

        self.last_mouse = self.mouse_pos

        return {'RUNNING_MODAL'}

    def finish(self, context):
        finish_modal_handlers(self)

        restore_gizmos(self)

        finish_status(self)

    def invoke(self, context, event):
        if self.is_gizmo_invocation:

            if event.alt and event.ctrl:
                bpy.ops.machin3.remove_unused_booleans('INVOKE_DEFAULT')
                return {'FINISHED'}

            elif event.alt:
                bpy.ops.machin3.pick_hyper_bevel('INVOKE_DEFAULT')
                return {'FINISHED'}

            elif event.ctrl:
                bpy.ops.machin3.pick_object_tree('INVOKE_DEFAULT')
                return {'FINISHED'}

            self.mode = 'ADD' if event.shift else 'PICK'

        get_mouse_pos(self, context, event)

        if self.is_button_invocation:
            self.warp_mouse_out_of_panel(context)

        self.init_settings(props=['subd_affect_render'])
        self.load_settings()

        self.dg = context.evaluated_depsgraph_get()
        self.active = context.active_object
        self.mx = self.active.matrix_world
        self.loc = self.mx.to_translation()

        self.bm = None

        self.mod = None
        self.preceding_mods = None
        self.is_double_subd = False

        self.mod_objects = {modobj: {'visible': visible_get(modobj)} for mod in self.active.modifiers if (modobj := get_mod_obj(mod))}
        self.wire_mod_objects = [obj for obj in self.mod_objects if is_wire_object(obj)]

        update_mod_keys(self)

        is_key(self, event, 'D')
        is_key(self, event, 'T')

        self.is_adjusting = False

        self.is_tab_locked = event.type == 'TAB'
        self.is_alt_locked = not self.is_gizmo_invocation and event.alt

        self.can_tab_finish = False

        self.subd_levels = 0
        self.subd_render_levels = 0

        self.verify_can_apply_mods()

        self.verify_sorting()

        self.batches = {}

        self.cancel_remove_mods = set()

        self.initial = self.get_initial_mod_states()

        self.deleted = {}

        if self.mode == 'ADD':

            modtype = 'WELD' if self.active.modifiers else 'SOLIDIFY'

            self.add_mod(modtype=modtype, debug=False)

            self.is_moving = True

        elif self.active.modifiers and self.mode == 'PICK':
            self.pick_mod(context)

            force_ui_update(context, active=self.active)

            self.is_moving = False

        else:
            text = [f"No Modifiers on {self.active.name} to pick/move!",
                    "You can run the tool with the SHIFT key pressed - while clicking on the 🔧 gizmo - to add a modifier!"]

            draw_fading_label(context, text=text, y=120, color=[red, white], alpha=[1, 0.5], move_y=30, time=3)

            return {'CANCELLED'}

        self.factor = get_zoom_factor(context, depth_location=self.loc, scale=1, ignore_obj_scale=False)

        self.last_mouse = self.mouse_pos

        hide_gizmos(self, context)

        init_status(self, context, func=draw_hyper_mod_status(self))

        init_modal_handlers(self, context, hud=True, view3d=True)
        return {'RUNNING_MODAL'}

    def warp_mouse_out_of_panel(self, context):
        distance = None

        HUD_width = get_text_dimensions(context, "Pick Modifier: Hyper Cut", size=12).x

        if self.is_sidebar_invocation:
            for region in context.area.regions:
                if region.type == 'UI':
                    distance = - (region.width - (context.region.width - self.mouse_pos.x) + HUD_width)

        else:
            is_button_left = self.mode == 'ADD'

            if self.mouse_pos.x < context.region.width / 2:
                distance = ((300 if is_button_left else 150) * get_scale(context))

            else:
                distance = - (((150 if is_button_left else 300) * get_scale(context)) + HUD_width)

        if distance:
            warp_mouse(self, context, Vector((self.mouse_pos.x + distance, self.mouse_pos.y)))

    def get_initial_mod_states(self):
        initial = {}

        for idx, mod in enumerate(self.active.modifiers):
            initial[mod] = {'index': idx,
                            'name': mod.name,
                            'show_viewport': mod.show_viewport}

            if mod.type in ['WELD', 'SOLIDIFY', 'DISPLACE', 'BOOLEAN'] or (smooth := is_auto_smooth(mod)):

                if mod.type == 'WELD':
                    initial[mod]['WELD'] = {'mode': mod.mode,
                                            'merge_threshold': mod.merge_threshold}

                elif mod.type == 'SOLIDIFY':
                    initial[mod]['SOLIDIFY'] = {'use_even_offset': mod.use_even_offset,
                                                'thickness': mod.thickness}

                elif mod.type == 'DISPLACE':
                    initial[mod]['DISPLACE'] = {'strength': mod.strength,
                                                'mid_level': mod.mid_level}

                elif mod.type == 'BOOLEAN':
                    initial[mod]['BOOLEAN'] = {'solver': mod.solver,
                                               'use_self': mod.use_self,
                                               'use_hole_tolerant': mod.use_hole_tolerant}

                elif smooth:
                    initial[mod]['AUTOSMOOTH'] = {'angle': get_mod_input(mod, 'Angle')}

        return initial

    def verify_can_apply_mods(self):
        self.can_apply_mods = False
        self.has_disabled_mods = False

        if self.mode == 'PICK':
            if not (self.active.library or (self.active.data and self.active.data.library)):
                for mod in self.active.modifiers:
                    if mod.show_viewport:
                        self.can_apply_mods = True

                    else:
                        self.has_disabled_mods = True

    def verify_sorting(self):
        self.is_unsorted = False

        if self.active.HC.ismodsort:
            current = list(self.active.modifiers)
            sorted = sort_modifiers(self.active, preview=True)

            self.is_unsorted = sorted != current

    def get_mods_and_indices(self, debug=False):
        mods = list(self.active.modifiers)
        mods_len = len(mods)

        current_idx = mods.index(self.mod)

        if debug:
            print("current:", current_idx, "of", mods_len - 1)

        return mods, mods_len, current_idx

    def ensure_prefix(self, debug=False):
        mods, mods_len, current_idx = self.get_mods_and_indices(debug=False)

        prefix = get_prefix_from_mod(self.mod)

        next_prefix = None
        prev_prefix = None

        if current_idx > 0:
            prev_mod = mods[current_idx - 1]
            prev_prefix = get_prefix_from_mod(prev_mod)

        if current_idx < mods_len - 1:
            next_mod = mods[current_idx + 1]
            next_prefix = get_prefix_from_mod(next_mod)

        if debug:
            print()
            print("setting prefix for mod:", self.modname, current_idx, "/", mods_len)
            print(" current prefix is:", prefix)
            print("    prev prefix is:", prev_prefix, f"({prev_mod.name if current_idx > 0 else ''})")
            print("    next prefix is:", next_prefix, f"({next_mod.name if current_idx < mods_len - 2 else ''})")

        if prefix == '+' and current_idx == 0:
            set_mod_prefix(self.mod, '-', self.modname)

        elif prefix == '-' and current_idx == mods_len - 1:
            set_mod_prefix(self.mod, '+', self.modname)

        elif prefix == '+' and prev_prefix == '-':
            if debug:
                print(f"mods {self.mod.name} and {prev_mod.name} reference each other, preventing")

            set_mod_prefix(self.mod, '-', self.modname)

        elif prefix == '-' and next_prefix == '+':
            if debug:
                print(f"mods {self.mod.name} and {next_mod.name} reference each other, preventing")

            set_mod_prefix(self.mod, '+', self.modname)

        elif prefix is None and self.is_moving:
            if debug:
                print()
                print("mod has no prefix!")
                print(" mods_len:", mods_len)
                print(" current idx:", current_idx)

            if current_idx == 0:
                set_mod_prefix(self.mod, '-', self.modname)

                if debug:
                    print(" added prefix -")

            else:
                set_mod_prefix(self.mod, '+', self.modname)

                if debug:
                    print(" added prefix +")

    def populate_batches(self, context):
        if self.mod not in self.batches:

            if self.mod.type == 'BOOLEAN':
                modobj = get_mod_obj(self.mod)

                if modobj:
                    self.batches[self.mod] = get_batch_from_obj(self.dg, modobj)

            elif is_edge_bevel(self.mod, simple=False):
                if self.bm is None:
                    bm = bmesh.new()
                    bm.from_mesh(self.active.data)
                    bm.edges.ensure_lookup_table()

                    vg_layer = ensure_default_data_layers(bm, vertex_groups=True, bevel_weights=False, crease=False)[0]
                    self.bm = (bm, vg_layer)

                else:
                    bm, vg_layer = self.bm

                if self.mod.limit_method == 'VGROUP':

                    vg_index = get_vgroup_index(self.active, self.mod.vertex_group)

                    vg_edges, verts = get_edges_from_edge_bevel_mod_vgroup(bm, vg_layer, vg_index, verts_too=True)

                    if vg_edges:

                        sequences = get_edges_as_vert_sequences(vg_edges, debug=False)

                        batch = []

                        for seq, cyclic in sequences:
                            coords = [self.mx @ v.co for v in seq]

                            if cyclic:
                                coords.append(self.mx @ seq[0].co)

                            batch.append(coords)

                        if batch:
                            self.batches[self.mod] = batch

                    else:
                        print(f"WARNING: Edge Bevel '{self.mod.name}' is invalid! It's vertex group does not create a single Edge.")

                elif self.mod.limit_method == 'WEIGHT':

                    bw_edges, verts = get_edges_from_edge_bevel_mod_weight(bm, self.mod.edge_weight, verts_too=True)

                    if bw_edges:

                        sequences = get_edges_as_vert_sequences(bw_edges, debug=False)

                        batch = []

                        for seq, cyclic in sequences:
                            coords = [self.mx @ v.co for v in seq]

                            if cyclic:
                                coords.append(self.mx @ seq[0].co)

                            batch.append(coords)

                        if batch:
                            self.batches[self.mod] = batch

                    else:
                        print(f"WARNING: Edge Bevel '{self.mod.name}' is invalid! It's bevel weights doe not create a single Edge.")

            elif is_radial_array(self.mod) or self.mod.type == 'MIRROR':
                modobj = get_mod_obj(self.mod)

                if modobj:
                    batch = get_batch_from_obj(self.dg, modobj, cross_in_screen_space=50)

                    if '_CROSS' in batch[2]:

                        co2d = get_location_2d(context, modobj.matrix_world.to_translation(), default='OFF_SCREEN')
                        ui_scale = get_scale(context)

                        self.batches[self.mod] = (*batch, co2d, ui_scale)

                    else:
                        self.batches[self.mod] = batch

            elif is_source(self.mod):
                modobj = get_mod_input(self.mod, 'Source')

                if modobj:
                    self.batches[self.mod] = get_batch_from_obj(self.dg, modobj)

    def check_multiple_warning(self, debug=False):
        mods, _, _ = self.get_mods_and_indices()

        solidifies = [mod for mod in self.active.modifiers if mod.type == 'SOLIDIFY']
        displaces = [mod for mod in self.active.modifiers if mod.type == 'DISPLACE']

        self.has_multiple_solidify = len(solidifies) > 1
        self.has_multiple_displace = len(displaces) > 1

        self.warn_indices = []

        if self.has_multiple_solidify:
            for mod in solidifies:
                self.warn_indices.append(mods.index(mod))

        if self.has_multiple_displace:
            for mod in displaces:
                self.warn_indices.append(mods.index(mod))

        if debug:
            print()
            print("multiple solidify:", self.has_multiple_solidify)
            print("multiple displace:", self.has_multiple_displace)
            print("       at indices:", self.warn_indices)

    def check_tab_finish(self):
        self.can_tab_finish = False

        if self.mode == 'PICK' and not self.is_tab_locked:

            if is_edge_bevel(self.mod) and self.mod in self.batches:
                self.can_tab_finish = True

            elif self.mod.type == 'BOOLEAN' and get_mod_obj(self.mod):
                self.can_tab_finish = True

            elif self.mod.type == 'SOLIDIFY':
                self.can_tab_finish = True

            elif self.mod.type == 'DISPLACE':
                self.can_tab_finish = True

            elif is_hyper_array(self.mod):
                self.can_tab_finish = True

    def get_reference_mod_index_from_prefix(self):
        prefix = get_prefix_from_mod(self.mod)

        if prefix in ['-', '+']:

            mods, mods_len, current_idx = self.get_mods_and_indices(debug=False)

            if prefix == '-':

                if current_idx < mods_len - 1:
                    return current_idx + 1, " 🡷 precedes"

            elif prefix == '+':

                if current_idx > 0:
                    return current_idx - 1, " 🡴 follows"

        return None, None

    def remove_preceding_mods(self):
        if self.preceding_mods:
            for mod in self.preceding_mods:
                self.cancel_remove_mods.remove(mod)

                remove_mod(mod)

            self.preceding_mods = None

    def avoid_all_toggling_autosmooth(self, mod):
        if get_prefs().avoid_all_toggling_autosmooth:
            if mod.type == 'NODES' and (ng := mod.node_group):
                return ng.name.startswith('Smooth by Angle') or ng.name.startswith('Auto Smooth')

        return False

    def get_total_HUD_height(self):
        total_offset = 24 + 18 * (len(self.active.modifiers) - 1)

        if self.mod.type in ['WELD', 'DISPLACE', 'SOLIDIFY', 'BOOLEAN', 'SUBSURF'] or is_auto_smooth(self.mod):
            total_offset += 18

        if self.mod.type == 'BOOLEAN' and self.mod.solver == 'EXACT' and (self.mod.use_self or self.mod.use_hole_tolerant):
            total_offset += 18

        if self.warn_indices:
            total_offset += 6

        if self.has_multiple_solidify:
            total_offset += 18

        if self.has_multiple_displace:
            total_offset += 18

        if self.is_unsorted:
            total_offset += 18

        elif not self.active.HC.ismodsort:
            total_offset += 25

        return total_offset

    def get_compensated_offset(self, context, gap=20, debug=False):

        ui_scale = get_scale(context)

        total_height = self.get_total_HUD_height() * ui_scale

        mouse_height = self.HUD_y

        if debug:
            print()
            print("UI scale:", ui_scale)
            print("HUD height:", total_height)
            print("mouse_height:", mouse_height)
            print("region height:", context.region.height)

        if mouse_height - gap < total_height:
            compensate_offset = total_height - mouse_height + gap

            if debug:
                print("offsetting up by:", compensate_offset)

            return - compensate_offset / ui_scale

        elif mouse_height + gap > context.region.height:
            compensate_offset = mouse_height - context.region.height + gap

            if debug:
                print("offsetting down by:", compensate_offset)

            return compensate_offset / ui_scale

        else:
            return 0

    def add_mod(self, modtype='WELD', debug=False):

        if self.mod:
            self.cancel_remove_mods.remove(self.mod)

            remove_mod(self.mod)

        self.remove_preceding_mods()

        self.modname = get_new_mod_name(self.active, modtype=modtype, debug=debug)

        if modtype == 'WELD':
            self.mod = add_weld(self.active)

        elif modtype == 'DISPLACE':

            self.mod = add_displace(self.active, mid_level=0, strength=-0.0001)

        elif modtype == 'SOLIDIFY':

            min_dim = get_min_dim(self.active, world_space=False)
            self.mod = add_solidify(self.active, name='Shell', thickness=min_dim / 50)

        self.cancel_remove_mods.add(self.mod)

        mods, mods_len, current_idx = self.get_mods_and_indices()

        if modtype == 'WELD':
            mirrors = [mod for mod in mods if mod.type == 'MIRROR']

            if mirrors:
                last_mirror = mirrors[-1]
                last_mirror_idx = mods.index(last_mirror)

                move_mod(self.mod, last_mirror_idx)
                set_mod_prefix(self.mod, '-', self.modname)

            elif mods_len > 1:
                set_mod_prefix(self.mod, '+', self.modname)

            else:
                self.mod.name = self.modname

        elif modtype == 'DISPLACE':
            earlier = [mod for mod in mods if mod.type in ['HOOK', 'BEVEL', 'SUBSURF', 'DISPLACE'] and mod != self.mod]

            if earlier:
                last_earlier = earlier[-1]
                last_earlier_idx = mods.index(last_earlier)

                move_mod(self.mod, last_earlier_idx + 1)

            else:
                move_mod(self.mod, 0)

            self.mod.name = self.modname

        elif modtype == 'SOLIDIFY':
            earlier = [mod for mod in mods if mod.type in ['HOOK', 'BEVEL', 'SUBSURF', 'DISPLACE', 'SOLIDIFY'] and mod != self.mod]

            if earlier:
                last_earlier = earlier[-1]
                last_earlier_idx = mods.index(last_earlier)

                move_mod(self.mod, last_earlier_idx + 1)

            else:
                move_mod(self.mod, 0)

            self.mod.name = self.modname

        if debug:
            print(f"Added Modifier {self.mod.name} to", self.active.name)

        self.check_multiple_warning(debug=debug)

        self.verify_sorting()

    def add_double_subd(self, index):
        simple = add_subdivision(self.active, subdivision_type='SIMPLE', levels=2)
        simple.name = 'Subdivision (Simple)'

        catmull = add_subdivision(self.active, subdivision_type='CATMULL_CLARK', levels=2)
        catmull.name = 'Subdivision (Catmull Clark)'

        move_mod(simple, index)
        move_mod(catmull, index + 1)

        self.cancel_remove_mods.update((simple, catmull))

        return simple, catmull

    def pick_mod(self, context, index=None, debug=False):
        mods = self.active.modifiers
        active_mod = mods.active

        if self.mod:
            self.mod = list(mods)[index]

        elif active_mod:
            self.mod = active_mod

        else:
            self.mod = self.active.modifiers[-1]

        if self.mod != active_mod:
            self.mod.is_active = True

        self.modname = get_mod_base_name(self.mod)

        if debug:
            print(f"Picked Modifier {self.mod.name} of", self.active.name, "at index", index)

        if self.mod.type == 'SUBSURF':
            self.subd_levels = self.mod.levels
            self.sub_rendr_levels = self.mod.render_levels

        self.populate_batches(context)

        self.check_multiple_warning(debug=debug)

        self.check_tab_finish()

class RemoveUnusedBooleanGizmoManager:
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

        self.gizmo_props['show'] = True
        self.gizmo_props['area_pointer'] = str(self.area.as_pointer())   # NOTE: we have to use self.area, instead of context.area as the tool can be called from the properties panel!
        self.gizmo_props['warp_mouse'] = None

        self.gizmo_data['modifiers'] = []

        for idx, (modname, data) in enumerate(self.remove_dict.items()):
            mod = {'co': data['co'],
                   'co2d': data['co2d'],

                   'index': idx,

                   'modname': modname,
                   'objname': data['obj'].name,

                   'remove': True,
                   'is_highlight': False}

            self.gizmo_data['modifiers'].append(mod)

        context.window_manager.gizmo_group_type_ensure('MACHIN3_GGT_remove_unused_booleans')

    def gizmo_group_finish(self, context):
        self.operator_data.clear()
        self.gizmo_props.clear()
        self.gizmo_data.clear()

        context.window_manager.gizmo_group_type_unlink_delayed('MACHIN3_GGT_remove_unused_booleans')

def draw_remove_unused_boolean_status(op):
    def draw(self, context):
        layout = self.layout

        row = layout.row(align=True)

        row.label(text="Remove Unused Boolean")

        if op.enabled_booleans and not op.is_picking:
            processed, total = op.progress

            processed = str(processed).rjust(len((str(total))))

            r = row.row(align=True)
            r.active = False
            r.label(text=f"Checking: {processed}/{total}")

            mod = op.enabled_booleans[0]
            row.label(text=mod.name)

        elif op.is_picking:

            if not op.highlighted:
                draw_status_item(row, key='LMB', text="Finish")

            draw_status_item(row, key='MMB', text="Viewport")
            draw_status_item(row, key='ESC', text="Cancel")

            row.separator(factor=10)

            draw_status_item(row, active=op.is_alt, key='ALT', text="Âffect all")

            row.separator(factor=2)

            if op.highlighted:
                row.label(text="", icon="RESTRICT_SELECT_OFF")
                row.label(text=op.highlighted['modname'])

                draw_status_item(row, key='F', text="Focus", gap=1)

            else:
                draw_status_item(row, key='F', text="Center Pick" if op.is_alt else "Focus on Active")

            if op.highlighted or op.is_alt:
                draw_status_item(row, key='D', text="Toggle Modifier", gap=2)
                draw_status_item(row, key='X', text="Toggle Remove/Keep Modifier", gap=2)

    return draw

class RemoveUnusedBooleans(bpy.types.Operator, RemoveUnusedBooleanGizmoManager):
    bl_idname = "machin3.remove_unused_booleans"
    bl_label = "MACHIN3: Remove Unused Booleans"
    bl_description = "Look for and remove unused Boolean Modifiers and their Mod Objects"
    bl_options = {'REGISTER', 'UNDO'}

    passthrough = False

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            return context.active_object and context.active_object.type == 'MESH'

    def draw_HUD(self, context):
        if context.area == self.area:

            draw_init(self)

            if self.enabled_booleans and not self.is_picking:
                current_mod = self.enabled_booleans[0]

                processed, total = self.progress
                left = total - processed

                draw_label(context, title="Remove Unused Booleans", coords=Vector((context.region.width / 2, context.region.height / 2)), center=True, color=red, alpha=1)

                self.offset += 18

                draw_label(context, title=f"Checking {processed}/{total}", coords=Vector((context.region.width / 2, context.region.height / 2)), offset=self.offset, center=True, alpha=1)

                self.offset += 18

                draw_label(context, title=current_mod.name, coords=Vector((context.region.width / 2, context.region.height / 2)), offset=self.offset, center=True, alpha=0.5)

                self.offset += 24

                bar_char = "█"
                total_dims = get_text_dimensions(context, text=total * bar_char)

                dims = draw_label(context, title=processed * bar_char, coords=Vector((context.region.width / 2 - total_dims.x / 2, context.region.height / 2)), offset=self.offset, center=False, alpha=1)
                dims += draw_label(context, title=left * bar_char, coords=Vector((context.region.width / 2 - total_dims.x/ 2 + dims.x, context.region.height / 2)), offset=self.offset, center=False, alpha=0.1)
                draw_label(context, title=f"{round((processed / total) * 100)}%".rjust(4), coords=Vector((context.region.width / 2 - total_dims.x/ 2 + dims.x, context.region.height / 2)), offset=self.offset, center=False, alpha=0.5)

            elif self.is_picking:

                ui_system_scale, gizmo_size = get_scale(context, modal_HUD=False, gizmo_size=True)

                if self.gizmo_props['show']:

                    for m in self.gizmo_data['modifiers']:
                        mod = self.active.modifiers.get(m['modname'])

                        color = red if m['remove'] else green
                        alpha = 0.7 if mod.show_viewport else 0.2

                        title = 'remove' if m['remove'] else 'keep'

                        if self.highlighted and m['is_highlight']:

                            coords = m['co2d'] + Vector((32, -3)) * gizmo_size * ui_system_scale
                            draw_label(context, title=title, coords=coords, center=False, color=color, alpha=1)

                            coords = m['co2d'] + Vector((-4.5, -4.5)) * gizmo_size * ui_system_scale * 1.25    # offset left down based on gizmo size

                            dims = get_text_dimensions(context, m['modname'], size=12)
                            coords -= Vector((0, dims.y)) * 1.2                                               # offset down based on the text height (+ some gap), to move into row below gizmos

                            draw_label(context, title=m['modname'], coords=coords, center=False, size=12, color=white, alpha=alpha)

                        elif not self.highlighted:

                            coords = m['co2d'] + Vector((26, -3)) * gizmo_size * ui_system_scale
                            draw_label(context, title=title, coords=coords, center=False, size=10, color=color, alpha=1)

                            coords = m['co2d'] + Vector((-4.5, -4.5)) * gizmo_size * ui_system_scale     # offset left and down based on gizmo size

                            dims = get_text_dimensions(context, m['modname'], size=10)
                            coords -= Vector((0, dims.y)) * 1.2                                         # offset down based on the text height, to move into row below gizmos

                            draw_label(context, title=m['modname'], coords=coords, center=False, size=10, color=white, alpha=alpha)

    def draw_VIEW3D(self, context):
        if context.area == self.area:

            if self.enabled_booleans and not self.is_picking:

                current_mod = self.enabled_booleans[0]

                batch = self.remove_dict[current_mod.name]['batch']

                draw_batch(batch, color=red, alpha=0.1, xray=True)
                draw_batch(batch, color=red, alpha=1, xray=False)

            elif self.is_picking:

                if self.gizmo_props['show']:

                    for m in self.gizmo_data['modifiers']:

                        if m['is_highlight']:
                            batch = self.remove_dict[m['modname']]['batch']
                            draw_batch(batch, color=red if m['remove'] else green, alpha=0.25, xray=True)
                            draw_batch(batch, color=red if m['remove'] else green, alpha=1, xray=False)

                        elif self.is_alt or (not m['remove']):
                            batch = self.remove_dict[m['modname']]['batch']
                            draw_batch(batch, color=red if m['remove'] else green, alpha=0.25)

                    if self.highlighted:
                        for m in self.gizmo_data['modifiers']:
                            if not m['is_highlight']:
                                draw_point(m['co'], size=4, color=red if m['remove'] else green, alpha=0.4)

                else:
                    for m in self.gizmo_data['modifiers']:
                        draw_point(m['co'], size=4, color=red if m['remove'] else green, alpha=0.4)

    def modal(self, context, event):
        if ignore_events(event, timer=False):
            return {'RUNNING_MODAL'}

        self.area.tag_redraw()

        if self.enabled_booleans:
            self.get_unused_booleans(context)

            return {'RUNNING_MODAL'}

        elif self.unused_booleans:

            if not self.is_picking:

                self.gizmo_group_init(context)

                self.highlighted = None
                self.last_highlighted = None

                self.batch = None

                update_mod_keys(self)
                self.is_alt_locked = event.alt

                self.is_picking = True

            if self.is_alt_locked:
                if event.type in alt and event.value == 'PRESS':
                    self.is_alt_locked = False

            if not self.is_alt_locked:
                update_mod_keys(self, event, shift=False, ctrl=False)

            if not self.is_launched_from_3d_view and event.type in alt:
                force_ui_update(context, active=self.active)

            self.highlighted = self.get_highlighted(context)

            events = ['MOUSEMOVE', 'F']

            if self.highlighted or self.is_alt:
                events.extend(['X', 'D'])

            if event.type in events:
                if event.type == 'MOUSEMOVE':

                    if not self.is_launched_from_3d_view:
                        force_ui_update(context, active=self.active)

                    if self.passthrough:
                        self.passthrough = False

                        for m in self.gizmo_data['modifiers']:
                            with context.temp_override(area=self.area, region=self.region, region_data=self.region_data):
                                m['co2d'] = get_location_2d(context, m['co'], default='OFF_SCREEN')

                        self.gizmo_props['show'] = True

                elif event.type in ['X', 'D', 'F'] and event.value == 'PRESS':

                    if event.type == 'X':
                        remove_entries, state = self.get_affected_gizmo_manager_entries('remove')

                        if remove_entries:
                            for m in remove_entries:
                                m['remove'] = state

                        if self.highlighted:
                            self.gizmo_props['warp_mouse'] = Vector((event.mouse_x, event.mouse_y))

                    elif event.type == 'D':
                        mod_entries, state = self.get_affected_gizmo_manager_entries('show_viewport')

                        if mod_entries:
                            for m in mod_entries:
                                mod = self.active.modifiers.get(m['modname'])
                                mod.show_viewport = state

                            if self.highlighted:
                                self.gizmo_props['warp_mouse'] = Vector((event.mouse_x, event.mouse_y))

                    elif event.type == 'F':

                        if event.alt:
                            bpy.ops.view3d.view_center_pick('INVOKE_DEFAULT')

                        else:
                            if self.highlighted:
                                obj = self.active.modifiers.get(self.highlighted['modname']).object

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

            if navigation_passthrough(event, alt=False, wheel=True) and not event.alt:
                self.passthrough = True

                self.gizmo_props['show'] = False

                return {'PASS_THROUGH'}

            finish_events = ['SPACE']

            if not self.highlighted:
                finish_events.append('LEFTMOUSE')

            if event.type in finish_events and event.value == 'PRESS':

                if context.active_object != self.active:
                    bpy.ops.object.select_all(action='DESELECT')

                    context.view_layer.objects.active = self.active
                    self.active.select_set(True)

                operand_objs = set()

                for m in self.gizmo_data['modifiers']:
                    if m['remove']:
                        mod = self.active.modifiers.get(m['modname'])

                        operand_objs.add(mod.object)

                        for obj in mod.object.children_recursive:
                            operand_objs.add(obj)

                        remove_mod(mod)

                remove = []

                for obj in operand_objs:
                    remote = remote_boolean_poll(context, obj)

                    if not remote:
                        remove.append(obj)

                        if obj in self.hidden:
                            self.hidden.remove(obj)

                if remove:
                    bpy.data.batch_remove(remove)

                    bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)

                    with context.temp_override(area=self.area, region=self.region, region_data=self.region_data):
                        draw_fading_label(context, text=f"Removed {len(remove)} unused Boolean Modifiers and their mod objects", y=120, color=red, alpha=1, move_y=40, time=4)

                else:
                    with context.temp_override(area=self.area, region=self.region, region_data=self.region_data):
                        draw_fading_label(context, text="Nothing removed.", y=120, color=green, alpha=1, move_y=20, time=2)

                self.finish(context)
                return {'FINISHED'}

            elif event.type in ['RIGHTMOUSE', 'ESC']:
                self.finish(context)

                return {'CANCELLED'}

            if gizmo_selection_passthrough(self, event):
                return {'PASS_THROUGH'}

            return {'RUNNING_MODAL'}

        else:
            self.finish(context)

            with context.temp_override(area=self.area, region=self.region, region_data=self.region_data):
                draw_fading_label(context, text="✔ There don't seem to be any unused Boolean Modifiers.", y=120, color=green, alpha=1, move_y=30, time=3)

            return {'FINISHED'}

    def finish(self, context):
        finish_modal_handlers(self)

        finish_status(self)

        self.gizmo_group_finish(context)

        if not self.is_launched_from_3d_view:
            force_ui_update(context)

        for obj in self.hidden:
            obj.hide_set(False)

        restore_gizmos(self)

    def invoke(self, context, event):
        self.active = context.active_object
        self.dg = context.evaluated_depsgraph_get()

        self.get_initial_state(self.active)

        view = context.space_data

        if view.type != 'VIEW_3D':
            self.is_launched_from_3d_view = False
            self.area, view, self.region, self.region_data = self.get_3d_view(context)

            if not view:
                popup_message("This operator needs a 3D present in the workspace!")
                return {'CANCELLED'}

        else:
            self.is_launched_from_3d_view = True

            self.area = context.area
            self.region = context.region
            self.region_data = context.region.data

        if self.enabled_booleans:

            self.hidden = {obj for obj in context.visible_objects if is_wire_object(obj)}

            for obj in self.hidden:
                obj.hide_set(True)

            with context.temp_override(area=self.area, region=self.region, region_data=self.region_data):
                self.init_remove_dict(context)

            self.is_picking = False

            hide_gizmos(self, context)

            init_status(self, context, func=draw_remove_unused_boolean_status(self))

            force_ui_update(context)

            with context.temp_override(area=self.area, region=self.region, region_data=self.region_data):
                init_modal_handlers(self, context, hud=True, view3d=True, timer=True)
            return {'RUNNING_MODAL'}

        else:
            with context.temp_override(area=self.area, region=self.region, region_data=self.region_data):
                draw_fading_label(context, text=f"⚠ {self.active.name} doesn't have any (enabled) boolean modifiers!", y=120, color=yellow, alpha=1, move_y=30, time=3)

            return {'CANCELLED'}

    def get_3d_view(self, context):
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        for region in area.regions:
                            if region.type == 'WINDOW':
                                return area, space, region, region.data

        return None, None, None, None

    def get_initial_state(self, obj):
        self.initial_booleans = [mod for mod in obj.modifiers if mod.type == 'BOOLEAN']

        self.invalid_booleans = [mod for mod in self.initial_booleans if not mod.object]

        for mod in self.invalid_booleans:
            remove_mod(mod)

        self.enabled_booleans = [mod for mod in self.initial_booleans if mod.object and mod.show_viewport]

        if self.enabled_booleans:
            self.dimensions = self.dg.objects[obj.name].dimensions.copy()
            self.facecount = len(self.dg.objects[obj.name].data.polygons)

            self.unused_booleans = []

        self.progress = [len(self.invalid_booleans), len(self.initial_booleans)]

    def init_remove_dict(self, context):
        self.remove_dict = {mod.name: {'remove': True,

                                       'obj': mod.object,

                                       'co': None,
                                       'co2d': None,

                                       'batch': None} for mod in self.enabled_booleans}

        for mod in self.enabled_booleans:
            obj = mod.object

            if obj.type == 'MESH' and [mod for mod in obj.modifiers if mod.type in ['ARRAY', 'MIRROR']]:
                bbox = get_bbox(obj.data)[0]
            else:
                bbox = get_eval_bbox(obj)

            co = obj.matrix_world @ average_locations(bbox)
            co2d = get_location_2d(context, co, default='OFF_SCREEN')
            batch = get_batch_from_obj(self.dg, obj)

            self.remove_dict[mod.name]['co'] = co
            self.remove_dict[mod.name]['co2d'] = co2d
            self.remove_dict[mod.name]['batch'] = batch

    def get_unused_booleans(self, context, debug=False):

        mod = self.enabled_booleans.pop(0)

        mod.show_viewport = False
        self.dg.update()

        mod_dimensions = self.dg.objects[self.active.name].dimensions.copy()
        mod_facecount = len(self.dg.objects[self.active.name].data.polygons)

        if debug:
            print(mod.name)
            print(" dimensions;", mod_dimensions)
            print(" facecount:", mod_facecount)

        is_removable = False

        if mod_dimensions == self.dimensions:
            if mod_facecount == self.facecount:
                self.unused_booleans.append(mod)

                is_removable = True

                if debug:
                    print("  can potentially be removed!")

        if not is_removable:
            del self.remove_dict[mod.name]

            if debug:
                print("  should not be removed, deleting from from remove dict")

        mod.show_viewport = True

        self.progress[0] += 1

    def get_highlighted(self, context):
        for m in self.gizmo_data['modifiers']:
            if m['is_highlight']:

                mod = self.active.modifiers.get(m['modname'], None)
                mod.is_active = True

                if m != self.last_highlighted:
                    self.last_highlighted = m
                    force_ui_update(context)

                return m

        if self.last_highlighted:
            self.last_highlighted = None
            force_ui_update(context)

    def get_affected_gizmo_manager_entries(self, prop):
        opd = self.operator_data
        gd = self.gizmo_data

        if self.highlighted:
            state_o = self.highlighted

        elif self.is_alt:
            state_o = gd['modifiers'][0]

        else:
            return None, None

        if self.is_alt:
            entries = [m for m in gd['modifiers']]

        else:
            entries = [state_o]

        if prop == 'show_viewport':
            state = opd['active'].modifiers.get(state_o['modname'], False).show_viewport

        else:
            state = state_o.get(prop, False)

        return entries, not state

    def update_2d_coords(self):
        for m in self.gizmo_data['modifiers']:
            m['co2d'] = Vector(round(i) for i in location_3d_to_region_2d(self.region, self.region_data, m['co'], default=Vector((-1000, -1000))))
        self.active.select_set(True)

class ToggleUnusedBooleanMod(bpy.types.Operator, RemoveUnusedBooleanGizmoManager):
    bl_idname = "machin3.toggle_unused_boolean_mod"
    bl_label = "MACHIN3: Toggle Unused Boolean Mod"
    bl_options = {'REGISTER', 'UNDO'}

    index: IntProperty()
    mode: StringProperty()

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            return bool(RemoveUnusedBooleanGizmoManager().gizmo_data)

    @classmethod
    def description(cls, context, properties):
        if properties:
            gd = RemoveUnusedBooleanGizmoManager.gizmo_data
            opd = RemoveUnusedBooleanGizmoManager.operator_data

            m = gd['modifiers'][properties.index]

            if properties.mode == 'REMOVE':
                action = "Keep" if m['remove'] else "Remove"
                desc = f"{action} Modifier '{m['modname']}' and it's mod object '{m['objname']}'"
                desc += "\nALT: Affect All"

                desc += "\n\nShortcut: X"

            elif properties.mode == 'TOGGLE':
                mod = opd['active'].modifiers.get(m['modname'])

                action = 'Disable' if mod.show_viewport else 'Enable'
                desc = f"{action} Modifier '{m['modname']}'"
                desc += "\nALT: Affect All"

                desc += "\n\nShortcut: D"

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

        active = opd['active']
        self.highlighted = gd['modifiers'][self.index]

        if self.highlighted:

            if self.mode == 'REMOVE':
                remove_entries, state = self.get_affected_gizmo_manager_entries('remove')

                if remove_entries:
                    for m in remove_entries:
                        m['remove'] = state

            elif self.mode == 'TOGGLE':
                mod_entries, state = self.get_affected_gizmo_manager_entries('show_viewport')

                if mod_entries:
                    active = opd['active']

                    for m in mod_entries:
                        mod = active.modifiers.get(m['modname'])
                        mod.show_viewport = state

        return {'FINISHED'}

    def get_affected_gizmo_manager_entries(self, prop):
        opd = self.operator_data
        gd = self.gizmo_data

        state_o = self.highlighted

        if self.is_alt:
            entries = [m for m in gd['modifiers']]

        else:
            entries = [state_o]

        if prop == 'show_viewport':
            state = opd['active'].modifiers.get(state_o['modname'], False).show_viewport

        else:
            state = state_o.get(prop, False)

        return entries, not state

class ToggleAll(bpy.types.Operator):
    bl_idname = "machin3.toggle_all_modifiers"
    bl_label = "MACHIN3: Toggle All Modifiers"
    bl_description = "Toggle All Modifiers\nALT: Toggle Boolean Objects"
    bl_options = {'REGISTER', 'UNDO'}

    toggle_objects: BoolProperty(name="Toggle Objects, instead of Modifiers", default=False)
    active_only: BoolProperty(name="Only apply mods on the active object", default=False)
    def draw(self, context):
        layout = self.layout

        column = layout.column(align=True)
        column.prop(self, 'toggle_objects', toggle=True)

    def invoke(self, context, event):
        self.toggle_objects = event.alt
        return self.execute(context)

    def execute(self, context):
        if self.active_only:
            sel = [context.active_object]

        else:
            sel = {obj for obj in context.selected_objects + [context.active_object] if obj.modifiers}

        for obj in sel:
            if self.toggle_objects:
                objects = [mod.object for mod in obj.modifiers if mod.type == 'BOOLEAN' and mod.object]

                if objects:
                    state = not objects[0].hide_get()

                    ensure_visibility(context, objects, scene=False, select=True)

            else:
                modifiers = [mod for mod in obj.modifiers]

                if modifiers:
                    if context.mode == 'EDIT_MESH':
                        state = not modifiers[0].show_in_editmode

                        for mod in modifiers:
                            mod.show_in_editmode = state

                    elif context.mode == 'OBJECT':
                        state = not modifiers[0].show_viewport

                        for mod in modifiers:
                            mod.show_viewport = state

        return {'FINISHED'}

class ApplyAll(bpy.types.Operator):
    bl_idname = "machin3.apply_all_modifiers"
    bl_label = "MACHIN3: Apply All Modifiers"
    bl_options = {'REGISTER', 'UNDO'}

    backup: BoolProperty(name="Create Backup", description="Create Backup before applying Mods", default=True)
    duplicate: BoolProperty(name="Duplicate", description="Apply Mods on Duplicate", default=False)
    parent_unparented_mod_objects: BoolProperty(name="Parent Unparented", description="Parent unparented Backup Mod Objects", default=True)
    stash_original: BoolProperty(name="Stash Original", default=False)
    stash_cutters: BoolProperty(name="Stash the Cutters", default=False)
    cleanup: BoolProperty(name="Clean Up", description="Clean up the Mesh, after the Mods have been applied", default=True)
    distance: FloatProperty(name="Distance", description="Distance by which Verts get merged", default=0.0001, precision=5, step=0.00001, min=0)
    active_only: BoolProperty(name="Only apply mods on the active object", default=False)
    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            active = context.active_object

            if active and active.type == 'MESH' and not (active.library or (active.data and active.data.library)):
                return get_3dview_space_from_context(context)

    @classmethod
    def description(cls, context, properties):
        desc = "Apply all Modifiers"
        desc += "\nCTRL: Apply Modifiers on Duplicate"
        return desc

    def draw(self, context):
        layout = self.layout

        column = layout.column(align=True)

        row = column.row(align=True)
        row.prop(self, "duplicate", toggle=True)
        row.prop(self, "backup", toggle=True)

        r = row.row(align=True)
        r.active = self.backup
        r.prop(self, "parent_unparented_mod_objects", toggle=True)

        row = column.row(align=True)

        if HC.get_addon('MESHmachine'):
            row.prop(self, "stash_original", toggle=True)
            row.prop(self, "stash_cutters", toggle=True)

        row = column.row(align=True)
        row.prop(self, "cleanup", toggle=True)
        r = row.row(align=True)
        r.active = self.cleanup
        r.prop(self, "distance")

    def invoke(self, context, event):
        meshmachine = bool(HC.get_addon('MESHmachine'))
        self.stash_cutters = meshmachine
        self.stash_original = meshmachine

        self.backup = not event.alt
        self.duplicate = event.ctrl
        return self.execute(context)

    def execute(self, context):
        debug = False

        view = get_3dview_space_from_context(context)
        dg = context.evaluated_depsgraph_get()

        if self.active_only:
            sel = [context.active_object] if any([mod.show_viewport for mod in context.active_object.modifiers]) else []

        else:
            sel = {obj for obj in context.selected_objects + [context.active_object] if any([mod.show_viewport for mod in obj.modifiers])}

        if debug:
            print()
            print("backup:", self.backup)
            print("duplicate:", self.duplicate)
            print("selection:", [obj.name for obj in sel])

        for obj in sel:

            if is_valid_object(obj):

                bpy.ops.object.select_all(action='DESELECT')
                context.view_layer.objects.active = obj
                obj.select_set(True)

                objname = obj.name

                if debug:
                    print("obj:", objname)

                if self.duplicate:

                    obj_tree, _, _, _, _ = self.analyse_object_tree(obj, debug=debug)

                    obj_dup, dups, duplicate_dict = self.duplicate_tree(context, dg, view, obj_tree, debug=debug)

                    self.restore_pre_duplication_visibility(obj, obj_dup, dups, duplicate_dict, debug=debug)

                    obj = obj_dup

                    bpy.ops.object.select_all(action='DESELECT')
                    context.view_layer.objects.active = obj
                    obj.select_set(True)

                if True:
                    if debug:
                        print("\nApplying mods on", obj.name)

                    obj_tree, mod_dict, outside_mod_objects, stashable_mod_objects, removable_mod_objects = self.analyse_object_tree(obj, debug=debug)

                    self.avoid_removing_outside_mirror_mod_objects(outside_mod_objects, removable_mod_objects, debug=debug)

                obj.name = f"{objname}_AppliedMods_on_Duplicate" if self.duplicate else f"{objname}_AppliedMods"

                if self.stash_original:
                    self.stash_orig(obj)

                bevel_cleanup = [('VGROUP', mod.vertex_group) if mod.limit_method == 'VGROUP' else ('WEIGHT', mod.edge_weight) for mod in obj.modifiers if mod.show_viewport and mod.type == 'BEVEL' if mod.limit_method in ['VGROUP', 'WEIGHT']]

                flatten(obj, depsgraph=dg, keep_mods=[mod for mod in obj.modifiers if not mod.show_viewport])

                if self.stash_cutters:
                    self.stash_modobjs(obj, stashable_mod_objects)

                self.remove_removable_and_unused(context, dg, obj, removable_mod_objects, debug=debug)

                self.cleanup_bevels(context, obj, bevel_cleanup)

                self.process_mesh(obj, debug=False)

            if sel and is_valid_object(obj):
                context.view_layer.objects.active = obj
                obj.select_set(True)

        return {'FINISHED'}

    def analyse_object_tree(self, obj, debug=False):
        obj_tree = []
        mod_dict = {}

        get_object_tree(obj, obj_tree=obj_tree, mod_objects=True, mod_dict=mod_dict, include_hidden=('VIEWLAYER', 'COLLECTION'))

        outside_mod_objects = []
        stashable_mod_objects = []
        removable_mod_objects = []

        if debug:
            print("\nentire obj tree")
            for ob in obj_tree:
                print(ob.name)

        if debug:
            print("\nmod objects only")

        for ob, mods in mod_dict.items():

            if ob == obj:
                continue

            if debug:
                print(ob.name, [(mod.name, mod.type, "on", mod.id_data.name) for mod in mods])

            if ob not in obj.children_recursive:
                outside_mod_objects.append((ob, mods))

                if debug:
                    print(" is not in obj's hierarchy")

            if ob.type == 'MESH' and any([mod.type == 'BOOLEAN' and mod.id_data == obj for mod in mods]):
                stashable_mod_objects.append(ob)

                if debug:
                    print(" is stashable")

            if not is_remote_mod_obj(obj, modobj=ob):
                removable_mod_objects.append(ob)

                if debug:
                    print(" is removable")

        return obj_tree, mod_dict, outside_mod_objects, stashable_mod_objects, removable_mod_objects

    def replace_outside_mirror_mod_objects(self, obj_tree, outside_mod_objects, removable_mod_objects, debug=False):
        if debug:
            print("\noutside mod objects")

        for ob, mods in outside_mod_objects:
            if debug:
                print(ob.name, [(mod.name, mod.type, mod.id_data.name) for mod in mods])

            if ob.data and all(mod.type in ['MIRROR'] for mod in mods):
                empty = bpy.data.objects.new("Mirror Empty", object_data=None)
                empty.matrix_world = ob.matrix_world

                if debug:
                    print(" replacing with empty", empty.name)

                for col in ob.users_collection:
                    col.objects.link(empty)

                for mod in mods:
                    mod.mirror_object = empty

                obj_tree.remove(ob)
                obj_tree.append(empty)

                removable_mod_objects.append(empty)

                if not self.duplicate and ob in removable_mod_objects:
                    removable_mod_objects.remove(ob)

    def avoid_removing_outside_mirror_mod_objects(self, outside_mod_objects, removable_mod_objects, debug=False):
        if debug:
            print("\noutside mod objects")

        for ob, mods in outside_mod_objects:
            if debug:
                print(ob.name, [(mod.name, mod.type, mod.id_data) for mod in mods], ob in removable_mod_objects)

            if ob in removable_mod_objects and ob.data and all(mod.type in ['MIRROR'] for mod in mods):
                if debug:
                    print(" avoid removing mod object", ob.name)

                removable_mod_objects.remove(ob)

    def duplicate_tree(self, context, dg, view, obj_tree, debug=False):
        dg.update()

        if debug:
            print("\nduplicating:")

        duplicate_dict = {str(uuid4()): (ob, ob.visible_get()) for ob in obj_tree if ob.name in context.view_layer.objects}

        for dup_hash, (ob, vis) in duplicate_dict.items():
            if debug:
                print(dup_hash, ob.name)

            ob.HC.dup_hash = dup_hash

            if view.local_view and not ob.local_view_get(view):
                if debug:
                    print("  adding", ob.name, "to local view")

                ob.local_view_set(view, True)

            ob.hide_set(False)
            ob.select_set(True)

        bpy.ops.object.duplicate(linked=False)

        obj_dup = context.active_object

        dups = [ob for ob in context.selected_objects if ob != obj_dup]

        return obj_dup, dups, duplicate_dict

    def link_duplicates_to_backup_collection(self, backupcol, obj, obj_backup, dups, duplicate_dict, outside_mod_objects, debug=False):
        outside_objs = [ob for ob, _ in outside_mod_objects]

        if debug:
            print("\nprocessing duplicated for backup")

        for dup in [obj_backup] + dups:

            if dup == obj_backup:
                if debug:
                    print(obj.name, ":", obj_backup.name)

            else:
                orig, vis = duplicate_dict[dup.HC.dup_hash]

                if debug:
                    print(orig.name, ":", dup.name)

                orig.hide_set(not vis)

                if orig in outside_objs:
                    if orig.parent:
                        if debug:
                            print("", orig.name, "is an outside object, whose dup will be unpareted now")

                        unparent(dup)

                if not dup.parent and self.parent_unparented_mod_objects:
                    if debug:
                        print(" parenting", dup.name, "to obj")

                    parent(dup, obj_backup)

                orig.HC.dup_hash = ''
                dup.HC.dup_hash = ''

            for col in dup.users_collection:
                col.objects.unlink(dup)

            backupcol.objects.link(dup)

            if debug:
                print(" added", dup.name, "to backup collection")

    def restore_pre_duplication_visibility(self, obj, obj_dup, dups, duplicate_dict, debug=False):
        if debug:
            print("\nprocessing duplicated for duplication")

        for dup in [obj_dup] + dups:
            if dup == obj_dup:
                print(obj.name, ":", obj_dup.name)

            else:
                orig, vis = duplicate_dict[dup.HC.dup_hash]

                if debug:
                    print(orig.name, ":", dup.name)

                orig.hide_set(not vis)
                dup.hide_set(not vis)

                orig.HC.dup_hash = ''
                dup.HC.dup_hash = ''

    def stash_orig(self, obj):
        MM = HC.addons['meshmachine']['module']

        dup = obj.copy()
        dup.data = obj.data.copy()
        dup.modifiers.clear()

        dup.HC.backupCOL.clear()

        for col in obj.users_collection:
            col.objects.link(dup)

        MM.utils.stash.create_stash(obj, dup)
        bpy.data.meshes.remove(dup.data, do_unlink=True)

    def stash_modobjs(self, obj, modobjs):
        MM = HC.addons['meshmachine']['module']

        for modobj in modobjs:
            MM.utils.stash.create_stash(obj, modobj)

    def remove_removable_and_unused(self, context, dg, obj, removable_mod_objects, debug=False):
        if debug:
            print("\nremoving")

        for ob in removable_mod_objects:
            if debug:
                print(ob, ob.name)

            for c in ob.children_recursive:
                if c not in removable_mod_objects:
                    if debug:
                        print(" re-parenting child object", c.name, "to obj")

                    parent(c, obj)

        bpy.data.batch_remove(removable_mod_objects)

        remove_unused_children(context, obj, depsgraph=dg, debug=debug)

        bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)

    def cleanup_bevels(self, context, obj, data):
        for type, name in data:
            if type == 'VGROUP':
                vgroup = obj.vertex_groups.get(name, None)

                if vgroup:
                    obj.vertex_groups.remove(vgroup)

            elif type == 'WEIGHT':
                if name != 'bevel_weight_edge':
                    if bw := obj.data.attributes.get(name, None):
                        obj.data.attributes.remove(bw)

    def process_mesh(self, obj, debug=False):
        if debug:
            print("\nprocess mesh")

            print("objtype:", obj.HC.objtype)
            print("editmode:", obj.HC.geometry_gizmos_edit_mode)
            print("show geo gizmos:", obj.HC.geometry_gizmos_show)
            print("geo gizmo limit:", obj.HC.geometry_gizmos_show_limit)
            print("geo gizmo cube limit:", obj.HC.geometry_gizmos_show_cube_limit)
            print("gie gizmo cylinder limit ", obj.HC.geometry_gizmos_show_cylinder_limit)

        unhide_deselect(obj.data)

        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bm.normal_update()
        bm.verts.ensure_lookup_table()

        edge_glayer, face_glayer = ensure_gizmo_layers(bm)

        if self.cleanup:
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=self.distance)
            bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=self.distance)

        gangle = 20

        for e in bm.edges:
            if len(e.link_faces) == 2:
                angle = get_face_angle(e)
                e[edge_glayer] = angle >= gangle
            else:
                e[edge_glayer] = 1

        for f in bm.faces:
            if obj.HC.objtype == 'CYLINDER' and len(f.edges) == 4:
                f[face_glayer] = 0
            elif not all(e[edge_glayer] for e in f.edges):
                f[face_glayer] = 0
            else:
                f[face_glayer] = any([get_face_angle(e, fallback=0) >= gangle for e in f.edges])

        bm.to_mesh(obj.data)
        bm.free()

class RemoveAll(bpy.types.Operator):
    bl_idname = "machin3.remove_all_modifiers"
    bl_label = "MACHIN3: Remove All Modifiers"
    bl_description = "Remove All Modifiers\nALT: Keep Cutters"
    bl_options = {'REGISTER', 'UNDO'}

    remove_cutters: BoolProperty(name="Remove Cutters", default=True)
    active_only: BoolProperty(name="Only remove mods from the active object", default=False)
    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            return context.active_object

    def draw(self, context):
        layout = self.layout

        column = layout.column(align=True)
        column.prop(self, 'remove_cutters', toggle=True)

    def invoke(self, context, event):
        self.remove_cutters = not event.alt
        return self.execute(context)

    def execute(self, context):
        if self.active_only:
            sel = [context.active_object]

        else:
            sel = {obj for obj in context.selected_objects + [context.active_object] if obj.modifiers}

        for obj in sel:

            all_modobjs = [(get_mod_obj(mod), mod.type) for mod in obj.modifiers if get_mod_obj(mod)]

            removable =[]

            for modobj, modtype in all_modobjs:

                if not is_remote_mod_obj(obj, modobj=modobj, debug=False):
                    if modtype == 'MIRROR' and modobj.type == 'MESH':
                        break
                    else:
                        removable.append(modobj)

            obj.modifiers.clear()

            if self.remove_cutters:

                children = [o for ob in removable for o in ob.children_recursive]

                bpy.data.batch_remove(removable + children)

                bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)

        return {'FINISHED'}

class ManifoldBooleanConvert(bpy.types.Operator):
    bl_idname = "machin3.manifold_boolean_convert"
    bl_label = "MACHIN3: Manifold Boolean Convert"
    bl_description = "Convert all boolean modifiers in the stack to Manifold Booleans"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (4, 5, 0):
            if context.mode == 'OBJECT':
                if active := context.active_object:
                    return [mod for mod in active.modifiers if mod.type == 'BOOLEAN' and mod.solver != 'MANIFOLD']

    def execute(self, context):
        active = context.active_object

        for mod in active.modifiers:
            if mod.type == 'BOOLEAN' and mod.solver != 'MANIFOLD':
                mod.solver = 'MANIFOLD'

        return {'FINISHED'}
