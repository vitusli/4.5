import bpy
from bpy_extras.view3d_utils import region_2d_to_vector_3d
import bmesh

from math import ceil, radians, sqrt
from mathutils import Matrix, Vector

from .. import HyperCursorManager as HC

from .. operators.add import PipeGizmoManager
from .. operators.bend import HyperBendGizmoManager
from .. operators.bevel import HyperBevelGizmoManager, PickHyperBevelGizmoManager
from .. operators.edit_face import CurveSurfaceGizmoManager
from .. operators.modifier import RemoveUnusedBooleanGizmoManager
from .. operators.object import PickObjectTreeGizmoManager

from .. utils.bmesh import ensure_gizmo_layers, ensure_select_layers, ensure_edge_glayer
from .. utils.cursor import set_cursor_2d
from .. utils.curve import get_curve_as_dict, verify_curve_data
from .. utils.gizmo import is_modal, create_button_gizmo, offset_button_gizmo, geometry_gizmo_poll, object_gizmo_poll, objects_gizmo_poll
from .. utils.math import average_locations, get_face_center, get_loc_matrix, create_rotation_matrix_from_vector, get_rot_matrix, get_sca_matrix, get_center_between_verts, get_world_space_normal, tween
from .. utils.mesh import get_bbox, get_mesh_user_count
from .. utils.modifier import displace_poll, boolean_poll, hyper_array_poll, solidify_poll, source_poll
from .. utils.object import get_eval_bbox, is_decalmachine_object, is_plug_handle, is_valid_object
from .. utils.registration import get_prefs
from .. utils.tools import get_active_tool
from .. utils.ui import is_on_screen, warp_mouse
from .. utils.view import get_view_bbox
from .. utils.workspace import get_assetbrowser_area

from .. colors import white, yellow, red, blue, light_blue, light_yellow, green, light_green
from .. shapes import ring, stem

force_obj_gizmo_update = False
force_objs_gizmo_update = False
force_geo_gizmo_update = False
force_pick_hyper_bevels_gizmo_update = False

class Gizmo2DRing(bpy.types.Gizmo):
    bl_idname = "MACHIN3_GT_2d_ring"

    def draw(self, context):
        self.draw_custom_shape(self.shape)

    def draw_select(self, context, select_id):
        self.draw_custom_shape(self.shape, select_id=select_id)

    def setup(self):
        self.draw_options = {}
        self.view_offset = (0, 0)
        self.shape = self.new_custom_shape('TRIS', ring)

class Gizmo3DStem(bpy.types.Gizmo):
    bl_idname = "MACHIN3_GT_3d_stem"

    def draw(self, context):
        self.draw_custom_shape(self.shape)

    def draw_select(self, context, select_id):
        self.draw_custom_shape(self.shape, select_id=select_id)

    def setup(self):
        self.shape = self.new_custom_shape('TRIS', stem)

def get_hyper_cursor_button_map(context):
    def set_HUD_offsets():
        offset = HC.props['HUD_offset']

        if rows:
            y_hud = (total_height / 2) + gap - 6
            x_hud = sqrt(pow(radius, 2) - pow(y_hud, 2)) - 6

        else:
            x_hud = radius
            y_hud = 12

        offset['right'] = Vector((x_hud, y_hud)) * gizmo_size * ui_scale

        offset['left'] = Vector((-radius, 12)) * gizmo_size * ui_scale
        offset['top'] = Vector((0, radius)) * gizmo_size * ui_scale

    hc = context.scene.HC

    gizmo_size = context.preferences.view.gizmo_size / 75
    ui_scale = context.preferences.system.ui_scale

    map = {'ADD_HISTORY': (0, 0),
           'REMOVE_HISTORY': (0, 0),
           'DRAW_HISTORY': (0, 0),
           'FOCUS': (0, 0),
           'SETTINGS': (0, 0),
           'POINT_CURSOR': (0, 0),
           'CAST_CURSOR': (0, 0),
           'ADD_CUBE': (0, 0),
           'ADD_CYLINDER': (0, 0),
           'ADD_ASSET': (0, 0)}

    rows = []

    if hc.show_button_history:
        rows.append(['ADD_HISTORY', 'REMOVE_HISTORY', 'DRAW_HISTORY'])

    if hc.show_button_focus:
        rows.append(['FOCUS'])

        if hc.show_button_settings:
            rows[-1].append('SETTINGS')

    elif hc.show_button_settings:
        rows.append(['SETTINGS'])

    if hc.show_button_cast:
        rows.append(['POINT_CURSOR', 'CAST_CURSOR'])

    if hc.show_button_object:
        rows.append(['ADD_CUBE', 'ADD_CYLINDER', 'ADD_ASSET'])

    gap = 22
    radius = 95
    total_height = gap * (len(rows) - 1)

    for ridx, row in enumerate(rows):

        y = - ridx * gap + (total_height / 2)

        for cidx, button in enumerate(row):

            x = sqrt(pow(radius, 2) - pow(y, 2)) + cidx * gap

            if button == 'DRAW_HISTORY':
                x += 7

            map[button] = (x * gizmo_size, y * gizmo_size)

    set_HUD_offsets()

    return map

