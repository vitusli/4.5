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
#   .oooooo.                                               .
#  d8P'  `Y8b                                            .o8
# 888      888 oo.ooooo.   .ooooo.  oooo d8b  .oooo.   .o888oo  .ooooo.  oooo d8b
# 888      888  888' `88b d88' `88b `888""8P `P  )88b    888   d88' `88b `888""8P
# 888      888  888   888 888ooo888  888      .oP"888    888   888   888  888
# `88b    d88'  888   888 888    .o  888     d8(  888    888 . 888   888  888
#  `Y8bood8P'   888bod8P' `Y8bod8P' d888b    `Y888""8o   "888" `Y8bod8P' d888b
#               888
#              o888o
#####################################################################################################

# in this module are all de-centralized settings of some operators. We store them separatelly as these settings shall be saved cross sessions.
# these settings are more important than your average operator properties. Especially for the scatter operators, stored in the 'Create' panel 'On Creation' menu
# `f_` stands for `future_` aka the future visibility/display or masks of operators located in scattering.add_psy.py or add_biome.py


import bpy

import os 

from .. translations import translate
from .. resources import directories
from .. utils.str_utils import get_surfs_shared_attrs
from .. utils.override_utils import get_any_view3d_region


# oooooooooooo                                               .          .oooooo.                       
# `888'     `8                                             .o8         d8P'  `Y8b                      
#  888         oooo    ooo oo.ooooo.   .ooooo.  oooo d8b .o888oo      888      888 oo.ooooo.   .oooo.o 
#  888oooo8     `88b..8P'   888' `88b d88' `88b `888""8P   888        888      888  888' `88b d88(  "8 
#  888    "       Y888'     888   888 888   888  888       888        888      888  888   888 `"Y88b.  
#  888       o  .o8"'88b    888   888 888   888  888       888 .      `88b    d88'  888   888 o.  )88b 
# o888ooooood8 o88'   888o  888bod8P' `Y8bod8P' d888b      "888"       `Y8bood8P'   888bod8P' 8""888P' 
#                           888                                                     888                
#                          o888o                                                   o888o               
                                                                                                     

class SCATTER5_PR_export_to_presets(bpy.types.PropertyGroup): 
    """scat_op = bpy.context.scene.scatter5.operators.export_to_presets
    decentralized settings of SCATTER5_OT_export_to_presets"""

    #Directory

    precrea_overwrite : bpy.props.BoolProperty(
        name=translate("Overwrite files?"),
        default=False,
        )
    precrea_creation_directory : bpy.props.StringProperty(
        name=translate("Overwrite if already exists"),
        default=directories.lib_presets, 
        )

    #preset related

    precrea_use_random_seed : bpy.props.BoolProperty(
        name=translate("Use Random Seed Values"),
        description=translate("Automatically randomize the seed values of all seed properties"),
        default=True, 
        )
    precrea_texture_is_unique : bpy.props.BoolProperty(
        name=translate("Create Unique Textures"),
        description=translate("When creating a texture data, our plugin will, by default, always create a new texture data.\nIf this option is set to False, our plugin will use the same texture data, if found"),
        default=True, 
        )
    precrea_texture_random_loc : bpy.props.BoolProperty(
        name=translate("Random Textures Translation"),
        description=translate("When creating a texture data, our plugin will randomize the location vector, useful to guarantee uniqueness textures location. Disable this option if you are using a texture that influences multiple particle systems."),
        default=True, 
        )
    precrea_auto_render : bpy.props.BoolProperty(
        name=translate("Render thumbnail"),
        description=translate("automatically render the thumbnail of the preset afterward"),
        default=False, 
        )


class SCATTER5_PR_export_to_biome(bpy.types.PropertyGroup): 
    """scat_op = bpy.context.scene.scatter5.operators.export_to_biome
    decentralized settings of SCATTER5_OT_export_to_biome"""

    #Directory
    
    biocrea_overwrite : bpy.props.BoolProperty(
        name=translate("Overwrite files?"),
        default=False,
        )
    biocrea_creation_directory : bpy.props.StringProperty(
        name="",
        default=os.path.join(directories.lib_biomes,"MyBiomes"),
        )

    #preset related
    
    biocrea_use_random_seed : bpy.props.BoolProperty(
        name=translate("Use random seed values"),
        description=translate("Automatically randomize the seed values of all seed properties of all scatter-system(s) when loading the scatter-preset's"),
        default=True,
        )
    biocrea_texture_is_unique : bpy.props.BoolProperty(
        name=translate("Create Unique Textures"),
        description=translate("When creating a texture data, our plugin will, by default, always create a new texture data.\nIf this option is set to False, our plugin will use the same texture data, if found"),
        default=True,
        )
    biocrea_texture_random_loc : bpy.props.BoolProperty(
        name=translate("Random textures translation"),
        description=translate("When creating a texture data, our plugin will randomize the location vector, useful to guarantee patch uniqueness location. Disable this option if you are using a texture that influence multiple particle systems."),
        default=True,
        )

    #use biome display
    biocrea_use_biome_display : bpy.props.BoolProperty(
        name=translate("Encode display settings"),
        description=translate("Also encode 'Display As' option of your biome scatter-system(s)"),
        default=True,
        )

    #biome information
    
    biocrea_biome_name : bpy.props.StringProperty(
        name=translate("Name"),
        default="My Biome",
        )
    biocrea_file_keywords : bpy.props.StringProperty(
        name=translate("Keywords"),
        default="Some, Examples, Of, Keywords, Use, Coma,",
        )
    biocrea_keyword_from_instances : bpy.props.BoolProperty(
        name=translate("Instances as keywords"),
        description=translate("Automatically add the instances names as new keywords"),
        default=True,
        )
    biocrea_file_author : bpy.props.StringProperty(
        name=translate("Author"),
        default="BD3D",
        )
    biocrea_file_website : bpy.props.StringProperty(
        name=translate("Website"),
        default="https://geoscatter.com/biomes.html",
        )
    biocrea_file_description : bpy.props.StringProperty(
        name=translate("Description"),
        default="this is a custom biome i made! :-)",
        )
    
    #biome instance export 
    
    biocrea_storage_method : bpy.props.EnumProperty(
        name=translate("Storage Type"),
        description=translate("Choose what you would like us to do with the objects this biome is using"),
        default="create", 
        items=( ("create" ,translate("Models need to be exported") ,translate("Objects used by this biome will be automatically exported in a new .blend file, typically called 'my_biome.instances.blend'"),),
                ("exists" ,translate("Models already exists") ,translate("Objects used by this biome already exist in a .blend somewhere, and you'd prefer the biome system to look for this blend"),),
              ),
        )
    biocrea_storage_library_type : bpy.props.EnumProperty(
        name=translate("Storage Method"),
        description=translate("Please tell us how your existing .blends are stored"),
        default="centralized", 
        items=( ("centralized" ,translate("One central .blend") ,translate("Objects used by this biome are centralized in one and only .blend file"),),
                ("individual" ,translate("Many individual .blends") ,translate("Objects used by this biome are made of many individual .blend files.\n\nIn order to use this option, all of your instances objects need to be linked in the scene, so we will automatically be able to find which .blend file the object comes from.\n\nPlease note that loading a biome assets from many .blend files is slower than loading a biome that uses objects from one central blend file"),),
              ),
        )
    biocrea_centralized_blend : bpy.props.StringProperty(
        name="",
        default="my_library.blend",
        )

    #reload previews
    
    biocrea_auto_reload_all  : bpy.props.BoolProperty(
        name=translate("Reload library afterward"),
        default=True,
        )

    #biome export gui steps
    
    biocrea_creation_steps : bpy.props.IntProperty(
        default=0,
        )


