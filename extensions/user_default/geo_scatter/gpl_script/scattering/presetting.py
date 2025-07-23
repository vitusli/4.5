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
# ooooooooo.                                             .       .    o8o
# `888   `Y88.                                         .o8     .o8    `"'
#  888   .d88' oooo d8b  .ooooo.   .oooo.o  .ooooo.  .o888oo .o888oo oooo  ooo. .oo.    .oooooooo
#  888ooo88P'  `888""8P d88' `88b d88(  "8 d88' `88b   888     888   `888  `888P"Y88b  888' `88b
#  888          888     888ooo888 `"Y88b.  888ooo888   888     888    888   888   888  888   888
#  888          888     888    .o o.  )88b 888    .o   888 .   888 .  888   888   888  `88bod8P'
# o888o        d888b    `Y8bod8P' 8""888P' `Y8bod8P'   "888"   "888" o888o o888o o888o `8oooooo.
#                                                                                      d"     YD
#                                                                                      "Y88888P'
#####################################################################################################


import bpy

import os
import pathlib

from .. resources.icons import cust_icon
from .. translations import translate
from .. resources import directories

from .. utils.extra_utils import dprint
from .. utils.str_utils import legal, is_illegal_string, word_wrap
from .. utils.import_utils import serialization 
from .. utils.event_utils import get_event
from .. utils.path_utils import dict_to_json, json_to_dict
from .. utils.override_utils import attributes_override
from .. utils.math_utils import ensure_rgba_colors

from .. ui import ui_templates


# oooooooooo.    o8o                .            .                   .oooooo..o               .
# `888'   `Y8b   `"'              .o8          .o8                  d8P'    `Y8             .o8
#  888      888 oooo   .ooooo.  .o888oo      .o888oo  .ooooo.       Y88bo.       .ooooo.  .o888oo
#  888      888 `888  d88' `"Y8   888          888   d88' `88b       `"Y8888o.  d88' `88b   888
#  888      888  888  888         888          888   888   888           `"Y88b 888ooo888   888
#  888     d88'  888  888   .o8   888 .        888 . 888   888      oo     .d8P 888    .o   888 .
# o888bood8P'   o888o `Y8bod8P'   "888"        "888" `Y8bod8P'      8""88888P'  `Y8bod8P'   "888"


