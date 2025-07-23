# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import os
import bpy
import re
import sys
import addon_utils
from datetime import datetime
import bpy.utils.previews
import inspect
from bpy.app.handlers import persistent
import requests
import textwrap
#Utils Comment
exceptional_names={'gui':'blender-osm','ape':'blender-osm','mmd_tools_local':'cats-blender-plugin-development'}
item_panels=['VIEW3D_PT_context_properties',]
view_panels=['VIEW3D_PT_view3d_properties','VIEW3D_PT_view3d_lock','VIEW3D_PT_view3d_cursor','VIEW3D_PT_grease_pencil','VIEW3D_PT_collections','NODE_PT_backdrop','NODE_PT_annotation','IMAGE_PT_view_display','IMAGE_PT_uv_cursor','IMAGE_PT_annotation']
tool_panels=['VIEW3D_PT_active_tool','VIEW3D_PT_tools_object_options','VIEW3D_PT_tools_object_options_transform','WORKSPACE_PT_main','WORKSPACE_PT_custom_props','WORKSPACE_PT_addons','NODE_PT_active_tool','IMAGE_PT_active_tool']
options_panels={'NODE_WORLD_PT_viewport_display','NODE_PT_quality','NODE_MATERIAL_PT_viewport','NODE_EEVEE_MATERIAL_PT_settings','NODE_DATA_PT_light','NODE_DATA_PT_EEVEE_light','NODE_CYCLES_WORLD_PT_settings_volume','NODE_CYCLES_WORLD_PT_settings_surface','NODE_CYCLES_WORLD_PT_settings','NODE_CYCLES_WORLD_PT_ray_visibility','NODE_CYCLES_MATERIAL_PT_settings_volume','NODE_CYCLES_MATERIAL_PT_settings_surface','NODE_CYCLES_MATERIAL_PT_settings','NODE_CYCLES_LIGHT_PT_light','NODE_CYCLES_LIGHT_PT_beam_shape'}
node_panels={'TI_OT_Transfer_Panel','BAN_PT_Bake_A_Node','NODE_PT_texture_mapping','NODE_PT_simulation_zone_items','NODE_PT_active_node_properties','NODE_PT_active_node_generic','NODE_PT_active_node_color','NODE_PT_PanelLinkedEdit'}
# addons_with_multiple_tabs={'home_builder':'Home Builder','shino':'Shino','cats-blender':'CATS','auto_rig_pro':'ARP','auto_rig_pro-master':'ARP','auto_rig_pro_master':'ARP','pbr_painter':'PBR Painter','pbr-painter':'PBR Painter'}
addons_with_multiple_tabs={}
LOGGING=True
def get_addon_identifier(package):
    if package.startswith("bl_ext."):
        return ".".join(package.split('.')[:3])
    elif '.' in package:
        return package[:package.index(".")]
    
    return package
def get_package_name(package):
    if package.startswith("bl_ext."):
        return package.split('.')[2]
    if "." in package:
        return package[:package.index(".")]
    return package
def get_correct_module_name(name):
    if name.startswith("bl_ext."):
        return name.split('.')[2]
    return name
def log(*args):
    if LOGGING:
        print(*args)
def preferences():
    return bpy.context.preferences.addons[__package__].preferences
def get_custom_module_name(bl_type,name):
    if preferences().filter_internal_tabs:
        if bl_type.__name__ in view_panels:
            name='View'
            if bl_type.__name__=='VIEW3D_PT_grease_pencil' and preferences().zen_uv_fix:
                name="Zen UV Fix"
        if bl_type.__name__ in item_panels:
            name='Item'
        if bl_type.__name__ in tool_panels:
            name='Tool'
        if bl_type.__name__ in options_panels:
            name='Options'
        if bl_type.__name__ in node_panels:
            name='Node'
    return name
def split_keep_substring(string, separator=',', substrings=('DAZ (.duf, .dsf) importer',)):
    holder=[]
    for sub in substrings:
        if sub in string:
            string=string.replace(sub,'')
            holder.append(sub)
    result=string.split(separator)
    result=[a for a in result if a.strip()]
    return result+holder

    
regex=re.compile("^\s*bl_category\s*=\s*.+")
def change_category(index,remove=False):
    #directory=os.path.dirname(os.path.dirname(__file__))
    directories=[]
    addons=[]
    a=preferences().addon_info_for_renaming[index]
    
    #print(addons)
    addons=[a.name,]
    new_category=a.tab_name
    #print(a.name,a.tab_name)
    for mod in addon_utils.modules():
        if get_correct_module_name(mod.__name__) in addons:
            version=bpy.app.version
            addon_dir_path=os.path.join(os.path.dirname(bpy.app.binary_path),f"{version[0]}.{version[1]}","scripts","addons")
            directories.append(os.path.dirname(mod.__file__) if os.path.dirname(mod.__file__)!=os.path.dirname(os.path.dirname(__file__)) and os.path.dirname(mod.__file__)!=addon_dir_path else mod.__file__)
            
        else:
            pass
    if not os.path.isdir(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),"Addon-Backups-CleanPanels")):
        os.mkdir(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),"Addon-Backups-CleanPanels"))
    for directory in directories:
        if os.path.isfile(directory):
            if not remove and preferences().auto_backup_addons:
                shutil.copy(directory, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),"Addon-Backups-CleanPanels",os.path.splitext(os.path.basename(directory))[0]+str(datetime.now().strftime(r' %d-%m-%Y %H %M'))+os.path.splitext(os.path.basename(directory))[1]))
                print("Creating Backup....\n", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),"Addon-Backups-CleanPanels",os.path.splitext(os.path.basename(directory))[0]+str(datetime.now().strftime(r' %d-%m-%Y %H %M'))+os.path.splitext(os.path.basename(directory))[1]))
            f=directory
            #print(f)
            try:
                data=[]
                with open(f,mode='r') as file:
                    replaced=False
                    while True:
                        line=file.readline()
                        if not line:
                            break
                        if remove:
                            if not "#--changed-by-CleanPanels--" in line:
                                replaced=True
                                data.append(line.replace("#--category-editied-by-CleanPanels--",""))
                            
                        else:
                            
                            match=regex.search(line)
                            if  ("bl_category" in line and new_category in line):
                                data.append(line)
                            else:
                                if "#--changed-by-CleanPanels--" not in line:
                                    
                                    if match:
                                        replaced=True
                                        data.append(line.replace("bl_category","#--category-editied-by-CleanPanels--bl_category"))
                                    else:
                                        data.append(line)
                            if match and not  ("bl_category" in line and new_category in line):
                                print("Replacing :",line)
                                replaced=True
                                data.append(line[:line.index("bl_category")]+f"bl_category='{new_category}'#--changed-by-CleanPanels--\n")
                if data:
                    if replaced:
                        with open(f,mode='w') as file:
                                file.writelines(data)
            except Exception as e:
                log("Error in file",f,'\n',e)
        else:
            #print(directory,os.path.dirname(os.path.dirname(__file__)))
            if directory!=os.path.dirname(os.path.dirname(__file__)):
                
                if not remove and preferences().auto_backup_addons:
                    dest_path=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),"Addon-Backups-CleanPanels",os.path.basename(directory)+str(datetime.now().strftime(r' %d-%m-%Y %H %M')))
                    if not os.path.isdir(dest_path):
                        shutil.copytree(directory, dest_path)
                        print("Creating Backup....\n", dest_path)
                for f in get_all_python_files(directory):
                    #print(f)
                    try:
                        data=[]
                        with open(f,mode='r') as file:
                            replaced=False
                            while True:
                                line=file.readline()
                                if not line:
                                    break
                                if remove:
                                    if not "#--changed-by-CleanPanels--" in line:
                                        replaced=True
                                        data.append(line.replace("#--category-editied-by-CleanPanels--",""))
                                    
                                else:
                                    match=regex.search(line)
                                    if  ("bl_category" in line and new_category in line):
                                        data.append(line)
                                    else:
                                        if "#--changed-by-CleanPanels--" not in line:
                                            
                                            if match:
                                                replaced=True
                                                data.append(line.replace("bl_category","#--category-editied-by-CleanPanels--bl_category"))
                                            else:
                                                data.append(line)
                                    if match and not  ("bl_category" in line and new_category in line):
                                        print("Replacing :",line)
                                        replaced=True
                                        data.append(line[:line.index("bl_category")]+f"bl_category='{new_category}'#--changed-by-CleanPanels--\n")
                        if data:
                            if replaced:
                                with open(f,mode='w') as file:
                                        file.writelines(data)
                    except Exception as e:
                        log("Error in file",f,'\n',e)
def get_installed_addon_names(self, context):
    addons=[]
    for a in bpy.context.preferences.addons.keys():

        try:
            if a not in split_keep_substring(preferences().addons_to_exclude)+addons_to_exclude and a not in split_keep_substring(preferences().workspace_categories[self.index].panels):
                mod = sys.modules[a]
                addons.append(addon_utils.module_bl_info(mod).get('name', "Unknown"))
        except:
            pass
    addons=sorted(addons,key=str.casefold)
    return addons
def get_all_addon_names(self, context):
    addons=[]
    for a in bpy.context.preferences.addons.keys():

        try:
            if a not in split_keep_substring(preferences().addons_to_exclude)+addons_to_exclude:
                mod = sys.modules[a]
                addons.append(addon_utils.module_bl_info(mod).get('name', "Unknown"))
        except:
            pass
    addons=sorted(addons,key=str.casefold)
    return addons
def get_all_addons(self, context):
    addons=[]
    for a in bpy.context.preferences.addons.keys():

        try:
            mod = sys.modules[a]
            a=addon_utils.module_bl_info(mod).get('name', "Unknown")
            if a not in addons_to_exclude+(split_keep_substring(getattr(preferences(),f'addons_to_exclude{self.space}')) if preferences().use_enum_search_for_popups else []):
                
                addons.append((a,a))
                # mod = sys.modules[a]
                # if mod not in preferences().addons_to_exclude)+addons_to_exclude:
                #     addons.append((mod.bl_info.get('name', "Unknown"),mod.bl_info.get('description', "")))
        except:
            pass
    internal_tabs=[]
    if preferences().filter_internal_tabs:
        internal_tabs=[("Tool","Tool"),("View","View"),("Node","Node"),("Options","Options")]
    addons=sorted(addons,key=lambda x:x[0].lower())
    return [(a,a,a) for a,b in addons]+[(a,f"{a}(Tab)",a) for a,b in internal_tabs]+[("Unfiltered","Unfiltered","Unfiltered"),]
def get_installed_addon_names(self, context):
    addons=[]
    for a in bpy.context.preferences.addons.keys():

        try:
            if a not in split_keep_substring(preferences().addons_to_exclude)+addons_to_exclude and a not in split_keep_substring(preferences().workspace_categories[self.index].panels):
                mod = sys.modules[a]
                addons.append(addon_utils.module_bl_info(mod).get('name', "Unknown"))
        except:
            pass
    addons=sorted(addons,key=str.casefold)
    return addons
def is_path_inside(path_a, path_b):
    # Normalize paths to handle different formats and separators
    path_a = os.path.abspath(path_a)
    path_b = os.path.abspath(path_b)
    
    # Check if the paths are on the same drive
    drive_a, tail_a = os.path.splitdrive(path_a)
    drive_b, tail_b = os.path.splitdrive(path_b)
    
    if drive_a != drive_b:
        return False
    
    # Check if path_a is a subdirectory of path_b
    common_path = os.path.commonpath([path_a, path_b])
    
    return common_path == path_b
def get_addons_for_atl(self,context):
    addons=[]
    for a in addon_utils.modules():
        if addon_utils.check(a.__name__)[0]:
            try:
                b=addon_utils.module_bl_info(a).get('name', "Unknown")
                if not hasattr(a,'__path__'):
                    mod_path=a.__file__
                else:
                    mod_path=a.__path__[0]
                if not is_path_inside(mod_path,os.path.dirname(os.path.dirname(os.path.dirname(sys.executable)))) and a!='bl_pkg' and b!='CleanPanels':
                    addons.append((b,get_correct_module_name(a.__name__)))
            except Exception as e:
                print(e)
    # for a in bpy.context.preferences.addons.keys():
    #     try:
    #         mod = sys.modules[a]
    #         b=addon_utils.module_bl_info(mod).get('name', "Unknown")
            
    #         if not hasattr(mod,'__path__'):
    #             mod_path=mod.__file__
    #         else:
    #             mod_path=mod.__path__[0]
    #         if not is_path_inside(mod_path,os.path.dirname(os.path.dirname(os.path.dirname(sys.executable)))) and a!='bl_pkg' and b!='CleanPanels':
    #             addons.append((b,get_correct_module_name(mod.__name__)))
    #     except:
    #         pass
    addons=sorted(addons,key=lambda x:x[0].lower())
    addons= [(b,f"{a}",b,'CHECKMARK' if b in preferences().atl_list else 'NONE',i) for i,(a,b) in enumerate(addons)]
    return addons
def get_installed_addons(self, context):
    addons=[]
    others=[]
    for i,a in enumerate(preferences().addon_loading_categories):
        if i!=self.index:
            others.extend(split_keep_substring(preferences().addon_loading_categories[i].panels))
    # for a in bpy.context.preferences.addons.keys():
    #     try:
    #         mod = sys.modules[a]
    #         a=addon_utils.module_bl_info(mod).get('name', "Unknown")
    #         if a not in addons_to_exclude and a not in (split_keep_substring(preferences().addon_loading_categories[self.index].panels) if preferences().use_enum_search_for_popups else []):
    #             addons.append(a)
    #     except:
    #         pass
    for a in addon_utils.modules():
        if addon_utils.check(a.__name__)[0]:
            try:
                
                if not hasattr(a,'__path__'):
                    mod_path=a.__file__
                else:
                    mod_path=a.__path__[0]
                # if 
                a=addon_utils.module_bl_info(a).get('name', "Unknown")
                if not is_path_inside(mod_path,os.path.dirname(os.path.dirname(os.path.dirname(sys.executable)))) and a not in addons_to_exclude and a not in (split_keep_substring(preferences().addon_loading_categories[self.index].panels) if preferences().use_enum_search_for_popups else []):
                    addons.append(a)
            except Exception as e:
                print(e)
    addons=sorted(addons,key=str.casefold)
    return [(a,a,a,'CHECKMARK' if a in others else 'NONE',i) for i,a in enumerate(addons)]

def get_installed_addons_for_filtering_categories(self, context):
    addons=[]
    others=[]
    for i,a in enumerate(getattr(preferences(),f'workspace_categories{self.space}')):
        if i!=self.index:
            others.extend(split_keep_substring(getattr(preferences(),f'workspace_categories{self.space}')[i].panels))
    others.extend(split_keep_substring(getattr(preferences(),f'addons_to_exclude{self.space}')))
    for a in bpy.context.preferences.addons.keys():
        # print("Key",a)
        try:
            if a not in ['View','Tool','Node','Options']:
                # print([b for b in sys.modules.keys() if "aunch" in b])
                mod = sys.modules[a]
                # print("mod1",mod)
                # print(dir(mod))
                a=addon_utils.module_bl_info(mod).get('name', "Unknown")
                # print("Mod",a)
            if a not in split_keep_substring(getattr(preferences(),f'addons_to_exclude{self.space}'))+addons_to_exclude and a not in (split_keep_substring(getattr(preferences(),f'workspace_categories{self.space}')[self.index].panels) if preferences().use_enum_search_for_popups and not getattr(self,'bl_idname','None')=='CP_OT_enableuncategorized' else []):
                addons.append(a)
                #addons.append(a)
        except:
            pass
    # if preferences().filter_internal_tabs:
    #     addons.append("Tool")
    #     addons.append("View")
    #     addons.append("Node")
    #     addons.append("Options")
    internal_tabs=[]
    if preferences().filter_internal_tabs:
        internal_tabs=["Tool","View","Node","Options"]
    addons=sorted(addons,key=str.casefold)
    return [(a,a+("(Tab)" if a in internal_tabs else ""),a,'CHECKMARK' if a in others else 'NONE',i) for i,a in enumerate(addons+internal_tabs)]+[("All",'All','All'),("Unfiltered","Unfiltered","Unfiltered")]
# def get_module_name_from_addon_name(name):
#     if name in ['Tool','View','Node','Options']:
#          return name
#     for addon in bpy.context.preferences.addons:
#         try:
#             mod = sys.modules[addon.module]
#             addon_name=addon_utils.module_bl_info(mod).get('name', "Unknown")
#             if addon_name==name:
#                 addon=get_package_name(addon.module)
#                 return addon
#         except:
#             pass
#     return "--Unknown--"
ALL_MODULES=addon_utils.modules()
def get_module_name_from_addon_name(name):
    if name in ['Tool','View','Node','Options']:
         return name
    for addon in ALL_MODULES:
        try:
            addon_name=addon_utils.module_bl_info(addon).get('name', "Unknown")
            
            if addon_name==name:
                addon=get_package_name(addon.__name__)
                return addon
            pkg_name=get_package_name(addon.__name__)
            if pkg_name==name:
                return pkg_name
        except:
            pass
    return "--Unknown--"
def get_addon_name_from_module_name(name):
    if name in ['Tool','View','Node','Options']:
         return name
     
    for addon in ALL_MODULES:
        if addon.__name__.startswith("bl_ext."):
            mod_name=addon.__name__.split(".")[2]
            if mod_name==name:
                return addon_utils.module_bl_info(addon).get('name', "Unknown")
        else:
            if addon.__name__==name:
                return addon_utils.module_bl_info(addon).get('name', "Unknown")
    return "--Unknown--"
def get_full_module_name(name):
    for addon in bpy.context.preferences.addons:
        try:
            if get_package_name(addon.module)==name:
                return addon.module
        except:
            pass
    return "--Unknown--"
