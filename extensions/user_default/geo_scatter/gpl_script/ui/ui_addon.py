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
# ooooo     ooo ooooo            .o.             .o8        .o8
# `888'     `8' `888'           .888.           "888       "888
#  888       8   888           .8"888.      .oooo888   .oooo888   .ooooo.  ooo. .oo.
#  888       8   888          .8' `888.    d88' `888  d88' `888  d88' `88b `888P"Y88b
#  888       8   888         .88ooo8888.   888   888  888   888  888   888  888   888
#  `88.    .8'   888        .8'     `888.  888   888  888   888  888   888  888   888
#    `YbodP'    o888o      o88o     o8888o `Y8bod88P" `Y8bod88P" `Y8bod8P' o888o o888o
#
#####################################################################################################


import bpy

import os
import platform 

from ... __init__ import addon_prefs

from .. resources.icons import cust_icon
from .. translations import translate
from .. resources import directories

from .. utils.str_utils import word_wrap
from .. utils.math_utils import square_area_repr, count_repr

from . import ui_templates


# ooo        ooooo            o8o                         .o.             .o8        .o8
# `88.       .888'            `"'                        .888.           "888       "888
#  888b     d'888   .oooo.   oooo  ooo. .oo.            .8"888.      .oooo888   .oooo888   .ooooo.  ooo. .oo.
#  8 Y88. .P  888  `P  )88b  `888  `888P"Y88b          .8' `888.    d88' `888  d88' `888  d88' `88b `888P"Y88b
#  8  `888'   888   .oP"888   888   888   888         .88ooo8888.   888   888  888   888  888   888  888   888
#  8    Y     888  d8(  888   888   888   888        .8'     `888.  888   888  888   888  888   888  888   888
# o8o        o888o `Y888""8o o888o o888o o888o      o88o     o8888o `Y8bod88P" `Y8bod88P" `Y8bod8P' o888o o888o


def draw_addon(self, layout, context,):
    """drawing dunction of AddonPrefs class, stored in properties"""

    #WARNING: Modifying the texts or code below does not in any shape or form change our legal conditions, find the conditions on www.geoscatter.com/legal 
    
    row = layout.row()
    r1 = row.separator()
    col = row.column()
    r3 = row.separator()
        
    #Enter Manager 

    col.label(text=translate("Enter The Plugin Manager."),)
    enter = col.row()
    enter.scale_y = 1.5
    enter.operator("scatter5.impost_addonprefs", text=translate("Enter Interface"), icon_value=cust_icon("W_SCATTER"),).state = True

    #Write license block 

    col.separator(factor=1.5)
    license_layout = col

    from ... __init__ import bl_info
    plugin_name = bl_info["name"]

    #License Agreement 
    
    license_layout.label(text=f"{plugin_name} Comprised Licenses:",)
    boxcol = license_layout.column(align=True)
    box = boxcol.box()
    text = f"The {plugin_name} product aggregate is comprised of three distinct and separate components comprised of their own distinct licenses:\n1) A series of python scripts stored in “/gpl_script/” released under the GNU-GPL 3.0 used for drawing an user interface. 2) A non-software geometry-node nodetree asset called the “GEO-SCATTER ENGINE” stored in “/non_gpl/blends/enging.blend” with a EULA license similar to Royalty free. 3). Icons stored in “/non_gpl/icons/” comprised of various licenses.\nBy using our {plugin_name} product, you, the user, agree to the terms and conditions of all comprised licenses.\nOnly “GEO-SCATTER ENGINE” licenses downloaded from the official source listed on “www.geoscatter.com/download” are legitimate. Compared to the Royalty Free license, the “GEO-SCATTER ENGINE” end user license agreement provides an additional advantage by allowing users to freely share Blender scenes containing the nodetree, while also placing restrictions on how users may interact with our engine nodetree through the usage of scripts or plugins.\nPlease read all additional LICENSES.txt files located within our products for more information and the legal information on “www.geoscatter.com/legal”."
    word_wrap(layout=box, max_char='auto', context=context, char_auto_sidepadding=0.99, alert=False, active=False, scale_y=0.81, string=text,)
    boxl = boxcol.box()
    boxllbl = boxl.row()
    boxllbl.alignment = "CENTER"
    boxllbl.active = False
    boxllbl.operator("wm.url_open", text="For more precisions, consult “www.geoscatter.com/legal”", emboss=False, ).url = "www.geoscatter.com/legal"

    #License Variation 
    
    match directories.engine_license:
        
        case "":
            licsc_tit, licsc_txt = "Geo-Scatter® Engine: No License Found.", "Hello. The script you are currently using sole purpose is to be the interface of our Geometry-node scatter asset called “GEO-SCATTER ENGINE”. Both assets and script can work fully independently. Without our 'engine.blend' present, the interface will work fine, you simply won't be able to communicate with our asset. Note that you can do that manually if you'd like. It looks like you detain no licenses for our “GEO-SCATTER ENGINE”. Please read the full EULA regarding our “GEO-SCATTER ENGINE” asset on “www.geoscatter.com/legal” make sure this engine is only downloaded from one of our recognized sources listed on “www.geoscatter.com/download” any other sources aren't legit."
            if ((licsc_tit is not None) and (licsc_txt is not None)):
                license_layout.separator(factor=1.5)
                license_layout.label(text=licsc_tit,)
                boxcol = license_layout.column(align=True)
                box = boxcol.box()
                word_wrap(layout=box, max_char='auto', context=context, char_auto_sidepadding=0.99, alert=False, active=False, scale_y=0.81, string=licsc_txt,)
                boxl = boxcol.box()
                boxllbl = boxl.row()
                boxllbl.alignment = "CENTER"
                boxllbl.active = False
                boxllbl.operator("wm.url_open", text="Get our asset on “www.geoscatter.com”", emboss=False, ).url = "www.geoscatter.com"
                        
        case str():
            licsc_tit, licsc_txt = "Geo-Scatter® Engine Individual License:", "The “Individual” license for “GEO-SCATTER ENGINE” is a non-transferable license that grants a single user the right to use the “GEO-SCATTER ENGINE” on any device they own for personal or commercial purposes. A one-time fee is required, as outlined in the terms and conditions at “www.geoscatter.com/legal”. This license grants the licensee the permission to interact with our engine through the use of our official interface script." #REPLACED_ON_SHIPPING
            if ((licsc_tit is not None) and (licsc_txt is not None)):
                license_layout.separator(factor=1.5)
                license_layout.label(text=licsc_tit,)
                boxcol = license_layout.column(align=True)
                box = boxcol.box()
                word_wrap(layout=box, max_char='auto', context=context, char_auto_sidepadding=0.99, alert=False, active=False, scale_y=0.81, string=licsc_txt,)
                boxl = boxcol.box()
                boxllbl = boxl.row()
                boxllbl.alignment = "CENTER"
                boxllbl.active = False
                boxllbl.operator("wm.url_open", text="This agreement is available on “www.geoscatter.com/legal”", emboss=False, ).url = "www.geoscatter.com/legal"

    #Trademark Info 
    
    license_layout.separator(factor=1.5)
    license_layout.label(text=f"Trademark Information:",)
    boxcol = license_layout.column(align=True)
    box = boxcol.box()
    text = f"Note that the Geo-Scatter® name & logo is a trademark or registered trademark of “BD3D DIGITAL DESIGN, SLU” in the U.S. and/or European Union and/or other countries. We reserve all rights to this trademark. For further details, please review our trademark and logo policies at “www.geoscatter.com/legal”. The use of our brand name, logo, or marketing materials to distribute content through any non-official channels not listed on “www.geoscatter.com/download” is strictly prohibited. Such unauthorized use falsely implies endorsement or affiliation with third-party activities, which has never been granted. We reserve all rights to protect our brand integrity & prevent any associations with unapproved third parties. You are not permitted to use our brand to promote your unapproved activities in a way that suggests official endorsement or affiliation. As a reminder, the GPL license explicitly excludes brand names from the freedom, our trademark rights remain distinct and enforceable under trademark laws."
    word_wrap(layout=box, max_char='auto', context=context, char_auto_sidepadding=0.99, alert=False, active=False, scale_y=0.81, string=text,)
    boxl = boxcol.box()
    boxllbl = boxl.row()
    boxllbl.alignment = "CENTER"
    boxllbl.active = False
    boxllbl.operator("wm.url_open", text="Visit “www.geoscatter.com/legal”", emboss=False, ).url = "www.geoscatter.com/legal"
    
    #Contact Info
    
    license_layout.separator(factor=1.5)
    license_layout.label(text="Contact Information:",)
    boxcol = license_layout.column(align=True)
    box = boxcol.box()
    text = "If you have any inquiries or questions, you may contact us via “contact@geoscatter.com” or through our diverse social medial lised on “www.geoscatter.com” or listed within this very plugin."
    word_wrap(layout=box, max_char='auto', context=context, char_auto_sidepadding=0.99, alert=False, active=False, scale_y=0.81, string=text,)
    boxl = boxcol.box()
    boxllbl = boxl.row()
    boxllbl.alignment = "CENTER"
    boxllbl.active = False
    boxllbl.operator("wm.url_open", text="Visit “www.geoscatter.com”", emboss=False, ).url = "www.geoscatter.com"

    #Extend Info
    
    disclaimer = col.column()
    disclaimer.separator(factor=0.7)
    disclaimer.active = True
    word_wrap(layout=disclaimer, max_char='auto', context=context, char_auto_sidepadding=0.99, alert=False, active=True, scale_y=0.91, alignment='LEFT',
        string="*Extend or zoom this interface if texts are not readable.",)

    col.separator(factor=2)

    return None


