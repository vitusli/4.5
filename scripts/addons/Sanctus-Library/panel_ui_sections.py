'''
Implementations of different UI sections of the Sanctus Library addon UI
'''


from . import auto_load as al
from .auto_load.common import *

from . import library_manager as lm
from . import operators as ops
from . import dev_info
from . import meta_data
from . import constants
from . import filters
from . import node_utils


DEAD_NODE_SOCKET_INTERFACES = [
    bt.NodeTreeInterfaceSocketMaterial,
    bt.NodeTreeInterfaceSocketImage,
    bt.NodeTreeInterfaceSocketCollection,
    bt.NodeTreeInterfaceSocketObject
]


def draw_item_popup(layout: bt.UILayout, path: Path):
    attrs = lm.get_library_attributes()
    layout = al.UI.row(layout, align=True)

    layout.scale_y = 8.0
    instance_path = attrs.get(path)
    instance = lm.MANAGER.runtime_library.search_hierarchy(instance_path)

    switch_backwards = ops.library.SwitchLibraryItem(path=str(instance_path), backwards=True)
    switch_forward = ops.library.SwitchLibraryItem(path=str(instance_path), backwards=False)

    col = al.UI.column(layout, align=True)
    item_docs_ui = al.UI.column(col, align=True)
    item_docs_ui.scale_y = 0.25
    col.scale_y = 0.835
    link = instance.asset.meta.documentation_link
    ops.library.OpenLibraryItemDocumentation(asset_path=str(instance.asset.asset_path)).draw_ui(
        al.UI.enabled(item_docs_ui, link != ''),
        al.UIOptionsOperator(text='', icon=al.BIcon.QUESTION)
    )
    switch_backwards.draw_ui(col)
    prefs = al.get_prefs()
    layout.template_icon_view(attrs, str(path), show_labels=True, scale=1.0, scale_popup=prefs.interface().asset_thumbnail_scale())
    col = al.UI.column(layout, align=True)
    star_ui = al.UI.column(col, align=True)
    star_ui.scale_y = 0.25
    col.scale_y = 0.835
    is_fav = lm.get_favorite(instance)
    ops.library.SetLibraryItemFavorite(path=str(instance.path), favorite=not is_fav).draw_ui(
        star_ui,
        al.UIOptionsOperator(text='', icon=al.BIcon.SOLO_ON if is_fav else al.BIcon.SOLO_OFF)
    )
    switch_forward.draw_ui(col)


def draw_item_description(layout: bt.UILayout, text: str):
    desc_box = layout.box()
    desc_col = desc_box.column(align=True)
    desc_col.scale_y = 0.9
    desc_box.enabled = False
    for line in text.splitlines():
        al.UI.label(desc_col.row(), text=line)

def draw_obj_material_list(layout: bt.UILayout, obj: bt.Object, collapsed: bool = False):
    layout.context_pointer_set('material', obj.active_material)
    layout.context_pointer_set('material_slot', obj.material_slots[obj.active_material_index])
    if collapsed:
        layout.popover(panel=bt.NODE_PT_material_slots.__name__)
    else:
        is_sortable = len(obj.material_slots) > 1
        num_rows = 5 if is_sortable else 3
        row = al.UI.row(layout)
        row.template_list("MATERIAL_UL_matslots", '', obj, 'material_slots', obj, 'active_material_index', rows=num_rows)
        col = al.UI.column(row)
        al.UI.operator(col, bo.object.material_slot_add, options=al.UIOptionsProp(text='', icon=al.BIcon.ADD))
        al.UI.operator(col, bo.object.material_slot_remove, options=al.UIOptionsOperator(text='', icon=al.BIcon.REMOVE))
        col.separator()
        al.UI.menu(col, bt.MATERIAL_MT_context_menu, options=al.UIOptionsProp(text='', icon=al.BIcon.DOWNARROW_HLT))

        if is_sortable:
            col.separator()
            al.UI.operator(col, bo.object.material_slot_move, {'direction': 'UP'}, options=al.UIOptionsOperator(text='', icon=al.BIcon.TRIA_UP))
            al.UI.operator(col, bo.object.material_slot_move, {'direction': 'DOWN'}, options=al.UIOptionsOperator(text='', icon=al.BIcon.TRIA_DOWN))

    row = al.UI.row(layout)
    row.template_ID(obj, 'active_material', new='material.new')

