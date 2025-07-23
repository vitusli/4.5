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
# oooooooooooo                    o8o      .       .                           ooooooooo.                                   oooo
# `888'     `8                    `"'    .o8     .o8                           `888   `Y88.                                 `888
#  888         ooo. .oo.  .oo.   oooo  .o888oo .o888oo  .ooooo.  oooo d8b       888   .d88'  .oooo.   ooo. .oo.    .ooooo.   888
#  888oooo8    `888P"Y88bP"Y88b  `888    888     888   d88' `88b `888""8P       888ooo88P'  `P  )88b  `888P"Y88b  d88' `88b  888
#  888    "     888   888   888   888    888     888   888ooo888  888           888          .oP"888   888   888  888ooo888  888
#  888       o  888   888   888   888    888 .   888 . 888    .o  888           888         d8(  888   888   888  888    .o  888
# o888ooooood8 o888o o888o o888o o888o   "888"   "888" `Y8bod8P' d888b         o888o        `Y888""8o o888o o888o `Y8bod8P' o888o
#
#####################################################################################################


import bpy

from .. resources.icons import cust_icon
from .. translations import translate

from .. utils.str_utils import word_wrap 

from . import ui_templates


# ooooo   ooooo                           .o8
# `888'   `888'                          "888
#  888     888   .ooooo.   .oooo.    .oooo888   .ooooo.  oooo d8b
#  888ooooo888  d88' `88b `P  )88b  d88' `888  d88' `88b `888""8P
#  888     888  888ooo888  .oP"888  888   888  888ooo888  888
#  888     888  888    .o d8(  888  888   888  888    .o  888
# o888o   o888o `Y8bod8P' `Y888""8o `Y8bod88P" `Y8bod8P' d888b


def emitter_header(self):
    """draw main panels header"""

    from ... __init__ import addon_prefs

    scat_scene  = bpy.context.scene.scatter5
    emitter = scat_scene.emitter
    layout = self.layout
    mode = bpy.context.mode

    
    if (mode in ('PAINT_WEIGHT','PAINT_VERTEX','PAINT_TEXTURE','EDIT_MESH')):
        
        row = layout.row()
        row.alignment = "RIGHT"
        ope = row.row(align=True)
        op = ope.operator("scatter5.exec_line", text=emitter.name, icon="NONE",      emboss=False, depress=False,) ; op.api = "bpy.ops.object.mode_set(mode='OBJECT')" ; op.description = translate("Go back to object mode")
        op = ope.operator("scatter5.exec_line", text="",           icon="LOOP_BACK", emboss=False, depress=False,) ; op.api = "bpy.ops.object.mode_set(mode='OBJECT')" ; op.description = translate("Go back to object mode")
        
        return None 

    match addon_prefs().emitter_method:
        
        case 'pointer':
            
            kwargs = {}
            if (emitter is not None) and emitter.library:
                kwargs["icon"] = "LINKED"
                
            row = layout.row(align=False)
            row.alignment = "RIGHT"
            # row.alert = (scat_scene.emitter not in bpy.context.view_layer.objects[:])
            row.prop(scat_scene, "emitter", text="", **kwargs)
            
        case 'pin':
            
            row = layout.row(align=False)
            row.alignment = "RIGHT"
            icon = "PINNED" if scat_scene.emitter_pinned else "UNPINNED"
            ope = row.row(align=True)
            op = ope.operator("scatter5.property_toggle", text=emitter.name, icon="NONE", emboss=False,) ; op.api = "scat_scene.emitter = None" ; op.description = translate("Return to main")
            op = ope.operator("scatter5.property_toggle", text="",           icon=icon,   emboss=False,) ; op.api = "scat_scene.emitter_pinned" ; op.description = translate("Pin this target")
            
        case 'menu':
            
            row = layout.row(align=False)
            row.alignment = "RIGHT"
            row.scale_x = 1.1
            row.box().box().menu("SCATTER5_MT_emitter_dropdown_menu", text=f" {emitter.name}  ", icon="DOWNARROW_HLT",)
                
    return None


class SCATTER5_MT_emitter_dropdown_menu(bpy.types.Menu):

    bl_idname = "SCATTER5_MT_emitter_dropdown_menu"
    bl_label  = ""
    bl_description = ""

    def draw(self, context):
        layout=self.layout

        active_emitter = bpy.context.scene.scatter5.emitter
        emitters = bpy.context.scene.scatter5.get_all_emitters(search_mode="active_view_layer", also_linked=True)

        for e in emitters:
            
            kwargs = {}
            if bool(e.library):
                  kwargs["icon"] = "LINKED"
            else: kwargs["icon_value"] = cust_icon("W_EMITTER" if (e is active_emitter) else "W_EMITTER_EMPTY")
                
            row = layout.row()
            row.enabled = (e is not active_emitter)
            op = row.operator("scatter5.set_new_emitter",text=f"Use '{e.name}'", **kwargs)
            op.obj_session_uid = e.session_uid
            
            continue

        layout.separator()

        o = bpy.context.object
        if (o is not None):
            row = layout.row()
            row.active = o is not active_emitter
            op = row.operator("scatter5.set_new_emitter", text=f"Use '{o.name}'", icon="RESTRICT_SELECT_OFF",)
            op.obj_session_uid = o.session_uid
        
        layout.operator("scatter5.new_dummy_emitter", text=translate("New Empty Emitter"), icon="PLUS",)
        layout.operator("scatter5.exec_line", text=translate("Back to Emitter Panel"), icon="LOOP_BACK",).api = "scat_scene.emitter = None"
        
        return None


