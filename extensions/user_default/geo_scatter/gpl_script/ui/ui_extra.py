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
# ooooo     ooo ooooo      oooooooooooo                 .
# `888'     `8' `888'      `888'     `8               .o8
#  888       8   888        888         oooo    ooo .o888oo oooo d8b  .oooo.
#  888       8   888        888oooo8     `88b..8P'    888   `888""8P `P  )88b
#  888       8   888        888    "       Y888'      888    888      .oP"888
#  `88.    .8'   888        888       o  .o8"'88b     888 .  888     d8(  888
#    `YbodP'    o888o      o888ooooood8 o88'   888o   "888" d888b    `Y888""8o
#
#####################################################################################################


import bpy

from .. resources.icons import cust_icon
from .. translations import translate

from . import ui_templates
from . ui_emitter_select import emitter_header

from .. utils.str_utils import word_wrap
from .. utils.vg_utils import is_vg_active

from .. utils.extra_utils import is_rendered_view


# ooo        ooooo            o8o                   ooooooooo.                                   oooo
# `88.       .888'            `"'                   `888   `Y88.                                 `888
#  888b     d'888   .oooo.   oooo  ooo. .oo.         888   .d88'  .oooo.   ooo. .oo.    .ooooo.   888
#  8 Y88. .P  888  `P  )88b  `888  `888P"Y88b        888ooo88P'  `P  )88b  `888P"Y88b  d88' `88b  888
#  8  `888'   888   .oP"888   888   888   888        888          .oP"888   888   888  888ooo888  888
#  8    Y     888  d8(  888   888   888   888        888         d8(  888   888   888  888    .o  888
# o8o        o888o `Y888""8o o888o o888o o888o      o888o        `Y888""8o o888o o888o `Y8bod8P' o888o


def draw_extra_panel(self, layout, context):
        
    main = layout.column()

    ui_templates.separator_box_out(main)
    ui_templates.separator_box_out(main)

    draw_masterseed(self, main)
    ui_templates.separator_box_out(main)

    draw_export(self, main)
    ui_templates.separator_box_out(main)

    draw_sync(self, main)
    ui_templates.separator_box_out(main)

    draw_animation_data(self, main, context,)
    ui_templates.separator_box_out(main)
    
    draw_update(self, main)
    ui_templates.separator_box_out(main)

    draw_parametric_masks(self, main)
    ui_templates.separator_box_out(main)
    
    draw_terrain_displace(self, main)
    ui_templates.separator_box_out(main)

    draw_social(self, main)
    ui_templates.separator_box_out(main)
            
    main.separator(factor=50)
    
    return None 



# ooo        ooooo                        .                            .oooooo..o                           .o8
# `88.       .888'                      .o8                           d8P'    `Y8                          "888
#  888b     d'888   .oooo.    .oooo.o .o888oo  .ooooo.  oooo d8b      Y88bo.       .ooooo.   .ooooo.   .oooo888
#  8 Y88. .P  888  `P  )88b  d88(  "8   888   d88' `88b `888""8P       `"Y8888o.  d88' `88b d88' `88b d88' `888
#  8  `888'   888   .oP"888  `"Y88b.    888   888ooo888  888               `"Y88b 888ooo888 888ooo888 888   888
#  8    Y     888  d8(  888  o.  )88b   888 . 888    .o  888          oo     .d8P 888    .o 888    .o 888   888
# o8o        o888o `Y888""8o 8""888P'   "888" `Y8bod8P' d888b         8""88888P'  `Y8bod8P' `Y8bod8P' `Y8bod88P"


def draw_masterseed(self,layout):

    box, is_open = ui_templates.box_panel(layout, 
        panelopen_propname="ui_extra_masterseed", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_extra_masterseed");BOOL_VALUE(0)
        panel_icon="W_DICE", 
        panel_name=translate("Master Seed"), 
        popover_info="SCATTER5_PT_docs",
        popover_uilayout_context_set="ui_extra_masterseed",
        )
    if is_open:
        
        from ... __init__ import blend_prefs
        scat_data  = blend_prefs()

        row = box.row()
        row.separator(factor=0.5)
        col = row.column(align=True)

        sed = col.row(align=True)
        sed.prop(scat_data,"s_master_seed")
        sedbutton = sed.row(align=True)
        sedbutton.scale_x = 1.2
        op = sedbutton.operator("scatter5.exec_line", icon_value=cust_icon("W_DICE"), text="",)
        op.api = f"scat_data.s_master_seed = random.randint(0,9999)"
        op.description = translate("Randomize Seed Value")
        op.undo = translate("Randomizing Master Seed Value")

        col.separator(factor=0.2)
        
        tocol, is_toggled = ui_templates.bool_toggle(box, scat_data, "s_master_seed_animate", 
            label=translate("Animate Master Seed"),
            icon="RENDER_ANIMATION", 
            arrowopen_propname="ui_openclose_master_seed_animate", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_openclose_master_seed_animate");BOOL_VALUE(0)
            return_sublayout=True,
            use_layout_left_spacer=False,
            )
        if is_toggled:
            tocol.separator(factor=0.2)
            tocol.prop(scat_data, "s_master_seed_animated",)
            tocol.separator(factor=0.5)

        #Right Spacer
        row.separator(factor=0.1)

        ui_templates.separator_box_in(box)
        
    return None


