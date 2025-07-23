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
# ooooo                          .
# `888'                        .o8
#  888  ooo. .oo.    .oooo.o .o888oo  .oooo.   ooo. .oo.    .ooooo.   .ooooo.   .oooo.o
#  888  `888P"Y88b  d88(  "8   888   `P  )88b  `888P"Y88b  d88' `"Y8 d88' `88b d88(  "8
#  888   888   888  `"Y88b.    888    .oP"888   888   888  888       888ooo888 `"Y88b.
#  888   888   888  o.  )88b   888 . d8(  888   888   888  888   .o8 888    .o o.  )88b
# o888o o888o o888o 8""888P'   "888" `Y888""8o o888o o888o `Y8bod8P' `Y8bod8P' 8""888P'
#
#####################################################################################################


import bpy

from .. utils.event_utils import get_event
from .. translations import translate
from .. utils.import_utils import import_selected_assets


# oooooooooooo                                       .    o8o
# `888'     `8                                     .o8    `"'
#  888         oooo  oooo  ooo. .oo.    .ooooo.  .o888oo oooo   .ooooo.  ooo. .oo.
#  888oooo8    `888  `888  `888P"Y88b  d88' `"Y8   888   `888  d88' `88b `888P"Y88b
#  888    "     888   888   888   888  888         888    888  888   888  888   888
#  888          888   888   888   888  888   .o8   888 .  888  888   888  888   888
# o888o         `V88V"V8P' o888o o888o `Y8bod8P'   "888" o888o `Y8bod8P' o888o o888o


def collection_users(collection, setting_name="s_instances_coll_ptr"):
    """return all scatter5 psy that use this collection as s_instances_coll_ptr"""

    users = set()
    
    for p in bpy.context.scene.scatter5.get_all_psys(search_mode="all", also_linked=True):
        if (getattr(p,setting_name)==collection):
            users.add(p)
        continue
    
    return list(users)

def is_compatible_instance(o, emitter=None,):
    """check if object compatible to be scattered"""

    #get emitter 
    if (emitter is None):
        emitter = bpy.context.scene.scatter5.emitter

    #emitter needs to exists!
    if (emitter is None):
        return False

    #cannot be active emitter
    if (o==emitter):
        return False

    #cannot be an emitter
    #ok?

    #cannot be a surface object?
    #ok?

    #cannot be a scatter object
    if (o.scatter5.is_scatter_obj):
        return False

    #un-supported meshes?
    if (o.type not in ('MESH','CURVE','LIGHT','LIGHT_PROBE','VOLUME','EMPTY','FONT','META','SURFACE')):
        return False

    return True 

def find_compatible_instances(obj_list, emitter=None,):
    """return a generator of compatible object"""

    for o in obj_list:
        if is_compatible_instance(o, emitter=emitter):
            yield o


# ooooo                          .                                    o8o                                .oooooo.                                               .
# `888'                        .o8                                    `"'                               d8P'  `Y8b                                            .o8
#  888  ooo. .oo.    .oooo.o .o888oo  .oooo.   ooo. .oo.    .ooooo.  oooo  ooo. .oo.    .oooooooo      888      888 oo.ooooo.   .ooooo.  oooo d8b  .oooo.   .o888oo  .ooooo.  oooo d8b  .oooo.o
#  888  `888P"Y88b  d88(  "8   888   `P  )88b  `888P"Y88b  d88' `"Y8 `888  `888P"Y88b  888' `88b       888      888  888' `88b d88' `88b `888""8P `P  )88b    888   d88' `88b `888""8P d88(  "8
#  888   888   888  `"Y88b.    888    .oP"888   888   888  888        888   888   888  888   888       888      888  888   888 888ooo888  888      .oP"888    888   888   888  888     `"Y88b.
#  888   888   888  o.  )88b   888 . d8(  888   888   888  888   .o8  888   888   888  `88bod8P'       `88b    d88'  888   888 888    .o  888     d8(  888    888 . 888   888  888     o.  )88b
# o888o o888o o888o 8""888P'   "888" `Y888""8o o888o o888o `Y8bod8P' o888o o888o o888o `8oooooo.        `Y8bood8P'   888bod8P' `Y8bod8P' d888b    `Y888""8o   "888" `Y8bod8P' d888b    8""888P'
#                                                                                      d"     YD                     888
#                                                                                      "Y88888P'                    o888o


