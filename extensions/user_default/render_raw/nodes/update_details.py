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


def update_sharpness(self, context, RR_group=None, layer_index=None):
    RR = get_settings(context, RR_group, layer_index)
    FAC = RR.props_pre.layer_factor
    SHARPNESS = RR.nodes_post['Sharpness']
    PROPS = RR.props_post

    if not is_layer_used(RR) or not RR.props_pre.use_values or PROPS.sharpness == 0:
        SHARPNESS.mute = True
    else:
        SHARPNESS.mute = False
        SHARPNESS.inputs['Strength'].default_value = PROPS.sharpness * FAC
        SHARPNESS.inputs['Masking'].default_value = PROPS.sharpness_mask


def update_texture(self, context, RR_group=None, layer_index=None):
    RR = get_settings(context, RR_group, layer_index)
    FAC = RR.props_pre.layer_factor
    TEXTURE = RR.nodes_post['Texture']
    PROPS = RR.props_post

    if not is_layer_used(RR) or not RR.props_pre.use_values or PROPS.texture == 0:
        TEXTURE.mute = True
    else:
        TEXTURE.mute = False
        TEXTURE.inputs['Strength'].default_value = PROPS.texture * FAC
        TEXTURE.inputs['Keep Color'].default_value = PROPS.texture_color


def update_clarity(self, context, RR_group=None, layer_index=None):
    RR = get_settings(context, RR_group, layer_index)
    FAC = RR.props_pre.layer_factor
    CLARITY = RR.nodes_post['Clarity']
    PROPS = RR.props_post

    if not is_layer_used(RR) or not RR.props_pre.use_values or PROPS.clarity == 0:
        CLARITY.mute = True
    else:
        CLARITY.mute = False
        CLARITY.inputs['Strength'].default_value = PROPS.clarity * FAC
        CLARITY.inputs['Size'].default_value = PROPS.clarity_size


def update_details_panel(self, context, RR_group=None, layer_index=None):
    update_sharpness(self, context, RR_group, layer_index)
    update_texture(self, context, RR_group, layer_index)
    update_clarity(self, context, RR_group, layer_index)