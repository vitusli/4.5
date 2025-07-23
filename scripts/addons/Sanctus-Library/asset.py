'''
This module contains functionality about importing assets from the source files. It only interfaces with library and library_manager objects
'''

from . import auto_load as al
from .auto_load.common import *

from . import library

import dataclasses


class Type(enum.Enum):
    ACTIONS = 'actions'
    ARMATURES = 'armatures'
    BRUSHES = 'brushes'
    CAMERAS = 'cameras'
    COLLECTIONS = 'collections'
    CURVES = 'curves'
    FONTS = 'fonts'
    GREASE_PENCILS = 'grease_pencils'
    HAIR_CURVES = 'hair_curves'
    IMAGES = 'images'
    LATTICES = 'lattices'
    LIGHTPROBES = 'lightprobes'
    LIGHTS = 'lights'
    LINESTYLES = 'linestyles'
    MASKS = 'masks'
    MATERIALS = 'materials'
    MESHES = 'meshes'
    METABALLS = 'metaballs'
    MOVIECLIPS = 'movieclips'
    NODE_GROUPS = 'node_groups'
    OBJECTS = 'objects'
    PAINT_CURVES = 'paint_curves'
    PALETTES = 'palettes'
    PARTICLES = 'particles'
    POINTCLOUDS = 'pointclouds'
    SCENES = 'scenes'
    SHAPE_KEYS = 'shape_keys'
    SOUNDS = 'sounds'
    SPEAKERS = 'speakers'
    TEXTS = 'texts'
    TEXTURES = 'textures'
    VOLUMES = 'volumes'
    WINDOW_MANAGERS = 'window_managers'
    WORKSPACES = 'workspaces'
    WORLDS = 'worlds'


def _import_asset(file: str, name: str, asset_type: Type, link: bool = False) -> bt.ID:
    with bpy.data.libraries.load(file, link=link) as (f, t):
        if not name in getattr(f, asset_type.value):
            raise KeyError(f'Asset "{name}" not in "{asset_type.value}" of source file "{file}"')
        getattr(t, asset_type.value).append(name)
    return get_asset_collection(asset_type).get(name)


def _is_ID_derived_from(id_name: str, original_name: str) -> bool:
    if id_name == original_name:
        return True

    if not id_name.startswith(original_name):  # has to start with original name
        return False
    stump = id_name.replace(original_name, '', 1)
    if not stump[0] == '.':  # stump has to have the number signature ".001"
        return False
    if not stump[1:].isnumeric():
        return False
    return True

def is_name_similar(name: str, reference_name: str):
    if name == reference_name:
        return True
    
    if name.startswith(reference_name.split(".")[0]):
        return True
    return False

def asset_is_image_asset(asset: library.Asset):
    return not asset.has_blend and asset.has_icons

def asset_meta_is_matching(meta: OrNone['AssetMeta'], asset_instance: library.AssetInstance):
    if meta is None:
        return False
    if meta.asset_instance_name != asset_instance.name:
        return False
    if meta.sl_version < al.get_adddon_bl_info()['version']:
        return False
    return True

def get_asset_collection(asset_type: Type) -> Union[bt.bpy_prop_collection, list[bt.ID]]:
    return getattr(bpy.data, asset_type.value)

def is_asset_in_file(asset_instance: library.AssetInstance, asset_type: Type):
    for asset in get_asset_collection(asset_type):
        if asset_meta_is_matching(AssetMeta.get(asset), asset_instance):
            return True
        continue
    return False # no matches found

def get_asset_from_file(asset_instance: library.AssetInstance, asset_type: Type) -> bt.ID:
    return next(x for x in get_asset_collection(asset_type) if asset_meta_is_matching(AssetMeta.get(x), asset_instance))

def try_get_asset_from_file(asset_instance: library.AssetInstance, asset_type: Type):
    try:
        return get_asset_from_file(asset_instance, asset_type)
    except StopIteration:
        return None