def dict_to_settings( d, psy,
    #filter the settings by category, by default we never save some settings in preset file, however this function is used universally in this plugin
    s_filter={
        "s_color":False,
        "s_surface":False, 
        "s_distribution":True,
        "s_mask":False, 
        "s_rot":True,
        "s_scale":True,
        "s_pattern":True,
        "s_push":True,
        "s_abiotic":True,
        "s_proximity":False,
        "s_ecosystem":True,
        "s_wind":True,
        "s_visibility":False, 
        "s_instances":True,
        "s_display":False, 
        },
    ):
    """ dict -> settings """

    if (psy.scatter_obj is None):
        raise Exception(f"ERROR: dict_to_settings(): Scatter system '{psy.name}' doesn't have a scatter_obj")
    if (not psy.get_scatter_mod(strict=True, raise_exception=True)):
        raise Exception(f"ERROR: dict_to_settings(): Scatter system '{psy.name}' doesn't have a engine modifier")
    
    scat_scene = bpy.context.scene.scatter5 
    emitter    = psy.id_data
    keys       = d.keys()

    def settpsy_check(prop_name, return_value=False, dict_override=None):
        """set attr, but check if attr in our dictornary of properties first, by default will return if attr was found, use return_value if you'd like to check and if the prop was a boolean and true"""

        dic = d
        if (dict_override):
            dic = dict_override

        if (prop_name in dic.keys()):

            if (getattr(psy, prop_name,)!=dic[prop_name]):
                setattr(psy, prop_name, dic[prop_name],)

            if return_value:
                return dic[prop_name]

            return True 

        return False

    def texture_ptr_to_settings(category_str=""):
        """helper funciton for scatter ng texure type, used a bit everywhere below"""

        #get the correct name of our texture ptr ng
        ng_name = d[f"{category_str}_texture_ptr"]
        if (not ng_name.startswith(".TEXTURE ")):
            ng_name = f".TEXTURE {ng_name}"

        #try to get the texture
        ng = bpy.data.node_groups.get(ng_name)

        #create a new ng if none found, or create a copy ng
        if (ng is None) or (d[f"{category_str}_texture_is_unique"]): 
            if (f"{category_str}_texture_dict" in d.keys()):
                node = psy.get_scatter_node(category_str, strict=True, raise_exception=False,)
                if (node):
                    ng = node.node_tree.nodes["texture"].node_tree.copy()
                    ng.scatter5.texture.user_name = ng_name.replace(".TEXTURE ","")
                else:
                    print(f"REPORT: texture_ptr_to_settings(): Couldn't find '{category_str}' node")

        #then retry 
        if (ng):
                    
            #support legacy textures? toi do so need to convert from legacy to new
            if (f"{category_str}_texture_data" in keys):  
                  ng.scatter5.texture.apply_legacy_texture_dict(d[f"{category_str}_texture_dict"],)
            else: ng.scatter5.texture.apply_texture_dict(d[f"{category_str}_texture_dict"],)

            setattr( psy, f"{category_str}_texture_ptr", ng.name)

        return None

    def u_mask_to_settings(category_str="",):
        """helper function to assign universal mask properties stored in dict"""

        if (f"{category_str}_mask_dict" not in d.keys()):
            setattr(psy, f"{category_str}_mask_allow", False,)
            return None 

        mdi = d[f"{category_str}_mask_dict"]
        
        #allow didn't used to exist in previous settings, set it true by default
        if (f"{category_str}_mask_allow" not in mdi):
            mdi[f"{category_str}_mask_allow"] = True 

        settpsy_check(f"{category_str}_mask_allow", dict_override=mdi)
        
        settpsy_check(f"{category_str}_mask_method", dict_override=mdi)
        method = mdi[f"{category_str}_mask_method"]
        
        match method:
            case 'mask_vg':
                settpsy_check(f"{category_str}_mask_ptr", dict_override=mdi)
                settpsy_check(f"{category_str}_mask_reverse", dict_override=mdi)
            case 'mask_vcol':
                settpsy_check(f"{category_str}_mask_ptr", dict_override=mdi)
                settpsy_check(f"{category_str}_mask_color_sample_method", dict_override=mdi)
                settpsy_check(f"{category_str}_mask_id_color_ptr", dict_override=mdi)
                settpsy_check(f"{category_str}_mask_reverse", dict_override=mdi)
            case 'mask_bitmap':
                settpsy_check(f"{category_str}_mask_bitmap_ptr", dict_override=mdi)
                settpsy_check(f"{category_str}_mask_bitmap_uv_ptr", dict_override=mdi)
                settpsy_check(f"{category_str}_mask_color_sample_method", dict_override=mdi)
                settpsy_check(f"{category_str}_mask_id_color_ptr", dict_override=mdi)
                settpsy_check(f"{category_str}_mask_reverse", dict_override=mdi)
            case 'mask_noise':
                settpsy_check(f"{category_str}_mask_noise_space", dict_override=mdi)
                settpsy_check(f"{category_str}_mask_noise_scale", dict_override=mdi)
                settpsy_check(f"{category_str}_mask_noise_seed", dict_override=mdi)
                settpsy_check(f"{category_str}_mask_noise_is_random_seed", dict_override=mdi)
                settpsy_check(f"{category_str}_mask_noise_brightness", dict_override=mdi)
                settpsy_check(f"{category_str}_mask_noise_contrast", dict_override=mdi)

        return None

    # #performance hide check
    # with attributes_override([psy,"hide_viewport",False]):
        
    #hide optimization
    attributes_args = [ [psy.scatter_obj,"hide_viewport",True] , [psy.get_scatter_mod(strict=True,raise_exception=True),"show_viewport",False] ]
    with attributes_override(*attributes_args):
        
        #ignore any properties update behavior, such as update delay or hotkeys
        with scat_scene.factory_update_pause(event=True, delay=True, sync=False):

            #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> COLOR

            if ( s_filter.get("s_color") ):
                    
                settpsy_check("s_color")

            #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> SURFACE

            if ( s_filter.get("s_surface") and not psy.is_locked("s_surface") ):
                    
                if ("s_surface_method" in d):
                    settpsy_check("s_surface_method")
                    
                    if (d["s_surface_method"]=="collection"):
                        settpsy_check("s_surface_collection")

                    elif (d["s_surface_method"]=="object"):
                        if ("s_surface_object" in d):
                            psy.s_surface_object = bpy.data.objects.get(d["s_surface_object"])
            
            #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> DISTRIBUTION

            if ( s_filter.get("s_distribution") and not psy.is_locked("s_distribution") ): 

                if settpsy_check("s_distribution_method"):
                    
                    match d["s_distribution_method"]:
                        
                        case 'random':  #Random Dist 

                            settpsy_check("s_distribution_space")    

                            is_in_dic = settpsy_check("s_distribution_is_count_method")
                            if (is_in_dic and d["s_distribution_is_count_method"]=="count"):
                                settpsy_check("s_distribution_count")
                            else: settpsy_check("s_distribution_density")

                            settpsy_check("s_distribution_seed")
                            settpsy_check("s_distribution_is_random_seed")

                            if settpsy_check("s_distribution_limit_distance_allow", return_value=True): 
                                settpsy_check("s_distribution_limit_distance")

                        case 'random_stable': #Stable Dist

                            is_in_dic = settpsy_check("s_distribution_stable_is_count_method")
                            if (is_in_dic and d["s_distribution_stable_is_count_method"]=="count"):
                                settpsy_check("s_distribution_stable_count")
                            else: settpsy_check("s_distribution_stable_density")

                            settpsy_check("s_distribution_stable_seed")
                            settpsy_check("s_distribution_stable_is_random_seed")

                            if settpsy_check("s_distribution_stable_limit_distance_allow", return_value=True): 
                                settpsy_check("s_distribution_stable_limit_distance")

                        case 'clumping': #Clump Dist 

                            settpsy_check("s_distribution_clump_space")    

                            settpsy_check("s_distribution_clump_density")
                            settpsy_check("s_distribution_clump_max_distance")
                            settpsy_check("s_distribution_clump_random_factor")
                            settpsy_check("s_distribution_clump_falloff")
                            settpsy_check("s_distribution_clump_seed")
                            settpsy_check("s_distribution_clump_is_random_seed")

                            if settpsy_check("s_distribution_clump_limit_distance_allow", return_value=True):
                                settpsy_check("s_distribution_clump_limit_distance")

                            if settpsy_check("s_distribution_clump_fallremap_allow", return_value=True):
                                settpsy_check("s_distribution_clump_fallremap_data")
                                settpsy_check("s_distribution_clump_fallremap_revert")
                                settpsy_check("s_distribution_clump_fallnoisy_strength")
                                settpsy_check("s_distribution_clump_fallnoisy_space") 
                                settpsy_check("s_distribution_clump_fallnoisy_scale") 
                                settpsy_check("s_distribution_clump_fallnoisy_seed")
                                settpsy_check("s_distribution_clump_fallnoisy_is_random_seed")

                            settpsy_check("s_distribution_clump_children_density")
                            settpsy_check("s_distribution_clump_children_seed")
                            settpsy_check("s_distribution_clump_children_is_random_seed")

                            if settpsy_check("s_distribution_clump_children_limit_distance_allow", return_value=True):
                                settpsy_check("s_distribution_clump_children_limit_distance")

                        case 'verts': #Verts Dist
                            
                            settpsy_check("s_distribution_vfe_space")
                            
                        case 'faces': #Faces Dist 
                            
                            settpsy_check("s_distribution_vfe_space")
                            
                        case 'edges': #Edges Dist
                            
                            settpsy_check("s_distribution_vfe_space")
                            settpsy_check("s_distribution_edges_selection_method")
                            settpsy_check("s_distribution_edges_position_method")

                        case 'volume': #Volume Dist
                            
                            settpsy_check("s_distribution_volume_space")
                            settpsy_check("s_distribution_volume_voxelsize")
                            settpsy_check("s_distribution_volume_method")

                            if (d["s_distribution_volume_method"]=="random"):
                                is_in_dic = settpsy_check("s_distribution_volume_is_count_method")
                                if (is_in_dic and d["s_distribution_volume_is_count_method"]=="count"):
                                    settpsy_check("s_distribution_volume_density")
                                else: settpsy_check("s_distribution_volume_count")

                                settpsy_check("s_distribution_volume_seed")
                                settpsy_check("s_distribution_volume_is_random_seed")

                                if settpsy_check("s_distribution_volume_limit_distance_allow", return_value=True): 
                                    settpsy_check("s_distribution_volume_limit_distance")
                                
                            elif (d["s_distribution_volume_method"]=="grid"):
                                settpsy_check("s_distribution_volume_grid_spacing")
                                                    
                        case 'projbezarea': #Project Bezier Area
                            
                            if ("s_distribution_projbezarea_curve_ptr" in keys):
                                psy.s_distribution_projbezarea_curve_ptr = bpy.data.objects.get(d["s_distribution_projbezarea_curve_ptr"])
                            
                            settpsy_check("s_distribution_projbezarea_space")
                            
                            settpsy_check("s_distribution_projbezarea_density")
                            settpsy_check("s_distribution_projbezarea_seed")
                            settpsy_check("s_distribution_projbezarea_is_random_seed")

                            if settpsy_check("s_distribution_projbezarea_limit_distance_allow", return_value=True): 
                                settpsy_check("s_distribution_projbezarea_limit_distance")
                            
                            if settpsy_check("s_distribution_projbezarea_projenabled", return_value=True): 
                                settpsy_check("s_distribution_projbezarea_projlength")
                                settpsy_check("s_distribution_projbezarea_projaxis")
                                                        
                        case 'projbezline': #Project Bezier Line
                            
                            if ("s_distribution_projbezline_curve_ptr" in keys):
                                psy.s_distribution_projbezline_curve_ptr = bpy.data.objects.get(d["s_distribution_projbezline_curve_ptr"])

                            settpsy_check("s_distribution_projbezline_space")
                            settpsy_check("s_distribution_projbezline_method")
                            settpsy_check("s_distribution_projbezline_normal_method")

                            is_in_dic = settpsy_check("s_distribution_projbezline_is_count_method")
                            if (is_in_dic and d["s_distribution_projbezline_is_count_method"]=="count"):
                                settpsy_check("s_distribution_projbezline_count")
                            else:
                                if (d["s_distribution_projbezline_method"]=="patharea"):
                                    settpsy_check("s_distribution_projbezline_patharea_density")
                                elif (d["s_distribution_projbezline_method"]=="onspline"):
                                    settpsy_check("s_distribution_projbezline_onspline_density")
                            
                            if (d["s_distribution_projbezline_method"]=="onspline"):
                                if settpsy_check("s_distribution_projbezline_randoff_allow", return_value=True): 
                                    settpsy_check("s_distribution_projbezline_randoff_dist")
                                    settpsy_check("s_distribution_projbezline_randoff_seed")
                                    settpsy_check("s_distribution_projbezline_randoff_is_random_seed")
                                
                                if settpsy_check("s_distribution_projbezline_creatrow_allow", return_value=True): 
                                    settpsy_check("s_distribution_projbezline_creatrow_rows")
                                    settpsy_check("s_distribution_projbezline_creatrow_dist")
                                    settpsy_check("s_distribution_projbezline_creatrow_shift")
                                    
                                if settpsy_check("s_distribution_projbezline_spread_allow", return_value=True): 
                                    settpsy_check("s_distribution_projbezline_spread_method")
                                    settpsy_check("s_distribution_projbezline_spread_dir")
                                    # settpsy_check("s_distribution_projbezline_spread_offset")
                                    settpsy_check("s_distribution_projbezline_spread_falloff")
                                    settpsy_check("s_distribution_projbezline_spread_seed")
                                    settpsy_check("s_distribution_projbezline_spread_is_random_seed")
                                
                            elif (d["s_distribution_projbezline_method"]=="patharea"):
                                settpsy_check("s_distribution_projbezline_patharea_width")
                                settpsy_check("s_distribution_projbezline_patharea_falloff")
                                settpsy_check("s_distribution_projbezline_patharea_seed")
                                settpsy_check("s_distribution_projbezline_patharea_is_random_seed")
                                
                                if settpsy_check("s_distribution_projbezline_patharea_radiusinfl_allow", return_value=True):
                                    settpsy_check("s_distribution_projbezline_patharea_radiusinfl_factor")
                                    
                                if settpsy_check("s_distribution_projbezline_fallremap_allow", return_value=True):
                                    settpsy_check("s_distribution_projbezline_fallremap_data")
                                    settpsy_check("s_distribution_projbezline_fallremap_revert")
                                    settpsy_check("s_distribution_projbezline_fallnoisy_strength")
                                    settpsy_check("s_distribution_projbezline_fallnoisy_space") 
                                    settpsy_check("s_distribution_projbezline_fallnoisy_scale") 
                                    settpsy_check("s_distribution_projbezline_fallnoisy_seed")
                                    settpsy_check("s_distribution_projbezline_fallnoisy_is_random_seed")
                                
                            if settpsy_check("s_distribution_projbezline_limit_distance_allow", return_value=True): 
                                settpsy_check("s_distribution_projbezline_limit_distance")
                                
                            if settpsy_check("s_distribution_projbezline_projenabled", return_value=True): 
                                settpsy_check("s_distribution_projbezline_projlength")
                                settpsy_check("s_distribution_projbezline_projaxis")
                        
                        case 'projempties': #Project Empties
                            
                            settpsy_check("s_distribution_projempties_coll_ptr")
                            settpsy_check("s_distribution_projempties_empty_only")

                            if settpsy_check("s_distribution_projempties_projenabled", return_value=True): 
                                settpsy_check("s_distribution_projempties_projlength")
                                settpsy_check("s_distribution_projempties_projaxis")                        

            #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> MASK

            if ( s_filter.get("s_mask") and not psy.is_locked("s_mask") ):

                settpsy_check("s_mask_master_allow")

                #Vgroups 

                if settpsy_check("s_mask_vg_allow", return_value=True):
                    settpsy_check("s_mask_vg_ptr")
                    settpsy_check("s_mask_vg_revert")

                #VColors 

                if settpsy_check("s_mask_vcol_allow", return_value=True):
                    settpsy_check("s_mask_vcol_ptr")
                    settpsy_check("s_mask_vcol_revert")
                    settpsy_check("s_mask_vcol_color_sample_method")
                    settpsy_check("s_mask_vcol_id_color_ptr")

                #Bitmap 

                if settpsy_check("s_mask_bitmap_allow", return_value=True):
                    settpsy_check("s_mask_bitmap_uv_ptr")
                    settpsy_check("s_mask_bitmap_ptr")
                    settpsy_check("s_mask_bitmap_revert")
                    settpsy_check("s_mask_bitmap_color_sample_method")
                    settpsy_check("s_mask_bitmap_id_color_ptr")

                #Curves

                if settpsy_check("s_mask_curve_allow", return_value=True):

                    if ("s_mask_curve_ptr" in keys):
                        psy.s_mask_curve_ptr = bpy.data.objects.get(d["s_mask_curve_ptr"])

                    settpsy_check("s_mask_curve_revert")

                #Boolean

                if settpsy_check("s_mask_boolvol_allow", return_value=True):
                    settpsy_check("s_mask_boolvol_coll_ptr")
                    settpsy_check("s_mask_boolvol_revert")

                #Material

                if settpsy_check("s_mask_material_allow", return_value=True):
                    settpsy_check("s_mask_material_ptr")
                    settpsy_check("s_mask_material_revert")

                #Upward Obstruction

                if settpsy_check("s_mask_upward_allow", return_value=True):
                    settpsy_check("s_mask_upward_coll_ptr")
                    settpsy_check("s_mask_upward_revert")

            #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> SCALE

            if ( s_filter.get("s_scale") and not psy.is_locked("s_scale") ):

                settpsy_check("s_scale_master_allow")

                #Default 

                if settpsy_check("s_scale_default_allow", return_value=True):
                    
                    #fix legacy values, Enum values used to be in 'local_scale'/'global_space'
                    if ("s_scale_default_space" in keys):
                        spacev = d["s_scale_default_space"]
                        spacev = spacev.replace("_scale","")
                        psy.s_scale_default_space = spacev
                        
                    settpsy_check("s_scale_default_value")
                    settpsy_check("s_scale_default_multiplier")

                #Random 

                if settpsy_check("s_scale_random_allow", return_value=True):
                    settpsy_check("s_scale_random_factor")
                    settpsy_check("s_scale_random_probability")
                    settpsy_check("s_scale_random_method")
                    settpsy_check("s_scale_random_seed")
                    settpsy_check("s_scale_random_is_random_seed")
                    u_mask_to_settings(category_str="s_scale_random",)
                
                #Shrink 

                if settpsy_check("s_scale_shrink_allow", return_value=True):
                    settpsy_check("s_scale_shrink_factor")
                    u_mask_to_settings(category_str="s_scale_shrink",)

                #Grow 

                if settpsy_check("s_scale_grow_allow", return_value=True):
                    settpsy_check("s_scale_grow_factor")
                    u_mask_to_settings(category_str="s_scale_grow",)

                #Distance Fade 

                if settpsy_check("s_scale_fading_allow", return_value=True):
                    settpsy_check("s_scale_fading_factor")
                    settpsy_check("s_scale_fading_per_cam_data")
                    settpsy_check("s_scale_fading_distance_min")
                    settpsy_check("s_scale_fading_distance_max")
                    if settpsy_check("s_scale_fading_fallremap_allow", return_value=True):
                        settpsy_check("s_scale_fading_fallremap_data")
                        settpsy_check("s_scale_fading_fallremap_revert")

                #Mirror 

                if settpsy_check("s_scale_mirror_allow", return_value=True):  
                    settpsy_check("s_scale_mirror_is_x")
                    settpsy_check("s_scale_mirror_is_y")
                    settpsy_check("s_scale_mirror_is_z")
                    settpsy_check("s_scale_mirror_seed")
                    settpsy_check("s_scale_mirror_is_random_seed")
                    u_mask_to_settings(category_str="s_scale_mirror",)

                #Minimal Scale 

                if settpsy_check("s_scale_min_allow", return_value=True):

                    settpsy_check("s_scale_min_method")
                    settpsy_check("s_scale_min_value")

                #Clump Distribution Special 

                if (psy.s_distribution_method=="clumping"):

                    if settpsy_check("s_scale_clump_allow", return_value=True):
                        settpsy_check("s_scale_clump_value")

                #Faces Distribution Special 

                elif (psy.s_distribution_method=="faces"):

                    if settpsy_check("s_scale_faces_allow", return_value=True):
                        settpsy_check("s_scale_faces_value")

                #Edges Distribution Special 

                elif (psy.s_distribution_method=="edges"):

                    if settpsy_check("s_scale_edges_allow", return_value=True):
                        settpsy_check("s_scale_edges_vec_factor")

                #ProjBezLine Distribution Special 

                elif (psy.s_distribution_method=="projbezline"):
                    
                    if settpsy_check("s_scale_projbezline_radius_allow", return_value=True):
                        settpsy_check("s_scale_projbezline_radius_value")

                #ProjEmpties Distribution Special 

                elif (psy.s_distribution_method=="projempties"):

                    if settpsy_check("s_scale_projempties_allow", return_value=True):
                        settpsy_check("s_scale_projempties_value")

            #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ROTATION

            if ( s_filter.get("s_rot") and not psy.is_locked("s_rot") ):

                settpsy_check("s_rot_master_allow")

                #Align Z 

                if settpsy_check("s_rot_align_z_allow", return_value=True):
                        
                    settpsy_check("s_rot_align_z_method")
                    settpsy_check("s_rot_align_z_method_projbezareanosurf_special")
                    settpsy_check("s_rot_align_z_method_projbezlinenosurf_special")
                    settpsy_check("s_rot_align_z_method_projemptiesnosurf_special")

                    settpsy_check("s_rot_align_z_revert", return_value=True)

                    if settpsy_check("s_rot_align_z_influence_allow", return_value=True):
                        settpsy_check("s_rot_align_z_influence_value")

                    if settpsy_check("s_rot_align_z_smoothing_allow", return_value=True):
                        settpsy_check("s_rot_align_z_smoothing_value")

                    if ("s_rot_align_z_object" in keys):
                        if (d["s_rot_align_z_object"]=="*CAMERA*"): #legacy support, use to encode camera like this
                                psy.s_rot_align_z_method = "meth_align_z_camera"
                        else: psy.s_rot_align_z_object = bpy.data.objects.get(d["s_rot_align_z_object"])

                    settpsy_check("s_rot_align_z_random_seed")
                    settpsy_check("s_rot_align_z_is_random_seed")

                    if settpsy_check("s_rot_align_z_clump_allow", return_value=True):
                        settpsy_check("s_rot_align_z_clump_value")

                #Align Y 

                if settpsy_check("s_rot_align_y_allow", return_value=True):

                    settpsy_check("s_rot_align_y_method")
                    settpsy_check("s_rot_align_y_method_projbezareanosurf_special")
                    settpsy_check("s_rot_align_y_method_projbezlinenosurf_special")
                    settpsy_check("s_rot_align_y_method_projemptiesnosurf_special")

                    settpsy_check("s_rot_align_y_revert", return_value=True)
                                
                    if ("s_rot_align_y_object" in keys) :
                        if (d["s_rot_align_y_object"]=="*CAMERA*"): #legacy support, use to encode camera like this
                                psy.s_rot_align_y_method = "meth_align_y_camera"
                        else: psy.s_rot_align_y_object = bpy.data.objects.get(d["s_rot_align_y_object"])

                    settpsy_check("s_rot_align_y_random_seed")
                    settpsy_check("s_rot_align_y_is_random_seed")

                    settpsy_check("s_rot_align_y_downslope_space")
                    if settpsy_check("s_rot_align_y_downslope_smoothing_allow", return_value=True):
                        settpsy_check("s_rot_align_y_downslope_smoothing_value")
                        
                    settpsy_check("s_rot_align_y_flow_method")
                    settpsy_check("s_rot_align_y_flow_direction")

                    settpsy_check("s_rot_align_y_vcol_ptr")
                    
                    if ("s_rot_align_y_texture_ptr" in keys):
                        texture_ptr_to_settings(category_str="s_rot_align_y")

                #Random Rotation 

                if settpsy_check("s_rot_random_allow", return_value=True):
                    settpsy_check("s_rot_random_tilt_value")
                    settpsy_check("s_rot_random_yaw_value")
                    settpsy_check("s_rot_random_seed")
                    settpsy_check("s_rot_random_is_random_seed")
                    u_mask_to_settings(category_str="s_rot_random",)

                #Rotate  

                if settpsy_check("s_rot_add_allow", return_value=True):
                    settpsy_check("s_rot_add_default")
                    settpsy_check("s_rot_add_random")
                    settpsy_check("s_rot_add_seed")
                    settpsy_check("s_rot_add_is_random_seed")
                    settpsy_check("s_rot_add_snap")
                    u_mask_to_settings(category_str="s_rot_add",)

                #Flowmap Tilting 

                if settpsy_check("s_rot_tilt_allow", return_value=True):

                    settpsy_check("s_rot_tilt_dir_method")
                    settpsy_check("s_rot_tilt_method")
                    settpsy_check("s_rot_tilt_force")
                    settpsy_check("s_rot_tilt_blue_influence")
                    settpsy_check("s_rot_tilt_direction")
                    
                    if (psy.s_rot_tilt_dir_method=="noise"):
                        settpsy_check("s_rot_tilt_noise_space")
                        settpsy_check("s_rot_tilt_noise_scale")
                    
                    if (psy.s_rot_tilt_method=="tilt_vcol"):
                        settpsy_check("s_rot_tilt_vcol_ptr")

                    elif (psy.s_rot_tilt_method=="tilt_text"):
                        if ("s_rot_tilt_texture_ptr" in keys):
                            texture_ptr_to_settings(category_str="s_rot_tilt")

                    u_mask_to_settings(category_str="s_rot_tilt",)

            #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> PATTERN

            if ( s_filter.get("s_pattern") and not psy.is_locked(f"s_pattern") ):

                settpsy_check("s_pattern_master_allow")

                for i in (1,2,3):
                    if settpsy_check(f"s_pattern{i}_allow", return_value=True):

                        if (f"s_pattern{i}_texture_ptr" in keys):
                            texture_ptr_to_settings(category_str=f"s_pattern{i}")

                        settpsy_check(f"s_pattern{i}_color_sample_method")
                        settpsy_check(f"s_pattern{i}_id_color_ptr")
                        settpsy_check(f"s_pattern{i}_id_color_tolerence")

                        settpsy_check(f"s_pattern{i}_dist_infl_allow") 
                        settpsy_check(f"s_pattern{i}_dist_influence")
                        settpsy_check(f"s_pattern{i}_dist_revert")
                        settpsy_check(f"s_pattern{i}_scale_infl_allow") 
                        settpsy_check(f"s_pattern{i}_scale_influence")
                        settpsy_check(f"s_pattern{i}_scale_revert")

                        u_mask_to_settings(category_str=f"s_pattern{i}",)

            #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ABIOTIC 

            if ( s_filter.get("s_abiotic") and not psy.is_locked("s_abiotic") ):

                settpsy_check("s_abiotic_master_allow")

                #Elevation 

                if settpsy_check("s_abiotic_elev_allow", return_value=True):

                    if ("s_abiotic_elev_space" in keys):
                        settpsy_check("s_abiotic_elev_space")
                        settpsy_check("s_abiotic_elev_method")
                        prop_mthd = "local"
                        if ("s_abiotic_elev_method" in keys):
                            prop_mthd = "local" if (d["s_abiotic_elev_method"]=="percentage") else "global"
                        settpsy_check(f"s_abiotic_elev_min_value_{prop_mthd}")
                        settpsy_check(f"s_abiotic_elev_min_falloff_{prop_mthd}")
                        settpsy_check(f"s_abiotic_elev_max_value_{prop_mthd}")
                        settpsy_check(f"s_abiotic_elev_max_falloff_{prop_mthd}")
                    
                    if settpsy_check("s_abiotic_elev_fallremap_allow", return_value=True):
                        settpsy_check("s_abiotic_elev_fallremap_data")
                        settpsy_check("s_abiotic_elev_fallremap_revert")
                        settpsy_check("s_abiotic_elev_fallnoisy_strength")
                        settpsy_check("s_abiotic_elev_fallnoisy_space") 
                        settpsy_check("s_abiotic_elev_fallnoisy_scale") 
                        settpsy_check("s_abiotic_elev_fallnoisy_seed")
                        settpsy_check("s_abiotic_elev_fallnoisy_is_random_seed")

                    settpsy_check("s_abiotic_elev_dist_infl_allow")
                    settpsy_check("s_abiotic_elev_dist_influence")
                    settpsy_check("s_abiotic_elev_dist_revert")
                    settpsy_check("s_abiotic_elev_scale_infl_allow")
                    settpsy_check("s_abiotic_elev_scale_influence")
                    settpsy_check("s_abiotic_elev_scale_revert")

                    u_mask_to_settings(category_str="s_abiotic_elev",)

                #Slope 

                if settpsy_check("s_abiotic_slope_allow", return_value=True):

                    settpsy_check("s_abiotic_slope_space")
                    settpsy_check("s_abiotic_slope_absolute")
                    settpsy_check("s_abiotic_slope_min_value")
                    settpsy_check("s_abiotic_slope_min_falloff")
                    settpsy_check("s_abiotic_slope_max_value")
                    settpsy_check("s_abiotic_slope_max_falloff")

                    if settpsy_check("s_abiotic_slope_smoothing_allow", return_value=True):
                        settpsy_check("s_abiotic_slope_smoothing_value")

                    if settpsy_check("s_abiotic_slope_fallremap_allow", return_value=True):
                        settpsy_check("s_abiotic_slope_fallremap_data")
                        settpsy_check("s_abiotic_slope_fallremap_revert")
                        settpsy_check("s_abiotic_slope_fallnoisy_strength")
                        settpsy_check("s_abiotic_slope_fallnoisy_space") 
                        settpsy_check("s_abiotic_slope_fallnoisy_scale") 
                        settpsy_check("s_abiotic_slope_fallnoisy_seed")
                        settpsy_check("s_abiotic_slope_fallnoisy_is_random_seed")

                    settpsy_check("s_abiotic_slope_dist_infl_allow")
                    settpsy_check("s_abiotic_slope_dist_influence")
                    settpsy_check("s_abiotic_slope_dist_revert")
                    settpsy_check("s_abiotic_slope_scale_infl_allow")
                    settpsy_check("s_abiotic_slope_scale_influence")
                    settpsy_check("s_abiotic_slope_scale_revert")

                    u_mask_to_settings(category_str="s_abiotic_slope",)

                #Orientation 

                if settpsy_check("s_abiotic_dir_allow", return_value=True):

                    settpsy_check("s_abiotic_dir_space")
                    settpsy_check("s_abiotic_dir_direction")
                    settpsy_check("s_abiotic_dir_max")
                    settpsy_check("s_abiotic_dir_treshold")

                    if settpsy_check("s_abiotic_dir_smoothing_allow", return_value=True):
                        settpsy_check("s_abiotic_dir_smoothing_value")
                        
                    if settpsy_check("s_abiotic_dir_fallremap_allow", return_value=True):
                        settpsy_check("s_abiotic_dir_fallremap_data")
                        settpsy_check("s_abiotic_dir_fallremap_revert")
                        settpsy_check("s_abiotic_dir_fallnoisy_strength")
                        settpsy_check("s_abiotic_dir_fallnoisy_space") 
                        settpsy_check("s_abiotic_dir_fallnoisy_scale") 
                        settpsy_check("s_abiotic_dir_fallnoisy_seed")
                        settpsy_check("s_abiotic_dir_fallnoisy_is_random_seed")

                    settpsy_check("s_abiotic_dir_dist_infl_allow")
                    settpsy_check("s_abiotic_dir_dist_influence")
                    settpsy_check("s_abiotic_dir_dist_revert")
                    settpsy_check("s_abiotic_dir_scale_infl_allow")
                    settpsy_check("s_abiotic_dir_scale_influence")
                    settpsy_check("s_abiotic_dir_scale_revert")

                    u_mask_to_settings(category_str="s_abiotic_dir",)

                #Curvature

                if settpsy_check("s_abiotic_cur_allow", return_value=True):

                    settpsy_check("s_abiotic_cur_type")
                    settpsy_check("s_abiotic_cur_max")
                    settpsy_check("s_abiotic_cur_treshold")
                    
                    if settpsy_check("s_abiotic_cur_smoothing_allow", return_value=True):
                        settpsy_check("s_abiotic_cur_smoothing_value")
                    
                    if settpsy_check("s_abiotic_cur_fallremap_allow", return_value=True):
                        settpsy_check("s_abiotic_cur_fallremap_data")
                        settpsy_check("s_abiotic_cur_fallremap_revert")
                        settpsy_check("s_abiotic_cur_fallnoisy_strength")
                        settpsy_check("s_abiotic_cur_fallnoisy_space") 
                        settpsy_check("s_abiotic_cur_fallnoisy_scale") 
                        settpsy_check("s_abiotic_cur_fallnoisy_seed")
                        settpsy_check("s_abiotic_cur_fallnoisy_is_random_seed")

                    settpsy_check("s_abiotic_cur_dist_infl_allow")
                    settpsy_check("s_abiotic_cur_dist_influence")
                    settpsy_check("s_abiotic_cur_dist_revert")
                    settpsy_check("s_abiotic_cur_scale_infl_allow")
                    settpsy_check("s_abiotic_cur_scale_influence")
                    settpsy_check("s_abiotic_cur_scale_revert")

                    u_mask_to_settings(category_str="s_abiotic_cur",)

                #Border

                if settpsy_check("s_abiotic_border_allow", return_value=True):

                    settpsy_check("s_abiotic_border_space")
                    settpsy_check("s_abiotic_border_max")
                    settpsy_check("s_abiotic_border_treshold")
                    
                    if settpsy_check("s_abiotic_border_fallremap_allow", return_value=True):
                        settpsy_check("s_abiotic_border_fallremap_data")
                        settpsy_check("s_abiotic_border_fallremap_revert")
                        settpsy_check("s_abiotic_border_fallnoisy_strength")
                        settpsy_check("s_abiotic_border_fallnoisy_space") 
                        settpsy_check("s_abiotic_border_fallnoisy_scale") 
                        settpsy_check("s_abiotic_border_fallnoisy_seed")
                        settpsy_check("s_abiotic_border_fallnoisy_is_random_seed")

                    settpsy_check("s_abiotic_border_dist_infl_allow")
                    settpsy_check("s_abiotic_border_dist_influence")
                    settpsy_check("s_abiotic_border_dist_revert")
                    settpsy_check("s_abiotic_border_scale_infl_allow")
                    settpsy_check("s_abiotic_border_scale_influence")
                    settpsy_check("s_abiotic_border_scale_revert")

                    u_mask_to_settings(category_str="s_abiotic_border",)

            #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> PROXIMITY


            if ( s_filter.get("s_proximity") and not psy.is_locked("s_proximity") ):

                settpsy_check("s_proximity_master_allow")
                
                #ProjBezArea Special
                
                if (psy.s_distribution_method=="projbezarea"):
                    
                    if settpsy_check("s_proximity_projbezarea_border_allow", return_value=True):

                        settpsy_check("s_proximity_projbezarea_border_max")
                        settpsy_check("s_proximity_projbezarea_border_treshold")
                        
                        if settpsy_check("s_proximity_projbezarea_border_fallremap_allow", return_value=True):
                            settpsy_check("s_proximity_projbezarea_border_fallremap_data")
                            settpsy_check("s_proximity_projbezarea_border_fallremap_revert")
                            settpsy_check("s_proximity_projbezarea_border_fallnoisy_strength")
                            settpsy_check("s_proximity_projbezarea_border_fallnoisy_space") 
                            settpsy_check("s_proximity_projbezarea_border_fallnoisy_scale") 
                            settpsy_check("s_proximity_projbezarea_border_fallnoisy_seed")
                            settpsy_check("s_proximity_projbezarea_border_fallnoisy_is_random_seed")

                        settpsy_check("s_proximity_projbezarea_border_dist_infl_allow")
                        settpsy_check("s_proximity_projbezarea_border_dist_influence")
                        settpsy_check("s_proximity_projbezarea_border_dist_revert")
                        settpsy_check("s_proximity_projbezarea_border_scale_infl_allow")
                        settpsy_check("s_proximity_projbezarea_border_scale_influence")
                        settpsy_check("s_proximity_projbezarea_border_scale_revert")
                    
                #Object-Repel 1&2

                for i in (1,2):

                    if settpsy_check(f"s_proximity_repel{i}_allow", return_value=True):

                        settpsy_check(f"s_proximity_repel{i}_type")
                        settpsy_check(f"s_proximity_repel{i}_max")
                        settpsy_check(f"s_proximity_repel{i}_treshold")

                        settpsy_check(f"s_proximity_repel{i}_volume_allow")
                        settpsy_check(f"s_proximity_repel{i}_volume_method")

                        if settpsy_check(f"s_proximity_repel{i}_fallremap_allow", return_value=True):
                            settpsy_check(f"s_proximity_repel{i}_fallremap_data")
                            settpsy_check(f"s_proximity_repel{i}_fallremap_revert")
                            settpsy_check(f"s_proximity_repel{i}_fallnoisy_strength")
                            settpsy_check(f"s_proximity_repel{i}_fallnoisy_space")
                            settpsy_check(f"s_proximity_repel{i}_fallnoisy_scale")
                            settpsy_check(f"s_proximity_repel{i}_fallnoisy_seed")
                            settpsy_check(f"s_proximity_repel{i}_fallnoisy_is_random_seed")

                        if settpsy_check(f"s_proximity_repel{i}_simulation_allow", return_value=True):
                            if settpsy_check(f"s_proximity_repel{i}_simulation_fadeaway_allow", return_value=True):
                                settpsy_check(f"s_proximity_repel{i}_simulation_fadeaway_method")
                                settpsy_check(f"s_proximity_repel{i}_simulation_fadeaway_frame")
                                settpsy_check(f"s_proximity_repel{i}_simulation_fadeaway_sec")
                        
                        settpsy_check(f"s_proximity_repel{i}_dist_infl_allow")
                        settpsy_check(f"s_proximity_repel{i}_dist_influence")
                        settpsy_check(f"s_proximity_repel{i}_dist_revert")
                        settpsy_check(f"s_proximity_repel{i}_scale_infl_allow")
                        settpsy_check(f"s_proximity_repel{i}_scale_influence")
                        settpsy_check(f"s_proximity_repel{i}_scale_revert")
                        settpsy_check(f"s_proximity_repel{i}_nor_infl_allow")
                        settpsy_check(f"s_proximity_repel{i}_nor_influence")
                        settpsy_check(f"s_proximity_repel{i}_nor_revert")
                        settpsy_check(f"s_proximity_repel{i}_tan_infl_allow")
                        settpsy_check(f"s_proximity_repel{i}_tan_influence")
                        settpsy_check(f"s_proximity_repel{i}_tan_revert")
                        settpsy_check(f"s_proximity_repel{i}_coll_ptr")

                        u_mask_to_settings(category_str=f"s_proximity_repel{i}",)

                #Outskirt

                if settpsy_check("s_proximity_outskirt_allow", return_value=True):

                    settpsy_check("s_proximity_outskirt_detection")
                    settpsy_check("s_proximity_outskirt_precision")
                    settpsy_check("s_proximity_outskirt_max")
                    settpsy_check("s_proximity_outskirt_treshold")

                    if settpsy_check("s_proximity_outskirt_fallremap_allow", return_value=True):
                        settpsy_check("s_proximity_outskirt_fallremap_data")
                        settpsy_check("s_proximity_outskirt_fallremap_revert")
                        settpsy_check("s_proximity_outskirt_fallnoisy_strength")
                        settpsy_check("s_proximity_outskirt_fallnoisy_space") 
                        settpsy_check("s_proximity_outskirt_fallnoisy_scale") 
                        settpsy_check("s_proximity_outskirt_fallnoisy_seed")
                        settpsy_check("s_proximity_outskirt_fallnoisy_is_random_seed")

                    settpsy_check("s_proximity_outskirt_dist_infl_allow")
                    settpsy_check("s_proximity_outskirt_dist_influence")
                    settpsy_check("s_proximity_outskirt_dist_revert")
                    settpsy_check("s_proximity_outskirt_scale_infl_allow")
                    settpsy_check("s_proximity_outskirt_scale_influence")
                    settpsy_check("s_proximity_outskirt_scale_revert")
                    # settpsy_check("s_proximity_outskirt_nor_infl_allow")
                    # settpsy_check("s_proximity_outskirt_nor_influence")
                    # settpsy_check("s_proximity_outskirt_nor_revert")
                    # settpsy_check("s_proximity_outskirt_tan_infl_allow")
                    # settpsy_check("s_proximity_outskirt_tan_influence")
                    # settpsy_check("s_proximity_outskirt_tan_revert")

                    u_mask_to_settings(category_str="s_proximity_outskirt",)

            #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ECOSYSTEM

            if ( s_filter.get("s_ecosystem") and not psy.is_locked("s_ecosystem") ):

                #Affinity

                if settpsy_check("s_ecosystem_affinity_allow", return_value=True):
                    settpsy_check("s_ecosystem_affinity_space")

                    for i in (1,2,3):
                        if (f"s_ecosystem_affinity_{i:02}_ptr" not in d):
                            continue
                        if (d[f"s_ecosystem_affinity_{i:02}_ptr"]==""):
                            continue
                        if (psy.name[-3:].isdigit() and psy.name[-4]=="."): #for biome, need to assign dupplicatas if needed
                            d[f"s_ecosystem_affinity_{i:02}_ptr"] = d[f"s_ecosystem_affinity_{i:02}_ptr"]+psy.name[-4:] #TODO biomes very bad practive..

                        settpsy_check(f"s_ecosystem_affinity_{i:02}_ptr")
                        settpsy_check(f"s_ecosystem_affinity_{i:02}_type")
                        settpsy_check(f"s_ecosystem_affinity_{i:02}_max_value")
                        settpsy_check(f"s_ecosystem_affinity_{i:02}_max_falloff")
                        settpsy_check(f"s_ecosystem_affinity_{i:02}_limit_distance")
                        continue

                    if settpsy_check("s_ecosystem_affinity_fallremap_allow", return_value=True):
                        settpsy_check("s_ecosystem_affinity_fallremap_data")
                        settpsy_check("s_ecosystem_affinity_fallremap_revert")
                        settpsy_check("s_ecosystem_affinity_fallnoisy_strength")
                        settpsy_check("s_ecosystem_affinity_fallnoisy_space") 
                        settpsy_check("s_ecosystem_affinity_fallnoisy_scale") 
                        settpsy_check("s_ecosystem_affinity_fallnoisy_seed")
                        settpsy_check("s_ecosystem_affinity_fallnoisy_is_random_seed")

                    settpsy_check("s_ecosystem_affinity_dist_infl_allow")
                    settpsy_check("s_ecosystem_affinity_dist_influence")
                    settpsy_check("s_ecosystem_affinity_scale_infl_allow")
                    settpsy_check("s_ecosystem_affinity_scale_influence")

                    #cancel out if nothing is assigned!
                    if all(not getattr(psy,f"s_ecosystem_affinity_{i:02}_ptr") for i in (1,2,3)):
                        psy.s_ecosystem_affinity_allow = False

                    u_mask_to_settings(category_str="s_ecosystem_affinity",)

                #Repulsion

                if settpsy_check("s_ecosystem_repulsion_allow", return_value=True):
                    settpsy_check("s_ecosystem_repulsion_space")

                    for i in (1,2,3):
                        if (f"s_ecosystem_repulsion_{i:02}_ptr" not in d):
                            continue
                        if (d[f"s_ecosystem_repulsion_{i:02}_ptr"]==""):
                            continue
                        if (psy.name[-3:].isdigit() and psy.name[-4]=="."): #for biome, need to assign dupplicatas if needed
                            d[f"s_ecosystem_repulsion_{i:02}_ptr"] = d[f"s_ecosystem_repulsion_{i:02}_ptr"]+psy.name[-4:] #TODO biomes very bad practive..

                        settpsy_check(f"s_ecosystem_repulsion_{i:02}_ptr")
                        settpsy_check(f"s_ecosystem_repulsion_{i:02}_type")
                        settpsy_check(f"s_ecosystem_repulsion_{i:02}_max_value")
                        settpsy_check(f"s_ecosystem_repulsion_{i:02}_max_falloff")
                        continue

                    if settpsy_check("s_ecosystem_repulsion_fallremap_allow", return_value=True):
                        settpsy_check("s_ecosystem_repulsion_fallremap_data")
                        settpsy_check("s_ecosystem_repulsion_fallremap_revert")
                        settpsy_check("s_ecosystem_repulsion_fallnoisy_strength")
                        settpsy_check("s_ecosystem_repulsion_fallnoisy_space") 
                        settpsy_check("s_ecosystem_repulsion_fallnoisy_scale") 
                        settpsy_check("s_ecosystem_repulsion_fallnoisy_seed")
                        settpsy_check("s_ecosystem_repulsion_fallnoisy_is_random_seed")

                    settpsy_check("s_ecosystem_repulsion_dist_infl_allow")
                    settpsy_check("s_ecosystem_repulsion_dist_influence")
                    settpsy_check("s_ecosystem_repulsion_scale_infl_allow")
                    settpsy_check("s_ecosystem_repulsion_scale_influence")

                    #cancel out if nothing is assigned!
                    if all(not getattr(psy,f"s_ecosystem_repulsion_{i:02}_ptr") for i in (1,2,3)):
                        psy.s_ecosystem_repulsion_allow = False

                    u_mask_to_settings(category_str="s_ecosystem_repulsion",)

                #Density
                
                if settpsy_check("s_ecosystem_density_allow", return_value=True):
                    settpsy_check("s_ecosystem_density_space")
                    settpsy_check("s_ecosystem_density_method")
                    settpsy_check("s_ecosystem_density_voxelsize")
                    settpsy_check("s_ecosystem_density_min")
                    settpsy_check("s_ecosystem_density_falloff")
                    
                    for i in (1,2,3):
                        if (f"s_ecosystem_density_{i:02}_ptr" not in d):
                            continue
                        if (d[f"s_ecosystem_density_{i:02}_ptr"]==""):
                            continue
                        if (psy.name[-3:].isdigit() and psy.name[-4]=="."): #for biome, need to assign dupplicatas if needed
                            d[f"s_ecosystem_density_{i:02}_ptr"] = d[f"s_ecosystem_density_{i:02}_ptr"]+psy.name[-4:] #TODO biomes very bad practive..
                        
                        settpsy_check(f"s_ecosystem_density_{i:02}_ptr")
                        continue 
                    
                    if settpsy_check("s_ecosystem_density_fallremap_allow", return_value=True):
                        settpsy_check("s_ecosystem_density_fallremap_data")
                        settpsy_check("s_ecosystem_density_fallremap_revert")
                        settpsy_check("s_ecosystem_density_fallnoisy_strength")
                        settpsy_check("s_ecosystem_density_fallnoisy_space") 
                        settpsy_check("s_ecosystem_density_fallnoisy_scale") 
                        settpsy_check("s_ecosystem_density_fallnoisy_seed")
                        settpsy_check("s_ecosystem_density_fallnoisy_is_random_seed")

                    settpsy_check("s_ecosystem_density_dist_infl_allow")
                    settpsy_check("s_ecosystem_density_dist_influence")
                    settpsy_check("s_ecosystem_density_scale_infl_allow")
                    settpsy_check("s_ecosystem_density_scale_influence")
                    
                    #cancel out if nothing is assigned!
                    if all(not getattr(psy,f"s_ecosystem_density_{i:02}_ptr") for i in (1,2,3)):
                        psy.s_ecosystem_density_allow = False

                    u_mask_to_settings(category_str="s_ecosystem_density",)
            
            #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> OFFSET

            if ( s_filter.get("s_push") and not psy.is_locked("s_push") ): 

                settpsy_check("s_push_master_allow")

                #Push Offset

                if settpsy_check("s_push_offset_allow", return_value=True):
                    settpsy_check("s_push_offset_space")
                    settpsy_check("s_push_offset_add_value")
                    settpsy_check("s_push_offset_add_random")
                    settpsy_check("s_push_offset_rotate_value")
                    settpsy_check("s_push_offset_rotate_random")
                    settpsy_check("s_push_offset_scale_value")
                    settpsy_check("s_push_offset_scale_random")
                    settpsy_check("s_push_offset_seed")
                    settpsy_check("s_push_offset_is_random_seed")
                    u_mask_to_settings(category_str="s_push_offset",)

                #Push 

                if settpsy_check("s_push_dir_allow", return_value=True):
                    settpsy_check("s_push_dir_space")
                    settpsy_check("s_push_dir_method")
                    settpsy_check("s_push_dir_method_projbezareanosurf_special")
                    settpsy_check("s_push_dir_method_projbezlinenosurf_special")
                    settpsy_check("s_push_dir_method_projemptiesnosurf_special")
                    settpsy_check("s_push_dir_add_value")
                    settpsy_check("s_push_dir_add_random")
                    settpsy_check("s_push_dir_seed")
                    settpsy_check("s_push_dir_is_random_seed")
                    u_mask_to_settings(category_str="s_push_dir",)

                #Noise 

                if settpsy_check("s_push_noise_allow", return_value=True):
                    settpsy_check("s_push_noise_space")
                    settpsy_check("s_push_noise_vector")
                    settpsy_check("s_push_noise_is_animated")
                    settpsy_check("s_push_noise_speed")
                    settpsy_check("s_push_noise_seed")
                    settpsy_check("s_push_noise_is_random_seed")
                    u_mask_to_settings(category_str="s_push_noise",)

                #Falling 

                if settpsy_check("s_push_fall_allow", return_value=True):
                    settpsy_check("s_push_fall_space")
                    settpsy_check("s_push_fall_height")
                    settpsy_check("s_push_fall_key1_pos")
                    settpsy_check("s_push_fall_key1_height")
                    settpsy_check("s_push_fall_key2_pos")
                    settpsy_check("s_push_fall_key2_height")
                    settpsy_check("s_push_fall_stop_when_initial_z")
              
                    if settpsy_check("s_push_fall_turbulence_allow", return_value=True):
                        settpsy_check("s_push_fall_turbulence_spread")
                        settpsy_check("s_push_fall_turbulence_speed")
                        settpsy_check("s_push_fall_turbulence_rot_vector")
                        settpsy_check("s_push_fall_turbulence_rot_factor")

                    settpsy_check("s_push_fall_seed")
                    settpsy_check("s_push_fall_is_random_seed")

                    u_mask_to_settings(category_str="s_push_fall",)

            #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> WIND EFFECT

            if ( s_filter.get("s_wind") and not psy.is_locked("s_wind") ):

                settpsy_check("s_wind_master_allow")

                #Wind Wave 

                if settpsy_check("s_wind_wave_allow", return_value=True):
                    settpsy_check("s_wind_wave_space")
                    settpsy_check("s_wind_wave_method")

                    if settpsy_check("s_wind_wave_loopable_cliplength_allow", return_value=True):
                        settpsy_check("s_wind_wave_loopable_frame_start")
                        settpsy_check("s_wind_wave_loopable_frame_end")

                    settpsy_check("s_wind_wave_speed")
                    settpsy_check("s_wind_wave_force")
                    
                    settpsy_check("s_wind_wave_swinging")
                    settpsy_check("s_wind_wave_swinging_factor")
                    
                    settpsy_check("s_wind_wave_scale_influence")
                    settpsy_check("s_wind_wave_scale_influence_factor")

                    settpsy_check("s_wind_wave_texture_scale")
                    settpsy_check("s_wind_wave_texture_turbulence")
                    settpsy_check("s_wind_wave_texture_distorsion")
                    settpsy_check("s_wind_wave_texture_brightness")
                    settpsy_check("s_wind_wave_texture_contrast")

                    settpsy_check("s_wind_wave_dir_method")

                    if (d["s_wind_wave_dir_method"]=="vcol"):
                        settpsy_check("s_wind_wave_flowmap_ptr")
                        settpsy_check("s_wind_wave_direction")

                    elif (d["s_wind_wave_dir_method"]=="fixed"):
                        settpsy_check("s_wind_wave_direction")
                        settpsy_check("s_wind_wave_direction_random")

                    u_mask_to_settings(category_str="s_wind_wave",)
                            
                #Wind Noise
                
                if settpsy_check("s_wind_noise_allow", return_value=True):
                    settpsy_check("s_wind_noise_space")
                    settpsy_check("s_wind_noise_method")

                    if settpsy_check("s_wind_noise_loopable_cliplength_allow", return_value=True):
                        settpsy_check("s_wind_noise_loopable_frame_start")
                        settpsy_check("s_wind_noise_loopable_frame_end")

                    settpsy_check("s_wind_noise_force")
                    settpsy_check("s_wind_noise_speed")

                    u_mask_to_settings(category_str="s_wind_noise",)

            #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> VISIBILITY

            if ( s_filter.get("s_visibility") and not psy.is_locked("s_visibility") ):

                settpsy_check("s_visibility_master_allow")

                #Face Preview 

                if settpsy_check("s_visibility_facepreview_allow", return_value=True):
                    settpsy_check("s_visibility_facepreview_viewport_method")

                #Visibility Percentage

                if settpsy_check("s_visibility_view_allow", return_value=True):
                    settpsy_check("s_visibility_view_percentage")
                    settpsy_check("s_visibility_view_viewport_method")
                    
                #Visibility Camera Optimization 

                if settpsy_check("s_visibility_cam_allow", return_value=True):
                    
                    settpsy_check("s_visibility_cam_predist_allow")
                    
                    if settpsy_check("s_visibility_camclip_allow", return_value=True):

                        if not settpsy_check("s_visibility_camclip_cam_autofill", return_value=True):
                            settpsy_check("s_visibility_camclip_cam_lens")
                            settpsy_check("s_visibility_camclip_cam_sensor_width")
                            settpsy_check("s_visibility_camclip_cam_res_xy")
                            settpsy_check("s_visibility_camclip_cam_shift_xy")
                        settpsy_check("s_visibility_camclip_cam_boost_xy")
                        if settpsy_check("s_visibility_camclip_proximity_allow", return_value=True):
                            settpsy_check("s_visibility_camclip_proximity_distance")

                    if settpsy_check("s_visibility_camdist_allow", return_value=True):
                        if settpsy_check("s_visibility_camdist_fallremap_allow", return_value=True):
                            settpsy_check("s_visibility_camdist_fallremap_data")
                            settpsy_check("s_visibility_camdist_fallremap_revert")
                        settpsy_check("s_visibility_camdist_per_cam_data")
                        settpsy_check("s_visibility_camdist_min")
                        settpsy_check("s_visibility_camdist_max")

                    if settpsy_check("s_visibility_camoccl_allow", return_value=True):
                        settpsy_check("s_visibility_camoccl_method")
                        settpsy_check("s_visibility_camoccl_threshold")
                        settpsy_check("s_visibility_camoccl_coll_ptr")

                    settpsy_check("s_visibility_cam_viewport_method")

                #Visibility Maxload

                if settpsy_check("s_visibility_maxload_allow", return_value=True):
                    settpsy_check("s_visibility_maxload_cull_method")
                    settpsy_check("s_visibility_maxload_treshold")
                    settpsy_check("s_visibility_maxload_viewport_method")

            #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> INSTANCING

            if ( s_filter.get("s_instances") and not psy.is_locked("s_instances") ):

                #instances methods settings support here
                #note that we never support instance model lists
                #`.preset` are only for settings, objects and blend file == stored in `.biome` format 

                if ("s_instances_method" in keys):

                    #versioning of old .biome files
                    if "s_instances_method" in d:
                        if (d["s_instances_method"]=="ins_coll_random"):
                            d["s_instances_method"]="ins_collection"

                    settpsy_check("s_instances_seed")
                    settpsy_check("s_instances_is_random_seed")
                    settpsy_check("s_instances_method")
                    settpsy_check("s_instances_pick_method")

                    pick_method = d.get("s_instances_pick_method")

                    if (pick_method=="pick_rate"):

                        for i in range(1,21):
                            settpsy_check(f"s_instances_id_{i:02}_rate")

                    elif (pick_method=="pick_scale"):

                        for i in range(1,21):
                            settpsy_check(f"s_instances_id_{i:02}_scale_min")
                            settpsy_check(f"s_instances_id_{i:02}_scale_max")

                        settpsy_check("s_instances_id_scale_method")

                    elif (pick_method=="pick_color"):

                        for i in range(1,21):
                            settpsy_check(f"s_instances_id_{i:02}_color")

                        settpsy_check("s_instances_id_color_tolerence")
                        settpsy_check("s_instances_id_color_sample_method")

                        sample_method = d["s_instances_id_color_sample_method"]
                        if (sample_method=="vcol"):
                            settpsy_check("s_instances_vcol_ptr")
                        elif (sample_method=="text"):
                            if (f"s_instances_texture_ptr" in keys):
                                texture_ptr_to_settings(category_str=f"s_instances")

                    elif (pick_method=="pick_cluster"):

                        settpsy_check("s_instances_pick_cluster_projection_method")
                        settpsy_check("s_instances_pick_cluster_scale")
                        settpsy_check("s_instances_pick_cluster_blur")
                        settpsy_check("s_instances_pick_clump")

            #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> DISPLAY

            if ( s_filter.get("s_display") and not psy.is_locked("s_display") ):

                settpsy_check("s_display_master_allow")

                #Display as

                settpsy_check("s_display_allow")
                settpsy_check("s_display_method")
                
                settpsy_check("s_display_placeholder_type")
                settpsy_check("s_display_custom_placeholder_ptr")
                settpsy_check("s_display_placeholder_scale")
                
                settpsy_check("s_display_point_radius")
                
                settpsy_check("s_display_camdist_allow")
                settpsy_check("s_display_camdist_distance")

                settpsy_check("s_display_cloud_radius")
                settpsy_check("s_display_cloud_density")

                settpsy_check("s_display_viewport_method")

            #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    return None


