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
from bpy.types import Operator
from bpy.props import EnumProperty

from .debug import log, debug_mode
from .. translations import translate


addon_keymaps = []

active = False
# NOTE: all operators, all ops which idnames starts with `manual_brush_tool_` are considered as tool in manual mode and will be included in too switching
# NOTE: other operators will be will be called with blender itself. but tools will handle that themselves. that is why tools are NOT ACTIVE!
op_key_defs = (
    "3D View",
    {"space_type": 'VIEW_3D', "region_type": 'WINDOW', },
    {
        "items": [
            # NOTE: enter manual mode will be active..
            ("scatter5.manual_enter", {'type': 'M', 'value': 'PRESS', 'shift': True, 'ctrl': True, 'alt': True, }, None, ),
            # NOTE: do not mess with exiting, all tools active = False, i just store data. tools has it's own mechanism to react on key press
            ("scatter5.manual_brush_tool_dot", {'type': 'ONE', 'value': 'PRESS', }, {'active': active, }, ),
            ("scatter5.manual_brush_tool_pose", {'type': 'TWO', 'value': 'PRESS', }, {'active': active, }, ),
            ("scatter5.manual_brush_tool_path", {'type': 'THREE', 'value': 'PRESS', }, {'active': active, }, ),
            ("scatter5.manual_brush_tool_chain", {'type': 'THREE', 'value': 'PRESS', 'shift': True, }, {'active': active, }, ),
            ("scatter5.manual_brush_tool_line", {'type': 'THREE', 'value': 'PRESS', 'ctrl': True, }, {'active': active, }, ),
            ("scatter5.manual_brush_tool_spatter", {'type': 'FOUR', 'value': 'PRESS', }, {'active': active, }, ),
            ("scatter5.manual_brush_tool_spray", {'type': 'FIVE', 'value': 'PRESS', }, {'active': active, }, ),
            ("scatter5.manual_brush_tool_spray_aligned", {'type': 'FIVE', 'value': 'PRESS', 'shift': True, }, {'active': active, }, ),
            ("scatter5.manual_brush_tool_lasso_fill", {'type': 'SIX', 'value': 'PRESS', }, {'active': active, }, ),
            ("scatter5.manual_brush_tool_clone", {'type': 'C', 'value': 'PRESS', }, {'active': active, }, ),
            ("scatter5.manual_brush_tool_eraser", {'type': 'E', 'value': 'PRESS', }, {'active': active, }, ),
            ("scatter5.manual_brush_tool_dilute", {'type': 'E', 'value': 'PRESS', 'shift': True, }, {'active': active, }, ),
            ("scatter5.manual_brush_tool_lasso_eraser", {'type': 'E', 'value': 'PRESS', 'ctrl': True, }, {'active': active, }, ),
            # ("scatter5.manual_brush_tool_smooth", {'type': 'NONE', 'value': 'PRESS', }, {'active': active, }, ),
            ("scatter5.manual_brush_tool_move", {'type': 'M', 'value': 'PRESS', }, {'active': active, }, ),
            ("scatter5.manual_brush_tool_free_move", {'type': 'M', 'value': 'PRESS', 'shift': True, }, {'active': active, }, ),
            ("scatter5.manual_brush_tool_attract_repulse", {'type': 'NONE', 'value': 'PRESS', }, {'active': active, }, ),
            ("scatter5.manual_brush_tool_push", {'type': 'NONE', 'value': 'PRESS', }, {'active': active, }, ),
            # ("scatter5.manual_brush_tool_turbulence", {'type': 'NONE', 'value': 'PRESS', }, {'active': active, }, ),
            ("scatter5.manual_brush_tool_relax2", {'type': 'NONE', 'value': 'PRESS', }, {'active': active, }, ),
            ("scatter5.manual_brush_tool_turbulence2", {'type': 'NONE', 'value': 'PRESS', }, {'active': active, }, ),
            ("scatter5.manual_brush_tool_manipulator", {'type': 'G', 'value': 'PRESS', }, {'active': active, }, ),
            ("scatter5.manual_brush_tool_drop_down", {'type': 'NONE', 'value': 'PRESS', }, {'active': active, }, ),
            ("scatter5.manual_brush_tool_rotation_set", {'type': 'R', 'value': 'PRESS', }, {'active': active, }, ),
            ("scatter5.manual_brush_tool_random_rotation", {'type': 'T', 'value': 'PRESS', }, {'active': active, }, ),
            ("scatter5.manual_brush_tool_comb", {'type': 'Y', 'value': 'PRESS', }, {'active': active, }, ),
            ("scatter5.manual_brush_tool_spin", {'type': 'Y', 'value': 'PRESS', 'shift': True, }, {'active': active, }, ),
            ("scatter5.manual_brush_tool_z_align", {'type': 'U', 'value': 'PRESS', }, {'active': active, }, ),
            ("scatter5.manual_brush_tool_scale_set", {'type': 'S', 'value': 'PRESS', }, {'active': active, }, ),
            ("scatter5.manual_brush_tool_grow_shrink", {'type': 'A', 'value': 'PRESS', }, {'active': active, }, ),
            ("scatter5.manual_brush_tool_object_set", {'type': 'O', 'value': 'PRESS', }, {'active': active, }, ),
            # # TODO: should i store all keys? but some such as exit are hard coded..
            # ("scatter5.manual_exit", {'type': 'ESC', 'value': 'PRESS', }, {'active': False, }, ),
        ],
    },
)
# NOTE: gesture definitions only, all NOT ACTIVE
mod_key_defs = (
    "3D View",
    {"space_type": 'VIEW_3D', "region_type": 'WINDOW', },
    {
        "items": [
            ("scatter5.manual_tool_gesture", {'type': 'F', 'value': 'PRESS', }, {'active': active, 'properties': [('gesture', 'PRIMARY', ), ], }, ),
            ("scatter5.manual_tool_gesture", {'type': 'F', 'value': 'PRESS', 'ctrl': True, }, {'active': active, 'properties': [('gesture', 'SECONDARY', ), ], }, ),
            ("scatter5.manual_tool_gesture", {'type': 'F', 'value': 'PRESS', 'shift': True, }, {'active': active, 'properties': [('gesture', 'TERTIARY', ), ], }, ),
            ("scatter5.manual_tool_gesture", {'type': 'F', 'value': 'PRESS', 'ctrl': True, 'shift': True, }, {'active': active, 'properties': [('gesture', 'QUATERNARY', ), ], }, ),
        ],
    },
)


