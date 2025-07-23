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
#   .oooooo.                                               .                               
#  d8P'  `Y8b                                            .o8                               
# 888      888 oo.ooooo.   .ooooo.  oooo d8b  .oooo.   .o888oo  .ooooo.  oooo d8b  .oooo.o 
# 888      888  888' `88b d88' `88b `888""8P `P  )88b    888   d88' `88b `888""8P d88(  "8 
# 888      888  888   888 888ooo888  888      .oP"888    888   888   888  888     `"Y88b.  
# `88b    d88'  888   888 888    .o  888     d8(  888    888 . 888   888  888     o.  )88b 
#  `Y8bood8P'   888bod8P' `Y8bod8P' d888b    `Y888""8o   "888" `Y8bod8P' d888b    8""888P' 
#               888                                                                        
#              o888o                                                                       
################################################################################################s
     
                                                                                         
import bpy

from mathutils import Vector

from .. translations import translate
from .. resources.icons import cust_icon

from .. utils.str_utils import word_wrap
from .. utils.extra_utils import dprint, get_from_uid
from .. utils.event_utils import get_event
from .. utils.draw_utils import add_font, clear_all_fonts

from .. widgets.infobox import SC5InfoBox, generic_infobox_setup


#   .oooooo.                        .o88o.        .oooooo.             oooo                        oooo                .    o8o
#  d8P'  `Y8b                       888 `"       d8P'  `Y8b            `888                        `888              .o8    `"'
# 888           .ooooo.   .ooooo.  o888oo       888           .oooo.    888   .ooooo.  oooo  oooo   888   .oooo.   .o888oo oooo   .ooooo.  ooo. .oo.
# 888          d88' `88b d88' `88b  888         888          `P  )88b   888  d88' `"Y8 `888  `888   888  `P  )88b    888   `888  d88' `88b `888P"Y88b
# 888          888   888 888ooo888  888         888           .oP"888   888  888        888   888   888   .oP"888    888    888  888   888  888   888
# `88b    ooo  888   888 888    .o  888         `88b    ooo  d8(  888   888  888   .o8  888   888   888  d8(  888    888 .  888  888   888  888   888
#  `Y8bood8P'  `Y8bod8P' `Y8bod8P' o888o         `Y8bood8P'  `Y888""8o o888o `Y8bod8P'  `V88V"V8P' o888o `Y888""8o   "888" o888o `Y8bod8P' o888o o888o


class SCATTER5_OT_property_coef(bpy.types.Operator):

    bl_idname = "scatter5.property_coef"
    bl_label = "Coef Calculation"
    bl_description = translate("Multiply/ Divide/ Add/ Subtract the value above by a given coeffitient. Hold 'ALT' to do the operation on all selected scatter-system(s) by using the active system coeffitient")
    bl_options     = {'INTERNAL','UNDO'}

    operation : bpy.props.StringProperty() # + - * /
    coef : bpy.props.FloatProperty()
    prop : bpy.props.StringProperty()

    def execute(self, context):

        from ... __init__ import blend_prefs
        scat_data  = blend_prefs()
        scat_scene = bpy.context.scene.scatter5
        emitter    = scat_scene.emitter
        psy_active = emitter.scatter5.get_psy_active()
        psys_sel = emitter.scatter5.get_psys_selected(all_emitters=scat_data.factory_alt_selection_method=="all_emitters")

        def calculate(val, coef, operation):
            
            match operation:
                case '+':
                    if (type(val) is Vector):
                        coef = Vector((coef,coef,coef))
                    return val + coef
                case '-':
                    if (type(val) is Vector):
                        coef = Vector((coef,coef,coef))
                    return val - coef
                case '*':
                    return val * coef
                case '/':
                    if (coef==0):
                        return val
                    return val / coef
            
            return None

        #alt for batch support
        event = get_event(nullevent=not scat_data.factory_alt_allow)

        #ignore any properties update behavior, such as update delay or hotkeys, avoid feedback loop 
        with scat_scene.factory_update_pause(event=True,delay=True,sync=False):        

            #get context psys
            psys = psys_sel if ((event.alt) and (scat_data.factory_alt_allow)) else [psy_active]
            
            for p in psys:
                
                #get calculated value for each psys 
                value = calculate(getattr(p, self.prop), self.coef, self.operation)

                #avoid float to int error (duh)
                if type(getattr(p, self.prop))==int:
                    value = int(value)

                #set value to prop 
                setattr(p, self.prop, value)

                continue

        return {'FINISHED'}


#   .oooooo.             oooo  oooo             .o.             .o8      o8o                          .                                               .
#  d8P'  `Y8b            `888  `888            .888.           "888      `"'                        .o8                                             .o8
# 888           .ooooo.   888   888           .8"888.      .oooo888     oooo oooo  oooo   .oooo.o .o888oo ooo. .oo.  .oo.    .ooooo.  ooo. .oo.   .o888oo
# 888          d88' `88b  888   888          .8' `888.    d88' `888     `888 `888  `888  d88(  "8   888   `888P"Y88bP"Y88b  d88' `88b `888P"Y88b    888
# 888          888   888  888   888         .88ooo8888.   888   888      888  888   888  `"Y88b.    888    888   888   888  888ooo888  888   888    888
# `88b    ooo  888   888  888   888        .8'     `888.  888   888      888  888   888  o.  )88b   888 .  888   888   888  888    .o  888   888    888 .
#  `Y8bood8P'  `Y8bod8P' o888o o888o      o88o     o8888o `Y8bod88P"     888  `V88V"V8P' 8""888P'   "888" o888o o888o o888o `Y8bod8P' o888o o888o   "888"
#                                                                        888
#                                                                    .o. 88P
#                                                                    `Y888P

# #NOTE should this be runned when user is changing -> TODO scene_callback

# def manage_scene_s5_viewlayers():
#     """When working with multiple scene(s), the Geo-Scatter 5 collection, containing all the scatter-system(s) data created by scatter will be present in your scene, 
#     run this operator to hide the viewlayers not used in the current scene."""

#     from .. utils.coll_utils import set_collection_view_layers_exclude
#     scene = bpy.context.scene
#     scat_scene = scene.scatter5
                
#     scatter_collections = [c for c in scene.collection.children_recursive if c.name.startswith("psy : ")]

#     if (len(scatter_collections)==0):
#         return None  

#     #get all psys collection names for this context scene
#     all_psys_coll = [ f"psy : {p.name}" for p in scat_scene.get_all_psys(search_mode="active_view_layer") ]

#     for coll in scatter_collections:
#         did = set_collection_view_layers_exclude(coll, scenes=[scene], hide=(coll.name not in all_psys_coll),)
#         if (did==True) and ("did_act" not in locals()):
#             did_act = True
        
#     if ("did_act" in locals()):
#         dprint("HANDLER: 'manage_scene_s5_viewlayers'", depsgraph=True,)

#     return None 

# class SCATTER5_OT_refresh_psy_viewlayers(bpy.types.Operator):

#     bl_idname      = "scatter5.refresh_psy_viewlayers"
#     bl_label       = translate("")
#     bl_description = translate("When working with multiple scene(s), the Geo-Scatter collection, containing all the scatter-system(s) data created by scatter will be present in your scene, run this operator to hide the viewlayers not used in the current scene.")
#     bl_options     = {'INTERNAL', 'UNDO'}

#     def execute(self, context):

#         manage_scene_s5_viewlayers()

#         return {'FINISHED'}


# ooooooooo.                                    .         .oooooo..o               .       .
# `888   `Y88.                                .o8        d8P'    `Y8             .o8     .o8
#  888   .d88'  .ooooo.   .oooo.o  .ooooo.  .o888oo      Y88bo.       .ooooo.  .o888oo .o888oo
#  888ooo88P'  d88' `88b d88(  "8 d88' `88b   888         `"Y8888o.  d88' `88b   888     888
#  888`88b.    888ooo888 `"Y88b.  888ooo888   888             `"Y88b 888ooo888   888     888
#  888  `88b.  888    .o o.  )88b 888    .o   888 .      oo     .d8P 888    .o   888 .   888 .
# o888o  o888o `Y8bod8P' 8""888P' `Y8bod8P'   "888"      8""88888P'  `Y8bod8P'   "888"   "888"



