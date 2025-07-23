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
import os

from . import coll_utils

from . extra_utils import dprint


#NOTE General Import/Export functions that can be used a bit everywhere 

def file_path_exists(blend_path, message_type=""):
    """warn users of non-existing file"""
    
    if (not os.path.exists(blend_path)):
        from .. translations import translate
        
        if (message_type=='geonode'):
            bpy.ops.scatter5.popup_dialog(
                'INVOKE_DEFAULT',
                msg=translate("Dear user, this plugin is an interface that control geometry-nodes setups.\nWe tried to find and import a nodegroup from this file but couldn't find it.")+f"\n\n'{blend_path}'\n",
                header_title=translate("Nodegroup Not Found"),
                header_icon="INFO",
                )
        return False
        
    return True


#  dP""b8 888888  dP"Yb  88b 88  dP"Yb  8888b.  888888
# dP   `" 88__   dP   Yb 88Yb88 dP   Yb  8I  Yb 88__
# Yb  "88 88""   Yb   dP 88 Y88 Yb   dP  8I  dY 88""
#  YboodP 888888  YbodP  88  Y8  YbodP  8888Y"  888888


def import_geonodes(blend_path, geonode_names, link=False, ):
    """import geonode(s) from given blend_path"""
    return_list=[]
    
    if (not file_path_exists(blend_path, message_type='geonode')):
        return [None]
        
    with bpy.data.libraries.load(blend_path, link=link) as (data_from, data_to):
        
        #loop over every nodegroups in blend
        for g in data_from.node_groups:
            
            #check for name
            if g in geonode_names:
                
                #add to return list 
                if g not in return_list:
                    return_list.append(g)
                    
                #check if not already imported
                if g not in bpy.data.node_groups:
                    # add to import list  
                    data_to.node_groups.append(g)
                    
            continue

    if (len(return_list)==0):
        return [None]

    return return_list


def import_and_add_geonode(o, mod_name="", node_name="", blend_path="", use_fake_user=True, is_unique=False, unique_nodegroups=[], show_viewport=True,):
    """Create a geonode modifier, import node from blend path if does not exist in user file
    use 'unique_nodegroups' argument to automatically make nodegroups contained within this modifier unique"""

    #create new modifier that will gost geonode
    m = o.modifiers.new(name=mod_name,type="NODES")
    
    #hide for optimization
    m.show_viewport = False
    
    #get geonodegraph
    geonode = bpy.data.node_groups.get(node_name)
    
    #import geonodegraph if not already in blend?
    if (geonode is None):
        import_geonodes(blend_path,[node_name],)
        geonode = bpy.data.node_groups.get(node_name)
    
    #couldn't import? simply return the modifier with no nodegroup assigned
    if (geonode is None):
        return m
    
    #add fake user
    geonode.use_fake_user = use_fake_user
        
    #does the nodegroup shall be unique? 
    if (is_unique):
        geonode = geonode.copy()

    #control if some nodegroups in this geonodegraph needs to be unique ?
    if (unique_nodegroups):
        for nm in unique_nodegroups:
            
            #support up to 1x level nested (ex "s_distribution_manual.uuid_equivalence")
            if ("." in nm):
                  nm, nnm, *_ = nm.split(".")
            else: nnm = None

            #get node
            n = geonode.nodes.get(nm)
            
            if (n is None):
                print("ERROR: import_and_add_geonode(): failed to nodes.get() ",nm)
                continue
                
            #support 1x level nested?
            if (nnm is not None):
                nn = n.node_tree.nodes.get(nnm)
                
                if (nn is None):
                    print("ERROR: import_and_add_geonode(): failed to nodes.get() ",nnm)
                    continue
                
                nn.node_tree = nn.node_tree.copy()
                continue

            n.node_tree = n.node_tree.copy()    
            continue

    #assign nodegraph to modifier
    m.node_group = geonode

    #NO LONGER AN ISSUE?
    #correct potential bug, unconnected nodes!
    # from .. scattering.update_factory import ensure_buggy_links
    # ensure_buggy_links()
    
    if (m.show_viewport!=show_viewport):
        m.show_viewport = show_viewport
    
    return m 


