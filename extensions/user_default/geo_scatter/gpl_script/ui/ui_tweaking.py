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
# ooooo     ooo ooooo      ooooooooooooo                                      oooo         o8o
# `888'     `8' `888'      8'   888   `8                                      `888         `"'
#  888       8   888            888      oooo oooo    ooo  .ooooo.   .oooo.    888  oooo  oooo  ooo. .oo.    .oooooooo
#  888       8   888            888       `88. `88.  .8'  d88' `88b `P  )88b   888 .8P'   `888  `888P"Y88b  888' `88b
#  888       8   888            888        `88..]88..8'   888ooo888  .oP"888   888888.     888   888   888  888   888
#  `88.    .8'   888            888         `888'`888'    888    .o d8(  888   888 `88b.   888   888   888  `88bod8P'
#    `YbodP'    o888o          o888o         `8'  `8'     `Y8bod8P' `Y888""8o o888o o888o o888o o888o o888o `8oooooo.
#                                                                                                           d"     YD
#####################################################################################################       "Y88888P'


import bpy

from .. resources.icons import cust_icon
from .. translations import translate

from .. utils.str_utils import word_wrap, is_attr_surfs_shared
from .. utils.math_utils import count_repr

from .. scattering.texture_datablock import draw_texture_datablock

from . import ui_templates
from . ui_emitter_select import emitter_header

#TIP: for icons use 'https://ui.blender.org/icons'

# oooooooooooo                                       .    o8o
# `888'     `8                                     .o8    `"'
#  888         oooo  oooo  ooo. .oo.    .ooooo.  .o888oo oooo   .ooooo.  ooo. .oo.    .oooo.o
#  888oooo8    `888  `888  `888P"Y88b  d88' `"Y8   888   `888  d88' `88b `888P"Y88b  d88(  "8
#  888    "     888   888   888   888  888         888    888  888   888  888   888  `"Y88b.
#  888          888   888   888   888  888   .o8   888 .  888  888   888  888   888  o.  )88b
# o888o         `V88V"V8P' o888o o888o `Y8bod8P'   "888" o888o `Y8bod8P' o888o o888o 8""888P'


def get_props():
    """get useful props used in interface""" 
    #IMPORTANT NOTE: perhaps a bad idea to constanly call this funciton in GUI, too many repetitive calls?

    scat_win = bpy.context.window_manager.scatter5
    scat_ui = scat_win.ui
    scat_scene = bpy.context.scene.scatter5
    emitter = scat_scene.emitter
    psy_active = emitter.scatter5.get_psy_active()
    group_active  = emitter.scatter5.get_group_active()

    return (scat_scene, scat_ui, scat_win, emitter, psy_active, group_active)

def warnings(layout, active=True, created=True,):
    """check if interface should be drawn, if nothing created or active"""

    emitter    = bpy.context.scene.scatter5.emitter
    psy_active = emitter.scatter5.get_psy_active()

    if (psy_active is None):
        txt = layout.row()
        txt.alignment = "CENTER"
        txt.label(text=translate("No System(s) Active."), icon="INFO",) #unlikely
        ui_templates.separator_box_in(layout)
        return True
    return False

def lock_check(psy_active, s_category="s_distribution", prop=None,):
    """check if category is locked"""

    if psy_active.is_locked(s_category):
        return False 
    return prop

def active_check(psy_active, s_category="s_distribution", prop=None,):
    """check if category master allow is off"""

    if (not getattr(psy_active,f"{s_category}_master_allow")):
        return False 
    return prop


#  8888b.  88""Yb    db    Yb        dP     888888 888888 8b    d8 88""Yb 88        db    888888 888888 .dP"Y8
#   8I  Yb 88__dP   dPYb    Yb  db  dP        88   88__   88b  d88 88__dP 88       dPYb     88   88__   `Ybo."
#   8I  dY 88"Yb   dP__Yb    YbdPYbdP         88   88""   88YbdP88 88"""  88  .o  dP__Yb    88   88""   o.`Y8b
#  8888Y"  88  Yb dP""""Yb    YP  YP          88   888888 88 YY 88 88     88ood8 dP""""Yb   88   888888 8bodP'


def draw_visibility_methods(psy_active, layout, api):
    """draw viewport method in visibility and display features"""

    if (not layout):
        return None
    
    from ... __init__ import addon_prefs
    
    if (addon_prefs().debug_interface):
        row = layout.row(align=True)
        row.alignment = "RIGHT"
        row.scale_x = 0.9
        row.prop(psy_active,f"{api}_viewport_method", text="",)

    row = layout.box().row(align=True)
    row.alignment = "RIGHT"
    row.scale_y = 0.4
    row.scale_x = 0.95
    
    is_shaded = getattr(psy_active, f"{api}_allow_shaded")
    is_render = getattr(psy_active, f"{api}_allow_render")

    row.emboss = "NONE"
    rwoo = row.row(align=True) ; rwoo.active = True      ; rwoo.prop(psy_active,f"{api}_allow_screen", text="", icon="RESTRICT_VIEW_OFF",)
    rwoo = row.row(align=True) ; rwoo.active = is_shaded ; rwoo.prop(psy_active,f"{api}_allow_shaded", text="", icon="SHADING_RENDERED" if is_shaded else "NODE_MATERIAL",)
    rwoo = row.row(align=True) ; rwoo.active = True      ; rwoo.prop(psy_active,f"{api}_allow_render", text="", icon="RESTRICT_RENDER_OFF" if is_render else "RESTRICT_RENDER_ON",)

    return None 

def draw_coll_str_ptr(layout=None, system=None, api="", revert_api="", add_coll_name="", add_parent_name="Geo-Scatter User Col", draw_popover=True,):
    """draw collection pointer template, for psy or group"""
        
    str_value = getattr(system,api)
    coll_found = bpy.data.collections.get(str_value)

    row = layout.row(align=True)

    #draw popover?
    if (coll_found and draw_popover):
        pop = row.row(align=True)
        #transfer arguments for collection drawing & add/remove buttons
        pop.context_string_set("pass_ui_arg_collapi", api,)
        pop.context_pointer_set("pass_ui_arg_collptr", coll_found,)
        pop.popover(panel="SCATTER5_PT_collection_popover", text="", icon="OUTLINER",)

    #draw str prop search
    ptr = row.row(align=True)
    ptr.alert = ( bool(str_value) and (not coll_found) )
    ptr.prop(system, api, text="", icon="OUTLINER_COLLECTION", placeholder=" "+translate("Collection"),)

    #draw reverse arrow?
    if (coll_found and revert_api):
        row.prop(system, revert_api, text="", icon="ARROW_LEFTRIGHT",)
    
    #draw create button if ptr is None
    if (str_value==""):
        op = row.operator("scatter5.create_coll", text="", icon="ADD",)
        op.api = f"{'psy_active' if (system.system_type=='SCATTER_SYSTEM') else 'group_active'}.{api}" 
        op.pointer_type = "str"
        op.coll_name = add_coll_name
        op.parent_name = add_parent_name

    return coll_found, row

def draw_camera_update_method(layout=None, psy_active=None):
    """draw context_scene.scatter5 camera update dependencies method"""

    from ... __init__ import blend_prefs
    scat_data  = blend_prefs()

    col = layout.column(align=True)
    txt = col.row()
    txt.label(text=translate("Cam Update")+" :")

    col.prop(scat_data, "factory_cam_update_method", text="",)

    if (scat_data.factory_cam_update_method=="update_delayed"):
        col.prop(scat_data, "factory_cam_update_secs")
        col.separator(factor=0.5)

    elif (scat_data.factory_cam_update_method=="update_apply") and psy_active:
        col.operator("scatter5.exec_line", text=translate("Refresh"), icon="FILE_REFRESH",).api = "update_camera_nodegroup(scene=C.scene, force_update=True, reset_hash=True,)"
        col.separator(factor=0.5)

    return None 

def draw_transition_control_feature(layout=None, psy_active=None, api="", fallnoisy=True,):
    """draw the transition control feature, this feature is repeated many times"""

    tocol, is_toggled = ui_templates.bool_toggle(layout, psy_active, f"{api}_fallremap_allow",
        label=translate("Transition Control"),
        icon="FCURVE", 
        use_layout_left_spacer=False,
        return_sublayout=True,
        )
    if is_toggled:

        #special case for camera distance, nodes is not the same as api
        if (api=="s_visibility_camdist"):
            api = "s_visibility_cam"

        #find back the fallremap node, the name node names & structure are standardized, otherwise will lead to issues!
        opapi = f"bpy.data.objects['{psy_active.scatter_obj.name}'].modifiers['{psy_active.get_scatter_mod().name}'].node_group.nodes['{api}'].node_tree.nodes['fallremap']"
        
        ope = tocol.row(align=True)
        op = ope.operator("scatter5.graph_dialog", text=translate("Falloff Graph"), icon="FCURVE",)
        op.source_api = opapi
        op.mapping_api = f"{opapi}.mapping"
        op.psy_name = psy_active.name
            
        #special case for camera distance
        if (api=="s_visibility_cam"):
              ope.prop(psy_active, f"s_visibility_camdist_fallremap_revert", text="", icon="ARROW_LEFTRIGHT",)
        else: ope.prop(psy_active, f"{api}_fallremap_revert", text="", icon="ARROW_LEFTRIGHT",)

        tocol.separator(factor=0.3)

        if (fallnoisy):

            noisyt = tocol.column(align=True)
            noisyt.scale_y = 0.9
            noisyt.label(text=translate("Noise")+":")
            noisyt.prop(psy_active, f"{api}_fallnoisy_strength")
            noisytt = noisyt.column(align=True)
            noisytt.active = getattr(psy_active, f"{api}_fallnoisy_strength")!=0
            noisytt.prop(psy_active, f"{api}_fallnoisy_scale")
            noisyp = noisytt.row(align=True)
            noisyp.prop(psy_active, f"{api}_fallnoisy_seed")
            noisyb = noisyp.row(align=True)
            noisyb.scale_x = 1.2
            noisyb.prop(psy_active, f"{api}_fallnoisy_is_random_seed", icon_value=cust_icon("W_DICE"), text="",)

            tocol.separator(factor=0.3)

    return tocol, is_toggled 

def draw_universal_masks(layout=None, mask_api="", psy_api=None,):
    """every universal masks api should have _mask_ptr _mask_reverse"""

    #group_api = "particle_groups" if (system.system_type=='SCATTER_SYSTEM') else "particle_groups" if (system.system_type=='SCATTER_GROUP') else "ERROR_NOT_FOUND"
    
    col = layout.column(align=True)

    col.separator(factor=0.5)

    # title = col.row(align=True)
    # title.scale_y = 0.9
    # title.label(text=translate("Feature Mask")+":",)

    tocol, is_toggled = ui_templates.bool_toggle(col, psy_api, f"{mask_api}_mask_allow",
        label=translate("Feature Mask"),
        icon="MOD_OPACITY",
        use_layout_left_spacer=False,
        return_sublayout=True,
        )
    if is_toggled:

        _mask_ptr_str = f"{mask_api}_mask_ptr"
        _mask_ptr_val = getattr(psy_api, f"{mask_api}_mask_ptr")
        _mask_method_val = getattr(psy_api, f"{mask_api}_mask_method")
        _mask_color_sample_method_val = getattr(psy_api, f"{mask_api}_mask_color_sample_method")

        methodcol = tocol.column(align=True)
        # methodcol.label(text=translate("Mask Type")+":",)
        method = methodcol.row(align=True)
        method.prop(psy_api, f"{mask_api}_mask_method", text="",)# icon_only=True, emboss=True,)

        match _mask_method_val:

            case "mask_vg": ################################ Vgroup Method
                    
                tocol.separator(factor=0.4)

                #Mask Ptr

                mask = tocol.row(align=True)

                ptr = mask.row(align=True)
                ptr_filled = bool(_mask_ptr_val)
                ptr_acrossall = is_attr_surfs_shared(system=psy_api, attr_type='vg', attr_name=_mask_ptr_val,)
                ptr.alert = (ptr_filled and not ptr_acrossall) or (ptr_filled and not psy_api.is_using_surf)
                ptr.prop(psy_api, _mask_ptr_str, text="", icon="GROUP_VERTEX", placeholder=" "+translate("Vertex-Group"),)

                buttons = mask.row(align=True)
                buttons.scale_x = 0.93

                if (_mask_ptr_val!=""):
                    buttons.prop(psy_api, f"{mask_api}_mask_reverse", text="", icon="ARROW_LEFTRIGHT",)

                op = buttons.operator("scatter5.vg_quick_paint",
                    text="",
                    icon="BRUSH_DATA" if _mask_ptr_val else "ADD",
                    depress=((bpy.context.mode=="PAINT_WEIGHT") and (getattr(bpy.context.object.vertex_groups.active,"name",'')==_mask_ptr_val)),
                    )
                op.group_name = _mask_ptr_val
                op.mode = "vg"
                op.api = f"emitter.scatter5.particle_systems['{psy_api.name}'].{_mask_ptr_str}"

            case "mask_vcol": ################################ Color Attribute Method
                
                tocol.separator(factor=0.4)

                #set color
                set_color = (1,1,1)
                if (_mask_ptr_val!=""):
                    equivalence = {"id_picker":getattr(psy_api,f"{mask_api}_mask_id_color_ptr"),"id_greyscale":(1,1,1),"id_red":(1,0,0),"id_green":(0,1,0),"id_blue":(0,0,1),"id_black":(0,0,0),"id_white":(1,1,1),"id_saturation":(1,1,1),"id_value":(1,1,1),"id_hue":(1,1,1),"id_lightness":(1,1,1),"id_alpha":(1,1,1),}
                    set_color = equivalence[_mask_color_sample_method_val]

                #Mask Ptr

                mask = tocol.row(align=True)

                ptr = mask.row(align=True)
                ptr_filled = bool(_mask_ptr_val)
                ptr_acrossall = is_attr_surfs_shared(system=psy_api, attr_type='vcol', attr_name=_mask_ptr_val,)
                ptr.alert = (ptr_filled and not ptr_acrossall) or (ptr_filled and not psy_api.is_using_surf)
                ptr.prop(psy_api, _mask_ptr_str, text="", icon="GROUP_VCOL", placeholder=" "+translate("Color Attribute"),)

                buttons = mask.row(align=True)
                buttons.scale_x = 0.93

                if (_mask_ptr_val!=""):
                    buttons.prop(psy_api, f"{mask_api}_mask_reverse", text="", icon="ARROW_LEFTRIGHT",)

                op = buttons.operator("scatter5.vg_quick_paint",
                    text="", icon="BRUSH_DATA" if _mask_ptr_val else "ADD",
                    depress=((bpy.context.mode=="PAINT_VERTEX") and (getattr(bpy.context.object.data.color_attributes.active_color,"name",'')==_mask_ptr_val)),
                    )
                op.group_name =_mask_ptr_val
                op.mode = "vcol"
                op.set_color = set_color
                op.api = f"emitter.scatter5.particle_systems['{psy_api.name}'].{_mask_ptr_str}"

                #sample method

                if (_mask_ptr_val!=""):

                    tocol.label(text=translate("Sample")+":")
                    sampl = tocol.column(align=True)
                    sampl.scale_y = 0.95
                    meth = sampl.row(align=True)
                    meth.prop(psy_api, f"{mask_api}_mask_color_sample_method", text="",)
                    if (_mask_color_sample_method_val=="id_picker"):
                        color = meth.row(align=True)
                        color.scale_x = 0.35
                        color.prop(psy_api, f"{mask_api}_mask_id_color_ptr", text="",)
                                
            case "mask_bitmap": ################################ Image Method

                tocol.separator(factor=0.4)

                _mask_bitmap_ptr_val = getattr(psy_api, f"{mask_api}_mask_bitmap_ptr")
                _mask_bitmap_uv_ptr_val = getattr(psy_api, f"{mask_api}_mask_bitmap_uv_ptr")

                #set color
                set_color = (0,0,0)
                if (_mask_bitmap_ptr_val!=""):
                    equivalence = {"id_picker":getattr(psy_api,f"{mask_api}_mask_id_color_ptr"),"id_greyscale":(1,1,1),"id_red":(1,0,0),"id_green":(0,1,0),"id_blue":(0,0,1),"id_black":(0,0,0),"id_white":(1,1,1),"id_saturation":(1,1,1),"id_value":(1,1,1),"id_hue":(1,1,1),"id_lightness":(1,1,1),"id_alpha":(1,1,1),}
                    set_color = equivalence[_mask_color_sample_method_val]
                    
                #Mask Ptr

                mask = tocol.row(align=True)
                
                ptr = mask.row(align=True)
                ptr.alert = ( bool(_mask_bitmap_ptr_val) and (_mask_bitmap_ptr_val not in bpy.data.images) )
                ptr.prop(psy_api, f"{mask_api}_mask_bitmap_ptr", text="", icon="IMAGE_DATA", placeholder=" "+translate("Image"),)

                buttons = mask.row(align=True)
                buttons.scale_x = 0.93

                if (_mask_bitmap_ptr_val!=""):
                    buttons.prop(psy_api, f"{mask_api}_mask_reverse", text="", icon="ARROW_LEFTRIGHT",)

                op = buttons.operator("scatter5.image_utils",
                    text="", icon="BRUSH_DATA" if _mask_bitmap_ptr_val else "ADD",
                    depress=((bpy.context.mode=="PAINT_TEXTURE") and (bpy.context.scene.tool_settings.image_paint.mode=='IMAGE') and (bpy.context.scene.tool_settings.image_paint.canvas==bpy.data.images.get(_mask_bitmap_ptr_val)) and (bpy.context.object.data.uv_layers.active) and (bpy.context.object.data.uv_layers.active.name==_mask_bitmap_uv_ptr_val)),
                    )
                if (_mask_bitmap_ptr_val==""):
                    op.option = "new"
                    op.img_name = _mask_bitmap_ptr_val
                    op.api = f"emitter.scatter5.particle_systems['{psy_api.name}'].{mask_api}_mask_bitmap_ptr"
                else:
                    op.option = "paint"
                    op.paint_color = set_color
                    op.uv_ptr = _mask_bitmap_uv_ptr_val
                    op.img_name = _mask_bitmap_ptr_val
                    op.api = f"emitter.scatter5.particle_systems['{psy_api.name}'].{mask_api}_mask_bitmap_ptr"

                if (_mask_bitmap_ptr_val!=""):
                    tocol.separator(factor=0.1)
                    ptr = tocol.row(align=True)
                    ptr.alert = ( bool(_mask_bitmap_uv_ptr_val) and not is_attr_surfs_shared(system=psy_api, attr_type='uv', attr_name=_mask_bitmap_uv_ptr_val,) )
                    ptr.prop(psy_api, f"{mask_api}_mask_bitmap_uv_ptr", text="", icon="GROUP_UVS", placeholder=" "+translate("UV Map"),)

                #sample method

                if (_mask_bitmap_ptr_val!=""):

                    tocol.label(text=translate("Sample")+":")
                    sampl = tocol.column(align=True)
                    sampl.scale_y = 0.95
                    meth = sampl.row(align=True)
                    meth.prop(psy_api, f"{mask_api}_mask_color_sample_method", text="",)
                    if (_mask_color_sample_method_val=="id_picker"):
                        color = meth.row(align=True)
                        color.scale_x = 0.35
                        color.prop(psy_api, f"{mask_api}_mask_id_color_ptr", text="",)  

            case "mask_noise": ################################ Noise Method

                tocol.label(text=translate("Space")+":")
                tocol.prop(psy_api, f"{mask_api}_mask_noise_space", text="",)
                
                tocol.separator(factor=0.1)

                noise_sett = tocol.column(align=True)
                noise_sett.scale_y = 0.9
                noise_sett.label(text=translate("Settings")+":")

                noise_sett.prop(psy_api, f"{mask_api}_mask_noise_scale",)
                noise_sett.prop(psy_api, f"{mask_api}_mask_noise_brightness",)
                noise_sett.prop(psy_api, f"{mask_api}_mask_noise_contrast",)

                sed = noise_sett.row(align=True)
                sed.prop(psy_api, f"{mask_api}_mask_noise_seed")
                sedbutton = sed.row(align=True)
                sedbutton.scale_x = 1.2
                sedbutton.prop(psy_api,f"{mask_api}_mask_noise_is_random_seed", icon_value=cust_icon("W_DICE"), text="",)
            

    return None

def draw_feature_influence(layout=None, system=None, api_name="",):
    """draw the feature influence api"""

    col=layout.column(align=True)
    lbl=col.row()
    lbl.scale_y = 0.9
    lbl.label(text=translate("Influence")+":")

    #loop the 4 possible domain influence, density, scale or rotation 2x

    for dom in ("dist","scale","nor","tan"): 

        domain_api = f"{api_name}_{dom}"
        prop = f"{domain_api}_infl_allow"

        #is property domain supported? 
        if (prop not in system.bl_rna.properties.keys()): 
            continue

        allow = getattr(system,prop)
            
        #enable influence
        row = col.row(align=True)
        enabled = getattr(system, prop)
        
        row.prop(system, prop, text="", icon="CHECKBOX_HLT" if enabled else "CHECKBOX_DEHLT",)

        row = row.row(align=True)
        row.enabled = enabled

        #influence value 
        row.prop(system, f"{domain_api}_influence")

        #influence revert if exists?
        rev_api = f"{domain_api}_revert"
        if (rev_api in system.bl_rna.properties.keys()): 
            row.prop(system, rev_api, text="", icon="ARROW_LEFTRIGHT",)

        continue

    return None 


# ooo        ooooo            o8o                   ooooooooo.                                   oooo
# `88.       .888'            `"'                   `888   `Y88.                                 `888
#  888b     d'888   .oooo.   oooo  ooo. .oo.         888   .d88'  .oooo.   ooo. .oo.    .ooooo.   888
#  8 Y88. .P  888  `P  )88b  `888  `888P"Y88b        888ooo88P'  `P  )88b  `888P"Y88b  d88' `88b  888
#  8  `888'   888   .oP"888   888   888   888        888          .oP"888   888   888  888ooo888  888
#  8    Y     888  d8(  888   888   888   888        888         d8(  888   888   888  888    .o  888
# o8o        o888o `Y888""8o o888o o888o o888o      o888o        `Y888""8o o888o o888o `Y8bod8P' o888o


def draw_tweaking_panel(self, layout, context,):
    """draw main tweaking panel"""

    scat_scene, scat_ui, scat_win, emitter, psy_active, group_active = get_props()

    main = layout.column()

    ui_templates.separator_box_out(main)
    ui_templates.separator_box_out(main)

    draw_particle_selection(self, main, context,)
    ui_templates.separator_box_out(main)

    if (group_active is not None):
        
    
        draw_group_masks(self, main)
        ui_templates.separator_box_out(main)

        draw_group_scale(self, main)
        ui_templates.separator_box_out(main)

        draw_group_pattern(self, main)
        ui_templates.separator_box_out(main)

        """
        #Really needed?
        draw_group_members(self, main)
        ui_templates.separator_box_out(main)

        #Maybe later?
        draw_group_distribution(self, main)
        ui_templates.separator_box_out(main)
        """
    
    elif (psy_active is not None):
        

        
        draw_particle_surface(self, main)
        ui_templates.separator_box_out(main)

        draw_particle_distribution(self, main)
        ui_templates.separator_box_out(main)

        draw_particle_masks(self, main)
        ui_templates.separator_box_out(main)

        draw_particle_rot(self, main)
        ui_templates.separator_box_out(main)

        draw_particle_scale(self, main, context)
        ui_templates.separator_box_out(main)

        draw_particle_pattern(self, main)
        ui_templates.separator_box_out(main)

        if (psy_active.is_using_surf): #don't draw abiotic if user is not using any surfaces (ex projempties dist method)
            draw_particle_abiotic(self, main)
            ui_templates.separator_box_out(main)

        draw_particle_ecosystem(self, main)
        ui_templates.separator_box_out(main)

        draw_particle_proximity(self, main)
        ui_templates.separator_box_out(main)

        draw_particle_push(self, main)
        ui_templates.separator_box_out(main)
                
        draw_particle_wind(self, main)
        ui_templates.separator_box_out(main)

        draw_particle_visibility(self, main)
        ui_templates.separator_box_out(main)

        draw_particle_instances(self, main)
        ui_templates.separator_box_out(main)

        if (psy_active.s_instances_method=="ins_collection"): #don't draw display method if user decided to only display raw pts
            draw_particle_display(self, main)
            ui_templates.separator_box_out(main)
        


    ui_templates.separator_box_out(main)
    ui_templates.separator_box_out(main)

    return 


#  .oooooo..o           oooo                          .    o8o                                   .o.
# d8P'    `Y8           `888                        .o8    `"'                                  .888.
# Y88bo.       .ooooo.   888   .ooooo.   .ooooo.  .o888oo oooo   .ooooo.  ooo. .oo.            .8"888.     oooo d8b  .ooooo.   .oooo.
#  `"Y8888o.  d88' `88b  888  d88' `88b d88' `"Y8   888   `888  d88' `88b `888P"Y88b          .8' `888.    `888""8P d88' `88b `P  )88b
#      `"Y88b 888ooo888  888  888ooo888 888         888    888  888   888  888   888         .88ooo8888.    888     888ooo888  .oP"888
# oo     .d8P 888    .o  888  888    .o 888   .o8   888 .  888  888   888  888   888        .8'     `888.   888     888    .o d8(  888
# 8""88888P'  `Y8bod8P' o888o `Y8bod8P' `Y8bod8P'   "888" o888o `Y8bod8P' o888o o888o      o88o     o8888o d888b    `Y8bod8P' `Y888""8o


def draw_particle_selection(self, layout, context,):

    scat_scene, scat_ui, scat_win, emitter, psy_active, group_active = get_props()

    extra_layout, box, is_open = ui_templates.box_panel(layout, 
        panelopen_propname="ui_tweak_select", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_tweak_select");BOOL_VALUE(1)
        panel_icon="PARTICLES", 
        panel_name=translate("System(s) List"),
        popover_info="SCATTER5_PT_docs", 
        popover_uilayout_context_set="ui_tweak_select",
        return_subpanel=True,
        )
    if is_open:

        from .ui_system_list import draw_particle_selection_inner
        draw_particle_selection_inner(layout=box, context=context, extra_layout=extra_layout, scat_scene=scat_scene, emitter=emitter, psy_active=psy_active, group_active=group_active,)

        ui_templates.separator_box_in(box)

    return None



#  .oooooo..o                       .o88o.
# d8P'    `Y8                       888 `"
# Y88bo.      oooo  oooo  oooo d8b o888oo   .oooo.    .ooooo.   .ooooo.   .oooo.o
#  `"Y8888o.  `888  `888  `888""8P  888    `P  )88b  d88' `"Y8 d88' `88b d88(  "8
#      `"Y88b  888   888   888      888     .oP"888  888       888ooo888 `"Y88b.
# oo     .d8P  888   888   888      888    d8(  888  888   .o8 888    .o o.  )88b
# 8""88888P'   `V88V"V8P' d888b    o888o   `Y888""8o `Y8bod8P' `Y8bod8P' 8""888P'

def draw_particle_surface(self,layout):

    scat_scene, scat_ui, scat_win, emitter, psy_active, group_active = get_props()
    surf_len = 0 if (psy_active is None) else len(psy_active.get_surfaces())

    box, is_open = ui_templates.box_panel(layout, 
        panelopen_propname="ui_tweak_surface", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_tweak_surface");BOOL_VALUE(0)
        panel_icon="SURFACE_NSURFACE", 
        panel_name=translate("Surfaces") if (psy_active is None) else translate("Surfaces") +f" [{surf_len}]",
        popover_info="SCATTER5_PT_docs", 
        popover_gearwheel="SCATTER5_PT_per_settings_category_header",
        popover_uilayout_context_set="s_surface",
        is_tweaking_panel=True,
        )
    if is_open:

            if warnings(box):
                return None

            ui_is_active, ui_is_enabled = True, True
            ui_is_enabled = lock_check(psy_active, s_category="s_surface", prop=ui_is_enabled,)
            if (psy_active.is_linked): ui_is_enabled = False

            main = box.column()
            main.active = ui_is_active
            main.enabled = ui_is_enabled

            mainr = main.row()
            mainr1 = mainr.row()
            mainr1.separator(factor=0.3) 
            mainr2 = mainr.row()

            col = mainr2.column(align=True)

            ########## ########## Method

            ptr = col.row()
            ptr_lbl = ptr.row()
            ptr_lbl.scale_x = 0.55
            ptr_lbl.label(text=translate("Surface")+":")
            ptr_col = ptr.column(align=True)
            ptr_col.prop(psy_active,"s_surface_method", text="", )

            col.separator(factor=1.5)

            match psy_active.s_surface_method:
                
                case "emitter":
                    prop = col.column(align=True)
                    ptr = prop.row(align=True)
                    ptr.enabled = False
                    ptr.prop(scat_scene, "emitter", text="", icon_value=cust_icon("W_EMITTER"),)

                case "object":
                    prop = col.column(align=True)
                    ptr = prop.row(align=True)
                    ptr.prop(psy_active,"s_surface_object", text="",)

                case "collection":
                    prop = col.column(align=True)
                    ptr = prop.row(align=True)
                    draw_coll_str_ptr(layout=ptr, system=psy_active, api="s_surface_collection", revert_api="", add_coll_name="ScatterSurfaces", add_parent_name="Geo-Scatter Surfaces",)

            #Separator 

            ui_templates.separator_box_in(box)

    return 

# oooooooooo.    o8o               .             o8o   .o8                       .    o8o
# `888'   `Y8b   `"'             .o8             `"'  "888                     .o8    `"'
#  888      888 oooo   .oooo.o .o888oo oooo d8b oooo   888oooo.  oooo  oooo  .o888oo oooo   .ooooo.  ooo. .oo.
#  888      888 `888  d88(  "8   888   `888""8P `888   d88' `88b `888  `888    888   `888  d88' `88b `888P"Y88b
#  888      888  888  `"Y88b.    888    888      888   888   888  888   888    888    888  888   888  888   888
#  888     d88'  888  o.  )88b   888 .  888      888   888   888  888   888    888 .  888  888   888  888   888
# o888bood8P'   o888o 8""888P'   "888" d888b    o888o  `Y8bod8P'  `V88V"V8P'   "888" o888o `Y8bod8P' o888o o888o


