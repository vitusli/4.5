# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import bpy
from . import drivers_utils

# Load a node group (append from a blend file)
def load_ng(ng_dir, ng_name):
    with bpy.data.libraries.load(ng_dir, link=False) as (data_src, data_dst):
        data_dst.node_groups = [ng_name]
    return bpy.data.node_groups.get(ng_name)

# Lens Flare Material
def create_lf_material(flare):
    node_groups = bpy.data.node_groups
    material = bpy.data.materials.new(flare.name +'_Material')
    material.use_fake_user = True
    material.use_nodes= True
    material.node_tree.nodes.clear()
    material.surface_render_method = 'BLENDED'
    material.blend_method = 'BLEND'
    if bpy.app.version < (4, 3, 0):
        material.shadow_method = 'NONE'
    material.use_transparent_shadow = False
    material.diffuse_color = (0.0, 0.0, 0.0, 0.0)
    material.roughness = 0
    nodes = material.node_tree.nodes
    links = material.node_tree.links
        
    # Adding new nodes
    # Coordinate Node
    tex_coord = nodes.new(type = 'ShaderNodeTexCoord')
    tex_coord.name = 'Texture Coord'
    tex_coord.label = 'Texture Coordinate'
    tex_coord.location = (0.0, 0.0)
    
    # Position Attribute Node
    pos_attr = nodes.new(type = 'ShaderNodeAttribute')
    pos_attr.name = 'Position Attribute'
    pos_attr.label = 'Position Attribute'
    pos_attr.attribute_name = flare.name + '_position'
    pos_attr.attribute_type = 'INSTANCER'
    pos_attr.location = (0.0, -300.0)
    
    # Angle Attribute Node
    angle_attr = nodes.new(type = 'ShaderNodeAttribute')
    angle_attr.name = 'Angle Attribute'
    angle_attr.label = 'Angle Attribute'
    angle_attr.attribute_name = flare.name + '_angle'
    angle_attr.attribute_type = 'INSTANCER'
    angle_attr.location = (0.0, -500.0)
    
    # Scale Factor Attribute Node
    scale_attr = nodes.new(type = 'ShaderNodeAttribute')
    scale_attr.name = 'Scale Fac Attribute'
    scale_attr.label = 'Scale Fac Attribute'
    scale_attr.attribute_name = flare.name + '_scale'
    scale_attr.attribute_type = 'INSTANCER'
    scale_attr.location = (0.0, -700.0)
    
    # Borders Attribute Node
    border_attr = nodes.new(type = 'ShaderNodeAttribute')
    border_attr.name = 'Borders Attribute'
    border_attr.label = 'Borders Attribute'
    border_attr.attribute_name = flare.name + '_borders'
    border_attr.attribute_type = 'INSTANCER'
    border_attr.location = (0.0, -900.0)
    
    # Color Attribute Node
    color_attr = nodes.new(type = 'ShaderNodeAttribute')
    color_attr.name = 'Color Attribute'
    color_attr.label = 'Color Attribute'
    color_attr.attribute_name = flare.name + '_color'
    color_attr.attribute_type = 'INSTANCER'
    color_attr.location = (0.0, -1100.0)
    
    # Intensity Attribute Node
    intensity_attr = nodes.new(type = 'ShaderNodeAttribute')
    intensity_attr.name = 'Intensity Attribute'
    intensity_attr.label = 'Intensity Attribute'
    intensity_attr.attribute_name = flare.name + '_intensity'
    intensity_attr.attribute_type = 'INSTANCER'
    intensity_attr.location = (0.0, -1300.0)
    
    # Vector Math Node
    vec_math = nodes.new(type = 'ShaderNodeVectorMath')
    vec_math.name = 'Vector Math'
    vec_math.label = 'Vector Math'
    vec_math.operation = 'SUBTRACT'
    vec_math.location = (300.0, 0.0)
    
    # Combine Elements node
    ng = combine_ng()
    combine_elements = nodes.new(type="ShaderNodeGroup")
    combine_elements.node_tree = ng
    ng.interface.new_socket(socket_type='NodeSocketColor', name='Color', in_out='OUTPUT')
    combine_elements.name = 'Combine Elements'
    combine_elements.label = 'Combine Elements'
    combine_elements.location = (900.0, 0.0)
    
    # Emission Node
    emission = nodes.new(type = 'ShaderNodeEmission')
    emission.name = 'Emission'
    emission.label = 'Emission'
    emission.inputs[0].default_value = [0.0,0.0,0.0,1.0]
    emission.location = (1200.0, 0.0)
    
    # Transparent Node
    transparent = nodes.new(type = 'ShaderNodeBsdfTransparent')
    transparent.name = 'Transparent'
    transparent.label = 'Transparent'
    transparent.location = (1200.0, -200.0)
    
    # Add Shader Node
    add = nodes.new(type = 'ShaderNodeAddShader')
    add.name = 'Add Shader'
    add.label = 'Add Shader'
    add.location = (1500.0, 0.0)
    
    # Output Node
    output = nodes.new(type = 'ShaderNodeOutputMaterial')
    output.name = 'Output'
    output.label = 'Output'
    output.location = (1800.0, 0.0)
    
    #links
    links.new(tex_coord.outputs[3], vec_math.inputs[0])
    links.new(pos_attr.outputs[1], vec_math.inputs[1])
    links.new(intensity_attr.outputs[2], emission.inputs[1])
    links.new(combine_elements.outputs[0], emission.inputs[0])
    links.new(emission.outputs[0], add.inputs[0])
    links.new(transparent.outputs[0], add.inputs[1])
    links.new(add.outputs[0], output.inputs[0])
    return material

# Backgroud Material
def add_bg_material():
    
    material = bpy.data.materials.new("BG Materia")
    material.use_nodes= True
    material.node_tree.nodes.clear()
    material.blend_method = 'BLEND'
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    loc = [0.0, 0.0]
    x_margine, y_margine = (400.0, 300.0)
    
    #Adding new nodes
    
    tex_coord = nodes.new(type = 'ShaderNodeTexCoord')
    tex_coord.name = 'Texture Coord'
    tex_coord.location = loc
    
    tex_image = nodes.new(type = 'ShaderNodeTexImage')
    tex_image.name = 'Image Texture'
    tex_image.extension = 'CLIP'    
    loc[0] += x_margine
    tex_image.location = loc
    
    emission = nodes.new(type = 'ShaderNodeEmission')
    emission.name = 'Emission Shader'
    emission.inputs[0].default_value = [0.0,0.0,0.0,1.0]
    loc[0] += x_margine
    emission.location = loc
    
    transparent = nodes.new(type = 'ShaderNodeBsdfTransparent')
    transparent.name = 'Transparent Shader'
    loc[0] = emission.location[0]
    loc[1] = emission.location[1] - y_margine
    transparent.location = loc
    
    mix = nodes.new(type = 'ShaderNodeMixShader')
    mix.name = 'Mix'
    loc[0] += x_margine
    loc[1] = emission.location[1]
    mix.location = loc
    
    output = nodes.new(type = 'ShaderNodeOutputMaterial')
    output.name = 'Output'
    loc[0] += x_margine
    output.location = loc
    
    #links
    links.new(tex_coord.outputs[5], tex_image.inputs[0])
    links.new(tex_image.outputs[0], emission.inputs[0])
    links.new(emission.outputs[0], mix.inputs[2])
    links.new(transparent.outputs[0], mix.inputs[1])
    links.new(mix.outputs[0], output.inputs[0])
    
    return material

# Add AOV Nodes
def add_aov_nodes(flare):
    mat = flare.material
    if not hasattr(mat, 'name'):
        return
    if not hasattr(mat, 'node_tree'):
        return
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    combine = nodes.get('Combine Elements')
    if combine is None:
        return
    intensity = nodes.get('Intensity Attribute')
    if intensity is None:
        return
    aov_intensity = nodes.get('AOV Intensity')
    if aov_intensity is None:
        aov_intensity = nodes.new(type = 'ShaderNodeVectorMath')
        aov_intensity.name = 'AOV Intensity'
        aov_intensity.operation = 'SCALE'
        aov_intensity.location = (1500.0, 200.0)
    aov_output = nodes.get('AOV Output')
    if aov_output is None:
        aov_output = nodes.new(type = 'ShaderNodeOutputAOV')
        aov_output.name = 'AOV Output'
        aov_output.aov_name = flare.name
        aov_output.location = (1800.0, 200.0)
    links.new(combine.outputs[0], aov_intensity.inputs[0])
    links.new(intensity.outputs[2], aov_intensity.inputs[3])
    links.new(aov_intensity.outputs[0], aov_output.inputs[0])
    
# Remove AOV Nodes
def remove_aov_nodes(flare):
    mat = flare.material
    if not hasattr(mat, 'name'):
        return
    if not hasattr(mat, 'node_tree'):
        return
    nodes = mat.node_tree.nodes
    aov_intensity = nodes.get('AOV Intensity')
    if aov_intensity is not None:
        nodes.remove(aov_intensity)
    aov_output = nodes.get('AOV Output')
    if aov_output is not None:
        nodes.remove(aov_output)

# Combine Elements node group
def combine_ng():
    node_groups = bpy.data.node_groups
    ng_name = 'LF_combine_ng'
    combine_ele_group = node_groups.new(ng_name, 'ShaderNodeTree')    
    nodes = combine_ele_group.nodes
    
    group_input = nodes.new('NodeGroupInput')
    group_input.name = 'Input'    
    group_input.location = (-200.0, 0.0)
        
    group_output = nodes.new('NodeGroupOutput')
    group_output.name = 'Output'    
    group_output.location = (0.0, 0.0)
    return combine_ele_group

# Prepare the Combine Elements node
def prepare_combine_node(combine_node, count, name):
    ng = combine_node.node_tree
    nodes, links = (ng.nodes, ng.links)
    input, output = (nodes['Input'], nodes['Output'])
    # reset
    for node in nodes:
        if node.type in ['MIX']:
            nodes.remove(node)
    output.inputs[0].default_value = [0,0,0,1]
    
    items_tree = ng.interface.items_tree
    sockets = [i for i in items_tree if i.item_type == 'SOCKET' and i.in_out == 'INPUT']
    for socket in sockets:
        ng.interface.remove(socket)
    
    output.location = ((count)*150.0, (count)*-50)
    # add inputs
    for i in range(count):
        ng.interface.new_socket(socket_type='NodeSocketColor', name=name+str(i+1), in_out='INPUT')
    # 0 element case
    if not count:
        return
    # 1 element case
    if count == 1:
        links.new(input.outputs[0], output.inputs[0])
        return
    # generate mix rgb nodes
    mix_sockets = []
    mix_out = None
    for i in range(count-1):
        add_node = nodes.new(type ="ShaderNodeMix")
        add_node.data_type = 'RGBA'
        add_node.inputs[0].default_value = 1.0
        add_node.blend_type = 'ADD'
        add_node.hide = True
        add_node.location = (i*150, i*-50)
        if mix_out is not None:
            links.new(mix_out, add_node.inputs[6])
        if i == 0:
            mix_sockets.append(add_node.inputs[6])
        mix_sockets.append(add_node.inputs[7])
        if i == count-2:
            links.new(add_node.outputs[2], output.inputs[0])
        else:
            mix_out = add_node.outputs[2]
    # link inputs
    for i in range(count):
        links.new(input.outputs[i], mix_sockets[i])
        