class SCATTER5_OT_reset_settings(bpy.types.Operator):

    bl_idname      = "scatter5.reset_settings"
    bl_label       = translate("Reset Settings")
    bl_description = translate("Reset the settings of this category to the default values")
    bl_options     = {'INTERNAL', 'UNDO'}

    single_category : bpy.props.StringProperty()

    def find_default(self, api, string_set):
        """find default value of a property"""

        pro = api.bl_rna.properties[string_set] 

        match pro.type:
            case 'ENUM'|'STRING'|'BOOLEAN':
                return pro.default
            case 'FLOAT'|'INT':
                return pro.default if (pro.array_length==0) else pro.default_array
            case 'POINTER':
                return None #Object pointers are None by default

        return None

    def execute(self, context):
        
        scat_scene = context.scene.scatter5
        emitter = scat_scene.emitter
        psy_active = emitter.scatter5.get_psy_active()

        if (psy_active is None):
            return {'FINISHED'}
        if (psy_active.is_locked(self.single_category)):
            return {'FINISHED'}

        #ignore any properties update behavior, such as update delay or hotkeys
        with scat_scene.factory_update_pause(event=True,delay=True,sync=False):

            #hide for optimization 
            did_hide = None 
            if (not psy_active.hide_viewport):
                psy_active.hide_viewport = did_hide = True

            for s in [k for k in psy_active.bl_rna.properties.keys() if k.startswith(self.single_category) ]:
                try:
                    default_value = self.find_default(psy_active,s)
                    setattr(psy_active, s, default_value)
                except Exception as e:
                    print(f"ERROR: scatter5.reset_settings(): couldn't reset '{s}'")
                    print(e)

            #restore optimization
            if (did_hide is not None):
                psy_active.hide_viewport = False
                
        return {'FINISHED'}


# oooooooooo.    o8o                      .o8       oooo                  .oooooo..o               .       .
# `888'   `Y8b   `"'                     "888       `888                 d8P'    `Y8             .o8     .o8
#  888      888 oooo   .oooo.o  .oooo.    888oooo.   888   .ooooo.       Y88bo.       .ooooo.  .o888oo .o888oo
#  888      888 `888  d88(  "8 `P  )88b   d88' `88b  888  d88' `88b       `"Y8888o.  d88' `88b   888     888
#  888      888  888  `"Y88b.   .oP"888   888   888  888  888ooo888           `"Y88b 888ooo888   888     888
#  888     d88'  888  o.  )88b d8(  888   888   888  888  888    .o      oo     .d8P 888    .o   888 .   888 .
# o888bood8P'   o888o 8""888P' `Y888""8o  `Y8bod8P' o888o `Y8bod8P'      8""88888P'  `Y8bod8P'   "888"   "888"


class SCATTER5_OT_disable_main_settings(bpy.types.Operator):

    bl_idname = "scatter5.disable_main_settings"
    bl_label = translate("Disable Procedural Settings")
    bl_description = translate("Disable Procedural Settings")
    bl_options = {'INTERNAL', 'UNDO'}
    
    mode : bpy.props.StringProperty(default="active", options={"SKIP_SAVE",},)
    emitter_name : bpy.props.StringProperty()

    @classmethod
    def poll(cls, context, ):
        return True
    
    def execute(self, context):

        if (self.emitter_name):
              emitter = bpy.data.objects.get(self.emitter_name)
              self.emitter_name = ""
        else: emitter = bpy.context.scene.scatter5.emitter

        if (self.mode=="active"):
              psys = [ emitter.scatter5.get_psy_active() ]
        else: psys = emitter.scatter5.get_psys_selected()

        for p in psys:
            for k in p.bl_rna.properties.keys():
                if (k.endswith("master_allow")):
                    if (k=="s_display_master_allow"):
                        continue #everything except display
                    setattr(p, k, False)
            
        return {'FINISHED'}

#   .oooooo.   oooo                                       ooooo                                                     .
#  d8P'  `Y8b  `888                                       `888'                                                   .o8
# 888           888   .ooooo.   .oooo.   ooo. .oo.         888  ooo. .oo.  .oo.   oo.ooooo.   .ooooo.  oooo d8b .o888oo
# 888           888  d88' `88b `P  )88b  `888P"Y88b        888  `888P"Y88bP"Y88b   888' `88b d88' `88b `888""8P   888
# 888           888  888ooo888  .oP"888   888   888        888   888   888   888   888   888 888   888  888       888
# `88b    ooo   888  888    .o d8(  888   888   888        888   888   888   888   888   888 888   888  888       888 .
#  `Y8bood8P'  o888o `Y8bod8P' `Y888""8o o888o o888o      o888o o888o o888o o888o  888bod8P' `Y8bod8P' d888b      "888"
#                                                                                  888
#                                                                                 o888o

class SCATTER5_OT_clean_unused_import_data(bpy.types.Operator):

    bl_idname      = "scatter5.clean_unused_import_data"
    bl_label       = translate("Removed any unused object(s) located in the 'Geo-Scatter Import' Collection")
    bl_description = translate("Removed any unused object(s) located in the 'Geo-Scatter Import' Collection")
    bl_options     = {'INTERNAL', 'UNDO'}

    def execute(self, context):

        import_coll = bpy.data.collections.get("Geo-Scatter Import")
        if (import_coll is None):
            raise Exception(translate("It seems that you didn't import anything yet?"))

        used_objs = []
        for sc in bpy.data.scenes:
            for coll in sc.collection.children_recursive:
                if (coll.name!=import_coll.name):
                    for o in coll.objects:
                        if (o not in used_objs):
                            used_objs.append(o)

        for o in import_coll.objects:
            if (o not in used_objs):
                bpy.data.meshes.remove(o.data)

        return {'FINISHED'}

# oooooooooo.                .             oooo
# `888'   `Y8b             .o8             `888
#  888     888  .oooo.   .o888oo  .ooooo.   888 .oo.
#  888oooo888' `P  )88b    888   d88' `"Y8  888P"Y88b
#  888    `88b  .oP"888    888   888        888   888
#  888    .88P d8(  888    888 . 888   .o8  888   888
# o888bood8P'  `Y888""8o   "888" `Y8bod8P' o888o o888o


class SCATTER5_OT_batch_toggle(bpy.types.Operator):

    bl_idname      = "scatter5.batch_toggle"
    bl_label       = translate("Batch toggle Scatter-System(s)")
    bl_description = translate("Batch change properties of multiple scatter-system(s)")
    bl_options     = {'INTERNAL','UNDO'}

    propname : bpy.props.StringProperty() #hide_viewport/hide_render
    emitter_name : bpy.props.StringProperty(options={'SKIP_SAVE',})
    emitter_session_uid : bpy.props.IntProperty(options={'SKIP_SAVE',})
    group_name : bpy.props.StringProperty(options={'SKIP_SAVE',})
    scene_name : bpy.props.StringProperty(options={'SKIP_SAVE',})
    setvalue : bpy.props.StringProperty(default="auto", options={'SKIP_SAVE',},)

    @classmethod
    def description(cls, context, properties,):
        match properties.propname:
            case 'sel':
                return translate("Batch Select/Deselet system(s)")
            case 'hide_viewport':
                return translate("Batch Hide/Unhide system(s) from viewport")
            case 'hide_render':
                return translate("Batch Hide/Unhide system(s) from render")
        return ""

    def execute(self, context):
        
        scat_scene = context.scene.scatter5

        #Get Emitter (will find context emitter if nothing passed)
        
        emitter = None
        
        #get emitter by sessuid? needed if linked emitter and name collision
        if (self.emitter_session_uid):
            emitter = get_from_uid(self.emitter_session_uid)
            
        #get emitter by name?
        elif(self.emitter_name):
            emitter = bpy.data.objects.get(self.emitter_name)
        
        #if none found, fallback on context emitter
        if (emitter is None):
            emitter = scat_scene.emitter

        #if input is scene, batch toggle all psys of scene
        if (self.scene_name!=""):
            assert (self.scene_name in bpy.data.scenes)
            psys = bpy.data.scenes[self.scene_name].scatter5.get_all_psys(search_mode="active_view_layer")

        #if input is group, batch toggle all element of group
        elif (self.group_name!=""):
            assert (emitter is not None)
            g = emitter.scatter5.particle_groups[self.group_name]
            psys = [p for p in emitter.scatter5.particle_systems if ((p.group!="") and (p.group==g.name)) ]

        #else we batch on all emitter psys if we passed an emitter
        elif ((self.emitter_name!="") or (self.emitter_session_uid!="")):
            assert (emitter is not None)
            psys = emitter.scatter5.particle_systems[:]

        else: 
            raise Exception("Please pass either a scene, emitter, or group_name + emitter as an arg for this operator")

        with context.scene.scatter5.factory_update_pause(event=True,delay=True,sync=True):

            #special case for lock property... lock property is a fake, used as an operator
            if (self.setvalue=="lock_special"):
                setvalue = not any(p.is_all_locked() for p in psys) #p.lock
                [setattr(p,"lock",True) for p in psys if (p.is_all_locked()!=setvalue)]
                return {'FINISHED'}

            setvalue = eval(self.setvalue)
            [setattr(p,self.propname,setvalue) for p in psys if (getattr(p,self.propname)!=setvalue)]

        #refresh areas
        [a.tag_redraw() for a in context.screen.areas]

        return {'FINISHED'}


