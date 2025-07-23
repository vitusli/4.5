from typing import Union
import bpy
import blf

import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Vector, Matrix, Quaternion

from math import pi, sin, cos

from . import math as m
from . registration import get_addon, get_addon_prefs, get_prefs

from .. colors import red

machin3tools = None

def vert_debug_print(debug, vert, msg, end="\n"):
    if debug:
        if type(debug) is list:
            if vert.index in debug:
                print(msg, end=end)
        else:
            print(msg, end=end)

def debug_draw_sweeps(self, sweeps, draw_loops=False, draw_handles=False):
    if draw_loops:
        self.loops = []

    if draw_handles:
        self.handles = []

    for sweep in sweeps:
        v1_co = sweep["verts"][0].co
        v2_co = sweep["verts"][1].co

        if draw_loops:
            loops = sweep.get("loops")

            if loops:
                remote1_co = loops[0][1]
                remote2_co = loops[1][1]

                self.loops.extend([v1_co, remote1_co, v2_co, remote2_co])

        if draw_handles:
            handles = sweep.get("handles")

            if handles:
                handle1_co = handles[0]
                handle2_co = handles[1]

                self.handles.extend([v1_co, handle1_co, v2_co, handle2_co])

def get_builtin_shader_name(name, prefix='3D'):
    if bpy.app.version >= (4, 0, 0):
        return name
    else:
        return f"{prefix}_{name}"

def draw_point(co, mx=Matrix(), color=(1, 1, 1), size=6, alpha=1, xray=True, modal=True, screen=False):
    def draw():
        shader = gpu.shader.from_builtin(get_builtin_shader_name('UNIFORM_COLOR'))
        shader.bind()
        shader.uniform_float("color", (*color, alpha))

        gpu.state.depth_test_set('NONE' if xray else 'LESS_EQUAL')
        gpu.state.blend_set('ALPHA' if alpha < 1 else 'NONE')
        gpu.state.point_size_set(size)

        batch = batch_for_shader(shader, 'POINTS', {"pos": [mx @ co]})
        batch.draw(shader)

    if modal:
        draw()

    elif screen:
        bpy.types.SpaceView3D.draw_handler_add(draw, (), 'WINDOW', 'POST_PIXEL')

    else:
        bpy.types.SpaceView3D.draw_handler_add(draw, (), 'WINDOW', 'POST_VIEW')

def draw_points(coords, indices=None, mx=Matrix(), color=(1, 1, 1), size=6, alpha=1, xray=True, modal=True, screen=False):
    def draw():
        shader = gpu.shader.from_builtin(get_builtin_shader_name('UNIFORM_COLOR'))
        shader.bind()
        shader.uniform_float("color", (*color, alpha))

        gpu.state.depth_test_set('NONE' if xray else 'LESS_EQUAL')
        gpu.state.blend_set('ALPHA' if alpha < 1 else 'NONE')
        gpu.state.point_size_set(size)

        if indices:
            if mx != Matrix():
                batch = batch_for_shader(shader, 'POINTS', {"pos": [mx @ co for co in coords]}, indices=indices)
            else:
                batch = batch_for_shader(shader, 'POINTS', {"pos": coords}, indices=indices)

        else:
            if mx != Matrix():
                batch = batch_for_shader(shader, 'POINTS', {"pos": [mx @ co for co in coords]})
            else:
                batch = batch_for_shader(shader, 'POINTS', {"pos": coords})

        batch.draw(shader)

    if modal:
        draw()

    elif screen:
        bpy.types.SpaceView3D.draw_handler_add(draw, (), 'WINDOW', 'POST_PIXEL')

    else:
        bpy.types.SpaceView3D.draw_handler_add(draw, (), 'WINDOW', 'POST_VIEW')

