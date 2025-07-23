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
# (c) 2024 Dorian Borremans

################################################################################################
#  .oooooo..o                                   oooo                                        o8o
# d8P'    `Y8                                   `888                                        `"'
# Y88bo.      oooo    ooo ooo. .oo.    .ooooo.   888 .oo.   oooo d8b  .ooooo.  ooo. .oo.   oooo    oooooooo  .ooooo.
#  `"Y8888o.   `88.  .8'  `888P"Y88b  d88' `"Y8  888P"Y88b  `888""8P d88' `88b `888P"Y88b  `888   d'""7d8P  d88' `88b
#      `"Y88b   `88..8'    888   888  888        888   888   888     888   888  888   888   888     .d8P'   888ooo888
# oo     .d8P    `888'     888   888  888   .o8  888   888   888     888   888  888   888   888   .d8P'  .P 888    .o
# 8""88888P'      .8'     o888o o888o `Y8bod8P' o888o o888o d888b    `Y8bod8P' o888o o888o o888o d8888888P  `Y8bod8P'
#             .o..P'
#             `Y8P'
################################################################################################


import bpy

from .. translations import translate
from .. resources.icons import cust_icon

from .. utils.extra_utils import dprint
from .. ui import ui_templates


#TODO should make sure sync don't work based on psy.name but psy.uuid
# See synchonisation on update on update factory 

#       .o.                   o8o
#      .888.                  `"'
#     .8"888.     oo.ooooo.  oooo
#    .8' `888.     888' `88b `888
#   .88ooo8888.    888   888  888
#  .8'     `888.   888   888  888
# o88o     o8888o  888bod8P' o888o
#                  888
#                 o888o


def search_all_psys(self, context, edit_text):
    """return list of all potential psys for search"""
    
    return [p.name for p in bpy.context.scene.scatter5.get_all_psys(search_mode="active_view_layer", also_linked=False) if (edit_text in p.name) and (p.name!=self.psy_name)]


class SCATTER5_PR_channel_members(bpy.types.PropertyGroup):
    """blend_prefs().sync_channels[i].members"""

    psy_name : bpy.props.StringProperty(
        default="",
        search=search_all_psys,
        search_options={'SUGGESTION','SORT'},
        )
    psy_uuid : bpy.props.IntProperty() #TODO, should base this system on uuid, not names..

    def get_psy(self):
        """get psy item from member"""
        
        return bpy.context.scene.scatter5.get_psy_by_name(self.psy_name) 

class SCATTER5_PR_sync_channels(bpy.types.PropertyGroup):
    """blend_prefs().sync_channels"""

    #name of this channel
    name    : bpy.props.StringProperty()
    
    #members of this channel
    members : bpy.props.CollectionProperty(type=SCATTER5_PR_channel_members) #Children Collection
        
    #which category of settings should this channel synchronize?
    s_surface      : bpy.props.BoolProperty(default=False) #never sync by default
    s_distribution : bpy.props.BoolProperty(default=True)
    s_mask         : bpy.props.BoolProperty(default=False) #never sync by default
    s_scale        : bpy.props.BoolProperty(default=True)
    s_rot          : bpy.props.BoolProperty(default=True)
    s_pattern      : bpy.props.BoolProperty(default=True)
    s_abiotic      : bpy.props.BoolProperty(default=True)
    s_proximity    : bpy.props.BoolProperty(default=True)
    s_ecosystem    : bpy.props.BoolProperty(default=True)
    s_push         : bpy.props.BoolProperty(default=True)
    s_wind         : bpy.props.BoolProperty(default=True)
    s_visibility   : bpy.props.BoolProperty(default=True)
    s_instances    : bpy.props.BoolProperty(default=True)
    s_display      : bpy.props.BoolProperty(default=True)

    def name_in_members(self,psy_name):
        """check if a psy exists in sync channel members"""

        if (len(self.members)==0):
            return False

        for m in self.members:
            if (m.psy_name==psy_name):
                return True

        return False

    def psy_settings_in_channel(self,psy_name,category):
        """check if given settings category is being sync"""

        if (not self.name_in_members(psy_name)):
            return False

        if (category not in self.bl_rna.properties.keys()):
            return False

        return getattr(self,category)

    def get_sibling_members(self):
        """return a list of psy members"""

        rlist = []
        for m in self.members:
            psy = m.get_psy()
            if ( (psy is not None) and (psy not in rlist) ):
                rlist.append(psy)   

        return rlist

    def add_psys_members(self, *args):
        """add the given psy args as new members"""

        for p in args: 
            if (p.name not in [m.psy_name for m in self.members]):
                mem = self.members.add()
                mem.psy_name = p.name

        return None 

    def category_list(self):

        rlist = []
        if (self.s_surface):
            rlist.append("s_surface")
        if (self.s_distribution):
            rlist.append("s_distribution")
        if (self.s_mask):
            rlist.append("s_mask")
        if (self.s_scale):
            rlist.append("s_scale")
        if (self.s_rot):
            rlist.append("s_rot")
        if (self.s_pattern):
            rlist.append("s_pattern")
        if (self.s_abiotic):
            rlist.append("s_abiotic")
        if (self.s_proximity):
            rlist.append("s_proximity")
        if (self.s_ecosystem):
            rlist.append("s_ecosystem")
        if (self.s_push):
            rlist.append("s_push")
        if (self.s_wind):
            rlist.append("s_wind")
        if (self.s_instances):
            rlist.append("s_instances")
        if (self.s_visibility):
            rlist.append("s_visibility")
        if (self.s_display):
            rlist.append("s_display")

        return rlist

