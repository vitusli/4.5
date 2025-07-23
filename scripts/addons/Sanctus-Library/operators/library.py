
from .. import auto_load as al
from ..auto_load.common import *

from .. import base_ops

from .. import constants
from ..t3dn_bip import ops as preview_ops

@al.register_operator
class SwitchLibraryItem(base_ops.SanctusOperator):
    bl_description = 'Switches the enum for a given library in the given direction'

    path = al.StringProperty()
    backwards = al.BoolProperty()

    def run(self, context: bt.Context):

        from .. import library_manager as lm
        instance_path = Path(self.path())
        category: dict = lm.MANAGER.runtime_library.search_hierarchy(instance_path.parent)
        keys = list(category.keys())
    
        index = next(i for i, key in enumerate(keys) if key == instance_path.name)
        offset = -1 if self.backwards() else +1
        new_name = keys[(index + offset) % len(keys)]

        lm.get_library_attributes().set_active(instance_path.with_name(new_name))
        

    def draw_ui(self, layout: bt.UILayout):
        options = al.UIOptionsProp(text='', icon=al.BIcon.TRIA_LEFT if self.backwards() else al.BIcon.TRIA_RIGHT)
        return base_ops.SanctusOperator.draw_ui(self, layout, options)


@al.register_operator
class SetLibraryItemFavorite(base_ops.SanctusOperator):
    bl_description = 'Set the current library item as favorite. Favorites will get sorted to the front'

    path = al.StringProperty()
    favorite = al.BoolProperty()

    def run(self, context: bt.Context):
        
        from .. import library_manager as lm
        asset_instance = lm.MANAGER.runtime_library.search_hierarchy(Path(self.path()))
        lm.set_favorite(asset_instance, self.favorite())
        lm.reload_library_attributes()

@al.register_operator
class OpenLibraryItemDocumentation(base_ops.SanctusOperator):
    bl_description = 'Open a weblink to the documentation page of the current item'

    asset_path = al.StringProperty()

    def run(self, context: bt.Context):
        from .. import library_manager as lm
        asset = lm.MANAGER.all_assets[Path(self.asset_path())]
        if asset.meta.documentation_link == '':
            return
        bpy.ops.wm.url_open(url=asset.meta.documentation_link)


@al.register_operator
class SetActiveLibraryItem(base_ops.SanctusOperator):
    bl_description = 'Select the asset as the current element in the Material panel'

    path = al.StringProperty()
    disable_search = al.BoolProperty(default=False)
    def run(self, context: bt.Context):
        from .. import library_manager as lm
        from .. import filters

        lm.get_library_attributes().set_active(Path(self.path()))
        if self.disable_search():
            filters.SanctusLibraryFilters.get_from(al.get_wm()).search_enabled.value = False

@al.register_operator
class OpenDocumentation(base_ops.SanctusOperator):
    bl_label = 'Documentation and Tutorials'
    bl_description = 'Open a weblink to the official Sanctus Library Documentation'

    def run(self, context: bt.Context):
        bpy.ops.wm.url_open(url=constants.DOCUMENTATION_LINK)


@al.register_operator
class OpenVideoGuide(base_ops.SanctusOperator):
    bl_description = 'Open a weblink to the official Sanctus Library Video Guide'

    def run(self, context: bt.Context):
        bpy.ops.wm.url_open(url=constants.VIDEO_GUIDE_LINK)


@al.register_operator
class OpenDiscordLink(base_ops.SanctusOperator):
    bl_label = 'Join Sanctus Library Discord'
    bl_description = "Open a weblink to the official Sanctus Library Discord Server"

    def run(self, context: bt.Context):
        bpy.ops.wm.url_open(url=constants.DISCORD_LINK)


@al.register_operator
class OpenPatreonLink(base_ops.SanctusOperator):
    bl_label = 'Support Sanctus Library'
    bl_description = "Open a weblink to the official Sanctus Library Patreon Page"

    def run(self, context: bt.Context):
        bpy.ops.wm.url_open(url=constants.PATREON_LINK)

@al.register_operator
class OpenBakingGuideLink(base_ops.SanctusOperator):
    bl_label = "How to Bake Materials"
    bl_description = "Open a weblink to the official Sanctus Library Baking Guide"

    def run(self, context: bt.Context):
        bpy.ops.wm.url_open(url=constants.BAKING_GUIDE_LINK)

@al.register_operator
class OpenMaterialEditorGuideLink(base_ops.SanctusOperator):
    bl_label = 'How to use the Material Editor'
    bl_description = "Open a weblink to the official Sanctus Library Material Editor Guide"

    def run(self, context: bt.Context):
        bo.wm.url_open(url=constants.MATERIAL_EDITOR_GUIDE_LINK)

@al.register_operator
class OpenShaderToolsGuideLink(base_ops.SanctusOperator):
    bl_label = "How to use Shader Tools"
    bl_description = "Open a weblink to the official Sanctus Library Shader Tools Guide"

    def run(self, context: bt.Context):
        bo.wm.url_open(url=constants.SHADER_TOOLS_GUIDE_LINK)
        

@al.register_operator
class ReloadLibrary(base_ops.SanctusOperator):
    bl_description = 'Reload the entire library'

    def run(self, context: bt.Context):
        from .. import library_manager
        library_manager.reload_library()

@al.register_operator
class OpenPreferences(al.Operator):
    bl_description = 'Open the preferences for the Sanctus Library addon'

    def run(self, context: bt.Context):
        wm = context.window_manager
        bl_info = al.get_adddon_bl_info()
        bpy.ops.screen.userpref_show(section='ADDONS')

        wm.addon_search = bl_info['name']
        wm.addon_filter = 'All'
        wm.addon_support = {'OFFICIAL', 'COMMUNITY'}
        if not bl_info.get("show_expanded", False):
            bpy.ops.preferences.addon_expand(module=__package__)
        al.Window.redraw_all_regions()

@al.register_operator
class InstallPillow(preview_ops.InstallPillow, base_ops.SanctusOperator):
    bl_description = 'Install the Pillow python library. Makes loading the addon much faster'

    @staticmethod
    def try_connect_to_internet() -> str:
        import requests
        error = ''
        try:
            requests.get(url='http://google.com', timeout=1)
        except requests.exceptions.ConnectionError:
            error = 'No internet connection...'
        except requests.exceptions.ReadTimeout:
            error = 'Internet connection timeout...'
        except:
            error = 'An unknown error has occured. Please report this!'
        return error

    def draw_ui(self, layout: bt.UILayout):

        def pillow_installed() -> bool:
            try:
                from PIL import Image  # Try to import module, if not existing then exception will be thrown
                return True
            except:
                return False

        pil_installed = pillow_installed()
        if pil_installed:
            layout = al.UI.row(layout)
            al.UI.label(layout, 'Pillow Installed')
        else:
            layout = al.UI.column(layout.box(), align=True)
            al.UI.label(al.UI.alert(layout), 'Install Pillow to improve loading times and visuals (favorite icons).', icon=al.BIcon.ERROR)
        return base_ops.SanctusOperator.draw_ui(self, layout, al.UIOptionsProp(text=self.bl_label if not pil_installed else 'Update Pillow'))

    def execute(self, context: bt.Context):
        if (error := self.try_connect_to_internet()) == '':
            return super().execute(context)
        else:
            self.report({"ERROR"}, error)
            return {"CANCELLED"}


@al.register_operator
class CopyText(base_ops.SanctusOperator):
    text = al.StringProperty()

    def run(self, context: bt.Context):
        al.get_wm().clipboard = self.text()
        self.report({'INFO'}, f'Copied to clipboard: {self.text()}')
