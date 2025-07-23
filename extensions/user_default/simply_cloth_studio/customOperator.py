# Copyright (C) 2025 Vjaceslav Tissen
# vjaceslavt@gmail.com
# Created by Vjaceslav Tissen

# Support by Daniel Meier - Kagi Vision 3D

#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
# '''

from ast import Invert
from ctypes import alignment
import math
import bpy
import bmesh
import os
import mathutils
import bgl
import blf
import random
import time

from math import cos, sin, pi

from os.path import dirname, join, splitext, isfile
from os import listdir
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree


from . import ui_panel
from . import presets


from bpy.props import IntProperty,EnumProperty,FloatProperty, StringProperty, BoolProperty, PointerProperty


class SimplyCollisionManager(bpy.types.Operator):
    bl_idname = "object.simply_collision_manager"
    bl_label = "Add Collision to selected objects"
    bl_description = "Here you can assign collision and friction to objects or to Cloth Meshes"
    mode: StringProperty(default="ADD")
    def addCollision(self, context):
        sel = context.selected_objects
        
        for obj in sel:
            if "SimplyCloth" not in obj.modifiers:
                obj.name = "simply_coll"
            obj.modifiers.new("SimplyCollision", "COLLISION")
            obj.collision.use_culling = False
            obj.collision.thickness_outer = 0.005
            obj.collision.thickness_inner = 0.001
            obj.collision.cloth_friction = 66.0


    def addCollisionToCloth(self, context):
        sel = context.selected_objects
        for obj in sel:
            obj.modifiers.new("SimplyCollision", "COLLISION")
            obj.collision.use_culling = False
            obj.collision.thickness_outer = 0.005
            obj.collision.thickness_inner = 0.003
    def removeCollision(self, context):
        for obj in bpy.context.selected_objects:
            if "SimplyCollision" in obj.modifiers:
                mod = obj.modifiers["SimplyCollision"]
                obj.modifiers.remove(mod)
    def execute(self, context):
        if self.mode == "ADDNEW":
            self.addCollision(context)
        if self.mode == "ADDFROMCLOTH":
            self.addCollisionToCloth(context)
        if self.mode == "REMOVE":
            self.removeCollision(context)
        return {'FINISHED'}
class AnimationManager(bpy.types.Operator):
    bl_idname = "screen.animation_manager"
    bl_label = "Play Cloth Simulation"
    bl_description = "This is the Animation Manager. This is where you set the gravity, speed. Here you can also decide if the Cloth animation is baked from the cache to allow a smooth presentation (degree recommended for animations)"
    icon = "PLAY"
    bl_options = {'REGISTER', 'UNDO'}

    mode: StringProperty(default="PAUSE")
    def checkScreenIsPlaying(self, context):
        screen = bpy.context.screen
        obj = context.active_object
        if not screen.is_animation_playing:
            self.icon_value ="PLAY"
            if "BaseSub" in context.active_object.modifiers:
                bpy.context.object.modifiers["BaseSub"].show_viewport = True
                bpy.context.object.modifiers["BaseSub"].show_in_editmode = True
            # print("ANIMATION RUNNING!")
            # for mod in obj.modifiers:
            # 	if mod.name == "qualityView" or mod.name =="simplySmooth":
            # 		mod.show_in_editmode = False
            # 		mod.show_viewport = True
        else:
            self.icon_value ="PAUSE"
            obj.show_wireframes = False
            bpy.ops.object.shade_smooth()
            # if "BaseSub" in context.active_object.modifiers:
            # 	bpy.context.object.modifiers["BaseSub"].show_viewport = True
            # 	bpy.context.object.modifiers["BaseSub"].show_in_editmode = True
            # for mod in obj.modifiers:
            # 	if mod.name == "qualityView" or mod.name =="simplySmooth":
            # 		mod.show_in_editmode = False
            # 		mod.show_viewport = False
    def stop(self, context):
        screen = bpy.ops.screen
        screen.frame_jump(1)
        screen.animation_cancel()
        bpy.context.object.updateSewingWeldModifier = False

        if "SimplyCloth" in context.active_object.modifiers:
            bpy.context.object.modifiers["SimplyCloth"].settings.shrink_max = 0

        if "BaseSub" in context.active_object.modifiers:
            bpy.context.object.modifiers["BaseSub"].show_viewport = True
            bpy.context.object.modifiers["BaseSub"].show_in_editmode = True

    def bakeFromCache(self,context):
        point_cache = context.active_object.modifiers['SimplyCloth'].point_cache
        override = {'scene': bpy.context.scene,'point_cache': point_cache}
        blenderVersion = bpy.app.version

        if blenderVersion[0] == 3 :
            bpy.ops.ptcache.bake_from_cache(override)

        elif blenderVersion[0] == 4:
            with bpy.context.temp_override(point_cache=point_cache):
                bpy.ops.ptcache.bake_from_cache('INVOKE_DEFAULT')

    def bakeAllFromCache(self,context):
        blenderVersion = bpy.app.version
        point_cache = context.active_object.modifiers['SimplyCloth'].point_cache
        override = {'scene': bpy.context.scene,'point_cache': point_cache, 'bake:': True}
        
        if blenderVersion[0] == 3 :
            bpy.ops.ptcache.bake_all(override)

        elif blenderVersion[0] == 4:
            with bpy.context.temp_override(point_cache=point_cache):
                bpy.ops.ptcache.bake_all('INVOKE_DEFAULT')

    def deleteBake(self,context):
        blenderVersion = bpy.app.version
        point_cache = context.active_object.modifiers['SimplyCloth'].point_cache
        override = {'scene': bpy.context.scene,'point_cache': point_cache}

        if blenderVersion[0] == 3 :
            bpy.ops.ptcache.free_bake(override)
        elif blenderVersion[0] == 4:
            with bpy.context.temp_override(point_cache=point_cache):
                bpy.ops.ptcache.free_bake('INVOKE_DEFAULT')

    def execute(self, context):
        bl_label = "Pause Cloth Simulation"
        screen = bpy.ops.screen
        if self.mode == "BAKEFROMCACHE":
            self.bakeFromCache(context)
        if self.mode == "BAKEALLFROMCACHE":
            self.bakeAllFromCache(context)
        if self.mode == "DELETEBAKECACHE":
            self.deleteBake(context)
        if self.mode == "PLAY":
            screen.animation_play()
        if self.mode == "STOP":
            self.stop(context)
        # self.checkScreenIsPlaying(context)
        return {'FINISHED'}

class SewingCleaningOperators(bpy.types.Operator):
    bl_idname = "object.additional_sewing_operator"
    bl_label = "Extra Sewing Operator"
    bl_description = "Additional Sewing Operators like Bridge Edge Loops, Grid Fill, Remove Sewing"
    icon = "PLAY"

    mode: StringProperty(default="CLOSE SELECTION")

    def bridgeEdgeLoopsClose(self, context):
        bpy.ops.mesh.bridge_edge_loops(use_merge=True, merge_factor=0.5, twist_offset=0, number_cuts=1, smoothness=0, profile_shape_factor=0)
        # bpy.ops.mesh.bridge_edge_loops(use_merge=True)

        # op = "use_merge=True, merge_factor=0.5, twist_offset=0, number_cuts=1, smoothness=0, profile_shape_factor=0"

    # def gridFill(self, context):
    # 	bpy.ops.mesh.fill_grid(span=10)



    def execute(self, context):
        if self.mode == "CLOSE SELECTION":
            self.bridgeEdgeLoopsClose(context)

        return {'FINISHED'}

class createSewing(bpy.types.Operator):
    bl_idname = "object.create_sewing"
    bl_label = "Create Sew"
    bl_description = "Sewing Tool. This is used to create or remove seams on the mesh. Very helpful for clothes that have sewn seams"
    mode: StringProperty()
    value: IntProperty()

    def selectBoundaries(self,context):
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
        bpy.ops.mesh.select_non_manifold()
        bpy.ops.mesh.select_non_manifold(extend=False, use_wire=False, use_boundary=True, use_multi_face=False,use_non_contiguous=False, use_verts=False)

    def removeSewing(self, context):
        if self.mode == "REMOVE_SEWING_UV":
            bpy.ops.uv.select_all(action='SELECT')
            bpy.ops.uv.pin(clear=True)
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
        bpy.ops.mesh.select_non_manifold(extend=False, use_wire=True, use_boundary=False,use_multi_face=False,use_non_contiguous=False,use_verts=False)
        bpy.ops.mesh.delete(type='EDGE')
        
        bpy.context.active_object.sc_sew_collection.clear()



    def createSewing(self, context):
        # bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
        if context.active_object.scs_sew_autoselect == True:
            bpy.ops.object.scs_sew_similar()
        bpy.ops.mesh.mark_sharp()
        bpy.ops.mesh.bridge_edge_loops()
        bpy.ops.mesh.delete(type='ONLY_FACE')
        context.object.cloth_sewing = True


    def createFineSewing(self, context):
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
        bpy.ops.mesh.subdivide()
        bpy.ops.mesh.bridge_edge_loops()
        bpy.ops.mesh.delete(type='ONLY_FACE')
        context.object.cloth_sewing = True

    def editSewing(self, context):
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.select_all(action="DESELECT")

    def mergeSewing(self, context):

        self.createSewing(context)
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
        bpy.ops.mesh.select_non_manifold(extend=False, use_wire=True, use_boundary=False,use_multi_face=False,use_non_contiguous=False,use_verts=False)
        bpy.ops.mesh.edge_collapse()

    def doneSewing(self, context):
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_all(action='SELECT')

        bpy.ops.object.editmode_toggle()
        bpy.context.object.show_wireframes = False
        context.space_data.overlay.show_face_normals = False
        context.space_data.overlay.show_face_orientation = False
        context.active_object.face_orientation = False
        bpy.ops.screen.frame_jump(1)

    def setup_animation_gravity(self, context):
        # print("GRAVITY ANIMATION ADDED")
        if "SimplyCloth" in context.active_object.modifiers:
            context.active_object.modifiers["SimplyCloth"].settings.effector_weights.gravity = 0
            bpy.context.active_object.modifiers["SimplyCloth"].settings.effector_weights.keyframe_insert(
                data_path='gravity', frame=0)            
            bpy.context.active_object.modifiers["SimplyCloth"].settings.effector_weights.keyframe_insert(
                data_path='gravity', frame=10)
            context.active_object.modifiers["SimplyCloth"].settings.effector_weights.gravity = 1
            bpy.context.active_object.modifiers["SimplyCloth"].settings.effector_weights.keyframe_insert(
                data_path='gravity', frame=15)

    def selectSewings(self, context):
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
        bpy.ops.mesh.select_non_manifold(extend=False, use_wire=True, use_boundary=False, use_multi_face=False,
                                            use_non_contiguous=False, use_verts=False)

    def addSelectionToWeldGroup(self, context):
        obj = context.active_object
        verts = obj.data.vertices
        for i, vg in enumerate(obj.vertex_groups):
            if "SimplyWeld" == vg.name:
                # print(True)
                bpy.ops.object.vertex_group_set_active(group='SimplyWeld')
                bpy.ops.object.vertex_group_assign()
            else:
                if "SimplyShrink" == vg.name:
                    if context.active_object.sc_add_sewing_to_shrink == True:
                        bpy.ops.object.vertex_group_set_active(group='SimplyShrink')
                        bpy.ops.object.vertex_group_assign()

    def addSewingToSewCollection(self, context):
        obj = context.active_object
        verts = bpy.data.objects[obj.name].data.vertices
        selected = []
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')

        for vert in verts:
            if vert.select:
                selected.append(vert.index)

            # print(vert.index)
        print("SEWING SELECTED:")
        # print(selected)
        obj.sc_sew_collection.append(selected)
        # bpy.ops.object.editmode_toggle()
        # print("SEWING COLLECTION:")
        # print(obj.sc_sew_collection)
        # bpy.ops.object.editmode_toggle()

    def execute(self, context):
        if self.mode == "SELECT_SEWING":
            self.selectSewings(context)
        if self.mode == "SELECT_BOUNDS":
            self.selectBoundaries(context)    			
        if self.mode == "CREATE_SEWING" or self.mode == "CREATE_SEWING_UV":	
            # context.active_object.sc_temp_selected_sew_verts.clear()
            if context.active_object.cloth_sewing == False:
                context.active_object.cloth_sewing = True
                for mod in context.active_object.modifiers:
                    if mod.type == "CLOTH":
                        mod.settings.sewing_force_max = 5
            


            bpy.ops.object.editmode_toggle()
            bpy.ops.object.editmode_toggle()
            
            self.createSewing(context)
            
            self.selectSewings(context)
            self.addSelectionToWeldGroup(context)
            self.addSewingToSewCollection(context)
            if self.mode == "CREATE_SEWING_UV":
                bpy.ops.uv.pin(clear=False)
                bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
            else:
                bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
            bpy.ops.mesh.select_all(action='DESELECT')

            # context.object.modifiers["SimplyWeld"].show_viewport = True
            # context.object.modifiers["SimplyWeld"].show_in_editmode = True

            # self.setup_animation_gravity(context)



        if self.mode == "CREATE_CUT":
            self.addSewingToSewCollection(context)
            self.createSewing(context)
            self.addSelectionToWeldGroup(context)

        if self.mode == "CREATE_FINE_SEWING":
            self.createFineSewing(context)
        if self.mode == "MERGE_SEWING":
            self.mergeSewing(context)

        if self.mode == "REMOVE_SEWING" or self.mode == "REMOVE_SEWING_UV":
            self.removeSewing(context)
        if self.mode == "EDIT_SEWING":
            self.editSewing(context)
        if self.mode == "DONE":
            self.doneSewing(context)

        return {'FINISHED'}
class PokeFace(bpy.types.Operator):
    bl_idname = "object.poke_faces"
    bl_label = "Poke Faces"
    # bl_description = "Poke Faces Operation"
    mode: StringProperty()

    def duplicateMesh(self,context):
        old_name = bpy.context.active_object.name
        bpy.context.active_object.cloth_status = False
        bpy.ops.object.duplicate()
        bpy.ops.object.select_all(action='DESELECT')
        for i, obj in enumerate(bpy.data.objects):
            print(obj.name)
            if obj.name == old_name:
                # print("TRUE")
                bpy.context.object.cloth_status = True
                bpy.context.object.baseSub_level = 0
    def refreshSelect(self,context):
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_all(action='SELECT')

    def lowPoke(self,context):
        self.refreshSelect(context)
        bpy.ops.mesh.poke()
        bpy.ops.mesh.tris_convert_to_quads()

    def midPoke(self,context):
        self.refreshSelect(context)
        bpy.ops.mesh.subdivide()
        bpy.ops.mesh.poke()
        bpy.ops.mesh.tris_convert_to_quads()

    def execute(self,context):

        if self.mode == "MID":
            self.duplicateMesh(context)
            bpy.ops.object.editmode_toggle()
            self.lowPoke(context)
            bpy.ops.object.editmode_toggle()
        if self.mode == "MAX":
            self.duplicateMesh(context)
            bpy.ops.object.editmode_toggle()
            self.midPoke(context)
            bpy.ops.object.editmode_toggle()


        return {'FINISHED'}
class RemeshCloth(bpy.types.Operator):
    bl_idname = "object.remesh_cloth"
    bl_label = "Remesh Cloth"
    bl_description = "Remesh Cloth Quad based"

    def remesh(self, context):
        target_faces = context.active_object.remesher_face_count
        bpy.ops.object.quadriflow_remesh(use_paint_symmetry=False, use_preserve_sharp=False, use_preserve_boundary=False,
                                            preserve_paint_mask=False, smooth_normals=False, mode='FACES',
                                            target_ratio=1.0,
                                            target_edge_length=0.1, target_faces=target_faces, mesh_area=-1, seed=0)
    def execute(self, context):
        bpy.context.object.show_wireframes = False
        self.remesh(context)
        bpy.context.object.show_wireframes = True
        return {"FINISHED"}
class FinishCloth(bpy.types.Operator):
    bl_idname = "object.finish_cloth"
    bl_label = "Finishing Cloth"
    bl_description = "Apply the Cloth mesh as a static mesh!"
    mode: StringProperty(options={'HIDDEN'})
    saveCloth: BoolProperty(default=False,name="Backup current cloth object", description="Finish Simply Cloth object")
    # applySubdivisionModifier: BoolProperty(name="Apply Subdivision Modifier (Higher Resolution)", default=False)
    # applySolidifyModifier: BoolProperty(name="Apply Solidify Modifier (Thickness)", default=False)
    @classmethod
    def poll(cls, context):
        return context.active_object is not None
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=400)
        # return context.window_manager.invoke_popup(self)


    def duplicateMesh(self,context):
        bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked": False, "mode": 'TRANSLATION'},
                                            TRANSFORM_OT_translate={"value": (0, 0, 0), "orient_type": 'GLOBAL',
                                                                    "orient_matrix": ((1, 0, 0), (0, 1, 0), (0, 0, 1)),
                                                                    "orient_matrix_type": 'GLOBAL',
                                                                    "constraint_axis": (False, False, False), "mirror": True,
                                                                    "use_proportional_edit": False,
                                                                    "proportional_edit_falloff": 'SMOOTH',
                                                                    "proportional_size": 0.148644,
                                                                    "use_proportional_connected": False,
                                                                    "use_proportional_projected": False, "snap": False,
                                                                    "snap_target": 'CLOSEST', "snap_point": (0, 0, 0),
                                                                    "snap_align": False, "snap_normal": (0, 0, 0),
                                                                    "gpencil_strokes": False, "cursor_transform": False,
                                                                    "texture_space": False, "remove_on_cancel": False,
                                                                    "release_confirm": False, "use_accurate": False})
        bpy.context.active_object.name = "Simply_Cloth_Finished"

    def applyModifiers(self, context):
        obj = context.active_object
        for mod in obj.modifiers:
            print(mod.name)
            if mod.type == "HOOK":
                bpy.ops.object.modifier_remove(modifier=mod.name, report=True)
            elif mod.name == "SimplySub" and mod.levels > 0:
                bpy.ops.object.modifier_apply(modifier=mod.name, report=True)
            elif mod.name == "SimplySub" and mod.levels == 0:
                bpy.ops.object.modifier_remove(modifier=mod.name, report=True)
            elif mod.name == "SurfaceDeform":
                if mod.target:
                    bpy.ops.object.modifier_apply(modifier=mod.name, report=True)
                else:
                    bpy.ops.object.modifier_remove(modifier=mod.name, report=True)
                    
            elif self.mode == "APPLYCLOTH" and mod.name == "SimplyCloth" and mod.type == "CLOTH":
                bpy.ops.object.modifier_apply(modifier=mod.name, report=True)
            elif mod.name == "SimplyShrink":
                bpy.ops.object.modifier_remove(modifier=mod.name, report=True)
            elif mod.type == "MIRROR":
                bpy.ops.object.modifier_apply(modifier=mod.name, report=True)


            # if self.applySolidifyModifier == True:
            #     if mod.name == "SimplySolidify":
            #         bpy.ops.object.modifier_apply(modifier=mod.name, report=True)

            elif mod.name == "SimplyDensity" and mod.show_viewport == True:
                bpy.ops.object.modifier_apply(modifier=mod.name, report=True)

            elif mod.name == "SimplyDensity" and mod.show_viewport == False:
                bpy.ops.object.modifier_remove(modifier=mod.name, report=True)

            elif mod.name == "SimplyWeld" and mod.show_viewport == True:
                bpy.ops.object.modifier_apply(modifier=mod.name, report=True)

            elif mod.name == "SimplyWeld" and mod.show_viewport == False:
                bpy.ops.object.modifier_remove(modifier=mod.name, report=True)

            # elif mod.name == "qualityView" and mod.show_viewport == False and self.applySubdivisionModifier == False:
            # 	bpy.ops.object.modifier_remove(modifier=mod.name, report=True)
            # 	if self.mode != "APPLYMODIFIERONLY":
            # 		mod.show_viewport = True
                # bpy.ops.object.modifier_apply(modifier=mod.name, report=True)
            # elif mod.name == "qualityView" and self.mode=="APPLYMODIFIERONLY" or self.mode=="SCULPTCLOTHEXTRA" or self.applySubdivisionModifier == True:
            # 	mod.show_viewport = True
            # 	bpy.ops.object.modifier_apply(modifier=mod.name, report=True)
            elif mod.name == "simplySmooth" and mod.show_viewport==False:
                mod.show_viewport = False

        if self.mode =="APPLYMODIFIERONLY":
            self.deleteBakeCache(context)

    def deleteBakeCache(self,context):
        override = {'scene': bpy.context.scene,'point_cache': bpy.context.active_object.modifiers['SimplyCloth'].point_cache}
        bpy.ops.ptcache.free_bake(override)
        bpy.ops.screen.frame_jump(1)
    def bakeCache(self, context):
        override = {'scene': bpy.context.scene,'point_cache' : bpy.context.active_object.modifiers['SimplyCloth'].point_cache}
        bpy.ops.ptcache.bake(override, bake=False)
    def updateDuplicateMesh(self, context):
        override = {'scene': bpy.context.scene, 'point_cache' : bpy.context.active_object.modifiers['SimplyCloth'].point_cache}
        bpy.ops.ptcache.bake_all(bake=False)
    def checkAndApplyShapeKeys(self, context):
        if bpy.data.shape_keys:
            for k in bpy.data.shape_keys:
                if k:
                    bpy.ops.object.shape_key_remove(all=True)
    def removePinGroup(self, context):
        vertexGroup = context.active_object.vertex_groups
        for group in vertexGroup:
            if group.name == "SimplyPin":
                vertexGroup.remove(group)
        bpy.ops.screen.frame_jump(1)
    def switchToSculptMode(self, context):
        bpy.ops.sculpt.sculptmode_toggle()
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Cloth")
        bpy.context.scene.tool_settings.sculpt.use_symmetry_x = False
        bpy.ops.screen.frame_jump(1)

    def unsubdivideMesh(self,context):
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.unsubdivide()
        bpy.ops.object.editmode_toggle()
    def execute(self,context):
        if self.mode == "SCULPTCLOTHEXTRA":
            if "Mirror" in context.active_object.modifiers:
                bpy.ops.object.modifier_apply(modifier="Mirror", report=True)
            if "BaseSub" in context.active_object.modifiers:
                bpy.ops.object.modifier_apply(modifier="SimplyCloth", report=True)
                context.active_object.modifiers["BaseSub"].levels = 1
            self.applyModifiers(context)
            self.unsubdivideMesh(context)
            self.switchToSculptMode(context)
            context.active_object.clothObjectSculpt = True
        elif self.mode == "SCULPTCLOTH":
            self.switchToSculptMode(context)
        elif self.mode == "APPLYMODIFIERONLY":
            bpy.context.space_data.overlay.show_wireframes = False
            # bpy.context.object.modifiers["qualityView"].show_viewport = False
            self.applyModifiers(context)
        elif self.mode != "SCULPTCLOTHEXTRA" and self.mode != "SCULPTCLOTH" and self.mode != "APPLYMODIFIERONLY":
            bpy.context.space_data.overlay.show_wireframes = False
            # if "qualityView" in bpy.context.active_object.modifiers:
            # 	bpy.context.object.modifiers["qualityView"].show_viewport = False
            self.applyModifiers(context)
            if context.active_object.cloth_sewing:
                bpy.ops.object.editmode_toggle()
                bpy.ops.mesh.select_all(action="DESELECT")
        bpy.context.object.weight_pin_view = False
        bpy.context.object.scs_mode = 'ADJUST'

        return {'FINISHED'}

class DensityWeightPaint(bpy.types.Operator):
    bl_idname = "object.density_paint"
    bl_label = "Density Paint"
    mode:StringProperty(default="FROM_OBJECT")
    def toggleWeight(self,context):
        obj = context.active_object
        if "SimplyCloth" in obj.modifiers:
            if "SimplyDensity" in context.active_object.vertex_groups:
                index =  bpy.context.active_object.vertex_groups["SimplyDensity"].index
                obj.vertex_groups.active_index = index
            else:
                group = bpy.context.object.vertex_groups.new()
                group.name = "SimplyDensity"
        obj.modifiers["SimplyDensity"].show_viewport = False
        bpy.ops.screen.frame_jump(1)
    def setVertexGroupToModifier(self,context):
        obj = context.active_object
        if "SimplyDensity" in context.active_object.modifiers:
            obj.modifiers["SimplyDensity"].vertex_group = "SimplyDensity"
            obj.modifiers["SimplyDensity"].invert_vertex_group = True
            obj.modifiers["SimplyDensity"].ratio = 0.35
            obj.modifiers["SimplyDensity"].show_viewport = True

    def removeGroup(self, context):
        vertexGroup = context.active_object.vertex_groups
        for group in vertexGroup:
            if group.name == "SimplyDensity":
                vertexGroup.remove(group)
        bpy.ops.screen.frame_jump(1)
    def execute(self, context):
        context.space_data.overlay.show_wireframes = False
        if self.mode == "FROM_OBJECT":
            bpy.ops.paint.weight_paint_toggle()
            self.toggleWeight(context)
            self.setVertexGroupToModifier(context)
        elif self.mode == "FROM_EDIT":
            bpy.ops.object.editmode_toggle()
            bpy.ops.paint.weight_paint_toggle()
            self.toggleWeight(context)
            self.setVertexGroupToModifier(context)
        elif self.mode == "HIDE":
            if "SimplyDensity" in context.active_object.modifiers:
                bpy.ops.object.modifier_remove(modifier="SimplyDensity")
                self.removeGroup(context)

        return {'FINISHED'}

