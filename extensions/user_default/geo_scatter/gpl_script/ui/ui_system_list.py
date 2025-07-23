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
# ooooo     ooo ooooo       .oooooo..o                          .                                    ooooo         o8o               .
# `888'     `8' `888'      d8P'    `Y8                        .o8                                    `888'         `"'             .o8
#  888       8   888       Y88bo.      oooo    ooo  .oooo.o .o888oo  .ooooo.  ooo. .oo.  .oo.         888         oooo   .oooo.o .o888oo
#  888       8   888        `"Y8888o.   `88.  .8'  d88(  "8   888   d88' `88b `888P"Y88bP"Y88b        888         `888  d88(  "8   888
#  888       8   888            `"Y88b   `88..8'   `"Y88b.    888   888ooo888  888   888   888        888          888  `"Y88b.    888
#  `88.    .8'   888       oo     .d8P    `888'    o.  )88b   888 . 888    .o  888   888   888        888       o  888  o.  )88b   888 .
#    `YbodP'    o888o      8""88888P'      .8'     8""888P'   "888" `Y8bod8P' o888o o888o o888o      o888ooooood8 o888o 8""888P'   "888"
#                                      .o..P'
#                                      `Y8P'
#####################################################################################################


import bpy

from ... __init__ import addon_prefs, blend_prefs

from .. resources.icons import cust_icon
from .. translations import translate

from .. utils.extra_utils import is_rendered_view
from .. utils.str_utils import word_wrap
from .. utils.math_utils import square_area_repr, count_repr

from .. scattering.emitter import can_add_psy_to_emitter


# ooooooooo.
# `888   `Y88.
#  888   .d88' oooo d8b  .ooooo.  oo.ooooo.   .oooo.o
#  888ooo88P'  `888""8P d88' `88b  888' `88b d88(  "8
#  888          888     888   888  888   888 `"Y88b.
#  888          888     888   888  888   888 o.  )88b
# o888o        d888b    `Y8bod8P'  888bod8P' 8""888P'
#                                  888
#                                 o888o


def interface_description_getter(self):

    match self.interface_item_type:
        case 'SCATTER_SYSTEM':
            desc = translate("Scatter-Group Selection:\n•Click on a group to set it active and reveal its properties.\n•If you'd like to tweak a system settings, please select the system, not the group!\n•Double click on a name to rename.\n•Shift-Click to conserve selection.\n•Alt-Click to isolate the selection viewport status")
        case 'GROUP_SYSTEM':
            desc = translate("Scatter-System Selection:\n•Click on a system to set it active and reveal its properties.\n•Double click on a name to rename.\n•Shift-Click to conserve selection.\n•Alt-Click to isolate the selection viewport status")
        case _:
            return 'DescriptionTypeError'

    desc += '.\n'

    itmdesc = self.get_interface_item_source().description if self.get_interface_item_source() else None
    if (itmdesc):
        desc = 'Item Description:\n' + itmdesc + '\n\n' + desc

    return desc

class SCATTER5_PR_particle_interface_items(bpy.types.PropertyGroup): 
    """bpy.context.object.scatter5.particle_interface_items, will be stored on emitter"""

    #these object.scatter5.particle_interface_items will be constantly rebuild on major user interaction

    #the type of ui item is 'GROUP_SYSTEM' or 'SCATTER_SYSTEM'
    interface_item_type : bpy.props.StringProperty() 
    
    #the name reference of the group
    interface_group_name : bpy.props.StringProperty()
    
    #the uuid reference of the psy
    interface_item_psy_uuid : bpy.props.IntProperty()
    
    #what kind of indent icon do we use? (if psy members of groups)
    interface_ident_icon : bpy.props.StringProperty()
    
    #do we add a separator spacer once the group stopped?
    interface_add_separator : bpy.props.BoolProperty()

    #show description of either group or scatter-system
    interface_description : bpy.props.StringProperty(
        get=interface_description_getter,
        )

    def get_interface_item_source(self):
        
        match self.interface_item_type:
            case 'SCATTER_SYSTEM':
                for p in [p for p in self.id_data.scatter5.particle_systems if (p.scatter_obj) and (p.uuid==self.interface_item_psy_uuid)]:
                    return p
            case 'GROUP_SYSTEM':
                for g in [g for g in self.id_data.scatter5.particle_groups if (g.name==self.interface_group_name)]:
                    return g
        return None

    def get_item_index(self):

        for i,itm in enumerate(self.id_data.scatter5.particle_interface_items):
            if (itm==self):
                return i

        return None


def ensure_particle_interface_items(objs=None):
    """ensure that the particle interface is drawn correctly, it has been implemeted in Geo-Scatter 5.4, and there might be some systems that need the interface to be initiated"""
    
    if (objs is None):
        objs = [o for o in bpy.data.objects if hasattr(o,'scatter5') and (o.scatter5.particle_systems or o.scatter5.particle_interface_items)]
        
    for o in objs:
        o.scatter5.particle_interface_refresh()
            
    return None


# ooooo     .                                    oooooooooo.
# `888'   .o8                                    `888'   `Y8b
#  888  .o888oo  .ooooo.  ooo. .oo.  .oo.         888      888 oooo d8b  .oooo.   oooo oooo    ooo
#  888    888   d88' `88b `888P"Y88bP"Y88b        888      888 `888""8P `P  )88b   `88. `88.  .8'
#  888    888   888ooo888  888   888   888        888      888  888      .oP"888    `88..]88..8'
#  888    888 . 888    .o  888   888   888        888     d88'  888     d8(  888     `888'`888'
# o888o   "888" `Y8bod8P' o888o o888o o888o      o888bood8P'   d888b    `Y888""8o     `8'  `8'


