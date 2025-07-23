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
# (c) 2024 Jakub Uhlik


import bpy

import os
import numpy as np
import gpu
from gpu.types import GPUShader
from gpu_extras.batch import batch_for_shader

from .shaders import load_shader_code
from .theme import ToolTheme


class GridOverlay():
    _shader = None
    _batch = None
    _handlers = []
    _initialized = False
    _theme = None
    
    @classmethod
    def init(cls, self, context, ):
        
        if(cls._initialized):
            return

        from ... __init__ import addon_prefs
        
        if(not addon_prefs().manual_use_overlay):
            return
        
        cls._theme = ToolTheme()
        
        v, f, _ = load_shader_code('CHECKERBOARD')
        # cls._shader = gpu.types.GPUShader(v, f, )
        
        # NOTE: "new style" shader ------------------------------------------- >>>
        shader_info = gpu.types.GPUShaderCreateInfo()
        shader_info.vertex_in(0, 'VEC2', "position")
        shader_info.push_constant('VEC4', "color_a")
        shader_info.push_constant('VEC4', "color_b")
        shader_info.push_constant('INT', "size")
        shader_info.fragment_out(0, 'VEC4', "fragColor")
        shader_info.vertex_source(v)
        # NOTE: does not automatically add `blender_srgb_to_framebuffer_space`.. lets provide our own (taken from blender source)
        colorspace = (
        "#undef blender_srgb_to_framebuffer_space\n"
        "vec4 blender_srgb_to_framebuffer_space(vec4 in_color)\n"
        "{\n"
        "    vec3 c = max(in_color.rgb, vec3(0.0));\n"
        "    vec3 c1 = c * (1.0 / 12.92);\n"
        "    vec3 c2 = pow((c + 0.055) * (1.0 / 1.055), vec3(2.4));\n"
        "    in_color.rgb = mix(c1, c2, step(vec3(0.04045), c));\n"
        "    return in_color;\n"
        "}\n"
        )
        shader_info.fragment_source(colorspace + f)
        cls._shader = gpu.shader.create_from_info(shader_info)
        # NOTE: "new style" shader ------------------------------------------- <<<
        
        cls._batch = batch_for_shader(cls._shader, 'TRIS', {'position': [(-1, -1), (3, -1), (-1, 3), ], })
        
        cls._handlers = []
        cls._initialized = True
        
        for a in context.screen.areas:
            s = a.spaces[0]
            for r in a.regions:
                try:
                    h = s.draw_handler_add(cls._draw, (self, a, r, ), r.type, 'POST_PIXEL', )
                    cls._handlers.append((s, r.type, h, ))
                except TypeError as e:
                    # NOTE: 3.0 bug: TypeError: unknown space type 'SpaceSpreadsheet'
                    # NOTE: https://developer.blender.org/T94685
                    pass
        
        cls._tag_redraw()
    
    @classmethod
    def deinit(cls, ):
        if(not cls._initialized):
            return
        
        for s, r, h in cls._handlers:
            s.draw_handler_remove(h, r, )
        cls._handlers = []
        
        cls._shader = None
        cls._batch = None
        
        cls._theme = None
        
        cls._initialized = False
        cls._tag_redraw()
    
    @classmethod
    def _draw(cls, self, area, region, ):
        # print("*")
        
        if(not cls._initialized):
            return
        
        for a, rt in self._grid_exclude:
            if(area.type == a.type):
                if(rt is None):
                    return
                if(region.type == rt):
                    r = None
                    for r in a.regions:
                        if(r.type == rt):
                            break
                    if(r):
                        x, y, w, h = gpu.state.viewport_get()
                        # WATCH: this is the only way i found to correctly identify area and region being drawn. so when two areas of same type and same dimensions are there, it won't work as expected..
                        if(r.width == w and r.height == h):
                            return
        
        gpu.state.depth_test_set('NONE')
        gpu.state.blend_set('ALPHA')
        
        cls._shader.bind()
        
        cls._shader.uniform_float('color_a', cls._theme._grid_overlay_color_a, )
        cls._shader.uniform_float('color_b', cls._theme._grid_overlay_color_b, )
        
        cls._shader.uniform_int('size', int(round(cls._theme._grid_overlay_size * cls._theme._ui_scale)), )
        
        cls._batch.draw(cls._shader, )
        # NOTE: do i need that?
        gpu.shader.unbind()
        
        gpu.state.depth_test_set('NONE')
        gpu.state.blend_set('NONE')
    
    @classmethod
    def _tag_redraw(cls, ):
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                area.tag_redraw()


classes = ()
