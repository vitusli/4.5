import bpy
from bpy.props import BoolProperty, StringProperty
import bmesh

from mathutils import Vector, Matrix
from mathutils.geometry import intersect_line_line, intersect_line_plane, intersect_point_line

from math import degrees
import numpy as np

from .. import HyperCursorManager as HC

from .. utils.bmesh import get_face_angle, get_tri_coords, ensure_gizmo_layers
from .. utils.draw import draw_fading_label, draw_point, draw_vector, draw_tris, draw_line, draw_points, draw_lines, draw_init, draw_label
from .. utils.gizmo import hide_gizmos, restore_gizmos
from .. utils.math import dynamic_format, get_center_between_points, get_center_between_verts, average_locations, get_loc_matrix, create_rotation_matrix_from_vectors, transform_coords
from .. utils.math import get_world_space_normal, create_rotation_matrix_from_normal
from .. utils.mesh import get_bbox, get_eval_mesh
from .. utils.modifier import add_solidify, apply_mod, get_new_mod_name, is_array, sort_mod_after_split, sort_modifiers, add_boolean, move_mod
from .. utils.object import get_eval_bbox, hide_render, parent, get_min_dim, setup_split_boolean
from .. utils.operator import Settings
from .. utils.property import get_biggest_index_among_names
from .. utils.snap import Snap
from .. utils.ui import finish_modal_handlers, force_geo_gizmo_update, get_mouse_pos, ignore_events, init_modal_handlers, navigation_passthrough, get_zoom_factor, init_status, finish_status, force_ui_update, is_key, update_mod_keys, warp_mouse, draw_status_item
from .. utils.view import get_view_origin_and_dir

from .. colors import red, green, blue, yellow, white, normal, orange
from .. items import ctrl, alt, shift

def draw_hyper_cut_status(op):
    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)

        depth_limit = dynamic_format(op.cut['depth_limit'], decimal_offset=1) if 0 < op.cut['depth_limit'] < 1 else None
        width_limit = dynamic_format(op.cut['width_limit'], decimal_offset=1) if 0 < op.cut['width_limit'] < 1 else None

        row.label(text="Hyper Cut")

        if not op.cut['start']:
            draw_status_item(row, key='LMB_DRAG', text='Start Cut')

        elif op.cut['start'] and not op.cut['end']:
            draw_status_item(row, key='LMB_DRAG', text='Draw Out Hyper Cut')

        else:
            draw_status_item(row, key='SPACE', text='Finish Cut')
            draw_status_item(row, key='LMB', text='Finish Cut and Select Cutter')

        draw_status_item(row, key='MMB', text='Viewport')
        draw_status_item(row, key='RMB', text='Cancel')

        row.separator(factor=10)

        if op.is_depth_limiting:
            draw_status_item(row, active=bool(depth_limit), key='MOVE', text='Depth Limit', prop=depth_limit)

            draw_status_item(row, key='ALT', text='Invert Depth Limit', gap=2)

        elif op.is_width_limiting:
            draw_status_item(row, active=bool(width_limit), key='MOVE', text='Width Limit', prop=width_limit)

            draw_status_item(row, key='ALT', text='Invert Width Limit', gap=2)

        else:

            if not op.cut['start']:
                draw_status_item(row, active=op.is_bbox, key='ALT', text='Draw on BBox')

                draw_status_item(row, active=op.face_index is not None, key='F', text='Draw on Face', gap=2)  # NOTE: we use str() to force "None" being drawn

                draw_status_item(row, active=op.is_cursor, key='C', text='Draw on Cursor:', gap=2)

                if op.is_cursor:
                    draw_status_item(row, active=op.cursor_x, key='X', gap=0)
                    draw_status_item(row, active=op.cursor_y, key='Y', gap=0)
                    draw_status_item(row, active=op.cursor_z, key='Z', gap=0)

                draw_status_item(row, key='V', text='Align View with Draw Plane', gap=2)
                draw_status_item(row, key=['SHIFT', 'V'], text='Align View with inveerted Draw Plane', gap=0)

            if op.cut['start'] and op.cut['end']:

                draw_status_item(row, active=op.mode == 'SPLIT', key='S', text='Split', gap=2)

                if op.mode == 'SPLIT' and not op.apply_boolean:
                    draw_status_item(row, active=op.lazy_split, key='Q', text='Lazy Split', gap=1)

                draw_status_item(row, active=op.is_snapping, key='CTRL', text='Snapping', gap=2)

                if op.is_snapping:
                    draw_status_item(row, active=op.is_snapping_on_others, key='SHIFT', text='Snap on Others', gap=1)

                draw_status_item(row, key='F', text='Flip Cut', gap=2)

                draw_status_item(row, active=bool(depth_limit), key='D', text='Depth Limit', prop=depth_limit if depth_limit else None, gap=2)
                draw_status_item(row, active=bool(width_limit), key='W', text='Width Limit', prop=width_limit if width_limit else None, gap=1)

                draw_status_item(row, active=op.apply_boolean, key='A', text='Apply Boolean', gap=2)

                if not op.apply_boolean:
                    draw_status_item(row, active=op.minimize_cutter, key='M', text='Minimize Cutter', gap=1)

                    draw_status_item(row, key='TAB', text='Finish + Invoke HyperMod', gap=2)

    return draw