def register_keyconfig():
    addon_keymaps.clear()
    
    kc = bpy.context.window_manager.keyconfigs.addon
    if(kc is None):
        return
    
    # ops
    km_name, km_args, km_content = op_key_defs
    km = kc.keymaps.new(km_name, **km_args)
    km_items = km_content["items"]
    for kmi_idname, kmi_args, kmi_data in km_items:
        kmi = km.keymap_items.new(kmi_idname, **kmi_args)
        if(kmi_data is not None):
            if(not kmi_data.get("active", True)):
                kmi.active = False
        addon_keymaps.append((km, kmi, ))
    
    # mods
    km_name, km_args, km_content = mod_key_defs
    km = kc.keymaps.new(km_name, **km_args)
    km_items = km_content["items"]
    for kmi_idname, kmi_args, kmi_data in km_items:
        kmi = km.keymap_items.new(kmi_idname, **kmi_args)
        if(kmi_data is not None):
            if(not kmi_data.get("active", True)):
                kmi.active = False
            kmi_props_data = kmi_data.get("properties", None)
            if(kmi_props_data is not None):
                for prop, value in kmi_props_data:
                    setattr(kmi.properties, prop, value)
        addon_keymaps.append((km, kmi, ))


def unregister_keyconfig():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()


# NOTE: this is internal, inactive, doing nothing. its sole purpose is to provide idname and enum for gesture key config
# DONE: maybe move that into keys module? makes more sense.. maybe..
class SCATTER5_OT_manual_tool_gesture(Operator, ):
    bl_idname = "scatter5.manual_tool_gesture"
    bl_label = translate("Manual Tool Gesture")
    bl_description = ""
    bl_options = {'INTERNAL'}
    
    gesture: EnumProperty(name="Gesture",
                          default='PRIMARY',
                          items=[('PRIMARY', "Primary", "", ),
                                 ('SECONDARY', "Secondary", "", ),
                                 ('TERTIARY', "Tertiary", "", ),
                                 ('QUATERNARY', "Quaternary", "", ), ],
                          )
    
    @classmethod
    def poll(cls, context):
        return False
    
    def execute(self, context):
        return {'CANCELLED'}


classes = (
    SCATTER5_OT_manual_tool_gesture,
)