class GizmoGroupHyperCursor(bpy.types.GizmoGroup):
    bl_idname = "MACHIN3_GGT_hyper_cursor"
    bl_label = "Hyper Cursor Gizmo"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'3D'}

    is_full_array = False

    @classmethod
    def poll(cls, context):
        view = context.space_data

        if view.overlay.show_overlays:
            if get_active_tool(context).idname == 'machin3.tool_hyper_cursor':
                hc = context.scene.HC

                return hc.show_gizmos and hc.draw_HUD

    def setup(self, context):
        self.button_map = get_hyper_cursor_button_map(context)

        self.create_gizmos(context)

    def refresh(self, context):
        if not is_modal(self):
            self.button_map = get_hyper_cursor_button_map(context)

    def draw_prepare(self, context):
        def toggle_scale_visibility(context):
            active = context.active_object

            if context.mode == 'EDIT_MESH':

                if active and active.type == 'MESH' and active.select_get() and active.HC.ishyper:
                    bm = bmesh.from_edit_mesh(active.data)
                    bm.normal_update()
                    bm.verts.ensure_lookup_table()

                    verts = [v for v in bm.verts if v.select]

                    if verts:
                        for gzm in [self.scale_x, self.scale_y, self.scale_z]:
                            gzm.hide = False
                        return

                for gzm in [self.scale_x, self.scale_y, self.scale_z]:
                    gzm.hide = True

            elif context.mode == 'OBJECT':
                if active and active.type == 'MESH' and active.select_get() and active.HC.ishyper and len(active.data.polygons) < active.HC.geometry_gizmos_show_limit:
                    for gzm in [self.scale_x, self.scale_y, self.scale_z]:
                        gzm.hide = False

                else:
                    for gzm in [self.scale_x, self.scale_y, self.scale_z]:
                        gzm.hide = True

        if is_modal(self):
            for gzm in self.gizmos:
                if gzm.is_modal:
                    if gzm.bl_idname == "GIZMO_GT_dial_3d":
                        gzm.line_width = 1

                        if self.is_full_array:
                            gzm.arc_inner_factor = 0.9
                            gzm.draw_options = {'CLIP'}

                        else:
                            gzm.arc_inner_factor = 0.4
                            gzm.draw_options = {'ANGLE_VALUE'}

                else:
                    gzm.hide = True

        else:

            for gzm in self.gizmos:
                gzm.hide = False

                if gzm.bl_idname == "GIZMO_GT_dial_3d":
                    gzm.draw_options = {'CLIP'}
                    gzm.line_width = 2
                    gzm.arc_inner_factor = 0

            set_cursor_2d(context)

            self.drag.matrix_basis = context.scene.cursor.matrix

            HC.props['gizmo_scale'] = self.drag.matrix_world.to_scale()[0]

            self.rot_x.matrix_basis = context.scene.cursor.matrix @ self.get_gizmo_rotation_matrix('X')
            self.rot_y.matrix_basis = context.scene.cursor.matrix @ self.get_gizmo_rotation_matrix('Y')
            self.rot_z.matrix_basis = context.scene.cursor.matrix

            self.move_x.matrix_basis = context.scene.cursor.matrix @ self.get_gizmo_rotation_matrix('X')
            self.move_y.matrix_basis = context.scene.cursor.matrix @ self.get_gizmo_rotation_matrix('Y')
            self.move_z.matrix_basis = context.scene.cursor.matrix

            self.scale_x.matrix_basis = context.scene.cursor.matrix @ self.get_gizmo_rotation_matrix('X')
            self.scale_y.matrix_basis = context.scene.cursor.matrix @ self.get_gizmo_rotation_matrix('Y')
            self.scale_z.matrix_basis = context.scene.cursor.matrix

            toggle_scale_visibility(context)

            hc = context.scene.HC
            offset = self.button_map

            for gzm, type in self.button_gzms:
                offset_button_gizmo(context, gzm, offset[type])

            self.add_history.hide = not hc.show_button_history
            self.remove_history.hide = self.draw_history.hide = True if not hc.historyCOL or not hc.show_button_history else False

            self.proximity.hide = not hc.show_button_focus
            self.settings.hide = not hc.show_button_settings

            self.cast.hide = self.point.hide = not hc.show_button_cast

            if context.mode == 'OBJECT':

                self.add_cube.hide = self.add_cylinder.hide = self.add_asset.hide = not hc.show_button_object

                if not self.add_asset.hide:
                    self.add_asset.hide = not get_assetbrowser_area(context)

            for gzm, type in self.button_gzms:
                if not gzm.hide:
                    gzm.scale_basis = self.get_gizmo_size(type, gzm)

    def get_gizmo_rotation_matrix(self, axis):
        if axis == 'X':
            return Matrix.Rotation(radians(90), 4, 'Y')

        if axis == 'Y':
            return Matrix.Rotation(radians(-90), 4, 'X')

        elif axis == 'Z':
            return Matrix()

    def get_gizmo_size(self, type='GENERAL', gzm=None):
        if type == 'DRAW_HISTORY':
            size = 0.08
        else:
            size = 0.1

        if gzm and gzm.is_highlight:
            size *= 1.25

        return size

    def create_gizmos(self, context):
        self.gizmos.clear()
        self.create_transform_gizmos(context)
        self.create_button_gizmos(context)

    def create_transform_gizmos(self, context):

        self.drag = self.create_drag_gizmo(context)

        self.rot_x = self.create_rotation_gizmo(context, axis='X')
        self.rot_y = self.create_rotation_gizmo(context, axis='Y')
        self.rot_z = self.create_rotation_gizmo(context, axis='Z')

        self.move_x = self.create_translation_gizmo(context, axis='X')
        self.move_y = self.create_translation_gizmo(context, axis='Y')
        self.move_z = self.create_translation_gizmo(context, axis='Z')

        self.scale_x = self.create_scale_gizmo(context, axis='X')
        self.scale_y = self.create_scale_gizmo(context, axis='Y')
        self.scale_z = self.create_scale_gizmo(context, axis='Z')

    def create_button_gizmos(self, context):
        offset = self.button_map
        self.button_gzms = []

        self.add_history = create_button_gizmo(self, context, 'machin3.call_hyper_cursor_operator', args={'idname': 'change_cursor_history', 'desc': 'Add current Cursor State to History', 'args': "{'mode': 'ADD'}"}, icon='RADIOBUT_OFF', scale=self.get_gizmo_size('ADD_HISTORY'), offset=offset['ADD_HISTORY'])
        self.remove_history = create_button_gizmo(self, context, 'machin3.call_hyper_cursor_operator', args={'idname': 'change_cursor_history', 'desc': 'Remove current Cursor State from History', 'args': "{'mode': 'REMOVE', 'index': -1}"}, icon='X', scale=self.get_gizmo_size('REMOV_HISTORY'), offset=offset['REMOVE_HISTORY'])

        self.draw_history = create_button_gizmo(self, context, 'machin3.call_hyper_cursor_operator', args={'idname': 'TOGGLE_HISTORY_DRAWING', 'desc': 'Toggle History Drawing'}, icon='CURSOR', scale=self.get_gizmo_size('DRAW_HISTORY'), offset=offset['DRAW_HISTORY'])

        self.proximity = create_button_gizmo(self, context, 'machin3.focus_proximity', args={'is_button_invocation': False, 'gizmoinvoke': True}, icon='HIDE_OFF', scale=self.get_gizmo_size('FOCUS'), offset=offset['FOCUS'])
        self.settings = create_button_gizmo(self, context, 'machin3.hyper_cursor_settings', icon='WORDWRAP_ON', scale=self.get_gizmo_size('SETTINGS'), offset=offset['SETTINGS'])

        self.cast = create_button_gizmo(self, context, 'machin3.cast_cursor', args={'is_button_invocation': False}, icon='PARTICLES', scale=self.get_gizmo_size('CAST_CURSOR'), offset=offset['CAST_CURSOR'])
        self.point = create_button_gizmo(self, context, 'machin3.point_cursor', args={'instant': False}, icon='SNAP_NORMAL', scale=self.get_gizmo_size('POINT_CURSOR'), offset=offset['POINT_CURSOR'])

        self.button_gzms.extend([(self.add_history, 'ADD_HISTORY'), (self.remove_history, 'REMOVE_HISTORY'), (self.draw_history, 'DRAW_HISTORY'), (self.proximity, 'FOCUS'), (self.settings, 'SETTINGS'), (self.cast, 'CAST_CURSOR'), (self.point, 'POINT_CURSOR')])

        if context.mode == 'OBJECT':
            self.add_cube = create_button_gizmo(self, context, 'machin3.add_object_at_cursor', args={'type': 'CUBE', 'is_drop': False}, icon='MESH_CUBE', scale=self.get_gizmo_size('ADD_CUBE'), offset=offset['ADD_CUBE'])
            self.add_cylinder = create_button_gizmo(self, context, 'machin3.add_object_at_cursor', args={'type': 'CYLINDER', 'is_drop': False}, icon='MESH_CYLINDER', scale=self.get_gizmo_size('ADD_CYLINDER'), offset=offset['ADD_CYLINDER'])
            self.add_asset = create_button_gizmo(self, context, 'machin3.add_object_at_cursor', args={'type': 'ASSET', 'is_drop': False}, icon='MESH_MONKEY', scale=self.get_gizmo_size('ADD_ASSET'), offset=offset['ADD_ASSET'])

            self.button_gzms.extend([(self.add_cube, 'ADD_CUBE'), (self.add_cylinder, 'ADD_CYLINDER'), (self.add_asset, 'ADD_ASSET')])

    def create_translation_gizmo(self, context, axis='Z', offset=0.5, scale=1.4, length=0, alpha=0.3, alpha_highlight=1, hover=False):
        gzm = self.gizmos.new("GIZMO_GT_arrow_3d")

        op = gzm.target_set_operator("machin3.transform_cursor")
        op.mode = 'TRANSLATE'
        op.is_cursor_pie_invocation = False
        op.axis = axis

        gzm.matrix_basis = context.scene.cursor.matrix @ self.get_gizmo_rotation_matrix(axis)
        gzm.matrix_offset = Matrix.Translation((0, 0, offset))

        gzm.draw_style = 'NORMAL'
        gzm.use_draw_offset_scale = True
        gzm.use_draw_modal = False
        gzm.use_draw_hover = hover

        gzm.length = length
        gzm.scale_basis = scale

        gzm.color = (1, 0.3, 0.3) if axis == 'X' else (0.3, 1, 0.3) if axis == 'Y' else (0.3, 0.3, 1)
        gzm.alpha = alpha
        gzm.color_highlight = (1, 0.5, 0.5) if axis == 'X' else (0.5, 1, 0.5) if axis == 'Y' else (0.5, 0.5, 1)
        gzm.alpha_highlight = alpha_highlight

        return gzm

    def create_rotation_gizmo(self, context, axis='Z', scale=0.6, line_width=2, alpha=0.3, alpha_highlight=1, hover=False):
        gzm = self.gizmos.new("GIZMO_GT_dial_3d")

        op = gzm.target_set_operator("machin3.transform_cursor")
        op.mode = 'ROTATE'
        op.is_cursor_pie_invocation = False
        op.axis = axis

        gzm.matrix_basis = context.scene.cursor.matrix @ self.get_gizmo_rotation_matrix(axis)

        gzm.draw_options = {'CLIP'}
        gzm.use_draw_value = True
        gzm.use_draw_hover = hover
        gzm.use_grab_cursor = True

        gzm.line_width = line_width
        gzm.scale_basis = scale

        gzm.color = (1, 0.3, 0.3) if axis == 'X' else (0.3, 1, 0.3) if axis == 'Y' else (0.3, 0.3, 1)
        gzm.alpha = alpha
        gzm.color_highlight = (1, 0.5, 0.5) if axis == 'X' else (0.5, 1, 0.5) if axis == 'Y' else (0.5, 0.5, 1)
        gzm.alpha_highlight = alpha_highlight

        return gzm

    def create_drag_gizmo(self, context, scale=0.4, color=(1, 1, 1), alpha=0.05, color_highlight=(0, 0, 0), alpha_highlight=0.5, hover=True):
        gzm = self.gizmos.new("GIZMO_GT_move_3d")

        op = gzm.target_set_operator("machin3.transform_cursor")
        op.mode = 'DRAG'
        op.is_cursor_pie_invocation = False

        gzm.matrix_basis = context.scene.cursor.matrix

        gzm.draw_style = 'RING_2D'
        gzm.draw_options = {'FILL', 'ALIGN_VIEW'}

        gzm.scale_basis = scale

        gzm.use_draw_hover = hover

        gzm.color = color
        gzm.alpha = alpha
        gzm.color_highlight = color_highlight
        gzm.alpha_highlight = alpha_highlight

        return gzm

    def create_scale_gizmo(self, context, axis='X', offset=-0.8, scale=1.0, length=0, alpha=0.3, alpha_highlight=1, hover=False):
        gzm = self.gizmos.new("GIZMO_GT_arrow_3d")

        op = gzm.target_set_operator("machin3.scale_mesh")
        op.direction = 'XMIN' if axis == 'X' else 'YMIN' if axis == 'Y' else 'ZMIN'
        op.cursor_space_rotation = True

        gzm.matrix_basis = context.scene.cursor.matrix @ self.get_gizmo_rotation_matrix(axis)
        gzm.matrix_offset = Matrix.Translation((0, 0, offset))

        gzm.draw_style = 'BOX'
        gzm.use_draw_offset_scale = True
        gzm.use_draw_modal = True
        gzm.use_draw_hover = hover

        gzm.length = length
        gzm.scale_basis = scale

        gzm.color = (1, 0.3, 0.3) if axis == 'X' else (0.3, 1, 0.3) if axis == 'Y' else (0.3, 0.3, 1)
        gzm.alpha = alpha
        gzm.color_highlight = (1, 0.5, 0.5) if axis == 'X' else (0.5, 1, 0.5) if axis == 'Y' else (0.5, 0.5, 1)
        gzm.alpha_highlight = alpha_highlight

        return gzm

class GizmoGroupHyperCursorSimple(bpy.types.GizmoGroup):
    bl_idname = "MACHIN3_GGT_hyper_cursor_simple"
    bl_label = "Hyper Cursor Simple Gizmo"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'3D'}

    @classmethod
    def poll(cls, context):
        view = context.space_data

        if view.overlay.show_overlays:
            if get_active_tool(context).idname == 'machin3.tool_hyper_cursor_simple':
                hc = context.scene.HC

                return hc.show_gizmos and hc.draw_HUD

    def setup(self, context):
        self.active = context.active_object

        self.drag = self.create_drag_gizmo(context)

    def draw_prepare(self, context):
        self.drag.matrix_basis = context.scene.cursor.matrix

        HC.props['gizmo_scale'] = self.drag.matrix_world.to_scale()[0] * 2

        set_cursor_2d(context)

    def create_drag_gizmo(self, context, scale=0.2, color=(1, 1, 1), alpha=0.05, color_highlight=(0, 0, 0), alpha_highlight=0.5, hover=True):
        gzm = self.gizmos.new("GIZMO_GT_move_3d")

        op = gzm.target_set_operator("machin3.transform_cursor")
        op.mode = 'DRAG'
        op.is_cursor_pie_invocation = False

        gzm.matrix_basis = context.scene.cursor.matrix

        gzm.draw_style = 'RING_2D'
        gzm.draw_options = {'FILL', 'ALIGN_VIEW'}

        gzm.scale_basis = scale

        gzm.use_draw_hover = hover

        gzm.color = color
        gzm.alpha = alpha
        gzm.color_highlight = color_highlight
        gzm.alpha_highlight = alpha_highlight

        return gzm

