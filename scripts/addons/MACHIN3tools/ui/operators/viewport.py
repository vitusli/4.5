import bpy
import bmesh
from bpy.props import EnumProperty, BoolProperty
from mathutils import Vector
from ... utils.draw import draw_fading_label
from ... utils.math import average_locations
from ... utils.registration import get_prefs
from ... utils.ui import warp_mouse
from ... utils.view import ensure_visibility, get_view_origin_and_dir, reset_viewport
from ... items import view_axis_items
from ... colors import yellow, white, green

class ViewAxis(bpy.types.Operator):
    bl_idname = "machin3.view_axis"
    bl_label = "View Axis"
    bl_options = {'REGISTER'}

    axis: EnumProperty(name="Axis", items=view_axis_items, default="FRONT")
    @classmethod
    def description(cls, context, properties):
        m3 = context.scene.M3

        if context.mode == 'OBJECT':
            selection = 'Object'
        elif context.mode == 'EDIT_MESH':
            selection = 'Verts' if tuple(bpy.context.scene.tool_settings.mesh_select_mode) == (True, False, False) else 'Edges' if tuple(bpy.context.scene.tool_settings.mesh_select_mode) == (False, True, False) else 'Faces' if tuple(bpy.context.scene.tool_settings.mesh_select_mode) == (False, False, True) else 'Elements'
        else:
            selection = 'Elements'

        if m3.custom_views_local:
            return f"Align Custom View to Active Object\nALT: Align View to Active {selection}"
        if m3.custom_views_cursor:
            return f"Align Custom View to Cursor\nALT: Align View to Active {selection}"
        else:
            return f"Align View to World\nALT: Align View to Active {selection}"

    @classmethod
    def poll(cls, context):
        return context.space_data and context.space_data.type == 'VIEW_3D'

    def invoke(self, context, event):
        m3 = context.scene.M3
        r3d = context.space_data.region_3d

        if event.alt:
            bpy.ops.view3d.view_axis(type=self.axis, align_active=True)

            r3d.view_perspective = 'ORTHO'

        elif m3.custom_views_local or m3.custom_views_cursor:
            mx = context.scene.cursor.matrix if m3.custom_views_cursor else context.active_object.matrix_world if m3.custom_views_local and context.active_object else None

            if not mx:
                context.scene.M3.custom_views_local = False
                bpy.ops.view3d.view_axis(type=self.axis, align_active=False)
                return {'FINISHED'}

            loc, rot, _ = mx.decompose()
            rot = self.create_view_rotation(rot, self.axis)

            if context.mode == 'EDIT_MESH':
                bm = bmesh.from_edit_mesh(context.active_object.data)

                verts = [v for v in bm.verts if v.select]

                if verts:
                    loc = context.active_object.matrix_world @ average_locations([v.co for v in verts])

            r3d.view_location = loc
            r3d.view_rotation = rot

            r3d.view_perspective = 'ORTHO'

        else:
            bpy.ops.view3d.view_axis(type=self.axis, align_active=False)

        return {'FINISHED'}

    def create_view_rotation(self, rot, axis):
        if self.axis == 'FRONT':
            rmx = rot.to_matrix()
            rotated = rot.to_matrix()

            rotated.col[1] = rmx.col[2]
            rotated.col[2] = -rmx.col[1]

            rot = rotated.to_quaternion()

        elif self.axis == 'BACK':
            rmx = rot.to_matrix()
            rotated = rot.to_matrix()

            rotated.col[0] = -rmx.col[0]
            rotated.col[1] = rmx.col[2]
            rotated.col[2] = rmx.col[1]

            rot = rotated.to_quaternion()

        elif self.axis == 'RIGHT':
            rmx = rot.to_matrix()
            rotated = rot.to_matrix()

            rotated.col[0] = rmx.col[1]
            rotated.col[1] = rmx.col[2]
            rotated.col[2] = rmx.col[0]

            rot = rotated.to_quaternion()

        elif self.axis == 'LEFT':
            rmx = rot.to_matrix()
            rotated = rot.to_matrix()

            rotated.col[0] = -rmx.col[1]
            rotated.col[1] = rmx.col[2]
            rotated.col[2] = -rmx.col[0]

            rot = rotated.to_quaternion()

        elif self.axis == 'BOTTOM':
            rmx = rot.to_matrix()
            rotated = rot.to_matrix()

            rotated.col[1] = -rmx.col[1]
            rotated.col[2] = -rmx.col[2]

            rot = rotated.to_quaternion()

        return rot