def draw_particle_distribution(self,layout):

    scat_scene, scat_ui, scat_win, emitter, psy_active, group_active = get_props()

    box, is_open = ui_templates.box_panel(layout, 
        panelopen_propname="ui_tweak_distribute", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_tweak_distribute");BOOL_VALUE(0)
        panel_icon="STICKY_UVS_DISABLE", 
        panel_name=translate("Distribution"),
        popover_info="SCATTER5_PT_docs", 
        popover_gearwheel="SCATTER5_PT_per_settings_category_header",
        popover_uilayout_context_set="s_distribution",
        is_tweaking_panel=True,
        )
    if is_open:

            if warnings(box):
                return None

            ui_is_active, ui_is_enabled = True, True
            ui_is_enabled = lock_check(psy_active, s_category="s_distribution", prop=ui_is_enabled,)
            if (psy_active.is_linked): ui_is_enabled = False
    
            main = box.column()
            main.active = ui_is_active
            main.enabled = ui_is_enabled

            ########## ########## Draw Distribution

            mainr = main.row()            
            mainr1 = mainr.row()
            mainr2 = mainr.row()

            col = mainr2.column(align=True)

            ########## ########## Distribution Method 

            method = col.row()
            method_lbl = method.row()
            method_lbl.scale_x = 0.55
            method_lbl.label(text=translate("Method")+":")
            method_col = method.column(align=True)
            method_col.prop(psy_active, "s_distribution_method", text="",)

            match psy_active.s_distribution_method:

                case "random": ########## ########## Random
                    
                    col.separator()

                    space = col.row()
                    space_lbl = space.row()
                    space_lbl.scale_x = 0.55
                    space_lbl.label(text=translate("Space")+":")
                    space_col = space.column(align=True)
                    space_col.prop(psy_active, "s_distribution_space", text="",)

                    col.separator(factor=1.5)

                    densco = col.column(align=True)
                    densmeth = densco.row(align=True)
                    densmeth.scale_y = 0.85
                    densmeth.prop(psy_active, "s_distribution_is_count_method", expand=True,)
                    densapi = "s_distribution_density" if (psy_active.s_distribution_is_count_method=="density") else "s_distribution_count"
                    densslider = densco.row(align=True)
                    densslider.prop(psy_active, densapi)

                    col.separator()

                    coef = col.column(align=True)
                    coef.scale_y = 0.9
                    coef_prop = coef.row(align=True)
                    coef_prop.prop(psy_active, "ui_distribution_coef")
                    coef_op = coef.row(align=True)
                    coef_op.scale_y = 0.9
                    op = coef_op.operator("scatter5.property_coef", text="*"); op.operation="*" ; op.prop=densapi ; op.coef=psy_active.ui_distribution_coef
                    op = coef_op.operator("scatter5.property_coef", text="/"); op.operation="/" ; op.prop=densapi ; op.coef=psy_active.ui_distribution_coef
                    op = coef_op.operator("scatter5.property_coef", text="+"); op.operation="+" ; op.prop=densapi ; op.coef=psy_active.ui_distribution_coef
                    op = coef_op.operator("scatter5.property_coef", text="-"); op.operation="-" ; op.prop=densapi ; op.coef=psy_active.ui_distribution_coef

                    col.separator()

                    sed = col.row(align=True)
                    sed.prop(psy_active, "s_distribution_seed")
                    sedbutton = sed.row(align=True)
                    sedbutton.scale_x = 1.2
                    sedbutton.prop(psy_active,"s_distribution_is_random_seed", icon_value=cust_icon("W_DICE"), text="",)

                    col.separator()

                    tocol, is_toggled = ui_templates.bool_toggle(col, psy_active, "s_distribution_limit_distance_allow",
                        label=translate("Limit Self-Collision"),
                        icon="AUTOMERGE_ON" if psy_active.s_distribution_limit_distance_allow else "AUTOMERGE_OFF",
                        use_layout_left_spacer=False,
                        return_sublayout=True,
                        )
                    if is_toggled:

                        tocol.prop(psy_active, "s_distribution_limit_distance")


                case "random_stable": ########## ########## Random Stable 

                    col.separator()

                    space = col.row()
                    space_lbl = space.row()
                    space_lbl.scale_x = 0.55
                    space_lbl.label(text=translate("Space")+":")
                    space_col = space.column(align=True)
                    space_col.scale_x = 0.95

                    ptr = space_col.row(align=True)
                    ptr.alert = ( bool(psy_active.s_distribution_stable_uv_ptr) and not is_attr_surfs_shared(system=psy_active, attr_type='uv', attr_name=psy_active.s_distribution_stable_uv_ptr,) )
                    ptr.prop(psy_active, "s_distribution_stable_uv_ptr", text="", icon="GROUP_UVS", placeholder=" "+translate("UV Map"),)

                    col.separator(factor=1.5)

                    densco = col.column(align=True)
                    densmeth = densco.row(align=True)
                    densmeth.scale_y = 0.85
                    densmeth.prop(psy_active, "s_distribution_stable_is_count_method", expand=True,)
                    densapi = "s_distribution_stable_density" if (psy_active.s_distribution_stable_is_count_method=="density") else "s_distribution_stable_count"
                    densslider = densco.row(align=True)
                    densslider.prop(psy_active, densapi)

                    col.separator()

                    coef = col.column(align=True)
                    coef.scale_y = 0.9
                    coef_prop = coef.row(align=True)
                    coef_prop.prop(psy_active, "ui_distribution_stable_coef")
                    coef_op = coef.row(align=True)
                    coef_op.scale_y = 0.9
                    op = coef_op.operator("scatter5.property_coef", text="*"); op.operation="*" ; op.prop=densapi ; op.coef=psy_active.ui_distribution_stable_coef
                    op = coef_op.operator("scatter5.property_coef", text="/"); op.operation="/" ; op.prop=densapi ; op.coef=psy_active.ui_distribution_stable_coef
                    op = coef_op.operator("scatter5.property_coef", text="+"); op.operation="+" ; op.prop=densapi ; op.coef=psy_active.ui_distribution_stable_coef
                    op = coef_op.operator("scatter5.property_coef", text="-"); op.operation="-" ; op.prop=densapi ; op.coef=psy_active.ui_distribution_stable_coef

                    col.separator()

                    sed = col.row(align=True)
                    sed.prop(psy_active, "s_distribution_stable_seed")
                    sedbutton = sed.row(align=True)
                    sedbutton.scale_x = 1.2
                    sedbutton.prop(psy_active,"s_distribution_stable_is_random_seed", icon_value=cust_icon("W_DICE"), text="",)

                    col.separator()

                    tocol, is_toggled = ui_templates.bool_toggle(col, psy_active, "s_distribution_stable_limit_distance_allow", 
                        label=translate("Limit Self-Collision"), 
                        icon="AUTOMERGE_ON" if psy_active.s_distribution_stable_limit_distance_allow else "AUTOMERGE_OFF", 
                        use_layout_left_spacer=False,
                        return_sublayout=True,
                        )
                    if is_toggled:

                        tocol.prop(psy_active, "s_distribution_stable_limit_distance")


                case "clumping": ########## ########## Clumping 

                    methodinfo = method.row()
                    method_lbl.scale_x = 0.63
                    methodinfo.scale_x = 0.9
                    methodinfo.emboss = "NONE"
                    methodinfo.context_string_set("pass_ui_arg_popover","distinfos_clumping")
                    methodinfo.popover(panel="SCATTER5_PT_docs", text="", icon="INFO",)

                    col.separator()

                    space = col.row()
                    space_lbl = space.row()
                    space_lbl.scale_x = 0.55
                    space_lbl.label(text=translate("Space")+":")
                    space_col = space.column(align=True)
                    space_col.prop(psy_active, "s_distribution_clump_space", text="",)

                    col.separator(factor=1.5)

                    col.prop(psy_active, "s_distribution_clump_density")

                    row = col.row(align=True)
                    row.prop(psy_active, "s_distribution_clump_seed")
                    button = row.row(align=True)
                    button.scale_x = 1.2
                    button.prop(psy_active, "s_distribution_clump_is_random_seed", icon_value=cust_icon("W_DICE"), text="",)

                    col.separator()

                    tocol, is_toggled = ui_templates.bool_toggle(col, psy_active, "s_distribution_clump_limit_distance_allow",
                        label=translate("Limit Self-Collision"),
                        icon="AUTOMERGE_ON" if psy_active.s_distribution_clump_limit_distance_allow else "AUTOMERGE_OFF", 
                        use_layout_left_spacer=False,
                        return_sublayout=True,
                        )
                    if is_toggled:

                        tocol.prop(psy_active, "s_distribution_clump_limit_distance")

                        tocol.separator(factor=0.2)
                        
                    col.separator()
                    
                    col.prop(psy_active, "s_distribution_clump_max_distance")
                    col.prop(psy_active, "s_distribution_clump_falloff")
                    col.prop(psy_active, "s_distribution_clump_random_factor")

                    col.separator(factor=0.65)

                    #Remap Graph UI
                    draw_transition_control_feature(layout=col, psy_active=psy_active, api="s_distribution_clump", fallnoisy=True,)

                    #Children Settings 

                    col.separator(factor=2.0)

                    #col.label(text=translate("Children")+":",)
                    
                    col.prop(psy_active,"s_distribution_clump_children_density")

                    row = col.row(align=True)
                    row.prop(psy_active, "s_distribution_clump_children_seed")
                    button = row.row(align=True)
                    button.scale_x = 1.2
                    button.prop(psy_active, "s_distribution_clump_children_is_random_seed", icon_value=cust_icon("W_DICE"), text="",)

                    col.separator()

                    tocol, is_toggled = ui_templates.bool_toggle(col, psy_active, "s_distribution_clump_children_limit_distance_allow", 
                        label=translate("Limit Self-Collision"), 
                        icon="AUTOMERGE_ON" if psy_active.s_distribution_clump_children_limit_distance_allow else "AUTOMERGE_OFF", 
                        use_layout_left_spacer=False,
                        return_sublayout=True,
                        )
                    if is_toggled:

                        tocol.prop(psy_active, "s_distribution_clump_children_limit_distance")

                        tocol.separator(factor=0.5)


                case "verts": ########## ########## Per Verts

                    col.separator()

                    space = col.row()
                    space_lbl = space.row()
                    space_lbl.scale_x = 0.55
                    space_lbl.label(text=translate("Space")+":")
                    space_col = space.column(align=True)
                    space_col.prop(psy_active, "s_distribution_vfe_space", text="",)


                case "faces": ########## ########## Per Faces

                    methodinfo = method.row()
                    method_lbl.scale_x = 0.63
                    methodinfo.scale_x = 0.9
                    methodinfo.emboss = "NONE"
                    methodinfo.context_string_set("pass_ui_arg_popover","distinfos_faces")
                    methodinfo.popover(panel="SCATTER5_PT_docs", text="", icon="INFO",)

                    col.separator()

                    space = col.row()
                    space_lbl = space.row()
                    space_lbl.scale_x = 0.55
                    space_lbl.label(text=translate("Space")+":")
                    space_col = space.column(align=True)
                    space_col.prop(psy_active, "s_distribution_vfe_space", text="",)


                case "edges": ########## ########## Per Edges

                    methodinfo = method.row()
                    method_lbl.scale_x = 0.63
                    methodinfo.scale_x = 0.9
                    methodinfo.emboss = "NONE"
                    methodinfo.context_string_set("pass_ui_arg_popover","distinfos_edges")
                    methodinfo.popover(panel="SCATTER5_PT_docs", text="", icon="INFO",)

                    col.separator()

                    space = col.row()
                    space_lbl = space.row()
                    space_lbl.scale_x = 0.55
                    space_lbl.label(text=translate("Space")+":")
                    space_col = space.column(align=True)
                    space_col.prop(psy_active, "s_distribution_vfe_space", text="",)

                    col.separator()

                    select = col.row()
                    select_lbl = select.row()
                    select_lbl.scale_x = 0.55
                    select_lbl.label(text=translate("Select")+":")
                    select_col = select.column(align=True)
                    select_col.prop(psy_active, "s_distribution_edges_selection_method", text="",)

                    col.separator()

                    posi = col.row()
                    posi_lbl = posi.row()
                    posi_lbl.scale_x = 0.55
                    posi_lbl.label(text=translate("Position")+":")
                    posi_col = posi.column(align=True)
                    posi_col.prop(psy_active, "s_distribution_edges_position_method", text="",)


                case "volume": ########## ########## Per Edges

                    methodinfo = method.row()
                    method_lbl.scale_x = 0.63
                    methodinfo.scale_x = 0.9
                    methodinfo.emboss = "NONE"
                    methodinfo.context_string_set("pass_ui_arg_popover","distinfos_volume")
                    methodinfo.popover(panel="SCATTER5_PT_docs", text="", icon="INFO",)

                    col.separator()

                    sub = col.row()
                    sub_lbl = sub.row()
                    sub_lbl.scale_x = 0.55
                    sub_lbl.label(text=translate("Type")+":")
                    sub_col = sub.column(align=True)
                    sub_col.prop(psy_active, "s_distribution_volume_method", text="",)
                    
                    col.separator()

                    space = col.row()
                    space_lbl = space.row()
                    space_lbl.scale_x = 0.55
                    space_lbl.label(text=translate("Space")+":")
                    space_col = space.column(align=True)
                    space_col.prop(psy_active, "s_distribution_volume_space", text="",)

                    col.separator(factor=1.5)
                    
                    col.prop(psy_active, "s_distribution_volume_voxelsize")
                        
                    col.separator()
                    
                    match psy_active.s_distribution_volume_method:
                        
                        case "random":
                            
                            densco = col.column(align=True)
                            densmeth = densco.row(align=True)
                            densmeth.scale_y = 0.85
                            densmeth.prop(psy_active, "s_distribution_volume_is_count_method", expand=True,)
                            densapi = "s_distribution_volume_density" if (psy_active.s_distribution_volume_is_count_method=="density") else "s_distribution_volume_count"
                            densslider = densco.row(align=True)
                            densslider.prop(psy_active, densapi)

                            col.separator()

                            coef = col.column(align=True)
                            coef.scale_y = 0.9
                            coef_prop = coef.row(align=True)
                            coef_prop.prop(psy_active, "ui_distribution_volume_coef")
                            coef_op = coef.row(align=True)
                            coef_op.scale_y = 0.9
                            op = coef_op.operator("scatter5.property_coef", text="*"); op.operation="*" ; op.prop=densapi ; op.coef=psy_active.ui_distribution_volume_coef
                            op = coef_op.operator("scatter5.property_coef", text="/"); op.operation="/" ; op.prop=densapi ; op.coef=psy_active.ui_distribution_volume_coef
                            op = coef_op.operator("scatter5.property_coef", text="+"); op.operation="+" ; op.prop=densapi ; op.coef=psy_active.ui_distribution_volume_coef
                            op = coef_op.operator("scatter5.property_coef", text="-"); op.operation="-" ; op.prop=densapi ; op.coef=psy_active.ui_distribution_volume_coef

                            col.separator()

                            sed = col.row(align=True)
                            sed.prop(psy_active, "s_distribution_volume_seed")
                            sedbutton = sed.row(align=True)
                            sedbutton.scale_x = 1.2
                            sedbutton.prop(psy_active,"s_distribution_volume_is_random_seed", icon_value=cust_icon("W_DICE"), text="",)
            
                            col.separator()

                            tocol, is_toggled = ui_templates.bool_toggle(col, psy_active, "s_distribution_volume_limit_distance_allow", 
                                label=translate("Limit Self-Collision"), 
                                icon="AUTOMERGE_ON" if psy_active.s_distribution_volume_limit_distance_allow else "AUTOMERGE_OFF", 
                                use_layout_left_spacer=False,
                                return_sublayout=True,
                                )
                            if is_toggled:

                                tocol.prop(psy_active, "s_distribution_volume_limit_distance")
                                
                        case "grid":
                            
                            col.prop(psy_active, "s_distribution_volume_grid_spacing")



                case "manual_all": ########## ########## Manual

                    methodinfo = method.row()
                    method_lbl.scale_x = 0.63
                    methodinfo.scale_x = 0.9
                    methodinfo.emboss = "NONE"
                    methodinfo.context_string_set("pass_ui_arg_popover","distinfos_manual")
                    methodinfo.popover(panel="SCATTER5_PT_docs", text="", icon="INFO",)

                    col.separator()

                    space = col.row()
                    space_lbl = space.row()
                    space_lbl.scale_x = 0.55
                    space_lbl.label(text=translate("Space")+":")
                    space_col = space.column(align=True)
                    space_col.enabled = False
                    space_col.prop(scat_win, "dummy_local_only", text="",)

                    col.separator(factor=0.5)

                    row  = box.row()
                    row1 = row.row() ; row1.scale_x = 0.17
                    row2 = row.row()
                    row3 = row.row() ; row3.scale_x = 0.17
                    butt = row2.column()

                    buttons = butt.column(align=True)
                    buttons.scale_y = 2.0
                    if (psy_active.is_linked):
                        buttons.enabled = False
                    buttons.operator("scatter5.manual_enter")
                    
                    """
                    # ------------------------------------------------------------------------------------------
                    # NOTE: testing new tool base class, remove when finished..
                    # ------------------------------------------------------------------------------------------
                    from ..manual import debug, brushes
                    if(debug.debug_mode()):
                        butt.separator()
                        c = butt.column()
                        # c.scale_y = 1.2
                        c.alert = brushes.ToolBox.tool is not None
                        # # c.operator("scatter5.manual_brush_tool_base")
                        # cc = c.column(align=True)
                        # cc.operator("scatter5.manual_brush_tool_dot")
                        # cc.operator("scatter5.manual_brush_tool_pose")
                        # cc.operator("scatter5.manual_brush_tool_path")
                        # cc.operator("scatter5.manual_brush_tool_chain")
                        # cc.operator("scatter5.manual_brush_tool_spatter")
                        # cc.operator("scatter5.manual_brush_tool_spray")
                        # cc.operator("scatter5.manual_brush_tool_spray_aligned")
                        # cc.operator("scatter5.manual_brush_tool_lasso_fill")
                        # cc = c.column(align=True)
                        # cc.operator("scatter5.manual_brush_tool_eraser")
                        # cc.operator("scatter5.manual_brush_tool_dilute")
                        # cc = c.column(align=True)
                        # cc.operator("scatter5.manual_brush_tool_smooth")
                        # cc.operator("scatter5.manual_brush_tool_move")
                        # cc = c.column(align=True)
                        # cc.operator("scatter5.manual_brush_tool_rotation_set")
                        # cc.operator("scatter5.manual_brush_tool_random_rotation")
                        # cc.operator("scatter5.manual_brush_tool_spin")
                        # cc.operator("scatter5.manual_brush_tool_comb")
                        # cc.operator("scatter5.manual_brush_tool_z_align")
                        # cc = c.column(align=True)
                        # cc.operator("scatter5.manual_brush_tool_scale_set")
                        # cc.operator("scatter5.manual_brush_tool_grow_shrink")
                        # cc = c.column(align=True)
                        # cc.operator("scatter5.manual_brush_tool_object_set")
                        
                        '''
                        # TODO: this is only for development, inspect should not be used in production code..
                        import inspect
                        classes = inspect.getmembers(brushes, inspect.isclass)
                        tools = []
                        for _n, _c in classes:
                            if(hasattr(_c, 'tool_id')):
                                tools.append(_c)
                        
                        def button(element, bl_idname, ):
                            ls = bl_idname.split('.', 1)
                            n = ls[-1]
                            for _c in tools:
                                if(_c.bl_idname == bl_idname):
                                    break
                            t = "{} [{}]".format(_c.bl_label, brushes.ToolKeyConfigurator.get_string_shortcut_for_tool(_c.tool_id))
                            element.operator(bl_idname, text=t, )
                        
                        cc = c.column(align=True)
                        button(cc, "scatter5.manual_brush_tool_dot")
                        button(cc, "scatter5.manual_brush_tool_pose")
                        button(cc, "scatter5.manual_brush_tool_path")
                        button(cc, "scatter5.manual_brush_tool_chain")
                        button(cc, "scatter5.manual_brush_tool_spatter")
                        button(cc, "scatter5.manual_brush_tool_spray")
                        button(cc, "scatter5.manual_brush_tool_spray_aligned")
                        button(cc, "scatter5.manual_brush_tool_lasso_fill")
                        cc = c.column(align=True)
                        button(cc, "scatter5.manual_brush_tool_eraser")
                        button(cc, "scatter5.manual_brush_tool_dilute")
                        cc = c.column(align=True)
                        button(cc, "scatter5.manual_brush_tool_smooth")
                        button(cc, "scatter5.manual_brush_tool_move")
                        button(cc, "scatter5.manual_brush_tool_free_move")
                        button(cc, "scatter5.manual_brush_tool_manipulator")
                        button(cc, "scatter5.manual_brush_tool_drop_down")
                        cc = c.column(align=True)
                        button(cc, "scatter5.manual_brush_tool_rotation_set")
                        button(cc, "scatter5.manual_brush_tool_random_rotation")
                        button(cc, "scatter5.manual_brush_tool_spin")
                        button(cc, "scatter5.manual_brush_tool_comb")
                        button(cc, "scatter5.manual_brush_tool_z_align")
                        cc = c.column(align=True)
                        button(cc, "scatter5.manual_brush_tool_scale_set")
                        button(cc, "scatter5.manual_brush_tool_grow_shrink")
                        cc = c.column(align=True)
                        button(cc, "scatter5.manual_brush_tool_object_set")
                        cc = c.column(align=True)
                        button(cc, "scatter5.manual_brush_tool_debug_3d")
                        '''
                        
                        cc = c.column(align=True)
                        cc.operator("scatter5.manual_brush_tool_dot")
                        cc.operator("scatter5.manual_brush_tool_pose")
                        cc.operator("scatter5.manual_brush_tool_path")
                        cc.operator("scatter5.manual_brush_tool_chain")
                        cc.operator("scatter5.manual_brush_tool_spatter")
                        cc.operator("scatter5.manual_brush_tool_spray")
                        cc.operator("scatter5.manual_brush_tool_spray_aligned")
                        cc.operator("scatter5.manual_brush_tool_lasso_fill")
                        cc.operator("scatter5.manual_brush_tool_clone")
                        cc = c.column(align=True)
                        cc.operator("scatter5.manual_brush_tool_eraser")
                        cc.operator("scatter5.manual_brush_tool_dilute")
                        cc = c.column(align=True)
                        cc.operator("scatter5.manual_brush_tool_smooth")
                        cc.operator("scatter5.manual_brush_tool_move")
                        cc.operator("scatter5.manual_brush_tool_free_move")
                        cc.operator("scatter5.manual_brush_tool_manipulator")
                        cc.operator("scatter5.manual_brush_tool_drop_down")
                        cc = c.column(align=True)
                        cc.operator("scatter5.manual_brush_tool_rotation_set")
                        cc.operator("scatter5.manual_brush_tool_random_rotation")
                        cc.operator("scatter5.manual_brush_tool_spin")
                        cc.operator("scatter5.manual_brush_tool_comb")
                        cc.operator("scatter5.manual_brush_tool_z_align")
                        cc = c.column(align=True)
                        cc.operator("scatter5.manual_brush_tool_scale_set")
                        cc.operator("scatter5.manual_brush_tool_grow_shrink")
                        cc = c.column(align=True)
                        cc.operator("scatter5.manual_brush_tool_object_set")
                        cc = c.column(align=True)
                        cc.operator("scatter5.manual_brush_tool_debug_3d")
                        
                    # ------------------------------------------------------------------------------------------
                    """
                    
                    butt.separator()

                
                case "projbezarea": ########## ########## Project Bezier Area

                    methodinfo = method.row()
                    method_lbl.scale_x = 0.63
                    methodinfo.scale_x = 0.9
                    methodinfo.emboss = "NONE"
                    methodinfo.context_string_set("pass_ui_arg_popover","distinfos_projbezarea")
                    methodinfo.popover(panel="SCATTER5_PT_docs", text="", icon="INFO",)
                    
                    col.separator()
                    
                    space = col.row()
                    space_lbl = space.row()
                    space_lbl.scale_x = 0.55
                    space_lbl.label(text=translate("Space")+":")
                    space_col = space.column(align=True)
                    space_col.prop(psy_active, "s_distribution_projbezarea_space", text="",)

                    col.separator()
                    
                    space = col.row()
                    space_lbl = space.row()
                    space_lbl.scale_x = 0.55
                    space_lbl.label(text=translate("Bezier")+":")
                    
                    maskrwoo = space.row(align=True)
                    curve_row = maskrwoo.row(align=True)
                    curve_row.scale_x = 0.95
                    curve_row.alert = (psy_active.s_distribution_projbezarea_curve_ptr is not None and psy_active.s_distribution_projbezarea_curve_ptr.name not in bpy.context.scene.objects)
                    curve_row.prop(psy_active, "s_distribution_projbezarea_curve_ptr", text="", icon="CURVE_BEZCIRCLE",)

                    exists = (psy_active.s_distribution_projbezarea_curve_ptr is not None)
                    if (exists):
                        op = maskrwoo.operator("scatter5.draw_bezier_area", text="", icon="BRUSH_DATA", depress=scat_win.mode=="DRAW_AREA",)
                        op.edit_existing = psy_active.s_distribution_projbezarea_curve_ptr.name 
                        op.standalone = True
                    else: 
                        op = maskrwoo.operator("scatter5.add_bezier_area", text="", icon="ADD",)
                        op.api = f"bpy.context.scene.scatter5.emitter.scatter5.particle_systems['{psy_active.name}'].s_distribution_projbezarea_curve_ptr"
                    
                    col.separator(factor=1.5)
                    
                    densco = col.column(align=True)
                    densco.prop(psy_active, "s_distribution_projbezarea_density")

                    col.separator()

                    coef = col.column(align=True)
                    coef.scale_y = 0.9
                    coef_prop = coef.row(align=True)
                    coef_prop.prop(psy_active, "ui_distribution_projbezarea_coef")
                    coef_op = coef.row(align=True)
                    coef_op.scale_y = 0.9
                    op = coef_op.operator("scatter5.property_coef", text="*"); op.operation="*" ; op.prop="s_distribution_projbezarea_density" ; op.coef=psy_active.ui_distribution_projbezarea_coef
                    op = coef_op.operator("scatter5.property_coef", text="/"); op.operation="/" ; op.prop="s_distribution_projbezarea_density" ; op.coef=psy_active.ui_distribution_projbezarea_coef
                    op = coef_op.operator("scatter5.property_coef", text="+"); op.operation="+" ; op.prop="s_distribution_projbezarea_density" ; op.coef=psy_active.ui_distribution_projbezarea_coef
                    op = coef_op.operator("scatter5.property_coef", text="-"); op.operation="-" ; op.prop="s_distribution_projbezarea_density" ; op.coef=psy_active.ui_distribution_projbezarea_coef

                    col.separator()

                    sed = col.row(align=True)
                    sed.prop(psy_active, "s_distribution_projbezarea_seed")
                    sedbutton = sed.row(align=True)
                    sedbutton.scale_x = 1.2
                    sedbutton.prop(psy_active,"s_distribution_projbezarea_is_random_seed", icon_value=cust_icon("W_DICE"), text="",)
                    
                    col.separator()

                    tocol, is_toggled = ui_templates.bool_toggle(col, psy_active, "s_distribution_projbezarea_limit_distance_allow", 
                        label=translate("Limit Self-Collision"), 
                        icon="AUTOMERGE_ON" if psy_active.s_distribution_projbezarea_limit_distance_allow else "AUTOMERGE_OFF", 
                        use_layout_left_spacer=False,
                        return_sublayout=True,
                        )
                    if is_toggled:

                        tocol.prop(psy_active, "s_distribution_projbezarea_limit_distance")

                    col.separator()
                    
                    tocol, is_toggled = ui_templates.bool_toggle(col, psy_active, "s_distribution_projbezarea_projenabled", 
                        label=translate("Project On Surface(s)"), 
                        icon="SORT_ASC", 
                        use_layout_left_spacer=False,
                        return_sublayout=True,
                        )
                    if is_toggled:
                        
                        tocol.prop(psy_active, "s_distribution_projbezarea_projaxis")
                        tocol.separator(factor=0.5)
                        tocol.prop(psy_active, "s_distribution_projbezarea_projlength")
                    
                    
                case "projbezline": ########## ########## Project Bezier Line 
                    
                    methodinfo = method.row()
                    method_lbl.scale_x = 0.63
                    methodinfo.scale_x = 0.9
                    methodinfo.emboss = "NONE"
                    methodinfo.context_string_set("pass_ui_arg_popover","distinfos_projbezline")
                    methodinfo.popover(panel="SCATTER5_PT_docs", text="", icon="INFO",)

                    col.separator()

                    meth = col.row()
                    meth_lbl = meth.row()
                    meth_lbl.scale_x = 0.55
                    meth_lbl.label(text=translate("Type")+":")
                    meth_col = meth.column(align=True)
                    meth_col.prop(psy_active, "s_distribution_projbezline_method", text="",)

                    col.separator()

                    meth = col.row()
                    meth_lbl = meth.row()
                    meth_lbl.scale_x = 0.55
                    meth_lbl.label(text=translate("Incline")+":")
                    meth_col = meth.column(align=True)
                    meth_col.prop(psy_active, "s_distribution_projbezline_normal_method", text="",)
                    
                    col.separator()
                    
                    space = col.row()
                    space_lbl = space.row()
                    space_lbl.scale_x = 0.55
                    space_lbl.label(text=translate("Space")+":")
                    space_col = space.column(align=True)
                    space_col.prop(psy_active, "s_distribution_projbezline_space", text="",)
                    
                    col.separator()
                    
                    space = col.row()
                    space_lbl = space.row()
                    space_lbl.scale_x = 0.55
                    space_lbl.label(text=translate("Bezier")+":")
                    
                    maskrwoo = space.row(align=True)
                    curve_row = maskrwoo.row(align=True)
                    curve_row.scale_x = 0.95
                    curve_row.alert = (psy_active.s_distribution_projbezline_curve_ptr is not None and psy_active.s_distribution_projbezline_curve_ptr.name not in bpy.context.scene.objects)
                    curve_row.prop(psy_active, "s_distribution_projbezline_curve_ptr", text="", icon="CURVE_BEZCURVE")

                    exists = (psy_active.s_distribution_projbezline_curve_ptr is not None)
                    if (exists):
                        op = maskrwoo.operator("scatter5.draw_bezier_spline", text="", icon="BRUSH_DATA", depress=bpy.context.mode=='EDIT_CURVE')
                        op.curve_name = psy_active.s_distribution_projbezline_curve_ptr.name 
                    else: 
                        op = maskrwoo.operator("scatter5.add_bezier_spline", text="", icon="ADD", )
                        op.api = f"bpy.context.scene.scatter5.emitter.scatter5.particle_systems['{psy_active.name}'].s_distribution_projbezline_curve_ptr"
                    
                    col.separator(factor=1.5)
                    
                    densco = col.column(align=True)
                    densmeth = densco.row(align=True)
                    densmeth.scale_y = 0.85
                    densmeth.prop(psy_active, "s_distribution_projbezline_is_count_method", expand=True,)
                    psy_active

                    densapi = "s_distribution_projbezline_count" if (psy_active.s_distribution_projbezline_is_count_method=='count') else "s_distribution_projbezline_onspline_density" if (psy_active.s_distribution_projbezline_method=='onspline') else "s_distribution_projbezline_patharea_density"
                    densslider = densco.row(align=True)
                    densslider.prop(psy_active, densapi)

                    col.separator()

                    coef = col.column(align=True)
                    coef.scale_y = 0.9
                    coef_prop = coef.row(align=True)
                    coef_prop.prop(psy_active, "ui_distribution_projbezline_coef")
                    coef_op = coef.row(align=True)
                    coef_op.scale_y = 0.9
                    op = coef_op.operator("scatter5.property_coef", text="*"); op.operation="*" ; op.prop=densapi ; op.coef=psy_active.ui_distribution_projbezline_coef
                    op = coef_op.operator("scatter5.property_coef", text="/"); op.operation="/" ; op.prop=densapi ; op.coef=psy_active.ui_distribution_projbezline_coef
                    op = coef_op.operator("scatter5.property_coef", text="+"); op.operation="+" ; op.prop=densapi ; op.coef=psy_active.ui_distribution_projbezline_coef
                    op = coef_op.operator("scatter5.property_coef", text="-"); op.operation="-" ; op.prop=densapi ; op.coef=psy_active.ui_distribution_projbezline_coef
                    
                    col.separator()
                    
                    match psy_active.s_distribution_projbezline_method:
                        
                        case 'patharea': #features exclusive to patharea submethod
                            
                            sed = col.row(align=True)
                            sed.prop(psy_active, "s_distribution_projbezline_patharea_seed")
                            sedbutton = sed.row(align=True)
                            sedbutton.scale_x = 1.2
                            sedbutton.prop(psy_active,"s_distribution_projbezline_patharea_is_random_seed", icon_value=cust_icon("W_DICE"), text="",)
                            
                            col.separator()
                            
                            atocol = col.column(align=True)
                            atocol.prop(psy_active,"s_distribution_projbezline_patharea_width")
                            atocol.prop(psy_active,"s_distribution_projbezline_patharea_falloff")
                            
                            col.separator()
                            
                            #Remap Graph UI
                            draw_transition_control_feature(layout=col, psy_active=psy_active, api="s_distribution_projbezline", fallnoisy=True,)                
                            
                            col.separator()
                            
                            tocol, is_toggled = ui_templates.bool_toggle(col, psy_active, "s_distribution_projbezline_patharea_radiusinfl_allow", 
                                label=translate("Spline Radius Influence"), 
                                icon="HANDLE_AUTOCLAMPED", 
                                use_layout_left_spacer=False,
                                return_sublayout=True,
                                )
                            if is_toggled:

                                tocol.prop(psy_active,"s_distribution_projbezline_patharea_radiusinfl_factor")
                                
                                tocol.separator(factor=0.7)
                                
                            col.separator()
                            
                        case 'onspline': #features exclusive to patharea submethod
                            
                            tocol, is_toggled = ui_templates.bool_toggle(col, psy_active, "s_distribution_projbezline_creatrow_allow", 
                                label=translate("Create Rows"), 
                                icon="MOD_INSTANCE", 
                                use_layout_left_spacer=False,
                                return_sublayout=True,
                                )
                            if is_toggled:

                                tocol.prop(psy_active,"s_distribution_projbezline_creatrow_dir")

                                tocol.separator()

                                atocol = tocol.column(align=True)
                                atocol.prop(psy_active,"s_distribution_projbezline_creatrow_rows")
                                atocol.prop(psy_active,"s_distribution_projbezline_creatrow_dist")
                                atocol.prop(psy_active,"s_distribution_projbezline_creatrow_shift")
                                
                                tocol.separator(factor=0.7)
                            
                            col.separator()
                            
                            tocol, is_toggled = ui_templates.bool_toggle(col, psy_active, "s_distribution_projbezline_randoff_allow", 
                                label=translate("Randomize Distribution"), 
                                icon="W_DICE", 
                                use_layout_left_spacer=False,
                                return_sublayout=True,
                                )
                            if is_toggled:

                                atocol = tocol.column(align=True)
                                atocol.prop(psy_active, "s_distribution_projbezline_randoff_dist")

                                sed = atocol.row(align=True)
                                sed.prop(psy_active, "s_distribution_projbezline_randoff_seed")
                                sedbutton = sed.row(align=True)
                                sedbutton.scale_x = 1.2
                                sedbutton.prop(psy_active,"s_distribution_projbezline_randoff_is_random_seed", icon_value=cust_icon("W_DICE"), text="",)
                            
                                tocol.separator(factor=0.7)
                                
                            col.separator()

                            tocol, is_toggled = ui_templates.bool_toggle(col, psy_active, "s_distribution_projbezline_spread_allow", 
                                label=translate("Spread Distribution"), 
                                icon="MOD_NOISE", 
                                use_layout_left_spacer=False,
                                return_sublayout=True,
                                )
                            if is_toggled:
                                
                                tocol.prop(psy_active,"s_distribution_projbezline_spread_method") 
                                if (psy_active.s_distribution_projbezline_spread_method=="sides"):
                                    tocol.prop(psy_active,"s_distribution_projbezline_spread_dir")
                                                        
                                tocol.separator()
                                
                                atocol = tocol.column(align=True)
                                #atocol.prop(psy_active,"s_distribution_projbezline_spread_offset") not interesting option to have?
                                atocol.prop(psy_active,"s_distribution_projbezline_spread_falloff")
                                
                                row = atocol.row(align=True)
                                row.prop(psy_active, "s_distribution_projbezline_spread_seed")
                                button = row.row(align=True)
                                button.scale_x = 1.2
                                button.prop(psy_active, "s_distribution_projbezline_spread_is_random_seed", icon_value=cust_icon("W_DICE"), text="",)
                                                    
                                tocol.separator(factor=0.7)
                                                                            
                            col.separator()

                    #features available to both submethods
                    
                    tocol, is_toggled = ui_templates.bool_toggle(col, psy_active, "s_distribution_projbezline_limit_distance_allow", 
                        label=translate("Limit Self-Collision"), 
                        icon="AUTOMERGE_ON" if psy_active.s_distribution_projbezline_limit_distance_allow else "AUTOMERGE_OFF", 
                        use_layout_left_spacer=False,
                        return_sublayout=True,
                        )
                    if is_toggled:

                        tocol.prop(psy_active, "s_distribution_projbezline_limit_distance")
                        
                        tocol.separator(factor=0.7)

                    col.separator()
                    
                    tocol, is_toggled = ui_templates.bool_toggle(col, psy_active, "s_distribution_projbezline_projenabled", 
                        label=translate("Project On Surface(s)"), 
                        icon="SORT_ASC", 
                        use_layout_left_spacer=False,
                        return_sublayout=True,
                        )
                    if is_toggled:

                        tocol.prop(psy_active, "s_distribution_projbezline_projaxis")
                        tocol.separator(factor=0.5)
                        tocol.prop(psy_active, "s_distribution_projbezline_projlength")
                        
                    
                case "projempties": ########## ########## Project Empties
                    
                    methodinfo = method.row()
                    method_lbl.scale_x = 0.63
                    methodinfo.scale_x = 0.9
                    methodinfo.emboss = "NONE"
                    methodinfo.context_string_set("pass_ui_arg_popover","distinfos_projempties")
                    methodinfo.popover(panel="SCATTER5_PT_docs", text="", icon="INFO",)
                    
                    col.separator()
                    
                    space = col.row()
                    space_lbl = space.row()
                    space_lbl.scale_x = 0.55
                    space_lbl.label(text=translate("Collection")+":")
                    
                    maskrwoo = space.row(align=True)
                    coll_row = maskrwoo.row(align=True)
                    coll_row.scale_x = 0.8
                    coll_row.alert = (psy_active.s_distribution_projempties_coll_ptr!="" and psy_active.s_distribution_projempties_coll_ptr not in bpy.context.scene.collection)
                    draw_coll_str_ptr(layout=coll_row, system=psy_active, api="s_distribution_projempties_coll_ptr", add_coll_name="Distribute Empties")

                    col.separator()
                    
                    ui_templates.bool_toggle(col, psy_active, "s_distribution_projempties_empty_only", 
                        label=translate("Empty Objects Only"), 
                        icon="EMPTY_AXIS",
                        use_layout_left_spacer=False,
                        return_sublayout=False,
                        )

                    col.separator()
                    
                    tocol, is_toggled = ui_templates.bool_toggle(col, psy_active, "s_distribution_projempties_projenabled", 
                        label=translate("Project On Surface(s)"), 
                        icon="SORT_ASC", 
                        use_layout_left_spacer=False,
                        return_sublayout=True,
                        )
                    if is_toggled:
                        
                        tocol.prop(psy_active, "s_distribution_projempties_projaxis")
                        tocol.separator(factor=0.5)
                        tocol.prop(psy_active, "s_distribution_projempties_projlength")
                        
            ui_templates.separator_box_in(box)
    return 


