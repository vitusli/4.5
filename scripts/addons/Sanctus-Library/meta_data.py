'''
SanctusMetaData can be loaded from and saved to disk. Each asset has specific tags and attributes used for filtering that are stored here. Meta data is being stored in .json format along-side assets. 
'''

import bpy
import json
import typing
import dataclasses

from . import auto_load as al
from .auto_load.common import *

from . import dev_info
from . import constants

FIX_META_DATA: bool = False

EEVEE_ENGINE_ENUM = 'BLENDER_EEVEE' if bpy.app.version < constants.EEVEE_NEXT else 'BLENDER_EEVEE_NEXT'

def fix_meta_data():
    return FIX_META_DATA and dev_info.DEVELOPER_MODE

def get_render_engine_name(engine_id: str) -> str:
    builtin_engines_map = {
        EEVEE_ENGINE_ENUM: 'Eevee',
        'BLENDER_WORKBENCH': 'Workbench',
        'CYCLES': 'Cycles'
    }
    fallback_name = engine_id.replace('_', ' ').title()
    return builtin_engines_map.get(engine_id, fallback_name)

class MetaEngine(al.BStaticEnum):

    C = dict(n='Cycles', d='Use the Cycles Render Engine', a='CYCLES')
    E = dict(n='Eevee', d='Use the Eevee Render Engine', a=EEVEE_ENGINE_ENUM)

    def get_id(self) -> str:
        return self.value['a']
    

def meta_engine_from_id(id: str):
    return next(x for x in MetaEngine if x.get_id() == id)

def material_output_id_from_met_engines(s = set[MetaEngine]):
    if s == {MetaEngine.C}:
        return 'CYCLES'
    if s == {MetaEngine.E}:
        return 'EEVEE'
    return 'ALL'

class MetaComplexity(al.BStaticEnum):

    _0 = dict(n='Low', d='Low Complexity')
    _1 = dict(n='Medium', d='Medium Complexity')
    _2 = dict(n='High', d='High Complexity')


class GeometryNodeAssetType(al.BStaticEnum):

    ADD_NEW = dict(n='Add New', d='Any type of asset or non-GN assets')
    APPLY_MESH = dict(n='Apply to Mesh', d='Add asset as modifier to selected mesh obeject')
    APPLY_CURVE = dict(n='Apply to Curve', d='Add asset as modifier to selected curve object')
    APPLY_PARENTED_CURVE = dict(n='Apply Parented Curve', d='Add asset as modifier on a curve parented to a mesh object')
    DRAW_FREE = dict(n='Free Draw', d='New curve object with curve draw mode enabled')
    DRAW_SURFACE = dict(n='Draw on Surface', d='New curve object added to selected object to draw on surface')
    PLACE_SURFACE = dict(n='Place on Surface', d='Add asset as new object and place it on surface')

@dataclasses.dataclass
class SanctusMetaData:

    engine: list[str] = dataclasses.field(default_factory=(lambda: [x() for x in MetaEngine.all()]))

    def get_engine(self):
        return {MetaEngine.from_string(x) for x in self.engine}

    def set_engine(self, value: MetaEngine):
        self.engine = list(value())

    complexity: str = MetaComplexity._0()

    def get_complexity(self):
        return MetaComplexity.from_string(self.complexity)

    def set_complexity(self, value: MetaComplexity):
        self.complexity = value()

    gn_type: list[str] = dataclasses.field(default_factory=(lambda: [GeometryNodeAssetType.ADD_NEW()]))

    def get_gn_type(self):
        return {GeometryNodeAssetType.from_string(x) for x in self.gn_type}
    
    def set_gn_type(self, value: GeometryNodeAssetType):
        self.gn_type = [value()]

    use_displacement: bool = False
    require_uvs: bool = False
    match_materials: bool = False

    description: str = ''
    documentation_link: str = ''

    @classmethod
    def keys(cls) -> list[str]:
        return cls.__dataclass_fields__.keys()

    def items(self) -> list[tuple[str, typing.Any]]:
        return [(k, getattr(self, k)) for k in self.keys()]

    def values(self) -> list[typing.Any]:
        return [getattr(self, k) for k in self.keys()]

    @classmethod
    def from_file(cls, filepath: Path) -> 'SanctusMetaData':
        with filepath.open('r') as openfile:
            try:
                data = json.load(openfile)
            except json.JSONDecodeError as e:
                print(f'Corrupted Meta Data in file "{str(filepath)}"')
                if fix_meta_data():
                    print('Using Default Meta Data')
                    data = SanctusMetaData().to_dict()
                else:
                    raise e
        if fix_meta_data():
            fix_json_meta_data(data)
        meta = SanctusMetaData(**data)
        if fix_meta_data():
            meta.to_file(filepath)
        return meta

    def to_dict(self):
        return {k: v for k, v in self.items()}

    def to_file(self, filepath: Path) -> None:
        data = self.to_dict()
        with filepath.open('w') as openfile:
            json.dump(data, openfile)

    def has_description(self) -> bool:
        return self.description != ''

    def get_description(self):
        real_description = self.description.replace('\\n', '\n')
        return real_description


def fix_json_meta_data(data: dict[str, typing.Any]):
    # Fix complexity being saved as int
    complexity = data['complexity']
    if isinstance(complexity, int):
        data['complexity'] = str(complexity)
    
    # Fix favorites being stores as meta data instead of preferences
    if 'favorite' in data.keys():
        del data['favorite']
    
    # Fix engine being saved as a string (enum) instead of list of strings (enum flag)
    engine = data.get('engine', None)
    if isinstance(engine, str):
        if engine == 'A':
            data['engine'] = [x() for x in MetaEngine.all()]
        else:
            data['engine'] = [engine]

    
    gn_type = data['gn_type']
    if isinstance(gn_type, str):
        data['gn_type'] = [GeometryNodeAssetType.ADD_NEW()]
    

    # remove invalid meta keys, run at end of method
    invalid_keys = [k for k in data.keys() if not k in SanctusMetaData.keys()]
    for k in invalid_keys:
        del data[k]


def validate_meta_data(meta: SanctusMetaData):
    failed_components: list[str] = []

    if not meta.complexity in (x.real_id for x in MetaComplexity):
        meta.set_complexity(MetaComplexity._0)
        failed_components.append('complexity')

    if not all(gnt in (e.real_id for e in GeometryNodeAssetType) for gnt in meta.gn_type):
        meta.set_gn_type(GeometryNodeAssetType.ADD_NEW)
        failed_components.append("gn type")
    if not all(eng in (e.real_id for e in MetaEngine) for eng in meta.engine):
        meta.engine = [x.real_id for x in MetaEngine]
        failed_components.append("engine")

    return failed_components
    