from re import A
import bpy
from bpy.props import EnumProperty, BoolProperty, FloatProperty, IntProperty, StringProperty
import bmesh

from bpy.types import ThemeDopeSheet
from mathutils import Vector, Matrix, Quaternion
from mathutils.geometry import intersect_line_plane, intersect_point_line
from math import radians, degrees, tan, sqrt
from itertools import zip_longest

from .. utils.asset import get_pretty_assetpath
from .. utils.bmesh import ensure_edge_glayer, ensure_gizmo_layers, is_edge_concave
from .. utils.collection import ensure_visible_collection
from .. utils.curve import get_curve_as_dict, get_profile_coords_from_spline, verify_curve_data
from .. utils.draw import draw_fading_label, draw_init, draw_label, draw_line, draw_batch, draw_point, draw_tris, draw_vector, draw_points
from .. utils.gizmo import hide_gizmos, restore_gizmos
from .. utils.history import add_history_entry
from .. utils.math import dynamic_snap, dynamic_format, average_locations, average_normals, create_rotation_matrix_from_vectors, get_center_between_verts, mirror_coords
from .. utils.mesh import get_bbox
from .. utils.modifier import add_boolean, add_subdivision, add_cast, add_mirror, get_edge_bevel_from_edge_vgroup, get_edge_bevel_from_edge_weight, get_subdivision, get_cast, get_auto_smooth, apply_mod, add_bevel, bevel_poll, is_edge_bevel, is_invalid_auto_smooth, is_remote_mod_obj, mirror_poll, remote_boolean_poll, remove_mod, sort_modifiers, hook_poll, create_bevel_profile
from .. utils.object import get_batch_from_obj, get_eval_bbox, hide_render, is_valid_object, meshcut, parent, is_uniform_scale, is_wire_object, remove_obj, setup_split_boolean
from .. utils.property import shorten_float_string, step_enum, step_list
from .. utils.raycast import cast_bvh_ray_from_mouse, get_closest, cast_scene_ray_from_mouse
from .. utils.registration import get_prefs
from .. utils.system import printd
from .. utils.tools import active_tool_is_hypercursor
from .. utils.ui import draw_status_item_numeric, finish_modal_handlers, get_mouse_pos, ignore_events, init_modal_handlers, is_on_screen, navigation_passthrough, get_zoom_factor, scroll, update_mod_keys, warp_mouse, wrap_mouse, init_status, finish_status, scroll_up, scroll_down, force_ui_update, get_scale, draw_status_item
from .. utils.vgroup import add_vgroup
from .. utils.view import get_location_2d, get_view_origin_and_dir
from .. utils.workspace import get_assetbrowser_area

from .. items import add_object_items, axis_items, add_cylinder_side_items, add_boolean_method_items, add_boolean_solver_items, number_mappings, display_type_items, boolean_display_type_items, numeric_input_event_items, pipe_round_mode_items, axis_vector_mappings, pipe_origin_items, numbers, input_mappings, index_axis_mappings, alt, boolean_color_mappings
from .. colors import green, red, normal, blue, yellow, orange, white

def draw_add_status(op):
    def draw(self, context):
        layout = self.layout

        row = layout.row(align=True)

        row.label(text=f"Add {op.type.title()}")

        if op.is_numeric_input:
            draw_status_item(row, key='RETURN', text="Finish")
            draw_status_item(row, key='ESC', text="Cancel")
            draw_status_item(row, key='TAB', text="Abort Numeric Input")

            draw_status_item_numeric(op, row, invert=False, gap=10)

        else:
            draw_status_item(row, key='LMB', text="Finish")

            if op.is_in_history:
                draw_status_item(row, key='MMB', text="Finish with Previous Size")

            draw_status_item(row, key='RMB', text="Cancel")
            draw_status_item(row, key='TAB', text="Enter Numeric Input")

            row.separator(factor=10)

            draw_status_item(row, key='MOVE', text="Size", prop=dynamic_format(op.size, decimal_offset=1 if op.is_snapping and op.is_incremental else 0 if op.is_snapping else 2))

            draw_status_item(row, active=op.is_snapping, key='CTRL', text="Dynamic Snap", gap=1)

            if op.is_snapping:
                draw_status_item(row, active=op.is_incremental, key='ALT', text="Incremental Snap", gap=1)

            if op.type == 'CYLINDER':
                draw_status_item(row, active=not op.boolean, key='MMB_SCROLL', text="Sides", prop=op.sides, gap=1)

                draw_status_item(row, active=op.use_side_presets and not op.boolean, key='Q', text="Presets", gap=1)

            elif op.type == 'ASSET':
                draw_status_item(row, key='R', text="Rotate", prop=op.HUD_angle, gap=1)

            if op.boolean_host and op.is_obj_mesh:

                if not (op.type in ['CUBE', 'CYLINDER'] and op.is_plane):

                    draw_status_item(row, active=op.can_boolean and op.boolean, key='B', text="Boolean", gap=2)

                    if op.can_boolean and op.boolean:
                        draw_status_item(row, active=op.boolean, key='MMB_SCROLL', text="Method", prop=op.boolean_method.title(), gap=1)

                        if op.boolean_method != 'MESHCUT':
                            draw_status_item(row, active=op.boolean, key='E', text="Solver", prop=op.boolean_solver.title(), gap=1)

                        if op.boolean_method not in ['SPLIT', 'MESHCUT']:
                            draw_status_item(row, active=op.boolean, key=['SHIFT', 'W'], text="Display", prop=op.obj.display_type.title(), gap=1)

            if op.can_surface_place:
                draw_status_item(row, active=op.is_surface, key='S', text="Surface Placement", gap=2)
                draw_status_item(row, active=op.is_embed, key='D', text="Embedded Placement", gap=1)

                if op.is_embed:
                    draw_status_item(row, key=['SHIFT', 'MMB_SCROLL'], text="Depth", prop=round(op.embed_depth, 1), gap=1)

            if op.type in ['CYLINDER', 'ASSET'] or (op.type == 'CUBE' and op.is_plane):
                draw_status_item(row, key=['X', 'Y', 'Z'], text="Align Axis", prop=op.align_axis, gap=1)

            if op.type == 'CUBE':
                if not op.is_plane:
                    draw_status_item(row, active=op.is_quad_sphere, key='Q', text="Quad Sphere", gap=2)

                    draw_status_item(row, active=op.is_rounded, key='R', text="Rounded Cube", gap=1)

                    if op.is_rounded:
                        if bpy.app.version >= (4, 3, 0):
                            draw_status_item(row, key=[1, 2, 3], text=f"Bevel Mods: {op.bevel_count}", gap=1)

                        draw_status_item(row, key=['ALT', 'MMB_SCROLL'], text="Segments", prop=op.bevel_segments, gap=1)

                draw_status_item(row, active=op.is_plane, key='C', text="Plane", gap=2 if op.is_plane else 1)

                if not op.is_rounded:
                    draw_status_item(row, active=op.is_subd or op.is_quad_sphere, key=[1, 2, 3, 4, 5], text=f"Subdivisions: {op.subdivisions}", gap=1)

            elif op.type in 'CYLINDER':
                if not op.is_plane:
                    draw_status_item(row, active=op.is_rounded, key='R', text="Rounded Cylinder", gap=1)

                    if op.is_rounded:
                        if bpy.app.version >= (4, 3, 0):
                            draw_status_item(row, key=[1, 2], text=f"Bevel Mods: {op.bevel_count}", gap=1)

                        draw_status_item(row, key=['ALT', 'MMB_SCROLL'], text="Segments", prop=op.bevel_segments, gap=1)

                draw_status_item(row, active=op.is_plane, key='C', text="Circle", gap=2 if op.is_plane else 1)

                draw_status_item(row, active=op.is_half, key='V', text="Half", gap=1)

            if op.is_scale_appliable:
                draw_status_item(row, active=op.apply_scale, key='A', text="Apply Scale", gap=2)

            if op.type in 'ASSET' and op.has_subset_mirror:
                draw_status_item(row, active=op.is_subset_mirror, key='M', text="Subset Mirror", gap=2)

            draw_status_item(row, active=op.is_wireframe_overlay, key='W', text="Wire Overlay", gap=2)

    return draw

