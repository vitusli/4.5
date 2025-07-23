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

if "bpy" in locals():
    import importlib
    if "drivers_utils" in locals():
        importlib.reload(drivers_utils)
    if "shader_utils" in locals():
        importlib.reload(shader_utils)
    if "props" in locals():
        importlib.reload(props)
else:
    from . import drivers_utils
    from . import shader_utils
    from . import props

import bpy, os, json
from sys import platform
from subprocess import check_output, call
from mathutils import Vector, Euler
from bpy.props import *
from bpy.types import UIList, Panel, Operator, Menu, AddonPreferences, Header
from bpy.app.handlers import load_post, persistent

# Paths
addon_folder = os.path.dirname(__file__)
textures_folder = os.path.join(addon_folder, "Textures")
presets_folder = os.path.join(addon_folder, "Presets")
previews_folder = os.path.join(addon_folder, "Previews")
icons_folder = os.path.join(addon_folder, "Icons")
geo_nodes_blend = os.path.join(addon_folder, "Geo_Node_Groups.blend")
shaders_blend = os.path.join(addon_folder, "Shader_Node_Groups.blend")
preview_blend = os.path.join(addon_folder, "preview_template.blend")
preset_to_render = os.path.join(addon_folder, "preset_to_render")
manual_path = os.path.join(addon_folder, "Manual.pdf")

# Previews Dictionary
preview_collections = {}

################################################################################
############################## Preferences #####################################
################################################################################
# Upadate the name of the add-on's tab
def update_tab_name(self, context):
    panels = [i for i in classes if '_PT_' in i.__name__]
    for panel in panels:
        try:
            bpy.utils.unregister_class(panel)
        except:
            pass
        panel.bl_category = self.tab_name
        bpy.utils.register_class(panel)
    return None

# Save the preferences when the presets path is updated
def update_presets_path(self, context):
    if os.path.exists(self.presets_path) and self.save_preferences:
        bpy.ops.wm.save_userpref()
    return None

# Update the page number of the presets browser
def update_filter(self, context):
    self.page_number = 1
    return None

class FLARESWIZARD_Preferences(AddonPreferences):
    bl_idname = __name__
    
    preferences_tabs : EnumProperty(
        items = (
            ('PRESETS', 'Presets', 'Your custom presets.', 'FILE_FOLDER', 0),
            ('UI', 'UI', 'UI Options.', 'IMAGE_BACKGROUND', 1),
            ('DOC', 'Documentation', 'Documentation of the add-on.', 'DOCUMENTS', 2),
            ('MORE', 'More from us', 'More of our tools.', 'URL', 3),
        ),
        name = 'Preferences Tabs',
        default = 'PRESETS',
        description = 'Preferences Tabs'
    )
    presets_path : StringProperty(
        name="Custom Presets Folder",
        description = "The folder where your custom presets are stored.\n"
        "If 'Save the preferences' is not enabled don't forget\n"
        "to save the preferences after selecting the folder",
        update = update_presets_path,
        subtype='DIR_PATH'
    )
    save_preferences : BoolProperty(
        name = 'Save the preferences',
        description = 'Save the preferences automatically when the presets path changes.\n'
        'You need to save the preferences first in order to save your custom presets properly',
        default = True
    )
    columns_count : IntProperty(
        name = 'Number of Columns',
        default = 5,
        min = 3,
        max = 10,
        update = update_filter,
        description = 'Number of columns in the Presets Browser'
    )
    rows_count : IntProperty(
        name = 'Number of Rows',
        default = 2,
        min = 1,
        max = 10,
        update = update_filter,
        description = 'Number of Rows in the Presets Browser'
    )    
    page_number : IntProperty(
        name = 'Page Number',
        default = 1,
        min = 1,
        max = 1000000,
        description = 'Page Number'
    )
    presets_filter : StringProperty(
        name = 'Presets Filter',
        update = update_filter,
        description = 'Search for Presets',
        options = {'TEXTEDIT_UPDATE'}
    )
    targets : EnumProperty(
        name = 'Targets',
        items = (
            ('OBJECT','Active Object','', 'OBJECT_DATA', 0),
            ('COLLECTION','Active Collection','', 'OUTLINER_COLLECTION', 1)
        ),
        default = 'OBJECT',
        description = 'You can attach the Lens Flare to the active object or the active collection'
    )
    thumb_size : EnumProperty(
        name = 'Thumbnails Size',
        default = '7',
        items = (
            ('5', 'Tiny', ''),
            ('6', 'Small', ''),
            ('7', 'Regular', ''),
            ('8', 'Large', ''),
            ('9', 'Very Large', '')
        ),
        description = 'Size of the Thumbnails',
    )
    builtin_presets : BoolProperty(
        name = 'Built-in Presets',
        default = True,
        update = update_filter,
        description = 'Display the presets that are shipped with the add-on'
    )
    custom_presets : BoolProperty(
        name = 'Custom Presets',
        default = True,
        update = update_filter,
        description = 'Display the custom presets'
    )
    tab_name : StringProperty(
        name ="Tab Name",
        default = "Lens Flares",
        update = update_tab_name,
        description = "Choose a name for the add-on's tab"
    )
    def draw(self, context):
        pcoll = preview_collections["icons"]
        scn = context.scene
        layout = self.layout
        col = layout.column()
        row = col.row()
        row.prop(self, 'preferences_tabs', expand = True)
        ################### Presets ###################
        if self.preferences_tabs == 'PRESETS':
            box = layout.box()
            col = box.column()
            col.prop(self, 'presets_path')
            col.prop(self, 'save_preferences')
            if not self.presets_path.strip():
                col.label(text = "Please select a folder", icon = 'INFO')
            elif not os.path.exists(self.presets_path):
                col.label(text = "Wrong Folder Path", icon = 'ERROR')
            else:
                presets = get_custom_presets(context)
                box = col.box()
                text = str(len(presets)) + ' Presets in this folder'
                box.label(text = text, icon = 'INFO')
        ######################## UI #########################
        elif self.preferences_tabs == 'UI':
            box = layout.box()
            box.prop(self, 'tab_name')
            box = layout.box()
            box.prop(self, 'thumb_size')
            box.prop(self, 'columns_count')
            box.prop(self, 'rows_count')
        ################### Documentation ###################
        elif self.preferences_tabs == 'DOC':
            box = layout.box()
            box.operator("flares_wizard.open_manual", icon = 'TEXT')
            ico = get_custom_icon_id(pcoll, 'yt_logo')
            box.operator("flares_wizard.video_tuts", icon_value = ico)
            
        ################### More from us ###################
        elif self.preferences_tabs == 'MORE':
            box = layout.box()
            ico = get_custom_icon_id(pcoll, 'coa')
            box.label(text = 'Check out our stores', icon_value=ico)
            
            ico = get_custom_icon_id(pcoll, 'gumroad_logo')
            url = 'https://codeofart.gumroad.com/'
            text = 'Our store in Gumroad'
            box.operator("wm.url_open", text = text, icon_value=ico).url = url
            
            ico = get_custom_icon_id(pcoll, 'blender_market_logo')
            url = 'https://blendermarket.com/creators/monaime'
            text = 'Our store in the Blender Market'
            box.operator("wm.url_open", text = text, icon_value=ico).url = url

# Add-on Preferences
def prefs(context):
    addon = context.preferences.addons.get(__name__)
    if addon is not None:
        return addon.preferences
    return None

# Custom presets folder
def custom_presets_dir(context):
    preferences = prefs(context)
    if preferences is None:
        return None
    if not os.path.exists(preferences.presets_path):
        return None
    return preferences.presets_path

#  Get the targets from the preferences
def get_targets(context):
    preferences = prefs(context)
    obs = context.scene.objects
    container = context.scene.fw_group.container
    collection = context.scene.fw_group.collection
    # Target
    targets_type = preferences.targets
    if targets_type == 'OBJECT':
        ob = context.object
        if not ob or ob == container or ob.type == 'CAMERA':
            targets = None
        else:
            targets = ob
    else:
        act_coll = context.view_layer.active_layer_collection
        if act_coll.collection == collection:
            targets = None
        else:
            targets = act_coll.collection
    return targets, targets_type

############################################################################################
######################################## Utils #############################################
############################################################################################
# Get a new unique name for a property
def get_prop_name(name, names):
    newname = name    
    i = 2
    while newname in names:
        newname = name + str(i)
        i += 1
    return newname

# Remove Unused Images
def remove_unused_images():
    images = bpy.data.images
    for image in images:
        if image.users:
            continue
        images.remove(image)

# Load and register the add-on's properties
def load_props():
    file = 'flares_wizard_properties.py'
    texts = bpy.data.texts
    text = texts.get(file)
    if text:
        texts.remove(text)
    text = texts.load(os.path.join(addon_folder, file))
    text.use_module = True
    exec(text.as_string(), {})

# On blend load Handler
@persistent
def fw_load_handler(dummy):
    # Set the name of the add-on's tab
    preferences = prefs(bpy.context)
    if preferences.tab_name != 'Lens Flares':
        preferences.tab_name = preferences.tab_name
    # Load the properties if necessary
    scn = bpy.context.scene
    if 'fw_group' in scn and not hasattr(scn, 'fw_group'):
        if not 'coll' in scn['fw_group']:
            return
        if not len(scn['fw_group']['coll']):
            return
        load_props()
        print('Flares Wizard Properties Loaded')
    
# Check if the properties are loaded and auto run scripts is enabled
def is_ready(context):
    paths = context.preferences.filepaths
    if not paths.use_scripts_auto_execute:
        return False
    if not hasattr(context.scene, 'fw_group'):
        return False
    engine = context.scene.render.engine
    if not engine in ['CYCLES', 'BLENDER_EEVEE_NEXT']:
        return False
    return True
    
# Load a node group (append from a blend file)
def load_ng(ng_dir, ng_name):
    with bpy.data.libraries.load(ng_dir, link=False) as (data_src, data_dst):
        data_dst.node_groups = [ng_name]
    return bpy.data.node_groups.get(ng_name)
    
# Lens Flares collection properties
def flares_coll(context):
    coll = context.scene.fw_group.coll
    index = context.scene.fw_group.index
    return coll, index

# The active Lens Flare
def active_flare(context):
    coll = context.scene.fw_group.coll
    index = context.scene.fw_group.index
    if len(coll):
        return coll[index]
    return None

# Remove the material of a lens flare
def remove_lf_material(material):
    if material is None:
        return
    if not hasattr(material, 'node_tree'):
        bpy.data.materials.remove(material)
        return
    for node in material.node_tree.nodes:
        if node.type != 'GROUP':
            continue
        groups = []
        for n in node.node_tree.nodes:
            if n.type != 'GROUP':
                continue
            if n.node_tree not in groups:
                groups.append(n.node_tree)
        for i in groups:
            bpy.data.node_groups.remove(i)
        bpy.data.node_groups.remove(node.node_tree)
    bpy.data.materials.remove(material)
    
# Remove the geometry node groups
def remove_lf_geo_ng(node_group):
    ngs = ['LF_Blinking', 'LF_Borders_Detection', 'LF_Generator',
           'LF_Obstacles_Detection', 'LF_Planes_Generator',
           'LF_Sort_Attribute', 'LF_Store_Attributes']
           
    node_groups = bpy.data.node_groups
    for i in ngs:
        group = node_groups.get(i) 
        if group is None:
            continue
        if group.type != 'GEOMETRY':
            continue
        node_groups.remove(group)
    if hasattr(node_group, 'name'):
        node_groups.remove(node_group)

# Add lens flare
def add_lens_flare(context, target, target_type):
    scn = context.scene
    coll = scn.fw_group.coll
    names = coll.keys()
    ui_names = [i.ui_name for i in coll]
    flare = coll.add()
    flare.name = get_prop_name('LF', names)
    flare.ui_name = get_prop_name('Lens Flare', ui_names)
    scn.fw_group.index = len(scn.fw_group.coll) -1
    # set the targets
    flare.target_type = target_type
    if target_type == 'COLLECTION':
        flare.target_collection = target
    else:
        flare.target_object = target
    flare.material = shader_utils.create_lf_material(flare)
    generate_lf_geo_node_tree(context)
    return flare

# Remove Lens Flare
def remove_lens_flare(context):
    coll, index = flares_coll(context)
    flare = coll[index]
    # Remove the LF geo node
    fw_group = context.scene.fw_group
    node_group = fw_group.node_group
    flare_node = None
    if hasattr(node_group, 'nodes'):
        nodes = node_group.nodes
        flare_node = nodes.get(flare.name)
    if flare_node is not None:
        nodes.remove(flare_node)
    # remove the material
    remove_lf_material(flare.material)
    # remove the AOV
    remove_lf_aov(context, flare)
    # remove the properties
    coll.remove(index)
    if index >0:
        context.scene.fw_group.index = (index - 1)
    # generate the geo node tree
    generate_lf_geo_node_tree(context)
    # Cleanup
    if len(coll):
        return
    # remove the container if empty
    if hasattr(fw_group.container, 'name'):
        mesh = fw_group.container.data
        bpy.data.objects.remove(fw_group.container)
        if not mesh.users:
            bpy.data.meshes.remove(mesh)
    # remove the LF collection if empty
    if hasattr(fw_group.collection, 'name'):
        if not len(fw_group.collection.all_objects):
            bpy.data.collections.remove(fw_group.collection)
    # remove the geometry node_group if empty
    remove_lf_geo_ng(node_group)
    # Remove Unused Images
    remove_unused_images()