#   .oooooo.               oooo  oooo   o8o                              ooo        ooooo                    oooo
#  d8P'  `Y8b              `888  `888   `"'                              `88.       .888'                    `888
# 888          oooo  oooo   888   888  oooo  ooo. .oo.    .oooooooo       888b     d'888   .oooo.    .oooo.o  888  oooo   .oooo.o
# 888          `888  `888   888   888  `888  `888P"Y88b  888' `88b        8 Y88. .P  888  `P  )88b  d88(  "8  888 .8P'   d88(  "8
# 888           888   888   888   888   888   888   888  888   888        8  `888'   888   .oP"888  `"Y88b.   888888.    `"Y88b.
# `88b    ooo   888   888   888   888   888   888   888  `88bod8P'        8    Y     888  d8(  888  o.  )88b  888 `88b.  o.  )88b
#  `Y8bood8P'   `V88V"V8P' o888o o888o o888o o888o o888o `8oooooo.       o8o        o888o `Y888""8o 8""888P' o888o o888o 8""888P'
#                                                        d"     YD
#                                                        "Y88888P'


def draw_particle_masks(self,layout):

    scat_scene, scat_ui, scat_win, emitter, psy_active, group_active = get_props()

    box, is_open = ui_templates.box_panel(layout, 
        panelopen_propname="ui_tweak_masks", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_tweak_masks");BOOL_VALUE(0)
        panel_icon="MOD_MASK", 
        master_category_bool="s_mask_master_allow",
        panel_name=translate("Culling Masks"),
        popover_info="SCATTER5_PT_docs",
        popover_gearwheel="SCATTER5_PT_per_settings_category_header",
        popover_uilayout_context_set="s_mask",
        is_tweaking_panel=True,
        )
    if is_open:

            if warnings(box):
                return None

            ui_is_active, ui_is_enabled = True, True
            ui_is_active = active_check(psy_active, s_category="s_mask", prop=ui_is_active,)
            ui_is_enabled = lock_check(psy_active, s_category="s_mask", prop=ui_is_enabled,)
            if (psy_active.is_linked): ui_is_enabled = False
            
            ########## ########## Vgroup

            tocol, is_toggled = ui_templates.bool_toggle(box, psy_active, "s_mask_vg_allow", 
                label=translate("Vertex-Group"), 
                icon="WPAINT_HLT", 
                enabled=ui_is_enabled,
                active=ui_is_active,
                arrowopen_propname="ui_mask_vg_allow", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_mask_vg_allow");BOOL_VALUE(1)
                return_sublayout=True,
                draw_condition=psy_active.s_distribution_method!="volume" and psy_active.is_using_surf,
                )
            if is_toggled:

                    mask_col = tocol.column(align=True)
                    mask_col.separator(factor=0.35)

                    exists = (psy_active.s_mask_vg_ptr!="")

                    #mask pointer

                    mask = mask_col.row(align=True)

                    ptr = mask.row(align=True)
                    ptr.alert = ( bool(psy_active.s_mask_vg_ptr) and not is_attr_surfs_shared(system=psy_active, attr_type='vg', attr_name=psy_active.s_mask_vg_ptr,) )
                    ptr.prop(psy_active, f"s_mask_vg_ptr", text="", icon="GROUP_VERTEX", placeholder=" "+translate("Vertex-Group"),)
                    
                    if (exists):
                        mask.prop(psy_active, f"s_mask_vg_revert", text="", icon="ARROW_LEFTRIGHT",)

                    #paint or create operator

                    op = mask.operator("scatter5.vg_quick_paint",
                        text="",
                        icon="BRUSH_DATA" if exists else "ADD",
                        depress=((bpy.context.mode=="PAINT_WEIGHT") and (getattr(bpy.context.object.vertex_groups.active,"name",'')==psy_active.s_mask_vg_ptr)),
                        )
                    op.group_name = psy_active.s_mask_vg_ptr
                    op.mode = "vg" 
                    op.api = f"emitter.scatter5.particle_systems['{psy_active.name}'].s_mask_vg_ptr"

                    tocol.separator(factor=1)

            ########## ########## Vcolor

            tocol, is_toggled = ui_templates.bool_toggle(box, psy_active, "s_mask_vcol_allow", 
                label=translate("Color Attribute"), 
                icon="VPAINT_HLT", 
                enabled=ui_is_enabled,
                active=ui_is_active,
                arrowopen_propname="ui_mask_vcol_allow", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_mask_vcol_allow");BOOL_VALUE(0)
                return_sublayout=True,
                draw_condition=psy_active.s_distribution_method!="volume" and psy_active.is_using_surf,
                )
            if is_toggled:

                    mask_col = tocol.column(align=True)

                    #mask pointer

                    mask = mask_col.row(align=True)

                    ptr = mask.row(align=True)
                    ptr.alert = ( bool(psy_active.s_mask_vcol_ptr) and not is_attr_surfs_shared(system=psy_active, attr_type='vcol', attr_name=psy_active.s_mask_vcol_ptr,) )
                    ptr.prop(psy_active, f"s_mask_vcol_ptr", text="", icon="GROUP_VCOL", placeholder=" "+translate("Color Attribute"),)

                    #color for add/paint operator 

                    exists = (psy_active.s_mask_vcol_ptr!="")
                    set_color = (1,1,1)

                    if (exists):

                        #set color
                        equivalence = {"id_picker":psy_active.s_mask_vcol_id_color_ptr,"id_greyscale":(1,1,1),"id_red":(1,0,0),"id_green":(0,1,0),"id_blue":(0,0,1),"id_black":(0,0,0),"id_white":(1,1,1),"id_saturation":(1,1,1),"id_value":(1,1,1),"id_hue":(1,1,1),"id_lightness":(1,1,1),"id_alpha":(1,1,1),}
                        set_color = equivalence[psy_active.s_mask_vcol_color_sample_method]

                        #reverse button 
                        mask.prop(psy_active, "s_mask_vcol_revert", text="", icon="ARROW_LEFTRIGHT",)

                    #add operator 

                    op = mask.operator("scatter5.vg_quick_paint",
                        text="",
                        icon="BRUSH_DATA" if exists else "ADD",
                        depress=((bpy.context.mode=="PAINT_VERTEX") and (getattr(bpy.context.object.data.color_attributes.active_color,"name",'')==psy_active.s_mask_vcol_ptr)),
                        )
                    op.group_name = psy_active.s_mask_vcol_ptr
                    op.mode = "vcol" 
                    op.set_color = set_color
                    op.api = f"emitter.scatter5.particle_systems['{psy_active.name}'].s_mask_vcol_ptr"

                    #sample method

                    if (exists): 

                        meth = mask_col.column(align=True)
                        meth.label(text=translate("Sample")+":")

                        methrow = meth.row(align=True)
                        methrow.prop(psy_active, "s_mask_vcol_color_sample_method", text="",)

                        if (psy_active.s_mask_vcol_color_sample_method=="id_picker"):
                            color = methrow.row(align=True)
                            color.scale_x = 0.35
                            color.prop(psy_active, "s_mask_vcol_id_color_ptr", text="",)

                    tocol.separator(factor=1)

            ########## ########## Bitmap

            tocol, is_toggled = ui_templates.bool_toggle(box, psy_active, "s_mask_bitmap_allow", 
                label=translate("Image"), 
                icon="TPAINT_HLT", 
                enabled=ui_is_enabled,
                active=ui_is_active,
                arrowopen_propname="ui_mask_bitmap_allow", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_mask_bitmap_allow");BOOL_VALUE(0)
                return_sublayout=True,
                draw_condition=psy_active.s_distribution_method!="volume" and psy_active.is_using_surf,
                )
            if is_toggled:

                    mask_col = tocol.column(align=True)

                    #mask pointer and add operator 

                    mask = mask_col.row(align=True)
                    
                    ptr = mask.row(align=True)
                    ptr.alert = ( bool(psy_active.s_mask_bitmap_ptr) and (psy_active.s_mask_bitmap_ptr not in bpy.data.images) )
                    ptr.prop(psy_active, "s_mask_bitmap_ptr", text="", icon="IMAGE_DATA", placeholder=" "+translate("Image"),)

                    #color for add/paint operator 

                    exists = (psy_active.s_mask_bitmap_ptr!="")
                    set_color = (0,0,0)

                    if (exists):

                        #set color
                        equivalence = {"id_picker":psy_active.s_mask_bitmap_id_color_ptr,"id_greyscale":(1,1,1),"id_red":(1,0,0),"id_green":(0,1,0),"id_blue":(0,0,1),"id_black":(0,0,0),"id_white":(1,1,1),"id_saturation":(1,1,1),"id_value":(1,1,1),"id_hue":(1,1,1),"id_lightness":(1,1,1),"id_alpha":(1,1,1),}
                        set_color = equivalence[psy_active.s_mask_bitmap_color_sample_method]

                        #reverse button 
                        mask.prop(psy_active, "s_mask_bitmap_revert", text="", icon="ARROW_LEFTRIGHT",)

                    #add operator 

                    if (not exists):

                        op = mask.operator("scatter5.image_utils", text="", icon="ADD",)
                        op.option = "new"
                        op.img_name = psy_active.s_mask_bitmap_ptr
                        op.api = f"emitter.scatter5.particle_systems['{psy_active.name}'].s_mask_bitmap_ptr"

                    else:
                        
                        imgpaint_depresscond = ( (bpy.context.mode=="PAINT_TEXTURE") and (bpy.context.scene.tool_settings.image_paint.mode=='IMAGE') and (bpy.context.scene.tool_settings.image_paint.canvas==bpy.data.images.get(psy_active.s_mask_bitmap_ptr)) and (bpy.context.object.data.uv_layers.active) and (bpy.context.object.data.uv_layers.active.name==psy_active.s_mask_bitmap_uv_ptr) )
                        op = mask.operator("scatter5.image_utils", text="", icon="BRUSH_DATA", depress=imgpaint_depresscond,)
                        op.option = "paint"
                        op.paint_color = set_color
                        op.uv_ptr = psy_active.s_mask_bitmap_uv_ptr
                        op.img_name = psy_active.s_mask_bitmap_ptr
                        op.api = f"emitter.scatter5.particle_systems['{psy_active.name}'].s_mask_bitmap_ptr"

                        mask_col.separator(factor=0.8)

                        ptr = mask_col.row(align=True)
                        ptr.alert = ( bool(psy_active.s_mask_bitmap_uv_ptr) and not is_attr_surfs_shared(system=psy_active, attr_type='uv', attr_name=psy_active.s_mask_bitmap_uv_ptr,) )
                        ptr.prop(psy_active, "s_mask_bitmap_uv_ptr", text="", icon="GROUP_UVS", placeholder=" "+translate("UV Map"),)

                        #sample method 

                        meth = mask_col.column(align=True)
                        meth.label(text=translate("Sample")+":")

                        methrow = meth.row(align=True)
                        methrow.prop(psy_active, "s_mask_bitmap_color_sample_method", text="",)

                        if (psy_active.s_mask_bitmap_color_sample_method=="id_picker"):
                            color = methrow.row(align=True)
                            color.scale_x = 0.35
                            color.prop(psy_active, "s_mask_bitmap_id_color_ptr", text="",)

                    tocol.separator(factor=1.15)

            ########## ########## Material

            tocol, is_toggled = ui_templates.bool_toggle(box, psy_active, "s_mask_material_allow", 
                label=translate("Material Slot"), 
                icon="MATERIAL", 
                enabled=ui_is_enabled,
                active=ui_is_active,
                arrowopen_propname="ui_mask_material_allow", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_mask_material_allow");BOOL_VALUE(0)
                return_sublayout=True,
                draw_condition=psy_active.s_distribution_method!="volume" and psy_active.is_using_surf,
                )
            if is_toggled:

                    mask = tocol.row(align=True)

                    ptr = mask.row(align=True)
                    ptr.alert = ( bool(psy_active.s_mask_material_ptr) and not is_attr_surfs_shared(system=psy_active, attr_type='mat', attr_name=psy_active.s_mask_material_ptr,) )
                    ptr.prop(psy_active, "s_mask_material_ptr", text="", icon="MATERIAL", placeholder=" "+translate("Material"),)
                    
                    if (psy_active.s_mask_material_ptr!=""):
                        mask.prop(psy_active, "s_mask_material_revert", text="", icon="ARROW_LEFTRIGHT",)

                    tocol.separator(factor=1)

            ########## ########## Curve 

            tocol, is_toggled = ui_templates.bool_toggle(box, psy_active, "s_mask_curve_allow", 
                label=translate("Bezier-Area"), 
                icon="CURVE_BEZCIRCLE", 
                enabled=ui_is_enabled,
                active=ui_is_active,
                arrowopen_propname="ui_mask_curve_allow", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_mask_curve_allow");BOOL_VALUE(0)
                return_sublayout=True,
                )
            if is_toggled:

                    mask = tocol.row(align=True)
                    curve_row = mask.row(align=True)
                    curve_row.alert = (psy_active.s_mask_curve_ptr is not None and psy_active.s_mask_curve_ptr.name not in bpy.context.scene.objects)
                    curve_row.prop(psy_active, "s_mask_curve_ptr", text="", icon="CURVE_BEZCIRCLE",)

                    exists = (psy_active.s_mask_curve_ptr is not None)
                    if (exists):
                        mask.prop(psy_active, "s_mask_curve_revert", text="", icon="ARROW_LEFTRIGHT",)
                        op = mask.operator("scatter5.draw_bezier_area", text="", icon="BRUSH_DATA", depress=scat_win.mode=="DRAW_AREA",)
                        op.edit_existing = psy_active.s_mask_curve_ptr.name 
                        op.standalone = True
                    else: 
                        op = mask.operator("scatter5.add_bezier_area", text="", icon="ADD",)
                        op.api = f"bpy.context.scene.scatter5.emitter.scatter5.particle_systems['{psy_active.name}'].s_mask_curve_ptr"

                    tocol.separator(factor=1)

            ########## ########## Boolean

            tocol, is_toggled = ui_templates.bool_toggle(box, psy_active, "s_mask_boolvol_allow", 
                label=translate("Boolean"), 
                icon="MOD_BOOLEAN", 
                enabled=ui_is_enabled,
                active=ui_is_active,
                arrowopen_propname="ui_mask_boolvol_allow", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_mask_boolvol_allow");BOOL_VALUE(0)
                return_sublayout=True,
                )
            if is_toggled:

                    draw_coll_str_ptr(layout=tocol, system=psy_active, api="s_mask_boolvol_coll_ptr", revert_api="s_mask_boolvol_revert", add_coll_name="Boolean-Objects",)

                    tocol.separator(factor=1)

            ########## ########## Upward Obstruction

            tocol, is_toggled = ui_templates.bool_toggle(box, psy_active, "s_mask_upward_allow", 
                label=translate("Upward-Obstruction"), 
                icon="TRIA_UP_BAR", 
                enabled=ui_is_enabled,
                active=ui_is_active,
                arrowopen_propname="ui_mask_upward_allow", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_mask_upward_allow");BOOL_VALUE(0)
                return_sublayout=True,
                )
            if is_toggled:

                    draw_coll_str_ptr(layout=tocol, system=psy_active, api="s_mask_upward_coll_ptr", revert_api="s_mask_upward_revert", add_coll_name="Upward-Objects",)

                    tocol.separator(factor=0.5)

            ui_templates.separator_box_in(box)
    return 


# ooooooooo.                 .                 .    o8o
# `888   `Y88.             .o8               .o8    `"'
#  888   .d88'  .ooooo.  .o888oo  .oooo.   .o888oo oooo   .ooooo.  ooo. .oo.
#  888ooo88P'  d88' `88b   888   `P  )88b    888   `888  d88' `88b `888P"Y88b
#  888`88b.    888   888   888    .oP"888    888    888  888   888  888   888
#  888  `88b.  888   888   888 . d8(  888    888 .  888  888   888  888   888
# o888o  o888o `Y8bod8P'   "888" `Y888""8o   "888" o888o `Y8bod8P' o888o o888o



def draw_particle_rot(self,layout):

    scat_scene, scat_ui, scat_win, emitter, psy_active, group_active = get_props()

    box, is_open = ui_templates.box_panel(layout, 
        panelopen_propname="ui_tweak_rot", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_tweak_rot");BOOL_VALUE(0)
        panel_icon="CON_ROTLIKE", 
        master_category_bool="s_rot_master_allow",
        panel_name=translate("Rotation"),
        popover_info="SCATTER5_PT_docs",
        popover_gearwheel="SCATTER5_PT_per_settings_category_header",       
        popover_uilayout_context_set="s_rot",
        is_tweaking_panel=True,
        )
    if is_open:

            if warnings(box):
                return None

            ui_is_active, ui_is_enabled = True, True
            ui_is_active = active_check(psy_active, s_category="s_rot", prop=ui_is_active,)
            ui_is_enabled = lock_check(psy_active, s_category="s_rot", prop=ui_is_enabled,)
            if (psy_active.is_linked): ui_is_enabled = False

            ########## ########## Align Z
            
            tocol, is_toggled = ui_templates.bool_toggle(box, psy_active, "s_rot_align_z_allow", 
                label=translate("Align Normal"), 
                icon="W_ARROW_NORMAL", 
                enabled=ui_is_enabled,
                active=ui_is_active,
                arrowopen_propname="ui_rot_align_z_allow", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_rot_align_z_allow");BOOL_VALUE(1)
                return_sublayout=True,
                )
            if is_toggled:

                #Normal Alignment 

                met = tocol.column(align=True)
                met.label(text=translate("Axis")+":")

                enum_row = met.row(align=True)
                
                if (psy_active.s_distribution_method=="projbezarea" and not psy_active.is_using_surf):
                    enum_row.prop(psy_active, "s_rot_align_z_method_projbezareanosurf_special", text="",)
                    current_method = psy_active.s_rot_align_z_method_projbezareanosurf_special
                elif (psy_active.s_distribution_method=="projbezline" and not psy_active.is_using_surf):
                    enum_row.prop(psy_active, "s_rot_align_z_method_projbezlinenosurf_special", text="",)
                    current_method = psy_active.s_rot_align_z_method_projbezlinenosurf_special
                elif (psy_active.s_distribution_method=="projempties" and not psy_active.is_using_surf):
                    enum_row.prop(psy_active, "s_rot_align_z_method_projemptiesnosurf_special", text="",)
                    current_method = psy_active.s_rot_align_z_method_projemptiesnosurf_special
                else:
                    enum_row.prop(psy_active, "s_rot_align_z_method", text="",)
                    current_method = psy_active.s_rot_align_z_method
                
                enum_row.prop(psy_active,"s_rot_align_z_revert", text="", icon="ARROW_LEFTRIGHT",)

                #Properties under method
                
                match current_method:
                        
                    case 'meth_align_z_random':
                        
                        met.separator()
                        seed = met.row(align=True)
                        seed.prop(psy_active, "s_rot_align_z_random_seed")
                        button = seed.row(align=True)
                        button.scale_x = 1.2
                        button.prop(psy_active, "s_rot_align_z_is_random_seed", icon_value=cust_icon("W_DICE"), text="",)

                    case 'meth_align_z_object'|'meth_align_z_origin'|'meth_align_z_normal'|'meth_align_z_camera':

                        if (current_method=="meth_align_z_object"):
                            
                            met.separator()
                            met.prop(psy_active, "s_rot_align_z_object", text="",)

                        met.separator()

                        tocol2, is_toggled2 = ui_templates.bool_toggle(met, psy_active, "s_rot_align_z_influence_allow", 
                            label=translate("Vertical Influence"), 
                            icon="EMPTY_SINGLE_ARROW", 
                            use_layout_left_spacer=False,
                            return_sublayout=True,
                            )
                        if is_toggled2:
                            tocol2.prop(psy_active, "s_rot_align_z_influence_value")
                        
                        if (current_method=="meth_align_z_normal"):
                            
                            met.separator()

                            tocol2, is_toggled2 = ui_templates.bool_toggle(met, psy_active, "s_rot_align_z_smoothing_allow", 
                                label=translate("Smoothing"), 
                                icon="MOD_SMOOTH", 
                                use_layout_left_spacer=False,
                                return_sublayout=True,
                                )
                            if is_toggled2:
                                tocol2.prop(psy_active, "s_rot_align_z_smoothing_value")
                        
                #clump distribution special 

                if (psy_active.s_distribution_method=="clumping"): 
                    met.separator(factor=1)

                tocol2, is_toggled = ui_templates.bool_toggle(met, psy_active, "s_rot_align_z_clump_allow", 
                    label=translate("Clump Influence"), 
                    icon="W_CLUMP", 
                    use_layout_left_spacer=False,
                    return_sublayout=True,
                    draw_condition=psy_active.s_distribution_method=="clumping",
                    )
                if is_toggled:
                    tocol2.prop(psy_active, "s_rot_align_z_clump_value", expand=True,)

                tocol.separator(factor=1.1)

            ########## ########## Align Y
            
            tocol, is_toggled = ui_templates.bool_toggle(box, psy_active, "s_rot_align_y_allow", 
                label=translate("Align Tangent"), 
                icon="W_ARROW_TANGENT", 
                enabled=ui_is_enabled,
                active=ui_is_active,
                arrowopen_propname="ui_rot_align_y_allow", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_rot_align_y_allow");BOOL_VALUE(0)
                return_sublayout=True,
                )
            if is_toggled:
                    
                #Tangent Alignment 

                met = tocol.column(align=True)
                met.label(text=translate("Axis")+":")

                enum_row = met.row(align=True)
                
                if (psy_active.s_distribution_method=="projbezarea" and not psy_active.is_using_surf):
                    enum_row.prop(psy_active, "s_rot_align_y_method_projbezareanosurf_special", text="",)
                    current_method = psy_active.s_rot_align_y_method_projbezareanosurf_special
                elif (psy_active.s_distribution_method=="projbezline" and not psy_active.is_using_surf):
                    enum_row.prop(psy_active, "s_rot_align_y_method_projbezlinenosurf_special", text="",)
                    current_method = psy_active.s_rot_align_y_method_projbezlinenosurf_special
                elif (psy_active.s_distribution_method=="projempties" and not psy_active.is_using_surf):
                    enum_row.prop(psy_active, "s_rot_align_y_method_projemptiesnosurf_special", text="",)
                    current_method = psy_active.s_rot_align_y_method_projemptiesnosurf_special
                else:
                    enum_row.prop(psy_active, "s_rot_align_y_method", text="",)
                    current_method = psy_active.s_rot_align_y_method
                                    
                enum_row.prop(psy_active,"s_rot_align_y_revert", text="", icon="ARROW_LEFTRIGHT",)

                #Properties under method

                match current_method:
                    
                    case 'meth_align_y_object':

                        met.separator()

                        met.prop(psy_active, "s_rot_align_y_object", text="",)

                    case 'meth_align_y_random':

                        met.separator()

                        seed = met.row(align=True)
                        seed.prop(psy_active, "s_rot_align_y_random_seed")
                        button = seed.row(align=True)
                        button.scale_x = 1.2
                        button.prop(psy_active, "s_rot_align_y_is_random_seed", icon_value=cust_icon("W_DICE"), text="",)

                    case 'meth_align_y_downslope':

                        met.separator()

                        met.prop(psy_active, "s_rot_align_y_downslope_space", text="",)
                        
                        met.separator()

                        tocol2, is_toggled2 = ui_templates.bool_toggle(met, psy_active, "s_rot_align_y_downslope_smoothing_allow", 
                            label=translate("Smoothing"), 
                            icon="MOD_SMOOTH", 
                            use_layout_left_spacer=False,
                            return_sublayout=True,
                            )
                        if is_toggled2:
                            tocol2.prop(psy_active, "s_rot_align_y_downslope_smoothing_value")
                                
                    case 'meth_align_y_flow':

                        met.separator()

                        met.prop(psy_active, "s_rot_align_y_flow_method", text="",)

                        met.separator()

                        match psy_active.s_rot_align_y_flow_method:
                            
                            case 'flow_vcol':

                                mask = met.row(align=True)

                                ptr = mask.row(align=True)
                                ptr.alert = ( bool(psy_active.s_rot_align_y_vcol_ptr) and not is_attr_surfs_shared(system=psy_active, attr_type='vcol', attr_name=psy_active.s_rot_align_y_vcol_ptr,) )
                                ptr.prop(psy_active, "s_rot_align_y_vcol_ptr", text="", icon="GROUP_VCOL", placeholder=" "+translate("Color Attribute"),)

                                op = mask.operator("scatter5.vg_quick_paint",
                                    text="",
                                    icon="VPAINT_HLT" if psy_active.s_rot_align_y_vcol_ptr else "ADD",
                                    depress=((bpy.context.mode=="PAINT_VERTEX") and (getattr(bpy.context.object.data.color_attributes.active_color,"name",'')==psy_active.s_rot_align_y_vcol_ptr)),
                                    )
                                op.group_name = psy_active.s_rot_align_y_vcol_ptr
                                op.mode = "vcol" 
                                op.api = f"emitter.scatter5.particle_systems['{psy_active.name}'].s_rot_align_y_vcol_ptr"

                                moreinfo = mask.row()
                                moreinfo.separator(factor=0.1)
                                moreinfo.emboss = "NONE"
                                moreinfo.context_string_set("pass_ui_arg_popover","get_flowmap")
                                moreinfo.popover(panel="SCATTER5_PT_docs", text="", icon="INFO",)

                            case 'flow_text':

                                #Draw Texture Data Block

                                block = met.column()
                                
                                #find node
                                patnode = psy_active.get_scatter_node("s_rot_align_y", strict=True, raise_exception=False,)
                                if (patnode is None):
                                    block.label(text="Error, Node missing")
                                    return
                                node = patnode.node_tree.nodes["texture"]

                                draw_texture_datablock(block, system=psy_active, ptr_name=f"s_rot_align_y_texture_ptr", texture_node=node, new_name=f"{psy_active.name.title()}AlignY",)

                        met.separator()

                        met.prop(psy_active, "s_rot_align_y_flow_direction",)

                tocol.separator(factor=1.1)

            ########## ########## Rotate

            tocol, is_toggled = ui_templates.bool_toggle(box, psy_active, "s_rot_add_allow", 
                label=translate("Rotate"), 
                icon="CON_ROTLIKE",
                enabled=ui_is_enabled,
                active=ui_is_active,
                arrowopen_propname="ui_rot_add_allow", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_rot_add_allow");BOOL_VALUE(0)
                return_sublayout=True,
                )
            if is_toggled:

                vec = tocol.column()
                vec.label(text=translate("Add/Random")+":")
                vecr = vec.row(align=True)
                veccol = vecr.column(align=True)
                veccol.scale_y = 0.9
                veccol.prop(psy_active,"s_rot_add_default", text="",)
                veccol = vecr.column(align=True)
                veccol.scale_y = 0.9
                veccol.prop(psy_active,"s_rot_add_random", text="",)

                tocol.separator()

                col = tocol.column(align=True)
                col.scale_y = 0.95
                seed = col.row(align=True)
                seed.prop(psy_active, "s_rot_add_seed")
                button = seed.row(align=True)
                button.scale_x = 1.2
                button.prop(psy_active, "s_rot_add_is_random_seed", icon_value=cust_icon("W_DICE"), text="",)
                col.prop(psy_active, "s_rot_add_snap")

                tocol.separator(factor=0.2)

                #Universal Masking System
                draw_universal_masks(layout=tocol, mask_api="s_rot_add", psy_api=psy_active,)

                tocol.separator()

            #Rotate Random

            tocol, is_toggled = ui_templates.bool_toggle(box, psy_active, "s_rot_random_allow", 
                label=translate("Random Rotation"),
                icon="ORIENTATION_GIMBAL",
                enabled=ui_is_enabled,
                active=ui_is_active,
                arrowopen_propname="ui_rot_random_allow", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_rot_random_allow");BOOL_VALUE(1)
                return_sublayout=True,
                )
            if is_toggled:

                col = tocol.column(align=True)
                col.label(text=translate("Values")+":")
                col.prop(psy_active, "s_rot_random_tilt_value")
                col.prop(psy_active, "s_rot_random_yaw_value")

                seed = col.row(align=True)
                seed.prop(psy_active, "s_rot_random_seed")
                button = seed.row(align=True)
                button.scale_x = 1.2
                button.prop(psy_active, "s_rot_random_is_random_seed", icon_value=cust_icon("W_DICE"), text="",)

                #Universal Masking System
                draw_universal_masks(layout=tocol, mask_api="s_rot_random", psy_api=psy_active,)

                tocol.separator()

            ########## ########## Tilting

            tocol, is_toggled = ui_templates.bool_toggle(box, psy_active, "s_rot_tilt_allow", 
                label=translate("Tilting"),
                icon="W_ARROW_SWINGY",
                enabled=ui_is_enabled,
                active=ui_is_active,
                arrowopen_propname="ui_rot_tilt_allow", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_rot_tilt_allow");BOOL_VALUE(0)
                return_sublayout=True,
                )
            if is_toggled:

                met = tocol.column()
                met.label(text=translate("Direction")+":")
                met.prop(psy_active, "s_rot_tilt_dir_method", text="",)
                
                #additional methods if flowmap or noise 
                
                match psy_active.s_rot_tilt_dir_method:
                    
                    case 'flowmap':

                        met.separator()
                        
                        met.prop(psy_active, "s_rot_tilt_method", text="",)

                        met.separator()

                        #Draw Vcol Data Block 
                        
                        match psy_active.s_rot_tilt_method:
                                
                            case 'tilt_vcol':

                                mask = met.row(align=True)

                                ptr = mask.row(align=True)
                                ptr_filled = bool(psy_active.s_rot_tilt_vcol_ptr)
                                ptr_acrossall = not is_attr_surfs_shared(system=psy_active, attr_type='vcol', attr_name=psy_active.s_rot_tilt_vcol_ptr,)
                                ptr.alert = (ptr_filled and not ptr_acrossall) or (ptr_filled and not psy_active.is_using_surf)
                                ptr.prop(psy_active, "s_rot_tilt_vcol_ptr", text="", icon="GROUP_VCOL", placeholder=" "+translate("Color Attribute"),)

                                op = mask.operator("scatter5.vg_quick_paint",
                                    text="",
                                    icon="VPAINT_HLT" if psy_active.s_rot_tilt_vcol_ptr else "ADD",
                                    depress=((bpy.context.mode=="PAINT_VERTEX") and (getattr(bpy.context.object.data.color_attributes.active_color,"name",'')==psy_active.s_rot_tilt_vcol_ptr)),
                                    )
                                op.group_name = psy_active.s_rot_tilt_vcol_ptr
                                op.mode = "vcol" 
                                op.api = f"emitter.scatter5.particle_systems['{psy_active.name}'].s_rot_tilt_vcol_ptr"

                                moreinfo = mask.row()
                                moreinfo.separator(factor=0.1)
                                moreinfo.emboss = "NONE"
                                moreinfo.context_string_set("pass_ui_arg_popover","get_flowmap")
                                moreinfo.popover(panel="SCATTER5_PT_docs", text="", icon="INFO",)

                            case 'tilt_text':    

                                #Draw Texture Data Block
                                block = met.column()
                                
                                #find node
                                patnode = psy_active.get_scatter_node("s_rot_tilt", strict=True, raise_exception=False,)
                                if (patnode is None):
                                    block.label(text="Error, Node missing")
                                    return
                                node = patnode.node_tree.nodes["texture"]
                                
                                draw_texture_datablock(block, system=psy_active, ptr_name=f"s_rot_tilt_texture_ptr", texture_node=node, new_name=f"{psy_active.name.title()}Tilt",)

                    case 'noise':
                                                
                        spaces = tocol.column()
                        spaces.label(text=translate("Space")+":")
                        
                        #space can only be global if using projempties with no projection enabled
                        if (psy_active.s_distribution_method=="projempties" and not psy_active.is_using_surf): 
                            spaces_dummy = spaces.row(align=True)
                            spaces_dummy.enabled = False
                            spaces_dummy.prop(scat_win, "dummy_global_only", text="",)
                        else: spaces.prop(psy_active, "s_rot_tilt_noise_space", text="",)
                        
                #strength

                tocol.separator(factor=0.5)

                props = tocol.column(align=True)
                props.label(text=translate("Values")+":")

                props.prop(psy_active,"s_rot_tilt_direction")
                props.prop(psy_active,"s_rot_tilt_force")

                match psy_active.s_rot_tilt_dir_method:
                    
                    case 'flowmap':
                        props.prop(psy_active,"s_rot_tilt_blue_influence")
                    
                    case 'noise':
                        props.prop(psy_active, "s_rot_tilt_noise_scale")
                        props.prop(psy_active,"s_rot_tilt_blue_influence")

                tocol.separator(factor=0.4)

                #Universal Masking System
                draw_universal_masks(layout=tocol, mask_api="s_rot_tilt", psy_api=psy_active,)

            ui_templates.separator_box_in(box)
    return 


