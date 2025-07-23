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
#  oooooooooooo                         .
#  `888'     `8                       .o8
#   888          .oooo.    .ooooo.  .o888oo  .ooooo.  oooo d8b oooo    ooo
#   888oooo8    `P  )88b  d88' `"Y8   888   d88' `88b `888""8P  `88.  .8'
#   888    "     .oP"888  888         888   888   888  888       `88..8'
#   888         d8(  888  888   .o8   888 . 888   888  888        `888'
#  o888o        `Y888""8o `Y8bod8P'   "888" `Y8bod8P' d888b        .8'
#                                                              .o..P'
#                                                              `Y8P'
#####################################################################################################


import bpy

import time, datetime, random
from mathutils import Matrix, Vector, Color, Euler

from .. translations import translate

from .. utils.extra_utils import dprint, is_rendered_view
from .. utils.import_utils import import_geonodes
from .. utils.event_utils import get_event
from .. resources import directories


#####################################################################################################

#All interactions with Scatter engine nodetree are located in this module

#What's happening in here?
# 1 Settings in particle_settings.py, need update fcts! (for psys or psygroups)
# 2 We generate the update fct with a fct factory
#   That way we can optionally add delay to update fct with wrapper
# 4 Then function goes in Dispatcher 
#   4.1 We gather & exec adequate update fct, all stored in UpdatesRegistry
#   4.2 Optional add effects == send update signals to other properties (alt/sync)

# oooooo   oooooo     oooo
#  `888.    `888.     .8'
#   `888.   .8888.   .8'   oooo d8b  .oooo.   oo.ooooo.  oo.ooooo.   .ooooo.  oooo d8b
#    `888  .8'`888. .8'    `888""8P `P  )88b   888' `88b  888' `88b d88' `88b `888""8P
#     `888.8'  `888.8'      888      .oP"888   888   888  888   888 888ooo888  888
#      `888'    `888'       888     d8(  888   888   888  888   888 888    .o  888
#       `8'      `8'       d888b    `Y888""8o  888bod8P'  888bod8P' `Y8bod8P' d888b
#                                              888        888
#                                             o888o      o888o


def factory(prop_name, delay_support=False, alt_support=True, sync_support=True,):
    """will find and return wrapped function according to propname at parsetime
    delay_support -> is the property supporting the delay wrapper? delay only needed when sliding! therefore always False except for sliders properties in Float/Int/Vector
    alt_support   -> is the property supporting the alt behavior? only `is_random_seed` should not, as it is a false property & may create feedback loop issue otherwise
    sync_support  -> is the property supporting the synchronization feature? `seed` properties do not support it for user convenience.
    """
    
    def update_fct(self,context):

        from ... __init__ import blend_prefs
        scat_data = blend_prefs()
        
        #Real Time Update? 
        if ( (scat_data.factory_delay_allow==False) or (delay_support==False) ):
            
            update_dispatcher(self, prop_name, alt_support=alt_support, sync_support=sync_support,)
            return None 

        #Fixed Interval update? 
        if (scat_data.factory_update_method=="update_delayed"): 
            
            if (scat_data.factory_update_delay==0):
                update_dispatcher(self, prop_name, alt_support=alt_support, sync_support=sync_support,)
                return None
            
            function_exec_delay(
                interval=scat_data.factory_update_delay,
                function=update_dispatcher, 
                arg=[self, prop_name,], 
                kwarg={"alt_support":alt_support, "sync_support":sync_support,} 
                )
            return None 

        #On mouse release Update? 
        if (scat_data.factory_update_method=="update_on_halt"):
            
            function_exec_event_release(
                function=update_dispatcher, 
                arg=[self, prop_name,],
                kwarg={"alt_support":alt_support, "sync_support":sync_support,} 
                )
            return None

    return update_fct


def function_exec_delay(interval=0, function=None, arg=[], kwarg={},):
    """add delay to function execution, 
    Note update delay can by avoid by turning the global switch 
    "scat_data.factory_delay_allow" to False"""

    _f = function_exec_delay
    #initialize static attr
    if (not hasattr(_f,"is_running")):
        _f.is_running = False

    #if timer already launched, quit
    if (_f.is_running):
        return None 

    def delay_call():
        """timer used to add delay when calling operator of the function"""

        dprint("PROP_FCT: delay_call()")

        with bpy.context.scene.scatter5.factory_update_pause(delay=True):
            function(*arg,**kwarg)

        _f.is_running = False
        return None

    #launching timer
    dprint("PROP_FCT: delay_call(): bpy.app.timers.register(delay_call)")
    bpy.app.timers.register(delay_call, first_interval=interval)
    _f.is_running = True
    
    return None 

def function_exec_event_release(function=None, arg=[], kwarg={},):
    """if "LEFTMOUSE PRESS" loop until no more pressed"""

    _f = function_exec_event_release
    #initialize static attr
    if (not hasattr(_f,"is_waiting")):
        _f.is_waiting = False

    #if timer fct is waiting for an exec already, skip
    if (_f.is_waiting):
        return None 

    event = get_event()
    
    #if user is hitting enter, update directly
    if (event.type=="RET"):

        with bpy.context.scene.scatter5.factory_update_pause(delay=True):
            function(*arg,**kwarg)

        return None 

    #if user is tweaking with left mouse click hold, launch timer to detect when he is done
    if (event.value=="PRESS"):

        def release_call():
            """timer used to add delay when calling operator of the function"""

            dprint("PROP_FCT: release_call()")

            if (get_event().value!="PRESS"):

                with bpy.context.scene.scatter5.factory_update_pause(delay=True):
                    function(*arg,**kwarg)

                _f.is_waiting = False
                return None 

            return 0.1

        dprint("PROP_FCT: release_call(): bpy.app.timers.register(release_call)")
        bpy.app.timers.register(release_call)
        _f.is_waiting = True

    return None 


# oooooooooo.    o8o                                    .             oooo
# `888'   `Y8b   `"'                                  .o8             `888
#  888      888 oooo   .oooo.o oo.ooooo.   .oooo.   .o888oo  .ooooo.   888 .oo.   
#  888      888 `888  d88(  "8  888' `88b `P  )88b    888   d88' `"Y8  888P"Y88b  
#  888      888  888  `"Y88b.   888   888  .oP"888    888   888        888   888  
#  888     d88'  888  o.  )88b  888   888 d8(  888    888 . 888   .o8  888   888  
# o888bood8P'   o888o 8""888P'  888bod8P' `Y888""8o   "888" `Y8bod8P' o888o o888o
#                               888
#                              o888o
#

# Normally all interaction through nodegraph is done via this function, for all psys and groups properties
# except for texture related data (transforms) as this is considered per texture data block
# see the scattering.texture_datablock module

def update_dispatcher(sys, prop_name, alt_support=True, sync_support=True,):
    """update nodegroup dispatch, this function is not meant to be used directly, use factory() instead"""
    
    from ... __init__ import blend_prefs
    scat_data = blend_prefs()
        
    if (not scat_data.factory_active):
        dprint(f"PROP_FCT: update_dispatcher('{sys.name}','{prop_name}'): UpdateDenied : `scat_data.factory_active` disabled")
        return None
    
    elif (sys.is_linked):
        if (prop_name not in ("hide_viewport","hide_render")): #hide props are special for linked scatters
            dprint(f"PROP_FCT: update_dispatcher('{sys.name}','{prop_name}'): UpdateDenied : is_linked!")
            return None
    
    #get prop value
    value = getattr(sys,prop_name)

    #get keyboard event 
    event = get_event() #TODO is this causing slow downs (launching a ope) ???? will need to check once optimization is at focus.

    #get update function we need from the procedurally generated dict and execute the correct funtion depending on prop_name
    dprint(f"PROP_FCT: update_dispatcher('{sys.name}','{prop_name}').run_update(): value={value}, event={event}")
    UpdatesRegistry.run_update(sys, prop_name, value, event=event)

    #Special ALT & SYNC behaviors for particle systems properties. We automatically set their values
    match sys.system_type:

        case 'GROUP_SYSTEM':
            pass
        
        case 'SCATTER_SYSTEM':
            
            #Alt Feature
            if (alt_support and scat_data.factory_alt_allow and event.alt):
                
                #Special case for '..is_random_seed' properties: Alt is supported within the property update function instead.
                if (not prop_name.endswith("_is_random_seed")):
                    update_alt_for_batch(sys, prop_name, value,)

            #Synchronize Feature
            if (sync_support and scat_data.factory_synchronization_allow):
                
                #Special case for seeds, we don't synchronize seeds
                if (not prop_name.endswith("_seed")):
                    update_sync_channels(sys, prop_name, value,)
    
    return None

def update_alt_for_batch(psy, prop_name, value,):
    """sync value to all selected psy when user is pressing alt"""

    dprint(f"PROP_FCT: update_alt_for_batch()")

    from ... __init__ import blend_prefs
    scat_data = blend_prefs()
            
    #turn off alt behavior to avoid feedback loop when batch changing selection settings, 
    #events will return None if factory_event_listening_allow is set to False
    with bpy.context.scene.scatter5.factory_update_pause(event=True):

        #alt for batch support
        emitter = psy.id_data
        psys_sel = emitter.scatter5.get_psys_selected(all_emitters=scat_data.factory_alt_selection_method=="all_emitters")

        #copy active settings for all selected systems
        for p in psys_sel:

            #no need to update itself
            if (p.name==psy.name):
                continue

            #avoid updating locked properties
            if (p.is_locked(prop_name)):
                continue

            #only update if value differ
            current_value = getattr(p, prop_name)
            if (current_value==value):
                continue

            #update!
            dprint(f"PROP_FCT: update_alt_for_batch(): setattr('{p.name}','{prop_name}',{value})", depsgraph=True)
            setattr(p, prop_name, value,)
            continue

    return None 

def update_sync_channels(psy, prop_name, value,):
    """sync all settings while updating, settings get synced in the update factory"""

    from ... __init__ import blend_prefs
    scat_data = blend_prefs()
    
    #check if channels exists at first place
    if (not scat_data.sync_channels):
        return None

    #check if there's some stuff to synch with
    #if yes find dict of psy with prop category
    siblings = psy.get_sync_siblings()
    if (len(siblings)==0):
        return None

    dprint(f"PROP_FCT: update_sync_channels()")

    #ignore any properties update behavior, such as update delay or hotkeys
    with bpy.context.scene.scatter5.factory_update_pause(event=True,delay=True,sync=False):

        #synchronize all syblings with given value
        for ch in siblings:
                
            #check if prop is a category that should be ignored
            if (not any( prop_name.startswith(c) for c in ch["categories"]) ):
                continue

            #batch change properties if not set to sync value
            for p in ch["psys"]:

                #no need to update itself
                if (p.name==psy.name):
                    continue

                #avoid updating locked properties
                if (p.is_locked(prop_name)):
                    continue

                #only update if value differ
                current_value = getattr(p, prop_name)
                if (current_value==value):
                    continue

                #update!
                dprint(f"PROP_FCT: update_sync_channels(): setattr('{p.name}','{prop_name}',{value})", depsgraph=True)
                setattr(p, prop_name, value,)
                continue
                
            continue
        
    return None


#   .oooooo.                                              o8o                 oooooooooooo               .
#  d8P'  `Y8b                                             `"'                 `888'     `8             .o8
# 888            .ooooo.  ooo. .oo.    .ooooo.  oooo d8b oooo   .ooooo.        888          .ooooo.  .o888oo
# 888           d88' `88b `888P"Y88b  d88' `88b `888""8P `888  d88' `"Y8       888oooo8    d88' `"Y8   888
# 888     ooooo 888ooo888  888   888  888ooo888  888      888  888             888    "    888         888
# `88.    .88'  888    .o  888   888  888    .o  888      888  888   .o8       888         888   .o8   888 .
#  `Y8bood8P'   `Y8bod8P' o888o o888o `Y8bod8P' d888b    o888o `Y8bod8P'      o888o        `Y8bod8P'   "888"

#various function interacting with properties or nodetrees, used in UpdatesRegistry


def get_enum_idx(item, prop_name, value,):
    """retrieve index of an item from an enum property
    WARNING will not work on dynamic items fct...""" 

    prop = item.bl_rna.properties[prop_name]
    element = prop.enum_items.get(value)
    
    if (element is None):
        print(f"ERROR get_enum_idx(): '{value}' element not found in '{prop_name}' enum")
        return 0
    
    return element.value

def color_type(value):
    """Ensure color value is of Vec4 type for RGBA"""
        
    if (len(value)==4):
        if (type(value) is not Vector):
            return Vector(value)
        return value
    
    #support alpha channel
    if (len(value)==3):
        return Vector((value[0],value[1],value[2],1))
    
    raise Exception(f"ERROR: color_type(): Unknown color type: '{value}' type={type(value)} len={len(value)}")

def vector_type(value):
    """Ensure value is of Vector type"""
    
    if (type(value) is not Vector):
        return Vector(value)
    
    return value
    
def get_node(psy, node_name, strict=True,):
    """get node from psy nodetree"""

    mod = psy.get_scatter_mod(strict=strict, raise_exception=False,)
    
    if (mod is None):
        print(f"REPORT: get_node(): Geo-Scatter Engine Modifier not Found, The plugin interface cannot access and change the nodetree.. (Information: psy='{psy.name}')")
        return None
    if (mod.node_group is None):
        print(f"REPORT: get_node(): Geo-Scatter Engine not Found, The plugin interface cannot access and change the nodetree.. (Information: psy='{psy.name}')")
        return None
    
    nodes = mod.node_group.nodes
    inner_name = None

    if ("." in node_name):
        node_name, inner_name, *_ = node_name.split(".")

    node = nodes.get(node_name)
    if (node is None):
        print("ERROR: get_node(): '",node_name,"' not found")
        return None 

    if ((inner_name) and (node.type=='GROUP')):
        inner_ng = node.node_tree
        if (inner_ng):

            node = inner_ng.nodes.get(inner_name)
            if (node is None):
                print("ERROR: get_node(): '",node_name,">",inner_name,"' not found")
                return None 

    return node

def node_value(psy, node_name, value=None, entry="", socket_idx=0,):
    """set value in psy nodetree from node name, depending on node entry type"""

    node = get_node(psy, node_name)
    if (node is None): 
        return None 
        
    match entry:
        
        case "node_socket": # For nodegroup socket parameters
            current_val = node.inputs[socket_idx].default_value
            
            #convert bpy_prop_array to Vector (could be color vec4 or vec3). Somehow blender will throw array type with bad __eq__
            if (type(current_val) is bpy.types.bpy_prop_array):
                current_val = Vector(current_val)
            #unsuported Rotation socket
            elif (type(current_val) is Euler):
                print("WARNING: node_value() unsuported new rotation socket type.")
            
            if (current_val!=value):
                node.inputs[socket_idx].default_value = value

        case "float_input": # For float input node (yeah weird api)
            if (node.outputs[0].default_value!=value):
                node.outputs[0].default_value = value

        case "integer_input": # For integer input node
            if (node.integer!=value):
                node.integer = value

        case "boolean_input": # For boolean input node
            if (node.boolean!=value):
                node.boolean = value

        case "vector_input": # For vector input node
            if (node.vector!=value):
                node.vector = value

        case "named_attr": # For the read named attr node
            if (node.inputs[0].default_value!=value):
                node.inputs[0].default_value = value
        
        case _:
            raise Exception("ERROR: node_value(): entry parameter shouldn't be None")

    return None  

def mute_color(psy, node_name, mute=True,):
    """mute a color of a node in psy nodetree"""

    node = get_node(psy, node_name)
    if (node is None): 
        return None

    mute = not mute
    if (node.use_custom_color!=mute): 
        node.use_custom_color = mute

    return None 

def mute_node(psy, node_name, mute=True,):
    """mute a node in psy nodetree"""

    node = get_node(psy, node_name)
    if (node is None): 
        return None

    if (node.mute!=mute):
        node.mute = mute

    return None

def node_link(psy, receptor_node_name, emetor_node_name, receptor_socket_idx=0, emetor_socket_idx=0,):
    """link two nodes together in psy nodetree"""
    #WARNING currently this fct does not support indented node_name

    mod = psy.get_scatter_mod(strict=True, raise_exception=False,)

    if (mod is None):
        print(f"REPORT: node_link(): Geo-Scatter Engine Modifier not Found, The plugin interface cannot access and change the nodetree.. (Information: psy='{psy.name}')")
        return None
    if (mod.node_group is None):
        print(f"REPORT: node_link(): Geo-Scatter Engine not Found, The plugin interface cannot access and change the nodetree.. (Information: psy='{psy.name}')")
        return None
    
    nodes = mod.node_group.nodes
    receptor_nd, emetor_nd = nodes.get(receptor_node_name), nodes.get(emetor_node_name)
    
    #check if nodes exists
    if (receptor_nd is None) or (emetor_nd is None):
        print(f"ERROR: node_link(): '{receptor_node_name}' or '{emetor_node_name}' nodes not found in {nodes}")
        return None 

    #Get sockets
    node_in, node_out = receptor_nd.inputs[receptor_socket_idx], emetor_nd.outputs[emetor_socket_idx]

    # Check if node_out is already linked to node_in
    if any(link.to_socket==node_in for link in node_out.links):
        return None

    #link the two inputs
    mod.node_group.links.new(node_in, node_out)
    
    return None

def set_keyword(psy, value, element=None, kw="info_keyword",):
    """update keword node in psy nodetree. ex: "random local singlesurf"""

    node = get_node(psy, kw)
    if (node is None): 
        return None
    
    #set whole string?
    if (element is None):
        node.string = value
    
    #or update string by elements? elements == "0=s_distribution_method 1=space(local/global) 2=surface(singlesurf/multisurf/nosurf)"
    else:
        l = node.string.split(" ")
        l[element] = value
        node.string = " ".join(l)

    return None

def get_keyword(psy, kw="info_keyword",):
    """get keyword value from psy node"""

    node = get_node(psy, kw)
    if (node is None):
        return ""
    
    return node.string

def random_seed(psy, event, api_is_random="", api_seed="",):
    """random psy function of a nodetree, will assign property"""

    # This BooleanProperty will always be False, it is acting as a function
    if (getattr(psy,api_is_random)==False):
          return None

    setattr(psy,api_is_random,False,)

    from ... __init__ import blend_prefs
    scat_data  = blend_prefs()
    scat_scene = bpy.context.scene.scatter5
    emitter = psy.id_data

    #ignore any properties update behavior, such as update delay or hotkeys
    with scat_scene.factory_update_pause(event=True,delay=True,sync=False):

        #alt for batch support
        if (event.alt and scat_data.factory_alt_allow):
            psys_sel = emitter.scatter5.get_psys_selected(all_emitters=scat_data.factory_alt_selection_method=="all_emitters")
            for p in psys_sel:
                setattr(p,api_seed,random.randint(0,9999),)
        else:
            setattr(psy,api_seed,random.randint(0,9999),)
    
    return None


# .dP"Y8 88""Yb 888888  dP""b8 88    db    88         88   88 88""Yb 8888b.     db    888888 888888
# `Ybo." 88__dP 88__   dP   `" 88   dPYb   88         88   88 88__dP  8I  Yb   dPYb     88   88__
# o.`Y8b 88"""  88""   Yb      88  dP__Yb  88  .o     Y8   8P 88"""   8I  dY  dP__Yb    88   88""
# 8bodP' 88     888888  YboodP 88 dP""""Yb 88ood8     `YbodP' 88     8888Y"  dP""""Yb   88   888888


def set_texture_ptr(psy, prop_name, value,):
    """changing a texture ptr == assigning texture nodetree to a psy texture nodegroup"""

    node = get_node(psy, prop_name)
    if (node is None):
        return None

    #make sure texture type, should startwith prefix
    ng_name = value if value.startswith(".TEXTURE ") else f".TEXTURE {value}"
    
    #empty name, can't exist.. must be referring to the default scatter-texture nodegroup
    if (ng_name==".TEXTURE "):
        ng_name = ".TEXTURE *DEFAULT* MKV"

    #try to get the nodegroup
    ng = bpy.data.node_groups.get(ng_name)
    if (ng is None):
        print(f"ERROR: set_texture_ptr(): node_groups '{ng_name}' not found")
        return None
    
    #update nodetree with our match
    if (node.node_tree!=ng):
        node.node_tree = ng

    return None 

def fallremap_getter(prop_name):
    """get remap graph points matrix from node"""

    from .. curve.fallremap import get_matrix

    def getter(self):
        node = get_node(self, f"{prop_name}.fallremap")
        matrix = get_matrix(node.mapping.curves[0], handle=True, string=True,)
        return matrix

    return getter

def fallremap_setter(prop_name):
    """set remap graph matrix from matrix str"""

    from .. curve.fallremap import set_matrix

    def setter(self,matrix):
        node = get_node(self, f"{prop_name}.fallremap")

        set_matrix(node.mapping.curves[0], matrix,)
        node.mute = not node.mute ; node.mute = not node.mute ; node.mapping.update() #trigger update signal
        return None 
        
    return setter

def update_transfer_attrs_nodegroup(psy,):
    """for some distribution methods, we need to manually track and transfer attributes"""
    
    dprint("FCT: update_transfer_attrs_nodegroup(): Updating nodetree attr transfer values..")
    
    #find all uvs, we transfer all uvs, shouldn't be many normally
    uvs = list(set(uv.name for s in psy.get_surfaces() if (s.data is not None) for uv in s.data.uv_layers))
    node = get_node(psy, "transfer_uvs")
    if (node):
        for i in range(20):
            value = uvs[i] if i<len(uvs) else ""
            if (node.inputs[i].default_value!=value):
                node.inputs[i].default_value = value
    
    #find needed mask attr & transfer
    grps = [getattr(psy,k) for k,v in psy.bl_rna.properties.items() if k.endswith("_mask_ptr")]
    grps = [v for v in grps if (v!="")]
    grps = list(set(grps))
    node = get_node(psy, "transfer_grps")
    if (node):
        for i in range(20):
            value = grps[i] if (i<len(grps)) else ""
            if (node.inputs[i].default_value!=value):
                node.inputs[i].default_value = value
                
    return None

def update_camera_nodegroup(scene=None, render=False, force_update=False, reset_hash=False, self_call=False, locked_interface=False,):
    """update camera pointer information, this function is runned on depsgraph handlers, we'll update the camera current transformation matrix in `s_cam_location`/`s_cam_rotation_euler`, 
    but also any camera fov and sensor information in `s_visibility_cam`, also any sort of per camera settings (such as various distance per camera) in `s_visibility_cam`/`s_scale_fading`"""
    
    # WARNING: we need to be extra carreful about feedback loop in this fct
    
    # WARNING: we are taking a lot of risk in this function. 
    #      Any error could mess up the users camera optimization
    
    # WARNING: we had report on some users "AttributeError: "
    #       Writing to ID classes in this context is not allowed: .Scatter5 Geonode Engine MKIII.003, NodeTree datablock, error setting FunctionNodeInputVector.vector"
    #      it seems that interacting with nodes from a depsgraph update is not recommanded?
    #      Very strange that it is only happening to some users. Only had one report so far, maybe a blender bug.

    from ... __init__ import blend_prefs
    scat_data = blend_prefs()
    
    if (scene is None):
        scene = bpy.context.scene
    
    ## Static Vars
    
    _f = update_camera_nodegroup
    if (not hasattr(_f,"is_updating")): #used to avoid calling option recursively. what we are doing in here might trigger another update..
        _f.is_updating = False
    if (not hasattr(_f,"camera_hash")): #used to avoid calling this function if the camera values didn't change
        _f.camera_hash = None
    if (not hasattr(_f,"upd_on_halt_camhash")): #used for on halt update method
        _f.upd_on_halt_camhash = None
    if (not hasattr(_f,"upd_on_halt_waiting")): #used for on halt update method, to avoid recursive call while waiting for user to halt cam movements.
        _f.upd_on_halt_waiting = False
        
    if (reset_hash):
        _f.camera_hash = None
        
    #a force update will reset the updating delay system, to avoid delay system freezing indefinitely, user can kick it. 
    # WARNING: this also means that it is strictly forbidden to call a force update from a depsgraph loop
    if (force_update):
        _f.is_updating = False
        
    dprint(f"FCT: update_camera_nodegroup(force_update={force_update},is_updating={_f.is_updating},self_call={self_call},render={render},locked_interface={locked_interface},): Simply Doing Checks..", depsgraph=True,)
    
    #skip if function is currently running updates.. 
    # WARNING: Dangerous.., if var is not updated properly, will lead to updates dependencies issues
    if (_f.is_updating): 
        dprint("FCT: update_camera_nodegroup(): Canceled: An update is already running. In order to avoid depsgraph feedback loop, we had to cancel this update",depsgraph=True,)
        return None 
    
    ## Get camera Info's
    
    #locked interface need to get an eval from depsgraph
    if (render and locked_interface):
          cam = scene.camera.evaluated_get(bpy.context.evaluated_depsgraph_get())
    else: cam = scene.camera 

    if (cam is None):
        dprint("FCT: update_camera_nodegroup(): Canceled: no cam found",depsgraph=True,)
        return None
    
    cam_loc, cam_rot = cam.matrix_world.translation, cam.matrix_world.to_euler()
    ca_sensor, ca_lens, ca_shiftxy, ca_resxy, ca_boostxy = cam.data.sensor_width, cam.data.lens, [cam.data.shift_x, cam.data.shift_y], [scene.render.resolution_x, scene.render.resolution_y], list(cam.scatter5.s_visibility_camclip_per_cam_boost_xy[:])
    ca_sensorfit = 0 if (cam.data.sensor_fit=='AUTO') else 1 if (cam.data.sensor_fit=='HORIZONTAL') else 2 if (cam.data.sensor_fit=='VERTICAL') else None
    if (cam.data.sensor_fit=='VERTICAL'):
        ca_sensor = cam.data.sensor_height
                    
    #check if it's worth updating the ngs.. if camera didn't change we don't bother sending a update signal
    camera_hash = hash((tuple(cam_loc), tuple(cam_rot), ca_sensor, ca_sensorfit, ca_lens, tuple(ca_shiftxy), tuple(ca_resxy), tuple(ca_boostxy),))
    if (_f.camera_hash==camera_hash):
        if (not render):
            dprint("FCT: update_camera_nodegroup(): Canceled: camera_hash didn't change since last time..")
            return None
    
    ## Delay Methods
    
    if ((not force_update) and (not self_call)):
        
        #special delayed update methods, we don't want constant update triggers. if we use the delay function we'll call this function again
        match scat_data.factory_cam_update_method:

            case 'update_realtime':
                #if we use realtime update method, then there's no function self call delay or stop manipulation
                pass
                            
            case 'update_delayed':
                #delay update depending on ms. if ms is set to 0, then, constant update flow
                if (scat_data.factory_cam_update_secs!=0):
                    function_exec_delay(interval=scat_data.factory_cam_update_secs, function=update_camera_nodegroup, arg=[], kwarg={"self_call":True},)
                    return None

            case 'update_apply':
                #update apply == will run force update signal via an operator
                return None

            case 'update_on_halt':
                #update when the camera has stopped moving only, for this we track camera movement

                #don't launch a new instance of the function if already running..
                if (_f.upd_on_halt_waiting):
                    dprint("FCT: update_camera_nodegroup(): Canceled: Halt timer fct already running..",depsgraph=True,)
                    return None 

                def update_on_halt_timer():
        
                    #if value changes every x ms, it means users is still moving.. we wait a little more..
                    camhash =  hash((tuple(cam.matrix_world.translation), tuple(cam.matrix_world.to_euler()),))
                    if (camhash!=_f.upd_on_halt_camhash):
                        _f.upd_on_halt_camhash = camhash
                        return 0.45

                    dprint("FCT: update_camera_nodegroup(): Halt loop finished",depsgraph=True,)
                    
                    #launching self call
                    _f.upd_on_halt_waiting = False
                    update_camera_nodegroup(self_call=True)
                    
                    return None

                dprint("FCT: update_camera_nodegroup(): Launching Halt loop..",depsgraph=True,)

                #launch an instance of the function
                bpy.app.timers.register(update_on_halt_timer)
                _f.upd_on_halt_waiting = True

                return None 
    
    ## Update Scatter-Systems

    try:
        _f.camera_hash = camera_hash
        _f.is_updating = True

        dprint(f"FCT: update_camera_nodegroup(): Doing Checks: Looping all psys, checking if actions needed...",depsgraph=True,)

        for p in [ p for p in scene.scatter5.get_all_psys(search_mode="all", also_linked=True) \
                   if (
                       (p.s_visibility_cam_allow)
                       or 
                       (p.s_scale_fading_allow)
                       or 
                       (p.s_display_allow and p.s_display_camdist_allow) 
                       or 
                       (p.s_rot_align_y_allow and p.s_rot_align_y_method=='meth_align_y_camera')
                       or 
                       (p.s_rot_align_z_allow and p.s_rot_align_z_method=='meth_align_z_camera') 
                       #note: master_allow not taken into consideration here, todo?
                      )
                 ]:
            
            #don't update the camera settings if the system is hidden
            if (render and p.hide_render):
                dprint(f"FCT: update_camera_nodegroup(render={render}): Skipping system '{p.name}', in render and renderview closed..",depsgraph=True,)
                continue
            if ((not render) and p.hide_viewport):
                dprint(f"FCT: update_camera_nodegroup(render={render}): Skipping system '{p.name}', in viewport and not visible..",depsgraph=True,)
                continue 

            #change psy node value(s)

            mod = p.get_scatter_mod(strict=True, raise_exception=False,)
            if (mod is None): 
                dprint(f"FCT: update_camera_nodegroup(): Skipping system '{p.name}', Geo-Scatter Engine Modifier not Found, The plugin interface cannot access and change the nodetree..",depsgraph=True,)
                continue
            if (mod.node_group is None): 
                dprint(f"FCT: update_camera_nodegroup(): Skipping system '{p.name}', Geo-Scatter Engine not Found, The plugin interface cannot access and change the nodetree..",depsgraph=True,)
                continue
            
            nodes, links = mod.node_group.nodes, mod.node_group.links

            #are we using the cam info node, or a we relying on manual cam loc/rot information via s_cam_location/s_cam_rotation_euler vector inputs?
            
            if ("RR_MTX use_active_cam Receptor" in nodes):
                
                #link cam transforms noodle
                use_active_cam_node = (scat_data.factory_cam_update_method=='update_realtime')
                node_link(p, f"RR_MTX use_active_cam Receptor", f"RR_MTX use_active_cam {use_active_cam_node}",)
                
                #optimize nodegroup, the mere presence of the node, even muted or unconnected can cause slowdowns
                active_cam_node, cam_obj_info = nodes.get("active_cam"), nodes.get("active_cam_object_info")
                if (cam_obj_info):
                    
                    match use_active_cam_node:
                        case False:
                            if (active_cam_node):
                                nodes.remove(active_cam_node)
                        case True:
                            if (not active_cam_node):
                                active_cam_node = nodes.new("GeometryNodeInputActiveCamera")
                                active_cam_node.name = active_cam_node.label = "active_cam"
                                active_cam_node.parent = cam_obj_info.parent
                                active_cam_node.width = cam_obj_info.width
                                active_cam_node.location = (cam_obj_info.location.x, cam_obj_info.location.y+60)
                                links.new(active_cam_node.outputs[0],cam_obj_info.inputs[0])
            
            #update camera matrix information 

            if (scat_data.factory_cam_update_method!="update_realtime"): #if use `update_realtime` method, then there's no need to update the camera matrix, cam info node will do it in the nodetree

                # NOTE: "or (force_update and render)" is needed because of an issue,
                # cam_loc/cam_rot refuse to give us accurate values if evaluated from depsgraph, read give us different value if it is read and written.. quantum bug..

                if (nodes["s_cam_location"].vector[:] != cam_loc[:]) or (force_update and render):
                    nodes["s_cam_location"].vector = cam_loc
                    dprint(f"FCT: update_camera_nodegroup(): UpdatingNode: 's_cam_location' (force_update={force_update})",depsgraph=True,)
                
                if (nodes["s_cam_rotation_euler"].vector[:] != cam_rot[:]) or (force_update and render):
                    nodes["s_cam_rotation_euler"].vector = cam_rot
                    dprint(f"FCT: update_camera_nodegroup(): UpdatingNode: 's_cam_rotation_euler' (force_update={force_update})",depsgraph=True,)    

            #per camera cam clipping properties

            if (p.s_visibility_camclip_allow and p.s_visibility_camclip_cam_autofill):
                
                #gather ng & cam infos
                caminfnpts = nodes["s_cam_infos"].inputs
                ng_sensor, ng_sensorfit, ng_lens, ng_shiftxy, ng_resxy, ng_boostxy = caminfnpts[0].default_value, int(caminfnpts[8].default_value), caminfnpts[1].default_value, [caminfnpts[2].default_value, caminfnpts[3].default_value], [int(caminfnpts[4].default_value), int(caminfnpts[5].default_value)], [caminfnpts[6].default_value, caminfnpts[7].default_value]
                
                if (ng_sensorfit!=ca_sensorfit):
                    node_value(p, "s_cam_infos", value=ca_sensorfit, entry="node_socket", socket_idx=8)
                    dprint(f"FCT: update_camera_nodegroup(): UpdatingNode: 'sensor_fit' (force_update={force_update}) (diff={ng_sensorfit!=ca_sensorfit}, ng_sensor='{ng_sensorfit}', ca_sensor='{ca_sensorfit}')",depsgraph=True,)
                    
                if (ng_sensor!=ca_sensor):
                    UpdatesRegistry.run_update(p,"s_visibility_camclip_cam_sensor_width", ca_sensor,)
                    dprint(f"FCT: update_camera_nodegroup(): UpdatingNode: 's_visibility_camclip_cam_sensor_width' (force_update={force_update}) (diff={ng_sensor!=ca_sensor}, ng_sensor='{ng_sensor}', ca_sensor='{ca_sensor}')",depsgraph=True,)

                if (ng_lens!=ca_lens):
                    UpdatesRegistry.run_update(p,"s_visibility_camclip_cam_lens", ca_lens,)
                    dprint(f"FCT: update_camera_nodegroup(): UpdatingNode: 's_visibility_camclip_cam_lens' (force_update={force_update}) (diff={ng_lens!=ca_lens}, ng_lens='{ng_lens}', ca_lens='{ca_lens}')",depsgraph=True,)

                if (ng_shiftxy!=ca_shiftxy):
                    UpdatesRegistry.run_update(p,"s_visibility_camclip_cam_shift_xy", ca_shiftxy,)
                    dprint(f"FCT: update_camera_nodegroup(): UpdatingNode: 's_visibility_camclip_cam_shift_xy' (force_update={force_update}) (diff={ng_shiftxy!=ca_shiftxy}, ng_shiftxy='{ng_shiftxy}', ca_shiftxy='{ca_shiftxy}')",depsgraph=True,)

                if (ng_boostxy!=ca_boostxy):
                    UpdatesRegistry.run_update(p,"s_visibility_camclip_cam_boost_xy", ca_boostxy,)
                    dprint(f"FCT: update_camera_nodegroup(): UpdatingNode: 's_visibility_camclip_cam_boost_xy' (force_update={force_update}) (diff={ng_boostxy!=ca_boostxy}, ng_boostxy='{ng_boostxy}', ca_boostxy='{ca_boostxy}')",depsgraph=True,)

                if (ng_resxy!=ca_resxy):
                    UpdatesRegistry.run_update(p,"s_visibility_camclip_cam_res_xy", ca_resxy,)
                    dprint(f"FCT: update_camera_nodegroup(): UpdatingNode: 's_visibility_camclip_cam_res_xy' (force_update={force_update}) (diff={ng_resxy!=ca_resxy}, ng_resxy='{ng_resxy}', ca_resxy='{ca_resxy}')",depsgraph=True,)

            #per camera culling distance properties

            if (p.s_visibility_camdist_allow and p.s_visibility_camdist_per_cam_data):

                if (nodes["s_visibility_cam"].inputs[9].default_value != cam.scatter5.s_visibility_camdist_per_cam_min):
                    UpdatesRegistry.run_update(p,"s_visibility_camdist_min", cam.scatter5.s_visibility_camdist_per_cam_min,)
                    dprint(f"FCT: update_camera_nodegroup(): UpdatingNode: 's_visibility_camdist_per_cam_min' (force_update={force_update})",depsgraph=True,)

                if (nodes["s_visibility_cam"].inputs[10].default_value != cam.scatter5.s_visibility_camdist_per_cam_max):
                    UpdatesRegistry.run_update(p,"s_visibility_camdist_max", cam.scatter5.s_visibility_camdist_per_cam_max,)
                    dprint(f"FCT: update_camera_nodegroup(): UpdatingNode: 's_visibility_camdist_per_cam_max' (force_update={force_update})",depsgraph=True,)

            #per camera scale fading distance properties 

            if (p.s_scale_fading_allow and p.s_scale_fading_per_cam_data):

                if (nodes["s_scale_fading"].inputs[3].default_value != cam.scatter5.s_scale_fading_distance_per_cam_min):
                    UpdatesRegistry.run_update(p,"s_scale_fading_distance_min", cam.scatter5.s_scale_fading_distance_per_cam_min,)
                    dprint(f"FCT: update_camera_nodegroup(): UpdatingNode: 's_scale_fading_distance_per_cam_min' (force_update={force_update})",depsgraph=True,)

                if (nodes["s_scale_fading"].inputs[4].default_value != cam.scatter5.s_scale_fading_distance_per_cam_max):
                    UpdatesRegistry.run_update(p,"s_scale_fading_distance_max", cam.scatter5.s_scale_fading_distance_per_cam_max,)
                    dprint(f"FCT: update_camera_nodegroup(): UpdatingNode: 's_scale_fading_distance_per_cam_max' (force_update={force_update})",depsgraph=True,)

            continue 

    except Exception as e:
        print("ERROR: update_camera_nodegroup(): An error occured while we tried to update your camera optimization settings:")    
        print(e)

    finally:
        _f.is_updating = False

    return None