# ooooo   ooooo  o8o   o8o                     oooo         o8o
# `888'   `888'  `"'   `"'                     `888         `"'
#  888     888  oooo  oooo  .oooo.    .ooooo.   888  oooo  oooo  ooo. .oo.    .oooooooo
#  888ooooo888  `888  `888 `P  )88b  d88' `"Y8  888 .8P'   `888  `888P"Y88b  888' `88b
#  888     888   888   888  .oP"888  888        888888.     888   888   888  888   888
#  888     888   888   888 d8(  888  888   .o8  888 `88b.   888   888   888  `88bod8P'
# o888o   o888o o888o  888 `Y888""8o `Y8bod8P' o888o o888o o888o o888o o888o `8oooooo.
#                      888                                                   d"     YD
#                  .o. 88P                                                   "Y88888P'
#                  `Y888P

def addonpanel_overridedraw(self, context,):
    """Impostor Main"""

    layout = self.layout

    scat_win = bpy.context.window_manager.scatter5

    #Prefs
    match scat_win.category_manager:
        
        case 'prefs':
            draw_add_prefs(self, layout)
            
        case 'library':
            from . ui_biome_library import draw_library_grid
            draw_library_grid(self, layout, context,)

        case 'market':
            from . ui_biome_library import draw_online_grid
            draw_online_grid(self, layout, context,)
            
        
        case 'lister_large':
            draw_addon_prefs_lister(self, layout, lister_large=True,)

        case 'lister_stats':
            draw_addon_prefs_lister(self, layout, lister_stats=True,)
            

    return None

            
def addonheader_overridedraw(self, context):
    """Impostor Header"""

    layout = self.layout

    scat_win = bpy.context.window_manager.scatter5
    scat_scene = context.scene.scatter5
    emitter = scat_scene.emitter
    
    from ... __init__ import bl_info
    plugin_name = bl_info["name"]
    
    row = layout.row(align=True)
    row.template_header()

    scat = row.row(align=True)
    scat.scale_x = 1.1
    scat.menu("SCATTER5_MT_manager_header_menu_scatter", text=plugin_name, icon_value=cust_icon("W_SCATTER"),)

    match scat_win.category_manager:

        case 'library':
            row.menu("SCATTER5_MT_manager_header_menu_interface", text=translate("Interface"),)
            row.menu("SCATTER5_MT_manager_header_menu_open", text=translate("File"),)
            popover = row.row(align=True)
            popover.emboss = "NONE"
            popover.popover(panel="SCATTER5_PT_creation_operator_load_biome", text="Settings",)

        case 'lister_large':
            row.menu("SCATTER5_MT_manager_header_menu_interface", text=translate("Interface"),)

        case 'lister_stats':
            row.menu("SCATTER5_MT_manager_header_menu_interface", text=translate("Interface"),)

        case 'market':
            row.menu("SCATTER5_MT_manager_header_menu_interface", text=translate("Interface"),)
            row.menu("SCATTER5_MT_manager_header_menu_open", text=translate("File"),)

        case 'prefs':
            row.menu("USERPREF_MT_save_load", text=translate("Preferences"),)

    layout.separator_spacer()

    if (scat_win.category_manager!="prefs"):
        
        emit = layout.row(align=True)
        
        #helper for noobs..
        if (emitter is None):
            emitlbl = emit.row(align=True)
            emitlbl.alert = True
            emitlbl.label(text=translate("Pick an Emitter →"),)
        
        kwargs = {}
        if (emitter is None):
            kwargs["icon_value"] = cust_icon("W_EMITTER")
        elif (emitter.library):
            kwargs["icon"] = "LINKED"
            
        emit.prop(scat_scene, "emitter",text="", **kwargs)

    exit = layout.row()
    exit.alert = True
    exit.operator("scatter5.impost_addonprefs",text=translate("Exit"),icon='PANEL_CLOSE').state = False

    return None


def addonnavbar_overridedraw(self, context):
    """importor T panel"""

    layout = self.layout

    from ... __init__ import blend_prefs
    scat_data  = blend_prefs()
    scat_win   = context.window_manager.scatter5
    scat_scene = context.scene.scatter5
    emitter = scat_scene.emitter

    #Close if user is dummy 

    if (not context.space_data.show_region_header):
        exit = layout.column()
        exit.alert = True
        exit.operator("scatter5.impost_addonprefs",text=translate("Exit"),icon='PANEL_CLOSE').state = False
        exit.scale_y = 1.8
        return None

    #Draw main categories 

    enum = layout.column()
    enum.scale_y = 1.3
    enum.prop(scat_win,"category_manager",expand=True)

    layout.separator(factor=0.3)
    layout.separator(type="LINE")

    #Per category T panel

    match scat_win.category_manager:
        
        case 'library':

            lbl = layout.row()
            lbl.active = False
            lbl.label(text=translate("Navigation"),)

            row = layout.row(align=True)
            row.scale_y = 1.0
            row.prop(scat_win,"library_search",icon="VIEWZOOM",text="") 
            row.prop(scat_win,"library_filter_favorite",icon_value=cust_icon("W_AFFINITY"),text="") 

            layout.separator(factor=0.33)

            wm = bpy.context.window_manager
            navigate = layout.column(align=True)
            navigate.scale_y = 1.0
            navigate.template_list("SCATTER5_UL_folder_navigation", "", wm.scatter5, "folder_navigation", wm.scatter5, "folder_navigation_idx",rows=15,)

            elements_count = 0 
            if (len(scat_win.folder_navigation)!=0):
                elements_count = scat_win.folder_navigation[scat_win.folder_navigation_idx].elements_count

            indic = navigate.box()
            indic.scale_y = 1.0
            indic.label(text=f'{elements_count} {translate("Elements in Folder")}')
            
            # layout.separator()

            # lbl = layout.row()
            # lbl.active = False
            # lbl.label(text=translate("Need More?"),)

            # row = layout.row(align=True)
            # row.scale_y = 1.0
            # row.operator("scatter5.exec_line",text=translate("Get Biomes"), icon="URL",).api = 'scat_win.category_manager = "market" ; bpy.context.area.tag_redraw()'

            # lbl = layout.row()
            # lbl.active = False
            # lbl.label(text=translate("Install a Scatpack?"),)

            # row = layout.row(align=True)
            # row.scale_y = 1.0
            # row.operator("scatter5.install_package", text=translate("Install a Pack"), icon="NEWFOLDER")

        case 'market':

            lbl = layout.row()
            lbl.active = False
            lbl.label(text=translate("All Biomes"),)

            row = layout.row(align=True)
            row.scale_y = 1.0
            row.operator("wm.url_open",text=translate("Visit Website"),icon="URL").url="https://geoscatter.com/biomes"

            lbl = layout.row()
            lbl.active = False
            lbl.label(text=translate("Share your Pack"),)

            row = layout.row(align=True)
            row.scale_y = 1.0
            row.operator("wm.url_open",text=translate("Contact Us"),icon="URL").url="https://discord.com/invite/F7ZyjP6VKB"

            lbl = layout.row()
            lbl.active = False
            lbl.label(text=translate("Refresh Page"),)

            row = layout.row(align=True)
            row.scale_y = 1.0
            row.operator("scatter5.fetch_content_from_git",text=translate("Refresh"), icon="FILE_REFRESH")

        case 'lister_large':

            if (emitter is not None):

                nbr = len(emitter.scatter5.get_psys_selected(all_emitters=scat_data.factory_alt_selection_method=="all_emitters"))

                # lbl = layout.row()
                # lbl.active = False
                # lbl.label(text=translate("Batch Optimize"),)
                #
                # row = layout.row(align=True)
                # row.scale_y = 1.00
                # row.operator("scatter5.batch_optimization",text=translate("Set Optimizations"),icon="MEMORY")

                lbl = layout.row()
                lbl.active = False
                lbl.label(text=translate("Bounding-Box"),)

                row = layout.row(align=True)
                row.scale_y = 1.0
                row.operator("scatter5.batch_bounding_box",text=translate("Set Bounds"),icon="CUBE").pop_dialog = True

                lbl = layout.row()
                lbl.active = False
                lbl.label(text=translate("Alt Behavior")+f" [{nbr}]",)
                
                row = layout.row(align=True)
                if (scat_data.factory_alt_allow):
                      row.scale_y = 1.1
                      row.prop(scat_data,"factory_alt_selection_method",text="",)
                else: row.prop(scat_data,"factory_alt_allow",text=translate("Enable Alt"), icon="BLANK1",)

        case 'lister_stats':

            if (emitter is not None):

                lbl = layout.row()
                lbl.active = False
                lbl.label(text=translate("Estimate Count"),)

                row = layout.row()
                row.scale_y = 1.0
                op = row.operator("scatter5.exec_line",text=translate("Refresh"),icon="FILE_REFRESH",)
                op.api = f"[ ( p.get_scatter_count(state='render',) , p.get_scatter_count(state='viewport') ) for p in scat_scene.get_all_psys(search_mode='all', also_linked=True)] ; [a.tag_redraw() for a in bpy.context.screen.areas]"
                op.description = translate("Compute the instance-count statistics of every single scatter-system in your scene")

                lbl = layout.row()
                lbl.active = False
                lbl.label(text=translate("Estimate Area"),)

                row = layout.row()
                row.scale_y = 1.0
                op = row.operator("scatter5.exec_line",text=translate("Refresh"),icon="FILE_REFRESH",)
                op.api = f"[ p.get_surfaces_square_area(evaluate='recalculate', eval_modifiers=True, get_selection=False,) for p in scat_scene.get_all_psys(search_mode='all', also_linked=True)] ; [a.tag_redraw() for a in bpy.context.screen.areas]"
                op.description = translate("Compute the square area statistics of every single scatter-surface in your scene")

        case 'prefs':
            
                lbl = layout.row()
                lbl.active = False
                lbl.label(text=translate("Export Settings"),)

                row = layout.row()
                row.scale_y = 1.0
                op = row.operator("scatter5.export_addon_settings",text=translate("Export"),icon="FILE_CACHE",)
                
                lbl = layout.row()
                lbl.active = False
                lbl.label(text=translate("Import Settings"),)

                row = layout.row()
                row.scale_y = 1.0
                op = row.operator("scatter5.import_addon_settings",text=translate("Import"),icon="FILE_CACHE",)

    return None


