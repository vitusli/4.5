'''
This module contains all the code for generating the python representation of the sanctus library and accessing it.
The global MANAGER object contains everything about the library. Definitions for the library objects can be found in the `library.py` file.
AssetClasses distinguish between the different types of assets. All of the `main()` asset classes are the ones found in the primary panel UI for the addon in the 3D View.
SanctusLibraryAttributes manages all the library category selections in the UI.
'''

from . import auto_load as al
from .auto_load.common import *
from .t3dn_bip import previews, settings as icon_settings

from . import library as lib
from . import preferences as pref
from . import constants
from . import dev_info

# Constants
LIBRARY_PATH = Path(__file__).parent.joinpath('lib')
RUNTIME_LIBRARY_ATTR = 'sanctus_runtime_library'

# Globals
MANAGER: lib.LibraryManager = None

MAIN_LIBRARY_ASSET_COUNTS: dict[str, int] = {}

ASSETS_UP_TO_DATE: bool = False

class AssetClasses:
    MATERIALS = 'materials'
    GNTOOLS = 'gntools'
    DECALS = 'stickers'
    SHADER = 'tools'
    COMPOSITOR = 'ctools'
    SMODULES = 'smodules'

    current_ui_class: str = MATERIALS

    @classmethod
    def all(cls):
        return [cls.MATERIALS, cls.GNTOOLS, cls.DECALS, cls.SHADER, cls.COMPOSITOR, cls.SMODULES]
    
    @classmethod
    def main(cls):
        return [cls.MATERIALS, cls.GNTOOLS, cls.DECALS]
    
    @classmethod
    def main_classes_enum(cls):
        return [
            (cls.MATERIALS, 'Materials', 'Material Assets'),
            (cls.GNTOOLS, 'GN Assets', 'Geometry Node Tools'),
            (cls.DECALS, 'Decals', 'Decal Assets'),
        ]
    
    @staticmethod
    def get_active() -> str:
        return get_library_attributes().current_context
    
    @staticmethod
    def set_active_main(clss: str):
        '''Setting one of the main classes (materials, gn assets, decals) as the current context'''
        get_library_attributes().current_context = clss

    @staticmethod
    def draw(layout: bt.UILayout):
        al.UI.prop(layout, get_library_attributes(), 'current_context', al.UIOptionsProp(expand=True))


@al.register
class SanctusLibraryAttributes(bt.PropertyGroup):
    
    current_context: bpy.props.EnumProperty(items=AssetClasses.main_classes_enum()) # type: ignore

    def get(self, path: Path):
        result = getattr(self, str(path))
        if result == '':
            raise ValueError(f'Path "{str(path)}" leads to invalid path')
        return Path(result)
    
    def get_active(self, root: Union[Path, str, None] = None):
        if root is None:
            root = AssetClasses.get_active()
        if isinstance(root, str):
            root = Path(root)
        
        next = self.get(root)
        if hasattr(self, str(next)):
            next = self.get_active(next)
        
        return next
    
    def set_active(self, path: Path):
        parts = path.parts
        path_length = len(parts)
        if path_length == 0:
            raise ValueError(f'Path "{str(path)}" needs to have at least 1 level')
        if parts[0] not in AssetClasses.all():
            raise ValueError(f'Path "{str(path)}" does not start with a valid asset class')
        if parts[0] in AssetClasses.main():
            AssetClasses.set_active_main(parts[0])
        index = 1
        while index < path_length:
            setattr(self, str(Path(*parts[:index])), str(Path(*parts[:index+1])))
            index += 1

    def resolve_dirty_selections(self, debug: bool = False):
        '''run when reloading library attributes. Makes sure that any selections made invalid are being resolved'''
        for k, v in MANAGER.runtime_library.attribute_map.items():
            try:
                selection = self.get(k) # trigger value error on invalid selection
            except ValueError:
                replacement_selection = Path(v[0][0])
                if debug:
                    print(f'Selection at {k} is invalid: Setting to {str(replacement_selection)}')
                self.set_active(replacement_selection)

def get_library_attributes() -> SanctusLibraryAttributes:
    return getattr(al.get_wm(), RUNTIME_LIBRARY_ATTR)
        
def get_favorite(asset_instance: lib.AssetInstance):
    prefs = al.get_prefs()
    favorites = prefs.favorites()
    return str(asset_instance.asset.instance_path(asset_instance.preset)) in favorites.keys()

def set_favorite(asset_instance: lib.AssetInstance, favorite: bool):
    p = asset_instance.asset.instance_path(asset_instance.preset)
    prefs = al.get_prefs()
    if favorite:
        prefs.favorites[str(p)] = True
    else:
        del prefs.favorites[str(p)]
    #Reloading has to be done manually instead of just reloading the ImagePreview because otherwise the post-processing wont be triggered
    MANAGER.reload_icon(asset_instance)

