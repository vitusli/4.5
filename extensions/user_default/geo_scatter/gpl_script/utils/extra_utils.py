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


import bpy 

import mathutils
import bpy_extras
    
from . event_utils import get_event
from .. translations import translate

from .. widgets.infobox import SC5InfoBox, generic_infobox_setup


#NOTE Here's it's a bunch of function that i store here because i do not know where to store them 

def dprint(string, depsgraph=False,):
    """debug print"""

    from ... __init__ import addon_prefs

    if (not addon_prefs().debug):
        return None
        
    if (depsgraph and (not addon_prefs().debug_depsgraph)):
        return None
    
    return print(string)


def get_from_uid(uid, collection=None):
    """get an item from it's given collection datablock from it's `session_uid` property
    by default collection will be bpy.data.objects"""
    
    if (collection is None):
        collection = bpy.data.objects
    
    for itm in collection:
        _uid = getattr(itm,"session_uid",None)
        if (_uid==uid):
            return itm
        
    if (_uid is None):
        print("ERROR: get_any_from_sessuid() collection datablock provided doesnt support `session_uid` api")
    return None


def exec_line(strline, local_vars=None, global_vars=None):
    """execute (using the exec builtin fct) a given line of code, with a convenient name space setted up"""
    
    #define useful namespace
    
    import random, os
    from ... __init__ import addon_prefs, blend_prefs
    from .. ui.ui_notification import check_for_notifications
    from .. utils.coll_utils import set_collection_view_layers_exclude, setup_scatter_collections, ensure_scatter_collection_viewlayers, cleanup_scatter_collections
    from .. scattering.update_factory import update_camera_nodegroup
    
    
    C,D          = bpy.context, bpy.data
    scat_scene   = bpy.context.scene.scatter5
    emitter      = scat_scene.emitter
    scat_ops     = scat_scene.operators
    scat_op_crea = scat_ops.create_operators
    scat_win     = bpy.context.window_manager.scatter5
    scat_data    = blend_prefs()
    psys         = emitter.scatter5.particle_systems if (emitter is not None) else []
    psys_sel     = emitter.scatter5. get_psys_selected() if (emitter is not None) else []
    psy_active   = emitter.scatter5.get_psy_active() if (emitter is not None) else None
    mod_active   = psy_active.get_scatter_mod(strict=True, raise_exception=False) if (psy_active) else None
    group_active = emitter.scatter5.get_group_active() if (emitter is not None) else None
        
    if hasattr(bpy.context,"pass_ui_arg_lib_obj"):
        path_arg = bpy.context.pass_ui_arg_lib_obj.name
    
    assert 'get_from_uid' in globals()
    
    #merge given locals/globals with current ones
    
    current_globals = globals()
    if (global_vars is not None):
        current_globals.update(global_vars)
        
    current_locals = locals()
    if (local_vars is not None):
        current_locals.update(local_vars)
        
    #execute the line
    try:
        r = exec(strline, current_globals, current_locals)
    except Exception as e:
        print(f"ERROR: exec_line('{strline}'), An Exception occured")
        raise Exception(e)
    
    return r


def has_duplicates(collection):
    """is there duplicates in the given collection of items?"""
    return len(collection) != len(set(collection))

def get_duplicates(collection):
    """return the duplicates of the given collection of items"""
    if (not has_duplicates(collection)):
        return []
    seen = set()
    return [x for i, x in enumerate(collection) if x in seen or seen.add(x) and collection[:i].count(x) > 0]


# FLAGDIC = {}
# def timer(msg="", init=False):
#     """timer decorator"""

#     #get modules
#     global FLAGDIC
#     import time, datetime

#     #launch timer
#     if (init==True):
#         print("TimerInit")
#         FLAGDIC = {}
#         FLAGDIC[0] = time.time()
#     else: 
#         i=1
#         while i in FLAGDIC:
#             i+=1
#         FLAGDIC[i] = time.time()
#         totdelay = datetime.timedelta(seconds=FLAGDIC[i]-FLAGDIC[0]).total_seconds()
#         lasdelay = datetime.timedelta(seconds=FLAGDIC[i]-FLAGDIC[i-1]).total_seconds()

#         print(f"Timer{i:02} ||| Total: {totdelay:.2f}s ||| FromLast: {lasdelay:.2f}s ||| '{msg}'")
    
#     return None


def all_3d_viewports():
    """return generator of all 3d view space"""

    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if (area.type=="VIEW_3D"):
                for space in area.spaces:
                    if (space.type=="VIEW_3D"):
                        yield space

