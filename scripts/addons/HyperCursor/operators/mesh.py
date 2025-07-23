import bpy
from bpy.props import EnumProperty, BoolProperty, FloatProperty
import bmesh
from .. utils.draw import draw_lines, draw_tris
from .. utils.ui import finish_modal_handlers, force_ui_update, force_geo_gizmo_update, init_modal_handlers
from .. utils.bmesh import ensure_gizmo_layers
from .. utils.mesh import get_mesh_user_count
from .. utils.gizmo import setup_geo_gizmos
from .. utils.view import ensure_visibility
from .. ui.panels import draw_geo_gizmo_panel
from .. items import gizmo_angle_presets
from .. colors import green, blue

class ToggleGizmoDataLayerPreview(bpy.types.Operator):
    bl_idname = "machin3.toggle_gizmo_data_layer_preview"
    bl_label = "MACHIN3: Toggle Gizmo Data Layer Preview"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.HC.ishyper and context.mode == 'EDIT_MESH'

    @classmethod
    def description(cls, context, properties):
        if tuple(context.scene.tool_settings.mesh_select_mode) == (True, False, False):
            return "Toggle Preview of Edge and Face Gizmos"
        elif tuple(context.scene.tool_settings.mesh_select_mode) == (False, True, False):
            return "Toggle Preview of Edge (and Face) Gizmos"
        elif tuple(context.scene.tool_settings.mesh_select_mode) == (False, False, True):
            return "Toggle Preview of Face (and Edge) Gizmos"

    def draw_VIEW3D(self, context):
        if context.area == self.area:

            if tuple(bpy.context.scene.tool_settings.mesh_select_mode) == (True, False, False):
                if self.edge_coords:
                    draw_lines(self.edge_coords, mx=self.mx, color=blue, width=2, alpha=0.15)

                if self.face_coords:
                    draw_tris(self.face_coords, mx=self.mx, color=blue, alpha=0.1)

            elif tuple(bpy.context.scene.tool_settings.mesh_select_mode) == (False, True, False):
                if self.edge_coords:
                    draw_lines(self.edge_coords, mx=self.mx, color=green, width=2, alpha=0.3)

                if self.face_coords:
                    draw_tris(self.face_coords, mx=self.mx, color=blue, alpha=0.1)

            elif tuple(bpy.context.scene.tool_settings.mesh_select_mode) == (False, False, True):
                if self.edge_coords:
                    draw_lines(self.edge_coords, mx=self.mx, color=blue, width=2, alpha=0.3)

                if self.face_coords:
                    draw_tris(self.face_coords, mx=self.mx, color=green, alpha=0.15)

    def modal(self, context, event):
        if not context.area:
            self.finish(context)
            return {'CANCELLED'}

        context.area.tag_redraw()

        if self.active.HC.geometry_gizmos_preview_force_update:
            if self.debug:
                print("updating preview coords")

            self.get_preview_coords()
            self.active.HC.geometry_gizmos_preview_force_update = False

        if not self.active.HC.geometry_gizmos_show_previews or context.mode != 'EDIT_MESH':
            self.finish(context)

            if self.debug:
                print(" finishing")
            return {'FINISHED'}

        return {'PASS_THROUGH'}

    def finish(self, context):
        finish_modal_handlers(self)

        if self.active.HC.geometry_gizmos_show_previews:
            if self.debug:
                print("\n toggling off (MODE SWITCH)")
            self.active.HC.geometry_gizmos_show_previews = False

    def invoke(self, context, event):
        self.debug = False

        self.active = context.active_object
        self.active.HC.geometry_gizmos_show_previews = not self.active.HC.geometry_gizmos_show_previews
        self.mx = self.active.matrix_world

        self.get_preview_coords()

        if self.active.HC.geometry_gizmos_show_previews:
            if self.debug:
                print("\ntoggling on")

            init_modal_handlers(self, context, view3d=True)
            return {'RUNNING_MODAL'}

        else:
            if self.debug:
                print("\ntoggling off (OPERATOR)")
            return {'FINISHED'}

    def get_preview_coords(self):
        bm = bmesh.from_edit_mesh(self.active.data)
        loop_triangles = bm.calc_loop_triangles()

        edge_glayer, face_glayer = ensure_gizmo_layers(bm)

        self.edge_coords = [v.co.copy() for e in bm.edges if e[edge_glayer] == 1 for v in e.verts ]
        self.face_coords = [l.vert.co.copy() for tri in loop_triangles if tri[0].face[face_glayer] == 1 for l in tri]

