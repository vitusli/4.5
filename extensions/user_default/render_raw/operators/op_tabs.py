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

class SwitchTabs(bpy.types.Operator):
    bl_label = 'Reset Scene Color Settings'
    bl_idname = "render.render_raw_switch_tabs"
    bl_description = 'Switches tabs in the Render Raw UI'

    prop: bpy.props.StringProperty()
    active: bpy.props.IntProperty()

    def execute(self, context):
        RR = get_settings(context, use_cache=False)
        RR.props_group[self.prop] = self.active
        return{'FINISHED'}

def register():
    bpy.utils.register_class(SwitchTabs)

def unregister():
    bpy.utils.unregister_class(SwitchTabs)