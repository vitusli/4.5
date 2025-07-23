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
from ..utilities.settings import get_settings
from ..utilities.layers import is_layer_used
from ..utilities.conversions import (
    get_rgb, map_range, set_alpha, expand_temperature, expand_tint, lerp
)


def update_preserve_color(self, context, RR_group=None, layer_index=None):
    RR = get_settings(context, RR_group, layer_index)
    FAC = RR.props_pre.layer_factor
    PROPS = RR.props_post
    PH =  RR.nodes_post['Preserve Color']
    is_default = PROPS.preserve_hue == 0 and PROPS.preserve_saturation == 0 and PROPS.preserve_filmic == 0
    if not is_layer_used(RR) or not RR.use_colors or is_default:
        PH.mute = True
    else:
        PH.mute = False
        PH.inputs['Filmic'].default_value = PROPS.preserve_filmic * FAC
        PH.inputs['Hue'].default_value = PROPS.preserve_hue * FAC
        PH.inputs['Saturation'].default_value = PROPS.preserve_saturation * FAC
        PH.inputs['Cutoff'].default_value = PROPS.preserve_cutoff
        PH.inputs['Spread'].default_value = PROPS.preserve_spread

def update_fix_clipping(self, context, RR_group=None, layer_index=None):
    RR = get_settings(context, RR_group, layer_index)
    FAC = RR.props_pre.layer_factor
    PROPS = RR.props_post
    FC =  RR.nodes_post['Fix Clipping']

    if not is_layer_used(RR) or not RR.use_colors or PROPS.fix_clipping == 0:
        FC.mute = True
    else:
        FC.mute = False
        FC.inputs['Factor'].default_value = PROPS.fix_clipping * FAC

def update_saturation(self, context, RR_group=None, layer_index=None):
    RR = get_settings(context, RR_group, layer_index)
    FAC = RR.props_pre.layer_factor
    SATURATION = RR.nodes_post['Saturation']
    PROPS = RR.props_post

    if not is_layer_used(RR) or not RR.use_colors or PROPS.saturation == 1:
        SATURATION.mute = True
    else:
        SATURATION.mute = False
        SATURATION.inputs['Saturation'].default_value = lerp(1, PROPS.saturation, FAC)
        SATURATION.inputs['Perceptual'].default_value = PROPS.saturation_perceptual


def update_color_boost(self, context, RR_group=None, layer_index=None):
    RR = get_settings(context, RR_group, layer_index)
    FAC = RR.props_pre.layer_factor
    PROPS = RR.props_pre
    BOOST = RR.nodes_pre['Color Boost']

    if not is_layer_used(RR) or not RR.use_colors or PROPS.color_boost == 0:
        BOOST.mute = True
    else:
        BOOST.mute = False
        BOOST.inputs['Strength'].default_value = PROPS.color_boost * FAC


