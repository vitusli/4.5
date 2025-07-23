import os
import platform
import re
import shutil
import site
import string
import subprocess
import sys
from pathlib import Path
from os.path import join, dirname, realpath
from os import listdir

from bpy.props import EnumProperty
from bpy.types import Object

from ..t3dn_bip import previews
from ..t3dn_bip.previews import ImagePreviewCollection
from .. import tasks_queue

import bpy

# Chargement des icones
materializer_icons_collection = {}
materializer_icones_is_loaded = False
materializer_previews = None
preview_collections = []

image_size = (32, 32)

main_dir = dirname(dirname(realpath(__file__)))
file_path_node_tree = join(main_dir, 'Blender_Files', 'Material_Studying.blend', 'NodeTree')


def make_oops(msg):
    def oops(self, context):
        for m in msg:
            self.layout.label(text=m)

    return oops


def get_addon_preferences():
    addon_key = __package__.split(".fluent_materializer")[0]+'.fluent_materializer'
    addon_prefs = bpy.context.preferences.addons[addon_key].preferences

    return addon_prefs


def active_object(obj=None, action='GET', solo=False):
    if solo:
        bpy.ops.object.select_all(action="DESELECT")
    if action == 'SET':
        if obj is not None:
            obj.hide_set(False)
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
        return obj
    elif action == 'GET':
        return bpy.context.active_object


def select_objects(objs=[], action='GET'):
    if action == 'SET':
        for obj in objs:
            obj.hide_set(False)
            obj.select_set(True)
        return True
    elif action == 'GET':
        return bpy.context.selected_objects


def load_icons():
    global materializer_icons_collection
    global materializer_icones_is_loaded
    global materializer_previews

    if materializer_icones_is_loaded:
        return materializer_icons_collection

    materializer_previews = previews.new(max_size=(256, 256))
    parent_dir = os.path.join(dirname(realpath(__file__)), os.pardir)
    icons_dir = join(os.path.abspath(parent_dir), 'UI')
    icons_dir = join(icons_dir, 'icons')

    for f in listdir(icons_dir):
        if f.split('.')[1] in ['jpg', 'jpeg', 'JPG', 'JPEG', 'png', 'PNG']:
            f_name = f.split('.')[0]
            icons_path = join(icons_dir, f)
            preview = materializer_previews.load_safe(f_name, icons_path, 'IMAGE')
            materializer_icons_collection[f_name] = preview

    materializer_icones_is_loaded = True

    return materializer_icons_collection


def clear_icons():
    global materializer_icones_is_loaded
    global materializer_icons_collection
    global materializer_previews
    if materializer_previews:
        previews.remove(materializer_previews)
    materializer_icons_collection.clear()
    materializer_icones_is_loaded = False


def unregister_previews(preview_coll_to_unregister=None):
    global preview_collections

    for coll_name, col in preview_collections:
        if preview_coll_to_unregister is not None and preview_coll_to_unregister != coll_name:
            continue

        try:
            delattr(bpy.types.WindowManager, "fm_" + coll_name)
        except:
            pass

        try:
            previews.remove(col)
        except:
            pass


def init_node_samples():
    print('--- init SAMPLE')
    props = bpy.context.scene.FluentShaderProps
    if not props.is_init:
        props.nb_samples = get_addon_preferences().nb_samples
        props.is_init = True


def import_selected_node(self, context):
    if bpy.context.scene.FluentShaderProps.sections == 'decals':
        bpy.ops.fluent.newdecal('INVOKE_DEFAULT', is_procedural_decal=True)
        return

    bpy.ops.fluent.add_nodes('INVOKE_DEFAULT', choice=bpy.context.scene.FluentShaderProps.sections)


def populate_preview_collection(col: ImagePreviewCollection, coll_name):
    items = []

    preview_dir = join(dirname(realpath(__file__)), '..', 'thumbnails')
    coll_dir = join(preview_dir, coll_name)

    files = os.listdir(coll_dir)
    for file in files:
        if ".jpg" not in file:
            continue

        image_name = file.replace('.jpg', '')
        icon_path = os.path.join(coll_dir, file)
        preview = col.load_safe(image_name, icon_path, 'IMAGE')

        items.append((image_name, image_name, image_name, preview.icon_id, preview.icon_id))

    return items


