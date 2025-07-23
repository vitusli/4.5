from mathutils import Vector, Matrix, Euler, Quaternion
from bpy_extras import view3d_utils
from gpu_extras import batch
import dataclasses
import numpy as np
import math
import gpu
import bpy
import gpu_extras
import typing
import bpy.types as bt

UV = tuple[float, float]
Position = tuple[float, float, float]
Color = tuple[float, float, float, float]


class ColorPreset:

    WHITE = (1, 1, 1, 1)
    BLACK = (0, 0, 0, 1)
    TRANSPARENT = (0, 0, 0, 0)
    GRAY = (0.6, 0.6, 0.6, 1)
    RED = (1, 0, 0, 1)
    GREEN = (0, 1, 0, 1)
    BLUE = (0, 0, 1, 1)
    YELLOW = (1, 1, 0, 1)
    MAGENTA = (1, 0, 1, 1)
    CYAN = (0, 1, 1, 1)
    ORANGE = (1, 0.3, 0, 1)
    PURPLE = (0.1, 0.02, 0.8, 1)
    BROWN = (0.3, 0.1, 0.02, 1)

@dataclasses.dataclass(frozen=True)
class RayHit:
    is_hit: bool
    location: Vector
    normal: Vector
    polygon_index: int
    obj: bt.Object
    obj_matrix: Matrix

FAILED_RAYHIT = RayHit(False, (0, 0, 0), (0, 0, 1), -1, None, None)

def center_mouse_in_window(context: bt.Context):
    try:
        region: bt.Region = next(x for x in context.area.regions if x.type == 'WINDOW')
    except StopIteration:
        return False
    x = int(region.x + region.width * 0.5)
    y = int(region.y + region.height * 0.5)
    context.window.cursor_warp(x, y)
    return True

def mouse_vector_from_event(event: bt.Event):
    return (event.mouse_region_x, event.mouse_region_y)

def region_2d_to_ray3d(context: bt.Context, coord: tuple[int, int]):
    region = context.region
    rd3d = context.region_data
    ray_vector = view3d_utils.region_2d_to_vector_3d(region, rd3d, coord).normalized()
    ray_origin = view3d_utils.region_2d_to_origin_3d(region, rd3d, coord)
    return ray_origin, ray_vector

def raycast_scene(scene: bt.Scene, dg: bt.Depsgraph, ray_origin: Vector = None, ray_vector: Vector = None):
    is_hit, location, normal, polygon_index, obj, obj_matrix = scene.ray_cast(dg, ray_origin, ray_vector)
    return RayHit(is_hit, location, normal, polygon_index, obj, obj_matrix)

def raycast_scene_view(context: bt.Context, dg: bt.Depsgraph, coord: tuple[int, int]):
    origin, vector = region_2d_to_ray3d(context, coord)
    return raycast_scene(context.scene, dg, origin, vector)

def lookat_matrix(normal: Vector, up: typing.Union[Vector, None] = None):
    if up is None:
        up = Vector((0,0,1))
    if normal.dot(up) in (1, -1):
        up = Vector((0, 1, 0))
    
    mx = Vector.cross(up, normal).normalized()
    my = Vector.cross(normal, mx).normalized()
    return np.array([mx[0], my[0], normal[0], mx[1], my[1], normal[1], mx[2], my[2], normal[2]]).reshape([3,3], order='C')

def trs_matrix(location: Vector, normal: Vector, up: Vector = None, scale: Vector = None):
    mat = Matrix(lookat_matrix(normal, up))
    return Matrix.LocRotScale(location, mat.to_quaternion(), scale)

def rotation2d(angle_rad: float) -> np.ndarray:
    return np.array([
        [np.cos(angle_rad), -np.sin(angle_rad)],
        [np.sin(angle_rad), np.cos(angle_rad)]
    ])

def set_location_and_direction(obj: bt.Object, location: Vector, normal: Vector):
    scale = obj.scale
    mat = Matrix(lookat_matrix(normal)).to_4x4()
    mat.translation = location
    obj.matrix_world = mat
    obj.scale = scale

def loc3D_to_2D(loc: Vector, context: bt.Context):
    return view3d_utils.location_3d_to_region_2d(context.region, context.region_data, loc)

def dpifac():
    prefs = bpy.context.preferences.system
    return prefs.dpi * prefs.pixel_size / 72

VertexColorProgram = typing.Callable[[UV, int, Position], Color]