class ImportManager:
    '''takes in an asset instance path and an asset type. Its main use is to load the asset from the assets external file or get an asset if it is already available in the
current blend file'''

    def __init__(self, instance_path: Path, asset_type: Type):
        self.instance_path = instance_path
        self.asset_type = asset_type
        self.main_asset: bt.ID = None
        self.all_imported_assets: dict[str, list[bt.ID]] = {}

        from . import library_manager
        instance = library_manager.MANAGER.runtime_library.search_hierarchy(self.instance_path)
        if not isinstance(instance, library.AssetInstance):
            raise ValueError(f'Path provided for Asset Imporer "{str(self.instance_path)}" does not lead to an asset instance')
        self.asset_instance = instance
        self.is_image_asset = asset_is_image_asset(self.asset_instance.asset)

    @property
    def asset_collection(self) -> Union[bt.bpy_prop_collection, list[bt.ID]]:
        return get_asset_collection(self.asset_type)

    @property
    def exists_in_file(self):
        return is_asset_in_file(self.asset_instance, self.asset_type)

    def is_compatible(self, context: bt.Context):
        return context.scene.render.engine in [x.get_id() for x in self.asset_instance.asset.meta.get_engine()]

    def get_asset(self, reimport: bool):

        if not reimport:
            asset_from_file = try_get_asset_from_file(self.asset_instance, self.asset_type)
            if asset_from_file is not None:
                self.main_asset = asset_from_file
                return self.main_asset
        
        old_assets_all = {k.value: get_asset_collection(k).values() for k in Type}
        self.main_asset = self._load_asset()
        main_asset_meta = AssetMeta.from_asset_instance(self.asset_instance)
        main_asset_meta.set(self.main_asset)
        for collection_key, old_collection in old_assets_all.items():
            new_collection = getattr(bpy.data, collection_key)
            self.all_imported_assets[collection_key] = [x for x in new_collection if x not in old_collection]

        return self.main_asset

    def load_buddy_asset(self, name=None, asset_type=None, make_unique=False):
        if name is None:
            name = self.asset_instance.name

        if asset_type is None:
            asset_type = self.asset_type

        assets = get_asset_collection(asset_type)
        asset = assets.get(name)
        old_assets = set(assets)

        if (not make_unique) and (asset is not None):
            return asset
        else:
            try:
                _import_asset(str(self.asset_instance.asset.blend_file), name, asset_type=asset_type, link=False)
                added_asset =  set(assets) - old_assets
                return next(iter(added_asset))
            except KeyError:
                return None

    def _load_asset(self):
        old_assets: list[bt.ID] = list(self.asset_collection.values())

        if self.is_image_asset:
            return bpy.data.images.load(str(self.asset_instance.asset.icon_files[self.asset_instance.preset]), check_existing=False)
        _import_asset(str(self.asset_instance.asset.blend_file), self.asset_instance.name, self.asset_type, link=False)
        try:
            return next(x for x in self.asset_collection if not x in old_assets and _is_ID_derived_from(x.name, self.asset_instance.name))
        except StopIteration: # strict name matching has not succeeded. Try looser name matching
            pass
        try:
            return next(x for x in self.asset_collection if not x in old_assets and is_name_similar(x.name, self.asset_instance.name))
        except StopIteration as e:
            print(f"Critical Error occured while trying to retrieve loaded asset. Reference name is '{self.asset_instance.name}'")
            print('New imported asset (names) are:')
            print([x.name for x in self.asset_collection if not x in old_assets])
            raise e
    
    
    def remove_all_imported_assets(self):
        for key, assets in self.all_imported_assets.items():
            collection: Union[bt.bpy_prop_collection, list[bt.ID]] = getattr(bpy.data, key)
            for a in assets:
                try:
                    collection.remove(a)
                except ReferenceError:
                    print("Could not remove ID object. It likely has been removed already.")

@dataclasses.dataclass
class AssetMeta:
    '''has meta data on instances of assets within the blend file. When for example a material is imported into a user file, some meta data is being attached to it which
can be used to determin further import behavior. Keep in mind this feature was added recently and some users might still use the addon without this feature.'''

    _KEY = 'sl_asset_meta_data'

    asset_name: str
    asset_instance_name: str
    bl_version: tuple[int, ...]
    sl_version: tuple[int, ...]

    @classmethod
    def get(cls, id: bt.ID) -> OrNone['AssetMeta']:
        if not cls._KEY in id:
            return None
        
        d: dict[str, Any] = id[cls._KEY]
        d = {k:(tuple(v) if hasattr(v, 'to_list') else v) for k, v in d.items()}
        return cls(**d)
    
    @classmethod
    def fast_check(cls, id: bt.ID, key: str):
        if not cls._KEY in id:
            return None
        d: dict[str, Any] = id[cls._KEY]
        return d[key]

    def set(self, id: bt.ID):
        id[self._KEY] = {x: getattr(self, x) for x in self.__dataclass_fields__.keys()}

    @classmethod
    def from_asset_instance(cls, asset_instance: library.AssetInstance):
        return cls(asset_instance.asset.asset_name, asset_instance.name, bpy.app.version, al.get_adddon_bl_info()['version'])