def update_white_balance(self, context, RR_group=None, layer_index=None):
    RR = get_settings(context, RR_group, layer_index)
    FAC = RR.props_pre.layer_factor
    PROPS = RR.props_pre
    WB = RR.nodes_pre['White Balance']

    is_default = PROPS.temperature == 0.5 and PROPS.tint == 0.5

    if not is_layer_used(RR) or not RR.use_colors or is_default:
        WB.mute = True
    else:
        WB.mute = False
        WB_NODES = WB.node_tree.nodes
        if bpy.app.version >= (4, 5, 0):
            WB.inputs['Temperature'].default_value = PROPS.temperature
            WB.inputs['Tint'].default_value = PROPS.tint
            WB.inputs['Perceptual'].default_value = PROPS.white_balance_perceptual
            INNER_WB = WB_NODES['White Balance']
            INNER_WB.input_temperature = expand_temperature(PROPS.temperature)
            INNER_WB.output_temperature = expand_temperature(map_range(PROPS.temperature, 0, 1, 1, 0))
            INNER_WB.input_tint = expand_tint(PROPS.tint)
            INNER_WB.output_tint = expand_tint(map_range(PROPS.tint, 0, 1, 1, 0))
            INNER_WB.inputs['Fac'].default_value = FAC
        elif bpy.app.version >= (4, 3, 0):
            WB.inputs['Temperature'].default_value = PROPS.temperature
            WB.inputs['Tint'].default_value = PROPS.tint
            WB_NODES['Perceptual'].inputs['Fac'].default_value = PROPS.white_balance_perceptual
            INNER_WB = WB_NODES['White Balance']
            INNER_WB.correction_method = 'WHITEPOINT'
            INNER_WB.input_temperature = expand_temperature(PROPS.temperature)
            INNER_WB.output_temperature = expand_temperature(map_range(PROPS.temperature, 0, 1, 1, 0))
            INNER_WB.input_tint = expand_tint(PROPS.tint)
            INNER_WB.output_tint = expand_tint(map_range(PROPS.tint, 0, 1, 1, 0))
            INNER_WB.inputs['Fac'].default_value = FAC
        else:
            WB.inputs['Temperature'].default_value = lerp(0.5, PROPS.temperature, FAC)
            WB.inputs['Tint'].default_value = lerp(0.5, PROPS.tint, FAC)
            WB_NODES['Perceptual'].inputs['Fac'].default_value = 0