class SCATTER5_OT_batch_randomize(bpy.types.Operator):

    bl_idname      = "scatter5.batch_randomize"
    bl_label       = translate("Batch Randomize Scatter-System(s)")
    bl_description = translate("Randomize most seeds of the chosen scatter-system(s) including their distribution seeds, pattern random transform seeds, and transition noise seeds")
    bl_options     = {'INTERNAL','UNDO'}

    use_context_sel : bpy.props.BoolProperty(default=False, options={'SKIP_SAVE',},)
    emitter_name : bpy.props.StringProperty(default="", options={'SKIP_SAVE',},)
    psy_name : bpy.props.StringProperty(default="", options={'SKIP_SAVE',},)
    group_name : bpy.props.StringProperty(default="", options={'SKIP_SAVE',},)
    scene_name : bpy.props.StringProperty(default="", options={'SKIP_SAVE',},)

    def invoke(self, context, event):
        self.alt = event.alt
        return self.execute(context)

    def execute(self, context):
        
        from ... __init__ import blend_prefs
        scat_data  = blend_prefs()
        scat_scene = context.scene.scatter5

        #Get Emitter (will find context emitter if nothing passed)
        emitter = bpy.data.objects.get(self.emitter_name)
        if (emitter is None):
            emitter = scat_scene.emitter

        #input is currently selected psys on context emitter?
        if (self.use_context_sel==True):
            psys = emitter.scatter5.get_psys_selected()
        
        #if input is scene, batch toggle all psys of scene
        elif (self.scene_name!=""):
            assert (self.scene_name in bpy.data.scenes)
            psys = bpy.data.scenes[self.scene_name].scatter5.get_all_psys(search_mode="active_view_layer")

        #if input is group, batch toggle all element of group
        elif (self.group_name!=""):
            assert (emitter is not None)
            g = emitter.scatter5.particle_groups[self.group_name]
            psys = [p for p in emitter.scatter5.particle_systems if ((p.group!="") and (p.group==g.name)) ]

        #if inputis group, just toggle psyname
        elif (self.psy_name!=""):
            assert (emitter is not None)
            psys = [ emitter.scatter5.particle_systems[self.psy_name] ]
            if (self.alt):
                psys = emitter.scatter5.get_psys_selected(all_emitters=scat_data.factory_alt_selection_method=="all_emitters")

        #else we batch on all emitter psys
        elif (self.emitter_name!=""):
            assert (emitter is not None)
            psys = emitter.scatter5.particle_systems[:]

        else: 
            raise Exception("Please choose either scene_name, emitter_name, or group_name + emitter_name as args")

        with context.scene.scatter5.factory_update_pause(event=True,delay=True,sync=True):

            for p in psys:

                #randomize distribution seed, depending on distype
                
                match p.s_distribution_method:
                    case 'random':
                        p.s_distribution_is_random_seed = True
                    case 'volume':
                        p.s_distribution_volume_is_random_seed = True
                    case 'random_stable':
                        p.s_distribution_stable_is_random_seed = True
                    case 'clumping':
                        p.s_distribution_clump_is_random_seed = True
                        p.s_distribution_clump_children_is_random_seed = True

                #randomize patterns
                for i in (1,2,3):
                    if getattr(p,f"s_pattern{i}_allow"):
                        texture_name = getattr(p,f"s_pattern{i}_texture_ptr")
                        if (texture_name is not None):
                            ng = p.get_scatter_node(f's_pattern{i}').node_tree.nodes['texture'].node_tree
                            if ng.name.startswith(".TEXTURE *DEFAULT*"):
                                continue
                            t = ng.scatter5.texture
                            t.mapping_random_is_random_seed = True

                #randomize fallnoisy
                for k in p.bl_rna.properties.keys():
                    if (k.endswith("fallnoisy_is_random_seed")):
                        if getattr(p,k.replace("fallnoisy_is_random_seed","fallremap_allow")):
                            setattr(p,k,True)

                #missing something?
                continue

        return {'FINISHED'}


class SCATTER5_OT_batch_set_space(bpy.types.Operator):

    bl_idname      = "scatter5.batch_set_space"
    bl_label       = translate("Batch set spaces of scatter-system(s)")
    bl_description = translate("Batch redefine the distribution/feature spaces of the chosen scatter-system(s)")
    bl_options     = {'INTERNAL','UNDO'}

    use_context_sel : bpy.props.BoolProperty(default=True, options={'SKIP_SAVE',},)
    emitter_name : bpy.props.StringProperty(default="", options={'SKIP_SAVE',},)
    psy_name : bpy.props.StringProperty(default="", options={'SKIP_SAVE',},)
    space : bpy.props.StringProperty(default='local', options={'SKIP_SAVE',},) #local/global

    def invoke(self, context, event):
        self.alt = event.alt
        return self.execute(context)

    def execute(self, context):

        scat_scene = context.scene.scatter5

        #Get Emitter (will find context emitter if nothing passed)
        emitter = bpy.data.objects.get(self.emitter_name)
        if (emitter is None):
            emitter = scat_scene.emitter

        #input is currently selected psys on context emitter?
        if (self.use_context_sel):
            psys = emitter.scatter5.get_psys_selected()
        
        #if input psyname, we only use given psy
        elif (self.psy_name!=""):
            assert self.psy_name in emitter.scatter5.particle_systems
            psys = [ emitter.scatter5.particle_systems[self.psy_name] ]

        with context.scene.scatter5.factory_update_pause(event=True,delay=True,sync=True):
            for p in psys:
                p.set_general_space(space=self.space)
    
        return {'FINISHED'}

# oooooooooo.                                          .o8   o8o                              oooooooooo.
# `888'   `Y8b                                        "888   `"'                              `888'   `Y8b
#  888     888  .ooooo.  oooo  oooo  ooo. .oo.    .oooo888  oooo  ooo. .oo.    .oooooooo       888     888  .ooooo.  oooo    ooo
#  888oooo888' d88' `88b `888  `888  `888P"Y88b  d88' `888  `888  `888P"Y88b  888' `88b        888oooo888' d88' `88b  `88b..8P'
#  888    `88b 888   888  888   888   888   888  888   888   888   888   888  888   888        888    `88b 888   888    Y888'
#  888    .88P 888   888  888   888   888   888  888   888   888   888   888  `88bod8P'        888    .88P 888   888  .o8"'88b
# o888bood8P'  `Y8bod8P'  `V88V"V8P' o888o o888o `Y8bod88P" o888o o888o o888o `8oooooo.       o888bood8P'  `Y8bod8P' o88'   888o
#                                                                             d"     YD
#                                                                             "Y88888P'

