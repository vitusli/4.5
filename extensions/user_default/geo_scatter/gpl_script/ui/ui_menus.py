"""
• Script License: 

    This python script file is licensed under GPL 3.0
    
    This program is free software; you can redistribute it and/or modify it under 
    the terms of the GNU General Public License as published by the Free Software
    Foundation; either version 3 of the License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
    without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 
    See the GNU General Public License for more details.
    
    See full license on 'https://www.gnu.org/licenses/gpl-3.0.en.html#license-text'

• Additonal Information: 

    The components in this archive are a mere aggregation of independent works. 
    The GPL-licensed scripts included here serve solely as a control and/or interface for 
    the Geo-Scatter geometry-node assets.

    The content located in the 'PluginFolder/non_gpl/' directory is NOT licensed under 
    the GPL. For details, please refer to the LICENSES.txt file within this folder.

    The non-GPL components and assets can function fully without the scripts and vice versa. 
    They do not form a derivative work, and are distributed together for user convenience.

    Redistribution, modification, or unauthorized use of the content in the 'non_gpl' folder,
    including .blend files or image files, is prohibited without prior written consent 
    from BD3D DIGITAL DESIGN, SLU.
        
• Trademark Information:

    Geo-Scatter® name & logo is a trademark or registered trademark of “BD3D DIGITAL DESIGN, SLU” 
    in the U.S. and/or European Union and/or other countries. We reserve all rights to this trademark. 
    For further details, please review our trademark and logo policies at “www.geoscatter.com/legal”. The 
    use of our brand name, logo, or marketing materials to distribute content through any non-official
    channels not listed on “www.geoscatter.com/download” is strictly prohibited. Such unauthorized use 
    falsely implies endorsement or affiliation with third-party activities, which has never been granted. We 
    reserve all rights to protect our brand integrity & prevent any associations with unapproved third parties.
    You are not permitted to use our brand to promote your unapproved activities in a way that suggests official
    endorsement or affiliation. As a reminder, the GPL license explicitly excludes brand names from the freedom,
    our trademark rights remain distinct and enforceable under trademark laws.

"""
# A product of “BD3D DIGITAL DESIGN, SLU”
# Authors:
# (c) 2024 Dorian Borremans

#####################################################################################################
#
# ooooo     ooo ooooo      ooo        ooooo
# `888'     `8' `888'      `88.       .888'
#  888       8   888        888b     d'888   .ooooo.  ooo. .oo.   oooo  oooo   .oooo.o
#  888       8   888        8 Y88. .P  888  d88' `88b `888P"Y88b  `888  `888  d88(  "8
#  888       8   888        8  `888'   888  888ooo888  888   888   888   888  `"Y88b.
#  `88.    .8'   888        8    Y     888  888    .o  888   888   888   888  o.  )88b
#    `YbodP'    o888o      o8o        o888o `Y8bod8P' o888o o888o  `V88V"V8P' 8""888P'
#
#####################################################################################################


import bpy

import os
import json

from ... __init__ import addon_prefs

from .. resources.icons import cust_icon
from .. translations import translate
from .. resources import directories

from .. utils.extra_utils import is_rendered_view
from .. utils.str_utils import word_wrap, is_attr_surfs_shared

from .. scattering.copy_paste import is_BufferCategory_filled

from . import ui_creation
from . import ui_templates


#NOTE not consistent, not all menus are regrouped here

#  .oooooo..o           oooo                          .    o8o                             ooo        ooooo
# d8P'    `Y8           `888                        .o8    `"'                             `88.       .888'
# Y88bo.       .ooooo.   888   .ooooo.   .ooooo.  .o888oo oooo   .ooooo.  ooo. .oo.         888b     d'888   .ooooo.  ooo. .oo.   oooo  oooo
#  `"Y8888o.  d88' `88b  888  d88' `88b d88' `"Y8   888   `888  d88' `88b `888P"Y88b        8 Y88. .P  888  d88' `88b `888P"Y88b  `888  `888
#      `"Y88b 888ooo888  888  888ooo888 888         888    888  888   888  888   888        8  `888'   888  888ooo888  888   888   888   888
# oo     .d8P 888    .o  888  888    .o 888   .o8   888 .  888  888   888  888   888        8    Y     888  888    .o  888   888   888   888
# 8""88888P'  `Y8bod8P' o888o `Y8bod8P' `Y8bod8P'   "888" o888o `Y8bod8P' o888o o888o      o8o        o888o `Y8bod8P' o888o o888o  `V88V"V8P'



class SCATTER5_MT_selection_export_submenu(bpy.types.Menu):

    bl_idname      = "SCATTER5_MT_selection_export_submenu"
    bl_label       = ""
    bl_description = ""

    def draw(self, context):
        layout = self.layout

        #get UILayout arg
        scat_scene   = bpy.context.scene.scatter5
        emitter      = context.pass_ui_arg_emitter
        elinked      = bool(emitter.library)
        psys         = emitter.scatter5.particle_systems
        all_psys     = scat_scene.get_all_psys(search_mode="all", also_linked=True)
        group_active = emitter.scatter5.get_group_active()
        psy_active   = emitter.scatter5.get_psy_active()
        psys_sel     = emitter.scatter5.get_psys_selected()


        #Select All 

        is_some_sel = any(p.sel for p in emitter.scatter5.particle_systems)
        is_addonprefs = (context.space_data.type=="PREFERENCES")
        
        
        #Select All 

        is_some_sel = any(p.sel for p in emitter.scatter5.particle_systems)
        is_addonprefs = (context.space_data.type=="PREFERENCES")
        
        layout.operator("scatter5.export_to_objects", icon="SCENE_DATA", text=translate("Selected to Instances")+f" [{len(psys_sel)}]", ).obj_session_uid = emitter.session_uid
        layout.operator("scatter5.export_to_json", icon="FILE_TEXT", text=translate("Selected to .Json")+f" [{len(psys_sel)}]", )
        layout.operator("scatter5.export_to_presets", icon="CURRENT_FILE", text=translate("Selected to Preset(s)")+f" [{len(psys_sel)}]", )
        layout.operator("scatter5.export_to_biome", icon="CURRENT_FILE", text=translate("Selected to Biome")+f" [{len(psys_sel)}]", )

        if (psy_active.s_distribution_method!="manual_all"):
            layout.separator()
            ope = layout.row()
            ope.operator_context = "INVOKE_DEFAULT"
            ope.operator("scatter5.export_psy_to_manual", text=translate("Selected to Manual-Distribution")+f" [{len(psys_sel)}]", icon="FILTER").use_selection = True
            
        return None 
    
class SCATTER5_MT_selection_menu(bpy.types.Menu):

    bl_idname      = "SCATTER5_MT_selection_menu"
    bl_label       = translate("Scatter-Lister Option Menu")
    bl_description = translate("Here you will find options and handy operators that will interact with all/selected/active scatter-system(s). The number between brackets '[n]' represents the system(s) that will be affected by the chosen operation")

    def draw(self, context):
        layout = self.layout

        #get UILayout arg
        from ... __init__ import blend_prefs
        scat_data    = blend_prefs()
        scat_scene   = bpy.context.scene.scatter5
        emitter      = context.pass_ui_arg_emitter
        elinked      = bool(emitter.library)
        psys         = emitter.scatter5.particle_systems
        all_psys     = scat_scene.get_all_psys(search_mode="all", also_linked=True)
        group_active = emitter.scatter5.get_group_active()
        psy_active   = emitter.scatter5.get_psy_active()
        psys_sel     = emitter.scatter5.get_psys_selected()

        #Select All 

        is_some_sel = any(p.sel for p in emitter.scatter5.particle_systems)
        is_addonprefs = (context.space_data.type=="PREFERENCES")

         
        #selection operators
        
        if (not is_addonprefs):

            if (len(psys_sel)==len(psys)):
                seltxt = translate("De-Select All System(s)")+f" [{len(psys)}]"
                selicon = cust_icon("W_GROUP_TOGGLE_SEL_NONE")
            else:
                seltxt = translate("Select All System(s)")+f" [{len(psys)}]"
                selicon = cust_icon("W_GROUP_TOGGLE_SEL_ALL")

            sel = layout.row()
            sel.enabled = bool(len(psys))
            if (elinked):
                sel.enabled = False
            op = sel.operator("scatter5.toggle_selection", text=seltxt, icon_value=selicon,)
            op.emitter_name = emitter.name

            layout.separator()

        
        #group

        _ = translate("Group") + translate("Ungroup") #For biome reader version, they'll need this translation
        
        sub = layout.row(align=True)
        sub.enabled = is_some_sel
        if (elinked):
            sub.enabled = False
        sub.menu("SCATTER5_MT_selection_menu_sub_groups",text=translate("Group Selected")+f" [{len(psys_sel)}]", icon="OUTLINER_COLLECTION")

        sub = layout.row(align=True)
        ungroup_enabled = is_some_sel
        if ( is_some_sel and all( (p.group=="") for p in psys_sel) ):
            ungroup_enabled = False
        sub.enabled = ungroup_enabled
        if (elinked):
            sub.enabled = False
        op = sub.operator("scatter5.group_psys",text=translate("Ungroup Selected")+f" [{len(psys_sel)}]", icon="GROUP")
        op.emitter_name = emitter.name
        op.action = "UNGROUP"

        layout.separator()
        

        #lock

        if (not is_addonprefs):
            
            sub = layout.row(align=True)
            sub.enabled = bool(len(psys_sel))
            if (elinked):
                sub.enabled = False
            op = sub.operator("scatter5.exec_line", icon="LOCKED", text=translate("Lock Selected")+f" [{len(psys_sel)}]")
            op.api = f"[p.lock_all() for p in psys_sel]"
            op.description = translate("Lock/unlock the selected scatter-system(s).\nOnce locked, it will not be possible to interact with their scatter-settings in the interface. Additionally, any potential update signals will be denied of reaching the geometry node scatter-engine.")
            op.undo = translate("Lock/unlock scatter-system(s)")

            sub = layout.row(align=True)
            sub.enabled = bool(len(psys_sel))
            if (elinked):
                sub.enabled = False
            op = sub.operator("scatter5.exec_line", icon="UNLOCKED", text=translate("Unlock Selected")+f" [{len(psys_sel)}]")
            op.api = f"[p.unlock_all() for p in psys_sel]"
            op.description = translate("Lock/unlock the selected scatter-system(s).\nOnce locked, it will not be possible to interact with their scatter-settings in the interface. Additionally, any potential update signals will be denied of reaching the geometry node scatter-engine.")
            op.undo = translate("Lock/unlock scatter-system(s)")

            layout.separator()
            
        #randomize

        if (not is_addonprefs):

            sub = layout.row(align=True)
            sub.enabled = bool(len(psys_sel))
            if (elinked):
                sub.enabled = False
            op = sub.operator("scatter5.batch_randomize", icon_value=cust_icon("W_DICE"), text=translate("Randomize Selected")+f" [{len(psys_sel)}]")
            op.use_context_sel=True
            
            layout.separator()

        #set local/global

        if (not is_addonprefs):

            sub = layout.row(align=True)
            sub.enabled = bool(len(psys))
            if (elinked):
                sub.enabled = False
            op = sub.operator("scatter5.batch_set_space",text=translate("Set Selected as Local")+f" [{len(psys_sel)}]", icon='ORIENTATION_LOCAL',)
            op.space = 'local'

            sub = layout.row(align=True)
            sub.enabled = bool(len(psys))
            if (elinked):
                sub.enabled = False
            op = sub.operator("scatter5.batch_set_space",text=translate("Set Selected as Global")+f" [{len(psys_sel)}]", icon='WORLD',)
            op.space = 'global'

            layout.separator()

        #show color 

        if (not is_addonprefs):

            sub = layout.row(align=True)
            sub.enabled = bool(len(psys))
            op = sub.operator("scatter5.set_solid_and_object_color",text=translate("Set Viewport Display Colors"), icon="RESTRICT_COLOR_ON",)
            op.mode = "restore" if ((context.space_data.shading.type=='SOLID') and (context.space_data.shading.color_type=='OBJECT')) else "set"

            sub = layout.row(align=True)
            op = sub.operator("scatter5.exec_line", icon="INFO_LARGE", text=translate("Hide Descriptions") if (scat_data.show_description) else translate("Show Descriptions"),)
            op.api = f"scat_data.show_description = not scat_data.show_description"
            op.description = translate("Show/Hide the Scatter-Systems or Groups description right below the lister interface, useful if you'd like to define hover descriptions on your scatter-items")

            layout.separator()

        #direct nodetree access

        if (psy_active):
                
            row = layout.row()
            row.enabled = (psy_active is not None)
            op = row.operator("scatter5.open_editor", text=translate("Show Active-System Engine"), icon="NODETREE",)
            op.editor_type = "GeometryNodeTree"
            op.instructions = f"area.spaces[0].pin=True ; area.spaces[0].node_tree = get_from_uid(psy_active.get_scatter_mod().node_group.session_uid,collection=bpy.data.node_groups)"
            op.description = translate("All scatter-system(s) are based on a complex geometry-node scatter engine. If you're an advanced user, you could potentially tweak the behavior of this scatter-engine in order to, for example, add new features, or change precise algorithmic behaviors. Use this operator to reveal the active system nodetree in a blender node editor.\n\nBy default all scatter-systems will have an according 'scatter_obj' located somewhere in your outliner. On this 'scatter_obj' the scatter modifier will be located. Note that this nodetree is being interacted with python api call's")

            layout.separator()

        #Copy 

        row = layout.row()
        row.enabled = is_some_sel
        if (elinked):
            row.enabled = False
        op = row.operator("scatter5.copy_paste_systems",text=translate("Copy Selected System(s)")+f" [{len(psys_sel)}]",icon="DUPLICATE")
        op.emitter_name = emitter.name
        op.copy = True

        #Paste 

        from .. scattering.copy_paste import is_BufferSystems_filled

        row = layout.row() 
        row.enabled = is_BufferSystems_filled()
        if (elinked):
            row.enabled = False
        op = row.operator("scatter5.copy_paste_systems",text=translate("Paste System(s)"),icon="DUPLICATE")
        op.emitter_name = emitter.name
        op.paste = True

        row = layout.row()
        row.enabled = is_BufferSystems_filled()
        if (elinked):
            row.enabled = False
        op = row.operator("scatter5.copy_paste_systems",text=translate("Paste System(s) & Synchronize"),icon="DUPLICATE")
        op.emitter_name = emitter.name
        op.paste = True
        op.synchronize = True

        #3D view special, this menu is also available from addon prefs
        
        layout.separator()

        row = layout.row()
        row.enabled = is_some_sel
        if (elinked):
            row.enabled = False
        row.menu("SCATTER5_MT_preset_menu_uilist",text=translate("Apply Preset to Selected")+f" [{len(psys_sel)}]",icon="PRESET",)

        #Exports operation
        
        layout.separator()

        row = layout.row()
        row.enabled = is_some_sel
        if (elinked):
            row.enabled = False
        row.menu("SCATTER5_MT_selection_export_submenu",text=translate("Export/Convert"),icon="EXPORT",)
        
        #Remove all System 

        if (not elinked):
                
            layout.separator()

            sub = layout.row(align=True)
            sub.enabled = bool(len(psys))
            op = sub.operator("scatter5.remove_system",text=translate("Clear All System(s)")+f" [{len(psys)}]", icon="TRASH")
            op.emitter_name = emitter.name
            op.method  = "clear"
            op.undo_push = True
        
        #Link operators
        
        if (elinked):
            
            layout.separator()
            
            sub = layout.row(align=True)
            op = sub.operator("scatter5.exec_line",text=translate("Reload System(s) Library"), icon="FILE_REFRESH")
            op.api  = f"get_from_uid({emitter.session_uid}).library.reload()"
            op.description = translate("Reload all the linked datablocks related to this emitter libraries. This operation will effectively refresh the scatters, assuming the initial file the link is coming from was updated.")
            
            # sub = layout.row(align=True)
            # op = sub.operator("scatter5.linked_scatter_manipulation",text=translate("Make System(s) Library Local")+f" [{len([p for p in all_psys if p.id_data.library==emitter.library])}]", icon="PACKAGE")
            # op.option  = "make_all_local"
            # op.emitter_session_uid = emitter.session_uid
            
            sub = layout.row(align=True)
            op = sub.operator("scatter5.linked_scatter_manipulation",text=translate("Clear Linked System(s)")+f" [{len(psys)}]", icon="TRASH")
            op.option  = "delete"
            op.emitter_session_uid = emitter.session_uid
        
        return None


