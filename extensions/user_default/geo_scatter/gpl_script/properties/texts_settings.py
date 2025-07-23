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
# ooooooooooooo                 .         .oooooo..o               .       .    o8o                                  
# 8'   888   `8               .o8        d8P'    `Y8             .o8     .o8    `"'                                  
#      888      oooo    ooo .o888oo      Y88bo.       .ooooo.  .o888oo .o888oo oooo  ooo. .oo.    .oooooooo  .oooo.o 
#      888       `88b..8P'    888         `"Y8888o.  d88' `88b   888     888   `888  `888P"Y88b  888' `88b  d88(  "8 
#      888         Y888'      888             `"Y88b 888ooo888   888     888    888   888   888  888   888  `"Y88b.  
#      888       .o8"'88b     888 .      oo     .d8P 888    .o   888 .   888 .  888   888   888  `88bod8P'  o.  )88b 
#     o888o     o88'   888o   "888"      8""88888P'  `Y8bod8P'   "888"   "888" o888o o888o o888o `8oooooo.  8""888P' 
#                                                                                                d"     YD           
#                                                                                                "Y88888P'                                                                                                                                        
######################################################################################################

import bpy

from .. utils.extra_utils import dprint
from .. utils.math_utils import generate_uuid_int
from .. translations import translate

from .. scattering.synchronize import SCATTER5_PR_sync_channels
from .. scattering import update_factory


######################################################################################################


class SCATTER5_PR_uuids_repository(bpy.types.PropertyGroup): 
    """uuids = blend_prefs().uuids_repository[i]"""
    
    name : bpy.props.StringProperty()
    uuid : bpy.props.IntProperty()
    ptr : bpy.props.PointerProperty(type=bpy.types.ID) #So far only used for objects type


def get_blendfile_uuid(self):
    """generate uuid once on first read"""

    if (not self.blendfile_uuid_initialized):
        dprint(f"REPORT: UuidInitialization: blend_prefs().blendfile_uuid")
        
        #generate uuid & set initialization status
        self.blendfile_uuid_private = generate_uuid_int(existing_uuids=list(set(p.blendfile_uuid for p in bpy.context.scene.scatter5.get_all_psys(search_mode="all", also_linked=True))),)
        self.blendfile_uuid_initialized = True
    
    return self.blendfile_uuid_private


