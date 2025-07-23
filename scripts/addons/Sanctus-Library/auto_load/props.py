import bpy
import sys
import typing
import enum
import os
import numpy as np

from pathlib import Path
from datetime import datetime

import bpy.types as bt
import bpy.props as bp

from . import utils
from . import enums
from . import ui

BLENDER_PROP_PREFIX = 'bpe_prop_'

T = typing.TypeVar('T')
PropType = typing.TypeVar('PropType')
ParentType = typing.TypeVar('ParentType')

PropUpdateFunction = typing.Callable[[typing.Any, bt.Context], None]
PropGetFunction = typing.Callable[[typing.Any], T]
PropSetFunction = typing.Callable[[typing.Any, T], None]
StringSearchFunction = typing.Callable[
    [typing.Any, bt.Context, str],
    typing.Iterable[typing.Union[
        str,
        tuple[str, str]
    ]]]
PointerPollFunction = typing.Callable[[typing.Any, T], bool]

TupleVector = tuple[typing.Union[T, 'TupleVector[T]']]
ListVector = tuple[typing.Union[T, 'ListVector[T]']]


class InvalidPropertyError(ValueError):
    ...


class Property(typing.Generic[PropType]):
    
    @property
    def ui_name(self):
        if self.has_parameter('name'):
            return self.get_parameter('name')
        return self.attr_name

    def __init__(self, deferred_property) -> None:
        self.deferred_property = deferred_property
        self.obj = None

    def _is_valid(self):
        return self.obj is not None

    def __repr__(self) -> str:
        if self._is_valid():
            return repr(self.obj) + '.' + self.attr_name
        else:
            return super().__repr__() + ' [INVALID!]'

    def __str__(self) -> str:
        return f'{self.__class__.__name__}["{self.attr_name}"] = {self.value if self._is_valid() else "..."}'

    def __set_name__(self, owner: typing.Type, name: str):
        self.set_context(owner, name)

    def set_context(self, owner: typing.Type, name: str):
        self.owner_cls = owner
        self.attr_name = name
        self.data_attr = f'{BLENDER_PROP_PREFIX}{self.attr_name}'

    def annotate(self, cls=None) -> None:
        if cls is None:
            cls = self.owner_cls
        annotations = cls.__annotations__
        prop_definition = self.deferred_property
        prop_definition.keywords['attr'] = self.data_attr
        annotations[self.data_attr] = prop_definition
        cls.__annotations__ = annotations

    def __get__(self, obj, objtype=None):
        import copy
        c = copy.copy(self)
        c.obj = obj
        return c

    def has_parameter(self, key: str):
        return key in self.deferred_property.keywords

    def get_parameter(self, key: str):
        return self.deferred_property.keywords[key]
    
    def check_option(self, flag: enums.BPropertyFlag):
        return flag() in self.get_parameter('options')

    def set_parameter(self, key: str, value: typing.Any):
        self.deferred_property.keywords[key] = value

    def get_property_default(self):
        return self.get_parameter('default')

    def ensure_default(self) -> None:
        setattr(self.obj, self.data_attr, self.get_property_default())

    def get_value(self) -> PropType:
        return getattr(self.obj, self.data_attr)

    def set_value(self, value: PropType) -> None:
        setattr(self.obj, self.data_attr, value)

    @property
    def value(self):
        return self.get_value()

    @value.setter
    def value(self, value: PropType) -> None:
        self.set_value(value)

    def __call__(self):
        return self.get_value()

    def get_from(self, obj, attr_name: str = ''):
        if attr_name == '':
            attr_name = self.attr_name
        return getattr(obj, attr_name)

    def __set__(self, obj, value) -> None:
        raise ValueError(f'Property {self.attr_name} is readonly. To set the property value, access the "value" field from this object')

    def set_to(self, obj, value, attr_name: str = ''):
        if attr_name == '':
            attr_name = self.attr_name
        setattr(obj, attr_name, value)

    @classmethod
    def get_property_descriptors(cls, clss: typing.Type, recursive: bool = False):
        result = {}
        if recursive:
            for superclass in (x for x in clss.mro()):
                result.update(cls.get_property_descriptors(superclass, recursive=False))
        result.update(**{k: v for k, v in clss.__dict__.items() if isinstance(v, Property)})
        return result

    @classmethod
    def get_standard_property_descriptors(cls, clss: typing.Type):
        return {k: v for k, v in clss.__dict__.items() if isinstance(v, StandardProperty)}

    @classmethod
    def get_property_descriptor_groups(cls, clss: typing.Type) -> tuple[dict[str, 'ContextProperty'], dict[str, 'Property']]:
        '''returns dictionaries with context and manual meta props'''
        items = cls.get_property_descriptors(clss, recursive=True).items()
        context_props = {k: v for k, v in items if isinstance(v, ContextProperty)}
        manual_props = {k: v for k, v in items if not isinstance(v, ContextProperty)}
        return context_props, manual_props


class StandardProperty(Property[PropType]):
    prop_func = None

    def __init__(self, **kwargs) -> None:
        discard_keys: list[str] = []
        for k, v in kwargs.items():
            if k == 'default':
                continue
            if v in [None, '']:
                discard_keys.append(k)
        [kwargs.pop(k, None) for k in discard_keys]

        super().__init__(self.prop_func(**kwargs))

    def draw_ui(self, layout: bt.UILayout, options: ui.UIOptionsProp = ui.UIOptions()) -> bt.UILayout:
        if not self._is_valid():
            raise InvalidPropertyError(f'Property Access is incorrect')
        ui.UI.prop(layout, self.obj, self.data_attr, options)
        return layout

    def serialize(self) -> PropType:
        return self.get_value()

    def deserialize(self, data: PropType, **_) -> None:
        self.set_value(data)

    @classmethod
    def get(cls, obj, attr_name: typing.Union[str, None] = None):
        if attr_name is not None:
            result = getattr(obj, attr_name)
            if not isinstance(result, cls):
                raise AttributeError(f'Attribute of name "{attr_name}" in {obj} is not a property of type {cls}')
            return result

        d = {}
        for clss in type(obj).mro():
            d.update(**clss.__dict__)

        attr_name = next(x.attr_name for x in d.values() if isinstance(x, cls))
        descriptor = getattr(obj, attr_name)
        if not isinstance(descriptor, cls):
            raise Exception(f'Impossible State')
        return descriptor


