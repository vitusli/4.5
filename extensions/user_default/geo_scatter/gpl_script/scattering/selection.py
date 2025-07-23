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
#  .oooooo..o           oooo                          .    o8o
# d8P'    `Y8           `888                        .o8    `"'
# Y88bo.       .ooooo.   888   .ooooo.   .ooooo.  .o888oo oooo   .ooooo.  ooo. .oo.
#  `"Y8888o.  d88' `88b  888  d88' `88b d88' `"Y8   888   `888  d88' `88b `888P"Y88b
#      `"Y88b 888ooo888  888  888ooo888 888         888    888  888   888  888   888
# oo     .d8P 888    .o  888  888    .o 888   .o8   888 .  888  888   888  888   888
# 8""88888P'  `Y8bod8P' o888o `Y8bod8P' `Y8bod8P'   "888" o888o `Y8bod8P' o888o o888o
#
#####################################################################################################


import bpy

from .. utils.event_utils import get_event
from .. utils . extra_utils import get_from_uid

from .. resources.icons import cust_icon
from .. translations import translate

from .. handlers.handlers import on_particle_interface_interaction_handler



def set_sel(psys,value):
    """batch set set all psy selection status""" #foreach_set() 'cound'nt access api for some reasons...
    for p in psys:
        p.sel = value
    return None



def on_particle_interface_interaction(self,context):
    """function that run when user set a particle system as active, used for shift&alt shortcut, also change selection"""

    #get latest active interface item
    itm = self.get_interface_active_item()

    #special case for psys, we have a handy p.active read-only property that we update on each list interaction
    if (itm is None): 
        for p in self.particle_systems:
            p.active = False
        return None 

    #get source itm, interface itm are fake, they are only useful to send back the original item, 
    #this item can either be a `emitter.scatter5.particle_groups[x]` or a `emitter.scatter5.particle_systems[x]`
    
    source_itm = itm.get_interface_item_source()
    
    if (source_itm is None):
        for p in self.particle_systems:
            p.active = False
        print(f"ERROR: on_particle_interface_interaction().get_interface_item_source() Returned None. User must've delete a scatter_obj? Interface is broken. itm={itm}",)
        return None
    
    elif (itm.interface_item_type=='GROUP_SYSTEM'):
        for p in self.particle_systems:
            p.active = False

    elif (itm.interface_item_type=='SCATTER_SYSTEM'):
        for p in self.particle_systems:
            p.active = (p.name==source_itm.name)

    #then we change selection or hide_viewport status automatically, if psy or group is not linked
    
    #get event for shortcut support
    event = get_event()
            
    #setting an itm as active will always trigger the reset of the selection, except if pressing shifts
    if (not event.shift):
        set_sel(self.particle_systems,False,)

    #auto set active 
    match itm.interface_item_type:
        
        case 'SCATTER_SYSTEM': #if active itm psy, if we set active a psy item, always set sel the psy active
            p = source_itm
            p.sel = True

        case 'GROUP_SYSTEM': #selection shortcuts if active itm is group! if we set active a group item, always set sel all psys members 
            g = source_itm
            gpsys = g.get_psy_members()
            set_sel(gpsys, True)

    #alt support = we hide anything that is not selected
    if (event.alt):
        with bpy.context.scene.scatter5.factory_update_pause(event=True,delay=True,sync=True):
            for p in self.particle_systems:
                p.hide_viewport = not p.sel
                continue

    #run handler function on each system list interaction
    on_particle_interface_interaction_handler()

    return None 