class GizmoGroupHyperCursorEditGeometry(bpy.types.GizmoGroup):
    bl_idname = "MACHIN3_GGT_hyper_cursor_edit_geometry"
    bl_label = "Edit Geometry"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'3D', 'SCALE', 'PERSISTENT'}

    obj = None
    size = 0.2

    @classmethod
    def poll(cls, context):
        view = context.space_data

        if view.overlay.show_overlays:
            if context.mode == 'OBJECT':
                if get_active_tool(context).idname in ['machin3.tool_hyper_cursor', 'machin3.tool_hyper_cursor_simple']:
                    return geometry_gizmo_poll(context, mode='EDIT')

    def setup(self, context):
        self.obj = context.active_object

        self.face_gizmos, self.edge_gizmos = self.create_face_and_edge_gizmos(context, size=self.size)

        self.states = self.get_states(context)

    def refresh(self, context):

        if not is_modal(self):

            if self.is_state_change(context):
                self.gizmos.clear()
                self.obj = context.active_object

                if self.obj and not self.gizmos:
                    self.face_gizmos, self.edge_gizmos = self.create_face_and_edge_gizmos(context, size=self.size)

    def draw_prepare(self, context):

        if is_modal(self):

            for gzm in self.gizmos:
                gzm.hide = not gzm.is_modal

        else:
            if self.is_state_change(context):
                self.gizmos.clear()
                self.obj = context.active_object

                if self.obj and not self.gizmos:
                    self.face_gizmos, self.edge_gizmos = self.create_face_and_edge_gizmos(context, size=self.size)

                else:
                    return

            if self.obj:
                view_dir = region_2d_to_vector_3d(context.region, context.region_data, (context.region.width / 2, context.region.height / 2))

                is_xray = context.scene.HC.gizmo_xray
                is_wire = self.obj.display_type in ['WIRE', 'BOUNDS']

                for gzm, normals, selected in self.edge_gizmos:

                    if not is_wire:
                        dots = [n.dot(view_dir) for n in normals]
                        is_obscured = any([d > 0.0001 for d in dots])

                        if is_xray:
                            gzm.hide = False

                            if selected:
                                gzm.alpha = 0.2 if is_obscured else 0.3
                            else:
                                gzm.alpha = 0.01 if is_obscured else 0.05

                            gzm.alpha_highlight = 0.1 if is_obscured else 0.5

                        else:
                            gzm.hide = is_obscured

                for gzm, normal, gzmtype, _, selected, scale in self.face_gizmos:
                    dot = normal.dot(view_dir)

                    is_obscured = dot > 0.0001
                    is_facing = abs(dot) > 0.9999

                    if gzmtype == 'SCALE':
                        if gzm.is_highlight and scale == gzm.scale_basis:
                            gzm.scale_basis = 1.3 * scale
                        elif not gzm.is_highlight and scale != gzm.scale_basis:
                            gzm.scale_basis = scale

                    elif gzmtype == 'PUSH':
                        if gzm.is_highlight and scale == gzm.scale_basis:
                            gzm.scale_basis = 1.1 * scale
                            gzm.line_width = 8
                        elif not gzm.is_highlight and scale != gzm.scale_basis:
                            gzm.scale_basis = scale
                            gzm.line_width = 1

                    if not is_wire:

                        if is_xray:
                            gzm.hide = False

                            if selected:
                                gzm.alpha = 0.2 if is_obscured else 0.3
                            else:
                                gzm.alpha = 0.02 if is_obscured else 0.1

                            gzm.alpha_highlight = 0.2 if is_obscured else 1

                        else:
                            gzm.hide = is_obscured
                            gzm.alpha = 0.3 if selected else 0.1
                            gzm.alpha_highlight = 0.2 if is_obscured else 1

                    if gzmtype == 'PUSH':
                        if is_facing and not gzm.hide:
                            gzm.hide = True

                        elif not is_facing and gzm.hide:
                            if is_wire or is_xray:
                                gzm.hide = False

                            else:
                                gzm.hide = is_obscured

    def get_states(self, context):
        states = [active := context.active_object]

        if active:
            if is_valid_object(active):
                from .. handlers import mode_history, event_history

                states.append(active.type)                                # obj type
                states.append(active.select_get())                        # selection
                states.append(active.visible_get())                       # visibility
                states.append(get_prefs().geometry_gizmos_scale)          # gizmo scale (prefs)
                states.append(active.HC.geometry_gizmos_scale)            # gizmo scale (obj prop)
                states.append(active.HC.geometry_gizmos_edit_mode)        # gizmo edit mode
                states.append(active.HC.geometry_gizmos_edge_thickness)   # gizmo edge thickness
                states.append(active.HC.geometry_gizmos_face_tween)       # gizmo face tween
                states.append(active.display_type)                        # display type
                states.append(len(active.data.vertices))                  # vert count
                states.append(len(active.data.edges))                     # edge count
                states.append(len(active.data.polygons))                  # face count
                states.append(active.data.library)                        # linked mesh
                states.append(active.matrix_world.copy())                 # world matrix
                states.append(mode_history)                               # mode history
                states.append(event_history)                              # event history (undo/redo)

        return states

    def is_state_change(self, context, debug=False):
        global force_geo_gizmo_update

        if force_geo_gizmo_update:
            force_geo_gizmo_update = False

            if debug:
                print()
                print("  Edit Geometry Gizmo forced update!!")
                print()
            return True

        if (states := self.get_states(context)) != self.states:
            if debug:
                print()
                print("  Edit Geometry Gizmo state has changed!!")
                print("    from:", self.states)
                print("      to:", states)
                print()

            self.states = states
            return True

        return False

    def create_face_and_edge_gizmos(self, context, size=0.2):
        mx = self.obj.matrix_world

        scale_mx = get_sca_matrix(mx.decompose()[2])

        edge_thickness = self.obj.HC.geometry_gizmos_edge_thickness

        face_tween = self.obj.HC.geometry_gizmos_face_tween

        ui_scale = context.preferences.system.ui_scale

        gizmo_size = context.preferences.view.gizmo_size / 75

        gizmo_scale_prefs = get_prefs().geometry_gizmos_scale
        gizmo_scale_obj = self.obj.HC.geometry_gizmos_scale

        gizmo_scale = gizmo_scale_prefs * gizmo_scale_obj

        _, _, dims = get_bbox(self.obj.data)
        mesh_dim = sum([abs(d) for d in get_sca_matrix(mx.to_scale()) @ dims]) / 3

        if self.obj.HC.objtype == 'CYLINDER':
            mesh_density = 1

        else:
            mesh_density = 10 * pow(0.8, 0.3 * (len(self.obj.data.polygons) + 35)) + 0.4

        bm = bmesh.new()
        bm.from_mesh(self.obj.data)

        edge_glayer, face_glayer = ensure_gizmo_layers(bm)
        edge_slayer, face_slayer = ensure_select_layers(bm)

        edge_gizmos = []

        edges = [e for e in bm.edges if e[edge_glayer] == 1]

        for e in edges:
            e_dir = mx.to_3x3() @ (e.verts[1].co - e.verts[0].co)

            loc = get_loc_matrix(mx @ get_center_between_verts(*e.verts))
            rot = create_rotation_matrix_from_vector(e_dir.normalized())
            sca = get_sca_matrix(Vector((1, 1, (e_dir.length) / (size * mesh_dim * mesh_density * ui_scale * gizmo_scale * gizmo_size * edge_thickness))))

            gzm = self.gizmos.new("MACHIN3_GT_3d_stem")
            op = gzm.target_set_operator("machin3.call_hyper_cursor_pie")
            op.idname = 'MACHIN3_MT_edit_edge'
            op.index = e.index

            gzm.matrix_basis = loc @ rot @ sca
            gzm.scale_basis = size * mesh_dim * mesh_density * gizmo_scale * gizmo_size * edge_thickness

            selected = e[edge_slayer] == 1 if edge_slayer else False

            gzm.color = (0.5, 1, 0.5) if selected == 1 else (1, 1, 1)
            gzm.alpha = 0.3 if selected == 1 else 0.05
            gzm.color_highlight = (1, 0.5, 0.5)
            gzm.alpha_highlight = 0.5

            edge_gizmos.append((gzm, [get_world_space_normal(f.normal, mx) for f in e.link_faces], selected))

        face_gizmos = []

        faces = [f for f in bm.faces if f[face_glayer] == 1]

        for face in faces:

            loc = get_loc_matrix(mx @ get_face_center(face, method='PROJECTED_BOUNDS'))

            rot = create_rotation_matrix_from_vector(get_world_space_normal(face.normal, mx))
            face_dim = (scale_mx @ Vector((sqrt(face.calc_area()), 0, 0))).length * 1.3

            face_size = tween(mesh_dim * mesh_density, face_dim, face_tween)

            gzm = self.gizmos.new("MACHIN3_GT_2d_ring")

            op = gzm.target_set_operator("machin3.call_hyper_cursor_pie")
            op.idname = 'MACHIN3_MT_edit_face'
            op.index = face.index

            gzm.matrix_basis = loc @ rot
            gzm.scale_basis = size * gizmo_size * gizmo_scale * 0.18 * face_size

            selected = face[face_slayer] == 1 if face_slayer else False

            gzm.color = (0.5, 1, 0.5) if selected == 1 else (1, 1, 1)
            gzm.alpha = 0.3 if selected == 1 else 0.05
            gzm.color_highlight = (1, 0.5, 0.5)
            gzm.alpha_highlight = 1

            face_gizmos.append((gzm, get_world_space_normal(face.normal, mx), 'SCALE', face.index, selected, gzm.scale_basis))

            gzm = self.gizmos.new("GIZMO_GT_arrow_3d")

            op = gzm.target_set_operator("machin3.push_face")
            op.index = face.index

            gzm.matrix_basis = loc @ rot
            gzm.scale_basis = size * gizmo_size * gizmo_scale * face_size

            gzm.draw_style = 'NORMAL'
            gzm.length = 0.1

            gzm.color = (1, 1, 1)
            gzm.alpha = 0.1
            gzm.color_highlight = (1, 0.5, 0.5)
            gzm.alpha_highlight = 1

            face_gizmos.append((gzm, get_world_space_normal(face.normal, mx), 'PUSH', face.index, False, gzm.scale_basis))

        return face_gizmos, edge_gizmos

class GizmoGroupHyperCursorScaleGeometry(bpy.types.GizmoGroup):
    bl_idname = "MACHIN3_GGT_hyper_cursor_scale_geometry"
    bl_label = "Scale Geometry"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'3D', 'SCALE', 'PERSISTENT'}

    obj = None
    size = 0.2

    @classmethod
    def poll(cls, context):
        view = context.space_data

        if view.overlay.show_overlays:
            if context.mode == 'OBJECT':
                if get_active_tool(context).idname in ['machin3.tool_hyper_cursor', 'machin3.tool_hyper_cursor_simple']:
                    return geometry_gizmo_poll(context, mode='SCALE')

    def setup(self, context):
        self.obj = context.active_object

        self.scale_gizmos = self.create_scale_gizmos(context, size=self.size)

        self.states = self.get_states(context)

    def refresh(self, context):
        if not is_modal(self):

            if self.is_state_change(context):
                self.gizmos.clear()
                self.obj = context.active_object

                if self.obj and not self.gizmos:
                    self.scale_gizmos = self.create_scale_gizmos(context, size=self.size)

    def draw_prepare(self, context):
        if is_modal(self):
            for gzm in self.gizmos:
                if not gzm.is_modal:
                    gzm.hide = True
        else:
            if self.is_state_change(context):
                self.gizmos.clear()
                self.obj = context.active_object

                if self.obj and not self.gizmos:
                    self.scale_gizmos = self.create_scale_gizmos(context, size=self.size)

                else:
                    return

            if self.obj:
                view_dir = region_2d_to_vector_3d(context.region, context.region_data, (context.region.width / 2, context.region.height / 2))

                is_xray = context.scene.HC.gizmo_xray
                is_wire = self.obj.display_type in ['WIRE', 'BOUNDS']

                for gzm, normal, scale in self.scale_gizmos:
                    dot = normal.dot(view_dir)

                    is_obscured = dot > 0.0001
                    is_facing = abs(dot) > 0.9999

                    if gzm.is_highlight:
                        gzm.scale_basis = 1.1 * scale
                        gzm.line_width = 8

                    elif not gzm.is_highlight:
                        gzm.scale_basis = scale
                        gzm.line_width = 1

                    if not is_wire:

                        if is_xray:
                            gzm.hide = False
                            gzm.alpha = 0.02 if is_obscured else 0.1
                            gzm.alpha_highlight = 0.2 if is_obscured else 1

                        else:
                            gzm.hide = is_obscured
                            gzm.alpha = 0.1
                            gzm.alpha_highlight = 1

                    if is_facing and not gzm.hide:
                        gzm.hide = True

                    elif not is_facing and gzm.hide:
                        if is_wire or is_xray:
                            gzm.hide = False
                        else:
                            gzm.hide = is_obscured

    def get_states(self, context):
        states = [active := context.active_object]

        if active:
            if is_valid_object(active):
                from .. handlers import mode_history, event_history

                states.append(active.type)                                # obj type
                states.append(active.select_get())                        # selection
                states.append(active.visible_get())                       # visibility
                states.append(active.HC.geometry_gizmos_edit_mode)        # gizmo edit mode
                states.append(active.display_type)                        # display type
                states.append(len(active.data.vertices))                  # vert count
                states.append(len(active.data.edges))                     # edge count
                states.append(len(active.data.polygons))                  # face count
                states.append(active.data.library)                        # linked mesh
                states.append(active.matrix_world.copy())                 # world matrix
                states.append(mode_history)                               # mode history
                states.append(event_history)                              # event history (undo/redo)

        return states

    def is_state_change(self, context, debug=False):
        global force_geo_gizmo_update

        if force_geo_gizmo_update:
            force_geo_gizmo_update = False

            if debug:
                print()
                print("  Edit Geometry Gizmo forced update!!")
                print()
            return True

        if (states := self.get_states(context)) != self.states:
            if debug:
                print()
                print("  Edit Geometry Gizmo state has changed!!")
                print("    from:", self.states)
                print("      to:", states)
                print()

            self.states = states
            return True

        return False

    def create_scale_gizmos(self, context, size=0.2):
        mx = self.obj.matrix_world

        bbox, centers, dims = get_bbox(self.obj.data)
        dim = sum([d for d in get_sca_matrix(mx.to_scale()) @ dims]) / 3

        xmin = centers[0]
        xmax = centers[1]
        ymin = centers[2]
        ymax = centers[3]
        zmin = centers[4]
        zmax = centers[5]

        scale_gizmos = []

        loc = get_loc_matrix(mx @ xmin)
        normal = (xmin - xmax).normalized()
        rot = create_rotation_matrix_from_vector(mx.to_quaternion() @ normal)

        self.xmin, scale = self.create_mesh_scale_gizmo(context, 'XMIN', mx, loc, rot, size, dim, length=0.1, color=(1, 1, 1), alpha=0.1, color_highlight=(1, 0.5, 0.5), alpha_highlight=1)
        scale_gizmos.append((self.xmin, mx.to_quaternion() @ normal, scale))

        loc = get_loc_matrix(mx @ xmax)
        normal = (xmax - xmin).normalized()
        rot = create_rotation_matrix_from_vector(mx.to_quaternion() @ normal)

        self.xmax, scale = self.create_mesh_scale_gizmo(context, 'XMAX', mx, loc, rot, size, dim, length=0.1, color=(1, 1, 1), alpha=0.1, color_highlight=(1, 0.5, 0.5), alpha_highlight=1)
        scale_gizmos.append((self.xmax, mx.to_quaternion() @ normal, scale))

        loc = get_loc_matrix(mx @ ymin)
        normal = (ymin - ymax).normalized()
        rot = create_rotation_matrix_from_vector(mx.to_quaternion() @ normal)

        self.ymin, scale = self.create_mesh_scale_gizmo(context, 'YMIN', mx, loc, rot, size, dim, length=0.1, color=(1, 1, 1), alpha=0.1, color_highlight=(1, 0.5, 0.5), alpha_highlight=1)
        scale_gizmos.append((self.ymin, mx.to_quaternion() @ normal, scale))

        loc = get_loc_matrix(mx @ ymax)
        normal = (ymax - ymin).normalized()
        rot = create_rotation_matrix_from_vector(mx.to_quaternion() @ normal)

        self.ymax, scale = self.create_mesh_scale_gizmo(context, 'YMAX', mx, loc, rot, size, dim, length=0.1, color=(1, 1, 1), alpha=0.1, color_highlight=(1, 0.5, 0.5), alpha_highlight=1)
        scale_gizmos.append((self.ymax, mx.to_quaternion() @ normal, scale))

        loc = get_loc_matrix(mx @ zmin)
        normal = (zmin - zmax).normalized()
        rot = create_rotation_matrix_from_vector(mx.to_quaternion() @ normal)

        self.zmin, scale = self.create_mesh_scale_gizmo(context, 'ZMIN', mx, loc, rot, size, dim, length=0.1, color=(1, 1, 1), alpha=0.1, color_highlight=(1, 0.5, 0.5), alpha_highlight=1)
        scale_gizmos.append((self.zmin, mx.to_quaternion() @ normal, scale))

        loc = get_loc_matrix(mx @ zmax)
        normal = (zmax - zmin).normalized()
        rot = create_rotation_matrix_from_vector(mx.to_quaternion() @ normal)

        self.zmax, scale = self.create_mesh_scale_gizmo(context, 'ZMAX', mx, loc, rot, size, dim, length=0.1, color=(1, 1, 1), alpha=0.1, color_highlight=(1, 0.5, 0.5), alpha_highlight=1)
        scale_gizmos.append((self.zmax, mx.to_quaternion() @ normal, scale))

        return scale_gizmos

    def create_mesh_scale_gizmo(self, context, direction, mx, loc, rot, size, dim, length=0.1, color=(1, 1, 1), alpha=0.1, color_highlight=(1, 0.5, 0.5), alpha_highlight=1):
        gzm = self.gizmos.new("GIZMO_GT_arrow_3d")

        op = gzm.target_set_operator("machin3.scale_mesh")
        op.direction = direction
        op.cursor_space_rotation = False

        gzm.matrix_basis = loc @ rot
        gzm.scale_basis = size * dim
        gzm.length = length

        gzm.draw_style = 'BOX'
        gzm.color = color
        gzm.alpha = alpha
        gzm.color_highlight = color_highlight
        gzm.alpha_highlight = alpha_highlight

        return gzm, size * dim