def get_all_panel_categories(self, context):
    cat=set()
    base_type = bpy.types.Panel
    for typename in dir(bpy.types):
        
        try:
            bl_type = getattr(bpy.types, typename,None)
            if issubclass(bl_type, base_type):
                if getattr(bl_type,'backup_space',"None")=='VIEW_3D' or getattr(bl_type,'bl_space_type',"None")=='VIEW_3D':
                    if getattr(bl_type,'backup_category',None):
                        cat.add(getattr(bl_type,'backup_category',None))
                    if getattr(bl_type,'bl_category',None):
                        cat.add(getattr(bl_type,'bl_category',None))
                    #cat.add(getattr(bl_type,'backup_category',None) if getattr(bl_type,'backup_category',None) else getattr(bl_type,'bl_category',"None"))
        except:
            pass
    cat=[a for a in cat if a!=preferences().holder_tab_name and a!='None']
    cat=sorted(cat)
    return [(a,a,a) for a in cat]
def get_panel_categories_for_favorites(self, context):
    cat=set()
    base_type = bpy.types.Panel
    if preferences().filter_internal_tabs:
            cat.add("Tool")
            cat.add("View")
    for addon in preferences().addon_info_for_renaming:
        if addon.tab_name not in [a.name for a in preferences().favorites]:
            cat.add(addon.tab_name)
    # for typename in dir(bpy.types):
    #     try:
    #         bl_type = getattr(bpy.types, typename,None)
    #         if issubclass(bl_type, base_type):
                
    #             if getattr(bl_type,'backup_space',"None")==preferences().space_type or getattr(bl_type,'bl_space_type',"None")==preferences().space_type:
                    
    #                 if getattr(bl_type,'bl_category',None) and getattr(bl_type,'bl_category',"None") not in [a.name for a in preferences().favorites]:
    #                     cat.add(getattr(bl_type,'bl_category',"None"))
    #                 if getattr(bl_type,'renamed_category',None) and getattr(bl_type,'renamed_category',"None") not in [a.name for a in preferences().favorites]:
    #                     cat.add(getattr(bl_type,'renamed_category',"None"))
    #                 else:
    #                     if getattr(bl_type,'backup_category',None) and getattr(bl_type,'backup_category',"None") not in [a.name for a in preferences().favorites]:
    #                         cat.add(getattr(bl_type,'backup_category',"None"))
                        
    #     except:
    #         pass
    cat=sorted(cat)

    return [(a,a,a) for i,a in enumerate(cat)]
def get_panel_categories(self, context):
    cat=set()
    base_type = bpy.types.Panel
    others=[]
    return_icons=hasattr(self,'return_icons')
    if self.category =='FP':
        if preferences().filter_internal_tabs:
                cat.add("Tool")
                cat.add("View")
        elif preferences().space_type=='NODE_EDITOR':
                cat.add("Node")
                cat.add("Options")
    for typename in dir(bpy.types):
        
        try:
            bl_type = getattr(bpy.types, typename,None)
            if issubclass(bl_type, base_type):
                if self.category=='Dropdown':
                    for i,a in enumerate(preferences().dropdown_categories):
                        if i!=self.index:
                            others.extend(split_keep_substring(preferences().dropdown_categories[i].panels))
                    if getattr(bl_type,'backup_space',"None")=='VIEW_3D' or getattr(bl_type,'bl_space_type',"None")=='VIEW_3D':
                        if getattr(bl_type,'bl_category',None) and getattr(bl_type,'bl_category',"None") not in (split_keep_substring(preferences().dropdown_categories[self.index].panels)  if preferences().use_enum_search_for_popups else []):
                            
                            cat.add(getattr(bl_type,'bl_category',"None"))
                        if getattr(bl_type,'backup_category',None) and  getattr(bl_type,'backup_category',"None") not in (split_keep_substring(preferences().dropdown_categories[self.index].panels) if preferences().use_enum_search_for_popups else []):
                            
                            cat.add(getattr(bl_type,'backup_category',"None"))
                elif self.category =='Pie':
                    for i,a in enumerate(preferences().panel_categories):
                        if i!=self.index:
                            others.extend(split_keep_substring(preferences().panel_categories[i].panels))
                    if getattr(bl_type,'backup_space',"None")=='VIEW_3D' or getattr(bl_type,'bl_space_type',"None")=='VIEW_3D':
                        
                        if getattr(bl_type,'bl_category',None) and getattr(bl_type,'bl_category',"None") not in (split_keep_substring(preferences().panel_categories[self.index].panels ) if preferences().use_enum_search_for_popups else []):
                            cat.add(getattr(bl_type,'bl_category',"None"))
                        if getattr(bl_type,'backup_category',None) and getattr(bl_type,'backup_category',"None") not in (split_keep_substring(preferences().panel_categories[self.index].panels) if preferences().use_enum_search_for_popups else []):
                            cat.add(getattr(bl_type,'backup_category',"None"))
                elif self.category =='FP':
                    for i,a in enumerate(preferences().focus_panel_categories):
                        if i!=self.index:
                            others.extend(split_keep_substring(preferences().focus_panel_categories[i].panels))
                    if getattr(bl_type,'backup_space',"None")==preferences().space_type or getattr(bl_type,'bl_space_type',"None")==preferences().space_type:
                        
                        if getattr(bl_type,'bl_category',None) and getattr(bl_type,'bl_category',"None") not in (split_keep_substring(preferences().focus_panel_categories[self.index].panels) if preferences().use_enum_search_for_popups else []):
                            cat.add(getattr(bl_type,'bl_category',"None"))
                        if getattr(bl_type,'renamed_category',None) and getattr(bl_type,'renamed_category',"None") not in (split_keep_substring(preferences().focus_panel_categories[self.index].panels) if preferences().use_enum_search_for_popups else []):
                            cat.add(getattr(bl_type,'renamed_category',"None"))
                        else:
                            if getattr(bl_type,'backup_category',None) and getattr(bl_type,'backup_category',"None") not in (split_keep_substring(preferences().focus_panel_categories[self.index].panels) if preferences().use_enum_search_for_popups else []):
                                cat.add(getattr(bl_type,'backup_category',"None"))
                        
        except:
            pass
    cat=sorted(cat)

    return [(a,a,a,'CHECKMARK' if a in others and not return_icons else 'NONE',i) for i,a in enumerate(cat)]

#addons_to_exclude=['CleanPanels','io_anim_bvh', 'io_curve_svg', 'io_mesh_ply', 'io_mesh_uv_layout', 'io_mesh_stl', 'io_scene_fbx', 'io_scene_gltf2', 'io_scene_obj', 'io_scene_x3d', 'cycles', 'pose_library','node_wrangler', 'node_arrange', 'node_presets','mesh_looptools', 'development_iskeyfree','development_icon_get','add_curve_extra_objects', 'add_mesh_extra_objects','space_view3d_spacebar_menu', 'development_edit_operator']
# addons_to_exclude=['CleanPanels','io_anim_bvh', 'io_curve_svg', 'io_mesh_ply', 'io_mesh_uv_layout', 'io_mesh_stl', 'io_scene_fbx', 'io_scene_gltf2', 'io_scene_obj', 'io_scene_x3d', 'cycles', 'node_presets', 'development_iskeyfree','development_icon_get','add_curve_extra_objects', 'add_mesh_extra_objects','space_view3d_spacebar_menu', 'development_edit_operator', 'add_camera_rigs','add_curve_sapling', 'add_mesh_BoltFactory', 'add_mesh_discombobulator', 'add_mesh_geodesic_domes', 'blender_id,btrace', 'system_blend_info', 'system_property_chart', 'io_anim_camera', 'io_export_dxf', 'io_export_pc2', 'io_import_BrushSet', 'io_import_dxf', 'io_import_images_as_planes', 'mesh_bsurfaces', 'context_browser', 'io_mesh_atomic', 'io_import_palette', 'io_scene_usdz', 'io_shape_mdd', 'lighting_tri_lights', 'lighting_dynamic_sky', 'mesh_inset', 'ui_translate', 'clouds_generator', 'blender_id', 'btrace', 'curve_assign_shapekey', 'curve_simplify', 'depsgraph_debug', 'sun_position', 'mesh_auto_mirror', 'mesh_f2', 'mesh_snap_utilities_line', 'MSPlugin', 'NodePreview', 'object_fracture_cell', 'object_scatter', 'object_skinify', 'render_copy_settings', 'space_view3d_3d_navigation', 'space_view3d_brush_menus', 'space_view3d_copy_attributes', 'space_view3d_math_vis', 'object_carver', 'object_color_rules', 'render_freestyle_svg', 'render_ui_animation_render', 'space_view3d_modifier_tools', 'space_view3d_pie_menus']
addons_to_exclude=['CleanPanels','bl_pkg','Blender Extensions']
DIRNAME=os.path.dirname(__file__)
if os.path.isfile(os.path.join(DIRNAME,"Addons to exclude.txt")):
    with open(os.path.join(DIRNAME,"Addons to exclude.txt"),newline='\n',encoding='utf-8') as f:
        for a in f.readlines():
            addons_to_exclude.append(a.strip())

# print(addons_to_exclude)
def get_all_python_files(dir_path):
    pyfiles = []
    for path, subdirs, files in os.walk(dir_path):
        for name in files:
            if name.endswith('.py') and os.path.join(path, name)!=__file__:
                pyfiles.append(os.path.join(path, name))
                #print(os.path.join(path, name))
    return pyfiles
import shutil
def get_icons(self, context):
    icons=bpy.types.UILayout.bl_rna.functions[
                "prop"].parameters["icon"].enum_items.keys()
    return [(a,a,a,a,i) for i,a in enumerate(icons)] 
ALL_ICONS_ENUM=get_icons(None,None)
ALL_ICONS=[a for a,_,_,_,_ in get_icons(None,None)]
def clean_all_python_files(remove=False):
    #directory=os.path.dirname(os.path.dirname(__file__))
    directories=[]
    addons=[]
    a=preferences().addon_info[preferences().addon_info_index]
    if remove:
        if a.addons:
            addons.extend(split_keep_substring(a.addons))
    else:
        if a.ordered:
            addons.extend(split_keep_substring(a.ordered))
    #print(addons)
    for mod in addon_utils.modules():
        if get_correct_module_name(mod.__name__) in addons:
            directories.append(os.path.dirname(mod.__file__) if os.path.dirname(mod.__file__)!=os.path.dirname(os.path.dirname(__file__)) else mod.__file__)
            
        else:
            pass
    if not os.path.isdir(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),"Addon-Backups-CleanPanels")):
        os.mkdir(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),"Addon-Backups-CleanPanels"))
    for directory in directories:
        if os.path.isfile(directory):
            if not remove and preferences().auto_backup_addons:
                shutil.copy(directory, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),"Addon-Backups-CleanPanels",os.path.splitext(os.path.basename(directory))[0]+str(datetime.now().strftime(r' %d-%m-%Y %H %M'))+os.path.splitext(os.path.basename(directory))[1]))
                print("Creating Backup....\n", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),"Addon-Backups-CleanPanels",os.path.splitext(os.path.basename(directory))[0]+str(datetime.now().strftime(r' %d-%m-%Y %H %M'))+os.path.splitext(os.path.basename(directory))[1]))
            f=directory
            #print(f)
            try:
                data=[]
                with open(f,mode='r') as file:
                    while True:
                        line=file.readline()
                        if not line:
                            break
                        if remove:
                            data.append(line.replace("#--editied-by-CleanPanels--",""))
                        else:
                            data.append(line.replace("bl_order","#--editied-by-CleanPanels--bl_order"))
                if data:
                    with open(f,mode='w') as file:
                            file.writelines(data)
            except Exception as e:
                log("Error in file",f,'\n',e)
        else:
            #print(directory,os.path.dirname(os.path.dirname(__file__)))
            if directory!=os.path.dirname(os.path.dirname(__file__)):
                if not remove and preferences().auto_backup_addons:
                    dest_path=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),"Addon-Backups-CleanPanels",os.path.basename(directory)+str(datetime.now().strftime(r' %d-%m-%Y %H %M')))
                    if not os.path.isdir(dest_path):
                        shutil.copytree(directory, dest_path)
                        print("Creating Backup....\n", dest_path)
                for f in get_all_python_files(directory):
                    #print(f)
                    try:
                        data=[]
                        with open(f,mode='r') as file:
                            while True:
                                line=file.readline()
                                if not line:
                                    break
                                if remove:
                                    data.append(line.replace("#--editied-by-CleanPanels--",""))
                                else:
                                    data.append(line.replace("bl_order","#--editied-by-CleanPanels--bl_order"))
                        if data:
                            with open(f,mode='w') as file:
                                    file.writelines(data)
                    except Exception as e:
                        log("Error in file",f,'\n',e)
import time
import numpy as np
def sort_panels2(panels,order):
    # st=time.time()
    sorted=[]
    used=[]
    bl_types=[a[1] for a in panels]
    order=[a.replace("\n","") for a in order if a in bl_types]
    for o in order:
        for b,p in panels:
            if p.__name__==o and p not in used:
                used.append(p)
                sorted.append((b,p))
                break
    for b,p in panels:
        if p not in used:
            sorted.append((b,p))
    # print(time.time()-st)        
    return sorted
def sort_by_another_list(source_list,ordered_list):
    keys = { ordered_list[i]: i for i in range(len(ordered_list)) }
    sorted_list = sorted(source_list, key=lambda x: keys[x] if x in keys else len(source_list)+1)   
    return sorted_list
def sort_panels(panels,order):
    order=view_panels+tool_panels+order
    keys = { order[i]: i for i in range(len(order)) }
    sorted_panels = sorted(panels, key=lambda x: keys[x[1].__name__] if x[1].__name__ in keys else len(panels)+1)  
    return sorted_panels
def sort_panels_dropdowns(panels,order):
    keys = { order[i]: i for i in range(len(order)) }
    sorted_panels = sorted(panels, key=lambda x: keys[x[0].__name__] if x[0].__name__ in keys else len(panels)+1)  
    return sorted_panels
def dummy():
    pass
def unregister_panel(c):
    try:
        if hasattr(c,"unregister"):
            og_func=c.unregister
            c.unregister=dummy
            bpy.utils.unregister_class(c)
            c.unregister=og_func
        else:
            bpy.utils.unregister_class(c)
    except:
        pass
def register_panel(c):
    if hasattr(c,"register"):
        og_func=c.register
        c.register=dummy
        bpy.utils.register_class(c)
        c.register=og_func
    else:
        try: 
            bpy.utils.register_class(c,False)
        except:
            bpy.utils.register_class(c)
def draw_dropdowns(self, context):
    if preferences().hide_dropdown_panels or preferences().easy_mode:
        return
    layout_str=repr(self.layout.introspect())
    already_drawn='bpy.ops.cp.popup' in layout_str or "search_dropdown" in layout_str
    if not already_drawn:
        if preferences().use_dropdowns:
            categories=[]
            layout=self.layout.row()
            layout.separator()
            if preferences().show_dropdown_search:
                layout.operator("cp.search_dropdown",icon='VIEWZOOM',text='Search')
            for a in preferences().dropdown_categories:
                    if a.name==context.scene.pap_active_dropdown_category:
                        categories=split_keep_substring(a.panels)
                        categories=[a.strip() for a in categories]
            for a in categories:
                if a:

                    layout.emboss='PULLDOWN_MENU'
                    layout.operator("cp.popupcompletepanel",text=a,icon="DOWNARROW_HLT").name=a
def panel_opened(self, context):
    if context.scene.pap_opened_panels.find(self.name)>=0:
        t=context.scene.pap_opened_panels[context.scene.pap_opened_panels.find(self.name)]
    else:
        t=context.scene.pap_opened_panels.add()
        t.name=self.name
    t.opened_before=True
    t.pap_opened_panels=""
    for i in range(1,39):
        if getattr(self,f"show_panel_{i}",False):
            t.pap_opened_panels=t.pap_opened_panels+","+str(i) if t.pap_opened_panels else str(i)

def get_current_context(context):
    if context.mode=='OBJECT':
        return "objectmode"
    elif context.mode =='EDIT_MESH':
        return "mesh_edit"
    elif context.mode =='EDIT_CURVE':
        return "curve_edit"
    elif context.mode =='EDIT_SURFACE':
        return "surface_edit"
    elif context.mode =='EDIT_TEXT':
        return "text_edit"
    elif context.mode =='SCULPT':
        return "sculpt_mode"
    elif context.mode =='EDIT_ARMATURE':
        return "armature_edit"
    elif context.mode =='EDIT_METABALL':
        return "mball_edit"
    elif context.mode =='EDIT_LATTICE':
        return "lattice_edit"
    elif context.mode =='POSE':
        return "posemode"
    elif context.mode =='PAINT_WEIGHT':
        return "weightpaint"
    elif context.mode =='PAINT_VERTEX':
        return "vertexpaint"
    elif context.mode =='PAINT_TEXTURE':
        return "imagepaint"
    elif context.mode =='PARTICLE':
        return "particlemode"
    else:
        return "None1"
def check_for_injection():
    # version=bpy.app.version
    # if sys.platform=='darwin':
    #     util_file_path=os.path.join(os.path.dirname(os.path.dirname(bpy.app.binary_path)),'Resources',f"{version[0]}.{version[1]}","scripts","modules","addon_utils.py")
    # elif "linux" in sys.platform:
    #         util_file_path=os.path.join(bpy.app.binary_path,f"{version[0]}.{version[1]}","scripts","modules","addon_utils.py")
    # else:
    #     util_file_path=os.path.join(os.path.dirname(bpy.app.binary_path),f"{version[0]}.{version[1]}","scripts","modules","addon_utils.py")
    import addon_utils
    util_file_path=addon_utils.__file__
    if os.path.isfile(util_file_path):
        with open(util_file_path,mode='r') as f:
            text=f.read()
            config_folder_path=Path(bpy.utils.user_resource('SCRIPTS')).parent/"config"
            path=os.path.join(config_folder_path, "CP-config.txt")
            if path in text:
                return True
    return False
