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

import bpy
import sys
import rna_keymap_ui
import importlib
from bpy.types import (PropertyGroup,Menu)
from bpy.app.handlers import persistent
import addon_utils
from bpy_extras.io_utils import ExportHelper,ImportHelper
import bpy.utils.previews
from bpy.app.handlers import persistent
from .utils import *
from .DropDownsAndPie import *
from .workspace_filtering import *
from .Preferences import *
import inspect
from .addon_update_checker import register,unregister
from . import export_addons_list
import functools
from . import guide_ops
bl_info = {
    "name": "CleanPanels vfxMed",
    "author": "Amandeep and Vectorr66",
    "description": "Panels and Workspace Manager",
    "blender": (3,6,0),
    "version": (7,0,3),
    "warning": "https://rantools.github.io/clean-panels/",
    "category": "Object",
}


class PAP_Opened_Panels(PropertyGroup):
    name: bpy.props.StringProperty()
    pap_opened_panels:bpy.props.StringProperty()
    opened_before: bpy.props.BoolProperty(default=False)
class PAP_Call_Favorites_Pie(bpy.types.Operator):
    bl_idname = "cp.callfavoritespie"
    bl_label = "Favorites"
    bl_description= "Open Favorites Pie Menu"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    def invoke(self, context, event):
        bpy.ops.wm.call_menu_pie(name="PAP_MT_Favorites_Pie_Menu")
        return {"FINISHED"}


class PAP_MT_Favorites_Pie_Menu(Menu):
    bl_label = "Clean Panels"

    def draw(self, context):
        layout = self.layout
        layout=layout.menu_pie()
        favorites=[a.name for a in preferences().favorites]
        if len(favorites)>8 :
            for a in favorites[:2]:
                # if "----focuspanel" in a:
                    layout.operator("cp.focuspanel",text=a).name=a
                # elif "----piepanel" in a:
                #     text=a.replace("----piepanel----True","").replace("----piepanel----False","")+"(Pie Panel)"
                #     if "----True" in a:
                #         base_type = bpy.types.Panel
                #         for typename in dir(bpy.types):
                #             try:
                #                 bl_type = getattr(bpy.types, typename,None)
                #                 if issubclass(bl_type, base_type):
                #                     if bl_type.__name__==a.replace("----piepanel----True","").replace("----piepanel----False",""):
                #                         text=bl_type.bl_label+"(Pie Panel)"
                #             except:
                #                 pass
                #     op=layout.operator("cp.popuppanel",text=text)
                #     op.name=a.replace("----piepanel----True","").replace("----piepanel----False","")
                #     op.call_panel='----True' in a
            column=layout.column()
            for a in favorites[7:]:
                # if "----focuspanel" in a:
                    column.operator("cp.focuspanel",text=a).name=a
                # elif "----piepanel" in a:
                #     text=a.replace("----piepanel----True","").replace("----piepanel----False","")+"(Pie Panel)"
                #     if "----True" in a:
                #         base_type = bpy.types.Panel
                #         for typename in dir(bpy.types):
                #             try:
                #                 bl_type = getattr(bpy.types, typename,None)
                #                 if issubclass(bl_type, base_type):
                #                     if bl_type.__name__==a.replace("----piepanel----True","").replace("----piepanel----False",""):
                #                         text=bl_type.bl_label+"(Pie Panel)"
                #             except:
                #                 pass
                #     op=column.operator("cp.popuppanel",text=text)
                #     op.name=a.replace("----piepanel----True","").replace("----piepanel----False","")
                #     op.call_panel='----True' in a
            for a in favorites[2:7]:
                # if "----focuspanel" in a:
                    layout.operator("cp.focuspanel",text=a).name=a
                # elif "----piepanel" in a:
                #     text=a.replace("----piepanel----True","").replace("----piepanel----False","")+"(Pie Panel)"
                #     if "----True" in a:
                #         base_type = bpy.types.Panel
                #         for typename in dir(bpy.types):
                #             try:
                #                 bl_type = getattr(bpy.types, typename,None)
                #                 if issubclass(bl_type, base_type):
                #                     if bl_type.__name__==a.replace("----piepanel----True","").replace("----piepanel----False",""):
                #                         text=bl_type.bl_label+"(Pie Panel)"
                #             except:
                #                 pass
                #     op=layout.operator("cp.popuppanel",text=text)
                #     op.name=a.replace("----piepanel----True","").replace("----piepanel----False","")
                #     op.call_panel='----True' in a
        else:
            for a in favorites:
                # if "----focuspanel" in a:
                    layout.operator("cp.focuspanel",text=a).name=a
                # elif "----piepanel" in a:
                #     text=a.replace("----piepanel----True","").replace("----piepanel----False","")+"(Pie Panel)"
                #     if "----True" in a:
                #         base_type = bpy.types.Panel
                #         for typename in dir(bpy.types):
                #             try:
                #                 bl_type = getattr(bpy.types, typename,None)
                #                 if issubclass(bl_type, base_type):
                #                     if bl_type.__name__==a.replace("----piepanel----True","").replace("----piepanel----False",""):
                #                         text=bl_type.bl_label+"(Pie Panel)"
                #             except:
                #                 pass
                #     op=layout.operator("cp.popuppanel",text=text)
                #     op.name=a.replace("----piepanel----True","").replace("----piepanel----False","")
                #     op.call_panel='----True' in a
class PAP_Call_Panels_Sub_Pie(bpy.types.Operator):
    bl_idname = "cp.callpanelssubpie"
    bl_label = "Clean Panels"
    bl_description= "Open Panels Sub Pie Menu"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    name: bpy.props.StringProperty()
    def invoke(self, context, event):
        context.scene.pap_last_panel_subcategory=self.name
        bpy.ops.wm.call_menu_pie(name="PAP_MT_Panels_Sub_Pie_Menu")
        return {"FINISHED"}