# ooo        ooooo            o8o                   ooooooooo.                                   oooo
# `88.       .888'            `"'                   `888   `Y88.                                 `888
#  888b     d'888   .oooo.   oooo  ooo. .oo.         888   .d88'  .oooo.   ooo. .oo.    .ooooo.   888
#  8 Y88. .P  888  `P  )88b  `888  `888P"Y88b        888ooo88P'  `P  )88b  `888P"Y88b  d88' `88b  888
#  8  `888'   888   .oP"888   888   888   888        888          .oP"888   888   888  888ooo888  888
#  8    Y     888  d8(  888   888   888   888        888         d8(  888   888   888  888    .o  888
# o8o        o888o `Y888""8o o888o o888o o888o      o888o        `Y888""8o o888o o888o `Y8bod8P' o888o


def draw_emit_panel(self, layout, context,):

    scat_scene   = bpy.context.scene.scatter5
    emitters     = scat_scene.get_all_emitters(search_mode="active_view_layer", also_linked=True)
    has_emitters = bool(len(emitters)!=0)
        
    main = layout.column()

    ui_templates.separator_box_out(main)
    ui_templates.separator_box_out(main)

    if (not has_emitters):
        draw_info(self, main, context,)
        ui_templates.separator_box_out(main)

    if (has_emitters):
        draw_swap(self,main)
        ui_templates.separator_box_out(main)
        
    draw_nonlinear_new(self,main)
    ui_templates.separator_box_out(main)

    if (bpy.context.object is not None):
        draw_remesh(self,main)
        ui_templates.separator_box_out(main)
    
    main.separator(factor=50)
    
    return None 


# ooooo              .o88o.
# `888'              888 `"
#  888  ooo. .oo.   o888oo   .ooooo.
#  888  `888P"Y88b   888    d88' `88b
#  888   888   888   888    888   888
#  888   888   888   888    888   888
# o888o o888o o888o o888o   `Y8bod8P'


def draw_info(self, layout, context,):

    box, is_open = ui_templates.box_panel(layout, 
        panelopen_propname="ui_emit_info", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_emit_info");BOOL_VALUE(1)
        panel_icon="HELP", 
        panel_name=translate("Information"),
        )
    if is_open:
            
            col = box.column()
            word_wrap(layout=col, max_char='auto', context=context, char_auto_sidepadding=0.85, alignment="CENTER", active=True, icon="INFO", 
                string=translate("Choose an emitter-object in the header above to start scattering!\n\nEmitters are where your scatter-system(s) settings will be stored, and by default, they will be the surface you'll scatter upon.\n\nYou can swap to other emitters at any moment from the header above."),)
            ui_templates.separator_box_in(box)

    return None 

# ooooo      ooo                       oooo   o8o                                                ooooo      ooo
# `888b.     `8'                       `888   `"'                                                `888b.     `8'
#  8 `88b.    8   .ooooo.  ooo. .oo.    888  oooo  ooo. .oo.    .ooooo.   .oooo.   oooo d8b       8 `88b.    8   .ooooo.  oooo oooo    ooo
#  8   `88b.  8  d88' `88b `888P"Y88b   888  `888  `888P"Y88b  d88' `88b `P  )88b  `888""8P       8   `88b.  8  d88' `88b  `88. `88.  .8'
#  8     `88b.8  888   888  888   888   888   888   888   888  888ooo888  .oP"888   888           8     `88b.8  888ooo888   `88..]88..8'
#  8       `888  888   888  888   888   888   888   888   888  888    .o d8(  888   888           8       `888  888    .o    `888'`888'
# o8o        `8  `Y8bod8P' o888o o888o o888o o888o o888o o888o `Y8bod8P' `Y888""8o d888b         o8o        `8  `Y8bod8P'     `8'  `8'

 
#"scatter5.new_dummy_emitter"

def draw_nonlinear_new(self,layout):

    box, is_open = ui_templates.box_panel(layout, 
        panelopen_propname="ui_emit_nonlinear_new", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_emit_nonlinear_new");BOOL_VALUE(0)
        panel_icon="RNA_ADD", 
        panel_name=translate("Dummy Emitter"),
        )
    if is_open:

            row = box.row()
            row.separator(factor=0.3)
            col = row.column()
            row.separator(factor=0.3)

            #button add new 

            button = col.row(align=True)
            button.scale_y=1.2
            button.operator("scatter5.new_dummy_emitter",text=translate("Create Dummy Emitter"), icon="PLUS",)

            ui_templates.separator_box_in(box)

    return None 