def init_libraries_previews(reload=False):
    print('--- init PREVIEW')
    global preview_collections
    fluent_props = bpy.context.scene.FluentShaderProps

    coll_name = fluent_props.sections
    print('---', coll_name)
    full_coll_name = "fm_" + coll_name
    if hasattr(bpy.types.WindowManager, full_coll_name) and not reload:
        return

    col = previews.new(max_size=(256, 256))
    unregister_previews(preview_coll_to_unregister=coll_name)

    try:
        items = populate_preview_collection(
            col,
            coll_name
        )
    except Exception as inst:
        return

    enum = EnumProperty(items=items, update=import_selected_node)
    setattr(bpy.types.WindowManager, full_coll_name, enum)
    preview_collections.append((coll_name, col))


def link(material, from_node, from_slot_name, to_node, to_slot_name):
    try:
        input = to_node.inputs[to_slot_name]
        output = from_node.outputs[from_slot_name]
        material.node_tree.links.new(input, output)
    except:pass


def get_node_tree(material):
    return material.node_tree


def get_nodes(material, context = None):
    if context:
        return get_node_tree(context.material).nodes
    return get_node_tree(material).nodes


def get_selected_nodes(nodes):
    selected_nodes = []
    for n in nodes:
        if n.select:
            selected_nodes.append(n)
    return selected_nodes


def enum_previews_from_directory_items(coll_name):
    global preview_collections
    enum_items = []
    if bpy.context is None or len(preview_collections) == 0:
        return enum_items

    pcoll = preview_collections[coll_name]
    directory = pcoll.my_previews_dir

    if directory and os.path.exists(directory):
        # Scan the directory for png files
        image_paths = []
        for fn in os.listdir(directory):
            if fn.lower().endswith(".jpg"):
                image_paths.append(fn)

        for i, name in enumerate(image_paths):
            # generates a thumbnail preview for a file.
            filepath = os.path.join(directory, name)
            icon = pcoll.get(name)
            if not icon:
                thumb = pcoll.load(name, filepath, 'IMAGE')
            else:
                thumb = pcoll[name]
            label = name.split('.jpg')[0]
            try:
                label = label.split('fm_')[1]
            except:pass
            label = label.replace('_', ' ')
            enum_items.append((name.split('.jpg')[0], label, "", thumb.icon_id, i))

    pcoll.my_previews = enum_items
    pcoll.my_previews_dir = directory
    return pcoll.my_previews


def import_node_group(group_name, context=None):
    if context:
        material = context.material
        tree = context.space_data.edit_tree
    else:
        material = bpy.context.active_object.active_material
        tree = material.node_tree
    nodes = tree.nodes
    if bpy.data.node_groups.get(group_name):
        new_group = nodes.new(type='ShaderNodeGroup')
        new_group.node_tree = bpy.data.node_groups.get(group_name)
        new_group.name = group_name
    else:
        bpy.ops.wm.append(
            filepath=join(file_path_node_tree, group_name),
            directory=file_path_node_tree,
            filename=group_name
        )
        new_group = nodes.new(type='ShaderNodeGroup')
        new_group.node_tree = bpy.data.node_groups.get(group_name)
    return new_group


def get_principlebsdf(nodes):
    for n in nodes:
        if n.type == 'BSDF_PRINCIPLED':
            return n
    print('--- no Principled BSDF')


def deselect_nodes(nodes):
    for node in nodes:
        node.select = False


def to_what(node, output_name):
    node_tab = []
    socket_tab = []
    for l in node.outputs[output_name].links:
        node_tab.append(l.to_node)
        socket_tab.append(l.to_socket.name)
    return {'node': node_tab, 'socket': socket_tab}


