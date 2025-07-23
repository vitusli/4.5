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
# oooooo   oooooo     oooo  o8o                    .oooooo..o               .       .    o8o                                  
#  `888.    `888.     .8'   `"'                   d8P'    `Y8             .o8     .o8    `"'                                  
#   `888.   .8888.   .8'   oooo  ooo. .oo.        Y88bo.       .ooooo.  .o888oo .o888oo oooo  ooo. .oo.    .oooooooo  .oooo.o 
#    `888  .8'`888. .8'    `888  `888P"Y88b        `"Y8888o.  d88' `88b   888     888   `888  `888P"Y88b  888' `88b  d88(  "8 
#     `888.8'  `888.8'      888   888   888            `"Y88b 888ooo888   888     888    888   888   888  888   888  `"Y88b.  
#      `888'    `888'       888   888   888       oo     .d8P 888    .o   888 .   888 .  888   888   888  `88bod8P'  o.  )88b 
#       `8'      `8'       o888o o888o o888o      8""88888P'  `Y8bod8P'   "888"   "888" o888o o888o o888o `8oooooo.  8""888P' 
#                                                                                                         d"     YD           
#                                                                                                         "Y88888P'                                                                                                                                              
######################################################################################################

import bpy
import re
import os
import pathlib

from .. resources.directories import product_dir
from .. translations import translate
from .. utils.path_utils import get_subpaths

from .. ui.ui_biome_library import SCATTER5_PR_library
from .. ui.ui_biome_library import SCATTER5_PR_folder_navigation


######################################################################################################


class SCATTER5_PR_ui(bpy.types.PropertyGroup): 
    """scat_ui = bpy.context.window_manager.scatter5.ui, props used for opening/closing gui"""

    # NOTE:
    # procedurally register the boolean props used for interface, all ui props need to be in bpy.context.window_manager to ingore history
    # we search for keywords commented in our whole projects and register our props with their default values
    # https://blender.stackexchange.com/questions/269837/how-to-pass-text-argument-to-a-popover-panel
    # this is our alternative solution ( than manually registering dedicated properties 30+ times for our header settings/docs popovers
    # we procedurally add these properties to scat_ui.popovers_args at regtime, we just search for string arg in tagged comment lines

    dummy : bpy.props.BoolProperty() #dummy needed just to make the class valid

    def codegen_reg_ui_booleans(scope_ref={},):
        """codegen for registering all ui open/close properties. example: 'INSTRUCTION:REGISTER:UI:BOOL_NAME("my_ui_property");BOOL_VALUE(0)' """

        d,keywords,defaults = {},[],[]

        #search everywhere except here
        files = get_subpaths(product_dir, file_type=".py", excluded_files=["windows_settings.py",])
        for py in files:
            with open(py, "r", encoding="utf-8") as file:
                for line in file.readlines():
                    matches = re.findall(r'INSTRUCTION:REGISTER:UI:BOOL_NAME\("(.*?)"\);BOOL_VALUE\((.*?)\)', line)
                    for match in matches:
                        propname, propvalstr = match
                        keywords.append(propname)
                        defaults.append(int(propvalstr))
                        continue
            continue

        assert len(keywords)==len(defaults), "ERROR: codegen_reg_ui_booleans(): Something went wrong on the registration process"
        
        #register the properties
        for (propname,propval) in zip(keywords,defaults):
            if (propname not in d.keys()):
                d[propname] = bpy.props.BoolProperty(default=bool(propval), name=translate("Reveal Interface"), description=translate("Open or Close this interface layout.\nPro-tip: Drag over many arrows while holding your left click to easily open/close many panels in one gesture"),)
            continue

        #define objects in dict
        scope_ref.update(d)
        return d

    #BoxPanel opening/closing props, registered on the fly 
    codegen_reg_ui_booleans(scope_ref=__annotations__)


