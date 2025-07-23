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
#   .oooooo.                                         88 ooooooooo.                          .                   .oooooo..o               .       .
#  d8P'  `Y8b                                       .8' `888   `Y88.                      .o8                  d8P'    `Y8             .o8     .o8
# 888           .ooooo.  oo.ooooo.  oooo    ooo    .8'   888   .d88'  .oooo.    .oooo.o .o888oo  .ooooo.       Y88bo.       .ooooo.  .o888oo .o888oo
# 888          d88' `88b  888' `88b  `88.  .8'    .8'    888ooo88P'  `P  )88b  d88(  "8   888   d88' `88b       `"Y8888o.  d88' `88b   888     888
# 888          888   888  888   888   `88..8'    .8'     888          .oP"888  `"Y88b.    888   888ooo888           `"Y88b 888ooo888   888     888
# `88b    ooo  888   888  888   888    `888'    .8'      888         d8(  888  o.  )88b   888 . 888    .o      oo     .d8P 888    .o   888 .   888 .
#  `Y8bood8P'  `Y8bod8P'  888bod8P'     .8'     88      o888o        `Y888""8o 8""888P'   "888" `Y8bod8P'      8""88888P'  `Y8bod8P'   "888"   "888"
#                         888       .o..P'
#                        o888o      `Y8P'
################################################################################################


import bpy

from . import presetting

from .. translations import translate
from .. resources.icons import cust_icon

from .. utils.import_utils import serialization 
from .. utils.event_utils import get_event
from .. utils.extra_utils import get_from_uid

from .. ui import ui_templates



#universal copy paste following settings naming system 

BUFFER_CATEGORY = {}

def is_BufferCategory_filled(buffer_category):

    global BUFFER_CATEGORY
    return buffer_category in BUFFER_CATEGORY

def clear_BufferCategory(buffer_category):

    global BUFFER_CATEGORY
    if buffer_category in BUFFER_CATEGORY:
        del BUFFER_CATEGORY[buffer_category]
    return None 

def stringify_BufferCategory(buffer_category):

    global BUFFER_CATEGORY
    return "".join([f"   {k} : {str(v)}\n" for k,v in BUFFER_CATEGORY[buffer_category].items() if not k.startswith(">") and k!="name" ])


class SCATTER5_OT_copy_paste_category(bpy.types.Operator): #Old pasteall copyall was overkill and i disable the dialog box, user can simply copy/paste per category now 

    bl_idname      = "scatter5.copy_paste_category"
    bl_label       = translate("Copy/Paste settings")
    bl_description = translate("Copy/Paste the settings of this category")
    bl_options     = {'REGISTER', 'INTERNAL'}

    single_category : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    copy : bpy.props.BoolProperty(default=False, options={"SKIP_SAVE",},)
    paste : bpy.props.BoolProperty(default=False, options={"SKIP_SAVE",},)

    @classmethod
    def description(cls, context, properties): 
        emitter = bpy.context.scene.scatter5.emitter
        if (properties.paste):
            if is_BufferCategory_filled(properties.single_category):
                  return translate("Paste the buffer content to the settings category below") +"\n"+ translate("Content of buffer") +" : \n"+ stringify_BufferCategory(properties.single_category)
            else: return translate("Paste the buffer content to the settings category below") +"\n"+ translate("The buffer is empty")
        if (properties.copy):
            return translate("Copy the settings of the category below to the buffer")
        return None 

    def execute(self, context):

        global BUFFER_CATEGORY
        scat_scene = bpy.context.scene.scatter5
        emitter    = scat_scene.emitter
        psy_active = emitter.scatter5.get_psy_active()      

        if (self.copy):
            d = presetting.settings_to_dict(psy_active, 
                use_random_seed=False, 
                texture_is_unique=False, 
                texture_random_loc=False, 
                get_scatter_density=False, 
                s_filter={self.single_category:True},
                )
            clear_BufferCategory(self.single_category)
            BUFFER_CATEGORY[self.single_category] = d 

        elif (self.paste):
            if (is_BufferCategory_filled(self.single_category)):
                d = BUFFER_CATEGORY[self.single_category]
                presetting.dict_to_settings(d, psy_active, s_filter={self.single_category:True},)
                bpy.ops.ed.undo_push(message=translate("Pasting Buffer to Settings"))
            
        return {'FINISHED'}


