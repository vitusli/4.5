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


import bpy
from bpy.props import (
    PointerProperty
)
import os
from mathutils import Euler
from . sunlight import *
from . fog import *
from . variables import *
from . versions import update_blend_version


PSA_NODE_GROUPS = (
    STARLIGHT_ATMOSPHERE_NODE_NAME,
    ATMOSPHERE_MATERIAL_NODE_NAME,
    PHYSICAL_INPUTS_NODE_NAME,
    PHYSICAL_CLOUDS_NODE_NAME,
    PHYSICAL_STARS_NODE_NAME,
    PHYSICAL_PLANET_DATA_NODE_NAME,
    PHYSICAL_COORDINATES_NODE_NAME,
    ACES_CONVERTER_NODE_NAME,
)

def check_pco_present(context):
    return hasattr(context.scene.world, 'pco_general_settings') and context.scene.world.pco_general_settings.enabled


def validate_version(context, settings):
    if settings.version_format < VERSION_FORMAT_NUMBER:
        update_blend_version(context, settings)
    elif settings.version_format > VERSION_FORMAT_NUMBER:
        pass # TODO What do we do if newer file is opened in older version?


def enable_atmosphere(self, context):
    psa_gsettings = context.scene.world.psa_general_settings
    psa_asettings = context.scene.world.psa_atmosphere_settings
    psa_exposed = context.scene.world.psa_exposed
    prefs = context.preferences.addons[__name__.split(".")[0]].preferences
    node_tree = context.scene.world.node_tree

    if psa_gsettings.enabled:
        validate_version(context, psa_gsettings)
        set_output_node(node_tree, psa_exposed)
        loaded_nodes = load_and_return_atmosphere_node_groups()
        if check_pco_present(context):
            planets_node = node_tree.nodes.get(context.scene.world.pco_exposed.celestial_node_name)
            loaded_nodes.append(planets_node)
        link_nodes(loaded_nodes)
        organize_nodes(context)
        create_sun()

        # set necessary variables
        psa_gsettings.material_count = len(bpy.data.materials)  # Needed for fog to compare with previous material count
        psa_gsettings.sun_pos_checksum = psa_asettings.azimuth + psa_asettings.elevation  # Has sun moved using obj or az/el
        psa_exposed.atmosphere_node_name = STARLIGHT_ATMOSPHERE_NODE_NAME
        psa_exposed.stars_node_name = PHYSICAL_STARS_NODE_NAME

        if prefs.use_physical_values:
            psa_gsettings.intensity_multiplier = 64
        if check_pco_present(context):
            context.scene.world.pco_general_settings.use_standalone_lighting = False
        first_draw(context, prefs, node_tree, psa_asettings)
        initiate_atmosphere_drivers()
        initiate_cloud_drivers()
    else:
        toggle_fog(0) 
        remove_psa_node_groups(context)
        relink_pco_to_output(context, node_tree)
        if not psa_enabled_in_other_worlds(context):
            purge_node_groups()
            remove_sun()
        if check_pco_present(context):
            context.scene.world.pco_general_settings.use_standalone_lighting = True

def first_draw(context, prefs, node_tree, psa_asettings):
    # make sure ACES state is correct (exact as toggle_aces(addon_prefs, context) to avoid circular dependency hell)
    world_output_name = context.scene.world.psa_exposed.output_node_name
    world_output_node = node_tree.nodes.get(world_output_name)
    if prefs.use_aces == 1 and get_previous_node(world_output_node).name != ACES_CONVERTER_NODE_NAME:
        converter = node_tree.nodes[ACES_CONVERTER_NODE_NAME]
        atmosphere = node_tree.nodes[STARLIGHT_ATMOSPHERE_NODE_NAME]
        node_tree.links.new(converter.outputs[0], world_output_node.inputs[0])
        node_tree.links.new(atmosphere.outputs[0], converter.inputs[0])
    stars_handler(psa_asettings, context)  # See which option is selected in settings and enable it (link it)
    context.scene.world.psa_atmosphere_settings.clouds_scale = context.scene.world.psa_atmosphere_settings.clouds_scale # a way to trigger update fn
    depsgraph = context.evaluated_depsgraph_get()
    sun_calculation(context, depsgraph, 'realtime') # draw atmosphere 


