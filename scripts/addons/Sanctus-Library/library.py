'''
This module contains all the definitions for library objects. pathlib.Path objects are used here as keys to find assets and navigate the graphs.  
'''


from . import auto_load as al
from .auto_load.common import *
import dataclasses
from .t3dn_bip import previews

# Constants
FILE_SEPARATOR = '_'
T = typing.TypeVar("T")
_NestedAssetMap = dict[str, Union['AssetInstance', '_NestedAssetMap']]

FILE_PNG = '.png'
FILE_JPG = '.jpg'
FILE_BLEND = '.blend'
FILE_BIP = '.bip'
FILE_JSON = '.json'

FILE_EXPANSION = '.expansion'

VALID_FILE_TYPES = [FILE_PNG, FILE_JPG, FILE_BIP, FILE_BLEND, FILE_JSON]
IMAGE_FILE_TYPES = [FILE_PNG, FILE_JPG, FILE_BIP]

FAVORITES_KEY = 'my_favorites'

class LibraryManager:
    '''container for everything to do with library management. Manages assets, asset instances and image files that are displayed as thumbnails. '''

    raw_files: 'RawFileStructure'
    all_assets: 'AssetRepository'
    filtered_assets: 'AssetRepository'
    image_files: dict[str, Path]
    icon_collection: previews.ImagePreviewCollection
    runtime_library: 'RuntimeLibrary'
    dynamic_menus: list[al.MenuBuilder]
    loaded: bool

    def __init__(self):
        self.loaded = False

    def icon_from_instance(self, instance: 'AssetInstance'):
        return get_icon_from_asset_instance(self.icon_collection, instance)
    
    def icon_from_asset(self, asset: 'Asset', index: int):
        return get_icon_from_asset(self.icon_collection, asset, index)
    
    def get_all_instances(self, asset: 'Asset') -> Generator['AssetInstance', None, None]:
        for preset_name in asset.preset_names:
            yield self.runtime_library.search_hierarchy(asset.asset_path.with_name(preset_name))
    
    def icon(self, obj: Union['Asset', 'AssetInstance', Path], index: int = 0):
        if isinstance(obj, Path):
            return self.icon_collection[str(obj)]
        if isinstance(obj, AssetInstance):
            return get_icon_from_asset_instance(self.icon_collection, obj)
        if isinstance(obj, Asset):
            return get_icon_from_asset(self.icon_collection, obj, index)
        
    def icon_id(self, obj: Union['Asset', 'AssetInstance', Path], index: int = 0):
        return self.icon(obj, index).icon_id

    def reload_icon(self, instance: 'AssetInstance'):
        reload_icon(self.icon_collection, instance.icon_path, instance.asset.icon_files[instance.preset])

def _filter_glob(search_results: typing.Generator[Path, None, None]):
    return sorted(x for x in search_results if x.is_dir() or x.suffix in VALID_FILE_TYPES)


def _preset_name(name: str) -> tuple[bool, str]:
    '''Returns tuple with first element checking if the name is a preset name and the second element returning the base name'''
    parts = name.split(FILE_SEPARATOR)
    if len(parts) < 2 or (not parts[-1].isnumeric()):
        return (False, name)
    return (True, name.removesuffix(f'{FILE_SEPARATOR}{parts[-1]}'))


def _create_blendpath(directory: Path, name: str):
    return directory.joinpath(name + FILE_BLEND)

def _get_blendpath(directory: Path, name: str):
    p = _create_blendpath(directory, name)
    return p if p.exists() else None

def _create_metapath(directory: Path, name: str):
    return directory.joinpath(name + FILE_JSON)

def _get_metapath(directory: Path, name: str):
    p = _create_metapath(directory, name)
    return p if p.exists() else None


def _is_image_file(file: Path):
    return file.suffix in IMAGE_FILE_TYPES


def search_dict(d: dict[str, T], path: Path):
    current = d
    parts = list(path.parts)
    while len(parts) > 0:
        current = current[parts[0]]
        parts.pop(0)
    return current

def get_icon_from_asset(icon_collection: previews.ImagePreviewCollection, asset: 'Asset', index: int = 0):
    if not asset.has_icons:
        return icon_collection[str(Path('icons/icon'))]
    lookup_path = asset.asset_path.with_name(asset.preset_names[index])
    return icon_collection[str(lookup_path)]

def get_icon_from_asset_instance(icon_collection: previews.ImagePreviewCollection, asset_instance: 'AssetInstance'):
    if not asset_instance.asset.has_icons:
        return icon_collection[str(Path('icons/icon'))]
    return icon_collection[str(asset_instance.icon_path)]

