import typing
import bpy
import bpy.types as bt
import functools
import importlib
import inspect
import sys
import types
import enum
from pathlib import Path

from . import ops
from . import props
from . import config
from . import utils
from . import prefs

T = typing.TypeVar('T')
RegisterFunction = typing.Callable[[bool], None]


def _get_module_names(file: str, package: str = '') -> list[str]:

    if not package == '':
        package += '.'
    all_modules = Path(file).parent.glob('*')
    # filter __init__ and __pycache__
    return [package + x.name.rsplit('.py', 1)[0] for x in all_modules if not x.name.startswith('__')]


def import_modules(file: str, package: typing.Union[str, None] = None) -> list[types.ModuleType]:
    modules = []
    for name in _get_module_names(file, package):
        try:
            mod = importlib.import_module(name, package=package)
            modules.append(mod)
        except ModuleNotFoundError:
            pass  # is not a module
    return modules


def get_classes_in_module(module_name):
    import sys
    import inspect
    return [x[1] for x in inspect.getmembers(sys.modules[module_name], inspect.isclass)]


def cleanse_modules():
    '''Remove module cache of entire package and subpackages of an addon.'''
    import sys
    utils.debug(f'Cleansing modules from {repr(config.ADDON_PACKAGE)}')
    for m in [x for x in sys.modules if x.startswith(config.ADDON_PACKAGE)]:
        sys.modules.pop(m)

class ClassMod:

    def __init__(self, clss: type, method_name: str, override_method: typing.Callable):
        if not hasattr(clss, method_name):
            raise AttributeError(f"Class {clss.__name__} does not have a member '{method_name}'")
        method = getattr(clss, method_name)
        if not inspect.isfunction(method):
            raise TypeError(f"Member '{method_name}' of class {clss.__name__} is not a function")
        self.clss = clss
        self.method_name = method_name
        self.override_method = override_method
        self.original_method = method


class RegisterType(enum.Enum):

    CLASS = enum.auto()
    CLASS_FUNC = enum.auto()
    FUNC = enum.auto()
    CLASS_MOD = enum.auto()

def _test_configuration(message: str = 'Some error occured because Auto-Load is not configured.'):
    if config.ADDON_PACKAGE is None:
        raise RuntimeError(message)
    
def _test_configuration_default(obj):
    _test_configuration(f'Auto-Load cannot register object {obj} before the module is configured. Use al.configure to do so.')

def _get_register_manager():
    module = utils.get_addon_module()
    manager: RegisterManager = getattr(module, config.REGISTER_MANAGER_NAME)
    return manager

def _add_obj_to_register_manager(obj, type: RegisterType):
    _test_configuration_default(obj)
    manager = _get_register_manager()
    if type == RegisterType.CLASS:
        manager.add_class(obj)
    elif type == RegisterType.CLASS_FUNC:
        manager.add_class_function(obj)
    elif type == RegisterType.FUNC:
        manager.add_function(obj)
    elif type == RegisterType.CLASS_MOD:
        obj: ClassMod
        manager.add_class_mod(obj)

def register(obj):
    '''Adds function or class to Global list for registration.'''

    if inspect.isclass(obj):

        if issubclass(obj, prefs.AddonPreferences):
            if getattr(obj, 'bl_idname', '') == '':
                _test_configuration(f'Cannot register AddonPreferences because Auto-Load is not configured yet. Use al.configure to do so.')
                obj.bl_idname = config.ADDON_PACKAGE
        if issubclass(obj, bt.Panel):
            panel_prefix = f'{config.ADDON_PREFIX}_PT_'
            if not obj.__name__.startswith(panel_prefix):
                obj.__name__ = panel_prefix + obj.__name__.split("_PT_")[-1]
                obj.bl_idname = obj.__name__
        if issubclass(obj, bt.Menu):
            menu_prefix = f'{config.ADDON_PREFIX}_MT_'
            if not obj.__name__.startswith(menu_prefix):
                obj.__name__ = menu_prefix + obj.__name__.split("_MT_")[-1]
                obj.bl_idname = obj.__name__

        if issubclass(obj, props.AnnotatedObject):
            obj.annotate()

    _add_obj_to_register_manager(obj, RegisterType.CLASS if inspect.isclass(obj) else RegisterType.FUNC)
    return obj


def _complete_missing_operator_properties(op_class: typing.Type[bt.Operator]):

    prefix = config.ADDON_PREFIX
    prefix_part = prefix.lower()
    name_part = utils.to_snake_case(op_class.__name__)

    if not hasattr(op_class, 'bl_idname'):
        op_class.bl_idname = f'{prefix_part}.{name_part}'
    if not hasattr(op_class, 'bl_label'):
        op_class.bl_label = name_part.replace('_', ' ').title()
    if not hasattr(op_class, 'bl_description'):
        op_class.bl_description = op_class.bl_label