# 88  88 88  88888    db     dP""b8 88  dP      dP"Yb  88""Yb 888888 88""Yb    db    888888  dP"Yb  88""Yb
# 88  88 88     88   dPYb   dP   `" 88odP      dP   Yb 88__dP 88__   88__dP   dPYb     88   dP   Yb 88__dP
# 888888 88 o.  88  dP__Yb  Yb      88"Yb      Yb   dP 88"""  88""   88"Yb   dP__Yb    88   Yb   dP 88"Yb
# 88  88 88 "bodP' dP""""Yb  YboodP 88  Yb      YbodP  88     888888 88  Yb dP""""Yb   88    YbodP  88  Yb


class SCATTER5_OT_impost_addonprefs(bpy.types.Operator):
    """Monkey patch drawing code of addon preferences to our own code, temporarily"""

    bl_idname      = "scatter5.impost_addonprefs"
    bl_label       = ""
    bl_description = translate("replace/restore native blender preference ui with a custom scatter manager ui")

    state : bpy.props.BoolProperty()

    Status = False
    AddonPanel_OriginalDraw = None
    AddonNavBar_OriginalDraw = None
    AddonHeader_OriginalDraw = None

    def panel_hijack(self):
        """register impostors"""

        cls = type(self)
        if (cls.Status==True):
            return None

        #show header just in case user hided it (show/hide header on 'PREFERENCE' areas)

        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if (area.type=='PREFERENCES'):
                    for space in area.spaces:
                        if (space.type=='PREFERENCES'):
                            space.show_region_header = True

        #Save Original Class Drawing Function in global , and replace their function with one of my own 

        cls.AddonPanel_OriginalDraw = bpy.types.USERPREF_PT_addons.draw
        bpy.types.USERPREF_PT_addons.draw = addonpanel_overridedraw
            
        cls.AddonNavBar_OriginalDraw = bpy.types.USERPREF_PT_navigation_bar.draw
        bpy.types.USERPREF_PT_navigation_bar.draw = addonnavbar_overridedraw
        
        cls.AddonHeader_OriginalDraw = bpy.types.USERPREF_HT_header.draw
        bpy.types.USERPREF_HT_header.draw = addonheader_overridedraw
        
        cls.Status=True

        return None

    def panel_restore(self):
        """restore and find original drawing classes"""

        cls = type(self)
        if (cls.Status==False):
            return None

        #restore original drawing code 
        
        bpy.types.USERPREF_PT_addons.draw = cls.AddonPanel_OriginalDraw
        cls.AddonPanel_OriginalDraw = None 

        bpy.types.USERPREF_PT_navigation_bar.draw = cls.AddonNavBar_OriginalDraw
        cls.AddonNavBar_OriginalDraw = None 

        bpy.types.USERPREF_HT_header.draw = cls.AddonHeader_OriginalDraw
        cls.AddonHeader_OriginalDraw = None 

        #Trigger Redraw, otherwise some area will be stuck until user put cursor 

        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if (area.type=='PREFERENCES'):
                    area.tag_redraw()
                    
        cls.Status=False

        return None

    def execute(self, context):
        
        match self.state:
            case True:
                self.panel_hijack()
            case False:
                self.panel_restore()

        return{'FINISHED'}


# oooooooooo.                                        ooooo     ooo                              ooooooooo.                       .o88o.
# `888'   `Y8b                                       `888'     `8'                              `888   `Y88.                     888 `"
#  888      888 oooo d8b  .oooo.   oooo oooo    ooo   888       8   .oooo.o  .ooooo.  oooo d8b   888   .d88' oooo d8b  .ooooo.  o888oo   .oooo.o
#  888      888 `888""8P `P  )88b   `88. `88.  .8'    888       8  d88(  "8 d88' `88b `888""8P   888ooo88P'  `888""8P d88' `88b  888    d88(  "8
#  888      888  888      .oP"888    `88..]88..8'     888       8  `"Y88b.  888ooo888  888       888          888     888ooo888  888    `"Y88b.
#  888     d88'  888     d8(  888     `888'`888'      `88.    .8'  o.  )88b 888    .o  888       888          888     888    .o  888    o.  )88b
# o888bood8P'   d888b    `Y888""8o     `8'  `8'         `YbodP'    8""888P' `Y8bod8P' d888b     o888o        d888b    `Y8bod8P' o888o   8""888P'



def draw_add_prefs(self, layout):
    
    #limit panel width

    row = layout.row()
    row.alignment="LEFT"
    main = row.column()
    main.alignment = "LEFT"

    draw_add_packs(self,main)
    ui_templates.separator_box_out(main)

    draw_add_environment(self,main)
    ui_templates.separator_box_out(main)

    draw_add_lang(self,main)
    ui_templates.separator_box_out(main)

    draw_add_fetch(self,main)
    ui_templates.separator_box_out(main)
    
    draw_add_paths(self,main)
    ui_templates.separator_box_out(main)
    
    draw_clean_data(self,main)
    ui_templates.separator_box_out(main)

    draw_add_workflow(self,main)
    ui_templates.separator_box_out(main)

    draw_add_customui(self,main)
    ui_templates.separator_box_out(main)
    
    draw_add_npanl(self,main)
    ui_templates.separator_box_out(main)

    draw_add_shortcut(self,main)
    ui_templates.separator_box_out(main)
    
    draw_add_browser(self,main)
    ui_templates.separator_box_out(main)

    draw_add_dev(self,main)
    ui_templates.separator_box_out(main)
            
    for i in range(10):
        layout.separator_spacer()

    return None 


def draw_add_packs(self,layout):

    box, is_open = ui_templates.box_panel(layout, 
        panelopen_propname="ui_add_packs", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_add_packs");BOOL_VALUE(1)
        panel_icon="NEWFOLDER", 
        panel_name=translate("Install a Package"),
        popover_info="SCATTER5_PT_docs",
        popover_uilayout_context_set="ui_add_packs",
        )
    if is_open:

            row = box.row()
            row.separator(factor=0.3)
            col = row.column()
            row.separator(factor=0.3)

            rwoo = col.row()
            rwoo.operator("scatter5.install_package", text=translate("Install a Package"), icon="NEWFOLDER")
            scatpack = rwoo.row()
            scatpack.operator("scatter5.exec_line", text=translate("Find Biomes Online"),icon_value=cust_icon("W_SUPERMARKET")).api = "scat_win.category_manager='market' ; bpy.ops.scatter5.tag_redraw()"

            ui_templates.separator_box_in(box)

    return None


def draw_add_fetch(self,layout):

    sysprefs = bpy.context.preferences.system
    online_access = bpy.app.online_access

    box, is_open = ui_templates.box_panel(layout, 
        panelopen_propname="ui_add_fetch", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_add_fetch");BOOL_VALUE(1)
        panel_icon="URL", 
        panel_name=translate("Scatpack Previews Fetch"),
        )
    if is_open:

            row = box.row()
            row.separator(factor=0.3)
            col = row.column()
            row.separator(factor=0.3)
                        
            ui_templates.bool_toggle(col, sysprefs, "use_online_access", 
                label=translate("Allow online access"), 
                icon="INTERNET" if sysprefs.use_online_access else "INTERNET_OFFLINE", 
                use_layout_left_spacer=False,
                )
            
            col.separator()
                                            
            ui_templates.bool_toggle(col, addon_prefs(), "fetch_automatic_allow", 
                label=translate("Automatically fetch Scatpacks previews"), 
                icon="FILE_REFRESH", 
                use_layout_left_spacer=False,
                active=online_access,
                )
            
            col.separator()
            row = col.row()
            
            subr = row.row()
            subr.active = addon_prefs().fetch_automatic_allow and online_access
            subr.prop(addon_prefs(), "fetch_automatic_daycount", text=translate("Fetch every n Day"),)
            
            subr = row.row()
            subr.operator("scatter5.fetch_content_from_git", text=translate("Refresh Online Previews"), icon="FILE_REFRESH")
            subr.active = online_access

            ui_templates.separator_box_in(box)
    
    return None

    
def draw_add_browser(self,layout):

    box, is_open = ui_templates.box_panel(layout, 
        panelopen_propname="ui_add_browser", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_add_browser");BOOL_VALUE(1)
        panel_icon="ASSET_MANAGER", 
        panel_name=translate("Asset Browser Convert"),
        popover_info="SCATTER5_PT_docs", 
        popover_uilayout_context_set="ui_add_browser",
        )
    if is_open:

            row = box.row()
            row.separator(factor=0.3)
            col = row.column()
            row.separator(factor=0.3)
            
            col.operator("scatter5.make_asset_library", text=translate("Convert blend(s) to Asset-Browser Format"), icon="FILE_BLEND",)
                
            col.separator(factor=0.5)
            word_wrap(layout=col, max_char=70, alert=False, active=True, string=translate("Warning, this operator will quit this session to sequentially open all blends and mark their asset(s). Please do not interact with the interface until the task is finished.."),)

            ui_templates.separator_box_in(box)
    
    return None


