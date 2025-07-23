from .. import auto_load as al
from ..auto_load.common import *

from .. import base_ops
from .. import meta_data as md


@al.register_operator
class SetMetaData(base_ops.SanctusOperator):
    bl_description = 'Set Meta Data on the selected Sanctus Library Item'

    engine = al.EnumFlagProperty(enum=md.MetaEngine, name='Engine', default=md.MetaEngine.all())
    complexity = al.EnumProperty(enum=md.MetaComplexity, name='Complexity', default=0)
    gn_type = al.EnumFlagProperty(enum=md.GeometryNodeAssetType, name='GN Type', default={md.GeometryNodeAssetType.ADD_NEW})
    use_displacement = al.BoolProperty(name='Use Displacement')
    require_uvs = al.BoolProperty(name='Require UVs')
    match_materials = al.BoolProperty(name='Match Materials')
    meta_description = al.StringProperty(name='Description', default='')
    meta_documentation_link = al.StringProperty(name='Documentation', default='')

    asset_path = al.StringProperty(options={al.BPropertyFlag.HIDDEN})

    def invoke(self, context: bt.Context, event: bt.Event) -> set[str]:
        item = self.get_item()
        meta = item.meta

        self.meta_description.value = meta.description
        self.meta_documentation_link.value = meta.documentation_link

        if event.shift:
            return self.execute(context)
        else:
            wm = al.get_wm()
            self.engine.value = meta.get_engine()
            self.complexity.value = meta.get_complexity()
            self.gn_type.value = meta.get_gn_type()
            self.use_displacement.value = meta.use_displacement
            self.require_uvs.value = meta.require_uvs
            self.match_materials.value = meta.match_materials
            return wm.invoke_props_dialog(self)

    def get_item(self):
        from .. import library_manager
        return library_manager.MANAGER.all_assets[Path(self.asset_path())]

    def draw(self, context):
        layout: bt.UILayout = al.UI.column(self.layout)
        item = self.get_item()
        al.UI.label(layout, text=item.asset_name)
        layout.use_property_split = True

        for p in self.get_annotated_properties().values():
            if p.check_option(al.BPropertyFlag.HIDDEN):
                continue

            if p.attr_name == "match_materials":
                if md.GeometryNodeAssetType.APPLY_PARENTED_CURVE.name in self.gn_type.serialize():
                    p.draw_ui(layout)
            else:  
                p.draw_ui(layout)

    def execute(self, context: bt.Context):
        from .. import library_manager as lm
        from .. import library
        meta_data = md.SanctusMetaData(
            engine=[x() for x in self.engine()],
            complexity=self.complexity()(),
            gn_type=[x() for x in self.gn_type()],
            use_displacement=self.use_displacement(),
            require_uvs=self.require_uvs(),
            description=self.meta_description(),
            documentation_link=self.meta_documentation_link(),
            match_materials=self.match_materials(),
        )

        item = self.get_item()
        if item.meta_file is None:
            item.meta_file = library._create_metapath(item.directory, item.asset_name)
        if(not item.meta_file.exists()):
            item.meta_file.touch(exist_ok=False)
        meta_data.to_file(item.meta_file)
        item.meta = meta_data
        
        for instance in lm.MANAGER.get_all_instances(item):
            lm.MANAGER.reload_icon(instance)

        return {'FINISHED'}

@al.register_operator
class ValidateAllMetaData(base_ops.SanctusOperator):

    def run(self, context: bt.Context):
        from .. import library_manager
        from .. import meta_data
        manager = library_manager.MANAGER

        failed_assets: list[str] = []

        for asset in manager.all_assets.values():
            if not asset.has_meta_file:
                continue
            failed_components = meta_data.validate_meta_data(asset.meta)

            if len(failed_components) > 0:
                asset.meta.to_file(asset.meta_file)
                component_str = ','.join(failed_components)
                failed_assets.append(f' - {asset.asset_name}: {component_str}')

        if len(failed_assets):
            print("Found invalid meta data and assigned default values on the following assets:")
            print("\n".join(failed_assets))
            self.report({"WARNING"}, "Found invalid meta data. Check console for details!")
        else:
            self.report({"INFO"}, "All meta data is valid.")