class PAP_MT_Panels_Sub_Pie_Menu(Menu):
    bl_label = "Clean Panels"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = "INVOKE_DEFAULT"
        pieMenu = layout.menu_pie()
        category=context.scene.pap_last_panel_subcategory
        base_type = bpy.types.Panel
        count=0
        # op=pieMenu.operator("cp.popuppanel",text=bl_type.bl_label)
                                            # op.name=bl_type.__name__
                                            # op.call_panel=True
                                            # count+=1
        panels_to_draw=[]
        panels_with_parents=[]
        base_type = bpy.types.Panel
        for typename in dir(bpy.types):
            
            try:
                bl_type = getattr(bpy.types, typename,None)
                if issubclass(bl_type, base_type):
                    if getattr(bl_type,"bl_category","None")==category or getattr(bl_type,"backup_category","None")==category or get_module_name(bl_type)==get_module_name_from_addon_name(category):
                        
                        if "." not in getattr(bl_type,"bl_context","None") and getattr(bl_type,"bl_parent_id","None")=="None":
                            if (getattr(bl_type,"bl_context","")=="" or getattr(bl_type,"bl_context","None")==get_current_context(context)) and (getattr(bl_type,"backup_region","None")=='UI' or getattr(bl_type,"bl_region_type","None")=='UI')  and (getattr(bl_type,'backup_space',"None")==context.space_data.type or getattr(bl_type,'bl_space_type',"None")==context.space_data.type):
                                if getattr(bl_type,'poll',None):
                                    if bl_type.poll(context):
                                        if "layout" in inspect.getsource(bl_type.draw) or "draw" in inspect.getsource(bl_type.draw):
                                            
                                            panels_to_draw.append((bl_type,False))
                                else:
                                    if "layout" in inspect.getsource(bl_type.draw) or "draw" in inspect.getsource(bl_type.draw):
                                            
                                            panels_to_draw.append((bl_type,False))
                    if getattr(bl_type,"bl_parent_id","None")!="None":
                        #print(bl_type)
                        panels_with_parents.append(bl_type)
            except Exception as e:
                if str(e)!="issubclass() arg 1 must be a class":
                    pass
                    #print(str(e))
        panels_to_draw=sorted(panels_to_draw,key=lambda x: getattr(x[0],'bl_order',0))
        panels_with_parents=sorted(panels_with_parents,key=lambda x: getattr(x,'bl_order',0))
        #print(panels_to_draw,panels_with_parents)
        for bl_type in panels_with_parents:
            try:
                #print(getattr(bl_type,"bl_parent_id","None"))
                # print([getattr(a,"bl_idname","None") for a,b in panels_to_draw]+[getattr(a,"__name__","None") for a,b in panels_to_draw])
                if getattr(bl_type,"bl_parent_id","None") in [getattr(a,"bl_idname",getattr(a,'__name__',"None")) for a,b in panels_to_draw]:
                    
                    if getattr(bl_type,'poll',None):
                        if bl_type.poll(context):
                            if "layout" in inspect.getsource(bl_type.draw) or "draw" in inspect.getsource(bl_type.draw)  or "draw" in inspect.getsource(bl_type._original_draw) :
                                
                                if getattr(bl_type,"bl_parent_id","None") in [getattr(a,"bl_idname",getattr(a,'__name__',"None")) for a,b in panels_to_draw]:
                                    panels_to_draw.insert([getattr(a,"bl_idname",getattr(a,'__name__',"None")) for a,b in panels_to_draw].index(getattr(bl_type,"bl_parent_id","None"))+1,(bl_type,True))
                                else:
                                    #print([getattr(a,"bl_idname",getattr(a,'__name__',"None")) for a in panels_to_draw],bl_type,getattr(bl_type,"bl_parent_id","None"))
                                    panels_to_draw.append((bl_type,True))
                    else:
                        if "layout" in inspect.getsource(bl_type.draw) or "draw" in inspect.getsource(bl_type.draw)  or "draw" in inspect.getsource(bl_type._original_draw) :
                                if getattr(bl_type,"bl_parent_id","None") in [getattr(a,"bl_idname",getattr(a,'__name__',"None")) for a,b in panels_to_draw]:
                                    panels_to_draw.insert([getattr(a,"bl_idname",getattr(a,'__name__',"None")) for a,b in panels_to_draw].index(getattr(bl_type,"bl_parent_id","None"))+1,(bl_type,True))
                                else:
                                    #print([getattr(a,"bl_idname",getattr(a,'__name__',"None")) for a in panels_to_draw],bl_type,getattr(bl_type,"bl_parent_id","None"))
                                    panels_to_draw.append((bl_type,True))
            except Exception as e:
                if str(e)!="issubclass() arg 1 must be a class":
                    pass
        if len(panels_to_draw)>8:
            for p,has_parent in panels_to_draw[:2]:
                op=pieMenu.operator("cp.popuppanel",text=p.bl_label)
                op.name=p.__name__
                op.call_panel=True
                count+=1
            column=pieMenu.column()
            for p,has_parent in panels_to_draw[7:]:
                op=column.operator("cp.popuppanel",text=p.bl_label)
                op.name=p.__name__
                op.call_panel=True
                count+=1
            for p,has_parent in panels_to_draw[2:7]:
                op=pieMenu.operator("cp.popuppanel",text=p.bl_label)
                op.name=p.__name__
                op.call_panel=True
                count+=1
        else:
            for p,has_parent in panels_to_draw:
                op=pieMenu.operator("cp.popuppanel",text=p.bl_label)
                op.name=p.__name__
                op.call_panel=True
                count+=1
            #pieMenu.popover(a.bl_idname, text=a.bl_label)
class PAP_MT_Panels_List(Menu):
    bl_label = "Focus Panel"
    
    def draw(self, context):
        categories=set([])
        registered_panels=[]
        for typename in dir(bpy.types):
            
            try:
                bl_type = getattr(bpy.types, typename,None)
                if issubclass(bl_type, bpy.types.Panel):
                    if preferences().filtering_method=="Use N-Panel Filtering":
                        if getattr(bl_type,"backup_space","None")==context.area.type and getattr(bl_type,'bl_category',None) :
                            if hasattr(bl_type,'poll'):
                                if bl_type.poll(context):
                                    registered_panels.append(bl_type)
                            else:
                                registered_panels.append(bl_type)
                    else:
                        if getattr(bl_type,"bl_space_type","None")==context.area.type and getattr(bl_type,'bl_category',None) :
                            if hasattr(bl_type,'poll'):
                                if bl_type.poll(context):
                                    registered_panels.append(bl_type)
                            else:
                                registered_panels.append(bl_type)
            except:
                pass
        
        # print(len(registered_panels))
        for a in registered_panels:
            if getattr(a,'bl_category',"Unknown")!=preferences().holder_tab_name:
                categories.add(getattr(a,'bl_category',"Unknown"))
            
            elif not preferences().only_show_unfiltered_panels:
                if getattr(a,'renamed_category',None):

                    categories.add(getattr(a,'renamed_category',"Unknown"))
                else:
                    if getattr(a,'backup_category',None):
                        categories.add(getattr(a,'backup_category',"Unknown"))
        layout = self.layout   
        count=0
        row=layout.row()
        if not preferences().filter_internal_tabs and bpy.app.version>=(4,1,0):
            if context.area.type=='NODE_EDITOR':
                categories.add("Node")
                categories.add("Tool")
                categories.add("View")
                categories.add("Options")
            elif context.area.type=='IMAGE_EDITOR':
                categories.add("Image")
                categories.add("Tool")
                categories.add("View")
                
            elif context.area.type=='VIEW_3D':
                categories.add("Item")
                categories.add("Tool")
                categories.add("View")
        categories=sorted(list(categories),key=str.casefold)
        if preferences().sort_focus_menu_based_on_clicks:
            if os.path.isfile(os.path.join(os.path.dirname(os.path.dirname(__file__)),"CP-FocusPanelClickCount.txt")):
                with open(os.path.join(os.path.dirname(os.path.dirname(__file__)),"CP-FocusPanelClickCount.txt"), "r") as file:
                        clicks_dict=json.load(file)
                clicks_dict=clicks_dict.get(context.workspace.name,dict())
                categories=sorted(list(categories),key=lambda x:1/clicks_dict.get(x,1))
        categories_to_remove=[]
        if getattr(preferences(),f"focus_panel_categories{get_active_space(context.area.type)}"):
            for fp in getattr(preferences(),f"focus_panel_categories{get_active_space(context.area.type)}"):
                if [a for a in split_keep_substring(fp.panels) if a in categories]:
                    col=row.column()
                            
                    if fp.panels:
                        col.label(text=fp.name)
                        col.separator()
                        for p in split_keep_substring(fp.panels):
                            if p not in ["Item",'Focused','Unknown']:
                            # if p not in ["Item",'Tool','View','Focused','Unknown']:
                                if p in categories:
                                    col.operator_context = "INVOKE_DEFAULT"
                                    col.operator("cp.focuspanel",text=p).name=p
                                    categories_to_remove.append(p)
                                    # categories.remove(p)
            col=row.column()
            col.label(text="Others")
            col.separator()
        categories=[a for a in categories if a not in categories_to_remove]
        for a in categories:
            panels_to_skip=["Item",'Focused','Unknown'] if bpy.app.version<(4,1,0) else ["Focused","Unknown"]
            if a not in panels_to_skip:
            # if a not in ["Item",'Tool','View','Focused','Unknown']:  
                
                if count%10==0 and (count!=0 or not getattr(preferences(),f"focus_panel_categories{get_active_space(context.area.type)}")):

                    col=row.column()
                    col.label(text="")
                    col.separator()
                col.operator_context = "INVOKE_DEFAULT"
                col.operator("cp.focuspanel",text=a).name=a
                count+=1
        col.operator_context = "INVOKE_DEFAULT"
        col.operator("cp.focuspanel",text="Turn OFF").name="Turn OFF"
