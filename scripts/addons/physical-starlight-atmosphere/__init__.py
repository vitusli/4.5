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

bl_info = {
	"name": "Physical Starlight and Atmosphere - PSA",
	"author": "Physical Addons",
	"version": (1, 8, 2),
	"blender": (3, 5, 0),
	"description": "Physical Starlight and Atmosphere",
	"location": "World > Atmosphere",
	"doc_url": "https://www.physicaladdons.com/psa/",
	"support": "COMMUNITY",
	"category": "Lighting",
	"tracker_url": "https://discord.gg/wvzPVzj9Vr"
	}

# External library imports
import bpy
from bpy.props import *
from bpy.app.handlers import persistent
from threading import Timer

# Project module imports
from . helpers import tuple_to_str
from . preferences import ( # PSA's preferences UI
	RIG_OT_OpenDocumentation,
	PSA_OT_ReloadDefaultPresets,
	RIG_MT_addon_preferences, 
	update_toolbar_label,
	setup_default_presets,
) 
from . sunlight import *
from . ui import * # PSA's viewport UI 
from . handlers import (
	validate_version, 
	create_sun, 
	initiate_cloud_drivers, 
	initiate_atmosphere_drivers
)
from . sunlight import resolve_sun_duplicates


# Reloads the addon and its code if it has already been loaded, 
# so as to reflect any changes made to the addon's source files 
# (python variables) without having to restart Blender. 
if locals().get('loaded') == True:
	loaded = False
	from importlib import reload
	from sys import modules

	# Reload apporpriate modules.
	modules[__name__] = reload(modules[__name__])
	for name, module in modules.items():
		if name.startswith(f"{__package__}."):
			globals()[name] = reload(module)
	
	# Free up the namespace.
	del reload, modules


# check if sun is being transformed
previous_world = None 

@persistent
def sun_handler(scene, depsgraph):  # allow rotating the sun and seeing changes in the real time
	"""
	Updates viewport whenever appropriate depsgraph changes occur. 
	"""	
	# Check if the the addon-specific settings exist in 
	# the current scene's world (if the current scene's world has an attribute named 'psa_general_settings')
	if not hasattr(scene.world, 'psa_general_settings'):
		return
	
	# Else proceed to reference settings and preferences

	gsettings = scene.world.psa_general_settings
	asettings = scene.world.psa_atmosphere_settings
	prefs = bpy.context.preferences.addons[__name__].preferences

	# Using early returns reduces nesting.
	if not gsettings.enabled == True:
		return 
	
	create_sun()
	# Initiates a loop that iterates through updates in the dependency graph 
	for update in depsgraph.updates:
		#! Delete this when changing the preset system.
		global previous_world
		if update.id.bl_rna.name == 'World' and previous_world != scene.world.name:
			update_blend_version(bpy.context, gsettings)
			previous_world = scene.world.name
			node_tree = scene.world.node_tree
			
			# Set correct physical values intensity multiplier
			# Depending on weather prefs.use_physical_values in enabled. 
			gsettings.intensity_multiplier = 1
			if prefs.use_physical_values == True:
				gsettings.intensity_multiplier = 64
			
			# Make sure to use ACES if selected in addon preferences
			world_output_name = scene.world.psa_exposed.output_node_name
			world_output_node = node_tree.nodes.get(world_output_name)
			if prefs.use_aces == 1 and get_previous_node(world_output_node).name != ACES_CONVERTER_NODE_NAME:
				converter = node_tree.nodes[ACES_CONVERTER_NODE_NAME]
				atmosphere = node_tree.nodes[STARLIGHT_ATMOSPHERE_NODE_NAME]
				node_tree.links.new(converter.outputs[0], world_output_node.inputs[0])
				node_tree.links.new(atmosphere.outputs[0], converter.inputs[0])
			
			# Reference to the sun object inside blender
			sun = scene.world.psa_exposed.sun_object
			
			sun_calculation(bpy.context, depsgraph, 'realtime')

			# Instantiate both atmosphere and cloud drivers.
			initiate_atmosphere_drivers()
			initiate_cloud_drivers()

			# Delete duplicate sun when dropping in a preset since PSA 1.7. 
			resolve_sun_duplicates()

	# Draw the world, If the addon is enabled and not in rendering mode			
	if gsettings.is_rendering == False:
		sun = scene.world.psa_exposed.sun_object
		
		# Check if a sun object exists. If it doesn't, skip the code.
		if sun is not None:
			for update in depsgraph.updates:
				if update.id.original == sun and update.is_updated_transform:
					sun_calculation(bpy.context, depsgraph, 'realtime')