def set_output_node(node_tree, psa_exposed):
    """Store output node name as an exposed variable"""
    active_output = node_tree.get_output_node('ALL')
    psa_exposed.output_node_name = active_output.name
    pre_output = get_previous_node(active_output)
    if pre_output is not None:
        if pre_output.type in ('BACKGROUND', 'EMISSION'):
            psa_exposed.output_node_name = pre_output.name


def relink_pco_to_output(context, node_tree):
    if check_pco_present(context):
        world_output_name = context.scene.world.psa_exposed.output_node_name
        world_output_node = node_tree.nodes.get(world_output_name)
        pco_planets_node = node_tree.nodes.get(context.scene.world.pco_exposed.celestial_node_name)
        node_tree.links.new(pco_planets_node.outputs[0], world_output_node.inputs[0])


def sun_calculation_handler(self, context):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    sun_calculation(context, depsgraph, 'realtime')


def create_sun():
    sun = get_object("Starlight Sun")
    if not sun:
        light_data = bpy.data.lights.new(name="Starlight Sun", type='SUN')
        light_object = bpy.data.objects.new(name="Starlight Sun", object_data=light_data)
        light_object.location = (0, 0, 10)
        light_object.rotation_euler = Euler((-1.519047, 0.0, 0.692023), 'XYZ')
        light_data.shadow_cascade_max_distance = 2000
        bpy.context.collection.objects.link(light_object)  # link light object
        bpy.context.view_layer.objects.active = light_object  # make it active
        sun = light_object
    bpy.context.scene.world.psa_exposed.sun_object = sun


def remove_sun():
    sun = get_object("Starlight Sun")
    if sun:
        light = sun.data
        bpy.data.lights.remove(light)
        bpy.context.scene.world.psa_exposed.sun_object = None

def toggle_fog_handler(self, context):
    asettings = bpy.context.scene.world.psa_atmosphere_settings
    if asettings.fog_state == 'auto':
        toggle_fog(1)


def remove_link(from_node, to_node):
    node_tree = bpy.context.scene.world.node_tree.nodes[PHYSICAL_STARS_NODE_NAME].node_tree
    output = from_node.outputs[0]
    input = to_node.inputs[0]
    for l in output.links :
        if l.to_socket == input :
            node_tree.links.remove(l)


def stars_handler(self, context):
    asettings = context.scene.world.psa_atmosphere_settings
    stars_type = asettings.stars_type

    world = bpy.context.scene.world
    if world is None:
        return
    stars_nodes = world.node_tree.nodes[PHYSICAL_STARS_NODE_NAME].node_tree
    procedural_node = stars_nodes.nodes['procedural_starmap']
    texture_node = stars_nodes.nodes['starmap_output']
    output_node = stars_nodes.nodes['stars_output']

    # remove any existing link
    remove_link(procedural_node, output_node)
    remove_link(texture_node, output_node)

    if stars_type == 'texture':
        stars_nodes.links.new(texture_node.outputs[0], output_node.inputs[0])
    elif stars_type == 'procedural':
        stars_nodes.links.new(procedural_node.outputs[0], output_node.inputs[0])
    output_node.outputs[0].default_value = (0, 0, 0, 1)  # node_tree.reload() alternative to refresh node tree


# Clouds
# UI checkbox handler
def toggle_clouds(self, context):
    asettings = bpy.context.scene.world.psa_atmosphere_settings
    if asettings.clouds_type in ['procedural', 'texture']:
        link_clouds(asettings.clouds_type, asettings.clouds_texture_type)
    else:
        unlink_clouds()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    sun_calculation(bpy.context, depsgraph, 'rendering')


def clouds_texture_handler(self, context):
    world = bpy.context.scene.world
    node_tree = bpy.context.scene.world.node_tree
    if world is None or node_tree.nodes.get(PHYSICAL_CLOUDS_NODE_NAME) is None:
        return
    asettings = bpy.context.scene.world.psa_atmosphere_settings
    clouds_tree = world.node_tree.nodes[PHYSICAL_CLOUDS_NODE_NAME].node_tree
    try:
        clouds_tree.nodes['PSA_fbm'].node_tree.nodes["texture_map_clouds"].image = asettings.clouds_map_texture
        clouds_tree.nodes['PSA_fbm'].node_tree.nodes["hdri_clouds"].image = asettings.clouds_hdri_texture
    except:
        pass