search_results=[]
def focus_panel_search_results(self,context):
    
    return search_results
def select_focus_panel(self,context):
    bpy.ops.cp.focuspanel('INVOKE_DEFAULT',name=self.focus_panel_search)
class CP_OT_Quick_Focus(bpy.types.Operator):
    bl_idname = "cp.quickfocus"  
    bl_label = "Quick Focus"
    bl_property = "my_enum"
    my_enum: bpy.props.EnumProperty(name="Focus Panel", description="", items=focus_panel_search_results)
    
    def execute(self,context):
        bpy.ops.cp.focuspanel('INVOKE_DEFAULT',name=self.my_enum)
        return {'FINISHED'}
    def invoke(self, context,event):
        registered_panels=[]
        self.categories=set()
        for typename in dir(bpy.types):
            
            try:
                bl_type = getattr(bpy.types, typename,None)
                if issubclass(bl_type, bpy.types.Panel):
                    if getattr(bl_type,"backup_space","None")==context.area.type and getattr(bl_type,'bl_category',None) :
                        if hasattr(bl_type,'poll'):
                            if bl_type.poll(context):
                                registered_panels.append(bl_type)
                        else:
                            registered_panels.append(bl_type)
            except:
                pass
        # print(registered_panels)
        
        for a in registered_panels:
            if getattr(a,'bl_category',"Unknown")!=preferences().holder_tab_name:
                self.categories.add(getattr(a,'bl_category',"Unknown"))
            
            elif not preferences().only_show_unfiltered_panels:
                if getattr(a,'renamed_category',None):

                    self.categories.add(getattr(a,'renamed_category',"Unknown"))
                else:
                    if getattr(a,'backup_category',None):
                        self.categories.add(getattr(a,'backup_category',"Unknown"))
        global search_results
        search_results=[(a,a,a) for  a in self.categories]
        wm = context.window_manager
        
        wm.invoke_search_popup(self)
        return {'FINISHED'}
class PAP_MT_Panels_Pie_Menu(Menu):
    bl_label = "Clean Panels"

    def draw(self, context):
        panel_list={}
        #categories_string=sentence = ''.join(preferences().panel_categories.split())
        #categories=categories_string)
        name=context.scene.pap_last_panel_subcategory
        categories=[]
        for a in preferences().panel_categories:
            if a.name==name:
                #categories_string= ''.join(a.panels.split())
                categories=split_keep_substring(a.panels)
                categories=[a.strip() for a in categories]
        layout = self.layout
        layout.operator_context = "INVOKE_DEFAULT"
        pieMenu = layout.menu_pie() if not preferences().use_verticle_menu else layout
        if len(categories)>8 and not preferences().use_verticle_menu:
            for index,a in enumerate(categories[:2]):
                pieMenu.operator("cp.callpanelspie",text=a).name=a
            column=pieMenu.column()
            for index,a in enumerate(categories[7:]):
                column.operator("cp.callpanelspie",text=a).name=a
            for index,a in enumerate(categories[2:7]):
                pieMenu.operator("cp.callpanelspie",text=a).name=a
        else:
            count=0
            for a in categories:
                count+=1
                #print(a)
                #pieMenu.popover(a.bl_idname, text=a.bl_label)
                pieMenu.operator("cp.popuppanel",text=a).name=a
                if count==8:
                    break
            #pieMenu.operator("cp.callpanelssubpie",text=a).name=a
class PAP_MT_Panel_Categories_Pie_Menu(Menu):
    bl_label = "Clean Panels"

    def draw(self, context):
        categories=[a.name for a in preferences().panel_categories]
        layout = self.layout
        layout.operator_context = "INVOKE_DEFAULT"
        pieMenu = layout.menu_pie()
        if len(categories)>8:
            for index,a in enumerate(categories[:2]):
                pieMenu.operator("cp.callpanelspie",text=a).name=a
            column=pieMenu.column()
            for index,a in enumerate(categories[7:]):
                column.operator("cp.callpanelspie",text=a).name=a
            for index,a in enumerate(categories[2:7]):
                pieMenu.operator("cp.callpanelspie",text=a).name=a
        else:
            count=0
            for a in categories:
                count+=1
                pieMenu.operator("cp.callpanelspie",text=a).name=a
                if count==8:
                    break

import pkgutil
class PAP_Call_Panels_Pie(bpy.types.Operator):
    bl_idname = "cp.callpanelspie"
    bl_label = "Clean Panels"
    bl_description="Open Panels Pie Menu"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    name:bpy.props.StringProperty()
    def invoke(self, context, event):
        
        context.scene.pap_last_panel_subcategory=self.name
        count=0
        single_name=None
        name=context.scene.pap_last_panel_subcategory
        categories=[]
        for a in preferences().panel_categories:
            if a.name==name:
                #categories_string= ''.join(a.panels.split())
                categories=split_keep_substring(a.panels)
                categories=[a.strip() for a in categories]
        count=0
        for a in categories:
            single_name=a
            count+=1
            if count==8:
                break
        if count>1:
            if preferences().use_verticle_menu:
                bpy.ops.wm.call_menu(name="PAP_MT_Panels_Pie_Menu")
            else:
                bpy.ops.wm.call_menu_pie(name="PAP_MT_Panels_Pie_Menu")
        else:
            if single_name:
                if preferences().pop_out_style=='Pie-PopUp':
                    context.scene.pap_last_panel_subcategory=single_name
                    bpy.ops.wm.call_menu_pie(name="PAP_MT_Panels_Sub_Pie_Menu")
                else:
                    bpy.ops.cp.popuppanel('INVOKE_DEFAULT',name=single_name,call_panel=False)
        return {"FINISHED"}
class PAP_Toggle_Filter(bpy.types.Operator):
    bl_idname = "cp.togglefiltering"
    bl_label = "Toggle Filter"
    bl_description="Toggle Filtering ON/OFF"
    def invoke(self, context, event):
        if not preferences().filtering_method=="Use N-Panel Filtering":
            context.workspace.category_indices.filter_enabled=not context.workspace.category_indices.filter_enabled
        else:
            preferences().categories.filter_enabled=not preferences().categories.filter_enabled
        context.area.tag_redraw()
        return {"FINISHED"}