# oooooooooooo                                               .
# `888'     `8                                             .o8
#  888         oooo    ooo oo.ooooo.   .ooooo.  oooo d8b .o888oo
#  888oooo8     `88b..8P'   888' `88b d88' `88b `888""8P   888
#  888    "       Y888'     888   888 888   888  888       888
#  888       o  .o8"'88b    888   888 888   888  888       888 .
# o888ooooood8 o88'   888o  888bod8P' `Y8bod8P' d888b      "888"
#                           888
#                          o888o


def draw_export(self,layout):

    box, is_open = ui_templates.box_panel(layout, 
        panelopen_propname="ui_extra_export", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_extra_export");BOOL_VALUE(0)
        panel_icon="W_EXPORT_FILE", 
        panel_name=translate("Export"),
        popover_info="SCATTER5_PT_docs", 
        popover_uilayout_context_set="ui_extra_export",
        )
    if is_open:

            emitter = bpy.context.scene.scatter5.emitter
            psys_sel = emitter.scatter5.get_psys_selected()

            row  = box.row()
            row1 = row.row() ; row1.scale_x = 0.17
            row2 = row.row()
            row3 = row.row() ; row3.scale_x = 0.17
            col = row2.column()

            exp = col.row()
            exp.scale_y = 1.2
            exp.operator("scatter5.export_to_objects", text=translate("Selected to Instances"), ).obj_session_uid = emitter.session_uid

            col.separator()
            
            exp = col.row()
            exp.scale_y = 1.2 
            exp.operator("scatter5.export_to_json", text=translate("Selected to .Json"), )

            col.separator()
                        
            exp = col.row()
            exp.scale_y = 1.2 
            exp.operator("scatter5.export_to_presets", text=translate("Selected to Preset(s)"), )

            col.separator()
            
            exp = col.row()
            exp.scale_y = 1.2 
            exp.operator("scatter5.export_to_biome", text=translate("Selected to Biome"), )

            col.separator()

            ui_templates.separator_box_in(col)
    
    return None


#  .oooooo..o                                   oooo                                        o8o
# d8P'    `Y8                                   `888                                        `"'
# Y88bo.      oooo    ooo ooo. .oo.    .ooooo.   888 .oo.   oooo d8b  .ooooo.  ooo. .oo.   oooo    oooooooo  .ooooo.
#  `"Y8888o.   `88.  .8'  `888P"Y88b  d88' `"Y8  888P"Y88b  `888""8P d88' `88b `888P"Y88b  `888   d'""7d8P  d88' `88b
#      `"Y88b   `88..8'    888   888  888        888   888   888     888   888  888   888   888     .d8P'   888ooo888
# oo     .d8P    `888'     888   888  888   .o8  888   888   888     888   888  888   888   888   .d8P'  .P 888    .o
# 8""88888P'      .8'     o888o o888o `Y8bod8P' o888o o888o d888b    `Y8bod8P' o888o o888o o888o d8888888P  `Y8bod8P'
#             .o..P'
#             `Y8P'


def draw_sync(self,layout):

    box, is_open = ui_templates.box_panel(layout, 
        panelopen_propname="ui_extra_synch", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_extra_synch");BOOL_VALUE(0)
        panel_icon="W_ARROW_SYNC", 
        panel_name=translate("Synchronize Scatter"), 
        popover_info="SCATTER5_PT_docs",
        popover_uilayout_context_set="ui_extra_synch",
        )
    if is_open:

        from ... __init__ import blend_prefs
        scat_win   = bpy.context.window_manager.scatter5
        scat_data  = blend_prefs()
        scat_scene = bpy.context.scene.scatter5
                
        tocol, is_toggled = ui_templates.bool_toggle(box, scat_data, "factory_synchronization_allow", 
            label=translate("Synchronize Settings"),
            icon="W_ARROW_SYNC", 
            arrowopen_propname="ui_openclose_synch", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_openclose_synch");BOOL_VALUE(0)
            return_sublayout=True,
            use_sublayout_indentation=False,
            )
        if is_toggled:

            row = tocol.row()
            row.active = scat_data.factory_synchronization_allow

            row.separator(factor=0.5)

            row.template_list("SCATTER5_UL_sync_channels", "", scat_data, "sync_channels", scat_data, "sync_channels_idx", rows=3)

            col = row.column(align=True)

            add = col.row(align=True)
            add.operator("scatter5.sync_channels_ops", icon="ADD", text="").add = True

            rem = col.row(align=True)
            rem.enabled = bool(len(scat_data.sync_channels)) and (scat_data.sync_channels_idx<len(scat_data.sync_channels))
            rem.operator("scatter5.sync_channels_ops", icon="REMOVE", text="").remove = True

            #Right Spacer
            row.separator(factor=0.1)

        ui_templates.separator_box_in(box)
        
    return None