def find_empty_mixlayer_inputs(mixlayers):
    if not len(mixlayers.inputs['Color 1'].links):
        return 1
    if not len(mixlayers.inputs['Color 2'].links):
        return 2
    return False


def connect_layer_to_mixlayers(material, layer, mixlayers, force=None):
    if not force:
        test = find_empty_mixlayer_inputs(mixlayers)
        if not test:
            return
    else:
        test = force
    if test == 1:
        link(material, layer, 'Color', mixlayers, 'Color 1')
        link(material, layer, 'Metallic', mixlayers, 'Metallic 1')
        link(material, layer, 'Roughness', mixlayers, 'Roughness 1')
        link(material, layer, 'IOR', mixlayers, 'IOR 1')
        link(material, layer, 'Alpha', mixlayers, 'Alpha 1')
        link(material, layer, 'Normal', mixlayers, 'Normal 1')
        link(material, layer, 'SSS Weight', mixlayers, 'SSS Weight 1')
        link(material, layer, 'SSS Scale', mixlayers, 'SSS Scale 1')
        link(material, layer, 'Transmission', mixlayers, 'Transmission 1')
        link(material, layer, 'Coat Weight', mixlayers, 'Coat Weight 1')
        link(material, layer, 'Coat Roughness', mixlayers, 'Coat Roughness 1')
        link(material, layer, 'Coat IOR', mixlayers, 'Coat IOR 1')
        link(material, layer, 'Coat Tint', mixlayers, 'Coat Tint 1')
        link(material, layer, 'Coat Normal', mixlayers, 'Coat Normal 1')
        link(material, layer, 'Sheen Weight', mixlayers, 'Sheen Weight 1')
        link(material, layer, 'Sheen Roughness', mixlayers, 'Sheen Roughness 1')
        link(material, layer, 'Sheen Tint', mixlayers, 'Sheen Tint 1')
        link(material, layer, 'Emission Strength', mixlayers, 'Emission Strength 1')
        link(material, layer, 'Height', mixlayers, 'Height 1')
    if test == 2:
        link(material, layer, 'Color', mixlayers, 'Color 2')
        link(material, layer, 'Metallic', mixlayers, 'Metallic 2')
        link(material, layer, 'Roughness', mixlayers, 'Roughness 2')
        link(material, layer, 'IOR', mixlayers, 'IOR 2')
        link(material, layer, 'Alpha', mixlayers, 'Alpha 2')
        link(material, layer, 'Normal', mixlayers, 'Normal 2')
        link(material, layer, 'SSS Weight', mixlayers, 'SSS Weight 2')
        link(material, layer, 'SSS Scale', mixlayers, 'SSS Scale 2')
        link(material, layer, 'Transmission', mixlayers, 'Transmission 2')
        link(material, layer, 'Coat Weight', mixlayers, 'Coat Weight 2')
        link(material, layer, 'Coat Roughness', mixlayers, 'Coat Roughness 2')
        link(material, layer, 'Coat IOR', mixlayers, 'Coat IOR 2')
        link(material, layer, 'Coat Tint', mixlayers, 'Coat Tint 2')
        link(material, layer, 'Coat Normal', mixlayers, 'Coat Normal 2')
        link(material, layer, 'Sheen Weight', mixlayers, 'Sheen Weight 2')
        link(material, layer, 'Sheen Roughness', mixlayers, 'Sheen Roughness 2')
        link(material, layer, 'Sheen Tint', mixlayers, 'Sheen Tint 2')
        link(material, layer, 'Emission Strength', mixlayers, 'Emission Strength 2')
        link(material, layer, 'Height', mixlayers, 'Height 2')