#  .oooooo..o               .            .                  oooooooooo.    o8o                .
# d8P'    `Y8             .o8          .o8                  `888'   `Y8b   `"'              .o8
# Y88bo.       .ooooo.  .o888oo      .o888oo  .ooooo.        888      888 oooo   .ooooo.  .o888oo
#  `"Y8888o.  d88' `88b   888          888   d88' `88b       888      888 `888  d88' `"Y8   888
#      `"Y88b 888ooo888   888          888   888   888       888      888  888  888         888
# oo     .d8P 888    .o   888 .        888 . 888   888       888     d88'  888  888   .o8   888 .
# 8""88888P'  `Y8bod8P'   "888"        "888" `Y8bod8P'      o888bood8P'   o888o `Y8bod8P'   "888"


def settings_to_dict( psy,
    use_random_seed=True,
    texture_is_unique=True,
    texture_random_loc=True,
    get_scatter_density=False,
    #filter the settings by category, by default we never save some settings in preset file, however this function is used universally in this plugin
    s_filter={
        "s_color":True,
        "s_surface":False,
        "s_distribution":True,
        "s_mask":False, 
        "s_rot":True,
        "s_scale":True,
        "s_pattern":True,
        "s_push":True,
        "s_abiotic":True,
        "s_proximity":False,
        "s_ecosystem":True,
        "s_wind":True,
        "s_visibility":False, 
        "s_instances":True,
        "s_display":False, 
        },
    ):
    """ dict <- settings """ 
    #extra care here, we save only what is being used
    
    d = {}

    def save_texture_ptr_in_dict(category_str="", texture_is_unique=False, texture_random_loc=False,):
        """helper funciton for scatter ng texture type, used a bit everywhere below"""

        #make sure texture_ptr is up to date 
        texture_node = psy.get_scatter_node(category_str).node_tree.nodes["texture"]
        ng_name = texture_node.node_tree.name 
        if ng_name.startswith(".TEXTURE *DEFAULT"): 
            ng_name=""
        setattr(psy, f"{category_str}_texture_ptr", ng_name)

        ng = bpy.data.node_groups.get(ng_name) 
        if (ng is not None):
            d[f"{category_str}_texture_ptr"] = ng_name
            d[f"{category_str}_texture_is_unique"] = texture_is_unique 
            d[f"{category_str}_texture_dict"] = ng.scatter5.texture.get_texture_dict(texture_random_loc=texture_random_loc,)

        return None 

    def save_u_mask_in_dict(category_str="",):
        """saving masks settings collection in .preset dict, this is an universal mask system, all settings are implemented the same way""" 

        try: 
            allow = getattr(psy, f"{category_str}_mask_allow")
            method = getattr(psy, f"{category_str}_mask_method")
        except Exception as e:
            print(f"ERROR: settings_to_dict().save_u_mask_in_dict(): getattr(psy,). This should never happen")
            print(e)
            return None 

        if ((method is None) or (allow is None)):
            return None
        if ((not allow) or (method=="none")):
            return None

        mdi = d[f"{category_str}_mask_dict"] = {}

        mdi[f"{category_str}_mask_method"] = getattr(psy,f"{category_str}_mask_method")
        
        match method:
            case 'mask_vg':
                mdi[f"{category_str}_mask_ptr"] = getattr(psy,f"{category_str}_mask_ptr")
                mdi[f"{category_str}_mask_reverse"] = getattr(psy,f"{category_str}_mask_reverse")
            case 'mask_vcol':
                mdi[f"{category_str}_mask_ptr"] = getattr(psy,f"{category_str}_mask_ptr")
                mdi[f"{category_str}_mask_color_sample_method"] = getattr(psy,f"{category_str}_mask_color_sample_method")
                mdi[f"{category_str}_mask_id_color_ptr"] = getattr(psy,f"{category_str}_mask_id_color_ptr")
                mdi[f"{category_str}_mask_reverse"] = getattr(psy,f"{category_str}_mask_reverse")
            case 'mask_bitmap':
                mdi[f"{category_str}_mask_bitmap_ptr"] = getattr(psy,f"{category_str}_mask_bitmap_ptr")
                mdi[f"{category_str}_mask_bitmap_uv_ptr"] = getattr(psy,f"{category_str}_mask_bitmap_uv_ptr")
                mdi[f"{category_str}_mask_color_sample_method"] = getattr(psy,f"{category_str}_mask_color_sample_method")
                mdi[f"{category_str}_mask_id_color_ptr"] = getattr(psy,f"{category_str}_mask_id_color_ptr")
                mdi[f"{category_str}_mask_reverse"] = getattr(psy,f"{category_str}_mask_reverse")
            case 'mask_noise':
                mdi[f"{category_str}_mask_noise_space"] = getattr(psy,f"{category_str}_mask_noise_space")
                mdi[f"{category_str}_mask_noise_scale"] = getattr(psy,f"{category_str}_mask_noise_scale")
                if use_random_seed: d[f"{category_str}_mask_noise_is_random_seed"] = True
                else: d[f"{category_str}_mask_noise_seed"] = getattr(psy,f"{category_str}_mask_noise_seed")
                mdi[f"{category_str}_mask_noise_brightness"] = getattr(psy,f"{category_str}_mask_noise_brightness")
                mdi[f"{category_str}_mask_noise_contrast"] = getattr(psy,f"{category_str}_mask_noise_contrast")

        return None

    d[">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> INFORMATION"] = ""
    
    d["name"] = psy.name

    if s_filter.get("s_distribution"):
        if (get_scatter_density):
            d["estimated_density"] = psy.get_scatter_density()

    if s_filter.get("s_color"):
        d[">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> COLOR"] = ""

        d["s_color"] = list(psy.s_color)

    if s_filter.get("s_surface"):
        d[">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> SURFACE"] = ""

        d["s_surface_method"] = psy.s_surface_method

        match d["s_surface_method"]:
            case 'object':
                d["s_surface_object"] = psy.s_surface_object.name if (psy.s_surface_object is not None) else ""
            case 'collection':
                d["s_surface_collection"] = psy.s_surface_collection

    if s_filter.get("s_distribution"):
        d[">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> DISTRIBUTION"] = ""

        d["s_distribution_method"] = psy.s_distribution_method

        match d["s_distribution_method"]:

            case 'random': #Random Distribution 

                d["s_distribution_space"] = psy.s_distribution_space
                d["s_distribution_is_count_method"] = psy.s_distribution_is_count_method
                if (psy.s_distribution_is_count_method=="density"):
                    d["s_distribution_density"] = psy.s_distribution_density
                else: d["s_distribution_count"] = psy.s_distribution_count

                if use_random_seed: d["s_distribution_is_random_seed"] = True
                else: d["s_distribution_seed"] = psy.s_distribution_seed

                d["s_distribution_limit_distance_allow"] = psy.s_distribution_limit_distance_allow
                if psy.s_distribution_limit_distance_allow:
                    d["s_distribution_limit_distance"] = psy.s_distribution_limit_distance

            case 'random_stable': #Stable Distribution 

                d["s_distribution_stable_is_count_method"] = psy.s_distribution_stable_is_count_method
                if (psy.s_distribution_stable_is_count_method=="density"):
                    d["s_distribution_stable_density"] = psy.s_distribution_stable_density
                else: d["s_distribution_stable_count"] = psy.s_distribution_stable_count

                if use_random_seed: d["s_distribution_stable_is_random_seed"] = True
                else: d["s_distribution_stable_seed"] = psy.s_distribution_stable_seed

                d["s_distribution_stable_limit_distance_allow"] = psy.s_distribution_stable_limit_distance_allow
                if psy.s_distribution_stable_limit_distance_allow:
                    d["s_distribution_stable_limit_distance"] = psy.s_distribution_stable_limit_distance

            case 'clumping': #Clump Distribution 

                d["s_distribution_clump_space"] = psy.s_distribution_clump_space
                d["s_distribution_clump_density"] = psy.s_distribution_clump_density
                d["s_distribution_clump_max_distance"] = psy.s_distribution_clump_max_distance
                d["s_distribution_clump_random_factor"] = psy.s_distribution_clump_random_factor
                d["s_distribution_clump_falloff"] = psy.s_distribution_clump_falloff

                if use_random_seed: d["s_distribution_clump_is_random_seed"] = True
                else: d["s_distribution_clump_seed"] = psy.s_distribution_clump_seed

                d["s_distribution_clump_limit_distance_allow"] = psy.s_distribution_clump_limit_distance_allow
                if psy.s_distribution_clump_limit_distance_allow:
                    d["s_distribution_clump_limit_distance"] = psy.s_distribution_clump_limit_distance

                d["s_distribution_clump_fallremap_allow"] = psy.s_distribution_clump_fallremap_allow
                if psy.s_distribution_clump_fallremap_allow:
                    d["s_distribution_clump_fallremap_data"] = psy.s_distribution_clump_fallremap_data
                    d["s_distribution_clump_fallremap_revert"] = psy.s_distribution_clump_fallremap_revert
                    d["s_distribution_clump_fallnoisy_strength"] = psy.s_distribution_clump_fallnoisy_strength
                    d["s_distribution_clump_fallnoisy_space"] = psy.s_distribution_clump_fallnoisy_space
                    d["s_distribution_clump_fallnoisy_scale"] = psy.s_distribution_clump_fallnoisy_scale
                    if use_random_seed: d["s_distribution_clump_fallnoisy_is_random_seed"] = True
                    else: d["s_distribution_clump_fallnoisy_seed"] = psy.s_distribution_clump_fallnoisy_seed

                d["s_distribution_clump_children_density"] = psy.s_distribution_clump_children_density

                if use_random_seed: d["s_distribution_clump_children_is_random_seed"] = True
                else: d["s_distribution_clump_children_seed"] = psy.s_distribution_clump_children_seed

                d["s_distribution_clump_children_limit_distance_allow"] = psy.s_distribution_clump_children_limit_distance_allow
                if psy.s_distribution_clump_children_limit_distance_allow:
                    d["s_distribution_clump_children_limit_distance"] = psy.s_distribution_clump_children_limit_distance

            case 'verts': #Verts Dist
                
                d["s_distribution_vfe_space"] = psy.s_distribution_vfe_space
                
            case 'faces': #Faces Dist 
                
                d["s_distribution_vfe_space"] = psy.s_distribution_vfe_space
                
            case 'edges': #Edges Dist
                
                d["s_distribution_vfe_space"] = psy.s_distribution_vfe_space
                d["s_distribution_edges_selection_method"] = psy.s_distribution_edges_selection_method
                d["s_distribution_edges_position_method"] = psy.s_distribution_edges_position_method

            case 'volume': #Volume Dist
                
                d["s_distribution_volume_space"] = psy.s_distribution_volume_space
                d["s_distribution_volume_voxelsize"] = psy.s_distribution_volume_voxelsize
                d["s_distribution_volume_method"] = psy.s_distribution_volume_method

                match d["s_distribution_volume_method"]:

                    case 'grid':
                        
                        d["s_distribution_volume_grid_spacing"] = psy.s_distribution_volume_grid_spacing
                        
                    case 'random':
                        
                        d["s_distribution_volume_is_count_method"] = psy.s_distribution_volume_is_count_method
                        if (psy.s_distribution_volume_is_count_method=="density"):
                            d["s_distribution_volume_density"] = psy.s_distribution_volume_density
                        else: d["s_distribution_volume_count"] = psy.s_distribution_volume_count

                        d["s_distribution_volume_limit_distance_allow"] = psy.s_distribution_volume_limit_distance_allow
                        if psy.s_distribution_volume_limit_distance_allow:
                            d["s_distribution_volume_limit_distance"] = psy.s_distribution_volume_limit_distance

                        if use_random_seed: d["s_distribution_volume_is_random_seed"] = True
                        else: d["s_distribution_volume_seed"] = psy.s_distribution_volume_seed
                    
            case 'projbezarea': #Project Bezier Area
                
                d["s_distribution_projbezarea_curve_ptr"] = psy.s_distribution_projbezarea_curve_ptr.name if (psy.s_distribution_projbezarea_curve_ptr is not None) else ""
                
                d["s_distribution_projbezarea_space"] = psy.s_distribution_projbezarea_space
                
                d["s_distribution_projbezarea_density"] = psy.s_distribution_projbezarea_density
                if use_random_seed: d["s_distribution_projbezarea_is_random_seed"] = True
                else: d["s_distribution_projbezarea_seed"] = psy.s_distribution_projbezarea_seed

                d["s_distribution_projbezarea_limit_distance_allow"] = psy.s_distribution_projbezarea_limit_distance_allow
                if psy.s_distribution_projbezarea_limit_distance_allow:
                    d["s_distribution_projbezarea_limit_distance"] = psy.s_distribution_projbezarea_limit_distance

                d["s_distribution_projbezarea_projenabled"] = psy.s_distribution_projbezarea_projenabled
                if psy.s_distribution_projbezarea_projenabled:
                    d["s_distribution_projbezarea_projlength"] = psy.s_distribution_projbezarea_projlength
                    d["s_distribution_projbezarea_projaxis"] = psy.s_distribution_projbezarea_projaxis
                
            case 'projbezline': #Project Bezier Line

                d["s_distribution_projbezline_curve_ptr"] = psy.s_distribution_projbezline_curve_ptr.name if (psy.s_distribution_projbezline_curve_ptr is not None) else ""
                
                d["s_distribution_projbezline_space"] = psy.s_distribution_projbezline_space
                d["s_distribution_projbezline_method"] = psy.s_distribution_projbezline_method
                
                d["s_distribution_projbezline_is_count_method"] = psy.s_distribution_projbezline_is_count_method
                if (psy.s_distribution_projbezline_is_count_method=="density"):
                    if (psy.s_distribution_projbezline_method=="onspline"):
                        d["s_distribution_projbezline_onspline_density"] = psy.s_distribution_projbezline_onspline_density
                    elif (psy.s_distribution_projbezline_method=="patharea"):
                        d["s_distribution_projbezline_patharea_density"] = psy.s_distribution_projbezline_patharea_density
                else: d["s_distribution_projbezline_count"] = psy.s_distribution_projbezline_count
                
                if (psy.s_distribution_projbezline_space=="onspline"):
                    
                    d["s_distribution_projbezline_randoff_allow"] = psy.s_distribution_projbezline_randoff_allow
                    if psy.s_distribution_projbezline_randoff_allow:
                        d["s_distribution_projbezline_randoff_dist"] = psy.s_distribution_projbezline_randoff_dist
                        
                        if use_random_seed: d["s_distribution_projbezline_randoff_seed"] = True
                        else: d["s_distribution_projbezline_randoff_is_random_seed"] = psy.s_distribution_projbezline_randoff_is_random_seed
                    
                    d["s_distribution_projbezline_creatrow_allow"] = psy.s_distribution_projbezline_creatrow_allow
                    if psy.s_distribution_projbezline_creatrow_allow:
                        d["s_distribution_projbezline_creatrow_dir"] = psy.s_distribution_projbezline_creatrow_dir
                        d["s_distribution_projbezline_creatrow_rows"] = psy.s_distribution_projbezline_creatrow_rows
                        d["s_distribution_projbezline_creatrow_dist"] = psy.s_distribution_projbezline_creatrow_dist
                        d["s_distribution_projbezline_creatrow_shift"] = psy.s_distribution_projbezline_creatrow_shift
                        
                    d["s_distribution_projbezline_spread_allow"] = psy.s_distribution_projbezline_spread_allow
                    if psy.s_distribution_projbezline_spread_allow:
                        d["s_distribution_projbezline_spread_method"] = psy.s_distribution_projbezline_spread_method
                        d["s_distribution_projbezline_spread_dir"] = psy.s_distribution_projbezline_spread_dir
                        # d["s_distribution_projbezline_spread_offset"] = psy.s_distribution_projbezline_spread_offset
                        d["s_distribution_projbezline_spread_falloff"] = psy.s_distribution_projbezline_spread_falloff
                
                        if use_random_seed: d["s_distribution_projbezline_spread_seed"] = True
                        else: d["s_distribution_projbezline_spread_is_random_seed"] = psy.s_distribution_projbezline_spread_is_random_seed

                elif (psy.s_distribution_projbezline_space=="patharea"):
                    
                    d["s_distribution_projbezline_patharea_width"] = psy.s_distribution_projbezline_patharea_width
                    d["s_distribution_projbezline_patharea_falloff"] = psy.s_distribution_projbezline_patharea_falloff
                    d["s_distribution_projbezline_patharea_seed"] = psy.s_distribution_projbezline_patharea_seed
                    d["s_distribution_projbezline_patharea_is_random_seed"] = psy.s_distribution_projbezline_patharea_is_random_seed

                    d["s_distribution_projbezline_patharea_radiusinfl_allow"] = psy.s_distribution_projbezline_patharea_radiusinfl_allow
                    if psy.s_distribution_projbezline_patharea_radiusinfl_allow:
                        d["s_distribution_projbezline_patharea_radiusinfl_factor"] = psy.s_distribution_projbezline_patharea_radiusinfl_factor

                    d["s_distribution_projbezline_fallremap_allow"] = psy.s_distribution_projbezline_fallremap_allow
                    if psy.s_distribution_projbezline_fallremap_allow:
                        d["s_distribution_projbezline_fallremap_data"] = psy.s_distribution_projbezline_fallremap_data
                        d["s_distribution_projbezline_fallremap_revert"] = psy.s_distribution_projbezline_fallremap_revert
                        d["s_distribution_projbezline_fallnoisy_strength"] = psy.s_distribution_projbezline_fallnoisy_strength
                        d["s_distribution_projbezline_fallnoisy_space"] = psy.s_distribution_projbezline_fallnoisy_space
                        d["s_distribution_projbezline_fallnoisy_scale"] = psy.s_distribution_projbezline_fallnoisy_scale
                        if use_random_seed: d["s_distribution_projbezline_fallnoisy_is_random_seed"] = True
                        else: d["s_distribution_projbezline_fallnoisy_seed"] = psy.s_distribution_projbezline_fallnoisy_seed
                
                d["s_distribution_projbezline_limit_distance_allow"] = psy.s_distribution_projbezline_limit_distance_allow
                if psy.s_distribution_projbezline_limit_distance_allow:
                    d["s_distribution_projbezline_limit_distance"] = psy.s_distribution_projbezline_limit_distance
                
                d["s_distribution_projbezline_projenabled"] = psy.s_distribution_projbezline_projenabled
                if psy.s_distribution_projbezline_projenabled:
                    d["s_distribution_projbezline_projlength"] = psy.s_distribution_projbezline_projlength
                    d["s_distribution_projbezline_projaxis"] = psy.s_distribution_projbezline_projaxis

            case 'projempties': #Project Empties
                
                d["s_distribution_projempties_coll_ptr"] = psy.s_distribution_projempties_coll_ptr
                d["s_distribution_projempties_empty_only"] = psy.s_distribution_projempties_empty_only

                d["s_distribution_projempties_projenabled"] = psy.s_distribution_projempties_projenabled
                if psy.s_distribution_projempties_projenabled:
                    d["s_distribution_projempties_projlength"] = psy.s_distribution_projempties_projlength
                    d["s_distribution_projempties_projaxis"] = psy.s_distribution_projempties_projaxis

    if s_filter.get("s_mask"):
        d[">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> MASK"] = ""

        d["s_mask_master_allow"] = psy.s_mask_master_allow

        #Vgroups 

        d["s_mask_vg_allow"] = psy.s_mask_vg_allow
        if psy.s_mask_vg_allow:
            d["s_mask_vg_ptr"] = psy.s_mask_vg_ptr
            d["s_mask_vg_revert"] = psy.s_mask_vg_revert

        #VColors 

        d["s_mask_vcol_allow"] = psy.s_mask_vcol_allow
        if psy.s_mask_vcol_allow:
            d["s_mask_vcol_ptr"] = psy.s_mask_vcol_ptr
            d["s_mask_vcol_revert"] = psy.s_mask_vcol_revert
            d["s_mask_vcol_color_sample_method"] = psy.s_mask_vcol_color_sample_method
            d["s_mask_vcol_id_color_ptr"] = psy.s_mask_vcol_id_color_ptr

        #Bitmap 

        d["s_mask_bitmap_allow"] = psy.s_mask_bitmap_allow
        if psy.s_mask_bitmap_allow:
            d["s_mask_bitmap_uv_ptr"] = psy.s_mask_bitmap_uv_ptr
            d["s_mask_bitmap_ptr"] = psy.s_mask_bitmap_ptr
            d["s_mask_bitmap_revert"] = psy.s_mask_bitmap_revert
            d["s_mask_bitmap_color_sample_method"] = psy.s_mask_bitmap_color_sample_method
            d["s_mask_bitmap_id_color_ptr"] = psy.s_mask_bitmap_id_color_ptr

        #Curves

        d["s_mask_curve_allow"] = psy.s_mask_curve_allow
        if psy.s_mask_curve_allow:
            d["s_mask_curve_ptr"] = psy.s_mask_curve_ptr.name if (psy.s_mask_curve_ptr is not None) else ""
            d["s_mask_curve_revert"] = psy.s_mask_curve_revert

        #Boolean

        d["s_mask_boolvol_allow"] = psy.s_mask_boolvol_allow
        if psy.s_mask_boolvol_allow:
            d["s_mask_boolvol_coll_ptr"] = psy.s_mask_boolvol_coll_ptr
            d["s_mask_boolvol_revert"] = psy.s_mask_boolvol_revert

        #Material

        d["s_mask_material_allow"] = psy.s_mask_material_allow
        if psy.s_mask_material_allow:
            d["s_mask_material_ptr"] = psy.s_mask_material_ptr
            d["s_mask_material_revert"] = psy.s_mask_material_revert

        #Upward Obstruction

        d["s_mask_upward_allow"] = psy.s_mask_upward_allow
        if psy.s_mask_upward_allow:
            d["s_mask_upward_coll_ptr"] = psy.s_mask_upward_coll_ptr
            d["s_mask_upward_revert"] = psy.s_mask_upward_revert

    if s_filter.get("s_scale"):
        d[">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> SCALE"] = ""

        d["s_scale_master_allow"] = psy.s_scale_master_allow
        
        #Default Scale 

        d["s_scale_default_allow"] = psy.s_scale_default_allow
        if psy.s_scale_default_allow:
            d["s_scale_default_space"] = psy.s_scale_default_space
            d["s_scale_default_value"] = psy.s_scale_default_value
            d["s_scale_default_multiplier"] = psy.s_scale_default_multiplier

        #Random Scale 

        d["s_scale_random_allow"] = psy.s_scale_random_allow
        if psy.s_scale_random_allow:
            d["s_scale_random_factor"] = psy.s_scale_random_factor
            d["s_scale_random_probability"] = psy.s_scale_random_probability
            d["s_scale_random_method"] = psy.s_scale_random_method

            if use_random_seed: d["s_scale_random_is_random_seed"] = True
            else: d["s_scale_random_seed"] = psy.s_scale_random_seed

            save_u_mask_in_dict(category_str="s_scale_random",)
        
        #Shrink 

        d["s_scale_shrink_allow"] = psy.s_scale_shrink_allow
        if psy.s_scale_shrink_allow:
            d["s_scale_shrink_factor"] = psy.s_scale_shrink_factor

            save_u_mask_in_dict(category_str="s_scale_shrink",)

        #Grow 

        d["s_scale_grow_allow"] = psy.s_scale_grow_allow
        if psy.s_scale_grow_allow:
            d["s_scale_grow_factor"] = psy.s_scale_grow_factor

            save_u_mask_in_dict(category_str="s_scale_grow",)
        
        #Distance Fade

        d["s_scale_fading_allow"] = psy.s_scale_fading_allow
        if psy.s_scale_fading_allow:
            d["s_scale_fading_factor"] = psy.s_scale_fading_factor
            d["s_scale_fading_per_cam_data"] = psy.s_scale_fading_per_cam_data
            d["s_scale_fading_distance_min"] = psy.s_scale_fading_distance_min
            d["s_scale_fading_distance_max"] = psy.s_scale_fading_distance_max
            d["s_scale_fading_fallremap_allow"] = psy.s_scale_fading_fallremap_allow
            if psy.s_scale_fading_fallremap_allow:
                d["s_scale_fading_fallremap_data"] = psy.s_scale_fading_fallremap_data
                d["s_scale_fading_fallremap_revert"] = psy.s_scale_fading_fallremap_revert

        #Random Mirror

        d["s_scale_mirror_allow"] = psy.s_scale_mirror_allow
        if psy.s_scale_mirror_allow:
            d["s_scale_mirror_is_x"] = psy.s_scale_mirror_is_x
            d["s_scale_mirror_is_y"] = psy.s_scale_mirror_is_y
            d["s_scale_mirror_is_z"] = psy.s_scale_mirror_is_z

            if use_random_seed: d["s_scale_mirror_is_random_seed"] = True
            else: d["s_scale_mirror_seed"] = psy.s_scale_mirror_seed

            save_u_mask_in_dict(category_str="s_scale_mirror",)

        #Minimal Scale 

        d["s_scale_min_allow"] = psy.s_scale_min_allow
        if psy.s_scale_min_allow:
            d["s_scale_min_method"] = psy.s_scale_min_method
            d["s_scale_min_value"] = psy.s_scale_min_value

        #Clump Distribution Special 

        if (psy.s_distribution_method=="clumping"):

            d["s_scale_clump_allow"] = psy.s_scale_clump_allow
            if psy.s_scale_clump_allow:
                d["s_scale_clump_value"] = psy.s_scale_clump_value

        #Faces Distribution Special 

        elif (psy.s_distribution_method=="faces"):

            d["s_scale_faces_allow"] = psy.s_scale_faces_allow
            if psy.s_scale_faces_allow:
                d["s_scale_faces_value"] = psy.s_scale_faces_value

        #Edges Distribution Special 

        elif (psy.s_distribution_method=="edges"):

            d["s_scale_edges_allow"] = psy.s_scale_edges_allow
            if psy.s_scale_edges_allow:
                d["s_scale_edges_vec_factor"] = psy.s_scale_edges_vec_factor

        #ProjBezLine Distribution Special 

        elif (psy.s_distribution_method=="projbezline"):

            d["s_scale_projbezline_radius_allow"] = psy.s_scale_projbezline_radius_allow
            if psy.s_scale_projbezline_radius_allow:
                d["s_scale_projbezline_radius_value"] = psy.s_scale_projbezline_radius_value

        #ProjEmpties Distribution Special 

        elif (psy.s_distribution_method=="projempties"):

            d["s_scale_projempties_allow"] = psy.s_scale_projempties_allow
            if psy.s_scale_projempties_allow:
                d["s_scale_projempties_value"] = psy.s_scale_projempties_value

    if s_filter.get("s_rot"):
        d[">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ROTATION"] = ""

        d["s_rot_master_allow"] = psy.s_rot_master_allow
        
        #Align Z 

        d["s_rot_align_z_allow"] = psy.s_rot_align_z_allow
        if psy.s_rot_align_z_allow:
            
            if (psy.s_distribution_method=="projbezarea" and not psy.is_using_surf):
                d["s_rot_align_z_method_projbezareanosurf_special"] = psy.s_rot_align_z_method_projbezareanosurf_special
                current_method = psy.s_rot_align_z_method_projbezareanosurf_special
            elif (psy.s_distribution_method=="projbezline" and not psy.is_using_surf):
                d["s_rot_align_z_method_projbezlinenosurf_special"] = psy.s_rot_align_z_method_projbezlinenosurf_special
                current_method = psy.s_rot_align_z_method_projbezlinenosurf_special
            elif (psy.s_distribution_method=="projempties" and not psy.is_using_surf):
                d["s_rot_align_z_method_projemptiesnosurf_special"] = psy.s_rot_align_z_method_projemptiesnosurf_special
                current_method = psy.s_rot_align_z_method_projemptiesnosurf_special
            else: 
                d["s_rot_align_z_method"] = psy.s_rot_align_z_method
                current_method = psy.s_rot_align_z_method

            if psy.s_rot_align_z_influence_allow:
                d["s_rot_align_z_influence_allow"] = True
                d["s_rot_align_z_influence_value"] = psy.s_rot_align_z_influence_value

            if psy.s_rot_align_z_revert:
                d["s_rot_align_z_revert"] = True 

            if (current_method=="meth_align_z_object"):
                if (psy.s_rot_align_z_object is not None):
                    d["s_rot_align_z_object"] = psy.s_rot_align_z_object.name #not a lot of use case for storing an object name tho

            elif (current_method=="meth_align_z_random"):
                if use_random_seed: d["s_rot_align_z_is_random_seed"] = True
                else: d["s_rot_align_z_random_seed"] = psy.s_rot_align_z_random_seed

            elif (current_method=="meth_align_z_normal"):
                if psy.s_rot_align_z_smoothing_allow:
                    d["s_rot_align_z_smoothing_allow"] = True
                    d["s_rot_align_z_smoothing_value"] = psy.s_rot_align_z_smoothing_value
            
            if (psy.s_distribution_method=="clumping"):
                d["s_rot_align_z_clump_allow"] = psy.s_rot_align_z_clump_allow
                if psy.s_rot_align_z_clump_allow:
                    d["s_rot_align_z_clump_value"] = psy.s_rot_align_z_clump_value

        #Align Y

        d["s_rot_align_y_allow"] = psy.s_rot_align_y_allow
        if psy.s_rot_align_y_allow:
            
            if (psy.s_distribution_method=="projbezarea" and not psy.is_using_surf):
                d["s_rot_align_y_method_projbezareanosurf_special"] = psy.s_rot_align_y_method_projbezareanosurf_special
                current_method = psy.s_rot_align_y_method_projbezareanosurf_special
            elif (psy.s_distribution_method=="projbezline" and not psy.is_using_surf):
                d["s_rot_align_y_method_projbezlinenosurf_special"] = psy.s_rot_align_y_method_projbezlinenosurf_special
                current_method = psy.s_rot_align_y_method_projbezlinenosurf_special
            elif (psy.s_distribution_method=="projempties" and not psy.is_using_surf):
                d["s_rot_align_y_method_projemptiesnosurf_special"] = psy.s_rot_align_y_method_projemptiesnosurf_special
                current_method = psy.s_rot_align_y_method_projemptiesnosurf_special
            else: 
                d["s_rot_align_y_method"] = psy.s_rot_align_y_method
                current_method = psy.s_rot_align_y_method
                
            if psy.s_rot_align_y_revert:
                d["s_rot_align_y_revert"] = True 

            if (current_method=="meth_align_y_object"):

                if (psy.s_rot_align_y_object is not None):
                    d["s_rot_align_y_object"] = psy.s_rot_align_z_object.name #not a lot of use case for storing an object name tho

            elif (current_method=="meth_align_y_random"):
                if use_random_seed: d["s_rot_align_y_is_random_seed"] = True
                else: d["s_rot_align_y_random_seed"] = psy.s_rot_align_y_random_seed

            elif (current_method=="meth_align_y_downslope"):
                d["s_rot_align_y_downslope_space"] = psy.s_rot_align_y_downslope_space 
                if psy.s_rot_align_y_downslope_smoothing_allow:
                    d["s_rot_align_y_downslope_smoothing_allow"] = True
                    d["s_rot_align_y_downslope_smoothing_value"] = psy.s_rot_align_y_downslope_smoothing_value
                    
            elif (current_method=="meth_align_y_flow"):
                d["s_rot_align_y_flow_method"] = psy.s_rot_align_y_flow_method
                d["s_rot_align_y_flow_direction"] = psy.s_rot_align_y_flow_direction

                if (psy.s_rot_align_y_flow_method=="flow_vcol"):
                    d["s_rot_align_y_vcol_ptr"] = psy.s_rot_align_y_vcol_ptr

                elif (psy.s_rot_align_y_flow_method=="flow_text"):
                    save_texture_ptr_in_dict(category_str=f"s_rot_align_y", texture_is_unique=texture_is_unique, texture_random_loc=texture_random_loc,)

        #Random Rotation 

        d["s_rot_random_allow"] = psy.s_rot_random_allow
        if psy.s_rot_random_allow:
            d["s_rot_random_tilt_value"] = psy.s_rot_random_tilt_value
            d["s_rot_random_yaw_value"] = psy.s_rot_random_yaw_value

            if use_random_seed: d["s_rot_random_is_random_seed"] = True
            else: d["s_rot_random_seed"] = psy.s_rot_random_seed

            save_u_mask_in_dict(category_str="s_rot_random",)

        #Rotation 

        d["s_rot_add_allow"] = psy.s_rot_add_allow
        if psy.s_rot_add_allow:
            d["s_rot_add_default"] = psy.s_rot_add_default
            d["s_rot_add_random"] = psy.s_rot_add_random

            if use_random_seed: d["s_rot_add_is_random_seed"] = True
            else: d["s_rot_add_seed"] = psy.s_rot_add_seed

            d["s_rot_add_snap"] = psy.s_rot_add_snap

            save_u_mask_in_dict(category_str="s_rot_add",)

        #Flowmap Tilting 

        d["s_rot_tilt_allow"] = psy.s_rot_tilt_allow
        if psy.s_rot_tilt_allow:
            d["s_rot_tilt_dir_method"] = psy.s_rot_tilt_dir_method
            d["s_rot_tilt_method"] = psy.s_rot_tilt_method
            d["s_rot_tilt_force"] = psy.s_rot_tilt_force
            d["s_rot_tilt_blue_influence"] = psy.s_rot_tilt_blue_influence
            d["s_rot_tilt_direction"] = psy.s_rot_tilt_direction
            
            if (psy.s_rot_tilt_dir_method=="noise"):
                d["s_rot_tilt_noise_space"] = psy.s_rot_tilt_noise_space
                d["s_rot_tilt_noise_scale"] = psy.s_rot_tilt_noise_scale

            if (psy.s_rot_tilt_method=="tilt_vcol"):
                d["s_rot_tilt_vcol_ptr"] = psy.s_rot_tilt_vcol_ptr

            elif (psy.s_rot_tilt_method=="tilt_text"):
                save_texture_ptr_in_dict(category_str=f"s_rot_tilt", texture_is_unique=texture_is_unique, texture_random_loc=texture_random_loc,)

            save_u_mask_in_dict(category_str="s_rot_tilt",)

    if s_filter.get("s_pattern"):
        d[">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> PATTERN"] = ""

        d["s_pattern_master_allow"] = psy.s_pattern_master_allow

        for i in (1,2,3):

            d[f"s_pattern{i}_allow"] = getattr(psy, f"s_pattern{i}_allow")
            if d[f"s_pattern{i}_allow"]:

                save_texture_ptr_in_dict(category_str=f"s_pattern{i}", texture_is_unique=texture_is_unique, texture_random_loc=texture_random_loc,)

                d[f"s_pattern{i}_color_sample_method"] = getattr(psy, f"s_pattern{i}_color_sample_method") #will break if no versioning
                if d[f"s_pattern{i}_color_sample_method"]=="id_picker":
                    d[f"s_pattern{i}_id_color_ptr"] = getattr(psy, f"s_pattern{i}_id_color_ptr")
                    d[f"s_pattern{i}_id_color_tolerence"] = getattr(psy, f"s_pattern{i}_id_color_tolerence")

                d[f"s_pattern{i}_dist_infl_allow"] = getattr(psy, f"s_pattern{i}_dist_infl_allow")
                if d[f"s_pattern{i}_dist_infl_allow"]:
                    d[f"s_pattern{i}_dist_influence"] = getattr(psy, f"s_pattern{i}_dist_influence")
                    d[f"s_pattern{i}_dist_revert"] = getattr(psy, f"s_pattern{i}_dist_revert")
                d[f"s_pattern{i}_scale_infl_allow"] = getattr(psy, f"s_pattern{i}_scale_infl_allow")
                if d[f"s_pattern{i}_scale_infl_allow"]:
                    d[f"s_pattern{i}_scale_influence"] = getattr(psy, f"s_pattern{i}_scale_influence")
                    d[f"s_pattern{i}_scale_revert"] = getattr(psy, f"s_pattern{i}_scale_revert")

                save_u_mask_in_dict(category_str=f"s_pattern{i}",)

    if s_filter.get("s_abiotic"):
        d[">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ABIOTIC"] = ""

        d["s_abiotic_master_allow"] = psy.s_abiotic_master_allow

        #Elevation 

        d["s_abiotic_elev_allow"] = psy.s_abiotic_elev_allow
        if psy.s_abiotic_elev_allow:
            d["s_abiotic_elev_space"] = psy.s_abiotic_elev_space
            d["s_abiotic_elev_method"] = psy.s_abiotic_elev_method

            prop_mthd = "local" if (psy.s_abiotic_elev_method =="percentage") else "global"
            d[f"s_abiotic_elev_min_value_{prop_mthd}"] = getattr(psy, f"s_abiotic_elev_min_value_{prop_mthd}")
            d[f"s_abiotic_elev_min_falloff_{prop_mthd}"] = getattr(psy, f"s_abiotic_elev_min_falloff_{prop_mthd}")
            d[f"s_abiotic_elev_max_value_{prop_mthd}"] = getattr(psy, f"s_abiotic_elev_max_value_{prop_mthd}")
            d[f"s_abiotic_elev_max_falloff_{prop_mthd}"] = getattr(psy, f"s_abiotic_elev_max_falloff_{prop_mthd}")

            d["s_abiotic_elev_fallremap_allow"] = psy.s_abiotic_elev_fallremap_allow
            if psy.s_abiotic_elev_fallremap_allow:
                d["s_abiotic_elev_fallremap_data"] = psy.s_abiotic_elev_fallremap_data
                d["s_abiotic_elev_fallremap_revert"] = psy.s_abiotic_elev_fallremap_revert
                d["s_abiotic_elev_fallnoisy_strength"] = psy.s_abiotic_elev_fallnoisy_strength
                d["s_abiotic_elev_fallnoisy_space"] = psy.s_abiotic_elev_fallnoisy_space
                d["s_abiotic_elev_fallnoisy_scale"] = psy.s_abiotic_elev_fallnoisy_scale
                if use_random_seed: d["s_abiotic_elev_fallnoisy_is_random_seed"] = True
                else: d["s_abiotic_elev_fallnoisy_seed"] = psy.s_abiotic_elev_fallnoisy_seed
            
            d["s_abiotic_elev_dist_infl_allow"] = psy.s_abiotic_elev_dist_infl_allow
            if psy.s_abiotic_elev_dist_infl_allow:
                d["s_abiotic_elev_dist_influence"] = psy.s_abiotic_elev_dist_influence
                d["s_abiotic_elev_dist_revert"] = psy.s_abiotic_elev_dist_revert
            d["s_abiotic_elev_scale_infl_allow"] = psy.s_abiotic_elev_scale_infl_allow
            if psy.s_abiotic_elev_scale_infl_allow:
                d["s_abiotic_elev_scale_influence"] = psy.s_abiotic_elev_scale_influence
                d["s_abiotic_elev_scale_revert"] = psy.s_abiotic_elev_scale_revert

            save_u_mask_in_dict(category_str="s_abiotic_elev",)

        #Slope 

        d["s_abiotic_slope_allow"] = psy.s_abiotic_slope_allow
        if psy.s_abiotic_slope_allow:
            d["s_abiotic_slope_space"] = psy.s_abiotic_slope_space
            d["s_abiotic_slope_absolute"] = psy.s_abiotic_slope_absolute

            d["s_abiotic_slope_min_value"] = psy.s_abiotic_slope_min_value
            d["s_abiotic_slope_min_falloff"] = psy.s_abiotic_slope_min_falloff
            d["s_abiotic_slope_max_value"] = psy.s_abiotic_slope_max_value
            d["s_abiotic_slope_max_falloff"] = psy.s_abiotic_slope_max_falloff

            if psy.s_abiotic_slope_smoothing_allow:
                d["s_abiotic_slope_smoothing_allow"] = True
                d["s_abiotic_slope_smoothing_value"] = psy.s_abiotic_slope_smoothing_value

            d["s_abiotic_slope_fallremap_allow"] = psy.s_abiotic_slope_fallremap_allow
            if psy.s_abiotic_slope_fallremap_allow:
                d["s_abiotic_slope_fallremap_data"] = psy.s_abiotic_slope_fallremap_data
                d["s_abiotic_slope_fallremap_revert"] = psy.s_abiotic_slope_fallremap_revert
                d["s_abiotic_slope_fallnoisy_strength"] = psy.s_abiotic_slope_fallnoisy_strength
                d["s_abiotic_slope_fallnoisy_space"] = psy.s_abiotic_slope_fallnoisy_space
                d["s_abiotic_slope_fallnoisy_scale"] = psy.s_abiotic_slope_fallnoisy_scale
                if use_random_seed: d["s_abiotic_slope_fallnoisy_is_random_seed"] = True
                else: d["s_abiotic_slope_fallnoisy_seed"] = psy.s_abiotic_slope_fallnoisy_seed

            d["s_abiotic_slope_dist_infl_allow"] = psy.s_abiotic_slope_dist_infl_allow
            if psy.s_abiotic_slope_dist_infl_allow:
                d["s_abiotic_slope_dist_influence"] = psy.s_abiotic_slope_dist_influence
                d["s_abiotic_slope_dist_revert"] = psy.s_abiotic_slope_dist_revert
            d["s_abiotic_slope_scale_infl_allow"] = psy.s_abiotic_slope_scale_infl_allow
            if psy.s_abiotic_slope_scale_infl_allow:
                d["s_abiotic_slope_scale_influence"] = psy.s_abiotic_slope_scale_influence
                d["s_abiotic_slope_scale_revert"] = psy.s_abiotic_slope_scale_revert

            save_u_mask_in_dict(category_str="s_abiotic_slope",)

        #Orientation 

        d["s_abiotic_dir_allow"] = psy.s_abiotic_dir_allow
        if psy.s_abiotic_dir_allow:
            d["s_abiotic_dir_space"] = psy.s_abiotic_dir_space

            d["s_abiotic_dir_direction"] = psy.s_abiotic_dir_direction
            d["s_abiotic_dir_max"] = psy.s_abiotic_dir_max
            d["s_abiotic_dir_treshold"] = psy.s_abiotic_dir_treshold

            if psy.s_abiotic_dir_smoothing_allow:
                d["s_abiotic_dir_smoothing_allow"] = True
                d["s_abiotic_dir_smoothing_value"] = psy.s_abiotic_dir_smoothing_value

            d["s_abiotic_dir_fallremap_allow"] = psy.s_abiotic_dir_fallremap_allow
            if psy.s_abiotic_dir_fallremap_allow:
                d["s_abiotic_dir_fallremap_data"] = psy.s_abiotic_dir_fallremap_data
                d["s_abiotic_dir_fallremap_revert"] = psy.s_abiotic_dir_fallremap_revert
                d["s_abiotic_dir_fallnoisy_strength"] = psy.s_abiotic_dir_fallnoisy_strength
                d["s_abiotic_dir_fallnoisy_space"] = psy.s_abiotic_dir_fallnoisy_space
                d["s_abiotic_dir_fallnoisy_scale"] = psy.s_abiotic_dir_fallnoisy_scale
                if use_random_seed: d["s_abiotic_dir_fallnoisy_is_random_seed"] = True
                else: d["s_abiotic_dir_fallnoisy_seed"] = psy.s_abiotic_dir_fallnoisy_seed

            d["s_abiotic_dir_dist_infl_allow"] = psy.s_abiotic_dir_dist_infl_allow
            if psy.s_abiotic_dir_dist_infl_allow:
                d["s_abiotic_dir_dist_influence"] = psy.s_abiotic_dir_dist_influence
                d["s_abiotic_dir_dist_revert"] = psy.s_abiotic_dir_dist_revert
            d["s_abiotic_dir_scale_infl_allow"] = psy.s_abiotic_dir_scale_infl_allow
            if psy.s_abiotic_dir_scale_infl_allow:
                d["s_abiotic_dir_scale_influence"] = psy.s_abiotic_dir_scale_influence
                d["s_abiotic_dir_scale_revert"] = psy.s_abiotic_dir_scale_revert

            save_u_mask_in_dict(category_str="s_abiotic_dir",)

        #Curvature

        d["s_abiotic_cur_allow"] = psy.s_abiotic_cur_allow
        if psy.s_abiotic_cur_allow:
            d["s_abiotic_cur_type"] = psy.s_abiotic_cur_type
            d["s_abiotic_cur_max"] = psy.s_abiotic_cur_max
            d["s_abiotic_cur_treshold"] = psy.s_abiotic_cur_treshold
            
            if psy.s_abiotic_cur_smoothing_allow:
                d["s_abiotic_cur_smoothing_allow"] = True
                d["s_abiotic_cur_smoothing_value"] = psy.s_abiotic_cur_smoothing_value
            
            d["s_abiotic_cur_fallremap_allow"] = psy.s_abiotic_cur_fallremap_allow
            if psy.s_abiotic_cur_fallremap_allow:
                d["s_abiotic_cur_fallremap_data"] = psy.s_abiotic_cur_fallremap_data
                d["s_abiotic_cur_fallremap_revert"] = psy.s_abiotic_cur_fallremap_revert
                d["s_abiotic_cur_fallnoisy_strength"] = psy.s_abiotic_cur_fallnoisy_strength
                d["s_abiotic_cur_fallnoisy_space"] = psy.s_abiotic_cur_fallnoisy_space
                d["s_abiotic_cur_fallnoisy_scale"] = psy.s_abiotic_cur_fallnoisy_scale
                if use_random_seed: d["s_abiotic_cur_fallnoisy_is_random_seed"] = True
                else: d["s_abiotic_cur_fallnoisy_seed"] = psy.s_abiotic_cur_fallnoisy_seed

            d["s_abiotic_cur_dist_infl_allow"] = psy.s_abiotic_cur_dist_infl_allow
            if psy.s_abiotic_cur_dist_infl_allow:
                d["s_abiotic_cur_dist_influence"] = psy.s_abiotic_cur_dist_influence
                d["s_abiotic_cur_dist_revert"] = psy.s_abiotic_cur_dist_revert
            d["s_abiotic_cur_scale_infl_allow"] = psy.s_abiotic_cur_scale_infl_allow
            if psy.s_abiotic_cur_scale_infl_allow:
                d["s_abiotic_cur_scale_influence"] = psy.s_abiotic_cur_scale_influence
                d["s_abiotic_cur_scale_revert"] = psy.s_abiotic_cur_scale_revert

            save_u_mask_in_dict(category_str="s_abiotic_cur",)

        #Border

        d["s_abiotic_border_allow"] = psy.s_abiotic_border_allow
        if psy.s_abiotic_border_allow:
            d["s_abiotic_border_space"] = psy.s_abiotic_border_space
            d["s_abiotic_border_max"] = psy.s_abiotic_border_max
            d["s_abiotic_border_treshold"] = psy.s_abiotic_border_treshold

            d["s_abiotic_border_fallremap_allow"] = psy.s_abiotic_border_fallremap_allow
            if psy.s_abiotic_border_fallremap_allow:
                d["s_abiotic_border_fallremap_data"] = psy.s_abiotic_border_fallremap_data
                d["s_abiotic_border_fallremap_revert"] = psy.s_abiotic_border_fallremap_revert
                d["s_abiotic_border_fallnoisy_strength"] = psy.s_abiotic_border_fallnoisy_strength
                d["s_abiotic_border_fallnoisy_space"] = psy.s_abiotic_border_fallnoisy_space
                d["s_abiotic_border_fallnoisy_scale"] = psy.s_abiotic_border_fallnoisy_scale
                if use_random_seed: d["s_abiotic_border_fallnoisy_is_random_seed"] = True
                else: d["s_abiotic_border_fallnoisy_seed"] = psy.s_abiotic_border_fallnoisy_seed

            d["s_abiotic_border_dist_infl_allow"] = psy.s_abiotic_border_dist_infl_allow
            if psy.s_abiotic_border_dist_infl_allow:
                d["s_abiotic_border_dist_influence"] = psy.s_abiotic_border_dist_influence
                d["s_abiotic_border_dist_revert"] = psy.s_abiotic_border_dist_revert
            d["s_abiotic_border_scale_infl_allow"] = psy.s_abiotic_border_scale_infl_allow
            if psy.s_abiotic_border_scale_infl_allow:
                d["s_abiotic_border_scale_influence"] = psy.s_abiotic_border_scale_influence
                d["s_abiotic_border_scale_revert"] = psy.s_abiotic_border_scale_revert

            save_u_mask_in_dict(category_str="s_abiotic_border",)

    if s_filter.get("s_proximity"):
        d[">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> PROXIMITY"] = ""

        d["s_proximity_master_allow"] = psy.s_proximity_master_allow

        #ProjBezArea Border
        
        if psy.s_distribution_method=="projbezarea":
            
            d["s_proximity_projbezarea_border_allow"] = psy.s_proximity_projbezarea_border_allow
            if psy.s_proximity_projbezarea_border_allow:
                d["s_proximity_projbezarea_border_max"] = psy.s_proximity_projbezarea_border_max
                d["s_proximity_projbezarea_border_treshold"] = psy.s_proximity_projbezarea_border_treshold

                d["s_proximity_projbezarea_border_fallremap_allow"] = psy.s_proximity_projbezarea_border_fallremap_allow
                if psy.s_proximity_projbezarea_border_fallremap_allow:
                    d["s_proximity_projbezarea_border_fallremap_data"] = psy.s_proximity_projbezarea_border_fallremap_data
                    d["s_proximity_projbezarea_border_fallremap_revert"] = psy.s_proximity_projbezarea_border_fallremap_revert
                    d["s_proximity_projbezarea_border_fallnoisy_strength"] = psy.s_proximity_projbezarea_border_fallnoisy_strength
                    d["s_proximity_projbezarea_border_fallnoisy_space"] = psy.s_proximity_projbezarea_border_fallnoisy_space
                    d["s_proximity_projbezarea_border_fallnoisy_scale"] = psy.s_proximity_projbezarea_border_fallnoisy_scale
                    if use_random_seed: d["s_proximity_projbezarea_border_fallnoisy_is_random_seed"] = True
                    else: d["s_proximity_projbezarea_border_fallnoisy_seed"] = psy.s_proximity_projbezarea_border_fallnoisy_seed

                d["s_proximity_projbezarea_border_dist_infl_allow"] = psy.s_proximity_projbezarea_border_dist_infl_allow
                if psy.s_proximity_projbezarea_border_dist_infl_allow:
                    d["s_proximity_projbezarea_border_dist_influence"] = psy.s_proximity_projbezarea_border_dist_influence
                    d["s_proximity_projbezarea_border_dist_revert"] = psy.s_proximity_projbezarea_border_dist_revert
                d["s_proximity_projbezarea_border_scale_infl_allow"] = psy.s_proximity_projbezarea_border_scale_infl_allow
                if psy.s_proximity_projbezarea_border_scale_infl_allow:
                    d["s_proximity_projbezarea_border_scale_influence"] = psy.s_proximity_projbezarea_border_scale_influence
                    d["s_proximity_projbezarea_border_scale_revert"] = psy.s_proximity_projbezarea_border_scale_revert
                
        #Object-Repel 1&2
        
        for i in (1,2):

            d[f"s_proximity_repel{i}_allow"] = getattr(psy,f"s_proximity_repel{i}_allow")
            if d[f"s_proximity_repel{i}_allow"]:

                d[f"s_proximity_repel{i}_type"] = getattr(psy,f"s_proximity_repel{i}_type")
                d[f"s_proximity_repel{i}_max"] = getattr(psy,f"s_proximity_repel{i}_max")
                d[f"s_proximity_repel{i}_treshold"] = getattr(psy,f"s_proximity_repel{i}_treshold")

                d[f"s_proximity_repel{i}_volume_allow"] = getattr(psy,f"s_proximity_repel{i}_volume_allow")
                d[f"s_proximity_repel{i}_volume_method"] = getattr(psy,f"s_proximity_repel{i}_volume_method")

                d[f"s_proximity_repel{i}_fallremap_allow"] = getattr(psy,f"s_proximity_repel{i}_fallremap_allow")
                if d[f"s_proximity_repel{i}_fallremap_allow"]:
                    d[f"s_proximity_repel{i}_fallremap_data"] = getattr(psy,f"s_proximity_repel{i}_fallremap_data")
                    d[f"s_proximity_repel{i}_fallremap_revert"] = getattr(psy,f"s_proximity_repel{i}_fallremap_revert")
                    d[f"s_proximity_repel{i}_fallnoisy_strength"] = getattr(psy,f"s_proximity_repel{i}_fallnoisy_strength")
                    d[f"s_proximity_repel{i}_fallnoisy_space"] = getattr(psy,f"s_proximity_repel{i}_fallnoisy_space")
                    d[f"s_proximity_repel{i}_fallnoisy_scale"] = getattr(psy,f"s_proximity_repel{i}_fallnoisy_scale")
                    if use_random_seed: d[f"s_proximity_repel{i}_fallnoisy_is_random_seed"] = True
                    else: d[f"s_proximity_repel{i}_fallnoisy_seed"] = getattr(psy,f"s_proximity_repel{i}_fallnoisy_seed")

                d[f"s_proximity_repel{i}_simulation_allow"] = getattr(psy,f"s_proximity_repel{i}_simulation_allow")
                if d[f"s_proximity_repel{i}_simulation_allow"]:
                    d[f"s_proximity_repel{i}_simulation_fadeaway_allow"] = getattr(psy,f"s_proximity_repel{i}_simulation_fadeaway_allow")
                    if d[f"s_proximity_repel{i}_simulation_fadeaway_allow"]:
                        d[f"s_proximity_repel{i}_simulation_fadeaway_method"] = getattr(psy,f"s_proximity_repel{i}_simulation_fadeaway_method")
                        d[f"s_proximity_repel{i}_simulation_fadeaway_frame"] = getattr(psy,f"s_proximity_repel{i}_simulation_fadeaway_frame")
                        d[f"s_proximity_repel{i}_simulation_fadeaway_sec"] = getattr(psy,f"s_proximity_repel{i}_simulation_fadeaway_sec")

                d[f"s_proximity_repel{i}_dist_infl_allow"] = getattr(psy,f"s_proximity_repel{i}_dist_infl_allow")
                if d[f"s_proximity_repel{i}_dist_infl_allow"]:
                    d[f"s_proximity_repel{i}_dist_influence"] = getattr(psy,f"s_proximity_repel{i}_dist_influence")
                    d[f"s_proximity_repel{i}_dist_revert"] = getattr(psy,f"s_proximity_repel{i}_dist_revert")
                d[f"s_proximity_repel{i}_scale_infl_allow"] = getattr(psy,f"s_proximity_repel{i}_scale_infl_allow")
                if d[f"s_proximity_repel{i}_scale_infl_allow"]:
                    d[f"s_proximity_repel{i}_scale_influence"] = getattr(psy,f"s_proximity_repel{i}_scale_influence")
                    d[f"s_proximity_repel{i}_scale_revert"] = getattr(psy,f"s_proximity_repel{i}_scale_revert")
                d[f"s_proximity_repel{i}_nor_infl_allow"] = getattr(psy,f"s_proximity_repel{i}_nor_infl_allow")
                if d[f"s_proximity_repel{i}_nor_infl_allow"]:
                    d[f"s_proximity_repel{i}_nor_influence"] = getattr(psy,f"s_proximity_repel{i}_nor_influence")
                    d[f"s_proximity_repel{i}_nor_revert"] = getattr(psy,f"s_proximity_repel{i}_nor_revert")
                d[f"s_proximity_repel{i}_tan_infl_allow"] = getattr(psy,f"s_proximity_repel{i}_tan_infl_allow")
                if d[f"s_proximity_repel{i}_tan_infl_allow"]:
                    d[f"s_proximity_repel{i}_tan_influence"] = getattr(psy,f"s_proximity_repel{i}_tan_influence")
                    d[f"s_proximity_repel{i}_tan_revert"] = getattr(psy,f"s_proximity_repel{i}_tan_revert")

                d[f"s_proximity_repel{i}_coll_ptr"] = getattr(psy,f"s_proximity_repel{i}_coll_ptr")

                save_u_mask_in_dict(category_str=f"s_proximity_repel{i}",)

        #Outskirt

        d["s_proximity_outskirt_allow"] = psy.s_proximity_outskirt_allow
        if psy.s_proximity_outskirt_allow:
            
            d["s_proximity_outskirt_detection"] = psy.s_proximity_outskirt_detection
            d["s_proximity_outskirt_precision"] = psy.s_proximity_outskirt_precision
            d["s_proximity_outskirt_max"] = psy.s_proximity_outskirt_max
            d["s_proximity_outskirt_treshold"] = psy.s_proximity_outskirt_treshold

            d[f"s_proximity_outskirt_fallremap_allow"] = getattr(psy,f"s_proximity_outskirt_fallremap_allow")
            if d[f"s_proximity_outskirt_fallremap_allow"]:
                d[f"s_proximity_outskirt_fallremap_data"] = getattr(psy,f"s_proximity_outskirt_fallremap_data")
                d[f"s_proximity_outskirt_fallremap_revert"] = getattr(psy,f"s_proximity_outskirt_fallremap_revert")
                d[f"s_proximity_outskirt_fallnoisy_strength"] = getattr(psy,f"s_proximity_outskirt_fallnoisy_strength")
                d[f"s_proximity_outskirt_fallnoisy_space"] = getattr(psy,f"s_proximity_outskirt_fallnoisy_space")
                d[f"s_proximity_outskirt_fallnoisy_scale"] = getattr(psy,f"s_proximity_outskirt_fallnoisy_scale")
                if use_random_seed: d[f"s_proximity_outskirt_fallnoisy_is_random_seed"] = True
                else: d[f"s_proximity_outskirt_fallnoisy_seed"] = getattr(psy,f"s_proximity_outskirt_fallnoisy_seed")

            d[f"s_proximity_outskirt_dist_infl_allow"] = getattr(psy,f"s_proximity_outskirt_dist_infl_allow")
            if d[f"s_proximity_outskirt_dist_infl_allow"]:
                d[f"s_proximity_outskirt_dist_influence"] = getattr(psy,f"s_proximity_outskirt_dist_influence")
                d[f"s_proximity_outskirt_dist_revert"] = getattr(psy,f"s_proximity_outskirt_dist_revert")
            d[f"s_proximity_outskirt_scale_infl_allow"] = getattr(psy,f"s_proximity_outskirt_scale_infl_allow")
            if d[f"s_proximity_outskirt_scale_infl_allow"]:
                d[f"s_proximity_outskirt_scale_influence"] = getattr(psy,f"s_proximity_outskirt_scale_influence")
                d[f"s_proximity_outskirt_scale_revert"] = getattr(psy,f"s_proximity_outskirt_scale_revert")
            # d[f"s_proximity_outskirt_nor_infl_allow"] = getattr(psy,f"s_proximity_outskirt_nor_infl_allow")
            # if d[f"s_proximity_outskirt_nor_infl_allow"]:
            #     d[f"s_proximity_outskirt_nor_influence"] = getattr(psy,f"s_proximity_outskirt_nor_influence")
            #     d[f"s_proximity_outskirt_nor_revert"] = getattr(psy,f"s_proximity_outskirt_nor_revert")
            # d[f"s_proximity_outskirt_tan_infl_allow"] = getattr(psy,f"s_proximity_outskirt_tan_infl_allow")
            # if d[f"s_proximity_outskirt_tan_infl_allow"]:
            #     d[f"s_proximity_outskirt_tan_influence"] = getattr(psy,f"s_proximity_outskirt_tan_influence")
            #     d[f"s_proximity_outskirt_tan_revert"] = getattr(psy,f"s_proximity_outskirt_tan_revert")

            save_u_mask_in_dict(category_str="s_proximity_outskirt",)

    if s_filter.get("s_ecosystem"):
        d[">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ECOSYSTEM"] = ""

        d["s_ecosystem_master_allow"] = psy.s_ecosystem_master_allow

        #Affinity

        d["s_ecosystem_affinity_allow"] = psy.s_ecosystem_affinity_allow
        if psy.s_ecosystem_affinity_allow:

            d["s_ecosystem_affinity_space"] = psy.s_ecosystem_affinity_space

            for i in (1,2,3):
                d[f"s_ecosystem_affinity_{i:02}_ptr"] = getattr(psy, f"s_ecosystem_affinity_{i:02}_ptr")
                if (getattr(psy, f"s_ecosystem_affinity_{i:02}_ptr")!=""):

                    d[f"s_ecosystem_affinity_{i:02}_type"] = getattr(psy, f"s_ecosystem_affinity_{i:02}_type")
                    d[f"s_ecosystem_affinity_{i:02}_max_value"] = getattr(psy, f"s_ecosystem_affinity_{i:02}_max_value")
                    d[f"s_ecosystem_affinity_{i:02}_max_falloff"] = getattr(psy, f"s_ecosystem_affinity_{i:02}_max_falloff")
                    d[f"s_ecosystem_affinity_{i:02}_limit_distance"] = getattr(psy, f"s_ecosystem_affinity_{i:02}_limit_distance")

            d["s_ecosystem_affinity_fallremap_allow"] = psy.s_ecosystem_affinity_fallremap_allow
            if psy.s_ecosystem_affinity_fallremap_allow:
                d["s_ecosystem_affinity_fallremap_data"] = psy.s_ecosystem_affinity_fallremap_data
                d["s_ecosystem_affinity_fallremap_revert"] = psy.s_ecosystem_affinity_fallremap_revert
                d["s_ecosystem_affinity_fallnoisy_strength"] = psy.s_ecosystem_affinity_fallnoisy_strength
                d["s_ecosystem_affinity_fallnoisy_space"] = psy.s_ecosystem_affinity_fallnoisy_space
                d["s_ecosystem_affinity_fallnoisy_scale"] = psy.s_ecosystem_affinity_fallnoisy_scale
                if use_random_seed: d["s_ecosystem_affinity_fallnoisy_is_random_seed"] = True
                else: d["s_ecosystem_affinity_fallnoisy_seed"] = psy.s_ecosystem_affinity_fallnoisy_seed

            d["s_ecosystem_affinity_dist_infl_allow"] = psy.s_ecosystem_affinity_dist_infl_allow
            if psy.s_ecosystem_affinity_dist_infl_allow:
                d["s_ecosystem_affinity_dist_influence"] = psy.s_ecosystem_affinity_dist_influence
            d["s_ecosystem_affinity_scale_infl_allow"] = psy.s_ecosystem_affinity_scale_infl_allow
            if psy.s_ecosystem_affinity_scale_infl_allow:
                d["s_ecosystem_affinity_scale_influence"] = psy.s_ecosystem_affinity_scale_influence

            save_u_mask_in_dict(category_str="s_ecosystem_affinity",)

        #Repulsion

        d["s_ecosystem_repulsion_allow"] = psy.s_ecosystem_repulsion_allow
        if psy.s_ecosystem_repulsion_allow:

            d["s_ecosystem_repulsion_space"] = psy.s_ecosystem_repulsion_space

            for i in (1,2,3):
                d[f"s_ecosystem_repulsion_{i:02}_ptr"] = getattr(psy, f"s_ecosystem_repulsion_{i:02}_ptr")
                if (d[f"s_ecosystem_repulsion_{i:02}_ptr"]!=""):

                    d[f"s_ecosystem_repulsion_{i:02}_type"] = getattr(psy, f"s_ecosystem_repulsion_{i:02}_type")
                    d[f"s_ecosystem_repulsion_{i:02}_max_value"] = getattr(psy, f"s_ecosystem_repulsion_{i:02}_max_value")
                    d[f"s_ecosystem_repulsion_{i:02}_max_falloff"] = getattr(psy, f"s_ecosystem_repulsion_{i:02}_max_falloff")

            d["s_ecosystem_repulsion_fallremap_allow"] = psy.s_ecosystem_repulsion_fallremap_allow
            if psy.s_ecosystem_repulsion_fallremap_allow:
                d["s_ecosystem_repulsion_fallremap_data"] = psy.s_ecosystem_repulsion_fallremap_data
                d["s_ecosystem_repulsion_fallremap_revert"] = psy.s_ecosystem_repulsion_fallremap_revert
                d["s_ecosystem_repulsion_fallnoisy_strength"] = psy.s_ecosystem_repulsion_fallnoisy_strength
                d["s_ecosystem_repulsion_fallnoisy_space"] = psy.s_ecosystem_repulsion_fallnoisy_space
                d["s_ecosystem_repulsion_fallnoisy_scale"] = psy.s_ecosystem_repulsion_fallnoisy_scale
                if use_random_seed: d["s_ecosystem_repulsion_fallnoisy_is_random_seed"] = True
                else: d["s_ecosystem_repulsion_fallnoisy_seed"] = psy.s_ecosystem_repulsion_fallnoisy_seed

            d["s_ecosystem_repulsion_dist_infl_allow"] = psy.s_ecosystem_repulsion_dist_infl_allow
            if psy.s_ecosystem_repulsion_dist_infl_allow:
                d["s_ecosystem_repulsion_dist_influence"] = psy.s_ecosystem_repulsion_dist_influence
            d["s_ecosystem_repulsion_scale_infl_allow"] = psy.s_ecosystem_repulsion_scale_infl_allow
            if psy.s_ecosystem_repulsion_scale_infl_allow:
                d["s_ecosystem_repulsion_scale_influence"] = psy.s_ecosystem_repulsion_scale_influence

            save_u_mask_in_dict(category_str="s_ecosystem_repulsion",)

        #Density
        
        d["s_ecosystem_density_allow"] = psy.s_ecosystem_density_allow
        if psy.s_ecosystem_density_allow:
            
            d["s_ecosystem_density_space"] = psy.s_ecosystem_density_space
            d["s_ecosystem_density_method"] = psy.s_ecosystem_density_method
            d["s_ecosystem_density_voxelsize"] = psy.s_ecosystem_density_voxelsize
            d["s_ecosystem_density_min"] = psy.s_ecosystem_density_min
            d["s_ecosystem_density_falloff"] = psy.s_ecosystem_density_falloff
            
            for i in (1,2,3):
                d[f"s_ecosystem_density_{i:02}_ptr"] = getattr(psy, f"s_ecosystem_density_{i:02}_ptr")
            
            d["s_ecosystem_density_fallremap_allow"] = psy.s_ecosystem_density_fallremap_allow
            if psy.s_ecosystem_density_fallremap_allow:
                d["s_ecosystem_density_fallremap_data"] = psy.s_ecosystem_density_fallremap_data
                d["s_ecosystem_density_fallremap_revert"] = psy.s_ecosystem_density_fallremap_revert
                d["s_ecosystem_density_fallnoisy_strength"] = psy.s_ecosystem_density_fallnoisy_strength
                d["s_ecosystem_density_fallnoisy_space"] = psy.s_ecosystem_density_fallnoisy_space
                d["s_ecosystem_density_fallnoisy_scale"] = psy.s_ecosystem_density_fallnoisy_scale
                if use_random_seed: d["s_ecosystem_density_fallnoisy_is_random_seed"] = True
                else: d["s_ecosystem_density_fallnoisy_seed"] = psy.s_ecosystem_density_fallnoisy_seed

            d["s_ecosystem_density_dist_infl_allow"] = psy.s_ecosystem_density_dist_infl_allow
            if psy.s_ecosystem_density_dist_infl_allow:
                d["s_ecosystem_density_dist_influence"] = psy.s_ecosystem_density_dist_influence
            d["s_ecosystem_density_scale_infl_allow"] = psy.s_ecosystem_density_scale_infl_allow
            if psy.s_ecosystem_density_scale_infl_allow:
                d["s_ecosystem_density_scale_influence"] = psy.s_ecosystem_density_scale_influence
                
            save_u_mask_in_dict(category_str="s_ecosystem_density",)

            
    if s_filter.get("s_push"):
        d[">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> OFFSET"] = ""

        d["s_push_master_allow"] = psy.s_push_master_allow

        #Push Offset 

        d["s_push_offset_allow"] = psy.s_push_offset_allow
        if psy.s_push_offset_allow:
            d["s_push_offset_space"] = psy.s_push_offset_space
            d["s_push_offset_add_value"] = psy.s_push_offset_add_value
            d["s_push_offset_add_random"] = psy.s_push_offset_add_random
            d["s_push_offset_rotate_value"] = psy.s_push_offset_rotate_value
            d["s_push_offset_rotate_random"] = psy.s_push_offset_rotate_random
            d["s_push_offset_scale_value"] = psy.s_push_offset_scale_value
            d["s_push_offset_scale_random"] = psy.s_push_offset_scale_random

            if use_random_seed: d["s_push_offset_is_random_seed"] = True
            else: d["s_push_offset_seed"] = getattr(psy,"s_push_offset_seed")

            save_u_mask_in_dict(category_str="s_push_offset",)

        #Push

        d["s_push_dir_allow"] = psy.s_push_dir_allow
        if psy.s_push_dir_allow:
            
            d["s_push_dir_space"] = psy.s_push_dir_space
            
            if (psy.s_distribution_method=="projbezarea" and not psy.is_using_surf):
                d["s_push_dir_method_projbezareanosurf_special"] = psy.s_push_dir_method_projbezareanosurf_special
            elif (psy.s_distribution_method=="projbezline" and not psy.is_using_surf):
                d["s_push_dir_method_projbezlinenosurf_special"] = psy.s_push_dir_method_projbezlinenosurf_special
            elif (psy.s_distribution_method=="projempties" and not psy.is_using_surf):
                d["s_push_dir_method_projemptiesnosurf_special"] = psy.s_push_dir_method_projemptiesnosurf_special
            else: 
                d["s_push_dir_method"] = psy.s_push_dir_method
                            
            d["s_push_dir_add_value"] = psy.s_push_dir_add_value
            d["s_push_dir_add_random"] = psy.s_push_dir_add_random

            if use_random_seed: d["s_push_dir_is_random_seed"] = True
            else: d["s_push_dir_seed"] = getattr(psy,"s_push_dir_seed")

            save_u_mask_in_dict(category_str="s_push_dir",)

        #Noise
        
        d["s_push_noise_allow"] = psy.s_push_noise_allow
        if psy.s_push_noise_allow:
            d["s_push_noise_space"] = psy.s_push_noise_space
            d["s_push_noise_vector"] = psy.s_push_noise_vector
            d["s_push_noise_is_animated"] = psy.s_push_noise_is_animated
            d["s_push_noise_speed"] = psy.s_push_noise_speed
            
            if use_random_seed: d["s_push_noise_is_random_seed"] = True
            else: d["s_push_noise_seed"] = getattr(psy,"s_push_noise_seed")
            
            save_u_mask_in_dict(category_str="s_push_noise",)

        #Falling
        
        d["s_push_fall_allow"] = psy.s_push_fall_allow
        if psy.s_push_fall_allow:
            d["s_push_fall_space"] = psy.s_push_fall_space
            d["s_push_fall_height"] = psy.s_push_fall_height
            d["s_push_fall_key1_pos"] = psy.s_push_fall_key1_pos
            d["s_push_fall_key1_height"] = psy.s_push_fall_key1_height
            d["s_push_fall_key2_pos"] = psy.s_push_fall_key2_pos
            d["s_push_fall_key2_height"] = psy.s_push_fall_key2_height
            d["s_push_fall_stop_when_initial_z"] = psy.s_push_fall_stop_when_initial_z
        
            d["s_push_fall_turbulence_allow"] = psy.s_push_fall_turbulence_allow
            if psy.s_push_fall_turbulence_allow:
                
                d["s_push_fall_turbulence_spread"] = psy.s_push_fall_turbulence_spread
                d["s_push_fall_turbulence_speed"] = psy.s_push_fall_turbulence_speed
                d["s_push_fall_turbulence_rot_vector"] = psy.s_push_fall_turbulence_rot_vector
                d["s_push_fall_turbulence_rot_factor"] = psy.s_push_fall_turbulence_rot_factor

            if use_random_seed: d["s_push_fall_is_random_seed"] = True
            else: d["s_push_fall_seed"] = getattr(psy,"s_push_fall_seed")

            save_u_mask_in_dict(category_str="s_push_fall",)

    if s_filter.get("s_wind"):
        d[">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> WIND"] = ""

        d["s_wind_master_allow"] = psy.s_wind_master_allow

        #Wind Wave 

        d["s_wind_wave_allow"] = psy.s_wind_wave_allow
        if psy.s_wind_wave_allow:
            d["s_wind_wave_space"] = psy.s_wind_wave_space
            d["s_wind_wave_method"] = psy.s_wind_wave_method

            if (psy.s_wind_wave_method=="wind_wave_loopable"):
                d["s_wind_wave_loopable_cliplength_allow"] = psy.s_wind_wave_loopable_cliplength_allow
                if psy.s_wind_wave_loopable_cliplength_allow:
                    d["s_wind_wave_loopable_frame_start"] = psy.s_wind_wave_loopable_frame_start
                    d["s_wind_wave_loopable_frame_end"] = psy.s_wind_wave_loopable_frame_end

            d["s_wind_wave_speed"] = psy.s_wind_wave_speed
            d["s_wind_wave_force"] = psy.s_wind_wave_force
            
            d["s_wind_wave_swinging"] = psy.s_wind_wave_swinging
            d["s_wind_wave_swinging_factor"] = psy.s_wind_wave_swinging_factor
            
            d["s_wind_wave_scale_influence"] = psy.s_wind_wave_scale_influence
            d["s_wind_wave_scale_influence_factor"] = psy.s_wind_wave_scale_influence_factor

            d["s_wind_wave_texture_scale"] = psy.s_wind_wave_texture_scale
            d["s_wind_wave_texture_turbulence"] = psy.s_wind_wave_texture_turbulence
            d["s_wind_wave_texture_distorsion"] = psy.s_wind_wave_texture_distorsion
            d["s_wind_wave_texture_brightness"] = psy.s_wind_wave_texture_brightness
            d["s_wind_wave_texture_contrast"] = psy.s_wind_wave_texture_contrast

            d["s_wind_wave_dir_method"] = psy.s_wind_wave_dir_method

            if (psy.s_wind_wave_dir_method=="vcol"):
                d["s_wind_wave_flowmap_ptr"] = psy.s_wind_wave_flowmap_ptr
                d["s_wind_wave_direction"] = psy.s_wind_wave_direction

            elif (psy.s_wind_wave_dir_method=="fixed"):
                d["s_wind_wave_direction"] = psy.s_wind_wave_direction
                d["s_wind_wave_direction_random"] = psy.s_wind_wave_direction_random
            
            save_u_mask_in_dict(category_str="s_wind_wave",)

        #Wind Noise 

        d["s_wind_noise_allow"] = psy.s_wind_noise_allow
        if psy.s_wind_noise_allow:
            d["s_wind_noise_space"] = psy.s_wind_noise_space
            d["s_wind_noise_method"] = psy.s_wind_noise_method

            if (psy.s_wind_noise_method=="wind_noise_loopable"):
                d["s_wind_noise_loopable_cliplength_allow"] = psy.s_wind_noise_loopable_cliplength_allow
                if psy.s_wind_noise_loopable_cliplength_allow:
                    d["s_wind_noise_loopable_frame_start"] = psy.s_wind_noise_loopable_frame_start
                    d["s_wind_noise_loopable_frame_end"] = psy.s_wind_noise_loopable_frame_end

            d["s_wind_noise_force"] = psy.s_wind_noise_force
            d["s_wind_noise_speed"] = psy.s_wind_noise_speed

            save_u_mask_in_dict(category_str="s_wind_noise",)

    if s_filter.get("s_visibility"):
        d[">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> VISIBILITY"] = ""

        d["s_visibility_master_allow"] = psy.s_visibility_master_allow

        #Face Preview 

        d["s_visibility_facepreview_allow"] = psy.s_visibility_facepreview_allow
        if psy.s_visibility_facepreview_allow:
            d["s_visibility_facepreview_viewport_method"] = psy.s_visibility_facepreview_viewport_method

        #Visibility Percentage

        d["s_visibility_view_allow"] = psy.s_visibility_view_allow
        if psy.s_visibility_view_allow:
            d["s_visibility_view_percentage"] = psy.s_visibility_view_percentage
            d["s_visibility_view_viewport_method"] = psy.s_visibility_view_viewport_method
            
        #Visibility Camera Optimization 

        d["s_visibility_cam_allow"] = psy.s_visibility_cam_allow
        if psy.s_visibility_cam_allow:
            
            d["s_visibility_cam_predist_allow"] = psy.s_visibility_cam_predist_allow
            
            d["s_visibility_camclip_allow"] = psy.s_visibility_camclip_allow
            if psy.s_visibility_camclip_allow:
                d["s_visibility_camclip_cam_autofill"] = psy.s_visibility_camclip_cam_autofill
                if not psy.s_visibility_camclip_cam_autofill:
                    d["s_visibility_camclip_cam_lens"] = psy.s_visibility_camclip_cam_lens
                    d["s_visibility_camclip_cam_sensor_width"] = psy.s_visibility_camclip_cam_sensor_width
                    d["s_visibility_camclip_cam_res_xy"] = psy.s_visibility_camclip_cam_res_xy
                    d["s_visibility_camclip_cam_shift_xy"] = psy.s_visibility_camclip_cam_shift_xy
                d["s_visibility_camclip_cam_boost_xy"] = psy.s_visibility_camclip_cam_boost_xy
                d["s_visibility_camclip_proximity_allow"] = psy.s_visibility_camclip_proximity_allow
                if psy.s_visibility_camclip_proximity_allow:
                    d["s_visibility_camclip_proximity_distance"] = psy.s_visibility_camclip_proximity_distance

            d["s_visibility_camdist_allow"] = psy.s_visibility_camdist_allow
            if psy.s_visibility_camdist_allow:
                d["s_visibility_camdist_fallremap_allow"] = psy.s_visibility_camdist_fallremap_allow
                if psy.s_visibility_camdist_fallremap_allow:
                    d["s_visibility_camdist_fallremap_data"] = psy.s_visibility_camdist_fallremap_data
                    d["s_visibility_camdist_fallremap_revert"] = psy.s_visibility_camdist_fallremap_revert
                d["s_visibility_camdist_per_cam_data"] = psy.s_visibility_camdist_per_cam_data
                d["s_visibility_camdist_min"] = psy.s_visibility_camdist_min
                d["s_visibility_camdist_max"] = psy.s_visibility_camdist_max

            d["s_visibility_camoccl_allow"] = psy.s_visibility_camoccl_allow
            if psy.s_visibility_camoccl_allow:
                d["s_visibility_camoccl_method"] = psy.s_visibility_camoccl_method
                d["s_visibility_camoccl_threshold"] = psy.s_visibility_camoccl_threshold
                d["s_visibility_camoccl_coll_ptr"] = psy.s_visibility_camoccl_coll_ptr

            d["s_visibility_cam_viewport_method"] = psy.s_visibility_cam_viewport_method

        #Visibility Maxload

        d["s_visibility_maxload_allow"] = psy.s_visibility_maxload_allow
        if psy.s_visibility_maxload_allow:
            d["s_visibility_maxload_cull_method"] = psy.s_visibility_maxload_cull_method
            d["s_visibility_maxload_treshold"] = psy.s_visibility_maxload_treshold
            d["s_visibility_maxload_viewport_method"] = psy.s_visibility_maxload_viewport_method

    if s_filter.get("s_instances"):
        d[">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> INSTANCING"] = ""

        d["s_instances_method"] = psy.s_instances_method

        #s_instances_coll_ptr never for presets, that's for biomes

        d["s_instances_seed"] = psy.s_instances_seed
        d["s_instances_is_random_seed"] = psy.s_instances_is_random_seed
        d["s_instances_method"] = psy.s_instances_method
        d["s_instances_pick_method"] = psy.s_instances_pick_method

        pick_method = psy.s_instances_pick_method

        if (pick_method=="pick_rate"):

            for i in range(1,21):
                d[f"s_instances_id_{i:02}_rate"] = getattr(psy,f"s_instances_id_{i:02}_rate")

        elif (pick_method=="pick_scale"):

            for i in range(1,21):
                d[f"s_instances_id_{i:02}_scale_min"] = getattr(psy,f"s_instances_id_{i:02}_scale_min")
                d[f"s_instances_id_{i:02}_scale_max"] = getattr(psy,f"s_instances_id_{i:02}_scale_max")
            d["s_instances_id_scale_method"] = psy.s_instances_id_scale_method

        elif (pick_method=="pick_color"):

            for i in range(1,21):
                d[f"s_instances_id_{i:02}_color"] = getattr(psy,f"s_instances_id_{i:02}_color")
            d["s_instances_id_color_tolerence"] = psy.s_instances_id_color_tolerence
            d["s_instances_id_color_sample_method"] = psy.s_instances_id_color_sample_method

            sample_method = d["s_instances_id_color_sample_method"]
            if (sample_method=="vcol"):
                d["s_instances_vcol_ptr"] = psy.s_instances_vcol_ptr
            elif (sample_method=="text"):
                save_texture_ptr_in_dict(category_str=f"s_instances", texture_is_unique=texture_is_unique, texture_random_loc=texture_random_loc,)

        elif (pick_method=="pick_cluster"):

            d["s_instances_pick_cluster_projection_method"] = psy.s_instances_pick_cluster_projection_method
            d["s_instances_pick_cluster_scale"] = psy.s_instances_pick_cluster_scale
            d["s_instances_pick_cluster_blur"] = psy.s_instances_pick_cluster_blur
            d["s_instances_pick_clump"] = psy.s_instances_pick_clump

    if s_filter.get("s_display"):
        d[">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> DISPLAY"] = ""

        d["s_display_master_allow"] = psy.s_display_master_allow

        #Display As, no indentation on purpose so biomes can load their display even if disabled

        d["s_display_allow"] = psy.s_display_allow
        d["s_display_method"] = psy.s_display_method
        
        d["s_display_placeholder_type"] = psy.s_display_placeholder_type
        d["s_display_custom_placeholder_ptr"] = psy.s_display_custom_placeholder_ptr
        d["s_display_placeholder_scale"] = psy.s_display_placeholder_scale

        d["s_display_point_radius"] = psy.s_display_point_radius        
        d["s_display_cloud_radius"] = psy.s_display_cloud_radius
        d["s_display_cloud_density"] = psy.s_display_cloud_density

        d["s_display_camdist_allow"] = psy.s_display_camdist_allow
        d["s_display_camdist_distance"] = psy.s_display_camdist_distance

        d["s_display_viewport_method"] = psy.s_display_viewport_method
        
    return serialization(d)


