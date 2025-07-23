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
from webbrowser import get
import bpy
import re
import sys
import rna_keymap_ui
import importlib
from bpy.types import (PropertyGroup,Menu)
from bpy.app.handlers import persistent
import addon_utils
from bpy_extras.io_utils import ExportHelper,ImportHelper
from datetime import datetime
import bpy.utils.previews
from bpy.app.handlers import persistent
from .utils import *
import inspect



    

            
def reload_lists():
    if preferences().filtering_method=="Use N-Panel Filtering":
        #workspace_category_enabled(preferences().categories,bpy.context)
        # print("Loading Lists")
        load_renaming_list(bpy.context)
        load_reordering_list(bpy.context)
        load_renaming_list(bpy.context,space="IMAGE_EDITOR")
        load_reordering_list(bpy.context,space="IMAGE_EDITOR")
        load_renaming_list(bpy.context,space="NODE_EDITOR")
        load_reordering_list(bpy.context,space="NODE_EDITOR")
    return None
def load_enabled_addons(space_type):
    
    if preferences().load_addons_with_filtering and preferences().delayed_loading_code_injected:
        addons_to_load=[]
        for a in split_keep_substring(getattr(preferences(),f"addons_to_exclude{get_active_space(space_type)}"))+addons_to_exclude:
            try:
                if get_module_name_from_addon_name(a)!='--Unknown--':
                    addons_to_load.append(get_module_name_from_addon_name(a))
            except:
                pass
        for index,a in enumerate(getattr(preferences(),f"workspace_categories{get_active_space(space_type)}")):
            if getattr(preferences().categories,f'enabled{get_active_space(space_type)}_{index}',False):
                categories_string=split_keep_substring(a.panels)
                addons_to_load.extend([get_module_name_from_addon_name(a) for a in categories_string])
        needs_to_load=[]
        for addon in addons_to_load:
            if addon in ['Tool','View','Node','Options']:
                continue
            enabled=False
            try:
                pkg_name=get_full_module_name(addon)
                if pkg_name=='--Unknown--':
                    enabled=False
                else:
                    enabled=addon_utils.check(pkg_name)[1]
            except:
                pass
            if not enabled:
                needs_to_load.append(addon)
        bpy.ops.cp.enableaddons('EXEC_DEFAULT',addons_to_load=",".join(needs_to_load) if needs_to_load else 'SKIP,SKIP')
class PAP_Enable_Category(bpy.types.Operator):
    bl_idname = "cp.enablecategory"
    bl_label = ""
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    name: bpy.props.StringProperty()
    index: bpy.props.IntProperty()
    unfiltered: bpy.props.BoolProperty()
    @classmethod
    def description(self, context,properties):
        return getattr(preferences(),f"workspace_categories{get_active_space(context.area.type)}")[properties.index].name
    def invoke(self, context, event):
        if not preferences().filtering_method=="Use N-Panel Filtering":
            enabled=[getattr(context.workspace.category_indices,f'enabled{get_active_space(context.area.type)}_{i}') for i in range(50) if getattr(context.workspace.category_indices,f'enabled_{i}')]
            
            if not event.shift:
                for a in range(50):
                    if a!=self.index:
                        setattr(context.workspace.category_indices,f"enabled{get_active_space(context.area.type)}_{a}",False)        
            if len(enabled)>1 and not event.shift:
                setattr(context.workspace.category_indices,f"enabled{get_active_space(context.area.type)}_{self.index}",True)
            else:
                
                setattr(context.workspace.category_indices,f"enabled{get_active_space(context.area.type)}_{self.index}",not getattr(context.workspace.category_indices,f"enabled_{self.index}",False))
            workspace_category_enabled(context.workspace.category_indices,context)
        else:
            enabled=[getattr(preferences().categories,f'enabled{get_active_space(context.area.type)}_{i}') for i in range(50) if getattr(preferences().categories,f'enabled{get_active_space(context.area.type)}_{i}')]
            if not event.shift:
                for a in range(50):
                    if a!=self.index:
                        setattr(preferences().categories,f"enabled{get_active_space(context.area.type)}_{a}",False)
                setattr(context.scene,f"load_uncategorized{get_active_space(context.area.type)}",False)
            if len(enabled)>1 and not event.shift:
                setattr(preferences().categories,f"enabled{get_active_space(context.area.type)}_{self.index}",True)
            else:
                
                setattr(preferences().categories,f"enabled{get_active_space(context.area.type)}_{self.index}",not getattr(preferences().categories,f"enabled{get_active_space(context.area.type)}_{self.index}",False))
            load_enabled_addons(context.area.type)
            workspace_category_enabled(preferences().categories,context)
            
        return {"FINISHED"}

    
class CP_OT_Enable_UnCategoried(bpy.types.Operator):
    bl_idname = "cp.enableuncategorized"
    bl_label = ""
    
    @classmethod
    def description(self, context,properties):
        return "Uncategorized"
    def invoke(self, context, event):
        if not event.shift:
            for a in range(50):
                setattr(preferences().categories,f"enabled{get_active_space(context.area.type)}_{a}",False)
        self.index=0
        addons_to_enable=[]
        setattr(context.scene,f"load_uncategorized{get_active_space(context.area.type)}",not getattr(context.scene,f"load_uncategorized{get_active_space(context.area.type)}",False))
        self.space=get_active_space(context.area.type)
        addons=get_installed_addons_for_filtering_categories(self,context)
        for addon in addons:
            addon=addon[0]
            is_in_any_category=False
            for cat in getattr(preferences(),f"workspace_categories{get_active_space(context.area.type)}"):
                if addon in split_keep_substring(cat.panels):
                    is_in_any_category=True
                    break
            if not is_in_any_category:
                if addon not in split_keep_substring(getattr(preferences(),f"addons_to_exclude{get_active_space(context.area.type)}"))+addons_to_exclude:
                    addons_to_enable.append(addon)
        
        setattr(context.scene,f"uncategorized_addons{get_active_space(context.area.type)}",",".join(addons_to_enable))
        # print(context.scene.uncategorized_addons)
        workspace_category_enabled(preferences().categories,context)
        return {"FINISHED"}