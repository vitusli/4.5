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
#  ooooo     ooo ooooo
#  `888'     `8' `888'
#   888       8   888
#   888       8   888
#   888       8   888
#   `88.    .8'   888
#     `YbodP'    o888o
#
#####################################################################################################


import bpy

from . import ui_templates 
from . import ui_menus
from . import ui_system_list
from . import ui_creation
from . import ui_notification
from . import ui_tweaking
from . import ui_extra
from . import ui_emitter_select
from . import ui_addon
from . import ui_manual
from . import ui_biome_library
from . import open_manager


#   ooooooooo.
#   `888   `Y88.
#    888   .d88'  .ooooo.   .oooooooo
#    888ooo88P'  d88' `88b 888' `88b
#    888`88b.    888ooo888 888   888
#    888  `88b.  888    .o `88bod8P'
#   o888o  o888o `Y8bod8P' `8oooooo.
#                          d"     YD
#                          "Y88888P'

classes  =  []
classes +=  ui_menus.classes
classes +=  ui_system_list.classes
classes +=  ui_creation.classes
classes +=  ui_notification.classes
classes +=  ui_tweaking.classes
classes +=  ui_extra.classes
classes +=  ui_emitter_select.classes
classes +=  ui_addon.classes
classes +=  ui_manual.classes
classes +=  ui_biome_library.classes
classes +=  open_manager.classes

#classes possessing "USER_DEFINED bl_category", will be dynamically reloaded
USER_TABS_CLS = [cls for cls in classes if hasattr(cls,'bl_category') and (cls.bl_category=='USER_DEFINED')]


def register():

    #patch class with user defined category
    from ... __init__ import addon_prefs
    for cls in USER_TABS_CLS: 
        cls.bl_category = addon_prefs().tab_name

    for cls in classes:
        bpy.utils.register_class(cls)

    #register biome library previews, build strucure, online fetch..
    ui_biome_library.register()

    #register shortcuts
    ui_system_list.register_quicklister_shortcuts()

    return 


def unregister():

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    #register biome library previews, build strucure, online fetch..
    ui_biome_library.unregister()

    #unregister shortcuts
    ui_system_list.unregister_quicklister_shortcuts()

    return



#if __name__ == "__main__":
#    register()