def load_raw_structure():
    MANAGER.raw_files = lib.RawFileStructure(LIBRARY_PATH)
    add_expansions_to_raw_structure()
    
def add_expansions_to_raw_structure():
    prefs = al.get_prefs()
    expansion_prop = prefs.expansions().expansion_libraries
    for expansion in expansion_prop():
        expansion.loaded_successfully.value = False
        try:
            if not expansion.directory.absolute.exists():
                continue
        except OSError:
            continue
        except Exception as e:
            print(f'Unhandled exception when loading custom decals of type "{type(e).__name__}"')
            import traceback
            traceback.print_exc()
            continue

        if expansion.is_decal_folder():
            MANAGER.raw_files.add_directory(
                expansion.directory.absolute,
                Path('stickers'),
                Path(expansion.category_name().lower()),
                recursive=False,
                replace=False,
                select=(lambda p: p.is_file() and p.suffix in lib.IMAGE_FILE_TYPES)
            )
        else:
            expansion_files = lib.RawFileStructure(expansion.directory.absolute)
            MANAGER.raw_files.join(expansion_files)

        expansion.loaded_successfully.value = True

def generate_assets():
    global MAIN_LIBRARY_ASSET_COUNTS
    MAIN_LIBRARY_ASSET_COUNTS = {}
    MANAGER.all_assets = lib.AssetRepository()
    for category_path in MANAGER.raw_files.get_category_paths():
        cat: lib.RawFileStructure = MANAGER.raw_files.get_element(category_path)
        if not cat.has_files: continue
        for asset in lib.get_assets_from_paths(list(cat.get_local_files()), category_path).values():
            MANAGER.all_assets[asset.asset_path] = asset
            if asset.is_main_library_asset():
                asset_class = asset.get_asset_class()
                MAIN_LIBRARY_ASSET_COUNTS.setdefault(asset_class, 0)
                MAIN_LIBRARY_ASSET_COUNTS[asset_class] += 1

        global ASSETS_UP_TO_DATE
        ASSETS_UP_TO_DATE = True

def generate_image_file_list():
    MANAGER.image_files = {}
    for path, asset in MANAGER.all_assets.items():
        for img_file in asset.icon_files:
            icon_id = path.parent.joinpath(img_file.stem)
            MANAGER.image_files[str(icon_id)] = img_file

def register_icon_collection(register: bool):
    if register:
        icon_settings.WARNINGS = False
        MANAGER.icon_collection = previews.new(max_size=constants.THUMBNAIL_SIZE, lazy_load=True)
        icon_settings.WARNINGS = True

        for icon_id, path in MANAGER.image_files.items():
            MANAGER.icon_collection.load_safe(icon_id, str(path.absolute()), 'IMAGE')
    else:
        MANAGER.icon_collection.close()
        try:
            previews.remove(MANAGER.icon_collection)
        except KeyError:
            pass
    
def create_runtime_library():
    runtime_lib = MANAGER.runtime_library = lib.RuntimeLibrary()
    from . import filters
    sanctus_filters = filters.SanctusLibraryFilters.get_from(al.get_wm())
    sanctus_filters.all_items.clear()

    MANAGER.filtered_assets = lib.AssetRepository()

    def add_asset_instance(asset: lib.Asset, preset: int, path: Path):
        inst = runtime_lib.add_asset_instance(asset, preset, path)

        filter_item = sanctus_filters.all_items.new()
        filter_item.path.value = str(inst.path)
        filter_item.display_name.value = inst.display_name
        filter_item.search_name.value = ''.join(inst.path.parts).lower()
        filter_item.icon_id.value = MANAGER.icon_id(inst)

    for path, asset in MANAGER.all_assets.items():

        if asset.has_meta_file and sanctus_filters.is_item_filtered_out(asset.meta, asset.asset_path):
            continue # Skip filtered assets
        
        MANAGER.filtered_assets[path] = asset

        if asset.has_presets:
            for i in range(asset.preset_count):
                add_asset_instance(asset, i, path.with_name(asset.preset_names[i]))
        else:
            add_asset_instance(asset, 0, path)
    
    # add favorites
    prefs: pref.SanctusLibraryPreferences = al.get_prefs()

    for instance_path in (Path(x) for x in prefs.favorites().keys()):
        _, base_name = lib._preset_name(instance_path.name)
        asset = MANAGER.filtered_assets.get(instance_path.with_name(base_name), None)
        if asset is None:
            return # skip filtered assets
    
        favorite_path = lib.make_favorites_path(asset.asset_path)
        index = next(i for i, n in enumerate(asset.preset_names) if n == instance_path.name)
        runtime_lib.add_asset_instance(asset, index, favorite_path)