class SCATTER5_PR_generate_thumbnail(bpy.types.PropertyGroup): 
    """scat_op = bpy.context.scene.scatter5.operators.generate_thumbnail
    decentralized settings of SCATTER5_OT_generate_thumbnail"""

    thumbcrea_camera_type : bpy.props.EnumProperty(
        name=translate("Distance"),
        default="cam_small", 
        items=( ("cam_forest" ,translate("Far") ,""),
                ("cam_plant" ,translate("Medium") ,""),
                ("cam_small" ,translate("Near") ,""),
              ),
        )
    thumbcrea_placeholder_type : bpy.props.EnumProperty(
        name=translate("Instance"),
        default="SCATTER5_placeholder_extruded_square", 
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
                #("SCATTER5_placeholder_lowpoly_cluster_01", "Lowpoly Cluster 01", "", "TOPATCH:W_placeholder_lowpoly_cluster_01", 34),
                #("SCATTER5_placeholder_lowpoly_cluster_02", "Lowpoly Cluster 02", "", "TOPATCH:W_placeholder_lowpoly_cluster_02", 35),
                #("SCATTER5_placeholder_lowpoly_cluster_03", "Lowpoly Cluster 03", "", "TOPATCH:W_placeholder_lowpoly_cluster_03", 36),
                #("SCATTER5_placeholder_lowpoly_cluster_04", "Lowpoly Cluster 04", "", "TOPATCH:W_placeholder_lowpoly_cluster_04", 37),
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
                #("SCATTER5_placeholder_helper_empty_stick", "Helper Empty Stick", "", "TOPATCH:W_placeholder_helper_empty_stick", 49),
                #("SCATTER5_placeholder_helper_empty_arrow", "Helper Empty Arrow", "", "TOPATCH:W_placeholder_helper_empty_arrow", 50),
                #("SCATTER5_placeholder_helper_empty_axis", "Helper Empty Axis", "", "TOPATCH:W_placeholder_helper_empty_axis", 51),
                ("SCATTER5_placeholder_helper_colored_axis", "Helper Colored Axis", "", "TOPATCH:W_placeholder_helper_colored_axis", 52),
                ("SCATTER5_placeholder_helper_colored_cube", "Helper Colored Cube", "", "TOPATCH:W_placeholder_helper_colored_cube", 53),
                ("SCATTER5_placeholder_helper_y_arrow", "Helper Tangent Arrow", "", "TOPATCH:W_placeholder_helper_y_arrow", 54),
                ("SCATTER5_placeholder_helper_y_direction", "Helper Tangent Direction", "", "TOPATCH:W_placeholder_helper_y_direction", 55),
                ("SCATTER5_placeholder_helper_z_arrow", "Helper Normal Arrow", "", "TOPATCH:W_placeholder_helper_z_arrow", 56),
              ),
        )
    thumbcrea_placeholder_color : bpy.props.FloatVectorProperty( 
        name=translate("Color"),
        default=(1,0,0.5),
        min=0,
        max=1,
        subtype="COLOR",
        )
    thumbcrea_placeholder_scale : bpy.props.FloatVectorProperty(
        name=translate("Scale"),
        subtype="XYZ", 
        default=(0.25,0.25,0.25), 
        )

    def upd_thumbcrea_use_current_blend_path(self,context):
        """update function for path property"""
        
        if (not self.thumbcrea_use_current_blend_path):
            return None
        
        if (not bpy.data.is_saved):
              pth = "None"
        else: pth = bpy.data.filepath
        
        self.thumbcrea_custom_blend_path = pth
        
        return None

    thumbcrea_use_current_blend_path  : bpy.props.BoolProperty(
        default=False,
        name=translate("Use current blend file"),
        update=upd_thumbcrea_use_current_blend_path,
        )
    thumbcrea_custom_blend_path  : bpy.props.StringProperty(
        name=translate("Blend Path"),
        description=translate("The plugin will open this .blend add the biome on the emitter named below then launch a render."),
        default=os.path.join(directories.addon_thumbnail,"custom_biome_icons.blend"),
        )
    thumbcrea_custom_blend_emitter : bpy.props.StringProperty(
        name=translate("Emit. Name"),
        description=translate("Enter the emitter name from the blend above please."),
        default="Ground",
        )
    thumbcrea_render_iconless : bpy.props.BoolProperty(
        default=False,
        name=translate("Render all biomes with no preview"),
        )
    thumbcrea_auto_reload_all : bpy.props.BoolProperty(
        default=True,
        name=translate("Reload library afterward"),
        )


#  .oooooo..o                         .       .                             .oooooo.                       
# d8P'    `Y8                       .o8     .o8                            d8P'  `Y8b                      
# Y88bo.       .ooooo.   .oooo.   .o888oo .o888oo  .ooooo.  oooo d8b      888      888 oo.ooooo.   .oooo.o 
#  `"Y8888o.  d88' `"Y8 `P  )88b    888     888   d88' `88b `888""8P      888      888  888' `88b d88(  "8 
#      `"Y88b 888        .oP"888    888     888   888ooo888  888          888      888  888   888 `"Y88b.  
# oo     .d8P 888   .o8 d8(  888    888 .   888 . 888    .o  888          `88b    d88'  888   888 o.  )88b 
# 8""88888P'  `Y8bod8P' `Y888""8o   "888"   "888" `Y8bod8P' d888b          `Y8bood8P'   888bod8P' 8""888P' 
#                                                                                       888                
#                                                                                      o888o               
                                                                                                         

# 88 88b 88 88  88 888888 88""Yb 88 888888     88""Yb 88""Yb  dP"Yb  88""Yb .dP"Y8 
# 88 88Yb88 88  88 88__   88__dP 88   88       88__dP 88__dP dP   Yb 88__dP `Ybo." 
# 88 88 Y88 888888 88""   88"Yb  88   88       88"""  88"Yb  Yb   dP 88"""  o.`Y8b 
# 88 88  Y8 88  88 888888 88  Yb 88   88       88     88  Yb  YbodP  88     8bodP' 


class SCATTER5_PR_objects(bpy.types.PropertyGroup):

    name : bpy.props.StringProperty(
        get=lambda self: self.object.name if (self.object is not None) else "",
        )
    object : bpy.props.PointerProperty(
        type=bpy.types.Object,
        )


""" #maybe later we'll define instances list like we do with f_surfaces?
class Inherit_f_instances:

    f_instances : bpy.props.CollectionProperty(
        type=SCATTER5_PR_objects,
        ) #internal use by SCATTER5_OT_define_objects

    #default is define in the end

    f_instances_method : bpy.props.EnumProperty(
        name=translate("Which objects would you like to distribute?"),
        default="define",
        items=( ("selection",translate("Use Current Selection"),translate("The object(s) currently selected will become the future instances of your scatter-system"),"RESTRICT_SELECT_OFF",1),
                ("define",translate("Define When Called"),translate("Upon scattering, we will ask to select your future instances"),"BORDERMOVE",2),
              ),
        )

    f_selection_method #TODO move in here and make define default???????
"""


