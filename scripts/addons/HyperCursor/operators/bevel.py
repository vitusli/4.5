import bpy
from bpy.props import FloatProperty, BoolProperty, IntProperty, EnumProperty, StringProperty
from bpy_extras.view3d_utils import location_3d_to_region_2d

import bmesh
from mathutils import Vector, Matrix
from mathutils.geometry import intersect_line_plane, intersect_line_line, intersect_point_line, interpolate_bezier

from math import sin, radians
from time import time

from .. utils.bmesh import ensure_gizmo_layers, is_edge_convex
from .. utils.draw import draw_batch, draw_vector, draw_point, draw_points, draw_line, draw_lines, draw_label, draw_vectors, draw_init, get_text_dimensions, draw_fading_label
from .. utils.gizmo import hide_gizmos, restore_gizmos
from .. utils.math import average_normals, average_locations, create_rotation_matrix_from_vector, create_rotation_matrix_from_vectors, get_edge_normal, get_loc_matrix, get_center_between_verts, get_center_between_points, dynamic_format
from .. utils.mesh import shade
from .. utils.modifier import add_boolean, flip_bevel_profile, flop_bevel_profile, get_mod_base_name, get_new_mod_name, get_next_mod, get_prefix_from_mod, get_previous_mod, move_mod, remove_mod, set_bevel_profile_from_dict, sort_mod_after_split, sort_modifiers, add_bevel, add_weld, get_bevel_profile_as_dict
from .. utils.object import get_batch_from_mesh, hide_render, parent, remove_obj, set_obj_origin
from .. utils.operator import Settings
from .. utils.property import get_biggest_index_among_names, step_list
from .. utils.raycast import cast_bvh_ray_from_mouse, get_closest
from .. utils.select import get_edges_as_vert_sequences, get_selected_vert_sequences, get_loop_edges, get_edges_vert_sequences
from .. utils.snap import Snap
from .. utils.system import printd
from .. utils.tools import active_tool_is_hypercursor
from .. utils.ui import finish_modal_handlers, get_mouse_pos, gizmo_selection_passthrough, ignore_events, init_modal_handlers, init_status, finish_status, is_key, is_on_screen, popup_message, navigation_passthrough, get_zoom_factor, get_mousemove_divisor, scroll, update_mod_keys, warp_mouse, wrap_mouse, scroll_up, scroll_down, force_ui_update, force_pick_hyper_bevels_gizmo_update, get_scale, draw_status_item
from .. utils.vgroup import add_vgroup
from .. utils.view import ensure_visibility, get_location_2d, get_view_origin_and_dir, restore_visibility, visible_get

from .. colors import yellow, blue, green, normal, white, red, orange
from .. items import shift, alt, ctrl, hyperbevel_mode_items, hyperbevel_segment_preset_items, numbers

from .. import HyperCursorManager as HC

class HyperBevelGizmoManager:
    operator_data = {}

    gizmo_props = {}
    gizmo_data = {}

    gizmo_highlighted = []
    gizmo_highlighted_neighbours = []

    def gizmo_poll(self, context):
        if context.mode == 'OBJECT':
            props = self.gizmo_props
            return props.get('area_pointer') == str(context.area.as_pointer()) and props.get('show')

    def gizmo_group_init(self, context, sweep_distance=0.3):
        self.operator_data.clear()
        self.gizmo_props.clear()
        self.gizmo_data.clear()

        self.gizmo_highlighted.clear()
        self.gizmo_highlighted_neighbours.clear()

        self.operator_data['bevel_mods'] = []
        self.operator_data['push_update'] = None                            # used to force an update of self.has_custom_profile from AddCurveAsset()

        self.gizmo_props['show'] = True
        self.gizmo_props['show_sweeps'] = True
        self.gizmo_props['area_pointer'] = str(context.area.as_pointer())
        self.gizmo_props['matrix'] = self.mx                                # both are used for rebuilding the sweep button gizmo locations, when changing the width
        self.gizmo_props['sweep_distance'] = sweep_distance                 # both are used for rebuilding the sweep button gizmo locations, when changing the width
        self.gizmo_props['push_update'] = None                              # used to force an update of the base geo data in HyperBevel.modal()

        self.gizmo_data['sweeps'] = {}
        self.gizmo_data['width'] = {}

        for sidx, data in self.hyper_bevels.items():
            self.operator_data['bevel_mods'].append(data['bevel'])

        self.operator_data['active'] = self.active

        for sidx, seq_data in self.data.items():
            verts = seq_data['verts']
            is_cyclic = seq_data['cyclic']
            is_convex = seq_data['convex']

            data = {'cyclic': is_cyclic,
                    'convex': is_convex,
                    'gizmos': {}}

            for idx, v in enumerate(verts):
                vdata = seq_data['vdata'][v]

                left_co = self.mx @ (v.co + vdata['left_dir'] * self.width * sweep_distance)
                right_co = self.mx @ (v.co + vdata['right_dir'] * self.width * sweep_distance)

                data['gizmos'][idx] = {'left': {'is_highlight': False,

                                                'co': v.co.copy(),
                                                'sweep_dir': vdata['left_dir'],

                                                'sweep_co': left_co,
                                                'options': vdata['left_options'],
                                                'default': vdata['left_default']},
                                       'right': {'is_highlight': False,

                                                 'co': v.co.copy(),                                 # keep these in local space, because they will be used to rebuild the gizmo loc using the local space width and extend amounts
                                                 'sweep_dir': vdata['right_dir'],                   # keep these in local space, because they will be used to rebuild the gizmo loc using the local space width and extend amounts

                                                 'sweep_co': right_co,
                                                 'options': vdata['right_options'],
                                                 'default': vdata['right_default']}}

                if not is_cyclic:
                    if idx == 0:
                        extend_dir = -vdata['dir']

                    elif idx == len(verts) - 1:
                        extend_dir = vdata['dir']

                    else:
                        continue

                    extend_dir_world = (self.mx.to_3x3() @ extend_dir).normalized()

                    loc = self.mx @ (v.co + vdata['dir'] * 0.02 * self.width)
                    rot = create_rotation_matrix_from_vector(extend_dir_world).to_3x3()

                    data['gizmos'][idx]['extend'] = {'is_highlight': False,
                                                     'extend': 0.02 * self.width if is_convex else 0,
                                                     'matrix': Matrix.LocRotScale(loc, rot, Vector((1, 1, 1))),

                                                     'co': v.co.copy(),                            # keep these in local space, because they will be used to rebuild the gizmo loc using the local space width and extend amounts
                                                     'extend_dir': extend_dir,                     # keep these in local space, because they will be used to rebuild the gizmo loc using the local space width and extend amounts

                                                     'loc': loc,
                                                     'rot': rot}

            self.gizmo_data['sweeps'][sidx] = data

        for sidx, seq_data in self.data.items():
            verts = seq_data['verts']

            for idx, v in enumerate(verts):
                vdata = seq_data['vdata'][v]

                next_edge = vdata['next_e']

                if next_edge == self.bmesh['active']:

                    normal = get_edge_normal(next_edge)
                    loop = vdata['loop']

                    center = get_center_between_verts(*next_edge.verts)

                    dir = (vdata['next_v'].co - v.co).normalized()

                    left_dir = normal.cross(dir)
                    right_dir = -normal.cross(dir)

                    left_face = loop.face
                    right_face = loop.link_loop_radial_next.face

                    if i := intersect_line_plane(v.co + left_dir * 0.1, v.co + left_dir * 0.1 + left_face.normal, v.co, left_face.normal):
                        left_face_dir = (i - v.co).normalized()
                    else:
                        print("WARNING: failed to created left face dir in gizmo_group_init(), failing back to vdata['left_face_dir']")
                        left_face_dir = vdata['left_face_dir']

                    if i := intersect_line_plane(v.co + right_dir * 0.1, v.co + right_dir * 0.1 + right_face.normal, v.co, right_face.normal):
                        right_face_dir = (i - v.co).normalized()
                    else:
                        print("WARNING: failed to created right face dir in gizmo_group_init(), failing back to vdata['right_face_dir']")
                        right_face_dir = vdata['right_face_dir']

                    left_face_co = center + left_face_dir * self.width
                    right_face_co = center + right_face_dir * self.width

                    center2d = get_location_2d(context, self.mx @ center)
                    left2d = get_location_2d(context, self.mx @ left_face_co)
                    right2d = get_location_2d(context, self.mx @ right_face_co)

                    mouse_dir= (self.mouse_pos - center2d).normalized()
                    left_dir = (left2d - center2d).normalized()
                    right_dir = (right2d - center2d).normalized()

                    left_dot = mouse_dir.dot(left_dir)
                    right_dot = mouse_dir.dot(right_dir)

                    if left_dot >= right_dot:
                        loc = self.mx @ left_face_co
                        side_dir = left_face_dir

                    else:
                        loc = self.mx @ right_face_co
                        side_dir = right_face_dir

                    side_dir_world = (self.mx.to_3x3() @ side_dir).normalized()        # important to normalize, to take out a potential scale component

                    rot = create_rotation_matrix_from_vector(side_dir_world).to_3x3()  # NOTE: using to_quaternion() will result in inverted gizmos? odd

                    self.gizmo_data['width'] = {'is_highlight': False,
                                                'width': self.width,
                                                'matrix': Matrix.LocRotScale(loc, rot, Vector((1, 1, 1))),

                                                'edge_center': self.mx @ center,
                                                'width_dir': side_dir,

                                                'loc': loc,
                                                'rot': rot}

        context.window_manager.gizmo_group_type_ensure('MACHIN3_GGT_hyper_bevel')

    def gizmo_group_finish(self, context):
        self.operator_data.clear()

        self.gizmo_props.clear()
        self.gizmo_data.clear()

        self.gizmo_highlighted.clear()
        self.gizmo_highlighted_neighbours.clear()

        context.window_manager.gizmo_group_type_unlink_delayed('MACHIN3_GGT_hyper_bevel')

    def gizmo_get_highlighted(self):
        for sidx, seq_data in self.gizmo_data['sweeps'].items():
            gizmos = seq_data['gizmos']

            for idx, data in gizmos.items():

                for side in ['left', 'right']:
                    if data[side]['is_highlight']:
                        default = data[side]['default']
                        highlighted = ['SWEEPS', sidx, idx, side, default]
                        self.gizmo_highlighted.clear()
                        self.gizmo_highlighted.extend(highlighted)
                        return highlighted

                if idx == 0 or idx == len(gizmos) - 1:
                    if (gizmo := data.get('extend')) and gizmo['is_highlight']:
                        highlighted = ['EXTEND', sidx, idx, None, None]

                        self.gizmo_highlighted.clear()
                        self.gizmo_highlighted.extend(highlighted)

                        return highlighted

        if (width := self.gizmo_data['width']) and width['is_highlight']:
            highlighted = ['WIDTH', None, None, None, None]

            self.gizmo_highlighted.clear()
            self.gizmo_highlighted.extend(highlighted)
            return highlighted

        self.gizmo_highlighted.clear()
        self.gizmo_highlighted_neighbours.clear()

    def gizmo_get_highlighted_neighbours(self):
        def get_prev_gizmo_idx(idx, default, new_default):
            if is_cyclic:
                prev_idx = (idx - 1) % len(gizmos)

            else:
                if idx == 0:
                    return

                else:
                    prev_idx = idx - 1

            prev_gizmo = gizmos[prev_idx]

            if default == prev_gizmo[side]['default'] and new_default in prev_gizmo[side]['options']:
                return prev_idx

        def get_next_gizmo_idx(idx, default, new_default):
            if is_cyclic:
                next_idx = (idx + 1) % len(gizmos)

            else:
                if idx == len(gizmos) - 1:
                    return

                else:
                    next_idx = idx + 1

            next_gizmo = gizmos[next_idx]

            if default == next_gizmo[side]['default'] and new_default in next_gizmo[side]['options']:
                return next_idx

        def get_prev_neighbours(start_idx, neighbours, default, new_default):
            idx = start_idx

            while (prev_idx := get_prev_gizmo_idx(idx, default, new_default)) is not None:
                if prev_idx in neighbours:
                    break

                else:
                    neighbours.append(prev_idx)

                idx = prev_idx

        def get_next_neighbours( start_idx, neighbours, default, new_default):
            idx = start_idx

            while (next_idx := get_next_gizmo_idx(idx, default, new_default)) is not None:
                if next_idx in neighbours:
                    break

                else:
                    neighbours.append(next_idx)

                idx = next_idx

        if self.gizmo_highlighted:
            gizmo_type, sidx, idx, side, default = self.gizmo_highlighted
            if gizmo_type == 'SWEEPS':
                is_cyclic = self.gizmo_data['sweeps'][sidx]['cyclic']
                gizmos = self.gizmo_data['sweeps'][sidx]['gizmos']

                options = gizmos[idx][side]['options']
                new_default = step_list(default, options, step=1, loop=True)
                neighbours = [idx]

                get_prev_neighbours(idx, neighbours, default, new_default)
                get_next_neighbours(idx, neighbours, default, new_default)
                neighbours.sort()

                self.gizmo_highlighted_neighbours.clear()
                self.gizmo_highlighted_neighbours.extend(neighbours)

                return neighbours

        self.gizmo_highlighted_neighbours.clear()

def draw_hyper_bevel_status(op):
    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)

        is_sel = op.HUD_selection['active'] or op.HUD_selection['loop'] or op.HUD_selection['edge']

        row.label(text="Hyper Bevel")

        if op.is_selecting:
            if op.is_weld_adjusting:
                draw_status_item(row, active=False, text="Weld Adjustment")

                row.separator(factor=10)

                draw_status_item(row, key='MOVE', text="Threshold", prop=dynamic_format(op.weld_threshold, decimal_offset=2))
                return

            elif op.is_loop_adjusting:
                draw_status_item(row, active=False, text="Loop Adjustment")

                row.separator(factor=10)

                angle = f"{int(180 - op.loop_angle)}°"
                draw_status_item(row, key='MOVE', text="Angle", prop=angle)
                return

            else:
                draw_status_item(row, active=False, text="Selection")

            if is_sel:
                draw_status_item(row, key='LMB_DRAG', text="Drag out Bevel Width")

                if op.width:
                    draw_status_item(row, key='SPACE', text="Repeat previous Bevel")

            draw_status_item(row, key='MMB', text="Viewport")
            draw_status_item(row, key='RMB', text="Cancel")

            row.separator(factor=10)

            draw_status_item(row, key='MOVE', text="Select Edge")

            if op.active_edge:
                draw_status_item(row, active=op.is_loop_selecting, key='SHIFT', text="Loop Select")

                if op.is_loop_selecting:
                    angle = f"{int(180 - op.loop_angle)}°"
                    draw_status_item(row, key='G', text="Adjust Loop Angle", prop=angle, gap=1)

                draw_status_item(row, key='A', text=f"Mark Edge{'s' if op.is_loop_selecting else ''}", gap=2)
                draw_status_item(row, key='X', text=f"Unmark Edge{'s' if op.is_loop_selecting else ''}", gap=2)

            draw_status_item(row, active=op.is_weld, key='ALT', text="Weld Pre-Processing", gap=2)

            if op.is_weld:
                draw_status_item(row, key='T', text="Weld Threshold", prop=dynamic_format(op.weld_threshold, decimal_offset=2), gap=1)

            draw_status_item(row, active=op.wireframe, key='W', text="Wireframe", gap=2)

        elif op.is_dragging:
            draw_status_item(row, active=False, text="width")

            draw_status_item(row, key='LMB', text="Finalize")
            draw_status_item(row, key='MMB', text="Viewport")
            draw_status_item(row, key='TAB', text="Finish into Edit Mode")

            row.separator(factor=10)

            draw_status_item(row, key='LMB_DRAG', text="Adjust", prop=dynamic_format(op.width, decimal_offset=2))

            if op.has_inbetween_align:
                draw_status_item(row, active=op.use_inbetween_align, key='A', text="Inbetween Align", gap=2)

            if op.has_center_aim:
                draw_status_item(row, active=op.use_center_aim, key='C', text="Center Aim", gap=2)

            draw_status_item(row, active=op.wireframe, key='W', text="Wireframe", gap=2)

        elif op.is_gizmo_adjusting:
            draw_status_item(row, active=False, text="Adjustment")

            if op.is_moving:
                draw_status_item(row, key='MMB_SCROLL', text="Move in Stack")
                return

            if op.highlighted:
                if op.highlighted[0] == 'SWEEPS':
                    draw_status_item(row, key='LMB', text="Toggle Sweep", prop=op.get_pretty_alignment()[0])

                elif op.highlighted[0] == 'WIDTH':
                    draw_status_item(row, key='LMB', text="Adjust Width", prop=dynamic_format(op.width, decimal_offset=2))

                elif op.highlighted[0] == 'EXTEND':
                    _, sidx, idx, _, _ = op.highlighted
                    amount = op.gizmo_data['sweeps'][sidx]['gizmos'][idx]['extend']['extend']
                    draw_status_item(row, key='LMB', text="Extend End", prop=dynamic_format(amount, decimal_offset=2))

                    draw_status_item(row, active=op.is_shift, key='SHIFT', text="Both Ends", gap=1)

                    draw_status_item(row, key='R', text="Reset to 0", gap=1)

            else:
                draw_status_item(row, key='LMB', text="Finish")
                draw_status_item(row, key='TAB', text="Finish in Edit Mode")
                draw_status_item(row, key='MMB', text="Viewport")
                draw_status_item(row, key='RMB', text="Cancel")

            if not op.highlighted:
                row.separator(factor=10)

                if op.realtime:
                    if op.can_move:
                        draw_status_item(row, key='ALT', text="Move in Stack")

                    draw_status_item(row, active=not op.chamfer and not op.is_custom_profile, key='MMB_SCROLL', text="Segments", prop=op.profile_segments if op.is_custom_profile else op.segments)

                    if not op.chamfer and not op.is_custom_profile:
                        if op.segments != 6:
                            draw_status_item(row, key=['Y', 'Z'], text="Preset 6", gap=1)

                        if op.segments != 12:
                            draw_status_item(row, key='X', text="Preset 12", gap=1)

                    draw_status_item(row, active=op.chamfer, key='C', text="Chamfer", gap=2)

                    if op.has_custom_profile:
                        row.separator(factor=2)

                        draw_status_item(row, active=False if op.chamfer else op.is_custom_profile, key='B', text="Custom Profile", gap=2)

                        if op.is_custom_profile:
                            draw_status_item(row, key='F', text="Flip Profile", gap=1)
                            draw_status_item(row, key='V', text="Flop Profile", gap=1)

                draw_status_item(row, active=op.gizmo_props['show_sweeps'], key='S', text="Show Sweep Gizmos", gap=2)

                draw_status_item(row, active=op.realtime, key='R', text="Realtime", gap=2)

                draw_status_item(row, active=op.evaluated_wireframe, key='W', text="Evaluated Wirefame", gap=2)
                draw_status_item(row, active=op.wireframe, key=['SHIFT', 'W'], text="Original Wirefame", gap=1)

    return draw

