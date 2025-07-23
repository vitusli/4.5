import bpy
from typing import Union

from mathutils import Vector, Matrix, Quaternion
from math import sin, cos, pi, radians
import gpu
from gpu_extras.batch import batch_for_shader
import blf

from copy import deepcopy

from . import ui
from . import view

from . math import get_world_space_normal, compare_matrix, transform_coords
from . registration import get_prefs
from . tools import get_active_tool

from .. colors import red, green, blue, yellow, white

def draw_point(co, mx=Matrix(), color=(1, 1, 1), size=6, alpha:float=1, xray=True, modal=True, screen=False):
    def draw():
        if len(co) == 2:
            co.resize(3)

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

def draw_points(coords, indices=None, mx=Matrix(), color=(1, 1, 1), size=6, alpha:float=1, xray=True, modal=True, screen=False):
    def draw():
        gpu.state.depth_test_set('NONE' if xray else 'LESS_EQUAL')
        gpu.state.blend_set('ALPHA' if alpha < 1 else 'NONE')
        gpu.state.point_size_set(size)

        shader = gpu.shader.from_builtin('POINT_UNIFORM_COLOR' if bpy.app.version >= (4, 5, 0) else 'UNIFORM_COLOR')
        shader.uniform_float("color", (*color, alpha))
        shader.bind()

        if indices:
            batch = batch_for_shader(shader, 'POINTS', {"pos": transform_coords(coords, mx)}, indices=indices)

        else:
            batch = batch_for_shader(shader, 'POINTS', {"pos": transform_coords(coords, mx)})

        batch.draw(shader)

    if modal:
        draw()

    elif screen:
        bpy.types.SpaceView3D.draw_handler_add(draw, (), 'WINDOW', 'POST_PIXEL')

    else:
        bpy.types.SpaceView3D.draw_handler_add(draw, (), 'WINDOW', 'POST_VIEW')

def draw_line(coords, indices=None, mx=Matrix(), color=(1, 1, 1), alpha:float=1, width=1, xray=True, modal=True, screen=False):
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

        batch = batch_for_shader(shader, 'LINES', {"pos": transform_coords(coords, mx)}, indices=indices)
        batch.draw(shader)

    if modal:
        draw()

    elif screen:
        bpy.types.SpaceView3D.draw_handler_add(draw, (), 'WINDOW', 'POST_PIXEL')

    else:
        bpy.types.SpaceView3D.draw_handler_add(draw, (), 'WINDOW', 'POST_VIEW')

def draw_lines(coords, indices=None, mx=Matrix(), color=(1, 1, 1), width=1, alpha:float=1, xray=True, modal=True, screen=False):
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

        batch = batch_for_shader(shader, 'LINES', {"pos": transform_coords(coords, mx)}, indices=indices)
        batch.draw(shader)

    if modal:
        draw()

    elif screen:
        bpy.types.SpaceView3D.draw_handler_add(draw, (), 'WINDOW', 'POST_PIXEL')

    else:
        bpy.types.SpaceView3D.draw_handler_add(draw, (), 'WINDOW', 'POST_VIEW')

def draw_vector(vector, origin=Vector((0, 0, 0)), mx=Matrix(), color=(1, 1, 1), width=1, alpha:float=1, fade=False, normal=False, xray=True, modal=True, screen=False):
    def draw():
        if normal:
            coords = [mx @ origin, mx @ origin + get_world_space_normal(vector, mx)]
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
                coords.append(mx @ o + get_world_space_normal(v, mx))
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

