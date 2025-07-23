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
from bpy.props import *
from math import pi
from bpy.types import PropertyGroup
from bpy.app.handlers import persistent

############################## Update Functions ##############################
# Get flare geo Nodes
def get_flare_geo_node(flare, context):
    fw_group = flare.id_data.path_resolve('fw_group')
    if not hasattr(fw_group.node_group, "nodes"):
        return None
    nodes = fw_group.node_group.nodes
    return nodes.get(flare.name)

# Update flare geo node Target
def update_flare_target(self, context):
    node = get_flare_geo_node(self, context)
    if node is not None:
        node.inputs[14].default_value = self.target_object
        node.inputs[15].default_value = self.target_collection
    return None

# Update Obstacles Collection
def update_obstacles_collection(self, context):
    node = get_flare_geo_node(self, context)
    if node is not None:
        node.inputs[18].default_value = self.obstacles_collection
    return None

# Update the Attributes
def update_attr(self, context):
    node = get_flare_geo_node(self, context)
    if node is not None:
        node.inputs[43].default_value = self.color_attr
        node.inputs[44].default_value = self.intensity_attr
        node.inputs[45].default_value = self.scale_attr
    return None

# Update Ghosts
def update_ghosts(self, context):
    context.scene.fw_update_element = ''
    return None

# Update Background Camera
def update_bg_cam(self, context):
    context.scene.fw_update_bg_cam = ''
    return None

# mute element node
def hide_element(self, context):
    coll = self.id_data.path_resolve('fw_group.coll')
    index = self.id_data.path_resolve('fw_group.index')
    flare = coll[index]
    material = flare.material
    if not hasattr(material, 'node_tree'):
        return None
    node_group = material.node_tree
    element_node = node_group.nodes.get(self.name)
    element_node.mute = self.hide
    return None

# Set Image Texture
def set_image(self, context):
    image_node = None
    coll = self.id_data.path_resolve('fw_group.coll')
    index = self.id_data.path_resolve('fw_group.index')
    flare = coll[index]
    material = flare.material
    if not hasattr(material, 'node_tree'):
        return None
    node_group = material.node_tree
    element_node = node_group.nodes.get(self.name)
    nodes = element_node.node_tree.nodes
    if self.type in ['IMAGE', 'LENS_DIRT']:
        image_node = nodes.get('Image Texture')
    elif self.type == 'GHOSTS':
        single_ghost = nodes.get('Single Ghost 0')
        if single_ghost is not None:
            ghost_nodes = single_ghost.node_tree.nodes
            image_node = ghost_nodes.get('Image Texture')
    if not image_node:
        return None
    image_node.image = self.image
    # Adjust the scale of the lens dirt texture
    if self.type == 'LENS_DIRT':
        res_x = context.scene.render.resolution_x
        res_y = context.scene.render.resolution_y
        scale_x = min(res_x/res_y, 1.0) + 0.01
        scale_y = min(res_y/res_x, 1.0) + 0.01
        self.scale_x = scale_x
        self.scale_y = scale_y
    return None

############################## Poll Functions ##############################
# Camera Poll
# Make sure that the object is camera
def camera_poll(self, object):
    return object.type == "CAMERA"

# Target Object Poll 
# Make sure that the target is not a geo node container and not a camera
def target_object_poll(self, object):
    fw_group = self.id_data.path_resolve('fw_group')
    container = fw_group.container
    return object != container and object.type != "CAMERA"

# Target Collection Poll
# Make sure the collection is not the Flares collection
def target_collection_poll(self, collection):
    fw_group = self.id_data.path_resolve('fw_group')
    return collection != fw_group.collection

