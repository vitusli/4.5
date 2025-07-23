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
# ooooooooo.                       oooo                              o8o
# `888   `Y88.                     `888                              `"'
#  888   .d88'  .oooo.    .ooooo.   888  oooo   .oooo.    .oooooooo oooo  ooo. .oo.    .oooooooo
#  888ooo88P'  `P  )88b  d88' `"Y8  888 .8P'   `P  )88b  888' `88b  `888  `888P"Y88b  888' `88b
#  888          .oP"888  888        888888.     .oP"888  888   888   888   888   888  888   888
#  888         d8(  888  888   .o8  888 `88b.  d8(  888  `88bod8P'   888   888   888  `88bod8P'
# o888o        `Y888""8o `Y8bod8P' o888o o888o `Y888""8o `8oooooo.  o888o o888o o888o `8oooooo.
#                                                        d"     YD                    d"     YD
#                                                        "Y88888P'                    "Y88888P'
################################################################################################


import bpy

import os
import zipfile

from . import directories
from .. translations import translate


# oooooooooooo               .
# `888'     `8             .o8
#  888          .ooooo.  .o888oo  .oooo.o
#  888oooo8    d88' `"Y8   888   d88(  "8
#  888    "    888         888   `"Y88b.
#  888         888   .o8   888 . o.  )88b
# o888o        `Y8bod8P'   "888" 8""888P'


def unzip_in_location(zip_path, unpack_path,):
    """unzip given zip file"""

    with zipfile.ZipFile(zip_path, 'r') as z:
        z.extractall(unpack_path)

    return None


def blend_in_zip(zip_path):
    """check if there are .blends in this zip"""

    with zipfile.ZipFile(zip_path, 'r') as z:
        for info in z.infolist():
            if (".blend" in info.filename):
                return True

    return False

#                                         .                                  oooo
#                                       .o8                                  `888
#         .oooo.o  .ooooo.   .oooo.   .o888oo oo.ooooo.   .oooo.    .ooooo.   888  oooo
#        d88(  "8 d88' `"Y8 `P  )88b    888    888' `88b `P  )88b  d88' `"Y8  888 .8P'
#        `"Y88b.  888        .oP"888    888    888   888  .oP"888  888        888888.
#  .o.   o.  )88b 888   .o8 d8(  888    888 .  888   888 d8(  888  888   .o8  888 `88b.
#  Y8P   8""888P' `Y8bod8P' `Y888""8o   "888"  888bod8P' `Y888""8o `Y8bod8P' o888o o888o
#                                              888
#                                             o888o



class SCATTER5_OT_install_package(bpy.types.Operator):

    bl_idname      = "scatter5.install_package"
    bl_label       = translate("Install a .scaptack")
    bl_description = translate("Install a given .scatpack archive file in your scatter library")
    bl_options     = {'INTERNAL'}

    filepath : bpy.props.StringProperty(subtype="FILE_PATH", options={'SKIP_SAVE'},)
    popup_menu : bpy.props.BoolProperty(default=True, options={"SKIP_SAVE","HIDDEN"},)

    def invoke(self, context, event):
        if (self.filepath):
            return self.execute(context)
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
            
        #assertions
        
        if (not self.filepath.endswith(".scatpack")):
            if (self.popup_menu):
                bpy.ops.scatter5.popup_dialog(
                    'INVOKE_DEFAULT',
                    msg=translate("Selected file is not in the '.scatpack' format"),
                    header_title=translate("Error!"),
                    header_icon="ERROR",
                    )
            else:
                print("ERROR: scatter5.install_package(): Selected file is not in the '.scatpack' format")
            return {'FINISHED'}
        
        if (not os.path.exists(self.filepath)):
            if (self.popup_menu):
                bpy.ops.scatter5.popup_dialog(
                    'INVOKE_DEFAULT',
                    msg=translate("Selected filepath does not exists"),
                    header_title=translate("Error!"),
                    header_icon="ERROR",
                    )
            else:
                print("ERROR: scatter5.install_package(): Selected filepath does not exists")
            return {'FINISHED'}  
            
        #check if creator of .scatpack is dummy or scatpack relying on external library
        
        with zipfile.ZipFile( self.filepath , 'r') as z:
            IsBlend = False
            IsCorrect = False
            for p in z.namelist():
                if p.startswith(("_presets_","_biomes_","_bitmaps_")):
                    IsCorrect = True 
                if ( p.endswith(".blend") ):
                    IsBlend = True
                continue
        
        if (IsCorrect==False):
            if (self.popup_menu):
                bpy.ops.scatter5.popup_dialog(
                    'INVOKE_DEFAULT',
                    msg=translate("your '.scatpack' structure is wrong, it doesn't contain a '_presets_' nor '_biomes_' folder on first level"),
                    header_title=translate("Error!"),
                    header_icon="ERROR",
                    )
            else:
                print("ERROR: scatter5.install_package(): Your '.scatpack' structure is wrong, it doesn't contain a '_presets_' nor '_biomes_' folder on first level")
            return {'FINISHED'} 

        #install .scatpack

        unzip_in_location(self.filepath, directories.lib_library)

        #reload all libs

        bpy.ops.scatter5.reload_biome_library()
        bpy.ops.scatter5.reload_preset_gallery()

        #Great Success!

        if (self.popup_menu):

            match IsBlend:
                case False:
                    bpy.ops.scatter5.popup_dialog(
                        'INVOKE_DEFAULT',
                        msg=translate("Congratulation, everything installed correctly!\n\nNote that no '.blend' files are contained in this scatpack.\n\nYou might need to add a new library in your blender asset browser! Our plugin automatically searches for the assets it needs in your asset-browser, or in the custom paths you can specify in the plugin settings."),
                        header_title=translate("Successful Scatpack Install"),
                        header_icon="CHECKMARK",
                        )
                case True:
                    bpy.ops.scatter5.popup_dialog(
                        'INVOKE_DEFAULT',
                        msg=translate("Congratulation, everything installed correctly!\n\nNote that a '.blend' file is contained in this scatpack. Our plugin will use the assets of this file."),
                        header_title=translate("Successful Scatpack Install"),
                        header_icon="CHECKMARK",
                        )

        return {'FINISHED'}
 

class SCATTER_FH_scatpack_drag_drop(bpy.types.FileHandler):
    """.scaptack drag and drop support"""
    
    bl_idname = "SCATTER_FH_scatpack_drag_drop"
    bl_label   = translate("File handler for .spatpack installation")
    
    bl_import_operator = "scatter5.install_package"
    bl_file_extensions = ".scatpack"

    @classmethod
    def poll_drop(cls, context):
        return True #support all kind of area of blender
    
    
classes = (

    SCATTER5_OT_install_package,
    SCATTER_FH_scatpack_drag_drop,

    )
