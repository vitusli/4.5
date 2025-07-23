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

#NOTE Here it's a bunch of functions related to collection 

def view_layer_collection_children_recursive(view_layer):
    """get all view_layer.layer_collection (like collection.children_recursive)"""
    
    def recur_layer_collection(layer_collection,all_vl,):
        """collect all viewlayer collections children in a given layer collection"""
        
        if (len(layer_collection.children)!=0):
            all_vl += layer_collection.children
            
            for ch in layer_collection.children:
                recur_layer_collection(ch,all_vl)
                
        return all_vl

    return recur_layer_collection(view_layer.layer_collection,[])


def get_collection_view_layer_exclude(collection, view_layer=None):
    """get the given collection"""

    if (view_layer is None):
        view_layer = bpy.context.view_layer
    
    excludes = []
    for lc in view_layer_collection_children_recursive(view_layer):
        if (lc.collection==collection):
            excludes.append(lc.exclude)
            
    return all(excludes)


def set_collection_view_layers_exclude(collection, view_layers="all", scenes="all", hide=True,):
    """set a collection view_layer exclude, for all given view_layers, for all given scenes"""
    
    acted = False

    if (scenes=="all"):
        scenes = bpy.data.scenes[:]

    for s in scenes:
        
        if (view_layers=="all"):
              vlys = s.view_layers
        else: vlys = [v for v in s.view_layers if v in view_layers]
            
        for v in vlys:
            for lc in view_layer_collection_children_recursive(v):
                
                if (lc.collection==collection):
                    if (lc.exclude!=hide):
                        lc.exclude = hide
                        acted = True
    
    return acted


def collection_clear(collection):
    """unlink all items (obj/coll) from a given collection"""

    for obj in collection.objects:
        collection.objects.unlink(obj)
        
    for coll in collection.children:
        collection.children.unlink(coll)

    return None


def get_collection_by_name(name):
    """can't use bpy.data.collections.get(name) because it may return linked collection and break everything"""
    
    for c in bpy.data.collections:
        if (c.name==name and not c.library):
            return c
    
    return None


# def set_collection_active(name="", scene=False):
#     """Set collection active by name, return False if failed."""

#     return (active_coll !=None)


# def close_collection_areas():
#     """close level on all outliner viewlayer area"""

#     for a in bpy.context.window.screen.areas:
#         if (a.type=="OUTLINER"):
#             if (a.spaces[0].display_mode=="VIEW_LAYER"):
#                 with bpy.context.temp_override(area=a,region=a.regions[0]):
#                     bpy.ops.outliner.show_one_level(open=False)
#                     bpy.ops.outliner.show_one_level(open=False)
#                     bpy.ops.outliner.show_one_level(open=False)
#                 a.tag_redraw()

#     return None 


def create_new_collection(name, parent=None, prefix=False, exclude_scenes=None,):
    """Create new collection and link in given parent (if not None)."""
    
    assert parent is not None
    assert type(parent) in (bpy.types.Scene, str, bpy.types.Collection,), "ERROR: create_new_collection(): Wrong Parent Argument Given"
    
    #we ignore linked collection, otherwise will create issues
    collnotlinked = [c for c in bpy.data.collections if not c.library]
    
    #if prefix, == will guarantee to create a new colleciton each time, 
    #otherwise will just get the existing colleciton with given name 
    #should be called "suffix" not prefix... anyway...
    if (prefix):
        from .. utils.str_utils import find_suffix
        name = find_suffix(name,[c.name for c in collnotlinked],)
    
    #Create the new collection if not exists
    is_init = False
    c = get_collection_by_name(name)
    if (c is None):
        c = bpy.data.collections.new(name=name)
        is_init = True
    
    #now we need to link the collection somewhere..
    
    #if passed a scene, we directly link to scene
    if (type(parent) is bpy.types.Scene):
        
        sccoll = parent.collection
        # then we simply link the collection to the context scene
        if (c not in sccoll.children_recursive[:]):
            sccoll.children.link(c)
    
    #else we link it to parent collection 
    elif (type(parent) in (str,bpy.types.Collection,)):
        
        #if we passed a string, then we try to find the coll by name
        if (type(parent) is str):
            parent = get_collection_by_name(parent)
            #assertion error print..
            if (parent is None):
                print(f"ERROR: create_new_collection(): collection '{parent}' not found.. Fallback on scene.. This shoudln't happen..")
                parent = bpy.context.scene.collection
                    
        #ensure collection in parent
        if (c not in parent.children[:]):
            parent.children.link(c)
            
        #ensure our coll is the only parent
        for col in collnotlinked:
            if (col!=parent):
                if (c in col.children[:]):
                    col.children.unlink(c)

    #if new, exclude on creation if needed
    if (is_init and exclude_scenes):
        set_collection_view_layers_exclude(c, scenes=exclude_scenes, hide=True,)

    return c 