def update_hue(self, context, RR_group=None, layer_index=None):
    RR = get_settings(context, RR_group, layer_index)
    FAC = RR.props_pre.layer_factor
    PROPS = RR.props_post
    HUE_CORRECT = RR.nodes_post['Hue Correct']

    hue = {
        'red': PROPS.red_hue, 
        'orange': PROPS.orange_hue,
        'yellow': PROPS.yellow_hue,
        'green': PROPS.green_hue,
        'teal': PROPS.teal_hue,    
        'blue': PROPS.blue_hue,  
        'pink': PROPS.pink_hue,    
    }
    sat = {
        'red': PROPS.red_saturation,
        'orange': PROPS.orange_saturation,
        'yellow': PROPS.yellow_saturation,
        'green': PROPS.green_saturation,
        'teal': PROPS.teal_saturation,
        'blue': PROPS.blue_saturation,
        'pink': PROPS.pink_saturation,
    }
    val = {
        'red': PROPS.red_value,
        'orange': PROPS.orange_value,
        'yellow': PROPS.yellow_value,
        'green': PROPS.green_value,
        'teal': PROPS.teal_value,
        'blue': PROPS.blue_value,
        'pink': PROPS.pink_value,
    }
    
    if not is_layer_used(RR) or not RR.use_colors or (
        all([x == 0.5 for x in hue]) and 
        all([x == 1 for x in sat]) and
        all([x == 1 for x in val])
    ):
        HUE_CORRECT.mute = True

    else:
        HUE_CORRECT.mute = False

        if bpy.app.version >= (4, 5, 0):
            HUE_CORRECT.inputs['Red Hue'].default_value =     hue['red']
            HUE_CORRECT.inputs['Orange Hue'].default_value =  hue['orange']
            HUE_CORRECT.inputs['Yellow Hue'].default_value =  hue['yellow']
            HUE_CORRECT.inputs['Green Hue'].default_value =   hue['green']
            HUE_CORRECT.inputs['Teal Hue'].default_value =    hue['teal']
            HUE_CORRECT.inputs['Blue Hue'].default_value =    hue['blue']
            HUE_CORRECT.inputs['Pink Hue'].default_value =    hue['pink']

            HUE_CORRECT.inputs['Red Saturation'].default_value =     sat['red']
            HUE_CORRECT.inputs['Orange Saturation'].default_value =  sat['orange']
            HUE_CORRECT.inputs['Yellow Saturation'].default_value =  sat['yellow']
            HUE_CORRECT.inputs['Green Saturation'].default_value =   sat['green']
            HUE_CORRECT.inputs['Teal Saturation'].default_value =    sat['teal']
            HUE_CORRECT.inputs['Blue Saturation'].default_value =    sat['blue']
            HUE_CORRECT.inputs['Pink Saturation'].default_value =    sat['pink']

            HUE_CORRECT.inputs['Red Value'].default_value =     val['red']
            HUE_CORRECT.inputs['Orange Value'].default_value =  val['orange']
            HUE_CORRECT.inputs['Yellow Value'].default_value =  val['yellow']
            HUE_CORRECT.inputs['Green Value'].default_value =   val['green']
            HUE_CORRECT.inputs['Teal Value'].default_value =    val['teal']
            HUE_CORRECT.inputs['Blue Value'].default_value =    val['blue']
            HUE_CORRECT.inputs['Pink Value'].default_value =    val['pink']

            HUE_CORRECT.inputs['Perceptual'].default_value = PROPS.hue_perceptual
            HUE_CORRECT.inputs['Range'].default_value = PROPS.hue_range
            HUE_CORRECT.inputs['Saturation Mask'].default_value = PROPS.hue_saturation_mask
            HUE_CORRECT.inputs['Value Mask'].default_value = PROPS.hue_value_mask
            HUE_CORRECT.inputs['Smoothing'].default_value = PROPS.hue_smoothing

        else:
            HUE_NODES = HUE_CORRECT.node_tree.nodes

            for section in [hue, sat, val]:
                for key in section.keys():
                    section[key] = lerp(0.5, section[key], FAC)

            HUE = HUE_NODES['Hue Correct'].mapping.curves[0]
            HUE.points[0].location[1] = 0.5 - ((0.5 - hue['red']) / 2)
            HUE.points[7].location[1] = 0.5 - ((0.5 - hue['red']) / 2)
            HUE.points[1].location[1] = 0.5 - ((0.5 - hue['orange']) / 6)
            HUE.points[2].location[1] = 0.5 - ((0.5 - hue['yellow']) / 2)
            HUE.points[3].location[1] = 0.5 - ((0.5 - hue['green']) / 2)
            HUE.points[4].location[1] = 0.5 - ((0.5 - hue['teal']) / 2)
            HUE.points[5].location[1] = 0.5 - ((0.5 - hue['blue']) / 2)
            HUE.points[6].location[1] = 0.5 - ((0.5 - hue['pink']) / 2)

            SAT = HUE_NODES['Hue Correct'].mapping.curves[1]
            SAT.points[0].location[1] = sat['red'] / 2
            SAT.points[7].location[1] = sat['red'] / 2
            SAT.points[1].location[1] = sat['orange'] / 2
            SAT.points[2].location[1] = sat['yellow'] / 2
            SAT.points[3].location[1] = sat['green'] / 2
            SAT.points[4].location[1] = sat['teal'] / 2
            SAT.points[5].location[1] = sat['blue'] / 2
            SAT.points[6].location[1] = sat['pink'] / 2

            VALUE = HUE_NODES['Hue Correct'].mapping.curves[2]
            VALUE.points[0].location[1] = val['red'] / 2
            VALUE.points[7].location[1] = val['red'] / 2
            VALUE.points[1].location[1] = val['orange'] / 2
            VALUE.points[2].location[1] = val['yellow'] / 2
            VALUE.points[3].location[1] = val['green'] / 2
            VALUE.points[4].location[1] = val['teal'] / 2
            VALUE.points[5].location[1] = val['blue'] / 2
            VALUE.points[6].location[1] = val['pink'] / 2

            HUE_NODES['Hue Correct'].mapping.update()
            HUE_NODES['Hue Correct'].update()


