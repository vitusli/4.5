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
# ooooooooo.
# `888   `Y88.
#  888   .d88'  .ooooo.  ooo. .oo.  .oo.    .ooooo.  oooo    ooo  .ooooo.
#  888ooo88P'  d88' `88b `888P"Y88bP"Y88b  d88' `88b  `88.  .8'  d88' `88b
#  888`88b.    888ooo888  888   888   888  888   888   `88..8'   888ooo888
#  888  `88b.  888    .o  888   888   888  888   888    `888'    888    .o
# o888o  o888o `Y8bod8P' o888o o888o o888o `Y8bod8P'     `8'     `Y8bod8P'
#
#####################################################################################################

import bpy 

from .. resources.icons import cust_icon
from .. translations import translate



class SCATTER5_OT_remove_system(bpy.types.Operator):
    """Remove the selected particle system(s)"""
    
    bl_idname      = "scatter5.remove_system" #this operator is stupid, prefer to use `p.remove_psy()`
    bl_label       = translate("Remove Scatter-System(s)")
    bl_description = ""

    emitter_name : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},) #mandatory argument
    scene_name : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},) #facultative, will override emitter

    method : bpy.props.StringProperty(default="selection", options={"SKIP_SAVE",},)  #mandatory argument in: selection|active|name|clear|group|dynamic_uilist
    name : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},) #only if method is name or group
    undo_push : bpy.props.BoolProperty(default=True, options={"SKIP_SAVE",},) 
    #TODO rework by name, pass uid or something
    
    @classmethod
    def description(cls, context, properties): 
        if (properties.method=="dynamic_uilist"):
            return translate("•By default, remove the active scatter-system or active group.\n•If pressing the 'ALT' key while clicking on the remove button, remove all selected system(s) simultaneously")
        elif (properties.scene_name!=""):
            if (properties.method=="clear"):
                translate("Remove all scatter-system(s) from this scene")
            return translate("Remove the scatter-system(s) from this scene")
        elif (properties.method=="selection"):
            return translate("Remove the selected scatter-system(s) simultaneously")
        elif (properties.method=="clear"):
            return translate("Remove all scatter-system(s) from this emitter")
        return ""

    def invoke(self, context, event):
        """only used if alt behavior == automatic selection|active"""

        if (self.method=="dynamic_uilist"):

            emitter      = bpy.data.objects[self.emitter_name]
            psy_active   = emitter.scatter5.get_psy_active()
            group_active = emitter.scatter5.get_group_active()
            
            if (event.alt):
                self.method = "selection"

            elif (group_active is not None):
                self.method = "group"
                self.name = group_active.name

            elif (psy_active is not None):
                self.method = "active"

        return self.execute(context)

    def execute(self, context):
            
        scat_scene = context.scene.scatter5

        if (self.scene_name!=""):
              psys = scat_scene.get_all_psys(search_mode="active_view_layer")
        else: psys = bpy.data.objects[self.emitter_name].scatter5.particle_systems

        # #save selection, this operation might f up sel
        # save_sel = [p.name for p in emitter.scatter5.get_psys_selected() if p.sel]

        #define what to del
        #need to remove by name as memory adress will keep changing, else might create crash
        to_del = []

        match self.method:
            case 'selection': #remove selection?
                to_del = [p.name for p in psys if p.sel]
            case 'active': #remove active?
                to_del = [p.name for p in psys if p.active]
            case 'name': #remove by name?
                to_del = [p.name for p in psys if (p.name==self.name)]
            case 'group': #remove whole group members?
                to_del = [p.name for p in psys if (p.group==self.name)]
            case 'clear': #remove everything?
                to_del = [p.name for p in psys]
            case _:
                raise Exception(f"ERROR: SCATTER5_OT_remove_system: Wrong str 'method' passed {self.method}, must be in 'selection|active|name|group|clear'")
        
        #cancel if nothing to remove 
        if (len(to_del)==0): 
            return {'FINISHED'}

        #remove each psy, pause user keyboard event listenting
        with context.scene.scatter5.factory_update_pause(event=True):
            
            #keep track of the emitters, in order to refresh their interfaces
            affected_emitters = set()
            
            for x in to_del:
                
                #we remove psys by name, otherwise will cause issues
                psy = scat_scene.get_psy_by_name(x)
                psy.remove_psy()
                
                #retain emitter, we need to refresh their interfaces
                emitter = psy.id_data
                affected_emitters.add(emitter)
                    
                continue

            #rebuild system-list interface, will take care of active index
            for e in affected_emitters:
                e.scatter5.particle_interface_refresh()
                continue
        
        # #restore selection ?
        # [setattr(p,"sel",p.name in save_sel) for p in emitter.scatter5.particle_systems]

        #UNDO_PUSH
        if (self.undo_push):
            bpy.ops.ed.undo_push(message=translate("Remove Scatter-System(s)"))

        return {'FINISHED'}



#   .oooooo.   oooo
#  d8P'  `Y8b  `888
# 888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
# 888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
# 888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
# `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#  `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'



classes = (

    SCATTER5_OT_remove_system,
    
    )



#if __name__ == "__main__":
#    register()