class GizmoGroupHyperCursorObject(bpy.types.GizmoGroup):
    bl_idname = "MACHIN3_GGT_hyper_cursor_object"
    bl_label = "Object"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'PERSISTENT', '3D'}

    @classmethod
    def poll(cls, context):
        view = context.space_data

        if view.overlay.show_overlays:
            if context.mode == 'OBJECT':
                if get_active_tool(context).idname in ['machin3.tool_hyper_cursor', 'machin3.tool_hyper_cursor_simple']:
                    return object_gizmo_poll(context)

    def setup(self, context):
        HC.get_addon('MACHIN3tools')
        HC.get_addon('MESHmachine')

        self.obj = context.active_object

        self.create_object_gizmos(context)

        self.states = self.get_states(context)

    def refresh(self, context):

        if self.is_state_change(context):
            self.gizmos.clear()
            self.obj = context.active_object

            if self.obj and not self.gizmos:
                self.create_object_gizmos(context)

    def draw_prepare(self, context):

        if self.is_state_change(context):
            self.gizmos.clear()
            self.obj = context.active_object

            if self.obj and not self.gizmos:
                self.create_object_gizmos(context)

            else:
                return

        if self.obj:
            gizmo_size = context.preferences.view.gizmo_size / 75

            if is_modal(self):
                for gzm in self.gizmos:
                    gzm.hide = True

            else:
                for gzm in self.gizmos:
                    gzm.hide = False

                corners = self.get_view_bbox_corners(context)

                offset = Vector((10, 10)) * gizmo_size

                offset_button_gizmo(context, self.objmenu_gzm, offset=offset, loc2d=corners['TOP_RIGHT'])

                if self.parented_gzm:
                    offset_button_gizmo(context, self.parented_gzm, offset=offset + Vector((25, 0)) * gizmo_size, loc2d=corners['TOP_RIGHT'])

                if self.instanced_gzm:
                    offset_button_gizmo(context, self.instanced_gzm, offset=offset + Vector((50 if self.parented_gzm else 25, 0)) * gizmo_size, loc2d=corners['TOP_RIGHT'])

                offset -= Vector((0, 25)) * gizmo_size

                if self.geogzm_setup_gzm:
                    offset_button_gizmo(context, self.geogzm_setup_gzm, offset=offset, loc2d=corners['TOP_RIGHT'])

                offset = Vector((10, -10)) * gizmo_size

                show_reflect_gizmo = (get_prefs().show_machin3tools_mirror_gizmo and HC.get_addon('MACHIN3tools')) or (self.obj.type == 'MESH' and not self.obj.data.library and get_prefs().show_meshmachine_symmetrize_gizmo and HC.get_addon('MESHmachine'))

                if show_reflect_gizmo:
                    offset_button_gizmo(context, self.reflect_gzm, offset=offset, loc2d=corners['BOTTOM_RIGHT'])

                    if self.hypermod_gzm:
                        offset_button_gizmo(context, self.hypermod_gzm, offset=offset + Vector((25, 0)) * gizmo_size, loc2d=corners['BOTTOM_RIGHT'])

                    offset += Vector((0, 25)) * gizmo_size

                elif self.hypermod_gzm:
                    offset_button_gizmo(context, self.hypermod_gzm, offset=offset, loc2d=corners['BOTTOM_RIGHT'])
                    offset += Vector((0, 25)) * gizmo_size

                if self.cylinder_gzm:
                    offset_button_gizmo(context, self.cylinder_gzm, offset=offset, loc2d=corners['BOTTOM_RIGHT'])
                    offset += Vector((0, 25)) * gizmo_size

                if self.pipe_gzm:
                    offset_button_gizmo(context, self.pipe_gzm, offset=offset, loc2d=corners['BOTTOM_RIGHT'])
                    offset += Vector((0, 25)) * gizmo_size

                if self.shell_gzm:
                    offset_button_gizmo(context, self.shell_gzm, offset=offset, loc2d=corners['BOTTOM_RIGHT'])
                    offset += Vector((0, 25)) * gizmo_size

                if self.displace_gzm:
                    offset_button_gizmo(context, self.displace_gzm, offset=offset, loc2d=corners['BOTTOM_RIGHT'])
                    offset += Vector((0, 25)) * gizmo_size

                if self.array_gzm:
                    offset_button_gizmo(context, self.array_gzm, offset=offset, loc2d=corners['BOTTOM_RIGHT'])
                    offset += Vector((0, 25)) * gizmo_size

                for gzm, type in self.gzms:
                    if not gzm.hide:
                        gzm.scale_basis = self.get_gizmo_size(type, gzm)

    def get_states(self, context):
        states = [active := context.active_object]

        if active:
            if is_valid_object(active):
                from .. handlers import mode_history, event_history

                states.append(active.type)                 # obj type, so you can watch curve to mesh conversion for instance
                states.append(active.select_get())         # selection state
                states.append(active.visible_get())        # visibility state
                states.append(active.parent)               # parent state
                states.append(len(active.modifiers))       # modifier count
                states.append(active.data.users)           # instance count
                states.append(active.library)              # linked object

                if active.data:
                    states.append(active.data.library)     # linked mesh

                states.append(mode_history)                # mode history
                states.append(event_history)               # event history (undo/redo)

                states.append(get_prefs().show_machin3tools_mirror_gizmo)
                states.append(get_prefs().show_meshmachine_symmetrize_gizmo)
                states.append(get_prefs().show_hypermod_gizmo)

        return states

    def is_state_change(self, context, debug=False):
        global force_obj_gizmo_update

        if force_obj_gizmo_update:
            force_obj_gizmo_update = False

            if debug:
                print()
                print("  Object button Gizmo forced update!!")
                print()
            return True

        if (states := self.get_states(context)) != self.states:
            if debug:
                print()
                print("  Object Button Gizmo state has changed!!")
                print("    from:", self.states)
                print("      to:", states)
                print()

            self.states = states
            return True

        return False

    def get_view_bbox_corners(self, context):
        eval_bbox = get_eval_bbox(self.obj)
        view_bbox = get_view_bbox(context, [self.obj.matrix_world @ co for co in eval_bbox])

        corner_dict = {'BOTTOM_LEFT': view_bbox[0],
                       'BOTTOM_RIGHT': view_bbox[1],
                       'BOTTOM_CENTER': Vector((round((view_bbox[0].x + view_bbox[1].x) / 2), view_bbox[0].y)),
                       'TOP_RIGHT': view_bbox[2],
                       'TOP_LEFT': view_bbox[3]}

        return corner_dict

    def get_gizmo_size(self, type='GENERAL', gzm=None):
        if type == 'INSTANCED':
            size = 0.09

        else:
            size = 0.1

        if gzm and gzm.is_highlight:
            size *= 1.25

        return size

    def is_non_manifold(self):
        if self.obj.type == 'MESH':
            bm = bmesh.new()
            bm.from_mesh(self.obj.data)

            is_non_manifold = any([not e.is_manifold for e in bm.edges])

            bm.free()

            return is_non_manifold and self.obj.data.polygons
        return False

    def has_displace(self, context):
        if displace_poll(context, self.obj):
            return True

        intersect_booleans = [mod for mod in boolean_poll(context, self.obj) if 'Split' in mod.name and mod.operation == 'INTERSECT']

        for mod in intersect_booleans:
            if displace_poll(context, obj=mod.object):
                return True

        if (host := self.obj.parent) and (gap_booleans := [mod for mod in boolean_poll(context, host) if 'Gap' in mod.name and mod.operation == 'DIFFERENCE']):
            gap_children = [obj for obj in self.obj.children_recursive if obj.name in context.scene.objects]

            if gap_children:
                if any([mod.object in gap_children and displace_poll(context, mod.object) for mod in gap_booleans]):
                    return True

        return False

    def create_object_gizmos(self, context):

        machin3tools = HC.get_addon('MACHIN3tools')
        meshmachine = HC.get_addon('MESHmachine')

        self.gizmos.clear()
        self.gzms = []

        self.objmenu_gzm = create_button_gizmo(self, context, 'machin3.hyper_cursor_object', icon='OBJECT_DATA', location=self.obj.location, scale=self.get_gizmo_size())
        self.gzms.append((self.objmenu_gzm, 'OBJMENU'))

        if self.obj.parent:
            self.parented_gzm = create_button_gizmo(self, context, 'machin3.unparent', icon='CON_CHILDOF', location=self.obj.location, scale=self.get_gizmo_size('PARENTED'))
            self.gzms.append((self.parented_gzm, 'PARENTED'))
        else:
            self.parented_gzm = None

        if self.obj.type == 'MESH' and get_mesh_user_count(self.obj.data) > 1:
            self.instanced_gzm = create_button_gizmo(self, context, 'machin3.unlink', icon='LINKED', location=self.obj.location, scale=self.get_gizmo_size('INSTANCED'))
            self.gzms.append((self.instanced_gzm, 'INSTANCED'))
        else:
            self.instanced_gzm = None

        if self.obj.type == 'MESH' and not self.obj.HC.ishyperbevel and not source_poll(context, self.obj) and not self.obj.data.library:
            self.geogzm_setup_gzm = create_button_gizmo(self, context, 'machin3.geogzm_setup', icon='MOD_EDGESPLIT', location=self.obj.location, scale=self.get_gizmo_size())
            self.gzms.append((self.geogzm_setup_gzm, 'GEOGZM_SETUP'))
        else:
            self.geogzm_setup_gzm = None

        if (machin3tools and get_prefs().show_machin3tools_mirror_gizmo) or (meshmachine and get_prefs().show_meshmachine_symmetrize_gizmo and self.obj.type == 'MESH' and not self.obj.data.library):
            self.reflect_gzm = create_button_gizmo(self, context, 'machin3.reflect', icon='MOD_MIRROR', location=self.obj.location, scale=self.get_gizmo_size())
            self.gzms.append((self.reflect_gzm, 'REFLECT'))
        else:
            self.reflect_gzm = None

        if get_prefs().show_hypermod_gizmo and self.obj.type == 'MESH':
            self.hypermod_gzm = create_button_gizmo(self, context, 'machin3.hyper_modifier', args={'is_gizmo_invocation': True, 'is_button_invocation': False}, icon='MODIFIER_DATA', location=self.obj.location, scale=self.get_gizmo_size())
            self.gzms.append((self.hypermod_gzm, 'HYPERMOD'))
        else:
            self.hypermod_gzm = None

        if self.obj.type == 'MESH' and self.obj.HC.objtype == 'CYLINDER':
            self.cylinder_gzm = create_button_gizmo(self, context, 'machin3.adjust_cylinder', icon='MESH_CYLINDER', location=self.obj.location, scale=self.get_gizmo_size())
            self.gzms.append((self.cylinder_gzm, 'CYLINDER'))
        else:
            self.cylinder_gzm = None

        if self.obj.type == 'CURVE' and (splines := self.obj.data.splines) and splines[0].type in ['POLY', 'NURBS']:
            self.pipe_gzm = create_button_gizmo(self, context, 'machin3.adjust_pipe', args={'is_profile_drop': False}, icon='META_CAPSULE', location=self.obj.location, scale=self.get_gizmo_size())
            self.gzms.append((self.pipe_gzm, 'PIPE'))
        else:
            self.pipe_gzm = None

        self.is_shell = solidify_poll(context) or self.is_non_manifold()

        if self.is_shell:
            self.shell_gzm = create_button_gizmo(self, context, 'machin3.adjust_shell', args={'is_hypermod_invocation': False}, icon='SNAP_OFF', location=self.obj.location, scale=self.get_gizmo_size())
            self.gzms.append((self.shell_gzm, 'SHELL'))
        else:
            self.shell_gzm = None

        self.is_displace = self.has_displace(context)

        if self.is_displace:
            self.displace_gzm = create_button_gizmo(self, context, 'machin3.adjust_displace', args={'is_hypermod_invocation': False}, icon='FULLSCREEN_EXIT', location=self.obj.location, scale=self.get_gizmo_size())
            self.gzms.append((self.displace_gzm, 'DISPLACE'))
        else:
            self.displace_gzm = None

        self.is_array = bool(hyper_array_poll(context))

        if self.is_array:
            self.array_gzm = create_button_gizmo(self, context, 'machin3.adjust_array', args={'is_hypermod_invocation': False}, icon='MOD_ARRAY', location=self.obj.location, scale=self.get_gizmo_size())
            self.gzms.append((self.array_gzm, 'ARRAY'))
        else:
            self.array_gzm = None

