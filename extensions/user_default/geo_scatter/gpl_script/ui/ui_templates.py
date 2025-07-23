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
#       .                                          oooo                .
#     .o8                                          `888              .o8
#   .o888oo  .ooooo.  ooo. .oo.  .oo.   oo.ooooo.   888   .oooo.   .o888oo  .ooooo.
#     888   d88' `88b `888P"Y88bP"Y88b   888' `88b  888  `P  )88b    888   d88' `88b
#     888   888ooo888  888   888   888   888   888  888   .oP"888    888   888ooo888
#     888 . 888    .o  888   888   888   888   888  888  d8(  888    888 . 888    .o
#     "888" `Y8bod8P' o888o o888o o888o  888bod8P' o888o `Y888""8o   "888" `Y8bod8P'
#                                        888
#                                       o888o
#####################################################################################################


import bpy 

from .. resources.icons import cust_icon
from .. translations import translate

from . ui_menus import SCATTER5_PT_docs


#  .oooooo..o                                                       .
# d8P'    `Y8                                                     .o8
# Y88bo.       .ooooo.  oo.ooooo.   .oooo.   oooo d8b  .oooo.   .o888oo  .ooooo.  oooo d8b  .oooo.o
#  `"Y8888o.  d88' `88b  888' `88b `P  )88b  `888""8P `P  )88b    888   d88' `88b `888""8P d88(  "8
#      `"Y88b 888ooo888  888   888  .oP"888   888      .oP"888    888   888   888  888     `"Y88b.
# oo     .d8P 888    .o  888   888 d8(  888   888     d8(  888    888 . 888   888  888     o.  )88b
# 8""88888P'  `Y8bod8P'  888bod8P' `Y888""8o d888b    `Y888""8o   "888" `Y8bod8P' d888b    8""888P'
#                        888
#                       o888o


def separator_box_out(layout):
    """spacing between box panels"""

    from ... __init__ import addon_prefs

    height = addon_prefs().ui_boxpanel_separator
    return layout.separator(factor=height)


def separator_box_in(layout):
    """spacing at the end of a box panel"""

    from ... __init__ import addon_prefs

    if addon_prefs().ui_use_dark_box:
          return layout.separator(factor=0.3)
    else: return layout.separator(factor=0.3)


# oooooooooo.                             ooooooooo.                                   oooo
# `888'   `Y8b                            `888   `Y88.                                 `888
#  888     888  .ooooo.  oooo    ooo       888   .d88'  .oooo.   ooo. .oo.    .ooooo.   888
#  888oooo888' d88' `88b  `88b..8P'        888ooo88P'  `P  )88b  `888P"Y88b  d88' `88b  888
#  888    `88b 888   888    Y888'          888          .oP"888   888   888  888ooo888  888
#  888    .88P 888   888  .o8"'88b         888         d8(  888   888   888  888    .o  888
# o888bood8P'  `Y8bod8P' o88'   888o      o888o        `Y888""8o o888o o888o `Y8bod8P' o888o


