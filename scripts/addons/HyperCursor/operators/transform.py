import bpy
from bpy.props import BoolProperty, EnumProperty, IntProperty, FloatProperty, StringProperty
from bpy_extras.view3d_utils import location_3d_to_region_2d, region_2d_to_location_3d

import bmesh
from mathutils import Vector, Matrix, Quaternion
from mathutils.geometry import intersect_line_line, intersect_line_plane, intersect_point_line

from typing import Set, Tuple, Union
from math import degrees, floor, radians, copysign
from uuid import uuid4

from .. import HyperCursorManager as HC

from .. utils.cursor import set_cursor, get_cursor_2d
from .. utils.draw import draw_fading_label, draw_batch, draw_vector, draw_line, draw_point, draw_tris, draw_points, draw_lines, draw_circle, get_text_dimensions, draw_init, draw_label
from .. utils.gizmo import hide_gizmos, restore_gizmos
from .. utils.math import create_rotation_matrix_from_vectors, get_center_between_verts, create_rotation_matrix_from_vertex, create_rotation_matrix_from_edge, create_rotation_matrix_from_face, get_face_center, get_center_between_points, dynamic_format, get_loc_matrix, get_world_space_normal, snap_value, create_rotation_matrix_from_normal, transform_batch
from .. utils.modifier import add_linear_hyper_array, add_radial_hyper_array, add_weld, is_array, set_mod_input, sort_modifiers
from .. utils.object import filter_non_child_objects, get_batch_from_obj, get_eval_bbox, is_wire_object
from .. utils.operator import Settings
from .. utils.property import shorten_float_string, step_enum
from .. utils.raycast import cast_scene_ray
from .. utils.registration import get_addon_prefs, get_prefs
from .. utils.snap import Snap
from .. utils.system import printd
from .. utils.ui import draw_status_item_numeric, draw_status_item_precision, finish_modal_handlers, get_mouse_pos, ignore_events, get_zoom_factor, init_modal_handlers, scroll, update_mod_keys, warp_mouse, wrap_mouse, init_status, finish_status, scroll_up, scroll_down, force_ui_update, navigation_passthrough, get_flick_direction, get_scale, is_on_screen, draw_status_item
from .. utils.view import get_location_2d, get_view_origin_and_dir
from .. utils.workspace import is_3dview

from .. colors import red, blue, green, yellow, axis_red, axis_green, axis_blue, white, orange, normal
from .. items import numeric_input_event_items, transform_mode_items, axis_items, axis_vector_mappings, axis_constraint_mappings, transform_snap_face_center_items, array_mode_items, ctrl, shift, alt, axis_color_mappings, numbers, input_mappings

def draw_transform_status(op):
    def draw(self, context):
        layout = self.layout

        row = layout.row(align=True)

        snap_element = op.snap_element.title() if op.snap_element else 'None'
        face_center = op.snap_face_center.title().replace('Median_', '').replace('Projected_', '')

        if op.is_array:
            if op.is_drag_snapping:
                text = f"Linear Array Drag Snap to {snap_element}"

            elif op.is_move_snapping:
                if len(op.snap_proximity_coords) == 3:
                    text = "Linear Array Parallel Edge Center Snap"

                else:
                    text = f"Linear Array {snap_element} Proximity Snap"

            elif op.mode in ['TRANSLATE', 'DRAG']:
                text = "Linear Array"

            elif op.mode == 'ROTATE':
                text = "Radial Array"

            else:
                text = "Array"   # just to silence pyright

        else:
            if op.is_limited_cursor_from_pie_setting:
                if op.only_set_cursor_location:
                    text = "Only Set Cursor Location"
                elif op.only_set_cursor_rotation:
                    text = "Only Set Cursor Rotation"
                else:
                    return

            else:

                if op.is_drag_snapping:
                    text = f"Drag Snap Cursor to {snap_element}"

                elif op.is_move_snapping:
                    if len(op.snap_proximity_coords) == 3:
                        text = "Translate Snap Cursor to Parallel Edge Center"

                    else:
                        text = f"Translate Snap Cursor to {snap_element} Proximity"

                elif op.is_angle_snapping:
                    text = "Angle Snap Rotate Cursor"

                else:
                    text = f"{op.mode.title()} Cursor"

        row.label(text=text)

        if op.is_numeric_input:
            draw_status_item(row, key='RETURN', text="Finish")
            draw_status_item(row, key='MMB', text="Viewport")
            draw_status_item(row, key='ESC', text="Cancel")

            draw_status_item(row, key='TAB', text="Abort Numeric Input")

            draw_status_item_numeric(op, row, invert=True, gap=10)

            return

        else:
            draw_status_item(row, key='LMB', text="Finish")

            if op.mode in ['TRANSLATE', 'DRAG']:
                draw_status_item(row, key='MMB', text="Viewport")

            draw_status_item(row, key='RMB', text="Cancel")

            draw_status_item(row, key='TAB', text="Enter Numeric Input")

            row.separator(factor=10)

        if op.is_array:
            draw_status_item(row, key='MMB_SCROLL', text="Array Count", prop=op.array_count)

            draw_status_item(row, key='A', text="Array Mode", prop=op.array_mode.title(), gap=1)

            if op.mode == 'ROTATE':

                if op.array_mode == 'ADD':
                    draw_status_item(row, active=op.array_full, key='F', text="Full", gap=1)

                    if op.array_mode == 'ADD' and op.array_full:
                        draw_status_item(row, active=op.array_weld, key='W', text="Weld", gap=1)

                elif op.array_mode == 'FIT':
                    draw_status_item(row, active=op.array_flip, key='F', text="Flip", gap=1)

            draw_status_item(row, active=op.array_center, key='C', text="Center", gap=1)

            if op.mode in ['TRANSLATE', 'DRAG']:
                draw_status_item(row, active=op.is_drag_snapping or op.is_move_snapping, key='CTRL', text="Snap", gap=2)

                if (op.is_drag_snapping or op.is_move_snapping) and snap_element == 'Grid':

                    if op.is_drag_snapping:
                        draw_status_item(row, active=op.is_grid_sliding, key='SHIFT', text=f"Slide on {snap_element}", gap=1)

                    if not op.is_grid_sliding:
                        draw_status_item(row, active=bool(op.grid_incremental), key=['ALT','MMB_SCROLL'], text="Grid Incremental", prop=f"1/{pow(10, op.grid_incremental)}" if op.grid_incremental else None, gap=1)

            elif op.mode == 'ROTATE' and not (op.array_mode == 'ADD' and op.array_full):
                draw_status_item(row, active=op.is_angle_snapping, key='CTRL', text="Snap to 5° increments", gap=2)

            if op.is_drag_snapping:
                if snap_element in ['Edge', 'Face']:
                    draw_status_item(row, active=bool(op.snap_lock_element), key='SHIFT', text=f"Slide on {snap_element}", gap=1)

                if not op.snap_lock_element:
                    if snap_element in ['Face']:
                        draw_status_item(row, key=['ALT', 'C'], text="Face Center Method", prop=face_center, gap=1)

            return

        if op.mode in ['TRANSLATE', 'DRAG']:

            if not (op.is_limited_cursor_from_pie_setting or op.is_always_drag_snapping):
                draw_status_item(row, active=op.is_drag_snapping or op.is_move_snapping, key='CTRL', text="Snap", gap=2)

            if (op.is_drag_snapping or op.is_move_snapping) and snap_element == 'Grid':

                if op.is_drag_snapping and not op.only_set_cursor_rotation:
                    draw_status_item(row, active=op.is_grid_sliding, key='SHIFT', text=f"Slide on {snap_element}", gap=1)

                if not op.is_grid_sliding:
                    draw_status_item(row, active=bool(op.grid_incremental), key='MMB_SCROLL', text="Grid Incremental", prop=f"1/{pow(10, op.grid_incremental)}" if op.grid_incremental else None, gap=1)

        elif op.mode == 'ROTATE':
            draw_status_item(row, active=op.is_angle_snapping, key='CTRL', text="Snap to 5° increments", gap=2)

        if op.is_drag_snapping:

            if not op.only_set_cursor_rotation:
                if snap_element in ['Edge', 'Face']:
                    draw_status_item(row, active=bool(op.snap_lock_element), key='SHIFT', text=f"Slide on {snap_element}", gap=1)

            if not op.is_limited_cursor_from_pie_setting:
                draw_status_item(row, key='R', text="Rotation", prop='Initial' if op.snap_ignore_rotation else 'Snap', gap=1)

            if op.snap_lock_element:
                if snap_element in ['Face'] and not op.snap_ignore_rotation:
                    draw_status_item(row, active=bool(op.snap_align_coords), key='ALT', text="Align with Edge", gap=1)

            else:
                if snap_element in ['Face']:
                    draw_status_item(row, key='C', text="Face Center Method", prop=face_center, gap=1)

                if not op.snap_ignore_rotation and not op.only_set_cursor_location:

                    if snap_element in ['Vertex', 'Edge']:
                        draw_status_item(row, active=op.snap_is_vert_or_edge_aligned_with_face, key='ALT', text="Align with Face", gap=1)

                        if op.snap_is_vert_or_edge_aligned_with_face:
                            if snap_element == 'Edge':
                                draw_status_item(row, active=op.snap_edge_align_face_and_edge, key='E', text="Edge Alignment", gap=1)

                            if snap_element == 'Vertex' or (snap_element == 'Edge' and not op.snap_edge_align_face_and_edge):
                                draw_status_item(row, key='F', text="Face Alignment", prop="Edge Pair" if op.snap_face_align_edge_pair else "Longest Edge", gap=1)

                    elif snap_element in ['Face']:
                        draw_status_item(row, key='F', text="Face Alignment Method", prop="Edge Pair" if op.snap_face_align_edge_pair else "Longest Edge", gap=1)
                        draw_status_item(row, active=bool(op.snap_align_coords), key='ALT', text="Align with Vert or Edge", gap=1)

        elif not op.is_move_snapping:
            draw_status_item(row, active=bool(op.location_reset_mx), key='G', text="Reset Location", gap=2)
            draw_status_item(row, active=bool(op.rotation_reset_mx), key='R', text="Reset Rotation", gap=1)

        if op.can_move_selection:
            draw_status_item(row, active=op.move_selection_and_cursor, key='Q', text="Move Selection and Cursor", gap=2)
            draw_status_item(row, active=op.move_selection, key='S', text="Move Selection only", gap=1)

            if op.mode == 'DRAG' and op.is_drag_snapping and (op.move_selection or op.move_selection_and_cursor) and not op.snap_ignore_rotation:
                draw_status_item(row, active=op.move_selection_drag_flip, key='X', text="Drag Flip", gap=1)

        draw_status_item(row, active=op.show_absolute_coords, key='A', text="Show Absolute Coords", gap=3)

        if not op.is_array and op.mode == 'DRAG' and op.is_drag_snapping and not op.transform_preset_from_machin3tools:
            transform = 'Orientation' if op.only_set_cursor_rotation else 'Pivot' if op.only_set_cursor_location else 'Pivot and Orientation'
            draw_status_item(row, active=op.drag_snap_set_transform, key='T', text=f"Set Transform {transform}", gap=2)

    return draw