def update_is_rendered_view_nodegroup(value=None,):
    """update nodegroup"""

    #check needed? perhaps we already have the information
    if (value is None): 
        value = is_rendered_view()

    #change value in nodegroup
    for ng in [ng for ng in bpy.data.node_groups if (ng.name.startswith(".S Handler is rendered")) and (ng.nodes["boolean"].boolean != value) ]:
        ng.nodes["boolean"].boolean = value
        dprint(f"FCT: update_is_rendered_view_nodegroup(): Updated node value to {value}",depsgraph=True)
        continue

    return None

def update_manual_uuid_surfaces(force_update=False, flush_uuid_cache:int=None, flush_entire_cache=False,):
    """run uuid update when user is adding/removing objects in collections, run on depsgraph update"""

    #init static variables
    _f = update_manual_uuid_surfaces
    if (not hasattr(_f,"cache") or flush_entire_cache):
        _f.cache = {}
    if (not hasattr(_f,"pause")):
        _f.pause = False

    #avoid running function?  use update_manual_uuid_surfaces.pause from external if needed
    if (_f.pause) and (not force_update):
        return None

    #flush cache of specific psy if needed
    if (flush_uuid_cache is not None): 
        if (flush_uuid_cache in _f.cache):
            del _f.cache[flush_uuid_cache]

    #find all psys with manual mode & multi-surface

    for p in [p for p in bpy.context.scene.scatter5.get_all_psys(search_mode="all") if (not p.hide_viewport) and (p.s_distribution_method=="manual_all")]:

        #check if cache changed? if so, send update & sample new cache
        cvalue = set(s.name for s in p.get_surfaces())

        if ((p.uuid not in _f.cache) or (_f.cache[p.uuid]!=cvalue)):
            
            #update nodetree uuid equivalence
            dprint("FCT: update_manual_uuid_surfaces(): Found uuid differences, running update_manual_uuid_equivalence()",)
            _f.cache[p.uuid] = cvalue
            update_manual_uuid_equivalence(p)

            continue

    return None 

def update_manual_uuid_equivalence(psy):
    """set equivalence id from uuid in nodetree, only for multi-surface + manual distribution"""
    
    mod = psy.get_scatter_mod(strict=True, raise_exception=False,)
    
    if (mod is None):
        print("REPORT: update_manual_uuid_equivalence(): Couldn't find Scatter Modifier")
        return None
    if (mod.node_group is None):
        print("REPORT: update_manual_uuid_equivalence(): Couldn't find the Scatter-Engine Nodegroup")
        return None

    #avoid feedback loop
    update_manual_uuid_surfaces.pause = True

    #we cannot rely on geometry node `surf_id` as the order might change
    #manual mode will write the contacted surface scatter5.uuid value as per point int attribute
    #we'll find the equivalence from `surf_id`& their uuid values in the nodetree in order to assign correct local to glonal transforms

    #set up nodetree for a depsgraph eval
    #just eval the surfaces as instances, nothing else.
    UpdatesRegistry.s_eval_depsgraph(psy, "s_eval_depsgraph", "surfaces",) #link surfaces as output
    
    nodes = mod.node_group.nodes
    nodes["s_surface_evaluator"].inputs[4].default_value = True #do not realize

    #get id of the surfaces from within the geometry node engine, cannot be deduced & create equivalent dict
    #seems weird, but order of depsgraph instance == order of geometry node collection instance index too (starting at 0)
    i = 0
    equivalence = {}
    for ins in [ ins.object.original for ins in bpy.context.evaluated_depsgraph_get().object_instances if \
                 ( (ins.is_instance) and (ins.parent.original==psy.scatter_obj) and (ins.object.original.name!=psy.scatter_obj.name) ) 
                ]: #we get the surfaces by interacting with the geonode engine
        equivalence[ins.name] = (i, ins.scatter5.uuid,)
        i+=1
        continue

    dprint(f"UPDFCT: equivalence '{psy.name}' : {equivalence}",)

    #restore depsgraph evalto old
    nodes["s_surface_evaluator"].inputs[4].default_value = False #set as realize again
    UpdatesRegistry.s_eval_depsgraph(psy, "s_eval_depsgraph", False,)

    #performance boost while changing nodetree
    _hide_viewport = psy.hide_viewport
    psy.hide_viewport = True

    #update nodetree equivalence nodes! will replace `manual_surface_uuid` with the real id
    ng_equi = nodes["s_distribution_manual"].node_tree.nodes["uuid_equivalence"].node_tree

    #get the equivalence node that replace uuid
    uuid_ng_name = ".S Replace UUID MKV"
    replace_uuid_ng = bpy.data.node_groups.get(uuid_ng_name) #need to be correct mk version!!!
    if (replace_uuid_ng is None):
        import_geonodes(directories.blend_engine, [uuid_ng_name], link=False,)
        replace_uuid_ng = bpy.data.node_groups.get(uuid_ng_name)
        print("WARNING: You are entering manual mode but the required scatter groups was not found. Are you sure you are using the correct version of the scatter-system?")

    #cleanse all noodles 
    ng_equi.links.clear()

    #modify or change existing
    idx = 0
    nodechain = []
    nodechain.append(ng_equi.nodes["Group Input"])

    for k,(idx,uuid) in equivalence.items():
        name = f"surf_id {idx}"
        n = ng_equi.nodes.get(name)
        if (n is None): 
            n = ng_equi.nodes.new("GeometryNodeGroup")
            n.node_tree = replace_uuid_ng
            n.name = n.label = name 
        n.location.x = (idx+1)*175
        n.location.y = 0
        n.inputs[1].default_value = uuid #search
        n.inputs[2].default_value = idx #replace
        nodechain.append(n)
        continue

    #adjust last output location
    outputnode = ng_equi.nodes["Group Output"]
    nodechain.append(outputnode)
    outputnode.location.x = (idx+2)*175
    outputnode.inputs[1].default_value = idx #update maxlen id

    #create the noodles
    for i,n in enumerate(nodechain): 
        #ignore first element
        if (i==0): 
            continue
        node_in  = nodechain[i].inputs[0]
        node_out = nodechain[i-1].outputs[0]
        ng_equi.links.new(node_in, node_out)
        continue

    #remove excess
    to_remove = [n for n in ng_equi.nodes if (n.name.startswith("surf_id") and (n not in nodechain))]
    for n in to_remove.copy(): 
        ng_equi.nodes.remove(n)

    #avoid feedback loop
    update_manual_uuid_surfaces.pause = False 
    #performance boost 
    psy.hide_viewport = _hide_viewport

    return None 

def update_frame_start_end_nodegroup():
    """update start/end frame nodegroup"""

    scene = bpy.context.scene
    if (not scene):
        return None

    #change value in nodegroup
    did_act = False
    for ng in [ng for ng in bpy.data.node_groups if ng.name.startswith(".S Handler Frame")]:
        if (ng.nodes["frame_start"].integer!=int(scene.frame_start)):
            ng.nodes["frame_start"].integer = scene.frame_start
            did_act = True
        if (ng.nodes["frame_end"].integer!=int(scene.frame_end)):
            ng.nodes["frame_end"].integer = scene.frame_end
            did_act = True
        continue
        
    if (did_act):
        dprint("HANDLER: update_frame_start_end_nodegroup(): Updated nodegroups values", depsgraph=True,)

    return None

def factory_viewport_method_proxy(api, bool_api):
    """special case update fct generator for viewport_method enum ui, we created BoolProperty proxy for interface
    this function is the update function of these properties, they will set the appropiate EnumProperty value"""

    #access self attr
    _f = factory_viewport_method_proxy

    def fct(self, context):

        nonlocal api, bool_api

        #avoid feedback loop
        if (_f.pause):
            return None  
        _f.pause = True

        #dprint(f"UPD: factory_viewport_method_proxy() bool_api={bool_api}")

        #update viewport enum property from bool values
        match bool_api:
            case 'screen':
                setattr(self,f"{api}_viewport_method","except_rendered")
            case 'shaded':
                setattr(self,f"{api}_viewport_method","viewport_only")
            case 'render':
                setattr(self,f"{api}_viewport_method","viewport_and_render")

        #avoid feedback loop
        _f.pause = False

        return None 

    return fct

factory_viewport_method_proxy.pause = False #singleton
def ensure_viewport_method_interface(psy, api, value,):
    """ensure values of BoolProperty are in synch with EnumProperty """

    #stop update funcs to avoid feedback loop
    global factory_viewport_method_proxy
    factory_viewport_method_proxy.pause = True
    
    screen = getattr(psy, f"{api}_allow_screen",)
    shaded = getattr(psy, f"{api}_allow_shaded",)
    render = getattr(psy, f"{api}_allow_render",)
    
    #dprint(f"UPD: ensure_viewport_method_interface() value={value}, scr/sh/rdr={screen,shaded,render}")

    #"except_rendered"     == screen
    #"viewport_only"       == screen + shaded
    #"viewport_and_render" == screen + shaded + render

    match value:
        case 'except_rendered':
            if not screen: setattr(psy, f"{api}_allow_screen", True,)
            if     shaded: setattr(psy, f"{api}_allow_shaded", False,)
            if     render: setattr(psy, f"{api}_allow_render", False,)
        case 'viewport_only':
            if not screen: setattr(psy, f"{api}_allow_screen", True,)
            if not shaded: setattr(psy, f"{api}_allow_shaded", True,)
            if     render: setattr(psy, f"{api}_allow_render", False,)
        case 'viewport_and_render':
            if not screen: setattr(psy, f"{api}_allow_screen", True,)
            if not shaded: setattr(psy, f"{api}_allow_shaded", True,)
            if not render: setattr(psy, f"{api}_allow_render", True,)

    #avoid feedback loop
    factory_viewport_method_proxy.pause = False
    return None


# def ensure_s_surface_evaluator():
#     """bugfix: it seems that if user delete an emitter and CTRL+Z, the emitter will not be present in the s_surface_evaluator first input anymore""" #HUMMM is this really needed? user just need to quit and reload blender. + it's hard to del an emitter intentionally
        
#     for p in [p for p in bpy.context.scene.scatter5.get_all_psys(search_mode="all", also_linked=True) if p.linked]:
#         e = p.id_data
#         m = p.get_scatter_mod(strict=True, raise_exception=False,)
#         if (not m.node_group):
#             continue
#         n = m.node_group.get("s_surface_evaluator")
#         if (n and not n.inputs[0].default_value):
#             n.inputs[0].default_value = e if (p.s_surface_method=='emitter') else None
#         continue
    
#     return None

# def ensure_buggy_links():
#     """sometimes blender remove some important link in the scatter-engine nodetree, very odd""" #NO LONGER AN ISSUE?
        
#     for ng in bpy.data.node_groups: 
#         if ng.name.startswith(".Geo-Scatter Engine"): 
    
#             node_in  = ng.nodes["Collection Info"].outputs[0]
#             node_out = ng.nodes["Reroute.792"].inputs[0]

#             # Check if node_in is already linked to node_in
#             if (len(node_in.links)==0):

#                 #link the two inputs
#                 ng.links.new(node_in, node_out)
                
#             continue
    
#     return None

def ensure_str_ptr_accuracy(emitter):
    """we sometimes use str properties in order to find some data in the scene,
    the problem with this technique is that it relies on datablock name, and if the user change the name of this datablock, either voluntarily, or during an append
    then the properties string are no longer representing an actual datablock. to solve this we need to find values from the nodetree, and place their name back in the scatter properties"""
            
    #avoid sending any update notification to update the nodetree
    with bpy.context.scene.scatter5.factory_update_pause(factory=True):
        
        #for every psys
        for p in emitter.scatter5.particle_systems:
            
            if (p.s_surface_collection):
                coll = get_node(p, "s_surface_evaluator").inputs[2].default_value
                if (p.s_surface_collection!=coll.name):
                    p.s_surface_collection=coll.name
            
            if (p.s_distribution_projempties_coll_ptr):
                coll = get_node(p, "s_distribution_projempties").inputs[1].default_value
                if (p.s_distribution_projempties_coll_ptr!=coll.name):
                    p.s_distribution_projempties_coll_ptr=coll.name
            
            if (p.s_mask_boolvol_coll_ptr):
                coll = get_node(p, "s_mask_boolvol").inputs[1].default_value
                if (p.s_mask_boolvol_coll_ptr!=coll.name):
                    p.s_mask_boolvol_coll_ptr=coll.name
            
            if (p.s_mask_upward_coll_ptr):
                coll = get_node(p, "s_mask_upward").inputs[1].default_value
                if (p.s_mask_upward_coll_ptr!=coll.name):
                    p.s_mask_upward_coll_ptr=coll.name
            
            if (p.s_proximity_repel1_coll_ptr):
                coll = get_node(p, "s_proximity_repel1").inputs[3].default_value
                if (p.s_proximity_repel1_coll_ptr!=coll.name):
                    p.s_proximity_repel1_coll_ptr=coll.name
            
            if (p.s_proximity_repel2_coll_ptr):
                coll = get_node(p, "s_proximity_repel2").inputs[3].default_value
                if (p.s_proximity_repel2_coll_ptr!=coll.name):
                    p.s_proximity_repel2_coll_ptr=coll.name
            
            if (p.s_visibility_camoccl_coll_ptr):
                coll = get_node(p, "s_visibility_cam").inputs[14].default_value
                if (p.s_visibility_camoccl_coll_ptr!=coll.name):
                    p.s_visibility_camoccl_coll_ptr=coll.name
            
            continue
        
        for g in emitter.scatter5.particle_groups:
            
            #gather the first psy member of this group.
            p = None
            for p in g.get_psy_members():
                break
            if (p is None):
                continue
            
            if (g.s_gr_mask_boolvol_coll_ptr):
                coll = get_node(p, "s_gr_mask_boolvol").inputs[1].default_value
                if (g.s_gr_mask_boolvol_coll_ptr!=coll.name):
                    g.s_gr_mask_boolvol_coll_ptr=coll.name
                
            if (g.s_gr_mask_upward_coll_ptr):
                coll = get_node(p, "s_gr_mask_upward").inputs[1].default_value
                if (g.s_gr_mask_upward_coll_ptr!=coll.name):
                    g.s_gr_mask_upward_coll_ptr=coll.name
            
            continue
        
    return None
                        

# ooooooooo.                         o8o               .
# `888   `Y88.                       `"'             .o8
#  888   .d88'  .ooooo.   .oooooooo oooo   .oooo.o .o888oo oooo d8b oooo    ooo
#  888ooo88P'  d88' `88b 888' `88b  `888  d88(  "8   888   `888""8P  `88.  .8'
#  888`88b.    888ooo888 888   888   888  `"Y88b.    888    888       `88..8'
#  888  `88b.  888    .o `88bod8P'   888  o.  )88b   888 .  888        `888'
# o888o  o888o `Y8bod8P' `8oooooo.  o888o 8""888P'   "888" d888b        .8'
#                        d"     YD                                  .o..P'
#                        "Y88888P'                                  `Y8P'