class SCATTER5_MT_selection_menu_sub_groups(bpy.types.Menu):

    bl_idname      = "SCATTER5_MT_selection_menu_sub_groups"
    bl_label       = ""
    bl_description = ""

    def __init__(self, *args, **kwargs):
        """cleansed unused groups when calling the submenu"""
        
        super().__init__(*args, **kwargs)
        
        scat_scene = bpy.context.scene.scatter5
        emitter = scat_scene.emitter
        emitter.scatter5.cleanse_unused_particle_groups()
        return None
        
    def draw(self, context):
        layout = self.layout

        #get UILayout arg
        layout     = self.layout
        scat_scene = bpy.context.scene.scatter5
        emitter    = context.pass_ui_arg_emitter 
        psys       = emitter.scatter5.particle_systems
        psy_active = emitter.scatter5.get_psy_active()
        psys_sel   = emitter.scatter5.get_psys_selected()

        layout.enabled = bool(len(psys_sel))

        for g in emitter.scatter5.particle_groups: 
            
            sub = layout.row(align=True)
            op = sub.operator("scatter5.group_psys",text=g.name, icon="GROUP")
            op.emitter_name = emitter.name
            op.action = "GROUP"
            op.name = g.name
            
            continue
        
        layout.separator()

        sub = layout.row(align=True)
        op = sub.operator("scatter5.group_psys",text=translate("New Group"), icon="ADD")
        op.emitter_name = emitter.name
        op.action = "NEWGROUP"
        op.name = "MyGroup"

        return None 


# ooooo   ooooo                           .o8                          ooo        ooooo
# `888'   `888'                          "888                          `88.       .888'
#  888     888   .ooooo.   .oooo.    .oooo888   .ooooo.  oooo d8b       888b     d'888   .ooooo.  ooo. .oo.   oooo  oooo   .oooo.o
#  888ooooo888  d88' `88b `P  )88b  d88' `888  d88' `88b `888""8P       8 Y88. .P  888  d88' `88b `888P"Y88b  `888  `888  d88(  "8
#  888     888  888ooo888  .oP"888  888   888  888ooo888  888           8  `888'   888  888ooo888  888   888   888   888  `"Y88b.
#  888     888  888    .o d8(  888  888   888  888    .o  888           8    Y     888  888    .o  888   888   888   888  o.  )88b
# o888o   o888o `Y8bod8P' `Y888""8o `Y8bod88P" `Y8bod8P' d888b         o8o        o888o `Y8bod8P' o888o o888o  `V88V"V8P' 8""888P'


class SCATTER5_PT_scatter_preset_header(bpy.types.Panel):

    bl_idname      = "SCATTER5_PT_scatter_preset_header"
    bl_label       = translate("Preset Settings")
    bl_category    = ""
    bl_space_type  = "VIEW_3D"
    bl_region_type = "HEADER" #Hide this panel? not sure how to hide them...
    #bl_options     = {"DRAW_BOX"}

    @classmethod
    def poll(cls, context):
        return (bpy.context.scene.scatter5.emitter!=None)

    def draw(self, context):
        layout = self.layout

        scat_scene = bpy.context.scene.scatter5
        scat_op = scat_scene.operators.add_psy_preset
        preset_exists = os.path.exists(scat_op.preset_path)

        #Preset Name

        #layout.label(text=translate("No Preset Chosen Yet") if not preset_exists else os.path.basename(scat_op.preset_path),)

        #Emitter

        # layout.separator(factor=0.33)

        # col = layout.column(align=True)
        # txt = col.row()
        # txt.label(text=translate("Emitter")+" :")

        # op = col.operator("scatter5.exec_line",text=translate("Refresh m² Estimation"),icon="SURFACE_NSURFACE",)
        # op.api = "bpy.context.scene.scatter5.emitter.scatter5.estimate_square_area()"
        # op.description = translate("Recalculate Emitter Surface m² Estimation")
        
        #Preset Path 

        layout.separator(factor=0.15)

        col = layout.column(align=True)
        txt = col.row()
        txt.label(text=translate("Active Preset")+" :")
        
        path = col.row(align=True)
        path.alert = not preset_exists
        path.prop(scat_op,"preset_path",text="")
        path.operator("scatter5.open_directory",text="",icon="FILE_TEXT").folder = os.path.join(directories.lib_presets, bpy.context.window_manager.scatter5_preset_gallery +".preset")
            
        #Options 

        col.separator(factor=0.6)

        col = layout.column(align=True)
        col.label(text=translate("Utility")+" :",)

        ui_templates.bool_toggle(col, scat_op, "preset_find_color", label=translate("Use Material Display Color"), use_layout_left_spacer=False,)
        
        col.separator(factor=0.5)

        ui_templates.bool_toggle(col, scat_op, "preset_find_name", label=translate("Use Instance Name"), use_layout_left_spacer=False,)

        #Library 

        col.separator(factor=0.6)

        col = layout.column(align=True)
        txt = col.row()
        txt.label(text=translate("Preset Library")+" :")

        col.operator("scatter5.reload_preset_gallery",text=translate("Reload Preset Library"), )#icon="FILE_REFRESH")

        col.separator()
        col.operator("scatter5.open_directory",text=translate("Open Preset Library"), ).folder = directories.lib_presets #icon="FOLDER_REDIRECT")

        #Create 

        col.separator(factor=0.6)

        col = layout.column(align=True)
        txt = col.row()
        txt.label(text=translate("Create Preset")+" :")

        col.operator("scatter5.export_to_presets", text=translate("New Preset(s) from Selected"),)#icon="CURRENT_FILE")

        col.separator()
        op = col.operator("scatter5.generate_thumbnail",text=translate("Render Active Thumbnail"),)#icon="RESTRICT_RENDER_OFF")
        op.json_path = os.path.join(directories.lib_presets, bpy.context.window_manager.scatter5_preset_gallery +".preset")
        op.render_output = os.path.join(directories.lib_presets, bpy.context.window_manager.scatter5_preset_gallery +".jpg")

        return None


