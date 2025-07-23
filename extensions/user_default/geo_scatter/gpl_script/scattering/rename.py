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
#  888   .d88'  .ooooo.  ooo. .oo.    .oooo.   ooo. .oo.  .oo.    .ooooo.
#  888ooo88P'  d88' `88b `888P"Y88b  `P  )88b  `888P"Y88bP"Y88b  d88' `88b
#  888`88b.    888ooo888  888   888   .oP"888   888   888   888  888ooo888
#  888  `88b.  888    .o  888   888  d8(  888   888   888   888  888    .o
# o888o  o888o `Y8bod8P' o888o o888o `Y888""8o o888o o888o o888o `Y8bod8P'
#
#####################################################################################################


import bpy

from .. utils.extra_utils import dprint
from .. utils.coll_utils import get_collection_by_name
from .. translations import translate


def rename_particle(self,context):
    
    from ... __init__ import blend_prefs
    scat_data  = blend_prefs()
    scat_scene = bpy.context.scene.scatter5
    
    emitter = self.id_data
    scatter_obj_name = f"scatter_obj : {self.name}"

    #deny update if no changes detected 
    if (self.name==self.name_bis):
        return None 
    
    #deny update if empty name 
    elif ( (self.name=="") or self.name.startswith(" ") ):
        self.name = self.name_bis
        bpy.ops.scatter5.popup_menu(msgs=translate("Name cannot be None, Please choose another name"),title=translate("Renaming Impossible"),icon="ERROR")
        return None
    
    #deny update if name already taken by another scatter_obj 
    elif (scatter_obj_name in [o.name for o in bpy.data.objects if o.name.startswith("scatter_obj : ") and not o.library]):
        if (self.name_bis!=""): #No update on creation
            self.name = self.name_bis
            bpy.ops.scatter5.popup_menu(msgs=translate("This name is taken, Please choose another name"),title=translate("Renaming Impossible"),icon="ERROR")
            return None

    dprint(f"PROP_FCT: updating name : {self.name_bis}->{self.name}")

    #change the scatter_obj & geonode_coll names
    if ((self.scatter_obj is not None) and (self.name_bis!="")):

        #change geonode collection name, if found
        geonode_coll = get_collection_by_name(f"psy : {self.name_bis}")
        if (geonode_coll):
            geonode_coll.name = f"psy : {self.name}"
       
        #change scatter obj name
        self.scatter_obj.name = scatter_obj_name

    #rename default instance_coll
    if (self.scatter_obj is not None):
        ins_coll = get_collection_by_name(f"ins_col : {self.name_bis}")
        if (ins_coll and ins_coll==self.s_instances_coll_ptr):
            ins_coll.name = f"ins_col : {self.name}"

    #loop channels & update members names
    if (scat_data.sync_channels):
        for ch in scat_data.sync_channels:

            #change channels name
            if (ch.name==self.name_bis):
                ch.name = self.name

            #change channel members
            if ((ch.members) and ch.name_in_members(self.name_bis)):
                for m in ch.members:
                    if (m.psy_name==self.name_bis):
                        m.psy_name = self.name
                    continue

            continue

    #change ecosystem relation names?
    for p in emitter.scatter5.particle_systems:
        for prop_name in [n.replace('XX',f'{i:02d}') for n in ('s_ecosystem_affinity_XX_ptr','s_ecosystem_repulsion_XX_ptr','s_ecosystem_density_XX_ptr',) for i in range(1,4)]:
            val = getattr(p,prop_name)
            if ((val) and (val==self.name_bis)):
                setattr(p,prop_name,self.name)
                continue

    #change name_bis name
    self.name_bis = self.name 

    return None


def rename_group(self,context):
    """special update name function for renaming a group"""

    emitter = self.id_data

    #should only happend on creation
    if (self.name_bis==""):
        self.name_bis=self.name
        return None

    #deny update if no changes detected 
    if (self.name==self.name_bis):
        return None 
    
    #deny update if empty name 
    elif ((self.name=="") or self.name.startswith(" ")):
        self.name = self.name_bis
        bpy.ops.scatter5.popup_menu(msgs=translate("Name cannot be None, Please choose another name"),title=translate("Renaming Impossible"),icon="ERROR")
        return None
    
    #deny update if name already taken by another scatter_obj 
    elif (self.name in [g.name_bis for g in emitter.scatter5.particle_groups]):
        self.name = self.name_bis
        bpy.ops.scatter5.popup_menu(msgs=translate("This name is taken, Please choose another name"),title=translate("Renaming Impossible"),icon="ERROR")
        return None

    #rename group psys
    for p in emitter.scatter5.particle_systems:
        if (p.group!=""):
            if (p.group==self.name_bis):
                p.group = self.name
        continue

    #rename interface names
    for itm in emitter.scatter5.particle_interface_items:
        if (itm.interface_group_name!=""):
            if (itm.interface_group_name==self.name_bis):
                itm.interface_group_name = self.name
        continue

    #change name_bis name
    self.name_bis = self.name 

    return None
    