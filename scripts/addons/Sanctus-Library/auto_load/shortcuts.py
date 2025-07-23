import bpy
import typing
import dataclasses

import bpy.types as bt

from . import utils
from . import ops
from . import enums
from . import ui

@dataclasses.dataclass
class ShortcutInfo():

    keymap: bt.KeyMap
    keymap_item: bt.KeyMapItem
    name: str = ''

    def get_user_binding(self) -> tuple[bt.KeyMap, bt.KeyMapItem]:
        
        user_km = bpy.context.window_manager.keyconfigs.user.keymaps[self.keymap.name]
        similar_items = [kmi for kmi in user_km.keymap_items if kmi.idname == self.keymap_item.idname]
        if len(similar_items) == 1:
            user_kmi = similar_items[0]
        else:
            user_kmi = next(x for x in similar_items if list(x.properties.values()) == list(self.keymap_item.properties.values()))
        return user_km, user_kmi
    
    def set_user_binding(self, type: enums.BEventType, shift: bool = False, ctrl: bool = False, alt: bool = False):
        _, kmi = self.get_user_binding()
        kmi.type = type()
        kmi.shift = shift
        kmi.ctrl = ctrl
        kmi.alt = alt
    
    def serialize(self):
        _, kmi = self.get_user_binding()
        return dict(
            type=kmi.type,
            shift=kmi.shift,
            ctrl=kmi.ctrl,
            alt=kmi.alt
            )
    
    def deserialize(self, data: dict[str, utils.JSONSerializable]):
        self.set_user_binding(
            type=data['type'],
            shift=data['shift'],
            ctrl=data['ctrl'],
            alt=data['alt'],
            )
        
    def draw_user_binding(self, layout: bt.UILayout, expand: bool = True, use_icons: bool = True) -> None:

        km, kmi = self.get_user_binding()
        if not expand:
            layout.context_pointer_set('keymap', km)
            ui.UI.prop(layout, kmi, 'type', ui.UIOptionsProp(text=self.name, event=True))
        else:
            main_split = layout.split(factor=1/3)
            main_split.context_pointer_set('keymap', km)
            ui.UI.label(main_split, text=f'{self.name}:')
            
            prop_split = main_split.split(factor=1/2)
            ui.UI.prop(prop_split, kmi, 'type', ui.UIOptionsProp(text='', event=True))

            mod_layout = prop_split.row(align=True)
            for prop_key, text, icon in [
                ('shift_ui', 'Shift', enums.BIcon.EVENT_SHIFT),
                ('ctrl_ui', 'Ctrl', enums.BIcon.EVENT_CTRL),
                ('alt_ui', 'Alt', enums.BIcon.EVENT_ALT)
            ]:
                ui.UI.prop(mod_layout, kmi, prop_key, ui.UIOptionsProp(
                    text='' if use_icons else text, 
                    icon=icon if use_icons else enums.BIcon.NONE,
                    toggle=1
                )
                )

class KeymapManager():

    def __init__(self):
        self.shortcuts: list[ShortcutInfo] = []

    def add_shortcut(
        self,
        operator: ops.Operator,
        input_type: enums.BEventType,
        input_value: enums.BEventValue = enums.BEventValue.PRESS,
        space_info: typing.Union[enums.BSpaceInfo, tuple[str, str]] = enums.BSpaceInfo.ALL,
        region_type: enums.BRegionType = enums.BRegionType.WINDOW,
        name: str = '',
        **keymap_item_settings: dict[str, typing.Any]
        ) -> bt.KeyMapItem:

        kmi = self.add_shortcut_builtin(
            operator.bl_idname,
            {},
            input_type,
            input_value=input_value,
            space_info=space_info,
            region_type=region_type,
            name=name,
            **keymap_item_settings   
        )
        operator.set_operator_properties(kmi.properties)
        return kmi
    
    def add_shortcut_builtin(
        self,
        operator: typing.Union[ui._BPyOpsSubModOp, str],
        operator_properties: dict[str, typing.Any],
        input_type: enums.BEventType,
        input_value: enums.BEventValue = enums.BEventValue.PRESS,
        space_info: typing.Union[enums.BSpaceInfo, tuple[str, str]] = enums.BSpaceInfo.ALL,
        region_type: enums.BRegionType = enums.BRegionType.WINDOW,
        name: str = '',
        **keymap_item_settings: dict[str, typing.Any]
        ) -> bt.KeyMapItem:

        operator_idname = operator
        if not isinstance(operator, str):
            operator_idname = operator.idname_py()
        if isinstance(space_info, enums.BSpaceInfo):
            keymap_name, space_type = space_info.get_space_name(), space_info.get_space_type()
        else:
            keymap_name, space_type = space_info
        
        # convert parameters given in either enum or string form to string
        region_type = region_type()
        input_type = input_type()
        input_value = input_value()

        addon_keyconfigs = bpy.context.window_manager.keyconfigs.addon

        km = addon_keyconfigs.keymaps.new(keymap_name, space_type=space_type, region_type=region_type)
        kmi = km.keymap_items.new(operator_idname, input_type, input_value, **keymap_item_settings)
        for k, v in operator_properties.items():
            setattr(kmi.properties, k, v)
        self.shortcuts.append(ShortcutInfo(km, kmi, name))
        return kmi

    def clear_shortcuts(self):
        for shortcut in self.shortcuts:
            shortcut.keymap.keymap_items.remove(shortcut.keymap_item)
        self.shortcuts.clear()

    def serialize(self):
        return [x.serialize() for x in self.shortcuts]

    def deserialize(self, data: list[dict[str, utils.JSONSerializable]]):
        if len(data) != len(self.shortcuts):
            print(f'Deserializing KeymapManager with data of mismatching size. Shortcuts={len(self.shortcuts)}, Data={len(data)}')
        for index in range(min(len(data), len(self.shortcuts))):
            self.shortcuts[index].deserialize(data[index])
        