def get_objects_button_map(self, context):
    gizmo_size = context.preferences.view.gizmo_size / 75

    map = {'HYPE': (0, 0),
           'PARENTED': (0, 0),
           'INSTANCED': (0, 0),
           'HYPERBOOL': (0, 0) }

    count = len(self.gzms)
    row_count = int(ceil(sqrt(count)))

    rows = []

    for idx, (gzm, type) in enumerate(self.gzms):

        if idx % row_count:
            rows[-1].append(type)

        else:
            rows.append([type])

    gap = 22
    total_height = gap * (len(rows) - 1)

    for ridx, row in enumerate(rows):
        y = - ridx * gap + (total_height / 2)

        row_width = gap * (len(row) - 1)

        for cidx, button in enumerate(row):
            x = cidx * gap - (row_width / 2)

            map[button] = (x * gizmo_size, y * gizmo_size)

    return map

class GizmoGroupHyperCursorObjects(bpy.types.GizmoGroup):
    bl_idname = "MACHIN3_GGT_hyper_cursor_objects"
    bl_label = "Objects"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'PERSISTENT', '3D'}

    @classmethod
    def poll(cls, context):
        view = context.space_data

        if view.overlay.show_overlays:
            if context.mode == 'OBJECT':
                if get_active_tool(context).idname in ['machin3.tool_hyper_cursor', 'machin3.tool_hyper_cursor_simple']:
                    return objects_gizmo_poll(context)

    def setup(self, context):
        self.get_objects(context)

        self.create_objects_gizmos(context)
        self.button_map = get_objects_button_map(self, context)

        self.states = self.get_states(context)

    def refresh(self, context):
        if self.is_state_change(context):
            self.gizmos.clear()

            self.get_objects(context)

            if self.objects and not self.gizmos:
                self.create_objects_gizmos(context)
                self.button_map = get_objects_button_map(self, context)

    def draw_prepare(self, context):
        if self.is_state_change(context):
            self.gizmos.clear()

            self.get_objects(context)

            if self.objects and not self.gizmos:
                self.create_objects_gizmos(context)
                self.button_map = get_objects_button_map(self, context)

            else:
                return

        if self.objects and self.gzms:

            if is_modal(self):
                for gzm in self.gizmos:
                    gzm.hide = True

            else:
                for gzm in self.gizmos:
                    gzm.hide = False

                center = self.get_view_selection_center(context)

                offset = self.button_map

                for gzm, type in self.gzms:
                    offset_button_gizmo(context, gzm, offset=offset[type], loc2d=center)

                for gzm, type in self.gzms:
                    if not gzm.hide:
                        gzm.scale_basis = self.get_gizmo_size(type, gzm)

    def get_objects(self, context):
        self.objects = [obj for obj in context.selected_objects if obj.visible_get() and not (is_decalmachine_object(obj) or is_plug_handle(obj)) and not (obj.library or (obj.data and obj.data.library))]
        self.mesh_objects = [obj for obj in self.objects if obj.type == 'MESH']

        return self.objects

    def get_states(self, context):
        objects = self.get_objects(context)
        active = context.active_object if context.active_object in objects else None

        states = [objects, active]

        if objects:
            states.append([obj.type for obj in objects])             # obj types should be watched as we want them stay MESHes
            states.append([obj.select_get() for obj in objects])     # selection states
            states.append([obj.visible_get() for obj in objects])    # visibility states
            states.append(len(set(obj.data for obj in objects)))     # unique mesh count among selected objects

        return states

    def is_state_change(self, context, debug=False):
        global force_objs_gizmo_update

        if force_objs_gizmo_update:
            force_objs_gizmo_update = False

            if debug:
                print()
                print("  Object button Gizmo forced update!!")
                print()
            return True

        if (states := self.get_states(context)) != self.states:
            if debug:
                print()
                print("  Object Button Gizmo state has changed!!")
                print("    from:", self.states)
                print("      to:", states)
                print()

            self.states = states
            return True

        return False

    def get_view_selection_center(self, context):
        co2ds = [average_locations(get_view_bbox(context, [obj.matrix_world @ co for co in bbox]), size=2) for obj in self.objects if (bbox := get_eval_bbox(obj))]
        on_screen = [co2d for co2d in co2ds if is_on_screen(context, co2d)]

        if on_screen:
            center = average_locations(on_screen, size=2)

        else:
            center = Vector((context.region.width / 2, context.region.height / 2))

        return center

    def get_gizmo_size(self, type='GENERAL', gzm=None):
        if type == 'INSTANCED':
            size = 0.09

        else:
            size = 0.1

        if gzm and gzm.is_highlight:
            size *= 1.25

        return size

    def create_objects_gizmos(self, context):

        self.gizmos.clear()
        self.gzms = []

        loc = self.objects[0].location
        active = context.active_object if context.active_object in self.objects else None     # active object that is part of the selection
        unique_mesh_count = len(set(obj.data for obj in self.mesh_objects))                   # unique mesh count among the selection
        unparented = [obj for obj in self.objects if obj != active and obj.parent != active]  # get objects not currently parented to the active

        if any(not obj.HC.ishyper for obj in self.mesh_objects):
            self.hype_gzm = create_button_gizmo(self, context, 'machin3.hype', icon='QUIT', location=loc, scale=self.get_gizmo_size())
            self.gzms.append((self.hype_gzm, 'HYPE'))
        else:
            self.hype_gzm = None

        if unparented:
            self.parented_gzm = create_button_gizmo(self, context, 'machin3.parent', args={}, icon='CON_CHILDOF', location=loc, scale=self.get_gizmo_size())
            self.gzms.append((self.parented_gzm, 'PARENTED'))
        else:
            self.parented_gzm = None

        if active and unique_mesh_count > 1:
            self.instanced_gzm = create_button_gizmo(self, context, 'machin3.link', icon='LINKED', location=loc, scale=self.get_gizmo_size('INSTANCED'))
            self.gzms.append((self.instanced_gzm, 'INSTANCED'))

        else:
            self.instanced_gzm = None

        if len(self.mesh_objects) >= 2:
            self.hyperbool_gzm = create_button_gizmo(self, context, 'machin3.add_boolean', args={'is_button_invocation': False}, icon='MOD_BOOLEAN', location=loc, scale=self.get_gizmo_size())
            self.gzms.append((self.hyperbool_gzm, 'HYPERBOOL'))
        else:
            self.hyperbool_gzm = None

