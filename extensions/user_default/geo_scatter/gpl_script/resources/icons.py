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

################################################################################################
#   ooooooooo.                                   o8o
#   `888   `Y88.                                 `"'
#    888   .d88' oooo d8b  .ooooo.  oooo    ooo oooo   .ooooo.  oooo oooo    ooo  .oooo.o
#    888ooo88P'  `888""8P d88' `88b  `88.  .8'  `888  d88' `88b  `88. `88.  .8'  d88(  "8
#    888          888     888ooo888   `88..8'    888  888ooo888   `88..]88..8'   `"Y88b.
#    888          888     888    .o    `888'     888  888    .o    `888'`888'    o.  )88b
#   o888o        d888b    `Y8bod8P'     `8'     o888o `Y8bod8P'     `8'  `8'     8""888P'
#
################################################################################################


import bpy
import bpy.utils.previews

import os
import sys 
import numpy as np

from . import directories


#NOTE General Previews code utility, used to create custom icons but also previews from manager and preset
#Note to self, Dorian, you could centralize everything icon/preview gallery register related perhaps in one and only module? 
# https://docs.blender.org/api/current/bpy.utils.previews.html#bpy.utils.previews.ImagePreviewCollection
# https://docs.blender.org/api/current/bpy.types.ImagePreview.html#imagepreview-bpy-struct


def get_previews_from_directory(directory, extension=".png", previews=None,):
    """install previews with bpy.utils.preview, will try to search for all image file inside given directory"""

    if (previews is None):
        previews = bpy.utils.previews.new()

    for f in os.listdir(directory):
        
        if (f.endswith(extension)):
            
            icon_name = f[:-len(extension)]
            path = os.path.abspath(os.path.join(directory, f))
            
            if (not os.path.isfile(path)):
                print(f"ERROR: get_previews_from_directory(): File not found: {path}")  # Debugging aid
                continue
            try:
                previews.load(icon_name, path, "IMAGE")
            except Exception as e:
                print(f"ERROR: get_previews_from_directory(): loading icon {icon_name} from '{path}':\n{e}")
                continue

            #debug invisible icons..
            if (True):
                if (icon_name!="W_BLANK1"):
                    px = np.array(previews[icon_name].icon_pixels[:])
                    is_all_zeros = np.all(px==0)
                    if (is_all_zeros):
                        print(f"ERROR: get_previews_from_directory(): Invisible icon found {icon_name} from '{path}")
                
        continue 

    return previews 

def get_previews_from_paths(paths, use_basename=True,  previews=None,):
    """install previews with bpy.utils.preview, will loop over list of image path"""

    if (previews is None):
        previews = bpy.utils.previews.new()

    for p in paths :
        
        if (use_basename):
              icon_name = os.path.basename(p).split('.')[0]
        else: icon_name = p  
        
        if (icon_name not in previews):
            
            path = os.path.abspath(p)
            
            previews.load( icon_name, path, "IMAGE")

        continue 

    return previews 

def remove_previews(previews):
    """remove previews wuth bpy.utils.preview"""

    bpy.utils.previews.remove(previews)
    previews.clear()

    return None 

def install_dat_icons_in_cache(directory):
    """Install Dat icons to `space_toolsystem_common.py` `_icon_cache` dictionary, 
    This is used by the native toolsystem and needed for our toolbar hijacking"""

    scr = bpy.utils.system_resource('SCRIPTS')
    pth = os.path.join(scr,'startup','bl_ui')

    if (pth not in sys.path):
        sys.path.append(pth)

    from bl_ui.space_toolsystem_common import _icon_cache

    for f in os.listdir(directory):
        if (f.startswith("SCATTER5") and f.endswith(".dat")):
            _icon_cache[f.replace(".dat","")] = bpy.app.icons.new_triangles_from_file(os.path.join(directory,f))
        continue 

    return None 


# ooooooooo.                             .oooooo.                            .         o8o
# `888   `Y88.                          d8P'  `Y8b                         .o8         `"'
#  888   .d88'  .ooooo.   .oooooooo    888          oooo  oooo   .oooo.o .o888oo      oooo   .ooooo.   .ooooo.  ooo. .oo.    .oooo.o
#  888ooo88P'  d88' `88b 888' `88b     888          `888  `888  d88(  "8   888        `888  d88' `"Y8 d88' `88b `888P"Y88b  d88(  "8
#  888`88b.    888ooo888 888   888     888           888   888  `"Y88b.    888         888  888       888   888  888   888  `"Y88b.
#  888  `88b.  888    .o `88bod8P'     `88b    ooo   888   888  o.  )88b   888 .       888  888   .o8 888   888  888   888  o.  )88b
# o888o  o888o `Y8bod8P' `8oooooo.      `Y8bood8P'   `V88V"V8P' 8""888P'   "888"      o888o `Y8bod8P' `Y8bod8P' o888o o888o 8""888P'
#                        d"     YD
#                        "Y88888P'


#Our custom "W_" Icons are stored here
PREVIEWS_ICONS = {}

def cust_icon(str_value):

    #"W_" Icons
    if (str_value.startswith("W_")):
        global PREVIEWS_ICONS
        if (str_value in PREVIEWS_ICONS):
            return PREVIEWS_ICONS[str_value].icon_id
        return 1

    #"SCATTER5_" Icons = .dat format
    elif str_value.startswith("SCATTER5_"):
        from bl_ui.space_toolsystem_common import _icon_cache
        if (str_value in _icon_cache):
            return _icon_cache[str_value] 

    return 0 


