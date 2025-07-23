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

#####################################################################################################
#
#       .o.             .o8        .o8       ooooooooo.
#      .888.           "888       "888       `888   `Y88.
#     .8"888.      .oooo888   .oooo888        888   .d88'  .oooo.o oooo    ooo
#    .8' `888.    d88' `888  d88' `888        888ooo88P'  d88(  "8  `88.  .8'
#   .88ooo8888.   888   888  888   888        888         `"Y88b.    `88..8'
#  .8'     `888.  888   888  888   888        888         o.  )88b    `888'
# o88o     o8888o `Y8bod88P" `Y8bod88P"      o888o        8""888P'     .8'
#                                                                  .o..P'
#                                                                  `Y8P'
#####################################################################################################

import bpy

import os, time, random
from mathutils import Vector

from .. resources.icons import cust_icon
from .. translations import translate
from .. resources import directories

from .. utils.import_utils import import_selected_assets
from .. utils.path_utils import json_to_dict
from .. utils.event_utils import get_mouse_context
from .. utils.override_utils import get_any_view3d_region

from . import presetting

from . instances import find_compatible_instances
from . emitter import get_compatible_surfaces_for_scatter

from .. ui.ui_creation import find_preset_name

from .. widgets.infobox import SC5InfoBox, generic_infobox_setup
from .. utils.draw_utils import add_font, clear_all_fonts


"""
Important info:

-ScatterDensity/ScatterPreset/ScatterManual/ScatterBiomes operators use their own scat_scene.operators settings
 see in ops_settings.py: 
    - scat_ops.create_operators
    - scat_ops.add_psy_preset
    - scat_ops.add_psy_density
    - scat_ops.add_psy_manual
    - scat_ops.add_psy_modal
    - scat_ops.load_biome

-ScatterDensity & ScatterBiomes are derrivate of ScatterPreset operator

-Structure Graph: 

          ┌──────────────────┐
          │ add_psy_virgin() │        #REMARK: we could use some class inheritence in there? maybe?
          └─┬─────┬───────┬──┘
            │     │       │
            │     │       │ ┌──────────────┐-> security features
┌───────────▼──┐  │       └─►add_psy_preset│-> complete visibility & display
│add_psy_simple│  │         └─┬────────────┘-> special mask assignation
└──────────────┘  │           │             
     ┌────────────▼─┐         │ ┌───────────────┐
     │add_psy_manual│         ├─►add_psy_density│
     └───▲──────────┘         │ └───────────────┘
         !                    │
         !                    │ ┌─────────────────┐
         !                    ├─►add_biome_layer()│
         !                    │ └─┬───────────────┘
         !  ┌─────────────┐   │   │
         !  │add_psy_modal◄───┘   │ ┌─────────┐
         !  └───▲─────────┘       ├─►add_biome│ for scripts
         !      !                 │ └─────────┘
         !      !                 │
     ┌---┴------┴--------┐        │ ┌──────────┐
     |  define_add_psy   |        └─►load_biome│ for ux/ui
     └-------------------┘          └──────────┘
                                  

"""

# oooooooooooo               .
# `888'     `8             .o8
#  888          .ooooo.  .o888oo
#  888oooo8    d88' `"Y8   888
#  888    "    888         888
#  888         888   .o8   888 .
# o888o        `Y8bod8P'   "888"

#REMARK: we could use some class inheritence instead of functions in there? maybe?

def utils_find_args(context, emitter_name="", surfaces_names="", instances_names="", selection_mode="viewport", psy_name="default", psy_color=(1,1,1,1), psy_color_random=False, pop_msg=True,):
    """utility function to define emitter, surfaces, instances, psy name&color quickly"""

    from ... __init__ import blend_prefs
    scat_data  = blend_prefs()
    scat_scene = context.scene.scatter5

    #Get Emitter

    emitter = bpy.data.objects.get(emitter_name)
    if (emitter is None):
        emitter = scat_scene.emitter
        
    if (emitter is None):
        if (pop_msg):
            msg = translate("\nNo emitter found.\n")
            bpy.ops.scatter5.popup_menu(msgs=msg, title=translate("Action Failed"),icon="ERROR",)
        print("ERROR: utils_find_args(): No emitter found")
        return {'FINISHED'}

    #Get Surfaces (from given names passed)

    l = [ bpy.data.objects[n] for n in surfaces_names.split("_!#!_") if n in context.scene.objects ]
    surfaces = list(get_compatible_surfaces_for_scatter(l))
    
    #no surfaces found? 
    if (len(surfaces)==0):
        if (pop_msg):
            msg = translate("\nNo valid surface(s) found.\nPlease define your surfaces in the operator 'On Creation' menu.\n")
            bpy.ops.scatter5.popup_menu(msgs=msg, title=translate("Action Failed"),icon="ERROR",)
        print("ERROR: utils_find_args(): No surfaces found")
        return {'FINISHED'}

    #Get Instances (either passedor found in selection of asset browser / 3D viewport selection)
    if (instances_names==""):
        match selection_mode:
            case 'browser':  l = import_selected_assets(link=(scat_data.objects_import_method=='LINK'),)
            case 'viewport': l = [o for o in bpy.context.selected_objects if (o.type=='MESH')]
    else:
        l = [bpy.data.objects[n] for n in instances_names.split("_!#!_") if (n in bpy.data.objects)]
    
    #find compatible instances in there
    instances = list(find_compatible_instances(l, emitter=emitter,))
    
    #no instances found?
    if (len(instances)==0):
        if (pop_msg):
            match selection_mode:
                case 'viewport':
                    msg = translate("\nNo valid object(s) found in selection.\n\nPlease select the object(s) you want to Scatter in the viewport.\n")
                case 'browser':
                    if (not bpy.context.window):
                        print("WARNING: utils_find_args(): No support for this operator in blender headless-mode, it relies on window selection")
                    else:
                        browsers_found = [a for w in bpy.context.window_manager.windows for a in w.screen.areas if (a.ui_type=='ASSETS')]
                        if (len(browsers_found)==0):
                              msg = translate("\nNo Asset-Browser Editor Found.\n\nThis selection-method works with the blender asset browser, please open one.\n")
                        else: msg = translate("\nNo Asset(s) Selected.\n\nPlease select some assets in yout asset browser.\n")
            #popup error message
            bpy.ops.scatter5.popup_menu(msgs=msg, title=translate("Action Failed"),icon="ERROR",)
        print("ERROR: utils_find_args(): No instances found")
        return {'FINISHED'}

    #Set Color & name 

    #Give default name is name is empty
    if (psy_name in (""," ","  ","   ","    ")):
        psy_name = "No Name"
        
    #support for automatic name finding
    if (psy_name=="*AUTO*"):
        psy_name = find_preset_name(instances) #auto color is done at ui level
        
    #random color
    if (psy_color_random):
        psy_color = [random.uniform(0,1),random.uniform(0,1),random.uniform(0,1),1]

    return psy_name, psy_color, emitter, surfaces, instances