#   .oooooo.                 o8o
#  d8P'  `Y8b                `"'
# 888           oooo  oooo  oooo
# 888           `888  `888  `888
# 888     ooooo  888   888   888
# `88.    .88'   888   888   888
#  `Y8bood8P'    `V88V"V8P' o888o


class SCATTER5_PT_sync_cat_menu(bpy.types.Panel):

    bl_idname      = "SCATTER5_PT_sync_cat_menu"
    bl_label       = translate("Channel Settings")
    bl_description = translate("Choose which scatter-system(s) settings type will be affected by this synchronization channel")
    bl_category    = ""
    bl_space_type  = "VIEW_3D"
    bl_region_type = "HEADER" #Hide this panel? not sure how to hide them...

    def draw(self, context):
        layout = self.layout
        col = layout.column()

        col.label(text=translate("Synchronization by Category")+" :")

        active_channel = context.pass_ui_arg_channel

        ui_templates.bool_toggle(col, active_channel, "s_surface", label=translate("Surface"), icon="SURFACE_NSURFACE", use_layout_left_spacer=False,)
        ui_templates.bool_toggle(col, active_channel, "s_distribution", label=translate("Distribution"), icon="STICKY_UVS_DISABLE", use_layout_left_spacer=False,)
        ui_templates.bool_toggle(col, active_channel, "s_mask", label=translate("Culling Masks"), icon="MOD_MASK", use_layout_left_spacer=False,)
        ui_templates.bool_toggle(col, active_channel, "s_scale", label=translate("Scale"), icon="OBJECT_ORIGIN", use_layout_left_spacer=False,)
        ui_templates.bool_toggle(col, active_channel, "s_rot", label=translate("Rotation"), icon="CON_ROTLIKE", use_layout_left_spacer=False,)

        col.separator()

        ui_templates.bool_toggle(col, active_channel, "s_pattern", label=translate("Pattern"), icon="TEXTURE", use_layout_left_spacer=False,)

        col.separator()

        ui_templates.bool_toggle(col, active_channel, "s_abiotic", label=translate("Abiotic"), icon="W_TERRAIN", use_layout_left_spacer=False,)
        ui_templates.bool_toggle(col, active_channel, "s_proximity", label=translate("Proximity"), icon="W_SNAP", use_layout_left_spacer=False,)
        ui_templates.bool_toggle(col, active_channel, "s_ecosystem", label=translate("Ecosystem"), icon="W_ECOSYSTEM",use_layout_left_spacer=False,)
        ui_templates.bool_toggle(col, active_channel, "s_push", label=translate("Offset"), icon="CON_LOCLIKE", use_layout_left_spacer=False,)
        ui_templates.bool_toggle(col, active_channel, "s_wind", label=translate("Wind"), icon="FORCE_WIND", use_layout_left_spacer=False,)

        col.separator()

        ui_templates.bool_toggle(col, active_channel, "s_visibility", label=translate("Visibility"), icon="HIDE_OFF", use_layout_left_spacer=False,)
        ui_templates.bool_toggle(col, active_channel, "s_instances", label=translate("Instances"), icon="W_INSTANCE", use_layout_left_spacer=False,)
        ui_templates.bool_toggle(col, active_channel, "s_display", label=translate("Display"), icon="CAMERA_STEREO", use_layout_left_spacer=False,)

        col.separator(factor=0.2)

        return None