def draw_circle(loc=Vector(), rot=Quaternion(), radius:float=100, segments:Union[str, int]='AUTO', width:float=1, color=(1, 1, 1), alpha:float=1, xray=True, modal=True, screen=False):
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

            x = radius * cos(theta)
            y = radius * sin(theta)

            coords.append(Vector((x, y, 0)))

        gpu.state.depth_test_set('NONE' if xray else 'LESS_EQUAL')
        gpu.state.blend_set('ALPHA')

        shader = gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
        shader.uniform_float("color", (*color, alpha))
        shader.uniform_float("lineWidth", width)
        shader.uniform_float("viewportSize", gpu.state.scissor_get()[2:])
        shader.bind()

        if len(loc) == 2:
            mx = Matrix()
            mx.col[3] = loc.resized(4)
            batch = batch_for_shader(shader, 'LINES', {"pos": [mx @ co for co in coords]}, indices=indices)

        else:
            mx = Matrix.LocRotScale(loc, rot, Vector.Fill(3, 1))
            batch = batch_for_shader(shader, 'LINES', {"pos": [mx @ co for co in coords]}, indices=indices)

        batch.draw(shader)

    if modal:
        draw()

    elif screen:
        bpy.types.SpaceView3D.draw_handler_add(draw, (), 'WINDOW', 'POST_PIXEL')

    else:
        bpy.types.SpaceView3D.draw_handler_add(draw, (), 'WINDOW', 'POST_VIEW')

def draw_pie_circle(loc=Vector(), rot=Quaternion(), radius=100, segments='AUTO', pies=5, active=0, rot_offset=0, width=1, color=(1, 1, 1), active_color=(1, 1, 1), gap=0, alpha=1, active_alpha=1, xray=True, modal=True, screen=False):
    def draw():
        nonlocal segments

        if segments == 'AUTO':
            segments = max(int(radius) - (int(radius) % pies), pies * 3)

        else:
            segments = max(segments - (segments % pies), pies * 3)

        circle_coords = []
        gap_coords = []
        pie_coords = []

        for i in range(segments):

            theta = 2 * pi * i / segments

            x = radius * cos(theta)
            y = radius * sin(theta)

            circle_coords.append(Vector((x, y, 0)))

            if gap:
                gap_coords.append(Vector((x, y, 0)) * gap)

            if gap:
                if i % (segments / pies) == 0:
                    if pie_coords:
                        inner_ring = gap_coords[-int(segments / pies) - 1:]
                        pie_coords[-1].extend([Vector((x, y, 0)), *reversed(inner_ring)])

                    pie_coords.append([Vector((x, y, 0)) * gap, Vector((x, y, 0))])

                else:
                    pie_coords[-1].append(Vector((x, y, 0)))

                if i == segments - 1:
                    inner_ring = gap_coords[-int(segments / pies):]
                    pie_coords[-1].extend([pie_coords[0][1], gap_coords[0], *reversed(inner_ring)])

            else:
                if i % (segments / pies) == 0:
                    if pie_coords:
                        pie_coords[-1].extend([Vector((x, y, 0)), Vector()])

                    pie_coords.append([Vector(), Vector((x, y, 0))])

                else:
                    pie_coords[-1].append(Vector((x, y, 0)))

                if i == segments - 1:
                    pie_coords[-1].extend([pie_coords[0][1], Vector()])

        offset_rot = Quaternion((0, 0, 1), radians(rot_offset - (360 / pies / 2)))

        if len(loc) == 2:
            mx = Matrix.LocRotScale(loc, offset_rot, Vector.Fill(3, 1))

        else:
            mx = Matrix.LocRotScale(loc, rot @ offset_rot, Vector.Fill(3, 1))

        ring_indices = [(i, i + 1) if i < segments - 1 else (i, 0) for i in range(segments)]

        draw_line(circle_coords, indices=ring_indices, mx=mx, width=width, color=color, alpha=alpha, xray=xray)

        if gap:
            draw_line(gap_coords, indices=ring_indices, mx=mx, width=width, color=color, alpha=alpha, xray=xray)

        for idx, coords in enumerate(pie_coords):

            if idx == active:
                draw_line(coords, mx=mx, width=width, color=active_color, alpha=active_alpha, xray=xray)

                if gap:
                    tri_coords = coords[1:-1] + [coords[0]]
                    tri_indices = [(i, i + 1, len(tri_coords) - i - 1) for i in range(len(tri_coords) - 1)]

                else:
                    tri_coords = coords[:-1]
                    tri_indices = [(0, i + 1, i + 2) for i in range(len(tri_coords) - 2)]

                draw_tris(tri_coords, indices=tri_indices, mx=mx, color=active_color, alpha=active_alpha/ 4, xray=xray)

            else:
                draw_line(coords, mx=mx, width=int(width / 2), color=color, alpha=alpha, xray=xray)

    if modal:
        draw()

    elif screen:
        bpy.types.SpaceView3D.draw_handler_add(draw, (), 'WINDOW', 'POST_PIXEL')

    else:
        bpy.types.SpaceView3D.draw_handler_add(draw, (), 'WINDOW', 'POST_VIEW')

