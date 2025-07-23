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

############################################################################################
#
#   .oooooo.                                                                        
#  d8P'  `Y8b                                                                       
# 888      888 oooo    ooo  .ooooo.  oooo d8b  .oooo.o  .ooooo.   .ooooo.  oooo d8b 
# 888      888  `88.  .8'  d88' `88b `888""8P d88(  "8 d88' `88b d88' `88b `888""8P 
# 888      888   `88..8'   888ooo888  888     `"Y88b.  888ooo888 888ooo888  888     
# `88b    d88'    `888'    888    .o  888     o.  )88b 888    .o 888    .o  888     
#  `Y8bood8P'      `8'     `Y8bod8P' d888b    8""888P' `Y8bod8P' `Y8bod8P' d888b    
#
############################################################################################

#ABOUT:
# users can dupplicate/link/append scatter-items. And when that happens we need to act accordinly (delete settings if dupplicated, ensure no uuid or name collision if appended, ect..)
# however, blender leave us no choice but to observe the user file and deduce if these actions happened base on our observation.
# if it was indeed possible to add our own function following a bpy.ops.wm.append() or a shift/altD copy/paste, then we wouldn't need such overseer module. 
# for now (b4.2LTS) we'll need to rely on it in order to detect these users actions, as the blender api isn't proposing anything that can help us

import bpy

from collections import Counter

from ... __init__ import blend_prefs
from .. scattering.update_factory import ensure_str_ptr_accuracy
from .. utils.extra_utils import dprint, get_from_uid, has_duplicates
from .. utils.create_utils import lock_transform
from .. utils.coll_utils import cleanup_scatter_collections
from .. utils.str_utils import find_suffix
from .. ui.ui_system_list import ensure_particle_interface_items
from .. ui.ui_notification import check_for_notifications


# ooooooooooooo                              oooo                           
# 8'   888   `8                              `888                           
#      888      oooo d8b  .oooo.    .ooooo.   888  oooo   .ooooo.  oooo d8b 
#      888      `888""8P `P  )88b  d88' `"Y8  888 .8P'   d88' `88b `888""8P 
#      888       888      .oP"888  888        888888.    888ooo888  888     
#      888       888     d8(  888  888   .o8  888 `88b.  888    .o  888     
#     o888o     d888b    `Y888""8o `Y8bod8P' o888o o888o `Y8bod8P' d888b    
                                                                          

def get_itm_tracker_type(itm):
    """automatically detect type. user can pass an emitter obj, scatter_obj, or psy directly"""
    
    #do we have a psy?
    if (hasattr(itm,'s_distribution_method')):
        return 'psy'
    
    #or a blender obj
    elif (type(itm) is bpy.types.Object) and (hasattr(itm,'scatter5')):
        
        #scatter obj?
        if (itm.scatter5.is_scatter_obj):
            p = itm.scatter5.get_psy_from_scatter_obj()
            if (p is not None):
                return 'psy'
            
        #emitter obj?
        elif (itm.scatter5.particle_systems):
            return 'emitter'
    
    return None
    
