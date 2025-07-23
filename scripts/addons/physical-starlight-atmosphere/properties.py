# ##### BEGIN GPL LICENSE BLOCK #####
# Physical Starlight and Atmosphere is is a completely volumetric procedural
# sky, sunlight, and atmosphere simulator addon for Blender
# Copyright (C) 2024  Physical Addons

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
# ##### END GPL LICENSE BLOCK #####

# External library imports
import bpy
from bpy.types import (
    PropertyGroup, 
    Object
)
from bpy.props import (
    BoolProperty,
    FloatProperty,
    FloatVectorProperty,
    EnumProperty,
    IntProperty,
    StringProperty,
    PointerProperty,
    CollectionProperty,
)

import json

from datetime import date

# Project module imports
from .handlers import *
from .helpers import current_addon_version


def validate_preset_name(preset_name):
    # A list of symbols that cannot be accepted in a file name
    invalid_symbols = "\\/?:*|\"<>"
    for i in preset_name:
        if i in invalid_symbols:
            return ("Invalid symbols found from the following: %s" % invalid_symbols, invalid_symbols)
    # Check if name is empty or all spaces
    if len(preset_name.replace(" ", "")) == 0:
        return ("Preset name cannot be empty", invalid_symbols)
    return None


def is_serializable(x):
    """A function to check if a param is JSON seriazible"""
    try:
        json.dumps(x)
        return True
    except:
        return False


def create_preset(context, preset_path):
    """Function that writes a preset based on current PSA atmosphere to a .json fila given a path"""

    world = context.scene.world

    preset_data = {"atmosphere": {}, "sun": {}, "version": current_addon_version()}

    # Save sun rotation
    preset_data["sun"]["rotation_euler"] = [
        world.psa_exposed.sun_object.rotation_euler.x,
        world.psa_exposed.sun_object.rotation_euler.y, 
        world.psa_exposed.sun_object.rotation_euler.z]

    for prop_name, prop in world.psa_atmosphere_settings.items():
        # Check if prop is serializable to avoid writing object pointers in presets
        # Color and Vector types don't return as serializable, but still work
        if is_serializable(prop):
            preset_data["atmosphere"][prop_name] = getattr(world.psa_atmosphere_settings, prop_name)
        else:
            # Assume prop is iterable
            # FIXME if in future more non-serializable types appear than just vectors/arrays
            write_prop = [] 
            for element in prop:
                write_prop.append(element)
            preset_data["atmosphere"][prop_name] = write_prop

    with open(preset_path, 'w') as json_file:
        json.dump(preset_data, json_file, indent=4)


def backup_preset(preset_path, preset_data, version):
    """Function that backups a preset given it's path and version data"""
    dir_path = os.path.split(preset_path)[0] # Get the preset's directory
    backup_path = os.path.join(dir_path, "backup_%s_%s" % (str(version), date.today()))
    os.makedirs(backup_path, exist_ok=True)
    backup_preset_path = os.path.join(backup_path, os.path.split(preset_path)[1])

    with open(backup_preset_path, 'w') as json_file:
        json.dump(preset_data, json_file, indent=4)
    

def update_preset_versions(context):
    psa_presets_dir = os.path.join(bpy.utils.user_resource('DATAFILES'), "presets", "PSA")

    for file in os.listdir(psa_presets_dir):
        file_name = os.fsdecode(file)
        if file_name.endswith(".json"):
            preset_path = os.path.join(psa_presets_dir, file_name)
            with open(preset_path) as json_data:
                data = json.load(json_data)
                atmosphere = data.get("atmosphere")

                if atmosphere.get("version") == None:
                    # No previous version of this type of presets is handled
                    pass


def apply_preset(context, preset_path):
    """Function that loads a preset .json from given path and applies to current PSA atmosphere"""

    world = context.scene.world

    with open(preset_path) as json_data:
        data = json.load(json_data)
    
    atmosphere = data.get("atmosphere")

    # Register the class to set defaults to the preset
    new_atmosphere = register_psa_property_groups(context, atmosphere)

    if new_atmosphere:
        for prop_name in new_atmosphere.keys():
            setattr(world.psa_atmosphere_settings, prop_name, new_atmosphere.get(prop_name))
    
    if world.psa_exposed.apply_preset_sun_data:
        sun = data.get("sun")
        world.psa_exposed.sun_object.rotation_euler = sun.get("rotation_euler")