class StandardVectorProperty(StandardProperty[TupleVector[PropType]]):

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.size = self.deferred_property.keywords['size']

    @classmethod
    def check_shape(cls, vector: TupleVector[PropType], size: utils.TypeSequence[PropType]) -> bool:
        if isinstance(size, int):
            size = (size,)
        else:
            size = tuple(size)
        t_vec = cls.to_tuple(vector)
        a = np.array(t_vec)
        return a.shape == size

    @classmethod
    def validate(cls, vector: TupleVector[PropType], size: utils.TypeSequence[PropType], type: typing.Type = float):
        if cls.check_shape(vector, size):
            return vector
        return cls.to_tuple(np.zeros(size, dtype=type))

    @classmethod
    def to_tuple(cls, vector) -> TupleVector[PropType]:
        def conv(data): return tuple((conv(x) for x in data)) if hasattr(data, '__iter__') else data
        return conv(vector)

    @classmethod
    def to_list(cls, vector) -> ListVector[PropType]:
        def conv(data): return list((conv(x) for x in data)) if hasattr(data, '__iter__') else data
        return conv(vector)

    def serialize(self, as_list: bool = True) -> TupleVector[PropType]:
        v = super().serialize()
        if as_list:
            return self.to_list(v)
        else:
            return self.to_tuple(v)

    def as_array(self):
        return np.array(self.serialize())

    def deserialize(self, data: PropType, **_) -> None:
        return super().deserialize(data, **_)

    def __getattribute__(self, key: str):
        old_get = super().__getattribute__
        swizzle_indices = utils.swizzle_to_indices(key)
        if len(swizzle_indices) == 0:
            return old_get(key)
        vec = old_get('serialize')()
        return tuple([vec[x] for x in swizzle_indices])
    
    def set_value_at(self, index: int, value: PropType):
        vector = self.get_value()
        vector[index] = value
        self.set_value(vector)

class BoolProperty(StandardProperty[bool]):
    prop_func = bp.BoolProperty

    def __init__(
        self,
        name: str = '',
        description: str = '',
        default: bool = False,
        options: set[enums.BPropertyFlag] = enums.BPropertyFlag.ANIMATABLE,
        override: set[enums.BPropertyOverrideFlag] = None,
        tags: set[str] = None,
        subtype: enums.BPropertySubtypeNumber = enums.BPropertySubtypeNumber.NONE,
        update: PropUpdateFunction = None,
        get: PropGetFunction[bool] = None,
        set: PropSetFunction[bool] = None
    ) -> None:
        super().__init__(
            name=name,
            description=description,
            default=default,
            options=enums.FlagEnum.unpack(options, force_flag=True),
            override=enums.FlagEnum.unpack(override, force_flag=True),
            tags=tags,
            subtype=subtype(),
            update=update,
            get=get,
            set=set
        )
    
    def draw_as_dropdown(self, layout: bt.UILayout, text_expanded: str = '', text_collapsed: str = '', invert_value: bool=False):
        return ui.UI.prop_bool_dropdown(layout, self.obj, self.data_attr, text_expanded=text_expanded, text_collapsed=text_collapsed, invert_value=invert_value)
    
    def draw_as_switch(self, layout: bt.UILayout, text_true: str, text_false: str, hide_highlighting: bool=True):
        return ui.UI.prop_bool_switch(layout, self.obj, self.data_attr, text_true, text_false, hide_highlighting)
    
    def draw_as_icon_switch(self, layout: bt.UILayout, icon_true: ui.IconParam, icon_false: ui.IconParam, hide_highlighting: bool=True, invert_value: bool=False):
        return ui.UI.prop_bool_icon_switch(layout, self.obj, self.data_attr, icon_true, icon_false, hide_highlighting, invert_value)


class BoolVectorProperty(StandardVectorProperty[bool]):
    prop_func = bp.BoolVectorProperty

    def __init__(
        self,
        name: str = '',
        description: str = '',
        default: TupleVector[bool] = (False, False, False),
        options: set[enums.BPropertyFlag] = enums.BPropertyFlag.ANIMATABLE,
        override: set[enums.BPropertyOverrideFlag] = None,
        tags: set[str] = None,
        subtype: enums.BPropertySubtypeNumberArray = enums.BPropertySubtypeNumberArray.NONE,
        size: utils.TypeSequence[int] = 3,
        update: PropUpdateFunction = None,
        get: PropGetFunction[TupleVector[bool]] = None,
        set: PropSetFunction[TupleVector[bool]] = None
    ) -> None:
        super().__init__(
            name=name,
            description=description,
            default=self.validate(default, size, type=bool),
            options=enums.FlagEnum.unpack(options, force_flag=True),
            override=enums.FlagEnum.unpack(override, force_flag=True),
            tags=tags,
            subtype=subtype(),
            size=size,
            update=update,
            get=get,
            set=set
        )


class FloatProperty(StandardProperty[float]):
    prop_func = bp.FloatProperty

    def __init__(
        self,
        name: str = '',
        description: str = '',
        default: float = 0.0,
        min: float = -3.402823e+38,
        max: float = 3.402823e+38,
        soft_min: float = -3.402823e+38,
        soft_max: float = 3.402823e+38,
        step: int = 3,
        precision: int = 2,
        options: set[enums.BPropertyFlag] = enums.BPropertyFlag.ANIMATABLE,
        override: set[enums.BPropertyOverrideFlag] = None,
        tags: set[str] = None,
        subtype: enums.BPropertySubtypeNumber = enums.BPropertySubtypeNumber.NONE,
        unit: enums.BPropertyUnit = enums.BPropertyUnit.NONE,
        update: PropUpdateFunction = None,
        get: PropGetFunction[float] = None,
        set: PropSetFunction[float] = None
    ) -> None:
        super().__init__(
            name=name,
            description=description,
            default=default,
            min=min,
            max=max,
            soft_min=soft_min,
            soft_max=soft_max,
            step=step,
            precision=precision,
            options=enums.FlagEnum.unpack(options, force_flag=True),
            override=enums.FlagEnum.unpack(override, force_flag=True),
            tags=tags,
            subtype=subtype(),
            unit=unit(),
            update=update,
            get=get,
            set=set
        )