#       .o.                    o8o                                  .    o8o                             oooooooooo.                 .             
#      .888.                   `"'                                .o8    `"'                             `888'   `Y8b              .o8             
#     .8"888.     ooo. .oo.   oooo  ooo. .oo.  .oo.    .oooo.   .o888oo oooo   .ooooo.  ooo. .oo.         888      888  .oooo.   .o888oo  .oooo.   
#    .8' `888.    `888P"Y88b  `888  `888P"Y88bP"Y88b  `P  )88b    888   `888  d88' `88b `888P"Y88b        888      888 `P  )88b    888   `P  )88b  
#   .88ooo8888.    888   888   888   888   888   888   .oP"888    888    888  888   888  888   888        888      888  .oP"888    888    .oP"888  
#  .8'     `888.   888   888   888   888   888   888  d8(  888    888 .  888  888   888  888   888        888     d88' d8(  888    888 . d8(  888  
# o88o     o8888o o888o o888o o888o o888o o888o o888o `Y888""8o   "888" o888o `Y8bod8P' o888o o888o      o888bood8P'   `Y888""8o   "888" `Y888""8o 
                                                                                                                                                                                                                                                                                                
                                                                                                                                                 
def draw_animation_data(self, layout, context,):

    box, is_open = ui_templates.box_panel(layout, 
        panelopen_propname="ui_extra_animation_data", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_extra_animation_data");BOOL_VALUE(0)
        panel_icon="GRAPH",
        panel_name=translate("Animation Data"),
        popover_info="SCATTER5_PT_docs",
        popover_uilayout_context_set="ui_extra_animation_data",
        )
    if is_open:

            row  = box.row()
            row1 = row.row() ; row1.scale_x = 0.17
            row2 = row.row()
            row3 = row.row() ; row3.scale_x = 0.17
            col = row2.column()
            
            scat_scene = bpy.context.scene.scatter5
            emitter    = scat_scene.emitter
            elinked    = bool(emitter.library)
            
            drivers,keyframes = [],[]
            
            #similar code in get_plugin_animated_props()
            
            #gather supported animated plugin properties
            keyable_list = []
            keyable_list += (scat_scene.get_all_emitters(search_mode="all"))
            keyable_list += ([ng for ng in bpy.data.node_groups if ng.name.startswith(".TEXTURE")])
    
            #loop all keyable
            for keyable in [k for k in keyable_list if k and k.animation_data]:
                
                #drivers
                if (keyable.animation_data.drivers):
                    for fc in keyable.animation_data.drivers:
                        if (fc.data_path.startswith("scatter5")):
                            drivers.append((keyable,fc))
                #keyframes
                if (keyable.animation_data.action):
                    for fc in keyable.animation_data.action.fcurves:
                        if (fc.data_path.startswith("scatter5")):
                            keyframes.append((keyable,fc))
                            
                            
            if ((not drivers) and (not keyframes)):
                word_wrap(layout=box, max_char='auto', context=context, char_auto_sidepadding=0.85, alignment="CENTER", active=True, icon="INFO", 
                    string=translate("No Geo-Scatter Animated Properties Found.\nYou can add Keyframes or Drivers to a Scatter property."),)
            
            else:
                
                def draw_fc_itm(layout,keyable,fc,fc_type):
                    
                    def draw_itm(layout,keyable,fc,fc_type, keyable_type,icon):
                        
                        col = layout.column(align=True)
                        
                        row = col.row(align=True).box()
                        row.scale_y = 0.45
                        row.label(text=keyable.name, icon=icon,)
                        
                        row = col.row(align=True)
                        prp = row.row(align=True)
                        if (not fc.is_valid):
                            prp.alert = True
                        else:
                            prp.active = False
                        prp.prop(fc,"data_path",text="",icon="RNA")
                        
                        # remove animation data?
                        # op = row.operator("scatter5.exec_line", text="", icon="TRASH",)
                        # op.api = f"{objapi}.{}"
                        
                        layout.separator(factor=0.7)
                        
                        return None
                    
                    if (type(keyable) is bpy.types.Object):
                        
                        if ("scatter5.particle_systems" in fc.data_path):
                            draw_itm(layout,keyable,fc,fc_type,"Scatter-System","PARTICLES")
                        elif ("scatter5.particle_groups" in fc.data_path):
                            draw_itm(layout,keyable,fc,fc_type,"Scatter-Group","OUTLINER_COLLECTION")
                        else:
                            draw_itm(layout,keyable,fc,fc_type,"Object","OUTLINER_OB_MESH")
                    
                    elif (type(keyable) is bpy.types.GeometryNodeTree):
                        draw_itm(layout,keyable,fc,fc_type,"Scatter-Texture","NODE_TEXTURE")
                    
                    return None
                
                if (keyframes):
                    itmcol = col.column(align=True)
                    itmcol.label(text=translate("Keyframes Found:"),)
                    for keyable,fc in keyframes:
                        draw_fc_itm(itmcol,keyable,fc,"Keyframe",)
                    
                if (drivers):
                    itmcol = col.column(align=True)
                    itmcol.label(text=translate("Drivers Found:"),)
                    for keyable,fc in drivers:
                        draw_fc_itm(itmcol,keyable,fc,"Driver",)
            
            ui_templates.separator_box_in(box)
    
    return None