def UL_scatter_list_factory(lister_large=False, lister_stats=False,):
    """drawing item function for large/small item lists are highly similar"""

    def fct(self, context, layout, data, item, icon, active_data, active_propname):

        if (not item):
            layout.label(text="ERROR: Item is None")
            return None
        
        #draw scatter item 
        source_itm = item.get_interface_item_source()
        if (not source_itm):
            layout.label(text="ERROR: Can't find Item")
            return None    

        emitter = item.id_data

        #define main layout
        col = layout.column(align=True)
        row = col.row(align=True)
        row.scale_y = addon_prefs().ui_selection_y   
         
        if (lister_large or lister_stats):
            row.scale_y *= addon_prefs().ui_lister_scale_y
            row.separator(factor=0.8)

        match item.interface_item_type:
                
            case 'SCATTER_SYSTEM':
                
                p = source_itm

                #Indentation

                if (item.interface_ident_icon!=""): 
                    indent = row.row(align=True)
                    indent.scale_x = 0.85
                    indent.label(text="", icon_value=cust_icon(item.interface_ident_icon),)

                #Color & name (& optional link info)

                colname = row.row(align=True)
                colname.alignment = "LEFT"
                    
                color = colname.row()
                color.scale_x = 0.25
                color.active = True
                color.prop(p,"s_color",text="")
                    
                if (p.is_linked):
                    name = colname.row(align=True)
                    name.scale_x = 0.95
                    name.alignment = "LEFT"
                    name.label(text=p.name)
                    nameicon = name.row(align=True)
                    nameicon.alignment = "LEFT"
                    nameicon.scale_x = 0.8
                    nameicon.label(text="", icon="LINKED")
                else:
                    name = colname.row(align=True)
                    name.prop(p,"name", text="", emboss=False, )

                #Adjustments

                if ((lister_stats) and (item.interface_ident_icon=="")):

                    #need to adjust indentation in statistic inferface
                    space = row.row(align=True)
                    space.scale_x = 0.85
                    space.label(text="", icon="BLANK1",)
                
                #rightside

                if (lister_stats): #statistic special lister

                    rightactions = row.row(align=True)
                    rightactions.alignment = "RIGHT"

                    infoactions = rightactions.split()
                    infoactions.active = False
                    infoactions.scale_x = 0.75
                    infoactions.label(text= square_area_repr( p.get_surfaces_square_area(evaluate="gather") ), icon="SURFACE_NSURFACE",)
                    infoactions.label(text=count_repr(p.scatter_count_viewport_consider_hide_viewport, unit="Pts"), icon="RESTRICT_VIEW_OFF",)
                    infoactions.label(text=count_repr(p.scatter_count_render, unit="Pts"), icon="RESTRICT_RENDER_OFF",)
                    
                if (not lister_stats or lister_large): #normal lister and lister large

                    rightactions = row.row(align=True)
                    rightactions.alignment = "RIGHT"
                    rightactions.scale_x = 0.95
                    
                    #select
                    ractions = rightactions.row(align=True)
                    ractions.scale_x = 0.85
                    ractions.prop(p,"sel", text="", icon="RESTRICT_SELECT_OFF" if p.sel else "RESTRICT_SELECT_ON", emboss=False,)
                    
                    #hide viewport
                    ractions = rightactions.row(align=True)
                    ractions.scale_x = 1.0
                    ractions.prop(p, "hide_viewport", text="", icon="RESTRICT_VIEW_ON" if p.hide_viewport else "RESTRICT_VIEW_OFF", invert_checkbox=True, emboss=False,)
                        
                    #hide render
                    ractions = rightactions.row(align=True)
                    ractions.scale_x = 1.0
                    ractions.prop(p, "hide_render", text="", icon_value=cust_icon("W_SHOW_RENDER_OFF") if p.hide_render else cust_icon("W_SHOW_RENDER_ON"), invert_checkbox=True, emboss=False,)

                if (lister_large): #large interface lister only

                    #lock
                    ractions = rightactions.row(align=True)
                    ractions.scale_x = 0.90
                    ractions.prop(p,"lock",text="",icon="LOCKED" if p.is_all_locked() else "UNLOCKED", emboss=False, invert_checkbox=p.is_all_locked(),)

                    #separator
                    rightactions.separator(factor=0.5) ; rightactions.label(text="",icon_value=cust_icon("W_BAR_VERTICAL")) ; rightactions.separator(factor=0.5)
                    
                    #dice
                    ractions = rightactions.row(align=True)
                    if (p.is_linked):
                        ractions.active = False
                        ractions.label(text="", icon_value=cust_icon("W_SHOW_DICE"))
                    else:
                        op = ractions.operator("scatter5.batch_randomize", text="", icon_value=cust_icon("W_SHOW_DICE"), emboss=False,)
                        op.emitter_name = emitter.name
                        op.psy_name = p.name

                    #separator
                    rightactions.separator(factor=0.5) ; rightactions.label(text="",icon_value=cust_icon("W_BAR_VERTICAL")) ; rightactions.separator(factor=0.5)

                    #percentage
                    ractions = rightactions.row(align=True)
                    ractions.scale_x = 1.0
                    ractions.prop(p, "s_visibility_view_allow", text="", icon_value=cust_icon("W_SHOW_VIS_PERC_ON") if p.s_visibility_view_allow else cust_icon("W_SHOW_VIS_PERC_OFF"), emboss=False,)

                    #preview area
                    ractions = rightactions.row(align=True)
                    ractions.scale_x = 1.0
                    ractions.prop(p, "s_visibility_maxload_allow", text="", icon_value=cust_icon("W_SHOW_VIS_MAXLOAD_ON") if p.s_visibility_maxload_allow else cust_icon("W_SHOW_VIS_MAXLOAD_OFF"), emboss=False,)

                    #preview area
                    ractions = rightactions.row(align=True)
                    ractions.scale_x = 1.0
                    ractions.prop(p, "s_visibility_facepreview_allow", text="", icon_value=cust_icon("W_SHOW_VIS_VIEW_ON") if p.s_visibility_facepreview_allow else cust_icon("W_SHOW_VIS_VIEW_OFF"), emboss=False,)

                    #cam opti
                    ractions = rightactions.row(align=True)
                    ractions.scale_x = 1.0
                    ractions.prop(p, "s_visibility_cam_allow", text="", icon_value=cust_icon("W_SHOW_VIS_CLIP_ON") if p.s_visibility_cam_allow else cust_icon("W_SHOW_VIS_CLIP_OFF"), emboss=False,)

                    #separator
                    rightactions.separator(factor=0.5) ; rightactions.label(text="",icon_value=cust_icon("W_BAR_VERTICAL")) ; rightactions.separator(factor=0.5)

                    #display as
                    ractions = rightactions.row(align=True)
                    ractions.scale_x = 1.0
                    ractions.prop(p, "s_display_allow", text="", icon_value=cust_icon("W_SHOW_DISPLAY_ON") if p.s_display_allow else cust_icon("W_SHOW_DISPLAY_OFF"), emboss=False,)

                    rightactions.separator(factor=0.991111)

            case 'GROUP_SYSTEM':
                
                g = source_itm
                gpsys = [p for p in emitter.scatter5.particle_systems if (p.group!="") and (p.group==g.name) ]
                glinked = bool(emitter.library)
                
                #Arrow

                arrow = row.row(align=True)
                arrow.scale_x = 0.8
                op = arrow.operator("scatter5.exec_line", text="", icon="TRIA_DOWN" if g.open else "TRIA_RIGHT", emboss=False,)
                op.api = f"g = get_from_uid({emitter.session_uid}).scatter5.particle_groups['{g.name}'] ; setattr(g,'open', not getattr(g,'open'))"
                op.description = translate("Open/Close group interface items")
                #Name 

                name = row.row(align=True)
                name.prop(g,"name", text="", emboss=False,)

                #set of icons

                rightactions = row.row(align=True)
                rightactions.alignment = "RIGHT"
                rightactions.scale_x = 0.95

                if (not lister_stats or lister_large):

                    #select
                    ractions = rightactions.row(align=True)
                    ractions.scale_x = 0.90
                    toggle_status = [p.sel for p in gpsys]
                    icon = cust_icon("W_GROUP_TOGGLE_SEL_ALL") if all(toggle_status) else cust_icon("W_GROUP_TOGGLE_SEL_SOME") if any(toggle_status) else cust_icon("W_GROUP_TOGGLE_SEL_NONE")
                    if (glinked):
                        ractions.active = False
                        ractions.label(text="", icon_value=icon)
                    else:
                        op = ractions.operator("scatter5.batch_toggle", text="", icon_value=icon, emboss=False,)
                        op.propname = "sel"
                        op.emitter_name = emitter.name
                        op.group_name = g.name
                        op.setvalue = str(not any(toggle_status))

                    #hide viewport
                    ractions = rightactions.row(align=True)
                    toggle_status = [not p.hide_viewport for p in gpsys]
                    icon = cust_icon("W_GROUP_TOGGLE_VIEW_ALL") if all(toggle_status) else cust_icon("W_GROUP_TOGGLE_VIEW_SOME") if any(toggle_status) else cust_icon("W_GROUP_TOGGLE_VIEW_NONE")
                    op = ractions.operator("scatter5.batch_toggle", text="", icon_value=icon, emboss=False,)
                    op.propname = "hide_viewport"
                    op.emitter_session_uid = emitter.session_uid
                    op.group_name = g.name
                    op.setvalue = str(any(toggle_status))

                    #hide render
                    ractions = rightactions.row(align=True)
                    toggle_status = [not p.hide_render for p in gpsys]
                    icon = cust_icon("W_GROUP_TOGGLE_RENDER_ALL") if all(toggle_status) else cust_icon("W_GROUP_TOGGLE_RENDER_SOME") if any(toggle_status) else cust_icon("W_GROUP_TOGGLE_RENDER_NONE")
                    op = ractions.operator("scatter5.batch_toggle", text="", icon_value=icon, emboss=False,)
                    op.propname = "hide_render"
                    op.emitter_session_uid = emitter.session_uid
                    op.group_name = g.name
                    op.setvalue = str(any(toggle_status))

                #props only for large lister
                if (lister_large):

                    #lock
                    ractions = rightactions.row(align=True)
                    ractions.scale_x = 0.90
                    toggle_status = [p.is_all_locked() for p in gpsys]
                    icon = cust_icon("W_GROUP_TOGGLE_LOCK_ALL") if all(toggle_status) else cust_icon("W_GROUP_TOGGLE_LOCK_SOME") if any(toggle_status) else cust_icon("W_GROUP_TOGGLE_LOCK_NONE")
                    if (glinked):
                        ractions.active = False
                        ractions.label(text="", icon_value=icon)
                    else:
                        op = ractions.operator("scatter5.batch_toggle", text="", icon_value=icon, emboss=False,)
                        op.propname = "lock"
                        op.emitter_name = emitter.name
                        op.group_name = g.name
                        op.setvalue = "lock_special"

                    #separator
                    rightactions.separator(factor=0.5) ; rightactions.label(text="",icon_value=cust_icon("W_BAR_VERTICAL")) ; rightactions.separator(factor=0.5)

                    #dice
                    ractions = rightactions.row(align=True)
                    if (glinked):
                        ractions.active = False
                        ractions.label(text="", icon_value=cust_icon("W_GROUP_TOGGLE_DICE"),)
                    else:
                        op = ractions.operator("scatter5.batch_randomize", text="", icon_value=cust_icon("W_GROUP_TOGGLE_DICE"), emboss=False,)
                        op.emitter_name = emitter.name
                        op.group_name = g.name

                    #separator
                    rightactions.separator(factor=0.5) ; rightactions.label(text="",icon_value=cust_icon("W_BAR_VERTICAL")) ; rightactions.separator(factor=0.5)

                    #percentage
                    ractions = rightactions.row(align=True)
                    toggle_status = [p.s_visibility_view_allow for p in gpsys]
                    icon = cust_icon("W_GROUP_TOGGLE_PERC_ALL") if all(toggle_status) else cust_icon("W_GROUP_TOGGLE_PERC_SOME") if any(toggle_status) else cust_icon("W_GROUP_TOGGLE_PERC_NONE")
                    if (glinked):
                        ractions.active = False
                        ractions.label(text="", icon_value=icon)
                    else:
                        op = ractions.operator("scatter5.batch_toggle", text="", icon_value=icon, emboss=False,)
                        op.propname = "s_visibility_view_allow"
                        op.emitter_name = emitter.name
                        op.group_name = g.name
                        op.setvalue = str(not any(toggle_status))

                    #maxload
                    ractions = rightactions.row(align=True)
                    toggle_status = [p.s_visibility_maxload_allow for p in gpsys]
                    icon = cust_icon("W_GROUP_TOGGLE_MAXLOAD_ALL") if all(toggle_status) else cust_icon("W_GROUP_TOGGLE_MAXLOAD_SOME") if any(toggle_status) else cust_icon("W_GROUP_TOGGLE_MAXLOAD_NONE")
                    if (glinked):
                        ractions.active = False
                        ractions.label(text="", icon_value=icon)
                    else:
                        op = ractions.operator("scatter5.batch_toggle", text="", icon_value=icon, emboss=False,)
                        op.propname = "s_visibility_maxload_allow"
                        op.emitter_name = emitter.name
                        op.group_name = g.name
                        op.setvalue = str(not any(toggle_status))

                    #preview area
                    ractions = rightactions.row(align=True)
                    toggle_status = [p.s_visibility_facepreview_allow for p in gpsys]
                    icon = cust_icon("W_GROUP_TOGGLE_PREV_ALL") if all(toggle_status) else cust_icon("W_GROUP_TOGGLE_PREV_SOME") if any(toggle_status) else cust_icon("W_GROUP_TOGGLE_PREV_NONE")
                    if (glinked):
                        ractions.active = False
                        ractions.label(text="", icon_value=icon)
                    else:
                        op = ractions.operator("scatter5.batch_toggle", text="", icon_value=icon, emboss=False,)
                        op.propname = "s_visibility_facepreview_allow"
                        op.emitter_name = emitter.name
                        op.group_name = g.name
                        op.setvalue = str(not any(toggle_status))

                    #cam opti
                    ractions = rightactions.row(align=True)
                    toggle_status = [p.s_visibility_cam_allow for p in gpsys]
                    icon = cust_icon("W_GROUP_TOGGLE_CLIP_ALL") if all(toggle_status) else cust_icon("W_GROUP_TOGGLE_CLIP_SOME") if any(toggle_status) else cust_icon("W_GROUP_TOGGLE_CLIP_NONE")
                    if (glinked):
                        ractions.active = False
                        ractions.label(text="", icon_value=icon)
                    else:
                        op = ractions.operator("scatter5.batch_toggle", text="", icon_value=icon, emboss=False,)
                        op.propname = "s_visibility_cam_allow"
                        op.emitter_name = emitter.name
                        op.group_name = g.name
                        op.setvalue = str(not any(toggle_status))

                    #separator
                    rightactions.separator(factor=0.5) ; rightactions.label(text="",icon_value=cust_icon("W_BAR_VERTICAL")) ; rightactions.separator(factor=0.5)

                    #display as
                    ractions = rightactions.row(align=True)
                    toggle_status = [p.s_display_allow for p in gpsys]
                    icon = cust_icon("W_GROUP_TOGGLE_DISP_ALL") if all(toggle_status) else cust_icon("W_GROUP_TOGGLE_DISP_SOME") if any(toggle_status) else cust_icon("W_GROUP_TOGGLE_DISP_NONE")
                    if (glinked):
                        ractions.active = False
                        ractions.label(text="", icon_value=icon)
                    else:
                        op = ractions.operator("scatter5.batch_toggle", text="", icon_value=icon, emboss=False,)
                        op.propname = "s_display_allow"
                        op.emitter_name = emitter.name
                        op.group_name = g.name
                        op.setvalue = str(not any(toggle_status))
                    
                    rightactions.separator(factor=0.991111)

        #draw separator
        if (item.interface_add_separator):

            #larger if large version
            if (lister_large or lister_stats):
                  col.separator(factor=1.6)
            else: col.separator(factor=2.0)

        return None

    return fct


