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
# ooooo      ooo                 .o8                           .oooooo..o               .       .    o8o                                  
# `888b.     `8'                "888                          d8P'    `Y8             .o8     .o8    `"'                                  
#  8 `88b.    8   .ooooo.   .oooo888   .ooooo.   .oooo.o      Y88bo.       .ooooo.  .o888oo .o888oo oooo  ooo. .oo.    .oooooooo  .oooo.o 
#  8   `88b.  8  d88' `88b d88' `888  d88' `88b d88(  "8       `"Y8888o.  d88' `88b   888     888   `888  `888P"Y88b  888' `88b  d88(  "8 
#  8     `88b.8  888   888 888   888  888ooo888 `"Y88b.            `"Y88b 888ooo888   888     888    888   888   888  888   888  `"Y88b.  
#  8       `888  888   888 888   888  888    .o o.  )88b      oo     .d8P 888    .o   888 .   888 .  888   888   888  `88bod8P'  o.  )88b 
# o8o        `8  `Y8bod8P' `Y8bod88P" `Y8bod8P' 8""888P'      8""88888P'  `Y8bod8P'   "888"   "888" o888o o888o o888o `8oooooo.  8""888P' 
#                                                                                                                     d"     YD           
#                                                                                                                     "Y88888P'                                                                                                                                                 
######################################################################################################

import bpy

from .. scattering.texture_datablock import SCATTER5_PR_node_texture


#####################################################################################################


class SCATTER5_PR_node_group(bpy.types.PropertyGroup): 
    """bpy.data.node_groups[i].scatter5"""
    
    texture : bpy.props.PointerProperty(type=SCATTER5_PR_node_texture)