class SCATTER5_PR_Window(bpy.types.PropertyGroup):
    """bpy.context.window_manager.scatter5
    WindoWManager props will reset on each session & never registered in undo history"""

    # 88""Yb 88  dP"Yb  8b    d8 888888     88     88 88""Yb 
    # 88__dP 88 dP   Yb 88b  d88 88__       88     88 88__dP 
    # 88""Yb 88 Yb   dP 88YbdP88 88""       88  .o 88 88""Yb 
    # 88oodP 88  YbodP  88 YY 88 888888     88ood8 88 88oodP 

    library : bpy.props.CollectionProperty(type=SCATTER5_PR_library) #Children Collection
    library_search : bpy.props.StringProperty(
        name="",
        description=translate("Search in your biome library"),
        )
    library_filter_favorite : bpy.props.BoolProperty(
        name="",
        description=translate("Only show favorite biomes"),
        )

    # 88""Yb 88  dP"Yb  8b    d8 888888     88b 88    db    Yb    dP 
    # 88__dP 88 dP   Yb 88b  d88 88__       88Yb88   dPYb    Yb  dP  
    # 88""Yb 88 Yb   dP 88YbdP88 88""       88 Y88  dP__Yb    YbdP   
    # 88oodP 88  YbodP  88 YY 88 888888     88  Y8 dP""""Yb    YP    

    folder_navigation : bpy.props.CollectionProperty(type=SCATTER5_PR_folder_navigation) #Children Collection
    folder_navigation_idx : bpy.props.IntProperty()
    
    #  dP""b8 88   88 88 
    # dP   `" 88   88 88 
    # Yb  "88 Y8   8P 88 
    #  YboodP `YbodP' 88 
    
    ui : bpy.props.PointerProperty(type=SCATTER5_PR_ui)

    # 8b    d8  dP"Yb  8888b.     db    88     
    # 88b  d88 dP   Yb  8I  Yb   dPYb   88     
    # 88YbdP88 Yb   dP  8I  dY  dP__Yb  88  .o 
    # 88 YY 88  YbodP  8888Y"  dP""""Yb 88ood8  
    
    mode : bpy.props.StringProperty(
        default="", 
        description="mode currently used: DRAW_AREA | MANUAL | PSY_MODAL | FACE_SEL | DIST_MEASURE",
        )
        #TODO, we are not consistant with this isn't it? 
        #NOTE, possibly not compatible with headless blender? but well, modal's can't be anyway
        #NOTE: there's a new api implemented to check which modal operator is active. This property is no longer needed
        
    # 8b    d8    db    88b 88    db     dP""b8 888888 88""Yb 
    # 88b  d88   dPYb   88Yb88   dPYb   dP   `" 88__   88__dP 
    # 88YbdP88  dP__Yb  88 Y88  dP__Yb  Yb  "88 88""   88"Yb  
    # 88 YY 88 dP""""Yb 88  Y8 dP""""Yb  YboodP 888888 88  Yb 
    
    category_manager : bpy.props.EnumProperty(
        default="prefs",
        items=(
            ("library", translate("Biomes"), translate("This is where you'll find your biome library"),),    
            ("market", translate("Scatpack"), translate("This is where you can see which biome pack is currently available online.\nNote that this interface will fetch information from our servers"),),
            None,
            ("lister_large", translate("Lister"), translate("This is where all the scatter-system(s) of your scene are displayed.\nYou'll be able to easily control the visibility features of your scatters from this condensed interface"),),
            ("lister_stats", translate("Statistics"), translate("This is where all the statistics of your scatter-system(s) are listed.\nYou'll be able to quickly overview which scatter's might generate too many instances and thus slow you down!"),),
            None,
            ("prefs", translate("Preferences"), translate("This is where you will be able to tweak your plugin preferences"),),
            ),
        )

    # 8888b.  88   88 8b    d8 8b    d8 Yb  dP 
    #  8I  Yb 88   88 88b  d88 88b  d88  YbdP  
    #  8I  dY Y8   8P 88YbdP88 88YbdP88   8P   
    # 8888Y"  `YbodP' 88 YY 88 88 YY 88  dP    

    dummy_bool_full : bpy.props.BoolProperty(
        name="",
        get=lambda s: True,
        )
    dummy_bool_empty : bpy.props.BoolProperty(
        name="",
        get=lambda s: False,
        )
    dummy_bool_cam : bpy.props.BoolProperty(
        name=translate("Camera Update Dependencies"),
        description=translate("Choose how you'd like the plugin to handle refresh signal when the active camera moves"),
        get=lambda s: True,
        set=lambda s, v: None,
        )
    dummy_idx : bpy.props.IntProperty(
        name="",
        default=-1,
        min=-1,
        max=-1,
        )
    dummy_global_only : bpy.props.EnumProperty(
        name=translate("Space"),
        description=translate("Under the current scatter configuration, only 'Global' space is available for this feature"),
        default="global", 
        items=(("global", translate("Global"), translate(""), "WORLD", 1),
               ("global_bis", translate("Global"), translate(""), "WORLD", 2),
              ),
        )
    dummy_local_only : bpy.props.EnumProperty(
        name=translate("Space"),
        description=translate("Under the current scatter configuration, only 'Local' space is available for this feature"),
        default="local", 
        items=(("local", translate("Local"), translate(""), "ORIENTATION_LOCAL", 1),
               ("local_bis", translate("Local"), translate(""), "ORIENTATION_LOCAL", 2),
              ),
        )
    