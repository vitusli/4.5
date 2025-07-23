import bpy, gpu

from ..utilities.layers import is_layer_used
from ..preferences import get_prefs
from .draw_tabs import draw_tabs
from .draw_upgrade import draw_upgrade_panel


def draw_color_management(self, context, RR):
    PREFS = get_prefs(context)
    VIEW = context.scene.view_settings

    col = self.layout.column()
    col.use_property_split = True
    col.use_property_decorate = False

    if (
        (RR.props_scene.enable_RR and not RR.group) or 
        (RR.props_scene.enable_RR and not RR.in_scene) or
        (RR.props_scene.enable_RR and RR.is_legacy) or
        (not RR.props_scene.enable_RR and context.scene.render_raw.enable_RR)
    ):
        draw_upgrade_panel(self, col, context, RR)
        return
    
    row = col.row(heading='Color Correction')
    row.prop(RR.props_scene, 'enable_RR', text='Render Raw')
    col.separator()

    if (
        RR.props_scene.enable_RR and
        not PREFS.enable_layers and
        len(RR.groups) > 1 and
        RR.group != None
    ):
        row = col.row(align=True)
        row.prop(RR.props_scene, "active_group", icon="NODETREE", icon_only=True)
        row.prop(RR.group, 'name', text="")
        col.separator()

    elif RR.props_scene.enable_RR:
        col.prop(RR.props_group, 'view_transform')
        if not get_prefs(context).enable_layers:
            draw_layer_presets(col, RR)
        col.prop(RR.props_scene, 'exposure', slider=True)
        col.prop(RR.props_scene, 'gamma', slider=True)

    else:
        col.prop(VIEW, 'view_transform')
        col.prop(VIEW, 'look')
        col.prop(VIEW, 'exposure')
        col.prop(VIEW, 'gamma')


""" Layers """


def draw_layer_presets(col, RR):
    row = col.row()
    row.enabled = RR.props_pre.use_layer
    row.prop(RR.props_pre, 'preset', text='Preset')
    #row.separator()
    row.menu('RENDER_MT_render_raw_preset_options', icon='OPTIONS', text='')


def draw_layers(self, RR):
    col = self.layout.column()
    col.use_property_split = True
    col.use_property_decorate = False
    col.enabled = RR.props_scene.enable_RR

    #col.operator('render.render_raw_refresh_layers', icon='FILE_REFRESH')
    if len(RR.groups) > 1 and RR.group != None:
        row = col.row(align=True)
        row.prop(RR.props_scene, "active_group", icon="NODETREE", icon_only=True)
        row.prop(RR.group, 'name', text="")
        col.separator()

    row = col.row()
    row.template_list(
        listtype_name="RENDER_UL_render_raw_layers",
        list_id="",
        dataptr=RR.group, # Main datablock
        propname="render_raw_layers", # Collection property group that becomes the list
        active_dataptr=RR.props_group, # Pointer property group that stores the active index
        active_propname="active_layer_index", # integer index
        rows=4,
        sort_reverse=True
    )

    actions = row.column(align=True)
    actions.operator('render.render_raw_add_layer', icon='ADD', text='')
    actions.operator('render.render_raw_remove_layer', icon='REMOVE', text='')
    actions.separator()
    #actions.operator('', icon='DOWNARROW_HLT', text='')
    #actions.operator('render.render_raw_refresh_layers', icon='FILE_REFRESH', text='')
    actions.separator()
    actions.operator('render.render_raw_move_layer', icon='TRIA_UP', text='').direction='UP'
    actions.operator('render.render_raw_move_layer', icon='TRIA_DOWN', text='').direction='DOWN'

    col.separator()

    if RR.props_layers.keys():
        col.prop(RR.props_pre, 'layer_name')
        draw_layer_presets(col, RR)
        row = col.row()
        row.enabled = RR.props_pre.use_layer
        row.prop(RR.props_pre, 'layer_factor', slider=True)


""" Values """