class FloatVectorProperty(StandardVectorProperty[float]):
    prop_func = bp.FloatVectorProperty

    def __init__(
        self,
        name: str = '',
        description: str = '',
        default: TupleVector[float] = (0.0, 0.0, 0.0),
        min: float = sys.float_info.min,
        max: float = sys.float_info.max,
        soft_min: float = sys.float_info.min,
        soft_max: float = sys.float_info.max,
        step: int = 3,
        precision: int = 2,
        options: set[enums.BPropertyFlag] = enums.BPropertyFlag.ANIMATABLE,
        override: set[enums.BPropertyOverrideFlag] = None,
        tags: set[str] = None,
        subtype: enums.BPropertySubtypeNumberArray = enums.BPropertySubtypeNumberArray.NONE,
        unit: enums.BPropertyUnit = enums.BPropertyUnit.NONE,
        size: utils.TypeSequence[int] = 3,
        update: PropUpdateFunction = None,
        get: PropGetFunction[TupleVector[float]] = None,
        set: PropSetFunction[TupleVector[float]] = None
    ) -> None:
        super().__init__(
            name=name,
            description=description,
            default=self.validate(default, size, type=float),
            min=min,
            max=max,
            soft_min=soft_min,
            soft_max=soft_max,
            step=step,
            precision=precision,
            options=enums.FlagEnum.unpack(options, force_flag=True),
            override=enums.FlagEnum.unpack(override, force_flag=True),
            tags=tags,
            subtype=subtype(),
            unit=unit(),
            size=size,
            update=update,
            get=get,
            set=set
        )


class IntProperty(StandardProperty[int]):
    prop_func = bp.IntProperty

    def __init__(
        self,
        name: str = '',
        description: str = '',
        default: int = False,
        min: int = -2**31,
        max: int = 2**31 - 1,
        soft_min: int = -2**31,
        soft_max: int = 2**31 - 1,
        step: int = 1,
        options: set[enums.BPropertyFlag] = enums.BPropertyFlag.ANIMATABLE,
        override: set[enums.BPropertyOverrideFlag] = None,
        tags: set[str] = None,
        subtype: enums.BPropertySubtypeNumber = enums.BPropertySubtypeNumber.NONE,
        update: PropUpdateFunction = None,
        get: PropGetFunction[int] = None,
        set: PropSetFunction[int] = None
    ) -> None:
        super().__init__(
            name=name,
            description=description,
            default=default,
            min=min,
            max=max,
            soft_min=soft_min,
            soft_max=soft_max,
            step=step,
            options=enums.FlagEnum.unpack(options, force_flag=True),
            override=enums.FlagEnum.unpack(override, force_flag=True),
            tags=tags,
            subtype=subtype(),
            update=update,
            get=get,
            set=set
        )


class IntVectorProperty(StandardVectorProperty[TupleVector[int]]):
    prop_func = bp.IntVectorProperty

    def __init__(
        self,
        name: str = '',
        description: str = '',
        default: TupleVector[int] = (0, 0, 0),
        min: int = -2**31,
        max: int = 2**31 - 1,
        soft_min: int = -2**31,
        soft_max: int = 2**31 - 1,
        step: int = 1,
        options: set[enums.BPropertyFlag] = enums.BPropertyFlag.ANIMATABLE,
        override: set[enums.BPropertyOverrideFlag] = None,
        tags: set[str] = None,
        subtype: enums.BPropertySubtypeNumberArray = enums.BPropertySubtypeNumberArray.NONE,
        size: utils.TypeSequence[int] = 3,
        update: PropUpdateFunction = None,
        get: PropGetFunction[TupleVector[int]] = None,
        set: PropSetFunction[TupleVector[int]] = None
    ) -> None:
        super().__init__(
            name=name,
            description=description,
            default=self.validate(default, size, type=int),
            min=min,
            max=max,
            soft_min=soft_min,
            soft_max=soft_max,
            step=step,
            options=enums.FlagEnum.unpack(options, force_flag=True),
            override=enums.FlagEnum.unpack(override, force_flag=True),
            tags=tags,
            subtype=subtype(),
            size=size,
            update=update,
            get=get,
            set=set
        )


class StringProperty(StandardProperty[str]):
    prop_func = bp.StringProperty

    def __init__(
        self,
        name: str = '',
        description: str = '',
        default: str = '',
        maxlen: int = 0,
        options: set[enums.BPropertyFlag] = enums.BPropertyFlag.ANIMATABLE,
        override: set[enums.BPropertyOverrideFlag] = None,
        tags: set[str] = None,
        subtype: enums.BPropertySubtypeString = enums.BPropertySubtypeString.NONE,
        update: PropUpdateFunction = None,
        get: PropGetFunction[str] = None,
        set: PropSetFunction[str] = None,
        search: StringSearchFunction = None,
        search_options: set[enums.BPropertyStringSearchFlag] = enums.BPropertyStringSearchFlag.SUGGESTION,
    ) -> None:
        args=dict(
            name=name,
            description=description,
            default=default,
            maxlen=maxlen,
            options=enums.FlagEnum.unpack(options, force_flag=True),
            override=enums.FlagEnum.unpack(override, force_flag=True),
            tags=tags,
            subtype=subtype(),
            update=update,
            get=get,
            set=set,
            search=search,
            search_options=enums.FlagEnum.unpack(search_options, force_flag=True),
        )
        if bpy.app.version < (3,3,0):
            args.pop('search_options', None)
        super().__init__(**args)



