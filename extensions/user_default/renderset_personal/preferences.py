# copyright (c) 2018- polygoniq xyz s.r.o.

import typing
import bpy
import enum
import logging
import functools
import re
from . import polib
from . import post_render_actions
from . import output_path_format
from . import scene_props

from . import __package__ as base_package

logger = logging.getLogger(f"polygoniq.{__name__}")


telemetry = polib.get_telemetry("renderset")


MODULE_CLASSES: typing.List[typing.Type] = []
CONFLICTING_ADDONS = polib.utils_bpy.get_conflicting_addons(__package__)

# This regex is used to extract enum items from the exception message
ENUM_ITEMS_FROM_EXCEPTION_RE = re.compile(r"\((.+?)\)$")


def _get_enum_items_from_exception(
    exception: TypeError,
) -> typing.Iterable[str]:
    # Attempt to get the enum items from the exception message.
    # This is really hacky solution, but we were not able to find a better way to get the
    # enum items.
    items_match = re.findall(ENUM_ITEMS_FROM_EXCEPTION_RE, str(exception))
    assert len(items_match) == 1, "Failed to match view transform items from exception."
    items_with_apostrophes = items_match[0].split(", ")
    return map(lambda item: item.strip("'"), items_with_apostrophes)


# Store the enum items for view transforms (avoids repeated extraction of the enum items)
# Do not use this variable directly, use `get_view_transform_enum_items` function instead.
CACHED_VIEW_TRANSFORM_ENUM_ITEMS: typing.Optional[
    typing.Tuple[typing.Tuple[str, str, str], ...]
] = None


def get_view_transform_enum_items(
    self: 'ColorManagedViewSettings', context: bpy.types.Context
) -> typing.Tuple[typing.Tuple[str, str, str], ...]:
    global CACHED_VIEW_TRANSFORM_ENUM_ITEMS
    if CACHED_VIEW_TRANSFORM_ENUM_ITEMS is not None:
        return CACHED_VIEW_TRANSFORM_ENUM_ITEMS

    # Attempt to get the view transform items from the exception raised by setting invalid value.
    # This is really hacky solution, but we were not able to find a better way to get the
    # view transform enum items.
    try:
        context.scene.view_settings.view_transform = ""
    except TypeError as e:
        items = _get_enum_items_from_exception(e)
        CACHED_VIEW_TRANSFORM_ENUM_ITEMS = tuple((item, item, "") for item in items)
        return CACHED_VIEW_TRANSFORM_ENUM_ITEMS
    except Exception as e:
        # The above line will raise different exceptions,
        # but we can not read the enum items from them.
        return (("Standard", "Standard", ""),)
    assert (
        False
    ), "This should never be reached, as the above line should always raise an exception."


# Store the enum items for looks (avoids repeated extraction of the enum items).
# This is a dictionary, as the look enum items are different for each view transform.
# Do not use this variable directly, use `get_look_enum_items` function instead.
# key: view_transform name; value: look enum items
CACHED_LOOK_ENUM_ITEMS: typing.Dict[str, typing.Tuple[typing.Tuple[str, str, str], ...]] = {}


def get_look_enum_items(
    self: 'ColorManagedViewSettings', context: bpy.types.Context
) -> typing.Tuple[typing.Tuple[str, str, str], ...]:
    global CACHED_LOOK_ENUM_ITEMS
    if self.view_transform in CACHED_LOOK_ENUM_ITEMS:
        return CACHED_LOOK_ENUM_ITEMS[self.view_transform]

    # Attempt to get the look items from the exception raised by setting invalid value.
    # This is really hacky solution, but we were not able to find a better way to get the
    # look enum items.
    original_view_transform = context.scene.view_settings.view_transform
    try:
        context.scene.view_settings.view_transform = self.view_transform
        context.scene.view_settings.look = ""
    except TypeError as e:
        items = _get_enum_items_from_exception(e)
        # Some look items are in format "view_transform - look_name",
        # but we want to display only the look name.
        enum_items = tuple((item, item.split(" - ")[-1], "") for item in items)
        CACHED_LOOK_ENUM_ITEMS[self.view_transform] = enum_items
        return enum_items
    except Exception as e:
        # The above line will raise different exceptions,
        # but we can not read the enum items from them.
        return (("None", "None", ""),)
    finally:
        # Restore the original view transform to avoid side effects
        if original_view_transform != context.scene.view_settings.view_transform:
            # We have to check if the view transform was changed,
            # as this could otherwise raise an exception
            context.scene.view_settings.view_transform = original_view_transform
    assert (
        False
    ), "This should never be reached, as the above line should always raise an exception."