class SCATTER5_PT_per_settings_category_header(bpy.types.Panel):

    bl_idname      = "SCATTER5_PT_per_settings_category_header"
    bl_label       = translate("Settings-Category Header")
    bl_description = translate("In this menu you'll be able to copy/paste settings related to this specific category of settings. You'll be able to batch-apply the current settings to the many system(s), lock/unlock the settings to avoid accidental changes, apply a preset to this category of settings, or restore the settings value to default.")
    bl_category    = ""
    bl_space_type  = "VIEW_3D"
    bl_region_type = "HEADER" #Hide this panel? not sure how to hide them...
    #bl_options     = {"DRAW_BOX"}

    @classmethod
    def poll(cls, context):
        return (bpy.context.scene.scatter5.emitter!=None)

    def draw(self, context):

        layout     = self.layout
        
        from ... __init__ import blend_prefs
        scat_data  = blend_prefs()
        scat_scene = bpy.context.scene.scatter5
        emitter    = scat_scene.emitter
        psys       = emitter.scatter5.particle_systems
        psy_active = emitter.scatter5.get_psy_active()
        psys_sel   = emitter.scatter5.get_psys_selected()

        #Msg if no system 
        if (psy_active is None):
            word_wrap(layout=layout, max_char=34, active=True, string=translate("Settings aren't currently accessible because no System(s) are currently active"), icon="INFO")
            return None

        #Msg if system is linked
        elif (psy_active.is_linked):
            word_wrap(layout=layout, max_char=34, active=True, string=translate("Settings aren't currently accessible because the active system is Read-Only"), icon="LINKED")
            return None
            
        #get UILayout arg
        s_category = context.pass_ui_arg_popover
        if (type(s_category) is not str):
            layout.label(icon="ERROR")
            print(f"ERROR: SCATTER5_PT_per_settings_category_header: context.pass_ui_arg_popover '{s_category}' is not string..")
            return None
        
        is_locked = psy_active.is_locked(s_category)

        #### Category Operators

        col = layout.column(align=True)
        txt = col.row()
        txt.label(text=translate("Operators")+" :")
        operators = col.row(align=True)
        operators.scale_x = 5

        #COPY
        rwoo = operators.row(align=True)
        rwoo.scale_x = 5
        op = rwoo.operator("scatter5.copy_paste_category",text="", icon_value=cust_icon("W_BOARD_COPY"),)
        op.copy = True
        op.single_category = s_category
            
        #PASTE
        rwoo = operators.row(align=True)
        rwoo.scale_x = 5
        rwoo.enabled = is_BufferCategory_filled(s_category)
        op = rwoo.operator("scatter5.copy_paste_category",text="", icon_value=cust_icon("W_BOARD_PASTE"),)
        op.paste = True
        op.single_category = s_category

        #RESET
        rwoo = operators.row(align=True)
        rwoo.scale_x = 5 
        op = rwoo.operator("scatter5.reset_settings",text="", icon="LOOP_BACK")
        op.single_category = s_category

        #APPLY
        rwoo = operators.row(align=True)
        rwoo.scale_x = 5
        op = rwoo.operator("scatter5.apply_category",text="", icon_value=cust_icon("W_BOARD_APPLY"),)
        op.single_category = s_category
        op.pop_dialog = True
            
        #### Lock Unlock

        col = layout.column(align=True)
        txt = col.row()
        txt.label(text=translate("Operators")+" :")
        locking = col.row(align=True)
        locking.scale_x = 2.5

        op = locking.operator("scatter5.exec_line", text="", icon="UNLOCKED", depress=not is_locked)
        op.api = f"psy_active.{s_category}_locked = False"
        op.description = translate("Lock/unlock the selected scatter-system(s).\nOnce locked, it will not be possible to interact with their scatter-settings in the interface. Additionally, any potential update signals will be denied of reaching the geometry node scatter-engine.")
        op.undo = translate("Lock/unlock scatter-system(s)")

        op = locking.operator("scatter5.exec_line", text="", icon="LOCKED", depress=is_locked )
        op.api = f"psy_active.{s_category}_locked = True"
        op.description = translate("Lock/unlock the selected scatter-system(s).\nOnce locked, it will not be possible to interact with their scatter-settings in the interface. Additionally, any potential update signals will be denied of reaching the geometry node scatter-engine.")
        op.undo = translate("Lock/unlock scatter-system(s)")

        #### Category Reset/Preset 

        col = layout.column(align=True)
        txt = col.row()
        txt.label(text=translate("Presets")+" :")
        row = col.row(align=True)
        row.menu("SCATTER5_MT_preset_menu_header", text=translate("Apply a Preset"),)

        #### Category Synchronization

        #INFO note that mask is currently not supported by synchronization feature currently in 5.1 release
        if (scat_data.factory_synchronization_allow and psy_active.is_synchronized(s_category)):
            
            col = layout.column(align=True)
            txt = col.row()
            txt.label(text=translate("Settings Synchronized")+" :")

            lbl = layout.row()
            lbl.alert = True
            ch = [ch for ch in scat_data.sync_channels if ch.psy_settings_in_channel(psy_active.name, s_category,)][0]
            lbl.prop(ch,s_category,text=translate("Disable Synchronization"),icon_value=cust_icon("W_ARROW_SYNC"), invert_checkbox=True,)

        #### Special Operators

        if ((s_category=="s_distribution") and (psy_active.s_distribution_method!="manual_all")):

            #Export to manual 

            col = layout.column(align=True)
            txt = col.row()
            txt.label(text=translate("Manual Edition")+" :")

            ope = col.row()
            ope.operator_context = "INVOKE_DEFAULT"
            ope.operator("scatter5.export_psy_to_manual", text=translate("Convert to Manual Distribution"), icon="FILTER").use_active = True

        if (s_category=="s_display"):

            #Visualize

            col = layout.column(align=True)
            txt = col.row()
            txt.label(text=translate("Display Color")+" :")

            ope = col.row()
            condition = (bpy.context.space_data.shading.type == 'SOLID') and (bpy.context.space_data.shading.color_type == 'OBJECT')
            op = ope.operator("scatter5.set_solid_and_object_color",text=translate("Set Viewport Display Colors"), icon="COLOR", depress=condition)
            op.mode = "restore" if condition else "set"

        if (s_category in ("s_display","s_instances",)):

            #Bounding Box

            col = layout.column(align=True)
            txt = col.row()
            txt.label(text=translate("Object(s) Bounding-Box")+" :")

            ope = col.row()
            condition = (bpy.context.space_data.shading.type == 'SOLID') and (bpy.context.space_data.shading.color_type == 'OBJECT')
            op = ope.operator("scatter5.batch_bounding_box",text=translate("Toggle Bounding-Box"), icon="CUBE",)
            op.emitter_name = emitter.name
            op.psy_name = psy_active.name

        layout.separator(factor=0.3)

        return None


class SCATTER5_PT_add_environment(bpy.types.Panel):
    
    bl_idname      = "SCATTER5_PT_add_environment"
    bl_label       = ""
    bl_category    = ""
    bl_space_type  = "VIEW_3D"
    bl_region_type = "HEADER" #Hide this panel? not sure how to hide them...
    #bl_options     = {"DRAW_BOX"}

    def draw(self, context):
        layout = self.layout

        scat_addon = addon_prefs()

        col = layout.column(align=True)
        col.label(text=translate("Additional Settings:"))
        col.prop(scat_addon,"blend_environment_search_cache_system")
        col.separator(factor=0.7)
        col.prop(scat_addon,"blend_environment_search_depth")
        
        return None


class SCATTER5_PT_mask_header(bpy.types.Panel):

    bl_idname      = "SCATTER5_PT_mask_header"
    bl_label       = ""
    bl_category    = ""
    bl_space_type  = "VIEW_3D"
    bl_region_type = "HEADER" #Hide this panel? not sure how to hide them...
    #bl_options     = {"DRAW_BOX"}

    @classmethod
    def poll(cls, context):
        return (bpy.context.scene.scatter5.emitter!=None)

    def draw(self, context):
        layout = self.layout

        scat_scene = bpy.context.scene.scatter5
        emitter = scat_scene.emitter

        col = layout.column()
        txt = col.row()
        txt.label(text=translate("Mask-Data :"))
        prp = col.row()
        prp.operator("scatter5.refresh_every_masks",text=translate("Recalculate All Masks"),icon="FILE_REFRESH")
        
        return None


class SCATTER5_PT_graph_subpanel(bpy.types.Panel):

    bl_idname      = "SCATTER5_PT_graph_subpanel"
    bl_label       = ""
    bl_category    = ""
    bl_space_type  = "VIEW_3D"
    bl_region_type = "HEADER" #Hide this panel? not sure how to hide them...
    #bl_options     = {"DRAW_BOX"}

    @classmethod
    def poll(cls, context):
        return (bpy.context.scene.scatter5.emitter!=None)

    def draw(self, context):
        layout = self.layout

        #get UILayout arg
        dialog = context.pass_ui_arg_popover
        if ("SCATTER5_OT_graph_dialog" not in str(dialog)):
            layout.label(icon="ERROR")
            print(f"ERROR: SCATTER5_PT_graph_subpanel: context.pass_ui_arg_popover '{dialog}' is not of class SCATTER5_OT_graph_dialog..")
            return None
        
        #Copy/Paste

        layout.label(text=translate("Graph Copy/Paste")+" :")

        row = layout.row(align=True)

        ope = row.row(align=True)
        ope.scale_x = 5
        op = ope.operator("scatter5.graph_copy_preset", text="", icon_value=cust_icon("W_BOARD_COPY"),)
        op.source_api=dialog.source_api
        op.mapping_api=dialog.mapping_api
        op.copy=True
        
        ope = row.row(align=True)
        ope.scale_x = 5
        from .. curve.fallremap import BUFFER_GRAPH_PRESET
        ope.enabled = (BUFFER_GRAPH_PRESET is not None)
        op = ope.operator("scatter5.graph_copy_preset", text="", icon_value=cust_icon("W_BOARD_PASTE"),)
        op.source_api=dialog.source_api
        op.mapping_api=dialog.mapping_api
        op.paste=True

        #Apply Selected, only for scatter-systems

        if (".nodes[" in dialog.source_api):
            
            ope = row.row(align=True)
            ope.scale_x = 5
            op = ope.operator("scatter5.graph_copy_preset", text="", icon_value=cust_icon("W_BOARD_APPLY"),)
            op.source_api=dialog.source_api
            op.mapping_api=dialog.mapping_api
            op.apply_selected=True

        #other options

        layout.label(text=translate("Widgets Defaults")+" :")

        col = layout.column(align=True)
        col.prop(dialog,"op_move")
        col.prop(dialog,"op_size")

        return None

#   .oooooo.                             .                             .        oooooooooo.
#  d8P'  `Y8b                          .o8                           .o8        `888'   `Y8b
# 888           .ooooo.  ooo. .oo.   .o888oo  .ooooo.  oooo    ooo .o888oo       888      888  .ooooo.   .ooooo.   .oooo.o
# 888          d88' `88b `888P"Y88b    888   d88' `88b  `88b..8P'    888         888      888 d88' `88b d88' `"Y8 d88(  "8
# 888          888   888  888   888    888   888ooo888    Y888'      888         888      888 888   888 888       `"Y88b.
# `88b    ooo  888   888  888   888    888 . 888    .o  .o8"'88b     888 .       888     d88' 888   888 888   .o8 o.  )88b
#  `Y8bood8P'  `Y8bod8P' o888o o888o   "888" `Y8bod8P' o88'   888o   "888"      o888bood8P'   `Y8bod8P' `Y8bod8P' 8""888P'