class Inherit_f_surfaces:

    f_surfaces : bpy.props.CollectionProperty(
        type=SCATTER5_PR_objects,
        )
    f_surface_method : bpy.props.EnumProperty(
        name=translate("Surface Method"),
        description=translate("Define the surface(s) which the instances will be scattered upon"),
        default="emitter", 
        items=( ("emitter",translate("Emitter Object"),translate("Scatter on the surface of your emitter object."),"TOPATCH:W_EMITTER",1),
                ("object",translate("Single Object"),translate("Scatter on the surface of a chosen object. This leads to a non-linear workflow."),"TOPATCH:W_SURFACE_SINGLE",2),
                ("collection",translate("Multiple Objects"),translate("Scatter on the surfaces of all objects in chosen collection. This leads to a multi-surface workflow."),"TOPATCH:W_SURFACE_MULTI",3),
              ),
        )
    f_surface_object : bpy.props.PointerProperty(
        type=bpy.types.Object,
        name=translate("Chosen Surface"),
        poll=lambda s,o: o.name in bpy.context.scene.objects,
        )

    def get_f_surfaces(self):
        """return a list of surface object(s)"""

        if (self.f_surface_method=='emitter'):
            return [bpy.context.scene.scatter5.emitter]

        elif (self.f_surface_method=='object'):
            return [self.f_surface_object] if (self.f_surface_object is not None) else []

        elif (self.f_surface_method=='collection'):
            return [e.object for e in self.f_surfaces if (e.object is not None)]

        return []

    def add_selection(self):
        """add the viewport selection to the list of surfaces"""

        for o in bpy.context.selected_objects:
            if (o.type!="MESH"):
                continue
            if (o in [o.object for o in self.f_surfaces]):
                continue
            #add obj to surfaces
            x = self.f_surfaces.add()
            x.object = o
            #refresh squarea area
            o.scatter5.estimate_square_area()
            continue

        return None 


class Inherit_f_mask_settings: 

    f_mask_action_method : bpy.props.EnumProperty(
        name=translate("Masking Operation"),
        description=translate("Define masking operation during the creation of your scatter(s). You are able to assign an existing mask or paint a new one"),
        default="none", 
        items=( ("none",translate("None"),translate("Do nothing. Neither assign nor paint masks on creation"),"PANEL_CLOSE",1),
                ("assign",translate("Assign Mask"),translate("Assign a mask on creation"),"EYEDROPPER",2),
                ("paint",translate("Paint Mask"),translate("Directly paint a mask on creation"),"BRUSH_DATA",3),
              ),
        )
    f_mask_action_type : bpy.props.EnumProperty(
        name=translate("Mask Type"),
        default="vg", 
        items=( ("vg",translate("Vertex-group"),translate("Mask your scatter(s) with a vertex-group"),"GROUP_VERTEX",1),
                ("bitmap",translate("Image"),translate("Mask your scatter(s) with an Bitmap/Image mask"),"IMAGE_DATA",2),
                ("curve",translate("Bezier-Area"),translate("Mask you scatter(s) by using a Bezier-Area object"),"CURVE_BEZCIRCLE",3),
                ("draw",translate("Bezier-Draw"),translate("Mask you scatter(s) by using Bezier-Spline object"),"CURVE_BEZCURVE",4),
              ),
        )
    f_mask_action_type_curve_subtype : bpy.props.EnumProperty(
        name=translate("Mask Type"),
        default="dist", 
        items=( ("dist",translate("As Distribution"),translate("Mask your scatter using a bezier-area distribution (from 'Tweak>Distribution>Method')"),"STICKY_UVS_DISABLE",1),
                ("mask",translate("As Mask"),translate("Mask your scatter using a bezier-area culling mask (from 'Tweak>Culling Masks>Bezier-Area')"),"MOD_MASK",2),
              ),
        )
    f_mask_assign_vg : bpy.props.StringProperty(
        name=translate("Vertex-Group Pointer"),
        description=translate("Search across all your surface(s) for shared vertex-group.\nWe will highlight the pointer in red if the attribute is not shared across your surface(s)"),
        search=lambda s,c,e: get_surfs_shared_attrs(surfaces=c.scene.scatter5.operators.create_operators.get_f_surfaces(), attr_type='vg', searchname=e,),
        search_options={'SUGGESTION','SORT'},
        )
    f_mask_assign_bitmap : bpy.props.StringProperty(
        name=translate("Image Pointer"),
        search=lambda s,c,e: set(img.name for img in bpy.data.images if (e in img.name)),
        search_options={'SUGGESTION','SORT'},
        )
    f_mask_assign_curve : bpy.props.PointerProperty(
        type=bpy.types.Object,
        poll=lambda s,o: o.type=='CURVE',
        )
    f_mask_assign_reverse : bpy.props.BoolProperty(
        default=False,
        )
    f_mask_paint_vg : bpy.props.StringProperty(
        default="",
        )
    f_mask_paint_bitmap : bpy.props.StringProperty(
        default="",
        )
    f_mask_paint_curve : bpy.props.PointerProperty(
        type=bpy.types.Object,
        poll=lambda s,o: o.type=='CURVE',
        )
    f_mask_spline_width : bpy.props.FloatProperty( #s_distribution_projbezline_patharea_width if f_mask_action_type=='draw'
        name=translate("Default Width"),
        description=translate("The width of the pathway created alongside the spline"),
        subtype="DISTANCE",
        default=0.25,
        min=0,
        precision=3,
        )


class Inherit_f_visibility_settings:

    f_visibility_hide_viewport : bpy.props.BoolProperty(
        description=translate("Hide this scatter on creation. The scatter will only be visible on your final render except if you change the scatter viewport visibility option in the system lister interface."),
        default=False,
        )
    f_visibility_facepreview_allow : bpy.props.BoolProperty(
        description=translate("Enable the 'Preview Area' feature directly upon creation. This feature let you see the scatter only on the selected set of polygons. By default the full scatter will be visible in the final render"),
        default=False,
        )
    f_visibility_view_allow : bpy.props.BoolProperty(
        description=translate("Enable the 'Reduce Density' feature directly upon creation. This feature will reduce the number of scatters visible on the viewport to a chosen percentage value. By default the full scatter will still be visible in the final render"),
        default=False,
        )
    f_visibility_view_percentage : bpy.props.FloatProperty(
        name=translate("Rate"),
        description=translate("Reduction Rate"),
        default=80,
        subtype="PERCENTAGE",
        min=0,
        max=100, 
        )
    f_visibility_cam_allow : bpy.props.BoolProperty(
        description=translate("Enable 'Camera Optimization' features upon creation. Handy to hide generated instances not visible by the active camera. By default the full scatter will be visible in the final render"),
        name=translate("Camera Optimizations"),
        default=False,
        )
    f_visibility_camclip_allow : bpy.props.BoolProperty(
        name=translate("Frustum Culling"),
        description=translate("Hide instances outside the active camera frustum volume"),
        default=True,
        )
    f_visibility_camclip_cam_boost_xy : bpy.props.FloatProperty(
        name=translate("FOV Boost"),
        description=translate("Boost the frustrum visibility angle of the active camera"),
        default=0.04,
        soft_min=-2,
        soft_max=2, 
        precision=3,
        )
    f_visibility_camdist_allow : bpy.props.BoolProperty(
        name=translate("Distance Culling"),
        description=translate("Hide instances far away from the active camera"),
        default=False,
        )
    f_visibility_camdist_min : bpy.props.FloatProperty(
        name=translate("Start"),
        description=translate("Starting this distance, we will start a transition effect until the 'end' distance value"),
        default=10,
        subtype="DISTANCE",
        min=0,
        soft_max=200, 
        )
    f_visibility_camdist_max : bpy.props.FloatProperty(
        name=translate("End"),
        description=translate("After this distance all instances will be culled"),
        default=40,
        subtype="DISTANCE",
        min=0,
        soft_max=200, 
        )
    f_visibility_maxload_allow : bpy.props.BoolProperty( 
        description=translate("Enable the 'Max Amount' feature directly upon creation. This feature will limit or shut-down your scatters when reaching a chosen instance count. By default the full scatter will be visible in the final render"),
        default=False,
        )
    f_visibility_maxload_cull_method : bpy.props.EnumProperty(
        name=translate("Limitation Method"),
        default="maxload_limit",
        items=( ("maxload_limit", translate("Limit"),translate("Limit how many instances are visible on screen. The total amount of instances produced by this scatter-system will never exceed the given threshold."),),
                ("maxload_shutdown", translate("Shutdown"),translate("If total amount of instances produced by this scatter-system goes beyond given threshold, we will shutdown the visibility of this system entirely"),),
              ),
        )
    f_visibility_maxload_treshold : bpy.props.IntProperty(
        name=translate("Threshold"),
        description=translate("The system will either limit or shut down what's visible, when  the instances count approximately reach above the chosen threshold"),
        min=1,
        soft_min=1_000,
        soft_max=9_999_999,
        default=199_000,
        )