class PAP_Call_Panels_Categories_Pie(bpy.types.Operator):
    bl_idname = "cp.callcategoriespie"
    bl_label = "Panels Pie Menu"
    bl_description="Open Panels Pie Menu"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    def invoke(self, context, event):
        bpy.ops.wm.call_menu_pie(name="PAP_MT_Panel_Categories_Pie_Menu")
        return {"FINISHED"}
class PAP_MT_Load_Addons(Menu):
    bl_label = "Load Addons"

    def draw(self, context):
        categories=[a.name for a in preferences().addon_loading_categories]
        layout = self.layout
        layout.operator_context = "INVOKE_DEFAULT"
        layout.operator("cp.loadaddonset",text="All").all=True
        
        for i,a in enumerate(categories):
            op=layout.operator("cp.loadaddonset",text=a)
            op.index=i
            op.all=False
        layout.separator()
        layout.operator("cp.loadaddonset",text="Excluded from Filtering").excluded=True
        layout.operator("cp.loadaddonfromselection")
class PAP_Call_Load_Addons_Set_Menu(bpy.types.Operator):
    bl_idname = "cp.callloadaddonsetmenu"
    bl_label = "Load Addons Menu"
    bl_description="Load addons from delayed-loading categories."
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    def invoke(self, context, event):
        bpy.ops.wm.call_menu(name="PAP_MT_Load_Addons")
        # if preferences().addon_loading_categories and 'addons_to_load' in inspect.signature(addon_utils.reset_all).parameters:
        #     bpy.ops.wm.call_menu(name="PAP_MT_Load_Addons")
        # else:
        #     bpy.ops.cp.loadaddonset('INVOKE_DEFAULT',all=True)
        return {"FINISHED"}
class PAP_MT_Workspace_Categories_Pie_Menu(Menu):
    bl_label = "Workspace Filters"

    def draw(self, context):
        categories=[a.name for a in preferences().panel_categories]
        layout = self.layout
        layout.operator_context = "INVOKE_DEFAULT"
        pieMenu = layout.menu_pie()
        pcoll= icon_collection["icons"]
        if len(preferences().workspace_categories)>8:
            for index,a in enumerate(preferences().workspace_categories[:2]):
                if context.workspace.category_indices.filter_enabled:
                    if a.icon in [b for b,_,_,_,_ in ALL_ICONS_ENUM]:
                        pieMenu.operator("cp.enablecategory",text=a.name,icon=a.icon,depress=getattr(context.workspace.category_indices,f'enabled_{index}')).index=index
                    else:
                        pieMenu.operator("cp.enablecategory",text=a.name,icon_value=pcoll[a.icon].icon_id,depress=getattr(context.workspace.category_indices,f'enabled_{index}')).index=index
            column=pieMenu.column()
            for index,a in enumerate(preferences().workspace_categories[7:]):
                if context.workspace.category_indices.filter_enabled:
                    if a.icon in [b for b,_,_,_,_ in ALL_ICONS_ENUM]:
                        column.operator("cp.enablecategory",text=a.name,icon=a.icon,depress=getattr(context.workspace.category_indices,f'enabled_{index+7}')).index=index+7
                    else:
                        column.operator("cp.enablecategory",text=a.name,icon_value=pcoll[a.icon].icon_id,depress=getattr(context.workspace.category_indices,f'enabled_{index+7}')).index=index+7
            for index,a in enumerate(preferences().workspace_categories[2:7]):
                if context.workspace.category_indices.filter_enabled:
                    if a.icon in [b for b,_,_,_,_ in ALL_ICONS_ENUM]:
                        pieMenu.operator("cp.enablecategory",text=a.name,icon=a.icon,depress=getattr(context.workspace.category_indices,f'enabled_{index+2}')).index=index+2
                    else:
                        pieMenu.operator("cp.enablecategory",text=a.name,icon_value=pcoll[a.icon].icon_id,depress=getattr(context.workspace.category_indices,f'enabled_{index+2}')).index=index+2
        else:
            for index,a in enumerate(preferences().workspace_categories):
                if context.workspace.category_indices.filter_enabled:
                    if a.icon in [b for b,_,_,_,_ in ALL_ICONS_ENUM]:
                        pieMenu.operator("cp.enablecategory",text=a.name,icon=a.icon,depress=getattr(context.workspace.category_indices,f'enabled_{index}')).index=index
                    else:
                        pieMenu.operator("cp.enablecategory",text=a.name,icon_value=pcoll[a.icon].icon_id,depress=getattr(context.workspace.category_indices,f'enabled_{index}')).index=index
            #row.prop(context.workspace.category_indices,f'enabled_{index}',text=a.name if a.icon=='NONE' else "",icon=a.icon)
class PAP_Call_Workspace_Categories_Pie(bpy.types.Operator):
    bl_idname = "cp.callwspie"
    bl_label = "Workspace Pie Menu"
    bl_description="Open Filtering Pie Menu"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    def invoke(self, context, event):
        context.workspace.category_indices.filter_enabled=True
        bpy.ops.wm.call_menu_pie(name="PAP_MT_Workspace_Categories_Pie_Menu")
        return {"FINISHED"}
class PAP_Call_Panels_List(bpy.types.Operator):
    bl_idname = "cp.callpanelslist"
    bl_label = "Focused Panels"
    bl_description="Open Panels List and choose which panel to display in the Focused Tab"
    def invoke(self, context, event):
        bpy.ops.wm.call_menu(name="PAP_MT_Panels_List")
        return {"FINISHED"}
def call_load_post_functions(mod):
    for a in bpy.app.handlers.load_post:
        if mod in str(a.__module__):
            num_params = len(inspect.signature(a).parameters)
            try:
                a(*([None] * num_params))
            except Exception as e:
                print("Could not call post load function",a,"\nFor module",mod,"\nError",e)
class CP_Load_Addons(bpy.types.Operator):
    bl_idname = "cp.enableaddons"
    bl_label = "Load Addons"
    bl_description="Load All Addons"
    addons_to_load: bpy.props.StringProperty(default='',options={'SKIP_SAVE'})
    def execute(self, context):
        if self.addons_to_load!='SKIP,SKIP':
            print("Loading Addons",self.addons_to_load)
            load_addons(addons_to_load=self.addons_to_load.split(',') if self.addons_to_load else '')
            # for mod in self.addons_to_load.split(','):
            #     call_load_post_functions(mod)
        else:
            pass
        # bpy.app.timers.register(read_keymaps,first_interval=5)
        return {"FINISHED"}