#  .oooooo..o                     oooo
# d8P'    `Y8                     `888
# Y88bo.       .ooooo.   .oooo.    888   .ooooo.
#  `"Y8888o.  d88' `"Y8 `P  )88b   888  d88' `88b
#      `"Y88b 888        .oP"888   888  888ooo888
# oo     .d8P 888   .o8 d8(  888   888  888    .o
# 8""88888P'  `Y8bod8P' `Y888""8o o888o `Y8bod8P'


def draw_particle_scale(self, layout, context):

    scat_scene, scat_ui, scat_win, emitter, psy_active, group_active = get_props()

    extra_layout, box, is_open = ui_templates.box_panel(layout, 
        panelopen_propname="ui_tweak_scale", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_tweak_scale");BOOL_VALUE(0)
        panel_icon="OBJECT_ORIGIN",
        master_category_bool="s_scale_master_allow",
        panel_name=translate("Scale"),
        popover_info="SCATTER5_PT_docs", 
        popover_gearwheel="SCATTER5_PT_per_settings_category_header",       
        popover_uilayout_context_set="s_scale",
        is_tweaking_panel=True,
        return_subpanel=True,
        )
    if is_open:
            
            if warnings(box):
                return None

            ui_is_active, ui_is_enabled = True, True
            ui_is_active = active_check(psy_active, s_category="s_scale", prop=ui_is_active,)
            ui_is_enabled = lock_check(psy_active, s_category="s_scale", prop=ui_is_enabled,)
            if (psy_active.is_linked): ui_is_enabled = False

            ########## ########## Default Scale

            tocol, is_toggled = ui_templates.bool_toggle(box, psy_active, "s_scale_default_allow", 
                label=translate("Default Scale"), 
                icon="OBJECT_ORIGIN", 
                enabled=ui_is_enabled,
                active=ui_is_active,
                arrowopen_propname="ui_scale_default_allow", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_scale_default_allow");BOOL_VALUE(0)
                return_sublayout=True,
                )
            if is_toggled:

                spaces = tocol.column(align=True)
                spaces.label(text=translate("Space")+":")
                
                #space can only be global if using projempties with no projection enabled
                if (psy_active.s_distribution_method=="projempties" and not psy_active.is_using_surf): 
                      spaces_dummy = spaces.row()
                      spaces_dummy.enabled = False
                      spaces_dummy.prop(scat_win, "dummy_global_only", text="",)
                else: spaces.prop(psy_active, "s_scale_default_space", text="",)
                    
                tocol.separator(factor=0.5)

                vec = tocol.column()
                vec.scale_y = 0.9
                vec.prop(psy_active, "s_scale_default_value",)

                tocol.separator(factor=0.5)

                vec = tocol.column(align=True)
                vec.label(text=translate("Uniform")+":",)
                vec.prop(psy_active, "s_scale_default_multiplier",)

                tocol.separator(factor=0.5)

                coef = tocol.column(align=True)
                coef.scale_y = 0.9
                coef_prop = coef.row(align=True)
                coef_prop.prop(psy_active, "ui_scale_default_coef")
                coef_op = coef.row(align=True)
                coef_op.scale_y = 0.9
                op = coef_op.operator("scatter5.property_coef", text="*"); op.operation="*" ; op.prop="s_scale_default_multiplier" ; op.coef=psy_active.ui_scale_default_coef
                op = coef_op.operator("scatter5.property_coef", text="/"); op.operation="/" ; op.prop="s_scale_default_multiplier" ; op.coef=psy_active.ui_scale_default_coef
                op = coef_op.operator("scatter5.property_coef", text="+"); op.operation="+" ; op.prop="s_scale_default_multiplier" ; op.coef=psy_active.ui_scale_default_coef
                op = coef_op.operator("scatter5.property_coef", text="-"); op.operation="-" ; op.prop="s_scale_default_multiplier" ; op.coef=psy_active.ui_scale_default_coef

                tocol.separator()

            ########## ########## Random

            tocol, is_toggled = ui_templates.bool_toggle(box, psy_active, "s_scale_random_allow", 
                label=translate("Random Scale"), 
                icon="W_DICE", 
                enabled=ui_is_enabled,
                active=ui_is_active,
                arrowopen_propname="ui_scale_random_allow", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_scale_random_allow");BOOL_VALUE(1)
                return_sublayout=True,
                )
            if is_toggled:

                vec = tocol.column()
                vec.scale_y = 0.9
                vec.prop(psy_active, "s_scale_random_factor",)

                tocol.separator(factor=0.3)

                ccol = tocol.column(align=True)
                ccol.label(text=translate("Randomization")+":")

                row = ccol.row(align=True)
                row.prop(psy_active,"s_scale_random_method", expand=True,)

                row = ccol.row(align=True)
                row.prop(psy_active, "s_scale_random_probability",)

                rrow = ccol.row(align=True)
                prop = rrow.row(align=True)
                prop.prop(psy_active, "s_scale_random_seed")
                button = rrow.row(align=True)
                button.scale_x = 1.2
                button.prop(psy_active, "s_scale_random_is_random_seed", icon_value=cust_icon("W_DICE"), text="",)
                    
                tocol.separator(factor=0.1)

                #Universal Masking System
                draw_universal_masks(layout=tocol, mask_api="s_scale_random", psy_api=psy_active,)

                tocol.separator()

            ########## ########## Shrink Mask

            tocol, is_toggled = ui_templates.bool_toggle(box, psy_active, "s_scale_shrink_allow", 
                label=translate("Shrink"), 
                icon="W_SCALE_SHRINK", 
                enabled=ui_is_enabled,
                active=ui_is_active,
                arrowopen_propname="ui_scale_shrink_allow", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_scale_shrink_allow");BOOL_VALUE(0)
                return_sublayout=True,
                )
            if is_toggled:
                
                    vec = tocol.column()
                    vec.scale_y = 0.9
                    vec.prop(psy_active,"s_scale_shrink_factor")

                    #Universal Masking System
                    draw_universal_masks(layout=tocol, mask_api="s_scale_shrink", psy_api=psy_active,)

                    tocol.separator()
                        
            ########## ########## Grow Mask

            tocol, is_toggled = ui_templates.bool_toggle(box, psy_active, "s_scale_grow_allow", 
                label=translate("Grow"), 
                icon="W_SCALE_GROW", 
                enabled=ui_is_enabled,
                active=ui_is_active,
                arrowopen_propname="ui_scale_grow_allow", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_scale_grow_allow");BOOL_VALUE(0)
                return_sublayout=True,
                )
            if is_toggled:

                    vec = tocol.column()
                    vec.scale_y = 0.9
                    vec.prop(psy_active,"s_scale_grow_factor")

                    #Universal Masking System
                    draw_universal_masks(layout=tocol, mask_api="s_scale_grow", psy_api=psy_active,)

                    tocol.separator()

            ########## ########## Clump Distribution Special
            
            tocol, is_toggled = ui_templates.bool_toggle(box, psy_active, "s_scale_clump_allow", 
                label=translate("Clump Scale"), 
                icon="W_CLUMP_STRAIGHT", 
                enabled=ui_is_enabled,
                active=ui_is_active,
                arrowopen_propname="ui_scale_clump_allow", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_scale_clump_allow");BOOL_VALUE(0)
                return_sublayout=True,
                draw_condition=psy_active.s_distribution_method=="clumping",
                )
            if is_toggled:

                tocol.prop(psy_active, "s_scale_clump_value")

                tocol.separator()

            ########## ########## Faces Distribution Special
            
            tocol, is_toggled = ui_templates.bool_toggle(box, psy_active, "s_scale_faces_allow", 
                label=translate("Face Size Influence"), 
                icon="SURFACE_NSURFACE", 
                enabled=ui_is_enabled,
                active=ui_is_active,
                arrowopen_propname="ui_scale_faces_allow", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_scale_faces_allow");BOOL_VALUE(0)
                return_sublayout=True,
                draw_condition=psy_active.s_distribution_method=="faces",
                )
            if is_toggled:

                tocol.prop(psy_active, "s_scale_faces_value")

                tocol.separator()

            ########## ########## Edges Distribution Special
            
            tocol, is_toggled = ui_templates.bool_toggle(box, psy_active, "s_scale_edges_allow", 
                label=translate("Edge Length Influence"), 
                icon="SNAP_INCREMENT",
                enabled=ui_is_enabled,
                active=ui_is_active,
                arrowopen_propname="ui_scale_edges_allow", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_scale_edges_allow");BOOL_VALUE(0)
                return_sublayout=True,
                draw_condition=psy_active.s_distribution_method=="edges",
                )
            if is_toggled:

                vec = tocol.column()
                vec.scale_y = 0.9
                vec.prop(psy_active, "s_scale_edges_vec_factor",)

                tocol.separator()

            ########## ########## ProjBezLine Distribution Special
            
            tocol, is_toggled = ui_templates.bool_toggle(box, psy_active, "s_scale_projbezline_radius_allow", 
                label=translate("Spline Radius Influence"), 
                icon="HANDLE_AUTOCLAMPED",
                enabled=ui_is_enabled,
                active=ui_is_active,
                arrowopen_propname="ui_scale_projbezline_radius_allow", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_scale_projbezline_radius_allow");BOOL_VALUE(0)
                return_sublayout=True,
                draw_condition=psy_active.s_distribution_method=="projbezline",
                )
            if is_toggled:

                tocol.prop(psy_active, "s_scale_projbezline_radius_value")

                tocol.separator()

            ########## ########## ProjBezLine Distribution Special
            
            tocol, is_toggled = ui_templates.bool_toggle(box, psy_active, "s_scale_projempties_allow", 
                label=translate("Empties Scale Influence"), 
                icon="EMPTY_AXIS", 
                enabled=ui_is_enabled,
                active=ui_is_active,
                arrowopen_propname="ui_scale_projempties_allow", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_scale_projempties_allow");BOOL_VALUE(0)
                return_sublayout=True,
                draw_condition=psy_active.s_distribution_method=="projempties",
                )
            if is_toggled:

                tocol.prop(psy_active, "s_scale_projempties_value")

                tocol.separator()
                
            ########## ########## Mirror

            tocol, is_toggled = ui_templates.bool_toggle(box, psy_active, "s_scale_mirror_allow", 
                label=translate("Random Mirror"), 
                icon="MOD_MIRROR", 
                enabled=ui_is_enabled,
                active=ui_is_active,
                arrowopen_propname="ui_scale_mirror_allow", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_scale_mirror_allow");BOOL_VALUE(0)
                return_sublayout=True,
                draw_condition=psy_active.s_instances_method=="ins_collection",
                )
            if is_toggled:

                subcol = tocol.column(align=True)
                subcol.scale_y = 0.95
                subcol.label(text=translate("Axis")+":")
                enum = subcol.row(align=True) 
                enum.prop(psy_active, "s_scale_mirror_is_x",text="X", icon="BLANK1")
                enum.prop(psy_active, "s_scale_mirror_is_y",text="Y", icon="BLANK1")
                enum.prop(psy_active, "s_scale_mirror_is_z",text="Z", icon="BLANK1")

                rrow = subcol.row(align=True)
                prop = rrow.row(align=True)
                prop.prop(psy_active, "s_scale_mirror_seed")
                button = rrow.row(align=True)
                button.scale_x = 1.2
                button.prop(psy_active, "s_scale_mirror_is_random_seed", icon_value=cust_icon("W_DICE"), text="",)

                #Universal Masking System
                draw_universal_masks(layout=tocol, mask_api="s_scale_mirror", psy_api=psy_active,)

                tocol.separator()

            ########## ########## Scale Fading

            tocol, is_toggled = ui_templates.bool_toggle(box, psy_active, "s_scale_fading_allow", 
                label=translate("Camera Distance Fade"), 
                icon="MOD_WAVE", 
                enabled=ui_is_enabled,
                active=ui_is_active,
                arrowopen_propname="ui_scale_fading_allow", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_scale_fading_allow");BOOL_VALUE(0)
                return_sublayout=True,
                )
            if is_toggled:

                if (bpy.context.scene.camera is None):

                    tocol.separator(factor=0.3)
                    moreinfo = tocol.row()
                    moreinfo.emboss = "NONE"
                    moreinfo.context_string_set("pass_ui_arg_popover","nocamera_info")
                    moreinfo.popover(panel="SCATTER5_PT_docs", text=translate("No Camera Found"), icon="INFO",)
                    tocol.separator(factor=0.9)

                else: 

                    vec = tocol.column()
                    vec.scale_y = 0.9
                    vec.prop(psy_active,"s_scale_fading_factor")

                    tocol.separator(factor=0.65)

                    #Remap Graph UI
                    draw_transition_control_feature(layout=tocol, psy_active=psy_active, api="s_scale_fading", fallnoisy=False,)

                    tocol.separator(factor=0.35)

                    #per cam data

                    _, is_toggled3 = ui_templates.bool_toggle(tocol, psy_active, "s_scale_fading_per_cam_data", 
                        label=translate("Per Cam Settings"),
                        icon="CON_CAMERASOLVER", 
                        use_layout_left_spacer=False,
                        return_sublayout=False,
                        )
                    if is_toggled3:

                        tocol.separator(factor=0.25)

                        prop = tocol.column(align=True)
                        prop.enabled = False
                        prop.prop(bpy.context.scene, "camera", text=translate("Active"),)

                        tocol.separator(factor=0.25)

                    if (psy_active.s_scale_fading_per_cam_data):
                          opdata,opstr = bpy.context.scene.camera.scatter5,"s_scale_fading_distance_per_cam_" #min/max
                    else: opdata,opstr = psy_active,"s_scale_fading_distance_" #min/max
                        
                    prop = tocol.column(align=True)
                    prop.scale_y = 0.9
                    prop.label(text=translate("Transition")+":",)
                    
                    camdistrow = prop.row(align=True)
                    camdistrow.prop(opdata, opstr+"min",)
                    op = camdistrow.operator("scatter5.modal_measure_distance", text="", icon="EYEDROPPER",)
                    op.mode = "CameraDistance"; op.apply_sett_psyname = psy_active.name; op.apply_sett_propname = opstr+"min"; op.camera_location = bpy.context.scene.camera.location
                    #
                    camdistrow = prop.row(align=True)
                    camdistrow.prop(opdata, opstr+"max",)
                    op = camdistrow.operator("scatter5.modal_measure_distance", text="", icon="EYEDROPPER",)
                    op.mode = "CameraDistance"; op.apply_sett_psyname = psy_active.name; op.apply_sett_propname = opstr+"max"; op.camera_location = bpy.context.scene.camera.location

                    #Camera Update Method

                    tocol.separator(factor=0.65)

                    draw_camera_update_method(layout=tocol, psy_active=psy_active)

                    tocol.separator()
                    
            ########## ########## Minimal Scale

            tocol, is_toggled = ui_templates.bool_toggle(box, psy_active, "s_scale_min_allow", 
                label=translate("Minimal Scale"), 
                icon="CON_SAMEVOL", 
                enabled=ui_is_enabled,
                active=ui_is_active,
                arrowopen_propname="ui_scale_min_allow", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_scale_min_allow");BOOL_VALUE(0)
                return_sublayout=True,
                )
            if is_toggled:

                subcol = tocol.column(align=True)
                subcol.label(text=translate("Method")+":")
                enum = subcol.row(align=True) 
                enum.prop(psy_active, "s_scale_min_method", expand=True,)
                subcol.prop(psy_active, "s_scale_min_value")

            ui_templates.separator_box_in(box)
            
            ########## ########## Extra Warning Box

            from ... __init__ import addon_prefs
            
            if (addon_prefs().ui_apply_scale_warn):
                    
                applied_scales = [s.scale[:]==(1.0,1.0,1.0) for s in psy_active.get_surfaces()]
                if (not all(applied_scales)):
                    
                    box = extra_layout.box()
                    box.separator(factor=0.5)
                    word_wrap(layout=box, alignment="CENTER", active=False, icon="ERROR", max_char='auto', context=context, char_auto_sidepadding=0.85,
                        string=translate("One of your surface scale isn't applied. Use [CTRL+A] to apply the selected objects(s) transforms."),)
                    
                    ui_templates.separator_box_in(box)
            
    return 


# ooooooooo.                 .       .
# `888   `Y88.             .o8     .o8
#  888   .d88'  .oooo.   .o888oo .o888oo  .ooooo.  oooo d8b ooo. .oo.
#  888ooo88P'  `P  )88b    888     888   d88' `88b `888""8P `888P"Y88b
#  888          .oP"888    888     888   888ooo888  888      888   888
#  888         d8(  888    888 .   888 . 888    .o  888      888   888
# o888o        `Y888""8o   "888"   "888" `Y8bod8P' d888b    o888o o888o


def draw_particle_pattern(self,layout):

    scat_scene, scat_ui, scat_win, emitter, psy_active, group_active = get_props()

    big_col = layout.column(align=True)

    box, is_open = ui_templates.box_panel(big_col, 
        panelopen_propname="ui_tweak_pattern", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_tweak_pattern");BOOL_VALUE(0)
        panel_icon="TEXTURE", 
        master_category_bool="s_pattern_master_allow",
        panel_name=translate("Pattern"),
        popover_info="SCATTER5_PT_docs",
        popover_gearwheel="SCATTER5_PT_per_settings_category_header",       
        popover_uilayout_context_set="s_pattern",
        is_tweaking_panel=True,
        )
    if is_open:

            if warnings(box):
                return None

            ui_is_active, ui_is_enabled = True, True
            ui_is_active = active_check(psy_active, s_category="s_pattern", prop=ui_is_active,)
            ui_is_enabled = lock_check(psy_active, s_category="s_pattern", prop=ui_is_enabled,)
            if (psy_active.is_linked): ui_is_enabled = False
            
            ########## ########## Pattern 1,2,3

            for i in (1,2,3):

                tocol, is_toggled = ui_templates.bool_toggle(box, psy_active, f"s_pattern{i}_allow",
                    label=translate("Pattern")+f" {i}",
                    icon=f"W_PATTERN{i}", 
                    enabled=ui_is_enabled,
                    active=ui_is_active,
                    arrowopen_propname=f"ui_pattern{i}_allow", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_pattern1_allow");BOOL_VALUE(1)
                    return_sublayout=True,                     #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_pattern2_allow");BOOL_VALUE(0)
                    )                                          #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_pattern3_allow");BOOL_VALUE(0 )
                if is_toggled:

                    #Draw Texture Data Block

                    block = tocol.column()
                    
                    #find node
                    patnode = psy_active.get_scatter_node(f"s_pattern{i}", strict=True, raise_exception=False,)
                    if (patnode is None):
                        block.label(text=f"Error, Node missing")
                        return
                    node = patnode.node_tree.nodes["texture"]
                                            
                    block.label(text=translate("Texture-Data")+":")
                    draw_texture_datablock(block, system=psy_active, ptr_name=f"s_pattern{i}_texture_ptr", texture_node=node, new_name=f"{psy_active.name.title()}Pattern{i}",)

                    #Draw Particle ID specific
                        
                    tocol.separator(factor=0.75)

                    met=tocol.column(align=True)
                    met.label(text=translate("Sample")+":")
                    met.prop(psy_active, f"s_pattern{i}_color_sample_method", text="",)
                    color_sample_method = eval(f"psy_active.s_pattern{i}_color_sample_method")
                    if (color_sample_method == "id_picker"):

                        pick = met.row(align=True)
                        ptrc = pick.row(align=True)
                        ptrc.scale_x = 0.4
                        ptrc.prop(psy_active, f"s_pattern{i}_id_color_ptr", text="",)
                        pick.prop(psy_active, f"s_pattern{i}_id_color_tolerence")

                    tocol.separator(factor=0.75)

                    #Feature Influence 
                    draw_feature_influence(layout=tocol, system=psy_active, api_name=f"s_pattern{i}",)

                    tocol.separator(factor=0.5)

                    #Universal Masking System
                    draw_universal_masks(layout=tocol, mask_api=f"s_pattern{i}", psy_api=psy_active,)

                    if (i<3):
                        tocol.separator(factor=1)

            ui_templates.separator_box_in(box)
    return 


#       .o.        .o8        o8o                .    o8o
#      .888.      "888        `"'              .o8    `"'
#     .8"888.      888oooo.  oooo   .ooooo.  .o888oo oooo   .ooooo.
#    .8' `888.     d88' `88b `888  d88' `88b   888   `888  d88' `"Y8
#   .88ooo8888.    888   888  888  888   888   888    888  888
#  .8'     `888.   888   888  888  888   888   888 .  888  888   .o8
# o88o     o8888o  `Y8bod8P' o888o `Y8bod8P'   "888" o888o `Y8bod8P'