@persistent
def fog_handler(scene, depsgraph): #! Doesnt use depsgraph. Why is it here?
	"""
	Fog event handler that checks if material count has changed then updates the scene. 
	"""	
	
	if not hasattr(bpy.context.scene.world, 'psa_atmosphere_settings'):
		return
	
	# Assign variables
	gsettings = scene.world.psa_general_settings
	asettings = scene.world.psa_atmosphere_settings
	bpy_material_count = len(bpy.data.materials)
	
	if bpy_material_count > gsettings.material_count and asettings.fog_state == 'auto':
		# Set scene.world.psa_general_settings.material_count equal
		# to that of len(bpy.data.materials)
		gsettings.material_count = bpy_material_count
		toggle_fog(1)


# Render engine handler
previous_scene = None 

@persistent
def frame_change_handler(scene, depsgraph):
	"""
	Frame change handler, that redraws the atmosphere if and when
	the scene has changed.
	"""	
	
	if not scene.world or bpy.context.scene.world.psa_exposed.sun_object is None:
		return

	general_settings = scene.world.psa_general_settings # previously g
	atmosphere_settings = scene.world.psa_atmosphere_settings # previously a

	global previous_scene
	if general_settings.enabled and previous_scene != bpy.context.scene:		
		# Redraws the atmosphere and sets the 
		# previous_scene to the current bpy.context.scene
		sun_calculation(bpy.context, depsgraph, 'rendering')
		previous_scene = bpy.context.scene
	
	# Redraw the atmosphere if, in between frames, any of the atmosphere UI parameters have been changed
	current_sun = scene.world.psa_exposed.sun_object.evaluated_get(depsgraph)
	
	atmosphere_props = (
		atmosphere_settings.sun_diameter, atmosphere_settings.sun_temperature, atmosphere_settings.sun_intensity,
		atmosphere_settings.binary_distance, atmosphere_settings.binary_phase, atmosphere_settings.binary_diameter, 
		atmosphere_settings.binary_temperature, atmosphere_settings.binary_intensity, atmosphere_settings.atmosphere_density, 
		atmosphere_settings.atmosphere_height, atmosphere_settings.atmosphere_intensity, atmosphere_settings.night_intensity, 
		atmosphere_settings.atmosphere_color, atmosphere_settings.atmosphere_inscattering, atmosphere_settings.atmosphere_extinction, 
		atmosphere_settings.atmosphere_mie, atmosphere_settings.atmosphere_mie_dir, atmosphere_settings.stars_intensity, 
		atmosphere_settings.stars_gamma, atmosphere_settings.stars_seed, atmosphere_settings.stars_amount,
		atmosphere_settings.stars_scale, atmosphere_settings.stars_temperature_min, atmosphere_settings.stars_temperature_max,
		atmosphere_settings.ground_albedo, atmosphere_settings.ground_offset, atmosphere_settings.atmosphere_distance, 
		atmosphere_settings.atmosphere_falloff, atmosphere_settings.sun_radiance_gamma, 
		
		current_sun.rotation_euler[0], 
		current_sun.rotation_euler[2],

		atmosphere_settings.clouds_scale, atmosphere_settings.clouds_min, atmosphere_settings.clouds_max, 
		atmosphere_settings.clouds_thickness, atmosphere_settings.clouds_scattering, atmosphere_settings.clouds_amount,
		atmosphere_settings.clouds_detail, atmosphere_settings.clouds_dimension, atmosphere_settings.clouds_lacunarity,
        atmosphere_settings.clouds_power, atmosphere_settings.clouds_lighting_intensity, atmosphere_settings.clouds_location[0], 
		atmosphere_settings.clouds_location[1], atmosphere_settings.clouds_location[2], atmosphere_settings.clouds_rotation[0], 
		atmosphere_settings.clouds_rotation[1], atmosphere_settings.clouds_rotation[2]
	)

	atmosphere_prop_strings = map(tuple_to_str, atmosphere_props)
	checksum = "".join(atmosphere_prop_strings)

	# Redraw atmosphere only when a property has changed or if the current frame is the first one?
	if general_settings.enabled and (general_settings.all_props_checksum != checksum or scene.frame_current == 1):  
		sun_calculation(bpy.context, depsgraph, 'rendering')
		general_settings.all_props_checksum = checksum


#! Why declare g? Doesnt really improve readability.
# To prevent triggering sun_handler on rendering we implement `is_rendering` flag
@persistent
def render_init_handler(scene, depsgraph): 
	scene.world.psa_general_settings.is_rendering = True