def link_clouds(type, texture_type): 
    node_tree = bpy.context.scene.world.node_tree
    if PHYSICAL_CLOUDS_NODE_NAME in node_tree.nodes:
        output = node_tree.nodes[PHYSICAL_CLOUDS_NODE_NAME].outputs["Result"]
        input = node_tree.nodes[STARLIGHT_ATMOSPHERE_NODE_NAME].inputs["in_clouds"]
        node_tree.links.new(output, input)

        cloud_tree = node_tree.nodes[PHYSICAL_CLOUDS_NODE_NAME].node_tree
        fbm_tree = cloud_tree.nodes["PSA_fbm"].node_tree
        fbm_out = fbm_tree.nodes["fbm_out"].inputs["Fac"]
        if type == 'procedural':
            pc_node = fbm_tree.nodes["procedural_clouds"]
            fbm_tree.links.new(pc_node.outputs[0], fbm_out)
        elif type == 'texture':
            if texture_type == 'map':
                texmap_node = fbm_tree.nodes["texture_map_clouds"]
                fbm_tree.links.new(texmap_node.outputs[0], fbm_out)
            elif texture_type == 'hdri':
                hdri_node = fbm_tree.nodes["hdri_clouds"]
                fbm_tree.links.new(hdri_node.outputs[0], fbm_out)



def unlink_clouds():
    node_tree = bpy.context.scene.world.node_tree
    if PHYSICAL_CLOUDS_NODE_NAME in node_tree.nodes:
        output = node_tree.nodes[PHYSICAL_CLOUDS_NODE_NAME].outputs["Result"]
        input = node_tree.nodes[STARLIGHT_ATMOSPHERE_NODE_NAME].inputs["in_clouds"]
        for l in output.links :
            if l.to_socket == input :
                node_tree.links.remove(l)