def draw_tris(coords, indices=None, mx=Matrix(), color=(1, 1, 1), alpha:float=1, xray=True, modal=True):
    def draw():

        gpu.state.depth_test_set('NONE' if xray else 'LESS_EQUAL')
        gpu.state.blend_set('ALPHA' if alpha < 1 else 'NONE')

        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        shader.uniform_float("color", (*color, alpha))
        shader.bind()

        batch = batch_for_shader(shader, 'TRIS', {"pos": transform_coords(coords, mx)}, indices=indices)
        batch.draw(shader)

    if modal:
        draw()

    else:
        bpy.types.SpaceView3D.draw_handler_add(draw, (), 'WINDOW', 'POST_VIEW')

def draw_batch(batch, color=(1, 1, 1), width:int=1, alpha:float=1, xray=True, modal=True):
    def draw():
        nonlocal batch

        coords, indices = batch[:2]

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

def draw_init(self):
    self.offset = 0

def get_text_dimensions(context, text='', size=12):

    ui_scale = ui.get_scale(context)

    font = 1
    fontsize = int(size * ui_scale)

    blf.size(font, fontsize)
    return Vector(blf.dimensions(font, text))

def draw_label(context, title='', coords:Union[None, Vector]=None, offset=0, center=True, size=12, color=(1, 1, 1), alpha:float=1):
    if coords is None:
        region = context.region
        width = region.width / 2
        height = region.height / 2
    else:
        width, height = coords

    ui_scale = ui.get_scale(context)

    shadow = get_prefs().modal_hud_shadow

    font = 1
    fontsize = int(size * ui_scale)

    if shadow:
        shadow_blur = int(get_prefs().modal_hud_shadow_blur)
        shadow_offset = round(get_prefs().modal_hud_shadow_offset * ui_scale)

    blf.size(font, fontsize)
    blf.color(font, *color, alpha)

    if shadow:
        blf.enable(font, blf.SHADOW)
        blf.shadow(font, shadow_blur, 0, 0, 0, 1)
        blf.shadow_offset(font, shadow_offset, -shadow_offset)

    if center:
        dims = Vector(blf.dimensions(font, title))
        blf.position(font, width - (dims.x / 2), height - (offset * ui_scale), 1)

    else:
        blf.position(font, width, height - (offset * ui_scale), 1)

    blf.draw(font, title)

    if shadow:
        blf.disable(font, blf.SHADOW)

    return Vector(blf.dimensions(font, title))

def draw_fading_label(context, text:Union[str, list[str]]='', x=None, y=100, gap=18, center=True, size=12, color=(1, 1, 1), alpha:Union[int, float, list]=1, move_y=0, time=5, delay=1, cancel=''):
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

            bpy.ops.machin3.draw_hyper_cursor_label(text=t, coords=line_coords, center=center, size=size, color=line_color, alpha=line_alpha, move_y=line_move, time=line_time, cancel=cancel)

    else:
        coords = (x, y)

        bpy.ops.machin3.draw_hyper_cursor_label(text=text, coords=coords, center=center, size=size, color=color, alpha=alpha, move_y=move_y, time=time, cancel=cancel)