class SCATTER5_UL_list_scatter_small(bpy.types.UIList):
    """system-list compact size, for N panel & quick list shortcut"""

    draw_item = UL_scatter_list_factory()

class SCATTER5_UL_list_scatter_large(bpy.types.UIList):
    """system-list full options, for manager interface"""
    
    draw_item = UL_scatter_list_factory(lister_large=True)

class SCATTER5_UL_list_scatter_stats(bpy.types.UIList):
    """system-list full options, for manager interface"""
    
    draw_item = UL_scatter_list_factory(lister_stats=True)



# oooooooooo.                                            oooo   o8o               .
# `888'   `Y8b                                           `888   `"'             .o8
#  888      888 oooo d8b  .oooo.   oooo oooo    ooo       888  oooo   .oooo.o .o888oo
#  888      888 `888""8P `P  )88b   `88. `88.  .8'        888  `888  d88(  "8   888
#  888      888  888      .oP"888    `88..]88..8'         888   888  `"Y88b.    888
#  888     d88'  888     d8(  888     `888'`888'          888   888  o.  )88b   888 .
# o888bood8P'   d888b    `Y888""8o     `8'  `8'          o888o o888o 8""888P'   "888"


def draw_particle_selection_inner(layout=None, context=None, extra_layout=None, scat_scene=None, emitter=None, psy_active=None, group_active=None,): 
    """used in tweaking panel but also in quick lister interface"""

    from .. ui.ui_notification import draw_notification_system_lister
    
    #emitter info
    assert (emitter is not None)
    elinked = bool(emitter.library)
    
    scat_addon = addon_prefs()
    scat_data  = blend_prefs()
    
    row = layout.row()

    #draw left spacers
    row.separator(factor=0.5)

    #draw list template
    template = row.column()

    ui_list = template.column()
    ui_list.scale_y = scat_addon.ui_selection_y
    ui_list.template_list(
        "SCATTER5_UL_list_scatter_small", "", emitter.scatter5, "particle_interface_items", emitter.scatter5, "particle_interface_idx",
        type="DEFAULT", rows=10, item_dyntip_propname="interface_description",
        )
    
    #description system on hover, 
    if ((scat_data.show_description) and (psy_active or group_active)):
        descrow = ui_list.row()
        descrow.scale_y = 1.15
        if (psy_active):
            descrow.prop(psy_active, "description", text="", placeholder=translate("Your Description Here"),)
        if (group_active):
            descrow.prop(group_active, "description", text="", placeholder=translate("Your Description Here"),)

    #developer debug info

    if (scat_addon.debug_interface) and (extra_layout):
        
        outerbox = extra_layout.box()
        outerbox.separator(factor=0.5)
        outerbox.label(text="Debug Interface, Dev Only", icon="GHOST_DISABLED",)
        outerbox.alignment = "LEFT"
        outerbox.scale_y = 0.8
        
        nfo = outerbox.column(align=True)
        nfo.box().label(text=f"emitter.get_psy_active() = {psy_active.name if psy_active else '/'}")
        nfo.box().label(text=f"emitter.get_group_active() = {group_active.name if group_active else '/'}")
        nfo.prop(emitter.scatter5,"particle_interface_idx", text="emitter.particle_interface_idx",)
        nfo.operator("scatter5.exec_line", text="emitter.particle_interface_refresh()").api = f"emitter.scatter5.particle_interface_refresh()"

        outerbox.separator(factor=0.5)
        outerbox.label(text="emitter.particle_systems:")

        debugcol = outerbox.column(align=True)
        for i,p in enumerate(emitter.scatter5.particle_systems):
            debugr = debugcol.row(align=True)
            debugr.scale_y = 0.7
            debugrr = debugr.row(align=True)
            debugrr.scale_x = 0.3
            debugrr.label(text=str(i),)
            debugrr = debugr.row(align=True)
            debugrr.scale_x = 0.3
            debugrr.prop(p,"s_color",text="",)
            debugr.prop(p,"name",text="",)
            debugr.prop(p,"group",text="")
            debugr.prop(p,"active",text="",icon="DOT")
            debugr.prop(p,"sel",text="",icon="RESTRICT_SELECT_OFF")

        outerbox.separator(factor=0.5)
        outerbox.label(text="emitter.particle_groups:")

        debugcol = outerbox.column(align=True)
        for i,g in enumerate(emitter.scatter5.particle_groups):
            debugr = debugcol.row(align=True)
            debugrr = debugr.row(align=True)
            debugrr.scale_x = 0.3
            debugrr.label(text=str(i),)
            debugr.prop(g,"name", text="", )
            debugr.prop(g,"name_bis", text="", )
            debugr.prop(g,"is_linked", text="", icon="LINKED",)
            debugr.prop(g,"open", text="", icon="DISCLOSURE_TRI_DOWN",)
            
            debugc = debugcol.column(align=True)
            debugc.scale_y = 1.1
            for p in g.get_psy_members():
                debugc.label(text=p.name, icon="PARTICLES")
                 
        if (psy_active is not None): 
            outerbox.separator(factor=0.5)
            outerbox.label(text="psy_active info:")
            
            nfo = outerbox.column(align=True)
            nfo.use_property_split = True
            nfo.prop(psy_active, "name")
            nfo.prop(psy_active, "name_bis")
            nfo.prop(psy_active, "scatter_obj",text="so")
            if (psy_active.scatter_obj):
                nfo.prop(psy_active.scatter_obj.scatter5, "original_emitter",text="so.original_emitter")
                nfo.prop(psy_active.id_data,"name", text="emitter.name")
                mod = psy_active.get_scatter_mod(strict=True, raise_exception=False,)
                if (mod):
                    nfo.prop(mod, "name",text="so.mod.name")
                    nfo.prop(mod, "node_group",text="so.mod.node_group")
            nfo.prop(psy_active, "blender_version")
            nfo.prop(psy_active, "addon_version")
            nfo.prop(psy_active, "addon_type")
            nfo.prop(psy_active,"is_linked", icon="LINKED",)
            nfo.prop(psy_active, "uuid", emboss=True,)
            nfo.prop(psy_active, "blendfile_uuid", emboss=True,)
            nfo.prop(scat_data, "blendfile_uuid", emboss=True,)

        outerbox.separator(factor=0.5)

    #send users some notifications and/or solutions
    
    draw_notification_system_lister(
        layout=template, context=context, extra_layout=extra_layout, scat_scene=scat_scene, 
        emitter=emitter, psy_active=psy_active, group_active=group_active,
        )

    #Operators side menu
    
    ope = row.column(align=True)

    #add
    
    add = ope.column(align=True)
    add.enabled = can_add_psy_to_emitter()
    op = add.operator("scatter5.add_psy_simple",text="",icon="ADD",)
    op.emitter_name = emitter.name
    op.surfaces_names = "_!#!_".join([o.name for o in bpy.context.selected_objects if (o.type=="MESH")])
    op.instances_names = "_!#!_".join([o.name for o in bpy.context.selected_objects])
    op.psy_color_random = True 

    #remove
    
    rem = ope.column(align=True)
    rem.enabled = not ((psy_active is None) and (group_active is None))
    if (elinked):
        rem.enabled = False
    op = rem.operator("scatter5.remove_system",text="",icon="REMOVE",)
    op.emitter_name = emitter.name
    op.method = "dynamic_uilist"
    op.undo_push = True

    ope.separator()
    
    #selection menu

    menu = ope.row()
    menu.context_pointer_set("pass_ui_arg_emitter", emitter)
    menu.menu("SCATTER5_MT_selection_menu", icon='DOWNARROW_HLT', text="",)
    
    #biome reader group/ungroup

    ope.separator()        

    #move up & down

    updo = ope.column(align=True)
    updo.enabled = bool(emitter.scatter5.particle_systems)
    if (elinked):
        updo.enabled = False
    op = updo.operator("scatter5.move_interface_items",text="",icon="TRIA_UP",)
    op.direction = "UP"
    op = updo.operator("scatter5.move_interface_items",text="",icon="TRIA_DOWN",)
    op.direction = "DOWN"

    #bring all system(s) to local view, if in local view and in view3d sapce
    
    if (bpy.context.space_data.type=="VIEW_3D") and (bpy.context.space_data.local_view is not None):

        ope.separator()
        op = ope.operator("scatter5.exec_line", text="", icon="ZOOM_SELECTED",)
        op.api = f"[p.scatter_obj.local_view_set(bpy.context.space_data,p.sel) for p in psys]"
        op.description = translate("Isolate the selected system(s) within local view")

    #right spacers
    row.separator(factor=0.1)

    return None