# Cleanup ghosts node group
def cleanup_ghosts_ng(node_group):
    nodes = node_group.nodes
    # remove combine node
    combine_node = nodes.get('Combine Ghosts')
    if combine_node is not None:
        nodes.remove(combine_node)
    # remove ghosts nodes
    for n in nodes:
        if not 'Single Ghost ' in n.name:
            continue
        nodes.remove(n)
        
# Cleanup streaks node group
def cleanup_streaks_ng(node_group):
    nodes = node_group.nodes
    # remove combine node
    combine_node = nodes.get('Combine Streaks')
    if combine_node is not None:
        nodes.remove(combine_node)
    # remove streaks nodes
    for n in nodes:
        if not 'Single Streak ' in n.name:
            continue
        nodes.remove(n)

# Get/Create an element's node
def get_element_node(context, flare, element, nodes, ng_path):
    ele_node = nodes.get(element.name)
    if ele_node is not None:
        return ele_node
    ele_dict = elements_dict.get(element.type)
    ng_name = ele_dict.get('NG_NAME')
    node_groups = bpy.data.node_groups
    ng = node_groups.get(ng_name)
    if ng is None:
        node_group = load_ng(ng_path, ng_name)
    else:
        node_group = ng.copy()
    ele_node = nodes.new(type="ShaderNodeGroup")
    ele_node.node_tree = node_group
    ele_node.name = element.name
    ele_node.label = element.ui_name
    if element.type == 'GHOSTS':
        cleanup_ghosts_ng(node_group)
    elif element.type == 'STREAKS':
        cleanup_streaks_ng(node_group)
    color_ramp = node_group.nodes.get('ProximityRamp')
    if color_ramp is not None:
        reset_color_ramp(color_ramp)
    ele_dict['ADD_DRIVERS'](context, flare, element, ele_node)
    return ele_node

def setup_glow(context, flare, element, element_node):
    scn = context.scene
    nodes = element_node.node_tree.nodes
    # Drivers
    v = 'default_value'
    # Location
    loc = nodes.get('Loc')
    # X Multiplier
    loc.inputs[1].driver_remove("default_value", 0)
    driver = loc.inputs[1].driver_add("default_value", 0)
    path = drivers_utils.element_prop_path(element, flare, 'position')
    drivers_utils.add_prop_var(driver, 'pos', 'SCENE', scn, path)
    path = drivers_utils.element_prop_path(element, flare, 'lock_x')
    drivers_utils.add_prop_var(driver, 'lock_x', 'SCENE', scn, path)
    driver.driver.expression = '-pos*(1-lock_x)'
    # Y Multiplier
    loc.inputs[1].driver_remove("default_value", 1)
    driver = loc.inputs[1].driver_add("default_value", 1)
    path = drivers_utils.element_prop_path(element, flare, 'position')
    drivers_utils.add_prop_var(driver, 'pos', 'SCENE', scn, path)
    path = drivers_utils.element_prop_path(element, flare, 'lock_y')
    drivers_utils.add_prop_var(driver, 'lock_y', 'SCENE', scn, path)
    driver.driver.expression = '-pos*(1-lock_y)'
    # X Addend
    path = drivers_utils.element_prop_path(element, flare, 'location_x')
    drivers_utils.add_driver(loc.inputs[2], v, 'location_x', 'SCENE', scn, path,'location_x', 0)
    # Y Addend
    path = drivers_utils.element_prop_path(element, flare, 'location_y')
    drivers_utils.add_driver(loc.inputs[2], v, 'location_y', 'SCENE', scn, path,'location_y', 1)
    # Rotation
    rot = nodes.get('Rot')
    # Z Multiplier
    path = drivers_utils.element_prop_path(element, flare, 'track_target')
    drivers_utils.add_driver(rot.inputs[1], v, 'track_target', 'SCENE', scn, path,'track_target', 2)
    # Z Addend
    path = drivers_utils.element_prop_path(element, flare, 'rotation')
    drivers_utils.add_driver(rot.inputs[2], v, 'rotation', 'SCENE', scn, path,'rotation', 2)
    # Scale
    scale = nodes.get('Scale')
    # X
    path = drivers_utils.element_prop_path(element, flare, 'scale_x')
    drivers_utils.add_driver(scale.inputs[0], v, 'scale_x', 'SCENE', scn, path,'scale_x', 0)
    # Y
    path = drivers_utils.element_prop_path(element, flare, 'scale_y')
    drivers_utils.add_driver(scale.inputs[0], v, 'scale_y', 'SCENE', scn, path,'scale_y', 1)
    # Map Range Interpolation
    map_range = nodes.get('Map Range')
    path = drivers_utils.element_prop_path(element, flare, 'interpolation')
    drivers_utils.add_driver(map_range, 'interpolation_type', 'interpolation', 'SCENE', scn, path,'interpolation')
    # Falloff
    falloff = nodes.get('Falloff')
    path = drivers_utils.element_prop_path(element, flare, 'light_falloff')
    drivers_utils.add_driver(falloff.inputs[1], v, 'falloff', 'SCENE', scn, path,'falloff')
    # Color
    col = nodes.get('Color')
    path = drivers_utils.element_prop_path(element, flare, 'color')
    drivers_utils.add_driver(col.inputs[6], v, 'color', 'SCENE', scn, path,'color', -1, 4)
    # Use Global Color
    path = drivers_utils.element_prop_path(element, flare, 'use_global_color')
    drivers_utils.add_driver(col.inputs[0], v, 'use_g_color', 'SCENE', scn, path,'use_g_color')
    # Intensity
    proximity = nodes.get('Proximity')
    path = drivers_utils.element_prop_path(element, flare, 'intensity')
    drivers_utils.add_driver(proximity.inputs[2], v, 'intensity', 'SCENE', scn, path,'intensity')
    # proximity intensity
    proximity.inputs[3].driver_remove("default_value")
    driver = proximity.inputs[3].driver_add("default_value")
    path = drivers_utils.element_prop_path(element, flare, 'intensity')
    drivers_utils.add_prop_var(driver, 'intensity', 'SCENE', scn, path)
    path = drivers_utils.element_prop_path(element, flare, 'proximity_trigger')
    drivers_utils.add_prop_var(driver, 'enabled', 'SCENE', scn, path)
    path = drivers_utils.element_prop_path(element, flare, 'proximity_intensity')
    drivers_utils.add_prop_var(driver, 'proximity_intensity', 'SCENE', scn, path)
    driver.driver.expression = 'proximity_intensity if enabled else intensity'
    
def setup_image(context, flare, element, element_node):
    scn = context.scene
    nodes = element_node.node_tree.nodes
    # Drivers
    v = 'default_value'

    # Location
    loc = nodes.get('Loc')
    # X Multiplier
    loc.inputs[1].driver_remove("default_value", 0)
    driver = loc.inputs[1].driver_add("default_value", 0)
    path = drivers_utils.element_prop_path(element, flare, 'position')
    drivers_utils.add_prop_var(driver, 'pos', 'SCENE', scn, path)
    path = drivers_utils.element_prop_path(element, flare, 'lock_x')
    drivers_utils.add_prop_var(driver, 'lock_x', 'SCENE', scn, path)
    driver.driver.expression = '-pos*(1-lock_x)'
    # Y Multiplier
    loc.inputs[1].driver_remove("default_value", 1)
    driver = loc.inputs[1].driver_add("default_value", 1)
    path = drivers_utils.element_prop_path(element, flare, 'position')
    drivers_utils.add_prop_var(driver, 'pos', 'SCENE', scn, path)
    path = drivers_utils.element_prop_path(element, flare, 'lock_y')
    drivers_utils.add_prop_var(driver, 'lock_y', 'SCENE', scn, path)
    driver.driver.expression = '-pos*(1-lock_y)'
    # X Addend
    path = drivers_utils.element_prop_path(element, flare, 'location_x')
    drivers_utils.add_driver(loc.inputs[2], v, 'location_x', 'SCENE', scn, path,'location_x', 0)
    # Y Addend
    path = drivers_utils.element_prop_path(element, flare, 'location_y')
    drivers_utils.add_driver(loc.inputs[2], v, 'location_y', 'SCENE', scn, path,'location_y', 1)
    # Location 2
    loc = nodes.get('Loc2')
    # X Multiplier
    loc.inputs[1].driver_remove("default_value", 0)
    driver = loc.inputs[1].driver_add("default_value", 0)
    path = drivers_utils.element_prop_path(element, flare, 'position')
    drivers_utils.add_prop_var(driver, 'pos', 'SCENE', scn, path)
    path = drivers_utils.element_prop_path(element, flare, 'lock_x')
    drivers_utils.add_prop_var(driver, 'lock_x', 'SCENE', scn, path)
    path = drivers_utils.element_prop_path(element, flare, 'fade_distance')
    drivers_utils.add_prop_var(driver, 'distance', 'SCENE', scn, path)
    driver.driver.expression = '-pos*(1+(distance/2))*(1-lock_x)'
    # Y Multiplier
    loc.inputs[1].driver_remove("default_value", 1)
    driver = loc.inputs[1].driver_add("default_value", 1)
    path = drivers_utils.element_prop_path(element, flare, 'position')
    drivers_utils.add_prop_var(driver, 'pos', 'SCENE', scn, path)
    path = drivers_utils.element_prop_path(element, flare, 'lock_y')
    drivers_utils.add_prop_var(driver, 'lock_y', 'SCENE', scn, path)
    path = drivers_utils.element_prop_path(element, flare, 'fade_distance')
    drivers_utils.add_prop_var(driver, 'distance', 'SCENE', scn, path)
    driver.driver.expression = '-pos*(1+(distance/2))*(1-lock_y)'
    # X Addend
    path = drivers_utils.element_prop_path(element, flare, 'location_x')
    drivers_utils.add_driver(loc.inputs[2], v, 'location_x', 'SCENE', scn, path,'location_x', 0)
    # Y Addend
    path = drivers_utils.element_prop_path(element, flare, 'location_y')
    drivers_utils.add_driver(loc.inputs[2], v, 'location_y', 'SCENE', scn, path,'location_y', 1)
    # Rotation
    rot = nodes.get('Rot')
    # Z Multiplier
    path = drivers_utils.element_prop_path(element, flare, 'track_target')
    drivers_utils.add_driver(rot.inputs[1], v, 'track_target', 'SCENE', scn, path,'track_target', 2)
    # Z Addend
    path = drivers_utils.element_prop_path(element, flare, 'rotation')
    drivers_utils.add_driver(rot.inputs[2], v, 'rotation', 'SCENE', scn, path,'rotation', 2)
    # Scale
    scale = nodes.get('Scale')
    # X
    path = drivers_utils.element_prop_path(element, flare, 'scale_x')
    drivers_utils.add_driver(scale.inputs[0], v, 'scale_x', 'SCENE', scn, path,'scale_x', 0)
    # Y
    path = drivers_utils.element_prop_path(element, flare, 'scale_y')
    drivers_utils.add_driver(scale.inputs[0], v, 'scale_y', 'SCENE', scn, path,'scale_y', 1)
    # Feathering
    feather = nodes.get('Feather')
    path = drivers_utils.element_prop_path(element, flare, 'feather')
    drivers_utils.add_driver(feather.inputs[1], v, 'feather', 'SCENE', scn, path,'feather')
    # Color
    col = nodes.get('Color')
    path = drivers_utils.element_prop_path(element, flare, 'color')
    drivers_utils.add_driver(col.inputs[6], v, 'color', 'SCENE', scn, path,'color', -1, 4)
    # Use Global Color
    path = drivers_utils.element_prop_path(element, flare, 'use_global_color')
    drivers_utils.add_driver(col.inputs[0], v, 'use_g_color', 'SCENE', scn, path,'use_g_color')
    # Intensity
    proximity = nodes.get('Proximity')
    path = drivers_utils.element_prop_path(element, flare, 'intensity')
    drivers_utils.add_driver(proximity.inputs[2], v, 'intensity', 'SCENE', scn, path,'intensity')
    # proximity intensity
    proximity.inputs[3].driver_remove("default_value")
    driver = proximity.inputs[3].driver_add("default_value")
    path = drivers_utils.element_prop_path(element, flare, 'intensity')
    drivers_utils.add_prop_var(driver, 'intensity', 'SCENE', scn, path)
    path = drivers_utils.element_prop_path(element, flare, 'proximity_trigger')
    drivers_utils.add_prop_var(driver, 'enabled', 'SCENE', scn, path)
    path = drivers_utils.element_prop_path(element, flare, 'proximity_intensity')
    drivers_utils.add_prop_var(driver, 'proximity_intensity', 'SCENE', scn, path)
    driver.driver.expression = 'proximity_intensity if enabled else intensity'
    # Default Values
    element.scale_x, element.scale_y = (0.25, 0.25)
    
