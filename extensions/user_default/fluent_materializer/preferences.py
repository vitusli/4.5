import rna_keymap_ui
from bpy.props import FloatVectorProperty, BoolProperty, IntProperty
from bpy.types import AddonPreferences

from .constants import MASKS_LIST
from .Tools.helper import *
from .operators import FLUENT_OT_restore_hotkey


class AddonKeymaps:
    _addon_keymaps = []
    _keymaps = {}

    @classmethod
    def new_keymap(cls, name, kmi_name, kmi_value=None, km_name='3D View',
                   space_type="VIEW_3D", region_type="WINDOW",
                   event_type=None, event_value=None, ctrl=False, shift=False,
                   alt=False, key_modifier="NONE"):
        """
        Adds a new keymap
        :param name: str, Name that will be displayed in the panel preferences
        :param kmi_name: str
                - bl_idname for the operators (exemple: 'object.cube_add')
                - 'wm.call_menu' for menu
                - 'wm.call_menu_pie' for pie menu
        :param kmi_value: str
                - class name for Menu or Pie Menu
                - None for operators
        :param km_name: str, keymap name (exemple: '3D View Generic')
        :param space_type: str, space type keymap is associated with, see:
                https://docs.blender.org/api/current/bpy.types.KeyMap.html?highlight=space_type#bpy.types.KeyMap.space_type
        :param region_type: str, region type keymap is associated with, see:
                https://docs.blender.org/api/current/bpy.types.KeyMap.html?highlight=region_type#bpy.types.KeyMap.region_type
        :param event_type: str, see:
                https://docs.blender.org/api/current/bpy.types.Event.html?highlight=event#bpy.types.Event.type
        :param event_value: str, type of the event, see:
                https://docs.blender.org/api/current/bpy.types.Event.html?highlight=event#bpy.types.Event.value
        :param ctrl: bool
        :param shift: bool
        :param alt: bool
        :param key_modifier: str, regular key pressed as a modifier
                https://docs.blender.org/api/current/bpy.types.KeyMapItem.html?highlight=modifier#bpy.types.KeyMapItem.key_modifier
        :return:
        """
        cls._keymaps.update({name: [kmi_name, kmi_value, km_name, space_type,
                                    region_type, event_type, event_value,
                                    ctrl, shift, alt, key_modifier]
                             })

    @classmethod
    def add_hotkey(cls, kc, keymap_name):

        items = cls._keymaps.get(keymap_name)
        if not items:
            return

        kmi_name, kmi_value, km_name, space_type, region_type = items[:5]
        event_type, event_value, ctrl, shift, alt, key_modifier = items[5:]
        km = kc.keymaps.new(name=km_name, space_type=space_type,
                            region_type=region_type)

        kmi = km.keymap_items.new(kmi_name, event_type, event_value,
                                  ctrl=ctrl,
                                  shift=shift, alt=alt,
                                  key_modifier=key_modifier
                                  )
        if kmi_value:
            kmi.properties.name = kmi_value

        kmi.active = True

        cls._addon_keymaps.append((km, kmi))

    @staticmethod
    def register_keymaps():
        wm = bpy.context.window_manager
        kc = wm.keyconfigs.addon
        # In background mode, there's no such thing has keyconfigs.user,
        # because headless mode doesn't need key combos.
        # So, to avoid error message in background mode, we need to check if
        # keyconfigs is loaded.
        if not kc:
            return

        for keymap_name in AddonKeymaps._keymaps.keys():
            AddonKeymaps.add_hotkey(kc, keymap_name)

    @classmethod
    def unregister_keymaps(cls):
        kmi_values = [item[1] for item in cls._keymaps.values() if item]
        kmi_names = [item[0] for item in cls._keymaps.values() if
                     item not in ['wm.call_menu', 'wm.call_menu_pie']]

        for km, kmi in cls._addon_keymaps:
            # remove addon keymap for menu and pie menu
            if hasattr(kmi.properties, 'name'):
                if kmi_values:
                    if kmi.properties.name in kmi_values:
                        km.keymap_items.remove(kmi)

            # remove addon_keymap for operators
            else:
                if kmi_names:
                    if kmi.idname in kmi_names:
                        km.keymap_items.remove(kmi)

        cls._addon_keymaps.clear()

    @staticmethod
    def get_hotkey_entry_item(name, kc, km, kmi_name, kmi_value, col):

        # for menus and pie_menu
        if kmi_value:
            for km_item in km.keymap_items:
                if km_item.idname == kmi_name and km_item.properties.name == kmi_value:
                    col.context_pointer_set('keymap', km)
                    rna_keymap_ui.draw_kmi([], kc, km, km_item, col, 0)
                    return

            col.label(text=f"No hotkey entry found for {name}")
            col.operator(FLUENT_OT_restore_hotkey.bl_idname,
                         text="Restore keymap",
                         icon='ADD').km_name = km.name

        # for operators
        else:
            if km.keymap_items.get(kmi_name):
                col.context_pointer_set('keymap', km)
                rna_keymap_ui.draw_kmi([], kc, km, km.keymap_items[kmi_name],
                                       col, 0)

            else:
                col.label(text=f"No hotkey entry found for {name}")
                col.operator(FLUENT_OT_restore_hotkey.bl_idname,
                             text="Restore keymap",
                             icon='ADD').km_name = km.name

    @staticmethod
    def draw_keymap_items(wm, layout):
        kc = wm.keyconfigs.user

        box = layout.box()
        for name, items in AddonKeymaps._keymaps.items():
            kmi_name, kmi_value, km_name = items[:3]
            split = box.split()
            col = split.column()
            # col.label(text=name)
            # col.separator()
            km = kc.keymaps[km_name]
            AddonKeymaps.get_hotkey_entry_item(name, kc, km, kmi_name,
                                               kmi_value, col)