# Add an Element
def add_element(context, flare, ele_type):
    elements = flare.elements
    names = elements.keys()
    element = elements.add()
    element.name = get_prop_name('ELEMENT', names)
    element.ui_name = ele_type.capitalize()
    element.type = ele_type
    element.flare = flare.name
    flare.ele_index = len(flare.elements) -1
    elements.update()
    shader_utils.generate_lf_shader_node_tree(context, flare, shaders_blend)
    return element

def get_image_node(flare, element):
    material = flare.material
    mat_node_group = material.node_tree
    element_node = mat_node_group.nodes.get(element.name)
    mat_nodes = element_node.node_tree.nodes
    image_node = None
    if element.type in ['IMAGE', 'LENS_DIRT']:
        image_node = mat_nodes.get('Image Texture')
    elif element.type == 'GHOSTS':
        single_ghost = mat_nodes.get('Single Ghost 0')
        if single_ghost is not None:
            ghost_nodes = single_ghost.node_tree.nodes
            image_node = ghost_nodes.get('Image Texture')
    return image_node

def get_ghost_color_ramp(flare, element):
    node = None
    material = flare.material
    mat_node_group = material.node_tree
    element_node = mat_node_group.nodes.get(element.name)
    mat_nodes = element_node.node_tree.nodes
    single_ghost = mat_nodes.get('Single Ghost 0')
    if single_ghost is not None:
        ghost_nodes = single_ghost.node_tree.nodes
        node = ghost_nodes.get('ColorRamp')
    return node

def get_proximity_color_ramp(flare, element):
    node = None
    material = flare.material
    mat_node_group = material.node_tree
    element_node = mat_node_group.nodes.get(element.name)
    nodes = element_node.node_tree.nodes
    node = nodes.get('ProximityRamp')
    return node

# set image
def set_image(flare, element, image_name):
    image_node = get_image_node(flare, element)
    if not image_node:
        print('Image Node Not Found!')
        return
    images = bpy.data.images
    image = images.get(image_name)
    if not image:
        path = os.path.join(textures_folder, image_name)
        if not os.path.exists(path):
            print('Image Path Not Found:', path)
            return
        image = images.load(path)
    element.image = image

# Remove Element
def remove_element(context):
    flare = active_flare(context)
    elements = flare.elements
    ele_index = flare.ele_index
    element = elements[ele_index]
    # Remove the element's node
    if flare.material is not None:
        nodes = flare.material.node_tree.nodes
        element_node = nodes.get(element.name)
        if element_node is not None:
            nodes.remove(element_node)
    # Remove the properties
    elements.remove(ele_index)
    if ele_index >0:
        flare.ele_index = (ele_index - 1)
    elements.update()
    shader_utils.generate_lf_shader_node_tree(context, flare, shaders_blend)
    
# remove all Elements
def remove_elements(context):
    flare = active_flare(context)
    elements = flare.elements
    count = len(elements)
    for i in range(count):
        if not len(elements):
            continue
        flare.ele_index = 0
        remove_element(context)
    
# update the element when some propeties chenges
def update_element(self, context):
    flare = active_flare(context)
    elements = flare.elements
    ele_index = flare.ele_index
    element = elements[ele_index]
    material = flare.material
    mat_node_group = material.node_tree
    element_node = mat_node_group.nodes.get(element.name)
    if not element_node:
        print('Element Node Not Found')
        return
    if element.type == 'GHOSTS':
        count = element.ghosts_count
        shader_utils.update_ghosts(context, flare, element, element_node, count, shaders_blend)
    if element.type == 'STREAKS':
        count = element.streaks_count
        shader_utils.update_streaks(context, flare, element, element_node, count, shaders_blend)
    return None

######################## Generating Thumbnails ########################

# Get the list of .png images in a folder
def images_in_folder(folder, filter = ''):
    images = []
    if not os.path.exists(folder):
        return images
    
    for fn in os.listdir(folder):
        if not fn.lower().endswith(".png"):
            continue
        if filter.lower() in fn.lower():
            images.append(fn)
    if filter and not images:
        images = ['EMPTY.jpg']
    return images

# List of buil-in presets
def get_builtin_presets():
    presets = []
    if not os.path.exists(presets_folder):
        return presets
    for p in os.listdir(presets_folder):
        if not p.lower().endswith(".lf"):
            continue
        presets.append('B_'+p[:-3])
    return presets

# List of the custom Presets
def get_custom_presets(context):
    presets = []
    custom_folder = custom_presets_dir(context)
    if custom_folder is None:
        return presets
    custom_presets = os.path.join(custom_folder, 'Presets')
    if not os.path.exists(custom_presets):
        return presets
    if os.path.samefile(custom_presets, presets_folder):
        return []
    for p in os.listdir(custom_presets):
        if not p.lower().endswith(".lf"):
            continue
        presets.append('C_'+p[:-3])
    return presets

# Get the list of available presets
def available_presets(context, filter='', builtin=True, custom=True):
    b = get_builtin_presets() if builtin else []
    c = get_custom_presets(context) if custom else []
    presets = [i for i in b+c if filter.lower() in i[2:].lower()]
    return presets

# Generate the presets previews
def genterate_presets_previews(context):        
    pcoll = preview_collections["presets_previews"]
    b = images_in_folder(previews_folder)
    b = ['B_'+i for i in b]
    c = []
    custom_folder = custom_presets_dir(context)
    if custom_folder is not None:
        custom = os.path.join(custom_folder, 'Previews')
        if os.path.exists(custom):
            c = images_in_folder(custom)
    c = ['C_'+i for i in c]
    for i, name in enumerate(b+c):
        folder = previews_folder if name.startswith('B_') else custom
        filepath = os.path.join(folder, name[2:])
        if pcoll.get(name[:-4]) is not None:
            continue
        thumb = pcoll.load(name[:-4], filepath, 'IMAGE')
        
# Generate the elements previews
def generate_elements_previews():
    pcoll = preview_collections["icons"]
    images = images_in_folder(icons_folder)
    for i, name in enumerate(images):
        filepath = os.path.join(icons_folder, name)
        if pcoll.get(name[:-4]) is not None:
            continue
        thumb = pcoll.load(name[:-4], filepath, 'IMAGE')

# Generate elements previews (Enum)
def icons_enum():
    pcoll = preview_collections["icons"]
    enum_items = []
    
    images = images_in_folder(icons_folder)

    for i, name in enumerate(images):
        filepath = os.path.join(icons_folder, name)
        name = name.replace('.png', '')
        thumb = pcoll.load(name, filepath, 'IMAGE')
        enum_items.append((name, name, "", thumb.icon_id, i))
        
    return enum_items

# get icon ID
def get_custom_icon_id(pcoll, image_name):
    icon = pcoll.get(image_name)
    if icon is not None:
        size = icon.image_size[:]
        return icon.icon_id
    return 0

############################################################################################
################################### Geo Nodes Utils ########################################
############################################################################################

# Create a collection for the geo node container
def flares_collection(context):
    flares = context.scene.fw_group
    collection =flares.collection
    if collection is None:
        coll_name = 'Lens Flares Collection'
        main_coll = context.scene.collection
        collections = bpy.data.collections
        scn_colls = [c.name for c in main_coll.children_recursive]
        if coll_name in scn_colls:
            collection = collections[coll_name]
        else:
            collection = collections.new(coll_name)
            main_coll.children.link(collection)
        flares.collection = collection
    return collection

# Add the object container for the geo node modifier
def add_geo_node_container(context):
    scn = context.scene
    # Lens Flares Collection
    coll = flares_collection(context)
    # Mesh    
    me = bpy.data.meshes.new("LF_container")
    # Object
    name = 'LF_GeoNode_Container'
    names = [o.name for o in bpy.data.objects]
    name = get_prop_name(name, names)
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    ob.hide_select = True
    # Modifier
    mod = ob.modifiers.new('FlaresWizard', 'NODES')
    ng = bpy.data.node_groups.new('Flares_Wizard_GEO_NG', 'GeometryNodeTree')
    ng.interface.new_socket(socket_type='NodeSocketGeometry', name='Geometry', in_out='OUTPUT')
    mod.node_group = ng
    path = 'fw_group.camera_valid'
    drivers_utils.add_driver(mod, 'show_viewport', 'show', 'SCENE', scn, path,'show')
    drivers_utils.add_driver(mod, 'show_render', 'show', 'SCENE', scn, path,'show')
    # Constraint
    constraint = ob.constraints.new(type = 'COPY_TRANSFORMS')
    constraint.target = scn.camera
    # Add Properties
    fw_group = scn.fw_group
    fw_group.container = ob
    fw_group.node_group = ng
    fw_group.camera_tmp = scn.camera
    # Cycles Visibility
    ob.visible_glossy = False
    ob.visible_volume_scatter = False
    ob.visible_diffuse = False
    ob.visible_transmission = False
    ob.visible_shadow = False
    # Eevee Visibility
    ob.hide_probe_volume = True
    ob.hide_probe_sphere = True
    ob.hide_probe_plane = True
    ob.visible_shadow = False
    return ob

# Generate Geometry Node Tree
def generate_lf_geo_node_tree(context):
    fw_group = context.scene.fw_group
    if not hasattr(fw_group.container, 'name'):
        add_geo_node_container(context)
    flares = fw_group.coll
    geo_ng = fw_group.node_group
    nodes = geo_ng.nodes
    links = geo_ng.links
    output_node = get_output_node(nodes)
    join_node = get_join_geo_node(nodes)
    links.new(join_node.outputs[0], output_node.inputs[0])
    loc = [0.0, 0.0]
    previous_node = None
    
    # Clear the "LF" outputs
    items_tree = geo_ng.interface.items_tree
    sockets = [i for i in items_tree if i.item_type == 'SOCKET' and i.in_out == 'OUTPUT' and 'LF' in i.name]
    for socket in sockets:
        geo_ng.interface.remove(socket)
    
    # Clear Join Geometry links
    for i in join_node.inputs[0].links:
        links.remove(i)
    
    for i, flare in enumerate(flares):
        flare_node = get_flare_node(context, nodes, flare)
        flare_node.inputs[0].default_value = flare.name
        flare_node.inputs[14].default_value = flare.target_object
        flare_node.inputs[15].default_value = flare.target_collection
        flare_node.inputs[12].default_value = flare.material
        flare_node.inputs[18].default_value = flare.obstacles_collection
        links.new(flare_node.outputs[0], join_node.inputs[0])
        loc[0]+=300
        flare_node.location = loc
        
        if previous_node != None:
            links.new(previous_node.outputs[1], flare_node.inputs[1])
        previous_node = flare_node
        
    loc[0]+=300
    join_node.location = loc
    loc[0]+=300
    output_node.location = loc

######################### Nodes #########################
# Group Output Node
def get_output_node(nodes):
    output = nodes.get('FlaresWizard_Output')
    if output is None:
        output = nodes.new('NodeGroupOutput')
        output.name = 'FlaresWizard_Output'
        output.label = 'Group Output'
    return output

# Join Geometry Node
def get_join_geo_node(nodes):
    join = nodes.get('FlaresWizard_Join_Geometry')
    if join is None:
        join = nodes.new('GeometryNodeJoinGeometry')
        join.name = 'FlaresWizard_Join_Geometry'
        join.label = 'Join Geometry'
    return join

