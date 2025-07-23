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
#  ooooo   ooooo                             .o8  oooo
#  `888'   `888'                            "888  `888
#   888     888   .oooo.   ooo. .oo.    .oooo888   888   .ooooo.  oooo d8b
#   888ooooo888  `P  )88b  `888P"Y88b  d88' `888   888  d88' `88b `888""8P
#   888     888   .oP"888   888   888  888   888   888  888ooo888  888
#   888     888  d8(  888   888   888  888   888   888  888    .o  888
#  o888o   o888o `Y888""8o o888o o888o `Y8bod88P" o888o `Y8bod8P' d888b
# 
#####################################################################################################

#find hereby callbacks and other updates function running in the background

#CRASH WARNING!! be very carreful here!!! 
#https://docs.blender.org/api/current/bpy.app.handlers.html?highlight=render_cancel#note-on-altering-data

import bpy

from bpy.app.handlers import persistent
from mathutils import Vector

from .. utils.extra_utils import dprint


# oooooooooo.                                                                          oooo
# `888'   `Y8b                                                                         `888
#  888      888  .ooooo.  oo.ooooo.   .oooo.o  .oooooooo oooo d8b  .oooo.   oo.ooooo.   888 .oo.
#  888      888 d88' `88b  888' `88b d88(  "8 888' `88b  `888""8P `P  )88b   888' `88b  888P"Y88b
#  888      888 888ooo888  888   888 `"Y88b.  888   888   888      .oP"888   888   888  888   888
#  888     d88' 888    .o  888   888 o.  )88b `88bod8P'   888     d8(  888   888   888  888   888
# o888bood8P'   `Y8bod8P'  888bod8P' 8""888P' `8oooooo.  d888b    `Y888""8o  888bod8P' o888o o888o
#                          888                d"     YD                      888
#                         o888o               "Y88888P'                     o888o

#lauch function on each depsgraph interaction


def is_depsgraph_check_conditions():
    """check if the current conditions are good, let's not overrun blender with depsgraph checks and functions.."""
    
    #don't do check if user not in view3d or outliner editor
    area = bpy.context.area
    if (not area):
        return False
    if (area.type not in {'VIEW_3D','OUTLINER',}):
        return False
    
    #don't do check if not in object mode
    if (bpy.context.mode!='OBJECT'):
        return False
    
    #don't do check if user is currently using common modal operators
    win = bpy.context.window
    if (win):
        opname = [op.bl_idname for op in win.modal_operators]
        if ("TRANSFORM_OT_" in opname):
            return False
    
    return True

@persistent
def scatter5_depsgraph(scene,desp):
    """Handler function executed on each depsgraph post update signal"""
    #WARNING: we need to be carreful to not slowdown blender in this function. only light checks when possible, rare heavy actions..
    
    from . overseer import Observer, scatter_items_cleanup
    
    from ... __init__ import addon_prefs

    from .. scattering.emitter import ensure_emitter_pin_mode_synchronization, handler_f_surfaces_cleanup
    from .. scattering.update_factory import update_camera_nodegroup
    from .. scattering.update_factory import update_manual_uuid_surfaces
    from .. ui.ui_notification import check_for_notifications
    
    #debug print
    dprint("HANDLER: scatter5_depsgraph(): Doing Checks...", depsgraph=True)

    allow = is_depsgraph_check_conditions()
    
    #Overseer module, observing what user is doing in his file to act accordingly
    if (allow):
        if ("AllowObserver"):
                
            #oberved notable event user did with scatter-item (psy/emitter) and the scene, or else..
            changes = Observer.observe_scatter_items_changes()
            
            #& take action according to what happened
            if (changes):
                scatter_items_cleanup(what_happened=changes)
                
            #if overseer saw an emitter getting deleted from thin air, we recalculate notifications, because might create orphans
            if ('EmitterTrackerCleansed' in changes):
                check_for_notifications(checks={"T_ORPHAN":True},)

    #check if f_surface op settings? see if obj has been deleted 
    handler_f_surfaces_cleanup()

    #update emitter pointer if in pin mode
    if (addon_prefs().emitter_method=="pin"):
        ensure_emitter_pin_mode_synchronization()
        
    #check for manual mode uuid if multisurfaces
    if (allow):
        try:
            update_manual_uuid_surfaces()
        except Exception as e:
            print("ERROR: scatter5_depsgraph().update_manual_uuid_surfaces(): Couldn't update surface uuid")
            print(str(e))

    #special option: hide system(s) when emitter is also hidden
    #auto_hide_psy_when_emitter_hidden()

    #update is_rendered_view nodegroup
    shading_type_callback()

    #update active camera nodegroup
    update_camera_nodegroup(force_update=False) #force_update=True strictly forbidden in this context, could create a feedback loop
    
    return None