def setup_scatter_collections(scene=None):
    """Create the Geo-Scatter collection for the context scene"""

    #if no scene arg passed, we work with context
    if (scene is None):
        scene = bpy.context.scene
        
    #we ignore linked collection, otherwise will create issues
    collnotlinked = [c for c in bpy.data.collections if not c.library]
    
    #versioning: legacy collection rename
    for col in collnotlinked:
        if (col.name.startswith("Scatter5")):
            col.name = col.name.replace("Scatter5","Geo-Scatter")
        continue

    gscol = get_collection_by_name("Geo-Scatter")
    is_init = (gscol is None)
    is_relink = (not is_init) and (gscol not in scene.collection.children[:])  

    gscol = create_new_collection("Geo-Scatter", parent=scene,)
    create_new_collection("Geo-Scatter Geonode", parent=gscol,)
    create_new_collection("Geo-Scatter Ins Col", parent=gscol, exclude_scenes="all",)
    create_new_collection("Geo-Scatter Import", parent=gscol, exclude_scenes="all",)
    create_new_collection("Geo-Scatter Extra", parent=gscol, exclude_scenes="all",)
    create_new_collection("Geo-Scatter Surfaces", parent=gscol, exclude_scenes="all",)
    create_new_collection("Geo-Scatter User Col", parent=gscol,)
    create_new_collection("Geo-Scatter Export", parent=gscol,)
    
    #if is a relink, it means the collection is linked in a new scene, and therefore we need to ensure viewlayers
    if (is_relink):
        ensure_scatter_collection_viewlayers(scene=scene)
        
    return gscol


def ensure_scatter_collection_viewlayers(scene=None):
    """Because the 'Geo-Scatter' collection regroup all psys ever made, and is appended on all scenes, 
    we need to make sure the Geonode collection containing the psy collections are all accurate regarding the existing psys system """
    
    #if no scene arg passed, we work with context
    if (scene is None):
        scene = bpy.context.scene
        
    #if the scene we are working with only has one viewlayer, we work with this one, otherwise, we are forced to work with bpy.context.viewl_layer
    if (len(scene.view_layers)==1):
          scn_viewly = scene.view_layers[0]
    else: scn_viewly = bpy.context.view_layer
    
    #we first ensure that viewlayers of these collections are hidden, always should be. (plus when append a Geo-Scatter collection or scene, we'll need to hide them to get accurate viewlayers in loop right below)
    for name in ("Geo-Scatter Ins Col","Geo-Scatter Import","Geo-Scatter Surfaces"):
        col = get_collection_by_name(name)
        if (col):
            for ch in col.children:
                set_collection_view_layers_exclude(ch, scenes=[scene], hide=True,)
            set_collection_view_layers_exclude(col, scenes=[scene], hide=True,)

    #for all psys with valid scatter_obj and original_emitter ptr
    for p in [p for p in scene.scatter5.get_all_psys(search_mode="all", also_linked=True) if p.scatter_obj and p.scatter_obj.scatter5.original_emitter]:
        oe = p.scatter_obj.scatter5.original_emitter
        #we hide the "psy : " coll if the original_emitter is not in viewlayer
        for c in [c for c in p.scatter_obj.users_collection if c.name.startswith(f"psy : {p.name}")]:
            set_collection_view_layers_exclude(c, scenes=[scene], hide=(oe not in scn_viewly.objects[:]),)
            break
        
    return None