class FluentAddonPreferences(AddonPreferences):
    bl_idname = __package__

    def update_samples(self, context):
        bpy.context.scene.FluentShaderProps.nb_samples = self.nb_samples

    color_layer: FloatVectorProperty(
        name="Layer node",
        description="Color of layer node",
        subtype='COLOR',
        min=0,
        max=1,
        default=(0, 0.3, 0.4)
    )

    color_mixlayers: FloatVectorProperty(
        name="Mix layers node",
        description="Color of mix layers node",
        subtype='COLOR',
        min=0,
        max=1,
        default=(0, 0.2, 0.4)
    )

    use_custom_node_color: BoolProperty(
        description="Use custom color instead of Blender native colors",
        name="Enable custom color",
        default=False
    )

    nb_samples: IntProperty(
        name='Samples',
        description='Number of samples in the bevel and AO nodes',
        default=8,
        update=update_samples
    )

    pil: BoolProperty(name="PIL", default=False)

    pil_warning: BoolProperty(name="PIL warning", default=False)

    cv2: BoolProperty(name="cv2", default=False)

    cv2_warning: BoolProperty(name="cv2 warning", default=False)

    bake_background: BoolProperty(name="Background baking", default=True, description='Render baking in background')

    use_favorites: BoolProperty(name="Use favorites mask", default=True)

    favorite_one: EnumProperty(name="Favorite one", items=MASKS_LIST, default='EDGES')
    favorite_two: EnumProperty(name="Favorite two", items=MASKS_LIST, default='ALL_EDGES')
    favorite_three: EnumProperty(name="Favorite three", items=MASKS_LIST, default='CAVITY')
    favorite_four: EnumProperty(name="Favorite four", items=MASKS_LIST, default='LOCAL')

    def draw(self, context):
        wm = context.window_manager
        layout = self.layout
        icons = load_icons()
        AddonKeymaps.draw_keymap_items(wm, layout)

        layout.prop(self, 'use_custom_node_color')
        layout.prop(self, 'color_layer')
        layout.prop(self, 'color_mixlayers')
        layout.prop(self, 'bake_background')
        layout.prop(self, 'nb_samples')

        box = layout.box()
        row = box.row()
        row.label(text="Masks")
        row = box.row()
        row.prop(self, 'use_favorites')

        if self.use_favorites:
            row = box.row()
            row.prop(self, 'favorite_one')
            row = box.row()
            row.prop(self, 'favorite_two')
            row = box.row()
            row.prop(self, 'favorite_three')
            row = box.row()
            row.prop(self, 'favorite_four')

        box = layout.box()
        column = box.column()
        column.scale_y = 1.2

        if self.pil_warning:
            row = column.row()
            row.label(text="PIL is installed. Please restart Blender", icon="ERROR")

        if self.pil and not self.pil_warning:
            row = column.row()
            row.label(text="PIL is installed.", icon_value=icons.get("added").icon_id)

        if not self.pil and not self.pil_warning:
            row = column.split(factor=0.2)
            row.operator("fluent.install_pil", text="Install PIL", icon="PREFERENCES")
            col = row.column()
            col.label(text="In order to have better quality thumbnails in the NPanel, PIL is needed")
            col.label(text="Internet connection required.", icon="INFO")

        if self.cv2_warning:
            row = column.row()
            row.label(text="cv2 is installed. Please restart Blender", icon="ERROR")

        if self.cv2 and not self.cv2_warning:
            row = column.row()
            row.label(text="cv2 is installed.", icon_value=icons.get("added").icon_id)

        if not self.cv2 and not self.cv2_warning:
            row = column.split(factor=0.2)
            row.operator("fluent.install_cv2", text="Install cv2", icon="PREFERENCES")
            col = row.column()
            col.label(text="In order to be able to worn decal edges, cv2 is needed")
            col.label(text="Internet connection required.", icon="INFO")
