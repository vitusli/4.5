import bpy
import dataclasses
import functools
import inspect
import typing
import bpy.types as bt

from . import props
from . import enums
from . import ui

Self = typing.TypeVar('Self', bound='Operator')

def _setup_props(self: 'Operator', context: bt.Context, error: bool = True):
    for k in props.Property.get_property_descriptors(self.__class__, recursive=True).keys():
        v = getattr(self, k)
        if isinstance(v, props.ContextProperty):
            v.context_init(context)
            v.value = v.get_from_context(context, self.uid(), error=error)

def _setup_props_operator(self: 'Operator', context: bt.Context):
    if self.is_setup:
        return
    _setup_props(self, context, error=True)
    self.is_setup = True

def pre_setup_invoke(invoke_func):
    @functools.wraps(invoke_func)
    def f(self, context, event):
        _setup_props_operator(self, context)
        return invoke_func(self, context, event)
    return f

def pre_setup_execute(exec_func):
    @functools.wraps(exec_func)
    def f(self, context):
        _setup_props_operator(self, context)
        return exec_func(self, context)
    return f

def default_delegate_description(cls: 'Operator', context: bt.Context, properties: bt.OperatorProperties) -> str:
    meta_op = cls.meta_op_type.from_operator_properties(properties)
    _setup_props(meta_op, context, error=False)
    return cls.meta_op_type.description(meta_op, context)

class MetaOperator:
    ...

AssertFunction = typing.Union[
    typing.Callable[[type, bt.Context], bool],
    typing.Callable[[], bool],
    typing.Callable[[bt.Context], bool]
]

@dataclasses.dataclass
class OperatorAssert:
    '''Creates an check for polling operators. When strict is set to False, exceptions will be ignored.'''
    assert_function: AssertFunction = lambda: True
    failed_message: str = 'anonymous rquirement not met'
    strict: bool = True

    def check(self, clss, context: bt.Context) -> bool:
        args = {
            0: (),
            1: (context,),
            2: (clss, context)
        }[self.assert_function.__code__.co_argcount]
        try:
            return self.assert_function(*args)
        except Exception as e:
            if self.strict:
                raise e
            else:
                return False

    def set_strict(self, strict: bool) -> 'OperatorAssert':
        self.strict = strict
        return self

class Operator(props.AnnotatedObject, bt.Operator):

    is_setup: bool = False
    meta_op_type: typing.Type[MetaOperator] = False
    op_cls: typing.Type[Self] = None

    uid = props.StringProperty(options={enums.BPropertyFlag.HIDDEN})

    def __init__(self, **kwargs):
        props_keys = props.Property.get_property_descriptors(self.__class__, recursive=True).keys()

        context_props = []
        for k in props_keys:
            prop: props.Property = getattr(self, k)
            prop.ensure_default()
            if k in kwargs.keys():
                prop.value = kwargs[k]
                if isinstance(prop, props.ContextListProperty):
                    context_props += prop.value
                elif isinstance(prop, props.ContextProperty):
                    context_props.append(prop.value)
                
        self.uid.value = str(abs(hash(tuple(context_props))))
        
    
    def execute(self, context: bt.Context) -> set[str]:
        raise NotImplementedError()
    
    def invoke(self, context: bt.Context, event: bt.Event) -> set[str]:
        return self.execute(context)

    def modal(self, context: bt.Context, event: bt.Event) -> set[str]:
        raise NotImplementedError()
    
    def draw(self, context: bt.Context) -> None:
        ui.UI.label(self.layout, text='Not Implemented', icon=enums.BIcon.ERROR)

    def description(self, context: bt.Context) -> str:
        '''Return a dynamic description string based on operator properties and context. Context Properties are not yet set and will return their default'''
        return getattr(self, 'bl_description', '')

    @classmethod
    def get_opmod(cls):
        cat, name = cls.bl_idname.split('.', maxsplit=1)
        return getattr(getattr(bpy.ops, cat), name)

    @classmethod
    def create_meta_op(cls) -> typing.Type[MetaOperator]:
        cls_name = f'META_{cls.__name__}'

        prop_descriptors = props.Property.get_property_descriptors(cls, recursive=True)

        cls_dict = dict(
            call=cls.call,
            draw_ui=cls.draw_ui,
            get_overrides_formatted=cls.get_overrides_formatted,
            get_opmod=cls.get_opmod,
            set_operator_properties=cls.set_operator_properties,
            from_operator_properties=classmethod(cls.from_operator_properties),
            description=cls.description,
            bl_idname=cls.bl_idname,
            bl_description=cls.bl_description,
            bl_label=cls.bl_label,
            op_cls=cls,
            __init__=cls.__init__,
        )
        for k, d in prop_descriptors.items():
            cls_dict[k] = d
        for k, v in cls.__dict__.items():
            if inspect.isfunction(v):
                cls_dict.setdefault(k, v)

        meta_op_cls = type(cls_name, (MetaOperator,), cls_dict)

        #Modify existing execute and invoke to setup proprties
        for attr, func in (('execute', pre_setup_execute), ('invoke', pre_setup_invoke)):
            if hasattr(cls, attr):
                setattr(cls, attr, func(getattr(cls, attr)))
        cls.description = cls.delegate_description
        cls.is_setup = False
        cls.meta_op_type = meta_op_cls

        return meta_op_cls
    
    def get_overrides_formatted(self) -> tuple[dict[str], dict[str]]:
        cp, mp = props.Property.get_property_descriptor_groups(self.__class__)

        context_overrides = {}
        for k, v in cp.items():
            context_overrides.update(v.get_context_overrides(getattr(self, k).value, self.uid()))
        manual_overrides = {v.data_attr: getattr(self, k).value for k, v in mp.items()}
        return context_overrides, manual_overrides
    
    def call(self, context: bt.Context = None, invocation: str = 'INVOKE_DEFAULT'):

        if context is None:
            context = bpy.context

        context_overrides, manual_overrides = self.get_overrides_formatted()

        with context.temp_override(**context_overrides):
            self.get_opmod()(invocation, **manual_overrides)

    def draw_ui(self, layout: bt.UILayout, options: ui.UIOptions=ui.UIOptions()):

        context_overrides, manual_overrides = self.get_overrides_formatted()
        ui.UI.operator(
            layout, 
            self.bl_idname, 
            properties={k: getattr(self, k) for k in manual_overrides.keys()}, 
            options=options, 
            overrides=context_overrides
        )
    
    def set_operator_properties(self, properties: bt.OperatorProperties):
        _, mo = self.get_overrides_formatted()
        for k, v in mo.items():
            properties[k] = v
    
    def from_operator_properties(cls, properties: bt.OperatorProperties):
        keys: list[str] = properties.keys()
        prop_map = {k.removeprefix(props.BLENDER_PROP_PREFIX): getattr(properties, k) for k in keys}
        return cls(**prop_map)

    #Start defining actual operator things

    al_asserts: list[OperatorAssert] = []
    al_description_failed: str = ''
    al_asserts_header: str = 'Requirements failed:'
    
    def execute(self, context: bt.Context) -> set[str]:
        result = self.run(context)
        if result is None:
            return {enums.BOperatorReturn.FINISHED()}
        if isinstance(result, enums.BOperatorReturn):
            result = result()
        return result
    
    def run(self, context: bt.Context):
        pass

    @classmethod
    def get_asserts(cls, context: bt.Context) -> typing.Generator[OperatorAssert, None, None]:
        return (a for a in cls.al_asserts)

    @classmethod
    def check_asserts(cls, context: bt.Context) -> typing.Generator[str, None, None]:
        for message in (a.failed_message for a in cls.get_asserts(context) if not a.check(cls, context)):
            yield message

    @classmethod
    def poll(cls, context: bt.Context) -> bool:
        asserts = list(cls.check_asserts(context))
        cls.poll_message_set("".join("\n-" + asrt for asrt in asserts))

        return len(asserts) == 0
    
    @classmethod
    def delegate_description(cls, context: bt.Context, properties: bt.OperatorProperties) -> str:
        return default_delegate_description(cls, context, properties)
    