def draw_curves(context, layout, RR):
    header, panel = layout.panel(idname='RR_curves_panel', default_closed=True)
    header.label(text="Curves")
    if panel:
        panel.use_property_split = False
        draw_tabs(panel, RR.props_group, 'display_curves')
        col = panel.column(align=True)
        col.enabled = RR.use_values

        if RR.props_group.display_curves == 'PRE':
            col.row().prop(RR.props_pre, 'pre_curves_tone', text='')
            col.separator()
            col.template_curve_mapping(
                RR.nodes_pre['Curves'], "mapping", type='COLOR', levels=False, show_tone=False
            )
            row = col.row(align=True)
            row.prop(RR.props_pre, 'pre_curves_black', text='')
            row.prop(RR.props_pre, 'pre_curves_white', text='')
            col.separator()
            col.prop(RR.props_pre, 'pre_curves_factor', text='Factor', slider=True)

        elif RR.props_group.display_curves == 'POST':
            col.row().prop(RR.props_pre, 'post_curves_tone', text='')
            col.separator()
            col.template_curve_mapping(
                RR.nodes_post['Curves'], "mapping", type='COLOR', levels=False, show_tone=False
            )
            row = col.row(align=True)
            row.prop(RR.props_post, 'post_curves_black', text='')
            row.prop(RR.props_post, 'post_curves_white', text='')
            col.separator()
            col.prop(RR.props_post, 'post_curves_factor', text='Factor', slider=True)


def draw_details(layout, props_pre, props_post):
    header, panel = layout.panel(idname='RR_details_panel', default_closed=True)
    header.label(text="Details")
    if panel:
        col = panel.column(align=True)
        col.enabled = props_pre.use_values
        col.prop(props_post, 'sharpness', slider=True)
        col.prop(props_post, 'sharpness_mask', slider=True, text='Mask')
        col.separator()
        col.prop(props_post, 'texture', slider=True)
        col.separator()
        col.prop(props_post, 'clarity', slider=True)
        col.prop(props_post, 'clarity_size', slider=True)


def draw_values(self, context, RR):
    layout = self.layout
    layout.use_property_split = True
    layout.use_property_decorate = False

    col = layout.column(align=True)
    col.enabled = RR.use_values and is_layer_used(RR)

    if get_prefs(context).enable_layers:
        col.prop(RR.props_pre, 'exposure', slider=True)
        col.prop(RR.props_pre, 'gamma', slider=True)
    col.prop(RR.props_pre, 'contrast', slider=True)
    col2 = col.column(align=True)
    col2.separator()
    col2.prop(RR.props_post, 'blacks', slider=True)
    col2.prop(RR.props_post, 'shadows', slider=True)
    col2.prop(RR.props_post, 'highlights', slider=True)
    col2.prop(RR.props_post, 'whites', slider=True)
    col.separator()
    col.prop(RR.props_post, 'fix_clipping', slider=True)
    col.separator()

    draw_details(layout, RR.props_pre, RR.props_post)
    draw_curves(context, layout, RR)


""" Colors """

def draw_color_balance(layout, props_pre, props_post):
    header, panel = layout.panel(idname='RR_color_balance_panel', default_closed=True)
    header.label(text="Color Balance")
    if panel:
        col = panel.column(align=True)
        col.enabled = props_pre.use_colors
        col.prop(props_pre, 'offset_color')
        col.prop(props_pre, 'power_color')
        col.prop(props_pre, 'slope_color')
        col.separator()
        col.prop(props_post, 'lift_color')
        col.prop(props_post, 'gamma_color')
        col.prop(props_post, 'gain_color')