def update_value_saturation(self, context, RR_group=None, layer_index=None):
    RR = get_settings(context, RR_group, layer_index)
    FAC = RR.props_pre.layer_factor
    PROPS = RR.props_post
    VS = RR.nodes_post['Value Saturation']

    if bpy.app.version >= (4, 5, 0):
        if not is_layer_used(RR) or not RR.use_colors or (
            PROPS.shadow_saturation == 1 and
            PROPS.midtone_saturation == 1 and
            PROPS.highlight_saturation == 1
        ):
            VS.mute = True
        else:
            VS.mute = False
            VS.inputs['Shadow Saturation'].default_value = PROPS.shadow_saturation
            VS.inputs['Midtone Saturation'].default_value = PROPS.midtone_saturation
            VS.inputs['Highlight Saturation'].default_value = PROPS.highlight_saturation
            VS.inputs['Shadow Range'].default_value = PROPS.shadow_saturation_range
            VS.inputs['Midtone Range'].default_value = PROPS.midtone_saturation_range
            VS.inputs['Highlight Range'].default_value = PROPS.highlight_saturation_range
            VS.inputs['Perceptual'].default_value = PROPS.value_saturation_perceptual

    else:
        VS_NODES = RR.nodes_post['Value Saturation'].node_tree.nodes
        SS = VS_NODES['Shadow Saturation']
        MS = VS_NODES['Midtone Saturation']
        HS = VS_NODES['Highlight Saturation']
        SS_RANGE = VS_NODES['Shadow Saturation Range']
        MS_RANGE = VS_NODES['Midtone Saturation Range']
        HS_RANGE = VS_NODES['Highlight Saturation Range']

        if not is_layer_used(RR) or not RR.use_colors:
            SS.mute = True
            MS.mute = True
            HS.mute = True
        else:
            shadow_saturation = lerp(1, PROPS.shadow_saturation, FAC)
            midtone_saturation = lerp(1, PROPS.midtone_saturation, FAC)
            highlight_saturation = lerp(1, PROPS.highlight_saturation, FAC)

            VS.mute = False
            SS.mute = shadow_saturation == 1
            MS.mute = midtone_saturation == 1
            HS.mute = highlight_saturation == 1

            SS.inputs['Saturation'].default_value = shadow_saturation
            MS.inputs['Saturation'].default_value = midtone_saturation
            HS.inputs['Saturation'].default_value = highlight_saturation

            SS.inputs['Perceptual'].default_value = PROPS.value_saturation_perceptual
            MS.inputs['Perceptual'].default_value = PROPS.value_saturation_perceptual
            HS.inputs['Perceptual'].default_value = PROPS.value_saturation_perceptual

            SS_RANGE.color_ramp.elements[1].position = 0.25 * (PROPS.shadow_saturation_range * 2)
            SS_RANGE.color_ramp.elements[2].position = 0.5 * (PROPS.shadow_saturation_range * 2)

            MS_RANGE.color_ramp.elements[0].position = 0.25 * (-PROPS.midtone_saturation_range * 2) + 0.5
            MS_RANGE.color_ramp.elements[2].position = 0.75 * (PROPS.midtone_saturation_range / 1.5) + 0.5

            HS_RANGE.color_ramp.elements[0].position = (0.5 * (-PROPS.highlight_saturation_range * 2)) + 1
            HS_RANGE.color_ramp.elements[1].position = (0.25 * (-PROPS.highlight_saturation_range * 2)) + 1


def update_color_balance(self, context, RR_group=None, layer_index=None):
    RR = get_settings(context, RR_group, layer_index)
    FAC = RR.props_pre.layer_factor
    OPS = RR.nodes_pre['Offset Power Slope']
    LGG = RR.nodes_post['Lift Gamma Gain']

    is_default = (
        get_rgb(RR.props_pre.offset_color) == [0, 0, 0] and
        get_rgb(RR.props_pre.power_color) == [1, 1, 1] and
        get_rgb(RR.props_pre.slope_color) == [1, 1, 1] and

        get_rgb(RR.props_post.lift_color) == [1, 1, 1] and
        get_rgb(RR.props_post.gamma_color) == [1, 1, 1] and
        get_rgb(RR.props_post.gain_color) == [1, 1, 1]
    )

    if not is_layer_used(RR) or not RR.use_colors or is_default:
        LGG.mute = True
        OPS.mute = True
    else:
        LGG.mute = False
        OPS.mute = False

        OPS.offset = RR.props_pre.offset_color
        OPS.power = RR.props_pre.power_color
        OPS.slope = RR.props_pre.slope_color
        OPS.inputs['Fac'].default_value = FAC

        LGG.lift = RR.props_post.lift_color
        LGG.gamma = RR.props_post.gamma_color
        LGG.gain = RR.props_post.gain_color
        LGG.inputs['Fac'].default_value = FAC