class SCATTER5_OT_batch_bounding_box(bpy.types.Operator):

    bl_idname      = "scatter5.batch_bounding_box"
    bl_label       = translate("Batch-Set Objects Bounding-Box")
    bl_description = translate("Toggle between 'Bounding-Box' or 'Textured' object display option for all original objects used as instances your scatter-system(s)")
    bl_options     = {'INTERNAL', 'UNDO'}

    #interface
    pop_dialog : bpy.props.BoolProperty(default=False, options={"SKIP_SAVE",},)
    pop_influence_options : bpy.props.EnumProperty(
        name=translate("Influence"),
        default="all",
        items=(("all",translate("All System(s)"),"",),
               ("sel",translate("All Selected System(s)"),"",),
              ),
        ) 
    pop_influence_value : bpy.props.EnumProperty(
        name=translate("Value"),
        default="BOUNDS",
        items=(("BOUNDS",translate("Enable"),"",),
               ("TEXTURED",translate("Disable"),"",),
              ),
        ) 

    #internal settings
    use_sel_all : bpy.props.BoolProperty(options={"SKIP_SAVE",},)
    psy_name : bpy.props.StringProperty(options={"SKIP_SAVE",},)
    group_name : bpy.props.StringProperty(options={"SKIP_SAVE",},)
    emitter_name : bpy.props.StringProperty(options={"SKIP_SAVE",},)
    scene_name : bpy.props.StringProperty(options={"SKIP_SAVE",},)
    set_value : bpy.props.StringProperty(default="auto", options={"SKIP_SAVE",},)

    def draw(self, context):
        layout = self.layout
        
        layout.prop(self,"pop_influence_options",)
        layout.prop(self,"pop_influence_value",)
        layout.separator(factor=0.5)

        psys = bpy.data.objects[0].scatter5.get_psys_selected(all_emitters=True) if (self.pop_influence_options=="sel") else bpy.context.scene.scatter5.get_all_psys(search_mode="active_view_layer")
        objs = [o for p in psys for o in p.get_instance_objs() ]

        layout.label(text=translate("Apply to")+f" {len(psys)} "+translate("Scatter-System(s)")+" → "+f" {len(objs)} "+translate("Objects"),)

        return None

    def invoke(self, context, event):

        if (self.pop_dialog):
            return bpy.context.window_manager.invoke_props_dialog(self) 

        return self.execute(context)

    def execute(self, context):

        scat_scene = context.scene.scatter5

        #automatically define settings if user has been using a dialog box
        if (self.pop_dialog):
            if (self.pop_influence_options=="all"):
                  self.use_sel_all = True
            else: self.scene_name = bpy.context.scene
            self.set_value = self.pop_influence_value

        #Get Emitter (will find context emitter if nothing passed)
        emitter = bpy.data.objects.get(self.emitter_name)
        if (emitter is None):
            emitter = scat_scene.emitter

        if (self.use_sel_all):
            psys = emitter.scatter5.get_psys_selected(all_emitters=True)

        #if input is scene, batch toggle all psys of scene
        elif (self.scene_name!=""):
            assert (self.scene_name in bpy.data.scenes)
            psys = bpy.data.scenes[self.scene_name].scatter5.get_all_psys(search_mode="active_view_layer")

        #if input is group, batch toggle all element of group
        elif (self.group_name!=""):
            assert (emitter is not None)
            g = emitter.scatter5.particle_groups[self.group_name]
            psys = [p for p in emitter.scatter5.particle_systems if ((p.group!="") and (p.group==g.name)) ]

        #if inputis group, just toggle psyname
        elif (self.psy_name!=""):
            assert (emitter is not None)
            psys = [ emitter.scatter5.particle_systems[self.psy_name] ]

        #else we batch on all emitter psys
        elif (self.emitter_name!=""):
            assert (emitter is not None)
            psys = emitter.scatter5.particle_systems[:]

        for p in psys:

            objs = p.get_instance_objs()
            
            if (not len(objs)):
                return {'FINISHED'}

            if (self.set_value=="auto"):
                  set_value = any(o.display_type=="TEXTURED" for o in objs)
                  set_value = "BOUNDS" if set_value else "TEXTURED"
            else: set_value = self.set_value

            for o in objs: 
                if (o.display_type!=set_value):
                    o.display_type = set_value

            continue

        return {'FINISHED'}


# class SCATTER5_OT_batch_optimization(bpy.types.Operator):

#     bl_idname      = "scatter5.batch_optimization"
#     bl_label       = translate("Batch-Set Objects Bounding-Box")
#     bl_description = translate("Toggle between 'Bounding-Box' or 'Textured' display for all original objects used as instances by of the scatter-system(s).\nPlease note that this might impact other scatter-systems as well.")
#     bl_options     = {'INTERNAL', 'UNDO'}

#     #interface
#     pop_dialog : bpy.props.BoolProperty(default=False, options={"SKIP_SAVE",},)
#     pop_influence_options : bpy.props.EnumProperty(
#         name=translate("Influence"),
#         default="all",
#         items=[("sel",translate("Selected System(s)"),"",),
#                ("all",translate("All System(s)"),"",),
#                ],) 


#     #replicate optimization features
#     #TODO, but would be nasty...


#     #internal settings
#     use_sel_all : bpy.props.BoolProperty(options={"SKIP_SAVE",},)
#     psy_name : bpy.props.StringProperty(options={"SKIP_SAVE",},)
#     group_name : bpy.props.StringProperty(options={"SKIP_SAVE",},)
#     emitter_name : bpy.props.StringProperty(options={"SKIP_SAVE",},)
#     scene_name : bpy.props.StringProperty(options={"SKIP_SAVE",},)
#     set_value : bpy.props.StringProperty(default="auto", options={"SKIP_SAVE",},)

#     def draw(self, context):
#         layout = self.layout
        
#         layout.prop(self,"pop_influence_options",)
#         layout.prop(self,"pop_influence_value",)
#         layout.separator(factor=0.5)

#         psys = bpy.data.objects[0].scatter5.get_psys_selected(all_emitters=True) if (self.pop_influence_options=="sel") else bpy.context.scene.scatter5.get_all_psys(search_mode="active_view_layer")
#         objs = [o for p in psys for o in p.get_instance_objs() ]

#         layout.label(text=translate("Apply to")+f" {len(psys)} "+translate("Scatter-System(s)")+" → "+f" {len(objs)} "+translate("Objects"),)

#         return None

#     def invoke(self, context, event):

#         if (self.pop_dialog):
#             return bpy.context.window_manager.invoke_props_dialog(self) 

#         return self.execute(context)

#     def execute(self, context):

#         scat_scene = context.scene.scatter5

#         #automatically define settings if user has been using a dialog box
#         if (self.pop_dialog):
#             if (self.pop_influence_options=="all"):
#                   self.use_sel_all = True
#             else: self.scene_name = bpy.context.scene
#             self.set_value = self.pop_influence_value

#         #Get Emitter (will find context emitter if nothing passed)
#         emitter = bpy.data.objects.get(self.emitter_name)
#         if (emitter is None):
#             emitter = scat_scene.emitter

#         if (self.use_sel_all):
#             psys = emitter.scatter5.get_psys_selected(all_emitters=True)

#         #if input is scene, batch toggle all psys of scene
#         elif (self.scene_name!=""):
#             assert (self.scene_name in bpy.data.scenes)
#             psys = bpy.data.scenes[self.scene_name].scatter5.get_all_psys(search_mode="active_view_layer")

#         #if input is group, batch toggle all element of group
#         elif (self.group_name!=""):
#             assert (emitter is not None)
#             g = emitter.scatter5.particle_groups[self.group_name]
#             psys = [p for p in emitter.scatter5.particle_systems if ((p.group!="") and (p.group==g.name)) ]

#         #if inputis group, just toggle psyname
#         elif (self.psy_name!=""):
#             assert (emitter is not None)
#             psys = [ emitter.scatter5.particle_systems[self.psy_name] ]

#         #else we batch on all emitter psys
#         elif (self.emitter_name!=""):
#             assert (emitter is not None)
#             psys = emitter.scatter5.particle_systems[:]

#         for p in psys:

#             objs = p.get_instance_objs()
            
#             if (not len(objs)):
#                 return {'FINISHED'}

#             if (self.set_value=="auto"):
#                   set_value = any(o.display_type=="TEXTURED" for o in objs)
#                   set_value = "BOUNDS" if set_value else "TEXTURED"
#             else: set_value = self.set_value

#             for o in objs: 
#                 if (o.display_type!=set_value):
#                     o.display_type = set_value

#             continue

#         return {'FINISHED'}