# Lens Flare Geo Node
def get_flare_node(context, nodes, flare):
    flare_node = nodes.get(flare.name)
    if flare_node is not None:
        return flare_node
    scn = context.scene
    # Make sure that the node group (LF_Generator) exists
    ng_name = 'LF_Generator'
    node_groups = bpy.data.node_groups
    flare_ng = node_groups.get(ng_name)
    if flare_ng is None:
        flare_ng = load_ng(geo_nodes_blend, ng_name)
    # Create the Flare Node
    flare_node = nodes.new(type = 'GeometryNodeGroup')
    flare_node.name = flare.name
    flare_node.label = flare.ui_name
    flare_node.node_tree = flare_ng
    ##################### Drivers ##########################
    idx = flare_node.inputs
    v = 'default_value'
    
    # Global Z offset
    drivers_utils.add_driver(idx[1], v, 'offset', 'SCENE', scn, 'fw_group.global_offset','offset')
    # Focal Length
    drivers_utils.add_driver(idx[2], v, 'focal_length', 'SCENE', scn, 'camera.data.lens','focal_length')
    # Sensor Width
    drivers_utils.add_driver(idx[3], v, 'sensor_width', 'SCENE', scn, 'camera.data.sensor_width','sensor_width')
    # Shift X
    drivers_utils.add_driver(idx[6], v, 'shift_x','SCENE', scn, 'camera.data.shift_x','shift_x')
    # Shift Y
    drivers_utils.add_driver(idx[7], v, 'shift_y', 'SCENE', scn, 'camera.data.shift_y','shift_y')
    # Resolution x
    drivers_utils.add_driver(idx[4], v, 'resolution_x', 'SCENE', scn, 'render.resolution_x','resolution_x')
    # Resolution Y
    drivers_utils.add_driver(idx[5], v, 'resolution_y', 'SCENE', scn, 'render.resolution_y','resolution_y')
    # Aspect X
    drivers_utils.add_driver(idx[8], v, 'aspect_x', 'SCENE', scn, 'render.pixel_aspect_x','aspect_x')
    # Aspect Y
    drivers_utils.add_driver(idx[9], v, 'aspect_y', 'SCENE', scn, 'render.pixel_aspect_y','aspect_y')
    # Camera Mrgin
    drivers_utils.add_driver(idx[10], v, 'margin', 'SCENE', scn, 'fw_group.planes_margin' ,'margin')
    # Relative Z offset
    drivers_utils.add_driver(idx[11], v, 'relative_offset', 'SCENE', scn, 'fw_group.relative_offset','relative_offset')
    # Traget type (Object, Collection)
    path = drivers_utils.flare_prop_path(flare, 'target_type')
    drivers_utils.add_driver(idx[13], v, 'target_type', 'SCENE', scn, path,'target_type')
    # Use Geometry Data
    path = drivers_utils.flare_prop_path(flare, 'use_geo_data')
    drivers_utils.add_driver(idx[16], v, 'use_geo_data', 'SCENE', scn, path,'use_geo_data')
    # Detect Obstacles
    path = drivers_utils.flare_prop_path(flare, 'detect_obstacles')
    drivers_utils.add_driver(idx[17], v, 'detect_obstacles', 'SCENE', scn, path,'detect_obstacles')
    # Obstacles Samples
    path = drivers_utils.flare_prop_path(flare, 'obstacles_samples')
    drivers_utils.add_driver(idx[19], v, 'obstacles_samples', 'SCENE', scn, path,'obstacles_samples')
    # Obstacles Steps
    path = drivers_utils.flare_prop_path(flare, 'obstacles_steps')
    drivers_utils.add_driver(idx[20], v, 'obstacles_steps', 'SCENE', scn, path,'obstacles_steps')
    # Obstacles Distance
    path = drivers_utils.flare_prop_path(flare, 'obstacles_distance')
    drivers_utils.add_driver(idx[21], v, 'obstacles_distance', 'SCENE', scn, path,'obstacles_distance/10')
    # Detect Borders
    path = drivers_utils.flare_prop_path(flare, 'detect_borders')
    drivers_utils.add_driver(idx[22], v, 'detect_borders', 'SCENE', scn, path,'detect_borders')
    # Borders Distance
    path = drivers_utils.flare_prop_path(flare, 'border_distance')
    drivers_utils.add_driver(idx[23], v, 'border_distance', 'SCENE', scn, path,'border_distance')
    # Enable Blinking
    path = drivers_utils.flare_prop_path(flare, 'blink')
    drivers_utils.add_driver(idx[24], v, 'blink', 'SCENE', scn, path,'blink')
    # Blinking Min
    path = drivers_utils.flare_prop_path(flare, 'blink_min')
    drivers_utils.add_driver(idx[25], v, 'blink_min', 'SCENE', scn, path,'blink_min')
    # Blinking Speed
    path = drivers_utils.flare_prop_path(flare, 'blink_speed')
    drivers_utils.add_driver(idx[26], v, 'blink_speed', 'SCENE', scn, path,'blink_speed')
    # Blinking Distortion
    path = drivers_utils.flare_prop_path(flare, 'blink_distortion')
    drivers_utils.add_driver(idx[27], v, 'distortion', 'SCENE', scn, path,'distortion')
    # Blinking Random Seed
    path = drivers_utils.flare_prop_path(flare, 'blink_random_seed')
    drivers_utils.add_driver(idx[28], v, 'blink_random_seed', 'SCENE', scn, path,'blink_random_seed')
    # Blinking Randomize
    path = drivers_utils.flare_prop_path(flare, 'blink_randomize')
    drivers_utils.add_driver(idx[29], v, 'blink_randomize', 'SCENE', scn, path,'blink_randomize')
    # In 3D Space
    path = drivers_utils.flare_prop_path(flare, 'in_3d_space')
    drivers_utils.add_driver(idx[30], v, 'in_3d_space', 'SCENE', scn, path,'in_3d_space')
    # Corrective Scale
    path = drivers_utils.flare_prop_path(flare, 'corrective_scale')
    drivers_utils.add_driver(idx[31], v, 'scale', 'SCENE', scn, path,'scale')
    # Scale
    path = drivers_utils.flare_prop_path(flare, 'scale')
    drivers_utils.add_driver(idx[32], v, 'scale', 'SCENE', scn, path,'scale')
    # Intensity
    path = drivers_utils.flare_prop_path(flare, 'intensity')
    drivers_utils.add_driver(idx[33], v, 'intensity', 'SCENE', scn, path,'intensity')
    # Global Color
    path = drivers_utils.flare_prop_path(flare, 'color')
    drivers_utils.add_driver(idx[34], v, 'color', 'SCENE', scn, path,'color', -1, 4)
    # Random Color
    path = drivers_utils.flare_prop_path(flare, 'random_color')
    drivers_utils.add_driver(idx[35], v, 'random_color', 'SCENE', scn, path,'random_color')
    # Color Seed
    path = drivers_utils.flare_prop_path(flare, 'random_color_seed')
    drivers_utils.add_driver(idx[36], v, 'seed', 'SCENE', scn, path,'seed')
    # Random Scale
    path = drivers_utils.flare_prop_path(flare, 'random_scale')
    drivers_utils.add_driver(idx[37], v, 'random_scale', 'SCENE', scn, path,'random_scale')
    # Color Seed
    path = drivers_utils.flare_prop_path(flare, 'random_scale_seed')
    drivers_utils.add_driver(idx[38], v, 'seed', 'SCENE', scn, path,'seed')
    # Random Intensity
    path = drivers_utils.flare_prop_path(flare, 'random_intensity')
    drivers_utils.add_driver(idx[39], v, 'random_intensity', 'SCENE', scn, path,'random_intensity')
    # Color Seed
    path = drivers_utils.flare_prop_path(flare, 'random_intensity_seed')
    drivers_utils.add_driver(idx[40], v, 'seed', 'SCENE', scn, path,'seed')
    # Max Number
    path = drivers_utils.flare_prop_path(flare, 'max_instances')
    drivers_utils.add_driver(idx[41], v, 'max_instances', 'SCENE', scn, path,'max_instances')
    # Max Distance
    path = drivers_utils.flare_prop_path(flare, 'max_distance')
    drivers_utils.add_driver(idx[42], v, 'max_distance', 'SCENE', scn, path,'max_distance')
    # Visibility
    path = drivers_utils.flare_prop_path(flare, 'hide')
    drivers_utils.add_driver(idx[46], v, 'mute', 'SCENE', scn, path,'mute')
    return flare_node

############################################################################################
################################ Save, Load, Duplicate #####################################
############################################################################################
# Get the data of a color-ramp
def get_color_ramp_data(color_ramp):
    cr_data = {}
    cr_data['interpolation'] = color_ramp.color_ramp.interpolation
    cr_ele = color_ramp.color_ramp.elements
    cr_data['elements'] = [[e.position, e.color[:]] for e in cr_ele]
    return cr_data
    
# Set the data of a color-ramp
def set_color_ramp_data(color_ramp, cr_data):
    interpolation = cr_data.get('interpolation')
    if interpolation is not None:
        color_ramp.color_ramp.interpolation = interpolation
    else:
        print('Color Ramp Interpolation not found!')
    elements = cr_data.get('elements')
    if elements is None:
        print('Color Ramp Elements not found!')
        return
    cr_ele = color_ramp.color_ramp.elements
    cr_ele.remove(cr_ele[0])
    for i, element in enumerate(elements):
        if i == 0:
            n = cr_ele[0]
            n.position = element[0]
        else:
            n = cr_ele.new(element[0])
        n.color = element[1]
        
# Get the data of an element
def get_element_data(flare, element):
    element_data = {}
    for p in props.elements[element.type]:
        if not hasattr(element, p):
            print('Property Not Found:', p)
            continue
        element_data[p] = getattr(element, p)
    cr = get_proximity_color_ramp(flare, element)
    element_data['proximity_color_ramp'] = get_color_ramp_data(cr)
    if element.type == 'GHOSTS':
        cr = get_ghost_color_ramp(flare, element)
        element_data['ghost_color_ramp'] = get_color_ramp_data(cr)
    return element_data

# Set the data of an element
def set_element_data(flare, element, element_data):
    # Set the properties
    for key, value in element_data.items():
        if key == 'proximity_color_ramp':
            cr = get_proximity_color_ramp(flare, element)
            set_color_ramp_data(cr, value)
            continue
        if key == 'ghost_color_ramp':
            cr = get_ghost_color_ramp(flare, element)
            set_color_ramp_data(cr, value)
            continue
        if key == 'image' and type(value) == str:
            set_image(flare, element, value)
            continue
        if not hasattr(element, key):
            print(element.type, ', Property Not Found:', key)
            continue
        try:
            setattr(element, key, value)
        except Exception as e:
            print('Error while setting element data:', e)
            continue
        
# Duplicate an element
def duplicate_element(context, flare, element):
    new_element = add_element(context, flare, element.type)
    element_data = get_element_data(flare, element)
    set_element_data(flare, new_element, element_data)
    new_element.ui_name += ' (Copy)'
    
# Get the data of a Flare
def get_flare_data(flare):
    flare_data = {}
    # flare properties
    for p in props.flare:
        if not hasattr(flare, p):
            print('Property Not Found:', p)
            continue
        flare_data[p] = getattr(flare, p)
    # flare elements
    flare_data['elements'] = []
    for element in flare.elements:
        element_data = get_element_data(flare, element)
        flare_data['elements'].append(element_data)
    return flare_data

# Set the data of a Flare
def set_flare_data(context, flare, flare_data):
    for key, value in flare_data.items():
        if not hasattr(flare, key):
            print('Property:', key, 'Not Found!')
            continue
        if key == 'elements':
            for element_data in value:
                ele_type = element_data['type']
                element = add_element(context, flare, ele_type)
                set_element_data(flare, element, element_data)
            continue
        setattr(flare, key, value)
        
# Duplicate a Flare
def duplicate_flare(context, flare):
    target_type = flare.target_type
    target = flare.target_object if target_type == 'OBJECT' else flare.target_collection
    flare_data = get_flare_data(flare)
    new_flare = add_lens_flare(context, target, target_type)
    set_flare_data(context, new_flare, flare_data)
    new_flare.ui_name += ' (Copy)'
    
# cleanup the flare data to be saved as a preset, and make it json friendly
def preset_flare_data(flare_data):
    preset_data = {}
    preset_props = ['ui_name', 'intensity', 'scale', 'color']
    for key, value in flare_data.items():
        if not key in preset_props:
            continue
        if key == 'color':
            preset_data[key] = value[:]
            continue
        preset_data[key] = value
    # Elements date    
    preset_data['elements'] = []
    elements_data = flare_data.get('elements')
    for element_data in elements_data:
        element = {}
        for key, value in element_data.items():
            if key == 'image' and hasattr(value, 'name'):
                element[key] = value.name
            elif 'color_ramp' in key:
                element[key] = value
            elif  hasattr(value, '__getitem__'):
                element[key] = value[:]
            else:
                element[key] = value
        preset_data['elements'].append(element)
    return preset_data
    
# Save a new preset
def save_preset(flare, file_path):
    flare_data = get_flare_data(flare)
    preset_data = preset_flare_data(flare_data)
    # Write to json file
    with open(file_path, 'w') as json_file:
        json.dump(preset_data, json_file, indent=5)
        
# Load a preset
def load_preset(context, flare, preset):
    with open(preset, 'r') as json_file:
        preset_data = json.load(json_file)
    set_flare_data(context, flare, preset_data)

# Display a list of items in a grid
def draw_grid_items(context, layout):
    pcoll = preview_collections["presets_previews"]
    preferences = prefs(context)
    filter = preferences.presets_filter
    builtin = preferences.builtin_presets
    custom = preferences.custom_presets
    items = available_presets(context, filter, builtin, custom)
    page_number = preferences.page_number
    columns_count = preferences.columns_count
    rows_count = preferences.rows_count
    presets_per_page = columns_count*rows_count
    pages_count = calc_pages_count(context)
    tot = presets_per_page*pages_count
    thumb_size = int(preferences.thumb_size)
    dif = tot-len(items)
    items.extend(['']*dif)
    items = items[(page_number-1)*presets_per_page:tot]
    custom_dir = custom_presets_dir(context)
    custom_dir = '' if custom_dir is None else custom_dir
    custom_folder = os.path.join(custom_dir, 'Presets')
            
    i = 0
    for c in range(rows_count):
        row = layout.row()
        for j in range(columns_count):
            name = items[i]
            name_raw = name[2:]
            icon_id = get_custom_icon_id(pcoll, name)
            col = row.column(align = True)
            col.enabled = (name != '')
            box = col.box()
            box.template_icon(icon_value = icon_id, scale=thumb_size)
            folder = presets_folder if name.startswith('B_') else custom_folder
            file_path = os.path.join(folder, name_raw+'.lf')
            text = name_raw if name else ' '
            #icon = 'IMPORT' if name else 'BLANK1'
            row2 = col.row(align = True)
            op = row2.operator("flares_wizard.load_flare",text=text)
            op.file_path = file_path
            op = row2.operator("flares_wizard.delete_preset",text='', icon='X')
            op.preset = name
            i+=1

