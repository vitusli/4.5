import bpy
from .panels_props import get_settings


class ClippingMenu(bpy.types.Panel):
    bl_label = 'Render Raw Clipping'
    bl_idname = 'RENDER_PT_render_raw_clipping'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = 'render'
    bl_ui_units_x = 14

    @classmethod
    def poll(self, context):
        RR = get_settings(context)
        try:
            return RR.props_group
        except:
            return False

    def draw(self, context):
        RR = get_settings(context)
        col = self.layout.column()
        col.use_property_split = True
        col.use_property_decorate = False
        row = col.row()
        row.enabled = RR.props_group.use_clipping
        titles = row.column()
        titles.alignment = 'RIGHT'
        titles.label(text='Black Threshold')
        titles.label(text='White Threshold')
        titles.label(text='Saturation Threshold')
        titles.label(text='Ignore Dark Saturation')
        values = row.column()
        values.prop(RR.props_group, 'clipping_black_threshold', text='')
        values.prop(RR.props_group, 'clipping_white_threshold', text='')
        values.prop(RR.props_group, 'clipping_saturation_threshold', text='')
        values.prop(RR.props_group, 'clipping_saturation_multiply', text='', slider=True)
        

def register():
    bpy.utils.register_class(ClippingMenu)

def unregister():
    bpy.utils.unregister_class(ClippingMenu)