class AddHook(bpy.types.Operator):
    bl_idname = "object.add_hook"
    bl_label = "Add Hook"
    bl_description = "Add Hook with selected Vertexgroup"
    mode: StringProperty(default="PIN")
    index: IntProperty(default=0)
    name: StringProperty(default="PinGroup")
    hookLocation = any

    def createHook(self,context):
        bpy.ops.object.hook_add_newob()
        vertName =  self.name
        for i, m in enumerate(context.active_object.modifiers):
            if m.type == 'HOOK':
                if m.vertex_group == "":
                    m.name = vertName
                    bpy.ops.object.modifier_move_to_index(modifier=vertName, index=0)
                    for j, v in enumerate(context.active_object.vertex_groups):
                        if v.name == self.name:
                            m.vertex_group = vertName
                            m.show_expanded = False

        # self.getHookPosition(context, currenvertNametHookObject)

    def getHookPosition(self, context, hookObject):

        currentHookObject = context.active_object.modifiers[hookName].object
        bpy.data.objects[currentHookObject.name].name = hookName
        self.hookLocation = hookObject.location
        bpy.data.objects[currentHookObject.name].name = hookName
        bpy.data.objects[hookName.name].location = self.hookLocation

    def execute(self, context):
        # if self.mode == "PIN":
        self.createHook(context)
        # 	self.getHookPosition(context, self.)
        # elif self.mode == "RESET":
        # 	self.reset
        return {'FINISHED'}

class DeleteHook(bpy.types.Operator):
    bl_idname = "object.delete_hook"
    bl_label = "Delete Hook"
    bl_description = "Delete Hook"

    name: StringProperty(default="PinGroup")

    def deleteModifierHook(self,context):
        vertName = self.name
        bpy.ops.object.modifier_remove(modifier=vertName)
    def deleteHookObject(self,contex):
        vertName = self.name
        for h in contex.active_object.modifiers:
            if h.name == vertName:
                bpy.ops.object.editmode_toggle()
                bpy.ops.object.select_all(action='DESELECT')
                if h.object is not None:
                    if bpy.data.objects[h.object.name_full]:
                        bpy.data.objects[h.object.name_full].select_set(True)
                        bpy.ops.object.delete()
                bpy.ops.object.editmode_toggle()

    def execute(self, context):
        self.deleteHookObject(context)
        self.deleteModifierHook(context)
        return {'FINISHED'}
class CreateWeightPins(bpy.types.Operator):
    bl_idname = "object.create_pin_layers"
    bl_label = "Weightpaint Pin Groups"
    bl_description = "Weightpaint pingroup"
    mode:StringProperty(default="SELECT")
    index:IntProperty(default=0)
    name:StringProperty(default="PinGroup")

    def toogleWeightPaint(self, context):
        if context.mode == "EDIT_MESH":
            bpy.ops.object.editmode_toggle()
            bpy.ops.paint.weight_paint_toggle()
        elif context.mode == "OBJECT":
            bpy.ops.paint.weight_paint_toggle()
    def createVertexPinWeightGroup(self,context):
        obj = context.active_object
        groupName = self.name
        if "SimplyCloth" in obj.modifiers:
            if groupName in context.active_object.vertex_groups:
                index = bpy.context.active_object.vertex_groups[groupName].index
                obj.vertex_groups.active_index = index
            else:
                group = bpy.context.object.vertex_groups.new()
                group.name = groupName

        bpy.ops.screen.frame_jump(1)
    def createMergePinGroup(self,context):
        obj = bpy.context.active_object
        name = self.name
        if "SimplyCloth" in obj.modifiers:
            for g in obj.vertex_groups:
                if g.name == name:
                    name = g.name + "_D"
            group = bpy.context.object.vertex_groups.new()
            group.name = name
    def fillAllVertsWithValue(self,context):
        bpy.ops.object.editmode_toggle()
        obj = context.active_object
        verts = obj.data.vertices
        vertName =  self.name
        for i, group in enumerate(obj.vertex_groups):
            if vertName == group.name:
                for v, vert in enumerate(verts):
                    bpy.context.active_object.vertex_groups[vertName].add([vert.index], 0.0, 'REPLACE')
        bpy.ops.object.editmode_toggle()

    def replaceAllVertsValues(self,context):
        # bpy.ops.object.editmode_toggle()
        obj = context.active_object
        verts = obj.data.vertices
        vertName =  self.name
        if vertName in obj.vertex_slider:
            for v, vert in enumerate(verts):
                bpy.context.active_object.vertex_groups[vertName].add([vert.index], 0.0, 'REPLACE')

    def calcMergedPinGroup(self, context):
        obj = context.active_object
        verts = obj.data.vertices
        groupData = {}
        simplyPinGroup = obj.vertex_groups["SimplyPin"]
        vertexSlider = obj.vertex_slider

        for group in obj.vertex_groups:
            for v in vertexSlider:
                if group.name == v.name:
                    for j, vert in enumerate(verts):
                        for group2 in vert.groups:
                            if group2.group == group.index:
                                if vert.index in groupData:
                                    if not v.hide:
                                        groupData[j] += group2.weight*v.slider_value
                                    else:
                                        groupData[j] += group2.weight*0
                                else:
                                    if not v.hide:
                                        groupData[j] = group2.weight*v.slider_value
                                    else:
                                        groupData[j] = group2.weight*0

        for index in groupData:
            simplyPinGroup.add([index], groupData[index], "REPLACE")

    def selectTargetVertexGroup(self,context):
        vertexSlider = context.active_object.vertex_slider
        vertexGroups = context.active_object.vertex_groups
        vertexSliderName = vertexSlider[self.index].name

        for j, vg in enumerate(vertexGroups):
            for v in vertexSlider:
                v.active= False
            if vg.name == vertexSliderName:
                vertexGroups.active_index = j
                vertexSlider[self.index].active = True
                break
    def selectMixedVertexGroup(self,context):
            vertexSlider = context.active_object.vertex_slider
            vertexGroups = context.active_object.vertex_groups
            vertexSliderName = vertexSlider[self.index].name

            for j, vg in enumerate(vertexGroups):
                if vg.name == "SimplyPin":
                    vertexGroups.active_index = j
                    break
    def selectMergedVertexGroup(self,context):
        vertexSlider = context.active_object.vertex_slider
        vertexGroups = context.active_object.vertex_groups

        for j, vg in enumerate(vertexGroups):
            if vg.name == "SimplyPin":
                vertexGroups.active_index = j
                break
    def assignSelectionToGroup(self,context):
        bpy.ops.object.vertex_group_assign()
    def clearSelectedPinGroup(self, context):
        obj = context.active_object
        verts = obj.data.vertices
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.object.vertex_group_remove_from()
    def execute(self,context):
        if self.mode == "RECALC":
            self.calcMergedPinGroup(context)
        if self.mode == "WEIGHTPAINT":
            bpy.ops.screen.frame_jump(1)
            self.selectTargetVertexGroup(context)
            self.toogleWeightPaint(context)
            # self.createVertexPinWeightGroup(context)

        elif self.mode == "MERGEWEIGHTS":
            # self.createMergePinGroup(context)
            # self.fillAllVertsWithValue(context)
            if context.mode == "EDIT_MESH":
                bpy.ops.object.editmode_toggle()
                self.calcMergedPinGroup(context)
                bpy.ops.object.editmode_toggle()
                bpy.context.object.weight_pin_view = True
            elif context.mode == "OBJECT":
                self.calcMergedPinGroup(context)

        elif self.mode == "ADD":
            self.assignSelectionToGroup(context)
            if context.mode == "EDIT_MESH":
                bpy.ops.object.editmode_toggle()
                self.calcMergedPinGroup(context)
                bpy.ops.object.editmode_toggle()
            elif context.mode == "OBJECT":
                # print("FROM OBJECT MODE")
                self.calcMergedPinGroup(context)
            self.selectMixedVertexGroup(context)
            bpy.ops.screen.frame_jump(1)
        elif self.mode == "DELETE":
            self.deleteSelectedPinGroup(context)
            bpy.ops.screen.frame_jump(1)
        elif self.mode == "SELECT":
            self.selectTargetVertexGroup(context)
        elif self.mode == "SELECTALL":
            self.selectMixedVertexGroup(context)
        elif self.mode == "CLEAR":
            self.selectTargetVertexGroup(context)
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.object.vertex_group_remove_from()
            bpy.context.object.weight_value = 1
            bpy.ops.object.editmode_toggle()
            self.calcMergedPinGroup(context)
            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.screen.frame_jump(1)
        return {'FINISHED'}

