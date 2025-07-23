import bpy
from ..utilities.settings import get_settings
from ..nodes.update_colors import update_preserve_color


def get_view_transforms():
    if bpy.app.version < (4, 2, 0):
        return [
            ('ACEScg', 'ACES', ''),
            ('AgX Base sRGB', 'AgX', ''),
            ('AgX Log', 'AgX Log', ''),
            ('False Color', 'False Color', ''),
            ('Filmic sRGB', 'Filmic', ''),
            ('Filmic Log', 'Filmic Log', ''),
            ('sRGB', 'Standard', ''),
        ]
    else:
        return [
            ('ACEScg', 'ACES', ''),
            ('AgX Base sRGB', 'AgX', ''),
            ('AgX Log', 'AgX Log', ''),
            ('False Color', 'False Color', ''),
            ('Filmic sRGB', 'Filmic', ''),
            ('Filmic Log', 'Filmic Log', ''),
            ('Khronos PBR Neutral sRGB', 'PBR Neutral', ''),
            ('sRGB', 'Standard', ''),
        ]


view_transforms_enable = {
        'AgX': 'AgX Base sRGB',
        'False Color': 'False Color',
        'Filmic': 'Filmic sRGB',
        'Filmic Log': 'Filmic Log',
        'Standard': 'sRGB',
        'Raw': 'AgX Base sRGB',
        'Khronos PBR Neutral': 'Khronos PBR Neutral sRGB'
    }

view_transforms_disable = {
        'ACEScg': 'AgX',
        'ACES2065-1': 'AgX',
        'AgX Base sRGB': 'AgX',
        'AgX Log': 'AgX',
        'False Color': 'False Color',
        'Filmic sRGB': 'Filmic',
        'Filmic Log': 'Filmic Log',
        'Khronos PBR Neutral sRGB': 'Khronos PBR Neutral',
        'sRGB': 'Standard'
    }


def update_view_transform(self, context, RR_group=None, RR_node=None):
    RR = get_settings(context, RR_group)

    transform = RR.props_group.view_transform

    if transform == 'False Color':
        context.scene.view_settings.view_transform = 'False Color'
    else:
        context.scene.view_settings.view_transform = 'Raw'
        for node in RR.nodes_group:
            if 'Convert Colorspace' in node.name:
                node.to_color_space = transform

    for node in RR.nodes_with_group:
        node.mute = transform == 'False Color'

    for node in RR.nodes_group:
        if 'ACES Gamma' in node.name:
            node.mute = transform != 'ACEScg'

    for layer_idx in range(len(RR.nodes_layers['Post']) - 1):
        update_preserve_color(self, context, RR.group, layer_idx)