def connect_layer_to_bsdf(material, layer, bsdf):
    link(material, layer, 'Color', bsdf, 0)
    link(material, layer, 'Metallic', bsdf, 1)
    link(material, layer, 'Roughness', bsdf, 2)
    link(material, layer, 'IOR', bsdf, 3)
    link(material, layer, 'Alpha', bsdf, 4)
    link(material, layer, 'Normal', bsdf, 5)
    link(material, layer, 'SSS Weight', bsdf, 8)
    link(material, layer, 'SSS Scale', bsdf, 10)
    link(material, layer, 'Transmission', bsdf, 18)
    link(material, layer, 'Coat Weight', bsdf, 19)
    link(material, layer, 'Coat Roughness', bsdf, 20)
    link(material, layer, 'Coat IOR', bsdf, 21)
    link(material, layer, 'Coat Tint', bsdf, 22)
    link(material, layer, 'Coat Normal', bsdf, 23)
    link(material, layer, 'Sheen Weight', bsdf, 24)
    link(material, layer, 'Sheen Roughness', bsdf, 25)
    link(material, layer, 'Sheen Tint', bsdf, 26)
    link(material, layer, 'Emission Color', bsdf, 27)
    link(material, layer, 'Emission Strength', bsdf, 28)


def connect_mixlayers_to_bsdf(material, mixlayer, bsdf):
    link(material, mixlayer, 'Color', bsdf, 0)
    link(material, mixlayer, 'Metallic', bsdf, 1)
    link(material, mixlayer, 'Roughness', bsdf, 2)
    link(material, mixlayer, 'IOR', bsdf, 3)
    link(material, mixlayer, 'Alpha', bsdf, 4)
    link(material, mixlayer, 'Normal', bsdf, 5)
    link(material, mixlayer, 'SSS Weight', bsdf, 8)
    link(material, mixlayer, 'SSS Scale', bsdf, 10)
    link(material, mixlayer, 'Transmission', bsdf, 18)
    link(material, mixlayer, 'Coat Weight', bsdf, 19)
    link(material, mixlayer, 'Coat Roughness', bsdf, 20)
    link(material, mixlayer, 'Coat IOR', bsdf, 21)
    link(material, mixlayer, 'Coat Tint', bsdf, 22)
    link(material, mixlayer, 'Coat Normal', bsdf, 23)
    link(material, mixlayer, 'Sheen Weight', bsdf, 24)
    link(material, mixlayer, 'Sheen Roughness', bsdf, 25)
    link(material, mixlayer, 'Sheen Tint', bsdf, 26)
    link(material, mixlayer, 'Emission Color', bsdf, 27)
    link(material, mixlayer, 'Emission Strength', bsdf, 28)


def make_single_user_node(node):
    original = node.node_tree
    single = original.copy()
    node.node_tree = single
    return node


def apply_node_color(node):
    if not get_addon_preferences().use_custom_node_color:
        return
    node.use_custom_color = True
    color = False
    try:
        if node.node_tree.name == 'Layer':
            color = get_addon_preferences().color_layer
        if node.node_tree.name == 'Mix Layers':
            color = get_addon_preferences().color_mixlayers
        if color:
            node.color = color
    except:pass


def get_python_paths():
    python_path = sys.executable

    python_lib_path = os.path.join(os.path.dirname(os.path.dirname(python_path)), "lib")
    if platform.system() != "Windows":
        python_lib_path = os.path.join(os.path.dirname(os.path.dirname(python_path)), "lib", os.path.basename(python_path))

    ensurepip_path = os.path.join(python_lib_path, "ensurepip")
    sitepackages_path = os.path.join(python_lib_path, "site-packages")
    usersitepackages_path = site.getusersitepackages()

    modules_paths = [os.path.join(path, 'modules') for path in bpy.utils.script_paths() if path.endswith('scripts')]

    return python_path, ensurepip_path, modules_paths, sitepackages_path, usersitepackages_path


def remove_pil(sitepackages_path, usersitepackages_path, modules_paths):
    for site_path in [sitepackages_path, usersitepackages_path] + modules_paths:
        if os.path.exists(site_path):
            folders = [(f, os.path.join(site_path, f)) for f in os.listdir(site_path)]

            for folder, path in folders:
                if (folder.startswith("Pillow") and folder.endswith("egg")) or folder.startswith("Pillow") or folder == "PIL":
                    shutil.rmtree(path, ignore_errors=True)


