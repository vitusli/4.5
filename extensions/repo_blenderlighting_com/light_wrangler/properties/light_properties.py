import bpy

# State dictionary to keep track of the addon's state
state = {
    "operator_running": False,
    "last_active_object_name": None,
    "last_active_object_update_counter": 0,
    "last_customization": "",
}

def add_custom_properties_to_lights():
    light_types = ["POINT", "SPOT", "AREA", "SUN"]
    custom_options = {
        "POINT": ["Default", "IES"],
        "SPOT": ["Default", "Gobo"],
        "AREA": ["Default", "Scrim", "HDRI", "Gobo"],
        "SUN": ["Default"],
    }

    for light_type in light_types:
        for option in custom_options[light_type]:
            prop_name = f"{light_type.lower()}_{option.lower()}"
            setattr(bpy.types.Light, prop_name, bpy.props.BoolProperty(name=prop_name))

def register():
    add_custom_properties_to_lights()

def unregister():
    # Clean up custom properties
    light_types = ["POINT", "SPOT", "AREA", "SUN"]
    custom_options = {
        "POINT": ["Default", "IES"],
        "SPOT": ["Default", "Gobo"],
        "AREA": ["Default", "Scrim", "HDRI", "Gobo"],
        "SUN": ["Default"],
    }

    for light_type in light_types:
        for option in custom_options[light_type]:
            prop_name = f"{light_type.lower()}_{option.lower()}"
            try:
                delattr(bpy.types.Light, prop_name)
            except:
                pass 