def setup_streaks(context, flare, element, element_node):
    scn = context.scene
    nodes = element_node.node_tree.nodes
    # Drivers
    v = 'default_value'
    
    # Location
    loc = nodes.get('Loc')
    # X Multiplier
    loc.inputs[1].driver_remove("default_value", 0)
    driver = loc.inputs[1].driver_add("default_value", 0)
    path = drivers_utils.element_prop_path(element, flare, 'position')
    drivers_utils.add_prop_var(driver, 'pos', 'SCENE', scn, path)
    path = drivers_utils.element_prop_path(element, flare, 'lock_x')
    drivers_utils.add_prop_var(driver, 'lock_x', 'SCENE', scn, path)
    driver.driver.expression = '-pos*(1-lock_x)'
    # Y Multiplier
    loc.inputs[1].driver_remove("default_value", 1)
    driver = loc.inputs[1].driver_add("default_value", 1)
    path = drivers_utils.element_prop_path(element, flare, 'position')
    drivers_utils.add_prop_var(driver, 'pos', 'SCENE', scn, path)
    path = drivers_utils.element_prop_path(element, flare, 'lock_y')
    drivers_utils.add_prop_var(driver, 'lock_y', 'SCENE', scn, path)
    driver.driver.expression = '-pos*(1-lock_y)'
    # X Addend
    path = drivers_utils.element_prop_path(element, flare, 'location_x')
    drivers_utils.add_driver(loc.inputs[2], v, 'location_x', 'SCENE', scn, path,'location_x', 0)
    # Y Addend
    path = drivers_utils.element_prop_path(element, flare, 'location_y')
    drivers_utils.add_driver(loc.inputs[2], v, 'location_y', 'SCENE', scn, path,'location_y', 1)
    # Scale
    scale = nodes.get('Scale')
    # X
    path = drivers_utils.element_prop_path(element, flare, 'scale_x')
    drivers_utils.add_driver(scale.inputs[0], v, 'scale_x', 'SCENE', scn, path,'scale_x', 0)
    # Y
    path = drivers_utils.element_prop_path(element, flare, 'scale_y')
    drivers_utils.add_driver(scale.inputs[0], v, 'scale_y', 'SCENE', scn, path,'scale_y', 1)
    # Map Range Interpolation
    map_range = nodes.get('Map Range')
    path = drivers_utils.element_prop_path(element, flare, 'interpolation')
    drivers_utils.add_driver(map_range, 'interpolation_type', 'interpolation', 'SCENE', scn, path,'interpolation')
    # Falloff
    falloff = nodes.get('Falloff')
    path = drivers_utils.element_prop_path(element, flare, 'light_falloff')
    drivers_utils.add_driver(falloff.inputs[1], v, 'falloff', 'SCENE', scn, path,'falloff')
    # Color
    col = nodes.get('Color')
    path = drivers_utils.element_prop_path(element, flare, 'color')
    drivers_utils.add_driver(col.inputs[6], v, 'color', 'SCENE', scn, path,'color', -1, 4)
    # Use Global Color
    path = drivers_utils.element_prop_path(element, flare, 'use_global_color')
    drivers_utils.add_driver(col.inputs[0], v, 'use_g_color', 'SCENE', scn, path,'use_g_color')
    # Intensity
    proximity = nodes.get('Proximity')
    path = drivers_utils.element_prop_path(element, flare, 'intensity')
    drivers_utils.add_driver(proximity.inputs[2], v, 'intensity', 'SCENE', scn, path,'intensity')
    # proximity intensity
    proximity.inputs[3].driver_remove("default_value")
    driver = proximity.inputs[3].driver_add("default_value")
    path = drivers_utils.element_prop_path(element, flare, 'intensity')
    drivers_utils.add_prop_var(driver, 'intensity', 'SCENE', scn, path)
    path = drivers_utils.element_prop_path(element, flare, 'proximity_trigger')
    drivers_utils.add_prop_var(driver, 'enabled', 'SCENE', scn, path)
    path = drivers_utils.element_prop_path(element, flare, 'proximity_intensity')
    drivers_utils.add_prop_var(driver, 'proximity_intensity', 'SCENE', scn, path)
    driver.driver.expression = 'proximity_intensity if enabled else intensity'
    # Default Values
    element.scale_x, element.scale_y = (8.0, 0.4)
    element.light_falloff = 2.0
    element.streaks_count = 1
    
def setup_ghosts(context, flare, element, element_node):
    scn = context.scene
    nodes = element_node.node_tree.nodes
    # Drivers
    v = 'default_value'
    
    # Use Global Color
    col = nodes.get('Color')
    path = drivers_utils.element_prop_path(element, flare, 'use_global_color')
    drivers_utils.add_driver(col.inputs[0], v, 'use_g_color', 'SCENE', scn, path,'use_g_color')
    # Intensity
    proximity = nodes.get('Proximity')
    path = drivers_utils.element_prop_path(element, flare, 'intensity')
    drivers_utils.add_driver(proximity.inputs[2], v, 'intensity', 'SCENE', scn, path,'intensity')
    # proximity intensity
    proximity.inputs[3].driver_remove("default_value")
    driver = proximity.inputs[3].driver_add("default_value")
    path = drivers_utils.element_prop_path(element, flare, 'intensity')
    drivers_utils.add_prop_var(driver, 'intensity', 'SCENE', scn, path)
    path = drivers_utils.element_prop_path(element, flare, 'proximity_trigger')
    drivers_utils.add_prop_var(driver, 'enabled', 'SCENE', scn, path)
    path = drivers_utils.element_prop_path(element, flare, 'proximity_intensity')
    drivers_utils.add_prop_var(driver, 'proximity_intensity', 'SCENE', scn, path)
    driver.driver.expression = 'proximity_intensity if enabled else intensity'
    # Default Values
    element.scale_x, element.scale_y = (0.15, 0.15)
    element.position = 1.25
    element.intensity = 0.1
    element.random_scale = 0.5
    element.random_scale_seed = 6
    element.ghosts_count = 10
    