#       .o.                             oooo                   ooooooooo.                                             .
#      .888.                            `888                   `888   `Y88.                                         .o8
#     .8"888.     oo.ooooo.  oo.ooooo.   888  oooo    ooo       888   .d88' oooo d8b  .ooooo.   .oooo.o  .ooooo.  .o888oo
#    .8' `888.     888' `88b  888' `88b  888   `88.  .8'        888ooo88P'  `888""8P d88' `88b d88(  "8 d88' `88b   888
#   .88ooo8888.    888   888  888   888  888    `88..8'         888          888     888ooo888 `"Y88b.  888ooo888   888
#  .8'     `888.   888   888  888   888  888     `888'          888          888     888    .o o.  )88b 888    .o   888 .
# o88o     o8888o  888bod8P'  888bod8P' o888o     .8'          o888o        d888b    `Y8bod8P' 8""888P' `Y8bod8P'   "888"
#                  888        888             .o..P'
#                 o888o      o888o            `Y8P'


class SCATTER5_OT_preset_apply(bpy.types.Operator):
    """external operator, on creation we use bpy.ops.scatter5.add_psy_preset()"""

    bl_idname      = "scatter5.preset_apply"
    bl_label       = translate("Apply a Preset")
    bl_description = translate("Apply a Preset")

    json_path : bpy.props.StringProperty() #mandatory
    emitter_name : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    single_category : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},) # given category name or use 'all'
    method : bpy.props.StringProperty(default="selection", options={"SKIP_SAVE",},) # mandatory argument in: selection|active|alt

    def invoke(self, context, event):
        """only used if alt behavior == automatic selection|active"""

        if (event.ctrl): #secret ctrl behavior
            bpy.ops.scatter5.open_directory(folder=self.json_path)
            return {'FINISHED'}

        if (self.method=="alt"):
            self.method = "selection" if event.alt else "active"

        return self.execute(context)

    def execute(self, context):

        if (self.json_path==""):
            raise Exception("No Path Specified")

        scat_scene = bpy.context.scene.scatter5
        emitter = bpy.data.objects.get(self.emitter_name)
        if (emitter is None):
            emitter = scat_scene.emitter

        #apply to selection/active?
        match self.method:
            case 'selection': psys = emitter.scatter5.get_psys_selected()
            case 'active': psys = [emitter.scatter5.get_psy_active()]
        
        for p in psys:

            #hide for optimization 
            did_hide = None 
            if (not p.hide_viewport):
                p.hide_viewport = did_hide = True

            #apply preset to settings
            path = os.path.dirname(self.json_path)
            file_name = os.path.basename(self.json_path)
            d = json_to_dict(path=path,file_name=file_name,)

            if (self.single_category=="all"):
                  dict_to_settings( d, p, )
            else: dict_to_settings( d, p, s_filter={self.single_category:True} )

            #restore optimization
            if (did_hide is not None):
                p.hide_viewport = False

            continue

        #UNDO_PUSH
        bpy.ops.ed.undo_push(message=translate("Pasting Preset to Settings"))

        return {'FINISHED'}


