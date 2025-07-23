#!/usr/bin/python3
# copyright (c) 2018- polygoniq xyz s.r.o.

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

# Parts made using the awesome UILists tutorial by Diego Gangl. Thanks!
# See https://sinestesia.co/blog/tutorials/amazing-uilists-in-blender/

import bpy
import bpy_extras.io_utils
import os
import sys
import typing
import json
import re
import tempfile
import datetime
import logging
import itertools
import functools
import logging.handlers
import importlib
import bl_ui

root_logger = logging.getLogger("polygoniq")
logger = logging.getLogger(f"polygoniq.{__name__}")
if not getattr(root_logger, "polygoniq_initialized", False):
    root_logger_formatter = logging.Formatter(
        "P%(process)d:%(asctime)s:%(name)s:%(levelname)s: [%(filename)s:%(lineno)d] %(message)s",
        "%H:%M:%S",
    )
    try:
        root_logger.setLevel(int(os.environ.get("POLYGONIQ_LOG_LEVEL", "20")))
    except (ValueError, TypeError):
        root_logger.setLevel(20)
    root_logger.propagate = False
    root_logger_stream_handler = logging.StreamHandler()
    root_logger_stream_handler.setFormatter(root_logger_formatter)
    root_logger.addHandler(root_logger_stream_handler)
    try:
        log_path = os.path.join(tempfile.gettempdir(), "polygoniq_logs")
        os.makedirs(log_path, exist_ok=True)
        root_logger_handler = logging.handlers.TimedRotatingFileHandler(
            os.path.join(log_path, f"blender_addons.txt"),
            when="h",
            interval=1,
            backupCount=2,
            utc=True,
        )
        root_logger_handler.setFormatter(root_logger_formatter)
        root_logger.addHandler(root_logger_handler)
    except:
        logger.exception(
            f"Can't create rotating log handler for polygoniq root logger "
            f"in module \"{__name__}\", file \"{__file__}\""
        )
    setattr(root_logger, "polygoniq_initialized", True)
    logger.info(
        f"polygoniq root logger initialized in module \"{__name__}\", file \"{__file__}\" -----"
    )


# To comply with extension encapsulation, after the addon initialization:
# - sys.path needs to stay the same as before the initialization
# - global namespace can not contain any additional modules outside of __package__

# Dependencies for all 'production' addons are shipped in folder `./python_deps`
# So we do the following:
# - Add `./python_deps` to sys.path
# - Import all dependencies to global namespace
# - Manually remap the dependencies from global namespace in sys.modules to a subpackage of __package__
# - Clear global namespace of remapped dependencies
# - Remove `./python_deps` from sys.path
# - For developer experience, import "real" dependencies again, only if TYPE_CHECKING is True

# See https://docs.blender.org/manual/en/4.2/extensions/addons.html#extensions-and-namespace
# for more details
ADDITIONAL_DEPS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "python_deps"))
try:
    if os.path.isdir(ADDITIONAL_DEPS_DIR) and ADDITIONAL_DEPS_DIR not in sys.path:
        sys.path.insert(0, ADDITIONAL_DEPS_DIR)

    # We import in reverse order of dependencies, to import dependencies first before they are
    # imported in the libraries. Technically this shouldn't matter.
    dependencies = ["hatchery", "polib"]
    for dependency in dependencies:
        logger.debug(f"Importing additional dependency {dependency}")
        dependency_module = importlib.import_module(dependency)
        local_module_name = f"{__package__}.{dependency}"
        sys.modules[local_module_name] = dependency_module
    for module_name in list(sys.modules.keys()):
        if module_name.startswith(tuple(dependencies)):
            del sys.modules[module_name]

    from . import polib
    from . import hatchery

    from . import utils
    from . import serialize_utils
    from . import output_path_format
    from . import multi_edit
    from . import lister
    from . import renderset_context_old
    from . import renderset_context
    from . import renderset_context_utils
    from . import scene_props
    from . import sync_overrides
    from . import post_render_actions
    from . import preferences
    from . import compositor_helpers

    if typing.TYPE_CHECKING:
        import polib
        import hatchery

finally:
    if ADDITIONAL_DEPS_DIR in sys.path:
        sys.path.remove(ADDITIONAL_DEPS_DIR)


bl_info = {
    "name": "renderset_personal",
    "author": "polygoniq xyz s.r.o.",
    "version": (2, 1, 0),  # bump doc_url as well!
    "blender": (3, 6, 0),
    "location": "renderset panel in the polygoniq tab in the sidebar of the 3D View window",
    "description": "Render manager addon for Blender 3.6+. Create a different render context for every camera in your scene.",
    "category": "System",
    "doc_url": "https://docs.polygoniq.com/renderset/2.1.0/",
    "tracker_url": "https://polygoniq.com/discord/",
}
telemetry = polib.get_telemetry("renderset")
telemetry.report_addon(bl_info, __file__)


MODULE_CLASSES: typing.List[typing.Type] = []


class MY_UL_RendersetContextList(bpy.types.UIList):
    """UI list for managing render contexts"""

    bl_description = "UI list for managing render contexts"

    def draw_item(
        self,
        context: bpy.types.Context,
        layout,
        data,
        item,
        icon,
        active_data,
        active_propname,
        index,
    ) -> None:

        custom_icon = (
            'FILE_IMAGE'
            if item.render_type == renderset_context.RenderType.STILL.value
            else 'FILE_MOVIE'
        )

        row = layout.row()
        renderset_context.draw_color_and_name(context, row, item, custom_icon)

        if os.path.exists(item.latest_preview_folder):
            col = row.column()
            open_preview_folder = col.operator(
                RendersetOpenResultFolder.bl_idname, text="", icon='ZOOM_ALL'
            )
            open_preview_folder.rset_context_idx = index
            open_preview_folder.preview = True

        col = row.column()
        open_folder = col.operator(RendersetOpenResultFolder.bl_idname, text="", icon='FILEBROWSER')
        open_folder.rset_context_idx = index
        open_folder.preview = False

        row.prop(item, "include_in_render_all", text="")

    def filter_items(
        self, context: bpy.types.Context, data: bpy.types.Scene, prop: str
    ) -> typing.Tuple[typing.List[int], typing.List[int]]:
        rset_contexts = getattr(data, prop)
        filter_bits = [
            (
                self.bitflag_filter_item
                if self.filter_name.lower() in rset_context.custom_name.strip().lower()
                else 0
            )
            for rset_context in rset_contexts
        ]
        if self.use_filter_sort_alpha:
            order_indices = bl_ui.UI_UL_list.sort_items_by_name(rset_contexts, "custom_name")
        else:
            order_indices = []
        return filter_bits, order_indices


MODULE_CLASSES.append(MY_UL_RendersetContextList)


@polib.log_helpers_bpy.logged_operator
class RendersetContextList_OT_AddItem(bpy.types.Operator):
    """Add a new render context to the list"""

    bl_idname = "renderset.renderset_context_list_add_item"
    bl_label = "Add an item"
    bl_description = "Add a new render context to the list"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return len(
            context.scene.renderset_contexts
        ) < renderset_context_utils.MAX_RENDER_CONTEXTS and not multi_edit.multi_edit_mode_enabled(
            context
        )

    def execute(self, context: bpy.types.Context):
        if len(context.scene.renderset_contexts) == 0:
            item = context.scene.renderset_contexts.add()
            item.init_default(context)
            context.scene.renderset_context_index = 0
        else:
            previously_selected_context_index = context.scene.renderset_context_index
            assert (
                previously_selected_context_index >= 0
                and previously_selected_context_index < len(context.scene.renderset_contexts)
            )
            item = context.scene.renderset_contexts.add()
            # we have to do this instead of storing the pointer because the pointers can get
            # invalidated when the prop collection reallocates. we'd get a crash!
            previously_selected_context = context.scene.renderset_contexts[
                previously_selected_context_index
            ]
            item.init_from(context, previously_selected_context)

            if context.scene.renderset_context_index + 1 < len(context.scene.renderset_contexts):
                # move the context right after the current context
                context.scene.renderset_contexts.move(
                    len(context.scene.renderset_contexts) - 1,
                    context.scene.renderset_context_index + 1,
                )
                # switch to it
                context.scene.renderset_context_index += 1

        logger.info(f"Added context {item.custom_name}")
        return {'FINISHED'}


MODULE_CLASSES.append(RendersetContextList_OT_AddItem)


@polib.log_helpers_bpy.logged_operator
class RendersetContextList_OT_DeleteItem(bpy.types.Operator):
    """Delete the selected render context from the list"""

    bl_idname = "renderset.renderset_context_list_delete_item"
    bl_label = "Delete an item"
    bl_description = "Delete the selected render context from the list"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        # you have to keep at least one renderset context,
        # the last one can't be removed!
        return len(context.scene.renderset_contexts) > 1 and not multi_edit.multi_edit_mode_enabled(
            context
        )

    def execute(self, context: bpy.types.Context):
        renderset_context_utils.SKIP_RENDER_CONTEXT_SYNC = True
        try:
            try:
                item_name = renderset_context_utils.get_active_renderset_context(
                    context
                ).custom_name
            except:
                item_name = "unknown"

            the_list = context.scene.renderset_contexts
            index = context.scene.renderset_context_index
            if index > 0:
                context.scene.renderset_context_index -= 1
                the_list.remove(index)
                # current index remains unchanged, we switch to context
                # just above the one we are deleting
            else:
                # switch to context just below the one we are deleting
                context.scene.renderset_context_index += 1
                # remove the first context
                the_list.remove(index)
                # this means all the indices have to be adjusted by -1
                context.scene.renderset_context_index -= 1

            renderset_context_utils.renderset_context_list_ensure_valid_index(context)

            logger.info(f"Deleted context {item_name}")
        finally:
            renderset_context_utils.SKIP_RENDER_CONTEXT_SYNC = False

        return {'FINISHED'}


MODULE_CLASSES.append(RendersetContextList_OT_DeleteItem)