def all_3d_viewports_shading_type():
    """return generator of all shading type str"""

    for space in all_3d_viewports():
        yield space.shading.type

def is_rendered_view():
    """check if is rendered view in a 3d view somewhere"""

    return 'RENDERED' in all_3d_viewports_shading_type()


#   .oooooo.   oooo
#  d8P'  `Y8b  `888
# 888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
# 888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
# 888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
# `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#  `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'


class SCATTER5_OT_property_toggle(bpy.types.Operator):
    """useful for some cases where we don't want to register an undo when we toggle a bool property"""
    #DO NOT REGISTER TO UNDO ON THIS OPERATOR, GOAL IS TO IGNORE UNDO WHEN CHANGING A PROP

    bl_idname      = "scatter5.property_toggle"
    bl_label       = ""
    bl_description = ""    

    api : bpy.props.StringProperty()
    description : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)

    @classmethod
    def description(cls, context, properties): 
        return properties.description

    def execute(self, context):

        if (self.api==""):
            return {'FINISHED'}

        from ... __init__ import addon_prefs
        
        scat_ui     = bpy.context.window_manager.scatter5.ui
        scat_scene  = bpy.context.scene.scatter5
        emitter     = scat_scene.emitter 
        psy_active  = emitter.scatter5.get_psy_active() if emitter else None
            
        subset_prop = self.api.split('.')[-1]

        #toggle via exec, not sure it's possible to use get/set here
        exec(f'{self.api} = not {self.api}')

        return {'FINISHED'}


class SCATTER5_OT_dummy(bpy.types.Operator):
    """dummy placeholder, might be used in interface related code"""

    bl_idname      = "scatter5.dummy"
    bl_label       = ""
    bl_description = ""

    description : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)

    @classmethod
    def description(cls, context, properties): 
        return properties.description

    def execute(self, context):
        return {'FINISHED'}

        
class SCATTER5_OT_exec_line(bpy.types.Operator):
    """quickly execute simple line of code, witouth needing to create a new operator"""

    bl_idname      = "scatter5.exec_line"
    bl_label       = ""
    bl_description = ""

    api : bpy.props.StringProperty()
    description : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)
    undo : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)

    @classmethod
    def description(cls, context, properties): 
        return properties.description
    
    def execute(self, context):
        
        exec_line(self.api)

        #write undo?
        if (self.undo!=""):
            bpy.ops.ed.undo_push(message=self.undo, )

        return {'FINISHED'}


class SCATTER5_OT_set_solid_and_object_color(bpy.types.Operator):

    bl_idname      = "scatter5.set_solid_and_object_color"
    bl_label       = ""
    bl_description = translate("Set the context viewport shading type to solid/object to see the particle systems colors")

    mode : bpy.props.StringProperty() #"set"/"restore"
    
    restore_dict = {}

    def execute(self, context):

        space_data = bpy.context.space_data 
        spc_hash   = hash(space_data)
        shading    = space_data.shading

        if (self.mode=="set"):

            self.restore_dict[spc_hash] = {"type":shading.type, "color_type":shading.color_type}
            shading.type = 'SOLID'
            shading.color_type = 'OBJECT'

        elif ((self.mode=="restore") and (spc_hash in self.restore_dict)):

            shading.type = self.restore_dict[spc_hash]["type"]
            shading.color_type = self.restore_dict[spc_hash]["color_type"]
            del self.restore_dict[spc_hash]

        return {'FINISHED'}


