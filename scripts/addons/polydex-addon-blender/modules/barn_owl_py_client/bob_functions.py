# #### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

from datetime import datetime
import os
from typing import Dict, List, Optional


# TODO(Patrick): Resolve poliigon_core dependency in better way, as right now
# it's in an implicit location while not actually used in this source repo.
try:
    from ..poliigon_core.assets import (
        AssetData,
        AssetThumbnail,
        AssetType,
        Hdri,
        LODS,
        MAP_EXT_LOWER,
        MapType,
        Model,
        ModelMesh,
        ModelType,
        SIZES,
        Texture,
        TextureMap,
        TextureMapDesc)
except ModuleNotFoundError:
    from assets import (
        AssetData,
        AssetThumbnail,
        AssetType,
        Hdri,
        LODS,
        MAP_EXT_LOWER,
        MapType,
        Model,
        ModelMesh,
        ModelType,
        SIZES,
        Texture,
        TextureMap,
        TextureMapDesc)

BO_ASSET_TYPE_TO_ASSET_TYPE = {
    "IMAGE": AssetType.TEXTURE,
    "IMAGE_SET": AssetType.TEXTURE,
    "MATERIAL": AssetType.TEXTURE,
    "MODEL": AssetType.MODEL,
    "HDRI": AssetType.HDRI,
    "UNKNOWN": AssetType.UNSUPPORTED,
}

ASSET_TYPE_TO_STRING = {AssetType.BRUSH: "Brushes",
                        AssetType.HDRI: "HDRIs",
                        AssetType.MODEL: "Models",
                        AssetType.SUBSTANCE: "Substances",
                        AssetType.TEXTURE: "Textures",
                        AssetType.UNSUPPORTED: "Unsupported"
                        }

BO_MAP_TYPE_TO_ASSET_MAP_TYPE = {
    "ALPHA": MapType.ALPHA,
    "ALPHAMASKED": MapType.ALPHAMASKED,
    "AO": MapType.AO,
    "ARM": None,  # unsupported packed map
    "BUMP": MapType.BUMP,
    "COL": MapType.COL,
    "DIFF": MapType.DIFF,
    "DISP": MapType.DISP,
    "EMISSIVE": MapType.EMISSIVE,
    "ENV": MapType.ENV,
    "FUZZ": MapType.FUZZ,
    "GLOSS": MapType.GLOSS,
    "HDR": MapType.HDR,
    "IDMAP": MapType.IDMAP,
    "LIGHT": MapType.LIGHT,
    "MASK": MapType.MASK,
    "METALNESS": MapType.METALNESS,
    "NORMAL": MapType.NRM,  # this is the reason this dict exists
    "OPACITY": MapType.OPACITY,
    "OVERLAY": MapType.OVERLAY,
    "REFLECTION": MapType.REFL,  # this is the reason this dict exists
    "ROUGHNESS": MapType.ROUGHNESS,
    "SSS": MapType.SSS,
    "TRANSLUCENCY": MapType.TRANSLUCENCY,
    "TRANSMISSION": MapType.TRANSMISSION,
    "UNKNOWN": MapType.UNKNOWN
}

# TODO: this should ultiamtely be determined by Polydex itself over the api.
EXT_TO_MODEL_TYPE = {
    ".blend": ModelType.BLEND,
    ".c4d": ModelType.C4D,
    ".fbx": ModelType.FBX,
    ".3ds": ModelType.MAX,
    ".obj": ModelType.OBJ,
    ".usd": ModelType.USD,
    ".usda": ModelType.USD,
    ".usdc": ModelType.USD,
    ".gltf": ModelType.GLTF,
    ".glb": ModelType.GLTF,
    ".stl": ModelType.STL,
}


def get_lod_from_filename(filename: str) -> str:
    """Returns LOD from a given filename."""

    lod = "NONE"
    for _lod in LODS:
        if f"_{_lod}" in filename:
            lod = _lod
            break

    return lod