class Tracker:
    """Trackers for both psy or emitter type scatter item"""
    
    def __init__(self, itm, category=None):
        
        #define type
        self.type = get_itm_tracker_type(itm)
        assert self.type in ('psy','emitter'), "Can only pass psy or emitter object!"
        
        self.category = category
        
        if (self.type=='psy'):
            self.uuid = itm.uuid
            self.session_uid = itm.id_data.session_uid
            
        elif (self.type=='emitter'):
            self.uuid = itm.scatter5.uuid
            self.session_uid = itm.session_uid
            
        return None

    def __eq__(self, other):
        if isinstance(other, Tracker):
            return ((self.uuid==other.uuid) and (self.session_uid==other.session_uid) and (self.type==other.type))
        return False

    def __hash__(self):
        return hash((self.uuid, self.session_uid, self.type))
    
    def __repr__(self):
        itm = self.get_item()
        if (itm is not None):
            itype = get_itm_tracker_type(itm)
            if (itype=='psy'):
                  s = f"Itm<{itm} link={itm.is_linked} e_users_scene={len(itm.id_data.users_scene)}> PsyEmitter{itm.id_data} PsyScatterObj{itm.scatter_obj}"
            elif (itype=='emitter'):
                  s = f"Itm<{itm} link={bool(itm.library)} users_scene={len(itm.users_scene)}>"
            else: s = 'EmitterNowEmpty'
        else: s = 'NothingFound'
        return f"<Tracker type='{self.type}' uuid={self.uuid} session_uid={self.session_uid}> {s}"
        
    def get_item(self, all_psys=None):
        """Return psy from tracker information"""
        
        #give opportunity to pass it, otherwise we might call the function too often, might create a few ms of slowdowns
        if (all_psys is None):
            all_psys = bpy.context.scene.scatter5.get_all_psys(search_mode="all", also_linked=True)
        
        match self.type:
            
            case 'psy':
                #p = bpy.context.scene.scatter5.get_psy_by_uuid(self.uuid) can't use that here. uuid might be non unique because dupplicated
                for p in [p for p in all_psys if (p.uuid==self.uuid) and (p.id_data.session_uid==self.session_uid)]:
                    return p
                
            case 'emitter':
                e = get_from_uid(self.session_uid)
                if (e):
                    if (self.uuid==e.scatter5.uuid):
                        return e
        return None


#   .oooooo.    .o8                                                                  
#  d8P'  `Y8b  "888                                                                  
# 888      888  888oooo.   .oooo.o  .ooooo.  oooo d8b oooo    ooo  .ooooo.  oooo d8b 
# 888      888  d88' `88b d88(  "8 d88' `88b `888""8P  `88.  .8'  d88' `88b `888""8P 
# 888      888  888   888 `"Y88b.  888ooo888  888       `88..8'   888ooo888  888     
# `88b    d88'  888   888 o.  )88b 888    .o  888        `888'    888    .o  888     
#  `Y8bood8P'   `Y8bod8P' 8""888P' `Y8bod8P' d888b        `8'     `Y8bod8P' d888b    
                                                                                                                                                      
                                                                                   

