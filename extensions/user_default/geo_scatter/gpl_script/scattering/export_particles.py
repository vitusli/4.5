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
# oooooooooooo                                               .
# `888'     `8                                             .o8
#  888         oooo    ooo oo.ooooo.   .ooooo.  oooo d8b .o888oo
#  888oooo8     `88b..8P'   888' `88b d88' `88b `888""8P   888
#  888    "       Y888'     888   888 888   888  888       888
#  888       o  .o8"'88b    888   888 888   888  888       888 .
# o888ooooood8 o88'   888o  888bod8P' `Y8bod8P' d888b      "888"
#                           888
#                          o888o
################################################################################################s


import bpy

import json
import os
import random

from .. ui import ui_templates
from .. resources.icons import cust_icon
from .. translations import translate
from .. utils.override_utils import mode_override
from .. utils.extra_utils import get_from_uid
from .. utils.str_utils import word_wrap

#   .oooooo.                                               .
#  d8P'  `Y8b                                            .o8
# 888      888 oo.ooooo.   .ooooo.  oooo d8b  .oooo.   .o888oo  .ooooo.  oooo d8b
# 888      888  888' `88b d88' `88b `888""8P `P  )88b    888   d88' `88b `888""8P
# 888      888  888   888 888ooo888  888      .oP"888    888   888   888  888
# `88b    d88'  888   888 888    .o  888     d8(  888    888 . 888   888  888
#  `Y8bood8P'   888bod8P' `Y8bod8P' d888b    `Y888""8o   "888" `Y8bod8P' d888b
#               888
#              o888o


class SCATTER5_OT_export_to_json(bpy.types.Operator):

    bl_idname  = "scatter5.export_to_json"
    bl_label   = translate("Export .Json")
    bl_description = translate("Export the selected scatter-system(s) visible in the viewport as a new '.json' file. This file contains important transforms information about each of your scatter's instances. You can then use this data in a game engine for example. If you don't know what is a '.json' file and how to decode it, please ignore this operator")

    filepath: bpy.props.StringProperty(subtype="FILE_PATH", options={"SKIP_SAVE",},)
    filename : bpy.props.StringProperty(subtype="FILE_NAME", options={"SKIP_SAVE",},)
    popup_menu: bpy.props.BoolProperty(default=True, options={"SKIP_SAVE", "HIDDEN"})
    
    def invoke(self, context, event):

        scat_scene = bpy.context.scene.scatter5 
        emitter    = scat_scene.emitter
        psys_sel   = emitter.scatter5.get_psys_selected()

        if (len(psys_sel)==0):
            if (self.popup_menu):
                bpy.ops.scatter5.popup_menu(title=translate("Export Failed"), msgs=translate("No Scatter-System(s) Selected\nPlease select scatters first in the lister interface"), icon="ERROR",)
            return {'FINISHED'}

        desktop = os.path.join(os.path.expanduser("~"),"Desktop",)
        if (os.path.exists(desktop)):
              self.filepath = os.path.join(desktop,"MyExport.json")
        else: self.filename = "MyExport.json"
        
        context.window_manager.fileselect_add(self)
        
        return {'RUNNING_MODAL'}

    def execute(self, context):
            
        
        if (not self.filename):
            self.filename = "MyExport.json"
            
        if os.path.isdir(self.filepath):
            self.filepath = os.path.join(self.filepath, self.filename)
            
        if (not self.filepath.endswith(".json")):
            self.filepath += ".json"

        #Create directories if they don't exist
        directory = os.path.dirname(self.filepath)
        if (not os.path.exists(directory)):
            try: os.makedirs(directory)
            except OSError as e:
                if (self.popup_menu):
                    bpy.ops.scatter5.popup_menu(title=translate("Export Failed"), msgs=translate("Failed to create directory"), icon="ERROR",)
                return {'CANCELLED'}
            
        scat_scene = bpy.context.scene.scatter5 
        emitter    = scat_scene.emitter
        psys_sel   = emitter.scatter5.get_psys_selected()

        #temporary hide 
        hidde_displays = {p.name:p.s_display_allow for p in psys_sel}
        for p in psys_sel:
            p.s_display_allow = False

        #get large dict of processed psys info by psyname
        dic = {p.name: p.get_instancing_info(processed_data=True) for p in psys_sel}

        #write dict to json in disk
        with open(self.filepath, 'w') as f:
            json.dump(dic, f, indent=4)

        #restore display 
        for n,v in hidde_displays.items(): 
            p = emitter.scatter5.particle_systems.get(n)
            if (p is not None): 
                p.s_display_allow = v

        #Great Success!
        if (self.popup_menu):
            bpy.ops.scatter5.popup_menu(title=translate("Success!"), msgs=translate("Export Successful"), icon="CHECKMARK", )

        return {'FINISHED'}