"""

def draw_color_blending(layout, props, layer_nodes):
    BALANCE_NODES = layer_nodes['Color Balance'].node_tree.nodes

    header, panel = layout.panel(idname='RR_color_blending_panel', default_closed=True)
    header.label(text="Color Blending")
    if panel:
        col = panel.column()
        col.prop(BALANCE_NODES['Shadow Color'], 'blend_type', text='Shadow Blend')
        col.prop(props, 'shadow_color')
        col.prop(props, 'shadow_range', slider=True)
        col.prop(props, 'shadow_factor', slider=True)
        col.separator()
        col.prop(BALANCE_NODES['Midtone Color'], 'blend_type', text='Midtone Blend')
        col.prop(props, 'midtone_color')
        col.prop(props, 'midtone_range', slider=True)
        col.prop(props, 'midtone_factor', slider=True)
        col.separator()
        col.prop(BALANCE_NODES['Highlight Color'], 'blend_type', text='Highlight Blend')
        col.prop(props, 'highlight_color')
        col.prop(props, 'highlight_range', slider=True)
        col.prop(props, 'highlight_factor', slider=True)


def draw_hue_hue(layout, props):
    header, panel = layout.panel(idname='RR_hue_hue_panel', default_closed=True)
    header.label(text="Hue / Hue")
    if panel:
        col = panel.column()
        col.prop(props, 'red_hue', slider=True)
        col.prop(props, 'orange_hue', slider=True)
        col.prop(props, 'yellow_hue', slider=True)
        col.prop(props, 'green_hue', slider=True)
        col.prop(props, 'teal_hue', slider=True)
        col.prop(props, 'blue_hue', slider=True)
        col.prop(props, 'pink_hue', slider=True)


def draw_hue_saturation(layout, props):
    header, panel = layout.panel(idname='RR_hue_saturation_panel', default_closed=True)
    header.label(text="Hue / Saturation")
    if panel:
        col = panel.column()
        col.prop(props, 'red_saturation', slider=True)
        col.prop(props, 'orange_saturation', slider=True)
        col.prop(props, 'yellow_saturation', slider=True)
        col.prop(props, 'green_saturation', slider=True)
        col.prop(props, 'teal_saturation', slider=True)
        col.prop(props, 'blue_saturation', slider=True)
        col.prop(props, 'pink_saturation', slider=True)


def draw_hue_value(layout, props):
    header, panel = layout.panel(idname='RR_hue_value_panel', default_closed=True)
    header.label(text="Hue / Value")
    if panel:
        col = panel.column()
        col.prop(props, 'red_value', slider=True)
        col.prop(props, 'orange_value', slider=True)
        col.prop(props, 'yellow_value', slider=True)
        col.prop(props, 'green_value', slider=True)
        col.prop(props, 'teal_value', slider=True)
        col.prop(props, 'blue_value', slider=True)
        col.prop(props, 'pink_value', slider=True)


def draw_value_saturation(layout, props):
    header, panel = layout.panel(idname='RR_value_saturation_panel', default_closed=True)
    header.label(text="Value / Saturation")
    if panel:
        col = panel.column()
        col.prop(props, 'shadow_saturation', slider=True)
        col.prop(props, 'shadow_saturation_range', slider=True)
        col.separator()
        col.prop(props, 'midtone_saturation', slider=True)
        col.prop(props, 'midtone_saturation_range', slider=True)
        col.separator()
        col.prop(props, 'highlight_saturation', slider=True)
        col.prop(props, 'highlight_saturation_range', slider=True)
        col.separator()
        col.prop(props, 'value_saturation_perceptual', slider=True)

"""

def draw_per_hue(layout, props_node, props_pre, props_post):
    header, panel = layout.panel(idname='RR_per_hue_panel', default_closed=True)
    header.label(text="Per Hue")
    if panel:
        col = panel.column(align=True)
        col.enabled = props_pre.use_colors
        draw_tabs(col, props_node, 'display_per_hue')
        col.separator()
        if props_node.display_per_hue == 'HUE':
            col.prop(props_post, 'red_hue', slider=True)
            col.prop(props_post, 'orange_hue', slider=True)
            col.prop(props_post, 'yellow_hue', slider=True)
            col.prop(props_post, 'green_hue', slider=True)
            col.prop(props_post, 'teal_hue', slider=True)
            col.prop(props_post, 'blue_hue', slider=True)
            col.prop(props_post, 'pink_hue', slider=True)
        elif props_node.display_per_hue == 'SATURATION':
            col.prop(props_post, 'red_saturation', slider=True)
            col.prop(props_post, 'orange_saturation', slider=True)
            col.prop(props_post, 'yellow_saturation', slider=True)
            col.prop(props_post, 'green_saturation', slider=True)
            col.prop(props_post, 'teal_saturation', slider=True)
            col.prop(props_post, 'blue_saturation', slider=True)
            col.prop(props_post, 'pink_saturation', slider=True)
        elif props_node.display_per_hue == 'VALUE':
            col.prop(props_post, 'red_value', slider=True)
            col.prop(props_post, 'orange_value', slider=True)
            col.prop(props_post, 'yellow_value', slider=True)
            col.prop(props_post, 'green_value', slider=True)
            col.prop(props_post, 'teal_value', slider=True)
            col.prop(props_post, 'blue_value', slider=True)
            col.prop(props_post, 'pink_value', slider=True)
        if bpy.app.version >= (4, 5, 0):
            col.separator(type='LINE', factor=2)
            col.prop(props_post, 'hue_perceptual', slider=True)
            col.prop(props_post, 'hue_range', slider=True)
            col.prop(props_post, 'hue_smoothing', slider=True)
            col.separator()
            col.prop(props_post, 'hue_saturation_mask', text='Saturation Mask', slider=True)
            col.prop(props_post, 'hue_value_mask', text='Value Mask', slider=True)


