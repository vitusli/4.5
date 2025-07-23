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
# (c) 2024 Jakub Uhlik

import bpy
from bpy.props import BoolProperty, FloatProperty, IntProperty, FloatVectorProperty
from bpy.types import PropertyGroup
from .. translations import translate


# NOTE: upon ToolTheme instatiation, this is read from its `__init__` and ONLY modified values written into instance.
# NOTE: values NOT user modified are left as they are defined in ToolTheme fields
# NOTE: because only modified are read, default values much MATCH exactly with defaults in ToolTheme fields
# NOTE: ToolTheme fields begin with underscore, props can't begin with underscore, so prop names are the same only without underscore
# NOTE: for fields that depends on `ui_scale` or `ui_line_width`, `*_default` values has to be linked here
# NOTE: prop `name` that does not match any `_name` in ToolTheme are ignored
class SCATTER5_PR_preferences_theme(PropertyGroup, ):
    show_ui: BoolProperty(name=translate("Show Options"), default=False, )
    
    circle_steps: IntProperty(name=translate("Circle Steps"), default=32, min=6, description="", )
    
    fixed_radius_default: IntProperty(name=translate("Fixed Radius"), default=48, min=24, description="", )
    fixed_center_dot_radius_default: IntProperty(name=translate("Fixed Dot Radius"), default=3, min=3, description="", )
    
    no_entry_sign_size_default: IntProperty(name=translate("No Entry Sign Size"), default=16, min=16, description="", )
    no_entry_sign_color: FloatVectorProperty(name=translate("No Entry Sign Color"), default=(1.0, 1.0, 1.0, 0.5, ), min=0, max=1, subtype='COLOR_GAMMA', size=4, description="", )
    no_entry_sign_thickness_default: IntProperty(name=translate("No Entry Sign Thickness"), default=2, min=1, description="", )
    
    default_outline_color: FloatVectorProperty(name=translate("Outline Color"), default=(1.0, 1.0, 1.0, 1.0, ), min=0, max=1, subtype='COLOR_GAMMA', size=4, description="", )
    default_outline_color_press: FloatVectorProperty(name=translate("Outline Color Press"), default=(1.0, 1.0, 0.5, 1.0, ), min=0, max=1, subtype='COLOR_GAMMA', size=4, description="", )
    outline_color_eraser: FloatVectorProperty(name=translate("Outline Color Eraser"), default=(1.0, 0.5, 0.4, 1.0, ), min=0, max=1, subtype='COLOR_GAMMA', size=4, description="", )
    outline_color_hint: FloatVectorProperty(name=translate("Outline Color Hint"), default=(0.4, 1.0, 1.0, 1.0 / 8, ), min=0, max=1, subtype='COLOR_GAMMA', size=4, description="", )
    
    outline_color_disabled_alpha: FloatProperty(name=translate("Outline Disabled Alpha"), default=1.0 / 2, min=0.0, max=1.0, subtype='FACTOR', description="", )
    outline_color_helper_alpha: FloatProperty(name=translate("Outline Helper Alpha"), default=1.0 / 4, min=0.0, max=1.0, subtype='FACTOR', description="", )
    outline_color_gesture_helper_alpha: FloatProperty(name=translate("Outline Gesture Helper Alpha"), default=1.0 / 2, min=0.0, max=1.0, subtype='FACTOR', description="", )
    outline_color_falloff_helper_alpha: FloatProperty(name=translate("Outline Falloff Helper Alpha"), default=1.0 / 2, min=0.0, max=1.0, subtype='FACTOR', description="", )
    
    outline_thickness_default: IntProperty(name=translate("Outline Thickness"), default=2, min=1, description="", )
    outline_thickness_helper_default: IntProperty(name=translate("Outline Helper Thickness"), default=1, min=1, description="", )
    outline_dashed_steps_multiplier: IntProperty(name=translate("Outline Dashed Steps Multiplier"), default=2, min=1, description="", )
    
    default_fill_color: FloatVectorProperty(name=translate("Fill Color"), default=(1.0, 1.0, 1.0, 0.05, ), min=0, max=1, subtype='COLOR_GAMMA', size=4, description="", )
    default_fill_color_press: FloatVectorProperty(name=translate("Fill Color Press"), default=(1.0, 1.0, 0.5, 0.05, ), min=0, max=1, subtype='COLOR_GAMMA', size=4, description="", )
    fill_color_press_eraser: FloatVectorProperty(name=translate("Fill Color Eraser"), default=(1.0, 0.5, 0.4, 0.05, ), min=0, max=1, subtype='COLOR_GAMMA', size=4, description="", )
    fill_color_helper_hint: FloatVectorProperty(name=translate("Fill Color Hint"), default=(0.4, 1.0, 1.0, 0.05 / 16, ), min=0, max=1, subtype='COLOR_GAMMA', size=4, description="", )
    
    fill_color_disabled_alpha: FloatProperty(name=translate("Fill Disabled Alpha"), default=0.05 / 2, min=0.0, max=1.0, subtype='FACTOR', description="", )
    fill_color_helper_alpha: FloatProperty(name=translate("Fill Helper Alpha"), default=0.05 / 4, min=0.0, max=1.0, subtype='FACTOR', description="", )
    fill_color_gesture_helper_alpha: FloatProperty(name=translate("Fill Gesture Helper Alpha"), default=0.05 * 2, min=0.0, max=1.0, subtype='FACTOR', description="", )
    
    text_size_default: IntProperty(name=translate("Text Size"), default=11, min=11, description="", )
    text_color: FloatVectorProperty(name=translate("Text Color"), default=(1.0, 1.0, 1.0, 1.0, ), min=0, max=1, subtype='COLOR_GAMMA', size=4, description="", )
    
    text_tooltip_outline_color: FloatVectorProperty(name=translate("Tooltip Outline Color"), default=(0.12, 0.12, 0.12, 0.95, ), min=0, max=1, subtype='COLOR_GAMMA', size=4, description="", )
    text_tooltip_background_color: FloatVectorProperty(name=translate("Tooltip Background Color"), default=(0.12, 0.12, 0.12, 0.95, ), min=0, max=1, subtype='COLOR_GAMMA', size=4, description="", )
    text_tooltip_outline_thickness: IntProperty(name=translate("Tooltip Outline Thickness"), default=2, min=1, description="", )
    
    point_size_default: IntProperty(name=translate("Point Size"), default=4, min=1, description="", )
    
    grid_overlay_size: IntProperty(name=translate("Overlay Grid Size"), default=1, min=1, description="", )
    grid_overlay_color_a: FloatVectorProperty(name=translate("Overlay Grid Color A"), default=(0.0, 0.0, 0.0, 1.0, ), min=0, max=1, subtype='COLOR_GAMMA', size=4, description="", )
    grid_overlay_color_b: FloatVectorProperty(name=translate("Overlay Grid Color B"), default=(0.0, 0.0, 0.0, 0.25, ), min=0, max=1, subtype='COLOR_GAMMA', size=4, description="", )
    
    info_box_scale: FloatProperty(name=translate("Infobox Scale"), default=1.0, min=0.5, description="", )
    info_box_shadow_color: FloatVectorProperty(name=translate("Infobox Shadow Color"), default=(0.0, 0.0, 0.0, 0.5, ), min=0, max=1, subtype='COLOR_GAMMA', size=4, description="", )
    info_box_fill_color: FloatVectorProperty(name=translate("Infobox Fill Color"), default=(0.12, 0.12, 0.12, 0.95, ), min=0, max=1, subtype='COLOR_GAMMA', size=4, description="", )
    info_box_outline_color: FloatVectorProperty(name=translate("Infobox Outline Color"), default=(0.12, 0.12, 0.12, 0.95, ), min=0, max=1, subtype='COLOR_GAMMA', size=4, description="", )
    info_box_outline_thickness_default: IntProperty(name=translate("Infobox Outline Thickness"), default=2, min=1, description="", )
    info_box_logo_color: FloatVectorProperty(name=translate("Infobox Logo Color"), default=(1.0, 1.0, 1.0, 1.0, ), min=0, max=1, subtype='COLOR_GAMMA', size=4, description="", )
    info_box_text_header_color: FloatVectorProperty(name=translate("Infobox Text Header Color"), default=(1.0, 1.0, 1.0, 1.0, ), min=0, max=1, subtype='COLOR_GAMMA', size=4, description="", )
    info_box_text_body_color: FloatVectorProperty(name=translate("Infobox Text Body Color"), default=(0.8, 0.8, 0.8, 1.0, ), min=0, max=1, subtype='COLOR_GAMMA', size=4, description="", )


classes = (
    SCATTER5_PR_preferences_theme,
)
