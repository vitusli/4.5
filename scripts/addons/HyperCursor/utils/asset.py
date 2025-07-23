import bpy
import os

from . object import is_instance_collection
from . registration import get_prefs
from . system import printd, abspath

def get_asset_ids(context):
    active = context.asset

    if active:
        return active, active.id_type, active.local_id

    return None, None, None

def get_catalogs_from_asset_libraries(context, debug=False):
    asset_libraries = context.preferences.filepaths.asset_libraries
    all_catalogs = []

    for lib in asset_libraries:
        libname = lib.name
        libpath = lib.path

        cat_path = os.path.join(libpath, 'blender_assets.cats.txt')

        if os.path.exists(cat_path):
            if debug:
                print(libname, cat_path)

            with open(cat_path) as f:
                lines = f.readlines()

            for line in lines:
                if line != '\n' and not any([line.startswith(skip) for skip in ['#', 'VERSION']]) and len(line.split(':')) == 3:
                    all_catalogs.append(line[:-1].split(':') + [libname, libpath])

    catalogs = {}

    for uuid, catalog, simple_name, libname, libpath in all_catalogs:
        if uuid not in catalogs:
            catalogs[uuid] = {'catalog': catalog,
                              'simple_name': simple_name,
                              'libname': libname,
                              'libpath': libpath}

    if debug:
        printd(catalogs)

    return catalogs

def update_asset_catalogs(self, context, curve=False):
    self.catalogs = get_catalogs_from_asset_libraries(context, debug=False)

    catalog_names = []
    items = [('NONE', 'None', '')]

    for uuid, catalog_data in self.catalogs.items():
        catalog = catalog_data['catalog']

        if catalog not in catalog_names:
            catalog_names.append(catalog)
            items.append((catalog, catalog, ''))

    if curve:
        default = get_prefs().preferred_default_catalog_curve if get_prefs().preferred_default_catalog_curve in catalog_names else 'NONE'
    else:
        default = get_prefs().preferred_default_catalog if get_prefs().preferred_default_catalog in catalog_names else 'NONE'
    bpy.types.WindowManager.HC_asset_catalogs = bpy.props.EnumProperty(name="Asset Categories", items=items, default=default)

def get_library_from_path(context, path):
    librariesCOL = context.preferences.filepaths.asset_libraries

    for lib in librariesCOL:
        if abspath(lib.path) == abspath(path):
            return lib

def get_import_method_from_library_path(context, path):
    if lib := get_library_from_path(context, path):
        return lib.import_method

def get_pretty_assetpath(inpt, debug=False) -> str:

    if debug:
        print()
        print("get_pretty_assetspath()")

    if isinstance(inpt, list):
        libname, filename = inpt

        if libname == 'LOCAL':
            if f"Object{os.sep}" in filename:
                filename = filename.replace(f"Object{os.sep}", '')
                return f"{libname} • {filename}"

        else:
            split = filename.split(f".blend{os.sep}Object{os.sep}")

            if len(split) == 2:
                blendname, assetname = split

                return f"{libname} • {blendname} • {assetname}"

    else:
        from HyperCursor.properties import RedoAddObjectCollection

        if isinstance(inpt, RedoAddObjectCollection):
            asset = inpt

        elif isinstance(inpt, dict):
            asset = inpt

        else:
            asset = inpt.HC

        if debug:
            print()
            print("libname:", asset.get('libname'))
            print("blendpath:", asset.get('blendpath'))
            print("assetname:", asset.get('assetname'))

        if asset.get('libname') == 'LOCAL':
            return f"{asset.get('libname')} • {asset.get('assetname')}"

        elif asset.get('assetname') and len(bpy.context.preferences.filepaths.asset_libraries) > 1:
            return f"{asset.get('libname')} • {asset.get('blendpath')} • {asset.get('assetname')}" if asset.get('blendpath') else f"{asset.get('libname')} • {asset.get('assetname')}"

        elif asset.get('assetname'):
            return f"{asset.get('blendpath')} • {asset.get('assetname')}" if asset.get('blendpath') else f"{asset.get('libname')} • {asset.get('assetname')}"

        else:
            return inpt.name

    return ''

def get_asset_details_from_space(context, space, asset_type='OBJECT', debug=False):

    lib_reference = space.params.asset_library_reference
    catalog_id = space.params.catalog_id
    libname = '' if lib_reference == 'ALL' else lib_reference
    libpath = space.params.directory.decode('utf-8')
    filename = space.params.filename
    import_method = space.params.import_method

    if debug:
        print()
        print("get_asset_details_from_space()")
        print(" asset_library_reference:", lib_reference)
        print(" catalog_id:", catalog_id)
        print(" libname:", libname)
        print(" libpath:", libpath)
        print(" filename:", filename)
        print(" import_method:", import_method)
        print()

    if not filename:
        if debug:
            print(" WARNING: no asset selected!")

        return None, None, '', None

    elif asset_type and f"{asset_type.title()}{os.sep}" not in filename:
        if debug:
            print(f" WARNING: unsupported asset type selected, expected '{asset_type}'")

        return None, None, '', None

    if libname == 'ESSENTIALS':
        return None, None, '', None

    elif asset_type and libname == 'LOCAL':
        if f"{asset_type.title()}{os.sep}" in filename:
            return libname, libpath, filename, import_method

    elif '.blend' not in filename:
        if debug:
            print(" WARNING: LOCAL library, but ALL or library is chosen (instead of current file)!")

        if f"{asset_type.title()}{os.sep}" in filename:
            return 'LOCAL', '', filename, import_method

    elif not libname and not libpath:
        if debug:
            print(" WARNING: EXTERNAL library, but library ref is ALL and directory is not set!")

        catalogs = get_catalogs_from_asset_libraries(context, debug=False)

        for uuid, catdata in catalogs.items():
            if catalog_id == uuid:
                catalog = catdata['catalog']
                libname = catdata['libname']
                libpath = catdata['libpath']

                if debug:
                    print(f" INFO: found catalog {catalog}'s libname and libpath via asset catalogs:", libname, "at", libpath)
                break
    if debug:
        print()

    if libpath:
        return libname, libpath, filename, import_method

    else:
        return None, None, '', None

def get_instance_collection_objects_recursively(col, objects: set):
    sub_cols = set(col.children_recursive)

    for col in {col} | sub_cols:
        for obj in col.objects:
            if icol := is_instance_collection(obj):
                get_instance_collection_objects_recursively(icol, objects)

            else:
                objects.add(obj)