class AddObjectAtCursor(bpy.types.Operator):
    bl_idname = "machin3.add_object_at_cursor"
    bl_label = "MACHIN3: Add Object at Cursor"
    bl_options = {'REGISTER', 'UNDO'}

    is_drop: BoolProperty(name="is Drop Asset", default=False)
    type: EnumProperty(name="Add Object Type", items=add_object_items, default='CUBE')

    def update_is_surface(self, context):
        if not self.is_interactive:
            if self.avoid_update:
                self.avoid_update = False
                return

            if self.is_surface:
                if self.is_embed:
                    self.avoid_update = True
                    self.is_embed = False

    def update_is_embed(self, context):
        if not self.is_interactive:
            if self.avoid_update:
                self.avoid_update = False
                return

            if self.is_embed:
                if self.is_surface:
                    self.avoid_update = True
                    self.is_surface = False

    def update_rotation_offset(self, context):
        if not self.is_interactive:
            if self.avoid_update:
                self.avoid_update = False
                return

            if self.rotation_offset > 360:
                self.avoid_update = True
                self.rotation_offset = 360

            elif self.rotation_offset < 0:
                self.avoid_update = True
                self.rotation_offset = 360 + self.rotation_offset

    is_surface: BoolProperty(name="Add Object at Cursor's Surface (Z-Plane)", description='Place Object on Surface', default=True, update=update_is_surface)
    is_embed: BoolProperty(name="Add Object embedded in Cursor's Surface (Z-Plane)", description='Embed Object in Surface', default=False, update=update_is_embed)
    embed_depth: FloatProperty(name="Embed Depth", default=0.1, min=0.1, max=0.9)
    rotation_offset: IntProperty(name="Rotation Offset", default=0, update=update_rotation_offset)
    align_axis: EnumProperty(name="Align with Axis", items=axis_items, default='Z')
    apply_scale: BoolProperty(name="Apply Scale", default=True)

    def update_is_quad_sphere(self, context):
        if not self.is_interactive:
            if self.avoid_update:
                self.avoid_update = False
                return

            if self.is_quad_sphere:

                if not self.is_subd:
                    self.avoid_update = True
                    self.is_subd = True

                if self.is_rounded:
                    self.avoid_update = True
                    self.is_rounded = False

                if self.is_plane:
                    self.avoid_update = True
                    self.is_plane = False

            else:
                if self.is_subd:
                    self.avoid_update = True
                    self.is_subd = False

    def update_is_plane(self, context):
        if not self.is_interactive:
            if self.avoid_update:
                self.avoid_update = False
                return

            if self.is_plane:

                if self.is_quad_sphere:
                    self.avoid_update = True
                    self.is_quad_sphere = False

                    if self.is_subd:
                        self.avoid_update = True
                        self.is_subd = False

                if self.is_rounded:
                    self.avoid_update = True
                    self.is_rounded = False

                if self.is_surface:
                    self.avoid_update = True
                    self.is_surface = False

                if self.is_embed:
                    self.avoid_update = True
                    self.is_embed = False

            else:
                if self.type == 'CUBE':
                    self.align_axis = 'Z'

    def update_is_rounded(self, context):
        if not self.is_interactive:
            if self.avoid_update:
                self.avoid_update = False
                return

            if self.is_rounded:

                if self.is_quad_sphere:
                    self.avoid_update = True
                    self.is_quad_sphere = False

                if self.is_subd:
                    self.avoid_update = True
                    self.is_subd = False

                if self.is_plane:
                    self.avoid_update = True
                    self.is_plane = False

    def update_is_subd(self, context):
        if not self.is_interactive:
            if self.avoid_update:
                self.avoid_update = False
                return

            if self.is_subd:

                if self.is_rounded:
                    self.avoid_update = True
                    self.is_rounded = False

    size: FloatProperty(name="Size of Object", default=1)
    sides: IntProperty(name="Sides", default=32, min=3)
    is_quad_sphere: BoolProperty(name="is Quad Sphere", default=False, update=update_is_quad_sphere)
    is_plane: BoolProperty(name="is Plane", default=False, update=update_is_plane)
    is_subd: BoolProperty(name="is SubD", default=False, update=update_is_subd)
    subdivisions: IntProperty(name="Subdivide", default=3, min=1, max=5)
    is_rounded: BoolProperty(name="is Rounded", default=False, update=update_is_rounded)
    bevel_count: IntProperty(name="Bevel Mod Count", default=2, min=1, max=3)
    bevel_segments: IntProperty(name="Bevel Segments", default=0, min=0)
    is_half: BoolProperty(name="is Semi", default=False)
    is_subset_mirror: BoolProperty(name="is Subset MIrror", default=True)

    boolean: BoolProperty(name="Boolean", default=False)
    boolean_method: EnumProperty(name="Method", items=add_boolean_method_items, default='DIFFERENCE')
    boolean_solver: EnumProperty(name="Solver", items=add_boolean_solver_items, default='MANIFOLD' if bpy.app.version >= (4, 5, 0) else 'FAST')
    boolean_display_type: EnumProperty(name="Boolean Display Type", items=display_type_items, default='WIRE')
    hide_boolean: BoolProperty(name="Hide Boolean", default=False)

    use_side_presets: BoolProperty(name="Adjust Cylidner Sides via Presets", default=True)
    is_scale_appliable: BoolProperty(name="is Scale appliable", default=False)
    is_in_history: BoolProperty(name="is Object in History", default=False)
    is_pipe_init: BoolProperty(name="is Pipe Init", default=False)  # used for MACHIN3tools screencasting

    is_numeric_input: BoolProperty()
    is_numeric_input_marked: BoolProperty()
    numeric_input_size: StringProperty(name="Numeric Size", description="Size of Object entered numerically", default='0')

    is_interactive: BoolProperty()
    avoid_update: BoolProperty()

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            return active_tool_is_hypercursor(context)

    @classmethod
    def description(cls, context, properties):
        if properties:
            desc = f"Drag out {properties.type.title()} from Cursor\nALT: Repeat Size and other props\nCTRL: Unit Size"

            if properties.type == 'CYLINDER':
                desc += "\nSHIFT: Initialize Pipe"

            return desc
        return "Invalid Context"

    def draw(self, context):
        layout = self.layout
        column = layout.column(align=True)

        if self.type == 'CUBE':
            row = column.row(align=True)

            row.prop(self, 'is_plane', text='Plane', toggle=True)
            row.prop(self, 'is_rounded', text='Rounded', toggle=True)
            row.prop(self, 'is_subd', text='Subdivided', toggle=True)
            row.prop(self, 'is_quad_sphere', text='Quad Sphere', toggle=True)

        elif self.type == 'CYLINDER':
            row = column.row(align=True)

            row.prop(self, 'is_plane', text='Circle', toggle=True)
            row.prop(self, 'is_rounded', text='Rounded', toggle=True)
            row.prop(self, 'is_half', text='Half', toggle=True)

        row = column.row(align=True)
        row.prop(self, 'size', text='Size')

        if self.type == 'CUBE':
            if self.is_subd:
                row.prop(self, 'subdivisions', text='Subdivisions')

            elif self.is_rounded:
                row.prop(self, 'bevel_count', text='Mods')
                row.prop(self, 'bevel_segments', text='Segments')

        elif self.type == 'CYLINDER':
            row.prop(self, 'sides', text='Sides')

            if self.is_rounded:
                row.prop(self, 'bevel_count', text='Mods')
                row.prop(self, 'bevel_segments', text='Segments')

        elif self.type == 'ASSET':
            row.prop(self, 'rotation_offset', text='Rotation')

        if self.can_surface_place:
            column.separator()
            row = column.row(align=True)

            row.prop(self, 'is_surface', text='on Surface', toggle=True)
            row.prop(self, 'is_embed', text='Embedded', toggle=True)

            r = row.row(align=True)
            r.active = self.is_embed
            r.prop(self, 'embed_depth', text='Depth')

        if self.type in ['CYLINDER', 'ASSET'] or (self.type in 'CUBE' and self.is_plane):
            if self.is_plane and self.align_axis == 'Z':
                column.separator()

            row = column.row(align=True)

            row.prop(self, 'align_axis', text='Align with Cursor Axis', expand=True)

        if self.boolean_host and self.is_obj_mesh:
            column.separator()

            row = column.row(align=True)

            split = row.split(factor=0.49, align=True)
            split.prop(self, 'boolean', text='Setup Boolean', toggle=True)

            r = split.row(align=True)
            r.active = self.boolean
            r.prop(self, 'boolean_solver', text='Solver', expand=True)

            row = column.row(align=True)
            row.active = self.boolean
            row.prop(self, 'boolean_method', text='Method', expand=True)

            row = column.row(align=True)
            row.active = self.boolean
            row.prop(self, 'hide_boolean', text='Hide Boolean Objects', toggle=True)

        if self.is_scale_appliable:
            column.separator()

            column.prop(self, 'apply_scale', text='Apply Scale', toggle=True)

    def draw_HUD(self, context):
        if context.area == self.area:
            draw_init(self)

            if not self.is_numeric_input:
                placement_origin = self.placement_origin_2d.resized(3)

                draw_point(placement_origin, size=4, alpha=0.5)
                draw_vector(self.mouse_pos.resized(3) - placement_origin, origin=placement_origin, alpha=0.2, fade=True)

            if self.type == 'CUBE':
                dims = draw_label(context, title="Add Cube ", coords=Vector((self.HUD_x, self.HUD_y)), center=False)

                if self.is_quad_sphere:
                    draw_label(context, title="Quad Sphere", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, size=10, color=green)

                elif self.is_subd:
                    draw_label(context, title="Subdivided", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, size=10, color=green)

                elif self.is_rounded:
                    draw_label(context, title="Rounded", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, size=10, color=green)

                elif self.is_plane:
                    draw_label(context, title="Plane", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, size=10, color=green)

            elif self.type == 'CYLINDER':
                dims = draw_label(context, title="Add Cylinder ", coords=Vector((self.HUD_x, self.HUD_y)), center=False)

                if self.is_rounded:
                    dims += draw_label(context, title="Rounded ", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, size=10, color=green)

                elif self.is_plane:
                    dims += draw_label(context, title="Circle ", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, size=10, color=green)

                if self.is_half:
                    draw_label(context, title="Half", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, size=10, color=red)

            elif self.type == 'ASSET':
                dims = draw_label(context, title="Add Asset ", coords=Vector((self.HUD_x, self.HUD_y)), center=False)

                pretty = get_pretty_assetpath(self.asset)
                pretty_split = pretty.split('•')

                if len(pretty_split) > 1:
                    dims += draw_label(context, title='•'.join(pretty_split[:-1]) + '•', coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, size=10, alpha=0.5)
                    draw_label(context, title=pretty_split[-1], coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, color=yellow)

                else:
                    draw_label(context, title=get_pretty_assetpath(self.obj), coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, color=yellow)

            if self.boolean and self.obj.type == 'MESH':
                self.offset += 18

                color = boolean_color_mappings[self.boolean_method]
                title = 'Meshcut' if self.boolean_method == 'MESHCUT' else f"{self.boolean_solver.title()} Boolean {self.boolean_method.title()}"
                draw_label(context, title=title, coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, color=color, center=False)

                if self.boolean_host:
                    self.offset += 12

                    dims = draw_label(context, title="with ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, size=10, alpha=0.5)
                    dims += draw_label(context, title=self.boolean_host.name, coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, size=10, center=False)

                    if not self.can_boolean and self.size > 0.00002:
                        dims += draw_label(context, title=" ⚠", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, size=20, color=yellow, center=False)
                        draw_label(context, title=" Out of Range!", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, size=10, color=yellow, center=False)

            if self.is_surface and self.obj.type != 'EMPTY':
                self.offset += 18

                dims = draw_label(context, title="on Surface ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=yellow)

            elif self.is_embed and self.obj.type != 'EMPTY':
                self.offset += 18

                dims = draw_label(context, title="Embedded: ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=yellow, alpha=1)
                dims += draw_label(context, title=f"{round(self.embed_depth, 1)} ", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False)

            elif (self.type in ['CYLINDER', 'ASSET'] or (self.type == 'CUBE' and self.is_plane)) and self.align_axis in ['X', 'Y']:
                self.offset += 18

                dims = Vector((0, 0))

            if (self.type in ['CYLINDER', 'ASSET'] or (self.type == 'CUBE' and self.is_plane)) and self.align_axis in ['X', 'Y']:
                draw_label(context, title=f"Cursor {self.align_axis} Aligned", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=red if self.align_axis == 'X' else green)

            self.offset += 18

            dims = draw_label(context, title="Size:", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, alpha=0.5)

            title = "🖩" if self.is_numeric_input else " "
            dims += draw_label(context, title=title, coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset + 3, center=False, size=20, color=green, alpha=0.5)

            if self.is_numeric_input:
                dims_numeric = draw_label(context, title=self.numeric_input_size, coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=green, alpha=1)

                if self.is_numeric_input_marked:
                    ui_scale = get_scale(context)

                    coords = [Vector((self.HUD_x + dims.x, self.HUD_y - (self.offset - 5) * ui_scale, 0)), Vector((self.HUD_x + dims.x + dims_numeric.x, self.HUD_y - (self.offset - 5) * ui_scale, 0))]
                    draw_line(coords, width=12 + 8 * ui_scale, color=green, alpha=0.1, screen=True)

            else:
                size = f"{dynamic_format(self.size, decimal_offset=1 if self.is_snapping and self.is_incremental else 0 if self.is_snapping else 2)}"
                dims += draw_label(context, title=size, coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False)

                if self.is_in_history:
                    redoCOL = context.scene.HC.redoaddobjCOL
                    name = self.type if self.type in ['CUBE', 'CYLINDER'] else self.asset['assetpath']

                    entry_size = f"{dynamic_format(redoCOL[name].size, decimal_offset=2)}"
                    dims += draw_label(context, title=f" / {entry_size}", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, alpha=0.5)

                if self.is_snapping:
                    draw_label(context, title=f" {'Dynamic Incremental' if self.is_incremental else 'Dynamic'} Snapping", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=yellow)

            if self.type == 'CYLINDER':
                self.offset += 18

                dims = draw_label(context, title="Sides: ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, alpha=0.5)

                if self.use_side_presets:

                    if self.prev_sides < self.sides:
                        dims += draw_label(context, title=f"{self.prev_sides} ", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=0.3)

                    dims += draw_label(context, title=f"{self.sides} ", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=yellow, alpha=1)

                    if self.next_sides > self.sides:
                        dims += draw_label(context, title=f"{self.next_sides}", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=0.3)

                    draw_label(context, title=' Presets', coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, size=12, color=normal, alpha=1)

                else:
                    draw_label(context, title=str(self.sides), coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, size=12)

            elif self.type == 'ASSET' and self.HUD_angle:
                self.offset += 18

                dims = draw_label(context, title="Rotate: ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, alpha=0.5)
                draw_label(context, title=str(self.HUD_angle), coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False)

            if self.is_rounded:
                self.offset += 18

                bevel_count = len([mod for mod in self.obj.modifiers if 'Edge Bevel' in mod.name])
                draw_label(context, title=f"{'Chamfer' if self.bevel_segments == 0 else 'Bevel'} Mods: {bevel_count} | Segments: {self.bevel_segments}", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, color=blue, center=False)

            if self.is_subd:
                self.offset += 18
                draw_label(context, title=f"Subdivisions: {self.subdivisions}", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, color=blue, center=False)

            if self.is_scale_appliable and self.apply_scale:
                self.offset += 18
                draw_label(context, title="Apply Scale", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=red)

            if self.is_wireframe_overlay:
                self.offset += 18
                draw_label(context, title="Wireframe", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=blue)

            if self.type == 'ASSET' and self.has_subset_mirror:
                self.offset += 18

                color, alpha = (green, 1) if self.is_subset_mirror else (white, 0.25)
                draw_label(context, title="Subset Mirror", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=color, alpha=alpha)

    def draw_VIEW3D(self, context):
        if context.area == self.area:

            if self.has_subset_mirror and self.is_subset_mirror:
                for batch, color in self.subset_batches:
                    draw_batch(batch, color=color, alpha=0.25)

            if self.surface_plane_coords and not (self.boolean and self.boolean_method in ['DIFFERENCE', 'INTERSECT', 'SPLIT', 'MESHCUT']):
                draw_tris(self.surface_plane_coords, indices=[(0, 1, 2), (0, 2, 3)], color=blue, alpha=0.15, xray=False)

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
        if self.boolean and self.boolean_host and self.boolean_method in ['SPLIT', 'MESHCUT']:
            self.boolean_host.select_set(False)

        finish_modal_handlers(self)

        finish_status(self)

        restore_gizmos(self)

        context.space_data.overlay.show_wireframes = self.init_wireframe_overlay

        if self.toggled_use_enter_edit_mode:
            context.preferences.edit.use_enter_edit_mode = True

        self.is_interactive = False

        force_ui_update(context)

    def invoke(self, context, event):
        if self.type == 'CYLINDER' and event.shift:
            bpy.ops.machin3.add_pipe('INVOKE_DEFAULT')
            return {'FINISHED'}

        self.obj = None
        self.asset = {}
        self.rotation_offset = 0
        self.HUD_angle = 0

        self.is_interactive = True

        ensure_visible_collection(context)

        self.get_placement_matrix(context, debug=False)

        if not self.placement_origin_2d:
            draw_fading_label(context, text="Make sure the Cursor is positioned and visible on the screen!", y=120, color=(1, 0.3, 0), alpha=1, move_y=20, time=2)
            return {'CANCELLED'}

        self.init_use_enter_edit_mode(context)

        self.prepare_for_boolean(context)

        if (event.ctrl and not self.is_drop) or event.alt:

            if self.type == 'ASSET':
                self.obj = self.create_asset_object(context)

                if self.obj:
                    self.verify_boolean_solvers()

                else:
                    draw_fading_label(context, text="Asset could not be added to scene!", y=120, color=red, alpha=1, move_y=40, time=4)

                    return {'CANCELLED'}

            self.prepare_for_subset_mirror(context)

            if event.ctrl:
                self.size = 1
                self.sides = 32
                self.rotation_offset = 0

                self.is_surface = True
                self.is_embed = False

                self.is_quad_sphere = False
                self.is_plane = False
                self.is_subd = False
                self.is_rounded = False

                self.boolean = False
                self.apply_scale = True

            elif event.alt:
                self.init_props(context, redo=True)

            if self.type == 'CUBE':
                self.obj = self.create_cube_object(context)

            elif self.type == 'CYLINDER':
                self.obj = self.create_cylinder_object(context)

            self.get_dimensions()

            self.transform_object(context, interactive=False)

            if self.type == 'ASSET':
                self.compensate_bevels(context, debug=False)

            elif self.type == 'CUBE' and (self.is_quad_sphere or self.is_subd):
                self.setup_quad_sphere_or_subdivided_cube()

                self.apply_mods()

            if self.type == 'CUBE':
                self.finish_cube()

            elif self.type == 'CYLINDER':
                self.finish_cylinder()

            if self.can_scale_be_applied(context):
                self.apply_obj_scale(context)

            if self.boolean and self.boolean_host:

                self.setup_boolean(interactive=False)

                self.verify_boolean_is_in_range()

                self.finish_boolean(context)

                if self.hide_boolean:
                    self.hide_cutter(context)

            self.subset_mirror()

            self.finalize_selection(context)

            if self.type in ['CUBE', 'CYLINDER'] and self.toggled_use_enter_edit_mode and not self.hide_boolean:
                bpy.ops.object.mode_set(mode='EDIT')

            if self.toggled_use_enter_edit_mode:
                context.preferences.edit.use_enter_edit_mode = True

            return {'FINISHED'}

        if self.type == 'CYLINDER':
            self.use_side_presets = True

        self.snap_reset_size = None
        self.is_snapping = False
        self.is_incremental = False

        self.is_numeric_input = False
        self.is_numeric_input_marked = False
        self.numeric_input_size = '0'

        self.is_wireframe_overlay = context.space_data.overlay.show_wireframes
        self.init_wireframe_overlay = self.is_wireframe_overlay

        if self.type == 'ASSET':
            self.obj = self.create_asset_object(context)

            if self.obj:
                self.verify_boolean_solvers()

            else:
                text= ["Make sure to select an OBJECT asset in the asset browser!",
                       "It can be a collection instance asset, but not a collection."]

                draw_fading_label(context, text=text, y=120, color=[red, white], alpha=[1, 0.5], move_y=40, time=4)
                return {'CANCELLED'}

        self.prepare_for_subset_mirror(context)

        self.can_surface_place = False
        self.surface_plane_coords = self.get_surface_plane_coords(init=True)

        get_mouse_pos(self, context, event)

        if not self.is_drop:
            warp_mouse(self, context, self.placement_origin_2d)

        self.init_props(context, redo=False)

        update_mod_keys(self)

        if self.type == 'CYLINDER':

            self.prev_sides, self.next_sides = self.get_prev_and_next_sides(self.sides, debug=False)

        if self.type == 'CUBE':
            self.obj = self.create_cube_object(context)

        elif self.type == 'CYLINDER':
            self.obj = self.create_cylinder_object(context)

        self.is_obj_mesh = self.obj.type == 'MESH'

        self.get_dimensions()

        self.transform_object(context)

        if self.type == 'ASSET':
            self.compensate_bevels(context, debug=False)

        if self.type == 'CUBE' and (self.is_quad_sphere or self.is_subd):
            self.setup_quad_sphere_or_subdivided_cube()

        self.is_scale_appliable = self.can_scale_be_applied(context)

        if self.boolean and self.boolean_host:
            self.setup_boolean(interactive=True)

        hide_gizmos(self, context)

        init_status(self, context, func=draw_add_status(self))

        init_modal_handlers(self, context, hud=True, view3d=True)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        self.is_interactive = False
        self.obj = None

        self.init_use_enter_edit_mode(context)

        self.prepare_for_boolean(context)

        if self.type == 'ASSET':
            asset = context.active_object

            if asset:

                if asset.type == 'EMPTY' and asset.instance_type == 'COLLECTION' and asset.HC.autodisband:

                    self.disband_collection_instance_asset(context, asset)

                    self.obj = context.active_object

                else:
                    self.obj = asset

        else:
            if self.type == 'CUBE':
                self.obj = self.create_cube_object(context)

            elif self.type == 'CYLINDER':
                self.obj = self.create_cylinder_object(context)

        if not self.obj:
            if self.toggled_use_enter_edit_mode:
                context.preferences.edit.use_enter_edit_mode = True
            return {'CANCELLED'}

        self.get_dimensions()

        self.transform_object(context, interactive=False)

        if self.type == 'ASSET':
            self.compensate_bevels(context, debug=False)

        if self.type == 'CUBE' and (self.is_quad_sphere or self.is_subd):
            self.setup_quad_sphere_or_subdivided_cube()

        if self.type == 'CUBE':
            if self.is_quad_sphere or self.is_subd:
                self.apply_mods()

            self.finish_cube()

        elif self.type == 'CYLINDER':
            self.finish_cylinder()

        if self.can_scale_be_applied(context):
            self.apply_obj_scale(context)

        if self.boolean and self.boolean_host:
            self.setup_boolean(interactive=False)

            self.finish_boolean(context, redo=True)

        self.store_props(context)

        if self.hide_boolean:
            self.hide_cutter(context)

        if self.type in ['CUBE', 'CYLINDER']:
            if self.toggled_use_enter_edit_mode:
                bpy.ops.object.mode_set(mode='EDIT')

        elif self.type == 'ASSET':
            self.finalize_selection(context)

        if self.toggled_use_enter_edit_mode:
            context.preferences.edit.use_enter_edit_mode = True

        return {'FINISHED'}

    def get_placement_matrix(self, context, debug=False):
        if self.is_drop:
            if debug:
                print("drop matrix")

            active = context.active_object

            pmx = active.matrix_world.copy()
            loc, rot, _ = pmx.decompose()

            if len(context.selected_objects) == 1 and active.type == 'MESH':
                if debug:
                    print(" single mesh object, offsetting placement origin to bottom")

                centers = get_bbox(active.data)[1]
                loc = pmx @ centers[-2]

        else:
            if debug:
                print("cursor matrix")

            pmx = context.scene.cursor.matrix
            loc, rot, _ = pmx.decompose()

        self.pmx = pmx
        self.placement_origin = loc
        self.placement_up = rot @ Vector((0, 0, 1))
        self.placement_view_plane = None
        self.placement_origin_2d = None

        loc2d = get_location_2d(context, loc, default='OFF_SCREEN')
        if is_on_screen(context, loc2d):
            self.placement_origin_2d = loc2d

    def init_use_enter_edit_mode(self, context):
        self.toggled_use_enter_edit_mode = False

        if self.type in ['CUBE', 'CYLINDER'] and context.preferences.edit.use_enter_edit_mode:
            context.preferences.edit.use_enter_edit_mode = False
            self.toggled_use_enter_edit_mode = True

    def verify_boolean_solvers(self, debug=False):
        debug = False

        version = tuple(int(v) for v in self.asset['version'].split('.'))

        if debug:
            print()
            print(self.obj.name)
            print("inset version:", version)
            print("legacy inset solver:", self.obj.HC.insetsolver)
            print("inset solver prop:", self.obj.HC.inset_solver)

        if bpy.app.version < (4, 5, 0):
            if debug:
                print(" Blender 4.4")

            booleans = [mod for obj in [self.obj] + self.obj.children_recursive for mod in obj.modifiers if mod.type == 'BOOLEAN' and not mod.solver]

            if booleans:
                if debug:
                    print()
                    print("invalid booleans:")

                for mod in booleans:
                    mod.solver = 'FAST'

                    if debug:
                        print(" remapped MANIFOLD boolean to FAST for", mod.name, "on", mod.id_data.name)

            if version == (1, 0):

                if debug:
                    print(" legacy inset")
                    print("  transfer solver from old prop to new prop")

                if self.obj.HC.inset_solver != self.obj.HC.insetsolver:
                    self.obj.HC.inset_solver = self.obj.HC.insetsolver

            elif version == (1, 1):
                if debug:
                    print(" latest inset")

                if not self.obj.HC.inset_solver:
                    if debug:
                        print("  remapping manifold to fast")

                    self.obj.HC.inset_solver = 'FAST'

        else:
            if debug:
                print(" Blender 4.5")

            if version == (1, 0):
                if debug:
                    print(" legacy inset")
                    print("  letting new prop's default MANIFOLD take over")
            elif version == (1, 1):
                if debug:
                    print(" latest inset")
                    print("  using new props solver")

        if debug:
            print()
            print("chosen solver:", self.obj.HC.inset_solver)

    def prepare_for_boolean(self, context):
        self.boolean_host = None
        self.boolean_mod = None
        self.secondary_booleans = []
        self.secondary_split_ignore = []

        self.boolean_host_location = None
        self.can_boolean = False

        if context.visible_objects:
            dg = context.evaluated_depsgraph_get()

            if self.is_drop:
                targets = [obj for obj in context.visible_objects if obj.type == 'MESH' and obj != context.active_object]

            else:
                targets = [obj for obj in context.visible_objects if obj.type == 'MESH']

            self.boolean_host, _, self.boolean_host_location, _, _, _ = get_closest(dg, targets=targets, origin=self.placement_origin, debug=False)

    def verify_boolean_is_in_range(self):
        if self.boolean and self.boolean_host and self.boolean_mod:
            distance = (self.placement_origin - self.boolean_host_location).length

            self.can_boolean = (self.size > 0.00002) and (distance * 1.5 < self.size)

            for mod in [self.boolean_mod] + self.secondary_booleans:
                if self.can_boolean and not mod.show_viewport:

                    if mod == self.boolean_mod:
                        mod.show_viewport = self.boolean_method not in ['SPLIT', 'MESHCUT']

                    else:
                        mod.show_viewport = True

                elif not self.can_boolean and mod.show_viewport:
                    mod.show_viewport = False

            if self.type in ['CUBE', 'CYLINDER']:
                self.obj.display_type = self.boolean_display_type if self.can_boolean else 'TEXTURED'

    def prepare_for_subset_mirror(self, context):
        self.has_subset_mirror = False
        self.is_subset_mirror = False
        self.subset_batches = []

        if self.type == 'ASSET' and self.boolean_host:

            self.mirror_mods = mirror_poll(context, obj=self.boolean_host)

            self.hook_objs = [mod.object for mod in hook_poll(context, obj=self.obj)]

            self.subset_objs = [obj for obj in self.obj.children_recursive if not is_wire_object(obj) and obj not in self.hook_objs]

            self.has_subset_mirror = bool(self.mirror_mods and self.subset_objs)

            if self.has_subset_mirror:
                self.update_subset_batches(context)

    def update_subset_batches(self, context):
        dg = context.evaluated_depsgraph_get()
        self.subset_batches.clear()

        for obj in self.subset_objs:
            coords, indices, _ = get_batch_from_obj(dg, obj)

            for mod in self.mirror_mods:

                mx = mod.mirror_object.matrix_world if mod.mirror_object else self.boolean_host.matrix_world

                origin = mx.decompose()[0]

                for idx, use_axis in enumerate(mod.use_axis):
                    if use_axis:
                        axis = index_axis_mappings[idx]
                        direction = mx.to_3x3() @ axis_vector_mappings[axis]

                        mirrored_coords = mirror_coords(coords, origin, direction)
                        self.subset_batches.append(((mirrored_coords, indices), green))

                        if idx == 0:
                            if  mod.use_axis[1]:
                                y_direction = mx.to_3x3() @ axis_vector_mappings['Y']
                                y_mirrored_coords = mirror_coords(mirrored_coords, origin, y_direction)
                                self.subset_batches.append(((y_mirrored_coords, indices), green))

                                if mod.use_axis[2]:
                                    z_direction = mx.to_3x3() @ axis_vector_mappings['Z']
                                    zy_mirrored_coords = mirror_coords(y_mirrored_coords, origin, z_direction)
                                    self.subset_batches.append(((zy_mirrored_coords, indices), green))

                            if  mod.use_axis[2]:
                                z_direction = mx.to_3x3() @ axis_vector_mappings['Z']
                                z_mirrored_coords = mirror_coords(mirrored_coords, origin, z_direction)
                                self.subset_batches.append(((z_mirrored_coords, indices), green))

                        if idx == 1:
                            if  mod.use_axis[2]:
                                z_direction = mx.to_3x3() @ axis_vector_mappings['Z']
                                z_mirrored_coords = mirror_coords(mirrored_coords, origin, z_direction)
                                self.subset_batches.append(((z_mirrored_coords, indices), green))

    def get_surface_plane_coords(self, init=False):
        if init:
            return []

        origin = self.placement_origin

        pmx = self.pmx.to_3x3()
        x_dir = pmx @ Vector((1, 0, 0))
        y_dir = pmx @ Vector((0, 1, 0))
        z_dir = pmx @ Vector((0, 0, 1))

        size = self.size * 0.7

        coords = [origin - x_dir * size - y_dir * size + z_dir * size * 0.01,
                  origin + x_dir * size - y_dir * size + z_dir * size * 0.01,
                  origin + x_dir * size + y_dir * size + z_dir * size * 0.01,
                  origin - x_dir * size + y_dir * size + z_dir * size * 0.01]

        return coords

    def init_props(self, context, redo=False):
        redoCOL = context.scene.HC.redoaddobjCOL

        name = self.type if self.type in ['CUBE', 'CYLINDER'] else self.asset['assetpath']

        if name in redoCOL:
            self.is_in_history = True

            entry = redoCOL[name]

            self.size = entry.size

            self.align_axis = entry.align_axis

            self.sides = entry.sides

            self.is_surface = entry.surface
            self.is_embed = entry.embed
            self.embed_depth = entry.embed_depth

            self.apply_scale = entry.apply_scale

            self.is_quad_sphere = entry.is_quad_sphere
            self.is_plane = entry.is_plane
            self.is_subd = entry.is_subd
            self.subdivisions = entry.subdivisions

            self.is_rounded = entry.is_rounded
            self.bevel_count = entry.bevel_count
            self.bevel_segments = entry.bevel_segments

            self.boolean = entry.boolean
            self.boolean_method = entry.boolean_method
            self.boolean_solver = entry.boolean_solver
            self.hide_boolean = entry.hide_boolean

            self.boolean_display_type = entry.display_type

            self.is_subset_mirror = entry.is_subset_mirror

        else:
            self.is_in_history = False

            self.align_axis = 'Z'

            self.boolean = False
            self.boolean_method = 'DIFFERENCE'
            self.boolean_solver = 'MANIFOLD' if bpy.app.version >= (4, 5, 0) else 'FAST'
            self.hide_boolean = False

            self.is_quad_sphere = False
            self.is_plane = False
            self.is_subd = False
            self.is_rounded = False
            self.bevel_count = 2 if self.type == 'CUBE' else 1

            if self.obj:
                self.boolean_display_type = 'WIRE' if context.active_object.display_type not in ['WIRE', 'BOUNDS'] else context.active_object.display_type

                if self.obj.HC.isinset:
                    self.is_surface = False
                    self.is_embed = False

                    self.boolean = True
                    self.boolean_method = self.obj.HC.inset_method

                    self.boolean_solver = self.obj.HC.inset_solver if self.obj.HC.inset_solver else 'EXACT'

            self.apply_scale = True if self.type in ['CUBE', 'CYLINDER'] else False

            self.is_subset_mirror = self.has_subset_mirror

        self.boolean_mod = None

        if not redo:
            self.size = 0

            if self.type in ['CUBE', 'CYLINDER']:
                self.boolean = False

    def get_prev_and_next_sides(self, sides, debug=False):
        side_presets = [int(p[0]) for p in add_cylinder_side_items]

        if self.sides in side_presets:
            index = side_presets.index(sides)

            prev_index = max(0, index - 1)
            next_index = min(len(side_presets) - 1, index + 1)

            prev_sides = side_presets[prev_index]
            next_sides = side_presets[next_index]

            if debug:
                print(sides, "is in presets at index", index)
                print("prev:", prev_sides)
                print("next:", next_sides)

        else:
            prev_sides = side_presets[0]
            next_sides = side_presets[-1]

            for p in side_presets:
                if p < sides:
                    prev_sides = p

                elif p > sides:
                    next_sides = p
                    break

            if debug:
                print(sides, "is NOT in pesets")
                print("prev:", prev_sides)
                print("next:", next_sides)

        return prev_sides, next_sides

    def get_placement_view_plane(self, view_dir):
        placement_x = self.pmx.col[0].xyz
        placement_y = self.pmx.col[1].xyz
        placement_z = self.placement_up

        self.placement_view_plane = max([(c, abs(view_dir.dot(c))) for c in [placement_x, placement_y, placement_z]], key=lambda x: x[1])[0]

    def get_dimensions(self):
        if self.type == 'ASSET':

            if self.obj.type == 'MESH':
                _, centers, dimensions = get_bbox(self.obj.data)

            else:
                _, centers, dimensions = get_eval_bbox(self.obj, advanced=True)

            if max(dimensions):
                self.mesh_dimensions = dimensions
                self.mesh_max_dimension_factor = 1 / max(dimensions)
                self.mesh_surface_offsets = [-centers[0].x, -centers[2].y, -centers[4].z]

                self.scaledivisor = max(self.obj.scale)
                self.scale_ratios = Vector([s / self.scaledivisor for s in self.obj.scale])

                return

        self.mesh_dimensions = Vector([2, 2, 2])
        self.mesh_max_dimension_factor = 0.5  # 1 / 2
        self.mesh_surface_offsets = [1, 1, 1]

        self.scale_divisor = 1
        self.scale_ratios = Vector((1, 1, 1))

    def create_asset_object(self, context):
        if self.type == 'ASSET':

            if self.is_drop:
                asset = context.active_object

            else:

                bpy.ops.object.select_all(action='DESELECT')
                context.view_layer.objects.active = None

                area = get_assetbrowser_area(context)

                if area:
                    with context.temp_override(area=area):
                        bpy.ops.machin3.get_object_asset(is_drop=False)

                    asset = context.active_object

                    if asset:
                        loc, rot, _ = self.pmx.decompose()
                        _, _, sca = asset.matrix_world.decompose()

                        asset.matrix_world = Matrix.LocRotScale(loc, rot, sca)

                        bpy.ops.ed.undo_push(message="MACHIN3: Fetch Object Asset")

                    else:
                        return

            self.asset = {'assetpath': asset.HC.assetpath,
                          'libname': asset.HC.libname,
                          'blendpath': asset.HC.blendpath,
                          'assetname': asset.HC.assetname,
                          'version': asset.HC.inset_version}

            if asset.type == 'EMPTY' and asset.instance_type == 'COLLECTION' and asset.HC.autodisband:
                self.disband_collection_instance_asset(context, asset)

            elif asset.type == 'MESH':

                mod = get_auto_smooth(asset)

                if mod and is_invalid_auto_smooth(mod):
                    remove_mod(mod)

            return context.active_object

    def disband_collection_instance_asset(self, context, asset):
        acol = asset.instance_collection
        mcol = context.scene.collection

        children = [obj for obj in acol.objects]

        bpy.ops.object.select_all(action='DESELECT')

        for obj in children:
            mcol.objects.link(obj)
            obj.select_set(True)

            mod = get_auto_smooth(obj)

            if mod and is_invalid_auto_smooth(mod):
                remove_mod(mod)

        if len(acol.users_dupli_group) > 1:
            bpy.ops.object.duplicate()

            for obj in children:
                mcol.objects.unlink(obj)

            children = [obj for obj in context.selected_objects]

            for obj in children:
                if obj.name in acol.objects:
                    acol.objects.unlink(obj)

        root = [obj for obj in children if not obj.parent][0]
        root.matrix_world = asset.matrix_world

        if root.HC.issecondaryboolean:
            self.secondary_booleans = [mod for mod in root.modifiers if mod.type == 'BOOLEAN' and mod.object and mod.show_viewport]

        elif root.HC.ignoresecondarysplit:
            self.secondary_split_ignore = [mod for mod in root.modifiers if mod.type == 'BOOLEAN' and mod.object and mod.show_viewport]

        root.select_set(True)
        context.view_layer.objects.active = root

        bpy.data.objects.remove(asset, do_unlink=True)

        if len(acol.users_dupli_group) == 0:
            bpy.data.collections.remove(acol, do_unlink=True)

    def create_cube_object(self, context):
        if self.obj:
            bpy.data.meshes.remove(self.obj.data, do_unlink=True)

        bpy.ops.mesh.primitive_cube_add(align='CURSOR')

        obj = context.active_object

        if self.is_quad_sphere:
            obj.name = 'Quad Sphere'

        elif self.is_rounded:
            obj.name = 'Rounded Cube'

            if self.bevel_count == 1 or bpy.app.version < (4, 3, 0):
                vertids = [0, 1, 2, 3, 4, 5, 6, 7]

                vgroup = add_vgroup(obj, 'Edge Bevel', ids=vertids, weight=1)

                mod = add_bevel(obj, name="Edge Bevel", width=0.2, limit_method='VGROUP', vertex_group=vgroup.name)
                mod.segments = self.bevel_segments + 1

            elif self.bevel_count == 2:
                bm = bmesh.new()
                bm.from_mesh(obj.data)
                bm.edges.ensure_lookup_table()

                bw_vertical = bm.edges.layers.float.new('Edge Bevel')
                bw_caps = bm.edges.layers.float.new('Edge Bevel.001')

                for e in bm.edges:
                    if e.index in [1, 3, 6, 9]:
                        e[bw_vertical] = 1

                    elif e.index in [0, 2, 4, 5, 7, 8, 10, 11]:
                        e[bw_caps] = 1

                bm.to_mesh(obj.data)

                mod_vectical = add_bevel(obj, name="Edge Bevel", width=0.21, limit_method='WEIGHT', weight_layer='Edge Bevel')
                mod_vectical.segments = self.bevel_segments + 1

                mod_caps = add_bevel(obj, name="Edge Bevel.001", width=0.19, limit_method='WEIGHT', weight_layer='Edge Bevel.001')
                mod_caps.segments = self.bevel_segments + 1

            elif self.bevel_count == 3:
                bm = bmesh.new()
                bm.from_mesh(obj.data)
                bm.edges.ensure_lookup_table()

                bw_vertical = bm.edges.layers.float.new('Edge Bevel')
                bw_top = bm.edges.layers.float.new('Edge Bevel.001')
                bw_bottom = bm.edges.layers.float.new('Edge Bevel.002')

                for e in bm.edges:
                    if e.index in [1, 3, 6, 9]:
                        e[bw_vertical] = 1

                    elif e.index in [2, 5, 8, 11]:
                        e[bw_top] = 1

                    elif e.index in [0, 4, 7, 10]:
                        e[bw_bottom] = 1

                bm.to_mesh(obj.data)

                mod_vectical = add_bevel(obj, name="Edge Bevel", width=0.21, limit_method='WEIGHT', weight_layer='Edge Bevel')
                mod_vectical.segments = self.bevel_segments + 1

                mod_caps = add_bevel(obj, name="Edge Bevel.001", width=0.19, limit_method='WEIGHT', weight_layer='Edge Bevel.001')
                mod_caps.segments = self.bevel_segments + 1

                mod_caps = add_bevel(obj, name="Edge Bevel.002", width=0.19, limit_method='WEIGHT', weight_layer='Edge Bevel.002')
                mod_caps.segments = self.bevel_segments + 1

        elif self.is_plane:
            obj.name = "Plane"

            bm = bmesh.new()
            bm.from_mesh(obj.data)
            bm.normal_update()
            bm.faces.ensure_lookup_table()

            delete = []

            for f in bm.faces:
                if f.index == 5:
                    for v in f.verts:
                        v.co.z = 0
                else:
                    delete.append(f)

            bmesh.ops.delete(bm, geom=delete, context='FACES')

            bm.to_mesh(obj.data)
            bm.free()

        if self.boolean and self.boolean_mod:
            self.boolean_mod.object = obj
            context.active_object.display_type = self.boolean_display_type

        return obj

    def create_cylinder_object(self, context):
        if self.obj:
            bpy.data.meshes.remove(self.obj.data, do_unlink=True)

        bpy.ops.mesh.primitive_cylinder_add(vertices=self.sides, align='CURSOR')

        obj = context.active_object

        is_43_half_cylinder_with_one_bevel = bpy.app.version >= (4, 3, 0) and self.bevel_count == 1 and self.is_half and not self.is_plane

        if self.is_rounded:
            obj.name = 'Rounded Cylinder'

            if self.is_half:

                if self.sides == 18:
                    width = 0.1
                elif self.sides == 9:
                    width = 0.12
                else:
                    width = min(3 / self.sides, 0.2)
            else:
                width = 0.2

            bm = bmesh.new()
            bm.from_mesh(obj.data)
            bm.edges.ensure_lookup_table()
            bm.faces.ensure_lookup_table()

            if is_43_half_cylinder_with_one_bevel:
                c = bm.faces.layers.int.new('CapFaces')

            caps = [bm.faces[2], bm.faces[5]] if self.sides == 4  else [f for f in bm.faces if len(f.verts) != 4]

            if bpy.app.version < (4, 3, 0) or self.bevel_count == 2:
                for f in caps:
                    vertids = [v.index for v in f.verts]
                    vgroup = add_vgroup(obj, 'Edge Bevel', ids=vertids, weight=1)

                    mod = add_bevel(obj, name="Edge Bevel", width=width, limit_method='VGROUP', vertex_group=vgroup.name)
                    mod.segments = self.bevel_segments + 1

            elif self.bevel_count == 1:

                if is_43_half_cylinder_with_one_bevel:
                    for f in caps:
                        f[c] = 1

                bw = bm.edges.layers.float.new('Edge Bevel')
                edges = [e for f in caps for e in f.edges]

                for e in edges:
                    e[bw] = 1

                bm.to_mesh(obj.data)
                bm.free()

                mod = add_bevel(obj, name="Edge Bevel", width=width, limit_method='WEIGHT', weight_layer='Edge Bevel')
                mod.segments = self.bevel_segments + 1

        elif self.is_plane:
            obj.name = 'Circle'

            bm = bmesh.new()
            bm.from_mesh(obj.data)
            bm.normal_update()

            delete = []

            top = Vector((0, 0, 1))

            for f in bm.faces:
                dot = round(top.dot(f.normal))

                if dot == 1:
                    for v in f.verts:
                        v.co.z = 0

                else:
                    delete.append(f)

            bmesh.ops.delete(bm, geom=delete, context='FACES')

            bm.to_mesh(obj.data)
            bm.free()

        if self.is_half:
            bm = bmesh.new()
            bm.from_mesh(obj.data)
            bm.normal_update()
            bm.verts.ensure_lookup_table()

            geom = [el for seq in [bm.verts, bm.edges, bm.faces] for el in seq]

            bmesh.ops.bisect_plane(bm, geom=geom, dist=0, plane_co=Vector((0, 0, 0)), plane_no=Vector((0, -1, 0)), use_snap_center=False, clear_outer=True, clear_inner=False)

            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.00001)

            if not self.is_plane:
                bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if not e.is_manifold], sides=0)

            if is_43_half_cylinder_with_one_bevel:
                c = bm.faces.layers.int.get('CapFaces')
                bw = bm.edges.layers.float.get('Edge Bevel')

                if c and bw:
                    cap_faces = [f for f in bm.faces if f[c]]

                    for f in cap_faces:
                        for e in f.edges:
                            e[bw] = 1

            bm.to_mesh(obj.data)
            bm.free()

        if self.boolean_mod:
            self.boolean_mod.object = obj

        return obj

    def compensate_bevels(self, context, debug=False):
        if debug:
            print()
            print("mesh users:", self.obj.data.users)

        bevel_mods = bevel_poll(context, self.obj)

        if bevel_mods and self.obj.data.users > 1:
            if debug:
                print("fetching original mesh max dimensions factor")

            redoCOL = context.scene.HC.redoaddobjCOL
            entry = redoCOL.get(self.asset['assetpath'])

            if entry and entry.original_mesh_max_dimension_factor:
                if debug:
                    print(" original:", entry.original_mesh_max_dimension_factor)

                    print("  current:", self.mesh_max_dimension_factor)

                if entry.original_mesh_max_dimension_factor != str(self.mesh_max_dimension_factor):
                    if debug:
                        print(" it differs, so the current bevels need to be adjusted!")

                    compensate = float(self.mesh_max_dimension_factor) / float(entry.original_mesh_max_dimension_factor)

                    for mod in bevel_mods:
                        mod.width /= compensate

    def setup_quad_sphere_or_subdivided_cube(self):
        subd = add_subdivision(self.obj, name="Subdivision")
        subd.levels = self.subdivisions
        subd.render_levels = self.subdivisions

        if self.is_quad_sphere:
            add_cast(self.obj, name="Cast")

        else:
            subd.subdivision_type = 'SIMPLE'

    def setup_boolean(self, interactive=True):
        method = 'DIFFERENCE' if self.boolean_method in ['SPLIT', 'MESHCUT'] else self.boolean_method
        self.boolean_mod = add_boolean(self.boolean_host, self.obj, method=method, solver=self.boolean_solver)
        self.boolean_mod.show_viewport = self.can_boolean

        if self.boolean_display_type not in ['WIRE', 'BOUNDS']:
            self.boolean_display_type = 'WIRE'

        self.obj.display_type = self.boolean_display_type

        if interactive:
            if self.boolean_method in ['SPLIT', 'MESHCUT']:
                self.boolean_mod.show_viewport = False

                self.boolean_host.select_set(True)

            else:
                self.boolean_host.select_set(False)

        if self.type == 'ASSET' and self.secondary_booleans:
            new_mods = []

            for mod in self.secondary_booleans:

                new_mod = add_boolean(self.boolean_host, mod.object, method=mod.operation, solver=mod.solver if mod.solver else 'FAST')
                new_mod.show_viewport = self.can_boolean
                new_mod.object.display_type = self.boolean_display_type
                new_mods.append(new_mod)

                remove_mod(mod)

            self.secondary_booleans = new_mods

    def update_boolean(self):

        if self.boolean:

            if self.boolean_method in ['SPLIT', 'MESHCUT']:

                if self.boolean_mod.operation != 'DIFFERENCE':
                    self.boolean_mod.operation = 'DIFFERENCE'

                self.boolean_mod.show_viewport = False

                self.obj.display_type = 'WIRE'

                if self.boolean_host and not self.boolean_host.select_get():
                    self.boolean_host.select_set(True)

            else:

                self.boolean_mod.operation  = self.boolean_method

                self.boolean_mod.show_viewport = self.can_boolean

                self.obj.display_type = self.boolean_display_type

                for mod in self.secondary_booleans:
                    mod.object.display_type = self.boolean_display_type

                if self.boolean_host and self.boolean_host.select_get():
                    self.boolean_host.select_set(False)

            self.boolean_mod.solver = self.boolean_solver

            self.boolean_mod.name = self.boolean_method.title()

        else:

            if self.boolean_mod and self.boolean_mod.show_viewport:
                self.boolean_mod.show_viewport = False

            if self.obj.display_type != 'TEXTURED':
                self.obj.display_type = 'TEXTURED'

            if self.boolean_host and self.boolean_host.select_get():
                self.boolean_host.select_set(False)

    def transform_object(self, context, interactive=True):
        self.set_obj_size(context, interactive=interactive)

        self.set_obj_location(context)

        if self.type in ['CYLINDER', 'ASSET'] or (self.type == 'CUBE' and self.is_plane):
            self.set_obj_axis_align(context)

        self.verify_boolean_is_in_range()

        if self.has_subset_mirror and self.is_subset_mirror:
            self.update_subset_batches(context)

        self.surface_plane_coords = self.get_surface_plane_coords()

        self.can_surface_place = self.obj.type != 'EMPTY' and not (self.type in ['CUBE', 'CYLINDER'] and (self.is_plane and self.align_axis == 'Z'))

    def set_obj_size(self, context, interactive=False):
        if interactive:
            view_origin, view_dir = get_view_origin_and_dir(context, self.mouse_pos)

            if not self.placement_view_plane:
                self.get_placement_view_plane(view_dir)

            i = intersect_line_plane(view_origin, view_origin + view_dir, self.placement_origin, self.placement_view_plane)

            if i:
                self.size = (self.placement_origin - i).length

                if self.is_snapping:
                    self.size = dynamic_snap(self.size, offset=1 if self.is_incremental else 0)

        self.obj.scale = Vector((self.size, self.size, self.size)) * self.mesh_max_dimension_factor * self.scale_ratios

    def set_obj_location(self, context):
        if self.type in ['CYLINDER', 'ASSET']:
            if self.align_axis == 'X':
                surface_offset = self.mesh_surface_offsets[1]
                mesh_dimension = self.mesh_dimensions[1]
                scale_ratio = self.scale_ratios[1]
            elif self.align_axis == 'Y':
                surface_offset = self.mesh_surface_offsets[0]
                mesh_dimension = self.mesh_dimensions[0]
                scale_ratio = self.scale_ratios[0]
            elif self.align_axis == 'Z':
                surface_offset = self.mesh_surface_offsets[2]
                mesh_dimension = self.mesh_dimensions[2]
                scale_ratio = self.scale_ratios[2]

        else:
            surface_offset = self.mesh_surface_offsets[2]
            mesh_dimension = self.mesh_dimensions[2]
            scale_ratio = 1

        mesh_size = self.size * self.mesh_max_dimension_factor

        if self.is_surface and self.obj.type != 'EMPTY':
            context.active_object.location = self.placement_origin + self.placement_up * mesh_size * surface_offset * scale_ratio

        elif self.is_embed and self.obj.type != 'EMPTY':
            context.active_object.location = self.placement_origin + self.placement_up * mesh_size * (surface_offset - mesh_dimension * self.embed_depth) * scale_ratio

        else:
            context.active_object.location = self.placement_origin

    def set_obj_axis_align(self, context):
        loc, _, sca = context.active_object.matrix_basis.decompose()

        rot_offset = Quaternion(Vector((0, 0, 1)), radians(self.rotation_offset)).to_matrix()

        self.HUD_angle = 360 - self.rotation_offset

        if self.HUD_angle == 360:
            self.HUD_angle = 0

        protmx = self.pmx.to_3x3() @ rot_offset

        if self.align_axis == 'X':
            rotmx = protmx.copy()

            rotmx.col[2] = protmx.col[0]
            rotmx.col[1] = protmx.col[2]
            rotmx.col[0] = protmx.col[1]

        elif self.align_axis == 'Y':
            rotmx = protmx.copy()

            rotmx.col[2] = protmx.col[1]
            rotmx.col[1] = protmx.col[0]
            rotmx.col[0] = protmx.col[2]

            z_rot = Quaternion(Vector((0, 0, 1)), radians(-90)).to_matrix()
            rotmx = rotmx @ z_rot

        else:
            rotmx = protmx

        context.active_object.matrix_basis = Matrix.LocRotScale(loc, rotmx, sca)

    def numeric_input(self, context, event):

        if event.type == "TAB" and event.value == 'PRESS':
            self.is_numeric_input = not self.is_numeric_input

            force_ui_update(context)

            if self.is_numeric_input:
                self.numeric_input_size = str(self.size)
                self.is_numeric_input_marked = True

            else:
                return

        if self.is_numeric_input:

            if event.type in alt:
                update_mod_keys(self, event)
                force_ui_update(context)
                return {'RUNNING_MODAL'}

            events = numeric_input_event_items(minus=False)

            if event.type in events and event.value == 'PRESS':

                if self.is_numeric_input_marked:
                    self.is_numeric_input_marked = False

                    if event.type == 'BACK_SPACE':

                        if self.is_alt:
                            self.numeric_input_size = self.numeric_input_size[:-1]

                        else:
                            self.numeric_input_size = shorten_float_string(self.numeric_input_size, 4)

                    else:
                        self.numeric_input_size = input_mappings[event.type]

                else:
                    if event.type in numbers:
                        self.numeric_input_size += input_mappings[event.type]

                    elif event.type == 'BACK_SPACE':
                        self.numeric_input_size = self.numeric_input_size[:-1]

                    elif event.type in ['COMMA', 'PERIOD', 'NUMPAD_COMMA', 'NUMPAD_PERIOD'] and '.' not in self.numeric_input_size:
                        self.numeric_input_size += '.'

                try:
                    self.size = float(self.numeric_input_size)

                except:
                    return {'RUNNING_MODAL'}

                self.transform_object(context, interactive=False)

            elif navigation_passthrough(event, alt=True, wheel=True):
                return {'PASS_THROUGH'}

            elif event.type in {'RET', 'NUMPAD_ENTER', 'SPACE'}:
                self.finish(context)

                self.hide_boolean = self.obj.type == 'MESH' and self.boolean and event.type == 'SPACE'

                if self.type == 'CUBE':
                    if self.is_quad_sphere or self.is_subd:
                        self.apply_mods()

                    self.finish_cube()

                elif self.type == 'CYLINDER':
                    self.finish_cylinder()

                if self.can_scale_be_applied:
                    self.apply_obj_scale(context)

                self.store_cursor()

                self.finish_boolean(context)

                self.store_props(context)

                if self.hide_boolean:
                    self.hide_cutter(context)

                self.subset_mirror()

                self.finalize_selection(context)

                if self.type in ['CUBE', 'CYLINDER'] and self.toggled_use_enter_edit_mode and not self.hide_boolean:
                    bpy.ops.object.mode_set(mode='EDIT')

                return {'FINISHED'}

            elif event.type in {'ESC', 'RIGHTMOUSE'}:
                self.finish(context)

                for obj in context.selected_objects:
                    if obj.type == 'MESH' and obj.data.users == 1:
                        bpy.data.meshes.remove(obj.data, do_unlink=True)
                    else:
                        bpy.data.objects.remove(obj, do_unlink=True)

                if self.boolean_mod:
                    self.boolean_host.modifiers.remove(self.boolean_mod)

                for mod in self.secondary_booleans:
                    self.boolean_host.modifiers.remove(mod)

                return {'CANCELLED'}

            return {'RUNNING_MODAL'}

    def interactive_input(self, context, event):
        if event.type == 'MOUSEMOVE':
            get_mouse_pos(self, context, event)

        self.is_snapping = self.is_ctrl
        self.is_incremental = self.is_alt

        if self.is_snapping and not self.snap_reset_size:
            self.snap_reset_size = self.size

            self.transform_object(context)

        elif not self.is_snapping and self.snap_reset_size is not None:
            self.size = self.snap_reset_size
            self.snap_reset_size = None

            self.transform_object(context)

        events = ['MOUSEMOVE', 'W']
        finish_events = ['LEFTMOUSE', 'SPACE', 'L', 'MIDDLEMOUSE'] if self.is_in_history else ['LEFTMOUSE', 'SPACE']

        if not (self.type in ['CUBE', 'CYLINDER'] and self.is_plane):
            events.append('R')

            if self.boolean_host:
                events.append('B')

            if self.type == 'CUBE':
                events.append('Q')

        if self.can_surface_place:
            events.extend(['S', 'D'])

        if self.is_scale_appliable:
            events.append('A')

        if self.type in ['CYLINDER', 'ASSET'] or (self.type == 'CUBE' and self.is_plane):
            events.extend(['X', 'Y', 'Z'])

        if self.boolean and self.boolean_method != 'MESHCUT':
            events.append('E')

        if self.type == 'CUBE':
            events.append('C')

            if self.is_rounded and bpy.app.version >= (4, 3, 0):
                events.extend(['ONE', 'TWO', 'THREE'])

            else:
                events.extend(['ONE', 'TWO', 'THREE', 'FOUR', 'FIVE'])

        elif self.type == 'CYLINDER':
            events.extend(['C', 'V', 'H'])

            if self.is_rounded and bpy.app.version >= (4, 3, 0):
                events.extend(['ONE', 'TWO'])

            if not self.boolean:
                events.append('Q')

        elif self.type == 'ASSET' and self.has_subset_mirror:
            events.append('M')

        if event.type in events or scroll(event, key=False):

            if self.type == 'CYLINDER':

                if event.type in ['X', 'Y', 'Z'] or scroll(event, key=False):

                    if scroll(event, key=True):

                        if not self.is_shift and not self.is_alt and not self.boolean:

                            if self.use_side_presets:
                                if scroll_up(event, key=True):
                                    self.sides = self.next_sides
                                else:
                                    self.sides = self.prev_sides

                                self.prev_sides, self.next_sides = self.get_prev_and_next_sides(self.sides)

                            else:
                                if scroll_up(event, key=True):
                                    self.sides += 1
                                else:
                                    self.sides -= 1

                            self.obj = self.create_cylinder_object(context)

                            self.update_boolean()

                        elif self.is_alt and self.is_rounded:
                            if scroll_up(event, key=True):
                                self.bevel_segments += 1

                            elif scroll_down(event, key=True):
                                self.bevel_segments -= 1

                            bevel_mods = bevel_poll(context, self.obj)

                            for mod in bevel_mods:
                                mod.segments = self.bevel_segments + 1

                    if event.type == 'X' and event.value == 'PRESS':
                        self.align_axis = 'Z' if self.align_axis == 'X' else 'X'

                    elif event.type in ['Y', 'Z'] and event.value == 'PRESS':
                        self.align_axis = 'Z' if self.align_axis == 'Y' else 'Y'

                    if self.align_axis == 'Z' and self.is_plane:
                        if self.is_surface:
                            self.is_surface = False

                        if self.is_embed:
                            self.is_embed = False

                    self.transform_object(context)

                elif event.type == 'Q' and event.value == 'PRESS':
                    self.use_side_presets = not self.use_side_presets

                    if self.use_side_presets:
                        self.prev_sides, self.next_sides = self.get_prev_and_next_sides(self.sides)

                    force_ui_update(context)

                elif event.type == 'C' and event.value == 'PRESS':
                    if self.is_plane:
                        self.is_plane = False

                    else:
                        self.is_rounded = False

                        if self.align_axis == 'Z':
                            self.is_embed = False
                            self.is_surface = False

                        if self.boolean:
                            self.boolean = False
                            remove_mod(self.boolean_mod)
                            self.boolean_mod = None

                        self.is_plane = True

                    self.obj = self.create_cylinder_object(context)

                    self.update_boolean()

                    self.transform_object(context)

                elif event.type in ['V', 'H'] and event.value == 'PRESS':
                    if self.is_half:
                        self.is_half = False

                    else:
                        self.is_half = True

                    self.obj = self.create_cylinder_object(context)

                    self.update_boolean()

                    self.transform_object(context)

                elif event.type == 'R' and event.value == 'PRESS':
                    self.is_rounded = not self.is_rounded

                    self.obj = self.create_cylinder_object(context)

                    self.update_boolean()

                    self.transform_object(context)

                elif event.type in ['ONE', 'TWO'] and event.value == 'PRESS' and self.is_rounded:
                    self.bevel_count = number_mappings[event.type]

                    self.obj = self.create_cylinder_object(context)

                    self.update_boolean()

                    self.transform_object(context)

            elif self.type == 'CUBE':
                subd = get_subdivision(self.obj)
                cast = get_cast(self.obj)

                if event.type == 'Q' and event.value == 'PRESS':

                    if subd and cast:
                        self.obj.modifiers.remove(subd)
                        self.obj.modifiers.remove(cast)

                        self.is_subd = False
                        self.is_quad_sphere = False
                        self.obj.show_wire = False

                        self.obj.name = 'Cube'

                    else:
                        self.is_rounded = False

                        self.is_subd = True
                        self.is_quad_sphere = True

                        self.obj = self.create_cube_object(context)
                        self.obj.show_wire = True

                        subd = add_subdivision(self.obj, name="Subdivision")
                        subd.levels = self.subdivisions
                        subd.render_levels = self.subdivisions

                        cast = add_cast(self.obj, name="Cast")

                        self.update_boolean()

                        self.transform_object(context)

                elif event.type == 'C' and event.value == 'PRESS':
                    if self.is_plane:
                        self.is_plane = False

                        if self.align_axis in ['X', 'Y']:
                            self.align_axis = 'Z'

                    else:

                        if self.is_quad_sphere:
                            self.is_quad_sphere = False
                            self.is_subd = False

                        self.is_rounded = False

                        self.is_embed = False
                        self.is_surface = False

                        if self.boolean:
                            self.boolean = False
                            remove_mod(self.boolean_mod)
                            self.boolean_mod = None

                        self.is_plane = True

                    self.obj = self.create_cube_object(context)

                    if self.is_subd:
                        subd = add_subdivision(self.obj, name="Subdivision")
                        subd.subdivision_type = 'SIMPLE'
                        subd.show_only_control_edges = False
                        subd.levels = self.subdivisions

                        self.obj.show_wire = True

                    self.update_boolean()

                    self.transform_object(context)

                elif event.type in ['ONE', 'TWO', 'THREE', 'FOUR', 'FIVE'] and event.value == 'PRESS' and not self.is_rounded:
                    self.subdivisions = number_mappings[event.type]

                    if subd:
                        levels = subd.levels

                        if levels != self.subdivisions:
                            subd.levels = self.subdivisions

                        elif not self.is_quad_sphere and levels == self.subdivisions:

                            self.obj.modifiers.remove(subd)

                            self.is_subd = False
                            self.obj.show_wire = False

                    else:
                        subd = add_subdivision(self.obj, name="Subdivision")
                        subd.subdivision_type = 'SIMPLE'
                        subd.show_only_control_edges = False

                        subd.levels = self.subdivisions

                        self.is_subd = True
                        self.obj.show_wire = True

                elif scroll(event, key=False):

                    if self.is_alt and self.is_subd:
                        if scroll_up(event, key=False):
                            self.subdivisions += 1

                        elif scroll_down(event, key=False):
                            self.subdivisions -= 1

                        subd.levels = self.subdivisions

                    elif self.is_alt and self.is_rounded:
                        if scroll_up(event, key=False):
                            self.bevel_segments += 1

                        elif scroll_down(event, key=False):
                            self.bevel_segments -= 1

                        bevel_mods = bevel_poll(context, self.obj)

                        for mod in bevel_mods:
                            mod.segments = self.bevel_segments + 1

                elif event.type in ['X', 'Y', 'Z'] and event.value == 'PRESS':
                    if event.type == 'X' and event.value == 'PRESS':
                        self.align_axis = 'Z' if self.align_axis == 'X' else 'X'

                    elif event.type in ['Y', 'Z'] and event.value == 'PRESS':
                        self.align_axis = 'Z' if self.align_axis == 'Y' else 'Y'

                    if self.align_axis == 'Z' and self.is_plane:
                        if self.is_surface:
                            self.is_surface = False

                        if self.is_embed:
                            self.is_embed = False

                    self.transform_object(context)

                elif event.type == 'R' and event.value == 'PRESS':

                    if self.is_rounded:
                        self.is_rounded = False
                        self.obj = self.create_cube_object(context)

                    else:
                        if subd or cast:
                            self.obj.show_wire = False

                            if subd:
                                self.obj.modifiers.remove(subd)

                                self.is_subd = False

                            if cast:
                                self.obj.modifiers.remove(cast)

                                self.is_quad_sphere = False

                        self.is_rounded = True

                        self.obj = self.create_cube_object(context)

                    self.update_boolean()

                    self.transform_object(context)

                elif event.type in ['ONE', 'TWO', 'THREE'] and event.value == 'PRESS' and self.is_rounded:
                    self.bevel_count = number_mappings[event.type]

                    self.obj = self.create_cube_object(context)

                    self.update_boolean()

                    self.transform_object(context)

            elif self.type == 'ASSET':

                if event.type in ['X', 'Y', 'Z', 'R'] and event.value == 'PRESS':
                    if event.type == 'X':
                        self.align_axis = 'Z' if self.align_axis == 'X' else 'X'

                    elif event.type in ['Y', 'Z']:
                        self.align_axis = 'Z' if self.align_axis == 'Y' else 'Y'

                    elif event.type == 'R':
                        if self.is_shift:
                            self.rotation_offset += 45
                        else:
                            self.rotation_offset -= 45

                        if self.rotation_offset >= 360:
                            self.rotation_offset = 0
                        elif self.rotation_offset < 0:
                            self.rotation_offset = 315

                    self.transform_object(context)

                elif event.type == 'M' and event.value == 'PRESS':
                    self.is_subset_mirror = not self.is_subset_mirror

                    force_ui_update(context)

            if event.type == 'MOUSEMOVE':
                self.transform_object(context)

            elif event.type == 'S' and event.value == 'PRESS' and self.obj.type != 'EMPTY':
                self.is_surface = not self.is_surface

                if self.is_surface and self.is_embed:
                    self.is_embed = False

                self.transform_object(context)

            elif event.type == 'D' and event.value == 'PRESS' and self.obj.type != 'EMPTY':
                self.is_embed = not self.is_embed

                if self.is_embed and self.is_surface:
                    self.is_surface = False

                self.transform_object(context)

            elif event.type == 'A' and event.value == 'PRESS' and self.obj.type != 'EMPTY':
                self.apply_scale = not self.apply_scale
                context.active_object.select_set(True)

            elif event.type == 'W' and not self.is_shift and event.value == 'PRESS':
                self.is_wireframe_overlay = not self.is_wireframe_overlay

                context.space_data.overlay.show_wireframes = self.is_wireframe_overlay

                force_ui_update(context)

            elif event.type == 'B' and event.value == 'PRESS' and self.obj.type == 'MESH':
                self.boolean = not self.boolean

                if self.boolean and not self.boolean_mod:
                    self.setup_boolean(interactive=True)

                self.verify_boolean_is_in_range()

                self.update_boolean()

            if self.is_embed:
                if not self.is_alt and self.is_shift and scroll(event, key=False):
                    if scroll_up(event, key=False):
                        self.embed_depth += 0.1

                    elif scroll_down(event, key=False):
                        self.embed_depth -= 0.1

                    self.transform_object(context)

            if self.boolean:

                if not self.is_shift and not self.is_alt and scroll(event, key=False):

                    if scroll_up(event, key=True):
                        self.boolean_method = step_enum(self.boolean_method, add_boolean_method_items, -1, loop=True)

                    elif scroll_down(event, key=True):
                        self.boolean_method = step_enum(self.boolean_method, add_boolean_method_items, 1, loop=True)

                    self.update_boolean()

                elif event.type == 'E' and event.value == 'PRESS':

                    if bpy.app.version >= (4, 5, 0):
                        solvers = ['MANIFOLD', 'FAST', 'EXACT']
                    else:
                        solvers = ['FAST', 'EXACT']

                    self.boolean_solver = step_list(self.boolean_solver, solvers, step=1)

                    self.update_boolean()

                elif event.type == 'W' and self.is_shift and event.value == 'PRESS':

                    if self.boolean_method not in ['SPLIT', 'MESHCUT']:
                        self.boolean_display_type = step_enum(self.boolean_display_type, boolean_display_type_items, 1)

                        self.obj.display_type = self.boolean_display_type

                        for mod in self.secondary_booleans:
                            mod.object.display_type = self.boolean_display_type

        if event.type in finish_events:
            self.finish(context)

            if event.type in ['L', 'MIDDLEMOUSE']:
                redoCOL = context.scene.HC.redoaddobjCOL

                name = self.type if self.type in ['CUBE', 'CYLINDER'] else self.asset['assetpath']
                entry = redoCOL[name]
                self.size = entry.size

                self.set_obj_size(context, interactive=False)

                if self.type == 'ASSET':
                    self.verify_boolean_is_in_range()

                self.hide_boolean = entry.hide_boolean

            else:
                self.hide_boolean = self.obj.type == 'MESH' and self.boolean and event.type == 'SPACE'

            if self.type == 'CUBE':
                if self.is_quad_sphere or self.is_subd:
                    self.apply_mods()

                self.finish_cube()

            elif self.type == 'CYLINDER':
                self.finish_cylinder()

            if self.can_scale_be_applied:
                self.apply_obj_scale(context)

            self.store_cursor()

            self.finish_boolean(context)

            self.store_props(context)

            if self.hide_boolean:
                self.hide_cutter(context)

            self.subset_mirror()

            self.finalize_selection(context)

            if self.type in ['CUBE', 'CYLINDER'] and self.toggled_use_enter_edit_mode and not self.hide_boolean:
                bpy.ops.object.mode_set(mode='EDIT')

            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            self.finish(context)

            for obj in context.selected_objects:
                if obj.type == 'MESH' and obj.data.users == 1:
                    bpy.data.meshes.remove(obj.data, do_unlink=True)
                else:
                    bpy.data.objects.remove(obj, do_unlink=True)

            if self.boolean_mod:
                self.boolean_host.modifiers.remove(self.boolean_mod)

            for mod in self.secondary_booleans:
                self.boolean_host.modifiers.remove(mod)

            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def finish_cube(self):
        bm = bmesh.new()
        bm.from_mesh(self.obj.data)
        bm.normal_update()

        edge_glayer, face_glayer = ensure_gizmo_layers(bm)

        if not (self.is_quad_sphere or self.is_subd):

            for e in bm.edges:
                e[edge_glayer] = 1

            for f in bm.faces:
                f[face_glayer] = 1

        bm.to_mesh(self.obj.data)
        bm.free()

        self.obj.HC.ishyper = True
        self.obj.HC.objtype = 'CUBE'

    def finish_cylinder(self):
        bm = bmesh.new()
        bm.from_mesh(self.obj.data)
        bm.normal_update()

        edge_glayer, face_glayer = ensure_gizmo_layers(bm)

        if self.is_plane:
            caps = bm.faces
            ring_edges = bm.edges

        else:
            caps = [f for f in bm.faces if len(f.verts) != 4]

            ring_edges = [e for f in caps for e in f.edges]
            vertical_edges = [e for e in bm.edges if e not in ring_edges]

        for e in ring_edges:
            e[edge_glayer] = 1

        if not self.is_plane:
            vertical_edges[0][edge_glayer] = 1

        for f in caps:
            f[face_glayer] = 1

        bm.to_mesh(self.obj.data)
        bm.free()

        self.obj.HC.ishyper = True
        self.obj.HC.objtype = 'CYLINDER'

        self.obj.HC.avoid_update = True
        self.obj.HC.objtype_without_none = 'CYLINDER'

    def apply_mods(self):
        subd = get_subdivision(self.obj)

        if subd:
            apply_mod(subd)
            self.obj.show_wire = False

        cast = get_cast(self.obj)

        if cast:
            apply_mod(cast)

    def can_scale_be_applied(self, context):
        if self.obj.type == 'MESH':

            if self.obj.children:
                return False

            if bevel_poll(context, self.obj) and not is_uniform_scale(self.obj):
                return False

            return True
        return False

    def apply_obj_scale(self, context, debug=False):
        if self.apply_scale and self.obj.type == 'MESH' and not self.obj.children:

            if debug:
                print("applying scale")

            bevel_mods = bevel_poll(context, self.obj)

            if debug and bevel_mods:
                print("found bevel mods")

            if bevel_mods:
                if not is_uniform_scale(self.obj):
                    if debug:
                        print("object has bevel mods but isn't scalled uniformly, not aplying scale")
                    return

                bevel_compensator = 1 / (self.size * self.mesh_max_dimension_factor)

                if debug:
                    print("bevel compensator:", bevel_compensator)

                if bevel_compensator >= 1:
                    if debug:
                        print(" compensating bevels before applying scale")

                    for mod in bevel_mods:
                        mod.width /= 1 / (self.size * self.mesh_max_dimension_factor)

                    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True, isolate_users=True)

                else:
                    if debug:
                        print(" compensating bevels after applying scale")

                    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True, isolate_users=True)

                    for mod in bevel_mods:
                        mod.width /= 1 / (self.size * self.mesh_max_dimension_factor)
            else:
                bpy.ops.object.transform_apply(location=False, rotation=False, scale=True, isolate_users=True)

            if debug:
                print("scale is applied")

    def finish_boolean(self, context, redo=False):
        if self.boolean and self.boolean_host and (self.can_boolean or redo):

            if self.boolean_method == 'MESHCUT':

                remove_mod(self.boolean_mod)

                remove_operands = set()

                if self.obj.children and not self.is_interactive:
                    dg = context.evaluated_depsgraph_get()

                for obj in self.obj.children:

                    if not self.secondary_booleans:

                        if self.obj in remote_boolean_poll(context, obj):
                            remove_operands.update([obj] + obj.children_recursive)
                            continue

                    parent(obj, self.boolean_host)

                meshcut(context, self.boolean_host, [self.obj])

                for mod in self.secondary_booleans:
                    hide_render(mod.object, True)
                    mod.show_viewport = True

                if remove_operands:
                    bpy.data.batch_remove(remove_operands)

            else:
                parent(self.obj, self.boolean_host)

                sort_modifiers(self.boolean_host, debug=False)

                for mod in [self.boolean_mod] + self.secondary_booleans:
                    hide_render(mod.object, True)
                    mod.show_viewport = True

                if self.boolean_method == 'SPLIT':

                    self.split = setup_split_boolean(context, self.boolean_mod)

                    if self.secondary_split_ignore:
                        for mod in self.secondary_split_ignore:
                            remove_obj(mod.object)
                            remove_mod(mod)

                    bpy.ops.object.select_all(action='DESELECT')

                    cutter_dup = self.split['dup']['cutter']
                    cutter_dup.select_set(True)
                    context.view_layer.objects.active = cutter_dup

        elif self.boolean_mod:
            for mod in [self.boolean_mod] + self.secondary_booleans:
                remove_mod(mod)

    def hide_cutter(self, context):
        if self.boolean:

            booleans = self.secondary_booleans if self.boolean_method == 'MESHCUT' else [self.boolean_mod] + self.secondary_booleans

            mod_objs = [mod.object for mod in booleans]

            cutters = set(mod_objs) | {child for obj in mod_objs for child in obj.children_recursive if is_wire_object(child)}

            for obj in cutters:
                obj.hide_set(True)

            if self.boolean_method == 'SPLIT':

                split_mod_objs = [self.split['map'][obj] for obj in mod_objs if obj in self.split['map']]

                cutters = set(split_mod_objs) | {child for obj in split_mod_objs for child in obj.children_recursive if is_wire_object(child)}

                for obj in cutters:
                    obj.hide_set(True)

    def finalize_selection(self, context):

        if self.type == 'ASSET' and self.boolean_host and self.boolean and self.hook_objs:
            handle = self.hook_objs[0]

            bpy.ops.object.select_all(action='DESELECT')

            if not handle.visible_get():
                handle.hide_set(False)

            handle.select_set(True)
            context.view_layer.objects.active = handle

        elif self.boolean_host and self.hide_boolean:
            bpy.ops.object.select_all(action='DESELECT')

            host = self.split['dup']['host'] if self.boolean_method == 'SPLIT' else self.boolean_host
            host.select_set(True)
            context.view_layer.objects.active = host

    def subset_mirror(self):
        if self.has_subset_mirror and self.is_subset_mirror:
            for mod in self.mirror_mods:
                for obj in self.subset_objs:
                    mirror = add_mirror(obj)

                    mirror.use_axis = mod.use_axis
                    mirror.show_expanded = mod.show_expanded

                    mirror.mirror_object = mod.mirror_object if mod.mirror_object else self.boolean_host

    def store_props(self, context):
        redoCOL = context.scene.HC.redoaddobjCOL

        name = self.type if self.type in ['CUBE', 'CYLINDER'] else self.asset['assetpath']

        if name in redoCOL:
            entry = redoCOL[name]

        else:
            entry = redoCOL.add()
            entry.name = name

            if self.type == 'ASSET':
                entry.original_mesh_max_dimension_factor = str(self.mesh_max_dimension_factor)

            if self.asset:
                entry.libname = self.asset['libname']
                entry.blendpath = self.asset['blendpath']
                entry.assetname = self.asset['assetname']

        entry.surface = self.is_surface

        entry.embed = self.is_embed
        entry.embed_depth = self.embed_depth

        entry.apply_scale = self.apply_scale

        entry.size = self.size

        entry.sides = self.sides

        entry.is_quad_sphere = self.is_quad_sphere
        entry.is_plane = self.is_plane
        entry.is_subd = self.is_subd
        entry.subdivisions = self.subdivisions

        entry.is_rounded = self.is_rounded
        entry.bevel_count = self.bevel_count
        entry.bevel_segments = self.bevel_segments

        entry.align_axis = self.align_axis

        entry.boolean = self.boolean
        entry.boolean_method = self.boolean_method

        if self.boolean and self.boolean_method != 'MESHCUT':
            entry.boolean_solver = self.boolean_solver

            entry.hide_boolean = self.hide_boolean

            entry.display_type = self.obj.display_type

        if self.has_subset_mirror:
            entry.is_subset_mirror = self.is_subset_mirror

        index = list(redoCOL).index(entry)

        context.scene.HC.redoaddobjIDX = index

        entry.selectable = True

    def store_cursor(self):
        if getattr(get_prefs(), f"add_{self.type.lower()}_store_cursor"):
            name = self.obj.name if self.type in ['CUBE', 'CYLINDER'] else (self.asset['assetname'])

            add_history_entry(mx=self.obj.matrix_world, name=f"Add {name}")