class RenderOperator(enum.Enum):
    STANDARD = "STANDARD"
    TURBO_TOOLS = "TURBO_TOOLS"


class PreviewPreset(enum.Enum):
    WORKBENCH = "WORKBENCH"
    SAMPLE_MULTIPLIER = "SAMPLE_MULTIPLIER"
    RESOLUTION_MULTIPLIER = "RESOLUTION_MULTIPLIER"


PREVIEW_PRESET_PREFIX: typing.Dict[str, str] = {
    PreviewPreset.WORKBENCH.value: "WRKB",
    PreviewPreset.SAMPLE_MULTIPLIER.value: "SMPL",
    PreviewPreset.RESOLUTION_MULTIPLIER.value: "RES",
}


class ListerProperties(bpy.types.PropertyGroup):

    def switch_to_first_page(self, context: bpy.types.Context) -> None:
        self.page_index = 0

    show: bpy.props.EnumProperty(
        name="Show Stored",
        description="Selects what stored properties are shown",
        items=(
            (
                'PRIMITIVE_PROPS',
                "Primitive Properties",
                "Primitive Properties - floats, integers and strings",
                'RADIOBUT_ON',
                0,
            ),
            (
                'CONTEXT_PROPS',
                "Context Properties",
                "renderset properties of the context",
                'FILE_CACHE',
                1,
            ),
            (
                'VIEW_LAYER_VISIBILITY',
                "View Layer Visibility",
                "Stored visibility restrictions of view layers",
                'RENDERLAYERS',
                2,
            ),
            (
                'COLLECTION_VISIBILITY',
                "Collection Visibility",
                "Stored visibility restrictions of collections",
                'OUTLINER_COLLECTION',
                3,
            ),
            (
                'OBJECT_VISIBILITY',
                "Object Visibility",
                "Stored visibility restrictions of objects",
                'OBJECT_DATA',
                4,
            ),
            (
                'DATA_PROPERTIES',
                "Data Properties",
                "Stored custom properties of Blender data",
                'FILE_BLEND',
                5,
            ),
            ('OUTPUT_PATH', "Output Path", "Preview of the output path", 'OUTPUT', 6),
            (
                'ALL',
                "All",
                "All stored properties in renderset",
                'LIGHTPROBE_GRID' if bpy.app.version < (4, 1, 0) else 'LIGHTPROBE_VOLUME',
                7,
            ),
        ),
        update=lambda self, context: self.switch_to_first_page(context),
        default=0,
    )

    search: bpy.props.StringProperty(
        name="Search",
        description="Search for a property",
        update=lambda self, context: self.switch_to_first_page(context),
    )

    width: bpy.props.IntProperty(
        name="Lister Width (px)",
        default=1500,
        min=1,
        description="Width of render context lister window",
    )

    page_index: bpy.props.IntProperty(name="Current page index", min=0, default=0)

    props_per_page: bpy.props.IntProperty(
        name="Properties per Page",
        min=1,
        default=12,
        description="How many properties to show per page",
    )


MODULE_CLASSES.append(ListerProperties)


def view_transform_update(self: 'ColorManagedViewSettings', context: bpy.types.Context) -> None:
    # Reset look when view transform changes
    self.look = "None"


class ColorManagedViewSettings(bpy.types.PropertyGroup):
    exposure: bpy.props.FloatProperty(
        name="Exposure",
        default=0.0,
        soft_min=-10.0,
        min=-32.0,
        soft_max=10.0,
        max=32.0,
        description="Exposure (stops) applied before display transform",
        subtype='FACTOR',
    )

    gamma: bpy.props.FloatProperty(
        name="Gamma",
        default=1.0,
        min=0.00,
        max=5.0,
        description="Amount of gamma modification applied after display transform",
        subtype='FACTOR',
    )

    look: bpy.props.EnumProperty(
        name="Look",
        description="Additional transform applied before view transform for artistic needs",
        items=get_look_enum_items,
    )

    view_transform: bpy.props.EnumProperty(
        name="View Transform",
        description="View used when converting image to a display space",
        items=get_view_transform_enum_items,
        update=view_transform_update,
    )


MODULE_CLASSES.append(ColorManagedViewSettings)