def install_pil(pythonbin_path, ensurepip_path):
    cmd = [pythonbin_path, ensurepip_path, "--upgrade", "--user"]
    pip = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if pip.returncode == 0:
        print("Pip installed!\n")
        cmd = [pythonbin_path, "-m", "pip", "install", "--upgrade", "--user", "Pillow"]
        pil = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if pil.returncode != 0:
            print("Failed to install PIL!\n")
            return False

        print("PIL installed!\n")

        cmd = [pythonbin_path, "-m", "pip", "install", "--upgrade", "--user", "wheel"]

        wheel = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if wheel.returncode != 0:
            print("Failed to install Wheel!\n")
            return False

        print("Wheel installed!\n")
        get_addon_preferences().pil_warning = True
        return True

    print("Failed to install pip!\n")
    return False


def checkMapBakeEnabled(map_name: string) -> bool:
    props = bpy.context.scene.FluentShaderProps
    if map_name == 'metallic':
        return props.bake_make_metallic
    if map_name == 'roughness':
        return props.bake_make_roughness
    if map_name == 'ao':
        return props.bake_make_ao
    if map_name == 'emission':
        return props.bake_make_emission
    if map_name == 'alpha':
        return props.bake_make_alpha

    return False


def checkMissingCombineChannel():
    props = bpy.context.scene.FluentShaderProps
    if props.bake_red_channel != 'none':
        if not checkMapBakeEnabled(props.bake_red_channel):
            return props.bake_red_channel

    if props.bake_green_channel != 'none':
        if not checkMapBakeEnabled(props.bake_green_channel):
            return props.bake_green_channel

    if props.bake_blue_channel != 'none':
        if not checkMapBakeEnabled(props.bake_blue_channel):
            return props.bake_blue_channel

    return None


def get_material_output(nodes):
    for n in nodes:
        if n.type == 'OUTPUT_MATERIAL':
            return n
    print('--- no output material')


def create_img(object, size, map, is_data, is_float, use_udim, udim_count):
    img = bpy.data.images.new(object.name + '_' + str(size) + 'px_' + map, width=size, height=size, tiled=use_udim, is_data=is_data, float_buffer=is_float)
    if use_udim:
        img.name = img.name+'.<UDIM>.'
        previous_area_ui_type = bpy.context.area.ui_type
        bpy.context.area.ui_type = 'IMAGE_EDITOR'
        for i in range(udim_count-1):
            tile = img.tiles.new(tile_number=1001+1+i)
            img.tiles.active = tile
            bpy.context.space_data.image = img
            bpy.ops.image.tile_fill(color=(0, 0, 0, 1), width=size, height=size, float=is_float)
        bpy.context.area.ui_type = previous_area_ui_type
    return img


def search_text_coord(node):
    nodes = node.node_tree.nodes
    tex_coord_obj = None
    for n in nodes:
        if n.type == 'TEX_COORD':
            tex_coord_obj = n.object
            return tex_coord_obj
    if not tex_coord_obj:
        for n in nodes:
            if n.type == 'GROUP':
                tex_coord_obj = search_text_coord(n)
                return tex_coord_obj
    return tex_coord_obj


def change_all_coordinates(node, obj_coord):
    make_unique_node_group(node)
    nodes = node.node_tree.nodes
    exceptions = ['grunge_for_decal_edges']
    for n in nodes:
        if n.type == 'GROUP' and not any(n.node_tree.name.startswith(exception) for exception in exceptions):
            change_all_coordinates(n, obj_coord)
        else:
            if n.type == 'TEX_COORD':
                n.object = obj_coord
    return


def make_unique_node_group(node):
    original = node.node_tree
    single = original.copy()
    node.node_tree = single


def update_error_baking(context, error_message):
    context.scene.FluentShaderProps.baking_error = error_message


def update_is_baking(context, value):
    context.scene.FluentShaderProps.is_baking = value