class SCATTER5_OT_add_instances(bpy.types.Operator):
    """operator only for the insance list context"""

    bl_idname = "scatter5.add_instances"
    bl_label       = translate("Add New Instances")
    bl_description = translate("Add the selected objects of the 3D viewport or of your asset-browser to your scatter system instance collection.\n• Press 'ALT' to add to it to all collections lists of all selected scatter-system simultaneously")
    bl_options     = {'INTERNAL','UNDO'}

    method : bpy.props.EnumProperty(
        name=translate("Add from"),
        default="viewport",
        items=(("viewport", translate("Viewport Selection"), translate("Add the selected compatible objects found in the viewport"), "VIEW3D",1 ),
               ("browser", translate("Browser Selection"), translate("Add the selected object found in the asset browser"), "ASSET_MANAGER",2 ),
              ),
        )

    def execute(self, context):

        from ... __init__ import blend_prefs
        scat_data  = blend_prefs()
        scat_scene = bpy.context.scene.scatter5
        emitter    = scat_scene.emitter
        psy_active = emitter.scatter5.get_psy_active()
        psys_sel   = emitter.scatter5.get_psys_selected(all_emitters=scat_data.factory_alt_selection_method=="all_emitters")

        event = get_event(nullevent=not scat_data.factory_alt_allow)

        match self.method:
            case 'browser':  obj_list = import_selected_assets(link=(scat_data.objects_import_method=="LINK"),)
            case 'viewport': obj_list = bpy.context.selected_objects 
        
        instances = list(find_compatible_instances(obj_list, emitter=emitter,))
             
        if (len(instances)==0):
            msg = translate("No valid object(s) found in selection.") if (not self.method=="browser") else translate("No asset(s) found in asset-browser.")
            bpy.ops.scatter5.popup_menu(msgs=msg, title=translate("Warning"),icon="ERROR",)
            return {'FINISHED'}

        if (event.alt):  
              colls = [p.s_instances_coll_ptr for p in psys_sel]
        else: colls = [psy_active.s_instances_coll_ptr]

        for coll in colls:
            
            if (not coll):
                continue
            
            o = None
            for o in instances:
                if (o.name not in coll.objects):
                    coll.objects.link(o)

            #refresh signal
            if (o):
                oldval = o.display_type
                o.display_type = 'BOUNDS'
                o.display_type = oldval
                
            continue

        return {'FINISHED'}


class SCATTER5_OT_remove_instances(bpy.types.Operator):
    """operator only for the insance list context"""

    bl_idname = "scatter5.remove_instances"
    bl_label       = translate("Remove this instance")
    bl_description = translate("Remove this instance from your instance collection list.\n• Press 'ALT' to simulaneously remove this instance from all instance lists of all selected system(s)")
    bl_options     = {'INTERNAL','UNDO'}

    obj_session_uid : bpy.props.IntProperty()
        
    def execute(self, context):

        from ... __init__ import blend_prefs
        scat_data  = blend_prefs()
        scat_scene = bpy.context.scene.scatter5
        emitter    = scat_scene.emitter
        psy_active = emitter.scatter5.get_psy_active()
        psys_sel   = emitter.scatter5.get_psys_selected(all_emitters=scat_data.factory_alt_selection_method=="all_emitters")

        event = get_event(nullevent=not scat_data.factory_alt_allow)
        
        if (event.alt):  
              colls = [p.s_instances_coll_ptr for p in psys_sel]
        else: colls = [psy_active.s_instances_coll_ptr]

        for coll in colls:
            
            if (not coll):
                continue
            
            o = None
            for o in coll.objects:
                if (o.session_uid==self.obj_session_uid):
                    coll.objects.unlink(o)
            
            #refresh signal
            if (o):
                oldval = o.display_type
                o.display_type = 'BOUNDS'
                o.display_type = oldval
            
            continue

        return {'FINISHED'}


#   .oooooo.   oooo
#  d8P'  `Y8b  `888
# 888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
# 888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
# 888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
# `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#  `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'


classes = (

    SCATTER5_OT_add_instances,
    SCATTER5_OT_remove_instances,
    
    )