def setup_ring(context, flare, element, element_node):
    scn = context.scene
    nodes = element_node.node_tree.nodes
    # Drivers
    v = 'default_value'
    
    # Location
    loc = nodes.get('Loc')
    # X Multiplier
    loc.inputs[1].driver_remove("default_value", 0)
    driver = loc.inputs[1].driver_add("default_value", 0)
    path = drivers_utils.element_prop_path(element, flare, 'position')
    drivers_utils.add_prop_var(driver, 'pos', 'SCENE', scn, path)
    path = drivers_utils.element_prop_path(element, flare, 'lock_x')
    drivers_utils.add_prop_var(driver, 'lock_x', 'SCENE', scn, path)
    driver.driver.expression = '-pos*(1-lock_x)'
    # Y Multiplier
    loc.inputs[1].driver_remove("default_value", 1)
    driver = loc.inputs[1].driver_add("default_value", 1)
    path = drivers_utils.element_prop_path(element, flare, 'position')
    drivers_utils.add_prop_var(driver, 'pos', 'SCENE', scn, path)
    path = drivers_utils.element_prop_path(element, flare, 'lock_y')
    drivers_utils.add_prop_var(driver, 'lock_y', 'SCENE', scn, path)
    driver.driver.expression = '-pos*(1-lock_y)'
    # X Addend
    path = drivers_utils.element_prop_path(element, flare, 'location_x')
    drivers_utils.add_driver(loc.inputs[2], v, 'location_x', 'SCENE', scn, path,'location_x', 0)
    # Y Addend
    path = drivers_utils.element_prop_path(element, flare, 'location_y')
    drivers_utils.add_driver(loc.inputs[2], v, 'location_y', 'SCENE', scn, path,'location_y', 1)
    # Rotation
    rot = nodes.get('Rot')
    # Z Multiplier
    path = drivers_utils.element_prop_path(element, flare, 'track_target')
    drivers_utils.add_driver(rot.inputs[1], v, 'track_target', 'SCENE', scn, path,'track_target', 2)
    # Z Addend
    path = drivers_utils.element_prop_path(element, flare, 'rotation')
    drivers_utils.add_driver(rot.inputs[2], v, 'rotation', 'SCENE', scn, path,'rotation', 2)
    # Scale
    scale = nodes.get('Scale')
    # X
    path = drivers_utils.element_prop_path(element, flare, 'scale_x')
    drivers_utils.add_driver(scale.inputs[0], v, 'scale_x', 'SCENE', scn, path,'scale_x', 0)
    # Y
    path = drivers_utils.element_prop_path(element, flare, 'scale_y')
    drivers_utils.add_driver(scale.inputs[0], v, 'scale_y', 'SCENE', scn, path,'scale_y', 1)
    # Color
    col = nodes.get('Color')
    path = drivers_utils.element_prop_path(element, flare, 'color')
    drivers_utils.add_driver(col.inputs[6], v, 'color', 'SCENE', scn, path,'color', -1, 4)
    # Use Global Color
    path = drivers_utils.element_prop_path(element, flare, 'use_global_color')
    drivers_utils.add_driver(col.inputs[0], v, 'use_g_color', 'SCENE', scn, path,'use_g_color')
    # Intensity
    proximity = nodes.get('Proximity')
    path = drivers_utils.element_prop_path(element, flare, 'intensity')
    drivers_utils.add_driver(proximity.inputs[2], v, 'intensity', 'SCENE', scn, path,'intensity')
    # proximity intensity
    proximity.inputs[3].driver_remove("default_value")
    driver = proximity.inputs[3].driver_add("default_value")
    path = drivers_utils.element_prop_path(element, flare, 'intensity')
    drivers_utils.add_prop_var(driver, 'intensity', 'SCENE', scn, path)
    path = drivers_utils.element_prop_path(element, flare, 'proximity_trigger')
    drivers_utils.add_prop_var(driver, 'enabled', 'SCENE', scn, path)
    path = drivers_utils.element_prop_path(element, flare, 'proximity_intensity')
    drivers_utils.add_prop_var(driver, 'proximity_intensity', 'SCENE', scn, path)
    driver.driver.expression = 'proximity_intensity if enabled else intensity'
    # Color Ramp
    col_ramp = nodes.get('Color Ramp')
    ele = col_ramp.color_ramp.elements[2]
    path = drivers_utils.element_prop_path(element, flare, 'ring_ray_length')
    drivers_utils.add_driver(ele, 'position', 'length', 'SCENE', scn, path,'length')
    ele = col_ramp.color_ramp.elements[1]
    path = drivers_utils.element_prop_path(element, flare, 'ring_ray_length')
    drivers_utils.add_driver(ele, 'position', 'length', 'SCENE', scn, path,'length/2')
    # Color Ramp Interpolation
    col_ramp = nodes.get('Color Ramp2')
    path = drivers_utils.element_prop_path(element, flare, 'spectrum_interpolation')
    drivers_utils.add_driver(col_ramp.color_ramp, 'interpolation', 'interpolation', 'SCENE', scn, path,'interpolation')
    # Map Range Interpolation
    map_range = nodes.get('Map Range3')
    path = drivers_utils.element_prop_path(element, flare, 'interpolation')
    drivers_utils.add_driver(map_range, 'interpolation_type', 'interpolation', 'SCENE', scn, path,'interpolation')
    # Count
    map_range = nodes.get('Map Range4')
    path = drivers_utils.element_prop_path(element, flare, 'ring_ray_count')
    drivers_utils.add_driver(map_range.inputs[4], v, 'count', 'SCENE', scn, path,'count>0')
    map_range = nodes.get('Map Range2')
    drivers_utils.add_driver(map_range.inputs[3], v, 'count', 'SCENE', scn, path,'count<1')
    math = nodes.get('Math2')
    drivers_utils.add_driver(math.inputs[1], v, 'count', 'SCENE', scn, path,'count')
    # Width
    path = drivers_utils.element_prop_path(element, flare, 'ring_ray_width')
    drivers_utils.add_driver(map_range.inputs[1], v, 'width', 'SCENE', scn, path,'(1-width)/2')
    # Noise Scale
    scale = nodes.get('TexScale')
    path = drivers_utils.element_prop_path(element, flare, 'noise_scale')
    drivers_utils.add_driver(scale.inputs[3], v, 'noise_scale', 'SCENE', scn, path,'noise_scale')
    # Roughness
    roughness = nodes.get('TexMix')
    path = drivers_utils.element_prop_path(element, flare, 'distortion')
    drivers_utils.add_driver(roughness.inputs[0], v, 'distortion', 'SCENE', scn, path,'distortion/10')
    # Ray Length
    math = nodes.get('Math10')
    math.inputs[1].driver_remove("default_value")
    driver = math.inputs[1].driver_add("default_value")
    path = drivers_utils.element_prop_path(element, flare, 'ring_ray_length')
    drivers_utils.add_prop_var(driver, 'length', 'SCENE', scn, path)
    path = drivers_utils.element_prop_path(element, flare, 'spectrum_offset')
    drivers_utils.add_prop_var(driver, 'spectrum_offset', 'SCENE', scn, path)
    driver.driver.expression = '1/length*spectrum_offset'
    # Random Length
    math = nodes.get('Math7')
    path = drivers_utils.element_prop_path(element, flare, 'ring_random_length')
    drivers_utils.add_driver(math.inputs[1], v, 'ran_length', 'SCENE', scn, path,'-ran_length')
    # Length Seed
    noise = nodes.get('Noise2')
    path = drivers_utils.element_prop_path(element, flare, 'ring_length_seed')
    drivers_utils.add_driver(noise.inputs[1], v, 'seed', 'SCENE', scn, path,'seed')
    # Random Width
    mix = nodes.get('Mix2')
    path = drivers_utils.element_prop_path(element, flare, 'ring_random_width')
    drivers_utils.add_driver(mix.inputs[0], v, 'ran_width', 'SCENE', scn, path,'ran_width')
    # Width Seed
    noise = nodes.get('Noise')
    path = drivers_utils.element_prop_path(element, flare, 'ring_width_seed')
    drivers_utils.add_driver(noise.inputs[1], v, 'seed', 'SCENE', scn, path,'seed')
    # Circular Completion
    map_range = nodes.get('Map Range5')
    path = drivers_utils.element_prop_path(element, flare, 'circular_completion')
    drivers_utils.add_driver(map_range.inputs[1], v, 'completion', 'SCENE', scn, path,'lerp(-0.5, 0.49, completion)')
    # Circular Completion Feather
    map_range = nodes.get('Map Range6')
    path = drivers_utils.element_prop_path(element, flare, 'completion_feather')
    drivers_utils.add_driver(map_range.inputs[1], v, 'feather', 'SCENE', scn, path,'lerp(0.499, 0.0, feather)')
    # Use Spectrum
    mix = nodes.get('Mix3')
    path = drivers_utils.element_prop_path(element, flare, 'use_spectrum')
    drivers_utils.add_driver(mix.inputs[0], v, 'use_spectrum', 'SCENE', scn, path,'use_spectrum')
    # Default Values
    element.scale_x, element.scale_y = (0.1, 0.1)
    
def setup_hoop(context, flare, element, element_node):
    scn = context.scene
    nodes = element_node.node_tree.nodes
    # Drivers
    v = 'default_value'
    
    # Location
    loc = nodes.get('Loc')
    # X Addend
    path = drivers_utils.element_prop_path(element, flare, 'position')
    drivers_utils.add_driver(loc.inputs[1], v, 'pos', 'SCENE', scn, path,'-pos-0.82', 0)
    # Rotation
    rot = nodes.get('Rot')
    # Z Addend
    rot.inputs[1].driver_remove("default_value", 2)
    driver = rot.inputs[1].driver_add("default_value", 2)
    driver.driver.expression = 'pi'
    # Scale
    scale = nodes.get('Scale')
    # X
    path = drivers_utils.element_prop_path(element, flare, 'scale_x')
    drivers_utils.add_driver(scale.inputs[0], v, 'scale_x', 'SCENE', scn, path,'scale_x', 0)
    # Y
    path = drivers_utils.element_prop_path(element, flare, 'scale_y')
    drivers_utils.add_driver(scale.inputs[0], v, 'scale_y', 'SCENE', scn, path,'scale_y', 1)
    # Color
    col = nodes.get('Color')
    path = drivers_utils.element_prop_path(element, flare, 'color')
    drivers_utils.add_driver(col.inputs[6], v, 'color', 'SCENE', scn, path,'color', -1, 4)
    # Use Global Color
    path = drivers_utils.element_prop_path(element, flare, 'use_global_color')
    drivers_utils.add_driver(col.inputs[0], v, 'use_g_color', 'SCENE', scn, path,'use_g_color')
    # Intensity
    proximity = nodes.get('Proximity')
    path = drivers_utils.element_prop_path(element, flare, 'intensity')
    drivers_utils.add_driver(proximity.inputs[2], v, 'intensity', 'SCENE', scn, path,'intensity')
    # proximity intensity
    proximity.inputs[3].driver_remove("default_value")
    driver = proximity.inputs[3].driver_add("default_value")
    path = drivers_utils.element_prop_path(element, flare, 'intensity')
    drivers_utils.add_prop_var(driver, 'intensity', 'SCENE', scn, path)
    path = drivers_utils.element_prop_path(element, flare, 'proximity_trigger')
    drivers_utils.add_prop_var(driver, 'enabled', 'SCENE', scn, path)
    path = drivers_utils.element_prop_path(element, flare, 'proximity_intensity')
    drivers_utils.add_prop_var(driver, 'proximity_intensity', 'SCENE', scn, path)
    driver.driver.expression = 'proximity_intensity if enabled else intensity'
    # Color Ramp
    col_ramp = nodes.get('Color Ramp')
    ele = col_ramp.color_ramp.elements[2]
    path = drivers_utils.element_prop_path(element, flare, 'ring_ray_length')
    drivers_utils.add_driver(ele, 'position', 'length', 'SCENE', scn, path,'length')
    ele = col_ramp.color_ramp.elements[1]
    path = drivers_utils.element_prop_path(element, flare, 'ring_ray_length')
    drivers_utils.add_driver(ele, 'position', 'length', 'SCENE', scn, path,'length/2')
    # Color Ramp Interpolation
    col_ramp = nodes.get('Color Ramp2')
    path = drivers_utils.element_prop_path(element, flare, 'spectrum_interpolation')
    drivers_utils.add_driver(col_ramp.color_ramp, 'interpolation', 'interpolation', 'SCENE', scn, path,'interpolation')
    # Map Range Interpolation
    map_range = nodes.get('Map Range3')
    path = drivers_utils.element_prop_path(element, flare, 'interpolation')
    drivers_utils.add_driver(map_range, 'interpolation_type', 'interpolation', 'SCENE', scn, path,'interpolation')
    # Count
    map_range = nodes.get('Map Range4')
    path = drivers_utils.element_prop_path(element, flare, 'ring_ray_count')
    drivers_utils.add_driver(map_range.inputs[4], v, 'count', 'SCENE', scn, path,'count>0')
    map_range = nodes.get('Map Range2')
    drivers_utils.add_driver(map_range.inputs[3], v, 'count', 'SCENE', scn, path,'count<1')
    math = nodes.get('Math2')
    drivers_utils.add_driver(math.inputs[1], v, 'count', 'SCENE', scn, path,'count')
    # Width
    path = drivers_utils.element_prop_path(element, flare, 'ring_ray_width')
    drivers_utils.add_driver(map_range.inputs[1], v, 'width', 'SCENE', scn, path,'(1-width)/2')
    # Noise Scale
    scale = nodes.get('TexScale')
    path = drivers_utils.element_prop_path(element, flare, 'noise_scale')
    drivers_utils.add_driver(scale.inputs[3], v, 'noise_scale', 'SCENE', scn, path,'noise_scale')
    # Roughness
    roughness = nodes.get('TexMix')
    path = drivers_utils.element_prop_path(element, flare, 'distortion')
    drivers_utils.add_driver(roughness.inputs[0], v, 'distortion', 'SCENE', scn, path,'distortion/10')
    # Ray Length
    math = nodes.get('Math10')
    math.inputs[1].driver_remove("default_value")
    driver = math.inputs[1].driver_add("default_value")
    path = drivers_utils.element_prop_path(element, flare, 'ring_ray_length')
    drivers_utils.add_prop_var(driver, 'length', 'SCENE', scn, path)
    path = drivers_utils.element_prop_path(element, flare, 'spectrum_offset')
    drivers_utils.add_prop_var(driver, 'spectrum_offset', 'SCENE', scn, path)
    driver.driver.expression = '1/length*spectrum_offset'
    # Random Length
    math = nodes.get('Math7')
    path = drivers_utils.element_prop_path(element, flare, 'ring_random_length')
    drivers_utils.add_driver(math.inputs[1], v, 'ran_length', 'SCENE', scn, path,'-ran_length')
    # Length Seed
    noise = nodes.get('Noise2')
    path = drivers_utils.element_prop_path(element, flare, 'ring_length_seed')
    drivers_utils.add_driver(noise.inputs[1], v, 'seed', 'SCENE', scn, path,'seed')
    # Random Width
    mix = nodes.get('Mix2')
    path = drivers_utils.element_prop_path(element, flare, 'ring_random_width')
    drivers_utils.add_driver(mix.inputs[0], v, 'ran_width', 'SCENE', scn, path,'ran_width')
    # Width Seed
    noise = nodes.get('Noise')
    path = drivers_utils.element_prop_path(element, flare, 'ring_width_seed')
    drivers_utils.add_driver(noise.inputs[1], v, 'seed', 'SCENE', scn, path,'seed')
    # Circular Completion
    map_range = nodes.get('Map Range5')
    path = drivers_utils.element_prop_path(element, flare, 'circular_completion')
    drivers_utils.add_driver(map_range.inputs[1], v, 'completion', 'SCENE', scn, path,'lerp(-0.5, 0.49, completion)')
    # Circular Completion Feather
    map_range = nodes.get('Map Range6')
    path = drivers_utils.element_prop_path(element, flare, 'completion_feather')
    drivers_utils.add_driver(map_range.inputs[1], v, 'feather', 'SCENE', scn, path,'lerp(0.499, 0.0, feather)')
    # Use Spectrum
    mix = nodes.get('Mix3')
    path = drivers_utils.element_prop_path(element, flare, 'use_spectrum')
    drivers_utils.add_driver(mix.inputs[0], v, 'use_spectrum', 'SCENE', scn, path,'use_spectrum')
    # Default Values
    element.completion_feather = 1.0
    
