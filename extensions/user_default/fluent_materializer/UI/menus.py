import bpy
from bpy_types import Menu

from .. import tasks_queue
from ..Tools.helper import load_icons, init_libraries_previews, get_addon_preferences, get_version_from_manifest
from ..operators import FLUENT_SHADER_OT_FindHelp, FLUENT_SHADER_OT_addNodes, \
    FLUENT_SHADER_OT_SwapLayers, FLUENT_SHADER_OT_LayerMixLayersConnect, FLUENT_SHADER_OT_Localmask, \
    FLUENT_SHADER_OT_NewPaintedMask, FLUENT_SHADER_OT_EditPaintedMask, FLUENT_SHADER_OT_OpenFilebrowser, \
    FLUENT_SHADER_OT_NewDecal, FLUENT_SHADER_OT_SynchronizeDecal, FLUENT_SHADER_OT_NodeCounter, \
    FLUENT_SHADER_OT_ImageExtractor, FLUENT_SHADER_OT_SearchIOR, FLUENT_SHADER_OT_HeightGradient, \
    FLUENT_SHADER_OT_SampleEditor, FLUENT_SHADER_OT_AttributeReader

from ..bake import FLUENT_OT_BakeMask

init_done = False
nb_version = get_version_from_manifest()


class FLUENT_SHADER_PT_ViewPanel(bpy.types.Panel):
    "Fluent Shader Editor"
    bl_label = "Materializer"
    bl_name = "Materializer"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = 'Fluent'

    def draw_header(self, context: bpy.types.Context):
        icons = load_icons()
        self.layout.label(text="", icon_value=icons.get("materializer_icon").icon_id)

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        row = box.row()
        props = context.scene.FluentShaderProps
        row.prop(props, 'show_bake_setting',
                 icon="TRIA_DOWN" if props.show_bake_setting else "TRIA_RIGHT",
                 icon_only=True, emboss=False
                 )
        row.label(text="Bake settings")
        if props.show_bake_setting:
            selection_col = box.column(align=True)
            selection_col.prop(props, 'map_size')
            selection_col.prop(props, 'bake_sample')
            selection_col.prop(props, 'bake_margin')
            selection_col.prop(props, 'bake_custom_colorspace')
            selection_col.prop(props, 'bake_image_format')
            selection_col.prop(props, 'udim_baking')
            selection_col.prop(props, 'udim_count')

        box = layout.box()
        row = box.row()
        row.prop(props, 'show_bake_pbr',
                 icon="TRIA_DOWN" if props.show_bake_pbr else "TRIA_RIGHT",
                 icon_only=True, emboss=False
                 )
        row.label(text="Bake PBR")
        if props.show_bake_pbr:
            selection_col = box.column(align=True)
            if props.is_baking:
                selection_col.label(text='Bake in progress')
                selection_col.operator('fluent.reset_baking')
                return

            if props.baking_error != '':
                selection_col.label(text='Error during baking', icon="ERROR")
                selection_col.label(text=props.baking_error)
                selection_col.operator('fluent.reset_baking')
                return

            selection_col.prop(props, 'bake_in_image')
            selection_col.prop(props, 'bake_make_color')
            selection_col.prop(props, 'bake_make_metallic')
            selection_col.prop(props, 'bake_make_roughness')
            selection_col_row = selection_col.row()
            selection_col_row.prop(props, 'bake_make_normal')
            selection_col_row.prop(props, 'bake_normal_directx')
            selection_col.prop(props, 'bake_make_emission')
            selection_col.prop(props, 'bake_make_ao')
            selection_col.prop(props, 'bake_make_alpha')
            selection_col.separator()
            selection_col.prop(props, 'bake_auto_set')
            selection_col.separator()

            low_high_box = selection_col.box()
            lh_col = low_high_box.column(align=True)
            lh_col.prop(props, 'bake_make_selected_to_active')
            if props.bake_make_selected_to_active:
                lh_col.prop(props, 'bake_use_cage')
                lh_col.prop(props, 'bake_cage_object')
                lh_col.prop(props, 'bake_make_selected_to_active_extrusion')

            selection_col = box.column(align=True)
            combine_channel_box = selection_col.box()
            comb_col = combine_channel_box.column(align=True)
            comb_col.prop(props, 'bake_combine_channels')
            if props.bake_combine_channels:
                comb_col.prop(props, 'bake_red_channel')
                comb_col.prop(props, 'bake_green_channel')
                comb_col.prop(props, 'bake_blue_channel')

            selection_col = box.column()
            selection_col.scale_y = 1.5
            if get_addon_preferences().bake_background:
                selection_col.operator('fluent.bakepbrmaps', text='Bake PBR maps')
            else:
                selection_col.operator('fluent.bakepbrmapsforeground', text='Bake PBR maps')

        box = layout.box()
        row = box.row()
        row.prop(props, 'show_bake_mask',
                 icon="TRIA_DOWN" if props.show_bake_mask else "TRIA_RIGHT",
                 icon_only=True, emboss=False
                 )
        row.label(text="Bake masks")
        if props.show_bake_mask:
            selection_col = box.column(align=True)
            selection_col.operator(FLUENT_OT_BakeMask.bl_idname, text='All edges and cavity').choice = 'ALL'
            selection_col.operator(FLUENT_OT_BakeMask.bl_idname, text='Only edges').choice = 'EDGES'
            selection_col.operator(FLUENT_OT_BakeMask.bl_idname, text='Only cavity').choice = 'CAVITY'
            selection_col.operator(FLUENT_OT_BakeMask.bl_idname, text='Only selected nodes').choice = 'SELECTED'

        # box = layout.box()
        # row = box.row()
        # row.prop(context.scene.FluentShaderProps, 'show_bake_decal',
        #          icon="TRIA_DOWN" if context.scene.FluentShaderProps.show_bake_decal else "TRIA_RIGHT",
        #          icon_only=True, emboss=False
        #          )
        # row.label(text="Decals")
        # if context.scene.FluentShaderProps.show_bake_decal:
        #     selection_col = box.column(align=True)
        #     selection_col.operator(FLUENT_SHADER_OT_MoveDecal.bl_idname, text='Move decal')

        layout.operator(FLUENT_SHADER_OT_FindHelp.bl_idname, text='Help', icon='HELP')


