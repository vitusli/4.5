import bpy
from bpy.props import EnumProperty, BoolProperty, FloatProperty, IntProperty, StringProperty
import bmesh
from math import degrees, radians, sin, cos
from mathutils import Vector, Quaternion, Matrix
from mathutils.geometry import intersect_line_line, intersect_line_plane

from .. utils.bmesh import ensure_gizmo_layers, get_face_angle
from .. utils.draw import draw_init, draw_label, draw_line, draw_tris, draw_point, draw_points, draw_vector, draw_batch
from .. utils.gizmo import hide_gizmos, restore_gizmos
from .. utils.math import dynamic_format
from .. utils.object import get_batch_from_mesh, get_object_tree
from .. utils.operator import Settings
from .. utils.system import printd
from .. utils.ui import finish_modal_handlers, force_ui_update, gizmo_selection_passthrough, init_modal_handlers, navigation_passthrough, scroll, scroll_up, scroll_down, ignore_events, init_status, finish_status, get_mouse_pos, get_scale, draw_status_item, update_mod_keys
from .. utils.view import get_location_2d, get_view_origin_and_dir

from .. items import bend_angle_presets, ctrl
from .. colors import red, green, yellow, white, blue, normal, black

class HyperBendGizmoManager:
    operator_data = {}

    gizmo_props = {}
    gizmo_data = {}

    def gizmo_poll(self, context):
        if context.mode == 'OBJECT':
            props = self.gizmo_props
            return props.get('area_pointer') == str(context.area.as_pointer()) and props.get('show')

    def gizmo_group_init(self, context, loc, rot):
        self.operator_data.clear()
        self.gizmo_props.clear()
        self.gizmo_data.clear()

        loc2d = get_location_2d(context, loc, debug=False)

        self.operator_data['show_HUD'] = True                               # not a true operator prop, as it doesn't exist on the op, and is exclusviely used from the operator_data dict, to toggle the main Bend HUD from external adjust ops'
        self.operator_data['active'] = self.active

        self.operator_data['BEND'] = {'POSITIVE': self.positive_bend,
                                      'NEGATIVE': self.negative_bend}

        self.operator_data['BISECT'] = {'POSITIVE': self.positive_bisect,
                                        'NEGATIVE': self.negative_bisect}

        self.operator_data['LIMIT'] = {'POSITIVE': self.positive_limit,
                                       'NEGATIVE': self.negative_limit}

        self.operator_data['CONTAIN'] = {'POSITIVE_Y': self.positive_y_contain,
                                         'NEGATIVE_Y': self.negative_y_contain,
                                         'POSITIVE_Z': self.positive_y_contain,
                                         'NEGATIVE_Z': self.negative_z_contain}

        self.operator_data['SEGMENTS'] = {'POSITIVE': self.positive_segments,
                                          'NEGATIVE': self.negative_segments}

        self.operator_data['angle'] = self.angle
        self.operator_data['offset'] = self.offset
        self.operator_data['mirror_bend'] = self.mirror_bend
        self.operator_data['is_kink'] = self.is_kink
        self.operator_data['use_kink_edges'] = self.use_kink_edges
        self.operator_data['remove_redundant'] = self.remove_redundant
        self.operator_data['has_children'] = self.has_children                 # never toggled, but checked by gizmo group's draw_prepare to see if affect children gizmo toggle should be shown'
        self.operator_data['affect_children'] = self.affect_children
        self.operator_data['contain'] = self.contain
        self.operator_data['push_update'] = False                              # used to update operator properties from other ops

        self.gizmo_props['show'] = True
        self.gizmo_props['area_pointer'] = str(context.area.as_pointer())
        self.gizmo_props['cmx'] = context.scene.cursor.matrix
        self.gizmo_props['loc'] = loc
        self.gizmo_props['loc2d'] = loc2d
        self.gizmo_props['rot'] = rot
        self.gizmo_props['obj'] = self.active
        self.gizmo_props['push_update'] = None                                 # used to force gizmo recreation, for instance when AdjustBendOffset() finishes, to set the new offset gizmo location
        self.gizmo_props['warp_mouse'] = None

        self.gizmo_data['ANGLE'] = {'loc': loc,
                                    'rot': rot,
                                    'angle': 0,
                                    'type': ['ANGLE'],
                                    'show': True,
                                    'is_highlight': False}

        self.gizmo_data['OFFSET'] = {'loc': loc,
                                     'rot': rot,
                                     'z_factor': 1,
                                     'type': ['OFFSET'],
                                     'show': True,
                                     'is_highlight': False}

        self.gizmo_data['LIMIT'] = {'POSITIVE': {'loc': loc,
                                                 'rot': rot,
                                                 'distance': 0,
                                                 'type': ['LIMIT', 'POSITIVE'],
                                                 'show': True,
                                                 'is_highlight': False},

                                    'NEGATIVE': {'loc': loc,
                                                 'rot': rot,
                                                 'distance': 0,
                                                 'type': ['LIMIT', 'NEGATIVE'],
                                                 'show': True,
                                                 'is_highlight': False}}

        self.gizmo_data['CONTAIN'] = {'POSITIVE_Y': {'loc': loc,
                                                     'rot': rot,
                                                     'distance': 0,
                                                     'type': ['CONTAIN', 'POSITIVE_Y'],
                                                     'show': True,
                                                     'is_highlight': False},
                                      'NEGATIVE_Y': {'loc': loc,
                                                     'rot': rot,
                                                     'distance': 0,
                                                     'type': ['CONTAIN', 'NEGATIVE_Y'],
                                                     'show': True,
                                                     'is_highlight': False},
                                      'POSITIVE_Z': {'loc': loc,
                                                     'rot': rot,
                                                     'distance': 0,
                                                     'type': ['CONTAIN', 'POSITIVE_Z'],
                                                     'show': True,
                                                     'is_highlight': False},
                                      'NEGATIVE_Z': {'loc': loc,
                                                     'rot': rot,
                                                     'distance': 0,
                                                     'type': ['CONTAIN', 'NEGATIVE_Z'],
                                                     'show': True,
                                                     'is_highlight': False}}

        self.gizmo_data['BEND'] = {'POSITIVE': {'type': ['BEND', 'POSITIVE'],
                                                'show': True,
                                                'is_highlight': False},
                                   'NEGATIVE': {'type': ['BEND', 'NEGATIVE'],
                                                'show': True,
                                                'is_highlight': False}}
        self.gizmo_data['BISECT'] = {'POSITIVE': {'type': ['BISECT', 'POSITIVE'],
                                                  'show': True,
                                                  'is_highlight': False},
                                     'NEGATIVE': {'type': ['BISECT', 'NEGATIVE'],
                                                  'show': True,
                                                  'is_highlight': False}}

        self.gizmo_data['is_kink'] = {'type': ['is_kink'],
                                   'show': True,
                                   'is_highlight': False}
        self.gizmo_data['use_kink_edges'] = {'type': ['use_kink_edges'],
                                         'show': True,
                                         'is_highlight': False}
        self.gizmo_data['mirror_bend'] = {'type': ['mirror_bend'],
                                     'show': True,
                                     'is_highlight': False}
        self.gizmo_data['remove_redundant'] = {'type': ['remove_redundant'],
                                               'show': True,
                                               'is_highlight': False}
        self.gizmo_data['affect_children'] = { 'type': ['affect_children'],
                                              'show': True,
                                              'is_highlight': False}

        context.window_manager.gizmo_group_type_ensure('MACHIN3_GGT_hyper_bend')

    def gizmo_group_finish(self, context):
        self.operator_data.clear()

        self.gizmo_props.clear()
        self.gizmo_data.clear()

        context.window_manager.gizmo_group_type_unlink_delayed('MACHIN3_GGT_hyper_bend')

    def push_updates_back_to_operator(self):
        has_changed = False
        opd = self.operator_data

        opd['push_update'] = False

        for key in opd:
            if key in ['show_HUD', 'active', 'push_update']:
                continue

            elif key in ['BEND', 'BISECT', 'LIMIT', 'SEGMENTS']:
                for side in ['POSITIVE', 'NEGATIVE']:
                    if (prop := opd[key][side]) != getattr(self, f"{side.lower()}_{key.lower()}"):
                        setattr(self, f"{side.lower()}_{key.lower()}", prop)

                        has_changed = True

            elif key == 'CONTAIN':
                for side in ['POSITIVE_Y', 'NEGATIVE_Y', 'POSITIVE_Z', 'NEGATIVE_Z']:
                    if (prop := opd[key][side]) != getattr(self, f"{side.lower()}_{key.lower()}"):
                        setattr(self, f"{side.lower()}_{key.lower()}", prop)

                        has_changed = True

            else:
                if (prop := opd[key]) != getattr(self, key):
                    setattr(self, key, prop)

                    has_changed = True

        return has_changed

def draw_bend_status(op):
    def draw(self, context):
        layout = self.layout

        row = layout.row(align=True)

        if op.highlighted:

            if op.highlighted['type'][0] in 'is_kink':
                text= "Toggle Kink/Bend"

            elif op.highlighted['type'][0] in 'use_kink_edges':
                text= "Toggle Kink Constrain to Edges"

            elif op.highlighted['type'][0] in 'affect_children':
                text = "Toggle Affect Children"

            elif op.highlighted['type'][0] in 'remove_redundant':
                text = "Toggle Redundant Edge Removal"

            elif op.highlighted['type'][0] in 'mirror_bend':
                text = "Toggle Mirrored Bending"

            elif op.highlighted['type'][0] in 'BISECT':
                text = f"Toggle {op.highlighted['type'][1].title()} Bisecting"

            elif op.highlighted['type'][0] in 'BEND':
                text = f"Toggle {op.highlighted['type'][1].title()} Bending"

            elif op.highlighted['type'][0] in 'ANGLE':
                text = f"Adjus {'Kink' if op.is_kink else 'Bend'} Angle"

            elif op.highlighted['type'][0] in 'OFFSET':
                text = f"Adjust {'Kink' if op.is_kink else 'Bend'} Offset"

            elif op.highlighted['type'][0] in 'LIMIT':
                text = f"Adjust {op.highlighted['type'][1].title()} Bend Limit"

            elif op.highlighted['type'][0] in 'CONTAIN':
                side, axis = op.highlighted['type'][1].split('_')
                text = f"Adjust {side.title()} Bend Containment on {axis}"

            else:
                text = "TODO"

            draw_status_item(row, key='LMB', text=text)
            draw_status_item(row, key='MMB', text="Viewport")
            draw_status_item(row, key='RMB', text="Cancel")
            return

        row.label(text=f"Hyper {'Kink' if op.is_kink else 'Bend'}")

        draw_status_item(row, key='LMB', text="Finish")
        draw_status_item(row, key='MMB', text="Viewport")
        draw_status_item(row, key='RMB', text="Cancel")

        row.separator(factor=10)

        if op.dim_data['POSITIVE_X']:
            draw_status_item(row, key='Q', text=f"Toggle {'Bend' if op.is_kink else 'Kink'}")

        if not op.is_kink and (op.positive_bisect or op.negative_bisect):
            if op.mirror_bend:
                draw_status_item(row, key='MMB_SCROLL', text="Segments", prop=op.positive_segments, gap=2)

            elif op.positive_bisect and op.negative_bisect:
                draw_status_item(row, key='MMB_SCROLL', text=f"({op.mouse_side.lower()}) Segments", prop=getattr(op, f"{op.mouse_side.lower()}_segments"), gap=2)

            elif op.positive_bisect:
                draw_status_item(row, key='MMB_SCROLL', text="Segments", prop=op.positive_segments, gap=2)

            else:
                draw_status_item(row, key='MMB_SCROLL', text="Segments", prop=op.negative_segments, gap=2)

        if op.has_children:
            draw_status_item(row, active=op.affect_children, key='A', text="Affect Children", gap=2 if op.dim_data['POSITIVE_X'] else 0)

        if op.is_kink:
            draw_status_item(row, active=op.use_kink_edges, key='E', text="Use Kink Edges", gap=2)

        elif op.dim_data['POSITIVE_X']:
            draw_status_item(row, active=op.positive_bisect, key='B', text="Bisect (positive)", gap=2)

        draw_status_item(row, active=op.contain, key='C', text="Contain", gap=2 if op.dim_data['POSITIVE_X'] or op.has_children else 0)

        if op.contain:
            draw_status_item(row, active=op.contain_locked, key='X', text="Locked Containment", gap=2)

        if op.is_kink or op.positive_bisect or op.negative_bisect:
            draw_status_item(row, active=op.remove_redundant, key='R', text="Remove Redundant", gap=2)

        draw_status_item(row, active=op.active.show_wire, key='W', text="Show Object Wireframe", gap=2)

        draw_status_item(row, active=op.wireframe, key=['SHIFT', 'W'], text=f"Show pre-{'Kink' if op.is_kink else 'Bend'} Wireframe", gap=2)

    return draw