class Inherit_f_display_settings:

    f_display_allow : bpy.props.BoolProperty(
        description=translate("Enable the 'Display As' feature directly upon creation. This feature will replace the instance geometry with a display object of your choice"),
        default=False,
        )
    f_display_method : bpy.props.EnumProperty(
        name=translate("Display as"),
        default="placeholder", 
        items= ( ("bb", translate("Bounding-Box"), translate("Display your instances as a solid bounding-box"), "CUBE",1 ),
                 ("convexhull", translate("Convex-Hull"), translate("Display your instances as their computed convexhull geometry. Note that the convex-hull is computed in real time and might be slow to compute"), "MESH_ICOSPHERE",2 ),
                 ("placeholder", translate("Placeholder"), translate("Display your instances as another object, choose from a set of pre-made low poly objects"), "MOD_CLOTH",3 ),
                 ("placeholder_custom", translate("Custom Placeholder"), translate("Display your instances as another object, choose your own custom object"), "MOD_CLOTH",4 ),
                 ("point", translate("Single Point"), translate("Display your instances as a single point"), "LAYER_ACTIVE",5 ),
                 ("cloud", translate("Point-Cloud"), translate("Display your instances as a generated point-cloud"), "OUTLINER_OB_POINTCLOUD",7 ),
               ),
        )
    f_display_custom_placeholder_ptr : bpy.props.PointerProperty(
        type=bpy.types.Object, 
        )
    f_display_bounding_box : bpy.props.BoolProperty(
        description=translate("Set the 'Object>Viewport Display>Display As' method of your scattered object as 'Bounds'. Please note that this is not an option of our plugin, this is a native blender option that can be found in the 'Properties>Object' panel"),
        default=False,
        )


class Inherit_f_security_settings:

    f_sec_count_allow : bpy.props.BoolProperty(
        name=translate("Max scatter-count"),
        default=True,
        description=translate("Enable/Disable the heavy scatter count security detector")
        )
    f_sec_count : bpy.props.IntProperty(
        default=199_000,
        min=1,
        soft_max=1_000_000,
        description=translate("This threshold value represents the maximal visible particle count. If threshold reached on scattering operation, our plugin will automatically hide your particle system and display the security warning menu")
        )
    f_sec_verts_allow : bpy.props.BoolProperty(
        default=True,
        name=translate("Max instance mesh density"),
        description=translate("Enable/Disable the heavy object vertices count security detector")
        )
    f_sec_verts : bpy.props.IntProperty(
        default=199_000,
        min=1,
        soft_max=1_000_000,
        description=translate("This threshold value represents the maximal allowed vertex count of your future instance(s). If the threshold has been reached during the scattering operation, our plugin will automatically set your instance(s) display as wired bounding box and display the security warning menu.")
        )


# 88 88b 88 88  88 888888 88""Yb 88 888888     888888  dP""b8 888888 .dP"Y8 
# 88 88Yb88 88  88 88__   88__dP 88   88       88__   dP   `"   88   `Ybo." 
# 88 88 Y88 888888 88""   88"Yb  88   88       88""   Yb        88   o.`Y8b 
# 88 88  Y8 88  88 888888 88  Yb 88   88       88      YboodP   88   8bodP' 

#below are useful functions based on operators settings cls