class SCATTER5_PT_docs(bpy.types.Panel):

    bl_idname      = "SCATTER5_PT_docs"
    bl_label       = translate("Documentation Panel")
    bl_description = translate("Click to open a short description about this panel and its features")
    bl_category    = ""
    bl_space_type  = "VIEW_3D"
    bl_region_type = "HEADER" #Hide this panel? not sure how to hide them...
    #bl_options     = {"DRAW_BOX"}

    txt_block_op_behavior = translate("Optionally, you can change the behavior of the operator by clicking on the icon next to the operator button. The goal of this 'On Creation' menu is to tweak the operator default behavior. You can for example directly paint masks, set-up optimization features, or define your future surface(s).")
    txt_block_feature_hover = translate("Please, hover your mouse cursor on the feature toggle of your choice to read each feature description.")
    txt_block_disinfo = translate("This distribution method has an impact on the workflow, please pay attention to the following information:")
    txt_block_grinfo = translate("Info: You are currently looking at a 'group' feature. Group settings will apply to all scatters being part of this group. If you'd like to tweak individual scatter-system settings, select a system in the system lister, you'll have many more settings and features to choose from.\n\nPro-Tip: If you'd like to batch apply settings to many scatter systems, this can also be done on a scatter-system leve via the 'Alt for batch' functionality of our plugin. Learn about it in our documentation, see 'Prerequisite'>'Batch Operation' page.")

    documentation_dict = {
        #Creation Panel
        "ui_create_densit" : { 
            "text": translate("Scatter the selected objects located in your viewport or in your asset browser with the chosen density per square area in the chosen unit scale.\n(Please note that our plugin and Blender default unit is in meter, and your chosen density will be converted to /m² automatically).")+"\n\n"+txt_block_op_behavior,
            "url" : "https://www.geoscatter.com/documentation.html#FeatureScattering&section_density_scatter",
            "url_title":translate("Online Manual"),
            },
        "ui_create_preset" : { 
            "text": translate("Scatter the selected objects located in your viewport or in your asset browser with the chosen preset. Preset files are storing scatter-system settings information, you can create and render your own presets in the header menu if needed, click on the gear icon to open this menu.")+"\n\n"+txt_block_op_behavior,
            "url" : "https://www.geoscatter.com/documentation.html#FeatureScattering&section_preset_scatter",
            "url_title":translate("Online Manual"),
            },
        "ui_create_manual" : { 
            "text": translate("Scatter the selected objects located in your viewport or in your asset browser and directly enter the manual distribution workflow. Manual-mode is an entirely new scattering experience, you can precisely place / move / rescale / rotate instances with a subset of various brushes.")+"\n\n"+translate("Optionally, you can change the behavior of this operator in the 'On Creation' popover menu right next to the operator button."), 
            "url" : "https://www.geoscatter.com/documentation.html#FeatureScattering&section_manual_scatter",
            "url_title":translate("Online Manual"),
            },
        "ui_create_quick" : { 
            "text": translate("The 'Quick Scatter' operator allows you to quickly create scatters from a pie menu and modal shortcut-based operators that can be called from a keyboard shortcut (by default 'SHIFT+CTRL+ALT+W', change the shortcut in the popover menu below).\n\nYou are able to either scatter the selected objects in the viewport or in the asset browser depending on where your mouse cursor was located when you executed the shortcut.")+"\n\n"+translate("Optionally, you can change the behavior of this operator in the 'On Creation' popover menu right next to the operator button."),
            "url" : "https://www.geoscatter.com/documentation.html#FeatureScattering&section_quick_scatter",
            "url_title":translate("Online Manual"),
            },
        "ui_create_biomes" : { 
            "text": translate("Open your biome library from where you can load new biomes onto your chosen surfaces. Our biome-system will first load the assets in your .blend file, then scatter them according to each biome preset layers.\n\nYou can create your own biomes at any moment, from the biome interface header menu or from the export panel.")+"\n\n"+txt_block_op_behavior+" "+translate("Note that this menu is also available in the biome interface header."),
            "url" : "https://www.geoscatter.com/documentation.html#FeatureScattering&section_biome_scatter",
            "url_title":translate("Online Manual"),
            },
        #Tweaking Panel
        "ui_tweak_select" : { 
            "text": translate("Select or set active your scatter-system or system-group in the interface below. Once a scatter-system or a group is set active, you will be able to access their scatter or group properties.\n\nYou can select multiple scatter-system(s) in order to batch tweak properties. Batch tweaks can be done by pressing the 'ALT' key while changing the value of any settings, toggles or pointers. While pressing 'ALT' you will apply the new property value to all selected system(s) simultaneously.\n\nPro-Tip: If you are doing a lot of back and forths between settings and the list, we advise you to close this panel and use instead the larger 'Lister' interface of the plugin manager, or use the 'Quick-Lister' shortcut (by default 'SHIFT+CTRL+Q').\n\nPro-Tip: pressing the 'ALT' or 'SHIFT' key while clicking on a system will isolate or add the selection."), 
            "url" : "https://www.geoscatter.com/documentation.html#FeatureScattering&section_list_interfaces",
            "url_title":translate("Online Manual"),
            },
        "s_surface" : { 
            "text": translate("Define the surface(s) you will distribute your instances upon.\n\nIf you choose to scatter on multiple surfaces, make sure that the UV(s), vertex-color(s) or vertex-group(s) attributes are shared across all surfaces. If an attribute isn't shared across all their surfaces, their contextual pointers will be highlighted in red.\n\nBy default, any new scatters will use the emitter mesh as default surface. You are able to define the default-surface(s) before their creation in the 'Create' panel 'On Creation' popover menu located next to each scatter operator buttons."), 
            "url" : "https://www.geoscatter.com/documentation.html#FeatureScattering&section_surfaces",
            "url_title":translate("Online Manual"),
            },
        "s_distribution" : { 
            "text": translate("Choose between a variety of distribution algorithms and define their distribution properties.\n\nPlease, hover on the distribution method of your choice to read their full description.\n\nInfo: Behind the scenes, we will first distribute points, then the activated features will either cull or change the rotation/scale attributes of these points, then finally, the points will be assigned instances depending on their instancing ID attributes"),
            "url" : "https://www.geoscatter.com/documentation.html#FeatureDistribution",
            "url_title":translate("Online Manual"),
            },
        "s_mask" : { 
            "text": translate("Remove your scattered instances non-destructively with the help of various masking features.")+"\n\n"+translate("Note that masks based on the topology of your surface(s) will be faster to compute as most distribution algorithm will only distribute on those areas. Other culling features will first distribute points, and cull them afterwards, on a second stage.")+"\n\n"+txt_block_feature_hover,
            "url" : "https://www.geoscatter.com/documentation.html#FeatureCullingmask",
            "url_title":translate("Online Manual"),
            },
        "s_scale" : { 
            "text": translate("Have complete control over the scale of your instances with the help of various scale features.")+"\n\n"+txt_block_feature_hover,
            "url" : "https://www.geoscatter.com/documentation.html#FeatureScale",
            "url_title":translate("Online Manual"),
            },
        "s_rot" : { 
            "text": translate("Have complete control over your instances orientations using various rotation and alignment techniques.\n\nIn Geo-Scatter you can either choose to have an influence over the existing XYZ rotation angles, or have an influence over the rotation componement, being the normal (+Z) or tangent (+Y) axis of the instances.")+"\n\n"+txt_block_feature_hover,
            "url" : "https://www.geoscatter.com/documentation.html#FeatureRotation",
            "url_title":translate("Online Manual"),
            },
        "s_pattern" : { 
            "text": translate("Influence your distribution density and the scale of your instances via an existing or newly created texture data-block.\n\n'Scatter Texture-Data' are re-usable datablocks similar to the now obsolete blender textures-data. You are able to create a variety of procedural textures, define how they are projected on your scatters, change their settings and colors. Optionally you can load images and have access to a default image library of useful patterns.\n\nTo access the scatter texture-data properties, click on the little 'parameter' icon right next to a texture name."), 
            "url" : "https://www.geoscatter.com/documentation.html#FeaturePattern",
            "url_title":translate("Online Manual"),
            },
        "s_abiotic" : { 
            "text": translate("The abiotic factors are all factors related to the topology of the mesh you are scattering upon. Use these factors to influence your distribution density or your instances scale.")+"\n\n"+txt_block_feature_hover, 
            "url" : "https://www.geoscatter.com/documentation.html#FeatureAbiotic",
            "url_title":translate("Online Manual"),
            },
        "s_proximity" : { 
            "text": translate("Influence your distribution density, orientation or scale depending on their proximity to chosen objects.\n\nPro Tip: You are also able to add curve objects as well in the chosen collection of the object-repel feature.")+"\n\n"+txt_block_feature_hover, 
            "url" : "https://www.geoscatter.com/documentation.html#FeatureProximity",
            "url_title":translate("Online Manual"),
            },
        "s_ecosystem" : { 
            "text": translate("Ecosystems give you the ability of defining relationship rules in-between your scatter-system(s) that can influence your distribution density or your instances scale.")+"\n\n"+txt_block_feature_hover,
            "url" : "https://www.geoscatter.com/documentation.html#FeatureEcosystem",
            "url_title":translate("Online Manual"),
            },
        "s_push" : { 
            "text": translate("Offset your instances positions using various displacement techniques.")+"\n\n"+txt_block_feature_hover, 
            "url" : "https://www.geoscatter.com/documentation.html#FeatureOffset",
            "url_title":translate("Online Manual"),
            },
        "s_wind" : { 
            "text": translate("Create the illusion of a wind by tilting your instances rotations.\n\nThese features will not interact with the mesh of your instances, it will only rotate them on their side following an animated 'Tilting' motion")+"\n\n"+txt_block_feature_hover,
            "url" : "https://www.geoscatter.com/documentation.html#FeatureWind",
            "url_title":translate("Online Manual"),
            },
        "s_visibility" : {
            "text": translate("Control how many instances are visible in the viewport with the help of various optimization tricks.\n\nThese features can help showing less triangle on screen, but also lower the calculation load of the distribution algorithms used by your scatters")+"\n\n"+txt_block_feature_hover,
            "url" : "https://www.geoscatter.com/documentation.html#FeatureOptimization",
            "url_title":translate("Online Manual"),
            },
        "s_instances" : { 
            "text": translate("Choose how your instances are assigned to the distributed points.")+"\n\n"+translate("Pro-Tip: If you are unsure how to retrieve the objects used as instances in your file, alt-click on the select icon next to the instance names"), 
            "url" : "https://www.geoscatter.com/documentation.html#FeatureInstancing",
            "url_title":translate("Online Manual"),
            },
        "s_display" : { 
            "text": translate("Replace high-poly objects to simpler placeholders (like boxes or low-poly shapes) to reduce on-screen triangles and prevent navigation lag.\n\nEevee, Game-engines, or the workbench 3Dviewport, all use a rendering technique called 'Rasterization' where performance scales with triangle count.\n\nPro-Tip: Performances of ray-tracers like Cycles aren't affected by triangles quantity, but Blender viewport overlay's still is, and the 'Auto-Depth' navigation orbit setting will too."),
            "url" : "https://www.geoscatter.com/documentation.html#FeatureOptimization&section_display_as",
            "url_title":translate("Online Manual"),
            },
        #Extra Panel
        "ui_extra_displace" : { 
            "text": translate("Quickly add displacement effects to the active object"), 
            "url" : "",
            "url_title":"",
            },
        "ui_extra_vgs" : { 
            "text": translate("Generate useful vertex-data masks, either to influence your scatter, your shaders, or else..\n\nNote that this feature might be removed in the near future to become its own standalone plugin"), 
            "url" : "",
            "url_title": "",
            },
        "ui_extra_masterseed" : { 
            "text": translate("The master seed influences every other Geo-Scatter seed in this .blend, increment this seed to iterate between various scattering possibilities non-destructively."), 
            "url" : "https://www.geoscatter.com/documentation.html#FeatureExtra&article_master_seed",
            "url_title":translate("Online Manual"),
            },
        "ui_extra_synch" : { 
            "text": translate("Synchronize the scattering settings of the chosen scatter-system(s).\n\nHow to use: create a synchronization channel, add system(s) to the channel, and define which settings categories are affected.\n\nChanging the value of one system will automatically apply the values to all systems in the channel."),
            "url" : "https://www.geoscatter.com/documentation.html#FeatureExtra&article_synchronization",
            "url_title":translate("Online Manual"),
            },
        "ui_extra_update" : { 
            "text": translate("Few controls update behavior controls.")+"\n\n"+txt_block_feature_hover, 
            "url" : "https://www.geoscatter.com/documentation.html#FeatureOptimization&section_slider_reactivity",
            "url_title":translate("Online Manual"),
            },
        "ui_extra_export" : { 
            "text": translate("Export or convert the selected-system(s) to various object types or instancing format."), 
            "url" : "https://www.geoscatter.com/documentation.html#FeatureExtra&article_export_to_json",
            "url_title":translate("Online Manual"),
            },
        "ui_extra_animation_data" : { 
            "text": translate("Geo-Scatter is supporting animation of most of its plugin properties via Drivers or Keyframe . In the following interface we will overview all animation-data encoded with any of our plugin properties.\n\nPlease note that this support is only available when the plugin is activated. If you'd like to animate properties for a render node with no plugin installed, it would be better to animate Geo-scatter geometry-node engine nodetree directly."), 
            "url" : "",
            "url_title":"",
            },
        #Addon prefs popover
        "ui_add_packs" : { 
            "text": translate("ScatPacks are premade libraries containing biomes, presets or assets ready to be used within our plugin. A scatpack format should end with the extension '.scatpack'.\n\nPlease note that some asset-makers might store their assets outside of our plugin scatter-library, if this is the case, you may need to install assets in your blender asset browser.\n\nAnyone is free to create his own biome pack! You can make your own '.scatpack' by renaming a compressed .zip extension. The content of the zip should respect the '_presets_'/'_biomes_' folder hierarchy. Be careful to only share what is yours & respect assets licenses!"),
            "url" : "https://www.geoscatter.com/documentation.html#FeatureInstallation",
            "url_title":translate("Online Manual"),
            },
        "ui_add_environment" : { 
            "text": translate("Most biome pack makers do not store their assets directly in the '.scatpack', their scatpacks might not contain any .blend files!\n\nIf this is the case, you will need to make sure that the .blend files related to the biomes can be found in the list(s) below."), 
            "url" : "https://www.geoscatter.com/documentation.html#FeatureInstallation&article_define_environment_paths",
            "url_title":translate("Online Manual"),
            },
        "ui_add_paths" : { 
            "text": translate("Change the default location of your scatter-library.\n\nThe scatter-library contains all your biomes, your presets & more."), 
            "url" : "https://www.geoscatter.com/documentation.html#FeatureInstallation&section_manage_your_scatter_library",
            "url_title":translate("Online Manual"),
            },
        "ui_add_browser" : { 
            "text": translate("Our scattering plugin works flawlessly with the blender asset browser, as you can directly Scatter the selected Assets. It might be worth it to also install your assets as an asset-browser library. This is done in the blender preferences editor ‘File Paths’.\n\nIf your pack does not support blender asset browser, you can automatically convert many blends of a given folder to asset-ready blends with the operator below."), 
            "url" : "https://www.geoscatter.com/documentation.html#FeatureInstallation&section_don_t_have_the_time_to_read_",
            "url_title":translate("Online Manual"),
            },
        "ui_add_workflow" : { 
            "text": translate("Change some default behaviors about the plugin"), 
            "url" : "https://www.geoscatter.com/documentation.html#FeatureScattering&article_switching_emitter_s",
            "url_title":translate("Online Manual"),
            },
        #Get flowmap painter info
        "get_flowmap" : { 
            "text": translate("A flowmap is a color information used in 3D graphics to control the direction and speed of movement on a surface (like simulating water, wind, or defining an orientation).\n\nThe directions (initially ranging from '1' to '-1') are stored as colors: the Red and Green channels hold the X and Y movement information, ranging from '0' to '1'. The Blue channel is usually unused in this context because we are working in tangent space, which only deals with directions within the surface itself. As the Blues are unused, it can be utilized as additional information such as a 'strength' map for example.\n\nSadly flowmaps cannot be created natively in Blender color painting tools. You'll need to download the 'Flowmap-painter' addon by Clemens Beute on Gumroad and use his addon in Vertex-paint while using the 'UV Space color' option if you'd like to create your own flowmaps."),
            "url" : "https://www.blendernation.com/2021/03/03/free-flow-map-painter-addon/",
            "url_title":translate("Flowmap Painter"),
            },
        #Features based on camera 
        "nocamera_info" : { 
            "text": translate("This functionality relies on the active camera, but an active camera can't be found in this scene.\n\nPlease add a camera, or disable this feature"), 
            "url" : "",
            "url_title":"",
            },
        #distribution availability
        "distinfos_clumping" : {
            "text": txt_block_disinfo+"\n\n"+translate("Some exclusive feature(s) are available for this method:\n• Clump Scale Influence\n• Clump Normal Influence"),
            "url" : "https://www.geoscatter.com/documentation.html#FeatureDistribution&section_clump_distribution",
            "url_title":translate("About Distribution"),
            },
        "distinfos_faces" : {
            "text": txt_block_disinfo+"\n\n"+translate("Some exclusive feature(s) are available for this method:\n• Face Size Influence"),
            "url" : "https://www.geoscatter.com/documentation.html#FeatureDistribution&section_mesh_element_distribution",
            "url_title":translate("About Distribution"),
            },
        "distinfos_edges" : {
            "text": txt_block_disinfo+"\n\n"+translate("Some exclusive feature(s) are available for this method:\n• Edge Length Influence"),
            "url" : "https://www.geoscatter.com/documentation.html#FeatureDistribution&section_mesh_element_distribution",
            "url_title":translate("About Distribution"),
            },
        "distinfos_volume" : {
            "text": txt_block_disinfo+"\n\n"+translate("Some feature(s) are not Available:\n• Mask>Vertex Group\n• Mask>Color-Attribute\n• Mask>Image\n• Mask>Material\n• Abiotic>Slope\n• Abiotic>Orientation\n• Abiotic>Curvature\n• Abiotic>Border\n• Visibility>Area-Preview\n\nAdditional Information:\n• Features relying on UV space or vertex-attributes will be inconsistent"),
            "url" : "https://www.geoscatter.com/documentation.html#FeatureDistribution&section_volume_distribution",
            "url_title":translate("About Distribution"),
            },
        "distinfos_manual" : {
            "text": txt_block_disinfo+"\n\n"+translate("Please be aware that all the features from the procedural workflow still apply on the points generated by manual-mode. The procedural features can impact your manual-distribution on their rotation/scale and can actually mask some areas of your distribution as well."),
            "url" : "https://www.geoscatter.com/documentation.html#FeatureDistribution&section_manual_distribution",
            "url_title":translate("About Distribution"),
            },
        "distinfos_projbezarea" : {
            "text": txt_block_disinfo+"\n\n"+translate("Some exclusive feature(s) are available for this method:\n• Proximity>Bezier-Area Border\n\nSome features/options relying on surface(s) will not be available/working when the 'Project on Surface(s)' option is turned off."),
            "url" : "https://www.geoscatter.com/documentation.html#FeatureDistribution&section_bezier_area_distribution",
            "url_title":translate("About Distribution"),
            },
        "distinfos_projbezline" : {
            "text": txt_block_disinfo+"\n\n"+translate("Some exclusive feature(s) are available for this method:\n• Scale>Spline Radius Influence\n\nSome features/options relying on surface(s) will not be available/working when the 'Project on Surface(s)' option is turned off."),
            "url" : "https://www.geoscatter.com/documentation.html#FeatureDistribution&section_bezier_spline_distribution",
            "url_title":translate("About Distribution"),
            },
        "distinfos_projempties" : {
            "text": txt_block_disinfo+"\n\n"+translate("Some exclusive feature(s) are available for this method:\n• Scale>Empties Scale Influence\n\nSome features/options relying on surface(s) will not be available/working when the 'Project on Surface(s)' option is turned off."),
            "url" : "https://www.geoscatter.com/documentation.html#FeatureDistribution&section_empties_distribution",
            "url_title":translate("About Distribution"),
            },
        #Beginner interface explanations
        "s_beginners_remove" : {
            "text": translate("The Geo-Scatter Plugin has a lot more features! And some are much more advanced than others!\n\nThe Biome-Reader interface is designed for beginners, access to these advanced features can be achieved with our Geo-Scatter plugin.\n\nIn the meanwhile, you can disable some Features in this panel."),
            "url" : "",
            "url_title":"",
            },
        #group category features Explanations
        "s_gr_distribution" : {
            "text": translate("This category of features is dedicated to influencing the distribution of the scatter-system(s) member of this group.")+"\n\n"+txt_block_grinfo,
            "url" : "https://www.geoscatter.com/documentation.html#FeatureScattering&section_scatter_groups",
            "url_title":translate("About Group Features"),
            },
        "s_gr_mask" : {
            "text": translate("This category of features is dedicated to masking the density of all scatter-system(s) members of this group.")+"\n\n"+txt_block_grinfo,
            "url" : "https://www.geoscatter.com/documentation.html#FeatureScattering&section_scatter_groups",
            "url_title":translate("About Group Features"),
            },
        "s_gr_scale" : {
            "text": translate("This category of features is dedicated to influencing the scale of the instances of the scatter-system(s) member of this group.")+"\n\n"+txt_block_grinfo,
            "url" : "https://www.geoscatter.com/documentation.html#FeatureScattering&section_scatter_groups",
            "url_title":translate("About Group Features"),
            },
        "s_gr_pattern" : {
            "text": translate("This category of features is dedicated to influencing the density or scale of all scatter-system(s) members of this group with the help of a scatter-texture data-block.")+"\n\n"+txt_block_grinfo,
            "url" : "https://www.geoscatter.com/documentation.html#FeatureScattering&section_scatter_groups",
            "url_title":translate("About Group Features"),
            },
        }

    def draw(self, context):
        layout = self.layout

        doc_key = context.pass_ui_arg_popover
        if (type(doc_key) is not str):
            layout.label(icon="ERROR")
            print(f"ERROR: SCATTER5_PT_docs: context.pass_ui_arg_popover '{doc_key}' is not string..")
            return None
        
        doc = self.documentation_dict.get(doc_key)
        if (doc is None):
            layout.label(icon="ERROR")
            print(f"ERROR: SCATTER5_PT_docs: '{doc_key}' not found in doc dictionary")
            return None
        
        doc_txt, doc_url, doc_url_tit = doc.get("text"), doc.get("url"), doc.get("url_title")
        
        if (doc_txt is None):
            layout.label(icon="ERROR")
            print(f"ERROR: SCATTER5_PT_docs: doc['text'] not found for '{doc_key}'")
            return None
        
        #write documentation text
        word_wrap(layout=layout, active=True, max_char=35, scale_y=0.875, string=doc_txt, alignment="LEFT")

        #doc has link to click on?
        if (doc_url is not None) and (doc_url_tit is not None) and (doc_url!=""):
            layout.separator()
            layout.operator("wm.url_open", text=doc_url_tit, icon="URL",).url = doc_url

        return None