class SCATTER5_PT_sync_cat_members(bpy.types.Panel):

    bl_idname      = "SCATTER5_PT_sync_cat_members"
    bl_label       = translate("Channel Members")
    bl_description = translate("Choose which scatter-system(s) will be affected by this synchronization channel")
    bl_category    = ""
    bl_space_type  = "VIEW_3D"
    bl_region_type = "HEADER" #Hide this panel? not sure how to hide them...

    def draw(self, context):
        layout = self.layout
        col = layout.column()

        from ... __init__ import blend_prefs
        scat_data  = blend_prefs()
        scat_scene = context.scene.scatter5
        
        active_channel = context.pass_ui_arg_channel
        active_channel_idx = [i for i,c in enumerate(scat_data.sync_channels) if c==active_channel][0]

        if (len(active_channel.members)==0):

            col.label(text=translate("No Members Added Yet"))

            add_icon = col.row(align=True)
            add_icon.enabled = bool(len(scat_data.sync_channels))
            op = add_icon.operator("scatter5.sync_members_ops", icon_value=cust_icon("W_MEMBER_ADD"), text=translate("Add New Member"))
            op.add = True
            op.channel_idx = [i for i,c in enumerate(scat_data.sync_channels) if c==active_channel][0]

            col.separator()

            return None

        col.label(text=translate("Synchronization Members")+" :")

        if (len(active_channel.members)!=0):

            mcol = col.column()

            for i,m in enumerate(active_channel.members):
                row = mcol.row(align=True)

                psy = m.get_psy()
                if (psy is not None):

                    #psy color
                    clr = row.row(align=True)
                    clr.scale_x = 0.3
                    clr.prop(psy, "s_color", text="")
                
                #psy ptr 
                ptrs = row.column(align=True)
                ptr = ptrs.row(align=True)
                ptr.alert = (m.psy_name not in [p.name for p in scat_scene.get_all_psys(search_mode="active_view_layer")])
                ptr.prop(m, "psy_name", text="", icon="PARTICLES",)

                #remove operator
                remo = row.column(align=True)
                op = remo.operator("scatter5.sync_members_ops",text="",icon="TRASH", emboss=True,)
                op.remove = True
                op.channel_idx = active_channel_idx
                op.member_idx = i
                
                mcol.separator(factor=0.2)
                continue

            col.separator(factor=0.5)

            ope = col.row(align=True)
            ope.scale_y = 0.9
            op = ope.operator("scatter5.sync_ensure", icon="FILE_REFRESH",)
            op.channel_idx = active_channel_idx    

            col.separator(factor=0.5)

        ope = col.row(align=True)
        ope.scale_y = 0.9
        ope.enabled = bool(len(scat_data.sync_channels))
        op = ope.operator("scatter5.sync_members_ops", icon_value=cust_icon("W_MEMBER_ADD"), text=translate("Add New Member"))
        op.add = True
        op.channel_idx = active_channel_idx

        return None


