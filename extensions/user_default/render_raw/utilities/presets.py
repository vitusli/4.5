import bpy, os, json, shutil

from ..constants import Pre_settings, Post_settings
from ..preferences import get_prefs
from ..utilities.conversions import map_range
from ..utilities.version import get_addon_version, get_RR_node_version
from ..utilities.curves import RGB_curve_default, create_curve_preset, set_curve_node
from ..utilities.settings import is_default, get_settings
from ..utilities.layers import get_layer_nodes, get_layer_node, reset_layer_settings, add_layer, remove_all_layers, refresh_layers
from ..nodes.update_values import update_group_exposure, update_group_gamma
from ..utilities.cache import cacheless

blank_preset = 'NONE'


preset_settings_to_skip = [
    'enable_RR', 'view_transform',
    'prev_look', 'prev_use_curves', 'prev_exposure',
    'preset', 'presets', 'preset_list', 'preset_name',
    'layer_name', 'layer_factor', 'use_layer', 'use_layer_mask', 'active_layer_index',
    'use_clipping', 'clipping_blacks', 'clipping_whites', 'clipping_saturation'
]


default_path = bpy.path.native_pathsep(
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        '..', 'assets', 'presets')
)


def get_path(context):
    prefs = get_prefs(context)
    prefs_path = prefs.preset_path
    if prefs_path and os.path.isdir(prefs_path):
        return prefs_path
    else:
        return default_path


def get_preset_files(context, path):
    return [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]


def copy_default_presets(context):
    prefs = get_prefs(context)
    path = prefs.preset_path
    if os.path.isdir(path):
        for file in get_preset_files(context, default_path):
            shutil.copy2(os.path.join(default_path, file), path)


def get_preset_list(preset_files):
    preset_names = []
    for file in preset_files:
        if file.endswith('.rr'):
            preset_names.append(file.replace('.rr', ''))
    return [blank_preset] + sorted(preset_names)


def preset_items(self, context):
    if hasattr(context.scene, 'render_raw_presets'):
        presets = []
        for preset_name in context.scene.render_raw_presets.keys():
            if preset_name == blank_preset:
                presets.append((blank_preset, 'None', ''))
            else:
                presets.append((preset_name, preset_name, ''))
        return presets
    else:
        return [(blank_preset, 'None', '')]


def refresh_presets(context):
    path = get_path(context)
    prev_preset = context.scene.render_raw.preset
    context.scene.render_raw_presets.clear()
    preset_list = get_preset_list(get_preset_files(context, path))

    #TODO: Clear out presets that have been deleted from the folder
    for preset in preset_list:
        if preset not in context.scene.render_raw_presets.keys():
            new_preset = context.scene.render_raw_presets.add()
            new_preset.name = preset

    if prev_preset not in preset_list:
        context.scene.render_raw.preset = blank_preset


def get_props_from_key(RR_group, layer_index, key):
    PRE = get_layer_node(RR_group, layer_index, 'Pre')
    POST = get_layer_node(RR_group, layer_index, 'Post')
    if key in Pre_settings:
        return PRE.node_tree.render_raw
    elif key in Post_settings:
        return POST.node_tree.render_raw
    else:
        return RR_group.render_raw


def get_active_props_from_key(RR, key):
    # Both the main group and the layers groups have the same property group which contains all settings
    # But the add-on only reads and writes to the node groups which are affected
    if key in Pre_settings:
        return RR.props_pre
    elif key in Post_settings:
        return RR.props_post
    else:
        return RR.props_group


def key_to_preset(key, preset, props):
    if key in preset_settings_to_skip or is_default(props, key):
        value = None
    else:
        rna = props.bl_rna.properties[key]
        if rna.subtype in ['COLOR', 'COLOR_GAMMA']:
            value = []
            for i in range(rna.array_length):
                value.append(props[key][i])
        else:
            value = props[key]

    return value


def get_layer_preset(node_pre, node_post):
    preset = {}
    preset['version'] = get_addon_version()

    # Older versions would also save group props while
    # newer versions have different presets for groups and layers
    props_pre = node_pre.node_tree.render_raw
    props_post = node_post.node_tree.render_raw

    for key in [x for x in props_pre.keys()]:
        value = key_to_preset(key, preset, props_pre)
        if value != None: 
            preset[key] = value

    for key in [x for x in props_post.keys()]:
        value = key_to_preset(key, preset, props_post)
        if value != None: 
            preset[key] = value

    if 'Color Blending' in [x.name for x in node_post.node_tree.nodes]:
        CB = node_post.node_tree.nodes['Color Blending'].node_tree.nodes
    else:
        CB = node_post.node_tree.nodes['Color Balance'].node_tree.nodes
    preset['highlight_blending'] = CB['Highlight Color'].blend_type
    preset['midtone_blending'] = CB['Midtone Color'].blend_type
    preset['shadow_blending'] = CB['Shadow Color'].blend_type

    preset['value_curves'] = create_curve_preset(node_post.node_tree.nodes['Curves'])

    return preset


def write_preset(context, preset, preset_name):
    path = get_path(context)
    with open(
        os.path.join(path, f"{preset_name}.rr"), "w"
    ) as file:
        file.write(json.dumps(preset, indent=4))


@cacheless
def save_preset(self, context):
    RR = get_settings(context)
    preset = get_layer_preset(RR.layer_pre, RR.layer_post)
    write_preset(context, preset, self.preset_name)
    refresh_presets(context)
    RR.props_pre.preset = self.preset_name


