import bpy
import typing
import inspect
import bpy.types as bt

from . import enums
from . import utils
from . import config


DrawFunction = typing.Callable[[bt.UILayout], typing.Union[bt.UILayout, None]]
MenuItemMap = tuple[str, list[typing.Union[DrawFunction, 'MenuItemMap']]]
MenuPollMethod = typing.Callable[[typing.Any, bt.Context], bool]
IconParam = typing.Union[enums.BIcon, int]

_T = typing.TypeVar("_T")

def parse_ui_args(kwargs: dict, ui_function: typing.Union[bt.Function, str]):
    if isinstance(ui_function, str):
        ui_function: bt.Function = bt.UILayout.bl_rna.functions[ui_function]
    optional_keys = [x.identifier for x in ui_function.parameters if not x.is_required]
    return {k: v for k, v in kwargs.items() if k in optional_keys}

class _UIEmptyArgument:
    pass

class _BPyOpsSubModOp:
    bl_options: set[str] = ...
    idname: typing.Callable[[], str] = ...
    idname_py: typing.Callable[[], str] = ...
    poll: typing.Callable[[tuple], bool] = ...


def replace_default_args(init_func: typing.Callable):
    defaults = getattr(init_func, '__defaults__', None)
    if defaults is None:
        return
    if len(defaults) < 1:
        return
    
    sig = inspect.signature(init_func)
    # Replacing all default arguments with a placeholder object makes the arguments filterable for all classes using the UIType metaclass
    init_func.__defaults__ = tuple([_UIEmptyArgument()] * len(init_func.__defaults__))
    init_func.__signature__ = sig

class UIType(type):
    '''Replaces all default arguments in init with _UIEmptyArgument instance but keeps the signature. Filters unused arguments out'''
    def __new__(mcs, name, bases, namespace: dict):
        init_func = namespace.get('__init__', None)
        if init_func is not None:
            replace_default_args(init_func)
        return super().__new__(mcs, name, bases, namespace)

class UIOptions(metaclass=UIType):

    def __init__(self, **ui_args):
        ui_args = {k: v for k, v in ui_args.items() if not isinstance(v, _UIEmptyArgument)}
        self.options = ui_args

    def get_options(self):
        return self.options

    def __call__(self, parse_with: typing.Union[bt.Function, str] = None):
        o = self.get_options()
        if parse_with is None:
            return o
        return parse_ui_args(o, parse_with)

    def __getitem__(self, key: typing.Union[str, tuple[str]]):
        if isinstance(key, tuple):
            return {k: v for k, v in self.options.items() if k in key}
        return self.options[key]
    def __setitem__(self, key: str, item):
        self.set(key, item)
    def __delitem__(self, key: str):
        self.remove_option(key)

    def get(self, key: str, default=None):
        return self.options.get(key, default)
    
    def has_option(self, key: str):
        return key in self.options.keys()

    def set(self, key: str, item):
        self.options[key] = item
        return self
    
    def set_icon(self, icon: IconParam):
        result = self.resolve_icon_parameter(icon)
        self.update(result)
        return self
    
    def default(self, key: str, item):
        if key in self.get_options().keys():
            return
        self.set(key, item)
        return self
    
    def remove_option(self, key: str):
        del self.options[key]
    
    def update(self, other: typing.Union[dict, 'UIOptions']):
        items = other if isinstance(other, dict) else other()
        for k, v in items.items():
            self.set(k, v)
        return self
    
    def copy(self):
        new = type(self)()
        new.options = self.options.copy()
        return new

    @staticmethod
    def resolve_icon_parameter(param: IconParam) -> dict[str, typing.Union[str, int]]:
        result = {}
        if isinstance(param, int):
            result['icon_value'] = param
        elif isinstance(param, enums.BIcon):
            result['icon'] = param()
        return result

class UIOptionsProp(UIOptions):

    def __init__(
        self,
        text: str = '',
        text_ctxt: str = '',
        translate: bool = True,
        icon: IconParam = enums.BIcon.NONE,
        expand: bool = False,
        slider: bool = False,
        toggle: typing.Literal[-1, 0, 1] = -1,
        icon_only: bool = False,
        event: bool = False,
        full_event: bool = False,
        emboss: bool = True,
        index: int = -1,
        invert_checkbox: bool = False,
        **other_options: dict,
    ):
        options = dict(
            text=text,
            text_ctxt=text_ctxt,
            translate=translate,
            expand=expand,
            slider=slider,
            toggle=toggle,
            icon_only=icon_only,
            event=event,
            full_event=full_event,
            emboss=emboss,
            index=index,
            invert_checkbox=invert_checkbox,
            **other_options
        )
        options.update(self.resolve_icon_parameter(icon))
        super().__init__(**options)