# Calculate the number of pages
def calc_pages_count(context):
    preferences = prefs(context)
    filter = preferences.presets_filter
    builtin = preferences.builtin_presets
    custom = preferences.custom_presets
    presets = available_presets(context, filter, builtin, custom)
    len_items = len(presets)
    columns_count = preferences.columns_count
    rows_count = preferences.rows_count
    presets_per_page = columns_count*rows_count
    if len_items < presets_per_page:
        return 1
    pages_count = len_items//presets_per_page
    if (len_items%presets_per_page):
        pages_count +=1
    return pages_count

# Render a preview image for the preset
def render_preview():
    blender = bpy.app.binary_path
    blend_file = preview_blend
    if not os.path.exists(blend_file):
        print('Previews Blend File Not found')
        return
    
    output = check_output([blender, blend_file, '--background', '--python-text', 'render.py'])
    
    print('---------------------------------------------')
    print('-----------Rendering Preview Started---------')
    print('---------------------------------------------')
    
    print(output.decode("utf-8"))
    
    print('---------------------------------------------')
    print('----------Rendering Preview Finished---------')
    print('---------------------------------------------')
    
############################################################################################
##################################### Background ###########################################
############################################################################################

# Add the Background plane
def add_bg_plane():
    me = bpy.data.meshes.new("LF_plane_mesh")
    ob = bpy.data.objects.new("FW_BG_Plane", me)
    # mesh data
    verts = [( 1.0,  1.0,  0.0), 
             ( 1.0, -1.0,  0.0),
             (-1.0, -1.0,  0.0),
             (-1.0,  1.0,  0.0),]
    edges = []
    faces = [[0, 1, 2, 3]]
    me.from_pydata(verts, edges, faces)
    return ob

# Create Background Plane
def create_bg(context):
    scn = context.scene
    x_margine, z_margin = (0.001, 0.005)
    
    # Collection
    collections = bpy.data.collections
    main_coll = context.scene.collection
    coll = scn.fw_group.get('bg_collection')
    if not coll:
        coll = collections.new('FW_Background')
        main_coll.children.link(coll)
        scn.fw_group.bg_collection = coll
    elif hasattr(coll, 'name'):
        coll.name = 'FW_Background'
        if coll.name in collections:
            if not main_coll.children.get(coll.name):
                main_coll.children.link(coll)
    
    # Material
    mat = shader_utils.add_bg_material()
    scn.fw_group.bg_material = mat
    img_node = mat.node_tree.nodes.get('Image Texture')
    image_path = os.path.join(textures_folder, 'Black_BG.png')
    if os.path.exists(image_path) and img_node:
        bg_image = bpy.data.images.load(image_path)
        img_node.image = bg_image
    mix = mat.node_tree.nodes.get('Mix')
    if mix is not None:
        # driver for the Opacity
        driver = mix.inputs[0].driver_add("default_value")
        path = 'fw_group.bg_opacity'
        drivers_utils.add_prop_var(driver, 'opacity', 'SCENE', scn, path)
        driver.driver.expression = 'opacity'
                
    # BG plane
    plane = add_bg_plane()
    coll.objects.link(plane)
    plane.data.materials.append(mat)
    scn.fw_group.bg_plane = plane
    plane.parent = scn.camera
    
    # Camera
    scn.fw_group.bg_camera = scn.camera
    
# Add the necessary drivers when the camera changes
def update_bg_camera(self, context):
    scn = context.scene
    plane = scn.fw_group.bg_plane
    if plane is None:
        print('Background Plane not found!')
        return
    cam = scn.fw_group.bg_camera
    if cam is None:
        print('Background Camera not found!')
        return
    
    plane.parent = cam
    plane.matrix_world = cam.matrix_world
    # Drivers
    # Location
    plane.driver_remove("location")
    # X Location
    driver = plane.driver_add("location", 0)
    drivers_utils.add_prop_var(driver, 'shift_x', 'OBJECT', cam, 'data.shift_x')
    driver.driver.expression = 'shift_x'
    # Y Location
    driver = plane.driver_add("location", 1)
    drivers_utils.add_prop_var(driver, 'shift_y', 'OBJECT', cam, 'data.shift_y')
    driver.driver.expression = 'shift_y'
    # Z Location
    driver = plane.driver_add("location", 2)
    drivers_utils.add_prop_var(driver, 'lens', 'OBJECT', cam, 'data.lens')
    drivers_utils.add_prop_var(driver, 'sensor_width', 'OBJECT', cam, 'data.sensor_width')
    drivers_utils.add_prop_var(driver, 'z_offs', 'SCENE', scn, 'fw_group.bg_z_offset')
    expression = '(-lens / sensor_width) * z_offs'
    driver.driver.expression = expression
    # Scale
    plane.driver_remove("scale")
    # X Scale
    driver = plane.driver_add("scale", 0)
    drivers_utils.add_prop_var(driver, 'res_x', 'SCENE', scn, 'render.resolution_x')
    drivers_utils.add_prop_var(driver, 'res_y', 'SCENE', scn, 'render.resolution_y')
    drivers_utils.add_prop_var(driver, 'aspect_x', 'SCENE', scn, 'render.pixel_aspect_x')
    drivers_utils.add_prop_var(driver, 'aspect_y', 'SCENE', scn, 'render.pixel_aspect_y')
    drivers_utils.add_prop_var(driver, 'z_offs', 'SCENE', scn, 'fw_group.bg_z_offset')
    expression = '(clamp((res_x*aspect_x)/(res_y*aspect_y))*z_offs/2)+0.001'
    driver.driver.expression = expression
    # Y Scale
    driver = plane.driver_add("scale", 1)
    drivers_utils.add_prop_var(driver, 'res_x', 'SCENE', scn, 'render.resolution_x')
    drivers_utils.add_prop_var(driver, 'res_y', 'SCENE', scn, 'render.resolution_y')
    drivers_utils.add_prop_var(driver, 'aspect_x', 'SCENE', scn, 'render.pixel_aspect_x')
    drivers_utils.add_prop_var(driver, 'aspect_y', 'SCENE', scn, 'render.pixel_aspect_y')
    drivers_utils.add_prop_var(driver, 'z_offs', 'SCENE', scn, 'fw_group.bg_z_offset')
    expression = '(clamp((res_y*aspect_y)/(res_x*aspect_x))*z_offs/2)+0.001'
    driver.driver.expression = expression
    return None

############################################################################################
##################################### Compositing ##########################################
############################################################################################
# names of the FW Collections
def fw_coll_names(context):
    scn = context.scene
    fw_collections = []
    # Flares Collection
    if hasattr(scn.fw_group.collection, 'name'):
        fw_collections.append(scn.fw_group.collection.name)
    # Background Collection
    if hasattr(scn.fw_group.bg_collection, 'name'):
        fw_collections.append(scn.fw_group.bg_collection.name)
    return fw_collections

# Setup view layers
def setup_view_layers(context):
    scn = context.scene
    fw_collections = fw_coll_names(context)
    if not fw_collections:
        return
    # Setup the view layers
    name = 'Lens Flares'
    view_layer = scn.view_layers.get(name)
    if view_layer is None:
        view_layer = scn.view_layers.new(name)
    elif len(scn.view_layers) == 1:
        return
    view_layer.samples = 1
    view_layer.use_sky = False
    view_layer.use_volumes = False
    view_layer.cycles.use_denoising = False
    for vl in scn.view_layers:
        colls = vl.layer_collection.children
        if vl != view_layer:
            for coll_name in fw_collections:
                colls[coll_name].exclude = True
            continue
        for coll in colls:
            if coll.name in fw_collections:
                coll.exclude = False
                continue
            coll.exclude = True
            
# Remove Lens Flares view layer
def remove_view_layer(context):
    scn = context.scene
    fw_collections = fw_coll_names(context)
    view_layer = scn.view_layers.get('Lens Flares')
    if view_layer is not None:
        remove_aovs(context)
        scn.view_layers.remove(view_layer)
    for vl in scn.view_layers:
        colls = vl.layer_collection.children
        for coll_name in fw_collections:
            colls[coll_name].exclude = False
            
# Setup AOVs
def setup_aovs(context):
    scn = context.scene
    coll, index = flares_coll(context)
    name = 'Lens Flares'
    if not scn.view_layers.get(name):
        setup_view_layers(context)
    view_layer = scn.view_layers.get(name)
    for flare in coll:
        shader_utils.add_aov_nodes(flare)
        if flare.name in view_layer.aovs:
            continue
        aov = view_layer.aovs.add()
        aov.name = flare.name
        aov.type = 'COLOR'
        
# Remove AOVs
def remove_aovs(context):
    scn = context.scene
    coll, index = flares_coll(context)
    for flare in coll:
        shader_utils.remove_aov_nodes(flare)
    flares_view_layer = scn.view_layers.get('Lens Flares')
    if flares_view_layer is None:
        return
    act_view_layer = context.view_layer
    try:
        context.window.view_layer = flares_view_layer
        for i in reversed(range(len(flares_view_layer.aovs))):
            flares_view_layer.active_aov_index = i
            aov = flares_view_layer.active_aov
            if aov.name not in coll.keys():
                continue
            bpy.ops.scene.view_layer_remove_aov()
    except Exception as e:
            print('Error while deleting the AOVs:', e)
    finally:
        context.window.view_layer = act_view_layer
        
# Remove Lens Flare AOV
def remove_lf_aov(context, flare):
    scn = context.scene
    flares_view_layer = scn.view_layers.get('Lens Flares')
    if flares_view_layer is None:
        return
    act_view_layer = context.view_layer
    try:
        context.window.view_layer = flares_view_layer
        for i in range(len(flares_view_layer.aovs)):
            flares_view_layer.active_aov_index = i
            aov = flares_view_layer.active_aov
            if aov.name == flare.name:
                bpy.ops.scene.view_layer_remove_aov()
                break
    except Exception as e:
            print('Error while deleting the AOVs:', e)
    finally:
        context.window.view_layer = act_view_layer

############################################################################################
###################################### Operators ###########################################
############################################################################################

# Load the FW properties
class FLARESWIZARD_OT_load_props(Operator):
    bl_idname = "flares_wizard.load_props"
    bl_label = "Load"
    bl_options = {'UNDO'}
    bl_description = "Load the add-on's properties to the blend file"
    
    def execute(self, context):
        load_props()
        return {'FINISHED'}

# Add a Lens Flare
class FLARESWIZARD_OT_add_lf(Operator):
    bl_idname = "flares_wizard.add_lens_flare"
    bl_label = "Blank"
    bl_options = {'UNDO'}
    bl_description = "Add an empty Lens Flare"
    
    @classmethod
    def poll(self, context):
        scn = context.scene
        if not hasattr(scn, 'fw_group'):
            return False
        cam = scn.camera
        if not hasattr(cam, 'type') or cam.type != 'CAMERA':
            return False
        return True
    
    def execute(self, context):
        targets, targets_type = get_targets(context)
        add_lens_flare(context, targets, targets_type)
        return {'FINISHED'}
    
# Remove Lens Flare
class FLARESWIZARD_OT_remove_lens_flare(Operator):
    bl_idname = "flares_wizard.remove_lens_flare"
    bl_label = "Remove"
    bl_options = {'UNDO'}
    bl_description = "Remove the selected Lens Flare"
    
    @classmethod
    def poll(self, context):
        scn = context.scene
        if not hasattr(scn, 'fw_group'):
            return False
        return len(scn.fw_group.coll)
    
    def execute(self, context):
        remove_lens_flare(context)
        return {'FINISHED'}
    
# Remove all Lens Flares
class FLARESWIZARD_OT_remove_flares(Operator):
    bl_idname = "flares_wizard.remove_flares"
    bl_label = "Remove All"
    bl_description = "Remove all the Lens Flares"
    
    @classmethod
    def poll(self, context):
        scn = context.scene
        if not hasattr(scn, 'fw_group'):
            return False
        return len(scn.fw_group.coll)
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.separator()
        message = 'Remove all the Lens Flares?'
        layout.label(text = message, icon = 'QUESTION')        
        layout.separator()        
        
    def execute(self, context):
        while len(context.scene.fw_group.coll):
            context.scene.fw_group.index = 0
            remove_lens_flare(context)
        return {'FINISHED'}
    
# Move the selected Flare
class FLARESWIZARD_OT_move_lens_flare(Operator):
    bl_idname = "flares_wizard.move_lens_flare"
    bl_label = "Move"
    bl_options = {'UNDO'}
    bl_description = "Move the selected Lens Flare"
    
    direction : StringProperty(name = 'Direction')
    
    @classmethod
    def poll(self, context):
        scn = context.scene
        if not hasattr(scn, 'fw_group'):
            return False
        return len(scn.fw_group.coll)
    
    def execute(self, context):
        scn = context.scene
        coll, index = flares_coll(context)
        
        if self.direction == 'UP':
            if index > 0:
                coll.move(index, index-1)
                scn.fw_group.index -= 1
        elif self.direction == 'DOWN':
            if index < len(coll)-1:
                coll.move(index, index+1)
                scn.fw_group.index += 1
        return {'FINISHED'}
    
