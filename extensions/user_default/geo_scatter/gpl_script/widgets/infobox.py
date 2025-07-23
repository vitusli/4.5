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
import blf

import os
import platform
import json
import gpu
import mathutils
from gpu_extras.batch import batch_for_shader
import numpy as np
from mathutils import Vector, Matrix

from . theme import ToolTheme
from .. resources.directories import icons_logo


# NOTE: it made some circular import problems, that is why log finctions are repeated here. uncomment if needed
'''
def debug_mode():
    return (bpy.app.debug_value != 0)


def colorize(msg, ):
    if(platform.system() == 'Windows'):
        return msg
    # return "{}{}{}".format("\033[42m\033[30m", msg, "\033[0m", )
    return "{}{}{}".format("\033[43m\033[30m", msg, "\033[0m", )


def log(msg, indent=0, prefix='>', ):
    m = "{}{} {}".format("    " * indent, prefix, colorize(msg, ), )
    if(debug_mode()):
        print(m)
'''


class SC5InfoBox():
    _initialized = False
    _handle = None
    # _sv3d = None
    _theme = None
    _draw = True
    _draw_in_this_region_only = None
    
    INFO = None
    
    # defaults
    FONT_ID = 0
    UI_SCALE = 1.0
    DEFAULT_BOX_OUTER_PADDING = 20
    DEFAULT_BOX_CORNER_RADIUS = 10
    DEFAULT_TEXT_PADDING = 10
    
    # outside of box so shadow have space
    BOX_OUTER_PADDING = int(DEFAULT_BOX_OUTER_PADDING * UI_SCALE)
    BOX_CORNER_RADIUS = int(DEFAULT_BOX_CORNER_RADIUS * UI_SCALE)
    BOX_SHADOW_COLOR = (0.0, 0.0, 0.0, 0.5, )
    BOX_FILL_COLOR = (0.12, 0.12, 0.12, 0.95, )
    BOX_OUTLINE_COLOR = (0.12, 0.12, 0.12, 0.95, )
    # text offset from box edges
    TEXT_PADDING = int(DEFAULT_TEXT_PADDING * UI_SCALE)
    
    VS, FS, ES = None, None, None
    if (os.path.exists(icons_logo)):
        with open(icons_logo, "r") as f:
            content = json.load(f)
            VS, FS, ES = content.get("VS"), content.get("FS"), content.get("ES")
        
    if (VS and FS and ES):
        LOGO_COLOR = (1.0, 1.0, 1.0, 1.0)
        LOGO_VS = np.array(VS, dtype=np.float32,)
        LOGO_FS = np.array(FS, dtype=np.int32,)
        LOGO_ES = np.array(ES, dtype=np.int32,)
        
        # NOTE: will fail when running headless: SystemError: GPU functions for drawing are not available in background mode
        if(not bpy.app.background):
            if(bpy.app.version < (3, 4, 0)):
                LOGO_FILL_SHADER = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
            else:
                LOGO_FILL_SHADER = gpu.shader.from_builtin('UNIFORM_COLOR')
            LOGO_FILL_BATCH = batch_for_shader(LOGO_FILL_SHADER, 'TRIS', {"pos": LOGO_VS[:, :2], }, indices=LOGO_FS, )
            if(bpy.app.version < (3, 4, 0)):
                LOGO_OUTLINE_SHADER = gpu.shader.from_builtin('3D_POLYLINE_UNIFORM_COLOR')
            else:
                LOGO_OUTLINE_SHADER = gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
            LOGO_OUTLINE_BATCH = batch_for_shader(LOGO_OUTLINE_SHADER, 'LINES', {'pos': LOGO_VS, }, indices=LOGO_ES, )
    
    @classmethod
    def init(cls, info, ):
        if(cls._initialized):
            # log("SC5InfoBox.init() denied, already running..", indent=0, prefix='>>>', )
            return
        
        # log("SC5InfoBox.init()", indent=0, prefix='>>>', )
        
        cls._theme = ToolTheme()
        cls.BOX_SHADOW_COLOR = cls._theme._info_box_shadow_color
        cls.BOX_FILL_COLOR = cls._theme._info_box_fill_color
        cls.BOX_OUTLINE_COLOR = cls._theme._info_box_outline_color
        cls.LOGO_COLOR = cls._theme._info_box_logo_color
        
        cls.INFO = info
        
        # # recalculate according to ui scale
        # u = bpy.context.preferences.addons['Scatter5'].preferences.ui_scale_viewport
        # cls.UI_SCALE = bpy.context.preferences.system.ui_scale * u
        cls.UI_SCALE = cls._theme._ui_scale * cls._theme._info_box_scale
        
        cls.BOX_OUTER_PADDING = int(cls.DEFAULT_BOX_OUTER_PADDING * cls.UI_SCALE)
        cls.BOX_CORNER_RADIUS = int(cls.DEFAULT_BOX_CORNER_RADIUS * cls.UI_SCALE)
        cls.TEXT_PADDING = int(cls.DEFAULT_TEXT_PADDING * cls.UI_SCALE)
        
        # cls._sv3d = sv3d
        # if(cls._sv3d is not None):
        #     # draw only in specific 3d view >> custom modal operators with overlay..
        #     # cls._handle = cls._sv3d.draw_handler_add(cls._post_pixel_handler, (context, ), 'WINDOW', 'POST_PIXEL')
        #     cls._handle = cls._sv3d.draw_handler_add(cls._post_pixel_handler, (), 'WINDOW', 'POST_PIXEL')
        #     print("!")
        # else:
        #     # draw in all 3d views >> using builtin tools like weight paint..
        #     cls._handle = bpy.types.SpaceView3D.draw_handler_add(cls._post_pixel_handler, (), 'WINDOW', 'POST_PIXEL')
        
        cls._handle = bpy.types.SpaceView3D.draw_handler_add(cls._post_pixel_handler, (), 'WINDOW', 'POST_PIXEL')
        
        # from ... __init__ import addon_prefs
        # cls._draw = addon_prefs().manual_show_infobox
        
        cls._initialized = True
        cls._setup()
        cls._tag_redraw()
    
    @classmethod
    def deinit(cls, ):
        if(not cls._initialized):
            # log("SC5InfoBox.deinit() denied, not running..", indent=0, prefix='>>>', )
            return
        
        # log("SC5InfoBox.deinit()", indent=0, prefix='>>>', )
        
        # if(cls._sv3d is not None):
        #     cls._sv3d.draw_handler_remove(cls._handle, 'WINDOW', )
        # else:
        #     bpy.types.SpaceView3D.draw_handler_remove(cls._handle, 'WINDOW', )
        
        bpy.types.SpaceView3D.draw_handler_remove(cls._handle, 'WINDOW', )
        
        cls.INFO = None
        # cls._sv3d = None
        cls._handle = None
        
        cls._theme = None
        
        cls._initialized = False
        
        # back to default, users should set this at start right after `init()`, but better to be safe
        cls._draw = True
        cls._draw_in_this_region_only = None
        
        cls._cleanup()
        cls._tag_redraw()
    
    @classmethod
    def _setup_text(cls, ):
        # find longest line in pixels and sum whole paragraph height
        max_line_width = 0
        total_height = 0
        for i, item in enumerate(reversed(cls.INFO)):
            s = int(round(item['style']['size'] * cls.UI_SCALE))
            if(bpy.app.version < (4, 0, 0)):
                blf.size(cls.FONT_ID, s, 72)
            else:
                # 4.0, `dpi` argument is removed
                blf.size(cls.FONT_ID, s)
            for j, t in enumerate(item['text']):
                if(t is None):
                    l = int(np.ceil(item['style']['separator'] * cls.UI_SCALE))
                    total_height += l
                    continue
                
                w, _ = blf.dimensions(cls.FONT_ID, t)
                _, h = blf.dimensions(cls.FONT_ID, 'F')
                ml = int(np.ceil(item['style']['margin_left'] * cls.UI_SCALE))
                l = int(np.ceil(item['style']['line_height'] * cls.UI_SCALE))
                total_height += l
                if(w + ml > max_line_width):
                    max_line_width = w + ml
        
        max_line_width += 2 * cls.TEXT_PADDING
        total_height += 2 * cls.TEXT_PADDING
        # subtract last line height without spacing
        total_height -= l - h
        
        cls._max_line_width = int(np.ceil(max_line_width))
        cls._total_height = int(np.ceil(total_height))
    
    @classmethod
    def _rounded_rectangle(cls, a, b, radius, steps=32, ):
        c = np.zeros((steps, 2), dtype=np.float32, )
        angstep = 2 * np.pi / steps
        aa = np.arange(steps, dtype=np.int32, )
        c[:, 0] = np.sin(aa * angstep) * radius
        c[:, 1] = np.cos(aa * angstep) * radius
        
        q = int(steps / 4)
        trc = c[:q + 1].copy()
        brc = c[q:q * 2 + 1].copy()
        blc = c[q * 2:q * 3 + 1].copy()
        tlc = c[q * 3:].copy()
        tlc = np.concatenate([tlc, c[0].copy().reshape((-1, 2))])
        
        trc[:, 0] += b[0] - radius
        trc[:, 1] += b[1] - radius
        brc[:, 0] += b[0] - radius
        brc[:, 1] += a[1] + radius
        blc[:, 0] += a[0] + radius
        blc[:, 1] += a[1] + radius
        tlc[:, 0] += a[0] + radius
        tlc[:, 1] += b[1] - radius
        
        vs = np.concatenate([trc, brc, blc, tlc, ])
        indices = np.array(mathutils.geometry.tessellate_polygon((vs, )), dtype=np.int32, )
        return vs, indices
    
    @classmethod
    def _clone_texture(cls, tex, ):
        w = tex.width
        h = tex.height
        f = tex.format
        b = tex.read()
        # NOTE: flatten first
        b.dimensions = w * h * 4
        # NOTE: should i be explicit about data type? i think i should..
        a = np.array(b, dtype=np.float32, )
        # a = a.copy()
        # NOTE: C-contiguous
        a = a.copy(order='C')
        # b = gpu.types.Buffer('FLOAT', (w, h, 4), a.flatten())
        b = gpu.types.Buffer('FLOAT', a.shape, a)
        t = gpu.types.GPUTexture((w, h), format=f, data=b, )
        return t
    
    @classmethod
    def _setup_box(cls, ):
        w = cls._max_line_width
        h = cls._total_height
        p = cls.BOX_OUTER_PADDING
        cls._box_width = w + (p * 2)
        cls._box_height = h + (p * 2)
        
        # draw rounded rectange as source of shadow
        cls._tex_color = gpu.types.GPUTexture((cls._box_width, cls._box_height), format='RGBA32F', )
        cls._fbo = gpu.types.GPUFrameBuffer(color_slots=cls._tex_color, )
        
        with cls._fbo.bind():
            cls._tex_color.clear(format='FLOAT', value=(0.0, ), )
            
            a = [p, p]
            b = [w + p, h + p]
            # color = [0.0, 0.0, 0.0, 1.0]
            color = cls.BOX_SHADOW_COLOR
            
            with gpu.matrix.push_pop():
                with gpu.matrix.push_pop_projection():
                    gpu.matrix.load_matrix(Matrix.Identity(4))
                    gpu.matrix.load_projection_matrix(Matrix.Identity(4))
                    
                    vertices, indices = cls._rounded_rectangle(a, b, cls.BOX_CORNER_RADIUS, steps=32, )
                    vertices[:, 0] *= (1 / cls._box_width)
                    vertices[:, 1] *= (1 / cls._box_height)
                    vertices *= 2.0
                    vertices -= 1.0
                    
                    if(bpy.app.version < (3, 4, 0)):
                        shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
                    else:
                        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
                    batch = batch_for_shader(shader, 'TRIS', {'pos': vertices, }, indices=indices, )
                    gpu.state.blend_set('ALPHA')
                    shader.bind()
                    shader.uniform_float('color', color, )
                    batch.draw(shader)
                    gpu.state.blend_set('NONE')
        
        # blur rectangle
        vert = '''
        // uniform mat4 ModelViewProjectionMatrix;
        // in vec2 pos;
        // out vec2 uv;
        void main()
        {
            gl_Position = ModelViewProjectionMatrix * vec4(pos.xy, 1.0f, 1.0f);
            uv = pos.xy;
        }
        '''
        # https://github.com/mrdoob/three.js/blob/c93db539b230417f6b8a5261fbc52bba1cd39d7d/examples/jsm/shaders/HorizontalBlurShader.js
        frag_h = '''
        // in vec2 uv;
        // uniform sampler2D color;
        // uniform float h;
        // out vec4 fragColor;
        void main() {
            vec4 sum = vec4(0.0);
            sum += texture(color, vec2(uv.x - 4.0 * h, uv.y)) * 0.051;
            sum += texture(color, vec2(uv.x - 3.0 * h, uv.y)) * 0.0918;
            sum += texture(color, vec2(uv.x - 2.0 * h, uv.y)) * 0.12245;
            sum += texture(color, vec2(uv.x - 1.0 * h, uv.y)) * 0.1531;
            sum += texture(color, vec2(uv.x, uv.y ) ) * 0.1633;
            sum += texture(color, vec2(uv.x + 1.0 * h, uv.y)) * 0.1531;
            sum += texture(color, vec2(uv.x + 2.0 * h, uv.y)) * 0.12245;
            sum += texture(color, vec2(uv.x + 3.0 * h, uv.y)) * 0.0918;
            sum += texture(color, vec2(uv.x + 4.0 * h, uv.y)) * 0.051;
            fragColor = sum;
            //fragColor = vec4(uv.x, uv.y, 0.0, 1.0);
        }
        '''
        frag_v = '''
        // in vec2 uv;
        // uniform sampler2D color;
        // uniform float v;
        // out vec4 fragColor;
        void main() {
            vec4 sum = vec4(0.0);
            sum += texture(color, vec2(uv.x, uv.y - 4.0 * v)) * 0.051;
            sum += texture(color, vec2(uv.x, uv.y - 3.0 * v)) * 0.0918;
            sum += texture(color, vec2(uv.x, uv.y - 2.0 * v)) * 0.12245;
            sum += texture(color, vec2(uv.x, uv.y - 1.0 * v)) * 0.1531;
            sum += texture(color, vec2(uv.x, uv.y ) ) * 0.1633;
            sum += texture(color, vec2(uv.x, uv.y + 1.0 * v)) * 0.1531;
            sum += texture(color, vec2(uv.x, uv.y + 2.0 * v)) * 0.12245;
            sum += texture(color, vec2(uv.x, uv.y + 3.0 * v)) * 0.0918;
            sum += texture(color, vec2(uv.x, uv.y + 4.0 * v)) * 0.051;
            fragColor = sum;
        }
        '''
        
        # # # # # debug
        # buffer = cls._tex_color.read()
        # buffer.dimensions = cls._box_width * cls._box_height * 4
        # image_name = "pcv_debug"
        # if(image_name not in bpy.data.images):
        #     bpy.data.images.new(image_name, cls._box_width, cls._box_height, float_buffer=True, )
        # image = bpy.data.images[image_name]
        # image.scale(cls._box_width, cls._box_height, )
        # a = np.array(buffer)
        # image.pixels = a.flatten()
        # # # # # debug
        
        # blur horizontally
        texture = cls._tex_color
        cls._h_color = gpu.types.GPUTexture((cls._box_width, cls._box_height), format='RGBA32F', )
        cls._h_fbo = gpu.types.GPUFrameBuffer(color_slots=cls._h_color, )
        with cls._h_fbo.bind():
            cls._h_color.clear(format='FLOAT', value=(0.0, ), )
            
            coords = ((0, 0), (1, 0), (1, 1), (0, 1))
            # shader = gpu.types.GPUShader(vert, frag_h, )
            
            # NOTE: "new style" shader ------------------------------------------- >>>
            shader_info = gpu.types.GPUShaderCreateInfo()
            shader_info.vertex_in(0, 'VEC2', "pos")
            vert_out = gpu.types.GPUStageInterfaceInfo("vertex_interface")
            vert_out.smooth('VEC2', "uv")
            shader_info.vertex_out(vert_out)
            shader_info.push_constant("MAT4", "ModelViewProjectionMatrix")
            shader_info.push_constant('FLOAT', "h")
            shader_info.sampler(0, 'FLOAT_2D', "color")
            shader_info.fragment_out(0, 'VEC4', "fragColor")
            shader_info.vertex_source(vert)
            shader_info.fragment_source(frag_h)
            shader = gpu.shader.create_from_info(shader_info)
            # NOTE: "new style" shader ------------------------------------------- <<<
            
            indices = mathutils.geometry.tessellate_polygon((coords, ))
            batch = batch_for_shader(shader, 'TRIS', {"pos": coords, }, indices=indices, )
            
            with gpu.matrix.push_pop():
                with gpu.matrix.push_pop_projection():
                    gpu.matrix.load_matrix(Matrix.Identity(4))
                    # gpu.matrix.load_projection_matrix(Matrix.Identity(4))
                    projection = Matrix.LocRotScale(Vector((-1, -1, 0.0)), None, Vector((2.0, 2.0, 1.0)))
                    gpu.matrix.load_projection_matrix(projection)
                    
                    gpu.state.blend_set('ALPHA')
                    shader.bind()
                    shader.uniform_sampler("color", texture)
                    shader.uniform_float("h", 1 / cls._box_width)
                    batch.draw(shader)
                    gpu.state.blend_set('NONE')
        
        # # # # # debug
        # buffer = cls._h_color.read()
        # buffer.dimensions = cls._box_width * cls._box_height * 4
        # image_name = "pcv_debug"
        # if(image_name not in bpy.data.images):
        #     bpy.data.images.new(image_name, cls._box_width, cls._box_height, float_buffer=True, )
        # image = bpy.data.images[image_name]
        # image.scale(cls._box_width, cls._box_height, )
        # a = np.array(buffer)
        # image.pixels = a.flatten()
        # # # # # debug
        
        texture = cls._h_color
        
        # and blur vertically
        cls._v_color = gpu.types.GPUTexture((cls._box_width, cls._box_height), format='RGBA32F', )
        cls._v_fbo = gpu.types.GPUFrameBuffer(color_slots=cls._v_color, )
        with cls._v_fbo.bind():
            cls._v_color.clear(format='FLOAT', value=(0.0, ), )
            
            coords = ((0, 0), (1, 0), (1, 1), (0, 1))
            # shader = gpu.types.GPUShader(vert, frag_v, )
            
            # NOTE: "new style" shader ------------------------------------------- >>>
            shader_info = gpu.types.GPUShaderCreateInfo()
            shader_info.vertex_in(0, 'VEC2', "pos")
            vert_out = gpu.types.GPUStageInterfaceInfo("vertex_interface")
            vert_out.smooth('VEC2', "uv")
            shader_info.vertex_out(vert_out)
            shader_info.push_constant("MAT4", "ModelViewProjectionMatrix")
            shader_info.push_constant('FLOAT', "v")
            shader_info.sampler(0, 'FLOAT_2D', "color")
            shader_info.fragment_out(0, 'VEC4', "fragColor")
            shader_info.vertex_source(vert)
            shader_info.fragment_source(frag_v)
            shader = gpu.shader.create_from_info(shader_info)
            # NOTE: "new style" shader ------------------------------------------- <<<
            
            indices = mathutils.geometry.tessellate_polygon((coords, ))
            batch = batch_for_shader(shader, 'TRIS', {"pos": coords, }, indices=indices, )
            
            with gpu.matrix.push_pop():
                with gpu.matrix.push_pop_projection():
                    gpu.matrix.load_matrix(Matrix.Identity(4))
                    # gpu.matrix.load_projection_matrix(Matrix.Identity(4))
                    projection = Matrix.LocRotScale(Vector((-1, -1, 0.0)), None, Vector((2.0, 2.0, 1.0)))
                    gpu.matrix.load_projection_matrix(projection)
                    
                    gpu.state.blend_set('ALPHA')
                    shader.bind()
                    shader.uniform_sampler("color", texture)
                    shader.uniform_float("v", 1 / cls._box_height)
                    batch.draw(shader)
                    gpu.state.blend_set('NONE')
        
        # # # # # debug
        # buffer = cls._v_color.read()
        # buffer.dimensions = cls._box_width * cls._box_height * 4
        # image_name = "pcv_debug"
        # if(image_name not in bpy.data.images):
        #     bpy.data.images.new(image_name, cls._box_width, cls._box_height, float_buffer=True, )
        # image = bpy.data.images[image_name]
        # image.scale(cls._box_width, cls._box_height, )
        # a = np.array(buffer)
        # image.pixels = a.flatten()
        # # # # # debug
        
        texture = cls._v_color
        
        # now draw it again with some shadow offset
        cls._fin_color = gpu.types.GPUTexture((cls._box_width, cls._box_height), format='RGBA32F', )
        cls._fin_fbo = gpu.types.GPUFrameBuffer(color_slots=cls._fin_color, )
        with cls._fin_fbo.bind():
            cls._fin_color.clear(format='FLOAT', value=(0.0, ), )
            
            shadow_offset = 5
            position = 0, -((1 / cls._box_height) * shadow_offset)
            coords = ((0, 0), (1, 0), (1, 1), (0, 1))
            if(bpy.app.version < (3, 4, 0)):
                shader = shader = gpu.shader.from_builtin('2D_IMAGE')
            else:
                shader = shader = gpu.shader.from_builtin('IMAGE')
            indices = mathutils.geometry.tessellate_polygon((coords, ))
            batch = batch_for_shader(shader, 'TRIS', {"pos": coords, "texCoord": coords, }, indices=indices, )
            
            with gpu.matrix.push_pop():
                with gpu.matrix.push_pop_projection():
                    gpu.matrix.load_matrix(Matrix.Identity(4))
                    gpu.matrix.translate(position)
                    # gpu.matrix.load_projection_matrix(Matrix.Identity(4))
                    projection = Matrix.LocRotScale(Vector((-1, -1, 0.0)), None, Vector((2.0, 2.0, 1.0)))
                    gpu.matrix.load_projection_matrix(projection)
                    
                    gpu.state.blend_set('ALPHA')
                    shader.bind()
                    shader.uniform_sampler("image", texture)
                    batch.draw(shader)
                    gpu.state.blend_set('NONE')
            
            # and draw zero color rectange into original location to knock out shadow from inside of box
            a = [p, p]
            b = [w + p, h + p]
            color = [0.0, 0.0, 0.0, 0.0]
            
            with gpu.matrix.push_pop():
                with gpu.matrix.push_pop_projection():
                    gpu.matrix.load_matrix(Matrix.Identity(4))
                    gpu.matrix.load_projection_matrix(Matrix.Identity(4))
                    vertices, indices = cls._rounded_rectangle(a, b, cls.BOX_CORNER_RADIUS, steps=32, )
                    vertices[:, 0] *= (1 / cls._box_width)
                    vertices[:, 1] *= (1 / cls._box_height)
                    vertices *= 2.0
                    vertices -= 1.0
                    if(bpy.app.version < (3, 4, 0)):
                        shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
                    else:
                        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
                    batch = batch_for_shader(shader, 'TRIS', {'pos': vertices, }, indices=indices, )
                    shader.bind()
                    shader.uniform_float('color', color, )
                    batch.draw(shader)
        
        # # # # # debug
        # buffer = cls._fin_color.read()
        # buffer.dimensions = cls._box_width * cls._box_height * 4
        # image_name = "pcv_debug"
        # if(image_name not in bpy.data.images):
        #     bpy.data.images.new(image_name, cls._box_width, cls._box_height, float_buffer=True, )
        # image = bpy.data.images[image_name]
        # image.scale(cls._box_width, cls._box_height, )
        # a = np.array(buffer)
        # image.pixels = a.flatten()
        # # # # # debug
        
        # that's mine finished box texture, lets hope it stays in memory
        # TODO: when this is cleared from memory? there is `bpy.types.Image.gl_touch` for images, do i need something similar? i don't see anything in docs..
        # cls._texture = cls._fin_color
        cls._texture = cls._clone_texture(cls._fin_color)
        
        # # # # # debug
        # # buffer = cls._fin_color.read()
        # # buffer = cls._texture.read()
        # w = cls._fin_color.width
        # h = cls._fin_color.height
        # f = cls._fin_color.format
        # b = cls._fin_color.read()
        # # a = np.array(b.to_list(), dtype=np.float32, )
        # b.dimensions = w * h * 4
        # a = np.array(b, dtype=np.float32, )
        # a = a.copy(order='C')
        # b = gpu.types.Buffer('FLOAT', a.shape, a)
        # # print(b)
        # t = gpu.types.GPUTexture((w, h), format=f, data=b, )
        # buffer = t.read()
        # buffer.dimensions = cls._box_width * cls._box_height * 4
        # image_name = "pcv_debug"
        # if(image_name not in bpy.data.images):
        #     bpy.data.images.new(image_name, cls._box_width, cls._box_height, float_buffer=True, )
        # image = bpy.data.images[image_name]
        # image.scale(cls._box_width, cls._box_height, )
        # a = np.array(buffer)
        # image.pixels = a.flatten()
        # # # # # debug
        
        cls._tex_color = None
        cls._fbo = None
        cls._h_color = None
        cls._h_fbo = None
        cls._v_color = None
        cls._v_fbo = None
        cls._fin_color = None
        cls._fin_fbo = None
        
        '''
        # # # # debug
        buffer = cls._texture.read()
        # print(buffer)
        buffer.dimensions = cls._box_width * cls._box_height * 4
        image_name = "pcv_debug"
        if(image_name not in bpy.data.images):
            bpy.data.images.new(image_name, cls._box_width, cls._box_height, float_buffer=True, )
        image = bpy.data.images[image_name]
        image.scale(cls._box_width, cls._box_height, )
        # print(image.size[:])
        a = np.array(buffer)
        # print(np.sum(a.flatten()))
        # print(a.flatten().tolist())
        image.pixels = a.flatten()
        # # # # debug
        '''
    
    @classmethod
    def _setup(cls, ):
        cls._setup_text()
        cls._setup_box()
    
    @classmethod
    def _cleanup(cls, ):
        # clear (set to None) all that might take memory..
        # print(dir(cls))
        cls._max_line_width = None
        cls._total_height = None
        cls._box_height = None
        cls._box_width = None
        
        cls._fbo = None
        cls._tex_color = None
        cls._h_fbo = None
        cls._h_color = None
        cls._v_fbo = None
        cls._v_color = None
        cls._fin_fbo = None
        cls._fin_color = None
        
        cls._texture = None
    
    @classmethod
    def _thick_line_2d(cls, a, b, color=(1.0, 0.0, 0.0, 0.5, ), thickness=2.0, ):
        vertices = np.array(((a[0], a[1], 0.0, ), (b[0], b[1], 0.0, ), ), dtype=np.float32, )
        indices = np.array(((0, 1), ), dtype=np.int32, )
        if(bpy.app.version < (3, 4, 0)):
            shader = gpu.shader.from_builtin('3D_POLYLINE_UNIFORM_COLOR')
        else:
            shader = gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'LINES', {'pos': vertices, }, indices=indices, )
        gpu.state.blend_set('ALPHA')
        shader.bind()
        shader.uniform_float('color', color, )
        # shader.uniform_float("lineSmooth", True, )
        shader.uniform_float("lineWidth", thickness, )
        _, _, w, h = gpu.state.viewport_get()
        shader.uniform_float("viewportSize", (w, h, ))
        batch.draw(shader)
        gpu.state.blend_set('NONE')
    
    @classmethod
    def _draw_logo(cls, height, ):
        color = cls.LOGO_COLOR
        cls.LOGO_SCALE = height * cls.UI_SCALE
        
        x = cls.BOX_OUTER_PADDING + cls.TEXT_PADDING
        # y = cls._total_height - (cls.BOX_OUTER_PADDING + cls.TEXT_PADDING) + int(6 * cls.UI_SCALE)
        y = cls._total_height - cls.BOX_OUTER_PADDING - cls.TEXT_PADDING + (cls.TEXT_PADDING / 2)
        
        # TODO: this should be called just once per viewport, no need to do it 3 times for each viewport, but like that is easy to implement now..
        # NOTE: fix info location when region overlap is enabled
        x_correction = 0
        if(bpy.context.preferences.system.use_region_overlap):
            vwx, vwy, vww, vwh = gpu.state.viewport_get()
            for window in bpy.context.window_manager.windows:
                screen = window.screen
                for area in screen.areas:
                    if(area.type == 'VIEW_3D'):
                        wh = -1
                        th = -1
                        tw = -1
                        ok = False
                        for r in area.regions:
                            if(r.type == 'TOOLS'):
                                th = r.height
                                tw = r.width
                            if(r.type == 'WINDOW'):
                                if(r.width == vww and r.height == vwh):
                                    ok = True
                                wh = r.height
                        if(ok):
                            # if(wh > 0 and th > 0 and tw > 0 and wh == th):
                            if(wh > 0 and th > 0 and tw > 0):
                                x_correction = tw
        
        x += x_correction
        
        if hasattr(cls,"LOGO_FILL_SHADER"):
            
            # draw filled triangles
            with gpu.matrix.push_pop():
                gpu.matrix.translate((x, y))
                gpu.matrix.scale((cls.LOGO_SCALE, cls.LOGO_SCALE))
                cls.LOGO_FILL_SHADER.bind()
                cls.LOGO_FILL_SHADER.uniform_float("color", color, )
                gpu.state.blend_set('ALPHA')
                cls.LOGO_FILL_BATCH.draw(cls.LOGO_FILL_SHADER)
                gpu.state.blend_set('NONE')
            
            # draw thick line outline to have it looking antialiased..
            with gpu.matrix.push_pop():
                gpu.matrix.translate((x, y))
                gpu.matrix.scale((cls.LOGO_SCALE, cls.LOGO_SCALE))
                cls.LOGO_OUTLINE_SHADER.bind()
                cls.LOGO_OUTLINE_SHADER.uniform_float('color', color, )
                cls.LOGO_OUTLINE_SHADER.uniform_float("lineWidth", 1.0, )
                _, _, w, h = gpu.state.viewport_get()
                cls.LOGO_OUTLINE_SHADER.uniform_float("viewportSize", (w, h, ))
                gpu.state.blend_set('ALPHA')
                cls.LOGO_OUTLINE_BATCH.draw(cls.LOGO_OUTLINE_SHADER)
                gpu.state.blend_set('NONE')
    
    @classmethod
    def _draw_box(cls, ):
        _, _, w, h = gpu.state.viewport_get()
        
        # TODO: this should be called just once per viewport, no need to do it 3 times for each viewport, but like that is easy to implement now..
        # NOTE: fix info location when region overlap is enabled
        x_correction = 0
        if(bpy.context.preferences.system.use_region_overlap):
            vwx, vwy, vww, vwh = gpu.state.viewport_get()
            for window in bpy.context.window_manager.windows:
                screen = window.screen
                for area in screen.areas:
                    if(area.type == 'VIEW_3D'):
                        wh = -1
                        th = -1
                        tw = -1
                        ok = False
                        for r in area.regions:
                            if(r.type == 'TOOLS'):
                                th = r.height
                                tw = r.width
                            if(r.type == 'WINDOW'):
                                if(r.width == vww and r.height == vwh):
                                    ok = True
                                wh = r.height
                        if(ok):
                            # if(wh > 0 and th > 0 and tw > 0 and wh == th):
                            if(wh > 0 and th > 0 and tw > 0):
                                x_correction = tw
        
        position = (0 + x_correction, 0, )
        
        # draw box shadow texture first
        texture = cls._texture
        
        width = texture.width
        height = texture.height
        coords = ((0, 0), (1, 0), (1, 1), (0, 1))
        if(bpy.app.version < (3, 4, 0)):
            shader = gpu.shader.from_builtin('2D_IMAGE')
        else:
            shader = gpu.shader.from_builtin('IMAGE')
        indices = mathutils.geometry.tessellate_polygon((coords, ))
        batch = batch_for_shader(shader, 'TRIS', {"pos": coords, "texCoord": coords, }, indices=indices, )
        
        with gpu.matrix.push_pop():
            gpu.matrix.translate(position)
            gpu.matrix.scale((width, height))
            gpu.state.blend_set('ALPHA')
            shader.bind()
            shader.uniform_sampler("image", texture)
            batch.draw(shader)
            gpu.state.blend_set('NONE')
        
        # then draw box fill
        w = cls._max_line_width
        h = cls._total_height
        p = cls.BOX_OUTER_PADDING
        a = [p + x_correction, p]
        b = [w + p + x_correction, h + p]
        # color = (0.3, 0.3, 0.3, 0.5)
        color = cls.BOX_FILL_COLOR
        vertices, indices = cls._rounded_rectangle(a, b, cls.BOX_CORNER_RADIUS, steps=32, )
        if(bpy.app.version < (3, 4, 0)):
            shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
        else:
            shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'TRIS', {'pos': vertices, }, indices=indices, )
        gpu.state.blend_set('ALPHA')
        shader.bind()
        shader.uniform_float('color', color, )
        batch.draw(shader)
        gpu.state.blend_set('NONE')
        
        # and lastly draw box outline to have it looking antialiased
        o = 0
        a = [p - o + x_correction, p - o]
        b = [w + p + o + x_correction, h + p + o]
        vertices, indices = cls._rounded_rectangle(a, b, cls.BOX_CORNER_RADIUS, steps=32 * 2, )
        color = cls.BOX_OUTLINE_COLOR
        # thickness = 2
        thickness = cls._theme._info_box_outline_thickness
        z = np.zeros(len(vertices), dtype=np.float32, )
        vs = np.c_[vertices[:, 0], vertices[:, 1], z]
        i = np.arange(len(vs), dtype=np.int32, )
        indices = np.c_[i, np.roll(i, -1), ]
        if(bpy.app.version < (3, 4, 0)):
            shader = gpu.shader.from_builtin('3D_POLYLINE_UNIFORM_COLOR')
        else:
            shader = gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'LINES', {'pos': vs, }, indices=indices, )
        gpu.state.blend_set('ALPHA')
        shader.bind()
        shader.uniform_float('color', color, )
        # shader.uniform_float("lineSmooth", True, )
        shader.uniform_float("lineWidth", thickness, )
        _, _, w, h = gpu.state.viewport_get()
        shader.uniform_float("viewportSize", (w, h, ))
        batch.draw(shader)
        gpu.state.blend_set('NONE')
    
    @classmethod
    def _draw_text(cls, ):
        x = cls.BOX_OUTER_PADDING + cls.TEXT_PADDING
        y = cls.BOX_OUTER_PADDING + cls.TEXT_PADDING
        
        # TODO: this should be called just once per viewport, no need to do it 3 times for each viewport, but like that is easy to implement now..
        # NOTE: fix info location when region overlap is enabled
        x_correction = 0
        if(bpy.context.preferences.system.use_region_overlap):
            vwx, vwy, vww, vwh = gpu.state.viewport_get()
            for window in bpy.context.window_manager.windows:
                screen = window.screen
                for area in screen.areas:
                    if(area.type == 'VIEW_3D'):
                        wh = -1
                        th = -1
                        tw = -1
                        ok = False
                        for r in area.regions:
                            if(r.type == 'TOOLS'):
                                th = r.height
                                tw = r.width
                            if(r.type == 'WINDOW'):
                                if(r.width == vww and r.height == vwh):
                                    ok = True
                                wh = r.height
                        if(ok):
                            # if(wh > 0 and th > 0 and tw > 0 and wh == th):
                            if(wh > 0 and th > 0 and tw > 0):
                                x_correction = tw
        
        x += x_correction
        
        # loop from last item in list (should be logo), the rest should be lines of text (or dividers)
        for i, item in enumerate(reversed(cls.INFO)):
            s = int(round(item['style']['size'] * cls.UI_SCALE))
            
            if(bpy.app.version < (4, 0, 0)):
                blf.size(cls.FONT_ID, s, 72)
            else:
                # 4.0, `dpi` argument is removed
                blf.size(cls.FONT_ID, s)
            blf.color(cls.FONT_ID, *item['style']['color'])
            blf.enable(cls.FONT_ID, blf.SHADOW)
            blf.shadow(cls.FONT_ID, 3, 0.0, 0.0, 0.0, 0.5)
            blf.shadow_offset(cls.FONT_ID, 0, -2)
            
            for j, t in enumerate(reversed(item['text'])):
                if(t is None):
                    l = int(np.ceil(item['style']['separator'] * cls.UI_SCALE))
                    y += l
                    continue
                
                w, _ = blf.dimensions(cls.FONT_ID, t)
                _, h = blf.dimensions(cls.FONT_ID, 'F')
                ml = int(np.ceil(item['style']['margin_left'] * cls.UI_SCALE))
                l = int(np.ceil(item['style']['line_height'] * cls.UI_SCALE))
                
                blf.position(cls.FONT_ID, x + ml, y, 0, )
                blf.draw(cls.FONT_ID, t)
                
                if('line' in item):
                    # divider
                    yy = y + int(l / 2) - (item['style']['size'] * cls.UI_SCALE) - (1 * cls.UI_SCALE)
                    a = (x + ml, yy, )
                    # TODO: this might not be right, some combinations of paddings cause line to be longer then it should be. and it also displaces logo, but that is unrelated to lines
                    b = (x + cls._max_line_width - cls.BOX_OUTER_PADDING, yy, )
                    cls._thick_line_2d(a, b, color=item['style']['color'], thickness=item['style']['size'] * cls.UI_SCALE, )
                
                if('logo' in item):
                    # call logo function
                    cls._draw_logo(item['height'], )
                
                y += l
    
    @classmethod
    def _post_pixel_handler(cls, ):
        if(cls._draw):
            region = bpy.context.region
            
            # NOTE: in order to limit drawing to invoke region, all operators that are using infobox must:
            # NOTE: - store VALID id string somewhere (preferably ToolBox class type)
            # NOTE: - store VALID reference to itself somewhere (preferably ToolBox class type)
            # NOTE: - store VALID reference to invoke region in itself as `_invoke_region`
            # NOTE: - do NOT allow user to change window layout so invoke region reference stays valid (so have a check for region in modal and consume events from outside)
            # NOTE: - have a check below
            
            # so, some do this anyway because other reasons..
            
            # NOTE: v1
            # NOTE: manual mode brushes and bezier mask draw tool
            try:
                from ..manual.brushes import ToolBox
                if(ToolBox.tool is not None):
                    if(ToolBox.reference is not None):
                        if(ToolBox.reference._invoke_region != region):
                            return
                from ..curve.draw_bezier_area import ToolBox
                if(ToolBox.tool is not None):
                    if(ToolBox.reference is not None):
                        if(ToolBox.reference._invoke_region != region):
                            return
            except Exception as e:
                # something went wrong, draw it anyway, but log a problem, errors in draw callback do not show error popup
                import traceback
                traceback.print_exc()
            
            # NOTE: OR (easier method) subclass, instatiate, supply region reference from operator itself by `self.help._draw_in_this_region_only = context.region`
            
            # other tools does not because they don't have to..
            
            # NOTE: v2
            # NOTE: SCATTER5_OT_add_psy_modal, SCATTER5_OT_scatter_texture_visualizer, SCATTER5_OT_facesel_to_vcol
            try:
                if(cls._draw_in_this_region_only is not None):
                    # check only if set to anything, don't want to break other uses
                    if(cls._draw_in_this_region_only != region):
                        return
            except Exception as e:
                # something went wrong, draw it anyway, but log a problem, errors in draw callback do not show error popup
                import traceback
                traceback.print_exc()
            
            cls._draw_box()
            cls._draw_text()
    
    @classmethod
    def _tag_redraw(cls, ):
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if(area.type == 'VIEW_3D'):
                    area.tag_redraw()