#NOTE: update render/frame pre+post are needed in order to avoid "laggy/delayed" effect

# ooooooooo.                               .o8                     
# `888   `Y88.                            "888                     
#  888   .d88'  .ooooo.  ooo. .oo.    .oooo888   .ooooo.  oooo d8b 
#  888ooo88P'  d88' `88b `888P"Y88b  d88' `888  d88' `88b `888""8P 
#  888`88b.    888ooo888  888   888  888   888  888ooo888  888     
#  888  `88b.  888    .o  888   888  888   888  888    .o  888     
# o888o  o888o `Y8bod8P' o888o o888o `Y8bod88P" `Y8bod8P' d888b    

#lauch function on pre/post final render operation


def ensure_visibility_states():
    """values of the visibility states might be buggy, need a refresh signal"""

    #for all psys, we ensure that some problematic properties are up to date.. 
    #ugly fix, we don't understand why, sometimes the values of the properties below are not synchronized with their nodetrees
    for p in bpy.context.scene.scatter5.get_all_psys(search_mode="all"):
        #of valid systems only, as we might encounter some psys that needs their full nodetree to be updated
        if p.is_valid_addon_version():
            p.property_nodetree_refresh("s_visibility_view_viewport_method",)
            p.property_nodetree_refresh("s_visibility_maxload_viewport_method",)
            p.property_nodetree_refresh("s_visibility_facepreview_viewport_method",)
            p.property_nodetree_refresh("s_visibility_cam_viewport_method",)
            p.property_nodetree_refresh("s_display_viewport_method",)
        continue

    return None


#Informal Singleton
IS_FINAL_RENDER = False


@persistent
def scatter5_render_init(scene,desp):
    """Handler function on each final F12 render initialization"""
    
    global IS_FINAL_RENDER
    IS_FINAL_RENDER = True

    #debug print
    dprint("HANDLER: scatter5_render_init(): updating singleton & ensure_visibility_states()", depsgraph=True)
    
    #headless mode?
    if (bpy.app.background or (bpy.context.window_manager is None)): 
        print("WARNING: we advise `scene.render.use_lock_interface` to be `True` while running blender headlessly, as it might create inaccurate result otherwise. We enabled the settings for you.")
        scene.render.use_lock_interface = True

    #make sure visibility states are ok
    ensure_visibility_states()
    
    return None


@persistent
def scatter5_render_pre(scene,desp):
    """Handler function on each final F12 render pre"""
    
    global IS_FINAL_RENDER
    IS_FINAL_RENDER = True

    #debug print
    dprint("HANDLER: scatter5_render_pre(): updating singleton", depsgraph=True)
        
    return None


@persistent
def scatter5_render_post(scene,desp):
    """Handler function on each final F12 post process"""

    # #debug print
    # dprint("HANDLER: scatter5_render_post()", depsgraph=True)
    
    return None


@persistent
def scatter5_render_cancel(scene,desp): 
    """Handler function on each final F12 render cancelation"""

    global IS_FINAL_RENDER
    IS_FINAL_RENDER = False

    #debug print
    dprint("HANDLER: scatter5_render_cancel(): updating singleton", depsgraph=True)
    
    return None


@persistent
def scatter5_render_complete(scene,desp):
    """Handler function on each final F12 render completion"""

    global IS_FINAL_RENDER
    IS_FINAL_RENDER = False

    #debug print
    dprint("HANDLER: scatter5_render_init(): updating singleton", depsgraph=True)

    return None


# oooooooooooo                                                  
# `888'     `8                                                  
#  888         oooo d8b  .oooo.   ooo. .oo.  .oo.    .ooooo.    
#  888oooo8    `888""8P `P  )88b  `888P"Y88bP"Y88b  d88' `88b   
#  888    "     888      .oP"888   888   888   888  888ooo888   
#  888          888     d8(  888   888   888   888  888    .o   
# o888o        d888b    `Y888""8o o888o o888o o888o `Y8bod8P'   

#lauch function on each frame interaction, when animation is playing or scrubbing