class SmartViewCam(bpy.types.Operator):
    bl_idname = "machin3.smart_view_cam"
    bl_label = "Smart View Cam"
    bl_description = "Default: View Active Scene Camera\nNo Camera in the Scene: Create Camera from View\nCamera Selected: Make Selected Camera active and view it.\nAlt + Click: Create Camera from current View."
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            return context.space_data and context.space_data.type == 'VIEW_3D'

    def invoke(self, context, event):
        cams = [obj for obj in context.scene.objects if obj.type == "CAMERA"]
        view = context.space_data
        is_cam_view = view.region_3d.view_perspective == 'CAMERA'

        if not cams or event.alt:

            if event.alt and is_cam_view:
                draw_fading_label(context, text=["You already are in Camera View", context.scene.camera.name], color=[yellow, white], move_y=40, time=4)
                return {'FINISHED'}

            sel = [obj for obj in context.selected_objects]
            active = context.active_object

            bpy.ops.object.camera_add()

            cam = context.active_object
            context.scene.camera = cam

            bpy.ops.view3d.camera_to_view()

            if get_prefs().smart_cam_perfectly_match_viewport:
                ratio = context.region.width / context.region.height
                context.scene.render.resolution_y = round(context.scene.render.resolution_x / ratio)

                cam.data.lens = view.lens
                cam.data.sensor_width = 72

            cam.data.show_mist = context.view_layer.use_pass_mist

            bpy.ops.object.select_all(action='DESELECT')

            for obj in sel:
                obj.select_set(True)

            context.view_layer.objects.active = active

            if cam:
                draw_fading_label(context, text=f"Created new {cam.name}", color=green, move_y=30, time=3)

        else:
            active = context.active_object

            if active:
                if active in context.selected_objects and active.type == "CAMERA":
                    context.scene.camera = active

            if view.region_3d.view_perspective == 'CAMERA':
                bpy.ops.view3d.view_persportho()
                bpy.ops.view3d.view_persportho()

            bpy.ops.view3d.view_camera()

            cam = context.scene.camera

            if cam:
                if is_cam_view:
                    draw_fading_label(context, text=f"Framed {cam.name} Bounds", move_y=30, time=3)
                else:
                    draw_fading_label(context, text=f"Switched to {cam.name}", move_y=30, time=3)

        bpy.ops.view3d.view_center_camera()

        return {'FINISHED'}

class MakeCamActive(bpy.types.Operator):
    bl_idname = "machin3.make_cam_active"
    bl_label = "Make Active"
    bl_description = "Make selected Camera active."
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        active = context.active_object
        if active:
            return active.type == "CAMERA"

    def execute(self, context):
        context.scene.camera = context.active_object

        return {'FINISHED'}

class NextCam(bpy.types.Operator):
    bl_idname = "machin3.next_cam"
    bl_label = "MACHIN3: Next Cam"
    bl_options = {'REGISTER', 'UNDO'}

    previous: BoolProperty(name="Previous", default=False)
    @classmethod
    def poll(cls, context):
        return context.space_data and context.space_data.type == 'VIEW_3D' and context.space_data.region_3d.view_perspective == 'CAMERA'

    @classmethod
    def description(cls, context, properties):
        if properties:
            if properties.previous:
                return "Switch to Previous Camera"
            else:
                return "Switch to Next Camera"
        return "Invalid Context"

    def execute(self, context):
        cams = sorted([obj for obj in context.scene.objects if obj.type == "CAMERA"], key=lambda x: x.name)

        if len(cams) > 1:
            active = context.scene.camera

            idx = cams.index(active)

            if not self.previous:
                idx = 0 if idx == len(cams) - 1 else idx + 1

            else:
                idx = len(cams) - 1 if idx == 0 else idx - 1

            newcam = cams[idx]

            context.scene.camera = newcam

            bpy.ops.view3d.view_center_camera()
            draw_fading_label(context, text=f"Switched to {'previous' if self.previous else 'next'} {newcam.name}", move_y=30, time=3)

        return {'FINISHED'}

class ToggleCamPerspOrtho(bpy.types.Operator):
    bl_idname = "machin3.toggle_cam_persportho"
    bl_label = "MACHIN3: Toggle Camera Perspective/Ortho"
    bl_description = "Toggle Active Scene Camera Perspective/Ortho"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.scene.camera

    def execute(self, context):
        cam = context.scene.camera

        if cam.data.type == "PERSP":
            cam.data.type = "ORTHO"
        else:
            cam.data.type = "PERSP"

        return {'FINISHED'}

toggledprefs = False