def draw_line(coords, indices=None, mx=Matrix(), color=(1, 1, 1), alpha=1, width=1, xray=True, modal=True, screen=False):
    def draw():
        nonlocal indices

        if indices is None:
            indices = [(i, i + 1) for i in range(0, len(coords)) if i < len(coords) - 1]

        gpu.state.depth_test_set('NONE' if xray else 'LESS_EQUAL')
        gpu.state.blend_set('ALPHA')

        shader = gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
        shader.uniform_float("color", (*color, alpha))
        shader.uniform_float("lineWidth", width)
        shader.uniform_float("viewportSize", gpu.state.scissor_get()[2:])
        shader.bind()

        batch = batch_for_shader(shader, 'LINES', {"pos": [mx @ co for co in coords]}, indices=indices)
        batch.draw(shader)

    if modal:
        draw()

    elif screen:
        bpy.types.SpaceView3D.draw_handler_add(draw, (), 'WINDOW', 'POST_PIXEL')

    else:
        bpy.types.SpaceView3D.draw_handler_add(draw, (), 'WINDOW', 'POST_VIEW')

def draw_lines(coords, indices=None, mx=Matrix(), color=(1, 1, 1), width=1, alpha=1, xray=True, modal=True, screen=False):
    def draw():
        nonlocal indices

        if not indices:
            indices = [(i, i + 1) for i in range(0, len(coords), 2)]

        gpu.state.depth_test_set('NONE' if xray else 'LESS_EQUAL')
        gpu.state.blend_set('ALPHA')

        shader = gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
        shader.uniform_float("color", (*color, alpha))
        shader.uniform_float("lineWidth", width)
        shader.uniform_float("viewportSize", gpu.state.scissor_get()[2:])
        shader.bind()

        if mx != Matrix():
            batch = batch_for_shader(shader, 'LINES', {"pos": [mx @ co for co in coords]}, indices=indices)
        else:
            batch = batch_for_shader(shader, 'LINES', {"pos": coords}, indices=indices)

        batch.draw(shader)

    if modal:
        draw()

    elif screen:
        bpy.types.SpaceView3D.draw_handler_add(draw, (), 'WINDOW', 'POST_PIXEL')

    else:
        bpy.types.SpaceView3D.draw_handler_add(draw, (), 'WINDOW', 'POST_VIEW')

def draw_vector(vector, origin=Vector((0, 0, 0)), mx=Matrix(), color=(1, 1, 1), width=1, alpha=1, fade=False, normal=False, xray=True, modal=True, screen=False):
    def draw():
        if normal:
            coords = [mx @ origin, mx @ origin + m.get_world_space_normal(vector, mx)]
        else:
            coords = [mx @ origin, mx @ origin + mx.to_3x3() @ vector]

        colors = ((*color, alpha), (*color, alpha / 10 if fade else alpha))

        gpu.state.depth_test_set('NONE' if xray else 'LESS_EQUAL')
        gpu.state.blend_set('ALPHA')

        shader = gpu.shader.from_builtin('POLYLINE_SMOOTH_COLOR')
        shader.uniform_float("lineWidth", width)
        shader.uniform_float("viewportSize", gpu.state.scissor_get()[2:])
        shader.bind()

        batch = batch_for_shader(shader, 'LINES', {"pos": coords, "color": colors})
        batch.draw(shader)

    if modal:
        draw()

    elif screen:
        bpy.types.SpaceView3D.draw_handler_add(draw, (), 'WINDOW', 'POST_PIXEL')

    else:
        bpy.types.SpaceView3D.draw_handler_add(draw, (), 'WINDOW', 'POST_VIEW')