class PreviewPresetProperties(bpy.types.PropertyGroup):
    preview_preset: bpy.props.EnumProperty(
        name="Preview Presets",
        description="Preview render preset",
        items=(
            (
                PreviewPreset.WORKBENCH.value,
                "Workbench",
                "Render preview using workbench render engine",
            ),
            (
                PreviewPreset.SAMPLE_MULTIPLIER.value,
                "Sample multiplier",
                "Render preview with sample multiplier",
            ),
            (
                PreviewPreset.RESOLUTION_MULTIPLIER.value,
                "Resolution multiplier",
                "Render preview with resolution multiplier",
            ),
        ),
        default=PreviewPreset.WORKBENCH.value,
    )

    sample_multiplier: bpy.props.IntProperty(
        name="Sample multiplier",
        min=1,
        soft_max=100,
        default=50,
        subtype='PERCENTAGE',
        description="Preview render sample multiplier",
    )

    resolution_multiplier: bpy.props.IntProperty(
        name="Resolution multiplier",
        min=1,
        soft_max=100,
        default=50,
        subtype='PERCENTAGE',
        description="Preview render resolution multiplier",
    )

    use_custom_view_settings: bpy.props.BoolProperty(
        name="Use Custom View Settings",
        default=False,
        description="If enabled, custom view settings will be used for the preview render",
    )

    view_settings: bpy.props.PointerProperty(
        type=ColorManagedViewSettings,
        name="Color Management",
        description="Color management settings for the preview render",
    )


MODULE_CLASSES.append(PreviewPresetProperties)