class SanctusPanelSection:
    '''Each asset class has a `SanctusPanelSection` where contextual UI is being displayed for every class. However all of the classes have UI similarities which are
implemented in the base `SanctusPanelSection` class. The classes in this module are being used in `panel_ui.py`'''

    asset_class: str = 'invalid'
    name: str = 'Test'
    description: str = 'description of test'
    minimum_blend_version: tuple = (1, 0)
    full_version_asset_text: str = '...'
    asset_search_enabled: bool = False

    @classmethod
    def poll(cls, context: bt.Context) -> bool:
        return True

    @classmethod
    def draw_ui(cls, layout: bt.UILayout, context: bt.Context) -> None:
        lm.AssetClasses.current_ui_class = cls.asset_class
        attributes = lm.get_library_attributes()
        manager = lm.MANAGER
        sanctus_filters = filters.SanctusLibraryFilters.get_from(al.get_wm())


        current_path = cls.asset_class
            
        search_icon_drawn = False
        while True:
            if not isinstance(manager.runtime_library.search_hierarchy(attributes.get(current_path)), dict): break

            row = al.UI.row(layout, align=True)
            al.UI.prop(row, attributes, str(current_path), al.UILabel(''))

            if not search_icon_drawn and cls.asset_search_enabled:
                sanctus_filters.search_enabled.draw_ui(row, al.UIIcon(al.BIcon.VIEWZOOM))
                search_icon_drawn = True
            
            current_path = attributes.get(current_path)

        if sanctus_filters.search_enabled() and cls.asset_search_enabled:
            sanctus_filters.draw_search(layout)

        draw_item_popup(layout, current_path)

        current_path = attributes.get(current_path)
        asset_instance: lm.lib.AssetInstance = manager.runtime_library.search_hierarchy(current_path)
        al.UI.label(layout, asset_instance.display_name, alignment=al.UIAlignment.CENTER)
        cls.draw_operators(layout, context, current_path)
        if asset_instance.asset.meta.has_description():
            draw_item_description(layout, asset_instance.asset.meta.get_description())

        if dev_info.LITE_VERSION:
            cls.draw_available_assets(al.UI.enabled(layout))
        cls.draw_details(layout, context)
        prefs = al.get_prefs()

    @classmethod
    def draw_available_assets(cls, layout: bt.UILayout):
        al.UI.label(
            layout,
            f'Available {cls.name}: {cls.get_light_version_asset_count()}/{cls.full_version_asset_text}',
            alignment=al.UIAlignment.CENTER,
            alert=True
        )

    @classmethod
    def get_light_version_asset_count(cls):
        from . import library_manager
        return library_manager.MAIN_LIBRARY_ASSET_COUNTS[cls.asset_class]

    @classmethod
    def draw_operators(cls, layout: bt.UILayout, context: bt.Context, path: Path) -> None:
        raise NotImplementedError()

    @classmethod
    def draw_details(cls, layout: bt.UILayout, context: bt.Context) -> None:
        pass