def reload_icon(icon_collection: previews.ImagePreviewCollection, path: Path, file: Path):
    icon_collection.pop(str(path))
    icon_collection.load_safe(str(path), str(file), 'IMAGE')

def display_name(name: str):
    return name.replace('_', ' ').title()

def make_favorites_path(path: Path):
    return path.parent.with_name(FAVORITES_KEY).joinpath(path.name)

class RawFileStructure(dict[str, Union["RawFileStructure", Path]]):
    '''a representation of the file structure on disk. Maps directories as strings to files as Paths'''

    @property
    def has_files(self):
        return any(isinstance(x, Path) for x in self.values())
    
    @property
    def files_only(self):
        return all(isinstance(x, Path) for x in self.values())
    
    def __init__(self, root: Path, recursive: bool = True, select: Callable[[Path], bool] = None):
        root_contents = _filter_glob(root.glob("*"))
        if select is not None:
            root_contents = [x for x in root_contents if select(x)]
        for c in root_contents:
            if c.is_dir() and recursive:
                self[c.name] = RawFileStructure(c, recursive=True, select=select)
            else:
                self[c.name] = c
    
    # post-processing the file structure
    def add_directory(self, directory: Path, parent: Path, new_path: Path, recursive: bool = True, replace: bool = False, select: Callable[[Path], bool] = None):
        current = self.get_element(parent)
        new_files = RawFileStructure(directory, recursive=recursive, select=select)
        if current.get(new_path.name, None) is None or replace:
            current[new_path.name] = new_files
        else:
            current[new_path.name].update(new_files)

    def __repr__(self):
        content = ','.join([(f'{k}: {v}' if isinstance(v, Path) else "[" + k + "]") for k, v in self.items()])
        return '{' + content + '}'
    
    def __getitem__(self, __key: Union[str, int]):
        if isinstance(__key, int):
            return super().__getitem__(list(self.keys())[__key])
        return super().__getitem__(__key)

    def get_files(self):
        for v in self.values():
            if isinstance(v, Path):
                yield v
            else:
                yield from v.get_files()

    def get_local_files(self):
        for v in self.values():
            if isinstance(v, Path):
                yield v
    
    def get_category_paths(self, parent_path: Path = Path()) -> Generator[Path, None, None]:
        yield parent_path
        for k, v in self.items():
            if isinstance(v, Path): continue
            current = parent_path.joinpath(k)
            yield from v.get_category_paths(current)
    
    def get_element(self, path: Path):
        current = self
        parts = list(path.parts)
        while len(parts) > 0:
            current = current[parts[0]]
            parts.pop(0)
        return current
    
    def join(self, other: "RawFileStructure"):
        keys = [x.lower() for x in self.keys()]
        for other_key, other_value in other.items():
            if other_key.lower() in keys:
                self_value = self[other_key]
                if isinstance(other_value, RawFileStructure) and isinstance(self_value, RawFileStructure):
                    self_value.join(other_value)
            else:
                self[other_key] = other_value


@dataclasses.dataclass(unsafe_hash=True)
class Asset:
    '''object describing a Sanctus Library Asset. Different uses of assets are documented in the addon __init__.py file'''

    directory: Path
    asset_path: Path
    asset_name: str
    blend_file: Optional[Path] = None
    meta_file: Optional[Path] = None
    icon_files: list[Path] = dataclasses.field(default_factory=[])
    has_presets: bool = False
    _meta: 'meta_data.SanctusMetaData' = None
    
    @property
    def has_blend(self):
        return self.blend_file is not None
    
    @property
    def has_meta_file(self):
        return self.meta_file is not None

    @property
    def meta(self):
        if self._meta is None: 
            if self.has_meta_file:
                self._meta = meta_data.SanctusMetaData.from_file(self.meta_file)
            else:
                self._meta = meta_data.SanctusMetaData()
        return self._meta
    
    @meta.setter
    def meta(self, value: 'meta_data.SanctusMetaData'):
        self._meta = value
    
    @property
    def has_icons(self):
        return len(self.icon_files) > 0
    
    @property
    def preset_count(self):
        return len(self.icon_files)
    
    @property
    def preset_names(self):
        return [x.stem for x in self.icon_files]
    
    def instance_path(self, index: int):
        if self.preset_count == 0:
            return self.asset_path
        return self.asset_path.with_name(self.preset_names[index])
    
    def __repr__(self):
        return f'Asset(name={self.asset_name}, path={str(self.asset_path)}, B={self.has_blend}, M={self.has_meta_file}, I={self.preset_count})'
    
    def get_asset_class(self):
        return self.asset_path.parts[0]
    
    def is_main_library_asset(self):
        from . import library_manager
        return self.directory.is_relative_to(library_manager.LIBRARY_PATH)