def draw_particle_abiotic(self,layout):

    scat_scene, scat_ui, scat_win, emitter, psy_active, group_active = get_props()

    box, is_open = ui_templates.box_panel(layout, 
        panelopen_propname="ui_tweak_abiotic", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_tweak_abiotic");BOOL_VALUE(0)
        panel_icon="W_TERRAIN", 
        master_category_bool="s_abiotic_master_allow",
        panel_name=translate("Abiotic"),
        popover_info="SCATTER5_PT_docs",
        popover_gearwheel="SCATTER5_PT_per_settings_category_header",       
        popover_uilayout_context_set="s_abiotic",
        is_tweaking_panel=True,
        )
    if is_open:
            
            if warnings(box):
                return None

            ui_is_active, ui_is_enabled = True, True
            ui_is_active = active_check(psy_active, s_category="s_abiotic", prop=ui_is_active,)
            ui_is_enabled = lock_check(psy_active, s_category="s_abiotic", prop=ui_is_enabled,)
            if (psy_active.is_linked): ui_is_enabled = False

            ########## ########## Elevation 

            tocol, is_toggled = ui_templates.bool_toggle(box, psy_active, "s_abiotic_elev_allow", 
                label=translate("Elevation"), 
                icon="W_ALTITUDE", 
                enabled=ui_is_enabled,
                active=ui_is_active,
                arrowopen_propname="ui_abiotic_elev_allow", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_abiotic_elev_allow");BOOL_VALUE(0)
                return_sublayout=True,
                draw_condition=psy_active.is_using_surf,
                )
            if is_toggled:

                spaces = tocol.column(align=True)
                spaces.label(text=translate("Space")+":")
                spaces.prop(psy_active, "s_abiotic_elev_space", text="",)

                tocol.separator(factor=0.6)

                method = tocol.column(align=True)
                method.label(text=translate("Method")+":")
                method.prop(psy_active, "s_abiotic_elev_method", text="",)
                prop_mthd = "local" if (psy_active.s_abiotic_elev_method=="percentage") else "global"

                tocol.separator(factor=0.9)

                #Min/Max & Falloff 

                elevprp = tocol.column(align=True)
                elevprp.label(text=translate("Range")+":",)
                elevprp.scale_y = 0.9
                
                elevprprwoo = elevprp.row(align=True)
                elevprprwoo.prop(psy_active, f"s_abiotic_elev_min_value_{prop_mthd}")  
                if ((psy_active.s_abiotic_elev_method=="altitude") and len(psy_active.get_surfaces())):
                    op = elevprprwoo.operator("scatter5.modal_measure_distance", text="", icon="EYEDROPPER")
                    op.mode = "Altitude"; op.apply_sett_psyname = psy_active.name; op.apply_sett_propname = "s_abiotic_elev_min_value_global"
                elevprp.prop(psy_active, f"s_abiotic_elev_min_falloff_{prop_mthd}")  

                elevprp.separator(factor=1.01)

                elevprprwoo = elevprp.row(align=True)
                elevprprwoo.prop(psy_active, f"s_abiotic_elev_max_value_{prop_mthd}")  
                if ((psy_active.s_abiotic_elev_method=="altitude") and len(psy_active.get_surfaces())):
                    op = elevprprwoo.operator("scatter5.modal_measure_distance", text="", icon="EYEDROPPER")
                    op.mode = "Altitude"; op.apply_sett_psyname = psy_active.name; op.apply_sett_propname = "s_abiotic_elev_max_value_global"
                elevprp.prop(psy_active, f"s_abiotic_elev_max_falloff_{prop_mthd}")  

                tocol.separator(factor=0.9)

                #Remap Graph UI
                draw_transition_control_feature(layout=tocol, psy_active=psy_active, api="s_abiotic_elev", fallnoisy=True,)

                tocol.separator(factor=0.3)

                #Feature Influence 
                draw_feature_influence(layout=tocol, system=psy_active, api_name="s_abiotic_elev",)

                tocol.separator(factor=0.5)

                #Universal Masking System
                draw_universal_masks(layout=tocol, mask_api=f"s_abiotic_elev", psy_api=psy_active,)

                tocol.separator()

            ########## ########## Slope 

            tocol, is_toggled = ui_templates.bool_toggle(box, psy_active, "s_abiotic_slope_allow", 
                label=translate("Slope"), 
                icon="W_SLOPE", 
                enabled=ui_is_enabled,
                active=ui_is_active,
                arrowopen_propname="ui_abiotic_slope_allow", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_abiotic_slope_allow");BOOL_VALUE(0)
                return_sublayout=True,
                draw_condition=psy_active.s_distribution_method!="volume" and psy_active.is_using_surf,
                )
            if is_toggled:

                spaces = tocol.column(align=True)
                spaces.label(text=translate("Space")+":")
                spaces.prop(psy_active, "s_abiotic_slope_space", text="",)

                tocol.separator(factor=0.9)

                #Min/Max & Falloff 

                slpprp = tocol.column(align=True)
                slpprp.label(text=translate("Angle")+":",)
                slpprp.scale_y = 0.9
                slpprp.prop(psy_active, "s_abiotic_slope_min_value")     
                slpprp.prop(psy_active, "s_abiotic_slope_min_falloff")     
                slpprp.separator(factor=1.01)
                slpprp.prop(psy_active, "s_abiotic_slope_max_value")     
                slpprp.prop(psy_active, "s_abiotic_slope_max_falloff")   

                tocol.separator(factor=0.9)

                #absolute slope 

                ui_templates.bool_toggle(tocol, psy_active, "s_abiotic_slope_absolute", 
                    label=translate("Absolute Slope"), 
                    icon="CON_TRANSLIKE", 
                    use_layout_left_spacer=False,
                    )

                tocol.separator(factor=0.2)
                
                tocol1, is_toggled1 = ui_templates.bool_toggle(tocol, psy_active, "s_abiotic_slope_smoothing_allow",
                    label=translate("Smoothing"), 
                    icon="MOD_SMOOTH", 
                    use_layout_left_spacer=False,
                    return_sublayout=True,
                    )
                if is_toggled1:
                    tocol1.prop(psy_active, "s_abiotic_slope_smoothing_value")
                    tocol1.separator(factor=0.3)
                
                tocol.separator(factor=0.2)

                #Remap Graph UI
                draw_transition_control_feature(layout=tocol, psy_active=psy_active, api="s_abiotic_slope", fallnoisy=True,)

                tocol.separator(factor=0.3)

                #Feature Influence
                draw_feature_influence(layout=tocol, system=psy_active, api_name="s_abiotic_slope",)

                tocol.separator(factor=0.5)

                #Universal Masking System
                draw_universal_masks(layout=tocol, mask_api=f"s_abiotic_slope", psy_api=psy_active,)

                tocol.separator()

            ########## ########## Normal 

            tocol, is_toggled = ui_templates.bool_toggle(box, psy_active, "s_abiotic_dir_allow", 
                label=translate("Orientation"), 
                icon="NORMALS_FACE", 
                enabled=ui_is_enabled,
                active=ui_is_active,
                arrowopen_propname="ui_abiotic_dir_allow", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_abiotic_dir_allow");BOOL_VALUE(0)
                return_sublayout=True,
                draw_condition=psy_active.s_distribution_method!="volume" and psy_active.is_using_surf,
                )
            if is_toggled:

                spaces = tocol.column(align=True)
                spaces.label(text=translate("Space")+":")
                spaces.prop(psy_active, "s_abiotic_dir_space", text="",)

                tocol.separator(factor=0.9)

                #Direction & Threshold

                dirprp = tocol.column()
                dirprp.scale_y = 0.9
                lbl = dirprp.row()
                lbl.label(text=translate("Angle")+":")
                rwoo = dirprp.row()
                rwoo.prop(psy_active, "s_abiotic_dir_direction", text="",)
                rowc = rwoo.column()
                rowc.scale_x = 0.55
                rowc.prop(psy_active, "ui_abiotic_dir_direction_euler", text="", expand=True,) #alias of direction

                tocol.separator(factor=0.7)

                dirprp = tocol.column(align=True,)
                dirprp.scale_y = 0.9
                dirprp.prop(psy_active, "s_abiotic_dir_max")
                dirprp.prop(psy_active, "s_abiotic_dir_treshold")

                tocol.separator(factor=0.9)

                tocol1, is_toggled1 = ui_templates.bool_toggle(tocol, psy_active, "s_abiotic_dir_smoothing_allow",
                    label=translate("Smoothing"), 
                    icon="MOD_SMOOTH", 
                    use_layout_left_spacer=False,
                    return_sublayout=True,
                    )
                if is_toggled1:
                    tocol1.prop(psy_active, "s_abiotic_dir_smoothing_value")
                    tocol1.separator(factor=0.3)
                
                tocol.separator(factor=0.2)

                #Remap Graph UI
                draw_transition_control_feature(layout=tocol, psy_active=psy_active, api="s_abiotic_dir", fallnoisy=True,)

                tocol.separator(factor=0.3)

                #Feature Influence
                draw_feature_influence(layout=tocol, system=psy_active, api_name="s_abiotic_dir",)

                tocol.separator(factor=0.5)

                #Universal Masking System
                draw_universal_masks(layout=tocol, mask_api=f"s_abiotic_dir", psy_api=psy_active,)

                tocol.separator()

            ########## ########## Curvature 

            tocol, is_toggled = ui_templates.bool_toggle(box, psy_active, "s_abiotic_cur_allow", 
                label=translate("Curvature"), 
                icon="W_CURVATURE", 
                enabled=ui_is_enabled,
                active=ui_is_active,
                arrowopen_propname="ui_abiotic_cur_allow", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_abiotic_cur_allow");BOOL_VALUE(0)
                return_sublayout=True,
                draw_condition=psy_active.s_distribution_method!="volume" and psy_active.is_using_surf,
                )
            if is_toggled:

                #Method

                spaces = tocol.column(align=True)
                spaces.label(text=translate("Method")+":")
                spaces.prop(psy_active, "s_abiotic_cur_type", text="",)

                tocol.separator(factor=0.9)
                
                #Threshold

                curprp = tocol.column(align=True,)
                curprp.scale_y = 0.9
                curprp.label(text=translate("Angle")+":")
                curprp.prop(psy_active, "s_abiotic_cur_max")
                curprp.prop(psy_active, "s_abiotic_cur_treshold")
                
                tocol.separator(factor=0.9)
                
                tocol1, is_toggled1 = ui_templates.bool_toggle(tocol, psy_active, "s_abiotic_cur_smoothing_allow",
                    label=translate("Smoothing"), 
                    icon="MOD_SMOOTH", 
                    use_layout_left_spacer=False,
                    return_sublayout=True,
                    )
                if is_toggled1:
                    tocol1.prop(psy_active, "s_abiotic_cur_smoothing_value")
                    tocol1.separator(factor=0.3)
                
                tocol.separator(factor=0.2)

                #Remap Graph UI
                draw_transition_control_feature(layout=tocol, psy_active=psy_active, api="s_abiotic_cur", fallnoisy=True,)

                tocol.separator(factor=0.3)

                #Feature Influence
                draw_feature_influence(layout=tocol, system=psy_active, api_name="s_abiotic_cur",)

                tocol.separator(factor=0.5)

                #Universal Masking System
                draw_universal_masks(layout=tocol, mask_api=f"s_abiotic_cur", psy_api=psy_active,)

                tocol.separator()

            ########## ########## Border 

            tocol, is_toggled = ui_templates.bool_toggle(box, psy_active, "s_abiotic_border_allow", 
                label=translate("Border"), 
                icon="W_BORDER", 
                enabled=ui_is_enabled,
                active=ui_is_active,
                arrowopen_propname="ui_abiotic_border_allow", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_abiotic_border_allow");BOOL_VALUE(0)
                return_sublayout=True,
                draw_condition=psy_active.s_distribution_method!="volume" and psy_active.is_using_surf,
                )
            if is_toggled:

                spaces = tocol.column(align=True)
                spaces.label(text=translate("Space")+":")
                spaces.prop(psy_active, "s_abiotic_border_space", text="",) #TODO implement for border

                tocol.separator(factor=0.9)

                #Threshold

                curprp = tocol.column(align=True)
                curprp.scale_y = 0.9
                curprp.label(text=translate("Range")+":")                
                curprp.prop(psy_active, "s_abiotic_border_max")
                curprp.prop(psy_active, "s_abiotic_border_treshold")

                tocol.separator(factor=0.9)

                #Remap Graph UI
                draw_transition_control_feature(layout=tocol, psy_active=psy_active, api="s_abiotic_border", fallnoisy=True,)

                tocol.separator(factor=0.3)

                #Feature Influence
                draw_feature_influence(layout=tocol, system=psy_active, api_name="s_abiotic_border",)

                tocol.separator(factor=0.5)

                #Universal Masking System
                draw_universal_masks(layout=tocol, mask_api=f"s_abiotic_border", psy_api=psy_active,)

            ui_templates.separator_box_in(box)
    return 


# ooooooooo.                                   o8o                     o8o      .
# `888   `Y88.                                 `"'                     `"'    .o8
#  888   .d88' oooo d8b  .ooooo.  oooo    ooo oooo  ooo. .oo.  .oo.   oooo  .o888oo oooo    ooo
#  888ooo88P'  `888""8P d88' `88b  `88b..8P'  `888  `888P"Y88bP"Y88b  `888    888    `88.  .8'
#  888          888     888   888    Y888'     888   888   888   888   888    888     `88..8'
#  888          888     888   888  .o8"'88b    888   888   888   888   888    888 .    `888'
# o888o        d888b    `Y8bod8P' o88'   888o o888o o888o o888o o888o o888o   "888"     .8'
#                                                                                   .o..P'
#                                                                                   `Y8P'

def draw_particle_proximity(self,layout):

    scat_scene, scat_ui, scat_win, emitter, psy_active, group_active = get_props()

    box, is_open = ui_templates.box_panel(layout, 
        panelopen_propname="ui_tweak_proxmity", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_tweak_proxmity");BOOL_VALUE(0)
        panel_icon="W_SNAP", 
        master_category_bool="s_proximity_master_allow",
        panel_name=translate("Proximity"),
        popover_info="SCATTER5_PT_docs",
        popover_gearwheel="SCATTER5_PT_per_settings_category_header",       
        popover_uilayout_context_set="s_proximity",
        is_tweaking_panel=True,
        )
    if is_open:

            if warnings(box):
                return None

            ui_is_active, ui_is_enabled = True, True
            ui_is_active = active_check(psy_active, s_category="s_proximity", prop=ui_is_active,)
            ui_is_enabled = lock_check(psy_active, s_category="s_proximity", prop=ui_is_enabled,)
            if (psy_active.is_linked): ui_is_enabled = False

            ########## ########## ProjBezArea Border
                            
            tocol, is_toggled = ui_templates.bool_toggle(box, psy_active, "s_proximity_projbezarea_border_allow",
                label=translate("Bezier-Area Border"), 
                icon="CURVE_BEZCIRCLE", 
                enabled=ui_is_enabled,
                active=ui_is_active,
                arrowopen_propname="ui_proximity_projbezarea_border_allow", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_proximity_projbezarea_border_allow");BOOL_VALUE(0)
                return_sublayout=True,
                draw_condition=psy_active.s_distribution_method=="projbezarea",
                )
            if is_toggled:

                #Threshold

                curprp = tocol.column(align=True)
                curprp.scale_y = 0.9
                curprp.label(text=translate("Distance")+":")                
                curprp.prop(psy_active, "s_proximity_projbezarea_border_max")
                curprp.prop(psy_active, "s_proximity_projbezarea_border_treshold")

                tocol.separator(factor=0.9)

                #Remap Graph UI
                draw_transition_control_feature(layout=tocol, psy_active=psy_active, api="s_proximity_projbezarea_border", fallnoisy=True,)

                tocol.separator(factor=0.3)

                #Feature Influence
                draw_feature_influence(layout=tocol, system=psy_active, api_name="s_proximity_projbezarea_border",)
                
                tocol.separator()
                
            ########## ########## Object-Repel 1&2
            
            for i in (1,2):

                tocol, is_toggled = ui_templates.bool_toggle(box, psy_active, f"s_proximity_repel{i}_allow",
                    label=translate("Object Repel")+f" {i}",
                    icon=f"W_SNAP{i}",
                    enabled=ui_is_enabled,
                    active=ui_is_active,
                    arrowopen_propname=f"ui_proximity_repel{i}_allow", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_proximity_repel1_allow");BOOL_VALUE(0)
                    return_sublayout=True,                            #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_proximity_repel2_allow");BOOL_VALUE(0)
                    )                                              
                if is_toggled:

                    #Target

                    proxprp = tocol.column(align=True)
                    proxprp.label(text=translate("Colliders")+":")
                    
                    coll_found,ptr_row = draw_coll_str_ptr(layout=proxprp, system=psy_active, api=f"s_proximity_repel{i}_coll_ptr", add_coll_name="Object-Repel",)
                    if (coll_found):

                        ptr_row_enum = ptr_row.row(align=True)
                        ptr_row_enum.scale_x = 0.9
                        ptr_row_enum.prop(psy_active, f"s_proximity_repel{i}_type", text="", icon_only=True,)

                    #Threshold

                    tocol.separator(factor=0.5)

                    proxprp = tocol.column(align=True)
                    proxprp.active = bool(coll_found)
                    proxprp.label(text=translate("Distance")+":")
                    proxprp.prop(psy_active, f"s_proximity_repel{i}_max")
                    proxprp.prop(psy_active, f"s_proximity_repel{i}_treshold")

                    tocol.separator(factor=1)

                    #Volume Consideration Option

                    tocol1, is_toggled = ui_templates.bool_toggle(tocol, psy_active, f"s_proximity_repel{i}_volume_allow",
                        label=translate("Consider Volume"), 
                        icon="SNAP_VOLUME", 
                        use_layout_left_spacer=False,
                        return_sublayout=True,
                        )
                    if is_toggled:

                        rowoo = tocol1.row(align=True)
                        rowoo.scale_y = 0.9
                        rowoo.prop(psy_active, f"s_proximity_repel{i}_volume_method", expand=True,)

                        tocol.separator(factor=0.4)

                    tocol.separator(factor=0.2)

                    tocol1, is_toggled = ui_templates.bool_toggle(tocol, psy_active, f"s_proximity_repel{i}_simulation_allow",
                        label=translate("Imprint Simulation"),
                        icon="PHYSICS",
                        use_layout_left_spacer=False,
                        return_sublayout=True,
                        )
                    if is_toggled:
                        
                        tocol2, is_toggled2 = ui_templates.bool_toggle(tocol1, psy_active, f"s_proximity_repel{i}_simulation_fadeaway_allow",
                            label=translate("Fade Away Effect"),
                            icon="SORTTIME",
                            use_layout_left_spacer=False,
                            return_sublayout=True,
                            )
                        if is_toggled2:
                            
                            methdd = getattr(psy_active,f"s_proximity_repel{i}_simulation_fadeaway_method")
                            coloo = tocol2.column(align=True)
                            rowoo = coloo.row(align=True)
                            rowoo.scale_y = 0.9
                            rowoo.prop(psy_active, f"s_proximity_repel{i}_simulation_fadeaway_method", expand=True,)
                            coloo.prop(psy_active, f"s_proximity_repel{i}_simulation_fadeaway_{methdd}")

                        tocol.separator(factor=0.4)

                    tocol.separator(factor=0.2)
                    
                    #Remap Graph UI
                    draw_transition_control_feature(layout=tocol, psy_active=psy_active, api=f"s_proximity_repel{i}", fallnoisy=True,)
                    
                    tocol.separator(factor=0.6)

                    #Feature Influence
                    draw_feature_influence(layout=tocol, system=psy_active, api_name=f"s_proximity_repel{i}",)

                    tocol.separator(factor=0.5)

                    #Universal Masking System
                    draw_universal_masks(layout=tocol, mask_api=f"s_proximity_repel{i}", psy_api=psy_active,)

                    tocol.separator()
            
            ########## ########## Outskirt 

            tocol, is_toggled = ui_templates.bool_toggle(box, psy_active, "s_proximity_outskirt_allow",
                label=translate("Outskirt"), 
                icon="W_PROXBOU",
                enabled=ui_is_enabled,
                active=ui_is_active,
                arrowopen_propname="ui_proximity_outskirt_allow", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_proximity_outskirt_allow");BOOL_VALUE(0)
                return_sublayout=True,
                draw_condition=psy_active.s_distribution_method not in ("projbezline","projempties"),
                )
            if is_toggled:

                #Detect

                prop = tocol.column(align=True)
                prop.label(text=translate("Edge Detection")+":")                
                prop.prop(psy_active, "s_proximity_outskirt_detection")
                prop.prop(psy_active, "s_proximity_outskirt_precision")

                tocol.separator(factor=0.3)

                #Threshold

                prop = tocol.column(align=True)
                prop.label(text=translate("Distance")+":")                
                prop.prop(psy_active, "s_proximity_outskirt_max")
                prop.prop(psy_active, "s_proximity_outskirt_treshold")

                tocol.separator(factor=0.7)

                #Remap Graph UI
                draw_transition_control_feature(layout=tocol, psy_active=psy_active, api="s_proximity_outskirt", fallnoisy=True,)

                tocol.separator(factor=0.3)

                #Feature Influence
                draw_feature_influence(layout=tocol, system=psy_active, api_name=f"s_proximity_outskirt",)

                tocol.separator(factor=0.5)

                #Universal Masking System
                draw_universal_masks(layout=tocol, mask_api=f"s_proximity_outskirt", psy_api=psy_active,)

            #TODO Bezier Paths??

            ui_templates.separator_box_in(box)
    return 


# oooooooooooo                                                       .
# `888'     `8                                                     .o8
#  888          .ooooo.   .ooooo.   .oooo.o oooo    ooo  .oooo.o .o888oo  .ooooo.  ooo. .oo.  .oo.
#  888oooo8    d88' `"Y8 d88' `88b d88(  "8  `88.  .8'  d88(  "8   888   d88' `88b `888P"Y88bP"Y88b
#  888    "    888       888   888 `"Y88b.    `88..8'   `"Y88b.    888   888ooo888  888   888   888
#  888       o 888   .o8 888   888 o.  )88b    `888'    o.  )88b   888 . 888    .o  888   888   888
# o888ooooood8 `Y8bod8P' `Y8bod8P' 8""888P'     .8'     8""888P'   "888" `Y8bod8P' o888o o888o o888o
#                                           .o..P'
#                                           `Y8P'

def is_valid_ecosystem_slot(p, i, api_start="", check_if_draw_props=False, check_if_draw_button=False,): 

    max_slot = getattr(p,f"{api_start}_ui_max_slot")

    slot1_full = getattr(p, f"{api_start}_01_ptr")!=""
    slot2_full = getattr(p, f"{api_start}_02_ptr")!=""
    slot3_full = getattr(p, f"{api_start}_03_ptr")!=""

    if (check_if_draw_props):
        match i:
            
            case 1:
                #always draw slot1
                return True
            case 2:
                #only draw slot2 if maxslot allow it or if ptr self or later are filled
                if (slot2_full or slot3_full):
                    #mandatory draw if slots behind are full
                    return True
                if (max_slot in (2,3)):
                    return True
                return False
            
            case 3:
                #only draw slot3 if maxslot allow it or if ptr self is filled
                if (slot3_full):
                    #mandatory draw if slots behind are full
                    return True
                if (max_slot==3):
                    return True
                return False

    if (check_if_draw_button):
        
        #dont draw button for last slot
        if (i==max_slot==3):
            return False
        
        #draw button for slot 2 only if no mandarory draw 
        if (i==max_slot==2): 
            if (slot3_full): 
                return False
            return True
        
        #draw button for slot 1 only if no mandarory draw 
        if (i==max_slot==1):
            if (slot2_full or slot3_full):
                return False
            return True

        return False

    return None


def draw_particle_ecosystem(self,layout):

    scat_scene, scat_ui, scat_win, emitter, psy_active, group_active = get_props()
    from ... __init__ import addon_prefs
    
    box, is_open = ui_templates.box_panel(layout, 
        panelopen_propname="ui_tweak_ecosystem", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_tweak_ecosystem");BOOL_VALUE(0)
        panel_icon="W_ECOSYSTEM", 
        master_category_bool="s_ecosystem_master_allow",
        panel_name=translate("Ecosystem"),
        popover_info="SCATTER5_PT_docs",
        popover_gearwheel="SCATTER5_PT_per_settings_category_header",       
        popover_uilayout_context_set="s_ecosystem",
        is_tweaking_panel=True,
        )
    if is_open:

            if warnings(box):
                return None

            ui_is_active, ui_is_enabled = True, True
            ui_is_active = active_check(psy_active, s_category="s_ecosystem", prop=ui_is_active,)
            ui_is_enabled = lock_check(psy_active, s_category="s_ecosystem", prop=ui_is_enabled,)
            if (psy_active.is_linked): ui_is_enabled = False

            ########## ########## Affinity

            tocol, is_toggled = ui_templates.bool_toggle(box, psy_active, "s_ecosystem_affinity_allow",
                label=translate("Affinity"),
                icon="W_AFFINITY",
                enabled=ui_is_enabled,
                active=ui_is_active,
                arrowopen_propname="ui_ecosystem_affinity_allow", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_ecosystem_affinity_allow");BOOL_VALUE(0)
                return_sublayout=True,
                )
            if is_toggled:
                
                spaces = tocol.column(align=True)
                spaces.label(text=translate("Space")+":")
                
                #spaces can only be global if multisurf chosen or if nosurf
                if (psy_active.s_surface_method=="collection" or not psy_active.is_using_surf):
                      spaces_dummy = spaces.row(align=True)
                      spaces_dummy.enabled = False
                      spaces_dummy.prop(scat_win, "dummy_global_only", text="",)
                else: spaces.prop(psy_active, "s_ecosystem_affinity_space", text="",)

                if addon_prefs().debug_interface:
                    tocol.prop(psy_active,"s_ecosystem_affinity_ui_max_slot",)
                    tocol.separator(factor=0.3)

                for i in (1,2,3):

                    if is_valid_ecosystem_slot(psy_active, i, api_start="s_ecosystem_affinity", check_if_draw_props=True,):

                        tocol.separator(factor=0.8)

                        api_str = f"s_ecosystem_affinity_{i:02}"

                        target_name = getattr(psy_active, f"{api_str}_ptr")
                        target_alert = ( bool(target_name) and (target_name not in psy_active.get_s_ecosystem_psy_match(bpy.context, target_name)) )
                        target_filled = ((not target_alert) and (target_name!=""))
                        
                        part_col = tocol.column(align=True)
                        ptr_col = part_col.column(align=True)
                        ptr_row = ptr_col.row(align=True)

                        if (target_filled):
                            psy_col = ptr_row.row(align=True)
                            psy_col.scale_x = 0.3
                            psy_col.prop(emitter.scatter5.particle_systems[target_name], "s_color", text="",)

                        ptr = ptr_row.row(align=True)
                        ptr.alert = target_alert
                        ptr.prop(psy_active, f"{api_str}_ptr", text="", icon="PARTICLES", placeholder=" "+translate("Scatter-System"),)

                        if (target_filled):
                            ptr_row_enum = ptr_row.row(align=True)
                            ptr_row_enum.scale_x = 0.9
                            ptr_row_enum.prop(psy_active, f"{api_str}_type", text="", icon_only=True,)
                            part_col.separator(factor=0.90)

                        part_props = part_col.column(align=True)
                        part_props.scale_y = 0.95
                        part_props.active = target_filled
                        part_props.label(text=translate("Distance")+":")
                        part_props.prop(psy_active, f"{api_str}_max_value",)
                        part_props.prop(psy_active, f"{api_str}_max_falloff",)
                        part_props.prop(psy_active, f"{api_str}_limit_distance",)

                        if is_valid_ecosystem_slot(psy_active, i, api_start="s_ecosystem_affinity", check_if_draw_button=True,):
                            part_col.separator(factor=1.6)
                            button = part_col.row()
                            button.scale_y = 0.9111
                            button.enabled = (getattr(psy_active,f"{api_str}_ptr")!="")
                            op = button.operator("scatter5.exec_line", text=translate("Add Slot"), icon="ADD",)
                            op.api = f"psy_active.s_ecosystem_affinity_ui_max_slot += 1"
                            op.description = translate("Take one more scatter system into consideration")

                        part_col.separator(factor=0.4)
                        continue

                tocol.separator(factor=1.0)

                #Remap Graph UI
                draw_transition_control_feature(layout=tocol, psy_active=psy_active, api="s_ecosystem_affinity", fallnoisy=True,)

                tocol.separator(factor=0.75)

                #Feature Influence 
                draw_feature_influence(layout=tocol, system=psy_active, api_name="s_ecosystem_affinity",)

                tocol.separator(factor=0.5)

                #Universal Masking System
                draw_universal_masks(layout=tocol, mask_api="s_ecosystem_affinity", psy_api=psy_active,)

                tocol.separator()

            ########## ########## Repulsion

            tocol, is_toggled = ui_templates.bool_toggle(box, psy_active, "s_ecosystem_repulsion_allow",
                label=translate("Repulsion"),
                icon="W_REPULSION",
                enabled=ui_is_enabled,
                active=ui_is_active,
                arrowopen_propname="ui_ecosystem_repulsion_allow", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_ecosystem_repulsion_allow");BOOL_VALUE(0)
                return_sublayout=True,
                )
            if is_toggled:
                
                spaces = tocol.column(align=True)
                spaces.label(text=translate("Space")+":")
                
                #spaces can only be global if multisurf chosen or if nosurf
                if (psy_active.s_surface_method=="collection" or not psy_active.is_using_surf):
                      spaces_dummy = spaces.row(align=True)
                      spaces_dummy.enabled = False
                      spaces_dummy.prop(scat_win, "dummy_global_only", text="",)
                else: spaces.prop(psy_active, "s_ecosystem_repulsion_space", text="",)

                if addon_prefs().debug_interface:
                    tocol.prop(psy_active,"s_ecosystem_repulsion_ui_max_slot",)
                    tocol.separator(factor=0.3)

                for i in (1,2,3):

                    if is_valid_ecosystem_slot(psy_active, i, api_start="s_ecosystem_repulsion", check_if_draw_props=True,):

                        tocol.separator(factor=0.8)

                        api_str = f"s_ecosystem_repulsion_{i:02}"

                        target_name = getattr(psy_active, f"{api_str}_ptr")
                        target_alert = ( bool(target_name) and (target_name not in psy_active.get_s_ecosystem_psy_match(bpy.context, target_name)) )
                        target_filled = ((not target_alert) and (target_name!=""))
                        
                        part_col = tocol.column(align=True)
                        ptr_col = part_col.column(align=True)
                        ptr_row = ptr_col.row(align=True)

                        if (target_filled):
                            psy_col = ptr_row.row(align=True)
                            psy_col.scale_x = 0.3
                            psy_col.prop(emitter.scatter5.particle_systems[target_name], "s_color", text="",)

                        ptr = ptr_row.row(align=True)
                        ptr.alert = target_alert
                        ptr.prop(psy_active, f"{api_str}_ptr", text="", icon="PARTICLES", placeholder=" "+translate("Scatter-System"),)

                        if (target_filled):
                            ptr_row_enum = ptr_row.row(align=True)
                            ptr_row_enum.scale_x = 0.9
                            ptr_row_enum.prop(psy_active, f"{api_str}_type", text="", icon_only=True,) 
                            part_col.separator(factor=0.90)

                        part_props = part_col.column(align=True)
                        part_props.scale_y = 0.95
                        part_props.active = target_filled
                        part_props.label(text=translate("Distance")+":")
                        part_props.prop(psy_active, f"{api_str}_max_value",)
                        part_props.prop(psy_active, f"{api_str}_max_falloff",)

                        if is_valid_ecosystem_slot(psy_active, i, api_start="s_ecosystem_repulsion", check_if_draw_button=True,):
                            part_col.separator(factor=1.6)
                            button = part_col.row()
                            button.scale_y = 0.9111
                            button.enabled = (getattr(psy_active,f"{api_str}_ptr")!="")
                            op = button.operator("scatter5.exec_line", text=translate("Add Slot"), icon="ADD",)
                            op.api = f"psy_active.s_ecosystem_repulsion_ui_max_slot += 1"
                            op.description = translate("Take one more scatter system into consideration")

                        part_col.separator(factor=0.4)
                        continue

                tocol.separator(factor=1.0)

                #Remap Graph UI
                draw_transition_control_feature(layout=tocol, psy_active=psy_active, api="s_ecosystem_repulsion", fallnoisy=True,)

                tocol.separator(factor=0.75)

                #Feature Influence 
                draw_feature_influence(layout=tocol, system=psy_active, api_name="s_ecosystem_repulsion",)

                tocol.separator(factor=0.5)

                #Universal Masking System
                draw_universal_masks(layout=tocol, mask_api="s_ecosystem_repulsion", psy_api=psy_active,)

                tocol.separator()

            ########## ########## Density

            tocol, is_toggled = ui_templates.bool_toggle(box, psy_active, "s_ecosystem_density_allow",
                label=translate("Density"),
                icon="OUTLINER_OB_POINTCLOUD",
                enabled=ui_is_enabled,
                active=ui_is_active,
                arrowopen_propname="ui_ecosystem_density_allow", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_ecosystem_density_allow");BOOL_VALUE(0)
                return_sublayout=True,
                )
            if is_toggled:
                
                spaces = tocol.column(align=True)
                spaces.label(text=translate("Space")+":")
                
                #spaces can only be global if surfs exists
                if (not psy_active.is_using_surf):
                      spaces_dummy = spaces.row(align=True)
                      spaces_dummy.enabled = False
                      spaces_dummy.prop(scat_win, "dummy_global_only", text="",)
                else: spaces.prop(psy_active, "s_ecosystem_density_space", text="",)
                
                tocol.separator(factor=0.3)

                if addon_prefs().debug_interface:
                    tocol.prop(psy_active,"s_ecosystem_density_ui_max_slot",)
                    tocol.separator(factor=0.3)
                                
                tocol.separator(factor=0.8)
                
                filled_once = False
                for i in (1,2,3):

                    if is_valid_ecosystem_slot(psy_active, i, api_start="s_ecosystem_density", check_if_draw_props=True,):
                        
                        api_str = f"s_ecosystem_density_{i:02}"

                        target_name = getattr(psy_active, f"{api_str}_ptr")
                        target_alert = ( bool(target_name) and (target_name not in psy_active.get_s_ecosystem_psy_match(bpy.context, target_name)) )
                        target_filled = ((not target_alert) and (target_name!=""))
                        
                        part_col = tocol.column(align=True)
                        ptr_col = part_col.column(align=True)
                        ptr_row = ptr_col.row(align=True)

                        if (target_filled):
                            filled_once = True
                            psy_col = ptr_row.row(align=True)
                            psy_col.scale_x = 0.3
                            psy_col.prop(emitter.scatter5.particle_systems[target_name], "s_color", text="",)

                        ptr = ptr_row.row(align=True)
                        ptr.alert = target_alert
                        ptr.prop(psy_active, f"{api_str}_ptr", text="", icon="PARTICLES", placeholder=" "+translate("Scatter-System"),)
                        
                        if is_valid_ecosystem_slot(psy_active, i, api_start="s_ecosystem_density", check_if_draw_button=True,):
                            part_col.separator(factor=1.0)
                            button = part_col.row()
                            button.scale_y = 0.9111
                            button.enabled = (getattr(psy_active,f"{api_str}_ptr")!="")
                            op = button.operator("scatter5.exec_line", text=translate("Add Slot"), icon="ADD",)
                            op.api = f"psy_active.s_ecosystem_density_ui_max_slot += 1"
                            op.description = translate("Take one more scatter system into consideration")

                        part_col.separator(factor=0.15)
                        continue
                    
                tocol.separator(factor=0.75)

                meth = tocol.column(align=True)
                meth.active = filled_once
                meth.label(text=translate("Method")+":")
                meth.prop(psy_active, "s_ecosystem_density_method", text="",)
                
                tocol.separator(factor=0.3)

                props = tocol.column(align=True)
                props.active = filled_once
                props.label(text=translate("Density")+":",)
                props.prop(psy_active,"s_ecosystem_density_voxelsize",)
                
                if (psy_active.s_ecosystem_density_method!="normalized"):
                    props.prop(psy_active,"s_ecosystem_density_min",)
                    props.prop(psy_active,"s_ecosystem_density_falloff",)

                tocol.separator(factor=1.0)

                #Remap Graph UI
                draw_transition_control_feature(layout=tocol, psy_active=psy_active, api="s_ecosystem_density", fallnoisy=True,)

                tocol.separator(factor=0.75)

                #Feature Influence 
                draw_feature_influence(layout=tocol, system=psy_active, api_name="s_ecosystem_density",)

                tocol.separator(factor=0.5)

                #Universal Masking System
                draw_universal_masks(layout=tocol, mask_api="s_ecosystem_density", psy_api=psy_active,)

                tocol.separator()
                
            ui_templates.separator_box_in(box)
    return 