class PipeGizmoManager:
    gizmo_props = {}
    gizmo_data = {}

    def gizmo_poll(self, context):
        if context.mode == 'OBJECT':
            props = self.gizmo_props
            return props.get('area_pointer') == str(context.area.as_pointer()) and props.get('show')

    def gizmo_group_init(self, context):
        self.gizmo_props.clear()
        self.gizmo_data.clear()

        self.gizmo_props['show'] = True
        self.gizmo_props['area_pointer'] = str(context.area.as_pointer())

        self.gizmo_data['points'] = []

        context.window_manager.gizmo_group_type_ensure('MACHIN3_GGT_pipe')

    def gizmo_group_finish(self, context):
        self.gizmo_props.clear()
        self.gizmo_data.clear()

        context.window_manager.gizmo_group_type_unlink_delayed('MACHIN3_GGT_pipe')

    def add_gizmo_point(self, co):
        point = {'co': co,
                 'index': -1,

                 'show': False,

                 'modulate': 0,
                 'segment_modulate': 0}

        self.gizmo_data['points'].append(point)

        self.ensure_gizmo_point_indices()

    def remove_gizmo_point(self, idx):
        self.gizmo_data['points'].pop(idx)

        self.ensure_gizmo_point_indices()

    def ensure_gizmo_point_indices(self):
        for idx, point in enumerate(self.gizmo_data['points']):
            point['index'] = idx