def draw_multi_label(self, context, labels:list=[str, float, tuple, float], dims=Vector((0, 0))):
    multi_dims = Vector((0, 0))

    for title, size, color, alpha in labels:
        multi_dims += draw_label(context, title=title, coords=Vector((self.HUD_x + dims.x + multi_dims.x, self.HUD_y)), offset=self.offset, size=size, center=False, color=color, alpha=alpha)

    return multi_dims

def draw_modifier_selection_title(self, context, title='Adjust', index=0, mods:list=[], additional=[], color=(1, 1, 1)):
    ui_scale = ui.get_scale(context)

    action = "Pick" if self.is_picking else title
    draw_label(context, title=action, coords=Vector((self.HUD_x, self.HUD_y)), center=False, color=color, alpha=1)

    action_dims = get_text_dimensions(context, text="Adjust ")

    if index > 0:
        self.offset -= (index - 1) * (18 if self.is_picking else 10) + 18

    for idx, mod in enumerate(mods):

        if idx < index:
            alpha = 0.3 if self.is_picking else (idx + 1) * (0.3 / (index + 1))
            draw_label(context, title=mod.name, coords=Vector((self.HUD_x + action_dims.x, self.HUD_y)), offset=self.offset, center=False, size=8, color=white, alpha=alpha)

            self.offset += 18 if (self.is_picking or idx == index - 1) else 10

        elif idx == index:

            if self.is_picking:
                coords = [Vector((self.HUD_x + action_dims.x - (5 * ui_scale), self.HUD_y - (self.offset * ui_scale), 0)), Vector((self.HUD_x + action_dims.x - (5 * ui_scale), self.HUD_y - (self.offset * ui_scale) + (10 * ui_scale), 0))]
                draw_line(coords, color=blue, width=2 * ui_scale, screen=True)

            current_mod_name_dims = draw_label(context, title=mod.name, coords=Vector((self.HUD_x + action_dims.x, self.HUD_y)), offset=self.offset, center=False, color=blue, alpha=1)

            if additional:
                current_mod_name_dims += draw_multi_label(self, context, additional, action_dims + current_mod_name_dims)

            if idx < len(mods) - 1:
                self.offset += 18

        else:
            alpha = 0.3 if self.is_picking else 0.3 - ((idx - index) * (0.3 / (len(mods) - index)))
            draw_label(context, title=mod.name, coords=Vector((self.HUD_x + action_dims.x, self.HUD_y)), offset=self.offset, center=False, size=8, color=white, alpha=alpha)

            if idx < len(mods) - 1:
                self.offset += 18 if self.is_picking else 10

    return action_dims + current_mod_name_dims

