import bpy

def update_sidebar_category(self, context):
    from . import panels_original
    from . import panels_props

    viewport_panels = panels_props.viewport_panels + panels_original.viewport_panels

    for panel in viewport_panels:
        try: bpy.utils.unregister_class(panel)
        except: pass

        panel.bl_category = self.sidebar_category

        bpy.utils.register_class(panel)