# TODO: link values to widgets.theme.ToolTheme directly. i don't need them defined here
HEADER_COLOR = (1.0, 1.0, 1.0, 1.0, )
BODY_COLOR = (0.8, 0.8, 0.8, 1.0, )
# NOTE: these will be properly scaled by ui_scale and theme._info_box_scale later, these are values at final scale 1.0 @ 72dpi
H1 = (18, 26, )
H2 = (14, 20, )
P = (12, 16, )
P_SEPARATOR = 6
HEADER_LOGO_OFFSET = 22


def generic_infobox_setup(h1, h2, ls, ):
    '''
    h1 - main header line
    h2 - second header line
    - both header lines are offset to right to make space for logo
    - then divider line is drawn
    ls - list of shortcuts for brush
    '''
    
    _theme = ToolTheme()
    HEADER_COLOR = _theme._info_box_text_header_color
    BODY_COLOR = _theme._info_box_text_body_color
    
    t = [
        # sizes at 72 dpi
        {
            'style': {
                'size': H1[0],
                'color': HEADER_COLOR,
                'line_height': H1[1],
                'margin_left': HEADER_LOGO_OFFSET,
            },
            # should be fixed for each mode
            'text': [h1, ],
        },
        {
            'style': {
                'size': H2[0],
                'color': HEADER_COLOR,
                'line_height': H2[1],
                'margin_left': HEADER_LOGO_OFFSET,
            },
            # should be fixed for each mode
            'text': [h2, ],
        },
        {
            'style': {
                'size': 2,
                'color': HEADER_COLOR,
                'line_height': 12,
                'margin_left': 0,
            },
            'text': ["", ],
            # divider line
            'line': True,
        },
        {
            'style': {
                'size': P[0],
                'color': BODY_COLOR,
                'line_height': P[1],
                'margin_left': 0,
                'separator': P_SEPARATOR,
            },
            'text': ls,
        },
        {
            # logo have to be as last element (i.e. reversed >> first) so i don't have messed up line spacing. and it contains nothing, zero sizes. draw function will make everything..
            'style': {'size': 0, 'color': HEADER_COLOR, 'line_height': 0, 'margin_left': 0, },
            'text': ["", ],
    
            'logo': True,
            # it is always in top left corner..
            # line 1: 26 + line 2: 20 = 46 - 10 padding - 2 = 34.. don't ask me why, but looks better..
            'height': 34,
        },
    ]
    return t