class GizmoGroupEditCurve(bpy.types.GizmoGroup):
    bl_idname = "MACHIN3_GGT_edit_curve"
    bl_label = "Object"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'PERSISTENT', '3D'}

    @classmethod
    def poll(cls, context):
        view = context.space_data

        if view.overlay.show_overlays:
            if context.mode == 'EDIT_CURVE':
                active = context.active_object
                data = get_curve_as_dict(active.data)

                if spline := verify_curve_data(data, 'has_active_spline'):
                    if spline['type'] in ['POLY', 'NURBS'] and len(spline['points']) >= 3:
                        if verify_curve_data(data, 'has_active_selection'):
                            if not verify_curve_data(data, 'is_entire_spline_selected'):
                                if verify_curve_data(data, 'is_active_selection_continuous_with_cyclic_support'):

                                    if verify_curve_data(data, 'is_active_end_selected') and not spline['cyclic']:
                                        return False
                                    return True

    def setup(self, context):
        self.states = self.get_states(context)
        self.obj, self.data = self.states

        self.create_edit_curve_gizmos(context)

    def refresh(self, context):
        if not is_modal(self):
            if self.is_state_change(context):
                self.create_edit_curve_gizmos(context)

    def draw_prepare(self, context):
        if is_modal(self):
            for gzm in self.gizmos:
                gzm.hide = True
        else:

            if self.is_state_change(context):
                self.create_edit_curve_gizmos(context)

            for gzm in self.gizmos:
                gzm.hide = False

            gizmo_size = context.preferences.view.gizmo_size / 75

            corners = self.get_view_bbox_corners(context)

            offset = Vector((20, 20)) * gizmo_size

            offset_button_gizmo(context, self.blendulate_gzm, offset=offset, loc2d=corners['TOP_RIGHT'])

            if not self.blendulate_gzm.hide:
                self.blendulate_gzm.scale_basis = 0.125 if self.blendulate_gzm.is_highlight else 0.1

    def get_view_bbox_corners(self, context):
        view_bbox = get_view_bbox(context, [self.obj.matrix_world @ point['co'].xyz for point in self.data['active_selection']])

        corner_dict = {'BOTTOM_LEFT': view_bbox[0],
                       'BOTTOM_RIGHT': view_bbox[1],
                       'TOP_RIGHT': view_bbox[2],
                       'TOP_LEFT': view_bbox[3]}

        return corner_dict

    def get_states(self, context):
        states = []

        obj = context.active_object
        data = get_curve_as_dict(obj.data)

        states.append(obj)
        states.append(data)

        return states

    def is_state_change(self, context, debug=False):

        if (states := self.get_states(context)) != self.states:
            if debug:
                print()
                print("  Edit Curve Gizmo state has changed!!")
                print("    from:", self.states)
                print("      to:", states)
                print()

            self.states = states

            self.obj, self.data = states
            return True

        return False

    def create_edit_curve_gizmos(self, context):

        self.gizmos.clear()

        self.blendulate_gzm = create_button_gizmo(self, context, 'machin3.blendulate', icon='DRIVER_ROTATIONAL_DIFFERENCE', location=self.obj.matrix_world @ self.data['active_selection_mid_point'], scale=0.1)

class GizmoGroupCursorHistory(bpy.types.GizmoGroup):
    bl_idname = "MACHIN3_GGT_cursor_history"
    bl_label = "Object"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'PERSISTENT', '3D'}

    @classmethod
    def poll(cls, context):
        view = context.space_data
        hc = context.scene.HC

        if view.overlay.show_overlays:
            if get_active_tool(context).idname in ['machin3.tool_hyper_cursor', 'machin3.tool_hyper_cursor_simple']:
                return hc.draw_history and (hc.draw_history_select or hc.draw_history_remove)

    def setup(self, context):
        self.create_history_buttons(context)

        self.states = self.get_states(context)

    def refresh(self, context):
        if self.is_state_change(context):
            self.create_history_buttons(context)

    def draw_prepare(self, context):
        if self.is_state_change(context):
            self.create_history_buttons(context)

        hc = context.scene.HC
        gizmo_size = context.preferences.view.gizmo_size / 75

        for gzm, entry, type in self.gzms:

            gzm.hide = not getattr(hc, f"draw_history_{type.lower()}")

            if not gzm.hide:

                if entry.show:
                    loc2d = entry.co2d_gzm

                    offset = 15 * gizmo_size if hc.draw_history_select and type == 'REMOVE' else 0
                    offset_button_gizmo(context, gzm, offset=(offset, 0), loc2d=loc2d)

                    gzm.scale_basis = self.get_gizmo_size(type, gzm)

                else:
                    gzm.hide = True

    def get_states(self, context):
        hc = context.scene.HC
        states = [len(hc.historyCOL)]

        return states

    def is_state_change(self, context, debug=False):

        if (states := self.get_states(context)) != self.states:
            if debug:
                print()
                print("  Cursor History Gizmo state has changed!!")
                print("    from:", self.states)
                print("      to:", states)
                print()

            self.states = states
            return True

        return False

    def get_gizmo_size(self, type, gzm=None):
        if type == 'SELECT':
            size = 0.09

        elif type == 'REMOVE':
            size = 0.11

        if gzm and gzm.is_highlight:
            size *= 1.25

        return size

    def create_history_buttons(self, context):
        self.gizmos.clear()
        self.gzms = []

        hc = context.scene.HC

        for entry in hc.historyCOL:
            for type in ['SELECT', 'REMOVE']:
                if type == 'SELECT':
                    idname = 'machin3.select_cursor_history'
                    args = {'index': entry.index}
                    icon = 'RESTRICT_SELECT_OFF'
                elif type == 'REMOVE':
                    idname = 'machin3.change_cursor_history'
                    args = {'index': entry.index, 'mode': 'REMOVE'}
                    icon = 'X'

                gzm = create_button_gizmo(self, context, idname, args=args, icon=icon, location=entry.location, scale=self.get_gizmo_size(type))

                self.gzms.append((gzm, entry, type))

class GizmoGroupPipe(bpy.types.GizmoGroup, PipeGizmoManager):
    bl_idname = "MACHIN3_GGT_pipe"
    bl_label = "Pipe"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'3D'}

    count = 0

    @classmethod
    def poll(cls, context):
        return PipeGizmoManager().gizmo_poll(context)

    def setup(self, context):
        self.create_pipe_radius_gizmos(context)

    def refresh(self, context):
        if len(self.gizmos) != len(self.gizmo_data['points']):
            self.create_pipe_radius_gizmos(context)

    def draw_prepare(self, context):
        if is_modal(self):
            for gzm, _ in self.gzms:
                gzm.hide = True
        else:
            for gzm, point in self.gzms:
                gzm.hide = not point['show']

                if not gzm.hide:
                    gzm.scale_basis = 0.1 if gzm.is_highlight else 0.06

    def create_pipe_radius_gizmos(self, context):
        self.gizmos.clear()
        self.gzms = []

        for point in self.gizmo_data['points']:
            gzm = create_button_gizmo(self, context, operator='machin3.adjust_pipe_arc', args={'index': point['index']}, icon='RADIOBUT_ON', location=point['co'], scale=0.06)
            self.gzms.append((gzm, point))

class GizmoGroupCurveSurface(bpy.types.GizmoGroup, CurveSurfaceGizmoManager):
    bl_idname = "MACHIN3_GGT_curve_surface"
    bl_label = "Pipe Radius"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'3D'}

    @classmethod
    def poll(cls, context):
        return CurveSurfaceGizmoManager().gizmo_poll(context)

    def setup(self, context):
        self.create_curve_surface_point_gizmos(context)

    def refresh(self, context):
        if len(self.gizmos) != len(self.gizmo_data['points']):
            self.gizmos.clear()

            self.create_curve_surface_point_gizmos(context)

    def draw_prepare(self, context):
        for gzm, point in self.gzms:
            gzm.matrix_basis.translation = point['co']
            gzm.scale_basis = 0.1 if gzm.is_highlight else 0.06

            point['is_highlight'] = gzm.is_highlight

    def create_curve_surface_point_gizmos(self, context):
        self.gzms = []

        for point in self.gizmo_data['points']:
            gzm = create_button_gizmo(self, context, operator='machin3.adjust_curve_surface_point', args={'index': point['index']}, icon='RADIOBUT_ON', location=point['co'], scale=0.06)
            self.gzms.append((gzm, point))

class GizmoGroupRemoveUnusedBooleans(bpy.types.GizmoGroup, RemoveUnusedBooleanGizmoManager):
    bl_idname = "MACHIN3_GGT_remove_unused_booleans"
    bl_label = "Remove Unused Booleans"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'3D'}

    @classmethod
    def poll(cls, context):
        return RemoveUnusedBooleanGizmoManager().gizmo_poll(context)

    def setup(self, context):
        self.states = self.get_states()

        self.create_remove_unused_booleans_gizmos(context)

    def refresh(self, context):

        if self.is_state_change():
            self.create_remove_unused_booleans_gizmos(context)

    def draw_prepare(self, context):
        if self.is_state_change():
            self.gizmos.clear()
            self.create_remove_unused_booleans_gizmos(context)

        gizmo_size = context.preferences.view.gizmo_size / 75
        is_any_highlight = False

        for gizmos, m in self.gzms:

            for gzm in gizmos:
                gzm.hide = False

            is_group_highlight = any(gzm.is_highlight for gzm in gizmos)

            offset = 0
            spacing_factor = 1.25 if is_group_highlight else 1

            for gzm in gizmos:
                offset_button_gizmo(context, gzm, offset=(offset * spacing_factor * gizmo_size, 0), loc2d=m['co2d'])
                offset += 15

                gzm.scale_basis = 0.125 if gzm.is_highlight else 0.1 if is_group_highlight else 0.08

            m['is_highlight'] = is_group_highlight

            if not is_any_highlight and is_group_highlight:
                is_any_highlight = True

        if is_any_highlight:
            for gizmos, m in self.gzms:
                if not m['is_highlight']:
                    for gzm in gizmos:
                        gzm.hide = True

    def get_states(self):
        states = []

        opd = self.operator_data
        gd = self.gizmo_data

        for m in gd['modifiers']:
            mod = opd['active'].modifiers.get(m['modname'])

            states.append(m['remove'])

            states.append(mod.show_viewport)

        return states

    def is_state_change(self, debug=False):

        if (states := self.get_states()) != self.states:
            if debug:
                print()
                print("  Remove Unused Booleans Gizmo state has changed!!")
                print("    from:", self.states)
                print("      to:", states)
                print()

            self.states = states
            return True

        return False

    def create_remove_unused_booleans_gizmos(self, context):

        self.gizmos.clear()
        self.gzms = []

        opd = self.operator_data['active']
        gp = self.gizmo_props
        gd = self.gizmo_data

        for m in gd['modifiers']:
            mod = opd.modifiers.get(m['modname'])

            icon = 'HIDE_OFF' if mod.show_viewport else 'HIDE_ON'
            mgzm = create_button_gizmo(self, context, operator='machin3.toggle_unused_boolean_mod', args={'index': m['index'], 'mode': 'TOGGLE'}, icon=icon, location=m['co'], scale=0.08)

            icon = 'X' if m['remove'] else 'RADIOBUT_OFF'
            rgzm = create_button_gizmo(self, context, operator='machin3.toggle_unused_boolean_mod', args={'index': m['index'], 'mode': 'REMOVE'}, icon=icon, location=m['co'], scale=0.08)

            self.gzms.append(((mgzm, rgzm), m))

        if mouse_pos := gp['warp_mouse']:
            gp['warp_mouse'] = None
            warp_mouse(self, context, mouse_pos, region=False, warp_hud=False)