################################ Properties ################################
# Elements    
class Elements(PropertyGroup):
    name : StringProperty()
    ui_name : StringProperty()
    flare : StringProperty()
    type : StringProperty()
    intensity : FloatProperty(
        name = 'Intensity',
        default = 1.0,
        min = 0.0,
        max = 10000.0,
        description = 'Intensity of the Element'
    )
    color : FloatVectorProperty(
        name = 'Color',
        size = 4,
        subtype='COLOR',
        default=[1.0,1.0,1.0,1.0],
        min = 0.0,
        max = 1.0,
        description = "Element's color"
    )
    image : PointerProperty(
        name = 'Image',
        type = bpy.types.Image,
        description = 'Image Texture',
        update = set_image
    )
    location_x : FloatProperty(
        name = 'X Location',
        default = 0.0,
        min = -10000.0,
        max = 10000.0,
        description = 'X Location'
    )
    location_y : FloatProperty(
        name = 'Y Location',
        default = 0.0,
        min = -10000.0,
        max = 10000.0,
        description = 'Y Location'
    )
    rotation : FloatProperty(
        name = 'Rotation',
        default = 0.0,
        min = -pi*10,
        max = pi*10,
        description = 'Rotation',
        subtype =  'ANGLE'
    )    
    scale_x : FloatProperty(
        name = 'Scale X',
        default = 1.0,
        min = 0.00001,
        max = 50.0,
        description = 'X Scale of the Element'
    )
    scale_y : FloatProperty(
        name = 'Scale Y',
        default = 1.0,
        min = 0.00001,
        max = 50.0,
        description = 'Y Scale of the Element'
    )
    position : FloatProperty(
        name = 'Position',
        default = 0.0,
        min = -10000.0,
        max = 10000.0,
        description = 'Position of the Element on a line passing through the center of the camera.\n'
        '0: The position of the Traget.\n'
        '1: The center of the camera.\n'
        '2: Mirrored position, considering the center of the camera as the pivot point'
    )
    lock_x : FloatProperty(
        name = 'Lock X',
        default = 0.0,
        min = 0.0,
        max = 1.0,
        description = 'Lock the X location'
    )
    lock_y : FloatProperty(
        name = 'Lock Y',
        default = 0.0,
        min = 0.0,
        max = 1.0,
        description = 'Lock the Y location'
    )
    use_global_color : FloatProperty(
        name = 'Use Global Color',
        default = 1.0,
        min = 0.0,
        max = 1.0,
        description = 'Use the Global Color'
    )
    light_falloff : FloatProperty(
        name = 'Falloff',
        default = 1.0,
        min = 0.5,
        max = 100.0,
        description = 'Light Falloff: Intensity of Light decrease with distance'
    )
    fade_distance : FloatProperty(
        name = 'Fading Distance',
        default = 0.0,
        min = -100.0,
        max = 100.0,
        description = 'The distance for the element to completely fade out'
    )
    feather : FloatProperty(
        name = 'Feathering',
        default = 1.0,
        min = 0.001,
        max = 100.0,
        description = 'Blur the edges'
    )
    track_target : BoolProperty(
        name = 'Track the target',
        default = False,
        description = "Make the element rotates to point toward the Target"
    )
    ghosts_count : IntProperty(
        name = 'Count',
        default = 10,
        min = 1,
        max = 30,
        soft_max = 15,
        update = update_ghosts,
        description = 'Number of the ghosts'
    )
    ghosts_distance : FloatProperty(
        name = 'Distance',
        default = 0.2,
        min = -100.0,
        max = 100.0,
        description = 'Distance between the Elements'
    )
    ghosts_random_distance : FloatProperty(
        name = 'Random Distance',
        default = 0.0,
        min = -100.0,
        max = 100.0,
        description = 'Random Distance between the Elements'
    )
    ghosts_random_x : FloatProperty(
        name = 'Random X',
        default = 0.0,
        min = -100.0,
        max = 100.0,
        description = 'Randomize the X Location'
    )
    ghosts_random_y : FloatProperty(
        name = 'Random Y',
        default = 0.0,
        min = -100.0,
        max = 100.0,
        description = 'Randomize the Y Location'
    )
    random_scale : FloatProperty(
        name = 'Random Scale',
        default = 0.0,
        min = 0.0,
        max = 1.0,
        description = 'Randomize the scale of the Ghosts'
    )
    random_scale_seed : IntProperty(
        name = 'Seed',
        default = 0,
        min = 0,
        max = 100000,
        description = 'Random seed'
    )
    random_rot : FloatProperty(
        name = 'Random Rotation',
        default = 0.0,
        min = 0.0,
        max = 1.0,
        description = 'Randomize the rotation'
    )
    random_rot_seed : IntProperty(
        name = 'Seed',
        default = 0,
        min = 0,max = 100000,
        description = 'Random seed'
    )
    ghosts_random_loc_seed : IntProperty(
        name = 'Seed',
        default = 0,
        min = 0,
        max = 100000,
        description = 'Random seed'
    )
    ghosts_random_col_seed : IntProperty(
        name = 'Seed',
        default = 0,
        min = 0,
        max = 100000,
        description = 'Random seed'
    )
    streaks_count : IntProperty(
        name = 'Count',
        default = 1,
        min = 1,
        max = 30,
        soft_max = 20,
        update = update_ghosts,
        description = 'Number of Streaks'
    )
    ring_ray_length : FloatProperty(
        name = 'Ray Length',
        default = 0.4,
        min = 0.02,
        max = 1.0,
        description = 'Length of the Rays'
    )
    ring_random_length : FloatProperty(
        name = 'Random Length',
        default = 0.0,
        min = 0.0,
        max = 1.0,
        description = 'Randomize the Length'
    )
    ring_ray_width : FloatProperty(
        name = 'Ray Width',
        default = 1.0,
        min = 0.01,
        max = 1.0,
        description = 'Width of the Rays'
    )
    ring_random_width : FloatProperty(
        name = 'Random Width',
        default = 0.5,
        min = 0.0,
        max = 1.0,
        description = 'Randomize the Width'
    )
    ring_ray_count : IntProperty(
        name = 'Count',
        default = 120,
        min = 0,
        max = 1000,
        description = 'Number of Rays'
    )
    ring_length_seed : IntProperty(
        name = 'Seed',
        default = 0,
        min = 0,
        max = 100000,
        description = 'Random seed'
    )
    ring_width_seed : IntProperty(
        name = 'Seed',
        default = 0,
        min = 0,
        max = 100000,
        description = 'Random seed'
    )
    use_spectrum : FloatProperty(
        name = 'Use Spectrum',
        default = 1.0,
        min = 0.0,
        max = 1.0,
        description = 'Use Spectrum'
    )
    spectrum_offset : FloatProperty(
        name = 'Offset',
        default = 1.0,
        min = 1.0,
        max = 1000.0,
        description = 'Spectrum Color Offset'
    )
    distortion : FloatProperty(
        name = 'Distortion',
        default = 0.0,
        min = 0.0,
        max = 10.0,
        description = 'Distort the element, for a more organic look'
    )
    noise_scale : FloatProperty(
        name = 'Noise Scale',
        default = 1.0,
        min = 1.0,
        max = 1000.0,
        description = 'Noise Scale'
    )
    circular_completion : FloatProperty(
        name = 'Circular Completion',
        default = 0.0,
        min = 0.0,
        max = 1.0,
        description = 'Circular Completion'
    )
    completion_feather : FloatProperty(
        name = 'Feather',
        default = 0.0,
        min = 0.0,
        max = 1.0,
        description = 'Feathering'
    )
    shimmer_complexity : IntProperty(
        name = 'Complexity',
        default = 16,
        min = 3,
        max = 1000,
        description = 'Complexity'
    )
    shimmer_length : FloatProperty(
        name = 'Random Length',
        default = 0.5,
        min = 0.0,
        max = 1.0,
        description = 'Randomize the length of the rays'
    )
    shimmer_width : FloatProperty(
        name = 'Ray Width',
        default = 1.0,
        min = 1.0,
        max = 100.0,
        description = 'Ray Width'
    )
    shimmer_length_seed : IntProperty(
        name = 'Random Seed',
        default = 0,
        min = 0,
        max = 100000,
        description = 'Random seed'
    )
    shimmer_speed : FloatProperty(
        name = 'Animation Speed',
        default = 0.0,
        min = 0.0,max = 1000.0,
        description = 'Speed of the Shimmer Animation.\n0 = No Animation'
    )
    mask_size : FloatProperty(
        name = 'Mask Size',
        default = 1.0,
        min = 0.01,
        max = 1000.0,
        description = 'Mask Size'
    )
    mask_feather : FloatProperty(
        name = 'Mask Feather',
        default = 5.0,
        min = 0.01,
        max = 1000.0,
        description = 'Smooth the edges of the mask'
    )
    interpolation : EnumProperty(
        name = 'Interpolation',
        items = (
            ('0', 'Linear', ''),
            ('1', 'Stepped Linear', ''),
            ('2', 'Smooth Step', ''),
            ('3', 'Smoother Step', '')
        ),
        description = 'Interpolation Type'
    )
    interpolation2 : EnumProperty(
        name = 'Interpolation',
        items = (
            ('0', 'Linear', ''),
            ('1', 'Stepped Linear', ''),
            ('2', 'Smooth Step', ''),
            ('3', 'Smoother Step', '')
        ),
        description = 'Interpolation Type'
    )
    spectrum_interpolation: EnumProperty(
        name = 'Interpolation',
        items = (
            ('0', 'Linear', ''),
            ('1', 'Ease', ''),
            ('2', 'B-Spline', ''),
            ('3', 'Cardinal', ''),
            ('4', 'Constant', '')
        ),
        description = 'Interpolation Type'
    )
    iris_count : IntProperty(
        name = 'Count',
        default = 6,
        min = 3,
        max = 200,
        description = 'Number of sides'
    )
    iris_roundness : FloatProperty(
        name = 'Roundness',
        default = 1.5,
        min = 0.5,
        max = 5.0,
        description = 'Roundness of the Iris'
    )
    iris_blades : FloatProperty(
        name = 'Blades',
        default = 0.0,
        min = -0.5,
        max = 0.5,
        description = 'Blades'
    )
    iris_feather : FloatProperty(
        name = 'Feather',
        default = 0.0001,
        min = 0.0001,
        max = 1.0,
        description = 'Blur the edges'
    )
    iris_outline_opacity : FloatProperty(
        name = 'Outline Opacity',
        default = 0.0,
        min = 0.0,
        max = 1.0,
        description = 'Opacity of the outline'
    )
    iris_outline_thikness : FloatProperty(
        name = 'Outline Thikness',
        default = 0.0,
        min = 0.0,
        max = 100.0,
        description = 'Thikness of the outline'
    )
    iris_rings_opacity : FloatProperty(
        name = 'Rings Opacity',
        default = 0.0,
        min = 0.0,
        max = 1.0,
        description = 'Opacity of the outline'
    )
    iris_rings_count : IntProperty(
        name = 'Rings Count',
        default = 8,
        min = 1,
        max = 100,
        description = 'Number of Rings'
    )
    caustic_thikness : FloatProperty(
        name = 'Thikness',
        default = 0.1,
        min = 0.001,
        max = 1.0,
        description = 'Thikness of the Outline'
    )
    caustic_shape : FloatProperty(
        name = 'Shape',
        default = 0.5,
        min = 0.0,
        max = 1.0,
        description = 'Shape of the Caustic.\n'
        '0: Circle Shape.\n'
        '1: X Shape'
    )
    proximity_trigger : BoolProperty(
        name = 'Use the Proximity Trigger',
        default = False,
        description = 'Use the proximity to the camera (borders & center) as a trigger.\n'
        'To change the intensity of the element dynamically,\n'
        'when the target gets close to the camera borders or center'
    )
    proximity_intensity : FloatProperty(
        name = 'Intensity',
        default = 1.0,
        min = 0.0,
        max = 1000000.0,
        description = 'Replace the intensity of the element by this value.\n'
        'It is mapped to the white color in the Color-ramp bellow.\n'
        'The intensity of the element is mapped to the black color.\n'
        'The far right side of the color-ramp represents the borders of the camera.\n'
        'The left side of the color-ramp represents the center of the camera'
    )
    hide : BoolProperty(
        name = 'Hide',
        default = False,
        description = 'Hide this Element',
        update = hide_element
    )

