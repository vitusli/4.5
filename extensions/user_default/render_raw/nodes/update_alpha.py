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


def update_alpha(self, context, RR_group=None):
    RR = get_settings(context, RR_group)
    PROPS = RR.props_group
    ALPHA = RR.nodes_group['Manage Alpha']

    if PROPS.alpha_factor == 0:
        ALPHA.mute = True
    else:
        ALPHA.mute = False
        ALPHA.inputs['Factor'].default_value = PROPS.alpha_factor
        ALPHA.inputs['Method'].default_value = int(PROPS.alpha_method)