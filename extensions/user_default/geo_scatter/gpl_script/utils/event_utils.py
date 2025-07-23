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

#   .oooooo.                  .        oooooooooooo                                       .
#  d8P'  `Y8b               .o8        `888'     `8                                     .o8
# 888            .ooooo.  .o888oo       888         oooo    ooo  .ooooo.  ooo. .oo.   .o888oo
# 888           d88' `88b   888         888oooo8     `88.  .8'  d88' `88b `888P"Y88b    888
# 888     ooooo 888ooo888   888         888    "      `88..8'   888ooo888  888   888    888
# `88.    .88'  888    .o   888 .       888       o    `888'    888    .o  888   888    888 .
#  `Y8bood8P'   `Y8bod8P'   "888"      o888ooooood8     `8'     `Y8bod8P' o888o o888o   "888"


# get_even() Hack to get even from non modal nor invoke

#https://blender.stackexchange.com/questions/211544/detect-user-event-bpy-types-event-anywhere-from-blender/211590#211590

class EventCopy():
    """empty event class, only use by singleton"""

    #imitate bpy.type.Event used attributes 

    def __init__(self):

        self.type = ""
        self.value = ""
        self.shift = False
        self.ctrl = False
        self.alt = False

    def update(self, event=None):
        
        #construct man-made event
        if (event is None):
            self.type = ""
            self.value = ""
            self.shift = False
            self.ctrl = False
            self.alt = False

        #or copy from existing blender event type
        else: 
            self.type = event.type
            self.value = event.value
            self.shift = event.shift
            self.ctrl = event.ctrl
            self.alt = event.alt

#Event Singleton

EVENT = EventCopy() 

#Get update value via operator as bpy.types.Event only accessible from invoke() or modal()

class SCATTER5_OT_get_event(bpy.types.Operator):
    """update event singleton, this is an internal operator"""

    bl_idname  = "scatter5.get_event"
    bl_label   = ""

    def invoke(self, context, event):
        
        global EVENT
        EVENT.update(event=event)

        return {'FINISHED'}
    
#access event singleton from all modules based on the 

def get_event(nullevent=False):
    """get rebuilt Event type via bpy.types.Operator invoke()"""

    from ... __init__ import blend_prefs
    scat_data = blend_prefs()
    
    global EVENT 

    if ((not scat_data.factory_event_listening_allow) or (bpy.app.background) or (bpy.context.window is None) or (nullevent==True)):
        EVENT.update(event=None)
    else:
        bpy.ops.scatter5.get_event('INVOKE_DEFAULT')

    return EVENT

# ooo        ooooo                                                 .oooooo.                             .                             .
# `88.       .888'                                                d8P'  `Y8b                          .o8                           .o8
#  888b     d'888   .ooooo.  oooo  oooo   .oooo.o  .ooooo.       888           .ooooo.  ooo. .oo.   .o888oo  .ooooo.  oooo    ooo .o888oo
#  8 Y88. .P  888  d88' `88b `888  `888  d88(  "8 d88' `88b      888          d88' `88b `888P"Y88b    888   d88' `88b  `88b..8P'    888
#  8  `888'   888  888   888  888   888  `"Y88b.  888ooo888      888          888   888  888   888    888   888ooo888    Y888'      888
#  8    Y     888  888   888  888   888  o.  )88b 888    .o      `88b    ooo  888   888  888   888    888 . 888    .o  .o8"'88b     888 .
# o8o        o888o `Y8bod8P'  `V88V"V8P' 8""888P' `Y8bod8P'       `Y8bood8P'  `Y8bod8P' o888o o888o   "888" `Y8bod8P' o88'   888o   "888"

    
#FAIL??? goal is to get correct context from modal

CONTEXT = {}

class SCATTER5_OT_get_mouse_context(bpy.types.Operator):
    """update event singleton, this is an internal operator"""

    bl_idname  = "scatter5.get_mouse_context"
    bl_label   = ""

    def invoke(self, context, event):
        
        global CONTEXT
        CONTEXT.update({"area_type":bpy.context.area.type})

        return {'FINISHED'}

def get_mouse_context():
    """get rebuilt Event type via bpy.types.Operator invoke()"""
        
    global CONTEXT 

    bpy.ops.scatter5.get_mouse_context('INVOKE_DEFAULT')

    return CONTEXT


#   .oooooo.   oooo
#  d8P'  `Y8b  `888
# 888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
# 888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
# 888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
# `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#  `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'


classes = (

    SCATTER5_OT_get_event,
    SCATTER5_OT_get_mouse_context,

    )