def draw_clean_data(self,layout):

    box, is_open = ui_templates.box_panel(layout, 
        panelopen_propname="clean_data", #INSTRUCTION:REGISTER:UI:BOOL_NAME("clean_data");BOOL_VALUE(1)
        panel_icon="MESH_DATA", 
        panel_name=translate("Clanse Data"),
        #popover_info="SCATTER5_PT_docs", 
        #popover_uilayout_context_set="clean_data",
        )
    if is_open:

            row = box.row()
            row.separator(factor=0.3)
            col = row.column()
            row.separator(factor=0.3)
            
            col.operator("scatter5.clean_unused_import_data", text=translate("Delete unused imports"), icon="TRASH",)
            col.separator(factor=0.5)
            col.operator("outliner.orphans_purge", text=translate("Purge orphans data"), icon="ORPHAN_DATA",).do_recursive = True
            col.separator(factor=0.5)
            col.operator("scatter5.fix_nodetrees", text=translate("Fix all Scatter-Objects/Engines"), icon="TOOL_SETTINGS",).force_update = True
            
            ui_templates.separator_box_in(box)
    
    return None


def draw_add_lang(self,layout):

    box, is_open = ui_templates.box_panel(layout, 
        panelopen_propname="ui_add_lang", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_add_lang");BOOL_VALUE(1)
        panel_icon="WORLD_DATA", 
        panel_name=translate("Languages"),
        )
    if is_open: 

            scat_addon = addon_prefs()

            row = box.row()
            row.separator(factor=0.3)
            col = row.column()
            row.separator(factor=0.3)
            
            ope = col.row()
            ope.prop(scat_addon,"language",text="")

            if (scat_addon.language!="English"):
                
                col.separator(factor=0.7)
                rwoo = col.row()
                word_wrap(layout=rwoo, max_char=65, active=True, string=translate("Translations are only applied when booting up blender. Please quit and restart blender to apply the changes!"),)
                
            ui_templates.separator_box_in(box)

    return None 


def draw_add_npanl(self,layout):

    box, is_open = ui_templates.box_panel(layout, 
        panelopen_propname="ui_add_npanl", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_add_npanl");BOOL_VALUE(1)
        panel_icon="MENU_PANEL", 
        panel_name=translate("N Panel Name"),
        )
    if is_open:

            row = box.row()
            row.separator(factor=0.3)
            col = row.column()
            row.separator(factor=0.3)

            ope = col.row()
            ope.alert = (addon_prefs().tab_name in (""," ","  "))
            ope.prop(addon_prefs(),"tab_name",text="")
            
            ui_templates.separator_box_in(box)

    return None


def draw_add_paths(self,layout):

    box, is_open = ui_templates.box_panel(layout, 
        panelopen_propname="ui_add_paths", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_add_paths");BOOL_VALUE(1)
        panel_icon="FILEBROWSER", 
        panel_name=translate("Scatter-Library Location"),
        popover_info="SCATTER5_PT_docs", 
        popover_uilayout_context_set="ui_add_paths",
        )
    if is_open:

            row = box.row()
            row.separator(factor=0.3)
            col = row.column()
            row.separator(factor=0.3)
                
            is_library = os.path.exists(addon_prefs().library_path)
            is_biomes  = os.path.exists(os.path.join(addon_prefs().library_path,"_biomes_"))
            is_presets = os.path.exists(os.path.join(addon_prefs().library_path,"_presets_"))
            is_bitmaps = os.path.exists(os.path.join(addon_prefs().library_path,"_bitmaps_"))

            colc = col.column(align=True)

            pa = colc.row(align=True)
            pa.alert = not is_library
            pa.prop(addon_prefs(),"library_path",text="")

            if ( False in (is_library, is_biomes, is_presets,) ):

                colc.separator(factor=0.7)

                warn = colc.column(align=True)
                warn.alignment = "CENTER"
                warn.scale_y = 0.9
                warn.alert = True
                word_wrap(layout=warn, alert=True, max_char=65, active=True, icon="ERROR", string=translate("There are problem(s) with the location you have chosen\n"),)
                
                if (not is_library):
                    warn.label(text=translate("-The following paths don't exist"))
                if (not is_biomes):
                    warn.label(text="-'_biomes_' "+translate("Directory Not Found"))
                if (not is_presets):
                    warn.label(text="-'_biomes_' "+translate("Directory Not Found"))
                if (not is_bitmaps):
                    warn.label(text="-'_biomes_' "+translate("Directory Not Found"))

                word_wrap(layout=warn, alert=True, max_char=65, active=True, icon="BLANK1", string=translate("\nAre you sure you chose the path of a Scatter-Library? Please note that this path is not where you're supposed to add a biome environment path, the settings related to biomes are right above.\nBecause the library is invalid, we will use the default library location instead"),)

            if all([ is_library, is_biomes, is_presets, is_bitmaps]) and (directories.lib_library!=addon_prefs().library_path):
                colc.separator(factor=0.7)

                warn = colc.column(align=True)
                warn.scale_y = 0.85
                warn.label(text=translate("Chosen Library is Valid, Please save your addonprefs and restart blender."),icon="CHECKMARK")

            col.separator()

            row = col.row()
            col1 = row.column()
            col1.operator("scatter5.reload_biome_library", text=translate("Reload Library"), icon="FILE_REFRESH")
            col1.operator("scatter5.reload_preset_gallery", text=translate("Reload Presets"), icon="FILE_REFRESH")
            col1.operator("scatter5.dummy", text=translate("Reload Images"), icon="FILE_REFRESH")

            col2 = row.column()
            col2.operator("scatter5.open_directory", text=translate("Open Library"),icon="FOLDER_REDIRECT").folder = directories.lib_library
            col2.operator("scatter5.open_directory", text=translate("Open Default Library"),icon="FOLDER_REDIRECT").folder = directories.lib_default
            col2.operator("scatter5.open_directory", text=translate("Open Blender Data"),icon="FOLDER_REDIRECT").folder = directories.blender_version
            
            ui_templates.separator_box_in(box)

    return None 


def draw_add_environment(self,layout):

    box, is_open = ui_templates.box_panel(layout, 
        panelopen_propname="ui_add_environment", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_add_environment");BOOL_VALUE(1)
        panel_icon="LONGDISPLAY", 
        panel_name=translate("Biomes Environment Paths"),
        popover_gearwheel="SCATTER5_PT_add_environment",
        popover_info="SCATTER5_PT_docs", 
        popover_uilayout_context_set="ui_add_environment",
        )
    if is_open:

            scat_addon = addon_prefs()
            
            row = box.row()
            row.separator(factor=0.3)
            col = row.column()
            row.separator(factor=0.3)

            ui_templates.bool_toggle(col, scat_addon, "blend_environment_scatterlib_allow",
                label=translate("Search for blend(s) first in your Biome-Library"),
                icon="W_BIOME",
                use_layout_left_spacer=False,
                )
            if (scat_addon.blend_environment_scatterlib_allow):

                col.separator(factor=0.5)
                alcol = col.box().column()

                if (not os.path.exists(directories.lib_library)):
                    row = alcol.row(align=True)
                    row.active = False
                    row.label(text=translate("No Path(s) Found"))
                else:
                    row = alcol.row()
                    row.enabled = False
                    row.prop(scat_addon,"library_path", text="")

                col.separator(factor=0.5)
                
            col.separator()
            
            ui_templates.bool_toggle(col, scat_addon, "blend_environment_path_allow",
                label=translate("Search for blend(s) in priority in given paths"),
                icon="FILE_BLEND",
                use_layout_left_spacer=False,
                )
            if (scat_addon.blend_environment_path_allow):

                col.separator(factor=0.5)

                alcocol = col.column(align=True)
                alcol = alcocol.box().column()

                #property interface

                if (len(scat_addon.blend_environment_paths)==0):
                    row = alcol.row(align=True)
                    row.active = False
                    row.label(text=translate("No Path(s) Found"))
                else:
                    for l in scat_addon.blend_environment_paths:

                        row = alcol.row(align=True)

                        path = row.row(align=True)
                        path.alert = not os.path.exists(l.blend_folder)
                        path.prop(l, "blend_folder", text="", )

                        #find index for remove operator
                        for i,p in enumerate(scat_addon.blend_environment_paths):
                            if (p.name==l.name):                        
                                op = row.operator("scatter5.exec_line", text="", icon="TRASH",)
                                op.api = f"addon_prefs().blend_environment_paths.remove({i})"
                                break

                        continue
                    
                #add button 

                addnew = alcocol.row(align=True)
                addnew.scale_y = 0.85
                op = addnew.operator("scatter5.exec_line", text=translate("Add New Path"), icon="ADD", depress=False)
                op.api = "n = addon_prefs().blend_environment_paths.add() ; n.name=str(len(addon_prefs().blend_environment_paths)-1)"
                op.description = translate("Add a path in which the biome system will search for blends!")

                col.separator(factor=1.0)

            col.separator()
            
            ui_templates.bool_toggle(col, scat_addon, "blend_environment_path_asset_browser_allow", 
                label=translate("Search for blend(s) in your blender asset-browser"),
                icon="ASSET_MANAGER",
                use_layout_left_spacer=False,
                )
            if (scat_addon.blend_environment_path_asset_browser_allow):

                col.separator(factor=0.5)
                
                alcocol = col.column(align=True)
                alcol = alcocol.box().column()

                if (len(bpy.context.preferences.filepaths.asset_libraries)==0):
                    row = alcol.row(align=True)
                    row.active = False
                    row.label(text=translate("No Path(s) Found"))
                else:
                    for l in bpy.context.preferences.filepaths.asset_libraries:

                        row = alcol.row()
                        row.enabled = False
                        row.alert = not os.path.exists(l.path)
                        row.prop(l,"path", text="")

                        continue

                #add button 
                addnew = alcocol.row(align=True)
                addnew.scale_y = 0.85
                addnew.operator("preferences.asset_library_add", text=translate("Add New Asset-Library"), icon="ADD", depress=False)

                col.separator(factor=1.0)

            ui_templates.separator_box_in(box)

    return None


