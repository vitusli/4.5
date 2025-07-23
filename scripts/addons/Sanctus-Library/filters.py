'''
Users can filter library assets through the panel UI using different filter criteria.
Whenever a filter is updated, some of the library building process is run again, which is the cause for the slight buffering after updating a filter.
This module contains a lot of UI code but also the function that determines if an asset should be hidden based on the active filters. Currently only
materials are being filtered.
'''


from . import auto_load as al
from .auto_load.common import *

from . import meta_data as md

class FilterSwitchProperty(al.BoolVectorProperty):

    def __init__(
            self, 
            name: str = '', 
            description: str = '', 
            default: al.TupleVector[bool] = (False, False),
            is_on_text: str = 'ON',
            is_off_text: str = 'OFF',
            ) -> None:
        self.is_on_text = is_on_text
        self.is_off_text = is_off_text
        super().__init__(name, description, default, {}, {}, None, al.BPropertySubtypeNumberArray.NONE, 2, None, None, None)
    
    def draw_ui(self, layout: bt.UILayout, options: al.UIOptions = al.UIOptions()):
        row = al.UI.row(layout, align=True)
        al.UI.prop(row, self.obj, self.data_attr, al.UIOptionsProp(text='', index=0, icon=options.get('icon')))
        al.UI.label(row, options.get('text', default=self.ui_name + ':'))
        override_row = al.UI.enabled(al.UI.row(row, align=True), self.is_enabled)
        filter_text = self.is_on_text if self.is_filter_on else self.is_off_text
        al.UI.prop(override_row, self.obj, self.data_attr, al.UIOptionsProp(
            text=filter_text if self.is_enabled else 'Disabled', 
            toggle=1, 
            index=1, 
            invert_checkbox=self.is_filter_on))
    
    @property
    def is_enabled(self):
        return self.value[0]
    
    @property
    def is_filter_on(self):
        return self.value[1]

@al.register
class FilterItem(al.PropertyGroup):
    
    display_name = al.StringProperty()
    path = al.StringProperty()
    search_name = al.StringProperty()
    icon_id = al.IntProperty()

@al.depends_on(FilterItem)
@al.register_property_group(bt.WindowManager)
class SanctusLibraryFilters(al.PropertyGroup):

    expand = al.BoolProperty(name='Expand', default=False)

    filter_engine = FilterSwitchProperty(name='Engine', default=(False, False), is_on_text='Cycles', is_off_text='Eevee')
    filter_complexity = al.EnumFlagProperty(enum=md.MetaComplexity, name='Complexity', default=md.MetaComplexity.all())
    filter_displacement = FilterSwitchProperty(name='Filter Displacement', default=(False, False), is_on_text='Only Displacement', is_off_text='No Displacement')
    filter_uvs = FilterSwitchProperty(name='Filter UVs', default=(False, False), is_on_text='UVs Required', is_off_text='No UVs required')

    all_items = al.CollectionProperty(FilterItem)
    active_filter_item = al.IntProperty()
    search_enabled = al.BoolProperty()

    @al.PD.set_draw_list_item(all_items)
    def all_items_draw_item(layout: bt.UILayout, c: al.CollectionProperty[FilterItem], i: FilterItem):
        from . import operators
        operators.library.SetActiveLibraryItem(path=i.path()).draw_ui(layout, al.UIOptionsOperator(text=i.display_name(), icon=i.icon_id()))

    @al.PD.set_sort_list(all_items)
    def all_items_sort_list(c: al.CollectionProperty[FilterItem], uilist: bt.UIList):
        return bt.UI_UL_list.sort_items_by_name(c(), FilterItem.display_name.data_attr)
    
    @al.PD.set_filter_list(all_items)
    def all_items_filter_list(c: al.CollectionProperty[FilterItem], uilist: bt.UIList):
        uilist.use_filter_show = True
        active_asset_class = library_manager.AssetClasses.current_ui_class
        items = c()
        filtered = [uilist.bitflag_filter_item] * len(items)
        if uilist.filter_name != "":
            filter_key = uilist.filter_name.lower().replace(' ', '').replace('_', '')
            filtered = bt.UI_UL_list.filter_items_by_name(filter_key, uilist.bitflag_filter_item, list(items), FilterItem.search_name.data_attr, reverse=False)
        for index, i in enumerate(items):
            if not i.path().startswith(active_asset_class):
                filtered[index] &= ~uilist.bitflag_filter_item
        return filtered
    
    @al.PD.set_draw_list_filters(all_items)
    def all_items_draw_filters(c: al.CollectionProperty[FilterItem], layout: bt.UILayout, context: bt.Context, uilist: bt.UIList):
        layout = al.UI.row(layout, align=True)
        al.UI.prop(layout, uilist, 'filter_name', al.UIIcon(al.BIcon.VIEWZOOM))
        al.UI.prop(layout, uilist, 'use_filter_sort_reverse', al.UIIcon(al.BIcon.SORT_DESC if uilist.use_filter_sort_reverse else al.BIcon.SORT_ASC))

    @property
    def use_filters(self):
        prefs = al.get_prefs()
        return prefs.interface().use_filters()

    def draw(self, layout: bt.UILayout):

        layout = al.UI.column(layout, align=True)
        if not self.expand.draw_as_dropdown(layout, 'Filters:', 'Filters...'):
            return

        self.filter_engine.draw_ui(layout)

        for prop in (self.filter_complexity,):
            c = al.UI.column(layout, align=True)
            al.UI.label(c, prop.ui_name + ':')
            prop.draw_ui(al.UI.row(c), al.UIOptionsProp(text=''))
            layout.separator()
        
        self.filter_displacement.draw_ui(layout)
        self.filter_uvs.draw_ui(layout)

    def draw_search(self, layout: bt.UILayout):
        layout = layout.box()
        self.all_items.draw_list(layout, self.active_filter_item, type='GRID', columns=1)

    @al.PD.update_property(filter_engine)
    @al.PD.update_property(filter_complexity)
    @al.PD.update_property(filter_displacement)
    @al.PD.update_property(filter_uvs)
    def on_material_filters_update(self, _):
        if bpy.app.background:
            return
        library_manager.reload_library_attributes()

    def is_item_filtered_out(self, meta_data: md.SanctusMetaData, asset_path: Path) -> bool:
        
        if not self.use_filters:
            return False

        def filter_materials():
            engine = meta_data.get_engine()
            if self.filter_engine.is_enabled:
                engine = md.MetaEngine.C if self.filter_engine.is_filter_on else md.MetaEngine.E
                if not engine in meta_data.get_engine():
                    return True
            if not meta_data.get_complexity() in self.filter_complexity():
                return True
            if self.filter_displacement.is_enabled and self.filter_displacement.is_filter_on != meta_data.use_displacement:
                return True
            if self.filter_uvs.is_enabled and self.filter_uvs.is_filter_on != meta_data.require_uvs:
                return True
            return False
        
        if 'materials' in asset_path.parts:
            return filter_materials()
        return False

LIBRARY_FILTERS_CACHE = {}

@al.register_handler_callback(bpy.app.handlers.load_pre)
def cache_filter_list(*_):
    global LIBRARY_FILTERS_CACHE
    filters = SanctusLibraryFilters.get_from(al.get_wm())
    LIBRARY_FILTERS_CACHE = filters.serialize()


@al.register_handler_callback(bpy.app.handlers.load_post)
def cache_filter_list(*_):

    filters = SanctusLibraryFilters.get_from(al.get_wm())
    filters.deserialize(LIBRARY_FILTERS_CACHE)


from . import preferences as pref
from . import library_manager
