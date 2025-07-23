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

#NOTE Here it's a bunch of functions related to math, float, int, vec, ect..


def ensure_rgba_colors(value):
    """ensure given value is a tuple of 4 float value"""

    # Ensure the input is at least iterable
    if (not hasattr(value,'__iter__')):
        raise ValueError("ERROR: ensure_rgba_colors(): The input must be an iterable of length 3 or 4.")

    # Convert the input to a list
    if (type(value) is not list):
        value = list(value)
    
    # Check the length and adjust if necessary
    if (len(value)!=4):
        if (len(value)==3):
            value.append(1.0)
        else:
            raise ValueError("ERROR: ensure_rgba_colors(): The input must be an iterable of length 3 (RGB) or 4 (RGBA).")
    
    return value


def generate_uuid_int(existing_uuids=[], exclude_zero=True, int_limit=2_147_483_646,):
    """Generate a unique UUID integer ranging from -2Billion to +2Billion."""
    
    # careful with the int range limits
    assert int_limit<=2_147_483_646
    
    if (exclude_zero):
        existing_uuids.append(0)
        
    # Check if it's possible to generate more UUIDs
    range_limit = (int_limit*2)-5
    if (len(existing_uuids) >= range_limit):
        raise ValueError("ERROR: generate_uuid_int(): Impossible to generate more UUIDs")
    
    import random
    u = 0
    while (u == 0) or (u in existing_uuids):
        u = random.randint(-int_limit, int_limit)
    
    return u


def smart_round(f):
    """return float value with rounding appropriate depending on decimal value"""
    
    if (f<0.0001):
        return round(f,6)
    if (f<0.001):
        return round(f,5)
    if (f<0.01):
        return round(f,4)
    if (f<0.1):
        return round(f,3)
    if (f<1.0):
        return round(f,2)
    if (f<100):
        return round(f,1)
    
    return int(f)


def square_area_repr(f):
    """stringify squarearea to cm²/m²/ha/km²"""
    
    if (f<0.1):
        return f"{int(f*10_000)} cm²"
    
    if (f<5_000):
        return f"{f:.1f} m²"
    
    if (f<1_000_000):
        return f"{f/10_000:.1f} ha"
    
    return f"{f/1_000_000:.1f} km²"


def count_repr(f, unit="",):
    """get string version of scatter count"""

    return "..." if (f==-1) else f'{f:,} {unit}'


#   .oooooo.   oooo
#  d8P'  `Y8b  `888
# 888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
# 888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
# 888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
# `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#  `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'


classes = (
    
    )