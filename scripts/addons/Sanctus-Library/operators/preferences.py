from .. import auto_load as al
from ..auto_load.common import *
from .. import base_ops
import json
from .. import constants

@al.register_operator
class ExportPreferences(base_ops.SanctusFilepathOperator):

    def set_defaults(self, context: bt.Context, event: bt.Event):
        prefs = al.get_prefs()
        version = prefs.addon.bl_info['version']
        version_string = '_'.join([str(x) for x in version])
        self.filepath = f'{al.config.ADDON_PACKAGE}_preferences_{version_string}{preferences.PREFERENCES_EXTENSION}'
        self.filter_glob = f'*{preferences.PREFERENCES_EXTENSION}'
        self.hide_props_region = True
        self.filter_folder = False

    def draw(self, context: bt.Context) -> None:
        l = self.layout
        l = l.box()
        al.UI.label(l, 'Save the Sanctus Preferences to an external file.')
        al.UI.label(l, 'This file serves as a backup.')
        al.UI.label(l, 'Preferences get saved automatically.')

    def run(self, context: bt.Context):
        prefs = al.get_prefs()
        file = Path(self.Filepath)
        file.unlink(missing_ok=True)
        file.write_text(json.dumps(prefs.serialize()))

@al.register_operator
class ImportPreferences(base_ops.SanctusFilepathOperator):

    def set_defaults(self, context: bt.Context, event: bt.Event):
        self.hide_props_region = True
        self.filter_glob = f'*{preferences.PREFERENCES_EXTENSION}'
        self.check_existing = False
        self.filter = False

    def draw(self, context: bt.Context) -> None:
        l = self.layout
        al.UI.label(l, 'Load Sanctus Preferences from a file.')


    def run(self, context: bt.Context):
        from .. import library_manager as lm
        prefs = al.get_prefs()
        backup = prefs.serialize()
        file = Path(self.Filepath)
        if not file.exists():
            self.report({'ERROR'}, f'Filepath "{str(file)}" does not exist')
        data = json.loads(file.read_text())
        try:
            prefs.deserialize(data)
            lm.reload_library()
        except:
            self.report({'ERROR'}, f'File content could not be used to load preferences.')
            prefs.deserialize(backup)

@al.register_operator
class AddDecalDirectory(base_ops.SanctusOperator):

    def run(self, context: bt.Context):
        prefs = al.get_prefs()
        lib = prefs.expansions().expansion_libraries.new()
        lib.is_decal_folder.value = True
        lib.directory.value = str(lib.directory.absolute)

@al.register_operator
class InstallExpansion(base_ops.SanctusFilepathOperator):
    bl_label = "Install"

    def set_defaults(self, context: bt.Context, event: bt.Event):
        from .. import library
        self.filter_glob = f'*{library.FILE_EXPANSION}'
        self.hide_props_region = False
        self.check_existing = False
        self.filter = False
        self.relative_path = False

    def draw(self, context: bt.Context):
        from .. import library
        l = self.layout
        al.UI.label(l, "Select Expansion File")
    
    def run(self, context: bt.Context):
        from .. import library_manager
        
        expansion_meta_file = Path(self.Filepath)
        print(f"Attempting to load expansion from '{str(expansion_meta_file)}'")

        if(not expansion_meta_file.exists()):
            self.report({"ERROR"}, f"Expansion not recognized! File does not exit. '{str(expansion_meta_file)}'")
            return

        if(not expansion_meta_file.is_file()):
            self.report({"ERROR"}, f"Expansion not recognized! Selected path is not a file. '{str(expansion_meta_file)}'")
            return

        expansion_folder = expansion_meta_file.parent
        prefs = al.get_prefs()
        expansion_prefs = prefs.expansions()
        if any(x.directory() == str(expansion_folder) for x in expansion_prefs.expansion_libraries()):
            self.report({"WARNING"}, f"Expansion already installed! '{str(expansion_folder)}'")
            return
        
        meta_info: dict[str, str] = json.loads(expansion_meta_file.read_text())

        lib = expansion_prefs.expansion_libraries.new()
        lib.is_decal_folder.value = False
        lib.directory.value = str(expansion_folder)

        lib.expansion_name.value = meta_info['name']
        lib.expansion_version.value = str(meta_info['version'])

        library_manager.reload_library()


@al.register_operator
class UninstallExpansion(base_ops.SanctusOperator):
    
    index = al.IntProperty()

    def invoke(self, context: bt.Context, event: bt.Event):
        return al.get_wm().invoke_confirm(self, event)

    def run(self, context: bt.Context):
        from .. import library_manager
        prefs = al.get_prefs()
        prefs.expansions().expansion_libraries.remove_at(self.index())
        library_manager.reload_library()

@al.register_operator
class ErrorPopup(base_ops.SanctusOperator):

    text = al.StringProperty()
    alert = al.BoolProperty(default=False)

    def invoke(self, context: bt.Context, event: bt.Event):
        return al.get_wm().invoke_popup(self, width=600)
    
    def draw(self, context: bt.Context):
        layout = self.layout
        if(self.alert()):
            layout = al.UI.alert(layout)
        al.UI.text(layout, self.text())

@al.register_operator
class ShowExpansionInfo(base_ops.SanctusOperator):

    def invoke(self, context: bt.Context, event: bt.Event):
        return al.get_wm().invoke_popup(self, width=600)
    
    def draw(self, context: bt.Context):
        al.UI.text(self.layout, constants.INSTALL_EXPANSION_TEXT)

from .. import preferences