class CP_Load_Addons_Set(bpy.types.Operator):
    bl_idname = "cp.loadaddonset"
    bl_label = "Load Addons"
    bl_description="Load Addons in this Set"
    all: bpy.props.BoolProperty(default=False)
    excluded: bpy.props.BoolProperty(default=False)
    index: bpy.props.IntProperty(default=0)
    def execute(self, context):
        addons_to_load = []
        filter_enabled=getattr(preferences().categories,f'filter_enabled{get_active_space(context.area.type)}')
        if self.all:
            to_load=[a.__name__ for a in addon_utils.modules() if addon_utils.check(a.__name__)[0] and not addon_utils.check(a.__name__)[1]]
            ac = next((a for a in to_load if "autoconstraints" in a.lower()), None)
            if ac:
                to_load.remove(ac)
                load_addons(addons_to_load=[ac])
                bpy.app.timers.register(functools.partial(load_addons,"",self),first_interval=0.1)
            else:
                load_addons(addons_to_load="",op_class=self)
                # for mod in to_load:
                #     call_load_post_functions(mod)
                self.report({"INFO"}, "Loaded all Addons")
        
        else:
            if self.excluded:
                panels=preferences().addons_to_exclude
            else:
                cat=preferences().addon_loading_categories[self.index]
                panels = cat.panels
            categories_string = split_keep_substring(panels)
            addons_to_load.extend(
                [get_module_name_from_addon_name(a) for a in categories_string]
            )
            needs_to_load = []
            for addon in addons_to_load:
                enabled = False
                try:
                    pkg_name = get_full_module_name(addon)
                    if pkg_name == "--Unknown--":
                        enabled = False
                    else:
                        enabled = addon_utils.check(pkg_name)[1]
                    # print("Enabled", enabled, pkg_name)
                except:
                    pass
                if not enabled:
                    needs_to_load.append(addon)
            if needs_to_load:
                ac = next((a for a in needs_to_load if "autoconstraints" in a.lower()), None)
                if ac:
                    needs_to_load.remove(ac)
                    load_addons(addons_to_load=[ac,])
                    bpy.app.timers.register(functools.partial(load_addons,needs_to_load,self),first_interval=0.1)
                else:
                    if needs_to_load:
                        load_addons(addons_to_load=needs_to_load)
                # for mod in needs_to_load:
                #     call_load_post_functions(mod)
                    self.report(
                        {"INFO"},
                        f"Loaded {','.join(needs_to_load)} Addons from Set {cat.name if not self.excluded else 'Excluded'}",
                    )
            else:
                self.report({"INFO"}, "All addons in this set are already loaded")
        loadPreferences()
        if self.all:
            preferences().delayed_addons_loaded = True
            self.report({"INFO"}, "Loaded All addons")
        setattr(preferences().categories,f'filter_enabled{get_active_space(context.area.type)}',filter_enabled)
        bpy.app.timers.register(read_keymaps,first_interval=3)
        
        return {"FINISHED"}
class Temp_Collection_Property(bpy.types.PropertyGroup):
    name:bpy.props.StringProperty()
    enabled:bpy.props.BoolProperty()
    icon:bpy.props.StringProperty()
class CP_OT_Load_From_Selection(bpy.types.Operator):
    bl_idname = "cp.loadaddonfromselection"
    bl_label = "Select To Load"
    bl_description="Load Addons from selection"
    addons_to_load:bpy.props.CollectionProperty(type=Temp_Collection_Property)
    index:bpy.props.IntProperty(default=0,options={'SKIP_SAVE'})
    space:bpy.props.StringProperty()
    def draw(self,context):
        layout = self.layout
        layout.ui_units_x=30
        if len(self.addons_to_load)<1:
            layout.label(text="All addons are already loaded!",icon='INFO')
            return
        layout=layout.grid_flow(columns=5)
        for addon in self.addons_to_load:
            row=layout.row()
            row.prop(addon,"enabled",text=addon.name)
    def execute(self, context):
        addons_to_load=[]
        for addon in self.addons_to_load:
            if addon.enabled:
                module_name=get_module_name_from_addon_name(addon.name)
                addons_to_load.append(module_name)
        filter_enabled=getattr(preferences().categories,f'filter_enabled{get_active_space(context.area.type)}')
        load_addons(addons_to_load)
        loadPreferences()
        setattr(preferences().categories,f'filter_enabled{get_active_space(context.area.type)}',filter_enabled)
        bpy.app.timers.register(read_keymaps,first_interval=3)
        return {'FINISHED'}
    def invoke(self,context,event):
        self.index=0
        self.space=''
        self.addons_to_load.clear()
        addons=get_installed_addons(self,context)
        for addon in addons:
            module_name=get_module_name_from_addon_name(addon[1])
            full_module_name=get_full_module_name(module_name)
            if addon_utils.check(full_module_name)[0] and not addon_utils.check(full_module_name)[1]:
                t=self.addons_to_load.add()
                t.name=addon[1]
        return context.window_manager.invoke_props_dialog(self)
class CP_Warning(bpy.types.PropertyGroup):
    message:bpy.props.StringProperty(default="")
    hidden:bpy.props.BoolProperty(default=True)
    def draw(self,layout,context):
        if not self.hidden:
            row=layout.row(align=True)
            row=row.split(factor=0.95,align=True)
            row.alert=True
            row.label(text=context.scene.cp_warning.message,icon='ERROR')
            row.operator("cp.hide_warning",text="",icon="PANEL_CLOSE")
            
    def hide(self):
        self.hidden=True
    def show(self):
        self.hidden=False
class CP_OT_Hide_Warning(bpy.types.Operator):
    bl_idname="cp.hide_warning"
    bl_label="Hide Warning"
    def execute(self,context):
        context.scene.cp_warning.hide()
        return{'FINISHED'}
define_keymaps = [
    {"name": "3D View", "space_type": "VIEW_3D", "keymaps": [
        {"idname": "cp.callfavoritespie", "type": 'U', "value": "PRESS", "ctrl": True},
        {"idname": "cp.callcategoriespie", "type": 'R', "value": "PRESS", "alt": True},
        {"idname": "cp.togglefiltering", "type": 'F', "value": "PRESS"},
        {"idname": "cp.callwspie", "type": 'F', "value": "PRESS", "alt": True},
        {"idname": "cp.callpanelslist", "type": 'J', "value": "PRESS", "alt": True},
        {"idname": "cp.quickfocus", "type": 'F7', "value": "PRESS"},
    ]},
    {"name": "Node Editor", "space_type": "NODE_EDITOR", "keymaps": [
        {"idname": "cp.callpanelslist", "type": 'J', "value": "PRESS", "alt": True},
    ]},
    {"name": "Image", "space_type": "IMAGE_EDITOR", "keymaps": [
        {"idname": "cp.callpanelslist", "type": 'J', "value": "PRESS", "alt": True},
    ]},
]
def get_user_keymap_items(context, debug=False):
    """
    Check the user keymap for all expected addon keymaps.
    Find and return missing ones.
    """
    wm = context.window_manager
    kc = wm.keyconfigs.user

    missing_keymaps = []

    for km_def in define_keymaps:
        km_name = km_def["name"]
        space_type = km_def["space_type"]

        # Get the keymap
        km = kc.keymaps.get(km_name, None)
        if not km:
            missing_keymaps.extend(km_def["keymaps"])
            continue

        for kmi_def in km_def["keymaps"]:
            idname = kmi_def["idname"]

            # Check if the keymap item exists
            exists = any(
                kmi.idname == idname
                for kmi in km.keymap_items
            )

            if not exists:
                missing_keymaps.append(kmi_def)

    return missing_keymaps

