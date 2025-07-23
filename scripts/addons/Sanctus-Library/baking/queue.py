'''
Baking in the Sanctus-Library addon is based on connecting output sockets to the material output node and baking them as colors. This is different from other baking addons
that mainly bake out mesh maps like normals, ambient occlusion etc.
'''

from .. import auto_load as al
from ..auto_load.common import *
from . import utils

@al.register
class SocketPath(al.PropertyGroup):
    '''is a string path to a specific socket relative to a material. Use get_socket() to resolve the path to the referenced socket object. Because the path is stored a string. It's possible for this path to be invalidated'''

    socket_path = al.StringProperty()
    material = al.PointerProperty(type=bt.Material)

    def get_socket(self) -> bt.NodeSocket:
        return self.material().node_tree.path_resolve(self.socket_path())
    
    def is_valid_socket_path(self):
        try:
            self.get_socket()
            return True
        except ValueError:
            return False

    def get_socket_path_formatted(self):
        socket = self.get_socket()
        return f'{self.material().name} / {utils.get_node_display_name(socket.node)} / {socket.name}'


@al.depends_on(SocketPath)
@al.register
class BakeMap(al.PropertyGroup):
    '''Description of what the baker generates. The map type serves as a default name for a map. Using map types, it is also possible to generate a PBR node setup from the bake results.
`socket_paths` is a collection of `SocketPath` objects. Because bake maps "live" on a `bpy.types.Object`, usually users will have one socket path for each material on the object. 
Using multiple socket paths per bake map allows the result of multiple materials to be baked together.
    '''

    map_type = al.EnumProperty(enum=utils.MapType, default=utils.MapType.OTHER)
    other_name = al.StringProperty(name="Map Name", default="Other")
    other_is_colorspace = al.BoolProperty(name='Has Color?', description='Enable when map bakes color information. Disable for maps like metallic, normal, roughness etc.')
    socket_paths = al.CollectionProperty(type=SocketPath)
    is_hidden = al.BoolProperty(default=False, name='Disabled')
    samples = al.IntProperty(name='Samples', default=1, min=1, description='Render samples used for this map. Increase above 1 if the baking result is too noisy')

    def add_socket_path(self, socket: bt.NodeSocket):
        material = utils.material_from_socket(socket)
        if not self.is_material_available(material):
            raise ValueError(f'Material {material.name} is already used in map "{self.get_map_name()}"')
        
        sp = self.socket_paths.new()
        sp.socket_path.value = socket.path_from_id()
        sp.material.value = material

    def is_valid(self):
        return (
            not self.is_hidden()
            and all(x.is_valid_socket_path() for x in self.socket_paths())
        )

    def get_map_name(self):
        if self.map_type() in utils.MapType.explicit():
            return self.map_type().get_name().replace(' ', '')
        return self.other_name()
    
    def get_map_colorspace(self):
        if self.map_type() in utils.MapType.explicit():
            return self.map_type().get_colorspace()
        return utils.ColorSpace.SRGB if self.other_is_colorspace() else utils.ColorSpace.NON_COLOR
    
    def is_material_available(self, material: bt.Material):
        return not any(x.material() == material and x.is_valid_socket_path() for x in self.socket_paths())
    
    def get_socket_for_material(self, material: bt.Material):
        try:
            return next(sp.get_socket() for sp in self.socket_paths() if sp.material() == material)
        except StopIteration:
            return None

@al.register
class BakingQueueSettings(al.PropertyGroup):
    '''contains all of the "general" settings for baking'''

    show_expanded = al.BoolProperty(default=True)

    resolution_preset = al.EnumProperty(enum=utils.ResolutionPreset, default=utils.ResolutionPreset._512, name='Resolution')
    custom_resolution = al.IntVectorProperty(min=16, size=2, default=(256, 256), name='Custom')

    use_auto_margin = al.BoolProperty(name='Auto Margin', default=True, description='Set the baking margin based on the resolution of the texture')
    margin = al.IntProperty(name='Margin', min=1, default=8, description='Padding added to the edges of UV islands on the bake')

    use_auto_bake_settings = al.BoolProperty(name="Auto Decal Settings", default=True, description='Automatically determine settings for decal baking. Works best on objets with applied scale and 0 decal offset')
    ray_distance = al.FloatProperty(name="Ray Distance", default = 0.02, precision=4, description="Length of the distance check to hit the target surface from a decal. Set to a value slighly larger than the maximum distance a decal is away from the surface. Scales with object scale")

    bake_decals = al.BoolProperty(name='Bake Decals', default=True, description="Include decals on this object in the bake. Roughly doubles the processing time")

    override_sets = al.BoolProperty(name='Override Texture Sets', default=True, description='Override existing texture sets and images. New sets and images are created when disabled')

    def get_resolution(self) -> tuple[int, int]:
        if self.resolution_preset() == utils.ResolutionPreset.CUSTOM:
            return self.custom_resolution()
        res = int(self.resolution_preset().get_name())
        return (res, res)

@al.depends_on(BakeMap, BakingQueueSettings)
@al.register_property_group(bt.Object)
class BakingQueue(al.PropertyGroup):
    '''contains bake settings and a list of bake maps'''

    settings = al.PointerProperty(type=BakingQueueSettings)
    bake_maps = al.CollectionProperty(type=BakeMap)

    def add_map(self, type: utils.MapType, socket: Optional[bt.NodeSocket], other_name: str = ""):
        if not self.is_map_available(type):
            print("Map type already used in queue")
            return
        bake_map = self.bake_maps.new()
        bake_map.map_type.value = type
        if other_name != '':
            bake_map.other_name.value = other_name
        if socket is not None:
            bake_map.add_socket_path(socket)
        return bake_map

    def get_valid_maps(self):
        return [x for x in self.bake_maps() if x.is_valid()]

    def has_valid_maps(self):
        return len(self.get_valid_maps()) > 0
    
    def has_map_overlap(self):
        map_type_list: list[str] = []
        for m in self.bake_maps():
            map_type_list.append(m.get_map_name())
        return len(map_type_list) != len(set(map_type_list))
    
    def is_valid(self):
        return self.has_valid_maps() and (not self.has_map_overlap())
    
    def is_map_available(self, type: utils.MapType):
        if type in utils.MapType.explicit():
            return not any(x.map_type() == type for x in self.bake_maps())
        return True