class JSONDataProperty(StandardProperty[utils.JSONSerializable]):
    prop_func = bp.StringProperty

    def __init__(
        self,
        name: str = '',
        description: str = '',
        default: utils.JSONSerializable = {'hello': 'World'},
        options: set[enums.BPropertyFlag] = {enums.BPropertyFlag.ANIMATABLE, enums.BPropertyFlag.HIDDEN},
        override: set[enums.BPropertyOverrideFlag] = None,
        tags: set[str] = None,
        update: PropUpdateFunction = None,
        get: PropGetFunction[str] = None,
        set: PropSetFunction[str] = None,
    ) -> None:
        args=dict(
            name=name,
            description=description,
            default=self.deserialize_value(default),
            maxlen=0,
            options=enums.FlagEnum.unpack(options, force_flag=True),
            override=enums.FlagEnum.unpack(override, force_flag=True),
            tags=tags,
            subtype=enums.BPropertySubtypeString.NONE(),
            update=update,
            get=get,
            set=set,
        )
        super().__init__(**args)

    def get_value(self) -> utils.JSONSerializable:
        return self.serialize_value(super().get_value())
    
    def set_value(self, value: utils.JSONSerializable) -> None:
        super().set_value(self.deserialize_value(value))

    def serialize(self) -> utils.JSONSerializable:
        return self.get_value()
    
    def deserialize(self, data: utils.JSONSerializable, **_) -> None:
        self.set_value(data)

    @classmethod
    def deserialize_value(self, value: utils.JSONSerializable) -> str:
        import json
        return json.dumps(value)
    
    @classmethod
    def serialize_value(self, value: str) -> utils.JSONSerializable:
        import json
        return json.loads(value)
    
    def __getitem__(self, key: str):
        data = self.get_value()
        return data[key]
    
    def __setitem__(self, key: str, item: utils.JSONSerializable):
        data = self.get_value()
        data[key] = item
        self.set_value(data)

    def __delitem__(self, key: str):
        data = self.get_value()
        del data[key]
        self.set_value(data)

    def get(self, key: str, default=None):
        data = self.get_value()
        return data.get(key, default)
    
    def has_key(self, key: str):
        return key in self.get_value().keys()
    
    def clear(self):
        self.set_value({})

class PointerProperty(StandardProperty[PropType]):
    prop_func = bp.PointerProperty

    def __init__(
        self,
        type: typing.Type[PropType],
        name: str = '',
        description: str = '',
        options: set[enums.BPropertyFlag] = enums.BPropertyFlag.ANIMATABLE,
        override: set[enums.BPropertyOverrideFlag] = None,
        tags: set[str] = None,
        poll: PointerPollFunction = None,
        update: PropUpdateFunction = None,
    ) -> None:
        super().__init__(
            type=type,
            name=name,
            description=description,
            options=enums.FlagEnum.unpack(options, force_flag=True),
            override=enums.FlagEnum.unpack(override, force_flag=True),
            tags=tags,
            poll=poll,
            update=update,
        )

    def set_poll(self, poll: PointerPollFunction[T]) -> None:
        self.deferred_property.keywords['poll'] = poll

    def serialize(self):
        v = self.value
        if isinstance(v, AnnotatedObject):
            return v.serialize()
        return repr(self.value)

    def deserialize(self, data: typing.Union[str, dict[str, utils.JSONSerializable]], assignment_attempts=0, print_debug: bool=True) -> None:
        v = self.value
        if isinstance(v, AnnotatedObject):
            v.deserialize(data, assignment_attempts=assignment_attempts, print_debug=print_debug)
        else:
            self.value = eval(data)

Self = typing.TypeVar('Self', bound='CollectionProperty')
NewElementFunction = typing.Callable[[Self, bt.Context, bt.Event], None]
RemoveElementFunction = typing.Callable[[Self, typing.Any, bt.Context, bt.Event], None]

