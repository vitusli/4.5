from pathlib import Path
from .. import library as lib

def create_new_library(new_path: Path, manager: lib.LibraryManager):
    import shutil
    for asset in manager.all_assets.values():
        
        source_blend_paths: list[Path] = []
        meta_file: Path = asset.directory.joinpath(asset.asset_name + lib.FILE_JSON)
        icon_files: list[Path] = []
        if asset.has_presets:
            for i in range(asset.preset_count):
                source_blend_paths.append(asset.directory.joinpath(asset.preset_names[i] + lib.FILE_BLEND))
                icon_files.append(asset.icon_files[i])
            meta_file = meta_file.with_name(asset.preset_names[0] + lib.FILE_JSON)
        else:
            if asset.has_blend:
                source_blend_paths.append(asset.blend_file)
            if asset.has_icons:
                icon_files += asset.icon_files

        new_asset_directory = (new_path / asset.asset_path.parent)

        new_blend_path = new_asset_directory.joinpath(asset.asset_name + lib.FILE_BLEND) if asset.has_blend or asset.has_presets else None
        new_asset_directory.mkdir(parents=True, exist_ok=True)
        if new_blend_path is not None:
            new_blend_path.touch(exist_ok=False)
        for if_ in icon_files:
            new_path = new_asset_directory.joinpath(if_.name)
            shutil.copy(str(if_), str(new_path))
        if meta_file.exists():
            shutil.copy(str(meta_file), new_asset_directory.joinpath(asset.asset_name + lib.FILE_JSON))
