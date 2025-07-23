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
# ooooooooo.                                                        .    o8o
# `888   `Y88.                                                    .o8    `"'
#  888   .d88' oooo d8b  .ooooo.  oo.ooooo.   .ooooo.  oooo d8b .o888oo oooo   .ooooo.   .oooo.o
#  888ooo88P'  `888""8P d88' `88b  888' `88b d88' `88b `888""8P   888   `888  d88' `88b d88(  "8
#  888          888     888   888  888   888 888ooo888  888       888    888  888ooo888 `"Y88b.
#  888          888     888   888  888   888 888    .o  888       888 .  888  888    .o o.  )88b
# o888o        d888b    `Y8bod8P'  888bod8P' `Y8bod8P' d888b      "888" o888o `Y8bod8P' 8""888P'
#                                  888
################################# o888o ##############################################################

"""

>>>DEPENDENCIES Precised below

>>>NOTE that in this module you'll find all properties registration of addon_prefs/window_manager/object/scene
   Some are stored in this module, some are not. See below, if `import from ..` 

>>>THERE ARE MORE PROPERTIES TOO! :

   -bpy.types.WindowManager.scatter5_bitmap_library ->Dynamic Enum
   -bpy.types.WindowManager.scatter5_preset_gallery ->Dynamic Enum
   -bpy.types.Texture.scatter5 

""" 

import bpy 

# ooooooooo.
# `888   `Y88.
#  888   .d88' oooo d8b  .ooooo.  oo.ooooo.   .oooo.o
#  888ooo88P'  `888""8P d88' `88b  888' `88b d88(  "8
#  888          888     888   888  888   888 `"Y88b.
#  888          888     888   888  888   888 o.  )88b
# o888o        d888b    `Y8bod8P'  888bod8P' 8""888P'
#                                  888
#                                 o888o

######### PER ADDON

#__init__.addon_prefs() == bpy.context.preferences.addons[__package__].preferences
from . addon_settings import SCATTER5_AddonPref
#__init__.addon_prefs().blend_environment_paths
from . addon_settings import SCATTER5_PR_blend_environment_paths

#special addon settings operator
from . addon_settings import SCATTER5_OT_export_addon_settings, SCATTER5_OT_import_addon_settings

######### PER OBJECT

#bpy.context.object.scatter5
from . objects_settings import SCATTER5_PR_Object
#bpy.context.object.scatter5.particle_systems
from . particle_settings import SCATTER5_PR_particle_systems
#bpy.context.object.scatter5.particle_groups
from . particle_settings import SCATTER5_PR_particle_groups
#bpy.context.object.scatter5.particle_interface_items
from .. ui.ui_system_list import SCATTER5_PR_particle_interface_items
#bpy.context.object.scatter5.mask_systems
from . mask_settings import SCATTER5_PR_procedural_vg

######### PER SCENE 

#bpy.context.scene.scatter5
from . scenes_settings import SCATTER5_PR_Scene

#bpy.context.scene.uuids
from . scenes_settings import SCATTER5_PR_uuids #LEGACY

#bpy.context.scene.scatter5.operators
from . ops_settings import SCATTER5_PR_operators
#bpy.context.scene.scatter5.operators.export_to_presets
from . ops_settings import SCATTER5_PR_export_to_presets
#bpy.context.scene.scatter5.operators.export_to_biome
from . ops_settings import SCATTER5_PR_export_to_biome
#bpy.context.scene.scatter5.operators.generate_thumbnail
from . ops_settings import SCATTER5_PR_generate_thumbnail
#bpy.context.scene.scatter5.operators.create_operators
from . ops_settings import SCATTER5_PR_creation_operators
#bpy.context.scene.scatter5.operators.xxx.instances/surfaces
from . ops_settings import SCATTER5_PR_objects
#bpy.context.scene.scatter5.operators.add_psy_preset
from . ops_settings import SCATTER5_PR_creation_operator_add_psy_preset
#bpy.context.scene.scatter5.operators.add_psy_density
from . ops_settings import SCATTER5_PR_creation_operator_add_psy_density
#bpy.context.scene.scatter5.operators.add_psy_manual
from . ops_settings import SCATTER5_PR_creation_operator_add_psy_manual
#bpy.context.scene.scatter5.operators.add_psy_modal
from . ops_settings import SCATTER5_PR_creation_operator_add_psy_modal
#bpy.context.scene.scatter5.operators.load_biome
from . ops_settings import SCATTER5_PR_creation_operator_load_biome