class CollectionProperty(PointerProperty[typing.Iterable[PropType]]):
    prop_func = bp.CollectionProperty

    def __init__(
        self: Self,
        type: utils.PropertyGroupType[PropType] = None,
        name: str = '',
        description: str = '',
        options: set[enums.BPropertyFlag] = enums.BPropertyFlag.ANIMATABLE,
        override: set[enums.BPropertyOverrideFlagCollection] = None,
        tags: set[str] = None,
        new: NewElementFunction = None,
        remove: NewElementFunction = None
    ) -> None:
        super().__init__(
            type=type,
            name=name,
            description=description,
            options=enums.FlagEnum.unpack(options, force_flag=True),
            override=enums.FlagEnum.unpack(override, force_flag=True),
            tags=tags,
        )
        self.elememt_type = type
        if new is not None:
            self.new_from_operator = new
        if remove is not None:
            self.remove_from_operator = remove

    def draw_ui(self, layout: bt.UILayout, box: int = 0, style: enums.BLayoutStyle = enums.BLayoutStyle.VERTICAL, options: ui.UIOptions = ui.UIOptions()) -> bt.UILayout:
        if box > 0:
            layout = layout.box()
        layout = ui.UI.create_layout_style(style, layout, options=options)
        for e in self.value:
            if isinstance(e, PropertyGroup):
                e.draw_ui(layout, box=box == 2, options=options)
        return layout
    
    @classmethod
    def draw_list_item(cls, layout: bt.UILayout, collection_prop: Self, item: PropType):
        layout.label(text=repr(item))

    @classmethod
    def filter_list(cls, collection_prop: Self, uilist: bt.UIList):
        return bt.UI_UL_list.filter_items_by_name(uilist.filter_name, uilist.bitflag_filter_item, collection_prop(), 'name', reverse=False)
    
    @classmethod
    def sort_list(cls, collection_prop: Self, uilist: bt.UIList):
        ordered = []
        if uilist.use_filter_sort_alpha:
            ordered = bt.UI_UL_list.sort_items_by_name(collection_prop(), 'name')
        return ordered

    @classmethod
    def draw_list_filters(cls, collection_prop: Self, layout: bt.UILayout, context: bt.UILayout, uilist: bt.UIList):
        layout = ui.UI.row(layout)
        left_row = ui.UI.row(layout, align=True)
        ui.UI.prop(left_row, uilist, 'filter_name', ui.UIOptionsProp(text=''))
        ui.UI.prop(left_row, uilist, 'use_filter_invert', ui.UIIcon(enums.BIcon.ARROW_LEFTRIGHT))
        right_row = ui.UI.row(layout, align=True)
        ui.UI.prop(right_row, uilist, 'use_filter_sort_alpha', ui.UIIcon(enums.BIcon.SORTALPHA))
        ui.UI.prop(right_row, uilist, 'use_filter_sort_reverse', ui.UIIcon(enums.BIcon.SORT_DESC if uilist.use_filter_sort_reverse else enums.BIcon.SORT_ASC))

    def draw_list(self, layout: bt.UILayout, active_item_prop: IntProperty, type: str ='DEFAULT', columns: int = 9):
        from . import property_ui
        prop_hash = str(hash(str(self.obj) + self.attr_name))
        property_ui.LIST_USERS_MAP[prop_hash] = self
        layout.template_list(property_ui.GenericUIList.bl_idname, prop_hash, self.obj, self.data_attr, self.obj, active_item_prop.data_attr, type=type, columns=columns)

    @staticmethod
    def on_add_element(self, element: PropType):
        pass

    @staticmethod
    def on_remove_element(self, element: PropType):
        pass

    def new(self) -> PropType:
        e = self.value.add()
        self.on_add_element(self, e)
        return e

    def contains(self, element: PropType) -> bool:
        return any(x == element for x in self.value)

    def index(self, element: PropType) -> int:
        if not isinstance(element, self.elememt_type):
            raise ValueError(f'Invalid type "{type(element)}". Collection contains objects of type "{self.elememt_type}"')
        return next(i for i, e in enumerate(self.value) if e == element)

    def remove(self, element: PropType) -> None:
        self.remove_at(self.index(element))
    
    def remove_at(self, index: int) -> None:
        e = self.value[index]
        self.on_remove_element(self, e)
        self.value.remove(index)

    def clear(self):
        for i in range(len(self.value)):
            self.remove_at(len(self.value) - 1)
        self.value.clear()

    def serialize(self) -> list:
        result = []
        for e in self.value:
            e: PropertyGroup
            result.append(e.serialize())
        return result

    def deserialize(self, data: list, assignment_attempts: int = 3, print_debug: bool = True) -> None:
        self.clear()
        for d in data:
            e: PropertyGroup = self.new()
            e.deserialize(d, assignment_attempts=assignment_attempts, print_debug=print_debug)

    def get_add_element(self, description: str = ''):
        from . import property_operators as po
        return po.AddCollectionElement(
            parent=self.obj, 
            property_attr=self.attr_name, 
            description_text=description,
        )

    def get_remove_element(self, element: PropType, description: str = ''):
        from . import property_operators as po
        return po.RemoveCollectionElement(
            parent=self.obj, 
            property_attr=self.attr_name, 
            description_text=description,
            element=element,
        )
    
    @staticmethod
    def new_from_operator(self: Self, context: bt.Context, event: bt.Event):
        self.new()
    
    @staticmethod
    def remove_from_operator(self: Self, element: PropType, context: bt.Context, event: bt.Event):
        self.remove(element)


BStaticEnumType = typing.TypeVar('BStaticEnumType', bound='enums.BStaticEnum')
EnumType = typing.TypeVar('EnumType', bound='enum.Enum')

BStaticEnumInput = typing.Union[str, int, BStaticEnumType]

class EnumProperty(StandardProperty[BStaticEnumType]):
    prop_func = bp.EnumProperty

    def __init__(
        self,
        enum: typing.Type[BStaticEnumType],
        name: str = '',
        description: str = '',
        default: typing.Union[enums.BStaticEnum, int] = 0,
        options: set[enums.BPropertyFlagEnum] = enums.BPropertyFlagEnum.ANIMATABLE,
        override: set[enums.BPropertyOverrideFlag] = None,
        tags: set[str] = None,
        update: PropUpdateFunction = None,
        get: PropGetFunction = None,
        set: PropSetFunction = None,
    ) -> None:
        
        self.enum_cls = enum
        resolved_options = enums.FlagEnum.unpack(options, force_flag=True)
        is_flag = enums.BPropertyFlagEnum.ENUM_FLAG()
        if is_flag in resolved_options:
            resolved_options.remove(is_flag)
        self.use_flags = False

        if isinstance(default, int):
            default = enum.from_int(default)

        super().__init__(
            items=enum.static_enum_items(),
            name=name,
            description=description,
            default=default(),
            options=resolved_options,
            override=enums.FlagEnum.unpack(override, force_flag=True),
            tags=tags,
            update=update,
            get=get,
            set=set,
        )
        

    def get_value(self) -> BStaticEnumType:
        v = super().get_value()
        return self.enum_cls.parse(v)

    def set_value(self, value: typing.Union[str, BStaticEnumType]) -> None:
        value = self.enum_cls.interpret_input(value)
        value = enums.FlagEnum.unpack(value)
        super().set_value(value)

    def serialize(self):
        return self.get_value()()

    def deserialize(self, data: str, **_) -> None:
        self.set_value(self.enum_cls.from_string(data))

