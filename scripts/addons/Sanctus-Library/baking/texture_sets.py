'''
This module contains the PropertyGroups for bake results
'''

from .. import auto_load as al
from ..auto_load.common import *
from . import utils

@al.register
class BakeTexture(al.PropertyGroup):
    '''A wrapper for a `bpy.types.Image` pointer. Each bake texture also has a map type. This matches the map type of the baking queue'''

    texture = al.PointerProperty(type=bt.Image)
    map_id = al.StringProperty()
    map_type = al.EnumProperty(enum=utils.MapType)

    def is_valid(self):
        return self.texture() is not None

@al.depends_on(BakeTexture)
@al.register
class TextureSet(al.PropertyGroup):
    '''a collection of bake textures. Each baking process creates a new `TextureSet` unless existing textures are overridden'''
    textures = al.CollectionProperty(type=BakeTexture)
    set_name = al.StringProperty()
    timecode = al.DateProperty()
    show_expanded = al.BoolProperty(default=True)

    def add_texture(self, map_type: utils.MapType, name: str, image: bt.Image):
        from .. import img_tools

        bake_texture = next((x for x in self.textures() if x.map_id() == name), None)
        if bake_texture is None:
            bake_texture = self.textures.new()
            bake_texture.texture.value = image
            bake_texture.map_id.value = name
            image.name = name
        else:
            img_tools.replace_image(bake_texture.texture(), image)

        bake_texture.map_type.value = map_type

    def get_valid_textures(self):
        return [x for x in self.textures() if x.texture() is not None]
    
    def has_vaid_bake_textures(self):
        return len(self.get_valid_textures()) > 0


@al.depends_on(TextureSet)
@al.register_property_group(bt.Scene)
class TextureSetManager(al.PropertyGroup):
    '''contains all baked texture sets. Instead of being stored for each object, all texture sets are stored globally so they are accessibly from every object'''

    texture_sets = al.CollectionProperty(type=TextureSet)
    sorting = al.EnumProperty(enum=utils.Sorting, default=utils.Sorting.DATE)
    reverse_sorting = al.BoolProperty(default=False, name='Reverse Sorting', description='Reverse the sorting of displayed texture sets')
    show_only_local_sets = al.BoolProperty(default=True, name="Show Only Local Sets", description="When enabled, show only sets with the same name as the active object")

    def add_set(self, obj: bt.Object, image_map: list[tuple[utils.MapType, str, bt.Image]], override_sets: bool):
        set_name = obj.name
        if self.set_exists(set_name) and override_sets:
            texture_set = self.get_set(set_name)
        else:
            texture_set = self.texture_sets.new()
            texture_set.set_name.value = set_name

        texture_set.timecode.set_to_now()

        for map_type, map_name, image in image_map:
            texture_set.add_texture(map_type, map_name, image)

    def get_set(self, name: str):
        return next(x for x in self.texture_sets() if x.set_name() == name)

    def set_exists(self, set_name: str):
        return any(x.set_name() == set_name for x in self.texture_sets())