#  dP"Yb  88""Yb  88888 888888  dP""b8 888888 .dP"Y8
# dP   Yb 88__dP     88 88__   dP   `"   88   `Ybo."
# Yb   dP 88""Yb o.  88 88""   Yb        88   o.`Y8b
#  YbodP  88oodP "bodP' 888888  YboodP   88   8bodP'


def import_objects( blend_path="", object_names=[], link=False, link_coll="Geo-Scatter Import",):
    """import obj(s) from given blend_path"""

    #if all object names are already imported, then we simply skip this function
    if all([n in bpy.data.objects for n in object_names]):
        return object_names

    dprint(f"FCT: import_objects({os.path.basename(blend_path)}): -start")

    r_list=[]

    with bpy.data.libraries.load(blend_path, link=link) as (data_from, data_to):
        
        #loop over every obj in blend
        for g in data_from.objects:
            
            #check if name in selected and not import twice
            if (g in object_names) and (g not in r_list):
                r_list.append(g)
                
                #import in data.objects if not already exists in this blend of course!
                if (g not in bpy.data.objects):
                    data_to.objects.append(g)
            
            continue

    dprint(f"FCT: import_objects({os.path.basename(blend_path)}): -bpy.data.libraries.load() done")

    #Nothing found ?
    if (len(r_list)==0):
        return [None]

    #cleanse asset mark?
    for n in r_list:
        o = bpy.data.objects.get(n)
        
        if (o is None):
            continue
        
        if (o.asset_data is None):
            continue
        
        o.asset_clear()
        continue

    #store import in collection?
    if (link_coll not in (None,""),):
        
        #create Geo-Scatter collections if not already
        coll_utils.setup_scatter_collections()
        
        #get collection, create if not found
        import_coll = coll_utils.create_new_collection(link_coll, parent="Geo-Scatter",)
        
        #always move imported in collection
        for n in r_list:
            if (n not in import_coll.objects):
                import_coll.objects.link(bpy.data.objects[n])
                
    dprint(f"FCT: import_objects({os.path.basename(blend_path)}): -end")

    return r_list


def export_objects( blend_path, objects_list, ):
    """export obj in a new .blend"""

    data_blocks = set(objects_list)
    bpy.data.libraries.write(blend_path, data_blocks, )

    return None


#    db    .dP"Y8 .dP"Y8 888888 888888     88""Yb 88""Yb  dP"Yb  Yb        dP .dP"Y8 888888 88""Yb
#   dPYb   `Ybo." `Ybo." 88__     88       88__dP 88__dP dP   Yb  Yb  db  dP  `Ybo." 88__   88__dP
#  dP__Yb  o.`Y8b o.`Y8b 88""     88       88""Yb 88"Yb  Yb   dP   YbdPYbdP   o.`Y8b 88""   88"Yb
# dP""""Yb 8bodP' 8bodP' 888888   88       88oodP 88  Yb  YbodP     YP  YP    8bodP' 888888 88  Yb


def get_selected_assets(window=None, filter_id_type=['OBJECT','COLLECTION',],):
    """get the selected assets, of all areas of all windows or optionally given window only"""
    
    ass_ets = set()

    if (not bpy.context.window_manager):
        print("ERROR: get_selected_assets(): Headless mode not supported for this function")
        return ass_ets
    
    if (window):
          windows = [window]
    else: windows = bpy.context.window_manager.windows
        
    for w in windows:
        if (w.screen):
            for a in w.screen.areas:
                if (a.ui_type=='ASSETS'):
                    C = bpy.context
                    with C.temp_override(window=w,area=a):
                        if (C.selected_assets):
                            for ass in C.selected_assets:
                                if (filter_id_type):
                                    if (ass.id_type in filter_id_type):
                                        ass_ets.add(ass)
                                else:
                                    ass_ets.add(ass)
    return ass_ets