# Duplicate the selected Flare
class FLARESWIZARD_OT_duplicate_flare(Operator):
    bl_idname = "flares_wizard.duplicate_flare"
    bl_label = "Duplicate"
    bl_options = {'UNDO'}
    bl_description = "Duplicate the selected Lens Flare"
    
    @classmethod
    def poll(self, context):
        scn = context.scene
        if not hasattr(scn, 'fw_group'):
            return False
        return len(scn.fw_group.coll)
    
    def execute(self, context):
        flare = active_flare(context)
        duplicate_flare(context, flare)
        return {'FINISHED'}
    
# Flares Visibility
class FLARESWIZARD_OT_flares_visibility(Operator):
    bl_idname = "flares_wizard.flares_visibility"
    bl_label = "Visibility"
    bl_options = {'UNDO'}
    bl_description = "Visibility of the Lens Flares"
    
    action : StringProperty()
    
    @classmethod
    def poll(self, context):
        scn = context.scene
        if not hasattr(scn, 'fw_group'):
            return False
        return len(scn.fw_group.coll)
    
    def execute(self, context):
        coll, index = flares_coll(context)
        count = len(coll)
        active = coll[index]
        visiblity = self.action != 'ENABLE'
        for flare in coll:
            flare.hide = visiblity
        if self.action == 'SOLO':
            active.hide = False
        coll.update()
        return {'FINISHED'}

########################## Elements ###########################
# Elements Browser
class FLARESWIZARD_OT_elements_browser(Operator):
    bl_idname = "flares_wizard.elements_browser"
    bl_label = "Add an Element"
    bl_options = {'UNDO'}
    bl_description = "Add a new Element"
    
    @classmethod
    def poll(self, context):
        scn = context.scene
        if not hasattr(scn, 'fw_group'):
            return False
        return len(scn.fw_group.coll)
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=560)
    
    def draw(self, context):
        pcoll = preview_collections["icons"]
        layout = self.layout
        grid = self.layout.grid_flow(row_major=True, columns=5, even_columns=True, even_rows=True)
        elements = [i.capitalize() for i in props.elements]
        for p in elements:
            icon_id = get_custom_icon_id(pcoll, p)
            col = grid.column(align=True)
            box = col.box()
            box.template_icon(icon_value = icon_id, scale=5.0)
            col.operator("flares_wizard.add_element",text = p, icon='ADD').type = p.upper()
            col.separator()
            col.separator()
    def execute(self, context):
        return {'FINISHED'}

# Add an Element
class FLARESWIZARD_OT_add_element(Operator):
    bl_idname = "flares_wizard.add_element"
    bl_label = "Add an Element"
    bl_options = {'UNDO'}
    bl_description = "Add This Element"
    
    type : StringProperty()
    
    @classmethod
    def poll(self, context):
        scn = context.scene
        if not hasattr(scn, 'fw_group'):
            return False
        return len(scn.fw_group.coll)
    
    def execute(self, context):
        flare = active_flare(context)
        ele_type = self.type.upper()
        element = add_element(context, flare, ele_type)
        if element.type == 'IMAGE':
            set_image(flare, element, 'Glow.jpg')
        elif element.type == 'LENS_DIRT':
            set_image(flare, element, 'Lens_Dirt_1.png')    
        elif element.type == 'GHOSTS':
            set_image(flare, element, 'Poly_hexagon_smt1.png')
            
        return {'FINISHED'}
    
# Remove LF Element
class FLARESWIZARD_OT_remove_element(Operator):
    bl_idname = "flares_wizard.remove_element"
    bl_label = "Remove Element"
    bl_options = {'UNDO'}
    bl_description = "Remove the selected Element"
    
    @classmethod
    def poll(self, context):
        scn = context.scene
        if not hasattr(scn, 'fw_group'):
            return False
        flare = active_flare(context)
        if flare is None:
            return False
        return len(flare.elements)
    
    def execute(self, context):
        remove_element(context)
        return {'FINISHED'}
    
# Remove all Elements
class FLARESWIZARD_OT_remove_elements(Operator):
    bl_idname = "flares_wizard.remove_elements"
    bl_label = "Remove All"
    bl_description = "Remove all the Elements"
    
    @classmethod
    def poll(self, context):
        scn = context.scene
        if not hasattr(scn, 'fw_group'):
            return False
        flare = active_flare(context)
        if flare is None:
            return False
        return len(flare.elements)
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.separator()
        message = 'Remove all the Elements?'
        layout.label(text = message, icon = 'QUESTION')        
        layout.separator()
        
    def execute(self, context):
        remove_elements(context)
        return {'FINISHED'}
    
# Move the selected Element
class FLARESWIZARD_OT_move_element(Operator):
    bl_idname = "flares_wizard.move_element"
    bl_label = "Move"
    bl_options = {'UNDO'}
    bl_description = "Move the selected Element"
    
    direction : StringProperty(name = 'Direction')
    
    @classmethod
    def poll(self, context):
        scn = context.scene
        if not hasattr(scn, 'fw_group'):
            return False
        flare = active_flare(context)
        if flare is None:
            return False
        return len(flare.elements)
    
    def execute(self, context):
        flare = active_flare(context)
        elements = flare.elements
        ele_index = flare.ele_index
        
        if self.direction == 'UP':
            if ele_index > 0:
                elements.move(ele_index, ele_index-1)
                flare.ele_index -= 1
        elif self.direction == 'DOWN':
            if ele_index < len(elements)-1:
                elements.move(ele_index, ele_index+1)
                flare.ele_index += 1
        return {'FINISHED'}
    
# Duplicate the selected Element
class FLARESWIZARD_OT_duplicate_element(Operator):
    bl_idname = "flares_wizard.duplicate_element"
    bl_label = "Duplicate"
    bl_options = {'UNDO'}
    bl_description = "Duplicate the selected Element"
    
    @classmethod
    def poll(self, context):
        scn = context.scene
        if not hasattr(scn, 'fw_group'):
            return False
        flare = active_flare(context)
        if flare is None:
            return False
        return len(flare.elements)
    
    def execute(self, context):
        flare = active_flare(context)
        elements = flare.elements
        ele_index = flare.ele_index
        element = elements[ele_index]
        duplicate_element(context, flare, element)
        return {'FINISHED'}

# Elements Visibility
class FLARESWIZARD_OT_elements_visibility(Operator):
    bl_idname = "flares_wizard.elements_visibility"
    bl_label = "Visibility"
    bl_options = {'UNDO'}
    bl_description = "Visibility of the Elements"
    
    action : StringProperty()
    
    @classmethod
    def poll(self, context):
        scn = context.scene
        if not hasattr(scn, 'fw_group'):
            return False
        flare = active_flare(context)
        if flare is None:
            return False
        return len(flare.elements)
    
    def execute(self, context):
        flare = active_flare(context)
        elements = flare.elements
        ele_index = flare.ele_index
        active = elements[ele_index]
        visiblity = self.action != 'ENABLE'
        for e in elements:
            e.hide = visiblity
        if self.action == 'SOLO':
            active.hide = False
        elements.update()
        return {'FINISHED'}

########################## Open Image ###########################
    
# Open Image
class FLARESWIZARD_OT_open_image(Operator):
    bl_idname = "flares_wizard.open_image"
    bl_label = "Open Image"
    bl_description = "Open Image"
    
    filepath : StringProperty(subtype="FILE_PATH")
    type : StringProperty()
        
    def execute(self, context):
        if not self.type in ['BG', 'ELEMENT']:
            return {'CANCELLED'}
        scn = context.scene
        image = None
        images =  bpy.data.images
        filename, file_extension = os.path.splitext(self.filepath)
        img_name = os.path.basename(self.filepath)
        
        extensions = ['.png', '.jpg', '.jpeg', '.bmp',
                      '.targa', '.avi', '.mp4', '.ogg',
                      '.flv', '.mov', '.mpeg', '.wmv',
                      '.exr', '.hdr', '.cin', '.webp',
                      '.tga', '.tif', '.dpx']
        
        if file_extension.lower() not in extensions:
            self.report({'WARNING'}, 'The selected file is not a compatible image file.')
            return {'CANCELLED'}
            
        image = images.get(img_name)
        if not image:
            image = images.load(self.filepath)
            
        if self.type == 'BG':
            mat = scn.fw_group.get('bg_material')
            if not mat:
                return {'CANCELLED'}
            img_node = mat.node_tree.nodes.get('Image Texture')
            if not img_node:
                self.report({'WARNING'}, 'Image Node Not Found!.')
                return {'CANCELLED'}
            img_node.image = image
            return {'FINISHED'}
            
        coll, index  = flares_coll(context)
        ele = coll[index].elements
        ele_index = coll[index].ele_index
        element = ele[ele_index]
        element.image = image
        return {'FINISHED'}
    
    def invoke(self, context, event):
        self.filepath = textures_folder + os.sep
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
########################## Presets ###########################

# Presets Browser
class FLARESWIZARD_OT_presets_browser(Operator):
    bl_idname = "flares_wizard.presets_browser"
    bl_label = "Add a Lens Flare"
    bl_options = {'UNDO'}
    bl_description = "Add a new Lens Flare"
    
    @classmethod
    def poll(self, context):
        cam = context.scene.camera
        if not hasattr(cam, 'type') or cam.type != 'CAMERA':
            return False
        return is_ready(context)
    
    def invoke(self, context, event):
        preferences = prefs(context)
        thumb_size = preferences.thumb_size
        columns_count = preferences.columns_count
        preferences.page_number = 1
        preferences.presets_filter = ''
        genterate_presets_previews(context)
        width = 74 + ((int(thumb_size)-3)*20)
        width *= columns_count
        return context.window_manager.invoke_props_dialog(self, width=width)
    
    def draw(self, context):
        preferences = prefs(context)
        layout = self.layout
        box = layout.box()
        row = box.row(align = True)
        row.operator("flares_wizard.add_lens_flare", icon = "SNAP_FACE")
        row.separator()
        row.prop(preferences, 'targets', text = '')
        row.separator()
        row.prop(preferences, 'builtin_presets', text = '', icon = 'EVENT_B')
        row.prop(preferences, 'custom_presets', text = '', icon = 'EVENT_C')
        row.prop(preferences, 'presets_filter', text = '', icon = 'VIEWZOOM')
        box = layout.box()
        draw_grid_items(context, box)
        box = layout.box()
        row = box.row(align = True)
        row.alignment = 'CENTER'
        row.operator("flares_wizard.previous_page", text = "", icon = "PLAY_REVERSE", emboss = False)
        text = 'Page ' + str(preferences.page_number) + '/' + str(calc_pages_count(context))
        row.label(text = text)
        row.operator("flares_wizard.next_page", text = "", icon = "PLAY", emboss = False)
    def execute(self, context):
        return {'FINISHED'}

# Save the selected Flare as a preset
class FLARESWIZARD_OT_save_flare(Operator):
    bl_idname = "flares_wizard.save_flare"
    bl_label = "Save"
    bl_options = {'UNDO'}
    bl_description = "Save the selected Lens Flare as a Preset"
    
    name : StringProperty(
        name = 'Name',
        default = 'My Preset',
        description = 'Name of the new preset',
    )
    
    @classmethod
    def poll(self, context):
        scn = context.scene
        if not hasattr(scn, 'fw_group'):
            return False
        return len(scn.fw_group.coll)
    
    def invoke(self, context, event):
        flare = active_flare(context)
        name = bpy.path.clean_name(flare.ui_name)
        presets = get_custom_presets(context)
        presets = [i[2:] for i in presets]
        self.name = get_prop_name(name, presets)
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        col = layout.column()
        
        custom_folder = custom_presets_dir(context)
        if custom_folder is None:
            box = layout.box()
            preferences = prefs(context)
            box.label(text = 'You need to select the presets folder first', icon = 'INFO')
            box.label(text = 'Or you can set it up from the preferences', icon = 'BLANK1')
            box.prop(preferences, 'presets_path', text = '')
            return
        name = bpy.path.clean_name(self.name)
        presets = [i[2:].lower() for i in get_custom_presets(context)]
        col.alert = name.lower() in presets or not name.strip()
        col.label(text = 'Name of the new Preset')
        col.prop(self, 'name', text = '')
        if name.lower() in presets:
            col = layout.column()
            msg = 'The name "' + name + '" already exists!'
            col.label(text = msg, icon = 'ERROR')
            col.label(text = 'Press OK if you want to overide the preset.', icon = 'INFO')
        
    def execute(self, context):
        folder = custom_presets_dir(context)
        if folder is None:
            self.report({'WARNING'}, 'Custom presets folder not found')
            return {'CANCELLED'}
        custom_presets_folder = os.path.join(folder, 'Presets')
        custom_previews_folder = os.path.join(folder, 'Previews')
        for i in [custom_presets_folder, custom_previews_folder]:
            if not os.path.exists(i):
                try:
                    os.makedirs(i)
                except Exception as e:
                    self.report({'WARNING'}, "Can't create the folder: "+i+' '+str(e))
                    return {'CANCELLED'}
                
        name = bpy.path.clean_name(self.name)
        if not name.strip():
            self.report({'WARNING'}, 'Wrong name')
            return {'CANCELLED'}
        
        flare = active_flare(context)
        file_path = os.path.join(custom_presets_folder, name+'.lf')
        save_preset(flare, file_path)
        
        with open(preset_to_render, 'w') as p:
            p.write(name)
            
        render_preview()
        
        if os.path.exists(file_path):
            self.report({'INFO'}, name+ ' : Saved Successfully!')
        else:
            self.report({'WARNING'}, 'Something Went Wrong! Preset Not Saved')
        return {'FINISHED'}
    