class DualPresetMenu(bpy.types.Menu):
    """needed to split the menu in two because passing a text argument to gui menus is incredibly difficult"""

    bl_idname      = ""
    bl_label       = ""
    bl_description = ""

    per_category_version = False

    def __init__(self, *args, **kwargs):
        """Generate menu content"""
        
        super().__init__(*args, **kwargs)

        #make sure sub categoryu dir exists
        if (not os.path.exists(directories.lib_prescat)):
            pathlib.Path(directories.lib_prescat).mkdir(parents=True, exist_ok=True)

        global PREVIEWS_PRST

        self.preset_ope_paths = [ os.path.join(directories.lib_presets,file) for file in os.listdir(directories.lib_presets) if file.endswith(".preset") ]
        self.preset_ope_names = [ os.path.basename(p).replace(".preset","").replace("_"," ").title() for p in self.preset_ope_paths ]
        self.preset_ope_icons = [ os.path.basename(p).replace(".preset","") for p in self.preset_ope_paths ]
        self.preset_ope_icons = [ PREVIEWS_PRST[p].icon_id if (p in PREVIEWS_PRST) else cust_icon("W_BLANK1") for p in self.preset_ope_icons ]

        self.preset_cat_paths = [ os.path.join(directories.lib_prescat,file) for file in os.listdir(directories.lib_prescat) if file.endswith(".preset") ]
        self.preset_cat_names = [ os.path.basename(p).replace(".preset","").split("___")[1].replace("_"," ").title() for p in self.preset_cat_paths ]

        return None 

    def draw(self, context):
        layout = self.layout

        wm = context.window_manager
        row = layout.row()

        #################### Operator Presets

        col = row.column()

        #draw title, only needed if we two type of presets
        if (self.per_category_version):
            col.label(text=translate("Operator Preset(s)"),)
            col.separator()

            #paste category do not make sense for the following settings categories
            
            s_category = context.pass_ui_arg_popover
            if (type(s_category) is not str):
                col.label(icon="ERROR")
                print(f"ERROR: DualPresetMenu: context.pass_ui_arg_popover '{s_category}' is not string..")
                return None
            
            if (s_category in ("s_surface","s_display","s_visibility","s_mask")):
                col.enabled = False

        #loop over all presets
        for (path, name, icon) in zip(self.preset_ope_paths, self.preset_ope_names, self.preset_ope_icons):
            op = col.operator("scatter5.preset_apply", text=name, icon_value=icon,)
            #in ui-list behavior = apply to all selection, if in header, only use per category
            op.method = "alt" if (self.per_category_version) else "selection"
            op.single_category = s_category if (self.per_category_version) else "all"
            op.json_path = path
            preset_ope_exists = True 

        #nothing found label if did not draw anything in loop
        if ("preset_ope_exists" not in locals()):
            col.label(text=translate("Nothing Found"),)

        #save operator, only for uilist version
        if (not self.per_category_version):
            col.operator("scatter5.export_to_presets", text=translate("Add New"), icon="ADD",)

        #draw the rest == only for header version
        if (not self.per_category_version):
            return None

        #################### Category Presets

        #draw title
        col = row.column()
        col.label(text=translate("Category Preset(s)"),)
        col.separator()

        #loop over all presets
        for (path, name) in zip(self.preset_cat_paths, self.preset_cat_names):
            if os.path.basename(path).startswith(s_category): #all category presets are mixed, we differentiate them with prefix
                op = col.operator("scatter5.preset_apply", text=name, icon="FILE_TEXT",)
                op.method = "alt"
                op.single_category = s_category
                op.json_path = path
                preset_cat_exists = True 
        
        #nothing found label if did not draw anything in loop
        if ("preset_cat_exists" not in locals()):
            col.label(text=translate("Nothing Found"),)

        #save operator
        op = col.operator("scatter5.save_category_preset", text=translate("Add New"), icon="ADD",)
        op.single_category = s_category

        return None