class HyperCut(bpy.types.Operator, Settings):
    bl_idname = "machin3.hyper_cut"
    bl_label = "MACHIN3: Hyper Cut"
    bl_description = ""
    bl_options = {'REGISTER', 'UNDO'}

    mode: StringProperty(name="Mode", default='CUT')
    is_bbox: BoolProperty(name="BBox Aligned Cutting", default=False)
    is_cursor: BoolProperty(name="Cursor Algned Cutting", default=False)
    cursor_x: BoolProperty(name="Cursor X Cutting", default=False)
    cursor_y: BoolProperty(name="Cursor Y Cutting", default=True)
    cursor_z: BoolProperty(name="Cursor Z Cutting", default=False)
    flip_width: BoolProperty(name="Flip Cutting Direction", default=False)
    lazy_split: BoolProperty(name="Lazy Split", default=False)
    is_depth_limiting: BoolProperty(name="Limit Depth", default=False)
    is_width_limiting: BoolProperty(name="Limit Width", default=False)
    apply_boolean: BoolProperty(name="Apply Boolean", default=False)
    minimize_cutter: BoolProperty(name="Minimize Cutter", default=False)
    active_cutter: BoolProperty(name="Make Cutter Active", default=False)
    is_tab_finish: BoolProperty(name="is Tab Finish", default=False)

    passthrough = None

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            active = context.active_object
            return active and active.type == 'MESH'

    def draw(self, context):
        layout = self.layout

        column = layout.column(align=True)

        row = column.row(align=True)
        row.prop(self, 'apply_boolean', toggle=True)

        if not self.apply_boolean:
            row.prop(self, 'active_cutter', toggle=True)

        row = column.row(align=True)
        row.prop(self, 'minimize_cutter', toggle=True)

    def draw_HUD(self, context):
        if context.area == self.area:
            draw_init(self)

            dims = Vector((0, 0))

            if self.cut['start']:
                dims += draw_label(context, title='Hyper ', coords=Vector((self.HUD_x, self.HUD_y)), center=False, alpha=1)

            if self.cut['start']:
                if self.mode == 'SPLIT' and self.lazy_split:
                    title = 'Lazy Split'
                else:
                    title = self.mode.title()
            else:
                title = 'Draw'

            color = green if self.cut['start'] and self.mode == 'SPLIT' else white
            dims += draw_label(context, title=title, coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, color=color, alpha=1)

            factor = 0.3 if self.cut['start'] else 1
            dims += draw_label(context, title=" on ", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=0.5 * factor)

            axis = 'X' if self.cursor_x else 'Y' if self.cursor_y else 'Z'
            title = 'BBox' if self.is_bbox else f'Cursor {axis} ' if self.is_cursor else f'Face {self.face_index}'
            color = red if self.is_bbox else green if self.is_cursor else blue
            dims += draw_label(context, title=title, coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=color, alpha=factor)

            if self.is_cursor:
                draw_label(context, title="plane", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=0.5 * factor)

            if self.cut['start']:

                if self.is_snapping:
                    self.offset += 18
                    dims = draw_label(context, title='Parallel ', coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=0.5)
                    dims += draw_label(context, title='Snapping ', coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=yellow, alpha=1)
                    linebreak_dims = dims.copy()

                    dims += draw_label(context, title='on ', coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=0.5)

                    if self.snap_target:
                        alpha = 1

                        if self.snap_target == 'EDGE':
                            color = yellow
                            title = 'Edge'

                        elif self.snap_target in ['BBOX', 'CURSOR']:
                            title = 'Border'
                            color = red if self.snap_target == 'BBOX' else green

                    else:
                        title, color, alpha = ('Nothing', white, 0.5)

                    draw_label(context, title=title, coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=color, alpha=alpha)

                    if self.snap_target == 'EDGE' and self.is_snapping_on_others and self.snap_obj_name:
                        self.offset += 18
                        dims = draw_label(context, title="of ", coords=Vector((self.HUD_x + linebreak_dims.x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=0.5)
                        draw_label(context, title=self.snap_obj_name, coords=Vector((self.HUD_x + linebreak_dims.x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=1)

                if (self.is_width_limiting or 0 < self.cut['width_limit'] < 1) and not (self.mode == 'SPLIT' and self.lazy_split):
                    self.offset += 18
                    title = 'None' if self.cut['width_limit'] in [0, 1] else dynamic_format(self.cut['width_limit'], decimal_offset=1)

                    if 0 < self.cut['width_limit'] < 1:
                        if self.is_width_limiting:
                            draw_label(context, title=f"Limit Width: {title}", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=orange, alpha=1)

                        else:
                            dims = draw_label(context, title="Limit Width: ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=0.5)
                            draw_label(context, title=title, coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=1)

                    else:
                        draw_label(context, title=f"Limit Width: {title}", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=0.25)

                if self.is_depth_limiting or 0 < self.cut['depth_limit'] < 1:
                    self.offset += 18
                    title = 'None' if self.cut['depth_limit'] in [0, 1] else dynamic_format(self.cut['depth_limit'], decimal_offset=1)

                    if 0 < self.cut['depth_limit'] < 1:
                        if self.is_depth_limiting:
                            draw_label(context, title=f"Limit Depth: {title}", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=orange, alpha=1)

                        else:
                            dims = draw_label(context, title="Limit Depth: ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=0.5)
                            draw_label(context, title=title, coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=1)

                    else:
                        draw_label(context, title=f"Limit Depth: {title}", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=0.25)

                if self.apply_boolean:
                    self.offset += 18
                    draw_label(context, title='Apply Boolean', coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=red, alpha=1)

                else:

                    if self.minimize_cutter:
                        self.offset += 18
                        draw_label(context, title='Minimize Cutter', coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=normal, alpha=1)

    def draw_VIEW3D(self, context):
        if context.area == self.area:

            if self.coords['draw_plane']:
                if not self.is_depth_limiting:
                    is_drawing = self.cut['start'] and self.cut['end']

                    if is_drawing:
                        color = white
                        alpha = 0.015 if any([self.is_bbox, self.is_cursor]) else 0.05

                    else:
                        color = red if self.is_bbox else green if self.is_cursor else blue
                        alpha = 0.05

                    mx = Matrix() if self.is_cursor else self.mx

                    draw_tris(self.coords['draw_plane'], mx=mx, color=color, alpha=alpha)

            if self.is_cursor:
                axes = [(self.cursor_x_dir, red), (self.cursor_y_dir, green), (self.cursor_z_dir, blue)]
                loc = self.cursor_origin
                scale = 0.5

                for axis, color in axes:
                    coords = [loc + axis * 0.1 * scale, loc + axis * scale]
                    draw_line(coords, color=color, width=2, alpha=1)

            if self.coords['cut_line']:
                draw_line(self.coords['cut_line'], color=red if self.apply_boolean else green, width=2, alpha=0.5)

            if self.cut['width']:
                is_lazy_split = self.mode == 'SPLIT' and self.lazy_split

                if not is_lazy_split:
                    draw_tris(self.coords['width_plane'], color=white, alpha=0.02)

                color = red if self.apply_boolean else green

                if self.mode == 'CUT':
                    for vector, origin in self.coords['cut_stripes']:
                        draw_vector(vector, origin=origin, color=color, width=10, alpha=0.1, fade=True)

                if self.is_width_limiting:
                    draw_line(self.coords['width_limit_line'], color=orange, alpha=1)

                if self.is_depth_limiting or 0 < self.cut['depth_limit'] < 1:
                    xray = not self.is_depth_limiting
                    cap = 7 if self.is_cursor else 4

                    if is_lazy_split:
                        color, alpha = (orange, 1) if self.is_depth_limiting else (white, 0.05)

                        draw_line(self.coords['depth_lazy_line'][:cap], color=color, alpha=alpha, xray=xray)
                        draw_tris(self.coords['depth_lazy_plane'], color=white, alpha=0.05 if self.is_depth_limiting else 0.02, xray=False)

                        if self.is_depth_limiting:
                            draw_line(self.coords['depth_lazy_line'][:cap], color=color, alpha=0.1, xray=True)

                    else:
                        alpha = 0.3 if self.is_depth_limiting else 0.05

                        draw_tris(self.coords['depth_plane'], color=white, alpha=alpha / 5, xray=xray)
                        draw_lines(self.coords['depth_lines'], alpha=alpha, xray=xray)

                        if self.is_depth_limiting:

                            xray = self.cut['width_limit'] in [0, 1]

                            draw_line(self.coords['depth_limit_line'][:cap], color=orange, alpha=1, xray=xray)
                            draw_line(self.coords['depth_limit_line'][:cap], color=orange, alpha=0.1, xray=True)

            if not self.is_depth_limiting:

                if self.coords['snap']:
                    color = yellow if self.snap_target == 'EDGE' else red if self.snap_target == 'BBOX' else green
                    draw_line(self.coords['snap'], width=2, color=color, alpha=1)

                    if self.coords['extended_snap']:
                        draw_line(self.coords['extended_snap'], width=1, color=color, alpha=0.3)

                    if self.coords['connected_snap']:
                        draw_lines(self.coords['connected_snap'], width=1, color=color, alpha=0.15)

            if self.cut['start']:
                draw_point(self.cut['start'], color=(1, 1, 1), size=3, alpha=0.5)

            if self.cut['end']:
                draw_point(self.cut['end'], color=(1, 1, 1), size=3, alpha=0.5)

            if self.is_bbox and self.bbox:
                coords = self.bbox[0]

                indices = [(0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7), (7, 4), (0, 4), (1, 5), (2, 6), (3, 7)]
                draw_lines(coords, indices=indices, mx=self.mx, alpha=0.05)

    def modal(self, context, event):
        if ignore_events(event):
            return {'RUNNING_MODAL'}

        context.area.tag_redraw()

        update_mod_keys(self, event)

        if self.cut['start'] and self.cut['end']:

            if not self.is_width_limiting:

                if is_key(self, event, 'D', onpress=self.update_depth_limiting(context, 'PRESS'), onrelease=self.update_depth_limiting(context, 'RELEASE')):
                    self.get_coords()
                    return self.adjust_depth_limit(context, event)

            if not self.is_depth_limiting and not (self.mode == 'SPLIT' and self.lazy_split):

                if is_key(self, event, 'W', onpress=self.update_width_limiting(context, 'PRESS'), onrelease=self.update_width_limiting(context, 'RELEASE')):
                    self.get_coords()
                    return self.adjust_width_limit(context, event)

        self.is_snapping = event.ctrl

        if self.is_snapping:
            self.is_snapping_on_others = event.shift

        if self.snap_dir and (not self.is_snapping or event.type in shift):
            self.snap_dir = None
            self.coords['snap'] = []
            self.coords['extended_snap'] = []
            self.coords['connected_snap'] = []

        if not self.cut['start'] and self.is_bbox:
            self.set_draw_plane_from_bbox(context)

        if self.passthrough:
            self.passthrough = False

            if self.is_cursor:
                self.update_cursor_plane_size(context)

        events = ['MOUSEMOVE', 'LEFTMOUSE', *ctrl, *alt, *shift, 'F', 'A', 'S', 'C', 'V']

        if self.is_width_limiting or self.is_depth_limiting:
            events.extend(['WHEELUPMOUSE', 'WHEELDOWNMOUSE'])

        if self.is_cursor:
            events.extend(['X', 'Y', 'Z'])

        if not self.apply_boolean:
            events.append('M')

            if self.mode == 'SPLIT' and not self.apply_boolean:
                events.extend(['L', 'Q'])

        if event.type in events:

            if event.type in ['MOUSEMOVE', 'LEFTMOUSE', *ctrl, *shift]:
                get_mouse_pos(self, context, event)

                if not self.cut['start'] and event.type == 'LEFTMOUSE' and event.value == 'PRESS':
                    self.get_start_point(context)

                    self.get_depth_vectors()

                    force_ui_update(context)

                elif self.cut['start'] and event.type in ['MOUSEMOVE', *ctrl, *shift] and not (self.is_depth_limiting or self.is_width_limiting):
                    self.get_end_point(context)

                if self.cut['start'] and self.cut['end']:

                    self.get_cut_vector()

                    self.get_cut_direction(debug=False)

                    self.get_width_vector(debug=False)

                    self.get_coords()

            if not self.cut['start']:

                if event.type == 'F' and event.value == 'PRESS':
                    if self.set_draw_plane_from_face(context):
                        self.is_bbox = False
                        self.is_cursor = False

                    else:
                        draw_fading_label(context, "Place the Mouse over the Object, then set the Draw Plane from a Face", color=yellow, move_y=20, time=2)

                elif event.type in alt and event.value == 'PRESS':
                    self.is_bbox = not self.is_bbox

                    if self.is_bbox:
                        if self.is_cursor:
                            self.is_cursor = False

                        self.set_draw_plane_from_bbox(context)

                    else:
                        if not self.set_draw_plane_from_face(context):
                            self.is_bbox = True
                            draw_fading_label(context, "Place the Mouse over the Object, then set the Draw Plane from a Face", color=yellow, move_y=20, time=2)

                elif event.type == 'C' and event.value == 'PRESS':
                    self.is_cursor = not self.is_cursor

                    if self.is_cursor:
                        if self.is_bbox:
                            self.is_bbox = False

                        self.set_draw_plane_from_cursor(context)

                    elif self.set_draw_plane_from_face(context):
                        pass

                    else:
                        self.is_bbox = True
                        self.set_draw_plane_from_bbox(context)

                elif self.is_cursor and event.type in ['X', 'Y', 'Z'] and event.value == 'PRESS':

                    if event.type == 'X':
                        self.cursor_x = True
                        self.cursor_y = False
                        self.cursor_z = False

                    elif event.type == 'Y':
                        self.cursor_x = False
                        self.cursor_y = True
                        self.cursor_z = False

                    elif event.type == 'Z':
                        self.cursor_x = False
                        self.cursor_y = False
                        self.cursor_z = True

                    self.set_draw_plane_from_cursor(context)

                elif event.type  == 'V' and event.value == 'PRESS':

                    if not self.init_viewmx:
                        self.init_viewmx = context.space_data.region_3d.view_matrix.copy()

                    self.align_view_to_draw_plane(context, inverted=event.shift, debug=False)

                    if self.is_cursor:
                        self.update_cursor_plane_size(context)

            elif self.cut['start'] and self.cut['end']:

                if event.type == 'S' and event.value == 'PRESS':
                    self.mode = 'SPLIT' if self.mode == 'CUT' else 'CUT'

                elif event.type == 'F' and event.value == 'PRESS':
                    self.flip_width = not self.flip_width

                    self.cut['direction'].negate()

                    self.get_width_vector()

                    self.get_coords()

                elif event.type == 'A' and event.value == 'PRESS':
                    self.apply_boolean = not self.apply_boolean

                    if self.apply_boolean:

                        if self.minimize_cutter:
                            self.minimize_cutter = False

                        if self.lazy_split:
                            self.lazy_split = False

                elif not self.apply_boolean and event.type == 'M' and event.value == 'PRESS':
                    self.minimize_cutter = not self.minimize_cutter

                elif event.type in ['L', 'Q'] and event.value == 'PRESS':
                    self.lazy_split = not self.lazy_split

                force_ui_update(context)

        if navigation_passthrough(event, wheel=False):
            self.passthrough = True

            return {'PASS_THROUGH'}

        elif self.cut['end'] and event.type in ['SPACE', 'LEFTMOUSE', 'TAB']:
            self.finish(context)

            self.reset_viewmx(context)

            self.is_tab_finish = event.type == 'TAB'

            self.active_cutter = event.type == 'LEFTMOUSE' and not self.is_tab_finish

            return self.execute(context)

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            self.finish(context)

            self.reset_viewmx(context)

            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def finish(self, context):
        finish_modal_handlers(self)

        self.S_on_active.finish()
        self.S_on_others.finish()

        restore_gizmos(self)

        finish_status(self)

        if self.has_switched_to_ortho:
            context.space_data.region_3d.view_perspective = 'PERSP'

    def invoke(self, context, event):
        self.init_settings(props=['apply_boolean'])
        self.load_settings()

        self.active = context.active_object
        self.mx = self.active.matrix_world
        self.origin = self.mx.to_translation()

        self.bbox = get_bbox(self.active.data)

        if not any(self.bbox[2]):
            self.bbox = get_eval_bbox(self.active, advanced=True)

        mods = [mod for mod in self.active.modifiers if mod.show_viewport and ((mod.type == 'MIRROR' and mod.mirror_object) or is_array(mod))]

        for mod in mods:
            mod.show_viewport= False

        self.dg = context.evaluated_depsgraph_get()

        self.bm = bmesh.new()
        self.bm.from_mesh(get_eval_mesh(self.dg, self.active, data_block=False))  # no need for the data block

        self.bm.normal_update()
        self.bm.verts.ensure_lookup_table()
        self.bm.faces.ensure_lookup_table()

        for mod in mods:
            mod.show_viewport = True

        self.face_index = None
        self.flip_width = False

        self.is_depth_limiting = False
        self.is_width_limiting = False

        self.limit_init_loc = None
        self.pre_limit_viewmx = None
        self.pre_limit_mousepos = None

        self.cut = {'draw_origin': None,      # draw origin, to define the draw plane
                    'draw_normal': None,      # draw normal, to define the draw plane
                    'start': None,            # start point of the cut, placed on the draw plane
                    'end': None,              # end point of the cut, also on the draw plane
                    'mid': None,              # center between both

                    'vector': None,           # vector between start and end point
                    'direction': None,        # orthogonal vector, determining the width of the cut and influenced by self.flip prop

                    'depths': None,           # max depth vectors
                    'depth_limit': 1,         # default depth limit, full depth
                    'width': None,            # width vector
                    'width_limit': 1}         # default width limit, full width
        self.coords = {
            'cut_line': [],
            'cut_stripes': [],

            'draw_plane': [],

            'depth_plane': [],
            'depth_lines': [],
            'depth_limit_line': [],

            'depth_lazy_plane': [],
            'depth_lazy_line': [],

            'width_plane': [],
            'width_limit_line': [],

            'verts': transform_coords([v.co[:] for v in self.bm.verts], self.mx),

            'snap': [],
            'extended_snap': [],
            'connected_snap': []}

        self.init_viewmx = None
        self.has_switched_to_ortho = False
        self.is_backside_drawing = False

        self.is_snapping = False
        self.is_snapping_on_others = False
        self.snap_target = None
        self.snap_obj_name = ''
        self.snap_dir = None

        update_mod_keys(self)

        self.S_on_active = Snap(context, include=[self.active], debug=False)
        self.S_on_others = Snap(context, exclude=[self.active], exclude_wire=True, debug=False)

        self.factor = get_zoom_factor(context, context.scene.cursor.location, scale=300, ignore_obj_scale=True)

        cmx = context.scene.cursor.matrix
        self.cursor_origin, self.cursor_rotation, _ = cmx.decompose()

        self.cursor_x_dir = self.cursor_rotation @ Vector((1, 0, 0)) * self.factor
        self.cursor_y_dir = self.cursor_rotation @ Vector((0, 1, 0)) * self.factor
        self.cursor_z_dir = self.cursor_rotation @ Vector((0, 0, 1)) * self.factor

        hide_gizmos(self, context)

        get_mouse_pos(self, context, event)

        self.init_draw_mode(context, debug=False)

        if self.is_cursor:
            self.set_draw_plane_from_cursor(context)

        elif self.is_bbox:
            self.set_draw_plane_from_bbox(context)

        else:
            self.set_draw_plane_from_face(context)

        init_status(self, context, func=draw_hyper_cut_status(self))

        init_modal_handlers(self, context, hud=True, view3d=True)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        dg = context.evaluated_depsgraph_get()

        active = context.active_object

        cutter, mod = self.hypercut(context, active, debug=False)

        facecount = self.validate_facecount(context, dg, active, cutter, mod, debug=False)

        if self.minimize_cutter:
            self.minimize(dg, active, cutter, facecount, debug=False)

        if self.mode == 'SPLIT' and not self.lazy_split:
            split = setup_split_boolean(context, mod)

            active_dup = split['dup']['host']
            cutter_dup = split['dup']['cutter']
            mod_dup = split['dup']['mod']

        else:
            active_dup = cutter_dup = mod_dup = None

        bpy.ops.object.select_all(action='DESELECT')

        if self.apply_boolean:
            self.apply_boolean_mod(context, active, cutter, mod, active_dup, mod_dup)

        if self.active_cutter and not self.apply_boolean:

            if self.mode == 'SPLIT' and not self.lazy_split:
                cutter_dup.select_set(True)
                context.view_layer.objects.active = cutter_dup
            else:
                cutter.select_set(True)
                context.view_layer.objects.active = cutter
        else:

            if self.mode == 'SPLIT' and not self.lazy_split:
                active_dup.select_set(True)
                context.view_layer.objects.active = active_dup

            else:
                active.select_set(True)
                context.view_layer.objects.active = active

            if not self.apply_boolean:
                cutter.hide_set(True)

                if self.mode == 'SPLIT' and not self.lazy_split:
                    cutter_dup.hide_set(True)

        force_ui_update(context)

        if self.apply_boolean:
            force_geo_gizmo_update(context)

        self.save_settings()

        if self.is_tab_finish:
            bpy.ops.machin3.hyper_modifier('INVOKE_DEFAULT', is_gizmo_invocation=False, is_button_invocation=False, mode='PICK')

        return {'FINISHED'}

    def init_draw_mode(self, context, debug=False):
        self.is_cursor = False
        self.is_bbox = False

        lastop = None
        faceindex = False

        ops = context.window_manager.operators

        if ops:
            lastop = ops[-1].bl_idname

        if lastop and any(lastop == bl_idname for bl_idname in ['MACHIN3_OT_transform_cursor']):
            self.is_cursor = True

        else:
            self.S_on_active.get_hit(self.mouse_pos)

            if not self.S_on_active.hit:
                self.is_bbox = True

        if debug:
            print()
            print("cursor:", self.is_cursor)
            print("  bbox:", self.is_bbox)
            print("  face:", faceindex)

    def set_draw_plane_from_face(self, context, debug=False):

        self.S_on_active.get_hit(self.mouse_pos)

        if self.active.name in self.S_on_active.cache.bmeshes:
            bm = self.S_on_active.cache.bmeshes[self.active.name]

            if self.S_on_active.hit:
                face = bm.faces[self.S_on_active.hitindex]

            else:
                coords = Vector((context.region.width / 2, context.region.height / 2))
                view_origin, view_dir = get_view_origin_and_dir(context, coords)

                faces = [(f, view_dir.dot(self.mx.to_3x3() @ f.normal), (self.mx @ f.calc_center_median() - view_origin).length) for f in bm.faces if view_dir.dot(self.mx.to_3x3() @ f.normal) < -0.5]

                if not faces:
                    faces = [(f, view_dir.dot(self.mx.to_3x3() @ f.normal), (self.mx @ f.calc_center_median() - view_origin).length) for f in bm.faces]

                face = min(faces, key=lambda x: (x[1], x[2]))[0]

            loop_triangles = self.S_on_active.cache.loop_triangles[self.active.name]

            self.coords['draw_plane'] = get_tri_coords(loop_triangles, [face])

            origin = self.mx @ face.calc_center_median()

            normal = get_world_space_normal(face.normal, self.mx)

            if debug:
                draw_point(origin, color=yellow, modal=False)
                draw_vector(normal, origin=origin, color=yellow, normal=False, modal=False)

            self.cut['draw_origin'] = origin
            self.cut['draw_normal'] = normal

            self.face_index = face.index

            force_ui_update(context)

            return True
        return False

    def set_draw_plane_from_bbox(self, context):
        xmin, xmax, ymin, ymax, zmin, zmax = self.bbox[1]

        faces = [(0, (ymin - ymax).normalized(), ymin),
                 (1, (xmax - xmin).normalized(), xmax),
                 (2, (ymax - ymin).normalized(), ymax),
                 (3, (xmin - xmax).normalized(), xmin),
                 (4, (zmax - zmin).normalized(), zmax),
                 (5, (zmin - zmax).normalized(), zmin)]

        coords = Vector((context.region.width / 2, context.region.height / 2))
        _, view_dir = get_view_origin_and_dir(context, coords)

        index, normal, origin = min(faces, key=lambda x: (view_dir.dot(self.mx.to_3x3() @ x[1]), self.mx @ x[2]))

        face_coords = [(self.bbox[0][0], self.bbox[0][1], self.bbox[0][5], self.bbox[0][4]),
                       (self.bbox[0][1], self.bbox[0][2], self.bbox[0][6], self.bbox[0][5]),
                       (self.bbox[0][2], self.bbox[0][3], self.bbox[0][7], self.bbox[0][6]),
                       (self.bbox[0][3], self.bbox[0][0], self.bbox[0][4], self.bbox[0][7]),
                       (self.bbox[0][4], self.bbox[0][5], self.bbox[0][6], self.bbox[0][7]),
                       (self.bbox[0][0], self.bbox[0][1], self.bbox[0][2], self.bbox[0][3])]

        cos = face_coords[index]
        self.coords['draw_plane'] = [cos[0], cos[1], cos[2], cos[0], cos[2], cos[3]]

        self.cut['draw_origin'] = self.mx @ origin
        self.cut['draw_normal'] = (self.mx.to_3x3() @ normal).normalized()

        if self.face_index is not None:
            self.face_index = None
            force_ui_update(context)

    def set_draw_plane_from_cursor(self, context, debug=False):
        loc = self.cursor_origin

        x = self.cursor_x_dir
        y = self.cursor_y_dir
        z = self.cursor_z_dir

        if self.cursor_x:
            draw_normal = x.normalized()
            self.coords['draw_plane'] = [loc - y - z, loc + y - z, loc + y + z, loc - y - z, loc + y + z, loc - y + z]

        elif self.cursor_y:
            draw_normal = y.normalized()
            self.coords['draw_plane'] = [loc - x - z, loc + x - z, loc + x + z, loc - x - z, loc + x + z, loc - x + z]

        elif self.cursor_z:
            draw_normal = z.normalized()
            self.coords['draw_plane'] = [loc - x - y, loc + x - y, loc + x + y, loc - x - y, loc + x + y, loc - x + y]

        if debug:
            draw_vector(draw_normal, origin=loc, color=normal, modal=False)

        self.cut['draw_origin'] = loc
        self.cut['draw_normal'] = draw_normal

        self.face_index = None
        force_ui_update(context)

    def update_cursor_plane_size(self, context):
        context.space_data.region_3d.update()

        self.factor = get_zoom_factor(context, context.scene.cursor.location, scale=300, ignore_obj_scale=True)

        self.cursor_x_dir = self.cursor_rotation @ Vector((1, 0, 0)) * self.factor
        self.cursor_y_dir = self.cursor_rotation @ Vector((0, 1, 0)) * self.factor
        self.cursor_z_dir = self.cursor_rotation @ Vector((0, 0, 1)) * self.factor

        self.set_draw_plane_from_cursor(context)

    def get_start_point(self, context):
        view_origin, view_dir = get_view_origin_and_dir(context, self.mouse_pos)

        self.cut['start'] = intersect_line_plane(view_origin, view_origin + view_dir, self.cut['draw_origin'], self.cut['draw_normal'])

    def get_end_point(self, context):
        view_origin, view_dir = get_view_origin_and_dir(context, self.mouse_pos)

        if self.is_snapping:

            if self.snap_dir:
                self.cut['end'] = self.get_projected_end_point_on_draw_plane(view_origin, view_dir)

            else:

                S = self.S_on_others if self.is_snapping_on_others else self.S_on_active

                S.get_hit(self.mouse_pos)

                if S.hit:

                    self.snap_dir = self.get_snap_dir_from_edge(S)

                    if self.snap_dir:
                        self.cut['end'] = self.get_projected_end_point_on_draw_plane(view_origin, view_dir)
                        self.snap_target = 'EDGE'

                    else:
                        self.cut['end'] = intersect_line_plane(view_origin, view_origin + view_dir, self.cut['draw_origin'], self.cut['draw_normal'])
                        self.snap_target = None

                elif self.is_bbox:
                    self.snap_dir, self.cut['end'] = self.get_snap_dir_from_bbox_border(view_origin, view_dir)
                    self.snap_target = 'BBOX'

                elif self.is_cursor:
                    self.snap_dir, self.cut['end'] = self.get_snap_dir_from_cursor_plane_border(view_origin, view_dir)
                    self.snap_target = 'CURSOR'

                else:
                    self.snap_dir = None
                    self.cut['end'] = intersect_line_plane(view_origin, view_origin + view_dir, self.cut['draw_origin'], self.cut['draw_normal'])
                    self.snap_target = None

            if self.cut['end'] and self.coords['snap']:
                self.get_additional_snap_coords(self.cut['end'])

        else:
            self.cut['end'] = intersect_line_plane(view_origin, view_origin + view_dir, self.cut['draw_origin'], self.cut['draw_normal'])

            if self.snap_target:
                self.snap_target = None

    def get_depth_vectors(self, debug=False):

        if debug:
            draw_point(self.cut['start'], color=yellow, modal=False)

        vectors = self.coords['verts'] - self.cut['start']

        distances = np.dot(vectors, -self.cut['draw_normal'])

        max_d = np.max(distances)

        min_d = np.abs(np.min(distances))

        depth = -self.cut['draw_normal'] * max_d
        neg_depth = self.cut['draw_normal'] * min_d

        if debug:
            draw_vector(depth, origin=self.cut['start'], color=yellow, fade=False, modal=False)
            draw_vector(neg_depth, origin=self.cut['start'], color=blue, fade=False, modal=False)

        self.cut['depths'] = (depth, neg_depth)

    def get_cut_vector(self, debug=False):
        self.cut['mid'] = get_center_between_points(self.cut['start'], self.cut['end'])

        self.cut['vector'] = (self.cut['end'] - self.cut['start']).normalized()

        if debug:
            draw_vector(self.cut['vector'], origin=self.cut['start'], color=red, modal=False)

    def get_cut_direction(self, debug=False):

        mid_origin_dir = self.origin - self.cut['mid']
        cross = mid_origin_dir.cross(self.cut['vector']).normalized()

        ortho = cross.cross((self.cut['vector'])).normalized()

        i = intersect_line_plane(self.cut['mid'] + ortho, self.cut['mid'] + ortho + self.cut['draw_normal'], self.cut['draw_origin'], self.cut['draw_normal'])

        if i:
            self.cut['direction'] = (i - self.cut['mid']).normalized()

            if self.flip_width:
                self.cut['direction'].negate()

            if debug:
                draw_vector(self.cut['direction'], origin=self.cut['mid'], color=blue, modal=False)

    def get_width_vector(self, debug=False):

        if debug:
            draw_point(self.cut['mid'], color=yellow, modal=False)
            draw_vector(self.cut['direction'], origin=self.cut['mid'], fade=True, modal=False)

        vectors = self.coords['verts'] - self.cut['mid']

        distances = np.dot(vectors, self.cut['direction'])

        max_d = np.max(distances)

        self.cut['width'] = self.cut['direction'] * max_d

    def get_width_and_depths(self):
        width =  self.cut['width'] * self.cut['width_limit'] if 0 < self.cut['width_limit'] < 1 else self.cut['width']
        depth = self.cut['depths'][0] * self.cut['depth_limit'] if 0 < self.cut['depth_limit'] < 1 else self.cut['depths'][0]
        neg_depth = Vector() if not self.is_cursor else self.cut['depths'][1] * self.cut['depth_limit'] if 0 < self.cut['depth_limit'] < 1 else self.cut['depths'][1]

        return width, depth, neg_depth

    def get_coords(self):

        width, depth, neg_depth = self.get_width_and_depths()

        self.coords['cut_line'] = [self.cut['start'], self.cut['end']]

        stripe_count = 5
        cut_vector = self.cut['end'] - self.cut['start']   # cut vector, but not normalized

        self.coords['cut_stripes'].clear()

        for i in range(stripe_count):
            factor = i  / (stripe_count - 1)
            self.coords['cut_stripes'].append((width, self.cut['start'] + (cut_vector * factor)))

        self.coords['width_plane'] = np.array([self.cut['start'], self.cut['end'], self.cut['end'] + width, self.cut['start'], self.cut['end'] + width, self.cut['start'] + width], dtype=np.float32)

        if self.is_width_limiting or 0 < self.cut['width_limit'] < 1:
            width_override = Vector() if self.is_width_limiting and self.cut['width_limit'] == 0 else width

            self.coords['width_limit_line'] = [self.cut['start'], self.cut['start'] + width_override, self.cut['end'] + width_override, self.cut['end']]

        if self.is_depth_limiting or 0 < self.cut['depth_limit'] < 1:

            self.coords['depth_plane'] = np.vstack((self.coords['width_plane'] + depth, self.coords['width_plane'] + neg_depth))

            self.coords['depth_lines'] = [self.cut['start'] + neg_depth, self.cut['start'] + depth,
                                          self.cut['end'] + neg_depth, self.cut['end'] + depth,
                                          self.cut['start'] + neg_depth + width, self.cut['start'] + depth + width,
                                          self.cut['end'] + neg_depth + width, self.cut['end'] + depth + width]

            self.coords['depth_lazy_plane'] = [self.cut['start'] + neg_depth, self.cut['start'] + depth, self.cut['end'] + neg_depth,
                                               self.cut['end'] + neg_depth, self.cut['start'] + depth, self.cut['end'] + depth]

            if self.is_depth_limiting and self.cut['depth_limit'] == 0:
                depth = neg_depth = Vector()

            base_line = np.array([self.cut['start'],
                                  self.cut['start'] + depth,
                                  self.cut['end'] + depth,
                                  self.cut['end'],

                                  self.cut['end'] + neg_depth,
                                  self.cut['end'] + neg_depth - cut_vector,
                                  self.cut['start']], dtype=np.float32)

            self.coords['depth_limit_line'] = np.float32(base_line + width)

            self.coords['depth_lazy_line'] = base_line

    def get_snap_dir_from_edge(self, SnapObject):
        hitmx = SnapObject.hitmx
        hitobj = SnapObject.hitobj
        hitlocation = SnapObject.hitlocation
        hitindex = SnapObject.hitindex
        bm = SnapObject.cache.bmeshes[hitobj.name]

        hit = hitmx.inverted_safe() @ hitlocation

        hitface = bm.faces[hitindex]

        edge = min([(e, (hit - intersect_point_line(hit, e.verts[0].co, e.verts[1].co)[0]).length, (hit - get_center_between_verts(*e.verts)).length) for e in hitface.edges if e.calc_length()], key=lambda x: (x[1] * x[2]) / x[0].calc_length())[0]

        edge_dir = hitmx.to_3x3() @ (edge.verts[0].co - edge.verts[1].co).normalized()

        if abs(edge_dir.dot(self.cut['draw_normal'])) > 0.999:
            self.coords['snap'] = []
            return None

        else:
            self.coords['snap'] = [hitmx @ v.co for v in edge.verts]
            self.snap_obj_name = hitobj.name
            return edge_dir

    def get_projected_end_point_on_draw_plane(self, view_origin, view_dir):
        end = intersect_line_plane(view_origin, view_origin + view_dir, self.cut['draw_origin'], self.cut['draw_normal'])

        if end is None:
            end = self.cut['end']

        snapped = intersect_point_line(end, self.cut['start'], self.cut['start'] + self.snap_dir)[0]

        return intersect_line_plane(snapped, snapped + self.cut['draw_normal'], self.cut['draw_origin'], self.cut['draw_normal'])

    def get_snap_dir_from_bbox_border(self, view_origin, view_dir):
        hit = self.mx.inverted_safe() @ intersect_line_plane(view_origin, view_origin + view_dir, self.cut['draw_origin'], self.cut['draw_normal'])

        bbox_edges = [(self.coords['draw_plane'][0], self.coords['draw_plane'][1]), (self.coords['draw_plane'][1], self.coords['draw_plane'][2]), (self.coords['draw_plane'][2], self.coords['draw_plane'][5]), (self.coords['draw_plane'][5], self.coords['draw_plane'][0])]

        edge = min([(e, (hit - intersect_point_line(hit, e[0], e[1])[0]).length, (hit - get_center_between_points(*e)).length) for e in bbox_edges], key=lambda x: (x[1] * x[2]) / (x[0][0] - x[0][1]).length)[0]

        edge_dir = self.mx.to_3x3() @ (edge[0] - edge[1]).normalized()

        self.coords['snap'] = [self.mx @ co for co in edge]

        end = intersect_line_plane(view_origin, view_origin + view_dir, self.cut['draw_origin'], self.cut['draw_normal'])

        snapped = intersect_point_line(end, self.cut['start'], self.cut['start'] + edge_dir)[0]

        return edge_dir, snapped

    def get_snap_dir_from_cursor_plane_border(self, view_origin, view_dir):
        hit = intersect_line_plane(view_origin, view_origin + view_dir, self.cut['draw_origin'], self.cut['draw_normal'])

        cursor_plane_edges = [(self.coords['draw_plane'][0], self.coords['draw_plane'][1]), (self.coords['draw_plane'][1], self.coords['draw_plane'][2]), (self.coords['draw_plane'][2], self.coords['draw_plane'][5]), (self.coords['draw_plane'][5], self.coords['draw_plane'][0])]

        edge = min([(e, (hit - intersect_point_line(hit, e[0], e[1])[0]).length, (hit - get_center_between_points(*e)).length) for e in cursor_plane_edges], key=lambda x: (x[1] * x[2]) / (x[0][0] - x[0][1]).length)[0]

        edge_dir = (edge[0] - edge[1]).normalized()

        self.coords['snap'] = edge

        end = intersect_line_plane(view_origin, view_origin + view_dir, self.cut['draw_origin'], self.cut['draw_normal'])

        snapped = intersect_point_line(end, self.cut['start'], self.cut['start'] + edge_dir)[0]

        return edge_dir, snapped

    def get_additional_snap_coords(self, end):

        projected_snap_co_1 = intersect_line_plane(self.coords['snap'][0], self.coords['snap'][0] - self.cut['draw_normal'], self.cut['draw_origin'], self.cut['draw_normal'])
        projected_snap_co_2 = intersect_line_plane(self.coords['snap'][1], self.coords['snap'][1] - self.cut['draw_normal'], self.cut['draw_origin'], self.cut['draw_normal'])

        start_parallel_co = intersect_point_line(self.cut['start'], projected_snap_co_1, projected_snap_co_2)[0]
        end_parallel_co = intersect_point_line(end, projected_snap_co_1, projected_snap_co_2)[0]

        start_reprojected_co = intersect_line_line(start_parallel_co, start_parallel_co + self.cut['draw_normal'], *self.coords['snap'])[0]
        end_reprojected_co = intersect_line_line(end_parallel_co, end_parallel_co + self.cut['draw_normal'], *self.coords['snap'])[0]
        self.coords['connected_snap'] = [self.cut['start'], start_parallel_co, start_parallel_co, start_reprojected_co, end, end_parallel_co, end_parallel_co, end_reprojected_co]

        extended_snap_line_1 = [start_reprojected_co, self.coords['snap'][0]]
        extended_snap_line_2 = [start_reprojected_co, self.coords['snap'][1]]
        extended_snap_line_5 = [start_reprojected_co, end_reprojected_co]
        extended_snap_line_3 = [end_reprojected_co, self.coords['snap'][0]]
        extended_snap_line_4 = [end_reprojected_co, self.coords['snap'][1]]

        longest = max([((line[1] - line[0]).length, line) for line in [extended_snap_line_1, extended_snap_line_2, extended_snap_line_3, extended_snap_line_4, extended_snap_line_5]], key=lambda x: x[0])
        self.coords['extended_snap'] = longest[1]

    def align_view_to_draw_plane(self, context, inverted=False, debug=False):
        normal = - self.cut['draw_normal'] if inverted else self.cut['draw_normal']

        loc = self.cut['draw_origin']
        rot = create_rotation_matrix_from_normal(self.active, normal)

        if debug:
            tangent = rot.col[0].xyz
            binormal = rot.col[1].xyz

            draw_point(self.cut['draw_origin'], modal=False)

            draw_vector(tangent, origin=self.cut['draw_origin'], color=red, modal=False)
            draw_vector(binormal, origin=self.cut['draw_origin'], color=green, modal=False)
            draw_vector(normal, origin=self.cut['draw_origin'], color=blue, modal=False)

        planemx = Matrix.LocRotScale(loc + normal, rot.to_3x3(), Vector((1, 1, 1)))

        space_data = context.space_data
        r3d = space_data.region_3d

        r3d.view_matrix = planemx.inverted_safe()

        if r3d.view_perspective == 'PERSP':
            r3d.view_perspective = 'ORTHO'

            self.has_switched_to_ortho = True

    def reset_viewmx(self, context):
        viewmx = self.init_viewmx if self.init_viewmx else self.pre_limit_viewmx if self.pre_limit_viewmx else None

        if viewmx:
            context.space_data.region_3d.view_matrix = viewmx

    def update_depth_limiting(self, context, value='PRESS'):
        def press():
            self.init_depth_limiting(context)

        def release():
            self.finish_depth_limiting(context)

        if value == 'PRESS':
            return press

        elif value == 'RELEASE':
            return release

    def init_depth_limiting(self, context, debug=False):

        self.is_depth_limiting = True

        self.pre_limit_mousepos = self.mouse_pos

        self.limit_init_loc = None

        self.depth_limit_init = self.cut['depth_limit']

        width, d1, d2 = self.get_width_and_depths()
        depth = d1 if d1.length > d2.length else d2

        pre_viewmx = context.space_data.region_3d.view_matrix.copy()

        self.pre_limit_viewmx = pre_viewmx

        pre_origin, pre_rot, _ = pre_viewmx.inverted_safe().decompose()

        pre_x = pre_rot @ Vector((1, 0, 0))
        pre_y = pre_rot @ Vector((0, 1, 0))
        pre_z = pre_rot @ Vector((0, 0, 1))

        if debug:
            draw_point(pre_origin, modal=False)

            draw_vector(pre_x, origin=pre_origin, color=red, modal=False)
            draw_vector(pre_y, origin=pre_origin, color=green, modal=False)
            draw_vector(pre_z, origin=pre_origin, color=blue, modal=False)

            draw_point(self.cut['mid'], modal=False)

        view_distance = (pre_origin - self.cut['mid']).length

        if depth.length > view_distance:
            view_distance = depth.length

        view_origin = self.cut['mid'] + (width + self.cut['direction'] * view_distance) + (depth / 2)

        view_z = self.cut['direction']

        coords = Vector((context.region.width / 2, context.region.height / 2))
        _, view_dir = get_view_origin_and_dir(context, coords)

        self.is_backside_drawing = view_dir.dot(self.cut['draw_normal']) > 0

        draw_normal = -self.cut['draw_normal'] if self.is_backside_drawing else self.cut['draw_normal']

        up_dot = draw_normal.dot(Vector((0, 0, 1)))

        if abs(up_dot) >= 0.95:

            cut_vec = self.cut['vector'].normalized()

            view_x = cut_vec if pre_x.dot(cut_vec) > 0 else -cut_vec

        else:

            view_x = -draw_normal if view_z.dot(pre_x) > 0 else draw_normal

        view_y = view_z.cross(view_x)

        if debug:
            draw_point(view_origin, color=yellow, modal=False)

            draw_vector(view_x, origin=view_origin, color=red, modal=False)
            draw_vector(view_z, origin=view_origin, color=blue, modal=False)

        rot = create_rotation_matrix_from_vectors(view_x, view_y, view_z)

        mx = Matrix.LocRotScale(view_origin, rot.to_3x3(), Vector((1, 1, 1)))

        if not debug:
            context.space_data.region_3d.view_matrix = mx.inverted_safe()

            context.space_data.region_3d.update()

        force_ui_update(context)

    def finish_depth_limiting(self, context):
        self.is_depth_limiting = False

        if self.pre_limit_mousepos:
            warp_mouse(self, context, self.pre_limit_mousepos)
            self.pre_limit_mousepos = None

        if self.pre_limit_viewmx:
            context.space_data.region_3d.view_matrix = self.pre_limit_viewmx
            self.pre_limit_viewmx = None

        if self.cut['depth_limit'] == 0:
            self.cut['depth_limit'] = 1

        force_ui_update(context)

    def adjust_depth_limit(self, context, event):
        if event.type  == 'MOUSEMOVE':
            get_mouse_pos(self, context, event)

            width = self.get_width_and_depths()[0]

            depth = self.cut['depths'][1 if self.is_backside_drawing else 0]
            depth_limited = depth * self.depth_limit_init

            view_origin, view_dir = get_view_origin_and_dir(context, self.mouse_pos)

            i = intersect_line_line(view_origin, view_origin + view_dir, self.cut['mid'] + width, self.cut['mid'] + depth + width)

            if i:
                loc = i[1]

                if self.limit_init_loc is None:
                    self.limit_init_loc = loc

                new_depth_limited = depth_limited + (loc - self.limit_init_loc)

                dot = new_depth_limited.normalized().dot(depth.normalized())

                if dot > 0:
                    factor = 1 if new_depth_limited.length >= depth.length else new_depth_limited.length / depth.length
                else:
                    factor = 0

                self.cut['depth_limit'] = factor

                self.get_coords()

                force_ui_update(context)

        elif event.type in alt and event.value == 'PRESS':
            self.limit_init_loc = None

            limit = max(0.01, 1 - self.cut['depth_limit'])

            self.cut['depth_limit'] = limit
            self.depth_limit_init = limit

            self.get_coords()

            force_ui_update(context)

        if navigation_passthrough(event, alt=False, wheel=False):
            self.passthrough = True

            return {'PASS_THROUGH'}

        elif event.type in ['SPACE', 'LEFTMOUSE', 'TAB']:
            self.finish(context)

            self.active_cutter = event.type == 'LEFTMOUSE'

            self.is_tab_finish = event.type == 'TAB'

            return self.execute(context)

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            self.finish(context)

            self.reset_viewmx(context)
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def update_width_limiting(self, context, value='PRESS'):
        def press():
            self.init_width_limiting(context)

        def release():
            self.finish_width_limiting(context)

        if value == 'PRESS':
            return press

        elif value == 'RELEASE':
            return release

    def init_width_limiting(self, context):
        self.is_width_limiting = True

        self.pre_limit_mousepos = self.mouse_pos

        self.limit_init_loc = None

        self.width_limit_init= self.cut['width_limit']

        force_ui_update(context)

    def finish_width_limiting(self, context):
        self.is_width_limiting = False

        if self.pre_limit_mousepos:
            warp_mouse(self, context, self.pre_limit_mousepos)
            self.pre_limit_mousepos = None

        if self.cut['width_limit'] == 0:
            self.cut['width_limit'] = 1

        force_ui_update(context)

    def adjust_width_limit(self, context, event):
        if event.type == 'MOUSEMOVE':
            get_mouse_pos(self, context, event)

            width = self.cut['width']
            width_limited = width * self.width_limit_init

            view_origin, view_dir = get_view_origin_and_dir(context, self.mouse_pos)

            i = intersect_line_line(view_origin, view_origin + view_dir, self.cut['end'], self.cut['end'] + width)

            if i:
                loc = i[1]

                if self.limit_init_loc is None:
                    self.limit_init_loc = loc

                new_width_limited = width_limited + (loc - self.limit_init_loc)

                dot = new_width_limited.normalized().dot(width.normalized())

                if dot > 0:
                    factor = 1 if new_width_limited.length > width.length else new_width_limited.length / width.length
                else:
                    factor = 0

                self.cut['width_limit'] = factor

                self.get_coords()

                force_ui_update(context)

        elif event.type in alt and event.value == 'PRESS':
            self.limit_init_loc = None

            limit = max(0.001, 1 - self.cut['width_limit'])

            self.cut['width_limit'] = limit
            self.width_limit_init = limit

            self.get_coords()

            force_ui_update(context)

        if navigation_passthrough(event, alt=False, wheel=False):
            self.passthrough = True

            return {'PASS_THROUGH'}

        elif event.type in ['SPACE', 'LEFTMOUSE', 'TAB']:
            self.finish(context)

            self.reset_viewmx(context)

            self.active_cutter = event.type == 'LEFTMOUSE'

            self.is_tab_finish = event.type == 'TAB'

            return self.execute(context)

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            self.finish(context)

            self.reset_viewmx(context)
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def hypercut(self, context, active, debug=False):
        def create_cutter(overshoot=0.01):

            start, end, vec, = self.cut['start'], self.cut['end'], self.cut['vector']
            width, depth, neg_depth = self.get_width_and_depths()

            if debug:
                draw_vector(vec, origin=start, color=yellow, modal=False)
                draw_vector(width, origin=end, color=blue, modal=False)

            if self.mode == 'SPLIT' and not lazy_split:
                width *= 1.005

                overshoot *= 20

            if debug:
                draw_vector(depth, origin=end, color=green, modal=False)
                draw_vector(neg_depth, origin=end, color=red, modal=False)

            if lazy_split:
                world_coords = [start + neg_depth, end + neg_depth,
                                start + depth, end + depth]

            else:
                world_coords = [start + neg_depth, end + neg_depth,
                                start + neg_depth + width, end + neg_depth + width,
                                start + depth, end + depth,
                                start + width + depth, end + width + depth]

            origin = average_locations(world_coords)

            if debug:
                draw_points(world_coords, modal=False)
                draw_point(origin, color=yellow, modal=False)

            axis_x = width.normalized()
            axis_y = vec.normalized()
            axis_z = depth.normalized()

            cross = axis_x.cross(axis_z)

            if cross.dot(axis_y) > 0:
                axis_y = - axis_y

            if debug:
                draw_vector(axis_x, origin=origin, color=red, modal=False)
                draw_vector(axis_y, origin=origin, color=green, modal=False)
                draw_vector(axis_z, origin=origin, color=blue, modal=False)

            loc = get_loc_matrix(origin)
            rot = create_rotation_matrix_from_vectors(axis_x, axis_y, axis_z)

            mx = loc @ rot

            cutter = bpy.data.objects.new(name='Hyper Cut', object_data=bpy.data.meshes.new(name='Hyper Cut'))

            bpy.context.scene.collection.objects.link(cutter)

            cutter.rotation_mode = 'QUATERNION'
            cutter.matrix_world = mx
            cutter.rotation_mode = 'XYZ'

            bm = bmesh.new()
            bm.from_mesh(cutter.data)

            verts = []

            for co in world_coords:
                verts.append(bm.verts.new(mx.inverted_safe() @ co))

            if lazy_split:
                indices = [0, 1, 3, 2]
                bm.faces.new([verts[i] for i in indices])

                offset = min([vec.length, depth.length]) * overshoot

                depth_dir = (verts[2].co - verts[0].co).normalized()

                for v in verts[0:2]:
                    v.co -= depth_dir * offset

                for v in verts[2:]:
                    v.co += depth_dir * offset

            else:
                indices = [(0, 1, 3, 2), (5, 4, 6, 7),
                           (1, 5, 7, 3), (4, 0, 2, 6),
                           (0, 4, 5, 1), (2, 3, 7, 6)]

                for ids in indices:
                    bm.faces.new([verts[i] for i in ids])

                offset = min([width.length, vec.length, depth.length]) * overshoot

                if self.mode == 'SPLIT':
                    offset *= 1.1

                if offset:
                    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

                    for v in verts:
                        v.co += v.normal * offset

            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

            edge_glayer, face_glayer = ensure_gizmo_layers(bm)

            for e in bm.edges:
                e[edge_glayer] = 1

            for f in bm.faces:
                f[face_glayer] = 1

            bm.to_mesh(cutter.data)
            bm.free()

            cutter.display_type = 'WIRE'
            hide_render(cutter, True)

            cutter.HC.ishyper = True
            cutter.HC.objtype = 'CUBE'

            return cutter

        lazy_split = self.mode == 'SPLIT' and self.lazy_split

        cutter = create_cutter()

        parent(cutter, active)

        indexed_name = get_new_mod_name(active, 'HYPERCUT')

        mod = add_boolean(active, cutter, method='DIFFERENCE', solver='MANIFOLD' if bpy.app.version >= (4, 5, 0) else 'FAST')
        mod.name = indexed_name

        if self.mode == 'SPLIT':
            if self.lazy_split:
                mod.name += " (Lazy Split)"
            else:
                mod.name += " (Split)"

        if lazy_split:

            min_dim = get_min_dim(self.active)
            thickness = min_dim / 333

            add_solidify(cutter, name="Shell", thickness=thickness, offset=0, even=True, high_quality=False)

        idx = sort_mod_after_split(mod)

        if idx is None:
            sort_modifiers(active, debug=False)

        return cutter, mod

    def validate_facecount(self, context, dg, active, cutter, mod, debug=False):
        dg.update()

        facecount = len(dg.objects[active.name].data.polygons)

        if debug:
            print("initial face count:", facecount)

        if facecount == 0:
            weld = active.modifiers.new(name='Weld', type='WELD')
            weld.show_expanded = False

            names = [mo.name for mo in active.modifiers if mo != weld and mo.type == 'WELD' and 'Weld' in mo.name]

            if names:
                maxidx = get_biggest_index_among_names(names)
                weld.name = f"- Weld.{str(maxidx + 1).zfill(3)}"
            else:
                weld.name = "- Weld"

            index = list(active.modifiers).index(mod)
            move_mod(weld, index=index)

            dg.update()
            facecount = len(dg.objects[active.name].data.polygons)

            if debug:
                print("initial (welded) face count:", facecount)

        return facecount

    def minimize(self, dg, active, cutter, facecount, debug=False):
        def push_face(first=True, step=0.1, reverse=False, debug=False):
            nonlocal height

            bm = bmesh.new()
            bm.from_mesh(cutter.data)
            bm.normal_update()
            bm.faces.ensure_lookup_table()

            if first:
                face = bm.faces[0]
            else:
                face = bm.faces[1]

            if debug:
                draw_point(face.calc_center_median(), mx=cutter.matrix_world, modal=False)

            for v in face.verts:
                move_edge = [e for e in v.link_edges if e not in face.edges][0]

                if height is None:
                    height = move_edge.calc_length()

                move_dir = (move_edge.other_vert(v).co - v.co).normalized()

                if reverse:
                    move_dir.negate()

                amount = height * step
                v.co = v.co + move_dir * amount

            if debug:
                draw_point(face.calc_center_median(), mx=cutter.matrix_world, color=yellow if reverse else white, modal=False)

            bm.to_mesh(cutter.data)
            bm.free()

        if debug:
            from time import time
            start = time()

        height = None
        step = 0.05

        new_facecount = facecount

        for state in [True, False]:
            if debug:
                print("front face") if state else print("back face")

            count = 0

            while facecount == new_facecount:
                count += 1

                if debug:
                    print(" count", count)

                push_face(first=state, step=step, debug=debug)

                dg.update()

                new_facecount = len(dg.objects[active.name].data.polygons)

                if debug:
                    print("  new face count:", new_facecount)

                if facecount != new_facecount:
                    if debug:
                        print("   reversing once")

                    push_face(first=state, step=step, reverse=True, debug=debug)

                    new_facecount = facecount
                    break

                if count >= 19:
                    if debug:
                        print("  aborting and resetting")
                    push_face(first=state, step=0.9, reverse=True, debug=debug)
                    break

        if debug:
            print("time:", time() - start)

    def apply_boolean_mod(self, context, active, cutter, mod, active_dup=None, mod_dup=None):
        def process_mesh(obj, redundant_angle=179.999, debug=False):
            bm = bmesh.new()
            bm.from_mesh(obj.data)
            bm.normal_update()

            edge_glayer, face_glayer = ensure_gizmo_layers(bm)

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

            if redundant_verts:
                if debug:
                    print(f"INFO: Removing {len(redundant_verts)} redundant vertices")

                bmesh.ops.dissolve_verts(bm, verts=redundant_verts)

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

        if meshmachine := HC.get_addon('MESHmachine'):
            MM = HC.addons['meshmachine']['module']
            MM.utils.stash.create_stash(active, mod.object)

        apply_mod(mod)

        if self.mode == 'SPLIT' and not self.lazy_split:

            if meshmachine:
                MM.utils.stash.create_stash(active_dup, mod_dup.object)

            apply_mod(mod_dup)

        process_mesh(active, debug=False)

        if self.mode == 'SPLIT' and not self.lazy_split:
            process_mesh(active_dup, debug=False)

        bpy.data.meshes.remove(cutter.data, do_unlink=True)