class HyperBend(bpy.types.Operator, Settings, HyperBendGizmoManager):
    bl_idname = "machin3.hyper_bend"
    bl_label = "MACHIN3: Hyper Bend"
    bl_description = "Hyper Bend"
    bl_options = {'REGISTER', 'UNDO'}

    affect_children: BoolProperty(name="Kink/Bend Children too", default=True)
    has_children: BoolProperty(name="Has Children", default=False)
    is_kink: BoolProperty(name="Kind instead of Bend", description="Toggle between Kink and Bend Mode", default=False)
    use_kink_edges: BoolProperty(name="Use Edge Dirs for Kinking", default=False)
    def update_angle(self, context):
        if self.avoid_update:
            self.avoid_update = False
            return

        if self.angle_presets != 'CUSTOM':
            self.avoid_update = True
            self.angle_presets = 'CUSTOM'

    def update_angle_presets(self, context):
        if self.avoid_update:
            self.avoid_update = False
            return

        if self.angle_presets != 'CUSTOM':
            self.avoid_update = True

            if self.angle < 0:
                self.angle = -float(self.angle_presets)
            else:
                self.angle = float(self.angle_presets)

    def update_negate_angle(self, context):
        if self.avoid_update:
            self.avoid_update = False
            return

        if self.negate_angle:
            self.avoid_update = True
            self.angle = - self.angle

            self.avoid_update = True
            self.negate_angle = False

    angle: FloatProperty(name="Angle", description="Bend Angle", default=0, min=-360, max=360, step=10, update=update_angle)
    angle_presets: EnumProperty(name="Angle Presets", description="Bend Angle Presets", items=bend_angle_presets, default='CUSTOM', update=update_angle_presets)
    negate_angle: BoolProperty(name="Negate the Angle", default=False, update=update_negate_angle)
    def update_reset_offset(self, context):
        if self.avoid_update:
            self.avoid_update = False
            return

        if self.reset_offset:
            self.offset = 0

            self.avoid_update = True
            self.reset_offset = False

    offset: FloatProperty(name="Offset", default=0, step=0.1)
    reset_offset: BoolProperty(name="Reset the Offset", default=False, update=update_reset_offset)
    limit_angle: BoolProperty(name="Limit the Angle", default=False)
    positive_bend: BoolProperty(name="Positive Side Bend", default=True)
    positive_bisect: BoolProperty(name="Positive Side Bisect", default=True)
    positive_limit: FloatProperty(name="Positive Side Limit", default=1, min=0, max=1, step=0.1)
    positive_segments: IntProperty(name="Positive Side Segments", default=6, min=0)
    negative_bend: BoolProperty(name="Negative Side Bend", default=False)
    negative_bisect: BoolProperty(name="Negative Side Bisect", default=False)
    negative_limit: FloatProperty(name="Negative Side Limit", default=1, min=0, max=1, step=0.1)
    negative_segments: IntProperty(name="Negative Side Segments", default=6, min=0)
    remove_redundant: BoolProperty(name="Remove Redundant Edges", description="Remove Redundnat Edges after Bending", default=True)
    wireframe: BoolProperty(name="Show Pre-Bend Wireframe", default=True)
    contain: BoolProperty(name="Contain the Bend", description="Contain the Bend on Y and/or Z", default=False)
    contain_locked: BoolProperty(name="Fixed the out-of-containment regions", default=False)
    positive_y_contain: FloatProperty(name="Positive Y Contain", default=1, min=0, max=1, step=0.1)
    negative_y_contain: FloatProperty(name="Negative Y Contain", default=1, min=0, max=1, step=0.1)
    positive_z_contain: FloatProperty(name="Positive Z Contain", default=1, min=0, max=1, step=0.1)
    negative_z_contain: FloatProperty(name="Negative Z Contain", default=1, min=0, max=1, step=0.1)

    def update_mirror_bend(self, context):
        if not self.mirror_bend:
            self.negative_limit = self.positive_limit
            self.negative_segments = self.positive_segments

    mirror_bend: BoolProperty(name="Mirror the Bend", default=False, update=update_mirror_bend)
    avoid_update: BoolProperty()
    passthrough = None

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            active = context.active_object
            return active and active.type == 'MESH'

    def draw(self, context):
        layout = self.layout

        column = layout.column()

        if self.has_children:
            split = column.split(factor=0.5, align=True)
            row = split.row(align=True)
            row.prop(self, 'is_kink', text='Kink' if self.is_kink else 'Bend', toggle=True)

            split.prop(self, 'affect_children', text='Affect Children', toggle=True)

        else:
            row = column.row(align=True)
            row.prop(self, 'is_kink', text='Kink' if self.is_kink else 'Bend', toggle=True)

        if self.is_kink:
            row.prop(self, 'use_kink_edges', text='', toggle=True, icon='MOD_SIMPLIFY')

        column = layout.column(align=True)
        row = column.row(align=True)
        row.active = self.angle_presets != 'CUSTOM'
        row.prop(self, 'angle_presets', expand=True)

        split = column.split(factor=0.5, align=True)
        row = split.row(align=True)
        r = row.row(align=True)
        r.active = self.angle_presets == 'CUSTOM'
        r.prop(self, 'angle')
        row.prop(self, 'negate_angle', text='', icon='FILE_REFRESH', toggle=True)

        row = split.row(align=True)
        row.prop(self, 'offset')
        r = row.row(align=True)
        r.active = bool(self.offset)
        r.prop(self, 'reset_offset', text='', icon='LOOP_BACK')

        if not self.is_kink:

            split = column.split(factor=0.5, align=True)
            split.prop(self, 'positive_bend', text="Bend", toggle=True)
            r = split.row(align=True)
            r.active = self.positive_bend or self.positive_bisect
            r.prop(self, 'positive_limit', text="Limit")

            rr = r.row(align=True)
            rr.active = self.positive_limit < 1 or (not self.mirror_bend and self.negative_limit < 1)
            rr.prop(self, 'limit_angle', text='', icon='GP_SELECT_BETWEEN_STROKES')

            row = column.row(align=True)
            row.prop(self, 'positive_bisect', text="Bisect", toggle=True)

            r = row.row(align=True)
            r.active = self.positive_bisect
            r.prop(self, 'positive_segments', text="Segments")

            column = layout.column()
            row = column.row()
            row.prop(self, 'mirror_bend', toggle=True)

            if not self.mirror_bend:
                column = layout.column(align=True)
                row = column.row(align=True)
                row.prop(self, 'negative_bend', text="Bend", toggle=True)

                r = row.row(align=True)
                r.active = self.negative_bend or self.negative_bisect
                r.prop(self, 'negative_limit', text="Limit", toggle=True)

                row = column.row(align=True)
                row.prop(self, 'negative_bisect', text="Bisect", toggle=True)
                r = row.row(align=True)
                r.active = self.negative_bisect
                r.prop(self, 'negative_segments', text="Segments")

        column = layout.column(align=True)
        column.prop(self, 'contain', text=f"Contain the {'Kink' if self.is_kink else 'Bend'}", toggle=True)

        if self.contain:
            row = column.row(align=True)
            row.prop(self, 'negative_y_contain', text='Y- Contain')
            row.prop(self, 'positive_y_contain', text='Y+ Contain')

            row = column.row(align=True)
            row.prop(self, 'negative_z_contain', text='Z- Contain')
            row.prop(self, 'positive_z_contain', text='Z+ Contain')

        column = layout.column()
        row = column.row()
        row.prop(self, 'remove_redundant', text="Remove Redundant Edges", toggle=True)

    def draw_HUD(self, context):
        if context.area == self.area:
            opd = self.operator_data

            if opd['show_HUD']:
                offset = 0

                if self.has_children:
                    offset -= 18

                if self.angle:
                    offset -= 18

                    if self.offset:
                        offset -= 18

                if self.is_kink and self.use_kink_edges:
                    offset -= 18

                else:

                    if self.positive_bisect or self.negative_bisect:
                        offset -= 18

                    if self.positive_bisect and self.negative_bisect and (self.positive_segments != self.negative_segments) and not self.mirror_bend:
                        offset -= 18

                if (self.is_kink or self.positive_bisect or self.negative_bisect) and self.remove_redundant:
                        offset -= 18

                if self.wireframe:
                    offset -= 18

                ui_scale = get_scale(context)
                center = not self.angle

                if center:
                    HUD = Vector(self.gizmo_props['loc2d']) + Vector((0, 90)) * ui_scale

                else:
                    HUD = Vector(self.gizmo_props['loc2d']) + Vector((20, 90)) * ui_scale

                color = yellow if self.is_kink or self.positive_bend or self.negative_bend else white

                dims = Vector((0, 0))

                if self.contain:
                    title = "🔒Contained " if self.contain_locked else "Contained "
                    titledims = draw_label(context, title=title, coords=HUD, offset=offset, center=center, color=white)

                    if center:
                        HUD.x -= titledims.x / 2

                    if self.contain_locked:
                        dims += draw_label(context, title="locked ", coords=Vector((HUD.x + titledims.x, HUD.y)), offset=offset, center=False, size=10, color=white, alpha=0.5)

                    dims += draw_label(context, title=f"Hyper {'Kink' if self.is_kink else 'Bend'} ", coords=Vector((HUD.x + titledims.x + dims.x, HUD.y)), offset=offset, center=False, color=color)

                else:
                    titledims = draw_label(context, title=f"Hyper {'Kink' if self.is_kink else 'Bend'} ", coords=HUD, offset=offset, center=center, color=color)

                    if center:
                        HUD.x -= titledims.x / 2

                if not self.is_kink and (self.positive_bisect or self.negative_bisect):
                    draw_label(context, title="+ Bisect", coords=Vector((HUD.x + titledims.x + dims.x, HUD.y)), offset=offset, center=False, size=10, alpha=0.5)

                if self.angle:
                    offset += 18

                    dims = draw_label(context, title="Angle: ", coords=HUD, offset=offset, center=False, alpha=0.5)
                    draw_label(context, title=dynamic_format(self.angle, decimal_offset=1), coords=Vector((HUD.x + dims.x, HUD.y)), offset=offset, center=False, alpha=1)

                    if self.offset:
                        offset += 18

                        dims = draw_label(context, title="Offset: ", coords=HUD, offset=offset, center=False, alpha=0.5)
                        draw_label(context, title=dynamic_format(self.offset, decimal_offset=1), coords=Vector((HUD.x + dims.x, HUD.y)), offset=offset, center=False, alpha=1)

                if not self.is_kink and (self.positive_bisect or self.negative_bisect):
                    offset += 18

                    if self.positive_bisect and self.negative_bisect and (self.positive_segments != self.negative_segments) and not self.mirror_bend:

                        dims = draw_label(context, title="Segments: ", coords=HUD, offset=offset, center=False, alpha=1 if self.mouse_side == 'POSITIVE' else 0.5)
                        dims += draw_label(context, title=str(self.positive_segments), coords=Vector((HUD.x + dims.x, HUD.y)), offset=offset, center=False, alpha=1)
                        draw_label(context, title=" positive", coords=Vector((HUD.x + dims.x, HUD.y)), offset=offset, center=False, size=10, alpha=0.5 if self.mouse_side == 'POSITIVE' else 0.3)

                        offset += 18

                        dims = draw_label(context, title="Segments: ", coords=HUD, offset=offset, center=False, alpha=1 if self.mouse_side == 'NEGATIVE' else 0.5)
                        dims += draw_label(context, title=str(self.negative_segments), coords=Vector((HUD.x + dims.x, HUD.y)), offset=offset, center=False, alpha=1)
                        draw_label(context, title=" negative", coords=Vector((HUD.x + dims.x, HUD.y)), offset=offset, center=False, size=10, alpha=0.5 if self.mouse_side == 'NEGATIVE' else 0.3)

                    elif self.positive_bisect:
                        dims = draw_label(context, title="Segments: ", coords=HUD, offset=offset, center=False, alpha=0.5)
                        draw_label(context, title=str(self.positive_segments), coords=Vector((HUD.x + dims.x, HUD.y)), offset=offset, center=False, alpha=1)

                    elif self.negative_bisect:
                        dims = draw_label(context, title="Segments: ", coords=HUD, offset=offset, center=False, alpha=0.5)
                        draw_label(context, title=str(self.negative_segments), coords=Vector((HUD.x + dims.x, HUD.y)), offset=offset, center=False, alpha=1)

                if self.is_kink and self.use_kink_edges:
                    offset += 18

                    draw_label(context, title="Use Kink Edges", coords=HUD, offset=offset, center=False, color=normal, alpha=1)

                if self.has_children:
                    offset += 18

                    color, alpha = (green, 1) if self.affect_children else (white, 0.2)
                    draw_label(context, title=f"{'Affect' if self.affect_children else 'Has'} Children", coords=HUD, offset=offset, center=False, color=color, alpha=alpha)

                if (self.is_kink or self.positive_bisect or self.negative_bisect) and self.remove_redundant:
                    offset += 18

                    draw_label(context, title="Remove Redundant", coords=HUD, offset=offset, center=False, color=red, alpha=1)

                if self.wireframe:
                    offset += 18

                    draw_label(context, title="Wireframe", coords=HUD, offset=offset, center=False, color=blue, alpha=1)

    def draw_VIEW3D(self, context):
        if context.area == self.area:
            for axis in self.view3d_bend_axes:
                draw_vector(axis * 1.5, mx=self.cmx, color=green, alpha=0.5, width=2, fade=True)

            if (self.operator_data['show_HUD'] or self.contain or (self.positive_limit or self.negative_limit)) and self.wireframe:
                draw_batch(self.batch, color=white, width=1, alpha=0.1)

            if self.contain and self.contain_locked and self.locked_coords:
                draw_points(self.locked_coords, mx=self.cmx, color=black, size=5, alpha=0.75)

    def modal(self, context, event):
        if ignore_events(event):
            return {'PASS_THROUGH'}

        if not context.area:
            for obj, bm in self.initbms.items():
                bm.to_mesh(obj.data)
            return {'CANCELLED'}

        context.area.tag_redraw()

        opd = self.operator_data
        gp = self.gizmo_props

        self.highlighted = self.get_highlighted(context)

        events = ['MOUSEMOVE', 'C', 'W']

        if self.dim_data['POSITIVE_X']:
            events.append('Q')

            if not self.is_kink:
                events.append('B')

        if self.is_kink:
            events.append('E')

        if self.has_children:
            events.append('A')

        if self.contain:
            events.append('X')

        if self.is_kink or self.positive_bisect or self.negative_bisect:
            events.append('R')

        if event.type in events or scroll(event, key=True):

            if event.type == 'MOUSEMOVE':

                get_mouse_pos(self, context, event, hud=False)

                if self.passthrough:
                    self.passthrough = False

                    gp['loc2d'] = get_location_2d(context, self.cmx.to_translation(), debug=False)

                    gp['show'] = True
                    opd['show_HUD'] = True

                    gp['push_update'] = "NAVIGATION_PASSTHROUGH_LOC2D_UPDATE"

                if opd['show_HUD']:
                    self.mouse_side = self.get_mouse_side(context)

                    if self.mouse_side != self.last_mouse_side:
                        self.last_mouse_side = self.mouse_side
                        force_ui_update(context)

            if opd['show_HUD']:

                if scroll(event, key=True):
                    if self.positive_bisect and self.negative_bisect:
                        side = 'POSITIVE' if self.mirror_bend else self.mouse_side

                    elif self.positive_bisect:
                        side = 'POSITIVE'
                    else:
                        side = 'NEGATIVE'

                    if scroll_up(event, key=True):
                        opd['SEGMENTS'][side] += 10 if event.ctrl else 1

                    else:
                        opd['SEGMENTS'][side] -= 10 if event.ctrl else 1

                elif event.type == 'C' and event.value == 'PRESS':
                    opd['contain'] = not opd['contain']

                    if opd['contain']:

                        if opd['mirror_bend']:
                            opd['mirror_bend'] = False
                            opd['BISECT']['NEGATIVE'] = False
                            opd['BEND']['NEGATIVE'] = False

                        if opd['BEND']['NEGATIVE'] and opd['BEND']['POSITIVE']:
                            opd['BISECT']['NEGATIVE'] = False
                            opd['BEND']['NEGATIVE'] = False

                elif event.type == 'X' and event.value == 'PRESS':
                    self.contain_locked = not self.contain_locked
                    self.modal_bend()

                elif event.type == 'W' and event.value == 'PRESS':

                    if event.shift:
                        self.wireframe = not self.wireframe

                    else:
                        self.active.show_wire = not self.active.show_wire

                    force_ui_update(context)

                elif (self.positive_bisect or self.negative_bisect) and event.type == 'R' and event.value == 'PRESS':
                    opd['remove_redundant'] = not opd['remove_redundant']

                elif event.type == 'Q' and event.value == 'PRESS':
                    opd['is_kink'] = not opd['is_kink']

                elif event.type == 'E' and event.value == 'PRESS':
                    opd['use_kink_edges'] = not opd['use_kink_edges']

                elif event.type == 'A' and event.value == 'PRESS':
                    opd['affect_children'] = not opd['affect_children']

                elif event.type == 'B' and event.value == 'PRESS':
                    opd['BISECT']['POSITIVE'] = not opd['BISECT']['POSITIVE']

                if event.type != 'MOUSEMOVE':
                    opd['push_update'] = True

        if self.operator_data['push_update']:

            if self.push_updates_back_to_operator():
                self.modal_bend()

        if navigation_passthrough(event, alt=True, wheel=False):
            gp['show'] = False
            opd['show_HUD'] = False

            self.passthrough = True
            return {'PASS_THROUGH'}

        finish_events = ['SPACE']

        if not self.highlighted:
            finish_events.append('LEFTMOUSE')

        if event.type in finish_events and event.value == 'PRESS':

            self.finish(context)
            self.save_settings()
            return {'FINISHED'}

        elif event.type in ['RIGHTMOUSE', 'ESC'] and event.value == 'PRESS':
            self.finish(context)

            for obj, bm in self.initbms.items():
                bm.to_mesh(obj.data)

            return {'CANCELLED'}

        if gizmo_selection_passthrough(self, event):
            return {'PASS_THROUGH'}

        return {'RUNNING_MODAL'}

    def finish(self, context):
        finish_modal_handlers(self)

        restore_gizmos(self)

        finish_status(self)

        self.gizmo_group_finish(context)

        force_ui_update(context)

    def invoke(self, context, event):
        self.init_settings(props=['is_kink', 'positive_bisect', 'positive_bend', 'positive_segments', 'negative_bisect', 'negative_bend', 'negative_segments', 'remove_redundant', 'affect_children'])
        self.load_settings()

        self.active = context.active_object
        self.objects = [self.active]
        self.highlighted = None
        self.last_highlighted = None

        self.mod_dict = self.get_children(context, self.active, self.objects)

        self.mx = self.active.matrix_world.copy()
        self.cmx = context.scene.cursor.matrix
        self.loc, rot, _ = self.cmx.decompose()

        self.deltamx = self.cmx.inverted_safe() @ self.mx

        self.initbms = {}

        for obj in self.objects:
            self.initbms[obj] = self.create_bmesh(obj)[0]

        self.gizmo_group_init(context, self.loc, rot)

        self.dim_data = self.get_dimensions_data(self.initbms[self.active], self.deltamx, self.loc, rot, modal=True, debug=False)

        self.verify_init_props(debug=False)

        self.cursor_x_dir = rot @ Vector((1, 0, 0))

        get_mouse_pos(self, context, event, hud=False)

        self.mouse_side = self.get_mouse_side(context)
        self.last_mouse_side = self.mouse_side

        self.locked_coords = []

        hide_gizmos(self, context)

        init_status(self, context, func=draw_bend_status(self))

        self.modal_bend()

        init_modal_handlers(self, context, hud=True, view3d=True)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        active = context.active_object
        objects = [active]

        context.evaluated_depsgraph_get()

        mod_dict = self.get_children(context, active, objects)

        for obj in objects:
            is_active = obj == active

            mx = obj.matrix_world.copy()
            cmx = context.scene.cursor.matrix
            deltamx = cmx.inverted_safe() @ mx

            bm, vgroups, edge_glayer, face_glayer = self.create_bmesh(obj)

            if is_active:
                loc, rot, _ = cmx.decompose()
                self.dim_data = self.get_dimensions_data(bm, deltamx, loc, rot, modal=False, debug=False)

            if self.mirror_bend:
                self.negative_bend = self.positive_bend
                self.negative_bisect = self.positive_bisect

            if mx != cmx:
                obj.matrix_world = cmx
                bmesh.ops.transform(bm, matrix=deltamx, verts=bm.verts, use_shapekey=False)

            if self.is_kink:
                self.kink(bm, vgroups, angle=self.angle, offset=self.offset, cmx=cmx, debug=False)

            else:

                if self.positive_bisect or self.negative_bisect:
                    self.bisect(bm, vgroups, force_final_cut=not is_active, debug=False)

                if self.angle:

                    if self.positive_bend or self.negative_bend:
                        self.bend(bm, angle=self.angle, offset=self.offset, debug=False)

            if self.angle and is_active:
                self.process_mesh(bm, edge_glayer, face_glayer, obj.HC.objtype, self.angle)

            if mx != cmx:
                bmesh.ops.transform(bm, matrix=deltamx.inverted_safe(), verts=bm.verts, use_shapekey=False)
                obj.matrix_world = mx

            bm.to_mesh(obj.data)
            bm.free()

            if not self.is_kink and not is_active and obj in mod_dict:
                mods = mod_dict[obj]

                for mod in mods:
                    if mod.type == 'BOOLEAN' and mod.solver == 'FAST':
                        mod.solver = 'EXACT'
                        mod.use_hole_tolerant = True

        return {'FINISHED'}

    def modal_bend(self):
        for obj in self.objects:
            is_active = obj == self.active

            if not is_active and not (self.has_children and self.affect_children):
                bm = self.initbms[obj]
                bm.to_mesh(obj.data)
                continue

            mx = obj.matrix_world.copy()
            cmx = self.cmx
            deltamx = cmx.inverted_safe() @ mx

            bm, vgroups, edge_glayer, face_glayer = self.copy_init_bmesh(obj)

            if mx != cmx:
                obj.matrix_world = cmx
                bmesh.ops.transform(bm, matrix=deltamx, verts=bm.verts, use_shapekey=False)

            if self.is_kink:
                self.kink(bm, vgroups, angle=self.angle, offset=self.offset, cmx=cmx, modal=is_active, debug=False)

            else:

                if self.positive_bisect or self.negative_bisect:
                    self.bisect(bm, vgroups, force_final_cut=not is_active, modal=is_active, debug=False)

                if is_active:
                    bm.to_mesh(obj.data)
                    self.batch = get_batch_from_mesh(obj.data, mx=self.cmx)

                if self.angle:
                    if self.positive_bend or self.negative_bend:
                        self.bend(bm, angle=self.angle, offset=self.offset, debug=False)

            if self.angle and is_active:
                self.process_mesh(bm, edge_glayer, face_glayer, obj.HC.objtype, self.angle)

            if mx != cmx:
                bmesh.ops.transform(bm, matrix=deltamx.inverted_safe(), verts=bm.verts, use_shapekey=False)
                obj.matrix_world = mx

            bm.to_mesh(obj.data)

            if not self.is_kink and not is_active and obj in self.mod_dict:
                mods = self.mod_dict[obj]

                for mod in mods:
                    if mod.type == 'BOOLEAN' and mod.solver == 'FAST':
                        mod.solver = 'EXACT'
                        mod.use_hole_tolerant = True

    def get_children(self, context, active, objects, debug=False):
        obj_tree = []
        mod_dict = {}

        get_object_tree(active, obj_tree, mod_objects=True, mod_dict=mod_dict, mod_type_ignore=['MIRROR'], include_hidden=('VIEWLAYER', 'COLLECTION'), debug=False)

        mesh_objects = set(obj for obj in mod_dict if obj.type == 'MESH')
        mesh_objects.update(obj for obj in obj_tree if obj.type == 'MESH')

        if active in mesh_objects:
            mesh_objects.remove(active)

        self.has_children = bool(mesh_objects)

        if mesh_objects:
            objects.extend(mesh_objects)

        if debug:
            print()
            print("mesh children (incl. mod objects):" )
            for obj in objects:
                print(obj.name, obj.name in context.scene.objects)

        return mod_dict

    def create_bmesh(self, active):
        bm = bmesh.new()
        bm.from_mesh(active.data)
        bm.normal_update()

        vgroups = bm.verts.layers.deform.verify()
        edge_glayer, face_glayer = ensure_gizmo_layers(bm)

        return bm, vgroups, edge_glayer, face_glayer

    def copy_init_bmesh(self, obj):
        bm = self.initbms[obj].copy()
        bm.normal_update()

        vgroups = bm.verts.layers.deform.verify()
        edge_glayer, face_glayer = ensure_gizmo_layers(bm)

        return bm, vgroups, edge_glayer, face_glayer

    def get_dimensions_data(self, bm, deltamx, loc, rot, modal=False, debug=False):
        dim_data = {'POSITIVE_X': 0,
                    'NEGATIVE_X': 0,
                    'POSITIVE_Y': 0,
                    'NEGATIVE_Y': 0,
                    'POSITIVE_Z': 0,
                    'NEGATIVE_Z': 0}

        dim_data['NEGATIVE_X'] = 0
        dim_data['POSITIVE_X'] = 0

        dim_data['NEGATIVE_Y'] = 0
        dim_data['POSITIVE_Y'] = 0

        dim_data['NEGATIVE_Z'] = 0
        dim_data['POSITIVE_Z'] = 0

        for v in bm.verts:
            co = deltamx @ v.co

            if co.x < dim_data['NEGATIVE_X']:
                dim_data['NEGATIVE_X'] = co.x

            if co.x > dim_data['POSITIVE_X']:
                dim_data['POSITIVE_X'] = co.x

            if co.y < dim_data['NEGATIVE_Y']:
                dim_data['NEGATIVE_Y'] = co.y

            if co.y > dim_data['POSITIVE_Y']:
                dim_data['POSITIVE_Y'] = co.y

            if co.z < dim_data['NEGATIVE_Z']:
                dim_data['NEGATIVE_Z'] = co.z

            if co.z > dim_data['POSITIVE_Z']:
                dim_data['POSITIVE_Z'] = co.z

        if debug:
            printd(dim_data)

        negative_x_limit_co = loc + rot @ Vector((dim_data['NEGATIVE_X'], 0, 0))
        positive_x_limit_co = loc + rot @ Vector((dim_data['POSITIVE_X'], 0, 0))

        if debug:
            draw_point(negative_x_limit_co, color=red, alpha=0.5, modal=False)
            draw_point(positive_x_limit_co, color=red, modal=False)

        negative_y_limit_co = loc + rot @ Vector((0, dim_data['NEGATIVE_Y'], 0))
        positive_y_limit_co = loc + rot @ Vector((0, dim_data['POSITIVE_Y'], 0))

        if debug:
            draw_point(negative_y_limit_co, color=green, alpha=0.5, modal=False)
            draw_point(positive_y_limit_co, color=green, modal=False)

        negative_z_limit_co = loc + rot @ Vector((0, 0, dim_data['NEGATIVE_Z']))
        positive_z_limit_co = loc + rot @ Vector((0, 0, dim_data['POSITIVE_Z']))

        if debug:
            draw_point(negative_z_limit_co, color=blue, alpha=0.5, modal=False)
            draw_point(positive_z_limit_co, color=blue, modal=False)

        if modal:

            ymindir = Vector((0, dim_data['NEGATIVE_Y'], 0))
            ymaxdir = Vector((0, dim_data['POSITIVE_Y'], 0))

            self.view3d_bend_axes = [ymindir, ymaxdir]

            self.gizmo_data['OFFSET']['z_factor'] = abs(dim_data['NEGATIVE_Z']) + dim_data['POSITIVE_Z']

            pos_rot = rot.copy()
            pos_rot.rotate(Quaternion(Vector(rot @ Vector((0, 1, 0))), radians(90)))

            self.gizmo_data['LIMIT']['POSITIVE']['loc'] = positive_x_limit_co
            self.gizmo_data['LIMIT']['POSITIVE']['rot'] = pos_rot
            self.gizmo_data['LIMIT']['POSITIVE']['distance'] = dim_data['POSITIVE_X']

            neg_rot = rot.copy()
            neg_rot.rotate(Quaternion(Vector(rot @ Vector((0, 1, 0))), radians(-90)))

            self.gizmo_data['LIMIT']['NEGATIVE']['loc'] = negative_x_limit_co
            self.gizmo_data['LIMIT']['NEGATIVE']['rot'] = neg_rot
            self.gizmo_data['LIMIT']['NEGATIVE']['distance'] = abs(dim_data['NEGATIVE_X'])

            pos_y_rot = rot.copy()
            pos_y_rot.rotate(Quaternion(Vector(rot @ Vector((-1, 0, 0))), radians(90)))

            self.gizmo_data['CONTAIN']['POSITIVE_Y']['loc'] = positive_y_limit_co
            self.gizmo_data['CONTAIN']['POSITIVE_Y']['rot'] = pos_y_rot
            self.gizmo_data['CONTAIN']['POSITIVE_Y']['distance'] = abs(dim_data['POSITIVE_Y'])

            neg_y_rot = rot.copy()
            neg_y_rot.rotate(Quaternion(Vector(rot @ Vector((-1, 0, 0))), radians(-90)))

            self.gizmo_data['CONTAIN']['NEGATIVE_Y']['loc'] = negative_y_limit_co
            self.gizmo_data['CONTAIN']['NEGATIVE_Y']['rot'] = neg_y_rot
            self.gizmo_data['CONTAIN']['NEGATIVE_Y']['distance'] = abs(dim_data['NEGATIVE_Y'])

            pos_z_rot = rot.copy()

            self.gizmo_data['CONTAIN']['POSITIVE_Z']['loc'] = positive_z_limit_co
            self.gizmo_data['CONTAIN']['POSITIVE_Z']['rot'] = pos_z_rot
            self.gizmo_data['CONTAIN']['POSITIVE_Z']['distance'] = abs(dim_data['POSITIVE_Z'])

            neg_z_rot = rot.copy()
            neg_z_rot.rotate(Quaternion(Vector(rot @ Vector((1, 0, 0))), radians(180)))

            self.gizmo_data['CONTAIN']['NEGATIVE_Z']['loc'] = negative_z_limit_co
            self.gizmo_data['CONTAIN']['NEGATIVE_Z']['rot'] = neg_z_rot
            self.gizmo_data['CONTAIN']['NEGATIVE_Z']['distance'] = abs(dim_data['NEGATIVE_Z'])

        return dim_data

    def verify_init_props(self, debug=False):

        opd = self.operator_data

        if debug:
            print()
            print("initial positive:", self.positive_bisect, self.positive_bend, opd['BISECT']['POSITIVE'], opd['BEND']['POSITIVE'])
            print("initial negative:", self.negative_bisect, self.negative_bend, opd['BISECT']['NEGATIVE'], opd['BEND']['NEGATIVE'])
            print("initial kink:", self.is_kink, opd['is_kink'])

        positive_distance = self.dim_data['POSITIVE_X']
        negative_distance = self.dim_data['NEGATIVE_X']

        if not positive_distance:
            if opd['BISECT']['POSITIVE']:
                opd['BISECT']['POSITIVE'] = False

                if debug:
                    print(" disabled positive bend")

            if opd['BEND']['POSITIVE']:
                opd['BEND']['POSITIVE'] = False

                if debug:
                    print(" disabled positive bisect")

        if not negative_distance:
            if opd['BISECT']['NEGATIVE']:
                opd['BISECT']['NEGATIVE'] = False

                if debug:
                    print(" disabled negative bend")

            if opd['BEND']['NEGATIVE']:
                opd['BEND']['NEGATIVE'] = False

                if debug:
                    print(" disabled negative bisect")

        if not positive_distance and opd['is_kink']:
            opd['is_kink'] = False

            if debug:
                print("disabled kink")

        if not any([opd['BISECT']['POSITIVE'], opd['BEND']['POSITIVE'], opd['BISECT']['NEGATIVE'], opd['BEND']['NEGATIVE']]):
            if positive_distance:
                opd['BISECT']['POSITIVE'] = True
                opd['BEND']['POSITIVE'] = True

                if debug:
                    print(" force enabled positive bisect and bend")

            elif negative_distance:
                opd['BISECT']['NEGATIVE'] = True
                opd['BEND']['NEGATIVE'] = True

                if debug:
                    print(" force enabled negative bisect and bend")

        self.push_updates_back_to_operator()

        if debug:
            print()
            print("verified positive:", self.positive_bisect, self.positive_bend, opd['BISECT']['POSITIVE'], opd['BEND']['POSITIVE'])
            print("verified negative:", self.negative_bisect, self.negative_bend, opd['BISECT']['NEGATIVE'], opd['BEND']['NEGATIVE'])
            print("verified kink:", self.is_kink, opd['is_kink'])

    def get_side_data(self, bm, positive=True, negative=True, debug=False):
        data = {'POSITIVE': {'verts': {}},

                'NEGATIVE': {'verts': {}}
                }

        for v in bm.verts:
            if positive and v.co.x > 0:
                data['POSITIVE']['verts'][v] = {'distance': v.co.x}

            elif negative and v.co.x < 0:
                data['NEGATIVE']['verts'][v] = {'distance': -v.co.x}

        if debug:
            printd(data, name="sides")

        return data

    def get_side_props(self, side):
        if side == 'POSITIVE' or self.mirror_bend:
            limit = self.positive_limit
            segments = self.positive_segments + 1
        else:
            limit = self.negative_limit
            segments = self.negative_segments + 1

        return 1 if side == 'POSITIVE' else -1 , limit, segments

    def get_mouse_side(self, context):
        self.view_origin, self.view_dir = get_view_origin_and_dir(context, self.mouse_pos)

        i = intersect_line_line(self.loc, self.loc + self.cursor_x_dir, self.view_origin, self.view_origin + self.view_dir)

        if i:
            mousedir = (i[0] - self.loc).normalized()

            dot = self.cursor_x_dir.dot(mousedir)
            return 'POSITIVE' if dot >= 0 else 'NEGATIVE'

    def get_out_of_cointainment_verts(self, bm, included_verts, consider_offset=True, buffer=0.0001, debug=False):

        offset = self.offset if consider_offset else 0

        negative_y_max = self.dim_data['NEGATIVE_Y'] * self.negative_y_contain
        positive_y_max = self.dim_data['POSITIVE_Y'] * self.positive_y_contain

        negative_z_max = self.dim_data['NEGATIVE_Z'] * self.negative_z_contain
        positive_z_max = self.dim_data['POSITIVE_Z'] * self.positive_z_contain

        if debug:
            print()
            print("negative y max:", negative_y_max)
            print("positive y max:", positive_y_max)
            print("negative z max:", negative_z_max)
            print("positive z max:", positive_z_max)

        out_of_containment = []

        for v in bm.verts:

            if v in included_verts:
                continue

            elif self.dim_data['NEGATIVE_Y'] - buffer < v.co.y < negative_y_max - buffer:
                out_of_containment.append(v)

                if debug:
                    print(" added", v.index, "y neg")

            elif positive_y_max + buffer < v.co.y < self.dim_data['POSITIVE_Y'] + buffer:
                out_of_containment.append(v)

                if debug:
                    print(" added", v.index, "y pos")

            elif self.dim_data['NEGATIVE_Z'] - offset - buffer < v.co.z < negative_z_max - offset - buffer:
                out_of_containment.append(v)

                if debug:
                    print(" added", v.index, v.co.z, "z neg")

            elif positive_z_max - offset + buffer < v.co.z < self.dim_data['POSITIVE_Z'] - offset + buffer:
                out_of_containment.append(v)

                if debug:
                    print(" added", v.index, v.co.z, "z pos")

        return out_of_containment

    def get_highlighted(self, context):
        for gzmtype, data in self.gizmo_data.items():

            if 'is_highlight' in data:
                if data['is_highlight']:
                    if self.last_highlighted != data:
                        self.last_highlighted = data

                    force_ui_update(context)
                    return data

            else:
                for direction, gdata in data.items():

                    if gdata['is_highlight']:
                        if self.last_highlighted != gdata:
                            self.last_highlighted = gdata

                        force_ui_update(context)
                        return gdata

        if self.last_highlighted:
            self.last_highlighted = None

            force_ui_update(context)

    def kink(self, bm, vgroups, angle=45, offset=0, cmx=Matrix(), modal=False, debug=False):
        if modal:
            self.locked_coords = []

        geom = [el for seq in [bm.verts, bm.edges, bm.faces] for el in seq]
        ret = bmesh.ops.bisect_plane(bm, geom=geom, dist=0, plane_co=Vector((0, 0, 0)), plane_no=Vector((1, 0, 0)), use_snap_center=False, clear_outer=False, clear_inner=False)

        geom_cut = ret['geom_cut']

        bisect_verts = [el for el in geom_cut if isinstance(el, bmesh.types.BMVert)]
        bisect_edges = [el for el in geom_cut if isinstance(el, bmesh.types.BMEdge)]

        for v in bisect_verts:
            for vgindex, weight in v[vgroups].items():
                if weight != 1 or v.calc_shell_factor() == 1:
                    del v[vgroups][vgindex]

        data = self.get_side_data(bm, positive=True, negative=False, debug=False)

        if offset:
            bmesh.ops.translate(bm, verts=bm.verts, vec=(0.0, 0.0, -offset))

        positive_verts = [v for v in data['POSITIVE']['verts'] if v not in bisect_verts]

        if debug:
            for v in positive_verts:
                draw_point(v.co.copy(), mx=cmx, modal=False)

            for v in bisect_verts:
                draw_point(v.co.copy(), mx=cmx, color=red, modal=False)

        rotmx = Quaternion(Vector((0, 1, 0)), -radians(angle)).to_matrix()

        if self.contain:

            out_of_cointainment_verts = self.get_out_of_cointainment_verts(bm, positive_verts, debug=False)

            remove_bisect_verts = [v for v in bisect_verts if v in out_of_cointainment_verts]
            remove_bisect_edges = [e for e in bisect_edges if all(v in remove_bisect_verts for v in e.verts)]

            if remove_bisect_edges:

                for v in remove_bisect_verts:
                    if not v.is_valid:
                        bisect_verts.remove(v)

            out_of_cointainment_verts = self.get_out_of_cointainment_verts(bm, [], debug=False)

            if modal:
                mx = self.cmx @ Matrix.Translation(Vector((0, 0, self.offset)))

                bm.to_mesh(self.active.data)
                self.batch = get_batch_from_mesh(self.active.data, mx=mx)

                if self.contain and self.contain_locked:
                    self.locked_coords = [Matrix.Translation(Vector((0, 0, self.offset))) @ v.co.copy() for v in out_of_cointainment_verts]

            if self.contain_locked:
                rotate_verts = [v for v in positive_verts if v not in out_of_cointainment_verts]

            else:
                other = set(bm.verts) - set(positive_verts)
                additional = [v for v in other if v in out_of_cointainment_verts]

                rotate_verts = positive_verts + list(additional)

        else:
            rotate_verts = positive_verts

            if modal:
                mx = self.cmx @ Matrix.Translation(Vector((0, 0, self.offset)))

                bm.to_mesh(self.active.data)
                self.batch = get_batch_from_mesh(self.active.data, mx=mx)

        bmesh.ops.rotate(bm, matrix=rotmx, verts=rotate_verts)

        x_dir = Vector((1, 0, 0))

        if debug:
            draw_vector(x_dir, origin=Vector(), mx=cmx, color=red, modal=False)

        x_dir_rot = x_dir.copy()
        x_dir_rot.rotate(Quaternion(Vector((0, 1, 0)), -radians(angle / 2)))

        if debug:
            draw_vector(x_dir_rot, origin=Vector(), mx=cmx, color=green, modal=False)

        for v in bisect_verts:

            rot_dir = x_dir

            if self.use_kink_edges:

                edge_dirs = [(e.other_vert(v).co - v.co).normalized() for e in v.link_edges if e.other_vert(v) not in bisect_verts and e.other_vert(v).co.x < 0]

                if edge_dirs:
                    rot_dir = edge_dirs[0]

            i = intersect_line_plane(v.co, v.co + rot_dir, Vector(), x_dir_rot)

            if i:
                if debug:
                    draw_point(i, mx=cmx, color=green, modal=False)

                v.co = i

        if offset:
            bmesh.ops.translate(bm, verts=bm.verts, vec=(0.0, 0.0, offset))

    def bisect(self, bm, vgroups, force_final_cut=False, modal=False, debug=False):
        if modal:
            self.locked_coords = []

        first_cut = None

        side_data = self.get_side_data(bm, debug=False)

        for side, side_dict in side_data.items():

            if not side_dict['verts'] or (side == 'POSITIVE' and not self.positive_bisect) or (side == 'NEGATIVE' and not self.negative_bisect):
                continue

            side_factor, limit, segments = self.get_side_props(side)

            if debug:
                print()
                print(f"bisecting {side} side {segments - 1} times")

            max_distance = abs(self.dim_data[f"{side}_X"])
            bisect_distance = max_distance * limit

            bisect_verts = []
            bisect_edges = []

            for i in range(segments):

                if i == 0:
                    if first_cut is None:
                        first_cut = True

                    elif first_cut:
                        continue

                reach = (i / segments) * bisect_distance

                geom = [el for seq in [bm.verts, bm.edges, bm.faces] for el in seq]
                ret = bmesh.ops.bisect_plane(bm, geom=geom, dist=0, plane_co=Vector((reach * side_factor, 0, 0)), plane_no=Vector((side_factor, 0, 0)), use_snap_center=False, clear_outer=False, clear_inner=False)

                geom_cut = ret['geom_cut']

                verts = [el for el in geom_cut if isinstance(el, bmesh.types.BMVert)]
                edges = [el for el in geom_cut if isinstance(el, bmesh.types.BMEdge)]

                bisect_verts.extend(verts)
                bisect_edges.extend(edges)

                for v in verts:
                    for vgindex, weight in v[vgroups].items():
                        if weight != 1 or v.calc_shell_factor() == 1:
                            del v[vgroups][vgindex]

                if i == segments - 1 and (limit < 1 or force_final_cut):
                    if debug:
                        print(" additional bisect at the end to delimit the bend")

                    geom = [el for seq in [bm.verts, bm.edges, bm.faces] for el in seq]
                    ret = bmesh.ops.bisect_plane(bm, geom=geom, dist=0, plane_co=Vector((bisect_distance * side_factor, 0, 0)), plane_no=Vector((side_factor, 0, 0)), use_snap_center=False, clear_outer=False, clear_inner=False)

                    geom_cut = ret['geom_cut']

                    verts = [el for el in geom_cut if isinstance(el, bmesh.types.BMVert)]
                    edges = [el for el in geom_cut if isinstance(el, bmesh.types.BMEdge)]

                    bisect_verts.extend(verts)
                    bisect_edges.extend(edges)

                    for v in verts:
                        for vgindex, weight in v[vgroups].items():
                            if weight != 1 or v.calc_shell_factor() == 1:
                                del v[vgroups][vgindex]

            if self.contain and bisect_edges:
                out_of_cointainment_verts = self.get_out_of_cointainment_verts(bm, included_verts=side_dict['verts'], consider_offset=False, debug=False)

                remove_bisect_verts = [v for v in bisect_verts if v in out_of_cointainment_verts]
                remove_bisect_edges = [e for e in bisect_edges if all(v in remove_bisect_verts for v in e.verts)]

                if remove_bisect_edges:
                    bmesh.ops.dissolve_edges(bm, edges=remove_bisect_edges, use_verts=True)

                if modal and self.contain and self.contain_locked:
                    out_of_cointainment_verts = self.get_out_of_cointainment_verts(bm, included_verts=[], consider_offset=False, debug=False)

                    self.locked_coords = [v.co.copy() for v in out_of_cointainment_verts]

    def bend(self, bm, angle=45, offset=0, debug=False):
        side_data = self.get_side_data(bm, debug=False)

        if offset:
            bmesh.ops.translate(bm, verts=bm.verts, vec=(0.0, 0.0, -offset))

        for side, side_dict in side_data.items():

            if not side_dict['verts'] or (side == 'POSITIVE' and not self.positive_bend) or (side == 'NEGATIVE' and not self.negative_bend):
                continue

            if debug:
                print(f"bending {side} side by {angle}")

            side_factor, limit, _ = self.get_side_props(side)

            if limit:
                if debug and limit < 1:
                    print(f"limiting to: {limit * 100}%")

                max_distance = abs(self.dim_data[f"{side}_X"])
                cutoff_distance = max_distance * limit

                bend_factor = radians(self.angle / (max_distance if self.limit_angle else cutoff_distance))

                if debug:
                    print(" max_distance:", max_distance)

                    if limit < 1:
                        print(" cutoff_distance:", cutoff_distance)

                    print(" bend factor:", bend_factor, degrees(bend_factor))

                bend_verts = side_dict['verts']

                if self.contain:
                    bend_verts = side_dict['verts']

                    out_of_cointainment_verts = self.get_out_of_cointainment_verts(bm, included_verts=[], debug=False)

                    for v in out_of_cointainment_verts:
                        bend_verts[v] = {'distance': v.co.x * side_factor}

                else:
                    out_of_cointainment_verts = []

                for v, vdata in bend_verts.items():

                    if self.contain and self.contain_locked and v in out_of_cointainment_verts:
                        continue

                    distance = vdata['distance']

                    theta = distance * bend_factor
                    theta_cutoff = cutoff_distance * bend_factor

                    if distance > cutoff_distance or v in out_of_cointainment_verts:
                        if debug:
                            print(" ", v.index, "angle:", degrees(theta_cutoff))

                        v.co.x = -(v.co.z - 1.0 / bend_factor) * sin(theta_cutoff) * side_factor
                        v.co.z = (v.co.z - 1.0 / bend_factor) * cos(theta_cutoff) + 1.0 / bend_factor

                        rot = Quaternion(Vector((0, 1, 0)), -theta_cutoff * side_factor)
                        push = rot @ Vector((side_factor, 0, 0))

                        delta = distance - cutoff_distance
                        v.co += push * delta

                    else:
                        if debug:
                            print(" ", v.index, "angle:", degrees(theta))

                        v.co.x = -(v.co.z - 1.0 / bend_factor) * sin(theta) * side_factor
                        v.co.z = (v.co.z - 1.0 / bend_factor) * cos(theta) + 1.0 / bend_factor

        if offset:
            bmesh.ops.translate(bm, verts=bm.verts, vec=(0.0, 0.0, offset))

    def process_mesh(self, bm, edge_glayer, face_glayer, objtype, angle):
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.00001)

        if not self.is_kink and angle in [360, -360]:

            loose_faces = [f for f in bm.faces if all([not e.is_manifold for e in f.edges])]

            if loose_faces:
                bmesh.ops.delete(bm, geom=loose_faces, context="FACES")

        if self.remove_redundant and (self.positive_bisect or self.negative_bisect):
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

            redundant = [e for e in bm.edges if len(e.link_faces) == 2 and round(get_face_angle(e), 4) == 0]

            if redundant:
                bmesh.ops.dissolve_edges(bm, edges=redundant, use_verts=True)

        geo_gzm_angle = 20

        for e in bm.edges:
            if len(e.link_faces) == 2:
                e[edge_glayer] = get_face_angle(e) >= geo_gzm_angle
            else:
                e[edge_glayer] = 1

        for f in bm.faces:
            if objtype == 'CYLINDER' and len(f.edges) == 4:
                f[face_glayer] = 0
            elif not all(e[edge_glayer] for e in f.edges):
                f[face_glayer] = 0
            else:
                f[face_glayer] = any([get_face_angle(e, fallback=0) >= geo_gzm_angle for e in f.edges])

        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