class SCATTER5_OT_toggle_selection(bpy.types.Operator):
    """toggle select all"""
    bl_idname      = "scatter5.toggle_selection"
    bl_label       = translate("Scatter-System(s) Selection Toggle")
    bl_description = ""

    emitter_name : bpy.props.StringProperty()
    group_name : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    select : bpy.props.BoolProperty(default=False, options={"SKIP_SAVE",},)
    deselect : bpy.props.BoolProperty(default=False, options={"SKIP_SAVE",},)

    @classmethod
    def description(cls, context, properties): 
        return translate("Select/Deselect Every System(s)") if properties.group_name=="" else translate("Select/Deselect group system(s)")

    @classmethod
    def poll(cls, context):
        return (bpy.context.scene.scatter5.emitter != None)

    def execute(self, context):

        #find emitter object 
        if (self.emitter_name==""):
              emitter = bpy.context.scene.scatter5.emitter
        else: emitter = bpy.data.objects.get(self.emitter_name)

        #specified a group name? if not use all psys, else use all psys of group
        if (self.group_name==""):
              psys = emitter.scatter5.particle_systems[:]
        else: psys = [p for p in emitter.scatter5.particle_systems if p.group==self.group_name]

        #Select All?
        if (self.select==True):
            set_sel(psys,True)

        #Deselect All?
        elif (self.deselect==True):
            set_sel(psys,False)

        #if neither then Toggle automatically 
        else:
            if (False in set(p.sel for p in psys)):
                  set_sel(psys,True)
            else: set_sel(psys,False)

        return {'FINISHED'}


class SCATTER5_OT_select_object(bpy.types.Operator):
    """Select/Deselect an object"""

    bl_idname      = "scatter5.select_object"
    bl_label       = translate("Selection")
    bl_description = translate("Select/Deselect this object.\n• Use the 'SHIFT' key while clicking to select many\n• Use the 'ALT' key while clicking to recenter the viewport toward object\n• Use 'ALT-SHIFT' for both")

    obj_session_uid : bpy.props.IntProperty()
    coll_name : bpy.props.StringProperty()

    def invoke(self, context, event):

        #Object do not exists?
        obj = get_from_uid(self.obj_session_uid)
        if (obj is None):
            return {'FINISHED'}

        #Object Not in scene? 
        if (obj not in bpy.context.scene.objects[:]):
            bpy.ops.scatter5.popup_menu(msgs=translate("Object is not in scene"),title=translate("Action Not Possible"),icon="ERROR",)
            return {'FINISHED'}

        #Object hidden in viewlayer?
        if (obj not in bpy.context.view_layer.objects[:]):
            #try to unhide from collection ?
            if (self.coll_name):
                _self = self
                def draw(self, context):
                    nonlocal _self #access arg from new fct namespace
                    self.layout.operator("scatter5.exec_line",text=translate("Unhide Viewlayer Collection")).api = f"set_collection_view_layers_exclude(D.collections['{_self.coll_name}'], scenes=[C.scene], hide=False,) ; o=get_from_uid({_self.obj_session_uid}) ; C.view_layer.objects.active=o ; o.select_set(True)"
                    return 
                context.window_manager.popup_menu(draw, title=translate("Object is in Hidden Viewlayer"))
                return {'FINISHED'}    
            bpy.ops.scatter5.popup_menu(msgs=translate("Object is not in Viewlayer"),title=translate("Selection Impossible"),icon="ERROR",)
            return {'FINISHED'}

        def deselect_all():
            for o in bpy.context.selected_objects:
                o.select_set(state=False)

        #event shift+alt click
        if (event.shift and event.alt):
            bpy.context.view_layer.objects.active = obj
            obj.select_set(state=True)
            bpy.ops.view3d.view_selected()

        #event shift click
        elif (event.shift):
            bpy.context.view_layer.objects.active = obj
            obj.select_set(state=True)

        #event alt click
        elif (event.alt):
            deselect_all()
            bpy.context.view_layer.objects.active = obj
            obj.select_set(state=True)
            bpy.ops.view3d.view_selected()

        #event normal
        else:
            deselect_all()
            bpy.context.view_layer.objects.active = obj
            obj.select_set(state=True)

        return {'FINISHED'}



#   .oooooo.   oooo
#  d8P'  `Y8b  `888
# 888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
# 888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
# 888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
# `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#  `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'



classes = (

    SCATTER5_OT_toggle_selection,
    SCATTER5_OT_select_object,
    
    )



#if __name__ == "__main__":
#    register()