#   .oooooo.             oooo  oooo       ooooo     ooo     .    o8o  oooo   o8o      .
#  d8P'  `Y8b            `888  `888       `888'     `8'   .o8    `"'  `888   `"'    .o8
# 888           .ooooo.   888   888        888       8  .o888oo oooo   888  oooo  .o888oo oooo    ooo
# 888          d88' `88b  888   888        888       8    888   `888   888  `888    888    `88.  .8'
# 888          888   888  888   888        888       8    888    888   888   888    888     `88..8'
# `88b    ooo  888   888  888   888        `88.    .8'    888 .  888   888   888    888 .    `888'
#  `Y8bood8P'  `Y8bod8P' o888o o888o         `YbodP'      "888" o888o o888o o888o   "888"     .8'
#                                                                                         .o..P'
#                                                                                         `Y8P'


class SCATTER5_UL_list_collection_utility(bpy.types.UIList):
    """selection area"""

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
            
        row  = layout.row(align=True)
        
        #show name label
        
        if ((item.library) or (item.data and item.data.library)):
              row.label(text=item.name, icon="LINKED")
        else: row.prop(item,"name", text="", emboss=False, icon="OUTLINER_OB_EMPTY" if (item.type=='EMPTY') else "OUTLINER_OB_CURVE" if (item.type=='CURVE') else "OUTLINER_OB_MESH")

        #select operator 

        selct = row.row()

        if (bpy.context.mode=="OBJECT"):

            selct.active = (item==bpy.context.object)
            op = selct.operator("scatter5.select_object", emboss=False, text="",icon="RESTRICT_SELECT_OFF" if (item in bpy.context.selected_objects) else "RESTRICT_SELECT_ON")
            op.obj_session_uid = item.session_uid
            op.coll_name = context.pass_ui_arg_collptr.name
        
        else:
            selct.separator(factor=1.2)

        #remove operator 
        
        ope = row.row(align=False)
        ope.scale_x = 0.9
        op = ope.operator("scatter5.remove_from_coll", emboss=False, text="", icon="TRASH",)
        op.obj_session_uid = item.session_uid
        op.coll_name = context.pass_ui_arg_collptr.name
        op.coll_api = context.pass_ui_arg_collapi

        return None


class SCATTER5_PT_collection_popover(bpy.types.Panel):
    """popover only used by draw_coll_str_ptr()"""

    bl_idname      = "SCATTER5_PT_collection_popover"
    bl_label       = translate("Easy Collection Access")
    bl_description = translate("Quickly and easily add or remove objects from a collection")
    bl_category    = ""
    bl_space_type  = "VIEW_3D"
    bl_region_type = "HEADER" #Hide this panel? not sure how to hide them...
    #bl_options     = {"DRAW_BOX"}

    def __init__(self, *args, **kwargs):
        """generate collection breadcrumbs information when calling gui"""
        
        super().__init__(*args, **kwargs)

        self.coll = bpy.context.pass_ui_arg_collptr

        #get breadcrumbs information 
        
        def get_collection_path(collection=None, path=[]):
            for c in bpy.context.scene.collection.children_recursive:
                if (collection.name in c.children):
                    path.insert(0, c.name)
                    get_collection_path(collection=c, path=path)
                    break 
            return path 

        self.breadcrumbs = get_collection_path(collection=self.coll, path=[])
        self.breadcrumbs.insert(0, bpy.context.scene.collection.name)
        self.breadcrumbs.append(self.coll.name)

        return None 

    def draw_breadcrumbs(self, layout):

        col = layout.box().column(align=True)
        col.scale_y = 0.9
        
        for i,name in enumerate(self.breadcrumbs):
            
            is_first = (i==0)
            is_last = (i==len(self.breadcrumbs)-1)
            
            row = col.row(align=True)
            row.alignment = "LEFT"
                
            #intendation
            if (not is_first):
               row.separator(factor=i*0.7)
            
            row.label(text="", icon="DISCLOSURE_TRI_DOWN" if (i!=len(self.breadcrumbs)-1) else "DISCLOSURE_TRI_RIGHT")
            row.label(text=name, icon="OUTLINER_COLLECTION")

        return None 

    def draw(self, context):
        layout = self.layout

        self.draw_breadcrumbs(layout)

        layout.template_list("SCATTER5_UL_list_collection_utility", "", self.coll, "objects", context.window_manager.scatter5, "dummy_idx", type="DEFAULT", rows=4,)

        ope = layout.row()
        op = ope.operator("scatter5.add_to_coll", text=translate("Add Viewport Selection"), icon="ADD")
        op.coll_name = self.coll.name
        op.coll_api = context.pass_ui_arg_collapi

        return None