def draw_add_workflow(self,layout):

    box, is_open = ui_templates.box_panel(layout, 
        panelopen_propname="ui_add_workflow", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_add_workflow");BOOL_VALUE(1)
        panel_icon="W_SCATTER", 
        panel_name=translate("Workflow"),
        popover_info="SCATTER5_PT_docs", 
        popover_uilayout_context_set="ui_add_workflow",
        )
    if is_open:

            row = box.row()
            row.separator(factor=0.3)
            col = row.column()
            row.separator(factor=0.3)

            emitmethod = col.column(align=True)
            emitmethod.label(text=translate("Emitter swapping:"))
            emit_prop = emitmethod.column() 
            emit_prop.scale_y = 1.0
            emit_prop.prop(addon_prefs(),"emitter_method",expand=False, text="",)

            col.separator(factor=0.9)

            ui_templates.bool_toggle(col, addon_prefs(), "opti_also_hide_mod", 
                label=translate("Hide & Optimize Scatter Modifiers"),
                icon="MODIFIER", 
                use_layout_left_spacer=False,
                )
            
            col.separator(factor=0.3)
            
            ui_templates.separator_box_in(box)

    return None

def draw_add_shortcut(self,layout):

    box, is_open = ui_templates.box_panel(layout, 
        panelopen_propname="ui_add_shortcut", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_add_shortcut");BOOL_VALUE(1)
        panel_icon="EVENT_TAB", 
        panel_name=translate("Shortcuts"),
        )
    if is_open:

            row = box.row()
            row.separator(factor=0.3)
            col = row.column()
            row.separator(factor=0.3)

            def get_hotkey_entry_item(km, kmi_name):
                """collect keymap item"""

                for i, km_item in enumerate(km.keymap_items):
                    if (km.keymap_items.keys()[i]==kmi_name):
                        return km_item
                return None 
            
            wm = bpy.context.window_manager
            kc = wm.keyconfigs.user
            km = kc.keymaps['Window']

            col.label(text=translate("Quick-Scatter Shortcut")+":",)

            kmi = get_hotkey_entry_item(km,"scatter5.define_add_psy")
            if (kmi):
                row = col.row()
                row.context_pointer_set("keymap", km)
                row.prop(kmi, "type", text="", full_event=True)

            col.label(text=translate("Quick-Lister Shortcut")+":",)
            
            kmi = get_hotkey_entry_item(km,"scatter5.quick_lister")
            if (kmi):
                row = col.row()
                row.context_pointer_set("keymap", km)
                row.prop(kmi, "type", text="", full_event=True)
            
            # WATCH: is user manually removes items from keymap, they will draw. that is ok, but not sure if something else can be missing. whole keymap? is that possible? or anything else?
            
            gesture_map = {
                'PRIMARY': ('Primary', 0),
                'SECONDARY': ('Secondary', 1),
                'TERTIARY': ('Tertiary', 2),
                'QUATERNARY': ('Quaternary', 3),
                }
            
            usermap = getattr(bpy.context.window_manager.keyconfigs.get("Blender user"), "keymaps", None, )
            if (usermap is not None):
                from ..manual import keys
                
                col.separator()
                col.label(text=translate("Manual Mode Shortcuts") + ":", )
                
                km_name, km_args, km_content = keys.op_key_defs
                km = usermap.find(km_name, **km_args)
                r = col.row()
                r.context_pointer_set("keymap", km)
                f = False
                for kmi in km.keymap_items:
                    if(kmi.idname == "scatter5.manual_enter"):
                        f = True
                        break
                if (f):
                    r.label(text=kmi.name, )
                    r.prop(kmi, "type", text="", full_event=True, )
                
                col.separator()
                col.label(text=translate("Tools") + ":", )
                
                km_name, km_args, km_content = keys.op_key_defs
                km = usermap.find(km_name, **km_args)
                for item in km_content['items']:
                    item_id = km.keymap_items.find(item[0])
                    if(item_id != -1):
                        kmi = km.keymap_items[item_id]
                        k = kmi.idname.split('.')[-1]
                        if(not k.startswith('manual_brush_tool_')):
                            # NOTE: skip ops that are not brush tools
                            continue
                        
                        r = col.row()
                        r.context_pointer_set("keymap", km)
                        r.label(text=kmi.name, )
                        r.prop(kmi, "type", text="", full_event=True, )
                
                # sort gestures
                ls = [None, None, None, None]
                km_name, km_args, km_content = keys.mod_key_defs
                km = usermap.find(km_name, **km_args)
                for kmi in km.keymap_items:
                    if (kmi.idname == 'scatter5.manual_tool_gesture'):
                        n = gesture_map[getattr(kmi.properties, 'gesture', )][0]
                        i = gesture_map[getattr(kmi.properties, 'gesture', )][1]
                        ls[i] = (n, kmi, )
                
                col.separator()
                col.label(text=translate("Tool Gestures") + ":", )
                
                for i in range(len(ls)):
                    if (ls[i] is not None):
                        n, kmi = ls[i]
                        r = col.row()
                        r.context_pointer_set("keymap", km)
                        r.label(text=n, )
                        r.prop(kmi, "type", text="", full_event=True, )
            
            ui_templates.separator_box_in(box)

    return None
    

def draw_add_customui(self,layout):

    box, is_open = ui_templates.box_panel(layout, 
        panelopen_propname="ui_add_customui", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_add_customui");BOOL_VALUE(1)
        panel_icon="COLOR", 
        panel_name=translate("Interface"),
        )
    if is_open:

            # row = box.row()
            # row.separator(factor=0.3)
            # row.prop(addon_prefs(),"ui_selection_y", text=translate("Selection Area: Items Height"))
            # row.separator(factor=0.3)

            ui_templates.bool_toggle(box, addon_prefs(), "ui_use_dark_box", label=translate("Panels: Use dark headers"), icon="ALIGN_MIDDLE",)
            ui_templates.bool_toggle(box, addon_prefs(), "ui_show_boxpanel_icon", label=translate("Panels: Use headers icons"), icon="MONKEY",)

            row = box.row()
            row.separator(factor=0.3)
            row.prop(addon_prefs(),"ui_boxpanel_separator", text=translate("Panels: Spacing between panels"))
            row.separator(factor=0.3)

            row = box.row()
            row.separator(factor=0.3)
            row.prop(addon_prefs(),"ui_boxpanel_height", text=translate("Panels: Title height"))
            row.separator(factor=0.3)

            ui_templates.bool_toggle(box, addon_prefs(), "ui_bool_use_arrow_openclose", label=translate("Toggles: Use open/close layout arrows"), icon="DOWNARROW_HLT",)
            ui_templates.bool_toggle(box, addon_prefs(), "ui_bool_use_standard", label=translate("Toggles: Use toggle buttons with icons"), icon="MONKEY", invert_checkbox=True,)
            ui_templates.bool_toggle(box, addon_prefs(), "ui_bool_use_iconcross", label=translate("Toggles: Use cross icon if button is disabled"), icon="CANCEL", enabled=(not addon_prefs().ui_bool_use_standard),)

            row = box.row()
            row.separator(factor=0.3)
            row.prop(addon_prefs(),"ui_bool_indentation", text=translate("Toggles: Sub-layout indentation"))
            row.separator(factor=0.3)

            row = box.row()
            row.separator(factor=0.3)
            row.prop(addon_prefs(),"ui_word_wrap_max_char_factor", text=translate("Texts: Paragraphs width"))
            row.separator(factor=0.3)

            row = box.row()
            row.separator(factor=0.3)
            row.prop(addon_prefs(),"ui_word_wrap_y", text=translate("Texts: Paragraphs height"))
            row.separator(factor=0.3)
            
            
            ui_templates.bool_toggle(box, addon_prefs(), "ui_apply_scale_warn", label=translate("Texts: Display 'apply scale' warning"), icon="FILE_TEXT",)
            
            # ------------------------------------------------------------------ manual mode options >>>
            
            ui_templates.bool_toggle(box, addon_prefs(), "manual_use_overlay", label=translate("ManualMode: Use overlay"), icon="OVERLAY",)
            
            # ------------------------------------------------------------------ manual mode options <<<
            # ------------------------------------------------------------------ manual mode theme >>>
            theme = addon_prefs().manual_theme
            
            ui_templates.bool_toggle(box, addon_prefs(), "manual_show_infobox", label=translate("ManualMode: Show infobox"), icon="HELP",)
            
            row = box.row()
            row.separator(factor=0.3)
            # NOTE: pulled out of theme section
            row.prop(theme, "info_box_scale", text=translate("ManualMode: Infobox scale"))
            row.separator(factor=0.3)
            
            ui_templates.bool_toggle(box, theme, "show_ui", label=translate("ManualMode: Tools Theme"), icon="W_DISTMANUAL",)
            if (theme.show_ui):

                row = box.row()
                row.separator(factor=0.3)
                
                c = row.box().column()
                c.row().prop(theme, 'circle_steps')
                c.row().prop(theme, 'fixed_radius_default')
                c.row().prop(theme, 'fixed_center_dot_radius_default')
                c.row().prop(theme, 'no_entry_sign_size_default')
                c.row().prop(theme, 'no_entry_sign_color')
                c.row().prop(theme, 'no_entry_sign_thickness_default')
                c.row().prop(theme, 'default_outline_color')
                c.row().prop(theme, 'default_outline_color_press')
                c.row().prop(theme, 'outline_color_eraser')
                c.row().prop(theme, 'outline_color_hint')
                c.row().prop(theme, 'outline_color_disabled_alpha')
                c.row().prop(theme, 'outline_color_helper_alpha')
                c.row().prop(theme, 'outline_color_gesture_helper_alpha')
                c.row().prop(theme, 'outline_color_falloff_helper_alpha')
                c.row().prop(theme, 'outline_thickness_default')
                c.row().prop(theme, 'outline_thickness_helper_default')
                c.row().prop(theme, 'outline_dashed_steps_multiplier')
                c.row().prop(theme, 'default_fill_color')
                c.row().prop(theme, 'default_fill_color_press')
                c.row().prop(theme, 'fill_color_press_eraser')
                c.row().prop(theme, 'fill_color_helper_hint')
                c.row().prop(theme, 'fill_color_disabled_alpha')
                c.row().prop(theme, 'fill_color_helper_alpha')
                c.row().prop(theme, 'fill_color_gesture_helper_alpha')
                c.row().prop(theme, 'text_size_default')
                c.row().prop(theme, 'text_color')
                c.row().prop(theme, 'text_tooltip_outline_color')
                c.row().prop(theme, 'text_tooltip_background_color')
                c.row().prop(theme, 'text_tooltip_outline_thickness')
                c.row().prop(theme, 'point_size_default')
                c.row().prop(theme, 'grid_overlay_size')
                c.row().prop(theme, 'grid_overlay_color_a')
                c.row().prop(theme, 'grid_overlay_color_b')
                # c.row().prop(theme, 'info_box_scale')
                c.row().prop(theme, 'info_box_shadow_color')
                c.row().prop(theme, 'info_box_fill_color')
                c.row().prop(theme, 'info_box_outline_color')
                c.row().prop(theme, 'info_box_outline_thickness_default')
                c.row().prop(theme, 'info_box_logo_color')
                c.row().prop(theme, 'info_box_text_header_color')
                c.row().prop(theme, 'info_box_text_body_color')
                
                row.separator(factor=0.3)
            # ------------------------------------------------------------------ manual mode theme <<<
            
            ui_templates.separator_box_in(box)

    return None
    