def draw_hyper_cursor_HUD(context):
    view = context.space_data

    from .. import HyperCursorManager as HC
    from . ui import is_on_screen

    if view.show_gizmo and context.scene.HC.show_gizmos and view.overlay.show_overlays:
        hc = context.scene.HC
        ui_scale = context.preferences.system.ui_scale

        active_tool = get_active_tool(context).idname

        if active_tool in ['machin3.tool_hyper_cursor', 'machin3.tool_hyper_cursor_simple'] and hc.show_gizmos and (hc.draw_HUD or hc.draw_pipe_HUD):
            coords = HC.props['cursor_2d']

            if is_on_screen(context, coords):
                if active_tool == 'machin3.tool_hyper_cursor':
                    offset = deepcopy(HC.props['HUD_offset'])

                    if hc.draw_pipe_HUD:
                        dims = get_text_dimensions(context, text="Pipe Mode", size=12)
                        draw_label(context, "Pipe Mode", coords=coords + offset['left'] - Vector((dims.x, 0)), center=False, size=12, color=blue, alpha=1)

                    if hc.draw_HUD:

                        if hc.use_world:
                            draw_label(context, "World Aligned", coords=coords + offset['top'], center=True, size=12, color=green, alpha=1)

                        is_current_stored = hc.historyCOL and compare_matrix(context.scene.cursor.matrix, hc.historyCOL[hc.historyIDX].mx)

                        if (hc.historyCOL and hc.show_button_history) or is_current_stored:

                            title = f"{hc.historyIDX + 1} "

                            color, alpha = (green, 1) if is_current_stored else (white, 0.3)
                            dims = draw_label(context, title, coords=coords + offset['right'], center=False, size=12, color=color, alpha=alpha)

                            offset['right'] += Vector((dims.x, 0))
                            title = f"/ {len(hc.historyCOL)} "
                            dims = draw_label(context, title, coords=coords + offset['right'], center=False, size=12, color=white, alpha=0.3)

                            if hc.auto_history:
                                offset['right'] += Vector((dims.x, 0))
                                draw_label(context, title="Auto History", coords=coords + offset['right'], center=False, size=12, color=green, alpha=1)

                        if is_current_stored:
                            draw_circle(coords, radius=10 * ui_scale, width=2 * ui_scale if active_tool == 'machin3.tool_hyper_cursor' else 1, segments=64, color=(0, 0.8, 0), alpha=1)

def draw_hyper_cursor_VIEW3D(context):
    view = context.space_data
    from .. import HyperCursorManager as HC

    if view.show_gizmo and context.scene.HC.show_gizmos and view.overlay.show_overlays:
        active_tool = get_active_tool(context).idname

        if context.scene.HC.draw_HUD:
            if active_tool == 'machin3.tool_hyper_cursor':
                if not view.overlay.show_cursor:
                    view.overlay.show_cursor = True

            elif active_tool == 'machin3.tool_hyper_cursor_simple':
                if view.overlay.show_cursor:
                    view.overlay.show_cursor = False

        if context.scene.HC.draw_cursor_axes:
            if active_tool == 'machin3.tool_hyper_cursor_simple':
                gizmo_scale = HC.props['gizmo_scale']

                axes = [(Vector((1, 0, 0)), red), (Vector((0, 1, 0)), green), (Vector((0, 0, 1)), blue)]

                cmx = context.scene.cursor.matrix
                corigin = cmx.decompose()[0]

                for axis, color in axes:
                    coords = [corigin + cmx.to_3x3() @ axis * gizmo_scale * 0.1, corigin + cmx.to_3x3() @ axis * gizmo_scale * 0.5]
                    draw_line(coords, color=color, width=2, alpha=1)
    else:
        if not view.overlay.show_cursor:
            view.overlay.show_cursor = True

get_zoom_factor = None

def draw_cursor_history(context):
    global get_zoom_factor

    view = context.space_data

    if view.overlay.show_overlays:
        if get_active_tool(context).idname in ['machin3.tool_hyper_cursor', 'machin3.tool_hyper_cursor_simple']:

            if not get_zoom_factor:
                from HyperCursor.utils.ui import get_zoom_factor

            hc = context.scene.HC

            if hc.historyCOL and hc.draw_history:

                locations = [entry.location for entry in hc.historyCOL.values()]

                active_location = locations[hc.historyIDX]

                inactive_locations = locations.copy()
                inactive_locations.pop(hc.historyIDX)

                draw_line(locations, width=1, alpha=0.2, modal=True)

                if inactive_locations:
                    draw_points(inactive_locations, size=4, alpha=0.5, modal=True)

                draw_point(active_location, alpha=1, color=yellow, modal=True)

                axes = [(Vector((1, 0, 0)), red), (Vector((0, 1, 0)), green), (Vector((0, 0, 1)), blue)]

                orientations = [entry.rotation for entry in hc.historyCOL.values()]

                active_orientation = orientations[hc.historyIDX]

                inactive_orientations = orientations.copy()
                inactive_orientations.pop(hc.historyIDX)

                for axis, color in axes:

                    size = 1
                    coords = []

                    for origin, orientation in zip(inactive_locations, inactive_orientations):
                        factor = get_zoom_factor(context, origin, scale=20, ignore_obj_scale=True)

                        coords.append(origin + (orientation @ axis).normalized() * size * factor * 0.1)
                        coords.append(origin + (orientation @ axis).normalized() * size * factor)

                    if coords:
                        draw_lines(coords, color=color, alpha=0.6)

                    size = 1.75
                    coords = []

                    factor = get_zoom_factor(context, active_location, scale=20, ignore_obj_scale=True)

                    coords.append(active_location + (active_orientation @ axis).normalized() * size * factor * 0.1)
                    coords.append(active_location + (active_orientation @ axis).normalized() * size * factor)

                    draw_line(coords, color=color, width=3, alpha=1)