#   .oooooo.                                                         .o.                     .    o8o
#  d8P'  `Y8b                                                       .888.                  .o8    `"'
# 888           oooo d8b  .ooooo.  oooo  oooo  oo.ooooo.           .8"888.      .ooooo.  .o888oo oooo   .ooooo.  ooo. .oo.
# 888           `888""8P d88' `88b `888  `888   888' `88b         .8' `888.    d88' `"Y8   888   `888  d88' `88b `888P"Y88b
# 888     ooooo  888     888   888  888   888   888   888        .88ooo8888.   888         888    888  888   888  888   888
# `88.    .88'   888     888   888  888   888   888   888       .8'     `888.  888   .o8   888 .  888  888   888  888   888
#  `Y8bood8P'   d888b    `Y8bod8P'  `V88V"V8P'  888bod8P'      o88o     o8888o `Y8bod8P'   "888" o888o `Y8bod8P' o888o o888o
#                                               888
#                                              o888o


class SCATTER5_OT_group_psys(bpy.types.Operator):

    bl_idname      = "scatter5.group_psys"
    bl_label       = translate("Group Action")
    bl_options     = {'INTERNAL','UNDO'}

    action : bpy.props.StringProperty(default="GROUP") #GROUP/UNGROUP/NEWGROUP
    name : bpy.props.StringProperty(default="MyGroup")
    emitter_name : bpy.props.StringProperty(default="", options={'SKIP_SAVE',},)
    group_target : bpy.props.StringProperty(default="", options={'SKIP_SAVE',})

    reset_index : bpy.props.BoolProperty(default=False, options={'SKIP_SAVE',})

    @classmethod
    def description(cls, context, properties, ):
        groupinfoblock = translate("Grouping scatter-systems together is a great way to manage your scatter layers, it offers a way to organize your scatters more easily in your interface. You'll be able to easily hide scatter layers by their groups, and tweak their group settings, such as defining a group mask, a group scale or a group pattern. Group settings apply to all scatter-system members of a defined group.")
        match properties.action:
            case 'NEWGROUP':
                return translate("Group the selected Scatter-System(s) in a newly created group")+"\n\n"+groupinfoblock
            case 'GROUP':
                return translate("Group the selected Scatter-System(s) in an existing group of your choice")+"\n\n"+groupinfoblock
            case 'UNGROUP':
                return translate("Remove the selected Scatter-System(s) from their currently assigned group (if exists)")
        return None
            
    def execute(self, context):

        scat_scene = context.scene.scatter5

        #Get Emitter (will find context emitter if nothing passed)
        emitter = bpy.data.objects.get(self.emitter_name)
        if (emitter is None):
            emitter = scat_scene.emitter
        if (emitter is None):
            raise Exception("No Emitter found")

        psys_sel = emitter.scatter5.get_psys_selected()

        #pause for optimization purposes, this might trigger a lot of updates
        with bpy.context.scene.scatter5.factory_update_pause(event=True,delay=True,sync=True):
                
            #if action is new group, need to find a proper name

            if (self.action=="NEWGROUP"):

                groups_used = [ p.group for p in emitter.scatter5.particle_systems if (p.group!="") ]

                idx = 0
                original_name = self.name
                while (self.name in groups_used):
                    idx += 1
                    self.name = f"{original_name}.{idx:03}"

            #add to group (note that psy.group update function will automatically create the group)

            if ((self.action=="GROUP") or (self.action=="NEWGROUP")):

                #if operator usedin the context of an active group
                if (self.group_target!=""):
                    self.name = self.group_target

                if (self.name==""):
                    bpy.ops.scatter5.popup_dialog(
                        'INVOKE_DEFAULT',
                        msg=translate("Please choose another name"),
                        header_title=translate("Invalid Name"),
                        header_icon="LIBRARY_DATA_BROKEN",
                        )
                    return {'FINISHED'}

                for p in psys_sel:
                    if (p.group!=self.name):
                        p.group = self.name

            #or ungroup 

            elif (self.action=="UNGROUP"):

                #if operator usedin the context of an active group
                if (self.group_target!=""):
                    for p in emitter.scatter5.particle_systems:
                        if (p.group==self.group_target):
                            p.group = ""

                else:
                    for p in psys_sel:
                        p.group = ""

            #rebuild system-list interface
            emitter.scatter5.particle_interface_refresh()

            #restore psy sel, rebuilding interface will trigger index change
            for p in emitter.scatter5.particle_systems:
                p.sel = p in psys_sel

        return {'FINISHED'}