def draw_per_value(layout, props_node, props_pre, props_post, nodes_post):
    header, panel = layout.panel(idname='RR_per_value_panel', default_closed=True)
    header.label(text="Per Value")
    if panel:
        col = panel.column(align=True)
        col.enabled = props_pre.use_colors
        draw_tabs(col, props_node, 'display_per_value')
        col.separator()
        if props_node.display_per_value == 'SATURATION':
            col.prop(props_post, 'shadow_saturation', slider=True)
            col.prop(props_post, 'shadow_saturation_range', slider=True)
            col.separator()
            col.prop(props_post, 'midtone_saturation', slider=True)
            col.prop(props_post, 'midtone_saturation_range', slider=True)
            col.separator()
            col.prop(props_post, 'highlight_saturation', slider=True)
            col.prop(props_post, 'highlight_saturation_range', slider=True)
            col.separator()
            col.prop(props_post, 'value_saturation_perceptual', slider=True)
        elif props_node.display_per_value == 'BLENDING':
            BALANCE_NODES = nodes_post['Color Blending'].node_tree.nodes
            col.prop(BALANCE_NODES['Shadow Color'], 'blend_type', text='Shadow Blend')
            col.prop(props_post, 'shadow_color')
            col.prop(props_post, 'shadow_range', slider=True)
            col.prop(props_post, 'shadow_factor', slider=True)
            col.separator()
            col.prop(BALANCE_NODES['Midtone Color'], 'blend_type', text='Midtone Blend')
            col.prop(props_post, 'midtone_color')
            col.prop(props_post, 'midtone_range', slider=True)
            col.prop(props_post, 'midtone_factor', slider=True)
            col.separator()
            col.prop(BALANCE_NODES['Highlight Color'], 'blend_type', text='Highlight Blend')
            col.prop(props_post, 'highlight_color')
            col.prop(props_post, 'highlight_range', slider=True)
            col.prop(props_post, 'highlight_factor', slider=True)


def draw_preserve_color(layout, RR):
    header, panel = layout.panel(idname='RR_preserve_color_panel', default_closed=True)
    header.label(text="Tone Mapping")
    if panel:
        col = panel.column(align=True)
        col.enabled = RR.props_pre.use_colors
        col.prop(RR.props_post, 'preserve_filmic', text='Filmic', slider=True)
        col.separator()
        col.prop(RR.props_post, 'preserve_hue', text='sRGB Hue', slider=True)
        col.prop(RR.props_post, 'preserve_saturation', text='Saturation', slider=True)
        col.separator()
        col.prop(RR.props_post, 'preserve_cutoff', text='Highlight Cutoff')
        col.prop(RR.props_post, 'preserve_spread', text='Spread', slider=True)


def draw_colors(self, RR):
    layout = self.layout
    layout.use_property_split = True
    layout.use_property_decorate = False
    col = layout.column(align=True)
    col.enabled = RR.use_colors and is_layer_used(RR)

    col.prop(RR.props_pre, 'temperature', slider=True)
    col.prop(RR.props_pre, 'tint', slider=True)
    if bpy.app.version >= (4, 3, 0):
        col.prop(RR.props_pre, 'white_balance_perceptual', slider=True)
    col.separator()
    col.prop(RR.props_pre, 'color_boost', slider=True)
    col.separator()
    col.prop(RR.props_post, 'saturation', slider=True)
    col.prop(RR.props_post, 'saturation_perceptual', slider=True)
    col.separator()

    draw_color_balance(layout, RR.props_pre, RR.props_post)
    draw_per_hue(layout, RR.props_group, RR.props_pre, RR.props_post)
    draw_per_value(layout, RR.props_group, RR.props_pre, RR.props_post, RR.nodes_post)
    draw_preserve_color(layout, RR)


