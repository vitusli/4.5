'''
Manages the preferences UI. Currently, all of the user preferences get saved to and loaded from an external file. I am not sure if that is super necessary...
But it is also possible to export and import preferences in a similar fashion as the user.
'''


from . import auto_load as al
from . auto_load.common import *
from . import dev_info
from . import operators
from . import baking
from . import constants

import json

PREFERENCES_EXTENSION: str = '.json'

KEYMAP_MANAGER: al.KeymapManager = None

class PreferencesContext(al.BStaticEnum):

    INTERFACE = dict(n="Interface", d="Interface Settings")
    SHORTCUTS = dict(n="Shortcuts", d="Shortcut Settings")
    BAKING = dict(n="Baking", d="Baking Settings")
    DECALS = dict(n="Decals", d="Decal Settings")
    EXPANSIONS = dict(n='Expansions', d="Expansion Settings")


'''ExternalLibrary is both uses for custom decal folders as well as expansions. A good idea might be to refactor the code so that both usecases are separated from one another.'''
@al.register
class ExternalLibrary(al.PropertyGroup):
    '''stores a path to a library outside of the main addon library. Users are able to load their own images as decals and as of recently users can install expansion packs'''

    directory = al.PathProperty(name='Custom Decals', description='Folder location where user decal images are stored', default='//', subtype=al.BPropertySubtypeString.DIR_PATH, fallback=al.BPathFallbackType.BLENDFILE_OR_USER_FOLDER)
    category_name = al.StringProperty(name='Category Name', default='Custom', description='Name of the custom decals category that is displayed in the UI')
    base_path = al.PathProperty()
    is_decal_folder = al.BoolProperty()
    
    loaded_successfully = al.BoolProperty(default=False)

    #expansion properties
    expansion_name = al.StringProperty()
    expansion_version = al.StringProperty()

    @property
    def expansion_version_formatted(self):
        version_tuple: tuple[int, int, int] = eval(self.expansion_version())
        version_str = [str(x) for x in version_tuple]
        return f'({".".join(version_str)})'


    def draw_ui(self, layout: bt.UILayout, collection: al.CollectionProperty['ExternalLibrary']):
        from . import library_manager
        from .operators import preferences as prefops
        row = al.UI.row(layout)

        has_error = False

        if self.is_decal_folder():
            if not self.directory.absolute.exists():
                row.alert = True
            f1 = lambda l: self.category_name.draw_ui(l, al.UILabel(""))
            f2 = lambda l: self.directory.draw_ui(l, al.UILabel(""))
            al.UI.weighted_split(row, (f1, 0.4), (f2, 1), align=True)
        elif not self.loaded_successfully():
            error_text = f"The external library at path:\n{self.directory()} \nwas unable to load.\nPlease make sure the selected path exists\nor relocate the expansion by removing it and reinstalling using the correct path."
            prefops.ErrorPopup(text=error_text, alert=True).draw_ui(al.UI.alert(row), al.UIOptionsOperator(text=self.expansion_name(), icon=al.BIcon.ERROR))
            has_error = True
        else:
            row = al.UI.row(row.box(), align=True)
            expansion_name = self.expansion_name()
            try:
                icon_id = library_manager.MANAGER.icon_id(Path(f'icons/{expansion_name}'))
                al.UI.label(row, f'{expansion_name} {self.expansion_version_formatted}', icon=icon_id)
            except KeyError:
                error_text = "An Error occurred finding the expansion icon" if self.directory.absolute.exists() else "Expansion could not be found"
                al.UI.label(al.UI.alert(row), error_text, icon=al.BIcon.ERROR)
                has_error = True
            al.UI.label(row, self.directory())
        
        remove_layout = al.UI.row(row, align=False)
        
        if self.is_decal_folder():
            collection.get_remove_element(self).draw_ui(remove_layout, al.UIIcon(al.BIcon.X))
        else:
            if has_error:
                remove_layout.scale_x = 0.8
            text = "Remove Expansion" if has_error else ''
            prefops.UninstallExpansion(index=collection.index(self)).draw_ui(remove_layout, al.UIOptionsOperator(text=text, icon=al.BIcon.X))

    @al.PD.update_property(directory)
    @al.PD.update_property(category_name)
    def validate_category_name(self, context: bt.Context):
        if not hasattr(bpy.data, "is_saved"):
            return
        
        # force paths to be absolute
        if self.directory.is_relative:
            self.directory.raw = self.directory.absolute

        from . import library_manager
        library_manager.ASSETS_UP_TO_DATE = False
        if self.category_name():
            return
        try:
            dir_str = str(self.directory.absolute)
        except OSError:
            self.category_name.value = "Custom"
            return
        if not dir_str:
            self.category_name.value = "Custom"
            return
        self.category_name.value = self.directory.absolute.name