def to_objects(psys):

    from .. import utils

    #return value
    exported_colls = []
    
    #get large dict of processed psys info by psyname
    dic = {p.name:p.get_instancing_info(processed_data=True) for p in psys}

    #Create export collection
    utils.coll_utils.setup_scatter_collections()
    exp_coll = utils.coll_utils.create_new_collection("Geo-Scatter Export",  parent="Geo-Scatter")
    
    #optimize by hiding the collection
    exp_coll_hid = exp_coll.hide_viewport
    exp_coll.hide_viewport = True 

    #Link created instances
    for PsyName in dic.keys():
        psy_exp_coll = utils.coll_utils.create_new_collection(f"ToObjects: {PsyName}", parent=exp_coll,)
        exported_colls.append(psy_exp_coll)
        utils.coll_utils.collection_clear(psy_exp_coll)

        d = dic[PsyName]
        for k,v in d.items():
            obj = bpy.data.objects.get(v["name"])
            mesh = obj.data

            inst = bpy.data.objects.new(name=obj.name+"."+k, object_data=mesh)
            inst.location=v["location"]
            inst.rotation_euler=v["rotation_euler"] 
            inst.scale=v["scale"] 
            psy_exp_coll.objects.link(inst)
            
        continue

    #restore previously hidden
    exp_coll.hide_viewport = exp_coll_hid
    
    return exported_colls

def to_mesh(psys):
    
    from .. import utils
    from .. resources import directories

    #return value
    exported_colls = []
    
    #Create export collection
    exp_coll = utils.coll_utils.create_new_collection("Geo-Scatter Export",  parent="Geo-Scatter",)
    #create a new temporary collection holding the scatter_obj we want to merge
    tmp_coll = utils.coll_utils.create_new_collection(".Geo-Scatter merge temp", parent=exp_coll,)
    
    for p in psys:
        
        #clear existing objs in the tmp coll    
        utils.coll_utils.collection_clear(tmp_coll)
        
        #link it's scat object
        tmp_coll.objects.link(p.scatter_obj)

        #create new export collection
        psy_exp_coll = utils.coll_utils.create_new_collection(f"ToMesh: {p.name}", parent=exp_coll,)
        exported_colls.append(psy_exp_coll)
        utils.coll_utils.collection_clear(psy_exp_coll)
        
        #Create a new merge modifiers on empty obj
        oname = f"ToMesh: {p.name}"
        o = bpy.data.objects.get(oname)
        if (o):
            bpy.data.objects.remove(o)
        o = utils.create_utils.point(f"ToMesh: {p.name}", psy_exp_coll)
        m = utils.import_utils.import_and_add_geonode(o, mod_name="ScatterMerge", node_name=".ScatterMerge", blend_path=directories.addon_merge_blend,)
        m["Input_4"] = tmp_coll

        #and apply mod
        with mode_override(selection=[o], active=o, mode="OBJECT",):
            bpy.ops.object.modifier_apply(modifier=m.name)

        #need adjust uv, fix devs issues
        for attribute in o.data.attributes:
            if ((attribute.domain=='CORNER') and (attribute.data_type=="FLOAT2")):
                o.data.attributes.active = attribute
                # #No longer needed in 3.5 ??
                # with mode_override(selection=[o], active=o, mode="OBJECT",):
                #     bpy.ops.geometry.attribute_convert(mode="UV_MAP")
                break
        
        continue
    
    #remove tmp coll
    bpy.data.collections.remove(tmp_coll)
    
    return exported_colls