#  .oooooo..o
# d8P'    `Y8
# Y88bo.      oooo oooo    ooo  .oooo.   oo.ooooo.
#  `"Y8888o.   `88. `88.  .8'  `P  )88b   888' `88b
#      `"Y88b   `88..]88..8'    .oP"888   888   888
# oo     .d8P    `888'`888'    d8(  888   888   888
# 8""88888P'      `8'  `8'     `Y888""8o  888bod8P'
#                                         888
#                                        o888o
 
def draw_swap(self,layout):

    box, is_open = ui_templates.box_panel(layout, 
        panelopen_propname="ui_emit_swap", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_emit_swap");BOOL_VALUE(1)
        panel_icon="W_EMITTER", 
        panel_name=translate("Emitters In Scene"),
        )
    if is_open:
            
            row = box.row()
            row.separator(factor=0.3)
            element_box = row.box().column()
            row.separator(factor=0.3)
            
            fixlay = element_box.row(align=True)
            fixlay.scale_y = 0.01
            fixlay.operator("scatter5.dummy",text="",)
            
            #emitter select box 

            for e in bpy.context.scene.scatter5.get_all_emitters(search_mode="active_view_layer", also_linked=True):
            
                element = element_box.row(align=True)
                element.scale_y = 1
                
                #emitter set operator
                sub = element.row(align=True)
                sub.alignment = "LEFT"
                op = sub.operator("scatter5.set_new_emitter",text=e.name, emboss=False, icon_value= cust_icon("W_EMITTER"),)
                op.obj_session_uid = e.session_uid
                op.select = True
                
                #thanks blender aligmnet system
                sub = element.row(align=True)
                sub.alignment = "RIGHT"
                sub.operator("scatter5.dummy", text="", icon="LINKED" if (e.library) else "BLANK1", emboss=False,)
                    
                continue

            ui_templates.separator_box_in(box)

    return None 

# ooooooooo.                                                  oooo
# `888   `Y88.                                                `888
#  888   .d88'  .ooooo.  ooo. .oo.  .oo.    .ooooo.   .oooo.o  888 .oo.
#  888ooo88P'  d88' `88b `888P"Y88bP"Y88b  d88' `88b d88(  "8  888P"Y88b
#  888`88b.    888ooo888  888   888   888  888ooo888 `"Y88b.   888   888
#  888  `88b.  888    .o  888   888   888  888    .o o.  )88b  888   888
# o888o  o888o `Y8bod8P' o888o o888o o888o `Y8bod8P' 8""888P' o888o o888o


def draw_remesh(self,layout):

    box, is_open = ui_templates.box_panel(layout, 
        panelopen_propname="ui_emit_remesh", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_emit_remesh");BOOL_VALUE(0)
        panel_icon="MOD_REMESH", 
        panel_name=translate("Utility Remesh"),
        )
    if is_open:

            row = box.row()
            row.separator(factor=0.3)
            col = row.column()
            row.separator(factor=0.3)
       
            button = col.row(align=True)
            button.scale_y=1.2
            button.enabled = bpy.context.object.type=="MESH"
            op = button.operator("scatter5.grid_bisect", text=translate("Grid Bisect Selection"), icon="MOD_REMESH",)
            op.obj_list = "_!#!_".join([o.name for o in bpy.context.selected_objects if (o.type=="MESH")])

            ui_templates.separator_box_in(box)

    return None 


#    .oooooo.   oooo
#   d8P'  `Y8b  `888
#  888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
#  888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
#  888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
#  `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#   `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'


class SCATTER5_PT_choose_emitter(bpy.types.Panel):

    bl_idname      = "SCATTER5_PT_choose_emitter"
    bl_label       = translate("Emitter")
    bl_category    = "USER_DEFINED" #will be replaced right before ui.__ini__.register()
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_context     = ""
    bl_order       = 1

    @classmethod
    def poll(cls, context,):
        if (context.scene.scatter5.emitter is not None):
            return False
        if (context.mode not in ('OBJECT','PAINT_WEIGHT','PAINT_VERTEX','PAINT_TEXTURE','EDIT_MESH','EDIT_CURVE',)):
            return False
        return True 

    def draw_header(self, context):

        self.layout.label(text="", icon_value=cust_icon("W_SCATTER"),)

    def draw_header_preset(self, context):

        layout = self.layout
        row = layout.row()
        row.scale_x = 0.85
        row.prop(bpy.context.scene.scatter5,"emitter",text="",icon_value=cust_icon("W_EMITTER"),)

    def draw(self, context):

        layout = self.layout
        draw_emit_panel(self, layout, context,)


classes = (

    SCATTER5_PT_choose_emitter,
    SCATTER5_MT_emitter_dropdown_menu,
    
    )

#if __name__ == "__main__":
#    register()

