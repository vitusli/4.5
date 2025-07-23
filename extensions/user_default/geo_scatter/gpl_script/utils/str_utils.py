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

from ... __init__ import addon_prefs
from .. resources.icons import cust_icon


ALIEN_CHARS = ['/','<','>',':','"','/','\\','|','?','*']

def is_illegal_string(string):
    """check if string has illegal char"""

    return any( (char in ALIEN_CHARS) for char in string )


def legal(string):
    """make string legal"""

    if is_illegal_string(string):
        return ''.join(char for char in string if (not char in ALIEN_CHARS) )
    
    return string 


def find_suffix(string, list_strings, zeros=3,): 
    """find suffix with name that do not exists yet"""

    assert zeros
    i = 1
    new = string
    
    while (new in list_strings):

        suffix_idx = f"{i:0{zeros}d}"
        new = f"{string}.{suffix_idx}"
        i += 1

    return new


def limit_string(word, char_limit,):
    """limit string representation"""

    if len(word)>char_limit-3:
        return word[:char_limit-3] + "..."

    return word


def match_word(search_string, keyword_string,):
    """check if the search string match the keywords values"""

    search_string, keyword_string = search_string.lower(), keyword_string.lower()
    
    r = []
    terms = search_string.split(" ")
    for w in terms:
        r.append(w in keyword_string)

    if (r):
        return all(r)
    
    return False 


def no_names_in_double(string, list_strings, startswith00=False, n=3,):
    """return a correct string with suffix to avoid doubles"""
    #used heavily in masks creation, to get correct names 
    #I Guess that this fct is a clone of find_suffix() ? 

    if (startswith00):
        #Always have suffix, startswith .00

        x=string
        i=0
        if (string+".00" not in list_strings):
            return string + ".00"

        while (f"{x}.{i:02d}" in list_strings):
            i += 1

        return f"{x}.{i:02d}" 

    #else Normal Behavior
    x=string 
    i=1
    while (x in list_strings):
        x = string + f".{i:03d}" if n==3 else string + f".{i:02d}"
        i +=1

    if (string!=x):
        return x

    return string 


def get_surfs_shared_attrs(system=None, surfaces=None, attr_type='', searchname="",):
    """return a list of common attr shared across all given surfaces, or surfaces of given psy/group system"""
    #replacement for old get_surfaces_match_attr() function pre GS5.5
    
    if ((system is None) and (surfaces is None)):
        raise ValueError(f"ERROR: get_surfs_shared_attrs(): Please pass at least a system or surfaces")

    #first find surfaces! surfaces of group or psy!
    if (surfaces is None):
        surfaces = system.get_surfaces()

    #return function that will return empty list if no surfaces
    if (not surfaces):
        return set()
    
    #return list of common attr across all surfaces
    match attr_type:
        case 'vg':
            return set.intersection(*[set(d.name for d in o.vertex_groups if (searchname in d.name)) for o in surfaces])
        case 'vcol':
            return set.intersection(*[ set(d.name for d in o.data.color_attributes if (searchname in d.name)) for o in surfaces])
        case 'uv':
            return set.intersection(*[set(d.name for d in o.data.uv_layers if (searchname in d.name)) for o in surfaces])
        case 'mat':
            return set.intersection(*[set(d.name for d in o.data.materials if ((d is not None) and (searchname in d.name))) for o in surfaces])
        case _:
            raise ValueError(f"ERROR: get_surfs_shared_attrs(): Invalid value '{attr_type}'. Must be in ('vg','vcol','uv','mat',).")
            
    return set()


def is_attr_surfs_shared(system=None, surfaces=None, attr_type='', attr_name="",):
    """check if given attr is shared across all surfs"""
    # mostly used for GUI, important to highlight pointer in red
    
    return attr_name in get_surfs_shared_attrs(system=system, surfaces=surfaces, attr_type=attr_type, searchname=attr_name,)
 
 