class SCATTER5_PR_Blend(bpy.types.PropertyGroup):
    """scat_blend = bpy.data.texts['.Geo-Scatter Settings'].scatter5 or use from ... __init__ import blend_prefs()"""                                                                              

    # .dP"Y8 Yb  dP 88b 88  dP""b8
    # `Ybo."  YbdP  88Yb88 dP   `"
    # o.`Y8b   8P   88 Y88 Yb
    # 8bodP'  dP    88  Y8  YboodP

    sync_channels : bpy.props.CollectionProperty(type=SCATTER5_PR_sync_channels) #Children Collection
    sync_channels_idx : bpy.props.IntProperty()
    
    # 88   88 88   88 88 8888b.
    # 88   88 88   88 88  8I  Yb
    # Y8   8P Y8   8P 88  8I  dY
    # `YbodP' `YbodP' 88 8888Y"
    
    #uuid per blend file
    
    blendfile_uuid : bpy.props.IntProperty(
        get=get_blendfile_uuid,
        description="random id between -2.147.483.647 & 2.147.483.647, can never be 0. should be unique. Is referenced by a scatter-system, in order to recognize links/appends from other files",
        )
    blendfile_uuid_initialized : bpy.props.BoolProperty(
        default=False,
        description="Don't touch this. was self.uuid initialized?",
        )
    blendfile_uuid_private : bpy.props.IntProperty(
        default=0,
        description="Don't touch this",
        )

    #global unique list of uuids for this blend?
    
    uuids_repository : bpy.props.CollectionProperty(
        type=SCATTER5_PR_uuids_repository,
        )
    
    def uuids_repository_cleanup(self, cleanse_none_ptr=True, cleanse_single_user_ptr=True,):
        """clean the uuid repository of expired ptr"""
        
        idx_to_remove = set()
        
        if (cleanse_none_ptr):
            idx_to_remove.update([i for i,itm in enumerate(self.uuids_repository) if (itm.ptr is None)])
            
        if (cleanse_single_user_ptr):
            idx_to_remove.update([i for i,itm in enumerate(self.uuids_repository) if (itm.ptr and itm.ptr.users==1)])
        
        if (idx_to_remove):
            for i in reversed(sorted(idx_to_remove)):
                itm = self.uuids_repository[i]
                dprint(f"REPORT: uuids_repository_cleanup().remove(): uuid={itm.uuid} ptr={itm.ptr}")
                self.uuids_repository.remove(i)
        
        return None
    
    # 8b    d8    db    .dP"Y8 888888 888888 88""Yb     .dP"Y8 888888 888888 8888b.
    # 88b  d88   dPYb   `Ybo."   88   88__   88__dP     `Ybo." 88__   88__    8I  Yb
    # 88YbdP88  dP__Yb  o.`Y8b   88   88""   88"Yb      o.`Y8b 88""   88""    8I  dY
    # 88 YY 88 dP""""Yb 8bodP'   88   888888 88  Yb     8bodP' 888888 888888 8888Y"
    
    s_master_seed : bpy.props.IntProperty(
        name=translate("Master Seed"),
        description=translate("The master seed influences every seed used by Geo-Scatter in this .blend file"),
        default=0,
        min=0,
        update=lambda s, c: ([setattr(ng.nodes["s_master_seed"],'integer',s.s_master_seed) for ng in bpy.data.node_groups if (not ng.library) and ng.name.startswith(".S Master Seed")],None)[1],
        )
    s_master_seed_animate : bpy.props.BoolProperty(
        name=translate("Animate Master Seed"),
        description=translate("Automatically change the master seed for each changing frame. Handy if you'd like to batch-render various scatter seeds"),
        default=False,
        update=lambda s, c: ([setattr(ng.nodes["s_master_seed_animate"],'boolean',s.s_master_seed_animate) for ng in bpy.data.node_groups if (not ng.library) and ng.name.startswith(".S Master Seed")],None)[1],
        )
    s_master_seed_animated : bpy.props.IntProperty(
        name=translate("Resulting Seed"),
        description=translate("The atuomatically calculated resulting value of the masted seed depending on the current frame and chosen master seed"),
        get=lambda s: s.s_master_seed + bpy.context.scene.frame_current,
        set=lambda s, v: None,
        )

    # 88 8b    d8 88""Yb  dP"Yb  88""Yb 888888
    # 88 88b  d88 88__dP dP   Yb 88__dP   88
    # 88 88YbdP88 88"""  Yb   dP 88"Yb    88
    # 88 88 YY 88 88      YbodP  88  Yb   88
    
    objects_import_method : bpy.props.EnumProperty(
        name=translate("Import Method"),
        description= translate("When you scatter a biome or when you scatter the selected assets from your asset browser, how do you wish to import the objects?"),
        default="APPEND", 
        items=( ("APPEND", translate("Append"), translate("Append the object(s) in your current .blend file"), "APPEND_BLEND",1),
                ("LINK", translate("Link"), translate("Link the object(s) in your current .blend file. When linking files in your .blend, you will save up on disk space and general performance, at the cost of risking losing data when the path of the linked libraries changes or are deleted"), "LINK_BLEND",2),
              ),
        )

    # 88   88 88""Yb 8888b.     db    888888 888888
    # 88   88 88__dP  8I  Yb   dPYb     88   88__
    # Y8   8P 88"""   8I  dY  dP__Yb    88   88""
    # `YbodP' 88     8888Y"  dP""""Yb   88   888888

    #Warning, 4 important properties ahead, first two not available in interface, quite dangerous because internally will be toggled on/off, if error, the scene is corrupted
    #these properties are used to control update function of the properties
    factory_active : bpy.props.BoolProperty(
        description="Enable the plugin to send update to the geo-scatter engine/nodetree",
        default=True,
        )
    factory_event_listening_allow : bpy.props.BoolProperty(
        description="Enable the plugin to listen to your keystrokes (used for the alt-for-batch functionality)",
        default=True,
        )
    factory_synchronization_allow : bpy.props.BoolProperty(
        name=translate("Synchronize Settings"),
        description=translate("The synchronization functionality allows you to create synchronization channels to link scatter-system(s) settings together. Tweaking one system will automatically apply the setting to another"),
        default=False,
        )
    factory_delay_allow : bpy.props.BoolProperty(
        name=translate("Settings Update Method"),
        description=translate("When tweaking a scatter property, our plugin will automatically update the value of the geometry-node property, which can be heavy to compute sometimes.\n\nWith this functionality of our plugin, we give you the option to control how the refresh signal is sent.\n\n• Note this option works best if the emitter object is not used as a scatter-surface"),
        default=False,
        )
    factory_update_method : bpy.props.EnumProperty(
        name=translate("Method"),
        default= "update_on_halt",
        description= translate("Change how the active particle system refreshes the viewport when you are tweaking the settings"),
        items=( ("update_delayed" ,translate("Fixed Interval"), translate("refresh viewport every x milliseconds"), 1),
                ("update_on_halt" ,translate("On Halt") ,translate("refresh viewport when the mouse button is released"), 2),
               #("update_apply" ,translate("Manual") ,translate("refresh viewport when clicking on the refresh button"), 3),
              ),
        )
    factory_update_delay : bpy.props.FloatProperty(
        name=translate("Refresh Rate"),
        unit='TIME_ABSOLUTE',
        default=0.25,
        max=2,
        min=0,
        step=3,
        precision=3,
        description=translate("Delay of the update when tweaking the system(s) settings"),
        )
    factory_cam_update_method : bpy.props.EnumProperty(
        name=translate("Method"),
        default="update_on_halt",
        description= translate("Some of our plugin features might be relying on the active camera. Unfortunately moving this camera will send a refresh signal to all dependent scatter-system(s), and this might create slowdowns.")+"\n\n"+translate("Choose which camera update signal you'd like to rely upon"),
        items=(("update_delayed", translate("Fixed Interval"), translate("Send an update signal automatically when the camera move, at given refreshrate"), 0),
               ("update_on_halt", translate("On Halt"), translate("Send an update signal automatically only when we detected that the camera stopped moving for a brief amount of time"), 1),
               ("update_apply", translate("Manual"), translate("Send an update signal only when enabling a camera related feature or when clicking on the refresh button"), 2),
               ("update_realtime", translate("Real-time"), translate("Use native blender camera info node to handle refresh signals. This means that blender might update all of your systems on every single camera move, which might slow down your viewport navigation experience!"), 3),
              ),
        update=lambda s,c: update_factory.update_camera_nodegroup(scene=c.scene, force_update=True),
        )
    factory_cam_update_secs : bpy.props.FloatProperty(
        name=translate("Refresh Rate"),
        unit='TIME_ABSOLUTE',
        default=0.35,
        max=2,
        min=0,
        step=3,
        precision=3,
        )
    factory_alt_allow : bpy.props.BoolProperty( #global control over event listening and tweaking delay, only for dev 
        name=translate("Allow Alt-for-batch"),
        description=translate("When pressing ALT while changing a scatter-system property, Geo-Scatter will automatically apply the value to all selected scatter-system"),
        default=True,
        )
    factory_alt_selection_method : bpy.props.EnumProperty(
        name=translate("Alt-for-batch selection method"),
        description=translate("Choose what you'd like the plugin to behave when alt-tweaking a system"),
        default="active_emitter",
        items=(("active_emitter", translate("Active Emitter"), translate("Apply the value to the selected scatter-system(s) of the same emitter"), 1),
               ("all_emitters", translate("All Emitters"), translate("Apply the value to the selected scatter-system(s) of this scene, across many emitters"), 2),
              ),
        )
    update_auto_overlay_rendered : bpy.props.BoolProperty(
        name=translate("Auto-Hide Overlay"),
        description=translate("Drawing objects contour overlay on your 3D viewport objects can consume a lot of performances when dealing with large scenes containing a lot of polygons.\n\nRay tracing renders are very good when dealing with highpoly objects, but the outline overlay drawing can potentially bottleneck your viewport performances while in rendered view.\n\nWhen choosing this option, we will automatically disable the overlay drawing when you use the 3D viewport rendered view"),
        default=False,
        )

    #  dP""b8 88   88 88
    # dP   `" 88   88 88
    # Yb  "88 Y8   8P 88
    #  YboodP `YbodP' 88

    show_description : bpy.props.BoolProperty(
        default=False,
        )
    ui_enabled : bpy.props.BoolProperty( #curently unused
        default=True,
        )