def draw_vectors(vectors, origins, mx=Matrix(), color=(1, 1, 1), width=1, alpha=1, fade=False, normal=False, xray=True, modal=True, screen=False):
    def draw():
        coords = []
        colors = []

        for v, o in zip(vectors, origins):
            coords.append(mx @ o)

            if normal:
                coords.append(mx @ o + m.get_world_space_normal(v, mx))
            else:
                coords.append(mx @ o + mx.to_3x3() @ v)

            colors.extend([(*color, alpha), (*color, alpha / 10 if fade else alpha)])

        gpu.state.depth_test_set('NONE' if xray else 'LESS_EQUAL')
        gpu.state.blend_set('ALPHA')

        shader = gpu.shader.from_builtin('POLYLINE_SMOOTH_COLOR')
        shader.uniform_float("lineWidth", width)
        shader.uniform_float("viewportSize", gpu.state.scissor_get()[2:])
        shader.bind()

        batch = batch_for_shader(shader, 'LINES', {"pos": coords, "color": colors})
        batch.draw(shader)

    if modal:
        draw()

    elif screen:
        bpy.types.SpaceView3D.draw_handler_add(draw, (), 'WINDOW', 'POST_PIXEL')

    else:
        bpy.types.SpaceView3D.draw_handler_add(draw, (), 'WINDOW', 'POST_VIEW')

def draw_circle(loc=Vector(), rot=Quaternion(), radius=100, segments='AUTO', width=1, color=(1, 1, 1), alpha=1, xray=True, modal=True, screen=False):
    def draw():
        nonlocal segments

        if segments == 'AUTO':
            segments = max(int(radius), 16)

        else:
            segments = max(segments, 16)

        indices = [(i, i + 1) if i < segments - 1 else (i, 0) for i in range(segments)]

        coords = []

        for i in range(segments):

            theta = 2 * pi * i / segments

            x = loc.x + radius * cos(theta)
            y = loc.y + radius * sin(theta)

            coords.append(Vector((x, y, 0)))

        gpu.state.depth_test_set('NONE' if xray else 'LESS_EQUAL')
        gpu.state.blend_set('ALPHA')

        shader = gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
        shader.uniform_float("color", (*color, alpha))
        shader.uniform_float("lineWidth", width)
        shader.uniform_float("viewportSize", gpu.state.scissor_get()[2:])
        shader.bind()

        batch = batch_for_shader(shader, 'LINES', {"pos": [rot @ co for co in coords]}, indices=indices)
        batch.draw(shader)

    if modal:
        draw()

    elif screen:
        bpy.types.SpaceView3D.draw_handler_add(draw, (), 'WINDOW', 'POST_PIXEL')

    else:
        bpy.types.SpaceView3D.draw_handler_add(draw, (), 'WINDOW', 'POST_VIEW')

def draw_mesh_wire(batch, color=(1, 1, 1), width=1, alpha=1, xray=True, modal=True):
    def draw():
        nonlocal batch
        coords, indices = batch

        gpu.state.depth_test_set('NONE' if xray else 'LESS_EQUAL')
        gpu.state.blend_set('ALPHA')

        shader = gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
        shader.uniform_float("color", (*color, alpha))
        shader.uniform_float("lineWidth", width)
        shader.uniform_float("viewportSize", gpu.state.scissor_get()[2:])
        shader.bind()

        b = batch_for_shader(shader, 'LINES', {"pos": coords}, indices=indices)
        b.draw(shader)

        del shader
        del b

    if modal:
        draw()

    else:
        bpy.types.SpaceView3D.draw_handler_add(draw, (), 'WINDOW', 'POST_VIEW')

def update_HUD_location(self, event, offsetx=20, offsety=20):
    self.HUD_x = event.mouse_x - self.region_offset_x + offsetx
    self.HUD_y = event.mouse_y - self.region_offset_y + offsety

def draw_init(self):
    self.font_id = 1
    self.offset = 0

def get_text_dimensions(context, text='', size=12):

    scale = context.preferences.system.ui_scale * get_prefs().modal_hud_scale

    font = 1
    fontsize = int(size * scale)

    blf.size(font, fontsize)
    return Vector(blf.dimensions(font, text))

