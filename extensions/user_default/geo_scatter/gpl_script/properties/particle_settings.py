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
# ooooooooooooo                                      oooo         o8o
# 8'   888   `8                                      `888         `"'
#      888      oooo oooo    ooo  .ooooo.   .oooo.    888  oooo  oooo  ooo. .oo.    .oooooooo
#      888       `88. `88.  .8'  d88' `88b `P  )88b   888 .8P'   `888  `888P"Y88b  888' `88b
#      888        `88..]88..8'   888ooo888  .oP"888   888888.     888   888   888  888   888
#      888         `888'`888'    888    .o d8(  888   888 `88b.   888   888   888  `88bod8P'
#     o888o         `8'  `8'     `Y8bod8P' `Y888""8o o888o o888o o888o o888o o888o `8oooooo.
#                                                                                  d"     YD
#                                                                                  "Y88888P'
#####################################################################################################

import bpy

import random
import mathutils

from ... __init__ import bl_info

from .. import scattering

from .. translations import translate
from .. utils.coll_utils import get_collection_by_name
from .. utils.str_utils import get_surfs_shared_attrs


# 88   88 88""Yb 8888b.     db    888888 888888     888888  dP""b8 888888 .dP"Y8
# 88   88 88__dP  8I  Yb   dPYb     88   88__       88__   dP   `"   88   `Ybo."
# Y8   8P 88"""   8I  dY  dP__Yb    88   88""       88""   Yb        88   o.`Y8b
# `YbodP' 88     8888Y"  dP""""Yb   88   888888     88      YboodP   88   8bodP'

#some related class functions: (most update functions are in the update_factory module)

def upd_group(self, context):
    """update function of p.group, will refresh all group properties accordingly"""
    
    p = self

    if (p.group==""):
        p.property_run_update("s_disable_all_group_features", True,)
        
    else:
        #Add new group properties!
        g = p.id_data.scatter5.particle_groups.get(p.group)
        if (g is None):
            g = p.id_data.scatter5.particle_groups.add()
            g.name = p.group

        #Optimize this operation 
        with bpy.context.scene.scatter5.factory_update_pause(event=True,delay=True,sync=True):
            #Ensure group properties values or disable the group settings of these psys
            g.properties_nodetree_refresh()

    return None

def upd_lock(self, context):

    if (self.lock):
        
        self.lock = False
        v = (not self.is_all_locked())
        
        for k in self.bl_rna.properties.keys():
            if (k.endswith("_locked")):
                setattr(self,k,v)
            continue

    return None 


#  dP""b8  dP"Yb  8888b.  888888      dP""b8 888888 88b 88
# dP   `" dP   Yb  8I  Yb 88__       dP   `" 88__   88Yb88
# Yb      Yb   dP  8I  dY 88""       Yb  "88 88""   88 Y88
#  YboodP  YbodP  8888Y"  888888      YboodP 888888 88  Y8


#generate code of feature mask properties 

def codegen_featuremask_properties(scope_ref={}, name="name",):
    """generate the redudant the properies declaration of featuremasks"""

    d = {}

    prop_name = f"{name}_mask_allow"
    d[prop_name] = bpy.props.BoolProperty(
        name=translate("Universal Feature Mask"),
        description=translate("A masking option available on most features. With this option enabled you will be able to define influence-areas where your feature will have an effect"),
        update=scattering.update_factory.factory(prop_name,),
        )
    prop_name = f"{name}_mask_ptr"
    d[prop_name] = bpy.props.StringProperty(
        name=translate("Attribute Pointer"),
        description=translate("Search across all your surface(s) for an attribute\nWe will highlight the pointer in red if the attribute is not shared across your surface(s)"),
        search=lambda s,c,e: get_surfs_shared_attrs(system=s, attr_type='vcol' if (getattr(s,f"{name}_mask_method")=="mask_vcol") else 'vg', searchname=e,),
        search_options={'SUGGESTION','SORT'},
        update=scattering.update_factory.factory(prop_name,),
        )
    prop_name = f"{name}_mask_reverse"
    d[prop_name] = bpy.props.BoolProperty(
        name=translate("Reverse"),
        description=translate("Reverse the influence of this mask"),
        update=scattering.update_factory.factory(prop_name,),
        )
    prop_name = f"{name}_mask_method"
    d[prop_name] = bpy.props.EnumProperty(
        name=translate("Mask Method"),
        description=translate("Select your masking method"),
        default="mask_vg",
        items=(#("none", translate("None"), translate("The feature is not filtered by any masks and is applied to all scattered instances"), "",0 ),
                ("mask_vg", translate("Vertex-Group"), translate("The feature is filtered by a vertex-group mask.\n• Only the instances located within the mask influence will be affected by the feature"), "WPAINT_HLT",1 ),
                ("mask_vcol", translate("Color-Attribute"), translate("The feature is filtered by a color-attribute mask.\n• Only the instances located within the mask influence will be affected by the feature"), "VPAINT_HLT",2 ),
                ("mask_bitmap", translate("Image"), translate("The feature is filtered by an image projected from a given uv map.\n• Only the instances located within the mask influence will be affected by the feature"), "TPAINT_HLT",3 ),
                ("mask_noise", translate("Noise"), translate("The feature is filtered by a procedural noise mask.\n• Only the instances located within the mask influence will be affected by the feature"), "TOPATCH:W_TEXTNOISE",4 ),
              ),
        update=scattering.update_factory.factory(prop_name,),
        )
    prop_name = f"{name}_mask_color_sample_method"
    d[prop_name] = bpy.props.EnumProperty(
        name=translate("Color Sampling"),
        description=translate("Define how to translate the RGBA color values into a mask that will influence your distribution"),
        default="id_greyscale",
        items=( ("id_greyscale", translate("Greyscale"), translate("Combine all colors into a black and white mask"), "NONE", 0,),
                ("id_red", translate("Red Channel"), translate("Only consider the Red channel as a mask"), "NONE", 1,),
                ("id_green", translate("Green Channel"), translate("Only consider the Green channel as a mask"), "NONE", 2,),
                ("id_blue", translate("Blue Channel"), translate("Only consider the Blue channel as a mask"), "NONE", 3,),
                ("id_black", translate("Pure Black"), translate("Only the areas containing a pure black color will be masked"), "NONE", 4,),
                ("id_white", translate("Pure White"), translate("Only the areas containing a pure white color will be masked"), "NONE", 5,),
                ("id_picker", translate("Color ID"), translate("Only the areas containing a color matching the color of your choice will be masked"), "NONE", 6,),
                ("id_hue", translate("Hue"), translate("Only consider the Hue channel as a mask, when converting the RGB colors to HSV values"), "NONE", 7,),
                ("id_saturation", translate("Saturation"), translate("Only consider the Saturation channel as a maskn when converting the RGB colors to HSV values"), "NONE", 8,),
                ("id_value", translate("Value"), translate("Only consider the Value channel as a mask, when converting the RGB colors to HSV values"), "NONE", 9,),
                ("id_lightness", translate("Lightness"), translate("Only consider the Lightness channel as a mask, when converting the RGB colors to HSL values"), "NONE", 10,),
                ("id_alpha", translate("Alpha Channel"), translate("Only consider the Alpha channel as a mask"), "NONE", 11,),
              ),
        update=scattering.update_factory.factory(prop_name,),
        )
    prop_name = f"{name}_mask_id_color_ptr"
    d[prop_name] = bpy.props.FloatVectorProperty(
        name=translate("ID Value"),
        description=translate("The areas containing this color will be considered as a mask"),
        subtype="COLOR",
        default=(1,0,0),
        min=0,
        max=1,
        update=scattering.update_factory.factory(prop_name, delay_support=True,),
        )
    prop_name = f"{name}_mask_bitmap_ptr"
    d[prop_name] = bpy.props.StringProperty(
        name=translate("Image Pointer"),
        search=lambda s,c,e: set(img.name for img in bpy.data.images if (e in img.name)),
        search_options={'SUGGESTION','SORT'},
        update=scattering.update_factory.factory(prop_name,),
        )
    prop_name = f"{name}_mask_bitmap_uv_ptr"
    d[prop_name] = bpy.props.StringProperty(
        name=translate("UV-Map Pointer"),
        description=translate("When interacting with the pointer the plugin will search across surface(s) for shared Uvmaps\nThe pointer will be highlighted in a red color if the chosen attribute is missing from one of your surfaces"),
        default="UVMap",
        search=lambda s,c,e: get_surfs_shared_attrs(system=s, attr_type='uv', searchname=e,),
        search_options={'SUGGESTION','SORT'},
        update=scattering.update_factory.factory(prop_name,),
        )
    prop_name = f"{name}_mask_noise_space"
    d[prop_name] = bpy.props.EnumProperty(
        name=translate("Space"),
        description=translate("Define the procedural texture space"),
        default="local",
        items=( ("local", translate("Local"), translate("The texture is being transformed alongside your object transforms. If your object is being re-scaled, the texture will grow alongside the object"),  "ORIENTATION_LOCAL",0 ),
                ("global", translate("Global"), translate("The texture is not taking your object transforms into consideration. The texture will stay at a consistent world-space size, independently from your object transformations"), "WORLD",1 ),
              ),
        update=scattering.update_factory.factory(prop_name,),
        )
    prop_name = f"{name}_mask_noise_scale"
    d[prop_name] = bpy.props.FloatProperty(
        name=translate("Scale"),
        description=translate("The scale of a procedural texture.\n• A value of '0.01' will creates a large noise pattern.\n• A value of '10.0' will create a small pattern"),
        default=0.2,
        min=0,
        update=scattering.update_factory.factory(prop_name, delay_support=True,),
        )
    prop_name = f"{name}_mask_noise_seed"
    d[prop_name] = bpy.props.IntProperty(
        name=translate("Seed"),
        description=translate("Change this value to randomize the result.\n\nIn 3D graphics, a seed is a starting value used by a random number generator to produce a sequence of random-looking numbers. These numbers can control things like the position, rotation, or scale of objects in a scene. Using the same seed will always generate the same 'random' result, which helps keep things consistent when needed."),
        update=scattering.update_factory.factory(prop_name, delay_support=True,),
        )
    prop_name = f"{name}_mask_noise_is_random_seed"
    d[prop_name] = bpy.props.BoolProperty(
        name=translate("Randomize Seed"),
        description=translate("Randomize the value of the hereby seed property.\n\n• Note that pressing 'ALT' while clicking on this button will garantee the attribution of an unique seed value of this property for all selected-system(s)"),
        default=False,
        update=scattering.update_factory.factory(prop_name),
        )
    prop_name = f"{name}_mask_noise_brightness"
    d[prop_name] = bpy.props.FloatProperty(
        name=translate("Brightness"),
        description=translate("The brightness of the colors of the texture"),
        default=1,
        min=0,
        soft_max=2,
        update=scattering.update_factory.factory(prop_name, delay_support=True,),
        )
    prop_name = f"{name}_mask_noise_contrast"
    d[prop_name] = bpy.props.FloatProperty(
        name=translate("Contrast"),
        description=translate("The contrast of the colors of the texture"),
        default=3,
        min=0,
        soft_max=5,
        update=scattering.update_factory.factory(prop_name, delay_support=True,),
        )

    #define objects in dict
    scope_ref.update(d)
    
    return d

def codegen_properties_by_idx(scope_ref={}, name="my_propXX", nbr=20, items={}, property_type=None, delay_support=False, alt_support=True, sync_support=True,):
    """this fun goal is to generate the redudant the properies declaration"""

    d = {}

    for i in (n+1 for n in range(nbr)):

        #adjust propname depending on index
        if ("XX" in name):
            prop_name = name.replace("XX",f"{i:02}")
        elif ("X" in name):
            prop_name = name.replace("X",f"{i}")
        else:
            raise Exception("codegen_properties_by_idx() forgot to use the XX or X kewords")

        kwargs = items.copy()

        #special case if defaults need to differ depending on number 
        if "default" in kwargs:
            if type(kwargs["default"]) is list:
                kwargs["default"] = kwargs["default"][i-1]

        #adjust label depending on index
        if ("name" in kwargs.keys()):
            to_replace = "XX" if ("XX" in kwargs["name"]) else "X" if ("X" in kwargs["name"]) else ""
            if (to_replace):
                kwargs["name"] = kwargs["name"].replace(to_replace, f" {i}")

        #add update method, update function keyward is always the same as the property name
        kwargs["update"] = scattering.update_factory.factory(prop_name, delay_support=delay_support, alt_support=alt_support, sync_support=sync_support)

        #add property to dict
        d[prop_name] = property_type(**kwargs)

        continue
        
    #define objects in dict
    scope_ref.update(d)
    return d


# ooooooooo.                          .    o8o            oooo
# `888   `Y88.                      .o8    `"'            `888
#  888   .d88'  .oooo.   oooo d8b .o888oo oooo   .ooooo.   888   .ooooo.   .oooo.o
#  888ooo88P'  `P  )88b  `888""8P   888   `888  d88' `"Y8  888  d88' `88b d88(  "8
#  888          .oP"888   888       888    888  888        888  888ooo888 `"Y88b.
#  888         d8(  888   888       888 .  888  888   .o8  888  888    .o o.  )88b
# o888o        `Y888""8o d888b      "888" o888o `Y8bod8P' o888o `Y8bod8P' 8""888P'
    

class SCATTER5_PR_particle_systems(bpy.types.PropertyGroup): 
    """bpy.context.object.scatter5.particle_systems, will be stored on emitter"""
    
    #  dP""b8 888888 88b 88 888888 88""Yb 88  dP""b8
    # dP   `" 88__   88Yb88 88__   88__dP 88 dP   `"
    # Yb  "88 88""   88 Y88 88""   88"Yb  88 Yb
    #  YboodP 888888 88  Y8 888888 88  Yb 88  YboodP
    
    system_type : bpy.props.StringProperty(
        description="Sometimes, we pass a 'system' argument to a function that is either a 'GROUP_SYSTEM' or 'SCATTER_SYSTEM', use this property to recognize one from the other",
        get=lambda s: "SCATTER_SYSTEM",
        set=lambda s,v: None
        )
    name : bpy.props.StringProperty(
        default="",
        name=translate("Scatter Name"),
        update=scattering.rename.rename_particle,
        )
    name_bis : bpy.props.StringProperty(
        description="important for renaming function, avoid name collision",
        default="",
        )
    description : bpy.props.StringProperty( #passed to interface props SCATTER5_PR_particle_interface_items for lister template 'item_dyntip_propname' option
        default="",
        name=translate("Description"),
        description=translate("Define descriptions for your scatter items, you can check them when hovering your Scatters or Groups in the System-Lister interface"),
        )
    scatter_obj : bpy.props.PointerProperty(
        type=bpy.types.Object,
        name=translate("Scatter Object"),
        description="Instance generator object. An object locked on scene origin where we'll generate points & instances, this is where our geometry node engine is located. This object might contain custom generated points such as vertices created by manual mode or cache information. This property is ready-only",
        )
    uuid : bpy.props.IntProperty(
        get=lambda s: s.scatter_obj.scatter5.uuid if (s.scatter_obj) else 0,
        description="will give you the uuid of the scatter_obj directly, return 0 if scatter_obj is None",
        )
    is_linked : bpy.props.BoolProperty(
        get=lambda s: bool(s.scatter_obj.library) if s.scatter_obj else False,
        description="check if scatter_obj is linked",
        )

    def get_scatter_mod(self, strict=True, raise_exception=True,):
        """return the Geo-scatter geonode modifier used by the scatter_obj
        - strict:          if True: the modifier need to be up to date with the current engine_version, if False: get any geo-scatter modifer, modifiers from previous geo-scatter versions that do need to be updated to work properly
        - raise_exception: throw an error message if the item couldn't be found
        """
        mod = None

        #no scatter obj?
        if (self.scatter_obj is None):
            msg = f"REPORT: get_scatter_mod(): Can't find a scatter_obj attached to your system? (Information: emitter='{self.id_data.name}' psy='{self.name}')"
            if (raise_exception):
                  raise Exception(msg)
            else: print(msg)
            return None
        
        #scatter obj hasn't modifiers?
        if (not self.scatter_obj.modifiers):
            msg = f"REPORT: get_scatter_mod(): Your scatter_obj doesn't have any modifier? (Information: emitter='{self.id_data.name}' psy='{self.name}' scatter_obj='{self.scatter_obj.name}')"
            if (raise_exception):
                  raise Exception(msg)
            else: print(msg)
            return None
        
        #search for the mod with our engine name:
        # only get latest version of scatter-engine?
        if (strict):
            mod = self.scatter_obj.modifiers.get(bl_info["engine_version"])
        # or more flexible way to get the engine, support old versions of engines
        else:
            for m in self.scatter_obj.modifiers:
                if m.name.startswith(("Geo-Scatter Engine","Scatter5 Geonode Engine")):
                    mod = m
                    break
        
        #did we find the mod?
        if (mod):
            
            #if geometry node type, then we found it!
            if (mod.type=='NODES'):
                return mod
        
            #if found a mod with correct name, but is not of geometry node type? how's that possible
            msg = f"REPORT: get_scatter_mod(): Modifier found is not a Geometry-node modifier? What happened? (Information: emitter='{self.id_data.name}' psy='{self.name}' scatter_obj='{self.scatter_obj.name}' modtype='{mod.type}' strict={strict})"
            if (raise_exception):
                raise Exception(msg)
            else: print(msg)
            return None

        #not found anything?
        msg = f"REPORT: get_scatter_mod(): Can't find a scatter-engine modifier! (Information: emitter='{self.id_data.name}' psy='{self.name}' scatter_obj='{self.scatter_obj.name}' strict={strict})"
        if (raise_exception):
              raise Exception(msg)
        else: print(msg)
        
        return None
    
    def get_scatter_node(self, node_name, strict=True, raise_exception=True,):
        """return a node contained within the Geo-scatter Engine nodegroup stored in the scatter_obj geonode modifiers. Return none if not found>.
        - strict:          if True: the modifier need to be up to date with the current engine_version, if False: get any geo-scatter modifer, modifiers from previous geo-scatter versions that do need to be updated to work properly
        - raise_exception: throw an error message if the item couldn't be found
        """
        mod = self.get_scatter_mod(strict=strict, raise_exception=raise_exception)
        
        #failed to get modifier?
        if (not mod):
            msg = f"REPORT: get_scatter_node(): Failed to get modifier, see previous error(s)."
            if (raise_exception):
                raise Exception(msg)
            else: print(msg)
            return None
        
        #modifier doens't have node_group ? 
        if (not hasattr(mod,'node_group') or (mod.node_group is None)):
            msg = f"REPORT: get_scatter_node(): Can't find a scatter-engine nodegroup for the modifier! (Information: emitter='{self.id_data.name}' psy='{self.name}' scatter_obj='{self.scatter_obj.name}' modifier='{mod.name}'/'{mod.type}' strict={strict})"
            if (raise_exception):
                raise Exception(msg)
            else: print(msg)
            return None
        
        #found the node?
        n = mod.node_group.nodes.get(node_name)
        if (n):
            return n
        
        #did not find the node?
        msg = f"REPORT: get_scatter_node(): Couldn't find '{node_name}' in scatter_obj.modifiers[].node_group.node!"
        if (raise_exception):
            raise Exception(msg)
        else: print(msg)
        
        return None

    def get_scatter_psy_collection(self, strict=True, ambiguous=False,):
        """get the 'psy : ScatterName' collection that has this system scatter_obj as chidren, If found"""
        
        so = self.scatter_obj
        if (so is None):
            return None
        
        psy_coll_name = f"psy : {self.name}"
        
        coll = None
        
        if (strict):
            for c in so.users_collection:
                if (c.name==psy_coll_name):
                    return c
        
        if (ambiguous):
            for c in so.users_collection:
                if (c.name.startswith(psy_coll_name)):
                    return c
        
        return coll
        
    # .dP"Y8 888888 88     888888  dP""b8 888888 88  dP"Yb  88b 88
    # `Ybo." 88__   88     88__   dP   `"   88   88 dP   Yb 88Yb88
    # o.`Y8b 88""   88  .o 88""   Yb        88   88 Yb   dP 88 Y88
    # 8bodP' 888888 88ood8 888888  YboodP   88   88  YbodP  88  Y8
    
    active : bpy.props.BoolProperty( 
        default=False,
        description="ready only! auto-updated by `psy.particle_interface_idx` update function `on_particle_interface_interaction()`",
        options={'LIBRARY_EDITABLE',},
        )
    sel : bpy.props.BoolProperty(
        default=False,
        name=translate("Selection State"),
        description=translate("Select/Deselect a scatter-system\nThe act of selection in Geo-Scatter is very important, as operators might act on the selected-system(s). Additionally, you can press the 'ALT' key while changing a property value to batch-apply the new value of the property to all the selected system(s) simultaneously!"),
        options={'LIBRARY_EDITABLE',},
        )

    # Yb    dP 888888 88""Yb .dP"Y8 88  dP"Yb  88b 88 88 88b 88  dP""b8
    #  Yb  dP  88__   88__dP `Ybo." 88 dP   Yb 88Yb88 88 88Yb88 dP   `"
    #   YbdP   88""   88"Yb  o.`Y8b 88 Yb   dP 88 Y88 88 88 Y88 Yb  "88
    #    YP    888888 88  Yb 8bodP' 88  YbodP  88  Y8 88 88  Y8  YboodP

    addon_type : bpy.props.StringProperty(
        default=bl_info["name"].replace('®',''),
        description="Scatter system created with Geo-Scatter or Biome-Reader ?",
        )
    addon_version : bpy.props.StringProperty(
        default="5.0", #lower possible by default, as we added this prop on Geo-Scatter 5.1, shall be fine for all users psys data
        description="Scatter version upon which this scatter-system was created (in add_psy_virgin())",
        )
    blender_version : bpy.props.StringProperty(
        default="3.0", #lower possible by default, as we added this prop on Geo-Scatter 5.2, could also be 3.1 
        description="Blender version upon which this scatter-system was created (in add_psy_virgin())",
        )
    blendfile_uuid : bpy.props.IntProperty(
        default=0,
        description="upon .add_psy_virgin() operation, the scatter system will be tagged with the current blend file geo-scatter blendfile_uuid property, important in order to distinguish append/links files. Property will be edited in overseer.py, otherwise READ ONLY",
        )
    
    def is_valid_addon_version(self):
        """verify if this psy version is adequate to the current addon version"""
        
        from .. utils.str_utils import as_version_tuple
        #scatter system need always to be up to date with the major releases, 
        #if the scatter was created with a lower version of the plugin, we changed the nodetree in newer version, and this system needs and update
        #if the scatter was created with a higher version of the plugin, the current interface will simply not be possible, illegal action by user
        return as_version_tuple(self.addon_version, trunc_to='minor',) == as_version_tuple(bl_info['version'], trunc_to='minor',)
    
    def is_valid_blender_version(self):
        """verify if this psy blender version is adequate to the current version of blender the user is using"""
        
        from .. utils.str_utils import as_version_tuple
        #blender version upon which the geometry-node nodetree was created from always need to be lower or equal of current blender version
        #if user brings nodetrees saved in a future version of blender, the data will be corrupted forever
        return as_version_tuple(self.blender_version, trunc_to='minor',) <= as_version_tuple(bpy.app.version, trunc_to='minor',)
    
    def is_from_another_blendfile(self):
        """check if this system has been created from this blendfile or is coming from an append/link operation"""
        
        from ... __init__ import blend_prefs
        scat_data = blend_prefs()
        
        if (scat_data.blendfile_uuid==0):
            print("ALERT: is_from_another_blendfile() blendfile_uuid should never be 0")
        
        return scat_data.blendfile_uuid!=self.blendfile_uuid #NOTE, there's always the risk of two blend file with independently generated uuid values.. one chance in 4 Billion tho..
    
    # 88""Yb 888888 8b    d8  dP"Yb  Yb    dP 888888
    # 88__dP 88__   88b  d88 dP   Yb  Yb  dP  88__
    # 88"Yb  88""   88YbdP88 Yb   dP   YbdP   88""
    # 88  Yb 888888 88 YY 88  YbodP     YP    888888

    def remove_psy(self): #best to use bpy.ops.scatter5.remove_system()
                          #NOTE: will need to use particle_interface_refresh() after this operator
        emitter = self.id_data

        #save selection 
        save_sel = [p.name for p in emitter.scatter5.get_psys_selected()]

        #remove scatter object 
        if (self.scatter_obj): 
            bpy.data.meshes.remove(self.scatter_obj.data)

        #remove scatter geonode_coll collection
        geonode_coll = get_collection_by_name(f"psy : {self.name}")
        if (geonode_coll):
            bpy.data.collections.remove(geonode_coll)

        #remove scatter instance_coll (if not used by another psy)
        instance_coll = get_collection_by_name(f"ins_col : {self.name}")
        if (instance_coll is not None):
            if (self.s_instances_coll_ptr==instance_coll):

                from .. scattering.instances import collection_users

                if (len(collection_users(instance_coll))==1):
                    bpy.data.collections.remove(instance_coll)

        #find idx from name in order to remove
        for i,p in enumerate(emitter.scatter5.particle_systems):
            if (p.name==self.name):
                emitter.scatter5.particle_systems.remove(i) #can we remove self from self context? hmm
                break

        #restore selection needed, when we change active index, default behavior == reset selection and select active
        for p in save_sel:
            if (p in emitter.scatter5.particle_systems):
                emitter.scatter5.particle_systems[p].sel = True

        return None

    # .dP"Y8 88  88  dP"Yb  Yb        dP   88  88 88 8888b.  888888
    # `Ybo." 88  88 dP   Yb  Yb  db  dP    88  88 88  8I  Yb 88__
    # o.`Y8b 888888 Yb   dP   YbdPYbdP     888888 88  8I  dY 88""
    # 8bodP' 88  88  YbodP     YP  YP      88  88 88 8888Y"  888888

    hide_viewport : bpy.props.BoolProperty(
        default=False,
        name=translate("Disable in Viewport"),
        description=translate("Hide/Unhide a scatter-system from viewport. Toggling this option will change the viewport visibility state of the corresponding 'scatter_obj'.\n(Optionally, it can also change the visibility state of the 'scatter_obj' geometry-node scatter modifier for an extra gain of performance during scene evaluation. Only if the optimization option s enabled in the Geo-Scatter plugin preferences)"),
        update=scattering.update_factory.factory("hide_viewport", sync_support=False,),
        options={'LIBRARY_EDITABLE',},
        )
    hide_render : bpy.props.BoolProperty(
        default=False, 
        name=translate("Disable in Render"),
        description=translate("Hide/Unhide a scatter-system from final render. Toggling this option will change the render visibility state of the corresponding 'scatter_obj'.\n(Optionally, it can also change the visibility state of the 'scatter_obj' geometry-node scatter modifier for an extra gain of performance during scene evaluation. Only if the optimization option is enabled in the Geo-Scatter plugin preferences)"),
        update=scattering.update_factory.factory("hide_render", sync_support=False,),
        options={'LIBRARY_EDITABLE',},
        )

    #  dP""b8 88""Yb  dP"Yb  88   88 88""Yb     .dP"Y8 Yb  dP .dP"Y8 888888 888888 8b    d8
    # dP   `" 88__dP dP   Yb 88   88 88__dP     `Ybo."  YbdP  `Ybo."   88   88__   88b  d88
    # Yb  "88 88"Yb  Yb   dP Y8   8P 88"""      o.`Y8b   8P   o.`Y8b   88   88""   88YbdP88
    #  YboodP 88  Yb  YbodP  `YbodP' 88         8bodP'  dP    8bodP'   88   888888 88 YY 88

    group : bpy.props.StringProperty(
        default="",
        description="we'll automatically create and assign the group items by updating this prop. EmptyField==NoGroup. Note that you might want to run emitter.particle_interface_refresh() after use. ",
        update=upd_group,
        )
    
    def get_group(self):
        """get group of which this system (self) is a member of, will return None if not part of any groups"""
        
        emitter = self.id_data
        for g in emitter.scatter5.particle_groups:
            if (g.name==self.group):
                return g
            
        return None

    # 88      dP"Yb   dP""b8 88  dP     .dP"Y8 Yb  dP .dP"Y8 888888 888888 8b    d8
    # 88     dP   Yb dP   `" 88odP      `Ybo."  YbdP  `Ybo."   88   88__   88b  d88
    # 88  .o Yb   dP Yb      88"Yb      o.`Y8b   8P   o.`Y8b   88   88""   88YbdP88
    # 88ood8  YbodP   YboodP 88  Yb     8bodP'  dP    8bodP'   88   888888 88 YY 88

    #lock settings, we just do not draw interface, and we need to be carreful, add conditions on operators that modify settings, ex copy paste, synchronize, preset/reset ect... 

    lock : bpy.props.BoolProperty(
        default=False,
        description=translate("Lock/unlock all settings of this scatter-system, locking means that the values will be be read only."),
        update=upd_lock, #this implementation is meh. need getter/setter, would be better perhaps? or maybe constant update in gui draw calls will slow perfs?
        )

    #each categories also have their own lock properties

    def is_locked(self,propname):
        """check if given keys, can be full propname or just category name, is locked"""

        _locked_api = ""
        for cat in ("s_surface","s_distribution","s_mask","s_rot","s_scale","s_pattern","s_abiotic","s_proximity","s_ecosystem","s_push","s_wind","s_visibility","s_instances","s_display",):
            if (cat in propname):
                _locked_api = cat + "_locked"
                break
        _locked_api = self.get(_locked_api)
        return False if (_locked_api is None) else _locked_api

    def is_all_locked(self,):
        """check if all categories are locked (mainly used to display lock icon in GUI)"""

        return all( self.get(k) for k,v in self.bl_rna.properties.items() if k.endswith("_locked") )

    def lock_all(self,):
        """lock all property categories"""

        for k in self.bl_rna.properties.keys():
            if (k.endswith("_locked")):
                setattr(self,k,True)

        return None

    def unlock_all(self,):
        """unlock all property categories"""

        for k in self.bl_rna.properties.keys():
            if (k.endswith("_locked")):
                setattr(self,k,False)

        return None 

    # 888888 88""Yb 888888 888888 8888P 888888     .dP"Y8 Yb  dP .dP"Y8 888888 888888 8b    d8
    # 88__   88__dP 88__   88__     dP  88__       `Ybo."  YbdP  `Ybo."   88   88__   88b  d88
    # 88""   88"Yb  88""   88""    dP   88""       o.`Y8b   8P   o.`Y8b   88   88""   88YbdP88
    # 88     88  Yb 888888 888888 d8888 888888     8bodP'  dP    8bodP'   88   888888 88 YY 88

    freeze : bpy.props.BoolProperty( #TODO LATER
        default=False,
        )

    # .dP"Y8 Yb  dP 88b 88  dP""b8 88  88     .dP"Y8 Yb  dP .dP"Y8 888888 888888 8b    d8
    # `Ybo."  YbdP  88Yb88 dP   `" 88  88     `Ybo."  YbdP  `Ybo."   88   88__   88b  d88
    # o.`Y8b   8P   88 Y88 Yb      888888     o.`Y8b   8P   o.`Y8b   88   88""   88YbdP88
    # 8bodP'  dP    88  Y8  YboodP 88  88     8bodP'  dP    8bodP'   88   888888 88 YY 88

    def is_synchronized(self, s_category, consider_settings=True,):
        """check if the psy is being synchronized"""

        from ... __init__ import blend_prefs
        scat_data = blend_prefs()

        if (consider_settings):
            if (not scat_data.factory_synchronization_allow):
                return False

        return any( ch.psy_settings_in_channel(self.name, s_category,) for ch in scat_data.sync_channels )

    def get_sync_siblings(self,):
        """get information about what is sync with what"""

        from ... __init__ import blend_prefs
        scat_data = blend_prefs()
        
        d = []

        for ch in scat_data.sync_channels:
            if ch.name_in_members(self.name):
                category_list=ch.category_list()
                if (len(category_list)!=0):
                    d.append({ "channel":ch.name, "categories":category_list, "psys":ch.get_sibling_members(), })
        return d

    #  dP""b8    db    888888 888888  dP""b8  dP"Yb  88""Yb Yb  dP     88   88 .dP"Y8 888888 8888b.
    # dP   `"   dPYb     88   88__   dP   `" dP   Yb 88__dP  YbdP      88   88 `Ybo." 88__    8I  Yb
    # Yb       dP__Yb    88   88""   Yb  "88 Yb   dP 88"Yb    8P       Y8   8P o.`Y8b 88""    8I  dY
    #  YboodP dP""""Yb   88   888888  YboodP  YbodP  88  Yb  dP        `YbodP' 8bodP' 888888 8888Y"

    def is_category_used(self, s_category):
        """check if the given property category is active"""

        match s_category:
            
            case 's_distribution':
                
                #distribution category is always active
                return True
            
            case 's_surface':
                
                #surfaces category is used if surfaces count is not none
                return len(self.get_surfaces())

            case 's_instances':
                
                #this category has special requirement in order to be used         
                if (self.s_instances_method=="ins_collection"):
                    if ( (self.s_instances_coll_ptr is not None) and len(self.s_instances_coll_ptr.objects)!=0 ):
                        return True
                return False
            
            case str(): #for every other categories they got a big master button
                    
                #consider mute functionality (master toggle)
                master_allow = getattr(self, f"{s_category}_master_allow")
                if (master_allow==False):
                    return False

                #they also got a get_xxx_main_features() function
                try: main_features = getattr(self, f"get_{s_category}_main_features")()
                except: raise Exception(f"BUG: categories not set up correctly, get_{s_category}_main_features() couldn't be found")

                #and we should verify
                return any( getattr(self,sett) for sett in main_features )
            
        raise Exception(f"ERROR: is_category_used(): passed non str arguments? {s_category}")
        

    # .dP"Y8 888888 888888 888888 88 88b 88  dP""b8 .dP"Y8     88""Yb 888888 888888 88""Yb 888888 .dP"Y8 88  88
    # `Ybo." 88__     88     88   88 88Yb88 dP   `" `Ybo."     88__dP 88__   88__   88__dP 88__   `Ybo." 88  88
    # o.`Y8b 88""     88     88   88 88 Y88 Yb  "88 o.`Y8b     88"Yb  88""   88""   88"Yb  88""   o.`Y8b 888888
    # 8bodP' 888888   88     88   88 88  Y8  YboodP 8bodP'     88  Yb 888888 88     88  Yb 888888 8bodP' 88  88
    
    def property_run_update(self, prop_name, value,):
        """directly run the property update task function (== changing nodetree) w/o changing any property value, and w/o going in the update fct wrapper/dispatcher"""

        return scattering.update_factory.UpdatesRegistry.run_update(self, prop_name, value,)

    def property_nodetree_refresh(self, prop_name,):
        """refresh this property value in it's scatter nodetree"""

        value = getattr(self,prop_name)
        return self.property_run_update(prop_name, value,)
    
    def properties_nodetree_refresh(self,):
        """for every properties, make sure nodetree is updated"""

        props = [k for k in self.bl_rna.properties.keys() if k.startswith("s_")]

        #need to ignore "s_beginner" settings if using Geo-Scatter, else will cause value conflicts
        if (self.addon_type=='Geo-Scatter'):
            props = [k for k in props if not k.startswith("s_beginner")]
            
        #need to ignore properties that doesn't have any update functions in the Registry
        props = [k for k in props if (k in scattering.update_factory.UpdatesRegistry.UpdatesDict.keys())]
        
        for prop_name in props:
            self.property_nodetree_refresh(prop_name)

        return None

    #  dP""b8 888888 888888      dP""b8  dP"Yb  88   88 88b 88 888888 
    # dP   `" 88__     88       dP   `" dP   Yb 88   88 88Yb88   88   
    # Yb  "88 88""     88       Yb      Yb   dP Y8   8P 88 Y88   88   
    #  YboodP 888888   88        YboodP  YbodP  `YbodP' 88  Y8   88   

    #TODO update for blender 4.3 can get rid of these and use warning message to pass the info
    
    scatter_count_viewport : bpy.props.IntProperty(
        description="Calculated scatter count for the viewport state, not considering the 'hide_viewport' property",
        default=-1,
        options={'LIBRARY_EDITABLE',},
        )
    scatter_count_viewport_consider_hide_viewport : bpy.props.IntProperty(
        description="Calculated scatter count for the viewport state, considering the 'hide_viewport' property",
        default=-1,
        options={'LIBRARY_EDITABLE',},
        )
    scatter_count_render : bpy.props.IntProperty(
        description="Calculated scatter count for the final render state",
        default=-1,
        options={'LIBRARY_EDITABLE',},
        )

    def get_depsgraph_count(self, attrs=[], ):
        """get an attribute of this scatter-system scatter-obj in evaluated depsgraph, 
        input a list of attr names you wish to get, you'll recieve a list of values back
        mode enum in 'scatterpoint' or 'pointcloud' """

        alist = [] 

        #nodetree to mesh
        self.property_run_update("s_eval_depsgraph", "scatterpoint",)

        #grab values
        depsgraph = bpy.context.evaluated_depsgraph_get()
        e = self.scatter_obj.evaluated_get(depsgraph)

        for name in attrs:
            att = e.data.attributes.get(name)
            
            if (att is None):
                  alist.append([None])
                  continue

            alist.append([att.data[0].value])
            continue

        #restore mesh state 
        self.property_run_update("s_eval_depsgraph", False,)

        return alist

    def get_scatter_count(self, state="viewport", viewport_unhide=True,):
        """evaluate the psy particle count (will unhide psy if it was hidden) slow! do not in real time"""

        #Need to unhide a sys?
        was_hidden = self.hide_viewport 
        if (was_hidden and viewport_unhide):
            self.hide_viewport = False
        
        #set fake render state by overriding all our visibility features?
        if (state=="render"):

            if (self.hide_render):
                count = 0
            else:
                #fake render state for visibility features
                self.property_run_update("s_simulate_final_render", True,)
                #get nodetree attr
                attrs = self.get_depsgraph_count(attrs=["scatter_count"],)
                #get count
                count = attrs[0][0] if (attrs[0]!=[None]) else 0
                #restore fake render state for visibility features
                self.property_run_update("s_simulate_final_render", False,)

            #update props
            self.scatter_count_render = count

        #or direct eval from viewport?
        elif (state=="viewport"):

            #get nodetree attr
            attrs = self.get_depsgraph_count(attrs=["scatter_count"],)
            #get count
            count = attrs[0][0] if (attrs[0]!=[None]) else 0
            #update props
            self.scatter_count_viewport = count
            uncount = 0 if (was_hidden) else count
            self.scatter_count_viewport_consider_hide_viewport = uncount

        #restore hidden ?
        if (was_hidden and viewport_unhide):
            self.hide_viewport = True
                
        return count

    def get_scatter_density(self, refresh_square_area=True,):
        """evaluate psy density /m² of this scatter system independently of , will remove masks and optimizations temporarily -- CARREFUL MIGHT BE SLOW -- DO NOT RUN IN REAL TIME"""

        p = self
        g = self.get_group()

        #Will need to disable all this, as they have an non-rerpresentative impact ond density
        to_disable = [
            "s_mask_vg_allow",
            "s_mask_vcol_allow",
            "s_mask_bitmap_allow",
            "s_mask_curve_allow",
            "s_mask_boolvol_allow",
            "s_mask_upward_allow",
            "s_mask_material_allow",
            "s_proximity_repel1_allow",
            "s_proximity_repel2_allow",
            "s_ecosystem_affinity_allow",
            "s_ecosystem_repulsion_allow",
            "s_visibility_facepreview_allow",
            "s_visibility_view_allow",
            "s_visibility_cam_allow",
            "s_visibility_maxload_allow",
            "s_display_allow",
            ]
        if (g is not None): 
            to_disable += [
                "s_gr_mask_vg_allow",
                "s_gr_mask_vcol_allow",
                "s_gr_mask_bitmap_allow",
                "s_gr_mask_curve_allow",
                "s_gr_mask_boolvol_allow",
                "s_gr_mask_material_allow",
                "s_gr_mask_upward_allow",
                ]

        #temprorarily disable mask features for psys or groups
        to_re_enable = []
        for prp in to_disable:
            e = g if prp.startswith("s_gr_") else p
            if (getattr(e,prp)==True):
                setattr(e,prp,False)
                to_re_enable.append(prp)
            continue

        #get square area 
        if (refresh_square_area):
              square_area = p.get_surfaces_square_area(evaluate="recalculate", eval_modifiers=True, get_selection=False,)
        else: square_area = p.get_surfaces_square_area(evaluate="gather",)

        #get density 
        count = p.get_scatter_count(state='viewport',)
        density = round(count/square_area,4)

        #re-enabled the temporarily disabled
        for prp in to_re_enable:
            e = g if prp.startswith("s_gr_") else p
            setattr(e,prp,True)
            continue

        return density
    
    # .dP"Y8 88""Yb    db     dP""b8 888888 
    # `Ybo." 88__dP   dPYb   dP   `" 88__   
    # o.`Y8b 88"""   dP__Yb  Yb      88""   
    # 8bodP' 88     dP""""Yb  YboodP 888888 
    
    def set_general_space(self,space='local'):
        """redefine the general space of this scatter as local or global. This function will impact all possible settings related to space"""
        
        contrary = 'global' if (space=='local') else 'local'
        
        #set all space to local
        for k in self.bl_rna.properties.keys():
            if (k.endswith("_space")):
                #ignore these specific settings
                if (k in ('s_distribution_projbezarea_space','s_distribution_projbezline_space')):
                    continue
                setattr(self,k,space)

        #now fix some direction alignment spaces too
        
        #fix Z alignment²
        if (self.s_rot_align_z_method==f'meth_align_z_{contrary}'):
            self.s_rot_align_z_method=f'meth_align_z_{space}'
        if (self.s_rot_align_z_method_projbezareanosurf_special==f'meth_align_z_{contrary}'):
            self.s_rot_align_z_method_projbezareanosurf_special=f'meth_align_z_{space}'
        if (self.s_rot_align_z_method_projbezlinenosurf_special==f'meth_align_z_{contrary}'):
            self.s_rot_align_z_method_projbezlinenosurf_special=f'meth_align_z_{space}'

        #fix Y alignment
        if (self.s_rot_align_y_method==f'meth_align_y_{contrary}'):
            self.s_rot_align_y_method=f'meth_align_y_{space}'
        if (self.s_rot_align_y_method_projbezareanosurf_special==f'meth_align_y_{contrary}'):
            self.s_rot_align_y_method_projbezareanosurf_special=f'meth_align_y_{space}'
        if (self.s_rot_align_y_method_projbezlinenosurf_special==f'meth_align_y_{contrary}'):
            self.s_rot_align_y_method_projbezlinenosurf_special=f'meth_align_y_{space}'
        if (self.s_rot_align_y_method_projemptiesnosurf_special==f'meth_align_y_{contrary}'):
            self.s_rot_align_y_method_projemptiesnosurf_special=f'meth_align_y_{space}'
        
        #fix push dir                    
        if (self.s_push_dir_method==f'push_{contrary}'):
            self.s_push_dir_method=f'push_{space}'
        if (self.s_push_dir_method_projbezareanosurf_special==f'push_{contrary}'):
            self.s_push_dir_method_projbezareanosurf_special=f'push_{space}'
        if (self.s_push_dir_method_projbezlinenosurf_special==f'push_{contrary}'):
            self.s_push_dir_method_projbezlinenosurf_special=f'push_{space}'

        #set patterns projectin spaces as local/global as well
        for i in (1,2,3):
            if getattr(self,f"s_pattern{i}_allow"):
                texture_name = getattr(self,f"s_pattern{i}_texture_ptr")
                if (texture_name is not None):
                    ng = self.get_scatter_node(f's_pattern{i}').node_tree.nodes['texture'].node_tree
                    if ng.name.startswith(".TEXTURE *DEFAULT*"):
                        continue
                    t = ng.scatter5.texture
                    t.mapping_projection = space
                            
        return None
    
    #  dP""b8  dP"Yb  88      dP"Yb  88""Yb
    # dP   `" dP   Yb 88     dP   Yb 88__dP
    # Yb      Yb   dP 88  .o Yb   dP 88"Yb
    #  YboodP  YbodP  88ood8  YbodP  88  Yb 
    
    s_color : bpy.props.FloatVectorProperty(
        name=translate("Display Color"),
        description=translate("Changing this color property will directly change the display color value of the corresponding 'scatter_obj' of this scatter-system. You can set the viewport shading color to 'Object' to visualize the display color in the viewport"),
        subtype="COLOR",
        min=0,
        max=1,
        size=4,
        get=lambda s: s.scatter_obj.color if (s.scatter_obj) else (0,0,0,1),
        set=lambda s,v: setattr(s.scatter_obj,"color",v) if (s.scatter_obj) else None,
        options={'LIBRARY_EDITABLE',},
        )

    # .dP"Y8 88   88 88""Yb 888888    db     dP""b8 888888
    # `Ybo." 88   88 88__dP 88__     dPYb   dP   `" 88__
    # o.`Y8b Y8   8P 88"Yb  88""    dP__Yb  Yb      88""
    # 8bodP' `YbodP' 88  Yb 88     dP""""Yb  YboodP 888888

    ###################### This category of settings keyword is : "s_surface"

    s_surface_locked : bpy.props.BoolProperty(
        description=translate("Lock/Unlock Settings"),
        )

    # def get_s_surface_main_features(self, availability_conditions=True,):
    #     return []

    # s_surface_master_allow : bpy.props.BoolProperty( 
    #     name=translate("Master Toggle"),
    #     description=translate("Mute/Unmute all features of this category in one click"),
    #     default=True, 
    #     update=scattering.update_factory.factory("s_surface_master_allow", sync_support=False,),
    #     )

    ########## ##########

    s_surface_method : bpy.props.EnumProperty(
        name=translate("Surface Method"),
        description=translate("Define the surface(s) which the instances will be scattered upon"),
        default= "emitter",
        items=( ("emitter",translate("Emitter Object"),translate("Scatter on the surface of your emitter object."),"TOPATCH:W_EMITTER",0),
                ("object",translate("Single Object"),translate("Scatter on the surface of a chosen object. This leads to a non-linear workflow."),"TOPATCH:W_SURFACE_SINGLE",1),
                ("collection",translate("Multiple Objects"),translate("Scatter on the surfaces of all objects in chosen collection. This leads to a multi-surface workflow."),"TOPATCH:W_SURFACE_MULTI",2),
              ),
        update=scattering.update_factory.factory("s_surface_method"),
        )
    s_surface_object : bpy.props.PointerProperty(
        name=translate("Chosen Surface"),
        description=translate("Scatter on the surface of this object"),
        type=bpy.types.Object,
        update=scattering.update_factory.factory("s_surface_object"),
        )
    s_surface_collection : bpy.props.StringProperty( #TODO, no longer rely on collection... need more flexible system for surface and collections or else. need a dynamic join geometry ng
        name=translate("Chosen Surface(s)"),
        description=translate("Scatter on the surface of all object(s) located in this collection"),
        search=lambda s,c,e: set(col.name for col in bpy.data.collections if (e in col.name)),
        search_options={'SUGGESTION','SORT'},
        update=scattering.update_factory.factory("s_surface_collection"),
        )

    def get_surfaces(self):
        """return a list of surface object(s)"""

        match self.s_surface_method:
                
            case 'emitter':
                return [self.id_data]

            case 'object':
                if (self.s_surface_object):
                    return [self.s_surface_object]

            case 'collection':
                node = self.get_scatter_node("s_surface_evaluator", strict=True, raise_exception=False,)
                if (node):
                    coll = node.inputs[2].default_value
                    if (coll):
                        return coll.objects[:]

        return []

    def get_surfaces_square_area(self, evaluate="gather", eval_modifiers=True, get_selection=False,):
        """will gather or optionally refresh each obj of the surfaces: object.scatter5.estimated_square_area"""

        total_area = 0
        for s in self.get_surfaces():
            object_area = 0

            match evaluate:
                    
                #just get each values, do not refresh?
                case 'gather':
                    object_area = s.scatter5.estimated_square_area

                #refresh each surfaces area?
                case 'recalculate':
                    object_area = s.scatter5.estimate_square_area(eval_modifiers=eval_modifiers, get_selection=get_selection, update_property=True,)
                
                #refresh only if surface area has not been initiated yet (because is -1)
                case 'init_only':
                    object_area = s.scatter5.estimated_square_area
                    if (object_area==-1):
                        object_area = s.scatter5.estimate_square_area(eval_modifiers=eval_modifiers, get_selection=get_selection, update_property=True,)
                
                case _:
                    raise Exception(f"ERROR: get_surfaces_square_area(): passed wrong arg {evaluate}, must be str in 'gather|recalculate|init_only'")

            total_area += object_area
            continue

        return total_area
    
    is_using_surf : bpy.props.BoolProperty(
        default=True,
        description="read only! Some distribution method, when some settings are selected (ex: projbezline with no projections), are not using any surfaces. we need to keep track of this information. (Note that a system is considered as using surfaces, even if no surfaces are selected.)"
        )

    # 8888b.  88 .dP"Y8 888888 88""Yb 88 88""Yb 88   88 888888 88  dP"Yb  88b 88
    #  8I  Yb 88 `Ybo."   88   88__dP 88 88__dP 88   88   88   88 dP   Yb 88Yb88
    #  8I  dY 88 o.`Y8b   88   88"Yb  88 88""Yb Y8   8P   88   88 Yb   dP 88 Y88
    # 8888Y"  88 8bodP'   88   88  Yb 88 88oodP `YbodP'   88   88  YbodP  88  Y8

    ###################### This category of settings keyword is : "s_distribution"

    s_distribution_locked : bpy.props.BoolProperty(description=translate("Lock/Unlock Settings"),)

    # def get_s_distribution_main_features(self, availability_conditions=True,):
    #     return []

    # s_distribution_master_allow : bpy.props.BoolProperty( 
    #     name=translate("Master Toggle"),
    #     description=translate("Mute/Unmute all features of this category in one click"),
    #     default=True, 
    #     update=scattering.update_factory.factory("s_distribution_master_allow", sync_support=False,),
    #     )
    
    ########## ##########

    s_distribution_method : bpy.props.EnumProperty(
        name=translate("Distribution Method"),
        description=translate("Distribution algorithm.\nThe distribution algorithms you'll choose will completely change the aspect of your scatter. And some distribution methods will considerably impact the workflow. Please note that some distribution methods might have less or exclusive features"),
        default="random", 
        items=( ("random",        translate("Random"),        translate("The 'Random' distribution algorithm will randomly distribute instances from a chosen count or density"), "TOPATCH:W_DISTRANDOM", 1),
                ("clumping",      translate("Clump"),         translate("The 'Clump' distribution algorithm is a variation of the 'Random' distribution, with the added benefit of a secondary distribution (called children) generated near the first distribution (called parents distribution).\n• Note that this distribution method is offering additional scale/orientation options.\n• By default, each instance tangent will be aligned toward their parent (also known as the center of the clump)"), "TOPATCH:W_DISTCLUMP",2),
                ("verts",         translate("Per Vertex"),    translate("The 'Per Vertex' distribution, as its name suggests, will distribute one instance per surface(s) vertex"), "TOPATCH:W_DISTVERTS",3),
                ("faces",         translate("Per Face"),      translate("The 'Per Face' distribution, as its name suggests, will distribute one instance per surface(s) face.\n• This distribution method is offering an additional option: The ability to scale depending on the face size.\n• By default, each instance's normal will be aligned toward the normal of the face, and each instance's tangent will be aligned toward the first adjacent edge of the face"), "TOPATCH:W_DISTFACES",4),
                ("edges",         translate("Per Edge"),      translate("The 'Per Edge' distribution, as its name suggests, will distribute one instance per surface(s) edge.\n• This distribution has subtype modes, please read the subtype description for more information"), "TOPATCH:W_DISTEDGES",5),
                ("volume",        translate("In Volume"),     translate("Distribute instances inside the volume of the chosen surface(s) mesh (if it exists).\nNote: If your surface does not have a volume, we suggest to use the 'Random' distribution algorithm with the 'Offset' feature activated"), "TOPATCH:W_DISTVOLUME", 6),
                ("manual_all",    translate("Manual"),        translate("The 'Manual' distribution mode is a distribution workflow consisting of manually placing instances with the help of brushes that can influence your instances' density, scale, rotation or instancing id!\n\nPlease note that all procedural features can still be used with manual mode. If you'd like a manual-only experience, make sure to disable all procedural features that could interfere with the distributed instances density/scale/rotation."), "TOPATCH:W_DISTMANUAL",8),
                #("physics",       translate("Physics"),       translate("Physics distribution mode is a distribution workflow consisting of creating or interacting through instances via physics brushes. When using physics distribution, the procedural features will be highly restricted, as the physics distribution will define precise scale/rotation/instancing id attributes according to the calculated simulation"), "EXPERIMENTAL",9),
                ("random_stable", translate("Deform Stable"), translate("The 'Deform Stable' algorithm is a variation of the 'Random' distribution algorithm, with the added benefit of having a stable seed that will always stay consistent even on animated/deformed surface(s).\nThis distribution is based on the chosen UVMap of your surface(s).\bPlease make sure that the chosen UVMap attribute is shared across all your surfaces if you are using a multi-surface workflow"), "TOPATCH:W_DISTDEFORM",12),
                ("projbezarea",   translate("Bezier-Area"),   translate("The 'Bezier-Area' distribution algoritm will distribute instances on the surface of a chosen bezier-area (the chosen bezier curve must be closed).\n• By default, the distribution will be projected on your designated scatter-surface(s).\n• By default, each instance tangent will be aligned on the +Y axis of the bezier object, and each instance's normals will be aligned on its +Z axis"), "CURVE_BEZCIRCLE",13),
                ("projbezline",   translate("Bezier-Spline"), translate("The 'Bezier-Spline' distribution will distribute instances alongside a chosen spline object.\n• By default, the distribution will be projected on your designated scatter-surfaces.\n• By default, each instance orientation will be aligned following your curve tilt and tangent/normal\n• This distribution has subtype modes, please read the subtype description for more information"), "CURVE_BEZCURVE",14),
                ("projempties",   translate("Empties"),       translate("The 'Empties' distribution will assign instances on empties object contained within a chosen collection.\n• The instances will by default take the same orientation and scale of the empties"), "EMPTY_AXIS",15), #option spot or area light with localized radius
                #("projspot",       translate("Projected Spots"),   translate("TODO."), "SUZANNE",16), #collections of spots with passing info to geonode?? option spot or area light with localized radius
                # projopti? optimized global volumetric distribution near surface and in camera frustrum, then projected in surfaces
                # pixel? distribute from a given pattern projected on uv? then pass attributes from pattern rgb data for scale/rotation/alignment/instance id? 
                # clean? custom distribution methods that depends on instances
               ),
        update=scattering.update_factory.factory("s_distribution_method"),
        )
    # s_distribution_two_sided : bpy.props.BoolProperty(
    #     name=translate("Two Sided Distribution"),
    #     description=translate("Distribute on both face-sides of the emitting surface"),
    #     default= False, 
    #     update=scattering.update_factory.factory("s_distribution_two_sided"),
    #     )
    
    ########## ########## Random #wrong naming convention here... 

    s_distribution_space : bpy.props.EnumProperty(
        name=translate("Space"),
        description=translate("Distribution space.\nThe distribution density is always based on your surface area(s) in square-meter, and the calculation of this area can vary if we take transforms into consideration"),
        default="local", 
        items= ( ("local", translate("Local"), translate("Choose the 'Local' option if you'd like the density to stay stable even when your surface(s) transforms are changing"), "ORIENTATION_LOCAL",1 ),
                 ("global", translate("Global"), translate("Choose the 'Global' option if you'd like the density to stay consistent in world space. The density will be recalculated when your surface(s) scale transforms are changing"), "WORLD",2 ),
               ),
        update=scattering.update_factory.factory("s_distribution_space"),
        )
    s_distribution_is_count_method : bpy.props.EnumProperty(
        default="density", 
        items= ( ("density", translate("Density"), translate("Define how many instances should be distributed per square meter unit"),),
                 ("count", translate("Count"),  translate("Choose how many instances will be distributed in total (before any other features may affect this count).\nNote that the amount may be imprecise under 50 points"),),
               ),
        update=scattering.update_factory.factory("s_distribution_is_count_method"),
        )
    s_distribution_count : bpy.props.IntProperty(
        name=translate("Instance Count"),
        default=0,
        min=0,
        soft_max=1_000_000,
        max=99_999_999,
        update=scattering.update_factory.factory("s_distribution_count", delay_support=True,),
        )
    s_distribution_density : bpy.props.FloatProperty(
        name=translate("Instances /m²"), 
        description=translate("Choose the density of the distribution by defining a number of approximative instances per square meter area"),
        default=0, 
        min=0, 
        precision=3,
        update=scattering.update_factory.factory("s_distribution_density", delay_support=True,),
        )
    s_distribution_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        description=translate("Change this value to randomize the result.\n\nIn 3D graphics, a seed is a starting value used by a random number generator to produce a sequence of random-looking numbers. These numbers can control things like the position, rotation, or scale of objects in a scene. Using the same seed will always generate the same 'random' result, which helps keep things consistent when needed."),
        update=scattering.update_factory.factory("s_distribution_seed", delay_support=True,),
        )
    s_distribution_is_random_seed : bpy.props.BoolProperty( 
        name=translate("Randomize Seed"),
        description=translate("Randomize the value of the hereby seed property.\n\n• Note that pressing 'ALT' while clicking on this button will garantee the attribution of an unique seed value of this property for all selected-system(s)"),
        default=False,
        update=scattering.update_factory.factory("s_distribution_is_random_seed",),
        )
    s_distribution_limit_distance_allow : bpy.props.BoolProperty(
        name=translate("Limit Self-Collision"),
        description=translate("Limit the probability of having instances close to each other's origin point.\n\n• Note that the distribution might become more expensive to compute when this feature is enabled on large distributions"),
        default=False, 
        update=scattering.update_factory.factory("s_distribution_limit_distance_allow",),
        )
    s_distribution_limit_distance : bpy.props.FloatProperty(
        name=translate("Radial Distance"),
        description=translate("Avoid overlaps by defining the minimum distance between your scattered instances origin"),
        subtype="DISTANCE",
        default=0.2,
        min=0,
        precision=3,
        update=scattering.update_factory.factory("s_distribution_limit_distance", delay_support=True,),
        )
    ui_distribution_coef : bpy.props.FloatProperty( #Not supported by Preset
        name=translate("Quick-Math"),
        description=translate("Quickly execute math operation on the property above with the given coefficient, use the universal 'ALT' shortcut to execute the same operation on all selected system(s) simultaneously"),
        default=2,
        min=0,
        )

    ########## ########## Verts
    
    s_distribution_vfe_space : bpy.props.EnumProperty(
        name=translate("Space"),
        description=translate("Distribution space.\nWhile the distribution and default orientations of your instances are fixed, as it depends on your surface(s) mesh, the default scale of your instances might change depending how you consider their transforms"),
        default="local", 
        items= ( ("local", translate("Local"), translate("Choose the 'Local' option if you'd like the default scale of your instances to stay stable when the transforms of the object(s) you are scattering upon are changing"), "ORIENTATION_LOCAL",1 ),
                 ("global", translate("Global"), translate("Choose the 'Global' option if you'd like the default scale of your instances to stay consistent in world space. The scale will therefore be recalculated when your object(s) you are scattering upon are changing scales"), "WORLD",2 ),
               ),
        update=scattering.update_factory.factory("s_distribution_vfe_space"),
        )
    
    ########## ########## Faces

    ########## ########## Edges

    s_distribution_edges_selection_method : bpy.props.EnumProperty(
        name=translate("Selection"),
        description=translate("Distribution submethod.\nChoose on which edges the instances will spawn"),
        default="all", 
        items= (("all",         translate("All"),          translate("Spawn instances on every edges"), "VIEW_PERSPECTIVE",0),
                ("unconnected", translate("Un-Connected"), translate("Spawn instances only on edges that aren't connected to faces"), "UNLINKED",1),
                ("boundary",    translate("Boundary"),     translate("Spawn instances only on boundary edges"), "MOD_EDGESPLIT",2),
               ),
        update=scattering.update_factory.factory("s_distribution_edges_selection_method"),
        )
    s_distribution_edges_position_method : bpy.props.EnumProperty(
        name=translate("Position"),
        description=translate("Distribution submethod.\nChoose the default position & orientation of the instances depending on their assigned edge"),
        default= "center", 
        items= (("center",  translate("Center"), translate("The instances tangent will face toward the other vertex"), "TOPATCH:W_DISTEDGESMIDDLE", 0),
                ("start",  translate("Along"),  translate("The the instances normal will be oriented alongside the edge"), "TOPATCH:W_DISTEDGESSTART", 1),
               ),
        update=scattering.update_factory.factory("s_distribution_edges_position_method"),
        )

    ########## ########## Volume

    s_distribution_volume_space : bpy.props.EnumProperty(
        name=translate("Space"),
        description=translate("Distribution space.\nThe distribution density is based on the volumetric cubic area of your surface(s), and this area can be calculated differenctly based on its transforms"),
        default="local", 
        items= ( ("local", translate("Local"), translate("Choose the 'Local' option if you'd like the density to stay stable even when your surface(s) transforms are changing"), "ORIENTATION_LOCAL",1 ),
                 ("global", translate("Global"), translate("Choose the 'Global' option if you'd like the density to stay consistent in world space. The density will be recalculated when your surface(s) scale transforms are changing"), "WORLD",2 ),
               ),
        update=scattering.update_factory.factory("s_distribution_volume_space"),
        )
    s_distribution_volume_method : bpy.props.EnumProperty(
        name=translate("Space"),
        description=translate("Distribution submethod"),
        default="random", 
        items= (("random", translate("Random"), translate("Distribute instances randomly in the volume of the surface(s)"), "STICKY_UVS_DISABLE",0 ),
                ("grid", translate("Grid"), translate("Distribute instances in an orderly manner following a volumetric grid pattern"), "LIGHTPROBE_VOLUME",1 ),
               ),
        update=scattering.update_factory.factory("s_distribution_volume_method"),
        )
    s_distribution_volume_is_count_method : bpy.props.EnumProperty( #too buggy for current algo
        default="density", 
        items= ( ("density", translate("Density"), translate("Define how many instances should be distributed per square meter unit"),),
                 ("count", translate("Count"),  translate("Define how many instances should be distributed in total, before limit-distance or masks are computed"),),
               ),
        update=scattering.update_factory.factory("s_distribution_volume_is_count_method"),
        )
    s_distribution_volume_count : bpy.props.IntProperty( #too buggy for current algo
        name=translate("Instance Count"),
        default=0,
        min=0,
        soft_max=1_000_000,
        max=99_999_999,
        update=scattering.update_factory.factory("s_distribution_volume_count", delay_support=True,),
        )
    s_distribution_volume_density : bpy.props.FloatProperty(
        name=translate("Instances /m³"), 
        default=3,
        min=0,
        precision=3,
        update=scattering.update_factory.factory("s_distribution_volume_density", delay_support=True,),
        )
    s_distribution_volume_voxelsize : bpy.props.FloatProperty(
        name=translate("Volume Precision"),
        description=translate("In order to scatter in the volume of your surface(s) we will first need to create a volume using a voxelization operation. Define the precision of the voxels with this property"),
        default=0.3,
        min=0, 
        soft_min=0.075,
        precision=3,
        update=scattering.update_factory.factory("s_distribution_volume_voxelsize", delay_support=True,),
        )
    s_distribution_volume_grid_spacing : bpy.props.FloatVectorProperty(
        name=translate("Spacing"),
        description=translate("Define the spacing between the scatter volumetric grid pattern X/Y/Z axis"),
        subtype="XYZ",
        unit="LENGTH",
        min=0,
        soft_min=0.1,
        default=(0.3,0.3,0.3), 
        update=scattering.update_factory.factory("s_distribution_volume_grid_spacing", delay_support=True,),
        ) 
    s_distribution_volume_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        description=translate("Change this value to randomize the result.\n\nIn 3D graphics, a seed is a starting value used by a random number generator to produce a sequence of random-looking numbers. These numbers can control things like the position, rotation, or scale of objects in a scene. Using the same seed will always generate the same 'random' result, which helps keep things consistent when needed."),
        update=scattering.update_factory.factory("s_distribution_volume_seed", delay_support=True,),
        )
    s_distribution_volume_is_random_seed : bpy.props.BoolProperty( 
        name=translate("Randomize Seed"),
        description=translate("Randomize the value of the hereby seed property.\n\n• Note that pressing 'ALT' while clicking on this button will garantee the attribution of an unique seed value of this property for all selected-system(s)"),
        default=False,
        update=scattering.update_factory.factory("s_distribution_volume_is_random_seed",),
        )
    s_distribution_volume_limit_distance_allow : bpy.props.BoolProperty(
        name=translate("Limit Self-Collision"),
        description=translate("Limit the probability of having instances close to each other's origin point.\n\n• Note that the distribution might become more expensive to compute when this feature is enabled on large distributions"),
        default=False, 
        update=scattering.update_factory.factory("s_distribution_volume_limit_distance_allow",),
        )
    s_distribution_volume_limit_distance : bpy.props.FloatProperty(
        name=translate("Radial Distance"),
        description=translate("Avoid overlaps by defining the minimum distance between your scattered instances origin"),
        subtype="DISTANCE",
        default=0.5,
        min=0,
        precision=3,
        update=scattering.update_factory.factory("s_distribution_volume_limit_distance", delay_support=True,),
        )
    ui_distribution_volume_coef : bpy.props.FloatProperty( #Not supported by Preset
        name=translate("Quick-Math"),
        description=translate("Quickly execute math operation on the property above with the given coefficient, use the universal 'ALT' shortcut to execute the same operation on all selected system(s) homogeneously"),
        default=2,
        min=0,
        )

    ########## ########## Random Stable

    s_distribution_stable_uv_ptr : bpy.props.StringProperty(
        name=translate("UV-Map Pointer"),
        description=translate("Choose the UV Unfolding upon which the distribution algorithm will distribute the instances.")+"\n"+translate("When interacting with the pointer the plugin will search across surface(s) for shared Uvmaps\nThe pointer will be highlighted in a red color if the chosen attribute is missing from one of your surfaces"),
        default="UVMap",
        search=lambda s,c,e: get_surfs_shared_attrs(system=s, attr_type='uv', searchname=e,),
        search_options={'SUGGESTION','SORT'},
        update=scattering.update_factory.factory("s_distribution_stable_uv_ptr",),
        )
    s_distribution_stable_is_count_method : bpy.props.EnumProperty(
        default="density", 
        items= ( ("density", translate("Density"), translate("Define how many instances should be distributed per square meter unit"),),
                 ("count", translate("Count"),  translate("Define how many instances should be distributed in total, before limit-distance or masks are computed"),),
               ),
        update=scattering.update_factory.factory("s_distribution_stable_is_count_method"),
        )
    s_distribution_stable_count : bpy.props.IntProperty(
        name=translate("Instance Count"),
        default=0,
        min=0,
        soft_max=1_000_000,
        max=99_999_999,
        update=scattering.update_factory.factory("s_distribution_stable_count", delay_support=True,),
        )
    s_distribution_stable_density : bpy.props.FloatProperty(
        name=translate("Instance /UVm²"), 
        default=50, 
        min=0, 
        precision=3,
        update=scattering.update_factory.factory("s_distribution_stable_density", delay_support=True,),
        )
    s_distribution_stable_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        description=translate("Change this value to randomize the result.\n\nIn 3D graphics, a seed is a starting value used by a random number generator to produce a sequence of random-looking numbers. These numbers can control things like the position, rotation, or scale of objects in a scene. Using the same seed will always generate the same 'random' result, which helps keep things consistent when needed."),
        update=scattering.update_factory.factory("s_distribution_stable_seed", delay_support=True,),
        )
    s_distribution_stable_is_random_seed : bpy.props.BoolProperty( 
        name=translate("Randomize Seed"),
        description=translate("Randomize the value of the hereby seed property.\n\n• Note that pressing 'ALT' while clicking on this button will garantee the attribution of an unique seed value of this property for all selected-system(s)"),
        default=False,
        update=scattering.update_factory.factory("s_distribution_stable_is_random_seed",),
        )
    s_distribution_stable_limit_distance_allow : bpy.props.BoolProperty(
        name=translate("Limit Self-Collision"),
        description=translate("Limit the probability of having instances close to each other's origin point.\n\n• Note that the distribution might become more expensive to compute when this feature is enabled on large distributions"),
        default=False,
        update=scattering.update_factory.factory("s_distribution_stable_limit_distance_allow",),
        )
    s_distribution_stable_limit_distance : bpy.props.FloatProperty(
        name=translate("Radial Distance"),
        description=translate("Avoid overlaps by defining the minimum distance between your scattered instances origin"),
        default=0.02,
        min=0, 
        precision=3,
        update=scattering.update_factory.factory("s_distribution_stable_limit_distance", delay_support=True,),
        )
    ui_distribution_stable_coef : bpy.props.FloatProperty( #Not supported by Preset
        name=translate("Quick-Math"),
        description=translate("Quickly execute math operation on the property above with the given coefficient, use the universal 'ALT' shortcut to execute the same operation on all selected system(s) homogeneously"),
        default=2,
        min=0,
        )

    ########## ########## Project Bezier Area 
    
    s_distribution_projbezarea_curve_ptr : bpy.props.PointerProperty( #Not supported by Preset
        name=translate("Bezier-Curve Pointer"),
        description=translate("The instances will be distributed on the inner area of the chosen curve object. Make sure the splines are set to 'Cyclic U' in the 'Properties>Curve Data' panel"),
        type=bpy.types.Object,
        poll=lambda s,o: o.type=="CURVE",
        update=scattering.update_factory.factory("s_distribution_projbezarea_curve_ptr"),
        )
    s_distribution_projbezarea_space : bpy.props.EnumProperty(
        name=translate("Space"),
        description=translate("Distribution space.\nThe distribution density is always based on your bezier-area in square-meter, and the calculation of this area can vary if we take transforms into consideration"),
        default="global",
        items= ( ("local", translate("Local"), translate("Choose the 'Local' option if you'd like the density to stay stable even when your curve transforms are changing"), "ORIENTATION_LOCAL",1 ),
                 ("global", translate("Global"), translate("Choose the 'Global' option if you'd like the density to stay consistent in world space. The density will be recalculated when your curve scale transforms are changing"), "WORLD",2 ),
               ),
        update=scattering.update_factory.factory("s_distribution_projbezarea_space"),
        )
    s_distribution_projbezarea_density : bpy.props.FloatProperty(
        name=translate("Instances /m²"),
        description=translate("Instances distributed per square meter area on the inner region of the chosen curve object"),
        default=1,
        min=0,
        update=scattering.update_factory.factory("s_distribution_projbezarea_density", delay_support=True,),
        )
    s_distribution_projbezarea_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        description=translate("Change this value to randomize the result.\n\nIn 3D graphics, a seed is a starting value used by a random number generator to produce a sequence of random-looking numbers. These numbers can control things like the position, rotation, or scale of objects in a scene. Using the same seed will always generate the same 'random' result, which helps keep things consistent when needed."),
        update=scattering.update_factory.factory("s_distribution_projbezarea_seed", delay_support=True,),
        )
    s_distribution_projbezarea_is_random_seed : bpy.props.BoolProperty(
        name=translate("Randomize Seed"),
        description=translate("Randomize the value of the hereby seed property.\n\n• Note that pressing 'ALT' while clicking on this button will garantee the attribution of an unique seed value of this property for all selected-system(s)"),
        default=False,
        update=scattering.update_factory.factory("s_distribution_projbezarea_is_random_seed",),
        )
    s_distribution_projbezarea_limit_distance_allow : bpy.props.BoolProperty(
        name=translate("Limit Self-Collision"),
        description=translate("Limit the probability of having instances close to each other's origin point.\n\n• Note that the distribution might become more expensive to compute when this feature is enabled on large distributions"),
        default=False, 
        update=scattering.update_factory.factory("s_distribution_projbezarea_limit_distance_allow",),
        )
    s_distribution_projbezarea_limit_distance : bpy.props.FloatProperty(
        name=translate("Radial Distance"),
        description=translate("Avoid overlaps by defining the minimum distance between your scattered instances origin"),
        subtype="DISTANCE",
        default=0.2,
        min=0,
        precision=3,
        update=scattering.update_factory.factory("s_distribution_projbezarea_limit_distance", delay_support=True,),
        )
    ui_distribution_projbezarea_coef : bpy.props.FloatProperty( #Not supported by Preset
        name=translate("Quick-Math"),
        description=translate("Quickly execute math operation on the property above with the given coefficient, use the universal 'ALT' shortcut to execute the same operation on all selected system(s) homogeneously"),
        default=2,
        min=0,
        )
    s_distribution_projbezarea_projenabled : bpy.props.BoolProperty(
        name=translate("Project On Surface(s)"),
        description=translate("The distribution will be projected onto your chosen surface(s) following the chosen axis and projection reach. The distributed points will automatically inherit the surface(s) attributes thanks to an attribute transfer. Any projected points that didn't make any contact with a surface will be culled"),
        default=True,
        update=scattering.update_factory.factory("s_distribution_projbezarea_projenabled"),
        )
    s_distribution_projbezarea_projlength : bpy.props.FloatProperty(
        name=translate("Projection Reach"),
        description=translate("The maximal range the scattered points can reach on one of your surface(s). The points are projected from the bezier-area surfaces following the direction of the bezier-area location"),
        subtype="DISTANCE",
        default=9_000,
        min=0,
        precision=3,
        update=scattering.update_factory.factory("s_distribution_projbezarea_projlength", delay_support=True,),
        )
    s_distribution_projbezarea_projaxis : bpy.props.EnumProperty(
        name=translate("Axis"),
        description=translate("On which axis should the projection occur?"),
        default= "local",
        items= ( ("local", translate("Local Z"), "", "ORIENTATION_LOCAL",0 ),
                 ("global", translate("Global Z"), "", "WORLD",1 ),
               ),
        update=scattering.update_factory.factory("s_distribution_projbezarea_projaxis"),
        )
    
    ########## ########## Project Bezier Line
    
    s_distribution_projbezline_curve_ptr : bpy.props.PointerProperty( #Not supported by Preset
        name=translate("Bezier-Curve Pointer"),
        type=bpy.types.Object,
        poll=lambda s,o: o.type=="CURVE",
        update=scattering.update_factory.factory("s_distribution_projbezline_curve_ptr"),
        )
    s_distribution_projbezline_space : bpy.props.EnumProperty(
        name=translate("Space"),
        description=translate("Distribution space.\nThe distribution density is always based on your bezier-spline length/pathway width in meter unit, and the calculation of the density can vary if we take transforms into consideration"),
        default="global",
        items= ( ("local", translate("Local"), translate("Choose the 'Local' option if you'd like the density to stay stable even when your curve transforms are changing"), "ORIENTATION_LOCAL",1 ),
                 ("global", translate("Global"), translate("Choose the 'Global' option if you'd like the density to stay consistent in world space. The density will be recalculated when your curve scale transforms are changing"), "WORLD",2 ),
               ),
        update=scattering.update_factory.factory("s_distribution_projbezline_space"),
        )
    s_distribution_projbezline_method : bpy.props.EnumProperty(
        name=translate("Type"),
        description=translate("Distribution Submethod.\nChoose how the instances are distributed along your spline"),
        default="patharea",
        items= ( ("onspline", translate("On Spline"), translate("Distribute instances directly on the spline bezier geometry. You will then be able to randomize the offset or spread of the distribution"), "PARTICLE_POINT",0 ),
                 ("patharea", translate("Pathway Area"), translate("Distribute instances on an generated pathway alongside the spline. You will be able to define the pathway width in the settings below"), "MOD_THICKNESS",1 ),
               ),
        update=scattering.update_factory.factory("s_distribution_projbezline_method"),
        )
    s_distribution_projbezline_normal_method : bpy.props.EnumProperty(
        name=translate("Normal"),
        description=translate("Distribution Submethod.\nYou chose to generate a pathway alongside your spline, but how shall the pathway incline be oriented? (If you are unsure about this behavior, disable the projection to clearly see the pathway forming around your spline)"),
        default="data",
        items= ( ("data", translate("Tilt Data"), translate("Align your pathway to the direction of the spline tilt data"), "HANDLE_ALIGNED",0 ),
                 ("local", translate("Local Z"), translate("Align your pathway to the curve-object local Z axis"), "ORIENTATION_LOCAL",1 ),
                 ("global", translate("Global Z"), translate("Align your pathway toward the global world-space Z axis"), "WORLD",2 ),
                 ("surf", translate("Surface(s)"), translate("Align your pathway with the normal of the nearest surface(s)"), "SURFACE_NSURFACE",3 ),
               ),
        update=scattering.update_factory.factory("s_distribution_projbezline_normal_method"),
        )
    #TODO for later, will need to orient the spread/row/pathwayarea either on curve normal or local XY or global XY..
    s_distribution_projbezline_is_count_method : bpy.props.EnumProperty(
        default="density", 
        items= ( ("density", translate("Density"), translate("Define how many instances should be distributed per curve meter"),),
                 ("count", translate("Count"),  translate("Choose how many instances will be distributed in total (before any other features may affect this count).\nNote that the amount may be imprecise under 50 points"),),
               ),
        update=scattering.update_factory.factory("s_distribution_projbezline_is_count_method"),
        )
    s_distribution_projbezline_count : bpy.props.IntProperty(
        name=translate("Instance Count"),
        description=translate("Total Instances distributed on your bezier spline"),
        default=20,
        min=0,
        update=scattering.update_factory.factory("s_distribution_projbezline_count", delay_support=True,),
        )
    s_distribution_projbezline_onspline_density : bpy.props.FloatProperty(
        name=translate("Instances /m"),
        description=translate("Instances per spline meters"),
        default=1,
        min=0,
        update=scattering.update_factory.factory("s_distribution_projbezline_onspline_density", delay_support=True,),
        )
    s_distribution_projbezline_patharea_density : bpy.props.FloatProperty(
        name=translate("Instances /m²"),
        description=translate("Instances per spline area square meters"),
        default=5,
        min=0,
        update=scattering.update_factory.factory("s_distribution_projbezline_patharea_density", delay_support=True,),
        )
    s_distribution_projbezline_patharea_width : bpy.props.FloatProperty(
        name=translate("Width"),
        description=translate("The width of the pathway created alongside the spline"),
        subtype="DISTANCE",
        default=0.25,
        min=0,
        precision=3,
        update=scattering.update_factory.factory("s_distribution_projbezline_patharea_width", delay_support=True,),
        )
    s_distribution_projbezline_patharea_falloff : bpy.props.FloatProperty(
        name=translate("Transition"),
        description=translate("Define a falloff transition distance added right after the width distance"),
        subtype="DISTANCE",
        default=1.5,
        min=0,
        precision=3,
        update=scattering.update_factory.factory("s_distribution_projbezline_patharea_falloff", delay_support=True,),
        )
    s_distribution_projbezline_patharea_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        description=translate("Change this value to randomize the result.\n\nIn 3D graphics, a seed is a starting value used by a random number generator to produce a sequence of random-looking numbers. These numbers can control things like the position, rotation, or scale of objects in a scene. Using the same seed will always generate the same 'random' result, which helps keep things consistent when needed."),
        update=scattering.update_factory.factory("s_distribution_projbezline_patharea_seed", delay_support=True,),
        )
    s_distribution_projbezline_patharea_is_random_seed : bpy.props.BoolProperty(
        name=translate("Randomize Seed"),
        description=translate("Randomize the value of the hereby seed property.\n\n• Note that pressing 'ALT' while clicking on this button will garantee the attribution of an unique seed value of this property for all selected-system(s)"),
        default=False,
        update=scattering.update_factory.factory("s_distribution_projbezline_patharea_is_random_seed",),
        )
    s_distribution_projbezline_patharea_radiusinfl_allow : bpy.props.BoolProperty(
        name=translate("Spline Radius Influence"),
        description=translate("Allow the spline(s) radius data to influence the width of the generated pathway. (The curve radius can be drawn using pen pressure directly with the blender bezier drawing active tool, and can be modified within curve edit mode)"),
        default=False,
        update=scattering.update_factory.factory("s_distribution_projbezline_patharea_radiusinfl_allow"),
        )
    s_distribution_projbezline_patharea_radiusinfl_factor : bpy.props.FloatProperty(
        name=translate("Factor"),
        description=translate("An influence factor of an effect is a value that determines how strong the effect is. A higher factor means more impact, while lower factor means less"),
        default=1.0,
        soft_min=0, 
        precision=3,
        update=scattering.update_factory.factory("s_distribution_projbezline_patharea_radiusinfl_factor", delay_support=True,),
        )
    s_distribution_projbezline_randoff_allow : bpy.props.BoolProperty(
        name=translate("Randomize Distribution"),
        description=translate("Randomly offset the points following the bezier spline to give the distribution a more 'non-uniform' look"),
        default=False,
        update=scattering.update_factory.factory("s_distribution_projbezline_randoff_allow"),
        )
    s_distribution_projbezline_randoff_dist : bpy.props.FloatProperty(
        name=translate("Offset"),
        subtype="DISTANCE",
        default=0.5,
        soft_min=0, 
        precision=3,
        update=scattering.update_factory.factory("s_distribution_projbezline_randoff_dist", delay_support=True,),
        )
    s_distribution_projbezline_randoff_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        description=translate("Change this value to randomize the result.\n\nIn 3D graphics, a seed is a starting value used by a random number generator to produce a sequence of random-looking numbers. These numbers can control things like the position, rotation, or scale of objects in a scene. Using the same seed will always generate the same 'random' result, which helps keep things consistent when needed."),
        update=scattering.update_factory.factory("s_distribution_projbezline_randoff_seed", delay_support=True,),
        )
    s_distribution_projbezline_randoff_is_random_seed : bpy.props.BoolProperty(
        name=translate("Randomize Seed"),
        description=translate("Randomize the value of the hereby seed property.\n\n• Note that pressing 'ALT' while clicking on this button will garantee the attribution of an unique seed value of this property for all selected-system(s)"),
        default=False,
        update=scattering.update_factory.factory("s_distribution_projbezline_randoff_is_random_seed",),
        )
    s_distribution_projbezline_creatrow_allow : bpy.props.BoolProperty(
        name=translate("Create Rows"),
        description=translate("Duplicate your distribution by creating side rows aligned to the curve tilt"),
        default=False,
        update=scattering.update_factory.factory("s_distribution_projbezline_creatrow_allow"),
        )
    s_distribution_projbezline_creatrow_rows : bpy.props.IntProperty(
        name=translate("Row Count"),
        description=translate("Number of duplicated rows offsetted on the side(s)"),
        default=1,
        min=1,
        soft_max=100,
        update=scattering.update_factory.factory("s_distribution_projbezline_creatrow_rows", delay_support=True,),
        )
    s_distribution_projbezline_creatrow_dist : bpy.props.FloatProperty(
        name=translate("Offset"),
        description=translate("Offset distance between each side rows"),
        subtype="DISTANCE",
        default=1,
        precision=3,
        update=scattering.update_factory.factory("s_distribution_projbezline_creatrow_dist", delay_support=True,),
        )
    s_distribution_projbezline_creatrow_shift : bpy.props.FloatProperty(
        name=translate("Shift"),
        description=translate("Shift the side rows lengthwise"),
        subtype="DISTANCE",
        default=0,
        precision=3,
        update=scattering.update_factory.factory("s_distribution_projbezline_creatrow_shift", delay_support=True,),
        )
    s_distribution_projbezline_creatrow_dir : bpy.props.EnumProperty(
        name=translate("Direction"),
        description=translate("On which direction of the axis should the spread occur?"),
        default= "leftright",
        items= ( ("left", translate("Left"), translate("The spread will only occur on the left sides of the spline"), "BACK",0 ),
                 ("right", translate("Right"), translate("The spread will only occur on the right sides of the spline"), "FORWARD",1 ),
                 ("leftright", translate("Left and Right"), translate("The spread will only occur on both left and right sides of the spline"), "ARROW_LEFTRIGHT",2 ),
               ),
        update=scattering.update_factory.factory("s_distribution_projbezline_creatrow_dir"),
        )
    s_distribution_projbezline_spread_allow : bpy.props.BoolProperty(
        name=translate("Spread Distribution"),
        description=translate("Spread the distribution around the curve"),
        default=False,
        update=scattering.update_factory.factory("s_distribution_projbezline_spread_allow"),
        )
    s_distribution_projbezline_spread_method : bpy.props.EnumProperty(
        name=translate("Axis"),
        description=translate("How do you wish the distribution to be spread near the bezier spline?"),
        default= "sides",
        items= ( ("sides", translate("Sides"), translate("Spread the distribution only on the sides of the curve"), "EMPTY_ARROWS",0 ),
                 ("around", translate("Around"), translate("Spread the distribution all around the curve"), "FILE_REFRESH",1 ),
               ),
        update=scattering.update_factory.factory("s_distribution_projbezline_spread_method"),
        )
    s_distribution_projbezline_spread_dir : bpy.props.EnumProperty(
        name=translate("Direction"),
        description=translate("On which direction of the axis should the spread occur?"),
        default= "leftright",
        items= ( ("left", translate("Left"), translate("The spread will only occur on the left sides of the spline"), "BACK",0 ),
                 ("right", translate("Right"), translate("The spread will only occur on the right sides of the spline"), "FORWARD",1 ),
                 ("leftright", translate("Left and Right"), translate("The spread will only occur on both left and right sides of the spline"), "ARROW_LEFTRIGHT",2 ),
                 ("up", translate("Up"), translate("The spread will only occur on the upper sides of the spline"), "SORT_DESC",3 ),
                 ("down", translate("Down"), translate("The spread will only occur on the lower sides of the spline"), "SORT_ASC",4 ),
                 ("updown", translate("Up and Down"), translate("The spread will only occur on both up and lower sides of the spline"), "MOD_LENGTH",5 ),
               ),
        update=scattering.update_factory.factory("s_distribution_projbezline_spread_dir"),
        )
    # s_distribution_projbezline_spread_offset : bpy.props.FloatProperty(
    #     name="NOT IN GUI",
    #     description=translate("Offset distance of the spread before the transition starts"),
    #     subtype="DISTANCE",
    #     default=0,
    #     precision=3,
    #     update=scattering.update_factory.factory("s_distribution_projbezline_spread_offset", delay_support=True,),
    #     )
    s_distribution_projbezline_spread_falloff : bpy.props.FloatProperty(
        name=translate("Offset"),
        description=translate("Spread falloff transition distance"),
        subtype="DISTANCE",
        default=0.5,
        precision=3,
        update=scattering.update_factory.factory("s_distribution_projbezline_spread_falloff", delay_support=True,),
        )
    s_distribution_projbezline_spread_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        description=translate("Change this value to randomize the result.\n\nIn 3D graphics, a seed is a starting value used by a random number generator to produce a sequence of random-looking numbers. These numbers can control things like the position, rotation, or scale of objects in a scene. Using the same seed will always generate the same 'random' result, which helps keep things consistent when needed."),
        update=scattering.update_factory.factory("s_distribution_projbezline_spread_seed", delay_support=True,),
        )
    s_distribution_projbezline_spread_is_random_seed : bpy.props.BoolProperty(
        name=translate("Randomize Seed"),
        description=translate("Randomize the value of the hereby seed property.\n\n• Note that pressing 'ALT' while clicking on this button will garantee the attribution of an unique seed value of this property for all selected-system(s)"),
        default=False,
        update=scattering.update_factory.factory("s_distribution_projbezline_spread_is_random_seed",),
        )
    #remap
    s_distribution_projbezline_fallremap_allow : bpy.props.BoolProperty(
        name=translate("Transition Control"),
        description=translate("Control the transition falloff by remapping the values with a curve-map graph or by adding a procedural noise transition to this falloff.\n\n• Please note that this feature assumes there is a transition distance to work with"),
        default=False, 
        update=scattering.update_factory.factory("s_distribution_projbezline_fallremap_allow",),
        )
    s_distribution_projbezline_fallremap_revert : bpy.props.BoolProperty(
        name=translate("Reverse Transition"),
        description=translate("Reverse the transition. This option will in fact remap the values from '0-1' to '1-0'"),
        default=False,
        update=scattering.update_factory.factory("s_distribution_projbezline_fallremap_revert",),
        )
    s_distribution_projbezline_fallnoisy_strength : bpy.props.FloatProperty(
        name=translate("Strength"), 
        description=translate("Combine the distance transition with a noise pattern. Great to make the transition look less uniform and more natural. Set this value to 0 to disable the noise overlay entirely"),
        default=0, min=0, max=5, precision=3,
        update=scattering.update_factory.factory("s_distribution_projbezline_fallnoisy_strength", delay_support=True,),
        )
    s_distribution_projbezline_fallnoisy_space : bpy.props.EnumProperty(
        name="NOT IN GUI",
        default="local",
        items= ( ("local", translate("Local"), "", "ORIENTATION_LOCAL",0 ),
                 ("global", translate("Global"), "", "WORLD",1 ),
               ),
        update=scattering.update_factory.factory("s_distribution_projbezline_fallnoisy_space"),
        )
    s_distribution_projbezline_fallnoisy_scale : bpy.props.FloatProperty(
        name=translate("Scale"),
        description=translate("The scale of a procedural texture.\n• A value of '0.01' will creates a large noise pattern.\n• A value of '10.0' will create a small pattern"),
        default=0.5, min=0, soft_max=2, precision=3, 
        update=scattering.update_factory.factory("s_distribution_projbezline_fallnoisy_scale", delay_support=True,),
        )
    s_distribution_projbezline_fallnoisy_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        description=translate("Change this value to randomize the result.\n\nIn 3D graphics, a seed is a starting value used by a random number generator to produce a sequence of random-looking numbers. These numbers can control things like the position, rotation, or scale of objects in a scene. Using the same seed will always generate the same 'random' result, which helps keep things consistent when needed."),
        update=scattering.update_factory.factory("s_distribution_projbezline_fallnoisy_seed", delay_support=True,)
        )
    s_distribution_projbezline_fallnoisy_is_random_seed : bpy.props.BoolProperty(
        name=translate("Randomize Seed"),
        description=translate("Randomize the value of the hereby seed property.\n\n• Note that pressing 'ALT' while clicking on this button will garantee the attribution of an unique seed value of this property for all selected-system(s)"),
        default=False,
        update=scattering.update_factory.factory("s_distribution_projbezline_fallnoisy_is_random_seed",),
        )
    s_distribution_projbezline_fallremap_data : bpy.props.StringProperty(
        set=scattering.update_factory.fallremap_setter("s_distribution_projbezline.fallremap"),
        get=scattering.update_factory.fallremap_getter("s_distribution_projbezline.fallremap"),
        )
    s_distribution_projbezline_limit_distance_allow : bpy.props.BoolProperty(
        name=translate("Limit Self-Collision"),
        description=translate("Limit the probability of having instances close to each other's origin point.\n\n• Note that the distribution might become more expensive to compute when this feature is enabled on large distributions"),
        default=False, 
        update=scattering.update_factory.factory("s_distribution_projbezline_limit_distance_allow",),
        )
    s_distribution_projbezline_limit_distance : bpy.props.FloatProperty(
        name=translate("Radial Distance"),
        description=translate("Avoid overlaps by defining the minimum distance between your scattered instances origin"),
        subtype="DISTANCE",
        default=0.5,
        min=0, 
        precision=3,
        update=scattering.update_factory.factory("s_distribution_projbezline_limit_distance", delay_support=True,),
        )
    ui_distribution_projbezline_coef : bpy.props.FloatProperty( #Not supported by Preset
        name=translate("Quick-Math"),
        description=translate("Quickly execute math operation on the property above with the given coefficient, use the universal 'ALT' shortcut to execute the same operation on all selected system(s) homogeneously"),
        default=2,
        min=0,
        )
    s_distribution_projbezline_projenabled : bpy.props.BoolProperty(
        name=translate("Project On Surface(s)"),
        description=translate("The distribution will be projected onto your chosen surface(s) following the chosen axis and projection reach. The distributed points will automatically inherit the surface(s) attributes thanks to an attribute transfer. Any projected points that didn't make any contact with a surface will be culled"),
        default=True,
        update=scattering.update_factory.factory("s_distribution_projbezline_projenabled"),
        )
    s_distribution_projbezline_projlength : bpy.props.FloatProperty(
        name=translate("Projection Reach"),
        description=translate("The maximal range the scattered points can reach on one of your surface(s). The points are projected from the bezier-area surfaces following the direction of the bezier-area location"),
        subtype="DISTANCE",
        default=9_000,
        min=0,
        precision=3,
        update=scattering.update_factory.factory("s_distribution_projbezline_projlength", delay_support=True,),
        )
    s_distribution_projbezline_projaxis : bpy.props.EnumProperty(
        name=translate("Axis"),
        description=translate("On which axis should the projection occur?"),
        default= "local",
        items= ( ("local", translate("Local Z"), "", "ORIENTATION_LOCAL",0 ),
                 ("global", translate("Global Z"), "", "WORLD",1 ),
               ),
        update=scattering.update_factory.factory("s_distribution_projbezline_projaxis"),
        )
    
    ########## ########## Project Empties
    
    s_distribution_projempties_coll_ptr : bpy.props.StringProperty(
        name=translate("Collection Pointer"),
        description=translate("Choose a collection containing empty objects"),
        search=lambda s,c,e: set(col.name for col in bpy.data.collections if (e in col.name)),
        search_options={'SUGGESTION','SORT'},
        update=scattering.update_factory.factory("s_distribution_projempties_coll_ptr"),
        )
    s_distribution_projempties_empty_only : bpy.props.BoolProperty(
        name=translate("Only consider Empties"),
        description=translate("Only spawn instances on object type considered as 'empties'"),
        default=True, 
        update=scattering.update_factory.factory("s_distribution_projempties_empty_only",),
        )     
    s_distribution_projempties_projenabled : bpy.props.BoolProperty(
        name=translate("Project On Surface(s)"),
        description=translate("The distribution will be projected onto your chosen surface(s) following the chosen axis and projection reach. The distributed points will automatically inherit the surface(s) attributes thanks to an attribute transfer. Any projected points that didn't make any contact with a surface will be culled"),
        default=False,
        update=scattering.update_factory.factory("s_distribution_projempties_projenabled"),
        )
    s_distribution_projempties_projlength : bpy.props.FloatProperty(
        name=translate("Projection Reach"),
        description=translate("The maximal range the scattered points can reach on one of your surface(s). The points are projected from the bezier-area surfaces following the direction of the bezier-area location"),
        subtype="DISTANCE",
        default=9_000,
        min=0,
        precision=3,
        update=scattering.update_factory.factory("s_distribution_projempties_projlength", delay_support=True,),
        )
    s_distribution_projempties_projaxis : bpy.props.EnumProperty(
        name=translate("Axis"),
        description=translate("On which axis should the projection occur?"),
        default= "local",
        items= ( ("local", translate("Local Z"), "", "ORIENTATION_LOCAL",0 ),
                 ("global", translate("Global Z"), "", "WORLD",1 ),
               ),
        update=scattering.update_factory.factory("s_distribution_projempties_projaxis"),
        )
    
    ########## ########## Clumps 

    s_distribution_clump_space : bpy.props.EnumProperty(
        name=translate("Space"),
        description=translate("Distribution space.\nThe distribution density is always based on your surface area(s) in square-meter, and the calculation of this area can vary if we take transforms into consideration"),
        default="local",
        items= ( ("local", translate("Local"), translate("Choose the 'Local' option if you'd like the density to stay stable even when your surface(s) transforms are changing"), "ORIENTATION_LOCAL",1 ),
                 ("global", translate("Global"), translate("Choose the 'Global' option if you'd like the density to stay consistent in world space. The density will be recalculated when your surface(s) scale transforms are changing"), "WORLD",2 ),
               ),
        update=scattering.update_factory.factory("s_distribution_clump_space"),
        )
    s_distribution_clump_density : bpy.props.FloatProperty(
        name=translate("Clump /m²"), 
        default=0.15,
        min=0, 
        update=scattering.update_factory.factory("s_distribution_clump_density", delay_support=True,),
        )
    s_distribution_clump_limit_distance_allow : bpy.props.BoolProperty(
        name=translate("Limit Self-Collision"),
        description=translate("Limit the probability of having instances close to each other's origin point.\n\n• Note that the distribution might become more expensive to compute when this feature is enabled on large distributions"),
        default=False, 
        update=scattering.update_factory.factory("s_distribution_clump_limit_distance_allow",),
        )
    s_distribution_clump_limit_distance : bpy.props.FloatProperty(
        name=translate("Radial Distance"),
        description=translate("Avoid overlaps by defining the minimum distance between your scattered instances origin"),
        subtype="DISTANCE",
        default=0,
        min=0,
        precision=3,
        update=scattering.update_factory.factory("s_distribution_clump_limit_distance", delay_support=True,),
        )
    s_distribution_clump_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        description=translate("Change this value to randomize the result.\n\nIn 3D graphics, a seed is a starting value used by a random number generator to produce a sequence of random-looking numbers. These numbers can control things like the position, rotation, or scale of objects in a scene. Using the same seed will always generate the same 'random' result, which helps keep things consistent when needed."),
        update=scattering.update_factory.factory("s_distribution_clump_seed", delay_support=True,),
        )
    s_distribution_clump_is_random_seed : bpy.props.BoolProperty(
        name=translate("Randomize Seed"),
        description=translate("Randomize the value of the hereby seed property.\n\n• Note that pressing 'ALT' while clicking on this button will garantee the attribution of an unique seed value of this property for all selected-system(s)"),
        default=False,
        update=scattering.update_factory.factory("s_distribution_clump_is_random_seed",),
        )
    s_distribution_clump_max_distance : bpy.props.FloatProperty(
        name=translate("Min Distance"),
        description=translate("Minimal reaching distance of the clump area before a transition distance starts"),
        subtype="DISTANCE",
        default=0.7,
        min=0,
        precision=3,
        update=scattering.update_factory.factory("s_distribution_clump_max_distance", delay_support=True,),
        )
    s_distribution_clump_falloff : bpy.props.FloatProperty(
        name=translate("Transition"),
        description=translate("Falloff transition distance of the clump area"),
        subtype="DISTANCE",
        default=0.5,
        min=0,
        precision=3,
        update=scattering.update_factory.factory("s_distribution_clump_falloff", delay_support=True,),
        )
    s_distribution_clump_random_factor : bpy.props.FloatProperty(
        name=translate("Random"),
        description=translate("Randomize the distance reached by multiplying the distance by a random float, ranging from 1 to a chosen ratio"),
        default=1,
        min=0,
        soft_max=10,
        update=scattering.update_factory.factory("s_distribution_clump_random_factor", delay_support=True,),
        )
    #child
    s_distribution_clump_children_density : bpy.props.FloatProperty(
        name=translate("Children /m²"), 
        default=15,
        min=0,
        update=scattering.update_factory.factory("s_distribution_clump_children_density", delay_support=True,),
        )
    s_distribution_clump_children_limit_distance_allow : bpy.props.BoolProperty(
        name=translate("Limit Self-Collision"),
        description=translate("Limit the probability of having instances close to each other's origin point.\n\n• Note that the distribution might become more expensive to compute when this feature is enabled on large distributions"),
        default=False, 
        update=scattering.update_factory.factory("s_distribution_clump_children_limit_distance_allow",),
        )
    s_distribution_clump_children_limit_distance : bpy.props.FloatProperty(
        name=translate("Radial Distance"),
        description=translate("Avoid overlaps by defining the minimum distance between your scattered instances origin"),
        subtype="DISTANCE",
        default=0.2, 
        min=0, 
        precision=3,
        update=scattering.update_factory.factory("s_distribution_clump_children_limit_distance", delay_support=True,),
        )
    s_distribution_clump_children_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        description=translate("Change this value to randomize the result.\n\nIn 3D graphics, a seed is a starting value used by a random number generator to produce a sequence of random-looking numbers. These numbers can control things like the position, rotation, or scale of objects in a scene. Using the same seed will always generate the same 'random' result, which helps keep things consistent when needed."),
        update=scattering.update_factory.factory("s_distribution_clump_children_seed", delay_support=True,),
        )
    s_distribution_clump_children_is_random_seed : bpy.props.BoolProperty(
        name=translate("Randomize Seed"),
        description=translate("Randomize the value of the hereby seed property.\n\n• Note that pressing 'ALT' while clicking on this button will garantee the attribution of an unique seed value of this property for all selected-system(s)"),
        default=False,
        update=scattering.update_factory.factory("s_distribution_clump_children_is_random_seed",),
        )
    #remap
    s_distribution_clump_fallremap_allow : bpy.props.BoolProperty(
        name=translate("Transition Control"),
        description=translate("Control the transition falloff by remapping the values with a curve-map graph or by adding a procedural noise transition to this falloff.\n\n• Please note that this feature assumes there is a transition distance to work with"),
        default=False, 
        update=scattering.update_factory.factory("s_distribution_clump_fallremap_allow",),
        )
    s_distribution_clump_fallremap_revert : bpy.props.BoolProperty(
        name=translate("Reverse Transition"),
        description=translate("Reverse the transition. This option will in fact remap the values from '0-1' to '1-0'"),
        default=False,
        update=scattering.update_factory.factory("s_distribution_clump_fallremap_revert",),
        )
    s_distribution_clump_fallnoisy_strength : bpy.props.FloatProperty(
        name=translate("Strength"), 
        description=translate("Combine the distance transition with a noise pattern. Great to make the transition look less uniform and more natural. Set this value to 0 to disable the noise overlay entirely"),
        default=0, min=0, max=5, precision=3,
        update=scattering.update_factory.factory("s_distribution_clump_fallnoisy_strength", delay_support=True,),
        )
    s_distribution_clump_fallnoisy_space : bpy.props.EnumProperty(
        name="NOT IN GUI",
        default="local",
        items= ( ("local", translate("Local"), "", "ORIENTATION_LOCAL",0 ),
                 ("global", translate("Global"), "", "WORLD",1 ),
               ),
        update=scattering.update_factory.factory("s_distribution_clump_fallnoisy_space"),
        )
    s_distribution_clump_fallnoisy_scale : bpy.props.FloatProperty(
        name=translate("Scale"),
        description=translate("The scale of a procedural texture.\n• A value of '0.01' will creates a large noise pattern.\n• A value of '10.0' will create a small pattern"),
        default=0.5, min=0, soft_max=2, precision=3, 
        update=scattering.update_factory.factory("s_distribution_clump_fallnoisy_scale", delay_support=True,),
        )
    s_distribution_clump_fallnoisy_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        description=translate("Change this value to randomize the result.\n\nIn 3D graphics, a seed is a starting value used by a random number generator to produce a sequence of random-looking numbers. These numbers can control things like the position, rotation, or scale of objects in a scene. Using the same seed will always generate the same 'random' result, which helps keep things consistent when needed."),
        update=scattering.update_factory.factory("s_distribution_clump_fallnoisy_seed", delay_support=True,),
        )
    s_distribution_clump_fallnoisy_is_random_seed : bpy.props.BoolProperty(
        name=translate("Randomize Seed"),
        description=translate("Randomize the value of the hereby seed property.\n\n• Note that pressing 'ALT' while clicking on this button will garantee the attribution of an unique seed value of this property for all selected-system(s)"),
        default=False,
        update=scattering.update_factory.factory("s_distribution_clump_fallnoisy_is_random_seed",),
        )
    s_distribution_clump_fallremap_data : bpy.props.StringProperty(
        set=scattering.update_factory.fallremap_setter("s_distribution_clump.fallremap"),
        get=scattering.update_factory.fallremap_getter("s_distribution_clump.fallremap"),
        )

    # 8888b.  888888 88b 88 .dP"Y8 88 888888 Yb  dP     8b    d8    db    .dP"Y8 88  dP .dP"Y8
    #  8I  Yb 88__   88Yb88 `Ybo." 88   88    YbdP      88b  d88   dPYb   `Ybo." 88odP  `Ybo."
    #  8I  dY 88""   88 Y88 o.`Y8b 88   88     8P       88YbdP88  dP__Yb  o.`Y8b 88"Yb  o.`Y8b
    # 8888Y"  888888 88  Y8 8bodP' 88   88    dP        88 YY 88 dP""""Yb 8bodP' 88  Yb 8bodP'

    ###################### This category of settings keyword is : "s_mask"
    ###################### this category is Not supported by Preset
    ###################### Same set of properties for groups

    s_mask_locked : bpy.props.BoolProperty(description=translate("Lock/Unlock Settings"),)

    def get_s_mask_main_features(self, availability_conditions=True,):
        r = ["s_mask_vg_allow", "s_mask_vcol_allow", "s_mask_bitmap_allow", "s_mask_curve_allow", "s_mask_boolvol_allow","s_mask_upward_allow", "s_mask_material_allow",]
        if (not availability_conditions):
            return r
        if (self.s_distribution_method=="volume" or not self.is_using_surf):
            return ["s_mask_curve_allow", "s_mask_boolvol_allow","s_mask_upward_allow",]
        return r

    s_mask_master_allow : bpy.props.BoolProperty( 
        name=translate("Master Toggle"),
        description=translate("Mute/Unmute all features of this category in one click"),
        default=True, 
        update=scattering.update_factory.factory("s_mask_master_allow", sync_support=False,),
        )

    ########## ########## Vgroups

    s_mask_vg_allow : bpy.props.BoolProperty( 
        name=translate("Vertex-Group Mask"),
        description=translate("Mask-out instances depending on their position on the areas affected by a chosen vertex-group attribute.")+"\n\n"+translate("• Please note that 'vertex' attributes rely on your surfaces geometries, the more your surfaces are dense in vertices, the more you will be able to paint with precision"),
        default=False, 
        update=scattering.update_factory.factory("s_mask_vg_allow"),
        )
    s_mask_vg_ptr : bpy.props.StringProperty(
        name=translate("Vertex-Group Pointer"),
        description=translate("Search across all your surface(s) for shared vertex-group.\nWe will highlight the pointer in red if the attribute is not shared across your surface(s)"),
        search=lambda s,c,e: get_surfs_shared_attrs(system=s, attr_type='vg', searchname=e,),
        search_options={'SUGGESTION','SORT'},
        update=scattering.update_factory.factory("s_mask_vg_ptr"),
        )
    s_mask_vg_revert : bpy.props.BoolProperty(
        name=translate("Reverse"),
        description=translate("Reverse the influence of this mask"),
        update=scattering.update_factory.factory("s_mask_vg_revert"),
        )

    ########## ########## VColors
    
    s_mask_vcol_allow : bpy.props.BoolProperty( 
        name=translate("Vertex-Color Mask"), 
        description=translate("Mask-out instances depending on their position on the areas affected by a chosen color-attribute.")+"\n\n"+translate("• Please note that 'vertex' attributes rely on your surfaces geometries, the more your surfaces are dense in vertices, the more you will be able to paint with precision"),
        default=False, 
        update=scattering.update_factory.factory("s_mask_vcol_allow"),
        )
    s_mask_vcol_ptr : bpy.props.StringProperty(
        name=translate("Color-Attribute Pointer"),
        description=translate("Search across all your surface(s) for shared color attributes.\nWe will highlight the pointer in red if the attribute is not shared across your surface(s)"),
        search=lambda s,c,e: get_surfs_shared_attrs(system=s, attr_type='vcol', searchname=e,),
        search_options={'SUGGESTION','SORT'},
        update=scattering.update_factory.factory("s_mask_vcol_ptr"),
        )
    s_mask_vcol_revert : bpy.props.BoolProperty(
        name=translate("Reverse"),
        description=translate("Reverse the influence of this mask"),
        update=scattering.update_factory.factory("s_mask_vcol_revert"),
        )
    s_mask_vcol_color_sample_method : bpy.props.EnumProperty(
        name=translate("Color Sampling"),
        description=translate("Define how to translate the RGBA color values into a mask that will influence your distribution"),
        default="id_greyscale", 
        items=( ("id_greyscale", translate("Greyscale"), translate("Combine all colors into a black and white mask"), "NONE", 0,),
                ("id_red", translate("Red Channel"), translate("Only consider the Red channel as a mask"), "NONE", 1,),
                ("id_green", translate("Green Channel"), translate("Only consider the Green channel as a mask"), "NONE", 2,),
                ("id_blue", translate("Blue Channel"), translate("Only consider the Blue channel as a mask"), "NONE", 3,),
                ("id_black", translate("Pure Black"), translate("Only the areas containing a pure black color will be masked"), "NONE", 4,),
                ("id_white", translate("Pure White"), translate("Only the areas containing a pure white color will be masked"), "NONE", 5,),
                ("id_picker", translate("Color ID"), translate("Only the areas containing a color matching the color of your choice will be masked"), "NONE", 6,),
                ("id_hue", translate("Hue"), translate("Only consider the Hue channel as a mask, when converting the RGB colors to HSV values"), "NONE", 7,),
                ("id_saturation", translate("Saturation"), translate("Only consider the Saturation channel as a maskn when converting the RGB colors to HSV values"), "NONE", 8,),
                ("id_value", translate("Value"), translate("Only consider the Value channel as a mask, when converting the RGB colors to HSV values"), "NONE", 9,),
                ("id_lightness", translate("Lightness"), translate("Only consider the Lightness channel as a mask, when converting the RGB colors to HSL values"), "NONE", 10,),
                ("id_alpha", translate("Alpha Channel"), translate("Only consider the Alpha channel as a mask"), "NONE", 11,),
              ),
        update=scattering.update_factory.factory("s_mask_vcol_color_sample_method"),
        )
    s_mask_vcol_id_color_ptr : bpy.props.FloatVectorProperty(
        name=translate("ID Value"),
        description=translate("The areas containing this color will be considered as a mask"),
        subtype="COLOR",
        min=0,
        max=1,
        default=(1,0,0), 
        update=scattering.update_factory.factory("s_mask_vcol_id_color_ptr", delay_support=True,),
        ) 

    ########## ########## Bitmap 

    s_mask_bitmap_allow : bpy.props.BoolProperty( 
        name=translate("Image Mask"), 
        description=translate("Mask-out instances depending on their position on the areas affected by an image projected on a given UVMap.\n\n• Don't forget to save the image in your blend file! Newly created image data might not be packed in your blendfile by default"),
        default=False, 
        update=scattering.update_factory.factory("s_mask_bitmap_allow"),
        )
    s_mask_bitmap_uv_ptr : bpy.props.StringProperty(
        name=translate("UV-Map Pointer"),
        description=translate("When interacting with the pointer the plugin will search across surface(s) for shared Uvmaps\nThe pointer will be highlighted in a red color if the chosen attribute is missing from one of your surfaces"),
        default="UVMap",
        search=lambda s,c,e: get_surfs_shared_attrs(system=s, attr_type='uv', searchname=e,),
        search_options={'SUGGESTION','SORT'},
        update=scattering.update_factory.factory("s_mask_bitmap_uv_ptr"),
        )
    s_mask_bitmap_ptr : bpy.props.StringProperty(
        name=translate("Image Pointer"),
        search=lambda s,c,e: set(img.name for img in bpy.data.images if (e in img.name)),
        search_options={'SUGGESTION','SORT'},
        update=scattering.update_factory.factory("s_mask_bitmap_ptr"),
        )
    s_mask_bitmap_revert : bpy.props.BoolProperty(
        name=translate("Reverse"),
        description=translate("Reverse the influence of this mask"),
        update=scattering.update_factory.factory("s_mask_bitmap_revert"),
        )
    s_mask_bitmap_color_sample_method : bpy.props.EnumProperty(
        name=translate("Color Sampling"),
        description=translate("Define how to translate the RGBA color values into a mask that will influence your distribution"),
        default="id_greyscale",
        items=( ("id_greyscale", translate("Greyscale"), translate("Combine all colors into a black and white mask"), "NONE", 0,),
                ("id_red", translate("Red Channel"), translate("Only consider the Red channel as a mask"), "NONE", 1,),
                ("id_green", translate("Green Channel"), translate("Only consider the Green channel as a mask"), "NONE", 2,),
                ("id_blue", translate("Blue Channel"), translate("Only consider the Blue channel as a mask"), "NONE", 3,),
                ("id_black", translate("Pure Black"), translate("Only the areas containing a pure black color will be masked"), "NONE", 4,),
                ("id_white", translate("Pure White"), translate("Only the areas containing a pure white color will be masked"), "NONE", 5,),
                ("id_picker", translate("Color ID"), translate("Only the areas containing a color matching the color of your choice will be masked"), "NONE", 6,),
                ("id_hue", translate("Hue"), translate("Only consider the Hue channel as a mask, when converting the RGB colors to HSV values"), "NONE", 7,),
                ("id_saturation", translate("Saturation"), translate("Only consider the Saturation channel as a maskn when converting the RGB colors to HSV values"), "NONE", 8,),
                ("id_value", translate("Value"), translate("Only consider the Value channel as a mask, when converting the RGB colors to HSV values"), "NONE", 9,),
                ("id_lightness", translate("Lightness"), translate("Only consider the Lightness channel as a mask, when converting the RGB colors to HSL values"), "NONE", 10,),
                ("id_alpha", translate("Alpha Channel"), translate("Only consider the Alpha channel as a mask"), "NONE", 11,),
              ),
        update=scattering.update_factory.factory("s_mask_bitmap_color_sample_method"),
        )
    s_mask_bitmap_id_color_ptr : bpy.props.FloatVectorProperty(
        name=translate("ID Value"),
        description=translate("The areas containing this color will be considered as a mask"),
        subtype="COLOR",
        min=0,
        max=1,
        default=(1,0,0), 
        update=scattering.update_factory.factory("s_mask_bitmap_id_color_ptr", delay_support=True,),
        ) 

    ########## ########## Material

    s_mask_material_allow : bpy.props.BoolProperty( 
        name=translate("Material ID Mask"), 
        description=translate("Mask-out instances located upon faces assigned to a chosen material slot"),
        default=False, 
        update=scattering.update_factory.factory("s_mask_material_allow"),
        )
    s_mask_material_ptr : bpy.props.StringProperty(
        name=translate("Material Pointer\nThe faces assigned to chosen material slot will be used as a culling mask"),
        description=translate("Search across all your surface(s) for shared Materials\nWe will highlight the pointer in red if the attribute is not shared across your surface(s)"),
        search=lambda s,c,e: get_surfs_shared_attrs(system=s, attr_type='mat', searchname=e,),
        search_options={'SUGGESTION','SORT'},
        update=scattering.update_factory.factory("s_mask_material_ptr"),
        )
    s_mask_material_revert : bpy.props.BoolProperty(
        name=translate("Reverse"),
        description=translate("Reverse the influence of this mask"),
        update=scattering.update_factory.factory("s_mask_material_revert"),
        )
    
    ########## ########## Curves

    s_mask_curve_allow : bpy.props.BoolProperty( 
        name=translate("Bezier-Area Mask"), 
        description=translate("Mask-out instances located under the inner-area of a closed bezier-curve.\n\n• Internally, the points will be projected upwards and culled if making contact with the inner area of the chosen bezier curve object. Please make sure that your bezier splines are set to 'Cyclic U' in the 'Object>Curve Data' properties panel"),
        default=False, 
        update=scattering.update_factory.factory("s_mask_curve_allow"),
        )
    s_mask_curve_ptr : bpy.props.PointerProperty(
        name=translate("Bezier-Curve Pointer"),
        type=bpy.types.Object, 
        poll=lambda s,o: o.type=="CURVE",
        update=scattering.update_factory.factory("s_mask_curve_ptr"),
        )
    s_mask_curve_revert : bpy.props.BoolProperty(
        name=translate("Reverse"),
        description=translate("Reverse the influence of this mask"),
        update=scattering.update_factory.factory("s_mask_curve_revert"),
        )

    ########## ########## Boolean Volume

    s_mask_boolvol_allow : bpy.props.BoolProperty( 
        name=translate("Boolean Mask"), 
        description=translate("Mask-out instances located inside the volume of the objects contained in the chosen collection.\n\n• If you'd like more control we'd suggest you to use the 'Proximity>Repel' features instead of this simple boolean mask"),
        default=False,
        update=scattering.update_factory.factory("s_mask_boolvol_allow"),
        )
    s_mask_boolvol_coll_ptr : bpy.props.StringProperty(
        name=translate("Collection Pointer"),
        search=lambda s,c,e: set(col.name for col in bpy.data.collections if (e in col.name)),
        search_options={'SUGGESTION','SORT'},
        update=scattering.update_factory.factory("s_mask_boolvol_coll_ptr"),
        )
    s_mask_boolvol_revert : bpy.props.BoolProperty(
        name=translate("Reverse"),
        description=translate("Reverse the influence of this mask"),
        update=scattering.update_factory.factory("s_mask_boolvol_revert"),
        )

    ########## ########## Upward Obstruction

    s_mask_upward_allow : bpy.props.BoolProperty( 
        name=translate("Upward-Obstruction Mask"), 
        description=translate("Mask-out instances located under the objects contained in the chosen collection"),
        default=False, 
        update=scattering.update_factory.factory("s_mask_upward_allow"),
        )
    s_mask_upward_coll_ptr : bpy.props.StringProperty(
        name=translate("Collection Pointer"),
        search=lambda s,c,e: set(col.name for col in bpy.data.collections if (e in col.name)),
        search_options={'SUGGESTION','SORT'},
        update=scattering.update_factory.factory("s_mask_upward_coll_ptr"),
        )
    s_mask_upward_revert : bpy.props.BoolProperty(
        name=translate("Reverse"),
        description=translate("Reverse the influence of this mask"),
        update=scattering.update_factory.factory("s_mask_upward_revert"),
        )

    # .dP"Y8  dP""b8    db    88     888888
    # `Ybo." dP   `"   dPYb   88     88__
    # o.`Y8b Yb       dP__Yb  88  .o 88""
    # 8bodP'  YboodP dP""""Yb 88ood8 888888

    ###################### This category of settings keyword is : "s_scale"

    s_scale_locked : bpy.props.BoolProperty(description=translate("Lock/Unlock Settings"),)

    def get_s_scale_main_features(self, availability_conditions=True,): 
        r = ["s_scale_default_allow", "s_scale_random_allow", "s_scale_min_allow", "s_scale_mirror_allow", "s_scale_shrink_allow", "s_scale_grow_allow", "s_scale_fading_allow",]
        
        if (not availability_conditions):
            return r + ["s_scale_clump_allow","s_scale_faces_allow","s_scale_edges_allow","s_scale_projbezline_radius_allow","s_scale_projempties_allow",]
        
        if (self.s_distribution_method=="clumping"):
            r.append("s_scale_clump_allow")
        elif (self.s_distribution_method=="faces"):
            r.append("s_scale_faces_allow")
        elif (self.s_distribution_method=="edges"):
            r.append("s_scale_edges_allow")
        elif (self.s_distribution_method=="projbezline"):
            r.append("s_scale_projbezline_radius_allow")
        elif (self.s_distribution_method=="projempties"):
            r.append("s_scale_projempties_allow")
            
        if (self.s_instances_method=="ins_points"):
            r.remove("s_scale_mirror_allow")
            
        return r

    s_scale_master_allow : bpy.props.BoolProperty( 
        name=translate("Master Toggle"),
        description=translate("Mute/Unmute all features of this category in one click"),
        default=True, 
        update=scattering.update_factory.factory("s_scale_master_allow", sync_support=False,),
        )

    ########## ########## Default 

    s_scale_default_allow : bpy.props.BoolProperty(
        name=translate("Default Scale"), 
        description=translate("Define the default scale of your instances"),
        default=False, 
        update=scattering.update_factory.factory("s_scale_default_allow"),
        )
    s_scale_default_space : bpy.props.EnumProperty(
        name=translate("Space"),
        description=translate("Space Calculation.\nHow do you wish the scale of your instances to behave if the object(s) you are scattering upon is/are being re-scaled?"),
        default="local",
        items= ( ("local", translate("Local"), translate("Choose the 'Local' option if you'd like the default scale of your instances to stay stable when the transforms of the object(s) you are scattering upon are changing"),  "ORIENTATION_LOCAL",1 ),
                 ("global", translate("Global"), translate("Choose the 'Global' option if you'd like the default scale of your instances to stay consistent in world space. The scale will therefore be recalculated when your object(s) you are scattering upon are changing scales"), "WORLD",2 ),
               ),
        update=scattering.update_factory.factory("s_scale_default_space"),
        )
    s_scale_default_value : bpy.props.FloatVectorProperty(
        name=translate("Factor"),
        description=translate("Scale factor.\nMultiply the scale of your instances on their XYZ dimensions by the following vector value"),
        subtype="XYZ", 
        default=(1,1,1), 
        update=scattering.update_factory.factory("s_scale_default_value", delay_support=True,),
        )
    s_scale_default_multiplier : bpy.props.FloatProperty(
        name=translate("Factor"),
        description=translate("Uniform Scale factor.\nMultiply the scale of your instances uniformly on their XYZ dimensions by the following value"),
        default=1,
        soft_max=5,
        soft_min=0,
        update=scattering.update_factory.factory("s_scale_default_multiplier", delay_support=True,),
        )
    ui_scale_default_coef : bpy.props.FloatProperty( #Not supported by Preset
        name=translate("Quick-Math"),
        description=translate("Quickly execute math operation on the property above with the given coefficient, use the universal 'ALT' shortcut to execute the same operation on all selected system(s) homogeneously"),
        default=2,
        min=0,
        )

    ########## ########## Random

    s_scale_random_allow : bpy.props.BoolProperty(
        name=translate("Random Scale"), 
        description=translate("Randomly multiply the scale of your instances"),
        default=False, 
        update=scattering.update_factory.factory("s_scale_random_allow"),
        )
    s_scale_random_factor : bpy.props.FloatVectorProperty(
        name=translate("Factor"),
        description=translate("Random Scale Factor.\nRandomly multiply the scale of your instances on their XYZ dimensions by a random vector ranging from '0,0,0' to the given vector value"),
        subtype="XYZ", 
        default=(0.33,0.33,0.33), 
        soft_min=0,
        soft_max=2,
        update=scattering.update_factory.factory("s_scale_random_factor", delay_support=True,),
        )
    s_scale_random_probability : bpy.props.FloatProperty(
        name=translate("Probability"),
        description=translate("Randomness Influence Probability Rate.\n• A rate ranging toward 0% means that less instances will be influenced by the scaling factor.\n• A probability rate ranging toward 100% means that most instances will get affected by the scaling factor"),
        subtype="PERCENTAGE",
        default=50,
        min=0,
        max=99, 
        update=scattering.update_factory.factory("s_scale_random_probability", delay_support=True,),
        )
    s_scale_random_method : bpy.props.EnumProperty(
        name=translate("Randomization Method"),
        description=translate("Define how the vectorial scale multiplication is affecting your instances"),
        default="random_uniform",
        items= ( ("random_uniform", translate("Uniform"), translate("Multiply the scale of your instances by scaling the X/Y/Z values uniformly toward the given random scale"), 1 ),
                 ("random_vectorial",  translate("Vectorial"), translate("Multiply the scale of your instances by scaling the X/Y/Z values individually toward the given random scale. Choosing this option means that sometimes you might randomly scale your instances on the X axis, sometimes on the Y axis, sometimes both, ect."), 2 ),
               ),
        update=scattering.update_factory.factory("s_scale_random_method",),
        )
    s_scale_random_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        description=translate("Change this value to randomize the result.\n\nIn 3D graphics, a seed is a starting value used by a random number generator to produce a sequence of random-looking numbers. These numbers can control things like the position, rotation, or scale of objects in a scene. Using the same seed will always generate the same 'random' result, which helps keep things consistent when needed."),
        update=scattering.update_factory.factory("s_scale_random_seed", delay_support=True,),
        )
    s_scale_random_is_random_seed : bpy.props.BoolProperty( 
        name=translate("Randomize Seed"),
        description=translate("Randomize the value of the hereby seed property.\n\n• Note that pressing 'ALT' while clicking on this button will garantee the attribution of an unique seed value of this property for all selected-system(s)"),
        default=False,
        update=scattering.update_factory.factory("s_scale_random_is_random_seed",),
        )
    #Feature Mask
    codegen_featuremask_properties(scope_ref=__annotations__, name="s_scale_random",)

    ########## ########## Shrink

    s_scale_shrink_allow : bpy.props.BoolProperty(
        name=translate("Shrink Mask"), 
        description=translate("Influences your instances with a shrinking scale effect.")+"\n\n• "+translate("Note that this feature is meant to be used with a feature-mask for precisely defining the effect area"),
        default=False, 
        update=scattering.update_factory.factory("s_scale_shrink_allow"),
        )
    s_scale_shrink_factor : bpy.props.FloatVectorProperty(
        name=translate("Factor"),
        description=translate("Scale factor.\nMultiply the scale of your instances on their XYZ dimensions by the following vector value"),
        subtype="XYZ",
        default=(0.1,0.1,0.1),
        soft_min=0,
        soft_max=1,
        update=scattering.update_factory.factory("s_scale_shrink_factor", delay_support=True,),
        )
    #Feature Mask
    codegen_featuremask_properties(scope_ref=__annotations__, name="s_scale_shrink",)

    ########## ########## Grow

    s_scale_grow_allow : bpy.props.BoolProperty(
        name=translate("Grow Mask"), 
        description=translate("Influences your instances with a growth scaling effect.")+"\n\n• "+translate("Note that this feature is meant to be used with a feature-mask for precisely defining the effect area"),
        default=False, 
        update=scattering.update_factory.factory("s_scale_grow_allow"),
        )
    s_scale_grow_factor : bpy.props.FloatVectorProperty(
        name=translate("Factor"),
        description=translate("Scale factor.\nMultiply the scale of your instances on their XYZ dimensions by the following vector value"),
        subtype="XYZ",
        default=(3,3,3),
        soft_min=1,
        soft_max=5,
        update=scattering.update_factory.factory("s_scale_grow_factor", delay_support=True,),
        )
    #Feature Mask
    codegen_featuremask_properties(scope_ref=__annotations__, name="s_scale_grow",)

    ########## ########## Mirrorring 

    s_scale_mirror_allow : bpy.props.BoolProperty(
        name=translate("Random Mirror"),
        description=translate("Hide the visual repetition of your instances with the help of a mirror effect randomly applied to the chosen axes.\n\n• Behind the scene, the feature will randomly scale your instances by a negative factor on the selected axis.\n• Selecting the Z axis might not be advised on most scenarios"),
        default=False,
        update=scattering.update_factory.factory("s_scale_mirror_allow"),
        )
    s_scale_mirror_is_x : bpy.props.BoolProperty(
        default=True,
        name=translate("X Axis"),
        description=translate("Add a mirroring effect to this axis"),
        update=scattering.update_factory.factory("s_scale_mirror_is_x"),
        )
    s_scale_mirror_is_y : bpy.props.BoolProperty(
        default=True,
        name=translate("Y Axis"),
        description=translate("Add a mirroring effect to this axis"),
        update=scattering.update_factory.factory("s_scale_mirror_is_y"),
        )
    s_scale_mirror_is_z : bpy.props.BoolProperty(
        default=False,
        name=translate("Z Axis"),
        description=translate("Add a mirroring effect to this axis"),
        update=scattering.update_factory.factory("s_scale_mirror_is_z"),
        ) 
    s_scale_mirror_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        description=translate("Change this value to randomize the result.\n\nIn 3D graphics, a seed is a starting value used by a random number generator to produce a sequence of random-looking numbers. These numbers can control things like the position, rotation, or scale of objects in a scene. Using the same seed will always generate the same 'random' result, which helps keep things consistent when needed."),
        update=scattering.update_factory.factory("s_scale_mirror_seed", delay_support=True,),
        )
    s_scale_mirror_is_random_seed : bpy.props.BoolProperty( 
        name=translate("Randomize Seed"),
        description=translate("Randomize the value of the hereby seed property.\n\n• Note that pressing 'ALT' while clicking on this button will garantee the attribution of an unique seed value of this property for all selected-system(s)"),
        default=False,
        update=scattering.update_factory.factory("s_scale_mirror_is_random_seed",),
        )
    #Feature Mask
    codegen_featuremask_properties(scope_ref=__annotations__, name="s_scale_mirror",)

    ########## ########## Minimal 

    s_scale_min_allow : bpy.props.BoolProperty(
        name=translate("Minimal Scale"),
        description=translate("Adjust instances that reach a minimum scale threshold to ensure none fall below a chosen size value"),
        default=False,
        update=scattering.update_factory.factory("s_scale_min_allow",),
        )
    s_scale_min_method : bpy.props.EnumProperty(
        name=translate("Method"),
        description=translate("Minimal Filter Method.\nDefine how you would like to handle instances that have a scale below the threshold"),
        default="s_scale_min_lock",
        items=( ("s_scale_min_lock"  ,translate("Adjusting")  ,translate("Re-adjust the instance(s) scale to fit to the minimal value") ),
                ("s_scale_min_remove",translate("Removing") ,translate("Remove the instance(s) from the distribution alltogether") ),
              ),
        update=scattering.update_factory.factory("s_scale_min_method"),
        )
    s_scale_min_value : bpy.props.FloatProperty(
        name=translate("Threshold"),
        description=translate("Minimal Scale Threshold.\nIf an instance scale reach below this value, we will act upon it"),
        default=0.05,
        soft_min=0,
        soft_max=10, 
        update=scattering.update_factory.factory("s_scale_min_value", delay_support=True,),
        )

    ########## ########## Scale Fading

    s_scale_fading_allow : bpy.props.BoolProperty(
        name=translate("Scale Fading"), 
        description=translate("Fade the scale of the instances depending on their distance from the active camera to create a force perspective effect.\n\n• We advise to disable this feature when rendering an animation"),
        default=False, 
        update=scattering.update_factory.factory("s_scale_fading_allow"),
        )
    s_scale_fading_factor : bpy.props.FloatVectorProperty(
        name=translate("Factor"),
        description=translate("Scale factor.\nMultiply the scale of your instances on their XYZ dimensions by the following vector value"),
        subtype="XYZ",
        default=(2,2,1.5),
        soft_min=0, soft_max=5,
        update=scattering.update_factory.factory("s_scale_fading_factor", delay_support=True,),
        )
    s_scale_fading_per_cam_data : bpy.props.BoolProperty(
        name=translate("Per Camera Settings"),
        description=translate("Swap settings depending on the camera object being active"),
        default=False,
        update=scattering.update_factory.factory("s_scale_fading_per_cam_data"),
        )
    s_scale_fading_distance_min : bpy.props.FloatProperty(
        name=translate("Start"),
        description=translate("Starting this distance, we will start a transition effect until the 'end' distance value"),
        default=30,
        subtype="DISTANCE",
        min=0,
        soft_max=200, 
        update=scattering.update_factory.factory("s_scale_fading_distance_min", delay_support=True,),
        )
    s_scale_fading_distance_max : bpy.props.FloatProperty(
        name=translate("End"),
        description=translate("After this distance the effect will end"),
        default=40,
        subtype="DISTANCE",
        min=0,
        soft_max=200, 
        update=scattering.update_factory.factory("s_scale_fading_distance_max", delay_support=True,),
        )
    #remap
    s_scale_fading_fallremap_allow : bpy.props.BoolProperty(
        name=translate("Transition Control"),
        description=translate("Control the transition falloff by remapping the values with a curve-map graph.\n\n• Please note that this feature assumes there is a transition distance to work with"),
        default=False, 
        update=scattering.update_factory.factory("s_scale_fading_fallremap_allow",),
        )
    s_scale_fading_fallremap_revert : bpy.props.BoolProperty(
        name=translate("Reverse Transition"),
        description=translate("Reverse the transition. This option will in fact remap the values from '0-1' to '1-0'"),
        default=False,
        update=scattering.update_factory.factory("s_scale_fading_fallremap_revert",),
        )
    s_scale_fading_fallremap_data : bpy.props.StringProperty(
        set=scattering.update_factory.fallremap_setter("s_scale_fading.fallremap"),
        get=scattering.update_factory.fallremap_getter("s_scale_fading.fallremap"),
        )

    ########## ########## Clump Special  

    s_scale_clump_allow : bpy.props.BoolProperty(
        name=translate("Clump Scale"), 
        description=translate("Scale your instances depending on how far they are from the clump center.\n\n• This feature is exclusive to 'Clumping' distribution mode"),
        default=True, 
        update=scattering.update_factory.factory("s_scale_clump_allow"),
        )
    s_scale_clump_value : bpy.props.FloatProperty(
        name=translate("Factor"),
        description=translate("An influence factor of an effect is a value that determines how strong the effect is. A higher factor means more impact, while lower factor means less"),
        default=0.3,
        soft_min=0,
        soft_max=1,
        precision=3,
        update=scattering.update_factory.factory("s_scale_clump_value", delay_support=True,),
        )

    ########## ########## Faces Special 

    s_scale_faces_allow : bpy.props.BoolProperty(
        name=translate("Face Size Influence"), 
        description=translate("Scale your instances depending faces area of their surface(s).\n\n• This feature is exclusive to 'Per Face' distribution mode"), 
        default=False, 
        update=scattering.update_factory.factory("s_scale_faces_allow"),
        )
    s_scale_faces_value : bpy.props.FloatProperty(
        name=translate("Factor"),
        description=translate("An influence factor of an effect is a value that determines how strong the effect is. A higher factor means more impact, while lower factor means less"),
        default=0.3,
        soft_min=0,
        precision=3,
        update=scattering.update_factory.factory("s_scale_faces_value", delay_support=True,),
        )

    ########## ########## Edges Special 

    s_scale_edges_allow : bpy.props.BoolProperty(
        name=translate("Edge Length Influence"), 
        description=translate("Scale your instances depending on edges length of their surface(s).\n\n• This feature is exclusive to 'Per Edge' distribution mode"), 
        default=False,
        update=scattering.update_factory.factory("s_scale_edges_allow"),
        )
    s_scale_edges_vec_factor : bpy.props.FloatVectorProperty(
        name=translate("Factor"),
        description=translate("Scale factor.\nMultiply the scale of your instances on their XYZ dimensions by the following vector value"),
        default=(1.3,1.3,1.3),
        subtype="XYZ",
        soft_min=0,
        update=scattering.update_factory.factory("s_scale_edges_vec_factor", delay_support=True,),
        )
    
    ########## ########## ProBezLine Special 

    s_scale_projbezline_radius_allow : bpy.props.BoolProperty(
        name=translate("Spline Radius Influence"), 
        description=translate("Scale your instances depending on the bezier-handle radius attribute of the spline they are distributed upon.\n\n• This feature is exclusive to 'Bezier-Spline' distribution mode\n• This radius bezier handle attribute can be edited in the curve editor, with the 'Radius' active tool"), 
        default=False,
        update=scattering.update_factory.factory("s_scale_projbezline_radius_allow"),
        )
    s_scale_projbezline_radius_value : bpy.props.FloatProperty(
        name=translate("Factor"),
        description=translate("An influence factor of an effect is a value that determines how strong the effect is. A higher factor means more impact, while lower factor means less"),
        default=0.5,
        soft_min=0,
        precision=3,
        update=scattering.update_factory.factory("s_scale_projbezline_radius_value", delay_support=True,),
        )
    
    ########## ########## ProEmpties Special 
    
    s_scale_projempties_allow : bpy.props.BoolProperty(
        name=translate("Empties Scale Influence"), 
        description=translate("Scale your instances depending on the scale of the empties they are spawned upon.\n\n• This feature is exclusive to 'Empties' distribution mode"),
        default=True,
        update=scattering.update_factory.factory("s_scale_projempties_allow"),
        )
    s_scale_projempties_value : bpy.props.FloatProperty(
        name=translate("Factor"),
        description=translate("An influence factor of an effect is a value that determines how strong the effect is. A higher factor means more impact, while lower factor means less"),
        default=1,
        soft_min=0, 
        precision=3,
        update=scattering.update_factory.factory("s_scale_projempties_value", delay_support=True,),
        )
    
    # 88""Yb  dP"Yb  888888    db    888888 88  dP"Yb  88b 88
    # 88__dP dP   Yb   88     dPYb     88   88 dP   Yb 88Yb88
    # 88"Yb  Yb   dP   88    dP__Yb    88   88 Yb   dP 88 Y88
    # 88  Yb  YbodP    88   dP""""Yb   88   88  YbodP  88  Y8

    ###################### This category of settings keyword is : "s_rot"

    s_rot_locked : bpy.props.BoolProperty(description=translate("Lock/Unlock Settings"),)

    def get_s_rot_main_features(self, availability_conditions=True,):
        return ["s_rot_align_z_allow", "s_rot_align_y_allow", "s_rot_random_allow", "s_rot_add_allow", "s_rot_tilt_allow",]

    s_rot_master_allow : bpy.props.BoolProperty( 
        name=translate("Master Toggle"),
        description=translate("Mute/Unmute all features of this category in one click"),
        default=True, 
        update=scattering.update_factory.factory("s_rot_master_allow", sync_support=False,),
        )

    ########## ########## Align Z

    s_rot_align_z_allow : bpy.props.BoolProperty(
        name=translate("Default Normal Orientation"),
        description=translate("Set the default orientation of your instances by defining their 'Normal' axis (The 'Normal' axis is the +Z axis, also known as the 'Upward' direction).\n\n• By aligning your instance's default normal direction toward an axis of your choice, you are effectively defining part of their default rotation. A rotation can be fully defined when both the normal (+Z) and tangent (+Y) orientations are chosen.\n\n• Please note that this feature will override the default orientations defined by the distribution method you've chosen"),
        default=False, 
        update=scattering.update_factory.factory("s_rot_align_z_allow"),
        )
    s_rot_align_z_method : bpy.props.EnumProperty( #changes to items in this enum must be in accordance of special method below
        name=translate("Normal Axis"),
        description=translate("Define your instance normal (your instance +Z axis, their upward direction) by aligning toward a chosen axis"),
        default= "meth_align_z_normal",
        items= ( ("meth_align_z_normal", translate("Surface Normal"), translate("Align each instance’s normal toward the face normal of the Scatter-Surface(s)"), "NORMALS_FACE", 0 ),
                 ("meth_align_z_local",  translate("Local Z"),        translate("Align each instance’s normal toward the local +Z axis of the Scatter-Surface(s)"), "ORIENTATION_LOCAL", 1 ),
                 ("meth_align_z_global", translate("Global Z"),       translate("Align each instance’s normal toward the global +Z axis of the scene-world"), "WORLD", 2),
                 ("meth_align_z_object", translate("Object"),         translate("Align each instance’s normal toward the origin point of the chosen object"), "EYEDROPPER", 4),
                 ("meth_align_z_random", translate("Random"),         translate("Align each instance’s normal toward random axis"), "TOPATCH:W_DICE", 5 ),
                 ("meth_align_z_origin", translate("Origin"),         translate("Align each instance’s normal toward the origin point of the Scatter-Surface(s)"),"TRACKER", 6 ),
                 ("meth_align_z_camera", translate("Camera"),         translate("Align each instance’s normal toward the active camera"),"CAMERA_DATA", 7 ),
               ),
        update=scattering.update_factory.factory("s_rot_align_z_method"),
        )
    #special methods for some distribution type. We only cull or change name of base method = superficial change
    s_rot_align_z_method_projbezareanosurf_special : bpy.props.EnumProperty(
        name=translate("Normal Axis"),
        description=translate("Define your instance normal (your instance +Z axis, their upward direction) by aligning toward a chosen axis"),
        default= "meth_align_z_local",
        items= ( ("meth_align_z_local",  translate("Local Z"),  translate("Align each instance’s normal toward the local +Z axis of the of the chosen Bezier Area"), "ORIENTATION_LOCAL", 1 ),
                 ("meth_align_z_global", translate("Global Z"), translate("Align each instance’s normal toward the global +Z axis of the scene-world"), "WORLD", 2),
                 ("meth_align_z_object", translate("Object"),   translate("Align each instance’s normal toward the origin point of the chosen object"), "EYEDROPPER", 4),
                 ("meth_align_z_random", translate("Random"),   translate("Align each instance’s normal toward random axis"), "TOPATCH:W_DICE", 5 ),
                 ("meth_align_z_origin", translate("Origin"),   translate("Align each instance’s normal toward the origin point of the chosen Bezier Area"),"TRACKER", 6 ),
                 ("meth_align_z_camera", translate("Camera"),   translate("Align each instance’s normal toward the active camera"),"CAMERA_DATA", 7 ),
               ),
        update=scattering.update_factory.factory("s_rot_align_z_method_projbezareanosurf_special"),
        )
    s_rot_align_z_method_projbezlinenosurf_special : bpy.props.EnumProperty(
        name=translate("Normal Axis"), 
        description=translate("Define your instance normal (your instance +Z axis, their upward direction) by aligning toward a chosen axis"),
        default= "meth_align_z_normal",
        items= ( ("meth_align_z_normal", translate("Curve Normal"), translate("Align each instance’s normal toward the chosen Bezier Spline normal. (This alignment method is the default alignment of the bezier spline distribution)."), "CURVE_BEZCURVE", 0 ),
                 ("meth_align_z_local",  translate("Local Z"),      translate("Align each instance’s normal toward the local +Z axis of the chosen Bezier object"), "ORIENTATION_LOCAL", 1 ),
                 ("meth_align_z_global", translate("Global Z"),     translate("Align each instance’s normal toward the global +Z axis of the scene-world"), "WORLD", 2),
                 ("meth_align_z_object", translate("Object"),       translate("Align each instance’s normal toward the origin point of the chosen object"), "EYEDROPPER", 4),
                 ("meth_align_z_random", translate("Random"),       translate("Align each instance’s normal toward random axis"), "TOPATCH:W_DICE", 5 ),
                 ("meth_align_z_origin", translate("Origin"),       translate("Align each instance’s normal toward the origin point of the chosen Bezier object"),"TRACKER", 6 ),
                 ("meth_align_z_camera", translate("Camera"),       translate("Align each instance’s normal toward the active camera"),"CAMERA_DATA", 7 ),
               ),
        update=scattering.update_factory.factory("s_rot_align_z_method_projbezlinenosurf_special"),
        )
    s_rot_align_z_method_projemptiesnosurf_special : bpy.props.EnumProperty(
        name=translate("Normal Axis"), 
        description=translate("Define your instance normal (your instance +Z axis, their upward direction) by aligning toward a chosen axis"),
        default= "meth_align_z_normal",
        items= ( ("meth_align_z_normal", translate("Empties Z"), translate("Align each instance’s normal toward the axis of their assigned empties (This alignment method is the default alignment of the empties distribution)."), "EMPTY_AXIS", 0 ),
                 ("meth_align_z_global", translate("Global Z"),  translate("Align each instance’s normal toward the global +Z axis of the scene-world"), "WORLD", 2),
                 ("meth_align_z_object", translate("Object"),    translate("Align each instance’s normal toward the origin point of the chosen object"), "EYEDROPPER", 4),
                 ("meth_align_z_random", translate("Random"),    translate("Align each instance’s normal toward random axis"), "TOPATCH:W_DICE", 5 ),
                 ("meth_align_z_camera", translate("Camera"),    translate("Align each instance’s normal toward the active camera"),"CAMERA_DATA", 7 ),
               ),
        update=scattering.update_factory.factory("s_rot_align_z_method_projemptiesnosurf_special"),
        )
    s_rot_align_z_revert : bpy.props.BoolProperty(
        name=translate("Reverse"),
        description=translate("Reverse the alignment direction. Internally it will multiply the direction value by '-1'"),
        default=False, 
        update=scattering.update_factory.factory("s_rot_align_z_revert"),
        )
    s_rot_align_z_random_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        description=translate("Change this value to randomize the result.\n\nIn 3D graphics, a seed is a starting value used by a random number generator to produce a sequence of random-looking numbers. These numbers can control things like the position, rotation, or scale of objects in a scene. Using the same seed will always generate the same 'random' result, which helps keep things consistent when needed."),
        default=1, #need to be different from y_random_seed otherwise axis conflict
        update=scattering.update_factory.factory("s_rot_align_z_random_seed", delay_support=True,),
        )
    s_rot_align_z_is_random_seed : bpy.props.BoolProperty( 
        name=translate("Randomize Seed"),
        description=translate("Randomize the value of the hereby seed property.\n\n• Note that pressing 'ALT' while clicking on this button will garantee the attribution of an unique seed value of this property for all selected-system(s)"),
        default=False,
        update=scattering.update_factory.factory("s_rot_align_z_is_random_seed",),
        )
    s_rot_align_z_influence_allow : bpy.props.BoolProperty(
        name=translate("Vertical Influence"), 
        description=translate("Toggle this feature if you'd like your current alignment to be influenced toward an upward/downward direction"),
        default=False, 
        update=scattering.update_factory.factory("s_rot_align_z_influence_allow"),
        )
    s_rot_align_z_influence_value : bpy.props.FloatProperty( #was 's_rot_align_z_method_mix' in beta, now legacy property 
        name=translate("Factor"), 
        description=translate("Influence Factor\n• A value of '1.0' means a complete alignment upward.\n• A value of '-1.0' means a complete alignment downward.\n• A Value of '0.0' represents no influences at all, like the option isn't even turned on"),
        default=0.7,
        min=-1,
        max=1,
        precision=3,
        update=scattering.update_factory.factory("s_rot_align_z_influence_value", delay_support=True,),
        )
    s_rot_align_z_smoothing_allow : bpy.props.BoolProperty(
        name=translate("Smoothing"), 
        description=translate("Evaluate angles on a smoothend geometry to ensure your effect isn’t impacted by the smallest surface imperfections of your mesh.\n\n• Note that this feature might be slow to compute if you are working with geometries heavy on polycount"),
        default=False, 
        update=scattering.update_factory.factory("s_rot_align_z_smoothing_allow"),
        )
    s_rot_align_z_smoothing_value : bpy.props.FloatProperty(
        name=translate("Factor"),
        description=translate("An influence factor of an effect is a value that determines how strong the effect is. A higher factor means more impact, while lower factor means less"),
        default=0.35,
        min=0,
        soft_max=1,
        precision=3,
        update=scattering.update_factory.factory("s_rot_align_z_smoothing_value", delay_support=True,),
        )
    s_rot_align_z_object  : bpy.props.PointerProperty(
        name=translate("Object"),
        description=translate("Align each instances toward the origin of that object"), 
        type=bpy.types.Object, 
        update=scattering.update_factory.factory("s_rot_align_z_object"),
        )
    s_rot_align_z_clump_allow : bpy.props.BoolProperty(
        description=translate("Tilt the instances normals toward the clump center.\n\n• This feature is exclusive to 'Clumping' distribution mode"),
        default=False, 
        update=scattering.update_factory.factory("s_rot_align_z_clump_allow"),
        )
    s_rot_align_z_clump_value : bpy.props.FloatProperty(
        name=translate("Factor"), 
        description=translate("Influence Factor\n• A value of '1.0' means a complete alignment toward.\n• A value of '-1.0' means a complete alignment to the opposite direction.\n• A Value of '0.0' represents no influences at all, like the option isn't even turned on"),
        default=-0.5,
        soft_min=-1,
        soft_max=1,
        update=scattering.update_factory.factory("s_rot_align_z_clump_value", delay_support=True,),
        )

    ########## ########## Align Y

    s_rot_align_y_allow : bpy.props.BoolProperty(
        name=translate("Default Tangent Orientation"), 
        description=translate("Set the default orientation of your instances by defining their 'Tangent' axis (The 'Tangent' axis is the +Y axis, also known as the 'Forward' direction).\n\n• By aligning your instance's default tangent direction toward an axis of your choice, you are effectively defining part of their default rotation. A rotation can be fully defined when both the normal (+Z) and tangent (+Y) orientations are chosen.\n\n• Please note that this feature will override the default orientations defined by the distribution method you've chosen"),
        default=False, 
        update=scattering.update_factory.factory("s_rot_align_y_allow"),
        )
    s_rot_align_y_method : bpy.props.EnumProperty( #changes to items in this enum must be in accordance of special method below
        name=translate("Tangent Axis"), 
        description=translate("Define your instance tangent (your instance's +Y axis, their forward direction) by aligning toward a chosen axis"),
        default= "meth_align_y_local",
        items= ( ("meth_align_y_downslope", translate("Downslope"), translate("Align each instance tangent toward the slope downward direction of the Scatter-Surface(s)"), "SORT_ASC", 0 ),
                 ("meth_align_y_local",     translate("Local Y"),   translate("Align each instance tangent toward the local +Y axis of the Scatter-Surface(s)"), "ORIENTATION_LOCAL", 1 ),
                 ("meth_align_y_global",    translate("Global Y"),  translate("Align each instance tangent toward the global +Y axis of the scene-world"), "WORLD", 2 ),
                 ("meth_align_y_boundary",  translate("Boundary"),  translate("Align each instance tangent toward the nearest mesh boundary-edge of the Scatter-Surface(s)"), "MOD_EDGESPLIT", 3 ),
                 ("meth_align_y_object",    translate("Object"),    translate("Align each instance tangent toward the origin point of the chosen object"), "EYEDROPPER", 4 ),
                 ("meth_align_y_flow",      translate("Flowmap"),   translate("Align each instance tangent with the directional information contained within the chosen flowmap"), "ANIM", 5 ),
                 ("meth_align_y_random",    translate("Random"),    translate("Align each instance tangent toward random axis"), "TOPATCH:W_DICE", 6 ),
                 ("meth_align_y_origin",    translate("Origin"),    translate("Align each instance tangent toward the origin point of the Scatter-Surface(s)"), "TRACKER", 7 ),
                 ("meth_align_y_camera",    translate("Camera"),    translate("Align each instance tangent toward the active camera"),"CAMERA_DATA", 8 ),
               ),
        update=scattering.update_factory.factory("s_rot_align_y_method"),
        )
    #special methods for some distribution type. We only cull or change name of base method = superficial change
    s_rot_align_y_method_projbezareanosurf_special : bpy.props.EnumProperty(
        name=translate("Tangent Axis"), 
        description=translate("Define your instance tangent (your instance's +Y axis, their forward direction) by aligning toward a chosen axis"),
        default= "meth_align_y_local",
        items= ( ("meth_align_y_local",    translate("Local Y"),  translate("Align each instance tangent toward the local +Y axis of the Curve object used by the distribution"), "ORIENTATION_LOCAL", 1 ),
                 ("meth_align_y_global",   translate("Global Y"), translate("Align each instance tangent toward the global +Y axis of the scene-world"), "WORLD", 2 ),
                 #buggy.. ("meth_align_y_boundary", translate("Curve"),    translate("Align each instance tangent toward the nearest Curve Geometry (use the distribution spread option first)"), "CURVE_BEZCURVE", 3 ),
                 ("meth_align_y_object",   translate("Object"),   translate("Align each instance tangent toward the origin point of the chosen object"), "EYEDROPPER", 4 ),
                 ("meth_align_y_random",   translate("Random"),   translate("Align each instance tangent toward random axis"), "TOPATCH:W_DICE", 6 ),
                 ("meth_align_y_origin",   translate("Origin"),   translate("Align each instance tangent toward the origin point of the Curve object used by the distribution"), "TRACKER", 7 ),
                 ("meth_align_y_camera",   translate("Camera"),   translate("Align each instance tangent toward the active camera"),"CAMERA_DATA", 8 ),
               ),
        update=scattering.update_factory.factory("s_rot_align_y_method_projbezareanosurf_special"),
        )
    s_rot_align_y_method_projbezlinenosurf_special : bpy.props.EnumProperty(
        name=translate("Tangent Axis"), 
        description=translate("Define your instance tangent (your instance's +Y axis, their forward direction) by aligning toward a chosen axis"),
        default= "meth_align_y_local",
        items= ( ("meth_align_y_downslope", translate("Downslope"), translate("Align each instance tangent toward the slope downward direction of your Bezier Spline"), "SORT_ASC", 0 ),
                 ("meth_align_y_local",     translate("Local Y"),   translate("Align each instance tangent toward the local +Y axis of the Curve object used by the distribution"), "ORIENTATION_LOCAL", 1 ),
                 ("meth_align_y_global",    translate("Global Y"),  translate("Align each instance tangent toward the global +Y axis of the scene-world"), "WORLD", 2 ),
                 #buggy.. ("meth_align_y_boundary",  translate("Curve"),     translate("Align each instance tangent toward the nearest Curve Geometry (use the distribution spread option first)"), "CURVE_BEZCURVE", 3 ),
                 ("meth_align_y_object",    translate("Object"),    translate("Align each instance tangent toward the origin point of the chosen object"), "EYEDROPPER", 4 ),
                 ("meth_align_y_random",    translate("Random"),    translate("Align each instance tangent toward random axis"), "TOPATCH:W_DICE", 6 ),
                 ("meth_align_y_origin",    translate("Origin"),    translate("Align each instance tangent toward the origin point of Curve Object"), "TRACKER", 7 ),
                 ("meth_align_y_camera",    translate("Camera"),    translate("Align each instance tangent toward the active camera"),"CAMERA_DATA", 8 ),
               ),
        update=scattering.update_factory.factory("s_rot_align_y_method_projbezlinenosurf_special"),
        )
    s_rot_align_y_method_projemptiesnosurf_special : bpy.props.EnumProperty(
        name=translate("Tangent Axis"), 
        description=translate("Define your instance tangent (your instance's +Y axis, their forward direction) by aligning toward a chosen axis"),
        default= "meth_align_y_local",
        items= ( ("meth_align_y_local",  translate("Empties Y"), translate("Align each instance tangent toward the local +Y axis their assigned Empties object (This alignment method is the default alignment of the bezier spline distribution)"), "EMPTY_AXIS", 1 ),
                 ("meth_align_y_global", translate("Global Y"),  translate("Align each instance tangent toward the global +Y axis of the scene-world"), "WORLD", 2 ),
                 ("meth_align_y_object", translate("Object"),    translate("Align each instance tangent toward the origin point of the chosen object"), "EYEDROPPER", 4 ),
                 ("meth_align_y_random", translate("Random"),    translate("Align each instance tangent toward random axis"), "TOPATCH:W_DICE", 6 ),
                 ("meth_align_y_camera", translate("Camera"),    translate("Align each instance tangent toward the active camera"),"CAMERA_DATA", 8 ),
               ),
        update=scattering.update_factory.factory("s_rot_align_y_method_projemptiesnosurf_special"),
        )
    s_rot_align_y_revert : bpy.props.BoolProperty(
        name=translate("Reverse"),
        description=translate("Reverse the alignment direction"),
        default=False, 
        update=scattering.update_factory.factory("s_rot_align_y_revert"),
        )
    s_rot_align_y_random_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        description=translate("Change this value to randomize the result.\n\nIn 3D graphics, a seed is a starting value used by a random number generator to produce a sequence of random-looking numbers. These numbers can control things like the position, rotation, or scale of objects in a scene. Using the same seed will always generate the same 'random' result, which helps keep things consistent when needed."),
        update=scattering.update_factory.factory("s_rot_align_y_random_seed", delay_support=True,),
        )
    s_rot_align_y_is_random_seed : bpy.props.BoolProperty( 
        name=translate("Randomize Seed"),
        description=translate("Randomize the value of the hereby seed property.\n\n• Note that pressing 'ALT' while clicking on this button will garantee the attribution of an unique seed value of this property for all selected-system(s)"),
        default=False,
        update=scattering.update_factory.factory("s_rot_align_y_is_random_seed",),
        )
    s_rot_align_y_object : bpy.props.PointerProperty(
        name=translate("Object"),
        type=bpy.types.Object, 
        update=scattering.update_factory.factory("s_rot_align_y_object"),
        )
    s_rot_align_y_downslope_space : bpy.props.EnumProperty(
        name=translate("Space"),
        description=translate("Evaluation Space.\nChoose how you would like to evaluate your object(s) slope angle depending on its relative transformation"),
        default="local", 
        items= ( ("local", translate("Local"), translate("Calculate the slope angle while considering your object(s) transforms. The slope will stay stable and consistent, following the object(s) transforms you are scattering upon"),  "ORIENTATION_LOCAL",1 ),
                 ("global", translate("Global"), translate("Calculate the slope angle considering your object(s) with its transforms applied"), "WORLD",2 ),
               ),
        update=scattering.update_factory.factory("s_rot_align_y_downslope_space",),
        )
    s_rot_align_y_downslope_smoothing_allow : bpy.props.BoolProperty(
        name=translate("Smoothing"), 
        description=translate("Evaluate angles on a smoothend geometry to ensure your effect isn’t impacted by the smallest surface imperfections of your mesh.\n\n• Note that this feature might be slow to compute if you are working with geometries heavy on polycount"),
        default=False, 
        update=scattering.update_factory.factory("s_rot_align_y_downslope_smoothing_allow"),
        )
    s_rot_align_y_downslope_smoothing_value : bpy.props.FloatProperty(
        name=translate("Factor"),
        description=translate("An influence factor of an effect is a value that determines how strong the effect is. A higher factor means more impact, while lower factor means less"),
        default=0.35,
        min=0,
        soft_max=1,
        precision=3,
        update=scattering.update_factory.factory("s_rot_align_y_downslope_smoothing_value", delay_support=True,),
        )
    s_rot_align_y_flow_method : bpy.props.EnumProperty(
        name=translate("Flowmap Method"),
        description=translate("Choose the source type of the flowmap data"),
        default="flow_vcol",
        items=( ("flow_vcol", translate("Vertex Colors"), translate("Use the flowmap vectorial information detained in a vertex-color attribute"), "VPAINT_HLT",0),
                 ("flow_text", translate("Texture Data"),  translate("Use the flowmap vectorial information detained in the colors of a scatter texture-data"), "NODE_TEXTURE",1),
              ),
        update=scattering.update_factory.factory("s_rot_align_y_flow_method"),
        )
    s_rot_align_y_flow_direction : bpy.props.FloatProperty(
        name=translate("Direction"),
        description=translate("Add a default spinning (yaw) rotation after the alignment.\nDefine the default tangent direction angle your instances should follow after being aligned with the flowmap.\nChoose a value of '0' to striclty follow the direction of the flowmap"),
        subtype="ANGLE",
        default=0, 
        precision=3,
        update=scattering.update_factory.factory("s_rot_align_y_flow_direction", delay_support=True,),
        )
    s_rot_align_y_texture_ptr : bpy.props.StringProperty(
        description="Internal setter property that will update a TEXTURE_NODE node tree from given nodetree name (used for presets and most importantly copy/paste or synchronization) warning name is not consistant, always check in nodetree to get correct name!",
        update=scattering.update_factory.factory("s_rot_align_y_texture_ptr",),
        )
    s_rot_align_y_vcol_ptr : bpy.props.StringProperty(
        name=translate("Color-Attribute Pointer"),
        description=translate("Search across all your surface(s) for shared color attributes.\nWe will highlight the pointer in red if the attribute is not shared across your surface(s)"),
        search=lambda s,c,e: get_surfs_shared_attrs(system=s, attr_type='vcol', searchname=e,),
        search_options={'SUGGESTION','SORT'},
        update=scattering.update_factory.factory("s_rot_align_y_vcol_ptr",),
        )


    ########## ########## Added Rotation

    s_rot_add_allow : bpy.props.BoolProperty(
        name=translate("Add Rotation"),
        description=translate("Rotate your instances with a defined XYZ euler angle value.\n\n• You can optionally add random XYZ angle values, and snap the rotation values to constrain the randomness giving it a more 'hardsurface-like' look"),
        default=False, 
        update=scattering.update_factory.factory("s_rot_add_allow"),
        )
    s_rot_add_default : bpy.props.FloatVectorProperty(
        name=translate("Add Angle"),
        description=translate("Additionally rotate your instances by this value"),
        subtype="EULER",
        default=(0,0,0), 
        update=scattering.update_factory.factory("s_rot_add_default", delay_support=True,),
        )
    s_rot_add_random : bpy.props.FloatVectorProperty(
        name=translate("Add Random Angle"),
        description=translate("Additionally randomly rotate your instances by random values start from '0,0,0' to this value"),
        subtype="EULER",
        default=(0,0,0), 
        update=scattering.update_factory.factory("s_rot_add_random", delay_support=True,),
        )
    s_rot_add_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        description=translate("Change this value to randomize the result.\n\nIn 3D graphics, a seed is a starting value used by a random number generator to produce a sequence of random-looking numbers. These numbers can control things like the position, rotation, or scale of objects in a scene. Using the same seed will always generate the same 'random' result, which helps keep things consistent when needed."),
        update=scattering.update_factory.factory("s_rot_add_seed", delay_support=True,),
        )
    s_rot_add_is_random_seed : bpy.props.BoolProperty( 
        name=translate("Randomize Seed"),
        description=translate("Randomize the value of the hereby seed property.\n\n• Note that pressing 'ALT' while clicking on this button will garantee the attribution of an unique seed value of this property for all selected-system(s)"),
        default=False,
        update=scattering.update_factory.factory("s_rot_add_is_random_seed",),
        )
    s_rot_add_snap : bpy.props.FloatProperty(
        default=0,
        name=translate("Snap"),
        description=translate("Restrict your addded rotation to a fixed increment, like '15' or '45' degrees for example. This will result in a more  precise and consistent hardsurface look"),
        subtype="ANGLE",
        min=0,
        soft_max=6.283185, #=360d
        update=scattering.update_factory.factory("s_rot_add_snap", delay_support=True,),
        )
    #Feature Mask
    codegen_featuremask_properties(scope_ref=__annotations__, name="s_rot_add",)
    
    ########## ########## Random Rotation 

    s_rot_random_allow : bpy.props.BoolProperty(
        name=translate("Add Random Rotation"), 
        description=translate("Randomly rotate your instances, based on a 'Spin' or 'Tilt' motion"),
        default=False, 
        update=scattering.update_factory.factory("s_rot_random_allow"),
        )
    s_rot_random_tilt_value : bpy.props.FloatProperty(
        name=translate("Tilt"),
        description=translate("Additionally randomly rotate your instance's following a 'Tilting' motion.\n(the instance's normal (+Z) axes will be inclined on their side)"),
        subtype="ANGLE",
        default=0.3490659,
        update=scattering.update_factory.factory("s_rot_random_tilt_value", delay_support=True,),
        )
    s_rot_random_yaw_value : bpy.props.FloatProperty(
        name=translate("Spin"),
        description=translate("Additionally randomly rotate your instance's following a 'Spinning' motion.\n(also known as the 'Yaw' motion in aeronautics, the instances will rotate on themselves alongside their normal (+Z) axes)"),
        subtype="ANGLE",
        default=6.28,
        update=scattering.update_factory.factory("s_rot_random_yaw_value", delay_support=True,),
        )
    s_rot_random_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        description=translate("Change this value to randomize the result.\n\nIn 3D graphics, a seed is a starting value used by a random number generator to produce a sequence of random-looking numbers. These numbers can control things like the position, rotation, or scale of objects in a scene. Using the same seed will always generate the same 'random' result, which helps keep things consistent when needed."),
        update=scattering.update_factory.factory("s_rot_random_seed", delay_support=True,),
        )
    s_rot_random_is_random_seed : bpy.props.BoolProperty( 
        name=translate("Randomize Seed"),
        description=translate("Randomize the value of the hereby seed property.\n\n• Note that pressing 'ALT' while clicking on this button will garantee the attribution of an unique seed value of this property for all selected-system(s)"),
        default=False,
        update=scattering.update_factory.factory("s_rot_random_is_random_seed",),
        )
    #Feature Mask
    codegen_featuremask_properties(scope_ref=__annotations__, name="s_rot_random",)

    ########## ########## Tilt

    s_rot_tilt_allow : bpy.props.BoolProperty(
        name=translate("Add Tilting Rotation"),
        description=translate("Rotate your instances following a 'Tilting' motion toward a specified direction"),
        default=False, 
        update=scattering.update_factory.factory("s_rot_tilt_allow"),
        )
    s_rot_tilt_dir_method : bpy.props.EnumProperty(
        name=translate("Direction"),
        description=translate("Specify the direction of the tilt"),
        default="flowmap",
         items=( ("fixed", translate("Fixed"), translate("Tilt your instances uniformly toward a given direction. All of your instances will tilt toward the same fixed direction"), "CURVE_PATH", 0),
                 ("flowmap", translate("Flowmap"), translate("Tilt your instances toward the direction encoded from a given flowmap color information. The instances will follow various tilting directions based on the flowmap values"), "DECORATE_DRIVER", 1),
                 ("noise", translate("Noise"), translate("Tilt your instances depending on a procedural colored noise. The noise color information can be interpreted as a flowmap that can influence tilting directions"),"FORCE_VORTEX", 2),
               ),
        update=scattering.update_factory.factory("s_rot_tilt_dir_method"),
        )
    s_rot_tilt_method : bpy.props.EnumProperty(
        name=translate("Flowmap Method"),
        description=translate("Choose the source type of the flowmap data"),
        default="tilt_vcol",
        items= ( ("tilt_vcol", translate("Vertex Colors"), translate("Use the flowmap vectorial information detained in a vertex-color attribute"), "VPAINT_HLT",0),
                 ("tilt_text", translate("Texture Data"),  translate("Use the flowmap vectorial information detained in the colors of a scatter texture-data"), "NODE_TEXTURE",1),
               ),
        update=scattering.update_factory.factory("s_rot_tilt_method"),
        )
    s_rot_tilt_noise_space : bpy.props.EnumProperty(
        name=translate("Space"),
        description=translate("Define the procedural texture space"),
        default="local", 
        items= ( ("local", translate("Local"), translate("The texture is being transformed alongside your object transforms. If your object is being re-scaled, the texture will grow alongside the object"),  "ORIENTATION_LOCAL",0 ),
                 ("global", translate("Global"), translate("The texture is not taking your object transforms into consideration. The texture will stay at a consistent world-space size, independently from your object transformations"), "WORLD",1 ),
               ),
        update=scattering.update_factory.factory("s_rot_tilt_noise_space",),
        )
    s_rot_tilt_noise_scale : bpy.props.FloatProperty(
        name=translate("Scale"),
        description=translate("The scale of a procedural texture.\n• A value of '0.01' will creates a large noise pattern.\n• A value of '10.0' will create a small pattern"),
        default=0.1, min=0, soft_max=2,
        update=scattering.update_factory.factory("s_rot_tilt_noise_scale", delay_support=True,),
        )
    s_rot_tilt_blue_influence : bpy.props.FloatProperty(
        name=translate("Strength"), 
        description=translate("Influence the strength of the tilt by looking at the blue channel of the chosen flowmap. As we are working in tangent space, the 2D directions are only encoded in the Red and Green colors, leaving the blue channel available as a strength channel"),
        default=1,
        soft_min=0,
        soft_max=1,
        update=scattering.update_factory.factory("s_rot_tilt_blue_influence", delay_support=True,),
        )
    s_rot_tilt_texture_ptr : bpy.props.StringProperty(
        description="Internal setter property that will update a TEXTURE_NODE node tree from given nodetree name (used for presets and most importantly copy/paste or synchronization) warning name is not consistant, always check in nodetree to get correct name!",
        update=scattering.update_factory.factory("s_rot_tilt_texture_ptr",),
        )
    s_rot_tilt_vcol_ptr : bpy.props.StringProperty(
        name=translate("Color-Attribute Pointer"),
        description=translate("Search across all your surface(s) for shared color attributes.\nWe will highlight the pointer in red if the attribute is not shared across your surface(s)"),
        search=lambda s,c,e: get_surfs_shared_attrs(system=s, attr_type='vcol', searchname=e,),
        search_options={'SUGGESTION','SORT'},
        update=scattering.update_factory.factory("s_rot_tilt_vcol_ptr",),
        )
    s_rot_tilt_direction : bpy.props.FloatProperty(
        name=translate("Direction"),
        description=translate("Spin the direction of the tilt around the normal axis of your instances"),
        subtype="ANGLE",
        default=0,
        precision=3,
        update=scattering.update_factory.factory("s_rot_tilt_direction", delay_support=True,),
        )
    s_rot_tilt_force : bpy.props.FloatProperty(
        name=translate("Tilt"), 
        description=translate("Define the rotation angle value of the tilting motion"),
        subtype="ANGLE",
        default=0.7,
        soft_min=-1.5708,
        soft_max=1.5708,
        update=scattering.update_factory.factory("s_rot_tilt_force", delay_support=True,),
        )
    #Feature Mask
    codegen_featuremask_properties(scope_ref=__annotations__, name="s_rot_tilt",)

    # 88""Yb    db    888888 888888 888888 88""Yb 88b 88 .dP"Y8
    # 88__dP   dPYb     88     88   88__   88__dP 88Yb88 `Ybo."
    # 88"""   dP__Yb    88     88   88""   88"Yb  88 Y88 o.`Y8b
    # 88     dP""""Yb   88     88   888888 88  Yb 88  Y8 8bodP'

    ###################### This category of settings keyword is : "s_pattern"
    ###################### These are per nodegroups pattern settings: other params are stored per texture data block!

    s_pattern_locked : bpy.props.BoolProperty(description=translate("Lock/Unlock Settings"),)

    def get_s_pattern_main_features(self, availability_conditions=True,):
        return ["s_pattern1_allow", "s_pattern2_allow","s_pattern3_allow",]

    s_pattern_master_allow : bpy.props.BoolProperty( 
        name=translate("Master Toggle"),
        description=translate("Mute/Unmute all features of this category in one click"),
        default=True, 
        update=scattering.update_factory.factory("s_pattern_master_allow", sync_support=False,),
        )

    ########## ########## Pattern Slots

    codegen_properties_by_idx(scope_ref=__annotations__,
        name="s_patternX_allow", property_type=bpy.props.BoolProperty, nbr=3, items={
        "name":translate("Enable Texture Slot"),
        "description":translate("Influence your distribution density and your instances scale and with the help of a scatter-texture datablock"),
        "default":False,
        },)
    codegen_properties_by_idx(scope_ref=__annotations__,
        name="s_patternX_texture_ptr", property_type=bpy.props.StringProperty, nbr=3, items={
        "description":"Internal setter property that will update a TEXTURE_NODE node tree from given nodetree name (used for presets and most importantly copy/paste or synchronization) warning name is not consistant, always check in nodetree to get correct name!",
        },)
    codegen_properties_by_idx(scope_ref=__annotations__,
        name="s_patternX_color_sample_method", property_type=bpy.props.EnumProperty, nbr=3, items={
        "name":translate("Color Sampling"),
        "description":translate("Define how to translate the RGBA color values into a mask that will influence your distribution"),
        "default":"id_greyscale", 
        "items":( ("id_greyscale", translate("Greyscale"), translate("Combine all colors into a black and white mask"), "NONE", 0,),
                  ("id_red", translate("Red Channel"), translate("Only consider the Red channel as a mask"), "NONE", 1,),
                  ("id_green", translate("Green Channel"), translate("Only consider the Green channel as a mask"), "NONE", 2,),
                  ("id_blue", translate("Blue Channel"), translate("Only consider the Blue channel as a mask"), "NONE", 3,),
                  ("id_black", translate("Pure Black"), translate("Only the areas containing a pure black color will be masked"), "NONE", 4,),
                  ("id_white", translate("Pure White"), translate("Only the areas containing a pure white color will be masked"), "NONE", 5,),
                  ("id_picker", translate("Color ID"), translate("Only the areas containing a color matching the color of your choice will be masked"), "NONE", 6,),
                  ("id_hue", translate("Hue"), translate("Only consider the Hue channel as a mask, when converting the RGB colors to HSV values"), "NONE", 7,),
                  ("id_saturation", translate("Saturation"), translate("Only consider the Saturation channel as a maskn when converting the RGB colors to HSV values"), "NONE", 8,),
                  ("id_value", translate("Value"), translate("Only consider the Value channel as a mask, when converting the RGB colors to HSV values"), "NONE", 9,),
                  ("id_lightness", translate("Lightness"), translate("Only consider the Lightness channel as a mask, when converting the RGB colors to HSL values"), "NONE", 10,),
                  ("id_alpha", translate("Alpha Channel"), translate("Only consider the Alpha channel as a mask"), "NONE", 11,),
                ),
        },)
    codegen_properties_by_idx(scope_ref=__annotations__,
        name="s_patternX_id_color_ptr", property_type=bpy.props.FloatVectorProperty, nbr=3, delay_support=True, items={
        "name":translate("ID Value"),
        "description":translate("The areas containing this color will be considered as a mask"),
        "subtype":"COLOR",
        "min":0,
        "max":1,
        "default":(1,0,0),
        },)
    codegen_properties_by_idx(scope_ref=__annotations__,
        name="s_patternX_id_color_tolerence", property_type=bpy.props.FloatProperty, nbr=3, delay_support=True, items={
        "name":translate("Tolerance"),
        "description":translate("Tolerance threshold defines the measure of similarity between two colors before they are considered the same. A tolerance of '0' means that the colors should exactly match with each other"),
        "default":0.15, 
        "soft_min":0, 
        "soft_max":1,
        },)
    #Feature Influence
    codegen_properties_by_idx(scope_ref=__annotations__,
        name="s_patternX_dist_infl_allow", property_type=bpy.props.BoolProperty, nbr=3, items={
        "name":translate("Enable Influence"), 
        "default":True, 
        },)
    codegen_properties_by_idx(scope_ref=__annotations__,
        name="s_patternX_dist_influence", property_type=bpy.props.FloatProperty, nbr=3, delay_support=True, items={
        "name":translate("Density"),
        "description":translate("Influence the density of your distribution.")+"\n"+translate("Changing this slider will adjust the intensity of the influence"),
        "default":100,
        "subtype":"PERCENTAGE", 
        "min":0, 
        "max":100, 
        "precision":1, 
        },)
    codegen_properties_by_idx(scope_ref=__annotations__,
        name="s_patternX_dist_revert", property_type=bpy.props.BoolProperty, nbr=3, items={
        "name":translate("Reverse Influence"), 
        },)
    codegen_properties_by_idx(scope_ref=__annotations__,
        name="s_patternX_scale_infl_allow", property_type=bpy.props.BoolProperty, nbr=3, items={
        "name":translate("Enable Influence"), 
        "default":True, 
        },)
    codegen_properties_by_idx(scope_ref=__annotations__,
        name="s_patternX_scale_influence", property_type=bpy.props.FloatProperty, nbr=3, delay_support=True, items={
        "name":translate("Scale"),
        "description":translate("Influence the scale of your instances.")+"\n"+translate("Changing this slider will adjust the intensity of the influence"),
        "default":70, 
        "subtype":"PERCENTAGE", 
        "min":0, 
        "max":100, 
        "precision":1, 
        },)
    codegen_properties_by_idx(scope_ref=__annotations__,
        name="s_patternX_scale_revert", property_type=bpy.props.BoolProperty, nbr=3, items={
        "name":translate("Reverse Influence"), 
        },)

    #Feature Mask
    codegen_featuremask_properties(scope_ref=__annotations__, name="s_pattern1",)
    codegen_featuremask_properties(scope_ref=__annotations__, name="s_pattern2",)
    codegen_featuremask_properties(scope_ref=__annotations__, name="s_pattern3",)

    #    db    88""Yb 88  dP"Yb  888888 88  dP""b8
    #   dPYb   88__dP 88 dP   Yb   88   88 dP   `"
    #  dP__Yb  88""Yb 88 Yb   dP   88   88 Yb
    # dP""""Yb 88oodP 88  YbodP    88   88  YboodP

    ###################### This category of settings keyword is : "s_abiotic"

    s_abiotic_locked : bpy.props.BoolProperty(description=translate("Lock/Unlock Settings"),)

    def get_s_abiotic_main_features(self, availability_conditions=True,):
        r = ["s_abiotic_elev_allow", "s_abiotic_slope_allow", "s_abiotic_dir_allow", "s_abiotic_cur_allow", "s_abiotic_border_allow",]
        if (not availability_conditions):
            return r
        if (self.s_distribution_method=="volume"):
            return ["s_abiotic_elev_allow",]
        if  (not self.is_using_surf):
            return []
        return r

    s_abiotic_master_allow : bpy.props.BoolProperty( 
        name=translate("Master Toggle"),
        description=translate("Mute/Unmute all features of this category in one click"),
        default=True, 
        update=scattering.update_factory.factory("s_abiotic_master_allow", sync_support=False,),
        )

    ########## ########## Elevation

    s_abiotic_elev_allow : bpy.props.BoolProperty(
        name=translate("Elevation Abiotic Factors"),
        description=translate("Influence your distribution density and instances scale depending on their location along the Z axis"),
        default=False,
        update=scattering.update_factory.factory("s_abiotic_elev_allow",),
        )
    s_abiotic_elev_space : bpy.props.EnumProperty(   
        name=translate("Space"),
        description=translate("Evaluation Space.\nChoose how you would like to evaluate your object(s) abiotic mask depending on their relative transformation"),
        default="local", 
        items= ( ("local", translate("Local"), translate("Calculate the abiotic mask while considering your object(s) transforms. The mask will stay stable and consistent, following the object(s) transforms you are scattering upon"), "ORIENTATION_LOCAL",0 ),
                 ("global", translate("Global"), translate("Calculate the abiotic mask considering your object(s) with its transforms applied"), "WORLD",1 ),
               ),
        update=scattering.update_factory.factory("s_abiotic_elev_space",),
        )
    s_abiotic_elev_method : bpy.props.EnumProperty(   
        name=translate("Elevation Method"),
        description=translate("Choose how you would like to compute the altitude values"),
        default="percentage", 
        items= ( ("percentage", translate("Percentage"),translate("The elevation information will be adjusted to fit within the minimum and maximum altitude range, letting you work with values as a percentage of the total height"), "TOPATCH:W_PERCENTAGE",0 ),
                 ("altitude", translate("Altitude"), translate("The elevation informations will use the raw altitude values, being the local or global Z coordinates"), "TOPATCH:W_MEASURE_HEIGHT",1 ),
               ),
        update=scattering.update_factory.factory("s_abiotic_elev_method",),
        )
    #percentage parameters (need a refactor, but would break users presets)
    s_abiotic_elev_min_value_local : bpy.props.FloatProperty(
        name=translate("Minimal"),
        description=translate("Any areas located on an elevation below this number will be part of the abiotic mask"),
        subtype="PERCENTAGE",
        default=0,
        min=0, 
        max=100,  
        precision=1,
        update=scattering.update_factory.factory("s_abiotic_elev_min_value_local", delay_support=True,),
        )
    s_abiotic_elev_min_falloff_local : bpy.props.FloatProperty(
        name=translate("Transition"),
        description=translate("Add a smoothing threshold to both ends of the range defined by the value above, creating a gradual effect rather than a sharp cut-off at the mask boundaries"),
        subtype="PERCENTAGE",
        default=0,
        min=0, 
        max=100, 
        soft_max=100, 
        precision=1,
        update=scattering.update_factory.factory("s_abiotic_elev_min_falloff_local", delay_support=True,),
        ) 
    s_abiotic_elev_max_value_local : bpy.props.FloatProperty(
        name=translate("Maximal"),
        description=translate("Any areas located on an elevation above this number will be part of the abiotic mask"),
        subtype="PERCENTAGE",
        default=75,
        min=0, 
        max=100, 
        precision=1,
        update=scattering.update_factory.factory("s_abiotic_elev_max_value_local", delay_support=True,),
        ) 
    s_abiotic_elev_max_falloff_local : bpy.props.FloatProperty(
        name=translate("Transition"),
        description=translate("Add a smoothing threshold to both ends of the range defined by the value above, creating a gradual effect rather than a sharp cut-off at the mask boundaries"),
        subtype="PERCENTAGE",
        default=5,
        min=0, 
        max=100, 
        soft_max=100, 
        precision=1,
        update=scattering.update_factory.factory("s_abiotic_elev_max_falloff_local", delay_support=True,),
        )
    #altitude parameters (need a refactor, but would break users presets)
    s_abiotic_elev_min_value_global : bpy.props.FloatProperty(
        name=translate("Minimal"),
        description=translate("Any areas located on an elevation below this number will be part of the abiotic mask"),
        subtype="DISTANCE",
        default=0,
        precision=1,
        update=scattering.update_factory.factory("s_abiotic_elev_min_value_global", delay_support=True,),
        )
    s_abiotic_elev_min_falloff_global : bpy.props.FloatProperty(
        name=translate("Transition"),
        description=translate("Add a smoothing threshold to both ends of the range defined by the value above, creating a gradual effect rather than a sharp cut-off at the mask boundaries"),
        subtype="DISTANCE",
        default=0,
        min=0, 
        precision=1,
        update=scattering.update_factory.factory("s_abiotic_elev_min_falloff_global", delay_support=True,),
        ) 
    s_abiotic_elev_max_value_global : bpy.props.FloatProperty(
        name=translate("Maximal"),
        description=translate("Any areas located on an elevation above this number will be part of the abiotic mask"),
        subtype="DISTANCE",
        default=10,
        precision=1,
        update=scattering.update_factory.factory("s_abiotic_elev_max_value_global", delay_support=True,),
        ) 
    s_abiotic_elev_max_falloff_global : bpy.props.FloatProperty(
        name=translate("Transition"),
        description=translate("Add a smoothing threshold to both ends of the range defined by the value above, creating a gradual effect rather than a sharp cut-off at the mask boundaries"),
        subtype="DISTANCE",
        default=0,
        min=0, 
        precision=1,
        update=scattering.update_factory.factory("s_abiotic_elev_max_falloff_global", delay_support=True,),
        ) 
    #remap
    s_abiotic_elev_fallremap_allow : bpy.props.BoolProperty(
        name=translate("Transition Control"),
        description=translate("Control the transition falloff by remapping the values with a curve-map graph or by adding a procedural noise transition to this falloff.\n\n• Please note that this feature assumes there is a transition distance to work with"),
        default=False, 
        update=scattering.update_factory.factory("s_abiotic_elev_fallremap_allow",),
        )
    s_abiotic_elev_fallremap_revert : bpy.props.BoolProperty(
        name=translate("Reverse Transition"),
        description=translate("Reverse the transition. This option will in fact remap the values from '0-1' to '1-0'"),
        default=False,
        update=scattering.update_factory.factory("s_abiotic_elev_fallremap_revert",),
        )
    s_abiotic_elev_fallnoisy_strength : bpy.props.FloatProperty(
        name=translate("Strength"), 
        description=translate("Combine the distance transition with a noise pattern. Great to make the transition look less uniform and more natural. Set this value to 0 to disable the noise overlay entirely"),
        default=0, min=0, max=5, precision=3,
        update=scattering.update_factory.factory("s_abiotic_elev_fallnoisy_strength", delay_support=True,),
        )
    s_abiotic_elev_fallnoisy_space : bpy.props.EnumProperty(
        name="NOT IN GUI",
        default="local",
        items= ( ("local", translate("Local"), "", "ORIENTATION_LOCAL",0 ),
                 ("global", translate("Global"), "", "WORLD",1 ),
               ),
        update=scattering.update_factory.factory("s_abiotic_elev_fallnoisy_space"),
        )
    s_abiotic_elev_fallnoisy_scale : bpy.props.FloatProperty(
        name=translate("Scale"),
        description=translate("The scale of a procedural texture.\n• A value of '0.01' will creates a large noise pattern.\n• A value of '10.0' will create a small pattern"),
        default=0.5, min=0, soft_max=2, precision=3, 
        update=scattering.update_factory.factory("s_abiotic_elev_fallnoisy_scale", delay_support=True,),
        )
    s_abiotic_elev_fallnoisy_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        description=translate("Change this value to randomize the result.\n\nIn 3D graphics, a seed is a starting value used by a random number generator to produce a sequence of random-looking numbers. These numbers can control things like the position, rotation, or scale of objects in a scene. Using the same seed will always generate the same 'random' result, which helps keep things consistent when needed."),
        update=scattering.update_factory.factory("s_abiotic_elev_fallnoisy_seed", delay_support=True,),
        )
    s_abiotic_elev_fallnoisy_is_random_seed : bpy.props.BoolProperty(
        name=translate("Randomize Seed"),
        description=translate("Randomize the value of the hereby seed property.\n\n• Note that pressing 'ALT' while clicking on this button will garantee the attribution of an unique seed value of this property for all selected-system(s)"),
        default=False,
        update=scattering.update_factory.factory("s_abiotic_elev_fallnoisy_is_random_seed",),
        )
    s_abiotic_elev_fallremap_data : bpy.props.StringProperty(
        set=scattering.update_factory.fallremap_setter("s_abiotic_elev.fallremap"),
        get=scattering.update_factory.fallremap_getter("s_abiotic_elev.fallremap"),
        )
    #Feature Influence
    s_abiotic_elev_dist_infl_allow : bpy.props.BoolProperty(name=translate("Enable Influence"), default=True, update=scattering.update_factory.factory("s_abiotic_elev_dist_infl_allow",),)
    s_abiotic_elev_dist_influence : bpy.props.FloatProperty(name=translate("Density"), description=translate("Influence your distribution density, you'll be able to adjust the intensity of the influence by changing this slider"), default=100, subtype="PERCENTAGE", min=0, max=100, precision=1, update=scattering.update_factory.factory("s_abiotic_elev_dist_influence", delay_support=True,),)
    s_abiotic_elev_dist_revert : bpy.props.BoolProperty(name=translate("Reverse Influence"), update=scattering.update_factory.factory("s_abiotic_elev_dist_revert",),)
    s_abiotic_elev_scale_infl_allow : bpy.props.BoolProperty(name=translate("Enable Influence"), default=True, update=scattering.update_factory.factory("s_abiotic_elev_scale_infl_allow",),)
    s_abiotic_elev_scale_influence: bpy.props.FloatProperty(name=translate("Scale"), description=translate("Influence your distributed instances scale, you'll be able to adjust the intensity of the influence by changing this slider"), default=30, subtype="PERCENTAGE", min=0, max=100, precision=1, update=scattering.update_factory.factory("s_abiotic_elev_scale_influence", delay_support=True,),)
    s_abiotic_elev_scale_revert : bpy.props.BoolProperty(name=translate("Reverse Influence"), update=scattering.update_factory.factory("s_abiotic_elev_scale_revert",),)
    #Feature Mask
    codegen_featuremask_properties(scope_ref=__annotations__, name="s_abiotic_elev",)

    ########## ########## Slope

    s_abiotic_slope_allow : bpy.props.BoolProperty(
        name=translate("Slope Abiotic Factors"),
        description=translate("Influence your distribution density and instances scale depending on the the slope angle of the area where they are located"),
        default=False,
        update=scattering.update_factory.factory("s_abiotic_slope_allow",),
        )
    s_abiotic_slope_space : bpy.props.EnumProperty(   
        name=translate("Space"),
        description=translate("Evaluation Space.\nChoose how you would like to evaluate your object(s) abiotic mask depending on their relative transformation"),
        default="local", 
        items= ( ("local", translate("Local"), translate("Calculate the abiotic mask while considering your object(s) transforms. The mask will stay stable and consistent, following the object(s) transforms you are scattering upon"), "ORIENTATION_LOCAL",0 ),
                 ("global", translate("Global"), translate("Calculate the abiotic mask considering your object(s) with its transforms applied"), "WORLD",1 ),
               ),
        update=scattering.update_factory.factory("s_abiotic_slope_space",),
        )
    s_abiotic_slope_absolute : bpy.props.BoolProperty(
        default=True,
        name=translate("Absolute Slope"),
        description=translate("Consider negative slope angles as positive"),
        update=scattering.update_factory.factory("s_abiotic_slope_absolute"),
        )
    s_abiotic_slope_smoothing_allow : bpy.props.BoolProperty(
        name=translate("Smoothing"), 
        description=translate("Evaluate angles on a smoothend geometry to ensure your effect isn’t impacted by the smallest surface imperfections of your mesh.\n\n• Note that this feature might be slow to compute if you are working with geometries heavy on polycount"),
        default=False, 
        update=scattering.update_factory.factory("s_abiotic_slope_smoothing_allow"),
        )
    s_abiotic_slope_smoothing_value : bpy.props.FloatProperty(
        name=translate("Factor"),
        description=translate("An influence factor of an effect is a value that determines how strong the effect is. A higher factor means more impact, while lower factor means less"),
        default=0.35,
        min=0,
        soft_max=1,
        precision=3,
        update=scattering.update_factory.factory("s_abiotic_slope_smoothing_value", delay_support=True,),
        )
    #parameters
    s_abiotic_slope_min_value : bpy.props.FloatProperty(
        name=translate("Minimal"),
        description=translate("Any slope angles below this number will be part of the abiotic mask"),
        subtype="ANGLE",
        default=0,
        min=0, 
        max=1.5708,
        precision=1,
        update=scattering.update_factory.factory("s_abiotic_slope_min_value", delay_support=True,),
        )
    s_abiotic_slope_min_falloff : bpy.props.FloatProperty(
        name=translate("Transition"),
        description=translate("Add a smoothing threshold to both ends of the range defined by the value above, creating a gradual effect rather than a sharp cut-off at the mask boundaries"),
        subtype="ANGLE",
        default=0,
        min=0, 
        max=1.5708, 
        soft_max=0.349066, 
        precision=3,
        update=scattering.update_factory.factory("s_abiotic_slope_min_falloff", delay_support=True,),
        ) 
    s_abiotic_slope_max_value : bpy.props.FloatProperty(
        name=translate("Maximal"),
        description=translate("Any slope angles above this number will be part of the abiotic mask"),
        subtype="ANGLE",
        default=0.2617994, #==15 degrees
        min=0, 
        max=1.5708,
        precision=1,
        update=scattering.update_factory.factory("s_abiotic_slope_max_value", delay_support=True,),
        ) 
    s_abiotic_slope_max_falloff : bpy.props.FloatProperty(
        name=translate("Transition"),
        description=translate("Add a smoothing threshold to both ends of the range defined by the value above, creating a gradual effect rather than a sharp cut-off at the mask boundaries"),
        subtype="ANGLE",
        default=0,
        min=0, 
        max=1.5708, 
        soft_max=0.349066, 
        precision=3,
        update=scattering.update_factory.factory("s_abiotic_slope_max_falloff", delay_support=True,),
        ) 
    #remap
    s_abiotic_slope_fallremap_allow : bpy.props.BoolProperty(
        name=translate("Transition Control"),
        description=translate("Control the transition falloff by remapping the values with a curve-map graph or by adding a procedural noise transition to this falloff.\n\n• Please note that this feature assumes there is a transition distance to work with"),
        default=False, 
        update=scattering.update_factory.factory("s_abiotic_slope_fallremap_allow",),
        )
    s_abiotic_slope_fallremap_revert : bpy.props.BoolProperty(
        name=translate("Reverse Transition"),
        description=translate("Reverse the transition. This option will in fact remap the values from '0-1' to '1-0'"),
        default=False,
        update=scattering.update_factory.factory("s_abiotic_slope_fallremap_revert",),
        )
    s_abiotic_slope_fallnoisy_strength : bpy.props.FloatProperty(
        name=translate("Strength"), 
        description=translate("Combine the distance transition with a noise pattern. Great to make the transition look less uniform and more natural. Set this value to 0 to disable the noise overlay entirely"),
        default=0, min=0, max=5, precision=3,
        update=scattering.update_factory.factory("s_abiotic_slope_fallnoisy_strength", delay_support=True,),
        )
    s_abiotic_slope_fallnoisy_space : bpy.props.EnumProperty(
        name="NOT IN GUI",
        default="local",
        items= ( ("local", translate("Local"), "", "ORIENTATION_LOCAL",0 ),
                 ("global", translate("Global"), "", "WORLD",1 ),
               ),
        update=scattering.update_factory.factory("s_abiotic_slope_fallnoisy_space"),
        )
    s_abiotic_slope_fallnoisy_scale : bpy.props.FloatProperty(
        name=translate("Scale"),
        description=translate("The scale of a procedural texture.\n• A value of '0.01' will creates a large noise pattern.\n• A value of '10.0' will create a small pattern"),
        default=0.5, min=0, soft_max=2, precision=3, 
        update=scattering.update_factory.factory("s_abiotic_slope_fallnoisy_scale", delay_support=True,),
        )
    s_abiotic_slope_fallnoisy_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        description=translate("Change this value to randomize the result.\n\nIn 3D graphics, a seed is a starting value used by a random number generator to produce a sequence of random-looking numbers. These numbers can control things like the position, rotation, or scale of objects in a scene. Using the same seed will always generate the same 'random' result, which helps keep things consistent when needed."),
        update=scattering.update_factory.factory("s_abiotic_slope_fallnoisy_seed", delay_support=True,),
        )
    s_abiotic_slope_fallnoisy_is_random_seed : bpy.props.BoolProperty(
        name=translate("Randomize Seed"),
        description=translate("Randomize the value of the hereby seed property.\n\n• Note that pressing 'ALT' while clicking on this button will garantee the attribution of an unique seed value of this property for all selected-system(s)"),
        default=False,
        update=scattering.update_factory.factory("s_abiotic_slope_fallnoisy_is_random_seed",),
        )
    s_abiotic_slope_fallremap_data : bpy.props.StringProperty(
        set=scattering.update_factory.fallremap_setter("s_abiotic_slope.fallremap"),
        get=scattering.update_factory.fallremap_getter("s_abiotic_slope.fallremap"),
        )
    #Feature Influence
    s_abiotic_slope_dist_infl_allow : bpy.props.BoolProperty(name=translate("Enable Influence"), default=True, update=scattering.update_factory.factory("s_abiotic_slope_dist_infl_allow",),)
    s_abiotic_slope_dist_influence : bpy.props.FloatProperty(name=translate("Density"), description=translate("Influence your distribution density, you'll be able to adjust the intensity of the influence by changing this slider"), default=100, subtype="PERCENTAGE", min=0, max=100, precision=1, update=scattering.update_factory.factory("s_abiotic_slope_dist_influence", delay_support=True,),)
    s_abiotic_slope_dist_revert : bpy.props.BoolProperty(name=translate("Reverse Influence"), update=scattering.update_factory.factory("s_abiotic_slope_dist_revert",),)
    s_abiotic_slope_scale_infl_allow : bpy.props.BoolProperty(name=translate("Enable Influence"), default=True, update=scattering.update_factory.factory("s_abiotic_slope_scale_infl_allow",),)
    s_abiotic_slope_scale_influence: bpy.props.FloatProperty(name=translate("Scale"), description=translate("Influence your distributed instances scale, you'll be able to adjust the intensity of the influence by changing this slider"), default=30, subtype="PERCENTAGE", min=0, max=100, precision=1, update=scattering.update_factory.factory("s_abiotic_slope_scale_influence", delay_support=True,),)
    s_abiotic_slope_scale_revert : bpy.props.BoolProperty(name=translate("Reverse Influence"), update=scattering.update_factory.factory("s_abiotic_slope_scale_revert",),)
    #Feature Mask
    codegen_featuremask_properties(scope_ref=__annotations__, name="s_abiotic_slope",)

    ########## ########## Direction

    s_abiotic_dir_allow : bpy.props.BoolProperty(
        name=translate("Directional Abiotic Factors"),
        description=translate("Influence your distribution density and instances scale depending on the slope orientation of the area where they are located"),
        default=False,
        update=scattering.update_factory.factory("s_abiotic_dir_allow",),
        )
    s_abiotic_dir_space : bpy.props.EnumProperty(   
        name=translate("Space"),
        description=translate("Evaluation Space.\nChoose how you would like to evaluate your object(s) abiotic mask depending on their relative transformation"),
        default="local", 
        items= ( ("local", translate("Local"), translate("Calculate the abiotic mask while considering your object(s) transforms. The mask will stay stable and consistent, following the object(s) transforms you are scattering upon"), "ORIENTATION_LOCAL",0 ),
                 ("global", translate("Global"), translate("Calculate the abiotic mask considering your object(s) with its transforms applied"), "WORLD",1 ),
               ),
        update=scattering.update_factory.factory("s_abiotic_dir_space",),
        )
    s_abiotic_dir_direction : bpy.props.FloatVectorProperty(
        name=translate("Direction"),
        description=translate("The abiotic mask will be created according to the areas of your surface(s) facing toward this direction"),
        subtype="DIRECTION",
        default=(0.701299,0.493506,0.514423),
        update=scattering.update_factory.factory("s_abiotic_dir_direction", delay_support=True,),
        )
    
    def ui_abiotic_dir_direction_euler_upd(self,context):
        e = getattr(self, "ui_abiotic_dir_direction_euler")
        v = mathutils.Vector((0.0,0.0,1.0))
        v.rotate(e)
        setattr(self,"s_abiotic_dir_direction",v)
        return None

    ui_abiotic_dir_direction_euler : bpy.props.FloatVectorProperty( #alternative ui for prop above
        name=translate("Euler Representation"),
        description=translate("Changing this property will update the hereby direction property converted from euler angles"),
        subtype="EULER",
        #get=lambda self: mathutils.Vector(getattr(self, 's_abiotic_dir_direction')).to_track_quat('Z', 'Y').to_euler(),
        update=ui_abiotic_dir_direction_euler_upd,
        )

    s_abiotic_dir_smoothing_allow : bpy.props.BoolProperty(
        name=translate("Smoothing"), 
        description=translate("Evaluate angles on a smoothend geometry to ensure your effect isn’t impacted by the smallest surface imperfections of your mesh.\n\n• Note that this feature might be slow to compute if you are working with geometries heavy on polycount"),
        default=False, 
        update=scattering.update_factory.factory("s_abiotic_dir_smoothing_allow"),
        )
    s_abiotic_dir_smoothing_value : bpy.props.FloatProperty(
        name=translate("Factor"),
        description=translate("An influence factor of an effect is a value that determines how strong the effect is. A higher factor means more impact, while lower factor means less"),
        default=0.35,
        min=0,
        soft_max=1,
        precision=3,
        update=scattering.update_factory.factory("s_abiotic_dir_smoothing_value", delay_support=True,),
        )
    s_abiotic_dir_max : bpy.props.FloatProperty(
        name=translate("Theshold"),
        description=translate("Any slope angles equals to the direction specified above within range of this threshold value will be considered as an abiotic mask"),
        subtype="ANGLE",
        default=0.261799,
        soft_min=0, 
        soft_max=1, 
        precision=3,
        update=scattering.update_factory.factory("s_abiotic_dir_max", delay_support=True,),
        ) 
    s_abiotic_dir_treshold : bpy.props.FloatProperty(
        name=translate("Transition"),
        description=translate("Add a smoothing threshold to both ends of the range defined by the value above, creating a gradual effect rather than a sharp cut-off at the mask boundaries"),
        subtype="ANGLE",
        default=0.0872665,
        soft_min=0,
        soft_max=1,
        precision=3,
        update=scattering.update_factory.factory("s_abiotic_dir_treshold", delay_support=True,),
        ) 
    #remap
    s_abiotic_dir_fallremap_allow : bpy.props.BoolProperty(
        name=translate("Transition Control"),
        description=translate("Control the transition falloff by remapping the values with a curve-map graph or by adding a procedural noise transition to this falloff.\n\n• Please note that this feature assumes there is a transition distance to work with"),
        default=False, 
        update=scattering.update_factory.factory("s_abiotic_dir_fallremap_allow",),
        )
    s_abiotic_dir_fallremap_revert : bpy.props.BoolProperty(
        name=translate("Reverse Transition"),
        description=translate("Reverse the transition. This option will in fact remap the values from '0-1' to '1-0'"),
        default=False,
        update=scattering.update_factory.factory("s_abiotic_dir_fallremap_revert",),
        )
    s_abiotic_dir_fallnoisy_strength : bpy.props.FloatProperty(
        name=translate("Strength"), 
        description=translate("Combine the distance transition with a noise pattern. Great to make the transition look less uniform and more natural. Set this value to 0 to disable the noise overlay entirely"),
        default=0, min=0, max=5, precision=3,
        update=scattering.update_factory.factory("s_abiotic_dir_fallnoisy_strength", delay_support=True,),
        )
    s_abiotic_dir_fallnoisy_space : bpy.props.EnumProperty(
        name="NOT IN GUI",
        default="local",
        items= ( ("local", translate("Local"), "", "ORIENTATION_LOCAL",0 ),
                 ("global", translate("Global"), "", "WORLD",1 ),
               ),
        update=scattering.update_factory.factory("s_abiotic_dir_fallnoisy_space"),
        )
    s_abiotic_dir_fallnoisy_scale : bpy.props.FloatProperty(
        name=translate("Scale"),
        description=translate("The scale of a procedural texture.\n• A value of '0.01' will creates a large noise pattern.\n• A value of '10.0' will create a small pattern"),
        default=0.5, min=0, soft_max=2, precision=3, 
        update=scattering.update_factory.factory("s_abiotic_dir_fallnoisy_scale", delay_support=True,),
        )
    s_abiotic_dir_fallnoisy_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        description=translate("Change this value to randomize the result.\n\nIn 3D graphics, a seed is a starting value used by a random number generator to produce a sequence of random-looking numbers. These numbers can control things like the position, rotation, or scale of objects in a scene. Using the same seed will always generate the same 'random' result, which helps keep things consistent when needed."),
        update=scattering.update_factory.factory("s_abiotic_dir_fallnoisy_seed", delay_support=True,),
        )
    s_abiotic_dir_fallnoisy_is_random_seed : bpy.props.BoolProperty(
        name=translate("Randomize Seed"),
        description=translate("Randomize the value of the hereby seed property.\n\n• Note that pressing 'ALT' while clicking on this button will garantee the attribution of an unique seed value of this property for all selected-system(s)"),
        default=False,
        update=scattering.update_factory.factory("s_abiotic_dir_fallnoisy_is_random_seed",),
        )
    s_abiotic_dir_fallremap_data : bpy.props.StringProperty(
        set=scattering.update_factory.fallremap_setter("s_abiotic_dir.fallremap"),
        get=scattering.update_factory.fallremap_getter("s_abiotic_dir.fallremap"),
        )
    #Feature Influence
    s_abiotic_dir_dist_infl_allow : bpy.props.BoolProperty(name=translate("Enable Influence"), default=True, update=scattering.update_factory.factory("s_abiotic_dir_dist_infl_allow",),)
    s_abiotic_dir_dist_influence : bpy.props.FloatProperty(name=translate("Density"), description=translate("Influence your distribution density, you'll be able to adjust the intensity of the influence by changing this slider"), default=100, subtype="PERCENTAGE", min=0, max=100, precision=1, update=scattering.update_factory.factory("s_abiotic_dir_dist_influence", delay_support=True,),)
    s_abiotic_dir_dist_revert : bpy.props.BoolProperty(name=translate("Reverse Influence"), update=scattering.update_factory.factory("s_abiotic_dir_dist_revert",),)
    s_abiotic_dir_scale_infl_allow : bpy.props.BoolProperty(name=translate("Enable Influence"), default=True, update=scattering.update_factory.factory("s_abiotic_dir_scale_infl_allow",),)
    s_abiotic_dir_scale_influence: bpy.props.FloatProperty(name=translate("Scale"), description=translate("Influence your distributed instances scale, you'll be able to adjust the intensity of the influence by changing this slider"), default=30, subtype="PERCENTAGE", min=0, max=100, precision=1, update=scattering.update_factory.factory("s_abiotic_dir_scale_influence", delay_support=True,),)
    s_abiotic_dir_scale_revert : bpy.props.BoolProperty(name=translate("Reverse Influence"), update=scattering.update_factory.factory("s_abiotic_dir_scale_revert",),)
    #Feature Mask
    codegen_featuremask_properties(scope_ref=__annotations__, name="s_abiotic_dir",)

    ########## ########## Edge Curvature

    s_abiotic_cur_allow : bpy.props.BoolProperty(
        name=translate("Curvature Abiotic Factors"),
        description=translate("Influence your distribution density and instances scale depending on the slope curvature of the area where they are located.\n\n• The curvature of a terrain describes how its surface bends, highlighting peaks (convex areas) and valleys (concave areas), indicating the slope and flow of the landscape"),
        default=False,
        update=scattering.update_factory.factory("s_abiotic_cur_allow",),
        )
    s_abiotic_cur_type : bpy.props.EnumProperty(   
        name=translate("Type"),
        description=translate("Choose your curvature type"),
        default="convex", 
        items= ( ("convex", translate("Convex"), translate("Compute only 'convex' angles, which are areas facing outward"), "SPHERECURVE",0 ),
                 ("concave", translate("Concave"), translate("Compute only 'concave' angles, which are areas facing inward"), "SHARPCURVE",1 ),
                 ("both", translate("Curvature"), translate("Compute both 'concave' and 'convex' angles in a same map"), "FORCE_HARMONIC",2 ),
               ),
        update=scattering.update_factory.factory("s_abiotic_cur_type",),
        )
    s_abiotic_cur_smoothing_allow : bpy.props.BoolProperty(
        name=translate("Smoothing"), 
        description=translate("Evaluate angles on a smoothend geometry to ensure your effect isn’t impacted by the smallest surface imperfections of your mesh.\n\n• Note that this feature might be slow to compute if you are working with geometries heavy on polycount"),
        default=False, 
        update=scattering.update_factory.factory("s_abiotic_cur_smoothing_allow"),
        )
    s_abiotic_cur_smoothing_value : bpy.props.FloatProperty(
        name=translate("Factor"),
        description=translate("An influence factor of an effect is a value that determines how strong the effect is. A higher factor means more impact, while lower factor means less"),
        default=0.35,
        min=0,
        soft_max=1,
        precision=3,
        update=scattering.update_factory.factory("s_abiotic_cur_smoothing_value", delay_support=True,),
        )
    s_abiotic_cur_max: bpy.props.FloatProperty(
        name=translate("Maximal"),
        description=translate("Define the maximum curvature angle, as a percentage, to include in the abiotic mask"),
        subtype="PERCENTAGE",
        default=55,
        min=0,
        max=100,
        precision=1,
        update=scattering.update_factory.factory("s_abiotic_cur_max", delay_support=True,),
        )
    s_abiotic_cur_treshold: bpy.props.FloatProperty(
        name=translate("Transition"),
        description=translate("Add a smoothing threshold to both ends of the range defined by the value above, creating a gradual effect rather than a sharp cut-off at the mask boundaries"),
        subtype="PERCENTAGE",
        default=0,
        min=0,
        max=100,
        precision=1,
        update=scattering.update_factory.factory("s_abiotic_cur_treshold", delay_support=True,),
        )
    #remap
    s_abiotic_cur_fallremap_allow : bpy.props.BoolProperty(
        name=translate("Transition Control"),
        description=translate("Control the transition falloff by remapping the values with a curve-map graph or by adding a procedural noise transition to this falloff.\n\n• Please note that this feature assumes there is a transition distance to work with"),
        default=False, 
        update=scattering.update_factory.factory("s_abiotic_cur_fallremap_allow",),
        )
    s_abiotic_cur_fallremap_revert : bpy.props.BoolProperty(
        name=translate("Reverse Transition"),
        description=translate("Reverse the transition. This option will in fact remap the values from '0-1' to '1-0'"),
        default=False,
        update=scattering.update_factory.factory("s_abiotic_cur_fallremap_revert",),
        )
    s_abiotic_cur_fallnoisy_strength : bpy.props.FloatProperty(
        name=translate("Strength"), 
        description=translate("Combine the distance transition with a noise pattern. Great to make the transition look less uniform and more natural. Set this value to 0 to disable the noise overlay entirely"),
        default=0, min=0, max=5, precision=3,
        update=scattering.update_factory.factory("s_abiotic_cur_fallnoisy_strength", delay_support=True,),
        )
    s_abiotic_cur_fallnoisy_space : bpy.props.EnumProperty(
        name="NOT IN GUI",
        default="local",
        items= ( ("local", translate("Local"), "", "ORIENTATION_LOCAL",0 ),
                 ("global", translate("Global"), "", "WORLD",1 ),
               ),
        update=scattering.update_factory.factory("s_abiotic_cur_fallnoisy_space"),
        )
    s_abiotic_cur_fallnoisy_scale : bpy.props.FloatProperty(
        name=translate("Scale"),
        description=translate("The scale of a procedural texture.\n• A value of '0.01' will creates a large noise pattern.\n• A value of '10.0' will create a small pattern"),
        default=0.5, min=0, soft_max=2, precision=3, 
        update=scattering.update_factory.factory("s_abiotic_cur_fallnoisy_scale", delay_support=True,),
        )
    s_abiotic_cur_fallnoisy_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        description=translate("Change this value to randomize the result.\n\nIn 3D graphics, a seed is a starting value used by a random number generator to produce a sequence of random-looking numbers. These numbers can control things like the position, rotation, or scale of objects in a scene. Using the same seed will always generate the same 'random' result, which helps keep things consistent when needed."),
        update=scattering.update_factory.factory("s_abiotic_cur_fallnoisy_seed", delay_support=True,),
        )
    s_abiotic_cur_fallnoisy_is_random_seed : bpy.props.BoolProperty(
        name=translate("Randomize Seed"),
        description=translate("Randomize the value of the hereby seed property.\n\n• Note that pressing 'ALT' while clicking on this button will garantee the attribution of an unique seed value of this property for all selected-system(s)"),
        default=False,
        update=scattering.update_factory.factory("s_abiotic_cur_fallnoisy_is_random_seed",),
        )
    s_abiotic_cur_fallremap_data : bpy.props.StringProperty(
        set=scattering.update_factory.fallremap_setter("s_abiotic_cur.fallremap"),
        get=scattering.update_factory.fallremap_getter("s_abiotic_cur.fallremap"),
        )
    #Feature Influence
    s_abiotic_cur_dist_infl_allow : bpy.props.BoolProperty(name=translate("Enable Influence"), default=True, update=scattering.update_factory.factory("s_abiotic_cur_dist_infl_allow",),)
    s_abiotic_cur_dist_influence : bpy.props.FloatProperty(name=translate("Density"), description=translate("Influence your distribution density, you'll be able to adjust the intensity of the influence by changing this slider"), default=100, subtype="PERCENTAGE", min=0, max=100, precision=1, update=scattering.update_factory.factory("s_abiotic_cur_dist_influence", delay_support=True,),)
    s_abiotic_cur_dist_revert : bpy.props.BoolProperty(name=translate("Reverse Influence"), update=scattering.update_factory.factory("s_abiotic_cur_dist_revert",),)
    s_abiotic_cur_scale_infl_allow : bpy.props.BoolProperty(name=translate("Enable Influence"), default=True, update=scattering.update_factory.factory("s_abiotic_cur_scale_infl_allow",),)
    s_abiotic_cur_scale_influence: bpy.props.FloatProperty(name=translate("Scale"), description=translate("Influence your distributed instances scale, you'll be able to adjust the intensity of the influence by changing this slider"), default=30, subtype="PERCENTAGE", min=0, max=100, precision=1, update=scattering.update_factory.factory("s_abiotic_cur_scale_influence", delay_support=True,),)
    s_abiotic_cur_scale_revert : bpy.props.BoolProperty(name=translate("Reverse Influence"), update=scattering.update_factory.factory("s_abiotic_cur_scale_revert",),)
    #Feature Mask
    codegen_featuremask_properties(scope_ref=__annotations__, name="s_abiotic_cur",)

    ########## ########## Edge Border

    s_abiotic_border_allow : bpy.props.BoolProperty(
        name=translate("Border Abiotic Factors"),
        description=translate("Influence your distribution density and instances scale depending on how close/far they are located from their surface(s) mesh boundary edges"),
        default=False,
        update=scattering.update_factory.factory("s_abiotic_border_allow",),
        )
    s_abiotic_border_space : bpy.props.EnumProperty(   
        name=translate("Space"),
        description=translate("Evaluation Space.\nChoose how you would like to evaluate your object(s) abiotic mask depending on their relative transformation"),
        default="local", 
        items= ( ("local", translate("Local"), translate("Calculate the abiotic mask while considering your object(s) transforms. The mask will stay stable and consistent, following the object(s) transforms you are scattering upon"), "ORIENTATION_LOCAL",0 ),
                 ("global", translate("Global"), translate("Calculate the abiotic mask considering your object(s) with its transforms applied"), "WORLD",1 ),
               ),
        update=scattering.update_factory.factory("s_abiotic_border_space",),
        )
    s_abiotic_border_max : bpy.props.FloatProperty( #too late to change property name
        name=translate("Offset"), 
        description=translate("Minimal distance defining the border offset range"),
        subtype="DISTANCE",
        default=1.0,
        min=0,
        update=scattering.update_factory.factory("s_abiotic_border_max", delay_support=True,),
        )
    s_abiotic_border_treshold : bpy.props.FloatProperty(
        name=translate("Transition"),
        description=translate("Add a transition distance after the offset distance defined above"),
        subtype="DISTANCE",
        default=0.5,
        min=0,
        update=scattering.update_factory.factory("s_abiotic_border_treshold", delay_support=True,),
        )
    #remap
    s_abiotic_border_fallremap_allow : bpy.props.BoolProperty(
        name=translate("Transition Control"),
        description=translate("Control the transition falloff by remapping the values with a curve-map graph or by adding a procedural noise transition to this falloff.\n\n• Please note that this feature assumes there is a transition distance to work with"),
        default=False, 
        update=scattering.update_factory.factory("s_abiotic_border_fallremap_allow",),
        )
    s_abiotic_border_fallremap_revert : bpy.props.BoolProperty(
        name=translate("Reverse Transition"),
        description=translate("Reverse the transition. This option will in fact remap the values from '0-1' to '1-0'"),
        default=False,
        update=scattering.update_factory.factory("s_abiotic_border_fallremap_revert",),
        )
    s_abiotic_border_fallnoisy_strength : bpy.props.FloatProperty(
        name=translate("Strength"), 
        description=translate("Combine the distance transition with a noise pattern. Great to make the transition look less uniform and more natural. Set this value to 0 to disable the noise overlay entirely"),
        default=0, min=0, max=5, precision=3,
        update=scattering.update_factory.factory("s_abiotic_border_fallnoisy_strength", delay_support=True,),
        )
    s_abiotic_border_fallnoisy_space : bpy.props.EnumProperty(
        name="NOT IN GUI",
        default="local",
        items= ( ("local", translate("Local"), "", "ORIENTATION_LOCAL",0 ),
                 ("global", translate("Global"), "", "WORLD",1 ),
               ),
        update=scattering.update_factory.factory("s_abiotic_border_fallnoisy_space"),
        )
    s_abiotic_border_fallnoisy_scale : bpy.props.FloatProperty(
        name=translate("Scale"),
        description=translate("The scale of a procedural texture.\n• A value of '0.01' will creates a large noise pattern.\n• A value of '10.0' will create a small pattern"),
        default=0.5, min=0, soft_max=2, precision=3, 
        update=scattering.update_factory.factory("s_abiotic_border_fallnoisy_scale", delay_support=True,),
        )
    s_abiotic_border_fallnoisy_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        description=translate("Change this value to randomize the result.\n\nIn 3D graphics, a seed is a starting value used by a random number generator to produce a sequence of random-looking numbers. These numbers can control things like the position, rotation, or scale of objects in a scene. Using the same seed will always generate the same 'random' result, which helps keep things consistent when needed."),
        update=scattering.update_factory.factory("s_abiotic_border_fallnoisy_seed", delay_support=True,),
        )
    s_abiotic_border_fallnoisy_is_random_seed : bpy.props.BoolProperty(
        name=translate("Randomize Seed"),
        description=translate("Randomize the value of the hereby seed property.\n\n• Note that pressing 'ALT' while clicking on this button will garantee the attribution of an unique seed value of this property for all selected-system(s)"),
        default=False,
        update=scattering.update_factory.factory("s_abiotic_border_fallnoisy_is_random_seed",),
        )
    s_abiotic_border_fallremap_data : bpy.props.StringProperty(
        set=scattering.update_factory.fallremap_setter("s_abiotic_border.fallremap"),
        get=scattering.update_factory.fallremap_getter("s_abiotic_border.fallremap"),
        )
    #Feature Influence
    s_abiotic_border_dist_infl_allow : bpy.props.BoolProperty(name=translate("Enable Influence"), default=True, update=scattering.update_factory.factory("s_abiotic_border_dist_infl_allow",),)
    s_abiotic_border_dist_influence : bpy.props.FloatProperty(name=translate("Density"), description=translate("Influence your distribution density, you'll be able to adjust the intensity of the influence by changing this slider"), default=100, subtype="PERCENTAGE", min=0, max=100, precision=1, update=scattering.update_factory.factory("s_abiotic_border_dist_influence", delay_support=True,),)
    s_abiotic_border_dist_revert : bpy.props.BoolProperty(name=translate("Reverse Influence"), update=scattering.update_factory.factory("s_abiotic_border_dist_revert",),)
    s_abiotic_border_scale_infl_allow : bpy.props.BoolProperty(name=translate("Enable Influence"), default=True, update=scattering.update_factory.factory("s_abiotic_border_scale_infl_allow",),)
    s_abiotic_border_scale_influence: bpy.props.FloatProperty(name=translate("Scale"), description=translate("Influence your distributed instances scale, you'll be able to adjust the intensity of the influence by changing this slider"), default=30, subtype="PERCENTAGE", soft_min=0, max=100, precision=1, update=scattering.update_factory.factory("s_abiotic_border_scale_influence", delay_support=True,),)
    s_abiotic_border_scale_revert : bpy.props.BoolProperty(name=translate("Reverse Influence"), update=scattering.update_factory.factory("s_abiotic_border_scale_revert",),)
    #Feature Mask
    codegen_featuremask_properties(scope_ref=__annotations__, name="s_abiotic_border",)

    #Edge Watershed Later? 

    #Edge Data Later ? 
    
    # 88""Yb 88""Yb  dP"Yb  Yb  dP 88 8b    d8 88 888888 Yb  dP
    # 88__dP 88__dP dP   Yb  YbdP  88 88b  d88 88   88    YbdP
    # 88"""  88"Yb  Yb   dP  dPYb  88 88YbdP88 88   88     8P
    # 88     88  Yb  YbodP  dP  Yb 88 88 YY 88 88   88    dP

    ###################### This category of settings keyword is : "s_proximity"

    s_proximity_locked : bpy.props.BoolProperty(description=translate("Lock/Unlock Settings"),)

    def get_s_proximity_main_features(self, availability_conditions=True,):
        r = ["s_proximity_repel1_allow", "s_proximity_repel2_allow", "s_proximity_projbezarea_border_allow", "s_proximity_outskirt_allow",]
        if (not availability_conditions):
            return r
        if (self.s_distribution_method!="projbezarea"):
            r.remove("s_proximity_projbezarea_border_allow")
        if (self.s_distribution_method in ("projbezline","projempties")): 
            r.remove("s_proximity_outskirt_allow")
        return r
    
    s_proximity_master_allow : bpy.props.BoolProperty( 
        name=translate("Master Toggle"),
        description=translate("Mute/Unmute all features of this category in one click"),
        default=True, 
        update=scattering.update_factory.factory("s_proximity_master_allow", sync_support=False,),
        )

    ########## ########## Object-Repel 1

    s_proximity_repel1_allow : bpy.props.BoolProperty( 
        name=translate("Object Repel"),
        description=translate("Influence your distribution density or instances scale and orientations depending on their location in proximity to the objects contained in a chosen collection"),
        default=False, 
        update=scattering.update_factory.factory("s_proximity_repel1_allow",),
        )
    #treshold
    s_proximity_repel1_coll_ptr : bpy.props.StringProperty(
        name=translate("Collection Pointer"),
        search=lambda s,c,e: set(col.name for col in bpy.data.collections if (e in col.name)),
        search_options={'SUGGESTION','SORT'},
        update=scattering.update_factory.factory("s_proximity_repel1_coll_ptr"),
        )
    s_proximity_repel1_type : bpy.props.EnumProperty(   
        name=translate("Proximity Contact"),
        description=translate("Define which part of the reference objects is used to evaluate a proximity distance field. Impacting both the precision of the proximity field and the computational speed required"),
        default="mesh", 
        items= ( ("origin", translate("Origin Point"),translate("Evaluate the proximity only with the location of given objects origin points, this is by far the fastest contact method to compute"),  "ORIENTATION_VIEW",0 ),
                 ("mesh", translate("Meshes Faces"), translate("Evaluate the proximity with the faces of the chosen objects. Note that this process can be extremely diffult to compute"), "MESH_DATA",1 ),
                 ("bb", translate("Bounding-Box"), translate("Evaluate the proximity with the applied bounding box of the given objects"), "CUBE",2 ),
                 ("convexhull", translate("Convex-Hull"), translate("Evaluate the proximity with a generated convex-hull mesh from the given objects"), "MESH_ICOSPHERE",3 ),
                 ("pointcloud", translate("Point-Cloud"), translate("Evaluate the proximity with a generated point cloud of the given objects "), "OUTLINER_OB_POINTCLOUD",4 )
               ),
        update=scattering.update_factory.factory("s_proximity_repel1_type",),
        )
    s_proximity_repel1_volume_allow : bpy.props.BoolProperty(
        name=translate("Consider Volume"),
        description=translate("Only keep areas located inside or outside the volumes of the chosen objects"),
        default=False, 
        update=scattering.update_factory.factory("s_proximity_repel1_volume_allow",),
        )
    s_proximity_repel1_volume_method : bpy.props.EnumProperty(   
        default="out",
        items= ( ("in",  translate("Inside"), translate("Only keep areas located inside or outside the volumes of the chosen objects"),"",0), 
                 ("out", translate("Outside"),translate("Only keep areas located inside or outside the volumes of the chosen objects"),"",1)
               ),
        update=scattering.update_factory.factory("s_proximity_repel1_volume_method",),
        )
    s_proximity_repel1_max : bpy.props.FloatProperty(
        name=translate("Minimal"), #too late to change property name
        description=translate("Minimal distance around the object's collided in the proximity field"),
        default=0.5, min=0, subtype="DISTANCE",
        update=scattering.update_factory.factory("s_proximity_repel1_max", delay_support=True,),
        )
    s_proximity_repel1_treshold : bpy.props.FloatProperty(
        name=translate("Transition"),
        description=translate("Add a transition distance after the distance above to create a transition effect"),
        default=0.5, min=0, subtype="DISTANCE",
        update=scattering.update_factory.factory("s_proximity_repel1_treshold", delay_support=True,),
        )
    #distremap
    s_proximity_repel1_fallremap_allow : bpy.props.BoolProperty(
        name=translate("Transition Control"),
        description=translate("Control the transition falloff by remapping the values with a curve-map graph or by adding a procedural noise transition to this falloff.\n\n• Please note that this feature assumes there is a transition distance to work with"),
        default=False, 
        update=scattering.update_factory.factory("s_proximity_repel1_fallremap_allow",),
        )
    s_proximity_repel1_fallremap_revert : bpy.props.BoolProperty(
        name=translate("Reverse Transition"),
        description=translate("Reverse the transition. This option will in fact remap the values from '0-1' to '1-0'"),
        default=False,
        update=scattering.update_factory.factory("s_proximity_repel1_fallremap_revert",),
        )
    s_proximity_repel1_fallnoisy_strength : bpy.props.FloatProperty(
        name=translate("Strength"), 
        description=translate("Combine the distance transition with a noise pattern. Great to make the transition look less uniform and more natural. Set this value to 0 to disable the noise overlay entirely"),
        default=0, min=0, max=5, precision=3,
        update=scattering.update_factory.factory("s_proximity_repel1_fallnoisy_strength", delay_support=True,),
        )
    s_proximity_repel1_fallnoisy_space : bpy.props.EnumProperty(
        name="NOT IN GUI",
        default="local",
        items= ( ("local", translate("Local"), "", "ORIENTATION_LOCAL",0 ),
                 ("global", translate("Global"), "", "WORLD",1 ),
               ),
        update=scattering.update_factory.factory("s_proximity_repel1_fallnoisy_space"),
        )
    s_proximity_repel1_fallnoisy_scale : bpy.props.FloatProperty(
        name=translate("Scale"),
        description=translate("The scale of a procedural texture.\n• A value of '0.01' will creates a large noise pattern.\n• A value of '10.0' will create a small pattern"),
        default=0.5, min=0, soft_max=2, precision=3, 
        update=scattering.update_factory.factory("s_proximity_repel1_fallnoisy_scale", delay_support=True,),
        )
    s_proximity_repel1_fallnoisy_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        description=translate("Change this value to randomize the result.\n\nIn 3D graphics, a seed is a starting value used by a random number generator to produce a sequence of random-looking numbers. These numbers can control things like the position, rotation, or scale of objects in a scene. Using the same seed will always generate the same 'random' result, which helps keep things consistent when needed."),
        update=scattering.update_factory.factory("s_proximity_repel1_fallnoisy_seed", delay_support=True,),
        )
    s_proximity_repel1_fallnoisy_is_random_seed : bpy.props.BoolProperty(
        name=translate("Randomize Seed"),
        description=translate("Randomize the value of the hereby seed property.\n\n• Note that pressing 'ALT' while clicking on this button will garantee the attribution of an unique seed value of this property for all selected-system(s)"),
        default=False,
        update=scattering.update_factory.factory("s_proximity_repel1_fallnoisy_is_random_seed",),
        )
    s_proximity_repel1_fallremap_data : bpy.props.StringProperty(
        set=scattering.update_factory.fallremap_setter("s_proximity_repel1.fallremap"),
        get=scattering.update_factory.fallremap_getter("s_proximity_repel1.fallremap"),
        )
    #simulation
    s_proximity_repel1_simulation_allow : bpy.props.BoolProperty(
        name=translate("Simulate Collision Imprint Field"),
        description=translate("Instead of calculating a proximity field in real time, simulate a proximity field imprint left behind by any object's/objects passing by.\n\n• Beware: this feature is a simulation set-up and will require an animation playing in the timeline"),
        default=False,
        update=scattering.update_factory.factory("s_proximity_repel1_simulation_allow"),
        )
    s_proximity_repel1_simulation_fadeaway_allow : bpy.props.BoolProperty(
        name=translate("Fade Away Effect"),
        description=translate("The imprints will fade away with time, restoring the effect to its original state"),
        default=False,
        update=scattering.update_factory.factory("s_proximity_repel1_simulation_fadeaway_allow")
        )
    s_proximity_repel1_simulation_fadeaway_method : bpy.props.EnumProperty(
        default="sec",
        items= ( ("sec", translate("Seconds"), translate("Calculate the fade away in seconds units"), "",0 ),
                 ("frame", translate("Frames"), translate("Calculate the fade away in frames units"), "",1 ),
               ),
        update=scattering.update_factory.factory("s_proximity_repel1_simulation_fadeaway_method"),
        )
    s_proximity_repel1_simulation_fadeaway_frame : bpy.props.IntProperty(
        name=translate("Frame"),
        description=translate("Time unit until the fade-away imprint starts to disappear"),
        default=75,
        soft_max=999,
        min=1,
        update=scattering.update_factory.factory("s_proximity_repel1_simulation_fadeaway_frame", delay_support=True,),
        )
    s_proximity_repel1_simulation_fadeaway_sec : bpy.props.FloatProperty(
        name=translate("Second"),
        description=translate("Time unit until the fade-away imprint starts to disappear"),
        default=2.0,
        soft_max=10,
        min=0.001,
        update=scattering.update_factory.factory("s_proximity_repel1_simulation_fadeaway_sec", delay_support=True,)
        )
    #Feature Influence
    s_proximity_repel1_dist_infl_allow : bpy.props.BoolProperty(name=translate("Enable Influence"), default=True, update=scattering.update_factory.factory("s_proximity_repel1_dist_infl_allow",),)
    s_proximity_repel1_dist_influence : bpy.props.FloatProperty(name=translate("Density"), description=translate("Influence your distribution density, you'll be able to adjust the intensity of the influence by changing this slider"), default=100, subtype="PERCENTAGE", min=0, max=100, precision=1, update=scattering.update_factory.factory("s_proximity_repel1_dist_influence", delay_support=True,),)
    s_proximity_repel1_dist_revert : bpy.props.BoolProperty(name=translate("Reverse Influence"), update=scattering.update_factory.factory("s_proximity_repel1_dist_revert",),)
    s_proximity_repel1_scale_infl_allow : bpy.props.BoolProperty(name=translate("Enable Influence"), default=False, update=scattering.update_factory.factory("s_proximity_repel1_scale_infl_allow",),)
    s_proximity_repel1_scale_influence: bpy.props.FloatProperty(name=translate("Scale"), description=translate("Influence your distributed instances scale, you'll be able to adjust the intensity of the influence by changing this slider"), default=0, subtype="PERCENTAGE", min=0, max=100, precision=1, update=scattering.update_factory.factory("s_proximity_repel1_scale_influence", delay_support=True,),)
    s_proximity_repel1_scale_revert : bpy.props.BoolProperty(name=translate("Reverse Influence"), update=scattering.update_factory.factory("s_proximity_repel1_scale_revert",),)
    s_proximity_repel1_nor_infl_allow : bpy.props.BoolProperty(name=translate("Enable Influence"), default=False, update=scattering.update_factory.factory("s_proximity_repel1_nor_infl_allow",),)
    s_proximity_repel1_nor_influence: bpy.props.FloatProperty(name=translate("Normal"), description=translate("Influence your distributed instances rotation, an influence on the 'normal' of the rotation will create a tilting effect"), default=0, subtype="PERCENTAGE", min=-100, max=100, precision=1, update=scattering.update_factory.factory("s_proximity_repel1_nor_influence", delay_support=True,),)
    s_proximity_repel1_nor_revert : bpy.props.BoolProperty(name=translate("Reverse Influence"), update=scattering.update_factory.factory("s_proximity_repel1_nor_revert",),)
    s_proximity_repel1_tan_infl_allow : bpy.props.BoolProperty(name=translate("Enable Influence"), default=False, update=scattering.update_factory.factory("s_proximity_repel1_tan_infl_allow",),)
    s_proximity_repel1_tan_influence : bpy.props.FloatProperty(name=translate("Tangent"), description=translate("Influence your distributed instances rotation, an influence on the 'tangent' of the rotation will rotate the instances on themselves in order to align them on a given direction"), default=0, subtype="PERCENTAGE", min=-100, max=100, precision=1, update=scattering.update_factory.factory("s_proximity_repel1_tan_influence", delay_support=True,),)
    s_proximity_repel1_tan_revert : bpy.props.BoolProperty(name=translate("Reverse Influence"), update=scattering.update_factory.factory("s_proximity_repel1_tan_revert",),)

    #Feature Mask
    codegen_featuremask_properties(scope_ref=__annotations__, name="s_proximity_repel1",)

    ########## ########## Object-Repel 2

    s_proximity_repel2_allow : bpy.props.BoolProperty( 
        name=translate("Object Repel"),
        description=translate("Influence your distribution density or instances scale and orientations depending on their location in proximity to the objects contained in a chosen collection"),
        default=False, 
        update=scattering.update_factory.factory("s_proximity_repel2_allow",),
        )
    #treshold
    s_proximity_repel2_coll_ptr : bpy.props.StringProperty(
        name=translate("Collection Pointer"),
        search=lambda s,c,e: set(col.name for col in bpy.data.collections if (e in col.name)),
        search_options={'SUGGESTION','SORT'},
        update=scattering.update_factory.factory("s_proximity_repel2_coll_ptr"),
        )
    s_proximity_repel2_type : bpy.props.EnumProperty(   
        name=translate("Proximity Contact"),
        description=translate("Define which part of the reference objects is used to evaluate a proximity distance field. Impacting both the precision of the proximity field and the computational speed required"),
        default="mesh", 
        items= ( ("origin", translate("Origin Point"),translate("Evaluate the proximity only with the location of given objects origin points, this is by far the fastest contact method to compute"),  "ORIENTATION_VIEW",0 ),
                 ("mesh", translate("Meshes Faces"), translate("Evaluate the proximity with the faces of the chosen objects. Note that this process can be extremely diffult to compute"), "MESH_DATA",1 ),
                 ("bb", translate("Bounding-Box"), translate("Evaluate the proximity with the applied bounding box of the given objects"), "CUBE",2 ),
                 ("convexhull", translate("Convex-Hull"), translate("Evaluate the proximity with a generated convex-hull mesh from the given objects"), "MESH_ICOSPHERE",3 ),
                 ("pointcloud", translate("Point-Cloud"), translate("Evaluate the proximity with a generated point cloud of the given objects "), "OUTLINER_OB_POINTCLOUD",4 )
               ),
        update=scattering.update_factory.factory("s_proximity_repel2_type",),
        )
    s_proximity_repel2_volume_allow : bpy.props.BoolProperty(
        name=translate("Consider Volume"),
        description=translate("Only keep areas located inside or outside the volumes of the chosen objects"),
        default=False, 
        update=scattering.update_factory.factory("s_proximity_repel2_volume_allow",),
        )
    s_proximity_repel2_volume_method : bpy.props.EnumProperty(   
        default="out",
        items= ( ("in",  translate("Inside"), translate("Only keep areas located inside or outside the volumes of the chosen objects"),"",0), 
                 ("out", translate("Outside"),translate("Only keep areas located inside or outside the volumes of the chosen objects"),"",1)
               ),
        update=scattering.update_factory.factory("s_proximity_repel2_volume_method",),
        )
    s_proximity_repel2_max : bpy.props.FloatProperty(
        name=translate("Minimal"), #too late to change property name
        description=translate("Minimal distance around the object's collided in the proximity field"),
        default=0.5, min=0, subtype="DISTANCE",
        update=scattering.update_factory.factory("s_proximity_repel2_max", delay_support=True,),
        )
    s_proximity_repel2_treshold : bpy.props.FloatProperty(
        name=translate("Transition"),
        description=translate("Add a transition distance after the distance above to create a transition effect"),
        default=0.5, min=0, subtype="DISTANCE",
        update=scattering.update_factory.factory("s_proximity_repel2_treshold", delay_support=True,),
        )
    #distremap
    s_proximity_repel2_fallremap_allow : bpy.props.BoolProperty(
        name=translate("Transition Control"),
        description=translate("Control the transition falloff by remapping the values with a curve-map graph or by adding a procedural noise transition to this falloff.\n\n• Please note that this feature assumes there is a transition distance to work with"),
        default=False, 
        update=scattering.update_factory.factory("s_proximity_repel2_fallremap_allow",),
        )
    s_proximity_repel2_fallremap_revert : bpy.props.BoolProperty(
        name=translate("Reverse Transition"),
        description=translate("Reverse the transition. This option will in fact remap the values from '0-1' to '1-0'"),
        default=False,
        update=scattering.update_factory.factory("s_proximity_repel2_fallremap_revert",),
        )
    s_proximity_repel2_fallnoisy_strength : bpy.props.FloatProperty(
        name=translate("Strength"), 
        description=translate("Combine the distance transition with a noise pattern. Great to make the transition look less uniform and more natural. Set this value to 0 to disable the noise overlay entirely"),
        default=0, min=0, max=5, precision=3,
        update=scattering.update_factory.factory("s_proximity_repel2_fallnoisy_strength", delay_support=True,),
        )
    s_proximity_repel2_fallnoisy_space : bpy.props.EnumProperty(
        name="NOT IN GUI",
        default="local",
        items= ( ("local", translate("Local"), "", "ORIENTATION_LOCAL",0 ),
                 ("global", translate("Global"), "", "WORLD",1 ),
               ),
        update=scattering.update_factory.factory("s_proximity_repel2_fallnoisy_space"),
        )
    s_proximity_repel2_fallnoisy_scale : bpy.props.FloatProperty(
        name=translate("Scale"),
        description=translate("The scale of a procedural texture.\n• A value of '0.01' will creates a large noise pattern.\n• A value of '10.0' will create a small pattern"),
        default=0.5, min=0, soft_max=2, precision=3, 
        update=scattering.update_factory.factory("s_proximity_repel2_fallnoisy_scale", delay_support=True,),
        )
    s_proximity_repel2_fallnoisy_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        description=translate("Change this value to randomize the result.\n\nIn 3D graphics, a seed is a starting value used by a random number generator to produce a sequence of random-looking numbers. These numbers can control things like the position, rotation, or scale of objects in a scene. Using the same seed will always generate the same 'random' result, which helps keep things consistent when needed."),
        update=scattering.update_factory.factory("s_proximity_repel2_fallnoisy_seed", delay_support=True,),
        )
    s_proximity_repel2_fallnoisy_is_random_seed : bpy.props.BoolProperty(
        name=translate("Randomize Seed"),
        description=translate("Randomize the value of the hereby seed property.\n\n• Note that pressing 'ALT' while clicking on this button will garantee the attribution of an unique seed value of this property for all selected-system(s)"),
        default=False,
        update=scattering.update_factory.factory("s_proximity_repel2_fallnoisy_is_random_seed",),
        )
    s_proximity_repel2_fallremap_data : bpy.props.StringProperty(
        set=scattering.update_factory.fallremap_setter("s_proximity_repel2.fallremap"),
        get=scattering.update_factory.fallremap_getter("s_proximity_repel2.fallremap"),
        )
    #simulation
    s_proximity_repel2_simulation_allow : bpy.props.BoolProperty(
        name=translate("Simulate Collision Imprint Field"),
        description=translate("Instead of calculating a proximity field in real time, simulate a proximity field imprint left behind by any object's/objects passing by.\n\n• Beware: this feature is a simulation set-up and will require an animation playing in the timeline"),
        default=False,
        update=scattering.update_factory.factory("s_proximity_repel2_simulation_allow"),
        )
    s_proximity_repel2_simulation_fadeaway_allow : bpy.props.BoolProperty(
        name=translate("Fade Away Effect"),
        description=translate("The imprints will fade away with time, restoring the effect to its original state"),
        default=False,
        update=scattering.update_factory.factory("s_proximity_repel2_simulation_fadeaway_allow")
        )
    s_proximity_repel2_simulation_fadeaway_method : bpy.props.EnumProperty(
        default="sec",
        items= ( ("sec", translate("Seconds"), translate("Calculate the fade away in seconds units"), "",0 ),
                 ("frame", translate("Frames"), translate("Calculate the fade away in frames units"), "",1 ),
               ),
        update=scattering.update_factory.factory("s_proximity_repel2_simulation_fadeaway_method"),
        )
    s_proximity_repel2_simulation_fadeaway_frame : bpy.props.IntProperty(
        name=translate("Frame"),
        description=translate("Time unit until the fade-away imprint starts to disappear"),
        default=75,
        soft_max=999,
        min=1,
        update=scattering.update_factory.factory("s_proximity_repel2_simulation_fadeaway_frame", delay_support=True,),
        )
    s_proximity_repel2_simulation_fadeaway_sec : bpy.props.FloatProperty(
        name=translate("Second"),
        description=translate("Time unit until the fade-away imprint starts to disappear"),
        default=2.0,
        soft_max=10,
        min=0.001,
        update=scattering.update_factory.factory("s_proximity_repel2_simulation_fadeaway_sec", delay_support=True,)
        )
    #Feature Influence
    s_proximity_repel2_dist_infl_allow : bpy.props.BoolProperty(name=translate("Enable Influence"), default=True, update=scattering.update_factory.factory("s_proximity_repel2_dist_infl_allow",),)
    s_proximity_repel2_dist_influence : bpy.props.FloatProperty(name=translate("Density"), description=translate("Influence your distribution density, you'll be able to adjust the intensity of the influence by changing this slider"), default=100, subtype="PERCENTAGE", min=0, max=100, precision=1, update=scattering.update_factory.factory("s_proximity_repel2_dist_influence", delay_support=True,),)
    s_proximity_repel2_dist_revert : bpy.props.BoolProperty(name=translate("Reverse Influence"), update=scattering.update_factory.factory("s_proximity_repel2_dist_revert",),)
    s_proximity_repel2_scale_infl_allow : bpy.props.BoolProperty(name=translate("Enable Influence"), default=False, update=scattering.update_factory.factory("s_proximity_repel2_scale_infl_allow",),)
    s_proximity_repel2_scale_influence: bpy.props.FloatProperty(name=translate("Scale"), description=translate("Influence your distributed instances scale, you'll be able to adjust the intensity of the influence by changing this slider"), default=0, subtype="PERCENTAGE", min=0, max=100, precision=1, update=scattering.update_factory.factory("s_proximity_repel2_scale_influence", delay_support=True,),)
    s_proximity_repel2_scale_revert : bpy.props.BoolProperty(name=translate("Reverse Influence"), update=scattering.update_factory.factory("s_proximity_repel2_scale_revert",),)
    s_proximity_repel2_nor_infl_allow : bpy.props.BoolProperty(name=translate("Enable Influence"), default=False, update=scattering.update_factory.factory("s_proximity_repel2_nor_infl_allow",),)
    s_proximity_repel2_nor_influence: bpy.props.FloatProperty(name=translate("Normal"), description=translate("Influence your distributed instances rotation, an influence on the 'normal' of the rotation will create a tilting effect"), default=0, subtype="PERCENTAGE", min=-100, max=100, precision=1, update=scattering.update_factory.factory("s_proximity_repel2_nor_influence", delay_support=True,),)
    s_proximity_repel2_nor_revert : bpy.props.BoolProperty(name=translate("Reverse Influence"), update=scattering.update_factory.factory("s_proximity_repel2_nor_revert",),)
    s_proximity_repel2_tan_infl_allow : bpy.props.BoolProperty(name=translate("Enable Influence"), default=False, update=scattering.update_factory.factory("s_proximity_repel2_tan_infl_allow",),)
    s_proximity_repel2_tan_influence : bpy.props.FloatProperty(name=translate("Tangent"), description=translate("Influence your distributed instances rotation, an influence on the 'tangent' of the rotation will rotate the instances on themselves in order to align them on a given direction"), default=0, subtype="PERCENTAGE", min=-100, max=100, precision=1, update=scattering.update_factory.factory("s_proximity_repel2_tan_influence", delay_support=True,),)
    s_proximity_repel2_tan_revert : bpy.props.BoolProperty(name=translate("Reverse Influence"), update=scattering.update_factory.factory("s_proximity_repel2_tan_revert",),)

    #Feature Mask
    codegen_featuremask_properties(scope_ref=__annotations__, name="s_proximity_repel2",)

    ########## ########## ProjBezArea Special
    
    s_proximity_projbezarea_border_allow : bpy.props.BoolProperty(
        name=translate("Bezier-Area Border"), 
        description=translate("Influences your distribution density and instances scale depending on how close/far away they are located from their bezier-area(s) curves"),
        default=False, 
        update=scattering.update_factory.factory("s_proximity_projbezarea_border_allow",),
        )
    s_proximity_projbezarea_border_max : bpy.props.FloatProperty(
        name=translate("Offset"),
        description=translate("Minimal distance defining the border offset range"),
        default=0,
        min=0,
        subtype="DISTANCE",
        update=scattering.update_factory.factory("s_proximity_projbezarea_border_max", delay_support=True,),
        )
    s_proximity_projbezarea_border_treshold : bpy.props.FloatProperty(
        name=translate("Transition"),
        description=translate("Add a transition distance after the offset distance defined above"),
        default=2,
        min=0,
        subtype="DISTANCE",
        update=scattering.update_factory.factory("s_proximity_projbezarea_border_treshold", delay_support=True,),
        )
    #remap
    s_proximity_projbezarea_border_fallremap_allow : bpy.props.BoolProperty(
        name=translate("Transition Control"),
        description=translate("Control the transition falloff by remapping the values with a curve-map graph or by adding a procedural noise transition to this falloff.\n\n• Please note that this feature assumes there is a transition distance to work with"),
        default=False, 
        update=scattering.update_factory.factory("s_proximity_projbezarea_border_fallremap_allow",),
        )
    s_proximity_projbezarea_border_fallremap_revert : bpy.props.BoolProperty(
        name=translate("Reverse Transition"),
        description=translate("Reverse the transition. This option will in fact remap the values from '0-1' to '1-0'"),
        default=False,
        update=scattering.update_factory.factory("s_proximity_projbezarea_border_fallremap_revert",),
        )
    s_proximity_projbezarea_border_fallnoisy_strength : bpy.props.FloatProperty(
        name=translate("Strength"), 
        description=translate("Combine the distance transition with a noise pattern. Great to make the transition look less uniform and more natural. Set this value to 0 to disable the noise overlay entirely"),
        default=0, min=0, max=5, precision=3,
        update=scattering.update_factory.factory("s_proximity_projbezarea_border_fallnoisy_strength", delay_support=True,),
        )
    s_proximity_projbezarea_border_fallnoisy_space : bpy.props.EnumProperty(
        name="NOT IN GUI",
        default="local",
        items= ( ("local", translate("Local"), "", "ORIENTATION_LOCAL",0 ),
                 ("global", translate("Global"), "", "WORLD",1 ),
               ),
        update=scattering.update_factory.factory("s_proximity_projbezarea_border_fallnoisy_space"),
        )
    s_proximity_projbezarea_border_fallnoisy_scale : bpy.props.FloatProperty(
        name=translate("Scale"),
        description=translate("The scale of a procedural texture.\n• A value of '0.01' will creates a large noise pattern.\n• A value of '10.0' will create a small pattern"),
        default=0.5, min=0, soft_max=2, precision=3, 
        update=scattering.update_factory.factory("s_proximity_projbezarea_border_fallnoisy_scale", delay_support=True,),
        )
    s_proximity_projbezarea_border_fallnoisy_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        description=translate("Change this value to randomize the result.\n\nIn 3D graphics, a seed is a starting value used by a random number generator to produce a sequence of random-looking numbers. These numbers can control things like the position, rotation, or scale of objects in a scene. Using the same seed will always generate the same 'random' result, which helps keep things consistent when needed."),
        update=scattering.update_factory.factory("s_proximity_projbezarea_border_fallnoisy_seed", delay_support=True,),
        )
    s_proximity_projbezarea_border_fallnoisy_is_random_seed : bpy.props.BoolProperty(
        name=translate("Randomize Seed"),
        description=translate("Randomize the value of the hereby seed property.\n\n• Note that pressing 'ALT' while clicking on this button will garantee the attribution of an unique seed value of this property for all selected-system(s)"),
        default=False,
        update=scattering.update_factory.factory("s_proximity_projbezarea_border_fallnoisy_is_random_seed",),
        )
    s_proximity_projbezarea_border_fallremap_data : bpy.props.StringProperty(
        set=scattering.update_factory.fallremap_setter("s_proximity_projbezarea_border.fallremap"),
        get=scattering.update_factory.fallremap_getter("s_proximity_projbezarea_border.fallremap"),
        )
    #Feature Influence
    s_proximity_projbezarea_border_dist_infl_allow : bpy.props.BoolProperty(name=translate("Enable Influence"), default=True, update=scattering.update_factory.factory("s_proximity_projbezarea_border_dist_infl_allow",),)
    s_proximity_projbezarea_border_dist_influence : bpy.props.FloatProperty(name=translate("Density"), description=translate("Influence your distribution density, you'll be able to adjust the intensity of the influence by changing this slider"), default=100, subtype="PERCENTAGE", min=0, max=100, precision=1, update=scattering.update_factory.factory("s_proximity_projbezarea_border_dist_influence", delay_support=True,),)
    s_proximity_projbezarea_border_dist_revert : bpy.props.BoolProperty(name=translate("Reverse Influence"), update=scattering.update_factory.factory("s_proximity_projbezarea_border_dist_revert",),)
    s_proximity_projbezarea_border_scale_infl_allow : bpy.props.BoolProperty(name=translate("Enable Influence"), default=True, update=scattering.update_factory.factory("s_proximity_projbezarea_border_scale_infl_allow",),)
    s_proximity_projbezarea_border_scale_influence: bpy.props.FloatProperty(name=translate("Scale"), description=translate("Influence your distributed instances scale, you'll be able to adjust the intensity of the influence by changing this slider"), default=60, subtype="PERCENTAGE", soft_min=0, max=100, precision=1, update=scattering.update_factory.factory("s_proximity_projbezarea_border_scale_influence", delay_support=True,),)
    s_proximity_projbezarea_border_scale_revert : bpy.props.BoolProperty(name=translate("Reverse Influence"), update=scattering.update_factory.factory("s_proximity_projbezarea_border_scale_revert",),)
    
    
    ########## ########## Outskirt 

    s_proximity_outskirt_allow : bpy.props.BoolProperty(
        name=translate("Outskirt Transition"), 
        description=translate("Create a transition effect at the outskirt areas at the outer part of your distribution.\n\n• Note that it is easier to identify outskirts if the distribution abruptly ends. If the distribution has a smooth transition toward points-free areas the algorithm will have more difficulty finding these areas.\n• Note that this feature is computer intensive"),
        default=False, 
        update=scattering.update_factory.factory("s_proximity_outskirt_allow",),
        )
    #TODO s_proximity_outskirt_space (local/global)
    s_proximity_outskirt_detection : bpy.props.FloatProperty(
        name=translate("Distance"),
        description=translate("Minimal distance between points in order to recognize grouped points areas"),
        default=0.7,
        min=0,
        subtype="DISTANCE",
        update=scattering.update_factory.factory("s_proximity_outskirt_detection", delay_support=True,),
        )
    s_proximity_outskirt_precision : bpy.props.FloatProperty(
        name=translate("Precision"),
        description=translate("Precision of the algorithm. More precision equals slower performances"),
        default=0.7,
        min=0.1,
        max=1,
        update=scattering.update_factory.factory("s_proximity_outskirt_precision", delay_support=True,),
        )
    s_proximity_outskirt_max : bpy.props.FloatProperty(
        name=translate("Minimal"), #too late to change property name
        description=translate("Minimal distance reached until the transition starts"),
        default=0,
        min=0,
        subtype="DISTANCE",
        update=scattering.update_factory.factory("s_proximity_outskirt_max", delay_support=True,),
        )
    s_proximity_outskirt_treshold : bpy.props.FloatProperty(
        name=translate("Transition"),
        default=2,
        min=0,
        subtype="DISTANCE",
        update=scattering.update_factory.factory("s_proximity_outskirt_treshold", delay_support=True,),
        )
    #remap
    s_proximity_outskirt_fallremap_allow : bpy.props.BoolProperty(
        name=translate("Transition Control"),
        description=translate("Control the transition falloff by remapping the values with a curve-map graph or by adding a procedural noise transition to this falloff.\n\n• Please note that this feature assumes there is a transition distance to work with"),
        default=False, 
        update=scattering.update_factory.factory("s_proximity_outskirt_fallremap_allow",),
        )
    s_proximity_outskirt_fallremap_revert : bpy.props.BoolProperty(
        name=translate("Reverse Transition"),
        description=translate("Reverse the transition. This option will in fact remap the values from '0-1' to '1-0'"),
        default=False,
        update=scattering.update_factory.factory("s_proximity_outskirt_fallremap_revert",),
        )
    s_proximity_outskirt_fallnoisy_strength : bpy.props.FloatProperty(
        name=translate("Strength"), 
        description=translate("Combine the distance transition with a noise pattern. Great to make the transition look less uniform and more natural. Set this value to 0 to disable the noise overlay entirely"),
        default=0, min=0, max=5, precision=3,
        update=scattering.update_factory.factory("s_proximity_outskirt_fallnoisy_strength", delay_support=True,),
        )
    s_proximity_outskirt_fallnoisy_space : bpy.props.EnumProperty(
        name="NOT IN GUI",
        default="local",
        items= ( ("local", translate("Local"), "", "ORIENTATION_LOCAL",0 ),
                 ("global", translate("Global"), "", "WORLD",1 ),
               ),
        update=scattering.update_factory.factory("s_proximity_outskirt_fallnoisy_space"),
        )
    s_proximity_outskirt_fallnoisy_scale : bpy.props.FloatProperty(
        name=translate("Scale"),
        description=translate("The scale of a procedural texture.\n• A value of '0.01' will creates a large noise pattern.\n• A value of '10.0' will create a small pattern"),
        default=0.5, min=0, soft_max=2, precision=3, 
        update=scattering.update_factory.factory("s_proximity_outskirt_fallnoisy_scale", delay_support=True,),
        )
    s_proximity_outskirt_fallnoisy_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        description=translate("Change this value to randomize the result.\n\nIn 3D graphics, a seed is a starting value used by a random number generator to produce a sequence of random-looking numbers. These numbers can control things like the position, rotation, or scale of objects in a scene. Using the same seed will always generate the same 'random' result, which helps keep things consistent when needed."),
        update=scattering.update_factory.factory("s_proximity_outskirt_fallnoisy_seed", delay_support=True,),
        )
    s_proximity_outskirt_fallnoisy_is_random_seed : bpy.props.BoolProperty(
        name=translate("Randomize Seed"),
        description=translate("Randomize the value of the hereby seed property.\n\n• Note that pressing 'ALT' while clicking on this button will garantee the attribution of an unique seed value of this property for all selected-system(s)"),
        default=False,
        update=scattering.update_factory.factory("s_proximity_outskirt_fallnoisy_is_random_seed",),
        )
    s_proximity_outskirt_fallremap_data : bpy.props.StringProperty(
        set=scattering.update_factory.fallremap_setter("s_proximity_outskirt.fallremap"),
        get=scattering.update_factory.fallremap_getter("s_proximity_outskirt.fallremap"),
        )
    #Feature Influence
    s_proximity_outskirt_dist_infl_allow : bpy.props.BoolProperty(name=translate("Enable Influence"), default=False, update=scattering.update_factory.factory("s_proximity_outskirt_dist_infl_allow",),)
    s_proximity_outskirt_dist_influence : bpy.props.FloatProperty(name=translate("Density"), description=translate("Influence your distribution density, you'll be able to adjust the intensity of the influence by changing this slider"), default=100, subtype="PERCENTAGE", min=0, max=100, precision=1, update=scattering.update_factory.factory("s_proximity_outskirt_dist_influence", delay_support=True,),)
    s_proximity_outskirt_dist_revert : bpy.props.BoolProperty(name=translate("Reverse Influence"), update=scattering.update_factory.factory("s_proximity_outskirt_dist_revert",),)
    s_proximity_outskirt_scale_infl_allow : bpy.props.BoolProperty(name=translate("Enable Influence"), default=True, update=scattering.update_factory.factory("s_proximity_outskirt_scale_infl_allow",),)
    s_proximity_outskirt_scale_influence: bpy.props.FloatProperty(name=translate("Scale"), description=translate("Influence your distributed instances scale, you'll be able to adjust the intensity of the influence by changing this slider"), default=70, subtype="PERCENTAGE", min=0, max=100, precision=1, update=scattering.update_factory.factory("s_proximity_outskirt_scale_influence", delay_support=True,),)
    s_proximity_outskirt_scale_revert : bpy.props.BoolProperty(name=translate("Reverse Influence"), update=scattering.update_factory.factory("s_proximity_outskirt_scale_revert",),)
    # s_proximity_outskirt_nor_infl_allow : bpy.props.BoolProperty(name=translate("Enable Influence"), default=False, update=scattering.update_factory.factory("s_proximity_outskirt_nor_infl_allow",),)
    # s_proximity_outskirt_nor_influence: bpy.props.FloatProperty(name=translate("Normal"), default=0, subtype="PERCENTAGE", min=-100, max=100, precision=1, update=scattering.update_factory.factory("s_proximity_outskirt_nor_influence", delay_support=True,),)
    # s_proximity_outskirt_nor_revert : bpy.props.BoolProperty(name=translate("Reverse Influence"), update=scattering.update_factory.factory("s_proximity_outskirt_nor_revert",),)
    # s_proximity_outskirt_tan_infl_allow : bpy.props.BoolProperty(name=translate("Enable Influence"), default=False, update=scattering.update_factory.factory("s_proximity_outskirt_tan_infl_allow",),)
    # s_proximity_outskirt_tan_influence : bpy.props.FloatProperty(name=translate("Tangent"), default=0, subtype="PERCENTAGE", min=-100, max=100, precision=1, update=scattering.update_factory.factory("s_proximity_outskirt_tan_influence", delay_support=True,),)
    # s_proximity_outskirt_tan_revert : bpy.props.BoolProperty(name=translate("Reverse Influence"), update=scattering.update_factory.factory("s_proximity_outskirt_tan_revert",),)

    #Feature Mask
    codegen_featuremask_properties(scope_ref=__annotations__, name="s_proximity_outskirt",)

    # 888888  dP""b8  dP"Yb  .dP"Y8 Yb  dP .dP"Y8 888888 888888 8b    d8
    # 88__   dP   `" dP   Yb `Ybo."  YbdP  `Ybo."   88   88__   88b  d88
    # 88""   Yb      Yb   dP o.`Y8b   8P   o.`Y8b   88   88""   88YbdP88
    # 888888  YboodP  YbodP  8bodP'  dP    8bodP'   88   888888 88 YY 88

    ###################### This category of settings keyword is : "s_ecosystem"

    s_ecosystem_locked : bpy.props.BoolProperty(description=translate("Lock/Unlock Settings"),)

    def get_s_ecosystem_main_features(self, availability_conditions=True,):
        return ["s_ecosystem_affinity_allow", "s_ecosystem_repulsion_allow", "s_ecosystem_density_allow",]

    s_ecosystem_master_allow : bpy.props.BoolProperty( 
        name=translate("Master Toggle"),
        description=translate("Mute/Unmute all features of this category in one click"),
        default=True, 
        update=scattering.update_factory.factory("s_ecosystem_master_allow", sync_support=False,),
        )

    def get_s_ecosystem_psy_match(self, context, edit_text):
        """return list of local scatter-systems, used for prop_search"""
        
        return [ p.name for p in bpy.context.scene.scatter5.get_all_psys(search_mode="active_view_layer", also_linked=True,) if ((edit_text in p.name) and (p.uuid!=self.uuid)) ]

    ########## ##########  Affinity

    s_ecosystem_affinity_allow : bpy.props.BoolProperty(
        name=translate("Ecosystem Affinity"), 
        description=translate("Tie this scatter to others using 'Affinity' rules, so instances appear only near the selected scatter-systems(s). Both your distribution density and instances scale can be affected by this feature"),
        default=False, 
        update=scattering.update_factory.factory("s_ecosystem_affinity_allow",),
        )
    s_ecosystem_affinity_space : bpy.props.EnumProperty(
        name=translate("Space"),
        description=translate("Evaluation Space.\nDetermines how distances between scattered elements are evaluated"),
        default="local", 
        items= ( ("local", translate("Local"), translate("Evaluate distances in local space, keeping distance fields consistent when objects are transformed"), "ORIENTATION_LOCAL",0 ),
                 ("global", translate("Global"), translate("Evaluate distances in world space, updating the distance field as objects are transformed"), "WORLD",1 ),
               ),
        update=scattering.update_factory.factory("s_ecosystem_affinity_space"),
        )
    #slots properties
    s_ecosystem_affinity_ui_max_slot : bpy.props.IntProperty(default=1,max=3,min=1)
    codegen_properties_by_idx(scope_ref=__annotations__, name="s_ecosystem_affinity_XX_ptr", nbr=3, items={"name":translate("Scatter System"),"search":get_s_ecosystem_psy_match,"search_options":{'SUGGESTION','SORT'}}, property_type=bpy.props.StringProperty,)
    codegen_properties_by_idx(scope_ref=__annotations__, name="s_ecosystem_affinity_XX_type", nbr=3, items={"name":translate("Proximity Contact"),"description":translate("Define which part of the reference objects is used to evaluate a proximity distance field. Impacting both the precision of the proximity field and the computational speed required"),"default":"origin","items":( ("origin", translate("Origin Point"),translate("Evaluate the proximity only with the location of given objects origin points, this is by far the fastest contact method to compute"),  "ORIENTATION_VIEW",0 ),("mesh", translate("Meshes Faces"), translate("Evaluate the proximity with the faces of the chosen objects. Note that this process can be extremely diffult to compute"), "MESH_DATA",1 ),("bb", translate("Bounding-Box"), translate("Evaluate the proximity with the applied bounding box of the given objects"), "CUBE",2 ),("convexhull", translate("Convex-Hull"), translate("Evaluate the proximity with a generated convex-hull mesh from the given objects"), "MESH_ICOSPHERE",3 ),("pointcloud", translate("Point-Cloud"), translate("Evaluate the proximity with a generated point cloud of the given objects "), "OUTLINER_OB_POINTCLOUD",4 )),}, property_type=bpy.props.EnumProperty,)
    codegen_properties_by_idx(scope_ref=__annotations__, name="s_ecosystem_affinity_XX_max_value", nbr=3, items={"name":translate("Minimal"),"description":translate("Minimal distance field where the affinity effect will occur around the specified system"),"default":0.5,"min":0,"precision":3,"subtype":"DISTANCE",}, property_type=bpy.props.FloatProperty, delay_support=True,)
    codegen_properties_by_idx(scope_ref=__annotations__, name="s_ecosystem_affinity_XX_max_falloff", nbr=3, items={"name":translate("Transition"),"description":translate("Add a transition distance after the distance above to create a transition effect"),"default":0.5,"min":0,"precision":3,"subtype":"DISTANCE",}, property_type=bpy.props.FloatProperty, delay_support=True,)
    codegen_properties_by_idx(scope_ref=__annotations__, name="s_ecosystem_affinity_XX_limit_distance", nbr=3, items={"name":translate("Limit Collision"),"description":translate("Avoid having instances too close to the chosen scatter-system"),"default":0,"min":0,"precision":3,"subtype":"DISTANCE",}, property_type=bpy.props.FloatProperty, delay_support=True,)
    #remap
    s_ecosystem_affinity_fallremap_allow : bpy.props.BoolProperty(
        name=translate("Transition Control"),
        description=translate("Control the transition falloff by remapping the values with a curve-map graph or by adding a procedural noise transition to this falloff.\n\n• Please note that this feature assumes there is a transition distance to work with"),
        default=False, 
        update=scattering.update_factory.factory("s_ecosystem_affinity_fallremap_allow",),
        )
    s_ecosystem_affinity_fallremap_revert : bpy.props.BoolProperty(
        name=translate("Reverse Transition"),
        description=translate("Reverse the transition. This option will in fact remap the values from '0-1' to '1-0'"),
        default=False,
        update=scattering.update_factory.factory("s_ecosystem_affinity_fallremap_revert",),
        )
    s_ecosystem_affinity_fallnoisy_strength : bpy.props.FloatProperty(
        name=translate("Strength"), 
        description=translate("Combine the distance transition with a noise pattern. Great to make the transition look less uniform and more natural. Set this value to 0 to disable the noise overlay entirely"),
        default=0, min=0, max=5, precision=3,
        update=scattering.update_factory.factory("s_ecosystem_affinity_fallnoisy_strength", delay_support=True,),
        )
    s_ecosystem_affinity_fallnoisy_space : bpy.props.EnumProperty(
        name="NOT IN GUI",
        default="local",
        items= ( ("local", translate("Local"), "", "ORIENTATION_LOCAL",0 ),
                 ("global", translate("Global"), "", "WORLD",1 ),
               ),
        update=scattering.update_factory.factory("s_ecosystem_affinity_fallnoisy_space"),
        )
    s_ecosystem_affinity_fallnoisy_scale : bpy.props.FloatProperty(
        name=translate("Scale"),
        description=translate("The scale of a procedural texture.\n• A value of '0.01' will creates a large noise pattern.\n• A value of '10.0' will create a small pattern"),
        default=0.5, min=0, soft_max=2, precision=3, 
        update=scattering.update_factory.factory("s_ecosystem_affinity_fallnoisy_scale", delay_support=True,),
        )
    s_ecosystem_affinity_fallnoisy_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        description=translate("Change this value to randomize the result.\n\nIn 3D graphics, a seed is a starting value used by a random number generator to produce a sequence of random-looking numbers. These numbers can control things like the position, rotation, or scale of objects in a scene. Using the same seed will always generate the same 'random' result, which helps keep things consistent when needed."),
        update=scattering.update_factory.factory("s_ecosystem_affinity_fallnoisy_seed", delay_support=True,),
        )
    s_ecosystem_affinity_fallnoisy_is_random_seed : bpy.props.BoolProperty(
        name=translate("Randomize Seed"),
        description=translate("Randomize the value of the hereby seed property.\n\n• Note that pressing 'ALT' while clicking on this button will garantee the attribution of an unique seed value of this property for all selected-system(s)"),
        default=False,
        update=scattering.update_factory.factory("s_ecosystem_affinity_fallnoisy_is_random_seed",),
        )
    s_ecosystem_affinity_fallremap_data : bpy.props.StringProperty(
        set=scattering.update_factory.fallremap_setter("s_ecosystem_affinity.fallremap"),
        get=scattering.update_factory.fallremap_getter("s_ecosystem_affinity.fallremap"),
        )
    #Feature Influence
    s_ecosystem_affinity_dist_infl_allow : bpy.props.BoolProperty(name=translate("Enable Influence"), default=True, update=scattering.update_factory.factory("s_ecosystem_affinity_dist_infl_allow",),)
    s_ecosystem_affinity_dist_influence : bpy.props.FloatProperty(name=translate("Density"), description=translate("Influence your distribution density, you'll be able to adjust the intensity of the influence by changing this slider"), default=100, subtype="PERCENTAGE", min=0, max=100, precision=1, update=scattering.update_factory.factory("s_ecosystem_affinity_dist_influence", delay_support=True,),)
    s_ecosystem_affinity_scale_infl_allow : bpy.props.BoolProperty(name=translate("Enable Influence"), default=True, update=scattering.update_factory.factory("s_ecosystem_affinity_scale_infl_allow",),)
    s_ecosystem_affinity_scale_influence: bpy.props.FloatProperty(name=translate("Scale"), description=translate("Influence your distributed instances scale, you'll be able to adjust the intensity of the influence by changing this slider"), default=50, subtype="PERCENTAGE", min=0, max=100, precision=1, update=scattering.update_factory.factory("s_ecosystem_affinity_scale_influence", delay_support=True,),)
    #Feature Mask
    codegen_featuremask_properties(scope_ref=__annotations__, name="s_ecosystem_affinity",)

    ########## ##########  Repulsion

    s_ecosystem_repulsion_allow : bpy.props.BoolProperty(
        name=translate("Ecosystem Repulsion"), 
        description=translate("Tie this scatter to others using 'Repulsion' rules, so instances avoid being located near selected scatter-system(s). Both your distribution density and instances scale can be affected by this feature"),
        default=False, 
        update=scattering.update_factory.factory("s_ecosystem_repulsion_allow",),
        )
    s_ecosystem_repulsion_space : bpy.props.EnumProperty(
        name=translate("Space"),
        description=translate("Evaluation Space.\nDetermines how distances between scattered elements are evaluated"),
        default="local", 
        items= ( ("local", translate("Local"), translate("Evaluate distances in local space, keeping distance fields consistent when objects are transformed"), "ORIENTATION_LOCAL",0 ),
                 ("global", translate("Global"), translate("Evaluate distances in world space, updating the distance field as objects are transformed"), "WORLD",1 ),
               ),
        update=scattering.update_factory.factory("s_ecosystem_repulsion_space"),
        )
    #slots properties
    s_ecosystem_repulsion_ui_max_slot : bpy.props.IntProperty(default=1,max=3,min=1)
    codegen_properties_by_idx(scope_ref=__annotations__, name="s_ecosystem_repulsion_XX_ptr", nbr=3, items={"name":translate("Scatter System"),"search":get_s_ecosystem_psy_match,"search_options":{'SUGGESTION','SORT'}}, property_type=bpy.props.StringProperty,)
    codegen_properties_by_idx(scope_ref=__annotations__, name="s_ecosystem_repulsion_XX_type", nbr=3, items={"name":translate("Proximity Contact"),"description":translate("Define which part of the reference objects is used to evaluate a proximity distance field. Impacting both the precision of the proximity field and the computational speed required"),"default":"origin","items":( ("origin", translate("Origin Point"),translate("Evaluate the proximity only with the location of given objects origin points, this is by far the fastest contact method to compute"),  "ORIENTATION_VIEW",0 ),("mesh", translate("Meshes Faces"), translate("Evaluate the proximity with the faces of the chosen objects. Note that this process can be extremely diffult to compute"), "MESH_DATA",1 ),("bb", translate("Bounding-Box"), translate("Evaluate the proximity with the applied bounding box of the given objects"), "CUBE",2 ),("convexhull", translate("Convex-Hull"), translate("Evaluate the proximity with a generated convex-hull mesh from the given objects"), "MESH_ICOSPHERE",3 ),("pointcloud", translate("Point-Cloud"), translate("Evaluate the proximity with a generated point cloud of the given objects "), "OUTLINER_OB_POINTCLOUD",4 ),),}, property_type=bpy.props.EnumProperty,)
    codegen_properties_by_idx(scope_ref=__annotations__, name="s_ecosystem_repulsion_XX_max_value", nbr=3, items={"name":translate("Minimal"),"description":translate("Minimal distance field where the repulsion effect will occur around the specified system"),"default":0.5,"min":0,"precision":3,"subtype":"DISTANCE",}, property_type=bpy.props.FloatProperty, delay_support=True,)
    codegen_properties_by_idx(scope_ref=__annotations__, name="s_ecosystem_repulsion_XX_max_falloff", nbr=3, items={"name":translate("Transition"),"description":translate("Add a transition distance after the distance above to create a transition effect"),"default":0.5,"min":0,"precision":3,"subtype":"DISTANCE",}, property_type=bpy.props.FloatProperty, delay_support=True,)
    #remap
    s_ecosystem_repulsion_fallremap_allow : bpy.props.BoolProperty(
        name=translate("Transition Control"),
        description=translate("Control the transition falloff by remapping the values with a curve-map graph or by adding a procedural noise transition to this falloff.\n\n• Please note that this feature assumes there is a transition distance to work with"),
        default=False, 
        update=scattering.update_factory.factory("s_ecosystem_repulsion_fallremap_allow",),
        )
    s_ecosystem_repulsion_fallremap_revert : bpy.props.BoolProperty(
        name=translate("Reverse Transition"),
        description=translate("Reverse the transition. This option will in fact remap the values from '0-1' to '1-0'"),
        default=False,
        update=scattering.update_factory.factory("s_ecosystem_repulsion_fallremap_revert",),
        )
    s_ecosystem_repulsion_fallnoisy_strength : bpy.props.FloatProperty(
        name=translate("Strength"), 
        description=translate("Combine the distance transition with a noise pattern. Great to make the transition look less uniform and more natural. Set this value to 0 to disable the noise overlay entirely"),
        default=0, min=0, max=5, precision=3,
        update=scattering.update_factory.factory("s_ecosystem_repulsion_fallnoisy_strength", delay_support=True,),
        )
    s_ecosystem_repulsion_fallnoisy_space : bpy.props.EnumProperty(
        name="NOT IN GUI",
        default="local",
        items= ( ("local", translate("Local"), "", "ORIENTATION_LOCAL",0 ),
                 ("global", translate("Global"), "", "WORLD",1 ),
               ),
        update=scattering.update_factory.factory("s_ecosystem_repulsion_fallnoisy_space"),
        )
    s_ecosystem_repulsion_fallnoisy_scale : bpy.props.FloatProperty(
        name=translate("Scale"),
        description=translate("The scale of a procedural texture.\n• A value of '0.01' will creates a large noise pattern.\n• A value of '10.0' will create a small pattern"),
        default=0.5, min=0, soft_max=2, precision=3, 
        update=scattering.update_factory.factory("s_ecosystem_repulsion_fallnoisy_scale", delay_support=True,),
        )
    s_ecosystem_repulsion_fallnoisy_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        description=translate("Change this value to randomize the result.\n\nIn 3D graphics, a seed is a starting value used by a random number generator to produce a sequence of random-looking numbers. These numbers can control things like the position, rotation, or scale of objects in a scene. Using the same seed will always generate the same 'random' result, which helps keep things consistent when needed."),
        update=scattering.update_factory.factory("s_ecosystem_repulsion_fallnoisy_seed", delay_support=True,),
        )
    s_ecosystem_repulsion_fallnoisy_is_random_seed : bpy.props.BoolProperty(
        name=translate("Randomize Seed"),
        description=translate("Randomize the value of the hereby seed property.\n\n• Note that pressing 'ALT' while clicking on this button will garantee the attribution of an unique seed value of this property for all selected-system(s)"),
        default=False,
        update=scattering.update_factory.factory("s_ecosystem_repulsion_fallnoisy_is_random_seed",),
        )
    s_ecosystem_repulsion_fallremap_data : bpy.props.StringProperty(
        set=scattering.update_factory.fallremap_setter("s_ecosystem_repulsion.fallremap"),
        get=scattering.update_factory.fallremap_getter("s_ecosystem_repulsion.fallremap"),
        )
    #Feature Influence
    s_ecosystem_repulsion_dist_infl_allow : bpy.props.BoolProperty(name=translate("Enable Influence"), default=True, update=scattering.update_factory.factory("s_ecosystem_repulsion_dist_infl_allow",),)
    s_ecosystem_repulsion_dist_influence : bpy.props.FloatProperty(name=translate("Density"), description=translate("Influence your distribution density, you'll be able to adjust the intensity of the influence by changing this slider"), default=100, subtype="PERCENTAGE", min=0, max=100, precision=1, update=scattering.update_factory.factory("s_ecosystem_repulsion_dist_influence", delay_support=True,),)
    s_ecosystem_repulsion_scale_infl_allow : bpy.props.BoolProperty(name=translate("Allow Influence"), default=True, update=scattering.update_factory.factory("s_ecosystem_repulsion_scale_infl_allow",),)
    s_ecosystem_repulsion_scale_influence: bpy.props.FloatProperty(name=translate("Scale"), description=translate("Influence your distributed instances scale, you'll be able to adjust the intensity of the influence by changing this slider"), default=50, subtype="PERCENTAGE", min=0, max=100, precision=1, update=scattering.update_factory.factory("s_ecosystem_repulsion_scale_influence", delay_support=True,),)
    #Feature Mask
    codegen_featuremask_properties(scope_ref=__annotations__, name="s_ecosystem_repulsion",)

    ########## ##########  Density
    
    s_ecosystem_density_allow : bpy.props.BoolProperty(
        name=translate("Ecosystem Density"), 
        description=translate("Tie this scatter to others using 'Density' rules, so instances are only located within dense/scarse areas of the selected scatter-systems(s). Both your distribution density and instances scale can be affected by this feature"),
        default=False, 
        update=scattering.update_factory.factory("s_ecosystem_density_allow",),
        )
    s_ecosystem_density_space : bpy.props.EnumProperty(
        name=translate("Space"),
        description=translate("Evaluation Space.\nDetermines how distances between scattered elements are evaluated"),
        default="local", 
        items= ( ("local", translate("Local"), translate("Evaluate distances in local space, keeping distance fields consistent when objects are transformed"), "ORIENTATION_LOCAL",0 ),
                 ("global", translate("Global"), translate("Evaluate distances in world space, updating the distance field as objects are transformed"), "WORLD",1 ),
               ),
        update=scattering.update_factory.factory("s_ecosystem_density_space"),
        )
    s_ecosystem_density_method : bpy.props.EnumProperty(
        name=translate("Method"),
        description=translate("Choose how you would like to evaluate your scatter's densities"),
        default="defined_above",
        items= ( ("defined_above", translate("Dense Areas"), translate("Select areas of the chosen scatter-system(s) only above the chosen density"), "OUTLINER_OB_POINTCLOUD",0 ),
                 ("defined_below", translate("Scarse Areas"), translate("Select areas of the chosen scatter-system(s) only below the chosen density"), "POINTCLOUD_POINT",1 ),
                 ("normalized", translate("Normalize Values"), translate("The calculated density field for the selected scatter system(s) will be normalized to a 0-1 range, making it easy to remap these values later if needed"), "TOPATCH:W_NORMALIZE",2 ),
               ),
        update=scattering.update_factory.factory("s_ecosystem_density_method"),
        )
    #slots properties
    s_ecosystem_density_ui_max_slot : bpy.props.IntProperty(default=1,max=3,min=1)
    codegen_properties_by_idx(scope_ref=__annotations__, name="s_ecosystem_density_XX_ptr", nbr=3, items={"name":translate("Scatter System"),"search":get_s_ecosystem_psy_match,"search_options":{'SUGGESTION','SORT'}}, property_type=bpy.props.StringProperty,)
    
    s_ecosystem_density_voxelsize : bpy.props.FloatProperty(
        default=1.0,
        min=0.0001,
        soft_max=100,
        unit="LENGTH",
        name=translate("Sample Area"),
        description=translate("To calculate the density of the chosen scatters, the space is divided into small cubic areas, called voxels. Each voxel counts the number of instances within, representing the 'Instance count' per area.\n\n• For accurate results, it's important to select a voxel size that matches the scale of your scatters"),
        update=scattering.update_factory.factory("s_ecosystem_density_voxelsize", delay_support=True,),
        )
    s_ecosystem_density_min : bpy.props.IntProperty(
        default=10,
        min=0,
        soft_max=9_999,
        name=translate("Instance Count"),
        description=translate("Set the minimum number of instances required within the defined sample area. This allows you to control the desired density range for the scatter system"),
        update=scattering.update_factory.factory("s_ecosystem_density_min", delay_support=True,),
        )
    s_ecosystem_density_falloff : bpy.props.IntProperty(
        default=0,
        min=0,
        soft_max=9_999,
        name=translate("Transition"),
        description=translate("Define a density falloff value to create a density transition effect"),
        update=scattering.update_factory.factory("s_ecosystem_density_falloff", delay_support=True,),
        )
    #remap
    s_ecosystem_density_fallremap_allow : bpy.props.BoolProperty(
        name=translate("Transition Control"),
        description=translate("Control the transition falloff by remapping the values with a curve-map graph or by adding a procedural noise transition to this falloff.\n\n• Please note that this feature assumes there is a transition distance to work with"),
        default=False, 
        update=scattering.update_factory.factory("s_ecosystem_density_fallremap_allow",),
        )
    s_ecosystem_density_fallremap_revert : bpy.props.BoolProperty(
        name=translate("Reverse Transition"),
        description=translate("Reverse the transition. This option will in fact remap the values from '0-1' to '1-0'"),
        default=False,
        update=scattering.update_factory.factory("s_ecosystem_density_fallremap_revert",),
        )
    s_ecosystem_density_fallnoisy_strength : bpy.props.FloatProperty(
        name=translate("Strength"), 
        description=translate("Combine the distance transition with a noise pattern. Great to make the transition look less uniform and more natural. Set this value to 0 to disable the noise overlay entirely"),
        default=0, min=0, max=5, precision=3,
        update=scattering.update_factory.factory("s_ecosystem_density_fallnoisy_strength", delay_support=True,),
        )
    s_ecosystem_density_fallnoisy_space : bpy.props.EnumProperty(
        name="NOT IN GUI",
        default="local",
        items= ( ("local", translate("Local"), "", "ORIENTATION_LOCAL",0 ),
                 ("global", translate("Global"), "", "WORLD",1 ),
               ),
        update=scattering.update_factory.factory("s_ecosystem_density_fallnoisy_space"),
        )
    s_ecosystem_density_fallnoisy_scale : bpy.props.FloatProperty(
        name=translate("Scale"),
        description=translate("The scale of a procedural texture.\n• A value of '0.01' will creates a large noise pattern.\n• A value of '10.0' will create a small pattern"),
        default=0.5, min=0, soft_max=2, precision=3, 
        update=scattering.update_factory.factory("s_ecosystem_density_fallnoisy_scale", delay_support=True,),
        )
    s_ecosystem_density_fallnoisy_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        description=translate("Change this value to randomize the result.\n\nIn 3D graphics, a seed is a starting value used by a random number generator to produce a sequence of random-looking numbers. These numbers can control things like the position, rotation, or scale of objects in a scene. Using the same seed will always generate the same 'random' result, which helps keep things consistent when needed."),
        update=scattering.update_factory.factory("s_ecosystem_density_fallnoisy_seed", delay_support=True,),
        )
    s_ecosystem_density_fallnoisy_is_random_seed : bpy.props.BoolProperty(
        name=translate("Randomize Seed"),
        description=translate("Randomize the value of the hereby seed property.\n\n• Note that pressing 'ALT' while clicking on this button will garantee the attribution of an unique seed value of this property for all selected-system(s)"),
        default=False,
        update=scattering.update_factory.factory("s_ecosystem_density_fallnoisy_is_random_seed",),
        )
    s_ecosystem_density_fallremap_data : bpy.props.StringProperty(
        set=scattering.update_factory.fallremap_setter("s_ecosystem_density.fallremap"),
        get=scattering.update_factory.fallremap_getter("s_ecosystem_density.fallremap"),
        )
    #Feature Influence
    s_ecosystem_density_dist_infl_allow : bpy.props.BoolProperty(name=translate("Enable Influence"), default=True, update=scattering.update_factory.factory("s_ecosystem_density_dist_infl_allow",),)
    s_ecosystem_density_dist_influence : bpy.props.FloatProperty(name=translate("Density"), description=translate("Influence your distribution density, you'll be able to adjust the intensity of the influence by changing this slider"), default=100, subtype="PERCENTAGE", min=0, max=100, precision=1, update=scattering.update_factory.factory("s_ecosystem_density_dist_influence", delay_support=True,),)
    s_ecosystem_density_scale_infl_allow : bpy.props.BoolProperty(name=translate("Allow Influence"), default=True, update=scattering.update_factory.factory("s_ecosystem_density_scale_infl_allow",),)
    s_ecosystem_density_scale_influence: bpy.props.FloatProperty(name=translate("Scale"), description=translate("Influence your distributed instances scale, you'll be able to adjust the intensity of the influence by changing this slider"), default=50, subtype="PERCENTAGE", min=0, max=100, precision=1, update=scattering.update_factory.factory("s_ecosystem_density_scale_influence", delay_support=True,),)
    #Feature Mask
    codegen_featuremask_properties(scope_ref=__annotations__, name="s_ecosystem_density",)

    # 88""Yb 88   88 .dP"Y8 88  88
    # 88__dP 88   88 `Ybo." 88  88
    # 88"""  Y8   8P o.`Y8b 888888
    # 88     `YbodP' 8bodP' 88  88
    
    ###################### This category of settings keyword is : "s_push"

    s_push_locked : bpy.props.BoolProperty(description=translate("Lock/Unlock Settings"),)

    def get_s_push_main_features(self, availability_conditions=True,):
        return ["s_push_offset_allow", "s_push_dir_allow", "s_push_noise_allow", "s_push_fall_allow",]

    s_push_master_allow : bpy.props.BoolProperty( 
        name=translate("Master Toggle"),
        description=translate("Mute/Unmute all features of this category in one click"),
        default=True, 
        update=scattering.update_factory.factory("s_push_master_allow", sync_support=False,),
        )

    ########## ########## Push Offset

    s_push_offset_allow : bpy.props.BoolProperty(
        name=translate("Apply Transformation"),
        description=translate("Displace the positions of your instances in space by the given transforms"),
        default=False,
        update=scattering.update_factory.factory("s_push_offset_allow",),
        )
    s_push_offset_space : bpy.props.EnumProperty(
        name=translate("Space"),
        description=translate("Displacement space.\nThe displacement will occur along an axis toward a certain distance, and the calculation of these parameters can vary if we take transforms into consideration"),
        default="local", 
        items= ( ("local", translate("Local"), translate("Choose the 'Local' option if you'd like the displacement to stay stable even when your surface(s) transforms are changing"), "ORIENTATION_LOCAL",1 ),
                 ("global", translate("Global"), translate("Choose the 'Global' option if you'd like the displacement to stay consistent in world space"), "WORLD",2 ),
               ),
        update=scattering.update_factory.factory("s_push_offset_space"),
        )
    s_push_offset_add_value : bpy.props.FloatVectorProperty(
        name=translate("Offset"),
        description=translate("Offset Transforms"),
        default=(0,0,0),
        subtype="XYZ",
        unit="LENGTH",
        update=scattering.update_factory.factory("s_push_offset_add_value", delay_support=True,),
        )
    s_push_offset_add_random : bpy.props.FloatVectorProperty(
        name=translate("Offset"),
        description=translate("Random Offset Transforms"),
        default=(0,0,0),
        subtype="XYZ",
        unit="LENGTH",
        update=scattering.update_factory.factory("s_push_offset_add_random", delay_support=True,),
        )
    s_push_offset_rotate_value : bpy.props.FloatVectorProperty(
        name=translate("Rotate"),
        description=translate("Rotation Transforms"),
        default=(0,0,0),
        subtype="XYZ",
        unit="ROTATION",
        update=scattering.update_factory.factory("s_push_offset_rotate_value", delay_support=True,),
        )
    s_push_offset_rotate_random : bpy.props.FloatVectorProperty(
        name=translate("Rotate"),
        description=translate("Random Rotation Transforms"),
        default=(0,0,0),
        subtype="XYZ",
        unit="ROTATION",
        update=scattering.update_factory.factory("s_push_offset_rotate_random", delay_support=True,),
        )
    s_push_offset_scale_value : bpy.props.FloatVectorProperty(
        name=translate("Scale"),
        description=translate("Scale Transforms"),
        default=(1,1,1),
        subtype="XYZ",
        update=scattering.update_factory.factory("s_push_offset_scale_value", delay_support=True,),
        )
    s_push_offset_scale_random : bpy.props.FloatVectorProperty(
        name=translate("Scale"),
        description=translate("Random Scale Transforms"),
        default=(0,0,0),
        subtype="XYZ",
        update=scattering.update_factory.factory("s_push_offset_scale_random", delay_support=True,),
        )
    s_push_offset_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        description=translate("Change this value to randomize the result.\n\nIn 3D graphics, a seed is a starting value used by a random number generator to produce a sequence of random-looking numbers. These numbers can control things like the position, rotation, or scale of objects in a scene. Using the same seed will always generate the same 'random' result, which helps keep things consistent when needed."),
        update=scattering.update_factory.factory("s_push_offset_seed", delay_support=True,),
        )
    s_push_offset_is_random_seed : bpy.props.BoolProperty(
        name=translate("Randomize Seed"),
        description=translate("Randomize the value of the hereby seed property.\n\n• Note that pressing 'ALT' while clicking on this button will garantee the attribution of an unique seed value of this property for all selected-system(s)"),
        default=False,
        update=scattering.update_factory.factory("s_push_offset_is_random_seed",),
        )
    #Feature Mask
    codegen_featuremask_properties(scope_ref=__annotations__, name="s_push_offset",)

    ########## ########## Push Direction

    s_push_dir_allow : bpy.props.BoolProperty(
        name=translate("Displace Along"),
        description=translate("Displace the positions of your instances along a chosen axis"),
        default=False,
        update=scattering.update_factory.factory("s_push_dir_allow",),
        )
    s_push_dir_space : bpy.props.EnumProperty(
        name=translate("Space"),
        description=translate("Displacement space.\nThe displacement will occur along an axis toward a certain distance, and the calculation of these parameters can vary if we take transforms into consideration"),
        default="global", 
        items= ( ("local", translate("Local"), translate("Choose the 'Local' option if you'd like the displacement to stay stable even when your surface(s) transforms are changing"), "ORIENTATION_LOCAL",1 ),
                 ("global", translate("Global"), translate("Choose the 'Global' option if you'd like the displacement to stay consistent in world space"), "WORLD",2 ),
               ),
        update=scattering.update_factory.factory("s_push_dir_space"),
        )
    s_push_dir_method : bpy.props.EnumProperty( #changes to items in this enum must be in accordance of special method below
         name=translate("Axis"),
         description=translate("Choose toward which direction you'll offset your instances"),
         default= "push_normal",
         items= ( ("push_normal", translate("Surface Normal"), translate("Offset your instances along the normal direction of the surfaces they are distributed upon"), "NORMALS_FACE", 0),
                  ("push_point",  translate("Instances Normal"), translate("Offset your instances along their own +Z axes"), "SNAP_NORMAL", 1),
                  ("push_local",  translate("Local Z"), translate("Offset your instances along the +Z direction of the object's you are scattering upon"), "ORIENTATION_LOCAL", 2),
                  ("push_global", translate("Global Z"), translate("Offset your instances along the +Z axis of the world-space"), "WORLD", 3),
                ),
         update=scattering.update_factory.factory("s_push_dir_method"),
         )
    #special methods for some distribution type. We only cull or change name of base method = superficial change
    s_push_dir_method_projbezareanosurf_special : bpy.props.EnumProperty(
         name=translate("Axis"),
         description=translate("Choose toward which direction you'll offset your instances"),
         default= "push_local",
         items= ( ("push_point",  translate("Instances Normal"), translate("Offset your instances along their own +Z axes"), "SNAP_NORMAL", 1),
                  ("push_local",  translate("Local Z"), translate("Offset your instances along the +Z direction of the object's you are scattering upon"), "ORIENTATION_LOCAL", 2),
                  ("push_global", translate("Global Z"), translate("Offset your instances along the +Z axis of the world-space"), "WORLD", 3),
                ),
         update=scattering.update_factory.factory("s_push_dir_method_projbezareanosurf_special"),
         )
    s_push_dir_method_projbezlinenosurf_special : bpy.props.EnumProperty(
         name=translate("Axis"),
         description=translate("Choose toward which direction you'll offset your instances"),
         default= "push_normal",
         items= ( ("push_normal", translate("Curve Normal"), translate("Offset your instances along the normal direction of the curve they are distributed upon"), "CURVE_BEZCURVE", 0),
                  ("push_point",  translate("Instances Normal"), translate("Offset your instances along their own +Z axes"), "SNAP_NORMAL", 1),
                  ("push_local",  translate("Local Z"), translate("Offset your instances along the +Z direction of the object's you are scattering upon"), "ORIENTATION_LOCAL", 2),
                  ("push_global", translate("Global Z"), translate("Offset your instances along the +Z axis of the world-space"), "WORLD", 3),
                ),
         update=scattering.update_factory.factory("s_push_dir_method_projbezlinenosurf_special"),
         )
    s_push_dir_method_projemptiesnosurf_special : bpy.props.EnumProperty(
         name=translate("Axis"),
         description=translate("Choose toward which direction you'll offset your instances"),
         default= "push_normal",
         items= ( ("push_normal", translate("Empties Z"), translate("Offset your instances along the +Z direction of the empties they are distributed upon"), "EMPTY_AXIS", 0),
                  ("push_point",  translate("Instances Normal"), translate("Offset your instances along their own +Z axes"), "SNAP_NORMAL", 1),
                  ("push_global", translate("Global Z"), translate("Offset your instances along the +Z axis of the world-space"), "WORLD", 3),
                ),
         update=scattering.update_factory.factory("s_push_dir_method_projemptiesnosurf_special"),
         )
    s_push_dir_add_value : bpy.props.FloatProperty(
        name=translate("Offset"),
        description=translate("Dispace your instances until reaching the given distance value"),
        default=1,
        precision=3,
        subtype="DISTANCE",
        update=scattering.update_factory.factory("s_push_dir_add_value", delay_support=True,),
        )
    s_push_dir_add_random : bpy.props.FloatProperty(
        name=translate("Random"),
        description=translate("Random displace your distances to a maximal given value"),
        default=0,
        precision=3,
        subtype="DISTANCE",
        update=scattering.update_factory.factory("s_push_dir_add_random", delay_support=True,),
        )
    s_push_dir_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        description=translate("Change this value to randomize the result.\n\nIn 3D graphics, a seed is a starting value used by a random number generator to produce a sequence of random-looking numbers. These numbers can control things like the position, rotation, or scale of objects in a scene. Using the same seed will always generate the same 'random' result, which helps keep things consistent when needed."),
        update=scattering.update_factory.factory("s_push_dir_seed", delay_support=True,),
        )
    s_push_dir_is_random_seed : bpy.props.BoolProperty(
        name=translate("Randomize Seed"),
        description=translate("Randomize the value of the hereby seed property.\n\n• Note that pressing 'ALT' while clicking on this button will garantee the attribution of an unique seed value of this property for all selected-system(s)"),
        default=False,
        update=scattering.update_factory.factory("s_push_dir_is_random_seed",),
        )
    #Feature Mask
    codegen_featuremask_properties(scope_ref=__annotations__, name="s_push_dir",)

    #TODO more method for 5.1 ?
    # s_push_dir_object_ptr  : bpy.props.PointerProperty(
    #     name=translate("Object"),
    #     type=bpy.types.Object, 
    #     update=scattering.update_factory.factory("s_push_dir_object_ptr"),
    #     )
    # s_push_dir_normalize : bpy.props.BoolProperty(
    #     name=translate("Vector Normalization"),
    #     default=True,
    #     update=scattering.update_factory.factory("s_push_dir_normalize"),
    #     )
    # s_push_dir_custom_direction : bpy.props.FloatVectorProperty(
    #     default=(0,0,1),
    #     subtype="DIRECTION",
    #     update=scattering.update_factory.factory("s_push_dir_custom_direction", delay_support=True,),
    #     )

    ########## ########## Push Noise 

    s_push_noise_allow : bpy.props.BoolProperty(
        name=translate("Noise Displacement"),
        description=translate("Displace the positions of your instances randomly"),
        default=False,
        update=scattering.update_factory.factory("s_push_noise_allow"),
        )
    s_push_noise_space : bpy.props.EnumProperty(
        name=translate("Space"),
        description=translate("Displacement space.\nThe displacement will occur along an axis toward a certain distance, and the calculation of these parameters can vary if we take transforms into consideration"),
        default="local", 
        items= ( ("local", translate("Local"), translate("Choose the 'Local' option if you'd like the displacement to stay stable even when your surface(s) transforms are changing"), "ORIENTATION_LOCAL",1 ),
                 ("global", translate("Global"), translate("Choose the 'Global' option if you'd like the displacement to stay consistent in world space"), "WORLD",2 ),
               ),
        update=scattering.update_factory.factory("s_push_noise_space"),
        )
    s_push_noise_vector : bpy.props.FloatVectorProperty(
        name=translate("Random Offset"),
        description=translate("Maximal distance the random displacement can reach on a XYZ axis"),
        default=(1,1,1),
        subtype="XYZ_LENGTH",
        update=scattering.update_factory.factory("s_push_noise_vector", delay_support=True,),
        )
    s_push_noise_is_animated : bpy.props.BoolProperty(
        name=translate("Noise Animation"),
        description=translate("Animate the random displacement following a noise animation"),
        default=True,
        update=scattering.update_factory.factory("s_push_noise_is_animated"),
        )
    s_push_noise_speed : bpy.props.FloatProperty(
        name=translate("Speed Factor"),
        description=translate("The speed of your noise animation"),
        default=1,
        soft_min=0,
        soft_max=5,
        update=scattering.update_factory.factory("s_push_noise_speed", delay_support=True,),
        )
    s_push_noise_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        description=translate("Change this value to randomize the result.\n\nIn 3D graphics, a seed is a starting value used by a random number generator to produce a sequence of random-looking numbers. These numbers can control things like the position, rotation, or scale of objects in a scene. Using the same seed will always generate the same 'random' result, which helps keep things consistent when needed."),
        update=scattering.update_factory.factory("s_push_noise_seed", delay_support=True,),
        )
    s_push_noise_is_random_seed : bpy.props.BoolProperty(
        name=translate("Randomize Seed"),
        description=translate("Randomize the value of the hereby seed property.\n\n• Note that pressing 'ALT' while clicking on this button will garantee the attribution of an unique seed value of this property for all selected-system(s)"),
        default=False,
        update=scattering.update_factory.factory("s_push_noise_is_random_seed",),
        )
    #Feature Mask
    codegen_featuremask_properties(scope_ref=__annotations__, name="s_push_noise",)

    ########## ########## Fall Effect

    s_push_fall_allow : bpy.props.BoolProperty(
        name=translate("Falling Displacement Animation"),
        description=translate("Displace the positions of your instances following a 'drop' effect. Possibility of also influencing your instances rotation along the fall to achieve a 'leaf-fall' effect"),
        default=False,
        update=scattering.update_factory.factory("s_push_fall_allow"),
        )
    s_push_fall_space : bpy.props.EnumProperty(
        name=translate("Space"),
        description=translate("Displacement space.\nThe displacement will occur along an axis toward a certain distance, and the calculation of these parameters can vary if we take transforms into consideration"),
        default="global", 
        items= ( ("local", translate("Local"), translate("Choose the 'Local' option if you'd like the displacement to stay stable even when your surface(s) transforms are changing"), "ORIENTATION_LOCAL",1 ),
                 ("global", translate("Global"), translate("Choose the 'Global' option if you'd like the displacement to stay consistent in world space"), "WORLD",2 ),
               ),
        update=scattering.update_factory.factory("s_push_fall_space"),
        )
    s_push_fall_height : bpy.props.FloatProperty(
        name=translate("Fall Distance"),
        description=translate("Maximal height of the column of instances falling toward the -Z direction"),
        default=20,
        subtype="DISTANCE",
        update=scattering.update_factory.factory("s_push_fall_height", delay_support=True,),
        )
    s_push_fall_key1_pos : bpy.props.IntProperty(
        name="",
        description=translate("Start frame.\nThe falling animation will start at this frame"),
        default=0,
        update=scattering.update_factory.factory("s_push_fall_key1_pos", delay_support=True,),
        )
    s_push_fall_key1_height : bpy.props.FloatProperty(
        name="",
        description=translate("Starting Height.\nStarting Z position the column of instances will start falling from"),
        default=5,
        subtype="DISTANCE",
        update=scattering.update_factory.factory("s_push_fall_key1_height", delay_support=True,),
        )
    s_push_fall_key2_pos : bpy.props.IntProperty(
        name="",
        description=translate("End Frame.\nThe falling animation will end at this frame"),
        default=100,
        update=scattering.update_factory.factory("s_push_fall_key2_pos", delay_support=True,),
        )
    s_push_fall_key2_height : bpy.props.FloatProperty(
        name="",
        description=translate("Ending Height.\nEnd Z position the column of instances will end up falling to"),
        default=-20,
        subtype="DISTANCE",
        update=scattering.update_factory.factory("s_push_fall_key2_height", delay_support=True,),
        )
    s_push_fall_stop_when_initial_z : bpy.props.BoolProperty(
        name=translate("Rest at Initial Position"),
        description=translate("Stop the instances from falling when they reach their initial position, simulating a collision effect from the fall"),
        default=True,
        update=scattering.update_factory.factory("s_push_fall_stop_when_initial_z"),
        )
    s_push_fall_turbulence_allow : bpy.props.BoolProperty(
        name=translate("Falling Turbulence"),
        description=translate("When falling, the instances will randomly offset and/or rotate giving it a more organic look"),
        default=False,
        update=scattering.update_factory.factory("s_push_fall_turbulence_allow"),
        )
    s_push_fall_turbulence_spread : bpy.props.FloatVectorProperty(
        name=translate("Reach"),
        description=translate("The instances will randomly offset toward these XYZ distances during the fall"),
        default=(1.0,1.0,0.5),
        subtype="XYZ_LENGTH",
        update=scattering.update_factory.factory("s_push_fall_turbulence_spread", delay_support=True,),
        )
    s_push_fall_turbulence_speed : bpy.props.FloatProperty(
        name=translate("Speed"),
        description=translate("The speed of instances doing back-and-forth from the specified distance above"),
        default=1,
        min=0,
        soft_max=4,
        update=scattering.update_factory.factory("s_push_fall_turbulence_speed", delay_support=True,),
        )
    s_push_fall_turbulence_rot_vector : bpy.props.FloatVectorProperty(
        name=translate("Rotation"),
        description=translate("The instances will randomly rotate to this specified maximal euler angle during the fall"),
        default=(0.5,0.5,0.5),
        subtype="EULER",
        update=scattering.update_factory.factory("s_push_fall_turbulence_rot_vector", delay_support=True,),
        )
    s_push_fall_turbulence_rot_factor : bpy.props.FloatProperty(
        name=translate("Factor"),
        description=translate("Influence the strength of the rotation effect"),
        default=1,
        soft_min=0,
        soft_max=1,
        update=scattering.update_factory.factory("s_push_fall_turbulence_rot_factor", delay_support=True,),
        )
    s_push_fall_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        description=translate("Change this value to randomize the result.\n\nIn 3D graphics, a seed is a starting value used by a random number generator to produce a sequence of random-looking numbers. These numbers can control things like the position, rotation, or scale of objects in a scene. Using the same seed will always generate the same 'random' result, which helps keep things consistent when needed."),
        update=scattering.update_factory.factory("s_push_fall_seed", delay_support=True,),
        )
    s_push_fall_is_random_seed : bpy.props.BoolProperty(
        name=translate("Randomize Seed"),
        description=translate("Randomize the value of the hereby seed property.\n\n• Note that pressing 'ALT' while clicking on this button will garantee the attribution of an unique seed value of this property for all selected-system(s)"),
        default=False,
        update=scattering.update_factory.factory("s_push_fall_is_random_seed",),
        )
    #Feature Mask
    codegen_featuremask_properties(scope_ref=__annotations__, name="s_push_fall",)

    # Yb        dP 88 88b 88 8888b.  
    #  Yb  db  dP  88 88Yb88  8I  Yb 
    #   YbdPYbdP   88 88 Y88  8I  dY 
    #    YP  YP    88 88  Y8 8888Y"  

    ###################### This category of settings keyword is : "s_wind"

    s_wind_locked : bpy.props.BoolProperty(description=translate("Lock/Unlock Settings"),)

    def get_s_wind_main_features(self, availability_conditions=True,):
        return ["s_wind_wave_allow", "s_wind_noise_allow",]

    s_wind_master_allow : bpy.props.BoolProperty(
        name=translate("Master Toggle"),
        description=translate("Mute/Unmute all features of this category in one click"),
        default=True, 
        update=scattering.update_factory.factory("s_wind_master_allow", sync_support=False,),
        )

    ########## ########## Wind Wave

    s_wind_wave_allow : bpy.props.BoolProperty(
        name=translate("Wind Wave Animation"),
        description=translate("Affect the rotation of your instances by tilting them on their sides following a repeating noise texture giving them the illusion of being affected by wind currents"),
        default=False,
        update=scattering.update_factory.factory("s_wind_wave_allow",),
        )
    s_wind_wave_space : bpy.props.EnumProperty(
        name=translate("Space"),
        description=translate("Evaluation Space.\nDetermines if the wind direction is affected by potential transforms"),
        default="global", 
        items= ( ("local", translate("Local"), translate("The wind direction will follow the transforms of the objects you are scattering upon"), "ORIENTATION_LOCAL",0 ),
                 ("global", translate("Global"), translate("The wind direction will align to global space, ignoring any of your object's transforms"), "WORLD",1 ),
               ),
        update=scattering.update_factory.factory("s_wind_wave_space"),
        )

    s_wind_wave_method : bpy.props.EnumProperty(
        name=translate("Animation"),
        description=translate("Animation repetition"),
        default= "wind_wave_constant", 
        items= ( ("wind_wave_constant", translate("Fixed"), translate("The wind animation seed is reliable, fixed in time with no regard to loop-ability"), "TRACKING_FORWARDS_SINGLE", 0,),
                 ("wind_wave_loopable", translate("Loop-able"), translate("The wind animation will seamlessly loop itself"), "MOD_DASH", 1,),
               ),
        update=scattering.update_factory.factory("s_wind_wave_method",),
        ) 
    s_wind_wave_loopable_cliplength_allow : bpy.props.BoolProperty(
        name=translate("Define Loop"),
        description=translate("By default, the animation loop will automatically adapt & recalculate depending on your start/end frames. Use this option if you'd like to define the min/max frames yourself"),
        default=False,
        update=scattering.update_factory.factory("s_wind_wave_loopable_cliplength_allow"),
        )
    s_wind_wave_loopable_frame_start : bpy.props.IntProperty(
        min=0, default=0,
        update=scattering.update_factory.factory("s_wind_wave_loopable_frame_start", delay_support=True,),
        )
    s_wind_wave_loopable_frame_end : bpy.props.IntProperty(
        min=0, default=200,
        update=scattering.update_factory.factory("s_wind_wave_loopable_frame_end", delay_support=True,),
        )

    s_wind_wave_speed : bpy.props.FloatProperty(
        name=translate("Speed"), 
        description=translate("The speed of the wind texture passing through"),
        default=1.0, 
        soft_min=0.001, 
        soft_max=5, 
        precision=3,
        update=scattering.update_factory.factory("s_wind_wave_speed", delay_support=True,),
        )
    s_wind_wave_force : bpy.props.FloatProperty(
        name=translate("Strength"), 
        description=translate("Describes the tilt strength the wind texture has on your instances rotation"),
        default=1, 
        soft_min=0, 
        soft_max=3, 
        precision=3,
        update=scattering.update_factory.factory("s_wind_wave_force", delay_support=True,),
        )
    s_wind_wave_scale_influence : bpy.props.BoolProperty(
        name=translate("Scale Influence"), 
        description=translate("The smaller/taller instances are, the less/more affected they are from the wind force"),
        default=False,
        update=scattering.update_factory.factory("s_wind_wave_scale_influence",),
        )
    s_wind_wave_scale_influence_factor : bpy.props.FloatProperty(
        name=translate("Factor"),
        description=translate("An influence factor of an effect is a value that determines how strong the effect is. A higher factor means more impact, while lower factor means less"),
        default=1,
        soft_min=0,
        soft_max=1,
        precision=3,
        update=scattering.update_factory.factory("s_wind_wave_scale_influence_factor", delay_support=True,),
        )
    s_wind_wave_swinging : bpy.props.BoolProperty(
        name=translate("Bilateral Swing"), 
        description=translate("The wind effect will swing instances back and forth instead of unilaterally inclining them"),
        default=False,
        update=scattering.update_factory.factory("s_wind_wave_swinging",),
        )
    s_wind_wave_swinging_factor : bpy.props.FloatProperty(
        name=translate("Factor"),
        description=translate("An influence factor of an effect is a value that determines how strong the effect is. A higher factor means more impact, while lower factor means less"),
        default=1,
        soft_min=0,
        soft_max=1,
        precision=3,
        update=scattering.update_factory.factory("s_wind_wave_swinging_factor", delay_support=True,),
        )
    s_wind_wave_texture_scale : bpy.props.FloatProperty(
        name=translate("Scale"),
        description=translate("The scale of a procedural texture.\n• A value of '0.01' will creates a large noise pattern.\n• A value of '10.0' will create a small pattern"),
        default=0.1,
        update=scattering.update_factory.factory("s_wind_wave_texture_scale", delay_support=True,),
        )
    s_wind_wave_texture_turbulence : bpy.props.FloatProperty(
        name=translate("Turbulence"),
        default=0,
        soft_min=0,
        soft_max=10,
        update=scattering.update_factory.factory("s_wind_wave_texture_turbulence", delay_support=True,),
        )
    s_wind_wave_texture_distorsion : bpy.props.FloatProperty(
        name=translate("Distortion"),
        default=0,
        soft_min=0,
        soft_max=3,
        update=scattering.update_factory.factory("s_wind_wave_texture_distorsion", delay_support=True,),
        )
    s_wind_wave_texture_brightness : bpy.props.FloatProperty(
        name=translate("Brightness"),
        default=1,
        min=0, 
        soft_max=2,
        update=scattering.update_factory.factory("s_wind_wave_texture_brightness", delay_support=True,),
        )
    s_wind_wave_texture_contrast : bpy.props.FloatProperty(
        name=translate("Contrast"),
        default=1.5,
        min=0, 
        soft_max=5,
        update=scattering.update_factory.factory("s_wind_wave_texture_contrast", delay_support=True,),
        )
    s_wind_wave_dir_method : bpy.props.EnumProperty(
         name=translate("Wind Direction"),
         description=translate("Define the direction of the tilting effect, and of the wind texture offset"),
         default= "fixed", 
         items= ( ("fixed", translate("Fixed Direction"), "", "SORT_DESC", 0),
                  ("vcol",  translate("Vertex-Color Flowmap"), "", "DECORATE_DRIVER", 1),
                ),
         update=scattering.update_factory.factory("s_wind_wave_dir_method"),
         )
    s_wind_wave_direction : bpy.props.FloatProperty(
        name=translate("Direction"), 
        description=translate("Correspond to the direction of the rotation tilting effect and the direction wind wave texture"),
        subtype="ANGLE",
        default=0.87266, 
        soft_min=-6.283185, 
        soft_max=6.283185, #=360d
        precision=3,
        update=scattering.update_factory.factory("s_wind_wave_direction", delay_support=True,),
        )
    s_wind_wave_direction_random : bpy.props.FloatProperty(
        name=translate("Randomness"),
        description=translate("The wind texture also influences a tilting on the sides of the chosen direction above"),
        default=0,
        soft_min=0,
        soft_max=1,
        precision=3,
        update=scattering.update_factory.factory("s_wind_wave_direction_random", delay_support=True,),
        )
    s_wind_wave_flowmap_ptr : bpy.props.StringProperty(
        name=translate("Color-Attribute Pointer"),
        description=translate("Search across all your surface(s) for shared color attributes.\nWe will highlight the pointer in red if the attribute is not shared across your surface(s)"),
        search=lambda s,c,e: get_surfs_shared_attrs(system=s, attr_type='vcol', searchname=e,),
        search_options={'SUGGESTION','SORT'},
        update=scattering.update_factory.factory("s_wind_wave_flowmap_ptr"),
        )
    #Feature Mask
    codegen_featuremask_properties(scope_ref=__annotations__, name="s_wind_wave",)

    ########## ########## Wind Noise

    s_wind_noise_allow : bpy.props.BoolProperty(
        name=translate("Wind Turbulence Animation"),
        description=translate("Affect the rotation of your instances by tilting them on their sides randomly giving them the illusion of being affected by random wind breezes"),
        default=False,
        update=scattering.update_factory.factory("s_wind_noise_allow",),
        )
    s_wind_noise_space : bpy.props.EnumProperty(
        name=translate("Space"),
        description=translate("Evaluation Space.\nDetermines if the wind direction is affected by potential transforms"),
        default="global", 
        items= ( ("local", translate("Local"), translate("The wind direction will follow the transforms of the objects you are scattering upon"), "ORIENTATION_LOCAL",0 ),
                 ("global", translate("Global"), translate("The wind direction will align to global space, ignoring any of your object's transforms"), "WORLD",1 ),
               ),
        update=scattering.update_factory.factory("s_wind_noise_space"),
        )

    s_wind_noise_method : bpy.props.EnumProperty(
        name=translate("Animation"),
        description=translate("Animation repetition"),
        default= "wind_noise_constant", 
        items= ( ("wind_noise_constant", translate("Fixed"), translate("The wind animation seed is reliable, fixed in time with no regard to loop-ability"), "TRACKING_FORWARDS_SINGLE", 0,),
                 ("wind_noise_loopable", translate("Loop-able"), translate("The wind animation will seamlessly loop itself"), "MOD_DASH", 1,),
               ),
        update=scattering.update_factory.factory("s_wind_noise_method"),
        ) 
    s_wind_noise_loopable_cliplength_allow : bpy.props.BoolProperty(
        name=translate("Define Loop"),
        description=translate("By default, the animation loop will automatically adapt & recalculate depending on your start/end frames. Use this option if you'd like to define the min/max frames yourself"),
        default=False,
        update=scattering.update_factory.factory("s_wind_noise_loopable_cliplength_allow"),
        )
    s_wind_noise_loopable_frame_start : bpy.props.IntProperty(
        min=0, default=0,
        update=scattering.update_factory.factory("s_wind_noise_loopable_frame_start", delay_support=True,),
        )
    s_wind_noise_loopable_frame_end : bpy.props.IntProperty(
        min=0, default=200,
        update=scattering.update_factory.factory("s_wind_noise_loopable_frame_end", delay_support=True,),
        )

    s_wind_noise_force : bpy.props.FloatProperty(
        name=translate("Strength"), 
        description=translate("Define the force of the wind noisy turbulence"),
        default=0.5, 
        soft_min=0, 
        soft_max=3, 
        precision=3,
        update=scattering.update_factory.factory("s_wind_noise_force", delay_support=True,),
        )
    s_wind_noise_speed : bpy.props.FloatProperty(
        name=translate("Speed"), 
        description=translate("Define the speed of the wind noisy turbulence.\n\n• Note that if the animation method is set to loop it might have an influence on the turbulence speed"),
        default=1, 
        soft_min=0.001, 
        soft_max=10, 
        precision=3,
        update=scattering.update_factory.factory("s_wind_noise_speed", delay_support=True,),
        )
    #Feature Mask
    codegen_featuremask_properties(scope_ref=__annotations__, name="s_wind_noise",)

    # Yb    dP 88 .dP"Y8 88 88""Yb 88 88     88 888888 Yb  dP
    #  Yb  dP  88 `Ybo." 88 88__dP 88 88     88   88    YbdP
    #   YbdP   88 o.`Y8b 88 88""Yb 88 88  .o 88   88     8P
    #    YP    88 8bodP' 88 88oodP 88 88ood8 88   88    dP

    ###################### This category of settings keyword is : "s_visibility"
    ###################### this category is Not supported by Preset

    s_visibility_locked   : bpy.props.BoolProperty(description=translate("Lock/Unlock Settings"),)

    def get_s_visibility_main_features(self, availability_conditions=True,):
        r = ["s_visibility_facepreview_allow","s_visibility_view_allow", "s_visibility_cam_allow", "s_visibility_maxload_allow",]
        if (not availability_conditions):
            return r
        if (self.s_distribution_method=="volume" or not self.is_using_surf):
            r.remove("s_visibility_facepreview_allow")
        return r

    s_visibility_master_allow : bpy.props.BoolProperty( 
        name=translate("Master Toggle"),
        description=translate("Mute/Unmute all features of this category in one click"),
        default=True, 
        update=scattering.update_factory.factory("s_visibility_master_allow", sync_support=False,),
        )

    ########## ########## Just for UI... 

    s_visibility_statistics_allow : bpy.props.BoolProperty(
        name=translate("Show Statistics"),
        description=translate("Compute how many instances the distribution generates"),
        default=True,
        )

    ########## ########## Only show on selected faces

    s_visibility_facepreview_allow : bpy.props.BoolProperty( 
        name=translate("Distribution Preview"),
        description=translate("Remove instances not located on the defined preview area"),
        default=False,
        update=scattering.update_factory.factory("s_visibility_facepreview_allow"),
        )

    s_visibility_facepreview_allow_screen : bpy.props.BoolProperty(default=True,  name=translate("Visibility State. (Define when the feature is active)"), description=translate("This optimization feature will be active only when working on the 3Dviewport, not during rendered view nor the final render"), update=scattering.update_factory.factory_viewport_method_proxy("s_visibility_facepreview","screen"),) #ui purpose
    s_visibility_facepreview_allow_shaded : bpy.props.BoolProperty(default=True,  name=translate("Visibility State. (Define when the feature is active)"), description=translate("This optimization feature will be active only when working in the viewport & during rendered-view, not during the final render"), update=scattering.update_factory.factory_viewport_method_proxy("s_visibility_facepreview","shaded"),) #ui purpose
    s_visibility_facepreview_allow_render : bpy.props.BoolProperty(default=False, name=translate("Visibility State. (Define when the feature is active)"), description=translate("This optimization feature will be active at all times, including the final render"), update=scattering.update_factory.factory_viewport_method_proxy("s_visibility_facepreview","render"),) #ui purpose
    s_visibility_facepreview_viewport_method : bpy.props.EnumProperty( #Internal Purpose
        default="viewport_only",
        items=(("viewport_only","sc+sh","","",1),("except_rendered","sc","","",0),("viewport_and_render","sc+sh+rd","","",2),),
        update=scattering.update_factory.factory("s_visibility_facepreview_viewport_method"),
        )

    ########## ########## Remove % of particles

    s_visibility_view_allow : bpy.props.BoolProperty( 
        name=translate("Percentage Reduction"),
        description=translate("Remove instances following a removal-rate percentage"),
        default=False,
        update=scattering.update_factory.factory("s_visibility_view_allow"),
        )
    s_visibility_view_percentage : bpy.props.FloatProperty(
        name=translate("Rate"),
        description=translate("The percentage of removed instances. Great to lower the amount of instances"),
        subtype="PERCENTAGE",
        default=80,
        min=0,
        max=100,
        precision=1,
        update=scattering.update_factory.factory("s_visibility_view_percentage", delay_support=True,),
        )

    s_visibility_view_allow_screen : bpy.props.BoolProperty(default=True,  name=translate("Visibility State. (Define when the feature is active)"), description=translate("This optimization feature will be active only when working on the 3Dviewport, not during rendered view nor the final render"), update=scattering.update_factory.factory_viewport_method_proxy("s_visibility_view","screen"),) #ui purpose
    s_visibility_view_allow_shaded : bpy.props.BoolProperty(default=False, name=translate("Visibility State. (Define when the feature is active)"), description=translate("This optimization feature will be active only when working in the viewport & during rendered-view, not during the final render"), update=scattering.update_factory.factory_viewport_method_proxy("s_visibility_view","shaded"),) #ui purpose
    s_visibility_view_allow_render : bpy.props.BoolProperty(default=False, name=translate("Visibility State. (Define when the feature is active)"), description=translate("This optimization feature will be active at all times, including the final render"), update=scattering.update_factory.factory_viewport_method_proxy("s_visibility_view","render"),) #ui purpose
    s_visibility_view_viewport_method : bpy.props.EnumProperty( #Internal Purpose
        default="except_rendered",
        items=(("viewport_only","sc+sh","","",1),("except_rendered","sc","","",0),("viewport_and_render","sc+sh+rd","","",2),),
        update=scattering.update_factory.factory("s_visibility_view_viewport_method"),
        )

    ########## ########## Camera Optimization

    s_visibility_cam_allow : bpy.props.BoolProperty(
        name=translate("Camera Optimizations"),
        description=translate("Remove instances based on camera optimization techniques"),
        default=False,
        update=scattering.update_factory.factory("s_visibility_cam_allow"),
        )
    s_visibility_cam_predist_allow : bpy.props.BoolProperty(
        name=translate("Efficient Distribution by Culling Surface(s)"),
        description=translate("Optimize your compute speed by masking surfaces-meshes invisible by the active camera view during the the initial distribution of the scatter algorithm.\n\nWhen enabled, this option will cull your surfaces-meshes invisible by the camera view *before* distributing the points (Instead of scattering across the entire surface first and removing the points later). In other words this option will scatter points only on the visible areas of your surfaces to begin with, therefore creating a speed up in processing time, especially for large surfaces, as it avoids the generation of unnecessary points.\n\nAdditional Information:\n• This option works best when using 'Frustum' or 'Distance' culling. 'Occlusion' will not benefit from any peformance gains.\n• This option works best for surfaces that have even and relatively dense topologies.\n• Not all distribution methods will benefit from this optimization option and its button will be greyed out when not compatible with your active distribution method"),
        default=True,
        update=scattering.update_factory.factory("s_visibility_cam_predist_allow"),
        )

    #Frustrum 

    s_visibility_camclip_allow : bpy.props.BoolProperty(
        name=translate("Frustum Culling"),
        description=translate("Only show instances whose origins are located inside the active-camera frustum volume"),
        default=True,
        update=scattering.update_factory.factory("s_visibility_camclip_allow"),
        )
    s_visibility_camclip_cam_autofill : bpy.props.BoolProperty(
        name=translate("Auto-define Frustrum"),
        description=translate("Define the settings of the frustrum cone automatically depending on the active camera"),
        default=True,
        update=scattering.update_factory.factory("s_visibility_camclip_cam_autofill"),
        )
    s_visibility_camclip_cam_lens : bpy.props.FloatProperty( #handler may set these values automatically
        name=translate("Lens"),
        subtype="DISTANCE_CAMERA",
        default=50,
        min=1,
        soft_max=5_000, 
        update=scattering.update_factory.factory("s_visibility_camclip_cam_lens", delay_support=True,),
        )
    s_visibility_camclip_cam_sensor_width : bpy.props.FloatProperty( #handler may set these values automatically
        name=translate("Sensor"),
        subtype="DISTANCE_CAMERA",
        default=36,
        min=1,
        soft_max=200, 
        update=scattering.update_factory.factory("s_visibility_camclip_cam_sensor_width", delay_support=True,),
        )
    s_visibility_camclip_cam_res_xy : bpy.props.FloatVectorProperty( #handler may set these values automatically
        name=translate("Resolution"),
        subtype="XYZ",
        size=2,
        default=(1920,1080),
        precision=0,
        update=scattering.update_factory.factory("s_visibility_camclip_cam_res_xy", delay_support=True,),
        )
    s_visibility_camclip_cam_shift_xy : bpy.props.FloatVectorProperty( #handler may set these values automatically
        name=translate("Shift"),
        subtype="XYZ",
        size=2,
        default=(0,0),
        soft_min=-2,
        soft_max=2, 
        precision=3,
        update=scattering.update_factory.factory("s_visibility_camclip_cam_shift_xy", delay_support=True,),
        )
    s_visibility_camclip_cam_boost_xy : bpy.props.FloatVectorProperty(
        name=translate("FOV Boost"),
        description=translate("Boost the frustrum visibility angle of the active camera"),
        subtype="XYZ",
        size=2,
        default=(0,0),
        soft_min=-2,
        soft_max=2, 
        precision=3,
        update=scattering.update_factory.factory("s_visibility_camclip_cam_boost_xy", delay_support=True,),
        )
    s_visibility_camclip_proximity_allow : bpy.props.BoolProperty(
        name=translate("Near Camera Radius"),
        description=translate("Reveal some instances when their origins are near the active-camera"),
        default=False,
        update=scattering.update_factory.factory("s_visibility_camclip_proximity_allow"),
        )
    s_visibility_camclip_proximity_distance : bpy.props.FloatProperty(
        name=translate("Distance"),
        subtype="DISTANCE",
        default=4,
        min=0,
        soft_max=20, 
        update=scattering.update_factory.factory("s_visibility_camclip_proximity_distance", delay_support=True,),
        )

    #Distance 

    s_visibility_camdist_allow: bpy.props.BoolProperty(
        name=translate("Camera Distance Culling"),
        description=translate("Only show instances close to the active-camera"),
        default=False,
        update=scattering.update_factory.factory("s_visibility_camdist_allow"),
        )
    s_visibility_camdist_per_cam_data: bpy.props.BoolProperty(
        name=translate("Per Camera Settings"),
        description=translate("The distances settings are unique to the active camera"),
        default=False,
        update=scattering.update_factory.factory("s_visibility_camdist_per_cam_data"),
        )
    s_visibility_camdist_min : bpy.props.FloatProperty(
        name=translate("Start"),
        description=translate("Starting this distance, we will start a distance culling transition until the end distance"),
        subtype="DISTANCE",
        default=10,
        min=0,
        soft_max=200, 
        update=scattering.update_factory.factory("s_visibility_camdist_min", delay_support=True,),
        )
    s_visibility_camdist_max : bpy.props.FloatProperty(
        name=translate("End"),
        description=translate("After this distance all instances will be culled"),
        subtype="DISTANCE",
        default=40,
        min=0,
        soft_max=200, 
        update=scattering.update_factory.factory("s_visibility_camdist_max", delay_support=True,),
        )
    #remap
    s_visibility_camdist_fallremap_allow : bpy.props.BoolProperty(
        default=False, 
        name=translate("Camera Distance Culling Remap"),
        description=translate("Control the transition falloff by remapping the values with a curve-map graph.\n\n• Please note that this feature assumes there is a transition distance to work with"),
        update=scattering.update_factory.factory("s_visibility_camdist_fallremap_allow",),
        )
    s_visibility_camdist_fallremap_revert : bpy.props.BoolProperty(
        name=translate("Reverse Transition"),
        description=translate("Reverse the transition. This option will in fact remap the values from '0-1' to '1-0'"),
        default=False,
        update=scattering.update_factory.factory("s_visibility_camdist_fallremap_revert",),
        )
    s_visibility_camdist_fallremap_data : bpy.props.StringProperty(
        set=scattering.update_factory.fallremap_setter("s_visibility_cam.fallremap"),
        get=scattering.update_factory.fallremap_getter("s_visibility_cam.fallremap"),
        )

    #Occlusion

    s_visibility_camoccl_allow : bpy.props.BoolProperty(
        name=translate("Camera Occlusion"),
        description=translate("Remove instances unseen by the camera because their visibility is obstructed by the surfaces and/or by given objects.\n\n• Note that evaluating heavy poly objects and/or evaluating a heavy distribution might be computer intensive"),
        default=False,
        update=scattering.update_factory.factory("s_visibility_camoccl_allow"),
        )
    s_visibility_camoccl_threshold : bpy.props.FloatProperty(
        name=translate("Threshold"),
        subtype="DISTANCE",
        default=0.01,
        min=0,
        soft_max=20, 
        update=scattering.update_factory.factory("s_visibility_camoccl_threshold", delay_support=True,),
        )
    s_visibility_camoccl_method : bpy.props.EnumProperty(
        name=translate("Occlusion Method"),
        description=translate("Choose your visibility occlusion method"),
        default="surface_only",
        items=(("surface_only", translate("Surface Only"),        translate("Mask instances whose origins are not visible because they are occluded by your surfaces"), "", 0),
               ("obj_only",     translate("Colliders Only"),      translate("Mask instances whose origins are not visible because they are occluded by meshes of objects within given collection"), "", 1),
               ("both",         translate("Surface & Colliders"), translate("Mask instances whose origins are not visible because they are ether occluded by your surfaces or by meshes of objects within given collection"), "", 2),
              ),
        update=scattering.update_factory.factory("s_visibility_camoccl_method"),
        )
    s_visibility_camoccl_coll_ptr : bpy.props.StringProperty(
        name=translate("Collection Pointer"),
        search=lambda s,c,e: set(col.name for col in bpy.data.collections if (e in col.name)),
        search_options={'SUGGESTION','SORT'},
        update=scattering.update_factory.factory("s_visibility_camoccl_coll_ptr"),
        )

    s_visibility_cam_allow_screen : bpy.props.BoolProperty(default=True,  name=translate("Visibility State. (Define when the feature is active)"), description=translate("This optimization feature will be active only when working on the 3Dviewport, not during rendered view nor the final render"), update=scattering.update_factory.factory_viewport_method_proxy("s_visibility_cam","screen"),) #ui purpose
    s_visibility_cam_allow_shaded : bpy.props.BoolProperty(default=True,  name=translate("Visibility State. (Define when the feature is active)"), description=translate("This optimization feature will be active only when working in the viewport & during rendered-view, not during the final render"), update=scattering.update_factory.factory_viewport_method_proxy("s_visibility_cam","shaded"),) #ui purpose
    s_visibility_cam_allow_render : bpy.props.BoolProperty(default=False, name=translate("Visibility State. (Define when the feature is active)"), description=translate("This optimization feature will be active at all times, including the final render"), update=scattering.update_factory.factory_viewport_method_proxy("s_visibility_cam","render"),) #ui purpose
    s_visibility_cam_viewport_method : bpy.props.EnumProperty( #Internal Purpose
        default="viewport_only",
        items=(("viewport_only","sc+sh","","",1),("except_rendered","sc","","",0),("viewport_and_render","sc+sh+rd","","",2),),
        update=scattering.update_factory.factory("s_visibility_cam_viewport_method"),
        )

    ########## ########## Maximum load

    s_visibility_maxload_allow : bpy.props.BoolProperty( 
        name=translate("Maximum Load"),
        description=translate("Limit the number of instances that can be shown on screen"),
        default=False,
        update=scattering.update_factory.factory("s_visibility_maxload_allow"),
        )
    s_visibility_maxload_cull_method : bpy.props.EnumProperty(
        name=translate("Limitation Method"),
        default="maxload_limit",
        items=( ("maxload_limit",    translate("Limit"),    translate("Limit how many instances are visible on screen. The total amount of instances produced by this scatter-system will never exceed the given threshold."), ),
                ("maxload_shutdown", translate("Shutdown"), translate("If total amount of instances produced by this scatter-system goes beyond given threshold, we will shutdown the visibility of this system entirely"), ),
              ),
        update=scattering.update_factory.factory("s_visibility_maxload_cull_method"),
        )
    s_visibility_maxload_treshold : bpy.props.IntProperty(
        name=translate("Threshold"),
        description=translate("The system will either limit or shut down what's visible, when  the instances count approximately reach above the chosen threshold"),
        default=199_000,
        min=1,
        soft_min=1_000,
        soft_max=9_999_999,
        update=scattering.update_factory.factory("s_visibility_maxload_treshold", delay_support=True,),
        )

    s_visibility_maxload_allow_screen : bpy.props.BoolProperty(default=True,  name=translate("Visibility State. (Define when the feature is active)"), description=translate("This optimization feature will be active only when working on the 3Dviewport, not during rendered view nor the final render"), update=scattering.update_factory.factory_viewport_method_proxy("s_visibility_maxload","screen"),) #ui purpose
    s_visibility_maxload_allow_shaded : bpy.props.BoolProperty(default=True,  name=translate("Visibility State. (Define when the feature is active)"), description=translate("This optimization feature will be active only when working in the viewport & during rendered-view, not during the final render"), update=scattering.update_factory.factory_viewport_method_proxy("s_visibility_maxload","shaded"),) #ui purpose
    s_visibility_maxload_allow_render : bpy.props.BoolProperty(default=False, name=translate("Visibility State. (Define when the feature is active)"), description=translate("This optimization feature will be active at all times, including the final render"), update=scattering.update_factory.factory_viewport_method_proxy("s_visibility_maxload","render"),) #ui purpose
    s_visibility_maxload_viewport_method : bpy.props.EnumProperty( #Internal Purpose
        default="viewport_only",
        items=(("viewport_only","sc+sh","","",1),("except_rendered","sc","","",0),("viewport_and_render","sc+sh+rd","","",2),),
        update=scattering.update_factory.factory("s_visibility_maxload_viewport_method"),
        )

    # 88 88b 88 .dP"Y8 888888    db    88b 88  dP""b8 88 88b 88  dP""b8
    # 88 88Yb88 `Ybo."   88     dPYb   88Yb88 dP   `" 88 88Yb88 dP   `"
    # 88 88 Y88 o.`Y8b   88    dP__Yb  88 Y88 Yb      88 88 Y88 Yb  "88
    # 88 88  Y8 8bodP'   88   dP""""Yb 88  Y8  YboodP 88 88  Y8  YboodP

    ###################### This category of settings keyword is : "s_instances"

    s_instances_locked : bpy.props.BoolProperty(description=translate("Lock/Unlock Settings"),)

    # def get_s_instances_main_features(self, availability_conditions=True,):
    #     return []

    # s_instances_master_allow : bpy.props.BoolProperty( 
    #     name=translate("Master Toggle"),
    #     description=translate("Mute/Unmute all features of this category in one click"),
    #     default=True, 
    #     update=scattering.update_factory.factory("s_instances_master_allow", sync_support=False,),
    #     )

    ########## ##########

    def get_instance_objs(self):
        """get all objects used by this particle instancing method"""
            
        instances = [] 

        if (self.s_instances_method=="ins_collection"):
            if (self.s_instances_coll_ptr):
                for o in self.s_instances_coll_ptr.objects:
                    if (o not in instances):
                        instances.append(o)

        return instances 
    
    def get_instancing_info(self, raw_data=False, loc_data=False, processed_data=False,): 
        """get information about the depsgraph instances for this system
        3 info type available:
        - raw_data: get the raw depsgraph information ( instance.object.original and instance.matrix_world )
        - loc_data: get only the locations of the instances
        - processed_data: get a comprehensive dict with "instance_ name", "location", "rotation_euler (radians)", "scale" as keys
        """
        
        #Note, fastest way to access all these data is via as_pointer(), however, speed does not matter here 
        
        scatter_obj = self.scatter_obj
        if (scatter_obj is None):
            raise Exception("No Scatter Obj Found")

        deps_data = [ ( i.object.original, i.matrix_world.copy() ) for i in bpy.context.evaluated_depsgraph_get().object_instances 
                if ( (i.is_instance) and (i.parent.original==scatter_obj) ) ]

        #return raw depsgraph option
        if (raw_data):
            return deps_data

        #return array of loc option
        elif (loc_data):
            data = []
            
            for i, v in enumerate(deps_data):
                _, m = v
                l, _, _ = m.decompose()
                
                data.append(l)
                continue
            
            return data
        
        #return processed dict option
        elif (processed_data):
            data = {}
            
            for i, v in enumerate(deps_data):
                b, m = v
                l, r, s = m.decompose()
                e = r.to_euler('XYZ', )

                data[str(i)]= {"name":b.name, "location":tuple(l), "rotation_euler":tuple(e[:]), "scale":tuple(s),}
                continue 
            
            return data
        
        raise Exception("Please Choose a named argument") 

    ########## ##########

    s_instances_method : bpy.props.EnumProperty( #maybe for later?
        name=translate("Instance Method"),
        description=translate("Define your instancing method"),
        default= "ins_collection", 
        items= ( ("ins_collection", translate("Collection"), translate("Spawn objects contained in a given collection into the distributed points with a chosen spawn method algorithm"), "OUTLINER_COLLECTION", 0,),
                 ("ins_points", translate("None"), translate("Skip the instancing part, and output the raw points generated by our plugin scatter-engine. Useful if you would like to add your own instancing rules with geometry nodes without interfering with our workflow, to do so, add a new geonode modifier right after our Geo-Scatter Engine modifier on your scatter object). Please note that our display system and random mirror features won't be available."), "PANEL_CLOSE", 1,),
               ),
        update=scattering.update_factory.factory("s_instances_method"),
        ) 
    s_instances_coll_ptr : bpy.props.PointerProperty( #TODO, no longer rely on collection... need more flexible system for surface and collections or else. need a dynamic join geometry ng
        name=translate("Collection Pointer"),
        type=bpy.types.Collection,
        update=scattering.update_factory.factory("s_instances_coll_ptr"),
        )
    ui_instances_list_idx : bpy.props.IntProperty() #for list template
    
    s_instances_pick_method : bpy.props.EnumProperty( #only for ins_collection
        name=translate("Spawn Method"),
        description=translate("Define how your instances will be assigned to the distributed points"),
        default= "pick_random", 
        items= ( ("pick_random", translate("Random"), translate("Randomly assign the instances from the object-list below to the scattered points"), "OBJECT_DATA", 0,),
                 ("pick_rate", translate("Probability"), translate("Assign instances to the generated points based on a defined probability rate per instances"), "MOD_HUE_SATURATION", 1,),
                 ("pick_scale", translate("Scale"), translate("Assign instances based on the generated points scale"), "OBJECT_ORIGIN", 2,),
                 ("pick_color", translate("Color Sampling"), translate("Assign instances to the generated points based on a given color attribute (vertex-color or texture)"), "COLOR", 3,),
                 ("pick_idx", translate("Manual Index"), translate("Assign instances based on the index attribute that can be generated using manual mode index painting brush"), "LINENUMBERS_ON", 4,),
                 ("pick_cluster", translate("Clusters"), translate("Assign instance to the generated points by packing them in clusters"), "CON_OBJECTSOLVER", 5,),
               ),
        update=scattering.update_factory.factory("s_instances_pick_method"),
        )
    #for pick_random & pick_rate
    s_instances_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        description=translate("Change this value to randomize the result.\n\nIn 3D graphics, a seed is a starting value used by a random number generator to produce a sequence of random-looking numbers. These numbers can control things like the position, rotation, or scale of objects in a scene. Using the same seed will always generate the same 'random' result, which helps keep things consistent when needed."),
        update=scattering.update_factory.factory("s_instances_seed", delay_support=True,),
        )
    s_instances_is_random_seed : bpy.props.BoolProperty( 
        name=translate("Randomize Seed"),
        description=translate("Randomize the value of the hereby seed property.\n\n• Note that pressing 'ALT' while clicking on this button will garantee the attribution of an unique seed value of this property for all selected-system(s)"),
        default=False,
        update=scattering.update_factory.factory("s_instances_is_random_seed",),
        )
    #for pick_rate
    codegen_properties_by_idx(scope_ref=__annotations__, name="s_instances_id_XX_rate", nbr=20, items={"default":0,"min":0,"max":100,"subtype":"PERCENTAGE","name":translate("Probability"),"description":translate("Set this object spawn rate, objects above will overshadow those located below in an alphabetically sorted list")}, property_type=bpy.props.IntProperty, delay_support=True,)
    #for pick_scale
    codegen_properties_by_idx(scope_ref=__annotations__, name="s_instances_id_XX_scale_min", nbr=20, items={"default":0,"soft_min":0,"soft_max":3,"name":translate("Scale Range Min"),"description":translate("Assign instance to scattered points fitting the given range, objects above will overshadow those located below in an alphabetically sorted list")}, property_type=bpy.props.FloatProperty, delay_support=True,)
    codegen_properties_by_idx(scope_ref=__annotations__, name="s_instances_id_XX_scale_max", nbr=20, items={"default":0,"soft_min":0,"soft_max":3,"name":translate("Scale Range Max"),"description":translate("Assign instance to scattered points fitting the given range, objects above will overshadow those located below in an alphabetically sorted list")}, property_type=bpy.props.FloatProperty, delay_support=True,)
    s_instances_id_scale_method : bpy.props.EnumProperty(
        name=translate("Scale Method"),
        default= "fixed_scale",
        items= ( ("fixed_scale", translate("Frozen Scale"), translate("Reset all instances scale to 1"),"FREEZE",0),
                 ("dynamic_scale", translate("Dynamic Scale"), translate("Rescale Items dynamically depending on given range"),"LIGHT_DATA",1),
                 ("default_scale", translate("Default Scale"), translate("Leave Scale as it is"),"OBJECT_ORIGIN",2),
               ),
        update=scattering.update_factory.factory("s_instances_id_scale_method"),
        )
    #for pick color
    codegen_properties_by_idx(scope_ref=__annotations__, name="s_instances_id_XX_color", nbr=20, items={"default":(1,0,0),"subtype":"COLOR","min":0,"max":1,"name":translate("Color"),"description":translate("Assign this instance to the corresponding color sampled")}, property_type=bpy.props.FloatVectorProperty, delay_support=True,)
    #for pick_cluster
    s_instances_pick_cluster_projection_method : bpy.props.EnumProperty( #TODO rename this as _space...
        name=translate("Projection Method"),
        default= "local", 
        items= ( ("local", translate("Local"), translate(""), "ORIENTATION_LOCAL",0 ),
                 ("global", translate("Global"), translate(""), "WORLD",1 ),
               ),
        update=scattering.update_factory.factory("s_instances_pick_cluster_projection_method"),
        )
    s_instances_pick_cluster_scale : bpy.props.FloatProperty(
        name=translate("Scale"),
        default=0.3,
        min=0,
        update=scattering.update_factory.factory("s_instances_pick_cluster_scale", delay_support=True,),
        )
    s_instances_pick_cluster_blur : bpy.props.FloatProperty(
        name=translate("Jitter"),
        default=0.5,
        min=0,
        max=3,
        update=scattering.update_factory.factory("s_instances_pick_cluster_blur", delay_support=True,),
        )
    s_instances_pick_clump : bpy.props.BoolProperty(
        default=False, 
        name=translate("Use Clumps as Clusters"),
        description=translate("This option appears if you are using clump distribution method, it will allow you to assign each instance to individual clumps"),
        update=scattering.update_factory.factory("s_instances_pick_clump"),
        )

    s_instances_id_color_tolerence : bpy.props.FloatProperty(
        name=translate("Tolerance"),
        description=translate("Tolerance threshold defines the measure of similarity between two colors before they are considered the same. A tolerance of '0' means that the colors should exactly match with each other"),
        default=0.3,
        min=0,
        soft_max=3,
        update=scattering.update_factory.factory("s_instances_id_color_tolerence", delay_support=True,), 
        )

    s_instances_id_color_sample_method : bpy.props.EnumProperty(
        name=translate("Color Source"),
        default= "vcol", 
        items= ( ("vcol", translate("Vertex Colors"), "", "VPAINT_HLT", 1,),
                 ("text", translate("Texture Data"), "", "NODE_TEXTURE", 2,),
               ),
        update=scattering.update_factory.factory("s_instances_id_color_sample_method"),
        ) 
    s_instances_texture_ptr : bpy.props.StringProperty(
        description="Internal setter property that will update a TEXTURE_NODE node tree from given nodetree name (used for presets and most importantly copy/paste or synchronization) warning name is not consistant, always check in nodetree to get correct name!",
        update=scattering.update_factory.factory("s_instances_texture_ptr",),
        )
    s_instances_vcol_ptr : bpy.props.StringProperty(
        name=translate("Color-Attribute Pointer"),
        description=translate("Search across all your surface(s) for shared color attributes.\nWe will highlight the pointer in red if the attribute is not shared across your surface(s)"),
        search=lambda s,c,e: get_surfs_shared_attrs(system=s, attr_type='vcol', searchname=e,),
        search_options={'SUGGESTION','SORT'},
        update=scattering.update_factory.factory("s_instances_vcol_ptr"),
        )

    # 8888b.  88 .dP"Y8 88""Yb 88        db    Yb  dP
    #  8I  Yb 88 `Ybo." 88__dP 88       dPYb    YbdP
    #  8I  dY 88 o.`Y8b 88"""  88  .o  dP__Yb    8P
    # 8888Y"  88 8bodP' 88     88ood8 dP""""Yb  dP

    ###################### This category of settings keyword is : "s_display"
    ###################### this category is Not supported by Preset

    s_display_locked : bpy.props.BoolProperty(description=translate("Lock/Unlock Settings"),)

    def get_s_display_main_features(self, availability_conditions=True,):
        return ["s_display_allow",]

    s_display_master_allow : bpy.props.BoolProperty( 
        name=translate("Master Toggle"),
        description=translate("Mute/Unmute all features of this category in one click"),
        default=True, 
        update=scattering.update_factory.factory("s_display_master_allow", sync_support=False,),
        )

    ########## ########## Display as

    s_display_allow : bpy.props.BoolProperty(
        name=translate("Display As"),
        description=translate("Display your instances as something else to lower the number of triangles shown in the 3D viewport"),
        default=False,
        update=scattering.update_factory.factory("s_display_allow",),
        )
    s_display_method : bpy.props.EnumProperty(
        name=translate("Display as"),
        description=translate("Display your instances as something else, easier to draw by your GPU"),
        default= "placeholder", 
        items= ( ("bb", translate("Bounding-Box"), translate("Display your instances as solid bounding-boxes"), "CUBE",1 ),
                 ("convexhull", translate("Convex-Hull"), translate("Display your instances as their computed convexhull geometry.\n• Note that the convex-hull is computed in real time and this might be slow to compute"), "MESH_ICOSPHERE",2 ),
                 ("placeholder", translate("Placeholder"), translate("Choose from a set of pre-made lowpoly objects to display your instances as"), "MOD_CLOTH",3 ),
                 ("placeholder_custom", translate("Custom Placeholder"), translate("Display your instances as another object, choose your own custom object"), "MOD_CLOTH",4 ),
                 ("point", translate("Single Point"), translate("Display your instances as a single point"), "LAYER_ACTIVE",5 ),
                 ("cloud", translate("Point-Cloud"), translate("Display your instances as a generated point-cloud"), "OUTLINER_OB_POINTCLOUD",7 ),
               ),
        update=scattering.update_factory.factory("s_display_method"),
        )
    s_display_placeholder_type : bpy.props.EnumProperty(
        name=translate("Placeholder Type"),
        description=translate("Choose from a set of pre-made lowpoly objects to display your instances as"),
        default="SCATTER5_placeholder_pyramidal_square",
        items=( ("SCATTER5_placeholder_extruded_triangle", "Extruded Triangle", "", "TOPATCH:W_placeholder_extruded_triangle", 1),
                ("SCATTER5_placeholder_extruded_square", "Extruded Square", "", "TOPATCH:W_placeholder_extruded_square", 2),
                ("SCATTER5_placeholder_extruded_pentagon", "Extruded Pentagon", "", "TOPATCH:W_placeholder_extruded_pentagon", 3),
                ("SCATTER5_placeholder_extruded_hexagon", "Extruded Hexagon", "", "TOPATCH:W_placeholder_extruded_hexagon", 4),
                ("SCATTER5_placeholder_extruded_decagon", "Extruded Decagon", "", "TOPATCH:W_placeholder_extruded_decagon", 5),
                ("SCATTER5_placeholder_pyramidal_triangle", "Pyramidal Triangle", "", "TOPATCH:W_placeholder_pyramidal_triangle", 6),
                ("SCATTER5_placeholder_pyramidal_square", "Pyramidal Square", "", "TOPATCH:W_placeholder_pyramidal_square", 7),
                ("SCATTER5_placeholder_pyramidal_pentagon", "Pyramidal Pentagon", "", "TOPATCH:W_placeholder_pyramidal_pentagon", 8),
                ("SCATTER5_placeholder_pyramidal_hexagon", "Pyramidal Hexagon", "", "TOPATCH:W_placeholder_pyramidal_hexagon", 9),
                ("SCATTER5_placeholder_pyramidal_decagon", "Pyramidal Decagon", "", "TOPATCH:W_placeholder_pyramidal_decagon", 10),
                ("SCATTER5_placeholder_flat_triangle", "Flat Triangle", "", "TOPATCH:W_placeholder_flat_triangle", 11),
                ("SCATTER5_placeholder_flat_square", "Flat Square", "", "TOPATCH:W_placeholder_flat_square", 12),
                ("SCATTER5_placeholder_flat_pentagon", "Flat Pentagon", "", "TOPATCH:W_placeholder_flat_pentagon", 13),
                ("SCATTER5_placeholder_flat_hexagon", "Flat Hexagon", "", "TOPATCH:W_placeholder_flat_hexagon", 14),
                ("SCATTER5_placeholder_flat_decagon", "Flat Decagon", "", "TOPATCH:W_placeholder_flat_decagon", 15),
                ("SCATTER5_placeholder_card_triangle", "Card Triangle", "", "TOPATCH:W_placeholder_card_triangle", 16),
                ("SCATTER5_placeholder_card_square", "Card Square", "", "TOPATCH:W_placeholder_card_square", 17),
                ("SCATTER5_placeholder_card_pentagon", "Card Pentagon", "", "TOPATCH:W_placeholder_card_pentagon", 18),
                ("SCATTER5_placeholder_hemisphere_01", "Hemisphere 01", "", "TOPATCH:W_placeholder_hemisphere_01", 19),
                ("SCATTER5_placeholder_hemisphere_02", "Hemisphere 02", "", "TOPATCH:W_placeholder_hemisphere_02", 20),
                ("SCATTER5_placeholder_hemisphere_03", "Hemisphere 03", "", "TOPATCH:W_placeholder_hemisphere_03", 21),
                ("SCATTER5_placeholder_hemisphere_04", "Hemisphere 04", "", "TOPATCH:W_placeholder_hemisphere_04", 22),
                ("SCATTER5_placeholder_lowpoly_pine_01", "Lowpoly Pine 01", "", "TOPATCH:W_placeholder_lowpoly_pine_01", 23),
                ("SCATTER5_placeholder_lowpoly_pine_02", "Lowpoly Pine 02", "", "TOPATCH:W_placeholder_lowpoly_pine_02", 24),
                ("SCATTER5_placeholder_lowpoly_pine_03", "Lowpoly Pine 03", "", "TOPATCH:W_placeholder_lowpoly_pine_03", 25),
                ("SCATTER5_placeholder_lowpoly_pine_04", "Lowpoly Pine 04", "", "TOPATCH:W_placeholder_lowpoly_pine_04", 26),
                ("SCATTER5_placeholder_lowpoly_coniferous_01", "Lowpoly Coniferous 01", "", "TOPATCH:W_placeholder_lowpoly_coniferous_01", 27),
                ("SCATTER5_placeholder_lowpoly_coniferous_02", "Lowpoly Coniferous 02", "", "TOPATCH:W_placeholder_lowpoly_coniferous_02", 28),
                ("SCATTER5_placeholder_lowpoly_coniferous_03", "Lowpoly Coniferous 03", "", "TOPATCH:W_placeholder_lowpoly_coniferous_03", 29),
                ("SCATTER5_placeholder_lowpoly_coniferous_04", "Lowpoly Coniferous 04", "", "TOPATCH:W_placeholder_lowpoly_coniferous_04", 30),
                ("SCATTER5_placeholder_lowpoly_coniferous_05", "Lowpoly Coniferous 05", "", "TOPATCH:W_placeholder_lowpoly_coniferous_05", 31),
                ("SCATTER5_placeholder_lowpoly_sapling_01", "Lowpoly Sapling 01", "", "TOPATCH:W_placeholder_lowpoly_sapling_01", 32),
                ("SCATTER5_placeholder_lowpoly_sapling_02", "Lowpoly Sapling 02", "", "TOPATCH:W_placeholder_lowpoly_sapling_02", 33),
                ("SCATTER5_placeholder_lowpoly_cluster_01", "Lowpoly Cluster 01", "", "TOPATCH:W_placeholder_lowpoly_cluster_01", 34),
                ("SCATTER5_placeholder_lowpoly_cluster_02", "Lowpoly Cluster 02", "", "TOPATCH:W_placeholder_lowpoly_cluster_02", 35),
                ("SCATTER5_placeholder_lowpoly_cluster_03", "Lowpoly Cluster 03", "", "TOPATCH:W_placeholder_lowpoly_cluster_03", 36),
                ("SCATTER5_placeholder_lowpoly_cluster_04", "Lowpoly Cluster 04", "", "TOPATCH:W_placeholder_lowpoly_cluster_04", 37),
                ("SCATTER5_placeholder_lowpoly_plant_01", "Lowpoly Plant 01", "", "TOPATCH:W_placeholder_lowpoly_plant_01", 38),
                ("SCATTER5_placeholder_lowpoly_plant_02", "Lowpoly Plant 02", "", "TOPATCH:W_placeholder_lowpoly_plant_02", 39),
                ("SCATTER5_placeholder_lowpoly_plant_03", "Lowpoly Plant 03", "", "TOPATCH:W_placeholder_lowpoly_plant_03", 40),
                ("SCATTER5_placeholder_lowpoly_plant_04", "Lowpoly Plant 04", "", "TOPATCH:W_placeholder_lowpoly_plant_04", 41),
                ("SCATTER5_placeholder_lowpoly_plant_05", "Lowpoly Plant 05", "", "TOPATCH:W_placeholder_lowpoly_plant_05", 42),
                ("SCATTER5_placeholder_lowpoly_plant_06", "Lowpoly Plant 06", "", "TOPATCH:W_placeholder_lowpoly_plant_06", 43),
                ("SCATTER5_placeholder_lowpoly_plant_07", "Lowpoly Plant 07", "", "TOPATCH:W_placeholder_lowpoly_plant_07", 44),
                ("SCATTER5_placeholder_lowpoly_flower_01", "Lowpoly Flower 01", "", "TOPATCH:W_placeholder_lowpoly_flower_01", 45),
                ("SCATTER5_placeholder_lowpoly_flower_02", "Lowpoly Flower 02", "", "TOPATCH:W_placeholder_lowpoly_flower_02", 46),
                ("SCATTER5_placeholder_lowpoly_flower_03", "Lowpoly Flower 03", "", "TOPATCH:W_placeholder_lowpoly_flower_03", 47),
                ("SCATTER5_placeholder_lowpoly_flower_04", "Lowpoly Flower 04", "", "TOPATCH:W_placeholder_lowpoly_flower_04", 48),
                ("SCATTER5_placeholder_helper_empty_stick", "Helper Empty Stick", "", "TOPATCH:W_placeholder_helper_empty_stick", 49),
                ("SCATTER5_placeholder_helper_empty_arrow", "Helper Empty Arrow", "", "TOPATCH:W_placeholder_helper_empty_arrow", 50),
                ("SCATTER5_placeholder_helper_empty_axis", "Helper Empty Axis", "", "TOPATCH:W_placeholder_helper_empty_axis", 51),
                ("SCATTER5_placeholder_helper_colored_axis", "Helper Colored Axis", "", "TOPATCH:W_placeholder_helper_colored_axis", 52),
                ("SCATTER5_placeholder_helper_colored_cube", "Helper Colored Cube", "", "TOPATCH:W_placeholder_helper_colored_cube", 53),
                ("SCATTER5_placeholder_helper_y_arrow", "Helper Tangent Arrow", "", "TOPATCH:W_placeholder_helper_y_arrow", 54),
                ("SCATTER5_placeholder_helper_y_direction", "Helper Tangent Direction", "", "TOPATCH:W_placeholder_helper_y_direction", 55),
                ("SCATTER5_placeholder_helper_z_arrow", "Helper Normal Arrow", "", "TOPATCH:W_placeholder_helper_z_arrow", 56),
               ),
        update=scattering.update_factory.factory("s_display_placeholder_type"),
        )
    s_display_custom_placeholder_ptr : bpy.props.PointerProperty(
        type=bpy.types.Object, 
        update=scattering.update_factory.factory("s_display_custom_placeholder_ptr",),
        )
    s_display_placeholder_scale : bpy.props.FloatVectorProperty(
        name=translate("Scale"),
        subtype="XYZ", 
        default=(0.3,0.3,0.3), 
        update=scattering.update_factory.factory("s_display_placeholder_scale", delay_support=True,),
        )
    s_display_point_radius : bpy.props.FloatProperty(
        name=translate("Scale"),
        default=0.3,
        min=0,
        precision=3,
        update=scattering.update_factory.factory("s_display_point_radius", delay_support=True,),
        )
    s_display_cloud_radius : bpy.props.FloatProperty(
        name=translate("Scale"),
        default=0.1,
        min=0,
        precision=3,
        update=scattering.update_factory.factory("s_display_cloud_radius", delay_support=True,),
        )
    s_display_cloud_density : bpy.props.FloatProperty(
        name=translate("Density"),
        description=translate("The density of the generated point cloud on your objects"),
        default=10,
        min=0,
        update=scattering.update_factory.factory("s_display_cloud_density", delay_support=True,),
        )
    s_display_camdist_allow: bpy.props.BoolProperty(
        name=translate("Reveal Near Instance Camera"),
        description=translate("Disable the display method for instances close to the active camera"),
        default=False,
        update=scattering.update_factory.factory("s_display_camdist_allow"),
        )
    s_display_camdist_distance : bpy.props.FloatProperty(
        name=translate("Distance"),
        description=translate("Any instances located near this distance threshold to the camera will have their full geometry revealed"),
        subtype="DISTANCE",
        default=5,
        min=0,
        soft_max=200, 
        update=scattering.update_factory.factory("s_display_camdist_distance", delay_support=True,),
        )

    s_display_allow_screen : bpy.props.BoolProperty(default=True,  name=translate("Visibility State. (Define when the feature is active)"), description=translate("This optimization feature will be active only when working on the 3Dviewport, not during rendered view nor the final render"), update=scattering.update_factory.factory_viewport_method_proxy("s_display","screen"),) #ui purpose
    s_display_allow_shaded : bpy.props.BoolProperty(default=False, name=translate("Visibility State. (Define when the feature is active)"), description=translate("This optimization feature will be active only when working in the viewport & during rendered-view, not during the final render"), update=scattering.update_factory.factory_viewport_method_proxy("s_display","shaded"),) #ui purpose
    s_display_allow_render : bpy.props.BoolProperty(default=False, name=translate("Visibility State. (Define when the feature is active)"), description=translate("This optimization feature will be active at all times, including the final render"), update=scattering.update_factory.factory_viewport_method_proxy("s_display","render"),) #ui purpose
    s_display_viewport_method : bpy.props.EnumProperty( #Internal Purpose
        default="except_rendered",
        items=(("viewport_only","sc+sh","","",1),("except_rendered","sc","","",0),("viewport_and_render","sc+sh+rd","","",2),),
        update=scattering.update_factory.factory("s_display_viewport_method"),
        )

    # 88""Yb 888888  dP""b8 88 88b 88 88b 88 888888 88""Yb  
    # 88__dP 88__   dP   `" 88 88Yb88 88Yb88 88__   88__dP  
    # 88""Yb 88""   Yb  "88 88 88 Y88 88 Y88 88""   88"Yb   
    # 88oodP 888888  YboodP 88 88  Y8 88  Y8 888888 88  Yb  

    s_beginner_default_scale: bpy.props.FloatProperty(
        name=translate("Default Scale"),
        description=translate("Factor for your instances XYZ scale"),
        soft_max=5,
        soft_min=0,
        default=1,
        update=scattering.update_factory.factory("s_beginner_default_scale", delay_support=True,),
        )
    s_beginner_random_scale : bpy.props.FloatProperty(
        name=translate("Random Scale"),
        description=translate("Randomize the XYZ scale of your instances"),
        default=0, 
        min=0,
        max=1,
        update=scattering.update_factory.factory("s_beginner_random_scale", delay_support=True,),
        )
    s_beginner_random_rot : bpy.props.FloatProperty(
        name=translate("Random Rotation"),
        description=translate("Randomize the XYZ rotation of your instances"),
        default=0, 
        min=0,
        max=1,
        update=scattering.update_factory.factory("s_beginner_random_rot", delay_support=True,),
        )



#   .oooooo.
#  d8P'  `Y8b
# 888           oooo d8b  .ooooo.  oooo  oooo  oo.ooooo.   .oooo.o
# 888           `888""8P d88' `88b `888  `888   888' `88b d88(  "8
# 888     ooooo  888     888   888  888   888   888   888 `"Y88b.
# `88.    .88'   888     888   888  888   888   888   888 o.  )88b
#  `Y8bood8P'   d888b    `Y8bod8P'  `V88V"V8P'  888bod8P' 8""888P'
#                                               888
#                                              o888o

#About group implementation:
#Groups are implemented via python properties update behavior
#on a scatter engine level, the group settings are just regular settings!
#group behavior is just added on an interface and property level


def upd_group_open(self,context):
    """open/close the group system"""

    emitter = self.id_data

    #save selection, as this operation might f up sel
    save_sel = emitter.scatter5.get_psys_selected()[:]

    #if we are opening a collection, we need to add back the psys item before refresh,
    #otherwise interface will consider them as new items and will set them active, we don't what that behavior
    if (self.open):
        all_uuids = [itm.interface_item_psy_uuid for itm in emitter.scatter5.particle_interface_items if (itm.interface_item_type=='SCATTER_SYSTEM')]
        
        for p in emitter.scatter5.particle_systems:
            if ((p.group!="") and (p.group==self.name)):
                if (p.uuid not in all_uuids):
                    itm = emitter.scatter5.particle_interface_items.add()
                    itm.interface_item_type = 'SCATTER_SYSTEM'
                    itm.interface_item_psy_uuid = p.uuid
            continue 

    #refresh interface
    emitter.scatter5.particle_interface_refresh()

    #restore selection
    [setattr(p,"sel",p in save_sel) for p in emitter.scatter5.particle_systems]

    return None


class SCATTER5_PR_particle_groups(bpy.types.PropertyGroup): 
    """bpy.context.object.scatter5.particle_groups, will be stored on emitter"""
    
    #  dP""b8 888888 88b 88 888888 88""Yb 88  dP""b8
    # dP   `" 88__   88Yb88 88__   88__dP 88 dP   `"
    # Yb  "88 88""   88 Y88 88""   88"Yb  88 Yb
    #  YboodP 888888 88  Y8 888888 88  Yb 88  YboodP

    system_type : bpy.props.StringProperty(
        description="Sometimes, we pass a 'system' argument to a function that is either a 'GROUP_SYSTEM' or 'SCATTER_SYSTEM', use this property to recognize one from the other",
        get=lambda s: "GROUP_SYSTEM",
        set=lambda s,v: None
        )
    name : bpy.props.StringProperty(
        default="",
        update=scattering.rename.rename_group,
        )
    name_bis : bpy.props.StringProperty(
        description="important for renaming function, avoid name collision",
        default="",
        )
    description : bpy.props.StringProperty( #passed to interface props SCATTER5_PR_particle_interface_items for lister template 'item_dyntip_propname' option
        default="",
        name=translate("Description"),
        description=translate("Define descriptions for your scatter items, you can check them when hovering your Scatters or Groups in the System-Lister interface"),
        )
    is_linked : bpy.props.BoolProperty(
        get=lambda s: bool(s.id_data.library),
        )

    # 88""Yb .dP"Y8 Yb  dP .dP"Y8 
    # 88__dP `Ybo."  YbdP  `Ybo." 
    # 88"""  o.`Y8b   8P   o.`Y8b 
    # 88     8bodP'  dP    8bodP' 
    
    def get_psy_members(self):
        """list all psys being members given group"""
        
        emitter = self.id_data
        psys = emitter.scatter5.particle_systems
        
        return [p for p in psys if (p.group==self.name)]
    
    def property_run_update(self, prop_name, value,):
        """directly run the property update task function (== changing nodetree) w/o changing any property value, and w/o going in the update fct wrapper/dispatcher"""

        return scattering.update_factory.UpdatesRegistry.run_update(self, prop_name, value,)

    def property_nodetree_refresh(self, prop_name,):
        """refresh this property value"""

        value = getattr(self,prop_name)
        return self.property_run_update(prop_name, value,)

    def properties_nodetree_refresh(self,):
        """for every settings, make sure nodetrees of psys members are updated"""

        props = [k for k in self.bl_rna.properties.keys() if k.startswith("s_")]
        
        #need to ignore properties that doesn't have any update functions in the Registry
        props = [k for k in props if (k in scattering.update_factory.UpdatesRegistry.UpdatesDict.keys())]
        
        for prop_name in props:
            self.property_nodetree_refresh(prop_name)
            continue
        
        return None
    
    # 88   88 88      dP"Yb  88""Yb 888888 88b 88 
    # 88   88 88     dP   Yb 88__dP 88__   88Yb88 
    # Y8   8P 88     Yb   dP 88"""  88""   88 Y88 
    # `YbodP' 88      YbodP  88     888888 88  Y8 
    
    open : bpy.props.BoolProperty(
        default=True,
        options={'LIBRARY_EDITABLE',},
        update=upd_group_open,
        )

    #  dP""b8    db    888888 888888  dP""b8  dP"Yb  88""Yb Yb  dP     88   88 .dP"Y8 888888 8888b.
    # dP   `"   dPYb     88   88__   dP   `" dP   Yb 88__dP  YbdP      88   88 `Ybo." 88__    8I  Yb
    # Yb       dP__Yb    88   88""   Yb  "88 Yb   dP 88"Yb    8P       Y8   8P o.`Y8b 88""    8I  dY
    #  YboodP dP""""Yb   88   888888  YboodP  YbodP  88  Yb  dP        `YbodP' 8bodP' 888888 8888Y"
    
    def is_category_used(self, s_category): #version for group systems == simplified
        """check if the given property category is active"""
        
        #consider mute functionality (master toggle)
        master_allow = getattr(self, f"{s_category}_master_allow")
        if (master_allow==False):
            return False

        try:
            method_name = f"get_{s_category}_main_features"
            method = getattr(self, method_name)
            main_features = method()
        except:
            raise Exception("BUG: categories not set up correctly")

        return any( getattr(self,sett) for sett in main_features )

    # .dP"Y8 88   88 88""Yb 888888    db     dP""b8 888888
    # `Ybo." 88   88 88__dP 88__     dPYb   dP   `" 88__
    # o.`Y8b Y8   8P 88"Yb  88""    dP__Yb  Yb      88""
    # 8bodP' `YbodP' 88  Yb 88     dP""""Yb  YboodP 888888
    
    def get_surfaces(self):
        """return a list of surface object(s)"""
        
        return set( s for p in self.get_psy_members() for s in p.get_surfaces() )
    
    # 8888b.  88 .dP"Y8 888888 88""Yb 88 88""Yb 88   88 888888 88  dP"Yb  88b 88
    #  8I  Yb 88 `Ybo."   88   88__dP 88 88__dP 88   88   88   88 dP   Yb 88Yb88
    #  8I  dY 88 o.`Y8b   88   88"Yb  88 88""Yb Y8   8P   88   88 Yb   dP 88 Y88
    # 8888Y"  88 8bodP'   88   88  Yb 88 88oodP `YbodP'   88   88  YbodP  88  Y8

    # def get_s_gr_distribution_main_features(self, availability_conditions=True,):
    #     return ["s_gr_distribution_density_boost_allow"]

    # s_gr_distribution_master_allow : bpy.props.BoolProperty( 
    #     name=translate("Master Toggle"),
    #     description=translate("Mute/Unmute all features of this category in one click"),
    #     default=True, 
    #     update=scattering.update_factory.factory("s_gr_distribution_master_allow",),
    #     )
    # s_gr_distribution_density_boost_allow : bpy.props.BoolProperty(
    #     description=translate("Boost the density of all scatters contained in this group by a given percentage (if the distribution methods allow it)"),
    #     default=False,
    #     update=scattering.update_factory.factory("s_gr_distribution_density_boost_allow"),
    #     )
    # s_gr_distribution_density_boost_factor : bpy.props.FloatProperty(
    #     name=translate("Factor"),
    #     description=translate("An influence factor of an effect is a value that determines how strong the effect is. A higher factor means more impact, while lower factor means less"),
    #     soft_max=2, soft_min=0, default=1,
    #     update=scattering.update_factory.factory("s_gr_distribution_density_boost_factor", delay_support=True,),
    #     )

    # 8888b.  888888 88b 88 .dP"Y8 88 888888 Yb  dP     8b    d8    db    .dP"Y8 88  dP .dP"Y8
    #  8I  Yb 88__   88Yb88 `Ybo." 88   88    YbdP      88b  d88   dPYb   `Ybo." 88odP  `Ybo."
    #  8I  dY 88""   88 Y88 o.`Y8b 88   88     8P       88YbdP88  dP__Yb  o.`Y8b 88"Yb  o.`Y8b
    # 8888Y"  888888 88  Y8 8bodP' 88   88    dP        88 YY 88 dP""""Yb 8bodP' 88  Yb 8bodP'

    def get_s_gr_mask_main_features(self, availability_conditions=True,):
        return ["s_gr_mask_vg_allow", "s_gr_mask_vcol_allow", "s_gr_mask_bitmap_allow", "s_gr_mask_curve_allow", "s_gr_mask_boolvol_allow", "s_gr_mask_material_allow", "s_gr_mask_upward_allow",]

    s_gr_mask_master_allow : bpy.props.BoolProperty( 
        name=translate("Master Toggle"),
        description=translate("Mute/Unmute all features of this category in one click"),
        default=True, 
        update=scattering.update_factory.factory("s_gr_mask_master_allow",),
        )

    ########## ########## Vgroups

    s_gr_mask_vg_allow : bpy.props.BoolProperty( 
        name=translate("Vertex-Group Mask"),
        description=translate("Mask-out instances depending on their position on the areas affected by a chosen vertex-group attribute.")+"\n\n"+translate("• Please note that 'vertex' attributes rely on your surfaces geometries, the more your surfaces are dense in vertices, the more you will be able to paint with precision"),
        default=False, 
        update=scattering.update_factory.factory("s_gr_mask_vg_allow"),
        )
    s_gr_mask_vg_ptr : bpy.props.StringProperty(
        name=translate("Vertex-Group Pointer"),
        description=translate("Search across all your surface(s) for shared vertex-group.\nWe will highlight the pointer in red if the attribute is not shared across your surface(s)"),
        search=lambda s,c,e: get_surfs_shared_attrs(system=s, attr_type='vg', searchname=e,),
        search_options={'SUGGESTION','SORT'},
        update=scattering.update_factory.factory("s_gr_mask_vg_ptr"),
        )
    s_gr_mask_vg_revert : bpy.props.BoolProperty(
        name=translate("Reverse"),
        description=translate("Reverse the influence of this mask"),
        update=scattering.update_factory.factory("s_gr_mask_vg_revert"),
        )

    ########## ########## VColors
    
    s_gr_mask_vcol_allow : bpy.props.BoolProperty( 
        name=translate("Vertex-Color Mask"), 
        description=translate("Mask-out instances depending on their position on the areas affected by a chosen color-attribute.")+"\n\n"+translate("• Please note that 'vertex' attributes rely on your surfaces geometries, the more your surfaces are dense in vertices, the more you will be able to paint with precision"),
        default=False, 
        update=scattering.update_factory.factory("s_gr_mask_vcol_allow"),
        )
    s_gr_mask_vcol_ptr : bpy.props.StringProperty(
        name=translate("Color-Attribute Pointer"),
        description=translate("Search across all your surface(s) for shared color attributes.\nWe will highlight the pointer in red if the attribute is not shared across your surface(s)"),
        search=lambda s,c,e: get_surfs_shared_attrs(system=s, attr_type='vcol', searchname=e,),
        search_options={'SUGGESTION','SORT'},
        update=scattering.update_factory.factory("s_gr_mask_vcol_ptr"),
        )
    s_gr_mask_vcol_revert : bpy.props.BoolProperty(
        name=translate("Reverse"),
        description=translate("Reverse the influence of this mask"),
        update=scattering.update_factory.factory("s_gr_mask_vcol_revert"),
        )
    s_gr_mask_vcol_color_sample_method : bpy.props.EnumProperty(
        name=translate("Color Sampling"),
        description=translate("Define how to translate the RGBA color values into a mask that will influence your distribution"),
        default="id_greyscale", 
        items=( ("id_greyscale", translate("Greyscale"), translate("Combine all colors into a black and white mask"), "NONE", 0,),
                ("id_red", translate("Red Channel"), translate("Only consider the Red channel as a mask"), "NONE", 1,),
                ("id_green", translate("Green Channel"), translate("Only consider the Green channel as a mask"), "NONE", 2,),
                ("id_blue", translate("Blue Channel"), translate("Only consider the Blue channel as a mask"), "NONE", 3,),
                ("id_black", translate("Pure Black"), translate("Only the areas containing a pure black color will be masked"), "NONE", 4,),
                ("id_white", translate("Pure White"), translate("Only the areas containing a pure white color will be masked"), "NONE", 5,),
                ("id_picker", translate("Color ID"), translate("Only the areas containing a color matching the color of your choice will be masked"), "NONE", 6,),
                ("id_hue", translate("Hue"), translate("Only consider the Hue channel as a mask, when converting the RGB colors to HSV values"), "NONE", 7,),
                ("id_saturation", translate("Saturation"), translate("Only consider the Saturation channel as a maskn when converting the RGB colors to HSV values"), "NONE", 8,),
                ("id_value", translate("Value"), translate("Only consider the Value channel as a mask, when converting the RGB colors to HSV values"), "NONE", 9,),
                ("id_lightness", translate("Lightness"), translate("Only consider the Lightness channel as a mask, when converting the RGB colors to HSL values"), "NONE", 10,),
                ("id_alpha", translate("Alpha Channel"), translate("Only consider the Alpha channel as a mask"), "NONE", 11,),
              ),
        update=scattering.update_factory.factory("s_gr_mask_vcol_color_sample_method"),
        )
    s_gr_mask_vcol_id_color_ptr : bpy.props.FloatVectorProperty(
        name=translate("ID Value"),
        description=translate("The areas containing this color will be considered as a mask"),
        subtype="COLOR",
        min=0,
        max=1,
        default=(1,0,0), 
        update=scattering.update_factory.factory("s_gr_mask_vcol_id_color_ptr", delay_support=True,),
        ) 

    ########## ########## Bitmap 

    s_gr_mask_bitmap_allow : bpy.props.BoolProperty( 
        name=translate("Image Mask"), 
        description=translate("Mask-out instances depending on their position on the areas affected by an image projected on a given UVMap.\n\n• Don't forget to save the image in your blend file! Newly created image data might not be packed in your blendfile by default"),
        default=False, 
        update=scattering.update_factory.factory("s_gr_mask_bitmap_allow"),
        )
    s_gr_mask_bitmap_uv_ptr : bpy.props.StringProperty(
        name=translate("UV-Map Pointer"),
        description=translate("When interacting with the pointer the plugin will search across surface(s) for shared Uvmaps\nThe pointer will be highlighted in a red color if the chosen attribute is missing from one of your surfaces"),
        default="UVMap",
        search=lambda s,c,e: get_surfs_shared_attrs(system=s, attr_type='uv', searchname=e,),
        search_options={'SUGGESTION','SORT'},
        update=scattering.update_factory.factory("s_gr_mask_bitmap_uv_ptr"),
        )
    s_gr_mask_bitmap_ptr : bpy.props.StringProperty(
        name=translate("Image Pointer"),
        search=lambda s,c,e: set(img.name for img in bpy.data.images if (e in img.name)),
        search_options={'SUGGESTION','SORT'},
        update=scattering.update_factory.factory("s_gr_mask_bitmap_ptr"),
        )
    s_gr_mask_bitmap_revert : bpy.props.BoolProperty(
        name=translate("Reverse"),
        description=translate("Reverse the influence of this mask"),
        update=scattering.update_factory.factory("s_gr_mask_bitmap_revert"),
        )
    s_gr_mask_bitmap_color_sample_method : bpy.props.EnumProperty(
        name=translate("Color Sampling"),
        description=translate("Define how to translate the RGBA color values into a mask that will influence your distribution"),
        default="id_greyscale",
        items=( ("id_greyscale", translate("Greyscale"), translate("Combine all colors into a black and white mask"), "NONE", 0,),
                ("id_red", translate("Red Channel"), translate("Only consider the Red channel as a mask"), "NONE", 1,),
                ("id_green", translate("Green Channel"), translate("Only consider the Green channel as a mask"), "NONE", 2,),
                ("id_blue", translate("Blue Channel"), translate("Only consider the Blue channel as a mask"), "NONE", 3,),
                ("id_black", translate("Pure Black"), translate("Only the areas containing a pure black color will be masked"), "NONE", 4,),
                ("id_white", translate("Pure White"), translate("Only the areas containing a pure white color will be masked"), "NONE", 5,),
                ("id_picker", translate("Color ID"), translate("Only the areas containing a color matching the color of your choice will be masked"), "NONE", 6,),
                ("id_hue", translate("Hue"), translate("Only consider the Hue channel as a mask, when converting the RGB colors to HSV values"), "NONE", 7,),
                ("id_saturation", translate("Saturation"), translate("Only consider the Saturation channel as a maskn when converting the RGB colors to HSV values"), "NONE", 8,),
                ("id_value", translate("Value"), translate("Only consider the Value channel as a mask, when converting the RGB colors to HSV values"), "NONE", 9,),
                ("id_lightness", translate("Lightness"), translate("Only consider the Lightness channel as a mask, when converting the RGB colors to HSL values"), "NONE", 10,),
                ("id_alpha", translate("Alpha Channel"), translate("Only consider the Alpha channel as a mask"), "NONE", 11,),
              ),
        update=scattering.update_factory.factory("s_gr_mask_bitmap_color_sample_method"),
        )
    s_gr_mask_bitmap_id_color_ptr : bpy.props.FloatVectorProperty(
        name=translate("ID Value"),
        description=translate("The areas containing this color will be considered as a mask"),
        subtype="COLOR",
        min=0,
        max=1,
        default=(1,0,0), 
        update=scattering.update_factory.factory("s_gr_mask_bitmap_id_color_ptr", delay_support=True,),
        ) 

    ########## ########## Material

    s_gr_mask_material_allow : bpy.props.BoolProperty( 
        name=translate("Material ID Mask"), 
        description=translate("Mask-out instances located upon faces assigned to a chosen material slot"),
        default=False, 
        update=scattering.update_factory.factory("s_gr_mask_material_allow"),
        )
    s_gr_mask_material_ptr : bpy.props.StringProperty(
        name=translate("Material Pointer\nThe faces assigned to chosen material slot will be used as a culling mask"),
        description=translate("Search across all your surface(s) for shared Materials\nWe will highlight the pointer in red if the attribute is not shared across your surface(s)"),
        search=lambda s,c,e: get_surfs_shared_attrs(system=s, attr_type='mat', searchname=e,),
        search_options={'SUGGESTION','SORT'},
        update=scattering.update_factory.factory("s_gr_mask_material_ptr"),
        )
    s_gr_mask_material_revert : bpy.props.BoolProperty(
        name=translate("Reverse"),
        description=translate("Reverse the influence of this mask"),
        update=scattering.update_factory.factory("s_gr_mask_material_revert"),
        )
    
    ########## ########## Curves

    s_gr_mask_curve_allow : bpy.props.BoolProperty( 
        name=translate("Bezier-Area Mask"), 
        description=translate("Mask-out instances located under the inner-area of a closed bezier-curve.\n\n• Internally, the points will be projected upwards and culled if making contact with the inner area of the chosen bezier curve object. Please make sure that your bezier splines are set to 'Cyclic U' in the 'Object>Curve Data' properties panel"),
        default=False, 
        update=scattering.update_factory.factory("s_gr_mask_curve_allow"),
        )
    s_gr_mask_curve_ptr : bpy.props.PointerProperty(
        name=translate("Bezier-Curve Pointer"),
        type=bpy.types.Object, 
        poll=lambda s,o: o.type=="CURVE",
        update=scattering.update_factory.factory("s_gr_mask_curve_ptr"),
        )
    s_gr_mask_curve_revert : bpy.props.BoolProperty(
        name=translate("Reverse"),
        description=translate("Reverse the influence of this mask"),
        update=scattering.update_factory.factory("s_gr_mask_curve_revert"),
        )

    ########## ########## Boolean Volume

    s_gr_mask_boolvol_allow : bpy.props.BoolProperty( 
        name=translate("Boolean Mask"), 
        description=translate("Mask-out instances located inside the volume of the objects contained in the chosen collection"),
        default=False,
        update=scattering.update_factory.factory("s_gr_mask_boolvol_allow"),
        )
    s_gr_mask_boolvol_coll_ptr : bpy.props.StringProperty(
        name=translate("Collection Pointer"),
        search=lambda s,c,e: set(col.name for col in bpy.data.collections if (e in col.name)),
        search_options={'SUGGESTION','SORT'},
        update=scattering.update_factory.factory("s_gr_mask_boolvol_coll_ptr"),
        )
    s_gr_mask_boolvol_revert : bpy.props.BoolProperty(
        name=translate("Reverse"),
        description=translate("Reverse the influence of this mask"),
        update=scattering.update_factory.factory("s_gr_mask_boolvol_revert"),
        )

    ########## ########## Upward Obstruction

    s_gr_mask_upward_allow : bpy.props.BoolProperty( 
        name=translate("Upward-Obstruction Mask"), 
        description=translate("Mask-out instances located under the objects contained in the chosen collection"),
        default=False, 
        update=scattering.update_factory.factory("s_gr_mask_upward_allow"),
        )
    s_gr_mask_upward_coll_ptr : bpy.props.StringProperty(
        name=translate("Collection Pointer"),
        search=lambda s,c,e: set(col.name for col in bpy.data.collections if (e in col.name)),
        search_options={'SUGGESTION','SORT'},
        update=scattering.update_factory.factory("s_gr_mask_upward_coll_ptr"),
        )
    s_gr_mask_upward_revert : bpy.props.BoolProperty(
        name=translate("Reverse"),
        description=translate("Reverse the influence of this mask"),
        update=scattering.update_factory.factory("s_gr_mask_upward_revert"),
        )
    
    # .dP"Y8  dP""b8    db    88     888888
    # `Ybo." dP   `"   dPYb   88     88__
    # o.`Y8b Yb       dP__Yb  88  .o 88""
    # 8bodP'  YboodP dP""""Yb 88ood8 888888

    def get_s_gr_scale_main_features(self, availability_conditions=True,):
        return ["s_gr_scale_boost_allow"]

    s_gr_scale_master_allow : bpy.props.BoolProperty( 
        name=translate("Master Toggle"),
        description=translate("Mute/Unmute all features of this category in one click"),
        default=True, 
        update=scattering.update_factory.factory("s_gr_scale_master_allow"),
        )
    s_gr_scale_boost_allow : bpy.props.BoolProperty(
        name=translate("Scale Boost"),
        description=translate("Boost the scale attribute of all scatters contained in this group by a given percentage"),
        default=False,
        update=scattering.update_factory.factory("s_gr_scale_boost_allow"),
        )
    s_gr_scale_boost_value : bpy.props.FloatVectorProperty(
        name=translate("Factor"),
        description=translate("An influence factor of an effect is a value that determines how strong the effect is. A higher factor means more impact, while lower factor means less"),
        subtype="XYZ", 
        default=(1,1,1), 
        soft_min=0,
        soft_max=5,
        update=scattering.update_factory.factory("s_gr_scale_boost_value", delay_support=True,),
        )
    s_gr_scale_boost_multiplier : bpy.props.FloatProperty(
        name=translate("Factor"),
        description=translate("An influence factor of an effect is a value that determines how strong the effect is. A higher factor means more impact, while lower factor means less"),
        soft_max=5,
        soft_min=0,
        default=1,
        update=scattering.update_factory.factory("s_gr_scale_boost_multiplier", delay_support=True,),
        )

    # 88""Yb    db    888888 888888 888888 88""Yb 88b 88 .dP"Y8
    # 88__dP   dPYb     88     88   88__   88__dP 88Yb88 `Ybo."
    # 88"""   dP__Yb    88     88   88""   88"Yb  88 Y88 o.`Y8b
    # 88     dP""""Yb   88     88   888888 88  Yb 88  Y8 8bodP'

    def get_s_gr_pattern_main_features(self, availability_conditions=True,):
        return ["s_gr_pattern1_allow"]

    s_gr_pattern_master_allow : bpy.props.BoolProperty( 
        name=translate("Master Toggle"),
        description=translate("Mute/Unmute all features of this category in one click"),
        default=True, 
        update=scattering.update_factory.factory("s_gr_pattern_master_allow"),
        )

    s_gr_pattern1_allow : bpy.props.BoolProperty(
        name=translate("Enable Texture Slot"),
        description=translate("Influence your distribution density and your instances scale and with the help of a scatter-texture datablock"),
        default=False,
        update=scattering.update_factory.factory("s_gr_pattern1_allow"),
        )
    s_gr_pattern1_texture_ptr : bpy.props.StringProperty(
        description="Internal setter property that will update a TEXTURE_NODE node tree from given nodetree name (used for presets and most importantly copy/paste or synchronization) warning name is not consistant, always check in nodetree to get correct name!",
        update=scattering.update_factory.factory("s_gr_pattern1_texture_ptr"),
        )
    s_gr_pattern1_color_sample_method : bpy.props.EnumProperty(
        name=translate("Color Sampling"),
        description=translate("Define how to translate the RGBA color values into a mask that will influence your distribution"),
        default="id_greyscale", 
        items=( ("id_greyscale", translate("Greyscale"), translate("Combine all colors into a black and white mask"), "NONE", 0,),
                ("id_red", translate("Red Channel"), translate("Only consider the Red channel as a mask"), "NONE", 1,),
                ("id_green", translate("Green Channel"), translate("Only consider the Green channel as a mask"), "NONE", 2,),
                ("id_blue", translate("Blue Channel"), translate("Only consider the Blue channel as a mask"), "NONE", 3,),
                ("id_black", translate("Pure Black"), translate("Only the areas containing a pure black color will be masked"), "NONE", 4,),
                ("id_white", translate("Pure White"), translate("Only the areas containing a pure white color will be masked"), "NONE", 5,),
                ("id_picker", translate("Color ID"), translate("Only the areas containing a color matching the color of your choice will be masked"), "NONE", 6,),
                ("id_hue", translate("Hue"), translate("Only consider the Hue channel as a mask, when converting the RGB colors to HSV values"), "NONE", 7,),
                ("id_saturation", translate("Saturation"), translate("Only consider the Saturation channel as a maskn when converting the RGB colors to HSV values"), "NONE", 8,),
                ("id_value", translate("Value"), translate("Only consider the Value channel as a mask, when converting the RGB colors to HSV values"), "NONE", 9,),
                ("id_lightness", translate("Lightness"), translate("Only consider the Lightness channel as a mask, when converting the RGB colors to HSL values"), "NONE", 10,),
                ("id_alpha", translate("Alpha Channel"), translate("Only consider the Alpha channel as a mask"), "NONE", 11,),
               ),
        update=scattering.update_factory.factory("s_gr_pattern1_color_sample_method"),
        )
    s_gr_pattern1_id_color_ptr : bpy.props.FloatVectorProperty(
        name=translate("ID Value"),
        description=translate("The areas containing this color will be considered as a mask"),
        subtype="COLOR",
        min=0,
        max=1,
        default=(1,0,0),
        update=scattering.update_factory.factory("s_gr_pattern1_id_color_ptr", delay_support=True,),
        )
    s_gr_pattern1_id_color_tolerence : bpy.props.FloatProperty(
        name=translate("Tolerance"),
        description=translate("Tolerance threshold defines the measure of similarity between two colors before they are considered the same. A tolerance of '0' means that the colors should exactly match with each other"),
        default=0.15, 
        soft_min=0, 
        soft_max=1,
        update=scattering.update_factory.factory("s_gr_pattern1_id_color_tolerence", delay_support=True,),
        )
    #Feature Influence
    s_gr_pattern1_dist_infl_allow : bpy.props.BoolProperty(
        name=translate("Enable Influence"), 
        default=True,
        update=scattering.update_factory.factory("s_gr_pattern1_dist_infl_allow"),
        )
    s_gr_pattern1_dist_influence : bpy.props.FloatProperty(
        name=translate("Density"),
        description=translate("Influence the density of your distribution.")+"\n"+translate("Changing this slider will adjust the intensity of the influence"),
        default=100,
        subtype="PERCENTAGE", 
        min=0, 
        max=100, 
        precision=1,
        update=scattering.update_factory.factory("s_gr_pattern1_dist_influence", delay_support=True,),
        )
    s_gr_pattern1_dist_revert : bpy.props.BoolProperty(
        name=translate("Reverse Influence"),
        update=scattering.update_factory.factory("s_gr_pattern1_dist_revert"), 
        )
    s_gr_pattern1_scale_infl_allow : bpy.props.BoolProperty(
        name=translate("Enable Influence"), 
        default=True,
        update=scattering.update_factory.factory("s_gr_pattern1_scale_infl_allow"),
        )
    s_gr_pattern1_scale_influence : bpy.props.FloatProperty(
        name=translate("Scale"),
        description=translate("Influence the scale of your instances.")+"\n"+translate("Changing this slider will adjust the intensity of the influence"),
        default=70, 
        subtype="PERCENTAGE", 
        min=0, 
        max=100, 
        precision=1, 
        update=scattering.update_factory.factory("s_gr_pattern1_scale_influence", delay_support=True,),
        )
    s_gr_pattern1_scale_revert : bpy.props.BoolProperty(
        name=translate("Reverse Influence"), 
        update=scattering.update_factory.factory("s_gr_pattern1_scale_revert"),
        )