def draw_bend_angle_status(op):
    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)

        opd = op.operator_data

        row.label(text=f"Adjust {'Kink' if opd['is_kink'] else 'Bend'} Angle")

        draw_status_item(row, key="LMB", text="Finish")
        draw_status_item(row, key="MMB", text="Viewport")
        draw_status_item(row, key="RMB", text="Cancel")

        row.separator(factor=10)

        row.label(text=f"Angle: {dynamic_format(opd['angle'], decimal_offset=1)}")

        draw_status_item(row, active=op.is_ctrl, key="CTRL", text="Snapped Angle", gap=2)

        if not opd['is_kink'] and (opd['BISECT']['POSITIVE'] or opd['BISECT']['NEGATIVE']):
            if opd['SEGMENTS']['POSITIVE'] == opd['SEGMENTS']['NEGATIVE'] or opd['mirror_bend']:
                draw_status_item(row, key="MMB_SCROLL", text="Segments", prop=opd['SEGMENTS']['POSITIVE'], gap=2)

            else:
                if opd['BISECT']['POSITIVE'] and opd['BISECT']['NEGATIVE']:
                    draw_status_item(row, key="MMB_SCROLL", text="Positive Segments", prop=opd['SEGMENTS']['POSITIVE'], gap=2)
                    draw_status_item(row, key="MMB_SCROLL", text="Negative Segments", prop=opd['SEGMENTS']['NEGATIVE'], gap=1)

                elif opd['BISECT']['POSITIVE']:
                    draw_status_item(row, key="MMB_SCROLL", text="Positive Segments", prop=opd['SEGMENTS']['POSITIVE'], gap=2)

                elif opd['BISECT']['NEGATIVE']:
                    draw_status_item(row, key="MMB_SCROLL", text="Negative Segments", prop=opd['SEGMENTS']['NEGATIVE'], gap=2)

        draw_status_item(row, key="R", text="Reset Angle to 0", gap=2)

    return draw