#bpy.context.scene.scatter5.manual
from .manual_settings import (
    SCATTER5_PR_manual_brush_tool_default,
    SCATTER5_PR_manual_brush_tool_dot,
    SCATTER5_PR_manual_brush_tool_spatter,
    SCATTER5_PR_manual_brush_tool_pose,
    SCATTER5_PR_manual_brush_tool_path,
    SCATTER5_PR_manual_brush_tool_chain,
    SCATTER5_PR_manual_brush_tool_line,
    SCATTER5_PR_manual_brush_tool_spray,
    SCATTER5_PR_manual_brush_tool_spray_aligned,
    SCATTER5_PR_manual_brush_tool_lasso_fill,
    SCATTER5_PR_manual_brush_tool_clone,
    SCATTER5_PR_manual_brush_tool_eraser,
    SCATTER5_PR_manual_brush_tool_dilute,
    SCATTER5_PR_manual_brush_tool_lasso_eraser,
    # SCATTER5_PR_manual_brush_tool_smooth,
    SCATTER5_PR_manual_brush_tool_move,
    SCATTER5_PR_manual_brush_tool_rotation_set,
    SCATTER5_PR_manual_brush_tool_random_rotation,
    SCATTER5_PR_manual_brush_tool_comb,
    SCATTER5_PR_manual_brush_tool_spin,
    SCATTER5_PR_manual_brush_tool_z_align,
    SCATTER5_PR_manual_brush_tool_scale_set,
    SCATTER5_PR_manual_brush_tool_grow_shrink,
    SCATTER5_PR_manual_brush_tool_object_set,
    SCATTER5_PR_manual_brush_tool_drop_down,
    SCATTER5_PR_manual_brush_tool_free_move,
    SCATTER5_PR_manual_brush_tool_attract_repulse,
    SCATTER5_PR_manual_brush_tool_push,
    # SCATTER5_PR_manual_brush_tool_turbulence,
    SCATTER5_PR_manual_brush_tool_gutter_ridge,
    SCATTER5_PR_manual_brush_tool_relax2,
    SCATTER5_PR_manual_brush_tool_turbulence2,
    SCATTER5_PR_manual_brush_tool_manipulator,
    SCATTER5_PR_manual_brush_tool_heaper,
    SCATTER5_PR_scene_manual,
)

######### PER BLEND (per text actually) 

#__init__.blend_prefs() == bpy.data.texts['.Geo-Scatter Settings'].scatter5
from . texts_settings import SCATTER5_PR_Blend

#blend_prefs().uuids
from . texts_settings import SCATTER5_PR_uuids_repository
#blend_prefs().sync_channels
from .. scattering.synchronize import SCATTER5_PR_sync_channels
#blend_prefs().sync_channels[].members
from .. scattering.synchronize import SCATTER5_PR_channel_members

######### PER WINDOW_MANAGER

#bpy.context.window_manager.scatter5
from . windows_settings import SCATTER5_PR_Window
#bpy.context.window_manager.scatter5.library
from .. ui.ui_biome_library import SCATTER5_PR_library
#bpy.context.window_manager.scatter5.folder_navigation
from .. ui.ui_biome_library import SCATTER5_PR_folder_navigation
#bpy.context.window_manager.scatter5.ui
from . windows_settings import SCATTER5_PR_ui

######### PER NODEGROUP

#bpy.context.node_tree.scatter5
from . nodes_settings import SCATTER5_PR_node_group
#bpy.context.node_tree.scatter5.texture
from ..scattering.texture_datablock import SCATTER5_PR_node_texture


# ooooooooo.                        
# `888   `Y88.                      
#  888   .d88'  .ooooo.   .oooooooo 
#  888ooo88P'  d88' `88b 888' `88b  
#  888`88b.    888ooo888 888   888  
#  888  `88b.  888    .o `88bod8P'  
# o888o  o888o `Y8bod8P' `8oooooo.  
#                        d"     YD
#                        "Y88888P'