def initiate_atmosphere_drivers():
    world = bpy.context.scene.world
    node_tree = world.node_tree
    sun = world.psa_exposed.sun_object
    as_tag = "psa_atmosphere_settings."

    if node_tree.nodes.get(PHYSICAL_COORDINATES_NODE_NAME) is None or node_tree.nodes.get(PHYSICAL_INPUTS_NODE_NAME) is None:
        return
        
    coordinates = node_tree.nodes[PHYSICAL_COORDINATES_NODE_NAME].node_tree
    inputs = node_tree.nodes[PHYSICAL_INPUTS_NODE_NAME].node_tree

    link_driver_simple(coordinates.nodes['sun_rot'].inputs[0], sun, 'default_value', 'rotation_euler.x', index=0, id_type='OBJECT')
    link_driver_simple(coordinates.nodes['sun_rot'].inputs[0], sun, 'default_value', 'rotation_euler.y', index=1, id_type='OBJECT')
    link_driver_simple(coordinates.nodes['sun_rot'].inputs[0], sun, 'default_value', 'rotation_euler.z', index=2, id_type='OBJECT')

    link_driver_simple(inputs.nodes['sun_diameter'].outputs[0], world, 'default_value', as_tag + 'sun_diameter')

    link_driver_simple(inputs.nodes['binary_sun_diameter'].outputs[0], world, 'default_value', as_tag + 'binary_diameter')
    link_driver_simple(inputs.nodes['binary_phase'].outputs[0], world, 'default_value', as_tag + 'binary_phase')
    link_driver_simple(inputs.nodes['binary_distance'].outputs[0], world, 'default_value', as_tag + 'binary_distance')

    link_driver_simple(inputs.nodes['sun_intensity'].outputs[0], world, 'default_value', as_tag + 'sun_intensity')
    link_driver_simple(inputs.nodes['binary_sun_intensity'].outputs[0], world, 'default_value', as_tag + 'binary_intensity')
    link_driver_simple(inputs.nodes['sun_lamp'].outputs[0], world, 'default_value', as_tag + 'sun_lamp')
    link_driver_simple(inputs.nodes['sun_disk'].outputs[0], world, 'default_value', as_tag + 'sun_disk')
    link_driver_simple(inputs.nodes['enable_binary_sun'].outputs[0], world, 'default_value', as_tag + 'enable_binary_sun')

    link_driver_simple(inputs.nodes['night_radiance'].outputs[0], world, 'default_value', as_tag + 'night_intensity')

    link_driver_simple(inputs.nodes['atmosphere_height'].outputs[0], world, 'default_value', as_tag + 'atmosphere_height')
    link_driver_simple(inputs.nodes['atmosphere_density'].outputs[0], world, 'default_value', as_tag + 'atmosphere_density')
    link_driver_simple(inputs.nodes['atmosphere_intensity'].outputs[0], world, 'default_value', as_tag + 'atmosphere_intensity')

    link_driver_simple(inputs.nodes['atmosphere_color'].outputs[0], world, 'default_value', as_tag + 'atmosphere_color.r', index=0)
    link_driver_simple(inputs.nodes['atmosphere_color'].outputs[0], world, 'default_value', as_tag + 'atmosphere_color.g', index=1)
    link_driver_simple(inputs.nodes['atmosphere_color'].outputs[0], world, 'default_value', as_tag + 'atmosphere_color.b', index=2)

    link_driver_simple(inputs.nodes['atmosphere_inscattering'].outputs[0], world, 'default_value', as_tag + 'atmosphere_inscattering.r', index=0)
    link_driver_simple(inputs.nodes['atmosphere_inscattering'].outputs[0], world, 'default_value', as_tag + 'atmosphere_inscattering.g', index=1)
    link_driver_simple(inputs.nodes['atmosphere_inscattering'].outputs[0], world, 'default_value', as_tag + 'atmosphere_inscattering.b', index=2)

    link_driver_simple(inputs.nodes['atmosphere_extinction'].outputs[0], world, 'default_value', as_tag + 'atmosphere_extinction.r', index=0)
    link_driver_simple(inputs.nodes['atmosphere_extinction'].outputs[0], world, 'default_value', as_tag + 'atmosphere_extinction.g', index=1)
    link_driver_simple(inputs.nodes['atmosphere_extinction'].outputs[0], world, 'default_value', as_tag + 'atmosphere_extinction.b', index=2)

    link_driver_simple(inputs.nodes['atmosphere_mie'].outputs[0], world, 'default_value', as_tag + 'atmosphere_mie')
    link_driver_simple(inputs.nodes['atmosphere_mie_dir'].outputs[0], world, 'default_value', as_tag + 'atmosphere_mie_dir')

    link_driver_simple(inputs.nodes['atmosphere_distance'].outputs[0], world, 'default_value', as_tag + 'atmosphere_distance')
    link_driver_simple(inputs.nodes['atmosphere_falloff'].outputs[0], world, 'default_value', as_tag + 'atmosphere_falloff')

    link_driver_simple(inputs.nodes['ground_visible'].outputs[0], world, 'default_value', as_tag + 'ground_visible')

    link_driver_simple(inputs.nodes['ground_albedo'].outputs[0], world, 'default_value', as_tag + 'ground_albedo.r', index=0)
    link_driver_simple(inputs.nodes['ground_albedo'].outputs[0], world, 'default_value', as_tag + 'ground_albedo.g', index=1)
    link_driver_simple(inputs.nodes['ground_albedo'].outputs[0], world, 'default_value', as_tag + 'ground_albedo.b', index=2)

    link_driver_simple(inputs.nodes['ground_offset'].outputs[0], world, 'default_value', as_tag + 'ground_offset')
    link_driver_simple(inputs.nodes['horizon_offset'].outputs[0], world, 'default_value', as_tag + 'horizon_offset')

    link_driver_simple(inputs.nodes['stars_radiance_intensity'].outputs[0], world, 'default_value', as_tag + 'stars_intensity')
    link_driver_simple(inputs.nodes['stars_radiance_gamma'].outputs[0], world, 'default_value', as_tag + 'stars_gamma')
    link_driver_simple(inputs.nodes['stars_seed_value'].outputs[0], world, 'default_value', as_tag + 'stars_seed')
    link_driver_simple(inputs.nodes['stars_amount'].outputs[0], world, 'default_value', as_tag + 'stars_amount')
    link_driver_simple(inputs.nodes['stars_scale'].outputs[0], world, 'default_value', as_tag + 'stars_scale')
    link_driver_simple(inputs.nodes['stars_temp_min'].outputs[0], world, 'default_value', as_tag + 'stars_temperature_min')
    link_driver_simple(inputs.nodes['stars_temp_max'].outputs[0], world, 'default_value', as_tag + 'stars_temperature_max')