class UIOptionsOperator(UIOptions):

    def __init__(
        self,
        text: str = '',
        text_ctxt: str='',
        translate: bool=True,
        icon: IconParam = enums.BIcon.NONE,
        emboss: bool = True,
        depress: bool = False
    ):
        options = dict(
            text=text,
            text_ctxt=text_ctxt,
            translate=translate,
            emboss=emboss,
            depress=depress
        )
        options.update(self.resolve_icon_parameter(icon))
        super().__init__(**options)

def UIIcon(icon: IconParam):
    '''Returns an UIOpionsProp instance with no text and a specific icon'''
    return UIOptionsProp(icon=icon, text='')

def UILabel(text: str):
    return UIOptionsProp(text=text)

class UIAlignment(enums.BStaticEnum):

    EXPAND = dict(n='Expand')
    LEFT = dict(n='Left')
    RIGHT = dict(n='Right')
    CENTER = dict(n='Center')

class UI:

    @staticmethod
    def prop(layout: bt.UILayout, obj: typing.Any, attr: str, options: UIOptions = UIOptionsProp()):
        new_ui_args = options(parse_with='prop')
        layout.prop(obj, attr, **new_ui_args)
        return new_ui_args
    
    @staticmethod
    def prop_custom(layout: bt.UILayout, obj: typing.Any, attr: str, options: UIOptions = UIOptionsProp()):
        return UI.prop(layout, obj=obj, attr=f'["{attr}"]', options=options)

    @staticmethod
    def prop_bool_dropdown(
        layout: bt.UILayout, 
        obj: typing.Any, 
        attr: str, 
        text_expanded: str = '', 
        text_collapsed: str = '', 
        icon_expanded: enums.BIcon = enums.BIcon.TRIA_DOWN, 
        icon_collapsed: enums.BIcon = enums.BIcon.TRIA_RIGHT,
        emboss: bool = False,
        invert_value: bool = False
    ):
        '''Draw the builtin property as a dropdown. Returns the value of the property. Inverted if "invert_value" is True'''
        value: bool = getattr(obj, attr)
        if invert_value:
            value = not value
        row = UI.row(layout, align=True)
        row.use_property_split = False
        UI.prop(row, obj, attr, UIOptionsProp(text='', icon=icon_expanded if value else icon_collapsed, emboss=emboss))
        if any(x != '' for x in (text_expanded, text_collapsed)):
            UI.prop(UI.align(row, UIAlignment.LEFT), obj, attr, UIOptionsProp(text=(text_expanded if value else text_collapsed), emboss=False))
        return value
    
    @staticmethod
    def prop_bool_switch(
        layout: bt.UILayout,
        obj: typing.Any,
        attr: str,
        text_true: str,
        text_false: str,
        hide_highlighting: bool
    ):
        value: bool = getattr(obj, attr)
        UI.prop(layout, obj, attr, UIOptionsProp(text=text_true if value else text_false, toggle=1, invert_checkbox=value if hide_highlighting else False))
        return value
    
    @staticmethod
    def prop_bool_icon_switch(
        layout: bt.UILayout,
        obj: typing.Any,
        attr: str,
        icon_true: IconParam,
        icon_false: IconParam,
        hide_highlighting: bool = True,
        invert_value: bool = False
    ):
        value: bool = getattr(obj, attr)
        invert_checkbox = value if hide_highlighting else False
        if(invert_value):
            invert_checkbox = not invert_checkbox
        UI.prop(layout, obj, attr, UIOptionsProp(text='', icon=icon_true if value else icon_false, invert_checkbox=invert_checkbox))
        return value

    @staticmethod
    def operator(
        layout: bt.UILayout, 
        operator: typing.Union[_BPyOpsSubModOp, str], 
        properties: dict[str] = {}, 
        options: UIOptions = UIOptionsOperator(),
        overrides: dict[str] = {},
        context: utils.AutoFill[enums.BOperatorContext] = None 
    ):
        operator_idname: str = operator
        if not isinstance(operator, str):
            operator_idname = operator.idname_py()
        if context is not None:
            layout.operator_context = context()
        for k, v in overrides.items():
            layout.context_pointer_set(k, v)

        new_ui_args = options(parse_with='operator')
        props = layout.operator(operator_idname, **new_ui_args)
        for k, v in properties.items():
            try:
                setattr(props, k, v)
            except TypeError:
                pass
        return new_ui_args
    
    @staticmethod
    def menu(
        layout: bt.UILayout,
        menu: bt.Menu,
        options: UIOptions = UIOptionsProp()
    ):
        layout.menu(menu.bl_rna.name, **options(parse_with='menu'))
        return layout

    @staticmethod
    def label(
        layout: bt.UILayout, 
        text: str, 
        text_ctxt: str = '',
        translate: bool = True,
        icon: IconParam = enums.BIcon.NONE,
        alignment: utils.AutoFill[UIAlignment] = None,
        alert: utils.AutoFill[bool] = None
    ):
        is_new_layout = False
        if alert and layout.alert != alert:
            layout = UI.row(layout, align=True)
            layout.alert = alert
            is_new_layout = True
        if alignment is not None:
            if not is_new_layout:
                layout = UI.row(layout, align=True)
            UI.align(layout, alignment=alignment)
        layout.label(
            text=text, 
            text_ctxt=text_ctxt,
            translate=translate,
            **UIOptions.resolve_icon_parameter(icon)
        )
        return layout
    
    @staticmethod
    def text(
        layout: bt.UILayout,
        text: str,
    ):
        lines_layout = layout.column(align=True)
        lines = text.split('\n')
        for line in lines:
            UI.label(lines_layout, line)

    @staticmethod
    def create_layout_style(style: enums.BLayoutStyle, layout: bt.UILayout, options: UIOptions = UIOptions()):
        return style.create(layout, **options['align', 'scale'])

    @staticmethod
    def even_split(layout: bt.UILayout, *functions: DrawFunction, align: bool = False) -> list[bt.UILayout]:
        if len(functions) == 0:
            return []
        current = layout
        remaining = list(functions)
        result = []
        while len(remaining) > 1:
            new = current.split(factor=1/len(remaining), align=align)
            result.append(new)
            remaining.pop(0)(new)
            current = new
        remaining[0](current)
        return result

    @staticmethod
    def weighted_split(layout: bt.UILayout, *weighted_functions: typing.Union[tuple[DrawFunction, float], DrawFunction], align: bool = False) -> list[bt.UILayout]:
        if len(weighted_functions) == 0:
            return []
        func_map: list[tuple[DrawFunction, float]] = []
        for data in list(weighted_functions):
            if isinstance(data, tuple):
                func, weight = data
            else:
                func = data
                weight = 1
            func_map.append((func, weight))
        
        result: list[bt.UILayout] = []
        current = layout
        while len(func_map) > 1:
            f, w = func_map.pop(0)
            weight_sum = sum(x[1] for x in func_map) + w
            ratio = w / weight_sum

            new = current.split(factor=ratio, align=align)
            result.append(f(new))
            current = new
        func_map[0][0](current)
        return result
    
    @staticmethod
    def row(layout: bt.UILayout, align: bool = False, heading: str = '', alignment: UIAlignment = UIAlignment.EXPAND):
        new_row = layout.row(align=align, heading=heading)
        new_row.alignment = alignment()
        return new_row

    @staticmethod
    def indent(layout: bt.UILayout, factor: float = 0.5, alignment: UIAlignment = UIAlignment.LEFT, align: bool = False):
        factor = max(min(factor, 1), 0)
        if alignment == UIAlignment.LEFT:
            s = layout.split(factor=factor, align=align)
            UI.label(s, '')
            return UI.row(s, align=align)
        elif alignment == UIAlignment.RIGHT:
            s = layout.split(factor=1-factor, align=align)
            r = UI.row(s, align=align, alignment=UIAlignment.RIGHT)
            UI.label(s, '')
            return r
        elif alignment in (UIAlignment.CENTER, UIAlignment.EXPAND):
            f = factor * 0.5
            
            new_layouts = UI.weighted_split(
                layout,
                (lambda l: UI.label(l, ''), f),
                (lambda l: UI.row(l, align=align, alignment=UIAlignment.CENTER), 1-factor),
                (lambda l: UI.label(l, ''), f),
                align=align
            )
            return new_layouts[1]
    
    @staticmethod
    def column(layout: bt.UILayout, align: bool = False, heading: str = '', alignment: UIAlignment = UIAlignment.EXPAND):
        new_column = layout.column(align=align, heading=heading)
        new_column.alignment = alignment()
        return new_column
    
    @staticmethod
    def enabled(layout: bt.UILayout, enabled: bool = True):
        if layout.enabled == enabled:
            return layout
        new_layout = UI.row(layout, align=True)
        new_layout.enabled = enabled
        return new_layout
    
    @staticmethod
    def set_enabled(layout: bt.UILayout, enabled: bool = True):
        layout.enabled = enabled
    
    @staticmethod
    def disable(layout: bt.UILayout):
        layout.enabled = False
        return layout
    
    @staticmethod
    def align(layout: bt.UILayout, alignment: UIAlignment):
        layout.alignment = alignment()
        return layout

    @staticmethod
    def alert(layout: bt.UILayout):
        if layout.alert == False:
            layout = UI.row(layout, align=True)
            layout.alert=True
        return layout
    
    @staticmethod
    def grid(layout: bt.UILayout, draw_functions: list[DrawFunction], major_column: bool = True, major_axis: int = 2, align: bool=True, scale: float = 1):
        import math
        major_axis = max(2, major_axis)
        count = len(draw_functions)
        if count < 1:
            return
        minor_axis = math.ceil(count / major_axis)
        items_per_row = major_axis if major_column else minor_axis
        r = range(len(draw_functions) % items_per_row)
        for i in r:
            draw_functions.append(lambda l: UI.label(l, ''))
        grid = UI.column(layout, align=align)
        grid.scale_y = scale
        funcs = []
        for i in range(len(draw_functions)):
            funcs.append(draw_functions[i])
            if len(funcs) == items_per_row:
                UI.even_split(grid, *funcs, align=align)
                funcs =  []

    @staticmethod
    def popover(layout: bt.UILayout, drawer: 'PropertyDrawer', options: UIOptionsProp = UIOptions()):
        from . import property_ui
        panel = property_ui.AL_PT_property_drawer_popover
        layout.context_pointer_set(panel.CONTEXT_TARGET_REF, drawer.target)
        layout.popover(panel.__name__, **options(parse_with='popover'))
    
    @staticmethod
    def resolve_icon(icon: IconParam):
        return UIOptions.resolve_icon_parameter(icon)
            