# ooooo     ooo                  .o8       ooooo      ooo                 .o8                .
# `888'     `8'                 "888       `888b.     `8'                "888              .o8
#  888       8  oo.ooooo.   .oooo888        8 `88b.    8   .ooooo.   .oooo888   .ooooo.  .o888oo oooo d8b  .ooooo.   .ooooo.   .oooo.o
#  888       8   888' `88b d88' `888        8   `88b.  8  d88' `88b d88' `888  d88' `88b   888   `888""8P d88' `88b d88' `88b d88(  "8
#  888       8   888   888 888   888        8     `88b.8  888   888 888   888  888ooo888   888    888     888ooo888 888ooo888 `"Y88b.
#  `88.    .8'   888   888 888   888        8       `888  888   888 888   888  888    .o   888 .  888     888    .o 888    .o o.  )88b
#    `YbodP'     888bod8P' `Y8bod88P"      o8o        `8  `Y8bod8P' `Y8bod88P" `Y8bod8P'   "888" d888b    `Y8bod8P' `Y8bod8P' 8""888P'
#                888
#               o888o


def fix_nodetrees(force_update=False):
    """either fix a broken nodetree to latest psy version, and/or also ensure some versioning actions"""
    
    from . texture_datablock import ensure_texture_ptr_name
    from ... __init__ import bl_info, addon_prefs, blend_prefs
    from .. import utils
    from .. resources import directories
    from .. scattering.update_factory import get_node
    
    scat_addon = addon_prefs()
    scat_data  = blend_prefs()
    scat_scene = bpy.context.scene.scatter5
    
    engine_version = bl_info['engine_version']
    engine_nbr     = bl_info['engine_nbr']
    
    print("")
    print(f"GEO-SCATTER: fix_nodetrees(force_update={force_update}) operation, for version {engine_version}")
    
    #in GS 5.5 we changed the uuid system bpy.conntext.scene.scatter5.uuids aren't used anymore
    print("   -Versioning: Update Legacy Uuids System..")
    for sc in bpy.data.scenes:
        if (sc.scatter5.uuids):
            for itm in sc.scatter5.uuids:
                obj = itm.owner
                if (obj):
                    print(f"         -Found scene.uuids '{sc.name}' owner '{obj.name}' with legacy uuid {itm.uuid}.")
                    _ = obj.scatter5.uuid #initializing uuid will automatically find legacy value if existing
        sc.scatter5.uuids.clear()
        continue
    
    #first, we ensure that the texture_ptr are accurate, normally we don't want to mess with these properties values, we only use it as a setter, but for this specific case, the property will get refreshed, & the value will need to be accurate
    print(f"   -Ensuring accurate scatter 'texture_ptr' properties")
    ensure_texture_ptr_name()
    
    #search for all psy we need to update, either we force update all, or we try to get latest scatter mod engine, 
    #if not engine found, means that psy is using old version & need an update
    print(f"   -Evaluating Scatter-System(s) needing a new Scatter-Engine..")
    
    all_psys = scat_scene.get_all_psys(search_mode="all", also_linked=False)
    psys_needing_upd = set()
    
    for p in all_psys:
        if (force_update):
            print(f"         -Found '{p.name}'")
            psys_needing_upd.add(p)
            continue
        mod = p.get_scatter_mod(strict=True, raise_exception=False)
        if (mod is None):
            psys_needing_upd.add(p)
            print(f"         -Found '{p.name}'")
            continue
        if (mod.node_group is None):
            psys_needing_upd.add(p)
            print(f"         -Found '{p.name}'")
            continue
        continue
                    
    #hide all psys
    hide_dict = {p.name:p.hide_viewport for p in all_psys}
    for p in all_psys:
        p.hide_viewport = True 
        continue 
    
    #force update all geonode engines ? then we remove the original engine node and their nodegroups
    if (force_update):

        print(f"   -Force update option enabled! We'll remove all Geo-Scatter nodegroups used for the current version as well (and re-implement fresh new ones later)")
        
        #remove default engine node
        old_nodetree = bpy.data.node_groups.get(f".{engine_version}")
        if (old_nodetree):
            bpy.data.node_groups.remove(old_nodetree)
            
        #remove default texture as well
        texture_default = bpy.data.node_groups.get(".TEXTURE *DEFAULT* MKV")
        if (texture_default):
            bpy.data.node_groups.remove(texture_default)
            
        #remove dependent Geo-scatter ng as well
        for nng in [nng for nng in bpy.data.node_groups if nng.name.startswith(".S ") and nng.name.endswith(engine_nbr)]: 
            bpy.data.node_groups.remove(nng)

    #importing latest Scatter Engine Nodetree, normally this is done automatically in import_and_add_geonode() however we need to have the engine first to get the default texture
    print(f"   -Importing the latest the Scatter Engine Nodetree, '{engine_version}' from '{directories.blend_engine}'")
    
    utils.import_utils.import_geonodes(directories.blend_engine, [f".{engine_version}"], link=False,)
    engine = bpy.data.node_groups.get(f".{engine_version}")
    
    if (not engine):
        print(f"   -Couldn't import '{engine_version}' from '{directories.blend_engine}'")
        print("   -Conversion Canceled..\n\n")
        return None
    
    engine.use_fake_user = True

    #we changed the universal mask enum in interface, no longer none by default. need to know old value before the change..
    print(f"   -Versioning: For all Scatter-System(s) Ensuring Feature mask toggle status")

    for p in psys_needing_upd:
        for propname in [k for k in p.bl_rna.properties.keys() if k.startswith("s_") and k.endswith("_mask_allow")]:
            basename = propname.split("_mask_allow")[0]
            n = get_node(p, f"{basename}.umask", strict=False,)
            if (n is None):
                continue
            if (len(n.inputs)<3):
                continue
            methdval = int(n.inputs[3].default_value)
            if (methdval!=0) and (getattr(p,propname)==False):
                with bpy.context.scene.scatter5.factory_update_pause(factory=True):
                    setattr(p,propname,True)
                    
    #about the scatter_texture_nodetrees, the also need an update! replace all .texture nodes by new one
    print(f"   -Updating the Scatter-Texture(s) to latest version..")
    
    all_textures_ng = [ng for ng in bpy.data.node_groups if (ng.name.startswith(".TEXTURE") and not ng.name.startswith((".TEXTURE *DEFAULT",".TEXTURE *VISUALIZER*")) ) ]
    
    for ng in all_textures_ng.copy():
        
        old_ng_name = ng.name
        old_user_name = ng.scatter5.texture.user_name
        
        print(f"         -Updating Texture '{old_user_name}' aka Nodegroup '{old_ng_name}'",)
        
        d = ng.scatter5.texture.get_texture_dict()
        bpy.data.node_groups.remove(ng)

        newng = bpy.data.node_groups.get(".TEXTURE *DEFAULT* MKV").copy() #is only availale because we imported the engine in import_geonodes()
        newng.name = old_ng_name #ensure same name as before
        newng.scatter5.texture.apply_texture_dict(d) #same settings as before
        newng.scatter5.texture.is_default = False #is not a default texture..
        newng.scatter5.texture.user_name = old_user_name #set new user name
        
        continue
    
    #for all psys needing an update.. 
    #remove it's current modifier and add a new one

    print(f"   -Updating Scatter-System(s) to latest version..")

    for p in psys_needing_upd.copy():
        print(f"         -Updating : '{p.name}'")
        
        so = p.scatter_obj
        if (so is None):
            print(f"             -ERROR! Scatter-System doesn't have a scatter_obj? That shouldn't be possible.")
            continue
            
        #remove all mods 
        print(f"             -Removing old Scatter-Engine Geonode modifier")
        so.modifiers.clear()

        #create new geonode mod and import latest nodetree 
        print(f"             -Implementing new Scatter-Engine Geonode modifier")
        #note that we already imported the .blend we need earlier, here we are simply setting up the modifier via this function
        m = utils.import_utils.import_and_add_geonode(so,
            mod_name=bl_info["engine_version"],
            node_name=f".{engine_version}",
            blend_path=directories.blend_engine,
            show_viewport=False,
            is_unique=True,
            unique_nodegroups=[
                #NOTE: also need to update params in add_psy_virgin()
                "s_distribution_projbezline",
                "s_distribution_manual",
                "s_distribution_manual.uuid_equivalence",
                "s_scale_random",
                "s_scale_grow",
                "s_scale_shrink",
                "s_scale_mirror",
                "s_rot_align_y",
                "s_rot_random",
                "s_rot_add",
                "s_rot_tilt",
                "s_abiotic_elev",
                "s_abiotic_slope",
                "s_abiotic_dir",
                "s_abiotic_cur",
                "s_abiotic_border",
                "s_pattern1",
                "s_pattern2",
                "s_pattern3",
                "s_gr_pattern1",
                "s_ecosystem_affinity",
                "s_ecosystem_repulsion",
                "s_ecosystem_density",
                "s_proximity_projbezarea_border",
                "s_proximity_repel1",
                "s_proximity_repel2",
                "s_push_offset",
                "s_push_dir",
                "s_push_noise",
                "s_push_fall",
                "s_wind_wave",
                "s_wind_noise",
                "s_instances_pick_color_textures",
                "s_visibility_cam",
                ],
            )

        #update nodetree versioning information
        version_tuple = bl_info['version'][:2] #'5.1' for ex
        p.addon_version = f"{version_tuple[0]}.{version_tuple[1]}"
        p.blender_version = bpy.app.version_string
        print(f"             -Setting addon/plugin version properties, addon_version:'{p.addon_version}' blender_version:'{p.blender_version}'")

        continue

    #update signal, might avoid crash 
    print(f"   -Refreshing Scene Depsgraph/Viewlayers")

    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()

    #update nodetrees values
    if (psys_needing_upd):
        
        print(f"   -Refreshing All System(s) Properties..")
        
        for p in psys_needing_upd:
            print(f"         -Refreshing : '{p.name}'")
            #refreshing all "s_" settings
            p.properties_nodetree_refresh()
            #also refreshing group, if exists
            if (p.group):
                p.group = p.group
            continue

    print(f"   -Refreshing All System(s) 'texture_ptr' properties")
    ensure_texture_ptr_name()

    #Geo-Scatter 5.3 introduced uuid per psy 5.5 distmeshes
    print(f"   -Versioning: For all Scatter-System(s) Ensuring ScatterObj Uuid")
    print(f"   -Versioning: For all Scatter-System(s) Ensuring Distribution Meshes Ptr")
    print(f"   -Versioning: For all Scatter-System(s) Ensuring Blendfile Uuid")
    
    if (scat_data.blendfile_uuid==0):
        print("     -ERROR: scat_data.blendfile_uuid")
        
    for p in all_psys:
        so = p.scatter_obj
        
        #maybe need to initialize uuid value, recent version implemented new uuid properties
        _ = p.uuid
        
        #Geo-Scatter 5.5 introduced leaving some traces in psy of blendfile
        if (p.blendfile_uuid==0):
            p.blendfile_uuid = scat_data.blendfile_uuid
                
        #Geo-Scatter 5.5 introduced distmesh per scatter_obj for custom distribution methods
        if (so):
            
            #the following are if we didn't set up the distmesh system yet. distmesh was implemented in Geo-Scatter 5.5.0
            if (not so.data.name.startswith(".distmesh")):
                so.data.name = f".distmesh_manual_all:{p.uuid}"
                
            #if the pointers are empty, we assign them
            if (not so.scatter5.distmesh_manual_all):
                so.scatter5.distmesh_manual_all = so.data
            if (not so.scatter5.distmesh_physics):
                so.scatter5.distmesh_physics = bpy.data.meshes.new(f".distmesh_physics:{p.uuid}")
            continue
        
    #restore all psys initial hide
    if (hide_dict):
        for p in all_psys:
            if (p.name in hide_dict):
                val = hide_dict[p.name]
                if (p.hide_viewport!=val):
                    p.hide_viewport = val
            continue
        #also refresh modifiers hide status
        scat_addon.opti_also_hide_mod = scat_addon.opti_also_hide_mod
    
    #update all emitter interfaces data
    print("   -Refresh All Scatter-Emitter(s) Interfaces")

    for e in [e for e in bpy.data.objects if e.scatter5.particle_systems or e.scatter5.particle_interface_items]:
        e.scatter5.particle_interface_refresh()
        continue
    
    #reload manual surface uuid (ensure nothing is regrouped at origin)
    print("   -Ensure manual scatter's surface uuid's")
    
    from . import update_factory
    for p in all_psys:
        update_factory.update_manual_uuid_surfaces(force_update=True, flush_uuid_cache=p.uuid,)

    #bugfix, potentially the camera clipping function can be left undefinitely waiting because of this operator
    if (hasattr(update_factory.update_camera_nodegroup,"is_updating")):
        print("   -Bugfix: update_camera_nodegroup was in a feedback loop?")
        update_factory.update_camera_nodegroup.is_updating = False

    print("   -Conversion Done!\n\n")
    return None 