class ToggleGizmo(bpy.types.Operator):
    bl_idname = "machin3.toggle_gizmo"
    bl_label = "MACHIN3: Toggle Gizmo"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.active_object and context.mode == 'EDIT_MESH':
            return tuple(bpy.context.scene.tool_settings.mesh_select_mode) in [(False, True, False), (False, False, True)]

    @classmethod
    def description(cls, context, properties):
        if tuple(context.scene.tool_settings.mesh_select_mode) == (False, True, False):
            return "Toggle Edge Gizmos on selected Edges"
        elif tuple(context.scene.tool_settings.mesh_select_mode) == (False, False, True):
            return "Toggle Face Gizmos on selected Faces"

    def draw(self, context):
        layout = self.layout
        column = layout.column()

        active = context.active_object

        row = column.row(align=True)
        row.label(text="Hyper Object Type")
        row.prop(active.HC, 'objtype_without_none', expand=True)

    def invoke(self, context, event):
        debug = False

        active = context.active_object
        objtype = active.HC.objtype

        if not active.HC.ishyper:
            if debug:
                print("creating hyper cursor object")
            active.HC.ishyper = True

        if objtype == 'NONE':
            if debug:
                print("initializing non-HC obj as CUBE")

            active.HC.objtype = 'CUBE'

        return self.execute(context)

    def execute(self, context):
        debug = False

        active = context.active_object

        bm = bmesh.from_edit_mesh(active.data)
        edge_glayer, face_glayer = ensure_gizmo_layers(bm)

        if tuple(bpy.context.scene.tool_settings.mesh_select_mode) == (False, True, False):
            if debug:
                print("toggling edge gizmo")

            edges = [e for e in bm.edges if e.select]

            state = all([e[edge_glayer] for e in edges])

            for e in edges:
                e[edge_glayer] = not state

        elif tuple(bpy.context.scene.tool_settings.mesh_select_mode) == (False, False, True):
            if debug:
                print("toggling face gizmo")

            faces = [f for f in bm.faces if f.select]
            state = all([f[face_glayer] for f in faces])

            for f in faces:
                f[face_glayer] = not state

        bmesh.update_edit_mesh(active.data)

        if active.HC.geometry_gizmos_show_previews:
            active.HC.geometry_gizmos_preview_force_update = True

        else:
            bpy.ops.machin3.toggle_gizmo_data_layer_preview('INVOKE_DEFAULT')

        return {'FINISHED'}