class FLUENT_SHADER_PT_Library(bpy.types.Panel):
    "Fluent node library"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Fluent'
    bl_label = 'Library'

    @classmethod
    def poll(cls, context):
        if (context.space_data.tree_type == "ShaderNodeTree" and context.space_data.shader_type == "OBJECT"):
            return True
        else:
            return False

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        if context.scene.render.engine not in ["CYCLES", "BLENDER_EEVEE_NEXT"]:
            row.label(text="Only Cycles / Eevee supported")
        else:
            if context.space_data.tree_type == "ShaderNodeTree" and context.space_data.shader_type == "OBJECT":
                if not context.material:
                    row.label(text="Add Material")
                elif not context.material.node_tree:
                    row.label(text="Enable Nodes")
                else:
                    layout = self.layout
                    layout.prop(context.scene.FluentShaderProps, 'scale_scale')
                    layout.prop(context.scene.FluentShaderProps, 'sections')
                    layout.template_icon_view(
                        bpy.context.window_manager, "fm_%s" % context.scene.FluentShaderProps.sections,
                        show_labels=True)
                    layout.operator(FLUENT_SHADER_OT_addNodes.bl_idname,
                                    text="Add").choice = context.scene.FluentShaderProps.sections


class FLUENT_SHADER_MT_Pie_Menu(bpy.types.Menu):
    bl_label = 'Fluent MZ ' + nb_version

    @classmethod
    def poll(cls, context):
        return (bpy.context.area.ui_type == 'ShaderNodeTree')

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()

        LEFT = pie.column()
        LEFT.label(text='Layers')
        box = LEFT.column()
        box.scale_x = 1.2
        box.scale_y = 1.5
        box.operator(FLUENT_SHADER_OT_addNodes.bl_idname, text="Mix layers").choice = "Mix Layers"
        row = box.row(align=True)
        row.operator(FLUENT_SHADER_OT_addNodes.bl_idname, text="New layer").choice = "Layer"
        row.operator(FLUENT_SHADER_OT_SwapLayers.bl_idname, text="", icon="FILE_REFRESH")
        row.operator(FLUENT_SHADER_OT_LayerMixLayersConnect.bl_idname, text="", icon="LINKED")
        row = LEFT.row(align=True)
        row.operator(FLUENT_SHADER_OT_addNodes.bl_idname, text="2 layers").choice = "Smart Shader 2 layers"
        row.operator(FLUENT_SHADER_OT_addNodes.bl_idname, text="3 layers").choice = "Smart Shader 3 layers"

        RIGHT = pie.column()
        RIGHT.label(text='Masks')
        grid_flow = RIGHT.column(align=True)
        grid_flow.scale_y = 1.5
        grid_flow.operator(FLUENT_SHADER_OT_addNodes.bl_idname, text="WornOut Wizard", icon='EXPERIMENTAL').choice = "WornOut Wizard"

        self.draw_mask_menus(RIGHT)

        RIGHT = pie.column()
        RIGHT.label(text='Decals')
        bloc = RIGHT.column(align=True)
        line = bloc.row(align=True)
        op = line.operator(FLUENT_SHADER_OT_OpenFilebrowser.bl_idname, text='Basic', icon='IMAGE_DATA')
        op.continue_to = 'new_decal'
        op.call_worn_edges = False
        op = line.operator(FLUENT_SHADER_OT_OpenFilebrowser.bl_idname, text='Worn', icon='LIBRARY_DATA_BROKEN')
        op.continue_to = 'new_decal'
        op.call_worn_edges = True
        line = bloc.row(align=True)
        line.operator(FLUENT_SHADER_OT_addNodes.bl_idname, text='Mixer', icon='SELECT_EXTEND').choice = 'Decal Mixer'
        line = bloc.row(align=True)
        line.scale_x = 1.05
        line.operator(FLUENT_SHADER_OT_OpenFilebrowser.bl_idname, text='Normal', icon='ORIENTATION_NORMAL').continue_to = 'new_decal_normal'
        line.operator(FLUENT_SHADER_OT_addNodes.bl_idname, text='N Mixer', icon='SELECT_EXTEND').choice = 'normal_decals_mixer_4'
        line = bloc.row(align=True)
        line.operator(FLUENT_SHADER_OT_NewDecal.bl_idname, text='Duplicate', icon='DUPLICATE').duplicate = True
        line.operator(FLUENT_SHADER_OT_SynchronizeDecal.bl_idname, text='Sync', icon='UV_SYNC_SELECT')

        BOTTOM = pie.column()
        BOTTOM.label(text='Data')
        BOTTOM.menu("FLUENT_MT_Math_Menu", icon='TRIA_RIGHT')
        BOTTOM.menu("FLUENT_MT_Color_Menu", icon='TRIA_RIGHT')
        BOTTOM.operator(FLUENT_SHADER_OT_SearchIOR.bl_idname, text='Search IOR')

    def draw_mask_menus(self, pie_bloc):
        icons = load_icons()
        multiply_ico = icons.get("multiply")
        difference_ico = icons.get("difference")

        bloc = pie_bloc.column(align=True)
        if get_addon_preferences().use_favorites:
            line = bloc.row(align=True)
            line.menu("FLUENT_MT_Masks_Menu", icon='TRIA_RIGHT')
            line = bloc.row(align=True)
            line.label(text='Favorites')
            self.draw_mask_operator(bloc, get_addon_preferences().favorite_one, icons)
            self.draw_mask_operator(bloc, get_addon_preferences().favorite_two, icons)
            self.draw_mask_operator(bloc, get_addon_preferences().favorite_three, icons)
            self.draw_mask_operator(bloc, get_addon_preferences().favorite_four, icons)
            return

        line = bloc.row(align=True)
        line.operator(FLUENT_SHADER_OT_addNodes.bl_idname, text="Edges", icon='EDGESEL').choice = "Edges"
        line.operator(FLUENT_SHADER_OT_addNodes.bl_idname, text="Cavity", icon='SNAP_PERPENDICULAR').choice = "Cavity"
        line = bloc.row(align=True)
        line.operator(FLUENT_SHADER_OT_addNodes.bl_idname, text="All Edges").choice = "All edges"
        line.operator(FLUENT_SHADER_OT_addNodes.bl_idname, text="N Edge").choice = "normal_edge_mask_2"

        line = bloc.row(align=True)
        line.operator(FLUENT_SHADER_OT_addNodes.bl_idname, text="Slope", icon="IPO_EASE_IN_OUT").choice = "Slope"
        line.operator(FLUENT_SHADER_OT_addNodes.bl_idname, text="Altitude", icon="TRIA_UP_BAR").choice = "Altitude"
        line = bloc.row(align=True)
        line.operator(FLUENT_SHADER_OT_HeightGradient.bl_idname, text="Streaks", icon='SEQ_HISTOGRAM').refresh = False

        bloc = pie_bloc.column(align=True)
        line = bloc.row(align=True)
        line.operator(FLUENT_SHADER_OT_addNodes.bl_idname, text="Directional", icon="EMPTY_SINGLE_ARROW").choice = "Directional Mask"
        line = bloc.row(align=True)
        line.operator(FLUENT_SHADER_OT_Localmask.bl_idname, text="Local", icon='PIVOT_CURSOR')
        line = bloc.row(align=True)
        line.operator(FLUENT_SHADER_OT_AttributeReader.bl_idname, text="Color mask", icon="COLOR")
        line = bloc.row(align=True)
        line.operator(FLUENT_SHADER_OT_NewPaintedMask.bl_idname, text="Paint", icon="BRUSH_DATA").option = "Painted Mask"
        line.operator(FLUENT_SHADER_OT_NewPaintedMask.bl_idname, text="", icon_value=multiply_ico.icon_id).option = 'MULTIPLY'
        line.operator(FLUENT_SHADER_OT_NewPaintedMask.bl_idname, text="", icon_value=difference_ico.icon_id).option = 'DIFFERENCE'
        line.operator(FLUENT_SHADER_OT_EditPaintedMask.bl_idname, text="", icon="GP_MULTIFRAME_EDITING")

    def draw_mask_operator(self, bloc, operator_type, icons):
        if operator_type == 'NONE':
            return

        multiply_ico = icons.get("multiply")
        difference_ico = icons.get("difference")
        line = bloc.row(align=True)
        if operator_type == 'EDGES':
            line.operator(FLUENT_SHADER_OT_addNodes.bl_idname, text="Edges", icon='EDGESEL').choice = "Edges"
            return
        if operator_type == 'CAVITY':
            line.operator(FLUENT_SHADER_OT_addNodes.bl_idname, text="Cavity", icon='SNAP_PERPENDICULAR').choice = "Cavity"
            return
        if operator_type == 'ALL_EDGES':
            line.operator(FLUENT_SHADER_OT_addNodes.bl_idname, text="All Edges").choice = "All edges"
            return
        if operator_type == 'N_EDGES':
            line.operator(FLUENT_SHADER_OT_addNodes.bl_idname, text="N Edge").choice = "normal_edge_mask_2"
            return
        if operator_type == 'SLOPE':
            line.operator(FLUENT_SHADER_OT_addNodes.bl_idname, text="Slope", icon="IPO_EASE_IN_OUT").choice = "Slope"
            return
        if operator_type == 'ALTITUDE':
            line.operator(FLUENT_SHADER_OT_addNodes.bl_idname, text="Altitude", icon="TRIA_UP_BAR").choice = "Altitude"
            return
        if operator_type == 'STREAKS':
            line.operator(FLUENT_SHADER_OT_HeightGradient.bl_idname, text="Streaks", icon='SEQ_HISTOGRAM').refresh = False
            return
        if operator_type == 'DIRECTIONAL':
            line.operator(FLUENT_SHADER_OT_addNodes.bl_idname, text="Directional", icon="EMPTY_SINGLE_ARROW").choice = "Directional Mask"
            return
        if operator_type == 'LOCAL':
            line.operator(FLUENT_SHADER_OT_Localmask.bl_idname, text="Local", icon='PIVOT_CURSOR')
            return
        if operator_type == 'PAINT':
            line.operator(FLUENT_SHADER_OT_NewPaintedMask.bl_idname, text="Paint", icon="BRUSH_DATA").option = "Painted Mask"
            line.operator(FLUENT_SHADER_OT_NewPaintedMask.bl_idname, text="", icon_value=multiply_ico.icon_id).option = 'MULTIPLY'
            line.operator(FLUENT_SHADER_OT_NewPaintedMask.bl_idname, text="", icon_value=difference_ico.icon_id).option = 'DIFFERENCE'
            line.operator(FLUENT_SHADER_OT_EditPaintedMask.bl_idname, text="", icon="GP_MULTIFRAME_EDITING")
            return
        if operator_type == 'COLOR':
            line.operator(FLUENT_SHADER_OT_AttributeReader.bl_idname, text="Color mask", icon="COLOR")


