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


from . import (
        
    ao,
    light,
    slope, 
    height, 
    aspect,
    normal, 
    border,
    boolean,
    position,
    curvature,
    mesh_data,
    watershed,
    camera_visibility,
    layer_paint,
    bezier_path,
    bezier_area,
    particle_proximity,
    texture_mask,
    vcol_to_vgroup,
    vgroup_split,
    vgroup_merge,

    )



from . boolean import SCATTER5_OT_mask_boolean_add_to_coll, SCATTER5_OT_mask_boolean_parameters
from . layer_paint import SCATTER5_OT_layer_paint_mode, SCATTER5_OT_layer_paint_reverse, SCATTER5_OT_layer_paint_fill


classes = (
    
    SCATTER5_OT_mask_boolean_add_to_coll,  
    SCATTER5_OT_mask_boolean_parameters,  
    
    SCATTER5_OT_layer_paint_mode,
    SCATTER5_OT_layer_paint_reverse,
    SCATTER5_OT_layer_paint_fill,

    )