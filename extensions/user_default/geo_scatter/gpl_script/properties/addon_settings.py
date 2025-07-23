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
#       .o.             .o8        .o8                        ooooooooo.                       .o88o.
#      .888.           "888       "888                        `888   `Y88.                     888 `"
#     .8"888.      .oooo888   .oooo888   .ooooo.  ooo. .oo.    888   .d88' oooo d8b  .ooooo.  o888oo
#    .8' `888.    d88' `888  d88' `888  d88' `88b `888P"Y88b   888ooo88P'  `888""8P d88' `88b  888
#   .88ooo8888.   888   888  888   888  888   888  888   888   888          888     888ooo888  888
#  .8'     `888.  888   888  888   888  888   888  888   888   888          888     888    .o  888
# o88o     o8888o `Y8bod88P" `Y8bod88P" `Y8bod8P' o888o o888o o888o        d888b    `Y8bod8P' o888o
#
#####################################################################################################


import bpy

import os
import json
from mathutils import Vector,Color

from .. ui import ui_addon #need to draw addon prefs from here..

from .. translations import translate
from .. resources import directories

from .. utils import path_utils 


def upd_tab_name(self,context):
    """dynamically change category & reload some panel upon update""" 

    from .. ui import USER_TABS_CLS

    for cls in reversed(USER_TABS_CLS):
        if (cls.is_registered):
            bpy.utils.unregister_class(cls)

    for cls in USER_TABS_CLS:
        if (not cls.is_registered):
            cls.bl_category = self.tab_name
            bpy.utils.register_class(cls)

    return None 

def upd_blend_folder(self,context):

    self.high_nest = False  

    if (self.blend_folder.startswith("//")):
        self.blend_folder = bpy.path.abspath(self.blend_folder)
    
    if (not os.path.exists(self.blend_folder)):
        print("ERROR: upd_blend_folder(): the selected folder do not exists")
        print(self.blend_folder)
        return None

    folds = path_utils.get_direct_folder_paths(self.blend_folder)

    if (folds is None): 
        print("ERROR: upd_blend_folder(): fct did not find any get_direct_folder_paths()")
        return None

    for f in folds:
        if len(path_utils.get_direct_folder_paths(f)):
            self.high_nest = True

    return None

class SCATTER5_PR_blend_environment_paths(bpy.types.PropertyGroup):
    """addon_prefs().blend_environment_paths[x]"""

    name : bpy.props.StringProperty()

    blend_folder : bpy.props.StringProperty(
        subtype="DIR_PATH",
        description=translate("When creating a biome, our plugin will search for blends in your _asset_library_ or in the given path"),
        update=upd_blend_folder
        )
    
    high_nest : bpy.props.IntProperty()