class Inherit_utils_fcts:

    def get_context_f_settings(self,):
        """get context operator settings depending operator name"""

        scat_scene   = bpy.context.scene.scatter5
        scat_ops     = scat_scene.operators
        scat_op_crea = scat_ops.create_operators

        d = {}

        #quick scatter or manual scatter do not support hide or hide %

        if (self.__class__.__name__ not in ("SCATTER5_PR_creation_operator_add_psy_modal","SCATTER5_PR_creation_operator_add_psy_manual")):
            d["f_visibility_hide_viewport"] = scat_op_crea.f_visibility_hide_viewport
            d["f_visibility_view_allow"] = scat_op_crea.f_visibility_view_allow
            d["f_visibility_view_percentage"] = scat_op_crea.f_visibility_view_percentage
        else: 
            d["f_visibility_hide_viewport"] = False
            d["f_visibility_view_allow"] = False
            d["f_visibility_view_percentage"] = 0

        #manual scatter do not support any visibility settings

        if (self.__class__.__name__ not in ("SCATTER5_PR_creation_operator_add_psy_manual")):
            d["f_visibility_facepreview_allow"] = scat_op_crea.f_visibility_facepreview_allow

            d["f_visibility_cam_allow"] = scat_op_crea.f_visibility_cam_allow
            d["f_visibility_camclip_allow"] = scat_op_crea.f_visibility_camclip_allow
            d["f_visibility_camclip_cam_boost_xy"] = scat_op_crea.f_visibility_camclip_cam_boost_xy
            d["f_visibility_camdist_allow"] = scat_op_crea.f_visibility_camdist_allow
            d["f_visibility_camdist_min"] = scat_op_crea.f_visibility_camdist_min
            d["f_visibility_camdist_max"] = scat_op_crea.f_visibility_camdist_max

            d["f_visibility_maxload_allow"] = scat_op_crea.f_visibility_maxload_allow
            d["f_visibility_maxload_cull_method"] = scat_op_crea.f_visibility_maxload_cull_method
            d["f_visibility_maxload_treshold"] = scat_op_crea.f_visibility_maxload_treshold
        else: 
            d["f_visibility_facepreview_allow"] = False

            d["f_visibility_cam_allow"] = False
            d["f_visibility_camclip_allow"] = False
            d["f_visibility_camclip_cam_boost_xy"] = 0
            d["f_visibility_camdist_allow"] = False
            d["f_visibility_camdist_min"] = 0
            d["f_visibility_camdist_max"] = 0

            d["f_visibility_maxload_allow"] = False
            d["f_visibility_maxload_cull_method"] = 0
            d["f_visibility_maxload_treshold"] = 0

        #biomes ignore display settings, they use their own encoded display in .biome format

        if (self.__class__.__name__ not in ("SCATTER5_PR_creation_operator_load_biome")):
            d["f_display_allow"] = scat_op_crea.f_display_allow
            d["f_display_method"] = scat_op_crea.f_display_method
            d["f_display_custom_placeholder_ptr"] = scat_op_crea.f_display_custom_placeholder_ptr
        else: 
            d["f_display_allow"] = False
            d["f_display_method"] = None
            d["f_display_custom_placeholder_ptr"] = None

        d["f_display_bounding_box"] = scat_op_crea.f_display_bounding_box

        #operators that do not support special masks will automatically ignore the following

        d["f_mask_action_method"] = getattr(self, "f_mask_action_method", "none",)
        d["f_mask_action_type"] = getattr(self, "f_mask_action_type", None,)
        d["f_mask_assign_vg"] = getattr(self, "f_mask_assign_vg", None,)
        d["f_mask_assign_bitmap"] = getattr(self, "f_mask_assign_bitmap", None,)
        d["f_mask_assign_curve"] = getattr(self, "f_mask_assign_curve", None,)
        d["f_mask_assign_reverse"] = getattr(self, "f_mask_assign_reverse", None,)
        d["f_mask_paint_vg"] = getattr(self, "f_mask_paint_vg", None,)
        d["f_mask_paint_bitmap"] = getattr(self, "f_mask_paint_bitmap", None,)
        d["f_mask_paint_curve"] = getattr(self, "f_mask_paint_curve", None,)
        d["f_mask_action_type_curve_subtype"] = getattr(self, "f_mask_action_type_curve_subtype", None,)
        d["f_mask_spline_width"] = getattr(self, "f_mask_spline_width", None,)
        
        #security settings (quick scatter & manual scatter do not need them)

        if (self.__class__.__name__ not in ("SCATTER5_PR_creation_operator_add_psy_modal","SCATTER5_PR_creation_operator_add_psy_manual")):
            d["f_sec_count_allow"] = scat_op_crea.f_sec_count_allow
            d["f_sec_count"] = scat_op_crea.f_sec_count
            d["f_sec_verts_allow"] = scat_op_crea.f_sec_verts_allow
            d["f_sec_verts"] = scat_op_crea.f_sec_verts
        else:
            d["f_sec_count_allow"] = False
            d["f_sec_verts_allow"] = False

        return d


    def estimate_future_instance_count(self, surfaces=[], d=None, preset_density=None, preset_keyword="", refresh_square_area=True,):
        """estimate a future particle count of a scatter-system before it's created by looking at preset and emitting surface(s)
        parameters: either pass settings_dict `d` or pass `preset_density` & `preset_keyword` """

        # Note that this estimation calculation is also done in  ui_creation.draw_scattering(self,layout) for preset GUI prupose...
        # some on creation options can affect final particle count, however not all can be taken into consideration. this is an appromaximative forecast

        scat_scene   = bpy.context.scene.scatter5
        scat_ops     = scat_scene.operators
        scat_op_crea = scat_ops.create_operators

        #creation settings we'll take into consideration 
        ctxt_op_sett = self.get_context_f_settings()
        count = 0

        #no problematic instance count will be appended if we use this optimization method
        if (ctxt_op_sett["f_visibility_hide_viewport"]):
            return 0

        #no problematic instance count will be appended if we use this optimization method
        if (ctxt_op_sett["f_visibility_cam_allow"]):
            return 0

        #no problematic instance count will be appended if we use this optimization method
        if (ctxt_op_sett["f_mask_action_method"]=='paint'):
            return 0

        #if passed a preset, then we have to fill preset_density & preset_keyword
        if (d is not None):
            preset_density = d["estimated_density"] if ("estimated_density" in d) else 0
            preset_keyword = ""
            if ("s_distribution_space" in d):
                preset_keyword += " "+d["s_distribution_space"]
            if ("s_distribution_method" in d):
                preset_keyword += " "+d["s_distribution_method"]

        #Should not be possible
        if (preset_keyword==""):
            return -1

        #these distribution methods aren't currently predictible
        if any(keyword in preset_keyword for keyword in ('volume','manual_all','random_stable','projbezarea','projbezline','projempties')):
            return 0
            
        if ('verts' in preset_keyword):
            return sum(len(s.data.vertices) for s in surfaces)

        if ('faces' in preset_keyword):
            return sum(len(s.data.polygons) for s in surfaces)

        if ('edges' in preset_keyword):
            return sum(len(s.data.edges) for s in surfaces)

        #most common, other distribution modes are exotic
        if (('random' in preset_keyword) or ('clumping' in preset_keyword)):

            #estimate surface area
            square_area = 0
            for s in surfaces:
                surface_area = s.scatter5.estimate_square_area() if refresh_square_area else s.scatter5.estimated_square_area
                if ('global' in preset_keyword):
                    surface_area *= sum(s.scale)/3
                square_area += surface_area
                continue

            #estimate selection square area if selection
            if (ctxt_op_sett["f_visibility_facepreview_allow"]): 
                square_area = sum(s.scatter5.s_visibility_facepreview_area for s in surfaces)

            #Instance-Count
            count = int(square_area*preset_density)

            #viewport % reduction
            if (ctxt_op_sett["f_visibility_view_allow"]):
                count = (count/100)*(100-ctxt_op_sett["f_visibility_view_percentage"])

        #estimate count if visibility maxload optimization method engaged
        if (ctxt_op_sett["f_visibility_maxload_allow"]):
            if (count>ctxt_op_sett["f_visibility_maxload_treshold"]):
                
                if (ctxt_op_sett["f_visibility_maxload_cull_method"]=="maxload_shutdown"):
                    return 0
                elif (ctxt_op_sett["f_visibility_maxload_cull_method"]=="maxload_limit"):
                    return ctxt_op_sett["f_visibility_maxload_treshold"]

        return count
    

    def set_psy_context_f_actions(self, context, p=None, d={}, surfaces=None, instances=None, pop_msg=True,):
        """tweak scatter-system depending on context f settings"""
        
        #load f_settings in current scope
        ctxt_op_sett = self.get_context_f_settings()

        #Visibility Settings 

        if (ctxt_op_sett["f_visibility_facepreview_allow"]): #Face Preview
            p.s_visibility_facepreview_allow = True

        if (ctxt_op_sett["f_visibility_view_allow"]): #Viewport % Optimization
            p.s_visibility_view_allow = True
            p.s_visibility_view_percentage = ctxt_op_sett["f_visibility_view_percentage"]

        if (ctxt_op_sett["f_visibility_cam_allow"]): #Camera Optimization
            p.s_visibility_cam_allow = True

            p.s_visibility_camclip_allow = ctxt_op_sett["f_visibility_camclip_allow"]
            if (ctxt_op_sett["f_visibility_camclip_allow"]):
                p.s_visibility_camclip_cam_boost_xy = [ctxt_op_sett["f_visibility_camclip_cam_boost_xy"]]*2
            
            p.s_visibility_camdist_allow = ctxt_op_sett["f_visibility_camdist_allow"]
            if (ctxt_op_sett["f_visibility_camdist_allow"]):
                p.s_visibility_camdist_min = ctxt_op_sett["f_visibility_camdist_min"]
                p.s_visibility_camdist_max = ctxt_op_sett["f_visibility_camdist_max"]

        if (ctxt_op_sett["f_visibility_maxload_allow"]): #Maximal Load
            p.s_visibility_maxload_allow = True 
            p.s_visibility_maxload_cull_method = ctxt_op_sett["f_visibility_maxload_cull_method"]
            p.s_visibility_maxload_treshold = ctxt_op_sett["f_visibility_maxload_treshold"]

        #Display Settings

        if (ctxt_op_sett["f_display_allow"]):
            p.s_display_allow = True
            
            if (ctxt_op_sett["f_display_method"]!='none'):
                p.s_display_method = ctxt_op_sett["f_display_method"]

                if (ctxt_op_sett["f_display_method"]=='placeholder_custom'):
                    p.s_display_custom_placeholder_ptr = ctxt_op_sett["f_display_custom_placeholder_ptr"]

        if (ctxt_op_sett["f_display_bounding_box"]): #BoundingBox Display of instances
            for o in instances:
                o.display_type = 'BOUNDS'

        #Special Direct Actions Masks

        if (ctxt_op_sett["f_mask_action_method"]!='none'):

            #mask implementation heavily changes if using load_biome operator
            
            if (self.__class__.__name__=='SCATTER5_PR_creation_operator_load_biome'):
                
                #biome masks are implemented on a group level! except for bezier-area, we use the specific bezier-area distribution for this case
                #biomes by default are assigned to a group, except if scattering a single layer
                
                g = p.get_group()
                
                #biomes direct paint actions are implemented on the load_biome operator directly,
                #so not from here, here we simple assign groups, paint and assign are used in a similar manner
                
                if (ctxt_op_sett["f_mask_action_method"]=='paint'):
                    ctxt_op_sett["f_mask_assign_vg"] = ctxt_op_sett["f_mask_paint_vg"]
                    ctxt_op_sett["f_mask_assign_bitmap"] = ctxt_op_sett["f_mask_paint_bitmap"]
                    ctxt_op_sett["f_mask_assign_curve"] = ctxt_op_sett["f_mask_paint_curve"]        
                    ctxt_op_sett["f_mask_assign_reverse"] = True #Biome painting is always reversed
                
                match ctxt_op_sett["f_mask_action_type"]:
                    
                    case 'vg':
                        
                        if (g is None):
                            p.s_mask_vg_allow = True
                            p.s_mask_vg_ptr = ctxt_op_sett["f_mask_assign_vg"]
                            p.s_mask_vg_revert = ctxt_op_sett["f_mask_assign_reverse"]
                        else:
                            if (g.s_gr_mask_vg_allow!=True):                         g.s_gr_mask_vg_allow = True
                            if (g.s_gr_mask_vg_ptr!=ctxt_op_sett["f_mask_assign_vg"]):         g.s_gr_mask_vg_ptr = ctxt_op_sett["f_mask_assign_vg"]
                            if (g.s_gr_mask_vg_revert!=ctxt_op_sett["f_mask_assign_reverse"]): g.s_gr_mask_vg_revert = ctxt_op_sett["f_mask_assign_reverse"]

                    case 'bitmap':
                        
                        if (g is None):
                            p.s_mask_bitmap_allow = True
                            p.s_mask_bitmap_ptr = ctxt_op_sett["f_mask_assign_bitmap"]
                            p.s_mask_bitmap_revert = ctxt_op_sett["f_mask_assign_reverse"]
                        else:
                            if (g.s_gr_mask_bitmap_allow!=True):                         g.s_gr_mask_bitmap_allow = True
                            if (g.s_gr_mask_bitmap_ptr!=ctxt_op_sett["f_mask_assign_bitmap"]):     g.s_gr_mask_bitmap_ptr = ctxt_op_sett["f_mask_assign_bitmap"]
                            if (g.s_gr_mask_bitmap_revert!=ctxt_op_sett["f_mask_assign_reverse"]): g.s_gr_mask_bitmap_revert = ctxt_op_sett["f_mask_assign_reverse"]

                    case 'curve':
                        
                        if (ctxt_op_sett["f_mask_action_type_curve_subtype"]=='mask'):
                            if (g is None):
                                p.s_mask_curve_allow = True
                                p.s_mask_curve_ptr = ctxt_op_sett["f_mask_assign_curve"]
                                p.s_mask_curve_revert = True #ctxt_op_sett["f_mask_assign_reverse"]
                            else:
                                if (g.s_gr_mask_curve_allow!=True):                         g.s_gr_mask_curve_allow = True
                                if (g.s_gr_mask_curve_ptr!=ctxt_op_sett["f_mask_assign_curve"]): g.s_gr_mask_curve_ptr = ctxt_op_sett["f_mask_assign_curve"]
                                if (g.s_gr_mask_curve_revert!=ctxt_op_sett["f_mask_assign_reverse"]): g.s_gr_mask_curve_revert = ctxt_op_sett["f_mask_assign_reverse"]
                        
                        elif (ctxt_op_sett["f_mask_action_type_curve_subtype"]=='dist'):
                            p.s_distribution_method = 'projbezarea'
                            p.s_distribution_projbezarea_space = 'global'
                            p.set_general_space(space='global')
                            p.s_distribution_projbezarea_density = p.s_distribution_density
                            p.s_distribution_projbezarea_seed = p.s_distribution_seed
                            p.s_distribution_projbezarea_limit_distance_allow = p.s_distribution_limit_distance_allow
                            p.s_distribution_projbezarea_limit_distance = p.s_distribution_limit_distance
                            p.s_distribution_projbezarea_curve_ptr = ctxt_op_sett["f_mask_assign_curve"]
                            
                    case 'draw':
                        
                        p.s_distribution_method = 'projbezline'
                        p.s_distribution_projbezline_normal_method = 'surf'
                        p.set_general_space(space='global')
                        p.s_distribution_projbezline_patharea_density = p.s_distribution_density
                        p.s_distribution_projbezline_patharea_width = ctxt_op_sett["f_mask_spline_width"]
                        p.s_distribution_projbezline_patharea_radiusinfl_allow = True
                        p.s_distribution_projbezline_seed = p.s_distribution_seed
                        p.s_distribution_projbezline_limit_distance_allow = p.s_distribution_limit_distance_allow
                        p.s_distribution_projbezline_limit_distance = p.s_distribution_limit_distance
                        p.s_distribution_projbezline_curve_ptr = ctxt_op_sett["f_mask_assign_curve"]
                            
            else: #mask implementation in the context of any other add_psy operator..
                
                match ctxt_op_sett["f_mask_action_method"]:
                    
                    case 'paint': #direct action of painting a mask?

                        if (ctxt_op_sett["f_mask_action_type"]=='vg'):
                            
                            i = 1
                            vg_name = "DirectPaint"
                            while vg_name in [v.name for o in surfaces for v in o.vertex_groups]:
                                vg_name = f"DirectPaint.{i:03}"
                                i += 1
                            for s in surfaces:
                                s.vertex_groups.new(name=vg_name)
                            p.s_mask_vg_allow = True
                            p.s_mask_vg_ptr = vg_name
                            p.s_mask_vg_revert = True
                            bpy.ops.scatter5.vg_quick_paint(mode='vg', group_name=vg_name,)

                        elif (ctxt_op_sett["f_mask_action_type"]=='bitmap'):
                            
                            img = bpy.data.images.new("ImageMask", 1000, 1000,)
                            p.s_mask_bitmap_allow = True
                            p.s_mask_bitmap_ptr = img.name
                            p.s_mask_bitmap_revert = True
                            bpy.ops.scatter5.image_utils(option='paint', paint_color=(1,1,1), img_name=img.name,)

                        elif (ctxt_op_sett["f_mask_action_type"] in ('curve','draw')):

                            from .. curve.draw_bezier_spline import add_empty_bezier_spline
                            obj,_ = add_empty_bezier_spline(
                                name="DrawSpline" if (ctxt_op_sett["f_mask_action_type"]=='curve') else "BezierArea",
                                collection="Geo-Scatter User Col",
                                location=(surfaces[0].location.x, surfaces[0].location.y, surfaces[0].bound_box[1][2]) if len(surfaces) else (0,0,0),
                                )
                            
                            if (ctxt_op_sett["f_mask_action_type"]=='curve'):
                                
                                if (ctxt_op_sett["f_mask_action_type_curve_subtype"]=='mask'):
                                    p.s_mask_curve_allow = True
                                    p.s_mask_curve_ptr = obj
                                    p.s_mask_curve_revert = True
                                    
                                elif (ctxt_op_sett["f_mask_action_type_curve_subtype"]=='dist'):
                                    p.s_distribution_method = 'projbezarea'
                                    p.s_distribution_projbezarea_space = 'global'
                                    p.set_general_space(space='global')
                                    p.s_distribution_projbezarea_density = p.s_distribution_density
                                    p.s_distribution_projbezarea_seed = p.s_distribution_seed
                                    p.s_distribution_projbezarea_limit_distance_allow = p.s_distribution_limit_distance_allow
                                    p.s_distribution_projbezarea_limit_distance = p.s_distribution_limit_distance
                                    p.s_distribution_projbezarea_curve_ptr = obj
                            
                            elif (ctxt_op_sett["f_mask_action_type"]=='draw'):
                                p.s_distribution_method = 'projbezline'
                                p.s_distribution_projbezline_normal_method = 'surf'
                                p.set_general_space(space='global')
                                p.s_distribution_projbezline_patharea_density = p.s_distribution_density
                                p.s_distribution_projbezline_patharea_width = ctxt_op_sett["f_mask_spline_width"]
                                p.s_distribution_projbezline_patharea_radiusinfl_allow = True
                                p.s_distribution_projbezline_seed = p.s_distribution_seed
                                p.s_distribution_projbezline_limit_distance_allow = p.s_distribution_limit_distance_allow
                                p.s_distribution_projbezline_limit_distance = p.s_distribution_limit_distance
                                p.s_distribution_projbezline_curve_ptr = obj

                            #bezier area drawing has special context override requisite

                            standalone = True
                            if (self.__class__.__name__=="SCATTER5_PR_creation_operator_add_psy_modal"):
                                standalone = False #do not display infobox gui if using modal mode.
                            window, area, region = context.window, context.area, context.region
                            if (area.type!='VIEW_3D'):
                                region_data = get_any_view3d_region(context=context, context_window_first=True,)
                                if (region_data):
                                      window, area, region = region_data
                                else: window, area, region = None, None, None
                            if (region):
                                with context.temp_override(window=window, area=area, region=region):
                                    if (ctxt_op_sett["f_mask_action_type"]=='curve'):
                                          bpy.ops.scatter5.draw_bezier_area('INVOKE_DEFAULT', False, edit_existing=obj.name, standalone=standalone,)
                                    else: bpy.ops.scatter5.draw_bezier_spline('INVOKE_DEFAULT', False, curve_name=obj.name,)

                    case 'assign': #or direct action of simply assigning a mask?

                        if (ctxt_op_sett["f_mask_action_type"]=='vg'):
                            p.s_mask_vg_allow = True
                            p.s_mask_vg_ptr = ctxt_op_sett["f_mask_assign_vg"]
                            p.s_mask_vg_revert = ctxt_op_sett["f_mask_assign_reverse"]

                        elif (ctxt_op_sett["f_mask_action_type"]=='bitmap'):
                            p.s_mask_bitmap_allow = True
                            p.s_mask_bitmap_ptr = ctxt_op_sett["f_mask_assign_bitmap"]
                            p.s_mask_bitmap_revert = ctxt_op_sett["f_mask_assign_reverse"]

                        elif (ctxt_op_sett["f_mask_action_type"]=='curve'):

                            if (ctxt_op_sett["f_mask_action_type_curve_subtype"]=='mask'):
                                p.s_mask_curve_allow = True
                                p.s_mask_curve_ptr = ctxt_op_sett["f_mask_assign_curve"]
                                p.s_mask_curve_revert = True #ctxt_op_sett["f_mask_assign_reverse"]
                                
                            elif (ctxt_op_sett["f_mask_action_type_curve_subtype"]=='dist'):
                                p.s_distribution_method = 'projbezarea'
                                p.s_distribution_projbezarea_space = 'global'
                                p.set_general_space(space='global')
                                p.s_distribution_projbezarea_density = p.s_distribution_density
                                p.s_distribution_projbezarea_seed = p.s_distribution_seed
                                p.s_distribution_projbezarea_limit_distance_allow = p.s_distribution_limit_distance_allow
                                p.s_distribution_projbezarea_limit_distance = p.s_distribution_limit_distance
                                p.s_distribution_projbezarea_curve_ptr = ctxt_op_sett["f_mask_assign_curve"]

                        elif (ctxt_op_sett["f_mask_action_type"]=='draw'):
                            p.s_distribution_method = 'projbezline'
                            p.s_distribution_projbezline_normal_method = 'surf'
                            p.set_general_space(space='global')
                            p.s_distribution_projbezline_patharea_density = p.s_distribution_density
                            p.s_distribution_projbezline_seed = p.s_distribution_seed
                            p.s_distribution_projbezline_limit_distance_allow = p.s_distribution_limit_distance_allow
                            p.s_distribution_projbezline_limit_distance = p.s_distribution_limit_distance
                            p.s_distribution_projbezline_curve_ptr = ctxt_op_sett["f_mask_assign_curve"]
            
        #Now time to Unhide the system (done at the end for optimization purpose & for security behavior)

        #will pop security msg?
        pop_msg_scatter, pop_msg_poly, max_poly = False, False, 0
        
        #by default, always visible
        is_visible = True

        #except if creation settings is overriding
        if (ctxt_op_sett["f_visibility_hide_viewport"]):
            is_visible = False

        #Security Threshold Estimated Particle Count
        if (ctxt_op_sett["f_sec_count_allow"]):

            #either we pass the dict of settings (most efficient way to calculate) or we pass distribution method/density
            if (d!={}):
                  count = self.estimate_future_instance_count(surfaces=surfaces, d=d, refresh_square_area=True,)
            else: count = self.estimate_future_instance_count(
                    surfaces=surfaces,
                    preset_density=p.s_distribution_density,
                    preset_keyword=p.s_distribution_method,
                    refresh_square_area=True,
                    )
            
            #check if security count thresgold affects visibility
            if (count>ctxt_op_sett["f_sec_count"]):
                is_visible = False
                pop_msg_scatter = True

        #Security Threshold Instance Polycount
        if (ctxt_op_sett["f_sec_verts_allow"]):

            too_high_poly = [o for o in instances if (o.type=='MESH' and o.display_type!='BOUNDS' and len(o.data.vertices)>=ctxt_op_sett["f_sec_verts"]) ]
            if (len(too_high_poly)!=0):
                pop_msg_poly = True
                
                for o in too_high_poly:
                    o.display_type = 'BOUNDS'
                    continue

        #finally, shall we show the system in viewport?
        if (is_visible):
            p.hide_viewport = False

        #Pop security message with additional options?
        if (pop_msg and (pop_msg_poly or pop_msg_scatter)):
            
            bpy.ops.scatter5.popup_security('INVOKE_DEFAULT',
                scatter=pop_msg_scatter,
                poly=pop_msg_poly,
                emitter=p.id_data.name,
                psy_name_00=p.name,
                )

        return None


