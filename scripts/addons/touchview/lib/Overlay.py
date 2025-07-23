import math

import bpy
import gpu
from bpy.types import Region, SpaceView3D
from gpu_extras.batch import batch_for_shader
from mathutils import Vector

from .utils import get_settings


class Overlay:
    def __init__(self):
        self.meshes = []

    def clear_overlays(self):
        for mesh in self.meshes:
            SpaceView3D.draw_handler_remove(mesh, "WINDOW")
        self.meshes = []

    def __getMidpoint(self, view: Region) -> Vector:
        return self.__getSize(view, 0.5)

    def __getSize(self, view: Region, scalar: float = 1) -> Vector:
        return Vector((view.width * scalar, view.height * scalar))

    def __getColors(self, type: str):
        settings = get_settings()
        if not settings.is_enabled and not settings.lazy_mode:
            return (0.0, 0.0, 0.0, 0.0)
        if type == "main" or not settings.use_multiple_colors:
            return settings.overlay_main_color
        elif type == "secondary":
            return settings.overlay_secondary_color
        else:
            return (0.0, 0.0, 0.0, 0.0)

    def drawUI(self):
        _handle = SpaceView3D.draw_handler_add(
            self.__renderCircle,
            (),
            "WINDOW",
            "POST_PIXEL",
        )
        self.meshes.append(_handle)
        _handle = SpaceView3D.draw_handler_add(
            self.__renderRailing, (), "WINDOW", "POST_PIXEL"
        )
        self.meshes.append(_handle)

    def __renderRailing(self):
        settings = get_settings()
        view = bpy.context.area
        if not settings.isVisible:
            return
        for region in view.regions:
            if bpy.context.region.as_pointer() == region.as_pointer():
                self.__makeBox(region, self.__getColors("main"))

    def __makeBox(self, view: Region, color: tuple[float, float, float, float]):
        settings = get_settings()
        mid = self.__getMidpoint(view)
        dimensions = self.__getSize(view)
        left_rail = (
            Vector((0.0, 0.0)),
            Vector((mid.x * settings.getWidth(), dimensions.y)),
        )
        right_rail = (
            Vector((dimensions.x, 0.0)),
            Vector((dimensions.x - mid.x * settings.getWidth(), dimensions.y)),
        )

        self.__drawVectorBox(left_rail[0], left_rail[1], color)
        self.__drawVectorBox(right_rail[0], right_rail[1], color)

    def __drawVectorBox(self, a, b, color):
        vertices = ((a.x, a.y), (b.x, a.y), (a.x, b.y), (b.x, b.y))
        indices = ((0, 1, 2), (2, 3, 1))

        self.__drawGeometry(vertices, indices, color, "TRIS")

    def __renderCircle(self):
        settings = get_settings()
        view = bpy.context.area
        if not settings.isVisible:
            return
        for region in view.regions:
            if (
                bpy.context.region.as_pointer() == region.as_pointer()
                and not region.data.lock_rotation
            ):
                self.__makeCircle(region, self.__getColors("secondary"))

    def __makeCircle(self, view: Region, color: tuple[float, float, float, float]):
        settings = get_settings()
        mid = self.__getMidpoint(view)
        radius = math.dist((0, 0), mid) * (settings.getRadius() * 0.5)  # type: ignore
        self.__drawCircle(mid, radius, color)

    def __drawCircle(self, mid: Vector, radius: float, color: tuple):
        segments = 100
        vertices = [mid]
        indices = []
        p = 0
        for p in range(segments):
            if p > 0:
                point = Vector((
                    mid.x + radius * math.cos(math.radians(360 / segments) * p),
                    mid.y + radius * math.sin(math.radians(360 / segments) * p),
                ))
                vertices.append(point)
                indices.append((0, p - 1, p))
        indices.append((0, 1, p))

        self.__drawGeometry(vertices, indices, color, "TRIS")

    def __drawGeometry(self, vertices, indices, color, type):
        shader = gpu.shader.from_builtin("UNIFORM_COLOR")
        batch = batch_for_shader(shader, type, {"pos": vertices}, indices=indices)
        shader.bind()
        gpu.state.blend_set("ALPHA")
        shader.uniform_float("color", color)
        batch.draw(shader)