def register_operator(auto_op_cls: ops.Operator) -> T:
    _complete_missing_operator_properties(auto_op_cls)

    meta_op_cls = auto_op_cls.create_meta_op()

    auto_op_cls.__init__ = bt.Operator.__init__
    auto_op_cls.annotate()
    _add_obj_to_register_manager(auto_op_cls, RegisterType.CLASS)
    return meta_op_cls


def register_property_wrapper(parent_cls, property: props.Property, attr_name: str = None):

    def register_inner(cls) -> T:
        nonlocal property, attr_name
        if attr_name in [None, '']:
            attr_name = utils.to_snake_case(cls.__name__)
        property.attr_name = attr_name

        if issubclass(cls, props.PropertyGroup):
            cls.annotate()
            property.deferred_property.keywords['type'] = cls

            _add_obj_to_register_manager(cls, RegisterType.CLASS)

        def register(register: bool):
            if register:
                setattr(parent_cls, property.attr_name, property.deferred_property)
            else:
                delattr(parent_cls, property.attr_name)

        register.__name__ = f'register_{cls.__name__}_to_{parent_cls.__name__}'

        _add_obj_to_register_manager(register, RegisterType.CLASS_FUNC)
        cls.prop_map = []
        cls.prop_map.append((attr_name, property, parent_cls))

        return cls

    return register_inner


def register_property_group(parent_cls, property: props.PointerProperty = None, attr_name: str = None):
    if property is None:
        property = props.PointerProperty(type=None)
    return register_property_wrapper(parent_cls=parent_cls, property=property, attr_name=attr_name)


def register_property(parent_cls, attr_name: str = None):
    def register_property_inner(cls) -> T:
        nonlocal attr_name
        if attr_name in [None, '']:
            attr_name = utils.to_snake_case(cls.__name__)
        if not cls.__init__.__code__.co_argcount == 1:
            raise ValueError(f'Init method of {cls} needs to accept a single "self" argument')

        def register(register: bool):
            if register:
                descriptor: props.Property = cls()
                descriptor.set_context(parent_cls, attr_name)
                setattr(parent_cls, attr_name, descriptor)
                setattr(parent_cls, descriptor.data_attr, descriptor.deferred_property)
            else:
                descriptor = vars(parent_cls)[attr_name]
                delattr(parent_cls, descriptor.attr_name)
                delattr(parent_cls, descriptor.data_attr)
        register.__name__ = f'register_{cls.__name__}_to_{parent_cls.__name__}'
        _add_obj_to_register_manager(register, RegisterType.CLASS_FUNC)
        return cls

    return register_property_inner


def register_draw_function(*menus: list[typing.Union[bt.Menu, bt.Panel]], prepend: bool = False):
    '''Auto register a draw callback to a Blender menu or panel.'''

    @functools.wraps(register_draw_function)
    def decorator(function: typing.Callable):

        def register_func(register: bool, menus: list[typing.Union[bt.Menu, bt.Panel]], prepend: bool, function: typing.Callable):
            add_function_name = 'prepend' if prepend else 'append'
            for menu in menus:
                getattr(menu, add_function_name if register else 'remove')(function)

        composed_func = functools.partial(register_func, menus=menus, prepend=prepend, function=function)
        composed_func.__name__ = f'register_callback_{function.__name__}'
        _add_obj_to_register_manager(composed_func, RegisterType.FUNC)
        skip_function_in_background(None)
        return function

    return decorator


def register_timer(first_interval: float = 0, threaded: bool = False, thread_delay: float = 60):
    '''Auto register a timer callback function'''

    def decorator(timer_function: typing.Callable):

        def thraded_timer_function():
            import threading
            thread = threading.Thread(target=timer_function)
            thread.start()
            return thread_delay
        final_timer_function = thraded_timer_function if threaded else timer_function

        def register_func(register: bool):
            if register:
                bpy.app.timers.register(final_timer_function, first_interval=first_interval, persistent=True)
            elif bpy.app.timers.is_registered(final_timer_function):
                bpy.app.timers.unregister(final_timer_function)

        register_func.__name__ = f'register_timer_{timer_function.__name__}'
        _add_obj_to_register_manager(register_func, RegisterType.FUNC)
        return timer_function

    return decorator

def register_handler_callback(*handlers: list, persistent: bool = True):
    '''register a callback function to a handler in the <bpy.app.handlers> module'''

    def decorator(callback):
        if persistent:
            bpy.app.handlers.persistent(callback)
        def register_func(register: bool):
            for h in handlers:
                if register:
                    h.append(callback)
                else:
                    h.remove(callback)
        
        register_func.__name__ = f'register_handler_callback_{callback.__name__}'
        _add_obj_to_register_manager(register_func, type=RegisterType.FUNC)
        return callback
    
    return decorator

def skip_function(func):
    _get_register_manager().pop_last(RegisterType.FUNC)
    return func

def skip_function_in_background(func):
    if bpy.app.background:
        _get_register_manager().pop_last(RegisterType.FUNC)
    return func

def depends_on(*deps):
    '''Define dependencies to determine a registration order for certain classes. Use as decorator.'''

    def wrap(cls):
        setattr(cls, config.DEPENDENCY_ATTR, getattr(cls, config.DEPENDENCY_ATTR, []) + list(deps))
        return cls

    return wrap