def get_plugin_animated_props():
    """find scatter5 properties that found in emitter animation data"""

    dprint("FCT: get_plugin_animated_props(): Checking for animated props..")
    
    global IS_FINAL_RENDER

    #make sure keyframe also works when rendering & lock option
    if (IS_FINAL_RENDER and bpy.context.scene.render.use_lock_interface):
          scene = bpy.context.evaluated_depsgraph_get().scene
    else: scene = bpy.context.scene

    frame = scene.frame_current

    #gather supported animated plugin properties
    keyable_list = []
    keyable_list += (scene.scatter5.get_all_emitters(search_mode="all"))
    keyable_list += ([ng for ng in bpy.data.node_groups if ng.name.startswith(".TEXTURE")])
    
    #gather properties to be updated 

    props = {} #(id_data,propname) : (keyword, value)

    def store_prop(keyable, fc, fctype):

        nonlocal props

        data_path = fc.data_path
        propname = data_path.split(".")[-1]

        #find id_data and keyword information depending on data type

        # if (type(keyable) is bpy.types.Scene):
        #     keyword = "Scene"
        #     id_data = keyable.scatter5
        #
        # elif (type(keyable) is bpy.types.Text):
        #     keyword = "Text"
        #     id_data = keyable.scatter5

        if (type(keyable) is bpy.types.GeometryNodeTree):
            keyword = "GeometryNodeTree"
            id_data = keyable.scatter5.texture
        
        elif (type(keyable) is bpy.types.Object):

            if ("particle_systems" in data_path):
                
                keyword = "ScatterSystem"
                idx = int(data_path.split("]")[0].split("[")[-1])
                id_data = None if (len(keyable.scatter5.particle_systems)<=idx) else keyable.scatter5.particle_systems[idx]
                                
                #trick BUGFIX for animation data on psys linked to idx.. data_path is based on index. it's crap.. we need to leave some trace off psy uuid
                if ("Geo-Scatter UuidTrack Initialized" not in fc.modifiers):
                    
                    if (id_data is None):
                        fc.data_path = "invalid"
                        return None
                    
                    mod = fc.modifiers.new('GENERATOR')
                    mod.mute,mod.show_expanded = True,False
                    mod.name = "Geo-Scatter UuidTrack Initialized"
                    
                    mod = fc.modifiers.new('GENERATOR')
                    mod.mute,mod.show_expanded = True,False
                    mod.name = f"uuid:{id_data.uuid}"
                
                #& fix idx when idx has changed, or if del
                else:
                    uuid = 0
                    for mod in fc.modifiers:
                        if mod.name.startswith("uuid:"):
                            uuid = int(mod.name.replace("uuid:",""))
                    p = bpy.context.scene.scatter5.get_psy_by_uuid(uuid)
                    if (p is None):
                        fc.data_path = "scatter_deleted"
                        for mod in reversed(fc.modifiers):
                            fc.modifiers.remove(mod)
                        return None
                    elif (p!=id_data):
                        for i,psy in enumerate(keyable.scatter5.particle_systems):
                            if (p==psy):
                                fc.data_path=fc.data_path.replace(f"particle_systems[{idx}]",f"particle_systems[{i}]")
                                id_data = p
                                #give it a kick
                                if (fctype=="Driver"):
                                    fc.driver.expression = fc.driver.expression
                                break
                            
            elif ("particle_groups" in data_path):
                
                keyword = "ScatterGroup"
                
                #unfortunately particle_groups don't have uuid, so.. can't fix this issue
                idx = int(data_path.split("]")[0].split("[")[-1])
                if (len(keyable.scatter5.particle_groups)<=idx):
                    return None
                
                id_data = keyable.scatter5.particle_groups[idx]

        #evaluate the driver/keyframe value
        match fctype:
            case 'Driver': value = keyable.path_resolve(fc.data_path) #evaluate() don't work for some reasons..
            case 'Action': value = fc.evaluate(frame)

        #ok, if our props is already stored, it means we are dealing a vector value.. 
        #blender is separating vector values back to floats, we need to reassemble the vector values in order to update our props..
        if (id_data,propname) in props.keys():
            #don't ask me about this code below, it seems that blender is quite cryptic on how it evaluate values.. sometimes float.. sometimes vectors.. weird..
            try:
                current_value = props[(id_data,propname)][1]            
                if (type(current_value) in (float,int)):
                      value = Vector((current_value,value,0))
                else: value = Vector((current_value[0],current_value[1],value))
            except Exception as e:
                dprint("ERROR: get_plugin_animated_props().store_prop() while handling vector value:\n",e)

        #zip values
        props[(id_data,propname)] = (keyword, value)
                    
        return None

    #loop all keyable
    for keyable in [k for k in keyable_list if k and k.animation_data]:
        
        #drivers
        if (keyable.animation_data.drivers):
            for fc in keyable.animation_data.drivers:
                if (fc.data_path.startswith("scatter5")):
                    
                    if (IS_FINAL_RENDER and bpy.context.scene.render.use_lock_interface):
                        print("WARNING: get_plugin_animated_props(): Driver animation of our plugin-settings are not supported with the lock interface option of blender enabled.")
                        
                    try: store_prop(keyable, fc, "Driver",)
                    except Exception as e:
                        print("ERROR: get_plugin_animated_props(): Driver support:\n",e)

        #keyframes
        if (keyable.animation_data.action):
            for fc in keyable.animation_data.action.fcurves:
                if (fc.data_path.startswith("scatter5")):
                    
                    try: store_prop(keyable, fc, "Action",)
                    except Exception as e:
                        print("ERROR: get_plugin_animated_props(): Keyframe support:\n",e)

    return props