class GeoGizmoSetup(bpy.types.Operator):
    bl_idname = "machin3.geogzm_setup"
    bl_label = "MACHIN3: Geometry Gizmo Setup"
    bl_options = {'REGISTER', 'UNDO'}

    def update_angle(self, context):
        if self.avoid_update:
            self.avoid_update = False
            return

        if self.angle_preset != 'CUSTOM':
            self.avoid_update = True
            self.angle_preset = 'CUSTOM'

    def update_angle_preset(self, context):
        if self.avoid_update:
            self.avoid_update = False
            return

        if self.angle_preset != 'CUSTOM':
            self.avoid_update = True
            self.angle = float(self.angle_preset)

    angle: FloatProperty(name="Angle", default=20, update=update_angle)
    angle_preset: EnumProperty(name="Angle", items=gizmo_angle_presets, default="CUSTOM", update=update_angle_preset)
    edges: BoolProperty(name="Affect Edge Gizmos", default=True)
    faces: BoolProperty(name="Affect Face Gizmos", default=True)
    skip_cylinder_quad_faces: BoolProperty(name="Skip Cylinder Quad Faces", description="On Cylinders, skip Faces, that are Quads", default=True)
    skip_incomplete_faces: BoolProperty(name="Skip Incomplete Faces", description="Skip Faces, that don't have Edge Gizmos on all Edges", default=True)
    def update_clear_gizmos(self, context):
        if self.avoid_update:
            self.avoid_update = False
            return

        if self.clear_gizmos:
            self.setup_gizmos = False

            if self.remove_redundant_edges:
                self.avoid_update = True
                self.remove_redundant_edges = False

        else:
            self.setup_gizmos = True

    def update_remove_redundant(self, context):
        if self.avoid_update:
            self.avoid_update = False
            return

        if self.remove_redundant_edges:
            if not self.setup_gizmos:
                self.setup_gizmos = True

            if self.clear_gizmos:
                self.avoid_update = True
                self.clear_gizmos = False

    setup_gizmos: BoolProperty(name="Setup Gizmos", default=False)
    clear_gizmos: BoolProperty(name="Clear Gizmos", default=False, update=update_clear_gizmos)
    remove_redundant_edges: BoolProperty(name="Remove Redundant Edges", default=False, update=update_remove_redundant)
    show_menu: BoolProperty(name="Show Gizmo Menu", default=False)
    avoid_update: BoolProperty()

    @classmethod
    def poll(cls, context):
        if context.mode in ['OBJECT', 'EDIT_MESH']:
            active = context.active_object
            return active and active.HC.ishyper and active.type == 'MESH'

    @classmethod
    def description(cls, context, properties):
        if properties:

            if properties.setup_gizmos:
                if properties.remove_redundant_edges:
                    desc = "Setup Edge and Face Geometry Gizmos based on Edge Angles"
                    desc += "\nAnd Remove Redundant Edges too"
                else:
                    desc = "Setup Edge and Face Geometry Gizmos based on Edge Angles"

            elif properties.clear_gizmos:
                desc = "Clear All Geometry Gizmos"

            else:
                desc = "Open Menu to Adjust Gizmo Settings and Limits"
                desc += "\n\nSHIFT: Setup Edge and Face Geometry Gizmos based on Edge Angles"
                desc += "\n\nCTRL: Setup Gizmos and Remove Redundant Edges too"
                desc += "\n\nALT: Clear All Geometry Gizmos"
            return desc
        return "Invalid Context"

    def draw(self, context):
        layout = self.layout

        if self.show_menu:
            draw_geo_gizmo_panel(context, layout)

        else:
            column = layout.column(align=True)

            row = column.row(align=True)
            row.prop(self, 'clear_gizmos', toggle=True)
            row.prop(self, 'remove_redundant_edges', toggle=True)

            if self.setup_gizmos:
                row = column.row(align=True)
                row.prop(self, 'edges', toggle=True)
                row.prop(self, 'faces', toggle=True)

                if self.faces:
                    row = column.row(align=True)

                    if self.objtype == 'CYLINDER':
                        row.prop(self, 'skip_cylinder_quad_faces', text='Skip Quad Faces', toggle=True)

                    row.prop(self, 'skip_incomplete_faces', text='Skip Incomplete Faces', toggle=True)

                row = column.row(align=True)
                row.active = self.angle_preset == 'CUSTOM'
                row.prop(self, 'angle')

                row = column.row(align=True)
                row.prop(self, 'angle_preset', expand=True)

    def invoke(self, context, event):
        active = context.active_object

        if active.HC.objtype == 'NONE':
            active.HC.objtype = 'CUBE'

        if not active.HC.geometry_gizmos_show:
            active.HC.geometry_gizmos_show = True

        if active.HC.geometry_gizmos_edit_mode == 'SCALE':
            active.HC.geometry_gizmos_edit_mode = 'EDIT'

        force_ui_update(context)

        if active.HC.objtype_without_none != active.HC.objtype:
            active.HC.objtype_without_none = active.HC.objtype
            print("INFO: initiate obj type without none")

        if context.mode == 'EDIT_MESH':
            self.show_menu = False
            self.remove_redundant_edges = False
            self.clear_gizmos = False
            self.setup_gizmos = True

        else:
            self.show_menu = not any([event.shift, event.ctrl, event.alt])

            if self.show_menu:
                return context.window_manager.invoke_popup(self, width=250)

            self.remove_redundant_edges = event.ctrl
            self.clear_gizmos = event.alt

            self.setup_gizmos = any([event.shift, event.ctrl]) and not self.clear_gizmos

        return self.execute(context)

    def execute(self, context):
        active = context.active_object

        self.objtype = context.active_object.HC.objtype

        setup_geo_gizmos(context, active, setup_gizmos=self.setup_gizmos, clear_gizmos=self.clear_gizmos, edges=self.edges, faces=self.faces, angle=self.angle, remove_redundant_edges=self.remove_redundant_edges, skip_cylinder_quad_faces=self.skip_cylinder_quad_faces, skip_incomplete_faces=self.skip_incomplete_faces)
        return {'FINISHED'}

class Link(bpy.types.Operator):
    bl_idname = "machin3.link"
    bl_label = "MACHIN3: Link"
    bl_description = "Link selected Objects' meshes together"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
            active = context.active_object if context.active_object in objects else None

            if objects and active:
                return len(set(obj.data for obj in objects)) > 1

    def execute(self, context):
        orig = context.active_object
        instances = [obj for obj in context.selected_objects if obj.type == 'MESH' and obj != orig]

        for obj in instances:
            obj.data = orig.data

        force_geo_gizmo_update(context)

        return {'FINISHED'}

class Unlink(bpy.types.Operator):
    bl_idname = "machin3.unlink"
    bl_label = "MACHIN3: Unlink"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            active = context.active_object
            return active and active.data and active.data.users > 1

    @classmethod
    def description(cls, context, properties):
        active = context.active_object
        count = get_mesh_user_count(active.data) - 1

        desc = "Unlink Mesh Instance"

        if count == 1:
            desc += "\n\nThere is " + str(count) + " other Object using this Mesh right now"
        else:
            desc += "\n\nThere are " + str(count) + " other Objects using this Mesh right now"

        desc += f"\n\nALT: Reveal Instance{'s' if count > 1 else ''}"
        return desc

    def invoke(self, context, event):
        active = context.active_object

        if event.alt:
            instances = [obj for obj in bpy.data.objects if obj != active and obj.data == active.data]

            bpy.ops.object.select_all(action='DESELECT')
            ensure_visibility(context, instances, select=True)

            context.view_layer.objects.active = instances[0]

        else:
            active.data = active.data.copy()

        return {'FINISHED'}