class SCATTER5_OT_apply_category(bpy.types.Operator):

    bl_idname      = "scatter5.apply_category"
    bl_label       = translate("Apply settings")
    bl_description = translate("Apply the settings of this category to the selected scatter-system(s)\n\nNote: This operation will batch apply all the settings of this category. If you wish to batch apply a single setting to the selected system(s), you can do so by pressing the 'ALT' key while tweaking the value of your setting")
    bl_options     = {'REGISTER', 'INTERNAL'}

    single_category : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    pop_dialog : bpy.props.BoolProperty(default=False, options={"SKIP_SAVE",},)
    apply_influence : bpy.props.EnumProperty(
        name=translate("Influence"),
        default="all",
        items=(("sel","","",),("grp","","",),("ale","","",),("ase","","",),("all","","",),),
        )

    def invoke(self, context, event):

        if (self.pop_dialog):

            _self = self
            def draw(self, context):
                nonlocal _self

                scat_scene = bpy.context.scene.scatter5
                emitter    = scat_scene.emitter
                psy_active = emitter.scatter5.get_psy_active()
                psy_group  = psy_active.get_group()
                
                layout = self.layout
                layout.label(text=translate("Apply to"))
                layout.separator()

                op = layout.operator(_self.bl_idname, text=translate("Selected System(s)")+f" [{len(emitter.scatter5.get_psys_selected(all_emitters=False))}]", )
                op.single_category = _self.single_category
                op.apply_influence = "sel"

                if (psy_group):
                    op = layout.operator(_self.bl_idname, text=translate("All System(s) of Group")+f" [{len(psy_group.get_psy_members())}]", )
                    op.single_category = _self.single_category
                    op.apply_influence = "grp"

                op = layout.operator(_self.bl_idname, text=translate("All System(s) of Emitter")+f" [{len(emitter.scatter5.particle_systems)}]", )
                op.single_category = _self.single_category
                op.apply_influence = "ale"

                op = layout.operator(_self.bl_idname, text=translate("All Selected System(s) across all Emitters")+f" [{len(emitter.scatter5.get_psys_selected(all_emitters=True))}]", )
                op.single_category = _self.single_category
                op.apply_influence = "ase"

                op = layout.operator(_self.bl_idname, text=translate("All System(s) across all Emitters")+f' [{len(scat_scene.get_all_psys(search_mode="active_view_layer"))}]', )
                op.single_category = _self.single_category
                op.apply_influence = "all"

                return None

            bpy.context.window_manager.popup_menu(draw)

            return {'FINISHED'}

        return self.execute(context)

    def execute(self, context):

        scat_scene = bpy.context.scene.scatter5
        emitter    = scat_scene.emitter
        psy_active = emitter.scatter5.get_psy_active()
        psy_group  = psy_active.get_group()

        d = presetting.settings_to_dict(psy_active,
            use_random_seed=False, 
            texture_is_unique=False, 
            texture_random_loc=False, 
            get_scatter_density=False, 
            s_filter={self.single_category:True},
            )

        match self.apply_influence:
            case 'sel': psys = emitter.scatter5.get_psys_selected(all_emitters=False)
            case 'grp': psys = psy_group.get_psy_members()
            case 'ase': psys = emitter.scatter5.get_psys_selected(all_emitters=True)
            case 'all': psys = scat_scene.get_all_psys(search_mode="active_view_layer")
            case 'ale': psys = emitter.scatter5.particle_systems[:]

        for p in psys:
            presetting.dict_to_settings(d, p, s_filter={self.single_category:True},)
            continue

        bpy.ops.ed.undo_push(message=translate("Apply Settings to System(s)"))
            
        return {'FINISHED'}

#   .oooooo.                                         88 ooooooooo.                          .                  ooooooooo.
#  d8P'  `Y8b                                       .8' `888   `Y88.                      .o8                  `888   `Y88.
# 888           .ooooo.  oo.ooooo.  oooo    ooo    .8'   888   .d88'  .oooo.    .oooo.o .o888oo  .ooooo.        888   .d88'  .oooo.o oooo    ooo
# 888          d88' `88b  888' `88b  `88.  .8'    .8'    888ooo88P'  `P  )88b  d88(  "8   888   d88' `88b       888ooo88P'  d88(  "8  `88.  .8'
# 888          888   888  888   888   `88..8'    .8'     888          .oP"888  `"Y88b.    888   888ooo888       888         `"Y88b.    `88..8'
# `88b    ooo  888   888  888   888    `888'    .8'      888         d8(  888  o.  )88b   888 . 888    .o       888         o.  )88b    `888'
#  `Y8bood8P'  `Y8bod8P'  888bod8P'     .8'     88      o888o        `Y888""8o 8""888P'   "888" `Y8bod8P'      o888o        8""888P'     .8'
#                         888       .o..P'                                                                                           .o..P'
#                        o888o      `Y8P'                                                                                            `Y8P'


BUFFER_SYSTEM = {}

def is_BufferSystems_filled():

    global BUFFER_SYSTEM

    return len(BUFFER_SYSTEM)!=0

def clear_BufferSystems():

    global BUFFER_SYSTEM
    BUFFER_SYSTEM.clear()

    return None 