class SCATTER5_AddonPref(bpy.types.AddonPreferences):
    """addon_prefs() = bpy.context.preferences.addons[__package__].preferences from __init__.py"""
    
    from ... import __package__ as base_package
    bl_idname = base_package
    
    # 88        db    88b 88  dP""b8 88   88    db     dP""b8 888888 
    # 88       dPYb   88Yb88 dP   `" 88   88   dPYb   dP   `" 88__   
    # 88  .o  dP__Yb  88 Y88 Yb  "88 Y8   8P  dP__Yb  Yb  "88 88""   
    # 88ood8 dP""""Yb 88  Y8  YboodP `YbodP' dP""""Yb  YboodP 888888 

    from .. translations import ENUM_LANG_ITEMS, ACTIVE_LANG, upd_language
    language : bpy.props.EnumProperty(
        name=translate("Choose your plugin language"),
        description=translate("Choose language based on .csv files loaded in the plugin 'translations' folder"),
        default=ACTIVE_LANG,
        items=ENUM_LANG_ITEMS,
        update=upd_language,
        ) 
    
    # 88b 88      88""Yb    db    88b 88 888888 88        88b 88    db    8b    d8 888888
    # 88Yb88 ___  88__dP   dPYb   88Yb88 88__   88        88Yb88   dPYb   88b  d88 88__
    # 88 Y88 """  88"""   dP__Yb  88 Y88 88""   88  .o    88 Y88  dP__Yb  88YbdP88 88""
    # 88  Y8      88     dP""""Yb 88  Y8 888888 88ood8    88  Y8 dP""""Yb 88 YY 88 888888

    from ... __init__ import bl_info
    tab_name : bpy.props.StringProperty(
        name="",
        default=bl_info["name"].replace('®',''),
        update=upd_tab_name,
        )

    # 8b    d8    db    88""Yb 88  dP 888888 888888 
    # 88b  d88   dPYb   88__dP 88odP  88__     88   
    # 88YbdP88  dP__Yb  88"Yb  88"Yb  88""     88   
    # 88 YY 88 dP""""Yb 88  Yb 88  Yb 888888   88   

    fetch_automatic_allow : bpy.props.BoolProperty(
        name="",
        default=True,
        )
    fetch_automatic_daycount : bpy.props.IntProperty(
        name="",
        default=6,
        min=1, max=31,
        )

    # 88     88 88""Yb 88""Yb    db    88""Yb Yb  dP
    # 88     88 88__dP 88__dP   dPYb   88__dP  YbdP
    # 88  .o 88 88""Yb 88"Yb   dP__Yb  88"Yb    8P
    # 88ood8 88 88oodP 88  Yb dP""""Yb 88  Yb  dP

    library_path : bpy.props.StringProperty(
        name="",
        default= directories.lib_default,
        subtype="DIR_PATH",
        )
    blend_environment_search_cache_system : bpy.props.BoolProperty(
        name=translate("Use Path Caching System"),
        description=translate("The Biome system will cache the .blend paths it finds in your scatter-library when searching a biome, avoiding redundant searches. A cache file will be stored alongside your biome file"),
        default=True,
        )
    blend_environment_search_depth : bpy.props.IntProperty(
        name=translate("Recursive Search Depth"),
        description=translate("When the Biome system search for a .blend in the list of priority custom paths or in the list of asset-libraries paths, the system will recursively search in all subfolders contained in the path until achieving the selected level of folder depth. Once reach, the search won't go deeper"),
        min=1,
        default=3,
        soft_max=7,
        )
    blend_environment_scatterlib_allow : bpy.props.BoolProperty(
        name="",
        default=True,
        )
    blend_environment_path_allow : bpy.props.BoolProperty(
        name="",
        default=False,
        )
    blend_environment_path_asset_browser_allow : bpy.props.BoolProperty(
        name="",
        default=True,
        )
    blend_environment_paths : bpy.props.CollectionProperty(type=SCATTER5_PR_blend_environment_paths)
    blend_environment_paths_idx : bpy.props.IntProperty()

    # 888888 8b    d8 88 888888     8b    d8 888888 888888 88  88  dP"Yb  8888b.
    # 88__   88b  d88 88   88       88b  d88 88__     88   88  88 dP   Yb  8I  Yb
    # 88""   88YbdP88 88   88       88YbdP88 88""     88   888888 Yb   dP  8I  dY
    # 888888 88 YY 88 88   88       88 YY 88 888888   88   88  88  YbodP  8888Y"

    emitter_method : bpy.props.EnumProperty(
        default= "pointer",
        name=translate("Change Emitter Method"),
        description=translate("Choose how to swap the emitter on the N panel headers"),
        items=(("pointer",translate("Pointer") ,translate("Display the emitter as an object-pointer property"),"EYEDROPPER",1 ),
               ("menu",translate("Menu") ,translate("Use a dropdown menu with many emitter options and operators"),"TOPBAR",2 ),
               ("pin",translate("Pin") ,translate("The active object will automatically be designated as an emitter, except if pinned"),"PINNED",3 ),
              ),
        ) 
    
    #  dP"Yb  88""Yb 888888 88 8b    d8 88 8888P    db    888888 88  dP"Yb  88b 88 
    # dP   Yb 88__dP   88   88 88b  d88 88   dP    dPYb     88   88 dP   Yb 88Yb88 
    # Yb   dP 88"""    88   88 88YbdP88 88  dP    dP__Yb    88   88 Yb   dP 88 Y88 
    #  YbodP  88       88   88 88 YY 88 88 d8888 dP""""Yb   88   88  YbodP  88  Y8 

    opti_also_hide_mod : bpy.props.BoolProperty(
        name="",
        default=False,
        description=translate("When you click on the 'hide viewport'/'hide render' button of a scatter it will set the viewport/render hide status of the scatter_obj accordingly. If you enable this option, it will also change the hide status of the scatter_obj geometry node modifier which can lead to further engine optimizations"),
        update=lambda s,c: [{setattr(p,"hide_viewport",p.hide_viewport):setattr(p,"hide_render",p.hide_render) for p in bpy.context.scene.scatter5.get_all_psys(search_mode="all", also_linked=True)},None][1], #send refresh signal
        )

    # 88 88b 88 888888 888888 88""Yb 888888    db     dP""b8 888888
    # 88 88Yb88   88   88__   88__dP 88__     dPYb   dP   `" 88__
    # 88 88 Y88   88   88""   88"Yb  88""    dP__Yb  Yb      88""
    # 88 88  Y8   88   888888 88  Yb 88     dP""""Yb  YboodP 888888

    ui_library_item_size : bpy.props.FloatProperty(
        name=translate("Item Size"),
        default=7.0,
        min=5,
        max=15,
        )
    ui_library_typo_limit : bpy.props.IntProperty(
        name=translate("Typo Limit"),
        default=40,
        min=4,
        max=100,
        )
    ui_library_adaptive_columns : bpy.props.BoolProperty(
        name=translate("Adaptive Columns"),
        default=True,
        )
    ui_library_columns : bpy.props.IntProperty(
        name=translate("Number of Columns"),
        default=4,
        min=1,
        max=40,
        soft_max=10,
        )
    ui_lister_scale_y : bpy.props.FloatProperty(
        name=translate("Row Height"),
        default=1.2,
        min=0.1,
        max=5,
        )
    ui_use_dark_box : bpy.props.BoolProperty(
        default=False,
        )
    ui_show_boxpanel_icon : bpy.props.BoolProperty(
        default=False,
        )
    ui_selection_y : bpy.props.FloatProperty(
        default=0.86,
        soft_min=0.7,
        max=1.25,
        )
    ui_boxpanel_separator : bpy.props.FloatProperty(
        default=1.0,
        max=10,
        )
    ui_boxpanel_height : bpy.props.FloatProperty(
        default=1.2,
        min=0.03, max=4,
        )
    ui_bool_use_standard : bpy.props.BoolProperty(
        default=False,
        )
    ui_bool_use_arrow_openclose : bpy.props.BoolProperty(
        default=True,
        )
    ui_bool_use_iconcross : bpy.props.BoolProperty(
        default=False,
        )
    ui_bool_indentation : bpy.props.FloatProperty(
        default=0.07,
        min=-0.2, max=0.2,
        )
    ui_word_wrap_max_char_factor : bpy.props.FloatProperty(
        default=1.0,
        soft_min=0.3,
        soft_max=3,
        )
    ui_word_wrap_y : bpy.props.FloatProperty(
        default=0.8,
        soft_min=0.1,
        soft_max=3,
        )
    ui_apply_scale_warn : bpy.props.BoolProperty(
        default=True,
        )
    
    # 8b    d8    db    88b 88 88   88    db    88         888888 88  88 888888 8b    d8 888888 
    # 88b  d88   dPYb   88Yb88 88   88   dPYb   88           88   88  88 88__   88b  d88 88__   
    # 88YbdP88  dP__Yb  88 Y88 Y8   8P  dP__Yb  88  .o       88   888888 88""   88YbdP88 88""   
    # 88 YY 88 dP""""Yb 88  Y8 `YbodP' dP""""Yb 88ood8       88   88  88 888888 88 YY 88 888888 
    
    from .. manual import config
    manual_theme : bpy.props.PointerProperty(
        type=config.SCATTER5_PR_preferences_theme,
        )
    manual_use_overlay : bpy.props.BoolProperty(
        name="Use Overlay",
        default=True,
        )
    manual_show_infobox : bpy.props.BoolProperty(
        name="Show Infobox",
        default=True,
        )
    
    # 8888b.  888888 88""Yb 88   88  dP""b8
    #  8I  Yb 88__   88__dP 88   88 dP   `"
    #  8I  dY 88""   88""Yb Y8   8P Yb  "88
    # 8888Y"  888888 88oodP `YbodP'  YboodP

    debug_interface : bpy.props.BoolProperty(
        default=False,
        )
    debug : bpy.props.BoolProperty(
        default=False,
        )
    debug_depsgraph : bpy.props.BoolProperty(
        default=False,
        )

    # 8888b.  88""Yb    db    Yb        dP 
    #  8I  Yb 88__dP   dPYb    Yb  db  dP  
    #  8I  dY 88"Yb   dP__Yb    YbdPYbdP   
    # 8888Y"  88  Yb dP""""Yb    YP  YP     
    #drawing part in ui module
    
    def draw(self,context):
        layout = self.layout
        ui_addon.draw_addon(self, layout, context,) #need to draw addon prefs from here..