class CP_OT_RestoreKeymaps(bpy.types.Operator):
    """
    Operator to restore missing keymaps for the addon.
    """
    bl_idname = "cp.restore_keymaps"
    bl_label = "Restore Missing Keymaps"
    bl_description = "Restore missing keymaps for the addon."
    def execute(self, context):
        wm = bpy.context.window_manager
        kc = wm.keyconfigs.user
        new_addon_keymaps = []
        if not kc:
            self.report({'WARNING'}, "No addon key configuration found.")
            return {'CANCELLED'}

        missing_keymaps = get_user_keymap_items(context)
        if not missing_keymaps:
            self.report({'INFO'}, "No missing keymaps found.")
            return {'FINISHED'}

        for km_def in define_keymaps:
            km_name = km_def["name"]
            space_type = km_def["space_type"]

            # Get or create the keymap
            km = kc.keymaps.get(km_name)
            if not km:
                km = kc.keymaps.new(name=km_name, space_type=space_type)
            for kmi_def in missing_keymaps:
                
                if kmi_def in km_def["keymaps"]:
                    idname = kmi_def["idname"]
                    type = kmi_def["type"]
                    value = kmi_def["value"]
                    ctrl = kmi_def.get("ctrl", False)
                    alt = kmi_def.get("alt", False)
                    ex=wm.keyconfigs.find_item_from_operator(idname)
                    kmi = km.keymap_items.new(idname, type=type, value=value, ctrl=ctrl, alt=alt)
                    addon_keymaps.append((km, kmi))
                    new_addon_keymaps.append((km, kmi))
        wm.keyconfigs.update()
        # for km, kmi in new_addon_keymaps:
        #     km.restore_item_to_default(kmi)
        # Recheck missing keymaps to verify success
        self.report({'INFO'}, "Missing keymaps restored successfully.")
        return {'FINISHED'}
classes = (  # CP_PT_Custom_Panel,
           CP_OT_RestoreKeymaps,
           BatchAssign,
           CP_OT_BatchAssignCategories,
           CP_OT_AutoSetup,
           CP_Show_Help,
           CP_Warning,CP_OT_Hide_Warning,
       CP_OT_SaveKeyMap,
    PAP_Call_Load_Addons_Set_Menu,
    PAP_OT_searchPopupForAddonLoading,
    PAP_MT_Load_Addons,
    CP_Load_Addons_Set,
    CP_OT_Reset_Config,
    CP_Load_Addons,
    CP_OT_Inject_Delayed_Start_Code,
    PAP_OT_Set_ATL,
    CP_OT_Fetch_Categories,
    PAP_MT_Favorites_Pie_Menu,
    PAP_Call_Favorites_Pie,
    Temp_Collection_Property,
    CP_OT_Quick_Focus,
    PAP_OT_Remove_Category_FP,
    PAP_OT_Remove_Category_Addon_Loading,
    PAP_OT_searchPopupForFP,
    CP_OT_Reset_Tab_Name,
    PAP_Call_Panels_List,
    PAP_MT_Panels_List,
    PAP_OT_Open_Focused_Panel,
    PAP_Addon_Info,
    PAP_Addon_Description,
    AddonDescriptionInfo,
    PAP_Addon_Edit_Description,
    CP_OT_Move_Addon_In_Category,
    CP_UL_Category_Order_List,
    PAP_OT_Reorder_Category,
    CP_OT_Inject_Tracking_Code,
    CP_OT_Change_Category,
    CP_OT_Load_Addons_List_For_Renaming,
    CP_UL_Addons_Order_List_For_Renaming,
    AddonInfoRename,
    PAP_OT_Search_Dropdown,
    CP_OT_Open_Preferences,
    CP_OT_Remove_Panel,
    CP_OT_Move_Category,
    PAP_OT_Remove_Panel,
    PAP_OT_Icon_Picker,
    CP_OT_Save_Config,
    CP_OT_Export_Config,
    CP_OT_Import_Config,
    AddonInfo,
    CP_OT_Inject_Code,
    CP_OT_Clear_Order,
    CP_OT_Move_Addon,
    CP_OT_Load_Addons_List,
    CP_UL_Addons_Order_List,
    Category_Indices,
    PAP_Opened_Panels,
    CP_Panel_Category,
    PAPPrefs,
    PAP_OT_PopUp,
    PAP_MT_Panels_Pie_Menu,
    PAP_Call_Panels_Pie,
    PAP_Toggle_Filter,
    PAP_OT_CP,
    PAP_OT_CP_Reorder,
    PAP_OT_searchPopupForExclusion,
    PAP_Call_Panels_Sub_Pie,
    PAP_MT_Panels_Sub_Pie_Menu,
    PAP_OT_Add_Category,
    PAP_OT_Remove_Category,
    PAP_MT_Panel_Categories_Pie_Menu,
    PAP_Call_Panels_Categories_Pie,
    PAP_Import_Workspaces,
    PAP_OT_searchPopup,
    PAP_OT_PopUp_Full_Panel,
    PAP_OT_searchPopupForDropDown,
    PAP_OT_Remove_Category_Dropdown,
    PAP_OT_Remove_Category_Workspace,
    PAP_OT_searchPopupForWorkspace,
    PAP_OT_Change_Icon,
    PAP_Enable_Category,
    PAP_Call_Workspace_Categories_Pie,
    PAP_MT_Workspace_Categories_Pie_Menu,
    PAP_OT_Make_FP_Categories_from_Filtering,
    CP_OT_Enable_UnCategoried,
    PAP_OT_Make_Delayed_Categories_from_Filtering,
    CP_OT_Load_From_Selection,
    CP_OT_Open_Config_Directory,
    CP_OT_EditFavoriteFocusPanel,
    CP_OT_Remove_FavoriteFocusPanel,
    CP_OT_Add_FavoriteFocusPanel,
    CP_OT_Update_Database,
    CP_OT_Reorder_Favorites
)
addon_keymaps = []
def get_dropdown_categories(self, context):
    return [("None","No Dropdowns","None")]+[(a.name,a.name,a.name) for a in preferences().dropdown_categories]
def get_workspace_categories(self, context):
    return [("None","None","None")]+[(a.name,a.name,a.name) for a in preferences().workspace_categories]


def pap_active_dropdown_category_changed(self, context):
    categories=[]
    for b in bpy.context.preferences.addons.keys():
        try:
            #print(sys.modules[b])
            mod=sys.modules[b].__name__
            #print(mod)
            module=importlib.import_module(mod)
            mods=[module]
            try:
                for loader, module_name, is_pkg in pkgutil.walk_packages(module.__path__):
                    _module = loader.find_module(module_name).load_module(module_name)
                    mods.append(_module)
            except:
                pass
            #print("Mods",mods)
            for m in mods:
                #print(m)
                for name, cls in inspect.getmembers(m, inspect.isclass):
                    if issubclass(cls,bpy.types.Panel):
                        if mod=='PowerSave':
                            print(cls.__name__)
                        if cls.is_registered:
                            print(b,cls.__name__)
        except Exception as e:
            print(e)
    for a in preferences().dropdown_categories:
            if a.name==context.scene.pap_active_dropdown_category:
                categories=split_keep_substring(a.panels)
                categories=[a.strip() for a in categories]
    base_type = bpy.types.Panel
    for category in categories:
        for typename in dir(bpy.types):
            
            try:
                bl_type = getattr(bpy.types, typename,None)
                if issubclass(bl_type, base_type):
                    if getattr(bl_type,"bl_category","None")==category:
                        #bpy.utils.unregister_class(bl_type)
                        bl_type.bl_context="None"
                        #bpy.utils.register_class(bl_type)
            except:
                pass

