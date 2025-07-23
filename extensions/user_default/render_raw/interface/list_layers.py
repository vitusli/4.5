import bpy
from ..utilities.layers import get_layer_settings


class Layers(bpy.types.PropertyGroup):
    #Collection property for the UI List to populate
    pass


class RENDER_UL_render_raw_layers(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        """
        data: render raw node group
        """
        LAYER = get_layer_settings(data, index, 'Pre')
        row = layout.row()
        # row.label(text=str(index)) # Useful for debugging
        row.label(text=LAYER.layer_name) # icon='OUTLINER_DATA_GP_LAYER'
        checkbox = 'CHECKBOX_HLT' if LAYER.use_layer else 'CHECKBOX_DEHLT'
        row.operator('render.render_raw_toggle_layer', text='', icon=checkbox, emboss=False).index = index
        # mask = 'MOD_MASK' if item.use_mask else 'CLIPUV_HLT'
        # row.prop(item, 'use_mask', icon=mask, text='', emboss=False)


"""
class RENDER_UL_example(bpy.types.UIList):
    # documentation at: https://docs.blender.org/api/current/bpy.types.UIList.html
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            if item:
                layout.prop(item, "name", text="", emboss=False, icon_value=icon)
            else:
                layout.label(text="", translate=False, icon_value=icon)
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)

        OR

        #split = layout.split(factor=0.1)
        #split.label(text=f'{index}')
        #custom_icon = 'OUTLINER_DATA_GP_LAYER'
        #split.prop(item, "name", text="", emboss=False, translate=False, icon=custom_icon)
        #split.label(text=item.name, icon=custom_icon) # avoids renaming the item by accident
"""



def register():
    bpy.utils.register_class(Layers)
    bpy.types.NodeTree.render_raw_layers = bpy.props.CollectionProperty(type=Layers)
    bpy.utils.register_class(RENDER_UL_render_raw_layers)

def unregister():
    bpy.utils.unregister_class(Layers)
    bpy.utils.unregister_class(RENDER_UL_render_raw_layers)