class FLUENT_MT_Color_Menu(Menu):
    bl_label = "Metals colors"

    def draw(self, context):
        layout = self.layout
        layout.operator(FLUENT_SHADER_OT_addNodes.bl_idname, text="Iron").choice = "Iron"
        layout.operator(FLUENT_SHADER_OT_addNodes.bl_idname, text="Aluminium").choice = "Aluminium"
        layout.operator(FLUENT_SHADER_OT_addNodes.bl_idname, text="Gold").choice = "Gold"
        layout.operator(FLUENT_SHADER_OT_addNodes.bl_idname, text="Platinium").choice = "Platinium"
        layout.operator(FLUENT_SHADER_OT_addNodes.bl_idname, text="Copper").choice = "Copper"
        layout.operator(FLUENT_SHADER_OT_addNodes.bl_idname, text="CuO").choice = "CuO"
        layout.operator(FLUENT_SHADER_OT_addNodes.bl_idname, text="Brass").choice = "Brass"
        layout.operator(FLUENT_SHADER_OT_addNodes.bl_idname, text="Silver").choice = "Silver"


class FLUENT_MT_Math_Menu(Menu):
    bl_label = "Maths"

    def draw(self, context):
        layout = self.layout
        layout.operator(FLUENT_SHADER_OT_addNodes.bl_idname, text="Screen").choice = "Screen"
        layout.operator(FLUENT_SHADER_OT_addNodes.bl_idname, text="Lighten").choice = "Lighten"
        layout.operator(FLUENT_SHADER_OT_addNodes.bl_idname, text="Overlay").choice = "Overlay"
        layout.operator(FLUENT_SHADER_OT_addNodes.bl_idname, text="Difference").choice = "Difference"
        layout.operator(FLUENT_SHADER_OT_addNodes.bl_idname, text="Multiply").choice = "Multiply"
        layout.operator(FLUENT_SHADER_OT_addNodes.bl_idname, text="Math Mix").choice = "Math Mix"
        layout.operator(FLUENT_SHADER_OT_addNodes.bl_idname, text="Shift/Sharpen").choice = "Shift/Sharpen"
        layout.operator(FLUENT_SHADER_OT_addNodes.bl_idname, text="Invert").choice = "Invert"


