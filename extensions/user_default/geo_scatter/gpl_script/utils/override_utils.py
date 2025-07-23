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

#Some function i use sometimes if context override do not work 

import bpy

import copy 
from mathutils import Euler, Vector, Color

class mode_override(object):
    """support for selection/active & also mode, i don't think that classic override support mode?"""

    api_convert = {
        "OBJECT"        : "OBJECT"       , 
        "EDIT_MESH"     : "EDIT"         , 
        "SCULPT"        : "SCULPT"       , 
        "PAINT_VERTEX"  : "VERTEX_PAINT" , 
        "PAINT_WEIGHT"  : "WEIGHT_PAINT" , 
        "PAINT_TEXTURE" : "TEXTURE_PAINT",
        }

    def __init__(self, selection=[], active=None, mode="",):
        self._selection, self._active, self._mode = bpy.context.selected_objects, bpy.context.object, bpy.context.mode #should prolly save obj by name to avoid potential crash?
        self.selection, self.active, self.mode = selection, active, mode
        return None 

    def __enter__(self,):
        
        #deselect
        for o in self._selection:
            o.select_set(state=False)
            
        #select new 
        for o in self.selection:
            o.select_set(state=True)
            
        #set active
        if (self.active is not None):
            bpy.context.view_layer.objects.active = self.active
            
        #set mode 
        try: #this is utterly ridiculous, this operator below might throw an error that there's no active object, even if WE DEFINED ONE RIGHT ABOVE.. WTFF
            bpy.ops.object.mode_set(mode=self.api_convert[self.mode])
        except Exception as e:
            print("ERROR: mode_override(): an error occured during object.mode_set():")
            print(e)
        
        return None 

    def __exit__(self,*args):
        
        #deselect
        for o in self.selection:
            o.select_set(state=False)
            
        #select old
        for o in self._selection:
            o.select_set(state=True)
            
        #set active
        if (self._active is not None):
            bpy.context.view_layer.objects.active = self._active
            
        #set mode 
        try:
            bpy.ops.object.mode_set(mode=self.api_convert[self._mode])
        except Exception as e:
            print("ERROR: mode_override(): an error occured during object.mode_set():")
            print(e)
        
        return None 


class attributes_override(object):
    """temporary set attrs from given list of instructions [object,attr_name,temporary_value],[..]] 
    we will use getattr/setattr on these instructions upon enter/exit"""

    def serialize_storage(self,):
        """naive serialization attempt on bpy types, we might need to implement new types later"""
        
        def serialize_element(e):

            #manual serialization?
            #if (type(e) in [Euler, Vector, Color, bpy.types.bpy_prop_array]):
            #    return e[:] 
            #return e
                
            #deepcopy method? perhaps not all types implemented __deep_copy__
            return copy.deepcopy(e)

        try:    
            for i,storage in enumerate(self.old_val.copy()):
                self.old_val[i][2] = serialize_element(storage[2])
        except:
            print("ERROR: override_utils.attributes_override.serialize_storage(): Serialization failed..")

        return None 

    def __init__(self, *args, enable=True, serialize=True):

        #instances attributes
        self.enable = enable
        self.new_val = [] #== instructions
        self.old_val = [] #== storage purpose

        #only if user enables it
        if (not self.enable):
            return None

        #fill instructions/storage lists
        for o,a,v in args: #o,a,v == object,attribute_name,new_value

            if (not hasattr(o,a)):
                continue

            #check if override needed
            current_value = getattr(o,a)
            if (v==current_value):
                continue

            #store values in dict
            self.new_val.append([o,a,v])
            self.old_val.append([o,a,current_value]) #storing bpy.object might cause crash...?

            continue

    #note: if stored value is bpy array for ex, it is not be reliable, need to serialize
        self.serialize_storage()

        return None

    def __enter__(self,):

        #only if user enables it
        if (not self.enable):
            return None

        #setattr from instructions
        for o,a,v in self.new_val:
            #print("new_val:",o,a,v)
            setattr(o,a,v)

        return None

    def __exit__(self,*args):

        #only if user enables it
        if (not self.enable):
            return None

        #restore attributes from storage
        for o,a,v in self.old_val:
            #print("old_val:",o,a,v)
            setattr(o,a,v)

        return None

def get_any_view3d_region(context=None, context_window_first=False,):
    """get the basic window, area, region argument"""
    
    if (context is None):
        context = bpy.context
    
    if (context_window_first):
          windows_list = [context.window] + list(context.window_manager.windows)
    else: windows_list = context.window_manager.windows
    
    for window in windows_list:
        for area in window.screen.areas:
            if (area.type=='VIEW_3D'):
                for region in area.regions:
                    if (region.type=='WINDOW'):
                        return window, area, region
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