class SCATTER5_MT_preset_menu_header(DualPresetMenu):
    """version for per category header"""
    bl_idname = "SCATTER5_MT_preset_menu_header"
    per_category_version = True


class SCATTER5_MT_preset_menu_uilist(DualPresetMenu):
    """version for ui list"""
    bl_idname = "SCATTER5_MT_preset_menu_uilist"
    per_category_version = False


#  .oooooo..o                                      ooooooooo.                                             .
# d8P'    `Y8                                      `888   `Y88.                                         .o8
# Y88bo.       .oooo.   oooo    ooo  .ooooo.        888   .d88' oooo d8b  .ooooo.   .oooo.o  .ooooo.  .o888oo
#  `"Y8888o.  `P  )88b   `88.  .8'  d88' `88b       888ooo88P'  `888""8P d88' `88b d88(  "8 d88' `88b   888
#      `"Y88b  .oP"888    `88..8'   888ooo888       888          888     888ooo888 `"Y88b.  888ooo888   888
# oo     .d8P d8(  888     `888'    888    .o       888          888     888    .o o.  )88b 888    .o   888 .
# 8""88888P'  `Y888""8o     `8'     `Y8bod8P'      o888o        d888b    `Y8bod8P' 8""888P' `Y8bod8P'   "888"


class SCATTER5_OT_save_category_preset(bpy.types.Operator):

    bl_idname      = "scatter5.save_category_preset"
    bl_label       = translate("Save a preset")
    bl_description = translate("Save the settings of this category as a new category preset")
    bl_options     = {'REGISTER', 'INTERNAL'}

    single_category : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    name : bpy.props.StringProperty(default="My Preset", options={"SKIP_SAVE",},)

    def invoke(self, context, event):
        
        #make sure sub categoryu dir exists
        if (not os.path.exists(directories.lib_prescat)):
            pathlib.Path(directories.lib_prescat).mkdir(parents=True, exist_ok=True)

        return context.window_manager.invoke_props_dialog(self)

    def find_file_name(self):
        return self.single_category+"___"+self.name.lower().replace(" ","_")

    def find_file_path(self):
        return os.path.join(directories.lib_prescat,self.find_file_name()+".preset",)

    def draw(self, context):
        layout = self.layout

        prop = layout.row()
        prop.alert = self.alert = (  is_illegal_string(self.name) or (self.name in [""," ","  ","   "]) ) 
        prop.prop(self,"name", text=translate("Preset Name"))

        if ( os.path.exists(self.find_file_path()) ):
            layout.label(text=translate("This preset already exists, Override?"))

        layout.separator()

        return None

    def execute(self, context):

        if (self.alert):
            bpy.ops.scatter5.popup_menu(msgs=translate("Please make sure the name of the preset is legal"),title=translate("Action Impossible"),icon="ERROR")
            return {'FINISHED'}

        emitter    = bpy.context.scene.scatter5.emitter
        psy_active = emitter.scatter5.get_psy_active()

        d = settings_to_dict(psy_active,
            use_random_seed=False,
            texture_is_unique=True,
            texture_random_loc=False,
            get_scatter_density=True,
            s_filter={self.single_category:True},
            ) 

        #we don't need the name here
        if ("name" in d):
            del d["name"]

        dict_to_json(d, path=directories.lib_prescat, file_name=self.find_file_name(), extension=".preset",)

        return {'FINISHED'}