def set_asset_meta_data(asset: Asset, new_meta_data: 'meta_data.SanctusMetaData'):
    new_meta_path = asset.directory.joinpath(asset.asset_name + FILE_JSON)
    new_meta_data.to_file(_get_metapath(asset.directory, asset.asset_name))
    asset.meta = new_meta_data
    asset.meta_file = new_meta_path


@dataclasses.dataclass
class AssetInstance:
    '''An instance of an asset using a specific preset. Assets without presets also have instances, but only one per asset'''
    asset: Asset
    preset: int
    path: Path
    
    @property
    def name(self):
        if self.asset.has_icons:
            return self.asset.preset_names[self.preset]
        return self.asset.asset_name

    @property
    def display_name(self):
        return display_name(self.name)
    
    @property
    def icon_path(self):
        return self.asset.instance_path(self.preset)



class AssetRepository(dict[Path, 'Asset']):
    '''`dict` wrapper mapping Paths to Assets'''

    def get_subrepo(self, path: Path) -> 'AssetRepository':
        if path in self.keys():
            raise KeyError(f'Key "{str(path)}" stores an Asset. Can only take part-paths')
        return type(self)({k: v for k, v in self.items() if k.is_relative_to(path)})

class RuntimeLibrary:
    '''This object inside the `LibraryManager` is dynamic and changes based on selected filters and other categories. Every time a filter is updated, this structure
also gets updated. This is used to lookup asset instances based on user interaction through the UI'''

    hierarchy: _NestedAssetMap
    attribute_map: dict[str, al.BEnumItem]

    def __init__(self):
        self.hierarchy = {}
        self.attribute_map = {}

    def search_hierarchy(self, path: Path):
        return search_dict(self.hierarchy, path)
    
    def get_or_create_sub_hierarchy(self, path: Path):
        current_level = self.hierarchy
        parts = path.parts
        while len(parts) > 0:
            start = parts[0]
            if not start in current_level.keys():
                current_level[start] = {}

            if not isinstance(current_level.get(start), dict):
                raise KeyError(f'Path "{str(path)}" does not follow through sub-hierarchies ONLY.')
            
            current_level: _NestedAssetMap #Helping the annotation
            
            current_level = current_level[start]
            parts = parts[1:]
        return current_level

    def add_asset_instance(self, asset: Asset, preset: int, path: Path):
        instance = AssetInstance(asset, preset, path)

        sub_hierarchy = self.get_or_create_sub_hierarchy(path.parent)
        sub_hierarchy[path.name] = instance
        return instance

    def pool_library_attribute_items(self) -> Generator[tuple[Path, _NestedAssetMap], None, None]:
        
        def generate(h: _NestedAssetMap, path: Path = Path()):
            yield (path, h)
            for (key, value) in h.items():
                if isinstance(value, dict): 
                    yield from generate(value, path.joinpath(key))

        for k, v in self.hierarchy.items():
            if isinstance(v, dict):
                yield from generate(v, Path(k))

def get_assets_from_paths(paths: list[Path], relative_path: Path):

    results: dict[str, Asset]  = {}
    used_keys: set[str] = set()

    #iterate image files
    image_files = [x for x in paths if _is_image_file(x)]
    for e in image_files:
        stem = e.stem
        if stem in used_keys: continue

        is_preset, base_name = _preset_name(stem)
        similar_preset_files = [e]

        if is_preset:
            similar_preset_files = [x for x in image_files if _preset_name(x.stem) == (True, base_name)]
            used_keys = used_keys.union({x.stem for x in similar_preset_files}) # log away image preset files
            used_keys.add(base_name) # log away blend file
        else:
            used_keys.add(e.stem)
        results[base_name] = Asset(
            directory=      e.parent, 
            asset_path=     relative_path.joinpath(base_name), 
            asset_name=     base_name, 
            blend_file=     _get_blendpath(e.parent, base_name), 
            meta_file=      _get_metapath(e.parent, base_name), 
            icon_files=     similar_preset_files,
            has_presets=    is_preset,
        )

    #iterate blend files without images
    for e in [x for x in paths if x.suffix == FILE_BLEND]:
        stem = e.stem
        if stem in used_keys: continue

        used_keys.add(stem)
        results[stem] = Asset(e.parent, relative_path.joinpath(stem), stem, e, _get_metapath(e.parent, stem), [], False)
    
    return results

from . import meta_data