# ooooooooo.                                                .o8                                 oooo       oooooo     oooo
# `888   `Y88.                                             "888                                 `888        `888.     .8'
#  888   .d88' oooo d8b  .ooooo.   .ooooo.   .ooooo.   .oooo888  oooo  oooo  oooo d8b  .oooo.    888         `888.   .8'    .oooooooo
#  888ooo88P'  `888""8P d88' `88b d88' `"Y8 d88' `88b d88' `888  `888  `888  `888""8P `P  )88b   888          `888. .8'    888' `88b
#  888          888     888   888 888       888ooo888 888   888   888   888   888      .oP"888   888           `888.8'     888   888
#  888          888     888   888 888   .o8 888    .o 888   888   888   888   888     d8(  888   888            `888'      `88bod8P'
# o888o        d888b    `Y8bod8P' `Y8bod8P' `Y8bod8P' `Y8bod88P"  `V88V"V8P' d888b    `Y888""8o o888o            `8'       `8oooooo.
#                                                                                                                          d"     YD
#                                                                                                                          "Y88888P'


def draw_parametric_masks(self,layout):

    MainCol = layout.column(align=True)
    box, is_open = ui_templates.box_panel(MainCol.column(align=True), 
        panelopen_propname="ui_extra_vgs", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_extra_vgs");BOOL_VALUE(0)
        panel_icon="GROUP_VERTEX", 
        panel_name=translate("Vertex-Data"),
        popover_gearwheel="SCATTER5_PT_mask_header",
        popover_info="SCATTER5_PT_docs",
        popover_uilayout_context_set="ui_extra_vgs",
        )
    if is_open:

            scat_scene  = bpy.context.scene.scatter5
            emitter     = scat_scene.emitter
            elinked     = bool(emitter.library) or bool(emitter.data.library)
            masks       = emitter.scatter5.mask_systems
            active_mask = None 
            mask_idx    = emitter.scatter5.mask_systems_idx

            if (len(masks)!=0):
                active_mask = masks[mask_idx]

            #Warnings to user 

            verts=len(emitter.data.vertices)
            
            if (elinked):
                word_wrap(layout=box, string=translate("This emitter is linked!\nVertex-data are read-only"), icon="LINKED", max_char=50,)
                box.separator(factor=0.1)
                
            elif (verts>175_000):
                word_wrap(layout=box, string=translate("This emitter mesh is too high poly!\nYou may experience slowdowns"), icon="ERROR", max_char=50,)
                box.separator(factor=0.1)

            elif (verts<999):
                word_wrap(layout=box, string=translate("This emitter mesh is too low poly!\nVertex-group masks need some vertices!"), icon="ERROR", max_char=60,)
                box.separator(factor=0.1)

            row = box.row()
            if (elinked):
                row.enabled = False

            #Left Spacers
            row.separator(factor=0.5)

            #List Template
            
            ULcol = row.column()
            ULcol.template_list("SCATTER5_UL_tweaking_masks", "", emitter.scatter5, "mask_systems", emitter.scatter5, "mask_systems_idx", rows=10,)
                
            #Operators side menu

            ope = row.column(align=True)

            #Add New mask 

            op = ope.operator("scatter5.add_mask", text="", icon="ADD")
            op.draw = True

            #remove mask 

            op = ope.operator("scatter5.remove_mask",text="",icon="REMOVE")
            op.mask_type = active_mask.type if (active_mask is not None) else ""
            op.mask_idx = mask_idx

            #move up down

            ope.separator()
            updo = ope.column(align=True)
            updo.enabled = len(masks)!=0
            op = updo.operator("scatter5.generic_list_move",text="",icon="TRIA_UP")
            op.target_idx = mask_idx       
            op.direction = "UP"    
            op.api_propgroup = "emitter.scatter5.mask_systems"
            op.api_propgroup_idx = "emitter.scatter5.mask_systems_idx"
            op = updo.operator("scatter5.generic_list_move",text="",icon="TRIA_DOWN")
            op.target_idx = mask_idx       
            op.direction = "DOWN"   
            op.api_propgroup = "emitter.scatter5.mask_systems"
            op.api_propgroup_idx = "emitter.scatter5.mask_systems_idx"

            #assign mask

            ope.separator()
            op = ope.operator("scatter5.assign_mask",text="",icon="FILE_PARENT")
            op.mask_idx = mask_idx

            #Right Spacer
            row.separator(factor=0.1)

            #Stop drawing if no active mask
            if (active_mask is None):
            
                ui_templates.separator_box_in(box)
                return None               

            #box.separator(factor=0.3)

            #Draw settings under tittle info
            
            undertittle = box.column(align=True)

            subrow = undertittle.row()
            subrow.active = False

            #vg pointer
            ptr = None 

            #Draw Vg Pointer, note that some masks don't respect the classic vg per mask format, such as modifier based masks 

            if (active_mask.type in ('vcol_to_vgroup','vgroup_split','vgroup_merge')):

                modname = f"Scatter5 {active_mask.name}"

                ptr = ULcol.column(align=True)
                ptr.scale_y = 0.85
                ptr.enabled = False
                ptr.alert = (modname not in emitter.modifiers)
                ptr.prop(active_mask, "name", icon="MODIFIER_OFF", text="",)

                #Stop drawing if no mod

                if (modname not in emitter.modifiers):

                    box = MainCol.box().column(align=True)   

                    warn = box.row(align=True)
                    warn.alignment = "CENTER"
                    warn.active = False
                    warn.scale_y = 0.9
                    warn.label(text=translate("Modifier Missing, Please Refresh"),icon="ERROR")
                    box.separator()

                    return None

            else:

                ptr = ULcol.column(align=True)
                ptr.scale_y = 0.85
                ptr.enabled = False
                ptr.prop_search(active_mask, "name", emitter, "vertex_groups", text="",)

                #Stop drawing if no vg pointers

                if (active_mask.name not in emitter.vertex_groups):

                    box = MainCol.box().column(align=True)   

                    warn = box.row(align=True)
                    warn.alignment = "CENTER"
                    warn.active = False
                    warn.scale_y = 0.9
                    warn.label(text=translate("Vertex Group Missing, Please Refresh"),icon="ERROR")
                    box.separator()

                    return None

            box = MainCol.box().column(align=True)            

            #drawing code of each masks stored within it's own type module. 
            from .. procedural_vg import mask_type 
            exec(f"mask_type.{active_mask.type}.draw_settings(box, mask_idx,)")

            box.separator(factor=1.2)
            return  None

    return None


