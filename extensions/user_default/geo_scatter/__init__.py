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
# (c) 2024 Dorian Borremans, Jakub Uhlik


# oooooooooo.  oooo       o8o               .o88o.           
# `888'   `Y8b `888       `"'               888 `"           
#  888     888  888      oooo  ooo. .oo.   o888oo   .ooooo.  
#  888oooo888'  888      `888  `888P"Y88b   888    d88' `88b 
#  888    `88b  888       888   888   888   888    888   888 
#  888    .88P  888       888   888   888   888    888   888 
# o888bood8P'  o888o     o888o o888o o888o o888o   `Y8bod8P' 


bl_info = { #PLEASE ALSO UPDATE 'blender_manifest.toml' !!!
    "name"           : "Geo-Scatter®",
    
    #versioning
    "description"    : "Geo-Scatter 5.5.2 for Blender 4.2+ (Individual License)",
    "version"        : (5, 5, 2),
    "blender"        : (4, 2, 0),
    
    #Update me on each major release thank you!
    "git_sha"        : "292f7771661764ffa07ac5612f6a58084d09a6d9", #== last git push SHA
    "git_desc"       : "auto save image in user library", #== last git push description
    
    #geometry-node engine info
    "engine_nbr"     : "MKV",
    "engine_version" : "Geo-Scatter Engine MKV", #PLEASE ALSO UPDATE '.TEXTURE *DEFAULT* MKV'
    
    "author"         : "bd3d, Carbon2",
    "doc_url"        : "https://www.geoscatter.com/documentation",
    "tracker_url"    : "https://discord.com/invite/F7ZyjP6VKB",
    "category"       : "",
    }


# ooooooooooooo                                         oooo                .             
# 8'   888   `8                                         `888              .o8             
#      888      oooo d8b  .oooo.   ooo. .oo.    .oooo.o  888   .oooo.   .o888oo  .ooooo.  
#      888      `888""8P `P  )88b  `888P"Y88b  d88(  "8  888  `P  )88b    888   d88' `88b 
#      888       888      .oP"888   888   888  `"Y88b.   888   .oP"888    888   888ooo888 
#      888       888     d8(  888   888   888  o.  )88b  888  d8(  888    888 . 888    .o 
#     o888o     d888b    `Y888""8o o888o o888o 8""888P' o888o `Y888""8o   "888" `Y8bod8P' 
                                                                                        
                                                        
from . gpl_script.translations import load_translations_csv
load_translations_csv()
    

#   .oooooo.                  .        ooooooooo.                       .o88o.          
#  d8P'  `Y8b               .o8        `888   `Y88.                     888 `"          
# 888            .ooooo.  .o888oo       888   .d88' oooo d8b  .ooooo.  o888oo   .oooo.o 
# 888           d88' `88b   888         888ooo88P'  `888""8P d88' `88b  888    d88(  "8 
# 888     ooooo 888ooo888   888         888          888     888ooo888  888    `"Y88b.  
# `88.    .88'  888    .o   888 .       888          888     888    .o  888    o.  )88b 
#  `Y8bood8P'   `Y8bod8P'   "888"      o888o        d888b    `Y8bod8P' o888o   8""888P' 
                                                                                      

def addon_prefs():
    """get preferences path from base_package, __package__ path change from submodules"""
    import bpy
    return bpy.context.preferences.addons[__package__].preferences


def blend_prefs():
    """return `scat_data = bpy.data.texts['.Geo-Scatter: Per BlendFile Properties'].scatter5` create text if doesnt exists yet"""
    import bpy
    name = ".Geo-Scatter: Per BlendFile Properties" #startswith '.' so is invisible by user
    if (name not in bpy.data.texts):
        t = bpy.data.texts.new(name)
        t.from_string(f"\n\n# DO NOT DELETE THIS TEXT, IMPORTANT PLUGIN SETTINGS ARE STORED ON THIS DATA-BLOCK\nimport bpy ; scat_data = bpy.data.texts['{name}'].scatter5\n# More info about this plugin on: 'www.geoscatter.com'\n\n\n                             ###########\n                          ##############\n                       #################\n                     ##############\n                    ##########\n                   #########   #########\n                  ########  ############\n                  ####### ##############\n                  ##################\n                  ###############\n                  ##############\n                  #############\n                  ########################\n                             #############\n                            ##############\n                           ###############\n                         #################\n                    ############## #######\n                    ############  ########\n                    #########    ########\n                              ##########\n                          #############\n                    #################\n                    ##############\n                    ###########")
        #t.use_fake_user = True #bpy.data.texts.new should set it to True by default
    return bpy.data.texts[name].scatter5

    #NOTE make sure to never use a PointerProperty pointing to this text, on any scatter-system or emitters, this textdata should stay unique for each blendfile. If importing an object, all Pointers will also be imported with it.

                                                                                                                  
