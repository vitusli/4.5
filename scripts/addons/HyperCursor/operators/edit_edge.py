import bpy
from bpy.props import IntProperty, FloatProperty, BoolProperty, StringProperty
from bpy_extras.view3d_utils import location_3d_to_region_2d

import bmesh
from mathutils import Vector
from mathutils.geometry import intersect_line_line, intersect_line_plane, intersect_point_line

from math import sin, radians, degrees

from .. utils.bmesh import ensure_default_data_layers, ensure_edge_glayer, ensure_gizmo_layers, is_edge_concave
from .. utils.draw import draw_fading_label, draw_line, draw_point, draw_init, draw_label, draw_vector, draw_lines, get_text_dimensions
from .. utils.gizmo import hide_gizmos, restore_gizmos
from .. utils.math import dynamic_format, get_center_between_verts, get_center_between_points, get_edge_normal, average_normals, get_angle_between_edges, get_world_space_normal
from .. utils.modifier import add_bevel, apply_mod, get_edge_bevel_from_edge_vgroup, get_edge_bevel_from_edge_weight, get_edge_bevel_layers, get_edges_from_edge_bevel_mod_vgroup, get_edges_from_edge_bevel_mod_weight, get_new_mod_name, is_edge_bevel, move_mod, remove_mod, sort_modifiers, source_poll, subd_poll, flip_bevel_profile, flop_bevel_profile, get_bevel_profile_as_dict, set_bevel_profile_from_dict
from .. utils.object import get_min_dim
from .. utils.operator import Settings
from .. utils.property import get_biggest_index_among_names, shorten_float_string
from .. utils.select import clear_hyper_edge_selection, get_edges_as_vert_sequences, get_selected_edges, get_hyper_edge_selection
from .. utils.system import printd
from .. utils.ui import draw_status_item_numeric, draw_status_item_precision, finish_modal_handlers, force_geo_gizmo_update, get_mouse_pos, get_mousemove_divisor, ignore_events, init_modal_handlers, is_key, navigation_passthrough, scroll, update_mod_keys, warp_mouse, wrap_mouse, get_zoom_factor, popup_message, init_status, finish_status, scroll_up, scroll_down, force_ui_update, get_scale, draw_status_item
from .. utils.vgroup import add_vgroup, get_vgroup_index
from .. utils.view import get_location_2d, get_view_origin_and_dir

from .. colors import white, yellow, green, red, blue, cyan, orange, normal
from .. items import ctrl, alt, numeric_input_event_items, shift, numbers, input_mappings

def draw_bevel_edge_status(op):
    def draw(self, context):
        layout = self.layout

        if op.is_modifier:
            bevel_mod = op.bevel_mods['active']['mod']
            mod_stack = op.bevel_mods['active']['stack']

        row = layout.row(align=True)
        row.label(text=f"{'Add Modifier' if op.is_modifier and op.is_new_modifier else 'Edit Modifier' if op.is_modifier and not op.is_new_modifier else 'Mesh'} Bevel")

        draw_status_item(row, key='LMB', text="Finish")
        draw_status_item(row, key='RMB', text="Cancel")

        if op.is_hypermod_invocation:
            draw_status_item(row, active=False, text="Returns to HyperMod", gap=1)

            row.separator(factor=2)

        else:
            row.separator(factor=10)

        if op.is_modifier:
            if len(mod_stack) > 1:
                draw_status_item(row, active=op.is_moving, key='ALT', text="Move in Stack")

                if op.is_moving:
                    draw_status_item(row, key='MMB_SCROLL', text="Move Up or Down", gap=2)
                    return

            draw_status_item(row, key='Q', text="Width Mode", prop=op.offset_type.title(), gap=2)

        draw_status_item(row, active=op.loop, key='SHIFT', text="Edge Loop", gap=2)

        if op.is_modifier and bpy.app.version > (4, 3, 0):
            draw_status_item(row, active=op.limit_method == 'WEIGHT', key='E', text="Edge Weight", gap=2)

        draw_status_item(row, active=op.is_chamfer, key='C', text="Chamfer", gap=2)

        if not op.is_chamfer:
            draw_status_item(row, active=not op.is_custom_profile, key='MMB_SCROLL', text="Segments", prop=op.segments, gap=2)

        if op.can_tension_adjust:
            tension = dynamic_format(op.tension, decimal_offset=1)
            draw_status_item(row, key='T', text="Tension", prop=tension, gap=2)

        if op.has_custom_profile:
            draw_status_item(row, active=not op.is_chamfer, key='B', text="Profile", prop=bevel_mod.profile_type.title(), gap=2)

            if op.is_custom_profile and not op.is_chamfer:
                draw_status_item(row, key='F', text="Flip Profile", gap=1)
                draw_status_item(row, key='V', text="Flop Profile", gap=1)

        draw_status_item(row, active=op.active.show_wire, key='W', text="Wireframe", gap=2)

        if op.is_modifier and not op.is_moving:
            draw_status_item(row, key='A', text="Apply Mod + Finish", gap=2)
            draw_status_item(row, key='X', text="Remove Mod + Finish", gap=1)

    return draw