# Load a preset
class FLARESWIZARD_OT_load_flare(Operator):
    bl_idname = "flares_wizard.load_flare"
    bl_label = "Load"
    bl_options = {'UNDO'}
    bl_description = ("Load this Preset.\n"
    "Hold the Ctrl key to replace the selected Lens Flare")
    
    file_path : StringProperty()
    
    @classmethod
    def poll(self, context):
        return is_ready(context)
    
    def invoke(self, context, event):
        targets, targets_type = get_targets(context)
        coll, index = flares_coll(context)
        if event.ctrl and len(coll):
            remove_elements(context)
            flare = coll[index]
        else:
            flare = add_lens_flare(context, targets, targets_type)
        load_preset(context, flare, self.file_path)
        return {'FINISHED'}
    
# Load a preset in the background
class FLARESWIZARD_OT_load_flare_bg(Operator):
    bl_idname = "flares_wizard.load_flare_bg"
    bl_label = "Load"
    bl_options = {'UNDO'}
    bl_description = "Load this Preset"    
    
    file_path : StringProperty()
    
    @classmethod
    def poll(self, context):
        return is_ready(context)
    
    def execute(self, context):
        targets = context.object
        flare = add_lens_flare(context, targets, 'OBJECT')
        load_preset(context, flare, self.file_path)
        return {'FINISHED'}
    
# Next Page
class FLARESWIZARD_OT_next_page(Operator):
    bl_idname = "flares_wizard.next_page"
    bl_label = "Next Page"
    bl_options = {'UNDO'}
    bl_description = "Next Page"
    
    @classmethod
    def poll(self, context):
        if not is_ready(context):
            return False
        pages_count = calc_pages_count(context)
        preferences = prefs(context)
        return pages_count > preferences.page_number
    
    def execute(self, context):
        preferences = prefs(context)
        preferences.page_number += 1
        return {'FINISHED'}
    
    
# Previous Page
class FLARESWIZARD_OT_previous_page(Operator):
    bl_idname = "flares_wizard.previous_page"
    bl_label = "Previous Page"
    bl_options = {'UNDO'}
    bl_description = "Previous Page"
    
    @classmethod
    def poll(self, context):
        if not is_ready(context):
            return False
        preferences = prefs(context)
        return preferences.page_number != 1
    
    def execute(self, context):
        preferences = prefs(context)
        preferences.page_number -= 1
        return {'FINISHED'}
    
# Delete a preset
class FLARESWIZARD_OT_delete_preset(Operator):
    bl_idname = "flares_wizard.delete_preset"
    bl_label = "Delete"
    bl_options = {'UNDO'}
    bl_description = "Delete this preset"
    
    preset : StringProperty()
    
    @classmethod
    def poll(self, context):
        return is_ready(context)
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        preset = self.preset[2:]
        layout = self.layout
        layout.separator()
        message = 'Delete the preset: ' + preset + '?'
        layout.label(text = message, icon = 'QUESTION')        
        layout.separator()
    
    def execute(self, context):
        scn = context.scene
        if self.preset.startswith('C_'):
            custom_folder = custom_presets_dir(context)
            presets = os.path.join(custom_folder, 'Presets')
            previews = os.path.join(custom_folder, 'Previews')
        elif self.preset.startswith('B_'):
            presets = presets_folder
            previews = previews_folder
        
        files = []    
        preset = self.preset[2:]
        preset_file = os.path.join(presets, preset+'.lf')
        if not os.path.exists(preset_file):
            self.report({'WARNING'}, "File doesn't exist")
        else:
            files.append(preset_file)
            
        preset_thumb = os.path.join(previews, preset+'.png')
        if not os.path.exists(preset_thumb):
            self.report({'WARNING'}, "Thumbnail doesn't exist")
        else:
            files.append(preset_thumb)
        
        for i in files:
            try:
                os.remove(i)
            except Exception as e:
                self.report({'WARNING'}, str(e))
                continue
        preferences = prefs(context)
        preferences.page_number = 1
        return {'FINISHED'}
    
##################################### Background Plane #####################################
# Add Background Plane
class FLARESWIZARD_OT_add_background(Operator):
    bl_idname = "flares_wizard.add_background"
    bl_label = "Add Background Plane"
    bl_options = {'UNDO'}
    bl_description = "Add The Background Plane"
    
    @classmethod
    def poll(self, context):
        if not is_ready(context):
            return False
        return context.scene.camera is not None
        
    def execute(self, context):
        engine = context.scene.render.engine
        if not engine in ['CYCLES', 'BLENDER_EEVEE_NEXT']:
            context.scene.render.engine = 'BLENDER_EEVEE_NEXT'
        create_bg(context)
        return {'FINISHED'}
    
# Delete Background Plane
class FLARESWIZARD_OT_delete_background(Operator):
    bl_idname = "flares_wizard.delete_background"
    bl_label = "Delete Background"
    bl_options = {'UNDO'}
    bl_description = "Delete Background"
        
    def execute(self, context):
        scn = context.scene
        collections = bpy.data.collections
        # Remove the plane
        plane = scn.fw_group.get('bg_plane')
        if plane is not None:
            mesh = plane.data
            if not mesh.users:
                bpy.data.meshes.remove(mesh)
            bpy.data.objects.remove(plane)
        # Remove the collection    
        coll = scn.fw_group.get('bg_collection')
        if coll is not None:
            if not len(coll.all_objects):
                collections.remove(coll)
        # Remove the material
        mat = scn.fw_group.get('bg_material')
        if mat is not None:
            bpy.data.materials.remove(mat)
        return {'FINISHED'}
    
# BG Set Scene Resolution
class FLARESWIZARD_OT_set_scene_resolution(Operator):
    bl_idname = "flares_wizard.set_scene_resolution"
    bl_label = "Set Scene Resolution"
    bl_options = {'UNDO'}
    bl_description = "Match the Scene resolution with the Image resolution"
        
    def execute(self, context):
        mat = context.scene.fw_group.get('bg_material')
        if mat is None:
            self.report({'WARNING'}, 'Metarial Not Found!')
            return {'CANCELLED'}
            
        nodes = mat.node_tree.nodes
        x, y = nodes['Image Texture'].image.size[:]
        context.scene.render.resolution_x = x
        context.scene.render.resolution_y = y
        return {'FINISHED'}
    
# BG Set movie length
class FLARESWIZARD_OT_set_movie_length(Operator):
    bl_idname = "flares_wizard.set_movie_length"
    bl_label = "Set Movie Length"
    bl_options = {'UNDO'}
    bl_description = "Set Movie Length"
        
    def execute(self, context):
        mat = context.scene.fw_group.get('bg_material')
        if mat is None:
            self.report({'WARNING'}, 'Metarial Not Found!')
            return {'CANCELLED'}
        
        nodes = mat.node_tree.nodes
        img = nodes['Image Texture'].image
        img_user = nodes['Image Texture'].image_user
        img_user.frame_duration = img.frame_duration
        return {'FINISHED'}
    
########################## Compositing ###########################
# Setup View Layers
class FLARESWIZARD_OT_setup_view_layers(Operator):
    bl_idname = "flares_wizard.setup_view_layers"
    bl_label = "Setup View Layers"
    bl_options = {'UNDO'}
    bl_description = "Setup the View Layers for compositing"
    
    @classmethod
    def poll(self, context):
        return is_ready(context)
        
    def execute(self, context):
        setup_view_layers(context)
        return {'FINISHED'}
    
# Remove View Layer
class FLARESWIZARD_OT_remove_view_layer(Operator):
    bl_idname = "flares_wizard.remove_view_layer"
    bl_label = "Remove View Layer"
    bl_options = {'UNDO'}
    bl_description = "Remove the Lens Flares View Layer"
    
    @classmethod
    def poll(self, context):
        return is_ready(context)
        
    def execute(self, context):
        remove_view_layer(context)
        return {'FINISHED'}
    
# Setup AOVs
class FLARESWIZARD_OT_setup_aovs(Operator):
    bl_idname = "flares_wizard.setup_aovs"
    bl_label = "Setup AOVs"
    bl_options = {'UNDO'}
    bl_description = "Setup the AOVs for the Lens Flares Shaders"
    
    @classmethod
    def poll(self, context):
        if not is_ready(context):
            return False
        scn = context.scene
        return len(scn.fw_group.coll)
        
    def execute(self, context):
        setup_aovs(context)
        return {'FINISHED'}
    
# Remove AOVs
class FLARESWIZARD_OT_remove_aovs(Operator):
    bl_idname = "flares_wizard.remove_aovs"
    bl_label = "Remove AOVs"
    bl_options = {'UNDO'}
    bl_description = "Remove the AOVs of the Lens Flares Shaders"
    
    @classmethod
    def poll(self, context):
        if not is_ready(context):
            return False
        scn = context.scene
        return len(scn.fw_group.coll)
        
    def execute(self, context):
        remove_aovs(context)
        return {'FINISHED'}
    
######################################## Opening Links #####################################
# Open a file, from this answer in stackoverflow
# https://stackoverflow.com/a/17317468
def open_file(filename):
    if platform == "win32":
        os.startfile(filename)
    else:
        opener = "open" if platform == "darwin" else "xdg-open"
        call([opener, filename])

# Open the manual
class FLARESWIZARD_OT_open_manual(Operator):
    bl_idname = "flares_wizard.open_manual"
    bl_label = "The Manual"
    bl_description = "Open The Manual"
        
    def execute(self, context):
        manual_dir = os.path.join(addon_folder, "Manual.pdf")
        if not os.path.exists(manual_dir):
            self.report({'WARNING'}, 'Manual file not found')
            return {'CANCELLED'}
        open_file(manual_dir)
        return {'FINISHED'}
    
# Open YT Playlist of tutorials
class FLARESWIZARD_OT_yt_playlist(Operator):
    bl_idname = "flares_wizard.video_tuts"
    bl_label = "Video Tutorials"
    bl_description = "Open a playlist of video tutorials on YouTube"
        
    def execute(self, context):
        url = 'https://youtube.com/playlist?list=PLHQA94bJq143SFkiqxgdKcNABoXA2F8Qv'
        bpy.ops.wm.url_open(url = url)
        return {'FINISHED'}
    
# Open a folder
class FLARESWIZARD_OT_open_folder(Operator):
    bl_idname = "flares_wizard.open_folder"
    bl_label = "Open a folder"
    bl_description = "Open a folder"
    
    filepath : StringProperty()
        
    def execute(self, context):
        if not os.path.exists(self.filepath):
            self.report({'WARNING'}, 'Folder not found')
            return {'CANCELLED'}
        open_file(self.filepath)
        return {'FINISHED'}
    
############################################################################################
####################################### The UI #############################################
############################################################################################

# UI list for the Flares
class FLARESWIZARD_UL_flares(UIList):
   def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
       row = layout.row()       
       row.prop(item, "ui_name", text="", emboss=False, icon = 'LIGHT_SUN')
       row = layout.row()
       icon = 'HIDE_ON' if item.hide else 'HIDE_OFF'
       row.alignment = 'RIGHT'
       row.prop(item, "hide", text="", icon = icon, emboss=False)
       
# UI list for the Elements
class FLARESWIZARD_UL_elements(UIList):
   def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
       pcoll = preview_collections["icons"]
       ele_type = item.type
       icon = 'HIDE_ON' if item.hide else 'HIDE_OFF'
       row = layout.row()
       icon_id = get_custom_icon_id(pcoll, item.type.capitalize())
       row.prop(item, "ui_name", text="", emboss=False, icon_value = icon_id)
       row.prop(item, "hide", text="", icon = icon, emboss=False)
       
# Special menu Lens Flare Options
class LensFlareOptions(Menu):
    bl_idname = "FLARESWIZARD_MT_lf_options"
    bl_label = "Options"
    bl_description = "Options"
    
    def draw(self, context):
        layout = self.layout
        layout.label(text='Options', icon = 'TOOL_SETTINGS')
        layout.separator()
        layout.operator("flares_wizard.flares_visibility", text='Show All', icon = 'HIDE_OFF').action = 'ENABLE'
        layout.operator("flares_wizard.flares_visibility", text='Hide All', icon = 'HIDE_ON').action = 'DISABLE'
        layout.operator("flares_wizard.flares_visibility", text='Solo Selected', icon = 'VIS_SEL_11').action = 'SOLO'
        layout.separator()
        layout.operator("flares_wizard.duplicate_flare", icon='DUPLICATE')
        layout.separator()
        layout.operator("flares_wizard.save_flare", icon='EXPORT')
        layout.separator()
        layout.operator("flares_wizard.remove_flares", icon='TRASH')
        