@al.register
class InterfacePreferences(al.PropertyGroup):

    use_static_panel = al.BoolProperty(name='Display N-Panel', default=True, description='Toggle the panel on the right side of the 3D View')
    use_filters = al.BoolProperty(name='Display Filters', default=True, description='Use Filters for organizing Sanctus Assets')
    display_material_slots = al.BoolProperty(name='Diplay Material Slots', default=True, description='Display a UI element for the active material of the active object in the Material Panel')
    center_mouse_on_gizmos = al.BoolProperty(name='Center Mouse when using Gizmos', default=False, description='When using the interactive decal or GN asset gizmos, your mouse gets centered when enabled')
    asset_thumbnail_scale = al.FloatProperty(name='Asset Thumbnail Scale', default=4.0, min=1.0)


@al.register
class ShortcutsPreferences(al.PropertyGroup):
    pass

@al.register
@al.depends_on(ExternalLibrary)
class ExpansionPreferences(al.PropertyGroup):

    expansion_libraries = al.CollectionProperty(type=ExternalLibrary, name="Expansions")

    @al.PD.set_on_add_element(expansion_libraries)
    @al.PD.set_on_remove_element(expansion_libraries)
    def on_expansion_libraries_change(c: al.CollectionProperty[ExternalLibrary], e: ExternalLibrary):
        from . import library_manager
        library_manager.ASSETS_UP_TO_DATE = False

    def draw_ui_expansions(self, layout: bt.UILayout, context: bt.Context):
        from .operators import preferences as prefops

        header = al.UI.row(layout)
        al.UI.label(header, "Expansions:")
        al.UI.operator(header, bo.wm.url_open, {'url':constants.EXPANSION_LINK}, al.UIOptionsOperator(text="About Expansions", icon=al.BIcon.QUESTION))

        expansions = [x for x in self.expansion_libraries() if not x.is_decal_folder()]

        col = al.UI.column(layout, align=False)
        col.scale_y = 1.3
        for lib in expansions:
            lib.draw_ui(col, self.expansion_libraries)

        layout.separator()
        install_layout = al.UI.column(layout)
        install_layout.scale_y = 1.3
        prefops.InstallExpansion().draw_ui(al.UI.indent(install_layout, 0.1, al.UIAlignment.CENTER), al.UIOptionsOperator(text='Install Expansion', icon=al.BIcon.ADD))

    def draw_ui_decals(self, layout: bt.UILayout, context: bt.Context):
        al.UI.label(layout, "Custom Decals:")
        from .operators import preferences as prefops
        prefops.AddDecalDirectory().draw_ui(layout, al.UIOptionsOperator(text="Add Custom Decal Directory", icon=al.BIcon.ADD))
        for lib in (x for x in self.expansion_libraries() if x.is_decal_folder()):
            lib.draw_ui(layout, self.expansion_libraries)


