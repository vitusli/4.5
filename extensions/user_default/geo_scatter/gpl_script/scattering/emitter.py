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

##################################################################################################
#
# oooooooooooo                    o8o      .       .
# `888'     `8                    `"'    .o8     .o8
#  888         ooo. .oo.  .oo.   oooo  .o888oo .o888oo  .ooooo.  oooo d8b
#  888oooo8    `888P"Y88bP"Y88b  `888    888     888   d88' `88b `888""8P
#  888    "     888   888   888   888    888     888   888ooo888  888
#  888       o  888   888   888   888    888 .   888 . 888    .o  888
# o888ooooood8 o888o o888o o888o o888o   "888"   "888" `Y8bod8P' d888b
#
#####################################################################################################


import bpy

import os
from mathutils import Vector

from .. utils.extra_utils import dprint, get_from_uid
from .. translations import translate


def is_correct_emitter(o):
    """check if emitter emitter type is mesh"""
    return (o.type=="MESH")

def get_compatible_surfaces_for_scatter(objects):
    """find objects that are compatible surfaces for a geo-scatter engine"""
    
    for o in objects:
        if (o.type=="MESH") : 
            if (o.name in bpy.context.scene.objects):
                yield o

def poll_emitter(self, o):
    """poll fct  for bpy.context.scene.scatter5.emitter prop"""

    dprint("PROP_FCT: poll 'scat_scene.emitter'")

    #don't poll if context object is not compatible
    return is_correct_emitter(o)

def ensure_emitter_pin_mode_synchronization():
    """automatically update emitter pointer to context.object, should only be executed if in pineed mode"""
    
    #don't update if no context object  
    a = bpy.context.object 
    if (not a):
        return None 

    #don't update if context object is not compatible
    if (not is_correct_emitter(a)):
        return None  

    scat_scene = bpy.context.scene.scatter5
    if (not scat_scene.emitter_pinned):
        if (scat_scene.emitter!=bpy.context.object):
            dprint("FCT: ensure_emitter_pin_mode_synchronization(): Auto swapping Emitter")
            scat_scene.emitter = bpy.context.object

    return None

def handler_f_surfaces_cleanup(scene=None):
    """despgraph: check if no deleted surfaces in f_surfaces collection properties, if passed scene is none, we work with the active scene"""

    if (scene is None):
        scene = bpy.context.scene
    op = scene.scatter5.operators.create_operators
    
    match op.f_surface_method:
        
        case 'emitter':
            pass

        case 'collection':
            for i in reversed(range(len(op.f_surfaces))):
                if (op.f_surfaces[i].name not in scene.objects):
                    op.f_surfaces.remove(i)
                    dprint("FCT: handler_f_surfaces_cleanup(): Updating f_surfaces")

        case 'object':
            if (op.f_surface_object is not None) and (op.f_surface_object.name not in scene.objects):
                op.f_surface_object = None
                dprint("FCT: handler_f_surfaces_cleanup(): Updating f_surface_object")

    return None

# def auto_hide_psy_when_emitter_hidden():
#     """depsgraph: hide scatter system(s) automatically when emitter is hidden"""

#     if not bpy.context.scene.scatter5.update_auto_hidden_emitter:
#         return None 

#     emitter = bpy.context.scene.scatter5.emitter
#     if (emitter is None):
#         return None 
        
#     psys = emitter.scatter5.particle_systems
#     is_hidden = emitter.hide_get()

#     if is_hidden:
#         for p in psys:
#             if not p.scatter_obj.hide_viewport:
#                 p.scatter_obj.hide_viewport = True 

#     else:
#         for p in psys:
#             if (p.hide_viewport != p.scatter_obj.hide_viewport):
#                 p.scatter_obj.hide_viewport = p.hide_viewport

#     return None 

def can_add_psy_to_emitter(emitter=None):
    """check if emitter is ok for scattering operators. If passed emitter is none, we take the active scene emitter"""
    
    if (emitter is None):
        emitter = bpy.context.scene.scatter5.emitter

    #can't scatter if no emitter is defined
    if (emitter is None):
        return False
    
    #can't scatter if not in object mode
    elif (bpy.context.mode!="OBJECT"):
        return False
    
    #can't scatter if emitter not in scene?
    # elif (emitter.name not in bpy.context.scene.objects):
    #     return False

    #can't scatter if emitter is linked (can't write new properties on linked objects)
    elif bool(emitter.library):
        return False    

    return True


#   .oooooo.   oooo
#  d8P'  `Y8b  `888
# 888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
# 888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
# 888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
# `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#  `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'


