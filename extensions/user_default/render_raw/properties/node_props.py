'''
Copyright (C) 2024 Orange Turbine
https://orangeturbine.com
orangeturbine@cgcookie.com

This file is part of the Render Raw add-on, created by Jonathan Lampel for Orange Turbine.

All code distributed with this add-on is open source as described below.

Render Raw is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 3
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, see <https://www.gnu.org/licenses/>.
'''

import bpy
from ..utilities.presets import apply_active_layer_preset, preset_items
from ..utilities.view_transforms import get_view_transforms, update_view_transform
from ..nodes.update_RR import update_all
from ..nodes.update_colors import (
    update_saturation, update_white_balance, update_hue, update_color_balance, update_color_blending,
    update_value_saturation, update_color_boost, update_color_panel, update_preserve_color, update_fix_clipping
)
from ..nodes.update_details import (
    update_sharpness, update_texture, update_clarity, update_details_panel
)
from ..nodes.update_effects import (
    update_vignette, update_glare, update_bloom, update_streaks, update_ghosting, update_distortion, update_grain,
    update_effects_panel
)
from ..nodes.update_values import (
    update_exposure, update_gamma, update_contrast, update_values, update_clipping, update_value_panel,
    update_pre_curves, update_post_curves
)
from ..nodes.update_alpha import update_alpha
from ..nodes.update_layer import update_active_layer, update_layer_name