# ooo        ooooo                                      ooooo         o8o               .
# `88.       .888'                                      `888'         `"'             .o8
#  888b     d'888   .ooooo.  oooo    ooo  .ooooo.        888         oooo   .oooo.o .o888oo
#  8 Y88. .P  888  d88' `88b  `88.  .8'  d88' `88b       888         `888  d88(  "8   888
#  8  `888'   888  888   888   `88..8'   888ooo888       888          888  `"Y88b.    888
#  8    Y     888  888   888    `888'    888    .o       888       o  888  o.  )88b   888 .
# o8o        o888o `Y8bod8P'     `8'     `Y8bod8P'      o888ooooood8 o888o 8""888P'   "888"


class SCATTER5_OT_move_interface_items(bpy.types.Operator):
    """special move-set behavior for our group system item"""

    bl_idname      = "scatter5.move_interface_items"
    bl_label       = translate("Move the active system in the interface")
    bl_description = translate("Organize your interface by moving your scatter-system or scatter-group up or down the interface lister")
    bl_options     = {'INTERNAL','UNDO'}

    direction : bpy.props.StringProperty(default="UP") #UP/DOWN
    target_idx : bpy.props.IntProperty(default=0)
    emitter_name : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)

    def execute(self, context):

        scat_scene = context.scene.scatter5

        #Get Emitter (will find context emitter if nothing passed)
        emitter = bpy.data.objects.get(self.emitter_name)
        if (emitter is None):
            emitter = scat_scene.emitter
        if (emitter is None):
            raise Exception("No Emitter found")
            return {'FINISHED'}

        psy_active = emitter.scatter5.get_psy_active()
        group_active = emitter.scatter5.get_group_active()

        propgroup     = emitter.scatter5.particle_interface_items
        target_idx    = emitter.scatter5.particle_interface_idx
        len_propgroup = len(propgroup)


        #don't even bother to move anything if we are located at the list extrmities
        if ((self.direction=="DOWN") and (target_idx==len_propgroup-1)) or \
           ((self.direction=="UP") and (target_idx==0)):
          return {'FINISHED'}

        #save selection, this operation might f up sel
        save_sel = emitter.scatter5.get_psys_selected()[:]

        #do we move a psy itm?
        if (psy_active is not None):

            #if we move a psy item in group, simply move them within their group
            if (psy_active.group!=""):

                #find all idx part of same group as psy_active
                possible_idxs = [ i for i,itm in enumerate(propgroup) if 
                                        (itm.interface_item_type=='SCATTER_SYSTEM') 
                                    and (itm.get_interface_item_source() is not None)
                                    and (itm.get_interface_item_source().group==psy_active.group) 
                                ]

                match self.direction:
                    
                    case 'DOWN':
                        #find first available index above target
                        possible_idxs = [i for i in possible_idxs if i>target_idx]
                        if (len(possible_idxs)):
                            new_idx = possible_idxs[0]
                            propgroup.move(target_idx,new_idx)

                    case 'UP':
                        #find last available index below target 
                        possible_idxs = [i for i in possible_idxs if i<target_idx]
                        if (len(possible_idxs)):
                            new_idx = possible_idxs[-1]
                            propgroup.move(target_idx,new_idx)

            #if we move a psy item in group, we need to ignore 
            else:
                
                #find all idx not part of any groups, or group idx
                possible_idxs = [ i for i,itm in enumerate(propgroup) if 
                                   (    (itm.interface_item_type=='SCATTER_SYSTEM') 
                                    and (itm.get_interface_item_source() is not None)
                                    and (itm.get_interface_item_source().group=="") ) \
                                    or  (itm.interface_item_type=='GROUP_SYSTEM')
                                ]

                match self.direction:
                    
                    case 'DOWN':
                        #find first available index above target
                        possible_idxs = [i for i in possible_idxs if i>target_idx]
                        if (len(possible_idxs)):
                            new_idx = possible_idxs[0]
                            propgroup.move(target_idx,new_idx)

                    case 'UP':
                        #find last available index below target 
                        possible_idxs = [i for i in possible_idxs if i<target_idx]
                        if (len(possible_idxs)):
                            new_idx = possible_idxs[-1]
                            propgroup.move(target_idx,new_idx)

            #update interface & make sure active item is still active
            emitter.scatter5.set_interface_active_item(item=psy_active,)

        #or we move a group itm? 
        elif (group_active is not None):
            
            #find all idx not part of any groups, or group idx
            possible_idxs = [ i for i,itm in enumerate(propgroup) if 
                               (    (itm.interface_item_type=='SCATTER_SYSTEM') 
                                and (itm.get_interface_item_source() is not None)
                                and (itm.get_interface_item_source().group=="") ) \
                                or  (itm.interface_item_type=='GROUP_SYSTEM')
                            ]

            match self.direction:
                
                case 'DOWN':
                    #find first available index above target
                    possible_idxs = [i for i in possible_idxs if i>target_idx]
                    if (len(possible_idxs)):
                        new_idx = possible_idxs[0]
                        propgroup.move(target_idx,new_idx)

                case 'UP':
                    #find last available index below target 
                    possible_idxs = [i for i in possible_idxs if i<target_idx]
                    if (len(possible_idxs)):
                        new_idx = possible_idxs[-1]
                        propgroup.move(target_idx,new_idx)

            #update interface & make sure active item is still active
            emitter.scatter5.set_interface_active_item(item=group_active,)

        #restore selection
        [setattr(p,"sel",p in save_sel) for p in emitter.scatter5.particle_systems]

        return {'FINISHED'}


