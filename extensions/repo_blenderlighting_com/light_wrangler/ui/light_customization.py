import bpy
from bpy.types import Panel
from .. import ADDON_MODULE_NAME

class LIGHTW_PT_LightCustomization(Panel):
    bl_label = "Light Customization"
    bl_idname = "LIGHTW_PT_light_customization"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "data"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def poll(cls, context):
        prefs = bpy.context.preferences.addons[ADDON_MODULE_NAME].preferences
        
        return (
            (context.scene.render.engine in {"CYCLES", "BLENDER_EEVEE", "BLENDER_EEVEE_NEXT", "octane"})
            and context.object is not None
            and context.object.type == "LIGHT"
        )
        
    def draw(self, context):
        layout = self.layout
        light_obj = context.object
        light_data = light_obj.data
        prefs = bpy.context.preferences.addons[ADDON_MODULE_NAME].preferences
        
        last_customization_key = f"last_customization_{light_data.type}"
        current_customization = light_obj.get(last_customization_key, "Default")
        
        if context.scene.render.engine in {"BLENDER_EEVEE", "BLENDER_EEVEE_NEXT", "octane"} and current_customization in ["Scrim", "HDRI", "Gobo"]:
            box = layout.box()
            op = box.operator(
                "lightwrangler.confirm_cycles_switch",
                text="Activate Cycles to Edit"
            )
            op.light_name = light_obj.name
            op.light_type = light_data.type
            op.customization = current_customization
        else:
            # Existing draw logic for Cycles and non-limited Eevee modes
            if light_data.type == "POINT":
                self.draw_customization_buttons(
                    layout, light_obj, "POINT", ["Default", "IES"]
                )
            elif light_data.type == "SPOT":
                self.draw_customization_buttons(
                    layout, light_obj, "SPOT", ["Default", "Gobo"]
                )
            elif light_data.type == "AREA":
                self.draw_customization_buttons(
                    layout, light_obj, "AREA", ["Default", "Scrim", "HDRI", "Gobo"]
                )
            elif light_data.type == "SUN":
                self.draw_customization_buttons(layout, light_obj, "SUN", ["Default"])
            
    def draw_customization_buttons(self, layout, light_obj, light_type, options):
        last_customization_key = f"last_customization_{light_type}"
        current_customization = light_obj.get(last_customization_key, "Default")

        row = layout.row(align=True)

        for option in options:
            if bpy.context.scene.render.engine in {"BLENDER_EEVEE", "BLENDER_EEVEE_NEXT", "octane"} and option in ["Scrim", "HDRI", "Gobo", "IES"]:
                op = row.operator(
                    "lightwrangler.confirm_cycles_switch",
                    text=option,
                    depress=option == current_customization,
                )
            else:
                op = row.operator(
                    "lightwrangler.apply_custom_data_block",
                    text=option,
                    depress=option == current_customization,
                )
            op.light_name = light_obj.name
            op.light_type = light_type
            op.customization = option

        if current_customization in ["Gobo", "HDRI", "IES"]:
            box = layout.box()
            col = box.column()

            if current_customization == "Gobo":
                col.template_icon_view(
                    light_obj.data,
                    "gobo_enum",
                    show_labels=True,
                    scale_popup=5,
                    scale=7,
                )
                # Only show Convert to Plane button for area lights
                if light_type == 'AREA':
                    # Add buttons in a row
                    row = col.row(align=True)
                    # Add the "Convert to Plane" button
                    row.operator(
                        "lightwrangler.convert_to_plane",
                        text="Convert to Plane",
                        icon='MESH_PLANE'
                    )
            elif current_customization == "HDRI":
                col.template_icon_view(
                    light_obj.data,
                    "hdri_enum",
                    show_labels=True,
                    scale_popup=5,
                    scale=7,
                )
            elif current_customization == "IES":
                col.template_icon_view(
                    light_obj.data, 
                    "ies_enum", 
                    show_labels=True, 
                    scale_popup=5, 
                    scale=7
                )

        elif current_customization == "Scrim":
            mat = bpy.data.materials.get("Scrim Preview")

# List of all classes in this file
classes = (
    LIGHTW_PT_LightCustomization,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls) 