def maps_to_workflows(
        texture_maps: List[TextureMap]) -> Dict[str, List[TextureMap]]:
    """Creates a dictionary with Texture instances per workflow."""

    tex_map_workflows = {}
    any_metalness = False

    for _tex_map in texture_maps:
        if _tex_map.map_type in [MapType.METALNESS, MapType.ROUGHNESS]:
            tex_map_workflows["METALNESS"] = texture_maps.copy()
            any_metalness = True
        elif _tex_map.map_type in [MapType.GLOSS, MapType.REFL]:
            tex_map_workflows["SPECULAR"] = texture_maps.copy()
        else:
            # If if there's no other info, default to assume metal
            # e.g. if there's only a normal + disp
            tex_map_workflows["METALNESS"] = texture_maps.copy()
            # any_metalness = True

    for workflow, _tex_map_list in tex_map_workflows.items():
        if not any_metalness and workflow == "METALNESS":
            continue
        if workflow == "SPECULAR":
            map_type_filter = [MapType.METALNESS, MapType.ROUGHNESS]
        elif workflow == "METALNESS":
            map_type_filter = [MapType.GLOSS, MapType.REFL]
        tex_maps_filtered = [_tex_map
                             for _tex_map in _tex_map_list
                             if _tex_map.map_type not in map_type_filter
                             ]
        tex_map_workflows[workflow] = tex_maps_filtered

    return tex_map_workflows


def accumulate_sizes(
    tex_map_workflows: Dict[str, List[TextureMap]]
) -> Dict[str, Dict[str, List[str]]]:
    """Creates a dictionary with size lists per map type and workflow."""

    accumulated_sizes = {}

    for workflow in tex_map_workflows.keys():
        accumulated_sizes[workflow] = {}

    for workflow, _tex_map_list in tex_map_workflows.items():
        for _tex_map in _tex_map_list:
            map_type = _tex_map.map_type
            size = _tex_map.size
            if map_type in accumulated_sizes[workflow]:
                if size not in accumulated_sizes[workflow][map_type]:
                    accumulated_sizes[workflow][map_type].append(size)
                else:
                    accumulated_sizes[workflow][map_type] = [size]
            else:
                accumulated_sizes[workflow][map_type] = [size]

    return accumulated_sizes


def bo_import_group_to_mesh_maps_maptype(
    name_import_group: str,
    file_dict: Dict,
    texture_maps: List[TextureMap]
) -> None:
    """Create TextureMap instance from a BarnOwl MAPTYPE import group."""

    if name_import_group in SIZES:
        size = name_import_group
    else:
        size = "1K"  # some size, we have no idea... # update to say "default"?
        # TODO(Andreas)
        # Still won't get some assets to work, as size is still
        # missing in filename...

    map_type = file_dict["sub_type"]
    map_type = BO_MAP_TYPE_TO_ASSET_MAP_TYPE[map_type]
    if map_type is None or map_type == MapType.UNKNOWN:
        # May happen with map type ORM
        return False
    file_path = file_dict["file_path"]
    directory, filename = os.path.split(file_path)
    _, ext = os.path.splitext(filename)
    lod = get_lod_from_filename(filename)
    tex_map = TextureMap(directory=directory,
                         filename=filename,
                         file_format=ext,
                         lod=lod,
                         map_type=map_type,
                         size=size,
                         variant=None)
    texture_maps.append(tex_map)


def bo_import_group_to_mesh_maps_file(
    name_import_group: str,
    file_dict: Dict,
    meshes: List[TextureMap]
) -> None:
    """Create TextureMap instance from a BarnOwl GENERICFILE or NATIVEFILE
    import group.
    """

    # Skip loading models entirely (for now), since there
    # are some textures which are shipped with example
    # native files, throwing off this logic. Means that
    # materials of these models will be loaded without geo.
    # TODO(Andreas): Enable Model importing

    file_path = file_dict["file_path"]
    directory, filename = os.path.split(file_path)
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in EXT_TO_MODEL_TYPE:
        # e.g. skip .skp, .max, or other 3d formats.
        return
    model_type = EXT_TO_MODEL_TYPE[ext]
    lod = get_lod_from_filename(filename)
    mesh = ModelMesh(directory=directory,
                     filename=filename,
                     lod=lod,
                     model_type=model_type)
    meshes.append(mesh)


def bo_import_group_to_mesh_maps_preview(
    name_import_group: str,
    file_dict: Dict,
    texture_maps: List[TextureMap]
) -> None:
    """Create TextureMap instances from a BarnOwl PREVIEW import group."""

    # Ignore previews
    return