def import_selected_assets(link=False, link_coll="Geo-Scatter Import",):
    """import selected object type assets from browser, link/append depends on technique"""

    #define and get globals via operators in order to override contexts
    ass_ets = get_selected_assets()
    
    #did we found something?
    if (len(ass_ets)==0):
        return []
    
    #then we import the assets

    #sort assets by path in order to batch import them
    to_import = {}
    
    for ass in ass_ets:
        if (not hasattr(ass,"full_library_path")):
            continue
        
        p = ass.full_library_path
        if (p not in to_import.keys()):
            to_import[p] = set()
            
        to_import[p].add(ass.name)
        continue

    #and create the return value list
    imported_objs = []
    
    #create Geo-Scatter collections if not already
    coll_utils.setup_scatter_collections()
    
    #import assets from path 
    for p,names in to_import.items():
        
        #import all the objects/collection objects
        import_objects(blend_path=p, object_names=names, link=link,)
        
        #mark them as found
        for n in names:
            o = bpy.data.objects.get(n)
            if (o):
                imported_objs.append(o)
                
        continue
        
    return imported_objs 


# 8b    d8    db    888888 888888 88""Yb 88    db    88
# 88b  d88   dPYb     88   88__   88__dP 88   dPYb   88
# 88YbdP88  dP__Yb    88   88""   88"Yb  88  dP__Yb  88  .o
# 88 YY 88 dP""""Yb   88   888888 88  Yb 88 dP""""Yb 88ood8


def import_materials(blend_path, material_names, link=False,):
    """import materials by name into blender data"""

    #if all material names are already imported, then we simply skip this function
    if all([n in bpy.data.materials for n in material_names]):
        return material_names

    r_list=[]

    with bpy.data.libraries.load(blend_path, link=link) as (data_from, data_to):
        
        #loop over every nodegroups in blend
        for g in data_from.materials:
            
            #check for name
            if (g in material_names):
                
                #add to return list 
                if (g not in r_list):
                    r_list.append(g)
                    
                #check if not already imported
                if (g not in bpy.data.materials):
                    # add to import list  
                    data_to.materials.append(g)
                    
            continue

    if (len(r_list)==0):
        return [None]

    return r_list


# 88 8b    d8    db     dP""b8 888888
# 88 88b  d88   dPYb   dP   `" 88__
# 88 88YbdP88  dP__Yb  Yb  "88 88""
# 88 88 YY 88 dP""""Yb  YboodP 888888


def import_image(fpath, hide=False, use_fake_user=False):
    """import images in bpy.data.images"""

    if (not os.path.exists(fpath)):
        return None 

    fname = os.path.basename(fpath)
    if (hide):
        fname = "." + fname

    image = bpy.data.images.get(fname)
    if (image is None):
        image = bpy.data.images.load(fpath) 
        image.name = fname

    image.use_fake_user=use_fake_user
    return image 


# 888888 Yb  dP 88""Yb  dP"Yb  88""Yb 888888     .dP"Y8 888888 88""Yb 88    db    88     88 8888P    db    888888 88  dP"Yb  88b 88
# 88__    YbdP  88__dP dP   Yb 88__dP   88       `Ybo." 88__   88__dP 88   dPYb   88     88   dP    dPYb     88   88 dP   Yb 88Yb88
# 88""    dPYb  88"""  Yb   dP 88"Yb    88       o.`Y8b 88""   88"Yb  88  dP__Yb  88  .o 88  dP    dP__Yb    88   88 Yb   dP 88 Y88
# 888888 dP  Yb 88      YbodP  88  Yb   88       8bodP' 888888 88  Yb 88 dP""""Yb 88ood8 88 d8888 dP""""Yb   88   88  YbodP  88  Y8


def serialization(d):
    """convert unknown blendertypes"""

    from mathutils import Euler, Vector, Color

    for key,value in d.items():
        
        #convert blender array type to list
        if (type(value) in [Euler, Vector, Color, bpy.types.bpy_prop_array]):
            d[key] = value[:] 
            
        #recursion needed for pattern texture data storage for example
        elif (type(value)==dict):
            d[key] = serialization(value)
        continue

    return d


#   .oooooo.   oooo
#  d8P'  `Y8b  `888
# 888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
# 888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
# 888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
# `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#  `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'


classes = (
        
    )