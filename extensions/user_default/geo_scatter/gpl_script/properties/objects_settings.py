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

#   .oooooo.    .o8           o8o       .oooooo..o               .       .    o8o                                  
#  d8P'  `Y8b  "888           `"'      d8P'    `Y8             .o8     .o8    `"'                                  
# 888      888  888oooo.     oooo      Y88bo.       .ooooo.  .o888oo .o888oo oooo  ooo. .oo.    .oooooooo  .oooo.o 
# 888      888  d88' `88b    `888       `"Y8888o.  d88' `88b   888     888   `888  `888P"Y88b  888' `88b  d88(  "8 
# 888      888  888   888     888           `"Y88b 888ooo888   888     888    888   888   888  888   888  `"Y88b.  
# `88b    d88'  888   888     888      oo     .d8P 888    .o   888 .   888 .  888   888   888  `88bod8P'  o.  )88b 
#  `Y8bood8P'   `Y8bod8P'     888      8""88888P'  `Y8bod8P'   "888"   "888" o888o o888o o888o `8oooooo.  8""888P' 
#                             888                                                              d"     YD           
#                         .o. 88P                                                              "Y88888P'           
#                         `Y888P                                                                                   
######################################################################################################

import bpy

from ... __init__ import bl_info, addon_prefs, blend_prefs
from .. utils.extra_utils import dprint
from .. utils.math_utils import generate_uuid_int, ensure_rgba_colors
from .. translations import translate
from .. resources import directories

from . particle_settings import SCATTER5_PR_particle_systems, SCATTER5_PR_particle_groups
from . mask_settings import SCATTER5_PR_procedural_vg

from .. ui.ui_system_list import SCATTER5_PR_particle_interface_items
from .. scattering.selection import on_particle_interface_interaction

'''
from . manual_settings import SCATTER5_manual_physics_brush_object_properties
'''

######################################################################################################


def get_uuid(self):
    """generate uuid once on first read"""

    obj = self.id_data
    scat_data = blend_prefs()
    
    #initialize uuid if not already done
    if (not self.uuid_initialized):
        dprint(f"REPORT: get_uuid(): Initialization: {obj}")
        
        #first do a cleanup of the repo, because user might have obj no longer used in his scene. That's a downside of this repo trick
        scat_data.uuids_repository_cleanup()
        
        #we have legacy uuids. did we generate a legacy uuid for this object already?
        legacy_uuids = {itm.owner:itm.uuid for sc in bpy.data.scenes for itm in sc.scatter5.uuids}
        if (obj in legacy_uuids):
            self.uuid_private = legacy_uuids[obj]
            print(f"REPORT: get_uuid(): Initialization from a Legacy Scene.scatter5.uuids : {obj}")
             
        else:
            self.uuid_private = generate_uuid_int(existing_uuids=[itm.uuid for itm in scat_data.uuids_repository],)
        
        #set initializaton status
        self.uuid_initialized = True
        
        #linked objs shouldn't be objected to initialization process. Limitation of uuid with linked objects unfortunately..
        if (obj.library):
            print(f"WARNING: get_uuid(): Initialization on a Linked Object.. Unsustainable practice.. : {obj}")

    #in case of dupplication (or append and collision dupplication), obj.uuid will also be dupplicated. To counter that, we have the uuid repository, listing all obj by their ptr
    if ((not obj.library) and (not obj.override_library) and (obj not in [itm.ptr for itm in scat_data.uuids_repository])):
        dprint(f"REPORT: get_uuid(): StoringInUuidRepo: {obj}")

        #first do a cleanup of the repo, because user might have obj no longer used in his scene. That's a downside of this repo trick
        scat_data.uuids_repository_cleanup()

        #then we create a new repo item
        newitm = scat_data.uuids_repository.add()
        newitm.ptr = obj
        
        #check for collision
        if (self.uuid_private in [itm.uuid for itm in scat_data.uuids_repository]):
            print(f"REPORT: get_uuid(): Uuid collision found. Modifying `uuid_private` of: {obj}")
            self.uuid_private = generate_uuid_int(existing_uuids=[itm.uuid for itm in scat_data.uuids_repository],)
            
        #store uuid as item.name
        newitm.uuid = self.uuid_private
        newitm.name = str(self.uuid_private)
    
    return self.uuid_private


