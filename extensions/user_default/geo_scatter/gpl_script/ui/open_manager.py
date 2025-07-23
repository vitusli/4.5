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

################################################################################################
#   .oooooo.                                         ooo        ooooo
#  d8P'  `Y8b                                        `88.       .888'
# 888      888 oo.ooooo.   .ooooo.  ooo. .oo.         888b     d'888   .oooo.   ooo. .oo.    .oooo.    .oooooooo  .ooooo.  oooo d8b
# 888      888  888' `88b d88' `88b `888P"Y88b        8 Y88. .P  888  `P  )88b  `888P"Y88b  `P  )88b  888' `88b  d88' `88b `888""8P
# 888      888  888   888 888ooo888  888   888        8  `888'   888   .oP"888   888   888   .oP"888  888   888  888ooo888  888
# `88b    d88'  888   888 888    .o  888   888        8    Y     888  d8(  888   888   888  d8(  888  `88bod8P'  888    .o  888
#  `Y8bood8P'   888bod8P' `Y8bod8P' o888o o888o      o8o        o888o `Y888""8o o888o o888o `Y888""8o `8oooooo.  `Y8bod8P' d888b
#               888                                                                                   d"     YD
#              o888o                                                                                  "Y88888P'
################################################################################################


import bpy

import platform
import os
import ctypes


class SCATTER5_OT_open_editor(bpy.types.Operator):

    bl_idname      = "scatter5.open_editor"
    bl_label       = ""
    bl_description = ""

    editor_type : bpy.props.StringProperty(default="", options={"SKIP_SAVE"},)
    instructions : bpy.props.StringProperty(default="", options={"SKIP_SAVE"},)
    description : bpy.props.StringProperty()

    @classmethod
    def description(cls, context, properties): 
        return properties.description

    @staticmethod
    def set_window(size=(100,100),):
        
        if (platform.system()=="Windows"):

            SWP_NOMOVE = 0x0002

            ctypes.windll.user32.SetWindowPos(
                ctypes.windll.user32.GetActiveWindow(), 
                0,
                0,
                0,
                size[0],
                size[1],
                SWP_NOMOVE,
                )

        return None

    def execute(self, context):

        from ... __init__ import addon_prefs
        from .. utils.extra_utils import exec_line

        #define convenience vars for execution
        wm = bpy.context.window_manager
        scat_win = wm.scatter5

        #first we search across all users windows, & see if there's an editor available we can simply use instead of opening a new window ect..
        for w in wm.windows:
            if (not w.screen.is_temporary):
                for a in w.screen.areas: 
                    if (a.ui_type==self.editor_type):
                        #we found an area with the editor we need, then we simply need to do the necessary step to maybe transform this space into something else (ex a prefs into a geo-scatter manager)
                        window, screen, area = w, w.screen, a #convenience vars for execution
                        exec_line(self.instructions, local_vars=locals(),)
                        return {'FINISHED'}

        #okay, if we are here, we didn't find any areas in any user windows that already has our editor, so we'll dupplicate top left corner area into it's own window
        curwin = bpy.context.window
        curwindim = curwin.width, curwin.height
        
        area_candidates = {a.y:a for a in curwin.screen.areas if (a.x==0)} #get all areas on extreme left
        area_candidates = dict(sorted(area_candidates.items())) #sort by lower y loc values first so we get top left
        area_found = list(area_candidates.values())[-1] #biggest value to get top editor

        #dupplicate area to window
        with context.temp_override(window=curwin, screen=curwin.screen, area=area_found):
            bpy.ops.screen.area_dupli('INVOKE_DEFAULT')

        #define convenience variables for exec
        window = wm.windows[-1] #get new window, we just duplicated a new one, should be the newest on top of the stack, no?
        screen = window.screen
        area = screen.areas[0] #we duplicated an area, so it should create a window with a single area
        
        #change editor type
        area.ui_type = self.editor_type

        #change window size, for now only window OS is supported
        window_size = ( int(curwindim[0]/4), int(curwindim[1]) )
        self.set_window(size=window_size,)

        exec_line(self.instructions, local_vars=locals(),)

        return {'FINISHED'}



classes = (

    SCATTER5_OT_open_editor,    

    )