class BevelEdge(bpy.types.Operator, Settings):
    bl_idname = "machin3.bevel_edge"
    bl_label = "MACHIN3: Bevel"
    bl_options = {'REGISTER', 'UNDO'}

    index: IntProperty(name="Index of Edge accociated with Gizmo, that is to be beveled")
    is_hypermod_invocation: BoolProperty(name="is HyperMod incocation", default=False)
    limit_method: StringProperty(name="LIMIT METHOD", default='VGROUP')
    offset_type: StringProperty(name="Offset Type", default='OFFSET')
    width: FloatProperty(name="Bevel Modifier Width", default=0)
    width_pct: FloatProperty(name="Bevel Modifier Width", default=0, min=0, max=100)
    tension: FloatProperty(name="Tension", default=0.5, min=0, max=1)
    segments: IntProperty(name="Bevel Segments", default=0, min=0)
    profile_segments: IntProperty(name="Bevel Profile Segments", default=0, min=0)
    profile_type: StringProperty(name="Profile Type", default='SUPERELLIPSE')
    is_chamfer: BoolProperty(name="Chamfer", default=False)
    use_full: BoolProperty(name="use special FULL 100% Bevel mode", default=True)
    loop: BoolProperty(name="Loop Bevel", default=False)
    is_modifier: BoolProperty(name="is Bevel Modifier", default=False)
    is_new_modifier: BoolProperty(name="is new Bevel Modifier", default=False)

    is_profile_drop: BoolProperty(name="is Profile Drop", default=False)
    has_custom_profile: BoolProperty(name="has Custom Profile", default=False)
    passthrough = None
    is_hypermod_invocation: BoolProperty()

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            active = context.active_object
            return active and active.select_get() and active.HC.ishyper

    @classmethod
    def description(cls, context, properties):
        if properties:
            return f"Bevel (Modifier) Edge {properties.index}\nALT: Repeat Previous Bevel\nCTRL: Use Mesh Bevel instead"
        return "Invalid Context"

    def draw_HUD(self, context):
        if context.area == self.area:

            if not (self.is_modifier and not self.is_new_modifier) and not self.is_tension_adjusting and self.init_loc_2d:
                draw_point(self.init_loc_2d.resized(3), size=4, alpha=1)

                mouse_dir = self.mouse_pos - self.init_loc_2d
                draw_vector(mouse_dir.resized(3), origin=self.init_loc_2d.resized(3), fade=True, alpha=0.5)

            draw_init(self)

            if self.is_modifier:
                bevel_mod = self.bevel_mods['active']['mod']
                has_instanced_mods = self.bevel_mods['instanced']

                if self.is_new_modifier:

                    limit_method = f"🔧 {'Move' if self.is_moving else 'Add'} Modifier{'s' if has_instanced_mods else ''}: "

                    dims = draw_label(context, title=limit_method, coords=Vector((self.HUD_x, self.HUD_y)), center=False, color=yellow, alpha=1)
                    action_dims = dims.copy()

                    dims += draw_label(context, title=f"{bevel_mod.name} ", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, color=white, alpha=0.5)

                    if has_instanced_mods:
                        draw_label(context, title="on active", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, size=9, color=white, alpha=0.3)

                        for data in self.bevel_mods['instanced']:
                            self.offset += 18

                            idims = draw_label(context, title=f"{data['mod'].name} ", coords=Vector((self.HUD_x + action_dims.x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=0.25)
                            idims += draw_label(context, title="on instance ", coords=Vector((self.HUD_x + action_dims.x + idims.x, self.HUD_y)), offset=self.offset, center=False, size=9, color=white, alpha=0.15)
                            draw_label(context, title=data['obj'].name, coords=Vector((self.HUD_x + action_dims.x + idims.x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=0.25)

                else:
                    if self.all_mods:
                        pass

                    else:

                        limit_method = f"🔧 {'Move' if self.is_moving else 'Edit'} Modifier{'s' if has_instanced_mods else''}: "

                        dims = draw_label(context, title=limit_method, coords=Vector((self.HUD_x, self.HUD_y)), center=False, color=green, alpha=1)
                        action_dims = dims.copy()

                        dims += draw_label(context, title=f"{bevel_mod.name} ", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, color=white, alpha=0.5)

                        if has_instanced_mods:
                            draw_label(context, title="on active", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, size=9, color=white, alpha=0.3)

                            for data in self.bevel_mods['instanced']:
                                self.offset += 18

                                idims = draw_label(context, title=f"{data['mod'].name} ", coords=Vector((self.HUD_x + action_dims.x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=0.25)
                                idims += draw_label(context, title="on instance ", coords=Vector((self.HUD_x + action_dims.x + idims.x, self.HUD_y)), offset=self.offset, center=False, size=9, color=white, alpha=0.15)
                                draw_label(context, title=data['obj'].name, coords=Vector((self.HUD_x + action_dims.x + idims.x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=0.25)

            else:

                dims = draw_label(context, title='🌐 Mesh Bevel ', coords=Vector((self.HUD_x, self.HUD_y)), center=False, color=white, alpha=1)

                if self.instanced_objects:
                    draw_label(context, title="on active", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, size=10, color=white, alpha=0.5)

                    for obj in self.instanced_objects:
                        self.offset += 12
                        idims = draw_label(context, title="on instance ", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, size=10, color=white, alpha=0.25)
                        draw_label(context, title=obj.name, coords=Vector((self.HUD_x + dims.x + idims.x, self.HUD_y)), offset=self.offset, center=False, size=10, color=white, alpha=0.5)

            if self.is_moving:
                ui_scale = get_scale(context)

                self.offset += 24

                stack_dims = draw_label(context, title="Stack: ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=0.5)

                for idx, mod in enumerate(self.bevel_mods['active']['stack']):
                    if idx:
                        self.offset += 18

                    is_sel = mod == self.bevel_mods['active']['mod']

                    color = yellow if self.is_new_modifier and is_sel else green if is_sel else white
                    size, alpha = (12, 1) if is_sel else (10, 0.5)

                    if is_sel:
                        coords = [Vector((self.HUD_x + stack_dims.x - (5 * ui_scale), self.HUD_y - (self.offset * ui_scale), 0)), Vector((self.HUD_x + stack_dims.x - (5 * ui_scale), self.HUD_y - (self.offset * ui_scale) + (10 * ui_scale), 0))]
                        draw_line(coords, color=color, width=2 * ui_scale, screen=True)

                    dims = draw_label(context, title=mod.name, coords=Vector((self.HUD_x + stack_dims.x, self.HUD_y)), offset=self.offset, center=False, size=size, color=color, alpha=alpha)

                    if mod.profile_type == 'CUSTOM':
                        draw_label(context, title=" 🌠", coords=Vector((self.HUD_x + stack_dims.x + dims.x, self.HUD_y)), offset=self.offset, center=False, size=size, color=blue, alpha=alpha)

            else:

                self.offset += 18
                bevel_type_color = orange if self.is_concave else blue

                if self.is_modifier:
                    bevel_mod = self.bevel_mods['active']['mod']
                    is_percent = self.offset_type == 'PERCENT'
                    width = dynamic_format(bevel_mod.width_pct if is_percent else bevel_mod.width, decimal_offset=1)

                    alpha = 0.3 if width == '0' else 0.5 if self.is_tension_adjusting else 1
                    dims = draw_label(context, title="Width: ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=alpha)

                    if self.offset_type == 'FULL':
                        draw_label(context, title="FULL", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=normal, alpha=alpha)
                    else:
                        color = green if is_percent else yellow
                        draw_label(context, title=f"{width}{'%' if is_percent else''}", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=color, alpha=alpha)

                else:
                    width = dynamic_format(self.width, decimal_offset=1)

                    alpha = 0.3 if width == '0' else 0.5 if self.is_tension_adjusting else 1
                    color = white if self.is_tension_adjusting else yellow

                    dims = draw_label(context, title="Width: ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=alpha)
                    draw_label(context, title=width, coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=color, alpha=alpha)

                if self.can_tension_adjust:
                    self.offset += 18

                    color, alpha = (yellow, 1) if self.is_tension_adjusting else (white, 0.5)

                    dims = draw_label(context, title="Tension: ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=alpha)
                    draw_label(context, title=dynamic_format(self.tension, decimal_offset=1), coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=color, alpha=alpha)

                self.offset += 18

                if self.is_chamfer:
                    dims = draw_label(context, title="Chamfer ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=bevel_type_color, alpha=1)

                    if self.has_custom_profile:
                        draw_label(context, title="🌠", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=bevel_type_color, alpha=1)

                else:
                    alpha = 0.3 if (self.is_custom_profile or self.segments == 0) else 1
                    segments = self.profile_segments if self.is_custom_profile else self.segments

                    dims = draw_label(context, title=f"Segments: {segments} ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=alpha)

                    if self.has_custom_profile:
                        text = "Custom Profile" if self.is_custom_profile else "🌠"
                        draw_label(context, title=text, coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=bevel_type_color, alpha=1)

                if self.is_modifier and bpy.app.version >= (4, 3, 0):
                    self.offset += 18

                    limit_method, color = ("Vertex Group", normal) if self.limit_method == 'VGROUP' else ('Edge Weight', green)
                    draw_label(context, title=limit_method, coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=color, alpha=1)

                if self.loop:
                    self.offset += 18
                    draw_label(context, title="Edge Loop", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=yellow, alpha=1)

                if self.active.show_wire:
                    self.offset += 18
                    draw_label(context, title="Wireframe", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=blue, alpha=1)

                if not self.is_chamfer and self.is_custom_profile and self.profile_HUD_coords:
                    draw_line(self.profile_HUD_coords, width=2, color=bevel_type_color, alpha=0.75)
                    draw_line(self.profile_HUD_border_coords, width=1, color=white, alpha=0.1)

                    for dir, origin in self.profile_HUD_edge_dir_coords:
                        draw_vector(dir, origin=origin, color=bevel_type_color, fade=True)

    def modal(self, context, event):
        if ignore_events(event):
            return {'RUNNING_MODAL'}

        context.area.tag_redraw()

        if self.is_hypermod_invocation and event.type == 'TAB' and event.value == 'RELEASE':
            context.window.cursor_set('SCROLL_X')

        if event.type == 'MOUSEMOVE':
            get_mouse_pos(self, context, event)

            if self.is_modifier and not self.is_new_modifier:
                wrap_mouse(self, context, x=not self.is_tension_adjusting, y=self.is_tension_adjusting)

            if self.is_custom_profile:
                self.get_profile_HUD_coords(context)

        self.is_custom_profile = self.has_custom_profile and self.profile_type == 'CUSTOM'

        self.can_tension_adjust = not self.is_custom_profile and not self.is_chamfer and self.segments and not self.is_moving

        if self.can_tension_adjust and is_key(self, event, 'T', onpress=self.update_tension_adjustment(context, 'PRESS'), onrelease=self.update_tension_adjustment(context, 'RELEASE')):
            divisor = get_mousemove_divisor(event, 3, 15, 1, sensitivity=50)

            delta_y = self.mouse_pos.y - self.last_mouse.y
            delta_tension = delta_y / divisor

            self.tension += delta_tension

            if self.is_modifier:
                for mod in self.get_affected_mods():
                    mod.profile = self.tension

            else:
                self.mesh_bevel(context, offset=self.width, profile=self.tension, loop=self.loop)

            self.last_mouse = self.mouse_pos
            return {'RUNNING_MODAL'}

        if self.is_modifier and len(self.bevel_mods['active']['stack']) > 1:
            self.is_moving = event.alt

        if self.is_moving:

            if scroll(event, key=True):
                if scroll_up(event, key=True):
                    self.move_bevel_mod_in_stack(direction='UP')

                else:
                    self.move_bevel_mod_in_stack(direction='DOWN')

            elif event.type in {'LEFTMOUSE', 'SPACE'} and event.value == 'PRESS':
                self.finish(context)

                if self.is_modifier:
                    profile = get_bevel_profile_as_dict(self.bevel_mods['active']['mod'])
                    self.store_settings('bevel_edge', {'custom_profile': profile})

                clear_hyper_edge_selection(context, self.active)

                self.validate_modifier_edge_bevels(context)
                return {'FINISHED'}

            elif event.type in {'RIGHTMOUSE', 'ESC'} and event.value == 'PRESS':

                if self.is_new_modifier:
                    self.cancel_new_modifier()

                else:
                    self.cancel_existing_modifier()

                if self.have_vgroups_changed or self.have_edge_weights_changed or self.has_loop_changed:
                    self.initbm.to_mesh(self.active.data)
                    self.initbm.free()

                self.finish(context)
                return {'CANCELLED'}

            return {'RUNNING_MODAL'}

        events = ['MOUSEMOVE', 'C', 'W', *shift, *alt, *ctrl]

        if self.is_modifier:
            events.append('Q')

        if self.has_custom_profile:
            events.append('B')

        if self.is_custom_profile:
            events.extend(['F', 'V'])

        if self.is_modifier and bpy.app.version > (4, 3, 0):
            events.extend(['E', 'L'])

        if event.type in events or (not self.is_chamfer and scroll(event, key=True)):

            if event.type == 'MOUSEMOVE':

                if self.passthrough:
                    self.passthrough = False

                    if self.is_modifier and not self.is_new_modifier:
                        self.last_mouse = self.mouse_pos

                self.get_width(context, event)

                if self.is_modifier:
                    for mod in self.get_affected_mods():
                        self.set_mod_bevel_width(mod)

            elif event.type in ['E', 'L'] and event.value == 'PRESS':
                self.switch_limit_method()

                if self.loop:
                    self.loop_selection(debug=False)

            elif event.type == 'Q' and event.value == 'PRESS':

                if self.offset_type == 'OFFSET':
                    self.offset_type = 'PERCENT'

                    if self.is_modifier and not self.is_new_modifier:
                        self.width_pct = self.width * (100 / self.min_dim)

                elif self.offset_type == 'PERCENT':
                    if self.use_full:
                        self.offset_type = 'FULL'

                    else:
                        self.offset_type = 'OFFSET'

                        if self.is_modifier and not self.is_new_modifier:
                            self.width = self.width_pct / (100 / self.min_dim)

                elif self.offset_type == 'FULL':
                    self.offset_type = 'OFFSET'

                    self.width = self.width_pct / (100 / self.min_dim)

                self.get_width(context, event)

                for mod in self.get_affected_mods():
                    mod.offset_type = 'PERCENT' if self.offset_type == 'FULL' else self.offset_type

                    self.set_mod_bevel_width(mod)

            elif not self.is_custom_profile and not self.is_chamfer and scroll(event, key=True):
                change = 1

                if scroll_up(event, key=True):
                    self.segments += change

                elif scroll_down(event, key=True):
                    self.segments -= change

                if self.is_modifier:

                    for mod in self.get_affected_mods():
                        mod.segments = self.segments + 1

                self.can_tension_adjust = not self.is_custom_profile and not self.is_chamfer and self.segments and not self.is_moving

            elif event.type == 'C' and event.value == 'PRESS':
                self.is_chamfer = not self.is_chamfer

                if self.is_modifier:

                    for mod in self.get_affected_mods():
                        mod.segments = 1 if self.is_chamfer else self.profile_segments if self.is_custom_profile else self.segments + 1

            elif event.type == 'B' and event.value == 'PRESS':

                if self.is_chamfer and self.profile_type == 'CUSTOM':
                    self.is_chamfer = False

                elif self.profile_type == 'SUPERELLIPSE':
                    self.profile_type = 'CUSTOM'

                else:
                    self.profile_type = 'SUPERELLIPSE'

                if self.profile_type == 'CUSTOM':

                    if self.is_chamfer:
                        self.is_chamfer = False

                    self.profile_segments = len(self.bevel_mods['active']['mod'].custom_profile.points) - 2

                    for mod in self.get_affected_mods():
                       mod.profile_type = 'CUSTOM'
                       mod.segments = self.profile_segments + 1

                    self.get_profile_HUD_coords(context)

                elif self.profile_type == 'SUPERELLIPSE':
                    for mod in self.get_affected_mods():
                        mod.profile_type = 'SUPERELLIPSE'
                        mod.segments = self.segments + 1

            elif event.type == 'F' and event.value == 'PRESS':
                for mod in self.get_affected_mods():
                    flip_bevel_profile(mod)

                self.get_profile_HUD_coords(context)

            elif event.type == 'V' and event.value == 'PRESS':
                for mod in self.get_affected_mods():
                    flop_bevel_profile(mod)

                self.get_profile_HUD_coords(context)

            elif event.type == 'W' and event.value == 'PRESS':
                self.active.show_wire = not self.active.show_wire

            if event.type in shift:
                self.loop = not self.loop

                if self.is_modifier:
                    self.loop_selection(debug=False)

                    self.has_loop_changed = True

            force_ui_update(context, self.active)

        if self.is_modifier:

            if event.type == 'X' and event.value == 'PRESS':
                self.finish(context)

                for data in self.get_affected_mods(data=True):
                    mod, hostobj = data['mod'], data['obj']
                    is_on_active = hostobj == self.active

                    remove_mod(mod)

                    if is_on_active:
                        if self.vgroup:
                            self.active.vertex_groups.remove(self.vgroup)

                        if self.weight_name:
                            bw = self.active.data.attributes.get(self.weight_name, None)

                            if bw:
                                self.active.data.attributes.remove(bw)

                clear_hyper_edge_selection(context, self.active)

                self.validate_modifier_edge_bevels(context)
                return {'FINISHED'}

            if event.type == 'A' and event.value == 'PRESS':
                self.finish(context)

                vg_name = self.vgroup.name if self.vgroup else None
                bw_name = self.weight_name
                old_mesh = None

                for data in self.get_affected_mods(data=True):
                    mod, hostobj = data['mod'], data['obj']
                    is_on_active = hostobj == self.active

                    if is_on_active:

                        if self.bevel_mods['instanced']:
                            old_mesh = hostobj.data

                        apply_mod(mod)

                        if vg_name:
                            vg = self.active.vertex_groups.get(vg_name)

                            if vg:
                                self.active.vertex_groups.remove(vg)

                        if self.weight_name:
                            bw = self.active.data.attributes.get(bw_name, None)

                            if bw:
                                self.active.data.attributes.remove(bw)

                    else:
                        remove_mod(mod)

                        hostobj.data = self.active.data

                if self.bevel_mods['instanced'] and old_mesh:
                    bpy.data.meshes.remove(old_mesh)

                clear_hyper_edge_selection(context, self.active)

                self.validate_modifier_edge_bevels(context)

                force_geo_gizmo_update(context)
                return {'FINISHED'}

        else:
            self.mesh_bevel(context, offset=self.width, loop=self.loop)

            force_ui_update(context, self.active)

        if navigation_passthrough(event, alt=False) and self.is_modifier and not self.is_new_modifier:
            self.passthrough = True

            return {'PASS_THROUGH'}

        elif event.type in {'LEFTMOUSE', 'SPACE'} and event.value == 'PRESS':
            self.finish(context)

            if self.is_modifier:

                profile = get_bevel_profile_as_dict(self.bevel_mods['active']['mod'])
                self.store_settings('bevel_edge', {'custom_profile': profile})

            clear_hyper_edge_selection(context, self.active)

            self.validate_modifier_edge_bevels(context)

            if self.is_hypermod_invocation:
                bpy.ops.machin3.hyper_modifier('INVOKE_DEFAULT', is_gizmo_invocation=False, is_button_invocation=False, mode='PICK')
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'} and event.value == 'PRESS':
            self.finish(context)

            if self.is_modifier:

                if self.is_new_modifier:
                    self.cancel_new_modifier()

                else:
                    self.cancel_existing_modifier()

                if self.have_vgroups_changed or self.have_edge_weights_changed or self.has_loop_changed:
                    self.initbm.to_mesh(self.active.data)
                    self.initbm.free()

            else:

                self.initbm.to_mesh(self.active.data)
                self.initbm.free()

            if self.is_hypermod_invocation:
                bpy.ops.machin3.hyper_modifier('INVOKE_DEFAULT', is_gizmo_invocation=False, is_button_invocation=False, mode='PICK')
            return {'CANCELLED'}

        self.last_mouse = self.mouse_pos

        return {'RUNNING_MODAL'}

    def finish(self, context):
        finish_modal_handlers(self)

        if self.is_modifier and not self.is_new_modifier:
            context.window.cursor_set('DEFAULT')

        restore_gizmos(self)

        self.active.show_wire = False

        finish_status(self)

        force_ui_update(context)

    def invoke(self, context, event):
        self.active = context.active_object
        self.mx = self.active.matrix_world
        self.min_dim = get_min_dim(self.active, world_space=False)  # used for get pct width in absolute mode (new mod or mesh bevel)

        if bpy.app.version >= (4, 3, 0):
            self.avoid_double_assignments()

        self.initbm = bmesh.new()
        self.initbm.from_mesh(self.active.data)
        self.initbm.edges.ensure_lookup_table()

        vg_layer = ensure_default_data_layers(self.initbm, vertex_groups=True, bevel_weights=False, crease=False)[0]

        if self.index == -1:
            if not self.is_hypermod_invocation:
                self.is_hypermod_invocation = True

            if self.is_hypermod_invocation:
                mod = self.active.modifiers.active

                if mod and is_edge_bevel(mod, simple=False):

                    if mod.limit_method == 'VGROUP':

                        vg_index = get_vgroup_index(self.active, mod.vertex_group)

                        vg_edges = get_edges_from_edge_bevel_mod_vgroup(self.initbm, vg_layer, vg_index)

                        if vg_edges:
                            self.edge = vg_edges[0]

                        else:
                            return {'CANCELLED'}

                    elif mod.limit_method == 'WEIGHT':
                        bw_edges = get_edges_from_edge_bevel_mod_weight(self.initbm, mod.edge_weight)

                        if bw_edges:
                            self.edge = bw_edges[0]

                        else:
                            return {'CANCELLED'}

                else:
                    return {'CANCELLED'}

        else:

            self.edge = self.initbm.edges[self.index]

        self.is_concave = is_edge_concave(self.edge)

        bevel_mod = self.unify_vgroups_and_edge_weights(vg_layer, mesh_bevel=event.ctrl)

        self.postunifybm = bmesh.new()
        self.postunifybm.from_mesh(self.active.data)
        self.postunifybm.edges.ensure_lookup_table()

        if event.alt:
            if self.is_modifier and self.width != 0:
                self.modifier_bevel(context, mod=bevel_mod, redo=True, debug=False)

                if self.loop:
                    self.loop_selection(debug=False)

                clear_hyper_edge_selection(context, self.active)
                return {'FINISHED'}

            elif not self.is_modifier and self.width != 0:
                self.mesh_bevel(context, offset=self.width, loop=self.loop)

                clear_hyper_edge_selection(context, self.active)

                force_ui_update(context)
                return {'FINISHED'}

            else:
                return {'CANCELLED'}

        else:

            self.loop = False if bevel_mod else self.active.HC.objtype == 'CYLINDER'

            self.is_modifier = not event.ctrl

            if self.is_modifier:
                self.modifier_bevel(context, mod=bevel_mod, redo=False, debug=False)

                if self.loop:
                    self.loop_selection(debug=False)

            else:
                self.instanced_objects = [obj for obj in bpy.data.objects if obj.data == self.active.data and obj != self.active] if self.active.data.users > 1 else None

                self.width = 0

        self.has_custom_profile = self.is_modifier and len(self.bevel_mods['active']['mod'].custom_profile.points) > 2
        self.is_custom_profile = self.has_custom_profile and self.bevel_mods['active']['mod'].profile_type == 'CUSTOM'

        if bevel_mod:
            self.factor = get_zoom_factor(context, self.mx @ get_center_between_verts(*[v for v in self.edge.verts]))

        get_mouse_pos(self, context, event, init_offset=True)

        self.get_profile_HUD_coords(context)

        if self.is_modifier and not self.is_new_modifier:

            self.last_mouse = self.mouse_pos

            context.window.cursor_set('SCROLL_X')

        else:

            self.edge_loc = self.get_mouse_edge_intersection(context, self.mouse_pos - self.mouse_offset)

            self.init_loc_2d = get_location_2d(context, self.edge_loc)

            warp_mouse(self, context, self.init_loc_2d, region=True)

            self.loc = self.get_view_plane_intersection(context, self.mouse_pos)
            self.init_loc = self.loc

        self.is_chamfer = (mod := self.bevel_mods['active']['mod']).profile_type == 'CUSTOM' and mod.segments == 1 if self.is_modifier else False
        self.is_moving = False
        self.all_mods = False
        self.has_loop_changed = False

        self.is_tension_adjusting = False
        self.tension_mouse = self.mouse_pos
        self.can_tension_adjust = not self.is_custom_profile and not self.is_chamfer and self.segments and not self.is_moving

        if self.is_modifier:
            self.get_mod_stack(init=True)

        self.active.show_wire = True

        hide_gizmos(self, context)

        force_ui_update(context)

        init_status(self, context, func=draw_bevel_edge_status(self))

        init_modal_handlers(self, context, hud=True)
        return {'RUNNING_MODAL'}

    def avoid_double_assignments(self):
        objects = [obj for obj in bpy.data.objects if obj.data == self.active.data]

        for obj in objects:
            edge_bevels = [mod for mod in obj.modifiers if is_edge_bevel(mod)]

            for mod in edge_bevels:
                if mod.limit_method == 'VGROUP' and mod.edge_weight:
                    mod.edge_weight = ''
                    print(f"WARNING: Fixed double VGROUP/WEIGHT assignment of {mod.name} on {obj.name}")

                if mod.limit_method == 'WEIGHT' and mod.vertex_group:
                    mod.vertex_group = ''
                    print(f"WARNING: Fixed double WEIGHT/VGROUP assignment of {mod.name} on {obj.name}")

    def unify_vgroups_and_edge_weights(self, vg_layer, mesh_bevel=False):
        weight_bevel_mod, weight_name = self.unify_bevel_weights(self.initbm, mesh_bevel=mesh_bevel)

        vg_bevel_mod, vg_name = self.unify_vgroups(vg_layer, mesh_bevel=mesh_bevel, debug=False)

        bevel_mod = weight_bevel_mod if weight_bevel_mod else vg_bevel_mod if vg_bevel_mod else None

        if weight_bevel_mod:
            self.limit_method = 'WEIGHT'

        elif vg_bevel_mod:
            self.limit_method = 'VGROUP'

        return bevel_mod

    def unify_bevel_weights(self, bm, mesh_bevel=False, debug=False):

        if debug:
            print()
            print("unify bevel weights")

        self.have_edge_weights_changed = False

        edge_weight_layers = get_edge_bevel_layers(bm)

        bevel_mod, weight_name = get_edge_bevel_from_edge_weight(bm, self.active, self.edge)

        if weight_name and mesh_bevel:
            if debug:
                print("clearing index edge's weight layer", weight_name, "due to mesh beveling")

            bm = bmesh.new()
            bm.from_mesh(self.active.data)

            bw = bm.edges.layers.float.get(weight_name)
            bm.edges.layers.float.remove(bw)

            bm.to_mesh(self.active.data)

            self.have_edge_weights_changed = True

        if not self.is_profile_drop:
            if debug:
                print()
                print("mesh bevel:", mesh_bevel)
                print("index edge:", self.edge.index)
                print()
                print("bevel mod:", bevel_mod.name if bevel_mod else None)
                print("bevel weight:", weight_name)

            hyper_selected_edges = get_hyper_edge_selection(self.initbm)
            other_edges = [e for e in hyper_selected_edges if e != self.edge]

            if other_edges:
                selected_edges = [self.edge] + other_edges

                bm = bmesh.new()
                bm.from_mesh(self.active.data)
                bm.edges.ensure_lookup_table()

                has_weight_changed = False

                for e in selected_edges:
                    edge = bm.edges[e.index]

                    for name in edge_weight_layers:
                        bw = bm.edges.layers.float.get(name)

                        if name != weight_name and edge[bw]:
                            if debug:
                                print("clearing edge's", e.index, "bevel weight from layer", name)

                            edge[bw] = 0
                            has_weight_changed = True

                        if name == weight_name and not edge[bw]:
                            edge[bw] = 1
                            has_weight_changed = True

                if has_weight_changed:
                    self.have_edge_weights_changed = True

                    bm.to_mesh(self.active.data)

        if debug:
            print()
            print("edge weight change?:", self.have_edge_weights_changed)
            print("return:", bevel_mod, weight_name)

        return bevel_mod, weight_name

    def unify_vgroups(self, vg_layer, mesh_bevel=False, debug=False):

        self.have_vgroups_changed = False

        bevel_mod, vg_name = get_edge_bevel_from_edge_vgroup(self.active, self.edge, vg_layer)

        vg = self.active.vertex_groups[vg_name] if vg_name else None

        if vg and mesh_bevel:
            vert_ids = [v.index for v in self.edge.verts]

            vg.remove(vert_ids)

            bevel_mod, vg_name = None, None

            self.have_vgroups_changed = True

        if not self.is_profile_drop:

            if debug:
                print()
                print("mesh bevel:", mesh_bevel)
                print("index edge:", self.edge.index)
                print(" vgroup:", f"{vg.name} index: {vg.index}" if vg else None)

            hyper_selected_edges = get_hyper_edge_selection(self.initbm)
            other_edges = [e for e in hyper_selected_edges if e != self.edge]

            if other_edges:
                selected_edges = [self.edge] + other_edges
                selected_verts = set(v for e in selected_edges for v in e.verts)

                sideways_edges = [e for v in selected_verts for e in v.link_edges if e not in selected_edges]

                sideways_vgroups = {v.index: set() for v in selected_verts}

                if debug:
                    print()
                    print("sideways edges:")

                for e in sideways_edges:
                    edge_vgroups = [idx for idx in e.verts[0][vg_layer].keys() if idx in e.verts[1][vg_layer].keys()]

                    if debug:
                        print("  edge_vgroups:", edge_vgroups)

                    for v in e.verts:
                        if v.index in sideways_vgroups:
                            sideways_vgroups[v.index].update(edge_vgroups)

                if debug:
                    printd(sideways_vgroups, name='sideways vgroups')

                if debug:
                    if debug:
                        print()
                        print(" other edges:")

                for other_edge in other_edges:
                    if debug:
                        print("  edge:", other_edge.index)

                    other_bevel_mod, other_vg_name = get_edge_bevel_from_edge_vgroup(self.active, other_edge, vg_layer)

                    if other_vg_name != vg_name:
                        other_vert_ids = [v.index for v in other_edge.verts]

                        if vg_name:
                            if debug:
                                print(f"   needs to be (re)assigned from vgroup '{other_vg_name}' to '{vg_name}'")

                            if vg_name:
                                vg.add(other_vert_ids, 1, 'ADD')

                        else:
                            if debug:
                                print(f"   vgroup '{other_vg_name}' needs to be cleared")

                        if other_vg_name:
                            other_vg = self.active.vertex_groups[other_vg_name]

                            for v in other_edge.verts:
                                if other_vg.index in sideways_vgroups[v.index]:
                                    other_vert_ids.remove(v.index)

                                    if debug:
                                        print(f"    avoiding removal of vgroup '{other_vg_name}' from vert {v.index}, as it has a sideways edge using the vgroup")

                            other_vg.remove(other_vert_ids)

                        self.have_vgroups_changed = True

        if debug:
            print()
            print("vgroup change?:", self.have_vgroups_changed)
            print("return:", bevel_mod, vg_name)

        return bevel_mod, vg_name

    def get_unique_vgroup_or_bevel_weight_name(self):
        vg_names = [vg.name for vg in self.active.vertex_groups if 'Edge Bevel' in vg.name]
        bw_names = [att.name for att in self.active.data.attributes if 'Edge Bevel' in att.name]

        idx = get_biggest_index_among_names(vg_names + bw_names)

        if idx is None:
            return 'Edge Bevel'
        else:
            return f'Edge Bevel.{str(idx + 1).zfill(3)}'

    def get_profile_HUD_coords(self, context):
        self.profile_HUD_coords = []
        self.profile_HUD_border_coords = []
        self.profile_HUD_edge_dir_coords = []

        if self.has_custom_profile:
            profile = self.bevel_mods['active']['mod'].custom_profile
            points = profile.points

            ui_scale = get_scale(context)
            size = 100

            offset_x = get_text_dimensions(context, text=f"Segments: {len(points) - 2} Custom Profile ")[0]
            offset_y = -(9 + (len(self.bevel_mods['instanced']) * 18) * ui_scale) - size

            offset = Vector((offset_x, offset_y))

            for p in points:
                co = Vector((self.HUD_x, self.HUD_y)) + offset + p.location * size
                self.profile_HUD_coords.append(co.resized(3))

            for corner in [(0, 0), (0, 100), (100, 100), (100, 0), (0, 0)]:
                co = Vector((self.HUD_x, self.HUD_y)) + offset + Vector(corner)
                self.profile_HUD_border_coords.append(co.resized(3))

            self.profile_HUD_edge_dir_coords.append((Vector((-size * 0.7, 0, 0)), Vector((self.HUD_x, self.HUD_y, 0)) + offset.resized(3) + Vector((0, size, 0))))
            self.profile_HUD_edge_dir_coords.append((Vector((0, -size * 0.7, 0)), Vector((self.HUD_x, self.HUD_y, 0)) + offset.resized(3) + Vector((size, 0, 0))))

    def get_mouse_edge_intersection(self, context, mouse_pos):
        view_origin, view_dir = get_view_origin_and_dir(context, mouse_pos)

        i = intersect_line_line(self.mx @ self.edge.verts[0].co, self.mx @ self.edge.verts[1].co, view_origin, view_origin + view_dir)

        if i:
            return i[0]

    def get_view_plane_intersection(self, context, mouse_pos):
        view_origin, view_dir = get_view_origin_and_dir(context, mouse_pos)

        i = intersect_line_plane(view_origin, view_origin + view_dir, self.edge_loc, view_dir)

        if i:
            return i

    def get_mod_stack(self, init=False, debug=False):
        stack = [mod for mod in self.active.modifiers if is_edge_bevel(mod)]

        if debug:
            print()
            print("stack:")

            for mod in stack:
                idx = list(self.active.modifiers).index(mod)
                print("*" if mod == self.bevel_mods['active']['mod'] else " ", idx, mod.name)

        self.bevel_mods['active']['stack'] = stack

        if init and not self.is_new_modifier:
            self.initial['stack_orders'][self.active] = {mod: list(self.active.modifiers).index(mod) for mod in stack}

        for data in self.bevel_mods['instanced']:
            hostobj = data['obj']

            data['stack'] = [m for m in hostobj.modifiers if is_edge_bevel(m)]

            if init and not self.is_new_modifier:
                self.initial['stack_orders'][hostobj] = {m: list(hostobj.modifiers).index(m) for m in data['stack']}

    def move_bevel_mod_in_stack(self, direction='UP'):
        for data in self.get_affected_mods(data=True):
            mod, hostobj, stack = data['mod'], data['obj'], data['stack']

            list_idx = stack.index(mod)

            if direction == 'UP':
                if list_idx == 0:
                    continue

                prev_mod = stack[list_idx - 1]
                prev_idx = list(hostobj.modifiers).index(prev_mod)

                move_mod(mod, prev_idx)

            elif direction == 'DOWN':
                if list_idx == len(stack) - 1:
                    continue

                next_mod = stack[list_idx + 1]
                next_idx = list(hostobj.modifiers).index(next_mod)
                move_mod(mod, next_idx)

        self.get_mod_stack()

    def get_affected_mods(self, data=False) -> list:
        bevels = self.bevel_mods

        if data:
            return [bevels['active']] + [data for data in bevels['instanced']]
        else:
            return [bevels['active']['mod']] + [data['mod'] for data in bevels['instanced']]

    def get_width(self, context, event):
        if self.offset_type == 'FULL':
            return

        if self.is_modifier and not self.is_new_modifier:
            divisor = 2 if event.ctrl else 10
            delta_x = self.mouse_pos.x - self.last_mouse.x

            delta_width = delta_x / divisor * self.factor
            delta_width_pct = delta_x / divisor  # percent bevels should not be distance based, so don't use the factor

            self.width += delta_width
            self.width_pct += delta_width_pct

        else:
            self.loc = self.get_view_plane_intersection(context, self.mouse_pos)

            self.width = (self.mx.to_3x3().inverted_safe() @ (self.loc - self.init_loc)).length

            self.width_pct = self.width * (100 / self.min_dim)

    def update_tension_adjustment(self, context, value='PRESS'):
        def press():
            self.is_tension_adjusting = True
            context.window.cursor_set('SCROLL_Y')

            self.tension_mouse = self.mouse_pos

        def release():
            self.is_tension_adjusting = False
            context.window.cursor_set('SCROLL_X')

            warp_mouse(self, context, self.tension_mouse)

        if value == 'PRESS':
            return press

        elif value == 'RELEASE':
            return release

    def validate_modifier_edge_bevels(self, context, debug=False):

        removed_vgroups = []
        removed_edge_weights = []
        removed_mods = []

        objects = [obj for obj in bpy.data.objects if obj.data == self.active.data]
        instances = [obj for obj in objects if obj != self.active]

        group_indices_in_use = set(group.group for v in self.active.data.vertices for group in v.groups)

        edge_bevel_vgroup_names = [(vg.name, vg.index in group_indices_in_use) for vg in self.active.vertex_groups if 'Edge Bevel' in vg.name]

        edge_bevel_weight_layer_names = [(att.name, any(data.value for data in att.data)) for att in self.active.data.attributes if 'Edge Bevel' in att.name]

        bm = bmesh.new()
        bm.from_mesh(self.active.data)
        vg_layer = ensure_default_data_layers(bm, vertex_groups=True, bevel_weights=False, crease=False)[0]
        for name, referenced_by_verts in edge_bevel_vgroup_names:

            if referenced_by_verts:
                vg_index = get_vgroup_index(self.active, name)

                if not get_edges_from_edge_bevel_mod_vgroup(bm, vg_layer, vg_index):
                    if debug:
                        print(f"removing vertex group {name} because it's not referencing any edges")

                    vg = self.active.vertex_groups.get(name, None)

                    self.active.vertex_groups.remove(vg)
                    removed_vgroups.append(f"Removed unused vertex group '{name}'")

            else:
                vg = self.active.vertex_groups.get(name, None)

                if vg:
                    if debug:
                        print(f"removing vertex group {name} because it's not referenced by any vert")

                    self.active.vertex_groups.remove(vg)
                    removed_vgroups.append(f"Removed unused vertex group '{name}'")

        edge_bevels = [mod for obj in objects for mod in obj.modifiers if is_edge_bevel(mod) and mod.limit_method == 'VGROUP']

        for mod in edge_bevels:
            vgname = mod.vertex_group

            if not vgname or vgname not in self.active.vertex_groups:
                modname = mod.name
                objname = mod.id_data.name

                if debug:
                    print(f"removing modifier {modname} on {objname} because it has no vertex group")

                remove_mod(mod)

                removed_mods.append(f"Removed unused Edge Bevel modifier '{modname}'")

                if instances:
                    removed_mods[-1] += f"on {objname}"

        edge_bevels = [mod for obj in objects for mod in obj.modifiers if is_edge_bevel(mod) and mod.limit_method == 'VGROUP']

        for name, referenced_by_verts in edge_bevel_vgroup_names:
            if referenced_by_verts:
                if any(mod.vertex_group == name for mod in edge_bevels):
                    continue

                vg = self.active.vertex_groups.get(name, None)

                if vg:
                    if debug:
                        print(f"removing vertex group {name} because it's not referenced by any Edge Bevel mod")

                    self.active.vertex_groups.remove(vg)
                    removed_vgroups.append(f"Removed unused vertex group '{name}'")

        if bpy.app.version >= (4, 3, 0):

            for name, referenced_by_edges in edge_bevel_weight_layer_names:
                if not referenced_by_edges:
                    bw = self.active.data.attributes.get(name, None)

                    if bw:
                        if debug:
                            print(f"removing edge weight layer {name} because it's not referenced by any edge")

                        self.active.data.attributes.remove(bw)
                        removed_edge_weights.append(f"Removed unused edge weight layer '{name}'")

            edge_bevels = [mod for obj in objects for mod in obj.modifiers if is_edge_bevel(mod) and mod.limit_method == 'WEIGHT']

            for mod in edge_bevels:
                weight_name = mod.edge_weight

                if not weight_name or weight_name not in self.active.data.attributes:
                    modname = mod.name
                    objname = mod.id_data.name

                    if debug:
                        print(f"removing modifier {modname} on {objname} because it has no vertex group")

                    remove_mod(mod)

                    removed_mods.append(f"Removed unused Edge Bevel modifier '{modname}'")

                    if instances:
                        removed_mods[-1] += f"on {objname}"

            edge_bevels = [mod for obj in objects for mod in obj.modifiers if is_edge_bevel(mod) and mod.limit_method == 'WEIGHT']

            for name, referenced_by_edges in edge_bevel_weight_layer_names:
                if referenced_by_edges:
                    if any(mod.edge_weight == name for mod in edge_bevels):
                        continue

                    bw = self.active.data.attributes.get(name, None)

                    if bw:
                        if debug:
                            print(f"removing edge weight layer {name} because it's not referenced by any Edge Bevel mod")

                        self.active.data.attributes.remove(bw)
                        removed_edge_weights.append(f"Removed unused edge weight layer '{name}'")

        edge_bevels = [mod for mod in self.active.modifiers if is_edge_bevel(mod, simple=False)]

        for mod in edge_bevels:
            if mod.limit_method == 'VGROUP':
                vg_name = mod.vertex_group
                vg = self.active.vertex_groups.get(vg_name)

                if vg and vg.name != mod.name:
                    vg.name = mod.name
                    mod.vertex_group = mod.name

                    if debug:
                        print(f"Renamed vertex group {vg_name} to {mod.name}")

            elif mod.limit_method == 'WEIGHT':
                bw_name = mod.edge_weight
                bw = self.active.data.attributes.get(bw_name)

                if bw and bw.name != mod.name:
                    bw.name = mod.name
                    mod.edge_weight = bw.name

                    if debug:
                        print(f"Renamed edge weight layer {bw_name} to {mod.name}")

        edge_bevels = [mod for obj in instances for mod in obj.modifiers if is_edge_bevel(mod)]

        for mod in edge_bevels:
            if mod.limit_method == 'VGROUP':
                vg = mod.id_data.vertex_groups.get(mod.name)

                if vg and vg.name != mod.vertex_group:
                    mod.vertex_group = mod.name

                    if debug:
                        print(f"Renamed vertex group {vg_name} to {mod.name}")

            elif mod.limit_method == 'WEIGHT':
                bw = mod.id_data.data.attributes.get(mod.name)

                if bw and bw.name != mod.edge_weight:
                    mod.edge_weight = mod.name

                    if debug:
                        print(f"Renamed edge weight layer {bw_name} to {mod.name}")

        if removed_vgroups or removed_edge_weights or removed_mods:
            draw_fading_label(context, text=removed_vgroups + removed_edge_weights + removed_mods, color=yellow)

    def switch_limit_method(self):
        if self.limit_method == 'VGROUP':
            self.limit_method = 'WEIGHT'

        else:
            self.limit_method = 'VGROUP'

        if self.is_new_modifier:
            edges = set(get_hyper_edge_selection(self.initbm, debug=False))
            edges.add(self.edge)

        else:
            bevel_mod = self.bevel_mods['active']['mod']

            if bevel_mod.limit_method == 'VGROUP':
                vg_layer = self.postunifybm.verts.layers.deform.verify()
                vg_index = get_vgroup_index(self.active, bevel_mod.vertex_group)

                edges = get_edges_from_edge_bevel_mod_vgroup(self.postunifybm, vg_layer, vg_index)

            else:
                edges = get_edges_from_edge_bevel_mod_weight(self.postunifybm, bevel_mod.edge_weight)

        if self.limit_method == 'VGROUP':
            verts = set(v for e in edges for v in e.verts)
            vertids = [v.index for v in verts]

            if not self.vgroup:
                vg_name = self.get_unique_vgroup_or_bevel_weight_name()
                self.vgroup = add_vgroup(self.active, vg_name, ids=vertids, weight=1)

            else:
                self.vgroup.add(vertids, 1, "ADD")

            for mod in self.get_affected_mods():
                mod.limit_method = self.limit_method
                mod.vertex_group = self.vgroup.name
                mod.edge_weight = ''

        else:
            bm = self.postunifybm.copy()
            bm.edges.ensure_lookup_table()

            if not self.weight_name:
                self.weight_name = self.get_unique_vgroup_or_bevel_weight_name()

            bw = bm.edges.layers.float.get(self.weight_name)

            if not bw:
                bw = bm.edges.layers.float.new(self.weight_name)

            for e in edges:
                edge = bm.edges[e.index]
                edge[bw] = 1

            bm.to_mesh(self.active.data)

            for mod in self.get_affected_mods():
                mod.limit_method = self.limit_method
                mod.edge_weight = self.weight_name
                mod.vertex_group = ''

    def loop_selection(self, debug=False):
        if self.limit_method == 'VGROUP':
            self.loop_vgroup(debug=debug)

        elif self.limit_method == 'WEIGHT':
            self.loop_bevel_weight(debug=debug)

    def loop_vgroup(self, debug=False):

        bm = self.initbm.copy()
        bm.edges.ensure_lookup_table()

        edge_gizmo_layer = ensure_edge_glayer(bm)
        edges = get_selected_edges(bm, index=self.index, loop=self.loop, loop_ensure_gizmo=edge_gizmo_layer)

        if debug:
            print([e.index for e in edges])

        allvertids = [v.index for v in bm.verts]
        self.vgroup.remove(allvertids)

        vertids = list({v.index for e in edges for v in e.verts})

        if debug:
            print(vertids)

        self.vgroup.add(vertids, 1, "ADD")

        bm.free()

    def loop_bevel_weight(self, debug=False):

        bm = self.initbm.copy()
        bm.edges.ensure_lookup_table()

        edges = get_selected_edges(bm, index=self.index, loop=self.loop)
        edge_indices = [e.index for e in edges]

        if debug:
            print([idx for idx in edge_indices])

        bm = bmesh.new()
        bm.from_mesh(self.active.data)
        bm.edges.ensure_lookup_table()

        bw = bm.edges.layers.float.get(self.weight_name)

        for e in bm.edges:
            e[bw] = 0

        for idx in edge_indices:
            edge = bm.edges[idx]
            edge[bw] = 1

        bm.to_mesh(self.active.data)

    def mesh_bevel(self, context, offset=0, profile=0.5, loop=False):
        bm = self.postunifybm.copy()
        bm.normal_update()
        bm.edges.ensure_lookup_table()

        edge_glayer, face_glayer = ensure_gizmo_layers(bm)

        edges = get_selected_edges(bm, index=self.index, loop=loop)

        geo = bmesh.ops.bevel(bm, geom=edges, offset=offset, offset_type='OFFSET', loop_slide=True, segments=1 if self.is_chamfer else self.segments + 1, profile=self.tension, affect='EDGES')

        if self.active.HC.objtype == 'CUBE':
            for e in geo['edges']:
                e[edge_glayer] = 1

            for f in geo['faces']:
                f[face_glayer] = 1

        elif self.active.HC.objtype == 'CYLINDER':

            cap_faces = [f for f in bm.faces if len(f.verts) != 4]

            if len(cap_faces) == 2:
                cyl_dir = (cap_faces[0].calc_center_median() - cap_faces[1].calc_center_median()).normalized()

                for e in geo['edges']:

                    if e[edge_glayer] == 1:
                        continue

                    else:
                        edge_dir = (e.verts[0].co - e.verts[1].co).normalized()
                        dot = abs(edge_dir.dot(cyl_dir))

                        e[edge_glayer] = dot < 0.5

            for f in geo['faces']:
                f[face_glayer] = 0

        if geo['edges']:
            shortest = min([e.calc_length() for e in geo['edges']])

            bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=shortest / 10)

        bm.to_mesh(self.active.data)
        bm.free()

    def set_mod_bevel_width(self, mod):
        if self.offset_type == 'FULL':
            if mod.width_pct != 100:
                mod.width_pct = 100

        else:

            if mod.offset_type == 'OFFSET':
                mod.width = self.width

            elif mod.offset_type == 'PERCENT':
                mod.width_pct = self.width_pct

    def modifier_bevel(self, context, mod=None, redo=False, debug=False):

        self.vgroup = None
        self.weight_name = None

        instanced_objects = [obj for obj in bpy.data.objects if obj != self.active and obj.data == self.active.data and not source_poll(context, obj)] if self.active.data.users > 1 else []

        self.bevel_mods = {'active': {'obj': self.active,
                                      'mod': None,
                                      'all': [],
                                      'stack': []},

                           'instanced': [{'obj': obj,
                                          'mod': None,
                                          'all': []} for obj in instanced_objects],
                                          'stack': []}

        if mod:

            self.bevel_mods['active']['mod'] = mod

            if mod.limit_method == 'VGROUP':
                self.vgroup = self.active.vertex_groups[mod.vertex_group]

            elif mod.limit_method == 'WEIGHT':
                self.weight_name = mod.edge_weight

            for data in self.bevel_mods['instanced']:

                if mod.limit_method == 'VGROUP':
                    mods = [m for m in data['obj'].modifiers if is_edge_bevel(m) and m.vertex_group == mod.vertex_group]

                elif mod.limit_method == 'WEIGHT':
                    mods = [m for m in data['obj'].modifiers if is_edge_bevel(m) and m.edge_weight == mod.edge_weight]

                else:
                    mods = None

                if mods:
                    data['mod'] = mods[0]

            if debug:
                print()
                print(f"editing bevel mod '{mod.name}' on active '{self.active.name}'")

                for data in self.bevel_mods['instanced']:
                    print(f" fetched bevel mod '{data['mod'].name}' on instanced obj '{data['obj'].name} too'")

            self.is_new_modifier = False

        else:
            edges = get_hyper_edge_selection(self.initbm, debug=False)

            modname = get_new_mod_name(self.active, modtype="EDGEBEVEL")

            if self.limit_method == 'VGROUP':
                edge_vert_ids = set(v.index for v in self.edge.verts)
                selected_vert_ids = set(v.index for e in edges for v in e.verts)
                vertids = list(edge_vert_ids | selected_vert_ids)

                vg_name = self.get_unique_vgroup_or_bevel_weight_name()

                self.vgroup = add_vgroup(self.active, vg_name, ids=vertids, weight=1)

                self.bevel_mods['active']['mod'] = add_bevel(self.active, name=modname, width=0, limit_method='VGROUP', vertex_group=vg_name)

                for data in self.bevel_mods['instanced']:
                    data['mod'] = add_bevel(data['obj'], name=modname, width=0, limit_method='VGROUP', vertex_group=self.vgroup.name)

                if bpy.app.version >= (4, 3, 0):

                    for mod in self.get_affected_mods():
                        mod.edge_weight = ''

            elif self.limit_method == 'WEIGHT':
                edge_indices = set(e.index for e in edges) | set([self.edge.index])

                bm = bmesh.new()
                bm.from_mesh(self.active.data)
                bm.edges.ensure_lookup_table()

                bw_name = self.get_unique_vgroup_or_bevel_weight_name()
                bw = bm.edges.layers.float.new(bw_name)

                for idx in edge_indices:
                    edge = bm.edges[idx]
                    edge[bw] = 1

                bm.to_mesh(self.active.data)

                self.bevel_mods['active']['mod'] = add_bevel(self.active, name=modname, width=0, limit_method='WEIGHT', weight_layer=bw_name)

                self.weight_name = bw_name

                for data in self.bevel_mods['instanced']:
                    data['mod'] = add_bevel(data['obj'], name=modname, limit_method='WEIGHT', weight_layer=self.weight_name)

            for data in self.get_affected_mods(data=True):
                mod, hostobj = data['mod'], data['obj']

                idx = list(hostobj.modifiers).index(mod)

                other_bevel_indices = [list(hostobj.modifiers).index(m) for m in hostobj.modifiers if is_edge_bevel(m) and m != mod]

                if other_bevel_indices and idx != (newidx := other_bevel_indices[-1] + 1):
                    move_mod(mod, newidx)

                else:
                    sort_modifiers(hostobj, remove_invalid=False, debug=False)

            self.is_new_modifier = True

        for mod in self.get_affected_mods():

            if self.is_new_modifier:
                mod.segments = 1 if self.is_chamfer else self.segments + 1

            else:
                mod.is_active = True
                mod.show_viewport = True

        if redo:

            profile = self.fetch_setting('bevel_edge', 'custom_profile')

            for mod in self.get_affected_mods():
                offset_type = 'PERCENT' if self.offset_type == 'FULL' else self.offset_type
                mod.offset_type = offset_type

                self.set_mod_bevel_width(mod)

                mod.segments = 1 if self.is_chamfer else self.segments + 1
                mod.profile = self.tension
                mod.profile_type = self.profile_type

                if profile and len(profile['points']) > 1:
                    set_bevel_profile_from_dict(mod, profile)

        else:
            bevel_mod = self.bevel_mods['active']['mod']

            if not self.is_new_modifier:
                self.initial = {}

                if self.is_profile_drop and (profile := self.active.HC.get('init_custom_profile', None)):
                    self.initial['custom_profile'] = dict(profile)

                    self.segments = profile['segments'] - 1

                else:
                    self.initial['custom_profile'] = get_bevel_profile_as_dict(mod)

                self.initial['offset_type'] = bevel_mod.offset_type
                self.initial['width'] = bevel_mod.width
                self.initial['width_pct'] = bevel_mod.width_pct
                self.initial['profile'] = bevel_mod.profile
                self.initial['limit_method'] = bevel_mod.limit_method
                self.initial['vertex_group'] = bevel_mod.vertex_group

                if bpy.app.version >= (4, 3, 0):
                    self.initial['edge_weight'] = bevel_mod.edge_weight

                self.initial['segments'] = self.initial['custom_profile']['segments']                   # both of these are part of the profile, which has been potentially dropped
                self.initial['profile_type'] = self.initial['custom_profile']['profile_type']           # so that's why we get the profile first

                self.initial['vgroup'] = self.vgroup
                self.initial['weight_name'] = self.weight_name

                self.initial['stack_orders'] = {}

            self.offset_type = 'FULL' if bevel_mod.width_pct == 100 else bevel_mod.offset_type
            self.width = bevel_mod.width
            self.width_pct = bevel_mod.width_pct
            self.tension = bevel_mod.profile

            self.profile_type = bevel_mod.profile_type

            if self.profile_type == 'SUPERELLIPSE':
                self.segments = bevel_mod.segments - 1

            elif self.profile_type == 'CUSTOM':
                self.profile_segments = len(bevel_mod.custom_profile.points) - 2

        if debug:
            printd(self.bevel_mods, name="bevel mods")

            if not self.is_new_modifier:
                printd(self.initial, name="initial")

    def cancel_new_modifier(self):
        mods = self.get_affected_mods()

        for mod in mods:
            remove_mod(mod)

        if self.vgroup:
            self.active.vertex_groups.remove(self.vgroup)

        if self.weight_name:
            bw = self.active.data.attributes.get(self.weight_name)

            if bw:
                self.active.data.attributes.remove(bw)

    def cancel_existing_modifier(self):
        for mod in self.get_affected_mods():
            mod.offset_type = self.initial['offset_type']
            mod.width = self.initial['width']
            mod.width_pct = self.initial['width_pct']
            mod.profile = self.initial['profile']
            mod.limit_method = self.initial['limit_method']
            mod.vertex_group = self.initial['vertex_group']

            if bpy.app.version >= (4, 3, 0):
                mod.edge_weight = self.initial['edge_weight']

            mod.segments = self.initial['segments']
            mod.profile_type = self.initial['profile_type']

            if not self.is_new_modifier:
                set_bevel_profile_from_dict(mod, self.initial['custom_profile'])

        if self.vgroup and not self.initial['vgroup']:
            self.active.vertex_groups.remove(self.vgroup)

        if self.weight_name and not self.initial['weight_name']:
            bw = self.active.data.attributes.get(self.weight_name)

            if bw:
                self.active.data.attributes.remove(bw)

        if self.is_profile_drop and (_data := self.active.HC.get('init_custom_profile', None)):
            del self.active.HC['init_custom_profile']

        for data in self.get_affected_mods(data=True):
            if len(data['stack']) > 1:
                stack_order = self.initial['stack_orders'].get(data['obj'])

                for mod, idx in stack_order.items():
                    if idx != list(mod.id_data.modifiers).index(mod):
                        move_mod(mod, idx)

class RemoveEdge(bpy.types.Operator):
    bl_idname = "machin3.remove_edge"
    bl_label = "MACHIN3: Remove Edge"
    bl_options = {'REGISTER', 'UNDO'}

    index: IntProperty(name="Index of Edge accociated with Gizmo, that is to be removed")

    loop: BoolProperty(name="Loop Edge Selection", default=False)
    loop_min_angle: IntProperty(name="Min Angle", default=60, min=0, max=180)
    loop_prefer_center_of_three: BoolProperty(name="Prefer Center of 3 Edges", default=True)
    ring: BoolProperty(name="Ring Edge Selection", default=False)
    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            active = context.active_object
            return active and active.select_get() and active.HC.ishyper

    def draw(self, context):
        layout = self.layout

        column = layout.column(align=True)

        if self.loop:
            column.prop(self, 'loop_prefer_center_of_three', toggle=True)
            column.prop(self, 'loop_min_angle', toggle=True)

    @classmethod
    def description(cls, context, properties):
        return "Remove Edge\nSHIFT: Remove Edge Loop\nCTRL: Remove Edge Ring"

    def invoke(self, context, event):
        self.loop = event.shift
        self.ring = event.ctrl
        return self.execute(context)

    def execute(self, context):
        active = context.active_object

        self.remove_edges(active, loop=self.loop, ring=self.ring)

        clear_hyper_edge_selection(context, active)

        return {'FINISHED'}

    def remove_edges(self, active, loop=False, ring=False):
        bm = bmesh.new()
        bm.from_mesh(active.data)
        bm.normal_update()
        bm.edges.ensure_lookup_table()

        edges = get_selected_edges(bm, index=self.index, loop=self.loop, loop_min_angle=180 - self.loop_min_angle, loop_prefer_center_of_three=self.loop_prefer_center_of_three, ring=ring)

        bmesh.ops.dissolve_edges(bm, edges=edges, use_verts=True, use_face_split=False)

        bm.normal_update()
        bm.to_mesh(active.data)
        bm.free()

def draw_loop_cut_status(op):
    def draw(self, context):
        layout = self.layout

        row = layout.row(align=True)

        row.label(text=f"{'Loop Cut'}")

        draw_status_item(row, key='LMB', text="Finish")
        draw_status_item(row, key='RMB', text="Cancel")

        row.separator(factor=10)

        draw_status_item(row, key='MOVE', text="Slide")

        draw_status_item(row, key='MMB_SCROLL', text="Cuts", prop=op.cuts, gap=2)

        draw_status_item(row, active=op.ring_ngons, key='G', text="Cut Ngons", gap=2)

    return draw

class LoopCut(bpy.types.Operator):
    bl_idname = "machin3.loop_cut"
    bl_label = "MACHIN3: Loop Cut"
    bl_description = "Loop Cut selected Edges\nALT: Repeat Previous Loop Cut\nCTRL: Force Ring Selection even with Hyper Selected Edges"
    bl_options = {'REGISTER', 'UNDO'}

    index: IntProperty(name="Index of Edge that is to be loop cut")

    cuts: IntProperty(name="Number of Loop Cuts", default=1, min=1)
    amount: FloatProperty(name="Side Amount", default=0, min=-1, max=1)
    ring: BoolProperty(name="Use Ring Selection", default=False)
    ring_ngons: BoolProperty(name="Ring Select across n-gons", default=True)
    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            active = context.active_object
            return active and active.select_get() and active.HC.ishyper

    def draw_VIEW3D(self, context):
        if context.area == self.area:
            if self.data['coords']:
                for seq_coords in self.data['coords']:
                    draw_line(seq_coords, mx=self.mx, color=yellow, width=2, alpha=0.5)

    def draw_HUD(self, context):
        if context.area == self.area:
            hud = self.HUD_coords

            slide_remapped = self.amount + 1

            if self.is_vertical:
                draw_line((hud['bottom_left'], hud['top_left']), width=2, alpha=0.3)

                if self.snap:
                    for i in range(19):
                        snap_y = hud['height_gap'] + (hud['guide_height'] / 20) * (i + 1)
                        draw_point(Vector((hud['width_gap'], snap_y, 0)), size=5 if i == 9 else 4, alpha=1 if i == 9 else 0.2)

                space = hud['guide_height'] / (self.cuts + 1)

                first_hud_y = space * slide_remapped + hud['height_gap']

                for idx, cut in enumerate(range(self.cuts)):
                    draw_point(Vector((hud['width_gap'], first_hud_y + space * idx, 0)), color=yellow)

            else:
                draw_line((hud['top_left'], hud['top_right']), width=2, alpha=0.3)

                if self.snap:
                    for i in range(19):
                        snap_x = hud['width_gap'] + (hud['guide_width'] / 20) * (i + 1)
                        draw_point(Vector((snap_x, hud['height_gap'] * 9, 0)), size=5 if i == 9 else 4, alpha=1 if i == 9 else 0.2)

                space = hud['guide_width'] / (self.cuts + 1)

                first_hud_x = space * slide_remapped + hud['width_gap']

                for idx, cut in enumerate(range(self.cuts)):
                    draw_point(Vector((first_hud_x + space * idx, hud['height_gap'] * 9, 0)), color=yellow)

            draw_init(self)

            draw_label(context, title="Loop Cut", coords=Vector((self.HUD_x, self.HUD_y)), center=False, color=white, alpha=1)

            self.offset += 18
            draw_label(context, title=f"Slide: {round(self.amount * 100)}%", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=1)

            if self.snap:
                self.offset += 18
                draw_label(context, title="Snapping", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=yellow, alpha=1)

    def modal(self, context, event):
        if ignore_events(event):
            return {'RUNNING_MODAL'}

        context.area.tag_redraw()

        self.snap = event.ctrl

        events = ['MOUSEMOVE', *ctrl, 'N', 'G']

        if event.type in events or scroll(event, key=True):

            if event.type in ['MOUSEMOVE', *ctrl]:
                get_mouse_pos(self, context, event)

                hud = self.HUD_coords

                if self.is_vertical:

                    if self.mouse_pos.y < hud['height_gap']:
                        warp_mouse(self, context, Vector((self.mouse_pos.x, hud['height_gap'])))

                    elif self.mouse_pos.y > hud['height_gap'] * 9:
                        warp_mouse(self, context, Vector((self.mouse_pos.x, hud['height_gap'] * 9)))

                    divisor = hud['guide_height'] / 2
                    subtractor = hud['mid_height'] / divisor

                    self.amount = self.mouse_pos.y / divisor - subtractor

                else:
                    if self.mouse_pos.x < hud['width_gap']:
                        context.window.cursor_warp(hud['width_gap'], event.mouse_y)
                        warp_mouse(self, context, Vector((hud['width_gap'], self.mouse_pos.y)))

                    elif self.mouse_pos.x > hud['width_gap'] * 9:
                        warp_mouse(self, context, Vector((hud['width_gap'] * 9, self.mouse_pos.y)))

                    divisor = hud['guide_width'] / 2
                    subtractor = hud['mid_width'] / divisor

                    self.amount = self.mouse_pos.x / divisor - subtractor

                if self.snap:
                    self.amount = round(self.amount, 1)

            elif scroll(event, key=True):
                if scroll_up(event, key=True):
                    self.cuts += 1

                elif scroll_down(event, key=True):
                    self.cuts -= 1

                force_ui_update(context)

            elif event.type in ['G', 'N'] and event.value == 'PRESS':
                self.ring_ngons = not self.ring_ngons

                force_ui_update(context)

            self.loop_cut(context, cuts=self.cuts, amount=self.amount)

        if event.type in {'LEFTMOUSE', 'SPACE'} and event.value == 'PRESS':
            self.finish(context)

            clear_hyper_edge_selection(context, self.active)
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'} and event.value == 'PRESS':

            self.initbm.to_mesh(self.active.data)
            self.initbm.free()

            self.finish(context)

            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def finish(self, context):
        finish_modal_handlers(self)

        self.active.show_wire = False

        restore_gizmos(self)

        finish_status(self)

        force_ui_update(context)

    def invoke(self, context, event):
        self.active = context.active_object
        self.mx = self.active.matrix_world

        self.initbm = bmesh.new()
        self.initbm.from_mesh(self.active.data)

        self.HUD_coords = self.get_HUD_coords(context)

        if event.alt:
            slide = self.loop_cut(context, cuts=self.cuts, amount=self.amount)

            force_ui_update(context, active=self.active)
            return {'FINISHED'}

        self.cuts = 1
        self.amount = 0
        self.is_vertical = False
        self.ring = event.ctrl

        self.snap = False

        self.HUD_coords = self.get_HUD_coords(context)

        slide = self.loop_cut(context, cuts=self.cuts, amount=self.amount)

        if not slide:
            self.ring = True
            slide = self.loop_cut(context, cuts=self.cuts, amount=self.amount)

        if slide:

            get_mouse_pos(self, context, event, init_offset=True)

            center_coords = self.get_center_coords(context, self.mouse_pos - self.mouse_offset)

            warp_mouse(self, context, center_coords)

            self.active.show_wire = True

            hide_gizmos(self, context)

            init_status(self, context, func=draw_loop_cut_status(self))

            init_modal_handlers(self, context, hud=True, view3d=True)
            return {'RUNNING_MODAL'}

        self.initbm.to_mesh(self.active.data)
        self.initbm.free()

        return {'CANCELLED'}

    def get_HUD_coords(self, context):
        width = context.region.width
        height = context.region.height

        width_gap = int(width / 10)
        height_gap = int(height / 10)

        hud = {'width': width,
               'height': height,

               'mid_width': width / 2,
               'mid_height': height / 2,

               'width_gap': width_gap,
               'height_gap': height_gap,

               'bottom_left': Vector((width_gap, height_gap, 0)),
               'top_left': Vector((width_gap, height_gap * 9, 0)),
               'top_right': Vector((width_gap * 9, height_gap * 9, 0)),

               'guide_width': width_gap * 8,
               'guide_height': height_gap * 8}

        return hud

    def get_center_coords(self, context, mouse_pos):
        if self.is_vertical:
            center_coords = Vector((mouse_pos.x, context.region.height / 2))
        else:
            center_coords = Vector((context.region.width / 2, mouse_pos.y))

        return center_coords

    def get_slide_data(self, bm, edges, debug=False):
        data = {'sequences': [],
                'coords': []}

        sequences = get_edges_as_vert_sequences(edges, debug=False)

        for verts, cyclic in sequences:

            seq_data = {'ordered': [v for v in verts],
                        'cyclic': cyclic,
                        'verts': {},
                        'edges': []}

            for idx, v in enumerate(verts):
                nextv = verts[(idx + 1) % len(verts)]

                if not cyclic and idx == len(verts) - 1:
                    prevv = verts[(idx - 1) % len(verts)]
                    edge = bm.edges.get([v, prevv])

                    fwd_loop = [l for l in edge.link_loops if l.vert == prevv][0]

                    left_edge = fwd_loop.link_loop_next.edge
                    right_edge = fwd_loop.link_loop_radial_next.link_loop_prev.edge

                else:
                    edge = bm.edges.get([v, nextv])
                    seq_data['edges'].append(edge)

                    fwd_loop = [l for l in edge.link_loops if l.vert == v][0]

                    left_edge = fwd_loop.link_loop_prev.edge
                    right_edge = fwd_loop.link_loop_radial_next.link_loop_next.edge

                seq_data['verts'][v] = {'co': v.co.copy(),
                                        'left_dir': left_edge.other_vert(v).co - v.co,
                                        'right_dir': right_edge.other_vert(v).co - v.co}

            data['sequences'].append(seq_data)

        if debug:
            printd(data, "sequences")

        return data

    def slide_edges(self, context, bm, edges=[], amount=0, index_edge_cos=[], debug=False):
        if edges:
            self.data = self.get_slide_data(bm, edges, debug=debug)

            hud = self.HUD_coords
            right_view_cos = [Vector((hud['mid_width'], hud['mid_height'])), Vector((hud['mid_width'] + 100, hud['mid_height']))]
            up_view_cos = [Vector((hud['mid_width'], hud['mid_height'])), Vector((hud['mid_width'], hud['mid_height'] + 100))]

            if debug:
                draw_line([co.resized(3) for co in right_view_cos], color=yellow, modal=False, screen=True)
                draw_line([co.resized(3) for co in up_view_cos], color=blue, modal=False, screen=True)

            right_view_dir = Vector((right_view_cos[1] - right_view_cos[0]))
            up_view_dir = Vector((up_view_cos[1] - up_view_cos[0]))

            for sequence in self.data['sequences']:
                coords = []

                if debug:
                    draw_line(index_edge_cos, mx=self.mx, color=cyan, modal=False)

                edge_distances = []

                for e in sequence['edges']:
                    vert_distances = sorted([((intersect_point_line(v.co, *index_edge_cos)[0] - v.co).length, v, e) for v in e.verts], key=lambda x: x[0])
                    edge_distances.append(vert_distances)

                first_vert, first_edge = min(edge_distances, key=lambda x: (x[0][0], x[1][0]))[0][1:3]

                fvco = first_vert.co.copy()

                if debug:
                    draw_point(fvco, mx=self.mx, modal=False)

                edge_view_cos = [location_3d_to_region_2d(context.region, context.region_data, self.mx @ v.co) for v in first_edge.verts]

                if debug:
                    draw_line([co.resized(3) for co in edge_view_cos], modal=False, screen=True)

                edge_view_dir = Vector((edge_view_cos[1] - edge_view_cos[0]))

                right_dot = edge_view_dir.normalized().dot(right_view_dir.normalized())
                up_dot = edge_view_dir.normalized().dot(up_view_dir.normalized())

                self.is_vertical = abs(right_dot) >= abs(up_dot)

                if debug:
                    print("\nvertical mouse movement:", self.is_vertical)

                factor = get_zoom_factor(context, self.mx @ fvco, scale=100, ignore_obj_scale=False)

                if debug:
                    print()
                    print("first vert:", first_vert.index)
                    print("factor:", factor)

                right_edge_dir = sequence['verts'][first_vert]['right_dir'].normalized() * factor
                left_edge_dir = sequence['verts'][first_vert]['left_dir'].normalized() * factor

                if debug:
                    draw_vector(right_edge_dir, origin=fvco, mx=self.mx, modal=False)
                    draw_vector(left_edge_dir, origin=fvco, mx=self.mx, modal=False)

                right_edge_view_cos = [location_3d_to_region_2d(context.region, context.region_data, self.mx @ fvco), location_3d_to_region_2d(context.region, context.region_data, self.mx @ (fvco + right_edge_dir))]
                left_edge_view_cos = [location_3d_to_region_2d(context.region, context.region_data, self.mx @ fvco), location_3d_to_region_2d(context.region, context.region_data, self.mx @ (fvco + left_edge_dir))]

                if debug:
                    print()
                    print("right edge view cos:", right_edge_view_cos)
                    print("left edge view cos:", left_edge_view_cos)

                    draw_line([co.resized(3) for co in right_edge_view_cos], color=red, modal=False, screen=True)
                    draw_line([co.resized(3) for co in left_edge_view_cos], color=green, modal=False, screen=True)

                right_edge_view_dir = right_edge_view_cos[1] - right_edge_view_cos[0]
                left_edge_view_dir = left_edge_view_cos[1] - left_edge_view_cos[0]

                if self.is_vertical:
                    right_dot = up_view_dir.normalized().dot(right_edge_view_dir.normalized())
                    left_dot = up_view_dir.normalized().dot(left_edge_view_dir.normalized())

                    if debug:
                        print("\nup view alignment")
                        print(" right edge:", right_dot)
                        print(" left edge:", left_dot)

                else:
                    right_dot = right_view_dir.normalized().dot(right_edge_view_dir.normalized())
                    left_dot = right_view_dir.normalized().dot(left_edge_view_dir.normalized())

                    if debug:
                        print("\nright view alignment")
                        print(" right edge:", right_dot)
                        print(" left edge:", left_dot)

                if amount >= 0:
                    move_dir_name = 'right' if right_dot >= left_dot else 'left'
                else:
                    move_dir_name = 'left' if right_dot >= left_dot else 'right'

                if debug:
                    print()
                    print("amount:", amount)
                    print("move_dir:", move_dir_name)

                for v in sequence['ordered']:
                    vdata = sequence['verts'][v]
                    v.co = vdata['co'] + vdata[f'{move_dir_name}_dir'] * abs(amount)

                    coords.append(v.co.copy())

                if sequence['cyclic']:
                    coords.append(sequence['ordered'][0].co.copy())

                self.data['coords'].append(coords)

    def loop_cut(self, context, cuts=1, amount=0):
        bm = self.initbm.copy()
        bm.normal_update()
        bm.edges.ensure_lookup_table()

        vertex_group_layer = bm.verts.layers.deform.verify()
        edge_glayer = ensure_gizmo_layers(bm)[0]

        edge = bm.edges[self.index]

        index_edge_cos = [v.co.copy() for v in edge.verts]

        selected = [e for e in get_hyper_edge_selection(bm) if e != edge]

        if not selected and not self.ring:
            self.ring = True

        edges = get_selected_edges(bm, index=self.index, ring=self.ring, ring_ngons=self.ring_ngons)

        geo = bmesh.ops.subdivide_edges(bm, edges=edges, cuts=cuts, use_only_quads=not self.ring_ngons)

        cut_edges = [el for el in geo['geom_inner'] if isinstance(el, bmesh.types.BMEdge)]
        cut_verts = list({v for e in cut_edges for v in e.verts})

        for v in cut_verts:
            for vgindex, weight in v[vertex_group_layer].items():

                if weight != 1 or v.calc_shell_factor() == 1:
                    del v[vertex_group_layer][vgindex]

        for e in cut_edges:
            e[edge_glayer] = 1

        self.slide_edges(context, bm, edges=cut_edges, amount=amount, index_edge_cos=index_edge_cos)

        bm.to_mesh(self.active.data)
        bm.free()

        return True if cut_edges else False

def draw_slide_edge_status(op):
    def draw(self, context):
        layout = self.layout

        row = layout.row(align=True)

        row.label(text="Slide Edge")

        draw_status_item(row, key='LMB', text="Finish")
        draw_status_item(row, key='RMB', text="Cancel")

        row.separator(factor=10)

        draw_status_item(row, key='MOVE', text="Amount", prop=round(op.slide * 100))

        draw_status_item(row, active=op.opposite, key='ALT', text="Slide on Opposite Side", gap=2)

    return draw

class SlideEdge(bpy.types.Operator):
    bl_idname = "machin3.slide_edge"
    bl_label = "MACHIN3: Slide Edge"
    bl_options = {'REGISTER', 'UNDO'}

    index: IntProperty(name="Index of Edge that is to be slid")

    slide: FloatProperty(name="Side Amount", default=0)
    loop: BoolProperty(name="Loop Slide", default=False)
    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            active = context.active_object
            return active and active.select_get() and active.HC.ishyper

    @classmethod
    def description(cls, context, properties):
        if context.active_object.HC.objtype == 'CUBE':
            desc = "Slide Edge(s) (on Cubes)"
            desc += "\nSHIFT: Loop Slide"

        elif context.active_object.HC.objtype == 'CYLINDER':
            desc = "Slide Edge(s) (on Cylinders)"
            desc += "\nSHIFT: Skip Loop Slide"

        return desc

    def draw_HUD(self, context):
        if context.area == self.area:
            draw_init(self)

            halve_screen_distance = context.region.height / 10 if self.is_vertical else context.region.width / 10
            guide_dir = Vector((0, halve_screen_distance)) if self.is_vertical else Vector((halve_screen_distance, 0))

            draw_vector(guide_dir.resized(3), origin=self.mouse_pos.resized(3), fade=True, alpha=0.3)
            draw_vector(-guide_dir.resized(3), origin=self.mouse_pos.resized(3), fade=True, alpha=0.3)

            dims = draw_label(context, title="Slide Edge", coords=Vector((self.HUD_x, self.HUD_y)), center=False, color=white, alpha=1)

            if self.is_shift:
                draw_label(context, title=" a little", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, size=10, color=white, alpha=0.5)

            elif self.is_ctrl:
                draw_label(context, title=" a lot", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, size=10, color=white, alpha=0.5)

            self.offset += 18
            draw_label(context, title=f"Amount: {round(self.slide * 100)}%", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=1)

            if self.opposite:
                self.offset += 18
                draw_label(context, title="Opposite", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=yellow, alpha=1)

    def draw_VIEW3D(self, context):
        if context.area == self.area:
            for seq_coords in self.data['coords']['sequences']:
                draw_line(seq_coords, mx=self.mx, color=yellow, width=2, alpha=0.5)

            if self.data['coords']['rails']:
                draw_lines(self.data['coords']['rails'], mx=self.mx, color=green, width=2, alpha=0.5)

    def modal(self, context, event):
        if ignore_events(event):
            return {'RUNNING_MODAL'}

        context.area.tag_redraw()

        self.opposite = event.alt

        update_mod_keys(self, event)

        events = ['MOUSEMOVE', *alt]

        if event.type in events:

            if event.type in ['MOUSEMOVE', *alt]:
                get_mouse_pos(self, context, event)
                wrap_mouse(self, context, x=True, y=True)

                divisor = 100 if event.shift else 1 if event.ctrl else 10

                if self.is_vertical:
                    delta_y = self.mouse_pos.y - self.last_mouse.y
                    delta_slide = (delta_y * self.factor) / divisor

                else:
                    delta_x = self.mouse_pos.x - self.last_mouse.x
                    delta_slide = (delta_x * self.factor) / divisor

                self.slide += delta_slide

                self.slide_edges(context, amount=self.slide, opposite=self.opposite)

                force_ui_update(context)

        if event.type in {'LEFTMOUSE', 'SPACE'} and event.value == 'PRESS':
            self.finish(context)

            clear_hyper_edge_selection(context, self.active)
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'} and event.value == 'PRESS':

            self.initbm.to_mesh(self.active.data)
            self.initbm.free()

            self.finish(context)
            return {'CANCELLED'}

        self.last_mouse = self.mouse_pos

        return {'RUNNING_MODAL'}

    def finish(self, context):
        finish_modal_handlers(self)

        context.window.cursor_set('DEFAULT')

        context.scene.HC.draw_HUD = True

        self.active.HC.geometry_gizmos_show = True

        self.active.show_wire = False

        restore_gizmos(self)

        finish_status(self)

        force_geo_gizmo_update(context)

    def invoke(self, context, event):
        self.active = context.active_object
        self.mx = self.active.matrix_world

        self.initbm = bmesh.new()
        self.initbm.from_mesh(self.active.data)

        self.slide = 0
        self.is_vertical = False
        self.opposite = False

        update_mod_keys(self)

        if self.active.HC.objtype == 'CUBE':
            self.loop = event.shift

        elif self.active.HC.objtype == 'CYLINDER':
            self.loop = not event.shift

        self.HUD_coords = self.get_HUD_coords(context)

        if not self.slide_edges(context):
            popup_message("You can't slide multiple edge sequences at the same time!", title="Illegal Selection")
            return {'CANCELLED'}

        self.factor = get_zoom_factor(context, self.data['edge_center'], scale=10, ignore_obj_scale=False)

        hide_gizmos(self, context)

        self.active.show_wire = True

        get_mouse_pos(self, context, event)

        context.window.cursor_set('SCROLL_Y' if self.is_vertical else 'SCROLL_X')

        self.last_mouse = self.mouse_pos

        init_status(self, context, func=draw_slide_edge_status(self))

        init_modal_handlers(self, context, hud=True, view3d=True)
        return {'RUNNING_MODAL'}

    def get_data(self, bm, edges, debug=False):
        data = {'sequences': [],
                'coords': {'sequences': [],
                           'rails': []},
                'edge_center': self.mx @ get_center_between_verts(*[v for v in bm.edges[self.index].verts])}

        sequences = get_edges_as_vert_sequences(edges, debug=False)

        if len(sequences) > 1:
            return

        for verts, cyclic in sequences:

            seq_data = {'ordered': [v for v in verts],
                        'cyclic': cyclic,
                        'verts': {}}

            for idx, v in enumerate(verts):
                nextv = verts[(idx + 1) % len(verts)]

                if not cyclic and idx == len(verts) - 1:
                    prevv = verts[(idx - 1) % len(verts)]
                    edge = bm.edges.get([v, prevv])

                    fwd_loops = [l for l in edge.link_loops if l.vert == prevv]

                    if fwd_loops:
                        fwd_loop = fwd_loops[0]
                    else:
                        fwd_loop = edge.link_loops[0]

                    left_edge = fwd_loop.link_loop_next.edge
                    right_edge = fwd_loop.link_loop_radial_next.link_loop_prev.edge

                else:
                    edge = bm.edges.get([v, nextv])

                    fwd_loops = [l for l in edge.link_loops if l.vert == v]

                    if fwd_loops:
                        fwd_loop = fwd_loops[0]
                    else:
                        fwd_loop = edge.link_loops[0]

                    left_edge = fwd_loop.link_loop_prev.edge
                    right_edge = fwd_loop.link_loop_radial_next.link_loop_next.edge

                left_vert = left_edge.other_vert(v)
                right_vert = right_edge.other_vert(v)

                if not left_vert:
                    left_vert = right_vert

                elif not right_vert:
                    right_vert = left_vert

                seq_data['verts'][v] = {'co': v.co.copy(),
                                        'left_dir': left_vert.co - v.co,
                                        'right_dir': right_vert.co - v.co,

                                        'left_vert': left_vert,
                                        'right_vert': right_vert}

            data['sequences'].append(seq_data)

        if debug:
            printd(data, "sequences")

        return data

    def get_HUD_coords(self, context):
        width = context.region.width
        height = context.region.height

        width_gap = int(width / 10)
        height_gap = int(height / 10)

        hud = {'width': width,
               'height': height,

               'mid_width': width / 2,
               'mid_height': height / 2,

               'width_gap': width_gap,
               'height_gap': height_gap,

               'bottom_left': Vector((width_gap, height_gap, 0)),
               'top_left': Vector((width_gap, height_gap * 9, 0)),
               'top_right': Vector((width_gap * 9, height_gap * 9, 0)),

               'guide_width': width_gap * 8,
               'guide_height': height_gap * 8}

        return hud

    def slide_edges(self, context, amount=0, opposite=False, debug=False):
        bm = self.initbm.copy()
        bm.normal_update()
        bm.edges.ensure_lookup_table()

        edges = get_selected_edges(bm, index=self.index, loop=self.loop)

        self.data = self.get_data(bm, edges, debug=debug)

        if not self.data:
            return False

        hud = self.HUD_coords
        right_view_cos = [Vector((hud['mid_width'], hud['mid_height'])), Vector((hud['mid_width'] + 100, hud['mid_height']))]
        up_view_cos = [Vector((hud['mid_width'], hud['mid_height'])), Vector((hud['mid_width'], hud['mid_height'] + 100))]

        if debug:
            draw_line([co.resized(3) for co in right_view_cos], color=yellow, modal=False, screen=True)
            draw_line([co.resized(3) for co in up_view_cos], color=blue, modal=False, screen=True)

        right_view_dir = Vector((right_view_cos[1] - right_view_cos[0]))
        up_view_dir = Vector((up_view_cos[1] - up_view_cos[0]))

        for sequence in self.data['sequences']:
            coords = []

            first_edge = bm.edges[self.index]

            edge_view_cos = [location_3d_to_region_2d(context.region, context.region_data, self.mx @ v.co) for v in first_edge.verts]
            if debug:
                draw_line([co.resized(3) for co in edge_view_cos], modal=False, screen=True)

            edge_view_dir = Vector((edge_view_cos[1] - edge_view_cos[0]))

            right_dot = edge_view_dir.normalized().dot(right_view_dir.normalized())
            up_dot = edge_view_dir.normalized().dot(up_view_dir.normalized())

            self.is_vertical = abs(right_dot) - 0.4 >= abs(up_dot)

            if debug:
                print("\nvertical mouse movement:", self.is_vertical)

            first_vert = first_edge.verts[0]
            fvco = first_vert.co.copy()

            if debug:
                draw_point(fvco, mx=self.mx, modal=False)

            factor = get_zoom_factor(context, self.mx @ fvco, scale=100, ignore_obj_scale=False)

            if debug:
                print()
                print("first vert:", first_vert.index)
                print("factor:", factor)

            right_edge_dir = sequence['verts'][first_vert]['right_dir'].normalized() * factor
            left_edge_dir = sequence['verts'][first_vert]['left_dir'].normalized() * factor

            if debug:
                draw_vector(right_edge_dir, origin=fvco, mx=self.mx, modal=False)
                draw_vector(left_edge_dir, origin=fvco, mx=self.mx, modal=False)

            right_edge_view_cos = [location_3d_to_region_2d(context.region, context.region_data, self.mx @ fvco), location_3d_to_region_2d(context.region, context.region_data, self.mx @ (fvco + right_edge_dir))]
            left_edge_view_cos = [location_3d_to_region_2d(context.region, context.region_data, self.mx @ fvco), location_3d_to_region_2d(context.region, context.region_data, self.mx @ (fvco + left_edge_dir))]

            if debug:
                print()
                print("right edge view cos:", right_edge_view_cos)
                print("left edge view cos:", left_edge_view_cos)

                draw_line([co.resized(3) for co in right_edge_view_cos], color=red, modal=False, screen=True)
                draw_line([co.resized(3) for co in left_edge_view_cos], color=green, modal=False, screen=True)

            right_edge_view_dir = right_edge_view_cos[1] - right_edge_view_cos[0]
            left_edge_view_dir = left_edge_view_cos[1] - left_edge_view_cos[0]

            if self.is_vertical:
                right_dot = up_view_dir.normalized().dot(right_edge_view_dir.normalized())
                left_dot = up_view_dir.normalized().dot(left_edge_view_dir.normalized())

                if debug:
                    print("\nup view alignment")
                    print(" right edge:", right_dot)
                    print(" left edge:", left_dot)

            else:
                right_dot = right_view_dir.normalized().dot(right_edge_view_dir.normalized())
                left_dot = right_view_dir.normalized().dot(left_edge_view_dir.normalized())

                if debug:
                    print("\nright view alignment")
                    print(" right edge:", right_dot)
                    print(" left edge:", left_dot)

            if amount >= 0:
                move_dir_name = 'right' if right_dot >= left_dot else 'left'
            else:
                move_dir_name = 'left' if right_dot >= left_dot else 'right'

            if debug:
                print()
                print("amount:", amount)
                print("move_dir:", move_dir_name)

            if opposite:
                move_dir_name = 'right' if move_dir_name == 'left' else 'left'

            if debug:
                print("opposite:", opposite)

            for v in sequence['ordered']:
                vdata = sequence['verts'][v]
                move_dir = vdata[f'{move_dir_name}_dir'].normalized()

                v.co = vdata['co'] + (- move_dir if opposite else move_dir) * abs(amount)

                coords.append(v.co.copy())

                rail_co = vdata[f'{move_dir_name}_vert'].co.copy()

                self.data['coords']['rails'].extend([v.co.copy(), rail_co])

            if sequence['cyclic']:
                coords.append(sequence['ordered'][0].co.copy())

            self.data['coords']['sequences'].append(coords)

        edge_center = self.mx @ get_center_between_verts(*[v for v in first_edge.verts])
        self.factor = get_zoom_factor(context, edge_center, scale=10, ignore_obj_scale=False)

        bm.to_mesh(self.active.data)
        bm.free()

        return True

def draw_crease_edge_status(op):
    def draw(self, context):
        layout = self.layout

        row = layout.row(align=True)

        row.label(text="Crease Edge")

        draw_status_item(row, key='LMB', text="Finish")
        draw_status_item(row, key='RMB', text="Cancel")

        row.separator(factor=10)

        draw_status_item(row, active=op.absolute, key='ALT', text="Absolute", gap=2)

    return draw

class CreaseEdge(bpy.types.Operator):
    bl_idname = "machin3.crease_edge"
    bl_label = "MACHIN3: Crease Edge"
    bl_description = "Crease Edge"
    bl_options = {'REGISTER', 'UNDO'}

    index: IntProperty(name="Index of Edge that is to be slid")

    amount: FloatProperty(name="Crease Amount", min=-1, max=1)
    absolute: BoolProperty(name="Absolute Crease", default=False)
    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT' and context.active_object:
            return subd_poll(context)

    def draw_HUD(self, context):
        if context.area == self.area:
            draw_init(self)

            guide_dir = Vector((context.region.width / 10, 0))
            draw_vector(guide_dir.resized(3), origin=self.mouse_pos.resized(3), fade=True, alpha=0.3)
            draw_vector(-guide_dir.resized(3), origin=self.mouse_pos.resized(3), fade=True, alpha=0.3)

            for crease, coords, center2d, is_sel in self.creased_edges:

                draw_label(context, title=dynamic_format(crease, decimal_offset=1), coords=center2d, center=True, size=12 if is_sel else 10, color=green if is_sel else white, alpha=1 if is_sel else 0.4)

            dims = draw_label(context, title="Adjust Crease", coords=Vector((self.HUD_x, self.HUD_y)), center=False, color=white, alpha=1)

            if self.is_shift:
                draw_label(context, title=" a little", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, size=10, color=white, alpha=0.5)

            elif self.is_ctrl:
                draw_label(context, title=" a lot", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, size=10, color=white, alpha=0.5)

            self.offset += 18
            decimal_offset = 2 if self.is_shift else 0 if self.is_ctrl else 1
            title = dynamic_format(self.amount, decimal_offset=decimal_offset)

            if self.absolute:
                if self.amount <= 0:
                    title = '0'
            elif self.amount > 0:
                title = '+' + title

            draw_label(context, title=title, coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=yellow, alpha=1)

            if self.absolute:
                self.offset += 18
                draw_label(context, title="Absolute", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=green, alpha=1)

    def draw_VIEW3D(self, context):
        if context.area == self.area:
            for crease, coords, center2d, is_sel in self.creased_edges:
                draw_line(coords, mx=self.mx, color=green if is_sel else white, alpha=0.2 if is_sel else 0.1, width=3 if is_sel else 1)

    def modal(self, context, event):
        if ignore_events(event):
            return {'RUNNING_MODAL'}

        context.area.tag_redraw()

        update_mod_keys(self, event)

        self.absolute = self.event.alt

        events = ['MOUSEMOVE', *alt]

        if event.type in events:
            if event.type in ['MOUSEMOVE', *alt]:
                get_mouse_pos(self, context, event)
                wrap_mouse(self, context, x=True)

                delta_x = self.mouse_pos.x - self.last_mouse.x

                divisor = get_mousemove_divisor(event, normal=5, shift=20, ctrl=2.5, sensitivity=100)

                delta_crease = delta_x / divisor

                self.amount += delta_crease

                self.crease(context, amount=self.amount, absolute=False)

        if event.type in ['LEFTMOUSE', 'SPACE'] and event.value == 'PRESS':
            self.finish(context)

            clear_hyper_edge_selection(context, self.active)

            return {'FINISHED'}

        elif event.type in ['RIGHTMOUSE', 'ESC']:

            self.initbm.to_mesh(self.active.data)
            self.initbm.free()

            self.finish(context)
            return {'CANCELLED'}

        self.last_mouse = self.mouse_pos

        return {'RUNNING_MODAL'}

    def finish(self, context):
        finish_modal_handlers(self)

        finish_status(self)

        context.window.cursor_set('DEFAULT')

        restore_gizmos(self)

        force_ui_update(context)

    def invoke(self, context, event):
        self.active = context.active_object
        self.mx = self.active.matrix_world

        self.initbm = bmesh.new()
        self.initbm.from_mesh(self.active.data)

        subd = subd_poll(context)[0]

        if not subd.use_creases:
            subd.use_creases = True

        if subd.levels > subd.render_levels:
            subd.render_levels = subd.levels

        if subd.show_expanded:
            subd.show_expanded = False

        self.amount = 0

        update_mod_keys(self)

        self.crease(context, amount=0)

        get_mouse_pos(self, context, event)

        self.last_mouse = self.mouse_pos

        context.window.cursor_set('SCROLL_X')

        hide_gizmos(self, context)

        init_status(self, context, func=draw_crease_edge_status(self))
        self.active.select_set(True)

        init_modal_handlers(self, context, hud=True, view3d=True)
        return {'RUNNING_MODAL'}

    def crease(self, context, amount, absolute=False):
        bm = self.initbm.copy()
        bm.normal_update()
        bm.edges.ensure_lookup_table()

        crease_layer = ensure_default_data_layers(bm, vertex_groups=False, bevel_weights=False, crease=True)[0]
        sel = get_selected_edges(bm, index=self.index)

        self.creased_edges = []

        for e in bm.edges:

            init_crease = e[crease_layer]

            if e in sel:
                if self.absolute:
                    e[crease_layer] = max(self.amount, 0)
                else:
                    e[crease_layer] = max(init_crease + self.amount, 0)

            if e[crease_layer]:
                coords = [v.co.copy() for v in e.verts]
                center2d = location_3d_to_region_2d(context.region, context.region_data, get_center_between_points(*[self.mx @ co for co in coords]))
                is_sel = e in sel

                if center2d:
                    self.creased_edges.append((e[crease_layer], coords, center2d, is_sel))

        bm.to_mesh(self.active.data)

def draw_push_edge_status(op):
    def draw(self, context):
        layout = self.layout

        row = layout.row(align=True)

        row.label(text="Push Edge")

        if op.is_numeric_input:
            draw_status_item(row, key='RETURN', text="Finish")
            draw_status_item(row, key='MMB', text="Viewport")
            draw_status_item(row, key='ESC', text="Cancel")

            draw_status_item(row, key='TAB', text="Abort Numeric Input")

            draw_status_item_numeric(op, row, invert=True, gap=10)

        else:
            draw_status_item(row, key='LMB', text="Finish")
            draw_status_item(row, key='MMB', text="Viewport")
            draw_status_item(row, key='RMB', text="Cancel")

            draw_status_item(row, key='TAB', text="Enter Numeric Input")

            draw_status_item_precision(row, fine=op.is_shift, coarse=op.is_ctrl, gap=10)

            precision = 2 if op.is_shift else 0 if op.is_ctrl else 1
            draw_status_item(row, key='MOVE', text="Amount", prop=dynamic_format(op.amount, decimal_offset=precision), gap=1)

    return draw

class PushEdge(bpy.types.Operator):
    bl_idname = "machin3.push_edge"
    bl_label = "MACHIN3: Push Edge"
    bl_description = "description"
    bl_options = {'REGISTER', 'UNDO'}

    index: IntProperty(name="Index of Edge that is to be slid")
    amount: FloatProperty(name="Push Amount", default=0)
    loop: BoolProperty(name="Loop Push", default=False)

    is_numeric_input: BoolProperty()
    is_numeric_input_marked: BoolProperty()
    numeric_input_amount: StringProperty(name="Numeric Amount", description="Amount of Edge-Pushing entered numerically", default='0')

    passthrough = None

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            active = context.active_object
            return active and active.select_get() and active.HC.ishyper

    @classmethod
    def description(cls, context, properties):
        if context.active_object.HC.objtype == 'CUBE':
            desc = "Push Edge(s) (on Cubes)"
            desc += "\nSHIFT: Loop Slide"

        elif context.active_object.HC.objtype == 'CYLINDER':
            desc = "Push Edge(s) (on Cylinders)"
            desc += "\nSHIFT: Skip Loop Slide"

        desc += "\nALT: Repeat Push using previous Amount"
        return desc

    def draw(self, context):
        layout = self.layout
        column = layout.column()

        row = column.split(align=True)
        row.prop(self, 'amount', text='Amount')

    def draw_HUD(self, context):
        if context.area == self.area:
            draw_init(self)

            dims = draw_label(context, title="Push Edge", coords=Vector((self.HUD_x, self.HUD_y)), center=False, color=white, alpha=1)

            if self.is_shift:
                draw_label(context, title=" a little", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, size=10, color=white, alpha=0.5)

            elif self.is_ctrl:
                draw_label(context, title=" a lot", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, size=10, color=white, alpha=0.5)

            self.offset += 18
            dims = draw_label(context, title="Amount:", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=0.5)

            title = "🖩" if self.is_numeric_input else " "
            dims += draw_label(context, title=title, coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset + 3, center=False, size=20, color=green, alpha=0.5)

            if self.is_numeric_input:
                numeric_dims = draw_label(context, title=self.numeric_input_amount, coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=green, alpha=1)

                if self.is_numeric_input_marked:
                    ui_scale = get_scale(context)
                    coords = [Vector((self.HUD_x + dims.x, self.HUD_y - (self.offset - 5) * ui_scale, 0)), Vector((self.HUD_x + dims.x + numeric_dims.x, self.HUD_y - (self.offset - 5) * ui_scale, 0))]
                    draw_line(coords, width=12 + 8 * ui_scale, color=green, alpha=0.1, screen=True)

            else:
                precision = 2 if self.is_shift else 0 if self.is_ctrl else 1
                draw_label(context, title=dynamic_format(self.amount, decimal_offset=precision), coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=1)

    def draw_VIEW3D(self, context):
        if context.area == self.area:
            push_dir = self.loc - self.init_loc

            draw_vector(self.edge_normal * self.min_dim * 0.4, origin=self.edge_origin, fade=True, alpha=0.2)
            draw_vector(-self.edge_normal * self.min_dim * 0.4, origin=self.edge_origin, fade=True, alpha=0.2)

            draw_point(self.edge_origin, color=(1, 1, 0))
            draw_point(self.edge_origin + push_dir, color=(1, 1, 1))

            draw_line([self.edge_origin, self.edge_origin + push_dir], width=2, alpha=0.3)

            for coords in self.data['coords']:
                draw_line(coords, width=2, color=yellow, alpha=0.5)

    def modal(self, context, event):
        if ignore_events(event):
            return {'RUNNING_MODAL'}

        context.area.tag_redraw()

        update_mod_keys(self, event)

        if ret := self.numeric_input(context, event):
            return ret

        else:
            return self.interactive_input(context, event)

    def finish(self, context):
        finish_modal_handlers(self)

        restore_gizmos(self)

        finish_status(self)

        force_geo_gizmo_update(context)

    def invoke(self, context, event):
        self.debug = True
        self.debug = False

        self.active = context.active_object
        self.mx = self.active.matrix_world

        self.min_dim = get_min_dim(self.active)

        if self.active.HC.objtype == 'CUBE':
            self.loop = event.shift
        elif self.active.HC.objtype == 'CYLINDER':
            self.loop = not event.shift

        self.initbm = bmesh.new()
        self.initbm.from_mesh(self.active.data)

        self.bm = self.initbm.copy()
        self.bm.normal_update()
        self.bm.edges.ensure_lookup_table()

        self.edge = self.bm.edges[self.index]
        self.edge_normal = get_world_space_normal(get_edge_normal(self.edge), self.mx)
        self.edge_origin = self.mx @ get_center_between_verts(*self.edge.verts)

        edges = get_selected_edges(self.bm, index=self.index, loop=self.loop)

        if event.alt and self.amount != 0:

            self.data = self.get_data(self.bm, edges, debug=self.debug)

            self.push(interactive=False)
            return {'FINISHED'}

        get_mouse_pos(self, context, event, init_offset=True)

        self.init_loc = self.get_edge_normal_intersection(context, self.mouse_pos - self.mouse_offset)

        if self.init_loc:
            self.loc = self.init_loc

            self.data = self.get_data(self.bm, edges, debug=self.debug)

            self.amount = 0

            update_mod_keys(self)

            self.is_numeric_input = False
            self.is_numeric_input_marked = False
            self.numeric_input_amount = '0'

            hide_gizmos(self, context)

            init_status(self, context, func=draw_push_edge_status(self))

            force_ui_update(context, active=self.active)

            init_modal_handlers(self, context, hud=True, view3d=True)
            return {'RUNNING_MODAL'}

        return {'CANCELLED'}

    def execute(self, context):
        self.active = context.active_object

        self.bm = bmesh.new()
        self.bm.from_mesh(self.active.data)
        self.bm.normal_update()
        self.bm.edges.ensure_lookup_table()

        edges = get_selected_edges(self.bm, index=self.index, loop=self.loop)

        self.data = self.get_data(self.bm, edges, debug=self.debug)

        self.push(interactive=False)
        return {'FINISHED'}

    def get_edge_normal_intersection(self, context, mouse_pos):
        view_origin, view_dir = get_view_origin_and_dir(context, mouse_pos)

        i = intersect_line_line(self.edge_origin, self.edge_origin + self.edge_normal, view_origin, view_origin + view_dir)

        if i:
            return i[0]

    def get_data(self, bm, edges, debug=False):
        index_edge = bm.edges[self.index]

        if debug:
            print("\nindex edge:", index_edge.index)
            print("\nselected edges:", [e.index for e in edges])

        data = {'sequences': [],
                'coords': []}

        sequences = get_edges_as_vert_sequences(edges, debug=False)

        for idx, (verts, cyclic) in enumerate(sequences):

            if debug:
                print("sequence:", idx, cyclic)

            seq_data = {'verts': {},
                        'sorted': [],
                        'cyclic': cyclic}

            for vidx, v in enumerate(verts):
                if debug:
                    print("", v.index)

                seq_data['sorted'].append(v)

                if cyclic:
                    prevv = verts[(vidx - 1) % len(verts)]
                    nextv = verts[(vidx + 1) % len(verts)]

                else:
                    prevv = verts[vidx - 1] if vidx > 0 else None
                    nextv = verts[vidx + 1] if vidx < len(verts) - 1 else None

                if debug:
                    print(" prev vert:", prevv.index if prevv else None)
                    print(" next vert:", nextv.index if nextv else None)

                if prevv and nextv:
                    prev_edge = bm.edges.get([v, prevv])
                    next_edge = bm.edges.get([v, nextv])
                    push_dir = average_normals([get_edge_normal(prev_edge), get_edge_normal(next_edge)])

                    angle = get_angle_between_edges(prev_edge, next_edge, radians=False)

                    beta = angle / 2

                    shell_factor = 1 / sin(radians(beta))

                    if debug:
                        print(" prev edge:", prev_edge.index if prev_edge else None)
                        print(" next edge:", next_edge.index if next_edge else None)

                elif prevv:
                    prev_edge = bm.edges.get([v, prevv])
                    edge_normal = get_edge_normal(prev_edge)
                    end_faces = [f for f in v.link_faces if f not in prev_edge.link_faces]

                    if debug:
                        print(" prev edge:", prev_edge.index)
                        print(" next edge:", None)
                        print(" end faces:", [f.index for f in end_faces])

                    push_dir, shell_factor = self.get_push_dir_from_end_faces(v, edge_normal, end_faces)

                else:
                    next_edge = bm.edges.get([v, nextv])
                    edge_normal = get_edge_normal(next_edge)
                    end_faces = [f for f in v.link_faces if f not in next_edge.link_faces]

                    push_dir, shell_factor = self.get_push_dir_from_end_faces(v, edge_normal, end_faces)

                    if debug:
                        print(" prev edge:", None)
                        print(" next edge:", next_edge.index)
                        print(" end faces:", [f.index for f in end_faces])

                if debug:
                    print(" push dir:", push_dir)
                    print(" shell_factor:", shell_factor)

                    if shell_factor != 1:

                        if shell_factor > 1:
                            draw_vector(push_dir * shell_factor, origin=v.co.copy(), mx=self.mx, color=yellow, normal=False, alpha=1, modal=False)
                            draw_vector(push_dir, origin=v.co.copy(),mx=self.mx, normal=False, alpha=1, modal=False)

                        else:
                            draw_vector(push_dir, origin=v.co.copy(),mx=self.mx, normal=False, alpha=1, modal=False)
                            draw_vector(push_dir * shell_factor, origin=v.co.copy(), mx=self.mx, color=yellow, normal=False, alpha=1, modal=False)

                    else:
                        draw_vector(push_dir, origin=v.co.copy(), mx=self.mx, normal=True, alpha=1, modal=False)

                seq_data['verts'][v] = {'init_co': v.co.copy(),
                                        'push_dir': push_dir,
                                        'shell_factor': shell_factor}

            data['sequences'].append(seq_data)

            coords = []

            for v in verts:
                coords.append(self.mx @ v.co.copy())

            if cyclic:
                coords.append(self.mx @ verts[0].co.copy())

            data['coords'].append(coords)

        if debug:
            printd(data, "sequences")

        return data

    def get_push_dir_from_end_faces(self, v, edge_normal, end_faces, debug=False):
        if end_faces:
            end_faces_normal = average_normals([f.normal for f in end_faces])

            if debug:
                draw_vector(end_faces_normal, origin=v.co, mx=self.mx, modal=False)

            i = intersect_line_plane(v.co + edge_normal, v.co + edge_normal + end_faces_normal, v.co, end_faces_normal)

            if i:
                push_dir = (i - v.co).normalized()

                if debug:
                    draw_point(i, mx=self.mx, modal=False)
                    draw_vector(end_faces_normal, origin=v.co, mx=self.mx, modal=False)

                alpha = degrees(edge_normal.angle(push_dir))

                beta = 180 - 90 - alpha

                if debug:
                    print(" alpha:", alpha)
                    print(" beta:", beta)

                shell_factor = 1 / sin(radians(beta))

            else:
                print("WARNING: no end face intersection, using edge normal as push dir")
                push_dir = edge_normal
                shell_factor = 1

        else:
            print("WARNING: no end faces, using edge normal as push dir")
            push_dir = edge_normal
            shell_factor = 1

        return push_dir, shell_factor

    def numeric_input(self, context, event):

        if event.type == "TAB" and event.value == 'PRESS':
            self.is_numeric_input = not self.is_numeric_input

            force_ui_update(context)

            if self.is_numeric_input:
                self.numeric_input_amount = str(self.amount)
                self.is_numeric_input_marked = True

            else:
                return

        if self.is_numeric_input:

            if event.type in alt:
                update_mod_keys(self, event)
                force_ui_update(context)
                return {'RUNNING_MODAL'}

            events = numeric_input_event_items()

            if event.type in events and event.value == 'PRESS':

                if self.is_numeric_input_marked:
                    self.is_numeric_input_marked = False

                    if event.type == 'BACK_SPACE':

                        if event.alt:
                            self.numeric_input_amount = self.numeric_input_amount[:-1]

                        else:
                            self.numeric_input_amount = shorten_float_string(self.numeric_input_amount, 4)

                    elif event.type in ['MINUS', 'NUMPAD_MINUS']:
                        if self.numeric_input_amount.startswith('-'):
                            self.numeric_input_amount = self.numeric_input_amount[1:]

                        else:
                            self.numeric_input_amount = '-' + self.numeric_input_amount

                    else:
                        self.numeric_input_amount = input_mappings[event.type]

                    force_ui_update(context)

                else:
                    if event.type in numbers:
                        self.numeric_input_amount += input_mappings[event.type]

                    elif event.type == 'BACK_SPACE':
                        self.numeric_input_amount = self.numeric_input_amount[:-1]

                    elif event.type in ['COMMA', 'PERIOD', 'NUMPAD_COMMA', 'NUMPAD_PERIOD'] and '.' not in self.numeric_input_amount:
                        self.numeric_input_amount += '.'

                    elif event.type in ['MINUS', 'NUMPAD_MINUS']:
                        if self.numeric_input_amount.startswith('-'):
                            self.numeric_input_amount = self.numeric_input_amount[1:]

                        else:
                            self.numeric_input_amount = '-' + self.numeric_input_amount

                try:
                    self.amount = float(self.numeric_input_amount)

                except:
                    return {'RUNNING_MODAL'}

                self.push(interactive=False)

            elif navigation_passthrough(event, alt=True, wheel=True):
                return {'PASS_THROUGH'}

            elif event.type in {'RET', 'NUMPAD_ENTER'}:
                self.finish(context)

                return {'FINISHED'}

            elif event.type in {'ESC', 'RIGHTMOUSE'}:
                self.finish(context)

                self.initbm.to_mesh(self.active.data)
                return {'CANCELLED'}

            return {'RUNNING_MODAL'}

    def interactive_input(self, context, event):
        events = ['MOUSEMOVE']

        if event.type in events:
            if event.type == 'MOUSEMOVE':
                get_mouse_pos(self, context, event)

                if self.passthrough:
                    self.passthrough = False

                    push_dir = self.loc - self.init_loc

                    self.loc = self.get_edge_normal_intersection(context, self.mouse_pos - self.mouse_offset)
                    self.init_loc = self.loc - push_dir

                self.loc = self.get_edge_normal_intersection(context, self.mouse_pos - self.mouse_offset)

                if self.loc:

                    self.push(interactive=True)

                    force_ui_update(context, active=self.active)

        elif navigation_passthrough(event):
            self.passthrough = True

            return {'PASS_THROUGH'}

        elif event.type in ['LEFTMOUSE', 'SPACE'] and event.value == 'PRESS':

            clear_hyper_edge_selection(context, self.active)

            self.finish(context)
            return {'FINISHED'}

        elif event.type in ['RIGHTMOUSE', 'ESC'] and event.value == 'PRESS':
            self.finish(context)

            self.initbm.to_mesh(self.active.data)
            self.initbm.free()

            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def push(self, interactive=True):
        if interactive:
            precision = 0.2 if self.is_shift else 5 if self.is_ctrl else 1

            push_dir = (self.loc - self.init_loc) * precision
            push_dir_local = self.mx.inverted_safe().to_3x3() @ push_dir

            dot = round(push_dir.normalized().dot(self.edge_normal))

            self.amount = push_dir_local.length * dot

        for seqdata in self.data['sequences']:
            cyclic = seqdata['cyclic']

            for v, vdata in seqdata['verts'].items():
                v.co = vdata['init_co'] + vdata['push_dir'] * vdata['shell_factor'] * self.amount

            if interactive:
                self.data['coords'] = []
                coords = []

                for v in seqdata['sorted']:
                    coords.append(self.mx @ v.co.copy())

                if cyclic:
                    coords.append(self.mx @ seqdata['sorted'][0].co.copy())

                self.data['coords'].append(coords)

        self.bm.to_mesh(self.active.data)

class StraightenEdges(bpy.types.Operator):
    bl_idname = "machin3.straighten_edges"
    bl_label = "MACHIN3: Straighten Edges"
    bl_description = "Straighten Multi-Edge Selections"
    bl_options = {'REGISTER', 'UNDO'}

    index: IntProperty(name="Index of Edge that is to be straightend")
    loop: BoolProperty(name="Loop Straighten", default=False)
    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            active = context.active_object
            return active and active.select_get() and active.HC.ishyper

    def draw(self, context):
        layout = self.layout
        _column = layout.column()

    def execute(self, context):
        self.active = context.active_object
        self.mx = self.active.matrix_world

        bm = bmesh.new()
        bm.from_mesh(self.active.data)
        bm.normal_update()
        bm.edges.ensure_lookup_table()

        edges = get_selected_edges(bm, index=self.index, loop=self.loop)

        data = self.get_data(bm, edges, debug=False)

        if data['can_straighten']:
            for sequence in data['sequences']:
                for v, co in sequence.items():
                    v.co = co

            bm.to_mesh(self.active.data)

            clear_hyper_edge_selection(context, self.active)

            return {'FINISHED'}

        else:

            if 'SINGLE' in data['fail_reasons'] and 'CYCLIC' in data['fail_reasons']:
                msg = ['A single Edge is straight already, dummy.', "And a cyclic loop can't be straightened either."]

            elif 'SINGLE' in data['fail_reasons']:
                msg = ['A single Edge is straight already, dummy.']

            else:
                msg = ["A cyclic loop can't be straightened, dummy."]

            msg.append('Select multiple connected edges instead.')

            popup_message(msg, title="Illegal Selection")
            return {'CANCELLED'}

    def get_data(self, bm, edges, debug=False):
        index_edge = bm.edges[self.index]

        if debug:
            print("\nindex edge:", index_edge.index)
            print("\nselected edges:", [e.index for e in edges])

        data = {'sequences': [],
                'can_straighten': False,
                'fail_reasons': set()}

        sequences = get_edges_as_vert_sequences(edges, debug=False)

        for idx, (verts, cyclic) in enumerate(sequences):
            if debug:
                print("sequence:", idx, cyclic, len(verts), " verts long")

            sequence = {}

            if not cyclic and len(verts) > 2:
                if debug:
                    print(" can be straightened")

                if not data['can_straighten']:
                    data['can_straighten'] = True

                v_start = verts[0]
                v_end = verts[-1]

                if debug:
                    draw_line([v_start.co.copy(), v_end.co.copy()], mx=self.mx, modal=False)

                for v in verts:

                    if v in [v_start, v_end]:
                        continue

                    else:
                        i = intersect_point_line(v.co, v_start.co, v_end.co)
                        sequence[v] = i[0]

                        if debug:
                            draw_point(i[0], mx=self.mx, color=yellow, modal=False)

                    data['sequences'].append(sequence)

            else:
                if debug:
                    print(" ignoring")

                if cyclic:
                    data['fail_reasons'].add('CYCLIC')
                else:
                    data['fail_reasons'].add('SINGLE')

        if debug:
            printd(data)
            bpy.context.area.tag_redraw()

        return data