class EnumFlagProperty(StandardProperty[set[BStaticEnumType]]):
    prop_func = bp.EnumProperty

    def __init__(
        self,
        enum: typing.Type[BStaticEnumType],
        name: str = '',
        description: str = '',
        default: set[typing.Union[enums.BStaticEnum, int]] = {0},
        options: set[enums.BPropertyFlagEnum] = {enums.BPropertyFlagEnum.ANIMATABLE},
        override: set[enums.BPropertyOverrideFlag] = None,
        tags: set[str] = None,
        update: PropUpdateFunction = None,
        get: PropGetFunction = None,
        set: PropSetFunction = None,
    ) -> None:
        
        self.enum_cls = enum
        resolved_options = enums.FlagEnum.unpack(options, force_flag=True)
        resolved_options.add(enums.BPropertyFlagEnum.ENUM_FLAG())
        self.use_flags = True

        new_default = {enum.from_int(x) if isinstance(x, int) else x for x in default}

        super().__init__(
            items=enum.static_enum_items_minimal(),
            name=name,
            description=description,
            default={x() for x in new_default},
            options=resolved_options,
            override=enums.FlagEnum.unpack(override, force_flag=True),
            tags=tags,
            update=update,
            get=get,
            set=set,
        )
        

    def get_value(self) -> BStaticEnumType:
        v = super().get_value()
        return self.enum_cls.parse(v)

    def set_value(self, value: typing.Union[str, BStaticEnumType]) -> None:
        value = self.enum_cls.interpret_input(value)
        value = enums.FlagEnum.unpack(value)
        super().set_value(value)

    def serialize(self):
        if self.use_flags:
            return [x() for x in self.get_value()]
        return self.get_value()()

    def deserialize(self, data: set[str], **_) -> None:
        self.set_value({self.enum_cls.from_string(x) for x in data})
        
    def draw_ui(self, layout: bt.UILayout, options: ui.UIOptionsProp = ui.UIOptions()) -> bt.UILayout:
        text = options.get('text', default=self.ui_name)
        if text != '' and not layout.use_property_split:
            layout = ui.UI.row(layout, align=True)
            ui.UI.label(layout, text + ':')
        if options.has_option('text'):
            options.remove_option('text')
        return super().draw_ui(layout, options)

class DynamicEnumProperty(StandardProperty[str]):
    '''Dynamic Version of the Enum Property. Use "fixed = true" to immediately resolve the items using (None, None) as parameters'''
    prop_func = bp.EnumProperty

    def __init__(
        self,
        items: enums.BEnumItemGenerator,
        name: str = '',
        description: str = '',
        default: int = 0,
        options: set[enums.BPropertyFlagEnum] = {enums.BPropertyFlagEnum.ANIMATABLE},
        override: set[enums.BPropertyOverrideFlag] = None,
        tags: set[str] = None,
        update: PropUpdateFunction = None,
        get: PropGetFunction = None,
        set: PropSetFunction = None,
        fixed: bool = False
    ) -> None:
        super().__init__(
            items=items(None, None) if fixed else items,
            name=name,
            description=description,
            default=default,
            options=enums.FlagEnum.unpack(options, force_flag=True),
            override=enums.FlagEnum.unpack(override, force_flag=True),
            tags=tags,
            update=update,
            get=get,
            set=set,
        )
        self.items = items


class PathProperty(StandardProperty[str]):
    prop_func = bp.StringProperty

    def __init__(
        self,
        name: str = '',
        description: str = '',
        default: str = '//',
        options: set[enums.BPropertyFlag] = enums.BPropertyFlag.ANIMATABLE,
        override: set[enums.BPropertyOverrideFlag] = None,
        tags: set[str] = None,
        subtype: enums.BPropertySubtypeString = enums.BPropertySubtypeString.FILE_PATH,
        update: PropUpdateFunction = None,
        get: PropGetFunction = None,
        set: PropSetFunction = None,
        fallback: enums.BPathFallbackType = enums.BPathFallbackType.NONE
    ):
        super().__init__(
            name=name,
            description=description,
            default=default,
            options=enums.FlagEnum.unpack(options, force_flag=True),
            override=enums.FlagEnum.unpack(override, force_flag=True),
            tags=tags,
            subtype=subtype(),
            update=update,
            get=get,
            set=set
        )
        self.fallback = fallback

    def get_value(self) -> str:
        return super().get_value()

    def set_value(self, value: str) -> None:
        return super().set_value(value)

    @property
    def raw(self):
        return Path(self.value)
    
    @raw.setter
    def raw(self, value: Path):
        self.set_value(str(value))

    @property
    def is_relative(self):
        return self.value.startswith('//')

    @property
    def relative_component(self):
        return self.value.removeprefix('//')

    @property
    def absolute(self):
        if not self.is_relative or not hasattr(bpy.data, "is_saved"):
            return self.raw

        relative_path = self.relative_component
        if self.fallback == enums.BPathFallbackType.NONE:
            if bpy.data.is_saved:
                p = Path(os.path.normpath(bpy.path.abspath(self.value)))
                return p
            else:
                raise OSError('Relative Path cannot be resolved. Blend File has to be saved or use another fallback type')

        root = self.fallback.get_root()
        absolute = root.joinpath(relative_path)
        return Path(os.path.normpath(str(absolute)))

    def to_absolute(self, root: Path, root_optional: bool = False):
        if not self.is_relative:
            if not root_optional:
                raise OSError(f'Cannot make already absolute path absolute. Path property must be relative.')
            return self.absolute
        return root.joinpath(self.relative_component)


