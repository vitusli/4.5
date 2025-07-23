'''
General collection of utility function and classes around the baking process
'''

from .. import auto_load as al
from ..auto_load.common import *
from .. import override_handler
from .. import poll

INVALID_SOCKET_TYPES: list[bt.NodeSocket] = [
    bt.NodeSocketShader,
]

MAX_SOCKETS_IN_SELECTOR = 20 # socket selectors for baking use a bool vector property with a limited size


class ColorSpace(al.BStaticEnum):

    SRGB = dict(n="sRGB")
    NON_COLOR = dict(n="Non-Color")

class BakeSetupError(Exception):
    pass

class MapType(al.BStaticEnum):

    BASE_COLOR = dict(n="Base Color", a="diffuse diff albedo base col color basecolor", default=(0, 0, 0), cs=ColorSpace.SRGB)
    METALLIC = dict(n="Metallic", a="metallic metalness metal mtl", default=0.0, cs=ColorSpace.NON_COLOR)
    SPECULAR = dict(n="Specular", a="specular specularity spec spc", default=0.5, cs=ColorSpace.NON_COLOR)
    ROUGHNESS = dict(n="Roughness", a="roughness rough rgh", default=0.5, cs=ColorSpace.NON_COLOR)
    NORMAL = dict(n="Normal", a="normal norm nrml nor nrm", default=(0.5, 0.5, 1.0), cs=ColorSpace.NON_COLOR)
    DISPLACEMENT = dict(n="Displacement", a="displacement displace heightmap height disp dsp", default=0.5, cs=ColorSpace.NON_COLOR)
    EMISSION = dict(n="Emission", a="emission emissive emit", default=0.0, cs=ColorSpace.SRGB)
    ALPHA = dict(n="Alpha", a="alpha opacity", default=1.0, cs=ColorSpace.NON_COLOR)
    OTHER = dict(n="Other", a="", default=0.0, cs=ColorSpace.NON_COLOR)

    def get_default_match(self) -> str:
        return self.value['a']
    
    def get_default_value(self) -> Union[float, tuple[float, float, float]]:
        return self.value['default']
    
    def get_colorspace(self) -> ColorSpace:
        return self.value['cs']
    
    @classmethod
    def explicit(cls):
        return (x for x in cls if x != cls.OTHER)


class ResolutionPreset(al.BStaticEnum):

    _512 = dict(n='512', d='512 pixel resolution')
    _1024 = dict(n='1024', d='1024 pixel resolution')
    _2048 = dict(n='2048', d='2048 pixel resolution')
    _4096 = dict(n='4096', d='4096 pixel resolution')
    _8192 = dict(n='8192', d='8192 pixel resolution')
    CUSTOM = dict(n='Custom', d='Use a custom square pixel resolution')

class Sorting(al.BStaticEnum):

    DATE = dict(n='Date', d='Sort by date', i=al.BIcon.SORTTIME)
    NAME = dict(n='Name', d='Sort by name of the texture set', i=al.BIcon.SORTALPHA)


def get_shader_output_socket(node_tree: bt.ShaderNodeTree) -> OrNone[bt.NodeSocketStandard]:
    node = node_tree.get_output_node('CYCLES')
    if not node:
        return
    return node.inputs.get('Surface', None)

def get_socket_colorspace(socket: bt.NodeSocketStandard):
    if 'color' in socket.bl_idname.lower():
        return ColorSpace.SRGB
    else:
        return ColorSpace.NON_COLOR

def get_node_display_name(node: bt.ShaderNode):
    result = node.name
    if isinstance(node, bt.ShaderNodeGroup):
        result = node.node_tree.name
    if node.label != '':
        result = node.label
    return result

def bake(bake_args: dict[str, Any]):

    bpy.ops.object.bake(**{
        k: v
        for k, v
        in bake_args.items()
        if k in bpy.ops.object.bake.get_rna_type().properties.keys()
    })  # Check properties of the function. Ensures no errors will occur when using Blender 3.0

def get_decal_material_surface_socket(decal: bt.Object) -> tuple[bt.NodeSocket, bt.ShaderNodeTree]:
    nt: bt.ShaderNodeTree = decal.active_material.node_tree
    return nt.get_output_node('CYCLES').inputs['Surface'], nt