# Lens Flare
class Flare(PropertyGroup):
    name : StringProperty()
    ui_name : StringProperty()
    hide : BoolProperty(
        name = 'Hide',
        default = False,
        description = 'Hide this Lens Flare'
    )
    target_type : EnumProperty(
        name = 'Targets Type',
        items = (
            ('OBJECT','Object','', 'OBJECT_DATA', 0),
            ('COLLECTION','Collection','', 'OUTLINER_COLLECTION', 1)
        ),
        default = 'OBJECT',
        description = 'The target could be a single object or the objects inside a collection'
    )
    target_object : PointerProperty(
        name = 'Target',
        type = bpy.types.Object,
        description = 'The lens flare will be attached to the origin of this object, or its geo data',
        poll = target_object_poll,
        update = update_flare_target
    )
    target_collection : PointerProperty(
        name = 'Targets',
        type = bpy.types.Collection,
        description = 'The lens flare will be attached to the objects inside this collection',
        poll = target_collection_poll,
        update = update_flare_target
    )
    use_geo_data : BoolProperty(
        name = 'Use Geometry Data',
        default = False,
        description = 'Use the geometry data of the target object.\n'
        'Position of the geo data (points, instances...) will be used to generate the Flares.\n'
        'It works with the objects that have a geometry (Mesh, Curve, Text...etc).\n'
        'The Modifiers are taken into account, including Geometry Nodes'
    )
    max_instances : IntProperty(
        name = 'Max Number',
        default = 100,
        min = -1,
        max = 5000,
        soft_min = 0,
        soft_max = 1000,
        description = 'Maximum number of instances.\n'
        'You can use the value -1 to display all the instances (No Limit)'
    )
    max_distance : FloatProperty(
        name = 'Max Distance',
        default = -1.0,
        min = -1.0,
        max = 1000000.0,
        soft_min = 0.0,
        soft_max = 10000.0,
        description = 'Maximum distance from the target to the active camera.\n'
        'Any target with a distance to the camera higher than this value will be ignored.\n'
        'You can use the value -1 to display all the instances (No Limit)'
    )
    material : PointerProperty(type = bpy.types.Material)
    intensity : FloatProperty(
        name = 'Intensity',
        default = 1.0,
        min = 0.0,
        max = 10000.0,
        description = 'Intensity of the Lens Flare'
    )
    scale : FloatProperty(
        name = 'Scale',
        default = 1.0,
        min = 0.00001,
        max = 10000.0,
        description = 'Scale of the Lens Flare'
    )
    color : FloatVectorProperty(
        name = 'Color',
        size = 4,
        subtype='COLOR',
        default=[1.0,1.0,1.0,1.0],
        min = 0.0,
        max = 1.0,
        description = 'Global color'
    )
    detect_obstacles : BoolProperty(
        name = 'Detect Obstacles',
        default = False,
        description = 'Make the Lens Flare disappear when the target is behind an object'
    )
    obstacles_collection : PointerProperty(
        name = 'Collection',
        type = bpy.types.Collection,
        description = 'The objects inside this collection will be considered as obstacles',
        poll = target_collection_poll,
        update = update_obstacles_collection
    )
    obstacles_samples : IntProperty(
        name = 'Samples',
        default = 8,
        min = 8,
        max = 64,
        description = 'Precision of the proximity detection.\n'
        '8 is more than enough for most cases.\n'
        'For optimal results choose a value that is a multiple of 8. (8, 16, 24, 32...)\n'
        'Just be aware that it is very expensive to compute'
    )
    obstacles_steps : IntProperty(
        name = 'Steps',
        default = 1,
        min = 1,
        max = 64,
        description = 'Divide the Distance into this amount of steps, for a smooth fadeout.\n'
        'Just be aware that it is very expensive to compute'
    )
    obstacles_distance : FloatProperty(
        name = 'Distance',
        default = 0.25,
        min = 0.001,
        max = 100.0,
        description = 'Distance to search for obstacles, so that the fadeout starts before reaching the object'
    )
    detect_borders : BoolProperty(
        name = 'Detect Borders',
        default = True,
        description = 'Make the Lens Flare disappear gradually when the\n'
        'Target is no longer visible from the Camera View'
    )
    border_distance : FloatProperty(
        name = 'Distance',
        default = 0.25,
        min = 0.001,
        max = 100.0,
        description = 'Fadeout Distance'
    )
    blink : BoolProperty(
        name = 'Enable Blinking',
        default = False,
        description = 'Make the Lens Flare blink (flickering)'
    )
    blink_min : FloatProperty(
        name = 'Minimum',
        default = 0.25,
        min = 0.0,
        max = 0.9,
        description = 'Blinking minimum value (Maximum = 1), the output is in the range (min, max)'
    )
    blink_speed : FloatProperty(
        name = 'Speed',
        default = 1.0,
        min = 0.01,
        max = 100.0,
        description = 'Blinking Speed'
    )
    blink_distortion : FloatProperty(
        name = 'Distortion',
        default = 1.0,
        min = 0.0,
        max = 10000.0,
        description = 'Distort the noise'
    )
    blink_random_seed : IntProperty(
        name = 'Random Seed',
        default = 0,
        min = 0,
        max = 1000000,
        description = 'To change the randomization pattern',
    )
    blink_randomize : BoolProperty(
        name = 'Randomize',
        default = True,
        description = 'For multiple targets, every instance will have a different random seed'
    )
    in_3d_space : FloatProperty(
        name = 'In 3D Space',
        default = 0.0,
        min = 0.0,
        max = 10.0,
        soft_max = 1.0,
        description = 'Change the scale of the flare dynamically Depending on\n'
        'the distance between the target and the camera.\n'
        'To make the lens flare looks like in 3D Space'
    )
    corrective_scale : FloatProperty(
        name = 'Corrective Scale',
        default = 1.0,
        min = 0.01,
        max = 1000000.0,
        description = 'Correcte the Scale'
    )
    random_color : FloatProperty(
        name = 'Randomize',
        default = 0.0,
        min = 0.0,
        max = 1.0,
        description = 'Give every instance a random Color'
    )
    random_color_seed : IntProperty(
        name = 'Seed',
        default = 0,
        min = 0,
        max = 1000000,
        description = 'Random Seed',
    )
    random_intensity : FloatProperty(
        name = 'Randomize',
        default = 0.0,
        min = 0.0,
        max = 1.0,
        description = 'Give every instance a random Intensity'
    )
    random_intensity_seed : IntProperty(
        name = 'Seed',
        default = 0,
        min = 0,
        max = 1000000,
        description = 'Random Seed',
    )
    random_scale : FloatProperty(
        name = 'Randomize',
        default = 0.0,
        min = 0.0,
        max = 1.0,
        description = 'Give every instance a random Scale'
    )
    random_scale_seed : IntProperty(
        name = 'Seed',
        default = 0,
        min = 0,
        max = 1000000,
        description = 'Random Seed',
    )
    color_attr : StringProperty(
        name = 'Attribute',
        default = '',
        description = "Use this attribute as the Global Color of the Flare(s).\n"
        "If the attribute doesn't exist the Global Color will be used instead",
        update = update_attr,
        options = {'TEXTEDIT_UPDATE'}
    )
    intensity_attr : StringProperty(
        name = 'Attribute',
        default = '',
        description = "Use this attribute to control the Intensity of the Flare(s).\n"
        "The intensity of the flare(s) will be multiplied by this attribute.\n"
        "So ideally it should be a float in the range 0 to 1",
        update = update_attr,
        options = {'TEXTEDIT_UPDATE'}
    )
    scale_attr : StringProperty(
        name = 'Attribute',
        default = '',
        description = "Use this attribute to control the Scale of the Flare(s).\n"
        "The scale of the flare(s) will be multiplied by this attribute.\n"
        "So ideally it should be a float in the range 0 to 1",
        update = update_attr,
        options = {'TEXTEDIT_UPDATE'}
    )
    elements : CollectionProperty(type=Elements)
    ele_index : IntProperty(name = 'Element')