def check_for_tracking_injection():
    # version=bpy.app.version
    # if sys.platform=='darwin':
    #     util_file_path=os.path.join(os.path.dirname(os.path.dirname(bpy.app.binary_path)),'Resources',f"{version[0]}.{version[1]}","scripts","modules","bpy","utils","__init__.py")
    # elif "linux" in sys.platform:
    #     util_file_path=os.path.join(bpy.app.binary_path,f"{version[0]}.{version[1]}","scripts","modules","bpy","utils","__init__.py")
    # else:
    #     util_file_path=os.path.join(os.path.dirname(bpy.app.binary_path),f"{version[0]}.{version[1]}","scripts","modules","bpy","utils","__init__.py")
    import bpy.utils
    util_file_path=bpy.utils.__file__
    if os.path.isfile(util_file_path):
        with open(util_file_path,mode='r') as f:
            text=f.read()
            config_folder_path=Path(bpy.utils.user_resource('SCRIPTS')).parent/"config"
            path=os.path.join(config_folder_path, "CP-PanelOrder.txt")
            if path in text:    
                return True
    return False
def check_for_delayed_loading_injection():
    # version=bpy.app.version
    # if sys.platform=='darwin':
    #     util_file_path=os.path.join(os.path.dirname(os.path.dirname(bpy.app.binary_path)),'Resources',f"{version[0]}.{version[1]}","scripts","modules","addon_utils.py")
    # elif "linux" in sys.platform:
    #     util_file_path=os.path.join(bpy.app.binary_path,f"{version[0]}.{version[1]}","scripts","modules","addon_utils.py")
    # else:
    #     util_file_path=os.path.join(os.path.dirname(bpy.app.binary_path),f"{version[0]}.{version[1]}","scripts","modules","addon_utils.py")
    import addon_utils
    util_file_path=addon_utils.__file__
    if os.path.isfile(util_file_path):
        with open(util_file_path,mode='r') as f:
            text=f.read()
            config_folder_path=Path(bpy.utils.user_resource('SCRIPTS')).parent/"config"
            path=os.path.join(config_folder_path, "CP-Addons To Load on Boot.txt")
            
            if f"atl_file=r'{path}'" in text:   
                return True
    return False
def get_module_name(bl_type):
    package_name=inspect.getmodule(bl_type).__name__
    if "." in package_name:
        name=get_package_name(package_name)
    else:
        name=package_name
    if name in exceptional_names.keys():
        name=exceptional_names[name]
    name=get_custom_module_name(bl_type,name)
    return name

def change_panel_category(old_name,new_name,space='VIEW_3D'):
    registered_panels=[]
    for typename in dir(bpy.types):
        
        try:
            bl_type = getattr(bpy.types, typename,None)
            if issubclass(bl_type, bpy.types.Panel):
                package_name=inspect.getmodule(bl_type).__package__ if inspect.getmodule(bl_type).__package__ else inspect.getmodule(bl_type).__name__
                if package_name=='__main__' or package_name=='Brush_Manager':
                    continue
                
                registered_panels.append(bl_type)
                if not getattr(bl_type,'backup_category',None) and getattr(bl_type,'bl_category'):
                    bl_type.backup_category=bl_type.bl_category
        except:
            pass
    config_folder_path=Path(bpy.utils.user_resource('SCRIPTS')).parent/"config"
    config_path=os.path.join(config_folder_path,"CP-PanelOrder.txt")
    order_of_panels=[]
    if os.path.isfile(config_path):
        with open(config_path, mode='r', newline='\n', encoding='utf-8') as file:
            order_of_panels=file.readlines()
    else:
        if os.path.isfile(os.path.join(os.path.dirname(__file__),'CP-PanelOrder.txt')):
            with open(os.path.join(os.path.dirname(__file__),'CP-PanelOrder.txt'), mode='r', newline='\n', encoding='utf-8') as file:
                order_of_panels=file.readlines()
    cleaned_order=[]

    if hasattr(bpy.utils,'panels'):
        if len(getattr(bpy.utils,'panels',[]))>len(order_of_panels):
            order_of_panels=getattr(bpy.utils,'panels',[])
    for o in order_of_panels:
        if o.replace("\n","") not in cleaned_order:
            cleaned_order.append(o.replace("\n",""))
    order_of_panels=cleaned_order
    categories=[]
    for a in split_keep_substring(preferences().addons_to_exclude)+addons_to_exclude:
        try:
            if get_module_name_from_addon_name(a)!='--Unknown--':
                categories.append(get_module_name_from_addon_name(a))
        except:
            pass
    for index,a in enumerate(preferences().workspace_categories):
        if getattr(preferences().categories,f'enabled_{index}',False):
            #if a.name==context.workspace.pap_active_workspace_category:
                #categories_string= ''.join(a.panels.split())
                categories_string=split_keep_substring(a.panels)
                #categories.extend([a.strip() for a in categories_string])
                categories.extend([get_module_name_from_addon_name(a) for a in categories_string])
    panels_to_reregister=[]
    parents=[]
    children=[]
    parents_to_move_back=[]
    children_to_move_back=[]
    panels_to_move_back=[]
    for bl_type in registered_panels:
        try:
            package_name=inspect.getmodule(bl_type).__package__ if inspect.getmodule(bl_type).__package__ else inspect.getmodule(bl_type).__name__
            if "." in package_name:
                name=get_package_name(package_name)
            else:
                name=package_name
            if name in exceptional_names.keys():
                name=exceptional_names[name]
            name=get_custom_module_name(bl_type,name)
            try:
                is_panel=False
                try:
                    is_panel=issubclass(bl_type, bpy.types.Panel)
                except:
                    pass                    
                if bl_type and is_panel:
                    if (getattr(bl_type,'bl_category',None) and getattr(bl_type,'backup_space',None)==space and getattr(bl_type,"backup_region","None")=='UI' ) and not getattr(bl_type,'bl_parent_id',None):
                        package_name=inspect.getmodule(bl_type).__package__ if inspect.getmodule(bl_type).__package__ else inspect.getmodule(bl_type).__name__
                        if "." in package_name:
                            name=get_package_name(package_name)
                        else:
                            name=package_name
                        if name in exceptional_names.keys():
                            name=exceptional_names[name]
                        name=get_custom_module_name(bl_type,name)
                        if name!="bl_ui":
                            
                            if getattr(bl_type,'bl_category',None)==old_name or(getattr(bl_type,'bl_category',None)==preferences().holder_tab_name and getattr(bl_type,'renamed_category',None)==old_name):
                                #bl_type.bl_category=bl_type.backup_category if getattr(bl_type,'backup_category',None) else bl_type.bl_category
                                
                                #print(bl_type,getattr(bl_type,'backup_category',None))
                                panels_to_reregister.append((name,bl_type))
                                
                            else:
                                if  getattr(bl_type,'bl_category',None)=='Focused':
                                    panels_to_move_back.append((name,bl_type))
                            # unregister_panel(bl_type)  
                            # bpy.utils.register_class(bl_type)
                    else:
                        if bl_type and getattr(bl_type,'bl_parent_id',None):
                            package_name=inspect.getmodule(bl_type).__package__ if inspect.getmodule(bl_type).__package__ else inspect.getmodule(bl_type).__name__
                            if "." in package_name:
                                name=get_package_name(package_name)
                            else:
                                name=package_name
                            name=get_custom_module_name(bl_type,name)
                            if name in exceptional_names.keys():
                                        name=exceptional_names[name]
                            if name!="bl_ui":
                                if getattr(bl_type,'bl_category',None)==old_name or(getattr(bl_type,'renamed_category',None)==old_name):
                                    pass
                                    #bl_type.bl_category=bl_type.backup_category if getattr(bl_type,'backup_category',None) else bl_type.bl_category
                                    #print(bl_type,getattr(bl_type,'backup_category',None))
                                    parents.append(bl_type.bl_parent_id)
                                    children.append((name,bl_type))
                                    # unregister_panel(bl_type)  
                                    # bpy.utils.register_class(bl_type)
                                else:
                                    if getattr(bl_type,'bl_category',None)=='Focused' :
                                        parents_to_move_back.append(bl_type.bl_parent_id)
                                        children_to_move_back.append((name,bl_type))
            except Exception as e:
                #pass
                print(e)
        except:
            pass
    panels_to_reregister=sort_panels(panels_to_reregister,order_of_panels)
    children=sort_panels(children,order_of_panels)
    children=sort_panels_by_dependency(children,panels_to_reregister)
    # children=sorted(children,key=lambda x:getattr(x[1],'bl_parent_id','Temp') in [getattr(a[1],'bl_idname','None') for a in children])
    # print("")
    # print("")
    # print("")
    # print("")
    # print(children,"Children")
    # for c in children:
    #      print(getattr(c,'bl_category',None))
    # print("")
    # print("")
    
    # print(panels_to_move_back)
    for name,p in panels_to_reregister:
        if getattr(p,'backup_space',None)!=None and getattr(p,'backup_region',None)!=None:
            p.bl_space_type=p.backup_space
            p.bl_region_type=p.backup_region
        if not getattr(p,'backup_category',None):
            p.backup_category=p.bl_category
        if getattr(p,'backup_order',None)!=None:
                                p.bl_order=getattr(p,'backup_order')
        p.bl_category=new_name

        try:
            unregister_panel(p)  
            register_panel(p)
        except Exception as e:
            print(e)
    for name,c in children:
        if getattr(c,'backup_space',None)!=None and getattr(c,'backup_region',None)!=None:
            c.bl_space_type=c.backup_space
            c.bl_region_type=c.backup_region
        if getattr(c,'backup_order',None)!=None:
                                c.bl_order=getattr(c,'backup_order')
        if getattr(c,'bl_category',None):
            if not getattr(c,'backup_category',None):
                c.backup_category=c.bl_category
        c.bl_category=new_name
        try:
            if c.bl_parent_id in parents:
                unregister_panel(c)  
                register_panel(c)
        except Exception as e:
                    print(e)
    for name,c in children:
        if getattr(c,'backup_space',None)!=None and getattr(c,'backup_region',None)!=None:
            c.bl_space_type=c.backup_space
            c.bl_region_type=c.backup_region
        if getattr(c,'backup_order',None)!=None:
                                c.bl_order=getattr(c,'backup_order')
        if getattr(c,'bl_category',None):
            if not getattr(c,'backup_category',None):
                c.backup_category=c.bl_category
        c.bl_category=new_name
        try:
            if c.bl_parent_id not in parents:
                unregister_panel(c)  
                register_panel(c)
        except Exception as e:
                    print(e)
    for name,p in panels_to_move_back:
        if name in categories or name.replace("ender-","") in categories:
            if preferences().addon_info_for_renaming.find(name)>=0:
                if getattr(p,'bl_category'):
                    if not getattr(p,'backup_category',None):
                        p.backup_category=p.bl_category
                if getattr(p,'backup_order',None)!=None:
                                p.bl_order=getattr(p,'backup_order')
                p.bl_category=preferences().addon_info_for_renaming[preferences().addon_info_for_renaming.find(name)].tab_name
                p.renamed_category=p.bl_category
            else:
                if getattr(p,'backup_category',None):   
                    p.bl_category=getattr(p,'backup_category',None)
        else:
            p.bl_category=preferences().holder_tab_name
            if getattr(p,'backup_order',None)!=None:
                                p.bl_order=getattr(p,'backup_order')
        try:
            unregister_panel(p)  
            register_panel(p)
        except Exception as e:
            print(e)
    for name,c in children_to_move_back:
                if preferences().addon_info_for_renaming.find(name)>=0:
                    if getattr(c,'bl_category',None):
                        if not getattr(c,'backup_category',None):
                            c.backup_category=c.bl_category
                    if getattr(c,'backup_order',None)!=None:
                                c.bl_order=getattr(c,'backup_order')
                    c.bl_category=preferences().addon_info_for_renaming[preferences().addon_info_for_renaming.find(name)].tab_name
                    c.renamed_category=c.bl_category
                else:
                    if getattr(c,'backup_category',None):   
                        c.bl_category=getattr(c,'backup_category',None)
                try:
                    if c.bl_parent_id in parents_to_move_back:
                        unregister_panel(c)  
                        register_panel(c)
                except Exception as e:
                            print(e)

    for name,c in children_to_move_back:
        if preferences().addon_info_for_renaming.find(name)>=0:
            if getattr(c,'bl_category',None):
                if not getattr(c,'backup_category',None):
                    c.backup_category=c.bl_category
            if getattr(c,'backup_order',None)!=None:
                                c.bl_order=getattr(c,'backup_order')
            c.bl_category=preferences().addon_info_for_renaming[preferences().addon_info_for_renaming.find(name)].tab_name
            c.renamed_category=c.bl_category
        else:
                if getattr(c,'backup_category',None):   
                    c.bl_category=getattr(c,'backup_category',None)
        try:
            if c.bl_parent_id not in parents_to_move_back:
                unregister_panel(c)  
                register_panel(c)
        except Exception as e:
                    print(e)
icon_collection = {}
def load_icons(only_custom=False):
    
    global icon_collection
    if "icons" in icon_collection.keys():
        pcoll=icon_collection["icons"]
    else:
        pcoll = bpy.utils.previews.new()
    loaded_icons=[]
    if not only_custom:
        my_icons_dir = os.path.join(os.path.dirname(__file__), "icons")
        for file in os.listdir(my_icons_dir):
            icon_name=os.path.splitext(file)[0].lower()
            if icon_name not in pcoll.keys():
                pcoll.load(icon_name, os.path.join(my_icons_dir, file), 'IMAGE')
    custom_icons_dir=preferences().custom_icons_dir
    if os.path.isdir(custom_icons_dir):
        for file in os.listdir(custom_icons_dir):
            if file.endswith('.png'):
                icon_name=os.path.splitext(file)[0].lower()
                if icon_name not in pcoll.keys():
                    pcoll.load(icon_name, os.path.join(custom_icons_dir, file), 'IMAGE')
    # pcoll.load("youtube", os.path.join(my_icons_dir, "Youtube.png"), 'IMAGE')
    # pcoll.load("discord", os.path.join(my_icons_dir, "Discord.png"), 'IMAGE')
    # pcoll.load("updatered", os.path.join(my_icons_dir, "updatered.png"), 'IMAGE')
    # pcoll.load("updategreen", os.path.join(my_icons_dir, "updategreen.png"), 'IMAGE')
    # pcoll.load("city", os.path.join(my_icons_dir, "City.png"), 'IMAGE')
    # pcoll.load("landscape", os.path.join(my_icons_dir, "landscape.png"), 'IMAGE')
    # pcoll.load("animal", os.path.join(my_icons_dir, "Animal.png"), 'IMAGE')
    # pcoll.load("tree", os.path.join(my_icons_dir, "Tree.png"), 'IMAGE')
    # pcoll.load("car", os.path.join(my_icons_dir, "Car.png"), 'IMAGE')
    # pcoll.load("transport", os.path.join(my_icons_dir, "Transport.png"), 'IMAGE')
    # pcoll.load("truck", os.path.join(my_icons_dir, "Truck.png"), 'IMAGE')
    # pcoll.load("reorder", os.path.join(my_icons_dir, "Reorder.png"), 'IMAGE')
    icon_collection["icons"] = pcoll
prefs_to_save = {'use_enum_search_for_popups':'bool',
     'filter_internal_tabs':'bool',
     'favorites':'pc',
                 'panel_categories':'pc',
                 'pop_out_style':'str',
                 'dropdown_categories':'pc',
                 'workspace_categories':'pc',
                 'focus_panel_categories':'pc',
                 'addons_to_exclude':'str',
                 
                 'addon_info':'order',
                 'addon_info_for_renaming':'order',

                 'workspace_categories_image_editor':'pc',
                 'focus_panel_categories_image_editor':'pc',
                 'addons_to_exclude_image_editor':'str',
                 
                 'addon_info_image_editor':'order',
                 'addon_info_for_renaming_image_editor':'order',

                 'workspace_categories_node_editor':'pc',
                 'focus_panel_categories_node_editor':'pc',
                 'addons_to_exclude_node_editor':'str',
                 
                 'addon_info_node_editor':'order',
                 'addon_info_for_renaming_node_editor':'order',

                 'draw_side':'str',
                 'addon_desc_info':'order',
                 'experimental':'bool',
                 'use_sticky_popup':'bool',
                 'columm_layout_for_popup':'str',
                 'use_verticle_menu':'bool',
                 'dropdown_width':'int',
                 'show_dropdown_search':'bool',
                 'auto_backup_addons':'bool',
                 'filtering_method':'str',
                 'show_advanced':'bool',
                 'use_dropdowns':'bool',
                 'sort_per_category':'bool',
                 'holder_tab_name':'str',
                 'custom_icons_dir':'str',
                 'sort_focus_menu_based_on_clicks':'bool',
                 'only_show_unfiltered_panels':'bool',
                 'filtering_per_workspace':'bool',
                 'show_delete_buttons_in_quick_settings':'bool',
                 'move_dropdowns_to_toolbar':'bool',
                 'atl_list':'str',
                 'zen_uv_fix':'bool',
                 
                 
}
def savePreferences(self=None,context=None):
    pcoll=icon_collection["icons"]
    if hasattr(self,'icon'):
        if self.icon not in ALL_ICONS+list(pcoll.keys()):
            # print("Icon not found",self.icon)
            self.icon='COLLAPSEMENU'
    savePreferencesToPath()
    