def pap_active_workspace_category_changed(self, context):
    if context.workspace.pap_active_workspace_category=="None":
        context.workspace.use_filter_by_owner = False
    else:
        context.workspace.use_filter_by_owner = True
        categories=[]
        for a in preferences().workspace_categories:
                if a.name==context.workspace.pap_active_workspace_category:
                    #categories_string= ''.join(a.panels.split())
                    categories=split_keep_substring(a.panels)
                    categories=[a.strip() for a in categories]
        for a in [__package__] + categories[:]:
            try:
                a=get_correct_module_name(sys.modules[a].__name__)
                if a not in [c.name for c in context.workspace.owner_ids] and a in bpy.context.preferences.addons.keys():
                    bpy.ops.wm.owner_enable(owner_id=a)
            except:
                pass
        for a in split_keep_substring(preferences().addons_to_exclude)+addons_to_exclude:
            try:
                if a not in [c.name for c in context.workspace.owner_ids] and a in bpy.context.preferences.addons.keys():
                    
                    bpy.ops.wm.owner_enable(owner_id=a)
            except:
                pass
        for b in bpy.context.preferences.addons.keys():
            try:
                #print(b)
                mod = sys.modules[b]
                if get_correct_module_name(mod.__name__) not in categories+[__package__] and get_correct_module_name(mod.__name__) in [a.name for a in context.workspace.owner_ids]:
                    if get_correct_module_name(mod.__name__) not in split_keep_substring(preferences().addons_to_exclude)+addons_to_exclude:
                        #print("Disable",get_correct_module_name(mod.__name__))
                        bpy.ops.wm.owner_disable(owner_id=get_correct_module_name(mod.__name__))
            except:
                    pass
import requests
def getCurrentVersion():
    try:
        response = requests.get(
            "https://github.com/rantools/clean-panels/blob/main/README.md", timeout=4)
        response = str(response.content)
        brokenResponse = response[response.index("Current Version")+17:]
        version = brokenResponse[:5]
        brokenResponse = response[response.index("Custom Message")+16:]
        message = brokenResponse[:brokenResponse.index("]")]

        return version, message
    except:
        return "Disconnected", "Disconnected"

@persistent
def setupdatestatus(scene):
    global last_workspace
    last_workspace=''
    current_version="".join([s for s in str(sys.modules['CleanPanels'].bl_info['version']) if s.isdigit()])
    #current_version=str(sys.modules['Clean Panels'].bl_info['version']).replace("(","").replace(")","").replace(", ","")
    og_online_version,message=getCurrentVersion()
    online_version=og_online_version.replace(".","")
    if online_version!="Disconnected":
        if int(online_version)<int(current_version):
            bpy.context.scene.cp_update_status ="Clean Panels is Up To Date! (Beta)" 
        elif int(online_version)==int(current_version):
            bpy.context.scene.cp_update_status ="Clean Panels is Up To Date!" 
        else:
            bpy.context.scene.cp_update_status=f"Update Available! (v{og_online_version})"
    else:
        print("Couldn't check for Updates")
last_workspace=''
LOAD_ADDONS=False
# def reset_all(addons_to_load=[]):
#     print("addon to load",addons_to_load)
#     if addons_to_load:
#         for a in addons_to_load:
#             pkg=get_full_module_name(a)
#             print("PKG",pkg)
#             print(addon_utils.check(pkg)[1])
#             if addon_utils.check(pkg)[0] and not addon_utils.check(pkg)[1]:
#                 print("Enable ",pkg)
#                 addon_utils.enable(pkg)
#     else:
#         for a in addon_utils.modules():
#             if addon_utils.check(a.__name__)[0] and not addon_utils.check(a.__name__)[1]:
#                 addon_utils.enable(a.__name__)

def load_addons(addons_to_load=[],op_class=None):
    import addon_utils
    # if "batch_ops" in addons_to_load:
        
    #     addons_to_load.remove("batch_ops")
    #     if not addons_to_load:
    #         addons_to_load.append("--Unknown--")
    #     return
    addons_loaded_init=[a.__name__ for a in addon_utils.modules() if addon_utils.check(a.__name__)[0] and addon_utils.check(a.__name__)[1]]
    if bpy.app.version>=(4,0,0):
        if 'addons_to_load' in inspect.signature(addon_utils.reset_all).parameters:
            addon_utils.reset_all(cp=True,addons_to_load=addons_to_load)
        else:
            addon_utils.reset_all(cp=True)
        # reset_all(addons_to_load=addons_to_load)
        # Exception to make sure modular workspaces ui is displayed
        try:
            if "Modular Workspaces" in [addon_utils.module_bl_info(a)['name'] for a in addon_utils.modules()]:
                full_name_mw=next((a.__name__ for a in addon_utils.modules() if addon_utils.module_bl_info(a)['name']=="Modular Workspaces"),None)
                if full_name_mw:
                    if addon_utils.check(full_name_mw)[1]:
                        addon_utils.enable(full_name_mw)
        except Exception:
            pass
        
    else:
        if 'addons_to_load' in inspect.signature(addon_utils.reset_all).parameters:
            addon_utils.reset_all(addons_to_load=addons_to_load)
        else:
            addon_utils.reset_all()
    addons_loaded=[a.__name__ for a in addon_utils.modules() if addon_utils.check(a.__name__)[0] and addon_utils.check(a.__name__)[1] and a.__name__ not in addons_loaded_init]
    print("Addons Loaded",addons_loaded)
    for mod in addons_to_load:
        call_load_post_functions(mod)
    try:
        if op_class:
            op_class.report(
                        {"INFO"},
                        f"Loaded {','.join(addons_to_load)} Addons",
                    )
    except Exception:
        pass
    
    if addons_loaded:
        # print(addons_loaded)
        reload_lists()
    global UI_UPDATE_COUNT
    UI_UPDATE_COUNT=0
    bpy.app.timers.register(keep_ui_enabled,first_interval=2)
def workspace_changed():
    
    
    if not preferences().filtering_per_workspace:
        # preferences().categories.filter_enabled=bpy.context.workspace.filter_enabled
        workspace_category_enabled(preferences().categories,bpy.context)
        return None
    global last_workspace
    if last_workspace!=bpy.context.workspace.name:
        last_workspace=bpy.context.workspace.name
        for a,_ in enumerate(preferences().workspace_categories):
            
            setattr(preferences().categories,f'enabled_{a}',f"{a}" in bpy.context.workspace.enabled_categories.split(','))
        preferences().categories.filter_enabled=bpy.context.workspace.filter_enabled

        workspace_category_enabled(preferences().categories,bpy.context)
    return 1
UI_UPDATE_COUNT=0
def keep_ui_enabled():
    global UI_UPDATE_COUNT
    UI_UPDATE_COUNT+=1
    draw_side_changed(preferences(),bpy.context)
    if UI_UPDATE_COUNT>10:
        return None
    return 2
def load_enabled_categories_addons(a=None,b=None):
    load_enabled_addons("VIEW_3D")