def box_panel(layout,
              panel_icon="", #Panel Header icon
              panel_name="", #Panel Header title
              panelopen_propname="", #String of the bool property property-name scatter5.ui panel close
              master_category_bool="", #Optional: For Tweak panels, we have a psy/group active master bool toggle available
              popover_gearwheel="", #Optional: For Tweak panels, we have a psy/group preference settings popover
              popover_info="", #Optional: Documentation popover panel 
              popover_uilayout_context_set="", #Optional: passing an argument to the popover panel. can be context_string_set() or context_pointer_set(). Additionally, should be the name of the s_category for tweaking panels
              is_warning_panel=False, #Panel with a warning icon on them
              is_tweaking_panel=False, #Special drawing for panels contained in the lead tweak panel
              is_always_open=False, #Force panel to be always open
              return_subpanel=False, #Return an extra box layout (double box column aligned with each others)
              ):
    """draw sub panel opening template, use fct to add own settings""" 

    from ... __init__ import addon_prefs
    
    scat_ui      = bpy.context.window_manager.scatter5.ui
    scat_scene   = bpy.context.scene.scatter5
    emitter      = scat_scene.emitter
    psy_active   = emitter.scatter5.get_psy_active() if (emitter) else None
    group_active = emitter.scatter5.get_group_active() if (emitter) else None
    active       = psy_active if (psy_active is not None) else group_active
    
    if (is_always_open):
        is_open = True 
    else:
        assert hasattr(scat_ui, panelopen_propname), f"ERROR: ui_templates.box_panel(): '{panelopen_propname}' property not found in 'bpy.context.window_manager.scatter5.ui'"
        is_open = getattr(scat_ui,panelopen_propname)

    #determine layout style

    if (addon_prefs().ui_use_dark_box):
        
        col = layout.column(align=True)
        box = col.box()
        header = box.box().row(align=True)
        
    elif (not addon_prefs().ui_use_dark_box):
        
        col = layout.column(align=True)
        header = col.box().row(align=True)
        header.scale_y = 1.1
        
        if (is_open):
            box = col.box()
            box.separator(factor=-1)
                
        elif (not is_open):
            box = None 
        
    #ui custom panel height
    header.scale_y = addon_prefs().ui_boxpanel_height

    #use open/close arrow icons style instead
    if (not addon_prefs().ui_show_boxpanel_icon):
        panel_icon = "W_PANEL_OPEN" if is_open else "W_PANEL_CLOSED"

        #special active icon behavior for tweaking panels in both particle systems and group systems 
        if ((is_tweaking_panel==True) and (active is not None)):

                #popover panel arg should be str
                if (type(popover_uilayout_context_set) is str):
                
                    s_category = popover_uilayout_context_set
                    if (active.is_category_used(s_category)): #Both group and particle collection property should have this method!
                        panel_icon += "_ACTIVE"

    #generic title open/close + icon on the left

    args={"text":panel_name, "emboss":False,}
    
    if (panel_icon):
        if (type(panel_icon) is int):
              args["icon_value"]=panel_icon
        elif (panel_icon.startswith("W_")):
              args["icon_value"]=cust_icon(panel_icon)
        else: args["icon"]=panel_icon

    title = header.row(align=True)
    title.alignment = "LEFT"
    title.prop(scat_ui, panelopen_propname, **args)

    #because everything is aligned on the left, if title is too tiny you can miss the hitbox
    hiddenprop = header.row(align=True)
    hiddenprop.prop(scat_ui, panelopen_propname, text=" ", icon="BLANK1", emboss=False,)

    toolbar = header.row(align=True)
    toolbar.alignment = "RIGHT"

    #category master toggle for tweaking active psy 

    if (master_category_bool!=""):
        
        if (active is not None):
            
            button = toolbar.row(align=True)
            button.scale_y = 0.9
            button.emboss = "NONE"
            button.active = True
            button.prop(active, master_category_bool, text="", icon_value=cust_icon(f"W_CHECKBOX_{str(getattr(active,master_category_bool)).upper()}"),)

        else: 
            button = toolbar.row(align=True)
            button.scale_y = 0.9
            button.active = True
            button.label(text="", icon="BLANK1",)

    #preference gear-panel popovers ? 

    if (popover_gearwheel!=""):

        button = toolbar.row(align=True)
        button.scale_x = 0.95
        button.active = False
        button.emboss = "NONE"
        icon_value = cust_icon("W_PREFERENCES")

        #for psys, special icon for this panel
        if (is_tweaking_panel and psy_active):

            if (type(popover_uilayout_context_set) is str):
                    
                #if settings category is locked, display lock icon
                s_category = popover_uilayout_context_set
                is_locked = getattr(psy_active, f"{s_category}_locked")
                if (is_locked): 
                    icon_value = cust_icon("W_LOCKED_GREY")
                else:
                    #is synch, display synch icon 
                    is_synch = psy_active.is_synchronized(s_category)
                    if is_synch: 
                        icon_value = cust_icon("W_ARROW_SYNC_GREY")
                        #later on, will need to also consider frozen state
                    
        #pass an ui arg to this panel? 
        if (popover_uilayout_context_set):
            if (type(popover_uilayout_context_set) is str):
                  button.context_string_set("pass_ui_arg_popover",popover_uilayout_context_set)
            else: button.context_pointer_set("pass_ui_arg_popover",popover_uilayout_context_set)
        
        #& draw the popover
        button.popover(panel=popover_gearwheel, text="", icon_value=icon_value,)

    #documentation popover?

    if (popover_info!=""):

        button = toolbar.row(align=True)
        button.scale_x = 0.95
        button.active = True
        button.emboss = "NONE"

        #pass an ui arg to this panel? 
        if (popover_uilayout_context_set):
            if (type(popover_uilayout_context_set) is str):
                  button.context_string_set("pass_ui_arg_popover",popover_uilayout_context_set)
            else: button.context_pointer_set("pass_ui_arg_popover",popover_uilayout_context_set)
        
        #& draw the popover
        button.popover(panel=popover_info, text="", icon_value=cust_icon("W_INFO"),)

    #big warning icon a panel right side? 

    if (is_warning_panel):

        button = toolbar.row(align=True)
        button.scale_x = 0.95
        button.alert = True
        button.active = False
        button.label(text="", icon="INFO")

    #return layout and opening values
    
    if (return_subpanel): #original column layout information, useful for more complex layout style, boxes aligned together ect..
        return col, box, is_open
    return box, is_open  