@persistent
def render_complete_handler(scene, depsgraph): 
	scene.world.psa_general_settings.is_rendering = False

@persistent
def render_cancel_handler(scene, depsgraph): 
	scene.world.psa_general_settings.is_rendering = False

@persistent
def blend_load_handler(scene, depsgraph): 
	# When loading a .blend file we need to check if there's an older version of PSA present and convert
	validate_version(bpy.context, bpy.context.scene.world.psa_general_settings)


def get_classes():
	return (
		# Main classes
		PSA_Preset,
		PA_Exposed,
		GeneralSettings,

		# Operators
		PSA_OT_OpenPresetsFolder,
		PSA_OT_SaveCurrentPreset,
		PSA_OT_DeleteCurrentPreset,
		PSA_OT_CreateNewPreset,
		RIG_OT_RemoveObjectFog,
		RIG_OT_ApplyObjectFog,
		RIG_OT_OpenDocumentation,
		PSA_OT_ReloadDefaultPresets,
		PSA_OT_AddAtmosphere,
		PSA_OT_RemoveAtmosphere,

		# UI
		RIG_PT_StarlightAtmosphereWT,
		RIG_PT_StarlightAtmosphereTB,
		RIG_PT_SunWT,
		RIG_PT_SunTB,
		RIG_PT_BinarySunWT,
		RIG_PT_BinarySunTB,
		RIG_PT_AtmosphereWT,
		RIG_PT_AtmosphereTB,
		RIG_PT_StarsWT,
		RIG_PT_StarsTB,
		RIG_PT_PhysicalCloudsWT,
		RIG_PT_PhysicalCloudsTB,
		RIG_PT_ObjectFogWT,
		RIG_PT_ObjectFogTB,
		RIG_PT_GroundWT,
		RIG_PT_GroundTB,
		RIG_PT_ArtisticControlsWT,
		RIG_PT_ArtisticControlsTB,
		RIG_PT_FooterWT,
		RIG_PT_FooterTB,
		RIG_PT_SubFooterWT,
		RIG_PT_SubFooterTB,
		PSA_UL_PresetList,

		# Preferences
		RIG_MT_addon_preferences,
	)


def register():
	# Register all classes returned by get_classes
	classes = get_classes()
	for cls in classes:
		bpy.utils.register_class(cls)
	
	# Instantiate pointers for our properties
	bpy.types.World.psa_exposed = PointerProperty(type=PA_Exposed)
	bpy.types.World.psa_general_settings = PointerProperty(type=GeneralSettings)
	#bpy.types.World.psa_atmosphere_settings = PointerProperty(type=AtmosphereSettings)
	register_psa_property_groups(bpy.context, {})

	setup_default_presets()

	# Depsgraph change handler
	bpy.app.handlers.depsgraph_update_post.append(sun_handler)
	bpy.app.handlers.depsgraph_update_post.append(fog_handler)
	
	# Frame change handler
	bpy.app.handlers.frame_change_post.append(frame_change_handler)
	
	# Render start/stop handlers
	bpy.app.handlers.render_init.append(render_init_handler)
	bpy.app.handlers.render_complete.append(render_complete_handler)
	bpy.app.handlers.render_cancel.append(render_cancel_handler)
	
	# Blend file load handler
	bpy.app.handlers.load_post.append(blend_load_handler)

	update_toolbar_label(
		bpy.context.preferences.addons[__name__].preferences,
		bpy.context
	)


def unregister():
	classes = get_classes()
	for cls in classes:
		bpy.utils.unregister_class(cls)
	
	# Delete addon specific settings
	del bpy.types.World.psa_atmosphere_settings
	del bpy.types.World.psa_general_settings
	del bpy.types.World.psa_exposed

	# Render start/stop handlers
	bpy.app.handlers.render_cancel.remove(render_cancel_handler)
	bpy.app.handlers.render_complete.remove(render_complete_handler)
	bpy.app.handlers.render_init.remove(render_init_handler)
	
	# Frame change handler
	bpy.app.handlers.frame_change_post.remove(frame_change_handler)
	
	# Depsgraph change handler
	bpy.app.handlers.depsgraph_update_post.remove(fog_handler)
	bpy.app.handlers.depsgraph_update_post.remove(sun_handler)
	
	# Blend file load handler
	bpy.app.handlers.load_post.remove(blend_load_handler)


if __name__ == "__main__":
	register()

# Set loaded to true, the addon has been loaded (registered).
loaded = True