def after_bake_task(context, objects):
    update_is_baking(context, False)
    remove_unpack_in_image(context)
    for obj in objects:
        load_baked_textures_in_current_blend(context, obj)
        set_baked_material(context, obj)

    area = next((area for area in bpy.context.screen.areas if area.type == 'VIEW_3D'))

    with bpy.context.temp_override(area=area):
        bpy.ops.wm.context_toggle(data_path='space_data.show_region_ui')
        bpy.ops.wm.context_toggle(data_path='space_data.show_region_ui')


def find_latest_texture_image(obj_name, texture_type, size):
    image_base_name = obj_name + '_' + str(size) + 'px_' + texture_type
    file_path = bpy.data.filepath
    file_name = os.path.basename(file_path)
    path = file_path.split(file_name)[0]

    textures_path = os.path.join(path, 'Textures')
    dir_list = os.listdir(textures_path)

    textures_found = []
    for file in dir_list:
        if image_base_name not in file:
            continue

        textures_found.append(file)

    sorted_images = sorted(textures_found)

    return bpy.data.images.load(filepath=os.path.join(textures_path, sorted_images.pop()), check_existing=True)


def remove_unpack_in_image(context):
    properties = bpy.context.scene.FluentShaderProps
    if properties.bake_in_image is None:
        return

    maps = find_all_maps_by_image(properties.bake_in_image.name)
    for map in maps:
        map.unpack(method='USE_ORIGINAL')
        bpy.data.images.remove(map, do_unlink=True)

    properties.bake_in_image = bpy.data.images.load(properties.bake_in_image_path)


def load_baked_textures_in_current_blend(context, obj:Object):
    properties = context.scene.FluentShaderProps
    size = int(properties.map_size)
    object_name = obj.name
    if properties.bake_in_image is not None:
        object_name = properties.bake_in_image.name.split('_')[0]
    if properties.bake_make_color:
        img = find_latest_texture_image(object_name, 'Color', size)
        img.use_fake_user = True
    if properties.bake_make_roughness:
        img = find_latest_texture_image(object_name, 'Roughness', size)
        img.use_fake_user = True
    if properties.bake_make_metallic:
        img = find_latest_texture_image(object_name, 'Metallic', size)
        img.use_fake_user = True
    if properties.bake_make_alpha:
        img = find_latest_texture_image(object_name, 'Alpha', size)
        img.use_fake_user = True
    if properties.bake_make_normal:
        img = find_latest_texture_image(object_name, 'Normal', size)
        img.use_fake_user = True
    if properties.bake_normal_directx:
        img = find_latest_texture_image(object_name, 'NDirectX', size)
        img.use_fake_user = True
    if properties.bake_make_emission:
        img = find_latest_texture_image(object_name, 'EmissionColor', size)
        img.use_fake_user = True
        img = find_latest_texture_image(object_name, 'EmissionStrength', size)
        img.use_fake_user = True
    if properties.bake_combine_channels:
        selected_maps = []
        if properties.bake_red_channel != 'none':
            selected_maps.append('R-' + properties.bake_red_channel)
        if properties.bake_green_channel != 'none':
            selected_maps.append('G-' + properties.bake_green_channel)
        if properties.bake_blue_channel != 'none':
            selected_maps.append('B-' + properties.bake_blue_channel)
        combine_img_name = '-'.join(selected_maps)
        img = find_latest_texture_image(object_name, combine_img_name, size)
        img.use_fake_user = True


