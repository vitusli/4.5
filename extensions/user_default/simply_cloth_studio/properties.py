'''
Copyright (C) 2024 Vjaceslav Tissen
vjaceslavt@gmail.com

Created by Vjaceslav Tissen
Support by Daniel Meier - Kagi Vision 3D

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import bpy

from . import customOperator
from . import ui_panel

from bpy.props import StringProperty, IntProperty, FloatProperty, EnumProperty, BoolProperty, PointerProperty


def calcMergedPinGroup(self, context):
    if context.active_object.updatePinLayerOnFly:
        bpy.ops.object.create_pin_layers(mode="MERGEWEIGHTS")


def selectActiveGroup(self, context):
    for i, vs in enumerate(context.active_object.vertex_slider):
        vs.active = False
    bpy.ops.object.create_pin_layers(mode="SELECT")
# context.active_object.vertex_slider[index].active=True
class SelectVertexGroup(bpy.types.Operator):
    bl_idname = "object.select_pin_layer"
    bl_label = "Select target Pin Layer"
    bl_description = "Weightpaint pingroup"
    mode: StringProperty(default="SELECT")
    index: IntProperty(default=0)
    name: StringProperty(default="PinGroup")

    def selectTargetVertexGroup(self, context):
        vertexSlider = context.active_object.vertex_slider
        vertexGroups = context.active_object.vertex_groups
        vertexSliderName = vertexSlider[self.index].name

        for j, vg in enumerate(vertexGroups):
            if vg.name == vertexSliderName:
                vertexGroups.active_index = j
                context.active_object.vertex_slider[j].active = True
                break
            context.active_object.vertex_slider[j].active = False

    def execute(self, context):
        self.selectTargetVertexGroup(context)
        return {'FINISHED'}


class VertexGroupMix(bpy.types.PropertyGroup):
    def get_name(self):
        if self:
            try:
                return self["name"]
            except:
                pass

    def set_name(self, value):
        prev_name = self.name
        self["name"] = value
        obj = self.id_data
        for i, v_group in enumerate(obj.vertex_groups):
            if v_group.name == prev_name:
                # print(v_group.name)
                obj.vertex_groups[v_group.name].name = value

    name: StringProperty(set=set_name, get=get_name)
    hide: BoolProperty(default=False, update=calcMergedPinGroup)
    slider_value: FloatProperty(default=1.0, min=0.0, max=1.0, update=calcMergedPinGroup, options={'ANIMATABLE'})
    active: BoolProperty(default=False)


class SLIDER_UL_List(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        ob = data
        slot = item
        box = layout.box()
        row = box.row(align=True)
        # if item.active:
        #     activeIcon = "TRIA_UP"
        # else:
        #     activeIcon = "TRIA_DOWN"

        # if context.mode == "EDIT_MESH" or context.mode == "PAINT_WEIGHT":
        op = row.operator("object.create_pin_layers", text="", icon="VIEWZOOM")
        op.mode = "SELECT"
        op.index = index

        if context.mode == "OBJECT":
            row.label(text=item.name)
        elif context.mode == "EDIT_MESH" or context.mode == "PAINT_WEIGHT":
            row.prop(item, "name", text="")
        if context.mode == "EDIT_MESH" or context.mode == "OBJECT":
            row.prop(item, "slider_value", text="", slider=True)
        row.separator(factor=1.0)
        
        if context.mode == "OBJECT" or context.mode == "EDIT_MESH":
            op = row.operator("object.delete_slider", text="", icon="TRASH")
            op.index = index
            # row = box.row(align=True)

            op = row.operator("object.create_pin_layers", text="", icon="BRUSH_DATA")
            op.mode = "WEIGHTPAINT"
            op.index = index

            if not item.hide:
                icon = "CHECKBOX_HLT"
            else:
                icon = "CHECKBOX_DEHLT"
            row.prop(item, "hide", text="", icon=icon)

        if context.mode == "EDIT_MESH":
            # row = box.row(align=True)
            if item.active:
                row = box.row(align=True)
                row.active_default = True
                # row.separator(factor=5.0)
                row.operator("object.add_selection_to_layer", text="Assign", icon="PLUS")
                op = row.operator("object.create_pin_layers", text="Clear", icon="LOOP_BACK")
                op.mode = "CLEAR"
                op.index = index

                row.separator(factor=1.0)
                op = row.operator("object.add_hook", text="Add Hook", icon="HOOK")
                op.name = item.name
                op.index = index
                op = row.operator("object.delete_hook", text="", icon="PANEL_CLOSE")
                op.name = item.name
            # op.index = index

class SLIDER_UL_List_Bend(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):

        ob = data
        slot = item

        box = layout.box()
        if context.mode == "EDIT_MESH":
            if item.active:
                row = box.row(align=True)
                row.separator(factor=5.0)
                row.operator("object.sc_bend_selected", text="Assign", icon="PLUS")
                op = row.operator("object.create_pin_layers", text="Clear", icon="LOOP_BACK")
                op.mode = "CLEAR"
                op.index = index

                # row.separator(factor=1.0)
                # op = row.operator("object.add_hook", text="Add Hook", icon="HOOK")
                # op.name = item.name
                # op.index = index
                # op = row.operator("object.delete_hook", text="", icon="PANEL_CLOSE")
                # op.name = item.name

        # row = box.row(align=True)
        # if item.active:
        #     activeIcon = "TRIA_UP"
        # else:
        #     activeIcon = "TRIA_DOWN"

        # if context.mode == "EDIT_MESH" or context.mode == "PAINT_WEIGHT":
        #     op = row.operator("object.sc_bend_selected", text="", icon=activeIcon)
        #     op.mode = "SELECT"
        #     op.index = index

        # if context.mode == "OBJECT":
        #     row.label(text=item.name)
        # elif context.mode == "EDIT_MESH" or context.mode == "PAINT_WEIGHT":
        #     row.prop(item, "name", text="")
        # if context.mode == "EDIT_MESH" or context.mode == "OBJECT":
        #     row.prop(item, "slider_value", text="", slider=True)
        # row.separator(factor=1.0)
        # if context.mode == "OBJECT" or context.mode == "EDIT_MESH":
        #     op = row.operator("object.delete_slider", text="", icon="TRASH")
        #     op.index = index

        #     op = row.operator("object.create_pin_layers", text="", icon="BRUSH_DATA")
        #     op.mode = "WEIGHTPAINT"
        #     op.index = index

        #     if not item.hide:
        #         icon = "CHECKBOX_HLT"
        #     else:
        #         icon = "CHECKBOX_DEHLT"
        #     row.prop(item, "hide", text="", icon=icon)

            # op.index = index


def register():
    bpy.utils.register_class(SelectVertexGroup)
    bpy.utils.register_class(VertexGroupMix)
    bpy.utils.register_class(customOperator.SimplyCollisionManager)
    bpy.utils.register_class(customOperator.RemoveModifier)
    bpy.utils.register_class(customOperator.SubdivideCloth)
    bpy.utils.register_class(customOperator.CreateCloth)
    bpy.utils.register_class(customOperator.AnimationManager)
    bpy.utils.register_class(customOperator.CreateWeightPins)
    bpy.utils.register_class(customOperator.CreatePins)
    bpy.utils.register_class(customOperator.createSewing)
    bpy.utils.register_class(customOperator.FinishCloth)
    bpy.utils.register_class(customOperator.PokeFace)
    bpy.utils.register_class(customOperator.AddPinGroup)
    bpy.utils.register_class(customOperator.AddSelectionToLayer)
    bpy.utils.register_class(customOperator.DeleteSlider)
    bpy.utils.register_class(ui_panel.PREFERENCES_CLOTHSTUDIOPANEL)
    bpy.utils.register_class(ui_panel.ClothStudioPanel)
    bpy.utils.register_class(ui_panel.UV_ClothStudioPanel)
    bpy.utils.register_class(customOperator.ResetClothParameter)
    bpy.utils.register_class(customOperator.DensityWeightPaint)
    bpy.utils.register_class(customOperator.AddHook)
    bpy.utils.register_class(customOperator.DeleteHook)
    bpy.utils.register_class(customOperator.FlipNormals)
    bpy.utils.register_class(customOperator.StrengthenSelection)
    bpy.utils.register_class(customOperator.ShrinkSelection)
    bpy.utils.register_class(customOperator.PressureSelection)
    bpy.utils.register_class(customOperator.LivePinningPaint)
    bpy.utils.register_class(customOperator.ClearSimplyPin)
    bpy.utils.register_class(customOperator.LoadTemplatesFromBlend)
    bpy.utils.register_class(customOperator.SelectClothSculptBrush)
    # bpy.utils.register_class(customOperator.RemeshCloth)
    bpy.utils.register_class(customOperator.SelectForceFalloff)
    bpy.utils.register_class(customOperator.SculptMaskOperator)
    bpy.utils.register_class(customOperator.SculptSubdivision)
    bpy.utils.register_class(customOperator.RemoveSimplyClothMesh)
    bpy.utils.register_class(customOperator.SculptMeshShading)
    bpy.utils.register_class(customOperator.AddWindToScene)
    bpy.utils.register_class(customOperator.RemoveWind)
    bpy.utils.register_class(customOperator.SewingCleaningOperators)
    # bpy.utils.register_class(customOperator.OpenURL)
    bpy.utils.register_class(customOperator.CleanModifiers)
    bpy.utils.register_class(customOperator.ClothDyntopoTriangulation)
    bpy.utils.register_class(customOperator.RefreshClothParameters)
    bpy.utils.register_class(customOperator.AutoSewing)
    bpy.utils.register_class(customOperator.AutoExtrudeEdges)
    # bpy.utils.register_class(customOperator.RemeshSimplyClothTriangulation)
    bpy.utils.register_class(customOperator.DrawCutAndSewPattern)
    bpy.utils.register_class(customOperator.SimulationToKeyFrame)
    bpy.utils.register_class(customOperator.AttachSelectedToCloth)
    bpy.utils.register_class(customOperator.DeattachObjectFromCloth)
    bpy.utils.register_class(customOperator.DragClothDuringSimulation)
    bpy.utils.register_class(customOperator.RebindAttachedObject)
    bpy.utils.register_class(customOperator.HighToLowSurfaceDeform)
    bpy.utils.register_class(customOperator.SelectOptiClothObject)
    bpy.utils.register_class(customOperator.SetUpGeoNodesSimplyCloth)
    bpy.utils.register_class(customOperator.SelectVertexGroupForGeoNodesEdit)
    bpy.utils.register_class(customOperator.AssignSelectedToVertexGroup)
    bpy.utils.register_class(customOperator.DrawFaceSetSelection)
    bpy.utils.register_class(customOperator.TearingCloth)
    bpy.utils.register_class(customOperator.ResetGeometryNodes)
    bpy.utils.register_class(customOperator.ConvertSlicedToSewing)
    bpy.utils.register_class(customOperator.BendSelected)
    bpy.utils.register_class(customOperator.CutSewingEditMode)
    bpy.utils.register_class(customOperator.SimplyClothTriangulation)
    bpy.utils.register_class(customOperator.SewMethodSimilar)
    bpy.utils.register_class(customOperator.OpenURLOperator)
    bpy.utils.register_class(customOperator.SIMPLY_preferences)
    bpy.utils.register_class(customOperator.FitToCharacter)
    bpy.utils.register_class(customOperator.ClickAndCreate)
    bpy.utils.register_class(customOperator.SimplyHexTriangulation)
    bpy.utils.register_class(customOperator.ChangeArmatureDummyPose)
    bpy.utils.register_class(customOperator.AppendSimplyCharacter)
    bpy.utils.register_class(customOperator.DeleteSelectedHolesAndMakeSew)
    bpy.utils.register_class(customOperator.MirrorCutPattern)
    bpy.utils.register_class(customOperator.CheckLanguageAndSwitchNewDataCheckbox)

    bpy.utils.register_class(SLIDER_UL_List)
    # bpy.utils.register_class(SLIDER_UL_List_Bend)
    # bpy.utils.register_class(customOperator.AddAssetLibraryToPreferences)

    bpy.types.Object.vertex_slider = bpy.props.CollectionProperty(type=VertexGroupMix)
    bpy.types.Object.vertex_slider_index = bpy.props.IntProperty(default=-1, max=-1)

    bpy.types.Object.vertex_slider = bpy.props.CollectionProperty(type=VertexGroupMix)

    bpy.types.Object.show_wireframes = BoolProperty(
        name="Wireframe",
        description="Wireframes on/off",
        default=False,
        update=ui_panel.update_wireframes_mode)

    bpy.types.Object.self_collision = BoolProperty(
        name="Self Collision",
        description="Self Collision on/off",
        default=False,
        update=ui_panel.update_self_collision)
    bpy.types.Object.cloth_settings = BoolProperty(
        name="Cloth Parameter",
        description="Base Cloth Parameter",
        default=False)

    bpy.types.Object.advanced_settings = BoolProperty(
        name="Advanced",
        description="Advanced on/off",
        default=False)
    bpy.types.Object.internal_spring = BoolProperty(
        name="Spring",
        description="Internal Spring on/off",
        default=False,
        update=ui_panel.update_internal_spring)

    bpy.types.Object.pressure = BoolProperty(
        name="Pressure",
        description="Pressure on/off",
        default=False,
        update=ui_panel.update_pressure)

    bpy.types.Object.cloth_sewing = BoolProperty(
        name="Sewing",
        description="Cloth Sewing on/off",
        default=False,
        update=ui_panel.update_cloth_sewing)

    bpy.types.Object.density_paint = BoolProperty(
        name="Density Paint",
        description="Density Paint on/off",
        default=True,
        update=ui_panel.update_density_paint)

    bpy.types.Object.cloth_status = BoolProperty(
        name="Enable/ Disable Cloth",
        description="Enable/ Disable Cloth Simulation",
        default=True,
        update=ui_panel.update_cloth_status)

    bpy.types.Object.face_orientation = BoolProperty(
        name="Face Orientation View",
        description="Enable/ Disable Face Orientation View",
        default=False,
        update=ui_panel.update_face_orientation_view)

    bpy.types.Object.weight_pin_view = BoolProperty(
        name="Weight Paint View",
        description="Enable/ Disable Pin Weight View",
        default=False,
        update=ui_panel.update_weight_pin_view)

    bpy.types.Object.updatePinLayerOnFly = BoolProperty(
        name="Update Pin Layer Slider directly",
        description="Enable/ Disable Update Pin Slider directly",
        default=True)

    bpy.types.Object.updateSewingWeldModifier = BoolProperty(
        name="On/ Off Sewing Merge Distance Weld",
        description="Enable/ Disable Sewing Merge Distance Weld",
        default=False,
        update=ui_panel.update_sewing_weld)

    bpy.types.Object.clothObjectSculpt = BoolProperty(
        name="info simply cloth for sculpt",
        description="Enable/ Disable Sewing Merge Distance Weld",
        default=False)

    bpy.types.Object.brushForceFalloff = BoolProperty(
        name="Switch Force Falloff",
        description="Switch Force Falloff between RADIAL and PLANE",
        default=True,
        update=ui_panel.update_brushForceFalloff)

    bpy.types.Object.thicknessBeforeAfterCloth = BoolProperty(
        name="Thickness Before/After Cloth",
        description="Decide where Solidify should be - before or after cloth computing",
        default=False,
        update=ui_panel.update_thicknessOverClothModifier)

    bpy.types.Object.subdivideOnSeparation = BoolProperty(
        name="Should subdivide on selection to cloth",
        description="Subdivide on selection to cloth on/ off",
        default=True)

    bpy.types.Object.triangulateOnSeparation = BoolProperty(
        name="Should triangulate on selection to cloth",
        description="Triangulate on selection to cloth on/ off",
        default=False)
    
    bpy.types.Object.is_SimplyCloth = BoolProperty(
        name="Is already Simply Cloth",
        description="Is already Simply Cloth",
        default=False)
    
    bpy.types.Object.is_Attached = BoolProperty(
        name="Is already Attached",
        description="Is already Attached",
        default=False)

    bpy.types.Object.fold_detail = EnumProperty(default="ACCURATE", items=(
    ("ROUGH", "Rough", "rough folds", "IPO_EASE_IN", 1), ("REGULAR", "Regular", "regular folds", "IPO_BACK", 2),
    ("ACCURATE", "Accurate", "accurate folds", "IPO_ELASTIC", 3)), update=ui_panel.change_fold_accuracy)





    bpy.types.Object.wrinkle_slider = FloatProperty(default=66.0, name="wrinkle Slider",
                                                    description="0 less wrinkles - 100 lot of wrinkles", min=0.1,
                                                    max=100.0, update=ui_panel.slide_wrinkles)
    bpy.types.Object.fold_slider = FloatProperty(default=0.0, name="fold Slider", description="General folding",
                                                 min=0.1, max=100.0, update=ui_panel.slide_folds)
    bpy.types.Object.friction_slider = FloatProperty(default=5.0, name="friction",
                                                     description="0 no friction - 100 strong friction", min=0.0,
                                                     max=100.0, update=ui_panel.slide_friction)

    bpy.types.Object.objectCollisionDistance_slider = FloatProperty(default=0.001, min=0.001, max=0.15, unit="LENGTH",
                                                                    precision=1, name="object collision distance",
                                                                    description="object collision distance",
                                                                    update=ui_panel.slide_objectCollisionDistance)
    bpy.types.Object.selfCollisionDistance_slider = FloatProperty(default=0.0001, min=0.0001, max=0.1, unit="LENGTH",
                                                                  precision=4, name="self collision distance",
                                                                  description="self collision distance (Be carefull!)",
                                                                  update=ui_panel.slide_selfCollisionDistance)

    bpy.types.Object.stiffness_slider = FloatProperty(default=66, name="stiffness",
                                                      description="0 no stiff - 100 very stiff", min=1, max=100.0,
                                                      update=ui_panel.slide_stiffness)
    bpy.types.Object.shrink_slider = FloatProperty(default=0.0, name="shrink",
                                                   description="lets the cloth expand (negativ value) or shrink (positive value) in itself",
                                                   min=-1, max=.5, update=ui_panel.slide_shrink)
    bpy.types.Object.fillHoles_slider = IntProperty(default=1, min=1, max=750,
                                                    description="fills holes in the mesh that can appear after the sewing process",
                                                    update=ui_panel.slide_fillHoles)
    # bpy.types.Object.mergeByDistance_slider = FloatProperty(default=0.0, min=0.0, max=5.0, description="Merge vertices by Distance value", update=ui_panel.slide_mergeByDistance)

    bpy.types.Object.quality_steps_slider = IntProperty(default=8, min=3, max=60,
                                                        description="This value defines the quality levels.  Small numbers - less quality = better performance.Higher numbers - better quality = poor performance",
                                                        update=ui_panel.slide_quality_steps)
    bpy.types.Object.pressure_intensity_slider = FloatProperty(default=2, min=-20, max=20,
                                                               description="The strength of the pressure is set here",
                                                               update=ui_panel.slide_pressure_intensity)
    bpy.types.Object.pressure_factor_slider = FloatProperty(default=1, min=1, max=10,
                                                            description="The factor of pressure intensity is set here",
                                                            update=ui_panel.slide_pressure_factor)
    bpy.types.Object.spring_intensity_slider = FloatProperty(default=2, min=-20, max=20,
                                                             description="The strength of the spring is set here",
                                                             update=ui_panel.slide_spring_intensity)
    bpy.types.Object.weight_slider = FloatProperty(default=0.3, min=0.01, max=10,
                                                   description="The weight of the Cloth Object is set here",
                                                   update=ui_panel.slide_weight)
    bpy.types.Object.weight_value = FloatProperty(default=1.0, min=0.0, max=1, description="Set the Weight Value",
                                                  update=ui_panel.changeWeightValue)
    bpy.types.Object.weld_slider = FloatProperty(default=0.04, min=0.0, max=1,
                                                 description="Adjust Sewing Weld Distance",
                                                 update=ui_panel.updateWeldDistanceValue)
    bpy.types.Object.strenghten_slider = FloatProperty(default=20, min=0.0, max=100,
                                                       description="Adjust Strengthen Intensity",
                                                       update=ui_panel.updateStrenghtenIntensity)
    bpy.types.Object.hardness_mask_slider = FloatProperty(default=0.5, min=0.0, max=1.0,
                                                       description="Mask Hardness",
                                                       update=ui_panel.updateMaskHardness)
    bpy.types.Object.collision_quality_slider = IntProperty(default=3, min=1, max=20,
                                                            description="Quality Steps of Collision",
                                                            update=ui_panel.slide_collision_quality)
    bpy.types.Object.preset_name = StringProperty(default="Standard")
    bpy.types.Object.brush_name = StringProperty(default="Drag")
    bpy.types.Scene.template_name = StringProperty(default="Standard")

    bpy.types.Object.baseSub_level = IntProperty(default=0, min=0, max=4, description="Subdivision Modifier Levels",
                                                 update=ui_panel.update_baseSub_level)
    bpy.types.Object.start_frame = IntProperty(default=0, description="Cloth Simulation Start Frame",
                                               update=ui_panel.update_frame_range)
    bpy.types.Object.end_frame = IntProperty(default=250, description="Cloth Simulation End Frame",
                                             update=ui_panel.update_frame_range)
    bpy.types.Object.remesher_face_count = IntProperty(default=6000, description="Desired count of Faces")

    bpy.types.Scene.sc_wind_slider = FloatProperty(default=10.0, name="Wind",
                                                   description="Wind Slider",
                                                   min=0.0, max=100.0, update=ui_panel.slide_wind_intensity)
    bpy.types.Scene.sc_wind_factor = FloatProperty(default=1.0, name="Wind Factor",
                                                   description="Wind Factor Slider",
                                                   min=0.0, max=1.0, update=ui_panel.slide_wind_factor)
    bpy.types.Scene.sc_triangulation_level = IntProperty(default=2, min=1, max = 3,description="Triangulation Level - 1-low res - 3- high res")
    
    bpy.types.Object.sc_triangulation_iteration = IntProperty(default=33, min=1, max = 300,description="Triangulation Iteration on Remesh")

    bpy.types.Object.sc_triangulation_resolution = FloatProperty(default=0.06, name="Triangulation Cloth Resolution",
                                                description="Triangulation Cloth Resolution",
                                                min=0.01, max=0.1)
    
    bpy.types.Object.sc_triangulation_quads = BoolProperty(
        name="Quads",
        description="Quads on/ off",
        default=False)  

    bpy.types.Object.sc_triangulation_reshape = BoolProperty(
        name="Reshape",
        description="Reshape on/ off",
        default=True)

    bpy.types.Scene.sc_cut_sew_pattern_created = BoolProperty(
        name="Cut & Sew Pattern available",
        description="Cut & Sew Pattern available",
        default=False)

    # UI ELEMENTS
    bpy.types.Scene.sc_UI_Cloth = BoolProperty(name="Cloth", description="Start", default=False)
    bpy.types.Object.sc_UI_Collision = BoolProperty(name="Collision", description="Start", default=False)
    bpy.types.Object.sc_UI_Sewing = BoolProperty(name="Sewing", description="Sewing", default=False)
    bpy.types.Object.sc_UI_Edit_Sewing = BoolProperty(name="Sewing", description="Edit Sewing", default=True)
    bpy.types.Object.sc_add_sewing_to_shrink = BoolProperty(name="Add Sewing To Shrink", description="Add Sewing to Shrink", default=False)

    bpy.types.Object.sc_UI_ClothParameters = BoolProperty(name="Cloth Parameters", description="Cloth Parameters", default=True)
    bpy.types.Object.sc_UI_Overlay = BoolProperty(name="Overlay", description="Overlay", default=False)
    bpy.types.Object.sc_UI_Settings = BoolProperty(name="Simulation Settings", description="Simulation Settings", default=False)

    bpy.types.Scene.sc_UI_ClothModifiers = BoolProperty(name="Cloth Modifiers", description="Cloth Parameters", default=False)
    bpy.types.Scene.sc_UI_ClothTriangulate = BoolProperty(name="Cloth Triangulation", description="Cloth Triangulation", default=False)
    bpy.types.Scene.sc_UI_ClothDrawCutAndSew = BoolProperty(name="Cloth Draw Cut & Sew", description="Draw Cut & Sewing Pattern", default=False)

    bpy.types.Scene.sc_UI_PinGroup = BoolProperty(name="Pin Groups", description="Cloth Pin Group", default=False)
    bpy.types.Object.sc_UI_Edit_PinGroup = BoolProperty(name="Pin Group", description="Edit Pin Group", default=False)

    bpy.types.Object.sc_UI_FinishSettings = BoolProperty(name="Cloth Finish", description="Cloth Finish", default=False)

    bpy.types.Scene.sc_cutdraw_unitard = BoolProperty(name="Unitard", description="Unitard (One closed piece)", default=False)
    bpy.types.Object.sc_cutdraw_trian_quad = BoolProperty(name="Tris to Quars", description="Quad Triangulation", default=False)
    
    bpy.types.Object.sc_UI_Edit_Extras = BoolProperty(name="Extras", description="Extras", default=False)

    bpy.types.Object.sc_UI_Drag_Cloth = BoolProperty(name="Drag Cloth", description="Drag Cloth", default=False)

    bpy.types.Scene.scs_open_urls = BoolProperty(name="Support My Friends", description="Support Bar", default=False)

    bpy.types.Scene.sc_sculpt_cloth_or_geometry = BoolProperty(name="Sculpt Mode: Geometry / Cloth", description="Sculpt Mode: Geometry / Cloth", default=True)

    bpy.types.Scene.sc_last_cloth_object = []
    # bpy.types.Scene.scs_collision_object = StringProperty(default="", name="")
    # bpy.types.Object.scs_mode = ['Simulate', 'Design', 'Adjust', 'Finish']
    ui_panel.registerIcon()
    global custom_icons
    # createClothIcon = custom_icons["simply_cloth_helper_icon"].icon_id
    bpy.types.Object.scs_mode = EnumProperty(default="SIM", description="CTRL+Scroll Mouse to change Mode ", items=(
    ("SIM", "Simulate", "Simulation Mode", "PLAY", 1), ("ADJUST", "Adjust & Pin", "Adjustments", "EDITMODE_HLT", 2),
    ("DESIGN", "Design", "Design Mode", "MOD_CLOTH", 3),  ("ENHANCE", "Enhance", "Enhance", "GEOMETRY_NODES", 4),
  ("FINISH", "Finish", "Finish Cloth", "CHECKMARK", 5)))

    bpy.types.Object.scs_mode_edit = EnumProperty(default="EDIT", items=(
    ("EDIT", "Editing", "Editing", "EDITMODE_HLT", 1), ("SEW", "Sewing", "Sewing", "DECORATE_LIBRARY_OVERRIDE", 2),("DESIGN", "Design", "Design Mode", "MOD_CLOTH", 3),
    ("PIN", "Pin System", "Pin Cloth", "HOOK", 4), ("EXTRAS", "Extras", "Extras", "SORTBYEXT", 5),("ENHANCE", "Enhance", "Enhance", "GEOMETRY_NODES", 6)
    ))

    bpy.types.Object.sc_sew_collection = []
    bpy.types.Object.sc_temp_selected_sew_verts = []

    bpy.types.Scene.sc_version_addon = StringProperty(default="v. 1.4.3 - ", name="v. 1.4.3 - ", description="addon version")
    bpy.types.Scene.sc_version_blender = StringProperty(default="for Blender 4.2 and higher",name="for Blender 4.2 and higher", description="blender version")
    # CUT AND SEWING
    # bpy.types.Scene.sc_cutsew_duplicate = BoolProperty(name="Cloth", description="Duplicate Drawing", default=False)

    bpy.types.Object.sc_geoNodes_simplycloth_modifier_name = StringProperty(default="", name="Simply Cloth Geo Nodes Modifier Name")
    bpy.types.Object.sc_UI_ModifierBeforeDetected = BoolProperty(name="Modifierdetected", description="Detect Modifier", default=False)
    
    bpy.types.Object.sc_UI_Enhance = BoolProperty(name="Enhance Cloth", description="Enhance with Geo Nodes", default=False)
    # bpy.types.Object.sc_UI_ModifierBeforeDetected = BoolProperty(name="Modifierdetected", description="Detect Modifier", default=False)

    bpy.types.Object.sc_cloth_status = BoolProperty(name="Enable/ Disable Cloth", description="Enable, Disable Cloth", default=True, update=ui_panel.updateClothEnableStatus)

    bpy.types.Object.sc_cloth_drag_info = BoolProperty(name="Drag Usage Information", description="Drag Information", default=False)
    bpy.types.Object.sc_hook_position = any

    bpy.types.Object.sc_cloth_rotate_faces = BoolProperty(name="Rotate Faces", description="Rotate Faces", default=False)

    bpy.types.Scene.scs_preferences_experimental = BoolProperty(name="Experimental Features", description="Experimental Features", default=True)
    bpy.types.Scene.scs_fit_target_object = bpy.props.PointerProperty(type=bpy.types.Object, description="Select Target Object")
    # bpy.types.Object.sc_cloth_rotate_faces = FloatProperty(name="Triangulate Faces", description="Rotate Faces", default=False)

    bpy.types.Object.scs_click_cloth = BoolProperty(name="Click Cloth", description="Current Object Click Cloth", default=False)

    bpy.types.Scene.scs_hex_tri_resolution = IntProperty(default=21, min=6, max=128, description="Resolution")
    bpy.types.Object.scs_hex_quad = BoolProperty(name="Quad Topology", description="Make Quads Topology", default=False)

    bpy.types.Object.scs_sew_autoselect = BoolProperty(name="Auto Select Sew", description="Auto Select Sewing", default=False)

    bpy.types.Scene.scs_use_custom_path = BoolProperty(name="Custom Addons Path", description="Use Custom Path", default=False)
    bpy.types.Scene.scs_extensions_path = StringProperty(default=bpy.utils.user_resource(resource_type="EXTENSIONS", path="user_default"), name="Simply Addons Path", description="Default or Custom Path", subtype="FILE_PATH")
    

def unregister():
    bpy.utils.unregister_class(SelectVertexGroup)
    bpy.utils.unregister_class(VertexGroupMix)
    bpy.utils.unregister_class(customOperator.SimplyCollisionManager)
    bpy.utils.unregister_class(customOperator.RemoveModifier)
    bpy.utils.unregister_class(customOperator.SubdivideCloth)
    bpy.utils.unregister_class(customOperator.CreateCloth)
    bpy.utils.unregister_class(customOperator.AnimationManager)
    bpy.utils.unregister_class(customOperator.CreateWeightPins)
    bpy.utils.unregister_class(customOperator.CreatePins)
    bpy.utils.unregister_class(customOperator.createSewing)
    bpy.utils.unregister_class(customOperator.FinishCloth)
    bpy.utils.unregister_class(customOperator.PokeFace)
    bpy.utils.unregister_class(customOperator.AddPinGroup)
    bpy.utils.unregister_class(customOperator.AddSelectionToLayer)
    bpy.utils.unregister_class(customOperator.DeleteSlider)
    bpy.utils.unregister_class(ui_panel.PREFERENCES_CLOTHSTUDIOPANEL)
    bpy.utils.unregister_class(ui_panel.ClothStudioPanel)
    bpy.utils.unregister_class(ui_panel.UV_ClothStudioPanel)
    bpy.utils.unregister_class(customOperator.ResetClothParameter)
    bpy.utils.unregister_class(customOperator.DensityWeightPaint)
    bpy.utils.unregister_class(customOperator.AddHook)
    bpy.utils.unregister_class(customOperator.DeleteHook)
    bpy.utils.unregister_class(customOperator.FlipNormals)
    bpy.utils.unregister_class(customOperator.StrengthenSelection)
    bpy.utils.unregister_class(customOperator.ShrinkSelection)
    bpy.utils.unregister_class(customOperator.PressureSelection)
    bpy.utils.unregister_class(customOperator.LivePinningPaint)
    bpy.utils.unregister_class(customOperator.ClearSimplyPin)
    bpy.utils.unregister_class(customOperator.LoadTemplatesFromBlend)
    bpy.utils.unregister_class(customOperator.SelectClothSculptBrush)
    bpy.utils.unregister_class(customOperator.SelectForceFalloff)
    bpy.utils.unregister_class(customOperator.SculptMaskOperator)
    bpy.utils.unregister_class(customOperator.SculptSubdivision)
    bpy.utils.unregister_class(customOperator.RemoveSimplyClothMesh)
    bpy.utils.unregister_class(customOperator.SculptMeshShading)
    bpy.utils.unregister_class(customOperator.AddWindToScene)
    bpy.utils.unregister_class(SLIDER_UL_List)
    # bpy.utils.unregister_class(SLIDER_UL_List_Bend)
    bpy.utils.unregister_class(customOperator.RemoveWind)
    bpy.utils.unregister_class(customOperator.SewingCleaningOperators)
    # bpy.utils.unregister_class(customOperator.OpenURL)
    bpy.utils.unregister_class(customOperator.CleanModifiers)
    bpy.utils.unregister_class(customOperator.ClothDyntopoTriangulation)
    bpy.utils.unregister_class(customOperator.RefreshClothParameters)
    bpy.utils.unregister_class(customOperator.AutoSewing)
    bpy.utils.unregister_class(customOperator.AutoExtrudeEdges)
    bpy.utils.unregister_class(customOperator.DrawCutAndSewPattern)
    bpy.utils.unregister_class(customOperator.SimulationToKeyFrame)
    bpy.utils.unregister_class(customOperator.AttachSelectedToCloth)
    bpy.utils.unregister_class(customOperator.DeattachObjectFromCloth)
    bpy.utils.unregister_class(customOperator.DragClothDuringSimulation)
    bpy.utils.unregister_class(customOperator.RebindAttachedObject)
    bpy.utils.unregister_class(customOperator.HighToLowSurfaceDeform)
    bpy.utils.unregister_class(customOperator.SelectOptiClothObject)
    bpy.utils.unregister_class(customOperator.SetUpGeoNodesSimplyCloth)
    bpy.utils.unregister_class(customOperator.SelectVertexGroupForGeoNodesEdit)
    bpy.utils.unregister_class(customOperator.AssignSelectedToVertexGroup)
    bpy.utils.unregister_class(customOperator.DrawFaceSetSelection)
    bpy.utils.unregister_class(customOperator.TearingCloth)
    bpy.utils.unregister_class(customOperator.ResetGeometryNodes)
    bpy.utils.unregister_class(customOperator.ConvertSlicedToSewing)
    bpy.utils.unregister_class(customOperator.BendSelected)
    bpy.utils.unregister_class(customOperator.CutSewingEditMode)
    bpy.utils.unregister_class(customOperator.OpenURLOperator)
    bpy.utils.unregister_class(customOperator.SimplyClothTriangulation)
    bpy.utils.unregister_class(customOperator.SewMethodSimilar)
    bpy.utils.unregister_class(customOperator.SIMPLY_preferences)
    bpy.utils.unregister_class(customOperator.FitToCharacter)
    bpy.utils.unregister_class(customOperator.ClickAndCreate)
    bpy.utils.unregister_class(customOperator.SimplyHexTriangulation)
    bpy.utils.unregister_class(customOperator.ChangeArmatureDummyPose)
    bpy.utils.unregister_class(customOperator.AppendSimplyCharacter)
    bpy.utils.unregister_class(customOperator.DeleteSelectedHolesAndMakeSew)
    bpy.utils.unregister_class(customOperator.MirrorCutPattern)
    bpy.utils.unregister_class(customOperator.CheckLanguageAndSwitchNewDataCheckbox)
    # bpy.utils.unregister_class(customOperator.AddAssetLibraryToPreferences)
    ui_panel.unregisterIcon()
    