""" Effects """

def draw_glare(layout, props, is_enabled):
    header, panel = layout.panel(idname='RR_glare_panel', default_closed=True)
    header.label(text="Glare")
    if not panel:
        row = header.row()
        row.enabled = is_enabled
        row.prop(props, 'glare', slider=True, text='')
    else:
        col = panel.column()
        col.enabled = is_enabled
        col.prop(props, 'glare', slider=True, text='Strength')

        glare = col.column(align=True)
        glare.enabled = props.glare != 0
        col2 = glare.column()
        col2.prop(props, 'glare_threshold')
        if bpy.app.version >= (4, 5, 0):
            col2.prop(props, 'bloom_saturation', text='Saturation', slider=True)
            col2.prop(props, 'bloom_tint', text='Tint')
        else:
            col2.prop(props, 'glare_quality')
        col2.separator()

        glare.prop(props, 'bloom', slider=True, text='Bloom')
        bloom = glare.column(align=True)
        bloom.enabled = props.glare != 0 and props.bloom != 0
        if bpy.app.version >= (4, 5, 0):
            bloom.prop(props, 'bloom_size_float', text='Size', slider=True)
        elif bpy.app.version >= (4, 4, 0):
            bloom.prop(props, 'bloom_size_float', text='Size', slider=True)
            bloom.prop(props, 'bloom_saturation', text='Saturation', slider=True)
            bloom.prop(props, 'bloom_tint', text='Tint')
        elif bpy.app.version >= (4, 2, 0) and bpy.app.version < (4, 4, 0):
            bloom.prop(props, 'bloom_size', text='Size')
        glare.separator()

        glare.prop(props, 'streaks', slider=True, text='Streaks')
        streaks = glare.column(align=True)
        streaks.enabled = props.glare != 0 and props.streaks != 0
        streaks.prop(props, 'streak_length', slider=True, text='Length')
        streaks.prop(props, 'streak_count', text='Count')
        streaks.prop(props, 'streak_angle', text='Angle')
        glare.separator()

        glare.prop(props, 'ghosting', slider=True)

        col.separator()


def draw_vignette(layout, props, is_enabled):
    header, panel = layout.panel(idname='RR_vignette_panel', default_closed=True)
    header.label(text="Vignette")
    if not panel:
        row = header.row()
        row.enabled = is_enabled
        row.prop(props, 'vignette_factor', slider=True, text='')
    else:
        col = panel.column()
        col.enabled = is_enabled
        col.prop(props, 'vignette_factor', slider=True, text='Factor')
        vig = col.column()
        vig.enabled = props.vignette_factor != 0 
        vig.prop(props, 'vignette_color')
        vig.prop(props, 'vignette_linear_blend', text='Blending', slider=True)

        vig.prop(props, 'vignette_highlights', slider=True)
        vig.prop(props, 'vignette_feathering', slider=True)
        vig.prop(props, 'vignette_roundness', slider=True)

        scale = vig.column(align=True)
        scale.prop(props, 'vignette_scale_x', slider=True)
        scale.prop(props, 'vignette_scale_y', slider=True, text='Y')

        vig.prop(props, 'vignette_rotation', slider=True)

        shift = vig.column(align=True)
        shift.prop(props, 'vignette_shift_x', slider=True)
        shift.prop(props, 'vignette_shift_y', slider=True, text='Y')




def draw_grain(layout, props, is_enabled):
    header, panel = layout.panel(idname='RR_grain_panel', default_closed=True)
    header.label(text="Film Grain")
    if not panel:
        row = header.row()
        row.enabled = is_enabled
        row.prop(props, 'grain', slider=True, text='')
    else:
        col = panel.column()
        col.enabled = is_enabled
        col.prop(props, 'grain', slider=True, text='Strength')

        grain = col.column()
        grain.enabled = props.grain != 0

        row = grain.row()
        row.prop(props, 'grain_method', expand=True)
        grain.prop(props, 'grain_scale', slider=True)
        grain.prop(props, 'grain_saturation', slider=True)
        grain.prop(props, 'grain_steps')

        if bpy.app.version < (4, 5, 0):
            grain.prop(props, 'grain_aspect', slider=True)

        row = grain.row(heading='Animate')
        row.prop(props, 'grain_is_animated', text='')