class SCATTER5_OT_export_to_presets(bpy.types.Operator):

    bl_idname      = "scatter5.export_to_presets"
    bl_label       = translate("Preset(s) Export")
    bl_description = translate("Export the selected scatter-system(s) as '.preset' files in your hard drive. Preset files are mainly used by the 'Preset-Scatter' operator located in the 'Create' panel")
    bl_options     = {'REGISTER', 'INTERNAL'}

    #settings if context of a biome overwrite
    #NOTE TO SELF, would be better to have a standalone exporter for biome overwrite?
    biome_overwrite_mode : bpy.props.BoolProperty(default=False, options={"SKIP_SAVE",},)
    biome_temp_directory : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)

    @classmethod
    def poll(cls, context):
        return ( (bpy.context.scene.scatter5.emitter is not None) and (os.path.exists(directories.lib_presets)) )

    def invoke(self, context, event):

        scat_scene = context.scene.scatter5
        scat_op    = scat_scene.operators.export_to_presets
        emitter    = scat_scene.emitter

        #overwrite == only overwrite active layer
        if (self.biome_overwrite_mode):
              self.export_psys = [ emitter.scatter5.get_psy_active() ]
        else: self.export_psys = emitter.scatter5.get_psys_selected()

        #display message if nothing to export!
        if (len(emitter.scatter5.get_psys_selected())==0):
            bpy.ops.scatter5.popup_menu(title=translate("Preset Creation Failed"), msgs=translate("No Scatter-System(s) Selected"), icon="ERROR",)
            return {'FINISHED'}

        return bpy.context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout

        scat_scene = context.scene.scatter5
        scat_op    = scat_scene.operators.export_to_presets

        box, is_open = ui_templates.box_panel(layout, 
            panelopen_propname="ui_dialog_presetsave", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_dialog_presetsave");BOOL_VALUE(1)
            panel_icon="CURRENT_FILE",
            panel_name=translate("Selected System(s) to Preset(s)") if (not self.biome_overwrite_mode) else translate("Overwrite Biome Preset"),
            )
        if is_open:

            sep = box.row()
            s1 = sep.separator(factor=0.2)
            s2 = sep.column()
            s3 = sep.separator(factor=0.2)

            #default behavior export information
            if (not self.biome_overwrite_mode):

                txt = s2.column(align=True)
                txt.label(text=translate("We will create the Following Presets :"))
                txt.scale_y = 0.8
                future_names = [ legal(p.name).lower().replace(" ","_") for p in self.export_psys]
                one_exists = False

                if (future_names):

                    for n in future_names: 
                        rtxt = txt.row()
                        rtxt.active = False
                        
                        if ( os.path.exists(os.path.join(scat_op.precrea_creation_directory, f"{n}.preset") ) ):
                            rtxt.alert = True
                            one_exists = True    

                        rtxt.label(text=f" - ''{n}.preset''")
                        continue
                else:
                    rtxt = txt.row()
                    rtxt.active = False
                    rtxt.label(text="   "+translate("Nothing Found"),)
                    
                s2.separator()

                word_wrap( string=translate("Note that not all properties can be exported in presets. A '.preset' file is only but a '.json' text file storing your settings."), layout=s2, alignment="LEFT", max_char=50,)

            #else show overwrite information
            else: 
                word_wrap( string=translate("The settings of the active system will be exported and replace this biome layer. This do not include display settings, name, color or instance objects!"), layout=s2, alignment="LEFT", max_char=50,)

            s2.separator()

            sub = s2.row()
            sub.prop(scat_op,"precrea_use_random_seed",)
            sub = s2.row()
            sub.prop(scat_op,"precrea_texture_is_unique",)
            sub = s2.row()
            sub.prop(scat_op,"precrea_texture_random_loc",)

            s2.separator()
            
            #show future preset path

            if (not self.biome_overwrite_mode):

                exp = s2.column(align=True)
                exp.label(text=translate("Export Directory")+":")
                exp.prop(scat_op,"precrea_creation_directory",text="")

                txt = s2.column()
                txt.scale_y = 0.8
                txt.active = False
                txt.label(text=translate("Preset gallery location is by default located in"))
                op = txt.operator("scatter5.open_directory", text=f"'{directories.lib_presets}", emboss=False,)
                op.folder = directories.lib_presets

            else: 
                txt = s2.column()
                txt.scale_y = 0.8
                txt.active = False
                txt.label(text=translate("We will overwrite the following path:"),)
                s2.prop(self,"biome_temp_directory",text="",)
                
            s2.separator()

            if (not self.biome_overwrite_mode):

                sub = s2.column()
                sub.alert = one_exists
                sub.prop(scat_op,"precrea_overwrite",)

                sub = s2.row()
                sub.prop(scat_op,"precrea_auto_render",)

            ui_templates.separator_box_in(box)
            layout.separator()

        return None

    def execute(self, context):

        scat_scene = bpy.context.scene.scatter5
        scat_op    = scat_scene.operators.export_to_presets
        
        for p in self.export_psys:

            #export psy as settings!
            d = settings_to_dict( p,
                use_random_seed=scat_op.precrea_use_random_seed,
                texture_is_unique=scat_op.precrea_texture_is_unique,
                texture_random_loc=scat_op.precrea_texture_random_loc,
                get_scatter_density=True,
                ) 

            #by default classic preset export path!
            if (not self.biome_overwrite_mode):
                file_name = legal(d["name"]).lower().replace(" ","_")
                folder_path = scat_op.precrea_creation_directory
                json_path = os.path.join( folder_path, f"{file_name}.preset" )
            #else override with our custom paht!
            else:
                folder_path, file_name = os.path.split(self.biome_temp_directory)
                file_name = file_name.replace(".preset","")
                json_path = ""

            #if path exists and user did not choose to overwrite, and not in special biome overwrite mode, then display error message
            if ( os.path.exists(json_path) and (not scat_op.precrea_overwrite) and (not self.biome_overwrite_mode) ):
                bpy.ops.scatter5.popup_menu(msgs=translate("File already exists! Overwriting not allowed."),title=translate("Preset Creation Skipped"),icon="ERROR",)
                continue 

            #write the file!
            dict_to_json(d, path=folder_path, file_name=file_name, extension=".preset",)

            #do the render if user requested and if not special biome overwrite mode
            if ( (scat_op.precrea_auto_render) and (not self.biome_overwrite_mode) ):
                bpy.ops.scatter5.generate_thumbnail(json_path=json_path, render_output=json_path.replace(".preset",".jpg"))

        #automatically reload the gallery if not biome overwrite
        if (not self.biome_overwrite_mode):
              reload_gallery()
        else: bpy.ops.scatter5.refresh_biome_estimated_density(path=self.biome_temp_directory.split(".layer")[0]+".biome")

        return {'FINISHED'}