def update_color_blending(self, context, RR_group=None, layer_index=None):
    RR = get_settings(context, RR_group, layer_index)
    FAC = RR.props_pre.layer_factor
    PROPS = RR.props_post

    CB = RR.nodes_post['Color Blending']
    CB_NODES = CB.node_tree.nodes
    S_COL = CB_NODES['Shadow Color']
    M_COL = CB_NODES['Midtone Color']
    H_COL = CB_NODES['Highlight Color']

    if not is_layer_used(RR) or not RR.use_colors:
        CB.mute = True
    else:
        CB.mute = False

        if bpy.app.version >= (4, 5, 0):
            CB.inputs['Shadow Color'].default_value  = set_alpha(PROPS.shadow_color, 1)
            CB.inputs['Midtone Color'].default_value  = set_alpha(PROPS.midtone_color, 1)
            CB.inputs['Highlight Color'].default_value = set_alpha(PROPS.highlight_color, 1)

            CB.inputs['Shadow Range'].default_value = PROPS.shadow_range
            CB.inputs['Midtone Range'].default_value = PROPS.midtone_range
            CB.inputs['Highlight Range'].default_value = PROPS.highlight_range

            CB.inputs['Shadow Factor'].default_value = PROPS.shadow_factor * FAC
            CB.inputs['Midtone Factor'].default_value = PROPS.midtone_factor * FAC
            CB.inputs['Highlight Factor'].default_value = PROPS.highlight_factor * FAC  

        else:
            S_RANGE = CB_NODES['Shadow Range'].color_ramp.elements
            M_RANGE = CB_NODES['Midtone Range'].color_ramp.elements
            H_RANGE = CB_NODES['Highlight Range'].color_ramp.elements
            S_FAC = CB_NODES['Shadow Fac'].inputs[1]
            M_FAC = CB_NODES['Midtone Fac'].inputs[1]
            H_FAC = CB_NODES['Highlight Fac'].inputs[1]

            S_COL.inputs[2].default_value = set_alpha(PROPS.shadow_color, 1)
            M_COL.inputs[2].default_value = set_alpha(PROPS.midtone_color, 1)
            H_COL.inputs[2].default_value = set_alpha(PROPS.highlight_color, 1)

            S_RANGE[1].position = 0.25 * (PROPS.shadow_range * 2)
            S_RANGE[2].position = 0.5 * (PROPS.shadow_range * 2)

            M_RANGE[0].position = 0.25 * (-PROPS.midtone_range * 2) + 0.5
            M_RANGE[2].position = 0.75 * (PROPS.midtone_range / 1.5) + 0.5

            H_RANGE[0].position = (0.5 * (-PROPS.highlight_range * 2)) + 1
            H_RANGE[1].position = (0.25 * (-PROPS.highlight_range * 2)) + 1

            S_FAC.default_value = PROPS.shadow_factor * FAC
            M_FAC.default_value = PROPS.midtone_factor * FAC
            H_FAC.default_value = PROPS.highlight_factor * FAC


def update_color_panel(self, context, RR_group=None, layer_index=None):
    update_preserve_color(self, context, RR_group, layer_index)
    update_saturation(self, context, RR_group, layer_index)
    update_color_boost(self, context, RR_group, layer_index)
    update_white_balance(self, context, RR_group, layer_index)
    update_color_balance(self, context, RR_group, layer_index)
    update_color_blending(self, context, RR_group, layer_index)
    update_hue(self, context, RR_group, layer_index)
    update_value_saturation(self, context, RR_group, layer_index)