#################################################################################################################################
#
#   .oooooo.                                    .    o8o                               .oooooo.
#  d8P'  `Y8b                                 .o8    `"'                              d8P'  `Y8b
# 888          oooo d8b  .ooooo.   .oooo.   .o888oo oooo   .ooooo.  ooo. .oo.        888      888 oo.ooooo.   .oooo.o
# 888          `888""8P d88' `88b `P  )88b    888   `888  d88' `88b `888P"Y88b       888      888  888' `88b d88(  "8
# 888           888     888ooo888  .oP"888    888    888  888   888  888   888       888      888  888   888 `"Y88b.
# `88b    ooo   888     888    .o d8(  888    888 .  888  888   888  888   888       `88b    d88'  888   888 o.  )88b
#  `Y8bood8P'  d888b    `Y8bod8P' `Y888""8o   "888" o888o `Y8bod8P' o888o o888o       `Y8bood8P'   888bod8P' 8""888P'
#                                                                                                  888
#                                                                                                 o888o
#################################################################################################################################


#  .oooooo..o  o8o                               oooo                  .oooooo..o                         .       .
# d8P'    `Y8  `"'                               `888                 d8P'    `Y8                       .o8     .o8
# Y88bo.      oooo  ooo. .oo.  .oo.   oo.ooooo.   888   .ooooo.       Y88bo.       .ooooo.   .oooo.   .o888oo .o888oo  .ooooo.  oooo d8b
#  `"Y8888o.  `888  `888P"Y88bP"Y88b   888' `88b  888  d88' `88b       `"Y8888o.  d88' `"Y8 `P  )88b    888     888   d88' `88b `888""8P
#      `"Y88b  888   888   888   888   888   888  888  888ooo888           `"Y88b 888        .oP"888    888     888   888ooo888  888
# oo     .d8P  888   888   888   888   888   888  888  888    .o      oo     .d8P 888   .o8 d8(  888    888 .   888 . 888    .o  888
# 8""88888P'  o888o o888o o888o o888o  888bod8P' o888o `Y8bod8P'      8""88888P'  `Y8bod8P' `Y888""8o   "888"   "888" `Y8bod8P' d888b
#                                      888
#                                     o888o


class SCATTER5_OT_add_psy_simple(bpy.types.Operator):

    bl_idname      = "scatter5.add_psy_simple"
    bl_label       = translate("Add Scatter-System")
    bl_description = translate("• By default, the operator will add a simple scatter-system with the selected 3D viewport object(s) as instances, it will use the emitter-object as scatter surface.\n•If the 'ALT' key is pressed while clicking on the add button, this operator will add a default scatter-system with the selected 3D viewport object(s) as scatter surface(s), but no instances will be defined, therefore we'll enable the “Tweak>Display>Display As” option. Feel free to define instances afterward in the “Tweak>Instances” feature")
    bl_options     = {'INTERNAL','UNDO'}

    emitter_name : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    surfaces_names : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    instances_names : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},) 

    psy_name : bpy.props.StringProperty(default="Default", options={"SKIP_SAVE",},)
    psy_color : bpy.props.FloatVectorProperty(size=4, default=(1,1,1,1), options={"SKIP_SAVE",},)
    psy_color_random : bpy.props.BoolProperty(default=False, options={"SKIP_SAVE",},)
    
    def invoke(self, context, event):

        #Get Emitter
        self.emitter = bpy.data.objects.get(self.emitter_name)
        if (self.emitter is None):
            self.emitter = context.scene.scatter5.emitter

        #Correct if no name or empty name
        if (self.psy_name in [""," ","  ","   ","    "]): #meh
            self.psy_name = "No Name"

        #Get Color 
        if (self.psy_color_random):
            self.psy_color = [random.uniform(0,1),random.uniform(0,1),random.uniform(0,1),1]

        #Alt workflow
        if (event.alt):

            #Get Surfaces
            if (self.surfaces_names):
                  self.surfaces = [ bpy.data.objects[n] for n in self.surfaces_names.split("_!#!_") if n in bpy.data.objects ]
            else: self.surfaces = []
            self.instances = []

        #Standard behavior
        else: 
            #Get instances
            if (self.instances_names):
                  obj_list = [ bpy.data.objects[n] for n in self.instances_names.split("_!#!_") if n in bpy.data.objects ]
            else: obj_list = []
            self.instances = list(find_compatible_instances(obj_list, emitter=self.emitter,))
            self.surfaces = []

        return self.execute(context) 

    def execute(self, context):

        emitter = self.emitter
        if (emitter is None):
            return {'FINISHED'}

        #ignore any properties update behavior, such as update delay or hotkeys
        with bpy.context.scene.scatter5.factory_update_pause(event=True,delay=True,sync=True):

            #create virgin psy
            p = emitter.scatter5.add_psy_virgin(
                psy_name=self.psy_name,
                psy_color=self.psy_color,
                deselect_all=True,
                instances=self.instances,
                surfaces=self.surfaces,
                )

            #display as point?
            if (len(self.instances)==0):
                p.s_display_allow = True
                p.s_display_method = "point"

            p.s_distribution_density = 0.222
            p.s_distribution_is_random_seed = True
            p.hide_viewport = False

        return {'FINISHED'}


# ooooooooo.                                             .         .oooooo..o                         .       .
# `888   `Y88.                                         .o8        d8P'    `Y8                       .o8     .o8
#  888   .d88' oooo d8b  .ooooo.   .oooo.o  .ooooo.  .o888oo      Y88bo.       .ooooo.   .oooo.   .o888oo .o888oo  .ooooo.  oooo d8b
#  888ooo88P'  `888""8P d88' `88b d88(  "8 d88' `88b   888         `"Y8888o.  d88' `"Y8 `P  )88b    888     888   d88' `88b `888""8P
#  888          888     888ooo888 `"Y88b.  888ooo888   888             `"Y88b 888        .oP"888    888     888   888ooo888  888
#  888          888     888    .o o.  )88b 888    .o   888 .      oo     .d8P 888   .o8 d8(  888    888 .   888 . 888    .o  888
# o888o        d888b    `Y8bod8P' 8""888P' `Y8bod8P'   "888"      8""88888P'  `Y8bod8P' `Y888""8o   "888"   "888" `Y8bod8P' d888b