class SCATTER5_OT_export_to_objects(bpy.types.Operator):

    bl_idname      = "scatter5.export_to_objects"
    bl_label       = translate("Export to Objects")
    bl_description = translate("Export the Selected Scatter-system(s) visible in the viewport as blender instances object in a newly created export collection.")
    bl_options     = {'INTERNAL','UNDO',}

    obj_session_uid : bpy.props.IntProperty()
    option : bpy.props.EnumProperty(
        name=translate("Option"),
        description=translate("What would you like to do with the scatter-system(s) once they've been converted? Would you like to preserve them?"),
        default="hide_original_systems", 
        items=( ("hide_original_systems",translate("Hide Them"),"","RESTRICT_VIEW_ON",0),
                ("remove_original_systems",translate("Delete Them"),"","TRASH",1),
              ),
        )
    merge_to_mesh : bpy.props.BoolProperty(
        name=translate("Merge as One Mesh"),
        default=False,
        options={"SKIP_SAVE",},
        )
    in_collection_instance : bpy.props.BoolProperty(
        name=translate("As a collection instance object"),
        description=translate("Create a collection instance object out of the freshly new exports collections."),
        default=False,
        )
    select_output : bpy.props.BoolProperty(
        name=translate("Select the export in the viewport"),
        default=True,
        )
    select_maxlen : bpy.props.IntProperty(
        name=translate("Maximum Selected"),
        default=9_999,
        min=0,
        )
    
    popup_menu : bpy.props.BoolProperty(default=True, options={"SKIP_SAVE",},)
    
    def invoke(self, context, event):

        self.emitter = get_from_uid(self.obj_session_uid)
        if (not self.emitter):
            bpy.ops.scatter5.popup_menu(title=translate("Action Impossible"), msgs=translate("No Emitters Defined"), icon="ERROR",)
            return {'FINISHED'}
        
        if (not self.emitter.scatter5.get_psys_selected()):
            bpy.ops.scatter5.popup_menu(title=translate("Action Impossible"), msgs=translate("No Scatter-System(s) Selected"), icon="ERROR",)
            return {'FINISHED'}
        
        if (self.merge_to_mesh):
            for p in self.emitter.scatter5.get_psys_selected():
                count = p.get_scatter_count(self, state="viewport", viewport_unhide=False)
                if (count==0):
                    bpy.ops.scatter5.popup_menu(title=translate("Action Impossible"), msgs=translate("Some of your Scatter-System(s) Don't seem to appear in the viewport"), icon="ERROR",)
                    return {'FINISHED'}
        
        return bpy.context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout

        box, is_open = ui_templates.box_panel(layout, 
            panelopen_propname="ui_dialog_export_to_objects", #INSTRUCTION:REGISTER:UI:BOOL_NAME("ui_dialog_export_to_objects");BOOL_VALUE(1)
            panel_icon="FILTER",
            panel_name=translate("Selected-System(s) to Objects"),
            )
        if is_open:

            sep = box.row()
            s1 = sep.separator(factor=0.2)
            s2 = sep.column()
            s3 = sep.separator(factor=0.2)
            
            word_wrap(string=translate("We are about to convert the selected system(s) to real blender instance objects. Please note that this operation might potentially create hundreds of thousands of objects, and blender might not have the ability to deal with that."), layout=s2, alignment="LEFT", max_char=50,)
            
            s2.separator()
            
            col = s2.column(align=True)
            col.label(text=translate("What shall we do with the Scatter-System(s)?"))
            col.prop(self,"option",text="")
            
            s2.separator()
            
            s2.prop(self,"merge_to_mesh")
            if (self.merge_to_mesh):
                word_wrap(string=translate("Warning, merging thousands of objects is extremely process intensive. Make sure to save your .blend file before doing such an operation."), alert=True, layout=s2, alignment="LEFT", max_char=50,)
                s2.separator(factor=0.6)
            
            s2.prop(self,"in_collection_instance")
            
            s2.prop(self,"select_output")
            if (self.select_output):
                row = s2.row()
                row.separator(factor=0.5)
                row.scale_y = 0.9
                row.prop(self,"select_maxlen")
                
            s2.separator(factor=0.6)
            
        return None

    def execute(self, context):
        
        from .. import utils
        
        emitter  = self.emitter
        psys_sel = emitter.scatter5.get_psys_selected()
        
        if (self.select_output):
            for o in bpy.context.selected_objects:
                try: o.select_set(False)
                except: pass
                
        #temporary hide 
        hidde_displays = {p.name:p.s_display_allow for p in psys_sel}
        for p in psys_sel:
            p.s_display_allow = False
            
        if (self.merge_to_mesh):
              created_colls = to_mesh(psys_sel)
        else: created_colls = to_objects(psys_sel)
        
        #select some items in coll, to signify changes visually to user
        if (self.select_output):
            for coll in created_colls:
                if (coll.objects):
                    if (self.merge_to_mesh):
                        for o in coll.objects:
                            try: o.select_set(True)
                            except: pass
                    else:
                        if (len(coll.objects)<self.select_maxlen):
                            for o in coll.objects:
                                try: o.select_set(True)
                                except: pass
                        else:
                            for o in random.sample(coll.objects[:], self.select_maxlen):
                                try: o.select_set(True)
                                except: pass
                    continue
            
        #restore display 
        for n,v in hidde_displays.items(): 
            p = emitter.scatter5.particle_systems.get(n)
            if (p is not None): 
                p.s_display_allow = v
                
        #hide remove depending on user choice
        if (self.option=="hide_original_systems"):
            for p in psys_sel:
                p.hide_viewport = p.hide_render = True
        elif (self.option=="remove_original_systems"):
            bpy.ops.scatter5.remove_system(method="selection", undo_push=False, emitter_name=self.emitter.name) 

        #option to create coll instance
        empts = []
        if (self.in_collection_instance):
            expcoll = bpy.data.collections["Geo-Scatter Export"]
            #hide the coll
            for coll in created_colls:
                utils.coll_utils.set_collection_view_layers_exclude(coll, scenes="all", hide=True,)
                emtname = f"ToCollInstance:{coll.name.split(':')[-1]}"
                emt = bpy.data.objects.get(emtname)
                if (emt is None):
                    emt = bpy.data.objects.new(name=emtname, object_data=None)
                emt.instance_type = 'COLLECTION'
                emt.instance_collection = coll
                if (emt not in expcoll.objects[:]):
                    expcoll.objects.link(emt)
                if (self.select_output):
                    try: emt.select_set(True)
                    except: pass
                empts.append((emt,len(coll.objects)))
                continue
                
        #Great Success!
        if (self.popup_menu):
            _s = self
            def draw(self, context):
                nonlocal _s, empts, created_colls
                layout = self.layout
                layout.label(text=translate("The following items have been created:"),icon="ZOOM_ALL")
                if (_s.in_collection_instance):
                    for emt,nbr in empts:
                        layout.label(text=f'“{emt.name}” {translate("Containing")} {nbr:,} {translate("Object(s)")}', icon="OUTLINER_OB_GROUP_INSTANCE")
                elif (_s.merge_to_mesh):
                    for coll in created_colls:
                        for o in coll.objects:
                            layout.label(text=f'“{o.name}” {translate("Containing")} {len(o.data.vertices):,} {translate("Verts")}', icon="OUTLINER_OB_MESH")    
                else:
                    for coll in created_colls:
                        layout.label(text=f'“{coll.name}” {translate("Containing")} {len(coll.objects):,} {translate("Object(s)")}', icon="OUTLINER_COLLECTION")
                return  None
            bpy.context.window_manager.popup_menu(draw, title=translate("Export Successful"), icon="CHECKMARK")
            

        return {'FINISHED'}
    


#           oooo
#           `888
#  .ooooo.   888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
# d88' `"Y8  888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
# 888        888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
# 888   .o8  888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
# `Y8bod8P' o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'


classes = (
    
    SCATTER5_OT_export_to_json,
    SCATTER5_OT_export_to_objects,

    )