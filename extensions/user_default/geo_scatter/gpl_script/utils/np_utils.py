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


import numpy as np


#NOTE some numpy functions 

def np_remap(vs, array_min="AUTO", array_max="AUTO", normalized_min=0, normalized_max=1, skip_denominator=False):
    """remap values to given minimal and maximal""" 

    #possibility of remap from given min max:
    if (array_min=="AUTO"):
        array_min = vs.min(axis=0)
    else: #if remap, then need to cut array min and max 
        vs = np.where((vs<array_min),array_min,vs)

    if (array_max=="AUTO"):
        array_max = vs.max(axis=0)
    else: #if remap, then need to cut array min and max 
        vs = np.where((vs>array_max),array_max,vs)

    nom = (vs-array_min)*(normalized_max-normalized_min)
    denominator = array_max-array_min

    if (not skip_denominator): #may cause crashes, with normal for example. didn't get why..
        denominator[denominator==0] = 1

    return normalized_min + nom/denominator 


def np_apply_transforms(o, co):
    """local to global numpy coordinates"""

    m = np.array(o.matrix_world)    
    mat = m[:3, :3].T
    loc = m[:3, 3]
    
    return co @ mat + loc


def np_global_to_local(obj, co):
    """local co to local obj"""

    mwi = obj.matrix_world.inverted()
    m = np.array(mwi)
    mat = m[:3, :3].T
    loc = m[:3, 3]
    
    return co @ mat + loc


#   .oooooo.   oooo
#  d8P'  `Y8b  `888
# 888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
# 888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
# 888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
# `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#  `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'


classes = (
    
    )