def draw_cursor_history_names(context):
    if context.space_data.overlay.show_overlays:
        if get_active_tool(context).idname in ['machin3.tool_hyper_cursor', 'machin3.tool_hyper_cursor_simple']:
            hc = context.scene.HC

            if hc.historyCOL and hc.draw_history:
                ui_system_scale, gizmo_size = ui.get_scale(context, system_scale=True, modal_HUD=False, gizmo_size=True)
                ui_modal_scale = ui.get_scale(context, system_scale=False, modal_HUD=True, gizmo_size=False)

                locations = [(entry, view.get_location_2d(context, entry.location, default='OFF_SCREEN')) for entry in hc.historyCOL.values()]
                labels = {}

                for idx, (entry, loc) in enumerate(locations):

                    rounded = tuple([round(co) for co in loc])

                    entry.show = ui.is_on_screen(context, rounded)

                    if entry.show:
                        if rounded in labels:
                            labels[rounded].append(entry)
                        else:
                            labels[rounded] = [entry]

                        entry.co2d = rounded

                gap = 1.5

                for loc, entries in labels.items():
                    for idx, entry in enumerate(entries):
                        is_active = entry.index == hc.historyIDX

                        size, color, alpha = (12, yellow, 1) if is_active else (10, white, 0.5)
                        size *= (gizmo_size / ui_modal_scale)                                                                 # text in this row of the gizmos needs to adapt to discrepancies in gizmo_size vs modal_hud_scale, effectively this takes out all influence of modal HUD scaling

                        coords = entry.co2d + Vector((5, -4.5 if is_active else -3)) * gizmo_size * ui_system_scale           # offset text slightly, to compensate for gizmos being placed dead on the 2d coords, this ensures text perfectly lines up with the gizmos that follow on the y axis
                        dims_row = get_text_dimensions(context, f"{entry.name}", size=12 * (gizmo_size / ui_modal_scale))     # NOTE: we get a constant one based on a text size of 12, even if there are mixed sizes in the stack, this massively simplifies things
                        dims_label = get_text_dimensions(context, f"{entry.name}", size=size)                                 # here we get the horizontal dimensions, based on the actual text width

                        if idx:
                            coords -= Vector((0, dims_row[1])) * gap * idx                                                    # offset down based on the text height (+ some gap) + the position in the stack

                        draw_label(context, title=entry.name, coords=coords, center=False, size=size, color=color, alpha=alpha)

                        co2d = entry.co2d + Vector((dims_label[0], 0))                                                        # get gizmos 2d location, offset to the right based on the length of the history entry's name
                        co2d += Vector((15, 0)) * gizmo_size * ui_system_scale                                                # offset to the right to compensate for the initial horizontal label offset, and also to create a gap to the label

                        if idx:
                            co2d -= Vector((0, dims_row[1])) * gap * idx                                                      # offset down based on the text height (+ some gap) + the position in the stack

                        entry.co2d_gzm = co2d

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
