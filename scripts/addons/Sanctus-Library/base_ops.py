'''
Here are some basic base classes for defining default bahaviors for Operators of the Sanctus Library addon.
'''

from . import auto_load as al
from .auto_load.common import *
from . import asset

def link_and_select_object(context: bt.Context, obj: bt.Object, collection: bt.Collection = None):
    if collection is None:
        collection = context.collection
    collection.objects.link(obj)
    context.view_layer.objects.active = obj
    for o in bpy.data.objects:
        o: bt.Object
        o.select_set(o == obj)

class SanctusOperator(al.Operator):
    bl_options = {al.BOperatorTypeFlag.UNDO()}

class SanctusFilepathOperator(SanctusOperator, al.FilepathOperator):
    pass

class SanctusFolderOperator(SanctusOperator, al.FolderOperator):
    pass

class SanctusAssetImportOperator(SanctusOperator):

    asset_type = asset.Type.MATERIALS
    use_reimport_prompt = True
    path = al.StringProperty()
    reimport_asset = al.BoolProperty(default=False)

    def invoke(self, context: bt.Context, _event):

        importer = self.get_importer()
        if (importer.exists_in_file and self.use_reimport_prompt) or (not importer.is_compatible(context)):
            return al.get_wm().invoke_props_dialog(self)
        return self.execute(context)

    def draw(self, context: bt.Context):
        from . import meta_data
        layout = self.layout
        importer = self.get_importer()
        if importer.exists_in_file and self.use_reimport_prompt:
            al.UI.label(layout, 'Asset found in Blend File. Re-Import?')
            r = layout.row(align=True)
            self.reimport_asset.draw_ui(r, al.UIOptionsProp(text='Use Existing', toggle=1, invert_checkbox=True))
            self.reimport_asset.draw_ui(r, al.UIOptionsProp(text='Reimport Asset', toggle=1, invert_checkbox=False))

        if not importer.is_compatible(context):
            engine = context.scene.render.engine
            c = layout.column()
            c.scale_y = 0.8
            compatible_engines_text = ','.join([f'"{x.get_name()}"' for x in importer.asset_instance.asset.meta.get_engine()])
            al.UI.label(c, f'This asset is not compatible with "{meta_data.get_render_engine_name(engine)}".')
            al.UI.label(c, text=f'Switching to {compatible_engines_text} is recommended.')

    def get_importer(self):
        return asset.ImportManager(Path(self.path()), self.asset_type)