def cleanup_scatter_collections(
        psys=None,
        scene=None,
        options={
            "unlink_distmeshes":True,
            "clean_placeholders":True,
            "ensure_single_gscol_ins":True,
            "ensure_no_gscol_dupp":True,
            "ensure_p_psy_col":True,
            "plus_reset_so_in_psy_col":False,
            "ensure_p_ins_col":True,
            "ensure_p_surf_col":True,
            "remove_unused_colls":True,
            "ensure_viewlayers":True,
        },
    ):
    """clean up the 'Geo-scatter' collection"""
    
    #if no scene arg passed, we work with context
    if (psys is None):
        psys = bpy.context.scene.scatter5.get_all_psys(search_mode="all", also_linked=True)
    if (scene is None):
        scene = bpy.context.scene

    #ensure base collection is here
    gscol = setup_scatter_collections(scene=scene)
    
    #make sure there are no distmeshes in user scene, this should be hidden
    if (options.get("unlink_distmeshes")):
        
        for c in [c for c in scene.collection.children_recursive if not c.library]:
            for o in [o for o in c.objects if o.name.startswith(".distmesh_")]:
                c.objects.unlink(o)
    
    #make sure there are no placeholder collection left somewhere, can happen on append operation
    if (options.get("clean_placeholders")):
        
        for c in [c for c in scene.collection.children_recursive if not c.library]:
            if c.name.startswith("Geo-Scatter Placeholders"):
                #in base scene?
                if (c.name in scene.collection.children):
                    scene.collection.children.unlink(c)
                    break
                #in any other scenes?
                for parent in scene.collection.children_recursive:
                    if (c.name in parent.children):
                        if (not parent.library):
                            parent.children.unlink(c)
                            break
                break
    
    #make sure there's only one instance of the geo-scatter collection in the file, if not, unlink all Geo-Scatter systems
    if (options.get("ensure_single_gscol_ins")):
        
        if len([c for c in scene.collection.children_recursive if c.name=="Geo-Scatter" and not c.library])>1:
            
            #remove our col from any other collection
            for c in scene.collection.children_recursive:
                if (gscol in c.children[:]):
                    if (not c.library):
                        c.children.unlink(gscol)
                    
            if (gscol not in scene.collection.children[:]):
                scene.collection.children.link(gscol)
        
    #make sure user did not dupplicate our collection
    if (options.get("ensure_no_gscol_dupp")):
            
        if [c for c in scene.collection.children_recursive if c.name.startswith("Geo-Scatter.") and not c.library]:
                
            # Iterate over the target collections
            for name in ("Geo-Scatter Geonode","Geo-Scatter Ins Col","Geo-Scatter Import","Geo-Scatter Extra","Geo-Scatter User Col","Geo-Scatter Surfaces","Geo-Scatter Export","Geo-Scatter"):
                original = bpy.data.collections.get(name)
                
                # Find any duplicated collections with .001, .002, etc.
                for c in bpy.data.collections:
                    if c.name.startswith(f"{name}."):
                        
                        # Transfer all objects from the duplicate collection to the original collection
                        for obj in c.objects:
                            if (obj not in original.objects[:]):
                                original.objects.link(obj)
                            if (not c.library):
                                c.objects.unlink(obj)
                            continue
                        
                        # Transfer all sub-collections (children) from the duplicate to the original
                        for child_col in c.children:
                            if (child_col not in original.children[:]):
                                original.children.link(child_col)
                            if (not c.library):
                                c.children.unlink(child_col)
                            continue
                        
                        if (not c.library):
                            bpy.data.collections.remove(c)
                        
                    continue
                continue
        
    #for each psys...
    
    for p in psys:
        
        #check if scatter obj is in the correct "psy : " collection
        if (options.get("ensure_p_psy_col")):
            
            geonode_coll = bpy.data.collections.get("Geo-Scatter Geonode")
            psy_coll = p.get_scatter_psy_collection(strict=True)
            if (psy_coll is None):
                
                #each scatter_obj should be in a psy collection
                psy_coll = create_new_collection(f"psy : {p.name}{' -linked' if p.is_linked else ''}", parent="Geo-Scatter Geonode", exclude_scenes=[sc for sc in bpy.data.scenes if sc!=scene],)
            
            if (options.get("plus_reset_so_in_psy_col")):
                
                #unlink scatter_obj from any other collection in scene (this might be problematic if users did some collections manipulation)
                for c in (scene.collection.children_recursive[:]+[scene.collection]):
                    if (p.scatter_obj in c.objects[:]):
                        if (not c.library):
                            c.objects.unlink(p.scatter_obj)
                
            #link new obj
            if (p.scatter_obj not in psy_coll.objects[:]):
                psy_coll.objects.link(p.scatter_obj)
                
            #ensure psy coll is in generic geonode collection
            if (psy_coll not in geonode_coll.children[:]):
                geonode_coll.children.link(psy_coll)
        
        #check if ins_col is in correct 
        if (options.get("ensure_p_ins_col")):
            
            if (p.s_instances_coll_ptr):
                
                ins_col = bpy.data.collections.get("Geo-Scatter Ins Col")

                #unlink from any other collection in scene
                for c in (scene.collection.children_recursive[:]+[scene.collection]):
                    if (p.s_instances_coll_ptr in c.children[:]):
                        if (not c.library):
                            c.children.unlink(p.s_instances_coll_ptr)
                        
                #and add it to our official collection
                if (p.s_instances_coll_ptr not in ins_col.children[:]):
                    ins_col.children.link(p.s_instances_coll_ptr)
                
                #also hide the collection by default
                set_collection_view_layers_exclude(p.s_instances_coll_ptr, hide=True)
                
                #also update it's name
                if (not p.is_linked):
                    p.s_instances_coll_ptr.name = f"ins_col : {p.name}"
        
        #& for surface collections
        if (options.get("ensure_p_surf_col")):
            
            if (p.s_surface_collection):
                
                s_surface_collection_ptr = bpy.data.collections.get(p.s_surface_collection) #I really don't like that.. name collision probable..
                surf_col = bpy.data.collections.get("Geo-Scatter Surfaces")

                #unlink from any other collection in scene
                for c in (scene.collection.children_recursive[:]+[scene.collection]):
                    if (s_surface_collection_ptr in c.children[:]):
                        if (not c.library):
                            c.children.unlink(s_surface_collection_ptr)
                        
                #and add it to our official collection
                if (s_surface_collection_ptr not in surf_col.children[:]):
                    surf_col.children.link(s_surface_collection_ptr)
        
        continue
    
    #clean up empty collections
    if (options.get("remove_unused_colls")):
            
        #NOTE ideally should check if psys aren't using these empty collections.. users might rant about pointers suddenly disappearing
        
        for name in ("Geo-Scatter Geonode","Geo-Scatter Ins Col","Geo-Scatter Surfaces",):
            original = bpy.data.collections.get(name)
            
            for subcol in original.children:
                if (len(subcol.children)==0 and len(subcol.objects)==0):
                    bpy.data.collections.remove(subcol)
                
    #make sure viewlayers hidding status are correct
    if (options.get("ensure_viewlayers")):
        
        for sc in [sc for sc in bpy.data.scenes if any(ch.name.startswith("Geo-Scatter") for ch in sc.collection.children_recursive)]:
            ensure_scatter_collection_viewlayers(scene=sc)
    
    return None


