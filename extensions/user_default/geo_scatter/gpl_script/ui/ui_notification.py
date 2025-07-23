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
# ooooo     ooo ooooo      ooooo      ooo               .    o8o   .o88o.
# `888'     `8' `888'      `888b.     `8'             .o8    `"'   888 `"
#  888       8   888        8 `88b.    8   .ooooo.  .o888oo oooo  o888oo 
#  888       8   888        8   `88b.  8  d88' `88b   888   `888   888   
#  888       8   888        8     `88b.8  888   888   888    888   888   
#  `88.    .8'   888        8       `888  888   888   888 .  888   888   
#    `YbodP'    o888o      o8o        `8  `Y8bod8P'   "888" o888o o888o  
#
#####################################################################################################


import bpy

from .. resources.icons import cust_icon
from .. translations import translate
from .. utils.extra_utils import dprint
from .. utils.str_utils import word_wrap
from .. utils.coll_utils import get_collection_by_name

from . import ui_templates

#NOTE that some notifications are also located outside of the notification module/panel 
#search for '#send users some notifications' in 'ui_system_list.py'


#   .oooooo.   oooo                            oooo
#  d8P'  `Y8b  `888                            `888
# 888           888 .oo.    .ooooo.   .ooooo.   888  oooo   .oooo.o
# 888           888P"Y88b  d88' `88b d88' `"Y8  888 .8P'   d88(  "8
# 888           888   888  888ooo888 888        888888.    `"Y88b.
# `88b    ooo   888   888  888    .o 888   .o8  888 `88b.  o.  )88b
#  `Y8bood8P'  o888o o888o `Y8bod8P' `Y8bod8P' o888o o888o 8""888P'


#globals, dict of notif str token, organized by type

NOTIFICATIONS = {
    "T_VERSION":set(), # could contain: EXPERIMENTAL_BUILD, OLD_BL_VERSION, PLUGIN_OVERLOAD
    "T_ORPHAN":set(),  # could contain: ORPHAN_PSYS, &ARGS
    "T_NAMECOL":set(), # could contain: EMIT_COLL, PSY_COLL, &ARGS
    "T_ENGINE":set(),  # could contain: NODE_UNDEFINED, NODETREE_UPDATE_NEEDED
    }