#   .oooooo.                                    .    o8o                              .oooooo..o               .       .    o8o
#  d8P'  `Y8b                                 .o8    `"'                             d8P'    `Y8             .o8     .o8    `"'
# 888          oooo d8b  .ooooo.   .oooo.   .o888oo oooo   .ooooo.  ooo. .oo.        Y88bo.       .ooooo.  .o888oo .o888oo oooo  ooo. .oo.    .oooooooo  .oooo.o
# 888          `888""8P d88' `88b `P  )88b    888   `888  d88' `88b `888P"Y88b        `"Y8888o.  d88' `88b   888     888   `888  `888P"Y88b  888' `88b  d88(  "8
# 888           888     888ooo888  .oP"888    888    888  888   888  888   888            `"Y88b 888ooo888   888     888    888   888   888  888   888  `"Y88b.
# `88b    ooo   888     888    .o d8(  888    888 .  888  888   888  888   888       oo     .d8P 888    .o   888 .   888 .  888   888   888  `88bod8P'  o.  )88b
#  `Y8bood8P'  d888b    `Y8bod8P' `Y888""8o   "888" o888o `Y8bod8P' o888o o888o      8""88888P'  `Y8bod8P'   "888"   "888" o888o o888o o888o `8oooooo.  8""888P'
#                                                                                                                                            d"     YD
#                                                                                                                                            "Y88888P'

def creation_operators_draw_visibility(layout, hide_viewport=True, facepreview_allow=True, view_allow=True, cam=True, maxload=True,):

    scat_scene   = bpy.context.scene.scatter5
    emitter      = scat_scene.emitter
    scat_op_crea = scat_scene.operators.create_operators

    #Hide on Creation 
    
    if (hide_viewport):
        ui_templates.bool_toggle(layout, scat_op_crea, "f_visibility_hide_viewport", label=translate("Set “Hide Viewport”"),)

    #Viewport % Reduction 

    if (view_allow):

        tocol, is_toggled = ui_templates.bool_toggle(layout, scat_op_crea, "f_visibility_view_allow", 
            label=translate("Set “Reduce Density”"), 
            return_sublayout=True,
            )
        if is_toggled:

            prop = tocol.column(align=True)
            prop.scale_y = 0.9
            prop.prop(scat_op_crea,"f_visibility_view_percentage",)

            tocol.separator(factor=0.2)

    #Maximal Load

    if (maxload): 

        tocol, is_toggled = ui_templates.bool_toggle(layout, scat_op_crea, "f_visibility_maxload_allow", 
            label=translate("Set “Max Amount”"),
            return_sublayout=True,
            )
        if is_toggled:

            subcol = tocol.column(align=True)
            subcol.scale_y = 0.95
            enum = subcol.row(align=True) 
            enum.prop(scat_op_crea, "f_visibility_maxload_cull_method", expand=True)
            subcol.prop(scat_op_crea, "f_visibility_maxload_treshold")

    #Face preview 
    
    if (facepreview_allow): 

        tocol, is_toggled = ui_templates.bool_toggle(layout, scat_op_crea, "f_visibility_facepreview_allow", 
            label=translate("Set “Preview Area”"), 
            return_sublayout=True,
            )
        if is_toggled:

            subcol = tocol.column(align=True)
            subcol.scale_y = 0.90
            opsurfs = scat_op_crea.get_f_surfaces()
            opsurfsnames = "_!#!_".join(s.name for s in opsurfs)
            subcol.operator("scatter5.facesel_to_vcol", text=translate("Define Area"), icon="RESTRICT_SELECT_OFF", ).surfaces_names = opsurfsnames
            subcol.operator("scatter5.facesel_to_vcol", text=f"{sum(s.scatter5.s_visibility_facepreview_area for s in opsurfs):0.2f} m² "+translate("used"),).surfaces_names = opsurfsnames
            
            tocol.separator(factor=0.2)

    #Camera Optimization 

    if (cam):
        
        tocol, is_toggled = ui_templates.bool_toggle(layout, scat_op_crea, "f_visibility_cam_allow", 
            label=translate("Set “Camera Optimization”"), 
            enabled=(bpy.context.scene.camera is not None),
            return_sublayout=True,
            )
        if is_toggled:

            #Camera Frustum 

            tocol2, is_toggled2 = ui_templates.bool_toggle(tocol, scat_op_crea, "f_visibility_camclip_allow", 
                label=translate("Set “Frustum Culling”"), 
                enabled=(bpy.context.scene.camera is not None),
                use_layout_left_spacer=False,
                return_sublayout=True,
                )
            if is_toggled2:
                
                prop = tocol2.column(align=True)
                prop.prop(scat_op_crea, "f_visibility_camclip_cam_boost_xy")

            #Camera Distance Culling 

            tocol2, is_toggled2 = ui_templates.bool_toggle(tocol, scat_op_crea, "f_visibility_camdist_allow", 
                label=translate("Set “Distance Culling”"), 
                enabled=(bpy.context.scene.camera is not None),
                use_layout_left_spacer=False,
                return_sublayout=True,
                )
            if is_toggled2:

                prop = tocol2.column(align=True)
                prop.scale_y = 0.9
                prop.prop(scat_op_crea, "f_visibility_camdist_min")
                prop.prop(scat_op_crea, "f_visibility_camdist_max")

    return None 
    
def creation_operators_draw_display(layout,ctxt_operator,):

    scat_scene   = bpy.context.scene.scatter5
    scat_op      = getattr(scat_scene.operators,ctxt_operator)
    scat_op_crea = scat_scene.operators.create_operators

    ui_templates.bool_toggle(layout, scat_op_crea, "f_display_bounding_box", label=translate("Set object(s) “Bounds”"),)

    if (ctxt_operator=="load_biome"): #special case for biomes: will use placeholder saved within the .biome file

        ui_templates.bool_toggle(layout, scat_scene.operators.load_biome, "f_display_biome_allow", label=translate("Set biome(s) “Display As”"),)

    else: #else, display allow, method option should be available 

        tocol, is_toggled = ui_templates.bool_toggle(layout, scat_op_crea, "f_display_allow", 
            label=translate("Set scatter(s) “Display As”"),
            return_sublayout=True,
            )
        if is_toggled:

            tocol.prop(scat_op_crea, "f_display_method", text="")

            if (scat_op_crea.f_display_method=="placeholder_custom"):

                col = tocol.column()
                col.separator(factor=0.5)
                col.prop(scat_op_crea, "f_display_custom_placeholder_ptr",text="")

    return None

def creation_operators_draw_surfaces(layout, ctxt_operator,):

    scat_scene   = bpy.context.scene.scatter5
    emitter      = bpy.context.scene.scatter5.emitter
    scat_op      = getattr(scat_scene.operators,ctxt_operator)
    scat_op_crea = scat_scene.operators.create_operators

    row = layout.row()
    row1 = row.row()
    row1.scale_x = 0.1
    row2 = row.column()
    row2.scale_y = 1.0

    col = row2
    if ( "is_toggled" in locals() ):
        col.enabled = not is_toggled 

    col.prop(scat_op_crea,"f_surface_method", text="")
    col.separator(factor=0.3)

    match scat_op_crea.f_surface_method:
            
        case 'emitter':
            pass
            #this interface is already too crowded
            #prop = col.row()
            #prop.enabled = False
            #prop.prop(scat_scene,"emitter", text="", icon_value=cust_icon("W_EMITTER"),)
            
        case 'object':
            col.prop(scat_op_crea,"f_surface_object", text="")

        case 'collection':
            surfcol = col.column(align=True)

            lis = surfcol.box().column(align=True)
            lis.scale_y = 0.85
            
            for i,o in enumerate(scat_op_crea.f_surfaces): 
                if (o.name!=""):
                    lisr = lis.row()
                    lisr.label(text=o.name)

                    #remove given object
                    op = lisr.operator("scatter5.exec_line", text="", icon="TRASH", emboss=False,)
                    op.api = f"scat_ops.create_operators.f_surfaces[{i}].object = None ; scat_ops.create_operators.f_surfaces.remove({i})"
                    op.undo = translate("Remove Surface(s)")
                    op.description = translate("Remove Surface(s)")
            
            if ("lisr" not in locals()):
                lisr = lis.row()
                lisr.label(text=translate("No Surface(s) Assigned"))

            #add selected objects & refresh their square area
            op = surfcol.operator("scatter5.exec_line", text=translate("Add Selection"), icon="ADD",)
            op.api = f"bpy.context.scene.scatter5.operators.create_operators.add_selection()"
            op.undo = translate("Add Surface(s)")
            op.description = translate("Add the selected object(s) in the 3D viewport as new future surface(s) for this scatter operator")

    return None

def creation_operators_draw_security(layout, sec_count=True, sec_verts=True):

    scat_op_crea = bpy.context.scene.scatter5.operators.create_operators

    if (sec_count):

        row = layout.row(align=True)
        col1 = row.column() ; col1.scale_x = 0.2
        col2 = row.column()
        col3 = row.column()
        col1.label(text=" ")
        col2.prop(scat_op_crea,"f_sec_count_allow",text="")
        col3.enabled = scat_op_crea.f_sec_count_allow
        col3.scale_y = 0.87
        col3.prop(scat_op_crea,"f_sec_count",text=translate("Heavy Scatter's"),)

    if (sec_verts):

        row = layout.row(align=True)
        col1 = row.column() ; col1.scale_x = 0.2
        col2 = row.column()
        col3 = row.column()
        col1.label(text=" ")
        col2.prop(scat_op_crea,"f_sec_verts_allow",text="")
        col3.enabled = scat_op_crea.f_sec_verts_allow
        col3.scale_y = 0.87
        col3.prop(scat_op_crea,"f_sec_verts",text=translate("Heavy Object's"),)

    return None 

def creation_operators_draw_mask(layout,ctxt_operator):

    scat_scene   = bpy.context.scene.scatter5
    emitter      = bpy.context.scene.scatter5.emitter
    scat_op      = getattr(scat_scene.operators,ctxt_operator)
    scat_op_crea = scat_scene.operators.create_operators

    row = layout.row()
    row1 = row.row()
    row1.scale_x = 0.1
    row2 = row.column()
    row2.scale_y = 1.0

    row2.prop(scat_op, "f_mask_action_method",text="",)
    opmeth = getattr(scat_op,"f_mask_action_method")
    
    if opmeth in ('paint','assign'):

        row2.separator(factor=0.2)
        row2.prop(scat_op, "f_mask_action_type",text="",)
        methact = getattr(scat_op,"f_mask_action_type")
        
        #bezarea action type get submethod dropdown
        if (methact=='curve'):
            row2.separator(factor=0.2)
            row2.prop(scat_op, "f_mask_action_type_curve_subtype", text="")
        
        #assign get extra pointers props
        if (opmeth=='assign'):
            row2.separator(factor=0.2)
            slotcol = row2.row(align=True)

            match methact:
                    
                case 'vg':
                    ptr = slotcol.row(align=True)
                    ptr.alert = ( bool(scat_op.f_mask_assign_vg) and not is_attr_surfs_shared(surfaces=scat_op_crea.get_f_surfaces(), attr_type='vg', attr_name=scat_op.f_mask_assign_vg,) )
                    ptr.prop(scat_op, "f_mask_assign_vg", text="", icon="GROUP_VERTEX", placeholder=" "+translate("Vertex-Group"),)
                    slotcol.prop(scat_op, "f_mask_assign_reverse", text="", icon="ARROW_LEFTRIGHT")
                    
                case 'bitmap':
                    ptr = slotcol.row(align=True)
                    ptr.alert = ( bool(scat_op.f_mask_assign_bitmap) and (scat_op.f_mask_assign_bitmap not in bpy.data.images) )
                    ptr.prop(scat_op, "f_mask_assign_bitmap", text="", icon="IMAGE_DATA", placeholder=" "+translate("Image"),)
                    slotcol.prop(scat_op, "f_mask_assign_reverse", text="", icon="ARROW_LEFTRIGHT")

                case 'curve':
                    slotcol.prop(scat_op, "f_mask_assign_curve", text="", icon="CURVE_BEZCIRCLE",)
                    #slotcol.prop(scat_op, "f_mask_assign_reverse", text="", icon="ARROW_LEFTRIGHT") #no longer supported, as now bezier area assignation will use the bezier distribution

                case 'draw':
                    slotcol.prop(scat_op, "f_mask_assign_curve", text="", icon="CURVE_BEZCURVE",)

        #bezspline action type, need width param
        if (methact=='draw'):
            row2.separator(factor=0.2)
            row2.prop(scat_op, "f_mask_spline_width",)
                
    return None 