class DeleteSlider(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "object.delete_slider"
    bl_label = "Delete Pin Layer"

    index: IntProperty(default=0)

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        vertexSlider = context.active_object.vertex_slider
        vertexGroups = context.active_object.vertex_groups
        vertexSliderName = vertexSlider[self.index].name
        for j, vg in enumerate(vertexGroups):
            if vg.name == vertexSliderName:
                vertexGroups.remove(vg)
                break
        vertexSlider.remove(self.index)
        bpy.ops.screen.frame_jump(1)
        return {'FINISHED'}

class AddPinGroup(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "object.add_pin_operator"
    bl_label = "Add Pin Layer"

    name: StringProperty(default="", name="Slider Name")
    weight_value: FloatProperty(default=1.0, min=0.0, max=1.0, name="Weight Value")

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def invoke(self, context, event):

        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        slider = context.active_object.vertex_slider.add()
        obj = context.active_object

        for g in obj.vertex_groups:
            if g.name == self.name:
                self.name = g.name + "_duplicate"
        group = bpy.context.object.vertex_groups.new()
        group.name = self.name

        slider.name = self.name
        context.active_object.weight_value = self.weight_value
        bpy.ops.object.create_pin_layers(mode="ADD", name=self.name)
        bpy.ops.object.create_pin_layers(mode="MERGEWEIGHTS", name=self.name)
        return {'FINISHED'}

class AddSelectionToLayer(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "object.add_selection_to_layer"
    bl_label = "Add Pin Layer"

    weight_value: FloatProperty(default=1.0, min=0.0, max=1.0, name="Weight Value")

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):

        context.active_object.weight_value = self.weight_value
        for i, slider in enumerate(context.active_object.vertex_slider):
            if slider.active:
                activeIndex= i

        bpy.ops.object.create_pin_layers(mode="SELECT", index=activeIndex)
        bpy.ops.object.create_pins(mode="APPLY", index=activeIndex)
        return {'FINISHED'}
class CreatePins(bpy.types.Operator):
    bl_idname = "object.create_pins"
    bl_label = "Assign or Weightpaint Pins"
    mode:StringProperty(default="SELECT")
    index:IntProperty(default=0)
    weightValue:FloatProperty(default=1.0)
    def toggleMode(self, context):
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.select_all(action="DESELECT")
        if "SimplyPin" in context.active_object.vertex_groups:
            bpy.ops.object.vertex_group_select()

    def toggleWeight(self,context):
        bpy.ops.object.editmode_toggle()
        self.createVertexGroup(context)
        bpy.ops.object.editmode_toggle()
        bpy.ops.paint.weight_paint_toggle()
        self.addVertexGroupToCloth(context)

    def assignSelectionToGroup(self,context):
        bpy.ops.object.vertex_group_assign()

    def selectVertexGroupByIndex(self,context):
        vertexSlider = context.active_object.vertex_slider
        vertexGroups = context.active_object.vertex_groups
        vertexSliderName = vertexSlider[self.index].name

        for j, vg in enumerate(vertexGroups):
            if vg.name == vertexSliderName:
                vertexGroups.active_index = j
                break

    def clearAllVertices(self, context):
        obj = context.active_object
        verts = obj.data.vertices
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.object.vertex_group_remove_from()
    def recalcMergedPinGroup(self, context):
        obj = context.active_object
        verts = obj.data.vertices
        groupData = {}
        simplyPinGroup = obj.vertex_groups["SimplyPin"]
        vertexSlider = obj.vertex_slider

        for group in obj.vertex_groups:
            for v in vertexSlider:
                if group.name == v.name:
                    for j, vert in enumerate(verts):
                        for group2 in vert.groups:
                            if group2.group == group.index:
                                if vert.index in groupData:
                                    if not v.hide:
                                        groupData[j] += group2.weight * v.slider_value
                                    else:
                                        groupData[j] += group2.weight * 0
                                else:
                                    if not v.hide:
                                        groupData[j] = group2.weight * v.slider_value
                                    else:
                                        groupData[j] = group2.weight * 0

        for index in groupData:
            simplyPinGroup.add([index], groupData[index], "REPLACE")
    def apply(self, context):
        self.selectVertexGroupByIndex(context)
        self.assignSelectionToGroup(context)
        bpy.ops.screen.frame_jump(1)
        for mod in context.active_object.modifiers:
            if mod.name == "BaseSub":
                context.active_object.modifiers["BaseSub"].show_in_editmode = True
            # elif mod.name == "qualityView":
            # 	context.active_object.modifiers["qualityView"].show_in_editmode = True
            elif mod.name == "simplySmooth":
                context.active_object.modifiers["simplySmooth"].show_in_editmode = True
        bpy.ops.object.editmode_toggle()
        self.recalcMergedPinGroup(context)
        bpy.ops.object.editmode_toggle()
    def removeGroup(self, context):
        vertexGroup = context.active_object.vertex_groups
        for group in vertexGroup:
            if group.name == "SimplyPin":
                vertexGroup.remove(group)
    def remove_fromEdit_Group(self, context):
        vertexGroup = context.active_object.vertex_groups
        for group in vertexGroup:
            if group.name == "SimplyPin":
                vertexGroup.remove(group)
                bpy.ops.mesh.select_all(action="DESELECT")
        if self.mode == "REMOVE_FROM_EDIT":
            bpy.ops.mesh.select_all(action="DESELECT")
            bpy.ops.object.editmode_toggle()
    def execute(self, context):
        obj = context.active_object.modifiers
        for mod in obj:
            if mod.name == "SimplySub" or mod.name == "simplySmooth" or mod.name == "SimplyThickness":
                if mod.name == "SimplySub":
                    obj["SimplySub"].show_in_editmode = False
                if mod.name == "simplySmooth":
                    obj["simplySmooth"].show_in_editmode = False
                if mod.name == "SimplyThickness":
                    obj["SimplyThickness"].show_in_editmode = False
        if self.mode == "SELECT":
            self.toggleMode(context)
        elif self.mode == "WEIGHT":
            self.toggleWeight(context)
        elif self.mode == "CLEAR":
            bpy.ops.object.editmode_toggle()
            bpy.ops.object.vertex_group_select()
            self.clearAllVertices(context)
            bpy.ops.object.editmode_toggle()
        elif self.mode == "APPLY":
            self.apply(context)
        elif self.mode == "REMOVE":
            self.removeGroup(context)
        elif self.mode == "REMOVE_FROM_EDIT":
            self.remove_fromEdit_Group(context)
        elif self.mode == "SELECT_ASSIGNED_PINS":
            bpy.ops.object.vertex_group_select()
        elif self.mode == "REMOVE_SELECTED":
            bpy.ops.object.vertex_group_remove_from()
            bpy.ops.mesh.select_all(action="DESELECT")
            bpy.ops.object.vertex_group_select()
        screen = bpy.ops.screen
        screen.frame_jump(1)
        return {'FINISHED'}
class ResetClothParameter(bpy.types.Operator):
    bl_idname = "object.reset_parameters"
    bl_label = "Reset all Cloth Parameters"
    bl_description = "Reset Cloth Parameters!"
    def execute(self, context):
        if "SimplyCloth" in context.active_object.modifiers:
            bpy.ops.object.modifier_move_up()
            bpy.context.object.self_collision = False
            bpy.context.object.modifiers["SimplyCloth"].settings.mass = 0.3
            bpy.context.object.stiffness_slider = 66
            bpy.context.object.fold_slider = 0.1
            bpy.context.object.wrinkle_slider = 66
            bpy.context.object.shrink_slider = 0
            if "simplySmooth" in context.active_object.modifiers:
                bpy.context.object.modifiers["simplySmooth"].iterations = 0
            bpy.context.object.cloth_sewing = False
            bpy.context.object.modifiers["SimplyCloth"].settings.sewing_force_max = 3
            bpy.context.object.internal_spring = False
            bpy.context.object.pressure = False
            bpy.context.object.advanced_settings = False
            bpy.context.object.modifiers["SimplyCloth"].settings.effector_weights.gravity = 0.6
            bpy.context.object.quality_steps_slider = 8
            bpy.context.object.collision_quality_slider = 4
            bpy.context.object.selfCollisionDistance_slider = 0.01
            bpy.context.object.strenghten_slider = 20




            bpy.context.object.presets = 'STANDARD'
            # bpy.context.object.templates = 'STANDARD'
            bpy.ops.object.modifier_remove()
        return {'FINISHED'}
class RemoveModifier(bpy.types.Operator):
    bl_idname = "object.remove_cloth"
    bl_label = "Remove Simply Cloth"
    bl_description = "Deletes Cloth and the modifiers from the selected mesh!"

    def removePinGroup(self, context):
        vertexGroup = context.active_object.vertex_groups
        for group in vertexGroup:
            if group.name == "SimplyPin" or \
                    group.name == "SimplyWeld" or \
                    group.name == "SimplyStrength" or \
                    group.name == "SimplyShrink" or \
                    group.name == "SimplyPressure":
                vertexGroup.remove(group)
        bpy.ops.screen.frame_jump(1)
    def execute(self, context):
        obj = context.active_object
        obj.cloth_sewing = False
        obj.internal_spring = False
        obj.pressure = False
        obj.self_collision = False
        obj.advanced_settings = False
        obj.face_orientation = False
        obj.show_wireframes = False
        obj.presets = 'STANDARD'
        for mod in obj.modifiers:
            if mod.name == "SimplySub"or \
                    mod.name == "SimplySub" or \
                    mod.name == "SurfaceDeform" or \
                    mod.name == "SimplyCloth" or \
                    mod.name == "SimplySolidify" or \
                    mod.name == "SimplyDensity" or \
                    mod.name == "SimplyWeld" or \
                    mod.name == "SimplyThickness" or \
                    mod.name == "SimplyShrink" or \
                    mod.name =="simplySmooth" or \
                    mod.name =="SimplySubsurf":
                obj.modifiers.remove(mod)
        self.removePinGroup(context)
        context.active_object.is_SimplyCloth = False
        return {'FINISHED'}
class RemoveWind(bpy.types.Operator):
    bl_idname = "scene.remove_wind"
    bl_label = "Remove Wind"
    bl_description = "Remove Wind from Scene"

    def removeWind(self, context):
        for i, obj in enumerate(bpy.data.objects):
            if "Wind" in obj.name_full:
                bpy.data.objects.remove(bpy.data.objects[i])
    def resetWindValues(self, context):
        context.scene.sc_wind_factor = 1.0
        context.scene.sc_wind_slider = 10.0

    def execute(self, context):
        self.removeWind(context)
        self.resetWindValues(context)
        return {'FINISHED'}
class RemoveSimplyClothMesh(bpy.types.Operator):
    bl_idname = "object.remove_simply_mesh"
    bl_label = "Remove Simply Cloth Mesh"
    bl_description = "Remove Simply Cloth created Mesh"
    def removeMesh(self, context):
        bpy.ops.object.delete()
    def execute(self, context):
        self.removeMesh(context)
        return {'FINISHED'}
class FlipNormals(bpy.types.Operator):
    bl_idname = "object.flip_normals"
    bl_label = "Flip Normals"
    bl_description = "Flip Faces Orientation"

    def execute(self,context):
        bpy.ops.mesh.select_linked(delimit={'SEAM'})
        bpy.ops.mesh.flip_normals()
        return {'FINISHED'}
class SubdivideCloth(bpy.types.Operator):
    bl_idname = "object.subdivide_cloth"
    bl_label = "Subdivide Mesh"
    bl_description = "The resolution of the mesh can be set here. (+) subdivide the mesh and increase the resolution, (-) un-subdivide and decreases the resolution of the mesh!"

    mode: StringProperty(default="SUBDIVIDE")
    def fillAllVertsWithValue(self,context):
        bpy.ops.object.editmode_toggle()
        obj = context.active_object
        verts = obj.data.vertices
        vertName =  self.name
        for i, group in enumerate(obj.vertex_groups):
            if vertName == group.name:
                for v, vert in enumerate(verts):
                    bpy.context.active_object.vertex_groups[vertName].add([vert.index], 0.001, 'REPLACE')
        bpy.ops.object.editmode_toggle()

    def execute(self, context):
        # create
        obj = context.active_object
        if self.mode == "SUBDIVIDE" or self.mode == "UNSUBDIVIDE":
            for mod in obj.modifiers:
                if mod.name == "BaseSub" and self.mode == "SUBDIVIDE":
                    mod.levels = mod.levels + 1
                elif mod.name == "BaseSub" and self.mode == "UNSUBDIVIDE":
                    mod.levels = mod.levels - 1
            screen = bpy.ops.screen
            screen.frame_jump(1)
        else:
            if self.mode == "SUBDIVIDE_EDIT":
                bpy.ops.mesh.select_all(action="SELECT")
                bpy.ops.mesh.subdivide()
            elif self.mode == "UNSUBDIVIDE_EDIT":
                bpy.ops.mesh.select_all(action="SELECT")
                bpy.ops.mesh.unsubdivide()
            bpy.ops.mesh.select_all(action="DESELECT")
        bpy.context.object.show_wireframes = True

        bpy.ops.screen.frame_jump(1)
        return {'FINISHED'}
class CreateCloth(bpy.types.Operator):
    bl_idname = "object.create_cloth"
    bl_label = "Create Cloth to selected Object"
    bl_description = "Creates a Simply Cloth Pro Mesh!"
    mode : StringProperty(default="FROM_OBJECT_MODE", options={'HIDDEN'})
    shrinkToCollision:BoolProperty(name="Shrink to Collision", description="Shrink to Collision if exists", default=False, options={"HIDDEN"})
    originObject = any
    nearestCollisionObject = StringProperty(default="")
    

    # # selectedObject: EnumProperty(items=[], name="select object", description="Select Object to Attach selected Object")
    # @classmethod
    # def poll(cls, context):
    # 	return context.active_object is not None

    # def invoke(self, context, event):
    # 	if self.mode == "CLOTHFROMSCULPT":
    # 		# return context.active_object is not None
    # 		return self.execute(context)
    # 	else:
    # 		return context.window_manager.invoke_props_dialog(self)
    def setup_animation_gravity(self, context):
        # print("GRAVITY ANIMATION ADDED")
        if "SimplyCloth" in context.active_object.modifiers:
            context.active_object.modifiers["SimplyCloth"].settings.effector_weights.gravity = -0.5
            bpy.context.active_object.modifiers["SimplyCloth"].settings.effector_weights.keyframe_insert(
                data_path='gravity', frame=0)
            
            context.active_object.modifiers["SimplyCloth"].settings.effector_weights.gravity = 1
            bpy.context.active_object.modifiers["SimplyCloth"].settings.effector_weights.keyframe_insert(
                data_path='gravity', frame=6)
            
    def add_base_sub_modifier(self, context):
        obj = context.active_object
        levels = 0
        if "SimplySub" not in obj.modifiers:
            # obj.modifiers.new("BaseSub", "SUBSURF")
            obj.modifiers.new("SimplySub", "SUBSURF")
            
            obj.modifiers["SimplySub"].levels = levels
            obj.modifiers["SimplySub"].render_levels = levels

            # obj.modifiers["SimplySub"].subdivision_type = "SIMPLE"
            obj.modifiers["SimplySub"].use_creases = False
            obj.modifiers["SimplySub"].use_limit_surface = False

    def add_cloth_sub_modifier(self, context):
        obj = context.active_object
        if "SimplySubsurf" not in obj.modifiers:
            obj.modifiers.new("SimplySubsurf", "SUBSURF")
            obj.modifiers["SimplySubsurf"].levels = 2
            obj.modifiers["SimplySubsurf"].levels = 2
            obj.modifiers["SimplySubsurf"].show_in_editmode = False

            # obj.modifiers["SimplySubsurf"].subdivision_type = "SIMPLE"
    def add_cloth_surfaceDeform_modifier(self, context):
        obj = context.active_object
        if "SurfaceDeform" not in obj.modifiers:
            obj.modifiers.new("SurfaceDeform", "SURFACE_DEFORM")
            if self.find_nearest_collision_object(obj):
                obj.modifiers["SurfaceDeform"].target = bpy.data.objects[self.nearestCollisionObject]
            # obj.modifiers["SimplySubsurf"].subdivision_type = "SIMPLE"
            
    def create_cloth(self,context):
        obj = context.active_object
        # obj.name = "simply_cloth"
        if "SimplyCloth" not in obj.modifiers:
            obj.modifiers.new("SimplyCloth","CLOTH")
            obj.modifiers["SimplyCloth"].settings.use_sewing_springs= True
            obj.modifiers["SimplyCloth"].settings.sewing_force_max= 4.0
            obj.modifiers["SimplyCloth"].settings.time_scale= 0.5

    def smoothViewModifier(self, context):
        obj = context.active_object
        # if "qualityView" not in obj.modifiers:
        # 	obj.modifiers.new("qualityView", "SUBSURF")
        # 	obj.modifiers["qualityView"].show_viewport = True
        # 	obj.modifiers["qualityView"].show_in_editmode = False
        if "simplySmooth" not in obj.modifiers:
            obj.modifiers.new("simplySmooth", "SMOOTH")
            obj.modifiers["simplySmooth"].iterations = 0

    def setCollisionParameters(self, context):
        obj = context.active_object
        obj.modifiers["SimplyCloth"].collision_settings.distance_min = 0.01
        obj.modifiers["SimplyCloth"].collision_settings.collision_quality = 4
        obj.modifiers["SimplyCloth"].collision_settings.self_distance_min = 0.001

    def createVertexGroup(self, context):
        obj = context.active_object
        if "SimplyCloth" in obj.modifiers:
            group = bpy.context.object.vertex_groups.new()
            group.name = "SimplyPin"
            verts = obj.data.vertices

    def addVertexGroupToCloth(self,context):
        obj = context.active_object
        if "SimplyCloth" in obj.modifiers:
            mod = obj.modifiers["SimplyCloth"]
            mod.settings.vertex_group_mass = "SimplyPin"

    def addPinVertexGroupToSurfaceDeform(self,context):
        obj = context.active_object
        if "SurfaceDeform" in obj.modifiers:
            mod = obj.modifiers["SurfaceDeform"]
            mod.vertex_group = "SimplyPin"
    def add_thickness(self, context):
        obj = context.active_object
        value = FloatProperty(default=0.0)
        if "SimplyThickness" not in obj.modifiers:
            mod = obj.modifiers.new("SimplyThickness", "SOLIDIFY")
            mod.thickness = 0
            mod.show_viewport = False
            mod.show_in_editmode = False

    def add_decimate_modifier(self,context):
        obj = context.active_object
        if "SimplyDensity" not in obj.modifiers:
            mod = obj.modifiers.new("SimplyDensity", "DECIMATE")
            mod.show_viewport = False
            mod.show_in_editmode =False

    def hide_expanded(self, context):
        obj = context.active_object
        for mod in obj.modifiers:
            if mod.name == "BaseSub" or mod.name == "SimplySubsurf" or mod.name == "SimplyCloth" or mod.name == "simplySmooth":
                mod.show_expanded = False

    def add_weld_modifier(self,context):
        obj = context.active_object
        if "SimplyWeld" not in obj.modifiers:
            mod = obj.modifiers.new("SimplyWeld", "WELD")
            mod.merge_threshold = 0.025
            mod.show_viewport = False
            mod.show_in_editmode= False
            mod.show_render= False

        
    def add_edge_split(self,context):
        obj = context.active_object
        mod = obj.modifiers.new(name="Edge Split", type="EDGE_SPLIT")
        mod.use_edge_angle = False

        
    def add_shrinkWrap_modifier(self, context):
        obj = context.active_object

        nearestObject = self.find_nearest_collision_object(obj)
        # print(nearestObject)
        if nearestObject:
            mod = obj.modifiers.new("SimplyShrink", "SHRINKWRAP")

            mod.offset = 0.02
            mod.wrap_mode = "OUTSIDE"

            mod.target = bpy.data.objects[nearestObject.name]

            mod.show_viewport = True
            mod.keyframe_insert(
            data_path='show_viewport', frame=1)

            mod.show_viewport = False
            mod.keyframe_insert(
            data_path='show_viewport', frame=2)

            mod.show_viewport = False
            self.nearestCollisionObject = nearestObject.name
            
    def find_nearest_collision_object(self, active_obj):
        all_objects = bpy.context.scene.objects
        # Filter objects to find those with a collision modifier
        collision_objects = [obj for obj in all_objects if obj != active_obj and "SimplyCollision" in obj.modifiers]
        print(collision_objects)
        if not collision_objects:
            return None
        
        # Filter objects to exclude the reference object itself
        other_objects = [obj for obj in all_objects if obj != active_obj]
        
        if not other_objects:
            return None
        
        # Calculate the distances between the reference object and other objects
        distances = [(obj, (active_obj.location - obj.location).length) for obj in collision_objects]
        
        # Find the nearest object
        nearest_obj, nearest_distance = min(distances, key=lambda x: x[1])
                
        return nearest_obj

    def addSewVertexGroupToWeld(self,context):
        group = bpy.context.object.vertex_groups.new()
        group.name = "SimplyWeld"
        # bpy.ops.object.vertex_group_assign()

    def addStrengthenVertexGroup(self,context):
        group = bpy.context.object.vertex_groups.new()
        group.name = "SimplyStrength"

    def addShrinkVertexGroup(self,context):
        group = bpy.context.object.vertex_groups.new()
        group.name = "SimplyShrink"

    def addBindVertexGroup(self,context):
        group = bpy.context.object.vertex_groups.new()
        group.name = "SimplyBind"

    def setup_animation_shrink_vertexGroup(self, context):
        if "SimplyCloth" in context.active_object.modifiers:
            context.active_object.modifiers["SimplyCloth"].settings.shrink_max = 0
            bpy.context.active_object.modifiers["SimplyCloth"].settings.keyframe_insert(
                data_path='shrink_max', frame=10)
            context.active_object.modifiers["SimplyCloth"].settings.shrink_max = 0.5
            bpy.context.active_object.modifiers["SimplyCloth"].settings.keyframe_insert(
                data_path='shrink_max', frame=30)
        # bpy.ops.object.vertex_group_assign()
    def sewVertexGroupToWeld(self, context):
        obj = context.active_object
        mod = obj.modifiers["SimplyWeld"]
        mod.vertex_group= "SimplyWeld"

    def strengthVertexGroupToStrength(self, context):
        obj = context.active_object
        mod = obj.modifiers["SimplyCloth"]
        mod.settings.vertex_group_bending = "SimplyStrength"

    def shrinkVertexGroupToShrink(self, context):
        obj = context.active_object
        mod = obj.modifiers["SimplyCloth"]
        mod.settings.vertex_group_shrink = "SimplyShrink"

    def addPressureVertexGroup(self,context):
        if context.mode == "OBJECT":
            bpy.ops.object.editmode_toggle()
        group = bpy.context.object.vertex_groups.new()
        group.name = "SimplyPressure"

        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.object.vertex_group_assign()
        if context.mode == "OBJECT":
            bpy.ops.object.editmode_toggle()

    def refreshAllVertexGroupsWithValue(self,context):
        obj = context.active_object
        verts = obj.data.vertices
        for i, group in enumerate(obj.vertex_groups):
            if group.name == "SimplyPin":
                print("no Vertex Group Addition")
            else:
                for j, vert in enumerate(verts):
                    bpy.context.active_object.vertex_groups[i].add([vert.index], 0, 'REPLACE')

    def addSolidifyModifier(self, context):
        obj = context.active_object
        if "SimplySolidify" not in obj.modifiers:
            mod = obj.modifiers.new("SimplySolidify", "SOLIDIFY")
            mod.show_viewport = False
            mod.show_in_editmode = False
            mod.offset = 1
            mod.thickness = 0.01
        else:
            obj.thicknessBeforeAfterCloth = False
            ui_panel.update_thicknessOverClothModifier

    def setValues(self, context):
        obj = context.active_object
        if self.mode == "SELECTCREATECLOTH":
            obj.quality_steps_slider = 8
        else:
            obj.modifiers["SimplyCloth"].settings.quality = obj.quality_steps_slider
    def create(self,context):
        print("CREATE")
        # if self.shrinkToCollision == True:
        self.add_shrinkWrap_modifier(context)
        self.add_base_sub_modifier(context)
        self.add_cloth_surfaceDeform_modifier(context)
        # self.add_decimate_modifier(context)
        self.create_cloth(context)
        self.add_weld_modifier(context)
        self.add_edge_split(context)
        self.smoothViewModifier(context)
        self.setCollisionParameters(context)
        self.addSewVertexGroupToWeld(context)
        self.sewVertexGroupToWeld(context)
        self.addStrengthenVertexGroup(context)
        self.addShrinkVertexGroup(context)
        self.addBindVertexGroup(context)
        self.setup_animation_gravity(context)
        # self.setup_animation_shrink_vertexGroup(context)
        self.strengthVertexGroupToStrength(context)
        self.shrinkVertexGroupToShrink(context)
        self.addPressureVertexGroup(context)

        
        self.setValues(context)
        

        if context.mode == "OBJECT":
            self.createVertexGroup(context)
            self.addVertexGroupToCloth(context)
            
        elif context.mode =="EDIT_MESH":
            bpy.ops.object.editmode_toggle()
            self.createVertexGroup(context)
        self.addVertexGroupToCloth(context)
        self.hide_expanded(context)
        if self.mode == "CREATE_FROM_EDIT":
            bpy.ops.object.editmode_toggle()
        bpy.ops.screen.frame_jump(1)
        bpy.context.object.weight_pin_view = False
        self.addSolidifyModifier(context)
        self.add_cloth_sub_modifier(context)
        self.addPinVertexGroupToSurfaceDeform(context)

    def separateSelection(self, context):
        bpy.ops.mesh.duplicate_move(MESH_OT_duplicate={"mode":1}, TRANSFORM_OT_translate={"value":(0, 0, 0), "orient_type":'GLOBAL', "orient_matrix":((1, 0, 0), (0, 1, 0), (0, 0, 1)), "orient_matrix_type":'GLOBAL', "constraint_axis":(False, False, False), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_target":'CLOSEST', "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "release_confirm":False, "use_accurate":False, "use_automerge_and_split":False})
        bpy.ops.mesh.separate(type='SELECTED')

    def addSelectionToPinGroup(self, context):
        bpy.ops.object.editmode_toggle()
        if "SimplyPin" in context.active_object.vertex_groups:
            bpy.ops.object.vertex_group_select()
            bpy.ops.object.vertex_group_assign()

        bpy.ops.object.editmode_toggle()

    def selectSeparatedObject(self, context):
        for i in bpy.context.selected_objects:
            if i.mode == "OBJECT":
                bpy.context.view_layer.objects.active = bpy.data.objects[i.name]

    def subdivideSelectedFaces(self, context):
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.subdivide()

    def selectBoundsForPinning(self, context):
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
        bpy.ops.mesh.select_non_manifold(extend=False, use_wire=False, use_boundary=True, use_multi_face=False,
                                            use_non_contiguous=False, use_verts=False)
        bpy.ops.object.editmode_toggle()


    def addBoundingAsPinning(self, context):
        vertexGroups = context.active_object.vertex_groups

        for j, vg in enumerate(vertexGroups):
            if vg.name == "SimplyPin":
                vertexGroups.active_index = j
                break
        bpy.ops.object.vertex_group_assign()
        bpy.ops.object.editmode_toggle()
    def invertSelectionAndRemove(self, context):
        if context.mode== "OBJECT":
            bpy.ops.object.editmode_toggle()

        bpy.ops.mesh.select_all(action='INVERT')
        bpy.ops.mesh.delete(type='FACE')
    
    def setupSkinThight(self, context):
        #Add Shrink Modifier
        if self.mode == "SKINTIGHT" or self.mode == "SKINTIGHT_OBJECT":
            for mod in context.active_object.modifiers:
                if mod.name == "geometry_extract_solidify":
                    context.active_object.modifiers.remove(mod)
            if self.mode == "SKINTIGHT":
                context.active_object.modifiers.new("SimplyShrinkWrap", "SHRINKWRAP")
                context.active_object.modifiers["SimplyShrinkWrap"].wrap_mode = "ABOVE_SURFACE"
                context.active_object.modifiers["SimplyShrinkWrap"].offset = 0.0005
                context.active_object.modifiers["SimplyShrinkWrap"].target = bpy.data.objects[self.originObject.name]
            context.active_object.sc_UI_Enhance = True
            bpy.context.object.scs_mode = 'DESIGN'


        #Add Smooth Modifier
        if self.mode == "SKINTIGHT":
            context.active_object.modifiers.new("SimplySmooth", 'SMOOTH')
            bpy.context.object.modifiers["SimplySmooth"].factor = 0.5
            bpy.context.object.modifiers["SimplySmooth"].iterations = 0

        bpy.ops.object.sc_setup_simply_geo_nodes()

        # bpy.ops.object.modifier_add(type='SOLIDIFY')
        context.active_object.modifiers.new("SimplySolidify", "SOLIDIFY")
        bpy.context.object.modifiers["SimplySolidify"].offset = 0
        bpy.context.object.modifiers["SimplySolidify"].thickness = 0.002
        bpy.context.object.modifiers["SimplySolidify"].thickness = 0.002


        context.active_object.modifiers.new("SimplySubdivision", "SUBSURF")
        bpy.context.object.modifiers["SimplySubdivision"].levels = 1
        bpy.context.object.modifiers["SimplySubdivision"].use_limit_surface = False
        # bpy.ops.mesh.duplicate_move(MESH_OT_duplicate={"mode":1} )

    def checkforArmature(self, context):
        cloth = context.active_object
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

        targetObject = None
        armature = None

        # if "SimplyCloth" not in context.active_object.modifiers:
        if "SimplyShrink" in context.active_object.modifiers:
            
            if context.active_object.modifiers["SimplyShrink"].target:
                targetObject = context.active_object.modifiers["SimplyShrink"].target

                for mod in targetObject.modifiers:
                    if mod.type == "ARMATURE":
                        armature = mod.object

        if armature:
            bpy.ops.object.select_all(action='DESELECT')
            context.view_layer.objects[cloth.name].select_set(True)
            bpy.context.view_layer.objects.active = armature
            if bpy.context.object.data.pose_position == "POSE":
                self.report({'INFO'}, "Armature was set to Rest Position")
                bpy.context.object.data.pose_position = 'REST'
                bpy.ops.object.parent_set(type ="ARMATURE_AUTO")
                bpy.context.view_layer.objects.active = cloth
                bpy.ops.object.modifier_move_to_index(modifier="Armature", index=0)
                bpy.context.view_layer.objects.active = armature

                # bpy.context.object.data.pose_position = 'POSE'
            else:
                bpy.ops.object.parent_set(type ="ARMATURE_AUTO")
                bpy.context.view_layer.objects.active = cloth
                bpy.ops.object.modifier_move_to_index(modifier="Armature", index=0)
                bpy.context.view_layer.objects.active = armature
                # bpy.context.object.data.pose_position = 'POSE'
            bpy.context.view_layer.objects.active = cloth
            bpy.context.object.modifiers["Armature"].show_in_editmode = True
            bpy.context.object.modifiers["Armature"].show_on_cage = True


    def execute(self, context):
        # self.checkforArmature(context)
        if self.mode == "CREATE_FROM_EDIT":
            bpy.ops.object.editmode_toggle()
            self.create(context)
        if self.mode == "CLOTHFROMSCULPT":
            context.space_data.overlay.show_wireframes = False
            bpy.ops.screen.frame_jump(1)
            if context.active_object.clothObjectSculpt == True:
                bpy.ops.sculpt.sculptmode_toggle()
                self.create(context)
                bpy.ops.screen.frame_jump(1)
            else:
                bpy.ops.sculpt.sculptmode_toggle()
        elif self.mode == "CREATECLOTH":
            for mod in context.active_object.modifiers:
                if mod.name == "geometry_extract_solidify":
                    context.active_object.modifiers.remove(mod)
            self.create(context)
            # self.setup_animation_gravity(context)
            context.scene.sc_last_cloth_object.append(bpy.data.objects[context.active_object.name])
        elif self.mode == "SELECTCREATECLOTH":
            print(context.mode)
            bpy.ops.object.editmode_toggle()
            bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked":False, "mode":'TRANSLATION'}, TRANSFORM_OT_translate={"value":(0, 0, 0), "orient_type":'GLOBAL', "orient_matrix":((0, 0, 0), (0, 0, 0), (0, 0, 0)), "orient_matrix_type":'GLOBAL', "constraint_axis":(False, False, False), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_target":'CLOSEST', "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "view2d_edge_pan":False, "release_confirm":False, "use_accurate":False, "use_automerge_and_split":False})
            bpy.ops.object.editmode_toggle()
            bpy.ops.transform.shrink_fatten(value=0.008, use_even_offset=False, mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
            self.invertSelectionAndRemove(context)
            
            if context.active_object.subdivideOnSeparation == True:
                # print("Subdivie bro")
                self.subdivideSelectedFaces(context)
                # self.subdivideSelectedFaces(context)
            # bpy.ops.object.editmode_toggle()

            self.create(context)	
            self.selectBoundsForPinning(context) 
            # bpy.ops.object.editmode_toggle()
            # self.subdivideSelectedFaces(context)
            # bpy.ops.object.editmode_toggle()
            self.addSelectionToPinGroup(context)

            bpy.context.object.presets = 'PRESSURE'
            bpy.context.object.pressure_factor_slider = 10
            bpy.context.object.pressure_intensity_slider = 10
            bpy.context.object.modifiers["SimplyCloth"].settings.mass = 0.1
            bpy.context.object.modifiers["SimplyCloth"].settings.effector_weights.gravity = 0


            ui_panel.slide_pressure_factor
            ui_panel.slide_pressure_intensity
            bpy.ops.object.shade_smooth()

            if context.active_object.triangulateOnSeparation == True:
                bpy.ops.object.sc_dyntopo_triangulation(mode="SELECTCREATECLOTH")
            bpy.ops.screen.animation_manager(mode="PLAY")

        elif self.mode == "SKINTIGHT" or self.mode == "SKINTIGHT_SCULPT" or self.mode == "SKINTIGHT_OBJECT":
            self.originObject = context.active_object

            if self.mode == "SKINTIGHT":
                bpy.ops.object.editmode_toggle()
                
                bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked":False, "mode":'TRANSLATION'}, TRANSFORM_OT_translate={"value":(0, 0, 0), "orient_type":'GLOBAL', "orient_matrix":((0, 0, 0), (0, 0, 0), (0, 0, 0)), "orient_matrix_type":'GLOBAL', "constraint_axis":(False, False, False), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_target":'CLOSEST', "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "view2d_edge_pan":False, "release_confirm":False, "use_accurate":False, "use_automerge_and_split":False})
                bpy.ops.object.editmode_toggle()

                # bpy.ops.object.editmode_toggle()
                self.invertSelectionAndRemove(context)
                
                bpy.ops.object.editmode_toggle()
                context.active_object.sc_UI_Enhance = True

            elif self.mode == "SKINTIGHT_SCULPT":
                print("SCULPTMODE")
                self.originObject = context.active_object
                bpy.ops.mesh.face_set_extract()
                for mod in context.active_object.modifiers:
                    if mod.name == "geometry_extract_solidify":
                        context.active_object.modifiers.remove(mod)

                context.active_object.sc_UI_Enhance = True
            elif self.mode == "SKINTIGHT_OBJECT":
                bpy.ops.object.editmode_toggle()
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.transform.shrink_fatten(value=0.0005, use_even_offset=False, mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
                bpy.ops.object.editmode_toggle()


            self.setupSkinThight(context)

            if context.mode == "OBJECT":
                bpy.ops.object.shade_smooth()
                bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        context.active_object.is_SimplyCloth = True
        bpy.ops.object.shade_smooth()

        # self.checkforArmature(context)
        

        return {'FINISHED'}

class StrengthenSelection(bpy.types.Operator):
    bl_idname = "object.strengthen_selection"
    bl_label = "Set selection as Strength Group"
    mode:StringProperty(default="ADD")
    def addSelectionToStrengthGroup(self, context):
        bpy.ops.object.vertex_group_set_active(group='SimplyStrength')
        bpy.ops.object.vertex_group_assign()
    def clearSelection(self, context):
        bpy.ops.object.vertex_group_set_active(group='SimplyStrength')
        bpy.ops.object.vertex_group_remove_from()
    def execute(self, context):
        if self.mode == "ADD":
            self.addSelectionToStrengthGroup(context)
        elif self.mode == "CLEAR":
            self.clearSelection(context)
        return {'FINISHED'}

class ShrinkSelection(bpy.types.Operator):
    bl_idname = "object.shrink_selection"
    bl_label = "Set selection as Shrink Group"
    mode:StringProperty(default="ADD")
    def addSelectionToShrinkGroup(self, context):
        bpy.ops.object.vertex_group_set_active(group='SimplyShrink')
        bpy.ops.object.vertex_group_assign()
    def clearSelection(self, context):
        bpy.ops.object.vertex_group_set_active(group='SimplyShrink')
        bpy.ops.object.vertex_group_remove_from()

    def execute(self, context):
        if self.mode == "ADD":
            self.addSelectionToShrinkGroup(context)
        elif self.mode == "REMOVE":
            self.clearSelection(context)
        
        return {'FINISHED'}

class PressureSelection(bpy.types.Operator):
    bl_idname = "object.pressure_assign_group"
    bl_label = "Pressure Group Selection"

    mode:StringProperty(default="ASSIGN")
    def calcMergedPinGroup(self, context):
        obj = context.active_object
        verts = obj.data.vertices
        groupData = {}
        simplyPinGroup = obj.vertex_groups["SimplyPin"]
        vertexSlider = obj.vertex_slider

        for group in obj.vertex_groups:
            for v in vertexSlider:
                if group.name == v.name:
                    for j, vert in enumerate(verts):
                        for group2 in vert.groups:
                            if group2.group == group.index:
                                if vert.index in groupData:
                                    if not v.hide:
                                        groupData[j] += group2.weight*v.slider_value
                                    else:
                                        groupData[j] += group2.weight*0
                                else:
                                    if not v.hide:
                                        groupData[j] = group2.weight*v.slider_value
                                    else:
                                        groupData[j] = group2.weight*0

        for index in groupData:
            if context.mode == "EDIT_MESH":
                bpy.ops.object.editmode_toggle()
                simplyPinGroup.add([index], groupData[index], "REPLACE")
            elif context.mode == "OBJECT":
                simplyPinGroup.add([index], groupData[index], "REPLACE")
    def addVertexGroupToPressure(self, context):
        obj = context.active_object
        mod = obj.modifiers["SimplyCloth"]
        mod.settings.vertex_group_pressure = "SimplyPressure"

    def paintPressureGroup(self, context):
        bpy.ops.object.vertex_group_set_active(group='SimplyPressure')

        # bpy.context.object.modifiers["qualityView"].show_viewport = False
        # bpy.context.object.modifiers["qualityView"].show_in_editmode = False
        # bpy.context.object.modifiers["BaseSub"].show_viewport = False
        # bpy.context.object.modifiers["BaseSub"].show_in_editmode = False
        bpy.ops.paint.weight_paint_toggle()
        bpy.context.scene.tool_settings.unified_paint_settings.weight = 0
        bpy.ops.screen.frame_jump(1)

    def addSelectionToPressureGroup(self, context):
        obj = context.active_object
        verts = obj.data.vertices
        # vertName =  self.name
        bpy.ops.object.vertex_group_set_active(group='SimplyPressure')
        context.active_object.weight_value = 0
        bpy.ops.object.vertex_group_assign()
        context.active_object.weight_value = 1
    def clearPressureGroup(self, context):
        bpy.ops.object.vertex_group_set_active(group='SimplyPressure')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.object.vertex_group_remove_from()
        bpy.ops.mesh.select_all(action='SELECT')
        context.active_object.weight_value = 1
        bpy.ops.object.vertex_group_assign()

    def execute(self, context):
        if self.mode == "ASSIGN":
            self.addSelectionToPressureGroup(context)
            self.addVertexGroupToPressure(context)
        elif self.mode == "PAINT":
            self.paintPressureGroup(context)
            self.addVertexGroupToPressure(context)
            if not bpy.context.screen.is_animation_playing:
                bpy.ops.screen.animation_manager(mode="PLAY")
        elif self.mode == "REMOVE":
            if context.mode == "OBJECT":
                bpy.ops.object.editmode_toggle()
                self.clearPressureGroup(context)
                bpy.ops.object.editmode_toggle()
            elif context.mode == "EDIT_MESH":
                self.clearPressureGroup(context)
            self.calcMergedPinGroup(context)
        bpy.ops.screen.frame_jump(1)
        return {'FINISHED'}
    
class LivePinningPaint(bpy.types.Operator):
    bl_idname = "object.live_pinning"
    bl_label = "Live painting Pin Group"

    def execute(self, context):
        bpy.context.space_data.overlay.show_wireframes = False

        # bpy.context.object.modifiers["qualityView"].show_viewport = False
        # bpy.context.object.modifiers["qualityView"].show_in_editmode = False
        if context.mode == "OBJECT":
            bpy.ops.object.shade_smooth()
            if not bpy.context.screen.is_animation_playing:
                bpy.ops.screen.animation_manager(mode="PLAY")
        bpy.ops.paint.weight_paint_toggle()
        bpy.ops.object.vertex_group_set_active(group='SimplyPin')
        bpy.context.scene.tool_settings.unified_paint_settings.weight = 1
        if "BaseSub" in context.object.modifiers:
            bpy.context.object.modifiers["BaseSub"].show_viewport = False
            bpy.context.object.modifiers["BaseSub"].show_in_editmode = False
        bpy.context.object.modifiers["SimplyCloth"].settings.effector_weights.gravity = 0.25

        bpy.ops.screen.frame_jump(1)

        return {'FINISHED'}
class ClearSimplyPin(bpy.types.Operator):
    bl_idname = "object.clear_simply_pin"
    bl_label = "Clear Pin Group"

    def execute(self, context):
        if context.mode == "OBJECT":
            bpy.ops.object.editmode_toggle()
            bpy.ops.object.vertex_group_set_active(group='SimplyPin')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.object.vertex_group_remove_from()
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.editmode_toggle()
        elif context.mode == "EDIT_MESH":
            bpy.ops.object.vertex_group_set_active(group='SimplyPin')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.object.vertex_group_remove_from()
            bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.screen.frame_jump(1)
        if "BaseSub" in context.object.modifiers:
            bpy.context.object.modifiers["BaseSub"].show_viewport = True
            bpy.context.object.modifiers["BaseSub"].show_in_editmode = True

        return {'FINISHED'}
class SelectClothSculptBrush(bpy.types.Operator):
    bl_idname = "object.sculpt_brush"
    bl_label = "Switch to Cloth Sculpt"
    mode: StringProperty(default="STANDARD")

    def switchToSculptMode(self, context):
        bpy.ops.sculpt.sculptmode_toggle()
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Cloth")
        bpy.context.scene.tool_settings.sculpt.use_symmetry_x = False
        bpy.ops.screen.frame_jump(1)

    def execute(self, context):
        bpy.ops.object.shade_smooth()
        if self.mode == "SCULPTCLOTH":
            self.switchToSculptMode(context)
            # context.active_object.clothObjectSculpt = False

        elif self.mode == "NOCLOTH":
            bpy.ops.sculpt.sculptmode_toggle()

        return {'FINISHED'}

class SelectForceFalloff(bpy.types.Operator):
    bl_idname = "object.sculpt_brush_falloff"
    bl_label = "Select Brush Force Falloff"
    mode: StringProperty(default="RADIAL")

    def switchToSculptMode(self, context):
        bpy.ops.sculpt.sculptmode_toggle()
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Cloth")
        bpy.context.scene.tool_settings.sculpt.use_symmetry_x = False
        bpy.ops.screen.frame_jump(1)

    def execute(self, context):
        bpy.ops.object.shade_smooth()
        if self.mode == "RADIAL":
            context.active_object.brushForceFalloff = True
            bpy.data.brushes["Cloth"].cloth_force_falloff_type = 'RADIAL'
            # context.active_object.clothObjectSculpt = False
        elif self.mode == "PLANE":
            context.active_object.brushForceFalloff = False
            bpy.data.brushes["Cloth"].cloth_force_falloff_type = 'PLANE'

        return {'FINISHED'}

class SculptMaskOperator(bpy.types.Operator):
    bl_idname = "object.sculpt_brush_mask"
    bl_label = "Sculpt Mask Functions"
    mode: StringProperty(default="MASK")

    def selectMaskBrush(self, context):
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Mask")

    def invertMask(self, context):
        bpy.ops.paint.mask_flood_fill(mode='INVERT')

    def cleanMask(self, context):
        bpy.ops.paint.mask_flood_fill(mode='VALUE', value=0)

    def execute(self, context):
        if self.mode == "MASK":
            self.selectMaskBrush(context)
        elif self.mode == "INVERT":
            self.invertMask(context)
        elif self.mode == "CLEANMASK":
            self.cleanMask(context)
        return {'FINISHED'}

class SculptSubdivision(bpy.types.Operator):
    bl_idname = "object.sculpt_subdivide"
    bl_label = "Mesh Resolution Subdivide or Un-Subdivide"
    mode:StringProperty(default="SUB")
    def subdivide(self, context):
        bpy.ops.mesh.subdivide()

    def unSubdivide(self, context):
        bpy.ops.mesh.unsubdivide()

    def selectAll(self, context):
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_all(action='SELECT')

    def switchToEdit(self, context):
        bpy.ops.object.editmode_toggle()

    def switchToSculpt(self, context):
        bpy.ops.sculpt.sculptmode_toggle()

    def execute(self, context):
        self.switchToEdit(context)
        self.selectAll(context)
        if self.mode == "SUB":
            self.subdivide(context)
        elif self.mode == "UNSUB":
            self.unSubdivide(context)
        self.switchToSculpt(context)
        return{"FINISHED"}

class SculptMeshShading(bpy.types.Operator):
    bl_idname = "object.sculpt_shade"
    bl_label = "Mesh Shader Smooth/ Flat"
    mode:StringProperty(default="SMOOTH")
    def smooth(self, context):
        bpy.ops.object.shade_smooth()

    def flat(self, context):
        bpy.ops.object.shade_flat()


    def switchToObject(self, context):
        bpy.ops.sculpt.sculptmode_toggle()

    def switchToSculpt(self, context):
        bpy.ops.sculpt.sculptmode_toggle()

    def execute(self, context):
        self.switchToObject(context)
        if self.mode == "SMOOTH":
            self.smooth(context)
        elif self.mode == "FLAT":
            self.flat(context)
        self.switchToSculpt(context)
        return{"FINISHED"}

class LoadTemplatesFromBlend(bpy.types.Operator):
    bl_idname = "scene.load_template"
    bl_label = "Load Cloth Templates"
    template_name:StringProperty(default="STANDARD")
    def loadMesh(self, context):
        # addons_path = bpy.utils.user_resource(resource_type="SCRIPTS", path="addons")
    

        rootdir = dirname(dirname(__file__))
        addons_path = join(rootdir, "simply_cloth_studio")
        # icons_dir = join(addons_dir, "icons")





        # addons_path = bpy.utils.user_resource(resource_type="EXTENSIONS", path="user_default")
        # folderName = "simply_cloth_studio"

        # script_path = os.path.join(addons_path, folderName)
    
        template_dir = join(addons_path, "template\library.blend")
        print(template_dir)

        # name of object(s) to append or link
        obj_name = self.template_name
        # print(obj_name)
        # print(self.template_name)

        # append, set to true to keep the link to the original file
        link = False

        # link all objects starting with 'Cube'
        with bpy.data.libraries.load(template_dir, link=link) as (data_from, data_to):
            data_to.objects = [name for name in data_from.objects if name == self.template_name]

        # link object to current scene
        for obj in data_to.objects:
            if obj is not None:
                # print("TRUE-------------")
                bpy.context.collection.objects.link(obj)

    def execute(self, context):
        if context.mode == "OBJECT":
            # print(self.template_name)
            self.loadMesh(context)

        return {'FINISHED'}

class AddWindToScene(bpy.types.Operator):
    bl_idname = "scene.sc_add_wind"
    bl_label = "Add Wind Force to Scene"
    bl_description ="Add Wind to your Scene and adjust with Strenght and Intensity"
    def addWindToScene(self, context):
        bpy.ops.view3d.snap_cursor_to_center()
        bpy.ops.object.effector_add(type='WIND', enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
        bpy.ops.transform.rotate(value=-1.5708, orient_axis='X', orient_type='GLOBAL',
                                    orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL',
                                    constraint_axis=(True, False, False), mirror=True, use_proportional_edit=False,
                                    proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False,
                                    use_proportional_projected=False)
        bpy.ops.transform.translate(value=(0, 0, 1), orient_type='GLOBAL',
                                    orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL',
                                    constraint_axis=(False, False, True), mirror=True, use_proportional_edit=False,
                                    proportional_edit_falloff='SMOOTH', proportional_size=1,
                                    use_proportional_connected=False, use_proportional_projected=False)
    def setWindProperties(self, context):
        bpy.context.object.field.strength = 7500.00

    def execute(self, context):
        self.addWindToScene(context)
        self.setWindProperties(context)
        return {'FINISHED'}

class CleanModifiers(bpy.types.Operator):
    bl_idname = "object.sc_clean_modifiers"
    bl_label = "Clean Modifiers"
    bl_description ="Clean up Modifiers - Delete all"

    
    def cleanSimplyModifiers(self, context):
        for mod in context.active_object.modifiers:
            if "simply" in mod.name or "Simply" in mod.name:
                bpy.ops.object.modifier_remove(modifier=mod.name)

    def execute(self, context):
        self.cleanSimplyModifiers(context)


        return {'FINISHED'}

class ClothDyntopoTriangulation(bpy.types.Operator):
    bl_idname = "object.sc_dyntopo_triangulation"
    bl_label = "Dyntopo Triangulation"
    bl_description ="Dyntopo Triangulation"
    bl_options = {'REGISTER', 'UNDO'}
    mode:StringProperty(default="DEFAULT")

    def addDyntopoTriangulation(self, context):
        bpy.ops.sculpt.sculptmode_toggle()
        bpy.ops.sculpt.dynamic_topology_toggle()
        bpy.ops.sculpt.sculptmode_toggle()

    def subdividePrepare(self, context):
        if context.mode == "OBJECT":
            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
            bpy.ops.mesh.select_non_manifold(extend=True, use_wire=True, use_boundary=True,use_multi_face=True,use_non_contiguous=True, use_verts=True)
            bpy.ops.mesh.select_all(action='INVERT')
            # self.addDyntopoTriangulation(context)
            # self.addToFaceMap(context)
            if self.mode == "DYNTOPO":
                self.addDyntopoTriangulation(context)
            elif self.mode == "DEFAULT":
                self.setLevelOfDetail(context)
                self.rotateFacesAndTriangulate(context)
            # self.simplyTriangulate(context)
            bpy.ops.object.editmode_toggle()
            

    def addToFaceMap(self, context):
        bpy.ops.object.face_map_add()
        bpy.ops.object.face_map_assign()
        objname = context.active_object.name
        bpy.data.objects[objname].face_maps['FaceMap'].name = "SimplyFaceMap"

    def setLevelOfDetail(self, context):
        if context.scene.sc_triangulation_level == 1:
            bpy.ops.mesh.unsubdivide()
        if context.scene.sc_triangulation_level == 2:
            bpy.ops.mesh.tris_convert_to_quads()

            # bpy.ops.mesh.subdivide()
        if context.scene.sc_triangulation_level == 3:
            bpy.ops.mesh.subdivide()
        

    def simplyTriangulate(self, context):
        if context.scene.sc_triangulation_level == 1:
            bpy.ops.mesh.unsubdivide()
        if context.scene.sc_triangulation_level == 2:
            bpy.ops.mesh.unsubdivide()
        # bpy.ops.mesh.unsubdivide()
        # bpy.ops.mesh.tris_convert_to_quads()
        # bpy.ops.mesh.poke()
        
        # bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
        bpy.ops.object.editmode_toggle()
        
        # if "BaseSub" in context.object.modifiers:
        # 	bpy.context.object.modifiers["BaseSub"].subdivision_type = 'CATMULL_CLARK'
        # 	# 	bpy.context.object.modifiers["BaseSub"].levels =  1
        # # if context.scene.sc_triangulation_level == 3:
        # 	bpy.context.object.modifiers["BaseSub"].levels =  1
        # 	bpy.ops.object.modifier_apply(modifier="BaseSub")
        # bpy.ops.object.modifier_apply(modifier="qualityView")

        # bpy.ops.object.editmode_toggle()
        # if context.scene.sc_triangulation_level == 3:
        # 	bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
        # if context.scene.sc_triangulation_level == 2:
        # 	bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
        # bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')


    def rotateFacesAndTriangulate(self, context):
        if context.mode == "OBJECT":
            bpy.ops.object.editmode_toggle()
        # bpy.ops.object.select_all(action='SELECT')
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
        # bpy.ops.mesh.inset(thickness=0.02, depth=0)
        bpy.ops.mesh.poke()
        bpy.ops.mesh.tris_convert_to_quads()
        bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
        if self.mode == "ROTATE":
            bpy.ops.mesh.tris_convert_to_quads()
        # bpy.ops.object.editmode_toggle()
            
    def rotateFacesFromSelection(self, context):
        if context.mode == "OBJECT":
            bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.poke()
        bpy.ops.mesh.tris_convert_to_quads()
        bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
        
        bpy.ops.mesh.tris_convert_to_quads()

    def duplicateMesh(self,context):
        old_name = bpy.context.active_object.name
        bpy.context.active_object.cloth_status = False
        bpy.ops.object.duplicate()

        bpy.ops.object.select_all(action='DESELECT')
        for i, obj in enumerate(bpy.data.objects):
            # print(obj.name)
            if obj.name == old_name:
                # print("TRUE")
                obj.hide_set(True)
                obj.cloth_status = True
                obj.baseSub_level = 0
        # bpy.context.active_object.cloth_status = True

    def execute(self, context):
        if self.mode == "ROTATE_SELECTION":
            self.rotateFacesFromSelection(context)
        else:
            if bpy.context.view_layer.objects.active.select_get() == True:
                if context.mode == "EDIT_MESH":
                    self.rotateFacesAndTriangulate(context)
                else:
                    self.duplicateMesh(context)
                self.subdividePrepare(context)
                if self.mode == "ROTATE":
                    self.rotateFacesAndTriangulate(context)
        
        if self.mode == "ROTATE":
            self.rotateFacesAndTriangulate(context)
            
        return {'FINISHED'}
class RefreshClothParameters(bpy.types.Operator):
    bl_idname = "scene.sc_refresh_parameter"
    bl_label = "Refresh Cloth Parameters"
    bl_description ="Refresh changed Cloth Parameters"

    def executeAllUpdateFunctions(self, context):
        obj = context.active_object
        obj.modifiers["SimplyCloth"].settings.quality = obj.quality_steps_slider
        obj.modifiers['SimplyCloth'].settings.use_sewing_springs = obj.cloth_sewing

    def execute(self, context):
        self.executeAllUpdateFunctions(context)
        bpy.context.object.presets = 'STANDARD'
        presets.set_preset(self=any, context=context, presetName="STANDARD")
        return {'FINISHED'}

class AutoSewing(bpy.types.Operator):
    bl_idname = "object.sc_auto_sewing"
    bl_label = "Auto Sewing Operator"
    bl_description ="Close Sewing holes after finishing sewed cloth patterns"
    mode : StringProperty(default="AUTO_SEWING")

    def removeSewingFirst(self, context):
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
        bpy.ops.mesh.select_non_manifold(extend=False, use_wire=True, use_boundary=False,use_multi_face=False,use_non_contiguous=False,use_verts=False)
        bpy.ops.mesh.delete(type='EDGE')

    def selectSewingAndMerge(self, context):
        obj_name = bpy.context.active_object.name
        print(len(context.active_object.sc_sew_collection))
        for i, sewIndex in enumerate(context.active_object.sc_sew_collection):
            for select in context.active_object.sc_sew_collection[i]:
                bpy.ops.object.editmode_toggle()
                bpy.data.objects[obj_name].data.vertices[select].select = True
                bpy.ops.object.editmode_toggle()
            bpy.ops.object.editmode_toggle()
            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
            bpy.ops.mesh.bridge_edge_loops(type='SINGLE', merge_factor=0, twist_offset=0, number_cuts=1, 
            interpolation='LINEAR', smoothness=1, profile_shape_factor=0)
            # bpy.ops.mesh.bridge_edge_loops(type='SINGLE', merge_factor=0, use_merge =True, twist_offset=0, number_cuts=1, 
            # interpolation='LINEAR', smoothness=1, profile_shape_factor=0)
            
            bpy.ops.mesh.select_less()
            bpy.ops.mesh.mark_seam(clear=False)
            bpy.ops.mesh.mark_sharp()


            
            bpy.ops.mesh.select_all(action='DESELECT')

    def execute(self, context):
        bpy.ops.mesh.select_all(action='DESELECT')

        self.removeSewingFirst(context)
        self.selectSewingAndMerge(context)
        # bpy.context.active_object.sc_sew_collection.clear()
        # bpy.ops.object.editmode_toggle()
        # bpy.ops.object.editmode_toggle()
        return {'FINISHED'}

class AutoExtrudeEdges(bpy.types.Operator):
    bl_idname = "object.sc_autoextrude_edges"
    bl_label = "Auto Extrude Selection"
    bl_description ="EXPERIMENTAL - WORK IN PROGRESS"

    def extrudeEdges(self, context):
        bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"use_normal_flip":False, "use_dissolve_ortho_edges":False, "mirror":False}, TRANSFORM_OT_translate={"value":(0, 0, 0),  "orient_type":'GLOBAL', "orient_matrix":((1, 0, 0), (0, 1, 0), (0, 0, 1)), "orient_matrix_type":'GLOBAL', "constraint_axis":(False, False, False), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_target":'CLOSEST', "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "view2d_edge_pan":False, "release_confirm":False, "use_accurate":False, "use_automerge_and_split":False})
        bpy.ops.transform.shrink_fatten(value=0.2, use_even_offset=False, mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
        bpy.ops.mesh.select_all(action='INVERT')
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
        bpy.ops.mesh.select_all(action='INVERT')
        bpy.ops.uv.smart_project(correct_aspect=True, scale_to_bounds=True)

    def assignMaterial(self, context):
        materials = bpy.data.materials

        for i, mat in enumerate(materials):
            if mat.name == "Extrude":
                bpy.context.object.active_material_index = i
                bpy.ops.object.material_slot_assign()


    def execute(self, context):
        self.extrudeEdges(context)
        self.assignMaterial(context)
        return {'FINISHED'}

class OpenURL(bpy.types.Operator):
    bl_idname = "scene.open_urls"
    bl_label = "Support other Developers"
    bl_description = "Support other Developers"
    mode:StringProperty(default="STANDARD")

    def openURL(self, context):
        bpy.ops.wm.url_open(url="https://www.youtube.com/watch?v=RrYNnrUxwIo&list=PLxLikJ_FS7uW9EsjiSRUSHSdspcn4wZc6/?ref=159")
    
    def openURL_ASSETS(self, context):
        bpy.ops.wm.url_open(url="https://blendermarket.com/products/simply-asset-packs/?ref=159")
    
    def openURL_MATS(self, context):
        bpy.ops.wm.url_open(url="https://blendermarket.com/products/extreme-pbr-addon-for-blender-279-2/?ref=159")
                
    def openURL_HDRI_Maker(self, context):
        bpy.ops.wm.url_open(url="https://blendermarket.com/products/hdri-maker/?ref=159")
            
    def openURL_RIGS(self, context):
        bpy.ops.wm.url_open(url="https://blendermarket.com/products/auto-rig-pro/?ref=159")
                    
    def openURL_VOXELHEAT(self, context):
        bpy.ops.wm.url_open(url="https://blendermarket.com/products/voxel-heat-diffuse-skinning/?ref=159")
                    
    def openURL_CHIPP(self, context):
        bpy.ops.wm.url_open(url="https://blendermarket.com/creators/altuit/?ref=159")
        
    def openURL_KCYCLES(self, context):
        bpy.ops.wm.url_open(url="https://blendermarket.com/products/k-cycles/?ref=159")
        
    def openURL_HUMANEGEN(self, context):
        bpy.ops.wm.url_open(url="https://blendermarket.com/products/humgen3d/?ref=159")
            
    def openURL_IMAGETO3D(self, context):
        bpy.ops.wm.url_open(url="https://blendermarket.com/products/tracegenius-pro/?ref=159")
        
    def openURL_CLOTHSMOTION(self, context):
        bpy.ops.wm.url_open(url="https://blendermarket.com/creators/xane-graphics/?ref=159")
        
    def openURL_POLYHAVEN(self, context):
        bpy.ops.wm.url_open(url="https://blendermarket.com/creators/polyhaven?ref=159")
    
    def openURL_WOLFSMARKT(self, context):
        bpy.ops.wm.url_open(url="https://blendermarket.com/creators/wolfs-thingsandstuff?ref=159")
    
    def openURL_BARTOSZ_HAIRTOOL(self, context):
        bpy.ops.wm.url_open(url="https://gumroad.com/a/511151827/Dbhj")
        
    def openURL_BARTOSZ_GARMENT(self, context):
        bpy.ops.wm.url_open(url="https://gumroad.com/a/511151827/MAnWP")
                
    def openURL_KAGIARMOR(self, context):
        bpy.ops.wm.url_open(url="https://blendermarket.com/products/kagi-vision-armor-pack/?ref=159")
                
    def openURL_SANCTUS(self, context):
        bpy.ops.wm.url_open(url="https://blendermarket.com/creators/sanctus?ref=159")
        
    def openURL_SHAPESHIFT(self, context):
        bpy.ops.wm.url_open(url="https://blendermarket.com/creators/shapeshift?ref=159")
        
    def openURL_SIMPLYADDONS(self, context):
        bpy.ops.wm.url_open(url="https://blendermarket.com/creators/vjaceslavt/?ref=159")
        
    def openURL_DOC(self, context):
        bpy.ops.wm.url_open(url="https://docs.google.com/document/d/1xYTW1D-_UBNLJrqQ3899ahOQJ_zCjS-v4XWOWQK7mQ0/edit?usp=sharing")
            
    def openURL_CUSTOMERSUPPORT(self, context):
        bpy.ops.wm.url_open(url="https://form.jotform.com/vjaceslavt/simply-problem")
    
    def execute(self, context):
        if self.mode == "VIDEOS":
            self.openURL(context)
        elif self.mode == "CLOTH":
            self.openURL_ASSETS(context)

        elif self.mode == "MATS":
            self.openURL_MATS(context)
                                                                                                
        elif self.mode == "HDRI":
            self.openURL_HDRI_Maker(context)

        elif self.mode == "RIGS":
            self.openURL_RIGS(context)
                                                                                                
        elif self.mode == "VOXELHEAT":
            self.openURL_VOXELHEAT(context)

        elif self.mode == "CHIPP":
            self.openURL_CHIPP(context)

        elif self.mode == "KCYCLES":
            self.openURL_KCYCLES(context)

        elif self.mode == "HUMANGEN":
            self.openURL_HUMANEGEN(context)

        elif self.mode == "CLOTHSMOTION":
            self.openURL_CLOTHSMOTION(context)
                                                                                                
        elif self.mode == "POLYHAVEN":
            self.openURL_POLYHAVEN(context)
                                                                                                
        elif self.mode == "WOLFSMARKT":
            self.openURL_WOLFSMARKT(context)
                                                                                                
        elif self.mode == "HAIRTOOL":
            self.openURL_BARTOSZ_HAIRTOOL(context)
                                                                                                
        elif self.mode == "GARMENTTOOL":
            self.openURL_BARTOSZ_GARMENT(context)
                                    
        elif self.mode == "ARMORPACK":
            self.openURL_KAGIARMOR(context)
            
        elif self.mode == "SANCTUS":
            self.openURL_SANCTUS(context)
            
        elif self.mode == "SHAPESHIFT":
            self.openURL_SHAPESHIFT(context)

        elif self.mode == "SIMPLYADDONS":
            self.openURL_SIMPLYADDONS(context)

        elif self.mode == "DOCS":
            self.openURL_DOC(context)

        elif self.mode == "CUSTOMERSUPPORT":
            self.openURL_CUSTOMERSUPPORT(context)
        return {'FINISHED'}
    
class RemeshSimplyClothTriangulation(bpy.types.Operator):
    bl_idname = "object.remesh_simply_cloth_triangulation"
    bl_label = "Simply Cloth Remesher"
    bl_description = "Remesh for Simply Clothing"
    # SPECIAL THANKS THOMAS KOLE / Thanks of his work I could figure out how to do this nice triangulation!

    meshBounding= []
    meshBoundingKDTree = any
    meshBVHTree = any

    triangulationResolution = FloatProperty
    triangulationIteration = IntProperty
    useQuads = BoolProperty
    useReshape = BoolProperty

    def checkQualityLevel(self, context):
        context.active_object.sc_triangulation_resolution = context.object.sc_triangulation_resolution*0.01

    def getObjectMeshData(self, context):
        self.object = bpy.context.active_object
        self.bmeshObject = bmesh.new()
        self.bmeshObject.from_mesh(self.object.data)
        self.meshBVHTree = BVHTree.FromBMesh(self.bmeshObject)

        self.triangulationResolution = context.active_object.sc_triangulation_resolution
        self.triangulationIteration = context.active_object.sc_triangulation_iteration
        self.useQuads = context.active_object.sc_cutdraw_trian_quad
        self.useShape = context.active_object.sc_triangulation_reshape

        for edge in self.bmeshObject.edges:
            if edge.is_boundary:
                v = (edge.verts[0].co - edge.verts[1].co).normalized()
                center = (edge.verts[0].co + edge.verts[1].co) * 0.5
                self.meshBounding.append((center, v))

        self.meshBoundingKDTree = KDTree(len(self.meshBounding))

        for boundVerticeIndex , (center, vec) in enumerate(self.meshBounding):
            self.meshBoundingKDTree.insert(center, boundVerticeIndex)

        self.meshBoundingKDTree.balance()

    def getBoundingVertices(self, location):
        location, index, dist = self.meshBoundingKDTree.find(location)
        location, vec = self.meshBounding[index]
        return vec

    def setEdgeLengthTriangulationsResolution(self, edge_length=triangulationResolution, bias=0.333):

        upper_length = edge_length + edge_length * bias
        lower_length = edge_length - edge_length * bias
        subdivideEdges = []
        for edge in self.bmeshObject.edges:
            if edge.calc_length() > upper_length:
                subdivideEdges.append(edge)
        
        bmesh.ops.subdivide_edges(self.bmeshObject, edges=subdivideEdges, cuts=1)
        bmesh.ops.triangulate(self.bmeshObject, faces=self.bmeshObject.faces)
        
        removeVertices = []
        for vert in self.bmeshObject.verts:
            if len(vert.link_edges) < 5:
                if not vert.is_boundary:
                    removeVertices.append(vert)
        
        bmesh.ops.dissolve_verts(self.bmeshObject, verts=removeVertices)
        bmesh.ops.triangulate(self.bmeshObject, faces=self.bmeshObject.faces)
        
        fixedVerticed = set(vert for vert in self.bmeshObject.verts if vert.is_boundary)
        collapse = []
        
        for edge in self.bmeshObject.edges:
            if edge.calc_length() < lower_length and not edge.is_boundary:
                verts = set(edge.verts)
                if verts & fixedVerticed:
                    continue
                collapse.append(edge)
                fixedVerticed |= verts
        
        bmesh.ops.collapse(self.bmeshObject, edges=collapse, uvs=True)
        bmesh.ops.beautify_fill(self.bmeshObject, faces=self.bmeshObject.faces, method="ANGLE")
        
    def vertAlignment(self, rule=(-1, -2, -3, -4)):
        for vert in self.bmeshObject.verts:
            if not vert.is_boundary:
                vec = self.getBoundingVertices(vert.co)
                neighborLocations = [edge.other_vert(vert).co for edge in vert.link_edges]
                betterLoactions = sorted(neighborLocations, 
                                        key = lambda n_loc: abs((n_loc - vert.co).normalized().dot(vec)))
                co = vert.co.copy()
                le = len(vert.link_edges)
                for i in   rule:
                    co += betterLoactions[i % le]
                co /= len(rule) + 1
                co -= vert.co
                co -= co.dot(vert.normal) * vert.normal
                vert.co += co
                
    def reshape(self):
        for vert in self.bmeshObject.verts:
            location, normal, index, dist = self.meshBVHTree.find_nearest(vert.co)
            if location:
                vert.co = location
                
    def simplyTriangulate(self,context, edge_length=triangulationResolution, iterations=triangulationIteration, quads=True, reproject=True):
        self.getObjectMeshData(context)
        
        wm = bpy.context.window_manager
        wm.progress_begin(0, 99)
        if quads:
            rule = (-1,-2, 0, 1)
        else:
            rule = (0, 1, 2, 3)
        
        for i in range(iterations):
            wm.progress_update(i/iterations)
            self.setEdgeLengthTriangulationsResolution(edge_length=self.triangulationResolution)
            self.vertAlignment(rule=rule)
            if reproject:
                self.reshape()
        if quads:
            bmesh.ops.join_triangles(self.bmeshObject, faces=self.bmeshObject.faces,
                                        angle_face_threshold=3.33,
                                        angle_shape_threshold=3.33)
        return self.bmeshObject

    def execute(self, context):
        self.getObjectMeshData(context)
        tempBmesh = self.simplyTriangulate(context, self.triangulationResolution, self.triangulationIteration, self.useQuads, self.useShape)
        tempBmesh.to_mesh(self.object.data)
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.editmode_toggle()
        context.area.tag_redraw()
        return {'FINISHED'}

class SimulationToKeyFrame(bpy.types.Operator):
    ######### SPECIAL THANKS TO XANE GRAPHICS ###########
    bl_idname = "object.cloth_to_keyframes"
    bl_label = "Convert Simulation Cache to Keyframe"
    # mode:StringProperty(default="SUB")
    

    def removeModifiers(self, context, deformObject):
        for mod in deformObject.modifiers:
            bpy.ops.object.modifier_remove(modifier=mod.name)

    def cacheToKeyframes(self, context):
        originObject = context.active_object
        deformObject = any
        deformObject_name = "SC_Key"
        bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked":False, "mode":'TRANSLATION'}, TRANSFORM_OT_translate={"value":(0, 0, 0), "orient_type":'GLOBAL', "orient_matrix":((1, 0, 0), (0, 1, 0), (0, 0, 1)), "orient_matrix_type":'GLOBAL', "constraint_axis":(False, False, False), "mirror":True, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_target":'CLOSEST', "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "release_confirm":False, "use_accurate":False})
        deformObject = context.active_object
        deformObject.name = deformObject_name

        self.fixEdges(context)
        self.removeModifiers(context, deformObject)

        bpy.context.scene.frame_set(bpy.context.scene.frame_start)
        bpy.ops.object.modifier_add(type='SURFACE_DEFORM')

        deformObject.modifiers["SurfaceDeform"].target = bpy.data.objects[originObject.name]
        bpy.ops.object.surfacedeform_bind(modifier="SurfaceDeform")
        
        self.recordKeys(context)

    def fixEdges(self, context):
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
        bpy.ops.mesh.select_non_manifold(extend=False, use_wire=True, use_boundary=False, use_multi_face=False, use_non_contiguous=False, use_verts=False)
        bpy.ops.mesh.delete(type='EDGE')
        bpy.ops.object.editmode_toggle()

    def recordKeys(self, context):
        for frame in range(context.scene.frame_current, context.scene.frame_end + 1):
            context.object.modifiers["SurfaceDeform"].name = str(context.active_object.name) + str(frame)
            bpy.ops.object.modifier_copy(modifier= str(context.active_object.name) + str(frame))

            context.scene.frame_set(frame+1)
            bpy.ops.object.modifier_apply_as_shapekey(keep_modifier=False, modifier= str(context.active_object.name) + str(frame))
            context.scene.frame_set(bpy.context.scene.frame_current)
            
        bpy.ops.object.modifier_remove(modifier="SurfaceDeform")

        frames = bpy.context.scene.frame_end + 1
        for frame in range(1, frames):
            for sKey in bpy.data.shape_keys:
                for i, key in enumerate(sKey.key_blocks):
                    if key.name.startswith(str(bpy.context.active_object.name)):
                        curr = i + 1
                        if curr != frame:
                            key.value = 0
                            key.keyframe_insert("value", frame = frame)
                        else:
                            key.value = 1
                            key.keyframe_insert("value", frame = frame) 
    def execute(self, context):
        self.cacheToKeyframes(context)
        return{"FINISHED"}
    
class AttachSelectedToCloth(bpy.types.Operator):
    bl_idname = "object.attach_selected_to_cloth"
    bl_label = "Attach as Surface Deform to Cloth Object"
    bl_description = "1. select Cloth first - 2. select object to attach"
    # objects:StringProperty(name="Select Object", description="Select Object", default="")
    selected = any
    active = any
    # # selectedObject: EnumProperty(items=[], name="select object", description="Select Object to Attach selected Object")
    # @classmethod
    # def poll(cls, context):
    # 	return context.active_object is not None

    # def invoke(self, context, event):
        # self.objects = bpy.data.objects
        
        # return context.window_manager.invoke_props_dialog(self)

    def prepareModifiers(self, context):
        # if context.scene.sc_last_cloth_object:
        originObject = self.selected
        attachObject = context.active_object
        addSubsurfModifier = False

        # bpy.ops.object.editmode_toggle()
        # bpy.ops.mesh.select_all(action='DESELECT')
        # bpy.ops.mesh.select_all(action='SELECT')
        # if context.active_object.data.total_face_sel < 16:
        # 	addSubsurfModifier = True
        # bpy.ops.object.editmode_toggle()

        # if addSubsurfModifier:			
        # 	bpy.ops.object.modifier_add(type='SUBSURF')
        # 	bpy.context.object.modifiers["Subdivision"].subdivision_type = 'SIMPLE'


        bpy.ops.object.modifier_add(type='SHRINKWRAP')
        bpy.context.object.modifiers["Shrinkwrap"].target = bpy.data.objects[originObject.name]
        bpy.context.object.modifiers["Shrinkwrap"].wrap_mode = 'OUTSIDE_SURFACE'
        bpy.context.object.modifiers["Shrinkwrap"].offset = 0.01



        bpy.ops.object.modifier_add(type='SURFACE_DEFORM')

        attachObject.modifiers["SurfaceDeform"].target = bpy.data.objects[originObject.name]
        bpy.ops.object.surfacedeform_bind(modifier="SurfaceDeform")

        bpy.ops.object.modifier_add(type='SOLIDIFY')
        bpy.context.object.modifiers["Solidify"].thickness = 0.01

    def getSelectedAndActiveObject(self, context):
        selected_objects = [obj for obj in context.view_layer.objects if obj.select_get()]

        for obj in selected_objects:
            if obj is not context.view_layer.objects.active:
                self.selected = obj
        self.active = context.active_object

    def execute(self, context):
        # bpy.ops.object.parent_set(type='OBJECT', keep_transform=False)
        self.getSelectedAndActiveObject(context)
        self.prepareModifiers(context)
        context.active_object.is_Attached= True
        return{"FINISHED"}	
    
class DeattachObjectFromCloth(bpy.types.Operator):
    bl_idname = "object.remove_attached_modifiers"
    bl_label = "Remove Attached Object Setup"


    def removeModifiers(self, context):
        for mod in context.active_object.modifiers:
            bpy.ops.object.modifier_remove(modifier=mod.name, report=True)

    def execute(self, context):
        self.removeModifiers(context)
        context.active_object.is_Attached = False
        return{"FINISHED"}	
    
class RebindAttachedObject(bpy.types.Operator):
    bl_idname = "object.rebind_attached_object"
    bl_label = "Attach as Surface Deform to Cloth Object"
    bl_description = "Rebind attached object to Cloth objects"
    
    mode: StringProperty(default="BIND", name="")

    def rebindActiveObject(self, context):
        if "SurfaceDeform" in context.active_object.modifiers:
            context.active_object.modifiers["SurfaceDeform"]
            bpy.ops.object.surfacedeform_bind(modifier="SurfaceDeform")
            bpy.ops.object.surfacedeform_bind(modifier="SurfaceDeform")

    def reposition(self, context):
        context.active_object.location = context.active_object.modifiers["SurfaceDeform"].target.location

    def execute(self, context):	
        bpy.context.scene.frame_current = 1
        if self.mode == "BIND":
            self.rebindActiveObject(context)
        elif self.mode == "POSITION":
            self.reposition(context)
        
        return{"FINISHED"}

class SelectOptiClothObject(bpy.types.Operator):
    bl_idname = "object.select_opti_cloth_object"
    bl_label = "Attach as Surface Deform to Cloth Object"
    bl_description = "Rebind attached object to Cloth objects"

    opticloth = any
    mode: StringProperty(name="SELECT", default="SELECT")

    def selectOptiClothObject(self, context):
        if "SurfaceDeform" in context.active_object.modifiers:
            self.opticloth = context.active_object.modifiers["SurfaceDeform"].target
            
    def toggleHide(self, context):
        if self.opticloth.hide_viewport == True:
            self.opticloth.hide_viewport = False
        else:
            self.opticloth.hide_viewport = True

    def execute(self, context):	
        self.selectOptiClothObject(context)
        if self.mode == "SELECT":
            bpy.context.view_layer.objects.active = self.opticloth
            self.opticloth.hide_viewport = False
        elif self.mode == "HIDE":
            self.toggleHide(context)
        return{"FINISHED"}

class HighToLowSurfaceDeform(bpy.types.Operator):
    bl_idname = "object.optimize_cloth_sim"
    bl_label = "Optimize Cloth Simulation Performance"
    bl_description = "Optimize Cloth Simulation Performance"
    mode: BoolProperty(default=False, name="Sure?", description="TEst")
    
    selected = any
    active = any
    clothObject = any
    surfaceDeform = any

    # # selectedObject: EnumProperty(items=[], name="select object", description="Select Object to Attach selected Object")
    # @classmethod
    # def poll(cls, context):
    # 	return context.active_object is not None

    def invoke(self, context, event):
        self.objects = bpy.data.objects
        
        return context.window_manager.invoke_props_dialog(self)
    def prepareSettings(self, context):
        bpy.context.scene.frame_current = 1
    
    def setupSurfaceDeform(self, context):
        self.surfaceDeform = context.active_object
        bpy.context.active_object.hide_viewport = False
        bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked":False, "mode":'TRANSLATION'}, TRANSFORM_OT_translate={"value":(0, 0, 0), "orient_type":'GLOBAL', "orient_matrix":((1, 0, 0), (0, 1, 0), (0, 0, 1)), "orient_matrix_type":'GLOBAL', "constraint_axis":(False, False, False), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":0.350494, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_elements":{'FACE'}, "use_snap_project":False, "snap_target":'CLOSEST', "use_snap_self":True, "use_snap_edit":True, "use_snap_nonedit":True, "use_snap_selectable":False, "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "view2d_edge_pan":False, "release_confirm":False, "use_accurate":False, "use_automerge_and_split":False})
        self.clothObject = context.active_object
        bpy.context.active_object.hide_viewport = True

    def setupOptimizedCloth(self, context):
        bpy.ops.object.modifier_add(type='DECIMATE')
        bpy.ops.object.modifier_move_to_index(modifier="Decimate", index=0)
        bpy.context.active_object.modifiers["Decimate"].decimate_type = 'UNSUBDIV'
        bpy.context.active_object.modifiers["Decimate"].iterations = 1


    def removeModifiersFromSurfaceDeform(self, context):
        for mod in self.surfaceDeform.modifiers:
            # print(mod)
            self.surfaceDeform.modifiers.remove(mod)

    def addModifiersToSurfaceDeformObject(self, context):
        bpy.context.view_layer.objects.active = self.surfaceDeform
        # context.active_object = self.surfaceDeform
        # bpy.ops.object.modifier_add(type='SHRINKWRAP')
        # context.active_object.modifiers["Shrinkwrap"].target = bpy.data.objects[self.clothObject.name]
        # context.active_object.modifiers["Shrinkwrap"].wrap_mode = 'OUTSIDE_SURFACE'
        # context.active_object.modifiers["Shrinkwrap"].offset = 0.01
        
        bpy.ops.object.modifier_add(type='MULTIRES')
        # bpy.ops.object.multires_subdivide(modifier="Multires", mode='CATMULL_CLARK')

        bpy.ops.object.modifier_add(type='SURFACE_DEFORM')

        context.active_object.modifiers["SurfaceDeform"].target = bpy.data.objects[self.clothObject.name]
        bpy.ops.object.surfacedeform_bind(modifier="SurfaceDeform")
        bpy.ops.object.modifier_add(type='SUBSURF')

        bpy.ops.object.modifier_add(type='SOLIDIFY')
        bpy.context.object.modifiers["Solidify"].thickness = 0.01

    def getSelectedAndActiveObject(self, context):
        selected_objects = [obj for obj in context.view_layer.objects if obj.select_get()]

        for obj in selected_objects:
            if obj is not context.view_layer.objects.active:
                self.selected = obj
        self.active = context.active_object

    def execute(self, context):
        if self.mode == True:
            self.prepareSettings(context)
            # self.setupOptimizedCloth(context)
            self.setupSurfaceDeform(context)
            self.removeModifiersFromSurfaceDeform(context)
            self.addModifiersToSurfaceDeformObject(context)

        return{"FINISHED"}	
    
class DrawCutAndSewPattern(bpy.types.Operator):
    bl_idname = "scene.sc_draw_cut_and_sew_pattern"
    bl_label = "draw Cut and Sew Pattern"
    bl_description = "Simply Cut & Sew"

    mode:StringProperty(default="CREATE", options={"HIDDEN"})
    # unitard: BoolProperty(default=False, name="Unitard (One closed piece)", description="Unitard (One closed piece)")
    gpencilLength:FloatProperty(default=0.005, name="Gpencil_length")
    blendFilesFolder: StringProperty(default='Blend Files')
    geoNodeBlendFile: StringProperty(default='Simply_Cloth_GeoNodes_Master.blend')

    path: StringProperty =  os.getcwd()

    rootdir = dirname(dirname(__file__))
    addons_path = join(rootdir, "simply_cloth_studio")

    blendFiles_dir = join(addons_path, "Blend Files")
    geoNodeBlendFilePath = os.path.join(blendFiles_dir, "Simply_Cloth_GeoNodes_Master.blend")

    

    geoNodeRename = ""
    geoNodeModifierRename = ""
    objectGeoNodes = any

    preName = "SimplyCutPattern_GeoNodes_"

    def createCurveAndOpenEditMode(self, context):
        bpy.ops.view3d.view_all(center=True)
        bpy.ops.curve.primitive_bezier_circle_add(radius=1, enter_editmode=False, align='WORLD', location=(0, 0.0, 0), scale=(1, 1, 1))
        bpy.context.active_object.name = "Simply Cut"
        bpy.context.view_layer.objects.active = bpy.context.active_object
        bpy.ops.transform.rotate(value=1.5708, orient_axis='X', orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(True, False, False), mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)
        # bpy.ops.transform.translate(value=(1.06573, 0, 0), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(True, False, False), mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)
        bpy.ops.object.editmode_toggle()
        bpy.ops.curve.select_all(action='SELECT')
        bpy.ops.curve.delete(type='VERT')
        bpy.ops.object.editmode_toggle()
        # bpy.ops.object.editmode_toggle()


        bpy.ops.object.modifier_add(type='MIRROR')
        bpy.context.object.modifiers["Mirror"].use_clip = True
        print("CUT")
        # self.appendSimplyClothGeoNodesFillCurveFromBlendFile(context)
        # self.addGeometryNodesModifierToSelectedObject(context)


        bpy.ops.object.editmode_toggle()
        bpy.ops.curve.select_all(action='DESELECT')
        bpy.ops.curve.delete(type='VERT')
        bpy.ops.object.editmode_toggle()



        bpy.ops.object.editmode_toggle()

        bpy.ops.view3d.view_axis(type='FRONT')
        bpy.ops.wm.tool_set_by_id(name="builtin.draw")
        bpy.context.scene.tool_settings.curve_paint_settings.curve_type = 'POLY'


    def createGPForCutAndSewDrawing(self, context):
        print("TEST BRO")
        bpy.ops.view3d.view_all(center=True)
        bpy.ops.object.gpencil_add(align='WORLD', location=(0, -0.5, 0), scale=(1, 1, 1), type='EMPTY')
        bpy.context.active_object.name = "SC_GP_Cut_Sew_Pattern"
        bpy.ops.object.gpencil_modifier_add(type='GP_SIMPLIFY')
        bpy.context.object.grease_pencil_modifiers["Simplify"].mode = 'SAMPLE'

        bpy.ops.object.gpencil_modifier_add(type='GP_MIRROR')

        bpy.ops.gpencil.paintmode_toggle()
        bpy.ops.view3d.view_axis(type='FRONT')
        bpy.context.object.active_material.grease_pencil.color = (1, 0, 0, 1)


        bpy.context.scene.tool_settings.use_gpencil_draw_additive = True
        bpy.context.scene.tool_settings.use_gpencil_automerge_strokes = True
        bpy.data.brushes["Pencil"].size = 10


        bpy.data.objects["SC_GP_Cut_Sew_Pattern"].data.layers[0].info = "SC_Layer"
        bpy.ops.wm.tool_set_by_id(name="builtin.curve")
        context.scene.sc_cut_sew_pattern_created = True


    def finishGPCutAndSewDrawing(self, context):
        bpy.ops.object.mode_set(mode='OBJECT')
        Simply_GeoNodes_Modifier = context.active_object.modifiers[context.active_object.sc_geoNodes_simplycloth_modifier_name]
        Simply_GeoNodes = context.active_object.modifiers[context.active_object.sc_geoNodes_simplycloth_modifier_name].node_group.nodes
        Simply_GeoNodes["SC_GeoN_Boolean"].mute = False
        bpy.ops.object.modifier_remove(modifier="Mirror")

        # row.prop(Simply_GeoNodes["SC_GeoN_Boolean"], "mute", text="", invert_checkbox=True, icon="IMAGE_ALPHA")
        # bpy.ops.object.gpencil_modifier_apply(modifier="Mirror")
        # bpy.ops.object.mode_set(mode='EDIT_GPENCIL')
        # bpy.ops.gpencil.select_all(action='DESELECT')
        # bpy.ops.gpencil.select_all(action='SELECT')
        # bpy.ops.gpencil.stroke_simplify(factor=0.005)
        # bpy.ops.gpencil.frame_clean_loose(limit=10)

        bpy.ops.gpencil.stroke_merge()
        # bpy.ops.gpencil.frame_clean_duplicate()

        bpy.ops.object.mode_set(mode='OBJECT')

    def convertGPToBezierCurve(self, context):
        bpy.ops.gpencil.convert(type='CURVE', use_timing_data=False)
        for obj in bpy.data.objects:
            if obj.type == "CURVE":
                if obj.name == "SC_Layer":
                    bpy.ops.object.select_all(action='DESELECT')
                    bpy.context.view_layer.objects.active = obj
                    self.fixRotation(context)

    def fixRotation(self, context):
        bpy.ops.object.editmode_toggle()
        bpy.ops.curve.select_all(action='DESELECT')
        bpy.ops.curve.select_all(action='SELECT')

        bpy.ops.transform.rotate(value=-1.5708, orient_axis='X', orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(True, False, False), mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)
        bpy.ops.curve.spline_type_set(type='BEZIER')

        bpy.ops.object.editmode_toggle()
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS', center='MEDIAN')
        # bpy.ops.transform.rotate(value=1.5708, orient_axis='X', orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(True, False, False), mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)


        # bpy.ops.object.convert(target='MESH')
        
    def fixCurveAndFillBounds(self, context):
        # print(context.mode)
        if context.mode != "EDIT_GPENCIL":
        # 	bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.object.editmode_toggle()

        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=0.01)
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_all(action='SELECT')


        # bpy.ops.mesh.edge_face_add()
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.inset(thickness=0.05, depth=0)

        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
        bpy.ops.mesh.select_non_manifold(extend=False, use_wire=False, use_boundary=True, use_multi_face=False, use_non_contiguous=False, use_verts=False)
        bpy.ops.mesh.mark_seam(clear=False)
        bpy.ops.mesh.mark_sharp()
        
    def extrudeSewingPattern(self, context):
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"use_normal_flip":False, "use_dissolve_ortho_edges":False, "mirror":False}, TRANSFORM_OT_translate={"value":(0, 0.27, 0), "orient_type":'GLOBAL', "orient_matrix":((1, 0, 0), (0, 1, 0), (0, 0, 1)), "orient_matrix_type":'GLOBAL', "constraint_axis":(False, True, False), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_elements":{'INCREMENT'}, "use_snap_project":False, "snap_target":'CLOSEST', "use_snap_self":True, "use_snap_edit":True, "use_snap_nonedit":True, "use_snap_selectable":False, "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "use_duplicated_keyframes":False, "view2d_edge_pan":False, "release_confirm":False, "use_accurate":False, "use_automerge_and_split":False})

        # bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"use_normal_flip":False, "use_dissolve_ortho_edges":False, "mirror":False}, TRANSFORM_OT_translate={"value":(0, -1.0, 0.0), "orient_type":'GLOBAL', "orient_matrix":((1, 0, 0), (0, 1, 0), (0, 0, 1)), "orient_matrix_type":'GLOBAL', "constraint_axis":(True, False, False), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_elements":{'INCREMENT'}, "use_snap_project":False, "snap_target":'CLOSEST', "use_snap_self":True, "use_snap_edit":True, "use_snap_nonedit":True, "use_snap_selectable":False, "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "view2d_edge_pan":False, "release_confirm":False, "use_accurate":False, "use_automerge_and_split":False})
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
        bpy.ops.mesh.select_face_by_sides(number=4, type="EQUAL", extend=True)
        bpy.ops.view3d.select_circle()
        bpy.ops.object.editmode_toggle()

    def createClothFromCutAndSewPattern(self, context):
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.shade_smooth()
        # print("CREATE CLOTH BRO")