def check_for_notifications(checks={"T_VERSION":True,"T_ORPHAN":True,"T_NAMECOL":True,"T_ENGINE":True,},):
    """check if we need to warn something in the notification panel"""
    
    dprint(f"FCT: check_for_notifications() -start -{checks}")
    
    from ... __init__ import bl_info, addon_prefs
    from .. utils.str_utils import as_version_tuple
    
    #reinitialize the flag we accumulated prior, we are going to recalculate them
    
    global NOTIFICATIONS
    for key,value in checks.items():
        if (value==True):
            NOTIFICATIONS[key] = set()

    all_psys     = bpy.context.scene.scatter5.get_all_psys(search_mode="all", also_linked=True)
    all_emitters = bpy.context.scene.scatter5.get_all_emitters(search_mode="all", also_linked=True)
            
    #version information
    
    if checks.get("T_VERSION"):
        dprint("   ...for 'T_VERSION'")
            
        user_addon_bl_version = as_version_tuple(bl_info['blender'], trunc_to='minor',)
        user_blender_version = as_version_tuple(bpy.app.version, trunc_to='minor',)
        
        # all_psys_blender_version = [ as_version_tuple(p.blender_version, trunc_to='minor',) for p in all_psys ]
        # psy_min_blender_version = min(all_psys_blender_version) 
        # psy_max_blender_version = max(all_psys_blender_version) 
        
        # all_psys_addon_version = [ as_version_tuple(p.addon_version, trunc_to='minor',) for p in all_psys ]
        # psy_min_addon_version = min(all_psys_addon_version)
        # psy_max_addon_version = max(all_psys_addon_version)


        #check if user is using a too old blender version?

        if (user_blender_version<user_addon_bl_version):

            print(f"\nWARNING: Your Blender version is too old for the Geo-Scatter plugin you have installed")
            NOTIFICATIONS["T_VERSION"].add("OLD_BL_VERSION")

        #check for users living dangerously 

        if ( ("Beta" in bpy.app.version_string) or ("Alpha" in bpy.app.version_string) or ("Candidate" in bpy.app.version_string) ):

            print(f"\nWARNING: Don't expect any plugin to work with unreleased, beta, alpha version of Blender")
            NOTIFICATIONS["T_VERSION"].add("EXPERIMENTAL_BUILD")

        #check if user have both plugins installed?

        user_plugins = {add.preferences.bl_info['name'] for add in bpy.context.preferences.addons if add.preferences and hasattr(add.preferences,'bl_info')}
        if ( ("Geo-Scatter" in user_plugins) and ("Biome-Reader" in user_plugins) ):
            
            print(f"\nWARNING: Don't install Biome-Reader and Geo-Scatter simultaneously please..")
            NOTIFICATIONS["T_VERSION"].add("PLUGIN_OVERLOAD")

    #orphan scatter object without any psy emitter settings?
    
    if checks.get("T_ORPHAN"):
        dprint("   ...for 'T_ORPHAN'")
        
        orphans = bpy.context.scene.scatter5.get_all_psy_orphans(search_mode="all")
        if (orphans):
            NOTIFICATIONS["T_ORPHAN"].add("ORPHAN_PSYS")
            for o in orphans:
                NOTIFICATIONS["T_ORPHAN"].add(f"ORPHAN_PSYS_ARG:{o.session_uid}")
            
    #if no psys in this .blend, nothing else to warn

    if (len(all_psys)==0):
        return None    
            
    #if there's a naming collision, likely due to a linked import..
    
    if checks.get("T_NAMECOL"):
        if (addon_prefs().debug_interface):
            dprint("   ...for 'T_NAMECOL'")
            
            from .. utils.extra_utils import has_duplicates, get_duplicates

            names = [e.name for e in all_emitters]
            if has_duplicates(names):
                
                NOTIFICATIONS["T_NAMECOL"].add("EMIT_COLL")
                
                #& pass arg
                dup = get_duplicates(names)
                for e in [e for e in all_emitters if e.name in dup]:
                    msg = f"emitter='{e.name}'\nlibrary='{e.library.name if e.library else str()}'\nsession_uid='{e.session_uid}'"
                    
                    NOTIFICATIONS["T_NAMECOL"].add("EMIT_COLL_ARG:"+msg)
                    
            names = [p.name for p in all_psys]
            if has_duplicates(names):
                
                NOTIFICATIONS["T_NAMECOL"].add("PSY_COLL")
                
                #& pass arg
                dup = get_duplicates(names)
                for p in [p for p in all_psys if p.name in dup]:
                    msg = f"scatter='{p.name}'\nemitter='{p.id_data.name}'\nis_linked={p.is_linked}\nuuid={p.uuid}"
                    
                    NOTIFICATIONS["T_NAMECOL"].add("PSY_COLL_ARG:"+msg)
                
    #check for forward compatibility errors, if a psy version is above current version

    if checks.get("T_ENGINE"):
        dprint("   ...for 'T_ENGINE'")
        
        def recursive_seek_undefined(ng,gather):
            if (ng is not None):
                for n in ng.nodes:
                    if (n.bl_idname=="NodeUndefined"):
                        gather.append([ng.name,n.name])
                    elif (n.type=="GROUP"):
                        recursive_seek_undefined(n.node_tree,gather)
            return None

        undef = {}
        for p in all_psys:
            e = []
            mod = p.get_scatter_mod(strict=False)
            if (mod):
                recursive_seek_undefined(mod.node_group,e,)
                if (len(e)!=0):
                    undef[p.name] = e
                continue

        if (undef):
            print(f"\nWARNING: Oh oh, looks like we found scatter-systems with corrupted nodes:")
            for k,v in undef.items():
                print(f"     Scatter-System: {k}")
                for e in v:
                    print(f"       -Undefined node: {e[0]}->{e[1]}")
                    
            NOTIFICATIONS["T_ENGINE"].add("NODE_UNDEFINED")

        #old systems in there? by default we get the scatter engine by their engine names, which are constantly up to date
        #if the scatter engine is not found with the struct mode activated, but found with the 
    
        old_psys = [ p for p in all_psys if (p.get_scatter_mod(strict=False, raise_exception=False) and not p.get_scatter_mod(strict=True, raise_exception=False)) ]
        if (old_psys):
            
            print(f"\nWARNING: It looks like there are scatters made with old version of our plugin in your .blend file:")
            for p in old_psys:
                print(f"     Scatter-System: {p.name} -> {p.get_scatter_mod(strict=False, raise_exception=False).name}")
                
            NOTIFICATIONS["T_ENGINE"].add("NODETREE_UPDATE_NEEDED")

    dprint("FCT: check_for_notifications() -end")
    return None 