def read_time_from_file(filename):
    with open(filename, 'r') as file:
        return file.read().strip()
def save_time_to_file(filename, time_str):
    with open(filename, 'w+') as file:
        file.write(time_str)
def create_backup_configs():
    if len(preferences().panel_categories)>0 or len(preferences().dropdown_categories)>0 or len(preferences().focus_panel_categories)>0 or len(preferences().workspace_categories)>0:
        current_time_iso=datetime.now().isoformat()
        if os.path.exists(os.path.join(os.path.dirname(__file__),"last_backup.txt")):
            try:
                last_time=read_time_from_file(os.path.join(os.path.dirname(__file__),"last_backup.txt"))
                current_time_dt = datetime.fromisoformat(current_time_iso)
                time_from_file_dt = datetime.fromisoformat(last_time)
                if abs((current_time_dt-time_from_file_dt).days)<7:
                    return
            except:
                pass
        try:
            save_time_to_file(os.path.join(os.path.dirname(__file__),"last_backup.txt"),current_time_iso)
        except Exception:
            pass
        savePreferencesToPath(True)
def savePreferencesToPathOld(backup=False):
    config_folder_path=Path(bpy.utils.user_resource('SCRIPTS')).parent/"config"
    config_file_path=os.path.join(config_folder_path, "CP-config.txt")
    atl_file_path=os.path.join(config_folder_path, "CP-Addons To Load on Boot.txt")
    if backup:
         config_folder_path=os.path.join(config_folder_path,"CP-Backups")
         config_file_path=os.path.join(config_folder_path, f"CP-config-{str(datetime.now().strftime(r' %d-%m-%Y %H %M'))}.txt")
    if not os.path.isdir(config_folder_path):
        os.makedirs(config_folder_path)
    with open(atl_file_path, mode='w+', newline='\n', encoding='utf-8') as file:
        for line in preferences().atl_list.split(","):
            file.write(f"{line}\n")
    with open(config_file_path, mode='w+', newline='\n', encoding='utf-8') as file:
        for p, t in prefs_to_save.items():
            if p == 'favorites':
                for s in preferences().favorites:
                    file.write(
                        f"{p}=>{t}==={s.name}>>{s.panels}\n")
            elif p == 'panel_categories':
                for s in preferences().panel_categories:
                    file.write(
                        f"{p}=>{t}==={s.name}>>{s.panels}\n")
            elif p == 'dropdown_categories':
                for s in preferences().dropdown_categories:
                    file.write(
                        f"{p}=>{t}==={s.name}>>{s.panels}\n")
            elif p == 'focus_panel_categories':
                for s in preferences().focus_panel_categories:
                    file.write(
                        f"{p}=>{t}==={s.name}>>{s.panels}\n")
            elif p == 'workspace_categories':
                for s in preferences().workspace_categories:
                    file.write(
                        f"{p}=>{t}==={s.name}>>{s.panels}===Icon=>{s.icon}\n")
            elif p == 'addon_info':
                for s in preferences().addon_info:
                    file.write(
                        f"{p}=>{t}==={s.name}>>{s.addons}===Ordered=>{s.ordered}\n")
            elif p == 'addon_info_for_renaming':
                for s in preferences().addon_info_for_renaming:
                    file.write(
                        f"{p}=>{t}==={s.name}>>{s.tab_name}\n")
            elif p == 'focus_panel_categories_node_editor':
                for s in preferences().focus_panel_categories_node_editor:
                    file.write(
                        f"{p}=>{t}==={s.name}>>{s.panels}\n")
            elif p == 'workspace_categories_node_editor':
                for s in preferences().workspace_categories_node_editor:
                    file.write(
                        f"{p}=>{t}==={s.name}>>{s.panels}===Icon=>{s.icon}\n")
            elif p == 'addon_info_node_editor':
                for s in preferences().addon_info_node_editor:
                    file.write(
                        f"{p}=>{t}==={s.name}>>{s.addons}===Ordered=>{s.ordered}\n")
            elif p == 'addon_info_for_renaming_node_editor':
                for s in preferences().addon_info_for_renaming_node_editor:
                    file.write(
                        f"{p}=>{t}==={s.name}>>{s.tab_name}\n")
            elif p == 'focus_panel_categories_image_editor':
                for s in preferences().focus_panel_categories_image_editor:
                    file.write(
                        f"{p}=>{t}==={s.name}>>{s.panels}\n")
            elif p == 'workspace_categories_image_editor':
                for s in preferences().workspace_categories_image_editor:
                    file.write(
                        f"{p}=>{t}==={s.name}>>{s.panels}===Icon=>{s.icon}\n")
            elif p == 'addon_info_image_editor':
                for s in preferences().addon_info_image_editor:
                    file.write(
                        f"{p}=>{t}==={s.name}>>{s.addons}===Ordered=>{s.ordered}\n")
            elif p == 'addon_info_for_renaming_image_editor':
                for s in preferences().addon_info_for_renaming_image_editor:
                    file.write(
                        f"{p}=>{t}==={s.name}>>{s.tab_name}\n")
            elif p == 'addon_desc_info':
                for s in preferences().addon_desc_info:
                    file.write(
                        f"{p}=>{t}==={s.name}>>{s.desc}\n")
            else:
                file.write(f"{p}=>{t}==={getattr(preferences(),p)}\n")
        order=[]
        for a in preferences().addon_info:
            order.extend(split_keep_substring(a.addons))
        #print(order)
        file.write("addon_order=>order===Category>>"+",".join(order)+"\n")

@persistent
def loadPreferencesOld(a=None,b=None):
    config_folder_path=Path(bpy.utils.user_resource('SCRIPTS')).parent/"config"
    all_icons=ALL_ICONS+list(icon_collection["icons"].keys())
    if not os.path.isdir(config_folder_path):
        os.makedirs(config_folder_path)
    if os.path.isfile(os.path.join(config_folder_path, "CP-config.txt")):
        with open(os.path.join(config_folder_path, "CP-config.txt"), mode='r', newline='\n', encoding='utf-8') as file:
            prefs = file.readlines()
            reset_preferences()
            for p in prefs:
                try:
                    attr = p[:p.index("=>")]
                    type = p[p.index("=>")+2:p.index("===")]
                    value = p[p.index("===")+3:]
                    value = value.replace("\n", "")
                    if attr =='favorites' and type=='pc':
                        
                        # value=value.replace("[","").replace("]","")
                        name=value[:value.index(">>")]
                        panels=value[value.index(">>")+2:]
                        pc=preferences().favorites.add()
                        pc.name=name
                        pc.panels=panels
                    if attr =='panel_categories' and type=='pc':
                        
                        # value=value.replace("[","").replace("]","")
                        name=value[:value.index(">>")]
                        panels=value[value.index(">>")+2:]
                        pc=preferences().panel_categories.add()
                        pc.name=name
                        pc.panels=panels
                    elif attr =='dropdown_categories' and type=='pc':
                        
                        # value=value.replace("[","").replace("]","")
                        name=value[:value.index(">>")]
                        panels=value[value.index(">>")+2:]
                        pc=preferences().dropdown_categories.add()
                        pc.name=name
                        pc.panels=panels
                    elif attr =='focus_panel_categories' and type=='pc':
                        
                        # value=value.replace("[","").replace("]","")
                        name=value[:value.index(">>")]
                        panels=value[value.index(">>")+2:]
                        pc=preferences().focus_panel_categories.add()
                        pc.name=name
                        pc.panels=panels
                    elif attr =='workspace_categories' and type=='pc':
                        
                        # value=value.replace("[","").replace("]","")
                        name=value[:value.index(">>")]
                        panels=value[value.index(">>")+2:value.index("Icon=>")-3]
                        icon=value[value.index("Icon=>")+6:]
                        pc=preferences().workspace_categories.add()
                        pc.name=name
                        pc.panels=panels
                        pc.icon=icon if icon in all_icons else 'NONE'
                    elif attr =='addon_info' and type=='order':
                        
                        # value=value.replace("[","").replace("]","")
                        name=value[:value.index(">>")]
                        addons=value[value.index(">>")+2:value.index("Ordered=>")-3]
                        ordered=value[value.index("Ordered=>")+9:]
                        pc=preferences().addon_info.add()
                        pc.name=name
                        pc.addons=addons
                        pc.ordered=ordered
                    elif attr =='addon_info_for_renaming' and type=='order':
                        
                        # value=value.replace("[","").replace("]","")
                        name=value[:value.index(">>")]
                        tab_name=value[value.index(">>")+2:]
                        pc=preferences().addon_info_for_renaming.add()
                        pc.name=name
                        pc.tab_name=tab_name
                    elif attr =='focus_panel_categories_image_editor' and type=='pc':
                        
                        # value=value.replace("[","").replace("]","")
                        name=value[:value.index(">>")]
                        panels=value[value.index(">>")+2:]
                        pc=preferences().focus_panel_categories_image_editor.add()
                        pc.name=name
                        pc.panels=panels
                    elif attr =='workspace_categories_image_editor' and type=='pc':
                        
                        # value=value.replace("[","").replace("]","")
                        name=value[:value.index(">>")]
                        panels=value[value.index(">>")+2:value.index("Icon=>")-3]
                        icon=value[value.index("Icon=>")+6:]
                        pc=preferences().workspace_categories_image_editor.add()
                        pc.name=name
                        pc.panels=panels
                        pc.icon=icon if icon in all_icons else 'NONE'
                    elif attr =='addon_info_image_editor' and type=='order':
                        
                        # value=value.replace("[","").replace("]","")
                        name=value[:value.index(">>")]
                        addons=value[value.index(">>")+2:value.index("Ordered=>")-3]
                        ordered=value[value.index("Ordered=>")+9:]
                        pc=preferences().addon_info_image_editor.add()
                        pc.name=name
                        pc.addons=addons
                        pc.ordered=ordered
                    elif attr =='addon_info_for_renaming_image_editor' and type=='order':
                        
                        # value=value.replace("[","").replace("]","")
                        name=value[:value.index(">>")]
                        tab_name=value[value.index(">>")+2:]
                        pc=preferences().addon_info_for_renaming_image_editor.add()
                        pc.name=name
                        pc.tab_name=tab_name
                    elif attr =='focus_panel_categories_node_editor' and type=='pc':
                        
                        # value=value.replace("[","").replace("]","")
                        name=value[:value.index(">>")]
                        panels=value[value.index(">>")+2:]
                        pc=preferences().focus_panel_categories_node_editor.add()
                        pc.name=name
                        pc.panels=panels
                    elif attr =='workspace_categories_node_editor' and type=='pc':
                        
                        # value=value.replace("[","").replace("]","")
                        name=value[:value.index(">>")]
                        panels=value[value.index(">>")+2:value.index("Icon=>")-3]
                        icon=value[value.index("Icon=>")+6:]
                        pc=preferences().workspace_categories_node_editor.add()
                        pc.name=name
                        pc.panels=panels
                        pc.icon=icon if icon in all_icons else 'NONE'
                    elif attr =='addon_info_node_editor' and type=='order':
                        
                        # value=value.replace("[","").replace("]","")
                        name=value[:value.index(">>")]
                        addons=value[value.index(">>")+2:value.index("Ordered=>")-3]
                        ordered=value[value.index("Ordered=>")+9:]
                        pc=preferences().addon_info_node_editor.add()
                        pc.name=name
                        pc.addons=addons
                        pc.ordered=ordered
                    elif attr =='addon_info_for_renaming_node_editor' and type=='order':
                        
                        # value=value.replace("[","").replace("]","")
                        name=value[:value.index(">>")]
                        tab_name=value[value.index(">>")+2:]
                        pc=preferences().addon_info_for_renaming_node_editor.add()
                        pc.name=name
                        pc.tab_name=tab_name
                    elif attr =='addon_desc_info':
                        
                        # value=value.replace("[","").replace("]","")
                        name=value[:value.index(">>")]
                        desc=value[value.index(">>")+2:]
                        pc=preferences().addon_desc_info.add()
                        pc.name=name
                        pc.desc=desc
                    elif type=='bool' or type=='int':
                        setattr(preferences(), attr, eval(value))
                    
                    else:
                        
                        setattr(preferences(), attr, value)
                    
                except Exception as e:
                    pass
        setattr(preferences(), 'injected_code', check_for_injection())
        setattr(preferences(), 'injected_code_tracking', check_for_tracking_injection())
        setattr(preferences(), 'delayed_loading_code_injected', check_for_delayed_loading_injection())
        # setattr(preferences(),'delayed_addons_loaded',False)

def reset_preferences():
    preferences().favorites.clear()
    preferences().panel_categories.clear()
    preferences().dropdown_categories.clear()
    preferences().focus_panel_categories.clear()
    preferences().workspace_categories.clear()
    preferences().addon_info.clear()
    preferences().addon_info_for_renaming.clear()
    preferences().focus_panel_categories_node_editor.clear()
    preferences().workspace_categories_node_editor.clear()
    preferences().addon_info_node_editor.clear()
    preferences().addon_info_for_renaming_node_editor.clear()
    preferences().focus_panel_categories_image_editor.clear()
    preferences().workspace_categories_image_editor.clear()
    preferences().addon_info_image_editor.clear()
    preferences().addon_info_for_renaming_image_editor.clear()
    preferences().addon_desc_info.clear()
    preferences().addons_to_exclude=""
    preferences().addons_to_exclude_image_editor=""
    preferences().addons_to_exclude_node_editor=""
    
import json
from collections.abc import Iterable
from pathlib import Path
def is_sequence(value):
    return isinstance(value, Iterable) and not isinstance(value, (str, bytes))


def property_group_to_dict(property_group):
    result = {}
    #    print("PPP",property_group)
    for key in property_group.rna_type.properties[2:]:
        #        print(key.type,key.identifier,key.is_readonly)
        try:
            if key.identifier not in {
                "rna_type",
            }:
                if not key.identifier.startswith("__"):
                    value = getattr(property_group, key.identifier)
                    if key.type == "POINTER":
                        result[key.identifier] = property_group_to_dict(value)
                    elif key.type == "COLLECTION":
                        result[key.identifier] = [
                            property_group_to_dict(item) for item in value
                        ]
                    else:
                        if is_sequence(value):
                            result[key.identifier] = value[:]
                        else:
                            if key.type in ["BOOL", "FLOAT", "INT"]:
                                # print(key.identifier,value)
                                if key.subtype in ["EULER", "XYZ_LENGTH"]:
                                    # print([value.x,value.y,value.z])
                                    result[key.identifier] = [value.x, value.y, value.z]
                                elif key.subtype in [
                                    "QUATERNION",
                                ]:
                                    # print([value.w,value.x,value.y,value.z])
                                    result[key.identifier] = [
                                        value.w,
                                        value.x,
                                        value.y,
                                        value.z,
                                    ]
                                else:
                                    result[key.identifier] = value
                            else:
                                result[key.identifier] = value
        except Exception as e:
            print(e)
    # print(result)
    return result


def save_property_group_to_json(property_group, file_path):
    property_dict = property_group_to_dict(property_group)
    #    print(property_dict)
    with open(file_path, "w+") as json_file:
        json.dump(property_dict, json_file, indent=4)
    

def dict_to_property_group(property_group, property_dict,to_skip=[]):
    for key, value in property_dict.items():
        if key not in [
            "rna_type",
        ]+to_skip:
            
            if isinstance(value, dict):
                # print(key,value)
                dict_to_property_group(getattr(property_group, key), value)
            elif isinstance(value,list):
                eval(f"property_group.{key}.clear()")
                for a in value:
                    try:
                        t=eval(f"property_group.{key}.add()")
                    except Exception:
                        break
                    
                    dict_to_property_group(t,a)
            else:
                if hasattr(property_group, key):
                    try:
                        setattr(property_group, key, value)
                    except Exception:
                        pass


def load_property_group_from_json(property_group, file_path,to_skip=[]):
    with open(file_path) as json_file:
        property_dict = json.load(json_file)
    # for key, value in property_dict.items():
    dict_to_property_group(property_group, property_dict,to_skip=to_skip)


def savePreferencesToPath(backup=False):
    config_folder_path=Path(bpy.utils.user_resource('SCRIPTS')).parent/"config"
    if not os.path.isdir(config_folder_path):
        os.makedirs(config_folder_path)
    json_path = config_folder_path / "CP-Config.json"
    if backup:
        backup_dir=config_folder_path / "CP-Backups"
        if not os.path.isdir(backup_dir):
            os.makedirs(backup_dir)
        json_path = config_folder_path / "CP-Backups" / f"CP-config-{str(datetime.now().strftime(r' %d-%m-%Y %H %M'))}.json"
        
    atl_file_path=os.path.join(config_folder_path, "CP-Addons To Load on Boot.txt")
    with open(atl_file_path, mode='w+', newline='\n', encoding='utf-8') as file:
        for line in preferences().atl_list.split(","):
            # print("True-Terrain",get_module_name_from_addon_name(line))
            module=get_module_name_from_addon_name(line)
            file.write(f"{module}\n")
    save_property_group_to_json(preferences(), json_path)