class FLUENT_MT_Masks_Menu(Menu):
    bl_label = "Masks list"

    def draw(self, context):
        icons = load_icons()
        multiply_ico = icons.get("multiply")
        difference_ico = icons.get("difference")

        layout = self.layout
        layout.operator(FLUENT_SHADER_OT_addNodes.bl_idname, text="Edges", icon='EDGESEL').choice = "Edges"
        layout.operator(FLUENT_SHADER_OT_addNodes.bl_idname, text="Cavity", icon='SNAP_PERPENDICULAR').choice = "Cavity"
        layout.operator(FLUENT_SHADER_OT_addNodes.bl_idname, text="All Edges").choice = "All edges"
        layout.operator(FLUENT_SHADER_OT_addNodes.bl_idname, text="N Edge").choice = "normal_edge_mask_2"
        layout.operator(FLUENT_SHADER_OT_addNodes.bl_idname, text="Slope", icon="IPO_EASE_IN_OUT").choice = "Slope"
        layout.operator(FLUENT_SHADER_OT_addNodes.bl_idname, text="Altitude", icon="TRIA_UP_BAR").choice = "Altitude"
        layout.operator(FLUENT_SHADER_OT_HeightGradient.bl_idname, text="Streaks", icon='SEQ_HISTOGRAM').refresh = False
        layout.operator(FLUENT_SHADER_OT_addNodes.bl_idname, text="Directional", icon="EMPTY_SINGLE_ARROW").choice = "Directional Mask"
        layout.operator(FLUENT_SHADER_OT_Localmask.bl_idname, text="Local", icon='PIVOT_CURSOR')
        layout.operator(FLUENT_SHADER_OT_AttributeReader.bl_idname, text="Color mask", icon="COLOR")
        layout.operator(FLUENT_SHADER_OT_NewPaintedMask.bl_idname, text="Paint", icon="BRUSH_DATA").option = "Painted Mask"
        layout.operator(FLUENT_SHADER_OT_NewPaintedMask.bl_idname, text="Multiply paint", icon_value=multiply_ico.icon_id).option = 'MULTIPLY'
        layout.operator(FLUENT_SHADER_OT_NewPaintedMask.bl_idname, text="Difference paint", icon_value=difference_ico.icon_id).option = 'DIFFERENCE'
        layout.operator(FLUENT_SHADER_OT_EditPaintedMask.bl_idname, text="Edit paint", icon="GP_MULTIFRAME_EDITING")