class SCATTER5_UL_tweaking_masks(bpy.types.UIList):
    """mask lists to set active"""

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if (not item):
            return None

        emitter = bpy.context.scene.scatter5.emitter
        if (emitter.library):
            layout.enabled = False
        
        #user_name
        if (item.icon.startswith("W_")):
              layout.prop(item, "user_name", text="", emboss=False, icon_value=cust_icon(item.icon),)
        else: layout.prop(item, "user_name", text="", emboss=False, icon=item.icon,)

        #mask refresh operation
        ope = layout.row()
        op = ope.operator("scatter5.refresh_mask", text="", icon="FILE_REFRESH", emboss=False,)
        op.mask_type = item.type
        op.mask_idx = [i for i,m in enumerate(emitter.scatter5.mask_systems) if m==item][0]

        #direct paint operator
        w = layout.row()
        
        if (item.type in ("vcol_to_vgroup","vgroup_split","vgroup_merge")):

            #these masks do not work like all other masks
            mod = emitter.modifiers.get(f"Scatter5 {item.name}")
            if ((item.type=="vgroup_merge") and (mod is not None) and (mod["Output_5_attribute_name"]!="")):
                
                vg_name = mod["Output_5_attribute_name"]
                vg_active = is_vg_active(emitter, vg_name)
                w.active = (vg_active) and (bpy.context.mode == "PAINT_WEIGHT")
                op = w.operator("scatter5.vg_quick_paint", text="", icon="BRUSH_DATA", emboss=vg_active, depress=vg_active,)
                op.group_name = vg_name
                op.mode = "vg"
                op.context_surfaces = "*EMITTER_CONTEXT*"
            
            else:
                w.operator("scatter5.dummy", text="", icon="BLANK1", emboss=False, depress=False,)

        else:

            #set mask active 
            vg_active = is_vg_active(emitter, item.name)
            w.active = (vg_active) and (bpy.context.mode == "PAINT_WEIGHT")
            op = w.operator("scatter5.vg_quick_paint", text="", icon="BRUSH_DATA", emboss=vg_active, depress=vg_active,)
            op.group_name = item.name
            op.mode = "vg"
            op.context_surfaces = "*EMITTER_CONTEXT*"

        return None