# ooooooooo.             oooo                            .o8  
# `888   `Y88.           `888                           "888  
#  888   .d88'  .ooooo.   888   .ooooo.   .oooo.    .oooo888  
#  888ooo88P'  d88' `88b  888  d88' `88b `P  )88b  d88' `888  
#  888`88b.    888ooo888  888  888   888  .oP"888  888   888  
#  888  `88b.  888    .o  888  888   888 d8(  888  888   888  
# o888o  o888o `Y8bod8P' o888o `Y8bod8P' `Y888""8o `Y8bod88P" 


def icons_reload():
    
    global PREVIEWS_ICONS
    for v in PREVIEWS_ICONS.values():
        v.reload()
        
    return None


#   .oooooo.   oooo
#  d8P'  `Y8b  `888
# 888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
# 888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
# 888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
# `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#  `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'


class SCATTER5_OT_print_icon_id(bpy.types.Operator):

    bl_idname      = "scatter5.print_icon_id"
    bl_label       = ""
    bl_description = "for debug purpose"

    icon : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)

    def execute(self, context):

        print(cust_icon(self.icon))

        return {'FINISHED'}


class SCATTER5_OT_print_icons_dict(bpy.types.Operator):

    bl_idname      = "scatter5.print_icons_dict"
    bl_label       = ""
    bl_description = "for debug purpose"
    
    exc : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)

    def execute(self, context):

        if (not os.path.exists(directories.icons_active)):
            print(f"INFO: SCATTER5_OT_print_icons_dict: Can't print any icons if icon dir don't exists '{directories.icons_active}'")
            return {'CANCELLED'}
            
        if (not os.path.exists(directories.icons_placeholder)):
            print(f"INFO: SCATTER5_OT_print_icons_dict: Can't print any icons if icon dir don't exists '{directories.icons_placeholder}'")
            return {'CANCELLED'}

        global PREVIEWS_ICONS
        
        DirIcons = [ inm.replace(".png","") for inm in os.listdir(directories.icons_active) if inm.startswith('W_') ]
        print("SCATTER5_OT_print_icons_dict")
        
        if (self.exc==""):
            for k,v in PREVIEWS_ICONS.items():
                print(k, v.icon_id, v.icon_size[:], v.image_size[:], )
        else: 
            exec(self.exc)

        return {'FINISHED'}


class SCATTER5_OT_icons_reload(bpy.types.Operator):

    bl_idname      = "scatter5.icons_reload"
    bl_label       = ""
    bl_description = "Repair broken (invisible) icons"

    def execute(self, context):
        
        if (not os.path.exists(directories.icons_active)):
            print(f"INFO: SCATTER5_OT_icons_reload: Can't reload any icons if icon dir don't exists '{directories.icons_active}'")
            return {'CANCELLED'}
            
        if (not os.path.exists(directories.icons_placeholder)):
            print(f"INFO: SCATTER5_OT_icons_reload: Can't reload any icons if icon dir don't exists '{directories.icons_placeholder}'")
            return {'CANCELLED'}
            
        icons_reload()
        
        global PREVIEWS_ICONS
        remove_previews(PREVIEWS_ICONS)
        PREVIEWS_ICONS = get_previews_from_directory(directories.icons_active, extension=".png",)
        PREVIEWS_ICONS = get_previews_from_directory(directories.icons_placeholder, extension=".png", previews=PREVIEWS_ICONS,)
            
        return {'FINISHED'}



classes = (

    SCATTER5_OT_print_icon_id,
    SCATTER5_OT_print_icons_dict,
    SCATTER5_OT_icons_reload,

)


# ooooooooo.
# `888   `Y88.
#  888   .d88'  .ooooo.   .oooooooo
#  888ooo88P'  d88' `88b 888' `88b
#  888`88b.    888ooo888 888   888
#  888  `88b.  888    .o `88bod8P'
# o888o  o888o `Y8bod8P' `8oooooo.
#                        d"     YD
#                        "Y88888P'



def register():

    global PREVIEWS_ICONS
    
    if os.path.exists(directories.icons_active):
          PREVIEWS_ICONS = get_previews_from_directory(directories.icons_active, extension=".png",)
    else: print(f"INFO: icons.register(): Can't register any icons if icon dir don't exists '{directories.icons_active}'")
        
    if os.path.exists(directories.icons_placeholder):
          PREVIEWS_ICONS = get_previews_from_directory(directories.icons_placeholder, extension=".png", previews=PREVIEWS_ICONS,)
    else: print(f"INFO: icons.register(): Can't register any icons if icon dir don't exists '{directories.icons_placeholder}'")
        
    if os.path.exists(directories.icons_dat):
          install_dat_icons_in_cache(directories.icons_dat)
    else: print(f"INFO: icons.register(): Can't register any icons if icon dir don't exists '{directories.icons_dat}'")

    return None 

def unregister():

    if (not os.path.exists(directories.icons_active)):
        print(f"INFO: icons.unregister(): Can't remove any icons if icon dir don't exists '{directories.icons_active}'")
        return None
        
    if (not os.path.exists(directories.icons_placeholder)):
        print(f"INFO: icons.unregister(): Can't remove any icons if icon dir don't exists '{directories.icons_placeholder}'")
        return None
        
    global PREVIEWS_ICONS
    remove_previews(PREVIEWS_ICONS)
    
    return None 