class ToggleViewPerspOrtho(bpy.types.Operator):
    bl_idname = "machin3.toggle_view_persportho"
    bl_label = "MACHIN3: Toggle View Perspective/Ortho"
    bl_description = "Toggle Viewport Perspective/Ortho"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        global toggledprefs

        view = context.space_data
        viewtype = view.region_3d.view_perspective
        prefs = context.preferences.inputs

        if viewtype == "PERSP" and prefs.use_auto_perspective:
            prefs.use_auto_perspective = False
            toggledprefs = True

        if viewtype == "ORTHO" and toggledprefs:
            prefs.use_auto_perspective = True

        bpy.ops.view3d.view_persportho()

        return {'FINISHED'}

class ToggleOrbitMethod(bpy.types.Operator):
    bl_idname = "machin3.toggle_orbit_method"
    bl_label = "MACHIN3: Toggle Orbit Method"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def description(cls, context, properties):
        if context.preferences.inputs.view_rotate_method == 'TURNTABLE':
            return "Change Orbit Method from Turntable to Trackball"
        return "Change Orbit Method from Trackball to Turntable"

    def execute(self, context):
        if context.preferences.inputs.view_rotate_method == 'TURNTABLE':
            context.preferences.inputs.view_rotate_method = 'TRACKBALL'
        else:
            context.preferences.inputs.view_rotate_method = 'TURNTABLE'

        return {'FINISHED'}

class ToggleOrbitSelection(bpy.types.Operator):
    bl_idname = "machin3.toggle_orbit_selection"
    bl_label = "MACHIN3: Toggle Orbit Selection"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def description(cls, context, properties):
        if context.preferences.inputs.use_rotate_around_active:
            return "Disable Orbit around Selection"
        return "Enable Orbit around Selection"

    def execute(self, context):
        context.preferences.inputs.use_rotate_around_active = not context.preferences.inputs.use_rotate_around_active
        return {'FINISHED'}

class CreateDoFEmpty(bpy.types.Operator):
    bl_idname = "machin3.create_dof_empty"
    bl_label = "MACHIN3: Create DoF Empty"
    bl_description = "Create Depth of Field Focus Empty"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            return context.scene.camera

    def execute(self, context):
        cam = context.scene.camera

        bpy.ops.object.empty_add(type='SPHERE', align='WORLD')

        empty = context.active_object
        empty.empty_display_size = 0.2
        empty.show_name = True
        empty.name = f"{cam.name}_DoF Focus"

        cam.data.dof.focus_object = empty

        cam.data.dof.aperture_fstop = 0.2

        warp_mouse(self, context, Vector((context.region.width / 2, context.region.height / 2)))

        view_origin, view_dir = get_view_origin_and_dir(context, self.mouse_pos)
        empty.location = view_origin + view_dir * 2

        context.scene.tool_settings.snap_elements = {'FACE'}
        context.scene.tool_settings.use_snap_align_rotation = True

        bpy.ops.transform.translate('INVOKE_DEFAULT')

        draw_fading_label(context, text="Hold CTRL to snap the DoF Focus empty to a Surface", y=self.mouse_pos.y, move_y=40, time=4)
        return {'FINISHED'}

class SelectDoFObject(bpy.types.Operator):
    bl_idname = "machin3.select_dof_object"
    bl_label = "MACHIN3: Select DoF Object"
    bl_description = "Select Depth of Field Focus Object"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            cam = context.scene.camera
            return cam and cam.data.dof.focus_object

    def execute(self, context):
        cam = context.scene.camera
        obj = cam.data.dof.focus_object

        bpy.ops.object.select_all(action='DESELECT')
        ensure_visibility(context, obj, scene=False, select=True)

        context.view_layer.objects.active = obj

        context.scene.tool_settings.snap_elements = {'FACE'}
        context.scene.tool_settings.use_snap_align_rotation = True

        draw_fading_label(context, text=[f"{obj.name} has been selected", "Invoke the Translate tool and snap it to a surface using CTRL"], y=100, move_y=40, time=4)

        return {'FINISHED'}

class ResetViewport(bpy.types.Operator):
    bl_idname = "machin3.reset_viewport"
    bl_label = "MACHIN3: Reset Viewport"
    bl_description = "Perfectly align the viewport with the Y axis, looking into Y+"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.space_data and context.space_data.type == 'VIEW_3D'

    def execute(self, context):
        context.space_data.region_3d.is_orthographic_side_view = False
        context.space_data.region_3d.view_perspective = 'PERSP'

        reset_viewport(context)

        return {'FINISHED'}