# Special menu Elements Options
class ElementsOptions(Menu):
    bl_idname = "FLARESWIZARD_MT_elements_options"
    bl_label = "Options"
    bl_description = "Options"

    def draw(self, context):
        layout = self.layout
        layout.label(text='Options', icon = 'TOOL_SETTINGS')
        layout.separator()
        layout.operator("flares_wizard.elements_visibility", text='Show All', icon = 'HIDE_OFF').action = 'ENABLE'
        layout.operator("flares_wizard.elements_visibility", text='Hide All', icon = 'HIDE_ON').action = 'DISABLE'
        layout.operator("flares_wizard.elements_visibility", text='Solo Selected', icon = 'VIS_SEL_11').action = 'SOLO'
        layout.separator()
        layout.operator("flares_wizard.duplicate_element", icon='DUPLICATE')
        layout.separator()
        layout.operator("flares_wizard.remove_elements", icon='TRASH')
        
# Special menu Shortcuts
class FLARESWIZARD_shortcuts(Menu):
    bl_idname = "FLARESWIZARD_MT_shortcuts"
    bl_label = "Shortcuts"
    bl_description = "Shortcuts"

    def draw(self, context):
        layout = self.layout
        layout.label(text='Shortcuts', icon = 'FOLDER_REDIRECT')
        layout.separator()
        layout.operator("flares_wizard.open_folder", text='Open Textures Folder', icon = 'NODE_COMPOSITING').filepath = textures_folder
        layout.operator("flares_wizard.open_folder", text='Open Thumbnails Folder', icon = 'IMAGE_PLANE').filepath = previews_folder
        layout.operator("flares_wizard.open_folder", text='Open Presets Folder', icon = 'DOCUMENTS').filepath = presets_folder
        layout.operator("flares_wizard.open_manual", icon = 'TEXT')
        
# Extra LF Options Panel
class FLARESWIZARD_PT_extra_options(Panel):
    bl_label = "Extra Options"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Lens Flares"
    bl_options = {"DEFAULT_CLOSED"}
    
    @classmethod
    def poll(self, context):
        return is_ready(context)
    
    def draw(self, context):
        layout = self.layout
        layout.menu('FLARESWIZARD_MT_shortcuts', text='Shortcuts')
        
# Flare Planes Panel
class FLARESWIZARD_PT_flare_planes(Panel):
    bl_label = "Lens Flare Planes"
    bl_parent_id = "FLARESWIZARD_PT_extra_options"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Lens Flares"
    bl_options = {"DEFAULT_CLOSED"}
    
    def draw(self, context):
        layout = self.layout
        fw_group = context.scene.fw_group
        layout.prop(fw_group, 'global_offset')
        layout.prop(fw_group, 'relative_offset')
        layout.prop(fw_group, 'planes_margin')
        
# Background Panel
class FLARESWIZARD_PT_background(Panel):
    bl_label = "Background Plane"
    bl_parent_id = "FLARESWIZARD_PT_extra_options"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Lens Flares"
    bl_options = {"DEFAULT_CLOSED"}
    
    def draw(self, context):
        layout = self.layout
        scn = context.scene
        plane = scn.fw_group.get('bg_plane')
        if plane is None:
            layout.operator("flares_wizard.add_background", icon = 'IMAGE_BACKGROUND')
            return
        
        if not scn.objects.get(plane.name):
            layout.operator("flares_wizard.add_background", icon = 'IMAGE_BACKGROUND')
            return
        
        slots = plane.material_slots
        if not len(slots):
            layout.operator("flares_wizard.delete_background", text = 'Delete BG', icon = 'TRASH')
            return
        
        layout.prop(scn.fw_group, 'bg_camera')
        layout.prop(plane, 'hide_viewport', text = 'Viewport Visibility')
        layout.prop(plane, 'hide_render', text = 'Render Visibility')
        mat = plane.material_slots[0].material
        nodes = mat.node_tree.nodes
        layout.prop(scn.fw_group, 'bg_z_offset')
        layout.prop(scn.fw_group, 'bg_opacity')
        
        img = nodes.get('Image Texture')
        if img is None:
            if not len(slots):
                layout.operator("flares_wizard.delete_background", icon = 'TRASH')
                return
        row = layout.row(align = True)
        row.prop(img, 'image', text = '')
        row.operator("flares_wizard.open_image", text = "", icon = "FILEBROWSER").type = 'BG'
        if img.image:
            layout.operator('flares_wizard.set_scene_resolution')
            if img.image.source == 'MOVIE':
                image = img.image_user
                col = layout.column(align = True)
                col.prop(image, 'frame_duration')
                col.prop(image, 'frame_start')
                col.prop(image, 'frame_offset')
                col = layout.column()
                col.prop(image, 'use_cyclic')
                col.prop(image, 'use_auto_refresh')
                col.operator('flares_wizard.set_movie_length')
                    
        layout.operator("flares_wizard.delete_background", icon = 'TRASH')
        
        
# Compositing Panel
class FLARESWIZARD_PT_compositing(Panel):
    bl_label = "Compositing"
    bl_parent_id = "FLARESWIZARD_PT_extra_options"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Lens Flares"
    bl_options = {"DEFAULT_CLOSED"}
    
    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.label(text = 'View Layers')
        box.operator("flares_wizard.setup_view_layers", icon = 'RENDERLAYERS')
        box.operator("flares_wizard.remove_view_layer", icon = 'TRASH')
        box = layout.box()
        box.label(text = 'AOVs')
        box2 = box.box()
        box2.label(text = 'Cycles Only', icon = 'INFO')
        box.operator("flares_wizard.setup_aovs", icon = 'SHADING_TEXTURE')
        box.operator("flares_wizard.remove_aovs", icon = 'TRASH')
       
# Lens Flares Panel
class FLARESWIZARD_PT_lens_flares(Panel):
    bl_label = "Lens Flares"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Lens Flares"
        
    def draw(self, context):
        scn = context.scene
        layout = self.layout
        
        if bpy.app.version < (4, 2, 0):
            box = layout.box()
            box.alert = True
            box.label(text = 'Works with Blender 4.2 and above.', icon = 'ERROR')
            return
        
        if not hasattr(scn, 'fw_group'):
            layout.operator("flares_wizard.load_props", icon='IMPORT')
            return
        
        engine = context.scene.render.engine
        if not engine in ['CYCLES', 'BLENDER_EEVEE_NEXT']:
            box = layout.box()
            box.label(text = "The add-on doesn't work with", icon = 'INFO')
            box.label(text = "the selected render engine", icon = 'BLANK1')
            return
        
        paths = context.preferences.filepaths
        if not paths.use_scripts_auto_execute:
            box = layout.box()
            box.label(text = "Auto Run Python Scripts is disabled", icon = 'ERROR')
            box.label(text = "It's necessary for the add-on", icon = 'BLANK1')
            box.prop(paths, 'use_scripts_auto_execute', icon='SCRIPT', text = 'Enable')
            return
        
        if not hasattr(scn.camera, 'type') or scn.camera.type != 'CAMERA':
            box = layout.box()
            box.alert = True
            box.label(text = 'No Active Camera', icon = 'ERROR')
            
        coll, index = flares_coll(context)
        
        row = layout.row()
        row.template_list("FLARESWIZARD_UL_flares", "coll", scn.fw_group, "coll", scn.fw_group, "index", rows = 5)
        col = row.column(align=True)
        col.operator("flares_wizard.presets_browser", icon='ADD', text = '')
        col.operator("flares_wizard.remove_lens_flare", icon='REMOVE', text = '')
        col.separator()
        col.menu("FLARESWIZARD_MT_lf_options", text = '', icon = 'DOWNARROW_HLT')
        col.separator()
        col.operator("flares_wizard.move_lens_flare", text = '', icon = 'TRIA_UP').direction = 'UP'
        col.operator("flares_wizard.move_lens_flare", text = '', icon = 'TRIA_DOWN').direction = 'DOWN'

# General Settings Panel
class FLARESWIZARD_PT_general_settings(Panel):
    bl_label = "General Settings"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Lens Flares"
    bl_parent_id = "FLARESWIZARD_PT_lens_flares"
    bl_options = {"DEFAULT_CLOSED"}
    
    @classmethod
    def poll(self, context):
        scn = context.scene
        if not hasattr(scn, 'fw_group'):
            return False
        if not len(scn.fw_group.coll):
            return False
        return is_ready(context)
    
    def draw(self, context):
        scn = context.scene
        layout = self.layout
        layout.use_property_split = True
        coll, index = flares_coll(context)
        flare = coll[index]
        col = layout.column(align = True)
        col.prop(flare, 'target_type')
        if flare.target_type == 'OBJECT':
            col.alert = not hasattr(flare.target_object, 'name')
            col.prop(flare, 'target_object')
            col.prop(flare, 'use_geo_data')
        else:
            col.alert = not hasattr(flare.target_collection, 'name')
            col.prop(flare, 'target_collection')
        col = layout.column()
        col.prop(flare, 'color')
        col.prop(flare, 'scale')
        col.prop(flare, 'intensity')
        col = layout.column(align = True)
        col.prop(flare, 'detect_borders', icon = 'OUTLINER_OB_CAMERA')
        if flare.detect_borders:
            col.prop(flare, 'border_distance')
        col = layout.column(align = True)
        col.prop(flare, 'in_3d_space', slider = True)
        if flare.in_3d_space:
            col.prop(flare, 'corrective_scale')

# Instances Panel
class FLARESWIZARD_PT_instances(Panel):
    bl_label = "Instances"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Lens Flares"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = "FLARESWIZARD_PT_lens_flares"
    
    @classmethod
    def poll(self, context):
        scn = context.scene
        if not hasattr(scn, 'fw_group'):
            return False
        coll, index = flares_coll(context)
        if not len(coll):
            return False
        flare = coll[index]
        if flare.target_type == 'OBJECT':
            if not flare.use_geo_data:
                return False
        return is_ready(context)
    
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        coll, index = flares_coll(context)
        flare = coll[index]
        layout.prop(flare, 'max_instances')
        layout.prop(flare, 'max_distance')
        
        box = layout.box()
        col = box.column(align = True)
        col.label(text = 'Color')
        if flare.target_type == 'OBJECT':
            col.prop(flare, 'color_attr')
        col.prop(flare, 'random_color', slider = True)
        col.prop(flare, 'random_color_seed')
        
        box = layout.box()
        col = box.column(align = True)
        col.label(text = 'Intensity')
        if flare.target_type == 'OBJECT':
            col.prop(flare, 'intensity_attr')
        col.prop(flare, 'random_scale', slider = True)
        col.prop(flare, 'random_scale_seed')
        
        box = layout.box()
        col = box.column(align = True)
        col.label(text = 'Scale')
        if flare.target_type == 'OBJECT':
            col.prop(flare, 'scale_attr')
        col.prop(flare, 'random_intensity', slider = True)
        col.prop(flare, 'random_intensity_seed')
            
# Blinking Panel
class FLARESWIZARD_PT_blinking(Panel):
    bl_label = "Blinking"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Lens Flares"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = "FLARESWIZARD_PT_lens_flares"
    
    @classmethod
    def poll(self, context):
        scn = context.scene
        if not hasattr(scn, 'fw_group'):
            return False
        if not len(scn.fw_group.coll):
            return False
        return is_ready(context)
    
    def draw_header(self, context):
        coll, index = flares_coll(context)
        flare = coll[index]
        self.layout.prop(flare, "blink", text="")
    
    def draw(self, context):
        scn = context.scene
        layout = self.layout
        layout.use_property_split = True
        coll, index = flares_coll(context)
        flare = coll[index]
        layout.prop(flare, 'blink_min')
        layout.prop(flare, 'blink_speed')
        layout.prop(flare, 'blink_distortion')
        layout.prop(flare, 'blink_random_seed')
        layout.prop(flare, 'blink_randomize')
            
# Obstacles Panel
class FLARESWIZARD_PT_obstacles(Panel):
    bl_label = "Obstacles Detection"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Lens Flares"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = "FLARESWIZARD_PT_lens_flares"
    
    @classmethod
    def poll(self, context):
        scn = context.scene
        if not hasattr(scn, 'fw_group'):
            return False
        if not len(scn.fw_group.coll):
            return False
        return is_ready(context)
    
    def draw_header(self, context):
        coll, index = flares_coll(context)
        flare = coll[index]
        self.layout.prop(flare, "detect_obstacles", text="")
    
    def draw(self, context):
        scn = context.scene
        layout = self.layout
        layout.use_property_split = True
        coll, index = flares_coll(context)
        flare = coll[index]
        layout.prop(flare, 'obstacles_collection')
        layout.prop(flare, 'obstacles_distance')
        layout.prop(flare, 'obstacles_steps')
        layout.prop(flare, 'obstacles_samples')
        