#   .oooooo.    .o88o.  .o88o.                        .
#  d8P'  `Y8b   888 `"  888 `"                      .o8
# 888      888 o888oo  o888oo   .oooo.o  .ooooo.  .o888oo
# 888      888  888     888    d88(  "8 d88' `88b   888
# 888      888  888     888    `"Y88b.  888ooo888   888
# `88b    d88'  888     888    o.  )88b 888    .o   888 .
#  `Y8bood8P'  o888o   o888o   8""888P' `Y8bod8P'   "888"


def draw_particle_push(self,layout):

    scat_scene, scat_ui, scat_win, emitter, psy_active, group_active = get_props()

    box, is_open = ui_templates.box_panel(layout, 
        panelopen_propname="ui_tweak_push", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_tweak_push");BOOL_VALUE(0)
        panel_icon="CON_LOCLIKE", 
        master_category_bool="s_push_master_allow",
        panel_name=translate("Offset"),
        popover_info="SCATTER5_PT_docs",
        popover_gearwheel="SCATTER5_PT_per_settings_category_header",       
        popover_uilayout_context_set="s_push",
        is_tweaking_panel=True,
        )
    if is_open:

            if warnings(box):
                return None

            ui_is_active, ui_is_enabled = True, True
            ui_is_active = active_check(psy_active, s_category="s_push", prop=ui_is_active,)
            ui_is_enabled = lock_check(psy_active, s_category="s_push", prop=ui_is_enabled,)
            if (psy_active.is_linked): ui_is_enabled = False

            ########## ########## Push Offset 

            tocol, is_toggled = ui_templates.bool_toggle(box, psy_active, "s_push_offset_allow", 
                label=translate("Transforms"), 
                icon="CON_LOCLIKE", 
                enabled=ui_is_enabled,
                active=ui_is_active,
                arrowopen_propname="ui_push_offset_allow", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_push_offset_allow");BOOL_VALUE(0)
                return_sublayout=True,
                )
            if is_toggled:

                spaces = tocol.column(align=True)
                spaces.label(text=translate("Space")+":")
                    
                #space can only be global if using projempties with no projection enabled
                if (psy_active.s_distribution_method=="projempties" and not psy_active.is_using_surf): 
                        spaces_dummy = spaces.row(align=True)
                        spaces_dummy.enabled = False
                        spaces_dummy.prop(scat_win, "dummy_global_only", text="",)
                else: spaces.prop(psy_active, "s_push_offset_space", text="",)
                    
                tocol.separator(factor=0.5)

                vec = tocol.column()
                vec.label(text=translate("Offset/Random")+":")
                vecr = vec.row(align=True)
                veccol = vecr.column(align=True)
                veccol.scale_y = 0.9
                veccol.prop(psy_active,"s_push_offset_add_value", text="",)
                veccol = vecr.column(align=True)
                veccol.scale_y = 0.9
                veccol.prop(psy_active,"s_push_offset_add_random", text="",)

                vec = tocol.column()
                vec.label(text=translate("Rotate/Random")+":")
                vecr = vec.row(align=True)
                veccol = vecr.column(align=True)
                veccol.scale_y = 0.9
                veccol.prop(psy_active,"s_push_offset_rotate_value", text="",)
                veccol = vecr.column(align=True)
                veccol.scale_y = 0.9
                veccol.prop(psy_active,"s_push_offset_rotate_random", text="",)

                vec = tocol.column()
                vec.label(text=translate("Scale/Random")+":")
                vecr = vec.row(align=True)
                veccol = vecr.column(align=True)
                veccol.scale_y = 0.9
                veccol.prop(psy_active,"s_push_offset_scale_value", text="",)
                veccol = vecr.column(align=True)
                veccol.scale_y = 0.9
                veccol.prop(psy_active,"s_push_offset_scale_random", text="",)

                tocol.separator(factor=1.0)
                
                sed = tocol.row(align=True)
                sed.prop(psy_active, "s_push_offset_seed")
                sedbutton = sed.row(align=True)
                sedbutton.scale_x = 1.2
                sedbutton.prop(psy_active, "s_push_offset_is_random_seed", icon_value=cust_icon("W_DICE"), text="",)

                tocol.separator(factor=0.4)

                #Universal Masking System
                draw_universal_masks(layout=tocol, mask_api=f"s_push_offset", psy_api=psy_active,)

                tocol.separator()

            ########## ########## Push Direction

            tocol, is_toggled = ui_templates.bool_toggle(box, psy_active, "s_push_dir_allow", 
                label=translate("Push Along"),
                icon="SORT_DESC", 
                enabled=ui_is_enabled,
                active=ui_is_active,
                arrowopen_propname="ui_push_dir_allow", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_push_dir_allow");BOOL_VALUE(0)
                return_sublayout=True,
                )
            if is_toggled:
                
                spaces = tocol.column(align=True)
                spaces.label(text=translate("Space")+":")
                spaces.prop(psy_active, "s_push_dir_space", text="",)

                met = tocol.column(align=True)
                met.label(text=translate("Axis")+":")
                
                if (psy_active.s_distribution_method=="projbezarea" and not psy_active.is_using_surf):
                    met.prop(psy_active, "s_push_dir_method_projbezareanosurf_special", text="",)
                elif (psy_active.s_distribution_method=="projbezline" and not psy_active.is_using_surf):
                    met.prop(psy_active, "s_push_dir_method_projbezlinenosurf_special", text="",)
                elif (psy_active.s_distribution_method=="projempties" and not psy_active.is_using_surf):
                    met.prop(psy_active, "s_push_dir_method_projemptiesnosurf_special", text="",)
                else:
                    met.prop(psy_active, "s_push_dir_method", text="",)
                    
                met.separator()

                vec = tocol.column()
                vec.label(text=translate("Distance")+":")
                veccol = vec.column(align=True)
                veccol.scale_y = 0.9
                veccol.prop(psy_active,"s_push_dir_add_value",)
                veccol.prop(psy_active,"s_push_dir_add_random",)

                tocol.separator(factor=0.5)
                
                sed = tocol.row(align=True)
                sed.prop(psy_active, "s_push_dir_seed")
                sedbutton = sed.row(align=True)
                sedbutton.scale_x = 1.2
                sedbutton.prop(psy_active, "s_push_dir_is_random_seed", icon_value=cust_icon("W_DICE"), text="",)

                tocol.separator(factor=0.4)

                #Universal Masking System
                draw_universal_masks(layout=tocol, mask_api=f"s_push_dir", psy_api=psy_active,)

                tocol.separator()

            ########## ########## Push Noise

            tocol, is_toggled = ui_templates.bool_toggle(box, psy_active, "s_push_noise_allow", 
                label=translate("Random"),
                icon="W_DICE", 
                enabled=ui_is_enabled,
                active=ui_is_active,
                arrowopen_propname="ui_push_noise_allow", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_push_noise_allow");BOOL_VALUE(0)
                return_sublayout=True,
                )
            if is_toggled:
                
                spaces = tocol.column(align=True)
                spaces.label(text=translate("Space")+":")
                spaces.prop(psy_active, "s_push_noise_space", text="",)

                tocol.separator(factor=0.55)

                col = tocol.column()
                col.scale_y = 0.85
                col.prop(psy_active, "s_push_noise_vector")

                tocol.separator(factor=0.4)

                sed = tocol.row(align=True)
                sed.prop(psy_active, "s_push_noise_seed")
                sedbutton = sed.row(align=True)
                sedbutton.scale_x = 1.2
                sedbutton.prop(psy_active, "s_push_noise_is_random_seed", icon_value=cust_icon("W_DICE"), text="",)

                tocol.separator()

                tocol2, is_toggled2 = ui_templates.bool_toggle(tocol, psy_active, "s_push_noise_is_animated", 
                    label=translate("Noise Animation"),
                    icon="ONIONSKIN_ON", 
                    use_layout_left_spacer=False,
                    return_sublayout=True,
                    )
                if is_toggled2:
                    tocol2.prop(psy_active, "s_push_noise_speed")
                    tocol.separator(factor=0.2)
                
                tocol.separator(factor=0.1)

                #Universal Masking System
                draw_universal_masks(layout=tocol, mask_api=f"s_push_noise", psy_api=psy_active,)

                tocol.separator()

            ########## ########## Push Fall

            tocol, is_toggled = ui_templates.bool_toggle(box, psy_active, "s_push_fall_allow", 
                label=translate("Falling Animation"), 
                icon="FORCE_FORCE", 
                enabled=ui_is_enabled,
                active=ui_is_active,
                arrowopen_propname="ui_push_fall_allow", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_push_fall_allow");BOOL_VALUE(0)
                return_sublayout=True,
                )
            if is_toggled:

                spaces = tocol.column(align=True)
                spaces.label(text=translate("Space")+":")
                spaces.prop(psy_active, "s_push_fall_space", text="",)

                tocol.separator(factor=0.85)

                props =tocol.column(align=True)
                props.scale_y = 0.9
                props.label(text=translate("Keyframes")+":")
                props_pos = props.row(align=True)
                props_pos.prop(psy_active, "s_push_fall_key1_pos", text=translate("Frame"),)
                props_pos.prop(psy_active, "s_push_fall_key2_pos", text="",)
                props_hei = props.row(align=True)
                props_hei.prop(psy_active, "s_push_fall_key1_height", text=translate("Height"),)
                props_hei.prop(psy_active, "s_push_fall_key2_height", text="",)

                tocol.separator(factor=0.5)
                tocol.prop(psy_active, "s_push_fall_height")
                
                tocol.separator(factor=0.5)
                
                sed = tocol.row(align=True)
                sed.prop(psy_active, "s_push_fall_seed")
                sedbutton = sed.row(align=True)
                sedbutton.scale_x = 1.2
                sedbutton.prop(psy_active, "s_push_fall_is_random_seed", icon_value=cust_icon("W_DICE"), text="",)

                tocol.separator()

                ui_templates.bool_toggle(tocol, psy_active, "s_push_fall_stop_when_initial_z", 
                    label=translate("Rest at Initial Position"), 
                    icon="ANCHOR_BOTTOM",
                    use_layout_left_spacer=False,
                    )

                tocol.separator(factor=0.4)

                tocol2, is_toggled2 = ui_templates.bool_toggle(tocol, psy_active, "s_push_fall_turbulence_allow", 
                    label=translate("Turbulence"),
                    icon="FORCE_MAGNETIC", 
                    use_layout_left_spacer=False,
                    return_sublayout=True,
                    )
                if is_toggled2:
                        
                    vec = tocol2.column(align=True)
                    vec.scale_y = 0.85
                    vec.prop(psy_active, "s_push_fall_turbulence_spread")

                    tocol2.separator(factor=0.5)
                    tocol2.prop(psy_active, "s_push_fall_turbulence_speed")
                    tocol2.separator(factor=0.5)
                    
                    vec = tocol2.column(align=True)
                    vec.scale_y = 0.85
                    vec.active = (psy_active.s_push_fall_turbulence_rot_factor!=0)
                    vec.prop(psy_active, "s_push_fall_turbulence_rot_vector")

                    tocol2.separator(factor=0.5)
                    tocol2.prop(psy_active, "s_push_fall_turbulence_rot_factor", expand=False)

                tocol.separator(factor=0.1)

                #Universal Masking System
                draw_universal_masks(layout=tocol, mask_api=f"s_push_fall", psy_api=psy_active,)

            ui_templates.separator_box_in(box)
    return 


# oooooo   oooooo     oooo  o8o                    .o8
#  `888.    `888.     .8'   `"'                   "888
#   `888.   .8888.   .8'   oooo  ooo. .oo.    .oooo888
#    `888  .8'`888. .8'    `888  `888P"Y88b  d88' `888
#     `888.8'  `888.8'      888   888   888  888   888
#      `888'    `888'       888   888   888  888   888
#       `8'      `8'       o888o o888o o888o `Y8bod88P"


def draw_particle_wind(self,layout):

    scat_scene, scat_ui, scat_win, emitter, psy_active, group_active = get_props()

    box, is_open = ui_templates.box_panel(layout, 
        panelopen_propname="ui_tweak_wind", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_tweak_wind");BOOL_VALUE(0)
        panel_icon="FORCE_WIND",
        master_category_bool="s_wind_master_allow",
        panel_name=translate("Wind"),
        popover_info="SCATTER5_PT_docs",
        popover_gearwheel="SCATTER5_PT_per_settings_category_header",       
        popover_uilayout_context_set="s_wind",
        is_tweaking_panel=True,
        )
    if is_open:

            if warnings(box):
                return None

            ui_is_active, ui_is_enabled = True, True
            ui_is_active = active_check(psy_active, s_category="s_wind", prop=ui_is_active,)
            ui_is_enabled = lock_check(psy_active, s_category="s_wind", prop=ui_is_enabled,)
            if (psy_active.is_linked): ui_is_enabled = False

            ########## ########## Wind Wave

            tocol, is_toggled = ui_templates.bool_toggle(box, psy_active, "s_wind_wave_allow", 
                label=translate("Waves"), 
                icon="FORCE_WIND", 
                enabled=ui_is_enabled,
                active=ui_is_active,
                arrowopen_propname="ui_wind_wave_allow", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_wind_wave_allow");BOOL_VALUE(0)
                return_sublayout=True,
                )
            if is_toggled:

                spaces = tocol.column(align=True)
                spaces.label(text=translate("Space")+":")
                    
                #space can only be global if using projempties with no projection enabled
                if (psy_active.s_distribution_method=="projempties" and not psy_active.is_using_surf): 
                        spaces_dummy = spaces.row(align=True)
                        spaces_dummy.enabled = False
                        spaces_dummy.prop(scat_win, "dummy_global_only", text="",)
                else: spaces.prop(psy_active, "s_wind_wave_space", text="",)
                
                tocol.separator(factor=0.3)

                met = tocol.column(align=True)
                met.label(text=translate("Animation")+":")
                enum_row = met.row(align=True)
                enum_row.prop(psy_active,"s_wind_wave_method", text="",)

                tocol.separator(factor=0.3)

                if (psy_active.s_wind_wave_method=="wind_wave_loopable"):

                    tocol2, is_toggled2 = ui_templates.bool_toggle(tocol, psy_active, "s_wind_wave_loopable_cliplength_allow", 
                        label=translate("Define Loop"), 
                        icon="FILE_MOVIE", 
                        use_layout_left_spacer=False,
                        return_sublayout=True,
                        )
                    if is_toggled2:
                            
                        min_api = "s_wind_wave_loopable_frame_start" if (psy_active.s_wind_wave_loopable_frame_start<=psy_active.s_wind_wave_loopable_frame_end) else "s_wind_wave_loopable_frame_end"
                        max_api = "s_wind_wave_loopable_frame_end" if (min_api=="s_wind_wave_loopable_frame_start") else "s_wind_wave_loopable_frame_start"
                        
                        prop = tocol2.column(align=True)
                        prop.scale_y = 0.9
                        prop.prop(psy_active, min_api,text=translate("Start"),)
                        prop.prop(psy_active, max_api,text=translate("End"),)

                        tocol2.separator(factor=0.2)
                
                tocol.separator(factor=0.5)

                col = tocol.column(align=True)
                col.scale_y = 0.9
                col.label(text=translate("Wind Intensity")+":")
                col.prop(psy_active, "s_wind_wave_speed")
                col.prop(psy_active, "s_wind_wave_force")
                
                tocol.separator(factor=0.65)

                tocol2, is_toggled2 = ui_templates.bool_toggle(tocol, psy_active, "s_wind_wave_scale_influence", 
                    label=translate("Scale Influence"), 
                    icon="CON_SAMEVOL",
                    use_layout_left_spacer=False,
                    return_sublayout=True,
                    )
                if is_toggled2:
                    tocol2.prop(psy_active,"s_wind_wave_scale_influence_factor", slider=False,)
                    tocol2.separator(factor=0.2)
                
                tocol.separator(factor=0.5)

                col = tocol.column(align=True)
                col.scale_y = 0.9
                col.label(text=translate("Wind Texture")+":")
                col.prop(psy_active, "s_wind_wave_texture_scale")
                col.prop(psy_active, "s_wind_wave_texture_turbulence")
                col.prop(psy_active, "s_wind_wave_texture_distorsion")
                col.prop(psy_active, "s_wind_wave_texture_brightness")
                col.prop(psy_active, "s_wind_wave_texture_contrast")
                col.separator()

                meth = tocol.column(align=True)
                meth.label(text=translate("Wind Orientation")+":")
                
                meth.prop(psy_active,"s_wind_wave_dir_method", text="",)

                tocol.separator(factor=0.3)
                
                if (psy_active.s_wind_wave_dir_method=="vcol"):
                    mask = tocol.row(align=True)

                    ptr = mask.row(align=True)
                    ptr_filled = bool(psy_active.s_wind_wave_flowmap_ptr)
                    ptr_acrossall = is_attr_surfs_shared(system=psy_active, attr_type='vcol', attr_name=psy_active.s_wind_wave_flowmap_ptr,)
                    ptr.alert = (ptr_filled and not ptr_acrossall) or (ptr_filled and not psy_active.is_using_surf)
                    ptr.prop(psy_active, "s_wind_wave_flowmap_ptr", text="", icon="GROUP_VCOL", placeholder=" "+translate("Color Attribute"),)
                    
                    op = mask.operator("scatter5.vg_quick_paint",
                        text="",
                        icon="VPAINT_HLT" if psy_active.s_wind_wave_flowmap_ptr else "ADD",
                        depress=((bpy.context.mode=="PAINT_VERTEX") and (getattr(bpy.context.object.data.color_attributes.active_color,"name",'')==psy_active.s_wind_wave_flowmap_ptr)),
                        )
                    op.group_name = psy_active.s_wind_wave_flowmap_ptr
                    op.mode = "vcol" 
                    op.api = f"emitter.scatter5.particle_systems['{psy_active.name}'].s_wind_wave_flowmap_ptr"

                    moreinfo = mask.row()
                    moreinfo.separator(factor=0.1)
                    moreinfo.emboss = "NONE"
                    moreinfo.context_string_set("pass_ui_arg_popover","get_flowmap")
                    moreinfo.popover(panel="SCATTER5_PT_docs", text="", icon="INFO",)

                    tocol.separator(factor=0.3)
                    tocol.prop(psy_active, "s_wind_wave_direction")
                    
                else:
                    dirs = tocol.column(align=True)
                    dirs.prop(psy_active, "s_wind_wave_direction")
                    dirs.prop(psy_active, "s_wind_wave_direction_random")
                
                tocol.separator(factor=0.5)

                tocol2, is_toggled2 = ui_templates.bool_toggle(tocol, psy_active, "s_wind_wave_swinging", 
                    label=translate("Bilateral Swing"), 
                    icon="W_ARROW_SWINGY",
                    use_layout_left_spacer=False,
                    return_sublayout=True,
                    )
                if is_toggled2:
                    tocol2.prop(psy_active,"s_wind_wave_swinging_factor", slider=False,)
                    tocol2.separator(factor=0.2)
                    
                tocol.separator(factor=0.1)
                
                #Universal Masking System
                draw_universal_masks(layout=tocol, mask_api=f"s_wind_wave", psy_api=psy_active,)

                tocol.separator(factor=0.8)

            ########## ########## Wind noise 

            tocol, is_toggled = ui_templates.bool_toggle(box, psy_active, "s_wind_noise_allow", 
                label=translate("Turbulence"), 
                icon="FORCE_TURBULENCE", 
                enabled=ui_is_enabled,
                active=ui_is_active,
                arrowopen_propname="ui_wind_noise_allow", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_wind_noise_allow");BOOL_VALUE(0)
                return_sublayout=True,
                )
            if is_toggled:

                spaces = tocol.column(align=True)
                spaces.label(text=translate("Space")+":")
                    
                #space can only be global if using projempties with no projection enabled
                if (psy_active.s_distribution_method=="projempties" and not psy_active.is_using_surf): 
                        spaces_dummy = spaces.row(align=True)
                        spaces_dummy.enabled = False
                        spaces_dummy.prop(scat_win, "dummy_global_only", text="",)
                else: spaces.prop(psy_active, "s_wind_noise_space", text="",)
                
                tocol.separator(factor=0.3)

                met = tocol.column(align=True)
                met.label(text=translate("Animation")+":")
                enum_row = met.row(align=True)
                enum_row.prop(psy_active,"s_wind_noise_method", text="",)

                if (psy_active.s_wind_noise_method=="wind_noise_loopable"):

                    met.separator()

                    tocol2, is_toggled2 = ui_templates.bool_toggle(met, psy_active, "s_wind_noise_loopable_cliplength_allow", 
                        label=translate("Define Loop"), 
                        icon="FILE_MOVIE", 
                        use_layout_left_spacer=False,
                        return_sublayout=True,
                        )
                    if is_toggled2:
                            
                        min_api = "s_wind_noise_loopable_frame_start" if (psy_active.s_wind_noise_loopable_frame_start<=psy_active.s_wind_noise_loopable_frame_end) else "s_wind_noise_loopable_frame_end"
                        max_api = "s_wind_noise_loopable_frame_end" if (min_api=="s_wind_noise_loopable_frame_start") else "s_wind_noise_loopable_frame_start"
                        
                        prop = tocol2.column(align=True)
                        prop.scale_y = 0.9
                        prop.prop(psy_active, min_api, text=translate("Start"),)
                        prop.prop(psy_active, max_api, text=translate("End"),)

                        tocol2.separator(factor=0.2)

                met.separator()

                col = tocol.column(align=True)
                col.scale_y = 0.9
                col.label(text=translate("Strength")+":")
                col.prop(psy_active, "s_wind_noise_force")
                col.prop(psy_active, "s_wind_noise_speed")

                tocol.separator(factor=0.7)
                
                #Universal Masking System
                draw_universal_masks(layout=tocol, mask_api=f"s_wind_noise", psy_api=psy_active,)

            ui_templates.separator_box_in(box)

    return 


# oooooo     oooo  o8o            o8o   .o8        o8o  oooo   o8o      .
#  `888.     .8'   `"'            `"'  "888        `"'  `888   `"'    .o8
#   `888.   .8'   oooo   .oooo.o oooo   888oooo.  oooo   888  oooo  .o888oo oooo    ooo
#    `888. .8'    `888  d88(  "8 `888   d88' `88b `888   888  `888    888    `88.  .8'
#     `888.8'      888  `"Y88b.   888   888   888  888   888   888    888     `88..8'
#      `888'       888  o.  )88b  888   888   888  888   888   888    888 .    `888'
#       `8'       o888o 8""888P' o888o  `Y8bod8P' o888o o888o o888o   "888"     .8'
#                                                                           .o..P'
#                                                                           `Y8P'

def draw_particle_visibility(self,layout):
    
    scat_scene, scat_ui, scat_win, emitter, psy_active, group_active = get_props()

    box, is_open = ui_templates.box_panel(layout, 
        panelopen_propname="ui_tweak_visibility", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_tweak_visibility");BOOL_VALUE(0)
        panel_icon="HIDE_OFF", 
        master_category_bool="s_visibility_master_allow",
        panel_name=translate("Visibility"),
        popover_info="SCATTER5_PT_docs", 
        popover_gearwheel="SCATTER5_PT_per_settings_category_header",       
        popover_uilayout_context_set="s_visibility",
        is_tweaking_panel=True,
        )
    if is_open:

            if warnings(box):
                return None

            ui_is_active, ui_is_enabled = True, True
            ui_is_active = active_check(psy_active, s_category="s_visibility", prop=ui_is_active,)
            ui_is_enabled = lock_check(psy_active, s_category="s_visibility", prop=ui_is_enabled,)
            if (psy_active.is_linked): ui_is_enabled = False

            ########## ########## Scatter Count Information

            tocol, is_toggled = ui_templates.bool_toggle(box, psy_active, "s_visibility_statistics_allow", 
                label=translate("Statistics"), 
                icon="SORTSIZE", 
                enabled=ui_is_enabled,
                active=ui_is_active,
                arrowopen_propname="ui_visibility_statistics_allow", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_visibility_statistics_allow");BOOL_VALUE(1)
                return_sublayout=True,
                )
            if is_toggled:

                #Viewport Count 

                info_box = tocol.box().row()
                info_box.scale_y = 0.6
                info_box_lbl = info_box.row()
                info_box_lbl.label(text=count_repr(psy_active.scatter_count_viewport, unit=translate("Instances")), icon="RESTRICT_VIEW_OFF",)
                info_box_refr = info_box.row()
                op = info_box_refr.operator("scatter5.exec_line", text="", icon="FILE_REFRESH", emboss=False,)
                op.api = f"psy_active.get_scatter_count(state='viewport',)"
                op.description = translate("Calculate instance count on viewport")

                #Final Render Count

                info_box = tocol.box().row()
                info_box.scale_y = 0.6
                info_box_lbl = info_box.row()
                info_box_lbl.label(text=count_repr(psy_active.scatter_count_render, unit=translate("Instances")), icon="RESTRICT_RENDER_OFF",)
                info_box_refr = info_box.row()
                op = info_box_refr.operator("scatter5.exec_line", text="", icon="FILE_REFRESH", emboss=False,)
                op.api = f"psy_active.get_scatter_count(state='render',)"
                op.description = translate("Calculate instance count on render")

                tocol.separator(factor=1)

            ########## ########## Percentage

            tocol, tits, is_toggled = ui_templates.bool_toggle(box, psy_active, "s_visibility_view_allow", 
                label=translate("Reduce Density"), 
                icon="W_PERCENTAGE", 
                enabled=ui_is_enabled,
                active=ui_is_active,
                arrowopen_propname="ui_visibility_view_allow", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_visibility_view_allow");BOOL_VALUE(0)
                return_sublayout=True,
                return_rowlayout=True,
                )
            draw_visibility_methods(psy_active, tits, "s_visibility_view")
            if is_toggled:

                subcol = tocol.column(align=True)
                subcol.scale_y = 0.95
                subcol.label(text=translate("Removal")+":")
                subcol.prop(psy_active,"s_visibility_view_percentage",)
    
                tocol.separator(factor=1.5)

            ########## ########## Maximum load

            tocol, tits, is_toggled = ui_templates.bool_toggle(box, psy_active, "s_visibility_maxload_allow", 
                label=translate("Max Amount"), 
                icon="W_SHOW_VIS_MAXLOAD_ON", 
                enabled=ui_is_enabled,
                active=ui_is_active,
                arrowopen_propname="ui_visibility_maxload_allow", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_visibility_maxload_allow");BOOL_VALUE(0)
                return_sublayout=True,
                return_rowlayout=True,
                )
            draw_visibility_methods(psy_active, tits, "s_visibility_maxload")
            if is_toggled:

                #Maxload Feature

                subcol = tocol.column(align=True)
                subcol.label(text=translate("Limit Method")+":")
                enum = subcol.row(align=True) 
                enum.prop(psy_active, "s_visibility_maxload_cull_method", expand=True,)
                subcol.prop(psy_active, "s_visibility_maxload_treshold")

                tocol.separator(factor=1.5)

            ########## ########## Face Preview 

            tocol, tits, is_toggled = ui_templates.bool_toggle(box, psy_active, "s_visibility_facepreview_allow", 
                label=translate("Preview Area"), 
                icon="W_SHOW_VIS_VIEW_ON", 
                enabled=ui_is_enabled,
                active=ui_is_active,
                arrowopen_propname="ui_visibility_facepreview_allow", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_visibility_facepreview_allow");BOOL_VALUE(0)
                return_sublayout=True,
                return_rowlayout=True,
                draw_condition=psy_active.s_distribution_method!="volume" and psy_active.is_using_surf,
                )
            draw_visibility_methods(psy_active, tits, "s_visibility_facepreview")
            if is_toggled:

                subcol = tocol.column(align=True)
                subcol.scale_y = 0.95
                subcol.label(text=translate("Selection")+":")
                opsurfs = psy_active.get_surfaces()
                opsurfsnames = "_!#!_".join(s.name for s in opsurfs)
                subcol.operator("scatter5.facesel_to_vcol", text=translate("Define Area"), icon="RESTRICT_SELECT_OFF",).surfaces_names = opsurfsnames
                subcol.operator("scatter5.facesel_to_vcol", text=f"{sum(s.scatter5.s_visibility_facepreview_area for s in opsurfs):0.2f} m² "+translate("used"),).surfaces_names = opsurfsnames
                
                tocol.separator(factor=1.5)

            ########## Camera Optimization

            tocol, tits, is_toggled = ui_templates.bool_toggle(box, psy_active, "s_visibility_cam_allow", 
                label=translate("Cam Optimization"), 
                icon="OUTLINER_OB_CAMERA", 
                enabled=ui_is_enabled,
                active=ui_is_active,
                arrowopen_propname="ui_visibility_cam_allow", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_visibility_cam_allow");BOOL_VALUE(0)
                return_sublayout=True,
                return_rowlayout=True,
                )
            draw_visibility_methods(psy_active, tits, "s_visibility_cam")
            if is_toggled:

                if (bpy.context.scene.camera is None):

                    tocol.separator(factor=0.3)
                    moreinfo = tocol.row()
                    moreinfo.emboss = "NONE"
                    moreinfo.context_string_set("pass_ui_arg_popover","nocamera_info")
                    moreinfo.popover(panel="SCATTER5_PT_docs", text=translate("No Camera Found"), icon="INFO",)
                    tocol.separator(factor=0.9)

                else: 
                    
                    tocol.separator(factor=0.1)
                    
                    ui_templates.bool_toggle(tocol, psy_active, "s_visibility_cam_predist_allow", 
                        label=translate("Efficient Distribution"),
                        icon="TIME",
                        active=(psy_active.s_distribution_method in ("random","clumping","verts","faces","edges","random_stable",)),
                        use_layout_left_spacer=False,
                        return_sublayout=False,
                        )
                    
                    tocol.separator(factor=0.2)

                    ### Frustum Culling 

                    tocol2, is_toggled2 = ui_templates.bool_toggle(tocol, psy_active, "s_visibility_camclip_allow", 
                        label=translate("Frustum Culling"),
                        icon="CAMERA_DATA",
                        use_layout_left_spacer=False,
                        return_sublayout=True,
                        )
                    if is_toggled2:

                        tocol2.separator(factor=0.1)

                        tocol3, is_toggled3 = ui_templates.bool_toggle(tocol2, psy_active, "s_visibility_camclip_proximity_allow", 
                            label=translate("Proximity Radius"),
                            icon="PROP_ON",
                            use_layout_left_spacer=False,
                            return_sublayout=True,
                            )
                        if is_toggled3:

                            prop = tocol3.column(align=True)
                            prop.scale_y = 0.9
                            prop.prop(psy_active, "s_visibility_camclip_proximity_distance")

                            tocol2.separator(factor=0.3)

                        #per cam data

                        tocol2.separator(factor=0.35)

                        _, is_toggled3 = ui_templates.bool_toggle(tocol2, psy_active, "s_visibility_camclip_cam_autofill", 
                            label=translate("Per Cam Settings"),
                            icon="CON_CAMERASOLVER", 
                            use_layout_left_spacer=False,
                            return_sublayout=False,
                            )
                        if is_toggled3:

                            tocol2.separator(factor=0.25)

                            prop = tocol2.column(align=True)
                            prop.enabled = False
                            prop.prop(bpy.context.scene, "camera", text=translate("Active"))

                        tocol2.separator(factor=0.25)

                        if (psy_active.s_visibility_camclip_cam_autofill):
                            prop = tocol2.column(align=True)
                            prop.enabled = False
                            prop.scale_y = 0.85
                            prop.label(text=translate("Resolution")+":")
                            propp = prop.column(align=True)
                            propp.scale_y = 0.85
                            propp.prop(bpy.context.scene.render, "resolution_x", text="X",)
                            propp.prop(bpy.context.scene.render, "resolution_y", text="Y",)
                        else: 
                            prop = tocol2.column(align=True)
                            prop.scale_y = 0.75
                            prop.prop(psy_active, "s_visibility_camclip_cam_res_xy")

                        if (psy_active.s_visibility_camclip_cam_autofill):
                            prop = tocol2.column(align=True)
                            prop.enabled = False
                            prop.scale_y = 0.85
                            prop.label(text=translate("Shift")+":")
                            propp = prop.column(align=True)
                            propp.scale_y = 0.85
                            propp.prop(bpy.context.scene.camera.data, "shift_x", text="X",)
                            propp.prop(bpy.context.scene.camera.data, "shift_y", text="Y",)
                        else: 
                            prop = tocol2.column(align=True)
                            prop.scale_y = 0.75
                            prop.prop(psy_active, "s_visibility_camclip_cam_shift_xy")

                        if (psy_active.s_visibility_camclip_cam_autofill):
                            prop = tocol2.column(align=True)
                            prop.enabled = False
                            prop.scale_y = 0.85
                            prop.label(text=translate("Lenses")+":",)
                            propp = prop.column(align=True)
                            propp.scale_y = 0.85
                            propp.prop(bpy.context.scene.camera.data, "lens", text=translate("Lens"),)
                            propp.prop(bpy.context.scene.camera.data, "sensor_width", text=translate("Sensor"),)
                        else: 
                            prop = tocol2.column(align=True)
                            prop.scale_y = 0.85
                            prop.label(text=translate("Lenses")+":",)
                            propp = prop.column(align=True)
                            propp.scale_y = 0.85
                            propp.prop(psy_active, "s_visibility_camclip_cam_lens",)
                            propp.prop(psy_active, "s_visibility_camclip_cam_sensor_width",)

                        tocol2.separator(factor=0.1)

                        if (psy_active.s_visibility_camclip_cam_autofill):
                            prop = tocol2.column(align=True)
                            prop.scale_y = 0.75
                            prop.prop(bpy.context.scene.camera.scatter5, "s_visibility_camclip_per_cam_boost_xy",)
                        else:
                            prop = tocol2.column(align=True)
                            prop.scale_y = 0.75
                            prop.prop(psy_active, "s_visibility_camclip_cam_boost_xy",)

                        tocol2.separator(factor=0.2)

                    ### Distance Culling 

                    tocol.separator(factor=0.2)

                    tocol2, is_toggled2 = ui_templates.bool_toggle(tocol, psy_active, "s_visibility_camdist_allow", 
                        label=translate("Distance Culling"), 
                        icon="MOD_WAVE", 
                        use_layout_left_spacer=False,
                        return_sublayout=True,
                        )
                    if is_toggled2:

                        #per cam data
                        tocol2.separator(factor=0.1)
                        
                        _, is_toggled3 = ui_templates.bool_toggle(tocol2, psy_active, "s_visibility_camdist_per_cam_data", 
                            label=translate("Per Cam Settings"),
                            icon="CON_CAMERASOLVER", 
                            use_layout_left_spacer=False,
                            return_sublayout=False,
                            )
                        if is_toggled3:

                            tocol2.separator(factor=0.25)

                            prop = tocol2.column(align=True)
                            prop.enabled = False
                            prop.prop(bpy.context.scene, "camera", text=translate("Active"),)

                        tocol2.separator(factor=0.25)

                        if (psy_active.s_visibility_camdist_per_cam_data):
                              opdata,opstr = bpy.context.scene.camera.scatter5,"s_visibility_camdist_per_cam_" #min/max
                        else: opdata,opstr = psy_active,"s_visibility_camdist_" #min/max
                            
                        prop = tocol2.column(align=True)
                        prop.scale_y = 0.9
                        prop.label(text=translate("Transition")+":",)
                        
                        camdistrow = prop.row(align=True)
                        camdistrow.prop(opdata, opstr+"min",)
                        op = camdistrow.operator("scatter5.modal_measure_distance", text="", icon="EYEDROPPER",)
                        op.mode = "CameraDistance"; op.apply_sett_psyname = psy_active.name; op.apply_sett_propname = opstr+"min"; op.camera_location = bpy.context.scene.camera.location
                        #
                        camdistrow = prop.row(align=True)
                        camdistrow.prop(opdata, opstr+"max",)
                        op = camdistrow.operator("scatter5.modal_measure_distance", text="", icon="EYEDROPPER",)
                        op.mode = "CameraDistance"; op.apply_sett_psyname = psy_active.name; op.apply_sett_propname = opstr+"max"; op.camera_location = bpy.context.scene.camera.location

                        tocol2.separator(factor=0.45)          
                        
                        #Remap Graph UI 
                        draw_transition_control_feature(layout=tocol2, psy_active=psy_active, api="s_visibility_camdist", fallnoisy=False,)
                        
                        tocol2.separator(factor=0.2)

                    ### Frustrum Culling 

                    tocol.separator(factor=0.2)

                    tocol2, is_toggled2 = ui_templates.bool_toggle(tocol, psy_active, "s_visibility_camoccl_allow", 
                        label=translate("Occlusion Culling"), 
                        icon="GHOST_ENABLED",
                        use_layout_left_spacer=False,
                        return_sublayout=True,
                        )
                    if is_toggled2:

                        met = tocol2.column(align=True)
                        met.label(text=translate("Method")+":")
                        met.prop(psy_active, "s_visibility_camoccl_method", text="",)

                        tocol2.separator(factor=0.35)

                        if (psy_active.s_visibility_camoccl_method!="surface_only"):

                            prop = tocol2.column(align=True)
                            prop.label(text=translate("Colliders")+":")

                            draw_coll_str_ptr(layout=prop, system=psy_active, api="s_visibility_camoccl_coll_ptr", add_coll_name="OcclusionColl",)

                            tocol2.separator(factor=0.5)

                        #TODO, need ot make this threshold a bit better.. need blur node i believe

                        #tocol2.separator(factor=0.35)

                        #prop = tocol2.column(align=True)
                        #prop.prop(psy_active, "s_visibility_camoccl_threshold")

                    #Camera Update Method

                    tocol.separator(factor=0.5)

                    draw_camera_update_method(layout=tocol, psy_active=psy_active)

                    tocol.separator(factor=0.5)

            ui_templates.separator_box_in(box)
    return 