def set_baked_material(context, obj: Object):
    properties = context.scene.FluentShaderProps
    if not properties.bake_auto_set:
        return

    baked_material = bpy.data.materials.new(name="Baked")
    baked_material.use_nodes = True
    obj.data.materials.append(baked_material)

    nodes = get_nodes(baked_material)
    material_output = get_material_output(nodes)
    PS = get_principlebsdf(nodes)
    size = int(bpy.context.scene.FluentShaderProps.map_size)

    if properties.bake_make_color:
        color_node = nodes.new(type='ShaderNodeTexImage')
        color_img = find_latest_texture_image(obj.name, 'Color', size)
        color_node.image = color_img
        link(baked_material, color_node, 0, PS, 'Base Color')
        color_node.location = (-500, 800)
    if properties.bake_make_roughness:
        roughness_node = nodes.new(type='ShaderNodeTexImage')
        roughness_node.image = find_latest_texture_image(obj.name, 'Roughness', size)
        roughness_node.image.colorspace_settings.name = 'Non-Color'
        link(baked_material, roughness_node, 0, PS, 'Roughness')
        roughness_node.location = (-500, 200)
    if properties.bake_make_metallic:
        metallic_node = nodes.new(type='ShaderNodeTexImage')
        metallic_node.image = find_latest_texture_image(obj.name, 'Metallic', size)
        metallic_node.image.colorspace_settings.name = 'Non-Color'
        link(baked_material, metallic_node, 0, PS, 'Metallic')
        metallic_node.location = (-500, 500)
    if properties.bake_make_alpha:
        alpha_node = nodes.new(type='ShaderNodeTexImage')
        alpha_node.image = find_latest_texture_image(obj.name, 'Alpha', size)
        alpha_node.image.colorspace_settings.name = 'Non-Color'
        link(baked_material, alpha_node, 0, PS, 'Alpha')
    if properties.bake_make_normal:
        normal_node = nodes.new(type='ShaderNodeTexImage')
        normal_node.image = find_latest_texture_image(obj.name, 'Normal', size)
        normal_node.image.colorspace_settings.name = 'Non-Color'
        normal_map_node = nodes.new(type='ShaderNodeNormalMap')
        link(baked_material, normal_node, 0, normal_map_node, 'Color')
        link(baked_material, normal_map_node, 0, PS, 'Normal')
        normal_node.location = (-500, -100)
        normal_map_node.location = (-200, -100)
    if properties.bake_make_emission:
        emission_color_node = nodes.new(type='ShaderNodeTexImage')
        emission_color_node.image = find_latest_texture_image(obj.name, 'EmissionColor', size)
        link(baked_material, emission_color_node, 0, PS, 26)
        emission_strength_node = nodes.new(type='ShaderNodeTexImage')
        emission_strength_node.image = find_latest_texture_image(obj.name, 'EmissionStrength', size)
        emission_strength_node.image.colorspace_settings.name = 'Non-Color'
        link(baked_material, emission_strength_node, 0, PS, 27)


def build_string_setting(setting_name: string):
    if not hasattr(bpy.context.scene.FluentShaderProps, setting_name):
        raise Exception(f'setting "{setting_name} not found')

    return setting_name + ':' + str(getattr(bpy.context.scene.FluentShaderProps, setting_name))


def find_all_maps_by_image(reuse_image_name: string) -> list:
    """Trouve toutes les maps à partir d'une image"""
    nomenclature = reuse_image_name.split('_')
    root_name = nomenclature[0]
    resolution = nomenclature[1]
    map_type = nomenclature[2]
    maps = []

    for img in bpy.data.images:
        nomenclature_test = img.name.split('_')
        if nomenclature_test[0] == root_name and nomenclature_test[1] == resolution:
            maps.append(img)
    return maps


def recursive_image_research_and_pack(nodes):
    for node in nodes:
        if node.type == 'TEX_IMAGE' and node.image:
            try:
                node.image.pack()
            except:
                pass
        if node.type == 'GROUP':
            recursive_image_research_and_pack(node.node_tree.nodes)


def get_version_from_manifest():
    content = open(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'blender_manifest.toml')).read()
    pattern = r'^version\s*=\s*"(\d+\.\d+\.\d+)"'
    match = re.search(pattern, content, re.MULTILINE)

    # Extract and print the version number if a match is found
    if match:
        return match.group(1)
    else:
        print("No version number found.")
        return 'x.x.x'


def install_cv2() -> bool:
    '''Install cv2 and import the Image module.'''
    if 'python' in Path(sys.executable).stem.lower():
        exe = sys.executable
    else:
        exe = bpy.app.binary_path_python

    args = [exe, '-m', 'ensurepip', '--user', '--upgrade', '--default-pip']
    if subprocess.call(args=args, timeout=600):
        return False

    args = [exe, '-m', 'pip', 'install', '--user', '--upgrade', 'opencv-python']
    if subprocess.call(args=args, timeout=600):
        return False

    return True