class SwitchCollectionProperty(typing.Generic[EnumType], StandardVectorProperty[bool]):
    prop_func = bp.BoolVectorProperty

    def __init__(
        self,
        flag: typing.Type[EnumType],
        name: str = '',
        description: str = '',
        default: tuple[bool, ...] = tuple(),
        options: set[enums.BPropertyFlag] = enums.BPropertyFlag.ANIMATABLE,
        override: set[enums.BPropertyOverrideFlag] = None,
        tags: set[str] = None,
        update: PropUpdateFunction = None,
        get: PropGetFunction[TupleVector[bool]] = None,
        set: PropSetFunction[TupleVector[bool]] = None
    ) -> None:

        enum_members: list[enum.Enum] = [x for x in flag]
        size = len(enum_members)
        if len(default) != size or any(not isinstance(x, bool) for x in default):
            default = [(x.value if isinstance(x.value, bool) else False) for x in enum_members]
        super().__init__(
            name=name,
            description=description,
            default=default,
            options=enums.FlagEnum.unpack(options, force_flag=True),
            override=enums.FlagEnum.unpack(override, force_flag=True),
            tags=tags,
            subtype=enums.BPropertySubtypeNumberArray.NONE(),
            size=size,
            update=update,
            get=get,
            set=set
        )
        self.enum_cls = flag

    def identifier_to_index(self, identifier: EnumType):
        try:
            return next(i for i, e in enumerate(self.enum_cls) if e == identifier)
        except:
            raise ValueError(f'Identifier {identifier} does not match required enum type: {self.enum_cls}.')

    def draw_switch(self, layout: bt.UILayout, identifier: EnumType, options: ui.UIOptions = ui.UIOptions()):
        options.set('index', self.identifier_to_index(identifier))
        return self.draw_ui(layout, options=options)

    def draw_switch_dropdown(
        self,
        layout: bt.UILayout,
        identifier: EnumType,
        expanded_text: str = 'Expanded',
        collapsed_text: str = 'Collapsed',
        expanded_icon: typing.Union[enums.BIcon, int] = enums.BIcon.TRIA_DOWN,
        collapsed_icon: typing.Union[enums.BIcon, int] = enums.BIcon.TRIA_RIGHT
    ) -> bool:
        row = layout.row(align=True)
        v = self.get_switch(identifier)
        self.draw_switch(row, identifier, options=ui.UIOptionsProp(text='', icon=expanded_icon if v else collapsed_icon, emboss=False))
        ui.UI.label(row, expanded_text if v else collapsed_text)
        return v

    def get_switch(self, identifier: EnumType):
        return self.value[self.identifier_to_index(identifier)]

    def set_switch(self, identifier: EnumType, value: bool):
        v = list(self.value)
        v[self.identifier_to_index(identifier)] = value
        self.value = v
    
    def draw_switches(self, layout: bt.UILayout, options: ui.UIOptions = ui.UIOptions()):
        for i in self.enum_cls:
            io = options.copy()
            if(isinstance(i, enums.BStaticEnum)):
                io.default('text', i.get_name())
            else:
                io.default('text', i.name)
            self.draw_switch(layout, i, io)
    
class DateProperty(StringProperty):
    
    def __init__(
            self, 
            name: str = '', 
            description: str = '', 
            default: datetime = None,
            options: set[enums.BPropertyFlag] = enums.BPropertyFlag.ANIMATABLE, 
            override: set[enums.BPropertyOverrideFlag] = None, 
            tags: set[str] = None,
            update: PropUpdateFunction = None, 
            get: PropGetFunction[datetime] = None, 
            set: PropSetFunction[datetime] = None,
        ) -> None:
        default = datetime.now() if default is None else default
        super().__init__(
            name, 
            description, 
            default=DateProperty.serialize_datetime(default), 
            maxlen=0, 
            options=options, 
            override=override, 
            tags=tags, 
            subtype=enums.BPropertySubtypeString.NONE, 
            update=update, 
            get=get, 
            set=set, 
            search=None,
            search_options={enums.BPropertyStringSearchFlag.SUGGESTION}
        )

    @staticmethod
    def serialize_datetime(date: datetime):
        return f'{date.year}::{date.month}::{date.day}::{date.hour}::{date.minute}::{date.second}'
    
    @staticmethod
    def deserialize_datetime(serialized_date: str):
        year, month, day, hour, minute, second = serialized_date.split('::')
        return datetime(int(year), int(month), int(day), int(hour), int(minute), int(second))

    def get_value(self) -> datetime:
        v = super().get_value()
        return DateProperty.deserialize_datetime(v)
    
    def set_value(self, value: datetime) -> None:
        super().set_value(DateProperty.serialize_datetime(value))

    def __call__(self) -> datetime:
        return self.get_value()

    @property
    def value(self) -> datetime:
        return self.get_value()
    
    @value.setter
    def value(self, value):
        self.set_value(value)

    def get_elapsed_time(self):
        now = datetime.now()
        delta = now - self.get_value()
        return delta.total_seconds()
    
    def get_elapsed_time_formatted(self) -> str:
        delta = self.get_elapsed_time()
        seconds = round(delta)
        if seconds < 1:
            return '0s'
        s = int(seconds) % 60
        minutes = seconds / 60
        m = int(minutes) % 60
        hours = minutes / 60
        h = int(hours) % 24
        days = hours / 24
        d = int(days)
        result = ''
        display_elements = 0
        if d > 0:
            result += f'{d}d'
            display_elements += 2
        if h > 0 and display_elements < 2:
            result += f'{h}h'
            display_elements += 1
        if m > 0 and display_elements < 2:
            result += f'{m}m'
            display_elements += 1
        if s > 0 and display_elements < 2:
            result += f'{s}s'
            display_elements += 1
        return result
    
    def set_to_now(self):
        self.set_value(datetime.now())

class ContextProperty(Property[PropType]):

    def __init__(self, default: typing.Callable[[bt.Context], PropType] = lambda c: None) -> None:
        self.default_getter = default
        self.obj = None
        self.context = None

    def __set_name__(self, owner: typing.Type, name: str):
        super().__set_name__(owner, name)
        self.context_key = f'autoload_context_{name}'

    def get_unique_context_key(self, uid: int):
        return f'{self.context_key}_{uid}_'

    def get_from_context(self, context: bt.Context, uid: int, error: bool = True) -> PropType:
        key = self.get_unique_context_key(uid)
        if not hasattr(context, key) and error:
            raise AttributeError(f'Context Property "{self.attr_name}" got invalid or no value. Has to be bpy.types.AnyType.')
        return getattr(context, key, self.default_getter(context))

    def annotate(self, cls=None) -> None:
        pass

    def context_init(self, context: bt.Context):
        self.context = context

    def get_property_default(self):
        return None

    def get_context_overrides(self, value: PropType, uid: int) -> dict[str, PropType]:
        return {self.get_unique_context_key(uid): value}


class ContextListProperty(ContextProperty[list[PropType]]):

    def get_from_context(self, context: bt.Context, uid: int, error: bool = True) -> list[PropType]:
        context_dir = dir(context)
        key = self.get_unique_context_key(uid)
        context_keys = [x for x in context_dir if x.startswith(key) and x.removeprefix(key).isnumeric()]
        if len(context_keys) == 0 and error:
            default = self.default_getter(context)
            return [] if default is None else default
        return [getattr(context, x) for x in context_keys]

    def get_context_overrides(self, value: list[PropType], uid: int) -> dict[str, PropType]:
        return {f'{self.get_unique_context_key(uid)}{i}': v for i, v in enumerate(value)}