class Window:

    @staticmethod
    def redraw_all_regions():

        '''Redraw every region in Blender.'''
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                for region in area.regions:
                    region.tag_redraw()
    
    @staticmethod
    def redraw_region(context: bt.Context = None):
        if context is None:
            context = bpy.context
        context.region.tag_redraw()


class MenuBuilder:

    menu_classes: list[bpy.types.Menu]
    main_menu: bpy.types.Menu
    poll_method: MenuPollMethod

    def __init__(self, menu_map: MenuItemMap, poll: MenuPollMethod = lambda s, c: True):
        self.menu_classes = []
        self.poll_method = poll
        self.main_menu = self._create_menu(menu_map, poll)

    def _create_menu(self, menu_map: MenuItemMap, poll: MenuPollMethod):
        import random
        generated_name = f"{config.ADDON_PREFIX}_MT_DynamicMenu_{random.randint(0, 9999999)}"
        menu_name = menu_map[0]
        draw_functions: list[DrawFunction] = []
        for i in menu_map[1]:
            if isinstance(i, tuple):
                menu = self._create_menu(i, poll)
                draw_functions.append(lambda layout, m=menu: UI.menu(layout, m))
            else:
                draw_functions.append(i)

        def draw(self: bt.Menu, context: bt.Context):
            for f in draw_functions:
                f(self.layout)
        
        members = dict(
            bl_idname = generated_name,
            bl_label = menu_name,
            poll = classmethod(poll),
            draw = draw
        )

        menu_class = type(generated_name, (bpy.types.Menu,), members)
        self.menu_classes.append(menu_class)
        return menu_class
    
    def register(self, register: bool):
        for mc in self.menu_classes:
            if register:
                bpy.utils.register_class(mc)
            else:
                bpy.utils.unregister_class(mc)

    def draw(self, layout: bt.UILayout, options: UIOptions = UIOptions()):
        return UI.menu(layout, self.main_menu, options)
    
    def call(self):
        bpy.ops.wm.call_menu(name=self.main_menu.bl_idname)


class PropertyDrawerType(type):
    
    _property_drawer_types: dict[typing.Any, type['PropertyDrawer']] = {}

    def __new__(mcs, name, bases, namespace: dict):
        built_class = super().__new__(mcs, name, bases, namespace)
        mcs.handle_new_class(built_class)
        return built_class
    
    @classmethod
    def handle_new_class(mcs, built_class: type):
        try:
            PropertyDrawer # skip the PropertyDrawer class because it is undefined and not applicable
        except NameError:
            return
        
        base = next(x for x in built_class.__orig_bases__ if x.__origin__ == PropertyDrawer)
        assigned_class = base.__args__[0]
        mcs._property_drawer_types[assigned_class] = built_class

    @classmethod
    def get_drawer_from_instance(mcs, instance: typing.Any):
        return mcs._property_drawer_types[type(instance)]

class PropertyDrawer(typing.Generic[_T], metaclass=PropertyDrawerType):

    def __init__(self, target: _T, layout: bt.UILayout, context: bt.Context):
        self.target: _T = target
        self.layout: bt.UILayout = layout
        self.context: bt.Context = context
    
    def draw(self):
        pass

    def draw_panel(self):
        pass