class SCATTER5_OT_set_new_emitter(bpy.types.Operator):

    bl_idname      = "scatter5.set_new_emitter"
    bl_label       = translate("Define a new emitter object")
    bl_description = translate("Define a new emitter object")
    bl_options     = {'INTERNAL','UNDO'}

    obj_session_uid : bpy.props.IntProperty()
    select : bpy.props.BoolProperty(default=False, options={"SKIP_SAVE",},)

    def execute(self, context):

        scat_scene = context.scene.scatter5
        e = get_from_uid(self.obj_session_uid)
        
        #no match?
        if (e is None):
            print(f"ERROR: scatter5.set_new_emitter(): {self.session_uid} uid for emitter not found in bpy.data.objects")
            return {'FINISHED'}
        
        #set emitter as active
        context.scene.scatter5.emitter = e
            
        #select option, if possible
        if (self.select):
            if ((context.mode=='OBJECT') and (e in context.view_layer.objects[:])):
                bpy.ops.object.select_all(action='DESELECT')
                e.select_set(True)
                context.view_layer.objects.active = e

        return {'FINISHED'}


def add_nonlinear_emitter(name="EmptyEmitter", link_in_coll="Geo-Scatter User Col", location=(0,0,0),):

    #get an non linear emit object data in blend?
    dataname = "GeoScatterEmptyEmitter"
    mesh = bpy.data.meshes.get(dataname)

    #import a new one if not already?
    if (mesh is None):
        
        from .. resources.directories import blend_gslogo
        if (os.path.exists(blend_gslogo)):
                
            from .. utils import import_utils
            import_utils.import_objects(
                blend_path=blend_gslogo,
                object_names=[dataname],
                link=False,
                )
            mesh = bpy.data.meshes.get(dataname)
        
    if (mesh is None):
        
        print(f"INFO: Path not found: {blend_gslogo}. Using another mesh instead then..")

        dataname = "UserDumbQuadMesh"
        mesh = bpy.data.meshes.get(dataname)
        
        if (mesh is None):
            mesh = bpy.data.meshes.new(name="UserDumbQuadMesh")
            mesh.from_pydata([(-1,-1,0),(1,-1,0),(1,1,0),(-1,1,0),], [], [(0, 1, 3, 2)])
            mesh.update(calc_edges=True)
            
    #create a new emitter object in Objects
    e = bpy.data.objects.new(name=name, object_data=mesh)
    e.location = location
    e.color = (0.011564, 0.011564, 0.011564, 1.000000)

    #the append the object in the scene or in a chosen collection
    if (link_in_coll):
        col = bpy.data.collections.get(link_in_coll)
    if (col is None):
        col = bpy.context.scene.collection
    col.objects.link(e)
        
    return e
            

class SCATTER5_OT_new_dummy_emitter(bpy.types.Operator):

    bl_idname      = "scatter5.new_dummy_emitter"
    bl_label       = translate("Create a new dummy emitter")
    bl_description = translate("Create a new dummy emitter at the 3D cursor\n\nWhat's the idea behind using a dummy emitter?\n• By default, Geo-Scatter uses the picked emitter object as the surface for your scatterings. However you are free to choose any other surfaces in the surface panel.\n• If you know in advance that you will work with multiple surfaces, it is wiser to use a dummy emitter to store all your scatter-settings, and afterwards choose your surfaces independently from the emitter (you can choose your surfaces in the 'Creation' panel 'on creation' menu or in the 'Tweak' panel 'Surface' settings.)\n• This technique is also best for saving performances, because in Blender, when you tweak the custom settings of a surface used by a geometry-node modifier (such as a Geo-Scatter Scattering Engine), it will send a refresh signal to this modifier, therefore causing potential unecessary slowdowns")
    bl_options     = {'INTERNAL','UNDO'}

    zoom : bpy.props.BoolProperty(default=False, options={"SKIP_SAVE",})

    def execute(self, context):

        emit = add_nonlinear_emitter(location=bpy.context.scene.cursor.location)
        
        #set emitter as active
        scat_scene = bpy.context.scene.scatter5
        scat_scene.emitter = emit

        #selection & zoom
        bpy.ops.object.select_all(action='DESELECT')
        emit.select_set(state=True)
        bpy.context.view_layer.objects.active = emit
        
        if (self.zoom):
            bpy.ops.view3d.view_selected(use_all_regions=False)

        return {'FINISHED'}
        

classes = (

    SCATTER5_OT_set_new_emitter,
    SCATTER5_OT_new_dummy_emitter,
    
    )