class BClassMappedObject:

    prop_map: list[tuple[str, Property, typing.Type[bt.AnyType]]] = None

    @classmethod
    def get_meta_prop(cls, obj) -> Property:
        try:
            return next(p for a, p, t in cls.prop_map if isinstance(obj, t))
        except StopIteration:
            raise ValueError(f'Property {cls} not registered to {obj.__class__}. Valid registrations: {[t for a, p, t in cls.prop_map]}')

class AnnotatedObject:

    annotated_property_keys: list[str] = None

    def get_annotated_properties(self) -> dict[str, StandardProperty]:
        return {k: getattr(self, k) for k in self.annotated_property_keys}

    @classmethod
    def annotate(cls):
        annotated_superclasses = [x for x in cls.mro()[1:] if issubclass(x, AnnotatedObject)]
        for super_clss in annotated_superclasses:
            super_clss.annotate()
        cls.annotated_property_keys = []
        if len(annotated_superclasses):
            cls.annotated_property_keys += annotated_superclasses[0].annotated_property_keys
        meta_props = Property.get_standard_property_descriptors(cls)
        for k, p in meta_props.items():
            p.annotate(cls)
            cls.annotated_property_keys.append(k)

    def serialize(self) -> dict[str, utils.JSONSerializable]:
        result = {}
        for k, prop in self.get_annotated_properties().items():
            result[k] = prop.serialize()
        return result

    def deserialize(self, data: dict[str, utils.JSONSerializable], assignment_attempts: int = 3, print_debug: bool = True):
        rotisserie = list(data.keys())
        failed_assignments: dict[str, list[Exception]] = {k: [] for k in rotisserie}
        props: dict[str, StandardProperty] = {k: getattr(self, k) for k in rotisserie if hasattr(self, k)}

        while len(rotisserie) > 0:
            k = rotisserie[0]
            try:
                props[k].deserialize(data[k], assignment_attempts=assignment_attempts, print_debug=print_debug)
                rotisserie.pop(0)
                failed_assignments[k] = []
            except Exception as e:
                if len(failed_assignments[k]) > assignment_attempts:
                    rotisserie.pop(0)
                else:
                    failed_assignments[k].append(e)
                    rotisserie.append(rotisserie.pop(0))

        if not print_debug:
            return

        error_found = False
        for k, v in failed_assignments.items():
            if v == []:
                continue
            if not error_found:
                print(f'Errors were found deserializing {self}:')
            error_found = True
            print(f'{k}:')
            for error in v:
                print(error)


class PropertyWrapper(typing.Generic[T, PropType], BClassMappedObject):

    parent_obj: bt.AnyType = None
    attr_name: str = ''

    @property
    def value(self) -> PropType:
        return self.meta_prop.get_from(self.parent_obj, attr_name=self.attr_name)

    @value.setter
    def value(self, value: PropType):
        self.meta_prop.set_to(self.parent_obj, value, attr_name=self.attr_name)

    def __init__(self, obj: T, attr_name: str = None) -> None:
        self.parent_obj = obj
        self.meta_prop = self.get_meta_prop(obj)
        self.attr_name = attr_name if attr_name is not None else self.meta_prop.attr_name

# TODO - FIND ALL SUBCLASSES OF PROPERTYGROUP AND REPLACE INSTATIATION WITH .get_from
class PropertyGroup(typing.Generic[ParentType], AnnotatedObject, BClassMappedObject, bt.PropertyGroup):
    def draw_ui(self, layout: bt.UILayout, box: bool = False, style: enums.BLayoutStyle = enums.BLayoutStyle.VERTICAL, options: ui.UIOptions = ui.UIOptions()) -> bt.UILayout:
        if box:
            layout = layout.box()
        layout = ui.UI.create_layout_style(style, layout, options=options)
        for a in self.get_annotated_properties().values():
            a.draw_ui(layout, options=options)
        return layout

    @classmethod
    def get_from(cls, obj: ParentType) -> typing.Any:
        prop = cls.get_meta_prop(obj)
        return getattr(obj, prop.attr_name)


class PD:
    '''Decorators for Properties'''

    @staticmethod
    def set_new_from_operator(property: CollectionProperty):
        def f(func: NewElementFunction):
            property.new_from_operator = func
            return func
        return f
    
    @staticmethod
    def set_remove_from_operator(property: CollectionProperty):
        def f(func: RemoveElementFunction):
            property.remove_from_operator = func
            return func
        return f
    
    @staticmethod
    def set_draw_list_item(property: CollectionProperty):
        def f(func):
            property.draw_list_item = func
            return func
        return f
    
    @staticmethod
    def set_filter_list(property: CollectionProperty):
        def f(func):
            property.filter_list = func
            return func
        return f
    
    @staticmethod
    def set_sort_list(property: CollectionProperty):
        def f(func):
            property.sort_list = func
            return func
        return f
    
    @staticmethod
    def set_draw_list_filters(property: CollectionProperty):
        def f(func):
            property.draw_list_filters = func
            return func
        return f
    
    @staticmethod
    def set_on_add_element(property: CollectionProperty):
        def f(func):
            property.on_add_element = func
            return func
        return f
    
    @staticmethod
    def set_on_remove_element(property: CollectionProperty):
        def f(func):
            property.on_remove_element = func
            return func
        return f

    @staticmethod
    def update_property(prop: StandardProperty):
        def func(update_func: PropUpdateFunction):
            prop.set_parameter('update', update_func)
            return update_func
        return func

    @staticmethod
    def get_property(prop: StandardProperty):
        def func(get_func: PropGetFunction):
            prop.set_parameter('get', get_func)
            return get_func
        return func

    @staticmethod
    def set_property(prop: StandardProperty):
        def func(set_func: PropSetFunction):
            prop.set_parameter('set', set_func)
            return set_func
        return func

    @staticmethod
    def search_property(prop: StringProperty):
        def func(search_func: StringSearchFunction):
            prop.set_parameter('search', search_func)
            return search_func
        return func
