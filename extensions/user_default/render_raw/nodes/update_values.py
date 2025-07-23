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
from ..utilities.conversions import lerp, map_range, set_alpha
from ..utilities.layers import is_layer_used
from ..utilities.nodes import get_RR_groups
from .update_details import update_details_panel


def update_exposure(self, context, RR_group=None, layer_index=None):
    RR = get_settings(context, RR_group, layer_index)
    EXPOSURE = RR.nodes_pre['Exposure']
    FAC = RR.props_pre.layer_factor

    if (
        not RR.props_pre.use_values or
        RR.props_pre.exposure == 0 or
        not is_layer_used(RR)
    ):
        EXPOSURE.mute = True
    else:
        EXPOSURE.mute = False
        EXPOSURE.inputs['Exposure'].default_value = RR.props_pre.exposure * FAC


def update_group_exposure(RR_group):
    RR = get_settings(bpy.context)
    EXPOSURE = RR_group.nodes['Exposure']

    if RR.props_scene.exposure == 0:
        EXPOSURE.mute = True
    else:
        EXPOSURE.mute = False
        EXPOSURE.inputs['Exposure'].default_value = RR.props_scene.exposure


def update_scene_exposure(self, context):
    for RR_group in get_RR_groups(context):
        update_group_exposure(RR_group)


def update_gamma(self, context, RR_group=None, layer_index=None):
    RR = get_settings(context, RR_group, layer_index)
    FAC = RR.props_pre.layer_factor
    GAMMA = RR.nodes_pre['Gamma']

    if (
        not RR.use_values or
        RR.props_pre.gamma == 1 or
        not is_layer_used(RR)
    ):
        GAMMA.mute = True
    else:
        GAMMA.mute = False
        GAMMA.inputs['Gamma'].default_value = lerp(1, RR.props_pre.gamma, FAC)


def update_group_gamma(RR_group):
    RR = get_settings(bpy.context)
    GAMMA = RR_group.nodes['Gamma']

    if RR.props_scene.exposure == 1:
        GAMMA.mute = True
    else:
        GAMMA.mute = False
        GAMMA.inputs['Gamma'].default_value = RR.props_scene.gamma


def update_scene_gamma(self, context):
    for RR_group in get_RR_groups(context):
        update_group_gamma(RR_group)


def update_contrast(self, context, RR_group=None, layer_index=None):
    RR = get_settings(context, RR_group, layer_index)
    FAC = RR.props_pre.layer_factor
    CONTRAST = RR.nodes_pre['Contrast']

    if (
        not RR.use_values or
        RR.props_pre.contrast == 0 or
        not is_layer_used(RR)
    ):
        CONTRAST.mute = True
    else:
        CONTRAST.mute = False
        CONTRAST.inputs['Contrast'].default_value = RR.props_pre.contrast * FAC


def update_values(self, context, RR_group=None, layer_index=None):
    RR = get_settings(context, RR_group, layer_index)
    FAC = RR.props_pre.layer_factor
    PROPS = RR.props_post
    VALUES = RR.nodes_post['Values']

    if (
        not RR.use_values or
        not is_layer_used(RR) or
        (PROPS.blacks == 0 and PROPS.whites == 0 and PROPS.shadows == 0 and PROPS.highlights == 0)
    ):
        VALUES.mute = True
        
    else:
        VALUES.mute = False

        if bpy.app.version >= (4, 5, 0):
            VALUES.inputs['Blacks'].default_value = PROPS.blacks
            VALUES.inputs['Shadows'].default_value = PROPS.shadows
            VALUES.inputs['Highlights'].default_value = PROPS.highlights
            VALUES.inputs['Whites'].default_value = PROPS.whites

        else:
            white_level = -PROPS.whites + 1
            VALUES_NODES = VALUES.node_tree.nodes
            VALUES_NODES['Values Black Level'].outputs[0].default_value = -PROPS.blacks
            VALUES_NODES['Values'].inputs['White Level'].default_value = [white_level, white_level, white_level, 1]
            CURVE = VALUES_NODES['Values'].mapping.curves[3]
            CURVE.points[1].location[1] = 0.25 + (PROPS.shadows / 2)
            CURVE.points[2].location[1] = 0.75 + (PROPS.highlights / 2)
            VALUES_NODES['Values'].mapping.update()
            VALUES_NODES['Values'].update()
            VALUES_NODES['Values'].inputs['Fac'].default_value = FAC


def update_pre_curves(self, context, RR_group=None, layer_index=None):
    RR = get_settings(context, RR_group, layer_index)
    FAC = RR.props_pre.layer_factor
    CURVES = RR.nodes_pre['Curves']
    CURVES.mute = not RR.use_values or not is_layer_used(RR)
    CURVES.inputs['Fac'].default_value = RR.props_pre.pre_curves_factor * FAC
    CURVES.mapping.tone = RR.props_pre.pre_curves_tone
    CURVES.inputs['Black Level'].default_value = set_alpha(RR.props_pre.pre_curves_black, 1)
    CURVES.inputs['White Level'].default_value = set_alpha(RR.props_pre.pre_curves_white, 1)


def update_post_curves(self, context, RR_group=None, layer_index=None):
    RR = get_settings(context, RR_group, layer_index)
    FAC = RR.props_pre.layer_factor
    CURVES = RR.nodes_post['Curves']
    CURVES.mute = not RR.use_values or not is_layer_used(RR)
    CURVES.inputs['Fac'].default_value = RR.props_post.post_curves_factor * FAC
    CURVES.mapping.tone = RR.props_post.post_curves_tone
    CURVES.inputs['Black Level'].default_value = set_alpha(RR.props_post.post_curves_black, 1)
    CURVES.inputs['White Level'].default_value = set_alpha(RR.props_post.post_curves_white, 1)


def update_clipping(self, context, RR_group=None):
    if RR_group != None:
        groups = [RR_group]
    else:
        groups = get_RR_groups(context)

    for RR_group in groups:
        PROPS = RR_group.render_raw
        CLIP = RR_group.nodes['Clipping']
        CLIP.mute = not PROPS.use_clipping
        CLIP.inputs['Black Overlay'].default_value = PROPS.clipping_blacks
        CLIP.inputs['White Overlay'].default_value = PROPS.clipping_whites
        CLIP.inputs['Saturation Overlay'].default_value = PROPS.clipping_saturation
        CLIP.inputs['Black Threshold'].default_value = PROPS.clipping_black_threshold
        CLIP.inputs['White Threshold'].default_value = PROPS.clipping_white_threshold
        CLIP.inputs['Saturation Threshold'].default_value = PROPS.clipping_saturation_threshold
        CLIP.inputs['Saturation Multiply'].default_value = map_range(PROPS.clipping_saturation_multiply, 0, 1, .0001, .9999)


def update_value_panel(self, context, RR_group=None, layer_index=None):
    update_pre_curves(self, context, RR_group, layer_index)
    update_post_curves(self, context, RR_group, layer_index)
    update_exposure(self, context, RR_group, layer_index)
    update_gamma(self, context, RR_group, layer_index)
    update_contrast(self, context, RR_group, layer_index)
    update_values(self, context, RR_group, layer_index)
    update_details_panel(self, context, RR_group, layer_index)