class SCATTER5_UL_sync_channels(bpy.types.UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        
        if (not item):
            return None

        col = layout.column()
        row = col.row()
        
        prop = row.row()
        prop.prop(item, "name", text="", emboss=False, )

        menu = row.row()
        menu.scale_y = 0.8
        menu.emboss = "NONE"
        menu.alignment = "RIGHT"
        menu.context_pointer_set("pass_ui_arg_channel", item)
        menu.popover(panel="SCATTER5_PT_sync_cat_menu",text="",icon="PREFERENCES")

        menu = row.row()
        menu.scale_y = 0.8
        menu.emboss = "NONE"
        menu.alignment = "RIGHT"
        menu.active = bool(len(item.members))
        menu.context_pointer_set("pass_ui_arg_channel", item)
        txt = f"{len(item.members):02}"
        menu.popover(panel="SCATTER5_PT_sync_cat_members",text=txt,icon="COMMUNITY")

        return None


#       .o.             .o8        .o8
#      .888.           "888       "888
#     .8"888.      .oooo888   .oooo888
#    .8' `888.    d88' `888  d88' `888
#   .88ooo8888.   888   888  888   888
#  .8'     `888.  888   888  888   888
# o88o     o8888o `Y8bod88P" `Y8bod88P"



class SCATTER5_OT_sync_channels_ops(bpy.types.Operator):

    bl_idname      = "scatter5.sync_channels_ops"
    bl_label       = translate("Add/Remove Channel")
    bl_description = translate("Add or remove a channel from the synchronization list")
    bl_options     = {'INTERNAL','UNDO'}

    add    : bpy.props.BoolProperty(default=False, options={"SKIP_SAVE",},)
    remove : bpy.props.BoolProperty(default=False, options={"SKIP_SAVE",},)

    def execute(self, context):

        from ... __init__ import blend_prefs
        scat_data  = blend_prefs()

        if (self.add):
            s = scat_data.sync_channels.add()
            s.name = f"Channel{len(scat_data.sync_channels):02}"
            scat_data.sync_channels_idx=len(scat_data.sync_channels)-1

        if (self.remove):
            scat_data.sync_channels.remove(scat_data.sync_channels_idx)
            if (scat_data.sync_channels_idx>=len(scat_data.sync_channels)):
                scat_data.sync_channels_idx=len(scat_data.sync_channels)-1

        return {'FINISHED'}


class SCATTER5_OT_sync_members_ops(bpy.types.Operator):

    bl_idname      = "scatter5.sync_members_ops"
    bl_label       = ""
    bl_description = ""
    bl_options     = {'INTERNAL','UNDO'}

    add    : bpy.props.BoolProperty(default=False, options={"SKIP_SAVE",},)
    remove : bpy.props.BoolProperty(default=False, options={"SKIP_SAVE",},)

    channel_idx : bpy.props.IntProperty()
    member_idx  : bpy.props.IntProperty()

    def execute(self, context):

        from ... __init__ import blend_prefs
        scat_data  = blend_prefs()
        
        active_channel = scat_data.sync_channels[self.channel_idx]

        if (self.add):
            active_channel.members.add()

        if (self.remove):
            active_channel.members.remove(self.member_idx)

        return {'FINISHED'}


#  .oooooo..o                                      oooooooooooo                                       .    o8o
# d8P'    `Y8                                      `888'     `8                                     .o8    `"'
# Y88bo.      oooo    ooo ooo. .oo.    .ooooo.      888         oooo  oooo  ooo. .oo.    .ooooo.  .o888oo oooo   .ooooo.  ooo. .oo.
#  `"Y8888o.   `88.  .8'  `888P"Y88b  d88' `"Y8     888oooo8    `888  `888  `888P"Y88b  d88' `"Y8   888   `888  d88' `88b `888P"Y88b
#      `"Y88b   `88..8'    888   888  888           888    "     888   888   888   888  888         888    888  888   888  888   888
# oo     .d8P    `888'     888   888  888   .o8     888          888   888   888   888  888   .o8   888 .  888  888   888  888   888
# 8""88888P'      .8'     o888o o888o `Y8bod8P'    o888o         `V88V"V8P' o888o o888o `Y8bod8P'   "888" o888o `Y8bod8P' o888o o888o
#             .o..P'
#             `Y8P'


class SCATTER5_OT_sync_ensure(bpy.types.Operator):
    """make sure all settings are set to the same values"""

    bl_idname      = "scatter5.sync_ensure"
    bl_label       = translate("Ensure Synchronization")
    bl_description = translate("Make sure that all settings from designed categories of the context members have the same values")
    bl_options     = {'INTERNAL','UNDO'}

    channel_idx : bpy.props.IntProperty()

    def execute(self, context):

        from ... __init__ import blend_prefs
        scat_data  = blend_prefs()
        scat_scene = context.scene.scatter5
        
        active_channel = scat_data.sync_channels[self.channel_idx]

        #find context psys we'll work with
        
        first = None
        others = []

        for m in active_channel.members:
            p = m.get_psy()
            if (p is None):
                continue

            #design an element we'll copy from
            if (first is None):
                first = p
                continue

            #copy from, toward others
            others.append(p)
            continue

        if ( (first is None) or (len(others)==0) ): 
            return {'FINISHED'}

        #copy/paste properties

        #REMARK: instead of manually copy/pasting we could `set(get())` 
        #to send a simply refresh singal, and the update_factory would do the job for us?
        #i did try that, and it gave me feedback loops, unsure why.
        
        with scat_scene.factory_update_pause(event=True,delay=True,sync=True):

            #for all properties
            category_list = active_channel.category_list()
            for k,v in first.bl_rna.properties.items():

                #remember, seed values 
                if (k.endswith("_seed")):
                    continue

                #only get props related to our designed categories
                if any(True for c in category_list if k.startswith(c)):

                    #we copy value of first to all others
                    value = getattr(first,k)
                    for p in others:
                        setattr(p,k,value)
                continue

        return {'FINISHED'}

#   .oooooo.   oooo
#  d8P'  `Y8b  `888
# 888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
# 888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
# 888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
# `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#  `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'


classes = (

    SCATTER5_UL_sync_channels,

    SCATTER5_PT_sync_cat_menu,
    SCATTER5_PT_sync_cat_members,

    SCATTER5_OT_sync_channels_ops,
    SCATTER5_OT_sync_members_ops,

    SCATTER5_OT_sync_ensure,

    )