def bo_import_group_to_mesh_maps_unknown(
    name_import_group: str,
    file_dict: Dict,
    texture_maps: List[TextureMap]
) -> bool:
    """Create TextureMap instances from BarnOwl IMAGE, IMAGE_SET and UNKNOWN
    import groups.
    """

    file_path = file_dict["file_path"]
    _, ext = os.path.splitext(file_path)
    ext_lower = ext.lower()
    if ext_lower not in MAP_EXT_LOWER:
        print(f"Import group {name_import_group} unknown file "
              f"type:\n{file_path}")
        return False

    # UNKNOWN images happen with IMAGE and IMAGE_SET assets.
    # In order to avoid material importer accidentally connecting these
    # to wrong channels, we'll mark the undefined.
    # BOB importer then for example creates disconnected texture nodes for
    # these maps.
    map_type = MapType.UNDEF

    directory, filename = os.path.split(file_path)
    _, ext = os.path.splitext(filename)

    tex_map = TextureMap(directory=directory,
                         filename=filename,
                         file_format=ext,
                         lod=None,
                         map_type=map_type,
                         size="1K",   # TODO(Andreas): any better?
                         variant=None)
    texture_maps.append(tex_map)
    return True


def bo_import_group_to_mesh_maps(
    bo_import_groups: Dict,
    texture_maps: List[TextureMap],
    meshes: List[ModelMesh],
) -> bool:
    """Create TextureMap and ModelMesh instances from a BarnOwl
    import group.

    Returns whether this is a stacked asset or not, true if 1+ files
    """

    preview_maps: List[TextureMap] = []
    is_stack = None

    for name_import_group, file_list in bo_import_groups.items():
        for file_dict in file_list:
            if is_stack is None:
                is_stack = False
            elif is_stack is False:
                is_stack = True
            file_type = file_dict["type"]

            if file_type == "MAPTYPE":
                bo_import_group_to_mesh_maps_maptype(
                    name_import_group, file_dict, texture_maps)
            elif file_type == "HDRI":
                bo_import_group_to_mesh_maps_maptype(
                    name_import_group, file_dict, texture_maps)
            elif file_type in ["GENERICFILE", "NATIVEFILE"]:
                bo_import_group_to_mesh_maps_file(
                    name_import_group, file_dict, meshes)
            elif file_type == "PREVIEW":
                bo_import_group_to_mesh_maps_unknown(
                    name_import_group, file_dict, preview_maps)
            elif file_type == "UNKNOWN":
                # Have unknown images as UNDEF tex files
                bo_import_group_to_mesh_maps_unknown(
                    name_import_group, file_dict, texture_maps)
            else:
                print(f"Unknown file type {file_type} "
                      f"in import group {name_import_group}"
                      f"\n{file_list}")
                continue

    # In case of no texture maps, we'll allow to import the preview thumb...
    if len(texture_maps) == 0 and len(preview_maps) > 0:
        texture_maps[:] = preview_maps[:]

    return bool(is_stack)


def bo_import_group_create_texture(
        texture_maps: List[TextureMap]) -> Optional[Texture]:
    """If import group contained any texture maps, create a Texture
    instance.
    """

    if len(texture_maps) <= 0:
        return None

    tex_map_workflows = maps_to_workflows(texture_maps)
    accumulated_sizes = accumulate_sizes(tex_map_workflows)

    texture_descs = {}
    tex_sizes = set()

    for workflow in accumulated_sizes.keys():
        texture_descs[workflow] = []

    for workflow, map_type_size_dict in accumulated_sizes.items():
        for _map_type, _sizes in map_type_size_dict.items():
            # Assuming here neither GLOSS nor METALNESS have a unique size
            tex_desc = TextureMapDesc(display_name=_map_type.name,
                                      file_formats=[],
                                      filename_preview="",
                                      map_type_code=_map_type.name,
                                      sizes=_sizes,
                                      variants=[])
            texture_descs[workflow].append(tex_desc)
            tex_sizes |= set(_sizes)

    lods = set()
    for _tex_map in texture_maps:
        lods |= {_tex_map.lod}

    texture = Texture(lods=list(lods),
                      map_descs=texture_descs,
                      maps=tex_map_workflows,
                      sizes=tex_sizes,
                      variants=None,
                      watermarked_urls=None,
                      real_world_dimension=None)
    return texture


def bo_import_group_create_model(
        meshes: List[ModelMesh], texture: Texture) -> Optional[Model]:
    """If import group contained any mesh files, create a Model
    instance.
    """

    if len(meshes) <= 0:
        return None

    lods = set()
    for _mesh in meshes:
        lods |= {_mesh.lod}

    model = Model(lods=list(lods),
                  meshes=meshes,
                  sizes=texture.sizes if texture else [],
                  size_default=None,
                  texture=texture)
    return model