#   .oooooo.                                               .
#  d8P'  `Y8b                                            .o8
# 888      888 oo.ooooo.   .ooooo.  oooo d8b  .oooo.   .o888oo  .ooooo.  oooo d8b
# 888      888  888' `88b d88' `88b `888""8P `P  )88b    888   d88' `88b `888""8P
# 888      888  888   888 888ooo888  888      .oP"888    888   888   888  888
# `88b    d88'  888   888 888    .o  888     d8(  888    888 . 888   888  888
#  `Y8bood8P'   888bod8P' `Y8bod8P' d888b    `Y888""8o   "888" `Y8bod8P' d888b
#               888
#              o888o


from .. translations import translate


class SCATTER5_OT_create_coll(bpy.types.Operator):

    bl_idname      = "scatter5.create_coll"
    bl_label       = translate("Create Collection")
    bl_description = translate("Create a new collection, containing all the objects selected in the 3D viewport")
    bl_options = {'REGISTER',}

    api : bpy.props.StringProperty()
    pointer_type : bpy.props.StringProperty() #expect "str" or "data"?  

    coll_name : bpy.props.StringProperty(name="Name", options={"SKIP_SAVE",})
    parent_name : bpy.props.StringProperty(name="Geo-Scatter User Col", options={"SKIP_SAVE",})

    @classmethod
    def poll(cls, context):
        return (context.mode=="OBJECT")

    def invoke(self, context, event):
        self.alt = event.alt #TODO ALT SUPPORT!
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.prop(self,"coll_name")
        return None 

    def execute(self, context):

        new_coll = create_new_collection(self.coll_name, parent=self.parent_name, prefix=True,)
        for o in bpy.context.selected_objects:
            new_coll.objects.link(o)

        #execute code & give useful namespace
        scat_scene = bpy.context.scene.scatter5
        emitter = scat_scene.emitter
        psy_active = emitter.scatter5.get_psy_active()
        group_active = emitter.scatter5.get_group_active()
        if (self.pointer_type=='str'):
              exec(f"{self.api}='{new_coll.name}'")
        else: exec(f"{self.api}=new_coll")

        #UNDO_PUSH
        bpy.ops.ed.undo_push(message=translate("Create a new collection with selected object(s)"),)

        return {'FINISHED'}


