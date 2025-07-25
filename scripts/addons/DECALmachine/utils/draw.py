import bpy
import blf
from mathutils import Vector, Matrix
import gpu
from gpu_extras.batch import batch_for_shader
from . registration import get_prefs
from . import math as m
from .. colors import yellow, green

def draw_point(co, mx=Matrix(), color=(1, 1, 1), size=6, alpha=1, xray=True, modal=True, screen=False):
    def draw():
        gpu.state.depth_test_set('NONE' if xray else 'LESS_EQUAL')
        gpu.state.blend_set('ALPHA' if alpha < 1 else 'NONE')
        gpu.state.point_size_set(size)

        shader = gpu.shader.from_builtin('POINT_UNIFORM_COLOR' if bpy.app.version >= (4, 5, 0) else 'UNIFORM_COLOR')
        shader.uniform_float("color", (*color, alpha))
        shader.bind()

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
        gpu.state.depth_test_set('NONE' if xray else 'LESS_EQUAL')
        gpu.state.blend_set('ALPHA' if alpha < 1 else 'NONE')
        gpu.state.point_size_set(size)

        shader = gpu.shader.from_builtin('POINT_UNIFORM_COLOR' if bpy.app.version >= (4, 5, 0) else 'UNIFORM_COLOR')
        shader.uniform_float("color", (*color, alpha))
        shader.bind()

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

def draw_lines(coords, indices=None, mx=None, color=(1, 1, 1), width=1, alpha=1, xray=True, modal=True, screen=False):
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

        if mx:
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

def draw_lines2d(coords, color=(1, 1, 1), width:float=1, alpha:float=1):
    indices = [(i, i + 1) for i in range(0, len(coords), 2)]

    gpu.state.blend_set('ALPHA' if alpha < 1 else 'NONE')

    shader = gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
    shader.uniform_float("color", (*color, alpha))
    shader.uniform_float("lineWidth", width)
    shader.uniform_float("viewportSize", gpu.state.scissor_get()[2:])
    shader.bind()

    batch = batch_for_shader(shader, 'LINES', {"pos": coords}, indices=indices)
    batch.draw(shader)

def draw_tris(coords, indices=None, mx=Matrix(), color=(1, 1, 1), alpha=1, xray=True, modal=True):
    def draw():

        gpu.state.depth_test_set('NONE' if xray else 'LESS_EQUAL')
        gpu.state.blend_set('ALPHA' if alpha < 1 else 'NONE')

        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        shader.uniform_float("color", (*color, alpha))
        shader.bind()

        if mx != Matrix():
            batch = batch_for_shader(shader, 'TRIS', {"pos": [mx @ co for co in coords]}, indices=indices)

        else:
            batch = batch_for_shader(shader, 'TRIS', {"pos": coords}, indices=indices)

        batch.draw(shader)

    if modal:
        draw()

    else:
        bpy.types.SpaceView3D.draw_handler_add(draw, (), 'WINDOW', 'POST_VIEW')

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

def draw_fading_label(context, text='', y=100, gap=18, center=True, size=12, color=(1, 1, 1), alpha=1, time=5, delay=1, cancel=''):
    scale = context.preferences.system.ui_scale * get_prefs().modal_hud_scale

    if isinstance(text, list):

        coords = (context.region.width / 2, y + gap * (len(text) - 1) * scale)

        for idx, t in enumerate(text):
            line_coords = (coords[0], coords[1] - (idx * gap * scale))
            line_color = color if isinstance(color, tuple) else color[idx if idx < len(color) else len(color) - 1]

            bpy.ops.machin3.draw_decal_label(text=t, coords=line_coords, center=center, color=line_color, alpha=alpha, time=time + idx * delay, cancel=cancel)

    else:
        coords = (context.region.width / 2, y)

        bpy.ops.machin3.draw_decal_label(text=text, coords=coords, center=center, color=color, alpha=alpha, time=time, cancel=cancel)

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

def draw_trim_grid_VIEW3D(context):
    active = getattr(bpy.context, 'active_object', None)

    if active:
        coords = active.DM.get('trim_snapping_coords', None)

        if coords:

            for gidx, grid in enumerate(coords):
                width = gidx + 1

                if active.DM.trimsnappingobject:
                    if gidx == 0 and not active.DM.trimsnappingdraw or gidx == 1 and not active.DM.trimsnappingobjectedgesdraw:
                        continue

                    color = yellow if gidx == 0 else green
                    alpha = 0.2 + (gidx * 0.1)

                else:
                    color = yellow
                    alpha = 0.1 * (gidx + 1)

                draw_lines(grid, width=width, color=color, alpha=alpha)