class SanctusMaterialSection(SanctusPanelSection):
    asset_class: str = lm.AssetClasses.MATERIALS
    name: str = 'Materials'
    description: str = ''
    full_version_asset_text = constants.FULL_MATERIAL_TEXT
    asset_search_enabled = True

    @classmethod
    def draw_operators(cls, layout: bt.UILayout, context: bt.Context, path: Path) -> None:
        c = layout.column(align=True)
        
        ops.materials.ApplyMaterial(path=str(path)).draw_ui(c)
        ops.materials.ImportMaterial(path=str(path)).draw_ui(c)

        if dev_info.LITE_VERSION:
            c.separator(factor=2)

            al.UI.operator(
                c,
                bpy.ops.wm.url_open,
                dict(url=constants.FULL_MATERIAL_LIST_LINK),
                al.UIOptionsOperator(text='Full list of Materials')
            )

    @classmethod
    def get_shader_output_node(cls, nt: bt.ShaderNodeTree, engine: str):
        if engine == meta_data.EEVEE_ENGINE_ENUM:
            engine = "EEVEE"
        if engine not in ("ALL", "EEVEE", "CYCLES"):
            engine = "ALL"
        node: Union[bt.ShaderNodeOutputMaterial, None] = nt.get_output_node(engine)
        if node is None:
            raise cls.ShaderNodeFindError('Material has no output node.')
        return node
    class ShaderNodeFindError(Exception):
        pass

    @classmethod
    def get_first_material_node(cls, output_node: bt.ShaderNodeOutputMaterial) -> bt.Node:
        surfacce_input = output_node.inputs['Surface']
        if len(surfacce_input.links) < 1:
            raise cls.ShaderNodeFindError('No nodes connected to output node.')
        return surfacce_input.links[0].from_node

    @classmethod
    def shader_input_is_category(cls, input: bt.NodeSocketStandard) -> bool:
        name = input.name
        return input.hide_value and node_utils.input_name_is_category(name)
    
    @classmethod
    def draw_material_properties(cls, layout: bt.UILayout, obj: bt.Object, engine: str):

        if obj.active_material is None:
            return

        box = layout.box()

        mat = obj.active_material
        nt: bt.ShaderNodeTree = mat.node_tree
        try:
            output_node = cls.get_shader_output_node(nt, engine)
            connected_node = cls.get_first_material_node(output_node)
        except cls.ShaderNodeFindError as e:
            al.UI.label(box, e.args[0], alert=True)
            return
        c = al.UI.column(box, align=False)
        show = True

        def draw_parameter_interface(node: bt.Node):
            nonlocal show
            for i in node.inputs:
                i: bt.NodeSocket
                if cls.shader_input_is_category(i):
                    display_name = i.name[2:-2]
                    show = al.UI.prop_bool_dropdown(c, i, 'show_expanded', display_name, display_name)
                    continue
                if not show:
                    continue
                if len(i.links) > 0:
                    connected_node: bt.Node = i.links[0].from_node
                    c.separator(factor=0.5)
                    draw_parameter_interface(connected_node)
                    c.separator(factor=0.5)
                    continue
                if i.hide_value:
                    continue
                if not i.enabled:
                    continue
                al.UI.prop(al.UI.row(c), i, 'default_value', al.UIOptionsProp(text=i.name, toggle=1))

        draw_parameter_interface(connected_node)

        if output_node.inputs['Displacement'].is_linked:
            al.UI.label(layout, 'Displacement Method:')
            if(bpy.app.version >= (4, 1, 0)):
                displacement_prop_object = mat
            else:
                displacement_prop_object = mat.cycles
            al.UI.prop(layout, displacement_prop_object, 'displacement_method', al.UIOptionsProp(text='', icon=al.BIcon.MOD_DISPLACE))

    @classmethod
    def draw_details(cls, layout: bt.UILayout, context: bt.Context):
        obj = context.object
        if obj is None:
            return
        if not obj in context.selected_objects:
            return

        global_mat_props = GlobalProperties.get_from(al.get_wm())
        prefs = al.get_prefs()

        if prefs.interface().display_material_slots():
            if global_mat_props.material_slots_expanded.draw_as_dropdown(layout, 'Material Slots:', 'Material Slots...'):
                draw_obj_material_list(layout, obj, collapsed=True)

        if global_mat_props.properties_expanded.draw_as_dropdown(layout, 'Active Material Properties:', 'Active Material Properties...'):
            cls.draw_material_properties(layout, obj, context.engine)


