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

RR_node_name = 'Render Raw'
RR_node_group_name = 'Render Raw'

# Presets ARE stored on the Pre group, but not listed
# here so as not to be applied when applying a preset.
Pre_settings = [
# Values
'use_values',
'exposure', 'gamma', 'contrast',
'pre_curves_factor', 'pre_curves_black', 'pre_curves_white', 'pre_curves_tone',
# Colors
'use_colors',
'temperature', 'tint', 'white_balance_perceptual', 'color_boost',
'offset_color', 'power_color', 'slope_color',
# Details
'use_details',
# Effects
'use_effects',
'glare', 'glare_threshold', 'glare_quality',
'bloom', 'bloom_size', 'ghosting',
'streaks', 'streak_length', 'streak_count', 'streak_angle',
# Alpha,
'opacity'
]

Post_settings = [
# Values
'whites', 'highlights', 'shadows', 'blacks',
'post_curves_factor', 'post_curves_black', 'post_curves_white', 'post_curves_tone',
# Colors
'saturation', 'saturation_perceptual', 
'preserve_hue', 'preserve_saturation', 'preserve_filmic', 'preserve_cutoff', 'preserve_spread',
'red_hue', 'red_saturation', 'red_value',
'orange_hue', 'orange_saturation', 'orange_value',
'yellow_hue', 'yellow_saturation', 'yellow_value',
'green_hue', 'green_saturation', 'green_value',
'teal_hue', 'teal_saturation', 'teal_value',
'blue_hue', 'blue_saturation', 'blue_value',
'pink_hue', 'pink_saturation', 'pink_value',
'lift_color', 'gamma_color', 'gain_color',
'shadow_range', 'highlight_range', 'midtone_range',
'shadow_factor', 'highlight_factor', 'midtone_factor',
'highlight_color', 'midtone_color', 'shadow_color',
'shadow_saturation', 'midtone_saturation', 'highlight_saturation',
'shadow_saturation_range', 'midtone_saturation_range', 'highlight_saturation_range',
'value_saturation_perceptual', 'dummy_blending', 'dummy_color',
# Details
'sharpness', 'sharpness_mask', 'texture', 'texture_color',
'clarity', 'clarity_size',
# Effects
'vignette_factor', 'vignette_feathering', 'vignette_linear_blend',
'vignette_roundness', 'vignette_highlights',
'vignette_scale_x', 'vignette_scale_y',
'vignette_shift_x', 'vignette_shift_y', 'vignette_rotation',
'distortion', 'dispersion',
'grain', 'grain_method', 'grain_scale', 'grain_aspect',
'grain_steps', 'grain_saturation', 'grain_is_animated',
# Alpha
'alpha_method', 'alpha_factor',
]

# These groups do not need to have a full copy made when creating a new layer
multiuser_subgroups = [
'.RR_contrast', '.RR_color_boost', '.RR_saturation',
'.YUV_adjustments', '.sRGB_to_LAB', '.LAB_adjustments', '.LAB_to_sRGB',
'.RR_sharpness', '.RR_difference_mask', '.RR_texture', '.RR_clarity',
'.RR_lens_distortion', '.RR_vignette',
'.RR_fast_grain_step', '.RR_grain_layer', '.RR_screeen_space_uvs', '.RR_displace_image',
'.RR_alpha_fix', '.RR_mask_values', '.RR_fix_clipping'
]