# ooo        ooooo            o8o                   ooo        ooooo                 .o8              oooo                     
# `88.       .888'            `"'                   `88.       .888'                "888              `888                     
#  888b     d'888   .oooo.   oooo  ooo. .oo.         888b     d'888   .ooooo.   .oooo888  oooo  oooo   888   .ooooo.   .oooo.o 
#  8 Y88. .P  888  `P  )88b  `888  `888P"Y88b        8 Y88. .P  888  d88' `88b d88' `888  `888  `888   888  d88' `88b d88(  "8 
#  8  `888'   888   .oP"888   888   888   888        8  `888'   888  888   888 888   888   888   888   888  888ooo888 `"Y88b.  
#  8    Y     888  d8(  888   888   888   888        8    Y     888  888   888 888   888   888   888   888  888    .o o.  )88b 
# o8o        o888o `Y888""8o o888o o888o o888o      o8o        o888o `Y8bod8P' `Y8bod88P"  `V88V"V8P' o888o `Y8bod8P' 8""888P' 


import importlib

MODULE_NAMES = (
    "resources",
    "widgets",
    "manual",        
    "properties",
    "scattering",
    "curve",
    "procedural_vg", 
    "utils",
    "terrain",       
    "handlers",
    "ui",
    )

# Import the modules dynamically

MAIN_MODULES = []

for module_name in MODULE_NAMES:
    
    module = importlib.import_module(f".gpl_script.{module_name}", __package__)
    MAIN_MODULES.append(module)
    
    continue 


#   .oooooo.   oooo
#  d8P'  `Y8b  `888
# 888           888   .ooooo.   .oooo.   ooo. .oo.    .oooo.o  .ooooo.
# 888           888  d88' `88b `P  )88b  `888P"Y88b  d88(  "8 d88' `88b
# 888           888  888ooo888  .oP"888   888   888  `"Y88b.  888ooo888
# `88b    ooo   888  888    .o d8(  888   888   888  o.  )88b 888    .o
#  `Y8bood8P'  o888o `Y8bod8P' `Y888""8o o888o o888o 8""888P' `Y8bod8P'


def cleanse_modules():
    """remove all plugin modules from sys.modules, will load them again, creating an effective hit-reload soluton
    Not sure why blender is no doing this already whe disabling a plugin..."""
    #https://devtalk.blender.org/t/plugin-hot-reload-by-cleaning-sys-modules/20040

    import sys
    
    all_modules = sys.modules
    all_modules = dict(sorted(all_modules.items(),key= lambda x:x[0])) #sort them
    
    for k,v in all_modules.items():
        if k.startswith(__package__):
            del sys.modules[k]

    return None 


# ooooooooo.                         o8o               .
# `888   `Y88.                       `"'             .o8
#  888   .d88'  .ooooo.   .oooooooo oooo   .oooo.o .o888oo  .ooooo.  oooo d8b
#  888ooo88P'  d88' `88b 888' `88b  `888  d88(  "8   888   d88' `88b `888""8P
#  888`88b.    888ooo888 888   888   888  `"Y88b.    888   888ooo888  888
#  888  `88b.  888    .o `88bod8P'   888  o.  )88b   888 . 888    .o  888
# o888o  o888o `Y8bod8P' `8oooooo.  o888o 8""888P'   "888" `Y8bod8P' d888b
#                        d"     YD
#                        "Y88888P'


def register():

    try:
        for m in MAIN_MODULES:
            m.register()
            
    # very common user report, previously failed register, then user try to register again, and stumble into the first already registered class
    # we don't want them to report this specific error, it' useless and don't indicate the original error, most of the time we gently ask them to restart their session
    # Note that we could skip a class register if the class is already registered, however the initial activation process shouldn't be faulty at the first place
    
    except Exception as e:        
        if ("register_class(...): already registered as a subclass 'SCATTER5_OT_print_icon_id'" in str(e)):
            print(e)
            raise Exception("\n\nDear User,\nAre you using the correct version of blender with our plugin?\nAn error occured during this activation, it seems that a previous activation failed\nPlease restart blender and try again, Open the console window to see more Error messages.\n\n")
        raise e
    
    return None

def unregister():

    for m in reversed(MAIN_MODULES):
        m.unregister()

    # final step, remove modules from sys.modules 
    cleanse_modules()

    return None


#if __name__ == "__main__":
#    register()