class SanctusGNAssetsSection(SanctusPanelSection):
    asset_class: str = lm.AssetClasses.GNTOOLS
    name: str = 'GN Assets'
    description: str = ''
    minimum_blend_version = constants.GN_BLEND_VERSION
    full_version_asset_text = constants.FULL_GN_ASSETS_TEXT
    asset_search_enabled = True

    @classmethod
    def draw_operators(cls, layout: bt.UILayout, context: bt.Context, path: Path) -> None:
        c = layout.column(align=True)

        asset = lm.MANAGER.runtime_library.search_hierarchy(path).asset
        md = asset.meta
        Type = meta_data.GeometryNodeAssetType

        if(Type.ADD_NEW() in md.gn_type):
            ops.geometry_nodes.GNAddNew(path=str(path)).draw_ui(c)

        if(Type.APPLY_MESH() in md.gn_type):
            ops.geometry_nodes.GNApplyMesh(path=str(path)).draw_ui(c)

        if(Type.APPLY_CURVE() in md.gn_type):
            ops.geometry_nodes.GNApplyCurve(path=str(path)).draw_ui(c)

        if(Type.APPLY_PARENTED_CURVE() in md.gn_type):
            ops.geometry_nodes.GNApplyParentedCurve(path=str(path)).draw_ui(c)

        if(Type.DRAW_FREE() in md.gn_type):
            ops.geometry_nodes.GNDrawFree(path=str(path)).draw_ui(c)
        
        if(Type.DRAW_SURFACE() in md.gn_type):
            ops.geometry_nodes.GNDrawSurface(path=str(path)).draw_ui(c)

        if(Type.PLACE_SURFACE() in md.gn_type):
            ops.geometry_nodes.GNPlaceSurface(path=str(path)).draw_ui(c)

        if dev_info.LITE_VERSION:
            c.separator(factor=2)
            al.UI.operator(
                c,
                bpy.ops.wm.url_open,
                dict(url=constants.FULL_GNASSETS_LIST_LINK),
                al.UIOptionsOperator(text='Full list of Assets')
            )

    @classmethod
    def draw_details(cls, layout: bt.UILayout, context: bt.Context):
        if context.object is None:
            return
        gn_mods = [x for x in context.object.modifiers if isinstance(x, bt.NodesModifier) and x.node_group is not None]
        if len(gn_mods) < 1:
            return
        for mod in gn_mods:
            col = al.UI.column(layout.box(), align=True)
            al.UI.label(col, mod.name, icon=al.BIcon.GEOMETRY_NODES)

            cls.draw_gn_inputs_blender4(col, mod)

    
    @classmethod
    def draw_gn_inputs_blender4(cls, layout: bt.UILayout, mod: bt.NodesModifier):
        mod_input_ids = dict(mod).keys()
        show = True
        for tree_item in mod.node_group.interface.items_tree:
            tree_item: bt.NodeTreeInterfaceItem
            if tree_item.item_type != 'SOCKET':
                continue
            if not tree_item.identifier in mod_input_ids:
                continue # geometry inputs for example are not available in the modifiers inputs
            if type(tree_item) in DEAD_NODE_SOCKET_INTERFACES:
                continue # these socket types do not really work for some reason TODO
            if isinstance(tree_item, bt.NodeTreeInterfaceSocketString) and node_utils.input_name_is_category(tree_item.name):
                display_name = node_utils.category_name_reduced(tree_item.name)
                show = al.UI.prop_bool_dropdown(layout, tree_item, 'hide_value', display_name, display_name, invert_value=True)
                continue
            if show:
                prop_layout = al.UI.row(layout)
                if tree_item.socket_type.startswith('NodeSocketVector'):
                    al.UI.label(prop_layout, tree_item.name + ':')
                    vector_layout = al.UI.column(prop_layout, align=True)
                    labels = [f'X', 'Y', 'Z', 'W']
                    for i in range(len(node_utils.get_gn_parameter(mod, tree_item.name))):
                        al.UI.prop_custom(vector_layout, mod, tree_item.identifier, al.UIOptionsProp(text=labels[i], index=i))
                else:
                    al.UI.prop_custom(prop_layout, mod, tree_item.identifier, al.UIOptionsProp(text=tree_item.name))