def draw_pipe_status(op):
    def draw(self, context):
        layout = self.layout

        row = layout.row(align=True)

        row.label(text="Add Pipe")

        if len(op.pipe_coords) > 1:
            draw_status_item(row, key='SPACE', text="Finish")

        draw_status_item(row, key='MMB', text="Viewport")
        draw_status_item(row, key='RMB', text="Cancel")

        row.separator(factor=10)

        if len(op.pipe_coords) > 1:
            draw_status_item(row, key='O', text="Origin", prop=op.origin.title().replace('_', ' '))

            draw_status_item(row, active=op.delete_mode, key='D', text="Delete Mode", gap=2)

            if op.delete_mode:
                draw_status_item(row, key='MMB_SCROLL', text="Select Previous/Next Curve Point for Deletion", gap=1)

            else:
                axis = 'X' if op.is_mirror_x else 'Y' if op.is_mirror_y else 'Z' if op.is_mirror_z else False
                draw_status_item(row, key=['X', 'Y', 'Z'], text="Mirror", prop=axis, gap=2)

        if len(op.pipe_coords) > 2 and not op.delete_mode:
            draw_status_item(row, active=op.is_cyclic, key='C', text="Cyclic", gap=2)

            draw_status_item(row, active=op.is_rounded, key='R', text="Rounded", gap=2)

            if op.is_rounded:
                draw_status_item(row, active=op.is_adaptive, key='A', text="Adaptive", gap=2)

                draw_status_item(row, key='MMB_SCROLL', text="Factor" if op.is_adaptive else "Segments", prop=op.adaptive_factor if op.is_adaptive else op.round_segments, gap=2)

                draw_status_item(row, key='Q', text="Mode", prop=op.round_mode.title(), gap=2)

                draw_status_item(row, key='W', text=f"Adjust {op.round_mode.title()}", gap=2)

        if len(op.pipe_coords) > 1:
            draw_status_item(row, key='TAB', text="Finish + Invoke AdjustPipe", gap=2)

    return draw