# 

        # bpy.ops.object.mode_set(mode='OBJECT')
        

        # bpy.context.object.grease_pencil_modifiers["Simplify"].length = 0.067

        # bpy.context.object.sc_triangulation_resolution = self.gpencilLength
        # bpy.ops.object.remesh_simply_cloth_triangulation()

        # """ WORK IN PROGRESS """
        # bpy.ops.object.create_cloth(mode="CREATECLOTH")
        # bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

        # bpy.ops.object.editmode_toggle()
        # bpy.ops.mesh.select_all(action='DESELECT')
        # bpy.ops.mesh.select_all(action='SELECT')
        # bpy.ops.mesh.inset(thickness=0.001, depth=0)
        # bpy.ops.object.editmode_toggle()


    def appendSimplyClothGeoNodesFillCurveFromBlendFile(self, context):       
        geoNodedirectory = self.geoNodeBlendFilePath+"/NodeTree/"
        geoNodeFilename="SimplyCloth_Geo_FillCurve"
        geoNodeFilePath = geoNodedirectory

        bpy.ops.wm.append(filepath= geoNodeFilePath, directory=geoNodedirectory, filename=geoNodeFilename,filter_obj=False)
        self.geoNodeRename = self.preName+context.active_object.name

        bpy.data.node_groups["SimplyCloth_Geo_FillCurve"].name = self.geoNodeRename

        self.objectGeoNodes = bpy.data.node_groups[self.geoNodeRename]

    def addGeometryNodesModifierToSelectedObject(self, context):
        obj = bpy.context.active_object
        bpy.ops.object.modifier_add(type='MIRROR')
        # self.geoNodeModifierRename = self.preName+context.active_object.name
        # obj.modifiers['GeometryNodes'].name = self.geoNodeModifierRename
        # obj.modifiers[self.geoNodeModifierRename].node_group = self.objectGeoNodes
        # obj.sc_geoNodes_simplycloth_modifier_name = self.geoNodeModifierRename

    def addGeoNodesFillCurve(self, context):
        bpy.ops.object.editmode_toggle()
        bpy.ops.curve.decimate(ratio=0.05)	
        bpy.ops.object.editmode_toggle()
        # bpy.ops.object.modifier_add(type='WELD')
        # bpy.context.object.modifiers["Weld"].merge_threshold = 0.005


        # self.appendSimplyClothGeoNodesFillCurveFromBlendFile(context)
        self.addGeometryNodesModifierToSelectedObject(context)


    def execute(self, context):
        if self.mode == "CREATE":
            # self.createGPForCutAndSewDrawing(context)

            self.createCurveAndOpenEditMode(context)
            # print("TEST")
        if self.mode == "FINISH":
            # self.gpencilLength = bpy.context.object.grease_pencil_modifiers["Simplify"].length
            print("FINISH")
            self.gpencilLength = 0.001
            self.finishGPCutAndSewDrawing(context)
            self.convertGPToBezierCurve(context)

            self.addGeoNodesFillCurve(context)

            # self.fixCurveAndFillBounds(context)
            self.createClothFromCutAndSewPattern(context)
            # if context.scene.sc_cutdraw_unitard == True:
            # 	# print("TRUEEEEEE")
            # 	self.extrudeSewingPattern(context)
            
        # self.createCurveAndOpenEditMode(context)f
        return {'FINISHED'}