class SCATTER5_PR_Object(bpy.types.PropertyGroup): 
    """scat_object = bpy.context.object.scatter5"""
    
    # 88   88 88   88 88 8888b.
    # 88   88 88   88 88  8I  Yb
    # Y8   8P Y8   8P 88  8I  dY
    # `YbodP' `YbodP' 88 8888Y"
    
    # sadly blender does not support native uuid at an oject level, so we needed to re-implemented it.
    
    uuid : bpy.props.IntProperty(
        get=get_uuid,
        description="random id between -2.147.483.647 & 2.147.483.647, can never be 0. Should be an unique identifier. Please don't do a for loop with every object.uuid's or it will initialize a lot of objects.",
        )
    uuid_initialized : bpy.props.BoolProperty(
        default=False,
        description="Don't touch this. was self.uuid initialized?",
        )
    uuid_private : bpy.props.IntProperty(
        default=0,
        description="Don't touch this",
        )

    # .dP"Y8  dP""b8    db    888888 888888 888888 88""Yb      dP"Yb  88""Yb  88888
    # `Ybo." dP   `"   dPYb     88     88   88__   88__dP     dP   Yb 88__dP     88
    # o.`Y8b Yb       dP__Yb    88     88   88""   88"Yb      Yb   dP 88""Yb o.  88
    # 8bodP'  YboodP dP""""Yb   88     88   888888 88  Yb      YbodP  88oodP "bodP'
    
    is_scatter_obj : bpy.props.BoolProperty(
        description="is the current object used as a scatter_obj? to determine so, check if a scatter engine modifier, new or legacy, is present on this object",
        get=lambda s: any(m.name.startswith(("Geo-Scatter Engine", "Scatter5 Geonode Engine")) for m in s.id_data.modifiers), #support new/legacy naming
        set=lambda s, v: None,
        )
    
    original_emitter : bpy.props.PointerProperty( #Keep Track of original emitter, in case of user dupplicating object data, it might cause BS 
        description="is needed when dupplicating an object, it will also dupplicate every object properties (could be solved more elegantly if blender had real uuid)",
        type=bpy.types.Object, 
        )

    def get_psy_from_scatter_obj(self):
        """find back psy from a scatter_obj"""
        
        o = self.id_data
        if (not o.scatter5.is_scatter_obj):
            return None
        
        oe = self.original_emitter
        if (oe is None):
            dprint(f"REPORT: get_psy_from_scatter_obj('{o.name}') original_emitter:None.")
            return None
        
        if (hasattr(oe,"scatter5")):
            
            if (not oe.scatter5.particle_systems):
                dprint(f"REPORT: get_psy_from_scatter_obj('{o.name}') original_emitter:'{oe.name}' doesn't have any psy(s).")
                return None
            
            for p in oe.scatter5.particle_systems:
                if (p.scatter_obj==o):
                    return p
        
        dprint(f"REPORT: get_psy_from_scatter_obj('{o.name}') original_emitter:'{oe.name}' no psys found with this scatter_obj assigned")
        return None
    
    # 8888b.  88 .dP"Y8 888888 88""Yb 88 88""Yb 88   88 888888 88  dP"Yb  88b 88     8b    d8 888888 .dP"Y8 88  88 888888 .dP"Y8 
    #  8I  Yb 88 `Ybo."   88   88__dP 88 88__dP 88   88   88   88 dP   Yb 88Yb88     88b  d88 88__   `Ybo." 88  88 88__   `Ybo." 
    #  8I  dY 88 o.`Y8b   88   88"Yb  88 88""Yb Y8   8P   88   88 Yb   dP 88 Y88     88YbdP88 88""   o.`Y8b 888888 88""   o.`Y8b 
    # 8888Y"  88 8bodP'   88   88  Yb 88 88oodP `YbodP'   88   88  YbodP  88  Y8     88 YY 88 888888 8bodP' 88  88 888888 8bodP' 
    
    distmesh_manual_all : bpy.props.PointerProperty(
        type=bpy.types.Mesh,
        )
    distmesh_physics : bpy.props.PointerProperty(
        type=bpy.types.Mesh,
        )
    
    # 88""Yb    db    88""Yb 888888 88  dP""b8 88     888888     .dP"Y8 Yb  dP .dP"Y8 888888 888888 8b    d8 .dP"Y8
    # 88__dP   dPYb   88__dP   88   88 dP   `" 88     88__       `Ybo."  YbdP  `Ybo."   88   88__   88b  d88 `Ybo."
    # 88"""   dP__Yb  88"Yb    88   88 Yb      88  .o 88""       o.`Y8b   8P   o.`Y8b   88   88""   88YbdP88 o.`Y8b
    # 88     dP""""Yb 88  Yb   88   88  YboodP 88ood8 888888     8bodP'  dP    8bodP'   88   888888 88 YY 88 8bodP'

    particle_systems : bpy.props.CollectionProperty(type=SCATTER5_PR_particle_systems) #Children Collection
    
    def get_psy_active(self):
        """return the active particle system of this emitter, will return bpy.types.Object or None"""

        if (not self.particle_systems):
            return None 

        itm = self.get_interface_active_item()
        if ((itm is not None) and (itm.interface_item_type=='SCATTER_SYSTEM')):
            return itm.get_interface_item_source()

        return None

    def get_psys_selected(self, all_emitters=False, respect_ui_order=False,): 
        """return the selected particle systems of this emitter, note that active psy is not considered as selected, will return a list"""

        if (all_emitters):
              emitters = bpy.context.scene.scatter5.get_all_emitters(search_mode="active_view_layer")
        else: emitters = [self.id_data]

        if (respect_ui_order):
              psys_sel = [itm.get_interface_item_source() for e in emitters for itm in e.scatter5.particle_interface_items if (itm.interface_item_type=='SCATTER_SYSTEM') and (itm.get_interface_item_source().sel)]
        else: psys_sel = [p for e in emitters for p in e.scatter5.particle_systems if p.sel]
            
        return psys_sel

    def add_psy_virgin(self, psy_name="", psy_color=None, psy_hide=True, deselect_all=False, instances=[], surfaces=[], default_group="",):
        """create virgin psy. Set up the collections, assign scatter_obj & geonodes, set addon_version, base name and color, 
        assign surfaces & instances, will always be hidden by default. Note that all this can be done manually by the user if needed, this function is simply a helper operation for the user""" 

        from .. import utils
        from .. handlers.overseer import Observer

        emitter    = self.id_data
        scat_scene = bpy.context.scene.scatter5
        scat_addon = addon_prefs()
        scat_data  = blend_prefs()
        psys       = emitter.scatter5.particle_systems

        #create scatter default collection
        utils.coll_utils.setup_scatter_collections()

        #deselect everything but new psys
        if (deselect_all):
            for p in psys:
                p.sel = False

        #create new scatter obj
        scatter_obj_name = f"scatter_obj : {psy_name}" #add default naming system for a scatter_obj
        scatter_obj = bpy.data.objects.new(scatter_obj_name, bpy.data.meshes.new(scatter_obj_name), )
        
        #initialize scatter_obj uuid
        _ = scatter_obj.scatter5.uuid
        
        #scatter_obj should never be selectable by user, not needed & outline is bad for performance
        scatter_obj.hide_select = True

        #scatter_obj should always be locked with null transforms
        utils.create_utils.lock_transform(scatter_obj)

        #we need to leave traces of the original emitter, in case of dupplication we need to identify the double
        scatter_obj.scatter5.original_emitter = emitter 
        
        #deduce psy_name from scatter obj, prefix will be done automatically by blender 
        psy_name = scatter_obj.name.split("scatter_obj : ")[1]

        #each scatter_obj should be in a psy collection
        geonode_coll = utils.coll_utils.create_new_collection(f"psy : {psy_name}", parent="Geo-Scatter Geonode", exclude_scenes=[sc for sc in bpy.data.scenes if sc!=bpy.context.scene], prefix=True,)
        geonode_coll.objects.link(scatter_obj)

        #add new psy data
        p = psys.add() 
    
        #assign scatter obj
        p.scatter_obj = scatter_obj
        
        #also assign distmesh, for custom .py based distribution algos that use the mesh data as scattered points
        scatter_obj.data.name = f".distmesh_manual_all:{p.uuid}"
        p.scatter_obj.scatter5.distmesh_manual_all = scatter_obj.data #by default all scatter_ob meshes are manual_all custom dist mesh
        p.scatter_obj.scatter5.distmesh_physics = bpy.data.meshes.new(f".distmesh_physics:{p.uuid}")

        #set name
        p.name = psy_name
        p.name_bis = psy_name

        #let track manager know that this psy and its emitter are not unknown duplicates/links/appends
        Observer.track_new_scatter_item(p)
        Observer.track_new_scatter_item(emitter)
        
        #hide on creation? better for performance..
        p.scatter_obj.hide_viewport = psy_hide

        #set color if defined
        if (psy_color is not None):
            p.s_color = ensure_rgba_colors(psy_color)

        #set version information
        engine_version = bl_info["engine_version"]
        p.addon_version = f"{bl_info['version'][0]}.{bl_info['version'][1]}"
        p.blender_version = bpy.app.version_string
        p.blendfile_uuid = scat_data.blendfile_uuid
        
        #add geonode scatter engine modifier to scatter object, note that some nodegroups need to always be unique
        m = utils.import_utils.import_and_add_geonode(p.scatter_obj,
            mod_name=engine_version,
            node_name=f".{engine_version}",
            blend_path=directories.blend_engine,
            show_viewport=False,
            is_unique=True,
            unique_nodegroups=[
                #NOTE: also need to update this list in bpy.ops.scatter5.fix_nodetrees()
                "s_distribution_projbezline",
                "s_distribution_manual",
                "s_distribution_manual.uuid_equivalence",
                "s_scale_random",
                "s_scale_grow",
                "s_scale_shrink",
                "s_scale_mirror",
                "s_rot_align_y",
                "s_rot_random",
                "s_rot_add",
                "s_rot_tilt",
                "s_abiotic_elev",
                "s_abiotic_slope",
                "s_abiotic_dir",
                "s_abiotic_cur",
                "s_abiotic_border",
                "s_pattern1",
                "s_pattern2",
                "s_pattern3",
                "s_gr_pattern1",
                "s_ecosystem_affinity",
                "s_ecosystem_repulsion",
                "s_ecosystem_density",
                "s_proximity_projbezarea_border",
                "s_proximity_repel1",
                "s_proximity_repel2",
                "s_push_offset",
                "s_push_dir",
                "s_push_noise",
                "s_push_fall",
                "s_wind_wave",
                "s_wind_noise",
                "s_instances_pick_color_textures",
                "s_visibility_cam",
                ],
            )

        #assign surfaces

        match len(surfaces):
            
            case 0:
                p.s_surface_method = "emitter"

            case 1:
                if (surfaces[0] is emitter):
                    p.s_surface_method = "emitter"
                else:
                    p.s_surface_method = "object"
                    p.s_surface_object = surfaces[0]

            case int():
                
                surfaces_coll = utils.coll_utils.create_new_collection(f"ScatterSurfaces", parent="Geo-Scatter Surfaces", prefix=True)
                for surf in surfaces: 
                    if (surf.name not in surfaces_coll.objects):
                        surfaces_coll.objects.link(surf)
                    continue

                #assign pointers
                p.s_surface_method = "collection"
                p.s_surface_collection = surfaces_coll.name

        #assign instances: 

        #create new instance collection
        instance_coll = utils.coll_utils.create_new_collection(f"ins_col : {p.name}", parent="Geo-Scatter Ins Col", prefix=True)
       
        #add instances in collection
        if (instances):
            for inst in instances:
                if (inst.name not in instance_coll.objects):
                    instance_coll.objects.link(inst)
                continue

        #assign pointers
        p.s_instances_coll_ptr = instance_coll

        #set in default group?
        if (default_group!=""):
            p.group = default_group

        #update interface by setting p as new active itm, always by default
        self.set_interface_active_item(item=p,)
        
        #set viewport activity for last to save on performances
        show_viewport_status = (not psy_hide) if (scat_addon.opti_also_hide_mod) else True
        if (m.show_viewport!=show_viewport_status):
            m.show_viewport = show_viewport_status

        #define main hide_viewport
        p.hide_viewport = psy_hide
        
        return p

    #  dP""b8 88""Yb  dP"Yb  88   88 88""Yb .dP"Y8
    # dP   `" 88__dP dP   Yb 88   88 88__dP `Ybo."
    # Yb  "88 88"Yb  Yb   dP Y8   8P 88"""  o.`Y8b
    #  YboodP 88  Yb  YbodP  `YbodP' 88     8bodP'

    particle_groups : bpy.props.CollectionProperty(type=SCATTER5_PR_particle_groups) #Children Collection

    def get_group_active(self):
        """get the group active in the particle_interface_items interface"""

        if (not self.particle_groups):
            return None 

        itm = self.get_interface_active_item()
        if ((itm is not None) and (itm.interface_item_type=='GROUP_SYSTEM')):
            return itm.get_interface_item_source()

        return None

    def cleanse_unused_particle_groups(self):
        """cleanse unused groups"""

        if (not self.particle_groups):
            return None

        used_groups = [ p.group for p in self.particle_systems if (p.group!="") ]

        if (not used_groups):
            self.particle_groups.clear()
            return None

        for i,g in enumerate(self.particle_groups):
            if (g.name not in used_groups) :
                self.particle_groups.remove(i)
            continue

        return None

    # 88""Yb    db    88""Yb 888888 88  dP""b8 88     888888     88     88 .dP"Y8 888888     88 88b 88 888888 888888 88""Yb 888888    db     dP""b8 888888
    # 88__dP   dPYb   88__dP   88   88 dP   `" 88     88__       88     88 `Ybo."   88       88 88Yb88   88   88__   88__dP 88__     dPYb   dP   `" 88__
    # 88"""   dP__Yb  88"Yb    88   88 Yb      88  .o 88""       88  .o 88 o.`Y8b   88       88 88 Y88   88   88""   88"Yb  88""    dP__Yb  Yb      88""
    # 88     dP""""Yb 88  Yb   88   88  YboodP 88ood8 888888     88ood8 88 8bodP'   88       88 88  Y8   88   888888 88  Yb 88     dP""""Yb  YboodP 888888
    
    particle_interface_items : bpy.props.CollectionProperty(
        type=SCATTER5_PR_particle_interface_items, #Children Collection
        options={'LIBRARY_EDITABLE',},
        ) 

    particle_interface_idx : bpy.props.IntProperty(
        update=on_particle_interface_interaction,
        options={'LIBRARY_EDITABLE',}, #make sure user can change this, even if linked and not editable
        name=translate("Scatter-Lister Interface"),
        description=translate("Scatter-System Selection:\n•Click on a system to set it active and reveal its properties.\n•Double click on a name to rename.\n•Shift-Click to conserve selection.\n•Alt-Click to isolate the selection viewport status")
        )
    
    def is_particle_interface_broken(self):
        """check if this object particle_interface_items is broken"""
        
        if (self.particle_interface_items):
            return any(e.get_interface_item_source() is None for e in self.particle_interface_items)
        return False
    
    def get_interface_active_item(self):

        if (len(self.particle_interface_items)==0):
            return None 

        if (0<=self.particle_interface_idx<len(self.particle_interface_items)): 
            return self.particle_interface_items[self.particle_interface_idx]

        return None

    def set_interface_active_item(self, item=None, item_type='SCATTER_SYSTEM', item_name="MyPsy",):
        """set interface items, either set by item directly, or set by item_type and item_name"""

        if (item is None):
            systems = self.particle_systems[:] if (item_type=='SCATTER_SYSTEM') else self.particle_groups[:] if (item_type=='GROUP_SYSTEM') else []
            for s in systems:
                if (s.name==item_name):
                    item = s
                    break
                continue
                    
        if (item is None):
            raise Exception(f"ERROR: set_interface_active_item(): Couldn't find the item you want to set active.. item_type='{item_type}',item_name='{item_name}'")

        #open the group if needed
        if (item.system_type=='SCATTER_SYSTEM'):
            if (item.group!=""):
                g = self.particle_groups[item.group]
                if (not g.open):
                    g.open = True

        self.id_data.scatter5.particle_interface_refresh()

        #set itm active via setting the indew IntProperty
        for i,itm in enumerate(self.particle_interface_items):
            if (itm.get_interface_item_source()==item):
                self.particle_interface_idx = i
                break
            continue

        return None

    def particle_interface_refresh(self):
        """object.scatter5.particle_interface_items will be constantly rebuild on major user interaction"""

        dprint("FCT: particle_interface_refresh()")

        #cleanse unused groups first, perhaps some need to be deleted! (exec topstack, important in order for get_interface_item_source() to get an accurate result )
        self.cleanse_unused_particle_groups()

        #save older interface before cleanse
        old_interface_active = None
        old_interface_items = [ ( itm.get_interface_item_source().name, itm.interface_item_type ) if (itm.get_interface_item_source() is not None) else ("",'DELETED') for itm in self.particle_interface_items]
        if (len(old_interface_items)) and (0<=self.particle_interface_idx<len(old_interface_items)):
            old_interface_active = old_interface_items[self.particle_interface_idx][:]

        #cleanse older interface
        self.particle_interface_items.clear()

        #if no psys, then no interface
        if (not self.particle_systems):
            return None

        #generate the new interface

        new_interface_items = old_interface_items[:]

        #remove ui items that got deleted, deleted if we cannot get their source!

        idx_before_removal = None #keep track of this, for setting active idx if needed
        for i,itm in enumerate(new_interface_items.copy()):
            if (itm[1]=='DELETED'):
                new_interface_items.remove(itm)
                if (idx_before_removal is None):
                    idx_before_removal = max(0,i-1)
            continue

        #add potential new psys itm + their groups

        new_item = None
        for p in self.particle_systems: 
            p_item = (p.name,'SCATTER_SYSTEM')
            
            #new group?
            if (p.group!=""):
                
                g_item = (p.group,'GROUP_SYSTEM')
                if (g_item not in new_interface_items):
                    
                    #if scatter already exists in list (it should!) the we insert element near scatter
                    if (p_item in new_interface_items):
                          new_interface_items.insert(new_interface_items.index(p_item),g_item)
                    else: new_interface_items.append(g_item) #else we consider the group as a new item (very improbable)

            #new scatters always added at the end
            if (p_item not in new_interface_items):
                new_item = p_item
                new_interface_items.append(p_item)
            
            continue 

        #ignore psy itms with group closed

        def get_psy_group(psy_itm):
            """get group tuple from psy tuple"""
            return (self.particle_systems[psy_itm[0]].group,'GROUP_SYSTEM') if (self.particle_systems[psy_itm[0]].group!="") else None

        vanish_index = None
        for itm in new_interface_items.copy():
            n,t = itm
            
            if (t=='SCATTER_SYSTEM'):
                pgroup = get_psy_group(itm)

                #if psy group exists and group is closed, we remove psy itm
                if (pgroup is not None): 
                    if (not self.particle_groups[pgroup[0]].open):
                        
                        new_interface_items.remove(itm)

                        #if the active item was just hidden, we make the active itm null
                        if ((old_interface_active==itm) and (vanish_index is None)):
                            vanish_index = True
            continue 

        #re-group psys near their groups, following list order

        for itm in reversed(new_interface_items.copy()):
            n,t = itm
            
            if (t=='SCATTER_SYSTEM'):
                
                pgroup = get_psy_group(itm)
                if (pgroup is not None):
                    assert pgroup in new_interface_items
                    new_interface_items.remove(itm)
                    new_interface_items.insert(new_interface_items.index(pgroup)+1, itm)
                    
            continue

        #python list to blender ui-list

        for n,t in new_interface_items:
            ui = self.particle_interface_items.add()
            ui.interface_item_type = t
            
            if (t=='SCATTER_SYSTEM'):
                ui.interface_item_psy_uuid = self.particle_systems[n].uuid
                
            elif (t=='GROUP_SYSTEM'):
                ui.interface_group_name = n
                
            continue

        #overview items indent_icon, define indents depending on sequence of scatter/groups items

        for i,itm in enumerate(self.particle_interface_items):
            
            if (itm.interface_item_type=='SCATTER_SYSTEM'):
                itm_source = itm.get_interface_item_source()
                if (itm_source and itm_source.group!=""):
                    
                    if (len(self.particle_interface_items)<=i+1):
                        itm.interface_ident_icon = "W_INDENT_LAST"
                        continue
                    
                    next_itm = self.particle_interface_items[i+1]
                    if (next_itm.interface_item_type=='GROUP_SYSTEM'):
                        itm.interface_ident_icon = "W_INDENT_LAST"
                        continue
                    
                    if (next_itm.get_interface_item_source().group!=""):
                        itm.interface_ident_icon = "W_INDENT_TREE"
                        continue
                    
                    itm.interface_ident_icon = "W_INDENT_LAST"
                    continue

        #overview items that need a separator

        for i,itm in enumerate(self.particle_interface_items):
            
            match itm.interface_item_type:
                
                case 'SCATTER_SYSTEM':
                    
                    #last psy element of group
                    if (itm.interface_ident_icon!=""):
                        if (itm.interface_ident_icon=="W_INDENT_LAST"):
                            itm.interface_add_separator = True
                        continue
                    
                    #non grouped psy with group below
                    if (i+1<len(self.particle_interface_items)):
                        next_itm = self.particle_interface_items[i+1]
                        if (next_itm.interface_item_type=='GROUP_SYSTEM'):
                            itm.interface_add_separator = True
                        continue

                case 'GROUP_SYSTEM':
                    
                    #non grouped psy located right before a group
                    if (i+1<len(self.particle_interface_items)):
                        next_itm = self.particle_interface_items[i+1]
                        if (next_itm.interface_ident_icon==""):
                            itm.interface_add_separator = True
                            
            continue

        #now for new active index..

        #if we just created a list, add the first item as active
        # if (len(old_interface_items)==0):
        #     self.particle_interface_idx = 0

        #if active item was in a now closed group, no more active item 
        if (vanish_index is not None):
            dprint("FCT: particle_interface_refresh(): (vanish_index is not None)")
            self.particle_interface_idx = -1

        #if there was no active items, simply add to latest
        # elif (old_interface_active is None):
        #     print("(old_interface_active is None)")
        #     self.particle_interface_idx = -1            
        #     self.particle_interface_idx = len(self.particle_interface_items)-1

        #if we have new items added in the list, select them 
        elif (new_item is not None) and (new_item in new_interface_items):
            dprint("FCT: particle_interface_refresh(): (new_item is not None) and (new_item in new_interface_items)")
            self.particle_interface_idx = new_interface_items.index(new_item)

        #if we have the same item still existing, select them
        elif (old_interface_active in new_interface_items):
            dprint("FCT: particle_interface_refresh(): (old_interface_active in new_interface_items)")
            self.particle_interface_idx = new_interface_items.index(old_interface_active)

        #final case, if we deleted the active item (along with others) choose last items
        elif (idx_before_removal is not None):
            dprint("FCT: particle_interface_refresh(): (idx_before_removal is not None)")
            self.particle_interface_idx = idx_before_removal

        #if there was no active idx to begin with, & we don't need to set something active?
        elif (old_interface_active is None):
            dprint("FCT: particle_interface_refresh(): (old_interface_active is None)")

        else: 
            #should not activate
            dprint("FCT: particle_interface_refresh(): else")

        return None 

    # .dP"Y8  dP"Yb  88   88    db    88""Yb 888888        db    88""Yb 888888    db
    # `Ybo." dP   Yb 88   88   dPYb   88__dP 88__         dPYb   88__dP 88__     dPYb
    # o.`Y8b Yb b dP Y8   8P  dP__Yb  88"Yb  88""        dP__Yb  88"Yb  88""    dP__Yb
    # 8bodP'  `"YoYo `YbodP' dP""""Yb 88  Yb 888888     dP""""Yb 88  Yb 888888 dP""""Yb
    
    #deeply linked with psy.get_surfaces_square_area

    estimated_square_area : bpy.props.FloatProperty(
        description="The estimated squarea area of the surface of this object",
        default=-1,
        )

    def estimate_square_area(self, eval_modifiers=True, get_selection=False, update_property=True,):
        """get the m² of this object mesh. carreful do not run this function in real time""" 
        
        object_area = 0
        o = self.id_data

        if (o.type=="MESH"):
            
            import numpy as np

            #evaluate mods?
            if (eval_modifiers):
                depsgraph = bpy.context.evaluated_depsgraph_get()
                eo = o.evaluated_get(depsgraph)
                ob = eo.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph,)
            else: ob = o.data

            ob.calc_loop_triangles()

            #get square area value
            tri_area = np.zeros(len(ob.loop_triangles), dtype=np.float64, )
            ob.loop_triangles.foreach_get('area', tri_area, )

            #selection influence?
            if (get_selection):
                tri_sel = np.asarray([float(ob.polygons[t.polygon_index].select) for t in ob.loop_triangles])
                tri_area *= tri_sel #if tri in sel *1 else *0

            object_area = np.sum(tri_area)

            #Check for NaN values
            if (np.isnan(object_area)):
                tri_area = tri_area[~(np.isnan(tri_area))]
                object_area = np.sum(tri_area)

            dprint(f"FCT: 'bpy.data.objects[`{o.name}`].scatter5.estimate_square_area() == {object_area}m²'", depsgraph=False)

        #Not mesh object? We might need to support curveobject or metaball perhaps someday?
        else:
            dprint(f"FCT: 'bpy.data.objects[`{o.name}`].scatter5.estimate_square_area(): Object-Type is not Mesh...", depsgraph=False)

        #write result? if selection method never write
        if ((update_property) and (not get_selection)):
            self.estimated_square_area = object_area

        return object_area

    # 888888    db     dP""b8 888888     88""Yb 88""Yb 888888 Yb    dP 88 888888 Yb        dP
    # 88__     dPYb   dP   `" 88__       88__dP 88__dP 88__    Yb  dP  88 88__    Yb  db  dP
    # 88""    dP__Yb  Yb      88""       88"""  88"Yb  88""     YbdP   88 88""     YbdPYbdP
    # 88     dP""""Yb  YboodP 888888     88     88  Yb 888888    YP    88 888888    YP  YP
            
    s_visibility_facepreview_area : bpy.props.FloatProperty(
        description="The estimated squarea area of the surface of this object, for the selection zone of the s_visibility_facepreview scatter feature",
        default=0,
        )

    # 88""Yb 888888 88""Yb      dP""b8    db    8b    d8 888888 88""Yb    db        .dP"Y8 888888 888888 888888 88 88b 88  dP""b8 .dP"Y8
    # 88__dP 88__   88__dP     dP   `"   dPYb   88b  d88 88__   88__dP   dPYb       `Ybo." 88__     88     88   88 88Yb88 dP   `" `Ybo."
    # 88"""  88""   88"Yb      Yb       dP__Yb  88YbdP88 88""   88"Yb   dP__Yb      o.`Y8b 88""     88     88   88 88 Y88 Yb  "88 o.`Y8b
    # 88     888888 88  Yb      YboodP dP""""Yb 88 YY 88 888888 88  Yb dP""""Yb     8bodP' 888888   88     88   88 88  Y8  YboodP 8bodP'

    #scale fading 
    s_scale_fading_distance_per_cam_min : bpy.props.FloatProperty(
        name=translate("Start"),
        description=translate("Starting this distance, we will start a transition effect until the 'end' distance value"),
        default=30,
        subtype="DISTANCE",
        min=0,
        soft_max=200, 
        #update done by depsgraph handler camera loop
        )
    s_scale_fading_distance_per_cam_max : bpy.props.FloatProperty(
        name=translate("End"),
        description=translate("After this distance the effect will end"),
        default=40,
        subtype="DISTANCE",
        min=0,
        soft_max=200, 
        #update done by depsgraph handler camera loop
        )

    #clipping fov boost 
    s_visibility_camclip_per_cam_boost_xy : bpy.props.FloatVectorProperty(
        name=translate("FOV Boost"),
        description=translate("Boost the frustrum visibility angle of the active camera"),
        subtype="XYZ",
        size=2,
        default=(0,0),
        soft_min=-2,
        soft_max=2, 
        precision=3,
        #update done by depsgraph handler camera loop
        )

    #culling distance 
    s_visibility_camdist_per_cam_min : bpy.props.FloatProperty(
        name=translate("Start"),
        description=translate("Starting this distance, we will start a distance culling transition until the end distance"),
        subtype="DISTANCE",
        default=10,
        min=0,
        soft_max=200, 
        #update done by depsgraph handler camera loop
        )
    s_visibility_camdist_per_cam_max : bpy.props.FloatProperty(
        name=translate("End"),
        description=translate("After this distance all instances will be culled"),
        subtype="DISTANCE",
        default=40,
        min=0,
        soft_max=200, 
        #update done by depsgraph handler camera loop
        )

    # 88""Yb 88""Yb  dP"Yb   dP""b8 888888 8888b.  88   88 88""Yb    db    88         8b    d8    db    .dP"Y8 88  dP
    # 88__dP 88__dP dP   Yb dP   `" 88__    8I  Yb 88   88 88__dP   dPYb   88         88b  d88   dPYb   `Ybo." 88odP
    # 88"""  88"Yb  Yb   dP Yb      88""    8I  dY Y8   8P 88"Yb   dP__Yb  88  .o     88YbdP88  dP__Yb  o.`Y8b 88"Yb
    # 88     88  Yb  YbodP   YboodP 888888 8888Y"  `YbodP' 88  Yb dP""""Yb 88ood8     88 YY 88 dP""""Yb 8bodP' 88  Yb

    mask_systems : bpy.props.CollectionProperty(type=SCATTER5_PR_procedural_vg) #Children Collection
    mask_systems_idx : bpy.props.IntProperty()

    '''
    # manual physics brush private properties for simulation objects.. used only during simulation while brush is running, hope i did not add some circular dependency..
    manual_physics_brush_object_properties: bpy.props.PointerProperty(type=SCATTER5_manual_physics_brush_object_properties, )
    '''