# ooooo                          .
# `888'                        .o8
#  888  ooo. .oo.    .oooo.o .o888oo  .oooo.   ooo. .oo.    .ooooo.   .ooooo.   .oooo.o
#  888  `888P"Y88b  d88(  "8   888   `P  )88b  `888P"Y88b  d88' `"Y8 d88' `88b d88(  "8
#  888   888   888  `"Y88b.    888    .oP"888   888   888  888       888ooo888 `"Y88b.
#  888   888   888  o.  )88b   888 . d8(  888   888   888  888   .o8 888    .o o.  )88b
# o888o o888o o888o 8""888P'   "888" `Y888""8o o888o o888o `Y8bod8P' `Y8bod8P' 8""888P'


class SCATTER5_UL_list_instances(bpy.types.UIList):
    """instance area"""

    def __init__(self, *args, **kwargs):
        """set default drawing UIList options"""
        
        super().__init__(*args, **kwargs)
        
        self.use_filter_sort_alpha = True
        self.use_filter_show = False
        
        return None
        
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        
        if not item:
            return 

        scat_scene, scat_ui, scat_win, emitter, psy_active, group_active = get_props()
        coll = psy_active.s_instances_coll_ptr

        #find index 

        i = None
        for i,o in enumerate(sorted(coll.objects, key= lambda o:o.name)):
            i+=1
            if o==item:
                break

        row = layout.row(align=True)
        row.scale_y = 0.7

        #select operator 

        selct = row.row()

        if (bpy.context.mode=="OBJECT"):

            selct.active = (item==bpy.context.object)
            op = selct.operator("scatter5.select_object",emboss=False, text="", icon="RESTRICT_SELECT_OFF" if item in bpy.context.selected_objects else "RESTRICT_SELECT_ON")
            op.obj_session_uid = item.session_uid
            op.coll_name = coll.name

        #name? or linked label?
        
        if bool(item.library):
            lnk = row.row()
            lnk.label(text=item.name, icon="LINKED",)
        else:
            name = row.row()
            name.prop(item,"name", text="", emboss=False, )

        #pick method chosen? 

        if (psy_active.s_instances_pick_method != "pick_random"):

            #pick rate slider 

            if (psy_active.s_instances_pick_method == "pick_rate"):

                slider = row.row()

                if (i<=20):
                    slider.prop(psy_active, f"s_instances_id_{i:02}_rate", text="",)
                else:
                    slider.alignment = "RIGHT"
                    slider.label(text=translate("Not Supported"),)

            #pick index 

            elif (psy_active.s_instances_pick_method == "pick_idx"):

                slider = row.row()
                slider.alignment= "RIGHT"
                slider.label(text=f"{i-1:02} ")

            #pick scale 

            elif (psy_active.s_instances_pick_method == "pick_scale"):

                slider = row.row(align=True)

                if (i<=20):
                    slider.scale_x = 0.71
                    slider.prop(psy_active, f"s_instances_id_{i:02}_scale_min", text="",)
                    slider.prop(psy_active, f"s_instances_id_{i:02}_scale_max", text="",)
                else:
                    slider.operator("scatter5.dummy",text=translate("Not Supported"),)

            #pick color 

            elif (psy_active.s_instances_pick_method == "pick_color"):

                clr = row.row(align=True)
                clr.alignment = "RIGHT"

                if (i<=20):
                      clr.prop(psy_active, f"s_instances_id_{i:02}_color", text="",)
                else: clr.label(text=translate("Not Supported"),)

        #remove operator 

        ope = row.row(align=False)
        ope.scale_x = 0.9
        ope.operator("scatter5.remove_instances",emboss=False, text="", icon="TRASH",).obj_session_uid = item.session_uid

        return


def draw_particle_instances(self,layout):

    scat_scene, scat_ui, scat_win, emitter, psy_active, group_active = get_props()
    ins_len = 0 if (psy_active is None) else len(psy_active.get_instance_objs())

    extra_layout, box, is_open = ui_templates.box_panel(layout, 
        panelopen_propname="ui_tweak_instances", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_tweak_instances");BOOL_VALUE(0)
        panel_icon="W_INSTANCE",
        panel_name=translate("Instances") if (psy_active is None) else translate("Instances")+f" [{ins_len}]" if (psy_active.s_instances_method=="ins_collection") else translate("Instances"),
        popover_info="SCATTER5_PT_docs", 
        popover_gearwheel="SCATTER5_PT_per_settings_category_header",       
        popover_uilayout_context_set="s_instances",
        is_tweaking_panel=True,
        return_subpanel=True,
        )
    if is_open:

            if warnings(box):
                return None

            ui_is_active, ui_is_enabled = True, True
            ui_is_enabled = lock_check(psy_active, s_category="s_instances", prop=ui_is_enabled,)
            if (psy_active.is_linked): ui_is_enabled = False

            main = box.column()
            main.active = ui_is_active
            main.enabled = ui_is_enabled

            ########## ########## Drawing Instancing

            mainr = main.row()
            mainr1 = mainr.row()
            mainr1.separator(factor=0.8) 
            mainr2 = mainr.row()

            col = mainr2.column(align=True)
                
            #agencing two labels spaces correctly with c1 & c2 

            twor = col.row()
            c1 = twor.column()
            c1.scale_x = 0.55
            c2 = twor.column()

            #instancing method? 

            c1.label(text=translate("Method")+":",)
            c2.prop(psy_active, "s_instances_method", text="",)
            
            #collection method?

            if (psy_active.s_instances_method=="ins_collection"): 
                                
                c1.separator(factor=0.55) ; c2.separator(factor=0.55)     
                
                #collection pointer 
                
                c1.label(text="")
                cproprow = c2.row(align=True)
                cproprow.prop(psy_active, "s_instances_coll_ptr", text="",)
                
                #show collection add button if no collection chosen yet 
                
                coll_ptr = psy_active.s_instances_coll_ptr
                if (coll_ptr is None):

                    op = cproprow.operator("scatter5.create_coll", text="", icon="ADD",)
                    op.api = "psy_active.s_instances_coll_ptr"
                    op.pointer_type = "data"
                    op.coll_name = "Instancing Objects"
                    
                    col.separator()

                    return None
                                    
                #spawning method 
                
                c1.separator(factor=0.55) ; c2.separator(factor=0.55)     

                c1.label(text=translate("Spawn")+":",)
                c2.prop(psy_active, "s_instances_pick_method", text="",)

                if (psy_active.s_instances_pick_method=="pick_idx") and (psy_active.s_distribution_method!="manual_all"):
                    
                    box.separator()
                    
                    box = extra_layout.box()
                    box.separator(factor=0.5)
                    word_wrap(layout=box, alignment="CENTER", max_char=34, active=False, icon="ERROR",
                        string=translate("This method is designed for manual distribution mode only."),)
                    
                    ui_templates.separator_box_in(box)
                    
                    return None 

                col.separator(factor=0.75)

                #list template

                ui_list = col.column(align=True)
                ui_list.template_list("SCATTER5_UL_list_instances", "", coll_ptr, "objects", psy_active, "ui_instances_list_idx", rows=5, sort_lock=True,)

                #add operator

                add = ui_list.column(align=True)
                add.active = (bpy.context.mode=="OBJECT")
                add.operator_menu_enum("scatter5.add_instances", "method", text=translate("Add Instance(s)"), icon="ADD",)

                #seed 

                if psy_active.s_instances_pick_method in ("pick_random","pick_rate",):

                    col.separator(factor=2)
                    
                    rrow = col.row(align=True)
                    prop = rrow.row(align=True)
                    prop.prop(psy_active, "s_instances_seed",)
                    button = rrow.row(align=True)
                    button.scale_x = 1.2
                    button.prop(psy_active, "s_instances_is_random_seed", icon_value=cust_icon("W_DICE"), text="",)

                #index

                elif (psy_active.s_instances_pick_method=="pick_idx"):
                    pass

                #scale

                elif (psy_active.s_instances_pick_method=="pick_scale"):

                    col.separator(factor=2)

                    col.prop(psy_active, "s_instances_id_scale_method", text="",)

                #color 

                elif (psy_active.s_instances_pick_method=="pick_color"):

                    col.separator(factor=2)

                    col.prop(psy_active, "s_instances_id_color_sample_method", text="",)

                    col.separator(factor=1)

                    if (psy_active.s_instances_id_color_sample_method=="vcol"):

                        mask = col.row(align=True)

                        ptr = mask.row(align=True)
                        ptr.alert = ( bool(psy_active.s_instances_vcol_ptr) and not is_attr_surfs_shared(system=psy_active, attr_type='vcol', attr_name=psy_active.s_instances_vcol_ptr,) )
                        ptr.prop(psy_active, "s_instances_vcol_ptr", text="", icon="GROUP_VCOL", placeholder=" "+translate("Color Attribute"),)

                        op = mask.operator("scatter5.vg_quick_paint",
                            text="",
                            icon="VPAINT_HLT" if psy_active.s_instances_vcol_ptr else "ADD",
                            depress=((bpy.context.mode=="PAINT_VERTEX") and (getattr(bpy.context.object.data.color_attributes.active_color,"name",'')==psy_active.s_instances_vcol_ptr)),
                            )
                        op.group_name = psy_active.s_instances_vcol_ptr
                        op.mode = "vcol" 
                        op.api = f"emitter.scatter5.particle_systems['{psy_active.name}'].s_instances_vcol_ptr"

                    elif (psy_active.s_instances_id_color_sample_method=="text"):

                        #Draw Texture Data Block

                        block = col.column()
                        
                        #find node
                        patnode = psy_active.get_scatter_node("s_instances_pick_color_textures", strict=True, raise_exception=False,)
                        if (patnode is None):
                            block.label(text="Error, Node missing")
                            return
                        node = patnode.node_tree.nodes["texture"]
                        
                        draw_texture_datablock(block, system=psy_active, ptr_name=f"s_instances_texture_ptr", texture_node=node, new_name=f"{psy_active.name.title()}InstanceIdx",)

                    col.separator(factor=1)

                    col.prop(psy_active, "s_instances_id_color_tolerence",)

                #cluster

                elif (psy_active.s_instances_pick_method=="pick_cluster"):
                        
                    col.separator(factor=2)

                    if (psy_active.s_distribution_method=="clumping"):

                        _, is_toggled = ui_templates.bool_toggle(col, psy_active, "s_instances_pick_clump", 
                            label=translate("Use Clumps as Clusters"), 
                            icon="STICKY_UVS_LOC", 
                            use_layout_left_spacer=False,
                            )
                        if is_toggled:

                            col = col.column(align=True)
                            col.active = False

                        col.separator(factor=1)

                    twor = col.row()
                    c1 = twor.column()
                    c1.scale_x = 0.55
                    c2 = twor.column()

                    c1.label(text=translate("Space")+":")
                    c2.prop(psy_active, "s_instances_pick_cluster_projection_method", text="",)

                    col.separator()
                    col.prop(psy_active, "s_instances_pick_cluster_scale",)
                    col.prop(psy_active, "s_instances_pick_cluster_blur",)
                
                    rrow = col.row(align=True)
                    prop = rrow.row(align=True)
                    prop.prop(psy_active, "s_instances_seed")
                    button = rrow.row(align=True)
                    button.scale_x = 1.2
                    button.prop(psy_active, "s_instances_is_random_seed", icon_value=cust_icon("W_DICE"), text="",)

            ui_templates.separator_box_in(box)
    return 


# oooooooooo.    o8o                      oooo
# `888'   `Y8b   `"'                      `888
#  888      888 oooo   .oooo.o oo.ooooo.   888   .oooo.   oooo    ooo
#  888      888 `888  d88(  "8  888' `88b  888  `P  )88b   `88.  .8'
#  888      888  888  `"Y88b.   888   888  888   .oP"888    `88..8'
#  888     d88'  888  o.  )88b  888   888  888  d8(  888     `888'
# o888bood8P'   o888o 8""888P'  888bod8P' o888o `Y888""8o     .8'
#                               888                       .o..P'
#                              o888o                      `Y8P'


def draw_particle_display(self,layout):
    
    scat_scene, scat_ui, scat_win, emitter, psy_active, group_active = get_props()
    
    box, is_open = ui_templates.box_panel(layout, 
        panelopen_propname="ui_tweak_display", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_tweak_display");BOOL_VALUE(0)
        panel_icon="CAMERA_STEREO", 
        master_category_bool="s_display_master_allow",
        panel_name=translate("Display"),
        popover_info="SCATTER5_PT_docs", 
        popover_gearwheel="SCATTER5_PT_per_settings_category_header",       
        popover_uilayout_context_set="s_display",
        is_tweaking_panel=True,
        )
    if is_open:

            if warnings(box):
                return None

            ui_is_active, ui_is_enabled = True, True
            ui_is_active = active_check(psy_active, s_category="s_display", prop=ui_is_active,)
            ui_is_enabled = lock_check(psy_active, s_category="s_display", prop=ui_is_enabled,)
            if (psy_active.is_linked): ui_is_enabled = False

            ########## ########## Display Method 

            tocol, tits, is_toggled = ui_templates.bool_toggle(box, psy_active, "s_display_allow", 
                label=translate("Display As"), 
                icon="CAMERA_STEREO", 
                enabled=ui_is_enabled,
                active=ui_is_active,
                arrowopen_propname="ui_display_allow", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_display_allow");BOOL_VALUE(1)
                return_sublayout=True,
                return_rowlayout=True,
                draw_condition=psy_active.s_instances_method=="ins_collection",
                )
            draw_visibility_methods(psy_active, tits, "s_display")
            if is_toggled:

                met = tocol.column(align=True)
                met.label(text=translate("Method")+":")
                met.prop(psy_active, "s_display_method", text="",)

                match psy_active.s_display_method:

                    case 'placeholder':
                        tocol.separator(factor=0.1)
                        col = tocol.column()
                        col.separator(factor=0.1)
                        col.template_icon_view(psy_active, "s_display_placeholder_type", show_labels=False, scale=5.0, scale_popup=5.0,)
                        
                        col.separator(factor=0.1)
                        vec = col.column()
                        vec.scale_y = 0.9
                        vec.prop(psy_active, "s_display_placeholder_scale")

                    case 'placeholder_custom':
                        tocol.separator(factor=0.1)
                        col = tocol.column()
                        col.separator(factor=0.1)
                        col.prop(psy_active, "s_display_custom_placeholder_ptr", text="",)
                        
                        col.separator(factor=0.1)
                        vec = col.column()
                        vec.scale_y = 0.9
                        vec.prop(psy_active, "s_display_placeholder_scale")

                    case 'point':
                        tocol.separator(factor=0.7)
                        col = tocol.column()
                        col.prop(psy_active, "s_display_point_radius")

                    case 'cloud':
                        tocol.separator(factor=0.7)
                        col = tocol.column(align=True)
                        col.prop(psy_active, "s_display_cloud_radius")
                        col.prop(psy_active, "s_display_cloud_density")
                    
                    case 'bb':
                        pass
                    
                    case 'convexhull':
                        pass
                    
                #Reveal Near

                tocol.separator(factor=0.65)

                tocol2, is_toggled2 = ui_templates.bool_toggle(tocol, psy_active, "s_display_camdist_allow", 
                    label=translate("Reveal Near Cam"), 
                    icon="PROP_ON", 
                    use_layout_left_spacer=False,
                    return_sublayout=True,
                    )
                if is_toggled2:

                    if (bpy.context.scene.camera is None):

                        tocol2.separator(factor=0.3)
                        moreinfo = tocol2.row()
                        moreinfo.emboss = "NONE"
                        moreinfo.context_string_set("pass_ui_arg_popover","nocamera_info")
                        moreinfo.popover(panel="SCATTER5_PT_docs", text=translate("No Camera Found"), icon="INFO",)
                        tocol2.separator(factor=0.01)

                    else: 
                        tocol2.prop(psy_active, "s_display_camdist_distance")

                        #Camera Update Method

                        tocol2.separator(factor=0.5)

                        draw_camera_update_method(layout=tocol2, psy_active=psy_active)

            ui_templates.separator_box_in(box)
    return 


#   .oooooo.
#  d8P'  `Y8b
# 888           oooo d8b  .ooooo.  oooo  oooo  oo.ooooo.
# 888           `888""8P d88' `88b `888  `888   888' `88b
# 888     ooooo  888     888   888  888   888   888   888
# `88.    .88'   888     888   888  888   888   888   888
#  `Y8bood8P'   d888b    `Y8bod8P'  `V88V"V8P'  888bod8P'
#                                               888
#                                              o888o

""""
def draw_group_members(self,layout):
    
    scat_scene, scat_ui, scat_win, emitter, psy_active, group_active = get_props()
    psy_members = group_active.get_psy_members()
    
    box, is_open = ui_templates.box_panel(layout, 
        panelopen_propname="ui_tweak_group_members", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_tweak_group_members");BOOL_VALUE(1)
        panel_icon="COMMUNITY", 
        panel_name=translate("Group Members")+f" [{len(psy_members)}]",
        popover_info="SCATTER5_PT_docs",
        popover_uilayout_context_set="s_gr_members",
        )
    if is_open:
            
            tocol = box.column()

            tocol.prop(group_active, "name", icon="OUTLINER_COLLECTION", text="",)

            items = tocol.column(align=True)
            
            #browse interface item
            for item in emitter.scatter5.particle_interface_items:
                
                #filter non psy members
                p = item.get_interface_item_source()
                if (p not in psy_members):
                    continue
                
                itembox = items.box()
                itemrow = itembox.row()
                
                if (item.interface_ident_icon!=""): 
                    indent = itemrow.row(align=True)
                    indent.scale_x = 0.85
                    indent.label(text="", icon_value=cust_icon(item.interface_ident_icon),)
                
                colname = itemrow.row(align=True)
                colname.alignment = "LEFT"

                color = colname.row()
                color.scale_x = 0.25
                color.prop(p,"s_color", text="",)

                name = colname.row()
                name.prop(p,"name", text="", emboss=False, )
                
                ope = colname.row()
                ope.operator("scatter5.dummy", text="", icon="TRASH",)
                
                continue
            
            add = tocol.row()
            add.operator_menu_enum("scatter5.add_instances", "method", text=translate("Add System(s)"), icon="ADD",)
                        
            ui_templates.separator_box_in(box)
        
    return 
"""

"""
def draw_group_distribution(self,layout):

    scat_scene, scat_ui, scat_win, emitter, psy_active, group_active = get_props()

    box, is_open = ui_templates.box_panel(layout, 
        panelopen_propname="ui_tweak_group_distribution", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_tweak_group_distribution");BOOL_VALUE(0)
        panel_icon="STICKY_UVS_DISABLE", 
        master_category_bool="s_gr_distribution_master_allow",
        panel_name=translate("Group Density"),
        popover_info="SCATTER5_PT_docs",
        popover_uilayout_context_set="s_gr_distribution",
        is_tweaking_panel=True,
        )
    if is_open:

            ui_is_active = True 
            ui_is_active = active_check(group_active, s_category="s_gr_distribution", prop=ui_is_active,)
            
            ########## ########## Density Boost

            tocol, is_toggled = ui_templates.bool_toggle(box, group_active, "s_gr_distribution_density_boost_allow",
                label=translate("Density Boost"),
                icon="ZOOM_IN",
                active=ui_is_active,
                arrowopen_propname="ui_gr_distribution_density_boost_allow", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_gr_distribution_density_boost_allow");BOOL_VALUE(1)
                return_sublayout=True,
                )
            if is_toggled:
                
                tocol.prop(group_active,"s_gr_distribution_density_boost_factor")
                
            ui_templates.separator_box_in(box)
    return 
"""