'''
class SCATTER5_OT_infobox_test_operator(bpy.types.Operator, ):
    bl_idname = "scatter5.infobox_test_operator"
    bl_label = "InfoBox Test Operator"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        print("start..")
    
    def __del__(self):
        print("end.")
    
    def modal(self, context, event):
        if(event.type in {'ESC', }):
            print("exiting..")
            
            SC5InfoBox.deinit()
            
            return {'CANCELLED'}
        
        return {'PASS_THROUGH'}
    
    def invoke(self, context, event):
        print("invoke..")
        
        ls = ["• Press 'ANY' key to continue"] * 5
        ls = ['{} ({})'.format(t, i) for i, t in enumerate(ls)]
        t = generic_infobox_setup("Manual Distribution Mode",
                                  "Brush Name",
                                  ls, )
        SC5InfoBox.init(t)
        
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


class SCATTER5_OT_infobox_test_operator2(bpy.types.Operator, ):
    bl_idname = "scatter5.infobox_test_operator2"
    bl_label = "InfoBox Test Operator"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        print("start..")
    
    def __del__(self):
        print("end.")

    class SC5InfoBox_TestOp2(SC5InfoBox):
        pass
    
    def modal(self, context, event):
        if(event.type in {'RET', }):
            print("exiting..")
            
            self.SC5InfoBox_TestOp2.deinit()
            
            return {'CANCELLED'}
        
        return {'PASS_THROUGH'}
    
    def invoke(self, context, event):
        print("invoke..")
        
        t = generic_infobox_setup("Another test",
                                  "Brush Name",
                                  ["• Press 'ANY' key to continue"] * 10, )
        self.SC5InfoBox_TestOp2.init(t)
        
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
'''


classes = ()

'''
if(bpy.app.debug_value != 0):
    classes += (SCATTER5_OT_infobox_test_operator, )
'''