def match_name_to_map_type(name: str):
    name = name.lower()
    for x in MapType.explicit():
        fragments = x.get_default_match()
        if name in fragments:
            return x
    return MapType.OTHER

def set_decal_bake_link(decal: bt.Object, map_type: MapType):

    surface_input, nt = get_decal_material_surface_socket(decal)
    group_node: bt.ShaderNodeGroup = surface_input.links[0].from_node
    
    output_map = assign_decal_sockets_to_map_types(group_node.outputs)
    try:
        target = next(socket for mt, socket in output_map if mt == map_type)
    except StopIteration:
        raise BakeSetupError(f'Socket not found on decal matching map type "{map_type.name}" on object "{decal.name}".')
    nt.links.new(target, surface_input)
    return target

def reset_decal_bake_link(decal: bt.Object, socket_identifier: Optional[typing.Callable[[bt.Node], bt.NodeSocket]] = None):
    if socket_identifier is None:
        socket_identifier = lambda n: n.outputs[0]

    surface_input, nt = get_decal_material_surface_socket(decal)
    group_node: bt.ShaderNodeGroup = surface_input.links[0].from_node
    nt.links.new(socket_identifier(group_node), surface_input)

def finalize_bake_texture(image: bt.Image, colorspace: ColorSpace, skip_conversion: bool = False):
    from .. import img_tools, image_processing as ip
    image.pixels.update()
    image.update()
    if colorspace == ColorSpace.SRGB and not skip_conversion:
        img_tools.convert_linear_to_srgb(image)
        image.update()
    image.pack()
    image.colorspace_settings.name = colorspace.get_name()
    image.preview_ensure()
    image.preview.reload()

def save_texture_data(image: bt.Image):
    image.update()
    image.pack()
    image.preview_ensure()
    image.preview.reload()


def create_new_image(name: str, resolution: tuple[int, int], override: bool):

    old_img: bt.Image = bpy.data.images.get(name, None)
    needs_remap = override and old_img is not None

    image = bpy.data.images.new(name=name, width=resolution[0], height=resolution[1], alpha=True, float_buffer=True)

    if needs_remap:
        old_img.user_remap(image)
        bpy.data.images.remove(old_img)
        image.name = name
    return image

def decal_bake_context(context: bt.Context, bake_obj: bt.Object, decals: list[bt.Object]):
    return context.temp_override(selected_objects=decals + [bake_obj], active_object=bake_obj)

def selected_objs_context(context: bt.Context, objs: typing.Iterable[bt.Object]):
    return context.temp_override(
        active_object=objs[0], 
        object=objs[0], 
        selected_objects=objs, 
        selected_editable_objects=objs
    )

def filter_baking_socket(socket: bt.NodeSocket):
    if not socket.enabled:
        return False
    if socket.hide:
        return False
    if type(socket) in INVALID_SOCKET_TYPES:
        return False
    if(socket.name == "Displacement" and isinstance(socket.node, bt.ShaderNodeGroup) and socket.type == 'VECTOR'): # UNEXPECTED BEHAVIOR
        return False
    return True

def get_socket_display_name(socket: bt.NodeSocket):
    if socket.label != '':
        return socket.label
    return socket.name

def assign_sockets_to_map_types(sockets: typing.Iterable[bt.NodeSocket], name_match: Optional[typing.Callable[[str,], str]] = None, filter_sockets: bool = True):
    
    if name_match is None:
        def default_name_match(n: str):
            return n.split(" ")[0]
        name_match = default_name_match

    result: list[tuple[MapType, bt.NodeSocket]] = []
    
    map_type_pool = [x for x in MapType.explicit()]
    if filter_sockets:
        sockets = [x for x in sockets if filter_baking_socket(x)]
    for x in sockets:
        map_type = match_name_to_map_type(name_match(x.name))
        if map_type in map_type_pool:
            map_type_pool.remove(map_type)
            result.append((map_type, x))
        elif map_type == MapType.OTHER:
            result.append((map_type, x))
    
    result.sort(key=lambda x: x[0].get_index())
    
    return result

def assign_decal_sockets_to_map_types(sockets: typing.Iterable[bt.NodeSocket]):

    result: list[tuple[MapType, bt.NodeSocket]] = []

    for socket in sockets:
        try:
            map_type = next(x for x in MapType.explicit() if x.name == socket.name)
            result.append((map_type, socket))
        except StopIteration:
            continue

    return result

