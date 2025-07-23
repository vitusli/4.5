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
# oooooo     oooo                                                           ooo        ooooo
#  `888.     .8'                                                            `88.       .888'
#   `888.   .8'    .oooooooo oooo d8b  .ooooo.  oooo  oooo  oo.ooooo.        888b     d'888   .ooooo.  oooo d8b  .oooooooo  .ooooo.
#    `888. .8'    888' `88b  `888""8P d88' `88b `888  `888   888' `88b       8 Y88. .P  888  d88' `88b `888""8P 888' `88b  d88' `88b
#     `888.8'     888   888   888     888   888  888   888   888   888       8  `888'   888  888ooo888  888     888   888  888ooo888
#      `888'      `88bod8P'   888     888   888  888   888   888   888       8    Y     888  888    .o  888     `88bod8P'  888    .o
#       `8'       `8oooooo.  d888b    `Y8bod8P'  `V88V"V8P'  888bod8P'      o8o        o888o `Y8bod8P' d888b    `8oooooo.  `Y8bod8P'
#                 d"     YD                                  888                                                d"     YD
#                 "Y88888P'                                 o888o                                               "Y88888P'
#####################################################################################################


import bpy

from ... import utils 
from ... utils.str_utils import no_names_in_double
from ... utils.vg_utils import is_vg_active

from ... resources.icons import cust_icon
from ... translations import translate
from ... resources import directories


url = "https://www.geoscatter.com/" #just link to website?


# oooooooooo.
# `888'   `Y8b
#  888      888 oooo d8b  .oooo.   oooo oooo    ooo
#  888      888 `888""8P `P  )88b   `88. `88.  .8'
#  888      888  888      .oP"888    `88..]88..8'
#  888     d88'  888     d8(  888     `888'`888'
# o888bood8P'   d888b    `Y888""8o     `8'  `8'



def draw_settings(layout,i):

    scat_scene = bpy.context.scene.scatter5
    emitter    = scat_scene.emitter
    masks      = emitter.scatter5.mask_systems
    m          = masks[i]

    layout.separator(factor=0.5)

    #layout setup 

    row = layout.row()
    row.row()
    row.scale_y = 0.9

    row1 = row.row()
    row1.scale_x = 0.80
    lbl = row1.column()
    lbl.alignment="RIGHT"

    row2 = row.row()
    prp = row2.column()

    #settings

    lbl.separator(factor=0.7)
    prp.separator(factor=0.7)

    modname = f"Scatter5 {m.name}"

    mod = emitter.modifiers.get(modname)
    if (mod is not None):
            
        slotidx = mod["Input_48"]

        for i,vgs,add,rever in ((1,"Input_2_attribute_name","Input_3","Input_4"),(2,"Input_6_attribute_name","Input_8","Input_7"),(3,"Input_9_attribute_name","Input_10","Input_11"),(4,"Input_12_attribute_name","Input_13","Input_14"),(5,"Input_15_attribute_name","Input_16","Input_17"),(6,"Input_18_attribute_name","Input_19","Input_20"),(7,"Input_21_attribute_name","Input_22","Input_23"),(8,"Input_24_attribute_name","Input_25","Input_26"),(9,"Input_27_attribute_name","Input_28","Input_29"),(10,"Input_30_attribute_name","Input_31","Input_32"),(11,"Input_33_attribute_name","Input_34","Input_35"),(12,"Input_36_attribute_name","Input_37","Input_38"),(13,"Input_39_attribute_name","Input_40","Input_41"),(14,"Input_42_attribute_name","Input_43","Input_44"),(15,"Input_45_attribute_name","Input_46","Input_47"),):

            if (i>=slotidx*5+1) and (i!=16):
                lbl.separator(factor=2.85)
                prpmore = prp.row(align=True) ; prpmore.scale_y = 0.9
                prpmore.operator("scatter5.exec_line",text=translate("Add More"),icon="ADD").api = f"bpy.data.objects['{emitter.name}'].modifiers['{mod.name}']"+'["Input_48"]+=1'
                break

            eval_ptr = mod[vgs]
            exists = (eval_ptr in emitter.vertex_groups)

            #label
            lbl.label(text=f"{i:02}")
            prprow = prp.row(align=True)
            prprow.prop_search(mod,f'["{vgs}"]', emitter,"vertex_groups",text="",)
            #revert
            if exists:
                prprow.operator("scatter5.exec_line",text="",icon="ARROW_LEFTRIGHT", depress=mod[rever]).api = f"emitter = bpy.data.objects['{emitter.name}'] ; mod =  emitter.modifiers['{mod.name}']  ; mod['{rever}'] = not mod['{rever}'] ; mod.show_viewport = not mod.show_viewport ; mod.show_viewport = not mod.show_viewport"
            
            #quickpaint or quick add
            op = prprow.operator("scatter5.vg_quick_paint",text="",icon="BRUSH_DATA" if exists else "ADD", depress=is_vg_active(emitter,eval_ptr)) ; op.mode = "vg" ; op.group_name = eval_ptr ; op.api = f"emitter.modifiers['{modname}']['{vgs}']" ; op.context_surfaces = "*EMITTER_CONTEXT*"
            
            if exists:

                eval_add = mod[add]
                api = f"emitter = bpy.data.objects['{emitter.name}'] ; mod =  emitter.modifiers['{mod.name}']  ; mod['{add}'] = not mod['{add}'] ; mod.show_viewport = not mod.show_viewport ; mod.show_viewport = not mod.show_viewport" #assign value and refresh mod
                desc = translate("Add/Remove from the vertex group above")
                prprow.separator(factor=0.5)
                add_rem = prprow.row(align=True)
                add_rem.scale_x = 0.9
                op = add_rem.operator("scatter5.exec_line",text="", icon="REMOVE",depress=eval_add) ; op.api = api ; op.description = desc
                op = add_rem.operator("scatter5.exec_line",text="", icon="ADD",depress=not eval_add) ; op.api = api ; op.description = desc

            lbl.separator(factor=0.7)
            prp.separator(factor=0.7)

            continue 
        
        lbl.separator(factor=2.5)
        prp.separator(factor=2.5)

        lbl.label(text=f"")
        prprow = prp.row(align=True)
        prprow.prop_search(mod,f'["Output_5_attribute_name"]', emitter,"vertex_groups",text="",)
        eval_ptr = mod["Output_5_attribute_name"]
        exists = (eval_ptr in emitter.vertex_groups)
        op = prprow.operator("scatter5.vg_quick_paint",text="",icon="BRUSH_DATA" if exists else "ADD", depress=is_vg_active(emitter,eval_ptr)) ; op.mode = "vg" ; op.group_name = eval_ptr ; op.api = f"emitter.modifiers['{modname}']['Output_5_attribute_name']" ; op.context_surfaces = "*EMITTER_CONTEXT*"

    layout.separator()

    return 



