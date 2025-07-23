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

# oooooooooo.    o8o                                   .                       o8o
# `888'   `Y8b   `"'                                 .o8                       `"'
#  888      888 oooo  oooo d8b  .ooooo.   .ooooo.  .o888oo  .ooooo.  oooo d8b oooo   .ooooo.   .oooo.o
#  888      888 `888  `888""8P d88' `88b d88' `"Y8   888   d88' `88b `888""8P `888  d88' `88b d88(  "8
#  888      888  888   888     888ooo888 888         888   888   888  888      888  888ooo888 `"Y88b.
#  888     d88'  888   888     888    .o 888   .o8   888 . 888   888  888      888  888    .o o.  )88b
# o888bood8P'   o888o d888b    `Y8bod8P' `Y8bod8P'   "888" `Y8bod8P' d888b    o888o `Y8bod8P' 8""888P'


import bpy, os 

# Addon Path (searching is relative from this file.)

product_dir            = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # ../{MainFolder}/
addon_gpl_dir          = os.path.dirname(os.path.dirname(__file__))                   # ../{MainFolder}/gpl_scripts/
non_gpl_dir            = os.path.join(product_dir,"non_gpl")                          # ../{MainFolder}/non_gpl/

addon_resources        = os.path.join(addon_gpl_dir,"resources")        # ../{MainFolder}/gpl_scripts/resources/
addon_thumbnail        = os.path.join(addon_resources,"thumbnail")      # ../{MainFolder}/gpl_scripts/resources/thumbnail/
addon_translations     = os.path.join(addon_resources,"translations")   # ../{MainFolder}/gpl_scripts/resources/translations/
addon_blendf           = os.path.join(addon_resources,"blendfiles")     # ../{MainFolder}/gpl_scripts/resources/blendfiles/
addon_vgmasks_blend    = os.path.join(addon_blendf,"vgmasks.blend")     # ../{MainFolder}/gpl_scripts/resources/blendfiles/vgmasks.blend
addon_visualizer_blend = os.path.join(addon_blendf,"visualizer.blend")  # ../{MainFolder}/gpl_scripts/resources/blendfiles/visualizer.blend
addon_merge_blend      = os.path.join(addon_blendf,"merge.blend")       # ../{MainFolder}/gpl_scripts/resources/blendfiles/merge.blend
addon_curve_blend      = os.path.join(addon_blendf,"curve.blend")       # ../{MainFolder}/gpl_scripts/resources/blendfiles/curve.blend
addon_masks            = os.path.join(addon_gpl_dir,"masks")            # ../{MainFolder}/gpl_scripts/masks/

                                                                        # Stored separately for clear license separation
icons_dir              = os.path.join(non_gpl_dir,"icons")              # ../{MainFolder}/non_gpl/icons/
icons_active           = os.path.join(icons_dir,"used")                 # ../{MainFolder}/non_gpl/icons/used/
icons_placeholder      = os.path.join(icons_dir,"placeholder")          # ../{MainFolder}/non_gpl/icons/placeholder/
icons_dat              = os.path.join(icons_dir,"brushes")              # ../{MainFolder}/non_gpl/icons/brushes/
icons_svg              = os.path.join(icons_dir,"svg")                  # ../{MainFolder}/non_gpl/icons/svg/
icons_logo             = os.path.join(icons_svg,"logo.txt")             # ../{MainFolder}/non_gpl/icons/svg/logo.txt

                                                                        # Stored separately for clear license separation
blends_dir             = os.path.join(non_gpl_dir,"blends")             # ../{MainFolder}/non_gpl/blends/
blend_engine           = os.path.join(blends_dir,"engine.blend")        # ../{MainFolder}/non_gpl/blends/engine.blend
blend_gslogo           = os.path.join(blends_dir,"logo.blend")          # ../{MainFolder}/non_gpl/blends/logo.blend

engine_license = ""
if os.path.exists(blends_dir): # ../{MainFolder}/non_gpl/blends/.license if found!
    for pth in os.listdir(blends_dir):
        if pth.endswith('.license'):
            engine_license = pth
            break
        continue

# Native Blender Paths & added ../data/library