def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    export_addons_list.register()
    
    load_icons()
    guide_ops.register()
    bpy.types.Scene.pap_last_panel_category = bpy.props.StringProperty(default="")
    bpy.types.Scene.pap_last_panel_subcategory = bpy.props.StringProperty(default="Item")
    bpy.types.Scene.pap_opened_panels= bpy.props.CollectionProperty(type=PAP_Opened_Panels)
    bpy.types.Scene.pap_active_dropdown_category=bpy.props.EnumProperty(items=get_dropdown_categories,name="Dropdowns")
    bpy.types.WorkSpace.pap_active_workspace_category=bpy.props.EnumProperty(items=get_workspace_categories,name="Dropdowns",update=pap_active_workspace_category_changed)
    bpy.types.WorkSpace.category_indices=bpy.props.PointerProperty(type=Category_Indices)
    bpy.types.WorkSpace.enabled_categories=bpy.props.StringProperty(default='')
    bpy.types.WorkSpace.filter_enabled=bpy.props.BoolProperty(default=False)
    bpy.types.IMAGE_HT_tool_header.append(draw_filter_buttons)
    bpy.types.NODE_HT_header.append(draw_filter_buttons)
    
    # if not bpy.types.VIEW3D_MT_editor_menus.is_extended() or  draw_dropdowns not in bpy.types.VIEW3D_MT_editor_menus.draw._draw_funcs[:]:
    #     bpy.types.VIEW3D_MT_editor_menus.append(draw_dropdowns)
    # if not bpy.types.VIEW3D_HT_tool_header.is_extended() or  draw_before_editor_menu not in bpy.types.VIEW3D_HT_tool_header.draw._draw_funcs[:]:
    #     bpy.types.VIEW3D_HT_tool_header.prepend(draw_before_editor_menu)
    bpy.types.Scene.cp_warning=bpy.props.PointerProperty(type=CP_Warning)
    bpy.types.Scene.cp_update_status=bpy.props.StringProperty(default="Clean Panels is Up To Date!")
    bpy.types.Scene.addon_info=bpy.props.CollectionProperty(type=AddonInfo)
    bpy.types.Scene.addon_info_index= bpy.props.IntProperty(default=0,name="Selected Tab")
    bpy.types.Scene.temp_collection=bpy.props.CollectionProperty(type=Temp_Collection_Property)
    bpy.types.Scene.load_uncategorized=bpy.props.BoolProperty(default=False)
    bpy.types.Scene.load_uncategorized_image_editor=bpy.props.BoolProperty(default=False)
    bpy.types.Scene.load_uncategorized_node_editor=bpy.props.BoolProperty(default=False)
    bpy.types.Scene.uncategorized_addons=bpy.props.StringProperty(default="")
    bpy.types.Scene.uncategorized_addons_image_editor=bpy.props.StringProperty(default="")
    bpy.types.Scene.uncategorized_addons_node_editor=bpy.props.StringProperty(default="")
    # bpy.types.Scene.focus_panel_search=bpy.props.StringProperty(default='',update=select_focus_panel,search=focus_panel_search_results)
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon

    km = kc.keymaps.new(name="3D View", space_type="VIEW_3D")
    if kc:
        
        kmi = km.keymap_items.new(
            "cp.callfavoritespie",
            type='U',
            value="PRESS",ctrl=True
        )
        addon_keymaps.append((km, kmi))
        kmi = km.keymap_items.new(
            "cp.callcategoriespie",
            type='R',
            value="PRESS",alt=True
        )
        addon_keymaps.append((km, kmi))
        kmi = km.keymap_items.new(
            "cp.togglefiltering",
            type='F',
            value="PRESS"
        )
        addon_keymaps.append((km, kmi))
        kmi = km.keymap_items.new(
            "cp.callwspie",
            type='F',
            value="PRESS",alt=True
        )
        
        addon_keymaps.append((km, kmi))
        kmi = km.keymap_items.new(
            "cp.callpanelslist",
            type='J',
            value="PRESS",alt=True
        )
        
        addon_keymaps.append((km, kmi))
        kmi = km.keymap_items.new(
            "cp.quickfocus",
            type='F7',
            value="PRESS"
        )
        
        addon_keymaps.append((km, kmi))
        km = kc.keymaps.new(name="Node Editor", space_type="NODE_EDITOR")
        kmi = km.keymap_items.new(
            "cp.callpanelslist",
            type='J',
            value="PRESS",alt=True
        )
        
        addon_keymaps.append((km, kmi))
        km = kc.keymaps.new(name="Image", space_type="IMAGE_EDITOR")
        kmi = km.keymap_items.new(
            "cp.callpanelslist",
            type='J',
            value="PRESS",alt=True
        )
        
        addon_keymaps.append((km, kmi))
    preferences().config_corrupted=False
            
    bpy.app.handlers.load_post.append(loadPreferences)
    bpy.app.handlers.load_post.append(load_enabled_categories_addons)
    # bpy.app.handlers.load_post.append(setupdatestatus)
    loadPreferences()
    
    bpy.app.timers.register(workspace_changed,persistent=True)
    # bpy.app.timers.register(keep_ui_enabled,persistent=True)
    preferences().delayed_addons_loaded=False
    # bpy.app.timers.register(load_addons,first_interval=5)
    # if not bpy.app.timers.is_registered(toggle_filtering_OnOff):
    #toggle_filtering_OnOff()
    if not check_for_delayed_loading_injection():
        if not bpy.app.timers.is_registered(reload_lists):
            bpy.app.timers.register(reload_lists, first_interval=5,persistent=True)
    addon_update_checker.register("04d5812b014ad59d8121e2fa934bc913")
def unregister():
    preferences().config_corrupted=False
    save_keymaps()
    create_backup_configs()
    savePreferences()
    from bpy.utils import unregister_class

    for cls in reversed(classes):
        unregister_class(cls)
    export_addons_list.unregister()
    guide_ops.unregister()
    for (km, kmi) in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    try:
        bpy.types.IMAGE_HT_tool_header.remove(draw_filter_buttons)
    except:
        pass
    try:
        bpy.types.NODE_HT_header.remove(draw_filter_buttons)
    except:
        pass
    try:
        bpy.types.VIEW3D_HT_header.remove(draw_dropdowns)
    except:
        pass
    try:
        bpy.types.VIEW3D_MT_editor_menus.remove(draw_dropdowns)
    except:
        pass
    try:
        bpy.types.VIEW3D_HT_tool_header.remove(draw_filter_buttons)
    except:
        pass
#inject_code(os.path.join(os.path.dirname(__file__),'test.py'))
    try:
        bpy.app.handlers.load_post.remove(loadPreferences)
        bpy.app.handlers.version_update.remove(reload_lists)
        bpy.app.handlers.load_post.remove(load_enabled_categories_addons)
    except:
        pass
    # try:
    #     bpy.app.handlers.load_post.remove(setupdatestatus)
    # except:
    #     pass
    if bpy.app.timers.is_registered(reload_lists):
        bpy.app.timers.unregister(reload_lists)
    if bpy.app.timers.is_registered(workspace_changed):
        bpy.app.timers.unregister(workspace_changed)
    if bpy.app.timers.is_registered(keep_ui_enabled):
        bpy.app.timers.unregister(keep_ui_enabled)
    addon_update_checker.unregister()
if __name__ == "__main__":
    register()