def loadPreferences(a=None,b=None):
    config_folder_path=Path(bpy.utils.user_resource('SCRIPTS')).parent/"config"
    if not os.path.isdir(config_folder_path):
        os.makedirs(config_folder_path)
    json_path = config_folder_path / "CP-Config.json"
    backup_dir=config_folder_path / "CP-Backups"
    # print(json_path)
    if json_path.exists():
        try:
            load_property_group_from_json(preferences(), json_path,to_skip=['delayed_addons_loaded','check_for_updates'])
            
        except:
            preferences().config_corrupted=True
            backup_files = sorted(
                backup_dir.glob("*.json"),
                key=lambda f: f.stat().st_mtime,
                reverse=True
            )
            for backup_file in backup_files:
                try:
                    load_property_group_from_json(preferences(), backup_file,to_skip=['delayed_addons_loaded','check_for_updates'])
                    print("Config File Corrupted. Loading from backup",backup_file)
                    break
                except:
                    pass
    else:
        loadPreferencesOld()
    setattr(preferences(), 'injected_code', check_for_injection())
    setattr(preferences(), 'injected_code_tracking', check_for_tracking_injection())
    setattr(preferences(), 'delayed_loading_code_injected', check_for_delayed_loading_injection())
    update_multitab_addons()
    # if preferences().auto_run_magic_setup:
    #     magic_setup()
def remove_duplicates(list):
    result=[]
    for a in list:
        if a not in result:
            result.append(a)
    return result

def sort_panels_by_dependency(panels, top_level_panels):
    graph = {}
    visited = set()
    temp_mark = set()
    sorted_panels = []
    panel_dict = {panel_class: (module_name, panel_class) for module_name, panel_class in panels+top_level_panels}

    # Build the dependency graph
    for module_name, panel_class in panels:
        bl_parent_id = getattr(panel_class, "bl_parent_id", None)
        if bl_parent_id:
            # Find the parent panel by `bl_idname`
            parent_panel = next(
                (cls for _, cls in panels+top_level_panels if getattr(cls, "bl_idname", None) == bl_parent_id),
                None,
            )
            if parent_panel:
                graph.setdefault(parent_panel, []).append(panel_class)
            else:
                pass
                # Log a warning if the parent panel is not found
                # print(f"Warning: Parent panel '{bl_parent_id}' not found for child panel '{getattr(panel_class, 'bl_idname', None)}'")
        else:
            # Treat this as a top-level panel
            graph.setdefault(None, []).append(panel_class)

    # Add top-level panels to the graph explicitly if provided
    for top_level_panel in top_level_panels:
        if top_level_panel not in graph:
            graph[top_level_panel] = []

    # Depth-first search to sort panels
    def visit(panel_class):
        if panel_class in visited:
            return
        if panel_class in temp_mark:
            print(f"Cyclic dependency detected at panel '{getattr(panel_class, 'bl_idname', None)}'")

        temp_mark.add(panel_class)

        # Append the current panel **before** visiting its children
        if panel_class in panel_dict:  # Only add panels that exist in panel_dict
            sorted_panels.append(panel_dict[panel_class])  # Append the tuple (module_name, panel_class)

        # Visit children afterward
        
        for child in graph.get(panel_class, []):
            visit(child)

        temp_mark.remove(panel_class)
        visited.add(panel_class)

    # Start DFS from top-level panels
    for top_level_panel in top_level_panels:
        visit(top_level_panel[1])

    # Visit remaining panels (in case some aren't reachable from top-level panels)
    for panel_class in panel_dict.keys():
        if panel_class not in visited:
            visit(panel_class)

    return [a for a in sorted_panels if a in panels]