class Observer:
    """main observer class, try to deduce what actions user did depending on the impaact on the scene"""
    
    #Here are global tracking lists
    
    TRACKED  = set() # - set of Tracker(), listing all tracked scatter-item, generated normally via add_psy_virgin() through this session. at blend session start, take all scatter items as tracked
    MISSOBJ  = set() # - set of (emitter.session_uid,psy_name) tuple, in the list are found psy with no tied scatter_obj. because these items does not have any scatter_obj it is impossible to track them as psyTracker
    INVALIDS = set() # - set of Tracker(), of found duplicated emitters, will create invalid original_emitter/psy emitter duos that need to be dealt with
    DUPPLIS  = set() # - set of Tracker(), in the list are found scatter-items coming from general valid dupplicata operation and/or an append operation. Append are duplicates basically.
    DUPPLIS  = set() # - set of Tracker(), in the list are found appended scatter-items
    ODITIES  = set() # - set of Tracker(), in the list we list all scatter-items that does not fit in any of the above categories
    CLEANSED = set() # - set of Tracker(), in the list are trackers that have been automatically cleansed because their uuids values no longer correspond to something in the user data
    SCNUIDS  = set() # - set of int scene.session_uid values, items that have been removed, probably because user deleted the object from his blend file
    
    @classmethod
    def track_new_scatter_item(cls,itm):
        """add a new psy or emitter in the tracked list"""
        
        typ = get_itm_tracker_type(itm)
        if (typ):
            cls.TRACKED.add(Tracker(itm, category='TRACKED'))
            dprint(f"HANDLER: overseer.track_new_scatter_item(): {itm}", depsgraph=True)
        
        return None
    
    @classmethod
    def cleanse_tracklists(cls):
        """reset all tracking lists, empty all the trackers"""
        for l in (cls.TRACKED,cls.MISSOBJ,cls.INVALIDS,cls.DUPPLIS,cls.ODITIES,cls.CLEANSED, cls.SCNUIDS):
            l.clear()
        return None
            
    @classmethod
    def initiate(cls):
        """consider all possible psys and emitters in current blend data as tracked"""

        dprint("HANDLER: overseer.Observer.initiate() -start", depsgraph=True)
        
        #start from scratch, set all tracking to default
        cls.cleanse_tracklists()
        
        #init track of all scatter items
        scat_scene = bpy.context.scene.scatter5
        all_itms = scat_scene.get_all_psys(search_mode="all", also_linked=True) + scat_scene.get_all_emitters(search_mode="all", also_linked=True)
        for itm in all_itms:
            cls.track_new_scatter_item(itm)
        
        #init track of all scenes
        for sc in bpy.data.scenes:
            cls.SCNUIDS.add(sc.session_uid)
            
        dprint("HANDLER: overseer.Observer.initiate() -end", depsgraph=True)
            
        return None
    
    @classmethod
    def observe_scenes_changes(cls):
        """observe changes related to scene, need to be in a different function, as observation happens from handlers.frame_post"""

        dprint("HANDLER: overseer.observe_scenes_changes() -start", depsgraph=True)

        #define a return value: inform what changes happened during the observation
        changes = set()
        
        #check for deleted scenes
        for uid in cls.SCNUIDS.copy():
            sc = get_from_uid(uid, collection=bpy.data.scenes)
            if (sc is None):
                dprint(f"HANDLER: overseer.observe_scenes_changes() SceneDeleted: {uid}", depsgraph=True)
                cls.SCNUIDS.remove(uid)
                changes.add("SceneDeleted")
            continue
        
        #check for added scenes, either with operator, or link/append
        for sc in bpy.data.scenes:
            uid = sc.session_uid
            if (uid not in cls.SCNUIDS):
                cls.SCNUIDS.add(uid)
                dprint(f"HANDLER: overseer.observe_scenes_changes(): NewSceneFound: {sc}", depsgraph=True)
                changes.add("NewSceneFound")
                changes.add(f"NewSceneFoundArg:{uid}")
                continue
        
        dprint("HANDLER: overseer.observe_scenes_changes() -end", depsgraph=True)

        return changes
        
    @classmethod
    def observe_scatter_items_changes(cls):
        """track of changes in scene datas, or scatter items (emitters & psys), observation should happens on handlers.depsgraph"""
            
        dprint("HANDLER: overseer.observe_scatter_items_changes() -start", depsgraph=True)
            
        #define a return value: inform what changes happened during the observation
        changes = set()
        
        scat_scene   = bpy.context.scene.scatter5
        all_psys     = scat_scene.get_all_psys(search_mode="all", also_linked=True)
        all_emitters = scat_scene.get_all_emitters(search_mode="all", also_linked=True)
        all_itms     = all_psys + all_emitters
            
        #for all tracklists of Tracker object, check if t.itm is valid. unvalid item means that the users prolly deleted them, via our remove_psy op, or by deleting a collection/scene.
        
        for l in (cls.TRACKED,cls.INVALIDS,cls.DUPPLIS,cls.ODITIES):
            if (l):
                for t in l.copy():
                    itm = t.get_item(all_psys=all_psys)
                    
                    #if tracked obj/psy no longer exists in user file, we consider this tracker as cleaned up. might do a comeback later if CTRL+Z
                    if (itm is None):
                        dprint(f"HANDLER: overseer.observe_scatter_items_changes() TrackerCleansed: {t}", depsgraph=True)
                        cls.CLEANSED.add(t)
                        l.remove(t)
                        if (t.type=='emitter'):
                            changes.add('EmitterTrackerCleansed') #if an emitter has been deleted by user, this information might be valuable to us
                        # elif (t.type=='emitter'):
                        #     changes.add('PsyTrackerCleansed') # useless to get notified of changes in internal tracklists (?)
                        continue
                    
                    #if tracked emitter still exists, but don't have any scatters, we simply remove the tracker
                    elif ((t.type=='emitter') and (not itm.scatter5.particle_systems)):
                        dprint(f"HANDLER: overseer.observe_scatter_items_changes() EmitterTrackerDeletion: {t}", depsgraph=True)
                        l.remove(t)
                        #changes.add('EmitterTrackerDeletion') # useless to get notified of changes in internal tracklists (?)
                        continue
                            
        #if a tracked in cleansed list actually exists, then we restore it to previous list. It means prolly user did a control-Z
        
        for t in cls.CLEANSED.copy():
            itm = t.get_item(all_psys=all_psys)
            if (itm):
                if (t.category is not None):
                    dprint(f"HANDLER: overseer.observe_scatter_items_changes() TrackerRestored: {itm} from {t.category}", depsgraph=True)
                    #
                    oldTRACKLIST = getattr(cls,t.category)
                    oldTRACKLIST.add(t)
                    #
                    cls.CLEANSED.remove(t)
                    #
                    #if we restored a psy, we also need to restore it's emitter
                    if (t.type=='psy'):
                        et = Tracker(itm.id_data, category=t.category)
                        oldTRACKLIST.add(et)
                    #
                    changes.add('TrackerRestored')
                    continue
        
        #then iterate through all tracker items
        
        for itm in all_itms:
            t = Tracker(itm)
                
            #skip this tracker if we are tracking them already
            if any(t in l for l in (cls.TRACKED,cls.INVALIDS,cls.DUPPLIS,cls.ODITIES)):
                continue
            
            #track for psys
            if (t.type=='psy'):
                p  = itm
                e  = p.id_data
                so = p.scatter_obj
                oe = so.scatter5.original_emitter if (so) else None
                
                #did some of our items are now psy with missing scatter_obj ?
                if (not so):
                    """
                    dprint(f"HANDLER: overseer.observe_scatter_items_changes(): FoundMissingScatterObj: {p}", depsgraph=True)
                    #
                    #add add custom tuple to tracklist
                    t = (e.session_uid,p.name)
                    cls.MISSOBJ.add(t)
                    #
                    changes.add("FoundMissingScatterObj")
                    """
                    continue
                
                #did we find psys coming from an emitter duplicated with shift/alt d? yes if psy scatter_object.original_emitter isn't the same as psy emitter
                elif ((oe) and (oe!=e)):
                    dprint(f"HANDLER: overseer.observe_scatter_items_changes(): FoundDupplisInvalidEmits: {p}", depsgraph=True)
                    #
                    #consider the emitter as invalid
                    cls.INVALIDS.add(Tracker(e, category='INVALIDS'))
                    #and also all it's psys
                    for ep in e.scatter5.particle_systems:
                        cls.INVALIDS.add(Tracker(ep, category='INVALIDS'))
                    #
                    changes.add("FoundDupplisInvalidEmits")
                    continue
                
                #we consider any links as officially tracked. perhaps there are some exception to this rule
                elif (p.is_linked):
                    dprint(f"HANDLER: overseer.observe_scatter_items_changes(): LinksFound: {itm}", depsgraph=True)
                    #
                    #consider the emitter as tracked, cause will be linked as well
                    cls.TRACKED.add(Tracker(e, category='TRACKED'))
                    #and also all it's psys, if one psy is linked, so are all emitter psys
                    for ep in e.scatter5.particle_systems:
                        cls.TRACKED.add(Tracker(ep, category='TRACKED'))
                    #
                    changes.add("LinksFound")
                    continue
                
                #did we find an appended scatter_obj? unsure how to detect if the item is a coming from an append..
                #if we append a scatter_obj or emitter by itself hide_select will be False, which would be strange. however it will not work if user is appending a full geo-scatter collection
                elif (oe):
                    dprint(f"HANDLER: overseer.observe_scatter_items_changes(): FoundDuplicates: {itm}", depsgraph=True)
                    #
                    #add this psy tracker to dupp list
                    t.category = 'DUPPLIS'
                    cls.DUPPLIS.add(t)
                    #
                    #also consider it's emitter as an append
                    et = Tracker(e, category='DUPPLIS')
                    cls.DUPPLIS.add(et)
                    #
                    changes.add("FoundDuplicates")
                    continue
            
            #looks like we do not know what is that? What user case is this?
            dprint(f"HANDLER: overseer.observe_scatter_items_changes(): FoundOdity: {t} / {itm}", depsgraph=True)
            #
            #add this tracker to the list of odities, we failed to determine if it is an append/link/dupplis. What can it be???
            t.category = 'ODITIES'
            cls.ODITIES.add(t)
            #
            changes.add("FoundOdity")
            continue
        
        dprint("HANDLER: overseer.observe_scatter_items_changes() -end", depsgraph=True)
        
        return changes
                    
    @classmethod
    def debug_print(cls):
        
        print("<Observer...")
        for n in ('TRACKED','MISSOBJ','INVALIDS','DUPPLIS','ODITIES','CLEANSED','SCNUIDS'):
            L = getattr(cls,n)
            if (L):
                print(f" -{n}[:]")
                for t in L:
                    print(f"  {t}")
        print("  ...>")
        
        return None
    