#       .o.             .o8        .o8
#      .888.           "888       "888
#     .8"888.      .oooo888   .oooo888
#    .8' `888.    d88' `888  d88' `888
#   .88ooo8888.   888   888  888   888
#  .8'     `888.  888   888  888   888
# o88o     o8888o `Y8bod88P" `Y8bod88P"



def add():

    scat_scene = bpy.context.scene.scatter5
    emitter    = scat_scene.emitter
    masks      = emitter.scatter5.mask_systems

    #add mask to list 
    m = masks.add()
    m.type      = "vgroup_merge"
    m.icon      = "W_ARROW_MERGE"                    
    m.name = m.user_name = no_names_in_double("VgroupMerge", [m.name for m  in masks], startswith00=True)

    modname = f"Scatter5 {m.name}"
    if (modname not in emitter.modifiers):

        mod = utils.import_utils.import_and_add_geonode(emitter, mod_name=modname, node_name=".Scatter5 VgroupMerge", blend_path=directories.addon_vgmasks_blend,)
        mod.show_expanded = False
        mod["Input_2_use_attribute"] = True
        mod["Input_6_use_attribute"] = True
        mod["Input_9_use_attribute"] = True
        mod["Input_12_use_attribute"] = True
        mod["Input_15_use_attribute"] = True
        mod["Input_18_use_attribute"] = True
        mod["Input_21_use_attribute"] = True
        mod["Input_24_use_attribute"] = True
        mod["Input_27_use_attribute"] = True
        mod["Input_30_use_attribute"] = True
        mod["Input_33_use_attribute"] = True
        mod["Input_36_use_attribute"] = True
        mod["Input_39_use_attribute"] = True
        mod["Input_42_use_attribute"] = True
        mod["Input_45_use_attribute"] = True

        m.mod_list = modname

    return 



# ooooooooo.              .o88o.                             oooo
# `888   `Y88.            888 `"                             `888
#  888   .d88'  .ooooo.  o888oo  oooo d8b  .ooooo.   .oooo.o  888 .oo.
#  888ooo88P'  d88' `88b  888    `888""8P d88' `88b d88(  "8  888P"Y88b
#  888`88b.    888ooo888  888     888     888ooo888 `"Y88b.   888   888
#  888  `88b.  888    .o  888     888     888    .o o.  )88b  888   888
# o888o  o888o `Y8bod8P' o888o   d888b    `Y8bod8P' 8""888P' o888o o888o



def refresh(i,obj=None):

    scat_scene = bpy.context.scene.scatter5

    if obj: 
          emitter = obj
    else: emitter = scat_scene.emitter

    masks = emitter.scatter5.mask_systems
    m = masks[i]

    modname = f"Scatter5 {m.name}"
    mod = emitter.modifiers.get(modname)
    if mod is None:
        mod = utils.import_utils.import_and_add_geonode(emitter, mod_name=modname, node_name=".Scatter5 VgroupMerge", blend_path=directories.addon_vgmasks_blend,)
        mod.show_expanded = False
        m.mod_list = modname

    #these should always be at the bottom
    utils.mod_utils.move_queue(emitter,mod, mode="bottom",)

    return 



# ooooooooo.
# `888   `Y88.
#  888   .d88'  .ooooo.  ooo. .oo.  .oo.    .ooooo.  oooo    ooo  .ooooo.
#  888ooo88P'  d88' `88b `888P"Y88bP"Y88b  d88' `88b  `88.  .8'  d88' `88b
#  888`88b.    888ooo888  888   888   888  888   888   `88..8'   888ooo888
#  888  `88b.  888    .o  888   888   888  888   888    `888'    888    .o
# o888o  o888o `Y8bod8P' o888o o888o o888o `Y8bod8P'     `8'     `Y8bod8P'



def remove(i):
    from ..remove import general_mask_remove
    general_mask_remove(obj_name=bpy.context.scene.scatter5.emitter.name,mask_idx=i) #remove vg, vgedit, mask from list, refresh viewport
    return 