class FlareGroup(PropertyGroup):
    # Flare
    coll : CollectionProperty(type=Flare)
    index : IntProperty(name = 'Lens Flare')
    # Collection
    collection : PointerProperty(type = bpy.types.Collection)
    # Container object
    container : PointerProperty(type = bpy.types.Object)
    # Node Group
    node_group : PointerProperty(type = bpy.types.NodeTree)
    # Active Camera
    camera_valid : BoolProperty(default = True)
    camera_tmp : PointerProperty(type = bpy.types.Object)
    # Camera Planes options
    relative_offset : FloatProperty(
        name = 'Relative Offset',
        default = 0.0001,
        min = 0.000001,
        max = 10000.0,
        description = 'Distance between the flare planes'
    )
    global_offset : FloatProperty(
        name = 'Global Offset',
        default = 0.0,
        min = -1000.0,
        max = 1000.0,
        description = 'Move all the flare planes in their Local Z axis'
    )
    planes_margin : FloatProperty(
        name = 'Planes Margin',
        default = 0.001,
        min = 0.0001,
        max = 10000.0,
        description = 'Scale up the flare planes to avoid artefacts on the borders'
    )
    # Background
    bg_plane : PointerProperty(type = bpy.types.Object)
    bg_collection : PointerProperty(type = bpy.types.Collection)
    bg_material : PointerProperty(type = bpy.types.Material)
    bg_z_offset : FloatProperty(
        name = 'Z Offset',
        default = 10.0,
        min = 0.0,
        max = 10000.0,
        description = 'Move the Backgroud Plane away from the Camera'
    )
    bg_opacity : FloatProperty(
        name = 'Opacity',
        default = 1.0,
        min = 0.0,
        max = 1.0,
        description = 'Opacity of the background'
    )
    bg_camera : PointerProperty(
        name = 'Camera',
        description = 'The Camera that the Background Plane will be attached to',
        type = bpy.types.Object,
        update = update_bg_cam,
        poll = camera_poll
    )
    
    