def fix_scatter_obj(): 

    from .. import utils
    
    print("")
    print(f"GEO-SCATTER: fix_scatter_obj() operation")
    
    #ensure Geo-Scatter collection exists
    print(f"   -Ensuring Geo-Scatter Collection Exist")
    utils.coll_utils.setup_scatter_collections()

    print(f"   -For all Scatter-System(s)")
    
    e_to_refresh = set()
    p_with_no_scatter_obj = set()
    
    for p in bpy.context.scene.scatter5.get_all_psys(search_mode="all", also_linked=True):
        
        emitter = p.id_data
        e_to_refresh.add(emitter)
        elinked = bool(emitter.library)
        
        #first we try to get the scatter obj if he's attached
        so = p.scatter_obj
        
        #if attached scatter_obj is None, then user must've delete it.. there might be a change it's still in datablock somewhere..
        
        if (so is None):
            p_with_no_scatter_obj.add(p)
            print(f"         -Looks like the scatter_obj got deleted. Bummer. Maybe it's still in bpy.data.objects")
            so = bpy.data.objects.get(f"scatter_obj : {p.name}") #might encounter name collision with linked scatter_obj here

        #if scatter_obj is not found, then we create a new one from scratch
                
        if (so is None): 
            print(f"         -Nope, we are creating a new one then..")
            #create new scatter obj
            so = bpy.data.objects.new(f"scatter_obj : {p.name}", bpy.data.meshes.new(f"scatter_obj : {p.name}"), )
            #scatter_obj should never be selectable by user, not needed & outline is bad for performance
            so.hide_select = True
            #scatter_obj should always be locked with null transforms
            utils.create_utils.lock_transform(so)
            #we need to leave traces of the original emitter, in case of dupplication we need to identify the double
            so.scatter5.original_emitter = emitter 
    
        #ensure in psy coll exists
        
        print(f"         -Ensuring that 'psy : {p.name}' Collection exists and is linked in 'Geo-Scatter Geonode'")

        cname = f"psy : {p.name}"
        coll = utils.coll_utils.get_collection_by_name(cname)
        if (coll is None):
            coll = utils.coll_utils.create_new_collection(cname, parent="Geo-Scatter Geonode",)
            
        if (coll.name not in bpy.data.collections["Geo-Scatter Geonode"].children):
            bpy.data.collections["Geo-Scatter Geonode"].children.link(coll)
            
        #ensure scatter obj in psy collection 
        
        if (so not in coll.objects[:]):
            print(f"         -Relinking scatter_obj '{so.name}' in  'psy : {p.name}' collection")
            coll.objects.link(so)
            
        #re-attach scatter_obj to psy 
        
        if (p.scatter_obj is None):
            print(f"         -Re-assigning the scatter_obj that surely got deleted by mistake. Don't do that please.")
            p.scatter_obj = so
                    
        #warning if weird name found?
        
        convention_name = f"scatter_obj : {p.name}"
        if (so.name!=convention_name):
            
            print(f"         -WARNING: scatter_obj '{so.name}' does not respect '{convention_name}' convention. How did that happen?..")
            
            if (convention_name not in bpy.data.objects):
                print(f"         -Renaming scatter_obj to  '{convention_name}' convention.")
                so.name = convention_name
                
        continue 
    
    #might need to refresh interface 
    if (e_to_refresh):
        for e in e_to_refresh:
            if (e.scatter5.is_particle_interface_broken()):
                e.scatter5.particle_interface_refresh()
            continue
        print(f"   -Refreshing related Lister Interface(s)")
            
    #overseer.py might consider this scatter as a dupplicate because previous tracker was cleansed
    if (p_with_no_scatter_obj):
        for p in p_with_no_scatter_obj:
            if (p.name[-1]=="⯎"):
                p.name = p.name[:-1]+"✚"
            continue
    
    return None