#Children types children aways first! 
classes = (
            
    SCATTER5_PR_blend_environment_paths,
    SCATTER5_AddonPref,

    SCATTER5_PR_folder_navigation, 
    SCATTER5_PR_library, 
    SCATTER5_PR_ui,
    SCATTER5_PR_Window,

    SCATTER5_PR_node_texture,
    SCATTER5_PR_node_group,

    SCATTER5_PR_manual_brush_tool_default,
    SCATTER5_PR_manual_brush_tool_dot,
    SCATTER5_PR_manual_brush_tool_spatter,
    SCATTER5_PR_manual_brush_tool_pose,
    SCATTER5_PR_manual_brush_tool_path,
    SCATTER5_PR_manual_brush_tool_chain,
    SCATTER5_PR_manual_brush_tool_line,
    SCATTER5_PR_manual_brush_tool_spray,
    SCATTER5_PR_manual_brush_tool_spray_aligned,
    SCATTER5_PR_manual_brush_tool_lasso_fill,
    SCATTER5_PR_manual_brush_tool_clone,
    SCATTER5_PR_manual_brush_tool_eraser,
    SCATTER5_PR_manual_brush_tool_dilute,
    SCATTER5_PR_manual_brush_tool_lasso_eraser,
    # SCATTER5_PR_manual_brush_tool_smooth,
    SCATTER5_PR_manual_brush_tool_move,
    SCATTER5_PR_manual_brush_tool_rotation_set,
    SCATTER5_PR_manual_brush_tool_random_rotation,
    SCATTER5_PR_manual_brush_tool_comb,
    SCATTER5_PR_manual_brush_tool_spin,
    SCATTER5_PR_manual_brush_tool_z_align,
    SCATTER5_PR_manual_brush_tool_scale_set,
    SCATTER5_PR_manual_brush_tool_grow_shrink,
    SCATTER5_PR_manual_brush_tool_object_set,
    SCATTER5_PR_manual_brush_tool_drop_down,
    SCATTER5_PR_manual_brush_tool_free_move,
    SCATTER5_PR_manual_brush_tool_manipulator,
    SCATTER5_PR_manual_brush_tool_attract_repulse,
    SCATTER5_PR_manual_brush_tool_push,
    # SCATTER5_PR_manual_brush_tool_turbulence,
    SCATTER5_PR_manual_brush_tool_gutter_ridge,
    SCATTER5_PR_manual_brush_tool_relax2,
    SCATTER5_PR_manual_brush_tool_turbulence2,
    SCATTER5_PR_manual_brush_tool_heaper,
    SCATTER5_PR_scene_manual,
    
    SCATTER5_PR_export_to_presets,
    SCATTER5_PR_export_to_biome,
    SCATTER5_PR_generate_thumbnail,
    SCATTER5_PR_objects,
    SCATTER5_PR_creation_operators,
    SCATTER5_PR_creation_operator_add_psy_preset,
    SCATTER5_PR_creation_operator_add_psy_density,
    SCATTER5_PR_creation_operator_add_psy_manual,
    SCATTER5_PR_creation_operator_add_psy_modal,
    SCATTER5_PR_creation_operator_load_biome,

    SCATTER5_PR_operators,
    
    SCATTER5_PR_uuids, #LEGACY

    SCATTER5_PR_Scene,
    
    SCATTER5_PR_uuids_repository,
    SCATTER5_PR_channel_members,
    SCATTER5_PR_sync_channels,
    
    SCATTER5_PR_Blend,

    SCATTER5_PR_procedural_vg,
    SCATTER5_PR_particle_systems,
    SCATTER5_PR_particle_groups,
    SCATTER5_PR_particle_interface_items,

    SCATTER5_PR_Object,
    

    )


def all_classes():
    """find all classes loaded in our plugin"""

    import sys, inspect
    ret = set()

    
    for mod_path,mod in sys.modules.copy().items(): #for all modules in sys.modules
        if (".geo_scatter." in mod_path): #filer module that isn't ours (usually module path starts with 'bl_ext.user_default.geo_scatter.')
            for o in mod.__dict__.values(): #for each objects found in module find & return class
                if (inspect.isclass(o)):
                    if (o not in ret): #guarantee unique values
                        ret.add(o)
                        yield o