#FILE OPERATORS

_boolTrue = bpy.props.BoolProperty(default=True, options={'HIDDEN', 'SKIP_SAVE'})
_boolFalse = bpy.props.BoolProperty(default=False, options={'HIDDEN', 'SKIP_SAVE'})

class _FileOperator(Operator):

    filter: _boolTrue #type: ignore
    filter_image: _boolFalse #type: ignore
    filter_text: _boolFalse #type: ignore
    filter_movie: _boolFalse #type: ignore
    filter_folder: _boolTrue #type: ignore
    filter_blender: _boolFalse #type: ignore
    filter_blendid: _boolFalse #type: ignore
    filter_font: _boolFalse #type: ignore
    filter_python: _boolFalse #type: ignore
    filter_sound: _boolFalse #type: ignore
    filter_volume: _boolFalse #type: ignore
    filter_backup: _boolFalse #type: ignore

    hide_props_region: _boolFalse #type: ignore
    relative_path: _boolTrue #type: ignore
    show_multiview: _boolFalse #type: ignore
    use_multiview: _boolFalse #type: ignore
    check_existing: _boolTrue #type: ignore
    
    filter_glob: bpy.props.StringProperty(default="", options={'HIDDEN'}, maxlen=255) #type: ignore

    def invoke(self, context: bt.Context, event: bt.Event) -> set[str]:
        self.set_defaults(context, event)
        bt.WindowManager.fileselect_add(self)
        return {enums.BOperatorReturn.RUNNING_MODAL()}

    def set_defaults(self, context: bt.Context, event: bt.Event):
        return


class FilepathOperator(_FileOperator):
    filepath: bpy.props.StringProperty(options={'HIDDEN', 'SKIP_SAVE'}, subtype='FILE_PATH', maxlen=1024) #type: ignore

    @property
    def Filepath(self) -> str:
        return self.filepath
    
    @Filepath.setter
    def Filepath(self, value: str):
        self.filepath = value


class FolderOperator(_FileOperator):
    directory: bpy.props.StringProperty(options={'HIDDEN', 'SKIP_SAVE'}, subtype='DIR_PATH', maxlen=1024) #type: ignore

    @property
    def Directory(self) -> str:
        return self.directory
    
    @Directory.setter
    def Directory(self, value: str):
        self.directory = value