# 8888b.  888888 888888 88 88b 88 888888      dP"Yb  88""Yb .dP"Y8     .dP"Y8 888888 888888 888888 
#  8I  Yb 88__   88__   88 88Yb88 88__       dP   Yb 88__dP `Ybo."     `Ybo." 88__     88     88   
#  8I  dY 88""   88""   88 88 Y88 88""       Yb   dP 88"""  o.`Y8b     o.`Y8b 88""     88     88   
# 8888Y"  888888 88     88 88  Y8 888888      YbodP  88     8bodP'     8bodP' 888888   88     88   

#assemble our operators propgroup from a bunch of properties and functions

class SCATTER5_PR_creation_operators(bpy.types.PropertyGroup, Inherit_f_visibility_settings, Inherit_f_display_settings, Inherit_f_security_settings, Inherit_f_surfaces,):
    """scat_op = bpy.context.scene.scatter5.operators.create_operators
    shared decentralized settings of most creation panel operators"""

    #+f_surfaces
    #+f_visibility
    #+f_display
    #+f_sec
    
    pass


class SCATTER5_PR_creation_operator_add_psy_density(bpy.types.PropertyGroup, Inherit_f_mask_settings, Inherit_utils_fcts,):
    """scat_op = bpy.context.scene.scatter5.operators.add_psy_density
    decentralized settings of SCATTER5_OT_add_psy_density"""

    #density options

    f_distribution_density : bpy.props.FloatProperty(
        name=translate("Instances"), 
        default=10,
        min=0,
        precision=3,
        )
    f_density_scale : bpy.props.EnumProperty(
        name=translate("Density Scale"),
        default="m", 
        items=( ("cm", "/ cm²", "",),
                ("m", "/ m²", "",),
                ("ha", "/ ha", "",),
                ("km", "/ km²", "",),
              ),
        )

    #selection method 

    selection_mode : bpy.props.EnumProperty(
        name=translate("Selection Method"),
        description=translate("Would you like to scatter the selection of the viewport or of the asset-browser?"),
        default="viewport", 
        items=( ("viewport", translate("Viewport Selection"), translate("Scatter the compatible selected-objects of your 3DViewport"), "VIEW3D",1 ),
                ("browser", translate("Browser Selection"), translate("Scatter the selected-objects of your asset browser"), "ASSET_MANAGER",2 ),
              ),
        )

    #+f_mask

    #+utils fcts 