# oooooooooo.
# `888'   `Y8b
#  888      888 oooo d8b  .oooo.   oooo oooo    ooo
#  888      888 `888""8P `P  )88b   `88. `88.  .8'
#  888      888  888      .oP"888    `88..]88..8'
#  888     d88'  888     d8(  888     `888'`888'
# o888bood8P'   d888b    `Y888""8o     `8'  `8'


def draw_notification_system_lister(layout=None, context=None, extra_layout=None, scat_scene=None, emitter=None, psy_active=None, group_active=None,):
    """draw some notification realted to emitter/activegroup/system right under the system lister interface, users can't miss it."""
    #NOTE: be carreful notifications are calculated in real time in a draw() call... checks need to be efficient..

    def notif_layout(layout,extra_layout):
        if (extra_layout):
            warn = extra_layout.box()
            warn.separator(factor=0.33)
        else:
            layout.separator(factor=0.5)
            warn = layout.column()
        return warn
    
    def button_layout(layout):
        row = layout.row()
        row.scale_y = 0.9
        row.alignment = 'CENTER'  # Center-align the contents of the row
        row.label(text="")  # Left spacer
        midrow = row.row()
        midrow.alignment = 'CENTER'  # Ensure the button is centered
        row.label(text="")  # Right spacer
        return midrow

    elinked = bool(emitter.library)
        
    #offer to repair particle_interface. Should never happen, but if it does, users can attempt to repair their interface. 
    if (emitter.scatter5.is_particle_interface_broken()):
        warn = notif_layout(layout,extra_layout)
        word_wrap(string=translate("Uh Oh, it seems that our scatter lister interface is broken. What happened?"), active=True, layout=warn, alignment="CENTER", max_char='auto', context=context, char_auto_sidepadding=0.85, icon="GHOST_ENABLED",)
        button = button_layout(warn)
        op = button.operator("scatter5.exec_line", text=translate("Refresh"))
        op.api = f"e = get_from_uid({emitter.session_uid}) ; e.scatter5.particle_interface_refresh()"
        warn.separator(factor=0.33)
        
        broken_p = [p for p in emitter.scatter5.particle_systems if p.scatter_obj is None]
        if (broken_p):
            warn = notif_layout(layout,extra_layout)
            word_wrap(string=translate("Looks like you deleted a 'scatter_obj'? We can attempt a Repair."), active=True, layout=warn, alignment="CENTER", max_char='auto', context=context, char_auto_sidepadding=0.85, icon="LIBRARY_DATA_BROKEN",)
            button = button_layout(warn)
            button.operator("scatter5.fix_scatter_obj", text=translate("Repair"))
            warn.separator(factor=0.33)
        
    #offer to re-link the emitter in the context scene if missing
    if (emitter not in bpy.context.scene.objects[:]):
        warn = notif_layout(layout,extra_layout)
        word_wrap(string=translate("Warning, the emitter object, which contains all the scatter settings, is not present in this scene."), active=True, layout=warn, alignment="CENTER", max_char='auto', context=context, char_auto_sidepadding=0.85, icon="ZOOM_ALL",)
        button = button_layout(warn)
        op = button.operator("scatter5.exec_line", text=translate("Re-Link"))
        op.api = f"e = get_from_uid({emitter.session_uid}) ; C.scene.collection.objects.link(e) ; bpy.ops.object.select_all(action='DESELECT') ; e.select_set(True) ; C.view_layer.objects.active = e"
        warn.separator(factor=0.33)
    
    #draw warning if emitter or active psy is linked
    if (elinked or (psy_active is not None and psy_active.is_linked)):
        warn = notif_layout(layout,extra_layout)
        word_wrap(string=translate("Your Scatter-Items are linked. It's Impossible to tweak settings or create new scatters."), active=True, layout=warn, alignment="CENTER", max_char='auto', context=context, char_auto_sidepadding=0.85, icon="LINKED",)
        warn.separator(factor=0.33)
            
    #draw some warnings related to the active psy
    if (psy_active is not None):
        so = psy_active.scatter_obj
        
        #if p.scatter_obj does not exists? shouldn't be possible
        if (so is None):
            warn = notif_layout(layout,extra_layout)
            word_wrap(string="Warning, the `scatter_obj` of this scatter is missing and you normally shoudln't be able to read this message. Please inform us about this issue.", active=True, layout=warn, alignment="CENTER", max_char='auto', context=context, char_auto_sidepadding=0.85, icon="GHOST_ENABLED",)
            warn.separator(factor=0.33)
            
        else:
            #get scatter mods for this version of our plugin
            scatter_mod_strict = psy_active.get_scatter_mod(strict=True, raise_exception=False)
            
            #scatter_mod is None? user deleted it or user nodetree need an update
            if (scatter_mod_strict is None):
                scatter_mod_any = psy_active.get_scatter_mod(strict=False, raise_exception=False)
                
                warn = notif_layout(layout,extra_layout)
                    
                if (psy_active.is_linked):
                    word_wrap(string=translate("Warning, the Scatter-Engine of this Scatter is broken or outdated. Please fix the issue in the original .blend file where this linked data originates from, then reload your libraries."), active=True, layout=warn, alignment="CENTER", max_char='auto', context=context, char_auto_sidepadding=0.85, icon="LIBRARY_DATA_BROKEN",)
                    
                else:
                    if (scatter_mod_any is None):
                        word_wrap(string=translate("Warning, the Scatter-Engine of this Scatter is missing."), active=True, layout=warn, alignment="CENTER", max_char='auto', context=context, char_auto_sidepadding=0.85, icon="LIBRARY_DATA_BROKEN",)
                        button = button_layout(warn)
                        button.operator("scatter5.fix_nodetrees", text=translate("Repair"))
                        
                    elif (scatter_mod_any):
                        word_wrap(string=translate("Warning, the Scatter-Engine of this Scatter is outdated for this version of our plugin."), active=True, layout=warn, alignment="CENTER", max_char='auto', context=context, char_auto_sidepadding=0.85, icon="TIME",)
                        button = button_layout(warn)
                        button.operator("scatter5.fix_nodetrees", text=translate("Update"))
                    
                warn.separator(factor=0.33)
            
            #what if we found the scatter mod but there's no node_group assigned?
            elif (scatter_mod_strict) and ((not hasattr(scatter_mod_strict,"node_group")) or (scatter_mod_strict.node_group is None)):
                warn = notif_layout(layout,extra_layout)
                word_wrap(string=translate("Warning, the Scatter-Engine of this Scatter is missing."), active=True, layout=warn, alignment="CENTER", max_char='auto', context=context, char_auto_sidepadding=0.85, icon="LIBRARY_DATA_BROKEN",)
                button = button_layout(warn)
                button.operator("scatter5.fix_nodetrees", text=translate("Repair"))
                warn.separator(factor=0.33)
                    
            #p.scatter_obj is not found anywhere in context scene?
            if (so not in bpy.context.scene.objects[:]):
                warn = notif_layout(layout,extra_layout)
                word_wrap(string=translate("Warning, the 'scatter_obj' used by this Scatter is not present in this scene."), active=True, layout=warn, alignment="CENTER", max_char='auto', context=context, char_auto_sidepadding=0.85, icon="ZOOM_ALL",)
                button = button_layout(warn)
                button.operator("scatter5.fix_scatter_obj", text=translate("Re-Link"))
                warn.separator(factor=0.33)
                
            #p.scatter_obj is not visible?
            elif ((not so.visible_get()) and (not psy_active.hide_viewport) and (bpy.context.area.type=="VIEW_3D") and (bpy.context.space_data.local_view is None)):
                warn = notif_layout(layout,extra_layout)
                
                from .. utils.coll_utils import get_collection_view_layer_exclude
                psy_coll = psy_active.get_scatter_psy_collection(strict=True)
                
                if (so in bpy.context.view_layer.objects[:]):
                    word_wrap(string=translate("The 'scatter_obj' of this Scatter is hidden in the active ViewLayer."), active=True, layout=warn, alignment="CENTER", max_char='auto', context=context, char_auto_sidepadding=0.85, icon="HIDE_OFF",)
                    button = button_layout(warn)
                    op = button.operator("scatter5.exec_line", text=translate("Un-hide"))
                    op.api = f"get_from_uid({so.session_uid}).hide_set(False)"
                    
                elif (psy_coll and get_collection_view_layer_exclude(psy_coll)==True):
                    word_wrap(string=translate("The collection containing the 'scatter_obj' of this Scatter is hidden in the active ViewLayer."), active=True, layout=warn, alignment="CENTER", max_char='auto', context=context, char_auto_sidepadding=0.85, icon="HIDE_OFF",)
                    button = button_layout(warn)
                    op = button.operator("scatter5.exec_line", text=translate("Un-hide"))
                    op.api = f"set_collection_view_layers_exclude(get_from_uid({psy_coll.session_uid},bpy.data.collections), view_layers=[bpy.context.view_layer], scenes=[bpy.context.scene], hide=False,)"
                    
                else:
                    word_wrap(string=translate("Warning, this Scatter is hidden. Please check your outliner for hidden 'scatter_obj' or 'psy' Collections."), active=True, layout=warn, alignment="CENTER", max_char='auto', context=context, char_auto_sidepadding=0.85, icon="HIDE_OFF")
                
                warn.separator(factor=0.33)

            surfaces = psy_active.get_surfaces()
            if (surfaces):
                    
                #check if psy_active surface is unlinked from scene?
                if (psy_active.s_surface_method in ('object','collection')):
                
                    surfobj  = psy_active.s_surface_object
                    surfcoll = psy_active.get_scatter_node("s_surface_evaluator").inputs[2].default_value #need to do that because collection link collision

                    if ((psy_active.s_surface_method=='object') and (surfobj) and (surfobj not in bpy.context.scene.objects[:])):                         
                        warn = notif_layout(layout,extra_layout)
                        word_wrap(string=translate("Warning, your Scatter-Surface(s) are not present in this scene."), active=True, layout=warn, alignment="CENTER", max_char='auto', context=context, char_auto_sidepadding=0.85, icon="ZOOM_ALL",)
                        button = button_layout(warn)
                        op = button.operator("scatter5.exec_line", text=translate("Re-Link"))
                        op.api = f"C.scene.collection.objects.link(get_from_uid({surfobj.session_uid}))"
                        warn.separator(factor=0.33)
                        
                    if ((psy_active.s_surface_method=='collection') and (surfcoll) and (surfcoll not in bpy.context.scene.collection.children_recursive[:])):
                        warn = notif_layout(layout,extra_layout)
                        word_wrap(string=translate("Warning, your Scatter-Surface(s) collection is not present in this scene."), active=True, layout=warn, alignment="CENTER", max_char='auto', context=context, char_auto_sidepadding=0.85, icon="ZOOM_ALL",)
                        button = button_layout(warn)
                        op = button.operator("scatter5.exec_line", text=translate("Re-Link"))
                        gssurf = get_collection_by_name("Geo-Scatter Surfaces")
                        if (gssurf and gssurf in bpy.context.scene.collection.children_recursive[:]):
                            op.api = f"get_from_uid({gssurf.session_uid},D.collections).children.link(get_from_uid({surfcoll.session_uid},D.collections))"
                        else: op.api = f"C.scene.collection.children.link(get_from_uid({surfcoll.session_uid},D.collections))"
                        warn.separator(factor=0.33)

                #check for surfaces subdiv problems
                if (psy_active.s_distribution_method in ('random','clumping','verts','faces','edges','volume','random_stable',)):
                    
                    subdiv_mods = [m for s in surfaces for m in s.modifiers if (m.type=='SUBSURF')]
                    if (subdiv_mods):
                        
                        if ([s for s in surfaces if s.cycles.use_adaptive_subdivision] and (bpy.context.scene.cycles.feature_set=='EXPERIMENTAL')):
                            warn = notif_layout(layout,extra_layout)
                            word_wrap(layout=warn, alignment="CENTER", active=True, alert=False, max_char='auto', context=context, char_auto_sidepadding=0.85, icon="SURFACE_NSURFACE", string=translate("Warning, One of your scatter surfaces is using adaptive subdivision. Shader-based displacement is not supported. Distribution's seed discrepancies may occur if the surface geometry changes on render."),)
                            warn.separator(factor=0.33)
                                
                        elif [m for m in subdiv_mods if (m.render_levels!=m.levels)]:
                            warn = notif_layout(layout,extra_layout)
                            word_wrap(layout=warn, alignment="CENTER", active=True, alert=False, max_char='auto', context=context, char_auto_sidepadding=0.85, icon="SURFACE_NSURFACE", string=translate("Warning, One of your scatter surfaces has different subdivision levels on render. Distribution's seed discrepancies may occur if the surface geometry changes on render."),)
                            warn.separator(factor=0.33)
    
    return None
    
