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
from ..utilities.conversions import map_range, set_alpha
from ..utilities.settings import get_settings
from ..utilities.layers import is_layer_used


def update_vignette(self, context, RR_group=None, layer_index=None):
    RR = get_settings(context, RR_group, layer_index)
    FAC = RR.props_pre.layer_factor
    PROPS = RR.props_post # Could be saved in pre or post now, but in post for reading older files
    
    NODE_PRE = RR.nodes_pre['Vignette']
    NODE_POST = RR.nodes_post['Vignette']

    if not RR.use_effects or PROPS.vignette_factor == 0 or not is_layer_used(RR):
        NODE_PRE.mute = True
        NODE_POST.mute = True
    else:
        NODE_PRE.mute = False
        NODE_POST.mute = PROPS.vignette_linear_blend == 1

    for V in [NODE_PRE, NODE_POST]:
            V.inputs['Highlights'].default_value = PROPS.vignette_highlights
            V.inputs['Feathering'].default_value = PROPS.vignette_feathering
            V.inputs['Roundness'].default_value = PROPS.vignette_roundness
            V.inputs['Color'].default_value = PROPS.vignette_color
            V.inputs['Scale X'].default_value = PROPS.vignette_scale_x - 0.01
            V.inputs['Scale Y'].default_value = PROPS.vignette_scale_y - 0.01
            V.inputs['Shift X'].default_value = PROPS.vignette_shift_x
            V.inputs['Shift Y'].default_value = PROPS.vignette_shift_y 
            V.inputs['Rotation'].default_value = PROPS.vignette_rotation

    # All linear blending happens pre-transform, while the simple mix happens post-transform
    NODE_PRE.inputs['Factor'].default_value = PROPS.vignette_factor * FAC 
    NODE_POST.inputs['Factor'].default_value = PROPS.vignette_factor * (1 - PROPS.vignette_linear_blend) * FAC 