class AdjustBendAngle(bpy.types.Operator, HyperBendGizmoManager):
    bl_idname = "machin3.adjust_bend_angle"
    bl_label = "MACHIN3: Adjust Bend Angle"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            return bool(HyperBendGizmoManager().gizmo_data)

    @classmethod
    def description(cls, context, properties):
        return f"Adjust {'Kink' if HyperBendGizmoManager().operator_data['is_kink'] else 'Bend'} Angle"

    def draw_HUD(self, context):
        if context.area == self.area:

            opd = self.operator_data

            draw_init(self)
            draw_label(context, title=f"Adjust {'Kink' if opd['is_kink'] else 'Bend'} Angle", coords=Vector((self.HUD_x, self.HUD_y)), center=False, color=white, alpha=1)

            self.offset += 18
            dims = draw_label(context, title="Angle: ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=0.5)

            color = red if opd['angle'] in [0, -0] else blue if opd['angle'] in [360, -360] else white
            dims += draw_label(context, title=dynamic_format(opd['angle'], decimal_offset=1), coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=color, alpha=1)

            if self.is_ctrl:
                draw_label(context, title=" Snapping", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=yellow, alpha=1)

            if not opd['is_kink'] and (opd['BISECT']['POSITIVE'] or opd['BISECT']['NEGATIVE']):
                self.offset += 18

                if opd['SEGMENTS']['POSITIVE'] == opd['SEGMENTS']['NEGATIVE'] or opd['mirror_bend']:
                    dims = draw_label(context, title="Segments: ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=0.5)
                    draw_label(context, title=str(opd['SEGMENTS']['POSITIVE']), coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=1)

                else:
                    if opd['BISECT']['POSITIVE'] and opd['BISECT']['NEGATIVE']:
                        dims = draw_label(context, title="Segments: ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=0.5)
                        dims += draw_label(context, title=str(opd['SEGMENTS']['POSITIVE']), coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=1)
                        draw_label(context, title=" positive", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=white, size=10, alpha=0.3)

                        self.offset += 18

                        dims = draw_label(context, title="Segments: ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=0.5)
                        dims += draw_label(context, title=str(opd['SEGMENTS']['NEGATIVE']), coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=1)
                        draw_label(context, title=" negative", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=white, size=10, alpha=0.3)

                    elif opd['BISECT']['POSITIVE']:
                        dims = draw_label(context, title="Segments: ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=0.5)
                        draw_label(context, title=str(opd['SEGMENTS']['POSITIVE']), coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=1)

                    else:
                        dims = draw_label(context, title="Segments: ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=0.5)
                        draw_label(context, title=str(opd['SEGMENTS']['NEGATIVE']), coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=1)

            draw_vector(self.mouse_pos.resized(3) - Vector(self.gizmo_props['loc2d']).resized(3), origin=Vector(self.gizmo_props['loc2d']).resized(3), color=green, fade=True, screen=True)

    def modal(self, context, event):
        if ignore_events(event):
            return {'RUNNING_MODAL'}

        opd = self.operator_data

        if not context.area:
            self.finish(context)

            opd['angle'] = self.initial['angle']
            opd['SEGMENTS']['POSITIVE'] = self.initial['positive_segments']
            opd['SEGMENTS']['NEGATIVE'] = self.initial['negative_segments']
            opd['push_update'] = True
            return {'CANCELLED'}

        context.area.tag_redraw()

        update_mod_keys(self, event)

        events = ['MOUSEMOVE', 'R', *ctrl]

        if event.type in events or scroll(event, key=True):

            if event.type in ['MOUSEMOVE', *ctrl]:
                get_mouse_pos(self, context, event)

                if self.gzm and self.gzm.draw_options == {'FILL_SELECT'}:
                    self.gzm.draw_options = {'ANGLE_VALUE'}

                if not (opd['BEND']['POSITIVE'] or opd['BEND']['NEGATIVE']):
                    opd['BEND']['POSITIVE'] = True

                self.delta_angle = self.get_delta_angle(context, self.mouse_pos, debug=False)

                if self.is_ctrl:
                    step = 5

                    angle = self.initial['angle'] + self.delta_angle

                    mod = angle % step

                    opd['angle'] = min(360, max(-360, round(angle + (step - mod) if mod >= (step / 2) else angle - mod)))

                else:
                    opd['angle'] = min(360, max(-360, self.initial['angle'] + self.delta_angle))

            elif scroll(event, key=True):
                if not opd['is_kink'] and (opd['BISECT']['POSITIVE'] or opd['BISECT']['NEGATIVE']):
                    if scroll_up(event, key=True):
                        positive_segments = opd['SEGMENTS']['POSITIVE'] + (10 if event.ctrl else 1)
                        negative_segments = opd['SEGMENTS']['NEGATIVE'] + (10 if event.ctrl else 1)

                    else:
                        positive_segments = opd['SEGMENTS']['POSITIVE'] - (10 if event.ctrl else 1)
                        negative_segments = opd['SEGMENTS']['NEGATIVE'] - (10 if event.ctrl else 1)

                    opd['SEGMENTS']['POSITIVE'] = max(0, positive_segments)
                    opd['SEGMENTS']['NEGATIVE'] = max(0, negative_segments)

            elif event.type == 'R' and event.value == 'PRESS':
                self.finish(context)

                opd['angle'] = 0
                opd['push_update'] = True
                return {'FINISHED'}

            opd['push_update'] = True

        elif (event.type == 'LEFTMOUSE' and event.value == 'RELEASE') or event.type == 'SPACE':
            self.finish(context)
            return {'FINISHED'}

        elif event.type in ['RIGHTMOUSE', 'ESC']:
            self.finish(context)

            opd['angle'] = self.initial['angle']
            opd['SEGMENTS']['POSITIVE'] = self.initial['positive_segments']
            opd['SEGMENTS']['NEGATIVE'] = self.initial['negative_segments']
            opd['push_update'] = True
            return {'CANCELLED'}

        return {'PASS_THROUGH'}

    def finish(self, context):
        finish_modal_handlers(self)

        finish_status(self)

        self.active.show_wire = False

        self.operator_data['show_HUD'] = True

    def invoke(self, context, event):
        self.init_props_from_gizmo_manager(context)

        self.delta_angle = 0
        self.last_angle = 0
        self.accumulated_angle = 0

        update_mod_keys(self)

        self.bend_origin = self.cmx.decompose()[0]
        self.bend_axis = self.cmx.to_quaternion() @ Vector((0, 1, 0))

        self.gzm = None
        self.gzm_group = context.gizmo_group

        if self.gzm_group:
            for gzm in self.gzm_group.gizmos:
                if gzm.bl_idname == 'GIZMO_GT_dial_3d':
                    self.gzm = gzm

        get_mouse_pos(self, context, event)

        self.init_co = self.get_bend_plane_intersection(context, self.mouse_pos)

        if self.init_co:

            self.bend_co = self.init_co

            self.active.show_wire = True

            self.operator_data['show_HUD'] = False

            init_status(self, context, func=draw_bend_angle_status(self))

            init_modal_handlers(self, context, hud=True)
            return {'RUNNING_MODAL'}
        return {'CANCELLED'}

    def init_props_from_gizmo_manager(self, context):
        opd = self.operator_data
        gp = self.gizmo_props

        self.cmx = gp['cmx']
        self.active = opd['active']

        self.initial = {'angle': opd['angle'],
                        'positive_segments': opd['SEGMENTS']['POSITIVE'],
                        'negative_segments': opd['SEGMENTS']['NEGATIVE']}

    def get_bend_plane_intersection(self, context, mouse_pos):
        view_origin, view_dir = get_view_origin_and_dir(context, mouse_pos)

        i = intersect_line_plane(view_origin, view_origin + view_dir, self.bend_origin, self.bend_axis)

        return i

    def get_delta_angle(self, context, mouse_pos, debug=False):
        self.bend_co = self.get_bend_plane_intersection(context, mouse_pos)

        if self.bend_co:

            init_dir = (self.init_co - self.bend_origin).normalized()
            bend_dir = (self.bend_co - self.bend_origin).normalized()

            angle = degrees(init_dir.angle(bend_dir))
            deltarot = init_dir.rotation_difference(bend_dir).normalized()

            dot = - round(self.bend_axis.dot(deltarot.axis))

            input_angle = dot * angle

            if input_angle < 0 and self.last_angle > 90:
                self.accumulated_angle += 180

            elif input_angle > 0 and self.last_angle < -90:
                self.accumulated_angle -= 180

            elif input_angle > 0 and -90 < self.last_angle < 0 and self.accumulated_angle:
                self.accumulated_angle += 180

            elif input_angle < 0 and 0 < self.last_angle < 90 and self.accumulated_angle:
                self.accumulated_angle -= 180

            if input_angle < 0 and self.accumulated_angle >= 180:
                delta_angle = self.accumulated_angle + (180 + input_angle)

            elif input_angle > 0 and self.accumulated_angle <= -180:
                delta_angle = self.accumulated_angle - (180 - input_angle)

            else:
                delta_angle = self.accumulated_angle + input_angle

            if debug:
                print("delta angle:", delta_angle)

            self.last_angle = input_angle

            return delta_angle

        return self.delta_angle

def draw_bend_offset_status(op):
    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)

        opd = op.operator_data

        row.label(text=f"Adjust {'Kink' if opd['is_kink'] else 'Bend'} Offset")

        draw_status_item(row, key="LMB", text="Finish")
        draw_status_item(row, key="MMB", text="Viewport")
        draw_status_item(row, key="RMB", text="Cancel")

        row.separator(factor=10)

        row.label(text=f"Offset: {dynamic_format(opd['offset'], decimal_offset=1)}")

        if not opd['is_kink'] and (opd['BISECT']['POSITIVE'] or opd['BISECT']['NEGATIVE']):
            row.separator(factor=2)

            if opd['SEGMENTS']['POSITIVE'] == opd['SEGMENTS']['NEGATIVE'] or opd['mirror_bend']:
                draw_status_item(row, key="MMB_SCROLL", text="Segments", prop=opd['SEGMENTS']['POSITIVE'], gap=2)

            else:
                if opd['BISECT']['POSITIVE'] and opd['BISECT']['NEGATIVE']:
                    draw_status_item(row, key="MMB_SCROLL", text="Positive Segments", prop=opd['SEGMENTS']['POSITIVE'], gap=2)
                    draw_status_item(row, key="MMB_SCROLL", text="Negative Segments", prop=opd['SEGMENTS']['NEGATIVE'], gap=1)

                elif opd['BISECT']['POSITIVE']:
                    draw_status_item(row, key="MMB_SCROLL", text="Positive Segments", prop=opd['SEGMENTS']['POSITIVE'], gap=2)

                elif opd['BISECT']['NEGATIVE']:
                    draw_status_item(row, key="MMB_SCROLL", text="Negative Segments", prop=opd['SEGMENTS']['NEGATIVE'], gap=2)

        draw_status_item(row, key="R", text="Reset Offset to 0", gap=2)

    return draw

class AdjustBendOffset(bpy.types.Operator, HyperBendGizmoManager):
    bl_idname = "machin3.adjust_bend_offset"
    bl_label = "MACHIN3: Adjust Bend Offset"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            return bool(HyperBendGizmoManager().gizmo_data)

    @classmethod
    def description(cls, context, properties):
        return f"Adjust {'Kink' if HyperBendGizmoManager().operator_data['is_kink'] else 'Bend'} Offset"

    def draw_HUD(self, context):
        if context.area == self.area:

            opd = self.operator_data

            draw_init(self)
            draw_label(context, title=f"Adjust {'Kink' if opd['is_kink'] else 'Bend'} Offset", coords=Vector((self.HUD_x, self.HUD_y)), center=False, color=white, alpha=1)

            self.offset += 18
            dims = draw_label(context, title="Offset: ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=0.5)

            color = red if opd['offset'] == 0 else white
            dims += draw_label(context, title=dynamic_format(opd['offset'], decimal_offset=1), coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=color, alpha=1)

            if not opd['is_kink'] and (opd['BISECT']['POSITIVE'] or opd['BISECT']['NEGATIVE']):
                self.offset += 18

                if opd['SEGMENTS']['POSITIVE'] == opd['SEGMENTS']['NEGATIVE'] or opd['mirror_bend']:
                    dims = draw_label(context, title="Segments: ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=0.5)
                    draw_label(context, title=str(opd['SEGMENTS']['POSITIVE']), coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=1)

                else:
                    if opd['BISECT']['POSITIVE'] and opd['BISECT']['NEGATIVE']:
                        dims = draw_label(context, title="Segments: ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=0.5)
                        dims += draw_label(context, title=str(opd['SEGMENTS']['POSITIVE']), coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=1)
                        draw_label(context, title=" positive", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=white, size=10, alpha=0.3)

                        self.offset += 18

                        dims = draw_label(context, title="Segments: ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=0.5)
                        dims += draw_label(context, title=str(opd['SEGMENTS']['NEGATIVE']), coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=1)
                        draw_label(context, title=" negative", coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=white, size=10, alpha=0.3)

                    elif opd['BISECT']['POSITIVE']:
                        dims = draw_label(context, title="Segments: ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=0.5)
                        draw_label(context, title=str(opd['SEGMENTS']['POSITIVE']), coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=1)

                    else:
                        dims = draw_label(context, title="Segments: ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=0.5)
                        draw_label(context, title=str(opd['SEGMENTS']['NEGATIVE']), coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=1)

    def draw_VIEW3D(self, context):
        if context.area == self.area:

            opd = self.operator_data
            gp = self.gizmo_props
            gd = self.gizmo_data['OFFSET']

            bend_origin = gp['cmx'].to_translation()
            loc = gd['loc']

            draw_line([bend_origin, loc], width=2, color=blue)

            factor = gd['z_factor'] * 2

            if opd['offset'] >= 0:
                draw_vector(self.cursor_z * factor, origin=loc, width=2, color=blue, fade=True)
                draw_vector(-self.cursor_z * factor, origin=bend_origin, width=2, color=blue, fade=True)
            else:
                draw_vector(self.cursor_z * factor, origin=bend_origin, width=2, color=blue, fade=True)
                draw_vector(-self.cursor_z * factor, origin=loc, width=2, color=blue, fade=True)

    def modal(self, context, event):
        if ignore_events(event):
            return {'PASS_THROUGH'}

        opd = self.operator_data
        gd = self.gizmo_data['OFFSET']
        gp = self.gizmo_props

        if not context.area:
            self.finish(context)

            opd['offset'] = self.initial['offset']
            opd['SEGMENTS']['POSITIVE'] = self.initial['positive_segments']
            opd['SEGMENTS']['NEGATIVE'] = self.initial['negative_segments']
            opd['push_update'] = True

            gd['loc'] = self.initial['loc']
            gp['push_update'] = 'OFFSET_GIZMO_CANCEL'
            return {'CANCELLED'}

        context.area.tag_redraw()

        events = ['MOUSEMOVE', 'R', *ctrl]

        if event.type in events or scroll(event, key=True):

            if event.type in ['MOUSEMOVE', *ctrl]:
                get_mouse_pos(self, context, event)

                co = self.get_cursor_z_intersection(context, self.mouse_pos)

                if co:
                    offset_dir = co - self.init_co

                    dot = self.cursor_z.dot(offset_dir.normalized())

                    offset = offset_dir.length * dot

                    opd['offset'] = self.initial['offset'] + offset

                    gd['loc'] = self.initial['loc'] + offset_dir

            elif scroll(event, key=True):
                if not opd['is_kink'] and (opd['BISECT']['POSITIVE'] or opd['BISECT']['NEGATIVE']):
                    if scroll_up(event, key=True):
                        positive_segments = opd['SEGMENTS']['POSITIVE'] + (10 if event.ctrl else 1)
                        negative_segments = opd['SEGMENTS']['NEGATIVE'] + (10 if event.ctrl else 1)

                    else:
                        positive_segments = opd['SEGMENTS']['POSITIVE'] - (10 if event.ctrl else 1)
                        negative_segments = opd['SEGMENTS']['NEGATIVE'] - (10 if event.ctrl else 1)

                    opd['SEGMENTS']['POSITIVE'] = max(0, positive_segments)
                    opd['SEGMENTS']['NEGATIVE'] = max(0, negative_segments)

            elif event.type == 'R' and event.value == 'PRESS':
                self.finish(context)

                opd['offset'] = 0
                opd['push_update'] = True

                gd['loc'] = self.gizmo_props['loc']
                gp['push_update'] = 'OFFSET_GIZMO_RESET'

                return {'FINISHED'}

            opd['push_update'] = True

        elif (event.type == 'LEFTMOUSE' and event.value == 'RELEASE') or event.type == 'SPACE':
            self.finish(context)

            gp['push_update'] = "OFFSET_GIZMO_ADJUST"
            return {'FINISHED'}

        elif event.type in ['RIGHTMOUSE', 'ESC']:
            self.finish(context)

            opd['offset'] = self.initial['offset']
            opd['SEGMENTS']['POSITIVE'] = self.initial['positive_segments']
            opd['SEGMENTS']['NEGATIVE'] = self.initial['negative_segments']
            opd['push_update'] = True

            gd['loc'] = self.initial['loc']
            gp['push_update'] = 'OFFSET_GIZMO_CANCEL'

            return {'CANCELLED'}

        return {'PASS_THROUGH'}

    def finish(self, context):
        finish_modal_handlers(self)

        finish_status(self)

        self.active.show_wire = False

        self.operator_data['show_HUD'] = True

    def invoke(self, context, event):
        self.get_init_props_from_gizmo_manager(context)

        get_mouse_pos(self, context, event)

        self.cursor_z = self.cmx.to_quaternion() @ Vector((0, 0, 1))

        self.init_co = self.get_cursor_z_intersection(context, self.mouse_pos)

        if self.init_co:

            self.active.show_wire = True

            self.operator_data['show_HUD'] = False

            init_status(self, context, func=draw_bend_offset_status(self))

            init_modal_handlers(self, context, hud=True, view3d=True)
            return {'RUNNING_MODAL'}

        return {'CANCELLED'}

    def get_init_props_from_gizmo_manager(self, context):

        opd = self.operator_data
        gp = self.gizmo_props
        gd = self.gizmo_data['OFFSET']

        self.cmx = gp['cmx']
        self.active = opd['active']

        self.initial = {'loc': gd['loc'],
                        'offset': opd['offset'],
                        'positive_segments': opd['SEGMENTS']['POSITIVE'],
                        'negative_segments': opd['SEGMENTS']['NEGATIVE']}

    def get_cursor_z_intersection(self, context, mouse_pos):
        view_origin, view_dir = get_view_origin_and_dir(context, mouse_pos)

        i = intersect_line_line(self.initial['loc'], self.initial['loc'] + self.cursor_z, view_origin, view_origin + view_dir)

        if i:
            return i[0]

def draw_bend_limit_status(op):
    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)

        opd = op.operator_data

        row.label(text=f"Adjust {op.side.title()} Bend Limit")

        draw_status_item(row, key="LMB", text="Finish")
        draw_status_item(row, key="MMB", text="Viewport")
        draw_status_item(row, key="RMB", text="Cancel")

        row.separator(factor=10)

        row.label(text=f"Limit: {dynamic_format(opd['LIMIT'][op.side], decimal_offset=1)}")

        if opd['BISECT'][op.side] and opd['LIMIT'][op.side] > 0:
            draw_status_item(row, key="MMB_SCROLL", text="Segments", prop=opd['SEGMENTS'][op.side], gap=2)

        draw_status_item(row, key="R", text="Reset Limit to 1", gap=2)

    return draw

class AdjustBendLimit(bpy.types.Operator, HyperBendGizmoManager):
    bl_idname = "machin3.adjust_bend_limit"
    bl_label = "MACHIN3: Adjust Bend Limit"
    bl_description = "Adjust Bend Limit"
    bl_options = {'REGISTER'}

    side: StringProperty(name="Limit Type", default='POSITIVE')
    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            return bool(HyperBendGizmoManager().gizmo_data)

    def draw_HUD(self, context):
        if context.area == self.area:

            opd = self.operator_data
            limit = opd['LIMIT'][self.side]

            draw_init(self)
            dims = draw_label(context, title="Adjust Bend Limit ", coords=Vector((self.HUD_x, self.HUD_y)), center=False, color=white, alpha=1)
            draw_label(context, title=self.side.lower(), coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, color=white, size=10, alpha=0.5)

            self.offset += 18
            dims = draw_label(context, title="Limit: ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=0.5)

            color = red if limit == 0 else blue if limit == 1 else white
            draw_label(context, title=dynamic_format(limit, decimal_offset=1), coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=color, alpha=1)

            if opd['BISECT'][self.side] and limit > 0:
                self.offset += 18
                dims = draw_label(context, title="Segments: ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=0.5)
                draw_label(context, title=str(opd['SEGMENTS'][self.side]), coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=1)

    def draw_VIEW3D(self, context):
        if context.area == self.area:

            bend_origin = self.cmx.to_translation()
            loc = self.gizmo_data['LIMIT'][self.side]['loc']
            max_loc = self.cmx.to_translation() + self.limit_dir * self.distance

            draw_line([bend_origin, loc], width=2, color=yellow)
            draw_line([bend_origin, max_loc], width=2, color=yellow, alpha=0.2)

    def modal(self, context, event):
        if ignore_events(event):
            return {'RUNNING_MODAL'}

        opd = self.operator_data
        gd = self.gizmo_data['LIMIT'][self.side]
        gp = self.gizmo_props

        if not context.area:
            self.finish(context)

            opd['LIMIT'][self.side] = self.initial['limit']
            opd['SEGMENTS'][self.side] = self.initial['segments']
            opd['push_update'] = True

            gd['loc'] = self.initial['loc']
            gp['push_update'] = f"{self.side}_LIMIT_GIZMO_CANCEL"

            return {'CANCELLED'}

        context.area.tag_redraw()

        events = ['MOUSEMOVE', 'R', *ctrl]

        if event.type in events or scroll(event, key=True):

            if event.type in ['MOUSEMOVE', *ctrl]:
                get_mouse_pos(self, context, event)

                co = self.get_limit_dir_intersection(context, self.mouse_pos)

                if co:
                    limit_dir = co - self.cmx.to_translation() - self.limit_offset_vector

                    dot = self.limit_dir.dot(limit_dir.normalized())

                    if dot > 0:

                        if 0 < limit_dir.length < self.distance:
                            limit = limit_dir.length / self.distance

                        else:
                            limit = 1

                    else:
                        limit = 0

                    opd['LIMIT'][self.side] = limit

                    if limit == 0:
                        gd['loc'] = self.cmx.to_translation()

                    elif limit == 1:
                        gd['loc'] = self.cmx.to_translation() + self.limit_dir * self.distance

                    else:
                        gd['loc'] = co - self.limit_offset_vector

            elif opd['BISECT'][self.side] and scroll(event, key=True):

                if scroll_up(event, key=True):
                    opd['SEGMENTS'][self.side] += 10 if event.ctrl else 1

                elif scroll_down(event, key=True):
                    opd['SEGMENTS'][self.side] -= 10 if event.ctrl else 1

            elif event.type == 'R' and event.value == 'PRESS':
                self.finish(context)

                opd['LIMIT'][self.side] = 1
                opd['push_update'] = True

                gd['loc'] = self.cmx.to_translation() + self.limit_dir * self.distance
                gp['push_update'] = f"{self.side}_LIMIT_GIZMO_RESET"

                return {'FINISHED'}

            opd['push_update'] = True

        if (event.type == 'LEFTMOUSE' and event.value == 'RELEASE') or event.type == 'SPACE':
            self.finish(context)

            gp['push_update'] = f"{self.side}_LIMIT_GIZMO_ADJUST"
            return {'FINISHED'}

        elif event.type in ['RIGHTMOUSE', 'ESC']:
            self.finish(context)

            opd['LIMIT'][self.side] = self.initial['limit']
            opd['SEGMENTS'][self.side] = self.initial['segments']
            opd['push_update'] = True

            gd['loc'] = self.initial['loc']
            gp['push_update'] = f"{self.side}_LIMIT_GIZMO_CANCEL"
            return {'CANCELLED'}

        return {'PASS_THROUGH'}

    def finish(self, context):
        finish_modal_handlers(self)

        finish_status(self)

        self.active.show_wire = False

        self.operator_data['show_HUD'] = True

    def invoke(self, context, event):
        self.get_init_props_from_gizmo_manager(context)

        get_mouse_pos(self, context, event)

        self.limit_dir = self.rot @ Vector((0, 0, 1))

        init_co = self.get_limit_dir_intersection(context, self.mouse_pos)

        if init_co:
            self.limit_offset_vector = init_co - self.initial['loc']

            if self.operator_data['angle']:
                self.active.show_wire = True

            self.operator_data['show_HUD'] = False

            init_status(self, context, func=draw_bend_limit_status(self))

            force_ui_update(context)

            init_modal_handlers(self, context, hud=True, view3d=True)
            return {'RUNNING_MODAL'}

        return {'CANCELLED'}

    def get_init_props_from_gizmo_manager(self, context):
        opd = self.operator_data
        gp = self.gizmo_props
        gd = self.gizmo_data['LIMIT'][self.side]

        self.cmx = gp['cmx']
        self.active = opd['active']

        self.rot = gd['rot']
        self.distance = gd['distance']

        self.initial = {'loc': gd['loc'],
                        'limit': opd['LIMIT'][self.side],
                        'segments': opd['SEGMENTS'][self.side]}

    def get_limit_dir_intersection(self, context, mouse_pos):
        view_origin, view_dir = get_view_origin_and_dir(context, mouse_pos)

        i = intersect_line_line(self.initial['loc'], self.initial['loc'] + self.limit_dir, view_origin, view_origin + view_dir)

        if i:
            return i[0]

def draw_bend_containment_status(op):
    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)

        opd = op.operator_data
        side, axis = op.side.split('_')

        row.label(text=f"Adjust {side.title()} {axis} {'Kink' if opd['is_kink'] else 'Bend'} Containment")

        draw_status_item(row, key="LMB", text="Finish")
        draw_status_item(row, key="MMB", text="Viewport")
        draw_status_item(row, key="RMB", text="Cancel")

        row.separator(factor=10)

        row.label(text=f"Contain: {dynamic_format(opd['CONTAIN'][op.side], decimal_offset=1)}")

        draw_status_item(row, key="R", text="Reset Contain to 1", gap=2)

    return draw

class AdjustBendContainment(bpy.types.Operator, HyperBendGizmoManager):
    bl_idname = "machin3.adjust_bend_containment"
    bl_label = "MACHIN3: Adjust Bend Containment"
    bl_description = "Adjust Bend Containment"
    bl_options = {'REGISTER'}

    side: StringProperty(name="Containment Side", default='CONTAIN_NEGATIVE_Z')
    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            return bool(HyperBendGizmoManager().gizmo_data)

    def draw_HUD(self, context):
        if context.area == self.area:

            opd = self.operator_data
            contain = opd['CONTAIN'][self.side]
            side, axis = self.side.split('_')

            draw_init(self)
            dims = draw_label(context, title=f"Adjust {'Kink' if opd['is_kink'] else 'Bend'} Containment ", coords=Vector((self.HUD_x, self.HUD_y)), center=False, color=white, alpha=1)

            title = f"{side.title()} {axis}"
            draw_label(context, title=title, coords=Vector((self.HUD_x + dims.x, self.HUD_y)), center=False, color=white, size=10, alpha=0.5)

            self.offset += 18
            dims = draw_label(context, title="Contain: ", coords=Vector((self.HUD_x, self.HUD_y)), offset=self.offset, center=False, color=white, alpha=0.5)

            color = red if contain == 0 else blue if contain == 1 else white
            draw_label(context, title=dynamic_format(contain, decimal_offset=1), coords=Vector((self.HUD_x + dims.x, self.HUD_y)), offset=self.offset, center=False, color=color, alpha=1)

    def draw_VIEW3D(self, context):
        if context.area == self.area:
            gd = self.gizmo_data['CONTAIN'][self.side]

            bend_origin = self.cmx.to_translation()
            loc = gd['loc']
            max_loc = self.cmx.to_translation() + self.contain_dir * self.distance
            is_z = self.side.endswith('_Z')

            color = blue if is_z else green
            draw_line([bend_origin, loc], width=2, color=color)
            draw_line([bend_origin, max_loc], width=2, color=color, alpha=0.2)

            if self.coords:
                draw_line(self.coords + [self.coords[0]], color=color)
                draw_tris(self.coords, indices=[(0, 1, 2), (2, 3, 0)], color=color, xray=False, alpha=0.3 if is_z else 0.15)

    def modal(self, context, event):
        if ignore_events(event):
            return {'RUNNING_MODAL'}

        opd = self.operator_data
        gd = self.gizmo_data['CONTAIN'][self.side]
        gp = self.gizmo_props

        if not context.area:
            self.finish(context)

            opd['CONTAIN'][self.side] = self.initial['contain']
            opd['push_update'] = True

            gd['loc'] = self.initial['loc']
            gp['push_update'] = f"{self.side}_CONTAIN_GIZMO_CANCEL"
            return {'CANCELLED'}

        context.area.tag_redraw()

        events = ['MOUSEMOVE', 'R', *ctrl]

        if event.type in events or scroll(event, key=True):

            if event.type in ['MOUSEMOVE', *ctrl]:
                get_mouse_pos(self, context, event)

                co = self.get_contain_dir_intersection(context, self.mouse_pos)

                if co:
                    contain_dir = co - self.cmx.to_translation() - self.contain_offset_vector

                    dot = self.contain_dir.dot(contain_dir.normalized())

                    if dot > 0:

                        if 0 < contain_dir.length < self.distance:
                            contain = contain_dir.length / self.distance

                        else:
                            contain = 1

                    else:
                        contain = 0

                    opd['CONTAIN'][self.side] = contain

                    if contain == 0:
                        gd['loc'] = self.cmx.to_translation()

                    elif contain == 1:
                        gd['loc'] = self.cmx.to_translation() + self.contain_dir * self.distance

                    else:
                        gd['loc'] = co - self.contain_offset_vector

                    self.coords = self.create_contain_plane_coords()

            elif event.type == 'R' and event.value == 'PRESS':
                self.finish(context)

                opd['CONTAIN'][self.side] = 1
                opd['push_update'] = True

                gd['loc'] = self.cmx.to_translation() + self.contain_dir * self.distance
                gp['push_update'] = f"{self.side}_CONTAIN_GIZMO_RESET"

                return {'FINISHED'}

            opd['push_update'] = True

        if (event.type == 'LEFTMOUSE' and event.value == 'RELEASE') or event.type == 'SPACE':
            self.finish(context)

            gp['push_update'] = f"{self.side}_CONTAIN_GIZMO_ADJUST"
            return {'FINISHED'}

        elif event.type in ['RIGHTMOUSE', 'ESC']:
            self.finish(context)

            opd['CONTAIN'][self.side] = self.initial['contain']
            opd['push_update'] = True

            gd['loc'] = self.initial['loc']
            gp['push_update'] = f"{self.side}_CONTAIN_GIZMO_CANCEL"
            return {'CANCELLED'}

        return {'PASS_THROUGH'}

    def finish(self, context):
        finish_modal_handlers(self)

        finish_status(self)

        self.active.show_wire = False

        self.operator_data['show_HUD'] = True

    def invoke(self, context, event):
        self.get_init_props_from_gizmo_manager(context)

        get_mouse_pos(self, context, event)

        self.contain_dir = self.rot @ Vector((0, 0, 1))

        init_co = self.get_contain_dir_intersection(context, self.mouse_pos)

        if init_co:
            self.contain_offset_vector = init_co - self.initial['loc']

            self.coords = self.create_contain_plane_coords()

            if self.operator_data['angle']:
                self.active.show_wire = True

            self.operator_data['show_HUD'] = False

            init_status(self, context, func=draw_bend_containment_status(self))

            init_modal_handlers(self, context, hud=True, view3d=True)
            return {'RUNNING_MODAL'}

        return {'CANCELLED'}

    def get_init_props_from_gizmo_manager(self, context):
        other_axis = 'Z' if self.side.endswith('_Y') else 'Y'

        opd = self.operator_data
        gp = self.gizmo_props
        gd = self.gizmo_data['CONTAIN'][self.side]

        self.cmx = gp['cmx']
        self.active = opd['active']

        self.rot = gd['rot']
        self.distance = gd['distance']

        self.initial = {'loc': gd['loc'],
                        'contain': opd['CONTAIN'][self.side]}

        max_distances = [self.gizmo_data['LIMIT']['POSITIVE']['distance'],
                         self.gizmo_data['LIMIT']['NEGATIVE']['distance'],
                         self.gizmo_data['CONTAIN'][f"POSITIVE_{other_axis}"]['distance'],
                         self.gizmo_data['CONTAIN'][f"NEGATIVE_{other_axis}"]['distance']]

        coords = [Vector((max_distances[0], -max_distances[3], 0)),
                  Vector((-max_distances[1], -max_distances[3], 0)),
                  Vector((-max_distances[1], max_distances[2], 0)),
                  Vector((max_distances[0], max_distances[2], 0))]

        mx = self.cmx if other_axis == 'Y' else self.cmx @ Matrix.Rotation(radians(90), 4, 'X')

        self.base_plane_coords = [mx @ co for co in coords]

    def get_contain_dir_intersection(self, context, mouse_pos):
        view_origin, view_dir = get_view_origin_and_dir(context, mouse_pos)

        i = intersect_line_line(self.initial['loc'], self.initial['loc'] + self.contain_dir, view_origin, view_origin + view_dir)

        if i:
            return i[0]

    def create_contain_plane_coords(self):

        contain = self.operator_data['CONTAIN'][self.side] * self.distance

        coords = []

        for co in self.base_plane_coords:
            coords.append(co + self.contain_dir * contain)

        return coords

class ToggleBend(bpy.types.Operator, HyperBendGizmoManager):
    bl_idname = "machin3.toggle_bend"
    bl_label = "MACHIN3: Toggle Bend"
    bl_options = {'REGISTER'}

    prop: StringProperty(name="Bend Prop to Toggle")

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            return bool(HyperBendGizmoManager().gizmo_data)

    @classmethod
    def description(cls, context, properties):
        if properties:
            opd = HyperBendGizmoManager().operator_data

            if properties.prop == 'is_kink':
                return f"Switch to {'Bending' if opd['is_kink'] else 'Kinking'}"

            elif properties.prop == 'use_kink_edges':
                return f"{'Disable' if opd['use_kink_edges'] else 'Enable'} Kink Constrain to Edges"

            elif properties.prop == 'affect_children':
                return f"{'Disable' if opd['affect_children'] else 'Enable'} Affect Children"

            elif properties.prop == 'mirror_bend':
                return f"{'Disable' if opd['mirror_bend'] else 'Enable'} Mirrored Bending"

            elif properties.prop == 'remove_redundant':
                return f"{'Disable' if opd['remove_redundant'] else 'Enable'} Redundant Edge Removal"

            elif properties.prop == 'positive_bend':
                return f"{'Disable' if opd['BEND']['POSITIVE'] else 'Enable'} Positive Bending"

            elif properties.prop == 'negative_bend':
                return f"{'Disable' if opd['BEND']['NEGATIVE'] else 'Enable'} Negative Bending"

            elif properties.prop == 'positive_bisect':
                return f"{'Disable' if opd['BISECT']['POSITIVE'] else 'Enable'} Positive Bisecting"

            elif properties.prop == 'negative_bisect':
                return f"{'Disable' if opd['BISECT']['NEGATIVE'] else 'Enable'} Negative Bisecting"
        return "Invalid Context"

    def invoke(self, context, event):
        self.mouse_pos = Vector((event.mouse_x, event.mouse_y))
        self.gizmo_props['warp_mouse'] = self.mouse_pos

        return self.execute(context)

    def execute(self, context):
        opd = self.operator_data

        if self.prop in ['is_kink', 'use_kink_edges', 'affect_children', 'remove_redundant', 'mirror_bend']:
            opd[self.prop] = not opd[self.prop]

            if self.prop == 'mirror_bend':

                if opd['mirror_bend']:
                    opd['BISECT']['NEGATIVE'] = opd['BISECT']['POSITIVE']
                    opd['BEND']['NEGATIVE'] = opd['BEND']['POSITIVE']

                    opd['contain'] = False

                else:
                    opd['BISECT']['NEGATIVE'] = not opd['BISECT']['POSITIVE']
                    opd['BEND']['NEGATIVE'] = not opd['BEND']['POSITIVE']

        elif self.prop.endswith('_bend'):
            side = 'POSITIVE' if self.prop.startswith('positive_') else 'NEGATIVE'

            opd['BEND'][side] = not opd['BEND'][side]

            if opd['contain'] and opd['BEND']['POSITIVE'] and opd['BEND']['NEGATIVE']:
                opd['contain'] = False

        elif self.prop.endswith('_bisect'):
            side = 'POSITIVE' if self.prop.startswith('positive_') else 'NEGATIVE'

            opd['BISECT'][side] = not opd['BISECT'][side]

        opd['push_update'] = True

        return {'FINISHED'}
