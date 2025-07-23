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
# ooooo                                                      ooooooooo.              o8o                  .    o8o
# `888'                                                      `888   `Y88.            `"'                .o8    `"'
#  888          .oooo.   oooo    ooo  .ooooo.  oooo d8b       888   .d88'  .oooo.   oooo  ooo. .oo.   .o888oo oooo  ooo. .oo.    .oooooooo
#  888         `P  )88b   `88.  .8'  d88' `88b `888""8P       888ooo88P'  `P  )88b  `888  `888P"Y88b    888   `888  `888P"Y88b  888' `88b
#  888          .oP"888    `88..8'   888ooo888  888           888          .oP"888   888   888   888    888    888   888   888  888   888
#  888       o d8(  888     `888'    888    .o  888           888         d8(  888   888   888   888    888 .  888   888   888  `88bod8P'
# o888ooooood8 `Y888""8o     .8'     `Y8bod8P' d888b         o888o        `Y888""8o o888o o888o o888o   "888" o888o o888o o888o `8oooooo.
#                        .o..P'                                                                                                 d"     YD
#                        `Y8P'                                                                                                  "Y88888P'
#####################################################################################################


import bpy 

from ... import utils 
from ... utils.str_utils import no_names_in_double

from ... resources.icons import cust_icon
from ... translations import translate


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
    row1.scale_x = 1.0
    lbl = row1.column()
    lbl.alignment="RIGHT"

    row2 = row.row()
    prp = row2.column()

    #operators

    lbl.separator(factor=0.7)
    prp.separator(factor=0.7)

    lbl.label(text=translate("Operators"))
    op = prp.operator("scatter5.layer_paint_mode",text=translate("Paint"),icon="BRUSH_DATA")
    op.obj_name = emitter.name
    op.vg_name = m.name

    lbl.separator(factor=0.7)
    prp.separator(factor=0.7)

    lbl.label(text="")
    op = prp.operator("scatter5.layer_paint_reverse",text=translate("Reverse"),icon="ARROW_LEFTRIGHT")
    op.obj_name = emitter.name
    op.vg_name = m.name

    lbl.separator(factor=0.7)
    prp.separator(factor=0.7)

    lbl.label(text="")
    op = prp.operator("scatter5.layer_paint_fill",text=translate("Set Full"),icon="RADIOBUT_ON")
    op.obj_name = emitter.name
    op.vg_name = m.name
    op.weight = 1

    lbl.separator(factor=0.7)
    prp.separator(factor=0.7)

    lbl.label(text="")
    op = prp.operator("scatter5.layer_paint_fill",text=translate("Set Empty"),icon="RADIOBUT_OFF")
    op.obj_name = emitter.name
    op.vg_name = m.name
    op.weight = 0

    lbl.separator(factor=0.7)
    prp.separator(factor=0.7)

    lbl.label(text="")
    op = prp.operator("scatter5.vg_transfer",text=translate("Transfer"),icon="PASTEDOWN")
    op.vg_destination = m.name
    op.display_des = False

    #weight remapping 

    lbl.separator(factor=3.7)
    prp.separator(factor=3.7)

    lbl.label(text=translate("Remap"))
    mod_name   = f"Scatter5 Remapping {m.name}"
    if (mod_name in emitter.modifiers) and (emitter.modifiers[mod_name].falloff_type=="CURVE"):
        mod = emitter.modifiers[mod_name]
        remap = prp.row(align=True)
        o = remap.operator("scatter5.graph_dialog",text=translate("Remap Values"),icon="FCURVE")
        o.source_api= f"bpy.data.objects['{emitter.name}'].modifiers['{mod.name}']"
        o.mapping_api= f"bpy.data.objects['{emitter.name}'].modifiers['{mod.name}'].map_curve"
        o.mask_name = m.name
        
        butt = remap.row(align=True)
        butt.operator("scatter5.property_toggle",
               text="",
               icon="RESTRICT_VIEW_OFF" if mod.show_viewport else"RESTRICT_VIEW_ON",
               depress=mod.show_viewport,
               ).api = f"bpy.context.scene.scatter5.emitter.modifiers['{mod_name}'].show_viewport"
    else:
        o = prp.operator("scatter5.vg_add_falloff",text=translate("Add Remap"),icon="FCURVE")
        o.mask_name = m.name
        

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
    m.type = "layer_paint"
    m.icon = "BRUSH_DATA"                        
    m.name = m.user_name = no_names_in_double("VgroupPaint", [vg.name for vg  in emitter.vertex_groups], startswith00=True)

    #create the vertex group
    vg = utils.vg_utils.create_vg(emitter, m.name, fill=0, )

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

    masks     = emitter.scatter5.mask_systems
    m         = masks[i]

    if (m.name not in emitter.vertex_groups):
        vg = utils.vg_utils.create_vg(emitter, m.name, fill=0, )

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




#   .oooooo.   oooo
#  d8P'  `Y8b  `888
# 888           888   .oooo.    .oooo.o  .oooo.o
# 888           888  `P  )88b  d88(  "8 d88(  "8
# 888           888   .oP"888  `"Y88b.  `"Y88b.
# `88b    ooo   888  d8(  888  o.  )88b o.  )88b
#  `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P'



class SCATTER5_OT_layer_paint_mode(bpy.types.Operator):

    bl_idname      = "scatter5.layer_paint_mode"
    bl_label       = translate("Enter Paint Mode")
    bl_description = ""
    bl_options     = {'INTERNAL','UNDO'}

    obj_name  : bpy.props.StringProperty()
    vg_name   : bpy.props.StringProperty()

    def execute(self, context):
        obj = bpy.data.objects[self.obj_name]
        
        #set object active
        bpy.context.view_layer.objects.active = obj

        #set vg active 
        if self.vg_name in obj.vertex_groups: 
            bpy.ops.object.vertex_group_set_active(group=self.vg_name)

        #enter weight painting mode 
        if bpy.context.mode == "OBJECT":
            bpy.ops.paint.weight_paint_toggle()
        
        bpy.context.scene.tool_settings.unified_paint_settings.weight = 1
        bpy.context.space_data.show_region_tool_header = True

        return {'FINISHED'}


class SCATTER5_OT_layer_paint_reverse(bpy.types.Operator):

    bl_idname      = "scatter5.layer_paint_reverse"
    bl_label       = translate("Reverse Weight")
    bl_description = ""
    bl_options     = {'INTERNAL','UNDO'}

    obj_name  : bpy.props.StringProperty()
    vg_name   : bpy.props.StringProperty()

    def execute(self, context):

        obj = bpy.data.objects[self.obj_name]
        if self.vg_name not in obj.vertex_groups:
            return {'FINISHED'} 

        #override mode to weight painting
        with utils.override_utils.mode_override(selection=[obj], active=obj, mode="PAINT_WEIGHT"):
            
            bpy.ops.object.vertex_group_set_active(group=self.vg_name)
            bpy.ops.object.vertex_group_invert()

        return {'FINISHED'}


class SCATTER5_OT_layer_paint_fill(bpy.types.Operator):

    bl_idname      = "scatter5.layer_paint_fill"
    bl_label       = translate("Fill Weight")
    bl_description = ""
    bl_options     = {'INTERNAL','UNDO'}

    obj_name : bpy.props.StringProperty()
    vg_name  : bpy.props.StringProperty()
    weight   : bpy.props.BoolProperty()

    def execute(self, context):

        obj = bpy.data.objects[self.obj_name]
        utils.vg_utils.create_vg(obj, self.vg_name, fill=self.weight, )

        return {'FINISHED'}
