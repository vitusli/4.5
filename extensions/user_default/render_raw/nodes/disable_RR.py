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
from .active_group import get_active_group
from ..utilities.view_transforms import view_transforms_disable
from ..utilities.nodes import get_RR_nodes
from ..utilities.cache import cacheless


@cacheless
def disable_RR(self, context):
    RR = get_active_group(context).render_raw
    RR_SCENE = context.scene.render_raw_scene
    VIEW = context.scene.view_settings

    # Convert nodes to scene settings
    if view_transforms_disable[RR.view_transform]:
        VIEW.view_transform = view_transforms_disable[RR.view_transform]

    #TODO: Is this still needed if exposure is not part of use_values?
    if RR.use_values:
        VIEW.exposure = RR.exposure
    else:
        VIEW.exposure = RR_SCENE.prev_exposure

    # Restore previous settings
    prev_look = RR_SCENE.prev_look
    view_transform = VIEW.view_transform
    if prev_look in ['None', '']:
        VIEW.look = 'None'
    elif view_transform == 'AgX':
        VIEW.look = f"{view_transform} - {prev_look}"
    else:
        VIEW.look = prev_look

    VIEW.use_curve_mapping = RR_SCENE.prev_use_curves

    if bpy.app.version >= (4, 3, 0):
        VIEW.use_white_balance = RR_SCENE.prev_use_white_balance
        VIEW.white_balance_temperature = RR_SCENE.prev_temperature
        VIEW.white_balance_tint = RR_SCENE.prev_tint

    for RR_node in get_RR_nodes(context):
        RR_node.mute = True