def bo_import_group_create_hdri(texture: Texture) -> Optional[Hdri]:
    hdri = Hdri(
        bg = texture,
        light = texture)
    return hdri


def bo_import_generate_categories(asset_type: AssetType) -> List[str]:
    """Have at least the top level categories."""

    if asset_type == AssetType.HDRI:
        categories = ["HDRIs"]
    elif asset_type == AssetType.MODEL:
        categories = ["Models"]
    elif asset_type == AssetType.TEXTURE:
        categories = ["Textures"]
    else:
        categories = []
    return categories


def create_unsupported_asset_type_data() -> Hdri:
    """Returns an Hdri AssetData sub-type with an more or less empty Texture.

    Note:
    Misusing HDRI type here to get to an "unsupported asset" thumbnail.
    It will appear "non-local" due to having no texture paths.
    BOB's UI will interpret this as "unsupported by BOB".
    """

    tex_map = TextureMap(directory="",
                         filename="",
                         lod="NONE",
                         map_type=MapType.UNKNOWN,
                         size="1K",
                         variant=None)
    tex_desc = TextureMapDesc(display_name="",
                              file_formats=[],
                              filename_preview="",
                              map_type_code=MapType.UNKNOWN,
                              sizes=["1K"],
                              variants=[])
    tex = Texture(lods=["NONE"],
                  map_descs={"REGULAR": [tex_desc]},
                  maps={"REGULAR": [tex_map]},
                  sizes=["1K"],
                  variants=None,
                  watermarked_urls=None,
                  real_world_dimension=None)

    hdri = Hdri(light=tex, bg=tex)
    # print("Failed to determine asset type")
    # print(bo_asset_data)
    return hdri


def bo_asset_data_to_ai_asset_data(bo_asset_data: Dict) -> AssetData:
    """Converts BarnOwl asset detail dictionary into an AssetData instance."""
    asset_id = bo_asset_data["asset_id"]
    asset_name = bo_asset_data["asset_name"]
    bo_asset_type = bo_asset_data["type"]
    asset_type = BO_ASSET_TYPE_TO_ASSET_TYPE.get(bo_asset_type, AssetType.UNSUPPORTED,)
    is_image_set = bo_asset_type in ["IMAGE", "IMAGE_SET"]
    thumb_path = bo_asset_data["thumbnail_path"]

    # Initialize all types to none, then map files to addon format
    hdri = None
    model = None
    texture = None

    # Iterate BarnOwl's import groups and build ModelMesh and/or
    # TextureMap instances
    bo_import_groups = bo_asset_data["import_groups"]
    texture_maps = []
    meshes = []
    is_local = True

    # Populate the breakdown of individual file types
    is_stack = bo_import_group_to_mesh_maps(bo_import_groups, texture_maps, meshes)
    if asset_type == AssetType.TEXTURE:
        texture = bo_import_group_create_texture(texture_maps)
    elif asset_type == AssetType.MODEL:
        model = bo_import_group_create_model(meshes, texture)
    elif asset_type == AssetType.HDRI:
        texture = bo_import_group_create_texture(texture_maps)
        hdri = bo_import_group_create_hdri(texture)
    else:
        asset_type = AssetType.HDRI
        hdri = create_unsupported_asset_type_data()
        texture = None
        is_local = False
        # print("Failed to determine asset type")
        # print(bo_asset_data)

    categories = bo_import_generate_categories(asset_type)

    thumbs = []
    if len(thumb_path) > 0 and os.path.isfile(thumb_path):
        thumb_ext = os.path.splitext(thumb_path)
        thumbnail = AssetThumbnail(
            filename=thumb_path,
            base_url="",
            index=0,
            time=datetime.now(),
            type=thumb_ext)
        thumbs.append(thumbnail)

    asset_data = AssetData(
        asset_id=asset_id,
        asset_type=asset_type,
        asset_name=asset_name,
        display_name=asset_name,
        categories=categories,
        url=None,
        slug=None,
        cloudflare_thumb_urls=thumbs,
        published_at=None,
        is_local=is_local,
        downloaded_at=None,
        is_purchased=True,
        purchased_at=None,
        render_custom_schema=None,
        api_convention=0,
        local_convention=0,
        brush=None,
        hdri=hdri,
        model=model,
        texture=texture
    )
    asset_data.runtime.set_is_polydex_image(is_polydex_image=is_image_set)
    asset_data.runtime.set_is_polydex_stack(is_polydex_stack=is_stack)

    return asset_data