class SCATTER5_OT_image_utils(bpy.types.Operator):
    """operator used to quickly create or paint images, with mutli-surface support, for the active psy or active group context or else
    due to the nature of the geoscatter multi-surface workflow, this tool will set up a painting mode on many objects simultaneously"""

    bl_idname  = "scatter5.image_utils"
    bl_label   = translate("Create a New Image")
    bl_options = {'REGISTER', 'INTERNAL'}

    img_name : bpy.props.StringProperty(name=translate("Image Name"), options={"SKIP_SAVE",},)    
    option : bpy.props.StringProperty() #enum in "open"/"new"/"paint"
    api : bpy.props.StringProperty()
    paint_color : bpy.props.FloatVectorProperty()
    uv_ptr : bpy.props.StringProperty(default="UVMap", options={"SKIP_SAVE",},)
    
    context_surfaces : bpy.props.StringProperty(default="*PSY_CONTEXT*", options={"SKIP_SAVE",},)

    #new dialog 
    res_x : bpy.props.IntProperty(default=1080, name=translate("resolution X"), options={"SKIP_SAVE",},)
    res_y : bpy.props.IntProperty(default=1080, name=translate("resolution Y"), options={"SKIP_SAVE",},)
    quitandopen : bpy.props.BoolProperty(default=False,name=translate("Open From Explorer"), options={"SKIP_SAVE",},)
    
    #open dialog
    filepath : bpy.props.StringProperty(subtype="DIR_PATH")

    def __init__(self, *args, **kwargs):
        """store surfaces target"""
        
        super().__init__(*args, **kwargs)
        
        #find surfaces automatically depending on group/psy interface context
        if (self.context_surfaces=="*PSY_CONTEXT*"):
            
            #get active psy, or group
            emitter = bpy.context.scene.scatter5.emitter
            itm = emitter.scatter5.get_psy_active()
            if (itm is None):
                itm = emitter.scatter5.get_group_active()
            
            #get their surfaces
            self.surfaces = itm.get_surfaces()
            
        #find surfaces simply using the active emitter
        elif (self.context_surfaces=="*EMITTER_CONTEXT*"):
            self.surfaces = [bpy.context.scene.scatter5.emitter]
            
        #custom surface context
        else: 
            self.surfaces = [ bpy.data.objects[sn] for sn in self.context_surfaces.split("_!#!_") ]
        
        return None 

    @classmethod
    def description(cls, context, properties): 
        match properties.option:
            case 'paint':
                return translate("Start Painting")
            case 'open':
                return translate("Load Image File from Explorer")
            case 'new':
                return translate("Create Image Data")
        return ""

    def invoke(self, context, event):
        match self.option:
            case'paint':
                self.execute(context)
                return {'FINISHED'}
            case'open':
                context.window_manager.fileselect_add(self)
                return {'RUNNING_MODAL'}  
            case'new':
                self.img_name="ImageMask"
                return context.window_manager.invoke_props_dialog(self)
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        
        layout.use_property_split = True
        layout.prop(self,"res_x")
        layout.prop(self,"res_x")
        layout.prop(self,"img_name")
        layout.prop(self,"quitandopen")     

        return None 

    def execute(self, context):

        if (self.quitandopen):
            bpy.ops.scatter5.image_utils(('INVOKE_DEFAULT'), option="open", img_name=self.img_name, api=self.api,)
            return {'FINISHED'}
        
        scat_scene = context.scene.scatter5
        emitter = scat_scene.emitter
        
        match self.option:
            
            case "paint":

                img = bpy.data.images.get(self.img_name)
                if (img):
                    
                    #need to set an object as active
                    o = context.object
                    if (o not in self.surfaces):
                        for o in self.surfaces:
                            if (self.uv_ptr in o.data.uv_layers):
                                context.view_layer.objects.active = o
                                break      
                            
                    #sett all uvlayers active
                    for o in self.surfaces:
                        for l in o.data.uv_layers:
                            if (l.name==self.uv_ptr):
                                o.data.uv_layers.active = l
                                
                    #enter mode and set up tools settings
                    bpy.ops.object.mode_set(mode='TEXTURE_PAINT')
                    tool_sett = context.scene.tool_settings
                    tool_sett.image_paint.mode = 'IMAGE'
                    tool_sett.image_paint.canvas = img
                    tool_sett.unified_paint_settings.color = self.paint_color
                    
                    #set brush. Might need to override space
                    if (context.area.type!='VIEW_3D'):
                        from . override_utils import get_any_view3d_region
                        region_data = get_any_view3d_region(context=context, context_window_first=True,)
                        if (region_data):
                            window, area, region = region_data
                            with context.temp_override(window=window, area=area, region=region):
                                bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")
                    else:
                        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")
                
            case "open":
                
                img = bpy.data.images.load(filepath=self.filepath)
                exec( f"{self.api}=img.name" )

            case "new":
                
                img = bpy.data.images.new(self.img_name, self.res_x, self.res_y,)
                exec( f"{self.api}=img.name" )
                
        return {'FINISHED'}


