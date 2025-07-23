
import bpy.types as bt
import typing
from enum import Enum

T = typing.TypeVar('T')

Self = typing.TypeVar('Self', bound='BStaticEnum')

BEnumItem = tuple[str, str, str, str, int]
BEnumItemMin = tuple[str, str, str]
BEnumItemGenerator = typing.Callable[[T, bt.Context], list[typing.Union[BEnumItem, BEnumItemMin]]]

def _is_iterable_collection(value: typing.Any, collection_type: typing.Type[typing.Iterable], element_type: typing.Type):
    return isinstance(value, collection_type) and all(isinstance(e, element_type) for e in value)

class FlagEnum(Enum):

    @property
    def real_id(self) -> str:
        '''Returns the blender-readable string name of the enum'''
        i = self.name
        i = i.removeprefix('_')
        return i

    def __call__(self) -> str:
        '''Convert Enum into a blender-readable string'''
        return self.real_id

    def __repr__(self) -> str:
        return super().__repr__()
    
    @classmethod
    def from_string(cls: typing.Type[Self], value: str) -> Self:
        adjusted = f'_{value}' if value[0].isnumeric() else value
        if hasattr(cls, adjusted):
            return getattr(cls, adjusted)
        string_set = {x.name for x in cls}
        raise ValueError(f'Key "{value}" not in {string_set}')

    @classmethod
    def parse(cls: typing.Type[Self], value: typing.Union[str, set[str], None]) -> typing.Union[Self, set[Self]]:
        if value is None:
            return set()
        if isinstance(value, str):
            return cls.from_string(value)
        if _is_iterable_collection(value, set, str):
            return {cls.parse(x) for x in value}
        raise ValueError(f'Value {value} is invalid for parsing BStaticEnum {cls}')
    
    @classmethod
    def unpack(cls: typing.Type[Self], value: typing.Union[Self, set[Self], None], force_flag: bool = False) -> typing.Union[set[str], str]:
        if value is None:
            return set()
        if isinstance(value, FlagEnum):
            return set([value.real_id]) if force_flag else value.real_id
        if _is_iterable_collection(value, set, cls):
            return {cls.unpack(x, force_flag=False) for x in value if isinstance(x, FlagEnum)}
        return set() if force_flag else ''

    @classmethod
    def from_int(cls: typing.Type[Self], value: int):
        try:
            return next(e for i, e in enumerate(cls) if value == i)
        except StopIteration:
            raise ValueError(f'Index {value} out of bounds for enum {cls} of size {len(cls)}')

    @classmethod
    def interpret_input(cls: typing.Type[Self], value) -> typing.Union[Self, set[Self]]:
        if isinstance(value, cls):
            return value
        if _is_iterable_collection(value, set, cls):
            return value
        
        if value is None:
            return set()
        
        if isinstance(value, int):
            return cls.from_int(value)
        if _is_iterable_collection(value, set, int):
            return {cls.from_int(x) for x in value}
        
        if isinstance(value, str):
            return cls.from_string(value)
        if _is_iterable_collection(value, set, str):
            return {cls.from_string(x) for x in value}
        
        raise ValueError(f'Input {value} cannot be interpreted as BStaticEnum {cls}')
    
    def get_index(self):
        return next(i for i, x in enumerate(self.__class__) if x==self)

class BStaticEnum(FlagEnum):

    @classmethod
    def static_enum_items(cls) -> list[BEnumItem]:
        result = []
        for i, e in enumerate(cls):
            d = e.get_enum_item()
            result.append(
                (d[0], d[1], d[2], d[3], i)
            )
        return result

    @classmethod
    def static_enum_items_minimal(cls) -> list[BEnumItemMin]:
        result = []
        for e in cls:
            d = e.get_enum_item()
            result.append((d[0], d[1], d[2]))
        return result

    def get_prop(self, dict_attr: str, fallback: T) -> typing.Union[str, T]:
        v = self.value
        return v.get(dict_attr, fallback) if isinstance(v, dict) else fallback

    def get_name(self):
        return self.get_prop('n', self.name.capitalize())
    
    def get_description(self):
        return self.get_prop('d', f'Item {self.get_name()}')
    
    def get_icon(self) -> typing.Union[str, int]:
        result = self.get_prop('i', 'NONE')
        if isinstance(result, FlagEnum):
            result = result()
        return result

    def get_enum_item(self) -> BEnumItem:
        return (self.real_id, self.get_name(), self.get_description(), self.get_icon(), 0)
    
    @classmethod
    def all(cls):
        return {x for x in cls}
    

def enum_items_from_bl_rna(rna_type: typing.Type, prop_identifier: str) -> list[BEnumItemMin]:
    rna_props: dict[str, bt.EnumProperty] = rna_type.bl_rna.properties
    return [(x.identifier, x.name, x.description) for x in rna_props[prop_identifier].enum_items]