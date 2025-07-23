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
#  .oooooo..o                             .oooooo..o               .       .    o8o                                  
# d8P'    `Y8                            d8P'    `Y8             .o8     .o8    `"'                                  
# Y88bo.       .ooooo.  ooo. .oo.        Y88bo.       .ooooo.  .o888oo .o888oo oooo  ooo. .oo.    .oooooooo  .oooo.o 
#  `"Y8888o.  d88' `"Y8 `888P"Y88b        `"Y8888o.  d88' `88b   888     888   `888  `888P"Y88b  888' `88b  d88(  "8 
#      `"Y88b 888        888   888            `"Y88b 888ooo888   888     888    888   888   888  888   888  `"Y88b.  
# oo     .d8P 888   .o8  888   888       oo     .d8P 888    .o   888 .   888 .  888   888   888  `88bod8P'  o.  )88b 
# 8""88888P'  `Y8bod8P' o888o o888o      8""88888P'  `Y8bod8P'   "888"   "888" o888o o888o o888o `8oooooo.  8""888P' 
#                                                                                                d"     YD           
#                                                                                                "Y88888P'                                                                                                                                   
######################################################################################################

import bpy

from ... __init__ import addon_prefs, blend_prefs
from .. translations import translate
from .. scattering.emitter import poll_emitter

from . manual_settings import SCATTER5_PR_scene_manual
from . ops_settings import SCATTER5_PR_operators


######################################################################################################


def upd_emitter(self,context):
    """update function for scat_scene.emitter prop"""
    
    if (self.emitter is not None):
        
        #update square area information
        self.emitter.scatter5.estimate_square_area()
        
        #ensure geo-scatter interface
        if (self.emitter.scatter5.is_particle_interface_broken()):
            self.emitter.scatter5.particle_interface_refresh()
        
    #check for warning messages
    from ..ui.ui_notification import check_for_notifications
    check_for_notifications(checks={"T_ORPHAN":True},)
    
    return None


class SCATTER5_PR_uuids(bpy.types.PropertyGroup): 
    """scat_scene.uuids LEGACY, READ ONLY!"""
    
    uuid : bpy.props.IntProperty()
    owner : bpy.props.PointerProperty(type=bpy.types.Object)