class DragClothDuringSimulation(bpy.types.Operator):
    bl_idname = "scene.sc_drag_cloth"
    bl_label = "Drag cloth during simulation"
    bl_description = "Simply Drag Cloth"
    # mode:StringProperty(default="CREATE")
    _timer = None
    _force_field = None
    _mouse_start = (0, 0)
    _strength = -1000.0 
    _falloff = 0.3
    _forceObject = False

    def modal(self, context, event):

        print(self._strength)
        if event.type == 'LEFTMOUSE':
            if event.value == 'PRESS':
                
                self.handle_mouse_release(context, event)
                self.handle_mouse_press(context, event)
            # elif event.valu e == 'RELEASE':
            # 	self.handle_mouse_release(context, event)
            # elif event.value == 'RELEASE':
        elif event.type == 'RIGHTMOUSE':
            if event.value == 'PRESS':
                self.handle_mouse_release(context, event)
                self._strength = -1000.0
        elif event.type == 'MOUSEMOVE':
            self.handle_mouse_move(context, event)


        elif event.type in {"LEFTMOUSE"} and event.ctrl:
            if event.value:
                self._strength = self._strength* -1
        
        elif event.type in {"WHEELDOWNMOUSE"} and event.ctrl:
            self._strength = self._strength+1000
            # self._falloff = self._falloff + 0.01

            self._force_field.field.strength = self._strength
            self._force_field.field.distance_max = self._falloff
        elif event.type in {"WHEELUPMOUSE"} and event.ctrl:
            self._strength = self._strength-1000
            # self._falloff = self._falloff - 0.01
            self._force_field.field.strength = self._strength
            self._force_field.field.distance_max = self._falloff

        elif event.type in {'ESC'} or event.type in {'SPACE'}:
            # bpy.ops.screen.animation_play()
            self.handle_mouse_release(context, event)
            self.cleanup()
            # bpy.types.SpaceView3D.draw_handler_remove(self._handle_2d, 'WINDOW')
            bpy.context.scene.tool_settings.use_snap = False
            bpy.context.scene.tool_settings.snap_elements = {'FACE'}

            # bpy.ops.screen.animation_play()
            screen = bpy.ops.screen
            screen.frame_jump(1)
            screen.animation_cancel()
            return {'CANCELLED'}
        return {'PASS_THROUGH'}
    
    def handle_mouse_press(self, context, event):
        print("NEW FORCE")
        self._mouse_start = (event.mouse_x, event.mouse_y)
        bpy.ops.object.effector_add(type='FORCE', enter_editmode=False, align='WORLD', location=context.scene.cursor.location, scale=(0.1, 0.1, 0.1))
        self._force_field = context.active_object
        # bpy.context.object.hide_viewport = True
        bpy.context.space_data.show_object_viewport_empty = False

        # context.active_object.hide_viewport = False

        # print(self._force_field)
        self._force_field.location = context.scene.cursor.location
        # bpy.context.collection.objects.link(self._force_field)
        self._force_field.field.strength = self._strength
        self._force_field.field.use_absorption = True
        self._force_field.field.use_max_distance = True
        # self._force_field.field.use_gravity_falloff = True
        self._force_field.field.distance_max = self._falloff
        # bpy.context.space_data.show_object_viewport_empty = False
        bpy.context.scene.tool_settings.use_snap = True
        bpy.context.scene.tool_settings.snap_elements = {'FACE'}
        # bpy.context.object.field.shape = 'PLANE'

    def handle_mouse_release(self, context, event):
        if self._force_field:
            # bpy.context.collection.objects.unlink(self._force_field)
            bpy.data.objects.remove(self._force_field)
            self._force_field = None
            bpy.context.space_data.show_object_viewport_empty = True
            print("REMOVE FORCE")
        # self.cleanup()

    def handle_mouse_move(self, context, event):
        mouse_pos = (event.mouse_x, event.mouse_y)
        # delta = Vector((0, 0, mouse_pos[1] - self._mouse_start[1]))
        # delta = Vector((mouse_pos[0] - self._mouse_start[0], mouse_pos[1] - self._mouse_start[1]))
        # delta = Vector((mouse_pos[0] - self._mouse_start[0], mouse_pos[0] - self._mouse_start[0],mouse_pos[1] - self._mouse_start[1]))
        delta = Vector((mouse_pos[0] - self._mouse_start[0],mouse_pos[0] - self._mouse_start[0],mouse_pos[1] - self._mouse_start[1]))
        if self._force_field:
            self._force_field.location = context.scene.cursor.location + delta.to_3d()*0.001
            
            # if self._strength == 0.0:
            # 	self._strength = 0.0
            # 	self._force_field.field.strength = self._strength
            # else:
            # 	self._strength = self._strength+100.0 
            # 	self._force_field.field.strength = self._strength
            
    def cleanup(self):
        for obj in bpy.data.objects:
            if obj.type == "EMPTY":
                bpy.ops.object.delete
        # bpy.types.SpaceView3D.draw_handler_remove(self._handle_2d, 'WINDOW')
        # self._handle_2d = None
        return {'FINISHED'}
    
    # def draw_callback_px(self, context):
    # 	font_id = 0
    # 	blf.position(font_id, 15, 30, 0)
    # 	blf.size(font_id, 20, 72)
    # 	blf.draw(font_id, f"Force Field Strength: {self._strength}")

    def invoke(self, context, event):
        if bpy.context.screen.is_animation_playing:
            pass
        else:
            bpy.ops.screen.animation_play()

        if context.space_data.type == 'VIEW_3D':
            # args = (self, context)
            # self._handle_2d = bpy.types.SpaceView3D.draw_handler_add(self.draw_callback_px, args, 'WINDOW', 'POST_PIXEL')
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "Active space must be a View3d")
            return {'CANCELLED'}