def draw_add_dev(self,layout):

    box, is_open = ui_templates.box_panel(layout, 
        panelopen_propname="ui_add_dev", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_add_dev");BOOL_VALUE(1)
        panel_icon="CONSOLE", 
        panel_name=translate("Debugging"),
        )
    if is_open:

            ui_templates.bool_toggle(box, addon_prefs(), "debug_interface", label="Debug interface", icon="CONSOLE", )
            ui_templates.bool_toggle(box, addon_prefs(), "debug", label="Debug prints", icon="CONSOLE", )
            ui_templates.bool_toggle(box, addon_prefs(), "debug_depsgraph", label="Debug depsgraph prints", icon="CONSOLE", active=addon_prefs().debug,)

            row = box.row()
            row.separator(factor=0.3)
            col = row.column()
            row.separator(factor=0.3)

            col.operator("scatter5.fix_nodetrees", text=translate("Fix all Scatter-Objects/Engines"), icon="TOOL_SETTINGS",).force_update = True
            
            col.separator(factor=0.5)
            col.operator("scatter5.icons_reload", text="Reload plugin icons", icon="TOOL_SETTINGS",)

            col.separator(factor=0.5)
            col.operator("scatter5.exec_line", text="Check for notifications", icon="TOOL_SETTINGS",).api = "check_for_notifications()"

            col.separator(factor=0.5)
            col.operator("scatter5.exec_line", text="Cleanup 'Geo-Scatter' collection", icon="TOOL_SETTINGS",).api = "cleanup_scatter_collections()"

            col.separator(factor=0.5)
            col.operator("scatter5.exec_line", text="Print uuid's repo content", icon="TOOL_SETTINGS",).api = "print('') ; print('Print uuids_repository') ; [print(' «',itm.uuid,'» ',itm.ptr) for itm in scat_data.uuids_repository] if scat_data.uuids_repository else print('Empty'); print('')"
            
            col.separator(factor=0.5)
            col.operator("scatter5.exec_line", text="Cleanup unused uuid's slots", icon="TOOL_SETTINGS",).api = "scat_data.uuids_repository_cleanup()"
            
            col.separator(factor=0.5)
            col.operator("scatter5.exec_line", text="Print `overseer.Observer` infos", icon="TOOL_SETTINGS",).api = "from .. handlers.overseer import Observer ; Observer.debug_print()"
            
            ui_templates.separator_box_in(box)

    return None



# oooooooooo.                                            ooooo         o8o               .
# `888'   `Y8b                                           `888'         `"'             .o8
#  888      888 oooo d8b  .oooo.   oooo oooo    ooo       888         oooo   .oooo.o .o888oo  .ooooo.  oooo d8b
#  888      888 `888""8P `P  )88b   `88. `88.  .8'        888         `888  d88(  "8   888   d88' `88b `888""8P
#  888      888  888      .oP"888    `88..]88..8'         888          888  `"Y88b.    888   888ooo888  888
#  888     d88'  888     d8(  888     `888'`888'          888       o  888  o.  )88b   888 . 888    .o  888
# o888bood8P'   d888b    `Y888""8o     `8'  `8'          o888ooooood8 o888o 8""888P'   "888" `Y8bod8P' d888b