def workspace_category_enabled(self, context):
    try:
        space_type=context.area.type
    except:
        space_type='VIEW_3D'
    try:
        if context.area.type=='PREFERENCES':
            space_type=preferences().space_type
    except:
        space_type='VIEW_3D'
    
    if not preferences().filtering_method=="Use N-Panel Filtering":
        if self.filter_enabled:
            context.workspace.use_filter_by_owner = True
            categories=[]
            
            for index,a in enumerate(getattr(preferences(),f"workspace_categories{get_active_space(space_type)}")):
                if getattr(self,f'enabled{get_active_space(space_type)}_{index}',False):
                    #if a.name==context.workspace.pap_active_workspace_category:
                        #categories_string= ''.join(a.panels.split())
                        categories_string=split_keep_substring(a.panels)
                        #categories.extend([a.strip() for a in categories_string])
                        categories.extend([get_module_name_from_addon_name(a) for a in categories_string])
            for a in [__package__,'bl_pkg'] + categories[:]:
                if a!=__package__ and a!='bl_pkg':
                    a=get_full_module_name(a)
                try:
                    # a=sys.modules[a].__name__
                    if a not in [c.name for c in context.workspace.owner_ids]:
                        bpy.ops.wm.owner_enable(owner_id=a)
                except Exception as e:
                    print(e)
            for a in split_keep_substring(getattr(preferences(),f"addons_to_exclude{get_active_space(space_type)}"))+addons_to_exclude:
                
                a=get_module_name_from_addon_name(a)
                try:
                    if a not in [c.name for c in context.workspace.owner_ids] and a in bpy.context.preferences.addons.keys():
                        bpy.ops.wm.owner_enable(owner_id=a)
                except:
                    pass
            for b in bpy.context.preferences.addons.keys():
                try:
                    #print(b)
                    if b!='bl_pkg':
                        mod = sys.modules[b]
                        
                        if get_correct_module_name(mod.__name__) not in categories+['CleanPanels'] and b in [a.name for a in context.workspace.owner_ids]:
                            
                            if get_correct_module_name(mod.__name__) not in [get_module_name_from_addon_name(a) for a in split_keep_substring(getattr(preferences(),f"addons_to_exclude{get_active_space(space_type)}"))]+addons_to_exclude:
                                bpy.ops.wm.owner_disable(owner_id=b)
                except:
                        pass
        else:
            context.workspace.use_filter_by_owner = False
    else:
        registered_panels=[]
        for typename in dir(bpy.types):
            try:
                bl_type = getattr(bpy.types, typename,None)
                if issubclass(bl_type, bpy.types.Panel):
                    # if getattr(bl_type,"bl_region_type","None")=='UI' and getattr(bl_type,'bl_space_type',None)==space_type:
                    #     registered_panels.append(bl_type)
                    

                    package_name=inspect.getmodule(bl_type).__package__ if inspect.getmodule(bl_type).__package__ else inspect.getmodule(bl_type).__name__
                    if package_name=='__main__':
                        continue
                    # if "mega" or "liq" in package_name:
                    #      print(bl_type,getattr(bl_type,'bl_category','None'))
                    if "." in package_name:
                        name=get_package_name(package_name)
                    else:
                        name=package_name
                    if name in exceptional_names.keys():
                        name=exceptional_names[name]
                    
                    # if "edusa" in bl_type.__name__:
                    #     print("Medusa",bl_type,inspect.getmodule(bl_type).__name__,getattr(bl_type,'bl_space_type',None),getattr(bl_type,'backup_space',None))
                    name=get_custom_module_name(bl_type,name)
                    if name!='bl_ui' and name!='Brush_Manager':
                        registered_panels.append(bl_type)
                        if bl_type.__name__ in ('SCENE_PT_MedusaNodesHierarchy_Viewport','SCENE_PT_MedusaNodesMain_Viewport','SCENE_PT_MedusaNodesHierarchy_Properties'):
                            bl_type.backup_space="VIEW_3D"
                            bl_type.backup_region="UI"
                        else:                            
                            if  getattr(bl_type,'backup_space',None)==None and not getattr(bl_type,'is_subclass_backup_space_set',False):
                                
                                bl_type.backup_space=getattr(bl_type,'bl_space_type',None)
                                # if "edusa" in bl_type.__name__:
                                #     for a in bl_type.__subclasses__():
                                #         if not getattr(a,'is_subclass_backup_space_set',False):
                                #             print("Sub",a,getattr(a,'bl_space_type',None))
                                #             a.backup_space=getattr(a,'bl_space_type',None)
                                #             a.is_subclass_backup_space_set=True
                            if getattr(bl_type,'backup_region',None)==None and not getattr(bl_type,'is_subclass_backup_region_set',False):
                                bl_type.backup_region=getattr(bl_type,'bl_region_type',None)
                                # if "edusa" in bl_type.__name__:
                                #     for a in bl_type.__subclasses__():
                                #         if not getattr(a,'is_subclass_backup_region_set',False):
                                #             a.backup_region=getattr(a,'bl_region_type',None)
                                #             a.is_subclass_backup_region_set=True
                        if getattr(bl_type,'backup_order',0)==0:
                            bl_type.backup_order=0#getattr(bl_type,'bl_order',0)
                        if not getattr(bl_type,'backup_category',None) and getattr(bl_type,'bl_category',None):
                            bl_type.backup_category=bl_type.bl_category
                        # if not getattr(bl_type,'renamed_category',None): 
                        if getattr(bl_type,"bl_region_type","None")in {'HEADER','UI'} and getattr(bl_type,'bl_space_type',None) in {space_type,'TOPBAR'}:
                            
                            if getattr(preferences(),f"addon_info_for_renaming{get_active_space(space_type)}").find(name)>=0 :
                                bl_type.renamed_category=getattr(preferences(),f"addon_info_for_renaming{get_active_space(space_type)}")[getattr(preferences(),f"addon_info_for_renaming{get_active_space(space_type)}").find(name)].tab_name
            except:
                pass
        config_folder_path=Path(bpy.utils.user_resource('SCRIPTS')).parent/"config"
        config_path=os.path.join(config_folder_path,"CP-PanelOrder.txt")
        order_of_panels=[]
        if os.path.isfile(config_path):
            with open(config_path, mode='r', newline='\n', encoding='utf-8') as file:
                order_of_panels=file.readlines()
        else:
            if os.path.isfile(os.path.join(os.path.dirname(__file__),'CP-PanelOrder.txt')):
                with open(os.path.join(os.path.dirname(__file__),'CP-PanelOrder.txt'), mode='r', newline='\n', encoding='utf-8') as file:
                    order_of_panels=file.readlines()

        cleaned_order=[]
        if hasattr(bpy.utils,'panels'):
            if len(getattr(bpy.utils,'panels',[]))>len(order_of_panels):
                order_of_panels=getattr(bpy.utils,'panels',[])
        for o in order_of_panels:
            if o.replace("\n","") not in cleaned_order:
                cleaned_order.append(o.replace("\n",""))
        order_of_panels=cleaned_order
        
        focused_panels=[]
        
        if getattr(self,f"filter_enabled{get_active_space(space_type)}"):
            #context.workspace.use_filter_by_owner = True
            categories=[]
            for a in split_keep_substring(getattr(preferences(),f"addons_to_exclude{get_active_space(space_type)}"))+addons_to_exclude:
                try:
                    if get_module_name_from_addon_name(a)!='--Unknown--':
                        categories.append(get_module_name_from_addon_name(a))
                except:
                    pass
            uncategorized_addons=getattr(context.scene,f"uncategorized_addons{get_active_space(space_type)}","")
            if getattr(context.scene,f"load_uncategorized{get_active_space(space_type)}",False):
                categories.extend([get_module_name_from_addon_name(a) for a in split_keep_substring(uncategorized_addons)])
                # print("Uncategorized addons",[get_module_name_from_addon_name(a) for a in split_keep_substring(context.scene.uncategorized_addons)])
            for index,a in enumerate(getattr(preferences(),f"workspace_categories{get_active_space(space_type)}")):
                if getattr(self,f'enabled{get_active_space(space_type)}_{index}',False):
                    #if a.name==context.workspace.pap_active_workspace_category:
                        #categories_string= ''.join(a.panels.split())
                        categories_string=split_keep_substring(a.panels)
                        #categories.extend([a.strip() for a in categories_string])
                        categories.extend([get_module_name_from_addon_name(a) for a in categories_string])
            panels_from_reorder_list=[]
            
            for a in getattr(preferences(),f"addon_info{get_active_space(space_type)}"):
                if a.name in ['Tool','View','Node','Options'] :
                    panels_from_reorder_list.append(a.name)
                else:
                    for b in split_keep_substring(a.addons):
                            panels_from_reorder_list.append(b)
            # print("Reorder list",panels_from_reorder_list)
            panels_from_reorder_list=remove_duplicates(panels_from_reorder_list)
            if not preferences().sort_per_category or preferences().easy_mode:
                categories=sort_by_another_list(categories,panels_from_reorder_list)
            modules=[]
            for a in [__package__] + categories[:]:
                try:
                    if a in ['Tool','View','Node','Options']:
                         modules.append(a)
                    else:
                        modules.append(get_correct_module_name(a))
                except:
                    pass
            # print("Categories",categories)
            panels_to_reregister=[]
            parents=[]
            children=[]
            for bl_type in registered_panels:
                try:
                    package_name=inspect.getmodule(bl_type).__package__ if inspect.getmodule(bl_type).__package__ else inspect.getmodule(bl_type).__name__
                    if "." in package_name:
                        name=get_package_name(package_name)
                    else:
                        name=package_name
                    if name in exceptional_names.keys():
                        name=exceptional_names[name]
                    name=get_custom_module_name(bl_type,name)
                    try:                  
                        if bl_type :
                            if (getattr(bl_type,'bl_category',None) and getattr(bl_type,'backup_space',None)==space_type and getattr(bl_type,"backup_region","None")=='UI' ) and not getattr(bl_type,'bl_parent_id',None):
                                package_name=inspect.getmodule(bl_type).__package__ if inspect.getmodule(bl_type).__package__ else inspect.getmodule(bl_type).__name__
                                
                                if "." in package_name:
                                    name=get_package_name(package_name)
                                else:
                                    name=package_name
                                if name in exceptional_names.keys():
                                    name=exceptional_names[name]
                                name=get_custom_module_name(bl_type,name)
                                if name in modules or name.replace('ender-','') in modules:
                                    if bl_type.bl_category!='Focused':
                                        bl_type.bl_category=bl_type.backup_category if getattr(bl_type,'backup_category',None) else bl_type.bl_category
                                    if bl_type.bl_category=='Focused':

                                        focused_panels.append((name,bl_type))
                                    else:
                                    #print(bl_type,getattr(bl_type,'backup_category',None))
                                        panels_to_reregister.append((name,bl_type))

                                    # unregister_panel(bl_type)  
                                    # bpy.utils.register_class(bl_type)
                            else:
                                if getattr(bl_type,'bl_parent_id',None) and getattr(bl_type,"backup_region","UI")=='UI':
                                    # print("ASAS",bl_type,bl_type.bl_parent_id,"\n\n")
                                    package_name=inspect.getmodule(bl_type).__package__ if inspect.getmodule(bl_type).__package__ else inspect.getmodule(bl_type).__name__
                                    if "." in package_name:
                                        name=get_package_name(package_name)
                                    else:
                                        name=package_name
                                    if name in exceptional_names.keys():
                                        name=exceptional_names[name]
                                    name=get_custom_module_name(bl_type,name)
                                    
                                    if name in modules or name.replace("ender-","") in modules:
                                        #print(bl_type.bl_category)
                                        #bl_type.bl_category=bl_type.backup_category if getattr(bl_type,'backup_category',None) else bl_type.bl_category
                                        #print(bl_type,getattr(bl_type,'backup_category',None))
                                        children.append((name,bl_type))
                                        parents.append(bl_type.bl_parent_id)
                                        # unregister_panel(bl_type)  
                                        # bpy.utils.register_class(bl_type)
                    except Exception as e:
                        pass
                        #print(e)
                except:
                    pass
            
            panels_to_reregister=sort_panels(panels_to_reregister,order_of_panels)
            children=sort_panels(children,order_of_panels)
            focused_panels=sort_panels(focused_panels,order_of_panels)
            # print([a for a in children if 'ac' in str(a[1]) and a[0]=='BlenRig-master'])
            children=sort_panels_by_dependency(children,panels_to_reregister)
            # print(children)
            # children=sorted(children,key=lambda x:getattr(x[1],'bl_parent_id','Temp') in [getattr(a[1],'bl_idname','None') for a in children])
            # print([a for a in children if 'ac' in str(a[1]) and a[0]=='BlenRig-master'])
            # print("Modules",modules)
            
            for addon in modules:
                # print(addon)
                for name,p in focused_panels:

                    if name==addon or name.replace('ender-','')==addon:
                        if getattr(preferences(),f"addon_info_for_renaming{get_active_space(space_type)}").find(name)>=0:
                            if getattr(p,'bl_category'):
                                if not getattr(p,'backup_category',None):
                                    p.backup_category=p.bl_category
                            if getattr(p,'backup_order',None)!=None:
                                p.bl_order=getattr(p,'backup_order')
                            if p.bl_category!='Focused':
                                # if name=='Animation_Layers':
                                #     print(p.bl_category,preferences().addon_info_for_renaming[preferences().addon_info_for_renaming.find(name)].tab_name)
                                p.bl_category=getattr(preferences(),f"addon_info_for_renaming{get_active_space(space_type)}")[getattr(preferences(),f"addon_info_for_renaming{get_active_space(space_type)}").find(name)].tab_name
                                p.renamed_category=p.bl_category
                        try:
                            unregister_panel(p)  
                            register_panel(p)
                        except Exception as e:
                            print(e)
            for addon in modules:
                # print("registering",addon)
                for name,p in panels_to_reregister:
                    if name==addon or name.replace('ender-','')==addon:
                        if name in addons_with_multiple_tabs.keys():
                            name=name+"-"+getattr(p,'backup_category',getattr(p,'bl_category'))
                            #print("Multi",name)
                        if getattr(p,'backup_space',None)!=None and getattr(p,'backup_region',None)!=None:
                            p.bl_space_type=p.backup_space
                            p.bl_region_type=p.backup_region
                        if "home_builder" in name:
                             p.bl_options={a for a in getattr(p,'bl_options',[]) if a!='HIDE_HEADER'}
                        # if "pbr-painter" in name and getattr(p,'backup_category',None)=='Tool':
                        #     p.bl_category='Tool'
                        #     p.renamed_category='Tool'
                        
                        # elif name in addons_with_multiple_tabs.keys() and getattr(p,'backup_category',None)!=addons_with_multiple_tabs[name]:
                            
                        #     p.bl_category=getattr(p,'backup_category',None)
                        #     p.renamed_category=getattr(p,'backup_category',None)
                        
    
                        # elif "cats-blender" in name and getattr(p,'backup_category',None)!='CATS':
                            
                        #     p.bl_category=getattr(p,'backup_category',None)
                        #     p.renamed_category=getattr(p,'backup_category',None)
                        # elif "shino" in name and getattr(p,'backup_category',None)!='Shino':
                            
                        #     p.bl_category=getattr(p,'backup_category',None)
                        #     p.renamed_category=getattr(p,'backup_category',None)
                        elif name in ['View','Tool','Node','Options']:
                            p.bl_category=getattr(p,'backup_category',None)
                            p.renamed_category=getattr(p,'backup_category',None)
                            p.bl_order=getattr(p,'backup_order',0)
                        else:
                            if getattr(preferences(),f"addon_info_for_renaming{get_active_space(space_type)}").find(name)>=0:
                                if getattr(p,'bl_category'):
                                    if not getattr(p,'backup_category',None):
                                        p.backup_category=p.bl_category
                                if getattr(p,'backup_order',None)!=None:
                                    p.bl_order=getattr(p,'backup_order')
                                if p.bl_category!='Focused':
                                    p.bl_category=getattr(preferences(),f"addon_info_for_renaming{get_active_space(space_type)}")[getattr(preferences(),f"addon_info_for_renaming{get_active_space(space_type)}").find(name)].tab_name
                                    p.renamed_category=p.bl_category
                        try:
                            unregister_panel(p)  
                            register_panel(p)
                        except Exception as e:
                            print(1,e)
            for name,c in children:
                if name in addons_with_multiple_tabs.keys():
                    name=name+"-"+getattr(c,'backup_category',getattr(c,'bl_category','None'))
                    #print("Multi",name)
                if getattr(c,'backup_space',None)!=None and getattr(c,'backup_region',None)!=None:
                    c.bl_space_type=c.backup_space
                    c.bl_region_type=c.backup_region
                if "home_builder" in name:
                    c.bl_options={a for a in getattr(c,'bl_options',[]) if a!='HIDE_HEADER'}
                # if "pbr-painter" in name and getattr(c,'backup_category',None)=='Tool':
                #         c.bl_category='Tool'
                #         c.renamed_category='Tool'
                # elif name in addons_with_multiple_tabs.keys():
                #     name=name+"-"+getattr(c,'backup_category',getattr(c,'bl_category','None'))
                    # if getattr(c,'backup_category',None)!=addons_with_multiple_tabs[name]:
                    #     c.bl_category=getattr(c,'backup_category',None)
                    #     c.renamed_category=getattr(c,'backup_category',None)
                # elif "home_builder" in name and getattr(c,'backup_category',None)!='Home Builder':
                #         c.bl_category=getattr(c,'backup_category',None)
                #         c.renamed_category=getattr(c,'backup_category',None)
                # elif "cats-blender" in name and getattr(c,'backup_category',None)!='CATS':
                            
                #             c.bl_category=getattr(c,'backup_category',None)
                #             c.renamed_category=getattr(c,'backup_category',None)
                # elif "shino" in name and getattr(c,'backup_category',None)!='Shino':
                            
                #             c.bl_category=getattr(c,'backup_category',None)
                #             c.renamed_category=getattr(c,'backup_category',None)
                elif name in ['View','Tool','Node','Options']:
                            
                    c.bl_category=getattr(c,'backup_category',None)
                    c.renamed_category=getattr(c,'backup_category',None)
                    c.bl_order=getattr(c,'backup_order')
                else:
                    if getattr(preferences(),f"addon_info_for_renaming{get_active_space(space_type)}").find(name)>=0:
                        if getattr(c,'bl_category',None):
                            if not getattr(c,'backup_category',None):
                                c.backup_category=c.bl_category
                        if getattr(c,'backup_order',None)!=None:
                            c.bl_order=getattr(c,'backup_order')
                        c.bl_category=getattr(preferences(),f"addon_info_for_renaming{get_active_space(space_type)}")[getattr(preferences(),f"addon_info_for_renaming{get_active_space(space_type)}").find(name)].tab_name
                        c.renamed_category=c.bl_category
                try:
                    if c.bl_parent_id in parents:
                        unregister_panel(c)  
                        register_panel(c)
                except Exception as e:
                            print(2,e)
            for name,c in children:
                if name in addons_with_multiple_tabs.keys():
                    name=name+"-"+getattr(c,'backup_category',getattr(c,'bl_category','None'))
                    #print("Multi",name)
                if getattr(c,'backup_space',None)!=None and getattr(c,'backup_region',None)!=None:
                    c.bl_space_type=c.backup_space
                    c.bl_region_type=c.backup_region
                # if "pbr-painter" in name and getattr(c,'backup_category',None)=='Tool':
                #         c.bl_category='Tool'
                #         c.renamed_category='Tool'
                # elif name in addons_with_multiple_tabs.keys():
                #     name=name+"-"+getattr(c,'backup_category',getattr(c,'bl_category','None'))
                # elif name in addons_with_multiple_tabs.keys() and getattr(c,'backup_category',None)!=addons_with_multiple_tabs[name]:
                            
                #     c.bl_category=getattr(c,'backup_category',None)
                #     c.renamed_category=getattr(c,'backup_category',None)
                # elif "home_builder" in name and getattr(c,'backup_category',None)!='Home Builder':
                #         c.bl_category=getattr(c,'backup_category',None)
                #         c.renamed_category=getattr(c,'backup_category',None)
                # elif "cats-blender" in name and getattr(c,'backup_category',None)!='CATS':
                            
                #         c.bl_category=getattr(c,'backup_category',None)
                #         c.renamed_category=getattr(c,'backup_category',None)
                # elif "shino" in name and getattr(c,'backup_category',None)!='Shino':
                            
                #             c.bl_category=getattr(c,'backup_category',None)
                #             c.renamed_category=getattr(c,'backup_category',None)
                elif name in ['View','Tool','Node','Options']:
                            
                    c.bl_category=getattr(c,'backup_category',None)
                    c.renamed_category=getattr(c,'backup_category',None)
                    c.bl_order=getattr(c,'backup_order',0)
                else:
                    if getattr(preferences(),f"addon_info_for_renaming{get_active_space(space_type)}").find(name)>=0:
                        if getattr(c,'bl_category',None):
                            if not getattr(c,'backup_category',None):
                                c.backup_category=c.bl_category
                        if getattr(c,'backup_order',None)!=None:
                            c.bl_order=getattr(c,'backup_order')
                        c.bl_category=getattr(preferences(),f"addon_info_for_renaming{get_active_space(space_type)}")[getattr(preferences(),f"addon_info_for_renaming{get_active_space(space_type)}").find(name)].tab_name
                        c.renamed_category=c.bl_category
                try:
                    if c.bl_parent_id not in parents:
                        unregister_panel(c)  
                        register_panel(c)
                except Exception as e:
                            print(3,e)
            
            #print([sys.modules[get_module_name_from_addon_name(a)] for a in preferences().addons_to_exclude)+addons_to_exclude])
            modules_to_remove=[]
            for b in bpy.context.preferences.addons.keys():
                try:
                    #print(b)
                    mod = sys.modules[b]
                    if get_correct_module_name(mod.__name__) not in categories+[__package__]+["cycles",]:
                            a = get_correct_module_name(mod.__name__)
                            modules_to_remove.append(a)
                except:
                    pass
            for b in ['View','Tool','Node','Options']:
                try:
                    #print(b)
                    if b not in categories+[__package__]+["cycles",]:
                            a = b
                            modules_to_remove.append(a)
                except:
                    pass
                            #print("Marker",a)
            # print("Modules to remove",modules_to_remove)
            panels_to_unregister=[]
            children_to_unregister=[]
            parents_to_unregister=[]
            for bl_type in registered_panels:
                try:
                    if issubclass(bl_type, bpy.types.Panel):
                        
                        if getattr(bl_type,"bl_parent_id","None")=='None' and getattr(bl_type,"backup_region","UI")=='UI' and getattr(bl_type,'backup_space',"VIEW_3D")==space_type :
                            # if "edusa" in bl_type.__name__:
                            #     print("Unregister",bl_type,getattr(bl_type,"bl_parent_id","None"),getattr(bl_type,"backup_region","UI"),getattr(bl_type,'backup_space',"VIEW_3D"))
                            package_name=inspect.getmodule(bl_type).__package__ if inspect.getmodule(bl_type).__package__ else inspect.getmodule(bl_type).__name__
                            
                            if "." in package_name:
                                name=get_package_name(package_name)
                            else:
                                name=package_name
                            if name in exceptional_names.keys():
                                name=exceptional_names[name]
                            name=get_custom_module_name(bl_type,name)
                            if name in modules_to_remove or name.replace("ender-","") in modules_to_remove:
                                
                                if not getattr(bl_type,'backup_category',None):
                                    bl_type.backup_category=bl_type.bl_category if getattr(bl_type,'bl_category',preferences().holder_tab_name)!=preferences().holder_tab_name else (bl_type.backup_category if getattr(bl_type,'backup_category',None) else getattr(bl_type,'bl_category','None'))
                                if getattr(bl_type,'backup_order',0)==0:
                                    bl_type.backup_order=0#getattr(bl_type,'bl_order',0)
                                
                                if getattr(bl_type,'bl_category','None')!='Focused':
                                    bl_type.bl_category=preferences().holder_tab_name
                                    
                                    # bl_type.bl_order=1000000
                                    if preferences().remove_holder_tab:
                                        bl_type.bl_region_type='HEADER'
                                        bl_type.bl_space_type='TOPBAR'
                                    panels_to_unregister.append((name,bl_type))
                                    
                                    
                            
                except:
                    pass
            for bl_type in registered_panels:
                try:
                    if issubclass(bl_type, bpy.types.Panel):
                        #print(getattr(bl_type,'bl_parent_id',None))
                        if getattr(bl_type,"bl_parent_id","None")!='None' and getattr(bl_type,"backup_region","UI")=='UI' and getattr(bl_type,'backup_space',"VIEW_3D")==space_type :
                            
                            package_name=inspect.getmodule(bl_type).__package__ if inspect.getmodule(bl_type).__package__ else inspect.getmodule(bl_type).__name__
                            
                            if "." in package_name:
                                name=get_package_name(package_name)
                            else:
                                name=package_name
                            if name in exceptional_names.keys():
                                name=exceptional_names[name]
                            name=get_custom_module_name(bl_type,name)
                            #print(name)
                            # print(modules_to_remove)
                            if name in modules_to_remove or name.replace("ender-","") in modules_to_remove:
                                #print(bl_type)
                                #print("296 setting backup",bl_type.bl_category)
                                
                                if not getattr(bl_type,'backup_category',None):
                                    bl_type.backup_category=bl_type.bl_category if getattr(bl_type,'bl_category',preferences().holder_tab_name)!=preferences().holder_tab_name else (bl_type.backup_category if getattr(bl_type,'backup_category',None) else getattr(bl_type,'bl_category','None'))
                                if getattr(bl_type,'backup_order',0)==0:
                                    bl_type.backup_order=0#getattr(bl_type,'bl_order',0)
                                
                                if getattr(bl_type,'bl_category','None')!='Focused' and getattr(getattr(bpy.types,bl_type.bl_parent_id,None),"bl_category","None")!='Focused':
                                    bl_type.bl_category=preferences().holder_tab_name
                                    
                                    # bl_type.bl_order=1000000
                                    if preferences().remove_holder_tab:
                                        bl_type.bl_region_type='HEADER'
                                        bl_type.bl_space_type='TOPBAR'
                                    children_to_unregister.append((name,bl_type))
                                    parents_to_unregister.append(bl_type.bl_parent_id)
                                # if preferences().addon_info_for_renaming.find(name)>=0 and hasattr(bl_type,'bl_category'):
                                #     bl_type.renamed_category=preferences().addon_info_for_renaming[preferences().addon_info_for_renaming.find(name)].tab_name
                                #print("removing",bl_type)
                                    
                                    # unregister_panel(bl_type)  
                                    # if 'kit' in name.lower():
                                    #     print(bl_type,getattr(bl_type,'backup_space','None'))
                                    # if 'VIEW3D_PT_blenderkit_advanced_model_search' in getattr(bl_type,'bl_idname','None'):
                                    #     if getattr(bl_type,'bl_parent_id','None') in [getattr(a,'bl_idname','None') for a in registered_panels]:
                                    #         print(getattr(bl_type,'bl_parent_id','None'),"is registered")
                                    
                                    # try:
                                    #     register_panel(bl_type)
                                    #     # if 'VIEW3D_PT_blenderkit_unified' in getattr(bl_type,'bl_idname','None'):
                                    #     #     print("Registering",'VIEW3D_PT_blenderkit_unified')
                                    # except Exception as e:
                                    #     print(e)
                                    
                            
                except:
                    pass
            panels_to_unregister=sort_panels(panels_to_unregister,order_of_panels)
            children_to_unregister=sort_panels(children_to_unregister,order_of_panels)
            children_to_unregister=sort_panels_by_dependency(children_to_unregister,panels_to_unregister)
            # print([a for a in panels_to_unregister if 'Sanctus' in a[0]])
            # print("\nC")
            # print([a for a in children_to_unregister if 'Sanctus' in a[0]])
            for _,bl_type in panels_to_unregister:
                unregister_panel(bl_type)  
                try:
                    register_panel(bl_type)
                except Exception as e:
                    print(e)
            for _,bl_type in children_to_unregister:
                if getattr(bl_type,'bl_parent_id','None') in parents_to_unregister:
                    unregister_panel(bl_type)  
                    try:
                        register_panel(bl_type)
                    except Exception as e:
                        print("Children Parent",e)
            for _,bl_type in children_to_unregister:
                if getattr(bl_type,'bl_parent_id','None') not in parents_to_unregister:
                    unregister_panel(bl_type)  
                    try:
                        register_panel(bl_type)
                    except Exception as e:
                        print("Children",e)
            
        else:
            # print("Disabled")
            # print(registered_panels)
            panels_to_reregister=[]
            parents=[]
            children=[]
            modules=[]
            focused_panels=[]
            for a in bpy.context.preferences.addons.keys():
                try:
                    if get_correct_module_name(sys.modules[a].__name__) not in ["cycles",]:
                        modules.append(get_correct_module_name(sys.modules[a].__name__))
                except Exception as e:
                    pass
            modules=['Tool','View','Node','Options']+modules
            sorted_modules=[]
            # for a in getattr(preferences(),f"addon_info{get_active_space(space_type)}"):
                
            #     for b in split_keep_substring(a.addons):
            #             panels_from_reorder_list.append(b)
            for addon_info in getattr(preferences(),f"addon_info{get_active_space(space_type)}"):
                if addon_info.name in ['Tool','View','Node','Options'] :
                    sorted_modules.append(addon_info.name)
                else:
                    for a in split_keep_substring(addon_info.addons):
                        if a in modules:
                            if a not in sorted_modules:
                                sorted_modules.append(a)
            # print("Sorted",sorted_modules)
            
            sorted_modules=sorted_modules+[a for a in modules if a not in sorted_modules]
            for bl_type in registered_panels:
                    
                    try:
                            if getattr(bl_type,'bl_category',None) and getattr(bl_type,'backup_space',None)==space_type and not getattr(bl_type,'bl_parent_id',None):
                                
                                package_name=inspect.getmodule(bl_type).__package__ if inspect.getmodule(bl_type).__package__ else inspect.getmodule(bl_type).__name__
                                
                                if "." in package_name:
                                    name=get_package_name(package_name)
                                else:
                                    name=package_name
                                if name in exceptional_names.keys():
                                        name=exceptional_names[name]
                                name=get_custom_module_name(bl_type,name)
                                
                                if name in sorted_modules or name.replace('ender-','') in sorted_modules:
                                    if bl_type.bl_category!='Focused':
                                        bl_type.bl_category=bl_type.backup_category if getattr(bl_type,'backup_category',None) else bl_type.bl_category
                                    if bl_type.bl_category=='Focused':
                                        focused_panels.append((name,bl_type))
                                    else:
                                        panels_to_reregister.append((name,bl_type))
                            else:
                                if bl_type and getattr(bl_type,'bl_parent_id',None) and getattr(bl_type,'backup_region','UI')=='UI':
                                    package_name=inspect.getmodule(bl_type).__package__ if inspect.getmodule(bl_type).__package__ else inspect.getmodule(bl_type).__name__
                                    if "." in package_name:
                                        name=get_package_name(package_name)
                                    else:
                                        name=package_name
                                    if name in exceptional_names.keys():
                                        name=exceptional_names[name]
                                    name=get_custom_module_name(bl_type,name)
                                    if name!='bl_ui' and name in sorted_modules:
                                        parents.append(bl_type.bl_parent_id)
                                        children.append((name,bl_type))
                    except Exception as e:
                        pass

            panels_to_reregister=sort_panels(panels_to_reregister,order_of_panels)
            children=sort_panels(children,order_of_panels)
            focused_panels=sort_panels(focused_panels,order_of_panels)
            children=sort_panels_by_dependency(children,panels_to_reregister)
            # children=sorted(children,key=lambda x:getattr(x[1],'bl_parent_id','Temp') in [getattr(a[1],'bl_idname','None') for a in children])
            #print(panels_to_reregister,children)
            # print("Sorted",[a.__name__ for b,a in panels_to_reregister if "RTOO" in a.__name__])
            for addon in sorted_modules:
                
                for name,p in focused_panels:
                    if getattr(p,'backup_space',None)!=None and getattr(p,'backup_region',None)!=None:
                        p.bl_space_type=p.backup_space
                        p.bl_region_type=p.backup_region
                    if getattr(preferences(),f"addon_info_for_renaming{get_active_space(space_type)}").find(name)>=0 and hasattr(p,'bl_category'):
                        
                        if not getattr(p,'backup_category',None):
                            p.backup_category=p.bl_category
                        if getattr(p,'backup_order',None)!=None:
                                p.bl_order=getattr(p,'backup_order')
                        if p.bl_category!='Focused':
                            p.bl_category=getattr(preferences(),f"addon_info_for_renaming{get_active_space(space_type)}")[getattr(preferences(),f"addon_info_for_renaming{get_active_space(space_type)}").find(name)].tab_name
                            p.renamed_category=p.bl_category
                    if name==addon or name.replace('ender-','')==addon:
                        try:
                            unregister_panel(p) 
                            register_panel(p)
                        except:
                            pass
            for addon in sorted_modules:
                for name,p in panels_to_reregister:
                    if name==addon or name.replace('ender-','')==addon:
                        if name in addons_with_multiple_tabs.keys():
                                name=name+"-"+getattr(p,'backup_category',getattr(p,'bl_category'))
                                #print("Multi",name)
                        if getattr(p,'backup_space',None)!=None and getattr(p,'backup_region',None)!=None:
                            # print(getattr(p,'backup_region',None))
                            p.bl_space_type=p.backup_space
                            p.bl_region_type=p.backup_region
                        if "home_builder" in name:
                                p.bl_options={a for a in getattr(p,'bl_options',[]) if a!='HIDE_HEADER'}
                        # if "pbr-painter" in name and getattr(p,'backup_category',None)=='Tool':
                        #     p.bl_category='Tool'
                        #     p.renamed_category='Tool'
                        # elif name in addons_with_multiple_tabs.keys():
                        #     name=name+"-"+getattr(p,'backup_category',getattr(p,'bl_category'))
                        # elif name in addons_with_multiple_tabs.keys() and getattr(p,'backup_category',None)!=addons_with_multiple_tabs[name]:
                                
                        #         p.bl_category=getattr(p,'backup_category',None)
                        #         p.renamed_category=getattr(p,'backup_category',None)
                        # elif "home_builder" in name and getattr(p,'backup_category',None)!='Home Builder':
                                
                        #         p.bl_category=getattr(p,'backup_category',None)
                        #         p.renamed_category=getattr(p,'backup_category',None)
                        # elif "cats-blender" in name and getattr(p,'backup_category',None)!='CATS':
                                
                        #         p.bl_category=getattr(p,'backup_category',None)
                        #         p.renamed_category=getattr(p,'backup_category',None)
                        # elif "shino" in name and getattr(p,'backup_category',None)!='Shino':
                                
                        #         p.bl_category=getattr(p,'backup_category',None)
                        #         p.renamed_category=getattr(p,'backup_category',None)
                        elif name in ['View','Tool','Node','Options']:
                                
                                p.bl_category=getattr(p,'backup_category',None)
                                p.renamed_category=getattr(p,'backup_category',None)
                                p.bl_order=getattr(p,'backup_order',0)
                        else:
                            if getattr(preferences(),f"addon_info_for_renaming{get_active_space(space_type)}").find(name)>=0 and hasattr(p,'bl_category'):
                                
                                if not getattr(p,'backup_category',None):
                                    p.backup_category=p.bl_category
                                if getattr(p,'backup_order',None)!=None:
                                    p.bl_order=getattr(p,'backup_order')
                                    
                                if p.bl_category!='Focused':
                                    p.bl_category=getattr(preferences(),f"addon_info_for_renaming{get_active_space(space_type)}")[getattr(preferences(),f"addon_info_for_renaming{get_active_space(space_type)}").find(name)].tab_name
                                    p.renamed_category=p.bl_category
                        
                        try:
                            
                            unregister_panel(p) 
                            register_panel(p)
                            # print(p.bl_region_type,p.bl_space_type)
                        except Exception as e:
                            # print("Already",p,e)
                            pass
            
            for name,c in children:
                if name in addons_with_multiple_tabs.keys():
                            name=name+"-"+getattr(c,'backup_category',getattr(c,'bl_category','None'))
                            #print("Multi",name)
                if getattr(c,'backup_space',None)!=None and getattr(c,'backup_region',None)!=None:
                    c.bl_space_type=c.backup_space
                    c.bl_region_type=c.backup_region
                # if "pbr-painter" in name and getattr(c,'backup_category',None)=='Tool':
                #         c.bl_category='Tool'
                #         c.renamed_category='Tool'
                # elif name in addons_with_multiple_tabs.keys():
                #     name=name+"-"+getattr(c,'backup_category',getattr(c,'bl_category','None'))
                # elif name in addons_with_multiple_tabs.keys() and getattr(c,'backup_category',None)!=addons_with_multiple_tabs[name]:
                            
                #             c.bl_category=getattr(c,'backup_category',None)
                #             c.renamed_category=getattr(c,'backup_category',None)
                # elif "home_builder" in name and getattr(c,'backup_category',None)!='Home Builder':
                #         c.bl_category=getattr(c,'backup_category',None)
                #         c.renamed_category=getattr(c,'backup_category',None)
                # elif "cats-blender" in name and getattr(c,'backup_category',None)!='CATS':
                            
                #             c.bl_category=getattr(c,'backup_category',None)
                #             c.renamed_category=getattr(c,'backup_category',None)
                # elif "shino" in name and getattr(c,'backup_category',None)!='Shino':
                            
                #             c.bl_category=getattr(c,'backup_category',None)
                #             c.renamed_category=getattr(c,'backup_category',None)
                elif name in ['View','Tool','Node','Options']:
                            
                            c.bl_category=getattr(c,'backup_category',None)
                            c.renamed_category=getattr(c,'backup_category',None)
                            c.bl_order=getattr(c,'backup_order',0)
                else:
                    if getattr(preferences(),f"addon_info_for_renaming{get_active_space(space_type)}").find(name)>=0 :
                        
                        if getattr(c,'bl_category',None) and not getattr(c,'backup_category',None):
                                c.backup_category=c.bl_category
                        if getattr(c,'backup_order',None)!=None:
                                    c.bl_order=getattr(c,'backup_order')
                        c.bl_category=getattr(preferences(),f"addon_info_for_renaming{get_active_space(space_type)}")[getattr(preferences(),f"addon_info_for_renaming{get_active_space(space_type)}").find(name)].tab_name
                        c.renamed_category=c.bl_category
                try:
                    if c.bl_parent_id in parents:
                        unregister_panel(c)  
                        register_panel(c)
                except:
                    pass
            for name,c in children:
                if name in addons_with_multiple_tabs.keys():
                            name=name+"-"+getattr(c,'backup_category',getattr(c,'bl_category','None'))
                            #print("Multi",name)
                if getattr(c,'backup_space',None)!=None and getattr(c,'backup_region',None)!=None:
                    c.bl_space_type=c.backup_space
                    c.bl_region_type=c.backup_region
                # if "pbr-painter" in name and getattr(c,'backup_category',None)=='Tool':
                #     c.bl_category='Tool'
                #     c.renamed_category='Tool'
                # elif name in addons_with_multiple_tabs.keys():
                #     name=name+"-"+getattr(c,'backup_category',getattr(c,'bl_category','None'))
                # elif name in addons_with_multiple_tabs.keys() and getattr(c,'backup_category',None)!=addons_with_multiple_tabs[name]:
                            
                #             c.bl_category=getattr(c,'backup_category',None)
                #             c.renamed_category=getattr(c,'backup_category',None)
                # elif "home_builder" in name and getattr(c,'backup_category',None)!='Home Builder':
                #         c.bl_category=getattr(c,'backup_category',None)
                #         c.renamed_category=getattr(c,'backup_category',None)
                # elif "cats-blender" in name and getattr(c,'backup_category',None)!='CATS':
                            
                #             c.bl_category=getattr(c,'backup_category',None)
                #             c.renamed_category=getattr(c,'backup_category',None)
                # elif "shino" in name and getattr(c,'backup_category',None)!='Shino':
                            
                #             c.bl_category=getattr(c,'backup_category',None)
                #             c.renamed_category=getattr(c,'backup_category',None)
                elif name in ['View','Tool','Node','Options']:
                            
                            c.bl_category=getattr(c,'backup_category',None)
                            c.renamed_category=getattr(c,'backup_category',None)
                            c.bl_order=getattr(c,'backup_order',0)
                else:
                    if getattr(preferences(),f"addon_info_for_renaming{get_active_space(space_type)}").find(name)>=0 :
                        if getattr(c,'bl_category',None) and not getattr(c,'backup_category',None):
                                c.backup_category=c.bl_category
                        if getattr(c,'backup_order',None)!=None:
                                    c.bl_order=getattr(c,'backup_order')
                        c.bl_category=getattr(preferences(),f"addon_info_for_renaming{get_active_space(space_type)}")[getattr(preferences(),f"addon_info_for_renaming{get_active_space(space_type)}").find(name)].tab_name
                        c.renamed_category=c.bl_category
                try:
                    if c.bl_parent_id not in parents:
                        unregister_panel(c)  
                        register_panel(c)
                except:
                    pass
    
    try:
        context.workspace.enabled_categories=""
            
        for i in range(50):
            if getattr(preferences().categories,f"enabled{get_active_space(space_type)}_{i}",False):
                context.workspace.enabled_categories=context.workspace.enabled_categories+f"{i},"
        context.workspace.filter_enabled=preferences().categories.filter_enabled
    except Exception:
        pass
    