class SetUpGeoNodesSimplyCloth(bpy.types.Operator):
    bl_idname = "object.sc_setup_simply_geo_nodes"
    bl_label = "Setup Simply Cloth Geo Nodes for active object"
    bl_description = "Setup Simply Cloth Geo Nodes for active object"
    activeObjectMaterialSlot = IntProperty(default= 0)
    activeObjectMaterialName = StringProperty(default="")

    blendFilesFolder: StringProperty(default='Blend Files')
    geoNodeBlendFile: StringProperty(default='Simply_Cloth_GeoNodes_Master.blend')

    path: StringProperty =  os.getcwd()

    rootdir = dirname(dirname(__file__))
    addons_path = join(rootdir, "simply_cloth_studio")

    blendFiles_dir = join(addons_path, "Blend Files")
    geoNodeBlendFilePath = join(blendFiles_dir, "Simply_Cloth_GeoNodes_Master.blend")

    geoNodeRename = ""
    geoNodeModifierRename = ""
    objectGeoNodes = any

    preName = "SimplyCloth_GeoNodes_"

    def checkForModifiers(self, context):
        if context.active_object.modifiers:
            for modifier in context.active_object.modifiers:
                if modifier.type =="NODES":
                    context.active_object.sc_UI_ModifierBeforeDetected = False
                if modifier:
                    context.active_object.sc_UI_ModifierBeforeDetected = True
                    

    def appendSimplyClothGeoNodesFromBlendFile(self, context):       
        geoNodedirectory = join(self.geoNodeBlendFilePath, "NodeTree")
        geoNodeFilename="SimplyCloth_GeoEnhance"
        geoNodeFilePath = geoNodedirectory

        bpy.ops.wm.append(filepath= geoNodeFilePath, directory=geoNodedirectory, filename=geoNodeFilename)
        self.geoNodeRename = self.preName+context.active_object.name

        bpy.data.node_groups["SimplyCloth_GeoEnhance"].name = self.geoNodeRename

        self.objectGeoNodes = bpy.data.node_groups[self.geoNodeRename]


    def addGeometryNodesModifierToSelectedObject(self, context):
        obj = bpy.context.active_object
        bpy.ops.object.modifier_add(type='NODES')
        self.geoNodeModifierRename = self.preName+context.active_object.name
        obj.modifiers['GeometryNodes'].name = self.geoNodeModifierRename
        obj.modifiers[self.geoNodeModifierRename].node_group = self.objectGeoNodes
        obj.sc_geoNodes_simplycloth_modifier_name = self.geoNodeModifierRename

    def addNeededGeometryNodeNameParametersToObject(self, context):
        obj = bpy.context.active_object
        
        bpy.ops.object.modifier_add(type='NODES')
        bpy.context.active_object.modifiers['GeometryNodes'].name = self.geoNodeModifierRename
        bpy.context.active_object.modifiers[self.geoNodeModifierRename].node_group = bpy.data.node_groups[self.geoNodeRename]

    def checkAndFixNameOfObject(self, context):
        obj = context.active_object
        if "." in obj.name:
                        obj.name = obj.name.replace(".", "_")

    def setupModifierProperties(self, context):
        blenderVersion = bpy.app.version

        if blenderVersion[0] == 3 :
            bpy.ops.object.geometry_nodes_input_attribute_toggle(prop_path="[\"Input_2_use_attribute\"]", modifier_name=self.geoNodeRename)
            bpy.ops.object.geometry_nodes_input_attribute_toggle(prop_path="[\"Input_4_use_attribute\"]", modifier_name=self.geoNodeRename)
            bpy.ops.object.geometry_nodes_input_attribute_toggle(prop_path="[\"Input_5_use_attribute\"]", modifier_name=self.geoNodeRename)
            bpy.ops.object.geometry_nodes_input_attribute_toggle(prop_path="[\"Input_6_use_attribute\"]", modifier_name=self.geoNodeRename)
            bpy.ops.object.geometry_nodes_input_attribute_toggle(prop_path="[\"Input_7_use_attribute\"]", modifier_name=self.geoNodeRename)

        elif blenderVersion[0] == 4:
            bpy.ops.object.geometry_nodes_input_attribute_toggle(input_name="Input_2", modifier_name=self.geoNodeRename)
            bpy.ops.object.geometry_nodes_input_attribute_toggle(input_name="Input_4", modifier_name=self.geoNodeRename)
            bpy.ops.object.geometry_nodes_input_attribute_toggle(input_name="Input_5", modifier_name=self.geoNodeRename)
            bpy.ops.object.geometry_nodes_input_attribute_toggle(input_name="Input_6", modifier_name=self.geoNodeRename)
            bpy.ops.object.geometry_nodes_input_attribute_toggle(input_name="Input_7", modifier_name=self.geoNodeRename)

            
                                
                                
    def setupVertexGroupsForGeoNodes(self, context):
        obj = context.active_object
        if "SimplyGeo_Sewing" not in obj.vertex_groups:
            group = bpy.context.object.vertex_groups.new()
            group.name = "SimplyGeo_Sewing"

        if "SimplyGeo_Pull" not in obj.vertex_groups:
            group = bpy.context.object.vertex_groups.new()
            group.name = "SimplyGeo_Pull"
        if "SimplyGeo_Push" not in obj.vertex_groups:
            group = bpy.context.object.vertex_groups.new()
            group.name = "SimplyGeo_Push"

        if "SimplyGeo_Detail" not in obj.vertex_groups:
            group = bpy.context.object.vertex_groups.new()
            group.name = "SimplyGeo_Detail"

        if "SimplyGeo_Edge" not in obj.vertex_groups:
            group = bpy.context.object.vertex_groups.new()
            group.name = "SimplyGeo_Edge"

    def connectVertexGroupsToGeoNodesAttributes(self, context):
        bpy.context.object.modifiers[self.geoNodeRename]["Input_2_attribute_name"] = "SimplyGeo_Sewing"
        bpy.context.object.modifiers[self.geoNodeRename]["Input_4_attribute_name"] = "SimplyGeo_Pull"
        bpy.context.object.modifiers[self.geoNodeRename]["Input_5_attribute_name"] = "SimplyGeo_Push"
        bpy.context.object.modifiers[self.geoNodeRename]["Input_6_attribute_name"] = "SimplyGeo_Detail"
        bpy.context.object.modifiers[self.geoNodeRename]["Input_7_attribute_name"] = "SimplyGeo_Edge"

    def execute(self, context):
        self.checkAndFixNameOfObject(context)
        self.checkForModifiers(context)
        if "Simply_Cloth_GeoNodes" not in bpy.data.node_groups:
            self.appendSimplyClothGeoNodesFromBlendFile(context)
        self.addGeometryNodesModifierToSelectedObject(context)
        self.setupModifierProperties(context)
        self.setupVertexGroupsForGeoNodes(context)
        self.connectVertexGroupsToGeoNodesAttributes(context)
        return {'FINISHED'}
    
class SelectVertexGroupForGeoNodesEdit(bpy.types.Operator):
    bl_idname = "object.sc_vertexgroup_geonodes_edit"
    bl_label = "Setup Simply Cloth Geo Nodes for active object"
    bl_description = "Setup Simply Cloth Geo Nodes for active object"
    vertexGroup : StringProperty(default="SEWING")
    selectedGroup = "SimplyGeo_"

    def selectVertexGroup(self, context):
        obj = context.active_object
        print("SELECT")
        if self.selectedGroup in context.active_object.vertex_groups:
            index =  bpy.context.active_object.vertex_groups[self.selectedGroup].index
            print(index)
            obj.vertex_groups.active_index = index

    def execute(self, context):
        if self.vertexGroup == "SEWING":
            self.selectedGroup = self.selectedGroup+"Sewing"
        if self.vertexGroup == "PULL":
            self.selectedGroup = self.selectedGroup+"Pull"
        if self.vertexGroup == "PUSH":
            self.selectedGroup = self.selectedGroup+"Push"
        if self.vertexGroup == "DETAIL":
            self.selectedGroup = self.selectedGroup+"Detail"
        if self.vertexGroup == "EDGE":
            self.selectedGroup = self.selectedGroup+"Edge"
        self.selectVertexGroup(context)
        if context.mode == "OBJECT":
            bpy.ops.paint.weight_paint_toggle()

        # print(selected_)
        return {'FINISHED'}

class AssignSelectedToVertexGroup(bpy.types.Operator):
    bl_idname = "object.sc_assign_to_vertex_group"
    bl_label = "Assign"
    bl_description = "Assign Selection to Vertex Group"
    vertexGroup : StringProperty(default="SEWING")
    selectedGroup = "SimplyGeo_"

    def selectVertexGroup(self, context):
        obj = context.active_object
        if self.selectedGroup in context.active_object.vertex_groups:
            index =  bpy.context.active_object.vertex_groups[self.selectedGroup].index
            print(index)
            obj.vertex_groups.active_index = index

    def addSelectionToWeldGroup(self, context):
        obj = context.active_object
        verts = obj.data.vertices
        for i, vg in enumerate(obj.vertex_groups):
            if self.selectedGroup == vg.name:
                # print(True)
                # bpy.ops.object.vertex_group_set_active(group='SimplyWeld')
                bpy.ops.object.vertex_group_assign()

    def execute(self, context):
        if self.vertexGroup == "SEWING":
            self.selectedGroup = self.selectedGroup+"Sewing"
        if self.vertexGroup == "PULL":
            self.selectedGroup = self.selectedGroup+"Pull"
        if self.vertexGroup == "PUSH":
            self.selectedGroup = self.selectedGroup+"Push"
        if self.vertexGroup == "DETAIL":
            self.selectedGroup = self.selectedGroup+"Detail"
        if self.vertexGroup == "EDGE":
            self.selectedGroup = self.selectedGroup+"Edge"
        self.selectVertexGroup(context)
        self.addSelectionToWeldGroup(context)
        if context.mode == "OBJECT":
            bpy.ops.paint.weight_paint_toggle()

        # print(selected_)
        return {'FINISHED'}

class DrawFaceSetSelection(bpy.types.Operator):
    bl_idname = "object.sc_draw_face_sets"
    bl_label = "Draw Face Sets"
    bl_description = "Draw Face Set Collections"
    vertexGroup : StringProperty(default="FACESET")

    def setupDrawFaceSet(self, context):
        obj = context.active_object
        bpy.context.object.scs_mode = 'DESIGN'


        bpy.ops.sculpt.sculptmode_toggle()
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw Face Sets")

# bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw Face Sets")
    def execute(self, context):
        self.setupDrawFaceSet(context)
        if context.active_object.modifiers:
            if "Armature" in context.active_object.modifiers:
                self.report({"WARNING"}, "Paint Cloth works best without Armature")
            
        # bpy.context.object.scs_mode = 'DESIGN'

        return {'FINISHED'}

class TearingCloth(bpy.types.Operator):
    bl_idname = "object.sc_tear_cloth_setup"
    bl_label = "Draw Face Sets"
    bl_description = "Draw Face Set Collections"
    customFrameRange = [0,36]
    endFrame = 10
    def setupTearing(self, context):
        
        currentFrame = self.customFrameRange[0]
        nextFrame = self.customFrameRange[0]+1

        # while currentFrame <= self.customFrameRange[1]:
        bpy.context.scene.frame_current = currentFrame
        # print("current: " + str(currentFrame))
        # print("next:" + str(nextFrame))
        # print("timeLine:" + str(bpy.context.scene.frame_current))
        
        #Dynamic Paint
        bpy.ops.object.modifier_add(type='DYNAMIC_PAINT')
        bpy.ops.dpaint.type_toggle(type='CANVAS')
        bpy.context.object.modifiers["Dynamic Paint"].canvas_settings.canvas_surfaces["Surface"].use_antialiasing = True
        bpy.context.object.modifiers["Dynamic Paint"].canvas_settings.canvas_surfaces["Surface"].surface_type = 'WEIGHT'
        bpy.ops.dpaint.output_toggle(output='A')

        bpy.ops.object.modifier_add(type='MASK')
        bpy.context.object.modifiers["Mask"].vertex_group = "dp_weight"
        bpy.context.object.modifiers["Mask"].invert_vertex_group = True
        bpy.context.object.modifiers["Mask"].use_smooth = True
        bpy.context.object.modifiers["Mask"].threshold = 0.8

        tearModifier = context.active_object.modifiers.new("SimplyTear", "CLOTH")

        tearModifier.point_cache.frame_start = 1
        tearModifier.point_cache.frame_end = nextFrame

        override = {'scene': bpy.context.scene,'point_cache' : bpy.context.active_object.modifiers['SimplyTear'].point_cache}
        bpy.ops.ptcache.bake(override, bake=False)

        bpy.ops.object.modifier_apply(modifier="Dynamic Paint", report=False)
        bpy.ops.object.modifier_apply(modifier="Mask")
        # bpy.ops.object.modifier_move_to_index(modifier="SimplyTear", index=0)
        bpy.ops.object.modifier_apply(modifier="SimplyTear")
        # bpy.ops.object.modifier_apply_as_shapekey(keep_modifier=False, modifier="SimplyTear")


        currentFrame = nextFrame+1
        nextFrame = currentFrame+1
        self.customFrameRange[0] = currentFrame
        if currentFrame == self.endFrame:

            tearModifier = context.active_object.modifiers.new("SimplyTear", "CLOTH")
            bpy.ops.screen.animation_play()
            # break

            # print("- - - - - - - - - - - - -")
            # print("current: " + str(currentFrame))
            # print("next:" + str(nextFrame))
            # break



# bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw Face Sets")
    def execute(self, context):
        context.scene.frame_current = 0
        self.setupTearing(context)
        return {'FINISHED'}

class ResetGeometryNodes(bpy.types.Operator):
    bl_idname = "object.sc_reset_simply_geo"
    bl_label = "Reset Simply Geometry Enhancement Nodes"
    bl_description = "Reset Simply Geometry Enhancement Nodes"
    

    def fixGeoNodesData(self, context):
        obj = context.active_object
        if obj.sc_geoNodes_simplycloth_modifier_name in obj.modifiers:
            obj.modifiers.remove(obj.modifiers[obj.sc_geoNodes_simplycloth_modifier_name])
        obj.sc_UI_Enhance = False
        obj.sc_geoNodes_simplycloth_modifier_name = ""

# bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw Face Sets")
    def execute(self, context):
        self.fixGeoNodesData(context)
        return {'FINISHED'}


class ConvertSlicedToSewing(bpy.types.Operator):
    bl_idname = "object.sc_convert_to_sew"
    bl_label = "Reset Simply Geometry Enhancement Nodes"
    bl_description = "Reset Simply Geometry Enhancement Nodes"

    threshold_distance = 0.005  # Adjust this value as needed
    selected = []
    foundNearVerts = []

    def selectSelectedVertices(self, context):
        obj = bpy.context.active_object
        self.selected.clear()

        for i, v in enumerate(obj.data.vertices):
            if v.select == True:
                self.selected.append(v)

    def getNearVertices(self, context):
        obj = bpy.context.active_object
        self.foundNearVerts.clear()
        for v in self.selected:
            
                for vert in obj.data.vertices:
                    if vert.select == False:
                # print(vert.index)
                    # print("is selected: ")
                    # print(vert.index)
                        
                        distance = 0.0
                        distance = (vert.co - v.co).length
                        if distance < self.threshold_distance:
                            vert.select = True
                            # print("is near: ")
                            # print(vert.index)	
                            self.foundNearVerts.append(v.index)   
                        # bpy.ops.object.editmode_toggle()
                
    def selectNearestVertices(self, context):
        obj = bpy.context.active_object
        # print(self.foundNearVerts)
        for vert in self.foundNearVerts:
            # print(vert)
            # bpy.ops.object.editmode_toggle()	
            bpy.data.objects[obj.name].data.vertices[vert].select = True
            # obj.data.vertices[vert.index].select = True
            # bpy.ops.object.editmode_toggle()
            # noselect.index = True
    def ripselected(self, context):
        mesh = context.active_object.data

        # Create a BMesh from the mesh data
        bm = bmesh.from_edit_mesh(mesh)

        # Select the vertices you want to rip (e.g., select by index)
        for vert_idx in [0, 1, 2]:
            bm.verts[vert_idx].select = True

        # Perform the rip operation
        # bmesh.ops.verts_rip(bm, verts=bm.verts.selected)
            bmesh.ops.split(bm, geom=[bm.verts])

            # Update the mesh with the modified BMesh
        bmesh.update_edit_mesh(mesh)
# bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw Face Sets")
    def execute(self, context):
        
        # bpy.ops.object.editmode_toggle()	
        # self.ripselected(context)
        bpy.ops.mesh.rip('INVOKE_DEFAULT')
        bpy.ops.mesh.mark_seam(clear=False)
        bpy.ops.mesh.mark_sharp()
        bpy.ops.object.editmode_toggle()	

        # bpy.ops.object.editmode_toggle()	
        # bpy.ops.mesh.rip_move(MESH_OT_rip={"mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "release_confirm":False, "use_accurate":False, "use_fill":False}, TRANSFORM_OT_translate={"value":(0.005, 0.005, 0.005), "orient_type":'GLOBAL', "orient_matrix":((1, 0, 0), (0, 1, 0), (0, 0, 1)), "orient_matrix_type":'GLOBAL', "constraint_axis":(False, False, False), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_elements":{'INCREMENT'}, "use_snap_project":False, "snap_target":'CLOSEST', "use_snap_self":False, "use_snap_edit":False, "use_snap_nonedit":False, "use_snap_selectable":False, "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "view2d_edge_pan":False, "release_confirm":False, "use_accurate":False, "use_automerge_and_split":False})
        # bpy.ops.mesh.rip_move(MESH_OT_rip={"mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "release_confirm":False, "use_accurate":False, "use_fill":False}, TRANSFORM_OT_resize={"value":(0.1, 0.1, 0.1), "mouse_dir_constraint":(0, 0, 0), "orient_type":'GLOBAL', "orient_matrix":((1, 0, 0), (0, 1, 0), (0, 0, 1)), "orient_matrix_type":'GLOBAL', "constraint_axis":(False, False, False), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_elements":{'INCREMENT'}, "use_snap_project":False, "snap_target":'CLOSEST', "use_snap_self":True, "use_snap_edit":True, "use_snap_nonedit":True, "use_snap_selectable":False, "snap_point":(0, 0, 0), "gpencil_strokes":False, "texture_space":False, "remove_on_cancel":False, "center_override":(0, 0, 0), "release_confirm":False, "use_accurate":False})

        # bpy.ops.object.editmode_toggle()	



        bpy.ops.object.editmode_toggle()	
        bpy.ops.object.editmode_toggle()	
        
        self.selectSelectedVertices(context)
        self.getNearVertices(context)
        # self.selectNearestVertices(context)
        bpy.ops.object.editmode_toggle()	
        # maxselect = len(self.foundNearVerts)+len(self.selected)
        bpy.ops.object.create_sewing(mode="CREATE_SEWING")
        return {'FINISHED'}

class BendSelected(bpy.types.Operator):
    bl_idname = "object.sc_bend_selected"
    bl_label = "Reset Simply Geometry Enhancement Nodes"
    bl_description = "Reset Simply Geometry Enhancement Nodes"
    name: StringProperty(default="", name="Slider Name")
    addEmpty: BoolProperty(default=False, name="Add Empty for Bend?")

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def addBendModifier(self, context):
        bpy.ops.object.modifier_add(type='SIMPLE_DEFORM')
        bpy.context.object.modifiers["SimpleDeform"].name = self.name

        bpy.ops.object.modifier_move_to_index(modifier=self.name, index=0)

        bpy.context.object.modifiers[self.name].show_on_cage = True
        bpy.context.object.modifiers[self.name].angle = 6.283
        bpy.context.object.modifiers[self.name].deform_method = 'BEND'
        bpy.context.object.modifiers[self.name].deform_axis = 'Z'
        bpy.context.object.modifiers[self.name].vertex_group = self.name


    def addVertexGroupForCurrentBendSelection(self,context):
        bpy.ops.mesh.faces_select_linked_flat()

        group = bpy.context.object.vertex_groups.new()
        group.name = self.name
        bpy.ops.object.vertex_group_assign()

    def applyScaleRotation(self, context):
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        bpy.ops.object.editmode_toggle()

    def addEmptyByCursorLocation(self, context):
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.empty_add(type='PLAIN_AXES', radius=0.1, align='WORLD', location=context.scene.cursor.location, scale=(1, 1, 1))


    def execute(self, context):
        self.applyScaleRotation(context)
        self.addVertexGroupForCurrentBendSelection(context)
        self.addBendModifier(context)
        if self.addEmpty == True:
            self.addEmptyByCursorLocation(context)
        return {'FINISHED'}

class OpenURLOperator(bpy.types.Operator):
    bl_idname = "scene.sc_open_url"
    bl_label = "Open URL"
    bl_description = "Support Url open"

    url: bpy.props.StringProperty()

    def execute(self, context):
        bpy.ops.wm.url_open(url=self.url)
        
        return {'FINISHED'}

class CutSewingEditMode(bpy.types.Operator):
    bl_idname = "object.sc_cutsew_edit"
    bl_label = "Open URL"
    bl_description = "Support Url open"

    mode: bpy.props.StringProperty()

    def makeBezier(self, context):
        # bpy.ops.curve.select_all(action='SELECT')
        bpy.ops.curve.spline_type_set(type='BEZIER')

    def execute(self, context):
        if self.mode == "MAKEBEZIER":
            self.makeBezier(context)
        
        return {'FINISHED'}
    