class GeoBuffer:

    vertices: np.ndarray
    indices: np.ndarray
    colors: np.ndarray
    uvs: np.ndarray

    UVS_AS_COLOR = lambda uv, i, pos: (uv[0], uv[1], 0, 1)

    def __init__(self, vertices: np.ndarray, indices: np.ndarray, colors: np.ndarray, uvs: np.ndarray = None):
        
        
        self.vertices = vertices
        self.indices = indices
        self.colors = colors

        count = self.index_offset

        if uvs is None:
            uvs = np.tile((0.0,0.0), count).reshape([count, 2])
        
        self.uvs = uvs

    @property
    def index_offset(self):
        return self.vertices.shape[0]
    
    def add(self, gdata: 'GeoBuffer'):
        offset = self.index_offset
        self.vertices = np.concatenate((self.vertices, gdata.vertices))
        self.indices = np.concatenate((self.indices, gdata.indices + offset))
        self.colors = np.concatenate((self.colors, gdata.colors))
        self.uvs = np.concatenate((self.uvs, gdata.uvs))
    
    def unpacked(self):
        return self.vertices.tolist() , self.indices.tolist(), self.colors.tolist()
    
    def copy(self):
        return GeoBuffer(self.vertices.copy(), self.indices.copy(), self.colors.copy())
    
    def __add__(self, other: 'GeoBuffer'):
        data = self.copy()
        data.add(other)
        return data
    
    def __iadd__(self, other: 'GeoBuffer'):
        self.add(other)
        return self
    
    @classmethod
    def empty(cls, vector_size: int):
        return cls(
            vertices=np.zeros([0, vector_size], dtype=np.float32), 
            indices=np.zeros([0, 3], dtype=np.int32), 
            colors=np.zeros([0, 4], dtype=np.float32),
            uvs=None
        )
    
    def set_colors(self, program: VertexColorProgram):
        for i in range(self.index_offset):
            self.colors[i] = program(self.uvs[i], i, self.vertices[i])

class BoundingBox:

    def __init__(self, points: np.ndarray):
        d = points.shape[1]
        minimum = np.zeros([d])
        maximum = np.zeros([d])
        for i in range(d):
            minimum[i] = np.min(points[:, i])
            maximum[i] = np.max(points[:, i])
        self.min = minimum
        self.max = maximum

    @property
    def span(self):
        return self.max - self.min
    
    @property
    def aspect2d(self) -> UV:
        s = self.span
        return (s[0] / s[1], 1)

    @property
    def aspect3d(self) -> Position:
        s = self.span
        return (s[0] / s[2], s[1] / s[2], 1)

    def remap(self, points: np.ndarray):
        return (points - self.min) / self.span

def repeat_color(color: Color, repeats: int):
    return np.tile(color, repeats).reshape((repeats, 4))

def lerp(a, b, t):
    return (1-t) * a + t * b

def use_aa():
    import bgl
    bgl.glHint(bgl.GL_POLYGON_SMOOTH_HINT, bgl.GL_NICEST)
    bgl.glEnable(bgl.GL_BLEND)
    bgl.glEnable(bgl.GL_POLYGON_SMOOTH)

class Shape2D:

    @staticmethod
    def square(loc: Vector, size: float, angle: float = 0, color: Color = ColorPreset.WHITE):
        verts = np.array([
            (-.5, -.5),
            (.5, -.5),
            (.5, .5),
            (-.5, .5)
        ])
        uvs = verts + 0.5
        verts *= size
        verts = (rotation2d(angle) @ verts.T).T
        verts += tuple(loc)

        return GeoBuffer(verts, np.array([(0, 1, 2), (0, 2, 3)]), repeat_color(color, 4), uvs=uvs)

    @staticmethod
    def quad(vertices: list[Vector], color: Color = ColorPreset.WHITE):
        uvs = np.array([
            (0,0),
            (1,0),
            (1,1),
            (0,1)
        ], dtype=np.float32)

        return GeoBuffer(np.array(vertices), np.array([(0, 1, 2), (0, 2, 3)]), repeat_color(color, 4), uvs=uvs)

    @staticmethod
    def rect(loc: Vector, size: Vector, angle: float = 0, pivot: Vector = Vector((0.5, 0.5)), color: Color = ColorPreset.WHITE):
        verts = np.array([
            (0.0, 0.0),
            (1.0, 0.0),
            (1.0, 1.0),
            (0.0, 1.0)
        ])
        uvs = verts.copy()
        verts -= tuple(pivot)
        verts *= size
        verts = (rotation2d(angle) @ verts.T).T
        verts += tuple(loc)
        return GeoBuffer(verts, np.array([(0, 1, 2), (0, 2, 3)]), repeat_color(color, 4), uvs=uvs)

    @staticmethod
    def convex_polygon(verts: np.ndarray, color: Color = ColorPreset.WHITE):
        
        vcount = verts.shape[0]
        bbox = BoundingBox(verts)
        uvs = bbox.remap(verts)

        fcount = vcount - 2
        ind0 = np.repeat(0, fcount)
        ind1 = np.arange(fcount) + 1
        ind2 = ind1 + 1
        indices = np.column_stack((ind0, ind1, ind2))
        return GeoBuffer(verts, indices, repeat_color(color, vcount), uvs=uvs)

    @staticmethod
    def circle(loc: Vector, radius: float, segments: int = 3, color: Color = ColorPreset.WHITE):
        segments = max(segments, 3)
        r = np.arange(segments)
        radians = r * ((2 * math.pi)/segments)
        verts = np.column_stack((np.cos(radians), np.sin(radians)))
        verts = np.row_stack([verts, (0.0, 0.0)])
        uvs = verts.copy()
        verts: np.ndarray = (verts * radius) + loc

        ind0 = np.repeat(segments, segments)
        ind1 = r
        ind2 = np.mod(r + 1, segments)

        indices = np.column_stack((ind0, ind1, ind2))

        vertex_colors = np.tile(color, len(verts)).reshape((len(verts), 4))
        return GeoBuffer(verts, indices, vertex_colors, uvs=uvs)

    @staticmethod
    def rect_line(start: Vector, end: Vector, width: float, color: Color = ColorPreset.WHITE):

        vec = end - start
        vec_normalized = vec.normalized()
        tangent = Vector((-vec_normalized.y, vec_normalized.x))
        offset = tangent * (width*0.5)
        
        verts: np.ndarray = np.array([
            tuple(start - offset),
            tuple(start + offset),
            tuple(end + offset),
            tuple(end - offset)
        ])
        uvs = np.array([
            (0,0),
            (1,0),
            (1,1),
            (0,1)
        ], dtype=np.float32)
        indices = np.array([(0,1,2), (2, 3, 0)])
        vertex_colors = np.tile(color, 4).reshape([4, 4])
        return GeoBuffer(verts, indices, vertex_colors, uvs=uvs)

    @staticmethod
    def polygon_line(points: list[Vector], width: float, color: Color = ColorPreset.WHITE):
        
        data = GeoBuffer.empty(2)
        for i, point in enumerate(points):
            next = points[(i + 1) % len(points)]
            data.add(Shape2D.rect_line(point, next, width, color=color))
        return data
    
    @staticmethod
    def polygon_wire(points: list[Vector], line_width: float = 3, circle_radius: float = 3, circle_segments = 6, color: Color = ColorPreset.WHITE):
        data = Shape2D.polygon_line(points, line_width, color)
        for p in points:
            data += Shape2D.circle(p, circle_radius, circle_segments, color)
        return data
    
    @staticmethod
    def wireframe(data: GeoBuffer, line_width: float):
        verts = data.vertices
        cols = data.colors
        result = GeoBuffer.empty(2)
        edges: set[tuple[int, int]] = set()
        for tri in data.indices:
            edges.add((tri[0], tri[1]))
            edges.add((tri[1], tri[2]))
            edges.add((tri[2], tri[0]))
        for e in edges:
            i0, i1 = e
            result += Shape2D.rect_line(Vector(verts[i0]), Vector(verts[i1]), line_width, (cols[i0] + cols[i1]) * 0.5)
        return result

