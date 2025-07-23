import bpy, gpu


'''
These panels replace the originals when Render Raw is unregistered
'''

class RENDER_PT_render_raw_dummy_color_management(bpy.types.Panel):
    bl_label = "Color Management"
    bl_options = {'DEFAULT_CLOSED'}
    bl_space_type = 'PROPERTIES'
    bl_context = 'render'
    bl_region_type = 'WINDOW'
    COMPAT_ENGINES = {
        'BLENDER_RENDER',
        'BLENDER_EEVEE',
        'BLENDER_EEVEE_NEXT',
        'BLENDER_WORKBENCH',
    }

    def draw(self, context):
        col = self.layout.column()
        col.use_property_split = True
        col.use_property_decorate = False
        col.prop(context.scene.display_settings, 'display_device')
        col.separator()
        col.prop(context.scene.view_settings, 'view_transform')
        col.prop(context.scene.view_settings, 'look')
        col.prop(context.scene.view_settings, 'exposure')
        col.prop(context.scene.view_settings, 'gamma')
        col.separator()
        col.prop(context.scene.sequencer_colorspace_settings, 'name', text='Sequencer')


class RENDER_PT_render_raw_dummy_display(bpy.types.Panel):
    bl_label = "Display"
    bl_parent_id = "RENDER_PT_render_raw_dummy_color_management"
    bl_options = {'DEFAULT_CLOSED'}
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    COMPAT_ENGINES = {
        'BLENDER_RENDER',
        'BLENDER_EEVEE',
        'BLENDER_EEVEE_NEXT',
        'BLENDER_WORKBENCH',
    }

    def draw(self, context):
        col = self.layout.column()
        col.use_property_split = True
        col.enabled = context.scene.view_settings.view_transform == 'Standard' and gpu.capabilities.hdr_support_get()
        col.prop(context.scene.view_settings, 'use_hdr_view')


class RENDER_PT_render_raw_dummy_curves(bpy.types.Panel):
    bl_label = "Use Curves"
    bl_parent_id = "RENDER_PT_render_raw_dummy_color_management"
    bl_options = {'DEFAULT_CLOSED'}
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    COMPAT_ENGINES = {
        'BLENDER_RENDER',
        'BLENDER_EEVEE',
        'BLENDER_EEVEE_NEXT',
        'BLENDER_WORKBENCH',
    }

    def draw_header(self, context):
        scene = context.scene
        view = scene.view_settings
        self.layout.prop(view, "use_curve_mapping", text="")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        view = scene.view_settings
        layout.use_property_split = False
        layout.use_property_decorate = False  # No animation.
        layout.enabled = view.use_curve_mapping
        layout.template_curve_mapping(view, "curve_mapping", type='COLOR', levels=True)


class RENDER_PT_render_raw_dummy_white_balance(bpy.types.Panel):
    bl_label = "White Balance"
    bl_parent_id = "RENDER_PT_render_raw_dummy_color_management"
    bl_options = {'DEFAULT_CLOSED'}
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    COMPAT_ENGINES = {
        'BLENDER_RENDER',
        'BLENDER_EEVEE',
        'BLENDER_EEVEE_NEXT',
        'BLENDER_WORKBENCH',
    }

    def draw_header(self, context):
        scene = context.scene
        view = scene.view_settings

        self.layout.prop(view, "use_white_balance", text="")

    def draw_header_preset(self, context):
        layout = self.layout

        bpy.types.RENDER_PT_color_management_white_balance_presets.draw_panel_header(layout)

        eye = layout.operator("ui.eyedropper_color", text="", icon='EYEDROPPER')
        eye.prop_data_path = "scene.view_settings.white_balance_whitepoint"

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        view = scene.view_settings

        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        layout.active = view.use_white_balance

        col = layout.column()
        col.prop(view, "white_balance_temperature")
        col.prop(view, "white_balance_tint")


def register():
    if hasattr(bpy.types, 'RENDER_PT_render_raw_dummy_color_management'):
        bpy.utils.unregister_class(bpy.types.RENDER_PT_render_raw_dummy_color_management)
    if hasattr(bpy.types, 'RENDER_PT_render_raw_dummy_curves'):
        bpy.utils.unregister_class(bpy.types.RENDER_PT_render_raw_dummy_curves)
    if hasattr(bpy.types, 'RENDER_PT_render_raw_dummy_display'):
        bpy.utils.unregister_class(bpy.types.RENDER_PT_render_raw_dummy_display)
    if hasattr(bpy.types, 'RENDER_PT_render_raw_dummy_white_balance'):
        bpy.utils.unregister_class(bpy.types.RENDER_PT_render_raw_dummy_white_balance)

def unregister():
    bpy.utils.register_class(RENDER_PT_render_raw_dummy_color_management)
    bpy.utils.register_class(RENDER_PT_render_raw_dummy_display)
    bpy.utils.register_class(RENDER_PT_render_raw_dummy_curves)
    if bpy.app.version >= (4, 3, 0):
        bpy.utils.register_class(RENDER_PT_render_raw_dummy_white_balance)