def draw_addon_prefs_lister(self, layout, lister_large=False, lister_stats=False,):

    col = layout.column()

    #defined later on
    scene_col = col.column()
    scat_scene = bpy.context.scene.scatter5
    emitter = scat_scene.emitter

    all_scene_psys = scat_scene.get_all_psys(search_mode="active_view_layer",)
    scene_emitters = scat_scene.get_all_emitters(search_mode="active_view_layer", also_linked=True)
    if (emitter is not None) and (emitter not in scene_emitters):
        scene_emitters.append(emitter)

    #gather some data while in the loop  
    
    total_psys_len = 0
    total_area_len = -1 
    total_viewport_len = -1
    total_render_len = -1 

    for e in scene_emitters:

        elinked = bool(e.library)
        epsys = e.scatter5.particle_systems[:]
        epsys_len = len(epsys)

        psy_active = e.scatter5.get_psy_active()
        group_active = e.scatter5.get_group_active()

        template = col.row()
        ui_list = template.column(align=True)

        #Emitter name and set new emitter operator 

        ui_list_emitterbox = ui_list.box()
        erow = ui_list_emitterbox.row(align=True)
        erow.scale_y = addon_prefs().ui_lister_scale_y

        sub = erow.row(align=True)
        sub.alignment="LEFT"
        op = sub.operator("scatter5.set_new_emitter",text=f'{e.name} → {epsys_len} {translate("System(s)")}', emboss=False, icon_value=cust_icon("W_EMITTER" if (e==emitter) else "W_EMITTER_EMPTY"),)
        op.obj_session_uid = e.session_uid
        op.select = True
        
        if (elinked):
            erow.label(text="", icon="LINKED")

        #rightside

        if (lister_stats and epsys_len):

            rightactions = erow.row()
            rightactions.alignment = "RIGHT"

            infoactions = rightactions.split()
            infoactions.active = False
            infoactions.scale_x = 0.75

            #emitter total surfaces square area

            all_count = [p.get_surfaces_square_area(evaluate="gather") for p in e.scatter5.particle_systems]
            total = sum([c for c in all_count if c>=0])
            skip = all([c<0 for c in all_count])

            infoactions.label(text= square_area_repr(total), icon="SURFACE_NSURFACE",)

            if (total>=0) and (not skip):
                if (total_area_len==-1): #default ==-1, trigger to 0 when valid
                    total_area_len=0
                total_area_len += total

            #emitter total visible viewport  

            all_count = [p.scatter_count_viewport_consider_hide_viewport for p in e.scatter5.particle_systems]
            total = sum([c for c in all_count if c>=0])
            skip = all([c<0 for c in all_count])

            infoactions.label(text=count_repr(total, unit="Pts"), icon="RESTRICT_VIEW_OFF")

            if (total>=0) and (not skip):
                if (total_viewport_len==-1): #default ==-1, trigger to 0 when valid
                    total_viewport_len=0
                total_viewport_len += total

            #gather total visble render 

            all_count = [p.scatter_count_render for p in e.scatter5.particle_systems]
            total = sum([c for c in all_count if c>=0])
            skip = all([c<0 for c in all_count])

            infoactions.label(text=count_repr(total, unit="Pts"), icon="RESTRICT_RENDER_OFF")

            if (total>=0) and (not skip):
                if (total_render_len==-1): #default ==-1, trigger to 0 when valid
                    total_render_len=0
                total_render_len += total

        if (lister_large and epsys_len):
             
            rightactions = erow.row(align=True)
            rightactions.alignment = "RIGHT"
            rightactions.scale_x = 0.95

            #select
            ractions = rightactions.row(align=True)
            ractions.scale_x = 0.90
            toggle_status = [p.sel for p in epsys]
            icon = cust_icon("W_GROUP_TOGGLE_SEL_ALL") if all(toggle_status) else cust_icon("W_GROUP_TOGGLE_SEL_SOME") if any(toggle_status) else cust_icon("W_GROUP_TOGGLE_SEL_NONE")
            if (elinked):
                ractions.active = False
                ractions.label(text="", icon_value=icon)
            else:
                op = ractions.operator("scatter5.batch_toggle", text="", icon_value=icon, emboss=False,)
                op.propname = "sel"
                op.emitter_name = e.name
                op.group_name = ""
                op.setvalue = str(not any(toggle_status))

            #hide viewport
            ractions = rightactions.row(align=True)
            toggle_status = [not p.hide_viewport for p in epsys]
            icon = cust_icon("W_GROUP_TOGGLE_VIEW_ALL") if all(toggle_status) else cust_icon("W_GROUP_TOGGLE_VIEW_SOME") if any(toggle_status) else cust_icon("W_GROUP_TOGGLE_VIEW_NONE")
            op = ractions.operator("scatter5.batch_toggle", text="", icon_value=icon, emboss=False,)
            op.propname = "hide_viewport"
            op.emitter_session_uid = e.session_uid
            op.group_name = ""
            op.setvalue = str(any(toggle_status))

            #hide render
            ractions = rightactions.row(align=True)
            toggle_status = [not p.hide_render for p in epsys]
            icon = cust_icon("W_GROUP_TOGGLE_RENDER_ALL") if all(toggle_status) else cust_icon("W_GROUP_TOGGLE_RENDER_SOME") if any(toggle_status) else cust_icon("W_GROUP_TOGGLE_RENDER_NONE")
            op = ractions.operator("scatter5.batch_toggle", text="", icon_value=icon, emboss=False,)
            op.propname = "hide_render"
            op.emitter_session_uid = e.session_uid
            op.group_name = ""
            op.setvalue = str(any(toggle_status))

            #lock
            ractions = rightactions.row(align=True)
            ractions.scale_x = 0.90
            toggle_status = [p.is_all_locked() for p in epsys]
            icon = cust_icon("W_GROUP_TOGGLE_LOCK_ALL") if all(toggle_status) else cust_icon("W_GROUP_TOGGLE_LOCK_SOME") if any(toggle_status) else cust_icon("W_GROUP_TOGGLE_LOCK_NONE")
            if (elinked):
                ractions.active = False
                ractions.label(text="", icon_value=icon)
            else:
                op = ractions.operator("scatter5.batch_toggle", text="", icon_value=icon, emboss=False,)
                op.propname = "lock"
                op.emitter_name = e.name
                op.group_name = ""
                op.setvalue = "lock_special"

            #separator
            rightactions.separator(factor=0.5) ; rightactions.label(text="",icon_value=cust_icon("W_BAR_VERTICAL")) ; rightactions.separator(factor=0.5)

            #dice
            ractions = rightactions.row(align=True)
            if (elinked):
                ractions.active = False
                ractions.label(text="", icon_value=cust_icon("W_GROUP_TOGGLE_DICE"))
            else:
                op = ractions.operator("scatter5.batch_randomize", text="", icon_value=cust_icon("W_GROUP_TOGGLE_DICE"), emboss=False,)
                op.emitter_name = e.name
                op.group_name = ""

            #separator
            rightactions.separator(factor=0.5) ; rightactions.label(text="",icon_value=cust_icon("W_BAR_VERTICAL")) ; rightactions.separator(factor=0.5)

            #percentage
            ractions = rightactions.row(align=True)
            toggle_status = [p.s_visibility_view_allow for p in epsys]
            icon = cust_icon("W_GROUP_TOGGLE_PERC_ALL") if all(toggle_status) else cust_icon("W_GROUP_TOGGLE_PERC_SOME") if any(toggle_status) else cust_icon("W_GROUP_TOGGLE_PERC_NONE")
            if (elinked):
                ractions.active = False
                ractions.label(text="", icon_value=icon)
            else:
                op = ractions.operator("scatter5.batch_toggle", text="", icon_value=icon, emboss=False,)
                op.propname = "s_visibility_view_allow"
                op.emitter_name = e.name
                op.group_name = ""
                op.setvalue = str(not any(toggle_status))

            #maxload
            ractions = rightactions.row(align=True)
            toggle_status = [p.s_visibility_maxload_allow for p in epsys]
            icon = cust_icon("W_GROUP_TOGGLE_MAXLOAD_ALL") if all(toggle_status) else cust_icon("W_GROUP_TOGGLE_MAXLOAD_SOME") if any(toggle_status) else cust_icon("W_GROUP_TOGGLE_MAXLOAD_NONE")
            if (elinked):
                ractions.active = False
                ractions.label(text="", icon_value=icon)
            else:
                op = ractions.operator("scatter5.batch_toggle", text="", icon_value=icon, emboss=False,)
                op.propname = "s_visibility_maxload_allow"
                op.emitter_name = e.name
                op.group_name = ""
                op.setvalue = str(not any(toggle_status))

            #preview area
            ractions = rightactions.row(align=True)
            toggle_status = [p.s_visibility_facepreview_allow for p in epsys]
            icon = cust_icon("W_GROUP_TOGGLE_PREV_ALL") if all(toggle_status) else cust_icon("W_GROUP_TOGGLE_PREV_SOME") if any(toggle_status) else cust_icon("W_GROUP_TOGGLE_PREV_NONE")
            if (elinked):
                ractions.active = False
                ractions.label(text="", icon_value=icon)
            else:
                op = ractions.operator("scatter5.batch_toggle", text="", icon_value=icon, emboss=False,)
                op.propname = "s_visibility_facepreview_allow"
                op.emitter_name = e.name
                op.group_name = ""
                op.setvalue = str(not any(toggle_status))

            #cam opti
            ractions = rightactions.row(align=True)
            toggle_status = [p.s_visibility_cam_allow for p in epsys]
            icon = cust_icon("W_GROUP_TOGGLE_CLIP_ALL") if all(toggle_status) else cust_icon("W_GROUP_TOGGLE_CLIP_SOME") if any(toggle_status) else cust_icon("W_GROUP_TOGGLE_CLIP_NONE")
            if (elinked):
                ractions.active = False
                ractions.label(text="", icon_value=icon)
            else:
                op = ractions.operator("scatter5.batch_toggle", text="", icon_value=icon, emboss=False,)
                op.propname = "s_visibility_cam_allow"
                op.emitter_name = e.name
                op.group_name = ""
                op.setvalue = str(not any(toggle_status))

            #separator
            rightactions.separator(factor=0.5) ; rightactions.label(text="",icon_value=cust_icon("W_BAR_VERTICAL")) ; rightactions.separator(factor=0.5)

            #display as
            ractions = rightactions.row(align=True)
            toggle_status = [p.s_display_allow for p in epsys]
            icon = cust_icon("W_GROUP_TOGGLE_DISP_ALL") if all(toggle_status) else cust_icon("W_GROUP_TOGGLE_DISP_SOME") if any(toggle_status) else cust_icon("W_GROUP_TOGGLE_DISP_NONE")
            if (elinked):
                ractions.active = False
                ractions.label(text="", icon_value=icon)
            else:
                op = ractions.operator("scatter5.batch_toggle", text="", icon_value=icon, emboss=False,)
                op.propname = "s_display_allow"
                op.emitter_name = e.name
                op.group_name = ""
                op.setvalue = str(not any(toggle_status))

            rightactions.separator(factor=0.991111)

        #Scatter List Templates 

        ui_list.scale_y = addon_prefs().ui_selection_y
        UL_type = "SCATTER5_UL_list_scatter_large" if lister_large else "SCATTER5_UL_list_scatter_stats" if lister_stats else None
        ui_list.template_list(UL_type, "", e.scatter5, "particle_interface_items", e.scatter5, "particle_interface_idx", type="DEFAULT", rows=max(len(e.scatter5.particle_interface_items),6),)

        if (lister_large):

            #Operators side menu
            
            ope = template.column(align=True)

            #add
            
            add = ope.column(align=True)
            if (elinked):
                add.enabled = False
            op = add.operator("scatter5.add_psy_simple",text="",icon="ADD",)
            op.emitter_name = e.name
            op.surfaces_names = "_!#!_".join([o.name for o in bpy.context.selected_objects if (o.type=="MESH")])
            op.instances_names = "_!#!_".join([o.name for o in bpy.context.selected_objects])
            op.psy_color_random = True 

            #remove
            
            rem = ope.column(align=True)
            rem.enabled = not ((psy_active is None) and (group_active is None))
            if (elinked):
                rem.enabled = False
            op = rem.operator("scatter5.remove_system",text="",icon="REMOVE",)
            op.emitter_name = e.name
            op.method = "dynamic_uilist"
            op.undo_push = True

            ope.separator()

            #selection menu

            menu = ope.row()
            menu.context_pointer_set("pass_ui_arg_emitter", e)
            menu.menu("SCATTER5_MT_selection_menu", icon='DOWNARROW_HLT', text="",)

            #move up & down

            ope.separator()        

            updo = ope.column(align=True)
            updo.enabled = epsys_len>0
            if (elinked):
                updo.enabled = False
            op = updo.operator("scatter5.move_interface_items",text="",icon="TRIA_UP",)
            op.emitter_name = e.name
            op.direction = "UP"
            op = updo.operator("scatter5.move_interface_items",text="",icon="TRIA_DOWN",)
            op.emitter_name = e.name
            op.direction = "DOWN"

        #Update global len 

        total_psys_len+= epsys_len

        ui_list.separator(factor=2.501)

        continue

    #emitter loop over
        
    ####################### draw grand total scene Recap?

    scene_row = scene_col.row()
    scene_box = scene_row.box()

    trow = scene_box.row(align=True)
    trow.scale_y = addon_prefs().ui_lister_scale_y

    sub = trow.row()
    sub.label(text=f'{bpy.context.scene.name} → {len(scene_emitters)} {translate("Emitter(s)")} → {total_psys_len} {translate("System(s)")}', icon="SCENE_DATA",)

    #rightside

    if (lister_stats and total_psys_len):

        rightactions = trow.row()
        rightactions.alignment = "RIGHT"

        infoactions = rightactions.split()
        infoactions.active = False
        infoactions.scale_x = 0.75
        
        infoactions.label(text= square_area_repr(total_area_len), icon="SURFACE_NSURFACE",)
        infoactions.label(text=count_repr(total_viewport_len, unit="Pts"), icon="RESTRICT_VIEW_OFF")
        infoactions.label(text=count_repr(total_render_len, unit="Pts"), icon="RESTRICT_RENDER_OFF")

    if (lister_large and total_psys_len):

        trow.separator_spacer()

        rightactions = trow.row(align=True)
        rightactions.scale_x = 0.95

        #select
        ractions = rightactions.row(align=True)
        ractions.scale_x = 0.90
        toggle_status = [p.sel for p in all_scene_psys]
        icon = cust_icon("W_GROUP_TOGGLE_SEL_ALL") if all(toggle_status) else cust_icon("W_GROUP_TOGGLE_SEL_SOME") if any(toggle_status) else cust_icon("W_GROUP_TOGGLE_SEL_NONE")
        op = ractions.operator("scatter5.batch_toggle", text="", icon_value=icon, emboss=False,)
        op.propname = "sel"
        op.scene_name = bpy.context.scene.name
        op.group_name = ""
        op.setvalue = str(not any(toggle_status))

        #hide viewport
        ractions = rightactions.row(align=True)
        toggle_status = [not p.hide_viewport for p in all_scene_psys]
        icon = cust_icon("W_GROUP_TOGGLE_VIEW_ALL") if all(toggle_status) else cust_icon("W_GROUP_TOGGLE_VIEW_SOME") if any(toggle_status) else cust_icon("W_GROUP_TOGGLE_VIEW_NONE")
        op = ractions.operator("scatter5.batch_toggle", text="", icon_value=icon, emboss=False,)
        op.propname = "hide_viewport"
        op.scene_name = bpy.context.scene.name
        op.group_name = ""
        op.setvalue = str(any(toggle_status))

        #hide render
        ractions = rightactions.row(align=True)
        toggle_status = [not p.hide_render for p in all_scene_psys]
        icon = cust_icon("W_GROUP_TOGGLE_RENDER_ALL") if all(toggle_status) else cust_icon("W_GROUP_TOGGLE_RENDER_SOME") if any(toggle_status) else cust_icon("W_GROUP_TOGGLE_RENDER_NONE")
        op = ractions.operator("scatter5.batch_toggle", text="", icon_value=icon, emboss=False,)
        op.propname = "hide_render"
        op.scene_name = bpy.context.scene.name
        op.group_name = ""
        op.setvalue = str(any(toggle_status))

        #lock
        ractions = rightactions.row(align=True)
        ractions.scale_x = 0.90
        toggle_status = [p.is_all_locked() for p in all_scene_psys]
        icon = cust_icon("W_GROUP_TOGGLE_LOCK_ALL") if all(toggle_status) else cust_icon("W_GROUP_TOGGLE_LOCK_SOME") if any(toggle_status) else cust_icon("W_GROUP_TOGGLE_LOCK_NONE")
        op = ractions.operator("scatter5.batch_toggle", text="", icon_value=icon, emboss=False,)
        op.propname = "lock"
        op.scene_name = bpy.context.scene.name
        op.group_name = ""
        op.setvalue = "lock_special"

        #separator
        rightactions.separator(factor=0.5) ; rightactions.label(text="",icon_value=cust_icon("W_BAR_VERTICAL")) ; rightactions.separator(factor=0.5)

        #dice
        ractions = rightactions.row(align=True)
        op = ractions.operator("scatter5.batch_randomize", text="", icon_value=cust_icon("W_GROUP_TOGGLE_DICE"), emboss=False,)
        op.scene_name = bpy.context.scene.name
        op.group_name = ""
        
        #separator
        rightactions.separator(factor=0.5) ; rightactions.label(text="",icon_value=cust_icon("W_BAR_VERTICAL")) ; rightactions.separator(factor=0.5)

        #percentage
        ractions = rightactions.row(align=True)
        toggle_status = [p.s_visibility_view_allow for p in all_scene_psys]
        icon = cust_icon("W_GROUP_TOGGLE_PERC_ALL") if all(toggle_status) else cust_icon("W_GROUP_TOGGLE_PERC_SOME") if any(toggle_status) else cust_icon("W_GROUP_TOGGLE_PERC_NONE")
        op = ractions.operator("scatter5.batch_toggle", text="", icon_value=icon, emboss=False,)
        op.propname = "s_visibility_view_allow"
        op.scene_name = bpy.context.scene.name
        op.group_name = ""
        op.setvalue = str(not any(toggle_status))

        #maxload
        ractions = rightactions.row(align=True)
        toggle_status = [p.s_visibility_maxload_allow for p in all_scene_psys]
        icon = cust_icon("W_GROUP_TOGGLE_MAXLOAD_ALL") if all(toggle_status) else cust_icon("W_GROUP_TOGGLE_MAXLOAD_SOME") if any(toggle_status) else cust_icon("W_GROUP_TOGGLE_MAXLOAD_NONE")
        op = ractions.operator("scatter5.batch_toggle", text="", icon_value=icon, emboss=False,)
        op.propname = "s_visibility_maxload_allow"
        op.scene_name = bpy.context.scene.name
        op.group_name = ""
        op.setvalue = str(not any(toggle_status))

        #preview area
        ractions = rightactions.row(align=True)
        toggle_status = [p.s_visibility_facepreview_allow for p in all_scene_psys]
        icon = cust_icon("W_GROUP_TOGGLE_PREV_ALL") if all(toggle_status) else cust_icon("W_GROUP_TOGGLE_PREV_SOME") if any(toggle_status) else cust_icon("W_GROUP_TOGGLE_PREV_NONE")
        op = ractions.operator("scatter5.batch_toggle", text="", icon_value=icon, emboss=False,)
        op.propname = "s_visibility_facepreview_allow"
        op.scene_name = bpy.context.scene.name
        op.group_name = ""
        op.setvalue = str(not any(toggle_status))

        #cam opti
        ractions = rightactions.row(align=True)
        toggle_status = [p.s_visibility_cam_allow for p in all_scene_psys]
        icon = cust_icon("W_GROUP_TOGGLE_CLIP_ALL") if all(toggle_status) else cust_icon("W_GROUP_TOGGLE_CLIP_SOME") if any(toggle_status) else cust_icon("W_GROUP_TOGGLE_CLIP_NONE")
        op = ractions.operator("scatter5.batch_toggle", text="", icon_value=icon, emboss=False,)
        op.propname = "s_visibility_cam_allow"
        op.scene_name = bpy.context.scene.name
        op.group_name = ""
        op.setvalue = str(not any(toggle_status))

        #separator
        rightactions.separator(factor=0.5) ; rightactions.label(text="",icon_value=cust_icon("W_BAR_VERTICAL")) ; rightactions.separator(factor=0.5)

        #display as
        ractions = rightactions.row(align=True)
        toggle_status = [p.s_display_allow for p in all_scene_psys]
        icon = cust_icon("W_GROUP_TOGGLE_DISP_ALL") if all(toggle_status) else cust_icon("W_GROUP_TOGGLE_DISP_SOME") if any(toggle_status) else cust_icon("W_GROUP_TOGGLE_DISP_NONE")
        op = ractions.operator("scatter5.batch_toggle", text="", icon_value=icon, emboss=False,)
        op.propname = "s_display_allow"
        op.scene_name = bpy.context.scene.name
        op.group_name = ""
        op.setvalue = str(not any(toggle_status))

        rightactions.separator(factor=0.991111)

    #Operators side menu
    
    if (lister_large):

        ope = scene_row.row()

        #disable clear all for now and just leave a space
        
        trash = ope.row()
        trash.operator("scatter5.dummy", text="", icon="BLANK1", emboss=False,)
    
        # op = trash.operator("scatter5.remove_system",text="", icon="TRASH")
        # op.scene_name = bpy.context.scene.name
        # op.method  = "clear"
        # op.undo_push = True

    #separator right below scene col
    scene_col.separator(factor=1.001)

    return 



#    .oooooo.   oooo
#   d8P'  `Y8b  `888
#  888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
#  888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
#  888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
#  `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#   `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'


classes = (
    
    SCATTER5_OT_impost_addonprefs,

    )


#if __name__ == "__main__":
#    register()