blender_version = bpy.utils.resource_path("USER")               # ../Blender Foundation/Blender/*VERSION*/
blender_user    = os.path.dirname(blender_version)              # ../Blender Foundation/Blender/
blender_data    = os.path.join(blender_user,"data")             # ../Blender Foundation/Blender/data/
lib_default     = os.path.join(blender_data,"scatter library")  # ../Blender Foundation/Blender/data/scatter library/  

# Library Path 
    
lib_library = lib_default                                  # ../scatter library/ 
lib_market  = os.path.join(lib_library,"_market_")         # ../scatter library/_market_/   
lib_userhas = os.path.join(lib_library,"_possessions_")    # ../scatter library/_possessions_/    
lib_biomes  = os.path.join(lib_library,"_biomes_")         # ../scatter library/_biomes_/   
lib_presets = os.path.join(lib_library,"_presets_")        # ../scatter library/_presets_/   
lib_prescat = os.path.join(lib_presets,"per_categories")   # ../scatter library/_presets_/per_categories/
lib_bitmaps = os.path.join(lib_library,"_bitmaps_")        # ../scatter library/_bitmaps_/    



#it will need to update library globals directly after properties are register to access addon_prefs().library_path
#everything is evaluated when import so we are forced to fire up  update_scatter_library_location() from properties register

def update_scatter_library_location(): 
    """update global from directories module with user custom addon_prefs().library_path"""

    from ... __init__ import addon_prefs
    
    new_lib_library = addon_prefs().library_path
    new_lib_market  = os.path.join(new_lib_library,"_market_") 
    new_lib_userhas = os.path.join(new_lib_library,"_possessions_")
    new_lib_biomes  = os.path.join(new_lib_library,"_biomes_") 
    new_lib_presets = os.path.join(new_lib_library,"_presets_")      
    new_lib_bitmaps = os.path.join(new_lib_library,"_bitmaps_")  

    #if user path is wrong or structure not respected, use default path

    if (    (not os.path.exists(new_lib_library) ) 
         or (not os.path.exists(new_lib_biomes) )
         or (not os.path.exists(new_lib_presets) ) 
         or (not os.path.exists(new_lib_bitmaps) ) 
        ):
        print(f"ERROR: update_scatter_library_location(): didn't find essential paths: [\n  '{new_lib_library}',\n  '{new_lib_biomes}',\n  '{new_lib_presets}',\n  '{new_lib_bitmaps}'\n] ")
        return None 

    #apply changes
    global lib_library, lib_market, lib_userhas, lib_biomes, lib_presets, lib_prescat, lib_bitmaps

    lib_library = new_lib_library        
    lib_market  = new_lib_market
    lib_userhas = new_lib_userhas
    lib_biomes  = new_lib_biomes
    lib_presets = new_lib_presets   
    lib_prescat = os.path.join(lib_presets,"per_categories")
    lib_bitmaps = new_lib_bitmaps   

    library_startup()

    return None 


# ooooo         o8o   .o8                                                     .oooooo..o     .                          .
# `888'         `"'  "888                                                    d8P'    `Y8   .o8                        .o8
#  888         oooo   888oooo.  oooo d8b  .oooo.   oooo d8b oooo    ooo      Y88bo.      .o888oo  .oooo.   oooo d8b .o888oo oooo  oooo  oo.ooooo.
#  888         `888   d88' `88b `888""8P `P  )88b  `888""8P  `88.  .8'        `"Y8888o.    888   `P  )88b  `888""8P   888   `888  `888   888' `88b
#  888          888   888   888  888      .oP"888   888       `88..8'             `"Y88b   888    .oP"888   888       888    888   888   888   888
#  888       o  888   888   888  888     d8(  888   888        `888'         oo     .d8P   888 . d8(  888   888       888 .  888   888   888   888
# o888ooooood8 o888o  `Y8bod8P' d888b    `Y888""8o d888b        .8'          8""88888P'    "888" `Y888""8o d888b      "888"  `V88V"V8P'  888bod8P'
#                                                           .o..P'                                                                       888
#                                                           `Y8P'                                                                       o888o


def library_startup():
    """Startup the library directories"""

    from pathlib import Path

    global blender_data, lib_default, lib_biomes, lib_market, lib_userhas, lib_presets, lib_bitmaps   
    for p in [ blender_data, lib_default, lib_biomes, lib_market, lib_userhas, lib_presets, lib_bitmaps]:
        if not os.path.exists(p): 
            Path(p).mkdir(parents=True, exist_ok=True)

    return None      