def update_bloom(self, context, RR_group=None, layer_index=None):
    RR = get_settings(context, RR_group, layer_index)
    FAC = RR.props_pre.layer_factor
    PROPS = RR.props_pre
    
    if bpy.app.version >= (4, 5, 0):
        GLARE = RR.nodes_pre['Glare']
        GLARE.inputs['Factor'].default_value = PROPS.glare
        GLARE.inputs['Threshold'].default_value = PROPS.glare_threshold
        GLARE.inputs['Saturation'].default_value = PROPS.bloom_saturation
        GLARE.inputs['Tint'].default_value = [PROPS.bloom_tint[0], PROPS.bloom_tint[1], PROPS.bloom_tint[2], 1]
        GLARE.inputs['Bloom Strength'].default_value = PROPS.bloom
        GLARE.inputs['Size'].default_value = PROPS.bloom_size_float
    
    else:
        GLARE_NODES = RR.nodes_pre['Glare'].node_tree.nodes
        GLARE_LINKS = RR.nodes_pre['Glare'].node_tree.links
        BLOOM = GLARE_NODES['Bloom']
        BLOOM_NODES = BLOOM.node_tree.nodes
        GLARE = GLARE_NODES['Glare']
        ADD = GLARE_NODES['Add Bloom']

        GLARE_NODES['Glare Alpha'].mute = (
            not RR.use_effects or
            not is_layer_used(RR) or
            (PROPS.bloom == 0 and PROPS.streaks == 0)
        )

        if (
            not RR.use_effects or
            PROPS.glare == 0 or
            PROPS.bloom == 0 or
            not is_layer_used(RR)
        ):
            BLOOM.mute = True
            GLARE.mute = True
            ADD.mute = True
            return

        if bpy.app.version >= (4, 4, 0):
            # The whole glare node was overhauled
            GLARE.mute = False
            ADD.mute = False
            GLARE_LINKS.new(GLARE.outputs[1], ADD.inputs[2])
            GLARE_LINKS.new(GLARE.outputs[0], GLARE_NODES['Ghosting'].inputs[0])
            GLARE.glare_type = 'BLOOM'
            GLARE.inputs['Strength'].default_value = PROPS.bloom * PROPS.glare * FAC
            GLARE.inputs['Threshold'].default_value = PROPS.glare_threshold
            GLARE.inputs['Smoothness'].default_value = 1
            GLARE.inputs['Saturation'].default_value = PROPS.bloom_saturation
            GLARE.inputs['Tint'].default_value = set_alpha(PROPS.bloom_tint, 1)
            GLARE.inputs['Size'].default_value = PROPS.bloom_size_float
            if PROPS.glare_quality == 5:
                GLARE.quality = 'HIGH'
            elif PROPS.glare_quality == 4:
                GLARE.quality = 'MEDIUM'
            elif PROPS.glare_quality == 3:
                GLARE.quality = 'MEDIUM'
            elif PROPS.glare_quality == 2:
                GLARE.quality = 'LOW'
            elif PROPS.glare_quality == 1:
                GLARE.quality = 'LOW'
        elif bpy.app.version >= (4, 2, 0):
            # Bloom was implemented in the compositor's glare node
            GLARE.mute = False
            GLARE_LINKS.new(GLARE.outputs[0], GLARE_NODES['Ghosting'].inputs[0])
            GLARE.glare_type = 'BLOOM'
            GLARE.mix = PROPS.bloom * PROPS.glare * FAC - 1
            GLARE.threshold = PROPS.glare_threshold + 0.001
            GLARE.size = PROPS.bloom_size
            if PROPS.glare_quality == 5:
                GLARE.quality = 'HIGH'
            elif PROPS.glare_quality == 4:
                GLARE.quality = 'MEDIUM'
            elif PROPS.glare_quality == 3:
                GLARE.quality = 'MEDIUM'
            elif PROPS.glare_quality == 2:
                GLARE.quality = 'LOW'
            elif PROPS.glare_quality == 1:
                GLARE.quality = 'LOW'
        else:
            # Fakes bloom with multiple blur nodes before better bloom was implemented
            BLOOM.mute = False
            GLARE_LINKS.new(BLOOM.outputs[0], GLARE_NODES['Ghosting'].inputs[0])
            BLOOM.inputs['Fac'].default_value = PROPS.bloom * PROPS.glare
            BLOOM.inputs['Threshold'].default_value = PROPS.glare_threshold + 0.001
            if PROPS.glare_quality == 5:
                BLOOM_NODES['Blur 1'].mute = False
                BLOOM_NODES['Blur 2'].mute = False
                BLOOM_NODES['Blur 3'].mute = False
                BLOOM_NODES['Blur 4'].mute = False
                BLOOM_NODES['Blur 5'].mute = False
            elif PROPS.glare_quality == 4:
                BLOOM_NODES['Blur 1'].mute = False
                BLOOM_NODES['Blur 2'].mute = False
                BLOOM_NODES['Blur 3'].mute = False
                BLOOM_NODES['Blur 4'].mute = False
                BLOOM_NODES['Blur 5'].mute = True
            elif PROPS.glare_quality == 3:
                BLOOM_NODES['Blur 1'].mute = True
                BLOOM_NODES['Blur 2'].mute = False
                BLOOM_NODES['Blur 3'].mute = False
                BLOOM_NODES['Blur 4'].mute = False
                BLOOM_NODES['Blur 5'].mute = True
            elif PROPS.glare_quality == 2:
                BLOOM_NODES['Blur 1'].mute = True
                BLOOM_NODES['Blur 2'].mute = True
                BLOOM_NODES['Blur 3'].mute = False
                BLOOM_NODES['Blur 4'].mute = False
                BLOOM_NODES['Blur 5'].mute = True
            elif PROPS.glare_quality == 1:
                BLOOM_NODES['Blur 1'].mute = True
                BLOOM_NODES['Blur 2'].mute = True
                BLOOM_NODES['Blur 3'].mute = True
                BLOOM_NODES['Blur 4'].mute = False
                BLOOM_NODES['Blur 5'].mute = True
            # BLOOM.inputs['Blend Highlights'].default_value = PROPS.bloom_blending