class SCATTER5_OT_make_asset_library(bpy.types.Operator):

    bl_idname      = "scatter5.make_asset_library"
    bl_label       = translate("Choose Folder")
    bl_description = translate("Mark all objects of .blends in the chosen folder as assets.\n\nNested folder are not supported. Please do not run this operator from a blend file located in the folder you want to process. Please use this operator carefully, the result cannot be undone. Do not use this operator from an unsaved blend file.`\n\nOpen the console window to see progress.")

    directory : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},) 
    recursive : bpy.props.BoolProperty(default=False, options={"SKIP_SAVE",},)
    
    # TODO:
    #-ADD CONFIRM DIALOGBOX: 
    #   "This process will restart your blender session, are you sure that you want to continue" "OK"
    #    Overall confirm boxes are shit to implement if invoke is already being used, perhaps we'd need a ConfirmOperator generic class, that would be nice!
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    def execute(self, context):

        import os
        import platform
        import functools
        import numpy as np
        
        # some checks..
        if (not os.path.exists(self.directory)):
            # raise Exception("The path you gave us do not exists?")
            self.report({'ERROR'}, "The path you gave us do not exists?")
            return {'FINISHED'}
        
        if (not os.path.isdir(self.directory)):
            # raise Exception("The path you gave us is not a directory?")
            self.report({'ERROR'}, "The path you gave us is not a directory?")
            return {'FINISHED'}
        
        print("\nINFO: scatter5.make_asset_library(): Starting the conversion:")
        
        def log(msg, indent=0, prefix='>', ):
            m = "{}{} {}".format("    " * indent, prefix, msg, )
            print(m)
        
        # collect paths to blends in directory
        def collect():
            paths = []
            for root, ds, fs in os.walk(self.directory):
                for f in fs:
                    if(f.endswith('.blend')):
                        p = os.path.join(self.directory, root, f)
                        paths.append(p)
                
                if(not self.recursive):
                    break
            
            return paths
        
        def activate_textures():
            include = ('diffuse', 'albedo', )
            
            def do_mat(mat, ):
                # AI grade if-tree!
                if(mat.use_nodes):
                    nt = mat.node_tree
                    if(nt is not None):
                        ns = nt.nodes
                        for n in ns:
                            n.select = False
                        for n in ns:
                            if(n.type == 'TEX_IMAGE'):
                                im = n.image
                                if(im is not None):
                                    p = im.filepath
                                    if(p != ""):
                                        a = bpy.path.abspath(p)
                                        h, t = os.path.split(a)
                                        s = t.lower()
                                        for i in include:
                                            if(i in s):
                                                n.select = True
                                                ns.active = n
                                                return
            
            for mat in bpy.data.materials:
                do_mat(mat)
        
        # periodical check if all previews are created
        def check(p, paths, assets, callback, ):
            if(bpy.app.is_job_running('RENDER_PREVIEW')):
                # NOTE: is something is rendering, skip to next timer run so i don't hit something out of main thread.. (well, i hope..)
                log('preview render job is running..', 1)
                return 1.0
            
            while assets:
                ok = False
                if(isinstance(assets[0], bpy.types.Object)):
                    if(assets[0].type in ('MESH', )):
                        ok = True
                if(not ok):
                    log('skipping: {}'.format(assets[0]))
                    assets.pop(0)
                
                preview = assets[0].preview
                if(preview is None):
                    assets[0].asset_generate_preview()
                    return 0.2
                
                a = np.zeros((preview.image_size[0] * preview.image_size[1]) * 4, dtype=np.float32, )
                preview.image_pixels_float.foreach_get(a)
                if(np.all((a == 0))):
                    assets[0].asset_generate_preview()
                    return 0.2
                else:
                    assets.pop(0)
            
            if(not dry_run):
                log('save: {}'.format(p), 1)
                bpy.ops.wm.save_as_mainfile(filepath=p, compress=True, )
            else:
                log('save: dry_run = True, skipping!', 1)
            
            callback(paths, )
            return None
        
        # run recursively on all blends
        def run(paths, ):
            if(not len(paths)):
                bpy.ops.wm.read_homefile()
                log('-' * 100)
                log('all done!')
                
                on_all_done()
                
                return
            
            log('-' * 100)
            
            p = paths.pop()
            log('open: {}'.format(p))
            
            bpy.ops.wm.open_mainfile(filepath=p, )
            
            activate_textures()
            
            assets = []
            for o in bpy.data.objects:
                o.asset_mark()
                o.preview_ensure()
                # o.asset_generate_preview()
                assets.append(o)
            
            log('assets: {}'.format(assets), 1)
            
            log('processing..', 1)
            bpy.app.timers.register(
                functools.partial(check, p, paths, assets, run, )
            )
        
        # callback when all is done
        def on_all_done():
            #add path if not loaded yet?
            if (os.path.realpath(directory) not in [os.path.realpath(l.path) for l in context.preferences.filepaths.asset_libraries]):
                print("It seems that you did not register this library in your file paths?")
                print("let us do this process for you")
                bpy.ops.preferences.asset_library_add(directory=directory, )
                # NOTE: save preferences after or on blender restart will be lost
                bpy.ops.wm.save_userpref()
            
            print("Conversion finished!")
            
            # read default scene
            bpy.ops.wm.read_homefile()
            
            def delayed_call():
                bpy.ops.scatter5.popup_dialog(
                    'INVOKE_DEFAULT',
                    msg=translate("All files have been processed.\nDirectory has been added to your Asset-Library paths.\n"),
                    header_title=translate("Conversion Done!"),
                    header_icon="CHECKMARK",
                )
            
            bpy.app.timers.register(delayed_call, first_interval=0.1, )
        
        dry_run = False
        paths = collect()
        # NOTE: at the time `run` finishes, self will no longer be available because operator ended just after `run` was called, keep that in local vars
        directory = self.directory
        
        log('-' * 100)
        log('paths:')
        for p in paths:
            log(p, 1)
        log('-' * 100)
        
        run(paths)
        
        # NOTE: nothing should be called after `run` because it will be executed before `run` finishes, use `on_all_done` callback to do some work after conversion
        
        return {'FINISHED'}



