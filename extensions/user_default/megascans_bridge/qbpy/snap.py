# https://blender.stackexchange.com/a/288739?noredirect=1

from math import ceil, cos, floor, log10, pi, sin

from bpy_extras.view3d_utils import (
    location_3d_to_region_2d,
    region_2d_to_location_3d,
    region_2d_to_origin_3d,
    region_2d_to_vector_3d,
)
from mathutils import Vector
from mathutils.geometry import intersect_line_plane

from . import ui_scale
from .draw import Draw2D
from .draw.circle_2d import circle_2d


class Snap(Draw2D):
    def __init__(self):
        self.radius = 20
        self.steps = 12
        self.hit_grid = False
        self.snap_location = None
        self.snap_object = None
        self.snap_type = None
        self.vertex_index = -1
        self.face_index = None
        self.best_distance = None
        self.view_point = None
        self.event = None
        self.region = None
        self.rv3d = None
        self.mouse_pos = None

    def draw_callback_px(self, context):
        # Early exit if conditions aren't met
        if not (self.event and self.event.ctrl and self.snap_type and self.snap_location):
            return

        size = 8 * ui_scale() if ui_scale() >= 1.777 else 8

        circle_loc = location_3d_to_region_2d(self.region, self.rv3d, self.snap_location)
        if circle_loc is None:
            return

        x, y = circle_loc

        if self.snap_type == "face":
            circle_2d(circle_loc, radius=self.radius, color=(1, 1, 1, 0), outline_color=(1, 1, 1, 1))
        elif self.snap_type == "edge":
            coords = ((x - size, y - size), (x + size, y - size), (x + size, y + size), (x - size, y + size))
            indices = ((0, 1), (1, 3), (3, 2), (2, 0))
            self.draw_2d_line(coords, indices)
        elif self.snap_type == "edge_center":
            coords = ((x - size, y - size), (x + size, y - size), (x, y + size))
            indices = ((0, 1), (1, 2), (2, 0))
            self.draw_2d_line(coords, indices)
        elif self.snap_type == "vertex":
            coords = ((x - size, y - size), (x + size, y - size), (x + size, y + size), (x - size, y + size))
            indices = ((0, 1), (1, 2), (2, 3), (3, 0))
            self.draw_2d_line(coords, indices)

    def ray_cast(self, context, depsgraph, position):
        origin = region_2d_to_origin_3d(self.region, self.rv3d, position)
        direction = region_2d_to_vector_3d(self.region, self.rv3d, position)
        return *context.scene.ray_cast(depsgraph, origin, direction), origin

    def best_hit(self, context, depsgraph, mouse_pos):
        # Try direct hit first
        result, location, normal, index, object, matrix, view_point = self.ray_cast(context, depsgraph, mouse_pos)
        if result:
            return result, location, index, object, view_point

        # No direct hit, try sampling around in a circle
        best_result = False
        best_index = index
        best_location = best_object = None
        best_distance = 0

        angle = 0
        delta_angle = 2 * pi / self.steps

        for _ in range(self.steps):
            pos = mouse_pos + self.radius * Vector((cos(angle), sin(angle)))
            result, location, normal, index, object, matrix, view_point = self.ray_cast(context, depsgraph, pos)

            if result and (best_object is None or (view_point - location).length < best_distance):
                best_distance = (view_point - location).length
                best_result = True
                best_location = location
                best_index = index
                best_object = object
            angle += delta_angle

        return best_result, best_location, best_index, best_object, best_distance

    def _search_edge_pos(self, mouse, v1, v2, epsilon=0.0001):
        while (v1 - v2).length > epsilon:
            v12D, v22D = map(lambda v: location_3d_to_region_2d(self.region, self.rv3d, v), (v1, v2))
            if v12D is None or v22D is None:
                return v1 if v22D is None else v2
            if (v12D - mouse).length < (v22D - mouse).length:
                v2 = (v1 + v2) / 2
            else:
                v1 = (v1 + v2) / 2
        return v1

    def _snap_to_geometry(self, context, data, vertices):
        snap_location = None
        snap_type = "face"
        vertex_index = -1
        best_distance = float("inf")

        # first snap to vertices
        # loop over vertices and keep the one which is closer once projected on screen
        for vert, co in vertices.items():
            co2D = location_3d_to_region_2d(self.region, self.rv3d, co)
            if co2D is not None:
                distance = (co2D - self.mouse_pos).length
                if distance < self.radius and distance < best_distance:
                    snap_location = co
                    snap_type = "vertex"
                    vertex_index = vert.index
                    best_distance = distance

        # then, if no vertex is found, try to snap to edges
        if snap_location is None:
            for co1, co2 in zip(list(vertices.values())[1:] + list(vertices.values())[:1], list(vertices.values())):
                center = (co1 + co2) / 2
                co = self._search_edge_pos(self.mouse_pos, co1, co2)
                v2D = location_3d_to_region_2d(self.region, self.rv3d, co)
                if v2D is not None:
                    distance = (v2D - self.mouse_pos).length
                    if distance < self.radius and distance < best_distance:
                        snap_location = co
                        snap_type = "edge_center" if co == center else "edge"
                        best_distance = distance

        if snap_location is not None:
            self.snap_location = snap_location
            self.snap_type = snap_type
            self.vertex_index = vertex_index

    def snap_to_object(self, context, depsgraph):
        evaluated = self.snap_object.evaluated_get(depsgraph)
        data = evaluated.data if self.snap_object.modifiers else self.snap_object.data
        polygon = data.polygons[self.face_index]
        matrix = evaluated.matrix_world

        vertices = {data.vertices[i]: matrix @ data.vertices[i].co for i in polygon.vertices}
        self._snap_to_geometry(context, data, vertices)

    def _snap_to_grid(self, context, vertices):
        snap_location = None
        best_distance = float("inf")

        # snap to grid vertices
        for co in vertices:
            co2D = location_3d_to_region_2d(self.region, self.rv3d, co)
            if co2D is not None:
                distance = (co2D - self.mouse_pos).length
                if distance < self.radius and distance < best_distance:
                    snap_location = co
                    best_distance = distance

        # snap to grid edges
        if snap_location is None:
            for co1, co2 in zip(vertices[1:] + vertices[:1], vertices):
                co = self._search_edge_pos(self.mouse_pos, co1, co2)
                v2D = location_3d_to_region_2d(self.region, self.rv3d, co)
                if v2D is not None:
                    distance = (v2D - self.mouse_pos).length
                    if distance < self.radius and distance < best_distance:
                        snap_location = co
                        best_distance = distance

        if snap_location is not None:
            self.snap_location = snap_location

    def snap_to_grid(self, context, ctrl):
        view_point = region_2d_to_origin_3d(self.region, self.rv3d, self.mouse_pos)
        view_vector = region_2d_to_vector_3d(self.region, self.rv3d, self.mouse_pos)
        norm = view_vector if self.rv3d.is_orthographic_side_view else Vector((0, 0, 1))

        # At which scale the grid is
        # (log10 is 1 for meters => 10 ** (1 - 1) = 1
        # (log10 is 0 for 10 centimeters => 10 ** (0 - 1) = 0.1
        scale = 10 ** (round(log10(self.rv3d.view_distance)) - 1)
        # ... to be improved with grid scale, subdivisions, etc.

        # here no ray cast, but intersection between the view line and the grid plane
        max_float = 1.0e38
        co = intersect_line_plane(view_point, view_point + max_float * view_vector, (0, 0, 0), norm)

        def floor_fit(co, scale):
            return floor(co / scale) * scale

        def ceil_fit(co, scale):
            return ceil(co / scale) * scale

        if co is not None:
            self.hit_grid = True
            if ctrl:
                # depending on the view angle, create the list of vertices for a plane around the hit point
                # which size is adapted to the view scale (view distance)
                if abs(norm.x) > 0:
                    vertices = [
                        Vector((0, floor_fit(co.y, scale), floor_fit(co.z, scale))),
                        Vector((0, floor_fit(co.y, scale), ceil_fit(co.z, scale))),
                        Vector((0, ceil_fit(co.y, scale), ceil_fit(co.z, scale))),
                        Vector((0, ceil_fit(co.y, scale), floor_fit(co.z, scale))),
                    ]
                elif abs(norm.y) > 0:
                    vertices = [
                        Vector((floor_fit(co.x, scale), 0, floor_fit(co.z, scale))),
                        Vector((floor_fit(co.x, scale), 0, ceil_fit(co.z, scale))),
                        Vector((ceil_fit(co.x, scale), 0, ceil_fit(co.z, scale))),
                        Vector((ceil_fit(co.x, scale), 0, floor_fit(co.z, scale))),
                    ]
                else:
                    vertices = [
                        Vector((floor_fit(co.x, scale), floor_fit(co.y, scale), 0)),
                        Vector((floor_fit(co.x, scale), ceil_fit(co.y, scale), 0)),
                        Vector((ceil_fit(co.x, scale), ceil_fit(co.y, scale), 0)),
                        Vector((ceil_fit(co.x, scale), floor_fit(co.y, scale), 0)),
                    ]
                # and snap on this plane
                self._snap_to_grid(context, vertices)

            # if no snap or out of snapping, keep the co
            if self.snap_location is None:
                # self.snap_location = Vector(co) # this was causing the grid issue
                self.snap_location = region_2d_to_location_3d(
                    self.region, self.rv3d, self.mouse_pos, depth_location=(0, 0, 0)
                )

    def snap(self, context, event) -> dict:
        # Setup context variables
        self.region = context.region
        self.rv3d = context.region_data
        self.mouse_pos = Vector((event.mouse_region_x, event.mouse_region_y))
        self.event = event

        depsgraph = context.evaluated_depsgraph_get()
        result, location, index, object, best_distance = self.best_hit(context, depsgraph, self.mouse_pos)

        # Initialize snap data
        self.snap_location = location
        self.snap_object = object
        self.snap_type = "face"
        self.vertex_index = -1
        self.face_index = index
        self.best_distance = best_distance

        if result and event.ctrl:
            self.snap_to_object(context, depsgraph)
        elif not result:
            self.snap_to_grid(context, event.ctrl)

        return {
            "location": Vector(self.snap_location) if self.snap_location else None,
            "object": self.snap_object,
            "type": self.snap_type,
            "vertex_index": self.vertex_index,
            "face_index": self.face_index,
        }