# ooooooooooooo                                 oooo
# 8'   888   `8                                 `888
#      888       .ooooo.   .oooooooo  .oooooooo  888   .ooooo.
#      888      d88' `88b 888' `88b  888' `88b   888  d88' `88b
#      888      888   888 888   888  888   888   888  888ooo888
#      888      888   888 `88bod8P'  `88bod8P'   888  888    .o
#     o888o     `Y8bod8P' `8oooooo.  `8oooooo.  o888o `Y8bod8P'
#                         d"     YD  d"     YD
#                         "Y88888P'  "Y88888P'

def bool_toggle(layout, data, property_name,
                label="",
                icon="", #If no icon passed, will use regular checkbox style by default, even if addonprefs style option is set to icon
                enabled=True,
                active=True,
                invert_checkbox=False,
                arrowopen_propname="", #Boolean ui Property name to use in case of open/close arrows
                use_layout_left_spacer=True, #Draw a little spacer on the left of the bool property & it's sublayout
                use_sublayout_indentation=True, #Use left indentation spacer for returned column sublayout
                return_sublayout=False, #Return column sublayout, layout under the boolean property, in case of enabled feature with subsettings
                return_rowlayout=False, #Return the title row layout, in case of extra drawing added in there
                draw_condition=True, #Define if we are drawing this layout template at the first place. If set to False, we skip the drawing altogether
                ):
    """draw feature checkbox template, customizable with icons, arrow to open the option sub-settings"""
        
    #check for condition of feature availability, maybe shouldn't draw anything 
    
    if (not draw_condition):
        if (return_sublayout):
            if (return_rowlayout):
                return None,None,None
            return None,None
        return None 

    from ... __init__ import addon_prefs
    scat_ui = bpy.context.window_manager.scatter5.ui
    is_toggled = getattr(data,property_name)==True
    is_open = None

    #main layout

    MainCol = layout.column(align=True)

    #main toggle row

    Boolrow = MainCol.row(align=True)

    #draw arrow open/close button on the left

    if (arrowopen_propname and addon_prefs().ui_bool_use_arrow_openclose):

        if (arrowopen_propname=="*USE_SPACER*"): #rare gui option, in case don't want to use arrows
            Boolrow.separator(factor=3.25)

        else:
            if ("." in arrowopen_propname):
                  is_open = eval(arrowopen_propname)
            else: is_open = getattr(scat_ui,arrowopen_propname)

            arrow = Boolrow.row(align=True)
            arrow.scale_x = 0.9
            arrow.prop(scat_ui, arrowopen_propname, text="", emboss=False, icon_value=cust_icon("W_PANEL_OPEN" if is_open else "W_PANEL_CLOSED"),)

            Boolrow.separator(factor=0.5)

    #draw small space on the left ?
    
    elif (use_layout_left_spacer):
        Boolrow.separator(factor=1.5)

    #draw toggle, two possible style
    
    if (addon_prefs().ui_bool_use_standard or (icon=="")):

        #classic checkbox style
        prop = Boolrow.row(align=True)
        prop.scale_y = 1.05
        prop.enabled = enabled
        prop.active = active
        prop.prop(data, property_name, text=label, invert_checkbox=invert_checkbox,)

    else:

        #or icon style
        if (addon_prefs().ui_bool_use_iconcross and not is_toggled and not invert_checkbox):
            args = {"text":"", "icon":"PANEL_CLOSE"}
        else:
            if (not icon.startswith("W_")): 
                  args = {"text":"", "icon":icon}
            else: args = {"text":"", "icon_value":cust_icon(icon)}
            
        if (invert_checkbox==True):
            args["invert_checkbox"] = True

        prop = Boolrow.row(align=True)
        prop.scale_y = 1.0
        prop.enabled = enabled
        prop.active = active
        prop.prop(data, property_name, **args )

        prop.separator()

        if (label!=""):
            prop.label(text=label)

    #just return toggle value?
    
    if (not return_sublayout):
        return None, is_toggled       

    #return layout for indentation style interface

    if (is_open is not None):
        active_feature = is_toggled
        is_toggled = is_open

    #main features layout, under

    FeaturesRow = MainCol.row()

    #create left indentation space
    if (is_toggled):
        
        if (use_layout_left_spacer):
            spacer = FeaturesRow.column()
            spacer.scale_x = 0.01
            
        if (use_sublayout_indentation):
            spacer = FeaturesRow.row()
            spacer.label(text="")
            spacer.scale_x = addon_prefs().ui_bool_indentation

    feature_col = FeaturesRow.column()

    if (is_open is not None):
        feature_col.enabled = enabled
        if (active):
              feature_col.active = active_feature
        else: feature_col.active = False

    #leave a little beathing gap
    if (is_toggled):
        feature_col.separator(factor=0.25)

    #special return values for drawing on the left space of the row? 
    if (return_rowlayout):
        feature_row = Boolrow.row()
        feature_row.enabled = enabled
        feature_row.active = active
        return feature_col, feature_row, is_toggled    

    return feature_col, is_toggled
        