def draw_label(context, title='', coords=None, offset=0, center=True, size=12, color=(1, 1, 1), alpha=1):
    if not coords:
        region = context.region
        width = region.width / 2
        height = region.height / 2
    else:
        width, height = coords

    scale = context.preferences.system.ui_scale * get_prefs().modal_hud_scale

    font = 1
    fontsize = int(size * scale)

    blf.size(font, fontsize)
    blf.color(font, *color, alpha)

    if center:
        dims = blf.dimensions(font, title)
        blf.position(font, width - (dims[0] / 2), height - (offset * scale), 1)

    else:
        blf.position(font, width, height - (offset * scale), 1)

    blf.draw(font, title)

    return blf.dimensions(font, title)

def draw_stashes_HUD(context, stashes_count, invalid_stashes_count):
    global machin3tools

    if machin3tools is None:
        machin3tools = get_addon('MACHIN3tools')[0]

    region = context.region
    view = context.space_data
    bprefs = context.preferences

    if stashes_count > 0 and len(context.selected_objects) > 0 and view.overlay.show_overlays:
        region_overlap = bprefs.system.use_region_overlap
        header_alpha = bprefs.themes['Default'].view_3d.space.header[3]

        top_header = [r for r in context.area.regions if r.type == 'HEADER' and r.alignment == 'TOP']
        top_tool_header = [r for r in context.area.regions if r.type == 'TOOL_HEADER' and r.alignment == 'TOP']

        scale = context.preferences.system.ui_scale * get_prefs().modal_hud_scale

        offset_y = 5 * scale

        if region_overlap:

            if top_header and header_alpha < 1:
                offset_y += top_header[0].height

            if top_tool_header:
                offset_y += top_tool_header[0].height

        if machin3tools and context.scene.M3.focus_history:
            machin3tools_scale = context.preferences.system.ui_scale * get_addon_prefs('MACHIN3tools').modal_hud_scale

            offset_y += 5 * machin3tools_scale + 12 * machin3tools_scale

        color = get_prefs().modal_hud_color
        font = 1
        fontsize = int(12 * scale)

        blf.size(font, fontsize)

        full_text = f"Stashes: {stashes_count}"

        if invalid_stashes_count:
            full_text += f" ({invalid_stashes_count} invalid)"

        offset_x = (blf.dimensions(font, full_text)[0] / 2)

        left_side = (region.width / 2) - offset_x

        title = 'Stashes: '
        dims = blf.dimensions(font, title)
        blf.color(font, *color, 0.5)
        blf.position(font,  left_side, region.height - offset_y - fontsize, 0)
        blf.draw(font, title)

        title = f"{stashes_count}"
        blf.color(font, *color, 1)
        dims2 = blf.dimensions(font, title)
        blf.position(font,  left_side + dims[0], region.height - offset_y - fontsize, 0)
        blf.draw(font, title)

        if invalid_stashes_count:
            title = f" ({invalid_stashes_count} invalid)"
            blf.color(font, *red, 1)
            blf.position(font, left_side + dims[0] + dims2[0], region.height - offset_y - fontsize, 0)
            blf.draw(font, title)