#Example

# bpy.ops.scatter5.add_psy_preset(
#     psy_name="New Psy Test",
#     psy_color = (1,1,1,1),
#     psy_color_random= False,
#     emitter_name="Plane",
#     selection_mode="viewport",
#     instances_names="Instance Cube_!#!_Suzanne_!#!_Cube",
#     json_path="C:/Users/Dude/Desktop/testing.json",
#     )


class SCATTER5_OT_add_psy_preset(bpy.types.Operator):
    """main scattering operator for user in 'Creation>Scatter' if running this from script, note that there are a few globals parameters that could have an influence over this operation, such as the security features"""

    #this operator parameters are automatically configuired in the ui_creation interface

    bl_idname      = "scatter5.add_psy_preset"
    bl_label       = translate("Preset Scatter")
    bl_description = translate("Scatter the selected items with the active preset")
    bl_options     = {'INTERNAL','UNDO'}

    emitter_name : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    surfaces_names : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    instances_names : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    default_group : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    selection_mode : bpy.props.StringProperty(default="viewport", options={"SKIP_SAVE",},) #"browser"/"viewport"
    
    psy_name : bpy.props.StringProperty(default="NewPsy", options={"SKIP_SAVE",},) #use "*AUTO*" to automatically find name and color
    psy_color : bpy.props.FloatVectorProperty(size=4, default=(1,1,1,1), options={"SKIP_SAVE",},)
    psy_color_random : bpy.props.BoolProperty(default=False, options={"SKIP_SAVE",},)

    json_path : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},) #string = json preset path, if not will use active preset
    settings_override : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},) #set settings via text format "propname:value_override,next_prop:next_override"

    ctxt_operator : bpy.props.StringProperty(default="add_psy_preset", options={"SKIP_SAVE",},) #Name of the operator for getting the scat_scene.operators.operator_name settings 

    pop_msg : bpy.props.BoolProperty(default=True, options={"SKIP_SAVE",},)

    def execute(self, context):

        scat_scene   = context.scene.scatter5
        scat_ops     = scat_scene.operators
        scat_op      = getattr(scat_ops, self.ctxt_operator)
        scat_op_crea = scat_ops.create_operators

        r = utils_find_args(context,
            pop_msg=self.pop_msg,
            emitter_name=self.emitter_name,
            surfaces_names=self.surfaces_names,
            instances_names=self.instances_names,
            selection_mode=self.selection_mode,
            psy_name=self.psy_name,
            psy_color=self.psy_color,
            psy_color_random=self.psy_color_random,
            )

        if (r=={'FINISHED'}):
            return {'FINISHED'}

        self.psy_name, self.psy_color, emitter, surfaces, instances = r

        #ignore any properties update behavior, such as update delay or hotkeys
        with scat_scene.factory_update_pause(event=True,delay=True,sync=True):

            #create virgin psy
            p = emitter.scatter5.add_psy_virgin(
                psy_name=self.psy_name,
                psy_color=self.psy_color,
                deselect_all=True,
                instances=instances,
                surfaces=surfaces,
                default_group=self.default_group,
                )

            #load json preset to settings
            d = {}

            #user don't want to apply any preset ? if so use default ""
            if (self.json_path==""):
                pass

            #if preset not exists, inform user
            elif (not os.path.exists(self.json_path)):
                if (self.pop_msg):
                    bpy.ops.scatter5.popup_menu(msgs=translate("The preset you are using is not valid")+f"\n {self.json_path}", title=translate("Warning"),icon="ERROR",)

            #paste preset to settings
            else:
                d = json_to_dict(
                    path=os.path.dirname(self.json_path),
                    file_name=os.path.basename(self.json_path),
                    )
                presetting.dict_to_settings( d, p,) #default "s_filter" argument, should be fit for basic preset usage, aka no s_surface,s_mask,s_visibility,s_display

                #refresh ecosystem dependencies?
                for ps in emitter.scatter5.particle_systems:
                    if (ps!=p):
                        if (ps.s_ecosystem_affinity_allow):
                            for i in (1,2,3):
                                if (getattr(ps,f"s_ecosystem_affinity_{i:02}_ptr")==p.name):
                                    setattr(ps,f"s_ecosystem_affinity_{i:02}_ptr",p.name)
                        if (ps.s_ecosystem_repulsion_allow):
                            for i in (1,2,3):
                                if (getattr(ps,f"s_ecosystem_repulsion_{i:02}_ptr")==p.name):
                                    setattr(ps,f"s_ecosystem_repulsion_{i:02}_ptr",p.name)

            #Settings override via text?
            if (self.settings_override!=""):
                for prop_value in self.settings_override.split(","):
                    prop,value = prop_value.split(":")
                    if (hasattr(p,prop)):
                        setattr(p,prop,eval(value))

            #now need to evaluate f_display/f_visibility/f_mask & f_security settings on this psy
            scat_op.set_psy_context_f_actions(context, p=p, d=d, surfaces=surfaces, instances=instances, pop_msg=self.pop_msg,)

        return {'FINISHED'}


# oooooooooo.                                   o8o      .                     .oooooo..o                         .       .
# `888'   `Y8b                                  `"'    .o8                    d8P'    `Y8                       .o8     .o8
#  888      888  .ooooo.  ooo. .oo.    .oooo.o oooo  .o888oo oooo    ooo      Y88bo.       .ooooo.   .oooo.   .o888oo .o888oo  .ooooo.  oooo d8b
#  888      888 d88' `88b `888P"Y88b  d88(  "8 `888    888    `88.  .8'        `"Y8888o.  d88' `"Y8 `P  )88b    888     888   d88' `88b `888""8P
#  888      888 888ooo888  888   888  `"Y88b.   888    888     `88..8'             `"Y88b 888        .oP"888    888     888   888ooo888  888
#  888     d88' 888    .o  888   888  o.  )88b  888    888 .    `888'         oo     .d8P 888   .o8 d8(  888    888 .   888 . 888    .o  888
# o888bood8P'   `Y8bod8P' o888o o888o 8""888P' o888o   "888"     .8'          8""88888P'  `Y8bod8P' `Y888""8o   "888"   "888" `Y8bod8P' d888b
#                                                            .o..P'
#                                                            `Y8P'