def setup_shimmer(context, flare, element, element_node):
    scn = context.scene
    nodes = element_node.node_tree.nodes
    # Drivers
    v = 'default_value'
    
    # Location
    loc = nodes.get('Loc')
    # X Multiplier
    loc.inputs[1].driver_remove("default_value", 0)
    driver = loc.inputs[1].driver_add("default_value", 0)
    path = drivers_utils.element_prop_path(element, flare, 'position')
    drivers_utils.add_prop_var(driver, 'pos', 'SCENE', scn, path)
    path = drivers_utils.element_prop_path(element, flare, 'lock_x')
    drivers_utils.add_prop_var(driver, 'lock_x', 'SCENE', scn, path)
    driver.driver.expression = '-pos*(1-lock_x)'
    # Y Multiplier
    loc.inputs[1].driver_remove("default_value", 1)
    driver = loc.inputs[1].driver_add("default_value", 1)
    path = drivers_utils.element_prop_path(element, flare, 'position')
    drivers_utils.add_prop_var(driver, 'pos', 'SCENE', scn, path)
    path = drivers_utils.element_prop_path(element, flare, 'lock_y')
    drivers_utils.add_prop_var(driver, 'lock_y', 'SCENE', scn, path)
    driver.driver.expression = '-pos*(1-lock_y)'
    # X Addend
    path = drivers_utils.element_prop_path(element, flare, 'location_x')
    drivers_utils.add_driver(loc.inputs[2], v, 'location_x', 'SCENE', scn, path,'location_x', 0)
    # Y Addend
    path = drivers_utils.element_prop_path(element, flare, 'location_y')
    drivers_utils.add_driver(loc.inputs[2], v, 'location_y', 'SCENE', scn, path,'location_y', 1)
    # Rotation
    rot = nodes.get('Rot')
    # Z Multiplier
    path = drivers_utils.element_prop_path(element, flare, 'track_target')
    drivers_utils.add_driver(rot.inputs[1], v, 'track_target', 'SCENE', scn, path,'track_target', 2)
    # Z Addend
    path = drivers_utils.element_prop_path(element, flare, 'rotation')
    drivers_utils.add_driver(rot.inputs[2], v, 'rotation', 'SCENE', scn, path,'rotation', 2)
    rot = nodes.get('Rot2')
    path = drivers_utils.element_prop_path(element, flare, 'shimmer_complexity')
    drivers_utils.add_driver(rot.inputs[1], v, 'count', 'SCENE', scn, path,'pi/count', 2)
    # Count
    math = nodes.get('Math2')
    drivers_utils.add_driver(math.inputs[1], v, 'count', 'SCENE', scn, path,'count')
    math = nodes.get('Math14')
    drivers_utils.add_driver(math.inputs[1], v, 'count', 'SCENE', scn, path,'count')
    # Scale
    scale = nodes.get('Scale')
    # X
    path = drivers_utils.element_prop_path(element, flare, 'scale_x')
    drivers_utils.add_driver(scale.inputs[0], v, 'scale_x', 'SCENE', scn, path,'scale_x', 0)
    # Y
    path = drivers_utils.element_prop_path(element, flare, 'scale_y')
    drivers_utils.add_driver(scale.inputs[0], v, 'scale_y', 'SCENE', scn, path,'scale_y', 1)
    # Color
    col = nodes.get('Color')
    path = drivers_utils.element_prop_path(element, flare, 'color')
    drivers_utils.add_driver(col.inputs[6], v, 'color', 'SCENE', scn, path,'color', -1, 4)
    # Use Global Color
    path = drivers_utils.element_prop_path(element, flare, 'use_global_color')
    drivers_utils.add_driver(col.inputs[0], v, 'use_g_color', 'SCENE', scn, path,'use_g_color')
    # Intensity
    proximity = nodes.get('Proximity')
    path = drivers_utils.element_prop_path(element, flare, 'intensity')
    drivers_utils.add_driver(proximity.inputs[2], v, 'intensity', 'SCENE', scn, path,'intensity')
    # proximity intensity
    proximity.inputs[3].driver_remove("default_value")
    driver = proximity.inputs[3].driver_add("default_value")
    path = drivers_utils.element_prop_path(element, flare, 'intensity')
    drivers_utils.add_prop_var(driver, 'intensity', 'SCENE', scn, path)
    path = drivers_utils.element_prop_path(element, flare, 'proximity_trigger')
    drivers_utils.add_prop_var(driver, 'enabled', 'SCENE', scn, path)
    path = drivers_utils.element_prop_path(element, flare, 'proximity_intensity')
    drivers_utils.add_prop_var(driver, 'proximity_intensity', 'SCENE', scn, path)
    driver.driver.expression = 'proximity_intensity if enabled else intensity'
    # Interpolation
    map_range = nodes.get('Map Range2')
    path = drivers_utils.element_prop_path(element, flare, 'interpolation2')
    drivers_utils.add_driver(map_range, 'interpolation_type', 'interpolation', 'SCENE', scn, path,'interpolation')
    map_range = nodes.get('Map Range5')
    path = drivers_utils.element_prop_path(element, flare, 'interpolation2')
    drivers_utils.add_driver(map_range, 'interpolation_type', 'interpolation', 'SCENE', scn, path,'interpolation')
    map_range = nodes.get('Map Range3')
    path = drivers_utils.element_prop_path(element, flare, 'interpolation')
    drivers_utils.add_driver(map_range, 'interpolation_type', 'interpolation', 'SCENE', scn, path,'interpolation')
    # Circular Completion
    map_range = nodes.get('Map Range6')
    path = drivers_utils.element_prop_path(element, flare, 'circular_completion')
    drivers_utils.add_driver(map_range.inputs[1], v, 'completion', 'SCENE', scn, path,'lerp(-0.1, 0.49, completion)')
    # Circular Completion Feather
    map_range = nodes.get('Map Range7')
    path = drivers_utils.element_prop_path(element, flare, 'completion_feather')
    drivers_utils.add_driver(map_range.inputs[2], v, 'feather', 'SCENE', scn, path,'lerp(0.01, 1.0, feather)')
    # Random Seed
    noise = nodes.get('Noise')
    path = drivers_utils.element_prop_path(element, flare, 'shimmer_length_seed')
    drivers_utils.add_driver(noise.inputs[1], v, 'se', 'SCENE', scn, path,'se')
    noise = nodes.get('Noise2')
    drivers_utils.add_driver(noise.inputs[1], v, 'se', 'SCENE', scn, path,'se+1')
    # Animation Speed
    math = nodes.get('Math6')
    path = drivers_utils.element_prop_path(element, flare, 'shimmer_speed')
    drivers_utils.add_driver(math.inputs[2], v, 'speed', 'SCENE', scn, path,'frame/speed if speed else 0')
    math = nodes.get('Math18')
    drivers_utils.add_driver(math.inputs[2], v, 'speed', 'SCENE', scn, path,'frame/speed*0.5 if speed else 0')
    # Random Length
    mix = nodes.get('Mix')
    path = drivers_utils.element_prop_path(element, flare, 'shimmer_length')
    drivers_utils.add_driver(mix.inputs[0], v, 'length', 'SCENE', scn, path,'length')
    mix = nodes.get('Mix2')
    drivers_utils.add_driver(mix.inputs[0], v, 'length', 'SCENE', scn, path,'length')
    # Width
    math = nodes.get('Math4')
    path = drivers_utils.element_prop_path(element, flare, 'shimmer_width')
    drivers_utils.add_driver(math.inputs[1], v, 'width', 'SCENE', scn, path,'width')
    math = nodes.get('Math16')
    drivers_utils.add_driver(math.inputs[1], v, 'width', 'SCENE', scn, path,'width')
    # Default Values
    element.interpolation2 = '2'
    