class SCATTER5_OT_fix_nodetrees(bpy.types.Operator):
    """fix missing/broken/older geonode engine nodegroups and their modifiers"""

    bl_idname = "scatter5.fix_nodetrees"
    bl_label = translate("Fix Plugin Nodetrees")
    bl_description = translate("Remove the plugin engine nodetrees, and re-apply them to fix any versioning or broken nodes error")
    bl_options = {'INTERNAL', 'UNDO'}

    force_update : bpy.props.BoolProperty(default=False, options={"SKIP_SAVE",},)
    
    def execute(self, context):

        try: 
            fix_nodetrees(force_update=self.force_update)
            
        except:
            print("ERROR: scatter5.fix_nodetrees(): Fallback bpy.ops.scatter5.fix_scatter_obj()")
                  
            fix_scatter_obj()
            fix_nodetrees(force_update=self.force_update)
        
        #remove warning message
        from .. ui.ui_notification import check_for_notifications
        check_for_notifications()

        return {'FINISHED'}


class SCATTER5_OT_fix_scatter_obj(bpy.types.Operator):
    """re-attach potentially broken scatter-obj to the scatter system settings"""

    bl_idname = "scatter5.fix_scatter_obj"
    bl_label = translate("Fix scatter_obj Related Issues")
    bl_description = translate("Fix scatter_obj Related Issues")
    bl_options = {'INTERNAL', 'UNDO'}
    
    def execute(self, context):
            
        fix_scatter_obj()
        fix_nodetrees()
            
        #remove warning message
        from .. ui.ui_notification import check_for_notifications
        check_for_notifications()
        
        return {'FINISHED'}


# class SCATTER5_OT_fix_orphan_psys(bpy.types.Operator):
#     """re-attach potentially broken scatter-obj to the scatter system settings"""

#     bl_idname = "scatter5.fix_orphan_psys"
#     bl_label = translate("Fix orphans scatters")
#     bl_description = translate("Re-attach orphans scatter_obj to a new emitter with default settings. If the orphan is a linked scatter_obj however, we'll delete it for you and you'll need to reimport them, as important data has been lost.")
#     bl_options = {'INTERNAL', 'UNDO'}
    
#     def execute(self, context):
        
#         #get orphans and sort them
        
#         orphans = context.scene.scatter5.get_all_psy_orphans(search_mode="all")
#         normal_orphans, linked_orphans = [o for o in orphans if not o.library], [o for o in orphans if o.library]
        
#         #the linked orphans we just del them. user should re-link the set up he broke..
#         if (linked_orphans):
            
#             for orphan in linked_orphans:
#                 bpy.data.objects.remove(orphan)
        
#         #for normal orphans, create new virgin psys and attach them to orphans
#         if (normal_orphans):
                    
#             #create new empty emitter if needed
#             emitname = context.scene.name+"Orphans"
#             e = context.scene.objects.get(emitname)
#             if (e is None):
#                 from . emitter import add_nonlinear_emitter
#                 e = add_nonlinear_emitter(name=emitname)
                
#             #loop over orphans
#             for orphan in normal_orphans:
                
#                 #define psy name
#                 name = orphan.name
#                 if name.startswith("scatter_obj : "):
#                     name = name.replace("scatter_obj : ","")
                    
#                 #create new default psy
#                 p = e.scatter5.add_psy_virgin(psy_name=f"{name}_repaired", psy_color=(1,1,1,1))
                
#                 #swap scatter_obj mesh data
#                 p.scatter_obj.data = orphan.data
#                 ACTUALLY CANT DO THAT ANYMORE, CARREFUL IF REWORKING THIS CODE
                
#                 #swap scatter_obj modifier engines
                
#                 orpha_ng = None
#                 for m in orphan.modifiers:
#                     #if modifier naming system is new or legacy
#                     if m.name.startswith(("Geo-Scatter Engine","Scatter5 Geonode Engine")):
#                         orpha_ng = m.node_group
#                         break
                
#                 assert orpha_ng is not None
                
#                 for m in p.scatter_obj.modifiers: 
#                     if m.name.startswith("Geo-Scatter Engine"):
#                         m.node_group = orpha_ng
#                         break
                        
#                 #refresh surfaces, a surface pointer might be missing
#                 p.s_surface_method = p.s_surface_method
                
#                 #then remove the origina scatter_obj
#                 bpy.data.objects.remove(orphan)
#                 continue
                
#         #remove warning message
#         from .. ui.ui_notification import check_for_notifications
#         check_for_notifications("T_ORPHAN":True})
        
#         return {'FINISHED'}


#  .oooooo..o                                           o8o      .
# d8P'    `Y8                                           `"'    .o8
# Y88bo.       .ooooo.   .ooooo.  oooo  oooo  oooo d8b oooo  .o888oo oooo    ooo
#  `"Y8888o.  d88' `88b d88' `"Y8 `888  `888  `888""8P `888    888    `88.  .8'
#      `"Y88b 888ooo888 888        888   888   888      888    888     `88..8'
# oo     .d8P 888    .o 888   .o8  888   888   888      888    888 .    `888'
# 8""88888P'  `Y8bod8P' `Y8bod8P'  `V88V"V8P' d888b    o888o   "888"     .8'
#                                                                    .o..P'
#                                                                    `Y8P'


