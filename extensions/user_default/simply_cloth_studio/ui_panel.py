'''
Copyright (C) 2025 Vjaceslav Tissen
vjaceslavt@gmail.com

Created by Vjaceslav Tissen
Support by Daniel Meier - Kagi Vision 3D

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FORc A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import bpy
import mathutils
import os
import bpy.utils.previews

from os.path import dirname, join, splitext, isfile
from os import listdir
from . import ui_panel
from . import presets
from . import supportlinks


from bpy.props import StringProperty,FloatProperty, BoolProperty, EnumProperty

custom_icons = None
class PREFERENCES_CLOTHSTUDIOPANEL(bpy.types.AddonPreferences):
    bl_label = "Simply Cloth Studio | 1.4.3"
    bl_idname = "PREF_SIMPLYCLOTHSTUDIO_PT_LAYOUT"
    bl_space_type = 'PREFERENCES'
    
    def draw(self, context):
        layout = self.layout
        self.ui_pref_scs_extensionpath(context, layout)
        
    def ui_pref_scs_extensionpath(self, layout, context):

        row = self.layout.row()
        # row.label(text="Sewing", icon="RIGID_BODY")
        # row.alignment = "CENTER"

        row = self.layout.row()
        row.active_default = True
class UV_ClothStudioPanel(bpy.types.Panel):
    bl_label = "Simply Cloth Studio | 1.4.3"
    bl_idname = "SIMPLYCLOTHSTUDIO_UV_PT_LAYOUT"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Simply"
    def draw(self, context):
        layout = self.layout


        self.ui_uv_edit_sewing(context, layout)


    def ui_uv_edit_sewing(self, layout, context):

        row = self.layout.row()
        row.label(text="Sewing", icon="RIGID_BODY")
        # row.alignment = "CENTER"

        row = self.layout.row()
        row.active_default = True
        row.scale_y = 1.3
        # op = row.label(text="", icon="BLANK1")
        op = row.operator("object.create_sewing", text="Sew", icon="DECORATE_LIBRARY_OVERRIDE")
        op.mode = "CREATE_SEWING_UV"
        row.active_default = False
        row = self.layout.row()
        # op = row.label(text="", icon="BLANK1")
        selectedEdges = bpy.context.active_object.data.total_edge_sel
        if selectedEdges:
            row.enabled = True
        else:
            row.enabled = False
        row.operator("object.scs_sew_similar", text="Auto Select", icon="ZOOM_SELECTED")
        # row.active_default = False
        # row = box.row()
        # row.alert= True
        # op = row.operator("object.create_sewing", text="Remove Sewings", icon="TRASH")
        # op.mode = "REMOVE_SEWING"
        # if "SimplyCloth" in context.active_object.modifiers:

        
        # if "SimplyCloth" in context.active_object.modifiers:
        row = row

        row = self.layout.row()
        row.label(text="Edit Sewing", icon="LINK_BLEND")

        row = self.layout.row()
        row.active_default = True	
        row.scale_y = 1.6
        op = row.operator("object.additional_sewing_operator",text="Sew - Close Selection", icon="LINK_BLEND")
        op = "CLOSE SELECTION"
        row.active_default = False
        op = row.operator("mesh.bridge_edge_loops",text="Sew - Bridge Edge Loops", icon="SNAP_EDGE")
        op = "use_merge=True, merge_factor=1, twist_offset=0, number_cuts=0, smoothness=1, profile_shape_factor=0"
        row = self.layout.row()
        row.scale_y = 1.6
        op = row.operator("object.create_sewing", text="Select Mesh Bounds", icon="MOD_MESHDEFORM")
        op.mode = "SELECT_BOUNDS"
        row = self.layout.row()
        op = row.operator("object.create_sewing", text="Select Sewing", icon="RESTRICT_SELECT_OFF")
        op.mode = "SELECT_SEWING"
        # row = box.row()
        row.alert= True
        op = row.operator("object.create_sewing", text="Remove Sewings", icon="TRASH")
        op.mode = "REMOVE_SEWING_UV"

class ClothStudioPanel(bpy.types.Panel):
    bl_label = "Simply Cloth Studio | 1.4.3"
    bl_idname = "SIMPLYCLOTHSTUDIO_PT_LAYOUT"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Simply Addons"

    def checkCounter(self, context):
        
        count= -1
        for i, vs in enumerate(context.active_object.vertex_slider):
            count = i
        if count > -1:
            return True
        elif count == -1:
            return False
        global custom_icons
        active_object = context.active_object

        createClothIcon = custom_icons["simply_cloth_helper_icon"].icon_id
        sculptClothIcon = custom_icons["icon_sculpt_mode"].icon_id
        attatchToIcon = custom_icons["icon_attach_to"].icon_id

    def draw(self, context):
        layout = self.layout
        # box = layout.box()
        # row = box.row()
        global custom_icons
        # icons = [{"create": createClothIcon}, {"sculpt": sculptClothIcon}, {"attatch":attatchToIcon}]
        if context.mode == "OBJECT":
            # if "SimplyCloth" in context.active_object.modifiers:

            if context.active_object:

                self.ui_selectMode(layout, context)
                if context.active_object.scs_mode == "SIM":
                    if "SimplyCloth" not in context.active_object.modifiers:
                        self.ui_createCloth(layout, context)
                        if "SimplyCollision" not in context.active_object.modifiers:
                            self.ui_collision_add(layout, context, "Add Collision")
                        else:
                            if "SimplyCollision" in context.active_object.modifiers:
                                self.ui_collision_start(layout, context, "Collision")
                        if context.active_object.name == "simply_dummy":
                            self.ui_dummy(layout, context)
                    else:
                        self.ui_sim_playmanager(layout, context)
                        self.ui_sim_presetManager(layout, context)
                        if context.active_object.sc_UI_Overlay:
                            self.ui_sim_overlaySettings(layout,context)
                        if context.active_object.sc_UI_Settings:
                            self.ui_sim_bakeSettings(layout, context)
                        if context.active_object.sc_UI_ClothParameters:
                            self.ui_sim_clothProperties(layout, context)
                            self.ui_collision_cloth(layout, context)
                            
                            # self.ui_sim_pressure(layout, context)
                            self.ui_adjust_sewing(layout, context)

                if context.active_object.scs_mode == "ADJUST":

                    if "SimplyCloth" not in context.active_object.modifiers:
                        self.ui_design_triangulate(layout, context)
                        self.ui_createCloth_sculpt(layout, context)
                        if "SimplyCollision" not in context.active_object.modifiers:
                            self.ui_collision_add(layout, context, "Set Collision")
                            self.ui_edit_solidify(layout, context)
                            self.ui_edit_smooth(layout, context)
                    else:
                        # self.ui_sim_overlaySettings(layout,context)
                        self.ui_sim_playmanager(layout, context)
                        # self.ui_createCloth_sculpt(layout, context)
                        # self.ui_collision_cloth(layout, context)
                        # self.ui_sim_overlaySettings(layout,context)
                        self.ui_adjust_pingroup(layout, context)
                        self.ui_adjust_shrink(layout, context)
                        self.ui_edit_solidify(layout, context)
                        self.ui_edit_smooth(layout, context)
                    if "SimplyCollision" in context.active_object.modifiers:
                        self.ui_collision_start(layout, context, "Collision")
                    self.ui_adjust_attachpanel(layout, context)

                    
                    
                    
                    if context.scene.scs_preferences_experimental:
                        self.ui_adjust_drag_cloth(layout, context)
                    # self.ui_adjust_density(layout, context)

                    # bpy.ops.sculpt.sculptmode_toggle()

                if context.active_object.scs_mode == "DESIGN":
                    if "SimplyCloth" not in context.active_object.modifiers:
                        self.ui_design_drawCloth(layout, context)
                        # self.ui_design_triangulate(layout, context)
                    else:
                        
                        self.ui_sim_playmanager(layout, context)
                        self.ui_adjust_subdivision(layout, context)
                        self.ui_design_triangulate(layout, context)
                        self.ui_design_drawCloth(layout, context)
                    self.ui_Design_fit_to_object(layout, context)
                    self.ui_adjust_shrink(layout, context)
                    self.ui_adjust_attachpanel(layout, context)
                    self.ui_edit_solidify(layout, context)
                    
                        # self.ui_finish_panel(layout, context)

                if context.active_object.scs_mode == "ENHANCE":
                    if "SimplyCloth" in context.active_object.modifiers:
                        self.ui_sim_playmanager(layout, context)
                    self.ui_enhance_geoNodes(layout, context)



                if context.active_object.scs_mode == "FINISH":
                    if "SimplyCloth" not in context.active_object.modifiers:
                        self.ui_finish_info_createcloth(layout, context)
                        if "SurfaceDeform" in context.active_object.modifiers:
                            self.ui_enhance_optim_cloth_surfaceDeform(layout, context)
                    else:
                        self.ui_finish_panel(layout, context)
                        self.ui_sim_playmanager(layout, context)

                        self.ui_final_optimcloth(layout, context)
                # if "SimplyCloth" not in context.active_object.modifiers:


                    # row.label(text="Cloth", icon="MOD_CLOTH")
                    # row = box.row()


                        # pass
                        # if "simply" in bpy.context.active_object.modifiers:

                        # if "SimplyCollision" not in context.active_object.modifiers:




                        # self.ui_collision_start(layout, context, "Collision")

            else:
                # self.ui_design_drawCloth(layout, context)
                self.ui_no_object_selected(layout, context)
                self.ui_noactive_cutsew(layout, context)

        elif context.mode == "SCULPT":
            # if context.active_object.scs_mode == "ADJUST":
                # self.ui_createCloth(layout, context)
            self.ui_adjust_sculptPanel(layout, context)

        elif context.mode == "EDIT_MESH":
            self.ui_edit_selectMode(layout, context)
            self.ui_sim_overlaySettings(layout, context)
            if context.active_object.scs_mode_edit == "EDIT":
                
                # self.ui_edit_cleanModifier(layout, context)
                self.ui_edit_subdiv(layout, context)
                self.ui_design_triangulate(layout, context)
                self.ui_edit_extrude_edge(layout, context)
                self.ui_edit_design_selection(layout, context)
                self.ui_edit_solidify(layout, context)
                self.ui_edit_smooth(layout, context)
            
            if context.active_object.scs_mode_edit == "SEW":
                self.ui_edit_sewing(layout, context)
                # self.ui_edit_autosewing(layout, context)
            if context.active_object.scs_mode_edit == "DESIGN":
                3
                self.ui_edit_separateClothSelection(layout, context)
                self.ui_edit_selectToCloth(layout, context)
                # self.ui_edit_draw_cutsew_pattern(layout, context)

            if context.active_object.scs_mode_edit == "PIN":
                # self.ui_edit_smooth(layout, context)
                self.ui_edit_pingroups(layout, context)
                # self.ui_edit_solidify(layout, context)

            if context.active_object.scs_mode_edit == "EXTRAS":
                self.ui_edit_extras(layout, context)
                self.ui_edit_bendSelect(layout, context)
            if context.active_object.scs_mode_edit == "ENHANCE":
                self.ui_enhance_geoNodes(layout, context)
            self.ui_edit_backToObject(layout, context)
        elif context.mode =="PAINT_WEIGHT":
            self.ui_paint_pingroups(layout, context)
        elif context.mode=="EDIT_CURVE":
            self.ui_curve_edit(layout, context)
            self.ui_curve_convert(layout, context)

        self.ui_infoBar(layout, context)
        self.ui_supportBar(layout, context)



##################################################################################
    def drawtest(self, context):
        layout = self.layout

        global custom_icons
        active_object = context.active_object

        createClothIcon = custom_icons["simply_cloth_helper_icon"].icon_id
        sculptClothIcon = custom_icons["icon_sculpt_mode"].icon_id
        attatchToIcon = custom_icons["icon_attach_to"].icon_id

        
                                    


                    #To Do
                    # # UI SIMPLY TEARING
                    # # if context.active_object.sc_geoNodes_simplycloth_modifier_name == "":
                    # box = layout.box()
                    # row = box.row(align=True)
                    # row.label(text="Cloth Tearing", icon="GEOMETRY_NODES")
                    # row.scale_y = 1.3
                    # row.operator("object.sc_tear_cloth_setup", text="Cloth Tearing (WIP)", icon="PLUS")
                        # row.operator("object.sc_setup_simply_geo_nodes", text="Simply Mesh Enhance (WIP)", icon="PLUS")
                    
                    # if context.scene.sc_last_cloth_object:
                        


        # DRAW CUT AND SEWING PATTERN
        # if context.mode == "OBJECT_MODE":
        # 	box = layout.box()
            # row = box.row()
            # row.prop(bpy.data.objects[context.active_object.name], "name", text="Name")
            
            # row = box.row()
            # row.scale_y = 2.0
            # # row.label(text="", icon="GREASEPENCIL")
            # op = row.operator("scene.sc_draw_cut_and_sew_pattern", text="Draw Cut & Sew Pattern", icon="GREASEPENCIL")
            # op.mode = "CREATE"



        # # DRAW CUT AND SEWING PATTERN
        # box = layout.box()
        # row = box.row()
        # row.label(text="",icon="MOD_SIMPLIFY")
        # row.operator("gpencil.stroke_simplify", text="Simplify Curve")
        # if "MIRROR" in context.active_object.grease_pencil_modifiers:
        # 	row = box.row()
        # 	row.label(text="", icon="MOD_MIRROR")
        # 	row.prop(context.object.grease_pencil_modifiers["Mirror"], "use_axis_x", text="X", icon="BLANK1")
        # 	row.prop(context.object.grease_pencil_modifiers["Mirror"], "use_axis_y", text="Y", icon="BLANK1")
        # 	row.prop(context.object.grease_pencil_modifiers["Mirror"], "use_axis_z", text="Z", icon="BLANK1")
        # # if "GP_SIMPLIFY" in context.active_object.grease_pencil_modifiers:
        # row = box.row()
        # row.label(text="", icon="MOD_LENGTH")
        # row.prop(context.object.grease_pencil_modifiers["Simplify"], "length", text="Length", icon="BLANK1")
    
        if context.mode == "EDIT_GPENCIL" or context.mode == "PAINT_GPENCIL" or context.mode =="OBJECT":
            if context.active_object and "SimplyCloth" not in context.active_object.modifiers:
                if context.active_object.type == "GPENCIL":
                    box = layout.box()
                    row = box.row()
                    row.label(text="",icon="MOD_SIMPLIFY")
                    row.operator("gpencil.stroke_simplify", text="Simplify Curve")
                    row.operator("gpencil.frame_clean_loose", text="Clean up")
                    # row = box.row()
                    # row.label(text="",icon="MOD_DECIM")
                    # row.label(text="",icon="MOD_DECIM")
                    # bpy.ops.gpencil.frame_clean_loose(limit=6)


                    if "Mirror" in context.active_object.grease_pencil_modifiers:
                        row = box.row()
                        row.label(text="", icon="MOD_MIRROR")
                        row.prop(context.object.grease_pencil_modifiers["Mirror"], "use_axis_x", text="X", icon="BLANK1")
                        row.prop(context.object.grease_pencil_modifiers["Mirror"], "use_axis_y", text="Y", icon="BLANK1")
                        row.prop(context.object.grease_pencil_modifiers["Mirror"], "use_axis_z", text="Z", icon="BLANK1")
                    
                    # if context.mode == "EDIT_GPENCIL":
                    row = box.row()	
                    row.label(text="", icon="MOD_LENGTH")
                    if context.active_object.type == "GPENCIL":
                        if "Simplify" in context.object.grease_pencil_modifiers:
                            row.prop(context.object.grease_pencil_modifiers["Simplify"], "length", text="Length", icon="BLANK1")

                    # row = box.row()
                    # row.label(text="", icon="MOD_SOLIDIFY")
                    # row.prop(context.scene, "sc_cutdraw_unitard", text="Unitard (One closed piece)", icon_value=)


                    # if context.active_object.type == "GPENCIL":
                        # box = layout.box()
                        # row = box.row()
                        # row.scale_y = 2.0
                        # op = row.operator("scene.sc_draw_cut_and_sew_pattern", text="Generate Cloth from Selected")
                        # op.mode = "FINISH"
                        # if context.mode == "PAINT_GPENCIL" or context.mode == "EDIT_GPENCIL":
                    if context.scene.sc_cut_sew_pattern_created==True:
                        box = layout.box()
                        row = box.row()
                        # row.label(text="", icon="MOD_MULTIRES")
                        # row.prop(context.active_object, "sc_cutdraw_trian_quad", text="Make Quad Based Topology", icon="BLANK1")
                        # row = box.row()
                        row.label(text="", icon="MOD_CLOTH")
                        row.scale_y = 1.6
                        op = row.operator("scene.sc_draw_cut_and_sew_pattern", text="Generate Cloth from Drawing")
                        op.mode = "FINISH"
                        box = layout.box()
                        row = box.row()
                        row.label(text="", icon="EDITMODE_HLT")
                        row.operator("gpencil.editmode_toggle", text="Edit Mode", icon="LOOP_BACK")
            # row = box.row()
            # row.scale_y = 2.0
            # op = row.operator("scene.sc_draw_cut_and_sew_pattern", text="Generate Simply Cloth")
            # op.mode = "FINISH"

        # row = box.row()
        selected = any
        active = any

        for obj in bpy.data.objects:
            if obj.select_get():
                if bpy.context.view_layer.objects.active == obj.name:
                    active = obj
                else:
                    selected = obj










    ################
    # UI
    ##############
            
    def ui_infoBar(self, layout, context):
        icons = custom_icons
        box = layout.box()	
        
        row = box.row()		
        row.alert = True
        sc_version = "Simply Cloth Studio - by Vjaceslav Tissen"				
        row.alignment="CENTER"
        row.label(text=sc_version, icon_value=icons["simply_cloth_helper_icon"].icon_id)

        row = box.row()				
        row.scale_y = 0.1	
        row.enabled = False
        row.alignment = "CENTER"
        versionslabel = context.scene.sc_version_addon + context.scene.sc_version_blender
        row.label(text=versionslabel)
            
    def ui_collision_add(self, layout, context, name):
        box = layout.box()
        row = box.row(align=True)
        # row = box.row()
        # row.label(text="Collision", icon="SNAP_PEEL_OBJECT")
        # row = box.row()
        row.scale_y = 1.6
        # row.label(text="", )
        op = row.operator("object.simply_collision_manager", text=name,icon_value=custom_icons["import"].icon_id)
        op.mode = "ADDNEW"

    def ui_collision_start(self, layout, context, name):
    # Collision
        settings = context.object.collision
        collisionActive = False

        # if context.scene.sc_UI_Collision:
        # 	collisionActive = True
        # else:
        # 	collisionActive = False
        
        # if not collisionActive:
        # 	row = box.row()
        # 	row.scale_y = 2.0
        # 	row.label(text="", icon="OBJECT_HIDDEN")
        # 	op = row.operator("object.simply_collision_manager", text="Activate")
        # 	op.mode = "ADDNEW"
        # if collisionActive:
        active_object = context.active_object

        box = layout.box()
        row = box.row(align=True)
        row.label(text=name, icon_value=custom_icons["layer"].icon_id)
        row.alert= True
        op = row.operator("object.simply_collision_manager", text="Remove", icon="TRASH")
        op.mode = "REMOVE"
        # row.label(text="", icon="BLANK1")
        # row.scale_y = 2.0
        #row.prop(active_object, "friction_slider", slider=True, text="Friction") # BAD CODE
        row = box.row()
        row.prop(active_object.modifiers["SimplyCollision"].settings, "cloth_friction", slider=True, text="Friction")  # GOOD CODE - Note that this changes the value somewhat since there's no calculation
        row = box.row()
        # row.label(text="", icon="BLANK1")
        row.prop(settings, "thickness_inner", text="Thickness Inner", slider=True)
        row.prop(settings, "thickness_outer", text="Thickness Outer", slider=True)

    def ui_createCloth(self, layout, context):
        box = layout.box()
        row = box.row(align=True)
        row.scale_y = 1.6

        # row.label(text="", icon="BLANK1")
        # row.label(text="")
        row.active_default = True
        op = row.operator("object.create_cloth", text="Convert to Simply Cloth", icon_value=custom_icons["simply_cloth_helper_icon"].icon_id)
        op.mode = "CREATECLOTH"   

        # op = row.operator("mesh.primitive_grid_add", text="primitive_grid_add to Simply Cloth", icon_value=custom_icons["createCloth"].icon_id)
        

        # op.x_subdivisions=20
        # op.y_subdivisions=20
        # op.size=2
        # op.enter_editmode=False
        # op.align='WORLD'
        # op.location=(0, 0, 2)
        # op.scale=(1, 1, 1)


        
    
    def ui_selectMode(self, layout, context):
        box = layout.box()
        row = box.row(align=True)
        row.scale_y = 1.6
        row.prop(context.active_object, "scs_mode", text="")
        row.alert= True
        row.scale_y = 1.6
        row.operator("object.remove_cloth", text="", icon="TRASH")

    def ui_edit_selectMode(self, layout, context):
        box = layout.box()
        row = box.row()
        row.scale_y = 1.6
        
        row.prop(context.active_object, "scs_mode_edit", text="")
        row.alert= True

        row.scale_y = 1.6
        row.operator("object.remove_cloth", text="", icon="TRASH")
        # row.label(text="", icon="BLANK1")
        # row.label(text="")
        # row.active_default = True

        # row.operator("object.create_cloth", text=name[0], icon_value=custom_icons["createCloth"].icon_id)
        # row.operator("object.create_cloth", text=name[1], icon_value=custom_icons["createCloth"].icon_id)
        # row = box.row(align=True)
        # row.scale_y = 1.6
        

        # row.operator("object.create_cloth", text=name[2], icon_value=custom_icons["createCloth"].icon_id)
        # row.operator("object.create_cloth", text=name[3], icon_value=custom_icons["createCloth"].icon_id)

    def ui_supportBar(self, layout, context):
        box = layout.box()
        row = box.row()
        row.label(text="", icon="FUND")
        row.prop(context.scene, "scs_open_urls", icon="BLANK1")
        row.label(text="", icon="FUND")
        if context.scene.scs_open_urls == True:
            for i, addons in enumerate(supportlinks.supportPartner):
                link = addons["link"]
                name = addons["name"]
                icon = addons["icon"]
                # custom_icons["createCloth"].icon_id
                if i % 2 == 0:
                    row = box.row(align=False)
                if addons["name"] == "Simply Addons":
                    row = box.row(align=False)
                    row.label(text="", icon="FUND")
                    row.scale_y = 1.5
                    opname = row.operator("scene.sc_open_url", text=name, icon_value=custom_icons["simply_cloth_helper_icon"].icon_id)
                    opname.url = link
                    row.label(text="", icon="FUND")
                else:
                    opname = row.operator("scene.sc_open_url", text=name, icon=icon)
                    opname.url = link

    def ui_enhance_optim_cloth_surfaceDeform(self, layout, context):
        
        box = layout.box()
        row = box.row()
        row.label(text="Optim Cloth ", icon="OBJECT_HIDDEN")
        op = row.operator("object.select_opti_cloth_object", text="Select Cloth", icon="UV_SYNC_SELECT")
        op.mode = "SELECT"
        op = row.operator("object.select_opti_cloth_object", text="", icon="HIDE_OFF")
        op.mode = "HIDE"
        row = box.row()
        op = row.operator("object.rebind_attached_object", text="Rebind", icon="FILE_REFRESH")
        op.mode = "BIND"
        row.prop(context.object.modifiers["SurfaceDeform"], "strength", text="Intensity", icon="LINK_BLEND")
        row = box.row()
        
        op = row.operator("object.rebind_attached_object", text="Reset Position", icon="TRANSFORM_ORIGINS")
        op.mode = "POSITION"
        
    
        # row.scale_y = 1.6

        # row.label(text="")
        # bpy.ops.object.surfacedeform_bind(modifier="SurfaceDeform")
        # bindingText = "Connect"
        # if context.active_object.modifiers["SurfaceDeform"].is_bound == True:
        # 	bindingText = "Unbind"
        # else:
        # 	bindingText = "Bind"
        # op = row.operator("object.surfacedeform_bind", text=bindingText, icon="BLANK1")
        # op.modifier="SurfaceDeform"

        # PLAY STOP SECTION
        # box = layout.box()
        
        # row.	scale_y=2.0
        
        row = box.row(align=False)
        screen = context.screen
        if screen.is_animation_playing:
            icon = custom_icons["pause_icon"].icon_id
            text = "Pause"
            iconClean= "PAUSE"
        else:
            icon = custom_icons["play_icon"].icon_id
            text = "Play"
            iconClean= "PLAY"
        # row.active_default = True
        op = row.operator("screen.animation_manager", text=text, icon_value=icon)
        op.mode = "PLAY"
        
        row.active_default = False
        # row.alert = True
        # op = row.operator("screen.animation_play", text="", icon=iconClean)
        op = row.operator("screen.animation_manager", text="Reset", icon_value=custom_icons["stop_icon"].icon_id)
        op.mode = "STOP"
    
    def ui_sim_presetManager(self, layout, context):
        # PRESET
        box = layout.box()
        # row = box.row()
        # row.label(text="Simply Cloth Settings")
        # row = box.row()
        preset_name = context.active_object.preset_name
        
        row = box.row()
        if bpy.context.object.sc_cloth_status == False:
            row.active = False
            row.active_default = False
            # row.enabled = False
            row.alert = True
        if bpy.context.object.sc_cloth_status == True:
            row.active = True
            row.active_default = True
            # row.enabled = True
            row.alert = False
        row.template_icon_view(context.active_object, "presets", scale=5.4,scale_popup=6.0,show_labels=False)
        
        if bpy.context.object.sc_cloth_status == False:
            # icon = "HIDE_ON"
            icon = custom_icons["disable"].icon_id
            text = "Inactive"
        else:
            icon = custom_icons["enable"].icon_id
            # "HIDE_OFF"
            text = "Active"
        col = row.column()
        col.scale_y = 1.3
        col.prop(context.active_object, "sc_cloth_status", text=text, icon_value=icon)
        col.prop(context.active_object, "sc_UI_Overlay", text="Overlay", icon_value = custom_icons["node_transparent"].icon_id)
        col.prop(context.active_object, "sc_UI_Settings", text="Bake Settings", icon_value = custom_icons["temp"].icon_id)
        # col = row.column()

        col.prop(context.active_object, "sc_UI_ClothParameters", text="Cloth Properties", icon_value = custom_icons["buts"].icon_id)
        # row = box.row()
        row = box.row()
    
        col = row.column()
        col.scale_y=1.2
        # col.scale_x=1.04
        col.prop(context.active_object, "sim_quality", text="")
        col.scale_x=1.1

        col = row.column()
        col.scale_y=1.2
        col.prop(context.active_object.modifiers["SimplyCloth"].settings, "quality", text="Quality")
        col = row.column()
        col.scale_y=1.2
        col.prop(context.active_object.modifiers["SimplyCloth"].collision_settings, "collision_quality", text="Collision") # GOOD CODE
        row = box.row()
        row.scale_x=1.1
        row.prop(context.active_object.modifiers["SimplyCloth"].settings, "bending_model", text="", icon_value= custom_icons["setup"].icon_id)
        
        
        # col.scale_y = 2
        # col.prop(context.active_object, "sc_cloth_status", text=text, icon=icon)
        
        col = row.column()
        # row = row.column()
        # row = box.row()
        # row.prop(context.active_object, "sim_quality", text="")
        
        # row.prop(context.active_object, "sc_UI_ClothParameters", text="Cloth Properties", icon="PROPERTIES")
        # row = box.row()
        # col = row.column()

        mod = context.active_object.modifiers["SimplyCloth"].settings.effector_weights
        col.prop(mod, "gravity", text="Gravity")
        
        
        col = row.column()
        mod = context.active_object.modifiers["SimplyCloth"].settings
        col.prop(mod, "time_scale", text="Speed")


    def ui_sim_bakeSettings(self, layout, context):

        # Animation Play
        box = layout.box()
        # box = layout.box()
        row = box.row()
        # row.label(text="Simulation", icon="RENDER_ANIMATION")

        row.prop(context.active_object, "start_frame", text="Start")
        # row.prop(context.active_object, "start_frame", text="Start")
        row.prop(context.active_object, "end_frame", text="End")
        # row.prop(context.active_object, "end_frame", text="End")
        row = box.row()
        op = row.operator("screen.animation_manager", text="Bake cache", icon_value = custom_icons["history_cycle_back"].icon_id)
        op.mode = "BAKEFROMCACHE"
        op = row.operator("screen.animation_manager", text="Bake all ", icon_value = custom_icons["time"].icon_id)
        op.mode = "BAKEALLFROMCACHE"
        row = box.row()
        row.operator("object.cloth_to_keyframes", text="Bake to Keyframe", icon_value = custom_icons["keyframes_clear"].icon_id)
        row.alert= True
        op = row.operator("screen.animation_manager", text="Delete Bake Cache", icon="TRASH")
        op.mode = "DELETEBAKECACHE"

    def ui_sim_playmanager(self, layout, context):
                # PLAY STOP SECTION
        box = layout.box()
        
        # row = box.row()
        # row.scale_x = 5.0
        # row.alignment = "CENTER"
        
        # row.scale_y=2.0
        # row = box.row(align=True)
        
        row = box.row(align=False)
        row.scale_y=2.0
        screen = context.screen
        if screen.is_animation_playing:
            icon = custom_icons["pause_icon"].icon_id
            text = "Pause"
            iconClean= "PAUSE"
            # row.scale_x = 0.2
            # row.scale_x = 1
            op = row.operator("screen.animation_manager", text=text, icon_value=icon)
            op.mode = "PLAY"
            # row.scale_x = 2
            op = row.operator("screen.animation_manager", text="Stop", icon_value=custom_icons["stop_icon"].icon_id)
            op.mode = "STOP"
            if context.active_object.scs_mode != "SIM":
                row = box.row()
                row.prop(context.active_object, "sim_quality", text="")
        else:
            icon = custom_icons["play_icon"].icon_id
            text = "Play"
            iconClean= "PLAY"
            # row.scale_x = 1
            op = row.operator("screen.animation_manager", text=text, icon_value=icon)
            op.mode = "PLAY"
            # row.scale_x = 2
            op = row.operator("screen.animation_manager", text="Stop", icon_value=custom_icons["stop_icon"].icon_id)
            op.mode = "STOP"
            if context.active_object.scs_mode != "SIM":
                row = box.row()
                # row.scale_x = 0.5
                row.prop(context.active_object, "sim_quality", text="")

        
    def ui_sim_overlaySettings(self, layout, context):
                #OVERLAY
        box = layout.box()
        row = box.row()

        row.prop(context.active_object, "face_orientation", text="Face Orientation", icon_value = custom_icons["markfsface"].icon_id)
        if context.mode == "EDIT_MESH":
            row.operator("object.flip_normals", text="Flip Normals", icon="DECORATE_OVERRIDE")
            row = box.row() 
            if context.active_object.weight_pin_view:
                icon = "HIDE_OFF"
            else:
                icon = "HIDE_ON"
                # box = layout.box()
                # row = box.row()
            row.prop(context.active_object, "weight_pin_view", text="Weights", icon=icon)
        row.prop(context.active_object, "show_wireframes", text="Wireframe", icon_value = custom_icons["mod_wireframe"].icon_id)

        if context.mode == "OBJECT":
            row = box.row()
            row.operator("object.shade_smooth", text="Shade Smooth", icon_value = custom_icons["antialiased"].icon_id)
            row.operator("object.shade_flat", text="Shade Flat", icon_value = custom_icons["aliased"].icon_id)

    def ui_sim_clothProperties(self, layout, context):
        #CLOTH SETTINGS
        active_object = context.active_object

        # box = layout.box()
        # row = box.row()
        # row.scale_y= 1.1
        
        # row.emboss = "NONE"
        # row.label(text="Cloth Quality", icon="MOD_HUE_SATURATION")
        # row.emboss = "NORMAL"
        # row.prop(active_object.modifiers["SimplyCloth"].settings, "bending_model", text="Bending")
        # bpy.data.objects["Cube"].modifiers["SimplyCloth"].settings.bending_model
        # row.operator("scene.sc_refresh_parameter", text="refresh", icon="PRESET_NEW")
        # row.label(text="", icon="BLANK1")

        
        # row = box.row()
        # # row.prop(active_object, "quality_steps_slider", text="Quality Steps")
        # row.active_default = True
        # row.prop(active_object.modifiers["SimplyCloth"].settings, "quality", text="Quality Steps") # GOOD CODE
# row = box.row()
        # if "SimplyCloth" in active_object.modifiers:
        obj = context.active_object
        # row = box.row()


        box = layout.box()
        row = box.row()
        row.emboss = "NONE"
        row.label(text="Cloth Parameter", icon_value = custom_icons["buts"].icon_id)
        row.label(text="", icon="BLANK1")
        row.alert= True
        row.label(text="", icon="TRASH")
        row.emboss = "NORMAL"
        # row = box.row()
        row.alert= False
        row.operator("object.reset_parameters", text="Restore Settings")




        row = box.row()
        row.label(icon_value= custom_icons["mod_simpledeform"].icon_id)
        row.prop(active_object, "stiffness_slider", slider=True, text="Stiffness") #- Added the asterisk to indicate that this is a one way control that affects multiple parameters
        # row.label(icon="OUTLINER_DATA_SURFACE")
        row.label(icon_value = custom_icons["shear"].icon_id)
        row.prop(active_object, "wrinkle_slider", slider=True, text="Wrinkles")
        row = box.row()
        row.label(icon_value = custom_icons["edge_collapse"].icon_id)
        row.prop(active_object, "shrink_slider", slider=True, text="Shrink")
        # row.label(icon="GROUP_VERTEX")
        row.label(icon_value = custom_icons["uv_vertexsel"].icon_id)
        row.prop(active_object.modifiers["SimplyCloth"].settings, "shrink_max", slider=True, text="Vertex Shrink")

        row = box.row()
        
        row.label(text="", icon_value = custom_icons["outliner_ob_curves"].icon_id)
        row.prop(active_object, "strenghten_slider", slider=True, text="Strength")
        row.label(icon_value= custom_icons["rndcurve"].icon_id)
        row.prop(active_object,"fold_slider",slider=True,text="Folds")
        # row.prop(active_object.modifiers["SimplyCloth"].settings,"bending_damping",slider=True,text="Folds") # GOOD CODE - Note that this changes the value somewhat since there's no calculation


        # row.prop(active_object.modifiers["SimplyCloth"].settings, "bending_stiffness", slider=True, text="Wrinkles") # GOOD CODE - Note that this changes the value somewhat since there's no calculation

        # bpy.context.object.shrink_max = 0.481865


        # row = box.row()
        # row.prop(active_object.modifiers["SimplyCloth"].settings, "shrink_max", slider=True, text="Shrink")


        
        # row = box.row()

        # row.prop(active_object.modifiers["SimplyCloth"].settings, "vertex_group_shrink", text="")
        # row = box.row()



        row = box.row()

        row.label(icon="MOD_VERTEX_WEIGHT")
        # row.label(icon_value = custom_icons["rigid_calculate_mass"].icon_id)
        row.prop(active_object.modifiers["SimplyCloth"].settings, "mass", text="Weight")
        # row = box.row()

        if "simplySmooth" in context.active_object.modifiers:
            mod = context.active_object.modifiers["simplySmooth"]
            row.label(icon_value = custom_icons["matfluid"].icon_id)
            row.prop(mod, "iterations", slider=True, text="Smoothing")
        # row = box.row()
        
        self.ui_edit_solidify(layout, context)
        # self.ui_edit_smooth(layout, context)
        # self.ui_subdivision_modifier(layout, context)
        if "SimplySub" in active_object.modifiers:
            row = box.row()
            row.alert=True
            # row.label(text="", icon="ERROR")
            row.label(text="", icon_value = custom_icons["mod_subsurf"].icon_id)
            # row.prop(active_object.modifiers["SimplySub"], "levels", text="Viewport Resolution",icon="MOD_SUBSURF")
            row.prop(active_object.modifiers["SimplySub"], "levels", text="Viewport Resolution")
            row.label(text="", icon="RESTRICT_RENDER_OFF")
            # row.label(text="", icon_value = custom_icons["restrict_render_off"].icon_id)
            row.prop(active_object.modifiers["SimplySub"], "render_levels", text="Render Resolution",icon="MOD_SUBSURF")
        # row = box.row()
        if context.active_object.sc_geoNodes_simplycloth_modifier_name in context.active_object.modifiers:
            Simply_GeoNodes_Modifier = context.active_object.modifiers[context.active_object.sc_geoNodes_simplycloth_modifier_name]
            Simply_GeoNodes = context.active_object.modifiers[context.active_object.sc_geoNodes_simplycloth_modifier_name].node_group.nodes
            if "SC_Global_Intensity" in Simply_GeoNodes:
                row = box.row()
                row.label(text="", icon="GEOMETRY_NODES")
                row.scale_y=1.6
                row.prop(Simply_GeoNodes["SC_Global_Intensity"].outputs[0], "default_value", text="Global Intensity", invert_checkbox=True)
        #PRESSURE
        # box = layout.box()
        row = box.row()
        # row.label(text="", icon="SNAP_FACE_NEAREST")
        row.label(text="", icon_value = custom_icons["force_drag"].icon_id)
        # row.prop(active_object, "pressure", text="Inflate Cloth", icon="GIZMO")
        row.prop(active_object, "pressure", text="Inflate Cloth", icon_value=custom_icons["gizmo"].icon_id)
        # row.label(text="", icon="BLANK1")
        row.scale_y=1
        if active_object.modifiers["SimplyCloth"].settings.use_pressure == True:
            mod = active_object.modifiers["SimplyCloth"].settings
            row = box.row()

            # row.label(text="", icon="MOD_VERTEX_WEIGHT")
            row.label(text="", icon_value = custom_icons["paint_add"].icon_id)
            op = row.operator("object.pressure_assign_group", text="Inflate Live Paint")
            op.mode = "PAINT"
            # row.label(icon="BLANK1")
            row.alert= True
            op = row.operator("object.pressure_assign_group", text="", icon="TRASH")
            op.mode = "REMOVE"
            row = box.row()
            if mod.use_pressure:
                # row.emboss="NONE"
                # row.label(text="", icon="IPO_LINEAR")
                row.label(text="", icon_value = custom_icons["spline_type"].icon_id)
                row.prop(active_object, "pressure_intensity_slider", text="Intensity")
                # row = box.row()
                # row.emboss = "NONE"
                # row.label(text="", icon="PANEL_CLOSE")
                row.label(text="", icon_value = custom_icons["multiplication"].icon_id)
                row.prop(active_object, "pressure_factor_slider", text="Factor")

        # self.ui_sim_pressure(layout, context)
    def ui_collision_cloth(self, layout, context):
            # COLLISION OBJECT MODE
        context = bpy.context
        active_object = context.active_object
        box = layout.box()
        row = box.row()
        # row.label(text="Collision", icon="MOD_BOOLEAN")
        row.label(text="Collision", icon_value = custom_icons["import"].icon_id)
        row.prop(active_object, "objectCollisionDistance_slider", slider=True, text="Collision Distance")
        # row = box.row()
        # row.label(icon="BLANK1")
        
        # row = box.row()
        row = box.row()
                            
        #row.prop(active_object, "self_collision", text="Self Collision") # BAD CODE
        # row.prop(active_object.modifiers["SimplyCloth"].collision_settings, "use_self_collision", text="Self Collision",icon="MOD_SKIN")
        row.prop(active_object.modifiers["SimplyCloth"].collision_settings, "use_self_collision", text="Self Collision",icon_value = custom_icons["mod_thickness"].icon_id)
        if active_object.modifiers["SimplyCloth"].collision_settings.use_self_collision == True:
            row.prop(active_object.modifiers["SimplyCloth"].collision_settings, "self_distance_min", slider=True, text="Self Distance")
            
        
        # Collision
        collisionActive = False
        if "SimplyCollision" in context.active_object.modifiers:
            collisionActive = True
        else:
            collisionActive = False

        if not collisionActive:
            
            row = box.row()
            # op = row.operator("object.simply_collision_manager", text="Collision with others", icon="NLA_PUSHDOWN")
            op = row.operator("object.simply_collision_manager", text="Collision with others", icon_value = custom_icons["mod_array"].icon_id)
            op.mode = "ADDFROMCLOTH"

        if collisionActive:
            settings = context.object.collision
            row = box.row()
            row.prop(active_object, "friction_slider", slider=True, text="Friction")
            # row.prop(active_object.modifiers["SimplyCollision"].settings, "cloth_friction", slider=True, text="Friction") # GOOD CODE - Note that this changes the value somewhat since there's no calculation
            row.alert= True
            op = row.operator("object.simply_collision_manager", text="Remove Collision", icon="TRASH")
            op.mode = "REMOVE"
            row = box.row()
            row.prop(settings, "thickness_inner", text="Thickness Inner", slider=True)
            row.prop(settings, "thickness_outer", text="Thickness Outer", slider=True)
            # row = box.row()



    def ui_finish_panel(self, layout, context):
        # FINISHING
        # box = layout.box()
        # row = box.row()
        # row.scale_y = 1.6
        # row.active_default = True
        # row.prop(context.active_object, "sc_UI_FinishSettings", icon="CHECKBOX_HLT", text="Apply Cloth")
        # row = box.row()
        box = layout.box()
        row = box.row()
        row.label(text="Cloth Finalization", icon="MATCLOTH")

        # bpy.context.object.modifiers["SimplyCloth"].show_viewport = True

        # row.alert= True
        # row.operator("object.remove_cloth", text="Remove Cloth", icon="TRASH")
        # row = box.row()
        # # row.operator("scene.open_urls", text="Workflow Videos", icon="VIEW_CAMERA")
        row = box.row()
        row.scale_y = 1.6
        row.active_default = True
        op =row.operator("object.finish_cloth", text="Finish & Apply Cloth", icon_value=custom_icons["simply_cloth_helper_icon"].icon_id)
        op.mode = "APPLYCLOTH"
        row.active_default = False

        row = box.row()
        # row.scale_y = 2
        op = row.operator("object.finish_cloth", text="Apply & Sculpt", icon_value=custom_icons["icon_sculpt_mode"].icon_id)
        op.mode = "SCULPTCLOTHEXTRA"
        # row.emboss="NONE"

        # row = box.row()
        # op = row.operator("object.finish_cloth", text="Apply for Animation", icon="CHECKBOX_HLT")
        # op.mode = "APPLYMODIFIERONLY"	
    
    def ui_adjust_sculptPanel(self, layout, context):
        ########### SCULPT MODE ##########

        active_object = context.active_object
        box = layout.box()
        row = box.row(align=True)
        row.emboss="NONE"
        # row.template_icon_view(context.scene, "brushes", scale=5, scale_popup=5.0, show_labels=True)
        row = box.row()
        if active_object.brushForceFalloff == True:
            text = "Radial"
            fallOffIcon = custom_icons["brush_radial"].icon_id
        elif active_object.brushForceFalloff == False:
            fallOffIcon = custom_icons["brush_plane"].icon_id
            text = "Plane"
        row.label(text="Force Falloff")

        # row = box.row()
        row.emboss = "NONE"
        row.prop(active_object, "brushForceFalloff", text=text, icon_value=fallOffIcon)

        iconMaskBrush = custom_icons["sculpt_mask"].icon_id

        iconMaskInvert = custom_icons["sculpt_mask_invert"].icon_id
        iconMaskClean = custom_icons["sculpt_mask_clean"].icon_id
        row = box.row()

        row.prop(context.scene, "sc_sculpt_cloth_or_geometry", text="Cloth Simulation", icon="MOD_CLOTH")
        
        # brush = ""

        # textSculptMethod = "Cloth"
        # method = False
        # if "POSE" in context.scene.brushes:
        #     brush="Pose"
        #     method = True
        # else:
        #     if "BOUNDARY" in context.scene.brushes:
        #         brush="Boundary"
        #         method = True
        #     else:
        #         method = False
            # method = False


        # if context.scene.sc_sculpt_cloth_or_geometry == True:
        # 	textSculptMethod = "Cloth"
            
        # else:
        # 	textSculptMethod = "Geometry"
            
        # if method == True:
        #     row.prop(bpy.data.brushes[brush], "deform_target", text="")
        
        

        box = layout.box()
        row = box.row()
        row.label(text="Face Sets")
        row = box.row()
        row.scale_y = 1.6
        # bpy.ops.mesh.face_set_extract()
        row.active_default = True
        row.operator("mesh.face_set_extract", text="Extract Face Set", icon="MOD_SKIN")
        

        box = layout.box()
        row = box.row()
        row.label(text="Masking")
        row = box.row()
        op = row.operator("object.sculpt_brush_mask", text="Invert", icon_value=iconMaskInvert)
        op.mode = "INVERT"

        # row = box.row()
        op = row.operator("object.sculpt_brush_mask", text="Clean", icon_value=iconMaskClean)
        op.mode = "CLEANMASK"

        # if context.scene.brushes == 'MASK':
        #     row = box.row()
        #     row.label(text="", icon="MOD_SMOOTH")
        #     row.prop(active_object, "hardness_mask_slider", text="Hardness")

        box = layout.box()
        row = box.row()
        row.label(text="Resolution")
        row = box.row()
        op = row.operator("object.sculpt_subdivide", text="Subdivide", icon="ADD")
        op.mode="SUB"
        op = row.operator("object.sculpt_subdivide", text="Un-Subdivide", icon="REMOVE")
        op.mode="UNSUB"
        row = box.row()
        row.label(text="Remesher")
        # row = box.row()

        row.emboss="NONE"
        row.prop(active_object, "remesher_face_count", text="Faces")
        row = box.row()
                        #Topology
        row = box.row()
        row.label(icon="MOD_REMESH")		
        row.operator("object.quadriflow_remesh")
        # row.operator("object.remesh_cloth", text="Remesh", icon="MOD_REMESH")

        box = layout.box()
        row = box.row()
        row.label(text="Display")
        row = box.row()
        op = row.operator("object.sculpt_shade",text="Smooth",icon="ANTIALIASED")
        op.mode = "SMOOTH"
        op = row.operator("object.sculpt_shade",text="Flat",icon="ALIASED")
        op.mode = "FLAT"
        row = box.row()
        row.prop(active_object, "show_wireframes", text="Wireframe", icon="MESH_GRID")
        row = box.row()
        row.prop(active_object, "face_orientation", text="Check Face Orientation", icon="NORMALS_FACE")

        
        box = layout.box()
        row = box.row()
        row.scale_y= 2
        op = row.operator("object.create_cloth", text="Done", icon="CHECKMARK")
        op.mode = "CLOTHFROMSCULPT"

    def ui_no_object_selected(self, layout, context):
        box = layout.box()
        row = box.row()
        row.alert = True
        row.label(text="Select an Object to Start or add Dummy", icon="INFO")
        # row.alignment = "CENTER"
        row = box.row()
        row.scale_y= 1.6
        op = row.operator("object.scs_char_dummy", text="Add Dummy", icon="ARMATURE_DATA")
        op.mode = "ADD"
    def ui_adjust_pingroup(self, layout, context):
        box = layout.box()
        row = box.row()
        # row.label(text="Pin Group", icon="PINNED")
        row.label(text="Pin Group", icon_value = custom_icons["unpinned"].icon_id)
        row = box.row()
        # row.operator("object.live_pinning", text="Pin Group - Live Paint ", icon="BRUSH_DATA")
        row.operator("object.live_pinning", text="Pin Group - Live Paint ", icon_value = custom_icons["paint_add"].icon_id)
        row.alert= True
    
        row.operator("object.clear_simply_pin", text="Delete Pin", icon="TRASH")
        # row = box.row()
        if self.checkCounter(context):
            obj = context.active_object
            box = layout.box()
            row = box.row()
            row.label(text="Pin Layer", icon="DOCUMENTS")
            row.prop(context.active_object, "updatePinLayerOnFly", text="Live Update", icon="CHECKMARK")
            row = box.row()
            row.template_list("SLIDER_UL_List", "", obj, "vertex_slider", obj, "vertex_slider_index")

    def ui_adjust_sewing(self, layout, context):
        # SEWING UI
        active_object = context.active_object
        box = layout.box()					
        row = box.row()
        # row.label(text="Sewing", icon="DECORATE_LINKED")
        row.label(text="Sewing", icon_value = custom_icons["edge_vertices"].icon_id)
        row = box.row()
        if "SimplyCloth" in context.active_object.modifiers and context.mode == "OBJECT":
            # row = box.row()
            # row.prop(active_object, "cloth_sewing", text="Sewing",icon="RIGID_BODY")
            mod = active_object.modifiers["SimplyCloth"].settings

            # row.prop(mod, "use_sewing_springs", text="Sewing",icon="RIGID_BODY")
            row.prop(mod, "use_sewing_springs", text="Sewing",icon_value = custom_icons["dissolve_edges"].icon_id)
            # if active_object.cloth_sewing:
            # row.emboss = "NONE"
            row.prop(mod, "sewing_force_max", text="Force")
            row = box.row()
            # row.label(text=" ", icon="DRIVER_DISTANCE")
            row.emboss = "NORMAL"
            row.prop(active_object, "updateSewingWeldModifier", text="Merge Distance", icon_value = custom_icons["automerge_off"].icon_id)
            # row.emboss = "NONE"
            if "SimplyWeld" in active_object.modifiers:
                row.prop(active_object.modifiers["SimplyWeld"], "merge_threshold", text="")

    def ui_design_triangulate(self, layout, context):
        box = layout.box()
        row = box.row()
        # row.label(text="Simply Triangulation", icon="MOD_TRIANGULATE")
        row.label(text="Simply Triangulation", icon_value = custom_icons["hex_tri"].icon_id)
        if context.mode == "OBJECT":
            row.prop(context.scene, "sc_triangulation_level", text="Resolution")
        # row = box.row()
        
        # # OLD METHOD
        # row.prop(context.object, "sc_triangulation_quads", text="Quads")
        row = box.row()
        # row.scale_y = 2.0
        if context.mode == "EDIT_MESH":
            op = row.operator("object.simplycloth_triangulation", text="Kushiro Triangulation", icon="MOD_DECIM")
            op.mode = "TRIANGULATE"
        # op = row.operator("object.sc_dyntopo_triangulation", text="Rotate Faces", icon="CON_ROTLIKE")
        op = row.operator("object.sc_dyntopo_triangulation", text="Rotate Faces", icon_value = custom_icons["rotate_plus_90"].icon_id)
        op.mode = "ROTATE_SELECTION"
        # row.prop(context.object, "sc_cloth_rotate_faces", text="Rotate Face", icon="CON_ROTLIKE")
        row = box.row()
        # row.active_default = True
        # op = row.operator("object.sc_dyntopo_triangulation", text="Triangulate", icon="MOD_MULTIRES")
        op = row.operator("object.sc_dyntopo_triangulation", text="Triangulate", icon_value = custom_icons["mod_triangulate"].icon_id)
        op.mode = "DEFAULT"
        # op = row.operator("object.sc_dyntopo_triangulation", text="Dyntopo Tri", icon="MOD_TRIANGULATE")
        op = row.operator("object.sc_dyntopo_triangulation", text="Dyntopo Tri", icon_value = custom_icons["triangulate"].icon_id)
        op.mode = "DYNTOPO"
        
        # row.operator("object.remesh_simply_cloth_triangulation", text="Simply Triangulate", icon="MOD_MULTIRES")
        # if context.scene.sc_triangulation_level == 3:
        # 	row.alert=True





        # row.prop(context.object, "sc_triangulation_quads", text="Quads", icon="BLANK1")
        # row = box.row()
        # if context.object.sc_triangulation_resolution <= 1.00:
        # 	resolutionText="Low - Fast Speed"
        # if context.object.sc_triangulation_resolution <= 0.07:
        # 	resolutionText="Mid - Normal Speed" 
        # if context.object.sc_triangulation_resolution <= 0.04:
        # 	row.alert = True
        # 	resolutionText="High - Slow Speed"
        # row.label(text=str.upper(resolutionText), icon="INFO")
        



        # NEW METHOD (WIP)
        # alert = False
        # if context.object.sc_triangulation_resolution <= 1.00:
        # 	alert = False
        # 	resolutionText="Low Resolution - Fast"
        # if context.object.sc_triangulation_resolution <= 0.07:
        # 	resolutionText="Mid Resolution - Normal"
        # 	alert = False
        # if context.object.sc_triangulation_resolution <= 0.04:
        # 	alert = True
        # 	row.alert = True
        # 	resolutionText="High Resolution - Slow"
            
        # row.label(text="", icon="CON_SIZELIMIT")
        # row.alert = alert
        # row.prop(context.object, "sc_triangulation_resolution", text="Resolution", slider=True)

        # row = box.row()
        # row.scale_y = 1.3
        
        # row.active_default = True
        # row.label(text="", icon="MOD_TRIANGULATE")
        # # row.operator("object.sc_dyntopo_triangulation", text="Simply Triangulate", icon="MOD_MULTIRES")
        # row.operator("object.remesh_simply_cloth_triangulation", text="Simply Triangulate", icon="MOD_MULTIRES")
        # row = box.row()
        # row.alert = alert
        # row.alignment = "CENTER"
        # row.label(text=str.upper(resolutionText), icon="INFO")

    def ui_final_optimcloth(self, layout, context):
        box = layout.box()
        row = box.row()
        row.operator("object.optimize_cloth_sim", text="Optim Cloth (new)", icon="OBJECT_HIDDEN")

    def ui_createCloth_sculpt(self, layout, context):
                #UI SCULPT CLOT
        box = layout.box()
        row = box.row(align=True)
        # row.label(text="Sculpting", icon_value=sculptClothIcon)
        # row = box.row(align=True)
        # row.scale_y = 2
        op = row.operator("object.sculpt_brush", text="Sculpting Cloth Mode",icon_value=custom_icons["icon_sculpt_mode"].icon_id)
        op.mode = "SCULPTCLOTH"

    def ui_design_drawCloth(self, layout, context):

        # DRAWING FACE SETS
        box = layout.box()
        row = box.row()
        # row.label(text="Design Cloth", icon="DESKTOP")
        row.label(text="Design Cloth", icon_value = custom_icons["greasepencil"].icon_id)
        row = box.row()
        row.active_default = True
        # row.label(text="Cloth Sets", icon="UV_FACESEL")
        row.scale_y=1.9

        # op = row.operator("scene.sc_draw_cut_and_sew_pattern", text="Design Cut & Sew Pattern", icon="MATCLOTH")
        op = row.operator("scene.sc_draw_cut_and_sew_pattern", text="Design Cut & Sew Pattern", icon_value = custom_icons["mod_cloth"].icon_id)
        op.mode = "CREATE"
        row = box.row()

        row.scale_y = 1.6
        # row.operator("object.sc_draw_face_sets", text="Paint Cloth" ,icon="BRUSHES_ALL")
        row.operator("object.sc_draw_face_sets", text="Paint Cloth" ,icon_value = custom_icons["brush_data"].icon_id)



        # row.operator("object.sc_draw_face_sets", text="Mesh Manipulator" ,icon="FACE_MAPS")

        # DRAWING FACE SETS
        # box = layout.box()
        # row = box.row(align=True)
        # row.label(text="Skin Tight", icon="RESTRICT_SELECT_OFF")
        # op = row.operator("object.create_cloth", text="Simply Skin Tight", icon="MOD_SKIN")
        op = row.operator("object.create_cloth", text="Simply Skin Tight", icon_value = custom_icons["mod_shrinkwrap"].icon_id)
        op.mode ="SKINTIGHT_OBJECT"

    def ui_Design_fit_to_object(self, layout, context):

        
        box = layout.box()
        row = box.row()
        # row.label(text="Target Object", icon="PIVOT_ACTIVE")
        row.label(text="Target Object", icon_value = custom_icons["object_contents"].icon_id)
        row.prop(context.scene, "scs_fit_target_object", text="", icon_value = custom_icons["object_data"].icon_id )
        if context.scene.scs_fit_target_object:
            row = box.row()
            row.scale_y=1.6
            row.active_default = True
            row.operator("object.scs_fit_to_object", text="Cloth Fit to Target" ,icon="MOD_SHRINKWRAP")
            self.ui_Design_click_cloth(layout, context)

    def ui_Design_click_cloth(self, layout, context):
        box = layout.box()
        row = box.row()
        # row.label(text="", icon="SNAP_MIDPOINT")
        row.scale_y=1.6
        op = row.operator("object.scs_clickcreate", text="Click Point Cloth", icon="SNAP_MIDPOINT")
        op.mode = "START"

    def ui_noactive_cutsew(self, layout, context):
        box = layout.box()
        row = box.row(align=True)
        row.scale_y = 1.9
        op = row.operator("scene.sc_draw_cut_and_sew_pattern", text="Design Cut & Sew Pattern", icon="MATCLOTH")
        op.mode = "CREATE"
    def ui_adjust_attachpanel(self, layout, context):
        if context.active_object and context.mode == "OBJECT" and context.active_object.type == "MESH":
            if context.active_object.is_SimplyCloth == False and context.active_object.is_Attached == False:
                box = layout.box()
                row = box.row()
                # row.prop(bpy.data.objects[context.active_object.name], "name", text="Name")
                # row.label(text="Attaching", icon="PINNED")				
                # box = layout.box()
                # row = box.row(align=True)
                # if context.view_layer.objects.selected == bpy.data.objects[context.active_object.name]:

                # row = box.row(align=True)
                if len(bpy.context.view_layer.objects.selected) == 2 and context.active_object.is_Attached == False:
                    row.enabled = True
                else:
                    row.enabled = False
                # row.scale_y = 2x
                # row = box.row(align=True)
                row.active_default = True
                row.operator("object.attach_selected_to_cloth", text="Attach to Cloth", icon="FACESEL")

            # BIND ATTACHED
            elif context.active_object.is_Attached == True:
                box = layout.box()
                row = box.row()
                row.scale_y = 2
                row.alert=True
                op = row.operator("object.rebind_attached_object", text="Rebind", icon="UNPINNED")
                op.mode= "BIND"
                # op.mode = "BIND"
                row.operator("object.remove_attached_modifiers", text="", icon="TRASH")

    def ui_edit_cleanModifier(self, layout, context):
        if "SimplyCloth" in context.active_object.modifiers:
            box = layout.box()
            # row = box.row()
            # row.label(text="Clean Up", icon="BRUSH_DATA")
            row = box.row()
            row.alert = True
            
            # row.label(text="", icon="TRASH")
            row.operator("object.sc_clean_modifiers", text="Clean up Modifiers",icon="BRUSH_DATA")

    def ui_edit_bendSelect(self, layout, context):

        if context.active_object.data.total_vert_sel > 0:

            # BEND SELECTION
            box = layout.box()
            row = box.row()
            # # row.alignment= "CENTER"
            row.label(text="Bend Selection", icon="MOD_SIMPLEDEFORM")
            row = box.row()
            row.operator("object.sc_bend_selected", text="Bend")
            # row = box.row()
            # row.template_list("SLIDER_UL_List_Bend", "", active_object, "vertex_slider", active_object,"vertex_slider_index")

    def ui_edit_separateClothSelection(self, layout, context):

        if context.active_object.data.total_vert_sel > 0:

            # SEPARATE CLOTH BY SELECTION
            box = layout.box()
            row = box.row()
            createClothIcon = custom_icons["simply_cloth_helper_icon"].icon_id
            # row.alignment= "CENTER"
            row.label(text="Separate selecton to Cloth", icon="MOD_EXPLODE" )
            row.prop(context.active_object,"subdivideOnSeparation", text="Subdivide Selection", icon="SHORTDISPLAY")
            # row = box.row()
                        
            # row.prop(context.active_object,"triangulateOnSeparation", text="Triangulate Selection", icon="MOD_TRIANGULATE")
            row = box.row()
            row.scale_y = 1.6
            op = row.operator("object.create_cloth", text="Selection -> Cloth", icon_value=custom_icons["simply_cloth_helper_icon"].icon_id)
            op.mode = "SELECTCREATECLOTH"
    def ui_edit_subdiv(self, layout, context):
        
        if context.active_object.data.total_vert_sel > 0:

            # SEPARATE CLOTH BY SELECTION
            box = layout.box()
            # row = box.row()
            # row.label(text="Create Cloth first!", icon="ERROR")
            # op.mode = "CREATE_FROM_EDIT"
            row = box.row()
            row.scale_y = 1.6
            row.operator("mesh.subdivide", text="Subdivide", icon="ADD")
            row.operator("mesh.unsubdivide", text="Un-Subdivide", icon="REMOVE")

    def ui_edit_selectToCloth(self, layout, context):

        if context.active_object.data.total_vert_sel > 0:

            box = layout.box()
            row = box.row()
            row.scale_y = 1.6
            op = row.operator("object.create_cloth", text="Skin Tight", icon="MOD_SKIN")
            op.mode = "SKINTIGHT"
            # row = box.row()
            if context.active_object.scs_click_cloth:
                if "Mirror" in context.active_object.modifiers:
                    row = box.row()
                    row.scale_y = 1.6
                    row.prop(context.active_object.modifiers["Mirror"], "use_clip", text="Mirror Clipping", icon="AUTOMERGE_ON")
                    op = row.operator("object.scs_clickcreate", text="Finish Click Cloth", icon="MOD_EDGESPLIT")
                    op.mode = "FINISH"
                else:
                    row = box.row()
                    row.scale_y = 1.6
                    op = row.operator("object.scs_clickcreate", text="Finish Click Cloth", icon="MOD_EDGESPLIT")
                    op.mode = "FINISH"

    def ui_adjust_shrink(self, layout, context):
                # SHRINKWRAP	
        active_object = context.active_object
        if "SimplyShrink" in active_object.modifiers:
            box = layout.box()
            row = box.row()
            row.prop(active_object.modifiers["SimplyShrink"], "offset", text="Offset from Target")
        if "SimplyShrinkWrap" in active_object.modifiers:
            box = layout.box()
            row = box.row()
            
            # row.label(text="", icon="BLANK1")
            row.label(text="Shrink", icon="MOD_SHRINKWRAP")
            
            
            row.prop(active_object.modifiers["SimplyShrinkWrap"], "show_viewport", text="")
            row.prop(active_object.modifiers["SimplyShrinkWrap"], "show_render", text="")
            row = box.row()
            # row.label(text="", icon="BLANK1")
            # row.prop(active_object.modifiers["SimplySolidify"], "show_viewport", text="Solidify")

            if active_object.modifiers["SimplyShrinkWrap"].show_viewport == True:
                # box = layout.box()
                # row.label(icon="BLANK1")
                row.prop(active_object.modifiers["SimplyShrinkWrap"], "offset", text="Offset", icon="DRIVER_DISTANCE")

    def ui_edit_smooth(self, layout, context):
        #        # SMOOTH	
        active_object = context.active_object
        if "simplySmooth" in active_object.modifiers:
            box = layout.box()
            row = box.row()
            
            # row.label(text="", icon="BLANK1")
            # row.label(text="", icon="MOD_SHRINKWRAP")
            row.label(text="", icon_value= custom_icons["matfluid"].icon_id)
            # if active_object.modifiers["simplySmooth"].show_viewport == True:
                # box = layout.box()
                # row.label(icon="BLANK1")
            row.prop(active_object.modifiers["simplySmooth"], "iterations", text="Smoothing Intensity", icon="DRIVER_DISTANCE")
            
            row.prop(active_object.modifiers["simplySmooth"], "show_in_editmode", text="", icon_value = custom_icons["editmode_hlt"].icon_id)
            row.prop(active_object.modifiers["simplySmooth"], "show_viewport", text="")
            row.prop(active_object.modifiers["simplySmooth"], "show_render", text="")
            
            # row.prop(active_object.modifiers["SimplySolidify"], "show_viewport", text="Solidify")

                    
    def ui_edit_solidify(self, layout, context):
        active_object = context.active_object
        # SOLIDIFY	
        if "SimplySolidify" in active_object.modifiers and "SimplyCloth":
            box = layout.box()
            row = box.row()
            
            
            # row.label(text="", icon="BLANK1")
            # row.label(text="", icon="MOD_SOLIDIFY")
            row.label(text="", icon_value = custom_icons["mod_outline"].icon_id)
            if active_object.modifiers["SimplySolidify"].show_viewport == False:
                icon = custom_icons["disable"].icon_id
            elif active_object.modifiers["SimplySolidify"].show_viewport == True:
                icon = custom_icons["enable"].icon_id


            row.prop(active_object.modifiers["SimplySolidify"], "show_viewport", text="Thickness",icon_value= icon)
            row.prop(active_object.modifiers["SimplySolidify"], "show_render", text="")

            # row.prop(active_object.modifiers["SimplySolidify"], "show_viewport", text="Solidify")

            if active_object.modifiers["SimplySolidify"].show_viewport == True:
                row = box.row()
                
                row.prop(active_object.modifiers["SimplySolidify"], "show_in_editmode", text="", icon_value = custom_icons["editmode_hlt"].icon_id)
                # row.prop(active_object.modifiers["SimplySolidify"], "thickness", text="Thickness", icon="MOD_THICKNESS")
                row.prop(active_object.modifiers["SimplySolidify"], "thickness", text="Thickness")
                row.prop(active_object.modifiers["SimplySolidify"], "offset", text="Offset", icon="DRIVER_DISTANCE")
                row.prop(active_object.modifiers["SimplySolidify"], "show_on_cage", text="")
                # row.label(text="", icon="BLANK1")
                # box = layout.box()
                # row.label(icon="BLANK1")
                row = box.row()
                # row.label(text="", icon="BLANK1")
                # row.prop(active_object, "thicknessBeforeAfterCloth", text="First Solidify (slower)", icon="FILE_PARENT")
                row.prop(active_object, "thicknessBeforeAfterCloth", text="First Solidify (slower)", icon_value = custom_icons["file_parent"].icon_id)

    def ui_adjust_subdivision(self, layout, context):
                # SUBDIVISION MODIFIER OBJECT MODE
        active_object = context.active_object
        if "BaseSub" in context.active_object.modifiers:
            box = layout.box()
            row = box.row()
            row.label(text="Subdivision Modifier", icon="VIEW_PERSPECTIVE")
            row.label(icon="BLANK1")
            row.prop(active_object.modifiers["BaseSub"], "show_viewport", text="")
            row.prop(active_object.modifiers["BaseSub"], "show_render", text="")

            row = box.row()
            row.prop(active_object, "baseSub_level",text="Level *") # GOOD CODE - Added the asterisk to indicate that this is a one way control that affects multiple parameters

    def ui_sim_pressure(self, layout, context):
        
        # UI PRESSURE
        active_object = context.active_object
        # box = self.layout.box()					
        box = layout.box()
        row= box.row()
        row.label(text="", icon="GIZMO")
        row.prop(active_object, "pressure", icon="GIZMO")
        row.label(text="", icon="BLANK1")
    
        if active_object.modifiers["SimplyCloth"].settings.use_pressure == True:
            mod = active_object.modifiers["SimplyCloth"].settings
            if mod.use_pressure:
                # row.emboss="NONE"
                row.prop(active_object, "pressure_intensity_slider", text="Intensity")
                row = box.row()
                # row.emboss = "NONE"
                row.prop(active_object, "pressure_factor_slider", text="Factor")
                row = box.row()

            op = row.operator("object.pressure_assign_group", text="Inflate Live Paint", icon="BRUSH_DATA")
            op.mode = "PAINT"
            # row.label(icon="BLANK1")
            row.alert= True
            op = row.operator("object.pressure_assign_group", text="", icon="TRASH")
            op.mode = "REMOVE"
            
    def ui_adjust_wind(self, layout, context):
        if "Wind" not in bpy.data.objects:
            if context.mode == "OBJECT":
                box = layout.box()
                row = box.row()
                # row.alignment = "CENTER"
                row.label(text="Wind Fx", icon ="SHADERFX")
                row = box.row()
                # row.scale_y = 2.0
                # row.label(text="", icon="BLANK1")
                row.operator("scene.sc_add_wind", text="Add Wind Fx", icon ="FORCE_WIND")
        # 	row = box.row()
        if "Wind" in bpy.data.objects:
            box = layout.box()
            row = box.row()
            row.label(text="Wind", icon="FORCE_WIND")
            row.alert= True
            row.operator("scene.remove_wind", text="", icon="TRASH")
            row = box.row()
            row.prop(context.scene, "sc_wind_slider", text="Strength *")
            row.prop(context.scene, "sc_wind_factor", text="Intensity *")

    def ui_adjust_spring(self, layout, context):
        active_object = context.active_object
        box = layout.box()					
        row = box.row()
        row.label(text="Spring", icon="MOD_SCREW")
        row = box.row()
        mod = context.active_object.modifiers["SimplyCloth"].settings
        # row = box.row()
        row.prop(active_object, "internal_spring",icon="MOD_SCREW")
        mod = context.active_object.modifiers["SimplyCloth"].settings
        if mod.use_internal_springs:
            # row.emboss="NONE"
            row.prop(active_object.modifiers["SimplyCloth"].settings, "internal_spring_max_length", text="Intensity")
        # row = box.row()

    def ui_adjust_density(self, layout, context):
        active_object = context.active_object
        if "SimplyDensity" in context.active_object.modifiers:
            box = layout.box()					
            row = box.row()
            row.label(text="Density Paint", icon="BRUSH_DATA")
            row.label(icon="BLANK1")
            row.prop(active_object.modifiers["SimplyDensity"], "show_viewport", text="")
            row.prop(active_object.modifiers["SimplyDensity"], "show_render", text="")
            row = box.row()
            row.prop(active_object, "density_paint", text="Density Paint", icon="STICKY_UVS_LOC")

            if active_object.density_paint:
                op = row.operator("object.density_paint", text="Paint", icon="BRUSH_DATA")
                op.mode = "FROM_OBJECT"
                row = box.row()
                row.prop(active_object.modifiers["SimplyDensity"], "ratio", text="Ratio")
                row.prop(active_object.modifiers["SimplyDensity"], "invert_vertex_group", text="Invert Density", icon="ARROW_LEFTRIGHT")

    def ui_edit_extras(self, layout, context):
        box = layout.box()
        row = box.row(align=True)
        # row.alignment= "CENTER"
        row.label(text="EXTRAS", icon="STICKY_UVS_LOC")
        # row = box.row()
        # row.label(text="", icon="BLANK1")
        # row.scale_y = 2.0
        # op = row.operator("object.density_paint", text="Paint Density", icon="BRUSH_DATA")
        # op.mode = "FROM_EDIT"

        # if active_object.density_paint:
        # 	icon = "CHECKBOX_HLT"
        # else:
        # 	icon = "CHECKBOX_DEHLT"
        # row.prop(active_object, "density_paint", text="Show", icon=icon)

        # STRENGHTEN VERTEX GROUP
        row = box.row()
        # row.alignment= "CENTER"
        # row.label(text="", icon="BLANK1")
        # row = box.row()
        # row.scale_y = 2.0
        row.emboss = "NORMAL"
        op = row.operator("object.strengthen_selection", text="Strengthen", icon="PLUS")
        op.mode = "ADD"
        op = row.operator("object.strengthen_selection", text="Remove", icon="TRASH")
        op.mode = "CLEAR"	

        # SHRINK VERTEX GROUP
        # box = layout.box()
        row = box.row()
        # row.alignment="CENTER"
        # row.scale_y = 2.0
        # row.label(text="", icon="BLANK1")
        # row = box.row()
        row.emboss = "NORMAL"
        op = row.operator("object.shrink_selection", text="Shrink", icon="PLUS")
        op.mode = "ADD"
        op = row.operator("object.shrink_selection", text="Remove", icon="TRASH")
        op.mode = "CLEAR"

        # PRESSURE RELEASE PAINT
        # box = layout.box()
        row = box.row()
        # row.scale_y = 2.0
        # row.label(text="", icon="BLANK1")
        op.mode = "REMOVE"
        row.emboss = "NORMAL"
        op = row.operator("object.pressure_assign_group", text="Paint Inflate", icon="BRUSH_DATA")
        op.mode = "PAINT"
        # row.label(text="",icon="BLANK1")
        op = row.operator("object.pressure_assign_group", text="Inflate ", icon="TRASH")
        op.mode = "ASSIGN"
        row = box.row()
        row.alert= True
        # row.label(text="", icon="BLANK1")
        op = row.operator("object.pressure_assign_group", text="Remove Inflate", icon="TRASH")
        # row.alert= False

    def ui_edit_pingroups(self, layout, context):
        active_object = context.active_object
        box = layout.box()
        row = box.row()
        # row.alignment = "CENTER"
        
        # row.alignment ="RIGHT"
        # row = box.row()

        if "SimplyCloth" in active_object.modifiers:
            row.label(text="Pin Layer System", icon="DOCUMENTS")
            if self.checkCounter(context):
                row.prop(active_object, "updatePinLayerOnFly", text="Live Update", icon="CHECKMARK")
            obj = context.active_object
            op = row.operator("object.create_pin_layers", text="", icon="FILE_REFRESH")
            op.mode = "MERGEWEIGHTS"
            layout = self.layout


            row = box.row()
            vertex_slider = context.active_object.vertex_slider
            row.scale_y = 1.3
            # row.label(icon="PLUS", text="")
            # row.label(text="", icon="BLANK1")
            row.active_default = True
            row.operator("object.add_pin_operator", icon="ADD", text="Pin Selection as Layer")
            row.scale_y = 1.6
            row.active_default = False
            # row.label(text="", )
            row.operator("object.live_pinning", text="", icon="BRUSH_DATA")
            row.alert= True

            row.operator("object.clear_simply_pin", text="", icon="TRASH")
            if self.checkCounter(context):      
                row = box.row()
                # row.label(text="", icon="BLANK1")
                # row.label(text="", icon="BLANK1")
                row.template_list("SLIDER_UL_List", "", active_object, "vertex_slider", active_object,
                                "vertex_slider_index")

        else:
            row.enabled = False
            row.label(text="Pin Layer System", icon="DOCUMENTS")
            row = box.row()
            row.scale_y = 2.0
            row.alert = True
            row.alignment = "CENTER"
            row.label(text="", icon="ERROR")
            row.label(text="First create Simply Cloth for this object")
            row.label(text="", icon="ERROR")

        # row = box.row()

    def ui_edit_sewing(self, layout, context):
        
        active_object = context.active_object
        box = layout.box()
        row = box.row(align=True)
        row.label(text="Sewing", icon="RIGID_BODY")
        # row.alignment = "CENTER"
        selectedEdges = context.active_object.data.total_edge_sel

        # row = box.row()
        # row.scale_y = 2.0
        selectedEdgesText= "selected "+str(selectedEdges)
        neededEdges= str(selectedEdges*2)+" needed"
        row.emboss = "NONE_OR_STATUS"
        if selectedEdges > 0 and selectedEdges is not None:
            row.label(text=selectedEdgesText+"/ "+neededEdges)
        row = box.row()

        row.prop(active_object, "sc_add_sewing_to_shrink", text="shrinking to Sew", icon="FULLSCREEN_EXIT")
        row.alert= False
        row = box.row()
        row.active_default = True
        row.scale_y = 1.3
        # op = row.label(text="", icon="BLANK1")
        op = row.operator("object.create_sewing", text="Sew", icon="DECORATE_LIBRARY_OVERRIDE")
        op.mode = "CREATE_SEWING"
        row.active_default = False
        # op = row.label(text="", icon="BLANK1")
        row.operator("object.scs_sew_similar", text="Auto Select", icon="ZOOM_SELECTED")

        # row.active_default = False
        # row = box.row()
        # row.alert= True
        # op = row.operator("object.create_sewing", text="Remove Sewings", icon="TRASH")
        # op.mode = "REMOVE_SEWING"
        # if "SimplyCloth" in context.active_object.modifiers:

        
        # if "SimplyCloth" in context.active_object.modifiers:
        row = box.row()
        # row = box.row()
        # row.label(text="", icon ="BLANK1")
        row.alert = True
        row.operator("object.scs_delete_selection_add_sew", text="Unitard Sew", icon="HAND")
        if "SimplyCloth" not in context.active_object.modifiers:
            op = row.operator("object.sc_auto_sewing", text="Auto Sewing (use after apply cloth)", icon="HAND")
            op.mode = "AUTO_SEWING"
        # row = box.row()
        # row.operator("object.sc_convert_to_sew", text="Cut and Sew (wip)", icon="HAND")
        
        
        box = layout.box()
        row = box.row()
        row.label(text="Edit Sewing", icon="LINK_BLEND")
        row.prop(bpy.context.active_object, "fillHoles_slider", text="Fill holes")

        row = box.row()
        row.scale_y = 1.6
        row.active_default = True	
        op = row.operator("object.additional_sewing_operator",text="Sew - Close Selection", icon="LINK_BLEND")
        op = "CLOSE SELECTION"
        row.active_default = False
        op = row.operator("mesh.bridge_edge_loops",text="Sew - Bridge Edge Loops", icon="SNAP_EDGE")
        op = "use_merge=True, merge_factor=1, twist_offset=0, number_cuts=0, smoothness=1, profile_shape_factor=0"
        row = box.row()
        row.scale_y = 1.6
        op = row.operator("object.create_sewing", text="Select Mesh Bounds", icon="MOD_MESHDEFORM")
        op.mode = "SELECT_BOUNDS"
        row = box.row()
        op = row.operator("object.create_sewing", text="Select Sewing", icon="RESTRICT_SELECT_OFF")
        op.mode = "SELECT_SEWING"
        # row = box.row()
        row.alert= True
        op = row.operator("object.create_sewing", text="Remove Sewings", icon="TRASH")
        op.mode = "REMOVE_SEWING"
    def ui_edit_design_selection(self, layout, context):
        # ROTATE FACES
        box = layout.box()
        row = box.row()
        row.label(text="Edit Selection", icon="EDITMODE_HLT")
        row.operator("mesh.remove_doubles",text="Merge by Distance", icon="AUTOMERGE_ON")
        # op = row.operator("object.sc_dyntopo_triangulation", text="Rotate Faces", icon="CON_ROTLIKE")
        # op.mode = "ROTATE_SELECTION"
        
        row = box.row()
        op = row.operator("object.create_sewing", text="Select Mesh Bounds", icon="MOD_MESHDEFORM")
        op.mode = "SELECT_BOUNDS"
        row.operator("object.sc_autoextrude_edges", text="Extrude Selected Edges", icon="MOD_EDGESPLIT")
        row = box.row()

        # op = row.operator("object.create_sewing", text="Select Sewing", icon="MOD_SIMPLIFY")
        # op.mode = "SELECT_SEWING"

        # row = box.row()

        op = row.operator("mesh.fill_grid",text="Grid Fill", icon="MESH_GRID")
        op = "span=9, offset=0, use_interp_simple=True"
        # row = box.row()

    def ui_edit_draw_cutsew_pattern(self, layout, context):
        # DRAW CUT AND SEWING PATTERN
                        # DRAW CUT AND SEWING PATTERN
        box = layout.box()
        row = box.row()
        row.prop(bpy.data.objects[context.active_object.name], "name", text="Name")
                    # bpy.ops.gpencil.editmode_toggle()
        box = layout.box()
        row = box.row(align=True)
        row.label(text="Drawing Pattern", icon="GREASEPENCIL")
        # row.label(text="Work in Progress", icon="ERROR")
        # row = box.row()
        row = box.row()
        # row.scale_y = 2.0
        op = row.operator("scene.sc_draw_cut_and_sew_pattern", text="Draw Cut & Sew Pattern", icon="MATCLOTH")
        # op = row.operator("scene.sc_draw_cut_and_sew_pattern", text="Draw Cut & Sew Pattern", icon="MATCLOTH")
        op.mode = "FINISH"

    def ui_edit_extrude_edge(self, layout, context):
                # EXTRUDE EDGE BY SELECTION
        box = layout.box()
        row = box.row()
        # row.alert = True
        # row.label(text="EXTRUDE - EXPERIMENTAL", icon="ERROR")

        row.operator("object.sc_autoextrude_edges", text="Extrude Selected Edges")
                
    def ui_edit_autosewing(self, layout, context):
        # TODO Auto Sewing
        box = layout.box()
        row = box.row()
        op = row.label(text="", icon="BLANK1")
        op = row.operator("object.sc_auto_sewing", text="AUTO SEW", icon="HAND")
        op.mode = "AUTO_SEWING"
        row = box.row()

        # row.active_default =True
        # op = row.operator("object.create_sewing", text="Sew", icon="DECORATE_LIBRARY_OVERRIDE")
        # op.mode = "CREATE_SEWING"
        # # row = box.row()
        # row.active_default =False
        # row.alert= True
        # op = row.operator("object.create_sewing", text="Remove Sewing", icon="TRASH")
        # op.mode = "REMOVE_SEWING"
        # row = box.row()

        row.alert=True
        row.scale_y = 2.0
        op = row.operator("object.sc_auto_sewing", text="AUTO SEW (EXPERIMENTAL) ", icon="HAND")
        op.mode = "AUTO_SEWING"

        row = box.row()
        op = row.operator("object.create_sewing", text="Select Mesh Bounds", icon="MOD_MESHDEFORM")
        op.mode = "SELECT_BOUNDS"

    def ui_paint_pingroups(self, layout, context):
        active_object = context.active_object
        # if self.checkCounter(context):
        box = layout.box()
        row = box.row()

        row.label(text="Pin Layer", icon="DOCUMENTS")
        row = box.row()
        row.template_list("SLIDER_UL_List", "", active_object, "vertex_slider", active_object,"vertex_slider_index")
        row = box.row()
        row.scale_y = 1.6
        row.operator("object.editmode_toggle", text="Edit Mode", icon="EDITMODE_HLT")
        box = layout.box()
        row = box.row()
        row.scale_y = 1.3
        row.operator("paint.weight_paint_toggle", text="Object Mode", icon="SCREEN_BACK")

    def ui_enhance_geoNodes(self, layout, context):
                            # GEO_SEWING
        # box = layout.box()
        if context.active_object.sc_geoNodes_simplycloth_modifier_name in context.active_object.modifiers:
            Simply_GeoNodes_Modifier = context.active_object.modifiers[context.active_object.sc_geoNodes_simplycloth_modifier_name]
            Simply_GeoNodes = context.active_object.modifiers[context.active_object.sc_geoNodes_simplycloth_modifier_name].node_group.nodes
        
        # if "SimplyCloth" not in context.active_object.modifiers:

        #     # UI SIMPLY GEOMETRY NODES
        #     if context.active_object.sc_geoNodes_simplycloth_modifier_name == "":
        #         box = layout.box()
        #         row = box.row(align=True)
        #         # row.label(text="Cloth Enhancement", icon="GEOMETRY_NODES")
        #         row.scale_y = 1.3
        #         row.operator("object.sc_setup_simply_geo_nodes", text="Cloth Enhancements", icon="PLUS")

        # if "SimplyCloth_GeoNodes_" in context.active_object.modifiers:
        #     row.prop(context.active_object, "sc_UI_Enhance", text="Cloth Enhancement" ,icon="GEOMETRY_NODES")
            # box = layout.box()
            # row.label()
            # row.label(text="Cloth Enhancement", icon="GEOMETRY_NODES")

            # else:
            #     row.prop(context.active_object, "sc_UI_Enhance", text="Cloth Enhancement" ,icon="HIDE_OFF")
        # UI SIMPLY GEOMETRY NODES
        if context.active_object.sc_geoNodes_simplycloth_modifier_name == "":
            box = layout.box()
            row = box.row()
            # row.label(text="Enhancement", icon="GEOMETRY_NODES")
            row.scale_y = 1.3
            # row.operator("object.sc_setup_simply_geo_nodes", text="Cloth Enhancements", icon="PLUS")
            row.operator("object.sc_setup_simply_geo_nodes", text="Cloth Enhancements", icon_value = custom_icons["node_glare"].icon_id)
            if context.active_object.sc_geoNodes_simplycloth_modifier_name not in context.active_object.modifiers:

                row.alert= True
                row.operator("object.sc_reset_simply_geo", text="", icon="RECOVER_LAST")
            # row.label(text="", icon="ERROR")        
        else:
            box = layout.box()
            row = box.row()
            row.alert= True
            row.operator("object.sc_reset_simply_geo", text="Reset Enhance Settings", icon="RECOVER_LAST")
        if context.active_object.sc_geoNodes_simplycloth_modifier_name in context.active_object.modifiers:

            box = layout.box()
            row = box.row(align=True)
            row.label(text="Cloth Enhancement", icon="GEOMETRY_NODES")
            # row = box.row()
            row.alert=True
            row.operator("object.sc_reset_simply_geo", text="Remove Enhancement", icon="TRASH")
            row = box.row()
            # row.active_default = True
            row.scale_y = 1.6
            # row.label(text="", icon="WORLD_DATA")
            if context.active_object.sc_geoNodes_simplycloth_modifier_name in context.active_object.modifiers:
                row.prop(context.active_object.modifiers[context.active_object.sc_geoNodes_simplycloth_modifier_name], "show_viewport", text="")
            # bpy.context.object.modifiers["SimplyCloth_GeoNodes_simply_cloth_001"].show_viewport = False

        
            if "SC_Global_Intensity" in Simply_GeoNodes:
                row.prop(Simply_GeoNodes["SC_Global_Intensity"].outputs[0], "default_value", text="Global Intensity", invert_checkbox=True)
            if context.active_object.sc_geoNodes_simplycloth_modifier_name in context.active_object.modifiers:
                row.prop(context.active_object.modifiers[context.active_object.sc_geoNodes_simplycloth_modifier_name], "show_render", text="")
            row = box.row()
            # row.label(text="Sewing Group")
            op = row.operator("object.sc_vertexgroup_geonodes_edit", text="", icon="WPAINT_HLT")
            if context.mode == "EDIT_MESH":
                op = row.operator("object.sc_assign_to_vertex_group", text="", icon="PLUS")
            op.vertexGroup = "SEWING"
            row.prop(Simply_GeoNodes["SC_Sewing_Intensity"].outputs[0], "default_value", text="Sewing Intensity", invert_checkbox=True, icon="MOD_MASK")
            row.prop(Simply_GeoNodes["SC_Sewing_Invert"], "mute", text="", invert_checkbox=True, icon="IMAGE_ALPHA")
            row = box.row()
            # row.label(text="Pull Group")
            op = row.operator("object.sc_vertexgroup_geonodes_edit", text="", icon="WPAINT_HLT")
            if context.mode == "EDIT_MESH":
                op = row.operator("object.sc_assign_to_vertex_group", text="", icon="PLUS")
            op.vertexGroup = "PULL"
            row.prop(Simply_GeoNodes["SC_Pull_Intensity"].outputs[0], "default_value", text="Pull Intensity", invert_checkbox=True, icon="MOD_MASK")
            row.prop(Simply_GeoNodes["SC_Pull_Invert"], "mute", text="", invert_checkbox=True, icon="IMAGE_ALPHA")
            row = box.row()
            # row.label(text="Push Group")
            op = row.operator("object.sc_vertexgroup_geonodes_edit", text="", icon="WPAINT_HLT")
            if context.mode == "EDIT_MESH":
                op = row.operator("object.sc_assign_to_vertex_group", text="", icon="PLUS")
            op.vertexGroup = "PUSH"
            row.prop(Simply_GeoNodes["SC_Push_Intensity"].outputs[0], "default_value", text="Push Intensity", invert_checkbox=True, icon="MOD_MASK")
            row.prop(Simply_GeoNodes["SC_Push_Invert"], "mute", text="", invert_checkbox=True, icon="IMAGE_ALPHA")
            row = box.row()
        # row.label(text="Push Group")
            op = row.operator("object.sc_vertexgroup_geonodes_edit", text="", icon="WPAINT_HLT")
            if context.mode == "EDIT_MESH":
                op = row.operator("object.sc_assign_to_vertex_group", text="", icon="PLUS")
            op.vertexGroup = "DETAIL"
            row.prop(Simply_GeoNodes["SC_Detail_Intensity"].outputs[0], "default_value", text="Detail Intensity", invert_checkbox=True, icon="MOD_MASK")
            row.prop(Simply_GeoNodes["SC_Detail_Contrast"].outputs[0], "default_value", text="Contrast", invert_checkbox=True, icon="MOD_MASK")
            row.prop(Simply_GeoNodes["SC_Detail_Invert"], "mute", text="", invert_checkbox=True, icon="IMAGE_ALPHA")
            row = box.row()
            row.prop(Simply_GeoNodes["SC_Cloth_Triangulate"], "mute", text="Triangulated Topology", invert_checkbox=True, icon="MOD_TRIANGULATE")
            # row = box.row()
            
            box = layout.box()
            row = box.row()
            row.scale_y = 1.6
            # row.label(text="Bounding Edges", icon="MOD_EDGESPLIT")
            
    # 
            blenderVersion = bpy.app.version

            if blenderVersion[1] == 0:
                row.prop(Simply_GeoNodes["SC_Switch_Edge_Frazzels"].inputs[1], "default_value", text="Bounding Edges", invert_checkbox=False, icon="MOD_EDGESPLIT")
                if Simply_GeoNodes["SC_Switch_Edge_Frazzels"].inputs[1].default_value == True:
                    row = box.row()
                    row.prop(Simply_GeoNodes["SC_EdgeDetail_Offset"].outputs[0], "default_value", text="Offset", invert_checkbox=True, icon="MOD_MASK")
                    row.prop(Simply_GeoNodes["SC_Edges_Group_Blur_Bounds"].inputs[4], "default_value", text="Blur", invert_checkbox=False, icon="BRUSHES_ALL")
                    row = box.row()
            elif blenderVersion[1] == 1:
                row.prop(Simply_GeoNodes["SC_Switch_Edge_Frazzels"].inputs[0], "default_value", text="Bounding Edges", invert_checkbox=False, icon="MOD_EDGESPLIT")
                if Simply_GeoNodes["SC_Switch_Edge_Frazzels"].inputs[0].default_value == True:
                    row = box.row()
                    row.prop(Simply_GeoNodes["SC_EdgeDetail_Offset"].outputs[0], "default_value", text="Offset", invert_checkbox=True, icon="MOD_MASK")
                    row.prop(Simply_GeoNodes["SC_Edges_Group_Blur_Bounds"].inputs[1], "default_value", text="Blur", invert_checkbox=False, icon="BRUSHES_ALL")
                    row = box.row()


                # row.label(text="Offset")
                # row = box.row()


                # row = box.row()

            # OFFSET
                row.prop(Simply_GeoNodes["SC_EdgeDetail_Random"], "mute", text="Randomize", invert_checkbox=True, icon="PARTICLE_TIP")
                row.prop(Simply_GeoNodes["SC_Bound_Vector_Add_Gravity"].outputs[0], "default_value", text="Gravity", invert_checkbox=True, icon="MOD_MASK")
                # row = box.row()

                # bpy.data.node_groups["SimplyCloth_GeoNodes_Male_Basics_T-Shirt"].nodes["SC_Bound_Vector_Add_Gravity"].vector[2] = 1

                # bpy.data.node_groups["SimplyCloth_GeoNodes_Plane"].nodes["SC_Bound_Vector_Add_Gravity"].vector[2] = 5.1

                # row.prop(Simply_GeoNodes["SC_Bound_Vector_Add_Gravity"].vector[2], text="Offset", invert_checkbox=True, icon="MOD_MASK", index=2)
                # row = box.row()

                # row.label(text="Edges")
                
                row = box.row()


                row.label(text="Dissolve Edges", icon="MOD_REMESH")	
                row = box.row()
                # RANDOM SELECT
                row.prop(Simply_GeoNodes["SC_EdgeSwitch_ON_OFF"].inputs[0], "default_value", text="Random Edges Select", invert_checkbox=False, icon="STICKY_UVS_DISABLE")
                if Simply_GeoNodes["SC_EdgeSwitch_ON_OFF"].inputs[0].default_value == True:
                    # row.prop(Simply_GeoNodes["SC_Edge_Random_Selection_Intensity"].outputs[0], "default_value", text="Intensity", invert_checkbox=False, icon="MOD_MASK")
                    #EMISSION COLOR RAMP
                    row = box.row()
                    randomSelect_ColorRamp = Simply_GeoNodes["SC_randomSelect_ColorRamp"]
                    col = box.column(align=True)
                    col.template_color_ramp(randomSelect_ColorRamp, "color_ramp", expand= True)   
                    
                # row.prop(Simply_GeoNodes["SC_EdgeSwitch_ON_OFF"].inputs[0], "default_value", text="Random Select", invert_checkbox=False, icon="MOD_MASK")
                row = box.row()
                
                row.prop(Simply_GeoNodes["SC_Edge_Switch_Object_Dissolve"].inputs[0], "default_value", text="Dissolve by Object",  icon="OBJECT_DATAMODE")
                
                
                
                # row = box.row()

                if Simply_GeoNodes["SC_Edge_Switch_Object_Dissolve"].inputs[0].default_value == True:
                    blenderVersion = bpy.app.version

                    if blenderVersion[1] == 0:
                        row.prop(Simply_GeoNodes["SC_Edges_Group_Blur_Object"].inputs[4], "default_value", text="Blur", invert_checkbox=False, icon="BRUSHES_ALL")
                    elif blenderVersion[1] == 1:
                        row.prop(Simply_GeoNodes["SC_Edges_Group_Blur_Object"].inputs[1], "default_value", text="Blur", invert_checkbox=False, icon="BRUSHES_ALL")
                    row = box.row()
                    row.prop(Simply_GeoNodes["SC_Dissolve_Object"].inputs[0], "default_value", text="",  icon="MOD_EDGESPLIT")
                    # row = box.row()
                    
                # row.prop(Simply_GeoNodes["SC_Detail_Invert"], "mute", text="", invert_checkbox=True, icon="IMAGE_ALPHA")
                # row.prop(Simply_GeoNodes["SC_Detail_Contrast"].outputs[0], "default_value", text="Contrast", invert_checkbox=True, icon="MOD_MASK")
                

                
                row = box.row()
                row.prop(Simply_GeoNodes["SC_Edge_Switch_Mix_Vertex_Bounds"].inputs[0], "default_value", text="Custom Edges", invert_checkbox=False, icon="BRUSHES_ALL")
                # row = box.row()
                # row.prop(Simply_GeoNodes["SC_Edge_Switch_VertexGroup"].inputs[0], "default_value", text="Custom Edge Group", invert_checkbox=False, icon="BRUSHES_ALL")
                if Simply_GeoNodes["SC_Edge_Switch_Mix_Vertex_Bounds"].inputs[0].default_value == True:
                    blenderVersion = bpy.app.version
                    if blenderVersion[1] == 0:
                        row.prop(Simply_GeoNodes["SC_Edges_Group_Blur_Custom"].inputs[4], "default_value", text="Blur", invert_checkbox=False, icon="BRUSHES_ALL")
                    elif blenderVersion[1] == 1:
                        row.prop(Simply_GeoNodes["SC_Edges_Group_Blur_Custom"].inputs[1], "default_value", text="Blur", invert_checkbox=False, icon="BRUSHES_ALL")
                    row = box.row()
                    op = row.operator("object.sc_vertexgroup_geonodes_edit", text="Paint ", icon="WPAINT_HLT")
                    op.vertexGroup = "EDGE"
                    
                    # row.prop(Simply_GeoNodes["SC_Edges_Group_Blur"].inputs[4], "default_value", text="Blur", invert_checkbox=False, icon="BRUSHES_ALL")
                # if Simply_GeoNodes["SC_Edge_Switch_VertexGroup"].inputs[0].default_value == True:
                # 	row.prop(Simply_GeoNodes["SC_Edge_Switch_Mix_Vertex_Bounds"].inputs[0], "default_value", text="Mix", invert_checkbox=False, icon="MOD_MULTIRES")
            box = layout.box()
            row = box.row()
            row.label(text="Wrinkles", icon="MOD_NOISE")
            row.prop(Simply_GeoNodes["SC_Wrinkle_Scale"].outputs[0], "default_value", text="Scale", invert_checkbox=True, icon="MOD_MASK")
            row.prop(Simply_GeoNodes["SC_Wrinkles_Rotate_Switch"], "invert", text="", invert_checkbox=True, icon="DRIVER_ROTATIONAL_DIFFERENCE")
            
            # row.label(text="Wrinkles")
            row = box.row()

            row.prop(Simply_GeoNodes["SC_Wrinkle_Invert"], "mute", text="", invert_checkbox=True, icon="IMAGE_ALPHA")
            row.prop(Simply_GeoNodes["SC_Wrinkle_Intensity"].outputs[0], "default_value", text="Intensity", invert_checkbox=True, icon="MOD_MASK")
            row.prop(Simply_GeoNodes["SC_Wrinkle_Distortion"].outputs[0], "default_value", text="Wrinkels", invert_checkbox=True, icon="MOD_MASK")
            row = box.row()
            wrinkle_ColorRamp = Simply_GeoNodes["SC_Wrinkle_ColorRamp"]
            col = box.column(align=True)
            col.template_color_ramp(wrinkle_ColorRamp, "color_ramp", expand= True)   
            # row.prop(Simply_GeoNodes["SC_Wrinkle_Contrast"].outputs[0], "default_value", text="Contrast", invert_checkbox=True, icon="MOD_MASK")
            row = box.row()
            row.prop(Simply_GeoNodes["SC_Wrinkle_Animation_Switch"].inputs[0], "default_value", text="Animate Wrinkle", invert_checkbox=False, icon="MOD_MASK")
            row.prop(Simply_GeoNodes["SC_Wrinkle_Animation_Speed"].outputs[0], "default_value", text="Speed", invert_checkbox=True, icon="MOD_MASK")
            

    def ui_adjust_drag_cloth(self, layout, context):
        # TODO
        # DRAG
        box = layout.box()
        row = box.row()
        row.emboss = "NONE"
        row.alert=True
        row.label(text="Drag Cloth ( HIGHLY work in progess)", icon="VIEW_PAN")
        row = box.row()
        row.scale_y = 1.6
        row.emboss = "NORMAL"
        row.alert=True
        row.operator("scene.sc_drag_cloth", text="Drag", icon="MOD_WARP")
        
        # row.prop(context.active_object, "sc_cloth_drag_info", text="Click on cloth for Drag", icon="INFO")
        # if context.active_object.sc_cloth_drag_info:
        # box = layout.box()
        row = box.row(align=True)
        row.alert= True
        
        row.label(text="Information", icon="INFO")
        row.label(text="", icon="EVENT_ESC")
        row.label(text="End Drag Mode")
        row = box.row(align=True)
        row.label(text="", icon="MOUSE_LMB")
        row.label(text="click |  Drag")
        # row = box.row(align=True)
        row.label(text="", icon="MOUSE_LMB_DRAG") 
        row.label(text="release | Release Drag")
        row = box.row(align=True)
        row.label(text="", icon="EVENT_CTRL")
        row.label(text="↑ | + Intensity", icon="MOUSE_MMB")
        
        row.label(text="", icon="EVENT_CTRL")
        row.label(text="↓ | - Intensity", icon="MOUSE_MMB")
        
        row = box.row(align=True)
        row.alignment = "RIGHT"
    
    def ui_finish_info_createcloth(self, layout, context):
        box = layout.box()
        row = box.row()
        row.emboss = "NONE"
        row.alert=True
        row.alignment ="CENTER"
        row.label(text="Create Cloth in Simulation", icon="INFO")

    def ui_curve_edit(self, layout, context):
        box = layout.box()
        if "Mirror" in context.active_object.modifiers:
            row = box.row(align=True)
            row.prop(context.active_object.modifiers["Mirror"] ,"use_clip", text="Clipping", icon="AUTOMERGE_ON")
            row.prop(context.active_object.modifiers["Mirror"] ,"use_axis", index=0, text="X", icon_value=custom_icons["mirror_x"].icon_id)
            row.prop(context.active_object.modifiers["Mirror"] ,"use_axis", index=1, text="Y", icon_value=custom_icons["mirror_y"].icon_id)
            row.prop(context.active_object.modifiers["Mirror"] ,"show_viewport",  text="")
            row.prop(context.active_object.data.splines[0] ,"use_cyclic_u",  text="", icon="CURVE_NCIRCLE")

        row = box.row()
        row.scale_y = 1.6
        op = row.operator("curve.subdivide", text="Subdivide", icon="FACESEL")
        op = row.operator("curve.dissolve_verts", text="Dissolve", icon="DOT")
        
        row = box.row()
        op = row.operator("object.sc_cutsew_edit", text="Make Curves", icon="CURVE_NCURVE")
        if "Mirror" in context.active_object.modifiers:
                row.operator("object.scs_mirror_cut_pattern", text="Apply Mirror", icon="CURVE_NCURVE")


        if "SimplyCutPattern_GeoNodes_"+context.active_object.name in context.active_object.modifiers:
            modName = "SimplyCutPattern_GeoNodes_"+context.active_object.name
            Simply_GeoNodes_CutModifier = context.active_object.modifiers[modName]
            Simply_GeoNodes_CutGeo = context.active_object.modifiers[modName].node_group.nodes

            row.prop(Simply_GeoNodes_CutGeo["Join Geometry"], "mute",text="Show Resolution Dots", icon="THREE_DOTS", invert_checkbox=True)
            # row.prop(Simply_GeoNodes_CutModifier, "['Socket_8']",text="Resolution", icon="THREE_DOTS")
        op.mode = "MAKEBEZIER"
        row = box.row()
        row.prop(context.scene, "sc_cutdraw_unitard", text="Unitard (One closed piece)", icon_value=custom_icons["unitard"].icon_id)



    def ui_curve_convert(self, layout, context):
        box = layout.box()
        row = box.row(align=False)
        row.label(text="Cut & Sew Pattern", icon="CURVE_NCURVE")
        # row = box.row(align=True)
        row.label(text="", icon="SORTALPHA")
        row.prop(context.active_object, "name", text="")
        row = box.row(align=False)
        row.label(text="",  icon_value=custom_icons["hex_tri"].icon_id)
        row.prop(context.scene, "scs_hex_tri_resolution", text="Resolution")
        # row.prop(context.active_object, "scs_hex_quad", icon="MATPLANE")
        row = box.row(align=True)
        row.scale_y =1.6
        row.active_default = True
        row.operator("object.scs_hex_triangulation", text="Create Cloth", icon="FACESEL")
        # op.mode = "CONVERT"

    def ui_edit_backToObject(self, layout, context):
        box = layout.box()
        row = box.row()
        row.active_default = True
        row.scale_y=1.6
        row.operator("object.editmode_toggle", text="Switch to Object Mode", icon="SCREEN_BACK")


    def ui_dummy(self, layout, context):
        box = layout.box()
        row = box.row()
        row.label(text="Character", icon="ARMATURE_DATA")
        row.operator("object.scs_char_dummy_pose", text="Pose | A-T", icon="POSE_HLT")
        row.alert = True
        op = row.operator("object.scs_char_dummy", text="", icon="TRASH")
        op.mode = "DELETE"
        
        row = box.row()
        row.label(text="", icon_value=custom_icons["female"].icon_id)
        # row.alignment="CENTER"
        row.prop(bpy.data.shape_keys["SimplyKey"].key_blocks["Female-Male"], "value", text="Female | Male",icon="FUND")
        row.label(text="", icon_value=custom_icons["male"].icon_id)








def update_cloth_sewing(self, context):
    obj = context.active_object
    if "SimplyCloth" in obj.modifiers:
        if self.cloth_sewing == True:
            if "SimplyCloth" in obj.modifiers:
                obj.modifiers['SimplyCloth'].settings.use_sewing_springs = True
        elif not self.cloth_sewing:
            obj.modifiers['SimplyCloth'].settings.use_sewing_springs = False
def update_cloth_status(self, context):
    obj = context.active_object
    if "SimplyCloth" in obj.modifiers:
        mod = obj.modifiers["SimplyCloth"]
        if self.cloth_status:
            mod.show_viewport = True
            mod.show_render = True
            bpy.context.object.display_type = 'TEXTURED'
        elif not self.cloth_status:
            mod.show_viewport = False
            mod.show_render = False
            bpy.context.object.display_type = 'WIRE'
def SmoothCloth(self, context):
        obj = context.active_object
        for mod in obj:
            if mod.name == "simplySmooth":
                mod.interations = self.smoothSlider
def update_self_collision(self, context):
    for mod in context.active_object.modifiers:
        if mod.type == "CLOTH":
            mod.collision_settings.use_self_collision = self.self_collision
            mod.collision_settings.self_distance_min = 0.001
def update_pressure(self, context):
    for mod in context.active_object.modifiers:
        if mod.type == "CLOTH":
            mod.settings.use_pressure = self.pressure
            mod.settings.uniform_pressure_force=5
            mod.settings.pressure_factor=5
def update_internal_spring(self, context):
    for mod in context.active_object.modifiers:
        if mod.type == "CLOTH":
            mod.settings.use_internal_springs = self.internal_spring
            mod.settings.internal_spring_max_length = 1
def update_wireframes_mode(self, context):

    obj = context.active_object
    if self.show_wireframes:
        context.space_data.overlay.show_wireframes = self.show_wireframes
        context.space_data.overlay.show_wireframes = True
    else:
        context.space_data.overlay.show_wireframes = self.show_wireframes
        context.space_data.overlay.show_wireframes = False
def update_density_paint(self, context):
    obj = context.active_object
    mod = obj.modifiers["SimplyDensity"]
    if "SimplyDensity" in obj.modifiers:
        bpy.ops.screen.frame_jump(1)
        if self.density_paint:
            mod.show_viewport = True
            mod.show_render = True
        elif not self.density_paint:
            mod.show_viewport = False
            mod.show_render = False
def slide_wrinkles(self, context):
    mod = context.active_object.modifiers["SimplyCloth"]
    value = self.wrinkle_slider
    mod.settings.bending_stiffness = abs(((value/100)*9.99)-10)
def slide_wind_intensity(self, context):
    if "Wind" in bpy.data.objects:
        obj = bpy.data.objects["Wind"]
        value = self.sc_wind_slider
        obj.field.strength = abs(value*25)
def slide_wind_factor(self, context):
    obj = bpy.data.objects['Wind']
    value = self.sc_wind_factor
    obj.field.wind_factor = value
def slide_folds(self, context):
    mod = context.active_object.modifiers["SimplyCloth"]
    value = self.fold_slider
    mod.settings.bending_damping = (7 / 100) * value
def slide_weight(self, context):
    mod = context.active_object.modifiers["SimplyCloth"]
    value = self.weight_slider
    mod.settings.mass = value
def updateWeldDistanceValue(self, context):
    mod = context.active_object.modifiers["SimplyWeld"]
    value = self.weld_slider
    mod.merge_threshold = value
def slide_objectCollisionDistance(self, context):
    mod = context.active_object.modifiers["SimplyCloth"]
    value = self.objectCollisionDistance_slider
    mod.collision_settings.distance_min = value
def slide_selfCollisionDistance(self, context):
    mod = context.active_object.modifiers["SimplyCloth"]
    value = self.selfCollisionDistance_slider
    mod.collision_settings.self_distance_min = value
def slide_collision_quality(self, context):
    mod = context.active_object.modifiers["SimplyCloth"]
    value = self.collision_quality_slider
    mod.collision_settings.collision_quality = value
def slide_friction(self, context):
    mod = context.active_object.modifiers["SimplyCollision"]
    value = self.friction_slider
    mod.settings.cloth_friction = (80/100)*value
def slide_quality_steps(self,context):
    mod = context.active_object.modifiers["SimplyCloth"]
    steps = self.quality_steps_slider
    mod.settings.quality = steps
def mergeByDistance(self, context):
    bpy.ops.mesh.remove_doubles()
def slide_fillHoles(self,context):
    vertSelect = False
    for vert in bpy.context.active_object.data.vertices:
        if vert.select:
            vertSelect = True
            break
        else:
            vertSelect = False
            break
    if vertSelect:
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_all(action='SELECT')
    else:
        bpy.ops.mesh.select_all(action='SELECT')

    value = self.fillHoles_slider
    bpy.ops.mesh.fill_holes()
    bpy.ops.mesh.fill_holes(sides=value)
def slide_mergeByDistance(self,context):
    vertSelect = False
    for vert in bpy.context.active_object.data.vertices:
        if vert.select:
            vertSelect = True
            break
        else:
            vertSelect = False
            break
    if vertSelect:
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_all(action='SELECT')
    else:
        bpy.ops.mesh.select_all(action='SELECT')

    value = self.mergeByDistance_slider
    bpy.ops.mesh.remove_doubles()
    bpy.ops.mesh.remove_doubles(threshold=value)
def update_sewing_weld(self, context):
    obj = context.active_object
    if obj.updateSewingWeldModifier==True:
        context.object.modifiers["SimplyWeld"].show_viewport = True
        context.object.modifiers["SimplyWeld"].show_render = True
        context.object.modifiers["SimplyWeld"].show_in_editmode = True
    if obj.updateSewingWeldModifier == False:
        context.object.modifiers["SimplyWeld"].show_viewport = False
        context.object.modifiers["SimplyWeld"].show_render = False
        context.object.modifiers["SimplyWeld"].show_in_editmode = False
def slide_shrink(self, context):
    # if "SimplyCloth" in context.active_object.modifiers:
    mod = context.active_object.modifiers["SimplyCloth"]
    value = self.shrink_slider
    mod.settings.shrink_min = value
def slide_pressure_intensity(self, context):
    mod = context.active_object.modifiers["SimplyCloth"]
    intensity = self.pressure_intensity_slider
    mod.settings.uniform_pressure_force= intensity
def slide_pressure_factor(self, context):
    mod = context.active_object.modifiers["SimplyCloth"]
    factor = self.pressure_factor_slider
    mod.settings.pressure_factor = factor
def slide_spring_intensity(self, context):
    mod = context.active_object.modifiers["SimplyCloth"]
    intensity = self.spring_intensity_slider
    mod.settings.internal_spring_max_length= intensity
def slide_stiffness(self, context):
    mod = context.active_object.modifiers["SimplyCloth"]
    value = self.stiffness_slider

    mod.settings.tension_stiffness = (45/100)*value
    mod.settings.compression_stiffness= (45/100)*value
    mod.settings.shear_stiffness= (45/100)*value
def change_fold_accuracy(self, context):
    if self.fold_detail == "ROUGH":
        for mod in context.active_object.modifiers:
            if mod.type == "CLOTH" and mod.name == "SimplyCloth":
                mod.settings.quality = 8
                mod.settings.bending_damping = 0

def change_sim_quality(self, context):
    if self.sim_quality == "TEST":
        for mod in context.active_object.modifiers:
            if mod.type == "CLOTH" and mod.name == "SimplyCloth":
                mod.settings.quality = 3
                mod.collision_settings.collision_quality = 3

    if self.sim_quality == "FAST":
        for mod in context.active_object.modifiers:
            if mod.type == "CLOTH" and mod.name == "SimplyCloth":
                mod.settings.quality = 9
                mod.collision_settings.collision_quality = 6


    if self.sim_quality == "REGULAR":
        for mod in context.active_object.modifiers:
            if mod.type == "CLOTH" and mod.name == "SimplyCloth":
                mod.settings.quality = 12
                mod.collision_settings.collision_quality= 9

    if self.sim_quality == "ACCURATE":
        for mod in context.active_object.modifiers:
            if mod.type == "CLOTH" and mod.name == "SimplyCloth":
                mod.settings.quality = 27
                mod.collision_settings.collision_quality=15
    if "SurfaceDeform" in context.active_object.modifiers:
        bpy.ops.object.surfacedeform_bind(modifier="SurfaceDeform")
        bpy.ops.object.surfacedeform_bind(modifier="SurfaceDeform")
    bpy.ops.screen.animation_manager(mode="STOP")

def update_subdivision(self,context):
    for mod in context.active_object.modifiers:
        if mod.type == "SUBSURF" and mod.name == "SimplySubsurf":
            if self.resolution == "NO":
                mod.levels = 0
            elif self.resolution == "LOW":
                mod.levels = 1
            elif self.resolution == "MID":
                mod.levels = 3
            elif self.resolution == "HIGH":
                mod.levels = 4
    screen = bpy.ops.screen
    screen.frame_jump(1)
def update_frame_range(self, context):
    obj = context.active_object
    scene = context.scene
    start = self.start_frame
    end = self.end_frame

    if "SimplyCloth" in obj.modifiers:
        mod = obj.modifiers["SimplyCloth"]
        mod.point_cache.frame_start = start
        scene.frame_start = start
        mod.point_cache.frame_end = end
        scene.frame_end = end
def update_baseSub_level(self, context):

    obj = context.active_object
    if obj.modifiers:
        if "BaseSub" in obj.modifiers:
            mod = obj.modifiers["BaseSub"]
            level = self.baseSub_level
            mod.levels = level
            mod.render_levels = level
            bpy.ops.screen.frame_jump(1)
def update_face_orientation_view(self, context):
    obj = context.active_object
    if self.face_orientation:
        context.space_data.overlay.show_face_normals = True
        context.space_data.overlay.show_face_orientation = True
        context.space_data.overlay.normals_length = 0.01
    else:
        context.space_data.overlay.show_face_normals = False
        context.space_data.overlay.show_face_orientation = False
        context.space_data.overlay.normals_length = 0.01
def update_weight_pin_view(self, context):
    obj = context.active_object
    if self.weight_pin_view:
        if "SimplyPin" in context.active_object.vertex_groups:
            index = bpy.context.active_object.vertex_groups["SimplyPin"].index
            obj.vertex_groups.active_index = index
        bpy.context.space_data.overlay.show_weight = True
    else:
        if "SimplyPin" in context.active_object.vertex_groups:
            index = bpy.context.active_object.vertex_groups["SimplyPin"].index
            obj.vertex_groups.active_index = index
        bpy.context.space_data.overlay.show_weight = True
        bpy.context.space_data.overlay.show_weight = False
# def update_pin_slider_on_fly(self, context):
def changeWeightValue(self, context):
    bpy.context.scene.tool_settings.vertex_group_weight = context.active_object.weight_value
def updateStrenghtenIntensity(self, context):
    mod = context.active_object.modifiers["SimplyCloth"]
    value = self.strenghten_slider
    mod.settings.bending_stiffness_max = (100 / 100) * value
def update_brushForceFalloff(self, context):
    if context.active_object.brushForceFalloff == True:
        bpy.data.brushes["Cloth"].cloth_force_falloff_type = 'RADIAL'
    elif context.active_object.brushForceFalloff == False:
        bpy.data.brushes["Cloth"].cloth_force_falloff_type = 'PLANE'
def updateMaskHardness(self, context):
    obj = context.active_object
    value = self.hardness_mask_slider
    bpy.data.brushes["Mask"].hardness = value
def getModifiersIdfromCloth(self, context):
    modifiers = context.active_object.modifiers
    for i, j in enumerate(modifiers):
        if j.name == "SimplyCloth":
            return i
        
def update_thicknessOverClothModifier(self, context):
    status = False
    obj = context.active_object
    value = self.thicknessBeforeAfterCloth
    modIndex = getModifiersIdfromCloth(self, context)
    print(modIndex)
    if value == True:
        bpy.ops.object.modifier_move_to_index(modifier="SimplySolidify", index=modIndex)
    elif value == False:
        bpy.ops.object.modifier_move_to_index(modifier="SimplySolidify", index=modIndex)
def updateClothEnableStatus(self, context):
    obj = context.active_object
    obj.modifiers["SimplyCloth"].show_viewport = obj.sc_cloth_status
    if obj.modifiers["SimplyCloth"].show_viewport == False:
        obj.display_type = 'WIRE'
    if obj.modifiers["SimplyCloth"].show_viewport == True:
        obj.display_type = 'SOLID'

def registerIcon():
    import bpy.utils.previews
    global custom_icons

    # icon_data = [
    #     ("createCloth", "simply_cloth_helper_icon.png"),
    #     ("icon_sculpt_mode", "icon_sculpt_mode.png"),
    #     ("brush_radial", "brush_radial.png"),
    # ]
    custom_icons = bpy.utils.previews.new()

    rootdir = dirname(dirname(__file__))
    addons_dir = join(rootdir, "simply_cloth_studio")
    icons_dir = join(addons_dir, "icons")

    for filename in listdir(icons_dir):
        if filename.lower().endswith('.png') or filename.lower().endswith('.svg'):
            finnm = filename.lower()
            key = splitext(finnm)[0]
            filepath = join(icons_dir, filename)
            if isfile(filepath):
                custom_icons.load(key, filepath, 'IMAGE')


#     custom_icons.load("createCloth", os.path.join(icons_dir, "simply_cloth_helper_icon.png"), 'IMAGE')
#     custom_icons.load("icon_sculpt_mode", os.path.join(icons_dir, "icon_sculpt_mode.png"), 'IMAGE')
#     custom_icons.load("brush_radial", os.path.join(icons_dir, "brush_radial.png"), 'IMAGE')
#     custom_icons.load("brush_plane", os.path.join(icons_dir, "brush_plane.png"), 'IMAGE')
#     custom_icons.load("sculpt_mask", os.path.join(icons_dir, "sculpt_mask.png"), 'IMAGE')
#     custom_icons.load("sculpt_mask_clean", os.path.join(icons_dir, "sculpt_mask_clean.png"), 'IMAGE')
#     custom_icons.load("sculpt_mask_invert", os.path.join(icons_dir, "sculpt_mask_invert.png"), 'IMAGE')
# #
#     custom_icons.load("play_icon", os.path.join(icons_dir, "play_icon.png"), 'IMAGE')
#     custom_icons.load("pause_icon", os.path.join(icons_dir, "pause_icon.png"), 'IMAGE')
#     custom_icons.load("stop_icon", os.path.join(icons_dir, "stop_icon.png"), 'IMAGE')

#     custom_icons.load("sim_test_icon", os.path.join(icons_dir, "sim_test_icon.png"), 'IMAGE')
#     custom_icons.load("sim_fast_icon", os.path.join(icons_dir, "sim_fast_icon.png"), 'IMAGE')
#     custom_icons.load("sim_regular_icon", os.path.join(icons_dir, "sim_regular_icon.png"), 'IMAGE')
#     custom_icons.load("sim_accurate_icon", os.path.join(icons_dir, "sim_accurate_icon.png"), 'IMAGE')

#     custom_icons.load("mirror_x", os.path.join(icons_dir, "mirror_x.png"), 'IMAGE')
#     custom_icons.load("mirror_y", os.path.join(icons_dir, "mirror_y.png"), 'IMAGE')
#     custom_icons.load("unitard", os.path.join(icons_dir, "unitard.png"), 'IMAGE')

#     custom_icons.load("male", os.path.join(icons_dir, "male.png"), 'IMAGE')
#     custom_icons.load("female", os.path.join(icons_dir, "female.png"), 'IMAGE')
#     custom_icons.load("hex_tri", os.path.join(icons_dir, "hex_tri.png"), 'IMAGE')

#     custom_icons.load("sup_zenuv", os.path.join(icons_dir, "sup_zenuv.png"), 'IMAGE')

#     custom_icons.load("preset_cotton", os.path.join(icons_dir, "preset_cotton.png"), 'IMAGE')
#     custom_icons.load("preset_denim", os.path.join(icons_dir, "preset_denim.png"), 'IMAGE')
#     custom_icons.load("preset_leather", os.path.join(icons_dir, "preset_leather.png"), 'IMAGE')
#     custom_icons.load("preset_rubber", os.path.join(icons_dir, "preset_rubber.png"), 'IMAGE')
#     custom_icons.load("preset_silk", os.path.join(icons_dir, "preset_silk.png"), 'IMAGE')
#     custom_icons.load("preset_wool", os.path.join(icons_dir, "preset_wool.png"), 'IMAGE')
#     custom_icons.load("preset_elastic_smooth", os.path.join(icons_dir, "preset_elastic_smooth.png"), 'IMAGE')
#     custom_icons.load("preset_crease", os.path.join(icons_dir, "preset_crease.png"), 'IMAGE')
#     custom_icons.load("preset_pressure", os.path.join(icons_dir, "preset_pressure.png"), 'IMAGE')
#     custom_icons.load("preset_shrink_pressure", os.path.join(icons_dir, "preset_shrink_pressure.png"), 'IMAGE')
#     custom_icons.load("preset_stiff_smooth", os.path.join(icons_dir, "preset_stiff_smooth.png"), 'IMAGE')
#     custom_icons.load("preset_heavy_silk", os.path.join(icons_dir, "preset_heavy_silk.png"), 'IMAGE')
#     custom_icons.load("preset_spring", os.path.join(icons_dir, "preset_spring.png"), 'IMAGE')
#     custom_icons.load("preset_stiff_paper", os.path.join(icons_dir, "preset_stiff_paper.png"), 'IMAGE')
#     custom_icons.load("preset_crumple_paper", os.path.join(icons_dir, "preset_crumple_paper.png"), 'IMAGE')
#     custom_icons.load("preset_standard", os.path.join(icons_dir, "preset_standard.png"), 'IMAGE')

#     custom_icons.load("icon_brush_drag", os.path.join(icons_dir, "icon_brush_drag.png"), 'IMAGE')
#     custom_icons.load("icon_brush_expand", os.path.join(icons_dir, "icon_brush_expand.png"), 'IMAGE')
#     custom_icons.load("icon_brush_grab", os.path.join(icons_dir, "icon_brush_grab.png"), 'IMAGE')
#     custom_icons.load("icon_brush_inflate", os.path.join(icons_dir, "icon_brush_inflate.png"), 'IMAGE')
#     custom_icons.load("icon_brush_pinch", os.path.join(icons_dir, "icon_brush_pinch.png"), 'IMAGE')
#     custom_icons.load("icon_brush_pinch_perpendicular", os.path.join(icons_dir, "icon_brush_pinch_perpendicular.png"), 'IMAGE')
#     custom_icons.load("icon_brush_push", os.path.join(icons_dir, "icon_brush_push.png"), 'IMAGE')
#     custom_icons.load("icon_brush_mask", os.path.join(icons_dir, "icon_brush_mask.png"), 'IMAGE')
#     custom_icons.load("icon_attach_to", os.path.join(icons_dir, "icon_attach_to.png"), 'IMAGE')

#     custom_icons.load("icon_brush_bound_bend", os.path.join(icons_dir, "icon_brush_Bound_ClothBend.png"), 'IMAGE')
#     custom_icons.load("icon_brush_bound_grab", os.path.join(icons_dir, "icon_brush_Bound_Grab.png"), 'IMAGE')
#     custom_icons.load("icon_brush_bound_inflate", os.path.join(icons_dir, "icon_brush_Bound_Inflate.png"), 'IMAGE')
#     custom_icons.load("icon_brush_bound_twist", os.path.join(icons_dir, "icon_brush_Bound_Twist.png"), 'IMAGE')
#     custom_icons.load("icon_brush_bound_smooth", os.path.join(icons_dir, "icon_brush_Bound_Smooth.png"), 'IMAGE')
#     custom_icons.load("icon_brush_pose_scale", os.path.join(icons_dir, "icon_brush_Pose_Scale.png"), 'IMAGE')
#     custom_icons.load("icon_brush_pose_stretch", os.path.join(icons_dir, "icon_brush_Pose_Stretch.png"), 'IMAGE')
#     custom_icons.load("icon_brush_pose_twist", os.path.join(icons_dir, "icon_brush_Pose_Twist.png"), 'IMAGE')

    bpy.types.Object.presets = EnumProperty(default="STANDARD", items=(
    ("COTTON", "Cotton", "Cotton Preset",custom_icons["preset_cotton"].icon_id,0),
    ("DENIM", "Denim", "Denim Preset",custom_icons["preset_denim"].icon_id,1),
    ("LEATHER", "Leather", "Leather Preset",custom_icons["preset_leather"].icon_id,2),
    ("RUBBER", "Rubber", "Rubber Preset",custom_icons["preset_rubber"].icon_id,3),
    ("SILK", "Silk", "Silk Preset",custom_icons["preset_silk"].icon_id,4),
    ("WOOL", "Wool", "Wool Preset",custom_icons["preset_wool"].icon_id,5),
    ("ELASTIC_SMOOTH", "Elastic Smooth", "Elastic Smooth Preset", custom_icons["preset_elastic_smooth"].icon_id, 6),
    ("CREASE", "Crease", "Crease Preset",custom_icons["preset_crease"].icon_id,7),
    ("PRESSURE", "Pressure", "Pressure Preset",custom_icons["preset_pressure"].icon_id,8),
    ("SHRINK_PRESSURE", "Shrink Pressure", "Shrink Pressure Preset",custom_icons["preset_shrink_pressure"].icon_id,9),
    ("STIFF_SMOOTH", "Stiff Smooth", "Stiff Smooth Preset",custom_icons["preset_stiff_smooth"].icon_id,10),
    ("HEAVY_SILK", "Heavy Silk", "Heavy Silk Preset",custom_icons["preset_heavy_silk"].icon_id,11),
    ("SPRING", "Spring", "Spring Preset",custom_icons["preset_spring"].icon_id,12),
    ("STIFF_PAPER", "Stiff Paper", "Stiff Paper Preset",custom_icons["preset_stiff_paper"].icon_id,13),
    ("CRUMPLE_PAPER", "Crumple Paper", "Crumple Paper Preset",custom_icons["preset_crumple_paper"].icon_id,14),
    ("STANDARD", "Standard", "Standard Preset",custom_icons["preset_standard"].icon_id,15),
    ),update=presets.set_preset)

    bpy.types.Scene.brushes = EnumProperty(default="DRAG", items=(
    ("DRAG", "Drag", "Drag",custom_icons["icon_brush_drag"].icon_id,0),
    ("PUSH", "Push", "Push", custom_icons["icon_brush_push"].icon_id, 1),
    ("INFLATE", "Inflate", "Inflate", custom_icons["icon_brush_inflate"].icon_id, 2),
    ("PINCH_POINT", "Pinch Point", "Pinch Point", custom_icons["icon_brush_pinch"].icon_id, 3),
    ("PINCH_PERPENDICULAR", "Pinch Prependicular", "Pinch Prependicular",custom_icons["icon_brush_pinch_perpendicular"].icon_id, 4),
    ("EXPAND", "Expand", "Expand", custom_icons["icon_brush_expand"].icon_id, 5),
    ("GRAB", "Grab", "Grab",custom_icons["icon_brush_grab"].icon_id,6),
    ("MASK", "Mask", "Mask",custom_icons["icon_brush_mask"].icon_id,7),

    ("POSE_TWIST", "Twist", "Twist",custom_icons["icon_brush_pose_twist"].icon_id,8),
    ("POSE_SCALE", "Scale", "Scale",custom_icons["icon_brush_pose_scale"].icon_id,9),
    ("POSE_STRETCH", "Stretch", "Stretch",custom_icons["icon_brush_pose_stretch"].icon_id,10),

    ("BOUNDARY_BEND", "Edge Bend", "Edge Bend",custom_icons["icon_brush_bound_bend"].icon_id,11),
    ("BOUNDARY_INFLATE", "Edge Inflate", "Edge Inflate",custom_icons["icon_brush_bound_inflate"].icon_id,12),
    ("BOUNDARY_GRAB", "Edge Grab", "Edge Grab",custom_icons["icon_brush_bound_grab"].icon_id,13),
    ("BOUNDARY_TWIST", "Edge Twist", "Test",custom_icons["icon_brush_bound_twist"].icon_id,14),
    ("BOUNDARY_SMOOTH", "Edge Smooth", "Test",custom_icons["icon_brush_bound_smooth"].icon_id,15),
    # ("CLOTHFILTER_GRAVITY", "Cloth Filter", "Cloth Filter",custom_icons["icon_brush_mask"].icon_id,11),
    # ("CLOTHFILTER_INFLATE", "Cloth Filter", "Cloth Filter",custom_icons["icon_brush_mask"].icon_id,12),
    # Pose, Cloth Sim
    # Boundary Cloth Sim
    # Cloth Filter, Pinch, Expand, Inflate
    # 
    ),update=presets.set_brush)

    bpy.types.Object.sim_quality = EnumProperty(default="REGULAR", items=(
    ("TEST", "Trial", "fast speed | bad quality", custom_icons["sim_test_icon"].icon_id, 1),
    ("FAST", "Fast", "good speed | low quality", custom_icons["sim_fast_icon"].icon_id, 2),
    ("REGULAR", "Regular", "regular speed | good quality", custom_icons["sim_regular_icon"].icon_id, 3),
    ("ACCURATE", "Accuracy", "slow speed | best quality", custom_icons["sim_accurate_icon"].icon_id, 4)
    ), update=ui_panel.change_sim_quality, name="Simulation Quality")

    brush_cloth_names_to_check = [
    "POSE_TWIST",
    "POSE_SCALE",
    "POSE_STRETCH",
    "BOUNDARY_BEND",
    "BOUNDARY_INFLATE",
    "BOUNDARY_GRAB",
    "BOUNDARY_TWIST"
]
def unregisterIcon():
    global custom_icons