#   .oooooo.                                    .    o8o                               .oooooo.                   ooooooooo.
#  d8P'  `Y8b                                 .o8    `"'                              d8P'  `Y8b                  `888   `Y88.
# 888          oooo d8b  .ooooo.   .oooo.   .o888oo oooo   .ooooo.  ooo. .oo.        888      888 oo.ooooo.        888   .d88'  .ooooo.  oo.ooooo.   .ooooo.  oooo    ooo  .ooooo.  oooo d8b  .oooo.o
# 888          `888""8P d88' `88b `P  )88b    888   `888  d88' `88b `888P"Y88b       888      888  888' `88b       888ooo88P'  d88' `88b  888' `88b d88' `88b  `88.  .8'  d88' `88b `888""8P d88(  "8
# 888           888     888ooo888  .oP"888    888    888  888   888  888   888       888      888  888   888       888         888   888  888   888 888   888   `88..8'   888ooo888  888     `"Y88b.
# `88b    ooo   888     888    .o d8(  888    888 .  888  888   888  888   888       `88b    d88'  888   888       888         888   888  888   888 888   888    `888'    888    .o  888     o.  )88b
#  `Y8bood8P'  d888b    `Y8bod8P' `Y888""8o   "888" o888o `Y8bod8P' o888o o888o       `Y8bood8P'   888bod8P'      o888o        `Y8bod8P'  888bod8P' `Y8bod8P'     `8'     `Y8bod8P' d888b    8""888P'
#                                                                                                  888                                    888
#                                                                                                 o888o                                  o888o


class SCATTER5_PT_creation_operator_add_psy_density(bpy.types.Panel):

    bl_idname      = "SCATTER5_PT_creation_operator_add_psy_density"
    bl_label       = translate("On Creation Options")
    bl_description = translate("Define the default behavior of this operator, such as defining the future optimization settings, the security behaviors when creating a heavy scatter, and the import behaviors. You can precisely define which surface(s) the operator is scattering upon. You can also choose to directly paint a new mask, or assign an existing mask")
    bl_category    = ""
    bl_space_type  = "VIEW_3D"
    bl_region_type = "HEADER" #Hide this panel? not sure how to hide them...
    #bl_options     = {"DRAW_BOX"}

    def draw(self, context):
        layout = self.layout

        from ... __init__ import blend_prefs
        scat_data  = blend_prefs()
        scat_scene = context.scene.scatter5
        scat_win   = context.window_manager.scatter5

        col = layout.column()
        col.scale_y = 0.85

        col.label(text=translate("Future Scatter's Visibility")+":",)
        creation_operators_draw_visibility(col)

        col.separator(factor=0.85)

        col.label(text=translate("Future Display")+":",)
        creation_operators_draw_display(col,"add_psy_density")

        col.separator(factor=0.85)
        
        col.label(text=translate("Security Threshold")+":",)
        creation_operators_draw_security(col)

        col.separator(factor=0.85)

        col.label(text=translate("Asset(s) Import Behavior")+":",)
        row = col.row()
        row1 = row.row()
        row1.scale_x = 0.1
        row2 = row.row()
        row2.scale_y = 0.9
        row2.prop(scat_data, "objects_import_method", text="")

        col.separator(factor=0.85)
        
        col.label(text=translate("Future Scatter's Mask")+":",)
        creation_operators_draw_mask(col,"add_psy_density")

        col.separator(factor=0.85)

        col.label(text=translate("Future Scatter's Surface(s)")+":",)
        creation_operators_draw_surfaces(col,"add_psy_density")

        return None

class SCATTER5_PT_creation_operator_add_psy_preset(bpy.types.Panel):

    bl_idname      = "SCATTER5_PT_creation_operator_add_psy_preset"
    bl_label       = translate("On Creation Options")
    bl_description = translate("Define the default behavior of this operator, such as defining the future optimization settings, the security behaviors when creating a heavy scatter, and the import behaviors. You can precisely define which surface(s) the operator is scattering upon. You can also choose to directly paint a new mask, or assign an existing mask")
    bl_category    = ""
    bl_space_type  = "VIEW_3D"
    bl_region_type = "HEADER" #Hide this panel? not sure how to hide them...
    #bl_options     = {"DRAW_BOX"}

    def draw(self, context):
        layout = self.layout

        from ... __init__ import blend_prefs
        scat_data  = blend_prefs()
        scat_scene = context.scene.scatter5
        scat_win   = context.window_manager.scatter5

        col = layout.column()
        col.scale_y = 0.85

        col.label(text=translate("Future Scatter's Visibility")+":",)
        creation_operators_draw_visibility(col)

        col.separator(factor=0.85)

        col.label(text=translate("Future Display")+":",)
        creation_operators_draw_display(col,"add_psy_preset")

        col.separator(factor=0.85)

        col.label(text=translate("Security Threshold")+":",)
        creation_operators_draw_security(col)

        col.separator(factor=0.85)

        col.label(text=translate("Asset(s) Import Behavior")+":",)
        row = col.row()
        row1 = row.row()
        row1.scale_x = 0.1
        row2 = row.row()
        row2.scale_y = 0.9
        row2.prop(scat_data, "objects_import_method", text="")

        col.separator(factor=0.85)

        col.label(text=translate("Future Scatter's Mask")+":",)
        creation_operators_draw_mask(col,"add_psy_preset")

        col.separator(factor=0.85)

        col.label(text=translate("Future Scatter's Surface(s)")+":",)
        creation_operators_draw_surfaces(col,"add_psy_preset")

        return None

class SCATTER5_PT_creation_operator_add_psy_manual(bpy.types.Panel):

    bl_idname      = "SCATTER5_PT_creation_operator_add_psy_manual"
    bl_label       = translate("On Creation Options")
    bl_description = translate("Define the default behavior of this operator, such as defining the future optimization settings, the security behaviors when creating a heavy scatter, and the import behaviors. You can precisely define which surface(s) the operator is scattering upon. You can also choose to directly paint a new mask, or assign an existing mask")
    bl_category    = ""
    bl_space_type  = "VIEW_3D"
    bl_region_type = "HEADER" #Hide this panel? not sure how to hide them...
    #bl_options     = {"DRAW_BOX"}

    def draw(self, context):
        layout = self.layout
        
        from ... __init__ import blend_prefs
        scat_data  = blend_prefs()
        scat_scene = context.scene.scatter5
        scat_win   = context.window_manager.scatter5

        col = layout.column()
        col.scale_y = 0.85

        col.label(text=translate("Future Display")+":",)
        creation_operators_draw_display(col,"add_psy_manual")

        col.separator(factor=0.85)

        col.label(text=translate("Asset(s) Import Behavior")+":",)
        row = col.row()
        row1 = row.row()
        row1.scale_x = 0.1
        row2 = row.row()
        row2.scale_y = 0.9
        row2.prop(scat_data, "objects_import_method", text="")
        
        col.separator(factor=0.85)

        col.label(text=translate("Transforms Settings")+":",)

        ui_templates.bool_toggle(col, scat_scene.operators.add_psy_manual, "f_rot_random_allow", label=translate("Use Random Rotation"),)
        ui_templates.bool_toggle(col, scat_scene.operators.add_psy_manual, "f_scale_random_allow", label=translate("Use Random Scale"),)

        col.separator(factor=0.85)

        col.label(text=translate("Future Scatter's Surface(s)")+":",)
        creation_operators_draw_surfaces(col,"add_psy_manual")

        return None

class SCATTER5_PT_creation_operator_add_psy_modal(bpy.types.Panel):

    bl_idname      = "SCATTER5_PT_creation_operator_add_psy_modal"
    bl_label       = translate("On Creation Options")
    bl_description = translate("Define the default behavior of this operator, such as defining the future optimization settings, the security behaviors when creating a heavy scatter, and the import behaviors. You can precisely define which surface(s) the operator is scattering upon. You can also choose to directly paint a new mask, or assign an existing mask")
    bl_category    = ""
    bl_space_type  = "VIEW_3D"
    bl_region_type = "HEADER" #Hide this panel? not sure how to hide them...
    #bl_options     = {"DRAW_BOX"}

    def draw(self, context):
        layout = self.layout

        from ... __init__ import blend_prefs
        scat_data  = blend_prefs()
        scat_scene = context.scene.scatter5
        scat_win   = context.window_manager.scatter5

        col = layout.column()
        col.scale_y = 0.85

        col.label(text=translate("Shortcut")+":",)

        def get_hotkey_entry_item(km, kmi_name):
            for i, km_item in enumerate(km.keymap_items):
                if (km.keymap_items.keys()[i]==kmi_name):
                    return km_item
            return None 

        row = col.row()
        row1 = row.row()
        row1.scale_x = 0.1
        row2 = row.row()
        row2.scale_y = 0.8

        wm = bpy.context.window_manager
        kc = wm.keyconfigs.user
        km = kc.keymaps['Window']
        kmi = get_hotkey_entry_item(km,"scatter5.define_add_psy")
        if (kmi):
            button = row2.row(align=True)
            button.scale_y = 1.2
            button.context_pointer_set("keymap", km)
            button.prop(kmi, "type", text="", full_event=True)

        col.separator(factor=0.85)

        col.label(text=translate("Default Density")+":",)

        row = col.row()
        row1 = row.row()
        row1.scale_x = 0.1
        row2 = row.row()
        row2.scale_y = 0.8
        row2.scale_y = 1.05
        row2.prop(scat_scene.operators.add_psy_modal, "f_distribution_density")

        col.separator(factor=0.85)

        col.label(text=translate("Future Scatter's Visibility")+":",)
        creation_operators_draw_visibility(col, hide_viewport=False, view_allow=False,)

        col.separator(factor=0.85)

        col.label(text=translate("Future Display")+":",)
        creation_operators_draw_display(col,"add_psy_modal")

        col.separator(factor=0.85)

        col.label(text=translate("Asset(s) Import Behavior")+":",)

        row = col.row()
        row1 = row.row()
        row1.scale_x = 0.1
        row2 = row.row()
        row2.scale_y = 0.9
        row2.prop(scat_data, "objects_import_method", text="")

        col.separator(factor=0.85)

        col.label(text=translate("Future Scatter's Surface(s)")+":",)
        creation_operators_draw_surfaces(col,"add_psy_modal")

        return None


class SCATTER5_PT_creation_operator_load_biome(bpy.types.Panel):

    bl_idname      = "SCATTER5_PT_creation_operator_load_biome"
    bl_label       = translate("On Creation Options")
    bl_description = translate("Define the default behavior of this operator, such as defining the future optimization settings, the security behaviors when creating a heavy scatter, and the import behaviors. You can precisely define which surface(s) the operator is scattering upon. You can also choose to directly paint a new mask, or assign an existing mask")
    bl_category    = ""
    bl_space_type  = "VIEW_3D"
    bl_region_type = "HEADER" #Hide this panel? not sure how to hide them...
    #bl_options     = {"DRAW_BOX"}

    def draw(self, context):
        layout = self.layout

        from ... __init__ import blend_prefs
        scat_data  = blend_prefs()
        scat_scene = context.scene.scatter5
        scat_win   = context.window_manager.scatter5

        col = layout.column()
        col.scale_y = 0.85

        col.label(text=translate("Future Scatter's Visibility")+":",)
        creation_operators_draw_visibility(col)

        col.separator(factor=0.85)

        col.label(text=translate("Future Display")+":",)
        creation_operators_draw_display(col,"load_biome")

        col.separator(factor=0.85)

        col.label(text=translate("Security Threshold")+":",)
        creation_operators_draw_security(col)

        col.separator(factor=0.85)

        col.label(text=translate("Asset(s) Import Behavior")+":",)
        row = col.row()
        row1 = row.row()
        row1.scale_x = 0.1
        row2 = row.row()
        row2.scale_y = 0.9
        row2.prop(scat_data, "objects_import_method", text="")

        col.separator(factor=0.85)

        col.label(text=translate("Future Scatter's Mask")+":",)
        creation_operators_draw_mask(col,"load_biome")

        col.separator(factor=0.85)

        col.label(text=translate("Future Scatter's Surface(s)")+":",)
        creation_operators_draw_surfaces(col,"load_biome")

        return None