class SCATTER5_OT_generic_list_move(bpy.types.Operator):

    bl_idname      = "scatter5.generic_list_move"
    bl_label       = translate("Move Item")
    bl_description = ""
    bl_options     = {'INTERNAL','UNDO'}

    direction : bpy.props.StringProperty(default="UP") #UP/DOWN
    target_idx : bpy.props.IntProperty(default=0)

    api_propgroup  : bpy.props.StringProperty(default="emitter.scatter5.mask_systems")
    api_propgroup_idx : bpy.props.StringProperty(default="emitter.scatter5.mask_systems_idx")

    def execute(self, context):

        scat_scene = bpy.context.scene.scatter5
        emitter    = scat_scene.emitter

        target_idx    = self.target_idx
        current_idx   = eval(f"{self.api_propgroup_idx}")
        len_propgroup = eval(f"len({self.api_propgroup})")

        if ((self.direction=="UP") and (current_idx!=0)):
            exec(f"{self.api_propgroup}.move({target_idx},{target_idx}-1)")
            exec(f"{self.api_propgroup_idx} -=1")
            return {'FINISHED'}

        if ((self.direction=="DOWN") and (current_idx!=len_propgroup-1)):
            exec(f"{self.api_propgroup}.move({target_idx},{target_idx}+1)")
            exec(f"{self.api_propgroup_idx} +=1")
            return {'FINISHED'}

        return {'FINISHED'}