def class_mod(clss: type, method: typing.Callable):

    method_name = method.__qualname__.split('.')[-1]

    def wrap(func):
        _add_obj_to_register_manager(ClassMod(clss, method_name, func), RegisterType.CLASS_MOD)
        return func
    return wrap

def _get_ordered_dependencies(clss: type) -> list[type]:
    '''For a class gets a list of all its dependencies going recursively through the inheritence stack.'''
    result = []
    for c in clss.mro():
        if c != clss:
            result += _get_ordered_dependencies(c)
    current_dependencies = getattr(clss, config.DEPENDENCY_ATTR, [])
    for d in current_dependencies:
        result += _get_ordered_dependencies(d)
    result += current_dependencies
    return utils.remove_duplicates(result)


def _get_skip_addon_initialization_in_background_message():
    from . import text
    lines = [
        "Skip initializing the addon while", 
        "Blender is a background process."
    ]
    box_text = text.box(lines, header=utils.get_adddon_bl_info()['name'])
    return text.color(box_text, color=text.COLOR_RED)

class RegisterManager:

    classes: list[type]
    class_functions: list[RegisterFunction]
    functions: list[RegisterFunction]
    class_mods: list[ClassMod]

    def __init__(self):
        self.classes = []
        self.class_functions = []
        self.functions = []
        self.class_mods = []

    def add_class(self, cls):
        for deps in _get_ordered_dependencies(cls):
            self.add_class(deps)
        if not cls in self.classes:
            self.classes.append(cls)

    def add_class_function(self, func: RegisterFunction):
        if not func in self.class_functions:
            self.class_functions.append(func)

    def add_function(self, func: RegisterFunction):
        if not func in self.functions:
            self.functions.append(func)

    def add_class_mod(self, class_mod: ClassMod):
        self.class_mods.append(class_mod)

    def pop_last(self, type: RegisterType):
        if type == RegisterType.CLASS:
            self.classes.pop()
        elif type == RegisterType.CLASS_FUNC:
            self.class_functions.pop()
        elif type == RegisterType.FUNC:
            self.functions.pop()
        elif type == RegisterType.CLASS_MOD:
            self.class_mods.pop()

    def register(self, register: bool):
        order = self.get_order(register)
        error: typing.Union[Exception, None] = None
        done: list[typing.Union[typing.Type, typing.Callable]] = []
        utils.debug("+++REGISTER ADDON:" if register else "---UNREGISTER ADDON:")
        for item, method in order:
            try:
                method(item, register)
                done.append((item, method))
            except Exception as e:
                error = e
                print('\n')
                print(f'-- An Error occured while trying to {"register" if register else "unregister"} {item.__name__}. Unregistering Addon!')
                print(f'Version: {config.ADDON_VERSION}')
                print('\n')
                break

        if error:
            if register:
                for item, method in reversed(done):
                    method(item, False)

            print('\n\n =======================================')
            raise error
        else:
            utils.debug('='*40)

    def get_order(self, register: bool):
        lists: list[tuple[list, typing.Callable[[typing.Any, bool]]]] = [
            (self.classes, self.register_class),
            (self.class_functions, self.register_function),
            (self.functions, self.register_function),
            (self.class_mods, self.register_class_mod)
        ]

        order: list[tuple[typing.Any, typing.Callable[[typing.Any, bool]]]] = []

        for collection, method in lists:
            for item in collection:
                order.append((item, method))
        return order if register else reversed(order)

    @staticmethod
    def register_class(cls, register: bool):
        utils.debug(f'{"   Register" if register else "Unregister"} Class: {cls.__name__}')
        if register:
            bpy.utils.register_class(cls)
        else:
            bpy.utils.unregister_class(cls)

    @staticmethod
    def register_function(func, register: bool):
        utils.debug(f'{"   Register" if register else "Unregister"} Function: {func.__name__}')
        func(register)

    @staticmethod
    def register_class_mod(class_mod: ClassMod, register: bool):
        utils.debug(f'{"    Register" if register else "Unregister"} Class Mod: {class_mod.clss.__name__}.{class_mod.method_name}')
        if register:
            setattr(class_mod.clss, class_mod.method_name, class_mod.override_method)
        else:
            setattr(class_mod.clss, class_mod.method_name, class_mod.original_method)


def register_addon():
    '''Set up register and unregister functions for the module. All imported modules will contribute to the register/unregister routine'''
    _test_configuration(f'Cannot register the addon before Auto-Load is configured. Do so using al.configure.')
    
    module = utils.get_addon_module()

    if bpy.app.background and not config.RUN_IN_BACKGROUND:
        print(_get_skip_addon_initialization_in_background_message())
        module.register = lambda: None
        module.unregister = lambda: None
        return

    
    manager: RegisterManager = getattr(module, config.REGISTER_MANAGER_NAME)

    def register():
        manager.register(True)

    def unregister():
        manager.register(False)
        cleanse_modules()

    module.register = register
    module.unregister = unregister