class SCATTER5_OT_add_psy_density(bpy.types.Operator):
    """running add_psy_preset w/o using presets and overriding with own density & default settings"""

    bl_idname      = "scatter5.add_psy_density"
    bl_label       = translate("Density Scatter")
    bl_description = translate("Scatter the selected items with the chosen density value")
    bl_options     = {'INTERNAL','UNDO'}
    
    emitter_name : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    surfaces_names : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    instances_names : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    selection_mode : bpy.props.StringProperty(default="viewport", options={"SKIP_SAVE",},) #"browser"/"viewport"

    psy_name : bpy.props.StringProperty(default="DensityScatter")
    psy_color : bpy.props.FloatVectorProperty(size=4, default=(0.220, 0.215, 0.200, 1), options={"SKIP_SAVE",},)
    psy_color_random : bpy.props.BoolProperty(default=False, options={"SKIP_SAVE",},)

    density_value : bpy.props.FloatProperty(default=10.0, options={"SKIP_SAVE",},)
    density_scale : bpy.props.StringProperty(default="m", options={"SKIP_SAVE",},)

    pop_msg : bpy.props.BoolProperty(default=True, options={"SKIP_SAVE",},)

    def execute(self, context):

        #adjust density depending on scale
        match self.density_scale:
            case 'm':  pass
            case 'cm': self.density_value*=10_000
            case 'ha': self.density_value*=0.0001
            case 'km': self.density_value*=0.000001
            case str():
                raise Exception(f"ERROR: SCATTER5_OT_add_psy_density: value {self.density_scale} not in 'm|cm|ha|km")

        #override settings, instead of dumping a .preset text file, there's the option to feed a string containing props instruction, directly like this
        d = f"s_distribution_density:{self.density_value},s_distribution_is_random_seed:True,s_rot_align_z_allow:True,s_rot_align_y_allow:True,s_rot_align_y_method:'meth_align_y_random'"

        bpy.ops.scatter5.add_psy_preset(
            emitter_name=self.emitter_name,
            surfaces_names=self.surfaces_names,
            selection_mode=self.selection_mode,
            instances_names=self.instances_names,
            psy_name=self.psy_name,
            psy_color=self.psy_color,
            psy_color_random=self.psy_color_random,
            ctxt_operator="add_psy_density", #using the f_visibility/f_display/f_mask ect.. of this ctxt_operator
            settings_override=d, #dont use  json path, use settings override instead
            pop_msg=self.pop_msg,
            )

        return {'FINISHED'}



# ooo        ooooo                                             oooo        .oooooo..o                         .       .
# `88.       .888'                                             `888       d8P'    `Y8                       .o8     .o8
#  888b     d'888   .oooo.   ooo. .oo.   oooo  oooo   .oooo.    888       Y88bo.       .ooooo.   .oooo.   .o888oo .o888oo  .ooooo.  oooo d8b
#  8 Y88. .P  888  `P  )88b  `888P"Y88b  `888  `888  `P  )88b   888        `"Y8888o.  d88' `"Y8 `P  )88b    888     888   d88' `88b `888""8P
#  8  `888'   888   .oP"888   888   888   888   888   .oP"888   888            `"Y88b 888        .oP"888    888     888   888ooo888  888
#  8    Y     888  d8(  888   888   888   888   888  d8(  888   888       oo     .d8P 888   .o8 d8(  888    888 .   888 . 888    .o  888
# o8o        o888o `Y888""8o o888o o888o  `V88V"V8P' `Y888""8o o888o      8""88888P'  `Y8bod8P' `Y888""8o   "888"   "888" `Y8bod8P' d888b


ADDMANUAL_OVERRIDES = {} 

class SCATTER5_OT_add_psy_manual(bpy.types.Operator):

    bl_idname      = "scatter5.add_psy_manual"
    bl_label       = translate("Manual Scatter")
    bl_description = translate("Add a new empty Scatter-System set on manual-distribution and directly enter the manual distribution workflow")
    bl_options     = {'INTERNAL','UNDO'}

    emitter_name : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    surfaces_names : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    instances_names : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    selection_mode : bpy.props.StringProperty(default="viewport", options={"SKIP_SAVE",},)
    
    psy_name : bpy.props.StringProperty(default="ManualScatter", options={"SKIP_SAVE",},)
    psy_color : bpy.props.FloatVectorProperty(size=4, default=(0.495, 0.484, 0.449, 1), options={"SKIP_SAVE",},)
    psy_color_random : bpy.props.BoolProperty(default=False, options={"SKIP_SAVE",},)
    
    pop_msg : bpy.props.BoolProperty(default=True, options={"SKIP_SAVE",},)

    def execute(self, context):

        scat_scene   = context.scene.scatter5
        scat_ops     = scat_scene.operators
        scat_op      = scat_ops.add_psy_manual
        scat_op_crea = scat_ops.create_operators
        
        r = utils_find_args(context,
            pop_msg=self.pop_msg,
            emitter_name=self.emitter_name,
            surfaces_names=self.surfaces_names,
            instances_names=self.instances_names,
            selection_mode=self.selection_mode,
            psy_name=self.psy_name,
            psy_color=self.psy_color,
            psy_color_random=self.psy_color_random,
            )

        if (r=={'FINISHED'}):
            return {'FINISHED'}

        self.psy_name, self.psy_color, emitter, surfaces, instances = r

        #create virgin psy & set to manual distribution

        p = emitter.scatter5.add_psy_virgin(
            psy_name=self.psy_name,
            psy_color=self.psy_color,
            deselect_all=True,
            instances=instances,
            surfaces=surfaces,
            )

        p.s_distribution_method = "manual_all"
        p.s_rot_random_allow = scat_op.f_rot_random_allow
        p.s_scale_random_allow = scat_op.f_scale_random_allow

        #now need to evaluate f_display,f_sec ect..
        scat_op.set_psy_context_f_actions(context, p=p, surfaces=surfaces, instances=instances, pop_msg=self.pop_msg,)

        #force unhide psy
        p.hide_viewport = False

        #override in case if user is calling this operator `from scatter5.define_add_psy`
        global ADDMANUAL_OVERRIDES
        if (ADDMANUAL_OVERRIDES):
            with context.temp_override(window=ADDMANUAL_OVERRIDES["window"],area=ADDMANUAL_OVERRIDES["area"],region=ADDMANUAL_OVERRIDES["region"]):
                bpy.ops.scatter5.manual_enter('INVOKE_DEFAULT',)
            ADDMANUAL_OVERRIDES = {}
        else: 
            bpy.ops.scatter5.manual_enter('INVOKE_DEFAULT')

        return {'FINISHED'}