#  .oooooo..o                                       .oooooo..o               .       .    o8o                                  
# d8P'    `Y8                                      d8P'    `Y8             .o8     .o8    `"'                                  
# Y88bo.       .oooo.   oooo    ooo  .ooooo.       Y88bo.       .ooooo.  .o888oo .o888oo oooo  ooo. .oo.    .oooooooo  .oooo.o 
#  `"Y8888o.  `P  )88b   `88.  .8'  d88' `88b       `"Y8888o.  d88' `88b   888     888   `888  `888P"Y88b  888' `88b  d88(  "8 
#      `"Y88b  .oP"888    `88..8'   888ooo888           `"Y88b 888ooo888   888     888    888   888   888  888   888  `"Y88b.  
# oo     .d8P d8(  888     `888'    888    .o      oo     .d8P 888    .o   888 .   888 .  888   888   888  `88bod8P'  o.  )88b 
# 8""88888P'  `Y888""8o     `8'     `Y8bod8P'      8""88888P'  `Y8bod8P'   "888"   "888" o888o o888o o888o `8oooooo.  8""888P' 
#                                                                                                          d"     YD           
#                                                                                                          "Y88888P'           


class SCATTER5_OT_export_addon_settings(bpy.types.Operator):

    bl_idname  = "scatter5.export_addon_settings"
    bl_label   = translate("Choose Folder")
    bl_description = translate("Export your addon settings to a '.geoscattersettings' file")
    bl_options = {'REGISTER', 'INTERNAL'}
    
    filepath : bpy.props.StringProperty()
    directory : bpy.props.StringProperty()
    filename : bpy.props.StringProperty(options={"SKIP_SAVE",})

    @classmethod
    def get_settings_dict(self):
        """get a dictionary ready to be dumped from addon_prefs()"""
        
        from ... __init__ import addon_prefs
        settings = {}

        #get addon_prefs()
        
        def getprops(prefs, props_dict):
            """recur fct"""
            
            for prop_name in prefs.bl_rna.properties.keys():
                
                if (prop_name in {'rna_type','bl_idname','language'}):
                    continue
                
                value = getattr(prefs, prop_name)
                
                if isinstance(value, (str, int, float, bool)):
                    props_dict[prop_name] = value
                
                elif isinstance(value, (Vector,Color,bpy.types.bpy_prop_array)):
                    props_dict[prop_name] = value[:]
                
                elif isinstance(value, bpy.types.EnumPropertyItem):
                    props_dict[prop_name] = value.identifier
                    
                elif (prop_name=='manual_theme'): #recur for pointer property preferences.manual_theme
                    props_dict[prop_name] = {}
                    getprops(value, props_dict[prop_name])
                    
                elif (prop_name=='blend_environment_paths'):
                    props_dict[prop_name] = [itm.blend_folder for itm in value]
                
                continue
            
            return None
        
        getprops(addon_prefs(), settings)
        
        # NOTE: shortcuts --------------------------------------- >>> v2
        from ..manual import keys
        # get IDs of everything i need, so operators defined here and there..
        ids_universal = ['scatter5.define_add_psy', 'scatter5.quick_lister', ]
        # and scrape keyconfig definitions in manual so i have one spot for this
        ids_manual = list(set([i[0] for i in keys.op_key_defs[2]['items']]))
        ids_gestures = list(set([i[0] for i in keys.mod_key_defs[2]['items']]))
        
        def kmi_to_data(kmi):
            # NOTE: it is a bit more complicated than that, see `modules/bl_keymap_utils/io.py` >> `keyconfig_export_as_data`
            # NOTE: there is some more logic behind.. some settings overide other and exporter adjust that. here is just small portion of it
            args = {
                'type': kmi.type,
                'value': kmi.value,
            }
            if(kmi.key_modifier != 'NONE'):
                args['key_modifier'] = kmi.key_modifier
            if(kmi.repeat):
                args['repeat'] = kmi.repeat
            ls = [
                'any',
                'shift',
                'ctrl',
                'alt',
                'oskey',
            ]
            for k in ls:
                v = getattr(kmi, k)
                if(v != 0):
                    args[k] = v
            props = {
                'active': kmi.active,
                'properties': [],
            }
            for n in kmi.properties.bl_rna.properties.keys():
                if(n != 'rna_type'):
                    v = getattr(kmi.properties, n)
                    props['properties'].append((n, v, ))
            if(not len(props['properties'])):
                del props['properties']
            if(kmi.direction != 'ANY'):
                props['direction'] = kmi.direction
            return (kmi.idname, args, props, )
        
        # NOTE: reading from `bpy.context.window_manager.keyconfigs.user.keymaps` so i get final key combos
        items = []
        km = bpy.context.window_manager.keyconfigs.user.keymaps["Window"]
        for n in ids_universal:
            ok = False
            for kmi in km.keymap_items:
                if(kmi.idname == n):
                    items.append(kmi_to_data(kmi))
                    ok = True
            if(not ok):
                # there is no such item, user must have deleted it from keyconfig, use empty and disabled instead as default value
                items.append((n, {'type': 'NONE', 'value': 'PRESS', }, {'active': False, }, ))
        # WATCH: lucky these two are in one spot, if that ever changes, this needs to be updated
        universal_defs = ("Window", {"space_type": 'EMPTY', "region_type": 'WINDOW', }, {"items": items, }, )
        
        items = []
        km = bpy.context.window_manager.keyconfigs.user.keymaps['3D View']
        for n in ids_manual:
            ok = False
            for kmi in km.keymap_items:
                if(kmi.idname == n):
                    items.append(kmi_to_data(kmi))
                    ok = True
            if(not ok):
                # there is no such item, user must have deleted it from keyconfig, use empty and disabled instead..
                items.append((n, {'type': 'NONE', 'value': 'PRESS', }, {'active': False, }, ))
        manual_defs = (keys.op_key_defs[0], keys.op_key_defs[1], {"items": items, }, )
        
        items = []
        km = bpy.context.window_manager.keyconfigs.user.keymaps['3D View']
        for n in ids_gestures:
            ok = False
            for kmi in km.keymap_items:
                if(kmi.idname == n):
                    items.append(kmi_to_data(kmi))
                    ok = True
            if(not ok):
                # there is no such item, user must have deleted it from keyconfig, use empty and disabled instead..
                items.append((n, {'type': 'NONE', 'value': 'PRESS', }, {'active': False, }, ))
        gestures_defs = (keys.mod_key_defs[0], keys.mod_key_defs[1], {"items": items, }, )
        
        settings["shortcuts"] = [
            universal_defs,
            manual_defs,
            gestures_defs,
        ]
        # NOTE: shortcuts --------------------------------------- <<< v2
        
        return settings

    def invoke(self, context, event):

        self.filename = "myfile.geoscattersettings"
        context.window_manager.fileselect_add(self)
        
        return {'RUNNING_MODAL'}  

    def execute(self, context):
        
        if (not os.path.exists(self.directory)):
            bpy.ops.scatter5.popup_menu(msgs=translate("The chosen directory does not exist"), title=translate("Warning"),icon="ERROR",)
            return {'FINISHED'}
        
        if (self.filename==""):
            self.filename = "myfile.geoscattersettings"
        elif (not self.filename.endswith(".geoscattersettings")):
            self.filename += ".geoscattersettings"
            
        with open(os.path.join(self.directory,self.filename),'w') as f:
            settings = self.get_settings_dict()
            json.dump(settings, f, indent=4)

        return {'FINISHED'}
    
    