def draw_group_masks(self,layout):

    scat_scene, scat_ui, scat_win, emitter, psy_active, group_active = get_props()

    box, is_open = ui_templates.box_panel(layout, 
        panelopen_propname="ui_tweak_group_masks", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_tweak_group_masks");BOOL_VALUE(1)
        panel_icon="MOD_MASK",
        master_category_bool="s_gr_mask_master_allow",
        panel_name=translate("Group Culling Masks"),
        popover_info="SCATTER5_PT_docs",
        popover_uilayout_context_set="s_gr_mask",
        is_tweaking_panel=True,
        )
    if is_open:
                
            ui_is_active, ui_is_enabled = True, True
            ui_is_active = active_check(group_active, s_category="s_gr_mask", prop=ui_is_active,)
            if (group_active.is_linked): ui_is_enabled = False
            
            ########## ########## Vgroup

            tocol, is_toggled = ui_templates.bool_toggle(box, group_active, "s_gr_mask_vg_allow", 
                label=translate("Vertex-Group"), 
                icon="WPAINT_HLT", 
                active=ui_is_active,
                enabled=ui_is_enabled,
                arrowopen_propname="ui_gr_mask_vg_allow", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_gr_mask_vg_allow");BOOL_VALUE(1)
                return_sublayout=True,
                )
            if is_toggled:

                    mask_col = tocol.column(align=True)
                    mask_col.separator(factor=0.35)

                    exists = (group_active.s_gr_mask_vg_ptr!="")

                    #mask pointer

                    mask = mask_col.row(align=True)

                    ptr = mask.row(align=True)
                    ptr.alert = ( bool(group_active.s_gr_mask_vg_ptr) and not is_attr_surfs_shared(system=group_active, attr_type='vg', attr_name=group_active.s_gr_mask_vg_ptr,) )
                    ptr.prop(group_active, f"s_gr_mask_vg_ptr", text="", icon="GROUP_VERTEX", placeholder=" "+translate("Vertex-Group"),)
                    
                    if (exists):
                        mask.prop(group_active, f"s_gr_mask_vg_revert", text="", icon="ARROW_LEFTRIGHT",)

                    #paint or create operator

                    op = mask.operator("scatter5.vg_quick_paint",
                        text="",
                        icon="BRUSH_DATA" if exists else "ADD",
                        depress=((bpy.context.mode=="PAINT_WEIGHT") and (getattr(bpy.context.object.vertex_groups.active,"name",'')==group_active.s_gr_mask_vg_ptr)),
                        )
                    op.group_name = group_active.s_gr_mask_vg_ptr
                    op.mode = "vg" 
                    op.api = f"emitter.scatter5.particle_groups['{group_active.name}'].s_gr_mask_vg_ptr"

                    tocol.separator(factor=1)

            ########## ########## Vcolor

            tocol, is_toggled = ui_templates.bool_toggle(box, group_active, "s_gr_mask_vcol_allow", 
                label=translate("Color Attribute"), 
                icon="VPAINT_HLT", 
                active=ui_is_active,
                enabled=ui_is_enabled,
                arrowopen_propname="ui_gr_mask_vcol_allow", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_gr_mask_vcol_allow");BOOL_VALUE(0)
                return_sublayout=True,
                )
            if is_toggled:

                    mask_col = tocol.column(align=True)

                    #mask pointer

                    mask = mask_col.row(align=True)

                    ptr = mask.row(align=True)
                    ptr.alert = ( bool(group_active.s_gr_mask_vcol_ptr) and not is_attr_surfs_shared(system=group_active, attr_type='vcol', attr_name=group_active.s_gr_mask_vcol_ptr,) )
                    ptr.prop(group_active, f"s_gr_mask_vcol_ptr", text="", icon="GROUP_VCOL", placeholder=" "+translate("Color Attribute"),)

                    #color for add/paint operator 

                    exists = (group_active.s_gr_mask_vcol_ptr!="")
                    set_color = (1,1,1)

                    if (exists):

                        #set color
                        equivalence = {"id_picker":group_active.s_gr_mask_vcol_id_color_ptr,"id_greyscale":(1,1,1),"id_red":(1,0,0),"id_green":(0,1,0),"id_blue":(0,0,1),"id_black":(0,0,0),"id_white":(1,1,1),"id_saturation":(1,1,1),"id_value":(1,1,1),"id_hue":(1,1,1),"id_lightness":(1,1,1),"id_alpha":(1,1,1),}
                        set_color = equivalence[group_active.s_gr_mask_vcol_color_sample_method]

                        #reverse button 
                        mask.prop(group_active, "s_gr_mask_vcol_revert", text="", icon="ARROW_LEFTRIGHT",)

                    #add operator 

                    op = mask.operator("scatter5.vg_quick_paint",
                        text="",
                        icon="BRUSH_DATA" if exists else "ADD",
                        depress=((bpy.context.mode=="PAINT_VERTEX") and (getattr(bpy.context.object.data.color_attributes.active_color,"name",'')==group_active.s_gr_mask_vcol_ptr)),
                        )
                    op.group_name = group_active.s_gr_mask_vcol_ptr
                    op.mode = "vcol" 
                    op.set_color = set_color
                    op.api = f"emitter.scatter5.particle_groups['{group_active.name}'].s_gr_mask_vcol_ptr"

                    #sample method

                    if (exists): 

                        meth = mask_col.column(align=True)
                        meth.label(text=translate("Sample")+":")

                        methrow = meth.row(align=True)
                        methrow.prop(group_active, "s_gr_mask_vcol_color_sample_method", text="",)

                        if (group_active.s_gr_mask_vcol_color_sample_method=="id_picker"):
                            color = methrow.row(align=True)
                            color.scale_x = 0.35
                            color.prop(group_active, "s_gr_mask_vcol_id_color_ptr", text="",)

                    tocol.separator(factor=1)

            ########## ########## Bitmap

            tocol, is_toggled = ui_templates.bool_toggle(box, group_active, "s_gr_mask_bitmap_allow", 
                label=translate("Image"), 
                icon="TPAINT_HLT", 
                active=ui_is_active,
                enabled=ui_is_enabled,
                arrowopen_propname="ui_gr_mask_bitmap_allow", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_gr_mask_bitmap_allow");BOOL_VALUE(0)
                return_sublayout=True,
                )
            if is_toggled:

                    mask_col = tocol.column(align=True)

                    #mask pointer and add operator 

                    mask = mask_col.row(align=True)
                    
                    ptr = mask.row(align=True)
                    ptr.alert = ( bool(group_active.s_gr_mask_bitmap_ptr) and (group_active.s_gr_mask_bitmap_ptr not in bpy.data.images) )
                    ptr.prop(group_active, "s_gr_mask_bitmap_ptr", text="", icon="IMAGE_DATA", placeholder=" "+translate("Image"),)

                    #color for add/paint operator 

                    exists = (group_active.s_gr_mask_bitmap_ptr!="")
                    set_color = (0,0,0)

                    if (exists):

                        #set color
                        equivalence = {"id_picker":group_active.s_gr_mask_bitmap_id_color_ptr,"id_greyscale":(1,1,1),"id_red":(1,0,0),"id_green":(0,1,0),"id_blue":(0,0,1),"id_black":(0,0,0),"id_white":(1,1,1),"id_saturation":(1,1,1),"id_value":(1,1,1),"id_hue":(1,1,1),"id_lightness":(1,1,1),"id_alpha":(1,1,1),}
                        set_color = equivalence[group_active.s_gr_mask_bitmap_color_sample_method]

                        #reverse button 
                        mask.prop(group_active, "s_gr_mask_bitmap_revert", text="", icon="ARROW_LEFTRIGHT",)

                    #add operator 

                    if (not exists):

                        op = mask.operator("scatter5.image_utils", text="", icon="ADD",)
                        op.option = "new"
                        op.img_name = group_active.s_gr_mask_bitmap_ptr
                        op.api = f"emitter.scatter5.particle_groups['{group_active.name}'].s_gr_mask_bitmap_ptr"

                    else:
                        imgpaint_depresscond = ( (bpy.context.mode=="PAINT_TEXTURE") and (bpy.context.scene.tool_settings.image_paint.mode=='IMAGE') and (bpy.context.scene.tool_settings.image_paint.canvas==bpy.data.images.get(group_active.s_gr_mask_bitmap_ptr)) and (bpy.context.object.data.uv_layers.active) and (bpy.context.object.data.uv_layers.active.name==group_active.s_gr_mask_bitmap_uv_ptr) )
                        op = mask.operator("scatter5.image_utils", text="", icon="BRUSH_DATA", depress=imgpaint_depresscond,)
                        op.option = "paint"
                        op.paint_color = set_color
                        op.uv_ptr = group_active.s_gr_mask_bitmap_uv_ptr
                        op.img_name = group_active.s_gr_mask_bitmap_ptr
                        op.api = f"emitter.scatter5.particle_groups['{group_active.name}'].s_gr_mask_bitmap_ptr"

                        mask_col.separator(factor=0.8)
                        
                        ptr = mask_col.row(align=True)
                        ptr.alert = ( bool(group_active.s_gr_mask_bitmap_uv_ptr) and not is_attr_surfs_shared(system=group_active, attr_type='uv', attr_name=group_active.s_gr_mask_bitmap_uv_ptr,) )
                        ptr.prop(group_active, "s_gr_mask_bitmap_uv_ptr", text="", icon="GROUP_UVS", placeholder=" "+translate("UV Map"),)

                        #sample method 

                        meth = mask_col.column(align=True)
                        meth.label(text=translate("Sample")+":")

                        methrow = meth.row(align=True)
                        methrow.prop(group_active, "s_gr_mask_bitmap_color_sample_method", text="",)

                        if (group_active.s_gr_mask_bitmap_color_sample_method=="id_picker"):
                            color = methrow.row(align=True)
                            color.scale_x = 0.35
                            color.prop(group_active, "s_gr_mask_bitmap_id_color_ptr", text="",)

                    tocol.separator(factor=1.15)
                    
            ########## ########## Material

            tocol, is_toggled = ui_templates.bool_toggle(box, group_active, "s_gr_mask_material_allow", 
                label=translate("Material Slot"), 
                icon="MATERIAL", 
                active=ui_is_active,
                enabled=ui_is_enabled,
                arrowopen_propname="ui_gr_mask_material_allow", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_gr_mask_material_allow");BOOL_VALUE(0)
                return_sublayout=True,
                )
            if is_toggled:

                    mask = tocol.row(align=True)

                    ptr = mask.row(align=True)
                    ptr.alert = ( bool(group_active.s_gr_mask_material_ptr) and not is_attr_surfs_shared(system=group_active, attr_type='mat', attr_name=group_active.s_gr_mask_material_ptr,) )
                    ptr.prop(group_active, "s_gr_mask_material_ptr", text="", icon="MATERIAL", placeholder=" "+translate("Material"),)
                    
                    if (group_active.s_gr_mask_material_ptr!=""):
                        mask.prop(group_active, "s_gr_mask_material_revert", text="", icon="ARROW_LEFTRIGHT",)

                    tocol.separator(factor=1)

            ########## ########## Curve 

            tocol, is_toggled = ui_templates.bool_toggle(box, group_active, "s_gr_mask_curve_allow", 
                label=translate("Bezier-Area"), 
                icon="CURVE_BEZCIRCLE", 
                active=ui_is_active,
                enabled=ui_is_enabled,
                arrowopen_propname="ui_gr_mask_curve_allow", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_gr_mask_curve_allow");BOOL_VALUE(0)
                return_sublayout=True,
                )
            if is_toggled:

                    mask = tocol.row(align=True)
                    curve_row = mask.row(align=True)
                    curve_row.alert = (group_active.s_gr_mask_curve_ptr is not None and group_active.s_gr_mask_curve_ptr.name not in bpy.context.scene.objects)
                    curve_row.prop(group_active, "s_gr_mask_curve_ptr", text="", icon="CURVE_BEZCIRCLE",)

                    exists = (group_active.s_gr_mask_curve_ptr is not None)
                    if (exists):
                        mask.prop(group_active, "s_gr_mask_curve_revert", text="", icon="ARROW_LEFTRIGHT",)
                        op = mask.operator("scatter5.draw_bezier_area", text="", icon="BRUSH_DATA", depress=scat_win.mode=="DRAW_AREA",)
                        op.edit_existing = group_active.s_gr_mask_curve_ptr.name 
                        op.standalone = True
                    else: 
                        op = mask.operator("scatter5.add_bezier_area", text="", icon="ADD",)
                        op.api = f"bpy.context.scene.scatter5.emitter.scatter5.particle_groups['{group_active.name}'].s_gr_mask_curve_ptr"

                    tocol.separator(factor=1)

            ########## ########## Boolean

            tocol, is_toggled = ui_templates.bool_toggle(box, group_active, "s_gr_mask_boolvol_allow", 
                label=translate("Boolean"), 
                icon="MOD_BOOLEAN", 
                active=ui_is_active,
                enabled=ui_is_enabled,
                arrowopen_propname="ui_gr_mask_boolvol_allow", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_gr_mask_boolvol_allow");BOOL_VALUE(0)
                return_sublayout=True,
                )
            if is_toggled:

                    draw_coll_str_ptr(layout=tocol, system=group_active, api="s_gr_mask_boolvol_coll_ptr", revert_api="s_gr_mask_boolvol_revert", add_coll_name="Boolean-Objects",)

                    tocol.separator(factor=1)

            ########## ########## Upward Obstruction

            tocol, is_toggled = ui_templates.bool_toggle(box, group_active, "s_gr_mask_upward_allow", 
                label=translate("Upward-Obstruction"), 
                icon="TRIA_UP_BAR", 
                active=ui_is_active,
                enabled=ui_is_enabled,
                arrowopen_propname="ui_gr_mask_upward_allow", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_gr_mask_upward_allow");BOOL_VALUE(0)
                return_sublayout=True,
                )
            if is_toggled:

                    draw_coll_str_ptr(layout=tocol, system=group_active, api="s_gr_mask_upward_coll_ptr", revert_api="s_gr_mask_upward_revert", add_coll_name="Upward-Objects",)

                    tocol.separator(factor=0.5)
                    
            ui_templates.separator_box_in(box)
    return 

def draw_group_scale(self,layout):

    scat_scene, scat_ui, scat_win, emitter, psy_active, group_active = get_props()

    box, is_open = ui_templates.box_panel(layout, 
        panelopen_propname="ui_tweak_group_scale", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_tweak_group_scale");BOOL_VALUE(1)
        panel_icon="OBJECT_ORIGIN",
        master_category_bool="s_gr_scale_master_allow",
        panel_name=translate("Group Scale"),
        popover_info="SCATTER5_PT_docs",
        popover_uilayout_context_set="s_gr_scale",
        is_tweaking_panel=True,
        )
    if is_open:

            ui_is_active, ui_is_enabled = True, True
            ui_is_active = active_check(group_active, s_category="s_gr_scale", prop=ui_is_active,)
            if (group_active.is_linked): ui_is_enabled = False
            
            ########## ########## Scale Boost
            
            tocol, is_toggled = ui_templates.bool_toggle(box, group_active, "s_gr_scale_boost_allow",
                label=translate("Scale Boost"),
                icon="ZOOM_IN",
                active=ui_is_active,
                enabled=ui_is_enabled,
                arrowopen_propname="ui_gr_scale_boost_allow", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_gr_scale_boost_allow");BOOL_VALUE(1)
                return_sublayout=True,
                )
            if is_toggled:
                
                vec = tocol.column()
                vec.scale_y = 0.9
                vec.prop(group_active, "s_gr_scale_boost_value",)

                tocol.separator(factor=0.5)

                vec = tocol.column(align=True)
                vec.label(text=translate("Uniform")+":",)
                vec.prop(group_active, "s_gr_scale_boost_multiplier",)
                                
                #ideally would need universal masks for groups as well.. 
                #but well, complicated to implement 
                
            ui_templates.separator_box_in(box)
    return 

def draw_group_pattern(self,layout):

    scat_scene, scat_ui, scat_win, emitter, psy_active, group_active = get_props()

    box, is_open = ui_templates.box_panel(layout, 
        panelopen_propname="ui_tweak_group_pattern", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_tweak_group_pattern");BOOL_VALUE(1)
        panel_icon="TEXTURE",
        master_category_bool="s_gr_pattern_master_allow",
        panel_name=translate("Group Pattern"),
        popover_info="SCATTER5_PT_docs",
        popover_uilayout_context_set="s_gr_pattern",
        )
    if is_open:

            ui_is_active, ui_is_enabled = True, True
            ui_is_active = active_check(group_active, s_category="s_gr_pattern", prop=ui_is_active,)
            if (group_active.is_linked): ui_is_enabled = False
            
            ########## ########## Pattern 1

            tocol, is_toggled = ui_templates.bool_toggle(box, group_active, "s_gr_pattern1_allow",
                label=translate("Pattern"),
                icon=f"W_PATTERN1", 
                active=ui_is_active,
                enabled=ui_is_enabled,
                arrowopen_propname=f"ui_gr_pattern1_allow", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_gr_pattern1_allow");BOOL_VALUE(1)
                return_sublayout=True,
                )
            if is_toggled:

                psy_members = group_active.get_psy_members()
                if (len(psy_members)==0):
                    tocol.label(text="Error, this group is empty")
                    return
                
                #find node
                patnode = psy_members[0].get_scatter_node("s_gr_pattern1", strict=True, raise_exception=False,)
                if (patnode is None):
                    tocol.label(text="Error, Node missing")
                    return
                node = patnode.node_tree.nodes["texture"]
                
                #Draw Texture Data Block

                block = tocol.column()
                block.label(text=translate("Texture-Data")+":")
                
                draw_texture_datablock(block, system=group_active, ptr_name="s_gr_pattern1_texture_ptr", texture_node=node, new_name=f"{group_active.name.title()}Pattern",)

                #Draw Particle ID specific
                    
                tocol.separator(factor=0.75)

                met=tocol.column(align=True)
                met.label(text=translate("Sample")+":")
                met.prop(group_active, "s_gr_pattern1_color_sample_method", text="",)
                color_sample_method = eval("group_active.s_gr_pattern1_color_sample_method")
                
                if (color_sample_method=="id_picker"):
                    pick = met.row(align=True)
                    ptrc = pick.row(align=True)
                    ptrc.scale_x = 0.4
                    ptrc.prop(group_active, "s_gr_pattern1_id_color_ptr", text="",)
                    pick.prop(group_active, "s_gr_pattern1_id_color_tolerence")

                tocol.separator(factor=0.75)

                #Feature Influence 
                draw_feature_influence(layout=tocol, system=group_active, api_name="s_gr_pattern1",)
                
                #ideally would need universal masks for groups as well.. 
                #but well, complicated to implement 
                                
            ui_templates.separator_box_in(box)
    return 



# oooooooooo.                        o8o
# `888'   `Y8b                       `"'
#  888     888  .ooooo.   .oooooooo oooo  ooo. .oo.   ooo. .oo.    .ooooo.  oooo d8b  .oooo.o
#  888oooo888' d88' `88b 888' `88b  `888  `888P"Y88b  `888P"Y88b  d88' `88b `888""8P d88(  "8
#  888    `88b 888ooo888 888   888   888   888   888   888   888  888ooo888  888     `"Y88b.
#  888    .88P 888    .o `88bod8P'   888   888   888   888   888  888    .o  888     o.  )88b
# o888bood8P'  `Y8bod8P' `8oooooo.  o888o o888o o888o o888o o888o `Y8bod8P' d888b    8""888P'
#                        d"     YD
#                        "Y88888P'


sepa_small = 0.15
sepa_large = 3.15

def draw_beginner_interface(self,layout):

    scat_scene, scat_ui, scat_win, emitter, psy_active, group_active = get_props()

    box, is_open = ui_templates.box_panel(layout, 
        panelopen_propname="ui_tweak_beginners", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_tweak_beginners");BOOL_VALUE(1)
        panel_name=translate("Beginner Interface"),
        )
    if is_open:

            if warnings(box):
                return None

            main = box.column()

            row = main.row()
            s1 = row.column()
            s1.scale_x = 1.25
            s1.active = True
            s1.alignment = "RIGHT"
            s2 = row.column() 

            #density controls 

            if (psy_active.s_distribution_method=="random"):
                s1.label(text=translate("Density"),)
                s2.prop(psy_active, "s_distribution_density", text="",)

                s1.label(text="Collision")
                ope = s2.row(align=True)
                ope.prop(psy_active,"s_distribution_limit_distance_allow", text="", icon="CHECKBOX_HLT" if psy_active.s_distribution_limit_distance_allow else "CHECKBOX_DEHLT")
                ope2 = ope.row(align=True)
                ope2.enabled = psy_active.s_distribution_limit_distance_allow
                ope2.prop(psy_active,"s_distribution_limit_distance", text="",) 
                
            else:
                s1.label(text=translate("Density"),)
                ope = s2.row()
                ope.active = False
                ope.operator("scatter5.dummy", text=translate("Read Only"),)

            s1.separator(factor=sepa_small) ; s2.separator(factor=sepa_small)

            #vgroup paint

            s1.label(text=translate("Vertex-Group"),)

            ope = s2.row(align=True)
            ope.prop(psy_active,"s_mask_vg_allow", text="", icon="CHECKBOX_HLT" if psy_active.s_mask_vg_allow else "CHECKBOX_DEHLT")
            ope2 = ope.row(align=True)
            ope2.enabled = psy_active.s_mask_vg_allow
            exists = (psy_active.s_mask_vg_ptr!="")
            op = ope2.operator("scatter5.vg_quick_paint",
                text="Paint",
                icon="BRUSH_DATA" if (exists) else "ADD",
                depress=((bpy.context.mode=="PAINT_WEIGHT") and (getattr(bpy.context.object.vertex_groups.active,"name",'')==psy_active.s_mask_vg_ptr)),
                )
            op.group_name = psy_active.s_mask_vg_ptr
            op.mode = "vg" 
            op.api = f"emitter.scatter5.particle_systems['{psy_active.name}'].s_mask_vg_ptr"

            s1.separator(factor=sepa_small) ; s2.separator(factor=sepa_small)

            #seed 

            s1.label(text=translate("Seed"),)
            ope = s2.row(align=True)
            op = ope.operator("scatter5.exec_line", text=translate("Randomize"), icon_value=cust_icon("W_DICE"),)
            op.api = f"psy_active.s_distribution_is_random_seed = True ; psy_active.get_scatter_mod().node_group.nodes['s_pattern1'].node_tree.nodes['texture'].node_tree.scatter5.texture.mapping_random_is_random_seed = True"
            op.description = translate("Randomize the seed of this distribution")
            
            #scale

            s1.separator(factor=sepa_large) ; s2.separator(factor=sepa_large)

            s1.label(text=translate("Scale"),)
            s2.prop(psy_active,"s_beginner_default_scale", text="",) 

            s1.separator(factor=sepa_small) ; s2.separator(factor=sepa_small)

            s1.label(text=translate("Random"),)
            s2.prop(psy_active,"s_beginner_random_scale", text="", slider=True,) 

            s1.separator(factor=sepa_small) ; s2.separator(factor=sepa_small)

            s1.label(text=translate("Vertex-Group"),)

            ope = s2.row(align=True)

            op = ope.operator("scatter5.exec_line", text="", icon="CHECKBOX_HLT" if psy_active.s_scale_shrink_allow else "CHECKBOX_DEHLT", depress=psy_active.s_scale_shrink_allow, )
            op.api = f"psy_active.s_scale_shrink_allow = {not psy_active.s_scale_shrink_allow} ; psy_active.s_scale_shrink_mask_method = 'mask_vg' ; psy_active.s_scale_shrink_mask_reverse = True"
            op.description = translate("Paint a scale shrink mask with the help of a vertex-group")
            
            ope2 = ope.row(align=True)
            ope2.enabled = psy_active.s_scale_shrink_allow
            exists = (psy_active.s_scale_shrink_mask_ptr!="")
            op = ope2.operator("scatter5.vg_quick_paint",
                text="Paint",
                icon="BRUSH_DATA" if exists else "ADD",
                depress=((bpy.context.mode=="PAINT_WEIGHT") and (getattr(bpy.context.object.vertex_groups.active,"name",'')==psy_active.s_scale_shrink_mask_ptr)),
                )
            op.group_name = psy_active.s_scale_shrink_mask_ptr
            op.mode = "vg" 
            op.api = f"emitter.scatter5.particle_systems['{psy_active.name}'].s_scale_shrink_mask_ptr"

            #rotation 

            s1.separator(factor=sepa_large) ; s2.separator(factor=sepa_large)

            s1.label(text=translate("Rotation Align"),)
            ope = s2.row(align=True)
            op = ope.operator("scatter5.exec_line",text=translate("Normal"), depress=(psy_active.s_rot_align_z_allow and psy_active.s_rot_align_z_method=='meth_align_z_normal'),)
            op.api = f"psy_active.s_rot_align_z_allow = True ;  psy_active.s_rot_align_z_method ='meth_align_z_normal'"
            op.description = translate("Align the +Z direction of your instances to your surface normal")

            op = ope.operator("scatter5.exec_line",text=translate("Local Z"), depress=(psy_active.s_rot_align_z_allow and psy_active.s_rot_align_z_method=='meth_align_z_local'),)
            op.api = f"psy_active.s_rot_align_z_allow = True ;  psy_active.s_rot_align_z_method ='meth_align_z_local'"
            op.description = translate("Align the +Z direction of your instances to the +Z direction of your surface object")
            
            s1.separator(factor=sepa_small) ; s2.separator(factor=sepa_small)

            s1.label(text=translate("Random"),)
            s2.prop(psy_active,"s_beginner_random_rot", text="", slider=True,)

            #texture

            s1.separator(factor=sepa_large) ; s2.separator(factor=sepa_large)

            #find node
            patnode = psy_active.get_scatter_node("s_pattern1", strict=True, raise_exception=False,)
            if (patnode is None):
                s1.label(text="Error, Node missing")
                return
            texture_node = patnode.node_tree.nodes["texture"]
            texture_exists = True
            texture_props = texture_node.node_tree.scatter5.texture

            if (texture_node.node_tree.name.startswith(".TEXTURE *DEFAULT")):

                s1.label(text=translate("Pattern"),)
                ope = s2.row(align=True)
                ope.context_pointer_set("pass_ui_arg_system", psy_active,)
                ope.context_pointer_set("pass_ui_arg_texture_node", texture_node,)
                op = ope.operator("scatter5.exec_line", text=translate("New"), icon="ADD",)
                op.api = "bpy.ops.scatter5.scatter_texture_new(ptr_name='s_pattern1_texture_ptr',new_name='BR-Pattern') ; psy_active.s_pattern1_allow = True"
                op.description = translate("Create a new Pattern texture, a procedural noise used to mask your distribution density and influence your instances scale")
                op.undo = "Creating New Pattern"

            elif (psy_active.s_pattern1_allow):

                s1.label(text=translate("Pattern"),)
                ope = s2.row(align=True)
                op = ope.operator("scatter5.exec_line", text=translate("Active"), icon="CHECKBOX_HLT", depress=True)
                op.api = f"psy_active.s_pattern1_allow = False"
                op.description = translate("Disable the procedural noise pattern influencing your distribution")

                s1.separator(factor=sepa_small) ; s2.separator(factor=sepa_small)

                s1.label(text=translate("Scale"),)
                s2.prop(texture_props, "scale", text="",)

                s1.separator(factor=sepa_small) ; s2.separator(factor=sepa_small)

                s1.label(text=translate("Brightness"),)
                s2.prop(texture_props, "intensity", text="",)

                s1.separator(factor=sepa_small) ; s2.separator(factor=sepa_small)

                s1.label(text=translate("Contrast"),)
                s2.prop(texture_props, "contrast", text="",)

                s1.separator(factor=sepa_small) ; s2.separator(factor=sepa_small)

                
            else:

                s1.label(text=translate("Pattern"),)
                ope = s2.row(align=True)
                op = ope.operator("scatter5.exec_line", text=translate("Inactive"), icon="CHECKBOX_DEHLT", depress=False,)
                op.api = f"psy_active.s_pattern1_allow = True"
                op.description = translate("Enable the procedural noise pattern influencing your distribution")

            #define instances 

            s1.separator(factor=sepa_large) ; s2.separator(factor=sepa_large)

            s1.label(text=translate("Displays"),)

            ope = s2.row(align=True)
            op = ope.operator("scatter5.exec_line", text=translate("Active") if psy_active.s_display_allow else translate("Inactive"), icon="CHECKBOX_HLT" if psy_active.s_display_allow else "CHECKBOX_DEHLT", depress=psy_active.s_display_allow, )
            op.api = f"psy_active.s_display_allow = {not psy_active.s_display_allow}"
            op.description = translate("Display your instances as lowpoly objects to draw less triangles on your screen and saving on GPU performance when navigating the viewport")

            s1.separator(factor=sepa_small) ; s2.separator(factor=sepa_small)

            s1.label(text=translate("Instances"),)

            ui_list = s2.column(align=True)
            ui_list.template_list("SCATTER5_UL_list_instances", "", psy_active.s_instances_coll_ptr, "objects", psy_active, "ui_instances_list_idx", rows=5, sort_lock=True,)
                
            add = ui_list.column(align=True)
            add.active = (bpy.context.mode=="OBJECT")
            add.operator_menu_enum("scatter5.add_instances", "method", text=translate("Add Instance(s)"), icon="ADD",)
        
            #Separator 

            ui_templates.separator_box_in(box)

    return

def draw_removal_interface(self,layout):

    scat_scene, scat_ui, scat_win, emitter, psy_active, group_active = get_props()

    if (psy_active is None):
        return

    s_abiotic_used    = psy_active.is_category_used("s_abiotic")
    s_ecosystem_used  = psy_active.is_category_used("s_ecosystem")
    s_proximity_used  = psy_active.is_category_used("s_proximity")
    s_push_used       = psy_active.is_category_used("s_push")
    s_wind_used       = psy_active.is_category_used("s_wind")
    s_visibility_used = psy_active.is_category_used("s_visibility")

    if any([s_abiotic_used, s_ecosystem_used, s_proximity_used, s_push_used, s_wind_used, s_visibility_used,]):

        box, is_open = ui_templates.box_panel(layout, 
            panelopen_propname="ui_tweak_removal", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_tweak_removal");BOOL_VALUE(1)
            panel_name=translate("Advanced Features"),
            popover_info="SCATTER5_PT_docs", 
            popover_uilayout_context_set="s_beginners_remove",
            )
        if is_open:

            main = box.column()

            row = main.row()
            split = row.split(factor = 0.375)
            s1 = split.column()
            s1.alignment = "RIGHT"
            s2 = split.column()

            s1.separator(factor=sepa_small) ; s2.separator(factor=sepa_small)

            if (s_visibility_used):
                s1.separator(factor=sepa_small) ; s2.separator(factor=sepa_small)

                s1.label(text=translate("Optimizations"),)
                ope = s2.row(align=True)
                op = ope.operator("scatter5.exec_line", text=translate("Remove"), icon="PANEL_CLOSE", depress=False,)
                op.api = f"psy_active.s_visibility_master_allow = False"
                op.undo = translate("Remove Visibility Features")
                op.description = translate("There are more advanced features enabled for this scatter-system, however these are not available for Biome-Reader! Would you like to remove them?")

            if (s_abiotic_used):
                s1.separator(factor=sepa_small) ; s2.separator(factor=sepa_small)

                s1.label(text=translate("Abiotic"),)
                ope = s2.row(align=True)
                op = ope.operator("scatter5.exec_line", text=translate("Remove"), icon="PANEL_CLOSE", depress=False,)
                op.api = f"psy_active.s_abiotic_master_allow = False"
                op.undo = translate("Remove Abiotic Features")
                op.description = translate("There are more advanced features enabled for this scatter-system, however these are not available for Biome-Reader! Would you like to remove them?")

            if (s_ecosystem_used):
                s1.separator(factor=sepa_small) ; s2.separator(factor=sepa_small)

                s1.label(text=translate("Ecosystem"),)
                ope = s2.row(align=True)
                op = ope.operator("scatter5.exec_line", text=translate("Remove"), icon="PANEL_CLOSE", depress=False,)
                op.api = f"psy_active.s_ecosystem_master_allow = False"
                op.undo = translate("Remove Ecosystem Features")
                op.description = translate("There are more advanced features enabled for this scatter-system, however these are not available for Biome-Reader! Would you like to remove them?")

            if (s_proximity_used):
                s1.separator(factor=sepa_small) ; s2.separator(factor=sepa_small)

                s1.label(text=translate("Proximity"),)
                ope = s2.row(align=True)
                op = ope.operator("scatter5.exec_line", text=translate("Remove"), icon="PANEL_CLOSE", depress=False,)
                op.api = f"psy_active.s_proximity_master_allow = False"
                op.undo = translate("Remove Proximity Features")
                op.description = translate("There are more advanced features enabled for this scatter-system, however these are not available for Biome-Reader! Would you like to remove them?")

            if (s_push_used):
                s1.separator(factor=sepa_small) ; s2.separator(factor=sepa_small)

                s1.label(text=translate("Offset"),)
                ope = s2.row(align=True)
                op = ope.operator("scatter5.exec_line", text=translate("Remove"), icon="PANEL_CLOSE", depress=False,)
                op.api = f"psy_active.s_push_master_allow = False"
                op.undo = translate("Remove Offset Features")
                op.description = translate("There are more advanced features enabled for this scatter-system, however these are not available for Biome-Reader! Would you like to remove them?")
            
            if (s_wind_used):
                s1.separator(factor=sepa_small) ; s2.separator(factor=sepa_small)

                s1.label(text=translate("Wind"),)
                ope = s2.row(align=True)
                op = ope.operator("scatter5.exec_line", text=translate("Remove"), icon="PANEL_CLOSE", depress=False,)
                op.api = f"psy_active.s_wind_master_allow = False"
                op.undo = translate("Remove Wind Features")
                op.description = translate("There are more advanced features enabled for this scatter-system, however these are not available for Biome-Reader! Would you like to remove them?")
            
            #Separator 

            ui_templates.separator_box_in(box)

    return

def draw_pros_interface(self, layout, context):

    scat_scene, scat_ui, scat_win, emitter, psy_active, group_active = get_props()

    box, is_open = ui_templates.box_panel(layout, 
        panelopen_propname="ui_tweak_pros", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_tweak_pros");BOOL_VALUE(1)
        panel_name=translate("Professional Workflow"),
        is_always_open=True,
        )
    if is_open:

        row = box.row()
        r1 = row.separator(factor=0.3)
        col = row.column()
        r3 = row.separator(factor=0.3)

        word_wrap(layout=col.box(), alignment="CENTER", active=True, max_char='auto', context=context, char_auto_sidepadding=0.85,
            string=translate("Get the workflow you need to become a pro!\n\nOur user-friendly interface is perfect for newbies, but our paid tool-kit for professionals is where the magic happens.\n\nWith advanced features, an efficient pipeline, and useful scattering operators, you'll be able to handle the most challenging projects with ease."),)
                
        col.separator(factor=0.75)

        ope = col.row()
        ope.scale_y = 1.2
        ope.operator("wm.url_open", text=translate("Upgrade Today"),).url = "https://blendermarket.com/products/scatter"

        #Separator 

        ui_templates.separator_box_in(box)

    return

def draw_group_beginner_masks(self,layout):

    scat_scene, scat_ui, scat_win, emitter, psy_active, group_active = get_props()

    box, is_open = ui_templates.box_panel(layout, 
        panelopen_propname="ui_beginners_tweak_group_masks", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_beginners_tweak_group_masks");BOOL_VALUE(1)
        panel_name=translate("Group Masks"),
        )
    if is_open:
            
        ui_is_active = True 
        ui_is_active = active_check(group_active, s_category="s_gr_mask", prop=ui_is_active,)
        
        ########## ########## Vgroup

        tocol, is_toggled = ui_templates.bool_toggle(box, group_active, "s_gr_mask_vg_allow", 
            label=translate("Vertex-Group"), 
            icon="WPAINT_HLT", 
            active=ui_is_active,
            return_sublayout=True,
            )
        if is_toggled:

                mask_col = tocol.column(align=True)
                mask_col.separator(factor=0.35)

                exists = (group_active.s_gr_mask_vg_ptr!="")

                #mask pointer

                mask = mask_col.row(align=True)

                ptr = mask.row(align=True)
                ptr.alert = ( bool(group_active.s_gr_mask_vg_ptr) and not is_attr_surfs_shared(system=group_active, attr_type='vg', attr_name=group_active.s_gr_mask_vg_ptr,) )
                ptr.prop(group_active, f"s_gr_mask_vg_ptr", text="", icon="GROUP_VERTEX", placeholder=" "+translate("Vertex-Group"),)
                
                if (exists):
                    mask.prop(group_active, f"s_gr_mask_vg_revert", text="", icon="ARROW_LEFTRIGHT",)

                #paint or create operator

                op = mask.operator("scatter5.vg_quick_paint",
                    text="",
                    icon="BRUSH_DATA" if exists else "ADD",
                    depress=((bpy.context.mode=="PAINT_WEIGHT") and (getattr(bpy.context.object.vertex_groups.active,"name",'')==group_active.s_gr_mask_vg_ptr)),
                    )
                op.group_name = group_active.s_gr_mask_vg_ptr
                op.mode = "vg" 
                op.api = f"emitter.scatter5.particle_groups['{group_active.name}'].s_gr_mask_vg_ptr"

                tocol.separator(factor=1)

        #Separator 

        ui_templates.separator_box_in(box)
            
    return 


#    .oooooo.   oooo
#   d8P'  `Y8b  `888
#  888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
#  888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
#  888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
#  `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#   `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'


class SCATTER5_PT_tweaking(bpy.types.Panel):

    bl_idname      = "SCATTER5_PT_tweaking"
    bl_label       = translate("Tweak")
    bl_category    = "USER_DEFINED" #will be replaced right before ui.__ini__.register()
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_context     = "" #nothing == enabled everywhere
    bl_order       = 3

    @classmethod
    def poll(cls, context,):
        if (context.scene.scatter5.emitter is None):
            return False
        if (context.mode not in ('OBJECT','PAINT_WEIGHT','PAINT_VERTEX','PAINT_TEXTURE','EDIT_MESH','EDIT_CURVE',)):
            return False
        return True 
        
    def draw_header(self, context):
        self.layout.label(text="", icon_value=cust_icon("W_SCATTER"),)

    def draw_header_preset(self, context):
        emitter_header(self)

    def draw(self, context):
        layout = self.layout
        draw_tweaking_panel(self, layout, context,)

classes = (
        
    SCATTER5_UL_list_instances,
    SCATTER5_PT_tweaking,

    )

#if __name__ == "__main__":
#    register()