class GizmoGroupPickObjectTree(bpy.types.GizmoGroup, PickObjectTreeGizmoManager):
    bl_idname = "MACHIN3_GGT_pick_object_tree"
    bl_label = "Pick Object Tree"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'3D'}

    @classmethod
    def poll(cls, context):
        return PickObjectTreeGizmoManager().gizmo_poll(context)

    def setup(self, context):
        self.states = [(o['remove'], bpy.data.objects[o['modhostobjname']].modifiers[o['modname']].show_viewport if o['modhostobjname'] else None) for o in self.gizmo_data['objects']]

        self.create_pick_object_tree_gizmos(context)

    def refresh(self, context):

        if self.is_state_change(context):
            self.create_pick_object_tree_gizmos(context)

    def draw_prepare(self, context):
        if self.is_state_change(context):
            self.create_pick_object_tree_gizmos(context)

        gizmo_size = context.preferences.view.gizmo_size / 75
        is_any_highlight = False

        for gizmos, o in self.gzms:

            for gzm in gizmos:
                gzm.hide = not o['show']

            if o['show']:

                is_group_highlight = any(gzm.is_highlight for gzm in gizmos)

                offset = 0
                spacing_factor = 1.25 if is_group_highlight else 1

                for gzm in gizmos:

                    offset_button_gizmo(context, gzm, offset=(offset * spacing_factor * gizmo_size, 0), loc2d=o['co2d'])
                    offset += 15

                    gzm.scale_basis = 0.125 if gzm.is_highlight else 0.1 if is_group_highlight else 0.08

                o['is_highlight'] = is_group_highlight

                if not is_any_highlight and is_group_highlight:
                    is_any_highlight = True

        if is_any_highlight:
            for gizmos, o in self.gzms:
                if not o['is_highlight']:
                    for gzm in gizmos:
                        gzm.hide = True

    def get_states(self, context):
        states = []

        for o in self.gizmo_data['objects']:
            obj = bpy.data.objects[o['objname']]

            modhostobj = bpy.data.objects[o['modhostobjname']] if o['modhostobjname'] else None
            mod = modhostobj.modifiers[o['modname']] if o['modhostobjname'] and o['modname'] else None

            states.append(obj.select_get())
            states.append(o['remove'])

            if mod:
                states.append(mod.show_viewport)

        return states

    def is_state_change(self, context, debug=False):

        if (states := self.get_states(context)) != self.states:
            if debug:
                print()
                print("  Pick Object Tree Gizmos state has changed!!")
                print("    from:", self.states)
                print("      to:", states)
                print()

            self.states = states
            return True
        return False

    def create_pick_object_tree_gizmos(self, context):

        self.gizmos.clear()
        self.gzms = []

        gp = self.gizmo_props
        gd = self.gizmo_data

        for o in gd['objects']:
            gizmos = []

            icon = 'RESTRICT_SELECT_OFF' if bpy.data.objects[o['objname']].select_get() else 'RESTRICT_SELECT_ON'
            select_gzm = create_button_gizmo(self, context, operator='machin3.toggle_pick_object_tree', args={'index': o['index'], 'mode': 'SELECT'}, icon=icon, location=o['co'], scale=0.08)
            gizmos.append(select_gzm)

            if o['modname']:
                if o['modhostobjname']:
                    modparent = bpy.data.objects[o['modhostobjname']]
                    mod = modparent.modifiers.get(o['modname'])

                    icon = 'HIDE_OFF' if mod.show_viewport else 'HIDE_ON'
                    mod_gizmo = create_button_gizmo(self, context, operator='machin3.toggle_pick_object_tree', args={'index': o['index'], 'mode': 'TOGGLE'}, icon=icon, location=o['co'], scale=0.08)
                    gizmos.append(mod_gizmo)

            icon = 'X' if o['remove'] else 'RADIOBUT_OFF'
            remove_gizmo = create_button_gizmo(self, context, operator='machin3.toggle_pick_object_tree', args={'index': o['index'], 'mode': 'REMOVE'}, icon=icon, location=o['co'], scale=0.08)
            gizmos.append(remove_gizmo)

            self.gzms.append((gizmos, o))

        if mouse_pos := gp['warp_mouse']:
            gp['warp_mouse'] = None
            warp_mouse(self, context, mouse_pos, region=False, warp_hud=False)

class GizmoGroupHyperBevel(bpy.types.GizmoGroup, HyperBevelGizmoManager):
    bl_idname = "MACHIN3_GGT_hyper_bevel"
    bl_label = "Hyper Bevel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'3D'}

    @classmethod
    def poll(cls, context):
        return HyperBevelGizmoManager().gizmo_poll(context)

    def setup(self, context):
        self.create_hyper_bevel_gizmos(context)

        self.states = self.get_states(context)

    def refresh(self, context):

        if self.is_state_change(context, debug=False):
            self.create_hyper_bevel_gizmos(context)

    def draw_prepare(self, context):

        if is_modal(self):
            for gzm in self.gizmos:
                gzm.hide = not gzm.is_modal

        else:
            if self.is_state_change(context, debug=False):
                self.create_hyper_bevel_gizmos(context)

            for gzm_type, gzm, gizmo in self.gzms:

                if gzm.hide:
                    gzm.hide = False

                if gzm_type == 'SWEEPS':
                    gzm.hide = not self.gizmo_props['show_sweeps']

                if gzm_type == 'SWEEPS':

                    _, scale = self.get_gizmo_icon_and_size(gzm, gizmo)

                    gzm.scale_basis = scale

                elif gzm_type == 'WIDTH':

                    gzm.scale_basis = 1.1 if gzm and gzm.is_highlight else 1

                    gzm.line_width = 3 if gzm and gzm.is_highlight else 1

                elif gzm_type == 'EXTEND':
                    gzm.scale_basis = 0.85 if gzm and gzm.is_highlight else 0.75

                    gzm.line_width = 2 if gzm and gzm.is_highlight else 1

                gizmo['is_highlight'] = gzm.is_highlight

    def get_states(self, context):
        states = []

        for sidx, seq_data in self.gizmo_data['sweeps'].items():
            gizmos = seq_data['gizmos']

            for idx, data in gizmos.items():

                for side in ['left', 'right']:
                    states.append(data[side]['default'])

                if gizmo := data.get('extend'):
                    states.append(gizmo['loc'])

        states.append(self.gizmo_data['width']['loc'])

        return states

    def is_state_change(self, context, debug=False):

        if (states := self.get_states(context)) != self.states:
            if debug:
                print()
                print("  Hyper Bevel Gizmo state has changed!!")
                print("    from:", self.states)
                print("      to:", states)
                print()

            self.states = states
            return True

        return False

    def get_gizmo_icon_and_size(self, gzm, gizmo):
        default = gizmo['default']
        factor = 1.25 if gzm and gzm.is_highlight else 1

        if default == 'FACE_DIR':
            return 'FACESEL', 0.09 * factor

        elif default == 'EDGE_DIR':
            return 'EDGESEL', 0.1 * factor

        elif default == 'INBETWEEN_DIR':
            return 'CENTER_ONLY', 0.08 * factor

        elif default == 'CENTER_AIM_DIR':
            return 'PROP_ON', 0.08 * factor

    def create_hyper_bevel_gizmos(self, context):
        self.gizmos.clear()
        self.gzms = []

        for sidx, seq_data in self.gizmo_data['sweeps'].items():
            gizmos = seq_data['gizmos']

            for idx, data in gizmos.items():
                for side in ['left', 'right']:
                    gizmo = data[side]

                    if len(gizmo['options']) > 1:
                        icon, scale = self.get_gizmo_icon_and_size(None, gizmo)
                        gzm = create_button_gizmo(self, context, operator='machin3.adjust_hyper_bevel_sweep', args={'sidx': sidx, 'idx': idx, 'side': side}, icon=icon, location=gizmo['sweep_co'], scale=scale)

                        self.gzms.append(('SWEEPS', gzm, gizmo))

                if idx == 0 or idx == len(gizmos) - 1:
                    if gizmo := data.get('extend'):
                        gzm = self.gizmos.new("GIZMO_GT_arrow_3d")
                        op = gzm.target_set_operator("machin3.adjust_hyper_bevel_extend")
                        op.sidx = sidx
                        op.idx = idx

                        gzm.matrix_basis = gizmo['matrix']
                        gzm.scale_basis = 0.75

                        gzm.draw_style = 'BOX'
                        gzm.length = 0.2

                        gzm.color = white
                        gzm.alpha = 0.3
                        gzm.color_highlight = yellow
                        gzm.alpha_highlight = 1

                        self.gzms.append(('EXTEND', gzm, gizmo))

        gizmo = self.gizmo_data['width']

        if gizmo:
            gzm = self.gizmos.new("GIZMO_GT_arrow_3d")
            gzm.target_set_operator("machin3.adjust_hyper_bevel_width")

            gzm.matrix_basis = gizmo['matrix']

            gzm.draw_style = 'BOX'
            gzm.length = 0.2

            gzm.color = white
            gzm.alpha = 0.3
            gzm.color_highlight = yellow
            gzm.alpha_highlight = 1

            self.gzms.append(('WIDTH', gzm, gizmo))

class GizmoGroupPickHyperBevel(bpy.types.GizmoGroup, PickHyperBevelGizmoManager):
    bl_idname = "MACHIN3_GGT_pick_hyper_bevel"
    bl_label = "Pick Hyper Bevel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'3D', 'SCALE'}

    count = 0

    @classmethod
    def poll(cls, context):
        return PickHyperBevelGizmoManager().gizmo_poll(context)

    def setup(self, context):
        self.obj = context.active_object

        _, _, dims = get_bbox(self.obj.data)
        self.dim = sum([d for d in get_sca_matrix(self.obj.matrix_world.to_scale()) @ dims]) / 3

        self.create_hyper_bevel_gizmos(context)

    def refresh(self, context):

        global force_pick_hyper_bevels_gizmo_update

        if len(self.gzms) != len(self.gizmo_data['hyperbevels']) or force_pick_hyper_bevels_gizmo_update:
            if force_pick_hyper_bevels_gizmo_update:
                force_pick_hyper_bevels_gizmo_update = False

            self.gizmos.clear()

            self.create_hyper_bevel_gizmos(context)

    def draw_prepare(self, context):

        if is_modal(self):
            for edge_gizmos, _ in self.gzms:
                for gzm in edge_gizmos:
                    gzm.hide = True

        else:
            for edge_gizmos, b in self.gzms:

                is_highlight = any(gzm.is_highlight for gzm in edge_gizmos)

                b['is_highlight'] = is_highlight

                for gzm in edge_gizmos:
                    gzm.hide = False

                    if gzm.is_highlight:
                        gzm.color_highlight = red if b['remove'] else yellow
                        gzm.alpha_highlight = 0.5 if b['show_viewport'] else 0.25

                    if is_highlight and not gzm.is_highlight:
                        gzm.color = red if b['remove'] else yellow
                        gzm.alpha = 0.5 if b['show_viewport'] else 0.25

                    elif not is_highlight:
                        gzm.color = red if b['remove'] else white
                        gzm.alpha = 0.1 if b['remove'] else 0.05 if b['show_viewport'] else 0.01

    def create_hyper_bevel_gizmos(self, context):
        def create_edge_gizmos(b, size=0.2):
            obj = b['obj']
            mx = obj.matrix_world

            ui_scale = context.preferences.system.ui_scale

            gizmo_size = context.preferences.view.gizmo_size / 75

            bm = bmesh.new()
            bm.from_mesh(obj.data)

            edge_glayer = ensure_edge_glayer(bm)

            edges = [e for e in bm.edges if e[edge_glayer] == 1]

            edge_gizmos = []

            for e in edges:
                e_dir = mx.to_3x3() @ (e.verts[1].co - e.verts[0].co)

                loc = get_loc_matrix(mx @ get_center_between_verts(*e.verts))
                rot = create_rotation_matrix_from_vector(e_dir.normalized())
                sca = get_sca_matrix(Vector((1, 1, (e_dir.length) / (size * self.dim * self.obj.HC.geometry_gizmos_scale * ui_scale * gizmo_size))))

                gzm = self.gizmos.new("MACHIN3_GT_3d_stem")
                op = gzm.target_set_operator("machin3.edit_hyper_bevel")
                op.objname = self.obj.name
                op.modname = b['modname']
                op.is_profile_drop = False
                op.is_hypermod_invocation = False

                gzm.matrix_basis = loc @ rot @ sca

                gzm.scale_basis = size * self.dim * self.obj.HC.geometry_gizmos_scale * gizmo_size

                gzm.color = white
                gzm.alpha = 0.05
                gzm.color_highlight = yellow
                gzm.alpha_highlight = 0.5

                edge_gizmos.append(gzm)

            return edge_gizmos

        self.gzms = []

        for b in self.gizmo_data['hyperbevels']:
            edge_gizmos = create_edge_gizmos(b)

            self.gzms.append((edge_gizmos, b))