#   .oooooo.   oooo                                                         
#  d8P'  `Y8b  `888                                                         
# 888           888   .ooooo.   .oooo.   ooo. .oo.   oooo  oooo  oo.ooooo.  
# 888           888  d88' `88b `P  )88b  `888P"Y88b  `888  `888   888' `88b 
# 888           888  888ooo888  .oP"888   888   888   888   888   888   888 
# `88b    ooo   888  888    .o d8(  888   888   888   888   888   888   888 
#  `Y8bood8P'  o888o `Y8bod8P' `Y888""8o o888o o888o  `V88V"V8P'  888bod8P' 
#                                                                 888       
#                                                                o888o      

def scatter_items_cleanup(what_happened=None):
    """cleaning up potential scatter-items that users duplicated with shift/alt+D, appended, or linked into file, based on overseer observation"""
    
    dprint(f"HANDLER: overseer.scatter_items_cleanup().what_happened = {what_happened}")
    cls = Observer
    
    #################### If user deleted a scene
    """
    if ('SceneDeleted' in what_happened):
        
        dprint(f"HANDLER: overseer.scatter_items_cleanup().SceneDeleted")
    """
    #################### If user added a new scene
    """
    if ('NewSceneFound' in what_happened):
        
        for what in what_happened:
            if what.startswith('NewSceneFoundArg:'):
                uid = int(what.replace('NewSceneFoundArg:',''))
                scn = get_from_uid(uid, bpy.data.scenes)
                dprint(f"HANDLER: overseer.scatter_items_cleanup().NewSceneFoundArg: {scn}")
    """
    #################### If user did a ctrl+z then we need to fix some blender bugs
    if ('TrackerRestored' in what_happened):
                
        for t in [t for t in cls.TRACKED.copy() if (t.type=='psy')]:
            
            try:
                p = t.get_item()
            
                #ensure ins_col in nodetree is correct. Blender might/will not remember to set up the coll pointer back in nodetree after a ctrl+Z
                if (p.s_instances_coll_ptr):
                    ng = p.get_scatter_node("s_instances_coll_ptr", raise_exception=False)
                    if (ng.inputs[0].default_value!=p.s_instances_coll_ptr):
                        ng.inputs[0].default_value = p.s_instances_coll_ptr
                        
                        dprint(f"HANDLER: overseer.scatter_items_cleanup().TrackerRestored.InsPtrCleanup -> psy:{p.name}")
                                        
            except Exception as e:
                print(f"ERROR: overseer.scatter_items_cleanup().TrackerRestored.Exception!")
                print(e)
                
            continue
            
    #################### If we found some links, ensure their interface is correct (uuid might be corrupt)
    if ('LinksFound' in what_happened):
        
        emts_added = set()
        psys_added = set()

        #ensure there's no scatter_obj alone roaming in the scene, do a collection cleanup, first we collect the items we'll clean
        
        for t in [t for t in cls.TRACKED if (t.type=='psy')]:

            try:
                p = t.get_item()
                if (p) and (p.is_linked):
                    e  = p.id_data
                    so = p.scatter_obj
                    
                    #refresh interface later
                    emts_added.add(e)
                    
                    #clean coll later
                    psys_added.add(p)

                    dprint(f"HANDLER: overseer.scatter_items_cleanup().LinksFound.psy.particle_interface_refresh -> psy:{p.name}")
                
            except Exception as e:
                print(f"ERROR: overseer.scatter_items_cleanup().LinksFound.psy.Exception!")
                print(e)
                
            continue

        #clean lone scatter_obj, place it in collection
        
        if (psys_added):
            dprint(f"HANDLER: overseer.scatter_items_cleanup().LinksFound.cleanup_scatter_collections()")
            cleanup_scatter_collections(psys=psys_added, options={"ensure_p_psy_col":True,"ensure_p_ins_col":True,"ensure_p_surf_col":True,"ensure_viewlayers":True},)
        
        #ensure emitter interfaces/somewhere in scene
        
        if (emts_added):
            for e in emts_added:
                
                #ensure new emitters in scene
                if (e not in bpy.context.view_layer.objects[:]):
                    if (e not in bpy.context.scene.collection.objects[:]):
                        bpy.context.scene.collection.objects.link(e)
                
                #ensure particle interface
                if (e.scatter5.is_particle_interface_broken()):
                    e.scatter5.particle_interface_refresh()
                    
                continue
            dprint(f"HANDLER: overseer.scatter_items_cleanup().LinksFound.emitter.particle_interface_refresh -> emitter:{e.name}")

        #ensure relyability of viewlayers
        if (psys_added):
            cleanup_scatter_collections(options={"ensure_viewlayers":True})

        #if user linked a collection instance of a whole Geo-Scatter collection, we lock it to 0,0,0 origin
        
        for o in [o for o in bpy.context.scene.objects if o.name.startswith("Geo-Scatter") and o.type=='EMPTY' and o.instance_type=='COLLECTION']:
            coll = o.instance_collection
            if (coll.library):
                dprint(f"HANDLER: overseer.scatter_items_cleanup().LinksFound.InstanceEmptyCleanup -> {o}")
                o.location = (0,0,0)
                o.rotation_euler = (0,0,0)
                o.scale = (1,1,1)
                o.hide_select = True
                lock_transform(o,True)
                continue

    #################### Delete psys with missing scatter_obj asap
    """
    if (cls.MISSOBJ):
        
        emts_added = set()
        
        for t in cls.MISSOBJ.copy():
            euid,psy_name = t #is not a list of tracker, but a list of tuple. Tracker won't work because uuid will be invalid if scatter_obj is None
            
            try:
                e = get_from_uid(euid)
                p = e.scatter5.particle_systems.get(psy_name)
                
                if (p.scatter_obj is None):
                    #remove the psy
                    pname = p.name
                    p.remove_psy()
                else:
                    print(f"ERROR: overseer.scatter_items_cleanup().FoundMissingScatterObj.removing_psy -> emitter:{e.name}/psy:{pname} does have a scatter_obj? why is it on the MISSOBJ at the first place then?")
                
                #refresh later
                emts_added.add(e)
                
                dprint(f"HANDLER: overseer.scatter_items_cleanup().FoundMissingScatterObj.removing_psy -> emitter:{e.name}/psy:{pname}")
                
            except Exception as e:
                print(f"ERROR: overseer.scatter_items_cleanup().FoundMissingScatterObj.Exception!")
                print(e)
            
            cls.MISSOBJ.remove(t)
            continue
        
        #refresh items
        ensure_particle_interface_items(objs=emts_added)
    """
    #################### Remove all emitter settings of duplicated emitters
    if (cls.INVALIDS):
        
        emts_added = set()

        for t in [t for t in cls.INVALIDS.copy() if (t.type=='emitter')]:
            
            try:
                e = t.get_item()
                
                #remove all psys trackers from dupplis
                for p in e.scatter5.particle_systems:
                    tp = Tracker(p)
                    if (tp in cls.INVALIDS):
                        cls.INVALIDS.remove(tp)
                    
                #remove all psys
                e.scatter5.particle_systems.clear()
                
                #refresh later
                emts_added.add(e)
                
                dprint(f"HANDLER: overseer.scatter_items_cleanup().FoundDupplisInvalidEmits.removing_psy -> emitter:{e.name}")

            except Exception as e:
                print(f"ERROR: overseer.scatter_items_cleanup().FoundDupplisInvalidEmits.Exception!")
                print(e)
                
            cls.INVALIDS.remove(t)
            continue
    
        #refresh items
        if (emts_added):
            ensure_particle_interface_items(objs=emts_added)
        
    #################### Ensure psy.uuid and emitter.scatter5.uuid are unique for appended or duplicated scatters 
    if (cls.DUPPLIS):
            
        scat_data = blend_prefs()
        psys_added = set()
        
        #then let's take care of appended psys
            
        for t in [t for t in cls.DUPPLIS.copy() if (t.type=='psy')]:
            
            try:
                p = t.get_item()
                so = p.scatter_obj
                is_appended = p.is_from_another_blendfile()
                
                #remove before potentially changing uuid value
                cls.DUPPLIS.remove(t)
                
                #refresh uuid, in case of collision. (system will automatically detect collision on read)
                _ = so.scatter5.uuid
                
                #update blendfile_uuid, now that we have converted the scatter, it's officially from this file
                if (is_appended):
                    p.blendfile_uuid = scat_data.blendfile_uuid
                
                #remove old tracker, and create a new one (uuid might have changed tracker is invalid)
                cls.TRACKED.add(Tracker(p, category='TRACKED'))
                
                #ensure no naming conflict
                existing_names = [o.name.replace("scatter_obj : ","") for o in bpy.data.objects if o.name.startswith("scatter_obj : ") and not o.library]
                new_name = find_suffix(f"{p.name} {'🢃' if is_appended else '⯎'}",existing_names) #unicode looks big in editor but look fine in blender IMO
                p.name_bis = "" #reset naming popup msg functionality. name_bis is here to restrict user from choosing a name not available
                p.name = new_name
                p.name_bis = new_name
                
                #ensure scatter obj is hidden from selection
                so.hide_select = True
                #ensure scatter obj name
                so.name = f"scatter_obj : {new_name}"
                
                #ensure viewport status
                p.hide_viewport = p.hide_viewport
                p.hide_render = p.hide_render
                
                #ensure scatter obj geonode modifier didn't get instanced during dupplication
                mod = p.get_scatter_mod(strict=True, raise_exception=False)
                if (mod):
                    if (mod.node_group.users>1):
                        mod.node_group = mod.node_group.copy()
                
                #mark for collection cleanup
                psys_added.add(p)
                
                #NOTE Hmmm what about instance & surfaces uuid collision? is it even possible?
                # & What about possible collision with links as well.. oh god..
                
                dprint(f"HANDLER: overseer.scatter_items_cleanup().FoundDuplicates.psy.uuid/name/coll -> {p}")
                
            except Exception as e:
                if (t in cls.DUPPLIS):
                    cls.DUPPLIS.remove(t)
                print(f"ERROR: overseer.scatter_items_cleanup().FoundDuplicates.psy.Exception!")
                print(e)
                
            continue
    
        #clean up the collection, always a mess after import
        
        if (psys_added):
            
            dprint(f"HANDLER: overseer.scatter_items_cleanup().FoundDuplicates.cleanup_scatter_collections()")
            for sc in [sc for sc in bpy.data.scenes if any(ch.name.startswith("Geo-Scatter") for ch in sc.collection.children_recursive)]:
                cleanup_scatter_collections(scene=sc, psys=psys_added, options={"ensure_single_gscol_ins":True,"ensure_no_gscol_dupp":True,"ensure_p_psy_col":True,"plus_reset_so_in_psy_col":True,"ensure_p_ins_col":True,"ensure_p_surf_col":True,"remove_unused_colls":True,"ensure_viewlayers":True,})
        
        #then let's clean their emitters
        
        for t in [t for t in cls.DUPPLIS.copy() if (t.type=='emitter')]:
            
            try:
                e = t.get_item()
                
                #remove before potentially changing uuid value
                cls.DUPPLIS.remove(t)
                                
                #refresh uuid, in case of collision. (system will automatically detect collision on read)
                _ = e.scatter5.uuid
                
                #remove old tracker, and create a new one (uuid might have changed tracker is invalid)
                cls.TRACKED.add(Tracker(e, category='TRACKED'))

                #in the previous loop we updated the scatter name/uuid therefore we need to rebuild the interface
                e.scatter5.particle_interface_refresh()
                    
                #ensure the str ptr are accurate with the ng collection
                ensure_str_ptr_accuracy(e)
                
                #ensure new emitters in scene
                if (e not in bpy.context.view_layer.objects[:]):
                    if (e not in bpy.context.scene.collection.objects[:]):
                        bpy.context.scene.collection.objects.link(e)
                        
                dprint(f"HANDLER: overseer.scatter_items_cleanup().FoundDuplicates.emitter.uuid/gui -> {e}")
                
            except Exception as e:
                if (t in cls.DUPPLIS):
                    cls.DUPPLIS.remove(t)
                print(f"ERROR: overseer.scatter_items_cleanup().FoundDuplicates.emitter.Exception!")
                print(e)
                
            continue
        
        #one last cleanup..
        if (psys_added):
            
            #ensure relyability of viewlayers
            cleanup_scatter_collections(options={"unlink_distmeshes":True,"clean_placeholders":True,"ensure_viewlayers":True})
        
            #& if user did a scene full copy, we need to clean that shit, leave a lot of nasty collections duplicates
            if ('NewSceneFound' in what_happened):
                for what in what_happened:
                    if what.startswith('NewSceneFoundArg:'):
                        uid = int(what.replace('NewSceneFoundArg:',''))
                        scn = get_from_uid(uid, bpy.data.scenes)         
                        cleanup_scatter_collections(scene=scn, psys=psys_added, options={"ensure_single_gscol_ins":True,"ensure_no_gscol_dupp":True,"ensure_p_psy_col":True,"plus_reset_so_in_psy_col":True,"ensure_p_ins_col":True,"ensure_p_surf_col":True,"remove_unused_colls":True,"ensure_viewlayers":True,},)
                        continue 
            
            #& need to ensure surfaces. might be messed up because of a dupplication behavior
            for p in bpy.context.scene.scatter5.get_all_psys(search_mode="all"):
                p.s_distribution_method = p.s_distribution_method
                p.s_surface_method = p.s_surface_method
                continue
                            
        #check for orphans, it's possible that during the dupplication operations, some scatter_obj got dupplicated without any emitters aside
        check_for_notifications(checks={"T_ORPHAN":True},)

    return None