# ooooo     ooo                  .o8                .
# `888'     `8'                 "888              .o8
#  888       8  oo.ooooo.   .oooo888   .oooo.   .o888oo  .ooooo.
#  888       8   888' `88b d88' `888  `P  )88b    888   d88' `88b
#  888       8   888   888 888   888   .oP"888    888   888ooo888
#  `88.    .8'   888   888 888   888  d8(  888    888 . 888    .o
#    `YbodP'     888bod8P' `Y8bod88P" `Y888""8o   "888" `Y8bod8P'
#                888
#               o888o


def draw_update(self,layout):

    box, is_open = ui_templates.box_panel(layout, 
        panelopen_propname="ui_extra_update", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_extra_update");BOOL_VALUE(0)
        panel_icon="FILE_REFRESH", 
        panel_name=translate("Update Behavior"),
        popover_info="SCATTER5_PT_docs",
        popover_uilayout_context_set="ui_extra_update",
        )
    if is_open:

            from ... __init__ import blend_prefs
            
            scat_data = blend_prefs()
            scat_win  = bpy.context.window_manager.scatter5

            #Alt batch Update 

            tocol, is_toggled = ui_templates.bool_toggle(box, scat_data, "factory_alt_allow", 
                label=translate("Alt Key for Batch"),
                icon="OUTLINER_DATA_FONT",
                arrowopen_propname="ui_openclose_upd_alt", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_openclose_upd_alt");BOOL_VALUE(0)
                return_sublayout=True,
                )
            if is_toggled:

                tocol.prop( scat_data, "factory_alt_selection_method",text="")

                tocol.separator(factor=0.5)

            #Property Update Method 

            tocol, is_toggled = ui_templates.bool_toggle(box, scat_data, "factory_delay_allow", 
                label=translate("Settings Update Method"),
                icon="FILE_REFRESH",
                arrowopen_propname="ui_openclose_upd_delay", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_openclose_upd_delay");BOOL_VALUE(0)
                return_sublayout=True,
                )
            if is_toggled:

                tocol.prop( scat_data, "factory_update_method",text="")
                
                if (scat_data.factory_update_method=="update_delayed"):
                    tocol.separator(factor=0.5)
                    tocol.prop( scat_data, "factory_update_delay")
                    
                tocol.separator(factor=0.5)

            #Camera group update

            emitter = bpy.context.scene.scatter5.emitter
            psy_active = emitter.scatter5.get_psy_active()

            tocol, is_toggled = ui_templates.bool_toggle(box, scat_win, "dummy_bool_cam", 
                label=translate("Camera Update Dependencies"),
                icon="CAMERA_DATA",
                arrowopen_propname="ui_openclose_upd_cam", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_openclose_upd_cam");BOOL_VALUE(0)
                return_sublayout=True,
                )
            if is_toggled:

                tocol.prop(scat_data,"factory_cam_update_method", text="")

                if (scat_data.factory_cam_update_method=="update_delayed"):
                    tocol.separator(factor=0.5)
                    tocol.prop( scat_data, "factory_cam_update_secs")

                elif ((scat_data.factory_cam_update_method=="update_apply") and psy_active):
                    tocol.separator(factor=0.5)
                    tocol.operator("scatter5.exec_line", text=translate("Refresh"), icon="FILE_REFRESH").api = "update_camera_nodegroup(scene=C.scene, force_update=True, reset_hash=True,)"

                tocol.separator(factor=0.5)

            #Rendered View Overlay 

            ui_templates.bool_toggle(box, scat_data, "update_auto_overlay_rendered", 
                label=translate("Auto-Hide Overlay"), 
                icon="OVERLAY", 
                enabled= not is_rendered_view(),
                arrowopen_propname="*USE_SPACER*",
                )

            ui_templates.separator_box_in(box)
    
    return None 