def word_wrap(string="", layout=None, alignment="CENTER", max_char=70, char_auto_sidepadding=1.0, context=None, active=False, alert=False, icon=None, scale_y=1.0,):
    """word wrap a piece of string""" 
    
    if ((max_char=='auto') and (context is not None)):
        
        charw = 6.0 # pixel width of a single char
        adjst = 35 # adjustment required
        totpixw = context.region.width * char_auto_sidepadding
        uifac = context.preferences.system.ui_scale
        max_char = ((totpixw/uifac)-adjst)/charw
    
    #adjust user preferences
    max_char = int(max_char * addon_prefs().ui_word_wrap_max_char_factor)
    scale_y = addon_prefs().ui_word_wrap_y * scale_y
    
    def wrap(string,max_char):
        """word wrap function""" 

        original_string = string
        newstring = ""
        
        while (len(string) > max_char):

            # find position of nearest whitespace char to the left of "width"
            marker = max_char - 1
            while (marker >= 0 and not string[marker].isspace()):
                marker = marker - 1

            # If no space was found, just split at max_char
            if (marker==-1):
                marker = max_char
    
            # remove line from original string and add it to the new string
            newline = string[0:marker] + "\n"
            newstring = newstring + newline
            string = string[marker + 1:]

        return newstring + string


    #Multiline string? 
    if ("\n" in string):
          wrapped = "\n".join([wrap(l,max_char) for l in string.split("\n")])
    else: wrapped = wrap(string,max_char)

    #UI Layout Draw? 

    if (layout is not None):

        lbl = layout.column()
        lbl.active = active 
        lbl.alert = alert
        lbl.scale_y = scale_y

        for i,l in enumerate(wrapped.split("\n")):

            if (alignment):
                  line = lbl.row()
                  line.alignment = alignment
            else: line = lbl

            if (icon and (i==0)):
                if (icon.startswith("W")):
                    line.label(text=l, icon_value=cust_icon(icon),)    
                    continue
                line.label(text=l, icon=icon)    
                continue

            line.label(text=l)
            continue 
    
    return wrapped


def as_version_tuple(itm, trunc_to=''):
    """unify all possible versioning fromat into a single float value, in order to easily make compatibility comparison for example"""
            
    def contains_int_only(container):
        is_made_of_int = all(isinstance(obj, int) for obj in container)
        if (not is_made_of_int):
            print(f"ALERT: as_version_tuple(): unrecognized input: '{container}' of type {type(container)}, contains non-integer values. Impossible to convert this itm to a version tuple")
        return is_made_of_int

    version_tuple = (0,0,0)

    match itm:
        
        case tuple():
            if contains_int_only(itm):
                version_tuple = itm
                
        case list() | set():
            if contains_int_only(itm):
                version_tuple = tuple(itm)
                
        case int():
            version_tuple = (itm,0,0)
            
        case float():
            floatstr = str(itm)
            nbr,decimal = floatstr.split('.')
            version_tuple = (int(nbr),int(decimal),0)
            
        case str() if ('.' in itm):
            cleanstr = ''.join(char for char in itm if char in "0123456789.") #we remove any kind of non-numerical infos, aka "Beta","Alpha","Release"," ","LTS" ect..
            version_tuple = tuple(int(char) for char in cleanstr.split('.'))
         
        case str():
            print(f"ALERT: as_version_tuple(): unrecognized str: '{itm}', Impossible convert to a version tuple, does not contains '.'?")
        
        case _:
            print(f"ALERT: as_version_tuple(): unrecognized input: '{itm}' of type {type(itm)}, Impossible convert to a version tuple")
        
    # truncate to only essential version?
    if (trunc_to!='') and (trunc_to in ('major','minor','patch')):
        i = 1 if (trunc_to=='major') else 2 if (trunc_to=='minor') else 3
        version_tuple = version_tuple[:i]
        
    return version_tuple


#   .oooooo.   oooo
#  d8P'  `Y8b  `888
# 888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
# 888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
# 888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
# `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#  `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'


classes = (
    
    )