def initiate_cloud_drivers():
    world = bpy.context.scene.world
    node_tree = world.node_tree
    if node_tree.nodes.get(PHYSICAL_CLOUDS_NODE_NAME) is not None:
        inputs = node_tree.nodes[PHYSICAL_CLOUDS_NODE_NAME].inputs
        as_tag = "psa_atmosphere_settings."
        link_driver_simple(inputs['Scale'], world, 'default_value', as_tag + "clouds_scale")
        link_driver_simple(inputs['Min'], world, 'default_value', as_tag + "clouds_min")
        link_driver_simple(inputs['Max'], world, 'default_value', as_tag + "clouds_max")
        link_driver_simple(inputs['Thickness'], world, 'default_value', as_tag + "clouds_thickness")
        link_driver_simple(inputs['Val1'], world, 'default_value', as_tag + "clouds_amount")
        link_driver_simple(inputs['Val2'], world, 'default_value', as_tag + "clouds_power")
        link_driver_simple(inputs['Intensity'], world, 'default_value', as_tag + "clouds_lighting_intensity")
        link_driver_simple(inputs['Detail'], world, 'default_value', as_tag + "clouds_detail")
        link_driver_simple(inputs['Dimension'], world, 'default_value', as_tag + "clouds_dimension")
        link_driver_simple(inputs['Lacunarity'], world, 'default_value', as_tag + "clouds_lacunarity")

        link_driver_simple(inputs['Scattering'], world, 'default_value', as_tag + "clouds_scattering.r", index=0)
        link_driver_simple(inputs['Scattering'], world, 'default_value', as_tag + "clouds_scattering.g", index=1)
        link_driver_simple(inputs['Scattering'], world, 'default_value', as_tag + "clouds_scattering.b", index=2)

        link_driver_simple(inputs['Location'], world, 'default_value', as_tag + "clouds_location.x", index=0)
        link_driver_simple(inputs['Location'], world, 'default_value', as_tag + "clouds_location.y", index=1)
        link_driver_simple(inputs['Location'], world, 'default_value', as_tag + "clouds_location.z", index=2)

        link_driver_simple(inputs['Rotation'], world, 'default_value', as_tag + "clouds_rotation.x", index=0)
        link_driver_simple(inputs['Rotation'], world, 'default_value', as_tag + "clouds_rotation.y", index=1)
        link_driver_simple(inputs['Rotation'], world, 'default_value', as_tag + "clouds_rotation.z", index=2)


def stars_texture_handler(self, context):
    world = bpy.context.scene.world
    node_tree = bpy.context.scene.world.node_tree
    if world is None or node_tree.nodes.get(PHYSICAL_STARS_NODE_NAME) is  None:
        return
    asettings = bpy.context.scene.world.psa_atmosphere_settings
    stars_nodes = world.node_tree.nodes[PHYSICAL_STARS_NODE_NAME].node_tree
    try:
        stars_nodes.nodes['starmap'].image = asettings.stars_texture
    except:
        pass


def purge_node_groups():
    """ Delete all Node Groups from the blenderfile """

    # List of shader node group prefixes in the addon
    group_name_prefixes = ('PSA_', '. PSA_')
    for g in bpy.data.node_groups:
        if any(g.name.startswith(s) for s in group_name_prefixes):
            bpy.data.node_groups.remove(g)

def link_nodes(nodes):
    node_tree = bpy.context.scene.world.node_tree
    for node in nodes:
        dictionary = get_links_for_node(node.name)
        if dictionary is None:
            continue
        for node_name, links in dictionary.items():
            target_node = node_tree.nodes[node_name]
            for socket in links:
                node_tree.links.new(node.outputs[socket[0]], target_node.inputs[socket[1]])


def get_links_for_node(node):
    context = bpy.context
    output_node_name = context.scene.world.psa_exposed.output_node_name
    node_links = {}

    def get_stars_links():
        if check_pco_present(context):
            return {context.scene.world.pco_exposed.celestial_node_name: [(0,0)]}
        else:
            return {STARLIGHT_ATMOSPHERE_NODE_NAME:[(0,4)]}

    node_links[PHYSICAL_COORDINATES_NODE_NAME] = {
        PHYSICAL_PLANET_DATA_NODE_NAME:[(0,0)],
        STARLIGHT_ATMOSPHERE_NODE_NAME:[(0,9),(1,10)],
        PHYSICAL_STARS_NODE_NAME:[(2,0)]
    }
    node_links[PHYSICAL_PLANET_DATA_NODE_NAME] = {
        PHYSICAL_CLOUDS_NODE_NAME:[(3,0)],
        STARLIGHT_ATMOSPHERE_NODE_NAME:[(0,11),(1,12),(2,13)]
    }
    node_links[PHYSICAL_CLOUDS_NODE_NAME] = {
        STARLIGHT_ATMOSPHERE_NODE_NAME:[(0,2),(1,3),(2,5),(3,6),(4,7),(5,8)]
    }
    node_links[PHYSICAL_STARS_NODE_NAME] = get_stars_links()
    node_links[STARLIGHT_ATMOSPHERE_NODE_NAME] = {
        output_node_name:[(0,0)]
    }
    if check_pco_present(context):
        node_links[context.scene.world.pco_exposed.celestial_node_name] = {
            STARLIGHT_ATMOSPHERE_NODE_NAME:[(0,4)]
        }
    return node_links.get(node, None)