class Shape3D:

    @staticmethod
    def cube(loc: Vector, size: float, color: Color=ColorPreset.WHITE):
        s = size * dpifac()
        matrix = np.array((
            (-1, -1, -1), (+1, -1, -1),
            (-1, +1, -1), (+1, +1, -1),
            (-1, -1, +1), (+1, -1, +1),
            (-1, +1, +1), (+1, +1, +1)))
        coords = matrix * s + np.array(loc)

        indices = np.array((
            (0, 1, 2), (2, 1, 3),
            (0, 1, 5), (5, 0, 4),
            (0, 4, 2), (2, 4, 6),
            (2, 3, 7), (7, 2, 6),
            (3, 1, 5), (5, 3, 7),
            (4, 5, 7), (7, 4, 6)))

        vertex_colors = np.tile(color, len(coords)).reshape((len(coords), 4))
        return GeoBuffer(coords, indices, vertex_colors)

def render_uniform(gdata: GeoBuffer, color: Color = ColorPreset.WHITE, shader_type: str = 'UNIFORM_COLOR'):

    shader: gpu.types.GPUShader = gpu.shader.from_builtin(shader_type)
    batch: gpu.types.GPUBatch = gpu_extras.batch.batch_for_shader(shader, 'TRIS', {'pos': gdata.vertices.tolist()}, indices=gdata.indices.tolist())
    shader.uniform_float('color', color)
    batch.draw(shader)

def render_vcol(gdata: GeoBuffer, color_type: str = 'SMOOTH_COLOR'):

    shader: gpu.types.GPUShader = gpu.shader.from_builtin(color_type)
    batch: gpu.types.GPUBatch = gpu_extras.batch.batch_for_shader(shader, 'TRIS', {'pos': gdata.vertices.tolist(), 'color': gdata.colors.tolist()}, indices=gdata.indices.tolist())
    batch.draw(shader)

def to_texture(image: bt.Image):
    return gpu.texture.from_image(image)

def render_image(gdata: GeoBuffer, texture: gpu.types.GPUTexture, color: Color = ColorPreset.WHITE):

    shader: gpu.types.GPUShader = gpu.shader.from_builtin('IMAGE_COLOR')
    vertex_data = dict(
        pos=gdata.vertices.tolist(),
        texCoord=gdata.uvs.tolist()
    )
    batch: gpu.types.GPUBatch = gpu_extras.batch.batch_for_shader(shader, 'TRIS', vertex_data, indices=gdata.indices.tolist())
    shader.uniform_sampler('image', texture)
    shader.uniform_float('color', color)
    batch.draw(shader)