def plugin_properties_animation_data_support():

    for k,v in get_plugin_animated_props().items():
        id_data, prop = k
        keyword, value = v

        #update signal is not sent automatically.. need to force it..
        if (keyword in ("ScatterSystem","ScatterGroup",)):
              id_data.property_run_update(prop, value,)
        else: setattr(id_data, prop, value,)
        
        dprint(f"HANDLER: plugin_properties_animation_data_support(): PropsFound! Updating: (prop={prop} keyword={keyword}, value={value})",)
        continue
    
    return None 


@persistent
def scatter5_frame_pre(scene,desp):
    """Handler function on each frame animation pre"""
    #WARNING: we need to be carreful to not slowdown blender in this function. only light checks when possible, rare heavy actions..
    #REMARK: desp always none? why?
    
    from .. scattering.update_factory import update_camera_nodegroup
    
    global IS_FINAL_RENDER
 
    #viewport optimization: slow camera move, even if all are hidden!
    if (not IS_FINAL_RENDER):
        if all(not p.scatter_obj.visible_get() for p in scene.scatter5.get_all_psys(search_mode="active_view_layer")):
            dprint(f"HANDLER: scatter5_frame_post(): Cancel: All Psys Are Hidden", depsgraph=True)
            return None

    #debug print
    dprint(f"HANDLER: scatter5_frame_pre() Doing Checks... (is_final_render:{IS_FINAL_RENDER})", depsgraph=True)
    
    #update active camera nodegroup, we need to evaluate depsgraph and also send scene evaluation
    update_camera_nodegroup(force_update=True, scene=scene, render=IS_FINAL_RENDER, locked_interface=scene.render.use_lock_interface,)

    #partial manual keyframe support 
    plugin_properties_animation_data_support()

    return None


@persistent
def scatter5_frame_post(scene,desp): 
    """Handler function on each frame animation post"""
    #WARNING: we need to be carreful to not slowdown blender in this function. only light checks when possible, rare heavy actions..

    from .. scattering.update_factory import update_camera_nodegroup
    from .. handlers.overseer import Observer, scatter_items_cleanup

    global IS_FINAL_RENDER

    dprint(f"HANDLER: scatter5_frame_post(): Doing Checks... (is_final_render:{IS_FINAL_RENDER})", depsgraph=True)
    
    #Overseer module, observing what user is doing in his file to act accordingly
    if ("AllowObserver"):
            
        #scene changes can be detected only from frame handler sadly.. depsgraph don't seem to picked up that information when user is using scene add operator
        scene_changes = Observer.observe_scenes_changes()
        
        #and act if changes found
        if (scene_changes):
            
            #re-oberved if this scene change added/removed scatter-item (psy/emitter)
            items_changes = Observer.observe_scatter_items_changes()
            
            #& take action according to what happened
            if (items_changes):
                changes = items_changes|scene_changes
                scatter_items_cleanup(what_happened=changes)
            
    #viewport optimization: slow camera move, even if all are hidden!
    if (not IS_FINAL_RENDER):
        if all(not p.scatter_obj.visible_get() for p in scene.scatter5.get_all_psys(search_mode="active_view_layer")):
            dprint(f"HANDLER: scatter5_frame_post() Cancel: All Psys Are Hidde", depsgraph=True)
            return None
    
    #update active camera nodegroup, we need to evaluate depsgraph and also send scene evaluation
    update_camera_nodegroup(force_update=True, scene=scene, render=IS_FINAL_RENDER, locked_interface=scene.render.use_lock_interface,)

    #partial manual keyframe support 
    plugin_properties_animation_data_support()
        
    return None


#   .oooooo.             oooo  oooo   .o8                           oooo
#  d8P'  `Y8b            `888  `888  "888                           `888
# 888           .oooo.    888   888   888oooo.   .oooo.    .ooooo.   888  oooo
# 888          `P  )88b   888   888   d88' `88b `P  )88b  d88' `"Y8  888 .8P'
# 888           .oP"888   888   888   888   888  .oP"888  888        888888.
# `88b    ooo  d8(  888   888   888   888   888 d8(  888  888   .o8  888 `88b.
#  `Y8bood8P'  `Y888""8o o888o o888o  `Y8bod8P' `Y888""8o `Y8bod8P' o888o o888o