class SCATTER5_PR_creation_operator_add_psy_preset(bpy.types.PropertyGroup, Inherit_f_mask_settings, Inherit_utils_fcts,): 
    """scat_op = bpy.context.scene.scatter5.operators.add_psy_preset
    decentralized settings of SCATTER5_OT_add_psy_preset"""

    #used mostly in creation interface, 
    #args will be passed from interface to operator

    preset_path : bpy.props.StringProperty(
        default="Please Choose a Preset First!",
        subtype="FILE_PATH",
        ) 
    preset_name : bpy.props.StringProperty(
        name=translate("Display Name"),
        description=translate("Future name of your particle system."),
        default="Default Preset",
        )
    preset_color : bpy.props.FloatVectorProperty( #default color used for preset_find_color if nothing found. only used for GUI
        name=translate("Display Color"),
        description=translate("Future color of your particle system."),
        size=4,
        default=(1,1,1,1),
        min=0,
        max=1,
        subtype="COLOR",
        )
    preset_find_name : bpy.props.BoolProperty(
        default=False,
        description=translate("Use the name of the first selected instance object as the name of your future scatter-system, instead of the preset name"),
        )
    preset_find_color : bpy.props.BoolProperty(
        default=False,
        description=translate("Use the first material display color of your fist selected instance object as the color of your future scatter-system, instead of the preset color"),
        )

    #estimate in interface directly 

    estimated_preset_density : bpy.props.FloatProperty(
        name=translate("Estimated Instances /m²"),
        default=0,
        )
    estimated_preset_keyword : bpy.props.StringProperty(
        default="",
        ) #in order to estimate the final density we need keyword information

    #selection method 

    selection_mode : bpy.props.EnumProperty(
        name=translate("Selection Method"),
        description=translate("Would you like to scatter the selection of the viewport or of the asset-browser?"),
        default="viewport", 
        items=( ("viewport", translate("Viewport Selection"), translate("Scatter the compatible selected-objects of your 3DViewport"), "VIEW3D",1 ),
                ("browser", translate("Browser Selection"), translate("Scatter the selected-objects of your asset browser"), "ASSET_MANAGER",2 ),
              ),
        )

    #+f_mask

    #+utils fcts


