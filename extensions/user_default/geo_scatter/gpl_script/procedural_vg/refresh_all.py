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
# ooooooooo.              .o88o.                             oooo                       oooo  oooo
# `888   `Y88.            888 `"                             `888                       `888  `888
#  888   .d88'  .ooooo.  o888oo  oooo d8b  .ooooo.   .oooo.o  888 .oo.         .oooo.    888   888
#  888ooo88P'  d88' `88b  888    `888""8P d88' `88b d88(  "8  888P"Y88b       `P  )88b   888   888
#  888`88b.    888ooo888  888     888     888ooo888 `"Y88b.   888   888        .oP"888   888   888
#  888  `88b.  888    .o  888     888     888    .o o.  )88b  888   888       d8(  888   888   888
# o888o  o888o `Y8bod8P' o888o   d888b    `Y8bod8P' 8""888P' o888o o888o      `Y888""8o o888o o888o
# 
#####################################################################################################


import bpy

from . import mask_type 
from .. translations import translate



class SCATTER5_OT_refresh_every_masks(bpy.types.Operator):
    """main scattering operator for user in 'Creation>Scatter' """

    bl_idname      = "scatter5.refresh_every_masks"
    bl_label       = ""
    bl_description = ""

    def execute(self, context):

        scat_scene = bpy.context.scene.scatter5
        emitter    = scat_scene.emitter 
        masks      = emitter.scatter5.mask_systems

        for i,m in enumerate(masks):
            exec(f"mask_type.{m.type}.refresh({i})")

        return {'FINISHED'}

class SCATTER5_OT_refresh_mask(bpy.types.Operator):

    bl_idname      = "scatter5.refresh_mask"
    bl_label       = translate("Refresh a mask")
    bl_description = translate("Refresh a mask")
    bl_options     = {'INTERNAL','UNDO'}

    mask_type : bpy.props.StringProperty()
    mask_idx  : bpy.props.IntProperty()

    def execute(self, context):

        exec(f"mask_type.{self.mask_type}.refresh({self.mask_idx})")

        return {'FINISHED'}


# ooooo   ooooo                             .o8  oooo
# `888'   `888'                            "888  `888
#  888     888   .oooo.   ooo. .oo.    .oooo888   888   .ooooo.  oooo d8b
#  888ooooo888  `P  )88b  `888P"Y88b  d88' `888   888  d88' `88b `888""8P
#  888     888   .oP"888   888   888  888   888   888  888ooo888  888
#  888     888  d8(  888   888   888  888   888   888  888    .o  888
# o888o   o888o `Y888""8o o888o o888o `Y8bod88P" o888o `Y8bod8P' d888b


def refresh_selected():

    for o in bpy.context.scene.objects: 

        masks = o.scatter5.mask_systems

        for i,m in enumerate(masks):
            if m.anim:
                exec(f"mask_type.{m.type}.refresh({i},obj=bpy.data.objects['{o.name}'])")

    return None


#    .oooooo.   oooo
#   d8P'  `Y8b  `888
#  888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
#  888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
#  888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
#  `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#   `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'


classes = (

    SCATTER5_OT_refresh_every_masks,
    SCATTER5_OT_refresh_mask,

    )

#if __name__ == "__main__":
#    register()