#   .oooooo.      ooooo         o8o               .
#  d8P'  `Y8b     `888'         `"'             .o8
# 888      888     888         oooo   .oooo.o .o888oo  .ooooo.  oooo d8b
# 888      888     888         `888  d88(  "8   888   d88' `88b `888""8P
# 888      888     888          888  `"Y88b.    888   888ooo888  888
# `88b    d88b     888       o  888  o.  )88b   888 . 888    .o  888
#  `Y8bood8P'Ybd' o888ooooood8 o888o 8""888P'   "888" `Y8bod8P' d888b


class SCATTER5_OT_quick_lister(bpy.types.Operator):
    #modal dialog box -> https://blender.stackexchange.com/questions/274785/how-to-create-a-modal-dialog-box-operator

    bl_idname = "scatter5.quick_lister"
    bl_label = translate("Quick Lister")
    bl_description = translate("Quick Lister")
    bl_options = {'INTERNAL'}

    #find if dialog is currently active?

    dialog_state = False

    def get_dialog_state(self)->bool:
        return SCATTER5_OT_quick_lister.dialog_state
        
    def set_dialog_state(self, value:bool,)->None:
        SCATTER5_OT_quick_lister.dialog_state = value
        return None

    instance_type : bpy.props.StringProperty(default="UNDEFINED", options={'SKIP_SAVE',},)

    def invoke(self,context,event,):
        """decide if we'll invoke modal or dialog"""

        match self.instance_type:
            
            case 'UNDEFINED': #launch both modal & dialog instance of this operator simultaneously
                bpy.ops.scatter5.quick_lister('INVOKE_DEFAULT',instance_type="DIALOG",)
                bpy.ops.scatter5.quick_lister('INVOKE_DEFAULT',instance_type="MODAL",)
                return {'FINISHED'}

            case 'DIALOG': #launch a dialog instance?
                self.set_dialog_state(True)
                return context.window_manager.invoke_popup(self)

            case 'MODAL': #launch a modal instance?
                self.modal_start(context)
                context.window_manager.modal_handler_add(self)  
                return {'RUNNING_MODAL'}

        return {'FINISHED'}

    def __del__(self):
        """called when the operator has finished"""

        #some of our instances might be gone from memory, 
        #therefore 'instance_type' is not available for some instance at this stage
        #not the dialog box instance tho & we need to update class status
        try:
            if (self.instance_type=="DIALOG"):
                self.set_dialog_state(False)
        except: pass
            
        return None

    def modal(self,context,event,):
        """for modal instance"""

        scat_scene = bpy.context.scene.scatter5
        emitter    = scat_scene.emitter
        
        #[a.tag_redraw() for a in context.screen.areas] #Not working :-(
        
        #modal state only active while dialog instance is! 
        if (self.get_dialog_state()==False):
            self.modal_quit(context)
            return {'FINISHED'}

        #no shortcut if no emitter!
        if (emitter is None):
            return {'PASS_THROUGH'}

        if (event.type=="A"): #A/ALT+A
            if (event.value=="RELEASE"):
                if (event.alt):
                    for p in emitter.scatter5.particle_systems:
                        p.sel = False
                    return {'PASS_THROUGH'}
                for p in emitter.scatter5.particle_systems:
                    p.sel = True
            return {'PASS_THROUGH'}

        elif (event.type=="DEL"): #DELETE
            if (event.value=="RELEASE"):
                bpy.ops.scatter5.remove_system(method="selection", emitter_name=emitter.name,) 
            return {'PASS_THROUGH'}

        elif (event.type=="G"): #CTRL+G/ALT+G
            if (event.value=="RELEASE"):

                #group
                if (event.ctrl):
                    group_active = emitter.scatter5.get_group_active()
                    #add to active group?
                    if (group_active is not None):
                        bpy.ops.scatter5.group_psys(emitter_name=emitter.name, action="GROUP",group_target=group_active.name,reset_index=True,)
                        return {'PASS_THROUGH'}
                    #or simply add new?
                    bpy.ops.scatter5.group_psys(emitter_name=emitter.name, action="NEWGROUP",reset_index=True,)
                    return {'PASS_THROUGH'}

                #ungroup
                if (event.alt):
                    save_hide_viewport = [p.hide_viewport for p in emitter.scatter5.particle_systems]
                    bpy.ops.scatter5.group_psys(emitter_name=emitter.name, action="UNGROUP",reset_index=True,)
                    for v,p in zip(save_hide_viewport,emitter.scatter5.particle_systems): 
                        p.hide_viewport = v
                    return {'PASS_THROUGH'}
                
        if (False):
            
            keyset = {"ONE":1,"NUMPAD_1":1,"TWO":2,"NUMPAD_2":2,"THREE":3,"NUMPAD_3":3,"FOUR":4,"NUMPAD_4":4,"FIVE":5,"NUMPAD_5":5,"SIX":6,"NUMPAD_6":6,"SEVEN":7,"NUMPAD_7":7,"EIGHT":8,"NUMPAD_8":8,"NINE":9,"NUMPAD_9":9,"ZERO":10,"NUMPAD_0":10,}
            
            if (event.type in self.keyset.keys()): #USE NUM KEY to switch active interface item
                if (event.value=="RELEASE"):
                    save_selection = [p.sel for p in emitter.scatter5.particle_systems]
                    emitter.scatter5.particle_interface_idx = self.keyset[event.type]
                    for v,p in zip(save_selection,emitter.scatter5.particle_systems): 
                        p.sel = v
                return {'PASS_THROUGH'}
        
            elif (event.ctrl and event.type=="C"): #CTRL+C
                if (event.value=="RELEASE"):
                    bpy.ops.scatter5.copy_paste_systems(emitter_name=emitter.name,copy=True,)
                return {'PASS_THROUGH'}

            elif (event.ctrl and event.type=="V"): #CTRL V
                if (event.value=="RELEASE"):
                    bpy.ops.scatter5.copy_paste_systems(emitter_name=emitter.name,paste=True,)
                return {'PASS_THROUGH'}
        
        return {'PASS_THROUGH'}

    def modal_start(self,context,):
        return None

    def modal_quit(self,context,):
        return None

    def draw(self, context):
        
        scat_scene   = bpy.context.scene.scatter5
        emitter      = scat_scene.emitter
        psy_active   = emitter.scatter5.get_psy_active() if emitter else None
        group_active = emitter.scatter5.get_group_active() if emitter else None

        layout = self.layout
        layout.separator(factor=1.5)
        row = layout.row()
            
        rwoo = row.row()
        rwoo.separator(factor=0.45)
        rwoo.alignment = "LEFT"
        rwoo.scale_x = 1.5
        rwoo.menu("SCATTER5_MT_emitter_dropdown_menu", text=f" {emitter.name}  " if (emitter is not None) else translate("Emitter"), icon="DOWNARROW_HLT",)
        
        rwoo = row.row()
        rwoo.alignment = "RIGHT"
        rwoo.scale_x = 1.2
        rwoo.prop(scat_scene, "emitter", text="")
        rwoo.separator(factor=0.3)

        if (emitter):
            draw_particle_selection_inner(layout=layout, context=context, extra_layout=None, scat_scene=scat_scene, emitter=emitter, psy_active=psy_active, group_active=group_active,)
            
        else: 
            col = layout.column()
            col.active = False
            col.separator()
            row = col.row()
            row.separator(factor=1.2)
            row.label(text=translate("Please Select an Emitter"), icon_value=cust_icon("W_EMITTER"),)
            col.separator()

        layout.separator(factor=1.5)

        return None 


    def execute(self, context,):
        """mandatory function called when user press on 'ok' """

        return {'FINISHED'}