def select_preset(self, context):
    world = context.scene.world

    # Check to ensure the preset index is valid
    if len(world.psa_exposed.presets) > world.psa_exposed.preset_index and world.psa_exposed.preset_index >= 0:
        preset_data = world.psa_exposed.presets[world.psa_exposed.preset_index]
        apply_preset(context, preset_data.path) # Apply preset
        world.psa_exposed.preset_name = preset_data.name


def update_preset_list(self, context):
    world = context.scene.world

    # Update presets list
    world.psa_exposed.presets.clear()

    # Find the directory of our presets and parse JSONs from there
    preset_path = os.path.join(bpy.utils.user_resource('DATAFILES'), "presets", "PSA")
    os.makedirs(preset_path, exist_ok=True)

    for file in os.listdir(preset_path):
        file_name = os.fsdecode(file)
        if file_name.endswith(".json"):
            preset_data = world.psa_exposed.presets.add()
            preset_data["name"] = file_name.removesuffix(".json")
            preset_data.path = os.path.join(preset_path, file_name)


def rename_preset(self, context):
    world = context.scene.world

    # We need the previous name to find the file and rename it
    old_name = world.psa_exposed.preset_name
    new_name = world.psa_exposed.presets[world.psa_exposed.preset_index].name

    # Generate the new file path for renaming
    base_path = os.path.join(bpy.utils.user_resource('DATAFILES'), "presets", "PSA")

    old_path = os.path.join(base_path, old_name + ".json")
    new_path = os.path.join(base_path, new_name + ".json")

    # Check if the name contains invalid symbols
    invalid_symbols = validate_preset_name(new_name)
    if invalid_symbols:
        world.psa_exposed.presets[world.psa_exposed.preset_index].name = old_name
        # TODO See if user can be notified of this operation's failure somehow
    # Check if we're not clashing with existing preset name
    elif os.path.isfile(new_path):
        world.psa_exposed.presets[world.psa_exposed.preset_index].name = old_name
        # TODO See if user can be notified of this operation's failure somehow
    else:
        # Rename the file
        os.rename(old_path, new_path)

        # Update preset list to ensure the new name is shown up in UI
        update_preset_list(self, context)

        # Make sure the renamed preset is still selected
        for i in range(len(world.psa_exposed.presets)):
            if world.psa_exposed.presets[i].name == new_name:
                world.psa_exposed.preset_index = i
                break


class PSA_Preset(PropertyGroup):
    """PSA Preset Object"""

    name: StringProperty(
        name = "Name",
        description = "Name of preset",
        update = rename_preset,
    )

    path: StringProperty(
        subtype = "FILE_PATH",
        name = "File Path",
        description = "Path of the JSON file that contains preset data",
    )


class PA_Exposed(PropertyGroup):
    """
    Exposed pointers and parameters
    """    

    output_node_name: StringProperty(
        description="Name of the output node",
    )

    atmosphere_node_name: StringProperty(
        description="Name of the Starlight Atmosphere node",
    )

    stars_node_name: StringProperty(
        description="Name of the Physical Stars node",
    )

    sun_object: PointerProperty(
        type=Object,
        description="Sun object used by addon"
    )

    presets: CollectionProperty(
        type = PSA_Preset,
        name = "Presets",
        description = "A list of all available presets for PSA",
    )

    preset_name: StringProperty(
        name = "Preset Name",
        description = "Name of current PSA preset",
        default = '',
    )

    preset_index: IntProperty(
        name = "Preset Index",
        description = "Index of preset selected to apply",
        default = -1,
        update = select_preset,
    )

    show_presets: BoolProperty(
        name = "Show Presets",
        description = "Show Presets in UI",
        default = False,
        update = update_preset_list,
    )

    apply_preset_sun_data: BoolProperty(
        name = "Use Preset Sun Position",
        description = "Whether to use sun position from preset",
        default = True,
    )