# .dP"Y8 88  88    db    8888b.  88 88b 88  dP""b8     8b    d8  dP"Yb  8888b.  888888
# `Ybo." 88  88   dPYb    8I  Yb 88 88Yb88 dP   `"     88b  d88 dP   Yb  8I  Yb 88__
# o.`Y8b 888888  dP__Yb   8I  dY 88 88 Y88 Yb  "88     88YbdP88 Yb   dP  8I  dY 88""
# 8bodP' 88  88 dP""""Yb 8888Y"  88 88  Y8  YboodP     88 YY 88  YbodP  8888Y"  888888

def set_overlay(boolean):
    """will toggle off overlay while in rendered view""" 

    from .. utils.extra_utils import all_3d_viewports
    
    #init static variable
    _f = set_overlay
    if (not hasattr(_f,"to_restore")):
        _f.to_restore = []

    match boolean:
            
        case True: #== restore

            for space in _f.to_restore:
                try: space.overlay.show_overlays = True
                except: pass #perhaps space do not exists anymore so we need to be careful 
            _f.to_restore = []

        case False:

            for space in all_3d_viewports():
                if (space.shading.type=="RENDERED"):
                    if space.overlay.show_overlays: 
                        _f.to_restore.append(space)
                        space.overlay.show_overlays = False

    return None 


SHADING_TYPE_OWNER = object()

def shading_type_callback(*args):
    """update rendered view nodegroup""" 

    from ... __init__ import blend_prefs
    from .. utils.extra_utils import is_rendered_view
    from .. scattering.update_factory import update_is_rendered_view_nodegroup
    
    #check for rendered view
    is_rdr = is_rendered_view()

    dprint(f"MSGBUS: shading_type_callback(): is_rdr={is_rdr}", depsgraph=True)

    #set/reset overlay
    scat_data = blend_prefs()
    if (scat_data.update_auto_overlay_rendered):
        set_overlay(not is_rdr)

    #update is rendered view nodegroup
    update_is_rendered_view_nodegroup(value=is_rdr)

    return None 

# 8b    d8  dP"Yb  8888b.  888888      dP""b8    db    88     88     88""Yb    db     dP""b8 88  dP
# 88b  d88 dP   Yb  8I  Yb 88__       dP   `"   dPYb   88     88     88__dP   dPYb   dP   `" 88odP
# 88YbdP88 Yb   dP  8I  dY 88""       Yb       dP__Yb  88  .o 88  .o 88""Yb  dP__Yb  Yb      88"Yb
# 88 YY 88  YbodP  8888Y"  888888      YboodP dP""""Yb 88ood8 88ood8 88oodP dP""""Yb  YboodP 88  Yb

MODE_OWNER = object()

def mode_callback(*args):
    """message bus rendered view check function""" 

    dprint("MSGBUS: mode_callback()", depsgraph=True)

    #init static variable
    _f = mode_callback
    if (not hasattr(_f,"were_editing")):
        _f.were_editing = [] #keep track of last objects edited
    if (not hasattr(_f,"last_mode")):
        _f.last_mode = "OBJECT" #keep track of blender mode states

    #Scatter5 track surface area of each objects

    current_mode = bpy.context.object.mode

    #if recently was in edit mode, and 
    if ((_f.last_mode=="EDIT") and (current_mode=="OBJECT")):
        dprint("MSGBUS: mode_callback(): Swapped back to object mode, Launching: objects.scatter5.estimate_square_area()", depsgraph=True)
        for o_name in _f.were_editing:
            o = bpy.data.objects.get(o_name)
            if (o is not None):
                o.scatter5.estimate_square_area()

    _f.last_mode = str(current_mode)
    if (current_mode=="EDIT"):
        _f.were_editing = [o.name for o in bpy.context.scene.objects if (o.mode=="EDIT")]

    return None 

# 888888 88""Yb    db    8b    d8 888888     88""Yb 88""Yb  dP"Yb  88""Yb      dP""b8 88  88    db    88b 88  dP""b8 888888
# 88__   88__dP   dPYb   88b  d88 88__       88__dP 88__dP dP   Yb 88__dP     dP   `" 88  88   dPYb   88Yb88 dP   `" 88__
# 88""   88"Yb   dP__Yb  88YbdP88 88""       88"""  88"Yb  Yb   dP 88"""      Yb      888888  dP__Yb  88 Y88 Yb  "88 88""
# 88     88  Yb dP""""Yb 88 YY 88 888888     88     88  Yb  YbodP  88          YboodP 88  88 dP""""Yb 88  Y8  YboodP 888888