class SCATTER5_PR_Scene(bpy.types.PropertyGroup):
    """scat_scene = bpy.context.scene.scatter5"""

    # 888888 8b    d8 88 888888 888888 888888 88""Yb
    # 88__   88b  d88 88   88     88   88__   88__dP
    # 88""   88YbdP88 88   88     88   88""   88"Yb
    # 888888 88 YY 88 88   88     88   888888 88  Yb

    #emitter terrain target workflow, the emitter is used to store scatter-systems

    emitter : bpy.props.PointerProperty( 
        type=bpy.types.Object, 
        poll=poll_emitter,
        name=translate("Emitter Object"),
        description=translate("The plugin will store your scatter-settings on this object when scattering.\nBy default, we will use the emitter mesh as the surface object, however you can choose other surface objects independently from the emitter in the 'Tweak>Surface' panel.\nNote that you are able to change the active emitter at any moment on the top of any 'Create' or 'Tweak' panels"),
        update=upd_emitter, #estimate square area when changing active object
        )
    emitter_pinned : bpy.props.BoolProperty( #pinned mode
        default=False, 
        description=translate("Pin/Unpin this emitter object"),
        )

    # 8b    d8    db    88b 88 88   88    db    88         8b    d8  dP"Yb  8888b.  888888     .dP"Y8 888888 888888 888888 88 88b 88  dP""b8 .dP"Y8 
    # 88b  d88   dPYb   88Yb88 88   88   dPYb   88         88b  d88 dP   Yb  8I  Yb 88__       `Ybo." 88__     88     88   88 88Yb88 dP   `" `Ybo." 
    # 88YbdP88  dP__Yb  88 Y88 Y8   8P  dP__Yb  88  .o     88YbdP88 Yb   dP  8I  dY 88""       o.`Y8b 88""     88     88   88 88 Y88 Yb  "88 o.`Y8b 
    # 88 YY 88 dP""""Yb 88  Y8 `YbodP' dP""""Yb 88ood8     88 YY 88  YbodP  8888Y"  888888     8bodP' 888888   88     88   88 88  Y8  YboodP 8bodP' 

    manual : bpy.props.PointerProperty(type=SCATTER5_PR_scene_manual)
    
    #  dP"Yb  88""Yb 888888 88""Yb    db    888888  dP"Yb  88""Yb .dP"Y8     .dP"Y8 888888 888888 888888 88 88b 88  dP""b8 .dP"Y8 
    # dP   Yb 88__dP 88__   88__dP   dPYb     88   dP   Yb 88__dP `Ybo."     `Ybo." 88__     88     88   88 88Yb88 dP   `" `Ybo." 
    # Yb   dP 88"""  88""   88"Yb   dP__Yb    88   Yb   dP 88"Yb  o.`Y8b     o.`Y8b 88""     88     88   88 88 Y88 Yb  "88 o.`Y8b 
    #  YbodP  88     888888 88  Yb dP""""Yb   88    YbodP  88  Yb 8bodP'     8bodP' 888888   88     88   88 88  Y8  YboodP 8bodP' 

    operators : bpy.props.PointerProperty(type=SCATTER5_PR_operators)
    
    # 88   88 .dP"Y8 888888 888888 88   88 88         888888 88   88 88b 88  dP""b8 888888 88  dP"Yb  88b 88 .dP"Y8 
    # 88   88 `Ybo." 88__   88__   88   88 88         88__   88   88 88Yb88 dP   `"   88   88 dP   Yb 88Yb88 `Ybo." 
    # Y8   8P o.`Y8b 88""   88""   Y8   8P 88  .o     88""   Y8   8P 88 Y88 Yb        88   88 Yb   dP 88 Y88 o.`Y8b 
    # `YbodP' 8bodP' 888888 88     `YbodP' 88ood8     88     `YbodP' 88  Y8  YboodP   88   88  YbodP  88  Y8 8bodP' 

    def get_all_emitters(self, search_mode="active_view_layer", also_linked=False,):
        """return list of all emitters visible in current context viewlayer"""
        
        ems = set()
        
        match search_mode:
            case 'all':
                objs = bpy.data.objects
            case 'scene':
                objs = self.id_data.objects
            case 'active_view_layer':
                objs = bpy.context.view_layer.objects
            case _:
                Exception("ERROR: get_all_emitters(): wrong search_mode arg given")
        
        for o in [o for o in objs if hasattr(o,"scatter5")]:
            
            #consider any objects that has a .scatter5.particle_systems[:] in it. will probably be invalid emitters as well
            if (o.scatter5.particle_systems):
                ems.add(o)
        
            #also consider any scatter_obj, might have a linked original_emitter hidden not in scene
            if (o.scatter5.is_scatter_obj):
                oe = o.scatter5.original_emitter
                if ((oe is not None) and hasattr(oe,"scatter5") and (oe.scatter5.particle_systems)):
                    ems.add(oe)
            
            continue
        
        #filter out linked?
        if (not also_linked):
            return [e for e in ems if not bool(e.library)]
        
        return list(ems)

    def get_all_psys(self, search_mode="active_view_layer", also_linked=False,):
        """return a list of all psys"""
        
        psys = set()
        
        match search_mode:
            case 'all':
                objs = bpy.data.objects
            case 'scene':
                objs = self.id_data.objects
            case 'active_view_layer':
                objs = bpy.context.view_layer.objects
            case _:
                raise Exception("ERROR: get_all_psys(): wrong search_mode arg given")
            
        for o in [o for o in objs if hasattr(o,"scatter5")]:
            
            #get all psys listed on emitters
            if (o.scatter5.particle_systems):
                psys.update(o.scatter5.particle_systems)
                
            #also consider scatter_obj with missing emitter
            if (o.scatter5.is_scatter_obj):
                p = o.scatter5.get_psy_from_scatter_obj()
                if (p is not None):
                    psys.add(p)
            
            continue

        #filter out linked?
        if (not also_linked):
            return [p for p in psys if (not p.is_linked)]
        
        return list(psys)
    
    def get_all_psy_orphans(self, search_mode="active_view_layer",):
        """return a list of scatter object that contains an engine modifier but with no psy scatter-settings attached
        (can occur if user delete his emitter object accidentally)"""
        
        orphans = set()

        match search_mode:
            case 'all':
                objs = bpy.data.objects
            case 'scene':
                objs = self.id_data.objects
            case 'active_view_layer':
                objs = bpy.context.view_layer.objects
            case _:
                raise Exception("ERROR: get_all_psy_orphans(): wrong search_mode arg given")
        
        for o in [o for o in objs if o.scatter5.is_scatter_obj]:
            p = o.scatter5.get_psy_from_scatter_obj()
            if (p is None):
                orphans.add(o)
        
        return list(orphans)
    
    def get_psy_by_name(self,name):
        """get a psy by its unique given name"""
        
        all_psys = self.get_all_psys(search_mode="all", also_linked=True)
        all_names = [p.name for p in all_psys]
        
        #is there a match? deny any further step if no match found..
        if (name not in all_names):
            return None
        
        #console warning if name collision found
        if (addon_prefs().debug):
            from .. utils.extra_utils import has_duplicates, get_duplicates
            if (has_duplicates(all_names)):
                dup = get_duplicates(all_names)
                print("WARNING: scatter5.get_psy_by_name(): duplicates found, can't ensure that this function works expectedly:")
                for p in [p for p in all_psys if p.name in dup]:
                    print(f"   -psy:'{p.name}'{p.uuid}, emitter:'{p.id_data.name}'{p.id_data.session_uid}")
        
        #first search in all psys that aren't linked
        for p in [p for p in all_psys if (p.name==name) and (not p.is_linked)]:
            return p
        
        #then if not found, fallback search in linked psys..
        for p in [p for p in all_psys if (p.name==name) and (p.is_linked)]:
            return p
        
        return None

    def get_psy_by_uuid(self,uuid):
        """get a psy by its unique uuid value"""
        
        all_psys = self.get_all_psys(search_mode="all", also_linked=True)
        all_uuids = [p.uuid for p in all_psys if p.scatter_obj]
        
        #is there a match? deny any further step if no match found..
        if (uuid not in all_uuids):
            return None
        
        #console warning if uuid collision found
        if (addon_prefs().debug):
            from .. utils.extra_utils import has_duplicates, get_duplicates
            if (has_duplicates(all_uuids)):
                dup = get_duplicates(all_uuids)
                print("WARNING: scatter5.get_psy_by_uuid(): duplicates found, can't ensure that this function works expectedly:")
                for p in [p for p in all_psys if p.uuid in dup]:
                    print(f"   -psy:'{p.name}'{p.uuid}, emitter:'{p.id_data.name}'{p.id_data.session_uid}")
        
        for p in all_psys:
            if (p.uuid==uuid):
                return p
        
        return None

    class factory_update_pause(object):
        """updating a scatter5 tweaking property will trigger the event/delay/sync modifiers, 
        use this 'with' obj to avoid triggering such behavior when changing properties, it will update context.scene globals use the return value to restore"""

        def __init__(self, factory=False, event=False, delay=False, sync=False, ):
            self._f, self._e, self._d, self._s = None, None, None, None
            self.factory, self.event, self.delay, self.sync = factory, event, delay, sync
            return None 

        def __enter__(self):
            scat_data = blend_prefs()
            
            if (self.factory):
                self._f = bool(scat_data.factory_active)
                scat_data.factory_active = False
                
            if (self.event):
                self._e = bool(scat_data.factory_event_listening_allow)
                scat_data.factory_event_listening_allow = False
                
            if (self.delay):
                self._d = bool(scat_data.factory_delay_allow)
                scat_data.factory_delay_allow = False
                
            if (self.sync):
                self._s = bool(scat_data.factory_synchronization_allow)
                scat_data.factory_synchronization_allow = False
                
            return None 

        def __exit__(self,*args):
            scat_data = blend_prefs()
                        
            if (self._f is not None):
                scat_data.factory_active = self._f
                
            if (self._e is not None):
                scat_data.factory_event_listening_allow = self._e
                
            if (self._d is not None):
                scat_data.factory_delay_allow = self._d
                
            if (self._s is not None):
                scat_data.factory_synchronization_allow = self._s
                
            return None 

    # 88     888888  dP""b8    db     dP""b8 Yb  dP 
    # 88     88__   dP   `"   dPYb   dP   `"  YbdP  
    # 88  .o 88""   Yb  "88  dP__Yb  Yb        8P   
    # 88ood8 888888  YboodP dP""""Yb  YboodP  dP    
    
    uuids : bpy.props.CollectionProperty(type=SCATTER5_PR_uuids)