class AddPipe(bpy.types.Operator, PipeGizmoManager):
    bl_idname = "machin3.add_pipe"
    bl_label = "MACHIN3: Add Pipe"
    bl_description = "Create Pipe Curve"
    bl_options = {'REGISTER', 'UNDO'}

    is_cyclic: BoolProperty(name="is Cyclic", default=False)
    is_rounded: BoolProperty(name="is Rounded", default=False)
    is_mirror_x: BoolProperty(name="is Mirror X", default=False)
    is_mirror_y: BoolProperty(name="is Mirror Y", default=False)
    is_mirror_z: BoolProperty(name="is Mirror Z", default=False)
    round_mode: EnumProperty(name="Round Mode", items=pipe_round_mode_items, default='RADIUS')
    round_segments: IntProperty(name="Round Segments", default=6, min=0)
    is_adaptive: BoolProperty(name="is Adaptive", default=True)
    adaptive_factor: IntProperty(name="Adaptive Factor", default=10, min=1)
    radius: FloatProperty(name="Radius", default=0.1, min=0)
    origin: EnumProperty(name="Origin", items=pipe_origin_items, default='AVERAGE_ENDS')
    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def draw_VIEW3D(self, context):
        if context.area == self.area:
            if len(self.cursor_coords) > 1:

                draw_line(self.pipe_coords, color=blue, width=3, alpha=0.8)

                draw_point(self.origin_loc, color=yellow, size=6)

                axes = [(Vector((1, 0, 0)), red), (Vector((0, 1, 0)), green), (Vector((0, 0, 1)), blue)]
                factor = get_zoom_factor(context, self.origin_loc, scale=20, ignore_obj_scale=True)
                size = 1

                for axis, color in axes:
                    coords = []

                    coords.append(self.origin_loc + (self.origin_rot @ axis).normalized() * size * factor * 0.1)
                    coords.append(self.origin_loc + (self.origin_rot @ axis).normalized() * size * factor)

                    draw_line(coords, color=color, alpha=1)

            if self.delete_mode:
                draw_point(self.cursor_coords[self.delete_idx], size=11 if self.is_rounded else 7, color=red, alpha=1)

            color, size = (yellow, 5) if self.is_rounded else (white, 3)
            draw_points(self.cursor_coords, size=size, color=color, alpha=0.5)

            if self.is_rounded:
                color = green if self.round_mode == 'RADIUS' else orange

                if self.rounded_mid_coords:
                    draw_points(self.rounded_mid_coords, size=5 if self.round_mode == 'RADIUS' else 4, color=color, alpha=0.5)

                if self.rounded_trim_coords:
                    draw_points(self.rounded_trim_coords, size=3, color=color, alpha=1)

                if self.rounded_mid_coords and self.rounded_trim_coords:

                    if self.round_mode == 'RADIUS':
                        for mid, trim_prev, trim_next in zip(self.rounded_mid_coords, self.rounded_trim_coords[0::2], self.rounded_trim_coords[1::2]):
                            draw_line([mid, trim_prev], alpha=0.2)
                            draw_line([mid, trim_next], alpha=0.2)

                    elif self.round_mode == 'OFFSET':
                        for corner, trim_prev, trim_next in zip(self.rounded_corner_coords, self.rounded_trim_coords[0::2], self.rounded_trim_coords[1::2]):
                            draw_line([corner, trim_prev], alpha=0.2)
                            draw_line([corner, trim_next], alpha=0.2)

                if self.rounded_arc_coords:
                    draw_points(self.rounded_arc_coords, size=3, alpha=0.5)

    def draw_HUD(self, context):
        if context.area == self.area:
            draw_init(self)

            if self.is_rounded and self.adjust_radius_mode:
                draw_label(context, title=f"Adjust {self.round_mode.title()}", coords=Vector((self.HUD_x, self.HUD_y)), center=False, color=white, alpha=1)

                self.offset += 18
                draw_label(context, title=dynamic_format(self.radius, decimal_offset=1), coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=yellow, alpha=1)

    def modal(self, context, event):
        if ignore_events(event):
            return {'RUNNING_MODAL'}

        if not context.area:
            self.finish(context)
            return {'CANCELLED'}

        context.area.tag_redraw()

        update_mod_keys(self, event)

        if ignore_events(event, timer=True, timer_report=True):
            return {'RUNNING_MODAL'}

        if self.is_rounded and event.type == 'ESC':
            return {'PASS_THROUGH'}

        elif event.shift and event.type == 'W':
            return {'PASS_THROUGH'}

        if event.type == 'W':
            if self.is_rounded:
                if event.value == 'PRESS':
                    get_mouse_pos(self, context, event)

                    self.last_mouse = self.mouse_pos

                    self.adjust_radius_mode = True

                    self.factor = get_zoom_factor(context, depth_location=self.cursor.location, scale=1, ignore_obj_scale=True)

                    context.window.cursor_set('SCROLL_X')

                elif event.value == 'RELEASE':
                    self.adjust_radius_mode = False

                    context.window.cursor_set('DEFAULT')

            return {'RUNNING_MODAL'}

        self.pipe_coords = self.get_pipe_coords(context, debug=False)

        if event.type == 'D':

            if len(self.cursor_coords) == 1:
                self.finish(context)
                return {'CANCELLED'}

            else:
                if event.value == 'PRESS':

                    if not self.delete_mode:
                        self.delete_mode = True
                        self.delete_idx = len(self.cursor_coords) - 1

                    context.window.cursor_set('STOP')

                elif event.value == 'RELEASE':
                    self.delete_mode = False

                    self.remove_cursor_coord(context, debug=False)

                    context.window.cursor_set('DEFAULT')

                    self.pipe_coords = self.get_pipe_coords(context, debug=False)

                force_ui_update(context)

            return {'RUNNING_MODAL'}

        if self.delete_mode:

            if scroll(event, key=True):
                if scroll_up(event, key=True):
                    self.delete_idx = max(self.delete_idx - 1, 0)

                elif scroll_down(event, key=True):
                    self.delete_idx = min(self.delete_idx + 1, len(self.cursor_coords) - 1)

            return {'RUNNING_MODAL'}

        events = ['MOUSEMOVE', 'R', 'Q', 'A', 'X', 'Y', 'Z', 'O']

        if event.type == 'C' and not event.shift:
            events.append('C')

        if event.type in events or (self.is_rounded and scroll(event, key=True)):
            if event.type == 'MOUSEMOVE' and self.adjust_radius_mode:
                get_mouse_pos(self, context, event)
                wrap_mouse(self, context, x=True)

                delta_x = self.mouse_pos.x - self.last_mouse.x
                factor = self.factor / 20 if event.shift else self.factor * 10 if self.is_ctrl else self.factor

                self.radius += delta_x * factor

                self.pipe_coords = self.get_pipe_coords(context, debug=False)

            if event.value == 'PRESS':
                if len(self.cursor_coords) > 1:

                    if event.type == 'O':
                        self.origin = step_enum(self.origin, pipe_origin_items, step=1, loop=True)

                    elif event.type in ['X', 'Y', 'Z']:
                        if event.type == 'X':
                            self.is_mirror_x = not self.is_mirror_x
                            self.is_mirror_y = False
                            self.is_mirror_z = False

                        elif event.type == 'Y':
                            self.is_mirror_x = False
                            self.is_mirror_y = not self.is_mirror_y
                            self.is_mirror_z = False

                        elif event.type == 'Z':
                            self.is_mirror_x = False
                            self.is_mirror_y = False
                            self.is_mirror_z = not self.is_mirror_z

                if len(self.cursor_coords) > 2:

                    if event.type == 'C':
                        self.is_cyclic = not self.is_cyclic

                    elif event.type == 'R':
                        self.is_rounded = not self.is_rounded

                        if self.is_rounded and not self.has_rounded_been_activated:
                            self.has_rounded_been_activated = True
                            self.radius = min([(co2 - co1).length for co1, co2 in zip(self.cursor_coords, self.cursor_coords[1:])]) / 2

                        if not self.is_rounded:
                            for point in self.gizmo_data['points']:
                                point['show'] = False

                    elif self.is_rounded and event.type == 'Q':
                        self.round_mode = step_enum(self.round_mode, pipe_round_mode_items, step=1, loop=True)

                    elif event.type == 'A':
                        self.is_adaptive = not self.is_adaptive

                    elif scroll(event, key=True):
                        if scroll_up(event, key=True):
                            if self.is_adaptive:
                                self.adaptive_factor -= 10 if self.is_ctrl else 1
                            else:
                                self.round_segments += 1

                        elif scroll_down(event, key=True):
                            if self.is_adaptive:
                                self.adaptive_factor += 10 if self.is_ctrl else 1
                            else:
                                self.round_segments -= 1

                self.pipe_coords = self.get_pipe_coords(context, debug=False)

                force_ui_update(context)

                return {'RUNNING_MODAL'}

        if self.cursor.location != self.cursor_coords[-1]:

            if False:
                print()
                print("adding pipe coord:", self.cursor.location)
                print("last cursor coord:", self.cursor_coords[-1])
                print("event:", event.type)

            self.add_pipe_point(context, debug=False)

            self.pipe_coords = self.get_pipe_coords(context, debug=False)

        if self.cursor.matrix.to_3x3() != self.last_cursor_rotation:
            if any([self.is_mirror_x, self.is_mirror_y, self.is_mirror_z]):
                self.pipe_coords = self.get_pipe_coords(context, debug=False)

        if event.type in ['SPACE', 'TAB'] and len(self.pipe_coords) > 1:
            self.finish(context)
            self.create_curve_object(context)

            if event.type == 'TAB':
                bpy.ops.machin3.adjust_pipe('INVOKE_DEFAULT')

            return {'FINISHED'}

        elif event.type in ['RIGHTMOUSE'] and event.value == 'PRESS':
            self.finish(context)

            return {'CANCELLED'}

        self.last_mouse = self.mouse_pos

        self.last_cursor_rotation = self.cursor.matrix.to_3x3()

        return {'PASS_THROUGH'}

    def finish(self, context):
        finish_modal_handlers(self)

        finish_status(self)

        self.gizmo_group_finish(context)

        restore_gizmos(self)

        force_ui_update(context)

    def invoke(self, context, event):
        self.cursor = context.scene.cursor
        self.last_cursor_rotation = self.cursor.matrix.to_3x3()
        self.is_rounded = False
        self.has_rounded_been_activated = False
        self.adjust_radius_mode = False
        self.delete_mode = False
        self.delete_idx = 0

        self.origin_loc = self.cursor.location.copy()
        self.origin_rot = self.cursor.rotation_quaternion.copy()

        self.factor = get_zoom_factor(context, depth_location=self.cursor.location, scale=5, ignore_obj_scale=True)

        self.gizmo_group_init(context)

        self.cursor_coords = []
        self.add_pipe_point(context, debug=False)

        self.pipe_coords = self.cursor_coords.copy()

        self.rounded_mid_coords = []
        self.rounded_corner_coords = []
        self.rounded_trim_coords = []
        self.rounded_arc_coords = []

        hide_gizmos(self, context, buttons=['HISTORY', 'FOCUS', 'SETTINGS', 'CAST', 'OBJECT'], debug=False)

        hc = context.scene.HC
        hc.show_gizmos = True
        hc.show_button_cast = True
        hc.draw_HUD = True

        hc.draw_pipe_HUD = True
        self.hidden_gizmos['draw_pipe_HUD'] = False

        self.store_pre_pipe_gizmo_settings_on_scene(context)

        get_mouse_pos(self, context, event)

        self.last_mouse = self.mouse_pos

        update_mod_keys(self)

        init_status(self, context, func=draw_pipe_status(self))

        force_ui_update(context)

        init_modal_handlers(self, context, hud=True, view3d=True)
        return {'RUNNING_MODAL'}

    def add_pipe_point(self, context, debug=False):

        coord = self.cursor.location.copy()

        self.cursor_coords.append(coord)

        self.add_gizmo_point(coord)

        if debug:
            print()
            print("added new pipe co to self.cursor_coords and HCpiperaddiCOL")

            for co in self.cursor_coords:
                print(co)

        if len(self.cursor_coords) > 2:
            redundant = []

            if debug:
                print()
                print("checking for redundant coords")

            for idx, co in enumerate(self.cursor_coords):

                if 0 < idx < len(self.cursor_coords) - 1:
                    prev_co = self.cursor_coords[(idx - 1) % len(self.cursor_coords)]
                    next_co = self.cursor_coords[(idx + 1) % len(self.cursor_coords)]

                    if debug:
                        print(idx, co)
                        print(" prev:", prev_co)
                        print(" next:", next_co)

                    vec_prev = (prev_co - co).normalized()
                    vec_next = (next_co - co).normalized()

                    angle = round(degrees(vec_prev.angle(vec_next)))

                    if debug:
                        print(" angle:", angle)

                    if angle in [0, 180]:
                        redundant.append(idx)

                        if debug:
                            print(" is redundant")

            if redundant:
                if debug:
                    print()
                    print("removing indices:", redundant)

                for idx in sorted(redundant, reverse=True):
                    if debug:
                        print("removing redundant index:", idx)

                    self.cursor_coords.pop(idx)
                    self.remove_gizmo_point(idx)

                if debug:
                    print()
                    print("post redundancy removal")

                    for co in self.cursor_coords:
                        print("", co)

                    print()

                    for p in self.gizmo_data['points']:
                        print(p['co'])

        force_ui_update(context)

    def remove_cursor_coord(self, context, debug=False):
        if debug:
            print("\nremoving index", self.delete_idx)

        self.cursor_coords.pop(self.delete_idx)
        self.remove_gizmo_point(self.delete_idx)

        if debug:
            for co in self.cursor_coords:
                print("", co)

            print()

            for point in self.gizmo_data['points']:
                print("", point['co'])

        if self.delete_idx != len(self.cursor_coords) - 1:
            self.cursor.location = self.cursor_coords[-1]

            bpy.ops.view3d.view_center_cursor('INVOKE_DEFAULT' if context.scene.HC.focus_mode == 'SOFT' else 'EXEC_DEFAULT')

    def get_pipe_coords(self, context, debug=False):
        is_mirror = any([self.is_mirror_x, self.is_mirror_y, self.is_mirror_z])

        if is_mirror:
            mirror_coords, angle = self.get_mirror_coords(debug=debug)

            if mirror_coords:
                cursor_coords = self.cursor_coords + mirror_coords

        else:
            cursor_coords = self.cursor_coords.copy()

        if self.is_rounded:
            pipe_coords = self.get_rounded_pipe_coords(context, cursor_coords, debug=False)

        else:

            if is_mirror and round(angle) == 180:
                cursor_coords.pop(len(self.cursor_coords) - 1)

            pipe_coords = cursor_coords.copy()

            if self.is_cyclic:
                pipe_coords.append(self.cursor_coords[0])

        self.update_pipe_origin(cursor_coords)

        return pipe_coords

    def get_rounded_pipe_coords(self, context, cursor_coords, debug=False):
        def get_arc_coords(idx, co, prev_co, next_co, modulate, segment_modulate, debug=False):
            vec_prev = (prev_co - co).normalized()
            vec_next = (next_co - co).normalized()

            if vec_prev.length != 0 and vec_next.length != 0:
                angle = degrees(vec_prev.angle(vec_next))

                if round(angle) == 180:
                    if debug:
                        print(idx, "coord is 180 degees and so redundant")
                    return []

            else:
                if debug:
                    print(idx, "coord has zero length vectors to the next and/or previous")
                return [co]

            if debug:
                print(idx, "has", angle, "degrees")

            if self.round_mode == 'OFFSET':
                trim_prev_co = co + vec_prev * (self.radius + modulate)
                trim_next_co = co + vec_next * (self.radius + modulate)

                beta = angle / 2
                a = self.radius + modulate
                b = a * tan(radians(beta))

            elif self.round_mode == 'RADIUS':

                alpha = 180 - 90 - (angle / 2)
                b = self.radius + modulate
                a = b * tan(radians(alpha))

                trim_prev_co = co + vec_prev * a
                trim_next_co = co + vec_next * a

            arc_coords = [trim_prev_co]

            self.rounded_trim_coords.extend([trim_prev_co, trim_next_co])

            c = sqrt(pow(a, 2) + pow(b, 2))

            vec_mid = (vec_prev + vec_next).normalized()
            mid_co = co + vec_mid * c

            self.rounded_mid_coords.append(mid_co)
            self.rounded_corner_coords.append(co)

            arc_vec_prev = trim_prev_co - mid_co
            arc_vec_next = trim_next_co - mid_co

            delta = arc_vec_prev.rotation_difference(arc_vec_next)

            if self.is_adaptive:

                if self.round_mode == 'RADIUS':
                    segments = round((180 - angle) / self.adaptive_factor) + int(segment_modulate)

                elif self.round_mode == 'OFFSET':

                    arc_length = b * (180 - angle)
                    segments = round(arc_length / (self.adaptive_factor / 10)) + int(segment_modulate)

            else:
                segments = self.round_segments + 1 + int(segment_modulate)

            for segment in range(1, segments):
                factor = segment / segments

                rot = delta.copy()
                rot.angle = delta.angle * factor

                arc = rot @ arc_vec_prev

                arc_co = mid_co + arc

                arc_coords.append(arc_co)

                self.rounded_arc_coords.append(arc_co)

            arc_coords.append(trim_next_co)

            return arc_coords

        self.rounded_mid_coords = []
        self.rounded_corner_coords = []
        self.rounded_trim_coords = []
        self.rounded_arc_coords = []

        if debug:
            print("\npre-rounding coordinate comparison")

            print(len(self.cursor_coords))
            print(len(self.gizmo_data['points']))
            print(len(cursor_coords))

            print()
            print("compare")

        is_mirror = len(self.gizmo_data['points']) != len(cursor_coords)
        is_cyclic = self.is_cyclic

        rounded_coords = []

        for idx, (origco, point, argco) in enumerate(zip_longest(self.cursor_coords, self.gizmo_data['points'], cursor_coords)):

            if debug:
                print()
                print(idx)
                print("orig:", origco)
                print(" col:", point['co'] if point else None)
                print(" arg:", argco)

            if idx == 0:
                if is_cyclic:
                    prev_co = cursor_coords[-1]
                    next_co = cursor_coords[idx + 1]

                    modulate = self.gizmo_data['points'][idx]['modulate']
                    segment_modulate = self.gizmo_data['points'][idx]['segment_modulate']

                    if debug:
                        print("first coord, and it's cyclic, so is rounded", modulate)
                else:
                    if debug:
                        print("first coord, no rounding")

                    rounded_coords.append(argco)

                    point['show'] = False
                    continue

            elif is_mirror and (idx == len(self.gizmo_data['points']) - 1 or idx == len(cursor_coords) - 1):

                if idx == len(self.gizmo_data['points']) - 1:
                    prev_co = cursor_coords[idx - 1]
                    next_co = cursor_coords[idx + 1]

                    modulate = self.gizmo_data['points'][idx]['modulate']
                    segment_modulate = self.gizmo_data['points'][idx]['segment_modulate']

                    if debug:
                        print("mirror intersection coord", modulate)

                elif idx == len(cursor_coords) - 1:
                    if is_cyclic:
                        mapped_back_idx = 0

                        prev_co = cursor_coords[idx - 1]
                        next_co = cursor_coords[0]

                        modulate = self.gizmo_data['points'][mapped_back_idx]['modulate']
                        segment_modulate = self.gizmo_data['points'][mapped_back_idx]['segment_modulate']

                        if debug:
                            print("last mirrored coord and its cyclic, so is rounded", modulate)
                            print(" but get's no gizmo!")
                            print(" mapped back to", mapped_back_idx)

                    else:
                        if debug:
                            print("last mirrored coord, no rounding")

                        rounded_coords.append(argco)
                        continue

            elif idx == len(self.gizmo_data['points']) - 1:
                if is_cyclic:
                    prev_co = cursor_coords[idx - 1]
                    next_co = cursor_coords[0]

                    modulate = self.gizmo_data['points'][idx]['modulate']
                    segment_modulate = self.gizmo_data['points'][idx]['segment_modulate']

                    if debug:
                        print("last original coord and it's cyclic, so is rounded", modulate)

                else:
                    if debug:
                        print("last original coord, no rounding")

                    rounded_coords.append(argco)

                    point['show'] = False
                    continue

            else:
                prev_co = cursor_coords[idx - 1]
                next_co = cursor_coords[idx + 1]

                if point:
                    modulate = self.gizmo_data['points'][idx]['modulate']
                    segment_modulate = self.gizmo_data['points'][idx]['segment_modulate']

                    if debug:
                        print("normal coord, so is rounded", modulate)

                else:
                    mapped_back_idx = len(cursor_coords) - idx - 1
                    modulate = self.gizmo_data['points'][mapped_back_idx]['modulate']
                    segment_modulate = self.gizmo_data['points'][mapped_back_idx]['segment_modulate']

                    if debug:
                        print("normal mirrored coord, so is rounded", modulate)
                        print(" but get's no gizmo!")
                        print(" mapped back to", mapped_back_idx)

            arc_coords = get_arc_coords(idx, argco, prev_co, next_co, modulate, segment_modulate, debug=debug)
            rounded_coords.extend(arc_coords)

            if point:
                point['show'] = len(arc_coords) > 1

        if is_cyclic:
            rounded_coords.append(rounded_coords[0])

        return rounded_coords

    def get_mirror_coords(self, debug=False):
        axis = 'X' if self.is_mirror_x else 'Y' if self.is_mirror_y else 'Z' if self.is_mirror_z else None

        mirror_coords = []

        if axis:
            if debug:
                print("mirroring across", axis)

            mirror_dir = self.cursor.matrix.to_3x3() @ axis_vector_mappings[axis]

            for co in reversed(self.cursor_coords[:-1]):
                i = intersect_line_plane(co, co + mirror_dir, self.cursor.location, mirror_dir)

                mirror_vec = i - co

                mirror_co = co + 2 * mirror_vec

                mirror_coords.append(mirror_co)

        vec_prev = self.cursor_coords[-2] - self.cursor_coords[-1]
        vec_next = mirror_coords[0] - self.cursor_coords[-1]
        mirror_angle = degrees(vec_prev.angle(vec_next))

        return mirror_coords, mirror_angle

    def update_pipe_origin(self, coords, debug=False):
        if self.origin in ['AVERAGE_ENDS', 'CURSOR_ORIENTATION']:
            self.origin_loc = average_locations([coords[0], coords[-1]])

        else:
            self.origin_loc = self.cursor.location

        if self.origin == 'AVERAGE_ENDS' and len(coords) > 2:

            v_start = (coords[1] - coords[0]).normalized()
            v_end = (coords[-2] - coords[-1]).normalized()
            z = average_normals([v_start, v_end])

            x = (coords[-1] - coords[0]).normalized()

            y = z.cross(x)

            z = x.cross(y)

            if debug:
                draw_vector(x * 0.1, origin=self.origin_loc + Vector((0, 0, 0.1)), color=red, alpha=1, modal=False)
                draw_vector(y * 0.1, origin=self.origin_loc + Vector((0, 0, 0.1)), color=green, alpha=1, modal=False)
                draw_vector(z * 0.1, origin=self.origin_loc + Vector((0, 0, 0.1)), color=blue, alpha=1, modal=False)

            self.origin_rot = create_rotation_matrix_from_vectors(x, y, z).to_quaternion()

        else:
            self.origin_rot = self.cursor.rotation_quaternion

    def store_pre_pipe_gizmo_settings_on_scene(self, context):
        context.scene.HC['hidden_gizmos'] = self.hidden_gizmos

    def create_curve_object(self, context):
        pipemx = Matrix.LocRotScale(self.origin_loc, self.origin_rot, Vector((1, 1, 1)))

        curve = bpy.data.curves.new('Pipe', type='CURVE')

        curve = bpy.data.curves.new(name='Curve', type='CURVE')
        curve.dimensions = '3D'

        curve.use_fill_caps = True
        curve.bevel_resolution = 12

        spline = curve.splines.new('POLY')

        coords = self.pipe_coords[:-1] if self.is_cyclic else self.pipe_coords
        spline.use_cyclic_u = self.is_cyclic

        spline.points.add(len(coords) - 1)

        for idx, co in enumerate(coords):
            local_co = pipemx.inverted_safe() @ co
            spline.points[idx].co = (*local_co, 1)

        spline.use_smooth = False

        pipe = bpy.data.objects.new('Pipe', object_data=curve)
        pipe.matrix_world = pipemx

        pipe.HC.ishyper = True

        bpy.ops.object.select_all(action='DESELECT')

        context.scene.collection.objects.link(pipe)
        pipe.select_set(True)
        context.view_layer.objects.active = pipe