def update_streaks(self, context, RR_group=None, layer_index=None):
    # Only used pre Blender 4.5 
    RR = get_settings(context, RR_group, layer_index)
    FAC = RR.props_pre.layer_factor
    PROPS = RR.props_pre

    if bpy.app.version >= (4, 5, 0):
        GLARE = RR.nodes_pre['Glare']
        GLARE.inputs['Factor'].default_value = PROPS.glare
        GLARE.inputs['Threshold'].default_value = PROPS.glare_threshold
        GLARE.inputs['Streaks Strength'].default_value = PROPS.streaks
        GLARE.inputs['Length'].default_value = PROPS.streak_length
        GLARE.inputs['Count'].default_value = PROPS.streak_count
        GLARE.inputs['Angle'].default_value = PROPS.streak_angle

    else:
        GLARE_NODES = RR.nodes_pre['Glare'].node_tree.nodes
        GLARE_LINKS = RR.nodes_pre['Glare'].node_tree.links
        STREAKS = GLARE_NODES['Streaks']
        MIX = GLARE_NODES['Streaks Mix']
        STRENGTH = GLARE_NODES['Streaks Strength']
        ADD = GLARE_NODES['Add Streaks']

        GLARE_NODES['Glare Alpha'].mute = (
            not RR.use_effects or
            not is_layer_used(RR) or
            (PROPS.bloom == 0 and PROPS.streaks == 0)
        )
        if not is_layer_used(RR) or not RR.use_effects or PROPS.glare == 0 or PROPS.streaks == 0:
            STREAKS.mute = True
            MIX.mute = True
            ADD.mute = True
            return
        
        if bpy.app.version >= (4, 4, 0):
            # The whole glare node was overhauled
            STREAKS.mute = False
            MIX.mute = False
            ADD.mute = False
            GLARE_LINKS.new(STREAKS.outputs[1], ADD.inputs[2])
            STRENGTH.outputs[0].default_value = PROPS.streaks * PROPS.glare * FAC
            STREAKS.inputs['Strength'].default_value = PROPS.streaks * PROPS.glare
            STREAKS.inputs['Threshold'].default_value = PROPS.glare_threshold
            STREAKS.inputs['Streaks'].default_value = PROPS.streak_count
            STREAKS.inputs['Streaks Angle'].default_value = PROPS.streak_angle
            STREAKS.inputs['Fade'].default_value = map_range(PROPS.streak_length, 0, 1, 0.9, 1)
        else:
            STREAKS.mute = False
            MIX.mute = False
            STRENGTH.outputs[0].default_value = PROPS.streaks * PROPS.glare * FAC
            STREAKS.mix = (PROPS.streaks * PROPS.glare) - 1
            STREAKS.threshold = PROPS.glare_threshold
            STREAKS.streaks = PROPS.streak_count
            STREAKS.angle_offset = PROPS.streak_angle
            STREAKS.fade = map_range(PROPS.streak_length, 0, 1, 0.9, 1)

def update_ghosting(self, context, RR_group=None, layer_index=None):
    # Only used pre Blender 4.5 
    RR = get_settings(context, RR_group, layer_index)
    FAC = RR.props_pre.layer_factor
    PROPS = RR.props_pre
    
    if bpy.app.version >= (4, 5, 0):
        GLARE = RR.nodes_pre['Glare']
        GLARE.inputs['Factor'].default_value = PROPS.glare
        GLARE.inputs['Threshold'].default_value = PROPS.glare_threshold
        GLARE.inputs['Ghosting Strength'].default_value = PROPS.ghosting

    else:
        GLARE_NODES = RR.nodes_pre['Glare'].node_tree.nodes
        GLARE_LINKS = RR.nodes_pre['Glare'].node_tree.links
        GHOSTING = GLARE_NODES['Ghosting']
        ADD = GLARE_NODES['Add Ghosting']

        GLARE_NODES['Glare Alpha'].mute = (
            not RR.use_effects or
            not is_layer_used(RR) or
            (PROPS.bloom == 0 and PROPS.streaks == 0)
        )

        if not is_layer_used(RR) or not RR.use_effects or PROPS.glare == 0 or PROPS.ghosting == 0:
            GHOSTING.mute = True
            ADD.mute = True
            return

        if bpy.app.version >= (4, 4, 0):
            # The whole glare node was overhauled
            GHOSTING.mute = False
            ADD.mute = False
            GLARE_LINKS.new(GHOSTING.outputs[1], ADD.inputs[2])
            GHOSTING.inputs['Strength'].default_value = PROPS.ghosting / 4 * PROPS.glare * FAC
            GHOSTING.inputs['Threshold'].default_value = PROPS.glare_threshold
            if PROPS.glare_quality == 5:
                GHOSTING.quality = 'HIGH'
            elif PROPS.glare_quality == 4:
                GHOSTING.quality = 'MEDIUM'
            elif PROPS.glare_quality == 3:
                GHOSTING.quality = 'MEDIUM'
            elif PROPS.glare_quality == 2:
                GHOSTING.quality = 'LOW'
            elif PROPS.glare_quality == 1:
                GHOSTING.quality = 'LOW'
        else:
            GHOSTING.mute = False
            GHOSTING.mix = PROPS.ghosting / 4 * PROPS.glare * FAC - 1
            GHOSTING.threshold = PROPS.glare_threshold
            if PROPS.glare_quality == 5:
                GHOSTING.quality = 'HIGH'
            elif PROPS.glare_quality == 4:
                GHOSTING.quality = 'MEDIUM'
            elif PROPS.glare_quality == 3:
                GHOSTING.quality = 'MEDIUM'
            elif PROPS.glare_quality == 2:
                GHOSTING.quality = 'LOW'
            elif PROPS.glare_quality == 1:
                GHOSTING.quality = 'LOW'