def load_and_return_atmosphere_node_groups():
    node_groups_list = []
    for node_group_name in PSA_NODE_GROUPS:
        node_groups_list.append(load_and_create_node_group(node_group_name, node_group_name))
    return node_groups_list


def remove_psa_node_groups(context):
    node_tree = context.scene.world.node_tree
    for node_group_name in PSA_NODE_GROUPS:
        delete_node_group(node_group_name, node_tree)


def delete_node_group(node_name, node_tree=None):
    if node_tree is None:
        node_tree = bpy.context.scene.world.node_tree
    node = node_tree.nodes.get(node_name)
    if node is not None:
        node_tree.nodes.remove(node)


def load_and_create_node_group(group_name, node_name):
    node_tree = bpy.context.scene.world.node_tree
    if group_name not in bpy.data.node_groups: # try to import node_group from Blendfile
        path = os.path.join(os.path.dirname(__file__), "blends/atmosphere.blend/NodeTree/")
        bpy.ops.wm.append(filepath=path+node_name, directory=path, filename=node_name, do_reuse_local_id=True)

    if group_name in bpy.data.node_groups:
        group = bpy.data.node_groups[group_name]  # fetch already existing group
        # create and add the new node to the tree
        group_node = node_tree.nodes.new(type='ShaderNodeGroup')
        group_node.name = node_name
        group_node.node_tree = group  # assign the existing group

        return group_node
    return None


def psa_enabled_in_other_worlds(context):
    for world in bpy.data.worlds:
        if hasattr(world, 'psa_general_settings') and world.psa_general_settings.enabled:
            return True
    return False

def organize_nodes(context):
    nodes = context.scene.world.node_tree.nodes
    node_padding = 40
    output_node_name = context.scene.world.psa_exposed.output_node_name

    node_positions = {}
    node_positions[output_node_name] = {
        'top': ACES_CONVERTER_NODE_NAME,
        'left': STARLIGHT_ATMOSPHERE_NODE_NAME,
        'bottom': ATMOSPHERE_MATERIAL_NODE_NAME
    }
    node_positions[STARLIGHT_ATMOSPHERE_NODE_NAME] = {
        'left': PHYSICAL_CLOUDS_NODE_NAME
    }
    node_positions[PHYSICAL_CLOUDS_NODE_NAME] = {
        'left': PHYSICAL_PLANET_DATA_NODE_NAME,
        'top': PHYSICAL_STARS_NODE_NAME
    }
    node_positions[PHYSICAL_PLANET_DATA_NODE_NAME] = {
        'left': PHYSICAL_COORDINATES_NODE_NAME
    }
    node_positions[PHYSICAL_COORDINATES_NODE_NAME] = {
        'bottom': PHYSICAL_INPUTS_NODE_NAME
    }

    for relative_node_name, directions in node_positions.items():
        relative_node = nodes.get(relative_node_name)
        for direction, target_node_name in directions.items():
            node = nodes.get(target_node_name)
            if direction == 'top':
                target_node_x = relative_node.location.x
                target_node_y = relative_node.location.y + node_padding + node.height
                node.location.xy = (target_node_x, target_node_y)
            elif direction == 'left':
                target_node_x = relative_node.location.x - node_padding - node.width
                target_node_y = relative_node.location.y
                node.location.xy = (target_node_x, target_node_y)
            elif direction == 'bottom':
                target_node_x = relative_node.location.x
                target_node_y = relative_node.location.y - node_padding - relative_node.height
                node.location.xy = (target_node_x, target_node_y)