class HyperBevel(bpy.types.Operator, Settings, HyperBevelGizmoManager):
    bl_idname = "machin3.hyper_bevel"
    bl_label = "MACHIN3: Hyper Bevel"
    bl_description = "description"
    bl_options = {'REGISTER', 'UNDO'}

    loop_angle: FloatProperty(name="Loop Select Angle", default=150, min=0, max=180)
    weld_threshold: FloatProperty(name="Weld Threshold", default=0.0001, min=0)
    weld_suggestion: BoolProperty(name="Weld Processing is Suggested", default=False)
    width: FloatProperty(name="Bevel Width Threshold", default=0, min=0)
    segments: IntProperty(name="Segments", default=12, min=0)
    chamfer: BoolProperty(name="Chamfer", default=False)
    has_center_aim: BoolProperty(name="has Center Aim", default=False)
    has_inbetween_align: BoolProperty(name="has Inbetween Alignment", default=False)
    use_center_aim: BoolProperty(name="use Center Aim", default=False)
    use_inbetween_align: BoolProperty(name="use Inbetween Alignment", default=False)
    realtime: BoolProperty(name="Realtime", default=False)
    wireframe: BoolProperty(name="Wireframe", default=False)
    evaluated_wireframe: BoolProperty(name="Evaluated Wireframe", default=False)

    passthrough = None

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            active = context.active_object
            return active and active.type == 'MESH'

    def draw(self, context):
        layout = self.layout
        _column = layout.column(align=True)

    def draw_HUD(self, context):
        def draw_HUD_selection_pass(self):
            sel = self.HUD_selection

            title = "Hyper Bevel " if sel['bevel_count'] <= 1 else f"{sel['bevel_count']} x Hyper Bevel "
            dims = draw_label(context, title=title, coords=Vector((self.HUD_x, self.HUD_y)), center=False, alpha=1)

            if self.is_weld_adjusting:
                dims += draw_label(context, title="Adjusting Weld", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, size=10, color=orange, alpha=1)

                if self.is_shift or self.is_ctrl:
                    title = ' a little' if self.is_shift else ' a lot'
                    draw_label(context, title=title, coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, size=10, color=white, alpha=0.5)

                self.offset += 18

                dims = draw_label(context, title="Threshold: ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=0.5)

                precision = 2 if self.is_shift else 0 if self.is_ctrl else 1
                draw_label(context, title=dynamic_format(self.weld_threshold, decimal_offset=precision), coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=yellow, alpha=1)

            else:

                if self.is_loop_adjusting:
                    dims += draw_label(context, title="Adjusting ", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, size=10, color=orange, alpha=1)

                title, color, alpha = ('Loop Selection', yellow, 1) if self.is_shift else ('Selection', white, 0.5)
                draw_label(context, title=title, coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, size=10, color=color, alpha=alpha)

                if self.is_loop_adjusting:
                    self.offset += 18

                    angle = f"{int(180 - self.loop_angle)}°"

                    dims = draw_label(context, title="Loop Angle: ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, alpha=0.5)
                    draw_label(context, title=angle, coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=yellow, alpha=1)

                self.offset += 18

                dims = draw_label(context, title="Edge: ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, alpha=0.5)
                dims += draw_label(context, title=str(sel['active']), coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=red if sel['active'] is None else yellow, alpha=1)

                if loop := sel['loop']:
                    dims += draw_label(context, title=f" +{len(loop)} Loop", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, size=10, color=yellow, alpha=1)

                if marked := sel['edge']:
                    draw_label(context, title=f" +{len(marked)} Marked", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, size=10, color=green, alpha=1)

                if self.is_loop_adjusting:
                    return

                if self.is_weld:
                    self.offset += 18

                    draw_label(context, title="Weld Pre-Processing", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=yellow, alpha=1)

                if self.wireframe:
                    self.offset += 18

                    draw_label(context, title="Wireframe", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=blue, alpha=1)

        def draw_HUD_drag_pass(self):
            sel = self.HUD_selection

            title = "Hyper Bevel " if sel['bevel_count'] == 1 else f"{sel['bevel_count']} x Hyper Bevel "
            dims = draw_label(context, title=title, coords=Vector((self.HUD_x, self.HUD_y)), center=False, alpha=1)
            draw_label(context, title="Creation ", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, size=10, color=white, alpha=0.5)

            self.offset += 18

            dims = draw_label(context, title="Width: ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=0.5)
            draw_label(context, title=dynamic_format(self.width, decimal_offset=2), coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=yellow, alpha=1)

            if self.has_inbetween_align or self.has_center_aim:#
                self.offset += 18

                dims = draw_label(context, title="Align: ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=0.5)

                if self.has_inbetween_align:
                    color, alpha = (blue, 1) if self.use_inbetween_align else (white, 0.3)
                    draw_label(context, title="Inbetween", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=color, alpha=alpha)

                if self.has_center_aim:
                    if self.has_inbetween_align:
                        self.offset += 18

                    color, alpha = (yellow, 1) if self.use_center_aim else (white, 0.3)
                    draw_label(context, title="Center Aim", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=color, alpha=alpha)

            if self.wireframe:
                self.offset += 18

                draw_label(context, title="Wireframe", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=blue, alpha=1)

        def draw_gizmo_adjustment_pass(self):
            sel = self.HUD_selection

            is_sweep_highlight = self.highlighted and self.highlighted[0] == 'SWEEPS'
            is_width_highlight = self.highlighted and self.highlighted[0] == 'WIDTH'
            is_extend_highlight = self.highlighted and self.highlighted[0] == 'EXTEND'

            title = "Hyper Bevel " if is_sweep_highlight or is_extend_highlight or sel['bevel_count'] == 1 else f"{sel['bevel_count']} x Hyper Bevel "
            dims = draw_label(context, title=title, coords=Vector((self.HUD_x, self.HUD_y)), center=False, alpha=1)

            if is_sweep_highlight:
                title, color = self.get_pretty_alignment()

                if self.is_shift:
                    dims += draw_label(context, title="Sweep ", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, size=10, color=white, alpha=0.5)
                    dims += draw_label(context, title="Batch ", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, size=10, color=color, alpha=1)
                    draw_label(context, title="Alignment", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, size=10, color=white, alpha=0.5)

                else:
                    draw_label(context, title="Sweep Alignment", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, size=10, color=white, alpha=0.5)

                self.offset += 18

                draw_label(context, title=title, coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=color, alpha=1)

            elif is_extend_highlight:
                dims += draw_label(context, title="Extend", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, size=10, color=yellow, alpha=1)

                if self.is_shift:
                    draw_label(context, title=" both ends", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, size=10, color=white, alpha=0.5)

                self.offset += 18

                _, sidx, idx, _, _ = self.highlighted
                amount = self.gizmo_data['sweeps'][sidx]['gizmos'][idx]['extend']['extend']

                dims = draw_label(context, title="Amount: ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=0.5)
                draw_label(context, title=dynamic_format(amount, decimal_offset=2), coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=yellow, alpha=1)

            else:
                if is_width_highlight:
                    dims += draw_label(context, title="Width ", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, size=10, color=yellow, alpha=1)
                    draw_label(context, title="Adjustment ", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, size=10, color=white, alpha=0.5)

                else:
                    draw_label(context, title="Adjustment ", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, size=10, color=white, alpha=0.5)

                self.offset += 18

                color = yellow if is_width_highlight else white

                dims = draw_label(context, title="Width: ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=0.5)
                draw_label(context, title=dynamic_format(self.width, decimal_offset=2), coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=color, alpha=1)

                if not is_width_highlight:

                    self.offset += 18

                    if self.chamfer:
                        dims = draw_label(context, title="Chamfer ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=blue, alpha=1)

                        if self.has_custom_profile:
                            draw_label(context, title="🌠", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=blue, alpha=1)

                    else:
                        segments = self.profile_segments if self.is_custom_profile else self.segments

                        dims = draw_label(context, title="Segments: ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=0.3 if self.is_custom_profile else 0.5)
                        dims += draw_label(context, title=f"{segments} ", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=color, alpha=0.3 if self.is_custom_profile else 1)

                        if self.has_custom_profile:
                            text = "Custom Profile" if self.is_custom_profile else "🌠"
                            draw_label(context, title=text, coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=blue, alpha=1)

                    if not self.chamfer and self.is_custom_profile and self.profile_HUD_coords:
                        draw_line(self.profile_HUD_coords, width=2, color=blue, alpha=0.75)
                        draw_line(self.profile_HUD_border_coords, width=1, color=white, alpha=0.1)

                        for dir, origin in self.profile_HUD_edge_dir_coords:
                            draw_vector(dir, origin=origin, color=blue, fade=True)

                    if self.realtime:
                        self.offset += 18

                        draw_label(context, title="Realtime", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=green, alpha=1)

                    if self.wireframe or self.evaluated_wireframe:
                        self.offset += 18

                        wiretype = "Original + Evaluated" if self.wireframe and self.evaluated_wireframe else "Original" if self.wireframe else "Evaluated"

                        draw_label(context, title=f"{wiretype} Wireframe", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=blue, alpha=1)

        if context.area == self.area:
            draw_init(self)

            if self.is_selecting:
                draw_HUD_selection_pass(self)

            elif self.is_dragging:
                draw_HUD_drag_pass(self)

            elif self.is_gizmo_adjusting:

                if self.is_moving:
                    sel = self.HUD_selection

                    ui_scale = get_scale(context)
                    mods, mods_len, current_idx = self.get_mods_and_indices(debug=False)
                    bevel_count = len(self.hyper_bevels)

                    dims = draw_label(context, title="Move ", coords=Vector((self.HUD_x, self.HUD_y)), center=False, color=yellow, alpha=1)

                    title = "Hyper Bevel " if sel['bevel_count'] == 1 else f"{sel['bevel_count']} x Hyper Bevel "
                    draw_label(context, title=title, coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, alpha=1)

                    self.offset += 18

                    dims = draw_label(context, title="Stack: ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, alpha=0.5)

                    for idx, mod in enumerate(mods):
                        is_bevel = current_idx <= idx < current_idx + bevel_count

                        if idx:
                            self.offset += 18

                        if idx == current_idx:
                            coords = [Vector((self.HUD_x + dims.x - (5 * ui_scale), self.HUD_y - (self.offset * ui_scale) - ((bevel_count - 1) * 18 * ui_scale) , 0)), Vector((self.HUD_x + dims.x - (5 * ui_scale), self.HUD_y - (self.offset * ui_scale) + (10 * ui_scale), 0))]
                            draw_line(coords, color=yellow, width=2 * ui_scale, screen=True)

                        size, color, alpha = (12, yellow, 1) if is_bevel else (10, white, 0.4)

                        draw_label(context, title=mod.name, coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, size=size, color=color, alpha=alpha)

                else:
                    draw_gizmo_adjustment_pass(self)

            if self.weld_suggestion:
                self.offset += 18

                dims = draw_label(context, title="⚠", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, size=20, color=yellow, alpha=1)
                draw_label(context, title=" Try Weld Pre-Processing", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=yellow, alpha=1)

    def draw_VIEW3D(self, context):
        if context.area == self.area:

            if self.is_selecting:

                if sel := self.coords['selected']:
                    draw_lines(sel, width=2, color=green, alpha=0.5)

                if loop := self.coords['loop']:
                    draw_lines(loop, width=2, color=yellow, alpha=0.4)

                if active := self.coords['active']:
                    draw_line(active, width=2, color=yellow, alpha=0.9)

                if self.wireframe:
                    batch = self.batches['WELD'] if self.is_weld else self.batches['ORIG']
                    draw_batch(batch, color=blue, xray=True, alpha=0.6 if self.is_weld_adjusting else 0.3)

            elif self.is_dragging:

                if self.wireframe:
                    batch = self.batches['WELD'] if self.is_weld else self.batches['ORIG']
                    draw_batch(batch, color=blue, xray=True, alpha=0.3)

                if sweep := self.coords['sweep']:

                    for coords, indices in sweep:
                        draw_lines(coords, indices, color=yellow, alpha=0.5)

                if False:
                    if self.coords['debug']:
                        coords = self.coords['debug']

                        if True:
                            draw_points(coords['spine'][1:-1], size=4)

                            draw_point(coords['spine'][0], size=6, color=green)
                            draw_point(coords['spine'][-1], size=6, color=red)

                            if False:
                                draw_vectors([dir for dir, _ in coords['dirs']], origins=[loc for _, loc in coords['dirs']], color=normal, fade=True, alpha=1)

                            if False:
                                draw_vectors([dir for dir, _ in coords['left_dirs']], origins=[loc for _, loc in coords['left_dirs']], color=white, fade=False, alpha=0.5)
                                draw_vectors([dir for dir, _ in coords['right_dirs']], origins=[loc for _, loc in coords['right_dirs']], color=white, fade=False, alpha=0.5)

                        if False:

                            if True:
                                draw_vectors([dir for dir, _ in coords['left_face_dirs']], origins=[loc for _, loc in coords['left_face_dirs']], color=red, fade=True, alpha=1)
                                draw_vectors([dir for dir, _ in coords['right_face_dirs']], origins=[loc for _, loc in coords['right_face_dirs']], color=red, fade=True, alpha=1)

                            if True:
                                draw_vectors([dir for dir, _ in coords['left_edge_dirs']], origins=[loc for _, loc in coords['left_edge_dirs']], color=green, fade=True, alpha=1)
                                draw_vectors([dir for dir, _ in coords['right_edge_dirs']], origins=[loc for _, loc in coords['right_edge_dirs']], color=green, fade=True, alpha=1)

                            if True:
                                draw_vectors([dir for dir, _ in coords['left_center_aim_dirs']], origins=[loc for _, loc in coords['left_center_aim_dirs']], color=yellow, fade=True, alpha=1)
                                draw_vectors([dir for dir, _ in coords['right_center_aim_dirs']], origins=[loc for _, loc in coords['right_center_aim_dirs']], color=yellow, fade=True, alpha=1)

                            if True:
                                draw_vectors([dir for dir, _ in coords['left_inbetween_dirs']], origins=[loc for _, loc in coords['left_inbetween_dirs']], color=blue, fade=True, alpha=1)
                                draw_vectors([dir for dir, _ in coords['right_inbetween_dirs']], origins=[loc for _, loc in coords['right_inbetween_dirs']], color=blue, fade=True, alpha=1)

                        if True:
                            for dir, origin, color in coords['sweep_dirs']:
                                draw_vector(dir, origin=origin, color=color, fade=True, alpha=1)

                        if True:
                            for co in coords['sweep_coords']:
                                draw_point(co)

            elif self.is_gizmo_adjusting:
                is_highlighted_sweeps = self.highlighted and self.highlighted[0] == 'SWEEPS'
                is_highlighted_width = self.highlighted and self.highlighted[0] == 'WIDTH'
                is_highlighted_extend = self.highlighted and self.highlighted[0] == 'EXTEND'

                if self.wireframe:
                    batch = self.batches['WELD'] if self.is_weld else self.batches['ORIG']
                    draw_batch(batch, color=blue, xray=True, alpha=0.3)

                if sweep := self.coords['sweep']:

                    for sidx, (coords, indices) in enumerate(sweep):
                        alpha = 1 if is_highlighted_width else 0.5
                        draw_lines(coords, indices, color=yellow, alpha=alpha)

                        if is_highlighted_extend and sidx == self.highlighted[1]:

                            if self.is_shift:
                                draw_line(coords[:3], width=2, color=yellow, alpha=1)
                                draw_line(coords[-3:], width=2, color=yellow, alpha=1)

                            else:
                                end_coords = coords[:3] if self.highlighted[2] == 0 else coords[-3:]
                                draw_line(end_coords, width=2, color=yellow, alpha=1)

                if is_highlighted_sweeps and (sweep_coords := self.coords['individual_sweeps']):
                    gizmo_type, sidx, idx, side, default = self.highlighted
                    if gizmo_type == 'SWEEPS':
                        if self.is_shift and self.highlighted_neighbours:
                            coords = []

                            for idx in self.highlighted_neighbours:
                                coords.extend(sweep_coords[sidx][idx][side])

                            draw_lines(coords, width=2, color=self.get_pretty_alignment()[1], alpha=1)

                        else:
                            coords = sweep_coords[sidx][idx][side]
                            draw_line(coords, width=2, color=self.get_pretty_alignment()[1], alpha=1)

    def modal(self, context, event) :
        if ignore_events(event):
            return {'RUNNING_MODAL'}

        context.area.tag_redraw()

        if event.type == 'MOUSEMOVE':
            get_mouse_pos(self, context, event, window=True)

            if self.is_gizmo_adjusting and self.is_custom_profile:
                self.get_profile_HUD_coords(context)

        if self.is_selecting:
            if ret := self.selection_pass(context, event):
                return ret

        elif self.is_dragging:
            if ret := self.drag_pass(context, event):
                return ret

        elif self.is_gizmo_adjusting:
            if ret := self.gizmo_adjustment_pass(context, event):
                return ret

        if navigation_passthrough(event) or (self.is_gizmo_adjusting and event.type == 'T'):
            return {'PASS_THROUGH'}

        elif self.is_gizmo_adjusting and not self.is_in_3d_view and event.type in ['LEFTMOUSE', *numbers[:10]] and event.value == 'PRESS':
            return {'PASS_THROUGH'}

        elif self.is_gizmo_adjusting and self.is_in_3d_view and event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            return {'PASS_THROUGH'}

        elif event.type in ['LEFTMOUSE', 'SPACE']:

            if self.is_selecting and event.value == 'PRESS':
                self.finish(context)
                return {'CANCELLED'}

            elif self.is_gizmo_adjusting and event.value == 'PRESS':
                self.finish(context)

                if not self.realtime:
                    for data in self.hyper_bevels.values():
                        mod = data['boolean']

                        if not mod.object:
                            mod.object = data['obj']

                        mod.show_viewport = True

                if event.type == 'LEFTMOUSE':
                    bpy.ops.object.select_all(action='DESELECT')

                    for data in self.hyper_bevels.values():
                        cutter = data['obj']

                        cutter.hide_set(False)
                        cutter.select_set(True)
                        context.view_layer.objects.active = cutter

                self.active.show_wire = self.init_show_wire

                self.save_settings()

                if self.is_custom_profile:
                    self.store_settings('hyper_bevel', {'custom_profile': get_bevel_profile_as_dict(self.hyper_bevels[0]['bevel'])})

                else:
                   self.store_settings('hyper_bevel', {'custom_profile': None})

                return {'FINISHED'}

        elif event.type in ['RIGHTMOUSE', 'ESC'] and event.value == 'PRESS':
            self.finish(context)

            for data in self.hyper_bevels.values():
                remove_mod(data['boolean'])

                remove_obj(data['obj'])

            self.active.show_wire = self.init_show_wire

            return {'CANCELLED'}

        self.last_mouse = self.mouse_pos

        return {'RUNNING_MODAL'}

    def finish(self, context):
        finish_modal_handlers(self)

        self.gizmo_group_finish(context)

        self.S.finish()
        self.S_weld.finish()

        finish_status(self)

        restore_gizmos(self)

    def invoke(self, context, event):
        self.init_settings(props=['segments', 'chamfer', 'width', 'loop_angle'])
        self.load_settings()

        self.active = context.active_object
        self.mx = self.active.matrix_world
        self.dg = context.evaluated_depsgraph_get()

        update_mod_keys(self)

        self.is_active_smooth = self.active.data.polygons[0].use_smooth

        self.is_selecting = True
        self.is_loop_selecting = False
        self.is_dragging = False
        self.is_gizmo_adjusting = False

        self.is_moving = False
        self.can_move = False

        self.is_weld = False
        self.is_weld_adjusting = False
        self.is_loop_adjusting = False

        self.realtime = True
        self.wireframe = False
        self.weld_suggestion = False
        self.evaluated_wireframe = self.active.show_wire
        self.init_show_wire = self.active.show_wire

        self.has_center_aim = False
        self.has_inbetween_align = False
        self.use_center_aim = False
        self.use_inbetween_align = False

        self.has_custom_profile = False
        self.is_custom_profile = False
        self.profile_segments = 2         # will be changed when a profile is actually dropped, or space repeated

        self.highlighted = None
        self.highlighted_neighbours = None
        self.skip_fetching_highlighted = 0

        self.coords = {'active': [],
                       'selected': [],
                       'loop': [],
                       'sorted': [],
                       'sweep': [],
                       'individual_sweeps': [],
                       'debug': {}}

        self.get_profile_HUD_coords(context)

        get_mouse_pos(self, context, event, window=True)

        self.last_mouse = self.mouse_pos

        self.init_snap_objects(context)

        self.active_edge = self.get_active_edge()
        self.prev_active = self.active_edge  # NOTE: used to watch changes in the active, for instance to re-init loop selection on the other object, when toggling ALT while holding shift

        self.selection = {'edges': [],
                          'loop': []}

        self.hyper_bevels = {}

        self.HUD_selection = self.get_total_selection(context, mode='HUD')

        self.batches = self.populate_batches(context, init=True)

        hide_gizmos(self, context)

        init_status(self, context, func=draw_hyper_bevel_status(self))

        self.area = context.area
        self.is_in_3d_view = self.is_mouse_in_3d_view()

        init_modal_handlers(self, context, area=False, hud=True, view3d=True)
        return {'RUNNING_MODAL'}

    def selection_pass(self, context, event):
        update_mod_keys(self, event)

        if self.active_edge:

            if self.is_shift and not self.is_loop_selecting:
                self.is_loop_selecting = True

                self.selection['loop'] = self.get_loop_selection()

            elif not self.is_shift and self.is_loop_selecting:
                self.is_loop_selecting = False

                self.selection['loop'] = []
                self.coords['loop'] = []

        if self.is_weld:
            is_key(self, event, 'T', onpress=self.update_weld_adjustment(context, 'PRESS'), onrelease=self.update_weld_adjustment(context, 'RELEASE'))

            if self.is_weld_adjusting:

                wrap_mouse(self, context, x=True)

                delta_x = self.mouse_pos.x - self.last_mouse.x

                divisor = get_mousemove_divisor(event, sensitivity=1000)
                self.weld_threshold += delta_x / divisor

                s = self.S_weld

                weldhost = s.alternative[0]

                welds = [mod for mod in weldhost.modifiers if mod.type == 'WELD']

                if welds:
                    weld = welds[-1]
                    weld.merge_threshold = self.weld_threshold

                    s._init_cache(weldhost)
                    s.hitface = None

                    self.active_edge = self.transfer_active_edge()

                    if self.is_loop_selecting:
                        self.selection['loop'] = self.get_loop_selection()

                    self.selection['edges'] = self.transfer_edge_selection()

                    self.batches = self.populate_batches(context, orig=False, weld=True)

                    self.last_mouse = self.mouse_pos

                    return {'RUNNING_MODAL'}

        if self.is_loop_selecting:
            is_key(self, event, 'G', onpress=self.update_loop_adjustment(context, 'PRESS'), onrelease=self.update_loop_adjustment(context, 'RELEASE'))

            if self.is_loop_adjusting:
                wrap_mouse(self, context, x=True)

                delta_x = self.mouse_pos.x - self.last_mouse.x
                divisor = get_mousemove_divisor(event, normal=1, shift=1, ctrl=1, sensitivity=20)

                self.loop_angle -= delta_x / divisor

                self.selection['loop'] = self.get_loop_selection()

                self.HUD_selection = self.get_total_selection(context, mode='HUD')

                self.last_mouse = self.mouse_pos

                force_ui_update(context)

                return {'RUNNING_MODAL'}

        self.HUD_selection = self.get_total_selection(context, mode='HUD')

        events = ['MOUSEMOVE', 'W', *alt]

        if self.active_edge:
            events.extend(['A', 'X'])

        if event.type in events or scroll(event, key=True):

            if event.type == 'MOUSEMOVE':

                self.active_edge = self.get_active_edge()

                if self.has_active_edge_changed(debug=False) and self.is_loop_selecting:
                    self.selection['loop'] = self.get_loop_selection()

                force_ui_update(context)

            elif event.type == 'A' and event.value == 'PRESS':
                self.update_edge_selection('ADD')

            elif event.type == 'X' and event.value == 'PRESS':
                self.update_edge_selection('REMOVE')

            elif event.type in alt and event.value == 'PRESS':
                self.is_weld = not self.is_weld

                self.active_edge = self.get_active_edge()

                if self.is_loop_selecting:
                    self.selection['loop'] = self.get_loop_selection()

                self.selection['edges'] = self.transfer_edge_selection()

                force_ui_update(context)

            elif event.type == 'W' and event.value == 'PRESS':
                self.wireframe = not self.wireframe

                force_ui_update(context)

        if (self.active_edge or self.selection['edges']):

            if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
                self.is_selecting = False
                self.is_dragging = True

                self.wireframe = True

                self.bmesh = self.get_total_selection(context, mode='BMESH', debug=False)

                if width := self.get_bevel_width(context):
                    self.width = width

                self.data = self.analyse_geometry_conditions(debug=False)

                self.base = self.create_base_cutter_data(debug=False)

                force_ui_update(context)
                return {'RUNNING_MODAL'}

            elif self.width and event.type == 'SPACE' and event.value == 'PRESS':
                self.is_selecting = False
                self.is_gizmo_adjusting = True

                self.wireframe = False
                self.evaluated_wireframe = True
                self.active.show_wire = True

                self.bmesh = self.get_total_selection(context, mode='BMESH', debug=False)

                self.data = self.analyse_geometry_conditions(debug=False)

                self.base = self.create_base_cutter_data(debug=False)

                self.create_base_cutter(context, init=True, edit_mode=False)

                if profile := self.fetch_setting('hyper_bevel', 'custom_profile'):

                    self.profile_segments = profile['segments'] - 1

                    self.has_custom_profile = True
                    self.is_custom_profile = True

                self.create_finished_cutter(context, init=True, profile=profile if not self.chamfer else None)

                self.gizmo_group_init(context)

                if profile:
                    self.get_profile_HUD_coords(context)

                force_ui_update(context)
                return {'RUNNING_MODAL'}

    def drag_pass(self, context, event):
        events = ['MOUSEMOVE', 'W']

        if self.has_inbetween_align:
            events.extend(['A', 'B'])

        if self.has_center_aim:
            events.append('C')

        if event.type in events:

            if event.type == 'MOUSEMOVE':
                if width := self.get_bevel_width(context):
                    self.width = width

                    self.base = self.create_base_cutter_data(debug=False)

                    force_ui_update(context)

            elif event.type in ['A', 'B'] and event.value == 'PRESS':
                self.use_inbetween_align = not self.use_inbetween_align

                self.set_global_inbetween_align()

                self.base = self.create_base_cutter_data(debug=False)

                force_ui_update(context)

            elif event.type == 'C' and event.value == 'PRESS':
                self.use_center_aim = not self.use_center_aim

                self.set_global_center_aim()

                self.base = self.create_base_cutter_data(debug=False)

                force_ui_update(context)

            elif event.type == 'W' and event.value == 'PRESS':
                self.wireframe = not self.wireframe

                force_ui_update(context)

        if self.width:

            if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
                self.is_dragging = False
                self.is_gizmo_adjusting = True

                self.wireframe = False
                self.evaluated_wireframe = True
                self.active.show_wire = True

                self.create_base_cutter(context, init=True, edit_mode=False)

                self.create_finished_cutter(context, init=True)

                self.gizmo_group_init(context)
                return {'RUNNING_MODAL'}

            elif event.type == 'TAB' and event.value == 'PRESS':
                self.finish(context)

                self.create_base_cutter(context, init=True, edit_mode=True)
                return {'FINISHED'}

    def gizmo_adjustment_pass(self, context, event):
        self.is_in_3d_view = self.is_mouse_in_3d_view()

        update_mod_keys(self, event)

        self.is_moving = self.can_move and self.is_in_3d_view and event.alt

        if self.is_moving:
            if scroll(event, key=True):
                mods, mods_len, current_idx = self.get_mods_and_indices(debug=False)
                bevel_count = len(self.hyper_bevels)

                if scroll_up(event, key=True):
                    if current_idx > 0:

                        for i in range(bevel_count):
                            self.active.modifiers.move(current_idx + i, current_idx + i - 1)

                        self.ensure_prefix(direction='UP')

                else:
                    if current_idx + len(self.hyper_bevels) < mods_len:
                        for i in range(bevel_count):
                            self.active.modifiers.move(current_idx, current_idx + bevel_count)

                        self.ensure_prefix(direction='DOWN')

            return {'RUNNING_MODAL'}

        if updated := self.gizmo_props['push_update']:
            self.gizmo_props['push_update'] = None
            update_type, data = updated

            if update_type == 'SWEEPS':
                if self.highlighted and self.highlighted[0] == 'SWEEPS':
                    self.highlighted[-1] = data

                warp_mouse(self, context, self.mouse_pos)

                self.skip_fetching_highlighted = 2

            elif update_type == 'EXTEND':
                pass

            elif update_type == 'WIDTH':
                self.width = data

            self.base = self.create_base_cutter_data(gizmo_data=True, debug=False)

            self.create_base_cutter(context, init=False, edit_mode=False)

            self.create_finished_cutter(context, init=False)

        if self.operator_data['push_update']:
            self.operator_data['push_update'] = None

            self.has_custom_profile = True
            self.is_custom_profile = True

            self.profile_segments = len(self.operator_data['bevel_mods'][0].custom_profile.points) - 2

            self.chamfer = False

            self.get_profile_HUD_coords(context)

        if self.skip_fetching_highlighted:
            self.skip_fetching_highlighted -= 1

        else:
            self.highlighted = self.gizmo_get_highlighted()

            self.highlighted_neighbours = self.gizmo_get_highlighted_neighbours()

            force_ui_update(context)

        if self.highlighted:

            if self.highlighted[0] == 'EXTEND':
                if event.type == 'R' and event.value == 'PRESS':
                    _, sidx, idx, _, _ = self.highlighted

                    gizmos = self.gizmo_data['sweeps'][sidx]['gizmos']

                    indices = [idx, len(gizmos) - 1 if idx == 0 else 0] if self.is_shift else [idx]

                    for idx in indices:
                        data = gizmos[idx]

                        for side in ['left', 'right']:
                            co = data[side]['co']

                            sweep_dir = data[side]['sweep_dir'] * self.gizmo_data['width']['width'] * self.gizmo_props['sweep_distance']
                            data[side]['sweep_co'] =  self.mx @ (co + sweep_dir)

                        data['extend']['extend'] = 0
                        data['extend']['matrix'] = Matrix.LocRotScale(self.mx @ data['extend']['co'], data['extend']['rot'], Vector((1, 1, 1)))
                        data['extend']['loc'] = self.mx @ data['extend']['co']

                    self.base = self.create_base_cutter_data(gizmo_data=True, debug=False)

                    self.create_base_cutter(context, init=False, edit_mode=False)

                    self.create_finished_cutter(context, init=False)

        else:
            events = ['R', 'S', 'W', 'C']

            if self.has_custom_profile:
                events.append('B')

                if self.is_custom_profile:
                    events.extend(['F', 'V'])

            if not self.chamfer and not self.is_custom_profile:
                events.extend(['X', 'Y', 'Z'])

            if event.type in events or scroll(event, key=True):

                if self.is_in_3d_view and not self.chamfer and not self.is_custom_profile and scroll(event, key=True):
                    if scroll_up(event, key=True):
                        self.segments += 1

                    else:
                        self.segments -= 1

                    for data in self.hyper_bevels.values():
                        data['bevel'].segments = self.segments + 1

                elif event.type == 'C' and event.value == 'PRESS':
                    self.chamfer = not self.chamfer

                    for data in self.hyper_bevels.values():
                        data['bevel'].segments = 1 if self.chamfer else self.profile_segments + 1 if self.is_custom_profile else self.segments + 1

                elif event.type in ['X', 'Y', 'Z'] and event.value == 'PRESS':
                    self.segments = 12 if event.type == 'X' else 6

                    for data in self.hyper_bevels.values():
                        data['bevel'].segments = self.segments + 1

                    if self.chamfer:
                        self.chamfer = False

                elif event.type == 'B' and event.value == 'PRESS':

                    if self.is_custom_profile:

                        if self.chamfer:
                            self.chamfer = False

                            for data in self.hyper_bevels.values():
                                data['bevel'].segments = self.profile_segments + 1

                            return {'RUNNING_MODAL'}

                        else:
                            self.is_custom_profile = False

                            for data in self.hyper_bevels.values():
                                data['bevel'].profile_type = 'SUPERELLIPSE'
                                data['bevel'].segments = self.segments + 1

                    else:
                        self.is_custom_profile = True

                        if self.chamfer:
                            self.chamfer = False

                        for data in self.hyper_bevels.values():
                            data['bevel'].profile_type = 'CUSTOM'
                            data['bevel'].segments = self.profile_segments + 1

                        self.get_profile_HUD_coords(context)

                elif event.type == 'F' and event.value == 'PRESS':
                    for data in self.hyper_bevels.values():
                        flip_bevel_profile(data['bevel'])

                    self.get_profile_HUD_coords(context)

                elif event.type == 'V' and event.value == 'PRESS':
                    for data in self.hyper_bevels.values():
                        flop_bevel_profile(data['bevel'])

                    self.get_profile_HUD_coords(context)

                elif event.type == 'S' and event.value == 'PRESS':
                    self.gizmo_props['show_sweeps'] = not self.gizmo_props['show_sweeps']

                elif event.type == 'R' and event.value == 'PRESS':
                    self.realtime = not self.realtime

                    for data in self.hyper_bevels.values():
                        mod = data['boolean']

                        if self.realtime:
                            mod.object = data['obj']
                            mod.show_viewport = True

                        else:
                            mod.show_viewport = False
                            mod.object = None

                elif event.type == 'W' and event.value == 'PRESS':

                    if event.shift:
                        self.wireframe = not self.wireframe

                    else:
                        self.evaluated_wireframe = not self.evaluated_wireframe
                        self.active.show_wire = self.evaluated_wireframe

            elif event.type == 'TAB' and event.value == 'PRESS':
                self.finish(context)

                self.create_base_cutter(context, init=False, edit_mode=True)

                self.active.show_wire = self.init_show_wire
                return {'FINISHED'}

        if gizmo_selection_passthrough(self, event):
            return {'PASS_THROUGH'}

    def init_snap_objects(self, context, debug=False):
        self.S = Snap(context, include=[self.active], debug=False)
        self.S._init_cache(self.active)

        self.S_weld = Snap(context, include=[self.active], alternative=[self.active], debug=False)

        add_weld(self.S_weld.alternative[0], distance=self.weld_threshold, mode='ALL')

        self.dg.update()
        self.S_weld._init_cache(self.S_weld.alternative[0])

        if debug:
            print(self.S.cache.bmeshes[self.active.name])
            print(self.S_weld.cache.bmeshes[self.S_weld.alternative[0].name])

    def populate_batches(self, context, init=False, orig=True, weld=True):
        batches = {} if init else self.batches

        if orig:
            mesh_eval = self.S.cache.meshes[self.active.name]
            batches['ORIG'] = get_batch_from_mesh(mesh_eval, mx=self.mx)

        if weld:
            mesh_eval = self.S_weld.cache.meshes[self.S_weld.alternative[0].name]
            batches['WELD'] = get_batch_from_mesh(mesh_eval, mx=self.mx)

        return batches

    def update_weld_adjustment(self, context, value='PRESS'):
        def press():
            self.is_weld_adjusting = True
            context.window.cursor_set('SCROLL_X')

            self.wireframe = True

            self.weld_mouse = self.mouse_pos

            force_ui_update(context)

        def release():
            self.is_weld_adjusting = False
            context.window.cursor_set('DEFAULT')

            warp_mouse(self, context, self.weld_mouse)

            force_ui_update(context)

        if value == 'PRESS':
            return press

        elif value == 'RELEASE':
            return release

    def update_loop_adjustment(self, context, value='PRESS'):
        def press():
            self.is_loop_adjusting = True
            context.window.cursor_set('SCROLL_X')

            self.wireframe = True

            self.loop_mouse = self.mouse_pos

            force_ui_update(context)

        def release():
            self.is_loop_adjusting = False
            context.window.cursor_set('DEFAULT')

            warp_mouse(self, context, self.loop_mouse)

            force_ui_update(context)

        if value == 'PRESS':
            return press

        elif value == 'RELEASE':
            return release

    def is_mouse_in_3d_view(self):
        area_coords = {'x': (self.area.x, self.area.x + self.area.width),
                       'y': (self.area.y, self.area.y + self.area.height)}

        if area_coords['x'][0] < self.mouse_pos_window.x < area_coords['x'][1]:
            return area_coords['y'][0] < self.mouse_pos_window.y < area_coords['y'][1]
        return False

    def get_profile_HUD_coords(self, context):
        self.profile_HUD_coords = []
        self.profile_HUD_border_coords = []
        self.profile_HUD_edge_dir_coords = []

        if self.has_custom_profile:
            profile = self.hyper_bevels[0]['bevel'].custom_profile

            points = profile.points

            ui_scale = get_scale(context)
            size = 100

            offset_x = get_text_dimensions(context, text=f"Segments: {len(points) - 2} Custom Profile ")[0]
            offset_y = -(6 * ui_scale) - size

            offset = Vector((offset_x, offset_y))

            for p in points:
                co = Vector((self.HUD_x, self.HUD_y)) + offset + p.location * size
                self.profile_HUD_coords.append(co.resized(3))

            for corner in [(0, 0), (0, 100), (100, 100), (100, 0), (0, 0)]:
                co = Vector((self.HUD_x, self.HUD_y)) + offset + Vector(corner)
                self.profile_HUD_border_coords.append(co.resized(3))

            self.profile_HUD_edge_dir_coords.append((Vector((-size * 0.7, 0, 0)), Vector((self.HUD_x, self.HUD_y, 0)) + offset.resized(3) + Vector((0, size, 0))))
            self.profile_HUD_edge_dir_coords.append((Vector((0, -size * 0.7, 0)), Vector((self.HUD_x, self.HUD_y, 0)) + offset.resized(3) + Vector((size, 0, 0))))

    def get_pretty_alignment(self):
        default = self.highlighted[-1]
        if default == 'EDGE_DIR':
            title = "Edge Aligned"
            color = green

        elif default == 'FACE_DIR':
            title = "Face Aligned"
            color = red

        elif default == 'INBETWEEN_DIR':
            title = "Inbetween Aligned"
            color = blue

        elif default == 'CENTER_AIM_DIR':
            title = "Center Aim"
            color = yellow

        return title, color

    def get_active_edge(self):
        self.coords['active'] = []

        s = self.S_weld if self.is_weld else self.S

        s.get_hit(self.mouse_pos)

        if s.hit:
            edge_data = {'type': 'WELD' if self.is_weld else 'ORIG'}

            name = s.alternative[0].name if self.is_weld else self.active.name

            bm = s.cache.bmeshes[name]

            hit = self.mx.inverted_safe() @ s.hitlocation
            edge_data['hit'] = hit

            hitface = bm.faces[s.hitindex]

            edge = min([(e, (hit - intersect_point_line(hit, e.verts[0].co, e.verts[1].co)[0]).length, (hit - get_center_between_verts(*e.verts)).length) for e in hitface.edges if e.is_manifold and e.calc_length()], key=lambda x: (x[1] * x[2]) / x[0].calc_length())[0]
            edge_data['index'] = edge.index
            edge_data['coords'] = [self.mx @ v.co for v in edge.verts]

            self.drag = {'origin': s.hitlocation,
                         'normal': s.hitnormal}

            self.coords['active'] = edge_data['coords']
            return edge_data

    def has_active_edge_changed(self, debug=False):
        has_changed = False

        if self.active_edge and not self.prev_active:
            if debug:
                print(f"changed from None to Edge {self.active_edge['index']}")
            has_changed = True

        elif not self.active_edge and self.prev_active:
            if debug:
                print(f"changed from Edge {self.prev_active['index']} to None")
            has_changed = True

        elif self.active_edge and self.prev_active:

            if self.active_edge['type'] != self.prev_active['type']:
                if debug:
                    print("changed from one object to another")
                has_changed = True

            elif self.active_edge['index'] != self.prev_active['index']:
                if debug:
                    print(f"changed from Edge {self.prev_active['index']} to {self.active_edge['index']}")
                has_changed = True

            else:
                if debug:
                    print("nothing changed (both Edge)")

        else:
            if debug:
                print("nothing changed (both None)")

        if has_changed:
            self.prev_active = self.active_edge

        return has_changed

    def get_loop_selection(self):
        self.coords['loop'] = []

        if self.active_edge:

            s = self.S_weld if self.is_weld else self.S

            name = s.alternative[0].name if self.is_weld else self.active.name

            bm = s.cache.bmeshes[name]

            bm.edges.ensure_lookup_table()

            edge = bm.edges[self.active_edge['index']]

            edges = [edge]

            get_loop_edges(self.loop_angle, edges, edge, edge.verts[0], prefer_center_of_three=False, prefer_center_90_of_three=False, ensure_manifold=True)
            get_loop_edges(self.loop_angle, edges, edge, edge.verts[1], prefer_center_of_three=False, prefer_center_90_of_three=False, ensure_manifold=True)

            loop_selection = [{'type': 'WELD' if self.is_weld else 'ORIG',
                               'hit': average_locations([v.co.copy() for v in e.verts]),     # use the edge center as the local space hitlocation
                               'index': e.index,
                               'coords': [self.mx @ v.co for v in e.verts]} for e in edges]

            for edge_data in loop_selection:
                self.coords['loop'].extend(edge_data['coords'])

            return loop_selection
        return []

    def update_edge_selection(self, mode='ADD', debug=False):
        if self.active_edge:
            edge = self.active_edge
            indices = [e['index'] for e in self.selection['edges']]

            sel = self.selection['loop'] if self.selection['loop'] else [edge]

            if mode == 'ADD':
                for e in sel:
                    if e['index'] not in indices:
                        self.selection['edges'].append(e)

                        if debug:
                            print("added Edge", e['index'])

            elif mode == 'REMOVE':
                sel_indices = [e['index'] for e in sel]

                self.selection['edges'] = [e for e in self.selection['edges'] if e['index'] not in sel_indices]

                if debug:
                    for idx in sel_indices:
                        if idx in indices:
                            print("removed Edge", idx)

            if debug:
                print("selection:", [e['index'] for e in self.selection['edges']])

            self.coords['selected'] = []

            for e in self.selection['edges']:
                self.coords['selected'].extend(e['coords'])

    def transfer_edge_selection(self):
        self.coords['selected'] = []
        edge_selection = []

        if self.selection['edges']:
            indices = []

            s = self.S_weld if self.is_weld else self.S

            target = s.alternative[0] if self.is_weld else self.active

            name = target.name

            bm = s.cache.bmeshes[name]

            for e in self.selection['edges']:
                hit = e['hit']

                _, _, _, _, hitindex, _ = get_closest(self.dg, targets=[target], origin=self.mx @ hit, debug=False)

                if hitindex is not None:
                    hitface = bm.faces[hitindex]

                    edge = min([(e, (hit - intersect_point_line(hit, e.verts[0].co, e.verts[1].co)[0]).length, (hit - get_center_between_verts(*e.verts)).length) for e in hitface.edges if e.is_manifold and e.calc_length()], key=lambda x: (x[1] * x[2]) / x[0].calc_length())[0]

                    if edge.index not in indices:
                        indices.append(edge.index)

                        edge_selection.append({'type': 'WELD' if self.is_weld else 'ORIG',
                                               'hit': average_locations([v.co.copy() for v in edge.verts]),
                                               'index': edge.index,
                                               'coords': [self.mx @ v.co for v in edge.verts]})

            for e in edge_selection:
                self.coords['selected'].extend(e['coords'])

        return edge_selection

    def transfer_active_edge(self):
        self.coords['active'] = []

        if self.active_edge:

            edge_data = {'type': 'WELD',
                         'hit': self.active_edge['hit']}

            s = self.S_weld

            target = s.alternative[0]

            bm = s.cache.bmeshes[target.name]

            hit = self.active_edge['hit']

            _, _, hitlocation, hitnormal, hitindex, _ = get_closest(self.dg, targets=[target], origin=self.mx @ hit, debug=False)

            if hitindex is not None:
                hitface = bm.faces[hitindex]

                edge = min([(e, (hit - intersect_point_line(hit, e.verts[0].co, e.verts[1].co)[0]).length, (hit - get_center_between_verts(*e.verts)).length) for e in hitface.edges if e.is_manifold and e.calc_length()], key=lambda x: (x[1] * x[2]) / x[0].calc_length())[0]

                edge_data['index'] = edge.index
                edge_data['coords'] = [self.mx @ v.co for v in edge.verts]

                self.drag['origin'] = hitlocation
                self.drag['normal'] = hitnormal

                self.coords['active'] = edge_data['coords']

                return edge_data

    def get_total_selection(self, context, mode='HUD', debug=False):
        s = self.S_weld if self.is_weld else self.S

        name = s.alternative[0].name if self.is_weld else self.active.name

        bm = s.cache.bmeshes[name]
        bm.edges.ensure_lookup_table()

        total = ([self.active_edge] if self.active_edge else []) + self.selection['loop'] + self.selection['edges']

        sequences = []

        if total:
            edges = list({bm.edges[e['index']] for e in total})
            sequences = get_edges_as_vert_sequences(edges, debug=debug)

        if mode == 'HUD':
            hud_selection = {}
            hud_selection['active'] = self.active_edge['index'] if self.active_edge else None
            hud_selection['loop'] = [e['index'] for e in self.selection['loop'] if e['index'] != hud_selection['active']]
            hud_selection['edge'] = [e['index'] for e in self.selection['edges'] if e['index'] != hud_selection['active'] and e['index'] not in hud_selection['loop']]
            hud_selection['bevel_count'] = len(sequences)

            if debug:
                printd(hud_selection)

            return hud_selection

        elif mode == 'BMESH':

            bm_data = {'bmesh': bm,
                       'edges': edges,
                       'active':  None,
                       'sorted': []}

            if self.active_edge:
                bm_data['active'] = bm.edges[self.active_edge['index']]

            else:
                distances = []

                for e in edges:

                    center = self.mx @ average_locations([v.co for v in e.verts])
                    center2d = get_location_2d(context, center, default='OFF_SCREEN')
                    if is_on_screen(context, center2d):
                        distances.append((center2d - self.mouse_pos, e))

                bm_data['active'] = min(distances, key=lambda x: x[0])[1]

            self.coords['active'] = [self.mx @ v.co for v in bm_data['active'].verts]

            for verts, cyclic in sequences:
                coords = [self.mx @ v.co for v in verts]

                if cyclic:
                    coords.append(coords[0])

                bm_data['sorted'].append({'cyclic': cyclic, 'verts': verts})

                self.coords['sorted'].append(coords)

            if debug:
                printd(bm_data)

            return bm_data

    def get_bevel_width(self, context):
        view_origin, view_dir = get_view_origin_and_dir(context, self.mouse_pos)

        i = intersect_line_plane(view_origin, view_origin + view_dir, self.drag['origin'], self.drag['normal'])

        if i:

            intersect = self.mx.inverted_safe() @ i

            edge_intersect = intersect_point_line(intersect, *[v.co for v in self.bmesh['active'].verts])

            if edge_intersect:
                closest = edge_intersect[0]

                return (closest - intersect).length

    def analyse_geometry_conditions(self, debug=False):
        def is_first(v):
            idx = verts.index(v)
            return idx == 0

        def is_last(v):
            idx = verts.index(v)
            return idx == len(verts) - 1

        def get_prev_vert(v):
            idx = verts.index(v)

            if is_cyclic:
                return verts[(idx - 1) % len(verts)]
            else:
                if not is_first(v):
                    return verts[(idx - 1) % len(verts)]

        def get_next_vert(v):
            idx = verts.index(v)

            if is_cyclic:
                return verts[(idx + 1) % len(verts)]

            else:
                if not is_last(v):
                    return verts[(idx + 1) % len(verts)]

        bm = self.bmesh['bmesh']

        data = {}

        debug_coords = {'spine': [],
                        'left_perimeter': [],
                        'right_perimeter': [],
                        'dirs': [],
                        'left_dirs': [],
                        'right_dirs': [],
                        'left_face_dirs': [],
                        'right_face_dirs': [],
                        'left_edge_dirs': [],
                        'right_edge_dirs': [],
                        'left_center_aim_dirs': [],
                        'right_center_aim_dirs': [],
                        'left_inbetween_dirs': [],
                        'right_inbetween_dirs': [],
                        }

        for sidx, seq_data in enumerate(self.bmesh['sorted']):
            verts = seq_data['verts']
            is_cyclic = seq_data['cyclic']

            data[sidx] = {'cyclic': is_cyclic,
                          'convex': None,
                          'verts': verts,
                          'edges': [],
                          'vdata': {},
                          'left_gaps': [],
                          'right_gaps': []}

            for idx, v in enumerate(verts):

                debug_coords['spine'].append(self.mx @ v.co)

                vdata = {'prev_v': None,
                         'next_v': None,

                         'prev_e': None,
                         'next_e': None,

                         'loop': None,
                         'left_face': None,
                         'right_face': None,

                         'left_edge': None,
                         'right_edge': None,

                         'left_gap': None,
                         'right_gap': None,

                         'dir': None,                       # direction of the sequence at each vert
                         'left_dir': None,                  # simple cross product of dir and vert's edge based normalcross
                         'right_dir': None,                 # simple cross product of dir and vert's edge based normal

                         'shell_factor': 1,                 # init as one, update when prev and next verts are present

                         'left_face_dir': None,             # always present
                         'right_face_dir': None,            # always present

                         'left_edge_dir': None,             # only set with side edge present
                         'right_edge_dir': None,            # only set with side edge present

                         'left_center_aim_dir': None,       # only set for gap vert with directly opposing prev and next side edge dirs
                         'right_center_aim_dir': None,      # only set for gap vert with directly opposing prev and next side edge dirs

                         'left_inbetween_dir': None,        # set for all gap verts, that aren't center aimed
                         'right_inbetween_dir': None,       # set for all gap verts, that aren't center aimed

                         'left_options': ['FACE_DIR'],      # FACE_DIR, EDGE_DIR, CENTER_AIM_DIR or INBETWEEN_DIR - with FACE_DIR always present, and all others optional
                         'right_options': ['FACE_DIR'],     # FACE_DIR, EDGE_DIR, CENTER_AIM_DIR or INBETWEEN_DIR - with FACE_DIR always present, and all others optional

                         'left_default': 'FACE_DIR',
                         'right_default': 'FACE_DIR'}

                prev_v = get_prev_vert(v)
                next_v = get_next_vert(v)

                vdata['prev_v'] = prev_v
                vdata['next_v'] = next_v

                prev_e = bm.edges.get([prev_v, v]) if prev_v else None
                next_e = bm.edges.get([v, next_v]) if next_v else None

                vdata['prev_e'] = prev_e
                vdata['next_e'] = next_e

                if next_e:
                    data[sidx]['edges'].append(next_e)

                    if idx == 0:
                        data[sidx]['convex'] = is_edge_convex(next_e)

                    loop = [l for l in v.link_loops if l.edge == next_e][0]

                    vdata['loop'] = loop

                    vdata['left_face'] = loop.face
                    vdata['right_face'] = loop.link_loop_radial_next.face

                    for side in ['left', 'right']:
                        if side == 'left':
                            loop_face = loop.face

                            if loop_face.normal == Vector():
                                print(f"WARNING: encountered invalid side face at likely double vert {v.index}, falling back to face next to it!")
                                loop_face = loop.link_loop_next.link_loop_radial_next.face
                                self.weld_suggestion = True

                        else:
                            loop_face = loop.link_loop_radial_next.face

                            if loop_face.normal == Vector():
                                print(f"WARNING: encountered invalid side face at likely double vert {v.index}, falling back to face next to it!")
                                loop_face = loop.link_loop_radial_next.link_loop_next.link_loop_radial_next.face
                                self.weld_suggestion = True

                        vdata[f"{side}_face"] = loop_face

                else:
                    vdata['left_face'] = data[sidx]['vdata'][prev_v]['left_face']
                    vdata['right_face'] = data[sidx]['vdata'][prev_v]['right_face']

                if next_v and prev_v:
                    dir = ((next_v.co - v.co).normalized() + (v.co - prev_v.co).normalized()).normalized()

                    try:
                        angle = (next_v.co - v.co).normalized().angle((prev_v.co - v.co).normalized())

                    except:
                        print(f"WARNING: encountered likely double vert {v.index}!")
                        angle = radians(180)

                        self.weld_suggestion = True

                    vdata['shell_factor'] = 1 / sin(angle / 2)

                elif next_v:
                    dir = (next_v.co - v.co).normalized()

                elif prev_v:
                    dir = (v.co - prev_v.co).normalized()

                vdata['dir'] = dir

                debug_coords['dirs'].append((self.mx.to_3x3() @ dir * 0.1, self.mx @ v.co))

                data[sidx]['vdata'][v] = vdata

        def get_edge_based_normal(vdata):
            prev_edge = vdata['prev_e']
            next_edge = vdata['next_e']

            if prev_edge and next_edge:
                return (get_edge_normal(prev_edge) + get_edge_normal(next_edge)) / 2
            elif next_edge:
                return get_edge_normal(next_edge)
            else:
                return get_edge_normal(prev_edge)

        def should_edge_dir_default(v, side='left'):
            prev_v = vdata['prev_v']
            next_v = vdata['next_v']

            edge_dir = vdata[f'{side}_edge_dir']
            face_dir = vdata[f'{side}_face_dir']

            if (is_first(v) or is_last(v)) and abs(dir.dot(edge_dir)) > 0.9:
                return False

            if prev_v and abs(edge_dir.dot((prev_v.co - v.co).normalized())) > 0.9:
                return False

            if next_v and abs(edge_dir.dot((next_v.co - v.co).normalized())) > 0.9:
                return False

            if edge_dir.dot(face_dir) < 0:
                return False

            return True

        for sidx, seq_data in data.items():
            for idx, v in enumerate(seq_data['verts']):
                verts = seq_data['verts']
                vdata = seq_data['vdata'][v]
                loop = vdata['loop']
                dir = vdata['dir']

                normal = get_edge_based_normal(vdata)

                left_dir = normal.cross(vdata['dir'])
                right_dir = -normal.cross(vdata['dir'])

                vdata['left_dir'] = left_dir
                vdata['right_dir'] = right_dir

                debug_coords['left_dirs'].append((self.mx.to_3x3() @ left_dir * 0.1, self.mx @ v.co))
                debug_coords['right_dirs'].append((self.mx.to_3x3() @ right_dir * 0.1, self.mx @ v.co))

                left_normal = vdata['left_face'].normal
                right_normal = vdata['right_face'].normal

                i = intersect_line_plane(v.co + left_dir * 0.1, v.co + left_dir * 0.1 + left_normal, v.co, left_normal)
                left_face_dir = (i - v.co).normalized()
                vdata['left_face_dir'] = left_face_dir

                i = intersect_line_plane(v.co + right_dir * 0.1, v.co + right_dir * 0.1 + right_normal, v.co, right_normal)
                right_face_dir = (i - v.co).normalized()
                vdata['right_face_dir'] = right_face_dir

                debug_coords['left_face_dirs'].append((self.mx.to_3x3() @ left_face_dir * 0.2, self.mx @ v.co))
                debug_coords['right_face_dirs'].append((self.mx.to_3x3() @ right_face_dir * 0.2, self.mx @ v.co))

                if loop:
                    edge = loop.link_loop_prev.edge
                    left_edge = edge if edge not in seq_data['edges'] else None

                    edge = loop.link_loop_radial_next.link_loop_next.edge
                    right_edge = edge if edge not in seq_data['edges'] else None

                else:
                    loop = seq_data['vdata'][vdata['prev_v']]['loop']

                    edge = loop.link_loop_next.edge
                    left_edge = edge if edge not in seq_data['edges'] else None

                    edge = loop.link_loop_radial_next.link_loop_prev.edge
                    right_edge = edge if edge not in seq_data['edges'] else None

                vdata['left_edge'] = left_edge
                vdata['right_edge'] = right_edge

                if left_edge:
                    edge_dir = (left_edge.other_vert(v).co - v.co).normalized()

                    if edge_dir.length:
                        vdata['left_edge_dir'] = edge_dir

                        vdata['left_options'].append('EDGE_DIR')

                        if should_edge_dir_default(v, side='left'):
                            vdata['left_default'] = 'EDGE_DIR'
                        debug_coords['left_edge_dirs'].append((self.mx.to_3x3() @ edge_dir * 0.2, self.mx @ v.co))

                    else:
                        print(f"WARNING: encountered zero length edge dir at vert {v.index} likely due to double vert, ignoring!")

                        self.weld_suggestion = True

                if right_edge:
                    edge_dir = (right_edge.other_vert(v).co - v.co).normalized()

                    if edge_dir.length:
                        vdata['right_edge_dir'] = edge_dir

                        vdata['right_options'].append('EDGE_DIR')

                        if should_edge_dir_default(v, side='right'):
                            vdata['right_default'] = 'EDGE_DIR'
                        debug_coords['right_edge_dirs'].append((self.mx.to_3x3() @ edge_dir * 0.2, self.mx @ v.co))

                    else:
                        print(f"WARNING: encountered zero length edge dir at vert {v.index} likely due to double vert, ignoring!")

                        self.weld_suggestion = True

        def get_prev_side_edge_vert(v, side='left'):
            vert = v
            steps = 0
            distance = 0

            while prev := get_prev_vert(vert):
                steps += 1
                distance += (vert.co - prev.co).length

                if seq_data['vdata'][prev][f'{side}_edge']:
                    return prev, steps, distance

                elif prev == v:
                    return None, None, None

                vert = prev

            return None, None, None

        def get_next_side_edge_vert(v, side='left'):
            vert = v
            steps = 0
            distance = 0

            while next := get_next_vert(vert):
                steps += 1
                distance += (vert.co - next.co).length

                if seq_data['vdata'][next][f'{side}_edge']:
                    return next, steps, distance

                elif next == v:
                    return None, None, None

                vert = next

            return None, None, None

        for sidx, seq_data in data.items():
            verts = seq_data['verts']
            is_cyclic = seq_data['cyclic']

            for idx, v in enumerate(verts):
                vdata = seq_data['vdata'][v]

                if not vdata['left_edge']:
                    gap = {}

                    side_edge_vert, steps, distance = get_prev_side_edge_vert(v, side='left')

                    if side_edge_vert:
                        gap['prev_edge_dir'] = seq_data['vdata'][side_edge_vert]['left_edge_dir']
                        gap['prev_edge_dir_in_use'] = seq_data['vdata'][side_edge_vert]['left_default'] == 'EDGE_DIR'
                        gap['prev_steps'] = steps
                        gap['prev_distance'] = distance

                    side_edge_vert, steps, distance = get_next_side_edge_vert(v, side='left')

                    if side_edge_vert:
                        gap['next_edge_dir'] = seq_data['vdata'][side_edge_vert]['left_edge_dir']
                        gap['next_edge_dir_in_use'] = seq_data['vdata'][side_edge_vert]['left_default'] == 'EDGE_DIR'
                        gap['next_steps'] = steps
                        gap['next_distance'] = distance

                    vdata['left_gap'] = gap

                if not vdata['right_edge']:
                    gap = {}

                    side_edge_vert, steps, distance = get_prev_side_edge_vert(v, side='right')

                    if side_edge_vert:
                        gap['prev_edge_dir'] = seq_data['vdata'][side_edge_vert]['right_edge_dir']
                        gap['prev_edge_dir_in_use'] = seq_data['vdata'][side_edge_vert]['right_default'] == 'EDGE_DIR'
                        gap['prev_steps'] = steps
                        gap['prev_distance'] = distance

                    side_edge_vert, steps, distance = get_next_side_edge_vert(v, side='right')

                    if side_edge_vert:
                        gap['next_edge_dir'] = seq_data['vdata'][side_edge_vert]['right_edge_dir']
                        gap['next_edge_dir_in_use'] = seq_data['vdata'][side_edge_vert]['right_default'] == 'EDGE_DIR'
                        gap['next_steps'] = steps
                        gap['next_distance'] = distance

                    vdata['right_gap'] = gap

        def get_valid_prev_side_edge_dir(gap):
            if (prev_side_dir := gap.get('prev_edge_dir')) and gap.get('prev_edge_dir_in_use'):
                return prev_side_dir

        def get_valid_next_side_edge_dir(gap):
            if (next_side_dir := gap.get('next_edge_dir')) and gap.get('next_edge_dir_in_use'):
                return next_side_dir

        def get_distance_lerp_factor(gap):

            prev_distance = gap.get('prev_distance')
            next_distance = gap.get('next_distance')

            total_distance = prev_distance + next_distance

            return prev_distance / total_distance

        def get_step_distance_lerp_factor(gap, side='left'):
            prev_steps = gap.get('prev_steps')
            next_steps = gap.get('next_steps')

            if prev_steps == 1 and next_steps == 1:
                return 0.5

            elif prev_steps == 1:
                return 0

            elif next_steps == 1:
                return 1

            else:
                prev_distance = gap.get('prev_distance')
                next_distance = gap.get('next_distance')

                gap_first_distance = seq_data['vdata'][verts[(idx - (prev_steps - 1)) % len(verts)]][f"{side}_gap"]['prev_distance']
                gap_last_distance = seq_data['vdata'][verts[(idx + (next_steps - 1)) % len(verts)]][f"{side}_gap"]['next_distance']

                total_distance = prev_distance + next_distance - gap_first_distance - gap_last_distance

                return (prev_distance - gap_first_distance) / total_distance

        def should_inbetween_dir_default(v, side='left'):
            if self.active.HC.objtype == 'CYLINDER':
                return False

            else:
                prev_v = vdata['prev_v']
                next_v = vdata['next_v']

                inbetween_dir = vdata[f'{side}_inbetween_dir']
                face_dir = vdata[f'{side}_face_dir']

                if prev_v and abs(inbetween_dir.dot((prev_v.co - v.co).normalized())) > 0.9:
                    return False

                if next_v and abs(inbetween_dir.dot((next_v.co - v.co).normalized())) > 0.9:
                    return False

                if inbetween_dir.dot(face_dir) < 0:
                    return False

            return True

        for sidx, seq_data in data.items():
            verts = seq_data['verts']
            is_cyclic = seq_data['cyclic']

            left_gap_start = False
            right_gap_start = False

            for idx, v in enumerate(verts):
                vdata = seq_data['vdata'][v]

                if gap := vdata['left_gap']:

                    if left_gap_start:
                        seq_data['left_gaps'][-1].append(idx)

                    else:
                        left_gap_start = True
                        seq_data['left_gaps'].append([idx])

                    prev_side_dir = get_valid_prev_side_edge_dir(gap)
                    next_side_dir = get_valid_next_side_edge_dir(gap)

                    if prev_side_dir and next_side_dir and prev_side_dir.dot(next_side_dir) < -0.99:

                        prev_idx = (idx - gap.get('prev_steps')) % len(verts)
                        next_idx = (idx + gap.get('next_steps')) % len(verts)

                        center = (verts[prev_idx].co + verts[next_idx].co) / 2
                        center_aim_dir = (center - v.co).normalized()

                        vdata['left_center_aim_dir'] = center_aim_dir

                        vdata['left_options'].append('CENTER_AIM_DIR')

                        debug_coords['left_center_aim_dirs'].append((self.mx.to_3x3() @ center_aim_dir * 0.2, self.mx @ v.co))

                    elif prev_side_dir and next_side_dir:

                        factor = get_step_distance_lerp_factor(gap, side='left')

                        inbetween_dir = prev_side_dir.lerp(next_side_dir, factor).normalized()

                        vdata['left_inbetween_dir'] = inbetween_dir

                        vdata['left_options'].append('INBETWEEN_DIR')

                        if should_inbetween_dir_default(v, side='left'):
                            vdata['left_default'] = 'INBETWEEN_DIR'
                        debug_coords['left_inbetween_dirs'].append((self.mx.to_3x3() @ inbetween_dir * 0.2, self.mx @ v.co))

                    else:

                        pass

                elif left_gap_start:
                    left_gap_start = False

                if gap := vdata['right_gap']:

                    if right_gap_start:
                        seq_data['right_gaps'][-1].append(idx)

                    else:
                        right_gap_start = True
                        seq_data['right_gaps'].append([idx])

                    prev_side_dir = get_valid_prev_side_edge_dir(gap)
                    next_side_dir = get_valid_next_side_edge_dir(gap)

                    if prev_side_dir and next_side_dir and prev_side_dir.dot(next_side_dir) < -0.99:
                        prev_idx = (idx - gap.get('prev_steps')) % len(verts)
                        next_idx = (idx + gap.get('next_steps')) % len(verts)

                        center = (verts[prev_idx].co + verts[next_idx].co) / 2
                        center_aim_dir = (center - v.co).normalized()

                        vdata['right_center_aim_dir'] = center_aim_dir

                        vdata['right_options'].append('CENTER_AIM_DIR')

                        debug_coords['right_center_aim_dirs'].append((self.mx.to_3x3() @ center_aim_dir * 0.2, self.mx @ v.co))

                    elif prev_side_dir and next_side_dir:

                        factor = get_step_distance_lerp_factor(gap, side='right')

                        inbetween_dir = prev_side_dir.lerp(next_side_dir, factor).normalized()

                        vdata['right_inbetween_dir'] = inbetween_dir

                        vdata['right_options'].append('INBETWEEN_DIR')

                        if should_inbetween_dir_default(v, side='right'):
                            vdata['right_default'] = 'INBETWEEN_DIR'
                        debug_coords['right_inbetween_dirs'].append((self.mx.to_3x3() @ inbetween_dir * 0.2, self.mx @ v.co))

                elif right_gap_start:
                    right_gap_start = False

        def get_gaps(side='left'):
            gaps = seq_data[f'{side}_gaps']

            if is_cyclic and len(gaps) > 1:
                if 0 in gaps[0] and len(verts) - 1 in gaps[-1]:
                    return [gaps[0] + gaps[-1]] + gaps[1:-1]

            return gaps

        def is_inbetween_dir_default(idx, side='left'):
            v = verts[idx]
            vdata = seq_data['vdata'][v]

            return vdata[f'{side}_default'] == 'INBETWEEN_DIR'
        for sidx, seq_data in data.items():
            verts = seq_data['verts']
            is_cyclic = seq_data['cyclic']

            left_gaps = get_gaps(side='left')
            right_gaps = get_gaps(side='right')

            for indices in left_gaps:
                inbetween_dirs = [is_inbetween_dir_default(idx, side='left') for idx in indices]
                if any(inbetween_dirs) and not all(inbetween_dirs):
                    for idx, is_inbetween in zip(indices, inbetween_dirs):
                        if is_inbetween:
                            seq_data['vdata'][verts[idx]]['left_default'] = 'FACE_DIR'

            for indices in right_gaps:
                inbetween_dirs = [is_inbetween_dir_default(idx, side='right') for idx in indices]
                if any(inbetween_dirs) and not all(inbetween_dirs):
                    for idx, is_inbetween in zip(indices, inbetween_dirs):
                        if is_inbetween:
                            seq_data['vdata'][verts[idx]]['right_default'] = 'FACE_DIR'

        for sidx, seq_data in data.items():
            verts = seq_data['verts']

            for idx, v in enumerate(verts):
                vdata = seq_data['vdata'][v]

                for side in ['left', 'right']:
                    options = vdata[f'{side}_options']
                    default = vdata[f'{side}_default']
                    if self.has_inbetween_align is False:
                        if 'INBETWEEN_DIR' in options:
                            self.has_inbetween_align = True

                    if self.has_center_aim is False:
                        if 'CENTER_AIM_DIR' in options:
                            self.has_center_aim = True

                    if self.use_inbetween_align is False:
                        if default == 'INBETWEEN_DIR':
                            self.use_inbetween_align = True

                    if self.use_center_aim is False:
                        if default == 'CENTER_AIM_DIR':
                            self.use_center_aim = True

        if debug:
            printd(data)

        self.coords['debug'] = debug_coords

        return data

    def set_global_inbetween_align(self):
        for sidx, seq_data in self.data.items():
            verts = seq_data['verts']

            for idx, v in enumerate(verts):
                vdata = seq_data['vdata'][v]

                for side in ['left', 'right']:
                    if 'INBETWEEN_DIR' in vdata[f'{side}_options']:
                        vdata[f'{side}_default'] = 'INBETWEEN_DIR' if self.use_inbetween_align else 'FACE_DIR'
    def set_global_center_aim(self):
        for sidx, seq_data in self.data.items():
            verts = seq_data['verts']

            for idx, v in enumerate(verts):
                vdata = seq_data['vdata'][v]

                for side in ['left', 'right']:
                    if 'CENTER_AIM_DIR' in vdata[f'{side}_options']:
                        vdata[f'{side}_default'] = 'CENTER_AIM_DIR' if self.use_center_aim else 'FACE_DIR'

    def create_base_cutter_data(self, gizmo_data=False, debug=False):
        base = {}

        self.coords['sweep'] = []                   # coords for drawing all sweeps (and rails) in one go, includes indices too
        self.coords['individual_sweeps'] = {}       # coords for drawing only individual sweeps (highlighted), addressing them through sidx, idx, side keys

        debug_coords = self.coords['debug']
        debug_coords['sweep_dirs'] = []
        debug_coords['sweep_coords'] = []

        def get_sweep_dir(v, side='left'):
            vdata = seq_data['vdata'][v]

            default = self.gizmo_data['sweeps'][sidx]['gizmos'][idx][side]['default'] if gizmo_data else vdata[f'{side}_default']
            if default == 'FACE_DIR':
                sweep_dir = vdata[f'{side}_face_dir']
                color = red

            elif default == 'EDGE_DIR':
                sweep_dir = vdata[f'{side}_edge_dir']
                color = green

            elif default == 'CENTER_AIM_DIR':
                sweep_dir = vdata[f'{side}_center_aim_dir']
                color = yellow

            elif default == 'INBETWEEN_DIR':
                sweep_dir = vdata[f'{side}_inbetween_dir']
                color = blue

            debug_coords['sweep_dirs'].append((self.mx.to_3x3() @ sweep_dir * 0.2, self.mx @ v.co, color))

            return sweep_dir

        def get_sweep_co(v, side='left'):
            vdata = seq_data['vdata'][v]

            default = self.gizmo_data['sweeps'][sidx]['gizmos'][idx][side]['default'] if gizmo_data else vdata[f'{side}_default']
            face_dir = vdata[f'{side}_face_dir']
            sweep_dir = get_sweep_dir(v, side=side)   # run it either way to ensure the debug dirs get populated
            shell_factor = vdata['shell_factor']

            if default == 'FACE_DIR':
                co = v.co + face_dir * self.width * shell_factor

                debug_coords['sweep_coords'].append(self.mx @ co)

                return co

            else:
                co1 = v.co + face_dir * self.width * shell_factor
                co2 = co1 + vdata['dir']
                co3 = v.co
                co4 = co3 + sweep_dir

                i = intersect_line_line(co1, co2, co3, co4)

                debug_coords['sweep_coords'].append(self.mx @ i[1])

                return i[1]

        def get_extend_amount():
            if gizmo_data:
                amount = self.gizmo_data['sweeps'][sidx]['gizmos'][idx]['extend']['extend']

            else:
                amount = 0.02 * self.width if is_convex else 0

            return amount

        for sidx, seq_data in self.data.items():
            verts = seq_data['verts']
            is_cyclic = seq_data['cyclic']
            is_convex = seq_data['convex']

            base[sidx] = {'cyclic': is_cyclic,
                          'convex': is_convex,
                          'coords': []}

            coords = []
            indices = []

            self.coords['individual_sweeps'][sidx] = {}

            for idx, v in enumerate(seq_data['verts']):
                vdata = seq_data['vdata'][v]

                if debug:
                    print(idx, v.index)
                    print(" left options:", vdata['left_default'], "of", vdata['left_options'])
                    print(" right options:", vdata['right_default'], "of", vdata['right_options'])
                center_co = v.co.copy()
                left_co = get_sweep_co(v, side='left')
                right_co = get_sweep_co(v, side='right')

                if not is_cyclic:
                    if idx == 0:
                        amount = get_extend_amount()

                        center_co = center_co - vdata['dir'] * amount
                        left_co = left_co - vdata['dir'] * amount
                        right_co = right_co - vdata['dir'] * amount

                    elif idx == len(seq_data['verts']) -1:
                        amount = get_extend_amount()

                        center_co = center_co + vdata['dir'] * amount
                        left_co = left_co + vdata['dir'] * amount
                        right_co = right_co + vdata['dir'] * amount

                base[sidx]['coords'].append((left_co, center_co, right_co))

                coords.extend([self.mx @ co for co in [left_co, center_co, right_co]])

                if idx < len(verts):

                    indices.append((idx * 3, idx * 3 + 1))
                    indices.append((idx * 3 + 1, idx * 3 + 2))

                    if idx < len(verts) - 1:
                        indices.append((idx * 3, (idx + 1) * 3))
                        indices.append((idx * 3 + 2, (idx + 1) * 3 + 2))

                    elif is_cyclic:
                        indices.append((idx * 3, 0))
                        indices.append((idx * 3 + 2, 2))

                self.coords['individual_sweeps'][sidx][idx] = {'left': (self.mx @ center_co, self.mx @ left_co),
                                                               'right': (self.mx @ center_co, self.mx @ right_co)}

            self.coords['sweep'].append((coords, indices))

        if debug:
            printd(base)

        return base

    def create_base_cutter(self, context, init=False, edit_mode=False):
        for sidx, seq_data in self.base.items():
            is_cyclic = seq_data['cyclic']
            coords = seq_data['coords']

            if init:
                cutter = bpy.data.objects.new(name="Hyper Bevel", object_data=bpy.data.meshes.new(name="Hyper Bevel"))
                context.scene.collection.objects.link(cutter)
                cutter.matrix_world = self.mx

                cutter.display_type = 'WIRE'
                hide_render(cutter, True)

                if not edit_mode:
                    cutter.hide_set(True)

                parent(cutter, self.active)

                cutter.HC.ishyper = True
                cutter.HC.objtype = 'CUBE'
                cutter.HC.geometry_gizmos_show = True
                cutter.HC.ishyperbevel = True

                self.hyper_bevels[sidx] = {'obj': cutter,
                                           'bevel': None,
                                           'boolean': None}

            else:
                cutter = self.hyper_bevels[sidx]['obj']

            bm = bmesh.new()
            bm.from_mesh(cutter.data)

            if not init:
                bm.clear()

            edge_glayer, face_glayer = ensure_gizmo_layers(bm)

            verts = []
            faces = []
            center_edges = []

            for idx, sweep in enumerate(coords):
                tripple = []

                for co in sweep:
                    tripple.append(bm.verts.new(co))

                verts.append(tripple)

                if idx > 0:
                    faces.append(bm.faces.new([verts[idx - 1][0], verts[idx - 1][1], tripple[1], tripple[0]]))
                    faces.append(bm.faces.new([verts[idx - 1][1], verts[idx - 1][2], tripple[2], tripple[1]]))

                    center_edges.append(bm.edges.get([verts[idx - 1][1], tripple[1]]))

                if is_cyclic and idx == len(coords) - 1:
                    bm.faces.new([tripple[0], tripple[1], verts[0][1], verts[0][0]])
                    bm.faces.new([tripple[1], tripple[2], verts[0][2], verts[0][1]])

                    center_edges.append(bm.edges.get([tripple[1], verts[0][1]]))

            for e in center_edges:
                e[edge_glayer] = 1

            if self.is_active_smooth:
                for f in faces:
                    f.smooth = True

            bm.to_mesh(cutter.data)
            bm.free()

        if edit_mode:
            bpy.ops.object.select_all(action='DESELECT')

            mods = list(self.active.modifiers)
            remove_booleans = []

            for data in self.hyper_bevels.values():
                cutter = data['obj']

                bevel = data['bevel']
                boolean = data['boolean']

                if boolean:
                    boolean.show_viewport = False

                    remove_booleans.append(boolean)

                    cutter.HC['hyperbevel_modname'] = boolean.name
                    cutter.HC['hyperbevel_index'] = mods.index(boolean)

                if bevel:
                    cutter.HC['hyperbevel_segments'] = bevel.segments

                    if self.is_custom_profile:
                        profile = get_bevel_profile_as_dict(bevel)
                        cutter.HC['hyperbevel_profile'] = profile

                cutter.hide_set(False)
                cutter.modifiers.clear()
                cutter.vertex_groups.clear()

                context.view_layer.objects.active = cutter
                cutter.select_set(True)

                cutter.HC.isfinishedhyperbevel = False

            for mod in remove_booleans:
                remove_mod(mod)

            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')

            if not active_tool_is_hypercursor(context):
                bpy.ops.wm.tool_set_by_id(name="machin3.tool_hyper_cursor")

    def recreate_base_cutter(self, cutter):
        if bevel := cutter.modifiers.get('Edge Bevel'):
            cutter.HC['hyperbevel_segments'] = bevel.segments

            if bevel.profile_type == 'CUSTOM':
                profile = get_bevel_profile_as_dict(bevel)
                cutter.HC['hyperbevel_profile'] = profile

        cutter.modifiers.clear()
        cutter.vertex_groups.clear()

        is_convex = True

        if host := cutter.parent:
            booleans = [mod for mod in host.modifiers if mod.type == 'BOOLEAN' and mod.object == cutter]

            if booleans:
                boolean = booleans[0]

                if boolean.operation == 'UNION':
                    is_convex = False

                cutter.HC['hyperbevel_modname'] = boolean.name
                cutter.HC['hyperbevel_index'] = list(host.modifiers).index(boolean)

                remove_mod(boolean)

        cutter.HC.isfinishedhyperbevel = False

        bm = bmesh.from_edit_mesh(cutter.data)
        bm.normal_update()
        bm.verts.ensure_lookup_table()

        edge_glayer, face_glayer = ensure_gizmo_layers(bm)

        center_edges = [e for e in bm.edges if e[edge_glayer] == 1]

        center_faces = [f for e in center_edges for f in e.link_faces]

        if not len(center_faces) == 2 * len(center_edges):
            msg = ["Invalid cutter geo, insufficient center faces"]
            print(f"WARNING: {msg}")
            return msg

        remove = [f for f in bm.faces if f not in center_faces]

        if remove:
            bmesh.ops.delete(bm, geom=remove, context='FACES')

        if is_convex:
            bmesh.ops.reverse_faces(bm, faces=center_faces)

        sequences = get_edges_as_vert_sequences(center_edges)

        if len(sequences) != 1:
            msg = ["Invalid cutter geo, multiple edge-gizmo loops detected"]
            print(f"WARNING: {msg}")
            return msg

        bmesh.update_edit_mesh(cutter.data)

    def create_finished_cutter(self, context, init=False, handler_invocation=False, profile=None):
        if handler_invocation:

            hyperbevels = {obj for obj in context.selected_objects + [context.active_object] if obj and obj.HC.ishyperbevel and not obj.HC.isfinishedhyperbevel}

            hyper_bevels = {}

            for idx, obj in enumerate(hyperbevels):
                data = {'obj': obj,
                        'bevel': None,
                        'boolean': None}

                hyper_bevels[idx] = data

        else:
            hyper_bevels = self.hyper_bevels

        host = None
        mods = []

        for sidx, data in hyper_bevels.items():
            cutter = data['obj']
            bevel = data['bevel']
            boolean = data['boolean']

            bm = bmesh.new()
            bm.from_mesh(cutter.data)
            bm.normal_update()

            edge_glayer, face_glayer = ensure_gizmo_layers(bm)

            faces = [f for f in bm.faces]

            if not all(len(f.verts) == 4 for f in faces):
                msg = ["Invalid base cutter geo, non-quad faces detected"]
                print(f"WARNING: {msg[0]}")
                return msg

            center_edges = [e for e in bm.edges if e[edge_glayer] == 1]

            if not center_edges:
                msg = ["Invalid base cutter geo, no center edge(s) found",
                       "The base cutter geo needs to feature 2 strips of quad faces, with the center edges marked as Edge Gizmos"]
                print(f"WARNING: {msg[0]}")
                return msg

            sequences = get_edges_as_vert_sequences(center_edges)

            if len(sequences) != 1:
                msg = ["Invalid base cutter geo, multiple center edge loops detected"]
                print(f"WARNING: {msg[0]}")
                return msg

            center_faces = [f for e in center_edges for f in e.link_faces]

            if len(center_faces) != len(faces) or any(len(e.link_faces) != 2 for e in center_edges):
                msg = ["Invalid base cutter geo, face count mismatch"
                       "Each center edge needs to have exactly 2 side faces, and nothing else"]
                return msg

            verts, is_cyclic = sequences[0]

            loop = [l for l in verts[0].link_loops if l.edge in center_edges][0]

            first_edge = loop.edge
            is_convex = is_edge_convex(first_edge)

            if handler_invocation:
                dir = (verts[1].co - verts[0].co).normalized()

                left_dir = -dir.cross(loop.face.normal)

                rail_edge = loop.link_loop_prev.link_loop_prev.edge
                i = intersect_line_line(verts[0].co, verts[0].co + left_dir, rail_edge.verts[0].co, rail_edge.verts[1].co)

                width = (i[1] - verts[0].co).length

            else:
                width = self.width

            sign = 1 if is_convex else -1

            ret = bmesh.ops.extrude_face_region(bm, geom=faces)
            top_faces = [el for el in ret['geom'] if isinstance(el, bmesh.types.BMFace)]
            top_verts = {v for f in top_faces for v in f.verts}

            for v in top_verts:
                normal = average_normals([f.normal for f in v.link_faces if f in top_faces])
                v.co = v.co + normal * v.calc_shell_factor() * sign * 0.1 * width

            top_center_edges = [e for f in top_faces for e in f.edges if e[edge_glayer] == 1]

            for e in top_center_edges:
                e[edge_glayer] = 0

            if not is_cyclic:
                first_center_vert = verts[0]
                last_center_vert = verts[-1]

                first_cap_faces = [f for f in first_center_vert.link_faces if f not in faces]
                last_cap_faces = [f for f in last_center_vert.link_faces if f not in faces]

                geo = bmesh.ops.dissolve_faces(bm, faces=first_cap_faces + last_cap_faces)

                for f in geo['region']:
                    f[face_glayer] = 1

                    center_vert = first_center_vert if first_center_vert in f.verts else last_center_vert

                    loop = [l for l in center_vert.link_loops if l.face == f][0]

                    sweep_vert1 = loop.link_loop_next.vert
                    sweep_vert2 = loop.link_loop_prev.vert

                    sweep_dir1 = (sweep_vert1.co - center_vert.co).normalized()
                    sweep_dir2 = (sweep_vert2.co - center_vert.co).normalized()

                    cap_dir = sweep_dir2.cross(sweep_dir1).normalized()

                    center_top_vert = loop.link_loop_next.link_loop_next.link_loop_next.vert

                    extrude_dir = (center_top_vert.co - center_vert.co).normalized()

                    dot = extrude_dir.dot(cap_dir)

                    if abs(dot) > 0.9:
                        pass

                    else:

                        flatten_verts = [v for v in f.verts if v not in [center_vert, sweep_vert1, sweep_vert2]]

                        for v in flatten_verts:
                            rail_edges = [e for e in v.link_edges if e not in f.edges]
                            other_vert = rail_edges[0].other_vert(v)

                            i = intersect_line_plane(v.co, other_vert.co, center_vert.co, cap_dir)

                            if i:
                                v.co = i

            if not is_convex:
                bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

            vgroup = cutter.vertex_groups.get("Edge Bevel")

            if not vgroup:
                vgroup = cutter.vertex_groups.new(name="Edge Bevel")

            vert_ids = [v.index for v in verts]

            bm.to_mesh(cutter.data)
            bm.free()

            vgroup.add(vert_ids, 1, "ADD")

            if bevel is None:
                bevel = add_bevel(cutter, name="Edge Bevel", width=0, limit_method='VGROUP', vertex_group=vgroup.name)
                bevel.offset_type = 'PERCENT'
                bevel.width_pct = 100
                bevel.profile = 0.5
                bevel.loop_slide = True

                data['bevel'] = bevel

                if segments := cutter.HC.get('hyperbevel_segments'):
                    bevel.segments = segments

                    del cutter.HC['hyperbevel_segments']

                else:
                    bevel.segments = 1 if self and self.chamfer else self.segments + 1 if self else 13

                if handler_invocation and (profile := cutter.HC.get('hyperbevel_profile')):
                    set_bevel_profile_from_dict(bevel, profile)

                    del cutter.HC['hyperbevel_profile']

                elif profile:
                    set_bevel_profile_from_dict(bevel, profile)

                _weld = add_weld(cutter, name="Weld", distance=0.000001, mode='CONNECTED')

            if host := cutter.parent:

                if boolean is None:
                    boolean = add_boolean(host, operator=cutter, method='DIFFERENCE' if is_convex else 'UNION', solver='MANIFOLD' if bpy.app.version >= (4, 5, 0) else 'EXACT')
                    boolean.name = get_new_mod_name(host, 'HYPERBEVEL')

                    data['boolean'] = boolean

                    mods.append(boolean)

            cutter.HC.isfinishedhyperbevel = True

        if init and host and len(host.modifiers) > len(hyper_bevels):
            if not handler_invocation:

                idx = sort_mod_after_split(mods[0])

                if idx is not None:

                    for mod in mods[1:]:
                        idx += 1
                        move_mod(mod, idx)
                        mod.name = f"+ {mod.name}"

                else:
                    sort_modifiers(host)

                if self:                     # should be given when not invoking from handler, but just to make sure
                    self.can_move = True

            if len(mods) > 1:
                mods[0].is_active = True

            if handler_invocation:
                for mod in mods:
                    cutter = mod.object

                    if modname := cutter.HC.get('hyperbevel_modname'):
                        mod.name = modname

                        del cutter.HC['hyperbevel_modname']

                    idx = cutter.HC.get('hyperbevel_index')

                    if idx is not None:
                        if idx < len(host.modifiers) - 1:
                            move_mod(mod, idx)

                        del cutter.HC['hyperbevel_index']

    def get_mods_and_indices(self, debug=False):
        mods = list(self.active.modifiers)
        mods_len = len(mods)

        mod = self.hyper_bevels[0]['boolean']
        current_idx = mods.index(mod)

        if debug:
            print("current:", current_idx, "of", mods_len - 1)

        return mods, mods_len, current_idx

    def ensure_prefix(self, direction='UP'):
        mods, mods_len, current_idx = self.get_mods_and_indices(debug=False)
        bevel_count = len(self.hyper_bevels)

        first_mod = mods[current_idx]
        last_mod = mods[current_idx + bevel_count - 1]

        if direction == 'UP':
            prefix = '-'

        elif direction == 'DOWN':
            prefix = '+'

        prev_mod = get_previous_mod(first_mod)
        next_mod = get_next_mod(last_mod)

        prev_index = get_prefix_from_mod(prev_mod) if prev_mod else None
        next_index = get_prefix_from_mod(next_mod) if next_mod else None

        if direction == 'UP' and next_index == '+':
            prefix = '+'

        elif direction == 'DOWN' and prev_index == '-':
            prefix = '-'

        for i in range(bevel_count):
            mod = mods[current_idx + i]
            mod.name = f"{prefix} {get_mod_base_name(mod)}"

class AdjustHyperBevelSweep(bpy.types.Operator, HyperBevelGizmoManager):
    bl_idname = "machin3.adjust_hyper_bevel_sweep"
    bl_label = "MACHIN3: Adjust Hyper Bevel Sweep"
    bl_description = "Adjust Sweep Alignment"
    bl_options = {'INTERNAL'}

    sidx: IntProperty()
    idx: IntProperty()
    side: StringProperty(default='left')
    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            mng = HyperBevelGizmoManager
            return mng.gizmo_data and mng.gizmo_props.get('show')

    def draw(self, context):
        layout = self.layout
        _column = layout.column(align=True)

    def invoke(self, context, event):
        gizmos = self.gizmo_data['sweeps'][self.sidx]['gizmos']

        default = gizmos[self.idx][self.side]['default']
        options = gizmos[self.idx][self.side]['options']
        new_default = step_list(default, options, step=1, loop=True)
        if event.shift and self.gizmo_highlighted_neighbours:
            indices = self.gizmo_highlighted_neighbours

        else:
            indices = [self.idx]

        for idx in indices:
            gizmos[idx][self.side]['default'] = new_default
        self.gizmo_props['push_update'] = ('SWEEPS', new_default)
        return {'FINISHED'}

def draw_adjust_hyper_bevel_width_status(op):
    def draw(self, context):
        layout = self.layout

        row = layout.row(align=True)

        row.label(text="Adjust Hyper Bevel Width")

        draw_status_item(row, key='LMB', text="Finish")
        draw_status_item(row, key='RMB', text="Cancel")

        row.separator(factor=10)

        draw_status_item(row, key='MOVE', text="Adjust Width", prop=dynamic_format(op.width, decimal_offset=2))

    return draw

class AdjustHyperBevelWidth(bpy.types.Operator, HyperBevelGizmoManager):
    bl_idname = "machin3.adjust_hyper_bevel_width"
    bl_label = "MACHIN3: Adjust Hyper Bevel Width"
    bl_description = "Adjust Width"
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            mng = HyperBevelGizmoManager
            return mng.gizmo_data and mng.gizmo_props.get('show')

    def draw_VIEW3D(self, context):
        if context.area == self.area:
            draw_point(self.init_loc, size=4, color=yellow)

            if self.coords:
                draw_line(self.coords, color=yellow, width=1, alpha=0.5)

    def modal(self, context, event):
        if ignore_events(event):
            return {'RUNNING_MODAL'}

        context.area.tag_redraw()

        if event.type == 'MOUSEMOVE':
            get_mouse_pos(self, context, event)

            co = self.get_width_dir_intersection(context, self.mouse_pos)

            if co:
                width_dir = (co - self.width_offset_vector - self.data['edge_center'])

                if width_dir.normalized().dot(self.width_dir) > 0:
                    self.loc = co - self.width_offset_vector

                    self.coords = [self.init_loc, self.loc]

                    self.width = (self.mx.inverted_safe().to_3x3() @ (self.loc - self.data['edge_center'])).length

                    self.gizmo_props['push_update'] = ('WIDTH', self.width)

                    force_ui_update(context)

                    return {'PASS_THROUGH'}

        elif event.type in ['LEFTMOUSE', 'SPACE']:
            self.finish(context)

            for sidx, seq_data in self.gizmo_data['sweeps'].items():
                gizmos = seq_data['gizmos']

                for idx, data in gizmos.items():
                    for side in ['left', 'right']:
                        co = data[side]['co']

                        sweep_dir = data[side]['sweep_dir'] * self.width * self.gizmo_props['sweep_distance']
                        extend_dir = data['extend']['extend_dir'] * data['extend']['extend'] if data.get('extend') else Vector()

                        data[side]['sweep_co'] =  self.mx @ (co + sweep_dir + extend_dir)

            self.data['width'] = self.width
            self.data['matrix'] = Matrix.LocRotScale(self.loc, self.data['rot'], Vector((1, 1, 1)))
            self.data['loc'] = self.loc

            return {'FINISHED'}

        elif event.type in ['RIGHTMOUSE', 'ESC'] and event.value == 'PRESS':
            self.finish(context)

            self.gizmo_props['push_update'] = ('WIDTH', self.init_width)
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def finish(self, context):
        finish_modal_handlers(self)

        finish_status(self)

    def invoke(self, context, event):
        self.data = self.gizmo_data['width']

        self.mx = self.gizmo_props['matrix']

        self.init_width = self.data['width']

        self.init_loc = self.data['loc']
        self.width_dir = (self.mx.to_3x3() @ self.data['width_dir']).normalized()

        self.width = self.init_width
        self.loc = self.init_loc

        self.coords = []

        get_mouse_pos(self, context, event, init_offset=True)

        offset_co = self.get_width_dir_intersection(context, self.mouse_pos)

        if offset_co:

            self.width_offset_vector = offset_co - self.init_loc

            init_status(self, context, func=draw_adjust_hyper_bevel_width_status(self))

            force_ui_update(context)

            init_modal_handlers(self, context, view3d=True)
            return {'RUNNING_MODAL'}
        return {'CANCELLED'}

    def get_width_dir_intersection(self, context, mouse_pos):
        view_origin, view_dir = get_view_origin_and_dir(context, mouse_pos)

        i = intersect_line_line(self.init_loc, self.init_loc + self.width_dir, view_origin, view_origin + view_dir)

        if i:
            return i[0]

def draw_adjust_hyper_bevel_extend_status(op):
    def draw(self, context):
        layout = self.layout

        row = layout.row(align=True)

        row.label(text="Adjust Hyper Bevel Extend")

        draw_status_item(row, key='LMB', text="Finish")
        draw_status_item(row, key='RMB', text="Cancel")

        row.separator(factor=10)

        draw_status_item(row, key='MOVE', text="Adjust Extend", prop=dynamic_format(op.extend, decimal_offset=2))

        draw_status_item(row, active=op.is_shift, key='SHIFT', text="Both Ends", gap=2)

        draw_status_item(row, key='R', text="Reset to 0", gap=2)

    return draw

class AdjustHyperBevelExtend(bpy.types.Operator, HyperBevelGizmoManager):
    bl_idname = "machin3.adjust_hyper_bevel_extend"
    bl_label = "MACHIN3: Adjust Hyper Bevel Extend"
    bl_description = "Adjust Extend"
    bl_options = {'INTERNAL'}

    sidx: IntProperty()
    idx: IntProperty()

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            mng = HyperBevelGizmoManager
            return mng.gizmo_data and mng.gizmo_props.get('show')

    def draw_VIEW3D(self, context):
        if context.area == self.area:
            draw_point(self.init_loc, size=4, color=yellow)

            if self.coords:
                draw_line(self.coords, color=yellow, width=1, alpha=0.5)

    def modal(self, context, event):
        if ignore_events(event):
            return {'RUNNING_MODAL'}

        context.area.tag_redraw()

        update_mod_keys(self, event)

        if event.type == 'MOUSEMOVE':
            get_mouse_pos(self, context, event)

            co = self.get_extend_dir_intersection(context, self.mouse_pos)

            if co:

                extend_dir = (co - self.extend_offset_vector - self.end_co).normalized()
                sign = round(extend_dir.dot(self.extend_dir))

                self.loc = co - self.extend_offset_vector

                self.coords = [self.init_loc, self.loc]

                self.extend = sign * (self.mx.inverted_safe().to_3x3() @ (self.loc - self.end_co)).length

                self.data['extend'] = self.extend

                if event.shift:
                    self.other_data['extend'] = self.extend

                elif self.other_data['extend'] != self.other_init_extend:
                    self.other_data['extend'] = self.other_init_extend

                self.gizmo_props['push_update'] = ('EXTEND', None)

                force_ui_update(context)

                return {'PASS_THROUGH'}

        elif event.type == 'R' and event.value == 'PRESS':
            self.finish(context)

            indices = [self.idx, len(self.gizmos) - 1 if self.idx == 0 else 0] if self.is_shift else [self.idx]

            for idx in indices:
                data = self.gizmo_data['sweeps'][self.sidx]['gizmos'][idx]

                for side in ['left', 'right']:
                    co = data[side]['co']

                    sweep_dir = data[side]['sweep_dir'] * self.gizmo_data['width']['width'] * self.gizmo_props['sweep_distance']
                    data[side]['sweep_co'] =  self.mx @ (co + sweep_dir)

            self.data['extend'] = 0
            self.data['matrix'] = Matrix.LocRotScale(self.end_co, self.data['rot'], Vector((1, 1, 1)))
            self.data['loc'] = self.end_co

            if self.is_shift:
                self.other_data['extend'] = 0
                self.other_data['matrix'] = Matrix.LocRotScale(self.other_end_co, self.other_data['rot'], Vector((1, 1, 1)))
                self.other_data['loc'] = self.other_end_co

            self.gizmo_props['push_update'] = ('EXTEND', None)

            return {'FINISHED'}

        elif event.type in ['LEFTMOUSE', 'SPACE']:
            self.finish(context)

            indices = [self.idx, len(self.gizmos) - 1 if self.idx == 0 else 0] if self.is_shift else [self.idx]

            for idx in indices:
                data = self.gizmo_data['sweeps'][self.sidx]['gizmos'][idx]

                for side in ['left', 'right']:
                    co = data[side]['co']

                    sweep_dir = data[side]['sweep_dir'] * self.gizmo_data['width']['width'] * self.gizmo_props['sweep_distance']
                    extend_dir = data['extend']['extend_dir'] * self.extend

                    data[side]['sweep_co'] =  self.mx @ (co + sweep_dir + extend_dir)

            self.data['extend'] = self.extend
            self.data['matrix'] = Matrix.LocRotScale(self.loc, self.data['rot'], Vector((1, 1, 1)))
            self.data['loc'] = self.loc

            if self.is_shift:
                other_loc = self.mx @ (self.other_data['co'] + self.other_data['extend_dir'] * self.extend)

                self.other_data['extend'] = self.extend
                self.other_data['matrix'] = Matrix.LocRotScale(other_loc, self.other_data['rot'], Vector((1, 1, 1)))
                self.other_data['loc'] = other_loc

            return {'FINISHED'}

        elif event.type in ['RIGHTMOUSE', 'ESC'] and event.value == 'PRESS':
            self.finish(context)

            self.data['extend'] = self.init_extend

            self.gizmo_props['push_update'] = ('EXTEND', None)
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def finish(self, context):
        finish_modal_handlers(self)

        finish_status(self)

    def invoke(self, context, event):
        self.gizmos = self.gizmo_data['sweeps'][self.sidx]['gizmos']

        self.data = self.gizmos[self.idx]['extend']
        self.other_data = self.gizmos[len(self.gizmos) - 1 if self.idx == 0 else 0]['extend']

        self.mx = self.gizmo_props['matrix']

        self.end_co = self.mx @ self.data['co']
        self.other_end_co = self.mx @ self.other_data['co']

        self.init_extend = self.data['extend']
        self.other_init_extend = self.other_data['extend']

        self.init_loc = self.data['loc']
        self.extend_dir = (self.mx.to_3x3() @ self.data['extend_dir']).normalized()

        self.extend = self.init_extend
        self.loc = self.init_loc

        update_mod_keys(self)

        self.coords = []

        get_mouse_pos(self, context, event, init_offset=True)

        offset_co = self.get_extend_dir_intersection(context, self.mouse_pos)

        if offset_co:

            self.extend_offset_vector = offset_co - self.init_loc

            init_status(self, context, func=draw_adjust_hyper_bevel_extend_status(self))

            force_ui_update(context)

            init_modal_handlers(self, context, view3d=True)
            return {'RUNNING_MODAL'}
        return {'CANCELLED'}

    def get_extend_dir_intersection(self, context, mouse_pos):
        view_origin, view_dir = get_view_origin_and_dir(context, mouse_pos)

        i = intersect_line_line(self.init_loc, self.init_loc + self.extend_dir, view_origin, view_origin + view_dir)

        if i:
            return i[0]

def draw_hyper_bevel_old(op):
    def draw(self, context):
        layout = self.layout

        row = layout.row(align=True)
        row.label(text='Hyper Bevel')

        row.label(text="", icon='MOUSE_MOVE')
        row.label(text="Drag out Bevel Width" if op.is_dragging else "Select Edge")

        row.label(text="", icon='MOUSE_LMB')
        row.label(text="Finish")

        if context.window_manager.keyconfigs.active.name.startswith('blender'):
            row.label(text="", icon='MOUSE_MMB')
            row.label(text="Viewport")

        row.label(text="", icon='MOUSE_RMB')
        row.label(text="Cancel")

        row.separator(factor=10)

        if op.is_dragging:

            row.label(text="", icon='EVENT_C')
            row.label(text=f"Chamfer: {op.modal_chamfer}")

            if not op.modal_chamfer:
                row.separator(factor=2)
                row.label(text="", icon='EVENT_A')
                row.label(text=f"Adaptvie: {op.modal_adaptive}")

                row.separator(factor=2)
                row.label(text="", icon='MOUSE_MMB')

                if op.modal_adaptive:
                    row.label(text=f"Adaptive Gain: {op.adaptive_gain}")
                else:
                    row.label(text=f"Segments: {op.bevel_segments}")

            row.separator(factor=2)
            row.label(text="", icon='EVENT_Y')
            row.label(text="", icon='EVENT_Z')
            row.label(text="Preset 6")

            row.separator(factor=2)
            row.label(text="", icon='EVENT_X')
            row.label(text="Preset 12")

        else:
            row.label(text="", icon='EVENT_SPACEKEY')
            row.label(text="Repeat Previous HyperBevel")

            row.separator(factor=2)

            row.label(text="", icon='EVENT_SHIFT')
            row.label(text=f"Loop Select: {op.loop}")

            if op.loop:
                row.separator(factor=2)

                row.label(text="", icon='MOUSE_MMB')
                row.label(text=f"Angle: {180 - op.loop_angle}")

            row.separator(factor=2)

            row.label(text="", icon='EVENT_ALT')
            row.label(text=f"Weld: {'True' if op.modal_weld else 'False'}")

            row.separator(factor=2)

            row.label(text="", icon='EVENT_A')
            row.label(text="Add to Selection")

            row.separator(factor=2)

            row.label(text="", icon='EVENT_X')
            row.label(text="Remove from Selection")

        row.separator(factor=2)

        row.label(text="", icon='EVENT_W')
        row.label(text=f"Wireframe: {context.active_object.show_wire}")

        if op.is_dragging:
            row.separator(factor=2)

            row.label(text="", icon='EVENT_TAB')
            row.label(text="Finish + Invoke HyperMod")

    return draw

class HyperBevelOld(bpy.types.Operator, Settings):
    bl_idname = "machin3.hyper_bevel_old"
    bl_label = "MACHIN3: Hyper Bevel (Old)"
    bl_description = ""
    bl_options = {'REGISTER', 'UNDO'}

    mode: EnumProperty(name="HyperCut Mode", items=hyperbevel_mode_items, default='SELECTION')
    width: FloatProperty(name='Width', default=0.1, min=0, step=0.1)
    overshoot: FloatProperty(name='Overshoot', default=0.02, min=0, step=0.1)
    def update_align_mids_inbetween(self, context):
        pass

    align_ends: BoolProperty(name='Align Ends', default=True)
    align_mids: BoolProperty(name='Align Mids', default=True)
    align_mids_inbetween: BoolProperty(name='Align Mids Inbetween', default=False, update=update_align_mids_inbetween)
    align_mids_inbetween_threshold: FloatProperty(name='Align Mids Inbetween Threshold', default=0.1, min=0, max=0.5, step=0.1)
    align_mids_centeraim: BoolProperty(name='Align Mids Center Aim', default=False)
    def update_bevel(self, context):
        if self.avoid_update:
            self.avoid_update = False

        if not self.bevel and self.boolean:
            self.boolean = False

    def update_bevel_segments(self, context):
        if not self.bevel:
            self.bevel = True

        if self.chamfer:
            self.avoid_update = True
            self.chamfer = False

        if self.adaptive:
            self.avoid_update = True
            self.adaptive = False

        if self.bevel_segment_preset != 'CUSTOM':
            self.bevel_segment_preset = 'CUSTOM'

    def update_bevel_segment_preset(self, context):
        if not self.bevel:
            self.bevel = True

        if self.chamfer:
            self.avoid_update = True
            self.chamfer = False

        if self.adaptive:
            self.avoid_update = True
            self.adaptive = False

    bevel: BoolProperty(name='Bevel', default=True, update=update_bevel)
    bevel_segments: IntProperty(name='Segments', default=12, min=0, max=100, step=1, update=update_bevel_segments)
    bevel_segment_preset: EnumProperty(name='Segment Preset', items=hyperbevel_segment_preset_items, default='CUSTOM', update=update_bevel_segment_preset)
    def update_adaptive(self, context):
        if self.avoid_update:
            self.avoid_update = False
            return

        if self.chamfer:
            self.avoid_update = True
            self.chamfer = False

    def update_chamfer(self, context):
        if self.avoid_update:
            self.avoid_update = False
            return

        if self.adaptive:
            self.avoid_update = True
            self.adaptive = False

    chamfer: BoolProperty(name="Chamfer", default=False, update=update_chamfer)
    adaptive: BoolProperty(name="Adaptive Bevel", default=False, update=update_adaptive)
    adaptive_factor: FloatProperty(name="Adaptive Factor", default=50)
    adaptive_gain: IntProperty(name="Adaptive Gain", default=0, min=0)
    modal_chamfer: BoolProperty(name="Chamfer (Modal)", default=False, update=update_chamfer)
    modal_adaptive: BoolProperty(name="Adaptive Bevel (Modal)", default=False, update=update_adaptive)
    boolean: BoolProperty(name='Add Boolean', default=True)
    boolean_self: BoolProperty(name='Self Boolean', default=False)
    show_wire: BoolProperty(name='Show Wire', default=False)
    weld: BoolProperty(name='Add Weld', default=False)
    edit: BoolProperty(name='Edit Cutter', default=False)
    draw_cutter_creation: BoolProperty(name='Draw Button', default=True)
    draw_non_cyclic_options: BoolProperty(name='Draw Non-Cyclic', default=True)
    draw_bevel_and_boolean: BoolProperty(name='Draw Anything', default=True)

    loop_angle: IntProperty(name="Loop Select Angle", default=140, min=0, max=180)
    dragging: BoolProperty(name="Dragging Width", default=False)
    is_tab_finish: BoolProperty(name="is Tab Finish", default=False)
    avoid_update: BoolProperty()

    @classmethod
    def poll(cls, context):
        return context.mode in ['EDIT_MESH', 'OBJECT'] and context.active_object and context.active_object.type == 'MESH'

    def draw(self, context):
        layout = self.layout

        column = layout.column(align=True)

        if not self.mode == 'CUTTER':
            column.prop(self, 'edit', text="Edit", toggle=True)
            column.separator()

        if self.draw_cutter_creation or self.edit:
            row = column.row(align=True)
            row.prop(self, 'width')

            if self.draw_non_cyclic_options:
                row.prop(self, 'overshoot')

            row = column.row(align=True)

            if self.draw_non_cyclic_options:
                row.prop(self, 'align_ends', text='Ends', toggle=True)

            row.prop(self, 'align_mids', text='Mids', toggle=True)

            r = row.row(align=True)
            r.active = self.align_mids
            r.prop(self, 'align_mids_inbetween', text='Inbetween', toggle=True)

            rr = r.row(align=True)
            rr.active = self.align_mids_inbetween
            rr.prop(self, 'align_mids_inbetween_threshold', text='')
            rr.prop(self, 'align_mids_centeraim', text='Aim', toggle=True)

            row.prop(self, 'show_wire', text='', icon='SHADING_WIRE', toggle=True)

        if self.draw_bevel_and_boolean:
            column.separator()

            row = column.split(factor=0.5, align=True)
            r = row.split(factor=0.3, align=True)
            rr = r.split(factor=0.5, align=True)
            rr.prop(self, 'chamfer', text='C', toggle=True)
            rr.prop(self, 'adaptive', text='A', toggle=True)
            r.prop(self, 'bevel', toggle=True)

            if self.adaptive:
                row.prop(self, 'adaptive_factor')

                if self.adaptive_gain:
                    row.prop(self, 'adaptive_gain', text='')
            else:
                r = row.row(align=True)
                r.active = not self.chamfer and self.bevel_segment_preset == 'CUSTOM'
                r.prop(self, 'bevel_segments')

            row = column.row(align=True)
            row.active = not self.chamfer and not self.adaptive and self.bevel_segment_preset != 'CUSTOM'
            row.prop(self, 'bevel_segment_preset', expand=True)

            column.separator()

            row = column.split(factor=0.5, align=True)
            row.prop(self, 'boolean', text="Cut", toggle=True)

            r = row.row(align=True)
            r.active = self.boolean
            r.prop(self, 'boolean_self', text="Self", toggle=True)
            r.prop(self, 'weld', text="Weld", toggle=True)

    def draw_VIEW3D(self, context):
        if context.area == self.area:

            if self.is_dragging:
                color = blue if self.modal_chamfer else green if self.modal_adaptive else yellow

                if self.width_coords:
                    draw_lines(self.width_coords, color=color, width=1, alpha=1)

                if self.segment_coords:
                    draw_lines(self.segment_coords, color=color, width=1, alpha=0.2)

            else:
                if self.selected_coords:
                    draw_line(self.selected_coords, color=yellow, width=2, alpha=0.2 if self.is_dragging else 0.99)

                if self.loop_coords:
                    draw_lines(self.loop_coords, color=yellow, width=2, alpha=0.2 if self.is_dragging else 0.4)

                if self.marked_coords:
                    draw_lines(self.marked_coords, color=green, width=2, alpha=0.2 if self.is_dragging else 0.4)

    def draw_HUD(self, context):
        if context.area == self.area:
            draw_init(self)

            dims = draw_label(context, title="Hyper Bevel ", coords=Vector((self.HUD_x, self.HUD_y)), center=False, alpha=1)

            if self.is_dragging:
                draw_label(context, title="Creation", coords=Vector((self.HUD_x + dims[0], self.HUD_y)), center=False, size=10, alpha=0.5)

                self.offset += 18

                width = dynamic_format(self.width, decimal_offset=2)
                draw_label(context, title=f'Width: {width}', coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=yellow, alpha=1)

                self.offset += 18

                if self.modal_chamfer:
                    draw_label(context, title='Chamfer', coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=blue, alpha=1)

                elif self.modal_adaptive:
                    title = f'Adaptive +{self.adaptive_gain}' if self.adaptive_gain else 'Adaptive'
                    draw_label(context, title=title, coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=green, alpha=1)

                else:
                    segments = self.bevel_segment_preset if self.bevel_segment_preset != 'CUSTOM' else self.bevel_segments
                    draw_label(context, title=f'Segments: {segments}', coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=1)

            else:
                draw_label(context, title="Selection", coords=Vector((self.HUD_x + dims[0], self.HUD_y)), center=False, size=10, alpha=0.5)

                self.offset += 18

                dims = draw_label(context, title="Edge: ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, alpha=0.5)

                title = str(self.edge_index) if self.edge_index is not None else "None"
                dims2 = draw_label(context, title=title, coords=Vector((self.HUD_x + dims[0], self.HUD_y)), offset=self.offset, center=False, color=yellow if self.edge_index is not None else red, alpha=1)

                highlighted = self.edge_index
                loop_selected = set(e.index for e in self.selected if e.index != highlighted)
                marked = set(e.index for e in self.marked if e.index != highlighted) - loop_selected

                if loop_selected:
                    dims3 = draw_label(context, title=f" +{len(loop_selected)} Loop Selected", coords=Vector((self.HUD_x + dims[0] + dims2[0], self.HUD_y)), offset=self.offset, center=False, size=10, color=yellow, alpha=1)
                else:
                    dims3 = (0, 0)

                if marked:
                    draw_label(context, title=f" +{len(marked)} Marked", coords=Vector((self.HUD_x + dims[0] + dims2[0] + dims3[0], self.HUD_y)), offset=self.offset, center=False, size=10, color=green, alpha=1)

                if self.loop:
                    self.offset += 18
                    draw_label(context, title=f"Loop Angle: {180 - self.loop_angle}", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=yellow, alpha=1)

                if self.modal_weld:
                    self.offset += 18
                    draw_label(context, title="Weld", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=yellow, alpha=1)

    def modal(self, context, event):
        context.area.tag_redraw()

        if event.type == 'MOUSEMOVE':
            get_mouse_pos(self, context, event)

        if event.type in ['W'] and event.value == 'PRESS':
            context.active_object.show_wire = not context.active_object.show_wire

        if not self.is_dragging:

            if event.type in ['MOUSEMOVE', *shift, *alt, 'A', 'X'] or scroll(event, key=True):

                self.loop = event.shift

                if event.type in alt and event.value == 'PRESS' and not self.is_dragging:

                    if self.modal_weld:
                        self.active.modifiers.remove(self.modal_weld)
                        self.modal_weld = None

                    else:
                        self.modal_weld = self.add_weld(self.active)

                    self.dg.update()

                    self.init_bmesh(context)

                    self.marked = []
                    self.marked_coords = []

                    for hitlocation, _, loop in self.marked_hits:
                        _, _, _, _, hitindex, _ = get_closest(depsgraph=self.dg, targets=[self.active], origin=hitlocation, debug=False)

                        hit = self.mx.inverted_safe() @ hitlocation
                        hitface = self.bm.faces[hitindex]

                        edge = min([(e, (hit - intersect_point_line(hit, e.verts[0].co, e.verts[1].co)[0]).length, (hit - get_center_between_verts(*e.verts)).length) for e in hitface.edges if e.calc_length()], key=lambda x: (x[1] * x[2]) / x[0].calc_length())[0]

                        self.marked.append(edge)

                        if loop:
                            get_loop_edges(self.loop_angle, self.marked, edge, edge.verts[0], prefer_center_of_three=False, prefer_center_90_of_three=False)
                            get_loop_edges(self.loop_angle, self.marked, edge, edge.verts[1], prefer_center_of_three=False, prefer_center_90_of_three=False)

                    for e in self.marked:
                        self.marked_coords.extend([self.mx @ v.co for v in e.verts])

                if event.type in ['MOUSEMOVE', *shift, *alt] or scroll(event, key=True):

                    if event.shift:
                        if scroll_up(event, key=True):
                            self.loop_angle -= 5

                        elif scroll_down(event, key=True):
                            self.loop_angle += 5

                        force_ui_update(context)

                    self.select_edge_via_raycast()

                elif self.selected and event.type in ['A', 'X']:
                    if event.type == 'A' and event.value == 'PRESS':

                        for e in self.selected:
                            if e not in self.marked:
                                self.marked.append(e)

                        self.marked_hits = [(hit, edge, loop) for hit, edge, loop in self.marked_hits if edge != self.selected[0]]
                        self.marked_hits.append(self.selected_hit)

                    elif event.type == 'X' and event.value == 'PRESS':

                        for e in self.selected:
                            if e in self.marked:
                                self.marked.remove(e)

                        self.marked_hits = [(hit, edge, loop) for hit, edge, loop in self.marked_hits if edge != self.selected[0]]

                    self.marked_coords = []

                    for e in self.marked:
                        self.marked_coords.extend([self.mx @ v.co for v in e.verts])

                self.edges = self.selected + [e for e in self.marked if e not in self.selected]

        if navigation_passthrough(event):
            return {'PASS_THROUGH'}

        if self.edges:

            if self.is_dragging:

                if scroll(event, key=True):

                    if self.modal_adaptive and not self.modal_chamfer:
                        if scroll_up(event, key=True):
                            self.adaptive_gain += 1

                        elif scroll_down(event, key=True):
                            self.adaptive_gain -= 1

                    elif not self.modal_chamfer:
                        self.bevel_segments = self.get_bevel_segments(modal=True)

                        if scroll_up(event, key=True):
                            self.bevel_segments += 1

                        elif scroll_down(event, key=True):
                            self.bevel_segments -= 1

                    force_ui_update(context)

                elif event.type == 'C' and event.value == 'PRESS':
                    self.modal_chamfer = not self.modal_chamfer

                elif event.type in ['Y', 'Z'] and event.value == 'PRESS':
                    self.modal_adaptive = False
                    self.modal_chamfer = False
                    self.bevel_segments = 6

                elif event.type in ['X'] and event.value == 'PRESS':
                    self.modal_adaptive = False
                    self.modal_chamfer = False
                    self.bevel_segments = 12

                elif event.type in ['A'] and event.value == 'PRESS':

                    if self.modal_chamfer:

                        if self.modal_adaptive:
                            self.modal_chamfer = False

                    else:
                        self.modal_adaptive = not self.modal_adaptive

                        if self.modal_adaptive:
                            self.adaptive_factor = self.get_fixed_bevel_segments() / self.width

                self.get_bevel_width(context)

                self.get_previz_coords()

                if event.type in {'LEFTMOUSE', 'SPACE', 'TAB'}:
                    self.finish(context)

                    self.set_operator_props_from_modal()

                    if (props := self._properties.get('MACHIN3_OT_hyper_bevel')) and props.get('custom_profile'):
                        del self._properties['MACHIN3_OT_hyper_bevel']['custom_profile']

                    self.is_tab_finish = event.type == 'TAB'

                    return self.execute(context)

            else:

                if event.type == 'LEFTMOUSE' and event.value == 'PRESS':

                    self.is_dragging = True

                    self.active.select_set(True)

                    self.get_bevel_width(context)

                    self.get_previz_coords()
                    return {'RUNNING_MODAL'}

                elif event.type in {'R', 'SPACE'}:
                    self.finish(context)
                    self.set_operator_props_from_modal()
                    return self.execute(context)

        if event.type in {'RIGHTMOUSE', 'ESC'} or (not self.edges and event.type in {'LEFTMOUSE', 'SPACE'}):
            self.finish(context)

            self.active.select_set(True)

            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def finish(self, context):
        finish_modal_handlers(self)

        finish_status(self)

        self.weld = True if self.modal_weld else False

        if self.modal_weld:
            self.active.modifiers.remove(self.modal_weld)

        restore_gizmos(self)

    def invoke(self, context, event):
        HC.get_addon('MESHmachine')

        wm = context.window_manager

        if wm.HC_pickhyperbevelsCOL:
            wm.gizmo_group_type_unlink_delayed('MACHIN3_GGT_pick_hyper_bevel')

            wm.HC_pickhyperbevelsCOL.clear()

        self.mode = 'RAYCAST' if context.mode == 'OBJECT' else 'CUTTER' if context.active_object.HC.ishyperbevel else 'SELECTION'
        self.overshoot = 0.1

        self.avoid_update = True
        self.bevel = context.active_object.HC.ishyperbevel

        self.boolean = False
        self.boolean_self = False

        self.weld = self.chamfer or self.modal_chamfer

        self.align_ends = True
        self.align_mids = True
        self.align_mids_inbetween = False
        self.align_mids_inbetween_threshold = 0.1
        self.align_mids_centeraim = False

        self.adaptive_gain = 0

        self.init = True
        self.edit = False

        self.draw_cutter_creation = not context.active_object.HC.ishyperbevel
        self.draw_bevel_and_boolean = True

        self.show_wire = context.active_object.show_wire

        if context.mode == 'OBJECT':

            self.active = context.active_object

            if self.chamfer or self.modal_chamfer:
                self.modal_weld = self.add_weld(self.active)

            else:
                self.modal_weld = None

            self.dg = context.evaluated_depsgraph_get()
            self.mx = context.active_object.matrix_world

            self.selected = []
            self.marked = []
            self.loop = False
            self.edge_index = False

            self.selected_hit = (None, None, False)
            self.marked_hits = []

            self.is_dragging = False
            self.drag_origin = None
            self.drag_normal = None

            hide_gizmos(self, context)

            self.init_bmesh(context)

            self.selected_coords = []
            self.marked_coords = []
            self.loop_coords = []
            self.width_coords = []
            self.segment_coords = []

            get_mouse_pos(self, context, event)

            self.select_edge_via_raycast()
            self.edges = self.selected

            init_status(self, context, func=draw_hyper_bevel_old(self))

            force_ui_update(context)

            init_modal_handlers(self, context, hud=True, view3d=True)
            return {'RUNNING_MODAL'}

        else:
            return self.execute(context)

    def execute(self, context):
        active = context.active_object

        if self.mode == 'RAYCAST':

            verts = list({v for e in self.edges for v in e.verts})
            sequences = get_edges_vert_sequences(verts, self.edges, debug=False)

            self.full_cut(context, active, self.bm, sequences, debug=False)

        elif self.mode == 'CUTTER':

            active = self.partial_cut(context)

        elif self.mode == 'SELECTION':

            bm = bmesh.from_edit_mesh(active.data)
            bm.normal_update()
            bm.verts.ensure_lookup_table()

            verts = [v for v in bm.verts if v.select]
            sequences = get_selected_vert_sequences(verts, debug=False)

            self.full_cut(context, active, bm, sequences, debug=False)

        if self.boolean and not self.edit:

            weld = active.modifiers[-2] if self.weld else None
            boolean = active.modifiers[-1]

            idx = sort_mod_after_split(boolean)

            if idx and weld:
                weld.name.replace('- ', '+ ')
                move_mod(weld, idx)

            sort_modifiers(active, debug=False)

        if self.mode == 'RAYCAST' and self.is_tab_finish:
            bpy.ops.machin3.hyper_modifier('INVOKE_DEFAULT', is_gizmo_invocation=False, is_button_invocation=False, mode='PICK')

        return {'FINISHED'}

    def get_bevel_segments(self, offset=0, modal=False):
        if modal:
            if self.modal_chamfer:
                return offset
            elif self.modal_adaptive:
                return self.get_adaptive_bevel_segments(offset)
            else:
                return self.get_fixed_bevel_segments(offset)

        else:
            if self.chamfer:
                return offset
            elif self.adaptive:
                return self.get_adaptive_bevel_segments(offset)
            else:
                return self.get_fixed_bevel_segments(offset)

    def get_fixed_bevel_segments(self, offset=0):
        segments = self.bevel_segments if self.bevel_segment_preset == 'CUSTOM' else int(self.bevel_segment_preset)
        return segments + offset

    def get_adaptive_bevel_segments(self, offset=0):
        segments = int(self.width * self.adaptive_factor) + self.adaptive_gain
        return segments + offset

    def get_bevel_width(self, context):
        view_origin, view_dir = get_view_origin_and_dir(context, self.mouse_pos)

        i = intersect_line_plane(view_origin, view_origin + view_dir, self.drag_origin, self.drag_normal)

        if i:
            edge = self.edges[0]

            intersect = self.mx.inverted_safe() @ i

            i = intersect_point_line(intersect, *[v.co for v in edge.verts])

            if i:
                closest = i[0]

                self.width = (closest - intersect).length

    def set_operator_props_from_modal(self):
        self.avoid_update = True
        self.bevel = True
        self.boolean = True

        self.avoid_update = True
        self.chamfer = self.modal_chamfer

        self.avoid_update = True
        self.adaptive = self.modal_adaptive

    def init_bmesh(self, context):
        self.mesh = bpy.data.meshes.new_from_object(self.active.evaluated_get(self.dg), depsgraph=self.dg)

        self.bm = bmesh.new()
        self.bm.from_mesh(self.mesh)
        self.bm.normal_update()
        self.bm.verts.ensure_lookup_table()
        self.bm.faces.ensure_lookup_table()

        self.bmeshes = {self.active.name: [self.bm]}
        self.bvhs = {}

    def select_edge_via_raycast(self):
        hitobj, hitlocation, hitnormal, hitindex, hitdistance, cache = cast_bvh_ray_from_mouse(self.mouse_pos, candidates=[self.active], bmeshes=self.bmeshes, bvhs=self.bvhs, debug=False)

        self.loop_coords = []
        self.selected_coords = []
        self.edge_index = None

        self.selected = []
        self.selected_hit = (None, None, False)

        if hitobj:

            for name, bvh in cache['bvh'].items():
                if name not in self.bvhs:
                    self.bvhs[name] = bvh

            hit = self.mx.inverted_safe() @ hitlocation

            hitface = self.bm.faces[hitindex]

            edge = min([(e, (hit - intersect_point_line(hit, e.verts[0].co, e.verts[1].co)[0]).length, (hit - get_center_between_verts(*e.verts)).length) for e in hitface.edges if e.calc_length()], key=lambda x: (x[1] * x[2]) / x[0].calc_length())[0]
            self.edge_index = edge.index
            self.selected.append(edge)

            self.selected_hit = (hitlocation, edge, self.loop)

            self.selected_coords = [self.mx @ v.co for v in edge.verts]

            if self.loop:
                get_loop_edges(self.loop_angle, self.selected, edge, edge.verts[0], prefer_center_of_three=False, prefer_center_90_of_three=False)
                get_loop_edges(self.loop_angle, self.selected, edge, edge.verts[1], prefer_center_of_three=False, prefer_center_90_of_three=False)

                self.loop_coords = [self.mx @ v.co for le in [e for e in self.selected if e != edge] for v in le.verts]

            self.drag_origin = hitlocation
            self.drag_normal = hitnormal

    def get_previz_coords(self):
        self.width_coords = []
        self.segment_coords = []

        for edge in self.edges:
            face_dirs = []

            for face in edge.link_faces:
                center = face.calc_center_median()
                i = intersect_point_line(center, edge.verts[0].co, edge.verts[1].co)

                if i:
                    face_dir = (center - i[0]).normalized()

                    face_dirs.append(face_dir)

                    for v in edge.verts:
                        self.width_coords.append(self.mx @ (v.co + face_dir * self.width))

            if len(face_dirs) == 2:
                face_dir1 = face_dirs[0]
                face_dir2 = face_dirs[1]

                v1coords = []
                v2coords = []

                for idx, v in enumerate(edge.verts):
                    co1 = v.co + face_dir1 * self.width
                    co2 = v.co + face_dir2 * self.width

                    handle1 = co1 + (v.co - co1) * 0.8
                    handle2 = co2 + (v.co - co2) * 0.8

                    if idx == 0:
                        v1coords.extend(interpolate_bezier(co1, handle1, handle2, co2, self.get_bevel_segments(offset=2, modal=True)))
                    else:
                        v2coords.extend(interpolate_bezier(co1, handle1, handle2, co2, self.get_bevel_segments(offset=2, modal=True)))

                for co1, co2 in zip(v1coords, v2coords):
                    self.segment_coords.extend([self.mx @ co1, self.mx @ co2])

    def get_data(self, bm, sequences):
        data = {}

        for sidx, (seq, cyclic) in enumerate(sequences):
            data[sidx] = {'cyclic': cyclic, 'convex': None, 'verts': seq, 'edges': []}

            for vidx, v in enumerate(seq):
                prev_vert = seq[(vidx - 1) % len(seq)]
                next_vert = seq[(vidx + 1) % len(seq)]

                data[sidx][v] = {'co': v.co.copy(),
                                 'no': v.normal.copy(),
                                 'dir': None,
                                 'cross': None,

                                 'prev_vert': prev_vert,
                                 'next_vert': next_vert,
                                 'prev_edge': None,
                                 'next_edge': None,

                                 'loop': None,
                                 'left_face': None,
                                 'left_face_dir': None,
                                 'right_face': None,
                                 'right_face_dir': None,

                                 'left_edge_dir': None,
                                 'right_edge_dir': None,

                                 'prev_left_edge_dir': None,
                                 'prev_left_edge_co': None,
                                 'prev_left_edge_distance': None,
                                 'next_left_edge_dir': None,
                                 'next_left_edge_co': None,
                                 'next_left_edge_distance': None,
                                 'prev_right_edge_dir': None,
                                 'prev_right_edge_co': None,
                                 'prev_right_edge_distance': None,
                                 'next_right_edge_dir': None,
                                 'next_right_edge_co': None,
                                 'next_right_edge_distance': None,

                                 'left_inbetween_dir': None,
                                 'left_inbetween_dot': None,
                                 'left_inbetween_ratios': [],
                                 'right_inbetween_dir': None,
                                 'right_inbetween_dot': None,
                                 'right_inbetween_ratios': [],

                                 'left_centeraim_dir': None,
                                 'right_centeraim_dir': None}

            if not cyclic:
                data[sidx][seq[0]]['prev_vert'] = None
                data[sidx][seq[-1]]['next_vert'] = None

            for idx, v in enumerate(seq):
                vdata = data[sidx][v]

                self.get_next_and_prev_edges(bm, v, data, vdata, sidx)

                if idx == 0:
                    edge = data[sidx]['edges'][0]
                    data[sidx]['convex'] = is_edge_convex(edge)

                self.get_directions(data, vdata, sidx)

                self.get_loop_and_faces(v, data, vdata, sidx)

                self.get_left_and_right_face_directions(vdata)

                self.get_aligned_edge_directions(v, data, vdata, sidx, debug=False)

            for v in seq:
                self.get_next_and_prev_aligned_edge_directions(v, data, sidx, debug=False)

            for v in seq:
                self.get_inbetween_and_centeraim_directions(v, data, sidx, debug=False)

        return data

    def get_next_and_prev_edges(self, bm, v, data, vdata, sidx):
        if vdata['next_vert']:
            edge = bm.edges.get([v, vdata['next_vert']])
            vdata['next_edge'] = edge

            if edge not in data[sidx]['edges']:
                data[sidx]['edges'].append(edge)

        if vdata['prev_vert']:
            edge = bm.edges.get([v, vdata['prev_vert']])
            vdata['prev_edge'] = edge

            if edge not in data[sidx]['edges']:
                data[sidx]['edges'].append(edge)

    def get_directions(self, data, vdata, sidx):
        if vdata['prev_vert'] and vdata['next_vert']:
            vdir = ((vdata['next_vert'].co - vdata['co']).normalized() + (vdata['co'] - vdata['prev_vert'].co).normalized()).normalized()
            vdata['dir'] = vdir

        elif vdata['next_vert']:
            vdir = (vdata['next_vert'].co - vdata['co']).normalized()
            vdata['dir'] = vdir

        else:
            vdir = (vdata['co'] - vdata['prev_vert'].co).normalized()
            vdata['dir'] = vdir

        vdata['cross'] = vdata['no'].cross(vdir).normalized()

    def get_loop_and_faces(self, v, data, vdata, sidx):
        if vdata['next_edge']:
            edge = vdata['next_edge']
            loops = [l for l in edge.link_loops if l.vert == v]

            vdata['loop'] = loops[0]
            vdata['left_face'] = loops[0].face
            vdata['right_face'] = loops[0].link_loop_radial_next.face

        else:
            vdata['loop'] = data[sidx][vdata['prev_vert']]['loop']
            vdata['left_face'] = data[sidx][vdata['prev_vert']]['left_face']
            vdata['right_face'] = data[sidx][vdata['prev_vert']]['right_face']

    def get_left_and_right_face_directions(self, vdata):
        i = intersect_line_plane(vdata['co'] + vdata['cross'], vdata['co'] + vdata['cross'] + vdata['left_face'].normal, vdata['co'], vdata['left_face'].normal)
        vdata['left_face_dir'] = (i - vdata['co']).normalized()

        i = intersect_line_plane(vdata['co'] - vdata['cross'], vdata['co'] - vdata['cross'] + vdata['right_face'].normal, vdata['co'], vdata['right_face'].normal)
        vdata['right_face_dir'] = (i - vdata['co']).normalized()

    def get_aligned_edge_directions(self, v, data, vdata, sidx, debug=False):

        connected_edges = [e for e in v.link_edges if e not in data[sidx]['edges']]

        if connected_edges:

            for side in ['left', 'right']:
                edges = [e for e in connected_edges if vdata.get(f'{side}_face') in e.link_faces]

                if edges:
                    edge_dir = (edges[0].other_vert(v).co - vdata['co']).normalized()
                    dot = edge_dir.dot(vdata['dir'])

                    middot = 0.99
                    enddot = 0.98

                    if abs(dot) < (enddot if not all([vdata['prev_vert'], vdata['next_vert']]) else middot):
                        co1 = vdata['co'] + vdata.get(f'{side}_face_dir')
                        co2 = co1 + vdata['dir']
                        co3 = vdata['co']
                        co4 = co3 + edge_dir

                        i = intersect_line_line(co1, co2, co3, co4)
                        if i:
                            aligned_edge_dir = i[1] - vdata['co']
                            vdata[f'{side}_edge_dir'] = aligned_edge_dir

                            if debug:
                                draw_vector(aligned_edge_dir * 0.1, origin=vdata['co'], mx=bpy.context.active_object.matrix_world, color=(1, 0, 1), width=2, modal=False)
                                draw_vector(edge_dir * 0.1, origin=vdata['co'], mx=bpy.context.active_object.matrix_world, width=2, modal=False)

    def get_next_and_prev_aligned_edge_directions(self, v, data, sidx, debug=False):

        if debug:
            print()
            print(v)

        for side in ['left', 'right']:
            if debug:
                print("", side)

            for direction in ['next', 'prev']:
                if debug:
                    print(" ", direction)

                vdata = data[sidx][v]
                co = vdata['co'].copy()
                distance = 0
                c = 0

                while vdata[f'{direction}_vert'] and not vdata[f'{side}_edge_dir']:
                    c += 1

                    vdata = data[sidx][vdata[f'{direction}_vert']]
                    edge_dir = vdata[f'{side}_edge_dir']

                    distance += (vdata['co'] - co).length
                    co = vdata['co'].copy()

                    if edge_dir:
                        if debug:
                            print("   edge_dir:", edge_dir)
                            print("         co:", co)
                            print("   distance:", distance)

                        data[sidx][v][f'{direction}_{side}_edge_dir'] = edge_dir.normalized()
                        data[sidx][v][f'{direction}_{side}_edge_co'] = co
                        data[sidx][v][f'{direction}_{side}_edge_distance'] = distance

                    if data[sidx]['cyclic'] and c > len(data[sidx]['verts']):
                        break

    def get_inbetween_and_centeraim_directions(self, v, data, sidx, debug=False):

        if debug:
            print()
            print(v.index)

        for side in ['left', 'right']:

            vdata = data[sidx][v]

            if not vdata[f'{side}_edge_dir'] and vdata[f'next_{side}_edge_dir'] and vdata[f'prev_{side}_edge_dir']:

                prev_dir = vdata[f'prev_{side}_edge_dir']
                next_dir = vdata[f'next_{side}_edge_dir']

                prev_co = vdata[f'prev_{side}_edge_co']
                next_co = vdata[f'next_{side}_edge_co']

                prev_distance = vdata[f'prev_{side}_edge_distance']
                next_distance = vdata[f'next_{side}_edge_distance']

                if debug:
                    print("        dir:", prev_dir, next_dir)
                    print("         co:", prev_co, next_co)
                    print("   distance:", prev_distance, next_distance)

                inbetween_dir = average_normals([edge_dir * (1 - distance / (prev_distance + next_distance)) for edge_dir, distance in zip([prev_dir, next_dir], [prev_distance, next_distance])])

                centeraim_dir = (get_center_between_points(prev_co, next_co) - vdata['co']).normalized()

                co1 = vdata['co'] + vdata.get(f'{side}_face_dir')
                co2 = co1 + vdata['dir']
                co3 = vdata['co']
                co4 = co3 + inbetween_dir

                i = intersect_line_line(co1, co2, co3, co4)

                if i:
                    corrected_inbetween_dir = i[1] - vdata['co']
                    vdata[f'{side}_inbetween_dir'] = corrected_inbetween_dir

                    vdata[f'{side}_inbetween_dot'] = prev_dir.dot(next_dir)
                    vdata[f'{side}_inbetween_ratios'] = [1 - prev_distance / (prev_distance + next_distance), 1 - next_distance / (prev_distance + next_distance)]

                    if debug:
                        draw_vector(corrected_inbetween_dir * 0.1, origin=vdata['co'], mx=bpy.context.active_object.matrix_world, color=(0, 1, 1), width=2, modal=False)
                        draw_vector(inbetween_dir * 0.1, origin=vdata['co'], mx=bpy.context.active_object.matrix_world, color=(1, 0, 1), width=2, modal=False)

                co4 = co3 + centeraim_dir

                i = intersect_line_line(co1, co2, co3, co4)
                if i:
                    corrected_centeraim_dir = i[1] - vdata['co']
                    vdata[f'{side}_centeraim_dir'] = corrected_centeraim_dir

                    if debug:
                        draw_vector(corrected_centeraim_dir * 0.1, origin=vdata['co'], mx=bpy.context.active_object.matrix_world, color=(0, 1, 1), width=2, modal=False)
                        draw_vector(centeraim_dir * 0.1, origin=vdata['co'], mx=bpy.context.active_object.matrix_world, color=(1, 0, 1), width=2, modal=False)

    def debug_data(self, context, data, mx, factor=0.1):
        printd(data, 'data dict')

        for sidx, selection in data.items():
            for idx, v in enumerate(selection['verts']):
                co = selection[v]['co']
                no = selection[v]['no']
                vdir = selection[v]['dir']
                cross = selection[v]['cross']

                draw_vector(no * factor, origin=co, mx=mx, color=normal, modal=False)
                draw_vector(vdir * factor, origin=co, mx=mx, color=(1, 1, 0), modal=False)

                draw_vector(cross * factor / 3, origin=co, mx=mx, color=(0, 1, 0), alpha=0.5, modal=False)
                draw_vector(-cross * factor / 3, origin=co, mx=mx, color=(1, 0, 0), alpha=0.5, modal=False)

                for side in ['left', 'right']:

                    face_dir = selection[v][f'{side}_face_dir']
                    edge_dir = selection[v][f'{side}_edge_dir']
                    inbetween_dir = selection[v][f'{side}_inbetween_dir']
                    centeraim_dir = selection[v][f'{side}_centeraim_dir']

                    draw_vector(face_dir * factor, origin=co, mx=mx, color=(0, 1, 0) if side == 'left' else (1, 0, 0), modal=False)

                    if edge_dir:
                        draw_vector(edge_dir * factor, origin=co, mx=mx, width=2, modal=False)

                    if inbetween_dir:
                        draw_vector(inbetween_dir * factor, origin=co, mx=mx, color=(0, 0, 1), width=1, modal=False)

                    if centeraim_dir:
                        draw_vector(centeraim_dir * factor, origin=co, mx=mx, color=(0, 1, 1), width=1, modal=False)

        context.area.tag_redraw()

    def get_geo_from_data(self, data, mx):
        geo = {}

        for sidx, selection in data.items():
            cutter = {'cyclic': selection['cyclic'],
                      'convex': selection['convex'],
                      'length': len(selection['verts']),
                      'verts': {},
                      'face_indices': [],
                      'center_edge_indices': [],
                      'overshoot_start': None,
                      'overshoot_end': None,
                      'mx': None}

            for idx, v in enumerate(selection['verts']):
                vdata = selection[v]

                if idx == 0:
                    if selection['convex']:
                        cutter['overshoot_start'] = - vdata['dir'] * vdata['next_edge'].calc_length()
                    else:
                        cutter['overshoot_start'] = Vector()

                elif idx == cutter['length'] - 1:
                    if selection['convex']:
                        cutter['overshoot_end'] = vdata['dir'] * vdata['prev_edge'].calc_length()
                    else:
                        cutter['overshoot_end'] = Vector()

                for i in range(3):
                    vidx = str(3 * idx + i)

                    cutter['verts'][vidx] = {'co': vdata['co'],
                                             'side': None,
                                             'offset': None,
                                             'offset_edge_aligned': None,

                                             'offset_inbetween_aligned': None,
                                             'offset_inbetween_dot': None,
                                             'offset_inbetween_ratios': [],

                                             'offset_centeraim_aligned': None}

                    if i == 1:
                        cutter['verts'][vidx]['side'] = 'CENTER'

                    else:
                        side = {0: 'left', 2: 'right'}[i]

                        cutter['verts'][vidx]['side'] = side.capitalize()
                        cutter['verts'][vidx]['offset'] = vdata[f'{side}_face_dir']

                        if vdata[f'{side}_edge_dir']:
                            cutter['verts'][vidx]['offset_edge_aligned'] = vdata[f'{side}_edge_dir']

                        if vdata[f'{side}_inbetween_dir']:
                            cutter['verts'][vidx]['offset_inbetween_aligned'] = vdata[f'{side}_inbetween_dir']
                            cutter['verts'][vidx]['offset_inbetween_dot'] = vdata[f'{side}_inbetween_dot']
                            cutter['verts'][vidx]['offset_inbetween_ratios'] = vdata[f'{side}_inbetween_ratios']

                        if vdata[f'{side}_centeraim_dir']:
                            cutter['verts'][vidx]['offset_centeraim_aligned'] = vdata[f'{side}_centeraim_dir']

                if idx < cutter['length'] - 1:

                    cutter['face_indices'].append([3 * idx + i for i in [0, 1, 4, 3]])
                    cutter['face_indices'].append([3 * idx + i for i in [1, 2, 5, 4]])

                    cutter['center_edge_indices'].append([3 * idx + 1, 3 * (idx + 1) + 1])

                elif cutter['cyclic']:
                    cutter['face_indices'].append([cutter['length'] * 3 - 3, cutter['length'] * 3 - 2, 1, 0])
                    cutter['face_indices'].append([cutter['length'] * 3 - 2, cutter['length'] * 3 - 1, 2, 1])

                    cutter['center_edge_indices'].append([cutter['length'] * 3 - 2, 1])

            loc = mx @ average_locations([selection[v]['co'] for v in selection['verts']])

            normal = (mx.to_quaternion() @ average_normals([selection[v]['no'] for v in selection['verts']])).normalized()
            binormal = (mx.to_quaternion() @ average_normals([selection[v]['dir'] for v in selection['verts']])).normalized()
            tangent = binormal.cross(normal).normalized()
            normal = tangent.cross(binormal).normalized()

            rot = create_rotation_matrix_from_vectors(tangent, binormal, normal)
            cutter['mx'] = get_loc_matrix(loc) @ rot.to_4x4()

            geo[sidx] = cutter

        return geo

    def debug_geo(self, context, geo, mx, factor=0.1):
        printd(geo, 'geo dict')

        for sidx, geometry in geo.items():
            for idx, vdata in geometry['verts'].items():
                if vdata['side'] == 'CENTER':
                    draw_point(vdata['co'], mx=mx, size=8, modal=False)

                else:
                    draw_point(vdata['co'] + vdata['offset'] * factor, mx=mx, color=(1, 1, 0), size=6, modal=False)

                    if vdata['offset_edge_aligned']:
                        draw_point(vdata['co'] + vdata['offset_edge_aligned'] * factor, mx=mx, color=(0, 1, 0), size=5, modal=False)

                    if vdata['offset_inbetween_aligned']:
                        draw_point(vdata['co'] + vdata['offset_inbetween_aligned'] * factor, mx=mx, color=(0, 0, 1), size=4, modal=False)

                    if vdata['offset_centeraim_aligned']:
                        draw_point(vdata['co'] + vdata['offset_centeraim_aligned'] * factor, mx=mx, color=(0, 1, 1), size=3, modal=False)

            cmx = geometry['mx']
            loc = cmx.to_translation()

            tangent = cmx.col[0].xyz
            binormal = cmx.col[1].xyz
            normal = cmx.col[2].xyz

            draw_point(loc, size=8, color=(0, 1, 0), modal=False)

            draw_vector(normal, origin=loc, color=(0, 0, 1), modal=False)
            draw_vector(binormal, origin=loc, color=(0, 1, 0), modal=False)
            draw_vector(tangent, origin=loc, color=(1, 0, 0), modal=False)

        context.area.tag_redraw()

    def create_cutter(self, context, active, geometry, edit=False):
        cutter = active.copy()
        cutter.data = bpy.data.meshes.new(name="Hyper Bevel")
        context.scene.collection.objects.link(cutter)

        cutter.HC.ishyperbevel = True
        cutter.modifiers.clear()

        if HC.get_addon('MESHmachine'):
            cutter.MM.stashes.clear()

        cutter.name = "Hyper Bevel"
        cutter.display_type = 'WIRE'
        hide_render(cutter, True)

        parent(cutter, active)

        cutter.HC.ishyper = True
        cutter.HC.objtype = 'CUBE'
        cutter.HC.geometry_gizmos_show = True

        bm = bmesh.new()
        bm.from_mesh(cutter.data)

        edge_glayer, face_glayer = ensure_gizmo_layers(bm)

        verts = []
        faces = []

        for idx, vdata in geometry['verts'].items():
            if vdata['side'] == 'CENTER':
                verts.append(bm.verts.new(vdata['co']))
            else:
                verts.append(bm.verts.new(vdata['co'] + vdata['offset'] * self.width))

        for indices in geometry['face_indices']:
            faces.append(bm.faces.new([verts[i] for i in indices]))

        align_indices = []

        if self.align_ends or (self.align_mids and geometry['cyclic']):
            vert_count = len(verts)
            align_indices.extend([0, 2, vert_count - 3, vert_count - 1])

        if self.align_mids:
            if geometry['length'] > 2:
                for l in range(1, geometry['length'] - 1):
                    align_indices.extend([l * 3, l * 3 + 2])

        for idx in align_indices:
            v = verts[idx]
            vdata = geometry['verts'][str(idx)]

            if vdata['offset_edge_aligned']:
                v.co = vdata['co'] + vdata['offset_edge_aligned'] * self.width

            elif self.align_mids_inbetween and vdata['offset_inbetween_aligned']:

                dot = vdata['offset_inbetween_dot']
                ratio = min(vdata['offset_inbetween_ratios'])

                if not (dot < - 0.97 and self.align_mids_inbetween_threshold < ratio):
                    v.co = vdata['co'] + vdata['offset_inbetween_aligned'] * self.width

                elif self.align_mids_centeraim and vdata['offset_centeraim_aligned']:
                    v.co = vdata['co'] + vdata['offset_centeraim_aligned'] * self.width

        if not geometry['cyclic'] and self.overshoot:
            for idx in [0, 1, 2]:
                verts[idx].co = verts[idx].co + geometry['overshoot_start'] * self.overshoot

            for idx in [-3, -2, -1]:
                verts[idx].co = verts[idx].co + geometry['overshoot_end'] * self.overshoot

        center_edges = [bm.edges.get([verts[idx] for idx in indices]) for indices in geometry['center_edge_indices']]

        for e in center_edges:
            e[edge_glayer] = 1

        center_vert_ids = []

        if not edit:
            self.extrude_cutter(cutter, bm, verts, faces, geometry, edge_glayer, face_glayer)

            if self.bevel or self.boolean:
                cutter.HC.ishyperbevel = False

        bm.to_mesh(cutter.data)
        bm.free()

        if not edit:
            if self.bevel:
                center_vert_ids = [int(vidx) for vidx in geometry['verts'] if geometry['verts'][vidx]['side'] == 'CENTER']

                vgroup = add_vgroup(cutter, 'Edge Bevel', ids=center_vert_ids, weight=1)

                bevel_mod = add_bevel(cutter, name="Edge Bevel", width=0, limit_method='VGROUP', vertex_group=vgroup.name)
                bevel_mod.offset_type = 'PERCENT'
                bevel_mod.width_pct = 100
                bevel_mod.segments = self.get_bevel_segments(offset=1, modal=False)
                bevel_mod.profile = 0.6
                bevel_mod.loop_slide = True

                if (props := self._properties.get('MACHIN3_OT_hyper_bevel')) and (data := props.get('custom_profile')):
                    set_bevel_profile_from_dict(bevel_mod, dict(data))

                _weld = add_weld(cutter, name="Weld", distance=0.000001, mode='CONNECTED')

        geometry['deltamx'] = geometry['mx'].inverted_safe() @ cutter.matrix_world

        set_obj_origin(cutter, geometry['mx'])

        cutter.HC['geometry'] = geometry

        return cutter

    def extrude_cutter(self, cutter, bm, verts, faces, geometry, edge_glayer, face_glayer):
        if self.boolean:
            ret = bmesh.ops.extrude_face_region(bm, geom=faces)

            top_faces = [el for el in ret['geom'] if isinstance(el, bmesh.types.BMFace)]
            top_verts = {v for f in top_faces for v in f.verts}

            for v in top_verts:
                normal = average_normals([f.normal for f in v.link_faces if f in top_faces])
                v.co = v.co + normal * self.width * 0.1 * (1 if geometry['convex'] else -1)

            top_center_edges = [e for f in top_faces for e in f.edges if e[edge_glayer] == 1]

            for e in top_center_edges:
                e[edge_glayer] = 0

            if not geometry['cyclic']:
                first_center_vert = verts[1]
                last_center_vert = verts[-2]

                first_cap_faces = [f for f in first_center_vert.link_faces if f not in faces]
                last_cap_faces = [f for f in last_center_vert.link_faces if f not in faces]

                geo = bmesh.ops.dissolve_faces(bm, faces=first_cap_faces + last_cap_faces)

                for f in geo['region']:
                    f[face_glayer] = 1

            if not geometry['convex']:
                bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

            hide_faces = {f for v in top_verts for f in v.link_faces}

            for f in hide_faces:
                f.hide_set(True)

    def full_cut(self, context, active, bm, sequences, debug=False):
        data = self.get_data(bm, sequences)

        if debug:
            self.debug_data(context, data, active.matrix_world)

        geo = self.get_geo_from_data(data, active.matrix_world)

        if debug:
            self.debug_geo(context, geo, active.matrix_world)

        for sidx, geometry in geo.items():
            cutter = self.create_cutter(context, active, geometry, edit=self.edit)

            if self.edit:
                if context.mode == 'EDIT_MESH':
                    bpy.ops.object.mode_set(mode='OBJECT')

                bpy.ops.object.select_all(action='DESELECT')

                context.view_layer.objects.active = cutter
                cutter.select_set(True)

                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')

                self.draw_cutter_creation = False
                self.draw_bevel_and_boolean = False

                return

            if self.boolean:
                boolean = self.add_boolean(context, active, cutter, convex=geometry['convex'])

                if self.mode == 'RAYCAST':

                    if self.init:
                        self.init = False

                        face_count = len(self.mesh.polygons)
                        bpy.data.meshes.remove(self.mesh, do_unlink=True)

                        dg = context.evaluated_depsgraph_get()
                        mesh = bpy.data.meshes.new_from_object(active.evaluated_get(dg), depsgraph=dg)

                        if len(mesh.polygons) < face_count / 10:
                            self.init = False
                            boolean.show_viewport = False

                            popup_message("Adjust the Operator Properties, or Undo the Operatrion.", title="Hyper Bevel failed!")

        active.show_wire = self.show_wire

        self.draw_cutter_creation = self.mode != 'CUTTER'
        self.draw_bevel_and_boolean = True

        self.draw_non_cyclic_options = not all([g['cyclic'] for g in geo.values()])

    def partial_cut(self, context):
        cutter = context.active_object
        parent = cutter.parent

        if cutter and parent:

            if cutter.hide_get():
                cutter.hide_set(False)

            booleans = [mod for mod in parent.modifiers if mod.type == 'BOOLEAN' and mod.object == cutter]

            if booleans:
                for mod in booleans:
                    print("removing previous mod:", mod)
                    parent.modifiers.remove(mod)

            bm = bmesh.from_edit_mesh(cutter.data)
            bm.normal_update()
            bm.verts.ensure_lookup_table()

            edge_glayer, face_glayer = ensure_gizmo_layers(bm)

            verts = [v for v in bm.verts]
            faces = [f for f in bm.faces]

            center_edges = [e for e in bm.edges if e[edge_glayer] == 1]
            center_vert_ids = list({v.index for e in center_edges for v in e.verts})

            geometry = {'center_edge_indices': [e.index for e in center_edges],
                        'cyclic': cutter.HC['geometry']['cyclic'],
                        'convex': cutter.HC['geometry']['convex']}

            if geometry['center_edge_indices']:
                self.extrude_cutter(cutter, bm, verts, faces, geometry, edge_glayer, face_glayer)

                bmesh.update_edit_mesh(cutter.data)

                bpy.ops.object.mode_set(mode='OBJECT')

                if self.bevel:

                    vgroup = add_vgroup(cutter, 'Edge Bevel', ids=center_vert_ids, weight=1)

                    bevel_mod = add_bevel(cutter, name="Edge Bevel", width=0, limit_method='VGROUP', vertex_group=vgroup.name)
                    bevel_mod.offset_type = 'PERCENT'
                    bevel_mod.width_pct = 100
                    bevel_mod.segments = self.get_bevel_segments(offset=1, modal=False)
                    bevel_mod.profile = 0.6
                    bevel_mod.loop_slide = True

                    _weld = add_weld(cutter, name="Weld", distance=0.000001, mode='CONNECTED')

                if self.boolean:
                    _boolean = self.add_boolean(context, parent, cutter, convex=geometry['convex'])

                context.view_layer.objects.active = parent

                return cutter.parent

    def add_boolean(self, context, active, cutter, convex=True):
        if self.weld:
            weld = self.add_weld(active)
            weld.show_in_editmode = self.mode == 'SELECTION'

        indexed_name = get_new_mod_name(active, 'HYPERBEVEL')

        boolean = active.modifiers.new(name=indexed_name, type='BOOLEAN')
        boolean.object = cutter
        boolean.solver = 'MANIFOLD' if bpy.app.version >= (4, 5, 0) else 'EXACT'
        boolean.operation = 'DIFFERENCE' if convex else 'UNION'
        boolean.show_expanded = False
        boolean.show_in_editmode = self.mode == 'SELECTION'
        boolean.use_self = self.boolean_self

        if self.bevel:
            cutter.hide_set(True)

        return boolean

    def add_weld(self, obj):
        mod = add_weld(obj, distance=0.0001, mode='ALL')

        names = [mo.name for mo in obj.modifiers if mo != mod and mo.type == 'WELD' and 'Weld' in mo.name]

        if names:
            maxidx = get_biggest_index_among_names(names)
            mod.name = f"- Weld.{str(maxidx + 1).zfill(3)}"
        else:
            mod.name = "- Weld"

        return mod

class PickHyperBevelGizmoManager:
    gizmo_props = {}
    gizmo_data = {}

    def gizmo_poll(self, context):
        if context.mode == 'OBJECT':
            props = self.gizmo_props
            return props.get('area_pointer') == str(context.area.as_pointer()) and props.get('show')

    def gizmo_group_init(self, context, hyperbevels):
        self.gizmo_props.clear()
        self.gizmo_data.clear()

        self.gizmo_props['show'] = True
        self.gizmo_props['area_pointer'] = str(context.area.as_pointer())

        self.gizmo_data['hyperbevels'] = []

        for idx, (modobj, mod) in enumerate(hyperbevels.items()):
            bevel = {'index': idx,
                     'modname': mod.name,

                     'is_highlight': False,

                     'obj': modobj,

                     'show_viewport': mod.show_viewport,
                     'remove': False}

            self.gizmo_data['hyperbevels'].append(bevel)

        context.window_manager.gizmo_group_type_ensure('MACHIN3_GGT_pick_hyper_bevel')

    def gizmo_group_finish(self, context):
        self.gizmo_props.clear()
        self.gizmo_data.clear()

        context.window_manager.gizmo_group_type_unlink_delayed('MACHIN3_GGT_pick_hyper_bevel')

def draw_pick_bevel(op):
    def draw(self, context):
        layout = self.layout

        row = layout.row(align=True)
        row.label(text='Pick Hyper Bevel')

        if not op.highlighted:
            draw_status_item(row, key='LMB', text="Finish")

        draw_status_item(row, key='MMB', text="Viewport")
        draw_status_item(row, key='RMB', text="Cancel")

        row.separator(factor=10)

        if op.highlighted:
            mod = op.active.modifiers.get(op.highlighted['modname'])
            obj = op.highlighted['obj']
            is_sel = obj.visible_get() and obj.select_get()

            row.label(text="", icon='RESTRICT_SELECT_OFF')
            row.label(text=op.highlighted['modname'])

            draw_status_item(row, key='S', text="Select + Finish", gap=2)
            draw_status_item(row, key=['CTRL', 'S'], text="Select + Finish into Edit Mode", gap=1)

            text = "Deselect" if op.initial[mod.name]['visible']['visible'] and is_sel else 'Hide' if is_sel else "Select"
            draw_status_item(row, key=['SHIFT', 'S'], text=text, gap=1)

            draw_status_item(row, active=mod.show_viewport, key='D', text="Enabled" if mod.show_viewport else "Disabled", gap=2)

            draw_status_item(row, active=op.highlighted['remove'], alert=op.highlighted['remove'], key='X', text="Deleting" if op.highlighted['remove'] else "Delete", gap=2)

            row.separator(factor=2)

            if mod.show_viewport:
                segments = edge_bevel.segments - 1 if (obj := op.highlighted['obj']) and (edge_bevel := obj.modifiers.get('Edge Bevel')) else None

                draw_status_item(row, key='LMB', text="Edit",gap=2)
                draw_status_item(row, key='E', text="Extend",gap=2)

                row.separator(factor=2)

                if segments is not None:
                    if segments:
                        draw_status_item(row, key='MMB_SCROLL', text="Segments", prop=segments, gap=2)

                    draw_status_item(row, active=bool(segments), key='C', text="Chamfer", gap=1)

                if getattr(bpy.types, 'MACHIN3_OT_mirror', False):
                    draw_status_item(row, key='M', text="Initialize Mirror", gap=2)

    return draw

class PickHyperBevel(bpy.types.Operator, PickHyperBevelGizmoManager, Settings):
    bl_idname = "machin3.pick_hyper_bevel"
    bl_label = "MACHIN3: Pick Hyper Bevel"
    bl_description = "Pick Hyper Bevel"
    bl_options = {'REGISTER', 'UNDO'}

    mirror = False

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            active = context.active_object
            return active

    def draw_HUD(self, context):
        if context.area == self.area:
            if self.gizmo_props['show']:
                draw_init(self)

                is_active = bool(self.highlighted and (name := self.highlighted['modname']) and (mod := self.active.modifiers.get(name, None)) and mod.show_viewport)
                dims = draw_label(context, title='Edit ' if self.highlighted else 'Pick ', coords=Vector((self.HUD_x, self.HUD_y)), color=white, center=False, alpha=1 if is_active else 0.25)

                if self.highlighted:
                    is_remove = self.highlighted['remove']
                    cutter = self.highlighted['obj']
                    edge_bevel = cutter.modifiers.get('Edge Bevel', None) if cutter else None

                    color, alpha = (green, 1) if is_active else (white, 0.5)
                    dims += draw_label(context, title=f"🔧 {name} ", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, color=color, center=False, alpha=alpha)

                    if is_remove:
                        draw_label(context, title="to be removed", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, size=10, color=red, center=False, alpha=1)

                    elif not is_active:
                        draw_label(context, title="disabled", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, size=10, color=white, center=False, alpha=0.25)

                else:
                     draw_label(context, title='Hyper Bevel', coords=Vector((self.HUD_x + dims.x, self.HUD_y)), color=white, center=False, alpha=0.25)

                self.offset += 18

                if self.highlighted:

                    if cutter:
                        dims = draw_label(context, title='Object: ', coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, size=10, color=white, center=False, alpha=0.5)

                        color = red if is_remove else yellow if is_active else white
                        dims += draw_label(context, title=f'{cutter.name} ', coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, size=10, color=color, center=False, alpha=1)

                        if not cutter.visible_get() and (meta := self.initial[self.highlighted['modname']]['visible']['meta']) in ['SCENE', 'VIEWLAYER', 'HIDDEN_COLLECTION']:
                            if meta == 'SCENE':
                                title = 'not in Scene'
                            elif meta == 'VIEWLAYER':
                                title = 'not on View Layer'
                            else:
                                title = 'in hidden Collection'

                            dims += draw_label(context, title=title, coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, size=10, color=orange, alpha=1)

                        if edge_bevel and is_active and not is_remove:
                            self.offset += 24

                            segments = str(edge_bevel.segments - 1)

                            if edge_bevel.segments > 1:
                                if edge_bevel.profile_type == 'CUSTOM':
                                    dims = draw_label(context, title=f"Segments: {segments} ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, color=white, center=False, alpha=0.25)
                                    draw_label(context, title="Custom Profile", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, color=blue, center=False, alpha=1)

                                else:
                                    dims = draw_label(context, title='Segments: ', coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, color=white, center=False, alpha=0.5)
                                    draw_label(context, title=segments, coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, color=white, center=False, alpha=1)

                            else:
                                draw_label(context, title="Chamfer", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, color=blue, center=False, alpha=1)

                else:
                    draw_label(context, title="None", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, size=10, color=red, center=False, alpha=1)

    def modal(self, context, event):
        if ignore_events(event):
            return {'RUNNING_MODAL'}

        context.area.tag_redraw()

        if self.active.show_wire and (time() - self.wire_time) > 1:
            self.active.show_wire = False

        if event.type == 'MOUSEMOVE':
            get_mouse_pos(self, context, event, window=True)

            self.is_in_3d_view = self.is_mouse_in_3d_view()

        self.highlighted = self.get_highlighted_hyper_bevel(context)

        if self.highlighted:
            events = ['E', 'S', 'D', 'X', 'C']

            if getattr(bpy.types, 'MACHIN3_OT_mirror', False):
                events.append('M')

            if event.type in events and event.value == 'PRESS' or scroll(event, key=True):
                active = bpy.data.objects.get(self.activename)

                mod = active.modifiers.get(self.highlighted['modname'])

                cutter = self.highlighted['obj']
                edge_bevel = cutter.modifiers.get('Edge Bevel')

                if event.type  == 'S':

                    if cutter:
                        self.active.select_set(False)

                        if event.shift:
                            state = not (cutter.visible_get() and cutter.select_get())

                            if state:
                                ensure_visibility(context, cutter, select=True)
                                context.view_layer.objects.active = cutter

                            else:

                                restore_visibility(cutter, self.initial[mod.name]['visible'])

                                if not any(b['obj'].select_get() for b in self.gizmo_data['hyperbevels']):
                                    context.view_layer.objects.active = self.active
                                    self.active.select_set(True)

                            warp_mouse(self, context, self.mouse_pos)

                        else:
                            self.finish(context)

                            ensure_visibility(context, cutter, select=True)
                            context.view_layer.objects.active = cutter

                            if event.ctrl:
                                bpy.ops.object.mode_set(mode='EDIT')

                                if not active_tool_is_hypercursor(context):
                                    bpy.ops.wm.tool_set_by_id(name="machin3.tool_hyper_cursor")

                            return {'FINISHED'}

                elif event.type == 'D':
                    mod.show_viewport = not mod.show_viewport
                    self.highlighted['show_viewport'] = mod.show_viewport

                    if mod.show_viewport and self.highlighted['remove']:
                        self.highlighted['remove'] = False

                elif event.type == 'X':
                    self.highlighted['remove'] = not self.highlighted['remove']

                    mod.show_viewport = not self.highlighted['remove']

                    if mod.show_viewport and not self.highlighted['show_viewport']:
                        self.highlighted['show_viewport'] = True

                if mod.show_viewport:

                    if edge_bevel:

                        if scroll(event, key=True):

                            if edge_bevel.profile_type == 'CUSTOM':
                                edge_bevel.profile_type = 'SUPERELLIPSE'

                            if scroll_up(event, key=True):
                                edge_bevel.segments += 1

                            else:
                                edge_bevel.segments -= 1

                            self.active.show_wire = True
                            self.wire_time = time()

                            self.highlighted_adjusted = self.highlighted

                        elif event.type in 'C':

                            if edge_bevel.segments == 1:

                                if self.segments[mod.name] != 1:
                                    edge_bevel.segments = self.segments[mod.name]

                                else:
                                    edge_bevel.segments = 13
                                    self.segments[mod.name] = 13

                            else:
                                self.segments[mod.name] = edge_bevel.segments
                                edge_bevel.segments = 1

                            self.highlighted_adjusted = self.highlighted

                    if event.type == 'E':
                        bpy.ops.machin3.extend_hyper_bevel('INVOKE_DEFAULT', objname=cutter.name, modname=mod.name, is_hypermod_invocation=False)

                    elif event.type == 'M':

                        bpy.ops.object.select_all(action='DESELECT')
                        context.view_layer.objects.active = active
                        active.select_set(True)

                        vis = visible_get(cutter)

                        ensure_visibility(context, cutter, select=True)

                        active.HC['hyperbevelmirror'] = {'name': cutter.name,
                                                         'visible': vis}

                        bpy.ops.machin3.macro_mirror_hide('INVOKE_DEFAULT')

        finish_events = ['SPACE']

        if self.is_in_3d_view and not self.highlighted:
            finish_events.append('LEFTMOUSE')

        if self.highlighted:
            finish_events.append('TAB')

        if event.type in finish_events and event.value == 'PRESS':

            for b in self.gizmo_data['hyperbevels']:
                if b['remove']:
                    mod = self.active.modifiers.get(b['modname'], None)

                    if mod:
                        if weld := self.get_preceding_weld_mod(self.active, mod):
                            remove_mod(weld)

                        remove_mod(mod)

                        if b['obj']:
                            remove_obj(b['obj'])

            if self.highlighted_adjusted:
                cutter = self.highlighted_adjusted['obj']
                edge_bevel = cutter.modifiers.get('Edge Bevel')

                self.store_settings('hyper_bevel', {'segments': edge_bevel.segments,
                                                    'chamfer': edge_bevel.segments == 1,
                                                    'custom_profile': get_bevel_profile_as_dict(edge_bevel) if edge_bevel.profile_type == 'CUSTOM' else None})

            self.finish(context)

            if event.type == 'TAB':
                bpy.ops.machin3.hyper_modifier('INVOKE_DEFAULT', is_gizmo_invocation=False, is_button_invocation=False, mode='PICK')

            return {'FINISHED'}

        elif event.type in ['ESC', 'RIGHTMOUSE'] and event.value == 'PRESS':
            self.finish(context)

            for name, data in self.initial.items():

                if name == 'MODIFIERS':

                    for idx, modname in enumerate(data):

                        if not self.active.modifiers.get(modname, None):

                            weld = add_weld(self.active)
                            weld.name = modname

                            move_mod(weld, idx)

                    remove = []

                    for mod in self.active.modifiers:
                        if mod.name not in data and 'Weld' in mod.name:
                            remove.append(mod)

                    for mod in remove:
                        remove_mod(mod)

                else:
                    mod = self.active.modifiers.get(name, None)
                    mod.show_viewport = data['show_viewport']

                    if mod and (obj := mod.object):
                        edge_bevel = obj.modifiers.get('Edge Bevel', None)

                        if edge_bevel:
                            edge_bevel.segments = data['segments']
                            edge_bevel.profile_type = data['profile_type']
                            edge_bevel.profile = data['profile']

                        bm = data['bmesh']

                        bm.to_mesh(obj.data)
                        bm.free()

                        restore_visibility(obj, data['visible'])

            return {'CANCELLED'}

        if event.type == 'T' and event.value == 'PRESS':
            return {'PASS_THROUGH'}

        elif navigation_passthrough(event, alt=True, wheel=not self.highlighted):
            return {'PASS_THROUGH'}

        elif gizmo_selection_passthrough(self, event):

            if event.type == 'LEFTMOUSE':
                self.highlighted_adjusted = None

            return {'PASS_THROUGH'}

        elif self.is_in_3d_view and event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            return {'PASS_THROUGH'}

        elif not self.is_in_3d_view and event.type in ['LEFTMOUSE', *numbers[:10]]:
            return {'PASS_THROUGH'}

        return {'RUNNING_MODAL'}

    def finish(self, context):
        finish_modal_handlers(self)

        self.gizmo_group_finish(context)

        finish_status(self)

        restore_gizmos(self)

        force_ui_update(context)

    def invoke(self, context, event):
        self.active = context.active_object

        self.activename = self.active.name

        hyperbevels = self.get_hyper_bevels()

        if hyperbevels:

            self.get_init_states(hyperbevels)

            self.gizmo_group_init(context, hyperbevels)

            self.highlighted = None
            self.highlighted_adjusted = None
            self.last_highlighted = None
            self.wire_time = 0

            hide_gizmos(self, context)

            get_mouse_pos(self, context, event, window=True)

            self.area = context.area
            self.is_in_3d_view = self.is_mouse_in_3d_view()

            init_status(self, context, func=draw_pick_bevel(self))

            force_ui_update(context)

            init_modal_handlers(self, context, area=False, hud=True)
            return {'RUNNING_MODAL'}

        else:
            draw_fading_label(context, text="No valid HyperBevels found!", y=120, color=red, alpha=1, move_y=40, time=4)
            return {'CANCELLED'}

    def get_hyper_bevels(self):
        hyperbevels = {mod.object: mod for mod in self.active.modifiers if mod.type == 'BOOLEAN' and 'Hyper Bevel' in mod.name and mod.object and mod.object.HC.ishyperbevel}

        invalid = []

        for cutter, mod in hyperbevels.items():

            edge_bevel = cutter.modifiers.get('Edge Bevel')

            if edge_bevel:
                bm = bmesh.new()
                bm.from_mesh(cutter.data)

                edge_glayer = bm.edges.layers.int.get('HyperEdgeGizmo')

                if edge_glayer:
                    continue

            invalid.append(mod.object)

        for cutter in invalid:
            del hyperbevels[cutter]

        return hyperbevels

    def get_init_states(self, hyperbevels):
        self.initial = {'MODIFIERS': [mod.name for mod in self.active.modifiers]}

        self.segments = {}

        for obj, mod in hyperbevels.items():
            edge_bevel = obj.modifiers.get('Edge Bevel')

            bm = bmesh.new()
            bm.from_mesh(obj.data)

            self.initial[mod.name] = {'show_viewport': mod.show_viewport,
                                      'visible': visible_get((obj)),
                                      'segments': edge_bevel.segments,
                                      'profile_type': edge_bevel.profile_type,
                                      'profile': edge_bevel.profile,
                                      'bmesh': bm}

            self.segments[mod.name] = edge_bevel.segments

    def get_highlighted_hyper_bevel(self, context):
        for b in self.gizmo_data['hyperbevels']:
            if b['is_highlight']:
                if b != self.last_highlighted:

                    mod = self.active.modifiers.get(b['modname'])
                    mod.is_active = True

                    force_ui_update(context)
                    self.last_highlighted = b

                return b

        if self.last_highlighted:
            self.last_highlighted = None
            force_ui_update(context)

    def get_preceding_weld_mod(self, obj, bevel_mod):
        all_mods = [mod for mod in obj.modifiers]
        bevel_index = all_mods.index(bevel_mod)

        if bevel_index >= 1:
            prev_mod = all_mods[bevel_index - 1]

            if prev_mod.type == 'WELD' and (prev_mod.name.startswith('- ') or bevel_mod.name.startswith('+ ')):
                return prev_mod

    def is_mouse_in_3d_view(self):
        area_coords = {'x': (self.area.x, self.area.x + self.area.width),
                       'y': (self.area.y, self.area.y + self.area.height)}

        if area_coords['x'][0] < self.mouse_pos_window.x < area_coords['x'][1]:
            return area_coords['y'][0] < self.mouse_pos_window.y < area_coords['y'][1]
        return False

def draw_edit_hyper_bevel_status(op):
    def draw(self, context):
        layout = self.layout

        row = layout.row(align=True)
        row.label(text='Edit Hyper Bevel')

        draw_status_item(row, key='LMB', text="Finish")
        draw_status_item(row, key='RMB', text="Cancel")

        if op.is_hypermod_invocation:
            draw_status_item(row, active=False, text="Returns to HyperMod", gap=1)

            row.separator(factor=2)

        else:
            row.separator(factor=10)

        if op.is_valid:
            draw_status_item(row, active=bool(op.weld), key='ALT', text="Weld")

            draw_status_item(row, key='LMB_DRAG', text="Adjust Width", prop=dynamic_format(op.amount, decimal_offset=2), gap=2)

            draw_status_item(row, active=op.relative, key='R', text="Relative", gap=1)

            solver = 'Exact'

            if op.boolean_mod.use_self:
                solver += " + Self Intersection"

            if op.boolean_mod.use_hole_tolerant:
                solver += " + Hole Tolerant"

            draw_status_item(row, key='E', text="Solver", prop=solver, gap=2)

            if not op.is_chamfer:
                draw_status_item(row, active=not op.is_custom_profile, key='MMB_SCROLL', text="Segments", prop=op.segments, gap=2)

            draw_status_item(row, active=op.is_chamfer, key='C', text="Chamfer", gap=2)

            if op.has_custom_profile:
                draw_status_item(row, active=not op.is_chamfer, key='B', text="Profile", prop=op.bevel_mod.profile_type.title(), gap=2)

                if op.is_custom_profile:
                    draw_status_item(row, key='F', text="Flip Profile", gap=1)
                    draw_status_item(row, key='V', text="Flop Profile", gap=1)

            if not op.is_chamfer and not op.is_custom_profile:
                draw_status_item(row, key='T', text="Tension", prop=dynamic_format(op.bevel_mod.profile, decimal_offset=1), gap=2)

            draw_status_item(row, active=op.is_smooth, key='S', text="Smooth Shading", gap=2)

        else:
            row.label(text="Hyper Bevel will be removed when finishing the Operator!", icon='ERROR')

    return draw

class EditHyperBevel(bpy.types.Operator, Settings, PickHyperBevelGizmoManager):
    bl_idname = "machin3.edit_hyper_bevel"
    bl_label = "MACHIN3: Edit Hyper Bevel"
    bl_options = {'REGISTER', 'UNDO'}

    modname: StringProperty()
    objname: StringProperty()  # objname here is the name of the host object carrying the hyper bevel (boolean) mod

    amount: FloatProperty(name="Amount", default=0)
    segments: IntProperty(name="Segments", default=6, min=0)
    profile_segments: IntProperty(name="Bevel Profile Segments", default=0, min=0)
    is_chamfer: BoolProperty(name="Chamfer", default=False)
    relative: BoolProperty(name="Relative", default=True)
    is_profile_drop: BoolProperty(name="is Profile Drop", default=False)
    has_custom_profile: BoolProperty(name="has Custom Profile", default=False)
    is_smooth: BoolProperty(name="is Smooth Shaded", default=False)
    is_hypermod_invocation: BoolProperty()

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            return True

    @classmethod
    def description(cls, context, properties):
        profile = Settings().fetch_setting('hyper_bevel', 'custom_profile')
        desc = "Edit Hyper Bevel"

        if profile:
            desc += "\nALT: Repeat previous Custom Profile"

        return desc

    def draw_HUD(self, context):
        if context.area == self.area:

            draw_init(self)

            dims = draw_label(context, title='Edit ', coords=Vector((self.HUD_x, self.HUD_y)), color=green, center=False, alpha=1)
            dims += draw_label(context, title=f'{self.boolean_mod.name} ', coords=Vector((self.HUD_x + dims.x, self.HUD_y)), color=white, center=False, alpha=1)

            if self.is_shift:
                draw_label(context, title='a little', coords=Vector((self.HUD_x + dims.x, self.HUD_y)), color=white, center=False, size=10, alpha=0.5)

            elif self.is_ctrl:
                draw_label(context, title='a lot', coords=Vector((self.HUD_x + dims.x, self.HUD_y)), color=white, center=False, size=10, alpha=0.5)

            if self.is_valid:

                self.offset += 18
                color, alpha = (white, 0.5) if self.is_tension_adjusting else (yellow, 1)
                dims = draw_label(context, title=f'Width: {dynamic_format(self.width, decimal_offset=2)} ', coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, color=color, center=False, alpha=alpha)

                if self.relative:
                    color, alpha = (white, 0.2) if self.is_tension_adjusting else (blue, 1)
                    draw_label(context, title='Relative', coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, color=color, center=False, alpha=alpha)

                if not self.is_custom_profile and not self.is_chamfer:
                    self.offset += 18
                    color, alpha = (yellow, 1) if self.is_tension_adjusting else (white, 0.5)
                    draw_label(context, title=f'Tension: {dynamic_format(self.bevel_mod.profile, decimal_offset=1)}', coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, color=color, center=False, alpha=alpha)

                self.offset += 18
                if self.is_chamfer:
                    dims = draw_label(context, title="Chamfer ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, color=blue, center=False, alpha=1)

                    if self.has_custom_profile:
                        draw_label(context, title="🌠", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=blue, alpha=1)

                else:
                    alpha = 0.3 if (self.is_custom_profile or self.segments == 0) else 1
                    segments = self.profile_segments if self.is_custom_profile else self.segments

                    dims = draw_label(context, title=f"Segments: {segments} ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, color=white, center=False, alpha=alpha)

                    if self.has_custom_profile:
                        text = "Custom Profile" if self.is_custom_profile else "🌠"
                        draw_label(context, title=text, coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=blue, alpha=1)

                if self.weld:
                    self.offset += 18
                    draw_label(context, title='Weld', coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, color=yellow, center=False, alpha=1)

                mod = self.boolean_mod

                if mod.use_self or mod.use_hole_tolerant:
                    self.offset += 18

                    title = "Self Intersection" if mod.use_self else "Hole Tolerant"
                    draw_label(context, title=title, coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, color=yellow, center=False, alpha=1)

                    if mod.use_self and mod.use_hole_tolerant:
                        title = "  + Hole Tolerant"
                        self.offset += 18
                        draw_label(context, title=title, coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, color=yellow, center=False, alpha=1)

                if self.is_smooth:
                    self.offset += 18

                    draw_label(context, title="Smooth", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, color=blue, center=False, alpha=1)

                if not self.is_chamfer and self.is_custom_profile and self.profile_HUD_coords:
                    draw_line(self.profile_HUD_coords, width=2, color=blue, alpha=0.75)
                    draw_line(self.profile_HUD_border_coords, width=1, color=white, alpha=0.1)

                    for dir, origin in self.profile_HUD_edge_dir_coords:
                        draw_vector(dir, origin=origin, color=blue, fade=True)

            else:
                self.offset += 18
                draw_label(context, title='Auto Remove', coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, color=red, center=False, alpha=1)

    def modal(self, context, event):
        if ignore_events(event):
            return {'RUNNING_MODAL'}

        context.area.tag_redraw()

        update_mod_keys(self, event)

        self.is_custom_profile = self.has_custom_profile and self.bevel_mod.profile_type == 'CUSTOM'

        if not self.is_custom_profile and not self.is_chamfer and event.type == 'T':
            if event.value == 'PRESS':
                self.is_tension_adjusting = True
                context.window.cursor_set('SCROLL_Y')

            elif event.value == 'RELEASE':
                self.is_tension_adjusting = False
                context.window.cursor_set('SCROLL_X')

        events = ['MOUSEMOVE', 'C', 'R', 'X', 'Y', 'Z', 'E', 'S', 'W', *shift, *ctrl, *alt]

        if self.has_custom_profile:
            events.append('B')

        if self.is_custom_profile:
            events.extend(['F', 'V'])

        if event.type in events or scroll(event, key=True):

            if event.type == 'MOUSEMOVE':
                get_mouse_pos(self, context, event)

                if self.is_custom_profile:
                    self.get_profile_HUD_coords(context)

                if self.is_tension_adjusting:
                    wrap_mouse(self, context, y=True)

                    divisor = get_mousemove_divisor(event, 3, 15, 1, sensitivity=50)

                    delta_y = self.mouse_pos.y - self.last_mouse.y
                    delta_tension = delta_y / divisor
                    self.bevel_mod.profile += delta_tension

                else:
                    wrap_mouse(self, context, x=True)

                    divisor = get_mousemove_divisor(event, 3, 15, 1)

                    delta_x = self.mouse_pos.x - self.last_mouse.x
                    delta_amount = delta_x / divisor * self.factor
                    self.amount += delta_amount

                    self.adjust_hyper_bevel_width(self.amount)

                force_ui_update(context)

            elif not self.is_chamfer and not self.is_custom_profile and scroll(event, key=True):
                if scroll_up(event, key=True):
                    self.segments += 1

                elif scroll_down(event, key=True):
                    self.segments -= 1

                self.bevel_mod.segments = self.segments + 1

            elif event.type == 'C' and event.value == 'PRESS':
                self.is_chamfer = not self.is_chamfer
                self.bevel_mod.segments = 1 if self.is_chamfer else self.profile_segments + 1 if self.is_custom_profile else self.segments + 1

            elif event.type == 'B' and event.value == 'PRESS':

                if self.is_custom_profile:

                    if self.is_chamfer:
                        self.is_chamfer = False
                        self.bevel_mod.segments = self.profile_segments + 1
                        return {'RUNNING_MODAL'}

                    else:

                        self.bevel_mod.profile_type = 'SUPERELLIPSE'
                        self.bevel_mod.segments = self.segments + 1

                else:

                    if self.is_chamfer:
                        self.is_chamfer = False

                    self.bevel_mod.profile_type = 'CUSTOM'
                    self.bevel_mod.segments = self.profile_segments + 1

                    self.get_profile_HUD_coords(context)

                self.is_custom_profile = self.has_custom_profile and self.bevel_mod.profile_type == 'CUSTOM'

            elif event.type == 'F' and event.value == 'PRESS':
                flip_bevel_profile(self.bevel_mod)

                self.get_profile_HUD_coords(context)

            elif event.type == 'V' and event.value == 'PRESS':
                flop_bevel_profile(self.bevel_mod)

                self.get_profile_HUD_coords(context)

            elif event.type == 'E' and event.value == 'PRESS':
                mod = self.boolean_mod

                if bpy.app.version >= (4, 5, 0):
                    modes = ['MANIFOLD', 'EXACT', 'EXACT_SELF', 'EXACT_HOLES', 'EXACT_SELF_HOLES']
                else:
                    modes = ['EXACT', 'EXACT_SELF', 'EXACT_HOLES', 'EXACT_SELF_HOLES']

                if mod.solver == 'EXACT':
                    if mod.use_self and mod.use_hole_tolerant:
                        mode = 'EXACT_SELF_HOLES'

                    elif mod.use_self:
                        mode = 'EXACT_SELF'

                    elif mod.use_hole_tolerant:
                        mode = 'EXACT_HOLES'

                    else:
                        mode = 'EXACT'

                elif mod.solver == 'MANIFOLD':
                    mode = 'MANIFOLD'

                else:
                    mode = 'EXACT'

                if event.shift:
                    next_mode = step_list(mode, modes, step=-1, loop=True)

                else:
                    next_mode = step_list(mode, modes, step=1, loop=True)

                if next_mode == 'MANIFOLD':
                    mod.solver = 'MANIFOLD'

                elif next_mode == 'EXACT':
                    mod.solver = 'EXACT'
                    mod.use_self = False
                    mod.use_hole_tolerant = False

                elif next_mode == 'EXACT_SELF':
                    mod.solver = 'EXACT'
                    mod.use_self = True
                    mod.use_hole_tolerant = False

                elif next_mode == 'EXACT_HOLES':
                    mod.solver = 'EXACT'
                    mod.use_self = False
                    mod.use_hole_tolerant = True

                elif next_mode == 'EXACT_SELF_HOLES':
                    mod.solver = 'EXACT'
                    mod.use_self = True
                    mod.use_hole_tolerant = True

            elif event.type == 'R' and event.value == 'PRESS':
                self.relative = not self.relative

                self.adjust_hyper_bevel_width(self.amount)

                force_ui_update(context)

            elif event.type in ['Y', 'Z'] and event.value == 'PRESS':
                self.bevel_mod.profile = 0.5

            elif event.type == 'X' and event.value == 'PRESS':
                self.bevel_mod.profile = 0.6

            elif event.type in [*alt, 'W'] and event.value == 'PRESS':

                if self.weld:
                    remove_mod(self.weld)
                    self.weld = None

                else:
                    self.weld = self.add_weld_before_hyper_bevel(self.active, self.boolean_mod)

            elif event.type == 'S' and event.value == 'PRESS':
                self.is_smooth = not self.is_smooth

                shade(self.cutter.data, self.is_smooth)

        if event.type in ['LEFTMOUSE', 'SPACE']:
            self.finish(context)

            if not self.is_valid:

                for b in self.gizmo_data['hyperbevels']:
                    if b['modname'] == self.modname and b['obj'] == self.cutter:
                        b['remove'] = True

            if self.is_profile_drop and self.cutter.HC.get('hyperbevel_init_profile', None):
                del self.cutter.HC['hyperbevel_init_profile']

            self.store_settings('hyper_bevel', {'width': self.width, 'segments': self.segments, 'chamfer': self.is_chamfer})

            if self.is_custom_profile:
                profile = get_bevel_profile_as_dict(self.bevel_mod)
                self.store_settings('hyper_bevel', {'custom_profile': profile})

            else:
                self.store_settings('hyper_bevel', {'custom_profile': None})

            if self.is_hypermod_invocation:
                bpy.ops.machin3.hyper_modifier('INVOKE_DEFAULT', is_gizmo_invocation=False, is_button_invocation=False, mode='PICK')

            return {'FINISHED'}

        elif event.type in ['RIGHTMOUSE', 'ESC']:
            self.finish(context)

            self.initbm.to_mesh(self.cutter.data)
            self.initbm.free()

            if not self.boolean_mod.show_viewport:
                self.boolean_mod.show_viewport = True

            if self.is_profile_drop and (data := self.cutter.HC.get('hyperbevel_init_profile', None)):
                set_bevel_profile_from_dict(self.bevel_mod, dict(data))

                del self.cutter.HC['hyperbevel_init_profile']

            else:
                for prop, value in self.initial.items():
                    if prop in ['segments', 'profile', 'profile_type']:
                        mod = self.bevel_mod

                    elif prop in ['solver', 'use_self', 'use_hole_tolerant']:
                        mod = self.boolean_mod

                    elif prop == 'weld':
                        weld = self.get_weld_mod(self.active, self.boolean_mod)

                        if value and not weld:
                            self.add_weld_before_hyper_bevel(self.active, self.boolean_mod)

                        elif not value and weld:
                            remove_mod(weld)

                        continue

                    setattr(mod, prop, value)

            if self.is_hypermod_invocation:
                bpy.ops.machin3.hyper_modifier('INVOKE_DEFAULT', is_gizmo_invocation=False, is_button_invocation=False, mode='PICK')

            return {'CANCELLED'}

        self.last_mouse = self.mouse_pos

        return {'RUNNING_MODAL'}

    def finish(self, context):
        finish_modal_handlers(self)

        finish_status(self)

        self.active.show_wire = False

        context.window.cursor_set('DEFAULT')

        self.gizmo_props['show'] = True

    def invoke(self, context, event):
        self.active = bpy.data.objects[self.objname]
        self.boolean_mod = self.active.modifiers.get(self.modname, None)

        if self.boolean_mod:
            if self.boolean_mod.show_viewport:

                self.active.modifiers.active = self.boolean_mod

                self.cutter = self.boolean_mod.object

                if self.cutter:
                    self.bevel_mod = self.cutter.modifiers.get('Edge Bevel', None)

                    if self.bevel_mod:
                        self.mx = self.cutter.matrix_world
                        loc, _, _ = self.mx.decompose()

                        self.initbm = bmesh.new()
                        self.initbm.from_mesh(self.cutter.data)
                        self.initbm.normal_update()
                        self.initbm.verts.ensure_lookup_table()

                        edge_glayer = self.initbm.edges.layers.int.get('HyperEdgeGizmo')

                        if edge_glayer:
                            center_edges = []

                            for e in self.initbm.edges:
                                if e[edge_glayer] == 1:
                                    center_edges.append(e)

                            if center_edges:
                                self.data = self.get_hyper_bevel_side_data(center_edges, debug=False)

                                if self.data:

                                    self.amount = 0     # what the operator uses to change the width, it's a relative value
                                    self.is_chamfer = self.bevel_mod.profile_type == 'CUSTOM' and self.bevel_mod.segments == 1
                                    self.segments = self.bevel_mod.segments - 1
                                    self.is_smooth = self.cutter.data.polygons[0].use_smooth

                                    update_mod_keys(self)

                                    self.is_valid = True
                                    self.is_tension_adjusting = False
                                    self.weld = self.get_weld_mod(self.active, self.boolean_mod)

                                    self.has_custom_profile = len(self.bevel_mod.custom_profile.points) > 2
                                    self.is_custom_profile = self.has_custom_profile and self.bevel_mod.profile_type == 'CUSTOM'

                                    self.profile_segments = len(self.bevel_mod.custom_profile.points) - 2

                                    self.initial = {'segments': self.bevel_mod.segments,
                                                    'profile': self.bevel_mod.profile,
                                                    'profile_type': self.bevel_mod.profile_type,

                                                    'solver': self.boolean_mod.solver,
                                                    'use_self': self.boolean_mod.use_self,
                                                    'use_hole_tolerant': self.boolean_mod.use_hole_tolerant,

                                                    'weld': bool(self.weld)}

                                    if event.alt:

                                        if profile := self.fetch_setting('hyper_bevel', 'custom_profile'):
                                            set_bevel_profile_from_dict(self.bevel_mod, profile)

                                        return {'FINISHED'}

                                    self.factor = get_zoom_factor(context, loc, scale=10, debug=False)

                                    self.active.show_wire = True

                                    get_mouse_pos(self, context, event)

                                    self.last_mouse = self.mouse_pos

                                    self.get_profile_HUD_coords(context)

                                    context.window.cursor_set('SCROLL_X')

                                    self.gizmo_props['show'] = False

                                    init_status(self, context, func=draw_edit_hyper_bevel_status(self))

                                    init_modal_handlers(self, context, hud=True)
                                    return {'RUNNING_MODAL'}

                                else:
                                    print("unsupported hyper bevel geometry")
                            else:
                                print("no center edges found, not valid hyper bevel object")
                        else:
                            print("no edge glayer found, not a valid hyper bevel object")

            else:
                draw_fading_label(context, text="You can't edit a disabled Hyper Bevel", color=red, time=2)

        return {'CANCELLED'}

    def get_hyper_bevel_side_data(self, center_edges, debug=False):
        data = {}

        if debug:
            print("center edges:", [e.index for e in center_edges])

        sequences = get_edges_as_vert_sequences(center_edges, debug=False)

        if len(sequences) == 1:
            sorted_center_verts, cyclic = sequences[0]

            for idx, v in enumerate(sorted_center_verts):

                if idx == 0:
                    dir = (sorted_center_verts[1].co - v.co).normalized()

                    loop = [l for l in v.link_loops if l.edge in center_edges][0]

                    left_dir = loop.face.normal

                    rail_edge = loop.link_loop_prev.link_loop_prev.edge
                    i = intersect_line_line(v.co, v.co + left_dir, rail_edge.verts[0].co, rail_edge.verts[1].co)

                    self.width = (i[1] - v.co).length

                    self.width_data = {'center_idx': v.index,
                                       'left_dir': left_dir,
                                       'rail_indices': [rail_edge.verts[0].index, rail_edge.verts[1].index]}

                side_edges = [e for e in v.link_edges if e not in center_edges]

                if len(side_edges) == 2:
                    side_verts = [e.other_vert(v) for e in side_edges]

                    for side_vert in side_verts:
                        dir = side_vert.co - v.co

                        data[side_vert.index] = {'co': side_vert.co.copy(),
                                                 'dir': dir.normalized(),

                                                 'length': dir.length,
                                                 'factor': None,

                                                 'type': 'BOTTOM',
                                                 'center': v.index}

                    top_center_vert = None

                    for e in side_edges:

                        loop = [l for l in e.link_loops if l.vert == v][0]

                        if len(loop.face.verts) == 4:
                            top_side_loop = loop.link_loop_next.link_loop_radial_next.link_loop_next.link_loop_next.link_loop_radial_next.link_loop_next

                            top_side_edge = top_side_loop.edge
                            top_side_vert = top_side_loop.vert

                        else:
                            top_side_loop = loop.link_loop_next.link_loop_next

                            top_side_edge = top_side_loop.edge
                            top_side_vert = top_side_loop.vert

                        if not top_center_vert:
                            top_center_vert = top_side_edge.other_vert(top_side_vert)

                        bottom_side_vert = loop.link_loop_next.vert

                        data[top_side_vert.index] = {'co': top_side_vert.co.copy(),
                                                     'dir': (top_side_vert.co - top_center_vert.co).normalized(),

                                                     'bottom_index': bottom_side_vert.index,
                                                     'factor': None,

                                                     'type': 'TOP',
                                                     'center': top_center_vert.index}

                else:
                    return

            max_length = max([vdata['length'] for vdata in data.values() if vdata['type'] == 'BOTTOM'])

            for vdata in data.values():
                if vdata['type'] == 'BOTTOM':
                    vdata['factor'] = vdata['length'] / max_length

            for vdata in data.values():
                if vdata['type'] == 'TOP':
                    bidx = vdata['bottom_index']
                    vdata['factor'] = data[bidx]['factor']

        else:
            return

        if debug:
            printd(data)

        return data

    def get_weld_mod(self, obj, bevel_mod):
        all_mods = [mod for mod in obj.modifiers]
        bevel_index = all_mods.index(bevel_mod)

        if bevel_index >= 1:
            prev_mod = all_mods[bevel_index - 1]

            if prev_mod.type == 'WELD' and prev_mod.name.startswith('- '):
                return prev_mod

    def add_weld_before_hyper_bevel(self, obj, hyper_bevel):
        mod = add_weld(obj, distance=0.0001, mode='ALL')

        names = [mo.name for mo in obj.modifiers if mo != mod and mo.type == 'WELD' and 'Weld' in mo.name]

        if names:
            maxidx = get_biggest_index_among_names(names)
            mod.name = f"- Weld.{str(maxidx + 1).zfill(3)}"
        else:
            mod.name = "- Weld"

        modidx = list(obj.modifiers).index(mod)
        bevelidx = list(obj.modifiers).index(hyper_bevel)

        obj.modifiers.move(modidx, bevelidx)
        return mod

    def get_profile_HUD_coords(self, context):
        self.profile_HUD_coords = []
        self.profile_HUD_border_coords = []
        self.profile_HUD_edge_dir_coords = []

        if self.has_custom_profile:
            profile = self.bevel_mod.custom_profile
            points = profile.points

            ui_scale = get_scale(context)
            size = 100

            offset_x = get_text_dimensions(context, text=f"Segments: {len(points) - 2} Custom Profile ")[0]
            offset_y = -(6 * ui_scale) - size

            offset = Vector((offset_x, offset_y))

            for p in points:
                co = Vector((self.HUD_x, self.HUD_y)) + offset + p.location * size
                self.profile_HUD_coords.append(co.resized(3))

            for corner in [(0, 0), (0, 100), (100, 100), (100, 0), (0, 0)]:
                co = Vector((self.HUD_x, self.HUD_y)) + offset + Vector(corner)
                self.profile_HUD_border_coords.append(co.resized(3))

            self.profile_HUD_edge_dir_coords.append((Vector((-size * 0.7, 0, 0)), Vector((self.HUD_x, self.HUD_y, 0)) + offset.resized(3) + Vector((0, size, 0))))
            self.profile_HUD_edge_dir_coords.append((Vector((0, -size * 0.7, 0)), Vector((self.HUD_x, self.HUD_y, 0)) + offset.resized(3) + Vector((size, 0, 0))))

    def adjust_hyper_bevel_width(self, amount):

        bm = self.initbm.copy()
        bm.verts.ensure_lookup_table()

        self.is_valid = True

        new_coords = {}

        for vidx, vdata in self.data.items():
            v = bm.verts[vidx]

            factor = vdata['factor'] if self.relative else 1
            new_co = vdata['co'] + vdata['dir'] * factor * self.amount

            new_coords[v] = new_co

            center = bm.verts[vdata['center']]
            new_dir = (new_co - center.co).normalized()
            dot = new_dir.dot(vdata['dir'])

            if dot <= 0:
                self.is_valid = False

        if self.is_valid:
            for v, co in new_coords.items():
                v.co = co

            center_co = bm.verts[self.width_data['center_idx']].co
            rail_co1 = bm.verts[self.width_data['rail_indices'][0]].co
            rail_co2 = bm.verts[self.width_data['rail_indices'][1]].co
            left_dir = self.width_data['left_dir']

            i = intersect_line_line(center_co, center_co + left_dir, rail_co1, rail_co2)
            self.width = (i[1] - center_co).length

            if not self.boolean_mod.show_viewport:
                self.boolean_mod.show_viewport = True

        else:

            if self.boolean_mod.show_viewport:
                self.boolean_mod.show_viewport = False

        for f in bm.faces:
            f.smooth = self.is_smooth

        bm.to_mesh(self.cutter.data)
        bm.free()

def draw_extend_hyper_bevel_status(op):
    def draw(self, context):
        layout = self.layout

        row = layout.row(align=True)
        row.label(text='Extend Hyper Bevel')

        if op.is_hypermod_invocation:
            draw_status_item(row, key='LMB', text="Finish")

        else:
            draw_status_item(row, key='E', text="Finish")

        draw_status_item(row, key='RMB', text="Cancel")

        if op.is_hypermod_invocation:
            draw_status_item(row, active=False, text="Returns to HyperMod", gap=1)

            row.separator(factor=2)

        else:
            row.separator(factor=10)

        draw_status_item(row, active=op.is_shift, key='SHIFT', text="Both Ends")

    return draw

class ExtendHyperBevel(bpy.types.Operator, PickHyperBevelGizmoManager):
    bl_idname = "machin3.extend_hyper_bevel"
    bl_label = "MACHIN3: Extend Hyper Bevel"
    bl_description = "Extend Hyper Bevel"
    bl_options = {'REGISTER', 'UNDO'}

    objname: StringProperty()  # the objname here is the hyper bevel cutter obj
    modname: StringProperty()  # only used for the HUD

    amount: FloatProperty(name="Extend Amount")

    is_hypermod_invocation: BoolProperty()

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            return True

    def draw_HUD(self, context):
        if context.area == self.area:

            draw_init(self)

            dims = draw_label(context, title='Extend ', coords=Vector((self.HUD_x, self.HUD_y)), color=green, center=False, alpha=1)
            dims += draw_label(context, title=f'{self.modname} ', coords=Vector((self.HUD_x + dims.x, self.HUD_y)), color=white, center=False, alpha=1)

            if self.is_shift:
                draw_label(context, title='both ends', coords=Vector((self.HUD_x + dims.x, self.HUD_y)), color=white, center=False, size=10, alpha=0.5)

            if not self.is_valid:
                self.offset += 18
                dims = draw_label(context, title='Invalid ', coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, color=red, center=False, size=12, alpha=1)
                draw_label(context, title=f"You can't move beyond {'these points' if self.is_shift else 'this point'}", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, color=white, center=False, size=10, alpha=0.5)

    def draw_VIEW3D(self, context):
        if context.area == self.area:
            if self.coords:
                if center := self.coords['center_edges']:
                    draw_line(center, color=yellow, width=2)

                if limits := self.coords['limits']:
                    color, alpha = (white, 0.5) if self.is_valid else (red, 1)
                    draw_points(limits, size=6, color=color, alpha=alpha)

                if batch := self.coords['parent']:
                    draw_batch(batch, color=blue, alpha=0.3)

    def modal(self, context, event):
        if ignore_events(event):
            return {'RUNNING_MODAL'}

        context.area.tag_redraw()

        update_mod_keys(self, event)

        events = ['MOUSEMOVE', *shift]

        if event.type in events:

            if event.type in ['MOUSEMOVE', *shift]:
                get_mouse_pos(self, context, event)

                self.loc = self.get_bevel_end_intersection(context, self.mouse_pos)
                self.amount = self.get_extend_amount(debug=False)

                if self.amount:
                    self.extend_hyper_bevel(both_ends=self.is_shift)

        if self.is_hypermod_invocation and event.type in ['LEFTMOUSE', 'SPACE'] and event.value == 'PRESS':
            self.finish(context)

            bpy.ops.machin3.hyper_modifier('INVOKE_DEFAULT', is_gizmo_invocation=False, is_button_invocation=False, mode='PICK')
            return {'FINISHED'}

        elif not self.is_hypermod_invocation and event.type == 'E' and event.value == 'RELEASE':

            if self.gizmo_data['hyperbevels']:
                force_pick_hyper_bevels_gizmo_update(context)

            self.finish(context)
            return {'FINISHED'}

        elif event.type in ['RIGHTMOUSE', 'ESC']:
            self.initbm.to_mesh(self.active.data)

            self.finish(context)

            if self.is_hypermod_invocation:
                bpy.ops.machin3.hyper_modifier('INVOKE_DEFAULT', is_gizmo_invocation=False, is_button_invocation=False, mode='PICK')

            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def finish(self, context):
        finish_modal_handlers(self)

        self.parent.show_wire = False

        self.gizmo_props['show'] = True

        finish_status(self)

        force_ui_update(context)

    def invoke(self, context, event):
        self.active = bpy.data.objects[self.objname]
        self.mx = self.active.matrix_world

        self.parent = self.active.parent

        if self.active and self.modname and self.parent:

            self.initbm = bmesh.new()
            self.initbm.from_mesh(self.active.data)
            self.initbm.normal_update()
            self.initbm.verts.ensure_lookup_table()

            edge_glayer = self.initbm.edges.layers.int.get('HyperEdgeGizmo')

            if edge_glayer:
                center_edges = []

                for e in self.initbm.edges:
                    if e[edge_glayer] == 1:
                        center_edges.append(e)

                if center_edges:

                    get_mouse_pos(self, context, event)

                    self.coords = {'parent': get_batch_from_mesh(self.parent.data, self.parent.matrix_world)}

                    self.data = self.get_hyper_bevel_end_data(context, center_edges, self.mouse_pos, debug=False)

                    if self.data:

                        self.init_loc = self.get_bevel_end_intersection(context, self.mouse_pos, debug=False)

                        self.loc = self.init_loc
                        self.amount = 0
                        self.is_valid = True

                        update_mod_keys(self)

                        self.parent.show_wire = True

                        self.gizmo_props['show'] = False

                        init_status(self, context, func=draw_extend_hyper_bevel_status(self))

                        init_modal_handlers(self, context, hud=True, view3d=True)
                        return {'RUNNING_MODAL'}

        return {'CANCELLED'}

    def get_hyper_bevel_end_data(self, context, center_edges, mouse_pos, debug=False):

        if debug:
            print("center edges:", [e.index for e in center_edges])

        sequences = get_edges_as_vert_sequences(center_edges, debug=False)

        if len(sequences) == 1:
            sorted_center_verts, cyclic = sequences[0]

            if not cyclic:

                start_vert = sorted_center_verts[0]
                next_vert = sorted_center_verts[1]

                end_vert = sorted_center_verts[-1]
                previous_vert = sorted_center_verts[-2]

                start_co = start_vert.co.copy()
                end_co = end_vert.co.copy()

                start_limit = next_vert.co + (start_co - next_vert.co) * 0.1
                end_limit = previous_vert.co + (end_co - previous_vert.co) * 0.1

                if debug:
                    draw_point(start_limit, mx=self.mx, color=green, modal=False)
                    draw_point(end_limit, mx=self.mx, color=red, modal=False)

                if len(sorted_center_verts) == 2:
                    center = get_center_between_verts(start_vert, end_vert)

                    start_center_limit = center + (start_co - center) * 0.1
                    end_center_limit = center + (end_co - center) * 0.1

                    if debug:
                        draw_point(center, mx=self.mx, modal=False)
                        draw_point(start_center_limit, mx=self.mx, color=green, modal=False)
                        draw_point(end_center_limit, mx=self.mx, color=red, modal=False)
                else:
                    start_center_limit = None
                    end_center_limit = None

                start_dir = (start_co - next_vert.co).normalized()
                end_dir = (end_co - previous_vert.co).normalized()

                if debug:
                    draw_vector(start_dir, start_co.copy(), mx=self.mx, color=green, fade=True, modal=False)
                    draw_vector(end_dir, end_co.copy(), mx=self.mx, color=red, fade=True, modal=False)

                start_co_2D = location_3d_to_region_2d(context.region, context.region_data, self.mx @ start_co)
                end_co_2D = location_3d_to_region_2d(context.region, context.region_data, self.mx @ end_co)

                side ='START' if (start_co_2D - mouse_pos).length < (end_co_2D - mouse_pos).length else 'END'

                if debug:
                    print("side:", side)

                data = {'side': side,

                        'start_indices': [start_vert.index],
                        'start_coords': [start_co],
                        'start_dirs': [start_dir],

                        'start_limit': start_limit,
                        'start_center_limit': start_center_limit,

                        'end_indices': [end_vert.index],
                        'end_coords': [end_co],
                        'end_dirs': [end_dir],

                        'end_limit': end_limit,
                        'end_center_limit': end_center_limit,

                        'center_indices': [v.index for v in sorted_center_verts],
                        }

                start_face = [f for f in start_vert.link_faces if len(f.verts) > 4][0]
                end_face = [f for f in end_vert.link_faces if len(f.verts) > 4][0]

                for face in [start_face, end_face]:
                    bevel_side = 'start' if face == start_face else 'end'
                    cap_verts = [v for v in face.verts if v not in [start_vert, end_vert]]
                    cap_edges = [e for e in face.edges]

                    for v in cap_verts:
                        data[f'{bevel_side}_indices'].append(v.index)
                        data[f'{bevel_side}_coords'].append(v.co.copy())

                        dir_edge = [e for e in v.link_edges if e not in cap_edges][0]
                        other_v = dir_edge.other_vert(v)

                        data[f'{bevel_side}_dirs'].append((v.co - other_v.co).normalized())

                if debug:
                    draw_vectors(data['start_dirs'][1:], data['start_coords'][1:], mx=self.mx, color=green, fade=True, alpha=0.3, modal=False)
                    draw_vectors(data['end_dirs'][1:], data['end_coords'][1:], mx=self.mx, color=red, fade=True, alpha=0.3, modal=False)

                self.coords['center_edges'] = [self.mx @ v.co for v in sorted_center_verts]

                self.coords['limits'] =[self.mx @ data[f'{side.lower()}_limit']]

                return data

    def get_bevel_end_intersection(self, context, mouse_pos, debug=False):
        view_origin, view_dir = get_view_origin_and_dir(context, mouse_pos)

        side = self.data['side'].lower()
        ext_origin = self.mx @ self.data[f'{side}_coords'][0]
        ext_dir = self.mx.to_3x3() @ self.data[f'{side}_dirs'][0]

        i = intersect_line_line(ext_origin, ext_origin + ext_dir, view_origin, view_origin + view_dir)

        if i:
            if debug:
                draw_point(i[0], color=yellow, modal=False)
            return i[0]

    def get_extend_amount(self, debug=False):
        move_dir = self.mx.inverted_safe().to_3x3() @ (self.loc - self.init_loc)

        ext_dir = self.data[f'{self.data["side"].lower()}_dirs'][0]
        dot = move_dir.normalized().dot(ext_dir)

        amount = move_dir.length if dot >= 0 else - move_dir.length

        if debug:
            print("amount:", self.amount)

        return amount

    def extend_hyper_bevel(self, both_ends=False):
        bm = self.initbm.copy()
        bm.verts.ensure_lookup_table()

        side = self.data["side"].lower()
        is_single_segment = len(self.data['center_indices']) == 2

        if both_ends:
            if is_single_segment:
                self.coords['limits'] = [self.mx @ self.data['start_center_limit'], self.mx @ self.data['end_center_limit']]
            else:
                self.coords['limits'] = [self.mx @ self.data['start_limit'], self.mx @ self.data['end_limit']]
        else:
            self.coords['limits'] = [self.mx @ self.data[f'{side}_limit']]

        for idx, (vidx, co, dir) in enumerate(zip(self.data[f'{side}_indices'], self.data[f'{side}_coords'], self.data[f'{side}_dirs'])):

            new_co = co + dir * self.amount

            if idx == 0:
                limit_co = self.data[f'{side}_center_limit'] if is_single_segment and both_ends else self.data[f'{side}_limit']
                new_dir = (new_co - limit_co).normalized()
                dot = new_dir.dot(dir)

                self.is_valid = dot > 0

                if not self.is_valid:
                    return

            vert = bm.verts[vidx]
            vert.co = new_co

        if both_ends:
            other_side = 'end' if side == 'start' else 'start'

            for idx, (vidx, co, dir) in enumerate(zip(self.data[f'{other_side}_indices'], self.data[f'{other_side}_coords'], self.data[f'{other_side}_dirs'])):

                new_co = co + dir * self.amount

                if idx == 0:
                    limit_co = self.data[f'{other_side}_center_limit'] if is_single_segment and both_ends else self.data[f'{other_side}_limit']
                    new_dir = (new_co - limit_co).normalized()
                    dot = new_dir.dot(dir)

                    self.is_valid = dot > 0

                    if not self.is_valid:
                        return

                vert = bm.verts[vidx]
                vert.co = co + dir * self.amount

        self.coords['center_edges'] = [self.mx @ bm.verts[idx].co.copy() for idx in self.data['center_indices']]

        bm.to_mesh(self.active.data)
        bm.free()