def draw_edit_stash_HUD(context, color=(1, 1, 1), alpha=1, width=2, title="", subtitle=""):
    global machin3tools

    if machin3tools is None:
        machin3tools = get_addon('MACHIN3tools')[0]

    region = context.region
    view = context.space_data
    bprefs = context.preferences

    if view.overlay.show_overlays:
        region_overlap = bprefs.system.use_region_overlap
        header_alpha = bprefs.themes['Default'].view_3d.space.header[3]

        top_header = [r for r in context.area.regions if r.type == 'HEADER' and r.alignment == 'TOP']
        top_tool_header = [r for r in context.area.regions if r.type == 'TOOL_HEADER' and r.alignment == 'TOP']

        scale = context.preferences.system.ui_scale * get_prefs().modal_hud_scale

        coords = [(width, width), (region.width - width, width), (region.width - width, region.height - width), (width, region.height - width)]
        indices =[(0, 1), (1, 2), (2, 3), (3, 0)]

        shader = gpu.shader.from_builtin(get_builtin_shader_name('UNIFORM_COLOR', prefix='2D'))
        shader.bind()
        shader.uniform_float("color", (*color, alpha))

        gpu.state.depth_test_set('NONE')
        gpu.state.blend_set('ALPHA' if alpha < 1 else 'NONE')
        gpu.state.line_width_set(width)

        batch = batch_for_shader(shader, 'LINES', {"pos": coords}, indices=indices)
        batch.draw(shader)

        offset_y = 5 * scale

        if region_overlap:

            if top_header and header_alpha < 1:
                offset_y += top_header[0].height

            if top_tool_header:
                offset_y += top_tool_header[0].height

        if machin3tools and context.scene.M3.focus_history:
            machin3tools_scale = context.preferences.system.ui_scale * get_addon_prefs('MACHIN3tools').modal_hud_scale

            offset_y += 5 * machin3tools_scale + 12 * machin3tools_scale

        font_color = get_prefs().modal_hud_color
        font = 1
        fontsize = int(16 * scale)

        center = region.width / 2

        blf.size(font, fontsize)
        blf.color(font, *font_color, 0.5)

        dims = blf.dimensions(font, title)
        blf.position(font, center - int(dims[0] / 2), region.height - offset_y - fontsize, 0)

        blf.draw(font, title)

        offset_y += dims[1] + 5 * scale

        fontsize = int(10 * scale)
        blf.size(font, fontsize)
        blf.color(font, *color, 1)

        dims = blf.dimensions(font, subtitle)
        blf.position(font, center - int(dims[0] / 2), region.height - offset_y - fontsize, 0)

        blf.draw(font, subtitle)

def draw_fading_label(context, text:Union[str, list]='', x=None, y:float=100, gap=18, center=True, size=12, color:Union[tuple, list]=(1, 1, 1), alpha:Union[float, list]=1, move_y=0, time=5, delay=1, cancel=''):
    scale = context.preferences.system.ui_scale * get_prefs().modal_hud_scale

    if x is None:
        x = (context.region.width / 2)

    if isinstance(text, list):

        coords = (x, y + gap * (len(text) - 1) * scale)

        for idx, t in enumerate(text):
            line_coords = (coords[0], coords[1] - (idx * gap * scale))
            line_color = color if isinstance(color, tuple) else color[idx if idx < len(color) else len(color) - 1]
            line_alpha = alpha if (isinstance(alpha, int) or isinstance(alpha, float)) else alpha[idx if idx < len(alpha) else len(alpha) - 1]
            line_move = int(move_y + (idx * gap)) if move_y > 0 else 0
            line_time = time + idx * delay

            bpy.ops.machin3.draw_meshmachine_label(text=t, coords=line_coords, center=center, size=size, color=line_color, alpha=line_alpha, move_y=line_move, time=line_time, cancel=cancel)

    else:
        coords = (x, y)

        bpy.ops.machin3.draw_meshmachine_label(text=text, coords=coords, center=center, size=size, color=color, alpha=alpha, move_y=move_y, time=time, cancel=cancel)

def draw_stashes_VIEW3D(scene, batch):
    draw_mesh_wire(batch, color=(0.4, 0.7, 1), xray=scene.MM.draw_active_stash_xray, alpha=0.4)

def draw_split_row(self, layout, prop='prop', text='', label='Label', factor=0.2, align=True, toggle=True, expand=True, info=None, warning=None):
    row = layout.row(align=align)
    split = row.split(factor=factor, align=align)

    text = text if text else str(getattr(self, prop)) if str(getattr(self, prop)) in ['True', 'False'] else ''
    split.prop(self, prop, text=text, toggle=toggle, expand=expand)

    if label:
        split.label(text=label)

    if info:
        split.label(text=info, icon='INFO')

    if warning:
        split.label(text=warning, icon='ERROR')

    return row

def draw_empty_split_row(self, layout, text='', text2='', factor=0.2, align=True):
    row = layout.row(align=align)
    split = row.split(factor=factor, align=align)
    split.label(text=text)
    split.label(text=text2)