class GeneralSettings(PropertyGroup):
    """
    General Properties
    """    

    enabled: BoolProperty(
        name="Enable starlight atmosphere",
        default=False,
        update=enable_atmosphere
    )

    version_format: IntProperty(
        name="Version format",
        default=0, # Default is set to zero, to detect previous version system .blend files
    )

    material_count: IntProperty(
        name="Material Count",
        default=0,
    )

    material_with_fog_count: IntProperty(
        name="Material with applied fog count",
        default=0,
    )

    intensity_multiplier: IntProperty(
        name="Default property intensity multiplier",
        default=1,
    )

    sun_pos_checksum: FloatProperty(
        name="Sun Position checksum",
        default=0,
    )

    all_props_checksum: StringProperty(
        description="Contains last frame all property string concatenation",
    )

    fog_enabled: BoolProperty(
        default=False
    )

    is_rendering: BoolProperty(
        default=False
        # description="Update azimuth or elevation without triggering update function"
    )

    is_generating_presets: BoolProperty(
        default=False,
        description="To avoid getting in a loop and generating presets when presets are being generated"
    )


def register_psa_property_groups(context, atmosphere):
    """Function that sets default values for all props and re-registers them."""

    atmosphere_defaults = {
        "sun_disk": True,
        "sun_lamp": True,
        "azimuth": 2.449570,
        "elevation": 3.089843,
        "sun_diameter": 0.009180,
        "atmosphere_color": (0.75, 0.8, 1.0, 1.0),
        "atmosphere_inscattering": (0.0573, 0.1001, 0.1971, 1.000000),
        "atmosphere_extinction": (1.0-0.0573, 1.0-0.1001, 1.0-0.1971, 1.000000),
        "atmosphere_density": 1.2,
        "atmosphere_height": 8000,
        "atmosphere_intensity": 2,
        "night_intensity": 0.02,
        "atmosphere_falloff": 1.0,
        "atmosphere_mie": 2.0,
        "atmosphere_mie_dir": 0.7,
        "atmosphere_distance": 1.0,
        "ground_visible": True,
        "ground_albedo": (0.25, 0.25, 0.25, 1.0),
        "ground_offset": -100,
        "horizon_offset": 0,
        "sun_temperature": 5700,
        "sun_intensity": 200000,
        "enable_binary_sun": False,
        "binary_distance": 0.16,
        "binary_phase": 2.0,
        "binary_diameter": 0.017453,
        "binary_temperature": 1800,
        "binary_intensity": 50000,
        "sun_radiance_gamma": 1.0,
        "stars_type": 'procedural',
        "stars_intensity": 0.02,
        "stars_gamma": 0.5,
        "stars_seed": 0,
        "stars_amount": 1.0,
        "stars_scale": 1.0,
        "stars_temperature_min": 4000,
        "stars_temperature_max": 7000,
        "clouds_type": 'procedural',
        "clouds_texture_type": 'map',
        "clouds_scale": 2.0,
        "clouds_detail": 8.0,
        "clouds_dimension": 1.0,
        "clouds_lacunarity": 2.1,
        "clouds_min": -1.0,
        "clouds_max": 1.0,
        "clouds_thickness": 15.0,
        "clouds_scattering": (0.4, 0.45, 0.8, 1.0),
        "clouds_amount": 5.0,
        "clouds_power": 5.0,
        "clouds_lighting_intensity": 1.0,
        "clouds_location": (0, 0, 0),
        "clouds_rotation": (0, 0, 0),
        "fog_state": 'manual',
    }

    # Replace all the default preset values with custom ones
    new_atmosphere_defaults = atmosphere_defaults.copy()
    for key, value in atmosphere.items():
        new_atmosphere_defaults[key] = value


    class AtmosphereSettings(PropertyGroup):
        """
        Physical Atmosphere panel properties
        """    
        
        sun_disk : BoolProperty(
            name = "Sun Disk",
            description = "Toggles Sun disk in the atmosphere",
            default = new_atmosphere_defaults["sun_disk"],
            update = sun_calculation_handler
        )

        sun_lamp : BoolProperty(
            name = "Sun Lamp",
            description = "Use Sun Lamp as light source instead of Sun Disk in world background",
            default = new_atmosphere_defaults["sun_disk"],
            update = sun_calculation_handler
        )

        azimuth : FloatProperty(
            name = "Azimuth",
            description = "Horizontal direction: at 0° the Sun is in the Y+ axis",
            soft_min = -999,
            soft_max = 999,
            step = 5,
            precision = 3,
            default = new_atmosphere_defaults["azimuth"],
            unit = "ROTATION",
            #update = azimuth_handler
        )

        elevation : FloatProperty(
            name = "Elevation",
            description = "Vertical direction: at 90° the Sun is in the zenith",
            soft_min = -999,
            soft_max = 999,
            step = 5,
            precision = 3,
            default = new_atmosphere_defaults["elevation"],
            unit = "ROTATION",
            #update = elevation_handler
        )

        sun_diameter : FloatProperty(
            name = "Angular Diameter",
            description = "Angular diameter of the Sun disk in degrees",
            min = 0.001,
            max = math.pi*0.5,
            step = 1,
            precision = 3,
            default = new_atmosphere_defaults["sun_diameter"],
            unit = "ROTATION",
            update = sun_calculation_handler
        )

        atmosphere_color : FloatVectorProperty(
            name = "", # leave empty (for layout considerations)
            description = "Atmosphere color",
            subtype = "COLOR_GAMMA",
            size = 4,
            min = 0.0,
            max = 1.0,
            default = new_atmosphere_defaults["atmosphere_color"],
            update = sun_calculation_handler
        )

        atmosphere_inscattering : FloatVectorProperty(
            name = "", # leave empty (for layout considerations)
            description = "Rayleigh scattering",
            subtype = "COLOR_GAMMA",
            size = 4,
            min = 0.0,
            max = 1.0,
            default = new_atmosphere_defaults["atmosphere_inscattering"],
            update = sun_calculation_handler
        )

        atmosphere_extinction : FloatVectorProperty(
            name = "", # leave empty (for layout considerations)
            description = "Atmosphere absorption / color wavelength extinction value",
            subtype = "COLOR_GAMMA",
            size = 4,
            min = 0.0,
            max = 1.0,
            default = new_atmosphere_defaults["atmosphere_extinction"],
            update = sun_calculation_handler
        )

        atmosphere_density : FloatProperty(
            name = "Density",
            description = "Atmosphere density in kg/m3",
            min = 0,
            soft_max = 100,
            step = 100,
            precision = 2,
            default = new_atmosphere_defaults["atmosphere_density"],
            unit = "NONE",
            subtype = "FACTOR",
            update = sun_calculation_handler
        )

        atmosphere_height : FloatProperty(
            name = "Scale Height",
            description = "Atmosphere height",
            min = 2,
            soft_max = 10000,
            step = 100,
            precision = 2,
            default = new_atmosphere_defaults["atmosphere_height"],
            unit = "LENGTH",
            subtype = "DISTANCE",
            update = sun_calculation_handler
        )

        atmosphere_intensity : FloatProperty(
            name = "Intensity",
            description = "Atmosphere Radiance Intensity in W/m2",
            min = 0,
            soft_max = 500,
            step = 100,
            precision = 2,
            default = new_atmosphere_defaults["atmosphere_intensity"],
            unit = "NONE",
            subtype = "FACTOR",
            update = sun_calculation_handler
        )

        night_intensity : FloatProperty(
            name = "Night Intensity",
            description = "Night Sky Radiance Intensity in W/m2",
            min = 0.000001,
            soft_max = 0.04,
            step = 100,
            precision = 2,
            default = new_atmosphere_defaults["night_intensity"],
            unit = "NONE",
            subtype = "FACTOR",
            update = sun_calculation_handler
        )

        atmosphere_falloff : FloatProperty(
            name = "Falloff",
            description = "Artistic atmosphere falloff curve",
            min = 0,
            max = 3.0,
            step = 10,
            precision = 2,
            default = new_atmosphere_defaults["atmosphere_falloff"],
            unit = "NONE",
            subtype = "FACTOR",
            update = sun_calculation_handler
        )

        atmosphere_mie : FloatProperty(
            name = "Intensity",
            description = "Mie scattering Intensity in W/m2",
            min = 0,
            soft_max = 500.0,
            step = 10,
            precision = 2,
            default = new_atmosphere_defaults["atmosphere_mie"],
            unit = "NONE",
            subtype = "FACTOR",
            update = sun_calculation_handler
        )

        atmosphere_mie_dir : FloatProperty(
            name = "Anisotropy",
            description = "Mie directional anisotropy",
            min = 0,
            max = 1.0,
            step = 10,
            precision = 2,
            default = new_atmosphere_defaults["atmosphere_mie_dir"],
            unit = "NONE",
            subtype = "FACTOR",
            update = sun_calculation_handler
        )

        atmosphere_distance : FloatProperty(
            name = "Distance Scalar",
            description = "Artistic atmosphere distance scalar",
            min = 0.0,
            soft_max = 500,
            step = 10,
            precision = 2,
            default = new_atmosphere_defaults["atmosphere_distance"],
            unit = "NONE",
            subtype = "FACTOR",
            update = sun_calculation_handler
        )

        ground_visible: BoolProperty(
            name = "Ground",
            description = "Parametric ground visibility",
            default = new_atmosphere_defaults["ground_visible"],
            update = sun_calculation_handler
        )

        ground_albedo : FloatVectorProperty(
            name = "", # leave empty (for layout considerations)
            description = "Ground color",
            subtype ="COLOR_GAMMA",
            size = 4,
            min = 0.0,
            max = 1.0,
            default = new_atmosphere_defaults["ground_albedo"],
            update = sun_calculation_handler
        )

        ground_offset : FloatProperty(
            name = "Ground Offset",
            description = "Parametric ground plane offset distance in meters",
            unit = "LENGTH",
            subtype = "DISTANCE",
            soft_min = -500000.0,
            soft_max = 0.0,
            default = new_atmosphere_defaults["ground_offset"],
            update = sun_calculation_handler
        )

        horizon_offset : FloatProperty(
            name = "Horizon Offset",
            description = "Move horizon line up or down",
            unit = "NONE",
            subtype = "FACTOR",
            min = -1.0,
            max = 1.0,
            default = new_atmosphere_defaults["horizon_offset"],
            update = sun_calculation_handler
        )

        sun_temperature : FloatProperty(
            name = "Temperature K",
            description = "Sun's blackbody temperature in Kelvins",
            min = 1000,
            soft_max = 10000,
            step = 100,
            precision = 2,
            default = new_atmosphere_defaults["sun_temperature"],
            unit = "NONE",
            subtype = "FACTOR",
            update = sun_calculation_handler
        )

        sun_intensity : FloatProperty(
            name = "Intensity",
            description = "Sun Radiance Intensity in W/m2. Influences only sun disk and ground",
            soft_min = 100,
            soft_max = 200000,
            step = 100,
            precision = 2,
            default = new_atmosphere_defaults["sun_intensity"],
            unit = "NONE",
            subtype = "FACTOR",
            update = sun_calculation_handler
        )

        enable_binary_sun: BoolProperty(
            name = "Binary Sun",
            description = "Use Binary Sun",
            default = new_atmosphere_defaults["enable_binary_sun"],
            update = sun_calculation_handler
        )

        binary_distance: FloatProperty(
            name = "Distance",
            description = "Distance from the Sun",
            min = 0.0,
            soft_max = 1,
            step = 0.001,
            precision = 3,
            default = new_atmosphere_defaults["binary_distance"],
            unit = "NONE",
            subtype = "FACTOR",
            update = sun_calculation_handler
        )

        binary_phase: FloatProperty(
            name = "Phase",
            description = "Phase in context of Sun",
            soft_min = -360,
            soft_max = 360,
            step = 5,
            precision = 3,
            default = new_atmosphere_defaults["binary_phase"],
            unit = "ROTATION",
            update = sun_calculation_handler
        )

        binary_diameter: FloatProperty(
            name = "Angular Diameter",
            description = "Angular diameter of the Binary Sun disk in degrees",
            min = 0.001,
            max = math.pi*0.5,
            step = 1,
            precision = 3,
            default = new_atmosphere_defaults["binary_diameter"],
            unit = "ROTATION",
            update = sun_calculation_handler
        )

        binary_temperature: FloatProperty(
            name = "Temperature K",
            description = "Binary Sun's blackbody temperature in Kelvins",
            min = 1000,
            soft_max = 10000,
            step = 100,
            precision = 2,
            default = new_atmosphere_defaults["binary_temperature"],
            unit = "NONE",
            subtype = "FACTOR",
            update = sun_calculation_handler
        )

        binary_intensity: FloatProperty(
            name = "Intensity",
            description = "Binary Sun Radiance Intensity in W/m2. Influences only sun disk and ground",
            soft_min = 100,
            soft_max = 200000,
            step = 100,
            precision = 2,
            default = new_atmosphere_defaults["binary_intensity"],
            unit = "NONE",
            subtype = "FACTOR",
            update = sun_calculation_handler
        )

        sun_radiance_gamma : FloatProperty(
            name = "Sun Radiance Gamma",
            description = "Artistic Sun Radiance Gamma",
            min = 0.01,
            max = 3.0,
            step = 10,
            precision = 2,
            default = new_atmosphere_defaults["sun_radiance_gamma"],
            unit = "NONE",
            subtype = "FACTOR",
            update = sun_calculation_handler,
        )

        stars_type: EnumProperty(
            items = [(
                        'procedural', 
                        'Procedural', 
                        'Enable procedurally generated stars (textures loading instantly)'
                    ),
                    (
                        'texture', 
                        'Texture', 
                        'Enable texture for the star map (textures loading slowly)'
                    ),
                    (
                        'none', 
                        'None', 
                        'disable stars'
                    )],
            default = new_atmosphere_defaults["stars_type"],
            update = stars_handler,
        )

        stars_texture : PointerProperty(
            name = "Star map Image",
            description = "Choose a Star map Image",
            type = bpy.types.Image,
            update = stars_texture_handler,
        )

        stars_intensity : FloatProperty(
            name = "Radiance Intensity",
            description = "Stars Radiance Intensity",
            min = 0,
            soft_max = 15.0,
            step = 10,
            precision = 2,
            default = new_atmosphere_defaults["stars_intensity"],
            unit = "NONE",
            subtype = "FACTOR",
            update = sun_calculation_handler
        )

        stars_gamma : FloatProperty(
            name = "Radiance Gamma",
            description = "Stars Radiance Gamma",
            min = 0,
            soft_max = 3.0,
            step = 10,
            precision = 2,
            default = new_atmosphere_defaults["stars_gamma"],
            unit = "NONE",
            subtype = "FACTOR",
            update = sun_calculation_handler
        )

        stars_seed : IntProperty(
            name = "Stars Seed",
            description = "Seed number for random stars distribution",
            default = new_atmosphere_defaults["stars_seed"],
            update = sun_calculation_handler
        )

        stars_amount : FloatProperty(
            name = "Stars Amount",
            description = "Control visible stars, offsets radius",
            min = 0.0,
            soft_max = 2.0,
            step = 10,
            precision = 2,
            default = new_atmosphere_defaults["stars_amount"],
            unit = "NONE",
            subtype = "FACTOR",
            update = sun_calculation_handler
        )

        stars_scale : FloatProperty(
            name = "Stars Scale",
            description = "Control the scale of stars procedural texture",
            default = new_atmosphere_defaults["stars_scale"],
            min = 0.001,
            soft_max = 5.0,
            update = sun_calculation_handler
        )

        stars_temperature_min: FloatProperty(
            name = "Temperature Min",
            description = "Control the minimum temperature of stars",
            min = 0.001,
            unit='TEMPERATURE',
            soft_min = 1000.0,
            soft_max = 10000.0,
            default = new_atmosphere_defaults["stars_temperature_min"],
            update = sun_calculation_handler
        )

        stars_temperature_max: FloatProperty(
            name = "Temperature Max",
            description = "Control the maximum temperature of stars",
            min = 0.001,
            unit='TEMPERATURE',
            soft_min = 1000.0,
            soft_max = 15000.0,
            default = new_atmosphere_defaults["stars_temperature_max"],
            update = sun_calculation_handler
        )

        # All cloud related properties
        clouds_type : EnumProperty(
            items=[(
                        'procedural', 
                        'Procedural', 
                        'Enable procedurally generated clouds'
                    ),
                    (
                        'texture', 
                        'Texture', 
                        'Enable texture for the cloud map (textures loading slowly)'
                    ),
                    (
                        'none', 
                        'None', 
                        'Disable clouds'
                    )],
            default = new_atmosphere_defaults["clouds_type"],
            update = toggle_clouds
        )

        clouds_texture_type : EnumProperty(
            items=[(
                        'hdri', 
                        'HDRi', 
                        'Use HDRi environment map for clouds'
                    ),
                    (
                        'map', 
                        '2D Map', 
                        'Use a 2D map from birdseye view for clouds'
                    )],
            default = new_atmosphere_defaults["clouds_texture_type"],
            update = toggle_clouds
        )

        clouds_map_texture : PointerProperty(
            name = "Cloud map Image",
            description="Choose a Cloud map Image",
            type=bpy.types.Image,
            update = clouds_texture_handler,
        )

        clouds_hdri_texture : PointerProperty(
            name = "Cloud map Image (HDRi)",
            description="Choose a Cloud map Image (HDRi)",
            type=bpy.types.Image,
            update = clouds_texture_handler,
        )

        clouds_scale : FloatProperty(
            name = "Scale",
            description = "Clouds scale",
            min = 0,
            soft_max = 15,
            step = 0.1,
            precision = 2,
            default = new_atmosphere_defaults["clouds_scale"],
            unit = "NONE",
            subtype = "FACTOR",
        )

        clouds_detail : FloatProperty(
            name = "Detail",
            description = "Detail of the procedural cloud texture",
            min = 0,
            soft_max = 10,
            step = 0.1,
            precision = 2,
            default = new_atmosphere_defaults["clouds_detail"],
            unit = "NONE",
            subtype = "FACTOR",
        )

        clouds_dimension : FloatProperty(
            name = "Dimension",
            description = "Cloud texture dimension parameter",
            min = 0,
            soft_max = 3,
            step = 0.1,
            precision = 2,
            default = new_atmosphere_defaults["clouds_dimension"],
            unit = "NONE",
            subtype = "FACTOR",
        )

        clouds_lacunarity : FloatProperty(
            name = "Lacunarity",
            description = "Scale of smaller cloud details",
            min = 0,
            soft_max = 10,
            step = 0.1,
            precision = 2,
            default = new_atmosphere_defaults["clouds_lacunarity"],
            unit = "NONE",
            subtype = "FACTOR",
        )

        clouds_min : FloatProperty(
            name = "Min",
            description = "Clouds min",
            min = -1,
            soft_max = 1,
            step = 0.1,
            precision = 2,
            default = new_atmosphere_defaults["clouds_min"],
            unit = "NONE",
            subtype = "FACTOR",
        )

        clouds_max : FloatProperty(
            name = "Max",
            description = "Clouds max",
            min = -1,
            soft_max = 1,
            step = 0.1,
            precision = 2,
            default = new_atmosphere_defaults["clouds_max"],
            unit = "NONE",
            subtype = "FACTOR",
        )

        clouds_thickness : FloatProperty(
            name = "Thickness",
            description = "Clouds thickness",
            min = 0,
            soft_max = 10,
            step = 0.1,
            precision = 2,
            default = new_atmosphere_defaults["clouds_thickness"],
            unit = "NONE",
            subtype = "FACTOR",
        )

        clouds_scattering : FloatVectorProperty(
            name = "",  # leave empty (for layout considerations)
            description = "Clouds Inscattering",
            subtype = "COLOR_GAMMA",
            size = 4,
            min = 0.0,
            max = 1.0,
            default = new_atmosphere_defaults["clouds_scattering"],
        )

        clouds_amount : FloatProperty(
            name = "Self Shadowing",
            description = "Self Shadowing",
            min = 0,
            soft_max = 100,
            step = 0.1,
            precision = 2,
            default = new_atmosphere_defaults["clouds_amount"],
            unit = "NONE",
            subtype = "FACTOR",
        )

        clouds_power : FloatProperty(
            name = "Directional Power",
            description = "Clouds power",
            min = 0,
            soft_max = 100,
            step = 0.1,
            precision = 2,
            default = new_atmosphere_defaults["clouds_power"],
            unit = "NONE",
            subtype = "FACTOR",
        )

        clouds_lighting_intensity : FloatProperty(
            name = "Lighting Intensity",
            description = "Lighting Intensity",
            min = 0,
            soft_max = 10,
            step = 1,
            precision = 2,
            default = new_atmosphere_defaults["clouds_lighting_intensity"],
            unit = "NONE",
            subtype = "FACTOR",
        )

        clouds_location : FloatVectorProperty(
            name = "Location",
            description = "Clouds Location",
            subtype = "XYZ",
            size = 3,
            default = new_atmosphere_defaults["clouds_location"],
        )

        clouds_rotation : FloatVectorProperty(
            name = "Rotation",
            description = "Clouds Rotation",
            subtype = "EULER",
            size = 3,
            default = new_atmosphere_defaults["clouds_rotation"],
        )


        fog_state: EnumProperty(
            items=[(
                        'manual', 
                        'Manual', 
                        'Enable fog for existing objects in the scene manually'
                    ),
                    (
                        'auto', 
                        'Auto', 
                        'Fog is automatically added whenever new material is added to an object'
                    )],
            default = new_atmosphere_defaults["fog_state"],
            update = toggle_fog_handler
        )
    
    bpy.utils.register_class(AtmosphereSettings)

    bpy.types.World.psa_atmosphere_settings = PointerProperty(type = AtmosphereSettings)

    return (new_atmosphere_defaults)