class SCATTER5_OT_popup_security(bpy.types.Operator):

    bl_idname = "scatter5.popup_security"
    bl_label = translate("Information")+":"
    bl_description = ""
    bl_options = {'REGISTER', 'INTERNAL'}

    scatter : bpy.props.BoolProperty(default=False, options={"SKIP_SAVE",},)
    total_scatter : bpy.props.IntProperty(default=-1, options={"SKIP_SAVE",},) #if -1, will compute the amount accurately

    poly : bpy.props.BoolProperty(default=False, options={"SKIP_SAVE",},)

    emitter : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    psy_name_00 : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    psy_name_01 : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    psy_name_02 : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    psy_name_03 : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    psy_name_04 : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    psy_name_05 : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    psy_name_06 : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    psy_name_07 : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    psy_name_08 : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    psy_name_09 : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    psy_name_10 : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    psy_name_11 : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    psy_name_12 : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    psy_name_13 : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    psy_name_14 : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    psy_name_15 : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    psy_name_16 : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    psy_name_17 : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    psy_name_18 : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    psy_name_19 : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    #biome with more than 20 layers? get outta here

    #scatter
    s_visibility_hide_system : bpy.props.BoolProperty(default=True, options={"SKIP_SAVE",},)
    s_visibility_hide_system_False : bpy.props.BoolProperty(default=False, options={"SKIP_SAVE",},)
    s_visibility_view_allow : bpy.props.BoolProperty(default=False, options={"SKIP_SAVE",},)
    s_visibility_cam_allow : bpy.props.BoolProperty(default=False, options={"SKIP_SAVE",},)

    #poly
    s_set_bounding_box : bpy.props.BoolProperty(default=True, options={"SKIP_SAVE",},)
    s_display_allow : bpy.props.BoolProperty(default=False, options={"SKIP_SAVE",},)

    def invoke(self, context, event):
    
        emitter = bpy.data.objects[self.emitter]

        #gather context psys passed
        self.psys = []
        for i in range(20): 
            name = getattr(self,f"psy_name_{i:02}")
            if (name!=""):
                p = emitter.scatter5.particle_systems[name]
                self.psys.append(p)
            continue
        
        #make sure scatters are hidden
        if (self.scatter and self.s_visibility_hide_system):
            for p in self.psys:
                p.hide_viewport = True
                
        #count total amount of pts created
        if (self.scatter and (self.total_scatter==-1)):
            self.total_scatter = 0
            for p in self.psys:
                self.total_scatter += p.get_scatter_count(state="render") #this operation might take a long time when reaching 10M+ instances

        #invoke interface
        return context.window_manager.invoke_props_dialog(self)

    @classmethod
    def description(cls, context, properties): 
        return properties.description
        
    def draw(self, context):

        from .. ui import ui_templates

        layout = self.layout

        box, is_open = ui_templates.box_panel(layout,         
            panelopen_propname="ui_dialog_secur", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_dialog_secur");BOOL_VALUE(1)
            panel_icon="FAKE_USER_ON",
            panel_name=translate("Security Warnings"),
            )
        if is_open:

            if (self.scatter):

                txtblock = box.column()
                txtblock.scale_y = 0.9
                txt = txtblock.row()
                txt.label(text=translate("Heavy Scatter Detected!"), icon="INFO",)
                word_wrap(layout=txtblock, alignment="LEFT", max_char=53, active=True, string=translate("This scatter generated a total of")+f" {self.total_scatter:,} "+translate("instances, more than the security threshold!\nPlease define the security measures below."),)
                
                opts = box.column()
                opts.scale_y = 0.9
                opts.separator(factor=0.4)

                #hide?
                if (self.s_visibility_view_allow or self.s_visibility_cam_allow):
                    prop = opts.row()                    
                    prop.enabled = False
                    prop.prop(self, "s_visibility_hide_system_False", text=translate("Hide the scatter-system(s)"),)
                else: 
                    opts.prop(self, "s_visibility_hide_system", text=translate("Hide the scatter-system(s)"),)

                #viewport % optimization?
                opts.prop(self, "s_visibility_view_allow", text=translate("Hide 90% of the instances"),)

                #camera optimization?
                prop = opts.row()
                prop.enabled = (context.scene.camera is not None)
                prop.prop(self, "s_visibility_cam_allow", text=translate("Hide instances invisible to camera"),)

                opts.separator(factor=0.4)

            if (self.poly):

                txtblock = box.column()
                txtblock.scale_y = 0.9
                txt = txtblock.row()
                txt.label(text=translate("Heavy Object Detected!"), icon="INFO",)
                word_wrap(layout=txtblock, alignment="LEFT", max_char=53, active=True, string=translate("Object(s) in your scatter had more polygons than the security threshold!\nPlease define the security measures below."),)

                opts = box.column()
                opts.scale_y = 0.9
                opts.separator(factor=0.4)
                
                #object bounding box?
                opts.prop(self, "s_set_bounding_box", text=translate("Set object(s) “Bounds”"),)

                #display as?
                opts.prop(self, "s_display_allow", text=translate("Set scatter(s) “Display As”"),)

                opts.separator(factor=0.4)

            txtblock = box.column()
            txtblock.scale_y = 0.9
            txt = txtblock.row()
            txt.label(text=translate("Did you know?"), icon="INFO",)
            word_wrap(layout=txtblock, alignment="LEFT", max_char=53, active=True, string=translate("Displaying a lot of polygons in the viewport can freeze blender! If you do not wish to see this menu, feel free to disable or change the security thresholds options located in the 'Create' panel 'On Creation' setting menu.\n"),)

        return None

    def execute(self, context):

        if (self.poly):

            if (not self.s_set_bounding_box):
                for p in self.psys:
                    for ins in p.get_instance_objs():
                        ins.display_type = 'TEXTURED'

            if (self.s_display_allow):
                for p in self.psys:
                    if (not p.s_display_allow):
                        p.s_display_allow = True
                        p.s_display_method = "cloud"

        if (self.scatter):

            if (self.s_visibility_view_allow):
                for p in self.psys:
                    p.s_visibility_view_allow = True 
                    p.s_visibility_view_percentage = 90

            if (self.s_visibility_cam_allow):
                for p in self.psys:
                    p.s_visibility_cam_allow = True
                    p.s_visibility_camclip_allow = True
                    p.s_visibility_camclip_cam_boost_xy = (0.1,0.1)
                    p.s_visibility_camdist_allow = True

            if (self.s_visibility_cam_allow or self.s_visibility_view_allow or (not self.s_visibility_hide_system)):
                for p in self.psys:
                    p.hide_viewport = False

        return {'FINISHED'}


class SCATTER5_OT_linked_scatter_manipulation(bpy.types.Operator):

    bl_idname      = "scatter5.linked_scatter_manipulation"
    bl_label       = translate("Override or Delete a linked scatter")
    bl_description = translate("Override or Delete a linked scatter")
    bl_options     = {'INTERNAL', 'UNDO'}
    
    option : bpy.props.StringProperty(options={'SKIP_SAVE'}) #'override'/'delete'
    emitter_session_uid : bpy.props.IntProperty(options={'SKIP_SAVE'})

    @classmethod
    def description(cls, context, properties): 
        if (properties.option=='delete'):
            return translate("Remove all linked scatter(s) related to this emitter from this .blend")
        if (properties.option=='make_all_local'):
            return translate("Make the linked scatter(s) of this scene all local. This action will remove the link, it will effectively make all scatters editable. This action is definitive, any links will be lost.")
    
    def execute(self, context):
        
        emitter = get_from_uid(self.emitter_session_uid)
        assert emitter is not None
        
        match self.option:
                
            case 'delete':
                
                #remove any scatter object related to this scene
                
                pnames = set()
                
                with context.scene.scatter5.factory_update_pause(event=True):
                    for p in emitter.scatter5.particle_systems:
                        pnames.add(p.name)
                        if p.scatter_obj: 
                            bpy.data.objects.remove(p.scatter_obj)
                    bpy.data.objects.remove(emitter)
                        
                #clear leftover collections?
                
                from .. scattering.instances import collection_users
                
                for n in pnames:
                    
                    col = bpy.data.collections.get(f"psy : {n}")
                    if (col is not None) and (len(col.objects)==0):
                        bpy.data.collections.remove(col)
                        
                    col = bpy.data.collections.get(f"ins_col : {n}")
                    if (col is not None) and (len(collection_users(col))==0):
                        bpy.data.collections.remove(col)
                                        
            case 'make_all_local':
                
                pass
            
                # lib = emitter.library
                # ems = context.scene.scatter5.get_all_emitters(search_mode="all", also_linked=True)
                # linked_ems = [e for e in ems if e.library==lib]
                # localizedp = set()
                
                # for e in linked_ems:
                    
                #     # when we make a link local, object is being replaced in place by a new one
                #     # so we identify the new one with the viewlayer.active
                    
                #     if (e in context.view_layer.objects[:]):
                        
                #         #FIRST let's make emitter local 
                        
                #         #set as active
                #         old_e = e
                #         context.view_layer.objects.active = old_e
                        
                #         #get rid of oe
                #         for p in old_e.scatter5.particle_systems:
                #             if (p.scatter_obj):
                #                 p.scatter_obj.scatter5.original_emitter = None
                                
                #         #make local, this will replace the object data
                #         old_e.make_local()
                        
                #         #find what's replaced it
                #         new_e = bpy.context.object
                        
                #         #delete old linked data
                #         bpy.data.objects.remove(old_e)
                        
                #         #THEN make their scatter_obj
                        
                #         for p in new_e.scatter5.particle_systems:
                #             if (p.scatter_obj):
                                
                #                 #make scatter_obj local
                #                 p.scatter_obj.make_local()
                #                 p.scatter_obj.data.make_local()
                                
                #                 #update original_emitter information
                #                 p.scatter_obj.scatter5.original_emitter = new_e
                                
                #                 #save that for later
                #                 localizedp.add(p)
                #         continue
                    
                #     else:
                #         print(f"couldn't make local: {e.name},{e.library.name}")
                        
                # #THEN also make all nodes ng local. making a linked ng local will make it local to all instance of tha ng unfortunately, so this method is easier

                # for ng in  bpy.data.node_groups:
                #     if ng.name.startswith(".S "):
                #         if (ng.library==lib):
                #             ng.make_local()
                    
                # #also refresh all surface methods, we might have
                # for p in localizedp:
                #     p.s_surface_method = p.s_surface_method
                #     p.s_surface_method = p.s_surface_method
                                
        return {'FINISHED'}
    

#   .oooooo.   oooo
#  d8P'  `Y8b  `888
# 888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
# 888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
# 888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
# `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#  `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'



classes = (
    
    SCATTER5_OT_reset_settings,
    SCATTER5_OT_disable_main_settings,
    SCATTER5_OT_clean_unused_import_data,
    SCATTER5_OT_batch_toggle,
    SCATTER5_OT_batch_randomize,
    SCATTER5_OT_batch_set_space,
    SCATTER5_OT_batch_bounding_box,
    SCATTER5_OT_fix_nodetrees,
    SCATTER5_OT_fix_scatter_obj,
    # SCATTER5_OT_fix_orphan_psys,
    SCATTER5_OT_property_coef,
    SCATTER5_OT_popup_security,
    SCATTER5_OT_linked_scatter_manipulation,
    
    )