#   .oooooo.                   o8o            oooo             oooooooooo.    o8o                      oooo
#  d8P'  `Y8b                  `"'            `888             `888'   `Y8b   `"'                      `888
# 888      888    oooo  oooo  oooo   .ooooo.   888  oooo        888      888 oooo   .oooo.o oo.ooooo.   888   .oooo.    .ooooo.   .ooooo.
# 888      888    `888  `888  `888  d88' `"Y8  888 .8P'         888      888 `888  d88(  "8  888' `88b  888  `P  )88b  d88' `"Y8 d88' `88b
# 888      888     888   888   888  888        888888.          888      888  888  `"Y88b.   888   888  888   .oP"888  888       888ooo888
# `88b    d88b     888   888   888  888   .o8  888 `88b.        888     d88'  888  o.  )88b  888   888  888  d8(  888  888   .o8 888    .o
#  `Y8bood8P'Ybd'  `V88V"V8P' o888o `Y8bod8P' o888o o888o      o888bood8P'   o888o 8""888P'  888bod8P' o888o `Y888""8o `Y8bod8P' `Y8bod8P'
#                                                                                            888
#                                                                                           o888o

def draw_terrain_displace(self,layout):

    box, is_open = ui_templates.box_panel(layout, 
        panelopen_propname="ui_extra_displace", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_extra_displace");BOOL_VALUE(0)
        panel_icon="MOD_DISPLACE", 
        panel_name=translate("Quick Displace"),
        popover_info="SCATTER5_PT_docs",
        popover_uilayout_context_set="ui_extra_displace",
        )
    if is_open:

            o = bpy.context.object
            is_linked = bool(o.library) if (o) else False
            box.enabled = not is_linked 
            
            if (o is None):
                box.label(text=translate("No Object Active"),)
                ui_templates.separator_box_in(box)
                return None 
            
            mods = o.modifiers

            row  = box.row()
            row1 = row.row() ; row1.scale_x = 0.17
            row2 = row.row()
            row3 = row.row() ; row3.scale_x = 0.17
            col = row2.column()
            
            if bool(o.library):
                col.enabled = False

            name = "Scatter5 Displace img-uv"
            mod = o.modifiers.get(name)
            if (mod is None):
                op = col.row()
                op.scale_y = 1.2
                ope = op.operator("scatter5.add_displace_uv",text=translate("UV Displace"))
                ope.obj_name = o.name
                ope.mod_name = name
            else:
                col = col.column(align=True)
                row = col.row(align=True) 
                row.scale_y = 1.1
                row.operator("scatter5.dummy",text="UV Displace")
                row.prop(mod,"show_viewport",text="")
                op = row.operator("scatter5.exec_line",text="",icon="TRASH")
                op.api=f"C.object.modifiers.remove(C.object.modifiers['{name}'])"
                op.undo=translate("Removing modifier")
                col.prop(mod,"strength")
                col.prop(mod,"mid_level")

            col.separator()

            name = "Scatter5 Displace noise 01"
            mod = o.modifiers.get(name)
            if (mod is None):
                op = col.row()
                op.scale_y = 1.2
                ope = op.operator("scatter5.add_displace",text=translate("Noise Displace 01"))
                ope.obj_name = o.name
                ope.mod_name = name
            else:
                col = col.column(align=True)
                row = col.row(align=True) 
                row.scale_y = 1.1
                row.operator("scatter5.dummy",text="Noise Displace 01")
                row.prop(mod,"show_viewport",text="")
                op = row.operator("scatter5.exec_line",text="",icon="TRASH")
                op.api=f"C.object.modifiers.remove(C.object.modifiers['{name}'])"
                op.undo=translate("Removing modifier")
                col.prop(mod,"strength")
                col.prop(mod,"mid_level")
                
                t = mod.texture
                if (t is not None):
                    col.prop(t,"noise_scale")
                    col.prop(t,"noise_depth")

            col.separator()

            name = "Scatter5 Displace noise 02"
            mod = o.modifiers.get(name)
            if (mod is None):
                op = col.row()
                op.scale_y = 1.2
                ope = op.operator("scatter5.add_displace",text=translate("Noise Displace 02"))
                ope.obj_name = o.name
                ope.mod_name = name
            else:
                col = col.column(align=True)
                row = col.row(align=True) 
                row.scale_y = 1.1
                row.operator("scatter5.dummy",text="Noise Displace 02")
                row.prop(mod,"show_viewport",text="")
                op = row.operator("scatter5.exec_line",text="",icon="TRASH")
                op.api=f"C.object.modifiers.remove(C.object.modifiers['{name}'])"
                op.undo=translate("Removing modifier")
                col.prop(mod,"strength")
                col.prop(mod,"mid_level")

                t = mod.texture
                if (t is not None):
                    col.prop(t,"noise_scale")
                    col.prop(t,"noise_depth")                    

            ui_templates.separator_box_in(box)

    return None