@polib.log_helpers_bpy.logged_preferences
class Preferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    show_context_stored_values: bpy.props.BoolProperty(
        name="Show Context Stored Values",
        default=False,
        description="If true we will show values of what's contained within the currently "
        "selected RendersetContext. Keep in mind that these values are not guaranteed to "
        "be up to date! RendersetContexts are stored when you switch away from them. No "
        "data is ever lost, it just may not be up to date in the stored details box",
    )
    show_context_colors: bpy.props.BoolProperty(
        name="Show Context Colors",
        default=True,
        description="Toggle showing colors labels next to each context in the renderset context list",
    )

    render_operators: bpy.props.EnumProperty(
        name="Render Operators",
        description="Which render operators should renderset use",
        items=(
            (
                RenderOperator.STANDARD.value,
                "Blender Standard",
                "Standard operators that come with Blender",
            ),
            (
                RenderOperator.TURBO_TOOLS.value,
                "Turbo Tools",
                "Turbo Tools operators for stills and animations",
            ),
        ),
        default=RenderOperator.STANDARD.value,
    )

    automatic_render_slots: bpy.props.BoolProperty(
        name="Automatic Render Slots",
        default=True,
        description="If enabled, each renderset context will be rendered into a render slot "
        "based on its index. This might take additional memory because it's all stored in Blender",
    )

    automatic_render_layer_split: bpy.props.BoolProperty(
        name="Automatic Render Layer Split",
        default=True,
        description="If enabled, renderset will automatically split renders into separate files",
    )

    use_custom_output_nodes: bpy.props.BoolProperty(
        name="Use Compositor File Output Nodes",
        default=True,
        description="If enabled, renderset will save outputs from user-defined compositor file output nodes to "
        "Output Folder Path and use them in Post Render Actions. Outputs will receive a prefix with the node's name",
    )

    debug_enabled: bpy.props.BoolProperty(
        name="Debug Enabled",
        default=False,
        description="If enabled, renderset shows new option to view internal stored debug information",
    )

    lister: bpy.props.PointerProperty(type=ListerProperties)

    previews: bpy.props.PointerProperty(type=PreviewPresetProperties)

    lock_interface: bpy.props.BoolProperty(
        name="Auto Lock Interface",
        default=True,
        description="Renderset automatically locks interface for rendering. This suppresses "
        "possible crashes and makes the rendering faster. On the other hand controlling of the "
        "interface during rendering is disabled. It is heavily recommended to leave this enabled!",
    )

    switch_to_solid_view_before_rendering: bpy.props.BoolProperty(
        name="Switch to Solid View before Rendering", default=True
    )
    free_persistent_data_after_rendering: bpy.props.BoolProperty(
        name="Free persistent data from memory after Rendering", default=True
    )

    show_render_output_settings: bpy.props.BoolProperty(
        description="Show/Hide Output Settings", default=True
    )

    show_output_filename_settings: bpy.props.BoolProperty(
        description="Show/Hide Output Filename Settings", default=False
    )

    show_post_render_actions: bpy.props.BoolProperty(
        description="Show/Hide Post Render Actions", default=False
    )

    show_options: bpy.props.BoolProperty(description="Show/Hide Options", default=True)

    def draw_all_output_filenames_ui(self, layout: bpy.types.UILayout):
        scene_output_format = scene_props.get_output_format(bpy.context)
        output_path_format.draw_output_filename_ui(
            scene_output_format,
            layout,
            output_path_format.OutputFormatProperty.STILL_IMAGE_FILENAME,
            scene_props.SceneAddVariable,
            output_path_format.MockRendersetContext(),
            "Still Image",
        )
        output_path_format.draw_output_filename_ui(
            scene_output_format,
            layout,
            output_path_format.OutputFormatProperty.ANIMATION_FRAME_FILENAME,
            scene_props.SceneAddVariable,
            output_path_format.MockRendersetContext(),
            "Animation Frame",
        )
        output_path_format.draw_output_filename_ui(
            scene_output_format,
            layout,
            output_path_format.OutputFormatProperty.ANIMATION_MOVIE_FILENAME,
            scene_props.SceneAddVariable,
            output_path_format.MockRendersetContext(),
            "Animation Movie",
        )

    def draw_collection_restriction_toggles(self, layout: bpy.types.UILayout) -> None:
        collection_toggles_settings = scene_props.get_collection_toggles_settings(bpy.context)
        layer_collection_toggles_settings = scene_props.get_layer_collection_toggles_settings(
            bpy.context
        )
        row = layout.row()
        row.label(text="Collection", icon='OUTLINER_COLLECTION')
        row.alignment = 'LEFT'
        row = row.row(align=True)
        row.prop(
            layer_collection_toggles_settings,
            "exclude",
            text="",
            icon=(
                'CHECKBOX_HLT' if layer_collection_toggles_settings.exclude else 'CHECKBOX_DEHLT'
            ),
            emboss=False,
        )
        row.prop(
            collection_toggles_settings,
            "hide_select",
            text="",
            icon=(
                'RESTRICT_SELECT_OFF'
                if collection_toggles_settings.hide_select
                else 'RESTRICT_SELECT_ON'
            ),
            emboss=False,
        )
        row.prop(
            layer_collection_toggles_settings,
            "hide_viewport",
            text="",
            icon='HIDE_OFF' if layer_collection_toggles_settings.hide_viewport else 'HIDE_ON',
            emboss=False,
        )
        row.prop(
            collection_toggles_settings,
            "hide_viewport",
            text="",
            icon=(
                'RESTRICT_VIEW_OFF'
                if collection_toggles_settings.hide_viewport
                else 'RESTRICT_VIEW_ON'
            ),
            emboss=False,
        )
        row.prop(
            collection_toggles_settings,
            "hide_render",
            text="",
            icon=(
                'RESTRICT_RENDER_OFF'
                if collection_toggles_settings.hide_render
                else 'RESTRICT_RENDER_ON'
            ),
            emboss=False,
        )
        row.prop(
            layer_collection_toggles_settings,
            "holdout",
            text="",
            icon='HOLDOUT_ON' if layer_collection_toggles_settings.holdout else 'HOLDOUT_OFF',
            emboss=False,
        )
        row.prop(
            layer_collection_toggles_settings,
            "indirect_only",
            text="",
            icon=(
                'INDIRECT_ONLY_ON'
                if layer_collection_toggles_settings.indirect_only
                else 'INDIRECT_ONLY_OFF'
            ),
            emboss=False,
        )

    def draw_object_restriction_toggles(self, layout: bpy.types.UILayout) -> None:
        object_toggles_settings = scene_props.get_object_toggles_settings(bpy.context)
        row = layout.row()
        row.label(text="Object", icon='OBJECT_DATA')
        row.alignment = 'LEFT'
        row = row.row(align=True)
        row.prop(
            object_toggles_settings,
            "hide_select",
            text="",
            icon=(
                'RESTRICT_SELECT_OFF'
                if object_toggles_settings.hide_select
                else 'RESTRICT_SELECT_ON'
            ),
            emboss=False,
        )
        row.prop(
            object_toggles_settings,
            "hide_viewport",
            text="",
            icon=(
                'RESTRICT_VIEW_OFF' if object_toggles_settings.hide_viewport else 'RESTRICT_VIEW_ON'
            ),
            emboss=False,
        )
        row.prop(
            object_toggles_settings,
            "hide_render",
            text="",
            icon=(
                'RESTRICT_RENDER_OFF'
                if object_toggles_settings.hide_render
                else 'RESTRICT_RENDER_ON'
            ),
            emboss=False,
        )

    def draw_render_output_settings_ui(
        self, context: bpy.types.Context, layout: bpy.types.UILayout
    ) -> None:
        col = layout.column()
        scene_output_format = scene_props.get_output_format(bpy.context)
        output_path_format.draw_output_folder_ui(
            scene_output_format,
            col,
            (
                polib.ui_bpy.OperatorButtonLoader(scene_props.SceneSelectOutputFolder)
                if bpy.app.version < (4, 1, 0)
                else None
            ),
            scene_props.SceneAddVariable,
            output_path_format.MockRendersetContext(),
        )

        # Output Filenames subsection
        polib.ui_bpy.collapsible_box(
            col,
            self,
            "show_output_filename_settings",
            "Output Filenames",
            self.draw_all_output_filenames_ui,
            docs_module=base_package,
            docs_rel_url="getting_started/rendering_and_outputs/#output-filenames",
        )

        # Post Render Actions subsection
        polib.ui_bpy.collapsible_box(
            col,
            self,
            "show_post_render_actions",
            "Post Render Actions",
            functools.partial(
                post_render_actions.draw_post_render_actions_ui,
                ui_list=scene_props.ACTION_UL_ScenePostRenderActionList,
                action_props=scene_props.get_post_render_actions(context),
                add_action_operator=scene_props.SceneAddPostRenderAction,
                edit_action_operator=scene_props.SceneEditPostRenderAction,
                delete_action_operator=scene_props.SceneDeletePostRenderAction,
                move_action_operator=scene_props.SceneMovePostRenderAction,
                remove_actions_operator=scene_props.SceneClearPostRenderActions,
            ),
            docs_module=base_package,
            docs_rel_url="advanced_topics/post_render_actions/",
        )

    def draw_renderset_options_settings_ui(self, layout: bpy.types.UILayout) -> None:
        col = layout.column()
        col.label(text="Remembered Visibility Restrictions:")
        self.draw_collection_restriction_toggles(col)
        self.draw_object_restriction_toggles(col)
        col.separator()

        col = layout.column(align=True)
        row = col.row()
        row.prop(self, "render_operators")

        col.separator()

        row = col.row()
        row.prop(self, "automatic_render_slots")
        row.prop(self, "automatic_render_layer_split")

        row = col.row()
        row.prop(self, "lock_interface")
        row.prop(self, "switch_to_solid_view_before_rendering")
        row = col.row()
        row.label(text="")  # empty space
        row.prop(self, "free_persistent_data_after_rendering")

        row = col.row()
        row.prop(self, "use_custom_output_nodes")

        row = col.row()
        row.prop(self, "show_context_colors")

        col.separator()
        row = col.row()
        row.prop(self, "debug_enabled")
        row.prop(self.lister, "width")

    def draw(self, context: bpy.types.Context):
        polib.ui_bpy.draw_conflicting_addons(self.layout, __package__, CONFLICTING_ADDONS)
        box_col = self.layout.column()

        # Render Output Settings section
        polib.ui_bpy.collapsible_box(
            box_col,
            self,
            "show_render_output_settings",
            "Render Output Setting",
            functools.partial(self.draw_render_output_settings_ui, context),
            docs_module=base_package,
            docs_rel_url="getting_started/rendering_and_outputs/#render-output-settings",
        )

        # Render Options section
        polib.ui_bpy.collapsible_box(
            box_col,
            self,
            "show_options",
            "Options",
            self.draw_renderset_options_settings_ui,
            docs_module=base_package,
            docs_rel_url="getting_started/rendering_and_outputs/?h=options#render-options",
        )

        row = self.layout.row()
        row.operator(PackLogs.bl_idname, icon='EXPERIMENTAL')

        polib.ui_bpy.draw_settings_footer(self.layout)


MODULE_CLASSES.append(Preferences)


@polib.log_helpers_bpy.logged_operator
class PackLogs(bpy.types.Operator):
    bl_idname = "renderset.pack_logs"
    bl_label = "Pack Logs"
    bl_description = "Archives polygoniq logs as zip file and opens its location"
    bl_options = {'REGISTER'}

    def execute(self, context):
        packed_logs_directory_path = polib.log_helpers_bpy.pack_logs(telemetry)
        polib.utils_bpy.xdg_open_file(packed_logs_directory_path)
        return {'FINISHED'}


MODULE_CLASSES.append(PackLogs)


def register():
    for cls in MODULE_CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(MODULE_CLASSES):
        bpy.utils.unregister_class(cls)
