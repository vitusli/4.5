import bpy.types as bt

LIST_USERS_MAP = {}

class GenericUIList(bt.UIList):
    bl_idname = 'AUTOLOAD_UL_generic'

    @property
    def collection_prop(self):
        from . import props
        prop: props.CollectionProperty = LIST_USERS_MAP[self.list_id]
        return prop
    
    def draw_item(self, context, layout: bt.UILayout, data, item, icon, active_data):
        prop = self.collection_prop
        prop.draw_list_item(layout, prop, item)
        
    def filter_items(self, context: bt.Context, data, property: str):
        prop = self.collection_prop
        return prop.filter_list(prop, self), prop.sort_list(prop, self)
    
    def draw_filter(self, context: bt.Context, layout: bt.UILayout):
        self.collection_prop.draw_list_filters(self.collection_prop, layout, context, self)

class AL_PT_property_drawer_popover(bt.Panel):
    bl_label = 'Property Settings'
    bl_space_type = 'CONSOLE'
    bl_region_type = 'WINDOW'
    CONTEXT_TARGET_REF = "al_property_drawer_context_target"

    def draw(self, context: bt.Context):
        from . import ui
        target = getattr(context, self.CONTEXT_TARGET_REF)
        ui.PropertyDrawerType.get_drawer_from_instance(target)(target, self.layout, context).draw_panel()