@al.depends_on(InterfacePreferences, ShortcutsPreferences, ExpansionPreferences, baking.settings.BakingPreferences)
@al.register
class SanctusLibraryPreferences(al.AddonPreferences):
    

    current_context = al.EnumProperty(enum=PreferencesContext, default=PreferencesContext.INTERFACE, name="Context", description="Current preferences tab")

    #contexts
    interface = al.PointerProperty(type=InterfacePreferences)
    shortcuts = al.PointerProperty(type=ShortcutsPreferences)
    baking = al.PointerProperty(type=baking.settings.BakingPreferences)
    expansions = al.PointerProperty(type=ExpansionPreferences)

    developer_mode = al.BoolProperty(name='Developer Mode', default=False, description='Enables Developer Options. Do not touch!')

    favorites = al.JSONDataProperty(name='Favorites', default={})

    def draw(self, context: bt.Context):
        layout: bt.UILayout = self.layout

        sl_col = al.UI.column(layout.box(), align=True)
        sle_row = al.UI.row(sl_col, align=True)
        operators.preferences.ImportPreferences().draw_ui(sle_row, al.UIOptionsOperator(icon=al.BIcon.FILE_FOLDER))
        operators.preferences.ExportPreferences().draw_ui(sle_row, al.UIOptionsOperator(icon=al.BIcon.FILE))

        operators.library.InstallPillow().draw_ui(layout)

        layout.separator()

        context_col = al.UI.column(layout, align=True)
        context_row = al.UI.row(context_col, align=True)
        context_row.scale_y = 1.3

        self.current_context.draw_ui(context_row, options=al.UIOptionsProp(expand=True))
        context_layout = context_col.box()

        if self.current_context() == PreferencesContext.INTERFACE:
            interface = self.interface()
            col = al.UI.column(context_layout)
            interface.use_static_panel.draw_ui(col)
            interface.use_filters.draw_ui(col)
            interface.display_material_slots.draw_ui(col)
            interface.center_mouse_on_gizmos.draw_ui(col)
            interface.asset_thumbnail_scale.draw_ui(col)

        elif self.current_context() == PreferencesContext.SHORTCUTS:
            for shortcut in KEYMAP_MANAGER.shortcuts:
                shortcut.draw_user_binding(context_layout, expand=True, use_icons=False)
            
        elif self.current_context() == PreferencesContext.BAKING:
            baking.ui.BakingPreferencesDrawer(self.baking(), al.UI.column(context_layout), context).draw()
        
        elif self.current_context() == PreferencesContext.DECALS:
            self.expansions().draw_ui_decals(context_layout.box(), context)
            self.draw_optional_reload_library_warning(context_layout)

        elif self.current_context() == PreferencesContext.EXPANSIONS:
            self.expansions().draw_ui_expansions(context_layout.box(), context)


    def draw_optional_reload_library_warning(self, layout: bt.UILayout):
        from . import library_manager
        if not library_manager.ASSETS_UP_TO_DATE:
            col = al.UI.column(layout)
            al.UI.label(al.UI.alert(col), 'Reload the library assets in order to reflect the library changes', icon=al.BIcon.ERROR)
            operators.library.ReloadLibrary().draw_ui(col, al.UIOptionsOperator(text='Reload Library'))


    def get_developer_mode(self):
        return self.developer_mode() and dev_info.DEVELOPER_MODE
    
    def load_prefs(self):
        if not self.preference_file.exists():
            return
        print('Loading SL Preferences...')
        try:
            data = self.preference_file.read_json()
        except json.decoder.JSONDecodeError:
            print('Decoder Error when parsing SL Preferences! Cannot load preferences.')
            return
        self.deserialize(data)
        print("Finished!")
        
        #TODO fix favorites
        keys = self.favorites().keys()
        if any('::' in x for x in keys):
            print('Old Favorite Keys Found')
            new_keys = [(Path(*x.split('::')[1:]) if '::' in x else x) for x in keys]
            self.favorites.value = {str(x) : True for x in new_keys}
    
    def save_prefs(self):
        print('Saving SL Preferences...')
        data = self.serialize()
        self.preference_file.write_json(data)
        print("Finished!")

@al.register
def register_keymaps(register: bool):
    from . import panel_ui
    global KEYMAP_MANAGER

    kc = al.get_wm().keyconfigs.addon
    if kc and not bpy.app.background:
        if register:
            KEYMAP_MANAGER = al.KeymapManager()
            KEYMAP_MANAGER.add_shortcut_builtin(
                bo.wm.call_panel,
                {'name': panel_ui.View3DUI.bl_idname},
                al.BEventType.S,
                al.BEventValue.PRESS,
                region_type=al.BRegionType.WINDOW,
                name='Floating Panel Shortcut',
                ctrl=True,
                alt=True
            )

        else:
            if KEYMAP_MANAGER is None:
                return
            KEYMAP_MANAGER.clear_shortcuts()

@al.register
def register_load_preferences(register: bool):
    prefs = al.get_prefs()
    if register:
        prefs.load_prefs()
    else:
        prefs.save_prefs()