def setup_lens_dirt(context, flare, element, element_node):
    scn = context.scene
    nodes = element_node.node_tree.nodes
    # Drivers
    v = 'default_value'
    
    # Location
    loc = nodes.get('Loc')
    # X Multiplier
    loc.inputs[1].driver_remove("default_value", 0)
    driver = loc.inputs[1].driver_add("default_value", 0)
    path = drivers_utils.element_prop_path(element, flare, 'position')
    drivers_utils.add_prop_var(driver, 'pos', 'SCENE', scn, path)
    path = drivers_utils.element_prop_path(element, flare, 'lock_x')
    drivers_utils.add_prop_var(driver, 'lock_x', 'SCENE', scn, path)
    driver.driver.expression = '-pos*(1-lock_x)'
    # Y Multiplier
    loc.inputs[1].driver_remove("default_value", 1)
    driver = loc.inputs[1].driver_add("default_value", 1)
    path = drivers_utils.element_prop_path(element, flare, 'position')
    drivers_utils.add_prop_var(driver, 'pos', 'SCENE', scn, path)
    path = drivers_utils.element_prop_path(element, flare, 'lock_y')
    drivers_utils.add_prop_var(driver, 'lock_y', 'SCENE', scn, path)
    driver.driver.expression = '-pos*(1-lock_y)'
    # X Addend
    path = drivers_utils.element_prop_path(element, flare, 'location_x')
    drivers_utils.add_driver(loc.inputs[2], v, 'location_x', 'SCENE', scn, path,'location_x', 0)
    # Y Addend
    path = drivers_utils.element_prop_path(element, flare, 'location_y')
    drivers_utils.add_driver(loc.inputs[2], v, 'location_y', 'SCENE', scn, path,'location_y', 1)
    # Texture Scale
    scale = nodes.get('Mapping2')
    # X
    path = drivers_utils.element_prop_path(element, flare, 'scale_x')
    drivers_utils.add_driver(scale.inputs[3], v, 'scale_x', 'SCENE', scn, path,'scale_x', 0)
    # Y
    path = drivers_utils.element_prop_path(element, flare, 'scale_y')
    drivers_utils.add_driver(scale.inputs[3], v, 'scale_y', 'SCENE', scn, path,'scale_y', 1)
    # Color
    col = nodes.get('Color')
    path = drivers_utils.element_prop_path(element, flare, 'color')
    drivers_utils.add_driver(col.inputs[6], v, 'color', 'SCENE', scn, path,'color', -1, 4)
    # Use Global Color
    path = drivers_utils.element_prop_path(element, flare, 'use_global_color')
    drivers_utils.add_driver(col.inputs[0], v, 'use_g_color', 'SCENE', scn, path,'use_g_color')
    # Intensity
    proximity = nodes.get('Proximity')
    path = drivers_utils.element_prop_path(element, flare, 'intensity')
    drivers_utils.add_driver(proximity.inputs[2], v, 'intensity', 'SCENE', scn, path,'intensity')
    # proximity intensity
    proximity.inputs[3].driver_remove("default_value")
    driver = proximity.inputs[3].driver_add("default_value")
    path = drivers_utils.element_prop_path(element, flare, 'intensity')
    drivers_utils.add_prop_var(driver, 'intensity', 'SCENE', scn, path)
    path = drivers_utils.element_prop_path(element, flare, 'proximity_trigger')
    drivers_utils.add_prop_var(driver, 'enabled', 'SCENE', scn, path)
    path = drivers_utils.element_prop_path(element, flare, 'proximity_intensity')
    drivers_utils.add_prop_var(driver, 'proximity_intensity', 'SCENE', scn, path)
    driver.driver.expression = 'proximity_intensity if enabled else intensity'
    # Mask Size
    scale = nodes.get('Scale')
    path = drivers_utils.element_prop_path(element, flare, 'mask_size')
    drivers_utils.add_driver(scale.inputs[3], v, 'size', 'SCENE', scn, path,'size')
    # Mask Feather
    math = nodes.get('Math')
    path = drivers_utils.element_prop_path(element, flare, 'mask_feather')
    drivers_utils.add_driver(math.inputs[1], v, 'feather', 'SCENE', scn, path,'feather')
    
def setup_iris(context, flare, element, element_node):
    scn = context.scene
    nodes = element_node.node_tree.nodes
    # Drivers
    v = 'default_value'
    
    # Location
    loc = nodes.get('Loc')
    # X Multiplier
    loc.inputs[1].driver_remove("default_value", 0)
    driver = loc.inputs[1].driver_add("default_value", 0)
    path = drivers_utils.element_prop_path(element, flare, 'position')
    drivers_utils.add_prop_var(driver, 'pos', 'SCENE', scn, path)
    path = drivers_utils.element_prop_path(element, flare, 'lock_x')
    drivers_utils.add_prop_var(driver, 'lock_x', 'SCENE', scn, path)
    driver.driver.expression = '-pos*(1-lock_x)'
    # Y Multiplier
    loc.inputs[1].driver_remove("default_value", 1)
    driver = loc.inputs[1].driver_add("default_value", 1)
    path = drivers_utils.element_prop_path(element, flare, 'position')
    drivers_utils.add_prop_var(driver, 'pos', 'SCENE', scn, path)
    path = drivers_utils.element_prop_path(element, flare, 'lock_y')
    drivers_utils.add_prop_var(driver, 'lock_y', 'SCENE', scn, path)
    driver.driver.expression = '-pos*(1-lock_y)'
    # X Addend
    path = drivers_utils.element_prop_path(element, flare, 'location_x')
    drivers_utils.add_driver(loc.inputs[2], v, 'location_x', 'SCENE', scn, path,'location_x', 0)
    # Y Addend
    path = drivers_utils.element_prop_path(element, flare, 'location_y')
    drivers_utils.add_driver(loc.inputs[2], v, 'location_y', 'SCENE', scn, path,'location_y', 1)
    # Rotation
    rot = nodes.get('Rot')
    # Z Multiplier
    path = drivers_utils.element_prop_path(element, flare, 'track_target')
    drivers_utils.add_driver(rot.inputs[1], v, 'track_target', 'SCENE', scn, path,'track_target', 2)
    # Z Addend
    path = drivers_utils.element_prop_path(element, flare, 'rotation')
    drivers_utils.add_driver(rot.inputs[2], v, 'rotation', 'SCENE', scn, path,'rotation', 2)
    # Scale
    scale = nodes.get('Scale')
    # X
    path = drivers_utils.element_prop_path(element, flare, 'scale_x')
    drivers_utils.add_driver(scale.inputs[0], v, 'scale_x', 'SCENE', scn, path,'scale_x', 0)
    # Y
    path = drivers_utils.element_prop_path(element, flare, 'scale_y')
    drivers_utils.add_driver(scale.inputs[0], v, 'scale_y', 'SCENE', scn, path,'scale_y', 1)
    # Color
    col = nodes.get('Color')
    path = drivers_utils.element_prop_path(element, flare, 'color')
    drivers_utils.add_driver(col.inputs[6], v, 'color', 'SCENE', scn, path,'color', -1, 4)
    # Use Global Color
    path = drivers_utils.element_prop_path(element, flare, 'use_global_color')
    drivers_utils.add_driver(col.inputs[0], v, 'use_g_color', 'SCENE', scn, path,'use_g_color')
    # Intensity
    proximity = nodes.get('Proximity')
    path = drivers_utils.element_prop_path(element, flare, 'intensity')
    drivers_utils.add_driver(proximity.inputs[2], v, 'intensity', 'SCENE', scn, path,'intensity')
    # proximity intensity
    proximity.inputs[3].driver_remove("default_value")
    driver = proximity.inputs[3].driver_add("default_value")
    path = drivers_utils.element_prop_path(element, flare, 'intensity')
    drivers_utils.add_prop_var(driver, 'intensity', 'SCENE', scn, path)
    path = drivers_utils.element_prop_path(element, flare, 'proximity_trigger')
    drivers_utils.add_prop_var(driver, 'enabled', 'SCENE', scn, path)
    path = drivers_utils.element_prop_path(element, flare, 'proximity_intensity')
    drivers_utils.add_prop_var(driver, 'proximity_intensity', 'SCENE', scn, path)
    driver.driver.expression = 'proximity_intensity if enabled else intensity'
    # Count
    math = nodes.get('Math12')
    path = drivers_utils.element_prop_path(element, flare, 'iris_count')
    drivers_utils.add_driver(math.inputs[1], v, 'count', 'SCENE', scn, path,'count')
    # Blades
    math = nodes.get('Math4')
    path = drivers_utils.element_prop_path(element, flare, 'iris_blades')
    drivers_utils.add_driver(math.inputs[1], v, 'blades', 'SCENE', scn, path,'0.5+blades')
    # Roundness
    math = nodes.get('Math22')
    path = drivers_utils.element_prop_path(element, flare, 'iris_roundness')
    drivers_utils.add_driver(math.inputs[1], v, 'roundness', 'SCENE', scn, path,'roundness')
    # outline thikness
    math = nodes.get('Math13')
    path = drivers_utils.element_prop_path(element, flare, 'iris_outline_thikness')
    drivers_utils.add_driver(math.inputs[1], v, 'thikness', 'SCENE', scn, path,'thikness')
    # Feather
    map_range = nodes.get('Map Range')
    path = drivers_utils.element_prop_path(element, flare, 'iris_feather')
    drivers_utils.add_driver(map_range.inputs[1], v, 'feather', 'SCENE', scn, path,'1-feather')
    # outline
    mix = nodes.get('Outline')
    path = drivers_utils.element_prop_path(element, flare, 'iris_outline_opacity')
    drivers_utils.add_driver(mix.inputs[0], v, 'opacity', 'SCENE', scn, path,'opacity')
    # Rings Opacity
    mix = nodes.get('Ribbons')
    path = drivers_utils.element_prop_path(element, flare, 'iris_rings_opacity')
    drivers_utils.add_driver(mix.inputs[0], v, 'opacity', 'SCENE', scn, path,'opacity')
    # Rings Count
    math = nodes.get('Math16')
    path = drivers_utils.element_prop_path(element, flare, 'iris_rings_count')
    drivers_utils.add_driver(math.inputs[1], v, 'count', 'SCENE', scn, path,'count')
    # Circular Completion
    map_range = nodes.get('Map Range3')
    path = drivers_utils.element_prop_path(element, flare, 'circular_completion')
    drivers_utils.add_driver(map_range.inputs[1], v, 'completion', 'SCENE', scn, path,'lerp(-pi, pi, completion)')
    # Completion Feather
    map_range = nodes.get('Map Range4')
    path = drivers_utils.element_prop_path(element, flare, 'completion_feather')
    drivers_utils.add_driver(map_range.inputs[1], v, 'feather', 'SCENE', scn, path,'lerp(0.4999, 0.0, feather)')
    # Map Range Interpolation
    map_range = nodes.get('Map Range2')
    path = drivers_utils.element_prop_path(element, flare, 'interpolation')
    drivers_utils.add_driver(map_range, 'interpolation_type', 'interpolation', 'SCENE', scn, path,'interpolation')
    # Default Values
    element.scale_x, element.scale_y = (0.1, 0.1)
    