def register_library_attributes(register: bool):
    if register:
        prefs = al.get_prefs()
        favorites = prefs.favorites().keys()
        for path, hierarchy in MANAGER.runtime_library.pool_library_attribute_items():
            items: list[al.BEnumItem] = []
            fav_items: list[al.BEnumItem] = []
            for index, (key, value) in enumerate(hierarchy.items()):
                item_id = str(path.joinpath(key))
                if isinstance(value, dict): 
                    if key == lib.FAVORITES_KEY:
                        fav_items.append((item_id, "My Favorites", al.BIcon.SOLO_ON(), index))
                    else:
                        name = lib.display_name(key)
                        items.append((item_id, name, name, 0, index))
                else:
                    target_list = fav_items if item_id in favorites else items
                    target_list.append((item_id, value.display_name, value.display_name, lib.get_icon_from_asset(MANAGER.icon_collection, value.asset, value.preset).icon_id, index))
            MANAGER.runtime_library.attribute_map[str(path)] = fav_items + items

        for attribute_name, items in MANAGER.runtime_library.attribute_map.items():
            setattr(SanctusLibraryAttributes, attribute_name, bpy.props.EnumProperty(items=items))
        setattr(bt.WindowManager, RUNTIME_LIBRARY_ATTR, bpy.props.PointerProperty(type=SanctusLibraryAttributes))
        
        get_library_attributes().resolve_dirty_selections(debug=dev_info.DEBUG)
        
    else:
        for attribute_name in MANAGER.runtime_library.attribute_map.keys():
            delattr(SanctusLibraryAttributes, attribute_name)
        delattr(bt.WindowManager, RUNTIME_LIBRARY_ATTR)

def register_dynamic_asset_menu(register: bool):
    global MANAGER
    from . import operators
    if register:
        
        def _create_sub_menu(hierarchy: lib._NestedAssetMap, current_items: list):
            for key, item in hierarchy.items():
                if isinstance(item, dict):
                    entry = (key, [])
                    current_items.append(entry)
                    _create_sub_menu(item, entry[1])
                else:
                    current_items.append(
                        lambda layout, asset_instance=item: operators.materials.ApplyMaterial(path=str(asset_instance.path)).draw_ui(
                            layout, 
                            al.UIOptionsOperator(text=asset_instance.display_name, icon=MANAGER.icon_id(asset_instance))
                            )
                        )

        menu_item_map: al.MenuItemMap = ['Sanctus Assets', []]
        _create_sub_menu(MANAGER.runtime_library.hierarchy, menu_item_map[1])
        
        MANAGER.dynamic_menus = [al.MenuBuilder(menu_item_map)]
    
    for menu in MANAGER.dynamic_menus:
        menu.register(register)


@al.register
def register_library(register: bool):
    global MANAGER
    if register:
        MANAGER = lib.LibraryManager()
        load_raw_structure()
        generate_assets()
        generate_image_file_list()
        register_icon_collection(True)
        create_runtime_library()
        register_library_attributes(True)
        register_dynamic_asset_menu(True)
        MANAGER.loaded = True
    else:
        register_dynamic_asset_menu(False)
        register_library_attributes(False)
        register_icon_collection(False)
        MANAGER = None

def reload_library():
    register_library(False)
    register_library(True)

def reload_library_attributes():
    register_library_attributes(False)
    create_runtime_library()
    register_library_attributes(True)
    register_dynamic_asset_menu(True)

def reload_icons():
    register_dynamic_asset_menu(False)
    register_icon_collection(False)
    register_icon_collection(True)

def is_loaded():
    return MANAGER is not None and MANAGER.loaded

def asset_path_and_index_to_icon_path(path: Path, index: int):
    asset = MANAGER.all_assets[path]
    return asset.instance_path(index)

@al.register_timer(first_interval=0.1, threaded=False)
def process_loaded_images():
    from .t3dn_bip import threads
    from . import img_tools
    from . import preferences
    icon_ids: list[str] = []
    for i in range(10):
        try:
            collection, name = threads._queue_loaded.get(block=False)
            if collection == MANAGER.icon_collection._collection:
                icon_ids.append(name)
        except:
            break
    if len(icon_ids) < 1:
        return 0.5
    
    star_icon = img_tools.LazyPreviewImage(MANAGER.icon(Path('icons/star')))
    uv_required_icon = img_tools.LazyPreviewImage(MANAGER.icon(Path("icons/uvs_required")))

    prefs = al.get_prefs()
    favorite_instance_paths: typing.Iterable[str] = prefs.favorites().keys()
    previews = {x: MANAGER.icon_collection[x] for x in icon_ids}
    for key, preview in previews.items():
        with img_tools.PreviewEditor(preview) as editor:

            if key in favorite_instance_paths:
                editor.overlay(star_icon.image)
            asset_instance: lib.AssetInstance = MANAGER.runtime_library.search_hierarchy(Path(key))
            meta = asset_instance.asset.meta
            if meta.require_uvs:
                editor.overlay(uv_required_icon.image)

    return 0.01