CLIP_START_OWNER = object()
CLIP_END_OWNER = object()

def frame_clip_callback(*args):
    """message bus rendered view check function""" 

    from .. scattering.update_factory import update_frame_start_end_nodegroup

    dprint("MSGBUS: update_frame_start_end_nodegroup(): Changed start/end properties: Checking if needs to update ng properties..", depsgraph=True)

    update_frame_start_end_nodegroup()

    return None 


# oooooooooo.  oooo                              .o8                          ooooo                                  .o8  
# `888'   `Y8b `888                             "888                          `888'                                 "888  
#  888     888  888   .ooooo.  ooo. .oo.    .oooo888   .ooooo.  oooo d8b       888          .ooooo.   .oooo.    .oooo888  
#  888oooo888'  888  d88' `88b `888P"Y88b  d88' `888  d88' `88b `888""8P       888         d88' `88b `P  )88b  d88' `888  
#  888    `88b  888  888ooo888  888   888  888   888  888ooo888  888           888         888   888  .oP"888  888   888  
#  888    .88P  888  888    .o  888   888  888   888  888    .o  888           888       o 888   888 d8(  888  888   888  
# o888bood8P'  o888o `Y8bod8P' o888o o888o `Y8bod88P" `Y8bod8P' d888b         o888ooooood8 `Y8bod8P' `Y888""8o `Y8bod88P" 

#on loading blender files, new file, ect.. used to launch callback, as they won't stick when changing files


@persistent
def scatter5_load_post(scene,desp):
    """Handler function when user is loading a file"""

    from . overseer import Observer
    
    from ... __init__ import blend_prefs
    from .. ui.ui_notification import check_for_notifications
    from .. ui.ui_system_list import ensure_particle_interface_items
    
    #debug print
    dprint(f"HANDLER: scatter5_load_post(): Loading new .blend file: Running few functions..", depsgraph=True)
    
    #make sure bpy.data.texts['.Geo-Scatter Settings'] exists, create if doesn't
    scat_data = blend_prefs()
    
    #initialize blendfile_uuid if not already for this blendfile
    _ = scat_data.blendfile_uuid

    #re-obseve new scene
    Observer.initiate()

    #need to add message bus on each blender load as well
    register_msgbusses()

    #check for warning messages
    check_for_notifications()

    #rebuild library, because biome library is stored in bpy.contewt.window_manager, will need to reload
    bpy.ops.scatter5.reload_biome_library()

    #make sure visibility states are ok
    ensure_visibility_states()
    
    #make sure all scatter systems gui is ok
    ensure_particle_interface_items()
    
    #NO LONGER AN ISSUE?
    #correct potential bug, unconnected nodes!
    # from .. scattering.update_factory import ensure_buggy_links
    # ensure_buggy_links()

    return None


# oooooooooo.  oooo                              .o8                           .oooooo..o
# `888'   `Y8b `888                             "888                          d8P'    `Y8
#  888     888  888   .ooooo.  ooo. .oo.    .oooo888   .ooooo.  oooo d8b      Y88bo.       .oooo.   oooo    ooo  .ooooo.
#  888oooo888'  888  d88' `88b `888P"Y88b  d88' `888  d88' `88b `888""8P       `"Y8888o.  `P  )88b   `88.  .8'  d88' `88b
#  888    `88b  888  888ooo888  888   888  888   888  888ooo888  888               `"Y88b  .oP"888    `88..8'   888ooo888
#  888    .88P  888  888    .o  888   888  888   888  888    .o  888          oo     .d8P d8(  888     `888'    888    .o
# o888bood8P'  o888o `Y8bod8P' o888o o888o `Y8bod88P" `Y8bod8P' d888b         8""88888P'  `Y888""8o     `8'     `Y8bod8P'

#right after saving a .blend

@persistent 
def scatter5_save_post(scene,desp):
    """Handler function when user is saving a file"""

    #debug print
    dprint(f"HANDLER: scatter5_save_post(): Saved blendfile, updating versionning info in properties..", depsgraph=True)

    #keep track of systems blender versions
    for p in bpy.context.scene.scatter5.get_all_psys(search_mode="all"):
        if (p.blender_version!=bpy.app.version_string):
            p.blender_version = bpy.app.version_string
        continue
        
    return None 