def uninstall_cv2():
    '''Install cv2 and import the Image module.'''
    if 'python' in Path(sys.executable).stem.lower():
        exe = sys.executable
    else:
        exe = bpy.app.binary_path_python

    args = [exe, '-m', 'pip', 'uninstall', 'opencv-python']
    if subprocess.call(args=args, timeout=600):
        return False

    return True


def decal_gradient_generator(img_path):
    import cv2 as cv
    import numpy as np

    # Ajout d'une bordure uniforme pour compenser les effets d'érosion
    def add_uniform_border(img, border_size=100):
        return cv.copyMakeBorder(img, border_size, border_size, border_size, border_size, cv.BORDER_CONSTANT, value=[0, 0, 0, 0])

    # Appliquer des érosions successives et stocker chaque résultat
    def apply_erosions(img, num_erosions, erosion_size):
        kernel = cv.getStructuringElement(cv.MORPH_ELLIPSE, (erosion_size, erosion_size))
        eroded_images = []

        for i in range(num_erosions):
            img = cv.erode(img, kernel, iterations=1)
            eroded_images.append(img.copy())

        return eroded_images

    # Mélanger les images érodées ensemble avec un poids égal pour chaque image
    def blend_images(images):
        blended_image = np.zeros_like(images[0], dtype=np.float32)
        weight = 1 / len(images)

        for img in images:
            blended_image += img.astype(np.float32) * weight

        # Convertir en uint8 pour une image correcte
        blended_image = np.clip(blended_image, 0, 255).astype(np.uint8)

        return blended_image

    # Rogner l'image au centre selon les dimensions originales
    def crop_to_original_size(image, original_size, border_size=100):
        height, width = original_size
        return image[border_size:height + border_size, border_size:width + border_size]

    # Charger l'image avec canal alpha
    img = cv.imread(img_path, cv.IMREAD_UNCHANGED)

    # Vérifier si l'image contient un canal alpha
    if img is None or img.shape[2] != 4:
        print("Erreur : L'image doit être au format RGBA.")
        return

    # Dimensions de l'image d'origine
    original_height, original_width = img.shape[:2]

    # Ajouter une bordure uniforme autour de l'image
    border_size = 100
    img_with_border = add_uniform_border(img, border_size)

    # Extraire la couche alpha pour les érosions
    alpha_channel = img_with_border[:, :, 3]

    # Paramètres d'érosion
    num_erosions = 256
    erosion_size = 3  # 3 semble être le minimum

    # Effectuer les érosions successives et stocker chaque résultat
    eroded_images = apply_erosions(alpha_channel, num_erosions, erosion_size)

    # Mélanger toutes les images érodées pour créer un dégradé
    blended_alpha = blend_images(eroded_images)

    # Rogner l'image au centre pour la ramener à la taille de l'image d'origine
    cropped_image = crop_to_original_size(blended_alpha, (original_height, original_width), border_size)

    # Sauvegarder le résultat en tant qu'image PNG
    # Construire le nouveau chemin avec le nouveau nom de fichier
    folder = os.path.dirname(img_path)
    file_name, extension = os.path.splitext(os.path.basename(img_path))
    new_name = f"{file_name}_edge_gradient{extension}"
    gradient_path = os.path.join(folder, new_name)
    cv.imwrite(gradient_path, cropped_image)

    return gradient_path


def get_x_y_for_node(node):
    for area in bpy.context.screen.areas:
        if area.type == 'NODE_EDITOR':
            for region in area.regions:
                if region.type == 'WINDOW':
                    ui_scale = bpy.context.preferences.system.ui_scale
                    x, y = region.view2d.region_to_view(region.width / 2, region.height / 2)
                    xx = (x / ui_scale) - node.dimensions.x//(2*ui_scale)
                    yy = (y / ui_scale) + node.dimensions.y//(2*ui_scale)
                    return (xx, yy)