class SCATTER5_OT_modal_measure_distance(bpy.types.Operator):
    """Calculate the distance from point origin, to selected click, in chosen direction"""

    bl_idname      = "scatter5.modal_measure_distance"
    bl_label   = translate("Measure Distance")
    bl_description = translate("Measure a distance by clicking on your scatter-surfaces")
    bl_options = {'REGISTER', 'INTERNAL'}
    
    mode : bpy.props.StringProperty(default="CameraDistance", options={"SKIP_SAVE",},)
    camera_location : bpy.props.FloatVectorProperty(options={"SKIP_SAVE",},) #Only for camera
    apply_sett_psyname : bpy.props.StringProperty(options={"SKIP_SAVE",},)
    apply_sett_propname : bpy.props.StringProperty(options={"SKIP_SAVE",},)
    
    class InfoBox_modal_measure_distance(SC5InfoBox):
        """append an instance of the infobox"""
        pass
    
    def __init__(self, *args, **kwargs):
        """set default vars"""
        
        super().__init__(*args, **kwargs)
        
        self.is_left_mouse = False
        self.psy = bpy.context.scene.scatter5.get_psy_by_name(self.apply_sett_psyname)
        
        assert (self.psy is not None)
        assert hasattr(self.psy,self.apply_sett_propname), "The property name passed does not exist in particle-system(s)"

        self._initial_sett_value = getattr(self.psy,self.apply_sett_propname)
        
        return None
                
    def invoke(self, context, event):
        
        if (bpy.context.window_manager.scatter5.mode!=""):
            self.report({'WARNING'}, translate("Modal operator already Running"))
            return {'CANCELLED'}
        
        if (context.area.type!='VIEW_3D'):
            self.report({'WARNING'}, translate("View3D not found, cannot run operator"))
            return {'CANCELLED'}
            
        #draw infobox on screen
        t = generic_infobox_setup(translate("Distance Measurement"),
                                  translate("Click on a surface to measure the distance"),
                                  ["• "+translate("Press 'ENTER' to Confirm"),
                                   "• "+translate("Press 'ESC' to Cancel"),
                                  ],)
        self.InfoBox_modal_measure_distance.init(t)
        # set following so infobox draw only in initial region
        self.InfoBox_modal_measure_distance._draw_in_this_region_only = context.region
        # it is class variable, we don't know how it is set, so we need to make sure it is set how we want, and we want it to draw, only manual mode have option to hide it
        self.InfoBox_modal_measure_distance._draw = True
        
        bpy.context.window_manager.scatter5.mode = "DIST_MEASURE"
        context.window_manager.modal_handler_add(self)
        
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        
        if (event.type in {'MIDDLEMOUSE','WHEELUPMOUSE','WHEELDOWNMOUSE'}):
            return {'PASS_THROUGH'} #let user move
    
        elif (event.type in {'ESC'}):
            self.cleanup(context)
            self.cancel(context)
            return {'CANCELLED'}
        
        elif (event.type in {'ENTER','RET'}):
            self.cleanup(context)
            return {'FINISHED'}
        
        elif (event.type=='LEFTMOUSE' and event.value=='PRESS'):
            self.is_left_mouse = True
            
        elif (event.type=='LEFTMOUSE' and event.value=='RELEASE'):
            self.is_left_mouse = False
        
        if (self.is_left_mouse):
            try:
                
                #get mouse information
                depsgraph = context.evaluated_depsgraph_get()
                region = context.region
                rv3d = context.region_data
                mouse_2d_loc = (event.mouse_region_x, event.mouse_region_y) #location of the mouse on the screen region

                #Convert the 2D mouse location to a 3D view vector and origin point
                view_dir = bpy_extras.view3d_utils.region_2d_to_vector_3d(region, rv3d, mouse_2d_loc)
                view_loc = bpy_extras.view3d_utils.region_2d_to_origin_3d(region, rv3d, mouse_2d_loc)
                #Calculate the ray end point
                ray_end = view_loc + (view_dir * 1000)
                
                #Perform ray casting on all objects we take the closest distance from user view
                
                _dist = float("inf")
                mouse_3d_loc = None
                mouse_o_hit = None
                
                for o in self.psy.get_surfaces():
                    
                    # Convert the ray start and end points to the object's local space
                    matrix_world_inv = o.matrix_world.inverted()
                    local_view_loc = matrix_world_inv @ view_loc
                    local_ray_end = matrix_world_inv @ ray_end
                    local_ray_direction = local_ray_end - local_view_loc
                    
                    #get the hit location, in local space, then convert back to global space again..
                    hit, hit_loc_local, *_ = o.ray_cast(local_view_loc, local_ray_direction, depsgraph=depsgraph)
                    if (not hit):
                        continue 
                    hit_loc_global = o.matrix_world @ hit_loc_local
                    
                    #if hit, we only take the hit location closest to viewer location
                    hit_dist = (view_loc-hit_loc_global).length
                    if (hit_dist<_dist):
                        _dist = hit_dist
                        mouse_o_hit = o
                        mouse_3d_loc = hit_loc_global
                        
                    continue
                            
                #if not mouse loc found, cancel all 
                if (mouse_3d_loc is not None): 
                    
                    if (self.mode=="CameraDistance"):
                        vec = mouse_3d_loc - mathutils.Vector(self.camera_location)
                        distance = vec.length
                        
                    elif (self.mode=="Altitude"):
                        distpoint = mathutils.Vector((0,0,0)) if (self.psy.s_abiotic_elev_space=="global") else mathutils.Vector(mouse_o_hit.location)
                        vec = mouse_3d_loc - distpoint
                        #
                        restricted_axis = mathutils.Vector((0,0,1)) if (self.psy.s_abiotic_elev_space=="global") else mouse_o_hit.matrix_world.to_3x3() @ mathutils.Vector((0,0,1))
                        restricted_axis.normalize()
                        #
                        distance = vec.dot(restricted_axis)
                    
                    #Apply the value we calculated to a setting? (Optional)
                    if (self.apply_sett_propname!=""):
                        p = context.scene.scatter5.get_psy_by_name(self.apply_sett_psyname)
                        if (p is not None):
                            setattr(p,self.apply_sett_propname,distance)
                
            except Exception as e:
                print("ERROR: scatter5.modal_measure_distance(): Error occured during modal execution")
                print(e)

        return {'RUNNING_MODAL'}
    
    def cleanup(self,context):
        
        #cleanup global singleton about mode operators
        context.window_manager.scatter5.mode = ""
        
        #remove screen indication 
        self.InfoBox_modal_measure_distance.deinit()
        
        return None
    
    def cancel(self,context): 
        
        #restore settings if used
        if (self._initial_sett_value is not None):
            p = context.scene.scatter5.get_psy_by_name(self.apply_sett_psyname)
            if (p is not None):
                setattr(p,self.apply_sett_propname,self._initial_sett_value)
            
        return None


#   .oooooo.   oooo
#  d8P'  `Y8b  `888
# 888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
# 888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
# 888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
# `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#  `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'



classes = (
        
    SCATTER5_OT_property_toggle,
    SCATTER5_OT_dummy,
    SCATTER5_OT_exec_line,

    SCATTER5_OT_set_solid_and_object_color,
    SCATTER5_OT_image_utils,
    
    SCATTER5_OT_make_asset_library,
    
    SCATTER5_OT_modal_measure_distance,

    )