quicklister_keymaps = []

def register_quicklister_shortcuts():
    
    if (bpy.app.background):
        # NOTE: if blender run headlessly, i.e. with -b, --background option, there is no window, so adding keymap will fail with error:
        #     km  = kc.keymaps.new(name="Window", space_type="EMPTY", region_type="WINDOW")
        # AttributeError: 'NoneType' object has no attribute 'keymaps'
        # so, lets skip that completely.. and unregistering step as well
        return None
    
    #add hotkey
    wm  = bpy.context.window_manager
    kc  = wm.keyconfigs.addon
    km  = kc.keymaps.new(name="Window", space_type="EMPTY", region_type="WINDOW")
    kmi = km.keymap_items.new("scatter5.quick_lister", 'Q', 'PRESS', shift=True,ctrl=True,alt=False,)

    quicklister_keymaps.append(kmi)

    return None

def unregister_quicklister_shortcuts():
    
    if (bpy.app.background):
        # see note above
        return None

    #remove hotkey
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    km = kc.keymaps["Window"]
    for kmi in quicklister_keymaps:
        km.keymap_items.remove(kmi)
    quicklister_keymaps.clear()

    return None

#    .oooooo.   oooo
#   d8P'  `Y8b  `888
#  888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
#  888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
#  888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
#  `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#   `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'


classes = (

    SCATTER5_UL_list_scatter_small,
    SCATTER5_UL_list_scatter_large,
    SCATTER5_UL_list_scatter_stats,

    SCATTER5_OT_group_psys,

    SCATTER5_OT_move_interface_items,
    SCATTER5_OT_generic_list_move,

    SCATTER5_OT_quick_lister,
    
    )