class TransformCursor(bpy.types.Operator, Settings):
    bl_idname = "machin3.transform_cursor"
    bl_label = "MACHIN3: Transform Cursor"
    bl_options = {'REGISTER', 'UNDO'}

    mode: EnumProperty(name='Translate or Rotate the Cursor', items=transform_mode_items, default='TRANSLATE')
    axis: EnumProperty(name='Transformations Axis', items=axis_items, default='Z')
    translate_amount: FloatProperty(name="Translate Amount", default=0)
    rotate_angle: FloatProperty(name="Rotate Angle", default=0)
    draw_axis_distance: IntProperty(default=1000)
    was_native_cursor_display_toggled: BoolProperty(name='Was Native Cursor Display Toggled', default=False)

    snap_face_center: EnumProperty(name='Face Center Method', items=transform_snap_face_center_items, default='PROJECTED_BOUNDS')
    snap_face_align_edge_pair: BoolProperty(name='Align to Face using longest disconnected Edge Pair', default=True)
    snap_edge_align_face_and_edge: BoolProperty(name='Align to Face and Edge', default=False)
    snap_ignore_rotation: BoolProperty(name='Use initial Cursor Rotation or Rotatino of Snapped Element', default=False)
    grid_incremental: IntProperty(default=0, min=0, max=2)
    is_drag_snapping: BoolProperty()
    is_move_snapping: BoolProperty()
    is_angle_snapping: BoolProperty()

    is_array: BoolProperty()

    array_count: IntProperty(name="Array Count", default=2, min=2)
    array_mode: EnumProperty(name="Array Mode", items=array_mode_items, default='ADD')
    array_full: BoolProperty(name="Radial Full Add Array", default=False)
    array_weld: BoolProperty(name="Weld Radial Array", default=False)
    array_flip: BoolProperty(name="Radial Fit Array Flip")
    array_center: BoolProperty(name="Center Offset Array", default=False)

    move_selection: BoolProperty(name="Move Selection", default=False)
    move_selection_and_cursor: BoolProperty(name="Move Selection and Cursor", default=False)
    move_selection_drag_flip: BoolProperty(name="Move Selection Drag Flip", default=True)

    show_absolute_coords: BoolProperty(name="Show Absolute Coords", default=False)
    drag_snap_set_transform: BoolProperty(name="Set Transform Pivot and Orientation to Cursor, when drag-snapping", default=False)

    is_numeric_input: BoolProperty()
    is_numeric_input_marked: BoolProperty()
    numeric_input_amount: StringProperty(name="Numeric Amount", description="Amount of Translation/Rotation entered numerically", default='0')

    passthrough = None
    is_cursor_pie_invocation: BoolProperty(name="Invoke operator from MACHIN3tools Cursor Pie", default=False)
    @classmethod
    def poll(cls, context):
        return context.mode in ['OBJECT', 'EDIT_MESH']

    @classmethod
    def description(cls, context, properties):
        if properties:
            if properties.is_cursor_pie_invocation:
                desc = "Drag the Cursor in Screen Space and optionally snap it to Geometry or the Grid via CTRL"
                desc += "\nALT: Only Set Cursor Location"
                desc += "\nCTRL: Only Set Cursor Rotation"
                return desc

            else:
                if properties.mode == 'TRANSLATE':
                    return f"Move the Cursor along {properties.axis}\nWith a Selection:\n  ALT: Move Selection instead of the Cursor\n  SHIFT: Duplicate-Move Selection in Cursor Space\n{'  CTRL: Linear Array in Cursor Space' if context.mode == 'OBJECT' else ''}"
                elif properties.mode == 'DRAG':
                    return f"Drag the Cursor in Screen Space\nWith a Selection:\n  ALT: Drag Selection instead of the Cursor\n  SHIFT: Duplicate-Drag Selection in Cursor Space\n{'  CTRL: Linear Array in Cursor Space' if context.mode == 'OBJECT' else ''}"
                elif properties.mode == 'ROTATE':
                    return f"Rotate the Cursor around {properties.axis}\nWith a Selection:\n  ALT: Rotate Selection instead of the Cursor\n  SHIFT: Duplicate-Rotate Selection in Cursor Space\n{'  CTRL: Radial Array in Cursor Space' if context.mode == 'OBJECT' else ''}"
        return "Invalid Context"

    def draw_HUD(self, context):
        if context.area == self.area:
            ui_scale = get_scale(context)

            draw_init(self)

            if self.mode == 'ROTATE' and not self.is_numeric_input:
                color = axis_color_mappings[self.axis]
                draw_vector(self.mouse_pos.resized(3) - self.init_cursor_loc_2d.resized(3), origin=self.init_cursor_loc_2d.resized(3), color=color, fade=True)

            if self.is_array:

                title = f"{'Radial' if self.mode == 'ROTATE' else 'Linear'} Array: "
                dims = draw_label(context, title=title, coords=Vector((self.HUD_x, self.HUD_y)), center=False)

                draw_label(context, title=str(self.array_count), coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=yellow)

                self.offset += 18

                dims = draw_label(context, title="Mode: ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, alpha=0.5)

                color = orange if self.array_mode == 'ADD' else blue
                draw_label(context, title=self.array_mode.title(), coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=color)

                if self.mode == 'ROTATE':
                    self.offset += 18

                    is_full_array = self.array_mode == 'ADD' and self.array_full
                    is_center_array = self.array_center and not is_full_array
                    decimal_offset = 0 if self.is_angle_snapping and not is_full_array else 2

                    angle = dynamic_format(self.rotate_amount_deg, decimal_offset=decimal_offset)
                    alpha = 0.2 if (self.array_mode == 'ADD' and self.array_full) else 1

                    if is_full_array:
                        dims = draw_label(context, title="Angle: ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, alpha=0.5)
                        dims += draw_label(context, title=f"{angle}° ", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, alpha=alpha)

                        draw_label(context, title="Full 360°", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=yellow)

                        if self.array_weld:
                            self.offset += 18

                            draw_label(context, title="Weld", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=yellow)

                    else:
                        dims = draw_label(context, title="Angle:", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, alpha=0.5)

                        title = "🖩" if self.is_numeric_input else " "
                        dims += draw_label(context, title=title, coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset + 3, center=False, size=20, color=green, alpha=0.5)

                        if self.is_numeric_input:
                            numeric_dims = draw_label(context, title=f"{self.numeric_input_amount}°", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=green, alpha=1)

                            if self.is_numeric_input_marked:
                                ui_scale = get_scale(context)
                                coords = [Vector((self.HUD_x + dims.x, self.HUD_y - (self.offset - 5) * ui_scale, 0)), Vector((self.HUD_x + dims.x + numeric_dims.x, self.HUD_y - (self.offset - 5) * ui_scale, 0))]
                                draw_line(coords, width=12 + 8 * ui_scale, color=green, alpha=0.1)

                        else:
                            angle = dynamic_format(self.rotate_amount_deg, decimal_offset=0 if self.is_angle_snapping else 2)

                            if is_center_array:
                                half_angle = dynamic_format(self.rotate_amount_deg / 2, decimal_offset=0 if self.is_angle_snapping else 2)
                                dims += draw_label(context, title=f"{half_angle}° ", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, alpha=0.2)
                                dims += draw_label(context, title=f"{angle}° ", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, alpha=1)
                                dims += draw_label(context, title="Center Array ", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=normal, alpha=1)

                            else:
                                dims += draw_label(context, title=f"{angle}° ", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, alpha=1)

                            if self.is_angle_snapping:
                                draw_label(context, title="Angle Snapping", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=yellow, alpha=1)

                    if self.array_mode == 'FIT' and self.array_flip:
                        self.offset += 18

                        color, alpha = (green, 1) if self.array_count > 2 else (white, 0.25)
                        draw_label(context, title="Flipped", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=color, alpha=alpha)

                elif self.mode in ['TRANSLATE', 'DRAG']:
                    self.offset += 18

                    dims = draw_label(context, title="Distance:", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=0.5)

                    title = "🖩" if self.is_numeric_input else " "
                    dims += draw_label(context, title=title, coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset + 3, center=False, size=20, color=green, alpha=0.5)

                    if self.is_numeric_input:
                        numeric_dims = draw_label(context, title=self.numeric_input_amount, coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=green, alpha=1)

                        if self.is_numeric_input_marked:
                            coords = [Vector((self.HUD_x + dims.x, self.HUD_y - (self.offset - 5) * ui_scale, 0)), Vector((self.HUD_x + dims.x + numeric_dims.x, self.HUD_y - (self.offset - 5) * ui_scale, 0))]
                            draw_line(coords, width=12 + 8 * ui_scale, color=green, alpha=0.1)

                    else:
                        if self.array_center:
                            dims += draw_label(context, title=f"{dynamic_format(self.translate_amount / 2, decimal_offset=2)} ", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=0.2)
                            dims += draw_label(context, title=dynamic_format(self.translate_amount, decimal_offset=2), coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=1)

                            draw_label(context, title=" Center Array", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=normal, alpha=1)

                        else:
                            draw_label(context, title=dynamic_format(self.translate_amount, decimal_offset=2), coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=1)

                    if self.is_snapping:

                        self.offset += 18
                        dims = draw_label(context, title="Snapping: ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=yellow)

                        if self.is_move_snapping:
                            if len(self.snap_coords) == 1:
                                dims += draw_label(context, title="Grid " if self.snap_element == 'GRID' else "Vert ", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=yellow if self.snap_element == 'GRID' else red)
                                draw_label(context, title="Proximity", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=0.5)

                                if self.snap_element == 'GRID':
                                    self.offset += 18
                                    dims = draw_label(context, title="🔳 Increment: ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, alpha=0.5)
                                    draw_label(context, title=f"1/{pow(10, self.grid_incremental)}" if self.grid_incremental else 'None', coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, alpha=1 if self.grid_incremental else 0.3)

                            elif len(self.snap_coords) == 2:
                                dims += draw_label(context, title="Edge ", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=red)

                                if len(self.snap_proximity_coords) == 3:
                                    dims += draw_label(context, title="Parallel Center ", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=green)

                                draw_label(context, title="Proximity", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=0.5)

                            else:
                                draw_label(context, title="Nothing", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=0.5)

                        if self.is_drag_snapping:

                            color = yellow if self.snap_element == 'GRID' else red
                            dims += draw_label(context, title=f"{self.snap_element.title()} ", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=color)

                            if self.snap_element == 'FACE' and not self.snap_lock_element:
                                title = self.snap_face_center.title().replace('Median_', '').replace('Projected_', '') + ' Center'
                                draw_label(context, title=title, coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=0.5)

                                self.offset += 18

                            if self.snap_element == 'GRID' and not self.is_grid_sliding:
                                self.offset += 18
                                dims = draw_label(context, title="🔳 Increment: ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, alpha=0.5)
                                draw_label(context, title=f"1/{pow(10, self.grid_incremental)}" if self.grid_incremental else 'None', coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, alpha=1 if self.grid_incremental else 0.3)

            else:

                if self.show_absolute_coords:
                    abs_coords = self.absolute_HUD_coords
                    corner = abs_coords - Vector((50 * ui_scale, 50 * ui_scale))

                    dims_neg = get_text_dimensions(context, "Location: " + self.absolute_HUD_coord_strings[0], size=10)

                    draw_label(context, title="Absolute Cursor Coords", coords=Vector((corner.x - dims_neg.x, corner.y)), offset=0, center=False, size=10, color=blue, alpha=1)

                    dims = draw_label(context, title="Location: ", coords=Vector((corner.x - dims_neg.x, corner.y)), offset=15, center=False, size=10, color=white, alpha=0.5)
                    draw_label(context, title=self.absolute_HUD_coord_strings[0], coords=Vector((corner.x - dims_neg.x + dims.x, corner.y)), offset=15, center=False, size=10, color=white, alpha=1)

                    dims = draw_label(context, title="Rotation: ", coords=Vector((corner.x - dims_neg.x, corner.y)), offset=30, center=False, size=10, color=white, alpha=0.5)
                    draw_label(context, title=self.absolute_HUD_coord_strings[1], coords=Vector((corner.x - dims_neg.x + dims.x, corner.y)), offset=30, center=False, size=10, color=white, alpha=1)

                    if not self.passthrough:
                        corner_with_gap = abs_coords - Vector((45 * ui_scale, 40 * ui_scale))
                        midpoint = (corner_with_gap + abs_coords) / 2

                        pointer1 = abs_coords - midpoint
                        pointer2 = corner_with_gap - midpoint

                        draw_vector(pointer1.resized(3), origin=midpoint.resized(3), fade=True, alpha=0.5)
                        draw_vector(pointer2.resized(3), origin=midpoint.resized(3), fade=True, alpha=0.5)

                if self.is_limited_cursor_from_pie_setting:
                    dims = draw_label(context, title="Only Set ", coords=Vector((self.HUD_x, self.HUD_y)), center=False, alpha=0.5)
                    dims += draw_label(context, title="Cursor ", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, color=green, alpha=1)

                    if self.only_set_cursor_location:
                        draw_label(context, title="Location", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, alpha=1)

                    elif self.only_set_cursor_rotation:
                        draw_label(context, title="Rotation", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, alpha=1)

                else:
                    dims = draw_label(context, title=f"{self.mode.title()} ", coords=Vector((self.HUD_x, self.HUD_y)), center=False, alpha=1)

                    if self.move_selection or self.move_selection_and_cursor:
                        if self.move_selection:
                            dims += draw_label(context, title="Selection", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, color=blue, alpha=1)

                        else:
                            dims += draw_label(context, title="Cursor", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, color=green, alpha=1)
                            dims += draw_label(context, title=" and ", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, size=10, alpha=0.5)
                            dims += draw_label(context, title="Selection", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, color=blue, alpha=1)

                    else:
                        dims += draw_label(context, title="Cursor", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, color=green, alpha=1)

                if not (self.mode == 'DRAG' and self.snap_coords):
                    title = ' on ' if self.mode == 'TRANSLATE' else ' around ' if self.mode == 'ROTATE' else ' in '
                    dims += draw_label(context, title=title, coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, size=10, alpha=0.5)

                    title, color = (self.axis, red if self.axis == 'X' else green if self.axis == 'Y' else blue) if self.mode in ['TRANSLATE', 'ROTATE'] else ('View Space', yellow)
                    dims += draw_label(context, title=title, coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, color=color, alpha=1)

                if self.mode == 'DRAG' and self.is_drag_snapping and (self.move_selection or self.move_selection_and_cursor) and self.move_selection_drag_flip and not self.snap_ignore_rotation:
                    dims += draw_label(context, title=" with", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, size=10, alpha=0.5)
                    draw_label(context, title=" Flipped Selection", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, size=10, color=normal)

                if self.mode == 'ROTATE':
                    self.offset += 18

                    dims = draw_label(context, title="Angle:", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, alpha=0.5)

                    title = "🖩" if self.is_numeric_input else " "
                    dims += draw_label(context, title=title, coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset + 3, center=False, size=20, color=green, alpha=0.5)

                    if self.is_numeric_input:
                        numeric_dims = draw_label(context, title=f"{self.numeric_input_amount}°", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=green, alpha=1)

                        if self.is_numeric_input_marked:
                            ui_scale = get_scale(context)
                            coords = [Vector((self.HUD_x + dims.x, self.HUD_y - (self.offset - 5) * ui_scale, 0)), Vector((self.HUD_x + dims.x + numeric_dims.x, self.HUD_y - (self.offset - 5) * ui_scale, 0))]
                            draw_line(coords, width=12 + 8 * ui_scale, color=green, alpha=0.1)

                    else:
                        angle = dynamic_format(self.rotate_amount_deg, decimal_offset=0 if self.is_angle_snapping else 2)
                        dims += draw_label(context, title=f"{angle}° ", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, alpha=1)

                        if self.is_angle_snapping:
                            draw_label(context, title="Angle Snapping", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=yellow, alpha=1)

                elif self.mode in ['TRANSLATE', 'DRAG']:
                    self.offset += 18

                    dims = draw_label(context, title="Distance:", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=0.5)

                    title = "🖩" if self.is_numeric_input else " "
                    dims += draw_label(context, title=title, coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset + 3, center=False, size=20, color=green, alpha=0.5)

                    if self.is_numeric_input:
                        numeric_dims = draw_label(context, title=self.numeric_input_amount, coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=green, alpha=1)

                        if self.is_numeric_input_marked:
                            ui_scale = get_scale(context)
                            coords = [Vector((self.HUD_x + dims.x, self.HUD_y - (self.offset - 5) * ui_scale, 0)), Vector((self.HUD_x + dims.x + numeric_dims.x, self.HUD_y - (self.offset - 5) * ui_scale, 0))]
                            draw_line(coords, width=12 + 8 * ui_scale, color=green, alpha=0.1)

                    else:
                        dims += draw_label(context, title=dynamic_format(self.translate_amount, decimal_offset=2), coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=1)

                    if self.is_drag_snapping:

                        if (self.snap_element in ['EDGE', 'FACE'] and self.snap_lock_element) or (self.snap_element == 'GRID' and self.is_grid_sliding):
                            draw_label(context, title=" Sliding", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=yellow, alpha=1)

                    if self.is_snapping:

                        self.offset += 18
                        dims = draw_label(context, title="Snapping: ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=yellow)

                        if self.is_move_snapping:
                            if len(self.snap_coords) == 1:
                                dims += draw_label(context, title=f"{self.snap_element.title()} ", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=yellow if self.snap_element == 'GRID' else red)
                                draw_label(context, title="Proximity", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=0.5)

                                if self.snap_element == 'GRID':
                                    self.offset += 18
                                    dims = draw_label(context, title="🔳 Increment: ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, alpha=0.5)
                                    draw_label(context, title=f"1/{pow(10, self.grid_incremental)}" if self.grid_incremental else 'None', coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, alpha=1 if self.grid_incremental else 0.3)

                            elif len(self.snap_coords) == 2:
                                dims += draw_label(context, title="Edge ", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=red)

                                if len(self.snap_proximity_coords) == 3:
                                    dims += draw_label(context, title="Parallel Center ", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=green)

                                draw_label(context, title="Proximity", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=0.5)

                            else:
                                draw_label(context, title="Nothing", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=0.5)

                        if self.is_drag_snapping:

                            color = yellow if self.snap_element == 'GRID' else red
                            dims += draw_label(context, title=f"{self.snap_element.title()} ", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=color)

                            if self.snap_element == 'FACE' and not self.snap_lock_element:
                                title = self.snap_face_center.title().replace('Median_', '').replace('Projected_', '') + ' Center'
                                draw_label(context, title=title, coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=0.5)

                                self.offset += 18

                            if not self.only_set_cursor_location:

                                if self.snap_ignore_rotation:
                                    draw_label(context, title="Ignore Snapped Rotation", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=0.5)

                                else:
                                    if self.snap_element in ['VERT', 'EDGE']:

                                        if self.snap_is_vert_or_edge_aligned_with_face:
                                            title = "Edge and Face Aligned " if self.snap_element == 'EDGE' and self.snap_edge_align_face_and_edge else 'Face Aligned '
                                            dims += draw_label(context, title=title, coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=0.5)

                                            if self.snap_element == 'VERT' or (self.snap_element == 'EDGE' and not self.snap_edge_align_face_and_edge):
                                                title = "(Edge Pair)" if self.snap_face_align_edge_pair else "(Longest Edge)"
                                                draw_label(context, title=title, coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=0.25)

                                    elif self.snap_element == 'FACE':

                                        if self.snap_align_coords:
                                            title = f"{'Edge' if len(self.snap_align_coords) == 2 else 'Vertex'} Aligned"
                                            color = yellow if self.snap_align_before_lock else green
                                            draw_label(context, title=title, coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=color)

                                        else:
                                            title = f"{'Edge Pair' if self.snap_face_align_edge_pair else 'Longest Edge'} Aligned"
                                            draw_label(context, title=title, coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=0.5)

                            if self.snap_element == 'GRID' and not self.is_grid_sliding:
                                self.offset += 18
                                dims = draw_label(context, title="🔳 Increment: ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, alpha=0.5)
                                draw_label(context, title=f"1/{pow(10, self.grid_incremental)}" if self.grid_incremental else 'None', coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, alpha=1 if self.grid_incremental else 0.3)

                            if self.drag_snap_set_transform or self.transform_preset_from_machin3tools:
                                self.offset += 18

                                if self.only_set_cursor_rotation:
                                    draw_label(context, title=f"Set Transform Orientation", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=green)

                                elif self.only_set_cursor_location:
                                    draw_label(context, title=f"Set Transform Pivot", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=green)

                                else:
                                    draw_label(context, title=f"Set Transform Pivot and Orientation", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=green)

    def draw_VIEW3D(self, context):
        if context.area == self.area:

            if self.is_array and self.array_coords:

                color = (0.3, 0.5, 1) if self.array_mode == 'FIT' else (1, 0.5, 0.3)

                for name, coords in self.array_coords.items():

                    if len(coords) == 4:
                        draw_lines(coords, color=color, width=2, alpha=1)
                        draw_points(coords, color=color, size=8)

                    elif len(coords) == 6:
                        draw_line(coords[:2], color=normal, width=2, alpha=0.5)
                        draw_points(coords[:2], color=normal, size=4, alpha=0.5)

                        draw_lines(coords[2:], color=color, width=2, alpha=1)
                        draw_points(coords[2:], color=color, size=8)

            if self.is_move_snapping:

                if len(self.snap_coords) == 2:
                    draw_line(self.snap_coords, color=red, width=2, alpha=0.75)

                elif len(self.snap_coords) == 1:
                    draw_point(self.snap_coords[0], color=yellow if self.snap_element == 'GRID' else red, size=10 if self.snap_element == 'GRID' else 6, alpha=0.75)

                if len(self.snap_proximity_coords) == 3:
                    draw_point(self.snap_proximity_coords[0], size=8, color=(1, 0, 0), alpha=0.75)
                    draw_line(self.snap_proximity_coords[1:3], color=(axis_green), width=1, alpha=0.75)

                elif len(self.snap_proximity_coords) == 2:
                    draw_line(self.snap_proximity_coords, color=(1, 0.8, 0.3), width=1, alpha=0.75)

                    if len(self.snap_coords) == 2:
                        draw_line([self.snap_coords[0], self.snap_proximity_coords[1]], color=(1, 0, 0), width=2, alpha=0.2)

                if not self.is_grid_sliding and self.snap_grid_increment_coords[0]:
                    draw_points(self.snap_grid_increment_coords[0], color=yellow, size=4, alpha=0.5)

                    if self.snap_grid_increment_coords[1]:
                        draw_points(self.snap_grid_increment_coords[1], color=yellow, size=2, alpha=0.2)

            if self.is_drag_snapping:

                if self.snap_tri_coords:
                    type, coords = self.snap_tri_coords
                    draw_tris(coords, color=red if type == 'FACE' else yellow, alpha=0.1)

                if self.snap_coords:

                    if len(self.snap_coords) == 2:
                        draw_line(self.snap_coords, color=red, width=2, alpha=0.75)

                    elif self.snap_element == 'GRID':
                        draw_point(self.snap_coords[0], size=10, color=yellow, alpha=0.75)

                    else:
                        draw_point(self.snap_coords[0], size=10, color=red, alpha=0.75)

                if self.snap_align_coords:

                    if len(self.snap_align_coords) == 2:
                        draw_line(self.snap_align_coords, color=(1, 0.8, 0.3) if self.snap_align_before_lock else (axis_green), width=2, alpha=0.75 if self.snap_align_before_lock else 0.99)
                    else:
                        draw_point(self.snap_align_coords[0], color=(1, 0.8, 0.3) if self.snap_align_before_lock else (axis_green), alpha=0.75 if self.snap_align_before_lock else 0.99)

                if self.snap_lock_element:
                    if self.snap_lock_element[0] == 'EDGE':
                        closest = min([(co, (co - self.loc).length) for co in self.snap_lock_element[1:3]], key=lambda x: x[1])
                        draw_line([self.loc, closest[0]], color=red, alpha=0.5)

                    elif self.snap_lock_element[0] == 'FACE':
                        draw_line([self.loc, self.snap_lock_element[1]], color=red, alpha=0.5)

                if not self.is_grid_sliding and self.snap_grid_increment_coords[0]:
                    draw_points(self.snap_grid_increment_coords[0], color=yellow, size=4, alpha=0.5)

                    if self.snap_grid_increment_coords[1]:
                        draw_points(self.snap_grid_increment_coords[1], color=yellow, size=2, alpha=0.2)

            if self.mode in ['TRANSLATE', 'DRAG'] and self.loc:
                draw_point(self.init_loc, size=4, alpha=0.5)

                if self.is_array and self.array_center:
                    move_dir = self.target_loc - self.init_loc
                    half_move_dir = move_dir / 2

                    draw_line([self.init_loc - half_move_dir, self.init_loc + half_move_dir], alpha=1 if self.mode == 'TRANSLATE' else 0.3)

                    draw_line([self.init_loc + half_move_dir, self.target_loc], alpha=0.5 if self.mode == 'TRANSLATE' else 0.15)
                    draw_point(self.target_loc, size=3, alpha=0.3)

                else:
                    draw_line([self.target_loc, self.init_loc], alpha=1 if self.mode == 'TRANSLATE' else 0.3)

            if self.mode in ['DRAG']:
                draw_vector(Vector((2, 0, 0)) * self.zoom_factor * 0.5, origin=Vector((-1, 0, 0)) * self.zoom_factor * 0.5, mx=self.cmx, color=(axis_red), width=2, alpha=1, xray=self.is_drag_snapping)
                draw_vector(Vector((0, 2, 0)) * self.zoom_factor * 0.5, origin=Vector((0, -1, 0)) * self.zoom_factor * 0.5, mx=self.cmx, color=(axis_green), width=2, alpha=1, xray=self.is_drag_snapping)
                draw_vector(Vector((0, 0, 2)) * self.zoom_factor * 0.5, origin=Vector((0, 0, -1)) * self.zoom_factor * 0.5, mx=self.cmx, color=(axis_blue), width=2, alpha=1, xray=self.is_drag_snapping)

            if self.mode in ['TRANSLATE', 'ROTATE']:

                if self.axis == 'X':
                    draw_vector(Vector((self.draw_axis_distance, 0, 0)) * 2, origin=Vector((-self.draw_axis_distance, 0, 0)), mx=self.cmx, color=(axis_red), alpha=0.5)

                    if not self.is_array:

                        if self.mode == 'TRANSLATE':
                            draw_vector(Vector((0, 2, 0)) * self.zoom_factor * 0.5, origin=Vector((0, -1, 0)) * self.zoom_factor * 0.5, mx=self.cmx, color=(axis_green), width=2, alpha=1, xray=False)
                            draw_vector(Vector((0, 0, 2)) * self.zoom_factor * 0.5, origin=Vector((0, 0, -1)) * self.zoom_factor * 0.5, mx=self.cmx, color=(axis_blue), width=2, alpha=1, xray=False)

                        elif self.mode == 'ROTATE':
                            draw_vector(Vector((0, 1, 0)) * self.zoom_factor * 1.2, mx=self.cmx, color=(axis_green), width=2, alpha=1)
                            draw_vector(Vector((0, 0, 1)) * self.zoom_factor * 1.2, mx=self.cmx, color=(axis_blue), width=2, alpha=1)

                elif self.axis == 'Y':
                    draw_vector(Vector((0, self.draw_axis_distance, 0)) * 2, origin=Vector((0, -self.draw_axis_distance, 0)), mx=self.cmx, color=(0.5, 1, 0), alpha=0.5)

                    if not self.is_array:

                        if self.mode == 'TRANSLATE':
                            draw_vector(Vector((2, 0, 0)) * self.zoom_factor * 0.5, origin=Vector((-1, 0, 0)) * self.zoom_factor * 0.5, mx=self.cmx, color=(axis_red), width=2, alpha=1, xray=False)
                            draw_vector(Vector((0, 0, 2)) * self.zoom_factor * 0.5, origin=Vector((0, 0, -1)) * self.zoom_factor * 0.5, mx=self.cmx, color=(axis_blue), width=2, alpha=1, xray=False)

                        elif self.mode == 'ROTATE':
                            draw_vector(Vector((1, 0, 0)) * self.zoom_factor * 1.2, mx=self.cmx, color=(axis_red), width=2, alpha=1)
                            draw_vector(Vector((0, 0, 1)) * self.zoom_factor * 1.2, mx=self.cmx, color=(axis_blue), width=2, alpha=1)

                elif self.axis == 'Z':
                    draw_vector(Vector((0, 0, self.draw_axis_distance)) * 2, origin=Vector((0, 0, -self.draw_axis_distance)), mx=self.cmx, color=(axis_blue), alpha=0.5)

                    if not self.is_array:

                        if self.mode == 'TRANSLATE':
                            draw_vector(Vector((0, 2, 0)) * self.zoom_factor * 0.5, origin=Vector((0, -1, 0)) * self.zoom_factor * 0.5, mx=self.cmx, color=(axis_green), width=2, alpha=1, xray=False)
                            draw_vector(Vector((2, 0, 0)) * self.zoom_factor * 0.5, origin=Vector((-1, 0, 0)) * self.zoom_factor * 0.5, mx=self.cmx, color=(axis_red), width=2, alpha=1, xray=False)

                        elif self.mode == 'ROTATE':
                            draw_vector(Vector((1, 0, 0)) * self.zoom_factor * 1.2, mx=self.cmx, color=(axis_red), width=2, alpha=1)
                            draw_vector(Vector((0, 1, 0)) * self.zoom_factor * 1.2, mx=self.cmx, color=(axis_green), width=2, alpha=1)

            if self.can_move_selection and (self.move_selection or self.move_selection_and_cursor):
                color = green if self.move_selection_and_cursor else blue

                for data in self.selection.values():
                    for batch in data['batches']:
                        draw_batch(batch, color=color, alpha=0.25, xray=True)
                        draw_batch(batch, color=color, alpha=0.5, xray=False)

    def modal(self, context, event):
        if ignore_events(event) and not self.is_init_run:
            return {'RUNNING_MODAL'}

        context.area.tag_redraw()

        update_mod_keys(self, event, shift=not self.only_set_cursor_rotation, ctrl=not self.is_limited_cursor_from_pie_setting, alt=not self.only_set_cursor_location)

        if ret := self.numeric_input(context, event):
            return ret

        else:
            return self.interactive_input(context, event)

    def finish(self, context):
        finish_modal_handlers(self)

        finish_status(self)

        self.S.finish()

        if self.gzm_group:
            self.gzm_group.is_full_array = False

        view = context.space_data
        hc = context.scene.HC

        view.overlay.show_wireframes = self.show_wires

        restore_gizmos(self, debug=False)

        if self.was_native_cursor_display_toggled:
            context.space_data.overlay.show_cursor = True

        if self.is_machin3tools_drawing_cursor_axes:
            context.scene.M3.draw_cursor_axes = True

        hc.track_history = True

        force_ui_update(context)

        if self.is_view_cursor_locked:
            context.space_data.lock_cursor = True

    def invoke(self, context, event):
        HC.init_operator_defaults(self.bl_idname, self.properties, include=['show_absolute_coords', 'drag_snap_set_transform'], debug=False)
        hc = context.scene.HC

        if context.mode == 'EDIT_MESH' and not context.active_object.select_get():
            context.active_object.select_set(True)

        if ret := self.transform_or_duplicate_macro_passthrough(context, event):
            return ret

        self.cursor = context.scene.cursor

        self.gzm_group = context.gizmo_group

        get_mouse_pos(self, context, event)

        self.cmx = self.cursor.matrix
        self.init_cmx = self.cmx.copy()
        self.axis_vector = axis_vector_mappings[self.axis]

        self.init_loc, self.init_rot, _ = self.cmx.decompose()

        self.loc = self.init_loc
        self.target_loc = self.init_loc  # used for drawing of the distance line, when translating the cursor or when setting up a linear array, for for batch matrix creation, NOTE: has to be kept separately from self.loc, to allow for numeric - flipping > self.transform_cursor() only selts self.target_loc for that reason

        self.init_rot_intersect = None
        self.passthrough_offset = Vector()

        self.move_cursor_under_mouse(context)

        self.init_settings(props=['show_absolute_coords', 'snap_ignore_rotation','grid_incremental', 'drag_snap_set_transform', 'move_selection_drag_flip'])

        if self.mode == 'DRAG' and not self.gzm_group:
            self.load_settings()

        self.init_cursor_loc_2d = HC.props['cursor_2d']

        if is_on_screen(context, self.init_cursor_loc_2d):

            self.mouse_offset = self.mouse_pos - self.init_cursor_loc_2d

            self.is_init_run = True   # just used for the timer modal, to ensure immediate, but not constant execution, helpful when RMB snapping right away

            update_mod_keys(self)

            self.translate_amount = 0
            self.rotate_amount = 0
            self.rotate_amount_deg = 0

            self.is_numeric_input = False
            self.is_numeric_input_marked = False
            self.numeric_input_amount = '0'

            self.enforce_cursor_to_origin_reset = False

            self.location_reset_mx = None
            self.rotation_reset_mx = None

            self.show_wires = context.space_data.overlay.show_wireframes
            self.wire_threshold = context.space_data.overlay.wireframe_threshold

            self.zoom_factor = get_zoom_factor(context, self.cursor.location, scale=50, ignore_obj_scale=True)

            hc.track_history = False

            self.prepare_snapping_and_arraying(context, event)

            self.is_view_cursor_locked = context.space_data.lock_cursor

            if self.is_view_cursor_locked:

                viewmx = context.space_data.region_3d.view_matrix.copy()

                context.space_data.lock_cursor = False

                context.space_data.region_3d.view_matrix = viewmx

            self.is_snapping = False

            self.is_drag_snapping = False
            self.is_move_snapping = False
            self.is_angle_snapping = False

            self.is_always_drag_snapping = self.mode =='DRAG' and get_prefs().transform_cursor_default_always_drag_snap
            self.snap_reset_mx = None
            self.snap_coords = []
            self.snap_tri_coords = []
            self.snap_grid_increment_coords = [[], []]
            self.snap_element = None
            self.is_grid_sliding = False

            self.snap_lock_element = None
            self.snap_align_coords = None
            self.snap_align_before_lock = False
            self.snap_is_vert_or_edge_aligned_with_face = False

            self.snap_proximity_coords = []

            self.transform_preset_from_machin3tools = HC.get_addon('MACHIN3tools') and get_addon_prefs('MACHIN3tools').cursor_set_transform_preset and get_prefs().transform_cursor_default_drag_snap_set_transform_machin3tools and self.is_cursor_pie_invocation
            self.only_set_cursor_location = self.is_cursor_pie_invocation and event.alt
            self.only_set_cursor_rotation = self.is_cursor_pie_invocation and not self.only_set_cursor_location and event.ctrl
            self.is_limited_cursor_from_pie_setting = self.is_cursor_pie_invocation and (self.only_set_cursor_location or self.only_set_cursor_rotation)

            self.can_move_selection = context.mode == 'OBJECT' and bool(context.selected_objects) and self.mode in ['DRAG', 'TRANSLATE'] and not self.is_cursor_pie_invocation
            self.move_selection = False
            self.move_selection_and_cursor = False

            if self.can_move_selection and not self.is_array:

                dg = context.evaluated_depsgraph_get()

                self.selection = {obj: {'name': obj.name,
                                        'mx': obj.matrix_world,
                                        'transformed_mx': None,
                                        'local_space_batch': get_batch_from_obj(dg, obj, world_space=False, single_icol_batch=False),
                                        'batches': None} for obj in context.selected_objects}

                self.update_selection_batches()

            self.get_absolute_HUD_coords(context)

            self.disable_blender_cursor(context)

            self.disable_machin3tools_cursor_axis_drawing(context)

            hide_gizmos(self, context, debug=False)

            init_status(self, context, func=draw_transform_status(self))

            force_ui_update(context)

            init_modal_handlers(self, context, hud=True, view3d=True, timer=True, time_step=0.01)
            return {'RUNNING_MODAL'}

        else:
            return {'CANCELLED'}

    def transform_or_duplicate_macro_passthrough(self, context, event):
        if not event.ctrl and (event.alt or event.shift) and (context.selected_objects and context.gizmo_group):

            context.scene.HC.draw_HUD = False

            if event.shift:
                if context.mode == 'OBJECT':
                    bpy.ops.object.duplicate()
                elif context.mode == 'EDIT_MESH':
                    bpy.ops.mesh.duplicate()

            pivot = context.scene.tool_settings.transform_pivot_point
            bpy.context.scene.tool_settings.transform_pivot_point = 'CURSOR'

            if self.mode == 'TRANSLATE':
                bpy.ops.machin3.macro_hyper_cursor_translate('INVOKE_DEFAULT',
                                                              TRANSFORM_OT_translate={'orient_type': 'CURSOR', 'constraint_axis': axis_constraint_mappings[self.axis], 'release_confirm': True},
                                                              WM_OT_context_toggle={'data_path': 'scene.HC.draw_HUD'})

            elif self.mode == 'DRAG':
                bpy.ops.machin3.macro_hyper_cursor_translate('INVOKE_DEFAULT',
                                                              TRANSFORM_OT_translate={'release_confirm': True},
                                                              WM_OT_context_toggle={'data_path': 'scene.HC.draw_HUD'}),

            elif self.mode == 'ROTATE':
                bpy.ops.machin3.macro_hyper_cursor_rotate('INVOKE_DEFAULT',
                                                           TRANSFORM_OT_rotate={'orient_type': 'CURSOR', 'constraint_axis': axis_constraint_mappings[self.axis], 'release_confirm': True},
                                                           WM_OT_context_toggle={'data_path': 'scene.HC.draw_HUD'})
            context.scene.tool_settings.transform_pivot_point = pivot
            return {'FINISHED'}

    def prepare_snapping_and_arraying(self, context, event):
        if context.mode == 'OBJECT' and context.selected_objects and self.gzm_group and event.ctrl:
            self.is_array = True
            self.array_count = 2

            sel = [obj for obj in context.selected_objects if obj.type in ['MESH', 'CURVE'] and not is_wire_object(obj, wire=False)]

            self.S = Snap(context, exclude_wire=True, alternative=sel, modifier_toggles=['BOOLEAN'], debug=False)

            self.arrays = []
            self.array_coords = {}
            self.last_angle = 0  # used for automatic flipping when crossing 0°

            empty = None

            uuid = str(uuid4()) if len(context.selected_objects) > 1 else None

            for obj in sel:
                if self.mode == 'ROTATE':

                    if empty is None:
                        loc = self.init_loc

                        y_dir = self.cmx.to_quaternion() @ axis_vector_mappings[self.axis]

                        obj_loc = obj.matrix_world.to_translation()
                        obj_dir = obj_loc - loc

                        projected = obj_dir.project(y_dir)

                        x_dir = (obj_dir - projected).normalized()

                        if not x_dir.length:
                            x_dir = self.cmx.to_quaternion() @ axis_vector_mappings['X' if self.axis == 'Z' else 'Z']

                        z_dir = x_dir.cross(y_dir)

                        rot = create_rotation_matrix_from_vectors(x_dir, y_dir, z_dir).to_3x3()

                        empty = bpy.data.objects.new(name="Radial Array Origin", object_data=None)
                        context.scene.collection.objects.link(empty)

                        empty.empty_display_type = 'CIRCLE'
                        empty.empty_display_size = (sum(obj.dimensions) / 3) / 3   # that the radius of the empty to a third of the averaged dimensions of obj

                        empty.matrix_world = Matrix.LocRotScale(loc, rot, Vector((1, 1, 1)))

                        empty.hide_set(True)

                    mod = add_radial_hyper_array(obj)
                    set_mod_input(mod, 'Origin', empty)

                else:
                    mod = add_linear_hyper_array(obj)

                if uuid:
                    set_mod_input(mod, 'UUID', uuid)

                obj.update_tag()

                self.arrays.append((obj, mod, empty))

            if self.array_weld:
                self.enable_full_radial_array_weld(context)

        else:
            self.is_array = False
            self.S = Snap(context, exclude_wire=True, debug=False)

    def update_selection_batches(self):
        for obj, data in self.selection.items():
            data['transformed_mx'] = self.get_selection_transform_matrix(data['mx'])

            if data['local_space_batch'][2] == 'INSTANCE_COLLECTION_MULTI_MESH_EVAL':
                batches = data['local_space_batch'][0]
                data['batches'] = [transform_batch(batch, data['transformed_mx']) for batch in batches]

            else:
                data['batches'] = [transform_batch(data['local_space_batch'], data['transformed_mx'])]

    def disable_blender_cursor(self, context):
        if context.space_data.overlay.show_cursor:
            context.space_data.overlay.show_cursor = False

            self.was_native_cursor_display_toggled = True
        else:
            self.was_native_cursor_display_toggled = False

    def disable_machin3tools_cursor_axis_drawing(self, context):
        self.is_machin3tools_drawing_cursor_axes = HC.get_addon('MACHIN3tools') and context.scene.M3.draw_cursor_axes

        if self.is_machin3tools_drawing_cursor_axes:
            context.scene.M3.draw_cursor_axes = False

    def get_transform(self, context) -> Union[Vector, Quaternion]:
        offset = self.mouse_offset if self.mode in ['TRANSLATE', 'DRAG'] else Vector((0, 0))

        view_origin, view_dir = get_view_origin_and_dir(context, self.mouse_pos - offset)

        cursor_origin = self.cursor.location
        cursor_dir = self.init_rot @ self.axis_vector

        if self.mode == 'TRANSLATE':
            i = intersect_line_line(view_origin, view_origin + view_dir, cursor_origin, cursor_origin + cursor_dir)

            if i:
                self.loc = i[1]

                self.translate_amount = (self.loc - self.init_loc).length
                return i[1]

            self.translate_amount = 0
            return self.init_loc

        elif self.mode == 'DRAG':
            i = intersect_line_plane(view_origin, view_origin + view_dir, cursor_origin, view_dir)

            if i:
                self.loc = i

                self.translate_amount = (self.loc - self.init_loc).length

                return i
            self.translate_amount = 0
            return self.init_loc

        elif self.mode == 'ROTATE':
            i = intersect_line_plane(view_origin, view_origin + view_dir, cursor_origin, cursor_dir)

            if i:
                if not self.init_rot_intersect:
                    self.init_rot_intersect = i
                    return self.init_rot

                else:
                    v1 = self.init_rot_intersect - cursor_origin
                    v2 = i - cursor_origin

                    deltarot = v1.rotation_difference(v2).normalized()

                    angle = v1.angle(v2)

                    if self.is_angle_snapping:
                        step = 5

                        dangle = degrees(angle)
                        mod = dangle % step

                        angle = radians(dangle + (step - mod)) if mod >= (step / 2) else radians(dangle - mod)

                        deltarot = Quaternion(deltarot.axis, angle)

                    dot = -round(cursor_dir.dot(deltarot.axis))

                    if self.is_array and self.array_mode == 'FIT':

                        if dot * angle > 0 and self.last_angle < 0 and degrees(angle) < 90:
                            self.array_flip = not self.array_flip

                        elif dot * angle < 0 and self.last_angle > 0 and degrees(angle) < 90:
                            self.array_flip = not self.array_flip

                    if self.is_array:
                        self.last_angle = dot * angle

                    rotation = (deltarot @ self.init_rot).normalized()

                    sign = copysign(1, cursor_dir.dot(deltarot.axis))

                    self.rotate_amount = sign * angle
                    self.rotate_amount_deg = degrees(self.rotate_amount)

                    return rotation
            return self.init_rot

        return self.init_loc

    def get_numeric_transform(self) -> Union[Vector, Quaternion, Tuple[Vector, Quaternion]]:

        if self.mode in ['TRANSLATE', 'DRAG']:
            self.translate_amount = float(self.numeric_input_amount)
            move_dir = (self.loc - self.init_loc).normalized()

            loc = self.init_loc + move_dir * self.translate_amount

            if self.is_array:
                return loc
            else:
                return loc, self.numeric_init_rot

        elif self.mode == 'ROTATE':
            self.rotate_amount_deg = float(self.numeric_input_amount)
            self.rotate_amount = radians(self.rotate_amount_deg)
            rotate = Quaternion(self.axis_vector, radians(self.rotate_amount_deg))

            if self.is_array:
                return self.init_rot @ rotate

            else:
                return self.init_loc, self.init_rot @ rotate

        else:
            return Vector(), Quaternion()

    def get_absolute_HUD_coords(self, context):
        loc, rot, _ = self.cmx.decompose()

        loc_string = f"({', '.join(dynamic_format(l, decimal_offset=2, clear_trailing_zeros=True) for l in loc)})"
        rot_string = f"({', '.join(dynamic_format(degrees(r), decimal_offset=2, clear_trailing_zeros=True) for r in rot.to_euler())})"

        self.absolute_HUD_coord_strings = loc_string, rot_string
        self.absolute_HUD_coords = get_location_2d(context, loc, default='OFF_SCREEN')
    def get_grid_incremental_coords(self, grid, loc):
        if grid == Vector((1, 0, 0)):

            y_floor = floor(loc.y)
            z_floor = floor(loc.z)

            for y in range(11):
                for z in range(11):
                    self.snap_grid_increment_coords[0].append(Vector([0, y_floor + y / 10, z_floor + z / 10]))

            if self.grid_incremental == 2:
                for y in range(101):
                    for z in range(101):
                        self.snap_grid_increment_coords[1].append(Vector([0, y_floor + y / 100, z_floor + z / 100]))

        elif grid == Vector((0, -1, 0)):

            x_floor = floor(loc.x)
            z_floor = floor(loc.z)

            for x in range(11):
                for z in range(11):
                    self.snap_grid_increment_coords[0].append(Vector([x_floor + x / 10, 0, z_floor + z / 10]))

            if self.grid_incremental == 2:
                for x in range(101):
                    for z in range(101):
                        self.snap_grid_increment_coords[1].append(Vector([x_floor + x / 100, 0, z_floor + z / 100]))

        elif grid == Vector((0, 0, 1)):

            x_floor = floor(loc.x)
            y_floor = floor(loc.y)

            for x in range(11):
                for y in range(11):
                    self.snap_grid_increment_coords[0].append(Vector([x_floor + x / 10, y_floor + y / 10, 0]))

            if self.grid_incremental == 2:
                for x in range(101):
                    for y in range(101):
                        self.snap_grid_increment_coords[1].append(Vector([x_floor + x / 100, y_floor + y / 100, 0]))

    def set_cursor_transform_preset(self, scene):
        if self.mode == 'DRAG' and self.is_drag_snapping:
            if self.drag_snap_set_transform or self.transform_preset_from_machin3tools:

                if self.only_set_cursor_rotation:
                    scene.transform_orientation_slots[0].type = 'CURSOR'

                elif self.only_set_cursor_location:
                    scene.tool_settings.transform_pivot_point = 'CURSOR'

                else:
                    scene.transform_orientation_slots[0].type = 'CURSOR'
                    scene.tool_settings.transform_pivot_point = 'CURSOR'

    def get_drag_snap_to_element_transform(self, context, lock=False) -> Union[Tuple[Vector, Quaternion], Tuple[None, None]]:
        alterntative_align = False if self.is_array else self.is_alt

        hitmx = self.S.hitmx
        hitface = self.S.hitface
        hitnormal = self.S.hitnormal

        tri_coords = self.S.cache.tri_coords[self.S.hitobj.name][self.S.hitindex]

        hit_co = hitmx.inverted_safe() @ self.S.hitlocation

        face_weight = 10000 if self.snap_align_before_lock else 100
        edge_weight = 10000 if self.snap_tri_coords and self.snap_tri_coords[0] == 'EDGE' else 1.5
        vert_weight = 10000 if self.snap_tri_coords and self.snap_tri_coords[0] == 'VERT' else 25

        face_distance = (hitface, (hit_co - hitface.calc_center_median_weighted()).length / face_weight)

        vert_distance = min([(v, (hit_co - v.co).length / vert_weight) for v in hitface.verts], key=lambda x: x[1])

        edge = min([(e, (hit_co - intersect_point_line(hit_co, e.verts[0].co, e.verts[1].co)[0]).length, (hit_co - get_center_between_verts(*e.verts)).length) for e in hitface.edges if e.calc_length()], key=lambda x: (x[1] * x[2]) / x[0].calc_length())
        edge_distance = (edge[0], ((edge[1] * edge[2]) / edge[0].calc_length()) / edge_weight)

        closest = min([face_distance, vert_distance, edge_distance], key=lambda x: x[1])

        self.snap_element = closest[0]

        self.snap_tri_coords = []

        self.snap_is_vert_or_edge_aligned_with_face = False

        if isinstance(closest[0], bmesh.types.BMVert):
            self.snap_element = 'VERT'

            loc = hitmx @ closest[0].co

            if self.snap_ignore_rotation:
                rot = self.init_rot.to_matrix()

            else:

                if alterntative_align:
                    rot = create_rotation_matrix_from_face(context, hitmx, hitface, edge_pair=self.snap_face_align_edge_pair)
                    self.snap_is_vert_or_edge_aligned_with_face = True

                    self.snap_tri_coords = ('VERT', tri_coords)

                else:
                    rot = create_rotation_matrix_from_vertex(hitmx, closest[0])

            self.snap_coords = [loc]

        elif isinstance(closest[0], bmesh.types.BMEdge):
            self.snap_element = 'EDGE'

            loc = hitmx @ get_center_between_verts(*closest[0].verts)

            if self.snap_ignore_rotation:
                rot = self.init_rot.to_matrix()

            else:

                if alterntative_align:
                    rot = create_rotation_matrix_from_face(context, hitmx, hitface, edge_pair=self.snap_face_align_edge_pair)
                    self.snap_is_vert_or_edge_aligned_with_face = True

                    if self.snap_edge_align_face_and_edge:
                        bitangent = rot.col[1].xyz
                        edge_dir = hitmx.to_3x3() @ (closest[0].verts[0].co - closest[0].verts[1].co)

                        quat = bitangent.rotation_difference(edge_dir)
                        rot = quat.to_matrix().to_4x4() @ rot

                    self.snap_tri_coords = ('EDGE', tri_coords)

                else:
                    rot = create_rotation_matrix_from_edge(context, hitmx, closest[0])

            self.snap_coords = [hitmx @ v.co for v in closest[0].verts]

            if lock and not self.snap_lock_element:
                self.snap_lock_element = ('EDGE', hitmx @ closest[0].verts[0].co, hitmx @ closest[0].verts[1].co, rot)
                return None, None

        elif isinstance(closest[0], bmesh.types.BMFace):
            self.snap_element = 'FACE'

            loc = hitmx @ get_face_center(closest[0], method=self.snap_face_center)

            if self.snap_ignore_rotation:
                rot = self.init_rot.to_matrix()

            else:

                if alterntative_align:

                    edge_distance = (edge[0], (get_center_between_verts(*edge[0].verts) - hit_co).length)

                    vert_distance = min([(v, (hit_co - v.co).length) for v in hitface.verts], key=lambda x: x[1])

                    self.snap_align_before_lock = True

                    if vert_distance[1] < edge_distance[1]:
                        vert = vert_distance[0]

                        normal = hitnormal.normalized()
                        tangent = (hitmx @ vert.co - loc).normalized()
                        binormal = normal.cross(tangent)

                        self.snap_align_coords = [hitmx @ vert.co]

                    else:
                        edge = edge_distance[0]

                        normal = hitnormal.normalized()
                        binormal = (hitmx @ edge.verts[1].co - hitmx @ edge.verts[0].co).normalized()
                        tangent = binormal.cross(normal).normalized()

                        view_up = context.space_data.region_3d.view_rotation @ Vector((0, 1, 0))
                        binormal_dot = binormal.dot(view_up)

                        if binormal_dot < 0:
                            binormal, tangent = -binormal, -tangent

                        self.snap_align_coords = [hitmx @ v.co for v in edge.verts]

                    rot = Matrix()
                    rot.col[0].xyz = tangent
                    rot.col[1].xyz = binormal
                    rot.col[2].xyz = normal

                else:
                    rot = create_rotation_matrix_from_face(context, hitmx, closest[0], edge_pair=self.snap_face_align_edge_pair)
                    self.snap_align_before_lock = False

            self.snap_coords = [loc]

            self.snap_tri_coords = ('FACE', tri_coords)

            if lock and not self.snap_lock_element:

                hitface_edge_cos = [[hitmx @ v.co for v in e.verts] for e in hitface.edges]

                self.snap_lock_element = ('FACE', loc, get_world_space_normal(closest[0].normal, hitmx), rot, hitface_edge_cos)
                return None, None

        self.loc = loc

        self.translate_amount = (self.loc - self.init_loc).length

        return loc, rot.to_quaternion()

    def get_drag_snap_to_locked_element_transform(self, context) -> Tuple[Vector, Quaternion]:
        alternative_align = False if self.is_array else self.is_alt
        lock = self.snap_lock_element

        view_origin, view_dir = get_view_origin_and_dir(context, self.mouse_pos)

        if lock[0] == 'EDGE':
            _, co1, co2, rot = lock

            i = intersect_line_line(view_origin, view_origin + view_dir, co1, co2)
            loc = i[1] if i else None

            if self.snap_ignore_rotation:
                rot = self.init_rot.to_matrix()

        elif lock[0] == 'FACE':
            _, co, no, rot, edge_cos = lock

            loc = intersect_line_plane(view_origin, view_origin + view_dir, co, no)

            if self.snap_ignore_rotation:
                rot = self.init_rot.to_matrix()

            elif alternative_align and not self.snap_align_before_lock:

                edge_distance = min([([co1, co2], (loc - get_center_between_points(co1, co2)).length) for co1, co2 in edge_cos], key=lambda x: x[1])

                normal = no.normalized()
                binormal = (edge_distance[0][1] - edge_distance[0][0]).normalized()
                tangent = binormal.cross(normal).normalized()

                self.snap_align_coords = edge_distance[0]

                rot = Matrix()
                rot.col[0].xyz = tangent
                rot.col[1].xyz = binormal
                rot.col[2].xyz = normal

        self.loc = loc

        self.translate_amount = (self.loc - self.init_loc).length

        return loc, rot.to_quaternion()

    def get_drag_snap_to_grid_transform(self, context, slide=False) -> Tuple[Vector, Quaternion]:
        self.snap_element = 'GRID'

        view_origin, view_dir = get_view_origin_and_dir(context, self.mouse_pos)

        self.snap_grid_increment_coords = [[], []]

        grid_yz = Vector((1, 0, 0))
        grid_xz = Vector((0, -1, 0))
        grid_xy = Vector((0, 0, 1))

        grid = max([(g, abs(view_dir.dot(g)) + (0.7 if idx == 2 else 0)) for idx, g in enumerate([grid_yz, grid_xz, grid_xy])], key=lambda x: x[1])

        i = intersect_line_plane(view_origin, view_origin + view_dir, Vector(), grid[0])

        if i:
            if slide:
                loc = i
                self.is_grid_sliding = True
            else:
                loc = Vector([round(co, self.grid_incremental) for co in i])
                self.is_grid_sliding = False

            self.snap_coords = [loc]

            if self.grid_incremental:
                self.get_grid_incremental_coords(grid[0], i)

            if self.snap_ignore_rotation:
                rot = self.init_rot.to_matrix()

            else:
                rot = self.init_rot.to_matrix()

                if grid[0] == grid_yz:

                    normal = Vector((1, 0, 0))
                    binormal = Vector((0, 0, 1))
                    tangent = Vector((0, 1, 0))

                elif grid[0] == grid_xz:
                    normal = Vector((0, -1, 0))
                    binormal = Vector((0, 0, 1))
                    tangent = Vector((1, 0, 0))

                elif grid[0] == grid_xy:
                    normal = Vector((0, 0, 1))
                    binormal = Vector((0, 1, 0))
                    tangent = Vector((1, 0, 0))

                if view_dir.dot(grid[0]) > 0:
                    normal.negate()
                    binormal.negate()

                rot = Matrix()
                rot.col[0].xyz = tangent
                rot.col[1].xyz = binormal
                rot.col[2].xyz = normal

            self.loc = loc

            self.translate_amount = (self.loc - self.init_loc).length

            return loc, rot.to_quaternion()

        return self.init_loc, self.init_rot

    def get_move_snap_to_element_transform(self) -> Vector:
        hitmx = self.S.hitmx
        hitface = self.S.hitface

        hit_co = hitmx.inverted_safe() @ self.S.hitlocation

        cursor_origin = self.cursor.location
        cursor_dir = self.cmx.to_3x3() @ self.axis_vector

        edge_weight = 1
        vert_weight = 20

        vert_distance = min([(v, (hit_co - v.co).length / vert_weight) for v in hitface.verts], key=lambda x: x[1])

        edge = min([(e, (hit_co - intersect_point_line(hit_co, e.verts[0].co, e.verts[1].co)[0]).length, (hit_co - get_center_between_verts(*e.verts)).length) for e in hitface.edges if e.calc_length()], key=lambda x: (x[1] * x[2]) / x[0].calc_length())
        edge_distance = (edge[0], ((edge[1] * edge[2]) / edge[0].calc_length()) / edge_weight)

        closest = min([vert_distance, edge_distance], key=lambda x: x[1])

        if isinstance(closest[0], bmesh.types.BMVert):
            self.snap_element = 'VERT'

            vert_co = hitmx @ closest[0].co

            i = intersect_point_line(vert_co, cursor_origin, cursor_origin + cursor_dir)
            loc = i[0]

            self.snap_coords = [vert_co]
            self.snap_proximity_coords = [vert_co, loc]

        elif isinstance(closest[0], bmesh.types.BMEdge):
            self.snap_element = 'EDGE'

            edge_dir = (hitmx.to_3x3() @ (closest[0].verts[0].co - closest[0].verts[1].co)).normalized()
            dot = cursor_dir.dot(edge_dir)

            if abs(dot) > 0.999:
                edge_center = hitmx @ get_center_between_verts(*closest[0].verts)

                i = intersect_point_line(edge_center, cursor_origin, cursor_origin + cursor_dir)
                loc = i[0]

                self.snap_proximity_coords = [edge_center, edge_center, loc]

            else:
                i = intersect_line_line(cursor_origin, cursor_origin + cursor_dir, hitmx @ closest[0].verts[0].co, hitmx @ closest[0].verts[1].co)
                loc = i[0]

                self.snap_proximity_coords = [*i] if i else []

            self.snap_coords = [hitmx @ v.co for v in closest[0].verts]

        self.loc = loc

        self.translate_amount = (self.loc - self.init_loc).length

        return loc

    def get_move_snap_to_grid_transform(self, context, slide=False) -> Vector:
        self.snap_element = 'GRID'

        view_origin, view_dir = get_view_origin_and_dir(context, self.mouse_pos)

        self.snap_grid_increment_coords = [[], []]

        grid_yz = Vector((1, 0, 0))
        grid_xz = Vector((0, -1, 0))
        grid_xy = Vector((0, 0, 1))

        grid = max([(g, abs(view_dir.dot(g)) + (0.7 if idx == 2 else 0)) for idx, g in enumerate([grid_yz, grid_xz, grid_xy])], key=lambda x: x[1])

        i = intersect_line_plane(view_origin, view_origin + view_dir, Vector(), grid[0])

        if i:
            grid_co = Vector([round(co, self.grid_incremental) for co in i])

            cursor_origin = self.cursor.location
            cursor_dir = self.cmx.to_3x3() @ self.axis_vector

            i = intersect_point_line(grid_co, cursor_origin, cursor_origin + cursor_dir)
            loc = i[0]

            self.snap_coords = [grid_co]
            self.snap_proximity_coords = [grid_co, loc]

            if self.grid_incremental:
                self.get_grid_incremental_coords(grid[0], grid_co)

            self.loc = loc

            self.translate_amount = (self.loc - self.init_loc).length

            return loc

        return self.init_loc

    def get_full_radial_array_transform(self) -> Quaternion:
        angle = radians(360 / self.array_count)

        if self.last_angle < 0:
            angle = -angle

        self.rotate_amount_deg = degrees(angle)

        return self.init_rot @ Quaternion(self.axis_vector, angle if self.axis == 'Y' else -angle)

    def enable_full_radial_array_weld(self, context):
        self.array_weld = True

        for obj, _, _ in self.arrays:
            lastmod = obj.modifiers[-1]

            if lastmod.type != 'WELD':
                add_weld(obj, name="+ Weld", mode='ALL')

        context.space_data.overlay.show_wireframes = True
        context.space_data.overlay.wireframe_threshold = True

    def disable_full_radial_array_weld(self, context):
        self.array_weld = False

        for obj, _, _ in self.arrays:
            lastmod = obj.modifiers[-1]

            if lastmod.type == 'WELD':
                obj.modifiers.remove(lastmod)

        context.space_data.overlay.show_wireframes = self.show_wires
        context.space_data.overlay.wireframe_threshold = self.wire_threshold

    def numeric_input(self, context, event) -> Union[Set[str], None]:
        if self.mode == 'ROTATE' and self.is_array and self.array_mode == 'ADD' and self.array_full:
            return

        if event.type == "TAB" and event.value == 'PRESS':
            self.is_numeric_input = not self.is_numeric_input

            force_ui_update(context)

            if self.is_numeric_input:
                if self.mode in ['TRANSLATE', 'DRAG']:
                    self.numeric_input_amount = str(self.translate_amount)

                    self.numeric_init_rot = self.cmx.to_quaternion()

                elif self.mode == 'ROTATE':
                    self.numeric_input_amount = str(self.rotate_amount_deg)

                    self.gzm_group.is_full_array = True

                self.is_numeric_input_marked = True

            else:
                if self.mode == 'ROTATE':
                    self.gzm_group.is_full_array = False

                    self.init_cursor_loc_2d = get_location_2d(context, self.cmx.to_translation(), default='OFF_SCREEN')
                return

        if self.is_numeric_input:
            if self.passthrough:
                self.passthrough = False

                self.get_absolute_HUD_coords(context)

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
                    transform = self.get_numeric_transform()

                except:
                    return {'RUNNING_MODAL'}

                self.transform(transform)

            elif navigation_passthrough(event, alt=True, wheel=True):
                self.passthrough = True

                return {'PASS_THROUGH'}

            elif event.type in {'RET', 'NUMPAD_ENTER', 'LEFTMOUSE'} and event.value == 'PRESS':
                self.finish(context)

                if self.is_array:
                    for obj, _, _ in self.arrays:
                        sort_modifiers(obj, debug=False)

                elif self.move_selection_and_cursor:
                    self.transform_selection(context)

                elif self.move_selection:
                    self.transform_selection(context)

                    set_cursor(matrix=self.orig_cmx if self.orig_cmx else self.init_cmx)

                self.save_settings()

                scene = context.scene
                hc = scene.HC

                if hc.focus_transform:

                    if not self.orig_cmx and not self.move_selection and self.init_loc != self.cmx.to_translation():
                        bpy.ops.view3d.view_center_cursor('INVOKE_DEFAULT' if hc.focus_mode == 'SOFT' else 'EXEC_DEFAULT')

                if hc.use_world and self.init_rot != self.cmx.to_quaternion():
                    hc.avoid_update = True
                    hc.use_world = False

                self.set_cursor_transform_preset(scene)

                return {'FINISHED'}

            elif event.type in {'ESC'}:

                if self.orig_cmx:
                    set_cursor(matrix=self.orig_cmx)

                else:
                    set_cursor(location=self.init_loc, rotation=self.init_rot)

                self.finish(context)

                if self.is_array:
                    for obj, arr, empty in self.arrays:
                        obj.modifiers.remove(arr)

                        if empty:
                            bpy.data.objects.remove(empty, do_unlink=True)

                return {'CANCELLED'}

            return {'RUNNING_MODAL'}

    def interactive_input(self, context, event) -> Set[str]:
        if event.type == 'MOUSEMOVE':
            get_mouse_pos(self, context, event)

        self.is_snapping = self.is_ctrl or self.is_limited_cursor_from_pie_setting or self.is_always_drag_snapping
        self.is_drag_snapping = self.mode == 'DRAG' and self.is_snapping
        self.is_move_snapping = self.mode == 'TRANSLATE' and self.is_snapping
        self.is_angle_snapping = self.mode == 'ROTATE' and self.is_snapping

        if any([self.is_drag_snapping, self.is_move_snapping]) and not self.snap_reset_mx:
            self.snap_reset_mx = self.cmx.copy()

            if context.mode == 'OBJECT':
                context.space_data.overlay.show_wireframes = True
                context.space_data.overlay.wireframe_threshold = 1

        elif (not any([self.is_drag_snapping, self.is_move_snapping]) or (event.type in shift and event.value == 'RELEASE' and not self.only_set_cursor_rotation)) and self.snap_reset_mx:
            set_cursor(matrix=self.snap_reset_mx)

            self.cmx = self.cursor.matrix
            self.loc = self.cmx.to_translation()

            self.snap_reset_mx = None

            self.snap_element = None

            self.snap_coords = []
            self.snap_tri_coords = []
            self.snap_grid_increment_coords = [[], []]

            if context.mode == 'OBJECT':
                context.space_data.overlay.show_wireframes = self.show_wires
                context.space_data.overlay.wireframe_threshold = self.wire_threshold

        if self.is_drag_snapping and self.snap_lock_element and not self.is_shift:
            self.snap_lock_element = None

        if self.snap_align_coords and not event.alt:
            self.snap_align_coords = None

        events = ['MOUSEMOVE', 'W', 'G', 'R', 'F', 'C', 'A', 'E', *ctrl, *alt, *shift]

        if self.can_move_selection:
            events.extend(['Q', 'S'])

            if self.move_selection or self.move_selection_and_cursor:
                events.append('X')

        if not self.is_array and self.mode == 'DRAG' and self.is_drag_snapping and not self.transform_preset_from_machin3tools:
            events.append('T')

        if self.is_limited_cursor_from_pie_setting:
            events.remove('R')

            for c in ctrl:
                events.remove(c)

            if self.only_set_cursor_location:
                events.remove('F')
                events.remove('E')

                for a in alt:
                    events.remove(a)

            if self.only_set_cursor_rotation:
                for s in shift:
                    events.remove(s)

        if event.type in events or scroll(event, key=True) or self.is_init_run:

            if self.is_init_run:
                self.is_init_run = False

            if self.passthrough:
                self.passthrough = False

                loc = self.cmx.to_translation()

                if self.mode == 'TRANSLATE':
                    new_loc = self.get_transform(context)

                    self.passthrough_offset = new_loc - loc

                self.get_absolute_HUD_coords(context)

            if self.is_drag_snapping and event.value == 'PRESS' and not event.is_repeat:

                if event.type == 'C':

                    if self.is_array:
                       if event.alt:
                            self.snap_face_center = step_enum(current=self.snap_face_center, items=transform_snap_face_center_items, step=1, loop=True)

                    else:
                        self.snap_face_center = step_enum(current=self.snap_face_center, items=transform_snap_face_center_items, step=1, loop=True)

                elif event.type == 'F':

                    if not self.snap_lock_element:
                        self.snap_face_align_edge_pair = not self.snap_face_align_edge_pair

                elif event.type == 'E':
                    self.snap_edge_align_face_and_edge = not self.snap_edge_align_face_and_edge

                elif event.type == 'R':
                    self.snap_ignore_rotation = not self.snap_ignore_rotation

            if event.type in ['MOUSEMOVE', *ctrl] and not any([self.enforce_cursor_to_origin_reset, self.is_drag_snapping, self.is_move_snapping]):

                transform = self.get_transform(context)

                self.transform(transform)

            elif self.is_drag_snapping:

                if event.type in shift and event.value == 'PRESS':
                    self.S.get_hit(self.mouse_pos)

                    if self.S.hit:
                        _ = self.get_drag_snap_to_element_transform(context, lock=True)

                if self.snap_lock_element:
                    transform = self.get_drag_snap_to_locked_element_transform(context)

                    self.transform(transform)

                else:
                    self.S.get_hit(self.mouse_pos)

                    if self.S.hit:
                        transform = self.get_drag_snap_to_element_transform(context, lock=False)

                        self.transform(transform)

                        self.snap_grid_increment_coords = [[], []]

                    else:
                        if self.snap_element == 'GRID':

                            if self.is_array:
                                if event.alt and scroll_up(event, key=True):
                                    self.grid_incremental += 1

                                elif event.alt and scroll_down(event, key=True):
                                    self.grid_incremental -= 1

                            else:
                                if scroll_up(event, key=True):
                                    self.grid_incremental += 1

                                elif scroll_down(event, key=True):
                                    self.grid_incremental -= 1

                        transform = self.get_drag_snap_to_grid_transform(context, slide=self.is_shift)

                        self.transform(transform)

            elif self.is_move_snapping:
                self.S.get_hit(self.mouse_pos)

                if self.S.hit:
                    transform = self.get_move_snap_to_element_transform()

                    self.transform(transform)

                    self.snap_grid_increment_coords = [[], []]

                else:
                    if self.snap_element == 'GRID':
                        if self.is_array:
                            if event.alt and scroll_up(event, key=True):
                                self.grid_incremental += 1

                            elif event.alt and scroll_down(event, key=True):
                                self.grid_incremental -= 1

                        else:
                            if scroll_up(event, key=True):
                                self.grid_incremental += 1

                            elif scroll_down(event, key=True):
                                self.grid_incremental -= 1

                    transform = self.get_move_snap_to_grid_transform(context)

                    self.transform(transform)

            if self.is_array:

                if event.type in ['A', 'C', 'F', 'W'] or scroll(event, key=True):
                    transform = self.get_transform(context)

                    if not event.alt and scroll_up(event, key=True):
                        self.array_count += 1

                    elif not event.alt and scroll_down(event, key=True):
                        self.array_count -= 1

                    elif event.type == 'A' and event.value == 'PRESS':
                        self.array_mode = step_enum(self.array_mode, array_mode_items, step=1, loop=True)

                        if self.array_mode == 'FIT':
                            self.array_flip = self.last_angle < 0 if self.axis == 'Y' else self.last_angle > 0

                            if self.array_weld:
                                self.disable_full_radial_array_weld(context)

                    elif event.type == 'C' and event.value == 'PRESS':
                        if self.mode == 'ROTATION' and (self.array_mode == 'ADD' and self.array_full):
                            return {'RUNNING_MODAL'}

                        if not event.alt:
                            self.array_center = not self.array_center

                    elif self.mode == 'ROTATE' and self.array_mode == 'ADD' and event.type == 'F' and event.value == 'PRESS':
                        self.array_full = not self.array_full

                        self.gzm_group.is_full_array = self.array_full

                        if not self.array_full and self.array_weld:
                            self.disable_full_radial_array_weld(context)

                    elif self.mode == 'ROTATE' and self.array_mode == 'ADD' and self.array_full and event.type == 'W' and event.value == 'PRESS':
                        if self.array_weld:
                            self.disable_full_radial_array_weld(context)

                        else:
                            self.enable_full_radial_array_weld(context)

                    elif self.mode == 'ROTATE' and self.array_mode == 'FIT' and event.type == 'F' and event.value == 'PRESS':
                        self.array_flip = not self.array_flip

                    self.adjust_array(transform)

                if self.mode == 'ROTATE' and self.array_mode == 'ADD' and self.array_full:
                    transform = self.get_full_radial_array_transform() if self.mode == 'ROTATE' and self.array_mode == 'ADD' and self.array_full else self.get_transform(context)

                    self.adjust_array(transform)

                force_ui_update(context)

            else:

                if event.type == 'A' and event.value == 'PRESS':
                    self.show_absolute_coords = not self.show_absolute_coords

                elif event.type == 'T' and event.value == 'PRESS':
                    self.drag_snap_set_transform = not self.drag_snap_set_transform

                elif event.type == 'S' and event.value == 'PRESS':
                    self.move_selection = not self.move_selection

                    if self.move_selection and self.move_selection_and_cursor:
                        self.move_selection_and_cursor = False

                    if self.move_selection:
                        self.update_selection_batches()

                elif event.type == 'Q' and event.value == 'PRESS':
                    self.move_selection_and_cursor = not self.move_selection_and_cursor

                    if self.move_selection and self.move_selection_and_cursor:
                        self.move_selection = False

                    if self.move_selection_and_cursor:
                        self.update_selection_batches()

                elif event.type == 'X' and event.value == 'PRESS':
                    self.move_selection_drag_flip = not self.move_selection_drag_flip

                    self.update_selection_batches()

                force_ui_update(context)

            if not self.is_array and not self.is_drag_snapping and not self.is_move_snapping:
                if event.type in ['W', 'G']:
                    self.reset_cursor_to_origin(context, event, location=True)

                    if self.move_selection or self.move_selection_and_cursor:
                        self.update_selection_batches()

                if event.type == 'R':
                    self.reset_cursor_to_origin(context, event, rotation=True)

        if self.mode in ['TRANSLATE', 'DRAG'] and navigation_passthrough(event, alt=False, wheel=False):
            self.passthrough = True

            return {'PASS_THROUGH'}

        if event.type in {'LEFTMOUSE', 'SPACE'} or (self.mode == 'DRAG' and event.type == 'RIGHTMOUSE' and event.value == 'RELEASE'):
            self.finish(context)

            if self.is_array:
                for obj, _, _ in self.arrays:
                    sort_modifiers(obj, debug=False)

            elif self.move_selection_and_cursor:
                self.transform_selection(context)

            elif self.move_selection:
                self.transform_selection(context)

                set_cursor(matrix=self.orig_cmx if self.orig_cmx else self.init_cmx)

            self.save_settings()

            scene = context.scene
            hc = scene.HC

            if hc.focus_transform:

                if not self.orig_cmx and not self.move_selection and self.init_loc != self.cmx.to_translation():
                    bpy.ops.view3d.view_center_cursor('INVOKE_DEFAULT' if hc.focus_mode == 'SOFT' else 'EXEC_DEFAULT')

            if hc.use_world and self.init_rot != self.cmx.to_quaternion():
                hc.avoid_update = True
                hc.use_world = False

            if self.mode == 'DRAG' and not self.gzm_group:
                if event.type == 'LEFTMOUSE':
                    hc.show_gizmos = True

                elif event.type in ['RIGHTMOUSE', 'SPACE']:
                    hc.show_gizmos = False

            self.set_cursor_transform_preset(scene)

            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:

            if self.orig_cmx:
                set_cursor(matrix=self.orig_cmx)

            else:
                set_cursor(location=self.init_loc, rotation=self.init_rot)

            self.finish(context)

            if self.is_array:
                for idx, (obj, arr, empty) in enumerate(self.arrays):
                    obj.modifiers.remove(arr)

                    if empty:

                        if idx > 0:
                            continue

                        bpy.data.objects.remove(empty, do_unlink=True)

            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def transform(self, transform: Union[Vector, Quaternion, Tuple[Vector, Quaternion]]):
        if self.is_array:
            self.adjust_array(transform)

        else:
            self.transform_cursor(transform)

    def move_cursor_under_mouse(self, context):
        if self.mode == 'DRAG' and not self.gzm_group:
            self.orig_cmx = self.cursor.matrix

            view_origin, view_dir = get_view_origin_and_dir(context, self.mouse_pos)

            cursor_3d = view_origin + view_dir * context.region_data.view_distance

            set_cursor(location=cursor_3d, rotation=self.cursor.matrix.to_quaternion())

            HC.props['cursor_2d'] = self.mouse_pos

        else:
            self.orig_cmx = None

    def reset_cursor_to_origin(self, context, event, location=False, rotation=False):
        if event.value == 'PRESS':
            self.enforce_cursor_to_origin_reset = True

            if location and not self.location_reset_mx:
                self.location_reset_mx = self.cmx.copy()

                self.reset_loc = Vector()
                self.reset_rot = self.cmx.to_quaternion()

            if rotation and not self.rotation_reset_mx:
                self.rotation_reset_mx = self.cmx.copy()

                self.reset_loc = self.cursor.location.copy()
                self.reset_rot = Quaternion()

        elif event.value == 'RELEASE':
            self.enforce_cursor_to_origin_reset = False

            if location and self.location_reset_mx:
                self.reset_loc, self.reset_rot, _ = self.location_reset_mx.decompose()
                self.location_reset_mx = None

            if rotation and self.rotation_reset_mx:
                self.reset_loc, self.reset_rot, _ = self.rotation_reset_mx.decompose()
                self.rotation_reset_mx = None

        if not event.is_repeat:
            set_cursor(location=self.reset_loc, rotation=self.reset_rot)

            self.cmx = context.scene.cursor.matrix.copy()

            if location:
                self.loc = self.reset_loc

                self.target_loc = self.loc

            self.get_absolute_HUD_coords(context)

    def transform_cursor(self, transform: Union[Vector, Quaternion, Tuple[Vector, Quaternion]]):
        if isinstance(transform, Vector):
            location = transform
            rotation = self.init_rot

        elif isinstance(transform, Quaternion):
            location = self.init_loc
            rotation = transform

        elif isinstance(transform, Tuple):
            location, rotation = transform

        if self.mode == 'TRANSLATE' and not self.snap_coords:
            location = location - self.passthrough_offset

        if self.is_cursor_pie_invocation:

            if self.only_set_cursor_location:
                rotation = self.init_rot

            if self.only_set_cursor_rotation:
                location = self.init_loc

        set_cursor(location=location, rotation=rotation)

        self.cmx = self.cursor.matrix

        self.target_loc = location

        self.zoom_factor = get_zoom_factor(bpy.context, self.cursor.location, scale=50, ignore_obj_scale=True)

        self.get_absolute_HUD_coords(bpy.context)

        if self.can_move_selection and (self.move_selection or self.move_selection_and_cursor):
            self.update_selection_batches()

    def adjust_array(self, transform: Union[Vector, Quaternion, Tuple[Vector, Quaternion]]):
        if type(transform) is tuple:
            transform = transform[0] if self.mode in ['TRANSLATE', 'DRAG'] else transform[1]

        for obj, mod, empty in self.arrays:

            loc, rot, sca = obj.matrix_world.decompose()

            if isinstance(transform, Vector):
                self.array_coords[obj.name] = [self.init_loc, loc]

                move_dir = transform - self.init_loc

                if self.array_center:
                    half_move_dir = move_dir / 2

                    self.array_coords[obj.name].extend([self.init_loc + half_move_dir, loc + half_move_dir])
                    self.array_coords[obj.name].extend([self.init_loc - half_move_dir, loc - half_move_dir])

                else:
                    self.array_coords[obj.name].extend([self.init_loc + move_dir, loc + move_dir])

                self.target_loc = self.init_loc + move_dir

            elif isinstance(transform, Quaternion):

                if self.array_center and not (self.array_mode == 'ADD' and self.array_full):
                    self.array_coords[obj.name] = [self.init_loc, loc]

                    drot = self.init_rot.rotation_difference(transform)

                    axis, angle = drot.to_axis_angle()

                    if self.array_mode == 'FIT':
                        if self.array_flip:
                            angle = radians(-360) + self.rotate_amount if self.rotate_amount >= 0 else self.rotate_amount

                        else:
                            angle = self.rotate_amount if self.rotate_amount >= 0 else radians(360) + self.rotate_amount

                    half_rot = Quaternion(axis, angle / 2)
                    half_neg_rot = Quaternion(axis, angle / -2)

                    instance_location = self.cmx @ half_rot.to_matrix().to_4x4() @ self.cmx.inverted_safe() @ loc
                    instance_neg_location = self.cmx @ half_neg_rot.to_matrix().to_4x4() @ self.cmx.inverted_safe() @ loc

                    self.array_coords[obj.name].extend([self.init_loc, instance_location, self.init_loc, instance_neg_location])

                else:
                    self.array_coords[obj.name] = [self.init_loc, loc]

                    drot = self.init_rot.rotation_difference(transform)

                    instance_location = self.cmx @ drot.to_matrix().to_4x4() @ self.cmx.inverted_safe() @ loc
                    self.array_coords[obj.name].extend([self.init_loc, instance_location])

            if isinstance(transform, Vector):

                set_mod_input(mod, 'Count', self.array_count)
                set_mod_input(mod, 'Fit', self.array_mode == 'FIT')
                set_mod_input(mod, 'Center', self.array_center)

                set_mod_input(mod, 'Offset', obj.matrix_world.inverted_safe().to_3x3() @ (transform - self.init_loc))

                obj.update_tag()

            elif isinstance(transform, Quaternion):

                set_mod_input(mod, 'Count', self.array_count)
                set_mod_input(mod, 'Fit', self.array_mode == 'FIT')
                set_mod_input(mod, 'Center', self.array_center)

                set_mod_input(mod, 'Full 360°', self.array_full if self.array_mode == 'ADD' else False)

                if self.array_mode == 'ADD':
                    angle = self.rotate_amount

                elif self.array_mode == 'FIT':
                    if self.array_flip:
                        angle = radians(-360) + self.rotate_amount if self.rotate_amount >= 0 else self.rotate_amount

                    else:
                        angle = self.rotate_amount if self.rotate_amount >= 0 else radians(360) + self.rotate_amount

                set_mod_input(mod, 'Angle', float(angle))  # without the float, blender will warn about a type mismatch when setting the initial 0 angle

                obj.update_tag()

            else:
                return

    def get_selection_transform_matrix(self, omx):
        if self.mode == 'TRANSLATE' or (self.is_drag_snapping and self.snap_ignore_rotation) or not self.is_drag_snapping:
            return get_loc_matrix(self.target_loc - self.init_loc) @ omx

        else:
            delta_obj_mx = omx.inverted_safe() @ self.init_cmx
            delta_cursor_mx = self.init_cmx.inverted_safe() @ self.cmx

            if self.move_selection_drag_flip:
                rot = Quaternion(Vector((0, 1, 0)), radians(180)).to_matrix().to_4x4()
                return omx @ delta_obj_mx @ delta_cursor_mx @ rot @ delta_obj_mx.inverted_safe()

            else:
                return omx @ delta_obj_mx @ delta_cursor_mx @ delta_obj_mx.inverted_safe()

    def transform_selection(self, context):
        objects = filter_non_child_objects([obj for obj in self.selection.keys()])

        for obj in objects:
            obj.matrix_world = self.get_selection_transform_matrix(obj.matrix_world)

def draw_snap_rotate_status(op):
    def draw(self, context):
        layout = self.layout

        row = layout.row(align=True)

        if op.is_snapping:
            row.label(text=f"Snap Rotating {'Cursor' if op.is_cursor else context.active_object.name}")
        else:
            row.label(text=f"Rotating {'Cursor' if op.is_cursor else context.active_object.name}")

        draw_status_item(row, key=op.finish_key, text="Finish")
        draw_status_item(row, key='RMB', text="Cancel")

        draw_status_item_precision(row, fine=op.is_shift, gap=10)

        draw_status_item(row, key='SHIFT', text="Presice", prop='fine' if op.is_shift else 'normal')
        draw_status_item(row, key='MOVE', text="Angle", prop=dynamic_format(op.angle, decimal_offset=1), gap=2)

        draw_status_item(row, active=op.is_snapping, key='CTRL', text="Snap", gap=2)

        draw_status_item(row, key='MMB_SCROLL', text="Snap Angle", prop=f"{round(op.snap_angle)}°", gap=1)

    return draw

class SnapRotate(bpy.types.Operator, Settings):
    bl_idname = "machin3.snap_rotate"
    bl_label = "MACHIN3: Snap Rotate"
    bl_options = {'REGISTER', 'UNDO'}

    angle: FloatProperty(name="Angle", default=0)
    axis: EnumProperty(name="Axis", items=axis_items, default='Z')
    is_snapping: BoolProperty(name="is Snapping", default=True)
    snap_angle: FloatProperty(name="Angle", default=5)
    invert_direction: BoolProperty("Invert Mouse Movement Direction", default=False)
    is_button_invocation: BoolProperty(name="Invoke operator from Sidebar Button", default=False)
    is_sidebar_invocation: BoolProperty(name="Invoke operator from Popup Panel Button", default=False)
    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    @classmethod
    def description(cls, context, properties):
        desc = "Snap Rotate Cursor or Active Object"
        desc += "\nAutomatically rotate on the Axis most aligned with the View"
        return desc

    def draw(self, context):
        layout = self.layout
        column = layout.column(align=True)

        row = column.split(factor=0.2, align=True)
        row.label(text='Axis')
        r = row.row(align=True)
        r.prop(self, 'axis', expand=True)

        row = column.split(factor=0.2, align=True)
        row.label(text='Angle')
        row.prop(self, 'angle', text='')

    def draw_HUD(self, context):
        if context.area == self.area:
            draw_init(self)

            dims = draw_label(context, title="Snap Rotating ", coords=Vector((self.HUD_x, self.HUD_y)), center=False)

            title = f"{'Cursor' if self.is_cursor else context.active_object.name} "
            dims += draw_label(context, title=title, coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, alpha=0.5)
            dims += draw_label(context, title='on ', coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, alpha=0.3)

            color = red if self.axis == 'X' else green if self.axis == 'Y' else blue
            dims += draw_label(context, title=self.axis, coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, color=color)

            if self.is_shift:
                draw_label(context, title=" a little", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, size=10, color=white, alpha=0.5)

            self.offset += 18
            angle = dynamic_format(self.angle, decimal_offset=1)
            dims = draw_label(context, title=f"{angle}° ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=yellow)

            if self.is_snapping:
                draw_label(context, title=f" {round(self.snap_angle)}° snapping", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, alpha=0.2)

    def draw_VIEW3D(self, context):
        if context.area == self.area:
            color = red if self.axis == 'X' else green if self.axis == 'Y' else blue
            alpha = 0.2 if self.axis == 'Y' else 0.25  # green seems stronger than red and blue, so use a little less alpha

            draw_vector(self.axis_dir * 200, origin=self.origin - self.axis_dir * 100, color=color, alpha=alpha)

            draw_circle(self.origin, self.rotation, radius=self.axis_radius, segments=64, width=10, color=color, alpha=0.1)

    def modal(self, context, event):
        if ignore_events(event):
            return {'RUNNING_MODAL'}

        context.area.tag_redraw()

        self.is_snapping = not event.ctrl

        update_mod_keys(self, event)

        events = ['MOUSEMOVE', *ctrl]

        if event.type in events or scroll(event, key=True):

            if scroll(event, key=True):
                if scroll_up(event, key=True):
                    self.snap_angle += 5 if self.snap_angle >= 5 else 1

                elif scroll_down(event, key=True):
                    self.snap_angle -= 5 if self.snap_angle > 5 else 1

                self.snap_angle = min(90, max(1, self.snap_angle))

            if event.type in ['MOUSEMOVE', *ctrl]:
                get_mouse_pos(self, context, event)
                wrap_mouse(self, context, y=True)

                divisor = 10 if event.shift else 1

                if self.is_flipped ^ self.invert_direction:
                    self.internal_angle -= (self.mouse_pos.y - self.last_mouse.y) / divisor

                else:
                    self.internal_angle += (self.mouse_pos.y - self.last_mouse.y) / divisor

                self.angle = snap_value(self.internal_angle, self.snap_angle) if self.is_snapping else self.internal_angle

            self.execute(context)

        if event.type == 'LEFTMOUSE' or (event.type == self.finish_event and event.value == 'RELEASE'):
            self.finish(context)
            self.save_settings()

            return {'FINISHED'}

        elif event.type in {'ESC', 'RIGHTMOUSE'}:
            self.finish(context)

            if self.is_cursor:
                context.scene.cursor.matrix = self.init_mx

                if context.space_data.overlay.show_cursor and context.visible_objects:
                    context.visible_objects[0].select_set(context.visible_objects[0].select_get())

            else:
                context.active_object.matrix_world = self.init_mx

            return {'CANCELLED'}

        self.last_mouse = self.mouse_pos

        return {'RUNNING_MODAL'}

    def finish(self, context):
        finish_modal_handlers(self)

        finish_status(self)

        context.window.cursor_set('DEFAULT')

        if not self.is_cursor:
            restore_gizmos(self)

            force_ui_update(context)

    def invoke(self, context, event):
        self.init_settings(props=['snap_angle'])
        self.load_settings()

        self.active = context.active_object if context.active_object in context.selected_objects else None

        self.is_cursor = not bool(self.active)

        self.init_mx = context.scene.cursor.matrix.copy() if self.is_cursor else self.active.matrix_world.copy()

        self.axis, self.axis_dir, self.origin, self.rotation, self.is_flipped = self.get_rotation_axis(context, debug=False)

        origin_2d = get_location_2d(context, self.origin, default="OFF_SCREEN")
        if is_on_screen(context, origin_2d):

            get_mouse_pos(self, context, event)
            self.last_mouse = self.mouse_pos

            if self.is_button_invocation:
                self.warp_mouse_out_of_panel(context)

            self.invert_direction = self.get_invert_direction(context)

            self.angle = 0
            self.internal_angle = 0

            self.is_snapping = True

            update_mod_keys(self)

            if self.is_button_invocation:
                self.finish_event = 'LEFTMOUSE'
                self.finish_key = 'LMB'

            else:
                self.finish_event = event.type
                self.finish_key = event.type.replace('EVENT_', '')

            self.axis_radius = self.get_axis_radius(context)

            context.window.cursor_set('SCROLL_Y')

            if not self.is_cursor:
                hide_gizmos(self, context)

            init_status(self, context, func=draw_snap_rotate_status(self))

            force_ui_update(context)

            init_modal_handlers(self, context, hud=True, view3d=True)
            return {'RUNNING_MODAL'}

        else:
            text = f"Position the {'Cursor' if self.is_cursor else 'Object'} somewhere in the Field of View to Snap Rotate it!"
            draw_fading_label(context, text=text, y=120, color=red, alpha=1, move_y=20, time=2)

            return {'CANCELLED'}

    def execute(self, context):
        loc, rot, sca = self.init_mx.decompose()
        q = Quaternion(axis_vector_mappings[self.axis], radians(self.angle))

        if self.is_cursor:
            context.scene.cursor.matrix = Matrix.LocRotScale(loc, rot @ q, sca)

            if context.space_data.overlay.show_cursor and context.visible_objects:
                context.visible_objects[0].select_set(context.visible_objects[0].select_get())

        else:
            loc, rot, sca = self.init_mx.decompose()
            context.active_object.matrix_world = Matrix.LocRotScale(loc, rot @ q, sca)

        return {'FINISHED'}

    def warp_mouse_out_of_panel(self, context):
        distance = None

        HUD_width = get_text_dimensions(context, "Snap Rotating Cursor on Z", size=12)[0]

        if self.is_sidebar_invocation:
            for region in context.area.regions:
                if region.type == 'UI':
                    distance = - (region.width - (context.region.width - self.mouse_pos.x) + HUD_width)

        else:
            if self.mouse_pos.x < context.region.width / 2:
                distance = (300 * get_scale(context))

            else:
                distance = - ((150 * get_scale(context)) + HUD_width)

        if distance:
            warp_mouse(self, context, Vector((self.mouse_pos.x + distance, self.mouse_pos.y)))

    def get_rotation_axis(self, context, debug=False):

        view_center = Vector((context.region.width / 2, context.region.height / 2))

        view_origin, view_dir = get_view_origin_and_dir(context, view_center)

        if debug:
            draw_point(view_origin, modal=False)
            draw_vector(view_dir, origin=view_origin, modal=False)

        axes = []

        origin = self.init_mx.decompose()[0]

        for axis in ['X', 'Y', 'Z']:
            rot = self.init_mx.to_quaternion()
            axis_dir = rot @ axis_vector_mappings[axis]

            if debug:
                draw_vector(axis_dir, origin=origin, modal=False)

            dot = axis_dir.dot(view_dir)

            if axis == 'X':
                rot.rotate(Quaternion(Vector(rot @ Vector((0, 1, 0))), radians(90)))

            elif axis == 'Y':
                rot.rotate(Quaternion(Vector(rot @ Vector((1, 0, 0))), radians(90)))

            axes.append((axis, axis_dir, rot, dot))

            if debug:
                print(axis, dot)

        aligned = max(axes, key=lambda x: abs(x[3]))

        if debug:
            print("aligned:", aligned)
            context.area.tag_redraw()

        return aligned[0], aligned[1], origin, aligned[2], aligned[3] >= 0

    def get_invert_direction(self, context, debug=False):
        origin_2d = location_3d_to_region_2d(context.region, context.region_data, self.origin)

        if debug:
            draw_point(origin_2d.resized(3), modal=False, screen=True)
            draw_point(self.mouse_pos.resized(3), color=yellow, modal=False, screen=True)

            context.area.tag_redraw()

        return self.mouse_pos.x < origin_2d.x

    def get_axis_radius(self, context):
        if self.is_cursor:
            radius = get_zoom_factor(context, self.origin, scale=50, ignore_obj_scale=True)

        else:
            mods = [mod for mod in self.active.modifiers if mod.show_viewport and ((mod.type == 'MIRROR' and mod.mirror_object) or is_array(mod))]

            for mod in mods:
                mod.show_viewport= False

            context.evaluated_depsgraph_get()

            _, _, dimensions = get_eval_bbox(self.active, advanced=True)

            for mod in mods:
                mod.show_viewport= True

            if any(dimensions):
                if self.axis == 'X':
                    dims = [dimensions.y, dimensions.z]

                    if any(dims):
                        radius = max(dims) * 0.6

                    else:
                        radius = sum(dimensions) / len([d for d in dimensions if d]) * 0.7

                elif self.axis == 'Y':
                    dims = [dimensions.x, dimensions.z]

                    if any(dims):
                        radius = max(dims) * 0.6

                    else:
                        radius = sum(dimensions) / len([d for d in dimensions if d]) * 0.7

                elif self.axis == 'Z':
                    dims = [dimensions.x, dimensions.y]

                    if any(dims):
                        radius = max(dims) * 0.6

                    else:
                        radius = sum(dimensions) / len([d for d in dimensions if d]) * 0.7

            elif (empty := context.active_object).type == 'EMPTY':
                radius = (sum(empty.matrix_world.decompose()[2]) / 3) * empty.empty_display_size * 1.3

            else:
                radius = get_zoom_factor(context, self.origin, scale=100, ignore_obj_scale=True)

        return radius

def draw_cast_cursor_status(op):
    def draw(self, context):
        layout = self.layout

        row = layout.row(align=True)

        row.label(text="Cast Cursor")

        draw_status_item(row, key='LMB', text="Finish")
        draw_status_item(row, key='MMB', text="Viewport")
        draw_status_item(row, key='RMB', text="Cancel")

        row.separator(factor=10)

        draw_status_item(row, active=op.align_to_surface, key='S', text="Surface Align")
        draw_status_item(row, active=op.center_cast, key='C', text="Center Cast", gap=2)

    return draw

class CastCursor(bpy.types.Operator, Settings):
    bl_idname = "machin3.cast_cursor"
    bl_label = "MACHIN3: Cast Cursor"
    bl_description = "Cast the Cursor along one of it's axes"
    bl_options = {'REGISTER', 'UNDO'}

    align_to_surface: BoolProperty(name="Align the Cursor to the hit surface or grid", default=False)
    center_cast: BoolProperty(name="Cast Halfe the Distance only", default=False)
    passthrough = None
    is_button_invocation: BoolProperty(name="Invoke operator from Popup Panel Button", default=False)
    is_sidebar_invocation: BoolProperty(name="Invoke operator from Sidebar Button", default=False)
    def draw_HUD(self, context):
        if context.area == self.area:
            if not self.passthrough:
                init_mouse = self.init_mouse.resized(3)

                draw_vector(self.flick_vector.resized(3), origin=init_mouse, fade=True, alpha=1)
                draw_circle(init_mouse, radius=self.flick_distance, width=3, color=white, alpha=0.02)

                if self.center_cast:
                    draw_label(context, title='Center ', coords=(init_mouse.x, init_mouse.y + self.flick_distance), center=True, color=yellow, alpha=1)

                draw_label(context, title='Cast Cursor', coords=(init_mouse.x, init_mouse.y + self.flick_distance - (15 * self.ui_scale)), center=True, color=white, alpha=0.5)

                if self.align_to_surface:
                    is_grid = (data := self.hit_data[self.flick_direction]) and data['is_grid']

                    draw_label(context, title=f"{'Grid' if is_grid else 'Surface'} Align", coords=(init_mouse.x, init_mouse.y + self.flick_distance - (30 * self.ui_scale)), center=True, color=yellow, alpha=1)

                draw_label(context, title=self.flick_direction.replace('_', ' ').title(), coords=(init_mouse.x, init_mouse.y - self.flick_distance + (15 * self.ui_scale)), center=True, alpha=0.5)

    def draw_VIEW3D(self, context):
        if context.area == self.area:

            for direction, data in self.hit_data.items():
                if data:
                    loc = data['loc']
                    center_loc = data['center_loc']

                    is_grid = data['is_grid']
                    is_chosen_direction = direction == self.flick_direction

                    draw_point(loc, color=yellow if is_grid else white, size=3 if self.center_cast else 4, alpha=0.5 if self.center_cast else 1)

                    if self.center_cast:
                        draw_point(center_loc, color=yellow if is_grid else white, size=4, alpha=1)

                    color = white if not is_chosen_direction else red if 'X' in direction else green if 'Y' in direction else blue

                    alpha = 0.99 if is_chosen_direction else 0.05

                    draw_line([self.cursor_origin, loc], color=color, width=1 if self.center_cast else 2, alpha=alpha / 3 if self.center_cast else alpha)

                    if self.center_cast:
                        draw_line([self.cursor_origin, center_loc], color=color, width=2, alpha=alpha)

                    if is_chosen_direction and not self.passthrough:
                        axis_coords = data['aligned_axis_coords'] if self.align_to_surface else data['axis_coords']

                        for coords, color in axis_coords:
                            draw_line(coords, color=color, alpha=0.5)

            if not self.passthrough:
                for direction, axis in self.axes.items():
                    positive = 'POSITIVE' in direction

                    color = red if 'X' in direction else green if 'Y' in direction else blue
                    draw_vector(axis * self.zoom / 2, origin=self.init_mouse_3d, color=color, width=2 if positive else 1, alpha=1 if positive else 0.3)

                is_grid = self.hit_data[self.flick_direction]['is_grid']
                color = yellow if is_grid else white

                draw_point(self.init_mouse_3d + self.axes[self.flick_direction] * self.zoom / 2 * 1.2, size=5, color=color, alpha=0.8)

    def modal(self, context, event):
        if ignore_events(event):
            return {'RUNNING_MODAL'}

        context.area.tag_redraw()

        events = ['MOUSEMOVE', 'S', 'C']

        if event.type in events:

            if event.type == 'MOUSEMOVE':
                get_mouse_pos(self, context, event)

                if self.passthrough:
                    self.passthrough = False

                    view_origin, view_dir = get_view_origin_and_dir(context, self.mouse_pos)

                    self.origin = view_origin + view_dir * 10

                    self.init_mouse = self.mouse_pos
                    self.init_mouse_3d = region_2d_to_location_3d(context.region, context.region_data, self.init_mouse, self.origin)

                    self.zoom = get_zoom_factor(context, depth_location=self.origin, scale=self.flick_distance, ignore_obj_scale=True)

                    self.create_cursor_axes_previews(context)

                self.flick_vector = self.mouse_pos - self.init_mouse

                if self.flick_vector.length:
                    self.flick_direction = get_flick_direction(context, self.init_mouse_3d, self.flick_vector, self.axes)

                if self.flick_vector.length > self.flick_distance:
                    self.finish(context)
                    self.save_settings()

                    self.set_cursor(context)
                    return {'FINISHED'}

            elif event.type == 'S' and event.value == 'PRESS':
                self.align_to_surface = not self.align_to_surface

                force_ui_update(context)

            elif event.type == 'C' and event.value == 'PRESS':
                self.center_cast = not self.center_cast

                force_ui_update(context)

        if navigation_passthrough(event, alt=True, wheel=True):
            self.passthrough = True
            return {'PASS_THROUGH'}

        elif event.type in ['LEFTMOUSE', 'SPACE'] and event.value == 'PRESS':
            self.finish(context)
            self.save_settings()

            self.set_cursor(context)
            return {'FINISHED'}

        elif event.type in ['RIGHTMOUSE', 'ESC']:
            self.finish(context)
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def finish(self, context):
        finish_modal_handlers(self)

        restore_gizmos(self)

        finish_status(self)

        force_ui_update(context)

    def invoke(self, context, event):
        self.init_settings(props=['align_to_surface'])
        self.load_settings()

        cursor_2d = get_cursor_2d(context)

        if is_on_screen(context, cursor_2d):

            get_mouse_pos(self, context, event)

            if self.is_button_invocation:
                self.warp_mouse_out_of_panel(context)

            self.cmx = context.scene.cursor.matrix.copy()
            self.init_rotation = self.cmx.to_quaternion()
            self.cursor_origin = self.cmx.to_translation()

            self.hit_data = self.get_hit_data(context, debug=False)

            self.axes = {direction: data['axis'] for direction, data in self.hit_data.items() if data}

            self.create_cursor_axes_previews(context)

            self.ui_scale = get_scale(context)
            self.flick_distance = get_prefs().cast_flick_distance * self.ui_scale
            self.flick_direction = None

            view_origin, view_dir = get_view_origin_and_dir(context, self.mouse_pos)

            self.origin = view_origin + view_dir * 10

            self.init_mouse = self.mouse_pos
            self.init_mouse_3d = region_2d_to_location_3d(context.region, context.region_data, self.init_mouse, self.origin)

            self.zoom = get_zoom_factor(context, depth_location=self.origin, scale=self.flick_distance, ignore_obj_scale=True)

            self.flick_vector = self.mouse_pos - self.init_mouse

            for direction, hitdata in reversed(self.hit_data.items()):
                if hitdata:
                    self.flick_direction = direction
                    break

            if self.flick_direction:

                hide_gizmos(self, context)

                init_status(self, context, func=draw_cast_cursor_status(self))

                force_ui_update(context)

                init_modal_handlers(self, context, hud=True, view3d=True)
                return {'RUNNING_MODAL'}

            text="Casting the Cursor is not possible with the current Cursor location and orientation, because no Cast Targets are found!"
            draw_fading_label(context, text=text, y=120, color=red, alpha=1, move_y=40, time=4)
            return {'CANCELLED'}

        else:
            draw_fading_label(context, text="Make sure the Cursor is in the Field of View", y=120, color=red, time=4)
            return {'PASS_THROUGH'}

    def warp_mouse_out_of_panel(self, context):
        distance = None

        if self.is_sidebar_invocation:
            for region in context.area.regions:
                if region.type == 'UI':
                    distance = - (region.width - (context.region.width - self.mouse_pos.x) + (get_prefs().cast_flick_distance * get_scale(context)))

        else:
            if self.mouse_pos.x < context.region.width / 2:
                distance = (150 * get_scale(context)) + (get_prefs().cast_flick_distance * get_scale(context))

            else:
                distance = - ((300 * get_scale(context)) + (get_prefs().cast_flick_distance * get_scale(context)))

        if distance:
            warp_mouse(self, context, Vector((self.mouse_pos.x + distance, self.mouse_pos.y)))

    def get_hit_data(self, context, debug=False):
        edit_mode_objs = [obj for obj in context.visible_objects if obj.type == 'MESH' and obj.mode == 'EDIT']

        mods = []

        for obj in edit_mode_objs:
            for mod in obj.modifiers:
                if mod.show_viewport:
                    mod.show_viewport = False
                    mods.append(mod)

        cmx = context.scene.cursor.matrix

        hit_data = {'POSITIVE_X': None,
                    'NEGATIVE_X': None,
                    'POSITIVE_Y': None,
                    'NEGATIVE_Y': None,
                    'POSITIVE_Z': None,
                    'NEGATIVE_Z': None}

        cache = {}

        for axis in ['X', 'Y', 'Z']:
            if debug:
                print(axis)

            for direction in [1, -1]:
                axis_dir = cmx.to_3x3() @ (direction * axis_vector_mappings[axis])
                dict_axis = f'POSITIVE_{axis}' if direction == 1 else f"NEGATIVE_{axis}"

                if debug:
                    print("", axis_dir)

                color = red if axis == 'X' else green if axis == 'Y' else blue

                offset = context.region_data.view_distance / 100
                cast_origin = self.cursor_origin + (axis_dir * offset)

                hit, hitobj, hitindex, hitlocation, hitnormal, hitmx = cast_scene_ray(cast_origin, axis_dir, depsgraph=context.evaluated_depsgraph_get(), exclude_wire=True, cache=cache, debug=False)

                is_grid = False

                if hitlocation:
                    if debug:
                        print("  object hit:", hitobj)

                    rot = create_rotation_matrix_from_normal(hitobj, hitnormal)

                else:
                    grid_yz = Vector((1, 0, 0))
                    grid_xz = Vector((0, -1, 0))
                    grid_xy = Vector((0, 0, 1))

                    intersections = []

                    for grid in [grid_yz, grid_xz, grid_xy]:
                        i = intersect_line_plane(self.cursor_origin, self.cursor_origin + axis_dir, Vector(), grid)

                        if i and i != self.cursor_origin:

                            if (i - self.cursor_origin).dot(axis_dir) > 0:

                                intersections.append((grid, i, (i - self.cursor_origin).length))

                    if intersections:
                        is_grid = True

                        closest = min(intersections, key=lambda x: x[2])
                        grid = closest[0]
                        hitlocation = closest[1]

                        if debug:
                            print("  grid hit:", grid)

                        if grid == grid_yz:
                            normal = Vector((1, 0, 0))
                            binormal = Vector((0, 0, 1))
                            tangent = Vector((0, 1, 0))

                        elif grid == grid_xz:
                            normal = Vector((0, -1, 0))
                            binormal = Vector((0, 0, 1))
                            tangent = Vector((1, 0, 0))

                        elif grid == grid_xy:
                            normal = Vector((0, 0, 1))
                            binormal = Vector((0, 1, 0))
                            tangent = Vector((1, 0, 0))

                        if axis_dir.dot(grid) > 0:
                            normal.negate()
                            binormal.negate()

                        rot = Matrix()
                        rot.col[0].xyz = tangent
                        rot.col[1].xyz = binormal
                        rot.col[2].xyz = normal

                if hitlocation:
                    cast_vec = hitlocation - self.cursor_origin

                    if is_grid and cast_vec.length > 100000:
                        continue

                    center_loc = self.cursor_origin + cast_vec / 2

                    if debug:
                        draw_point(hitlocation, color=yellow if is_grid else white, modal=False)
                        draw_point(center_loc, color=yellow if is_grid else white, alpha=0.5, size=4, modal=False)

                        draw_line([self.cursor_origin, hitlocation], color=color, alpha=0.3, modal=False)
                        draw_line([self.cursor_origin, center_loc], color=color, alpha=0.8, modal=False)

                    hit_data[dict_axis] = {'axis': axis_dir,
                                           'is_grid': is_grid,

                                           'loc': hitlocation,
                                           'center_loc': self.cursor_origin + cast_vec / 2,

                                           'rot': rot.to_quaternion(),

                                           'axis_coords': None,
                                           'aligned_axis_coords': None}

        if debug:
            printd(hit_data, "hit data")

        for mod in mods:
            mod.show_viewport =True

        return hit_data

    def create_cursor_axes_previews(self, context):
        size = 1
        axes = [(Vector((1, 0, 0)), red), (Vector((0, 1, 0)), green), (Vector((0, 0, 1)), blue)]

        for direction, hitdata in self.hit_data.items():
            if hitdata:
                loc = hitdata['loc']
                rot = hitdata['rot']

                factor = get_zoom_factor(context, loc, scale=30, ignore_obj_scale=True)

                axis_coords = []
                aligned_axis_coords = []

                for axis, color in axes:

                    coords = []

                    coords.append(loc + (rot @ axis).normalized() * size * factor * 0.1)
                    coords.append(loc + (rot @ axis).normalized() * size * factor)

                    aligned_axis_coords.append((coords, color))

                    coords = []

                    coords.append(loc + (self.init_rotation @ axis).normalized() * size * factor * 0.1)
                    coords.append(loc + (self.init_rotation @ axis).normalized() * size * factor)

                    axis_coords.append((coords, color))

                self.hit_data[direction]['axis_coords'] = axis_coords
                self.hit_data[direction]['aligned_axis_coords'] = aligned_axis_coords

    def set_cursor(self, context):
        hc = context.scene.HC

        hit = self.hit_data[self.flick_direction]
        rot = hit['rot'] if self.align_to_surface else self.init_rotation

        set_cursor(location=hit['center_loc'] if self.center_cast else hit['loc'], rotation=rot)

        if hc.use_world and self.init_rotation != rot:
            hc.avoid_update = True
            hc.use_world = False

        if hc.focus_cast:
            bpy.ops.view3d.view_center_cursor('INVOKE_DEFAULT' if hc.focus_mode == 'SOFT' else 'EXEC_DEFAULT')

def draw_point_cursor_status(op):
    def draw(self, context):
        layout = self.layout

        row = layout.row(align=True)

        row.label(text="Point Cursor")

        draw_status_item(row, key='LMB', text="Finish")
        draw_status_item(row, key='RMB', text="Cancel")

        row.separator(factor=10)

        if op.S.hit:
            target = 'Edge' if op.align_x_axis or op.align_y_axis else "Face"
        else:
            target = 'None' if op.align_x_axis or op.align_y_axis else "World Z"

        draw_status_item(row, active=target != "None", key='MOVE', text="Pick Target", prop=target)

        draw_status_item(row, active=op.align_x_axis, key='CTRL', text="Align X Axis", gap=2)
        draw_status_item(row, active=op.align_y_axis, key='ALT', text="Align Y Axis", gap=1)

        if op.can_point_selection:
            draw_status_item(row, active=op.point_selection, key='S', text="Point Selection", gap=2)

        draw_status_item(row, active=op.set_transform_orientation, key='T', text="Transform Orietnation", gap=2)

    return draw

class PointCursor(bpy.types.Operator, Settings):
    bl_idname = "machin3.point_cursor"
    bl_label = "MACHIN3: Point Cursor"
    bl_description = "Point Cursor's Z or Y Axis"
    bl_options = {'REGISTER', 'UNDO'}

    instant: BoolProperty(name="Instantly Align Z with Target Surface", description="Prevents Modal Execution and potential Y-Axis-to-Edge Alignment")

    align_x_axis: BoolProperty(name="is X Axis", description="Align the X Axis to an Edge, instead of the Z axis to a Face")
    align_y_axis: BoolProperty(name="is Y Axis", description="Align the Y Axis to an Edge, instead of the Z axis to a Face")

    set_transform_orientation: BoolProperty(name="Set Transform Orientation", description="Set Blender's Transform Orientation to Cursor", default=False)
    @classmethod
    def poll(cls, context):
        return is_3dview(context)

    def draw_HUD(self, context):
        if context.area == self.area:
            draw_init(self)

            dims = draw_label(context, title="Point ", coords=Vector((self.HUD_x, self.HUD_y)), center=False, alpha=1)
            title, color = ("Selection's ", blue) if self.point_selection else ("Cursor's ", green)
            dims += draw_label(context, title=title, coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, color=color, alpha=1)
            dims += draw_label(context, title=f"{'X' if self.align_x_axis else 'Y' if self.align_y_axis else 'Z'}", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, color=red if self.align_x_axis else green if self.align_y_axis else blue, alpha=1)
            draw_label(context, title=" Axis", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, alpha=0.5)

            self.offset += 18

            if self.S.hit:
                dims = draw_label(context, title=f"{self.S.hitobj.name} ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=1)

                if self.align_x_axis or self.align_y_axis:
                    draw_label(context, title=f"Edge: {self.edge_index}", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=yellow, alpha=1)

                else:
                    draw_label(context, title=f"Face: {self.S.hitindex}", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=yellow, alpha=1)

            else:
                if self.align_x_axis or self.align_y_axis:
                    draw_label(context, title="None", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=red, alpha=1)
                else:
                    draw_label(context, title="World Z", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=blue, alpha=1)

            if self.set_transform_orientation:
                self.offset += 18

                draw_label(context, title="Set Transform Orientation", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=green, alpha=1)

    def draw_VIEW3D(self, context):
        if context.area == self.area:

            if self.S.hit:
                if self.align_x_axis:
                    draw_tris(self.tri_coords, color=red, alpha=0.03)
                    draw_point(self.edge_start_co, color=white, size=4)
                    draw_vector(self.edge_dir, origin=self.edge_start_co, color=red, width=2, alpha=1, fade=True)

                elif self.align_y_axis:
                    draw_tris(self.tri_coords, color=green, alpha=0.03)
                    draw_point(self.edge_start_co, color=white, size=4)
                    draw_vector(self.edge_dir, origin=self.edge_start_co, color=green, width=2, alpha=1, fade=True)

                else:
                    draw_point(self.S.hitlocation, color=white, size=4)
                    draw_vector(self.S.hitnormal * self.factor, origin=self.S.hitlocation, color=blue, width=2, alpha=1, fade=True)

            axes = [(Vector((1, 0, 0)), red), (Vector((0, 1, 0)), green), (Vector((0, 0, 1)), blue)]
            size = 1.5

            if self.point_selection:
                for data in self.selection.values():
                    factor = get_zoom_factor(context, data['loc'], scale=30, ignore_obj_scale=True)

                    for axis, color in axes:
                        coords = []

                        coords.append(data['loc'] + (data['rot'] @ axis).normalized() * size * factor * 0.1)
                        coords.append(data['loc'] + (data['rot'] @ axis).normalized() * size * factor)

                        draw_line(coords, color=color, width=2, alpha=1)

                    for batch in data['batches']:
                        draw_batch(batch, color=blue, alpha=0.25, xray=True)
                        draw_batch(batch, color=blue, alpha=0.5, xray=False)

            else:
                factor = get_zoom_factor(context, self.cursor_loc, scale=30, ignore_obj_scale=True)

                for axis, color in axes:
                    coords = []

                    coords.append(self.cursor_loc + (self.cursor_rot @ axis).normalized() * size * factor * 0.1)
                    coords.append(self.cursor_loc + (self.cursor_rot @ axis).normalized() * size * factor)

                    draw_line(coords, color=color, width=2, alpha=1)

    def modal(self, context, event):
        context.area.tag_redraw()

        update_mod_keys(self, event)

        self.align_x_axis = self.is_ctrl
        self.align_y_axis = self.is_alt and not self.is_ctrl

        events = ['MOUSEMOVE', 'T']

        if self.can_point_selection:
            events.append('S')

        if event.type in events:
            if event.type in ['MOUSEMOVE']:
                get_mouse_pos(self, context, event)

                self.S.get_hit(self.mouse_pos)

                if self.S.hit:
                    self.factor = get_zoom_factor(context, self.S.hitlocation, scale=100, ignore_obj_scale=True)

            elif event.type == 'S' and event.value == 'PRESS':
                self.point_selection = not self.point_selection

                force_ui_update(context)

            elif event.type == 'T' and event.value == 'PRESS':
                self.set_transform_orientation = not self.set_transform_orientation

                force_ui_update(context)

        if self.S.hit and (self.align_x_axis or self.align_y_axis):
            self.get_edge_coords(context)

        else:
            self.edge_index = None
            self.edge_start_co = None
            self.tri_coords = []
            self.edge_dir = None

            force_ui_update(context)

        direction = self.edge_dir.normalized() if (self.align_x_axis or self.align_y_axis) and self.edge_dir else self.S.hitnormal if self.S.hit else Vector((0, 0, 1))

        if direction:
            if self.point_selection:
                self.get_pointed_obj_matrices(context, direction=direction)

                self.update_selection_batches()

            else:
                self.pointed_cursor_mx = self.get_pointed_cursor_mx(context, direction=direction)

        if navigation_passthrough(event, alt=False, wheel=True):
            return {'PASS_THROUGH'}

        elif event.type in {'LEFTMOUSE', 'SPACE'} and event.value == 'PRESS':
            self.finish(context)

            if self.point_selection:

                objects = filter_non_child_objects([obj for obj in self.selection.keys()])

                for obj in objects:
                    obj.matrix_world = self.selection[obj]['pointed_mx']

            else:
                context.scene.cursor.matrix = self.pointed_cursor_mx

                hc = context.scene.HC

                if hc.use_world:
                    hc.avoid_update = True
                    hc.use_world = False

                hc.show_gizmos = event.type == 'LEFTMOUSE'

            if self.set_transform_orientation:
                context.scene.transform_orientation_slots[0].type = 'CURSOR'

            self.save_settings()
            return {'FINISHED'}

        elif event.type in ['RIGHTMOUSE', 'ESC']:
            self.finish(context)
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def finish(self, context):
        finish_modal_handlers(self)

        finish_status(self)

        force_ui_update(context)

        restore_gizmos(self)

        if self.was_cursor_toggled:
            context.space_data.overlay.show_cursor = True

        self.S.finish()

    def invoke(self, context, event):
        HC.init_operator_defaults(self.bl_idname, self.properties, include=['set_transform_orientation'], debug=False)
        self.init_settings(props=['set_transform_orientation'])
        self.load_settings()

        get_mouse_pos(self, context, event)

        self.S = Snap(context, exclude_wire=True, debug=False)
        self.S.get_hit(self.mouse_pos)

        self.edge_index = None
        self.edge_start_co = None
        self.edge_dir = None
        self.tri_coords = []
        self.edge_dir = None

        self.align_x_axis = False
        self.align_y_axis = False

        update_mod_keys(self)

        self.pointed_cursor_mx = self.get_pointed_cursor_mx(context, direction=self.S.hitnormal if self.S.hit else Vector((0, 0, 1)))

        if self.instant:
            context.scene.cursor.matrix = self.pointed_cursor_mx

            if self.set_transform_orientation:
                context.scene.transform_orientation_slots[0].type = 'CURSOR'

            force_ui_update(context)

            self.S.finish()
            return {'FINISHED'}

        self.cursor_loc, self.cursor_rot, _ = self.pointed_cursor_mx.decompose()

        self.factor = get_zoom_factor(context, self.S.hitlocation, scale=100, ignore_obj_scale=True) if self.S.hit else 1

        self.can_point_selection = context.mode == 'OBJECT' and bool(context.selected_objects)
        self.point_selection = False

        if self.can_point_selection:

                dg = context.evaluated_depsgraph_get()

                self.selection = {obj: {'name': obj.name,
                                        'mx': obj.matrix_world,
                                        'pointed_mx': None,
                                        'loc': obj.matrix_world.decompose()[0],
                                        'rot': obj.matrix_world.decompose()[1],
                                        'local_space_batch': get_batch_from_obj(dg, obj, world_space=False, single_icol_batch=False),
                                        'batches': None} for obj in context.selected_objects}

                self.get_pointed_obj_matrices(context, direction=self.S.hitnormal if self.S.hit else Vector((0, 0, 1)))

                self.update_selection_batches()

        hide_gizmos(self, context)

        if context.space_data.overlay.show_cursor:
            context.space_data.overlay.show_cursor = False
            self.was_cursor_toggled = True
        else:
            self.was_cursor_toggled = False

        context.window.cursor_set('DEFAULT')

        init_status(self, context, func=draw_point_cursor_status(self))

        force_ui_update(context)

        init_modal_handlers(self, context, hud=True, view3d=True)
        return {'RUNNING_MODAL'}

    def get_pointed_cursor_mx(self, context, direction):
        cmx = context.scene.cursor.matrix

        if self.align_x_axis:
            axis_dir = cmx.to_3x3() @ Vector((1, 0, 0))

        elif self.align_y_axis:
            axis_dir = cmx.to_3x3() @ Vector((0, 1, 0))

        else:
            axis_dir = cmx.to_3x3() @ Vector((0, 0, 1))

        deltarot = axis_dir.rotation_difference(direction)

        loc, rot, sca = cmx.decompose()
        pointedmx = Matrix.LocRotScale(loc, deltarot @ rot, sca)

        self.cursor_rot = deltarot @ rot

        return pointedmx

    def get_pointed_obj_matrices(self, context, direction):
        def get_pointed_obj_mx(context, direction, data):
            omx = data['mx']

            if self.align_x_axis:
                axis_dir = omx.to_3x3() @ Vector((1, 0, 0))

            elif self.align_y_axis:
                axis_dir = omx.to_3x3() @ Vector((0, 1, 0))

            else:
                axis_dir = omx.to_3x3() @ Vector((0, 0, 1))

            deltarot = axis_dir.rotation_difference(direction)

            loc, rot, sca = omx.decompose()
            data['pointed_mx'] = Matrix.LocRotScale(loc, deltarot @ rot, sca)

            data['rot'] = deltarot @ rot

        for obj, data in self.selection.items():
            get_pointed_obj_mx(context, direction, data)

    def update_selection_batches(self):
        for obj, data in self.selection.items():
            if data['local_space_batch'][2] == 'INSTANCE_COLLECTION_MULTI_MESH_EVAL':
                batches = data['local_space_batch'][0]
                data['batches'] = [transform_batch(batch, data['pointed_mx']) for batch in batches]

            else:
                data['batches'] = [transform_batch(data['local_space_batch'], data['pointed_mx'])]

    def get_edge_coords(self, context):
        hitmx = self.S.hitmx
        hit_co = hitmx.inverted_safe() @ self.S.hitlocation

        hitface = self.S.hitface

        self.tri_coords = self.S.cache.tri_coords[self.S.hitobj.name][self.S.hitindex]

        closest_edge = min([(e, (hit_co - intersect_point_line(hit_co, e.verts[0].co, e.verts[1].co)[0]).length, (hit_co - get_center_between_verts(*e.verts)).length) for e in hitface.edges if e.calc_length()], key=lambda x: (x[1] * x[2]) / x[0].calc_length())[0]

        self.edge_index = closest_edge.index

        edge_coords = [hitmx @ v.co for v in closest_edge.verts]

        self.edge_start_co = max([((co - self.S.hitlocation).length, co) for co in edge_coords], key=lambda x: x[0])[1]

        sorted_edge_coords = sorted([((co - self.S.hitlocation).length, co) for co in edge_coords], key=lambda x: x[0])

        self.edge_dir = sorted_edge_coords[0][1] - sorted_edge_coords[1][1]