def load_reordering_list(context,space='VIEW_3D',force_clear=False):
        for a in getattr(preferences(),f"addon_info{get_active_space(space)}"):
            a.addons=""
            a.ordered=""
        #preferences().addon_info.clear()
        change_panel_category("Turn OFF","Focused",space)
        workspace_category_enabled(preferences().categories,context) 
        og_filter=preferences().categories.filter_enabled
        preferences().categories.filter_enabled=False
        panels_in_use=[]
        no_fix_required=[]
        base_type = bpy.types.Panel
        for typename in dir(bpy.types):
            
            try:
                bl_type = getattr(bpy.types, typename,None)
                if issubclass(bl_type, base_type):
                    if getattr(bl_type,'bl_parent_id',None) ==None and getattr(bl_type,'bl_category',None) and getattr(bl_type,'bl_space_type',None)==space and getattr(bl_type,'bl_category',None) not in ["Item","Dev",preferences().holder_tab_name]:
                        if getattr(bl_type,'bl_category')!='None':
                            panels_in_use.append(getattr(bl_type,'bl_category'))
                        if getattr(bl_type,'bl_category') not in [a.name for a in  getattr(preferences(),f"addon_info{get_active_space(space)}")]:
                            t=getattr(preferences(),f"addon_info{get_active_space(space)}").add()
                            t.name=getattr(bl_type,'bl_category')
                            package_name=inspect.getmodule(bl_type).__package__ if inspect.getmodule(bl_type).__package__ else inspect.getmodule(bl_type).__name__
                            if "." in package_name:
                                name=get_package_name(package_name)
                            else:
                                name=package_name
                            if name in exceptional_names.keys():
                                name=exceptional_names[name]
                            name=get_custom_module_name(bl_type,name)
                            if name not in t.addons:
                                t.addons=name
                            if getattr(bl_type,'bl_order',None)!=None:
                                if getattr(bl_type,'bl_order',None)==0:
                                    no_fix_required.append(name)
                                t.ordered=name
                                #print(t.name,t.ordered)
                        else:
                            t=getattr(preferences(),f"addon_info{get_active_space(space)}")[getattr(preferences(),f"addon_info{get_active_space(space)}").find(getattr(bl_type,'bl_category'))]
                            if t=='None':
                                continue
                            package_name=inspect.getmodule(bl_type).__package__ if inspect.getmodule(bl_type).__package__ else inspect.getmodule(bl_type).__name__
                            if "." in package_name:
                                name=get_package_name(package_name)
                            else:
                                name=package_name
                            if name in exceptional_names.keys():
                                        name=exceptional_names[name]
                            name=get_custom_module_name(bl_type,name)
                            if name not in t.addons:
                                t.addons=t.addons+","+name
                            if getattr(bl_type,'bl_order',None) !=None:
                                if getattr(bl_type,'bl_order',None)==0:
                                    no_fix_required.append(name)
                                if name not in t.ordered:
                                    t.ordered=t.ordered+("," if t.ordered else '') +name
                                    #print(t.name,t.ordered)
            except Exception as e:
                if str(e)!="issubclass() arg 1 must be a class":
                    pass
        # print(no_fix_required)
        # for addon in preferences().addon_info:
        #     temp_array=addon.ordered)
        #     for a in no_fix_required:
        #         if a in temp_array:
        #             temp_array.remove(a)
        #     print(addon,temp_array)
        #     addon.ordered=",".join(temp_array)
        for tab in getattr(preferences(),f"addon_info{get_active_space(space)}"):
            if tab.ordered:
                if tab.ordered!=tab.addons:
                    temp_array=sorted(split_keep_substring(tab.addons),key=lambda x:x in tab.ordered)
                    tab.addons=",".join(temp_array)
                    tab.ordered=""
        # print(preferences().addon_info[:])
        # print("Panels in use\n\n\n",panels_in_use)
        if preferences().remove_uninstalled_addons or force_clear:
            for tab in getattr(preferences(),f"addon_info{get_active_space(space)}"):
                # print(tab.name ,[a.tab_name for a in  getattr(preferences(),f"addon_info_for_renaming{get_active_space(space)}")])
                if tab.name not in panels_in_use and tab.name not in [a.tab_name for a in  getattr(preferences(),f"addon_info_for_renaming{get_active_space(space)}")]:
                    if getattr(preferences(),f"addon_info{get_active_space(space)}").find(tab.name)>-1:
                        getattr(preferences(),f"addon_info{get_active_space(space)}").remove(getattr(preferences(),f"addon_info{get_active_space(space)}").find(tab.name))
        # print(preferences().addon_info[:])
        # for addon in sorted([a.module for a in context.preferences.addons]):
        #     t=preferences().addon_info.add()
        #     t.name=addon
        # for b in preferences().addon_info:
        #     print(b.name,b.addons)
        savePreferences()
        preferences().categories.filter_enabled=og_filter
tab_names_dict={
     'pbr-pbr-painter':'PBR pbr-painter',
     'home_builder':'Home Builder',
     'shape_generator':'Shape Generator',
     'auto_rig_pro':'ARP',
     'auto_rig_pro-master':'ARP',
     'auto_rig_pro_master':'ARP'
}
multi_tab_to_ignore=['hops','true-vfx']
def update_multitab_addons():
    global addons_with_multiple_tabs
    base_type = bpy.types.Panel
    panels_dict = {}
    for typename in dir(bpy.types):
        try:
            bl_type = getattr(bpy.types, typename, None)
            if issubclass(bl_type, base_type):
                if getattr(bl_type, 'bl_category', None):
                    
                    package_name = inspect.getmodule(bl_type).__package__ if inspect.getmodule(bl_type).__package__ else inspect.getmodule(bl_type).__name__
                    
                    if "." in package_name:
                        name = get_package_name(package_name)
                    else:
                        name = package_name
                    
                    if name in exceptional_names.keys():
                        name = exceptional_names[name]
                    name = get_custom_module_name(bl_type, name)

                    bl_space_type = getattr(bl_type, 'bl_space_type', None)
                    if "bl_ui" not in name:
                        if panels_dict.get(name, None):
                            existing_space_type = panels_dict[name][0]['bl_space_type']
                            if bl_space_type == existing_space_type:
                                if getattr(bl_type, 'backup_category', getattr(bl_type, 'bl_category'))!=None and getattr(bl_type, 'backup_category', getattr(bl_type, 'bl_category')) not in panels_dict[name][0]['categories']:
                                    panels_dict[name][0]['categories'].append(getattr(bl_type, 'backup_category', getattr(bl_type, 'bl_category')))
                        else:
                            panels_dict[name] = [{'bl_space_type': bl_space_type, 'categories': [getattr(bl_type, 'backup_category', getattr(bl_type, 'bl_category'))]}]
                            
        except Exception as e:
            pass
    
    for addon_name, panels_info in panels_dict.items():
        if len(panels_info[0]['categories']) > 1:
            if addon_name.lower() not in multi_tab_to_ignore:
                addons_with_multiple_tabs[addon_name] = panels_info[0]['categories']
    # print(addons_with_multiple_tabs)