def update_glare(self, context, RR_group=None, layer_index=None):
    update_bloom(self, context, RR_group, layer_index)
    update_streaks(self, context, RR_group, layer_index)
    update_ghosting(self, context, RR_group, layer_index)


def update_distortion(self, context, RR_group=None, layer_index=None):
    RR = get_settings(context, RR_group, layer_index)
    FAC = RR.props_pre.layer_factor
    PROPS = RR.props_post
    DISTORTION = RR.nodes_post['Lens Distortion']

    if not is_layer_used(RR) or not RR.use_effects or (PROPS.distortion == 0 and PROPS.dispersion == 0):
        DISTORTION.mute = True
    else:
        DISTORTION.mute = False
        DISTORTION.inputs['Distortion'].default_value = PROPS.distortion * FAC / 2
        DISTORTION.inputs['Dispersion'].default_value = PROPS.dispersion * FAC / 4


def update_grain(self, context, RR_group=None, layer_index=None):
    RR = get_settings(context, RR_group, layer_index)
    FAC = RR.props_pre.layer_factor
    PROPS = RR.props_post
    FAST = RR.nodes_post['Film Grain Fast']
    ACCURATE = RR.nodes_post['Film Grain Accurate']

    if not is_layer_used(RR) or not RR.use_effects or PROPS.grain == 0 or PROPS.grain_method == 'ACCURATE':
        FAST.mute = True
    else:
        FAST.mute = False
        FAST.inputs['Strength'].default_value = PROPS.grain * FAC
        FAST.inputs['Scale'].default_value = PROPS.grain_scale
        FAST.inputs['Saturation'].default_value = PROPS.grain_saturation

        if bpy.app.version >= (4, 5, 0):
            FAST.inputs['Detail'].default_value = PROPS.grain_steps
            FAST.inputs['Animate'].default_value = PROPS.grain_is_animated
        
        else:
            FAST.inputs['Aspect Correction'].default_value = PROPS.grain_aspect
            FAST.node_tree.nodes['Animate Offset'].mute = not PROPS.grain_is_animated
            FAST.node_tree.links.new(
                FAST.node_tree.nodes[f'Step {PROPS.grain_steps}'].outputs[0],
                FAST.node_tree.nodes['HSV'].inputs[0]
            )

    if not RR.use_effects or PROPS.grain == 0 or PROPS.grain_method == 'FAST':
        ACCURATE.mute = True
    else:
        ACCURATE.mute = False
        ACCURATE.inputs['Strength'].default_value = PROPS.grain * FAC
        ACCURATE.inputs['Scale'].default_value = PROPS.grain_scale
        ACCURATE.inputs['Saturation'].default_value = PROPS.grain_saturation

        if bpy.app.version >= (4, 5, 0):
            ACCURATE.inputs['Animate'].default_value = PROPS.grain_is_animated
            output_idx = 0 if PROPS.grain_steps == 1 else 2
            ACCURATE.node_tree.links.new(
                ACCURATE.node_tree.nodes[f'Step {PROPS.grain_steps}'].outputs[output_idx],
                ACCURATE.node_tree.nodes['Group Output'].inputs[0]
            )
        else:
            ACCURATE.inputs['Aspect Correction'].default_value = PROPS.grain_aspect
            ACCURATE.node_tree.nodes['Step 1'].node_tree.nodes['Animate Offset'].mute = not PROPS.grain_is_animated
            ACCURATE.node_tree.links.new(
                ACCURATE.node_tree.nodes[f'Step {PROPS.grain_steps}'].outputs[0],
                ACCURATE.node_tree.nodes['Group Output'].inputs[0]
            )

def update_effects_panel(self, context, RR_group=None, layer_index=None):
    update_vignette(self, context, RR_group, layer_index)
    update_distortion(self, context, RR_group, layer_index)
    update_glare(self, context, RR_group, layer_index)
    update_grain(self, context, RR_group, layer_index)