class RenderRawSettings(bpy.types.PropertyGroup):
    """
    The General settings are stored on the main Render Raw node group
    while the rest of the settings are stored on the individual layer groups

    Lambda functions are used for updates so the actual functions can
    accept optional arguments and be reused for other operations

    """

    """ General """
    #region
    view_transform: bpy.props.EnumProperty(
        name = 'View Transform',
        description = 'View used when converting an image to a display space',
        items = get_view_transforms(),
        default = 'AgX Base sRGB',
        update = lambda self, context: update_view_transform(self, context)
    )
    active_layer_index: bpy.props.IntProperty(
        default = 0,
        update = lambda self, context: update_active_layer(self, context)
    )
    alpha_method: bpy.props.EnumProperty(
        name = 'Method',
        items = [
            ('0', 'Straight', 'Converts the alpha to straight'),
            ('1', 'Premultiplied', 'Converts the alpha method to premultiplied'),
        ],
        default = '1',
        update = lambda self, context: update_alpha(self, context)
    )
    alpha_factor: bpy.props.FloatProperty(
        name = 'Factor',
        description = "Adjusts how much straight or premultiplied alpha is mixed in",
        default = 0.5,
        min = 0,
        max = 1,
        update = lambda self, context: update_alpha(self, context)
    )
    use_clipping: bpy.props.BoolProperty(
        name = 'Use Clipping',
        default = False,
        update = lambda self, context: update_clipping(self, context)
    )
    clipping_blacks: bpy.props.FloatVectorProperty(
        name = 'Black Highlight',
        description = "Color overlay for areas with a value of 0. The overlay strength can be set via the color's alpha",
        subtype = 'COLOR',
        min = 0,
        max = 1,
        size=4,
        default=[0, 0, 1, 1],
        update = lambda self, context: update_clipping(self, context)
    )
    clipping_whites: bpy.props.FloatVectorProperty(
        name = 'White Highlight',
        description = "Color overlay areas with a value of 1. The overlay strength can be set via the color's alpha",
        subtype = 'COLOR',
        min = 0,
        max = 1,
        size=4,
        default=[1, 0, 0, 1],
        update = lambda self, context: update_clipping(self, context)
    )
    clipping_saturation: bpy.props.FloatVectorProperty(
        name = 'Fully Saturated Highlight',
        description = "Color overlay for 100 percent saturated areas. The overlay strength can be set via the color's alpha",
        subtype = 'COLOR_GAMMA',
        min = 0,
        max = 1,
        size=4,
        default=[1, 1, 1, 0],
        update = lambda self, context: update_clipping(self, context)
    )
    clipping_black_threshold: bpy.props.FloatProperty(
        name = 'Black Threshold',
        description = "Any value below this number will get the overlay",
        default = 0.0001,
        precision = 5,
        step = .01,
        min = 0,
        max = 1,
        update = lambda self, context: update_clipping(self, context)
    )
    clipping_white_threshold: bpy.props.FloatProperty(
        name = 'White Threshold',
        description = "Any value above this number will get the overlay",
        default = 0.9999,
        precision = 5,
        step = .01,
        min = 0,
        max = 1,
        update = lambda self, context: update_clipping(self, context)
    )
    clipping_saturation_threshold: bpy.props.FloatProperty(
        name = 'Saturation Threshold',
        description = "Any HSL saturation above this number will get the overlay",
        default = 0.9999,
        precision = 5,
        step = .01,
        min = 0,
        max = 1,
        update = lambda self, context: update_clipping(self, context)
    )
    clipping_saturation_multiply: bpy.props.FloatProperty(
        name = 'Ignore Dark Saturation',
        description = "Multiplies ",
        default = 0.25,
        min = 0,
        max = 1,
        update = lambda self, context: update_clipping(self, context)
    )
    display_curves: bpy.props.EnumProperty(
        name = 'Curves',
        items = [
            ('PRE', 'Pre', 'Displays pre-transform curves. They will not cause clipping but are harder to use because they are not bound to the 0-1 range'),
            ('POST', 'Post', 'Displays post-transform curves. They can easily break the image but are easier to use because all values are within the 0-1 range'),
        ],
        default = 'POST'
    )
    display_per_hue: bpy.props.EnumProperty(
        name = 'Per Hue',
        items = [
            ('HUE', 'Hue', 'Displays the Hue Hue controls'),
            ('SATURATION', 'Saturation', 'Displays the Hue Saturation controls'),
            ('VALUE', 'Value', 'Displays the Hue Value controls'),
        ],
        default = 'HUE'
    )
    display_per_value: bpy.props.EnumProperty(
        name = 'Per Value',
        items = [
            ('BLENDING', 'Color', 'Displays the Color Blending per Value controls'),
            ('SATURATION', 'Saturation', 'Displays the Saturation per Value controls'),
        ],
        default = 'BLENDING'
    )
    #endregion

    """ Layer """
    #region
    """
    These settings are stored and accessed on the pre layer but apply to the layer as a whole
    """
    layer_name: bpy.props.StringProperty(
        name = 'Name',
        default = 'New Layer',
        update = lambda self, context: update_layer_name(self, context)
    )
    layer_factor: bpy.props.FloatProperty(
        name = 'Factor',
        description = "Adjusts how much the active layer contributes to the result",
        default = 1,
        min = 0,
        max = 1,
        update = lambda self, context: update_all(self, context)
    )
    use_layer: bpy.props.BoolProperty(
        default = True,
        update = lambda self, context: update_all(self, context)
    )
    use_layer_mask: bpy.props.BoolProperty(
        default = True
    )
    preset: bpy.props.EnumProperty(
        name = 'Preset',
        description = 'Preset configurations of Render Raw settings',
        items = preset_items,
        default = None,
        update = lambda self, context: apply_active_layer_preset(self, context)
    )
    #endregion

    """ Values """
    #region
    use_values: bpy.props.BoolProperty(
        default = True,
        update = lambda self, context: update_value_panel(self, context)
    )
    # Separate controls for viewport and render have not been implemented yet
    use_values_viewport: bpy.props.BoolProperty(
        default = True,
        update = lambda self, context: update_value_panel(self, context)
    )
    use_values_render: bpy.props.BoolProperty(
        default = True,
        update = lambda self, context: update_value_panel(self, context)
    )
    # Pre Transform
    exposure: bpy.props.FloatProperty(
        name = 'Exposure',
        description = 'Sets the exposure pre-transform for the active layer',
        default = 0,
        min = -10,
        max = 10,
        precision = 3,
        update = lambda self, context: update_exposure(self, context)
    )
    gamma: bpy.props.FloatProperty(
        name = 'Gamma',
        description = 'Sets the gamma pre-transform for the active layer',
        default = 1,
        min = 0,
        max = 5,
        precision = 3,
        update = lambda self, context: update_gamma(self, context)
    )
    contrast: bpy.props.FloatProperty(
        name = 'Contrast',
        description = "Adjusts the exposure and gamma at the same time pre-transform to increase contrast, similar to Blender's high or low contrast looks but with more control",
        default = 0,
        min = -1,
        max = 1,
        update = lambda self, context: update_contrast(self, context)
    )
    pre_curves_factor: bpy.props.FloatProperty(
        name = 'Curves Factor',
        description = 'Adjusts how much the RGB curves get applied',
        default = 1,
        min = 0,
        max = 1,
        update = lambda self, context: update_pre_curves(self, context)
    )
    pre_curves_black: bpy.props.FloatVectorProperty(
        name = 'Black Level',
        description = "Color considered as black by the pre-transform curve",
        subtype = 'COLOR_GAMMA',
        default = [0, 0, 0],
        min = 0,
        max = 1,
        update = lambda self, context: update_pre_curves(self, context)
    )
    pre_curves_white: bpy.props.FloatVectorProperty(
        name = 'White Level',
        description = "Color considered as white by the pre-transform curve",
        subtype = 'COLOR_GAMMA',
        default = [1, 1, 1],
        min = 0,
        max = 1,
        update = lambda self, context: update_pre_curves(self, context)
    )
    pre_curves_tone: bpy.props.EnumProperty(
        name = 'Tone',
        items = [
            ('STANDARD', 'RGB', 'Curve is applied to each channel individually, which may result in a change of hue'),
            ('FILMLIKE', 'Filmlike', 'Keeps the hue constant while removing control over individual channels'),
        ],
        default = 'FILMLIKE',
        update = lambda self, context: update_pre_curves(self, context)
    )
    # Post Transform
    whites: bpy.props.FloatProperty(
        name = 'Whites',
        description = 'Adjusts how bright a pixel needs to be in order to result in white, post-transform. Useful for fine tuning highlights to be very bright but not blown out',
        default = 0,
        min = -0.5,
        max = 0.5,
        update = lambda self, context: update_values(self, context)
    )
    highlights: bpy.props.FloatProperty(
        name = 'Highlights',
        description = 'Smoothly adjusts the values between 0.5 and 1.0, post-transform',
        default = 0,
        min = -0.5,
        max = 0.5,
        update = lambda self, context: update_values(self, context)
    )
    shadows: bpy.props.FloatProperty(
        name = 'Shadows',
        description = 'Smoothly adjusts the values between 0.0 and .5, post-transform',
        default = 0,
        min = -0.5,
        max = 0.5,
        update = lambda self, context: update_values(self, context)
    )
    blacks: bpy.props.FloatProperty(
        name = 'Blacks',
        description = 'Adjusts how dark a pixel needs to be in order to result in black, post-transform. Useful for crushing or lifting shadows or increasing contrast in dark areas',
        default = 0,
        min = -0.5,
        max = 0.5,
        update = lambda self, context: update_values(self, context)
    )
    post_curves_factor: bpy.props.FloatProperty(
        name = 'Curves Factor',
        description = 'Adjusts how much the RGB curves get applied',
        default = 1,
        min = 0,
        max = 1,
        update = lambda self, context: update_post_curves(self, context)
    )
    post_curves_black: bpy.props.FloatVectorProperty(
        name = 'Black Level',
        description = "Color considered as black by the post-transform curve",
        subtype = 'COLOR_GAMMA',
        default = [0, 0, 0],
        min = 0,
        max = 1,
        update = lambda self, context: update_post_curves(self, context)
    )
    post_curves_white: bpy.props.FloatVectorProperty(
        name = 'White Level',
        description = "Color considered as white by the post-transform curve",
        subtype = 'COLOR_GAMMA',
        default = [1, 1, 1],
        min = 0,
        max = 1,
        update = lambda self, context: update_post_curves(self, context)
    )
    post_curves_tone: bpy.props.EnumProperty(
        name = 'Curve Tone',
        items = [
            ('STANDARD', 'RGB', 'Curve is applied to each channel individually, which may result in a change of hue'),
            ('FILMLIKE', 'Filmlike', 'Keeps the hue constant while removing control over individual channels'),
        ],
        default = 'STANDARD',
        update = lambda self, context: update_post_curves(self, context)
    )
    fix_clipping: bpy.props.FloatProperty(
        name = 'Fix Clipping',
        description = ('Softly clamps the post-transform value to not be above 1'),
        default = 0,
        min = 0,
        max = 2,
        update = lambda self, context: update_fix_clipping(self, context)
    )
    #endregion

    """ Colors """
    #region
    use_colors: bpy.props.BoolProperty(
        default = True,
        update = lambda self, context: update_color_panel(self, context)
    )
    temperature: bpy.props.FloatProperty(
        name = 'Temperature',
        description = 'Adjusts the prominence of the red and blue channels for a warmer or cooler look, pre-transform',
        default = 0.5,
        min = 0,
        max = 1,
        update = lambda self, context: update_white_balance(self, context)
    )
    tint: bpy.props.FloatProperty(
        name = 'Tint',
        description = 'Adjusts the prominence of the green channel for a green or purple look, pre-transform',
        default = 0.5,
        min = 0,
        max = 1,
        update = lambda self, context: update_white_balance(self, context)
    )
    white_balance_perceptual: bpy.props.FloatProperty(
        name = 'Perceptual',
        description = "Choose between simply multiplying the RGB values or Blender's chromatic adaption for the white balance. The latter is generally nicer for most cases, but becomes less stable at low temperatures",
        default = 1,
        min = 0,
        max = 1,
        update = lambda self, context: update_white_balance(self, context)
    )
    saturation: bpy.props.FloatProperty(
        name = 'Saturation',
        description = 'Adjusts saturation uniformly, post-transform',
        default = 1,
        min = 0,
        max = 2,
        update = lambda self, context: update_saturation(self, context)
    )
    saturation_perceptual: bpy.props.FloatProperty(
        name = 'Perceptual',
        description = 'Keeps the perceived value the same during saturation adjustments rather than the RGB value, which is more intuitive but can cause colors to clip',
        default = 0.5,
        min = 0,
        max = 1,
        update = lambda self, context: update_saturation(self, context)
    )
    color_boost: bpy.props.FloatProperty(
        name = 'Color Boost',
        description = 'Adjusts the saturation of lower saturated areas without changing highly saturated areas, pre-transform',
        default = 0,
        min = -1,
        max = 1,
        update = lambda self, context: update_color_boost(self, context)
    )
    preserve_hue: bpy.props.FloatProperty(
        name = 'Preserve Hue',
        description = 'Returns the colors to their original sRGB hue after the transform to counter any hue shifting. Use with caution as it can break the smooth blending between colors',
        default = 0,
        min = 0,
        max = 1,
        update = lambda self, context: update_preserve_color(self, context)
    )
    preserve_saturation: bpy.props.FloatProperty(
        name = 'Preserve Saturation',
        description = 'Returns the colors to their original sRGB saturation after the transform to reduce the effect of desaturated highlights. Use with caution as it can break the smooth blending between colors',
        default = 0,
        min = 0,
        max = 1,
        update = lambda self, context: update_preserve_color(self, context)
    )
    preserve_filmic: bpy.props.FloatProperty(
        name = 'Preserve Filmic',
        description = 'Mixes in some Filmic colors for when you need smooth blending between saturated primaries',
        default = 0,
        min = 0,
        max = 1,
        update = lambda self, context: update_preserve_color(self, context)
    )
    preserve_cutoff: bpy.props.FloatProperty(
        name = 'Value Cutoff',
        description = 'The maximum value to allow to mix with the original sRGB to help prevent artifacts',
        default = 4,
        min = 0,
        max = 50,
        update = lambda self, context: update_preserve_color(self, context)
    )
    preserve_spread: bpy.props.FloatProperty(
        name = 'Cutoff Spread',
        description = (
            'How big of a range the highlights roll off over. '
            'Increase this for smoother transitions but less pure influence over the whole image'
        ),
        default = 0,
        min = 0,
        max = 1,
        update = lambda self, context: update_preserve_color(self, context)
    )
    hue_perceptual: bpy.props.FloatProperty(
        name = 'Perceptual',
        description = (
            'Shift the Hue and Saturation using the LAB color model rather than HSV. '
            'LAB attempts to preserve perceptual brightness and better blends between hues, '
            'but can cause clipping when increasing saturation in bright areas'
        ),
        default = 1,
        min = 0,
        max = 1,
        update = lambda self, context: update_hue(self, context)
    )
    hue_range: bpy.props.FloatProperty(
        name = 'Range',
        description = 'Determines how much of the spectrum each color adjustment will affect',
        default = 0.2,
        min = 0,
        max = 1,
        update = lambda self, context: update_hue(self, context)
    )
    hue_smoothing: bpy.props.FloatProperty(
        name = 'Smoothing',
        description = 'Smooth the falloff between each hue',
        default = 0,
        min = 0,
        max = 1,
        update = lambda self, context: update_hue(self, context)
    )
    hue_saturation_mask: bpy.props.FloatProperty(
        name = 'Saturation Mask',
        description = (
            'A positive value makes the per-hue adjustments affect only saturated areas '
            'while a negative value makes them affect only less saturated areas'
        ),
        default = 0,
        min = -1,
        max = 1,
        update = lambda self, context: update_hue(self, context)
    )
    hue_value_mask: bpy.props.FloatProperty(
        name = 'Value Mask',
        description = (
            'A positive value makes the per-hue adjustments affect only bright areas '
            'while a negative value makes them affect only dark areas'
        ),
        default = 0,
        min = -1,
        max = 1,
        update = lambda self, context: update_hue(self, context)
    )
    red_hue: bpy.props.FloatProperty(
        name = 'Red',
        default = 0.5,
        min = 0,
        max = 1,
        update = lambda self, context: update_hue(self, context)
    )
    red_saturation: bpy.props.FloatProperty(
        name = 'Red',
        default = 1,
        min = 0,
        max = 2,
        update = lambda self, context: update_hue(self, context)
    )
    red_value: bpy.props.FloatProperty(
        name = 'Red',
        default = 1,
        min = 0,
        max = 2,
        update = lambda self, context: update_hue(self, context)
    )
    orange_hue: bpy.props.FloatProperty(
        name = 'Orange',
        default = 0.5,
        min = 0,
        max = 1,
        update = lambda self, context: update_hue(self, context)
    )
    orange_saturation: bpy.props.FloatProperty(
        name = 'Orange',
        default = 1,
        min = 0,
        max = 2,
        update = lambda self, context: update_hue(self, context)
    )
    orange_value: bpy.props.FloatProperty(
        name = 'Orange',
        default = 1,
        min = 0,
        max = 2,
        update = lambda self, context: update_hue(self, context)
    )
    yellow_hue: bpy.props.FloatProperty(
        name = 'Yellow',
        default = 0.5,
        min = 0,
        max = 1,
        update = lambda self, context: update_hue(self, context)
    )
    yellow_saturation: bpy.props.FloatProperty(
        name = 'Yellow',
        default = 1,
        min = 0,
        max = 2,
        update = lambda self, context: update_hue(self, context)
    )
    yellow_value: bpy.props.FloatProperty(
        name = 'Yellow',
        default = 1,
        min = 0,
        max = 2,
        update = lambda self, context: update_hue(self, context)
    )
    green_hue: bpy.props.FloatProperty(
        name = 'Green',
        default = 0.5,
        min = 0,
        max = 1,
        update = lambda self, context: update_hue(self, context)
    )
    green_saturation: bpy.props.FloatProperty(
        name = 'Green',
        default = 1,
        min = 0,
        max = 2,
        update = lambda self, context: update_hue(self, context)
    )
    green_value: bpy.props.FloatProperty(
        name = 'Green',
        default = 1,
        min = 0,
        max = 2,
        update = lambda self, context: update_hue(self, context)
    )
    teal_hue: bpy.props.FloatProperty(
        name = 'Teal',
        default = 0.5,
        min = 0,
        max = 1,
        update = lambda self, context: update_hue(self, context)
    )
    teal_saturation: bpy.props.FloatProperty(
        name = 'Teal',
        default = 1,
        min = 0,
        max = 2,
        update = lambda self, context: update_hue(self, context)
    )
    teal_value: bpy.props.FloatProperty(
        name = 'Teal',
        default = 1,
        min = 0,
        max = 2,
        update = lambda self, context: update_hue(self, context)
    )
    blue_hue: bpy.props.FloatProperty(
        name = 'Blue',
        default = 0.5,
        min = 0,
        max = 1,
        update = lambda self, context: update_hue(self, context)
    )
    blue_saturation: bpy.props.FloatProperty(
        name = 'Blue',
        default = 1,
        min = 0,
        max = 2,
        update = lambda self, context: update_hue(self, context)
    )
    blue_value: bpy.props.FloatProperty(
        name = 'Blue',
        default = 1,
        min = 0,
        max = 2,
        update = lambda self, context: update_hue(self, context)
    )
    pink_hue: bpy.props.FloatProperty(
        name = 'Pink',
        default = 0.5,
        min = 0,
        max = 1,
        update = lambda self, context: update_hue(self, context)
    )
    pink_saturation: bpy.props.FloatProperty(
        name = 'Pink',
        default = 1,
        min = 0,
        max = 2,
        update = lambda self, context: update_hue(self, context)
    )
    pink_value: bpy.props.FloatProperty(
        name = 'Pink',
        default = 1,
        min = 0,
        max = 2,
        update = lambda self, context: update_hue(self, context)
    )
    lift_color: bpy.props.FloatVectorProperty(
        name = 'Lift',
        description = "Adjusts the shadows, post-transform",
        subtype = 'COLOR_GAMMA',
        default = [1, 1, 1],
        min = 0,
        max = 2,
        update = lambda self, context: update_color_balance(self, context)
    )
    gamma_color: bpy.props.FloatVectorProperty(
        name = 'Gamma',
        description = "Adjusts the midtones, post-transform",
        subtype = 'COLOR_GAMMA',
        default = [1, 1, 1],
        min = 0,
        max = 2,
        update = lambda self, context: update_color_balance(self, context)
    )
    gain_color: bpy.props.FloatVectorProperty(
        name = 'Gain',
        description = "Adjusts the highlights, post-transform",
        subtype = 'COLOR_GAMMA',
        default = [1, 1, 1],
        min = 0,
        max = 2,
        update = lambda self, context: update_color_balance(self, context)
    )
    offset_color: bpy.props.FloatVectorProperty(
        name = 'Offset',
        description = "An addative adjustment, pre-transform",
        subtype = 'COLOR_GAMMA',
        default = [0, 0, 0],
        min = 0,
        max = 1,
        update = lambda self, context: update_color_balance(self, context)
    )
    power_color: bpy.props.FloatVectorProperty(
        name = 'Power',
        description = "A pre-transform contrast adjustment defined by a power curve",
        subtype = 'COLOR_GAMMA',
        default = [1, 1, 1],
        min = 0,
        max = 2,
        update = lambda self, context: update_color_balance(self, context)
    )
    slope_color: bpy.props.FloatVectorProperty(
        name = 'Slope',
        description = "Adjusts the image without affecting the black level, pre-transform. It can be thought of as a contrast control that pivots at 0",
        subtype = 'COLOR_GAMMA',
        default = [1, 1, 1],
        min = 0,
        max = 2,
        update = lambda self, context: update_color_balance(self, context)
    )
    shadow_range: bpy.props.FloatProperty(
        name = 'Range',
        description = "Scales the range of values that are considered to be in the shadow range",
        default = 0.5,
        min = 0,
        max = 1,
        update = lambda self, context: update_color_blending(self, context)
    )
    highlight_range: bpy.props.FloatProperty(
        name = 'Range',
        description = "Scales the range of values that are considered to be in the highlight range",
        default = 0.5,
        min = 0,
        max = 1,
        update = lambda self, context: update_color_blending(self, context)
    )
    midtone_range: bpy.props.FloatProperty(
        name = 'Range',
        description = "Scales the range of values that are considered to be in the midtone range",
        default = 0.5,
        min = 0,
        max = 1,
        update = lambda self, context: update_color_blending(self, context)
    )
    shadow_factor: bpy.props.FloatProperty(
        name = 'Factor',
        description = "How much the shadow adjustment gets mixed in with the origional image",
        default = 1,
        min = 0,
        max = 1,
        update = lambda self, context: update_color_blending(self, context)
    )
    highlight_factor: bpy.props.FloatProperty(
        name = 'Factor',
        description = "How much the highlight adjustment gets mixed in with the origional image",
        default = 1,
        min = 0,
        max = 1,
        update = lambda self, context: update_color_blending(self, context)
    )
    midtone_factor: bpy.props.FloatProperty(
        name = 'Factor',
        description = "How much the midtone adjustment gets mixed in with the origional image",
        default = 1,
        min = 0,
        max = 1,
        update = lambda self, context: update_color_blending(self, context)
    )
    highlight_color: bpy.props.FloatVectorProperty(
        name = 'Color',
        subtype = 'COLOR',
        size = 3,
        max = 1,
        min = 0.1,
        precision = 3,
        default = [0.5, 0.5, 0.5],
        update = lambda self, context: update_color_blending(self, context)
    )
    midtone_color: bpy.props.FloatVectorProperty(
        name = 'Color',
        subtype = 'COLOR',
        size = 3,
        max = 1,
        min = 0.1,
        precision = 3,
        default = [0.5, 0.5, 0.5],
        update = lambda self, context: update_color_blending(self, context)
    )
    shadow_color: bpy.props.FloatVectorProperty(
        name = 'Color',
        subtype = 'COLOR',
        size = 3,
        max = 1,
        min = 0.1,
        precision = 3,
        default = [0.5, 0.5, 0.5],
        update = lambda self, context: update_color_blending(self, context)
    )
    shadow_saturation: bpy.props.FloatProperty(
        name = 'Shadows',
        description = "Adjusts the saturation in only the shadow areas, post-transform",
        default = 1,
        min = 0,
        max = 2,
        update = lambda self, context: update_value_saturation(self, context)
    )
    midtone_saturation: bpy.props.FloatProperty(
        name = 'Midtones',
        description = "Adjusts the saturation in only the midtone areas, post-transform",
        default = 1,
        min = 0,
        max = 2,
        update = lambda self, context: update_value_saturation(self, context)
    )
    highlight_saturation: bpy.props.FloatProperty(
        name = 'Highlights',
        description = "Adjusts the saturation in only the highlight areas, post-transform",
        default = 1,
        min = 0,
        max = 2,
        update = lambda self, context: update_value_saturation(self, context)
    )
    shadow_saturation_range: bpy.props.FloatProperty(
        name = 'Range',
        description = "Scales the range of values that are considered to be in the shadow range",
        default = 0.5,
        min = 0,
        max = 1,
        update = lambda self, context: update_value_saturation(self, context)
    )
    midtone_saturation_range: bpy.props.FloatProperty(
        name = 'Range',
        description = "Scales the range of values that are considered to be in the midtone range",
        default = 0.5,
        min = 0,
        max = 1,
        update = lambda self, context: update_value_saturation(self, context)
    )
    highlight_saturation_range: bpy.props.FloatProperty(
        name = 'Range',
        description = "Scales the range of values that are considered to be in the highlight range",
        default = 0.5,
        min = 0,
        max = 1,
        update = lambda self, context: update_value_saturation(self, context)
    )
    value_saturation_perceptual:bpy.props.FloatProperty(
        name = 'Perceptual',
        description = "Adjusts saturation while keeping the perceived brightness the same",
        default = 1,
        min = 0,
        max = 1,
        update = lambda self, context: update_value_saturation(self, context)
    )
    dummy_blending: bpy.props.EnumProperty(
        name = 'Blending',
        items = [
            ('Soft Light', 'Soft Light', ''),
            ('Color', 'Color', '')
        ],
        default='Soft Light'
    )
    dummy_color: bpy.props.FloatVectorProperty(
        name = 'Color',
        subtype = 'COLOR',
        default=[0.5, 0.5, 0.5]
    )
    #endregion

    """ Details """
    #region
    use_details: bpy.props.BoolProperty(
        default = False,
        update = lambda self, context: update_details_panel(self, context)
    )
    sharpness: bpy.props.FloatProperty(
        name = 'Sharpness',
        description = "Adds high frequency contrast around edges, post-transform",
        default = 0,
        min = 0,
        max = 1,
        update = lambda self, context: update_sharpness(self, context)
    )
    sharpness_mask: bpy.props.FloatProperty(
        name = 'Masking',
        description = "Adjusts how different neighboring pixels need to be in order to be considered an edge",
        default = 0,
        min = 0,
        max = 1,
        update = lambda self, context: update_sharpness(self, context)
    )
    texture: bpy.props.FloatProperty(
        name = 'Texture',
        description = "Adjusts the contrast in only the midtone areas, post-transform",
        default = 0,
        min = -1,
        max = 1,
        update = lambda self, context: update_texture(self, context)
    )
    texture_color: bpy.props.FloatProperty(
        name = 'Keep Color',
        default = 1,
        min = 0,
        max = 1,
        update = lambda self, context: update_texture(self, context)
    )
    clarity: bpy.props.FloatProperty(
        name = 'Clarity',
        description = "Adds or removes lower frequency contrast around edges, post-transform",
        default = 0,
        min = -1,
        max = 1,
        update = lambda self, context: update_clarity(self, context)
    )
    clarity_size: bpy.props.FloatProperty(
        name = 'Size',
        description = "Adjusts how much of the area around edges are affected by the clarity control",
        default = 0.5,
        min = 0,
        max = 1,
        update = lambda self, context: update_clarity(self, context)
    )
    #endregion

    """ Effects """
    #region
    use_effects: bpy.props.BoolProperty(
        default = True,
        update = lambda self, context: update_effects_panel(self, context)
    )
    vignette_factor: bpy.props.FloatProperty(
        name = 'Vignette Factor',
        description = "Brightens or darkens the edges of the image, post-transform",
        default = 0,
        min = 0,
        max = 1,
        update = lambda self, context: update_vignette(self, context)
    )
    vignette_feathering: bpy.props.FloatProperty(
        name = 'Feathering',
        description = "Adjusts the softness of the vignette",
        default = 0.5,
        min = 0,
        max = 1,
        update = lambda self, context: update_vignette(self, context)
    )
    vignette_scale_x: bpy.props.FloatProperty(
        name = 'Scale X',
        description = "Adjusts the width of the vignette",
        default = 1,
        min = 0,
        max = 2,
        update = lambda self, context: update_vignette(self, context)
    )
    vignette_scale_y: bpy.props.FloatProperty(
        name = 'Scale Y',
        description = "Adjusts the height of the vignette",
        default = 1,
        min = 0,
        max = 2,
        update = lambda self, context: update_vignette(self, context)
    )
    vignette_shift_x: bpy.props.FloatProperty(
        name = 'Shift X',
        description = "Adjusts the horizontal location of the vignette",
        default = 0,
        min = -0.5,
        max = 0.5,
        update = lambda self, context: update_vignette(self, context)
    )
    vignette_shift_y: bpy.props.FloatProperty(
        name = 'Shift Y',
        description = "Adjusts the vertical location of the vignette",
        default = 0,
        min = -0.5,
        max = 0.5,
        update = lambda self, context: update_vignette(self, context)
    )
    vignette_rotation: bpy.props.FloatProperty(
        name = 'Rotation',
        description = "Rotates the vignette",
        subtype = 'ANGLE',
        default = 0,
        min = -3.14159,
        max = 3.14159,
        update = lambda self, context: update_vignette(self, context)
    )
    vignette_roundness: bpy.props.FloatProperty(
        name = 'Roundness',
        description = "Adjusts how round the corners of the vignette are",
        default = 1,
        min = 0,
        max = 1,
        update = lambda self, context: update_vignette(self, context)
    )
    vignette_linear_blend: bpy.props.FloatProperty(
        name = 'Linear Blending',
        description = (
            "Adjusts how much the vignette preserves origional colors. "
            "0 is fully post-transform and 1 is fully pre-transform"
        ),
        default = 0,
        min = 0,
        max = 1,
        update = lambda self, context: update_vignette(self, context)
    )
    vignette_highlights: bpy.props.FloatProperty(
        name = 'Highlights',
        description = ("Adjusts how much the vignette preserves highlights"),
        default = 0,
        min = 0,
        max = 1,
        update = lambda self, context: update_vignette(self, context)
    )
    vignette_color: bpy.props.FloatVectorProperty(
        name = 'Color',
        description = "The color of the vignette",
        subtype = 'COLOR',
        size = 4,
        max = 1,
        min = 0,
        default = [0, 0, 0, 1],
        update = lambda self, context: update_vignette(self, context)
    )
    vignette_value: bpy.props.FloatProperty(
        # Legacy prop! Only registered to make conversions from old presets
        name = 'Vignette Value',
        description = "Brightens or darkens the edges of the image, post-transform",
        default = 0,
        min = -1,
        max = 1,
    )
    vignette_tint: bpy.props.FloatVectorProperty(
        # Legacy prop! Only registered to make conversions from old presets
        name = 'Tint',
        description = "Linear light color adjustment over the resulting vignette. The default of 0.5 grey produces no change.",
        subtype = 'COLOR',
        size = 4,
        max = 1,
        min = 0,
        default = [0.5, 0.5, 0.5, 1]
    )
    glare: bpy.props.FloatProperty(
        name = 'Glare',
        description = "Adjusts how much total glare is applied, pre-transform",
        default = 0,
        min = 0,
        max = 1,
        update = lambda self, context: update_glare(self, context)
    )
    glare_threshold: bpy.props.FloatProperty(
        name = 'Threshold',
        description = "Adjusts how bright a pixel needs to be in order to cause glare",
        default = 1,
        min = 0,
        max = 100,
        update = lambda self, context: update_glare(self, context)
    )
    glare_quality: bpy.props.IntProperty(
        name = 'Quality',
        description = 'Determines how many layers of blur are used in the bloom',
        default = 5,
        min = 1,
        max = 5,
        update = lambda self, context: update_glare(self, context)
    )
    bloom: bpy.props.FloatProperty(
        name = 'Bloom Strength',
        description = "Adjusts how much glow is applied around bright areas",
        default = 1,
        min = 0,
        max = 1,
        update = lambda self, context: update_bloom(self, context)
    )
    bloom_size: bpy.props.IntProperty(
        name = 'Bloom Size',
        description = "Adjusts the size of the glow around bright areas",
        default = 9,
        min = 1,
        max = 9,
        update = lambda self, context: update_bloom(self, context)
    )
    bloom_size_float: bpy.props.FloatProperty(
        # For Blender 4.4+
        name = 'Bloom Size',
        description = "Adjusts the size of the glow around bright areas",
        default = 1,
        min = 0,
        max = 1,
        update = lambda self, context: update_bloom(self, context)
    )
    bloom_saturation: bpy.props.FloatProperty(
        name = 'Bloom Initial Saturation',
        description = "Adjusts how much color the bloom picks up from the scene before the tint",
        default = 1,
        min = 0,
        max = 1,
        update = lambda self, context: update_bloom(self, context)
    )
    bloom_tint: bpy.props.FloatVectorProperty(
        name = 'Bloom Tint',
        description = "Color to multiply the bloom with. To fully use this color, set the Saturation above to 0",
        subtype = 'COLOR_GAMMA',
        default = [1, 1, 1],
        min = 0,
        max = 1,
        update = lambda self, context: update_bloom(self, context)
    )
    streaks: bpy.props.FloatProperty(
        name = 'Streaks Strength',
        description = "Adjusts how much the streaks are mixed in with the origional image",
        default = 0.5,
        min = 0,
        max = 1,
        update = lambda self, context: update_streaks(self, context)
    )
    streak_length: bpy.props.FloatProperty(
        name = 'Length',
        description = "Adjusts the size of the streaks",
        default = 0.25,
        min = 0,
        max = 1,
        update = lambda self, context: update_streaks(self, context)
    )
    streak_count: bpy.props.IntProperty(
        name = 'Count',
        description = "Adjusts how many streaks are created around bright areas",
        default = 13,
        min = 2,
        max = 16,
        update = lambda self, context: update_streaks(self, context)
    )
    streak_angle: bpy.props.FloatProperty(
        name = 'Angle',
        description = "Adjusts the rotation of the streaks",
        subtype = 'ANGLE',
        default = 0,
        min = 0,
        max = 180,
        update = lambda self, context: update_streaks(self, context)
    )
    ghosting: bpy.props.FloatProperty(
        name = 'Ghosting',
        description = "Adjusts how much camera artifacting is applied on top of the image",
        default = 0.05,
        min = 0,
        max = 1,
        update = lambda self, context: update_ghosting(self, context)
    )
    distortion: bpy.props.FloatProperty(
        name = 'Lens Distortion',
        description = "Simulates warping from the shape of a camera lens",
        default = 0,
        min = -1,
        max = 1,
        update = lambda self, context: update_distortion(self, context)
    )
    dispersion: bpy.props.FloatProperty(
        name = 'Dispersion',
        description = "Simulates color fringing from the imperfect refraction of a camera lens",
        default = 0,
        min = 0,
        max = 1,
        update = lambda self, context: update_distortion(self, context)
    )
    grain: bpy.props.FloatProperty(
        name = 'Film Grain',
        description = "Simulates the noise on film or a digital sensor, which has a very different look from render noise",
        default = 0,
        min = 0,
        max = 1,
        update = lambda self, context: update_grain(self, context)
    )
    grain_method: bpy.props.EnumProperty(
        name = 'Method',
        items = [
            ('FAST', 'Fast', 'Adds a grain texture as a simple overlay'),
            ('ACCURATE', 'Accurate', 'Simulates grain realistically by displacing the image differently per color channel'),
        ],
        default = 'FAST',
        update = lambda self, context: update_grain(self, context)
    )
    grain_scale: bpy.props.FloatProperty(
        name = 'Scale',
        description = "Adjusts the size of the noise pattern",
        default = 5,
        min = 1,
        max = 20,
        update = lambda self, context: update_grain(self, context)
    )
    grain_aspect: bpy.props.FloatProperty(
        name = 'Aspect',
        description = "Adjusts the hight and width of the noise pattern so that the noise doesn't appear stretched when the image is not square",
        default = 0.5,
        min = 0,
        max = 1,
        update = lambda self, context: update_grain(self, context)
    )
    grain_steps: bpy.props.IntProperty(
        name = 'Steps',
        description = "Adjusts the complexity of the noise pattern. Increasing the steps results in more realistic noise but also increases processing time",
        default = 2,
        min = 1,
        max = 5,
        update = lambda self, context: update_grain(self, context)
    )
    grain_saturation: bpy.props.FloatProperty(
        name = 'Color',
        description = "Adjusts how much the noise colors the image",
        default = 1,
        min = 0,
        max = 1,
        update = lambda self, context: update_grain(self, context)
    )
    grain_is_animated: bpy.props.BoolProperty(
        name = 'Animmate',
        description = 'Randomize the grain per frame. This is more realistic but fairly slow in the viewport',
        default = False,
        update = lambda self, context: update_grain(self, context)
    )
    #endregion

    """ Scene """
    # This property is only here so that RR can read whether or not files
    # saved with older versions of RR were enabled. Newer versions use the
    # property saved in scene.render_raw_scene instead
    enable_RR: bpy.props.BoolProperty(
        default=False
    )


def register():
    bpy.utils.register_class(RenderRawSettings)
    bpy.types.NodeTree.render_raw = bpy.props.PointerProperty(type=RenderRawSettings)
    bpy.types.Scene.render_raw = bpy.props.PointerProperty(type=RenderRawSettings)

def unregister():
    bpy.utils.unregister_class(RenderRawSettings)