#this class is never instanced
class UpdatesRegistry():
    """most of our scatter-systems properties update fct are centralized in this class
    some might be generated at parsetime, final result is store in UpdatesDict""" 
    
    ################ update fct decorator factory:

    def tag_register(nbr=0):
        """update fct can either be a generator fct or just a direct update fct"""

        def tag_update_decorator(fct):
            """just mark function with tag"""

            fct.register_tag = True
            if (nbr>0):
                fct.generator_nbr = nbr 
            return fct

        return tag_update_decorator

    ################ generator for umask properties

    def codegen_umask_updatefct(scope_ref={}, name=""):
        """code generation, automatize the creation of the update functions for the universal mask system"""

        d = {}

        def _gen_mask_allow(p, prop_name, value, event=None,):
            methstr = getattr(p,f"{name}_mask_method")
            methidx = get_enum_idx(p, f"{name}_mask_method", methstr,)
            node_value(p, f"{name}.umask", value=methidx if (value) else False, entry="node_socket", socket_idx=3)
        _gen_mask_allow.register_tag = True #add tag
        d[f"{name}_mask_allow"] = _gen_mask_allow

        def _gen_mask_ptr(p, prop_name, value, event=None,):
            node_value(p, f"{name}.umask", value=value, entry="node_socket", socket_idx=1)
            update_transfer_attrs_nodegroup(p)
        _gen_mask_ptr.register_tag = True #add tag
        d[f"{name}_mask_ptr"] = _gen_mask_ptr

        def _gen_mask_reverse(p, prop_name, value, event=None,):
            node_value(p, f"{name}.umask", value=value, entry="node_socket", socket_idx=2)
        _gen_mask_reverse.register_tag = True #add tag
        d[f"{name}_mask_reverse"] = _gen_mask_reverse

        def _gen_mask_method(p, prop_name, value, event=None,):
            node_value(p, f"{name}.umask", value=get_enum_idx(p, prop_name, value,), entry="node_socket", socket_idx=3) #/!\ 1: also update fix_nodetrees()
        _gen_mask_method.register_tag = True #add tag
        d[f"{name}_mask_method"] = _gen_mask_method

        def _gen_mask_color_sample_method(p, prop_name, value, event=None,):
            node_value(p, f"{name}.umask", value=get_enum_idx(p, prop_name, value,), entry="node_socket", socket_idx=4)
        _gen_mask_color_sample_method.register_tag = True #add tag
        d[f"{name}_mask_color_sample_method"] = _gen_mask_color_sample_method

        def _gen_mask_id_color_ptr(p, prop_name, value, event=None,):
            node_value(p, f"{name}.umask", value=color_type(value), entry="node_socket", socket_idx=5)
        _gen_mask_id_color_ptr.register_tag = True #add tag
        d[f"{name}_mask_id_color_ptr"] = _gen_mask_id_color_ptr

        def _gen_mask_bitmap_ptr(p, prop_name, value, event=None,):
            node_value(p, f"{name}.umask", value=bpy.data.images.get(value), entry="node_socket", socket_idx=11)
        _gen_mask_bitmap_ptr.register_tag = True #add tag
        d[f"{name}_mask_bitmap_ptr"] = _gen_mask_bitmap_ptr

        def _gen_mask_bitmap_uv_ptr(p, prop_name, value, event=None,):
            node_value(p, f"{name}.umask", value=value, entry="node_socket", socket_idx=12)
            update_transfer_attrs_nodegroup(p)
        _gen_mask_bitmap_uv_ptr.register_tag = True #add tag
        d[f"{name}_mask_bitmap_uv_ptr"] = _gen_mask_bitmap_uv_ptr
    
        def _gen_mask_noise_space(p, prop_name, value, event=None,):
            node_value(p, f"{name}.umask", value=value=='local', entry="node_socket", socket_idx=13)
        _gen_mask_noise_space.register_tag = True #add tag
        d[f"{name}_mask_noise_space"] = _gen_mask_noise_space
        
        def _gen_mask_noise_scale(p, prop_name, value, event=None,):
            node_value(p, f"{name}.umask", value=value, entry="node_socket", socket_idx=7)
        _gen_mask_noise_scale.register_tag = True #add tag
        d[f"{name}_mask_noise_scale"] = _gen_mask_noise_scale

        def _gen_mask_noise_seed(p, prop_name, value, event=None,): 
            node_value(p, f"{name}.umask", value=value, entry="node_socket", socket_idx=8)
        _gen_mask_noise_seed.register_tag = True #add tag
        d[f"{name}_mask_noise_seed"] = _gen_mask_noise_seed

        def _gen_mask_noise_is_random_seed(p, prop_name, value, event=None,): 
            random_seed(p, event, api_is_random=f"{name}_mask_noise_is_random_seed", api_seed=f"{name}_mask_noise_seed")
        _gen_mask_noise_is_random_seed.register_tag = True #add tag
        d[f"{name}_mask_noise_is_random_seed"] = _gen_mask_noise_is_random_seed

        def _gen_mask_noise_brightness(p, prop_name, value, event=None,):
            node_value(p, f"{name}.umask", value=value, entry="node_socket", socket_idx=9)
        _gen_mask_noise_brightness.register_tag = True #add tag
        d[f"{name}_mask_noise_brightness"] = _gen_mask_noise_brightness

        def _gen_mask_noise_contrast(p, prop_name, value, event=None,):
            node_value(p, f"{name}.umask", value=value, entry="node_socket", socket_idx=10)
        _gen_mask_noise_contrast.register_tag = True #add tag
        d[f"{name}_mask_noise_contrast"] = _gen_mask_noise_contrast

        #define objects in dict
        scope_ref.update(d)
        return d

    ################ list of all our updatefunction, can be generator:

    # .dP"Y8 88  88  dP"Yb  Yb        dP   88  88 88 8888b.  888888
    # `Ybo." 88  88 dP   Yb  Yb  db  dP    88  88 88  8I  Yb 88__
    # o.`Y8b 888888 Yb   dP   YbdPYbdP     888888 88  8I  dY 88""
    # 8bodP' 88  88  YbodP     YP  YP      88  88 88 8888Y"  888888

    @tag_register()
    def hide_viewport(p, prop_name, value, event=None,):
        if (p.scatter_obj.hide_viewport!=value):
            p.scatter_obj.hide_viewport = value
        #also update geonode mod!
        from ... __init__ import addon_prefs
        mod = p.get_scatter_mod(strict=True, raise_exception=False,)
        if (mod):
            if (addon_prefs().opti_also_hide_mod):
                if (mod.show_viewport==value): mod.show_viewport = not value
            else:
                if (mod.show_viewport==False): mod.show_viewport = True

    @tag_register()
    def hide_render(p, prop_name, value, event=None,):
        if (p.scatter_obj.hide_render!=value):
            p.scatter_obj.hide_render = value
        #also update geonode mod!
        from ... __init__ import addon_prefs
        mod = p.get_scatter_mod(strict=True, raise_exception=False,)
        if (mod):
            if (addon_prefs().opti_also_hide_mod):
                if (mod.show_render==value): mod.show_render = not value
            else:
                if (mod.show_render==False): mod.show_render = True

    #  dP""b8  dP"Yb  88      dP"Yb  88""Yb
    # dP   `" dP   Yb 88     dP   Yb 88__dP
    # Yb      Yb   dP 88  .o Yb   dP 88"Yb
    #  YboodP  YbodP  88ood8  YbodP  88  Yb 

    # #Since 5.5.0 we use a getter/setter
    # @tag_register()
    # def s_color(p, prop_name, value, event=None,):
    #     so = p.scatter_obj
    #     if (so):
    #         so.color = value if (len(value)==4) else (value[0],value[1],value[2],1) if (len(value)==3) else (0,0,0,1)
                
    # .dP"Y8 88   88 88""Yb 888888    db     dP""b8 888888
    # `Ybo." 88   88 88__dP 88__     dPYb   dP   `" 88__
    # o.`Y8b Y8   8P 88"Yb  88""    dP__Yb  Yb      88""
    # 8bodP' `YbodP' 88  Yb 88     dP""""Yb  YboodP 888888

    @tag_register()
    def s_surface_method(p, prop_name, value, event=None,):
        
        #some distribution methods, with some settings enabled, don't use surfaces at all
        if (p.s_distribution_method in ("projbezarea","projbezline","projempties")):
            projenabled = getattr(p, f"s_distribution_{p.s_distribution_method}_projenabled")
            if (not projenabled):
                set_keyword(p, "nosurf", element=2,)
                p.is_using_surf = False
                return None
        
        #precise if this system is using the surfaces
        if (not p.is_using_surf):
            p.is_using_surf = True
            
        #set the main surface evaluation nodegroup to "use multi surface" or not
        usemultisurf = value=="collection"
        node_value(p, "s_surface_evaluator", value=usemultisurf, entry="node_socket", socket_idx=1)
        
        #update nodetree keyword info
        surfinfo = "multisurf" if (value=="collection") else "singlesurf"
        set_keyword(p, surfinfo, element=2,)
        
        #update pointers two methods shares the same obj ptr spot in the nodetree
        if (value in ("emitter","object")):
            surfobj = p.id_data if (value=="emitter") else p.s_surface_object
            node_value(p, "s_surface_evaluator", value=surfobj, entry="node_socket", socket_idx=0)
        
        #update square area value
        p.get_surfaces_square_area(evaluate="init_only", eval_modifiers=True, get_selection=False,)

        #refresh uuid?
        if (p.s_distribution_method=="manual_all"):
            update_manual_uuid_surfaces(force_update=True, flush_uuid_cache=p.uuid,)

    @tag_register()
    def s_surface_object(p, prop_name, value, event=None,):
        if (p.s_surface_method=="object"):
            node_value(p, "s_surface_evaluator", value=p.s_surface_object, entry="node_socket", socket_idx=0)

        #update square area value
        p.get_surfaces_square_area(evaluate="init_only", eval_modifiers=True, get_selection=False,)

        #refresh uuid?
        if (p.s_distribution_method=="manual_all"):
            update_manual_uuid_surfaces(force_update=True, flush_uuid_cache=p.uuid,)

    @tag_register()
    def s_surface_collection(p, prop_name, value, event=None,):
        node_value(p, "s_surface_evaluator", value=bpy.data.collections.get(p.s_surface_collection), entry="node_socket", socket_idx=2)
        
        #update square area value
        p.get_surfaces_square_area(evaluate="init_only", eval_modifiers=True, get_selection=False,)
        
        #refresh uuid?
        if (p.s_distribution_method=="manual_all"):
            update_manual_uuid_surfaces(force_update=True, flush_uuid_cache=p.uuid,)

    # 8888b.  88 .dP"Y8 888888 88""Yb 88 88""Yb 88   88 888888 88  dP"Yb  88b 88
    #  8I  Yb 88 `Ybo."   88   88__dP 88 88__dP 88   88   88   88 dP   Yb 88Yb88
    #  8I  dY 88 o.`Y8b   88   88"Yb  88 88""Yb Y8   8P   88   88 Yb   dP 88 Y88
    # 8888Y"  88 8bodP'   88   88  Yb 88 88oodP `YbodP'   88   88  YbodP  88  Y8

    @tag_register()
    def s_distribution_method(p, prop_name, value, event=None,):

        #refresh surfaces methods, will refresh p.is_using_surf as well
        
        p.s_surface_method = p.s_surface_method 
        
        #if using custom distribution algos that are relying on scatter_obj.mesh, swap meshes
        
        if ((p.scatter_obj) and (value in ("manual_all","physics"))):
            so = p.scatter_obj
            assert so.data, f"ERROR: s_distribution_method(): It seems that somehow, your scatter_obj mesh is missing? What happened? {so}"
            
            #the following are if we didn't set up the distmesh system yet. distmesh was implemented in Geo-Scatter 5.5.0
            if (not so.data.name.startswith(".distmesh")):
                so.data.name = f".distmesh_manual_all:{p.uuid}"
            #if the pointers are empty, we assign them
            if (not so.scatter5.distmesh_manual_all):
                so.scatter5.distmesh_manual_all = so.data
            if (not so.scatter5.distmesh_physics):
                so.scatter5.distmesh_physics = bpy.data.meshes.new(f".distmesh_physics:{p.uuid}")
                
            #we swap mesh data according to custom distribution method
            propname = f"distmesh_{value}"
            mesh = getattr(so.scatter5, propname)
            assert mesh
            so.data = mesh
            
        #link noodle distribution methods in nodetree
        
        node_link(p, prop_name, value,)
        node_link(p, prop_name+"_N", value+"_N",)

        #update nodetree local/global distribution keyword info & update dependencies    

        match value:
            
            case "random":
                set_keyword(p, "random", element=0,) #set distribution keyword
                p.s_distribution_space = p.s_distribution_space #send refresh signal to distribution space
                
            case "clumping":
                set_keyword(p, "clumping", element=0,) #set distribution keyword
                p.s_distribution_clump_space = p.s_distribution_clump_space #send refresh signal to distribution space
            
            case "verts"|"faces"|"edges":
                #v/f/e distributions uses local usrfaces, but does support local
                set_keyword(p, value, element=0,) #set distribution keyword
                p.s_distribution_vfe_space = p.s_distribution_vfe_space #send refresh signal to distribution space
                
            case "volume":
                #volume dist..
                set_keyword(p, "volume", element=0,) #set distribution keyword
                p.s_distribution_volume_space = p.s_distribution_volume_space #send refresh signal to distribution space
                
            case "projbezarea"|"projbezline"|"projempties":
                #projection distributions are evaluating global surfaces only
                set_keyword(p, value, element=0,) #set distribution keyword
                set_keyword(p, "global", element=1,) #set space keyword, force global
                node_value(p, "use_local_surfaces", value=False, entry="boolean_input")

            case "random_stable"|"manual_all":
                #random stable and manual distribution uses local only surfaces
                set_keyword(p, value, element=0,) #set distribution keyword
                set_keyword(p, "local", element=1,) #set space keyword, force local
                node_value(p, "use_local_surfaces", value=True, entry="boolean_input")
            
        #some distribution methods have special exclusive properties of existing features, we need to refresh their values, as they share the same settings in the nodetree
        
        if (value=="projbezarea" and not p.is_using_surf):
            p.s_rot_align_z_method_projbezareanosurf_special = p.s_rot_align_z_method_projbezareanosurf_special
            p.s_rot_align_y_method_projbezareanosurf_special = p.s_rot_align_y_method_projbezareanosurf_special
            p.s_push_dir_method_projbezareanosurf_special = p.s_push_dir_method_projbezareanosurf_special
        elif (value=="projbezline" and not p.is_using_surf):
            p.s_rot_align_z_method_projbezlinenosurf_special = p.s_rot_align_z_method_projbezlinenosurf_special
            p.s_rot_align_y_method_projbezlinenosurf_special = p.s_rot_align_y_method_projbezlinenosurf_special
            p.s_push_dir_method_projbezlinenosurf_special = p.s_push_dir_method_projbezlinenosurf_special
        elif (value=="projempties" and not p.is_using_surf):
            p.s_rot_align_z_method_projemptiesnosurf_special = p.s_rot_align_z_method_projemptiesnosurf_special
            p.s_rot_align_y_method_projemptiesnosurf_special = p.s_rot_align_y_method_projemptiesnosurf_special
            p.s_push_dir_method_projemptiesnosurf_special = p.s_push_dir_method_projemptiesnosurf_special
        else: 
            p.s_rot_align_z_method = p.s_rot_align_z_method
            p.s_rot_align_y_method = p.s_rot_align_y_method
            p.s_push_dir_method = p.s_push_dir_method
                
        #do we need to enable the part of the nodetree that automatically transfer all vg/vcol/uv ect.. attributes from surfaces to point?
        
        needtransferattr = False
        if (value in ("manual_all","volume")): #manual mode and volume dist need an attr transfer
            needtransferattr = True
        elif (value in ("projbezarea","projbezline","projempties") and p.is_using_surf): #projection distribution need a transfer if the projection option is disabled
            needtransferattr = True
                
        node_link(p, f"RR_GEO use_attr_transfer Receptor", f"RR_GEO use_attr_transfer {needtransferattr}",)
        mute_color(p, "Attr Transfer?", mute=not needtransferattr,)
        
        return None

    #Random Distribution 

    @tag_register()
    def s_distribution_space(p, prop_name, value, event=None,):
        if (p.s_distribution_method=="random"):
            node_value(p, "use_local_surfaces", value=value=="local", entry="boolean_input")
            set_keyword(p, value, element=1,)

    @tag_register()
    def s_distribution_is_count_method(p, prop_name, value, event=None,):
        node_value(p, "s_distribution_random", value=p.s_distribution_count if (value=="count") else -1, entry="node_socket", socket_idx=2)
    
    @tag_register()
    def s_distribution_count(p, prop_name, value, event=None,):
        if (p.s_distribution_is_count_method=="count"):
            node_value(p, "s_distribution_random", value=value, entry="node_socket", socket_idx=2)
    
    @tag_register()
    def s_distribution_density(p, prop_name, value, event=None,):
        node_value(p, "s_distribution_random", value=value, entry="node_socket", socket_idx=3)
    
    @tag_register()
    def s_distribution_limit_distance_allow(p, prop_name, value, event=None,):
        node_value(p, "s_distribution_random", value=value, entry="node_socket", socket_idx=5)
    
    @tag_register()
    def s_distribution_limit_distance(p, prop_name, value, event=None,):
        node_value(p, "s_distribution_random", value=value, entry="node_socket", socket_idx=6)
    
    @tag_register()
    def s_distribution_seed(p, prop_name, value, event=None,):
        node_value(p, "s_distribution_random", value=value, entry="node_socket", socket_idx=4)
    
    @tag_register()
    def s_distribution_is_random_seed(p, prop_name, value, event=None,):
        random_seed(p, event, api_is_random=prop_name, api_seed="s_distribution_seed", )

    #Verts

    @tag_register()
    def s_distribution_vfe_space(p, prop_name, value, event=None,):
        if (p.s_distribution_method in ("verts","faces","edges")):
            node_value(p, "use_local_surfaces", value=True, entry="boolean_input") #we need to feed local surfaces only to the verts/edges/faces distribution
            set_keyword(p, value, element=1,)
            
    #Faces

    #Edges

    @tag_register()
    def s_distribution_edges_selection_method(p, prop_name, value, event=None,):
        node_value(p, "s_distribution_edges", value=get_enum_idx(p, prop_name, value,)-1, entry="node_socket", socket_idx=2)
    
    @tag_register()
    def s_distribution_edges_position_method(p, prop_name, value, event=None,):
        node_value(p, "s_distribution_edges", value=0 if (value=="center") else 1, entry="node_socket", socket_idx=3)

    #Volume

    @tag_register()
    def s_distribution_volume_method(p, prop_name, value, event=None,):
        node_value(p, "s_distribution_volume", value=get_enum_idx(p, prop_name, value,), entry="node_socket", socket_idx=7)
    
    @tag_register()
    def s_distribution_volume_space(p, prop_name, value, event=None,):
        if (p.s_distribution_method=="volume"):
            node_value(p, "use_local_surfaces", value=value=="local", entry="boolean_input")
            set_keyword(p, value, element=1,)
            
    @tag_register()
    def s_distribution_volume_is_count_method(p, prop_name, value, event=None,):
       node_value(p, "s_distribution_volume", p.s_distribution_volume_count if (value=="count") else -1, entry="node_socket", socket_idx=2)

    @tag_register() 
    def s_distribution_volume_count(p, prop_name, value, event=None,):
        if (p.s_distribution_volume_is_count_method=="count"):
           node_value(p, "s_distribution_volume", value, entry="node_socket", socket_idx=2)

    @tag_register()
    def s_distribution_volume_density(p, prop_name, value, event=None,):
        node_value(p, "s_distribution_volume", value=value, entry="node_socket", socket_idx=3)
    
    @tag_register()
    def s_distribution_volume_seed(p, prop_name, value, event=None,):
        node_value(p, "s_distribution_volume", value=value, entry="node_socket", socket_idx=4)
    
    @tag_register()
    def s_distribution_volume_is_random_seed(p, prop_name, value, event=None,):
        random_seed(p, event, api_is_random=prop_name, api_seed="s_distribution_volume_seed", )
    
    @tag_register()
    def s_distribution_volume_limit_distance_allow(p, prop_name, value, event=None,):
        node_value(p, "s_distribution_volume", value=value, entry="node_socket", socket_idx=5)
    
    @tag_register()
    def s_distribution_volume_limit_distance(p, prop_name, value, event=None,):
        node_value(p, "s_distribution_volume", value=value, entry="node_socket", socket_idx=6)
        
    @tag_register()
    def s_distribution_volume_voxelsize(p, prop_name, value, event=None,):
        node_value(p, "s_distribution_volume", value=value, entry="node_socket", socket_idx=8)
        
    @tag_register()
    def s_distribution_volume_grid_spacing(p, prop_name, value, event=None,):
        node_value(p, "s_distribution_volume", value=value, entry="node_socket", socket_idx=9)

    #Project Bezier Area
    
    @tag_register()
    def s_distribution_projbezarea_curve_ptr(p, prop_name, value, event=None,):
        node_value(p, "s_distribution_projbezarea", value=value, entry="node_socket", socket_idx=5)
        
    @tag_register()
    def s_distribution_projbezarea_space(p, prop_name, value, event=None,):
        node_value(p, "s_distribution_projbezarea", value=value=="local", entry="node_socket", socket_idx=6)
    
    @tag_register()
    def s_distribution_projbezarea_density(p, prop_name, value, event=None,):
        node_value(p, "s_distribution_projbezarea", value=value, entry="node_socket", socket_idx=1)

    @tag_register()
    def s_distribution_projbezarea_seed(p, prop_name, value, event=None,):
        node_value(p, "s_distribution_projbezarea", value=value, entry="node_socket", socket_idx=2)

    @tag_register()
    def s_distribution_projbezarea_is_random_seed(p, prop_name, value, event=None,):
        random_seed(p, event, api_is_random=prop_name, api_seed="s_distribution_projbezarea_seed",)
        
    @tag_register()
    def s_distribution_projbezarea_limit_distance_allow(p, prop_name, value, event=None,):
        node_value(p, "s_distribution_projbezarea", value=value, entry="node_socket", socket_idx=3)

    @tag_register()
    def s_distribution_projbezarea_limit_distance(p, prop_name, value, event=None,):
        node_value(p, "s_distribution_projbezarea", value=value, entry="node_socket", socket_idx=4)
        
    @tag_register()
    def s_distribution_projbezarea_projenabled(p, prop_name, value, event=None,):
        p.s_distribution_method = p.s_distribution_method #also need to send refresh signal to dist method, so we can update the consequence of not attaching the point to the surfaces
        node_value(p, "s_distribution_projbezarea", value=value, entry="node_socket", socket_idx=7)
        
    @tag_register()
    def s_distribution_projbezarea_projlength(p, prop_name, value, event=None,):
        node_value(p, "s_distribution_projbezarea", value=value, entry="node_socket", socket_idx=8)

    @tag_register()
    def s_distribution_projbezarea_projaxis(p, prop_name, value, event=None,):
        node_value(p, "s_distribution_projbezarea", value=get_enum_idx(p, prop_name, value,), entry="node_socket", socket_idx=9)

    #Project Bezier Line 
    
    @tag_register()
    def s_distribution_projbezline_curve_ptr(p, prop_name, value, event=None,):
        node_value(p, f"s_distribution_projbezline.{prop_name}", value=value, entry="node_socket", socket_idx=0)

    @tag_register()
    def s_distribution_projbezline_space(p, prop_name, value, event=None,):
        node_value(p, f"s_distribution_projbezline.s_distribution_projbezline_space_is_local", value=value=="local", entry="boolean_input")

    @tag_register()
    def s_distribution_projbezline_method(p, prop_name, value, event=None,):
        node_value(p, f"s_distribution_projbezline.{prop_name}", value=get_enum_idx(p, prop_name, value,), entry="integer_input")
    
    @tag_register()
    def s_distribution_projbezline_normal_method(p, prop_name, value, event=None,):
        node_value(p, f"s_distribution_projbezline.{prop_name}", value=get_enum_idx(p, prop_name, value,), entry="integer_input")
    
    @tag_register()
    def s_distribution_projbezline_is_count_method(p, prop_name, value, event=None,):
        node_value(p, "s_distribution_projbezline.s_distribution_projbezline_count", value=p.s_distribution_projbezline_count if (value=="count") else -1, entry="integer_input")
        
    @tag_register()
    def s_distribution_projbezline_count(p, prop_name, value, event=None,):
        if (p.s_distribution_projbezline_is_count_method=="count"):
            node_value(p, f"s_distribution_projbezline.{prop_name}", value=value, entry="integer_input")
    
    @tag_register()
    def s_distribution_projbezline_onspline_density(p, prop_name, value, event=None,):
        node_value(p, f"s_distribution_projbezline.{prop_name}", value=value, entry="float_input")

    @tag_register()
    def s_distribution_projbezline_patharea_density(p, prop_name, value, event=None,):
        node_value(p, f"s_distribution_projbezline.{prop_name}", value=value, entry="float_input")
        
    @tag_register()
    def s_distribution_projbezline_patharea_width(p, prop_name, value, event=None,): 
        node_value(p, f"s_distribution_projbezline.{prop_name}", value=value, entry="float_input")
        
    @tag_register()
    def s_distribution_projbezline_patharea_falloff(p, prop_name, value, event=None,): 
        node_value(p, f"s_distribution_projbezline.{prop_name}", value=value, entry="float_input")
        
    @tag_register()
    def s_distribution_projbezline_patharea_seed(p, prop_name, value, event=None,): 
        node_value(p, f"s_distribution_projbezline.{prop_name}", value=value, entry="integer_input")
    
    @tag_register()
    def s_distribution_projbezline_patharea_is_random_seed(p, prop_name, value, event=None,): 
        random_seed(p, event, api_is_random=prop_name, api_seed="s_distribution_projbezline_patharea_seed",)
        
    @tag_register()
    def s_distribution_projbezline_patharea_radiusinfl_allow(p, prop_name, value, event=None,):
        mute_node(p, "s_distribution_projbezline.radiusinfl_allow1",mute=not value)
        mute_node(p, "s_distribution_projbezline.radiusinfl_allow2",mute=not value)
        mute_node(p, "s_distribution_projbezline.radiusinfl_allow3",mute=not value)
    
    @tag_register()
    def s_distribution_projbezline_patharea_radiusinfl_factor(p, prop_name, value, event=None,):
        node_value(p, f"s_distribution_projbezline.{prop_name}", value=value, entry="float_input")

    @tag_register()
    def s_distribution_projbezline_randoff_allow(p, prop_name, value, event=None,):
        node_value(p, f"s_distribution_projbezline.{prop_name}", value=value, entry="boolean_input")
        
    @tag_register()
    def s_distribution_projbezline_randoff_dist(p, prop_name, value, event=None,):
        node_value(p, f"s_distribution_projbezline.{prop_name}", value=value, entry="float_input")
        
    @tag_register()
    def s_distribution_projbezline_randoff_seed(p, prop_name, value, event=None,):
        node_value(p, f"s_distribution_projbezline.{prop_name}", value=value, entry="integer_input")

    @tag_register()
    def s_distribution_projbezline_randoff_is_random_seed(p, prop_name, value, event=None,):
       random_seed(p, event, api_is_random=prop_name, api_seed="s_distribution_projbezline_randoff_seed",)
    
    @tag_register()
    def s_distribution_projbezline_creatrow_allow(p, prop_name, value, event=None,):
        node_value(p, f"s_distribution_projbezline.{prop_name}", value=value, entry="boolean_input")
        
    @tag_register()
    def s_distribution_projbezline_creatrow_rows(p, prop_name, value, event=None,):
        node_value(p, f"s_distribution_projbezline.{prop_name}", value=value, entry="integer_input")
        
    @tag_register()
    def s_distribution_projbezline_creatrow_dist(p, prop_name, value, event=None,):
        node_value(p, f"s_distribution_projbezline.{prop_name}", value=value, entry="float_input")

    @tag_register()
    def s_distribution_projbezline_creatrow_shift(p, prop_name, value, event=None,):
        node_value(p, f"s_distribution_projbezline.{prop_name}", value=value, entry="float_input")
    
    @tag_register()
    def s_distribution_projbezline_creatrow_dir(p, prop_name, value, event=None,):
        node_value(p, f"s_distribution_projbezline.{prop_name}", value=get_enum_idx(p, prop_name, value,), entry="integer_input")
        
    @tag_register()
    def s_distribution_projbezline_spread_allow(p, prop_name, value, event=None,):
        node_value(p, f"s_distribution_projbezline.{prop_name}", value=value, entry="boolean_input")

    @tag_register()
    def s_distribution_projbezline_spread_method(p, prop_name, value, event=None,): 
        node_value(p, f"s_distribution_projbezline.{prop_name}", value=get_enum_idx(p, prop_name, value,), entry="integer_input")

    @tag_register()
    def s_distribution_projbezline_spread_dir(p, prop_name, value, event=None,):
        node_value(p, f"s_distribution_projbezline.{prop_name}", value=get_enum_idx(p, prop_name, value,), entry="integer_input")
        
    # @tag_register()
    # def s_distribution_projbezline_spread_offset(p, prop_name, value, event=None,):
    #     node_value(p, f"s_distribution_projbezline.{prop_name}", value=value, entry="float_input")

    @tag_register()
    def s_distribution_projbezline_spread_falloff(p, prop_name, value, event=None,):
        node_value(p, f"s_distribution_projbezline.{prop_name}", value=value, entry="float_input")
        
    @tag_register()
    def s_distribution_projbezline_spread_seed(p, prop_name, value, event=None,):
        node_value(p, f"s_distribution_projbezline.{prop_name}", value=value, entry="integer_input")

    @tag_register()
    def s_distribution_projbezline_spread_is_random_seed(p, prop_name, value, event=None,):
        random_seed(p, event, api_is_random=prop_name, api_seed="s_distribution_projbezline_spread_seed",)

    @tag_register()
    def s_distribution_projbezline_fallremap_allow(p, prop_name, value, event=None,):
        mute_node(p, "s_distribution_projbezline.fallremap",mute=not value)
        mute_node(p, "s_distribution_projbezline.fallremap_revert",mute=not p.s_distribution_projbezline_fallremap_revert if value else True)
        mute_node(p, "s_distribution_projbezline.fallnoisy",mute=not value)

    @tag_register()
    def s_distribution_projbezline_fallremap_revert(p, prop_name, value, event=None,):
        mute_node(p, "s_distribution_projbezline.fallremap_revert",mute=not value)
    
    @tag_register()
    def s_distribution_projbezline_fallnoisy_strength(p, prop_name, value, event=None,):
        node_value(p, "s_distribution_projbezline.fallnoisy", value=value, entry="node_socket", socket_idx=1)
    
    @tag_register()
    def s_distribution_projbezline_fallnoisy_space(p, prop_name, value, event=None,):
        node_value(p, "s_distribution_projbezline.fallnoisy", value=value=='local', entry="node_socket", socket_idx=5)
        
    @tag_register()
    def s_distribution_projbezline_fallnoisy_scale(p, prop_name, value, event=None,):
        node_value(p, "s_distribution_projbezline.fallnoisy", value=value, entry="node_socket", socket_idx=2)
    
    @tag_register()
    def s_distribution_projbezline_fallnoisy_seed(p, prop_name, value, event=None,):
        node_value(p, "s_distribution_projbezline.fallnoisy", value=value, entry="node_socket", socket_idx=3)
    
    @tag_register()
    def s_distribution_projbezline_fallnoisy_is_random_seed(p, prop_name, value, event=None,):
        random_seed(p, event, api_is_random=prop_name, api_seed="s_distribution_projbezline_fallnoisy_seed")
        
    @tag_register()
    def s_distribution_projbezline_limit_distance_allow(p, prop_name, value, event=None,):
        node_value(p, f"s_distribution_projbezline.{prop_name}", value=value, entry="boolean_input")

    @tag_register()
    def s_distribution_projbezline_limit_distance(p, prop_name, value, event=None,):
        node_value(p, f"s_distribution_projbezline.{prop_name}", value=value, entry="float_input")
        
    @tag_register()
    def s_distribution_projbezline_projenabled(p, prop_name, value, event=None,):
        p.s_distribution_method = p.s_distribution_method #also need to send refresh signal to dist method, so we can update the consequence of not attaching the point to the surfaces
        node_value(p, f"s_distribution_projbezline.{prop_name}", value=value, entry="boolean_input")
        
    @tag_register()
    def s_distribution_projbezline_projlength(p, prop_name, value, event=None,):
        node_value(p, f"s_distribution_projbezline.{prop_name}", value=value, entry="float_input")

    @tag_register()
    def s_distribution_projbezline_projaxis(p, prop_name, value, event=None,):
        node_value(p, f"s_distribution_projbezline.{prop_name}", value=get_enum_idx(p, prop_name, value,), entry="integer_input")
    
    #Project Empties
    
    @tag_register()
    def s_distribution_projempties_coll_ptr(p, prop_name, value, event=None,):
        node_value(p, "s_distribution_projempties", value=bpy.data.collections.get(value), entry="node_socket", socket_idx=1)

    @tag_register()
    def s_distribution_projempties_empty_only(p, prop_name, value, event=None,):
        node_value(p, "s_distribution_projempties", value=value, entry="node_socket", socket_idx=2)

    @tag_register()
    def s_distribution_projempties_projenabled(p, prop_name, value, event=None,):
        p.s_distribution_method = p.s_distribution_method #also need to send refresh signal to dist method, so we can update the consequence of not attaching the point to the surfaces
        node_value(p, "s_distribution_projempties", value=value, entry="node_socket", socket_idx=3)

    @tag_register()
    def s_distribution_projempties_projlength(p, prop_name, value, event=None,):
        node_value(p, "s_distribution_projempties", value=value, entry="node_socket", socket_idx=4)

    @tag_register()
    def s_distribution_projempties_projaxis(p, prop_name, value, event=None,):
        node_value(p, "s_distribution_projempties", value=get_enum_idx(p, prop_name, value,), entry="node_socket", socket_idx=5)

    #Random Stable 

    @tag_register()
    def s_distribution_stable_uv_ptr(p, prop_name, value, event=None,):
        node_value(p, "s_distribution_stable", value=value, entry="node_socket", socket_idx=7)
    
    @tag_register()
    def s_distribution_stable_is_count_method(p, prop_name, value, event=None,):
        node_value(p, "s_distribution_stable", value=p.s_distribution_stable_count if (value=="count") else -1, entry="node_socket", socket_idx=2)
    
    @tag_register()
    def s_distribution_stable_count(p, prop_name, value, event=None,):
        if (p.s_distribution_stable_is_count_method=="count"):
            node_value(p, "s_distribution_stable", value=value, entry="node_socket", socket_idx=2)
    
    @tag_register()
    def s_distribution_stable_density(p, prop_name, value, event=None,):
        node_value(p, "s_distribution_stable", value=value, entry="node_socket", socket_idx=3)
    
    @tag_register()
    def s_distribution_stable_seed(p, prop_name, value, event=None,):
        node_value(p, "s_distribution_stable", value=value, entry="node_socket", socket_idx=4)
    
    @tag_register()
    def s_distribution_stable_is_random_seed(p, prop_name, value, event=None,):
        random_seed(p, event, api_is_random=prop_name, api_seed="s_distribution_stable_seed", )
    
    @tag_register()
    def s_distribution_stable_limit_distance_allow(p, prop_name, value, event=None,):
        node_value(p, "s_distribution_stable", value=value, entry="node_socket", socket_idx=5)
    
    @tag_register()
    def s_distribution_stable_limit_distance(p, prop_name, value, event=None,):
        node_value(p, "s_distribution_stable", value=value, entry="node_socket", socket_idx=6)

    #Clump Distribution
    
    @tag_register()
    def s_distribution_clump_space(p, prop_name, value, event=None,):
        if (p.s_distribution_method=="clumping"):
            node_value(p, "use_local_surfaces", value=value=="local", entry="boolean_input")
            set_keyword(p, value, element=1,)
    
    @tag_register()
    def s_distribution_clump_density(p, prop_name, value, event=None,):
        node_value(p, "s_distribution_clump", value=value, entry="node_socket", socket_idx=3)
    
    @tag_register()
    def s_distribution_clump_limit_distance_allow(p, prop_name, value, event=None,):
        node_value(p, "s_distribution_clump", value=value, entry="node_socket", socket_idx=4)
    
    @tag_register()
    def s_distribution_clump_limit_distance(p, prop_name, value, event=None,):
        node_value(p, "s_distribution_clump", value=value, entry="node_socket", socket_idx=5)
    
    @tag_register()
    def s_distribution_clump_seed(p, prop_name, value, event=None,):
        node_value(p, "s_distribution_clump", value=value, entry="node_socket", socket_idx=6)
    
    @tag_register()
    def s_distribution_clump_is_random_seed(p, prop_name, value, event=None,):
        random_seed(p, event, api_is_random=prop_name, api_seed="s_distribution_clump_seed")
    
    @tag_register()
    def s_distribution_clump_max_distance(p, prop_name, value, event=None,):
        node_value(p, "s_distribution_clump", value=value, entry="node_socket", socket_idx=7)
    
    @tag_register()
    def s_distribution_clump_falloff(p, prop_name, value, event=None,):
        node_value(p, "s_distribution_clump", value=value, entry="node_socket", socket_idx=8)
    
    @tag_register()
    def s_distribution_clump_random_factor(p, prop_name, value, event=None,):
        node_value(p, "s_distribution_clump", value=value, entry="node_socket", socket_idx=9)

    @tag_register()
    def s_distribution_clump_children_density(p, prop_name, value, event=None,):
        node_value(p, "s_distribution_clump", value=value, entry="node_socket", socket_idx=10)
    
    @tag_register()
    def s_distribution_clump_children_limit_distance_allow(p, prop_name, value, event=None,):
        node_value(p, "s_distribution_clump", value=value, entry="node_socket", socket_idx=11)
    
    @tag_register()
    def s_distribution_clump_children_limit_distance(p, prop_name, value, event=None,):
        node_value(p, "s_distribution_clump", value=value, entry="node_socket", socket_idx=12)
    
    @tag_register()
    def s_distribution_clump_children_seed(p, prop_name, value, event=None,):
        node_value(p, "s_distribution_clump", value=value, entry="node_socket", socket_idx=13)
    
    @tag_register()
    def s_distribution_clump_children_is_random_seed(p, prop_name, value, event=None,):
        random_seed(p, event, api_is_random=prop_name, api_seed="s_distribution_clump_children_seed")
    
    @tag_register()
    def s_distribution_clump_fallremap_allow(p, prop_name, value, event=None,):
        mute_node(p, "s_distribution_clump.fallremap",mute=not value)
        mute_node(p, "s_distribution_clump.fallremap_revert",mute=not p.s_distribution_clump_fallremap_revert if value else True)
        mute_node(p, "s_distribution_clump.fallnoisy",mute=not value)

    @tag_register()
    def s_distribution_clump_fallremap_revert(p, prop_name, value, event=None,):
        mute_node(p, "s_distribution_clump.fallremap_revert",mute=not value)
    
    @tag_register()
    def s_distribution_clump_fallnoisy_strength(p, prop_name, value, event=None,):
        node_value(p, "s_distribution_clump.fallnoisy", value=value, entry="node_socket", socket_idx=1)
    
    @tag_register()
    def s_distribution_clump_fallnoisy_space(p, prop_name, value, event=None,):
        node_value(p, "s_distribution_clump.fallnoisy", value=value=='local', entry="node_socket", socket_idx=5)
        
    @tag_register()
    def s_distribution_clump_fallnoisy_scale(p, prop_name, value, event=None,):
        node_value(p, "s_distribution_clump.fallnoisy", value=value, entry="node_socket", socket_idx=2)
    
    @tag_register()
    def s_distribution_clump_fallnoisy_seed(p, prop_name, value, event=None,):
        node_value(p, "s_distribution_clump.fallnoisy", value=value, entry="node_socket", socket_idx=3)
    
    @tag_register()
    def s_distribution_clump_fallnoisy_is_random_seed(p, prop_name, value, event=None,):
        random_seed(p, event, api_is_random=prop_name, api_seed="s_distribution_clump_fallnoisy_seed")

    # 8888b.  888888 88b 88 .dP"Y8 88 888888 Yb  dP     8b    d8    db    .dP"Y8 88  dP .dP"Y8
    #  8I  Yb 88__   88Yb88 `Ybo." 88   88    YbdP      88b  d88   dPYb   `Ybo." 88odP  `Ybo."
    #  8I  dY 88""   88 Y88 o.`Y8b 88   88     8P       88YbdP88  dP__Yb  o.`Y8b 88"Yb  o.`Y8b
    # 8888Y"  888888 88  Y8 8bodP' 88   88    dP        88 YY 88 dP""""Yb 8bodP' 88  Yb 8bodP'
    
    @tag_register()
    def s_mask_master_allow(p, prop_name, value, event=None,):
        for prop in p.get_s_mask_main_features(availability_conditions=False,):
            mute_node(p, prop.replace("_allow",""), mute=not value,)

    #Vgroup
    
    @tag_register()
    def s_mask_vg_allow(p, prop_name, value, event=None,):
        mute_color(p, "Vg Mask", mute=not value,)
        node_link(p, f"RR_FLOAT s_mask_vg Receptor", f"RR_FLOAT s_mask_vg {bool(value)}",)
    
    @tag_register()
    def s_mask_vg_ptr(p, prop_name, value, event=None,):
        node_value(p, "s_mask_vg", value=value, entry="node_socket", socket_idx=2)
    
    @tag_register()
    def s_mask_vg_revert(p, prop_name, value, event=None,):
        node_value(p, "s_mask_vg", value=value, entry="node_socket", socket_idx=3)

    #VColor
    
    @tag_register()
    def s_mask_vcol_allow(p, prop_name, value, event=None,):
        mute_color(p, "Vcol Mask", mute=not value,)
        node_link(p, f"RR_FLOAT s_mask_vcol Receptor", f"RR_FLOAT s_mask_vcol {bool(value)}",)
    
    @tag_register()
    def s_mask_vcol_ptr(p, prop_name, value, event=None,):
        node_value(p, "s_mask_vcol", value=value, entry="node_socket", socket_idx=2)
    
    @tag_register()
    def s_mask_vcol_revert(p, prop_name, value, event=None,):
        node_value(p, "s_mask_vcol", value=value, entry="node_socket", socket_idx=3)
    
    @tag_register()
    def s_mask_vcol_color_sample_method(p, prop_name, value, event=None,):
        node_value(p, "s_mask_vcol", value=get_enum_idx(p, prop_name, value,), entry="node_socket", socket_idx=4)
    
    @tag_register()
    def s_mask_vcol_id_color_ptr(p, prop_name, value, event=None,):
        node_value(p, "s_mask_vcol", value=color_type(value), entry="node_socket", socket_idx=5)

    #Bitmap 
    
    @tag_register()
    def s_mask_bitmap_allow(p, prop_name, value, event=None,):
        mute_color(p, "Img Mask", mute=not value,)
        node_link(p, f"RR_GEO s_mask_bitmap Receptor", f"RR_GEO s_mask_bitmap {bool(value)}",)
        p.s_mask_bitmap_uv_ptr = p.s_mask_bitmap_uv_ptr
    
    @tag_register()
    def s_mask_bitmap_uv_ptr(p, prop_name, value, event=None,):
        node_value(p, "s_mask_bitmap", value=value, entry="node_socket", socket_idx=2)
    
    @tag_register()
    def s_mask_bitmap_ptr(p, prop_name, value, event=None,):
        node_value(p, "s_mask_bitmap", value=bpy.data.images.get(value), entry="node_socket", socket_idx=3)
    
    @tag_register()
    def s_mask_bitmap_revert(p, prop_name, value, event=None,):
        node_value(p, "s_mask_bitmap", value=not value, entry="node_socket", socket_idx=4)
    
    @tag_register()
    def s_mask_bitmap_color_sample_method(p, prop_name, value, event=None,):
        node_value(p, "s_mask_bitmap", value=get_enum_idx(p, prop_name, value,), entry="node_socket", socket_idx=5)
    
    @tag_register()
    def s_mask_bitmap_id_color_ptr(p, prop_name, value, event=None,):
        node_value(p, "s_mask_bitmap", value=color_type(value), entry="node_socket", socket_idx=6)

    #Materials
    
    @tag_register()
    def s_mask_material_allow(p, prop_name, value, event=None,):
        mute_color(p, "Mat Mask", mute=not value,)
        node_link(p, f"RR_FLOAT s_mask_material Receptor", f"RR_FLOAT s_mask_material {bool(value)}",)
    
    @tag_register()
    def s_mask_material_ptr(p, prop_name, value, event=None,):
        node_value(p, "s_mask_material", value=bpy.data.materials.get(value), entry="node_socket", socket_idx=2)
    
    @tag_register()
    def s_mask_material_revert(p, prop_name, value, event=None,):
        node_value(p, "s_mask_material", value=value, entry="node_socket", socket_idx=3)
        
    #Curves

    @tag_register()
    def s_mask_curve_allow(p, prop_name, value, event=None,):
        mute_color(p, "Cur Mask", mute=not value,)
        node_link(p, f"RR_GEO s_mask_curve Receptor", f"RR_GEO s_mask_curve {bool(value)}",)    
    
    @tag_register()
    def s_mask_curve_ptr(p, prop_name, value, event=None,):
        node_value(p, "s_mask_curve", value=value, entry="node_socket", socket_idx=1)
    
    @tag_register()
    def s_mask_curve_revert(p, prop_name, value, event=None,):
        node_value(p, "s_mask_curve", value=value, entry="node_socket", socket_idx=2)

    #Boolean
    
    @tag_register()
    def s_mask_boolvol_allow(p, prop_name, value, event=None,):
        mute_color(p, "Bool Mask", mute=not value,)
        node_link(p, f"RR_GEO s_mask_boolvol Receptor", f"RR_GEO s_mask_boolvol {bool(value)}",)
    
    @tag_register()
    def s_mask_boolvol_coll_ptr(p, prop_name, value, event=None,):
        node_value(p, "s_mask_boolvol", value=bpy.data.collections.get(value), entry="node_socket", socket_idx=1)
    
    @tag_register()
    def s_mask_boolvol_revert(p, prop_name, value, event=None,):
        node_value(p, "s_mask_boolvol", value=value, entry="node_socket", socket_idx=2)

    #Upward Obstruction

    @tag_register()
    def s_mask_upward_allow(p, prop_name, value, event=None,):
        mute_color(p, "Up Mask", mute=not value,)
        node_link(p, f"RR_GEO s_mask_upward Receptor", f"RR_GEO s_mask_upward {bool(value)}",)
    
    @tag_register()
    def s_mask_upward_coll_ptr(p, prop_name, value, event=None,):
        node_value(p, "s_mask_upward", value=bpy.data.collections.get(value), entry="node_socket", socket_idx=1)
    
    @tag_register()
    def s_mask_upward_revert(p, prop_name, value, event=None,):
        node_value(p, "s_mask_upward", value=value, entry="node_socket", socket_idx=2)

    # .dP"Y8  dP""b8    db    88     888888
    # `Ybo." dP   `"   dPYb   88     88__
    # o.`Y8b Yb       dP__Yb  88  .o 88""
    # 8bodP'  YboodP dP""""Yb 88ood8 888888
    
    @tag_register()
    def s_scale_master_allow(p, prop_name, value, event=None,):
        for prop in p.get_s_scale_main_features(availability_conditions=False,):
            mute_node(p, prop.replace("_allow",""), mute=not value,)

    #Default 
    
    @tag_register()
    def s_scale_default_allow(p, prop_name, value, event=None,):
        mute_color(p, "Default Scale", mute=not value,)
        node_link(p, f"RR_VEC s_scale_default Receptor", f"RR_VEC s_scale_default {bool(value)}",)
    
    @tag_register()
    def s_scale_default_space(p, prop_name, value, event=None,):
        node_value(p, "s_scale_default", value=value=="local", entry="node_socket", socket_idx=2)
    
    @tag_register()
    def s_scale_default_value(p, prop_name, value, event=None,):
        node_value(p, "s_scale_default", value=value, entry="node_socket", socket_idx=3)
    
    @tag_register()
    def s_scale_default_multiplier(p, prop_name, value, event=None,):
        node_value(p, "s_scale_default", value=value, entry="node_socket", socket_idx=4)

    #Random

    @tag_register()
    def s_scale_random_allow(p, prop_name, value, event=None,):
        mute_color(p, "Random Scale", mute=not value,)
        node_link(p, f"RR_VEC s_scale_random Receptor", f"RR_VEC s_scale_random {bool(value)}",)
    
    @tag_register()
    def s_scale_random_method(p, prop_name, value, event=None,):
        node_value(p, "s_scale_random", value=value=="random_uniform", entry="node_socket", socket_idx=1)
    
    @tag_register()
    def s_scale_random_factor(p, prop_name, value, event=None,):
        node_value(p, "s_scale_random", value=value, entry="node_socket", socket_idx=2)
    
    @tag_register()
    def s_scale_random_probability(p, prop_name, value, event=None,):
        node_value(p, "s_scale_random", value=value/100, entry="node_socket", socket_idx=3)
    
    @tag_register()
    def s_scale_random_seed(p, prop_name, value, event=None,):
        node_value(p, "s_scale_random", value=value, entry="node_socket", socket_idx=4)
    
    @tag_register()
    def s_scale_random_is_random_seed(p, prop_name, value, event=None,):
        random_seed(p, event, api_is_random=prop_name, api_seed="s_scale_random_seed")

    codegen_umask_updatefct(scope_ref=locals(), name="s_scale_random",)

    #Shrink 
    
    @tag_register()
    def s_scale_shrink_allow(p, prop_name, value, event=None,):
        mute_color(p, "Shrink", mute=not value,)
        node_link(p, f"RR_VEC s_scale_shrink Receptor", f"RR_VEC s_scale_shrink {bool(value)}",)
    
    @tag_register()
    def s_scale_shrink_factor(p, prop_name, value, event=None,):
        node_value(p, "s_scale_shrink", value=value, entry="node_socket", socket_idx=1)

    codegen_umask_updatefct(scope_ref=locals(), name="s_scale_shrink",)

    #Grow

    @tag_register()
    def s_scale_grow_allow(p, prop_name, value, event=None,):
        mute_color(p, "Grow", mute=not value,)
        node_link(p, f"RR_VEC s_scale_grow Receptor", f"RR_VEC s_scale_grow {bool(value)}",)
    
    @tag_register()
    def s_scale_grow_factor(p, prop_name, value, event=None,):
        node_value(p, "s_scale_grow", value=value, entry="node_socket", socket_idx=1)

    codegen_umask_updatefct(scope_ref=locals(), name="s_scale_grow",)

    #Fading 
    
    @tag_register()
    def s_scale_fading_allow(p, prop_name, value, event=None,):
        mute_color(p, "Scale Fading", mute=not value,)
        node_link(p, f"RR_VEC s_scale_fading Receptor", f"RR_VEC s_scale_fading {bool(value)}",)
        if (value==True):
            update_camera_nodegroup(force_update=True, reset_hash=True,)
    
    @tag_register()
    def s_scale_fading_factor(p, prop_name, value, event=None,):
            node_value(p, "s_scale_fading", value=value, entry="node_socket", socket_idx=2)
    
    @tag_register()
    def s_scale_fading_per_cam_data(p, prop_name, value, event=None,):
        match value:
            case True:
                active_cam = bpy.context.scene.camera
                if (active_cam is not None):
                    active_cam.scatter5.s_scale_fading_distance_per_cam_min = active_cam.scatter5.s_scale_fading_distance_per_cam_min 
                    active_cam.scatter5.s_scale_fading_distance_per_cam_max = active_cam.scatter5.s_scale_fading_distance_per_cam_max 
            case False:
                node_value(p, "s_scale_fading", value=p.s_scale_fading_distance_min, entry="node_socket", socket_idx=3)
                node_value(p, "s_scale_fading", value=p.s_scale_fading_distance_max, entry="node_socket", socket_idx=4)
    
    @tag_register()
    def s_scale_fading_distance_min(p, prop_name, value, event=None,):
        node_value(p, "s_scale_fading", value=value, entry="node_socket", socket_idx=3)
    
    @tag_register()
    def s_scale_fading_distance_max(p, prop_name, value, event=None,):
        node_value(p, "s_scale_fading", value=value, entry="node_socket", socket_idx=4)
    
    @tag_register()
    def s_scale_fading_fallremap_allow(p, prop_name, value, event=None,):
        mute_node(p, "s_scale_fading.fallremap", mute=not value)

    @tag_register()
    def s_scale_fading_fallremap_revert(p, prop_name, value, event=None,):
        mute_node(p, "s_scale_fading.fallremap_revert",mute=not value)

    #Mirror
    
    @tag_register()
    def s_scale_mirror_allow(p, prop_name, value, event=None,):
        mute_color(p, "Random Mirror", mute=not value,)
        node_link(p, f"RR_GEO s_scale_mirror Receptor", f"RR_GEO s_scale_mirror {bool(value)}",)
    
    @tag_register()
    def s_scale_mirror_is_x(p, prop_name, value, event=None,):
        node_value(p, "s_scale_mirror", value=value, entry="node_socket", socket_idx=1)
    
    @tag_register()
    def s_scale_mirror_is_y(p, prop_name, value, event=None,):
        node_value(p, "s_scale_mirror", value=value, entry="node_socket", socket_idx=2)
    
    @tag_register()
    def s_scale_mirror_is_z(p, prop_name, value, event=None,):
        node_value(p, "s_scale_mirror", value=value, entry="node_socket", socket_idx=3)
    
    @tag_register()
    def s_scale_mirror_seed(p, prop_name, value, event=None,):
        node_value(p, "s_scale_mirror", value=value, entry="node_socket", socket_idx=4)
    
    @tag_register()
    def s_scale_mirror_is_random_seed(p, prop_name, value, event=None,):
        random_seed(p, event, api_is_random=prop_name, api_seed="s_scale_mirror_seed")

    codegen_umask_updatefct(scope_ref=locals(), name="s_scale_mirror",)

    #Minimum 
    
    @tag_register()
    def s_scale_min_allow(p, prop_name, value, event=None,):
        mute_color(p, "Min Scale", mute=not value,)
        node_link(p, f"RR_VEC s_scale_min Receptor", f"RR_VEC s_scale_min {bool(value)}",)
        node_link(p, f"RR_GEO s_scale_min Receptor", f"RR_GEO s_scale_min {bool(value)}",)
    
    @tag_register()
    def s_scale_min_method(p, prop_name, value, event=None,):
        node_value(p, "s_scale_min", value=(value=="s_scale_min_remove"), entry="node_socket", socket_idx=2)
    
    @tag_register()
    def s_scale_min_value(p, prop_name, value, event=None,):
        node_value(p, "s_scale_min", value=value, entry="node_socket", socket_idx=3)

    #Clump Distribution Exlusive 

    @tag_register()
    def s_scale_clump_allow(p, prop_name, value, event=None,):
        mute_color(p, "Clump Scale", mute=not value,)
        node_link(p, f"RR_VEC s_scale_clump Receptor", f"RR_VEC s_scale_clump {bool(value)}",)
    
    @tag_register()
    def s_scale_clump_value(p, prop_name, value, event=None,):
        node_value(p, "s_scale_clump", value=value, entry="node_socket", socket_idx=2)

    #Faces Distribution Exlusive 
    
    @tag_register()
    def s_scale_faces_allow(p, prop_name, value, event=None,):
        mute_color(p, "Face Scale", mute=not value,)
        node_link(p, f"RR_VEC s_scale_faces Receptor", f"RR_VEC s_scale_faces {bool(value)}",)
    
    @tag_register()
    def s_scale_faces_value(p, prop_name, value, event=None,):
        node_value(p, "s_scale_faces", value=value, entry="node_socket", socket_idx=2)

    #Edges Distribution Exlusive 

    @tag_register()
    def s_scale_edges_allow(p, prop_name, value, event=None,):
        mute_color(p, "Edge Scale", mute=not value,)
        node_link(p, f"RR_VEC s_scale_edges Receptor", f"RR_VEC s_scale_edges {bool(value)}",)
    
    @tag_register()
    def s_scale_edges_vec_factor(p, prop_name, value, event=None,):
        node_value(p, "s_scale_edges", value=value, entry="node_socket", socket_idx=2)
        
    #ProjBezLine Exclusive
    
    @tag_register()
    def s_scale_projbezline_radius_allow(p, prop_name, value, event=None,):
        mute_color(p, "Bez Radius", mute=not value,)
        node_link(p, f"RR_VEC s_scale_projbezline_radius Receptor", f"RR_VEC s_scale_projbezline_radius {bool(value)}",)
    
    @tag_register()
    def s_scale_projbezline_radius_value(p, prop_name, value, event=None,):
        node_value(p, "s_scale_projbezline_radius", value=value, entry="node_socket", socket_idx=2)
      
    #ProjEmpties Exclusive
    
    @tag_register()
    def s_scale_projempties_allow(p, prop_name, value, event=None,):
        mute_color(p, "Empt Sca", mute=not value,)
        node_link(p, f"RR_VEC s_scale_projempties Receptor", f"RR_VEC s_scale_projempties {bool(value)}",)
    
    @tag_register()
    def s_scale_projempties_value(p, prop_name, value, event=None,):
        node_value(p, "s_scale_projempties", value=value, entry="node_socket", socket_idx=2)

    # 88""Yb  dP"Yb  888888    db    888888 88  dP"Yb  88b 88
    # 88__dP dP   Yb   88     dPYb     88   88 dP   Yb 88Yb88
    # 88"Yb  Yb   dP   88    dP__Yb    88   88 Yb   dP 88 Y88
    # 88  Yb  YbodP    88   dP""""Yb   88   88  YbodP  88  Y8
        
    @tag_register()
    def s_rot_master_allow(p, prop_name, value, event=None,):
        for prop in p.get_s_rot_main_features(availability_conditions=False,):
            mute_node(p, prop.replace("_allow",""), mute=not value,)
        #specific align Z nodetree set up is a little special
        mute_node(p, "s_rot_align_z_clump", mute=not value,)

    #Align Z

    @tag_register()
    def s_rot_align_z_allow(p, prop_name, value, event=None,):
        mute_color(p, "Align Normal", mute=not value,)
        node_link(p, f"RR_VEC s_rot_align_z Receptor", f"RR_VEC s_rot_align_z {bool(value)}",)
    
    @tag_register()
    def s_rot_align_z_method(p, prop_name, value, event=None,):
        node_value(p, "s_rot_align_z", value=get_enum_idx(p, prop_name, value,), entry="node_socket", socket_idx=5)
        if ('camera' in value):
            update_camera_nodegroup(force_update=True, reset_hash=True,)
    @tag_register()
    def s_rot_align_z_method_projbezareanosurf_special(p, prop_name, value, event=None,):
        if (p.s_distribution_method=="projbezarea" and not p.is_using_surf):
            node_value(p, "s_rot_align_z", value=get_enum_idx(p, prop_name, value,), entry="node_socket", socket_idx=5)
            if ('camera' in value):
                update_camera_nodegroup(force_update=True, reset_hash=True,)
    @tag_register()
    def s_rot_align_z_method_projbezlinenosurf_special(p, prop_name, value, event=None,):
        if (p.s_distribution_method=="projbezline" and not p.is_using_surf):
            node_value(p, "s_rot_align_z", value=get_enum_idx(p, prop_name, value,), entry="node_socket", socket_idx=5)
            if ('camera' in value):
                update_camera_nodegroup(force_update=True, reset_hash=True,)
    @tag_register()
    def s_rot_align_z_method_projemptiesnosurf_special(p, prop_name, value, event=None,):
        if (p.s_distribution_method=="projempties" and not p.is_using_surf):
            node_value(p, "s_rot_align_z", value=get_enum_idx(p, prop_name, value,), entry="node_socket", socket_idx=5)
            if ('camera' in value):
                update_camera_nodegroup(force_update=True, reset_hash=True,)
    
    @tag_register()
    def s_rot_align_z_revert(p, prop_name, value, event=None,):
        node_value(p, "s_rot_align_z", value=value, entry="node_socket", socket_idx=6)
    
    @tag_register()
    def s_rot_align_z_influence_allow(p, prop_name, value, event=None,):
        node_value(p, "s_rot_align_z", value=value, entry="node_socket", socket_idx=7)
    
    @tag_register()
    def s_rot_align_z_influence_value(p, prop_name, value, event=None,):
        node_value(p, "s_rot_align_z", value=value, entry="node_socket", socket_idx=8)

    @tag_register()
    def s_rot_align_z_smoothing_allow(p, prop_name, value, event=None,):
        node_value(p, f"s_rot_align_z", value=value, entry="node_socket", socket_idx=9)

    @tag_register()
    def s_rot_align_z_smoothing_value(p, prop_name, value, event=None,):
        node_value(p, f"s_rot_align_z", value=value, entry="node_socket", socket_idx=10)
        
    @tag_register()
    def s_rot_align_z_object(p, prop_name, value, event=None,):
        node_value(p, "s_rot_align_z", value=value, entry="node_socket", socket_idx=11)
    
    @tag_register()
    def s_rot_align_z_random_seed(p, prop_name, value, event=None,):
        node_value(p, "s_rot_align_z", value=value, entry="node_socket", socket_idx=12)
    
    @tag_register()
    def s_rot_align_z_is_random_seed(p, prop_name, value, event=None,):
        random_seed(p, event, api_is_random=prop_name, api_seed="s_rot_align_z_random_seed")
    
    @tag_register()
    def s_rot_align_z_clump_allow(p, prop_name, value, event=None,): 
        mute_color(p, "Clump Influence", mute=not value,)
        node_link(p, f"RR_VEC s_rot_align_z_clump Receptor", f"RR_VEC s_rot_align_z_clump {bool(value)}",)
    
    @tag_register()
    def s_rot_align_z_clump_value(p, prop_name, value, event=None,):
        node_value(p, "s_rot_align_z_clump", value=value, entry="node_socket", socket_idx=2)

    #Align Y

    @tag_register()
    def s_rot_align_y_allow(p, prop_name, value, event=None,):
        mute_color(p, "Align Tangent", mute=not value,)
        node_link(p, f"RR_VEC s_rot_align_y Receptor", f"RR_VEC s_rot_align_y {bool(value)}",)
    
    @tag_register()
    def s_rot_align_y_method(p, prop_name, value, event=None,):
        node_value(p, "s_rot_align_y", value=get_enum_idx(p, prop_name, value,), entry="node_socket", socket_idx=5)
        if ('camera' in value):
            update_camera_nodegroup(force_update=True, reset_hash=True,)
    @tag_register()
    def s_rot_align_y_method_projbezareanosurf_special(p, prop_name, value, event=None,):
        if (p.s_distribution_method=="projbezarea" and not p.is_using_surf):
            node_value(p, "s_rot_align_y", value=get_enum_idx(p, prop_name, value,), entry="node_socket", socket_idx=5)
            if ('camera' in value):
                update_camera_nodegroup(force_update=True, reset_hash=True,)
    @tag_register()
    def s_rot_align_y_method_projbezlinenosurf_special(p, prop_name, value, event=None,):
        if (p.s_distribution_method=="projbezline" and not p.is_using_surf):
            node_value(p, "s_rot_align_y", value=get_enum_idx(p, prop_name, value,), entry="node_socket", socket_idx=5)
            if ('camera' in value):
                update_camera_nodegroup(force_update=True, reset_hash=True,)
    @tag_register()
    def s_rot_align_y_method_projemptiesnosurf_special(p, prop_name, value, event=None,):
        if (p.s_distribution_method=="projempties" and not p.is_using_surf):
            node_value(p, "s_rot_align_y", value=get_enum_idx(p, prop_name, value,), entry="node_socket", socket_idx=5)
            if ('camera' in value):
                update_camera_nodegroup(force_update=True, reset_hash=True,)
            
    @tag_register()
    def s_rot_align_y_revert(p, prop_name, value, event=None,):
        node_value(p, "s_rot_align_y", value=value, entry="node_socket", socket_idx=6)
    
    @tag_register()
    def s_rot_align_y_object(p, prop_name, value, event=None,):
        node_value(p, "s_rot_align_y", value=value, entry="node_socket", socket_idx=7)
    
    @tag_register()
    def s_rot_align_y_random_seed(p, prop_name, value, event=None,):
        node_value(p, "s_rot_align_y", value=value, entry="node_socket", socket_idx=8)
    
    @tag_register()
    def s_rot_align_y_is_random_seed(p, prop_name, value, event=None,):
        random_seed(p, event, api_is_random=prop_name, api_seed="s_rot_align_y_random_seed")
    
    @tag_register()
    def s_rot_align_y_downslope_space(p, prop_name, value, event=None,):
        node_value(p, "s_rot_align_y", value=value=="local", entry="node_socket", socket_idx=9)

    @tag_register()
    def s_rot_align_y_downslope_smoothing_allow(p, prop_name, value, event=None,):
        node_value(p, "s_rot_align_y", value=value, entry="node_socket", socket_idx=10)

    @tag_register()
    def s_rot_align_y_downslope_smoothing_value(p, prop_name, value, event=None,):
        node_value(p, "s_rot_align_y", value=value, entry="node_socket", socket_idx=11)

    @tag_register()
    def s_rot_align_y_flow_method(p, prop_name, value, event=None,): 
        node_value(p, "s_rot_align_y.flowmap_method", value=get_enum_idx(p, prop_name, value,), entry="integer_input",)
    
    @tag_register()
    def s_rot_align_y_flow_direction(p, prop_name, value, event=None,): 
        node_value(p, "s_rot_align_y.flow_direction", value=value, entry="float_input")
    
    @tag_register()
    def s_rot_align_y_texture_ptr(p, prop_name, value, event=None,): 
        set_texture_ptr(p, "s_rot_align_y.texture", value)
    
    @tag_register()
    def s_rot_align_y_vcol_ptr(p, prop_name, value, event=None,):
        node_value(p, "s_rot_align_y.vcol_ptr", value=value, entry="named_attr",)

    #Tilt 

    @tag_register()
    def s_rot_tilt_allow(p, prop_name, value, event=None,):
        mute_color(p, "Tilt", mute=not value,)
        node_link(p, f"RR_VEC s_rot_tilt Receptor", f"RR_VEC s_rot_tilt {bool(value)}",)
    
    @tag_register()
    def s_rot_tilt_dir_method(p, prop_name, value, event=None,):
        node_value(p, "s_rot_tilt", value=get_enum_idx(p, prop_name, value,), entry="node_socket", socket_idx=1)
    
    @tag_register()
    def s_rot_tilt_method(p, prop_name, value, event=None,):
        node_value(p, "s_rot_tilt", value=get_enum_idx(p, prop_name, value,), entry="node_socket", socket_idx=2)
    
    @tag_register()
    def s_rot_tilt_noise_space(p, prop_name, value, event=None,):
        node_value(p, "s_rot_tilt", value=get_enum_idx(p, prop_name, value,), entry="node_socket", socket_idx=7)
        
    @tag_register()
    def s_rot_tilt_noise_scale(p, prop_name, value, event=None,):
        node_value(p, "s_rot_tilt", value=value, entry="node_socket", socket_idx=8)
    
    @tag_register()
    def s_rot_tilt_texture_ptr(p, prop_name, value, event=None,):
        set_texture_ptr(p, "s_rot_tilt.texture", value)
    
    @tag_register()
    def s_rot_tilt_vcol_ptr(p, prop_name, value, event=None,):
        node_value(p, "s_rot_tilt", value=value, entry="node_socket", socket_idx=3)
    
    @tag_register()
    def s_rot_tilt_direction(p, prop_name, value, event=None,):
        node_value(p, "s_rot_tilt", value=value, entry="node_socket", socket_idx=4)
    
    @tag_register()
    def s_rot_tilt_force(p, prop_name, value, event=None,):
        node_value(p, "s_rot_tilt", value=value, entry="node_socket", socket_idx=5)
    
    @tag_register()
    def s_rot_tilt_blue_influence(p, prop_name, value, event=None,):
        node_value(p, "s_rot_tilt", value=1-value, entry="node_socket", socket_idx=6)

    codegen_umask_updatefct(scope_ref=locals(), name="s_rot_tilt",)

    #Rot Random
    
    @tag_register()
    def s_rot_random_allow(p, prop_name, value, event=None,):
        mute_color(p, "Random Rotation", mute=not value,)
        node_link(p, f"RR_VEC s_rot_random Receptor", f"RR_VEC s_rot_random {bool(value)}",)
    
    @tag_register()
    def s_rot_random_tilt_value(p, prop_name, value, event=None,):
        node_value(p, "s_rot_random", value=value, entry="node_socket", socket_idx=1)
    
    @tag_register()
    def s_rot_random_yaw_value(p, prop_name, value, event=None,):
        node_value(p, "s_rot_random", value=value, entry="node_socket", socket_idx=2)
    
    @tag_register()
    def s_rot_random_seed(p, prop_name, value, event=None,):
        node_value(p, "s_rot_random", value=value, entry="node_socket", socket_idx=3)
    
    @tag_register()
    def s_rot_random_is_random_seed(p, prop_name, value, event=None,):
        random_seed(p, event, api_is_random=prop_name, api_seed="s_rot_random_seed")

    codegen_umask_updatefct(scope_ref=locals(), name="s_rot_random",)

    #Rot Add

    @tag_register()
    def s_rot_add_allow(p, prop_name, value, event=None,):
        mute_color(p, "Rotate", mute=not value,)
        node_link(p, f"RR_VEC s_rot_add Receptor", f"RR_VEC s_rot_add {bool(value)}",)
    
    @tag_register()
    def s_rot_add_default(p, prop_name, value, event=None,):
        node_value(p, "s_rot_add", value=vector_type(value), entry="node_socket", socket_idx=1)
    
    @tag_register()
    def s_rot_add_random(p, prop_name, value, event=None,):
        node_value(p, "s_rot_add", value=vector_type(value), entry="node_socket", socket_idx=2)
    
    @tag_register()
    def s_rot_add_seed(p, prop_name, value, event=None,):
        node_value(p, "s_rot_add", value=value, entry="node_socket", socket_idx=3)
    
    @tag_register()
    def s_rot_add_is_random_seed(p, prop_name, value, event=None,):
        random_seed(p, event, api_is_random=prop_name, api_seed="s_rot_add_seed")
    
    @tag_register()
    def s_rot_add_snap(p, prop_name, value, event=None,):
        node_value(p, "s_rot_add", value=value, entry="node_socket", socket_idx=4)

    codegen_umask_updatefct(scope_ref=locals(), name="s_rot_add",)

    # 88""Yb    db    888888 888888 888888 88""Yb 88b 88 .dP"Y8
    # 88__dP   dPYb     88     88   88__   88__dP 88Yb88 `Ybo."
    # 88"""   dP__Yb    88     88   88""   88"Yb  88 Y88 o.`Y8b
    # 88     dP""""Yb   88     88   888888 88  Yb 88  Y8 8bodP'

    @tag_register()
    def s_pattern_master_allow(p, prop_name, value, event=None,):
        for prop in p.get_s_pattern_main_features(availability_conditions=False,):
            mute_node(p, prop.replace("_allow",""), mute=not value,)

    #Pattern 1/2/3
    
    @tag_register(nbr=3)
    def s_patternX_allow(p, prop_name, value, event=None,):
        idx = int(prop_name[9])
        mute_color(p, f"Pattern{idx}", mute=not value,)
        node_link(p, f"RR_VEC s_pattern{idx} Receptor", f"RR_VEC s_pattern{idx} {bool(value)}",)
        node_link(p, f"RR_GEO s_pattern{idx} Receptor", f"RR_GEO s_pattern{idx} {bool(value)}",)
    
    @tag_register(nbr=3)
    def s_patternX_texture_ptr(p, prop_name, value, event=None,):
        idx = int(prop_name[9])
        set_texture_ptr(p, f"s_pattern{idx}.texture", value)
    
    @tag_register(nbr=3)
    def s_patternX_color_sample_method(p, prop_name, value, event=None,):
        idx = int(prop_name[9])
        node_value(p, f"s_pattern{idx}", value=get_enum_idx(p, prop_name, value,), entry="node_socket", socket_idx=2)
    
    @tag_register(nbr=3)
    def s_patternX_id_color_ptr(p, prop_name, value, event=None,):
        idx = int(prop_name[9])
        node_value(p, f"s_pattern{idx}", value=color_type(value), entry="node_socket", socket_idx=3)
    
    @tag_register(nbr=3)
    def s_patternX_id_color_tolerence(p, prop_name, value, event=None,):
        idx = int(prop_name[9])
        node_value(p, f"s_pattern{idx}", value=value, entry="node_socket", socket_idx=4)
    
    @tag_register(nbr=3)
    def s_patternX_dist_infl_allow(p, prop_name, value, event=None,):
        idx = int(prop_name[9])
        node_value(p, f"s_pattern{idx}", value=value, entry="node_socket", socket_idx=5)
    
    @tag_register(nbr=3)
    def s_patternX_dist_influence(p, prop_name, value, event=None,):
        idx = int(prop_name[9])
        node_value(p, f"s_pattern{idx}", value=value/100, entry="node_socket", socket_idx=6)
    
    @tag_register(nbr=3)
    def s_patternX_dist_revert(p, prop_name, value, event=None,):
        idx = int(prop_name[9])
        node_value(p, f"s_pattern{idx}", value=value, entry="node_socket", socket_idx=7)
    
    @tag_register(nbr=3)
    def s_patternX_scale_infl_allow(p, prop_name, value, event=None,):
        idx = int(prop_name[9])
        node_value(p, f"s_pattern{idx}", value=value, entry="node_socket", socket_idx=8)
    
    @tag_register(nbr=3)
    def s_patternX_scale_influence(p, prop_name, value, event=None,):
        idx = int(prop_name[9])
        node_value(p, f"s_pattern{idx}", value=value/100, entry="node_socket", socket_idx=9)
    
    @tag_register(nbr=3)
    def s_patternX_scale_revert(p, prop_name, value, event=None,):
        idx = int(prop_name[9])
        node_value(p, f"s_pattern{idx}", value=value, entry="node_socket", socket_idx=10)

    codegen_umask_updatefct(scope_ref=locals(), name="s_pattern1",)
    codegen_umask_updatefct(scope_ref=locals(), name="s_pattern2",)
    codegen_umask_updatefct(scope_ref=locals(), name="s_pattern3",)
    
    #    db    88""Yb 88  dP"Yb  888888 88  dP""b8
    #   dPYb   88__dP 88 dP   Yb   88   88 dP   `"
    #  dP__Yb  88""Yb 88 Yb   dP   88   88 Yb
    # dP""""Yb 88oodP 88  YbodP    88   88  YboodP

    @tag_register()
    def s_abiotic_master_allow(p, prop_name, value, event=None,):
        for prop in p.get_s_abiotic_main_features(availability_conditions=False,):
            mute_node(p, prop.replace("_allow",""), mute=not value,)

    #Elevation
    
    @tag_register()
    def s_abiotic_elev_allow(p, prop_name, value, event=None,):
        mute_color(p, f"Abiotic Elev", mute=not value,)
        node_link(p, f"RR_VEC s_abiotic_elev Receptor", f"RR_VEC s_abiotic_elev {bool(value)}",)
        node_link(p, f"RR_GEO s_abiotic_elev Receptor", f"RR_GEO s_abiotic_elev {bool(value)}",)
    
    @tag_register()
    def s_abiotic_elev_space(p, prop_name, value, event=None,):
        node_value(p, f"s_abiotic_elev", value=get_enum_idx(p, prop_name, value,), entry="node_socket", socket_idx=5)
    
    @tag_register()
    def s_abiotic_elev_method(p, prop_name, value, event=None,):
        node_value(p, f"s_abiotic_elev", value=(value=="percentage"), entry="node_socket", socket_idx=4)
        #need a refactor, but would break users presets)
        prop_mthd = "local" if (p.s_abiotic_elev_method=="percentage") else "global"
        #update values, both local/global properties min/max range share the same nodal inputs  
        setattr(p, f"s_abiotic_elev_min_value_{prop_mthd}", getattr(p, f"s_abiotic_elev_min_value_{prop_mthd}"),)
        setattr(p, f"s_abiotic_elev_min_falloff_{prop_mthd}", getattr(p, f"s_abiotic_elev_min_falloff_{prop_mthd}"),)
        setattr(p, f"s_abiotic_elev_max_value_{prop_mthd}", getattr(p, f"s_abiotic_elev_max_value_{prop_mthd}"),)
        setattr(p, f"s_abiotic_elev_max_falloff_{prop_mthd}", getattr(p, f"s_abiotic_elev_max_falloff_{prop_mthd}"),)
    
    @tag_register()
    def s_abiotic_elev_min_value_local(p, prop_name, value, event=None,):
        if (p.s_abiotic_elev_method=="percentage"):
            node_value(p, f"s_abiotic_elev", value=value/100, entry="node_socket", socket_idx=6)
    
    @tag_register()
    def s_abiotic_elev_min_falloff_local(p, prop_name, value, event=None,):
        if (p.s_abiotic_elev_method=="percentage"):
            node_value(p, f"s_abiotic_elev", value=value/100, entry="node_socket", socket_idx=7)
    
    @tag_register()
    def s_abiotic_elev_max_value_local(p, prop_name, value, event=None,):
        if (p.s_abiotic_elev_method=="percentage"):
            node_value(p, f"s_abiotic_elev", value=value/100, entry="node_socket", socket_idx=8)
    
    @tag_register()
    def s_abiotic_elev_max_falloff_local(p, prop_name, value, event=None,):
        if (p.s_abiotic_elev_method=="percentage"):
            node_value(p, f"s_abiotic_elev", value=value/100, entry="node_socket", socket_idx=9)
    
    @tag_register()
    def s_abiotic_elev_min_value_global(p, prop_name, value, event=None,):
        if (p.s_abiotic_elev_method=="altitude"):
            node_value(p, f"s_abiotic_elev", value=value, entry="node_socket", socket_idx=6)
    
    @tag_register()
    def s_abiotic_elev_min_falloff_global(p, prop_name, value, event=None,):
        if (p.s_abiotic_elev_method=="altitude"):
            node_value(p, f"s_abiotic_elev", value=value, entry="node_socket", socket_idx=7)
    
    @tag_register()
    def s_abiotic_elev_max_value_global(p, prop_name, value, event=None,):
        if (p.s_abiotic_elev_method=="altitude"):
            node_value(p, f"s_abiotic_elev", value=value, entry="node_socket", socket_idx=8)
    
    @tag_register()
    def s_abiotic_elev_max_falloff_global(p, prop_name, value, event=None,):
        if (p.s_abiotic_elev_method=="altitude"):
            node_value(p, f"s_abiotic_elev", value=value, entry="node_socket", socket_idx=9)

    @tag_register()
    def s_abiotic_elev_fallremap_allow(p, prop_name, value, event=None,):
        mute_node(p, "s_abiotic_elev.fallremap", mute=not value)
        mute_node(p, "s_abiotic_elev.fallremap_revert",mute=not p.s_abiotic_elev_fallremap_revert if value else True)
        mute_node(p, "s_abiotic_elev.fallnoisy", mute=not value)
    
    @tag_register()
    def s_abiotic_elev_fallremap_revert(p, prop_name, value, event=None,):
        mute_node(p, "s_abiotic_elev.fallremap_revert",mute=not value)
    
    @tag_register()
    def s_abiotic_elev_fallnoisy_strength(p, prop_name, value, event=None,):
        node_value(p, "s_abiotic_elev.fallnoisy", value=value, entry="node_socket", socket_idx=1)
    
    @tag_register()
    def s_abiotic_elev_fallnoisy_space(p, prop_name, value, event=None,):
        node_value(p, "s_abiotic_elev.fallnoisy", value=value=='local', entry="node_socket", socket_idx=5)

    @tag_register()
    def s_abiotic_elev_fallnoisy_scale(p, prop_name, value, event=None,):
        node_value(p, "s_abiotic_elev.fallnoisy", value=value, entry="node_socket", socket_idx=2)
    
    @tag_register()
    def s_abiotic_elev_fallnoisy_seed(p, prop_name, value, event=None,):
        node_value(p, "s_abiotic_elev.fallnoisy", value=value, entry="node_socket", socket_idx=3)
    
    @tag_register()
    def s_abiotic_elev_fallnoisy_is_random_seed(p, prop_name, value, event=None,):
        random_seed(p, event, api_is_random=prop_name, api_seed="s_abiotic_elev_fallnoisy_seed")

    @tag_register()
    def s_abiotic_elev_dist_infl_allow(p, prop_name, value, event=None,):
        node_value(p, f"s_abiotic_elev", value=value, entry="node_socket", socket_idx=10)
    
    @tag_register()
    def s_abiotic_elev_dist_influence(p, prop_name, value, event=None,):
        node_value(p, f"s_abiotic_elev", value=value/100, entry="node_socket", socket_idx=11)
    
    @tag_register()
    def s_abiotic_elev_dist_revert(p, prop_name, value, event=None,):
        node_value(p, f"s_abiotic_elev", value=value, entry="node_socket", socket_idx=12)
    
    @tag_register()
    def s_abiotic_elev_scale_infl_allow(p, prop_name, value, event=None,):
        node_value(p, f"s_abiotic_elev", value=value, entry="node_socket", socket_idx=13)
    
    @tag_register()
    def s_abiotic_elev_scale_influence(p, prop_name, value, event=None,):
        node_value(p, f"s_abiotic_elev", value=value/100, entry="node_socket", socket_idx=14)
    
    @tag_register()
    def s_abiotic_elev_scale_revert(p, prop_name, value, event=None,):
        node_value(p, f"s_abiotic_elev", value=value, entry="node_socket", socket_idx=15)

    codegen_umask_updatefct(scope_ref=locals(), name="s_abiotic_elev",)

    #Slope
    
    @tag_register()
    def s_abiotic_slope_allow(p, prop_name, value, event=None,):
        mute_color(p, f"Abiotic Slope", mute=not value,)
        node_link(p, f"RR_VEC s_abiotic_slope Receptor", f"RR_VEC s_abiotic_slope {bool(value)}",)
        node_link(p, f"RR_GEO s_abiotic_slope Receptor", f"RR_GEO s_abiotic_slope {bool(value)}",)
    
    @tag_register()
    def s_abiotic_slope_space(p, prop_name, value, event=None,):
        node_value(p, f"s_abiotic_slope", value=get_enum_idx(p, prop_name, value,), entry="node_socket", socket_idx=5)
    
    @tag_register()
    def s_abiotic_slope_absolute(p, prop_name, value, event=None,):
        node_value(p, f"s_abiotic_slope", value=value, entry="node_socket", socket_idx=10)
    
    @tag_register()
    def s_abiotic_slope_min_value(p, prop_name, value, event=None,):
        node_value(p, f"s_abiotic_slope", value=value, entry="node_socket", socket_idx=6)
    
    @tag_register()
    def s_abiotic_slope_min_falloff(p, prop_name, value, event=None,):
        node_value(p, f"s_abiotic_slope", value=value, entry="node_socket", socket_idx=7)
    
    @tag_register()
    def s_abiotic_slope_max_value(p, prop_name, value, event=None,):
        node_value(p, f"s_abiotic_slope", value=value, entry="node_socket", socket_idx=8)
    
    @tag_register()
    def s_abiotic_slope_max_falloff(p, prop_name, value, event=None,):
        node_value(p, f"s_abiotic_slope", value=value, entry="node_socket", socket_idx=9)

    @tag_register()
    def s_abiotic_slope_smoothing_allow(p, prop_name, value, event=None,):
        node_value(p, f"s_abiotic_slope", value=value, entry="node_socket", socket_idx=11)

    @tag_register()
    def s_abiotic_slope_smoothing_value(p, prop_name, value, event=None,):
        node_value(p, f"s_abiotic_slope", value=value, entry="node_socket", socket_idx=12)
        
    @tag_register()
    def s_abiotic_slope_fallremap_allow(p, prop_name, value, event=None,):
        mute_node(p, "s_abiotic_slope.fallremap", mute=not value)
        mute_node(p, "s_abiotic_slope.fallremap_revert",mute=not p.s_abiotic_slope_fallremap_revert if value else True)
        mute_node(p, "s_abiotic_slope.fallnoisy", mute=not value)

    @tag_register()
    def s_abiotic_slope_fallremap_revert(p, prop_name, value, event=None,):
        mute_node(p, "s_abiotic_slope.fallremap_revert",mute=not value)

    @tag_register()
    def s_abiotic_slope_fallnoisy_strength(p, prop_name, value, event=None,):
        node_value(p, "s_abiotic_slope.fallnoisy", value=value, entry="node_socket", socket_idx=1)
    
    @tag_register()
    def s_abiotic_slope_fallnoisy_scale(p, prop_name, value, event=None,):
        node_value(p, "s_abiotic_slope.fallnoisy", value=value, entry="node_socket", socket_idx=2)

    @tag_register()
    def s_abiotic_slope_fallnoisy_space(p, prop_name, value, event=None,):
        node_value(p, "s_abiotic_slope.fallnoisy", value=value=='local', entry="node_socket", socket_idx=5)
    
    @tag_register()
    def s_abiotic_slope_fallnoisy_seed(p, prop_name, value, event=None,):
        node_value(p, "s_abiotic_slope.fallnoisy", value=value, entry="node_socket", socket_idx=3)
    
    @tag_register()
    def s_abiotic_slope_fallnoisy_is_random_seed(p, prop_name, value, event=None,):
        random_seed(p, event, api_is_random=prop_name, api_seed="s_abiotic_slope_fallnoisy_seed")
    
    @tag_register()
    def s_abiotic_slope_dist_infl_allow(p, prop_name, value, event=None,):
        node_value(p, f"s_abiotic_slope", value=value, entry="node_socket", socket_idx=13)
    
    @tag_register()
    def s_abiotic_slope_dist_influence(p, prop_name, value, event=None,):
        node_value(p, f"s_abiotic_slope", value=value/100, entry="node_socket", socket_idx=14)
    
    @tag_register()
    def s_abiotic_slope_dist_revert(p, prop_name, value, event=None,):
        node_value(p, f"s_abiotic_slope", value=value, entry="node_socket", socket_idx=15)

    @tag_register()
    def s_abiotic_slope_scale_infl_allow(p, prop_name, value, event=None,):
        node_value(p, f"s_abiotic_slope", value=value, entry="node_socket", socket_idx=16)
    
    @tag_register()
    def s_abiotic_slope_scale_influence(p, prop_name, value, event=None,):
        node_value(p, f"s_abiotic_slope", value=value/100, entry="node_socket", socket_idx=17)
    
    @tag_register()
    def s_abiotic_slope_scale_revert(p, prop_name, value, event=None,):
        node_value(p, f"s_abiotic_slope", value=value, entry="node_socket", socket_idx=18)

    codegen_umask_updatefct(scope_ref=locals(), name="s_abiotic_slope",)

    #Direction
    
    @tag_register()
    def s_abiotic_dir_allow(p, prop_name, value, event=None,):
        mute_color(p, f"Abiotic Dir", mute=not value,)
        node_link(p, f"RR_VEC s_abiotic_dir Receptor", f"RR_VEC s_abiotic_dir {bool(value)}",)
        node_link(p, f"RR_GEO s_abiotic_dir Receptor", f"RR_GEO s_abiotic_dir {bool(value)}",)
    
    @tag_register()
    def s_abiotic_dir_space(p, prop_name, value, event=None,):
        node_value(p, f"s_abiotic_dir", value=get_enum_idx(p, prop_name, value,), entry="node_socket", socket_idx=5)
    
    @tag_register()
    def s_abiotic_dir_direction(p, prop_name, value, event=None,):
        node_value(p, f"s_abiotic_dir", value=value, entry="node_socket", socket_idx=6)
    
    @tag_register()
    def s_abiotic_dir_max(p, prop_name, value, event=None,):
        node_value(p, f"s_abiotic_dir", value=value, entry="node_socket", socket_idx=7)
    
    @tag_register()
    def s_abiotic_dir_treshold(p, prop_name, value, event=None,):
        node_value(p, f"s_abiotic_dir", value=value, entry="node_socket", socket_idx=8)
    
    @tag_register()
    def s_abiotic_dir_smoothing_allow(p, prop_name, value, event=None,):
        node_value(p, f"s_abiotic_dir", value=value, entry="node_socket", socket_idx=9)

    @tag_register()
    def s_abiotic_dir_smoothing_value(p, prop_name, value, event=None,):
        node_value(p, f"s_abiotic_dir", value=value, entry="node_socket", socket_idx=10)
        
    @tag_register()
    def s_abiotic_dir_fallremap_allow(p, prop_name, value, event=None,):
        mute_node(p, "s_abiotic_dir.fallremap", mute=not value)
        mute_node(p, "s_abiotic_dir.fallremap_revert",mute=not p.s_abiotic_dir_fallremap_revert if value else True)
        mute_node(p, "s_abiotic_dir.fallnoisy", mute=not value)

    @tag_register()
    def s_abiotic_dir_fallremap_revert(p, prop_name, value, event=None,):
        mute_node(p, "s_abiotic_dir.fallremap_revert",mute=not value)
    
    @tag_register()
    def s_abiotic_dir_fallnoisy_strength(p, prop_name, value, event=None,):
        node_value(p, "s_abiotic_dir.fallnoisy", value=value, entry="node_socket", socket_idx=1)
    
    @tag_register()
    def s_abiotic_dir_fallnoisy_scale(p, prop_name, value, event=None,):
        node_value(p, "s_abiotic_dir.fallnoisy", value=value, entry="node_socket", socket_idx=2)

    @tag_register()
    def s_abiotic_dir_fallnoisy_space(p, prop_name, value, event=None,):
        node_value(p, "s_abiotic_dir.fallnoisy", value=value=='local', entry="node_socket", socket_idx=5)
    
    @tag_register()
    def s_abiotic_dir_fallnoisy_seed(p, prop_name, value, event=None,):
        node_value(p, "s_abiotic_dir.fallnoisy", value=value, entry="node_socket", socket_idx=3)
    
    @tag_register()
    def s_abiotic_dir_fallnoisy_is_random_seed(p, prop_name, value, event=None,):
        random_seed(p, event, api_is_random=prop_name, api_seed="s_abiotic_dir_fallnoisy_seed")

    @tag_register()
    def s_abiotic_dir_dist_infl_allow(p, prop_name, value, event=None,):
        node_value(p, f"s_abiotic_dir", value=value, entry="node_socket", socket_idx=11)
    
    @tag_register()
    def s_abiotic_dir_dist_influence(p, prop_name, value, event=None,):
        node_value(p, f"s_abiotic_dir", value=value/100, entry="node_socket", socket_idx=12)
    
    @tag_register()
    def s_abiotic_dir_dist_revert(p, prop_name, value, event=None,):
        node_value(p, f"s_abiotic_dir", value=value, entry="node_socket", socket_idx=13)
    
    @tag_register()
    def s_abiotic_dir_scale_infl_allow(p, prop_name, value, event=None,):
        node_value(p, f"s_abiotic_dir", value=value, entry="node_socket", socket_idx=14)
    
    @tag_register()
    def s_abiotic_dir_scale_influence(p, prop_name, value, event=None,):
        node_value(p, f"s_abiotic_dir", value=value/100, entry="node_socket", socket_idx=15)
    
    @tag_register()
    def s_abiotic_dir_scale_revert(p, prop_name, value, event=None,):
        node_value(p, f"s_abiotic_dir", value=value, entry="node_socket", socket_idx=16)

    codegen_umask_updatefct(scope_ref=locals(), name="s_abiotic_dir",)

    #Curvature 

    @tag_register()
    def s_abiotic_cur_allow(p, prop_name, value, event=None,):
        mute_color(p, f"Abiotic Cur", mute=not value,)
        node_link(p, f"RR_VEC s_abiotic_cur Receptor", f"RR_VEC s_abiotic_cur {bool(value)}",)
        node_link(p, f"RR_GEO s_abiotic_cur Receptor", f"RR_GEO s_abiotic_cur {bool(value)}",)
    
    @tag_register()
    def s_abiotic_cur_type(p, prop_name, value, event=None,):
        node_value(p, f"s_abiotic_cur", value=get_enum_idx(p, prop_name, value,), entry="node_socket", socket_idx=4)
    
    @tag_register()
    def s_abiotic_cur_max(p, prop_name, value, event=None,):
        node_value(p, f"s_abiotic_cur", value=value/100, entry="node_socket", socket_idx=5)
        
    @tag_register()
    def s_abiotic_cur_treshold(p, prop_name, value, event=None,):
        node_value(p, f"s_abiotic_cur", value=value/100, entry="node_socket", socket_idx=6)

    @tag_register()
    def s_abiotic_cur_smoothing_allow(p, prop_name, value, event=None,):
        node_value(p, f"s_abiotic_cur", value=value, entry="node_socket", socket_idx=7)

    @tag_register()
    def s_abiotic_cur_smoothing_value(p, prop_name, value, event=None,):
        node_value(p, f"s_abiotic_cur", value=value, entry="node_socket", socket_idx=8)
    
    @tag_register()
    def s_abiotic_cur_fallremap_allow(p, prop_name, value, event=None,):
        mute_node(p, "s_abiotic_cur.fallremap", mute=not value)
        mute_node(p, "s_abiotic_cur.fallremap_revert",mute=not p.s_abiotic_cur_fallremap_revert if value else True)
        mute_node(p, "s_abiotic_cur.fallnoisy", mute=not value)
    
    @tag_register()
    def s_abiotic_cur_fallremap_revert(p, prop_name, value, event=None,):
        mute_node(p, "s_abiotic_cur.fallremap_revert",mute=not value)

    @tag_register()
    def s_abiotic_cur_fallnoisy_strength(p, prop_name, value, event=None,):
        node_value(p, "s_abiotic_cur.fallnoisy", value=value, entry="node_socket", socket_idx=1)
    
    @tag_register()
    def s_abiotic_cur_fallnoisy_space(p, prop_name, value, event=None,):
        node_value(p, "s_abiotic_cur.fallnoisy", value=value=='local', entry="node_socket", socket_idx=5)
    
    @tag_register()
    def s_abiotic_cur_fallnoisy_scale(p, prop_name, value, event=None,):
        node_value(p, "s_abiotic_cur.fallnoisy", value=value, entry="node_socket", socket_idx=2)
    
    @tag_register()
    def s_abiotic_cur_fallnoisy_seed(p, prop_name, value, event=None,):
        node_value(p, "s_abiotic_cur.fallnoisy", value=value, entry="node_socket", socket_idx=3)
    
    @tag_register()
    def s_abiotic_cur_fallnoisy_is_random_seed(p, prop_name, value, event=None,):
        random_seed(p, event, api_is_random=prop_name, api_seed="s_abiotic_cur_fallnoisy_seed")

    @tag_register()
    def s_abiotic_cur_dist_infl_allow(p, prop_name, value, event=None,):
        node_value(p, f"s_abiotic_cur", value=value, entry="node_socket", socket_idx=9)
    
    @tag_register()
    def s_abiotic_cur_dist_influence(p, prop_name, value, event=None,):
        node_value(p, f"s_abiotic_cur", value=value/100, entry="node_socket", socket_idx=10)
    
    @tag_register()
    def s_abiotic_cur_dist_revert(p, prop_name, value, event=None,):
        node_value(p, f"s_abiotic_cur", value=value, entry="node_socket", socket_idx=11)
    
    @tag_register()
    def s_abiotic_cur_scale_infl_allow(p, prop_name, value, event=None,):
        node_value(p, f"s_abiotic_cur", value=value, entry="node_socket", socket_idx=12)
    
    @tag_register()
    def s_abiotic_cur_scale_influence(p, prop_name, value, event=None,):
        node_value(p, f"s_abiotic_cur", value=value/100, entry="node_socket", socket_idx=13)
    
    @tag_register()
    def s_abiotic_cur_scale_revert(p, prop_name, value, event=None,):
        node_value(p, f"s_abiotic_cur", value=value, entry="node_socket", socket_idx=14)

    codegen_umask_updatefct(scope_ref=locals(), name="s_abiotic_cur",)

    #Border
    
    @tag_register()
    def s_abiotic_border_allow(p, prop_name, value, event=None,):
        mute_color(p, f"Abiotic Border", mute=not value,)
        node_link(p, f"RR_VEC s_abiotic_border Receptor", f"RR_VEC s_abiotic_border {bool(value)}",)
        node_link(p, f"RR_GEO s_abiotic_border Receptor", f"RR_GEO s_abiotic_border {bool(value)}",)
    
    @tag_register()
    def s_abiotic_border_space(p, prop_name, value, event=None,):
        node_value(p, f"s_abiotic_border", value=(value=="global"), entry="node_socket", socket_idx=4)
    
    @tag_register()
    def s_abiotic_border_max(p, prop_name, value, event=None,):
        node_value(p, f"s_abiotic_border", value=value, entry="node_socket", socket_idx=5)
    
    @tag_register()
    def s_abiotic_border_treshold(p, prop_name, value, event=None,):
        node_value(p, f"s_abiotic_border", value=value, entry="node_socket", socket_idx=6)

    @tag_register()
    def s_abiotic_border_fallremap_allow(p, prop_name, value, event=None,):
        mute_node(p, "s_abiotic_border.fallremap", mute=not value)
        mute_node(p, "s_abiotic_border.fallremap_revert",mute=not p.s_abiotic_border_fallremap_revert if value else True)
        mute_node(p, "s_abiotic_border.fallnoisy", mute=not value)

    @tag_register()
    def s_abiotic_border_fallremap_revert(p, prop_name, value, event=None,):
        mute_node(p, "s_abiotic_border.fallremap_revert",mute=not value)
    
    @tag_register()
    def s_abiotic_border_fallnoisy_strength(p, prop_name, value, event=None,):
        node_value(p, "s_abiotic_border.fallnoisy", value=value, entry="node_socket", socket_idx=1)
    
    @tag_register()
    def s_abiotic_border_fallnoisy_space(p, prop_name, value, event=None,):
        node_value(p, "s_abiotic_border.fallnoisy", value=value=='local', entry="node_socket", socket_idx=5)
    
    @tag_register()
    def s_abiotic_border_fallnoisy_scale(p, prop_name, value, event=None,):
        node_value(p, "s_abiotic_border.fallnoisy", value=value, entry="node_socket", socket_idx=2)
    
    @tag_register()
    def s_abiotic_border_fallnoisy_seed(p, prop_name, value, event=None,):
        node_value(p, "s_abiotic_border.fallnoisy", value=value, entry="node_socket", socket_idx=3)
    
    @tag_register()
    def s_abiotic_border_fallnoisy_is_random_seed(p, prop_name, value, event=None,):
        random_seed(p, event, api_is_random=prop_name, api_seed="s_abiotic_border_fallnoisy_seed")

    @tag_register()
    def s_abiotic_border_dist_infl_allow(p, prop_name, value, event=None,):
        node_value(p, f"s_abiotic_border", value=value, entry="node_socket", socket_idx=7)
    
    @tag_register()
    def s_abiotic_border_dist_influence(p, prop_name, value, event=None,):
        node_value(p, f"s_abiotic_border", value=value/100, entry="node_socket", socket_idx=8)
    
    @tag_register()
    def s_abiotic_border_dist_revert(p, prop_name, value, event=None,):
        node_value(p, f"s_abiotic_border", value=value, entry="node_socket", socket_idx=9)
    
    @tag_register()
    def s_abiotic_border_scale_infl_allow(p, prop_name, value, event=None,):
        node_value(p, f"s_abiotic_border", value=value, entry="node_socket", socket_idx=10)
    
    @tag_register()
    def s_abiotic_border_scale_influence(p, prop_name, value, event=None,):
        node_value(p, f"s_abiotic_border", value=value/100, entry="node_socket", socket_idx=11)
    
    @tag_register()
    def s_abiotic_border_scale_revert(p, prop_name, value, event=None,):
        node_value(p, f"s_abiotic_border", value=value, entry="node_socket", socket_idx=12)

    codegen_umask_updatefct(scope_ref=locals(), name="s_abiotic_border",)

    # 88""Yb 88""Yb  dP"Yb  Yb  dP 88 8b    d8 88 888888 Yb  dP
    # 88__dP 88__dP dP   Yb  YbdP  88 88b  d88 88   88    YbdP
    # 88"""  88"Yb  Yb   dP  dPYb  88 88YbdP88 88   88     8P
    # 88     88  Yb  YbodP  dP  Yb 88 88 YY 88 88   88    dP

    @tag_register()
    def s_proximity_master_allow(p, prop_name, value, event=None,):
        for prop in p.get_s_proximity_main_features(availability_conditions=False,):
            mute_node(p, prop.replace("_allow",""), mute=not value,)

    #Object-Repel 1&2

    @tag_register(nbr=2)
    def s_proximity_repelX_allow(p, prop_name, value, event=None,):
        idx = int(prop_name[17])
        mute_color(p, f"Repel{idx}", mute=not value,)
        node_link(p, f"RR_VEC1 s_proximity_repel{idx} Receptor", f"RR_VEC1 s_proximity_repel{idx} {bool(value)}",)
        node_link(p, f"RR_VEC2 s_proximity_repel{idx} Receptor", f"RR_VEC2 s_proximity_repel{idx} {bool(value)}",)
        node_link(p, f"RR_GEO s_proximity_repel{idx} Receptor", f"RR_GEO s_proximity_repel{idx} {bool(value)}",)
    
    @tag_register(nbr=2)
    def s_proximity_repelX_coll_ptr(p, prop_name, value, event=None,):
        idx = int(prop_name[17])
        node_value(p, f"s_proximity_repel{idx}.coll_ptr", value=bpy.data.collections.get(value), entry="node_socket", socket_idx=0)
    
    @tag_register(nbr=2)
    def s_proximity_repelX_type(p, prop_name, value, event=None,):
        idx = int(prop_name[17])
        node_value(p, f"s_proximity_repel{idx}.repel_type", value=get_enum_idx(p, prop_name, value,), entry="integer_input")
    
    @tag_register(nbr=2)
    def s_proximity_repelX_max(p, prop_name, value, event=None,):
        idx = int(prop_name[17])
        node_value(p, f"s_proximity_repel{idx}.max", value=value, entry="float_input")
    
    @tag_register(nbr=2)
    def s_proximity_repelX_treshold(p, prop_name, value, event=None,):
        idx = int(prop_name[17])
        node_value(p, f"s_proximity_repel{idx}.treshold", value=value, entry="float_input")
    
    @tag_register(nbr=2)
    def s_proximity_repelX_volume_allow(p, prop_name, value, event=None,):
        idx = int(prop_name[17])
        node_value(p, f"s_proximity_repel{idx}.volume_allow", value=value, entry="boolean_input")
    
    @tag_register(nbr=2)
    def s_proximity_repelX_volume_method(p, prop_name, value, event=None,):
        idx = int(prop_name[17])
        node_value(p, f"s_proximity_repel{idx}.out_method", value=value=="out", entry="boolean_input")
    
    @tag_register(nbr=2)
    def s_proximity_repelX_fallremap_allow(p, prop_name, value, event=None,):
        idx = int(prop_name[17])
        mute_node(p, f"s_proximity_repel{idx}.fallremap",mute=not value)
        mute_node(p, f"s_proximity_repel{idx}.fallremap_revert",mute=not getattr(p,f"s_proximity_repel{idx}_fallremap_revert") if value else True)
        mute_node(p, f"s_proximity_repel{idx}.fallnoisy",mute=not value)

    @tag_register(nbr=2)
    def s_proximity_repelX_fallremap_revert(p, prop_name, value, event=None,):
        idx = int(prop_name[17])
        mute_node(p, f"s_proximity_repel{idx}.fallremap_revert",mute=not value)

    @tag_register(nbr=2)
    def s_proximity_repelX_fallnoisy_strength(p, prop_name, value, event=None,):
        idx = int(prop_name[17])
        node_value(p, f"s_proximity_repel{idx}.fallnoisy", value=value, entry="node_socket", socket_idx=1)
    
    @tag_register(nbr=2)
    def s_proximity_repelX_fallnoisy_space(p, prop_name, value, event=None,):
        idx = int(prop_name[17])
        node_value(p, f"s_proximity_repel{idx}.fallnoisy", value=value=='local', entry="node_socket", socket_idx=5)
        
    @tag_register(nbr=2)
    def s_proximity_repelX_fallnoisy_scale(p, prop_name, value, event=None,):
        idx = int(prop_name[17])
        node_value(p, f"s_proximity_repel{idx}.fallnoisy", value=value, entry="node_socket", socket_idx=2)
    
    @tag_register(nbr=2)
    def s_proximity_repelX_fallnoisy_seed(p, prop_name, value, event=None,):
        idx = int(prop_name[17])
        node_value(p, f"s_proximity_repel{idx}.fallnoisy", value=value, entry="node_socket", socket_idx=3)
    
    @tag_register(nbr=2)
    def s_proximity_repelX_fallnoisy_is_random_seed(p, prop_name, value, event=None,):
        idx = int(prop_name[17])
        random_seed(p, event, api_is_random=prop_name, api_seed=f"s_proximity_repel{idx}_fallnoisy_seed")
    
    @tag_register(nbr=2)
    def s_proximity_repelX_simulation_allow(p, prop_name, value, event=None,):
        idx = int(prop_name[17])
        node_value(p, f"s_proximity_repel{idx}.simulation_allow", value=value, entry="boolean_input")

    @tag_register(nbr=2)
    def s_proximity_repelX_simulation_fadeaway_allow(p, prop_name, value, event=None,):
        idx = int(prop_name[17])
        node_value(p, f"s_proximity_repel{idx}.fadeaway_allow", value=value, entry="boolean_input")

    @tag_register(nbr=2)
    def s_proximity_repelX_simulation_fadeaway_method(p, prop_name, value, event=None,):
        idx = int(prop_name[17])
        node_value(p, f"s_proximity_repel{idx}.use_frame", value=value=="frame", entry="boolean_input")

    @tag_register(nbr=2)
    def s_proximity_repelX_simulation_fadeaway_frame(p, prop_name, value, event=None,):
        idx = int(prop_name[17])
        node_value(p, f"s_proximity_repel{idx}.frame", value=value, entry="integer_input")

    @tag_register(nbr=2)
    def s_proximity_repelX_simulation_fadeaway_sec(p, prop_name, value, event=None,):
        idx = int(prop_name[17])
        node_value(p, f"s_proximity_repel{idx}.sec", value=value, entry="float_input")

    @tag_register(nbr=2)
    def s_proximity_repelX_dist_infl_allow(p, prop_name, value, event=None,):
        idx = int(prop_name[17])
        node_value(p, f"s_proximity_repel{idx}.influences", value=value, entry="node_socket", socket_idx=0)
    
    @tag_register(nbr=2)
    def s_proximity_repelX_dist_influence(p, prop_name, value, event=None,):
        idx = int(prop_name[17])
        node_value(p, f"s_proximity_repel{idx}.influences", value=value/100, entry="node_socket", socket_idx=1)
    
    @tag_register(nbr=2)
    def s_proximity_repelX_dist_revert(p, prop_name, value, event=None,):
        idx = int(prop_name[17])
        #because we use the "is in volume" option, the influence on density is a bit more complicated to handle in the nodetree
        node_value(p, f"s_proximity_repel{idx}.influences", value=not value, entry="node_socket", socket_idx=2)
        node_value(p, f"s_proximity_repel{idx}.is_reverse_density", value=value, entry="boolean_input")

    @tag_register(nbr=2)
    def s_proximity_repelX_scale_infl_allow(p, prop_name, value, event=None,):
        idx = int(prop_name[17])
        node_value(p, f"s_proximity_repel{idx}.influences", value=value, entry="node_socket", socket_idx=3)
    
    @tag_register(nbr=2)
    def s_proximity_repelX_scale_influence(p, prop_name, value, event=None,):
        idx = int(prop_name[17])
        node_value(p, f"s_proximity_repel{idx}.influences", value=value/100, entry="node_socket", socket_idx=4)
    
    @tag_register(nbr=2)
    def s_proximity_repelX_scale_revert(p, prop_name, value, event=None,):
        idx = int(prop_name[17])
        node_value(p, f"s_proximity_repel{idx}.influences", value=not value, entry="node_socket", socket_idx=5)
    
    @tag_register(nbr=2)
    def s_proximity_repelX_nor_infl_allow(p, prop_name, value, event=None,):
        idx = int(prop_name[17])
        node_value(p, f"s_proximity_repel{idx}.influences", value=value, entry="node_socket", socket_idx=6)
    
    @tag_register(nbr=2)
    def s_proximity_repelX_nor_influence(p, prop_name, value, event=None,):
        idx = int(prop_name[17])
        node_value(p, f"s_proximity_repel{idx}.influences", value=value/100, entry="node_socket", socket_idx=7)
    
    @tag_register(nbr=2)
    def s_proximity_repelX_nor_revert(p, prop_name, value, event=None,):
        idx = int(prop_name[17])
        node_value(p, f"s_proximity_repel{idx}.influences", value=value, entry="node_socket", socket_idx=8)

    @tag_register(nbr=2)
    def s_proximity_repelX_tan_infl_allow(p, prop_name, value, event=None,):
        idx = int(prop_name[17])
        node_value(p, f"s_proximity_repel{idx}.influences", value=value, entry="node_socket", socket_idx=9)
    
    @tag_register(nbr=2)
    def s_proximity_repelX_tan_influence(p, prop_name, value, event=None,):
        idx = int(prop_name[17])
        node_value(p, f"s_proximity_repel{idx}.influences", value=value/100, entry="node_socket", socket_idx=10)
    
    @tag_register(nbr=2)
    def s_proximity_repelX_tan_revert(p, prop_name, value, event=None,):
        idx = int(prop_name[17])
        node_value(p, f"s_proximity_repel{idx}.influences", value=value, entry="node_socket", socket_idx=11)

    codegen_umask_updatefct(scope_ref=locals(), name="s_proximity_repel1",)
    codegen_umask_updatefct(scope_ref=locals(), name="s_proximity_repel2",)

    #ProjBezArea Border
    
    @tag_register()
    def s_proximity_projbezarea_border_allow(p, prop_name, value, event=None,):
        mute_color(p, f"Bez Border", mute=not value,)
        node_link(p, f"RR_VEC s_proximity_projbezarea_border Receptor", f"RR_VEC s_proximity_projbezarea_border {bool(value)}",)
        node_link(p, f"RR_GEO s_proximity_projbezarea_border Receptor", f"RR_GEO s_proximity_projbezarea_border {bool(value)}",)

    @tag_register()
    def s_proximity_projbezarea_border_max(p, prop_name, value, event=None,):
        node_value(p, f"s_proximity_projbezarea_border", value=value, entry="node_socket", socket_idx=3)
    
    @tag_register()
    def s_proximity_projbezarea_border_treshold(p, prop_name, value, event=None,):
        node_value(p, f"s_proximity_projbezarea_border", value=value, entry="node_socket", socket_idx=4)

    @tag_register()
    def s_proximity_projbezarea_border_fallremap_allow(p, prop_name, value, event=None,):
        mute_node(p, "s_proximity_projbezarea_border.fallremap", mute=not value)
        mute_node(p, "s_proximity_projbezarea_border.fallremap_revert",mute=not p.s_proximity_projbezarea_border_fallremap_revert if value else True)
        mute_node(p, "s_proximity_projbezarea_border.fallnoisy", mute=not value)

    @tag_register()
    def s_proximity_projbezarea_border_fallremap_revert(p, prop_name, value, event=None,):
        mute_node(p, "s_proximity_projbezarea_border.fallremap_revert",mute=not value)
    
    @tag_register()
    def s_proximity_projbezarea_border_fallnoisy_strength(p, prop_name, value, event=None,):
        node_value(p, "s_proximity_projbezarea_border.fallnoisy", value=value, entry="node_socket", socket_idx=1)
    
    @tag_register()
    def s_proximity_projbezarea_border_fallnoisy_space(p, prop_name, value, event=None,):
        node_value(p, "s_proximity_projbezarea_border.fallnoisy", value=value=='local', entry="node_socket", socket_idx=5)
    
    @tag_register()
    def s_proximity_projbezarea_border_fallnoisy_scale(p, prop_name, value, event=None,):
        node_value(p, "s_proximity_projbezarea_border.fallnoisy", value=value, entry="node_socket", socket_idx=2)
    
    @tag_register()
    def s_proximity_projbezarea_border_fallnoisy_seed(p, prop_name, value, event=None,):
        node_value(p, "s_proximity_projbezarea_border.fallnoisy", value=value, entry="node_socket", socket_idx=3)
    
    @tag_register()
    def s_proximity_projbezarea_border_fallnoisy_is_random_seed(p, prop_name, value, event=None,):
        random_seed(p, event, api_is_random=prop_name, api_seed="s_proximity_projbezarea_border_fallnoisy_seed")

    @tag_register()
    def s_proximity_projbezarea_border_dist_infl_allow(p, prop_name, value, event=None,):
        node_value(p, f"s_proximity_projbezarea_border", value=value, entry="node_socket", socket_idx=5)
    
    @tag_register()
    def s_proximity_projbezarea_border_dist_influence(p, prop_name, value, event=None,):
        node_value(p, f"s_proximity_projbezarea_border", value=value/100, entry="node_socket", socket_idx=6)
    
    @tag_register()
    def s_proximity_projbezarea_border_dist_revert(p, prop_name, value, event=None,):
        node_value(p, f"s_proximity_projbezarea_border", value=value, entry="node_socket", socket_idx=7)
    
    @tag_register()
    def s_proximity_projbezarea_border_scale_infl_allow(p, prop_name, value, event=None,):
        node_value(p, f"s_proximity_projbezarea_border", value=value, entry="node_socket", socket_idx=8)
    
    @tag_register()
    def s_proximity_projbezarea_border_scale_influence(p, prop_name, value, event=None,):
        node_value(p, f"s_proximity_projbezarea_border", value=value/100, entry="node_socket", socket_idx=9)
    
    @tag_register()
    def s_proximity_projbezarea_border_scale_revert(p, prop_name, value, event=None,):
        node_value(p, f"s_proximity_projbezarea_border", value=value, entry="node_socket", socket_idx=10)
        
    #Outskirt
    
    @tag_register()
    def s_proximity_outskirt_allow(p, prop_name, value, event=None,):
        mute_color(p, "Outskirt", mute=not value,)
        node_link(p, f"RR_VEC1 s_proximity_outskirt Receptor", f"RR_VEC1 s_proximity_outskirt {bool(value)}",)
        node_link(p, f"RR_VEC2 s_proximity_outskirt Receptor", f"RR_VEC2 s_proximity_outskirt {bool(value)}",)
        node_link(p, f"RR_GEO s_proximity_outskirt Receptor", f"RR_GEO s_proximity_outskirt {bool(value)}",)
    
    @tag_register()
    def s_proximity_outskirt_detection(p, prop_name, value, event=None,):
        node_value(p, "s_proximity_outskirt", value=value, entry="node_socket", socket_idx=5)
    
    @tag_register()
    def s_proximity_outskirt_precision(p, prop_name, value, event=None,):
        node_value(p, "s_proximity_outskirt", value=value, entry="node_socket", socket_idx=6)

    @tag_register()
    def s_proximity_outskirt_max(p, prop_name, value, event=None,):
        node_value(p, "s_proximity_outskirt", value=value, entry="node_socket", socket_idx=7)

    @tag_register()
    def s_proximity_outskirt_treshold(p, prop_name, value, event=None,):
        node_value(p, "s_proximity_outskirt", value=value, entry="node_socket", socket_idx=8)

    @tag_register()
    def s_proximity_outskirt_fallremap_allow(p, prop_name, value, event=None,):       
        mute_node(p, "s_proximity_outskirt.fallremap",mute=not value)
        mute_node(p, "s_proximity_outskirt.fallremap_revert",mute=not p.s_proximity_outskirt_fallremap_revert if value else True)
        mute_node(p, "s_proximity_outskirt.fallnoisy",mute=not value)

    @tag_register()
    def s_proximity_outskirt_fallremap_revert(p, prop_name, value, event=None,):
        mute_node(p, "s_proximity_outskirt.fallremap_revert",mute=not value)

    @tag_register()
    def s_proximity_outskirt_fallnoisy_strength(p, prop_name, value, event=None,):
        node_value(p, "s_proximity_outskirt.fallnoisy", value=value, entry="node_socket", socket_idx=1)
    
    @tag_register()
    def s_proximity_outskirt_fallnoisy_space(p, prop_name, value, event=None,):
        node_value(p, "s_proximity_outskirt.fallnoisy", value=value=='local', entry="node_socket", socket_idx=5)
    
    @tag_register()
    def s_proximity_outskirt_fallnoisy_scale(p, prop_name, value, event=None,):
        node_value(p, "s_proximity_outskirt.fallnoisy", value=value, entry="node_socket", socket_idx=2)
    
    @tag_register()
    def s_proximity_outskirt_fallnoisy_seed(p, prop_name, value, event=None,):
        node_value(p, "s_proximity_outskirt.fallnoisy", value=value, entry="node_socket", socket_idx=3)
    
    @tag_register()
    def s_proximity_outskirt_fallnoisy_is_random_seed(p, prop_name, value, event=None,):
        random_seed(p, event, api_is_random=prop_name, api_seed="s_proximity_outskirt_fallnoisy_seed")
    
    @tag_register()
    def s_proximity_outskirt_dist_infl_allow(p, prop_name, value, event=None,):
        node_value(p, "s_proximity_outskirt.influences", value=value, entry="node_socket", socket_idx=0)
    
    @tag_register()
    def s_proximity_outskirt_dist_influence(p, prop_name, value, event=None,):
        node_value(p, "s_proximity_outskirt.influences", value=value/100, entry="node_socket", socket_idx=1)
    
    @tag_register()
    def s_proximity_outskirt_dist_revert(p, prop_name, value, event=None,):
        node_value(p, "s_proximity_outskirt.influences", value=value, entry="node_socket", socket_idx=2)

    @tag_register()
    def s_proximity_outskirt_scale_infl_allow(p, prop_name, value, event=None,):
        node_value(p, "s_proximity_outskirt.influences", value=value, entry="node_socket", socket_idx=3)
    
    @tag_register()
    def s_proximity_outskirt_scale_influence(p, prop_name, value, event=None,):
        node_value(p, "s_proximity_outskirt.influences", value=value/100, entry="node_socket", socket_idx=4)
    
    @tag_register()
    def s_proximity_outskirt_scale_revert(p, prop_name, value, event=None,):
        node_value(p, "s_proximity_outskirt.influences", value=value, entry="node_socket", socket_idx=5)
    
    # @tag_register()
    # def s_proximity_outskirt_nor_infl_allow(p, prop_name, value, event=None,):
    #     node_value(p, f"s_proximity_outskirt.influences", value=value, entry="node_socket", socket_idx=6)
    
    # @tag_register()
    # def s_proximity_outskirt_nor_influence(p, prop_name, value, event=None,):
    #     node_value(p, f"s_proximity_outskirt.influences", value=value/100, entry="node_socket", socket_idx=7)
    
    # @tag_register()
    # def s_proximity_outskirt_nor_revert(p, prop_name, value, event=None,):
    #     node_value(p, f"s_proximity_outskirt.influences", value=not value, entry="node_socket", socket_idx=8)

    # @tag_register()
    # def s_proximity_outskirt_tan_infl_allow(p, prop_name, value, event=None,):
    #     node_value(p, f"s_proximity_outskirt.influences", value=value, entry="node_socket", socket_idx=9)
    
    # @tag_register()
    # def s_proximity_outskirt_tan_influence(p, prop_name, value, event=None,):
    #     node_value(p, f"s_proximity_outskirt.influences", value=value/100, entry="node_socket", socket_idx=10)
    
    # @tag_register()
    # def s_proximity_outskirt_tan_revert(p, prop_name, value, event=None,):
    #     node_value(p, f"s_proximity_outskirt.influences", value=not value, entry="node_socket", socket_idx=11)

    codegen_umask_updatefct(scope_ref=locals(), name="s_proximity_outskirt",)

    # 888888  dP""b8  dP"Yb  .dP"Y8 Yb  dP .dP"Y8 888888 888888 8b    d8
    # 88__   dP   `" dP   Yb `Ybo."  YbdP  `Ybo."   88   88__   88b  d88
    # 88""   Yb      Yb   dP o.`Y8b   8P   o.`Y8b   88   88""   88YbdP88
    # 888888  YboodP  YbodP  8bodP'  dP    8bodP'   88   888888 88 YY 88

    @tag_register()
    def s_ecosystem_master_allow(p, prop_name, value, event=None,):
        for prop in p.get_s_ecosystem_main_features(availability_conditions=False,):
            mute_node(p, prop.replace("_allow",""), mute=not value,)

    #Affinity

    @tag_register()
    def s_ecosystem_affinity_allow(p, prop_name, value, event=None,):
        mute_color(p, f"Eco Affinity", mute=not value,)
        node_link(p, f"RR_VEC s_ecosystem_affinity Receptor", f"RR_VEC s_ecosystem_affinity {bool(value)}",)
        node_link(p, f"RR_GEO s_ecosystem_affinity Receptor", f"RR_GEO s_ecosystem_affinity {bool(value)}",)
    
    @tag_register()
    def s_ecosystem_affinity_space(p, prop_name, value, event=None,):
        node_value(p, "s_ecosystem_affinity.use_global", value=(value=="global"), entry="boolean_input")
    
    @tag_register(nbr=3)
    def s_ecosystem_affinity_XX_ptr(p, prop_name, value, event=None,):
        idx = int(prop_name[22])
        targetp = bpy.context.scene.scatter5.get_psy_by_name(value)
        so = targetp.scatter_obj if (targetp) else None
        node_value(p, f"s_ecosystem_affinity.slot{idx}", value=so, entry="node_socket", socket_idx=2)
        mute_node(p, f"s_ecosystem_affinity.slot{idx}", mute=(so is None),)
        #adjust slot interface
        if (value==""):
            if (idx==3):
                if (p.s_ecosystem_affinity_02_ptr==""):
                      p.s_ecosystem_affinity_ui_max_slot = 1
                else: p.s_ecosystem_affinity_ui_max_slot = 2
            elif (idx==2):
                if (p.s_ecosystem_affinity_03_ptr==""):
                    p.s_ecosystem_affinity_ui_max_slot = 1

    @tag_register(nbr=3)
    def s_ecosystem_affinity_XX_type(p, prop_name, value, event=None,):
        idx = int(prop_name[22])
        node_value(p, f"s_ecosystem_affinity.slot{idx}", value=get_enum_idx(p, prop_name, value,), entry="node_socket", socket_idx=3)
    
    @tag_register(nbr=3)
    def s_ecosystem_affinity_XX_max_value(p, prop_name, value, event=None,):
        idx = int(prop_name[22])
        node_value(p, f"s_ecosystem_affinity.slot{idx}", value=value, entry="node_socket", socket_idx=4)
    
    @tag_register(nbr=3)
    def s_ecosystem_affinity_XX_max_falloff(p, prop_name, value, event=None,):
        idx = int(prop_name[22])
        node_value(p, f"s_ecosystem_affinity.slot{idx}", value=value, entry="node_socket", socket_idx=5)
    
    @tag_register(nbr=3)
    def s_ecosystem_affinity_XX_limit_distance(p, prop_name, value, event=None,):
        idx = int(prop_name[22])
        node_value(p, f"s_ecosystem_affinity.slot{idx}", value=value, entry="node_socket", socket_idx=6)
    
    @tag_register()
    def s_ecosystem_affinity_fallremap_allow(p, prop_name, value, event=None,):
        mute_node(p, "s_ecosystem_affinity.fallremap",mute=not value)
        mute_node(p, "s_ecosystem_affinity.fallremap_revert",mute=not p.s_ecosystem_affinity_fallremap_revert if value else True)
        mute_node(p, "s_ecosystem_affinity.fallnoisy",mute=not value)

    @tag_register()
    def s_ecosystem_affinity_fallremap_revert(p, prop_name, value, event=None,):
        mute_node(p, "s_ecosystem_affinity.fallremap_revert",mute=not value)
    
    @tag_register()
    def s_ecosystem_affinity_fallnoisy_strength(p, prop_name, value, event=None,):
        node_value(p, "s_ecosystem_affinity.fallnoisy", value=value, entry="node_socket", socket_idx=1)
    
    @tag_register()
    def s_ecosystem_affinity_fallnoisy_space(p, prop_name, value, event=None,):
        node_value(p, "s_ecosystem_affinity.fallnoisy", value=value=='local', entry="node_socket", socket_idx=5)
    
    @tag_register()
    def s_ecosystem_affinity_fallnoisy_scale(p, prop_name, value, event=None,):
        node_value(p, "s_ecosystem_affinity.fallnoisy", value=value, entry="node_socket", socket_idx=2)
    
    @tag_register()
    def s_ecosystem_affinity_fallnoisy_seed(p, prop_name, value, event=None,):
        node_value(p, "s_ecosystem_affinity.fallnoisy", value=value, entry="node_socket", socket_idx=3)
    
    @tag_register()
    def s_ecosystem_affinity_fallnoisy_is_random_seed(p, prop_name, value, event=None,):
        random_seed(p, event, api_is_random=prop_name, api_seed="s_ecosystem_affinity_fallnoisy_seed")
    
    @tag_register()
    def s_ecosystem_affinity_dist_infl_allow(p, prop_name, value, event=None,):
        node_value(p, "s_ecosystem_affinity.influences", value=value, entry="node_socket", socket_idx=0)
    
    @tag_register()
    def s_ecosystem_affinity_dist_influence(p, prop_name, value, event=None,):
        node_value(p, "s_ecosystem_affinity.influences", value=value/100, entry="node_socket", socket_idx=1)

    @tag_register()
    def s_ecosystem_affinity_scale_infl_allow(p, prop_name, value, event=None,):
        node_value(p, "s_ecosystem_affinity.influences", value=value, entry="node_socket", socket_idx=3)
    
    @tag_register()
    def s_ecosystem_affinity_scale_influence(p, prop_name, value, event=None,):
        node_value(p, "s_ecosystem_affinity.influences", value=value/100, entry="node_socket", socket_idx=4)

    codegen_umask_updatefct(scope_ref=locals(), name="s_ecosystem_affinity",)

    #Repulsion

    @tag_register()
    def s_ecosystem_repulsion_allow(p, prop_name, value, event=None,):
        mute_color(p, f"Eco Repulsion", mute=not value,)
        node_link(p, f"RR_VEC s_ecosystem_repulsion Receptor", f"RR_VEC s_ecosystem_repulsion {bool(value)}",)
        node_link(p, f"RR_GEO s_ecosystem_repulsion Receptor", f"RR_GEO s_ecosystem_repulsion {bool(value)}",)
    
    @tag_register()
    def s_ecosystem_repulsion_space(p, prop_name, value, event=None,):
        node_value(p, "s_ecosystem_repulsion.use_global", value=(value=="global"), entry="boolean_input")
    
    @tag_register(nbr=3)
    def s_ecosystem_repulsion_XX_ptr(p, prop_name, value, event=None,):
        idx = int(prop_name[23])
        targetp = bpy.context.scene.scatter5.get_psy_by_name(value)
        so = targetp.scatter_obj if (targetp) else None
        node_value(p, f"s_ecosystem_repulsion.slot{idx}", value=so, entry="node_socket", socket_idx=2)
        mute_node(p, f"s_ecosystem_repulsion.slot{idx}", mute=(so is None),)
        #adjust slot interface
        if (value==""):
            if (idx==3):
                if (p.s_ecosystem_repulsion_02_ptr==""):
                      p.s_ecosystem_repulsion_ui_max_slot = 1
                else: p.s_ecosystem_repulsion_ui_max_slot = 2
            elif (idx==2):
                if (p.s_ecosystem_repulsion_03_ptr==""):
                    p.s_ecosystem_repulsion_ui_max_slot = 1
    
    @tag_register(nbr=3)
    def s_ecosystem_repulsion_XX_type(p, prop_name, value, event=None,):
        idx = int(prop_name[23])
        node_value(p, f"s_ecosystem_repulsion.slot{idx}", value=get_enum_idx(p, prop_name, value,), entry="node_socket", socket_idx=3)
    
    @tag_register(nbr=3)
    def s_ecosystem_repulsion_XX_max_value(p, prop_name, value, event=None,):
        idx = int(prop_name[23])
        node_value(p, f"s_ecosystem_repulsion.slot{idx}", value=value, entry="node_socket", socket_idx=4)
    
    @tag_register(nbr=3)
    def s_ecosystem_repulsion_XX_max_falloff(p, prop_name, value, event=None,):
        idx = int(prop_name[23])
        node_value(p, f"s_ecosystem_repulsion.slot{idx}", value=value, entry="node_socket", socket_idx=5)
    
    @tag_register()
    def s_ecosystem_repulsion_fallremap_allow(p, prop_name, value, event=None,):
        mute_node(p, "s_ecosystem_repulsion.fallremap",mute=not value)
        mute_node(p, "s_ecosystem_repulsion.fallremap_revert",mute=not p.s_ecosystem_repulsion_fallremap_revert if value else True)
        mute_node(p, "s_ecosystem_repulsion.fallnoisy",mute=not value)

    @tag_register()
    def s_ecosystem_repulsion_fallremap_revert(p, prop_name, value, event=None,):
        mute_node(p, "s_ecosystem_repulsion.fallremap_revert",mute=not value)
    
    @tag_register()
    def s_ecosystem_repulsion_fallnoisy_strength(p, prop_name, value, event=None,):
        node_value(p, "s_ecosystem_repulsion.fallnoisy", value=value, entry="node_socket", socket_idx=1)

    @tag_register()
    def s_ecosystem_repulsion_fallnoisy_space(p, prop_name, value, event=None,):
        node_value(p, "s_ecosystem_repulsion.fallnoisy", value=value=='local', entry="node_socket", socket_idx=5)
    
    @tag_register()
    def s_ecosystem_repulsion_fallnoisy_scale(p, prop_name, value, event=None,):
        node_value(p, "s_ecosystem_repulsion.fallnoisy", value=value, entry="node_socket", socket_idx=2)
    
    @tag_register()
    def s_ecosystem_repulsion_fallnoisy_seed(p, prop_name, value, event=None,):
        node_value(p, "s_ecosystem_repulsion.fallnoisy", value=value, entry="node_socket", socket_idx=3)
    
    @tag_register()
    def s_ecosystem_repulsion_fallnoisy_is_random_seed(p, prop_name, value, event=None,):
        random_seed(p, event, api_is_random=prop_name, api_seed="s_ecosystem_repulsion_fallnoisy_seed")

    @tag_register()
    def s_ecosystem_repulsion_dist_infl_allow(p, prop_name, value, event=None,):
        node_value(p, "s_ecosystem_repulsion.influences", value=value, entry="node_socket", socket_idx=0)
    
    @tag_register()
    def s_ecosystem_repulsion_dist_influence(p, prop_name, value, event=None,):
        node_value(p, "s_ecosystem_repulsion.influences", value=value/100, entry="node_socket", socket_idx=1)
    
    @tag_register()
    def s_ecosystem_repulsion_scale_infl_allow(p, prop_name, value, event=None,):
        node_value(p, "s_ecosystem_repulsion.influences", value=value, entry="node_socket", socket_idx=3)
    
    @tag_register()
    def s_ecosystem_repulsion_scale_influence(p, prop_name, value, event=None,):
        node_value(p, "s_ecosystem_repulsion.influences", value=value/100, entry="node_socket", socket_idx=4)

    codegen_umask_updatefct(scope_ref=locals(), name="s_ecosystem_repulsion",)

    #Density
    
    @tag_register()
    def s_ecosystem_density_allow(p, prop_name, value, event=None,):
        mute_color(p, f"Eco Density", mute=not value,)
        node_link(p, f"RR_VEC s_ecosystem_density Receptor", f"RR_VEC s_ecosystem_density {bool(value)}",)
        node_link(p, f"RR_GEO s_ecosystem_density Receptor", f"RR_GEO s_ecosystem_density {bool(value)}",)
        
    @tag_register()
    def s_ecosystem_density_space(p, prop_name, value, event=None,):
        node_value(p, "s_ecosystem_density.use_local", value=(value=="local"), entry="boolean_input")
        
    @tag_register()
    def s_ecosystem_density_method(p, prop_name, value, event=None,):
        node_value(p,  f"s_ecosystem_density.{prop_name}", value=get_enum_idx(p, prop_name, value,), entry="integer_input")
    
    @tag_register(nbr=3)
    def s_ecosystem_density_XX_ptr(p, prop_name, value, event=None,):
        idx = int(prop_name[21])
        targetp = bpy.context.scene.scatter5.get_psy_by_name(value)
        so = targetp.scatter_obj if (targetp) else None
        node_value(p, f"s_ecosystem_density.slot{idx}", value=so, entry="node_socket", socket_idx=0)
        mute_node(p, f"s_ecosystem_density.slot{idx}", mute=(so is None),)
        #adjust slot interface
        if (value==""):
            if (idx==3):
                if (p.s_ecosystem_density_02_ptr==""):
                      p.s_ecosystem_density_ui_max_slot = 1
                else: p.s_ecosystem_density_ui_max_slot = 2
            elif (idx==2):
                if (p.s_ecosystem_density_03_ptr==""):
                    p.s_ecosystem_density_ui_max_slot = 1

    @tag_register()
    def s_ecosystem_density_voxelsize(p, prop_name, value, event=None,):
        node_value(p, f"s_ecosystem_density.{prop_name}", value=value, entry="float_input")

    @tag_register()
    def s_ecosystem_density_min(p, prop_name, value, event=None,):
        node_value(p, f"s_ecosystem_density.{prop_name}", value=value, entry="integer_input")

    @tag_register()
    def s_ecosystem_density_falloff(p, prop_name, value, event=None,):
        node_value(p, f"s_ecosystem_density.{prop_name}", value=value, entry="integer_input")

    @tag_register()
    def s_ecosystem_density_fallremap_allow(p, prop_name, value, event=None,):
        mute_node(p, "s_ecosystem_density.fallremap",mute=not value)
        mute_node(p, "s_ecosystem_density.fallremap_revert",mute=not p.s_ecosystem_density_fallremap_revert if value else True)
        mute_node(p, "s_ecosystem_density.fallnoisy",mute=not value)

    @tag_register()
    def s_ecosystem_density_fallremap_revert(p, prop_name, value, event=None,):
        mute_node(p, "s_ecosystem_density.fallremap_revert",mute=not value)
    
    @tag_register()
    def s_ecosystem_density_fallnoisy_strength(p, prop_name, value, event=None,):
        node_value(p, "s_ecosystem_density.fallnoisy", value=value, entry="node_socket", socket_idx=1)

    @tag_register()
    def s_ecosystem_density_fallnoisy_space(p, prop_name, value, event=None,):
        node_value(p, "s_ecosystem_density.fallnoisy", value=value=='local', entry="node_socket", socket_idx=5)
    
    @tag_register()
    def s_ecosystem_density_fallnoisy_scale(p, prop_name, value, event=None,):
        node_value(p, "s_ecosystem_density.fallnoisy", value=value, entry="node_socket", socket_idx=2)
    
    @tag_register()
    def s_ecosystem_density_fallnoisy_seed(p, prop_name, value, event=None,):
        node_value(p, "s_ecosystem_density.fallnoisy", value=value, entry="node_socket", socket_idx=3)
    
    @tag_register()
    def s_ecosystem_density_fallnoisy_is_random_seed(p, prop_name, value, event=None,):
        random_seed(p, event, api_is_random=prop_name, api_seed="s_ecosystem_density_fallnoisy_seed")

    @tag_register()
    def s_ecosystem_density_dist_infl_allow(p, prop_name, value, event=None,):
        node_value(p, "s_ecosystem_density.influences", value=value, entry="node_socket", socket_idx=0)
    
    @tag_register()
    def s_ecosystem_density_dist_influence(p, prop_name, value, event=None,):
        node_value(p, "s_ecosystem_density.influences", value=value/100, entry="node_socket", socket_idx=1)
    
    @tag_register()
    def s_ecosystem_density_scale_infl_allow(p, prop_name, value, event=None,):
        node_value(p, "s_ecosystem_density.influences", value=value, entry="node_socket", socket_idx=3)
    
    @tag_register()
    def s_ecosystem_density_scale_influence(p, prop_name, value, event=None,):
        node_value(p, "s_ecosystem_density.influences", value=value/100, entry="node_socket", socket_idx=4)

    codegen_umask_updatefct(scope_ref=locals(), name="s_ecosystem_density",)

    # 88""Yb 88   88 .dP"Y8 88  88
    # 88__dP 88   88 `Ybo." 88  88
    # 88"""  Y8   8P o.`Y8b 888888
    # 88     `YbodP' 8bodP' 88  88

    @tag_register()
    def s_push_master_allow(p, prop_name, value, event=None,):
        for prop in p.get_s_push_main_features(availability_conditions=False,):
            mute_node(p, prop.replace("_allow",""), mute=not value,)

    #Push Offset

    @tag_register()
    def s_push_offset_allow(p, prop_name, value, event=None,):
        mute_color(p, f"Push Offset", mute=not value,)
        node_link(p, f"RR_GEO s_push_offset Receptor", f"RR_GEO s_push_offset {bool(value)}",)

    @tag_register()
    def s_push_offset_space(p, prop_name, value, event=None,):
        node_value(p, f"s_push_offset", value=(value=="global"), entry="node_socket", socket_idx=1)

    @tag_register()
    def s_push_offset_add_value(p, prop_name, value, event=None,):
        node_value(p, f"s_push_offset", value=value, entry="node_socket", socket_idx=2)

    @tag_register()
    def s_push_offset_add_random(p, prop_name, value, event=None,):
        node_value(p, f"s_push_offset", value=value, entry="node_socket", socket_idx=3)

    @tag_register()
    def s_push_offset_rotate_value(p, prop_name, value, event=None,):
        node_value(p, f"s_push_offset", value=value, entry="node_socket", socket_idx=4)

    @tag_register()
    def s_push_offset_rotate_random(p, prop_name, value, event=None,):
        node_value(p, f"s_push_offset", value=value, entry="node_socket", socket_idx=5)

    @tag_register()
    def s_push_offset_scale_value(p, prop_name, value, event=None,):
        node_value(p, f"s_push_offset", value=value, entry="node_socket", socket_idx=6)

    @tag_register()
    def s_push_offset_scale_random(p, prop_name, value, event=None,):
        node_value(p, f"s_push_offset", value=value, entry="node_socket", socket_idx=7)

    @tag_register()
    def s_push_offset_seed(p, prop_name, value, event=None,):
        node_value(p, f"s_push_offset", value=value, entry="node_socket", socket_idx=8)
        
    @tag_register()
    def s_push_offset_is_random_seed(p, prop_name, value, event=None,):
        random_seed(p, event, api_is_random=prop_name, api_seed="s_push_offset_seed")

    codegen_umask_updatefct(scope_ref=locals(), name="s_push_offset",)

    #Push Direction 

    @tag_register()
    def s_push_dir_allow(p, prop_name, value, event=None,):
        mute_color(p, f"Push Direction", mute=not value,)
        node_link(p, f"RR_GEO s_push_dir Receptor", f"RR_GEO s_push_dir {bool(value)}",)

    @tag_register()
    def s_push_dir_space(p, prop_name, value, event=None,):
        node_value(p, f"s_push_dir", value=(value=="global"), entry="node_socket", socket_idx=3)

    @tag_register()
    def s_push_dir_method(p, prop_name, value, event=None,):
        node_value(p, f"s_push_dir", value=get_enum_idx(p, prop_name, value,), entry="node_socket", socket_idx=4)
    @tag_register()
    def s_push_dir_method_projbezareanosurf_special(p, prop_name, value, event=None,):
        if (p.s_distribution_method=="projbezarea" and not p.is_using_surf):
            node_value(p, f"s_push_dir", value=get_enum_idx(p, prop_name, value,), entry="node_socket", socket_idx=4)
    @tag_register()
    def s_push_dir_method_projbezlinenosurf_special(p, prop_name, value, event=None,):
        if (p.s_distribution_method=="projbezline" and not p.is_using_surf):
            node_value(p, f"s_push_dir", value=get_enum_idx(p, prop_name, value,), entry="node_socket", socket_idx=4)
    @tag_register()
    def s_push_dir_method_projemptiesnosurf_special(p, prop_name, value, event=None,):
        if (p.s_distribution_method=="projempties" and not p.is_using_surf):
            node_value(p, f"s_push_dir", value=get_enum_idx(p, prop_name, value,), entry="node_socket", socket_idx=4)
            
    @tag_register()
    def s_push_dir_add_value(p, prop_name, value, event=None,):
        node_value(p, f"s_push_dir", value=value, entry="node_socket", socket_idx=5)

    @tag_register()
    def s_push_dir_add_random(p, prop_name, value, event=None,):
        node_value(p, f"s_push_dir", value=value, entry="node_socket", socket_idx=6)

    @tag_register()
    def s_push_dir_seed(p, prop_name, value, event=None,):
        node_value(p, f"s_push_dir", value=value, entry="node_socket", socket_idx=7)
        
    @tag_register()
    def s_push_dir_is_random_seed(p, prop_name, value, event=None,):
        random_seed(p, event, api_is_random=prop_name, api_seed="s_push_dir_seed")

    codegen_umask_updatefct(scope_ref=locals(), name="s_push_dir",)

    #Push Noise 

    @tag_register()
    def s_push_noise_allow(p, prop_name, value, event=None,):
        mute_color(p, f"Push Noise", mute=not value,)
        node_link(p, f"RR_GEO s_push_noise Receptor", f"RR_GEO s_push_noise {bool(value)}",)

    @tag_register()
    def s_push_noise_space(p, prop_name, value, event=None,):
        node_value(p, f"s_push_noise", value=(value=="global"), entry="node_socket", socket_idx=1)

    @tag_register()
    def s_push_noise_vector(p, prop_name, value, event=None,):
        node_value(p, f"s_push_noise", value=value, entry="node_socket", socket_idx=2)

    @tag_register()
    def s_push_noise_is_animated(p, prop_name, value, event=None,):
        node_value(p, f"s_push_noise", value=value, entry="node_socket", socket_idx=3)

    @tag_register()
    def s_push_noise_speed(p, prop_name, value, event=None,):
        node_value(p, f"s_push_noise", value=value, entry="node_socket", socket_idx=4)

    @tag_register()
    def s_push_noise_seed(p, prop_name, value, event=None,):
        node_value(p, f"s_push_noise", value=value, entry="node_socket", socket_idx=5)
        
    @tag_register()
    def s_push_noise_is_random_seed(p, prop_name, value, event=None,):
        random_seed(p, event, api_is_random=prop_name, api_seed="s_push_noise_seed")

    codegen_umask_updatefct(scope_ref=locals(), name="s_push_noise",)

    #Fall

    @tag_register()
    def s_push_fall_allow(p, prop_name, value, event=None,):
        mute_color(p, f"Push Fall", mute=not value,)
        node_link(p, f"RR_VEC s_push_fall Receptor", f"RR_VEC s_push_fall {bool(value)}",)
        node_link(p, f"RR_GEO s_push_fall Receptor", f"RR_GEO s_push_fall {bool(value)}",)

    @tag_register()
    def s_push_fall_space(p, prop_name, value, event=None,):
        node_value(p, f"s_push_fall", value=(value=="global"), entry="node_socket", socket_idx=2)

    @tag_register()
    def s_push_fall_height(p, prop_name, value, event=None,):
        node_value(p, f"s_push_fall", value=value, entry="node_socket", socket_idx=3)

    @tag_register()
    def s_push_fall_key1_pos(p, prop_name, value, event=None,):
        node_value(p, f"s_push_fall", value=value, entry="node_socket", socket_idx=4)

    @tag_register()
    def s_push_fall_key2_pos(p, prop_name, value, event=None,):
        node_value(p, f"s_push_fall", value=value, entry="node_socket", socket_idx=5)

    @tag_register()
    def s_push_fall_key1_height(p, prop_name, value, event=None,):
        node_value(p, f"s_push_fall", value=value, entry="node_socket", socket_idx=6)

    @tag_register()
    def s_push_fall_key2_height(p, prop_name, value, event=None,):
        node_value(p, f"s_push_fall", value=value, entry="node_socket", socket_idx=7)

    @tag_register()
    def s_push_fall_stop_when_initial_z(p, prop_name, value, event=None,):
        node_value(p, f"s_push_fall", value=value, entry="node_socket", socket_idx=8)

    @tag_register()
    def s_push_fall_turbulence_allow(p, prop_name, value, event=None,):
        node_value(p, f"s_push_fall", value=value, entry="node_socket", socket_idx=9)

    @tag_register()
    def s_push_fall_turbulence_spread(p, prop_name, value, event=None,):
        node_value(p, f"s_push_fall", value=value, entry="node_socket", socket_idx=10)

    @tag_register()
    def s_push_fall_turbulence_speed(p, prop_name, value, event=None,):
        node_value(p, f"s_push_fall", value=value, entry="node_socket", socket_idx=11)

    @tag_register()
    def s_push_fall_turbulence_rot_vector(p, prop_name, value, event=None,):
        node_value(p, f"s_push_fall", value=vector_type(value), entry="node_socket", socket_idx=12)

    @tag_register()
    def s_push_fall_turbulence_rot_factor(p, prop_name, value, event=None,):
        node_value(p, f"s_push_fall", value=value, entry="node_socket", socket_idx=13)

    @tag_register()
    def s_push_fall_seed(p, prop_name, value, event=None,):
        node_value(p, f"s_push_fall", value=value, entry="node_socket", socket_idx=14)
        
    @tag_register()
    def s_push_fall_is_random_seed(p, prop_name, value, event=None,):
        random_seed(p, event, api_is_random=prop_name, api_seed="s_push_fall_seed")
    
    codegen_umask_updatefct(scope_ref=locals(), name="s_push_fall",)

    ################ Wind 

    @tag_register()
    def s_wind_master_allow(p, prop_name, value, event=None,):
        for prop in p.get_s_wind_main_features(availability_conditions=False,):
            mute_node(p, prop.replace("_allow",""), mute=not value,)

    # Yb        dP 88 88b 88 8888b.  
    #  Yb  db  dP  88 88Yb88  8I  Yb 
    #   YbdPYbdP   88 88 Y88  8I  dY 
    #    YP  YP    88 88  Y8 8888Y" 

    @tag_register()
    def s_wind_wave_allow(p, prop_name, value, event=None,):
        mute_color(p, f"Wind Wave", mute=not value,)
        node_link(p, f"RR_VEC s_wind_wave Receptor", f"RR_VEC s_wind_wave {bool(value)}",)
        update_frame_start_end_nodegroup()

    @tag_register()
    def s_wind_wave_space(p, prop_name, value, event=None,):
        node_value(p, "s_wind_wave", value=(value=="global"), entry="node_socket", socket_idx=3)

    @tag_register()
    def s_wind_wave_method(p, prop_name, value, event=None,):
        node_value(p, "s_wind_wave", value=value=="wind_wave_loopable", entry="node_socket", socket_idx=4)
        update_frame_start_end_nodegroup()

    @tag_register()
    def s_wind_wave_loopable_cliplength_allow(p, prop_name, value, event=None,):
        node_value(p, "s_wind_wave", value=not value, entry="node_socket", socket_idx=5)
        update_frame_start_end_nodegroup()

    @tag_register()
    def s_wind_wave_loopable_frame_start(p, prop_name, value, event=None,):
        node_value(p, "s_wind_wave", value=value, entry="node_socket", socket_idx=6)

    @tag_register()
    def s_wind_wave_loopable_frame_end(p, prop_name, value, event=None,):
        node_value(p, "s_wind_wave", value=value, entry="node_socket", socket_idx=7)

    @tag_register()
    def s_wind_wave_speed(p, prop_name, value, event=None,):
        node_value(p, "s_wind_wave", value=value, entry="node_socket", socket_idx=8)

    @tag_register()
    def s_wind_wave_direction(p, prop_name, value, event=None,):
        node_value(p, "s_wind_wave", value=value, entry="node_socket", socket_idx=9)

    @tag_register()
    def s_wind_wave_direction_random(p, prop_name, value, event=None,):
        node_value(p, "s_wind_wave", value=value, entry="node_socket", socket_idx=10)

    @tag_register()
    def s_wind_wave_force(p, prop_name, value, event=None,):
        node_value(p, "s_wind_wave", value=value, entry="node_socket", socket_idx=11)

    @tag_register()
    def s_wind_wave_scale_influence(p, prop_name, value, event=None,):
        node_value(p, "s_wind_wave", value=value, entry="node_socket", socket_idx=12)
        
    @tag_register()
    def s_wind_wave_scale_influence_factor(p, prop_name, value, event=None,):
        node_value(p, "s_wind_wave", value=value, entry="node_socket", socket_idx=13) 
        
    @tag_register()
    def s_wind_wave_swinging(p, prop_name, value, event=None,):
        node_value(p, "s_wind_wave", value=value, entry="node_socket", socket_idx=14)
    
    @tag_register()
    def s_wind_wave_swinging_factor(p, prop_name, value, event=None,):
        node_value(p, "s_wind_wave", value=value, entry="node_socket", socket_idx=15)    

    @tag_register()
    def s_wind_wave_texture_scale(p, prop_name, value, event=None,):
        node_value(p, "s_wind_wave", value=value, entry="node_socket", socket_idx=16)

    @tag_register()
    def s_wind_wave_texture_turbulence(p, prop_name, value, event=None,):
        node_value(p, "s_wind_wave", value=value, entry="node_socket", socket_idx=17)

    @tag_register()
    def s_wind_wave_texture_distorsion(p, prop_name, value, event=None,):
        node_value(p, "s_wind_wave", value=value, entry="node_socket", socket_idx=18)

    @tag_register()
    def s_wind_wave_texture_brightness(p, prop_name, value, event=None,):
        node_value(p, "s_wind_wave", value=value, entry="node_socket", socket_idx=19)

    @tag_register()
    def s_wind_wave_texture_contrast(p, prop_name, value, event=None,):
        node_value(p, "s_wind_wave", value=value, entry="node_socket", socket_idx=20)

    @tag_register()
    def s_wind_wave_dir_method(p, prop_name, value, event=None,):
        node_value(p, "s_wind_wave", value=(value=='vcol'), entry="node_socket", socket_idx=21) #allow flowmap

    @tag_register()
    def s_wind_wave_flowmap_ptr(p, prop_name, value, event=None,):
        node_value(p, "s_wind_wave", value=value, entry="node_socket", socket_idx=22)

    codegen_umask_updatefct(scope_ref=locals(), name="s_wind_wave",)

    #Wind Noise

    @tag_register()
    def s_wind_noise_allow(p, prop_name, value, event=None,):
        mute_color(p, f"Wind Noise", mute=not value,)
        node_link(p, f"RR_VEC s_wind_noise Receptor", f"RR_VEC s_wind_noise {bool(value)}",)
        update_frame_start_end_nodegroup()

    @tag_register()
    def s_wind_noise_space(p, prop_name, value, event=None,):
        node_value(p, "s_wind_noise", value=(value=="global"), entry="node_socket", socket_idx=2)

    @tag_register()
    def s_wind_noise_method(p, prop_name, value, event=None,):
        node_value(p, "s_wind_noise", value=value=="wind_noise_loopable", entry="node_socket", socket_idx=3)
        update_frame_start_end_nodegroup()

    @tag_register()
    def s_wind_noise_loopable_cliplength_allow(p, prop_name, value, event=None,):
        node_value(p, "s_wind_noise", value=not value, entry="node_socket", socket_idx=4)
        update_frame_start_end_nodegroup()

    @tag_register()
    def s_wind_noise_loopable_frame_start(p, prop_name, value, event=None,):
        node_value(p, "s_wind_noise", value=value, entry="node_socket", socket_idx=5)

    @tag_register()
    def s_wind_noise_loopable_frame_end(p, prop_name, value, event=None,):
        node_value(p, "s_wind_noise", value=value, entry="node_socket", socket_idx=6)

    @tag_register()
    def s_wind_noise_force(p, prop_name, value, event=None,):
        node_value(p, "s_wind_noise", value=value, entry="node_socket", socket_idx=7)

    @tag_register()
    def s_wind_noise_speed(p, prop_name, value, event=None,):
        node_value(p, "s_wind_noise", value=value, entry="node_socket", socket_idx=8)

    codegen_umask_updatefct(scope_ref=locals(), name="s_wind_noise",)


    # Yb    dP 88 .dP"Y8 88 88""Yb 88 88     88 888888 Yb  dP
    #  Yb  dP  88 `Ybo." 88 88__dP 88 88     88   88    YbdP
    #   YbdP   88 o.`Y8b 88 88""Yb 88 88  .o 88   88     8P
    #    YP    88 8bodP' 88 88oodP 88 88ood8 88   88    dP
    
    @tag_register()
    def s_visibility_master_allow(p, prop_name, value, event=None,):
        for prop in p.get_s_visibility_main_features(availability_conditions=False,):
            mute_node(p, prop.replace("_allow",""), mute=not value,)
        mute_node(p, "s_visibility_cam_predist", mute=not value,) #also this feature, linked to s_visibility cam

    #Face Preview

    @tag_register()
    def s_visibility_facepreview_allow(p, prop_name, value, event=None,):
        mute_color(p, "Face Preview", mute=not value,)
        node_link(p, f"RR_FLOAT s_visibility_facepreview Receptor", f"RR_FLOAT s_visibility_facepreview {bool(value)}",)

    @tag_register()
    def s_visibility_facepreview_viewport_method(p, prop_name, value, event=None,):
        ensure_viewport_method_interface(p, "s_visibility_facepreview", value,)
        node_value(p, "s_visibility_facepreview", value=get_enum_idx(p, prop_name, value), entry="node_socket", socket_idx=4)

    #Viewport %

    @tag_register()
    def s_visibility_view_allow(p, prop_name, value, event=None,):
        mute_color(p,"% Optimization", mute=not value,) 
        node_link(p, f"RR_FLOAT s_visibility_view Receptor", f"RR_FLOAT s_visibility_view {bool(value)}",)

    @tag_register()
    def s_visibility_view_percentage(p, prop_name, value, event=None,):
        node_value(p, "s_visibility_view", value=value/100, entry="node_socket", socket_idx=1)

    @tag_register()
    def s_visibility_view_viewport_method(p, prop_name, value, event=None,):
        ensure_viewport_method_interface(p, "s_visibility_view", value,)
        node_value(p, "s_visibility_view", value=get_enum_idx(p, prop_name, value), entry="node_socket", socket_idx=2)

    #Camera Optimization 

    @tag_register()
    def s_visibility_cam_allow(p, prop_name, value, event=None,):
        mute_color(p,"Camera Optimization", mute=not value,) 
        node_link(p, f"RR_GEO s_visibility_cam Receptor", f"RR_GEO s_visibility_cam {bool(value)}",)
        p.property_nodetree_refresh("s_visibility_cam_predist_allow")
        if (value==True):
            update_camera_nodegroup(force_update=True, reset_hash=True,)
    
    @tag_register()
    def s_visibility_cam_predist_allow(p, prop_name, value, event=None,):
        if (not p.s_visibility_cam_allow):
            value = False
        mute_color(p,"Pre Cam Opti", mute=not value,) 
        node_link(p, f"RR_FLOAT s_visibility_cam_predist Receptor", f"RR_FLOAT s_visibility_cam_predist {bool(value)}",)

    @tag_register()
    def s_visibility_camclip_allow(p, prop_name, value, event=None,):
        node_value(p, "s_visibility_cam", value=value, entry="node_socket", socket_idx=5)
        node_value(p, "s_visibility_cam_predist", value=value, entry="node_socket", socket_idx=5)
        if (value==True):
            update_camera_nodegroup(force_update=True, reset_hash=True,)
            
    @tag_register()
    def s_visibility_camclip_cam_autofill(p, prop_name, value, event=None,):
        match value:
            case True:
                update_camera_nodegroup(force_update=True, reset_hash=True,)
            case False:
                p.s_visibility_camclip_cam_res_xy = p.s_visibility_camclip_cam_res_xy
                p.s_visibility_camclip_cam_shift_xy = p.s_visibility_camclip_cam_shift_xy
                p.s_visibility_camclip_cam_lens = p.s_visibility_camclip_cam_lens
                p.s_visibility_camclip_cam_sensor_width = p.s_visibility_camclip_cam_sensor_width
                p.s_visibility_camclip_cam_boost_xy = p.s_visibility_camclip_cam_boost_xy
                node_value(p, "s_cam_infos", value=0, entry="node_socket", socket_idx=8) #Default sensor fit method==auto

    @tag_register()
    def s_visibility_camclip_cam_lens(p, prop_name, value, event=None,):
        node_value(p, "s_cam_infos", value=value, entry="node_socket", socket_idx=1)

    @tag_register()
    def s_visibility_camclip_cam_sensor_width(p, prop_name, value, event=None,):
        node_value(p, "s_cam_infos", value=value, entry="node_socket", socket_idx=0)

    @tag_register()
    def s_visibility_camclip_cam_res_xy(p, prop_name, value, event=None,):
        node_value(p, "s_cam_infos", value=value[0], entry="node_socket", socket_idx=4)
        node_value(p, "s_cam_infos", value=value[1], entry="node_socket", socket_idx=5)

    @tag_register()
    def s_visibility_camclip_cam_shift_xy(p, prop_name, value, event=None,):
        node_value(p, "s_cam_infos", value=value[0], entry="node_socket", socket_idx=2)
        node_value(p, "s_cam_infos", value=value[1], entry="node_socket", socket_idx=3)
        
    @tag_register()
    def s_visibility_camclip_cam_boost_xy(p, prop_name, value, event=None,):
        node_value(p, "s_cam_infos", value=value[0], entry="node_socket", socket_idx=6)
        node_value(p, "s_cam_infos", value=value[1], entry="node_socket", socket_idx=7)
        
    @tag_register()
    def s_visibility_camclip_proximity_allow(p, prop_name, value, event=None,):
        node_value(p, "s_visibility_cam", value=value, entry="node_socket", socket_idx=6)
        node_value(p, "s_visibility_cam_predist", value=value, entry="node_socket", socket_idx=6)

    @tag_register()
    def s_visibility_camclip_proximity_distance(p, prop_name, value, event=None,):
        node_value(p, "s_visibility_cam", value=value, entry="node_socket", socket_idx=7)
        node_value(p, "s_visibility_cam_predist", value=value, entry="node_socket", socket_idx=7)

    @tag_register()
    def s_visibility_camdist_allow(p, prop_name, value, event=None,):
        node_value(p, "s_visibility_cam", value=value, entry="node_socket", socket_idx=8)
        node_value(p, "s_visibility_cam_predist", value=value, entry="node_socket", socket_idx=8)
        if (value==True):
            update_camera_nodegroup(force_update=True, reset_hash=True,)

    @tag_register()
    def s_visibility_camdist_min(p, prop_name, value, event=None,):
        node_value(p, "s_visibility_cam", value=value, entry="node_socket", socket_idx=9)
        node_value(p, "s_visibility_cam_predist", value=value, entry="node_socket", socket_idx=9)

    @tag_register()
    def s_visibility_camdist_max(p, prop_name, value, event=None,):
        node_value(p, "s_visibility_cam", value=value, entry="node_socket", socket_idx=10)
        node_value(p, "s_visibility_cam_predist", value=value, entry="node_socket", socket_idx=10)

    @tag_register()
    def s_visibility_camdist_fallremap_allow(p, prop_name, value, event=None,):
        mute_node(p, "s_visibility_cam.fallremap",mute=not value)

    @tag_register()
    def s_visibility_camdist_fallremap_revert(p, prop_name, value, event=None,):
        mute_node(p, "s_visibility_cam.fallremap_revert",mute=not value)

    @tag_register()
    def s_visibility_camdist_per_cam_data(p, prop_name, value, event=None,):
        match value:
            case True:
                active_cam = bpy.context.scene.camera
                if (active_cam is not None):
                    active_cam.scatter5.s_visibility_camdist_per_cam_min = active_cam.scatter5.s_visibility_camdist_per_cam_min 
                    active_cam.scatter5.s_visibility_camdist_per_cam_max = active_cam.scatter5.s_visibility_camdist_per_cam_max 
            case False:
                p.property_nodetree_refresh("s_visibility_camdist_min")
                p.property_nodetree_refresh("s_visibility_camdist_max")

    @tag_register()
    def s_visibility_camoccl_allow(p, prop_name, value, event=None,):
        node_value(p, "s_visibility_cam", value=value, entry="node_socket", socket_idx=11)

    @tag_register()
    def s_visibility_camoccl_threshold(p, prop_name, value, event=None,):
        node_value(p, "s_visibility_cam", value=value, entry="node_socket", socket_idx=12)

    @tag_register()
    def s_visibility_camoccl_method(p, prop_name, value, event=None,):
        node_value(p, "s_visibility_cam", value=get_enum_idx(p, prop_name, value), entry="node_socket", socket_idx=13)

    @tag_register()
    def s_visibility_camoccl_coll_ptr(p, prop_name, value, event=None,):
        node_value(p, "s_visibility_cam", value=bpy.data.collections.get(value), entry="node_socket", socket_idx=14)

    @tag_register()
    def s_visibility_cam_viewport_method(p, prop_name, value, event=None,):
        ensure_viewport_method_interface(p, "s_visibility_cam", value,)
        node_value(p, "s_visibility_cam", value=get_enum_idx(p, prop_name, value), entry="node_socket", socket_idx=15)

    #Maximum Load

    @tag_register()
    def s_visibility_maxload_allow(p, prop_name, value, event=None,):
        mute_color(p, f"Max Load", mute=not value,)
        node_link(p, f"RR_GEO s_visibility_maxload Receptor", f"RR_GEO s_visibility_maxload {bool(value)}",)

    @tag_register()
    def s_visibility_maxload_cull_method(p, prop_name, value, event=None,):
        node_value(p, "s_visibility_maxload", value=value=="maxload_limit", entry="node_socket", socket_idx=1)

    @tag_register()
    def s_visibility_maxload_treshold(p, prop_name, value, event=None,):
        node_value(p, "s_visibility_maxload", value=value, entry="node_socket", socket_idx=2)

    @tag_register()
    def s_visibility_maxload_viewport_method(p, prop_name, value, event=None,):
        ensure_viewport_method_interface(p, "s_visibility_maxload", value,)
        node_value(p, "s_visibility_maxload", value=get_enum_idx(p, prop_name, value), entry="node_socket", socket_idx=3)

    # 88 88b 88 .dP"Y8 888888    db    88b 88  dP""b8 88 88b 88  dP""b8
    # 88 88Yb88 `Ybo."   88     dPYb   88Yb88 dP   `" 88 88Yb88 dP   `"
    # 88 88 Y88 o.`Y8b   88    dP__Yb  88 Y88 Yb      88 88 Y88 Yb  "88
    # 88 88  Y8 8bodP'   88   dP""""Yb 88  Y8  YboodP 88 88  Y8  YboodP

    @tag_register()
    def s_instances_method(p, prop_name, value, event=None,):
        ins_points = p.s_instances_method=="ins_points"
        mute_color(p, "Raw Points", mute=not ins_points,)
        node_link(p, f"RR_GEO output_points Receptor", f"RR_GEO output_points {ins_points}",)
        
    @tag_register()
    def s_instances_coll_ptr(p, prop_name, value, event=None,):
        node_value(p, prop_name, value=value, entry="node_socket")

    @tag_register()
    def s_instances_pick_method(p, prop_name, value, event=None,):
        node_link(p, prop_name, value)
        node_link(p, prop_name+" PICK", value+" PICK")
        mute_node(p, "s_instances_pick_scale", mute=(value!="pick_scale"))

    @tag_register()
    def s_instances_seed(p, prop_name, value, event=None,):
        node_value(p, prop_name, value=value, entry="integer_input")

    @tag_register()
    def s_instances_is_random_seed(p, prop_name, value, event=None,):
        random_seed(p, event, api_is_random=prop_name, api_seed="s_instances_seed")

    @tag_register(nbr=20)
    def s_instances_id_XX_rate(p, prop_name, value, event=None,):
        idx = int(prop_name[15:17])
        node_value(p, "s_instances_pick_rate", value=value/100, entry="node_socket", socket_idx=idx)

    @tag_register()
    def s_instances_id_scale_method(p, prop_name, value, event=None,):
        node_value(p, prop_name, value=get_enum_idx(p, prop_name, value), entry="integer_input")

    @tag_register(nbr=20)
    def s_instances_id_XX_scale_min(p, prop_name, value, event=None,):
        idx = int(prop_name[15:17])
        idx *=2 
        idx -=1
        node_value(p, "s_instances_pick_scale", value=value, entry="node_socket", socket_idx=idx)

    @tag_register(nbr=20)
    def s_instances_id_XX_scale_max(p, prop_name, value, event=None,):
        idx = int(prop_name[15:17])
        idx *=2 
        node_value(p, "s_instances_pick_scale", value=value, entry="node_socket", socket_idx=idx)

    @tag_register()
    def s_instances_pick_cluster_projection_method(p, prop_name, value, event=None,):
        node_value(p, "s_instances_pick_cluster", value=get_enum_idx(p, prop_name, value), entry="node_socket", socket_idx=0)

    @tag_register()
    def s_instances_pick_cluster_scale(p, prop_name, value, event=None,):
        node_value(p, "s_instances_pick_cluster", value=value, entry="node_socket", socket_idx=1)

    @tag_register()
    def s_instances_pick_cluster_blur(p, prop_name, value, event=None,):
        node_value(p, "s_instances_pick_cluster", value=value, entry="node_socket", socket_idx=2)

    @tag_register()
    def s_instances_pick_clump(p, prop_name, value, event=None,):
        node_value(p, prop_name, value=value, entry="boolean_input")

    @tag_register(nbr=20)
    def s_instances_id_XX_color(p, prop_name, value, event=None,):
        idx = int(prop_name[15:17])
        node_value(p, "s_instances_pick_color", value=color_type(value), entry="node_socket", socket_idx=idx)

    @tag_register()
    def s_instances_id_color_tolerence(p, prop_name, value, event=None,):
        node_value(p, prop_name, value=value, entry="float_input") 

    @tag_register()
    def s_instances_id_color_sample_method(p, prop_name, value, event=None,):
        node_value(p, "s_instances_is_vcol", value=value=="vcol", entry="boolean_input")

    @tag_register()
    def s_instances_texture_ptr(p, prop_name, value, event=None,):
        set_texture_ptr(p, f"s_instances_pick_color_textures.texture", value)

    @tag_register()
    def s_instances_vcol_ptr(p, prop_name, value, event=None,):
        node_value(p, prop_name, value=value, entry="named_attr",)

    # 8888b.  88 .dP"Y8 88""Yb 88        db    Yb  dP
    #  8I  Yb 88 `Ybo." 88__dP 88       dPYb    YbdP
    #  8I  dY 88 o.`Y8b 88"""  88  .o  dP__Yb    8P
    # 8888Y"  88 8bodP' 88     88ood8 dP""""Yb  dP

    @tag_register()
    def s_display_master_allow(p, prop_name, value, event=None,):
        for prop in p.get_s_display_main_features(availability_conditions=False,):
            continue #TODO, this will bug, need nodegroups...
            mute_node(p, prop.replace("_allow",""), mute=not value,)

    #Display As

    @tag_register()
    def s_display_allow(p, prop_name, value, event=None,):
        node_value(p, prop_name, value=value, entry="boolean_input")
        mute_color(p, "Display", mute=not value)
        mute_color(p, "Display Features", mute=not value)
        if (value==True):
            update_is_rendered_view_nodegroup()

    @tag_register()
    def s_display_method(p, prop_name, value, event=None,):
        node_link(p, prop_name, value,)

    @tag_register()
    def s_display_placeholder_type(p, prop_name, value, event=None,):
        placeholder = bpy.data.objects.get(value)
        if (placeholder is None): 
            #attempt to find duplicates?
            for i in range(9):
                placeholder = bpy.data.objects.get(f"{value}.00{i}")
                if (placeholder is not None):
                    break
        if (placeholder is not None): 
              node_value(p, prop_name, value=placeholder, entry="node_socket")
        else: print("ERROR: s_display_placeholder_type(): Couldn't find placeholder object data, was it removed from this .blend ?")

    @tag_register()
    def s_display_custom_placeholder_ptr(p, prop_name, value, event=None,):
        node_value(p, prop_name, value=value, entry="node_socket")

    @tag_register()
    def s_display_placeholder_scale(p, prop_name, value, event=None,):
        node_value(p, prop_name, value=value, entry="vector_input")

    @tag_register()
    def s_display_point_radius(p, prop_name, value, event=None,):
        node_value(p, prop_name, value=value, entry="float_input")

    @tag_register()
    def s_display_cloud_radius(p, prop_name, value, event=None,):
        node_value(p, prop_name, value=value, entry="float_input")

    @tag_register()
    def s_display_cloud_density(p, prop_name, value, event=None,):
        node_value(p, prop_name, value=value, entry="float_input")

    @tag_register()
    def s_display_camdist_allow(p, prop_name, value, event=None,):
        node_value(p, prop_name, value=value, entry="boolean_input")
        mute_color(p, "Closeby Optimization1", mute=not value)
        mute_color(p, "Closeby Optimization2", mute=not value)
        mute_node(p, "s_display_camdist", mute=not value)
        if (value==True):
            update_camera_nodegroup(force_update=True, reset_hash=True,)

    @tag_register()
    def s_display_camdist_distance(p, prop_name, value, event=None,):
        node_value(p, "s_display_camdist", value=value, entry="node_socket", socket_idx=1)

    @tag_register()
    def s_display_viewport_method(p, prop_name, value, event=None,):
        ensure_viewport_method_interface(p, "s_display", value,)
        node_value(p, "s_display_viewport_method", value=get_enum_idx(p, prop_name, value), entry="node_socket", socket_idx=0)

    # 88""Yb 888888  dP""b8 88 88b 88 88b 88 888888 88""Yb  
    # 88__dP 88__   dP   `" 88 88Yb88 88Yb88 88__   88__dP  
    # 88""Yb 88""   Yb  "88 88 88 Y88 88 Y88 88""   88"Yb   
    # 88oodP 888888  YboodP 88 88  Y8 88  Y8 888888 88  Yb  

    @tag_register()
    def s_beginner_default_scale(p, prop_name, value, event=None,):
        if (not p.s_scale_default_allow):
            p.s_scale_default_allow = True
        p.s_scale_default_multiplier = value

    @tag_register()
    def s_beginner_random_scale(p, prop_name, value, event=None,):
        if (not p.s_scale_random_allow):
            p.s_scale_random_allow = True
        p.s_scale_random_factor = [1-value]*3

    @tag_register()
    def s_beginner_random_rot(p, prop_name, value, event=None,):
        if (not p.s_rot_random_allow):
            p.s_rot_random_allow = True
        p.s_rot_random_tilt_value = value * 2.50437
        p.s_rot_random_yaw_value = value * 6.28319
        
    #  dP""b8 88""Yb  dP"Yb  88   88 88""Yb     888888 888888    db    888888 88   88 88""Yb 888888 .dP"Y8 
    # dP   `" 88__dP dP   Yb 88   88 88__dP     88__   88__     dPYb     88   88   88 88__dP 88__   `Ybo." 
    # Yb  "88 88"Yb  Yb   dP Y8   8P 88"""      88""   88""    dP__Yb    88   Y8   8P 88"Yb  88""   o.`Y8b 
    #  YboodP 88  Yb  YbodP  `YbodP' 88         88     888888 dP""""Yb   88   `YbodP' 88  Yb 888888 8bodP' 

    #TODO OPTIMIZATION! 
    # will need to optimize functions to make sure execution is not useless!!
    # Need to check if nodegraph != already equal what we want! 

    @tag_register()
    def s_disable_all_group_features(p, prop_name, value, event=None,):
        """undo all group features (if a psy is not assigned to any groups anymore)"""
        #... keep this function up to date with main group features..
        #if ungroup a group:
        # - mute all mask feature 
        mute_node(p, "s_gr_mask_vg", mute=True,)
        mute_node(p, "s_gr_mask_vcol", mute=True,)
        mute_node(p, "s_gr_mask_bitmap", mute=True,)
        mute_node(p, "s_gr_mask_material", mute=True,)
        mute_node(p, "s_gr_mask_curve", mute=True,)
        mute_node(p, "s_gr_mask_boolvol", mute=True,)
        mute_node(p, "s_gr_mask_upward", mute=True,)
        # - mute all scale features 
        mute_node(p, "s_gr_scale_boost", mute=True,)
        # - mute all pattern feature, and reset texture pointer to avoid virtual users
        mute_node(p, "s_gr_pattern1", mute=True,)
        set_texture_ptr(p, "s_gr_pattern1.texture", "")
        
    ### Distribution
    
    # @tag_register()
    # def s_gr_distribution_master_allow(g, prop_name, value, event=None,):
    #     pass
        
    # @tag_register()
    # def s_gr_distribution_density_boost_allow(g, prop_name, value, event=None,):
    #     pass

    # @tag_register()
    # def s_gr_distribution_density_boost_factor(g, prop_name, value, event=None,):
    #     pass
    
    ### Masks

    @tag_register()
    def s_gr_mask_master_allow(g, prop_name, value, event=None,):
        for prop in g.get_s_gr_mask_main_features(availability_conditions=False,):
            for p in g.get_psy_members():
                mute_node(p, prop.replace("_allow",""), mute=not value,)
    #Vgroup
    
    @tag_register()
    def s_gr_mask_vg_allow(g, prop_name, value, event=None,):
        for p in g.get_psy_members():
            mute_color(p, "Vg Gr Mask", mute=not value,)
            node_link(p, f"RR_FLOAT s_gr_mask_vg Receptor", f"RR_FLOAT s_gr_mask_vg {bool(value)}",)
    
    @tag_register()
    def s_gr_mask_vg_ptr(g, prop_name, value, event=None,):
        for p in g.get_psy_members():
            node_value(p, "s_gr_mask_vg", value=value, entry="node_socket", socket_idx=2)
    
    @tag_register()
    def s_gr_mask_vg_revert(g, prop_name, value, event=None,):
        for p in g.get_psy_members():
            node_value(p, "s_gr_mask_vg", value=value, entry="node_socket", socket_idx=3)

    #VColor
    
    @tag_register()
    def s_gr_mask_vcol_allow(g, prop_name, value, event=None,):
        for p in g.get_psy_members():
            mute_color(p, "Vcol Gr Mask", mute=not value,)
            node_link(p, f"RR_FLOAT s_gr_mask_vcol Receptor", f"RR_FLOAT s_gr_mask_vcol {bool(value)}",)
    
    @tag_register()
    def s_gr_mask_vcol_ptr(g, prop_name, value, event=None,):
        for p in g.get_psy_members():
            node_value(p, "s_gr_mask_vcol", value=value, entry="node_socket", socket_idx=2)
    
    @tag_register()
    def s_gr_mask_vcol_revert(g, prop_name, value, event=None,):
        for p in g.get_psy_members():
            node_value(p, "s_gr_mask_vcol", value=value, entry="node_socket", socket_idx=3)
    
    @tag_register()
    def s_gr_mask_vcol_color_sample_method(g, prop_name, value, event=None,):
        for p in g.get_psy_members():
            node_value(p, "s_gr_mask_vcol", value=get_enum_idx(g, prop_name, value,), entry="node_socket", socket_idx=4)
    
    @tag_register()
    def s_gr_mask_vcol_id_color_ptr(g, prop_name, value, event=None,):
        for p in g.get_psy_members():
            node_value(p, "s_gr_mask_vcol", value=color_type(value), entry="node_socket", socket_idx=5)
    
    #Bitmap 
    
    @tag_register()
    def s_gr_mask_bitmap_allow(g, prop_name, value, event=None,):
        for p in g.get_psy_members():
            mute_color(p, "Img Gr Mask", mute=not value,)
            node_link(p, f"RR_GEO s_gr_mask_bitmap Receptor", f"RR_GEO s_gr_mask_bitmap {bool(value)}",)
        g.s_gr_mask_bitmap_uv_ptr = g.s_gr_mask_bitmap_uv_ptr
    
    @tag_register()
    def s_gr_mask_bitmap_uv_ptr(g, prop_name, value, event=None,):
        for p in g.get_psy_members():
            node_value(p, "s_gr_mask_bitmap", value=value, entry="node_socket", socket_idx=2)
    
    @tag_register()
    def s_gr_mask_bitmap_ptr(g, prop_name, value, event=None,):
        for p in g.get_psy_members():
            node_value(p, "s_gr_mask_bitmap", value=bpy.data.images.get(value), entry="node_socket", socket_idx=3)
    
    @tag_register()
    def s_gr_mask_bitmap_revert(g, prop_name, value, event=None,):
        for p in g.get_psy_members():
            node_value(p, "s_gr_mask_bitmap", value=not value, entry="node_socket", socket_idx=4)
    
    @tag_register()
    def s_gr_mask_bitmap_color_sample_method(g, prop_name, value, event=None,):
        for p in g.get_psy_members():
            node_value(p, "s_gr_mask_bitmap", value=get_enum_idx(g, prop_name, value,), entry="node_socket", socket_idx=5)
    
    @tag_register()
    def s_gr_mask_bitmap_id_color_ptr(g, prop_name, value, event=None,):
        for p in g.get_psy_members():
            node_value(p, "s_gr_mask_bitmap", value=color_type(value), entry="node_socket", socket_idx=6)
        
    #Materials
    
    @tag_register()
    def s_gr_mask_material_allow(g, prop_name, value, event=None,):
        for p in g.get_psy_members():
            mute_color(p, "Mat Gr Mask", mute=not value,)
            node_link(p, f"RR_FLOAT s_gr_mask_material Receptor", f"RR_FLOAT s_gr_mask_material {bool(value)}",)
    
    @tag_register()
    def s_gr_mask_material_ptr(g, prop_name, value, event=None,):
        for p in g.get_psy_members():
            node_value(p, "s_gr_mask_material", value=bpy.data.materials.get(value), entry="node_socket", socket_idx=2)
    
    @tag_register()
    def s_gr_mask_material_revert(g, prop_name, value, event=None,):
        for p in g.get_psy_members():
            node_value(p, "s_gr_mask_material", value=value, entry="node_socket", socket_idx=3)
        
    #Curves

    @tag_register()
    def s_gr_mask_curve_allow(g, prop_name, value, event=None,):
        for p in g.get_psy_members():
            mute_color(p, "Cur Gr Mask", mute=not value,)
            node_link(p, f"RR_GEO s_gr_mask_curve Receptor", f"RR_GEO s_gr_mask_curve {bool(value)}",)    
    
    @tag_register()
    def s_gr_mask_curve_ptr(g, prop_name, value, event=None,):
        for p in g.get_psy_members():
            node_value(p, "s_gr_mask_curve", value=value, entry="node_socket", socket_idx=1)
    
    @tag_register()
    def s_gr_mask_curve_revert(g, prop_name, value, event=None,):
        for p in g.get_psy_members():
            node_value(p, "s_gr_mask_curve", value=value, entry="node_socket", socket_idx=2)

    #Boolean
    
    @tag_register()
    def s_gr_mask_boolvol_allow(g, prop_name, value, event=None,):
        for p in g.get_psy_members():
            mute_color(p, "Bool Gr Mask", mute=not value,)
            node_link(p, f"RR_GEO s_gr_mask_boolvol Receptor", f"RR_GEO s_gr_mask_boolvol {bool(value)}",)
    
    @tag_register()
    def s_gr_mask_boolvol_coll_ptr(g, prop_name, value, event=None,):
        for p in g.get_psy_members():
            node_value(p, "s_gr_mask_boolvol", value=bpy.data.collections.get(value), entry="node_socket", socket_idx=1)
    
    @tag_register()
    def s_gr_mask_boolvol_revert(g, prop_name, value, event=None,):
        for p in g.get_psy_members():
            node_value(p, "s_gr_mask_boolvol", value=value, entry="node_socket", socket_idx=2)

    #Upward Obstruction

    @tag_register()
    def s_gr_mask_upward_allow(g, prop_name, value, event=None,):
        for p in g.get_psy_members():
            mute_color(p, "Up Gr Mask", mute=not value,)
            node_link(p, f"RR_GEO s_gr_mask_upward Receptor", f"RR_GEO s_gr_mask_upward {bool(value)}",)
    
    @tag_register()
    def s_gr_mask_upward_coll_ptr(g, prop_name, value, event=None,):
        for p in g.get_psy_members():
            node_value(p, "s_gr_mask_upward", value=bpy.data.collections.get(value), entry="node_socket", socket_idx=1)
    
    @tag_register()
    def s_gr_mask_upward_revert(g, prop_name, value, event=None,):
        for p in g.get_psy_members():
            node_value(p, "s_gr_mask_upward", value=value, entry="node_socket", socket_idx=2)
        
    ### Scale
    
    @tag_register()
    def s_gr_scale_master_allow(g, prop_name, value, event=None,):
        for prop in g.get_s_gr_scale_main_features(availability_conditions=False,):
            for p in g.get_psy_members():
                mute_node(p, prop.replace("_allow",""), mute=not value,)
                
    @tag_register()
    def s_gr_scale_boost_allow(g, prop_name, value, event=None,):
        for p in g.get_psy_members():
            mute_color(p, "Group Scale", mute=not value,)
            node_link(p, f"RR_VEC s_gr_scale_boost Receptor", f"RR_VEC s_gr_scale_boost {bool(value)}",)
    
    @tag_register()
    def s_gr_scale_boost_value(g, prop_name, value, event=None,):
        for p in g.get_psy_members():
            node_value(p, "s_gr_scale_boost", value=value, entry="node_socket", socket_idx=1)
            
    @tag_register()
    def s_gr_scale_boost_multiplier(g, prop_name, value, event=None,):
        for p in g.get_psy_members():
            node_value(p, "s_gr_scale_boost", value=value, entry="node_socket", socket_idx=2)
    
    ### Pattern
    
    @tag_register()
    def s_gr_pattern_master_allow(g, prop_name, value, event=None,):        
        for prop in g.get_s_gr_pattern_main_features(availability_conditions=False,):
            for p in g.get_psy_members():
                mute_node(p, prop.replace("_allow",""), mute=not value,)
                
    #Pattern
    
    @tag_register()
    def s_gr_pattern1_allow(g, prop_name, value, event=None,):
        for p in g.get_psy_members():
            mute_color(p, f"Pattern1 Gr", mute=not value,)
            node_link(p, f"RR_VEC s_gr_pattern1 Receptor", f"RR_VEC s_gr_pattern1 {bool(value)}",)
            node_link(p, f"RR_GEO s_gr_pattern1 Receptor", f"RR_GEO s_gr_pattern1 {bool(value)}",)
    
    @tag_register()
    def s_gr_pattern1_texture_ptr(g, prop_name, value, event=None,):
        for p in g.get_psy_members():
            set_texture_ptr(p, "s_gr_pattern1.texture", value)
    
    @tag_register()
    def s_gr_pattern1_color_sample_method(g, prop_name, value, event=None,):
        for p in g.get_psy_members():
            node_value(p, "s_gr_pattern1", value=get_enum_idx(g, prop_name, value,), entry="node_socket", socket_idx=2)
    
    @tag_register()
    def s_gr_pattern1_id_color_ptr(g, prop_name, value, event=None,):
        for p in g.get_psy_members():
            node_value(p, "s_gr_pattern1", value=color_type(value), entry="node_socket", socket_idx=3)
    
    @tag_register()
    def s_gr_pattern1_id_color_tolerence(g, prop_name, value, event=None,):
        for p in g.get_psy_members():
            node_value(p, "s_gr_pattern1", value=value, entry="node_socket", socket_idx=4)
    
    @tag_register()
    def s_gr_pattern1_dist_infl_allow(g, prop_name, value, event=None,):
        for p in g.get_psy_members():
            node_value(p, "s_gr_pattern1", value=value, entry="node_socket", socket_idx=5)
    
    @tag_register()
    def s_gr_pattern1_dist_influence(g, prop_name, value, event=None,):
        for p in g.get_psy_members():
            node_value(p, "s_gr_pattern1", value=value/100, entry="node_socket", socket_idx=6)
    
    @tag_register()
    def s_gr_pattern1_dist_revert(g, prop_name, value, event=None,):
        for p in g.get_psy_members():
            node_value(p, "s_gr_pattern1", value=value, entry="node_socket", socket_idx=7)
    
    @tag_register()
    def s_gr_pattern1_scale_infl_allow(g, prop_name, value, event=None,):
        for p in g.get_psy_members():
            node_value(p, "s_gr_pattern1", value=value, entry="node_socket", socket_idx=8)
    
    @tag_register()
    def s_gr_pattern1_scale_influence(g, prop_name, value, event=None,):
        for p in g.get_psy_members():
            node_value(p, "s_gr_pattern1", value=value/100, entry="node_socket", socket_idx=9)
    
    @tag_register()
    def s_gr_pattern1_scale_revert(g, prop_name, value, event=None,):
        for p in g.get_psy_members():
            node_value(p, "s_gr_pattern1", value=value, entry="node_socket", socket_idx=10)

    # codegen_umask_updatefct(scope_ref=locals(), name="s_pattern1",)
    
    # 88 88b 88 888888 888888 88""Yb 88b 88    db    88
    # 88 88Yb88   88   88__   88__dP 88Yb88   dPYb   88
    # 88 88 Y88   88   88""   88"Yb  88 Y88  dP__Yb  88  .o
    # 88 88  Y8   88   888888 88  Yb 88  Y8 dP""""Yb 88ood8

    #Internal use only, ex: psy.property_run_update() or class.fct() or class.run_update()
    #NOTE: Hum this has nothing to do here? rigth? Should be in particle_systems property class directly

    @tag_register()
    def s_eval_depsgraph(p, prop_name, value, event=None,):
        #set nodetree for eval depsgraph event
        mute_color(p, f"Depsgraph", mute=value!=False,)
        node_link(p, f"s_eval_depsgraph_method", f"s_eval_depsgraph_{str(value).lower()}_eval",)

    @tag_register()
    def s_simulate_final_render(p, prop_name, value, event=None,):
        #mute a node in viewport method evaluation ng to simulate the final render
        for ng in bpy.data.node_groups:
            if (ng.name.startswith(".S Viewport Method MK")):
                if ("s_simulate_final_render" in ng.nodes): #5.5 or above
                    ng.nodes["s_simulate_final_render"].boolean = value
                elif ("temporarily simulate" in ng.nodes): #5.4.1 or above
                    ng.nodes["temporarily simulate"].mute = not value
                elif ("Boolean Math.008" in ng.nodes): #5.4.0 or below
                    ng.nodes["Boolean Math.008"].mute = value
                continue
    

    #  dP""b8 888888 88b 88 888888 88""Yb    db    888888 888888
    # dP   `" 88__   88Yb88 88__   88__dP   dPYb     88   88__
    # Yb  "88 88""   88 Y88 88""   88"Yb   dP__Yb    88   88""
    #  YboodP 888888 88  Y8 888888 88  Yb dP""""Yb   88   888888

    #Generate Dict at parsetime

    #list all update functions of this class, by looking at tag
    UpdateFcts = { k:v for k,v in locals().items() if (callable(v) and hasattr(v,"register_tag")) }

    #generated update dictionary
    UpdatesDict = {}
    for k,v in UpdateFcts.items():
        
        #no need to generate fcts?
        if (not hasattr(v,"generator_nbr")):
            if (k not in UpdatesDict):
                UpdatesDict[k]=v
            continue            
    
        #generate a fct from given name convention?
        if (("XX" in k) and (0<v.generator_nbr<100)):
            for i in range(v.generator_nbr):
                _k = k.replace("XX",f"{i+1:02}")
                if (_k not in UpdatesDict):
                    UpdatesDict[_k]=v
            continue
        elif (("X" in k) and (0<v.generator_nbr<10)):
            for i in range(v.generator_nbr):
                _k = k.replace("X",f"{i+1}")
                if (_k not in UpdatesDict):
                    UpdatesDict[_k]=v
            continue

        #else raise error
        raise Exception(f"For generator, please use X or XX convention, make sure {v.generator_nbr} number can fit")

    #    db     dP""b8  dP""b8 888888 .dP"Y8 .dP"Y8
    #   dPYb   dP   `" dP   `" 88__   `Ybo." `Ybo."
    #  dP__Yb  Yb      Yb      88""   o.`Y8b o.`Y8b
    # dP""""Yb  YboodP  YboodP 888888 8bodP' 8bodP'

    #access to UpdatesDict from outer modules:

    @classmethod
    def run_update(cls, p, prop_name, value, event=None,):
        """run update function equivalence from given propname, return True if propname found else False"""

        fct = cls.UpdatesDict.get(prop_name)

        if (fct is None):
            print(f"ERROR: UpdatesRegistry.run_update(): Property '{prop_name}' of system '{p.name}' not in UpdatesDict class")
            return False

        dprint(f"PROP_FCT: UpdatesRegistry.run_update('{p.name}','{prop_name}',{value})", depsgraph=True)
        fct(p, prop_name, value, event=event,)

        return True


#   .oooooo.   oooo
#  d8P'  `Y8b  `888
# 888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
# 888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
# 888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
# `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#  `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'


classes = ()