#   .oooooo.                   o8o            oooo              .oooooo..o                         .       .
#  d8P'  `Y8b                  `"'            `888             d8P'    `Y8                       .o8     .o8
# 888      888    oooo  oooo  oooo   .ooooo.   888  oooo       Y88bo.       .ooooo.   .oooo.   .o888oo .o888oo  .ooooo.  oooo d8b
# 888      888    `888  `888  `888  d88' `"Y8  888 .8P'         `"Y8888o.  d88' `"Y8 `P  )88b    888     888   d88' `88b `888""8P
# 888      888     888   888   888  888        888888.              `"Y88b 888        .oP"888    888     888   888ooo888  888
# `88b    d88b     888   888   888  888   .o8  888 `88b.       oo     .d8P 888   .o8 d8(  888    888 .   888 . 888    .o  888
#  `Y8bood8P'Ybd'  `V88V"V8P' o888o `Y8bod8P' o888o o888o      8""88888P'  `Y8bod8P' `Y888""8o   "888"   "888" `Y8bod8P' d888b


class SCATTER5_OT_define_add_psy(bpy.types.Operator):
    """define dynamic selection for surfaces or instances, 
    here only used for the add_psy_modal operator"""

    bl_idname      = "scatter5.define_add_psy"
    bl_label       = translate("Quick Scatter")
    bl_description = translate("Call the Quick-Scatter pie menu")

    operation_type : bpy.props.StringProperty(default="", options={"SKIP_SAVE","HIDDEN"},)
    description : bpy.props.StringProperty(default="", options={"SKIP_SAVE","HIDDEN"},)

    @classmethod
    def description(cls, context, properties): 
        return properties.description

    @classmethod
    def poll(cls,context,):
        if (context.mode!="OBJECT"):
            return False
        if (context.area.type not in ('VIEW_3D','FILE_BROWSER',)):
            return False
        if (context.scene.scatter5.emitter is None):
            return False
        return True

    def invoke(self, context, event):

        self.areatype = context.area.type
        
        match self.areatype:
            case 'VIEW_3D':
                self.areaicon, self.areamode = "VIEW3D", "viewport"
            case 'FILE_BROWSER':
                self.areaicon, self.areamode = "ASSET_MANAGER", "browser"

        match self.operation_type:
            
            case 'vg'|'bitmap'|'standard'|'curve'|'draw'|'manual':
                #if we passed an operator type, then we simply pass to execution
                self.execute(context)

            case '':
                #if we didn't pass anything, then we draw pie menu, user need to define his operation type
                def draw(self, context):

                    scat_scene   = bpy.context.scene.scatter5
                    scat_ops     = scat_scene.operators
                    scat_op_crea = scat_ops.create_operators

                    layout = self.layout
                    pie = layout.menu_pie()

                    #left
                    op = pie.operator("scatter5.define_add_psy", text=translate("Manual Scatter"), icon="BRUSHES_ALL",)
                    op.operation_type = 'manual'
                    op.description = translate("Directly enter manual mode with the selected objects/assets as future instances")
                    
                    #right
                    op = pie.operator("scatter5.define_add_psy", text="..."+translate("Vgroup Mask"), icon="TEMP",)
                    op.operation_type = 'vg'
                    op.description = translate("Directly scatter in a modal mode, while vertex-painting, with the selected objects/assets as future instances")
                        
                    #low
                    
                    col = pie.column()
                    col.scale_x = 1.1
                    
                    #similar code on ui_menus.creation_operators_draw_surfaces()

                    surfcol = col.column(align=True)
                    surfcol.label(text=translate("Future Surface(s):"))

                    lis = surfcol.box().column(align=True)
                    lis.scale_y = 0.85

                    for i,o in enumerate(scat_op_crea.get_f_surfaces()): 
                        if (o.name!=""):
                            lisr = lis.row()
                            lisr.label(text=o.name)

                            # #remove given object #Too slow, will quit automatically
                            # op = lisr.operator("scatter5.exec_line", text="", icon="TRASH", emboss=False,)
                            # op.api = f"scat_ops.create_operators.f_surfaces[{i}].object = None ; scat_ops.create_operators.f_surfaces.remove({i})"
                            # op.undo = translate("Remove Predefined Surface(s)")

                    if ("lisr" not in locals()):
                        lisr = lis.row()
                        lisr.label(text=translate("No Surface(s) Assigned"))

                    op = surfcol.operator("scatter5.exec_line", text = translate("Use Selection"), icon="ADD",)
                    op.api = f"scat_op_crea.f_surface_method = 'collection' ; scat_op_crea.f_surfaces.clear() ; scat_op_crea.add_selection()"
                    op.description = translate("Redefine the viewport selected-objects as your future scatter-surface(s)")

                    #top
                    op = pie.operator("scatter5.define_add_psy", text = "..."+translate("Image Mask"), icon="TEMP",)
                    op.operation_type = 'bitmap'
                    op.description = translate("Directly scatter in a modal mode, while image painting, with the selected objects/assets as your future instances")
                    
                    #top left
                    op = pie.operator("scatter5.define_add_psy", text = translate("Modal Scatter"), icon="TEMP",)
                    op.operation_type = 'standard'
                    op.description = translate("Directly scatter in a modal mode, with the selected objects/assets as your future instances")
                    
                    #top right
                    op = pie.operator("scatter5.define_add_psy", text = "..."+translate("Bezier-Area"), icon="TEMP",)
                    op.operation_type = 'curve'
                    op.description = translate("Directly scatter in a modal mode, while drawing a bezier-area distribution, with the selected objects/assets as your future instances")
                    
                    #low left
                    pie.separator()
                        
                    #low right
                    op = pie.operator("scatter5.define_add_psy", text = "..."+translate("Bezier-Spline"), icon="TEMP",)
                    op.operation_type = 'draw'
                    op.description = translate("Directly scatter in a modal mode, while drawing a bezier-spline distribution, with the selected objects/assets as your future instances")

                    return None 

                bpy.context.window_manager.popup_menu_pie(event, draw, title=translate("Quick Scatter"), icon=self.areaicon,)

            case _:
                raise Exception("ERROR: SCATTER5_OT_define_add_psy: operation_type must be in ''|'vg'|'bitmap'|'standard'|'curve'|'manual'")
                
        return {'FINISHED'}

    def execute(self,context,):

        from ... __init__ import blend_prefs
        scat_data    = blend_prefs()
        scat_scene   = bpy.context.scene.scatter5
        emitter      = scat_scene.emitter
        scat_ops     = scat_scene.operators
        scat_op_crea = scat_ops.create_operators

        #Get Surfaces from operator settings

        l = scat_op_crea.get_f_surfaces()
        surfaces = list(get_compatible_surfaces_for_scatter(l))

        #no surfaces found? 
        if (len(surfaces)==0):
            msg = translate("\nNo valid surface(s) found.\nPlease define your surfaces in the operator 'On Creation' menu.\n")
            bpy.ops.scatter5.popup_menu(msgs=msg, title=translate("Action Failed"),icon="ERROR",)
            return {'FINISHED'}

        #Get Instances (either find selection in asset browser or selection)
        match self.areamode:
            case 'browser':  l = import_selected_assets(link=(scat_data.objects_import_method=="LINK"),)
            case 'viewport': l = [ o for o in bpy.context.selected_objects ]
        instances = list(find_compatible_instances(l, emitter=emitter,))
        
        #no instances found?
        if (len(instances)==0):
            match self.areamode:
                case 'viewport':
                    msg = translate("\nNo valid object(s) found in selection.\n\nPlease select the object(s) you want to Scatter in the viewport.\n")
                case 'browser':
                    if (not bpy.context.window):
                        print("WARNING: SCATTER5_OT_define_add_psy: No support for this operator in blender headless-mode, it relies on window selection")
                    else:
                        browsers_found = [a for w in bpy.context.window_manager.windows for a in w.screen.areas if (a.ui_type=='ASSETS')]
                        if (len(browsers_found)==0):
                              msg = translate("\nNo Asset-Browser Editor Found.\n\nThis selection-method works with the blender asset browser, please open one.\n")
                        else: msg = translate("\nNo Asset(s) Selected.\n\nPlease select some assets in yout asset browser.\n")
            #popup error message
            bpy.ops.scatter5.popup_menu(msgs=msg, title=translate("Action Failed"),icon="ERROR",)
            return {'FINISHED'}

        #Launch operators, find args and potential override if context not in 3dviewport

        match self.operation_type:
            
            case 'vg'|'bitmap'|'standard'|'curve'|'draw':
                scat_operator = bpy.ops.scatter5.add_psy_modal
                op_ctxt_item = 'INVOKE_DEFAULT'
                op_kwargs = {
                    "emitter_name":emitter.name,
                    "surfaces_names":"_!#!_".join(o.name for o in surfaces),
                    "instances_names":"_!#!_".join(o.name for o in instances),
                    "default_startup":self.operation_type.replace('standard',''),
                    }

            case 'manual':
                scat_operator = bpy.ops.scatter5.add_psy_manual
                op_ctxt_item = 'EXEC_DEFAULT'
                op_kwargs = {
                    "emitter_name":emitter.name,
                    "surfaces_names":"_!#!_".join(o.name for o in surfaces),
                    "instances_names":"_!#!_".join(o.name for o in instances),
                    "psy_color_random":True,
                    "selection_mode":self.areamode,
                    "pop_msg":False,
                    }

        match self.areatype:

            case 'VIEW_3D':
                scat_operator(op_ctxt_item,**op_kwargs)
                
            case 'FILE_BROWSER':
                window, area, region = context.window, context.area, context.region
                if (area.type!='VIEW_3D'):
                    region_data = get_any_view3d_region(context=context, context_window_first=True,)
                    if (region_data):
                          window, area, region = region_data
                    else: window, area, region = None, None, None
                if (region):
                    global ADDMANUAL_OVERRIDES
                    ADDMANUAL_OVERRIDES = {'window':window, 'area':area, 'region':region,}
                    with context.temp_override(window=window, area=area, region=region):
                        scat_operator(op_ctxt_item,**op_kwargs)

        return {'FINISHED'}


