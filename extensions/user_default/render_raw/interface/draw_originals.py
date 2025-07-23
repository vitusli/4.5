import gpu

def draw_original_curves(self, context):
        layout = self.layout
        scene = context.scene
        view = scene.view_settings
        layout.use_property_split = False
        layout.use_property_decorate = False  # No animation.
        layout.enabled = view.use_curve_mapping
        layout.template_curve_mapping(view, "curve_mapping", type='COLOR', levels=True)

def draw_original_display(self, context):
    col = self.layout.column()
    col.use_property_split = True
    col.use_property_decorate = False
    col.enabled = context.scene.view_settings.view_transform == 'Standard' and gpu.capabilities.hdr_support_get()
    col.prop(context.scene.view_settings, 'use_hdr_view')

def draw_original_white_balance(self, context):
    col = self.layout.column()
    col.use_property_split = True
    col.use_property_decorate = False
    col.active = context.scene.view_settings.use_white_balance
    col.prop(context.scene.view_settings, 'white_balance_temperature')
    col.prop(context.scene.view_settings, 'white_balance_tint')