# ooooooooo.   oooo                          o8o                   ooooo                          .             oooo  oooo
# `888   `Y88. `888                          `"'                   `888'                        .o8             `888  `888
#  888   .d88'  888  oooo  oooo   .oooooooo oooo  ooo. .oo.         888  ooo. .oo.    .oooo.o .o888oo  .oooo.    888   888
#  888ooo88P'   888  `888  `888  888' `88b  `888  `888P"Y88b        888  `888P"Y88b  d88(  "8   888   `P  )88b   888   888
#  888          888   888   888  888   888   888   888   888        888   888   888  `"Y88b.    888    .oP"888   888   888
#  888          888   888   888  `88bod8P'   888   888   888        888   888   888  o.  )88b   888 . d8(  888   888   888
# o888o        o888o  `V88V"V8P' `8oooooo.  o888o o888o o888o      o888o o888o o888o 8""888P'   "888" `Y888""8o o888o o888o
#                                d"     YD
#                                "Y88888P'


def on_plugin_installation():
    """is executed either right after plugin installation (when user click on install checkbox),
    or when blender is booting, it will also load plugin"""
        
    def wait_restrict_state_timer():
        """wait until bpy.context is not bpy_restrict_state._RestrictContext anymore
            BEWARE: this is a function from a bpy.app timer, context is trickier to handle"""
        
        dprint(f"HANDLER: on_plugin_installation(): Still in restrict state?",)

        #don't do anything until context is cleared out
        if (str(bpy.context).startswith("<bpy_restrict_state")): 
            return 0.01
        
        dprint(f"HANDLER: on_plugin_installation(): Loading Plugin: Running few functions..",)
        
        from . overseer import Observer
        
        from ... __init__ import blend_prefs
        from .. ui.ui_notification import check_for_notifications
        from .. ui.ui_system_list import ensure_particle_interface_items
        from .. scattering.update_factory import update_manual_uuid_surfaces
        
        #make sure bpy.data.texts['.Geo-Scatter Settings'] exists, create if doesn't
        scat_data = blend_prefs()
        
        #initialize blendfile_uuid if not already for this blendfile
        _ = scat_data.blendfile_uuid
            
        #make sure crutial factory properties are enabled, if not, prolly because of an unexpected crash
        if (not scat_data.factory_event_listening_allow):
            scat_data.factory_event_listening_allow = True
        if (not scat_data.factory_active):
            scat_data.factory_active = True
        
        #initiate tracker system
        Observer.initiate()
        
        #check for warning messages
        check_for_notifications()

        #make sure manual mode uuid are accurate (rare bugfix)
        update_manual_uuid_surfaces(force_update=True)

        #make sure visibility states are ok
        ensure_visibility_states()

        #make sure all scatter systems gui is ok
        ensure_particle_interface_items()

        return None

    bpy.app.timers.register(wait_restrict_state_timer)
    
    return None

#  .oooooo..o                      oooo   o8o               .        ooooo     ooo                  .o8
# d8P'    `Y8                      `888   `"'             .o8        `888'     `8'                 "888
# Y88bo.      oooo    ooo  .oooo.o  888  oooo   .oooo.o .o888oo       888       8  oo.ooooo.   .oooo888
#  `"Y8888o.   `88.  .8'  d88(  "8  888  `888  d88(  "8   888         888       8   888' `88b d88' `888
#      `"Y88b   `88..8'   `"Y88b.   888   888  `"Y88b.    888         888       8   888   888 888   888
# oo     .d8P    `888'    o.  )88b  888   888  o.  )88b   888 .       `88.    .8'   888   888 888   888
# 8""88888P'      .8'     8""888P' o888o o888o 8""888P'   "888"         `YbodP'     888bod8P' `Y8bod88P"
#             .o..P'                                                                888
#             `Y8P'                                                                o888o

def on_particle_interface_interaction_handler():
    """when user is interacting with system lists"""
    
    from .. scattering.update_factory import update_transfer_attrs_nodegroup
    
    #debug print
    dprint(f"HANDLER: on_particle_interface_interaction_handler(): User interacted with lister, we do some checks..", depsgraph=True)

    #make sure inner properties that should update via callback are updated
    frame_clip_callback()
    
    #update attr transfers, used by some distribution methods
    for p in bpy.context.scene.scatter5.get_all_psys(search_mode="active_view_layer"):
        update_transfer_attrs_nodegroup(p)
        
    from ..ui.ui_notification import check_for_notifications
    check_for_notifications(checks={"T_ORPHAN":True},)
    
    return None

# ooooooooo.                        
# `888   `Y88.                      
#  888   .d88'  .ooooo.   .oooooooo 
#  888ooo88P'  d88' `88b 888' `88b  
#  888`88b.    888ooo888 888   888  
#  888  `88b.  888    .o `88bod8P'  
# o888o  o888o `Y8bod8P' `8oooooo.  
#                        d"     YD  
#                        "Y88888P'  
                                  
                                  
def get_running_handlers():
    """return a list of handler stored in .blend"""

    return_list = []
    
    for oh in bpy.app.handlers:
        try:
            for h in oh:
                return_list.append(h)
        except: pass
    
    return return_list