def draw_notification_panel(self, layout,):
    """draw some notification, if found in global notification list"""

    main = layout.column()

    ui_templates.separator_box_out(main)
    ui_templates.separator_box_out(main)
    
    global NOTIFICATIONS

    #undefined nodes, corrupted, do not save
    if ("NODE_UNDEFINED" in NOTIFICATIONS["T_ENGINE"]):

        box, is_open = ui_templates.box_panel(main, 
            panelopen_propname="ui_notification_1", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_notification_1");BOOL_VALUE(1)
            panel_icon="ERROR", 
            panel_name=translate("Node(s) Undefined"),
            is_warning_panel=True,
            )
        if is_open:

            col = box.column()

            word_wrap(layout=col, alignment="CENTER", active=True, alert=False, max_char=32, icon="INFO", string=translate("Your blend file has corrupted nodes, likely because of a forward compatibility manipulation."),)
            col.separator()

            rwoo = col.row()
            rwo1 = rwoo.row()
            exp = rwoo.row()
            rwo2 = rwoo.row()

            buttons = exp.column()
            buttons.scale_y = 1.2
            buttons.operator("wm.url_open", text=translate("About Forward Compatibility"), icon="URL",).url = "https://www.geoscatter.com/documentation.html#FeaturePrerequisite&article_compatibility_issues"
            buttons.separator()
            buttons.operator("scatter5.fix_nodetrees", text=translate("Attempt Reparation"), icon="RECOVER_LAST",).force_update = True

            col.separator()
            word_wrap(layout=col, alignment="CENTER", active=True, alert=False, max_char=30, string=translate("The undefined nodegroup(s) we found are displayed in your console window."),)
            
            ui_templates.separator_box_in(box)

        ui_templates.separator_box_out(main)

    #version of blender do not match with plugin
    if ("OLD_BL_VERSION" in NOTIFICATIONS["T_VERSION"]):

        box, is_open = ui_templates.box_panel(main, 
            panelopen_propname="ui_notification_2", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_notification_2");BOOL_VALUE(1)
            panel_icon="ERROR", 
            panel_name=translate("Incompatible Version"),
            is_warning_panel=True,
            )
        if is_open:

            col = box.column()

            word_wrap(layout=col, alignment="CENTER", active=True, alert=False, max_char=31, icon="INFO", string=translate("Are you using the correct version of our plugin?\nWe don't think so. Please read the page below"),)
            col.separator()

            rwoo = col.row()
            rwo1 = rwoo.row()
            exp = rwoo.row()
            rwo2 = rwoo.row()

            exp.scale_y = 1.2
            exp.operator("wm.url_open", text=translate("About Compatibility"), icon="URL",).url = "https://www.geoscatter.com/documentation.html#Changelogs&article_compatibility_advices"

            ui_templates.separator_box_in(box)

        ui_templates.separator_box_out(main)

    #user is using beta or alpha build
    if ("EXPERIMENTAL_BUILD" in NOTIFICATIONS["T_VERSION"]):

        box, is_open = ui_templates.box_panel(main, 
            panelopen_propname="ui_notification_3", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_notification_3");BOOL_VALUE(1)
            panel_icon="ERROR", 
            panel_name=translate("Unofficial Build"),
            is_warning_panel=True,
            )
        if is_open:

            col = box.column()
            word_wrap(layout=col, alignment="CENTER", active=True, alert=False, max_char=28, icon="INFO", string=translate("Please don't expect any Plugin to support experimental versions of Blender. Our plugin might not support this version of Blender (yet)."),)
            
            ui_templates.separator_box_in(box)

        ui_templates.separator_box_out(main)

    #both our plugins installed?
    if ("PLUGIN_OVERLOAD" in NOTIFICATIONS["T_VERSION"]):

        box, is_open = ui_templates.box_panel(main, 
            panelopen_propname="ui_notification_4", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_notification_4");BOOL_VALUE(1)
            panel_icon="ERROR", 
            panel_name=translate("Plugin Overload"),
            is_warning_panel=True,
            )
        if is_open:

            col = box.column()
            word_wrap(layout=col, alignment="CENTER", active=True, alert=False, max_char=28, icon="INFO", string=translate("Please do not install 'Biome-Reader' and 'Geo-Scatter' simultaneously, it might lead to errors.\n\nGeo-Scatter can do everything that Biome-Reader can do, better!"),)
            
            ui_templates.separator_box_in(box)

        ui_templates.separator_box_out(main)

    #old psy found, please update
    if ("NODETREE_UPDATE_NEEDED" in NOTIFICATIONS["T_ENGINE"]):

        box, is_open = ui_templates.box_panel(main, 
            panelopen_propname="ui_notification_5", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_notification_5");BOOL_VALUE(1)
            panel_icon="ERROR", 
            panel_name=translate("Update Required"),
            is_warning_panel=True,
            )
        if is_open:

            col = box.column()

            word_wrap(layout=col, alignment="CENTER", active=True, alert=False, max_char=29, icon="INFO", string=translate("Hello dear user, there are Scatter-system(s) made with a lower version of our plugin in this .blend file, we need to update the Scatter-Engines nodetrees."),)
            col.separator()

            rwoo = col.row()
            rwo1 = rwoo.row()
            exp = rwoo.row()
            rwo2 = rwoo.row()

            exp.scale_y = 1.2
            exp.operator("scatter5.fix_nodetrees", text=translate("Update Nodetree(s)"), icon="FILE_REFRESH",)

            col.separator()
            word_wrap(layout=col, alignment="CENTER", active=True, alert=False, max_char=31, string=translate("This update process might take a minute. Changing versions of your sofware(s)/plugin(s) mid-project is not advised, save copies of your project first!",),)
            
            ui_templates.separator_box_in(box)

        ui_templates.separator_box_out(main)
    
    #if emitter name collision
    if ("EMIT_COLL" in NOTIFICATIONS["T_NAMECOL"]):

        box, is_open = ui_templates.box_panel(main, 
            panelopen_propname="ui_notification_8", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_notification_8");BOOL_VALUE(1)
            panel_icon="ERROR", 
            panel_name=translate("Emitter Name Collision"),
            is_warning_panel=True,
            )
        if is_open:

            col = box.column()
            word_wrap(layout=col, alignment="CENTER", active=True, alert=False, max_char=33, icon="INFO", string=translate("We detected a name collision in your Scatter-Items, probably related to a link. This might lead to unexpected errors."),)
            
            for notif in NOTIFICATIONS["T_NAMECOL"]:
                if notif.startswith("EMIT_COLL_ARG:"):
                    col.separator(factor=1.5)
                    word_wrap(layout=col, alignment="CENTER", active=False, alert=False, max_char=40, string=notif[14:],)

            ui_templates.separator_box_in(box)

        ui_templates.separator_box_out(main)
    
    #if psy name collision
    if ("PSY_COLL" in NOTIFICATIONS["T_NAMECOL"]):

        box, is_open = ui_templates.box_panel(main, 
            panelopen_propname="ui_notification_9", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_notification_9");BOOL_VALUE(1)
            panel_icon="ERROR", 
            panel_name=translate("Scatter Name Collision"),
            is_warning_panel=True,
            )
        if is_open:

            col = box.column()
            word_wrap(layout=col, alignment="CENTER", active=True, alert=False, max_char=33, icon="INFO", string=translate("We detected a name collision in your Scatter-Items, probably related to a link. This might lead to unexpected errors."),)
            
            for notif in NOTIFICATIONS["T_NAMECOL"]:
                if notif.startswith("PSY_COLL_ARG:"):
                    col.separator(factor=1.5)
                    word_wrap(layout=col, alignment="CENTER", active=False, alert=False, max_char=40, string=notif[13:],)

            ui_templates.separator_box_in(box)

        ui_templates.separator_box_out(main)

    #if orphan psy, scatter_obj alone with no emitter settings found
    if ("ORPHAN_PSYS" in NOTIFICATIONS["T_ORPHAN"]):

        box, is_open = ui_templates.box_panel(main, 
            panelopen_propname="ui_notification_10", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_notification_10");BOOL_VALUE(1)
            panel_icon="ERROR", 
            panel_name=translate("Missing Scatters"),
            is_warning_panel=True,
            )
        if is_open:

            col = box.column()
            word_wrap(layout=col, alignment="CENTER", active=True, alert=False, max_char=33, icon="LIBRARY_DATA_BROKEN", string=translate("We detected Scatter-Object(s) without any associated Scatter-Settings. Would you like to remove them?"),)
            col.separator()

            from .. utils.extra_utils import get_from_uid
            
            orphans = set()
            linked_orphan = False
            
            for notif in NOTIFICATIONS["T_ORPHAN"]:
                if notif.startswith("ORPHAN_PSYS_ARG:"):
                    orphan = get_from_uid(int(notif[16:]))
                    orphans.add(orphan)
                    if (orphan):
                        linked_orphan = orphan.library
                        word_wrap(layout=col, alignment="CENTER", active=False, alert=False, max_char=40, string=orphan.name, icon="LINKED" if (linked_orphan) else None)

            # if (linked_orphan):
            #     col.separator()
            #     word_wrap(layout=col, alignment="CENTER", active=True, alert=False, max_char=33, icon="INFO", string=translate("Note that linked orphans will be deleted. It is better to re-link these items from your original file."),)
            
            col.separator(factor=1.3)
            
            rwoo = col.row()
            rwo1 = rwoo.row()
            exp = rwoo.row()
            rwo2 = rwoo.row()
            buttons = exp.column()
            buttons.scale_y = 1.2
            op = buttons.operator("scatter5.exec_line", text=translate("Remove Orphans"), icon="TRASH",)
            op.api = ";".join([f"D.objects.remove(get_from_uid({o.session_uid}))" for o in orphans if o]) + " ; cleanup_scatter_collections(options={'remove_unused_colls':True,}) ; check_for_notifications(checks={'T_ORPHAN':True})"
            op.undo = translate("Remove Orphans")
            #buttons.operator("scatter5.fix_orphan_psys", text=translate("Attempt Repair"), icon="LIBRARY_DATA_BROKEN",)

            ui_templates.separator_box_in(box)

        ui_templates.separator_box_out(main)
    
    ui_templates.separator_box_out(main)
    ui_templates.separator_box_out(main)

    return None 