class SanctusDecalsSection(SanctusPanelSection):
    asset_class: str = lm.AssetClasses.DECALS
    name: str = 'Decals'
    description: str = ''
    minimum_blend_version = constants.DECAL_BLEND_VERSION
    full_version_asset_text = constants.FULL_DECALS_TEXT
    asset_search_enabled = True

    @classmethod
    def draw_operators(cls, layout: bt.UILayout, context: bt.Context, path: Path) -> None:

        button_column = al.UI.column(layout, align=True)

        ops.decal.AddDecal(path=str(path)).draw_ui(button_column)
        ops.decal.AddCustomDecal().draw_ui(button_column)
        ops.decal.SwapDecalImage(path=str(path)).draw_ui(button_column)
        ops.decal.RepositionDecal(path=str(path)).draw_ui(button_column)
        ops.decal.ToggleDecalNormals().draw_ui(button_column)

        if dev_info.LITE_VERSION:
            layout.separator(factor=2)
            al.UI.operator(
                layout,
                bpy.ops.wm.url_open,
                dict(url=constants.FULL_DECAL_LIST_LINK),
                al.UIOptionsOperator(text='Watch Decal Tool Demo')
            )

    @classmethod
    def draw_details(cls, layout: bt.UILayout, context: bt.Context) -> None:
        from . import decals
        if context.object is None:
            return
        decal_settings = decals.SanctusDecalSettings.get_from(context.object)
        if not decal_settings.is_decal():
            return
        decal_mod = decal_settings.get_decal_nodes_modifier()
        if decal_mod is None:
            return

        cls.draw_decal_inputs_blender4(al.UI.column(layout.box()), decal_mod)
    
    @classmethod
    def draw_decal_inputs_blender4(cls, layout: bt.UILayout, decal_mod: bt.NodesModifier):
        SanctusGNAssetsSection.draw_gn_inputs_blender4(layout, decal_mod)


class SanctusShaderSection(SanctusPanelSection):
    asset_class: str = lm.AssetClasses.SHADER
    name: str = 'Shader Tools'
    description: str = ''
    full_version_asset_text = constants.FULL_STOOLS_TEXT

    @classmethod
    def draw_operators(cls, layout: bt.UILayout, context: bt.Context, path: Path) -> None:
        ops.nodes.AddShaderNodeGroup(path=str(path)).draw_ui(layout)

class SanctusCompositorSection(SanctusPanelSection):
    asset_class: str = lm.AssetClasses.COMPOSITOR
    name: str = 'Compositor Tools'
    description: str = ''
    full_version_asset_text = constants.FULL_CTOOLS_TEXT

    @classmethod
    def draw_operators(cls, layout: bt.UILayout, context: bt.Context, path: Path) -> None:
        ops.nodes.AddCompositorNodeGroup(path=str(path)).draw_ui(layout)


class SanctusMaterialEditorSection(SanctusPanelSection):
    asset_class: str = lm.AssetClasses.SMODULES
    name: str = 'Material Editor'
    description: str = ''
    full_version_asset_text = constants.FULL_SMODULES_TEXT

    @classmethod
    def draw_operators(cls, layout: bt.UILayout, context: bt.Context, path: Path) -> None:
        ops.nodes.AddSmartModuleNodeGroup(path=str(path)).draw_ui(layout)
        ops.nodes.ConnectSmartModules().draw_ui(layout)


@al.register_property(bt.WindowManager)
class ActiveMaterialPropertiesExpanded(al.BoolProperty):
    obj: bt.WindowManager

    def __init__(self):
        return super().__init__(
            name='Active Material Properties Expanded',
            default=False
        )

    def draw_ui(self, layout: bt.UILayout) -> bt.UILayout:
        super().draw_ui(layout, al.UIOptionsProp(
            text='',
            icon=al.BIcon.TRIA_DOWN if self.value else al.BIcon.TRIA_RIGHT,
            invert_checkbox=self.value,
            emboss=False
        ))

    @classmethod
    def get(cls, parent: bt.WindowManager, attr_name: str = None):
        return super().get(parent, attr_name)


@al.register_property_group(bt.WindowManager)
class GlobalProperties(al.PropertyGroup):

    properties_expanded = al.BoolProperty(name='Properties Expanded')
    material_slots_expanded = al.BoolProperty(name='Material Slots Expanded')

from . import preferences as pref