class SCATTER5_OT_import_addon_settings(bpy.types.Operator):

    bl_idname  = "scatter5.import_addon_settings"
    bl_label   = translate("Choose File")
    bl_description = translate("Import your addon settings from a selected '.geoscattersettings' file. Warning, this option will overwrite all your Geo-Scatter addon preferences.")
    bl_options = {'REGISTER', 'INTERNAL'}
    
    filepath : bpy.props.StringProperty()
                            
    def set_settings_from_dict(self, settings):
        
        from ... __init__ import addon_prefs
        
        def setprops(prefs, props_dict):
            """recur fct"""
            
            for prop_name, value in props_dict.items():
                
                if (not hasattr(prefs, prop_name)):
                    continue
                
                match prop_name:
                    
                    case 'manual_theme':
                        #recur for pointer property preferences.manual_theme
                        setprops(prefs.manual_theme, value)
                    
                    case 'blend_environment_paths':
                        prefs.blend_environment_paths.clear()
                        for path in value:
                            n = prefs.blend_environment_paths.add()
                            setattr(n,"blend_folder",path)
                        
                    case str():
                        setattr(prefs, prop_name, value)
                    
                continue
                    
            return None
        
        setprops(addon_prefs(), settings)
        
        # NOTE: shortcuts --------------------------------------- >>> v2
        universal_defs, manual_defs, gestures_defs = settings["shortcuts"]
        
        '''
        def process_defs(defs, is_gestures=False, ):
            r = []
            km_name, km_args, km_content = defs
            # NOTE: !!
            kc = bpy.context.window_manager.keyconfigs.addon
            km = kc.keymaps.new(km_name, **km_args)
            kc_write = bpy.context.window_manager.keyconfigs.user
            km_write = kc_write.keymaps.new(km_name, **km_args)
            km_items = km_content["items"]
            for kmi_idname, kmi_args, kmi_data in km_items:
                # check if idname is already in config somewhere, if not it must be user manually removed item or too has been renamed in this version, in that case, skip..
                if(kmi_idname in km.keymap_items.keys()):
                    # it exists, so i am safe to say i can remove old
                    if(is_gestures):
                        # i need to use different strategy, gestures are defined as single idname with multiple entries
                        # i need to identify correct entry first..
                        gesture = None
                        for k, v in kmi_data['properties']:
                            if(k == 'gesture'):
                                gesture = v
                                break
                        if(gesture is None):
                            # this should not happen, but lets not interrupt process
                            continue
                        old = None
                        for kmi in km.keymap_items:
                            if(kmi.idname == kmi_idname):
                                try:
                                    if(kmi.properties.gesture == gesture):
                                        old = kmi
                                        break
                                except Exception as e:
                                    pass
                        if(old is None):
                            # not found..
                            continue
                        # km.keymap_items.remove(old)
                    else:
                        old = km.keymap_items[kmi_idname]
                        # km.keymap_items.remove(old)
                    # # add add new. on top..
                    # kmi_args['head'] = True
                    kmi = km_write.keymap_items.new(kmi_idname, **kmi_args)
                    if(kmi_data is not None):
                        if(not kmi_data.get("active", True)):
                            kmi.active = False
                    kmi_props_data = kmi_data.get("properties", None)
                    if(kmi_props_data is not None):
                        for prop, value in kmi_props_data:
                            setattr(kmi.properties, prop, value)
                    r.append((km, kmi, ))
                else:
                    # does not exist, use the one that has been created at addon activation
                    pass
            return r
        '''
        
        def process_defs(defs, is_gestures=False, ):
            km_name, km_args, km_content = defs
            # NOTE: write to `user` and by modifying existing items, not replacing with new. if they are replaced, they won't work
            kc = bpy.context.window_manager.keyconfigs.user
            km = kc.keymaps.new(km_name, **km_args)
            km_items = km_content["items"]
            for kmi_idname, kmi_args, kmi_data in km_items:
                if(kmi_idname in km.keymap_items.keys()):
                    if(is_gestures):
                        gesture = None
                        for k, v in kmi_data['properties']:
                            if(k == 'gesture'):
                                gesture = v
                                break
                        if(gesture is None):
                            continue
                        found_item = None
                        for kmi in km.keymap_items:
                            if(kmi.idname == kmi_idname):
                                try:
                                    if(kmi.properties.gesture == gesture):
                                        found_item = kmi
                                        break
                                except Exception as e:
                                    pass
                        if(found_item is None):
                            # not found..
                            continue
                        kmi = found_item
                    else:
                        kmi = km.keymap_items[kmi_idname]
                    # NOTE: now, i need to write everything prop by prop, i cannot create new item and add. it will not work
                    defs = {
                        'active': False,
                        'alt': 0,
                        'any': False,
                        'ctrl': 0,
                        'direction': 'ANY',
                        'key_modifier': 'NONE',
                        'map_type': 'KEYBOARD',
                        'oskey': 0,
                        'repeat': False,
                        'shift': 0,
                        'type': 'NONE',
                        'value': 'NOTHING',
                    }
                    defs.update(kmi_args)
                    # NOTE: properties are read only
                    # properties = kmi_data.get('properties', None)
                    if('properties' in kmi_data.keys()):
                        del kmi_data['properties']
                    defs.update(kmi_data)
                    # write that..
                    for k, v in defs.items():
                        setattr(kmi, k, v)
                else:
                    # missing..
                    pass
        
        universal_keymaps = process_defs(universal_defs)
        manual_keymaps = process_defs(manual_defs)
        gestures_keymaps = process_defs(gestures_defs, is_gestures=True, )
        
        '''
        # now i modified keymap, but i need to store items in original places or i get error on quit
        # manual is easy, i use the same format, just clear/extend
        from ..manual import keys
        keys.addon_keymaps.clear()
        keys.addon_keymaps.extend(manual_keymaps)
        keys.addon_keymaps.extend(gestures_keymaps)
        
        # other places are a bit more complicated and only items is stored
        from ..scattering import add_psy
        add_psy.quickscatter_keymaps.clear()
        for _, kmi in universal_keymaps:
            if(kmi.idname == 'scatter5.define_add_psy'):
                add_psy.quickscatter_keymaps.append(kmi)
        from ..ui import ui_system_list
        ui_system_list.quicklister_keymaps.clear()
        for _, kmi in universal_keymaps:
            if(kmi.idname == 'scatter5.quick_lister'):
                ui_system_list.quicklister_keymaps.append(kmi)
        '''
        
        # NOTE: shortcuts --------------------------------------- <<< v2
        
        return None

    def invoke(self, context, event):

        context.window_manager.fileselect_add(self)
        
        return {'RUNNING_MODAL'}

    def execute(self, context):
        
        if (not os.path.exists(self.filepath)):
            bpy.ops.scatter5.popup_menu(msgs=translate("The chosen file path does not exist"), title=translate("Warning"),icon="ERROR",)
            return {'FINISHED'}
        
        if (not self.filepath.endswith(".geoscattersettings")):
            bpy.ops.scatter5.popup_menu(msgs=translate("The chosen file does not end with '.geoscattersettings'. Please choose a proper GeoScatterSettings File"), title=translate("Warning"),icon="ERROR",)
            return {'FINISHED'}
            
        with open(self.filepath,'r') as f:
            settings = json.load(f)

        self.set_settings_from_dict(settings)
        
        return {'FINISHED'}