def setup_caustic(context, flare, element, element_node):
    scn = context.scene
    nodes = element_node.node_tree.nodes
    # Drivers
    v = 'default_value'
    
    # Location
    loc = nodes.get('Loc')
    # X Multiplier
    loc.inputs[1].driver_remove("default_value", 0)
    driver = loc.inputs[1].driver_add("default_value", 0)
    driver.driver.expression = '-2.0'
    # Y Multiplier
    loc.inputs[1].driver_remove("default_value", 1)
    driver = loc.inputs[1].driver_add("default_value", 1)
    driver.driver.expression = '-2.0'
    # Scale
    scale = nodes.get('Scale')
    # X
    path = drivers_utils.element_prop_path(element, flare, 'scale_x')
    drivers_utils.add_driver(scale.inputs[0], v, 'scale_x', 'SCENE', scn, path,'scale_x', 0)
    # Y
    path = drivers_utils.element_prop_path(element, flare, 'scale_y')
    drivers_utils.add_driver(scale.inputs[0], v, 'scale_y', 'SCENE', scn, path,'scale_y', 1)
    # Falloff
    falloff = nodes.get('Falloff')
    path = drivers_utils.element_prop_path(element, flare, 'light_falloff')
    drivers_utils.add_driver(falloff.inputs[1], v, 'falloff', 'SCENE', scn, path,'falloff')
    # Color
    col = nodes.get('Color')
    path = drivers_utils.element_prop_path(element, flare, 'color')
    drivers_utils.add_driver(col.inputs[6], v, 'color', 'SCENE', scn, path,'color', -1, 4)
    # Use Global Color
    path = drivers_utils.element_prop_path(element, flare, 'use_global_color')
    drivers_utils.add_driver(col.inputs[0], v, 'use_g_color', 'SCENE', scn, path,'use_g_color')
    # Intensity
    proximity = nodes.get('Proximity')
    path = drivers_utils.element_prop_path(element, flare, 'intensity')
    drivers_utils.add_driver(proximity.inputs[2], v, 'intensity', 'SCENE', scn, path,'intensity')
    # proximity intensity
    proximity.inputs[3].driver_remove("default_value")
    driver = proximity.inputs[3].driver_add("default_value")
    path = drivers_utils.element_prop_path(element, flare, 'intensity')
    drivers_utils.add_prop_var(driver, 'intensity', 'SCENE', scn, path)
    path = drivers_utils.element_prop_path(element, flare, 'proximity_trigger')
    drivers_utils.add_prop_var(driver, 'enabled', 'SCENE', scn, path)
    path = drivers_utils.element_prop_path(element, flare, 'proximity_intensity')
    drivers_utils.add_prop_var(driver, 'proximity_intensity', 'SCENE', scn, path)
    driver.driver.expression = 'proximity_intensity if enabled else intensity'
    # Shape
    math = nodes.get('Math17')
    path = drivers_utils.element_prop_path(element, flare, 'caustic_shape')
    drivers_utils.add_driver(math.inputs[1], v, 'shape', 'SCENE', scn, path,'(shape*100)+2')
    # Thikness
    math = nodes.get('Math7')
    path = drivers_utils.element_prop_path(element, flare, 'caustic_thikness')
    drivers_utils.add_driver(math.inputs[0], v, 'thikness', 'SCENE', scn, path,'-thikness')
    math = nodes.get('Math12')
    drivers_utils.add_driver(math.inputs[0], v, 'thikness', 'SCENE', scn, path,'thikness')
    # Use Spectrum
    mix = nodes.get('Mix')
    path = drivers_utils.element_prop_path(element, flare, 'use_spectrum')
    drivers_utils.add_driver(mix.inputs[0], v, 'use_spectrum', 'SCENE', scn, path,'use_spectrum')
    # Default Values
    element.scale_x, element.scale_y = (0.05, 0.05)
    element.use_spectrum = 0.0
    
def setup_single_ghost(context, flare, element, node, index):
    scn = context.scene
    nodes = node.node_tree.nodes
    # Drivers
    idx = node.inputs
    v = 'default_value'
    # Location
    # X Multiplier
    idx[4].driver_remove("default_value", 0)
    driver = idx[4].driver_add("default_value", 0)
    path = drivers_utils.element_prop_path(element, flare, 'position')
    drivers_utils.add_prop_var(driver, 'pos', 'SCENE', scn, path)
    path = drivers_utils.element_prop_path(element, flare, 'lock_x')
    drivers_utils.add_prop_var(driver, 'lock_x', 'SCENE', scn, path)
    path = drivers_utils.element_prop_path(element, flare, 'ghosts_distance')
    drivers_utils.add_prop_var(driver, 'dis', 'SCENE', scn, path)
    path = drivers_utils.element_prop_path(element, flare, 'ghosts_random_distance')
    drivers_utils.add_prop_var(driver, 'random_dis', 'SCENE', scn, path)
    path = drivers_utils.element_prop_path(element, flare, 'ghosts_random_loc_seed')
    drivers_utils.add_prop_var(driver, 'se', 'SCENE', scn, path)
    e = ''.join(['((random_dis*noise.cell((se+', str(index),',0,0)))+((-dis*', str(index), ')-pos))*(1-lock_x)'])
    driver.driver.expression = e
    # Y Multiplier
    idx[4].driver_remove("default_value", 1)
    driver = idx[4].driver_add("default_value", 1)
    path = drivers_utils.element_prop_path(element, flare, 'position')
    drivers_utils.add_prop_var(driver, 'pos', 'SCENE', scn, path)
    path = drivers_utils.element_prop_path(element, flare, 'lock_y')
    drivers_utils.add_prop_var(driver, 'lock_y', 'SCENE', scn, path)
    path = drivers_utils.element_prop_path(element, flare, 'ghosts_distance')
    drivers_utils.add_prop_var(driver, 'dis', 'SCENE', scn, path)
    path = drivers_utils.element_prop_path(element, flare, 'ghosts_random_distance')
    drivers_utils.add_prop_var(driver, 'random_dis', 'SCENE', scn, path)
    path = drivers_utils.element_prop_path(element, flare, 'ghosts_random_loc_seed')
    drivers_utils.add_prop_var(driver, 'se', 'SCENE', scn, path)
    e = ''.join(['((random_dis*noise.cell((se+', str(index),',0,0)))+((-dis*', str(index), ')-pos))*(1-lock_y)'])
    driver.driver.expression = e
    # X Addend
    idx[5].driver_remove("default_value", 0)
    driver = idx[5].driver_add("default_value", 0)
    path = drivers_utils.element_prop_path(element, flare, 'location_x')
    drivers_utils.add_prop_var(driver, 'x', 'SCENE', scn, path)
    path = drivers_utils.element_prop_path(element, flare, 'ghosts_random_x')
    drivers_utils.add_prop_var(driver, 'random_x', 'SCENE', scn, path)
    path = drivers_utils.element_prop_path(element, flare, 'ghosts_random_loc_seed')
    drivers_utils.add_prop_var(driver, 'se', 'SCENE', scn, path)
    e = ''.join(['(random_x*noise.cell((se+1+',str(index),',0,0))) + x'])
    driver.driver.expression = e
    # Y Addend
    idx[5].driver_remove("default_value", 1)
    driver = idx[5].driver_add("default_value", 1)
    path = drivers_utils.element_prop_path(element, flare, 'location_y')
    drivers_utils.add_prop_var(driver, 'y', 'SCENE', scn, path)
    path = drivers_utils.element_prop_path(element, flare, 'ghosts_random_y')
    drivers_utils.add_prop_var(driver, 'random_y', 'SCENE', scn, path)
    path = drivers_utils.element_prop_path(element, flare, 'ghosts_random_loc_seed')
    drivers_utils.add_prop_var(driver, 'se', 'SCENE', scn, path)
    e = ''.join(['(random_y*noise.cell((se+1+',str(index),',0,0))) + y'])
    driver.driver.expression = e
    # Rotation
    # Z Multiplier
    path = drivers_utils.element_prop_path(element, flare, 'track_target')
    drivers_utils.add_driver(idx[6], v, 'track_target', 'SCENE', scn, path,'track_target', 2)
    # Z Addend
    idx[7].driver_remove("default_value", 2)
    driver = idx[7].driver_add("default_value", 2)
    path = drivers_utils.element_prop_path(element, flare, 'rotation')
    drivers_utils.add_prop_var(driver, 'rot', 'SCENE', scn, path)
    path = drivers_utils.element_prop_path(element, flare, 'random_rot')
    drivers_utils.add_prop_var(driver, 'random_rot', 'SCENE', scn, path)
    path = drivers_utils.element_prop_path(element, flare, 'random_rot_seed')
    drivers_utils.add_prop_var(driver, 'se', 'SCENE', scn, path)
    e = ''.join(['(random_rot*pi*noise.cell((se+',str(index),',0,0))) + rot'])
    driver.driver.expression = e
    # Scale
    # X
    idx[8].driver_remove("default_value", 0)
    driver = idx[8].driver_add("default_value", 0)
    path = drivers_utils.element_prop_path(element, flare, 'scale_x')
    drivers_utils.add_prop_var(driver, 'scale_x', 'SCENE', scn, path)
    path = drivers_utils.element_prop_path(element, flare, 'random_scale')
    drivers_utils.add_prop_var(driver, 'random_scale', 'SCENE', scn, path)
    path = drivers_utils.element_prop_path(element, flare, 'random_scale_seed')
    drivers_utils.add_prop_var(driver, 'se', 'SCENE', scn, path)
    e = ''.join(['lerp(1, abs(noise.cell((se+',str(index),',0,0))), random_scale) * scale_x'])
    driver.driver.expression = e
    # Y
    idx[8].driver_remove("default_value", 1)
    driver = idx[8].driver_add("default_value", 1)
    path = drivers_utils.element_prop_path(element, flare, 'scale_y')
    drivers_utils.add_prop_var(driver, 'scale_y', 'SCENE', scn, path)
    path = drivers_utils.element_prop_path(element, flare, 'random_scale')
    drivers_utils.add_prop_var(driver, 'random_scale', 'SCENE', scn, path)
    path = drivers_utils.element_prop_path(element, flare, 'random_scale_seed')
    drivers_utils.add_prop_var(driver, 'se', 'SCENE', scn, path)
    e = ''.join(['lerp(1, abs(noise.cell((se+',str(index),',0,0))), random_scale) * scale_y'])
    driver.driver.expression = e
    # Color Seed
    path = drivers_utils.element_prop_path(element, flare, 'ghosts_random_col_seed')
    drivers_utils.add_driver(idx[9], v, 'se', 'SCENE', scn, path,'se+'+str(index))
    # Use Global Color
    color = nodes.get('Color')
    path = drivers_utils.element_prop_path(element, flare, 'use_global_color')
    drivers_utils.add_driver(color.inputs[0], v, 'use_g_color', 'SCENE', scn, path,'1-use_g_color')
    