class SimplyClothTriangulation(bpy.types.Operator):
    """Triangulation by Kushiro - THANK YOU!"""
    bl_idname = "object.simplycloth_triangulation"
    bl_label = "Triangulation by Kushiro - THANK YOU!"
    bl_options = {'REGISTER', 'UNDO'}

    density : FloatProperty(default=0.5, min=0.1, name="Density", description="Triangulation Desity")
    mode: StringProperty(default="TRIANGULATE", options={"HIDDEN"})

    def get_bm(self):
        obj = bpy.context.active_object
        me = obj.data
        bm = bmesh.from_edit_mesh(me)
        return bm

    def smooth(self, bm, fs, plen):
        tol = 0.99
        areas = {}
        cens = {}
        for f1 in fs:
            a1 = f1.calc_area()
            areas[f1] = math.sqrt(a1)
            c1 = f1.calc_center_median()
            cens[f1] = c1
        vs = set()
        for f1 in fs:
            for v1 in f1.verts:
                vs.add(v1)
        for f1 in fs:
            for e1 in f1.edges:
                if e1.is_boundary:
                    a, b = e1.verts
                    if a in vs:
                        vs.remove(a)
                    if b in vs:
                        vs.remove(b)
        vs = list(vs)        
        vmap = [None] * len(vs)
        for k, v1 in enumerate(vs):
            vn = v1.normal
            ms = []
            area = []
            skip = False
            for f2 in v1.link_faces:
                pro = vn.dot(f2.normal)
                if pro < tol:
                    skip = True
                    break
                if f2 not in areas:
                    continue
                a1 = areas[f2]
                area.append(a1)
                c1 = cens[f2] * a1
                ms.append(c1)
            if len(ms) == 0 or skip:
                vmap[k] = v1.co
                continue
            v2 = sum(ms, Vector()) / sum(area)
            vmap[k] = v2
        for k, v1 in enumerate(vs):                
            v1.co = vmap[k]                    

    def random_dissolve(self, bm, fs, plen):       
        ra = 0.1
        fs2 = set(bm.faces) - set(fs)
        es = set()
        d1 = math.radians(1)
        for f1 in fs:
            for e1 in f1.edges:
                if len(e1.link_faces) != 2:
                    continue
                if e1.is_boundary:
                    continue
                if e1.calc_face_angle() > d1:
                    continue
                if e1.select:
                    continue
                if random.random() < ra:
                    es.add(e1)
        es = list(es)
        bmesh.ops.dissolve_edges(bm, edges=es, use_verts=False, use_face_split=False)
        fs = set(bm.faces) - fs2
        return list(fs)

    def triangulate_face(self, bm, sel, plen):
        random.seed(0)
        fs = sel
        count = 6
        while True:
            count += 1
            
            if count < 100:
                fs = self.random_dissolve(bm, fs, plen)

            res = bmesh.ops.triangulate(bm, faces=fs)
            fs = res['faces']                   
            self.smooth(bm, fs, plen) 
            es = set()
            for f1 in fs:
                for e1 in f1.edges:
                    es.add(e1)

            es = list(es)
            es2 = []
            for e1 in es:
                elen = e1.calc_length()
                if elen > plen:
                    es2.append(e1)
            if len(es2) > 0:
                # bisect
                bmesh.ops.bisect_edges(bm, edges=es2, cuts=1)
            else:
                self.smooth(bm, fs, plen)
                break
                
    def curveToMesh(self, context):
        # bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.editmode_toggle()
        
        # Simply_GeoNodes_Modifier = context.active_object.modifiers[context.active_object.sc_geoNodes_simplycloth_modifier_name]
        # Simply_GeoNodes = context.active_object.modifiers[context.active_object.sc_geoNodes_simplycloth_modifier_name].node_group.nodes
        # Simply_GeoNodes["Join Geometry"].mute = True
        # print(Simply_GeoNodes)
        # print(context.active_object.sc_geoNodes_simplycloth_modifier_name)
        # bpy.data.objects[context.active_object.name].select_set(True)
        # bpy.context.view_layer.objects.active = bpy.data.objects[context.active_object.name]
        # bpy.ops.object.convert(target='MESH', keep_original=True)
        bpy.ops.object.convert(target='MESH')
        bpy.ops.transform.rotate(value=-1.5708, orient_axis='X', orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(True, False, False), mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        bpy.ops.object.convert(target='CURVE')
        bpy.ops.object.editmode_toggle()
        bpy.ops.curve.select_all(action='SELECT')
        bpy.ops.curve.spline_type_set(type='BEZIER')


        


        # bpy.ops.object.scs_hex_triangulation()

        # bpy.ops.transform.rotate(value=1.5708, orient_axis='X', orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(True, False, False), mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)
        # bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

        # bpy.ops.object.convert(target='GPENCIL')
        # bpy.ops.gpencil.editmode_toggle()
        # bpy.ops.gpencil.select_all(action='SELECT')
        # bpy.ops.object.create_cloth(mode="CREATECLOTH")

    def triangulate(self, context):
        bm = self.get_bm() 
        sel = [f1 for f1 in bm.faces if f1.select]
        # selected_verts = [v for v in context.active_object.data.vertices if v.select]
        # print(sel)
        # if context.active_object.data.total_vert_sel <100:
        #     self.density = 0.05
        # elif context.active_object.data.total_vert_sel > 100:
        #     self.density = 0.1
        # print(self.density)
        plen = self.density

        self.triangulate_face(bm, sel, plen)

    def releaseObject(self, context):
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.editmode_toggle()
        
    def execute(self, context):
        if self.mode == "TRIANGULATE":
            self.triangulate(context)
            self.releaseObject(context)

        elif self.mode == "CONVERT":
            self.curveToMesh(context)
            # self.triangulate(context)
            # self.releaseObject(context)

        return {'FINISHED'}
    



class SewMethodSimilar(bpy.types.Operator):
    bl_idname = "object.scs_sew_similar"
    bl_label = "Sew automatic similar edges"
    bl_description = "Sew automatic similar edges"
    

    def selectSimilar(self, context):
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')

        bpy.ops.mesh.select_similar(type='EDGE_DIR', threshold=0.0001)

# bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw Face Sets")
    def execute(self, context):
        self.selectSimilar(context)
        # bpy.ops.object.create_sewing(mode="CREATE_SEWING")

        return {'FINISHED'}




class AppendSimplyCharacter(bpy.types.Operator):
    bl_idname = "object.scs_char_dummy"
    bl_label = "Sew automatic similar edges"
    bl_description = "Sew automatic similar edges"
    
    path: StringProperty =  os.getcwd()
    mode: StringProperty(default="ADD")

    rootdir = dirname(dirname(__file__))
    addons_path = join(rootdir, "simply_cloth_studio")
    blendFiles_dir = join(addons_path, "Blend Files")
    masterFile = join(blendFiles_dir, "Simply_Cloth_GeoNodes_Master.blend")


    def appendSimplyDummyFromBlendFile(self, context):       
        directory = self.masterFile+"/Collection/"
        ObjectName="SimplyDummy"
        filePath = directory

        bpy.ops.wm.append(filepath= filePath, directory=directory, filename=ObjectName)
        bpy.ops.transform.translate(value=(0, 0.33, 0), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(False, True, False), mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)

        # self.geoNodeRename = self.preName+context.active_object.name

        # bpy.data.node_groups["SimplyCloth_Geo_FillCurve"].name = self.geoNodeRename

        # self.objectGeoNodes = bpy.data.node_groups[self.geoNodeRename]
    def remove_shape_keys(self, context):
        if bpy.data.shape_keys:
            # Deselect all objects
            bpy.ops.object.select_all(action='DESELECT')

            # Select the object
            context.active_object.select_set(True)
            bpy.context.view_layer.objects.active = context.active_object

            # Get the shape keys
            shape_keys = context.active_object.data.shape_keys
            key_blocks = shape_keys.key_blocks
            # Remove each shape key
            while key_blocks:
                # Select the first shape key
                bpy.context.object.active_shape_key_index = 0
                
                # Remove the shape key
                bpy.ops.object.shape_key_remove()

# bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw Face Sets")
    def remove_connected_data(self, context):
        # Remove shape keys
        # self.remove_shape_keys(context)
        obj = context.active_object
        # Remove actions
        
        # if obj.animation_data != None:
        #     obj.animation_data_clear()
        
        # Remove armature modifier and related data
        if obj.type == 'MESH':
            for modifier in obj.modifiers:
                if modifier.type == 'ARMATURE':
                    obj.modifiers.remove(modifier)
        
        # Remove mesh data
        if obj.type == 'MESH':
            mesh_data = obj.data
            bpy.data.meshes.remove(mesh_data)
        
        # Remove armature data

        for arm in bpy.data.armatures:
            if "SimplyArmature" in arm.name:
                bpy.data.armatures.remove(arm)

        for c in bpy.data.collections:
            if "SimplyDummy" in c.name:
                bpy.data.collections.remove(c)

    def cleanBeforeAdd(self, context):
        self.remove_connected_data(context)



        # for obj in bpy.data.objects:
        #     if obj.name == "Simply_Dummy" or obj.name == "simply_dummy":
        #         if obj.name == "Simply_Dummy":
        #             for arm in bpy.data.armatures:
        #                 if arm.name == "SimplyArmature":
        #                     bpy.ops.object.delete()
        #         elif obj.name == "simply_dummy":
        #             bpy.context.view_layer.objects.active = bpy.data.objects[obj.name]
        #             for key in bpy.data.shape_keys:
        #                 if "SimplyKey" in key.name:
        #                     bpy.ops.object.shape_key_remove()
        #         obj.select_set(True)
        #         bpy.ops.object.delete()


        for block in bpy.data.meshes:
            if "dummy" in block.name:
                bpy.data.meshes.remove(block)
        if "SimplyDummy" in bpy.data.collections:
            bpy.data.collections.remove(bpy.data.collections['SimplyDummy'])
    def execute(self, context):
        if self.mode == "ADD":
            # self.cleanBeforeAdd(context)
            self.appendSimplyDummyFromBlendFile(context)
        elif self.mode == "DELETE":
            self.cleanBeforeAdd(context)
        # bpy.ops.object.create_sewing(mode="CREATE_SEWING")

        return {'FINISHED'}



class ChangeArmatureDummyPose(bpy.types.Operator):
    bl_idname = "object.scs_char_dummy_pose"
    bl_label = "Change Dummy Pose from A to T Pose"
    bl_description = "Change Dummy Pose"
    
    def setPose(self, context):
        animdata = bpy.data.objects["Simply_Dummy"].animation_data
        if animdata.action.name == "T-Pose" or "T-Pose." in animdata.action.name:
            animdata.action = bpy.data.actions['A-Pose']
        elif animdata.action.name == "A-Pose" or "A-Pose." in animdata.action.name:
            animdata.action = bpy.data.actions['T-Pose']

    def execute(self, context):
        self.setPose(context)
        # bpy.ops.object.create_sewing(mode="CREATE_SEWING")

        return {'FINISHED'}

class SIMPLY_preferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    def draw(self, context):
        pass
        # layout = self.layout
        # self.draw_pref_tab(layout)

    def draw_pref_tab(self, layout):
        box = layout.box()
        row = box.row(align=False)
        # row.prop(bpy.context.scene, "scs_use_custom_path", text="Use custom Path?")
        if bpy.context.scene.scs_use_custom_path:
            row.prop(bpy.context.scene, "scs_extensions_path", text="")
        row.prop(bpy.context.scene, "scs_preferences_experimental", text="Experimental Features")

class FitToCharacter(bpy.types.Operator):
    bl_idname = "object.scs_fit_to_object"
    bl_label = "Fit selected Cloth to Object"
    bl_description = "Fit selected Cloth to Object"
    def add_shrinkWrap_modifier(self, context):
        obj = context.active_object
        # nearestObject = self.find_nearest_collision_object(obj)
        # print(nearestObject)
        if context.scene.scs_fit_target_object:
            mod = obj.modifiers.new("SimplyShrink", "SHRINKWRAP")

            mod.offset = 0.01
            mod.wrap_mode = "OUTSIDE"

            mod.target = context.scene.scs_fit_target_object
            mod.offset = 0.3

            # mod.show_viewport = True
            # mod.keyframe_insert(
            # data_path='show_viewport', frame=1)

            # mod.show_viewport = False
            # mod.keyframe_insert(
            # data_path='show_viewport', frame=2)

            # mod.show_viewport = False
            # self.nearestCollisionObject = nearestObject.name
            
# bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw Face Sets")
    def execute(self, context):
        self.add_shrinkWrap_modifier(context)
        # bpy.ops.object.create_sewing(mode="CREATE_SEWING")

        return {'FINISHED'}



class ClickAndCreate(bpy.types.Operator):
    bl_idname = "object.scs_clickcreate"
    bl_label = "Click points and create Cloth"
    bl_description = "Click points and create Cloth-  Hold in Edit Mode ctrl + mouse click to create vert"

    mode: StringProperty(default="START", name="Click Cloth")

    def removeEndings(self, context):
        obj = bpy.context.active_object
        bpy.ops.object.mode_set(mode='EDIT')

        bm = bmesh.from_edit_mesh(obj.data)

        bpy.ops.mesh.select_all(action='DESELECT')
        vertices_to_select = []
        for vert in bm.verts:
            if len(vert.link_edges) == 3:
                vert.select = True
                vertices_to_select.append(vert)
        bm.select_flush_mode()

        for f in bpy.context.object.data.polygons:
            s = True
            for v in f.vertices:
                if not bpy.context.object.data.vertices[v].select:
                    s = False
            f.select = s
            if f.select:
                print("selected")

        bmesh.update_edit_mesh(obj.data)
        bpy.ops.mesh.delete(type='ONLY_FACE')
        bpy.ops.object.editmode_toggle()

    def setVertSettings(self, context):
        bpy.context.scene.tool_settings.snap_elements_base = {'VOLUME'}
        bpy.context.scene.tool_settings.use_snap_peel_object = True
        bpy.context.scene.tool_settings.use_snap = True
        bpy.context.space_data.shading.show_xray = True
        bpy.ops.view3d.view_axis(type='FRONT')

    def addModifiers(self, context):
        bpy.ops.object.modifier_add(type='MIRROR')
        bpy.context.object.modifiers["Mirror"].use_clip = True


    def makeClothLines(self, context):
        self.setVertSettings(context)
        bpy.ops.mesh.primitive_plane_add(enter_editmode=False, align='WORLD', location=(0.0,0.0,0.0), scale=(1, 1, 1))

        self.addModifiers(context)
        bpy.context.object.scs_mode_edit = 'DESIGN'
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.delete(type='VERT')

        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
        # bpy.ops.mesh.primitive_vert_add()
        bpy.ops.mesh.dupli_extrude_cursor(rotate_source=False)



    def finishCloth(self, context):

        bpy.ops.object.editmode_toggle()
        bpy.ops.object.modifier_add(type='SKIN')

        bpy.ops.object.modifier_add(type='SHRINKWRAP')
        bpy.context.object.modifiers["Shrinkwrap"].wrap_mode = 'OUTSIDE'
        bpy.context.object.modifiers["Shrinkwrap"].target = bpy.data.objects[context.scene.scs_fit_target_object.name]
        bpy.context.object.modifiers["Shrinkwrap"].offset = 0.025
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.transform.skin_resize(value=(0.5, 0.5, 0.5), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=0.1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)
        
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.convert(target='MESH')
        self.removeEndings(context)
        
        # bpy.ops.object.modifier_add(type='SUBSURF')
        # bpy.ops.object.modifier_apply(modifier="Mirror", report=True)

    def execute(self, context):
        if context.scene.scs_fit_target_object:
            if self.mode == "START":
                self.makeClothLines(context)
                context.active_object.scs_click_cloth = True
            elif self.mode == "FINISH":
                
                # self.removeEndings(context)
                self.finishCloth(context)
                bpy.context.space_data.shading.show_xray = False

                bpy.context.scene.tool_settings.use_snap = False
                bpy.ops.object.subdivision_set(level=2, relative=False)
                bpy.ops.object.modifier_apply(modifier="Subdivision", report=True)

                bpy.ops.object.modifier_add(type='MIRROR')
                bpy.context.object.modifiers["Mirror"].show_on_cage = True
                bpy.context.object.modifiers["Mirror"].use_bisect_axis[0] = True
                bpy.ops.object.modifier_add(type='SHRINKWRAP')
                context.active_object.modifiers["Shrinkwrap"].name = "1-sw"
                bpy.context.object.modifiers["1-sw"].wrap_mode = 'OUTSIDE'
                bpy.context.object.modifiers["1-sw"].target = bpy.data.objects[context.scene.scs_fit_target_object.name]
                bpy.context.object.modifiers["1-sw"].offset = 0.025
                bpy.context.object.modifiers["1-sw"].wrap_method = 'PROJECT'
                bpy.context.object.modifiers["1-sw"].use_negative_direction = True
                bpy.context.object.modifiers["1-sw"].project_limit = 0.1
                bpy.context.object.modifiers["1-sw"].use_negative_direction = True
                bpy.context.object.modifiers["1-sw"].show_on_cage = True

                bpy.ops.object.modifier_add(type='SHRINKWRAP')
                context.active_object.modifiers["Shrinkwrap"].name = "2-sw"
                bpy.context.object.modifiers["2-sw"].target = bpy.data.objects[context.scene.scs_fit_target_object.name]
                bpy.context.object.modifiers["2-sw"].wrap_mode = 'OUTSIDE_SURFACE'
                bpy.context.object.modifiers["2-sw"].offset = 0.025
                bpy.context.object.modifiers["2-sw"].show_on_cage = True


                # bpy.ops.object.modifier_apply(modifier="Mirror", report=True)

                # bpy.ops.object.create_cloth(mode="CREATECLOTH")
                bpy.ops.object.editmode_toggle()
                bpy.context.object.scs_mode_edit = 'DESIGN'
                context.active_object.scs_click_cloth = False
                # bpy.ops.object.create_cloth(mode="CREATECLOTH")
        else:
            print("Please select Target Object")
            self.report({"WARNING"}, "Please select Target Object")
        return {'FINISHED'}




class SimplyHexTriangulation(bpy.types.Operator):
    bl_idname = "object.scs_hex_triangulation"
    bl_label = "Triangulate hexagonal"
    bl_description = "Hexagonal Triangulation by Wojtek W."
    bl_options = {'REGISTER', 'UNDO'}

    obj_name: StringProperty(default="_")
    obj_todelete: StringProperty(default="_")
    def get_bbox(self, context, obj):
        if obj.type != 'MESH':
            raise ValueError("The object must be a mesh")
        bpy.context.view_layer.update()
        # bounding box coordinates
        bbox_corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
        # min and max coordinates
        min_x = min(corner.x for corner in bbox_corners)
        max_x = max(corner.x for corner in bbox_corners)
        min_y = min(corner.y for corner in bbox_corners)
        max_y = max(corner.y for corner in bbox_corners)
        min_z = min(corner.z for corner in bbox_corners)
        max_z = max(corner.z for corner in bbox_corners)
        # size of the bounding box
        size_x = max_x - min_x
        size_y = max_y - min_y
        size_z = max_z - min_z
        size = Vector((size_x, size_y, size_z,))
        # center of the bounding box
        origin_x = (min_x + max_x) / 2
        origin_y = (min_y + max_y) / 2
        origin_z = (min_z + max_z) / 2
        origin = Vector((origin_x, origin_y, origin_z,))
        return [origin, size]

    def create_quad(self, context, position=(0,0,0)):
        curve = context.active_object
        curveSize = curve.dimensions

        if curveSize[0] > curveSize[2]:
            size = curveSize[0]
        else:
            size = curveSize[2 ]

        # bpy.ops.mesh.primitive_grid_add(x_subdivisions=2, y_subdivisions=2, size=size, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
        bpy.context.scene.cursor.location = position
        bpy.ops.mesh.primitive_plane_add(enter_editmode=False, align='WORLD', location=position, scale=(size*3, 1, size*3))
        bpy.ops.transform.translate(value=(0, 1, 0), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(False, True, False), mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=True, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)


        bpy.ops.object.editmode_toggle()
        sub_range = int(round(context.scene.scs_hex_tri_resolution/25,2))
        i=0
        while i < sub_range:
            bpy.ops.mesh.subdivide()
            i = i+1
        bpy.ops.object.editmode_toggle()

        context.active_object.name = "Hexagon"
        # bpy.context.collection.objects.link(context.active_object)


        
    def create_umbrella(self, position=(0, 0, 0), radius=1):
        # create a new mesh and object
        mesh = bpy.data.meshes.new("hexagon_mesh")
        obj = bpy.data.objects.new("Hexagon", mesh)
        bpy.context.collection.objects.link(obj)
        # create bmesh object
        bm = bmesh.new()
        # calculate the vertices of the hexagon
        angle_step = pi / 3  # 60 degrees in radians
        center = bm.verts.new(position)  # center vertex
        vertices = [center]

        for i in range(6):
            angle = i * angle_step
            x = position[0] + radius * cos(angle)
            y = position[1] + radius * sin(angle)
            vertices.append(bm.verts.new((x, y, 0)))
        # create the 6 triangles
        for i in range(1, 7):
            v1 = vertices[0]
            v2 = vertices[i]
            v3 = vertices[1] if i == 6 else vertices[i + 1]
            bm.faces.new([v1, v2, v3])
        # write to the mesh
        bm.to_mesh(mesh)
        bm.free()

    def get_world_coords(self, context, obj):
        world_coords = []
        for vertex in obj.data.vertices:
            world_coords.append(obj.matrix_world @ vertex.co)
        return world_coords

    def is_planar(self, context, face):
        if len(face.verts) < 3:
            return False
        normal = face.normal
        distance = face.verts[0].co.dot(normal)
        for vert in face.verts:
            if not math.isclose(vert.co.dot(normal), distance, abs_tol=1e-6):
                return False
        return True

    # def point_in_polygon(self, context, p, v):
    #     # p -> point, v -> polygonverts
    #     num = len(v)
    #     j = num - 1
    #     c = False
    #     for i in range(num):
    #         if ((v[i].y > p.y) != (v[j].y > p.y)) and (p.x < (v[j].x - v[i].x) * (p.y - v[i].y) / (v[j].y - v[i].y) + v[i].x):
    #             c = not c
    #         j = i
    #     return c
    def get_polygon_coords_from_object(self, context, obj):
        if len(obj.data.polygons) == 0:
            raise ValueError(obj.name, "does not have any polygons.")
        polygon = obj.data.polygons[0]
        polygon_coords = [(obj.data.vertices[v].co.x, obj.data.vertices[v].co.y) for v in polygon.vertices]
        return polygon_coords

    def point_in_polygon(self, context, point, poly):
        x, y = point
        n = len(poly)
        inside = False

        p1x, p1y = poly[0]
        for i in range(n + 1):
            p2x, p2y = poly[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        return inside

    def delete_vertices_outside_polygon(self, context, obj, polygon_obj):
        # obj = context.active_object
        # delete vertices outside of polygon using numpy
        polygon_coords = self.get_polygon_coords_from_object(context, polygon_obj)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')
        # get bmesh
        bm = bmesh.from_edit_mesh(obj.data)
        # check if verts are inside polygon
        vertices_to_delete = []
        for vert in bm.verts:
            point = (vert.co.x, vert.co.y)
            if not self.point_in_polygon(context,point, polygon_coords):
                vertices_to_delete.append(vert)
        # delete vertices
        bmesh.ops.delete(bm, geom=vertices_to_delete, context='VERTS')
        # update mesh
        bmesh.update_edit_mesh(obj.data)


    def face_inside_face(self, context, face1, face2):
        for vert in face1.verts:
            if not self.point_in_polygon(context,vert.co, [v.co for v in face2.verts]):
                return False
        return True

    def extrudeSewingPattern(self, context):
        if context.mode == "OBJECT":
            bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"use_normal_flip":False, "use_dissolve_ortho_edges":False, "mirror":False}, TRANSFORM_OT_translate={"value":(0, 0.5, 0), "orient_type":'GLOBAL', "orient_matrix":((1, 0, 0), (0, 1, 0), (0, 0, 1)), "orient_matrix_type":'GLOBAL', "constraint_axis":(False, True, False), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_elements":{'INCREMENT'}, "use_snap_project":False, "snap_target":'CLOSEST', "use_snap_self":True, "use_snap_edit":True, "use_snap_nonedit":True, "use_snap_selectable":False, "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "use_duplicated_keyframes":False, "view2d_edge_pan":False, "release_confirm":False, "use_accurate":False, "use_automerge_and_split":False})
        # bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"use_normal_flip":False, "use_dissolve_ortho_edges":False, "mirror":False}, TRANSFORM_OT_translate={"value":(0.0, 0.0, 0.0 ), "orient_type":'GLOBAL', "orient_matrix":((1, 0, 0), (0, 1, 0), (0, 0, 1)), "orient_matrix_type":'GLOBAL', "constraint_axis":(False, True, False), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_elements":{'INCREMENT'}, "use_snap_project":False, "snap_target":'CLOSEST', "use_snap_self":True, "use_snap_edit":True, "use_snap_nonedit":True, "use_snap_selectable":False, "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "view2d_edge_pan":False, "release_confirm":False, "use_accurate":False, "use_automerge_and_split":False})
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
        bpy.ops.mesh.select_face_by_sides(number=4, type="EQUAL", extend=True)
        bpy.ops.view3d.select_circle()
        bpy.ops.object.editmode_toggle()

    def check_face_inside_obj(self, context, obj1, face_index1, obj2):
        bm1 = bmesh.new()
        bm1.from_mesh(obj1.data)
        bm1.faces.ensure_lookup_table()
        face1 = bm1.faces[face_index1]
        if not self.is_planar(context, face1):
            return False

        world_coords1 = self.get_world_coords(context,obj1)
        face1_world_verts = [world_coords1[vert.index] for vert in face1.verts]

        bm2 = bmesh.new()
        bm2.from_mesh(obj2.data)

        for face2 in bm2.faces:
            if not self.is_planar(context, face2):
                print("Non planar face found")
                continue

            world_coords2 = self.get_world_coords(context, obj2)
            face2_world_verts = [world_coords2[vert.index] for vert in face2.verts]

            face1_world_normal = face1.normal
            face2_world_normal = face2.normal

            if not mathutils.geometry.normal(face1_world_verts).dot(face1_world_normal) > 0.99:
                continue
            if not mathutils.geometry.normal(face2_world_verts).dot(face2_world_normal) > 0.99:
                continue
            if self.face_inside_face(context, face1, face2):
                return True
        return False


    def prepare_curve(self, context):
        if context.mode == "EDIT_CURVE":
            bpy.ops.object.editmode_toggle()
        # if "Mirror" in context.active_object.modifiers:
        #     if context.active_object.modifiers["Mirror"].show_viewport:
        #         pass
        #         # bpy.ops.object.scs_mirror_cut_pattern()


        #         # bpy.ops.object.convert(target='MESH', keep_original=False)
        #         # bpy.ops.transform.rotate(value=-1.5708, orient_axis='X', orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(True, False, False), mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)
        #         # bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        #         # bpy.ops.object.convert(target='CURVE')
        #         # bpy.ops.object.editmode_toggle()
        #         # bpy.ops.curve.select_all(action='SELECT')
        #         # bpy.ops.curve.spline_type_set(type='BEZIER')
                
        #         # bpy.ops.object.editmode_toggle()
        #     else:
        bpy.ops.object.editmode_toggle()
        bpy.ops.curve.select_all(action='SELECT')
        bpy.ops.curve.spline_type_set(type='BEZIER')
        bpy.context.object.data.splines[0].use_cyclic_u = True
        bpy.ops.object.editmode_toggle()
        bpy.ops.transform.rotate(value=-1.5708, orient_axis='X', orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(True, False, False), mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)
        # bpy.ops.object.editmode_toggle()

        
    def convert_curve(self, curve_obj, resolution):
        # bpy.ops.object.convert(target='CURVE')

        if bpy.context.mode == "EDIT_CURVE":
            bpy.ops.object.editmode_toggle()
        # print(bpy.context.mode)
        self.obj_todelete = bpy.context.active_object.name

            # ensure 2D curve
        if curve_obj.data.dimensions == "3D":
            curve_obj.data.dimensions = "2D"
        # Set the curve resolution
        curve_obj.data.resolution_u = resolution
        curve_obj.data.resolution_v = 1
        curve_obj.data.fill_mode = "NONE"
        # bpy.context.object.data.dimensions  = '2D'

        # Convert the curve to a mesh
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = curve_obj
        curve_obj.select_set(True)

        bpy.ops.object.convert(target='MESH', keep_original=True)
        
        # bpy.ops.object.convert(target='MESH', keep_original=False)
        # bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

        # bpy.ops.object.location_clear(clear_delta=False)
        

        # bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

        # fill
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.edge_face_add()
        bpy.ops.object.mode_set(mode='OBJECT')

    def interpolate_bezier_points(self, context, p0, p1, p2, p3, t):
        # cubic bezier interpolation
        return ((1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3)

    def select_sharp_mark_seam(self, context):
        context.tool_settings.mesh_select_mode = (False, True, False)

        # bpy.ops.object.mode_set(mode='OBJECT')
        for i in context.active_object.data.edges:
            i.select = False
            if i.use_edge_sharp:
                i.select = True 
        # bpy.ops.object.mode_set(mode='EDIT')
        
    def resample_bezier_curve(self, context, curve_obj, num_points):
        if curve_obj.type != 'CURVE':
            print("Object is not a curve.")
            return

        curve_data = curve_obj.data
        spline = curve_data.splines.active

        try:
            curve_closed = spline.use_cyclic_u
        except:
            curve_closed = spline

        # get all segments of the curve
        segments = []
        if spline.type == 'BEZIER':
            num_bezier_points = len(spline.bezier_points)
            for i, bp in enumerate(spline.bezier_points):
                p0 = bp.co
                p1 = bp.handle_right
                if i == num_bezier_points - 1:
                    if curve_closed:
                        next_bp = spline.bezier_points[0]
                    else:
                        break
                else:
                    next_bp = spline.bezier_points[i + 1]
                p2 = next_bp.handle_left
                p3 = next_bp.co
                segments.append((p0, p1, p2, p3))
        # subtract original points from numpoints
        num_points = num_points - len(segments)

        # total length of curve
        total_length = 0.0
        resolution = 100
        for seg in segments:
            segment_length = 0.0
            previous_point = seg[0]
            for i in range(1, resolution + 1):
                t = i / resolution
                point = self.interpolate_bezier_points(context,*seg, t)
                segment_length += (point - previous_point).length
                previous_point = point
            total_length += segment_length

        # sample interval length
        interval_length = total_length / num_points
        # sample points at regular intervals
        evaluated_points = []
        # remember previous segment from which point was added
        previous_segment = 0
        for i in range(num_points):
            target_length = i * interval_length
            accumulated_length = 0.0
            # for seg in segments:
            for s, seg in enumerate(segments):
                segment_length = 0.0
                # previous_point = Vector((0, 10, 0))
                previous_point = seg[0]
                for j in range(1, resolution + 1):
                    t = j / resolution
                    point = self.interpolate_bezier_points(context,*seg, t)
                    segment_length += (point - previous_point).length
                    if accumulated_length + segment_length >= target_length:
                        ratio = (target_length - accumulated_length) / segment_length
                        t_segment = (j - 1 + ratio) / resolution
                        point = self.interpolate_bezier_points(context,*seg, t_segment)
                        if previous_segment == s:
                            evaluated_points.append(point)
                            previous_segment = s
                        else:
                            if not evaluated_points[-1] == seg[0]:
                                evaluated_points.append(seg[0])
                            if not evaluated_points[-1] == point:
                                evaluated_points.append(point)
                            previous_segment = s
                        break
                    previous_point = point
                if accumulated_length + segment_length >= target_length:
                    break
                accumulated_length += segment_length

        # Create a new curve object
        new_curve_data = bpy.data.curves.new(name='ResampledCurve', type='CURVE')
        new_curve_data.dimensions = '2D'

        # poly for polyline
        new_spline = new_curve_data.splines.new(type='POLY')
        new_spline.points.add(len(evaluated_points) - 1)

        for i, point in enumerate(evaluated_points):
            new_spline.points[i].co = (point.x, point.y, point.z, 1)

        new_spline.use_cyclic_u = curve_closed

        new_curve_obj = bpy.data.objects.new('ResampledCurveObj', new_curve_data)
        new_curve_obj.location = curve_obj.location
        bpy.context.collection.objects.link(new_curve_obj)

        return new_curve_obj

    def execute(self, context):
        subdivision = context.scene.scs_hex_tri_resolution
        curveresolution = 12
        start_time = time.time()

        obj = context.active_object
        self.obj_name = obj.name
        curve_obj = context.active_object
        bpy.ops.object.scs_mirror_cut_pattern()
        bpy.ops.object.editmode_toggle()
        
        bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked":False, "mode":'TRANSLATION'}, TRANSFORM_OT_translate={"value":(0, 0, 0), "orient_type":'GLOBAL', "orient_matrix":((1, 0, 0), (0, 1, 0), (0, 0, 1)), "orient_matrix_type":'GLOBAL', "constraint_axis":(False, False, False), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":0.148644, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_elements":{'VOLUME'}, "use_snap_project":False, "snap_target":'CLOSEST', "use_snap_self":True, "use_snap_edit":True, "use_snap_nonedit":True, "use_snap_selectable":False, "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "use_duplicated_keyframes":False, "view2d_edge_pan":False, "release_confirm":False, "use_accurate":False, "use_automerge_and_split":False})

        original_cut_curve = context.active_object
        # original_cut_curve.name = original_cut_curve.name+"_"
        bpy.context.active_object.hide_set(True)
        # curve_obj = context.active_object
        bpy.ops.object.select_all(action='DESELECT')

        curve_obj.select_set(True)
        context.view_layer.objects.active = curve_obj
        # bpy.ops.object.editmode_toggle()

        if context.mode == "EDIT_CURVE":
            if context.mode == "OBJECT":
                bpy.ops.object.editmode_toggle()                
                
            obj.select_set(True)
            context.view_layer.objects.active = obj
            # bpy.ops.object.convert(target='MESH', keep_original=True)
            # pass    

        if not obj:
            print("Select something")
            print("________ SCRIPT FAILED")
            return
        if obj.type == "CURVE":
            self.prepare_curve(context)
            self.convert_curve(obj, curveresolution)
            # update obj property with result
            obj = context.active_object

        bbox = self.get_bbox(context, obj)
        #print("bbox pos: ", bbox[0], " obj pos: ", obj.location)
        bpy.ops.object.mode_set(mode='OBJECT')

        objsize = max(obj.dimensions[0], obj.dimensions[1], obj.dimensions[2]) / 2
        objsize *= 1.6 #compensate for roundness of hexagon
        bbox_offset = obj.location - bbox[0]

        # move 3D cursor, need this later
        context.scene.cursor.location = obj.location
        # create hexagon
        # bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS', center='MEDIAN')
        if context.active_object.scs_hex_quad:
            self.create_quad(context, obj.location)
        else:
            self.create_umbrella(position=obj.location - bbox_offset, radius=objsize)
        bpy.ops.object.select_all(action="DESELECT")
        hexobj = context.view_layer.objects["Hexagon"]
        hexobj.select_set(True)
        context.view_layer.objects.active = hexobj

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.subdivide(number_cuts=subdivision)
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
        # remove outside geometry
        self.delete_vertices_outside_polygon(context, hexobj, obj)
        bpy.ops.mesh.select_mode(type='EDGE')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_non_manifold()
        # add vertices in need of smoothing to vertex group
        bpy.ops.object.mode_set(mode='OBJECT')
        vertex_group = hexobj.vertex_groups.new(name="UmbrellaEdge")
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='VERT')
        selected_verts = [v.index for v in hexobj.data.vertices if v.select]
        bpy.ops.object.mode_set(mode='OBJECT')
        vertex_group.add(selected_verts, 1.0, 'ADD')
        # prepare new outline from resampled curve
        # resample curve
        bpy.ops.object.select_all(action="DESELECT")
        # print("selectedvert count:", len(selected_verts))
        obj.select_set(True)
        bpy.ops.object.delete()
        # reassign to obj var
        # bpy.ops.object.convert(target="CURVE")


        obj = self.resample_bezier_curve(context, curve_obj, len(selected_verts*2))
        
        obj.select_set(True)
        context.view_layer.objects.active = obj
        bpy.ops.object.convert(target="MESH")
        # obj.name = "Resampled"
        # bpy.ops.object.convert(target='CURVE')

        # # join
        hexobj.select_set(True)
        bpy.ops.object.join()
        # select outer edgeloop and curve edgeloop
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='EDGE')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_non_manifold()
        # finally fill
        bpy.ops.mesh.fill()
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        # select remaining vertices in vertex group
        vertex_group = obj.vertex_groups["UmbrellaEdge"]
        selected_verts = [v for v in obj.data.vertices if vertex_group.index in [vg.group for vg in v.groups]]
        for v in selected_verts:
            v.select = True
        bpy.ops.object.mode_set(mode='EDIT')
        # smooth vertices
        bpy.ops.mesh.vertices_smooth(factor=1.0)
        bpy.ops.object.mode_set(mode='OBJECT')
        # cleanup
        obj.vertex_groups.remove(vertex_group)
        obj.data.update()
        bpy.ops.transform.rotate(value=1.5708, orient_axis='X', orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(True, False, False), mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)
        

        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        if context.scene.sc_cutdraw_unitard == True:
            self.extrudeSewingPattern(context)
            bpy.ops.object.shade_smooth_by_angle()
            # bpy.ops.object.editmode_toggle()
            self.select_sharp_mark_seam(context)
            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.mark_seam(clear=False)
            bpy.ops.mesh.mark_sharp()
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.normals_make_consistent(inside=False)


            bpy.ops.object.editmode_toggle()
        # bpy.ops.transform.rotate(value=1.5708, orient_axis='X', orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(True, False, False), mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)
        end_time = time.time()
        elapsed_time = end_time - start_time

        # time in minutes, seconds, and milliseconds
        minutes = int(elapsed_time // 60)
        seconds = int(elapsed_time % 60)
        milliseconds = int((elapsed_time % 1) * 1000)
        minutes = f"{minutes:02d}"
        seconds = f"{seconds:02d}"
        milliseconds = f"{milliseconds:03d}"
        print(f"________ TRIANGULATION FINISHED IN: {minutes} ' {seconds} ' {milliseconds}")
        
        bpy.ops.object.select_all(action='DESELECT')

        bpy.context.view_layer.objects.active = bpy.data.objects[self.obj_todelete]
        bpy.data.objects[self.obj_todelete].select_set(True)
        bpy.ops.object.delete()

        # bpy.ops.object.select_all(action='DESELECT')
        # curve_obj.select_set(True)
        # context.view_layer.objects.active = curve_obj
        # bpy.ops.transform.rotate(value=1.5708, orient_axis='X', orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(True, False, False), mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)
        # bpy.context.active_object.hide_set(True)
        obj.select_set(True)
        context.view_layer.objects.active = obj
        bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS', center='MEDIAN')

        bpy.context.object.scs_mode_edit = 'SEW'

        # bpy.ops.object.create_cloth(mode="CREATECLOTH")
        bpy.context.object.sim_quality = 'REGULAR'


        return {'FINISHED'}


class DeleteSelectedHolesAndMakeSew(bpy.types.Operator):
    bl_idname = "object.scs_delete_selection_add_sew"
    bl_label = "Delete Selection of Unitard Object and make Sew"
    bl_description = "Delete Selected Faces for Holes and the others connection will be Sew"

    def addSelectionToWeldGroup(self, context):
        obj = context.active_object
        verts = obj.data.vertices
        for i, vg in enumerate(obj.vertex_groups):
            if "SimplyWeld" == vg.name:
                # print(True)
                bpy.ops.object.vertex_group_set_active(group='SimplyWeld')
                bpy.ops.object.vertex_group_assign()

    def deleteSelection(self, context):
        bpy.ops.mesh.delete(type='FACE')
        bpy.ops.mesh.select_face_by_sides(number=4)
        self.addSelectionToWeldGroup(context)
        bpy.ops.mesh.delete(type='ONLY_FACE')



    def execute(self, context):
        self.deleteSelection(context)
        # bpy.ops.object.create_sewing(mode="CREATE_SEWING")

        return {'FINISHED'}
    
class CheckLanguageAndSwitchNewDataCheckbox(bpy.types.Operator):
    bl_idname = "scene.scs_check_language"
    bl_label = "Fix language NEW DATA issue on using not english language"
    bl_description = "Detect Language and setup New Data for correct operators name"

    def check_language_and_disable_translate():
        prefs = bpy.context.preferences.view
        current_language = prefs.language

        print(f"Current Language: {current_language}")

        if current_language != 'en_US' and current_language != 'DEFAULT':
            bpy.context.preferences.view.use_translate_new_dataname = False
            print("New data-block name translation disabled because the language is not English.")
        else:
            print("Language is English or set to default, no changes made.")

    def execute(self, context):
        self.check_language_and_disable_translate(context)

        return {'FINISHED'}

class MirrorCutPattern(bpy.types.Operator):
    bl_idname = "object.scs_mirror_cut_pattern"
    bl_label = "Mirror Cut Pattern manually"
    bl_description = "USED CURVE TOOLS CODE by ALEXANDER MEIßNER - THANK YOU! to MERGE ENDS on CURVE"
    
    max_dist: bpy.props.FloatProperty(name='Distance', description='Threshold of the maximum distance at which two control points are merged', unit='LENGTH', min=0.0, default=0.1)

    def selectAndMoveCurve(self, context):
        #EDIT MODE
        if context.mode == "EDIT_CURVE":
            bpy.ops.object.editmode_toggle()
        original = context.active_object
        bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked":False, "mode":'TRANSLATION'}, TRANSFORM_OT_translate={"value":(0, 0, 0), "orient_type":'GLOBAL', "orient_matrix":((1, 0, 0), (0, 1, 0), (0, 0, 1)), "orient_matrix_type":'GLOBAL', "constraint_axis":(False, False, False), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_elements":{'INCREMENT'}, "use_snap_project":False, "snap_target":'CLOSEST', "use_snap_self":True, "use_snap_edit":True, "use_snap_nonedit":True, "use_snap_selectable":False, "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "use_duplicated_keyframes":False, "view2d_edge_pan":False, "release_confirm":False, "use_accurate":False, "use_automerge_and_split":False})
        bpy.ops.transform.mirror(orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(True, False, False))
        context.active_object.select_set(True)
        # bpy.context.view_layer.objects.active = context.active_object
        original.select_set(True)
        bpy.context.view_layer.objects.active = original
        bpy.ops.object.join()
        bpy.ops.object.editmode_toggle()
        bpy.ops.curve.select_all(action='SELECT')

        bpy.ops.curve.spline_type_set(type='BEZIER')
        self.mergeCurve(context)

    def getSelectedSplines(include_bezier, include_polygon, allow_partial_selection=False):
        result = []
        for spline in bpy.context.object.data.splines:
            selected = not allow_partial_selection
            if spline.type == 'BEZIER':
                if not include_bezier:
                    continue
                for index, point in enumerate(spline.bezier_points):
                    if point.select_left_handle == allow_partial_selection or \
                    point.select_control_point == allow_partial_selection or \
                    point.select_right_handle == allow_partial_selection:
                        selected = allow_partial_selection
                        break
            elif spline.type == 'POLY':
                if not include_polygon:
                    continue
                for index, point in enumerate(spline.points):
                    if point.select == allow_partial_selection:
                        selected = allow_partial_selection
                        break
            else:
                continue
            if selected:
                result.append(spline)
        return result
    def mergeEnds(self, splines, points, is_last_point):
        bpy.ops.curve.select_all(action='DESELECT')
        points[0].handle_left_type = points[0].handle_right_type = 'FREE'
        new_co = (points[0].co+points[1].co)*0.5
        handle = (points[1].handle_left if is_last_point[1] else points[1].handle_right)+new_co-points[1].co
        points[0].select_left_handle = points[0].select_right_handle = True
        if is_last_point[0]:
            points[0].handle_left += new_co-points[0].co
            points[0].handle_right = handle
        else:
            points[0].handle_right += new_co-points[0].co
            points[0].handle_left = handle
        points[0].co = new_co
        points[0].select_control_point = points[1].select_control_point = True
        bpy.ops.curve.make_segment()
        spline = splines[0] if splines[0] in bpy.context.object.data.splines.values() else splines[1]
        point = next(point for point in spline.bezier_points if point.select_left_handle)
        point.select_left_handle = point.select_right_handle = point.select_control_point = False
        bpy.ops.curve.delete()
        return spline

    def mergeCurve(self, context):

        splines = [spline for spline in self.getSelectedSplines(True, False) if spline.use_cyclic_u == False]

        while len(splines) > 0:
            spline = splines.pop()
            closest_pair = ([spline, spline], [spline.bezier_points[0], spline.bezier_points[-1]], [False, True])
            min_dist = (spline.bezier_points[0].co-spline.bezier_points[-1].co).length
            for other_spline in splines:
                for j in range(-1, 1):
                    for i in range(-1, 1):
                        dist = (spline.bezier_points[i].co-other_spline.bezier_points[j].co).length
                        if min_dist > dist:
                            min_dist = dist
                            closest_pair = ([spline, other_spline], [spline.bezier_points[i], other_spline.bezier_points[j]], [i == -1, j == -1])
            if min_dist > self.max_dist:
                continue
            if closest_pair[0][0] != closest_pair[0][1]:
                splines.remove(closest_pair[0][1])
            spline = self.mergeEnds(closest_pair[0], closest_pair[1], closest_pair[2])
            if spline.use_cyclic_u == False:
                splines.append(spline)


    def execute(self, context):
        if "Mirror" in context.active_object.modifiers:
            if bpy.context.object.modifiers["Mirror"].show_viewport == True:
                bpy.ops.object.modifier_remove(modifier="Mirror", report=True)
                self.selectAndMoveCurve(context)

        return {'FINISHED'}