def load_preset(context, preset_name):
    try:
        path = get_path(context)
        with open(
            os.path.join(path, f"{preset_name}.rr"), "r"
        ) as file:
            return json.load(file)
    except:
        refresh_presets(context)
        print('ERROR: Render Raw preset not found. Refreshing list instead.')


def remove_preset(context):
    RR = get_settings(context)
    path = get_path(context)
    os.remove(
        os.path.join(path, f"{RR.props_pre.preset}.rr")
    )
    RR.props_pre.preset = 'NONE'


def apply_layer_preset(RR_group, layer_index, preset):
    from ..nodes.update_RR import update_all

    reset_layer_settings(RR_group, layer_index)

    try:
        preset_keys = preset.keys()
    except:
        refresh_presets(bpy.context)
        print('ERROR: Render Raw preset not found. Refreshing list instead.')
        return

    PRE = get_layer_node(RR_group, layer_index, 'Pre')
    POST = get_layer_node(RR_group, layer_index, 'Post')
    PROPS_POST = POST.node_tree.render_raw
    CB_NODES = POST.node_tree.nodes['Color Blending'].node_tree.nodes

    for key in preset_keys:
        PROPS = get_props_from_key(RR_group, layer_index, key)

        if key == 'value_curves':
            set_curve_node(POST.node_tree.nodes['Curves'], preset[key])
        elif key == 'value_curves_pre':
            set_curve_node(PRE.node_tree.nodes['Curves'], preset[key])
        elif key == 'highlight_blending':
            CB_NODES['Highlight Color'].blend_type = preset[key]
        elif key == 'midtone_blending':
            CB_NODES['Midtone Color'].blend_type = preset[key]
        elif key == 'shadow_blending':
            CB_NODES['Shadow Color'].blend_type = preset[key]
        elif hasattr(PROPS, key):
            prop = PROPS.bl_rna.properties[key]
            if prop.type == 'ENUM':
                default = prop.default
                PROPS[key] = prop.enum_items.get(default).value
            else:
                PROPS[key] = preset[key]

    # Handle conversions from previous RR versions
    if 'version' not in preset_keys:
        print('Converting Render Raw preset from < v1.0.0 to v1.0.0')
        preset['version'] = '(1, 0, 0)'
        for key in preset_keys:
            PROPS = get_props_from_key(RR_group, layer_index, key)
            if hasattr(PROPS, key):
                if key == 'blacks':
                    PROPS[key] = map_range(preset[key], 0, 1, 0.5, -0.5)
                if key == 'whites':
                    PROPS[key] = map_range(preset[key], 0, 1, 0.5, -0.5)
                if key == 'highlights':
                    PROPS[key] = map_range(preset[key], 0, 1, -0.5, 0.5)
                if key == 'shadows':
                    PROPS[key] = map_range(preset[key], 0, 1, -0.5, 0.5)

    if eval(preset['version']) < (1, 2, 3):
        if 'curves_factor' in preset_keys:
            PROPS_POST.post_curves_factor = preset['curves_factor']

    if eval(preset['version']) < (1, 2, 8):
        if 'vignette_value' in preset_keys:
            PROPS_POST.vignette_factor = abs(preset['vignette_value'])
            tint = preset['vignette_value'] if 'vignette_tint' in preset_keys else [0,0,0,1]
            value = [0,0,0,1] if preset['vignette_value'] < 0 else [1,1,1,1]
            PROPS_POST.vignette_color = [tint[0]*value[0], tint[1]*value[1], tint[2]*value[2], 1]
        if 'vignette_highlights' in preset_keys:
            PROPS_POST.vignette_linear_blend = preset['vignette_highlights']

    if eval(preset['version']) < (1, 2, 10):
        per_hue = [
            'red_saturation', 'red_value', 'orange_saturation', 'orange_value',
            'yellow_saturation', 'yellow_value', 'green_saturation', 'green_value',
            'teal_saturation', 'teal_value', 'blue_saturation', 'blue_value',
            'pink_saturation', 'pink_value',
        ]
        for key in per_hue:
            if key in preset_keys:
                PROPS[key] = preset[key] / 2
        
    update_all(None, bpy.context, RR_group, layer_index)


@cacheless
def apply_active_layer_preset(self, context):
    from ..nodes.update_RR import update_all
    RR = get_settings(context)

    if RR.props_pre.preset == blank_preset:
        reset_layer_settings(RR.group, RR.active_layer_index)
        update_all(self, context, RR.group, RR.active_layer_index)
        return

    preset = load_preset(context, RR.props_pre.preset)
    apply_layer_preset(RR.group, RR.active_layer_index, preset)


def get_group_preset(RR_group):
    preset = {
        'group': RR_group.render_raw,
        'layers': {},
    }

    layer_nodes = get_layer_nodes(RR_group)

    for index, layer_pre in enumerate(layer_nodes['Pre']):
        layer_post = layer_nodes['Post'][index]
        layer_name = layer_pre.node_tree.render_raw.layer_name
        preset['layers'][layer_name] = get_layer_preset(layer_pre, layer_post)

    return preset


def apply_group_preset(RR_group, preset):
    from ..nodes.update_RR import update_all

    update_group_exposure(RR_group)
    update_group_gamma(RR_group)

    for prop in preset['group'].keys():
        RR_group.render_raw[prop] = preset['group'][prop]


    refresh_layers(RR_group)
    remove_all_layers(RR_group)

    for index, layer_name in enumerate(preset['layers'].keys()):
        new_layer = add_layer(RR_group, layer_name)
        apply_layer_preset(RR_group, index, preset['layers'][layer_name])
        RR_group.render_raw.active_layer_index = index
        update_all(None, bpy.context, RR_group)