# Elements Panel
class FLARESWIZARD_PT_elements(Panel):
    bl_label = "Elements"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Lens Flares"
    bl_options = {"DEFAULT_CLOSED"}
    
    @classmethod
    def poll(self, context):
        scn = context.scene
        if not hasattr(scn, 'fw_group'):
            return False
        if not len(scn.fw_group.coll):
            return False
        return is_ready(context)
        
    def draw(self, context):
        scn = context.scene
        layout = self.layout
        coll, index = flares_coll(context)
        flare = coll[index]
        elements = flare.elements
        ele_index = flare.ele_index
                
        row = layout.row()
        row.template_list("FLARESWIZARD_UL_elements", "elements", flare, "elements", flare, "ele_index", rows = 5)
        col = row.column(align=True)
        col.operator("flares_wizard.elements_browser", icon='ADD', text = '')
        col.operator("flares_wizard.remove_element", icon='REMOVE', text = '')
        col.separator()
        col.menu("FLARESWIZARD_MT_elements_options", text = '', icon = 'DOWNARROW_HLT')
        col.separator()
        col.operator("flares_wizard.move_element", text = '', icon = 'TRIA_UP').direction = 'UP'
        col.operator("flares_wizard.move_element", text = '', icon = 'TRIA_DOWN').direction = 'DOWN'

# Elements Shader
class FLARESWIZARD_PT_elements_shader(Panel):
    bl_label = "Shader"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Lens Flares"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = "FLARESWIZARD_PT_elements"
    
    @classmethod
    def poll(self, context):
        scn = context.scene
        if not hasattr(scn, 'fw_group'):
            return False
        coll, index = flares_coll(context)
        if not len(coll):
            return False
        if not is_ready(context):
            return False
        return len(coll[index].elements)
        
    def draw(self, context):
        scn = context.scene
        layout = self.layout
        layout.use_property_split = True
        coll, index = flares_coll(context)
        flare = coll[index]
        elements = flare.elements
        ele_index = flare.ele_index
        element = elements[ele_index]
                
        col  = layout.column()
        col.prop(element, 'use_global_color', slider = True)
        if element.type != 'GHOSTS':
            col.prop(element, "color")
        else:
            color_ramp = get_ghost_color_ramp(flare, element)
            if element.use_global_color < 1.0 and color_ramp:
                box = col.box()
                box.template_color_ramp(color_ramp, "color_ramp", expand=False)
                box.prop(element, 'ghosts_random_col_seed')
        col.prop(element, "intensity")
        if element.type in ["IMAGE", "GHOSTS", "LENS_DIRT"]:
            row  = layout.row(align = True)                        
            row.prop(element, "image")
            row.operator("flares_wizard.open_image", text = "", icon = "FILEBROWSER").type = 'ELEMENT'
            return
        if element.type in ["GLOW", 'STREAKS', 'CAUSTIC']:
            col.prop(element, "light_falloff")
        if element.type in ["SHIMMER", "RING", "HOOP", "GLOW", "STREAKS", "IRIS"]:
            col.prop(element, "interpolation")
        
# Elements Transform
class FLARESWIZARD_PT_elements_transform(Panel):
    bl_label = "Transform"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Lens Flares"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = "FLARESWIZARD_PT_elements"
    
    @classmethod
    def poll(self, context):
        scn = context.scene
        if not hasattr(scn, 'fw_group'):
            return False
        coll, index = flares_coll(context)
        if not len(coll):
            return False
        if not is_ready(context):
            return False
        return len(coll[index].elements)
        
    def draw(self, context):
        scn = context.scene
        layout = self.layout
        layout.use_property_split = True
        coll, index = flares_coll(context)
        flare = coll[index]
        elements = flare.elements
        ele_index = flare.ele_index
        element = elements[ele_index]
        
        col  = layout.column()
        if element.type not in ['CAUSTIC',]:
            col.prop(element, "position")
        if element.type not in ['HOOP', 'CAUSTIC']:
            col  = layout.column(align = True)
            col.prop(element, "location_x")
            col.prop(element, "location_y")
            col  = layout.column(align = True)
            col.prop(element, "lock_x")
            col.prop(element, "lock_y")
            if element.type != 'LENS_DIRT':
                col  = layout.column(align = True)
                col.prop(element, "rotation")
                col.prop(element, "track_target", icon = 'TRACKER')
        col  = layout.column(align = True)
        col.prop(element, "scale_x")
        col.prop(element, "scale_y")
        
# Elements Trigger
class FLARESWIZARD_PT_triggers(Panel):
    bl_label = "Proximity Trigger"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Lens Flares"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = "FLARESWIZARD_PT_elements"
    
    @classmethod
    def poll(self, context):
        scn = context.scene
        if not hasattr(scn, 'fw_group'):
            return False
        coll, index = flares_coll(context)
        if not len(coll):
            return False
        if not is_ready(context):
            return False
        return len(coll[index].elements)
    
    def draw_header(self, context):
        coll, index = flares_coll(context)
        flare = coll[index]
        elements = flare.elements
        ele_index = flare.ele_index
        element = elements[ele_index]
        self.layout.prop(element, "proximity_trigger", text="")
        
    def draw(self, context):
        scn = context.scene
        layout = self.layout
        layout.use_property_split = True
        coll, index = flares_coll(context)
        flare = coll[index]
        elements = flare.elements
        ele_index = flare.ele_index
        element = elements[ele_index]
        
        layout.prop(element, 'proximity_intensity')
        color_ramp = get_proximity_color_ramp(flare, element)
        if color_ramp is not None:
            box = layout.box()
            box.template_color_ramp(color_ramp, "color_ramp", expand=False)
        
        
        
# Elements Special Options
class FLARESWIZARD_PT_special_options(Panel):
    bl_label = "Special Options"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Lens Flares"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = "FLARESWIZARD_PT_elements"
    
    @classmethod
    def poll(self, context):
        scn = context.scene
        if not hasattr(scn, 'fw_group'):
            return False
        coll, index = flares_coll(context)
        if not len(coll):
            return False
        elements = coll[index].elements
        if not len(elements):
            return False
        if not is_ready(context):
            return False
        ele_index = coll[index].ele_index
        return elements[ele_index].type != 'GLOW'
    
    def draw(self, context):
        scn = context.scene
        layout = self.layout
        layout.use_property_split = True
        coll, index = flares_coll(context)
        flare = coll[index]
        elements = flare.elements
        ele_index = flare.ele_index
        element = elements[ele_index]
        
        col  = layout.column()
        if element.type == 'IMAGE':
            col.prop(element, "fade_distance")
            col.prop(element, "feather")
            
        elif element.type == 'GHOSTS':
            col.prop(element, 'ghosts_count')
            col = layout.column(align = True)
            col.prop(element, 'ghosts_distance')
            col.prop(element, 'ghosts_random_distance')
            col = layout.column(align = True)
            col.prop(element, 'ghosts_random_x')
            col.prop(element, 'ghosts_random_y')
            col  = layout.column()
            col.prop(element, 'ghosts_random_loc_seed')
            col = layout.column(align = True)
            col.prop(element, 'random_rot', slider = True)
            col.prop(element, 'random_rot_seed')
            col = layout.column(align = True)
            col.prop(element, 'random_scale', slider = True)
            col.prop(element, 'random_scale_seed')
        elif element.type == 'STREAKS':
            col.prop(element, 'streaks_count')
            col = layout.column(align = True)
            col.prop(element, 'random_rot', slider = True)
            col.prop(element, 'random_rot_seed')
            col = layout.column(align = True)
            col.prop(element, 'random_scale', slider = True)
            col.prop(element, 'random_scale_seed')
        elif element.type in ['RING', 'HOOP']:
            col.prop(element, 'ring_ray_count')
            col = layout.column(align = True)
            col.prop(element, 'ring_ray_length')
            col.prop(element, 'ring_random_length', slider = True)
            col.prop(element, 'ring_length_seed')
            col = layout.column(align = True)
            col.prop(element, 'ring_ray_width', slider = True)
            col.prop(element, 'ring_random_width', slider = True)
            col.prop(element, 'ring_width_seed')
            col = layout.column(align = True)
            col.prop(element, 'use_spectrum', slider = True)
            col.prop(element, 'spectrum_offset')
            col.prop(element, 'spectrum_interpolation')
            col = layout.column(align = True)
            col.prop(element, 'circular_completion', slider = True)
            col.prop(element, 'completion_feather', slider = True)
            col = layout.column(align = True)
            col.prop(element, 'distortion')
            col.prop(element, 'noise_scale')
        elif element.type == 'SHIMMER':
            col.prop(element, 'shimmer_complexity')
            col.prop(element, 'shimmer_width')
            col.prop(element, 'shimmer_speed')
            col = layout.column(align = True)
            col.prop(element, 'shimmer_length', slider = True)
            col.prop(element, 'shimmer_length_seed')
            col = layout.column(align = True)
            col.prop(element, 'circular_completion', slider = True)
            col.prop(element, 'completion_feather', slider = True)
            col = layout.column()
            col.prop(element, 'interpolation2')
        elif element.type == 'LENS_DIRT':
            col  = layout.column(align = True)
            col.prop(element, 'mask_size')
            col.prop(element, 'mask_feather')
        elif element.type == 'IRIS':
            col.prop(element, 'iris_count')
            col.prop(element, 'iris_feather')
            col.prop(element, 'iris_roundness')
            col.prop(element, 'iris_blades')
            col = layout.column(align = True)
            col.prop(element, 'iris_outline_thikness')
            col.prop(element, 'iris_outline_opacity', slider = True)
            col = layout.column(align = True)
            col.prop(element, 'iris_rings_count')
            col.prop(element, 'iris_rings_opacity', slider = True)
            col = layout.column(align = True)
            col.prop(element, 'circular_completion', slider = True)
            col.prop(element, 'completion_feather', slider = True)
        elif element.type == 'CAUSTIC':
            col.prop(element, 'caustic_shape', slider = True)
            col.prop(element, 'caustic_thikness', slider = True)
            col.prop(element, 'use_spectrum', slider = True)

############################################################################################
################################ Register/Unregister #######################################
############################################################################################

classes = (
    FLARESWIZARD_Preferences,
    FLARESWIZARD_OT_load_props,
    FLARESWIZARD_OT_add_lf,
    FLARESWIZARD_OT_remove_lens_flare,
    FLARESWIZARD_OT_remove_flares,
    FLARESWIZARD_OT_move_lens_flare,
    FLARESWIZARD_OT_duplicate_flare,
    FLARESWIZARD_OT_flares_visibility,
    FLARESWIZARD_OT_elements_browser,
    FLARESWIZARD_OT_add_element,
    FLARESWIZARD_OT_remove_element,
    FLARESWIZARD_OT_remove_elements,
    FLARESWIZARD_OT_move_element,
    FLARESWIZARD_OT_duplicate_element,
    FLARESWIZARD_OT_elements_visibility,
    FLARESWIZARD_OT_presets_browser,
    FLARESWIZARD_OT_save_flare,
    FLARESWIZARD_OT_load_flare,
    FLARESWIZARD_OT_load_flare_bg,
    FLARESWIZARD_OT_next_page,
    FLARESWIZARD_OT_previous_page,
    FLARESWIZARD_OT_delete_preset,
    FLARESWIZARD_OT_add_background,
    FLARESWIZARD_OT_delete_background,
    FLARESWIZARD_OT_set_scene_resolution,
    FLARESWIZARD_OT_set_movie_length,
    FLARESWIZARD_OT_setup_view_layers,
    FLARESWIZARD_OT_remove_view_layer,
    FLARESWIZARD_OT_setup_aovs,
    FLARESWIZARD_OT_remove_aovs,
    FLARESWIZARD_OT_open_image,
    FLARESWIZARD_OT_open_manual,
    FLARESWIZARD_OT_open_folder,
    FLARESWIZARD_OT_yt_playlist,
    FLARESWIZARD_UL_flares,
    FLARESWIZARD_UL_elements,
    FLARESWIZARD_shortcuts,
    FLARESWIZARD_PT_extra_options,
    FLARESWIZARD_PT_flare_planes,
    FLARESWIZARD_PT_background,
    FLARESWIZARD_PT_compositing,
    FLARESWIZARD_PT_lens_flares,
    FLARESWIZARD_PT_general_settings,
    FLARESWIZARD_PT_instances,
    FLARESWIZARD_PT_blinking,
    FLARESWIZARD_PT_obstacles,
    FLARESWIZARD_PT_elements,
    FLARESWIZARD_PT_elements_shader,
    FLARESWIZARD_PT_elements_transform,
    FLARESWIZARD_PT_triggers,
    FLARESWIZARD_PT_special_options,
    LensFlareOptions,
    ElementsOptions,    
)

pcolls = [
    "icons",
    "presets_previews",
]

def register():
    from bpy.utils import register_class, previews
    for cls in classes:
        register_class(cls)
        
    bpy.types.Scene.fw_update_element = StringProperty(update = update_element)
    bpy.types.Scene.fw_update_bg_cam = StringProperty(update = update_bg_camera)
    
    for i in pcolls:
        preview_collections[i] = bpy.utils.previews.new()
    bpy.types.Scene.fw_icons = EnumProperty(items=icons_enum())
    load_post.append(fw_load_handler)
    
    
def unregister():
    from bpy.utils import unregister_class, previews
    for cls in reversed(classes):
        unregister_class(cls)
        
    del bpy.types.Scene.fw_update_element
    del bpy.types.Scene.fw_update_bg_cam
    
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()
    del bpy.types.Scene.fw_icons
    load_post.remove(fw_load_handler)

if __name__ == "__main__":
    register()