def setup_single_streak(context, flare, element, node, index):
    scn = context.scene
    nodes = node.node_tree.nodes
    # Drivers
    idx = node.inputs
    v = 'default_value'
    # Rotation
    # Z Multiplier
    path = drivers_utils.element_prop_path(element, flare, 'track_target')
    drivers_utils.add_driver(idx[4], v, 'track_target', 'SCENE', scn, path,'track_target', 2)
    # Z Addend
    idx[5].driver_remove("default_value", 2)
    driver = idx[5].driver_add("default_value", 2)
    path = drivers_utils.element_prop_path(element, flare, 'rotation')
    drivers_utils.add_prop_var(driver, 'rot', 'SCENE', scn, path)
    path = drivers_utils.element_prop_path(element, flare, 'streaks_count')
    drivers_utils.add_prop_var(driver, 'count', 'SCENE', scn, path)
    path = drivers_utils.element_prop_path(element, flare, 'random_rot')
    drivers_utils.add_prop_var(driver, 'random_rot', 'SCENE', scn, path)
    path = drivers_utils.element_prop_path(element, flare, 'random_rot_seed')
    drivers_utils.add_prop_var(driver, 'se', 'SCENE', scn, path)
    e = ''.join(['(pi/count*',str(index),') + (random_rot*pi*noise.cell((se+(',str(index),'*10),0,0))) + rot'])
    driver.driver.expression = e
    # Scale Multiplier
    idx[6].driver_remove("default_value")
    driver = idx[6].driver_add("default_value")
    path = drivers_utils.element_prop_path(element, flare, 'random_scale')
    drivers_utils.add_prop_var(driver, 'random_scale', 'SCENE', scn, path)
    path = drivers_utils.element_prop_path(element, flare, 'random_scale_seed')
    drivers_utils.add_prop_var(driver, 'se', 'SCENE', scn, path)
    e = ''.join(['lerp(1, abs(noise.cell((se+(',str(index),'*20),0,0))), random_scale)'])
    driver.driver.expression = e

# Update Ghosts
def update_ghosts(context, flare, element, ghosts_node, count, ng_path):
    node_groups = bpy.data.node_groups
    nodes = ghosts_node.node_tree.nodes
    links = ghosts_node.node_tree.links
    # Vector Math Node
    vec_math = nodes.get('Vector Math')
    # Group Input Node
    input = nodes.get('Group Input')
    
    # Combine Node
    combine_node = nodes.get('Combine Ghosts')
    if combine_node is None:
        comb_ng = combine_ng()
        combine_node = nodes.new(type="ShaderNodeGroup")
        combine_node.node_tree = comb_ng
        comb_ng.interface.new_socket(socket_type='NodeSocketColor', name='Color', in_out='OUTPUT')
        combine_node.name = 'Combine Ghosts'
        combine_node.label = 'Combine Ghosts'
    prepare_combine_node(combine_node, count, 'Ghost')
    combine_node.location = (600.0, 0.0)
    links.new(combine_node.outputs[0], vec_math.inputs[0])
    # Node group
    single_ghost = nodes.get('Single Ghost 0')
    if single_ghost is None:
        ng = node_groups.get('LF_SIngle_Ghost')
        if ng is None:
            single_ng = load_ng(ng_path, 'LF_SIngle_Ghost')
        else:
            single_ng = ng.copy()
        color_ramp = single_ng.nodes.get('ColorRamp')
        if color_ramp is not None:
            reset_color_ramp(color_ramp, True)
    else:
        single_ng = single_ghost.node_tree
    # create nodes    
    for i in range(count):
        n = nodes.get('Single Ghost '+str(i))
        if n is None:
            n = nodes.new(type="ShaderNodeGroup")
            n.name = 'Single Ghost '+str(i)
            n.label = 'Single Ghost '+str(i)
            n.node_tree = single_ng
            setup_single_ghost(context, flare, element, n, i)
        for j in range(4):
            links.new(input.outputs[j], n.inputs[j])
        n.hide = True
        n.location = (300.0, i*-150.0)
        links.new(n.outputs[0], combine_node.inputs[i])
    # Delete unnecessary nodes
    single_nodes = [i for i in nodes if 'Single Ghost ' in i.name]
    expected_nodes = ['Single Ghost '+str(i) for i in range(count)]
    for n in single_nodes:
        if n.name in expected_nodes:
            continue
        nodes.remove(n)
        
# Update Streaks
def update_streaks(context, flare, element, streaks_node, count, ng_path):
    node_groups = bpy.data.node_groups
    nodes = streaks_node.node_tree.nodes
    links = streaks_node.node_tree.links
    # Vector Math Node
    math = nodes.get('Falloff')
    # Group Input Node
    input = nodes.get('Group Input')
    loc = nodes.get('Loc')
    scale = nodes.get('Scale')
    # Combine Node
    combine_node = nodes.get('Combine Streaks')
    if combine_node is None:
        comb_ng = combine_ng()
        combine_node = nodes.new(type="ShaderNodeGroup")
        combine_node.node_tree = comb_ng
        comb_ng.interface.new_socket(socket_type='NodeSocketColor', name='Color', in_out='OUTPUT')
        combine_node.name = 'Combine Streaks'
        combine_node.label = 'Combine Streaks'
    prepare_combine_node(combine_node, count, 'Streak')
    combine_node.location = (600.0, 0.0)
    links.new(combine_node.outputs[0], math.inputs[0])
    # Node group
    single_streak = nodes.get('Single Streak 0')
    if single_streak is None:
        ng = node_groups.get('LF_Single_Streak')
        if ng is None:
            single_ng = load_ng(ng_path, 'LF_Single_Streak')
        else:
            single_ng = ng.copy()
    else:
        single_ng = single_streak.node_tree
    # create nodes    
    for i in range(count):
        n = nodes.get('Single Streak '+str(i))
        if n is None:
            n = nodes.new(type="ShaderNodeGroup")
            n.name = 'Single Streak '+str(i)
            n.label = 'Single Streak '+str(i)
            n.node_tree = single_ng
            setup_single_streak(context, flare, element, n, i)
        n.hide = True
        n.location = (300.0, i*-150.0)
        links.new(input.outputs[0], n.inputs[0])
        links.new(input.outputs[2], n.inputs[2])
        links.new(loc.outputs[0], n.inputs[1])
        links.new(scale.outputs[0], n.inputs[3])
        links.new(n.outputs[0], combine_node.inputs[i])
    # Delete unnecessary nodes
    single_nodes = [i for i in nodes if 'Single Streak ' in i.name]
    expected_nodes = ['Single Streak '+str(i) for i in range(count)]
    for n in single_nodes:
        if n.name in expected_nodes:
            continue
        nodes.remove(n)
        
# reset color ramp
def reset_color_ramp(node, color = False):
    elements = node.color_ramp.elements
    col = (0.02, 0.98, 0.115, 1.0) if color else (0.0, 0.0, 0.0, 1.0)
    col2 = (0.002, 0.192, 1.0, 1.0) if color else (1.0, 1.0, 1.0, 1.0)
    while len(elements) > 1:
        elements.remove(elements[0])
    elements[0].position = 0.0
    elements[0].color = col
    element = elements.new(1.0)
    element.color = col2
    node.color_ramp.interpolation = 'LINEAR'

# Generate Lens Flare Shader
def generate_lf_shader_node_tree(context, flare, ng_path):
    scn = context.scene
    material = flare.material
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    combine = nodes.get('Combine Elements')
    prepare_combine_node(combine, len(flare.elements), 'Element')
    if not len(flare.elements):
        return
    tex_coord = nodes.get('Texture Coord')
    vec_math = nodes.get('Vector Math')
    pos_attr = nodes.get('Position Attribute')
    angle_attr = nodes.get('Angle Attribute')
    scale_attr = nodes.get('Scale Fac Attribute')
    borders_attr = nodes.get('Borders Attribute')
    color_attr = nodes.get('Color Attribute')
    
    for i, element in enumerate(flare.elements):
        ele_node = get_element_node(context, flare, element, nodes, ng_path)
        ele_node.hide = True
        ele_node.location = (600.0, -i*(150.0))
        links.new(ele_node.outputs[0], combine.inputs[i])
        #links
        links.new(vec_math.outputs[0], ele_node.inputs[0])
        links.new(pos_attr.outputs[1], ele_node.inputs[1])
        links.new(angle_attr.outputs[1], ele_node.inputs[2])
        links.new(scale_attr.outputs[2], ele_node.inputs[3])
        links.new(borders_attr.outputs[2], ele_node.inputs[4])
        links.new(color_attr.outputs[0], ele_node.inputs[5])
    
elements_dict = {
    'GLOW': {
        'NG_NAME': 'LF_Glow_Element',
        'ADD_DRIVERS': setup_glow
    },
    'IMAGE': {
        'NG_NAME': 'LF_Image_Element',
        'ADD_DRIVERS': setup_image
    },
    'GHOSTS': {
        'NG_NAME': 'LF_Ghosts_Element',
        'ADD_DRIVERS': setup_ghosts
    },
    'STREAKS': {
        'NG_NAME': 'LF_Streaks_Element',
        'ADD_DRIVERS': setup_streaks
    },
    'RING': {
        'NG_NAME': 'LF_Ring_Element',
        'ADD_DRIVERS': setup_ring
    },
    'HOOP': {
        'NG_NAME': 'LF_Hoop_Element',
        'ADD_DRIVERS': setup_hoop
    },
    'SHIMMER': {
        'NG_NAME': 'LF_Shimmer_Element',
        'ADD_DRIVERS': setup_shimmer
    },
    'LENS_DIRT': {
        'NG_NAME': 'LF_Lens_Dirt_Element',
        'ADD_DRIVERS': setup_lens_dirt
    },
    'IRIS': {
        'NG_NAME': 'LF_Iris_Element',
        'ADD_DRIVERS': setup_iris
    },
    'CAUSTIC': {
        'NG_NAME': 'LF_Caustic_Element',
        'ADD_DRIVERS': setup_caustic
    },
}