class GizmoGroupHyperBend(bpy.types.GizmoGroup, HyperBendGizmoManager):
    bl_idname = "MACHIN3_GGT_hyper_bend"
    bl_label = "HyperBend"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'3D'}

    @classmethod
    def poll(cls, context):
        return HyperBendGizmoManager().gizmo_poll(context)

    def setup(self, context):
        self.create_bend_gizmos(context)

        self.states = self.get_states(context)

    def refresh(self, context):

        if self.is_state_change(context, debug=False):
            self.create_bend_gizmos(context)

    def draw_prepare(self, context):
        opd = self.operator_data
        gp = self.gizmo_props
        gd = self.gizmo_data

        gizmo_size = context.preferences.view.gizmo_size / 75

        if modal := is_modal(self):
            for gzm in self.gizmos:
                if gzm.bl_idname == "GIZMO_GT_dial_3d":
                    gzm.line_width = 1
                    gzm.arc_inner_factor = 0.4

                gzm.hide = not gzm.is_modal

        else:
            if self.is_state_change(context, debug=False):
                self.create_bend_gizmos(context)

            for gzm in self.gizmos:

                if gzm.bl_idname == "GIZMO_GT_dial_3d":
                    gzm.line_width = 2
                    gzm.arc_inner_factor = 0
                    gzm.draw_options = {'FILL_SELECT'}

                gzm.hide = False

        opd = self.operator_data
        gd = self.gizmo_data

        for gzm, data in self.gzms:

            data['is_highlight'] = gzm.is_highlight

            if data['type'][0] == 'ANGLE':
                data['show'] = opd['BEND']['POSITIVE'] or opd['BEND']['NEGATIVE']

            if data['type'][0] == 'OFFSET':
                data['show'] = opd['angle'] != 0 and opd['BEND']['POSITIVE'] or opd['BEND']['NEGATIVE']

            elif data['type'][0] == 'LIMIT':
                side = data['type'][1]

                if side == 'POSITIVE':
                    data['show'] = (opd['BEND'][side] or opd['BISECT'][side]) and not opd['is_kink'] and gd['LIMIT'][side]['distance']
                else:
                    data['show'] = (opd['BEND'][side] and opd['BISECT'][side]) and not opd['mirror_bend'] and not opd['is_kink'] and gd['LIMIT'][side]['distance']

            elif data['type'][0] == 'CONTAIN':
                side = data['type'][1]

                data['show'] = opd['contain'] and gd['CONTAIN'][side]['distance']

            elif (prop := data['type'][0]) in ['is_kink', 'use_kink_edges', 'affect_children', 'remove_redundant']:
                offset_button_gizmo(context, gzm, offset=(self.get_horizontal_button_offset(data['type']) * gizmo_size, -100 * gizmo_size), loc2d=gp['loc2d'])

                if prop == 'is_kink':
                    data['show'] = gd['LIMIT']['POSITIVE']['distance']

                elif prop == 'use_kink_edges':
                    data['show'] = opd['is_kink']

                elif prop == 'affect_children':
                    data['show'] = opd['has_children']

                elif prop == 'remove_redundant':
                    data['show'] = opd['BISECT']['POSITIVE'] or opd['BISECT']['NEGATIVE'] or opd['is_kink']

            elif (prop := data['type'][0]) in ['mirror_bend', 'BISECT', 'BEND']:
                offset_button_gizmo(context, gzm, offset=(self.get_horizontal_button_offset(data['type']) * gizmo_size, -120 * gizmo_size), loc2d=gp['loc2d'])

                if prop == 'mirror_bend':
                    data['show'] = not opd['is_kink'] and gd['LIMIT']['POSITIVE']['distance'] and gd['LIMIT']['NEGATIVE']['distance']

                elif (side := data['type'][1]) == 'POSITIVE':
                    data['show'] = not opd['is_kink'] and gd['LIMIT'][side]['distance']

                elif (side := data['type'][1]) == 'NEGATIVE':
                    data['show'] = not opd['mirror_bend'] and not opd['is_kink'] and gd['LIMIT'][side]['distance']

            if not modal:
                gzm.hide =  not data['show']

            if not gzm.hide and data['type'][0] in ['is_kink', 'use_kink_edges', 'affect_children', 'remove_redundant', 'mirror_bend', 'BISECT', 'BEND']:
                gzm.scale_basis = self.get_gizmo_size(gzm)

    def get_states(self, context):
        opd = self.operator_data
        gp = self.gizmo_props

        states = []

        for prop in  ['affect_children', 'is_kink', 'use_kink_edges', 'mirror_bend', 'remove_redundant']:
            states.append(opd[prop])

        for gzm_type in ['BISECT', 'BEND']:
            for side in ['POSITIVE', 'NEGATIVE']:
                states.append(opd[gzm_type][side])

        if gp['push_update']:
            states.append(gp['push_update'])
            gp['push_update'] = None

        return states

    def is_state_change(self, context, debug=False):

        if (states := self.get_states(context)) != self.states:
            if debug:
                print()
                print("  Hyper Bend Gizmo state has changed!!")
                print("    from:", self.states)
                print("      to:", states)
                print()

            self.states = states
            return True

        return False

    def get_horizontal_button_offset(self, type):
        gd = self.gizmo_data
        opd = self.operator_data

        if (prop := type[0]) in ['is_kink', 'use_kink_edges', 'affect_children', 'remove_redundant']:

            button_count = 0

            if gd['LIMIT']['POSITIVE']['distance']:
                button_count += 1

            if opd['is_kink']:
                button_count += 1

            if opd['has_children']:
                button_count += 1

            if opd['is_kink'] or (opd['BISECT']['POSITIVE'] or opd['BISECT']['NEGATIVE']):
                button_count += 1

            offsets = [-10 * (button_count - 1) + i * 20 for i in range(button_count)]

            if offsets:

                if prop == 'is_kink':
                    return offsets[0]

                elif prop == 'use_kink_edges':
                    return offsets[min(1, len(offsets) - 1)]

                elif prop == 'affect_children':
                    return offsets[min(2 if opd['is_kink'] else 1 if gd['LIMIT']['POSITIVE']['distance'] else 0, len(offsets) - 1)]

                elif prop == 'remove_redundant':
                    return offsets[-1]

        elif type[0] == 'BISECT':
            return 30 if type[1] == 'POSITIVE' else -30

        elif type[0] == 'BEND':
            return 50 if type[1] == 'POSITIVE' else -50

        return 0

    def get_gizmo_size(self, gzm=None):
        size = 0.09

        if gzm and gzm.is_highlight:
            size *= 1.25

        return size

    def create_bend_gizmos(self, context):

        self.gizmos.clear()
        self.gzms = []

        opd = self.operator_data
        gp = self.gizmo_props
        gd = self.gizmo_data

        gzm = self.gizmos.new("GIZMO_GT_dial_3d")
        gzm.target_set_operator("machin3.adjust_bend_angle")

        gzm.matrix_basis = gp['cmx'] @ Matrix.Rotation(radians(90), 4, 'X')

        gzm.draw_options = {'FILL_SELECT'}
        gzm.use_draw_value = True
        gzm.use_draw_hover = False

        gzm.line_width = 2
        gzm.scale_basis = 1

        gzm.color = (0.3, 1, 0.3)
        gzm.alpha = 0.3
        gzm.color_highlight = (0.5, 1, 0.5)
        gzm.alpha_highlight = 1

        self.gzms.append((gzm, self.gizmo_data['ANGLE']))

        gzm = self.gizmos.new("GIZMO_GT_arrow_3d")
        gzm.target_set_operator("machin3.adjust_bend_offset")

        gzm.matrix_basis = get_loc_matrix(gd['OFFSET']['loc']) @ get_rot_matrix(gd['OFFSET']['rot'])

        gzm.draw_style = 'NORMAL'

        gzm.length = 0.3
        gzm.scale_basis = 1

        gzm.color = blue
        gzm.alpha = 0.5
        gzm.color_highlight = light_blue
        gzm.alpha_highlight = 1

        self.gzms.append((gzm, gd['OFFSET']))

        for side in ['POSITIVE', 'NEGATIVE']:
            gzm = self.gizmos.new("GIZMO_GT_arrow_3d")
            op = gzm.target_set_operator("machin3.adjust_bend_limit")
            op.side = side

            gzm.matrix_basis = get_loc_matrix(gd['LIMIT'][side]['loc']) @ get_rot_matrix(gd['LIMIT'][side]['rot'])

            gzm.draw_style = 'BOX'

            gzm.length = 0.1
            gzm.scale_basis = 1

            gzm.color = yellow
            gzm.alpha = 0.5
            gzm.color_highlight = light_yellow
            gzm.alpha_highlight = 1

            self.gzms.append((gzm, gd['LIMIT'][side]))

        for side in ['POSITIVE_Y', 'NEGATIVE_Y', 'POSITIVE_Z', 'NEGATIVE_Z']:
            gzm = self.gizmos.new("GIZMO_GT_arrow_3d")
            op = gzm.target_set_operator("machin3.adjust_bend_containment")
            op.side = side

            gzm.matrix_basis = get_loc_matrix(gd['CONTAIN'][side]['loc']) @ get_rot_matrix(gd['CONTAIN'][side]['rot'])

            gzm.draw_style = 'BOX'

            gzm.length = 0.1
            gzm.scale_basis = 1

            gzm.color = green if '_Y' in side else blue
            gzm.alpha = 0.5
            gzm.color_highlight = light_green if '_Y' in side else light_blue
            gzm.alpha_highlight = 1

            self.gzms.append((gzm, gd['CONTAIN'][side]))

        for prop in ['mirror_bend', 'is_kink', 'use_kink_edges', 'affect_children', 'remove_redundant']:

            if prop == 'mirror_bend':
                icon = 'MOD_MIRROR' if opd[prop] else 'RADIOBUT_OFF'

            elif prop == 'is_kink':
                icon = 'LAYER_USED' if opd[prop] else 'MOD_OUTLINE'

            elif prop == 'use_kink_edges':
                icon = 'MOD_SIMPLIFY' if opd[prop] else 'LAYER_USED'

            elif prop == 'affect_children':
                icon = 'COMMUNITY' if opd[prop] else 'LAYER_USED'

            elif prop == 'remove_redundant':
                icon = 'TRASH' if opd[prop] else 'LAYER_USED'

            gzm = create_button_gizmo(self, context, operator='machin3.toggle_bend', args={'prop': prop}, icon=icon, location=gp['loc'], scale=0.1)
            self.gzms.append((gzm, gd[prop]))

        for side in ['POSITIVE', 'NEGATIVE']:

            icon = 'STRANDS' if opd['BISECT'][side] else 'LAYER_USED'
            gzm = create_button_gizmo(self, context, operator='machin3.toggle_bend', args={'prop': f"{side.lower()}_bisect"}, icon=icon, location=gp['loc'], scale=0.1)

            self.gzms.append((gzm, gd['BISECT'][side]))

            icon = 'MOD_SIMPLEDEFORM' if opd['BEND'][side] else 'LAYER_USED'
            gzm = create_button_gizmo(self, context, operator='machin3.toggle_bend', args={'prop': f"{side.lower()}_bend"}, icon=icon, location=gp['loc'], scale=0.1)

            self.gzms.append((gzm, gd['BEND'][side]))

        if mouse_pos := gp['warp_mouse']:
            gp['warp_mouse'] = None
            warp_mouse(self, context, mouse_pos, region=False, warp_hud=False)

class GizmoGroupTest(bpy.types.GizmoGroup):
    bl_idname = "MACHIN3_GGT_test"
    bl_label = "Test Gizmo"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'3D', 'PERSISTENT'}

    @classmethod
    def poll(cls, context):
        return False

    def setup(self, context):
        print("Test Gizmo setup")

    def refresh(self, context):

        pass

    def draw_prepare(self, context):

        pass