# ooo        ooooo
# `88.       .888'
#  888b     d'888   .ooooo.  ooo. .oo.   oooo  oooo
#  8 Y88. .P  888  d88' `88b `888P"Y88b  `888  `888
#  8  `888'   888  888ooo888  888   888   888   888
#  8    Y     888  888    .o  888   888   888   888
# o8o        o888o `Y8bod8P' o888o o888o  `V88V"V8P'


class SCATTER5_MT_manager_header_menu_scatter(bpy.types.Menu):

    bl_idname = "SCATTER5_MT_manager_header_menu_scatter"
    bl_label  = ""

    def draw(self, context):

        layout = self.layout

        from ... __init__ import bl_info
        layout.label(text=f"Plugin Version: {bl_info['version']}")
        layout.label(text=f"Blender Version: {bl_info['blender']}")

        layout.separator()

        layout.operator("wm.url_open",text=translate("Official Website"),icon="URL").url = "https://geoscatter.com"
        layout.operator("wm.url_open",text=translate("Documentation"),icon="URL").url = "https://geoscatter.com/documentation"
        layout.operator("wm.url_open",text=translate("Discord Community"),icon="URL").url = "https://discord.com/invite/F7ZyjP6VKB"
        layout.operator("wm.url_open",text=translate("Personal Assistance"),icon="URL").url = "https://www.blendermarket.com/products/scatter"
        layout.operator("wm.url_open",text=translate("Leave a Nice Review?"),icon="SOLO_ON").url = "https://www.blendermarket.com/products/scatter/ratings"
        

        return None


class SCATTER5_MT_manager_header_menu_interface(bpy.types.Menu):

    bl_idname      = "SCATTER5_MT_manager_header_menu_interface"
    bl_label       = translate("Manager Interface")
    bl_description = translate("Tweak how the interface is displayed")

    def draw(self, context):

        layout = self.layout
        
        scat_addon = addon_prefs()
        scat_win = context.window_manager.scatter5
        
        match scat_win.category_manager:
            
            case 'lister_large'|'lister_stats':

                layout.prop(scat_addon,"ui_lister_scale_y") 
                
            case 'library'|'market':

                layout.prop(scat_addon,"ui_library_adaptive_columns") 
                layout.prop(scat_addon,"ui_library_item_size",icon="ARROW_LEFTRIGHT") 
                #layout.prop(scat_addon,"ui_library_typo_limit",icon="OUTLINER_DATA_FONT")  #seem that this is no longer required
                
                if (not scat_addon.ui_library_adaptive_columns):
                    layout.prop(scat_addon,"ui_library_columns") 

        return None 


class SCATTER5_MT_manager_header_menu_open(bpy.types.Menu):

    bl_idname      = "SCATTER5_MT_manager_header_menu_open"
    bl_label       = translate("File Menu")
    bl_description = translate("Options about the files contained in this interface")

    def draw(self, context):

        layout = self.layout

        scat_win = context.window_manager.scatter5

        match scat_win.category_manager:
            
            case 'library':

                row = layout.row()
                row.operator_context = "INVOKE_DEFAULT"
                row.operator("scatter5.export_to_biome", text=translate("Create New Biome"),icon="CURRENT_FILE")
                layout.separator()

                layout.operator("scatter5.reload_biome_library", text=translate("Reload Library"), icon="FILE_REFRESH")
                layout.operator("scatter5.open_directory", text=translate("Open Library"), icon="FOLDER_REDIRECT").folder = directories.lib_biomes
                layout.operator("scatter5.install_package", text=translate("Install a Package"), icon="NEWFOLDER")
                            
            case 'market':

                layout.operator("wm.url_open",text=translate("Your Pack Here? Contact Us"),icon="URL").url="https://discord.com/invite/F7ZyjP6VKB"

                layout.separator()

                layout.operator("scatter5.fetch_content_from_git",text=translate("Refresh Online Previews"), icon="FILE_REFRESH")
                layout.operator("scatter5.open_directory",text=translate("Open Library"), icon="FOLDER_REDIRECT").folder = directories.lib_biomes
                layout.operator("scatter5.install_package", text=translate("Install a Package"), icon="NEWFOLDER")

        return None 


class SCATTER5_MT_per_biome_main_menu(bpy.types.Menu):

    bl_idname = "SCATTER5_MT_per_biome_main_menu"
    bl_label  = ""

    def __init__(self, *args, **kwargs):
        """get the biome path"""
        
        super().__init__(*args, **kwargs)

        #get context element 
        self.path_arg = bpy.context.pass_ui_arg_lib_obj.name

        return None 

    def draw(self, context):
        layout = self.layout

        scat_win = bpy.context.window_manager.scatter5
        lib_element = scat_win.library[self.path_arg]

        #favorite option
        
        match lib_element.is_favorite:
            case True:
                op = layout.operator("scatter5.exec_line", text=translate("Remove Favorite"),icon_value=cust_icon("W_REPULSION"),)
                op.api = f"scat_win.library[path_arg].is_favorite = False ; favorite_file = os.path.splitext(path_arg)[0] + '.is_favorite' ; os.remove(favorite_file)"
                op.description = translate("Remove Favorite")
            case False:
                op = layout.operator("scatter5.exec_line", text=translate("Add Favorite"),icon_value=cust_icon("W_AFFINITY"),)
                op.api = f"scat_win.library[path_arg].is_favorite = True ; favorite_file = os.path.splitext(path_arg)[0] + '.is_favorite' ; f = open(favorite_file, 'w') ;  f.write('777') ; f.close()"
                op.description = translate("Add Favorite")
        
        layout.separator()
        
        #Scatter Single Layer Menu

        layout.menu("SCATTER5_MT_per_biome_sub_menu_single_layer",text=translate("Scatter single layer"),icon="DOCUMENTS")

        #Rename 

        ope = layout.column()
        ope.operator_context = "INVOKE_DEFAULT"
        op = ope.operator("scatter5.rename_biome", text=translate("Rename this .biome"), icon="FONT_DATA")
        op.old_name = lib_element.user_name
        op.path = lib_element.name #element.name == path

        #Thumbnail Operator 

        ope = layout.row()
        ope.operator_context = "INVOKE_DEFAULT"
        op = ope.operator("scatter5.generate_thumbnail",text=translate("Thumbnail generator"),icon="RESTRICT_RENDER_OFF")
        op.json_path = lib_element.name
        op.render_output = lib_element.name.replace(".biome",".jpg")

        #Overwrite Biome Menu

        layout.menu("SCATTER5_MT_per_biome_sub_menu_overwrite",text=translate("Overwrite this .biome"),icon="CURRENT_FILE")  

        #Open Files Menu 

        layout.menu("SCATTER5_MT_per_biome_sub_menu_open_files",text=translate("Open files"),icon="FILE_FOLDER")
        
        return None 


class SCATTER5_MT_per_biome_sub_menu_single_layer(bpy.types.Menu):

    bl_idname = "SCATTER5_MT_per_biome_sub_menu_single_layer"
    bl_label  = ""

    def __init__(self, *args, **kwargs):
        """get the biome path and their layers"""
        
        super().__init__(*args, **kwargs)

        #get context element 
        self.path_arg = bpy.context.pass_ui_arg_lib_obj.name

        #get json dict 
        with open(self.path_arg) as f:
            d = json.load(f)

        self.layers = []
        for k,v in d.items():
            #only care about layers!
            if (not k.isdigit()):
                continue
            self.layers.append(v["name"])

        return None 

    def draw(self, context):
        layout = self.layout

        for i,l in enumerate(self.layers):
            op = layout.operator("scatter5.load_biome", text=l, icon="FILE_BLANK" )
            op.emitter_name = "" #Auto
            op.json_path = self.path_arg
            op.single_layer = i+1

        return None 


class SCATTER5_MT_per_biome_sub_menu_overwrite(bpy.types.Menu):

    bl_idname = "SCATTER5_MT_per_biome_sub_menu_overwrite"
    bl_label  = ""

    def __init__(self, *args, **kwargs):
        """get the biome path and their layers"""
        
        super().__init__(*args, **kwargs)

        #get context element 
        self.path_arg = bpy.context.pass_ui_arg_lib_obj.name
        lib_element = bpy.context.window_manager.scatter5.library[self.path_arg]

        #get json dict 
        with open(self.path_arg) as f:
            d = json.load(f)

        basepath, basename = os.path.split(lib_element.name)
        basename = basename.replace(".biome","")

        #get layer 
        self.layers = []
        for k,v in d.items():
            #save biome name!
            if (k=="info"):
                self.biome_name = v["name"]
                continue
            #only care about layers!
            if (not k.isdigit()):
                continue
            #can only overwrite unique preset style!
            if ("BASENAME" not in v["preset"]):
                continue
            p = os.path.join(basepath,v["preset"].replace("BASENAME",basename))
            if (not os.path.exists(p)):
                continue
            self.layers.append((v["name"],p))
            continue

        return None 

    def draw(self, context):
        layout = self.layout

        lib_element = bpy.context.window_manager.scatter5.library[self.path_arg]

        #overwrite whole biome 

        ope = layout.column()
        ope.operator_context = "INVOKE_DEFAULT"
        op = ope.operator("scatter5.export_to_biome", text=f'{translate("Overwrite")} "{self.biome_name}" .biome', icon="CURRENT_FILE")
        op.redefine_biocrea_settings = True
        op.biocrea_biome_name = lib_element.user_name
        op.biocrea_creation_directory = os.path.dirname(lib_element.name)
        op.biocrea_file_keywords = lib_element.keywords
        op.biocrea_file_author = lib_element.author
        op.biocrea_file_website = lib_element.website
        op.biocrea_file_description = lib_element.description

        #overwrite layers settings 

        if (len(self.layers)!=0):
            
            layout.separator()

            for i,(n,l) in enumerate(self.layers):
                op = layout.operator("scatter5.export_to_presets", text=f'{translate("Overwrite")} "{n}" .preset', icon="CURRENT_FILE" )
                op.biome_overwrite_mode = True 
                op.biome_temp_directory = l

        return None 


class SCATTER5_MT_per_biome_sub_menu_open_files(bpy.types.Menu):

    bl_idname = "SCATTER5_MT_per_biome_sub_menu_open_files"
    bl_label  = ""

    def __init__(self, *args, **kwargs):
        """get the biome path and their layers"""
        
        super().__init__(*args, **kwargs)

        #get context element 
        self.path_arg = bpy.context.pass_ui_arg_lib_obj.name

        #get layer 
        with open(self.path_arg) as f:
            d = json.load(f)
        self.layers = []
        i=0
        for k,v in d.items():
            if k.isdigit():
                self.layers.append( (v["name"],self.path_arg.replace(".biome",f".layer{i:02}.preset")) )
                i+=1

        return None 

    def draw(self, context):
        layout = self.layout

        op = layout.operator("scatter5.open_directory", text=f'{translate("Open")} "{os.path.basename(self.path_arg)}"', icon="FILE_TEXT")
        op.folder = self.path_arg

        if (len(self.layers)!=0):

            layout.separator()

            for n,p in self.layers:
                op = layout.operator("scatter5.open_directory", text=f'{translate("Open")} "{n}" .preset', icon="FILE_TEXT" )
                op.folder = p

        layout.separator()

        op = layout.operator("scatter5.open_directory", text=translate("Open Parent Directory"), icon="FOLDER_REDIRECT")
        op.folder = os.path.dirname(self.path_arg)
        
        return None 


#   ooooooooo.
#   `888   `Y88.
#    888   .d88'  .ooooo.   .oooooooo
#    888ooo88P'  d88' `88b 888' `88b
#    888`88b.    888ooo888 888   888
#    888  `88b.  888    .o `88bod8P'
#   o888o  o888o `Y8bod8P' `8oooooo.
#                          d"     YD
#                          "Y88888P'


import sys, inspect
classes = ( obj for name, obj in inspect.getmembers(sys.modules[__name__]) if inspect.isclass(obj) and name.startswith("SCATTER5_") )


#if __name__ == "__main__":
#    register()