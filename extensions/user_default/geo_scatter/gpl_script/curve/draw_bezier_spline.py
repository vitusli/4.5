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

from .. translations import translate
from ..utils.extra_utils import dprint


class SCATTER5_OT_draw_bezier_spline(bpy.types.Operator):
    
    bl_idname = "scatter5.draw_bezier_spline"
    bl_label = translate("Draw Curve")
    bl_description = translate("Draw bezier-splines(s) with an active tool")
    bl_options = {'REGISTER'}
    
    curve_name : bpy.props.StringProperty()
    
    def execute(self, context,):
        
        obj = bpy.data.objects.get(self.curve_name)
        assert (obj is not None)
        
        if ("OffsetCurveZ" not in obj.modifiers):
            from .. resources import directories
            from .. utils . import_utils import import_and_add_geonode
            import_and_add_geonode(obj, mod_name="OffsetCurveZ", node_name="OffsetCurveZ", blend_path=directories.addon_curve_blend,)
        
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)

        context.view_layer.objects.active = obj
        
        bpy.ops.object.editmode_toggle()
        bpy.ops.wm.tool_set_by_id(name="builtin.draw")
        
        settings = context.scene.tool_settings.curve_paint_settings
        settings.error_threshold = 4
        settings.depth_mode = 'SURFACE'
        settings.use_project_only_selected = False

        return {'FINISHED'}


def add_empty_bezier_spline(dimensions='3D', name="Curve", location=(0,0,0), collection=None):
    
    #create new curve data
    curve = bpy.data.curves.new(name,'CURVE')
    curve.dimensions = dimensions
    
    #find non taken obj name and append it in obj data
    i = 1
    nonused_n = name
    while nonused_n in bpy.data.objects:
        nonused_n = f"{name}.{i:03}"
        i += 1         
    obj = bpy.data.objects.new(nonused_n,curve)
    obj.location = location

    coll = None
    if (type(collection) is str):
        coll = bpy.data.collections.get(collection)
        if (coll is None) and ("Geo-Scatter" in collection): 
            from ..utils.coll_utils import setup_scatter_collections
            setup_scatter_collections()
            coll = bpy.data.collections.get(collection)
    else:
        if (collection is None):
              coll = bpy.context.scene.collection
        else: coll = collection
        
    if (coll is not None): 
        coll.objects.link(obj)

    return obj, curve


class SCATTER5_OT_add_bezier_spline(bpy.types.Operator):
    
    bl_idname = "scatter5.add_bezier_spline"
    bl_label = ""
    bl_description = translate("Add a new bezier-spline at cursor location.")
    bl_options = {'INTERNAL', 'UNDO', }
    
    api : bpy.props.StringProperty(default="", )
    
    def execute(self, context):
        
        obj, curve = add_empty_bezier_spline(name="DrawSpline", collection="Geo-Scatter User Col")
        
        obj.location = context.scene.cursor.location
        obj.location.z += 1

        spline = curve.splines.new(type='BEZIER')
        spline.bezier_points.add(1)
        spline.bezier_points[0].co = (-1,0,0)
        spline.bezier_points[1].co = (1,0,0)
        
        for pt in spline.bezier_points:
            pt.handle_left_type = pt.handle_right_type = 'AUTO'
            pt.select_left_handle = pt.select_right_handle = True
        
        if (self.api):
            # TODO: is the use of exec really needed? don't like any exec anywhere.. there should be another way
            scat_scene = context.scene.scatter5
            exec(f"{self.api} = bpy.data.objects['{obj.name}']")
        
        return {'FINISHED'}


classes = (
    SCATTER5_OT_add_bezier_spline,
    SCATTER5_OT_draw_bezier_spline,
)