def draw_effects(self, RR):
    is_enabled = RR.use_effects and is_layer_used(RR)

    layout = self.layout
    layout.use_property_split = True
    layout.use_property_decorate = False
    col = layout.column(align=True)
    col.enabled = is_enabled

    col.prop(RR.props_post, 'distortion', slider=True)
    col.prop(RR.props_post, 'dispersion', slider=True)

    col.separator()

    draw_glare(layout, RR.props_pre, is_enabled)
    draw_vignette(layout, RR.props_post, is_enabled)
    draw_grain(layout, RR.props_post, is_enabled)


""" Utilities """

def draw_overlays_panel(layout, props):
    header, panel = layout.panel(idname='RR_overlays_panel', default_closed=False)
    header.label(text="Overlays")
    if panel:
        row = panel.row(heading='Clipping', align=False)
        row.prop(props, 'use_clipping', text='')
        row2 = row.row(align=True)
        row2.enabled = props.use_clipping
        row2.prop(props, 'clipping_blacks', text='')
        row2.prop(props, 'clipping_whites', text='')
        row2.prop(props, 'clipping_saturation', text='')
        row.popover('RENDER_PT_render_raw_clipping', icon='OPTIONS', text='')


def draw_display_panel(layout, props):
    header, panel = layout.panel(idname='scene_display_panel', default_closed=False)
    header.label(text="Display")
    if panel:
        hdr = panel.row()
        hdr.enabled = gpu.capabilities.hdr_support_get()
        hdr.prop(props, 'use_hdr_view')


def draw_alpha_panel(layout, props):
    header, panel = layout.panel(idname='RR_alpha_panel', default_closed=False)
    header.label(text="Alpha")
    if panel:
        panel.prop(props, 'alpha_method')
        panel.prop(props, 'alpha_factor', slider=True)


def draw_compositor_panel(layout, context):
    header, panel = layout.panel(idname='scene_compositor_panel', default_closed=False)
    header.label(text="Compositor")
    if panel:
        if context.area.type == 'VIEW_3D':
            panel.prop(context.space_data.shading, 'use_compositor', text='Viewport')
        if bpy.app.version >= (4, 2, 0):
            device = panel.row()
            device.prop(context.scene.render, 'compositor_device', text='Render', expand=True)


def draw_utilities(self, context, RR):
    VIEW = context.scene.view_settings

    layout = self.layout
    layout.use_property_split = True
    layout.use_property_decorate = False

    draw_overlays_panel(layout, RR.props_group)

    draw_alpha_panel(layout, RR.props_group)

    if RR.props_group.view_transform == 'sRGB':
        draw_display_panel(layout, VIEW)

    draw_compositor_panel(layout, context)

    header, panel = layout.panel(idname='scene_nodes_panel', default_closed=True)
    header.label(text="Nodes")
    if panel:
        panel.operator('render.render_raw_duplicate_active', icon='DUPLICATE')
        panel.operator('render.render_raw_unlink_active', icon='UNLINKED')
        panel.operator('render.render_raw_refresh_nodes', icon='FILE_REFRESH')

    header, panel = layout.panel(idname='scene_values_panel', default_closed=True)
    header.label(text="Actual Scene Values")
    if panel:
        panel.prop(VIEW, 'view_transform', text="Transform")
        panel.prop(VIEW, 'look', text="Look")
        panel.prop(VIEW, 'exposure', text="Exposure")
        panel.prop(VIEW, 'gamma', text="Gamma")
        panel.separator()
        panel.operator('render.render_raw_fix_scene_settings', icon='FILE_REFRESH')

    header, panel = layout.panel(idname='help_panel', default_closed=True)
    header.label(text="Documentation and Help")
    if panel:
        panel.operator(
            'wm.url_open', text='Read the Docs', icon='HELP'
        ).url = 'https://cgcookie.github.io/render_raw/'
        panel.operator(
            'wm.url_open', text='Report an Issue', icon='ERROR'
        ).url = 'https://orangeturbine.com/#contact'
        panel.operator(
            "wm.url_open", text='View on Blender Market', icon='IMPORT'
        ).url = 'https://blendermarket.com/products/render-raw'
