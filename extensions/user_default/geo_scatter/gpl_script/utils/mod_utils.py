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


import bpy

from itertools import chain

from . override_utils import attributes_override


#NOTE modstack related functions

def optimize_modstack(obj):
    """return argument to unpack for attr overrides"""
    
    return [[m,"show_viewport",False] for m in obj.modifiers]


def is_a_above_b(obj, a="my_name", b="my_other_name",):
    """check modifier order (compare index)"""

    if (a==b):
        return False
    
    d = {m.name:i for i, m in enumerate(obj.modifiers)}
    return bool(d[a.name]<d[b.name])


def get_mod_idx(obj,mod):
    """get index of mod"""

    for i,m in enumerate(obj.modifiers):
        if (m==mod):
            return i

    return None

def move_queue(obj, mod, mode="bottom",):

    with attributes_override(*optimize_modstack(obj)):
        
        match mode:
            case 'top':
                idx, move_operator = 0, bpy.ops.object.modifier_move_up
            case 'bottom':
                idx, move_operator = -1, bpy.ops.object.modifier_move_down

        while (obj.modifiers[idx]!=mod):
            with bpy.context.temp_override(object=obj):
                move_operator(modifier=mod.name)

    return None 


def order_by_names(obj, names=[], strict=True, modtype_filter=[], ): #NOTE immutable in param? ouch
    """order the modstack by names, filter by type option"""

    def find_first_idx():
    
        for m in obj.modifiers:

            #filter by type
            if (modtype_filter):
                if (m.type not in modtype_filter):
                    continue 

            #filter by name strict
            if (strict):
                if (m.name in names):
                    return get_mod_idx(obj,m) 

            #filter by name relax
            else:
                for n in names: 
                    if (n in m.name):
                        return get_mod_idx(obj,m) 

        return None 
    
    with attributes_override(*optimize_modstack(obj)):

        #find the mod in this list that is the highest of all 
        first_idx = find_first_idx()

        #move to the top
        for n in reversed(names):
            for m in obj.modifiers:  
                
                #filters
                if (modtype_filter and (m.type not in modtype_filter)):
                    continue
                
                elif (strict and (m.name!=n)):
                    continue
                
                elif (n not in m.name):
                    continue
                
                #move until 
                top = obj.modifiers[first_idx]
                while is_a_above_b(obj, a=top, b=m,):
                    with bpy.context.temp_override(object=obj):
                        bpy.ops.object.modifier_move_up(modifier=m.name)
        
    return None


#   .oooooo.   oooo
#  d8P'  `Y8b  `888
# 888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
# 888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
# 888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
# `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#  `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'


classes = (
    
    )