@polib.log_helpers_bpy.logged_operator
class RendersetContextList_OT_MoveItem(bpy.types.Operator):
    """Move selected render context in the list"""

    bl_idname = "renderset.render_context_list_move_item"
    bl_label = "Move render context in the list"
    bl_description = (
        "Move selected render context in the list, use CTRL to move all the way up or down, "
        "or SHIFT to show a dialog where you can select the amount of movement"
    )
    bl_options = {'UNDO'}

    delta: bpy.props.IntProperty(
        name="Delta Steps",
        default=1,
        description="Context will be moved this many places up (for negative values) "
        "or down (positive values)",
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return len(context.scene.renderset_contexts) > 0 and not multi_edit.multi_edit_mode_enabled(
            context
        )

    def execute(self, context: bpy.types.Context):
        renderset_context_utils.SKIP_RENDER_CONTEXT_SYNC = True
        renderset_context_utils.SKIP_RENDER_CONTEXT_APPLY = True

        try:
            active_context = renderset_context_utils.get_active_renderset_context(context)
            item_name = active_context.custom_name if active_context is not None else "unknown"

            the_list = context.scene.renderset_contexts
            old_index = context.scene.renderset_context_index
            new_index = old_index + self.delta
            new_index = min(new_index, len(the_list) - 1)
            new_index = max(new_index, 0)
            the_list.move(old_index, new_index)
            context.scene.renderset_context_index = new_index
            renderset_context_utils.renderset_context_list_ensure_valid_index(context)

            logger.info(
                f"Moved {item_name} by delta {self.delta}, "
                f"old_index: {old_index}, new_index: {new_index}"
            )
        finally:
            renderset_context_utils.SKIP_RENDER_CONTEXT_SYNC = False
            renderset_context_utils.SKIP_RENDER_CONTEXT_APPLY = False

        return {'FINISHED'}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        if event.ctrl:
            # if we multiply by max amount of contexts we go all the way up or down
            self.delta *= renderset_context_utils.MAX_RENDER_CONTEXTS

        if event.shift:
            return context.window_manager.invoke_props_dialog(self)
        else:
            return self.execute(context)


MODULE_CLASSES.append(RendersetContextList_OT_MoveItem)


@polib.log_helpers_bpy.logged_operator
class RendersetAddContextPerCamera(bpy.types.Operator):
    bl_idname = "renderset.renderset_add_context_per_camera"
    bl_label = "Context per Selected Camera"
    bl_description = "Adds a new renderset context per selected camera"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        if renderset_context_utils.get_active_renderset_context(context) is None:
            return False

        for obj in context.selected_objects:
            if obj.type == 'CAMERA':
                return True

        return False

    def execute(self, context: bpy.types.Context):
        previously_selected_context_index = context.scene.renderset_context_index
        assert previously_selected_context_index >= 0 and previously_selected_context_index < len(
            context.scene.renderset_contexts
        )
        prev_active_camera = context.scene.camera
        try:
            selected_cameras = [obj for obj in context.selected_objects if obj.type == 'CAMERA']
            # Sort the cameras as they appear in outliner. This is not exactly the same as Blender's own sorting
            # implementation, since it has special rules for names with ".001".
            # Sorting by name.lower() is closest to Blender's way of sorting.
            selected_cameras.sort(key=lambda obj: obj.name.lower(), reverse=True)

            for camera in selected_cameras:
                # Set selected camera as active in the scene, so that created context stores it
                context.scene.camera = camera

                item = context.scene.renderset_contexts.add()
                # we have to do this instead of storing the pointer because the pointers can get
                # invalidated when the prop collection reallocates. we'd get a crash!
                previously_selected_context = context.scene.renderset_contexts[
                    previously_selected_context_index
                ]
                item.init_from(context, previously_selected_context)
                item.custom_name = camera.name

                logger.info(f"Created context {item.custom_name} for camera {camera.name}")

                if context.scene.renderset_context_index + 1 < len(
                    context.scene.renderset_contexts
                ):
                    # move the context right after the current context
                    context.scene.renderset_contexts.move(
                        len(context.scene.renderset_contexts) - 1,
                        context.scene.renderset_context_index + 1,
                    )

        finally:
            # Set back camera of selected context
            context.scene.camera = prev_active_camera

        return {'FINISHED'}


MODULE_CLASSES.append(RendersetAddContextPerCamera)


@polib.log_helpers_bpy.logged_operator
class RendersetAddContextFromViewport(bpy.types.Operator):
    bl_idname = "renderset.add_context_from_viewport"
    bl_label = "Context from Viewport"
    bl_description = (
        "Adds a new renderset context from viewport, copies camera and other stored "
        "properties from a current context"
    )
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        if renderset_context_utils.get_active_renderset_context(context) is None:
            return False
        return bpy.ops.view3d.camera_to_view.poll()

    def execute(self, context: bpy.types.Context):
        previously_selected_context_index = context.scene.renderset_context_index
        assert previously_selected_context_index >= 0 and previously_selected_context_index < len(
            context.scene.renderset_contexts
        )

        assert context.scene.camera is not None  # camera_to_view.poll() ensures this
        prev_camera = context.scene.camera

        # Deselect all, so that we can get a new camera from selected_objects
        polib.asset_pack_bpy.clear_selection(context)
        # Create a new camera and move it to the current view
        with context.temp_override(selected_objects=[context.scene.camera]):
            bpy.ops.object.duplicate()
        new_camera = context.selected_objects[0]
        new_camera.animation_data_clear()
        context.scene.camera = new_camera
        bpy.ops.view3d.camera_to_view()
        # The new camera is the only selected object after duplicate(), make it also active
        context.view_layer.objects.active = new_camera

        item = context.scene.renderset_contexts.add()
        # we have to do this instead of storing the pointer because the pointers can get
        # invalidated when the prop collection reallocates. we'd get a crash!
        previously_selected_context = context.scene.renderset_contexts[
            previously_selected_context_index
        ]
        item.init_from(context, previously_selected_context)
        item.custom_name = "Viewport"

        if context.scene.renderset_context_index + 1 < len(context.scene.renderset_contexts):
            # move the context right after the current context
            context.scene.renderset_contexts.move(
                len(context.scene.renderset_contexts) - 1, context.scene.renderset_context_index + 1
            )
            # switch to it
            context.scene.camera = prev_camera
            context.scene.renderset_context_index += 1

        return {'FINISHED'}


MODULE_CLASSES.append(RendersetAddContextFromViewport)


@polib.log_helpers_bpy.logged_operator
class RendersetRenderContexts(bpy.types.Operator):
    """Renders RendersetContext where include_in_render_all==True if action=="all".
    If action=="current" renders active RendersetContext
    """

    bl_idname = "renderset.render_all_renderset_contexts"
    bl_label = "Render"
    bl_description = "Render current or all checked renderset contexts. If preview is enabled, "
    "the contexts are rendered using the chosen preview preset"
    bl_options = {'REGISTER'}

    action: bpy.props.EnumProperty(
        name="action",
        items=(
            (
                utils.RenderAction.ALL,
                utils.RenderAction.ALL,
                utils.RenderAction.ALL,
            ),
            (
                utils.RenderAction.CURRENT,
                utils.RenderAction.CURRENT,
                utils.RenderAction.CURRENT,
            ),
        ),
        options={'HIDDEN'},
    )

    preview: bpy.props.BoolProperty(
        name="Preview Mode",
        description="Render context in preview mode. Previews are rendered using a chosen preview preset, "
        "stills will remain in original file format, animation previews will be stored in mp4 format",
        default=False,
    )

    # has rendering been cancelled?
    rendering_cancelled: bool = False
    # is the render initialized?
    # we use this to prevent initializing the same failing render in a loop
    render_initialized: bool = False
    # are we currently rendering?
    rendering: bool = False
    # renderset context index queue of what we still have to render
    render_queue: typing.List[int] = []
    render_index: int = 0
    timer_event: typing.Optional[bpy.types.Timer] = None
    frozen_time: typing.Optional[datetime.datetime] = None

    was_interface_locked: bool = False

    @classmethod
    def description(
        cls, context: bpy.types.Context, properties: bpy.types.OperatorProperties
    ) -> str:
        action = "all checked" if properties.action == utils.RenderAction.ALL else "the current"
        plural = "s" if properties.action == utils.RenderAction.ALL else ""

        if properties.preview:
            description = f"Render preview{plural} of {action} context{plural} using workbench"
        else:
            description = f"Render {action} renderset context{plural}"

        return description

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        included_contexts_count = renderset_context_utils.get_included_renderset_contexts_count(
            context
        )
        return (
            context.scene.camera is not None
            and included_contexts_count > 0
            and not multi_edit.multi_edit_mode_enabled(context)
        )

    def reset(self, context: bpy.types.Context) -> None:
        RendersetRenderContexts.rendering_cancelled = False
        RendersetRenderContexts.render_initialized = False
        RendersetRenderContexts.rendering = False
        RendersetRenderContexts.render_queue = []
        RendersetRenderContexts.render_index = 0
        context.scene.render.filepath = context.scene.renderset_old_render_filepath

        if self.on_post_render in bpy.app.handlers.render_post:
            bpy.app.handlers.render_post.remove(self.on_post_render)
        if self.on_render_cancel in bpy.app.handlers.render_cancel:
            bpy.app.handlers.render_cancel.remove(self.on_render_cancel)

        if RendersetRenderContexts.timer_event is not None:
            context.window_manager.event_timer_remove(RendersetRenderContexts.timer_event)
        RendersetRenderContexts.timer_event = None
        RendersetRenderContexts.frozen_time = None

    def on_post_render(self, scene: bpy.types.Scene, _=None) -> None:
        assert RendersetRenderContexts.render_index < len(RendersetRenderContexts.render_queue)
        active = renderset_context_utils.get_active_renderset_context(bpy.context)
        assert active is not None

        try:
            scene_output_format = scene_props.get_output_format(bpy.context)
            render_finished_status = active.render_finished(
                scene,
                override_folder_path=(
                    scene_output_format.preset_folder_path if self.preview else None
                ),
            )
            if render_finished_status == 'FRAME_FINISHED':
                return

            if render_finished_status == 'ERROR':
                RendersetRenderContexts.rendering_cancelled = True
                return

            RendersetRenderContexts.render_index += 1
            RendersetRenderContexts.render_initialized = False
            RendersetRenderContexts.rendering = False
        except Exception as e:
            logger.error(f"Post render handler error: {e}")
            RendersetRenderContexts.rendering_cancelled = True

    def on_render_cancel(self, scene: bpy.types.Scene, _=None) -> None:
        RendersetRenderContexts.rendering_cancelled = True

    @staticmethod
    def can_render_into_stored_file_format(
        bpy_context: bpy.types.Context, rset_context: bpy.types.Context
    ) -> bool:
        """Return False if a still image is trying to be saved to a movie format file.

        It's possible to call this method on a non-active context.
        """
        MOVIE_FORMATS = ['AVI_JPEG', 'AVI_RAW', 'FFMPEG']
        scene_dict = rset_context.try_get_scene_settings()
        image_settings_dict = scene_dict.get("render", {}).get("image_settings", {})

        if 'file_format' in image_settings_dict:
            is_movie_format = image_settings_dict['file_format'] in MOVIE_FORMATS
        else:
            # rset_context cannot change it, the one from current bpy_context will be used
            is_movie_format = bpy_context.scene.render.image_settings.file_format in MOVIE_FORMATS
        if is_movie_format and rset_context.render_type == renderset_context.RenderType.STILL.value:
            return False
        return True

    def can_render_preview(
        self, context: bpy.types.Context, rset_context: renderset_context.RendersetContext
    ) -> typing.Tuple[bool, typing.Optional[str]]:
        """Checks if the current render engine supports preview rendering.

        Returns a bool and an optional message why preview can't be rendered.
        """

        prefs = utils.get_preferences(context)
        if prefs.previews.preview_preset == preferences.PreviewPreset.SAMPLE_MULTIPLIER.value:
            engine = (
                rset_context.synced_data_dict.get("bpy", {})
                .get("context", {})
                .get("scene", {})
                .get("render", {})
                .get("engine", "")
            )
            if engine not in {
                'BLENDER_EEVEE',
                'BLENDER_EEVEE_NEXT',
                'CYCLES',
                'octane',
            }:
                return False, f"Cannot set samples in {engine} engine"
            if engine == 'octane' and not any(
                node.name in utils.OCTANE_KERNELS_WITH_SAMPLES_NAMES
                for node in bpy.data.node_groups["Octane Kernel"].nodes
            ):
                # Check we can set samples on octane kernel nodes
                return False, "Current Octane Kernel node isn't compatible with setting samples"
        return True, None

    def execute(self, context: bpy.types.Context):
        context.scene.renderset_old_render_filepath = context.scene.render.filepath
        self.reset(context)
        rset_context = renderset_context_utils.get_active_renderset_context(context)
        if rset_context is not None:
            # Sync data into current context, so that we can validate data stored in the context
            # e.g. with self.can_render_into_stored_file_format()
            rset_context.sync(context)

        # Let's freeze the time, all rendered contexts will have the same time of render start
        RendersetRenderContexts.frozen_time = datetime.datetime.now()
        if self.action == utils.RenderAction.ALL:
            previous_render_queue = RendersetRenderContexts.render_queue.copy()
            for i, rset_context in enumerate(
                renderset_context_utils.get_all_renderset_contexts(context)
            ):
                if not rset_context.include_in_render_all:
                    continue
                if not self.can_render_into_stored_file_format(context, rset_context):
                    self.report(
                        {'ERROR'},
                        f"In '{context.scene.renderset_contexts[i].custom_name}' context, "
                        f"Render Type is set to 'Still Image' but the output file format is "
                        f"'{context.scene.render.image_settings.file_format}' which is "
                        f"an animation format. Cancelling render.",
                    )
                    RendersetRenderContexts.render_queue = previous_render_queue
                    return {'CANCELLED'}
                if self.preview:
                    success, reason = self.can_render_preview(context, rset_context)
                    if not success:
                        RendersetRenderContexts.render_queue = previous_render_queue
                        self.report(
                            {'ERROR'},
                            f"Preview rendering is not supported in '{rset_context.custom_name}' context. "
                            f"{reason}. Cancelling render.",
                        )
                        return {'CANCELLED'}

                RendersetRenderContexts.render_queue.append(i)

        elif self.action == utils.RenderAction.CURRENT:
            active_i = renderset_context_utils.get_active_renderset_context_index(context)
            if active_i is None:
                self.report({'ERROR'}, "Invalid Render Context index!")
                return {'CANCELLED'}
            rset_context = context.scene.renderset_contexts[active_i]
            if not self.can_render_into_stored_file_format(context, rset_context):
                self.report(
                    {'ERROR'},
                    f"In '{rset_context.custom_name}' context, "
                    f"Render Type is set to 'Still Image' but the output file format is "
                    f"'{context.scene.render.image_settings.file_format}' which is "
                    f"an animation format. Cancelling render.",
                )
                return {'CANCELLED'}
            if self.preview:
                success, reason = self.can_render_preview(context, rset_context)
                if not success:
                    self.report(
                        {'ERROR'},
                        f"Preview rendering is not supported in '{rset_context.custom_name}' context. "
                        f"{reason}. Cancelling render.",
                    )
                    return {'CANCELLED'}

            RendersetRenderContexts.render_queue.append(active_i)

        else:
            raise RuntimeError(f"Unknown action '{self.action}'!")

        bpy.app.handlers.render_post.append(self.on_post_render)
        bpy.app.handlers.render_cancel.append(self.on_render_cancel)

        # Switch to SOLID view before rendering
        if utils.get_preferences(bpy.context).switch_to_solid_view_before_rendering:
            utils.set_all_opened_viewports_to_solid_shading()

        RendersetRenderContexts.was_interface_locked = context.scene.render.use_lock_interface

        assert RendersetRenderContexts.timer_event is None
        RendersetRenderContexts.timer_event = context.window_manager.event_timer_add(
            1.0, window=context.window
        )
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def post_context_render_cleanup(self, context: bpy.types.Context) -> None:
        rset_context = renderset_context_utils.get_active_renderset_context(context)
        assert rset_context is not None
        rset_context.reset_custom_output_nodes(context.scene)

        if self.preview:
            if not RendersetRenderContexts.rendering_cancelled:
                scene_output_format = scene_props.get_output_format(bpy.context)
                output_folder_path = rset_context.generate_output_folder_path(
                    override_folder_path=scene_output_format.preset_folder_path
                )
                rset_context.latest_preview_folder = output_folder_path

            rset_context.reset_preview_settings(context)

    def final_post_render_cleanup(self, context: bpy.types.Context) -> None:
        self.post_context_render_cleanup(context)
        self.reset(context)

        context.scene.render.use_lock_interface = RendersetRenderContexts.was_interface_locked
        if utils.get_preferences(bpy.context).free_persistent_data_after_rendering:
            utils.free_memory_for_persistent_data(context)

    def modal(self, context: bpy.types.Context, event):
        if event.type != 'TIMER':
            return {'PASS_THROUGH'}

        if RendersetRenderContexts.rendering_cancelled:
            self.final_post_render_cleanup(context)
            self.report({'INFO'}, "Rendering cancelled!")
            return {'CANCELLED'}

        if RendersetRenderContexts.render_index == len(RendersetRenderContexts.render_queue):
            self.final_post_render_cleanup(context)
            self.report({'INFO'}, "Rendering finished!")
            return {'FINISHED'}

        if not RendersetRenderContexts.rendering:
            if RendersetRenderContexts.render_initialized:
                # This means we already initialized the render, but some error made it fail without
                # raising an exception. In this scenario, the render_pre handler was not called and
                # we are trying to initialize the same render again.
                # This can happen for example by using an unsupported combination of container and
                # codec in the output settings. The render operator should display a report,
                # so let's not display another one here, but let's still log it.
                self.final_post_render_cleanup(context)
                logger.error("Trying to initialize already initialized render!")
                return {'CANCELLED'}

            # clean up after individual context rendering before starting rendering the next one
            if RendersetRenderContexts.render_index > 0:
                self.post_context_render_cleanup(context)

            # https://docs.blender.org/api/master/bpy.app.handlers.html#note-on-altering-data
            if utils.get_preferences(context).lock_interface:
                context.scene.render.use_lock_interface = True

            # we are not currently rendering and we still have indices in the queue
            index = RendersetRenderContexts.render_queue[RendersetRenderContexts.render_index]
            rset_context = context.scene.renderset_contexts[index]
            self.report({'INFO'}, f"Rendering {rset_context.custom_name}")
            context.scene.renderset_context_index = index
            RendersetRenderContexts.render_initialized = True
            RendersetRenderContexts.rendering = True
            scene_output_format = scene_props.get_output_format(context)
            try:
                rset_context.render(
                    context,
                    time=RendersetRenderContexts.frozen_time,
                    override_folder_path=(
                        scene_output_format.preset_folder_path if self.preview else None
                    ),
                )
            except Exception as e:
                if self.preview:
                    rset_context.reset_preview_settings(context)
                self.reset(context)

                context.scene.render.use_lock_interface = (
                    RendersetRenderContexts.was_interface_locked
                )

                self.report({'ERROR'}, f"Error rendering {rset_context.custom_name}: {e}")
                return {'CANCELLED'}

        return {'PASS_THROUGH'}

    def _draw_color_management_ui(
        self,
        layout: bpy.types.UILayout,
        view_settings: bpy.types.ColorManagedViewSettings,
    ):
        layout.prop(view_settings, "view_transform")
        layout.prop(view_settings, "look")
        layout.separator()
        layout.prop(view_settings, "exposure")
        layout.prop(view_settings, "gamma")

    def _draw_preview_preset_ui(self, context: bpy.types.Context) -> None:
        box = self.layout.box()
        preview_prefs = utils.get_preferences(context).previews
        assert isinstance(preview_prefs, preferences.PreviewPresetProperties)
        scene_output_format = scene_props.get_output_format(context)
        select_preset_folder_operator = None

        box.label(text="Preview preset:")
        row = box.row(align=True)
        row.prop_tabs_enum(preview_prefs, "preview_preset")

        rset_contexts = []
        if self.action == utils.RenderAction.ALL:
            rset_contexts = [
                rset_context
                for rset_context in renderset_context_utils.get_all_renderset_contexts(context)
                if rset_context.include_in_render_all
            ]
        elif self.action == utils.RenderAction.CURRENT:
            rset_contexts.append(renderset_context_utils.get_active_renderset_context(context))

        for i, rset_context in enumerate(rset_contexts):
            assert rset_context is not None
            success, reason = self.can_render_preview(context, rset_context)
            if not success:
                col = box.column()
                col.alert = True
                col.label(
                    text=f"Preview rendering is not supported in '{rset_context.custom_name}' context.",
                    icon='ERROR',
                )
                col.label(text=f"{reason}")
                return

        row = box.row(align=True)
        if preview_prefs.preview_preset == preferences.PreviewPreset.SAMPLE_MULTIPLIER.value:
            box.prop(preview_prefs, "sample_multiplier", slider=True)
        elif preview_prefs.preview_preset == preferences.PreviewPreset.RESOLUTION_MULTIPLIER.value:
            box.prop(preview_prefs, "resolution_multiplier", slider=True)
            out_resolution_x = int(
                context.scene.render.resolution_x
                * context.scene.render.resolution_percentage
                * preview_prefs.resolution_multiplier
                / 10000.0
            )
            out_resolution_y = int(
                context.scene.render.resolution_y
                * context.scene.render.resolution_percentage
                * preview_prefs.resolution_multiplier
                / 10000.0
            )
            row_label = box.row()
            row_label.enabled = False
            row_label.label(text=f"Output resolution: {out_resolution_x}x{out_resolution_y}px")

        custom_view_settings_box = box.box()
        custom_view_settings_box.prop(preview_prefs, "use_custom_view_settings")
        if preview_prefs.use_custom_view_settings:
            self._draw_color_management_ui(
                custom_view_settings_box,
                preview_prefs.view_settings,
            )

        if bpy.app.version < (4, 1, 0):
            select_preset_folder_operator = polib.ui_bpy.OperatorButtonLoader(
                scene_props.SceneSelectOutputFolder,
                output_folder_attribute_name=output_path_format.OutputFormatProperty.PRESET_OUTPUT_FOLDER.value,
                dialog_type=self.action,
            )
        box = self.layout.box()
        output_path_format.draw_output_folder_ui(
            scene_output_format,
            box,
            select_preset_folder_operator,
            scene_props.SceneAddVariable,
            output_path_format.MockRendersetContext(),
            output_path_format.OutputFormatProperty.PRESET_OUTPUT_FOLDER,
            label="Preview Output Folder Path:",
        )

    def draw(self, context: bpy.types.Context) -> None:
        if bpy.data.filepath == "":
            col = self.layout.column()
            col.alert = True
            col.label(text="Attempting to render an unsaved file!", icon='ERROR')
            col.separator()
            col.label(text="Some features may not work correctly!")

        if self.preview:
            self._draw_preview_preset_ui(context)

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        # NOTE: Do not setup any additional state in the 'invoke' method. This operator is used
        # for headless rendering, where only the 'execute' method is called by default.
        if bpy.data.filepath == "" or self.preview:
            return context.window_manager.invoke_props_dialog(self, width=400)

        return self.execute(context)


MODULE_CLASSES.append(RendersetRenderContexts)


@polib.log_helpers_bpy.logged_operator
class RendersetOpenResultFolder(bpy.types.Operator):
    bl_idname = "renderset.open_result_folder"
    bl_label = "Open Result Folder"
    bl_description = "Opens the last render result output folder in file explorer"
    bl_options = {'REGISTER'}

    rset_context_idx: bpy.props.IntProperty(name="rset_context_idx", default=-1)
    preview: bpy.props.BoolProperty(
        name="preview",
        default=False,
    )

    @classmethod
    def description(
        cls, context: bpy.types.Context, properties: bpy.types.OperatorProperties
    ) -> str:
        if properties.preview:
            return "Opens the last preview render result output folder in file explorer"
        return "Opens the last render result output folder in file explorer"

    def execute(self, context: bpy.types.Context):
        if not renderset_context_utils.is_valid_renderset_context_index(
            context, self.rset_context_idx
        ):
            self.report({'ERROR'}, "Cannot infer path of non-existing renderset context")
            return {'CANCELLED'}

        rset_context = context.scene.renderset_contexts[self.rset_context_idx]
        if self.preview:
            output_folder_path = rset_context.latest_preview_folder
        else:
            output_folder_path = rset_context.generate_output_folder_path()

        longest_existing_dir_prefix, _ = output_path_format.split_path_to_existing_and_nonexisting(
            output_folder_path
        )
        if not os.path.isdir(longest_existing_dir_prefix):
            self.report({'WARNING'}, "Output path is not valid for this context!")
            return {'CANCELLED'}

        polib.utils_bpy.xdg_open_file(longest_existing_dir_prefix)
        return {'FINISHED'}


MODULE_CLASSES.append(RendersetOpenResultFolder)


@polib.log_helpers_bpy.logged_operator
class RendersetSaveAndPack(bpy.types.Operator, bpy_extras.io_utils.ExportHelper):
    bl_idname = "renderset.save_and_pack"
    bl_label = "Save & Pack (Beta)"
    bl_description = (
        "Save original file, then pack all externally used data and save result in a separate file"
    )
    bl_options = {'REGISTER'}

    # ExportHelper mixin class uses this
    filename_ext = ".blend"

    filter_glob: bpy.props.StringProperty(
        default="*.blend",
        options={'HIDDEN'},
    )

    open_packed: bpy.props.BoolProperty(
        name="Open packed",
        description="Open the packed copy instead of going back to working copy with dependencies",
        default=False,
    )

    pack_ies: bpy.props.BoolProperty(
        name="Pack IES",
        description="Pack IES files from Shaders to Text datablocks",
        default=True,
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        # we only allow save and pack if the file has already been saved somewhere
        return bpy.data.filepath != ""

    @staticmethod
    def get_all_datablocks(data: bpy.types.BlendData) -> typing.Iterable[bpy.types.ID]:
        for member_variable_name in dir(data):
            member_variable = getattr(data, member_variable_name)
            if isinstance(member_variable, bpy.types.bpy_prop_collection):
                for datablock in member_variable:
                    if isinstance(datablock, bpy.types.ID):
                        yield datablock

    @staticmethod
    def remove_all_unused_datablocks(data: bpy.types.BlendData, max_iterations: int = 200) -> None:
        # we need to remove datablocks in multiple iterations because fake_user datablocks
        # may depend on other datablocks, thus increasing their users count as well
        iteration = 0
        while True:
            to_remove = []
            for datablock in RendersetSaveAndPack.get_all_datablocks(data):
                if datablock.library is not None:
                    if datablock.use_fake_user and datablock.users == 1:
                        to_remove.append(datablock)
                    elif datablock.users == 0:
                        to_remove.append(datablock)

            if len(to_remove) > 0:
                logger.debug(f"Iteration {iteration}, removing {len(to_remove)} unused datablocks.")
                iteration += 1
                bpy.data.batch_remove(to_remove)
                if iteration > max_iterations:
                    logger.error(
                        f"Not able to remove all unused datablocks local after "
                        f"{iteration} iterations. Aborting!"
                    )
                    break
            else:
                break

    @staticmethod
    def make_all_datablocks_local(data: bpy.types.BlendData, max_iterations: int = 200) -> None:
        # datablocks in blender have a lot of complex dependencies, for example:
        # collections depend on objects, objects depend on meshes, etc...
        # that means we can't make the dependencies local before making their "parents"
        # local first. doing that results in datablock.library staying the same
        # that's why we have to do multiple iterations
        iteration = 0
        non_local_datablocks = -1
        while True:
            previous_non_local_datablocks = non_local_datablocks
            non_local_datablocks = 0
            for datablock in RendersetSaveAndPack.get_all_datablocks(data):
                if datablock.library is not None:
                    if not datablock.use_fake_user or datablock.users >= 2:
                        # we do not count datablocks that have fake_user and are not used
                        non_local_datablocks += 1

            if (
                previous_non_local_datablocks >= 0
                and non_local_datablocks >= previous_non_local_datablocks
            ):
                logger.debug(f"Final non local datablocks: {non_local_datablocks}")
                break

            logger.debug(
                f"Iteration {iteration}, non local datablocks {previous_non_local_datablocks} -> {non_local_datablocks}"
            )
            iteration += 1
            if iteration > max_iterations:
                logger.error(
                    f"Not able to make all datablocks local after "
                    f"{iteration} iterations. Aborting!"
                )
                break

            for datablock in RendersetSaveAndPack.get_all_datablocks(data):
                datablock.make_local()

        # check that everything is local now, log warnings otherwise
        for datablock in RendersetSaveAndPack.get_all_datablocks(data):
            if datablock.library is not None:
                logger.warning(
                    f"{type(datablock).__name__} datablock (name='{datablock.name}') is still "
                    f"using library {datablock.library.name} after packing!"
                )

    @staticmethod
    def pack_all_external_data() -> None:
        # pack_all fails if the image is not reachable, we have to set filepath of all images
        # that don't exist to ""
        for img in bpy.data.images:
            abspath = os.path.abspath(bpy.path.abspath(img.filepath, library=img.library))
            if not os.path.exists(abspath):
                logger.warning(
                    f"Image datablock (name='{img.name}') references non-existent file '{img.filepath}'. "
                    f"This image's filepath will be set to \"\" to skip it when packing."
                )
                img.filepath = ""

        bpy.ops.file.pack_all()

    @staticmethod
    def pack_external_ies() -> None:
        """Packs external IES files from ShaderNodeTexIES nodes to Text datablocks."""
        # Sometimes IES files contain non-UTF-8 characters in the comments
        # These characters will make the UTF-8 decoding fail, so we decode the file with latin-1
        # Latin-1 never fails to decode, but it can replace the original characters with others
        # This can produce some weird characters in the comments, but the important values will remain intact
        CODECS = ['utf-8', 'latin-1']
        for datablock in itertools.chain(bpy.data.materials, bpy.data.lights):
            if not datablock.use_nodes or datablock.node_tree is None:
                continue

            nodes = typing.cast(
                typing.Set[bpy.types.ShaderNodeTexIES],
                polib.node_utils_bpy.find_nodes_in_tree(
                    datablock.node_tree, lambda x: x.bl_idname == 'ShaderNodeTexIES'
                ),
            )
            for node in nodes:
                if node.mode != 'EXTERNAL':
                    continue

                abspath = polib.utils_bpy.normalize_path(bpy.path.abspath(node.filepath))
                if not polib.utils_bpy.isfile_case_sensitive(abspath):
                    continue

                # Create new text datablock, load IES content inside and use it in the node
                text_name = "PACKED_" + (
                    node.filepath if node.filepath.startswith("//") else abspath
                )
                text = bpy.data.texts.get(text_name)
                if text is None:
                    text = bpy.data.texts.new(text_name)

                ies_str = None
                for codec in CODECS:
                    try:
                        with open(abspath, encoding=codec) as f:
                            ies_str = f.read()
                    except UnicodeDecodeError:
                        pass
                if ies_str is None:
                    logger.error(f"IES file '{node.filepath}' could not be decoded")
                    continue

                text.clear()
                text.from_string(ies_str)

                node.mode = 'INTERNAL'
                node.ies = text

    def execute(self, context: bpy.types.Context):
        if bpy.data.is_dirty:
            bpy.ops.wm.save_mainfile()

        previous_filepath = bpy.data.filepath

        try:
            RendersetSaveAndPack.remove_all_unused_datablocks(bpy.data)
            RendersetSaveAndPack.make_all_datablocks_local(bpy.data)
            RendersetSaveAndPack.pack_all_external_data()
            if self.pack_ies:
                RendersetSaveAndPack.pack_external_ies()

            parent_dirname = os.path.dirname(self.filepath)
            if not os.path.isdir(parent_dirname):
                os.makedirs(parent_dirname)
            bpy.ops.wm.save_as_mainfile(filepath=self.filepath)

        finally:
            if not self.open_packed:
                bpy.ops.wm.open_mainfile(filepath=previous_filepath)

        return {'FINISHED'}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        filepath, ext = os.path.splitext(bpy.data.filepath)
        self.filepath = f"{filepath}_PACKED{ext}"

        return super().invoke(context, event)


MODULE_CLASSES.append(RendersetSaveAndPack)


@polib.log_helpers_bpy.logged_operator
class RendersetSelectCamera(bpy.types.Operator):
    bl_idname = "renderset.select_camera"
    bl_label = "Select Camera"
    bl_description = "Selects camera that is used by active renderset context"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return context.scene.camera is not None

    def execute(self, context: bpy.types.Context):
        # We use context.scene.camera because camera in renderset context
        # may not be synced with the user selection before context
        # gets changed
        camera = context.scene.camera
        polib.asset_pack_bpy.clear_selection(context)
        try:
            # Objects are only selectible if they are not excluded from the view layer
            # To find all view layers we would need to find all collections and then find
            # all view layers containing those collections, which can be quite heavy depending
            # on the hierarchy depth. Doing this in try except block is more straightforward.
            camera.select_set(True)
            context.view_layer.objects.active = camera
            logger.info(f"Selected camera {camera.name}")
        except RuntimeError:
            logger.exception(f"Uncaught exception while selecting camera")
            self.report(
                {'ERROR'},
                "Camera can't be selected. It may be in another scene or the view layer is disabled.",
            )
            return {'CANCELLED'}

        return {'FINISHED'}


MODULE_CLASSES.append(RendersetSelectCamera)


@polib.log_helpers_bpy.logged_operator
class SwitchRenderOrientation(bpy.types.Operator):
    bl_idname = "renderset.switch_render_orientation"
    bl_description = "Switch between Landscape and Portrait render orientation"
    bl_options = {'REGISTER', 'UNDO'}
    bl_label = "Switch Render Orientation"

    def execute(self, context: bpy.types.Context):
        render = context.scene.render
        render.resolution_x, render.resolution_y = render.resolution_y, render.resolution_x
        return {'FINISHED'}


MODULE_CLASSES.append(SwitchRenderOrientation)


class BatchRenameItem(bpy.types.PropertyGroup):
    selected: bpy.props.BoolProperty(
        name="Selected", description="Select item for renaming", default=True
    )


MODULE_CLASSES.append(BatchRenameItem)


@polib.log_helpers_bpy.logged_operator
class BatchRenameRendersetContexts(bpy.types.Operator):
    bl_idname = "renderset.batch_rename_contexts"
    bl_label = "Batch Rename Contexts"
    bl_description = (
        "Rename multiple renderset contexts at once using find and replace or a regular expression"
    )
    bl_options = {'UNDO'}

    find: bpy.props.StringProperty(
        name="Input",
        default="",
        options={'TEXTEDIT_UPDATE'},
        update=lambda self, context: BatchRenameRendersetContexts._find_updated(self, context),
    )
    replace: bpy.props.StringProperty(
        name="Replace With",
        default="",
        options={'TEXTEDIT_UPDATE'},
        update=lambda self, context: BatchRenameRendersetContexts._replace_updated(self, context),
    )

    use_regex: bpy.props.BoolProperty(
        name="Use Regex",
        default=False,
        update=lambda self, context: BatchRenameRendersetContexts._use_regex_updated(self, context),
    )

    applicable_contexts: bpy.props.CollectionProperty(type=BatchRenameItem, options={'HIDDEN'})

    regex_compilation_error: typing.Optional[str] = None
    regex_replace_error: typing.Optional[str] = None

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return len(context.scene.renderset_contexts) > 0

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        split = layout.split(factor=0.2)
        labels_col = split.column(align=True)
        labels_col.label(text="Find:")
        labels_col.label(text="Replace:")

        prop_col = split.column(align=True)
        row = prop_col.row(align=True)
        row.alert = self.use_regex and not self.is_find_regex_valid
        row.prop(self, "find", text="")
        row.prop(self, "use_regex", text="", toggle=True, icon='SORTBYEXT')

        row = prop_col.row(align=True)
        row.alert = self.use_regex and not self.is_replace_regex_valid
        row.prop(self, "replace", text="")

        if self.use_regex:
            if not self.is_find_regex_valid:
                row = layout.row()
                row.alert = True
                row.label(text=BatchRenameRendersetContexts.regex_compilation_error, icon='ERROR')
            # only display replace error if find regex is valid
            elif not self.is_replace_regex_valid:
                row = layout.row()
                row.alert = True
                row.label(text=BatchRenameRendersetContexts.regex_replace_error, icon='ERROR')

            if not self.is_find_regex_valid or not self.is_replace_regex_valid:
                return

        layout.separator()

        box = layout.box()
        box.label(text="Preview:")
        col = box.column(align=True)
        new_context_names = set()
        for rset_context in context.scene.renderset_contexts:
            changed, new_context_name = self._apply_rename(rset_context.custom_name)
            new_context_names.add(new_context_name)
            row = col.row(align=True)
            applicable_context = self.applicable_contexts.get(rset_context.custom_name)
            assert applicable_context is not None
            row.prop(applicable_context, "selected", text="")
            sub = row.row()
            sub.enabled = changed and applicable_context.selected
            sub.label(
                text=(
                    f"{rset_context.custom_name} -> {new_context_name}"
                    if applicable_context.selected
                    else rset_context.custom_name
                )
            )

        # check for duplicates
        if len(new_context_names) != len(context.scene.renderset_contexts):
            row = layout.row()
            row.alert = True
            row.label(
                text="Rename will create duplicate names. Duplicate suffix will be added.",
                icon='ERROR',
            )

        if any(name == "" for name in new_context_names):
            row = layout.row()
            row.alert = True
            row.label(text="Rename will create empty name(s)!", icon='ERROR')

    def execute(self, context: bpy.types.Context):
        if self.use_regex:
            if not self.is_find_regex_valid:
                self.report({'ERROR'}, f"Provided find regex is not valid '{self.find}'!")
                return {'CANCELLED'}
            if not self.is_replace_regex_valid:
                self.report({'ERROR'}, f"Provided replace regex is not valid '{self.replace}'!")
                return {'CANCELLED'}

        renamed_contexts = 0
        for rset_context in context.scene.renderset_contexts:
            if not self._should_apply_rename(rset_context):
                continue

            changed, rset_context.custom_name = self._apply_rename(rset_context.custom_name)
            renamed_contexts += int(changed)

        self.report({'INFO'}, f"Renamed {renamed_contexts} contexts")
        return {'FINISHED'}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        self._initialize_applicable_contexts(context)
        BatchRenameRendersetContexts.regex_compilation_error = None
        BatchRenameRendersetContexts.regex_replace_error = None
        return context.window_manager.invoke_props_dialog(self, width=400)

    @property
    def is_replace_regex_valid(self) -> bool:
        return BatchRenameRendersetContexts.regex_replace_error is None

    @property
    def is_find_regex_valid(self) -> bool:
        return BatchRenameRendersetContexts.regex_compilation_error is None

    def _apply_rename(self, context_name: str) -> typing.Tuple[bool, str]:
        new_context_name = ""
        if self.use_regex and self.is_find_regex_valid:
            new_context_name = re.sub(self.find, self.replace, context_name)
        else:
            new_context_name = context_name.replace(self.find, self.replace)

        return new_context_name != context_name, new_context_name

    def _find_updated(self, context: bpy.types.Context) -> None:
        if self.use_regex:
            try:
                re.compile(self.find)
                BatchRenameRendersetContexts.regex_compilation_error = None
            except re.error as e:
                BatchRenameRendersetContexts.regex_compilation_error = f"Find: {e}"

        # The regex might've changed so the replace might be valid now, we call the update manually
        BatchRenameRendersetContexts._replace_updated(self, context)

    def _replace_updated(self, context: bpy.types.Context) -> None:
        # Try replacing first context with the replace string to see if it is valid - e. g.
        # when using replacement groups.
        name = context.scene.renderset_contexts[0].custom_name
        try:
            re.sub(self.find, self.replace, name)
            BatchRenameRendersetContexts.regex_replace_error = None
        except re.error as e:
            BatchRenameRendersetContexts.regex_replace_error = f"Replace: {e}"

    def _use_regex_updated(self, context: bpy.types.Context) -> None:
        BatchRenameRendersetContexts._find_updated(self, context)
        BatchRenameRendersetContexts._replace_updated(self, context)

    def _should_apply_rename(self, rset_context: renderset_context.RendersetContext) -> bool:
        """Checks if the rename should be applied to the given renderset context.

        Returns True if the context is not found in the selection. This can happen when the
        operator is called without 'invoke'.
        """
        item = self.applicable_contexts.get(rset_context.custom_name)
        if item is None:
            return True

        return item.selected

    def _initialize_applicable_contexts(self, context: bpy.types.Context) -> None:
        """Initializes the 'applicable_contexts' collection with all renderset contexts."""
        self.applicable_contexts.clear()
        for rset_context in context.scene.renderset_contexts:
            item = self.applicable_contexts.add()
            item.name = rset_context.custom_name
            item.selected = True


MODULE_CLASSES.append(BatchRenameRendersetContexts)


@polib.log_helpers_bpy.logged_operator
class DumpStoredValues(bpy.types.Operator):
    bl_idname = "renderset.dev_dump_stored_values"
    bl_label = "Dump Stored Values"
    bl_description = "Dump values stored in active renderset context"
    bl_options = {'REGISTER'}

    @staticmethod
    def sort_dict(dict_to_sort: typing.Dict[str, typing.Any]) -> typing.Dict[str, typing.Any]:
        """Sorts dict recursively, first primitive values, then nested dictionaries."""
        result = {}
        for key, value in sorted(dict_to_sort.items()):
            if not isinstance(value, dict):
                result[key] = value
        for key, value in sorted(dict_to_sort.items()):
            if isinstance(value, dict):
                result[key] = DumpStoredValues.sort_dict(value)
        return result

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return len(context.scene.renderset_contexts) > 0

    def execute(self, context: bpy.types.Context):
        dump_filepath = os.path.join(tempfile.gettempdir(), "renderset_dumps")
        os.makedirs(dump_filepath, exist_ok=True)

        active_context = renderset_context_utils.get_active_renderset_context(context)
        with open(os.path.join(dump_filepath, f"{active_context.custom_name}.json"), "w") as fp:
            json.dump(DumpStoredValues.sort_dict(active_context.synced_data_dict), fp, indent=4)

        polib.utils_bpy.xdg_open_file(dump_filepath)
        return {'FINISHED'}


MODULE_CLASSES.append(DumpStoredValues)


class RendersetPanelInfoMixin:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "polygoniq"


@polib.log_helpers_bpy.logged_panel
class RendersetPanel(RendersetPanelInfoMixin, bpy.types.Panel):
    bl_idname = "VIEW3D_PT_renderset"
    bl_label = str(bl_info.get("name", "renderset")).replace("_", " ")
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "polygoniq"
    bl_order = 20
    bl_options = {'DEFAULT_CLOSED'}

    @staticmethod
    def toggle_button(layout: bpy.types.UILayout, data, attribute: str, text: str = "") -> None:
        layout.prop(
            data,
            attribute,
            text=text,
            icon='TRIA_DOWN' if getattr(data, attribute) else 'TRIA_RIGHT',
            icon_only=True,
            expand=True,
        )

    def draw_stored_values(
        self, rset_context: renderset_context.RendersetContext, layout: bpy.types.UILayout
    ) -> None:
        box = layout.row().box()
        box.label(text=f"{'-' * 20} ADD Overrides {'-' * 20}")
        col = box.column()
        for prop_path in sorted(rset_context.overrides.add):
            col.row().label(text=prop_path)

        box.label(text=f"{'-' * 20} REMOVE Overrides {'-' * 20}")
        col = box.column()
        for prop_path in sorted(rset_context.overrides.remove):
            col.row().label(text=prop_path)

        box.label(text=f"{'-' * 20} Stored values {'-' * 20}")
        self._debug_draw_dict_on_rows(
            box.column(), 0, DumpStoredValues.sort_dict(rset_context.synced_data_dict)
        )

    def draw_header(self, context: bpy.types.Context) -> None:
        self.layout.label(
            text="", icon_value=polib.ui_bpy.icon_manager.get_polygoniq_addon_icon_id("renderset")
        )

    def draw_header_preset(self, context: bpy.types.Context) -> None:
        master_row = self.layout.row(align=True)
        master_row.row().operator("preferences.addon_show", icon='SETTINGS').module = __package__
        polib.ui_bpy.draw_doc_button(master_row.row(), __package__)

    def draw(self, context: bpy.types.Context) -> None:
        polib.ui_bpy.draw_conflicting_addons(
            self.layout, __package__, preferences.CONFLICTING_ADDONS
        )
        layout = self.layout
        scene = context.scene
        prefs = utils.get_preferences(context)

        row = layout.row()

        col = row.column(align=True)
        col.operator(RendersetContextList_OT_AddItem.bl_idname, text="", icon='ADD')
        col.operator(RendersetContextList_OT_DeleteItem.bl_idname, text="", icon='REMOVE')
        col.separator()
        col.operator(RendersetContextList_OT_MoveItem.bl_idname, text="", icon='TRIA_UP').delta = -1
        col.operator(
            RendersetContextList_OT_MoveItem.bl_idname, text="", icon='TRIA_DOWN'
        ).delta = 1
        col.separator()
        if multi_edit.multi_edit_mode_enabled(context):
            r = col.row()
            r.alert = True
            r.operator(multi_edit.RendersetLeaveMultiEdit.bl_idname, text="", icon='CHECKMARK')
        else:
            col.operator(multi_edit.RendersetEnterMultiEdit.bl_idname, text="", icon='RENDERLAYERS')
        col.separator()
        col.operator(BatchRenameRendersetContexts.bl_idname, text="", icon='GREASEPENCIL')
        col.operator(lister.RendersetLister.bl_idname, text="", icon='LINENUMBERS_ON')
        col.prop(prefs, "show_context_colors", text="", icon='COLOR', emboss=False)

        col = row.column(align=True)
        col.template_list(
            "MY_UL_RendersetContextList",
            "RenderContextList",
            scene,
            "renderset_contexts",
            scene,
            "renderset_context_index",
            rows=6,
        )
        col.enabled = not multi_edit.multi_edit_mode_enabled(context)

        renderset_context_utils.renderset_context_list_ensure_valid_index(context)

        box = col.box()
        row = box.row()
        col = row.column(align=True)
        if context.scene.camera:

            render_current = col.operator(
                RendersetRenderContexts.bl_idname, text="Render Current", icon='SHADING_BBOX'
            )
            render_current.action = utils.RenderAction.CURRENT
            render_current.preview = False

            render_all = col.operator(
                RendersetRenderContexts.bl_idname,
                text=f"Render All ({renderset_context_utils.get_included_renderset_contexts_count(context)})",
                icon='IMGDISPLAY',
            )
            render_all.action = utils.RenderAction.ALL
            render_all.preview = False

            col = row.column(align=True)
            preview_current = col.operator(
                RendersetRenderContexts.bl_idname, text="Preview Current", icon='VIEWZOOM'
            )
            preview_current.action = utils.RenderAction.CURRENT
            preview_current.preview = True

            preview_all = col.operator(
                RendersetRenderContexts.bl_idname,
                text=f"Preview All ({renderset_context_utils.get_included_renderset_contexts_count(context)})",
                icon='ZOOM_IN',
            )
            preview_all.action = utils.RenderAction.ALL
            preview_all.preview = True

        else:
            # no action specification needed, poll method ensures that this cannot be invoked
            col.operator(RendersetRenderContexts.bl_idname, text="No Camera", icon='SHADING_BBOX')
            col.operator(RendersetRenderContexts.bl_idname, text="No Camera", icon='IMGDISPLAY')
            col = row.column(align=True)
            col.operator(RendersetRenderContexts.bl_idname, text="No Camera", icon='VIEWZOOM')
            col.operator(RendersetRenderContexts.bl_idname, text="No Camera", icon='ZOOM_IN')

        if len(scene.renderset_contexts) == 0:
            return
        item = scene.renderset_contexts[scene.renderset_context_index]

        # Show context stored values
        if prefs.debug_enabled:
            row = layout.row()
            row.scale_x = 0.7
            row.scale_y = 0.7
            RendersetPanel.toggle_button(
                row, prefs, "show_context_stored_values", text="Show stored values"
            )

            if prefs.show_context_stored_values:
                layout.operator(DumpStoredValues.bl_idname, icon='FILE_TICK')
                self.draw_stored_values(item, layout)

    def _debug_draw_dict_on_rows(
        self,
        layout: bpy.types.UILayout,
        indentation: int,
        dict_to_draw: typing.Dict[str, typing.Any],
    ) -> None:
        for key, value in dict_to_draw.items():
            row = layout.row()
            if isinstance(value, dict):
                row.label(text=f"{indentation * ' '}{key}:")
                self._debug_draw_dict_on_rows(layout, indentation + 6, value)
            else:
                row.label(text=f"{indentation * ' '}{key}: {value}")


MODULE_CLASSES.append(RendersetPanel)


@polib.log_helpers_bpy.logged_panel
class RendersetToolboxPanel(RendersetPanelInfoMixin, bpy.types.Panel):
    bl_idname = "VIEW_3D_PT_renderset_toolbox"
    bl_parent_id = RendersetPanel.bl_idname
    bl_label = "Toolbox"

    def draw_header(self, context: bpy.types.Context) -> None:
        self.layout.label(text="", icon='TOOL_SETTINGS')

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        layout.operator(RendersetSelectCamera.bl_idname, icon='RESTRICT_SELECT_OFF')
        layout.operator(RendersetAddContextFromViewport.bl_idname, icon='VIEW3D')
        layout.operator(RendersetAddContextPerCamera.bl_idname, icon='CON_CAMERASOLVER')
        layout.operator(RendersetSaveAndPack.bl_idname, icon='PACKAGE')


MODULE_CLASSES.append(RendersetToolboxPanel)


@polib.log_helpers_bpy.logged_panel
class RendersetGlobalSettingsPanel(RendersetPanelInfoMixin, bpy.types.Panel):
    bl_idname = "VIEW_3D_PT_renderset_global_settings"
    bl_parent_id = RendersetPanel.bl_idname
    bl_label = "Global Settings"
    bl_description = (
        "Settings that are not stored in renderset context, they are drawn in "
        "renderset UI because it's convenient to have them accessible there"
    )

    def draw_header(self, context: bpy.types.Context) -> None:
        self.layout.label(text="", icon='PREFERENCES')

    def draw(self, context: bpy.types.Context) -> None:
        col = self.layout.column()

        row = col.row(align=True)
        row.prop(context.scene.render, "use_simplify")
        if context.scene.render.engine == 'CYCLES':
            if context.scene.render.use_simplify:
                col = self.layout.column()
                col.label(text="Cycles Texture Size", icon='UV_DATA')
                col.prop(context.scene.cycles, "texture_limit", text="Viewport")
                col.prop(context.scene.cycles, "texture_limit_render", text="Render")

            col.separator()
            row = col.row(align=True)
            row.prop(context.scene.cycles, "use_auto_tile")
            if context.scene.cycles.use_auto_tile:
                row.prop(context.scene.cycles, "tile_size")

            if bpy.app.version >= (3, 5, 0):
                col.prop(context.scene.cycles, "use_light_tree")

        row = col.row(align=True)
        row.prop(context.scene.render, "use_persistent_data")

        is_region_stored = sync_overrides.is_render_region_stored(context)
        col.separator()
        col.operator(
            sync_overrides.ToggleStoreCameraRenderRegion.bl_idname,
            icon='SELECT_SET' if not is_region_stored else 'PANEL_CLOSE',
            text=(
                "Store Camera Render Region"
                if not is_region_stored
                else "Remove Storing Camera Render Region"
            ),
        )


MODULE_CLASSES.append(RendersetGlobalSettingsPanel)


@polib.log_helpers_bpy.logged_panel
class RendersetContextSettingsPanel(RendersetPanelInfoMixin, bpy.types.Panel):
    bl_idname = "VIEW_3D_PT_renderset_context_settings"
    bl_parent_id = RendersetPanel.bl_idname
    bl_label = "Context Settings"

    def draw_header(self, context: bpy.types.Context) -> None:
        self.layout.label(text="", icon='FILE_CACHE')

    def draw_header_preset(self, context):
        if utils.get_preferences(context).show_context_colors:
            row = self.layout.row()
            row.alignment = 'RIGHT'
            row.scale_x = 0.25
            row.prop(
                renderset_context_utils.get_active_renderset_context(context), "color", text=""
            )

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        layout.use_property_split = True

        if len(context.scene.renderset_contexts) == 0:
            return

        rset_context = context.scene.renderset_contexts[context.scene.renderset_context_index]

        col = layout.column(align=True)
        col.prop(rset_context, "render_type")
        col.prop(context.scene.render, "engine")

        col = layout.column(align=True)
        if context.scene.render.engine == 'CYCLES':
            col.separator()
            col.prop(context.scene.cycles, "samples")
            col.prop(context.scene.cycles, "max_bounces")
        elif context.scene.render.engine in {'BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'}:
            col.separator()
            col.prop(context.scene.eevee, "taa_render_samples")

        col.separator()
        col.prop(context.scene.view_settings, "view_transform")
        col.prop(context.scene.view_settings, "look")
        col.prop(context.scene.view_settings, "exposure")
        col.prop(context.scene.view_settings, "gamma")

        col.separator()
        res_col = col.column(align=True)
        res_col.use_property_split = False
        row = res_col.row(align=True)
        left = row.column(align=True)
        left.prop(context.scene.render, "resolution_x")
        left.prop(context.scene.render, "resolution_y")
        right = row.column(align=True)
        right.scale_x = 1.5
        right.scale_y = 2.0
        right.operator(SwitchRenderOrientation.bl_idname, icon='FILE_REFRESH', text="")
        res_col.prop(context.scene.render, "resolution_percentage")

        if context.scene.render.engine == 'CYCLES':
            col.separator()
            col.prop(context.scene.cycles, "sample_clamp_direct")
            col.prop(context.scene.cycles, "sample_clamp_indirect")
            row = col.row(align=True)
            if rset_context.render_type == renderset_context.RenderType.ANIMATION.value:
                seed_col = row.column()
                if not context.scene.cycles.use_animated_seed:
                    seed_col.alert = True
                    col.label(
                        text="Using constant seed can produce artifacts visible between frames!",
                        icon='ERROR',
                    )
                seed_col.prop(
                    context.scene.cycles, "use_animated_seed", icon_only=True, icon='TIME'
                )

        col.separator()
        col.prop(context.scene, "frame_current")
        if rset_context.render_type == renderset_context.RenderType.ANIMATION.value:
            col.prop(context.scene, "frame_start")
            col.prop(context.scene, "frame_end")


MODULE_CLASSES.append(RendersetContextSettingsPanel)


@polib.log_helpers_bpy.logged_panel
class RendersetCameraPanel(RendersetPanelInfoMixin, bpy.types.Panel):
    bl_idname = "VIEW_3D_PT_renderset_camera"
    bl_parent_id = RendersetPanel.bl_idname
    bl_label = "Camera"

    def draw_header(self, context: bpy.types.Context) -> None:
        self.layout.label(text="", icon='CAMERA_DATA')

    def draw_header_preset(self, context: bpy.types.Context) -> None:
        row = self.layout.row(align=True)

        camera_row = row.row(align=True)
        camera_row.prop(context.scene, "camera", text="", icon='CAMERA_DATA')
        camera_row.scale_x = (
            0.79  # aligns the two overlapping camera and header icons in default panel scale
        )

        row.separator()
        row.operator(RendersetSelectCamera.bl_idname, icon='RESTRICT_SELECT_OFF', text="")
        row.prop(context.space_data, "lock_camera", icon='LOCKVIEW_ON', toggle=True, text="")

    def draw(self, context: bpy.types.Context) -> None:
        if context.scene.camera is None:
            return
        camera_data = context.scene.camera.data
        if camera_data is None:
            return

        self.layout.use_property_split = True
        col = self.layout.column(align=True)
        col.prop(context.scene.camera, "name")

        col.separator()
        if camera_data.type != 'ORTHO':
            col.prop(camera_data, "lens")
        col.prop(camera_data, "clip_start")
        col.prop(camera_data, "clip_end")

        col.separator()
        col.prop(camera_data, "shift_x")
        col.prop(camera_data, "shift_y")

        col.separator()
        row = col.row(align=True)
        row.use_property_split = False
        row.prop(camera_data, "show_passepartout", text="Passepartout")
        row.prop(camera_data, "passepartout_alpha", text="")


MODULE_CLASSES.append(RendersetCameraPanel)


@polib.log_helpers_bpy.logged_panel
class RendersetWorldPanel(RendersetPanelInfoMixin, bpy.types.Panel):
    bl_idname = "VIEW_3D_PT_renderset_world"
    bl_parent_id = RendersetPanel.bl_idname
    bl_label = "World"

    def draw_header(self, context: bpy.types.Context) -> None:
        self.layout.label(text="", icon='WORLD_DATA')

    def draw_header_preset(self, context: bpy.types.Context) -> None:
        self.layout.prop(context.scene, "world", text="")

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        if context.scene.world is None:
            return

        layout.use_property_split = True
        col = layout.column()
        col.prop(context.scene.world, "name")
        col.prop(context.scene.render, "film_transparent")


MODULE_CLASSES.append(RendersetWorldPanel)


@polib.log_helpers_bpy.logged_panel
class RendersetOutputPanel(RendersetPanelInfoMixin, bpy.types.Panel):
    bl_idname = "VIEW_3D_PT_renderset_output"
    bl_parent_id = RendersetPanel.bl_idname
    bl_label = "Output"

    def draw_header(self, context: bpy.types.Context) -> None:
        self.layout.label(text="", icon='OUTPUT')

    def draw(self, context: bpy.types.Context) -> None:
        if len(context.scene.renderset_contexts) > 0:
            image_settings = context.scene.render.image_settings
            self.layout.template_image_settings(image_settings, color_management=False)
            rset_context = context.scene.renderset_contexts[context.scene.renderset_context_index]

            if (
                rset_context.render_type == renderset_context.RenderType.STILL.value
                and context.scene.render.is_movie_format
            ):
                row = self.layout.row()
                row.alert = True
                row.label(text="Movie format is not supported for still renders!", icon='ERROR')


MODULE_CLASSES.append(RendersetOutputPanel)


class RendersetOutputFolderPanel(RendersetPanelInfoMixin, bpy.types.Panel):
    bl_idname = "VIEW_3D_PT_renderset_output_folder"
    bl_parent_id = RendersetOutputPanel.bl_idname
    bl_label = "Output Folder"

    def draw_header(self, context: bpy.types.Context) -> None:
        self.layout.label(text="", icon='FILE_FOLDER')

    def draw_header_preset(self, context: bpy.types.Context) -> None:
        if len(context.scene.renderset_contexts) > 0:
            rset_context = context.scene.renderset_contexts[context.scene.renderset_context_index]
            self.layout.prop(
                rset_context,
                "override_output_folder",
                text="",
                icon=(
                    'DECORATE_UNLOCKED'
                    if rset_context.override_output_folder
                    else 'DECORATE_LOCKED'
                ),
            )

    def draw(self, context: bpy.types.Context) -> None:
        if len(context.scene.renderset_contexts) > 0:
            rset_context = context.scene.renderset_contexts[context.scene.renderset_context_index]
            scene_output_format = scene_props.get_output_format(context)
            row = self.layout.row()
            row.enabled = rset_context.override_output_folder
            select_folder_operator = None
            if bpy.app.version < (4, 1, 0):
                # We need custom folder picker in the lower versions
                # because the default crashes operator dialogs
                select_folder_operator = (
                    polib.ui_bpy.OperatorButtonLoader(
                        renderset_context.RendersetContextSelectOutputFolder
                    )
                    if row.enabled
                    else polib.ui_bpy.OperatorButtonLoader(scene_props.SceneSelectOutputFolder)
                )
            add_variable_operator = (
                renderset_context.RendersetContextAddVariable
                if row.enabled
                else scene_props.SceneAddVariable
            )

            output_path_format.draw_output_folder_ui(
                rset_context.output_format if row.enabled else scene_output_format,
                row,
                select_folder_operator,
                add_variable_operator,
                rset_context,
                label="",
            )


MODULE_CLASSES.append(RendersetOutputFolderPanel)


class RendersetOutputFilenamesPanel(RendersetPanelInfoMixin, bpy.types.Panel):
    bl_idname = "VIEW_3D_PT_renderset_output_filenames"
    bl_parent_id = RendersetOutputPanel.bl_idname
    bl_label = "Output Filenames"

    def draw_header(self, context: bpy.types.Context) -> None:
        self.layout.label(text="", icon='FILE')

    def draw_header_preset(self, context: bpy.types.Context) -> None:
        if len(context.scene.renderset_contexts) > 0:
            rset_context = context.scene.renderset_contexts[context.scene.renderset_context_index]
            self.layout.prop(
                rset_context,
                "override_output_filenames",
                text="",
                icon=(
                    'DECORATE_UNLOCKED'
                    if rset_context.override_output_filenames
                    else 'DECORATE_LOCKED'
                ),
            )

    def draw(self, context: bpy.types.Context) -> None:
        if len(context.scene.renderset_contexts) > 0:
            rset_context = context.scene.renderset_contexts[context.scene.renderset_context_index]
            scene_output_format = scene_props.get_output_format(context)
            col = self.layout.column()
            col.enabled = rset_context.override_output_filenames
            add_variable_operator = (
                renderset_context.RendersetContextAddVariable
                if col.enabled
                else scene_props.SceneAddVariable
            )

            output_path_format.draw_output_filename_ui(
                rset_context.output_format if col.enabled else scene_output_format,
                col,
                output_path_format.OutputFormatProperty.STILL_IMAGE_FILENAME,
                add_variable_operator,
                rset_context,
                label_text="Still Image",
            )
            output_path_format.draw_output_filename_ui(
                rset_context.output_format if col.enabled else scene_output_format,
                col,
                output_path_format.OutputFormatProperty.ANIMATION_FRAME_FILENAME,
                add_variable_operator,
                rset_context,
                label_text="Animation Frame",
            )
            output_path_format.draw_output_filename_ui(
                rset_context.output_format if col.enabled else scene_output_format,
                col,
                output_path_format.OutputFormatProperty.ANIMATION_MOVIE_FILENAME,
                add_variable_operator,
                rset_context,
                label_text="Animation Movie",
            )


MODULE_CLASSES.append(RendersetOutputFilenamesPanel)


class RendersetPostRenderActionsPanel(RendersetPanelInfoMixin, bpy.types.Panel):
    bl_idname = "VIEW_3D_PT_renderset_post_render_actions"
    bl_parent_id = RendersetOutputPanel.bl_idname
    bl_label = "Post Render Actions"

    def draw_header(self, context: bpy.types.Context) -> None:
        self.layout.label(text="", icon='PRESET')

    def draw_header_preset(self, context: bpy.types.Context) -> None:
        if len(context.scene.renderset_contexts) > 0:
            rset_context = context.scene.renderset_contexts[context.scene.renderset_context_index]
            self.layout.prop(
                rset_context,
                "override_post_render_actions",
                text="",
                icon=(
                    'DECORATE_UNLOCKED'
                    if rset_context.override_post_render_actions
                    else 'DECORATE_LOCKED'
                ),
            )

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        rset_context = renderset_context_utils.get_active_renderset_context(context)
        if rset_context is None:
            return
        layout.enabled = rset_context.override_post_render_actions
        action_props = (
            rset_context.post_render_actions
            if rset_context.override_post_render_actions
            else scene_props.get_post_render_actions(context)
        )
        edit_action_operator = (
            renderset_context.RendersetContextEditPostRenderAction
            if rset_context.override_post_render_actions
            else scene_props.SceneEditPostRenderAction
        )
        add_action_operator = (
            renderset_context.RendersetContextAddPostRenderAction
            if rset_context.override_post_render_actions
            else scene_props.SceneAddPostRenderAction
        )
        delete_action_operator = (
            renderset_context.RendersetContextDeletePostRenderAction
            if rset_context.override_post_render_actions
            else scene_props.SceneDeletePostRenderAction
        )
        move_action_operator = (
            renderset_context.RendersetContextMovePostRenderAction
            if rset_context.override_post_render_actions
            else scene_props.SceneMovePostRenderAction
        )
        clear_actions_operator = (
            renderset_context.RendersetContextClearPostRenderActions
            if rset_context.override_post_render_actions
            else scene_props.SceneClearPostRenderActions
        )
        post_render_actions.draw_post_render_actions_ui(
            layout,
            renderset_context.ACTION_UL_RendersetContextPostRenderActionList,
            action_props,
            add_action_operator,
            edit_action_operator,
            delete_action_operator,
            move_action_operator,
            clear_actions_operator,
        )


MODULE_CLASSES.append(RendersetPostRenderActionsPanel)


@polib.log_helpers_bpy.logged_panel
class RendersetOverridesPanel(RendersetPanelInfoMixin, bpy.types.Panel):
    bl_idname = "VIEW_3D_PT_renderset_overrides"
    bl_parent_id = RendersetPanel.bl_idname
    bl_label = "Overrides"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        rset_context = renderset_context_utils.get_active_renderset_context(context)
        return rset_context is not None and len(rset_context.overrides) > 0

    def draw_header(self, context: bpy.types.Context) -> None:
        self.layout.label(text="", icon='DECORATE_OVERRIDE')

    def draw(self, context: bpy.types.Context) -> None:
        rset_context = context.scene.renderset_contexts[context.scene.renderset_context_index]
        self.layout.use_property_split = True

        if len(rset_context.overrides.add) > 0:
            self.layout.label(text="Added Properties", icon='ADD')
            col = self.layout.column()

            # Sort by human readable property name to group props of the same parent
            sorted_add = sorted(
                rset_context.overrides.add,
                key=lambda prop_path: sync_overrides.get_human_readable_property_name(
                    prop_path, rset_context
                ),
            )
            for prop_path in sorted_add:
                prop_parent_path, prop_name = sync_overrides.split_prop_to_path_and_name(prop_path)
                parent = sync_overrides.evaluate_prop_path(prop_parent_path)

                if parent is None or prop_name is None:
                    continue

                serialize_utils.draw_property(
                    parent,
                    prop_name,
                    col,
                    text=sync_overrides.get_human_readable_property_name(prop_path, rset_context),
                )

        if len(rset_context.overrides.remove) > 0:
            self.layout.label(text="Removed Properties", icon='REMOVE')
            col = self.layout.column()
            col.enabled = False

            sorted_remove = sorted(
                rset_context.overrides.remove,
                key=lambda prop_path: sync_overrides.get_human_readable_property_name(
                    prop_path, rset_context
                ),
            )
            for prop_path in sorted_remove:
                prop_parent_path, prop_name = sync_overrides.split_prop_to_path_and_name(prop_path)
                parent = sync_overrides.evaluate_prop_path(prop_parent_path)

                serialize_utils.draw_property(parent, prop_name, col)


MODULE_CLASSES.append(RendersetOverridesPanel)


def renderset_context_changed(self, context: bpy.types.Context) -> None:
    if (
        multi_edit.multi_edit_mode_enabled(context)
        and context.scene.renderset_context_index != context.scene.previous_renderset_context_index
    ):
        context.scene.renderset_context_index = context.scene.previous_renderset_context_index
        logger.warning("Can't change active context while in multi-edit mode!")
        return

    old_context_index = context.scene.previous_renderset_context_index
    old_context_name = "unknown"
    new_context_index = context.scene.renderset_context_index
    new_context_name = "unknown"

    if (
        not renderset_context_utils.SKIP_RENDER_CONTEXT_SYNC
        and renderset_context_utils.is_valid_renderset_context_index(context, old_context_index)
    ):
        old_context = context.scene.renderset_contexts[old_context_index]
        # this context is no longer active but we want to sync before we switch to the next one
        old_context.sync(context)
        old_context_name = old_context.custom_name

    index = context.scene.renderset_context_index
    if not renderset_context_utils.is_valid_renderset_context_index(context, index):
        raise RuntimeError(
            "Invalid new RendersetContext index! Don't know which RendersetContext " "to apply!"
        )
    context.scene.previous_renderset_context_index = index

    if not renderset_context_utils.SKIP_RENDER_CONTEXT_APPLY:
        new_context = context.scene.renderset_contexts[index]
        new_context.apply(context)
        new_context_name = new_context.custom_name

    logger.info(
        f"Switched context from {old_context_name} (index: {old_context_index}) to "
        f"{new_context_name} (index: {new_context_index})"
    )


def ensure_all_contexts_have_same_overrides(
    contexts: typing.List[renderset_context.RendersetContext],
) -> None:
    """Ensures that all contexts have the same overrides

    If all contexts don't have the same overrides, it removes overrides that are not present in all
    contexts.
    """
    if len(contexts) < 2:
        return
    min_add_overrides = contexts[0].overrides.add
    min_remove_overrides = contexts[0].overrides.remove
    max_remove_overrides = contexts[0].overrides.remove

    # Find which overrides are present in all contexts
    for ctx in contexts[1:]:
        min_add_overrides.intersection_update(ctx.overrides.add)
        min_remove_overrides.intersection_update(ctx.overrides.remove)
        max_remove_overrides.update(ctx.overrides.remove)

    # Remove extensive overrides
    for ctx in contexts:
        remove_overrides = [
            override for override in ctx.overrides.add if override not in min_add_overrides
        ]
        ctx.add_overrides(remove_overrides, False)

        add_overrides = [
            override for override in ctx.overrides.remove if override not in min_remove_overrides
        ]
        ctx.add_overrides(add_overrides, True)


def remove_unused_overrides(contexts: typing.List[renderset_context.RendersetContext]) -> None:
    """Removes 'ADD' overrides that store the same value in all contexts

    It expects that all contexts have the same overrides otherwise in can fail. It's useful when
    converting old contexts to the new format which stores much less properties by default.
    """
    if len(contexts) == 0:
        return

    unused_overrides: typing.Set[str] = set()
    if len(contexts) == 1:
        # There is only one context in the blend -> remove all overrides. The blend was created with
        # old renderset enabled but renderset wasn't used here for storing stuff per context.
        unused_overrides = contexts[0].overrides.add
    else:
        ctxs_props = [serialize_utils.flatten_dict(ctx.stored_props_dict) for ctx in contexts]
        first, others = ctxs_props[0], ctxs_props[1:]

        for override in contexts[0].overrides.add:
            if all(first[override] == other[override] for other in others):
                unused_overrides.add(override)

    logger.info(f"Will remove {len(unused_overrides)} unused overrides from all contexts")
    for ctx in contexts:
        logger.info(
            f"Removing {len(unused_overrides)} unused overrides from context: {ctx.custom_name}"
        )
        ctx.add_overrides(unused_overrides, False)


def set_restriction_toggles_based_on_old_context(
    old_context: renderset_context_old.RendersetContextOld,
) -> None:
    """Because preferences are lost on addon update, we cannot read settings of old renderset to
    see if remember_all_restriction_toggles and per_object_visibility properties were enabled.
    We can only guess that based on data stored in the context."""
    remember_all_restriction_toggles = False
    per_object_visibility = False

    collections_json = json.loads(old_context.root_collection_json)
    if "hide_select" in collections_json:
        remember_all_restriction_toggles = True

    if old_context.objects_visibility_json != "{}":
        per_object_visibility = True

    collection_toggles_settings = scene_props.get_collection_toggles_settings(bpy.context)
    layer_collection_toggles_settings = scene_props.get_layer_collection_toggles_settings(
        bpy.context
    )
    object_toggles_settings = scene_props.get_object_toggles_settings(bpy.context)

    # These were always stored in renderset 1.9 and older
    collection_toggles_settings.hide_render = True
    layer_collection_toggles_settings.exclude = True
    layer_collection_toggles_settings.holdout = True
    layer_collection_toggles_settings.indirect_only = True

    if remember_all_restriction_toggles:
        collection_toggles_settings.hide_select = True
        collection_toggles_settings.hide_viewport = True
        layer_collection_toggles_settings.hide_viewport = True

    if per_object_visibility:
        object_toggles_settings.hide_render = True
        if remember_all_restriction_toggles:
            object_toggles_settings.hide_select = True
            object_toggles_settings.hide_viewport = True


def check_and_convert_old_contexts() -> None:
    """Converts contexts from renderset 1.9 or older to the new format"""
    old_contexts: typing.List[renderset_context_old.RendersetContextOld] = (
        bpy.context.scene.render_set_contexts
    )
    new_contexts: typing.List[renderset_context.RendersetContext] = (
        bpy.context.scene.renderset_contexts
    )

    if len(new_contexts) > 0 or len(old_contexts) == 0:
        # Already converted or nothing to convert
        return

    set_restriction_toggles_based_on_old_context(old_contexts[0])

    logger.info(f"Converting {len(old_contexts)} old contexts to the new format")
    for old_context in old_contexts:
        new_context = new_contexts.add()
        logger.info(f"Converting '{old_context.custom_name}'")
        new_context.convert_from_old(old_context, bpy.context)

    # Ensure all contexts have the same overrides, it could happen that some of old contexts were
    # missing properties. E.g. contexts were created in old Blender or with old renderset and then
    # only some of them were serialized with newer version of either which stored more properties.
    ensure_all_contexts_have_same_overrides(new_contexts)
    remove_unused_overrides(new_contexts)

    # Switch to the context based on the old stored index. Don't sync or apply, we're just getting
    # to the same state where blend file and old contexts where.
    renderset_context_utils.SKIP_RENDER_CONTEXT_SYNC = True
    renderset_context_utils.SKIP_RENDER_CONTEXT_APPLY = True
    bpy.context.scene.renderset_context_index = bpy.context.scene.render_set_context_index
    renderset_context_utils.SKIP_RENDER_CONTEXT_SYNC = False
    renderset_context_utils.SKIP_RENDER_CONTEXT_APPLY = False

    # Delete old contexts, keep only the first one with warning that contexts were migrated. We
    # don't need the old contexts as the new ones now contain all the data. Note, the new contexts
    # won't disappear even if they are opened with old renderset, in that case Blender just keeps
    # the data stored in bpy.context.scene.renderset_contexts unchanged.
    for i in range(len(old_contexts) - 1, 0, -1):
        bpy.context.scene.render_set_contexts.remove(i)

    bpy.context.scene.render_set_contexts[0].custom_name = (
        "INVALID - DATA MIGRATED TO RENDERSET 2.0! Please install renderset 2.0 or newer"
    )
    # Set old index to a valid value in case this blend is opened with a old renderset
    bpy.context.scene.render_set_context_index = 0


@bpy.app.handlers.persistent
def renderset_initialize_handler(_=None) -> None:
    check_and_convert_old_contexts()

    # Ensure that all stored uuids have serialize_utils.RSET_UUID_PREFIX prefix
    for rset_context in bpy.context.scene.renderset_contexts:
        rset_context.ensure_uuid_prefix()

    the_list: typing.List[renderset_context.RendersetContext] = bpy.context.scene.renderset_contexts
    if len(the_list) == 0:
        item = the_list.add()
        item.init_default(bpy.context)
        bpy.context.scene.renderset_context_index = 0

        # First initialization of renderset in this blend file -> set up default post-render actions
        actions_props = scene_props.get_post_render_actions(bpy.context)
        action = actions_props.actions.add()
        action.action_type = post_render_actions.PostRenderActionType.COPY_OUTPUT_FILE.value
        action.render_layer_type = compositor_helpers.RenderPassType.COMPOSITE.value
        action.output_format.folder_path = os.path.join(
            "{blend_parent_folder}", "renders", "LATEST_RENDERS"
        )
        action.output_format.still_image_filename = "{context_name}"
        action.output_format.animation_frame_filename = "{context_name}{frame_current}"
        action.output_format.animation_movie_filename = "{context_name}{frame_start}-{frame_end}"

    bpy.context.scene.previous_renderset_context_index = bpy.context.scene.renderset_context_index


def register():
    output_path_format.register()
    multi_edit.register()
    lister.register()
    post_render_actions.register()
    preferences.register()
    renderset_context_old.register()
    renderset_context.register()
    scene_props.register()
    sync_overrides.register()

    for cls in MODULE_CLASSES:
        bpy.utils.register_class(cls)

    # TODO: Setters that throw deprecation exception
    # Deprecated renderset properties stored by renderset 1.9 and older
    bpy.types.Scene.render_set_contexts = bpy.props.CollectionProperty(
        type=renderset_context_old.RendersetContextOld,
        description="Deprecated from renderset 2.0, use renderset_contexts instead",
    )
    bpy.types.Scene.render_set_context_index = bpy.props.IntProperty(
        description="Deprecated from renderset 2.0, use renderset_context_index instead"
    )

    # renderset properties stored by renderset 2.0 and newer
    bpy.types.Scene.renderset_contexts = bpy.props.CollectionProperty(
        type=renderset_context.RendersetContext
    )
    bpy.types.Scene.renderset_context_index = bpy.props.IntProperty(
        name="renderset_context_index",
        default=0,
        update=renderset_context_changed,
        description="Currently active renderset context in the scene",
    )
    bpy.types.Scene.previous_renderset_context_index = bpy.props.IntProperty(
        name="previous_renderset_context_index",
        default=-1,
        description="Previously active renderset context in the scene",
    )
    bpy.types.Scene.renderset_old_render_filepath = bpy.props.StringProperty(
        name="renderset_old_render_filepath",
        subtype='FILE_PATH',
    )

    # All datablock that inherit from ID will have this property
    bpy.types.ID.renderset_uuid = bpy.props.StringProperty(default="")
    # ViewLayer doesn't inherit from ID, so we need to add it separately
    bpy.types.ViewLayer.renderset_uuid = bpy.props.StringProperty(default="")

    # Called when a blend file is opened. This hook is not run when renderset is installed in
    # a running Blender or when Blender is opened with a startup file.
    bpy.app.handlers.load_post.append(renderset_initialize_handler)
    # This is called exactly in the situations when load_post is not called = fresh renderset
    # install or File->New.
    bpy.app.timers.register(renderset_initialize_handler, first_interval=0, persistent=False)


def unregister():
    bpy.app.handlers.load_post.remove(renderset_initialize_handler)

    del bpy.types.ViewLayer.renderset_uuid
    del bpy.types.ID.renderset_uuid

    del bpy.types.Scene.previous_renderset_context_index
    del bpy.types.Scene.renderset_context_index
    del bpy.types.Scene.renderset_contexts
    del bpy.types.Scene.render_set_context_index
    del bpy.types.Scene.render_set_contexts

    for cls in reversed(MODULE_CLASSES):
        bpy.utils.unregister_class(cls)

    sync_overrides.unregister()
    scene_props.unregister()
    renderset_context.unregister()
    renderset_context_old.unregister()
    preferences.unregister()
    post_render_actions.unregister()
    lister.unregister()
    multi_edit.unregister()
    output_path_format.unregister()

    # Remove all nested modules from module cache, more reliable than importlib.reload(..)
    # Idea by BD3D / Jacques Lucke
    for module_name in list(sys.modules.keys()):
        if module_name.startswith(__package__):
            del sys.modules[module_name]

    # We clear the master 'polib' icon manager to prevent ResourceWarning and leaks.
    # If other addon uses the icon_manager, the previews will be reloaded on demand.
    polib.ui_bpy.icon_manager.clear()