def is_shader_context(context: al.BContext[bt.SpaceNodeEditor]):
    return (
        context.area.type == 'NODE_EDITOR'
        and context.space_data.edit_tree.bl_idname == 'ShaderNodeTree'
    )

def assert_shader_context():
    return al.OperatorAssert(lambda c: is_shader_context(c), 'Current context is not in a shader nodetree.', strict=False)

def assert_bake_socket_context(context: bt.Context):
    yield al.OperatorAssert(lambda c: is_shader_context(c), 'Current context is not in a shader nodetree.', strict=False)
    yield al.OperatorAssert(lambda c: context.object is not None, 'No active object selected.')
    materials = [x.material for x in context.object.material_slots if x.material is not None]
    space: bt.SpaceNodeEditor = context.space_data
    node_tree = space.edit_tree
    yield al.OperatorAssert(lambda c: node_tree in [x.node_tree for x in materials], 'The material to bake is not in the active object.')
    active_node = node_tree.nodes.active
    yield al.OperatorAssert(lambda c: active_node is not None and active_node.select == True, 'No active node selected.')
    yield al.OperatorAssert(lambda c: len([o for o in active_node.outputs if filter_baking_socket(o)]) > 0, 'Active node does not have bakeable outputs. (Shader outputs are not supported)')

def assert_baking_context(context: bt.Context) -> Generator[al.OperatorAssert, None, None]:
    yield al.OperatorAssert(lambda c: c.scene.render.engine == 'CYCLES', 'Render engine is not Cycles.')
    yield al.OperatorAssert(lambda c: c.object, 'No active object selected.', strict=False)
    yield al.OperatorAssert(poll.is_object_type(types='MESH'), 'Active object is not of type “MESH”.')
    yield al.OperatorAssert(lambda c: c.object in c.selected_objects, 'No active object selected.')
    yield al.OperatorAssert(lambda c: len(c.selected_objects) <= 1, "More than one object is selected.")
    yield al.OperatorAssert(lambda c: c.object.data.uv_layers.active is not None, 'No available UVs found.')

    depsgraph = context.evaluated_depsgraph_get()
    yield al.OperatorAssert(lambda c: c.object.evaluated_get(depsgraph).data.uv_layers.active is not None, 'Active object has no UVs due to modifiers.')

def get_texture_bake_args(oh: override_handler.OverrideHandler, bake: bt.BakeSettings, margin: int = 1):
    bake_args = dict(
        type=al.BBakePassType.DIFFUSE(),
        use_selected_to_active=False,
        use_cage=False,
        use_clear=True,
        target=al.BBakeTarget.IMAGE_TEXTURES(),
        save_mode=al.BBakeSaveMode.INTERNAL(),
        margin=margin,
        margin_type=al.BBakeMarginType.EXTEND(),
    )

    oh.override(bake, 'use_pass_color', True)
    oh.override(bake, 'use_pass_direct', False)
    oh.override(bake, 'use_pass_indirect', False)

    return bake_args

def set_bake_args_auto_margin(bake_args: dict[str, Any], resolution: tuple[int, int]):
    average_resolution = int((resolution[0] + resolution[1]) / 2)
    bake_args['margin'] = int(average_resolution / 32)
    return bake_args


def get_decal_bake_args(oh: override_handler.OverrideHandler, bake: bt.BakeSettings, max_ray_distance: float = 0.01, cage_extrusion = 0.003):
    bake_args = get_texture_bake_args(oh, bake, 1)
    bake_args['use_selected_to_active'] = True
    bake_args['max_ray_distance'] = max_ray_distance
    bake_args['cage_extrusion'] = cage_extrusion
    bake_args['margin_type'] = al.BBakeMarginType.EXTEND()
    return bake_args

def material_from_socket(socket: bt.NodeSocket) -> bt.Material:
    return next(x for x in bpy.data.materials if x.node_tree == socket.id_data)

def map_type_to_pbr_socket_name(t: MapType):
    return {
        MapType.BASE_COLOR: 'Base Color',
        MapType.METALLIC: 'Metallic',
        MapType.SPECULAR: 'Specular',
        MapType.ROUGHNESS: 'Roughness',
        MapType.NORMAL: 'Normal',
        MapType.DISPLACEMENT: '',
        MapType.EMISSION: 'Emissive Color',
        MapType.ALPHA: 'Alpha'
    }[t]