class SCATTER5_OT_add_psy_modal(bpy.types.Operator):

    bl_idname      = "scatter5.add_psy_modal"
    bl_label       = translate("Quickly scatter the selected object(s), then change a few settings directly in modal mode.")
    bl_description = translate("Quickly scatter the selected object(s), then change a few settings directly in modal mode.")
    
    emitter_name : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    surfaces_names : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    instances_names : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},) 
    default_startup : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},) #"vg"|"bitmap"|"curve"

    p = None
    is_running = False
    recursive_launch = False

    def __init__(self, *args, **kwargs):
        """init default vars to False"""
        
        super().__init__(*args, **kwargs)
        
        self.is_density_D = self.is_scale_S = self.is_brightness_B = self.is_transforms_T = self.is_width_W = False
        return None 

    class InfoBox_add_psy_modal(SC5InfoBox):
        pass

    def invoke(self, context, event):
        cls = type(self)

        scat_scene = context.scene.scatter5
        scat_ops   = scat_scene.operators
        scat_op    = scat_ops.add_psy_modal

        #Get Emitter

        emitter = bpy.data.objects.get(self.emitter_name)
        if (emitter is None):
            emitter = scat_scene.emitter
        if (emitter is None):
            raise Exception("ERROR: add_psy_modal: Need an emitter object")

        #if user is relaunching, ,then we quit old loop, and start another loop soon

        """
        if (cls.is_running==True):

            cls.recursive_launch = True
            default_startup = str(self.default_startup)

            def launch_new_modal():
                nonlocal default_startup
                bpy.ops.scatter5.add_psy_modal(('INVOKE_DEFAULT'),default_startup=default_startup)
                #BUG here, when using draw_bezier_area, will lose the context 
                return None 

            bpy.app.timers.register(launch_new_modal, first_interval=0.1)
            return {'FINISHED'}
        """

        #set settings, normally these are in interface, here they are handled by the operator directly

        match self.default_startup:
            case 'vg'|'bitmap'|'curve'|'draw':
                scat_op.f_mask_action_method = "paint"
                scat_op.f_mask_action_type = self.default_startup
            case '':
                scat_op.f_mask_action_method = "none"
            case _:
                raise Exception("ERROR: SCATTER5_OT_add_psy_modal: unrecognized 'default_startup' passed argument")

        #override settings, instead of dumping a .preset text file

        density_value = scat_op.f_distribution_density
        override_dict_str = f"s_distribution_density:{density_value},s_distribution_is_random_seed:True,s_scale_default_allow:True,s_rot_align_z_allow:True,s_rot_align_y_allow:True,s_rot_align_y_method:'meth_align_y_random'"

        bpy.ops.scatter5.add_psy_preset(
            emitter_name=emitter.name,
            surfaces_names=self.surfaces_names,
            instances_names=self.instances_names,
            psy_name="QScatter",
            psy_color_random=True,
            settings_override=override_dict_str,
            ctxt_operator="add_psy_modal",
            pop_msg=True,
            )

        #save name for later
        self.p = emitter.scatter5.get_psy_active()

        #ignore any properties update behavior, such as update delay or hotkeys
        with bpy.context.scene.scatter5.factory_update_pause(event=True,delay=True,sync=True):

            # #add default vertex group
            # if (not self.p.s_mask_vg_allow):

            #     #TODO SURFACE
            #     vg = emitter.vertex_groups.new()
            #     vg.name = "Vgroup"
            #     self.p.s_mask_vg_allow = True
            #     self.p.s_mask_vg_ptr = vg.name

            #add default texture
            self.texture_node = self.p.get_scatter_node("s_pattern1").node_tree.nodes["texture"]
            self.texture_node.node_tree = self.texture_node.node_tree.copy()
            self.texture_node.node_tree.scatter5.texture.user_name = "QuickSatterTexture"
            self.texture_node.node_tree.scatter5.texture.mapping_random_allow = True 
            self.texture_node.node_tree.nodes["random_loc_switch"].mute = True

        textbox_title = translate("Quick Scatter Mode")
        textbox_undertitle = translate("Quickly adjust the settings with shortcuts below.")
        textbox_message = [
            "• "+translate("Press 'D+MOUSEWHEEL' to Adjust Density"),
            "• "+translate("Press 'S+MOUSEWHEEL' to Adjust Default Scale"),
            "• "+translate("Press 'R' to Randomize Seeds"),
            "• "+translate("Press 'P' to Toggle Pattern Slot 1"),
            "• "+translate("Press 'T+MOUSEWHEEL' to Adjust Pattern Transform Scale"),
            "• "+translate("Press 'B+MOUSEWHEEL' to Adjust Pattern Brightness"),
            "────────────────────────────",
            "• "+translate("Press 'SHIFT+MOUSEWHEEL' to Adjust With Precision"),
            "• "+translate("Press 'ESC' to Cancel"),
            "• "+translate("Press 'ENTER' to Confirm"),
            ]
        
        if (self.p.s_distribution_method=='projbezline'):
            textbox_message.insert(6, "• "+translate("Press 'W+MOUSEWHEEL' to Adjust the Spline-Pathwhay Width"),)
            
        #add infobox on screen
        t = generic_infobox_setup(textbox_title, textbox_undertitle, textbox_message,)
                                  
        self.InfoBox_add_psy_modal.init(t)
        # set following so infobox draw only in initial region
        self.InfoBox_add_psy_modal._draw_in_this_region_only = context.region
        # it is class variable, we don't know how it is set, so we need to make sure it is set how we want, and we want it to draw, only manual mode have option to hide it
        self.InfoBox_add_psy_modal._draw = True

        #set global scatter5 mode
        context.window_manager.scatter5.mode = 'PSY_MODAL'
        cls.is_running = True

        #start modal
        context.window_manager.modal_handler_add(self)

        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        cls = type(self)

        clear_all_fonts()

        #confirm event
        if ((event.type=='RET') or cls.recursive_launch):
            self.confirm(context)
            return {'FINISHED'}

        #cancel event
        if ((event.type=='ESC') or (context.window_manager.scatter5.mode!='PSY_MODAL')):
            self.cancel(context)
            return {'CANCELLED'}

        #shortcut detection

        if (event.type=='D'):
            if (event.value=="PRESS"):
                self.is_density_D = True
            elif (event.value!="PRESS"):
                self.is_density_D = False

        elif (event.type=='S'):
            if (event.value=="PRESS"):
                self.is_scale_S = True
            elif (event.value!="PRESS"):
                self.is_scale_S = False

        elif (event.type=='R'):
            if (event.value!="PRESS"): #wait for release
                self.p.s_distribution_is_random_seed = True
                self.p.s_rot_align_y_is_random_seed = True
                if (self.p.s_pattern1_allow):
                    self.texture_node.node_tree.scatter5.texture.mapping_random_is_random_seed = True
            return {'RUNNING_MODAL'}

        elif (event.type=='P'):
            if (event.value!="PRESS"): #wait for release
                self.p.s_pattern1_allow = not self.p.s_pattern1_allow
            return {'RUNNING_MODAL'}

        elif ((self.p.s_pattern1_allow) and (event.type=='B')):
            if (event.value=="PRESS"):
                self.is_brightness_B = True
            elif (event.value!="PRESS"):
                self.is_brightness_B = False

        elif ((self.p.s_pattern1_allow) and (event.type=='T')):
            if (event.value=="PRESS"):
                self.is_transforms_T = True
            elif (event.value!="PRESS"):
                self.is_transforms_T = False
        
        elif ((self.p.s_distribution_method=='projbezline') and (event.type=='W')):
            if (event.value=="PRESS"):
                self.is_width_W = True
            elif (event.value!="PRESS"):
                self.is_width_W = False

        #shortcut action

        if (self.is_density_D):
            
            densval = 0
            match event.type:
                case 'WHEELUPMOUSE':  densval += 0.1 if (event.shift) else 1
                case 'WHEELDOWNMOUSE':densval -= 0.1 if (event.shift) else 1
            
            match self.p.s_distribution_method:
                case 'random':
                    self.p.s_distribution_density += densval
                    density = self.p.s_distribution_density
                case 'projbezarea':
                    self.p.s_distribution_projbezarea_density += densval
                    density = self.p.s_distribution_projbezarea_density
                case 'projbezline':
                    self.p.s_distribution_projbezline_patharea_density += densval
                    density = self.p.s_distribution_projbezline_patharea_density
                
            add_font(text=translate("Instances/m²")+f": {density:.2f}", size=[40,40], position=[event.mouse_region_x,event.mouse_region_y], color=[1,1,1,0.9], origin="BOTTOM LEFT", shadow={"blur":3,"color":[0,0,0,0.6],"offset":[2,-2],})
            return {'RUNNING_MODAL'}

        elif (self.is_scale_S):
            
            if (not self.p.s_scale_default_allow):
                self.p.s_scale_default_allow=True
            match event.type:
                case 'WHEELUPMOUSE':  self.p.s_scale_default_value += Vector([0.01]*3) if (event.shift) else Vector([0.1]*3)
                case 'WHEELDOWNMOUSE':self.p.s_scale_default_value -= Vector([0.01]*3) if (event.shift) else Vector([0.1]*3)
            
            add_font(text=translate("Default Scale")+f": {self.p.s_scale_default_value[2]:.2f}", size=[40,40], position=[event.mouse_region_x,event.mouse_region_y], color=[1,1,1,0.9], origin="BOTTOM LEFT", shadow={"blur":3,"color":[0,0,0,0.6],"offset":[2,-2],})
            return {'RUNNING_MODAL'}

        elif (self.is_brightness_B):
            
            match event.type:
                case 'WHEELUPMOUSE':  self.texture_node.node_tree.scatter5.texture.intensity += 0.01 if (event.shift) else 0.1
                case 'WHEELDOWNMOUSE':self.texture_node.node_tree.scatter5.texture.intensity -= 0.01 if (event.shift) else 0.1
            
            add_font(text=translate("Pattern Brightness")+f": {self.texture_node.node_tree.scatter5.texture.intensity:.2f}", size=[40,40], position=[event.mouse_region_x,event.mouse_region_y], color=[1,1,1,0.9], origin="BOTTOM LEFT", shadow={"blur":3,"color":[0,0,0,0.6],"offset":[2,-2],})
            return {'RUNNING_MODAL'}

        elif (self.is_transforms_T):
            
            match event.type:
                case 'WHEELUPMOUSE':  self.texture_node.node_tree.scatter5.texture.scale -= 0.01 if (event.shift) else 0.1
                case 'WHEELDOWNMOUSE':self.texture_node.node_tree.scatter5.texture.scale += 0.01 if (event.shift) else 0.1
            
            add_font(text=translate("Pattern Scale")+f": {self.texture_node.node_tree.scatter5.texture.scale:.2f}", size=[40,40], position=[event.mouse_region_x,event.mouse_region_y], color=[1,1,1,0.9], origin="BOTTOM LEFT", shadow={"blur":3,"color":[0,0,0,0.6],"offset":[2,-2],})
            return {'RUNNING_MODAL'}

        elif (self.is_width_W):
        
            match event.type:
                case 'WHEELUPMOUSE':  self.p.s_distribution_projbezline_patharea_width -= 0.1 if (event.shift) else 0.35
                case 'WHEELDOWNMOUSE':self.p.s_distribution_projbezline_patharea_width += 0.1 if (event.shift) else 0.35
            
            add_font(text=translate("Spline Width")+f": {self.p.s_distribution_projbezline_patharea_width:.2f}", size=[40,40], position=[event.mouse_region_x,event.mouse_region_y], color=[1,1,1,0.9], origin="BOTTOM LEFT", shadow={"blur":3,"color":[0,0,0,0.6],"offset":[2,-2],})
            return {'RUNNING_MODAL'}
        
        return {'PASS_THROUGH'}

    def cancel(self, context):

        #remove psys, & refresh the interface
        self.p.remove_psy()
        context.scene.scatter5.emitter.scatter5.particle_interface_refresh()

        #what if created a curve area ?

        self.exit(context)
        return None

    def confirm(self, context):

        bpy.ops.ed.undo_push(message=translate("Quick Scatter Confirm"))

        self.exit(context)
        return None

    def exit(self, context):
        cls = type(self)

        #quit mode, if was in paint vg/texture
        if (context.mode!="OBJECT"):
            bpy.ops.object.mode_set(mode="OBJECT")

        context.window_manager.scatter5.mode = ""

        #reset modal
        cls.is_running = False
        cls.recursive_launch = False

        #clear indications
        self.InfoBox_add_psy_modal.deinit()

        return None