class SCATTER5_OT_add_to_coll(bpy.types.Operator):

    bl_idname = "scatter5.add_to_coll"
    bl_label       = translate("Add to Collection")
    bl_description = translate("Link the compatible object(s) selected in the viewport to this collection.\nHold 'ALT' to batch apply this action to the collections of the selected system(s)")
    bl_options     = {'REGISTER',}

    coll_name : bpy.props.StringProperty(options={"SKIP_SAVE",})
    alt_support : bpy.props.BoolProperty(default=True, options={"SKIP_SAVE",})
    coll_api : bpy.props.StringProperty(options={"SKIP_SAVE",})

    @classmethod
    def poll(cls, context):
        return (context.mode=="OBJECT")

    def __init__(self, *args, **kwargs):
        """get var user selection"""
        
        super().__init__(*args, **kwargs)
        
        self.selection = bpy.context.selected_objects
        return None 

    def invoke(self, context, event):
        self.using_alt_behavior = (event.alt and self.alt_support)
        return self.execute(context)

    def execute(self, context):
        
        if (len(bpy.context.selected_objects)==0):
            bpy.ops.scatter5.popup_menu(msgs=translate("No Compatible Object(s) Found in Selection"), title=translate("Warning"),icon="ERROR",)
            return {'FINISHED'}

        #collect all our collections, if using alt, we gather all collections of selected scatter-systems

        if (self.using_alt_behavior):
            
            colls = []
            
            if (self.coll_api):
                for p in context.scene.scatter5.emitter.scatter5.get_psys_selected():
                    collname = getattr(p,self.coll_api)
                    coll = get_collection_by_name(collname)
                    if (coll is not None):
                        if (coll not in colls):
                            colls.append(coll)
                    
        else:
            coll = get_collection_by_name(self.coll_name)
            if (coll is None):
                print(f"ERROR: scatter5.add_to_coll(): {self.coll_name} not found")
                return {'FINISHED'}
            colls = [coll]

        #for all collection, add obj

        for coll in colls:
            for o in bpy.context.selected_objects:
                if (o.name not in coll.objects):
                    coll.objects.link(o)
        
        #UNDO_PUSH
        bpy.ops.ed.undo_push(message=translate("Add selected object(s) to the context collection(s)"),)

        return {'FINISHED'}


class SCATTER5_OT_remove_from_coll(bpy.types.Operator):

    bl_idname = "scatter5.remove_from_coll"
    bl_label       = translate("Remove from collection")
    bl_description = translate("Unlink this object from the context collection.\nHold 'ALT' to batch apply this action to the collections of the selected system(s)")
    bl_options     = {'REGISTER',}

    obj_session_uid : bpy.props.IntProperty(options={"SKIP_SAVE",})
    coll_name : bpy.props.StringProperty(options={"SKIP_SAVE",})
    alt_support : bpy.props.BoolProperty(default=True, options={"SKIP_SAVE",},)
    coll_api : bpy.props.StringProperty(options={"SKIP_SAVE",})

    def invoke(self, context, event):
        self.using_alt_behavior = (event.alt and self.alt_support)
        return self.execute(context)

    def execute(self, context):

        from .. utils.extra_utils import get_from_uid
        o = get_from_uid(self.obj_session_uid)
        if (o is None):
            print(f"ERROR: scatter5.remove_from_coll(): obj {self.obj_session_uid} not found")
            return {'FINISHED'}

        #collect all our collections, if using alt, we gather all collections of selected scatter-systems

        if (self.using_alt_behavior):

            colls = []

            if (self.coll_api):
                for p in context.scene.scatter5.emitter.scatter5.get_psys_selected():
                    collname = getattr(p,self.coll_api)
                    coll = get_collection_by_name(collname)
                    if (coll is not None):
                        if (coll not in colls):
                            colls.append(coll)

        else:
            coll = get_collection_by_name(self.coll_name)
            if (coll is None):
                print(f"ERROR: scatter5.remove_from_coll(): collection {self.coll_name} not found")
                return {'FINISHED'}
            colls = [coll]

        #for all our collections, remove obj, if present in there

        for coll in colls:
            if (o.name in coll.objects):
                coll.objects.unlink(o)
                continue

        #UNDO_PUSH
        bpy.ops.ed.undo_push(message=translate("Remove an object from the context collection(s)"),)

        return {'FINISHED'}


#   .oooooo.   oooo
#  d8P'  `Y8b  `888
# 888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
# 888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
# 888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
# `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#  `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'


classes = (

    SCATTER5_OT_create_coll,
    SCATTER5_OT_add_to_coll,
    SCATTER5_OT_remove_from_coll,
    
    )