class AddCurveAsset(bpy.types.Operator):
    bl_idname = "machin3.add_curve_asset"
    bl_label = "MACHIN3: Add Curve Asset"
    bl_description = ""
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            return context.active_object

    def invoke(self, context, event):
        curve = context.active_object
        is_bevel_profile, spline = self.verify_bevel_profile(curve)

        if is_bevel_profile:

            from . bevel import HyperBevelGizmoManager as mng

            if mng.operator_data:

                mods = mng.operator_data['bevel_mods']
                active = mng.operator_data['active']
                if is_valid_object(active):

                    mods = mng.operator_data['bevel_mods']

                    for sidx, mod in enumerate(mods):

                        coords = get_profile_coords_from_spline(spline, flop=not mng.gizmo_data['sweeps'][sidx]['convex'])

                        create_bevel_profile(mod, coords)

                    remove_obj(curve)

                    active.select_set(True)
                    context.view_layer.objects.active = active

                    mng.operator_data['push_update'] = True
                    return {'FINISHED'}

            from . bevel import PickHyperBevelGizmoManager as mng2

            if gizmo_data := mng2.gizmo_data:

                hyper_bevel = None

                for b in gizmo_data['hyperbevels']:
                    if b['is_highlight']:
                        hyper_bevel = b

                if hyper_bevel:
                    obj = hyper_bevel['obj']
                    active = obj.parent

                    edge_bevel = obj.modifiers.get('Edge Bevel')

                    if edge_bevel:

                        coords = get_profile_coords_from_spline(spline, flop=False)

                        create_bevel_profile(edge_bevel, coords)

                        remove_obj(curve)

                        active.select_set(True)
                        context.view_layer.objects.active = active

                        bpy.ops.machin3.edit_hyper_bevel('INVOKE_DEFAULT', modname=hyper_bevel['modname'], objname=active.name, is_profile_drop=True)

                        return {'FINISHED'}

                    else:
                        self.msg.append("There is no Edge Bevel Modifier on this HyperBevel!")
                        draw_fading_label(context, text=self.msg, color=[yellow, white], alpha=[1, 0.5])
                        return {'CANCELLED'}

        is_wire_shading = context.space_data.shading.type == 'WIREFRAME'

        wire_objs = [] if is_wire_shading else [obj for obj in context.visible_objects if is_wire_object(obj)]

        get_mouse_pos(self, context, event)

        hit, hitobj, _, hitlocation_eval, _, _ = cast_scene_ray_from_mouse(self.mouse_pos, context.evaluated_depsgraph_get(), exclude=wire_objs, cache={}, debug=False)

        if hit:

            if hitobj.type == 'MESH':

                if is_bevel_profile:
                    bevel_obj = hitobj
                    mx = bevel_obj.matrix_world

                    hitobj, hitlocation, hitnormal, hitindex, hitdistance, cache = cast_bvh_ray_from_mouse(self.mouse_pos, candidates = [bevel_obj], debug=False)

                    hit_co = mx.inverted_safe() @ hitlocation

                    bm = bmesh.new()
                    bm.from_mesh(bevel_obj.data)
                    bm.normal_update()
                    bm.faces.ensure_lookup_table()

                    vertex_group_layer = bm.verts.layers.deform.verify()
                    edge_glayer = ensure_edge_glayer(bm)

                    hitface = bm.faces[hitindex]

                    gizmo_edges = [e for e in hitface.edges if e[edge_glayer] == 1]

                    if gizmo_edges:

                        edge = min([(e, (hit_co - intersect_point_line(hit_co, e.verts[0].co, e.verts[1].co)[0]).length, (hit_co - get_center_between_verts(*e.verts)).length) for e in gizmo_edges if e.calc_length()], key=lambda x: (x[1] * x[2]) / x[0].calc_length())[0]

                        is_concave = is_edge_concave(edge)

                        index = edge.index

                        vg_name = weight_name = None

                        edge_bevel, vg_name = get_edge_bevel_from_edge_vgroup(bevel_obj, edge, vertex_group_layer)

                        if not edge_bevel and bpy.app.version >= (4, 3, 0):
                            edge_bevel, weight_name = get_edge_bevel_from_edge_weight(bm, bevel_obj, edge)

                        if edge_bevel:

                            coords = get_profile_coords_from_spline(spline, flop=is_concave)

                            create_bevel_profile(edge_bevel, coords)

                            if bevel_obj.data.users > 1:
                                instanced_objects = [obj for obj in bpy.data.objects if obj.data == bevel_obj.data and obj != bevel_obj]

                                for obj in instanced_objects:
                                    if vg_name:
                                        mods = [mod for mod in obj.modifiers if is_edge_bevel(mod) and mod.limit_method == 'VGROUP' and mod.vertex_group == vg_name]

                                    elif weight_name:
                                        mods = [mod for mod in obj.modifiers if is_edge_bevel(mod) and mod.limit_method == 'WEIGHT' and mod.edge_weight == weight_name]

                                    if mods:
                                        create_bevel_profile(mods[0], coords)

                            remove_obj(curve)

                            bpy.ops.object.select_all(action='DESELECT')
                            bevel_obj.select_set(True)
                            context.view_layer.objects.active = bevel_obj

                            bpy.ops.machin3.bevel_edge('INVOKE_DEFAULT', index=index, is_profile_drop=True)

                            return {'FINISHED'}

                        else:
                            self.msg.append("There is no Edge Bevel Modifier close to the dropped location!")

                            if gizmo_data:
                                self.msg.append("If you want to apply the profile to a HyperBevel, then you need to drop it on the Gizmo!")

                    else:
                        self.msg.append("There are no Edges with Gizmos close to the dropped location!")

                    remove_obj(curve)
                    draw_fading_label(context, text=self.msg, color=[yellow, white], alpha=[1, 0.5])

                else:
                    msg = ["ℹℹ Drop Curve Assets on Pipes, if you want ot use them as Profiles ℹℹ",
                           "Otherwise prepare the curve like a proper Bevel Profile, if you want to use the Curve for that"]

                    draw_fading_label(context, text=msg, color=[yellow, white], alpha=[1, 0.5])
                return {'CANCELLED'}

            elif hitobj.type == 'CURVE':
                pipe = hitobj

                curve.matrix_world = pipe.matrix_world
                parent(curve, pipe)

                pipe.data.bevel_mode = 'OBJECT'
                pipe.data.bevel_object = curve

                maxdim = max(curve.dimensions)

                if pipe.data.bevel_depth == 0:
                    pipe.data.bevel.depth = 0.0001

                dimdivisor = maxdim / pipe.data.bevel_depth / 2
                curve.dimensions = curve.dimensions / dimdivisor

                context.view_layer.objects.active = pipe
                pipe.select_set(True)

                bpy.ops.machin3.adjust_pipe('INVOKE_DEFAULT', is_profile_drop=True)

                return {'FINISHED'}

        return {'CANCELLED'}

    def verify_bevel_profile(self, curve):
        self.msg = ["ℹℹ The dropped Curve Asset couldn't be used as a Bevel Profile ℹℹ"]

        data = get_curve_as_dict(curve.data)

        if spline := verify_curve_data(data, 'is_first_spline_non-cyclic'):

            if verify_curve_data(data, 'is_first_spline_profile'):
                return True, spline

            else:
                self.msg.append("The Profile needs to have a first point, that is to the left, and above the last point!")

        else:
            self.msg.append("The Profile can't be a cyclic Curve!")

        return False, None