#  .oooooo..o oooo                               .                             .   
# d8P'    `Y8 `888                             .o8                           .o8   
# Y88bo.       888 .oo.    .ooooo.  oooo d8b .o888oo  .ooooo.  oooo  oooo  .o888oo 
#  `"Y8888o.   888P"Y88b  d88' `88b `888""8P   888   d88' `"Y8 `888  `888    888   
#      `"Y88b  888   888  888   888  888       888   888        888   888    888   
# oo     .d8P  888   888  888   888  888       888 . 888   .o8  888   888    888 . 
# 8""88888P'  o888o o888o `Y8bod8P' d888b      "888" `Y8bod8P'  `V88V"V8P'   "888" 
                                                                                 

quickscatter_keymaps = []

def register_quickscatter_shortcuts():
    
    if (bpy.app.background):
        return None
    
    wm  = bpy.context.window_manager
    kc  = wm.keyconfigs.addon
    km  = kc.keymaps.new(name="Window", space_type="EMPTY", region_type="WINDOW")
    kmi = km.keymap_items.new("scatter5.define_add_psy", 'W', 'PRESS', shift=True, alt=True, ctrl=True,)

    quickscatter_keymaps.append(kmi)

    return None

def unregister_quickscatter_shortcuts():

    if (bpy.app.background):
        return None

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    km = kc.keymaps["Window"]
    for kmi in quickscatter_keymaps:
        km.keymap_items.remove(kmi)
    quickscatter_keymaps.clear()

    return None
                                                                                 
                                                                                 
#   .oooooo.   oooo
#  d8P'  `Y8b  `888
# 888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
# 888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
# 888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
# `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#  `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'


classes = (

    SCATTER5_OT_add_psy_simple,
    SCATTER5_OT_add_psy_density,
    SCATTER5_OT_add_psy_preset,
    SCATTER5_OT_add_psy_manual,

    SCATTER5_OT_define_add_psy,
    SCATTER5_OT_add_psy_modal,

    )

#if __name__ == "__main__":
#    register()