#  .oooooo..o                      o8o            oooo
# d8P'    `Y8                      `"'            `888
# Y88bo.       .ooooo.   .ooooo.  oooo   .oooo.    888
#  `"Y8888o.  d88' `88b d88' `"Y8 `888  `P  )88b   888
#      `"Y88b 888   888 888        888   .oP"888   888
# oo     .d8P 888   888 888   .o8  888  d8(  888   888
# 8""88888P'  `Y8bod8P' `Y8bod8P' o888o `Y888""8o o888o



def draw_social(self,layout): #TODO update links
    """draw manual sub panel"""

    col = layout.column(align=True)
    box, is_open = ui_templates.box_panel(col, 
        panelopen_propname="ui_extra_links", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_extra_links");BOOL_VALUE(0)
        panel_icon="HELP", 
        panel_name=translate("Help and Links"), 
        )
    if is_open:

            row  = box.row()
            row1 = row.row() ; row1.scale_x = 0.17
            row2 = row.row()
            row3 = row.row() ; row3.scale_x = 0.17
            col = row2.column()

            #title
            txt=col.row(align=True)
            txt.label(text=translate("Official Websites")+":",)

            exp = col.row()
            exp.scale_y = 1.2
            exp.operator("wm.url_open", text=translate("Official Website"),).url = "https://www.geoscatter.com/"

            col.separator()

            exp = col.row()
            exp.scale_y = 1.2
            exp.operator("wm.url_open", text=translate("Discover The Biomes"),).url = "https://www.geoscatter.com/biomes.html"

            col.separator()

            exp = col.row()
            exp.scale_y = 1.2
            exp.operator("wm.url_open", text=translate("Documentation"),).url = "https://www.geoscatter.com/documentation"

            col.separator()

            #title
            txt=col.row(align=True)
            txt.label(text=translate("Social Media")+":",)

            exp = col.row()
            exp.scale_y = 1.2
            exp.operator("wm.url_open", text="Youtube",).url = "https://www.youtube.com/channel/UCdtlx635Lq69YvDkBsu-Kdg"

            col.separator()
            
            exp = col.row()
            exp.scale_y = 1.2
            exp.operator("wm.url_open", text="Twitter",).url = "https://twitter.com/geoscatter/"

            col.separator()

            exp = col.row()
            exp.scale_y = 1.2
            exp.operator("wm.url_open", text="Instagram",).url = "https://www.instagram.com/geoscatter"

            col.separator()

            #title
            txt=col.row(align=True)
            txt.label(text=translate("Customer Service")+":",)

            exp = col.row()
            exp.scale_y = 1.2
            exp.operator("wm.url_open", text="Discord Community",).url = "https://discord.com/invite/F7ZyjP6VKB"

            col.separator()

            exp = col.row()
            exp.scale_y = 1.2
            exp.operator("wm.url_open", text=translate("Personal Assistance"),).url = "https://www.blendermarket.com/products/scatter"

            ui_templates.separator_box_in(box)

    return None


#    .oooooo.   oooo
#   d8P'  `Y8b  `888
#  888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
#  888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
#  888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
#  `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#   `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'



class SCATTER5_PT_extra(bpy.types.Panel):

    bl_idname      = "SCATTER5_PT_extra"
    bl_label       = translate("Extra")
    bl_category    = "USER_DEFINED" #will be replaced right before ui.__ini__.register()
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_context     = ""
    bl_order       = 4

    @classmethod
    def poll(cls, context,):
        if (context.scene.scatter5.emitter is None):
            return False
        if (context.mode not in ('OBJECT','PAINT_WEIGHT','PAINT_VERTEX','PAINT_TEXTURE','EDIT_MESH','EDIT_CURVE',)):
            return False
        return True 
      
    def draw_header(self, context):
        self.layout.label(text="", icon_value=cust_icon("W_SCATTER"),)
        return None 

    def draw_header_preset(self, context):
        emitter_header(self)
        return None

    def draw(self, context):
        layout = self.layout
        draw_extra_panel(self, layout, context,)
        return None


classes = (
            
    SCATTER5_UL_tweaking_masks,
    SCATTER5_PT_extra,

    )


#if __name__ == "__main__":
#    register()