class SCATTER5_PR_creation_operator_add_psy_manual(bpy.types.PropertyGroup, Inherit_utils_fcts,):
    """scat_op = bpy.context.scene.scatter5.operators.add_psy_manual
    decentralized settings of SCATTER5_OT_add_psy_manual"""

    #special rotation options for manual scatter operator

    f_rot_random_allow : bpy.props.BoolProperty(
        default=False,
        description=translate("Enable the 'Tweak>Rotation>Random Rotation' procedural setting directly upon creation. When choosing this option, the instances will be randomly rotated in addition to the original rotation defined in manual mode"),
        )
    f_scale_random_allow : bpy.props.BoolProperty(
        default=False,
        description=translate("Enable the 'Tweak>Scale>Random Scale' procedural setting directly upon creation. When choosing this option, the instances will be randomly rescaled in addition to the original scale defined in manual mode"),
        )

    #selection method 

    selection_mode : bpy.props.EnumProperty(
        name=translate("Selection Method"),
        description=translate("Would you like to scatter the selection of the viewport or of the asset-browser?"),
        default="viewport", 
        items=( ("viewport", translate("Viewport Selection"), translate("Scatter the compatible selected-objects of your 3DViewport"), "VIEW3D",1 ),
                ("browser", translate("Browser Selection"), translate("Scatter the selected-objects of your asset browser"), "ASSET_MANAGER",2 ),
              ),
        )
    
    #+utils fcts
    

class SCATTER5_PR_creation_operator_add_psy_modal(bpy.types.PropertyGroup, Inherit_f_mask_settings, Inherit_utils_fcts,):
    """scat_op = bpy.context.scene.scatter5.operators.add_psy_modal
    decentralized settings of the add_psy_modal series of operators"""

    #define default density

    f_distribution_density : bpy.props.FloatProperty(
        name=translate("Instances/m²"), 
        description=translate("Default distribution density for the Quick-Scatter operator"),
        default=3,
        min=0,
        precision=3,
        )

    #+f_mask (using method&type, hidden from user, used by operator)
    
    #+utils fcts


class SCATTER5_PR_creation_operator_load_biome(bpy.types.PropertyGroup, Inherit_f_mask_settings, Inherit_utils_fcts,):
    """scat_op = bpy.context.scene.scatter5.operators.load_biome
    decentralized settings of SCATTER5_OT_load_biome"""

    #biomes progress

    progress_bar : bpy.props.FloatProperty(
        default=0,
        subtype="PERCENTAGE",
        soft_min=0, 
        soft_max=100, 
        precision=0,
        )
    progress_label : bpy.props.StringProperty(
        default="",
        )
    progress_context : bpy.props.StringProperty(
        default="",
        )

    #special display for biomes 

    f_display_biome_allow : bpy.props.BoolProperty(
        default=False,
        description=translate("Use the display method encoded in the biome file"),
        )

    #+f_mask

    #+utils fcts
    

class SCATTER5_PR_operators(bpy.types.PropertyGroup): 
    """scat_ops = bpy.context.scene.scatter5.operators"""

    #settings for export ops (there's a lot of options, justified to be separated from their Op class)
    
    export_to_presets : bpy.props.PointerProperty(type=SCATTER5_PR_export_to_presets)
    export_to_biome : bpy.props.PointerProperty(type=SCATTER5_PR_export_to_biome)
    generate_thumbnail : bpy.props.PointerProperty(type=SCATTER5_PR_generate_thumbnail)
    
    #settings for scattering operators, all stored in the 'Create' > 'On Creation' Popover
    
    create_operators : bpy.props.PointerProperty(type=SCATTER5_PR_creation_operators) #these are shared across all creation operators
    add_psy_preset : bpy.props.PointerProperty(type=SCATTER5_PR_creation_operator_add_psy_preset)
    add_psy_density : bpy.props.PointerProperty(type=SCATTER5_PR_creation_operator_add_psy_density)
    add_psy_manual : bpy.props.PointerProperty(type=SCATTER5_PR_creation_operator_add_psy_manual)
    add_psy_modal : bpy.props.PointerProperty(type=SCATTER5_PR_creation_operator_add_psy_modal)
    load_biome : bpy.props.PointerProperty(type=SCATTER5_PR_creation_operator_load_biome)