def register_handlers():
    """append all our plugin handlers"""
    
    handlers = get_running_handlers()
        
    #depsgraph
    if (scatter5_depsgraph not in handlers):
        bpy.app.handlers.depsgraph_update_post.append(scatter5_depsgraph)

    #frame change
    if (scatter5_frame_pre not in handlers):
        bpy.app.handlers.frame_change_pre.append(scatter5_frame_pre)
    if (scatter5_frame_post not in handlers):
        bpy.app.handlers.frame_change_post.append(scatter5_frame_post)
        
    #render
    if (scatter5_render_init not in handlers):
        bpy.app.handlers.render_init.append(scatter5_render_init)
    if (scatter5_render_pre not in handlers):
        bpy.app.handlers.render_pre.append(scatter5_render_pre)
    if (scatter5_render_post not in handlers):
        bpy.app.handlers.render_post.append(scatter5_render_post)
    if (scatter5_render_cancel not in handlers):
        bpy.app.handlers.render_cancel.append(scatter5_render_cancel)
    if (scatter5_render_complete not in handlers):
        bpy.app.handlers.render_complete.append(scatter5_render_complete)

    #on blend open 
    if (scatter5_load_post not in handlers):
        bpy.app.handlers.load_post.append(scatter5_load_post)

    #on blend save 
    if (scatter5_save_post not in handlers):
        bpy.app.handlers.save_post.append(scatter5_save_post)
    
    return None

def unregister_handlers():
    """remove all our plugin handlers"""

    #remove all handlers 
    for h in get_running_handlers():

        #depsgraph
        if (h.__name__=="scatter5_depsgraph"):
            bpy.app.handlers.depsgraph_update_post.remove(h)

        #frame change
        elif (h.__name__=="scatter5_frame_pre"):
            bpy.app.handlers.frame_change_pre.remove(h)
        elif (h.__name__=="scatter5_frame_post"):
            bpy.app.handlers.frame_change_post.remove(h)

        #render 
        elif (h.__name__=="scatter5_render_init"):
            bpy.app.handlers.render_init.remove(h)
        elif (h.__name__=="scatter5_render_pre"):
            bpy.app.handlers.render_pre.remove(h)
        elif (h.__name__=="scatter5_render_post"):
            bpy.app.handlers.render_post.remove(h)
        elif (h.__name__=="scatter5_render_cancel"):
            bpy.app.handlers.render_cancel.remove(h)
        elif (h.__name__=="scatter5_render_complete"):
            bpy.app.handlers.render_complete.remove(h)
            
        #on blend open 
        elif (h.__name__=="scatter5_load_post"):
            bpy.app.handlers.load_post.remove(h)

        #on blend save 
        elif (h.__name__=="scatter5_save_post"):
            bpy.app.handlers.save_post.remove(h)

        continue
    
    return None


def register_msgbusses():
    """subscribe our plugin msgbus"""
    
    #TODO, better msgbus registration, need to check if not added already perhaps??? unsure if this can be done, msgbus only has a single owner
        
    bpy.msgbus.subscribe_rna(
        key=(bpy.types.View3DShading, "type"), # not accurate signal enough, need both msgbus & depsgraph
        owner=SHADING_TYPE_OWNER,
        notify=shading_type_callback,
        args=(None,),
        options={"PERSISTENT"},
        )
    bpy.msgbus.subscribe_rna(
        key=(bpy.types.Object, "mode"),
        owner=MODE_OWNER,
        notify=mode_callback,
        args=(None,),
        options={"PERSISTENT"},
        )
    bpy.msgbus.subscribe_rna(
        key=(bpy.types.Scene, "frame_start"),
        owner=CLIP_START_OWNER,
        notify=frame_clip_callback,
        args=(None,),
        options={"PERSISTENT"},
        )
    bpy.msgbus.subscribe_rna(
        key=(bpy.types.Scene, "frame_end"),
        owner=CLIP_END_OWNER,
        notify=frame_clip_callback,
        args=(None,),
        options={"PERSISTENT"},
        )

def unregister_msgbusses():
    """clear our plugin msgbus"""

    bpy.msgbus.clear_by_owner(SHADING_TYPE_OWNER)
    bpy.msgbus.clear_by_owner(MODE_OWNER)
    bpy.msgbus.clear_by_owner(CLIP_START_OWNER)
    bpy.msgbus.clear_by_owner(CLIP_END_OWNER)

    return None