def load_renaming_list(context,reset=False,space='VIEW_3D',force_clear=False):
    change_panel_category("Turn OFF","Focused",space)
    workspace_category_enabled(preferences().categories,context) 
    og_filter=preferences().categories.filter_enabled
    preferences().categories.filter_enabled=False
    panels_in_use=[]
    no_fix_required=[]
    base_type = bpy.types.Panel
    update_multitab_addons()
    for typename in dir(bpy.types):
        try:
            bl_type = getattr(bpy.types, typename,None)
            if issubclass(bl_type, base_type):
                if getattr(bl_type,'bl_category',None) and getattr(bl_type,'bl_space_type',None)==space:
                    
                    package_name=inspect.getmodule(bl_type).__package__ if inspect.getmodule(bl_type).__package__ else inspect.getmodule(bl_type).__name__

                    identifier=get_addon_identifier(package_name)
                    if "." in package_name:
                        name=get_package_name(package_name)
                    else:
                        name=package_name
                    if name in exceptional_names.keys():
                        name=exceptional_names[name]
                    name=get_custom_module_name(bl_type,name)
                    
                    display_name=get_addon_name_from_module_name(name)
                    if name in addons_with_multiple_tabs.keys():
                        name=name+"-"+getattr(bl_type,'backup_category',getattr(bl_type,'bl_category'))
                        display_name=display_name+" ("+getattr(bl_type,'backup_category',getattr(bl_type,'bl_category'))+")"
                    if "bl_ui" not in name:
                        panels_in_use.append(name)
                        if name not in [a.name for a in  getattr(preferences(),f"addon_info_for_renaming{get_active_space(space)}")]:
                            
                            t=getattr(preferences(),f"addon_info_for_renaming{get_active_space(space)}").add()
                            t.backup_tab_name=getattr(bl_type,'backup_category',getattr(bl_type,'bl_category'))
                            t.tab_name=getattr(bl_type,'bl_category') if getattr(bl_type,'bl_category',preferences().holder_tab_name) !=preferences().holder_tab_name else (getattr(bl_type,'backup_category',preferences().holder_tab_name))
                            t.tab_name=tab_names_dict.get(name,t.tab_name)
                            t.name=name
                            t.display_name=display_name
                            t.identifier=identifier
                            t.space=getattr(bl_type,'bl_space_type','None')
                                #print(t.name,t.ordered)
                        else:
                            t=getattr(preferences(),f"addon_info_for_renaming{get_active_space(space)}")[getattr(preferences(),f"addon_info_for_renaming{get_active_space(space)}").find(name)]
                            if not t.tab_name or t.tab_name==preferences().holder_tab_name or t.tab_name=='None':
                                t.tab_name=getattr(bl_type,'bl_category') if getattr(bl_type,'bl_category',preferences().holder_tab_name) !=preferences().holder_tab_name else (getattr(bl_type,'backup_category',preferences().holder_tab_name))
                                
                            if reset and getattr(bl_type,'backup_category',None):
                                 t.tab_name=getattr(bl_type,'backup_category')
                            t.backup_tab_name=getattr(bl_type,'backup_category',getattr(bl_type,'bl_category'))
                            t.display_name=display_name
                            t.identifier=identifier
                            t.space=getattr(bl_type,'bl_space_type','None')
                            # package_name=inspect.getmodule(bl_type).__package__ if inspect.getmodule(bl_type).__package__ else inspect.getmodule(bl_type).__name__
                            # if "." in package_name:
                            #     name=get_package_name(package_name)
                            # else:
                            #     name=package_name
                            # t.name=name
        except Exception as e:
            if str(e)!="issubclass() arg 1 must be a class":
                pass
    #print(panels_in_use)
        # print(addons_with_multiple_tabs)
    if preferences().remove_uninstalled_addons or force_clear:
        for a in getattr(preferences(),f"addon_info_for_renaming{get_active_space(space)}"):
            # if "vscode" not in a.identifier:
            #     print(a.identifier,addon_utils.check(a.identifier)[0] , addon_utils.check(a.identifier)[1])
            # if a.identifier not in addon_utils.module[]:
            # print("Removing",get_correct_module_name(a.name))
            # if a.name not in panels_in_use:
            #     print('Removing22',a.name)
            if addon_utils.check(a.identifier)[0]==False or (a.space and a.space!=space):
                getattr(preferences(),f"addon_info_for_renaming{get_active_space(space)}").remove(getattr(preferences(),f"addon_info_for_renaming{get_active_space(space)}").find(a.name))

    savePreferences()
    preferences().categories.filter_enabled=og_filter
def get_active_space(specified=None):
        # if preferences().easy_mode:
        #     return ''
        if specified:
            space="_"+specified
            if space=='_VIEW_3D':
                space=''
            space=space.lower()
            return space
        space="_"+preferences().space_type
        if space=='_VIEW_3D':
            space=''
        space=space.lower()
        return space
def get_gist_text(id="",file="",all_files=False):
    try:
        try:
            r=requests.get('https://api.github.com/gists/' + id)
        except ConnectionError as e:
            print("Could not fetch gist! No Internet connection!")
            return None,'No Internet'
        results=r.json()
        if not all_files:
            if not file:
                file=list(results['files'].keys())[0]
            return str(results['files'][file]['content'])
        else:
            data={}
            for a in list(results['files'].keys()):
                data[a]=str(results['files'][a]['content'])
            return data
    except Exception as e:
        print("API Limit reached! Please try later!")
        return ''
def remove_duplicates_preserve_order(lst):
    seen = set()
    return [x for x in lst if not (x in seen or seen.add(x))]
def update_cp_database():
    import addon_utils
    result=get_gist_text("b974e9819f9d327ab15e87dd4f4da434",all_files=True)
    for name,data in result.items():
        if "database" in name:
            json_file_path = os.path.join(os.path.dirname(__file__), "cp_database.json")
            with open(json_file_path, "w+") as f:
                f.write(data)
def fetch_categories():
    import addon_utils
    enabled_addons=[addon_utils.module_bl_info(a)['name'] for a in addon_utils.modules() if addon_utils.check(a.__name__)[1]]
    
    categories=get_gist_text("377e6d64956df704765a71b10df6eeb6",all_files=True)
    for cat,addons in categories.items():
        addons=[a for a in split_keep_substring(addons) if a in enabled_addons]
        if ("(Node Editor)") in cat :
            if preferences().space_type=='NODE_EDITOR':
                if preferences().workspace_categories_node_editor.get(cat,None):
                    t=preferences().workspace_categories_node_editor.get(cat,None)
                    current_addons=split_keep_substring(preferences().workspace_categories_node_editor.get(cat).panels)
                    t.panels=",".join(remove_duplicates_preserve_order(current_addons+addons))
                else:
                    t=preferences().workspace_categories_node_editor.add()
                    t.name=cat
                    t.panels=",".join(addons)
        elif ("(Image Editor)") in cat :
            if preferences().space_type=='IMAGE_EDITOR':            
                if preferences().workspace_categories_image_editor.get(cat,None):
                    t=preferences().workspace_categories_image_editor.get(cat,None)
                    current_addons=split_keep_substring(preferences().workspace_categories_image_editor.get(cat).panels)
                    t.panels=",".join(remove_duplicates_preserve_order(current_addons+addons))
                else:
                    t=preferences().workspace_categories_image_editor.add()
                    t.name=cat
                    t.panels=",".join(addons)
        else:
            if preferences().space_type=='VIEW_3D':
                if preferences().workspace_categories.get(cat,None):
                    t=preferences().workspace_categories.get(cat,None)
                    current_addons=split_keep_substring(preferences().workspace_categories.get(cat).panels)
                    t.panels=",".join(remove_duplicates_preserve_order(current_addons+addons))
                else:
                    t=preferences().workspace_categories.add()
                    t.name=cat
                    t.panels=",".join(addons)
def draw_dropdown_panel(layout: bpy.types.UILayout, data, prop,text=""):
    layout=layout.row(align=True)
    layout.alignment = "LEFT"
    if text:
        layout.prop(
        data,
        prop,
        text=text,
        emboss=False,
        icon="DOWNARROW_HLT" if getattr(data, prop) else "RIGHTARROW",
    )
    else:
        layout.prop(
            data,
            prop,
            emboss=False,
            icon="DOWNARROW_HLT" if getattr(data, prop) else "RIGHTARROW",
        )
    return getattr(data, prop)
def draw_category(layout, data, prop,text,index,pcoll,show_icon=True,category_type='Workspace'):
    layout=layout.row()
    name_row=layout.row(align=True)
    name_row.alignment = "LEFT"
    # name_row=name_row.split(factor=0.9)
    if text:
        name_row.prop(
        data,
        prop,
        text=text,
        emboss=False,
        icon="DOWNARROW_HLT" if getattr(data, prop) else "RIGHTARROW",
    )
    else:
        name_row.prop(
            data,
            prop,
            emboss=False,
            icon="DOWNARROW_HLT" if getattr(data, prop) else "RIGHTARROW",
        )
    # row1=layout.row()
    # row1=row1.split(factor=0.7)
                
    # row1.prop(data,'name',text="")
    # layout.alignment = "RIGHT"
    # layout.separator_spacer()
    row2=layout.row(align=True)
    row2.alignment = "RIGHT"
    if show_icon:
        if data.icon in ALL_ICONS:
            row2.operator("cp.change_icon",text="Icon",icon=data.icon if data.icon else None).index=index
        else:
            row2.operator("cp.change_icon",text="Icon",icon_value=pcoll[data.icon].icon_id).index=index
    # row2=row2.split(factor=0.5)
    op = row2.operator(f'cp.remove_category_from_{category_type.lower()}', text='',
                                icon='PANEL_CLOSE')
    op.index = index
                
    op = row2.operator('cp.movecategory', text='',
                                icon='TRIA_UP')
    op.index = index
    op.category = category_type
    op.direction='UP'
    op = row2.operator('cp.movecategory', text='',
                                icon='TRIA_DOWN')
    op.index = index
    op.category = category_type
    op.direction='DOWN'
    return getattr(data, prop)
def message_box(layout, context, message,icon='NONE', width=None,alert=False):
    text_box = layout.column()
    text_box.alignment = "CENTER"
    width = width or context.region.width
    if not message:
        return
    icon_drawn=False
    for line in message.split("\n"):
        lines = textwrap.wrap(line, width / 10 if context else 100, break_long_words=False)
        for l in lines:
            trow = text_box.row()
            trow.alert=alert
            trow.alignment = "CENTER"
            trow.label(text=l,icon=icon if not icon_drawn else 'NONE')
            icon_drawn=True
def assign_addon_to_category(addon_name):
    # Path to the JSON configuration file
    json_file_path = os.path.join(os.path.dirname(__file__) ,"cp_config.json")
    if not os.path.exists(json_file_path):
        print(f"Configuration file not found: {json_file_path}")
        return
    
    # Load JSON data
    with open(json_file_path, 'r') as f:
        data = json.load(f)
    
    # Find the add-on's category
    category_name = None
    icon='NONE'
    for category, info in data.get("categories", {}).items():
        if addon_name in info.get("addons", []):
            category_name = category
            icon=info.get("icon")
            break
    
    if not category_name:
        print(f"Add-on '{addon_name}' not found in any category in the configuration.")
        return
    
    # Access the preferences workspace categories
    workspace_categories = preferences().workspace_categories
    
    # Find or create the category
    category = None
    for existing_category in workspace_categories:
        if existing_category.name == category_name:
            category = existing_category
            break
    
    if not category:
        category = workspace_categories.add()
        category.name = category_name
        category.icon=icon
    
    # Update the panels property with the add-on name
    panels = list(split_keep_substring(category.panels)) if category.panels else []
    if addon_name not in panels:
        panels.append(addon_name)
    category.panels = ','.join(panels)
    
    # print(f"Add-on '{addon_name}' assigned to category '{category_name}'.")
def assign_addon_to_category(addon_name,only_check=False):
    """
    Assigns an add-on to a category based on a JSON configuration file.
    Matches categories based on proportional similarity. If no match is found, creates a new category.

    Args:
        addon_name (str): The name of the add-on to assign.
    """
    # Path to the JSON configuration file
    json_file_path = os.path.join(os.path.dirname(__file__), "cp_config.json")
    if not os.path.exists(json_file_path):
        print(f"Configuration file not found: {json_file_path}")
        return

    # Load JSON data
    with open(json_file_path, 'r') as f:
        data = json.load(f)

    # Find the add-on's category from the JSON
    category_name = None
    json_icon = 'NONE'
    json_addons = []
    for category, info in data.get("categories", {}).items():
        if addon_name in info.get("addons", []):
            category_name = category
            json_icon = info.get("icon", "NONE")
            json_addons = info.get("addons", [])
            break

    if not category_name:
        # print(f"Add-on '{addon_name}' not found in any category in the configuration.")
        return

    # Access the preferences workspace categories
    workspace_categories = preferences().workspace_categories

    # Helper function to calculate proportional similarity
    def proportional_similarity(json_set, existing_set):
        if min(len(existing_set), len(json_set))<1:
            return 0
        common_items = len(json_set.intersection(existing_set))
        return common_items / min(len(existing_set), len(json_set))

    # Find the best matching category in the workspace
    best_match = None
    highest_similarity = 0

    for existing_category in workspace_categories:
        existing_addons = set(split_keep_substring(existing_category.panels) if existing_category.panels else [])
        json_addons_set = set(json_addons)
        ratio = proportional_similarity(json_addons_set, existing_addons)
        if ratio > highest_similarity:
            highest_similarity = ratio
            best_match = existing_category
    # Use the best match if similarity is greater than 50%
    if best_match and highest_similarity > 0.5:
        category = best_match
        if only_check:
            return category.name
        # print(f"Matched '{addon_name}' to existing category '{category.name}' with {highest_similarity:.2%} similarity.")
    else:
        if only_check:
            return None
        # Create a new category
        category = workspace_categories.add()
        category.name = category_name
        category.icon = json_icon
        print(f"Created new category '{category.name}' for '{addon_name}'.")

    # Update the panels property with the add-on name
    panels = list(split_keep_substring(category.panels)) if category.panels else []
    if addon_name not in panels:
        panels.append(addon_name)
    category.panels = ','.join(panels)
    return category.name
def assign_addon_to_category(addon_name,only_check=False):
    """
    Assigns an add-on to a category based on a JSON configuration file.
    Matches categories based on proportional similarity. If no match is found, creates a new category.

    Args:
        addon_name (str): The name of the add-on to assign.
    """
    # Path to the JSON configuration file
    json_file_path = os.path.join(os.path.dirname(__file__), "cp_database.json")
    json_backup_file_path = os.path.join(os.path.dirname(__file__), "cp_database_backup.json")
    if not os.path.exists(json_file_path):
        print(f"Configuration file not found: {json_file_path}")
        return

    # Load JSON data
    with open(json_file_path, 'r') as f:
        try:
            data = json.load(f)
        except:
            try:
                with open(json_backup_file_path, 'r') as f:
                    data = json.load(f)
            except:
                print("Error loading JSON file")
                return None

    # Find the add-on's category from the JSON
    category_name = None
    json_icon = 'NONE'
    json_addons = []
    for category, info in data.get("categories", {}).items():
        if addon_name in info.get("addons", []):
            category_name = category
            json_icon = info.get("icon", "NONE")
            json_addons = info.get("addons", [])
            break

    if not category_name:
        # print(f"Add-on '{addon_name}' not found in any category in the configuration.")
        return

    # Access the preferences workspace categories
    workspace_categories = preferences().workspace_categories

    # Helper function to calculate proportional similarity
    def proportional_similarity(json_set, existing_set):
        if min(len(existing_set), len(json_set))<1:
            return 0
        common_items = len(json_set.intersection(existing_set))
        return common_items / min(len(existing_set), len(json_set))

    # Find the best matching category in the workspace
    best_match = None
    highest_similarity = 0

    for existing_category in workspace_categories:
        existing_addons = set(split_keep_substring(existing_category.panels) if existing_category.panels else [])
        json_addons_set = set(json_addons)
        ratio = proportional_similarity(json_addons_set, existing_addons)
        if ratio > highest_similarity:
            highest_similarity = ratio
            best_match = existing_category
    # Use the best match if similarity is greater than 50%
    if best_match and highest_similarity > 0.5:
        category = best_match
        if only_check:
            return category.name
        # print(f"Matched '{addon_name}' to existing category '{category.name}' with {highest_similarity:.2%} similarity.")
    else:
        if only_check:
            return None
        # Create a new category
        category = workspace_categories.add()
        category.name = category_name
        category.icon = json_icon
        print(f"Created new category '{category.name}' for '{addon_name}'.")

    # Update the panels property with the add-on name
    panels = list(split_keep_substring(category.panels)) if category.panels else []
    if addon_name not in panels:
        panels.append(addon_name)
    category.panels = ','.join(panels)
    return category.name
def magic_setup():
    addons=get_addons_for_atl(None,None)
    addons=addons
    all_categorized_addons=[]
    for a in preferences().workspace_categories:
        all_categorized_addons.extend(split_keep_substring(a.panels))
    all_categorized_addons=split_keep_substring(preferences().addons_to_exclude)+all_categorized_addons
    for a in addons:
        if a[1] not in ('All','Unfiltered') and a[1] not in all_categorized_addons:
            assign_addon_to_category(a[1])
def get_addon_name_from_tab_name(tab_name,space=''):
    for addon in getattr(preferences(),f"addon_info_for_renaming{space}"):
        if addon.tab_name==tab_name:
            return addon.name
def draw_pie_layout(layout):
    
    row1=layout.row(align=True)
    row2=layout.row(align=True)
    row3=layout.row(align=True)
    row4=layout.row(align=True)
    row5=layout.row(align=True)
    
    row1.alignment='CENTER'
    row1_middle=row1.box()
    
    # row2.alignment='CENTER'
    t_row=row2.row(align=True)
    row2_left=t_row.row(align=True)
    row2_left=row2_left.row(align=True)
    row2_left.alignment='CENTER'
    row2_left=row2_left.box()
    row2_right=t_row.row(align=True)
    row2_right.alignment='CENTER'
    row2_right=row2_right.box()
    
    # row3.alignment='CENTER'
    t_row=row3.row(align=True)
    row3_left=t_row.row(align=True)
    row3_left.alignment='LEFT'
    row3_left=row3_left.box()
    row3_right=t_row.row(align=True)
    row3_right.alignment='RIGHT'
    row3_right=row3_right.box()
    
    t_row=row4.row(align=True)
    row4_left=t_row.row(align=True)
    row4_left=row4_left.row(align=True)
    row4_left.alignment='CENTER'
    row4_left=row4_left.box()
    row4_right=t_row.row(align=True)
    row4_right.alignment='CENTER'
    row4_right=row4_right.box()
    
    row5.alignment='CENTER'
    row5_middle=row5.box()
    return row3_left,row3_right,row5_middle,row1_middle,row2_left,row2_right,row4_left,row4_right