class FLUENT_SHADER_PT_Tool(bpy.types.Panel):
    "Fluent Shader Panel"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Fluent'
    bl_label = 'Tools'

    @classmethod
    def poll(cls, context):
        if (context.space_data.tree_type == "ShaderNodeTree" and context.space_data.shader_type == "OBJECT") and context.material:
            return True
        else:
            return False

    def draw(self, context):
        layout = self.layout
        if not context.material:
            layout.label(text="Add Material")
        else:
            layout.operator(FLUENT_SHADER_OT_NodeCounter.bl_idname)
            layout.operator(FLUENT_SHADER_OT_ImageExtractor.bl_idname)

            box = layout.box()
            box.label(text='Bevels and AO samples')
            row = box.row()

            row.prop(context.scene.FluentShaderProps, 'nb_samples')
            row = box.row()
            row.operator(FLUENT_SHADER_OT_SampleEditor.bl_idname)


class FLUENT_SHADER_PT_Paint(bpy.types.Panel):
    "Fluent Shader Panel"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Fluent'
    bl_label = 'Paint'

    @classmethod
    def poll(cls, context):
        if (
                context.space_data.tree_type == "ShaderNodeTree" and context.space_data.shader_type == "OBJECT") and context.object and context.object.active_material:
            return True
        else:
            return False

    def draw(self, context):
        layout = self.layout
        layout.prop(context.scene.FluentShaderProps, 'udim_paint_baking')
        layout.prop(context.scene.FluentShaderProps, 'udim_paint_size')
        layout.prop(context.scene.FluentShaderProps, 'udim_paint_count')


class FLUENT_SHADER_PT_Streak(bpy.types.Panel):
    "Fluent Shader Panel"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Fluent'
    bl_label = 'Streaks'

    @classmethod
    def poll(cls, context):
        if (
                context.space_data.tree_type == "ShaderNodeTree" and context.space_data.shader_type == "OBJECT") and context.object and context.object.active_material:
            return True
        else:
            return False

    def draw(self, context):
        layout = self.layout
        if not context.material:
            layout.label(text="Add Material")
        else:
            layout.prop(context.scene.FluentShaderProps, 'auto_mid')
            layout.prop(context.scene.FluentShaderProps, 'max_ray_distance')
            layout.prop(context.scene.FluentShaderProps, 'angle_threshold')
            layout.operator(FLUENT_SHADER_OT_HeightGradient.bl_idname, text="Update").refresh = True