################################# Handler #################################

# Mute the drivers if the active camera is not valide
def mute_drivers(node_group, value):
    if not hasattr(node_group, 'animation_data'):
        return
    animation_data = node_group.animation_data
    if not hasattr(animation_data, 'drivers'):
        return
    for driver in animation_data.drivers:
        if driver.mute != value:
            driver.mute = value

# Active camera handler function
@persistent
def fw_active_cam(scn):
    fw_group = scn.fw_group
    node_group = fw_group.node_group
    # Camera
    cam = scn.camera
    if not hasattr(cam, 'type') or cam.type != 'CAMERA':
        if fw_group.camera_valid:
            fw_group.camera_valid = False
        if fw_group.camera_tmp != None:
            fw_group.camera_tmp = None
        mute_drivers(node_group, True)
        return
    if not fw_group.camera_valid:
        fw_group.camera_valid = True
    # Container
    container = fw_group.container
    if not hasattr(container, 'name'):
        mute_drivers(node_group, True)
        return
    if fw_group.camera_tmp != cam:
        fw_group.camera_tmp = cam
        mute_drivers(node_group, False)
    # Constraint
    constraint = container.constraints.get('FW')
    if constraint is None:
        container.constraints.clear()
        constraint = container.constraints.new(type = 'COPY_TRANSFORMS')
        constraint.name = 'FW'
    if not constraint.target == cam:
        constraint.target = cam

############################################################################################
################################ Register/Unregister #######################################
############################################################################################
classes = (
    Elements,
    Flare,
    FlareGroup,
)    
    
def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    bpy.types.Scene.fw_group = PointerProperty(type = FlareGroup)
    # Handlers
    for i in bpy.app.handlers.depsgraph_update_pre:
        if not i.__name__ == 'fw_active_cam':
            continue
        bpy.app.handlers.depsgraph_update_pre.remove(i)
        
    for i in bpy.app.handlers.frame_change_pre:
        if not i.__name__ == 'fw_active_cam':
            continue
        bpy.app.handlers.frame_change_pre.remove(i)

    bpy.app.handlers.depsgraph_update_pre.append(fw_active_cam)
    bpy.app.handlers.frame_change_pre.append(fw_active_cam)
    
def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    del bpy.types.Scene.fw_group  
    
    
register()