class SCATTER5_OT_copy_paste_systems(bpy.types.Operator):

    bl_idname      = "scatter5.copy_paste_systems"
    bl_label       = translate("Copy/Paste selected scatter-system(s)")
    bl_description = ""
    bl_options     = {'INTERNAL', 'UNDO'}

    emitter_name : bpy.props.StringProperty()
    copy : bpy.props.BoolProperty(default=False, options={"SKIP_SAVE",},)
    paste : bpy.props.BoolProperty(default=False, options={"SKIP_SAVE",},)
    synchronize : bpy.props.BoolProperty(default=False, options={"SKIP_SAVE",},)

    @classmethod
    def description(cls, context, properties): 
        txt =""
        if (properties.copy):
            txt += translate("Copy the selected scatter-system(s)\nEasily create duplicates of your scatter-system(s) to the same, or another, emitter")
        elif (properties.paste):
            txt += translate("Paste the scatter-systems(s) currently detained in the Buffer onto the currently defined emitter object")
            txt += translate("\n• Note: you might want to change the seed of the distribution after this operation, as the duplicated scatter's instances might overlap with the original instances.")
        if (properties.synchronize):
              txt += translate("\n• Note: With the synchronization option we will set up a synchronization channel with the original scatter-settings. Meaning that every setting will be synchronized with the original scatter and vice-versa")
        return txt

    def execute(self, context):

        from ... __init__ import blend_prefs
        scat_data  = blend_prefs()
        scat_scene = bpy.context.scene.scatter5
        
        emitter = bpy.data.objects.get(self.emitter_name)
        if (emitter is None): 
            return {'FINISHED'}

        global BUFFER_SYSTEM

        if (self.copy):

            clear_BufferSystems()

            for p in emitter.scatter5.get_psys_selected():

                d = presetting.settings_to_dict(p,
                    use_random_seed=False,
                    texture_is_unique=False,
                    texture_random_loc=False,
                    get_scatter_density=False,
                    s_filter={ k:True for k in ("s_color","s_surface","s_distribution","s_mask","s_rot","s_scale","s_pattern","s_push","s_abiotic","s_proximity","s_ecosystem","s_wind","s_visibility","s_instances","s_display")}, #all settings cat are True
                    )

                #need to add extra information for instances, unfortunately instances names are not passed in presets... #TODO add kw argument for this option?
                d[">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> BUFFER_EXTRA"] = ""
                d["initial_instances"] = [o.name for o in p.s_instances_coll_ptr.objects]
                d["is_linked"] = p.is_linked
                d["initial_scatter_obj_session_uid"] = p.scatter_obj.session_uid
                
                #add dict to buffer
                initial_name = p.name
                BUFFER_SYSTEM[initial_name]= d

                continue

        elif (self.paste):

            if is_BufferSystems_filled():

                bpy.ops.scatter5.toggle_selection(deselect=True, emitter_name=emitter.name,)

                for initial_name, d in BUFFER_SYSTEM.items():

                    #create a new psy with same instances
                    p = emitter.scatter5.add_psy_virgin(
                        psy_name=f"{initial_name} 🗗",
                        instances=[ bpy.data.objects.get(n) for n in d["initial_instances"] if (n in bpy.data.objects) ],
                        )
                    p.sel = True
                    p.hide_viewport = True

                    #TODO: what do we do if user copy/paste ecosystem ptr too? ugh need to re-evaluate

                    #apply same settings of initial_p to newly added psy
                    presetting.dict_to_settings(d, p,
                        s_filter={ k:True for k in ("s_color","s_surface","s_distribution","s_mask","s_rot","s_scale","s_pattern","s_push","s_abiotic","s_proximity","s_ecosystem","s_wind","s_visibility","s_instances","s_display")}, #all settings cat are True
                        )
                    
                    #copy obj data? make sure scat_obj was found, and that it's not a linked asset. otherwise we won't be able to do the operation
                    if (not d["is_linked"]):
                        initial_scat_obj = get_from_uid(d["initial_scatter_obj_session_uid"])
                        if ((initial_scat_obj is not None) and (not bool(initial_scat_obj.library))):
                            from .. utils.create_utils import add_objdata_a_to_b
                            add_objdata_a_to_b(a=initial_scat_obj,b=p.scatter_obj,)

                    #synchronize? only if initial psy still exists
                    if (self.synchronize):

                        #find back our initial psy, from which we pasted the data
                        initial_p = scat_scene.get_psy_by_name(initial_name)
                        if (initial_p is None):
                            continue

                        #enable synchronization, will not be enabled by default
                        if (not scat_data.factory_synchronization_allow):
                            scat_data.factory_synchronization_allow = True 

                        #create new channel if needed
                        ch = scat_data.sync_channels.get(initial_name)
                        if (ch is None):
                              ch = scat_data.sync_channels.add()
                              ch.name = initial_name

                        #add the psys as members
                        ch.add_psys_members(initial_p, p)

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

    SCATTER5_OT_copy_paste_category,
    SCATTER5_OT_apply_category,
    SCATTER5_OT_copy_paste_systems,
    
    )