def all_classes_with_enums():
    """find all classes who detain blender enum properties in their annotation space"""

    for cls in all_classes():
        if (hasattr(cls,"__annotations__")):
            if ("<built-in function EnumProperty>" in [repr(a.function) for a in cls.__annotations__.values() if hasattr(a,"function") ]):
                yield cls

def patch_enum_custom_icons(cls):
    """because properties are defined in __annotation__ space, we cannot get custom icon value as icons are not registered yet
    thus we need to re-sample the icons right before registering the PropertyGroup, this function will patch EnumProperty when needed"""

    #ignore operators, we can't patch them it seems????? might be very problematic if we want operators with custom icons, problem to be resolve me later if needed
    if ("_OT_" in cls.__name__):
        #print("ignored due to being an operator : ",cls)
        return None

    #ignore classes already registered
    if ( (hasattr(cls, "is_registered")) and (cls.is_registered) ):
        #print("ignored due to already being registered : ",cls)
        return None

    def patch_needed(itm):
        """check if this item need to be patched, if the icon element of the item has a patchsignal"""
        return (type(itm[3]) is str) and itm[3].startswith("TOPATCH:")

    def patch_item(itm):
        """patch icon element of an item if needed"""
        if (not patch_needed(itm)):
            return itm
        from .. resources.icons import cust_icon
        return tuple(cust_icon(e.replace("TOPATCH:","")) if (type(e) is str and e.startswith("TOPATCH:")) else e for e in itm)

    #for all props in current class annotation space, &..
    for prop in [ prop for propname,prop in cls.__annotations__.items() 
                  #& if props is EnumProperties Proptype..
                  if (repr(prop.function)=="<built-in function EnumProperty>")
                  #& if items is not a custom items function..
                  and (not callable(prop.keywords["items"]))
                  #& if that have more than 3 element per items, aka contain an icon..
                  and (len(prop.keywords["items"][0])>3)
                  #& have at least one icon value that containing the patch signal
                  and len([itm for itm in prop.keywords["items"] if patch_needed(itm)])
        ]:
        #then we monkey-patch new items tuple w correct icon values
        prop.keywords["items"] = tuple(patch_item(itm) for itm in prop.keywords["items"])
        continue

    return None 

def register():

    #monkey patch all classes with enums & custom icons before registration, before annotation space becomes real properties

    for cls in all_classes_with_enums():
        patch_enum_custom_icons(cls)

    #register classes

    for cls in classes:
        bpy.utils.register_class(cls)
        
    #register special properties operator
    
    bpy.utils.register_class(SCATTER5_OT_export_addon_settings)
    bpy.utils.register_class(SCATTER5_OT_import_addon_settings)

    #register main props 

    bpy.types.Text.scatter5 = bpy.props.PointerProperty(type=SCATTER5_PR_Blend)
    bpy.types.Scene.scatter5 = bpy.props.PointerProperty(type=SCATTER5_PR_Scene)
    bpy.types.Object.scatter5 = bpy.props.PointerProperty(type=SCATTER5_PR_Object)
    bpy.types.WindowManager.scatter5 = bpy.props.PointerProperty(type=SCATTER5_PR_Window)
    bpy.types.NodeTree.scatter5 = bpy.props.PointerProperty(type=SCATTER5_PR_node_group) #TODO: tell me why again we aren't we unregistering nodetrees props?

    #update directories globals with new addon_prefs().library_path
    
    from .. resources.directories import update_scatter_library_location
    update_scatter_library_location()

    return 

def unregister():

    #remove props 

    del bpy.types.Text.scatter5
    del bpy.types.Scene.scatter5
    del bpy.types.Object.scatter5
    del bpy.types.WindowManager.scatter5

    #unregister classes 

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
        
    #register special properties operator
    
    bpy.utils.unregister_class(SCATTER5_OT_export_addon_settings)
    bpy.utils.unregister_class(SCATTER5_OT_import_addon_settings)
     
    return 

#if __name__ == "__main__":
#    register()