#    .oooooo.   oooo
#   d8P'  `Y8b  `888
#  888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
#  888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
#  888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
#  `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#   `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'


class SCATTER5_PT_notification(bpy.types.Panel):

    bl_idname      = "SCATTER5_PT_notification"
    bl_label       = translate("Notification")
    bl_category    = "USER_DEFINED" #will be replaced right before ui.__ini__.register()
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_context     = "" #nothing == enabled everywhere
    bl_order       = 0

    @classmethod
    def poll(cls, context,):
        
        if (context.mode not in ('OBJECT','PAINT_WEIGHT','PAINT_VERTEX','PAINT_TEXTURE','EDIT_MESH','EDIT_CURVE',)):
            return False
        
        global NOTIFICATIONS
        if all(not s for s in NOTIFICATIONS.values()):
           return False

        return True
        
    def draw_header(self, context):
        self.layout.label(text="", icon_value=cust_icon("W_SCATTER"),)

    def draw_header_preset(self, context):
        row = self.layout.row()
        row.alignment = "RIGHT"
        row.alert = True
        row.label(text=translate("Warning"),)
        row.label(text="", icon="INFO")

    def draw(self, context):
        layout = self.layout
        draw_notification_panel(self,layout)


classes = (

    SCATTER5_PT_notification,

    )


#if __name__ == "__main__":
#    register()