# ooooooooo.                                   o8o
# `888   `Y88.                                 `"'
#  888   .d88' oooo d8b  .ooooo.  oooo    ooo oooo   .ooooo.  oooo oooo    ooo  .oooo.o
#  888ooo88P'  `888""8P d88' `88b  `88.  .8'  `888  d88' `88b  `88. `88.  .8'  d88(  "8
#  888          888     888ooo888   `88..8'    888  888ooo888   `88..]88..8'   `"Y88b.
#  888          888     888    .o    `888'     888  888    .o    `888'`888'    o.  )88b
# o888o        d888b    `Y8bod8P'     `8'     o888o `Y8bod8P'     `8'  `8'     8""888P'


from .. resources.icons import get_previews_from_directory, remove_previews


#store bpy.utils.previews here
PREVIEWS_PRST = {}


def gallery_register():
    """Dynamically create EnumProperty from custom loaded previews"""

    items = [ ( "nothing_found", translate("Nothing Found"), "", cust_icon("W_DEFAULT_NO_PRESET_FOUND"), 0,), ]

    global PREVIEWS_PRST 
    PREVIEWS_PRST = get_previews_from_directory(directories.lib_presets, extension=".jpg")

    listpreset = [ file.replace(".preset","") for file in os.listdir(directories.lib_presets) if file.endswith(".preset") ]
    listpreset = sorted(listpreset) #MacOs directories might not be ordered
    if (len(listpreset)!=0): 
        items = [ ( e, e.title().replace("_"," "), "", PREVIEWS_PRST[e].icon_id if (e in PREVIEWS_PRST) else cust_icon("W_DEFAULT_PREVIEW"), i, ) for i,e in enumerate(listpreset) ]

    #gather properties from chosen preset

    def upd_scatter5_preset_gallery(self, context):
        """runned each time user change the active item from the preset gallery
        for recalculating estimation & setting preset path for the operator"""

        dprint("PROP_FCT: updating WindowManager.scatter5_preset_gallery")
            
        #== all properties related to the add psy operator
        scat_op = bpy.context.scene.scatter5.operators.add_psy_preset

        scat_op.preset_path = os.path.join( directories.lib_presets , bpy.context.window_manager.scatter5_preset_gallery + ".preset" )

        #Gather information from .preset file to display above operator
        d = json_to_dict(path=directories.lib_presets, file_name=self.scatter5_preset_gallery+".preset",)

        #Get Name of the Preset
        if ("name" in d):
            scat_op.preset_name = d["name"]

        #Color Information 
        if ("s_color" in d):
            scat_op.preset_color = ensure_rgba_colors(d["s_color"])

        #Density Estimation need to update when changing the preset 
        scat_op.estimated_preset_density = d["estimated_density"] if ("estimated_density" in d) else 0
        scat_op.estimated_preset_keyword = ""

        #gather method keyword
        if ("s_distribution_method" in d):
            scat_op.estimated_preset_keyword += " "+d["s_distribution_method"]

        #gather space keyword
        if ("s_distribution_space" in d):
            scat_op.estimated_preset_keyword += " "+d["s_distribution_space"]
        elif ("s_distribution_clump_space" in d):
            scat_op.estimated_preset_keyword += " "+d["s_distribution_clump_space"]
        else: 
            scat_op.estimated_preset_keyword += " "+"local"

        return None

    bpy.types.WindowManager.scatter5_preset_gallery = bpy.props.EnumProperty(
        name=translate("Scatter Preset Library"),
        description=translate("Choose an active preset from your library"),
        items=items,
        update=upd_scatter5_preset_gallery,
        )

    return None 


def gallery_unregister():

    del bpy.types.WindowManager.scatter5_preset_gallery

    global PREVIEWS_PRST 
    remove_previews(PREVIEWS_PRST)

    return None 


def reload_gallery():

    gallery_unregister()
    gallery_register()

    return None 


class SCATTER5_OT_reload_preset_gallery(bpy.types.Operator):

    bl_idname      = "scatter5.reload_preset_gallery"
    bl_label       = ""
    bl_description = ""

    def execute(self, context):
        reload_gallery()
        return {'FINISHED'} 


class SCATTER5_OT_preset_enum_increment(bpy.types.Operator):

    bl_idname      = "scatter5.preset_enum_increment"
    bl_label       = translate("Previous/Next Preset")
    bl_description = translate("Change the active preset by pressing on the previous/next arrow")
    bl_options     = {'INTERNAL'}

    direction : bpy.props.StringProperty(default="LEFT") #LEFT/RIGHT

    def execute(self, context):
        wm = bpy.context.window_manager 
        gallery_items = wm.bl_rna.properties["scatter5_preset_gallery"].enum_items

        if (len(gallery_items)<=1):
            return {'FINISHED'}
 
        def real_name(name):
            return name.lower().replace(" ","_")

        #get_enum_order_and_length
        for e in gallery_items:
            if (wm.scatter5_preset_gallery==real_name(e.name)):
                i,l = e.value , len(gallery_items) 
                break

        # Go Forward/Backward
        if (self.direction=="LEFT"):
            i -= 1
        elif (self.direction=="RIGHT"):
            i += 1

        #Loop over
        if (i==l):
            i = 0  
        if (i<0):
            i = l-1

        #update enum property with increment
        wm.scatter5_preset_gallery = real_name(gallery_items[i].name)

        return {'FINISHED'}


#   .oooooo.   oooo
#  d8P'  `Y8b  `888
# 888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
# 888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
# 888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
# `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#  `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'


classes = (

    SCATTER5_MT_preset_menu_header,
    SCATTER5_MT_preset_menu_uilist,
    SCATTER5_OT_preset_apply,
    SCATTER5_OT_save_category_preset,
    SCATTER5_OT_export_to_presets,
    SCATTER5_OT_preset_enum_increment,
    SCATTER5_OT_reload_preset_gallery,

    )

