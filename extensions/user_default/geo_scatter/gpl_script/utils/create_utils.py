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

#NOTE Here it's a bunch of function related to mesh creation and other simple interraction

def texture_data(type="", name="", duppli_existing=False, image_data=None):
    """create e new texture data, type in [IMAGE,CLOUDS,NOISE,WOOD]""" #used in terrain displacement 
    
    if (image_data):
          typestr = "IMAGE"
    else: typestr = type
        
    t = bpy.data.textures.get(name)
    if duppli_existing: #Dorian, first of all this is false and second of all this function is not used anywhere except for the shitty terrain module.. 
        t = t.copy()
    if t is None:
        t = bpy.data.textures.new(name=name,type=typestr)
        
    t.type = typestr 
    
    if (image_data):
        t.image = image_data
     
    return t

def get_bb_points(o):
    """get the four bounding box top points""" 
    #used in 2dremesher
    
    from mathutils import Vector

    points = []
    for i in [1,2,5,6]: #=top
        p = o.matrix_world @ Vector((o.bound_box[i][0],o.bound_box[i][1],o.bound_box[i][2]))
        p += Vector((0,0,p[2]*0.1))
        points.append(p)
        
    return points

def quad(objname,points):
    """create quad from four points""" 
    #used in 2dremesher 

    m = bpy.data.meshes.new(objname)
    o = bpy.data.objects.new(objname, m)
    
    bpy.context.scene.collection.objects.link(o)
    
    # Generate mesh data
    m.from_pydata(points, [], [(0, 1, 3, 2)])
    
    # Calculate the edges
    m.update(calc_edges=True)

    return o

def point(name,collection):
    """create single point object"""
    #used in camera culling and dynamic camera mask 

    # Create new mesh and a new object
    me = bpy.data.meshes.new(name)
    o = bpy.data.objects.new(name, me)

    # Make a mesh from a list of vertices/edges/faces
    me.from_pydata([(0.0, 0.0, 0.0)], [], [])

    # Display name and update the mesh
    me.update()

    collection.objects.link(o)

    return o

def lock_transform(o,value=True):
    """lock object transforms""" 
    #used when creating the scattering object, and in dynamic camera 
    
    for i in [0,1,2]:
        o.lock_location[i] = value
        o.lock_rotation[i] = value
        o.lock_scale[i]    = value

    return None 

def add_objdata_a_to_b(a=None,b=None):
    """Duplicate object `a` and join its mesh data into object `b`, preserving original selection, active object, and hidden states, using bpy.ops"""
    
    if (a is None or b is None):
        print("ERROR: join_obj_a_to_b(): a or b are None")
        return None
    
    if (a.type!='MESH' or b.type!='MESH'):
        print("ERROR: join_obj_a_to_b(): a or b types aren't MESH")
        return None
    
    if (not a.data.vertices):
        return None
        
    from . import override_utils
    
    with override_utils.attributes_override([b,"hide_select",False],[b,"hide_viewport",False],):
        with override_utils.mode_override(mode="OBJECT"):
                        
            # Create a duplicate
            a_dup = bpy.data.objects.new("_TMP_DUPLICATE_", a.data.copy())
            bpy.context.collection.objects.link(a_dup)
            a_dup.matrix_world = a.matrix_world
            
            # Set selection
            bpy.ops.object.select_all(action='DESELECT')
            a_dup.select_set(True)
            b.select_set(True)
            bpy.context.view_layer.objects.active = b

            # Perform the join operation
            bpy.ops.object.join()
                    
    return None


#   .oooooo.   oooo
#  d8P'  `Y8b  `888
# 888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
# 888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
# 888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
# `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#  `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'


classes = (
    
    )