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

import os
import sys
import collections
import typing
import bpy
import tempfile
import logging
import logging.handlers
import importlib

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

    from . import preferences
    from . import utils
    from . import optimized_output_aggregator
    from . import image_sizer
    from . import object_render_estimator
    from . import memory_usage
    from . import mesh_decimation
    from . import derivative_generator

    if typing.TYPE_CHECKING:
        import polib
        import hatchery

finally:
    if ADDITIONAL_DEPS_DIR in sys.path:
        sys.path.remove(ADDITIONAL_DEPS_DIR)

bl_info = {
    "name": "memsaver_personal",
    "author": "polygoniq xyz s.r.o.",
    "version": (1, 3, 0),  # bump doc_url as well!
    "blender": (3, 6, 0),
    "location": "memsaver panel in the polygoniq tab in the sidebar of the 3D View window",
    "description": "",
    "category": "System",
    "doc_url": "https://docs.polygoniq.com/memsaver/1.3.0/",
    "tracker_url": "https://polygoniq.com/discord/",
}
telemetry = polib.get_telemetry("memsaver")
telemetry.report_addon(bl_info, __file__)


ADDON_CLASSES: typing.List[typing.Type] = []


class ImageSizerOperatorBase(bpy.types.Operator):
    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context: bpy.types.Context) -> None:
        prefs = preferences.get_preferences(context)
        self.layout.prop(prefs, "image_resize_target")


@polib.log_helpers_bpy.logged_operator
class ChangeImageSize(ImageSizerOperatorBase):
    bl_idname = "memsaver.change_image_size"
    bl_label = "Change Image Size"
    bl_description = (
        "Change images of given objects, generate lower resolution images on demand if necessary. "
        "Packed images are not supported."
    )
    bl_options = {'REGISTER', 'UNDO'}

    def draw(self, context: bpy.types.Context):
        super().draw(context)

        prefs = preferences.get_preferences(context)
        self.layout.prop(prefs, "change_size_desired_size")
        if prefs.change_size_desired_size == preferences.ImageSize.CUSTOM.value:
            self.layout.prop(prefs, "change_size_custom_size")

    @polib.utils_bpy.blender_cursor('WAIT')
    def execute(self, context: bpy.types.Context):
        prefs = preferences.get_preferences(context)
        cache_path = prefs.get_cache_path()

        images = image_sizer.get_target_images(context)
        logger.info(f"Working with target images: {images}")
        logger.info(f"desired_size={prefs.change_size_desired_size}")
        logger.info(f"custom_size={prefs.change_size_custom_size}")

        desired_size = (
            prefs.change_size_custom_size
            if prefs.change_size_desired_size == preferences.ImageSize.CUSTOM.value
            else int(prefs.change_size_desired_size)
        )
        aggregator = image_sizer.ResizeImageOutputAggregator()
        image_sizer.change_image_sizes(
            cache_path,
            {image: desired_size for image in images},
            aggregator,
            progress_wm=context.window_manager,
        )

        if bpy.context.scene.render.engine == 'octane':
            image_sizer.octane_reload_images()

        for message in aggregator.get_error_messages():
            self.report(
                {'WARNING'},
                message,
            )
        for changed_to_original in filter(
            lambda x: x.result
            in {
                image_sizer.ImageResizeResult.CHANGED_TO_ORIGINAL,
                image_sizer.ImageResizeResult.KEEP_ORIGINAL,
            },
            aggregator._outputs,
        ):
            self.report(
                {'INFO'},
                aggregator.get_output_result_message(changed_to_original),
            )
        self.report(
            {'INFO'},
            aggregator.get_summary_message(),
        )
        return {'FINISHED'}


ADDON_CLASSES.append(ChangeImageSize)


@polib.log_helpers_bpy.logged_operator
class RevertImagesToOriginals(ImageSizerOperatorBase):
    bl_idname = "memsaver.revert_images_to_originals"
    bl_label = "Revert Images to Originals"
    bl_description = (
        "Change given images back to their originals. This does not delete lower "
        "resolution images that may have been generated previously"
    )
    bl_options = {'REGISTER', 'UNDO'}

    @polib.utils_bpy.blender_cursor('WAIT')
    def execute(self, context: bpy.types.Context):
        images = image_sizer.get_target_images(context)
        logger.info(f"Working with target images: {images}")

        aggregator = image_sizer.RevertImagesToOriginalOutputAggregator()
        for image in images:
            try:
                image_sizer.revert_to_original(image, aggregator)
            except Exception as e:
                aggregator.add_output(
                    optimized_output_aggregator.OptimizedDatablockInfo(
                        image.name, optimized_output_aggregator.RevertOperationResult.FAILED
                    )
                )
                logger.exception(
                    f"Uncaught exception while reverting image {image.name} to original"
                )
                self.report(
                    {'WARNING'},
                    f"Errors encountered when reverting image {image.name} to original, skipping...",
                )
        if bpy.context.scene.render.engine == 'octane':
            image_sizer.octane_reload_images()

        self.report({'INFO'}, aggregator.get_summary_message())
        return {'FINISHED'}


ADDON_CLASSES.append(RevertImagesToOriginals)


@polib.log_helpers_bpy.logged_operator
class CheckDerivatives(ImageSizerOperatorBase):
    bl_idname = "memsaver.check_derivatives"
    bl_label = "Check & Regenerate Images"
    bl_description = (
        "Check that given images all have valid paths, if the path is invalid and "
        "it is a lower resolution derivative we re-generate it"
    )
    bl_options = {'REGISTER'}

    @polib.utils_bpy.blender_cursor('WAIT')
    def execute(self, context: bpy.types.Context):
        prefs = preferences.get_preferences(context)
        cache_path = prefs.get_cache_path()
        logger.debug(f"Cache path: {cache_path}")
        images = image_sizer.get_target_images(context)
        logger.info(f"Working with target images: {images}")

        output_aggregator = image_sizer.CheckDerivativeOutputAggregator()

        for image in images:
            try:
                # Unlike in the post_load handler, here we insist on the currently set cache_path
                image_sizer.check_derivative(cache_path, image, output_aggregator)
            except Exception as e:
                logger.exception(f"Uncaught exception while checking image {image.name}")
                self.report(
                    {'WARNING'}, f"Errors encountered when checking image {image.name}, skipping..."
                )

        self.report({'INFO'}, output_aggregator.get_summary_message())
        return {'FINISHED'}


ADDON_CLASSES.append(CheckDerivatives)


class MeshDecimationOperatorBase(bpy.types.Operator):
    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context: bpy.types.Context) -> None:
        prefs = preferences.get_preferences(context)
        self.layout.prop(prefs, "decimate_meshes_target")


@polib.log_helpers_bpy.logged_operator
class DecimateMeshes(MeshDecimationOperatorBase):
    bl_idname = "memsaver.decimate_meshes"
    bl_label = "Decimate Meshes"
    bl_description = "Decimate meshes of given objects based on the given ratio"
    bl_options = {'REGISTER', 'UNDO'}

    def draw(self, context: bpy.types.Context):
        super().draw(context)

        prefs = preferences.get_preferences(context)
        self.layout.prop(prefs, "decimate_meshes_ratio")

    @polib.utils_bpy.blender_cursor('WAIT')
    def execute(self, context: bpy.types.Context):
        prefs = preferences.get_preferences(context)
        objects = mesh_decimation.get_target_objects(context)
        logger.info(f"Working with target meshes: {objects}")
        logger.info(f"Decimation ratio={prefs.decimate_meshes_ratio}")
        aggregator = mesh_decimation.DecimateMeshObjectOutputAggregator()
        mesh_decimation.set_decimation_ratios(
            {obj: prefs.decimate_meshes_ratio for obj in objects if obj.type == 'MESH'},
            aggregator,
        )
        for message in aggregator.get_error_messages():
            self.report(
                {'WARNING'},
                message,
            )
        self.report(
            {'INFO'},
            aggregator.get_summary_message(),
        )

        return {'FINISHED'}


ADDON_CLASSES.append(DecimateMeshes)


@polib.log_helpers_bpy.logged_operator
class RevertMeshesToOriginals(MeshDecimationOperatorBase):
    bl_idname = "memsaver.revert_meshes_to_originals"
    bl_label = "Revert Meshes to Originals"
    bl_description = "Removes any memsaver decimate modifiers if present"
    bl_options = {'REGISTER', 'UNDO'}

    @polib.utils_bpy.blender_cursor('WAIT')
    def execute(self, context: bpy.types.Context):
        objects = mesh_decimation.get_target_objects(context)
        logger.info(f"Working with target objects: {objects}")

        aggregator = mesh_decimation.RevertMeshToOriginalOutputAggregator()
        for obj in objects:
            mesh_decimation.revert_to_original(obj, aggregator)

        self.report({'INFO'}, aggregator.get_summary_message())
        return {'FINISHED'}


ADDON_CLASSES.append(RevertMeshesToOriginals)


class AdaptiveOptimizeBase(bpy.types.Operator):
    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context: bpy.types.Context):
        prefs = preferences.get_preferences(context)

        row = self.layout.row()
        row.alert = context.scene.camera is None
        row.label(text=f"Active Camera{' is required!' if row.alert else ''}")
        row.prop_search(context.scene, "camera", context.scene, "objects", text="")

        self.layout.prop(prefs, "adaptive_image_enabled")
        if prefs.adaptive_image_enabled:
            box = self.layout.box()
            self._draw_image_props(box, prefs)
        self.layout.separator()
        self.layout.prop(prefs, "adaptive_mesh_enabled")
        if prefs.adaptive_mesh_enabled:
            box = self.layout.box()
            self._draw_mesh_props(box, prefs)
        self.layout.separator()
        self.layout.prop(prefs, "adaptive_animation_mode")

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return context.scene is not None

    def _draw_image_props(self, box: bpy.types.UILayout, prefs: preferences.Preferences):
        box.prop(prefs, "adaptive_image_quality_factor")
        SPLIT_FACTOR = 0.5
        split = box.split(factor=SPLIT_FACTOR)
        split.label(text="Minimum Image Size")
        split.prop(prefs, "adaptive_image_minimum_size", text="")
        split = box.split(factor=SPLIT_FACTOR)
        split.label(text="Maximum Image Size")
        split.prop(prefs, "adaptive_image_maximum_size", text="")

    def _draw_mesh_props(self, box: bpy.types.UILayout, prefs: preferences.Preferences):
        box.prop(prefs, "adaptive_mesh_full_quality_distance")
        box.prop(prefs, "adaptive_mesh_lowest_quality_distance")
        box.prop(prefs, "adaptive_mesh_lowest_quality_decimation_ratio", slider=True)
        box.prop(prefs, "adaptive_mesh_lowest_face_count")


@polib.log_helpers_bpy.logged_operator
class AdaptiveOptimize(AdaptiveOptimizeBase):
    bl_idname = "memsaver.adaptive_optimize"
    bl_label = "Adaptive Optimize"
    bl_description = (
        "Adaptively change image size of given objects based on how large the "
        "objects appear in the render based on active camera, generate lower resolution images "
        "if necessary. Packed images are not supported. "
        "Adaptively decimate far away meshes based on the distance from camera"
    )
    bl_options = {'REGISTER', 'UNDO'}

    @polib.utils_bpy.blender_cursor('WAIT')
    def execute(self, context: bpy.types.Context):
        if context.scene.camera is None:
            self.report(
                {'ERROR'},
                f"{AdaptiveOptimize.__name__} requires an active camera!",
            )
            return {'CANCELLED'}

        prefs = preferences.get_preferences(context)

        logger.info(f"image_enabled={prefs.adaptive_image_enabled}")
        objs_for_image_resize = list(image_sizer.get_adaptive_optimize_target_objects(context))
        logger.info(f"Image resize working with target objects: {objs_for_image_resize}")
        if prefs.adaptive_image_enabled:
            adaptive_image_minimum_size = int(prefs.adaptive_image_minimum_size)
            adaptive_image_maximum_size = int(prefs.adaptive_image_maximum_size)
            if adaptive_image_minimum_size > adaptive_image_maximum_size:
                error_msg = (
                    f"Selected Minimal image size '{adaptive_image_minimum_size}' is "
                    f"bigger than Maximal size '{adaptive_image_maximum_size}'!"
                )
                logger.error(f"{error_msg} Aborting..")
                self.report({'ERROR'}, f"{error_msg} Please select valid values.")
                return {'CANCELLED'}

            logger.info(f"image_quality_factor={prefs.adaptive_image_quality_factor}")
            logger.info(f"image_minimum_size={adaptive_image_minimum_size}")
            logger.info(f"image_maximum_size={adaptive_image_maximum_size}")

        logger.info(f"mesh_enabled={prefs.adaptive_mesh_enabled}")
        objs_to_decimate = list(mesh_decimation.get_adaptive_optimize_target_objects(context))
        logger.info(f"Mesh decimation working with target objects: {objs_to_decimate}")
        if prefs.adaptive_mesh_enabled:
            if (
                prefs.adaptive_mesh_full_quality_distance
                > prefs.adaptive_mesh_lowest_quality_distance
            ):
                error_msg = (
                    f"Selected Full quality distance "
                    f"'{prefs.adaptive_mesh_full_quality_distance}' is bigger than Lowest "
                    f"quality distance '{prefs.adaptive_mesh_lowest_quality_distance}'!"
                )
                logger.error(f"{error_msg} Aborting..")
                self.report({'ERROR'}, f"{error_msg} Please select valid values.")
                return {'CANCELLED'}

            logger.info(f"mesh_minimum_distance={prefs.adaptive_mesh_full_quality_distance}")
            logger.info(
                f"mesh_lowest_quality_distance={prefs.adaptive_mesh_lowest_quality_distance}"
            )
            logger.info(
                f"mesh_lowest_quality_decimation_ratio="
                f"{prefs.adaptive_mesh_lowest_quality_decimation_ratio}"
            )

        logger.info(f"animation_mode={prefs.adaptive_animation_mode}")

        report_message = ""
        if prefs.adaptive_image_enabled:
            size_map_generator = object_render_estimator.get_size_map_for_objects_current_frame
            if prefs.adaptive_animation_mode:
                size_map_generator = object_render_estimator.get_size_map_for_objects_animation_mode
            image_size_map = size_map_generator(
                context.scene,
                context.scene.camera,
                objs_for_image_resize,
                prefs.adaptive_image_quality_factor,
                adaptive_image_minimum_size,
                adaptive_image_maximum_size,
                True,
            )
            cache_path = prefs.get_cache_path()
            image_aggregator = image_sizer.ResizeImageOutputAggregator()
            image_sizer.change_image_sizes(
                cache_path,
                image_size_map,
                image_aggregator,
                progress_wm=context.window_manager,
            )

            if bpy.context.scene.render.engine == 'octane':
                image_sizer.octane_reload_images()

            for message in image_aggregator.get_error_messages():
                self.report(
                    {'WARNING'},
                    message,
                )

            report_message += image_aggregator.get_summary_message()

        if prefs.adaptive_mesh_enabled:
            objects_decimation_ratio_map_generator = (
                mesh_decimation.get_objects_decimation_ratio_map_current_frame
            )
            if prefs.adaptive_animation_mode:
                objects_decimation_ratio_map_generator = (
                    mesh_decimation.get_objects_decimation_ratio_map_animation_mode
                )

            object_to_decimation_ratio_map = objects_decimation_ratio_map_generator(
                context.scene,
                context.scene.camera,
                filter(lambda obj: obj.type == 'MESH', objs_to_decimate),
                prefs.adaptive_mesh_full_quality_distance,
                prefs.adaptive_mesh_lowest_quality_distance,
                prefs.adaptive_mesh_lowest_quality_decimation_ratio,
                prefs.adaptive_mesh_lowest_face_count,
            )
            mesh_object_aggregator = mesh_decimation.DecimateMeshObjectOutputAggregator()
            mesh_decimation.set_decimation_ratios(
                object_to_decimation_ratio_map, mesh_object_aggregator
            )
            for message in mesh_object_aggregator.get_error_messages():
                self.report(
                    {'WARNING'},
                    message,
                )
            report_message += mesh_object_aggregator.get_summary_message()

        self.report({'INFO'}, report_message)

        return {'FINISHED'}

    def _draw_image_props(self, box: bpy.types.UILayout, prefs: preferences.Preferences):
        box.prop(prefs, "adaptive_image_target")
        super()._draw_image_props(box, prefs)

    def _draw_mesh_props(self, box: bpy.types.UILayout, prefs: preferences.Preferences):
        box.prop(prefs, "adaptive_mesh_target")
        super()._draw_mesh_props(box, prefs)


ADDON_CLASSES.append(AdaptiveOptimize)


@polib.log_helpers_bpy.logged_operator
class PreviewAdaptiveOptimize(AdaptiveOptimizeBase):
    bl_idname = "memsaver.preview_adaptive_optimize"
    bl_label = "Preview Adaptive Optimize"
    bl_description = (
        "Starts a preview mode to observe what image sizes and which mesh "
        "decimations will be generated when using Adaptive Optimize operator"
    )
    bl_options = {'REGISTER'}

    bgl_2d_handler_ref = None
    is_running: bool = False
    obj_image_info_map: typing.DefaultDict[
        bpy.types.Object,
        typing.List[typing.Tuple[bpy.types.Image, float, float, float, typing.Optional[str]]],
    ] = collections.defaultdict(list)
    obj_decimation_ratio_map: typing.DefaultDict[bpy.types.Object, float] = collections.defaultdict(
        lambda: 1.0
    )

    def draw(self, context: bpy.types.Context) -> None:
        self.layout.label(text="Preview sizes will be generated based on those settings")
        super().draw(context)

    def draw_px(self):
        prefs = preferences.get_preferences(bpy.context)
        ui_scale = bpy.context.preferences.system.ui_scale
        font_size = prefs.overlay_text_size_px * ui_scale
        region = bpy.context.region
        rv3d = bpy.context.space_data.region_3d
        text_style = polib.render_bpy.TextStyle(font_size=font_size, color=prefs.overlay_text_color)
        half_width = bpy.context.region.width / 2.0

        polib.render_bpy.mouse_info(
            half_width - 70 * ui_scale,
            20,
            "Select object",
            left_click=True,
        )

        polib.render_bpy.key_info(half_width + 70 * ui_scale, 20, "ESC", "Exit")

        for obj in bpy.context.selected_objects:
            texts = []
            if prefs.adaptive_image_enabled:
                images = PreviewAdaptiveOptimize.obj_image_info_map.get(obj, None)
                if images is None:
                    continue
                texts.extend([(self._format_image_size(*i), text_style) for i in images])

            if prefs.adaptive_mesh_enabled and obj.type == 'MESH':
                decimation_ratio = PreviewAdaptiveOptimize.obj_decimation_ratio_map.get(obj, 1.0)
                texts.append((self._format_mesh_decimation(decimation_ratio), text_style))

            if len(texts) > 0:
                polib.render_bpy.text_box_3d(
                    obj.matrix_world.translation, 10, 10, None, texts, region, rv3d
                )

    def modal(self, context: bpy.types.Context, event: bpy.types.Event):
        polib.ui_bpy.tag_areas_redraw(context, {'VIEW_3D'})

        if event.value == 'PRESS' and event.type == 'ESC':
            self.cancel(context)
            return {'FINISHED'}

        return {'PASS_THROUGH'}

    @staticmethod
    def remove_draw_handlers() -> None:
        if (
            hasattr(PreviewAdaptiveOptimize, "bgl_2d_handler_ref")
            and PreviewAdaptiveOptimize.bgl_2d_handler_ref is not None
        ):
            bpy.types.SpaceView3D.draw_handler_remove(
                PreviewAdaptiveOptimize.bgl_2d_handler_ref, 'WINDOW'
            )
            PreviewAdaptiveOptimize.bgl_2d_handler_ref = None

    def cancel(self, context: bpy.types.Context):
        PreviewAdaptiveOptimize.remove_draw_handlers()
        PreviewAdaptiveOptimize.is_running = False

    def __del__(self):
        PreviewAdaptiveOptimize.remove_draw_handlers()

    @polib.utils_bpy.blender_cursor('WAIT')
    def execute(self, context: bpy.types.Context):
        if context.scene.camera is None:
            self.report(
                {'ERROR'},
                f"{PreviewAdaptiveOptimize.__name__} requires an active camera!",
            )
            return {'CANCELLED'}

        cls = type(self)
        cls.obj_image_info_map.clear()
        cls.obj_decimation_ratio_map.clear()

        prefs = preferences.get_preferences(context)
        if prefs.adaptive_image_enabled:
            adaptive_image_minimum_size = int(prefs.adaptive_image_minimum_size)
            adaptive_image_maximum_size = int(prefs.adaptive_image_maximum_size)
            if adaptive_image_minimum_size > adaptive_image_maximum_size:
                error_msg = (
                    f"Selected Minimal image size '{adaptive_image_minimum_size}' is "
                    f"bigger than Maximal size '{adaptive_image_maximum_size}'!"
                )
                logger.error(error_msg)
                self.report({'ERROR'}, f"{error_msg} Please select valid values.")
                return {'CANCELLED'}

            # Pre-compute the maps from all objects in the .blend file, then in draw_px display
            # only information about selected objects
            size_map_generator = object_render_estimator.get_size_map_for_objects_current_frame
            if prefs.adaptive_animation_mode:
                size_map_generator = object_render_estimator.get_size_map_for_objects_animation_mode
            image_size_map = size_map_generator(
                context.scene,
                context.scene.camera,
                context.scene.objects,
                prefs.adaptive_image_quality_factor,
                adaptive_image_minimum_size,
                adaptive_image_maximum_size,
                True,
            )

            for obj in context.scene.objects:
                images = utils.get_images_used_in_object(obj)
                for img in images:
                    orig_size = max(img.size[0], img.size[1])
                    assert orig_size >= 0, "negative original size!"
                    if orig_size == 0:
                        logger.warning(f"{img.name} has original size equal to 0!")
                    new_size = image_size_map.get(img, 1)
                    if img.packed_file is not None:
                        cls.obj_image_info_map[obj].append(
                            (
                                img,
                                orig_size,
                                orig_size,
                                1,
                                "Image is PACKED, resizing is not possible!",
                            )
                        )
                    else:
                        cls.obj_image_info_map[obj].append(
                            (img, orig_size, new_size, new_size / max(1, orig_size), None)
                        )

                cls.obj_image_info_map[obj].sort(key=lambda x: x[3], reverse=True)

        if prefs.adaptive_mesh_enabled:
            if (
                prefs.adaptive_mesh_full_quality_distance
                > prefs.adaptive_mesh_lowest_quality_distance
            ):
                error_msg = (
                    f"Selected Full quality distance "
                    f"'{prefs.adaptive_mesh_full_quality_distance}' is bigger than Lowest "
                    f"quality distance '{prefs.adaptive_mesh_lowest_quality_distance}'!"
                )
                logger.error(f"{error_msg} Aborting..")
                self.report({'ERROR'}, f"{error_msg} Please select valid values.")
                return {'CANCELLED'}

            objects_decimation_ratio_map_generator = (
                mesh_decimation.get_objects_decimation_ratio_map_current_frame
            )
            if prefs.adaptive_animation_mode:
                objects_decimation_ratio_map_generator = (
                    mesh_decimation.get_objects_decimation_ratio_map_animation_mode
                )

            cls.obj_decimation_ratio_map = objects_decimation_ratio_map_generator(
                context.scene,
                context.scene.camera,
                context.scene.objects,
                prefs.adaptive_mesh_full_quality_distance,
                prefs.adaptive_mesh_lowest_quality_distance,
                prefs.adaptive_mesh_lowest_quality_decimation_ratio,
                prefs.adaptive_mesh_lowest_face_count,
            )

        assert cls.bgl_2d_handler_ref is None, "Draw handler already registered!"
        PreviewAdaptiveOptimize.bgl_2d_handler_ref = bpy.types.SpaceView3D.draw_handler_add(
            self.draw_px, (), 'WINDOW', 'POST_PIXEL'
        )

        cls.is_running = True
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        # If the operator is already running, don't do anything
        if PreviewAdaptiveOptimize.is_running:
            return {'PASS_THROUGH'}

        return context.window_manager.invoke_props_dialog(self)

    def _format_image_size(
        self,
        img: bpy.types.Image,
        orig_size: int,
        new_size: int,
        ratio: float,
        additional_info: typing.Optional[str],
    ) -> str:
        formatted_msg = f"{img.name}, {orig_size}px -> {new_size}px, {ratio * 100.0:.0f}%"
        if additional_info is not None:
            formatted_msg += f", {additional_info}"
        return formatted_msg

    def _format_mesh_decimation(self, decimation_ratio: float) -> str:
        if decimation_ratio == 1.0:
            return "Mesh, No decimation"
        else:
            return f"Mesh, {(1.0 - decimation_ratio)*100:.0f}% decimation"


ADDON_CLASSES.append(PreviewAdaptiveOptimize)


@polib.log_helpers_bpy.logged_panel
class MemSaverPanel(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_memsaver"
    bl_label = str(bl_info.get("name", "memsaver")).replace("_", " ")
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "polygoniq"
    bl_order = 30
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context: bpy.types.Context):
        try:
            self.layout.label(
                text="",
                icon_value=polib.ui_bpy.icon_manager.get_polygoniq_addon_icon_id("memsaver"),
            )
        except KeyError:
            pass

    def draw_header_preset(self, context: bpy.types.Context) -> None:
        master_row = self.layout.row(align=True)
        master_row.row().operator(
            preferences.OpenCacheFolder.bl_idname, icon='FILEBROWSER', text=""
        )
        master_row.row().operator("preferences.addon_show", icon='SETTINGS').module = __package__
        polib.ui_bpy.draw_doc_button(master_row.row(), __package__)

    def draw_preview_mode(self, context: bpy.types.Context):
        layout = self.layout
        col = layout.column(align=True)
        col.label(text="Select object to preview", icon='RESTRICT_SELECT_OFF')

        prefs = preferences.get_preferences(context)
        col.prop(prefs, "overlay_text_size_px")
        col.prop(prefs, "overlay_text_color", text="")
        col.separator()
        row = col.row()
        row.alert = True
        row.label(text="Press ESC to exit", icon='PANEL_CLOSE')

    def draw(self, context: bpy.types.Context):
        polib.ui_bpy.draw_conflicting_addons(
            self.layout, __package__, preferences.CONFLICTING_ADDONS
        )
        layout = self.layout
        if PreviewAdaptiveOptimize.is_running:
            self.draw_preview_mode(context)
            return

        any_generator_available = derivative_generator.is_generator_available()
        col = layout.column(align=True)
        if not any_generator_available:
            col.alert = True
            col.label(text="Failed to install Python image")
            col.label(text="processing library! Try to close")
            col.label(text="Blender and run it once as")
            col.label(text="administrator in order for")
            col.label(text="memsaver to install the missing")
            col.label(text="library.")
            col.label(text="You can also use Blender 3.5")
            col.label(text="or newer since it contains")
            col.label(text="the library by default.")

        row = layout.row(align=True)
        row.scale_x = row.scale_y = 1.4
        row.operator(AdaptiveOptimize.bl_idname, text="Adaptive Optimize", icon='VIEW_PERSPECTIVE')
        row.operator(PreviewAdaptiveOptimize.bl_idname, text="", icon='VIEWZOOM')
        row.enabled = any_generator_available

        col = layout.column(align=True)
        row = col.row()
        row.operator(ChangeImageSize.bl_idname, text="Resize Images", icon='ARROW_LEFTRIGHT')
        row.enabled = any_generator_available
        col.operator(DecimateMeshes.bl_idname, text="Decimate Meshes", icon='MOD_DECIM')

        col = layout.column(align=True)
        col.operator(RevertImagesToOriginals.bl_idname, icon='LOOP_BACK')
        col.operator(RevertMeshesToOriginals.bl_idname, icon='LOOP_BACK')
        row = col.row(align=True)
        row.operator(CheckDerivatives.bl_idname)
        row.enabled = any_generator_available


ADDON_CLASSES.append(MemSaverPanel)


@polib.log_helpers_bpy.logged_panel
class MemoryEstimationPanel(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_memsaver_memory_estimation"
    bl_label = "Memory Estimation"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "polygoniq"
    bl_parent_id = MemSaverPanel.bl_idname

    def draw_header(self, context: bpy.types.Context):
        self.layout.label(text="", icon='MEMORY')

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        estimation_running = not memory_usage.EstimateMemoryUsageBase.poll(context)
        if estimation_running:
            row = layout.row()
            row.label(text=f"Estimation Running...")

            row = row.row()
            row.alert = True
            row.operator(memory_usage.CancelMemoryUsageEstimation.bl_idname, text="", icon='X')

        col = layout.column()
        col.enabled = not estimation_running
        prefs = preferences.get_preferences(context)
        col.operator(
            memory_usage.EstimateMemoryUsageCurrentFile.bl_idname,
            text="Estimate This File",
            icon='BLENDER',
        )
        col.operator(
            memory_usage.EstimateMemoryUsage.bl_idname,
            text="Estimate File/Folder",
            icon='FILEBROWSER',
        ).filename = ""

        col.separator()
        row = col.row()
        row.enabled = False
        row.label(text="Output Settings:")
        col.prop(prefs, "memory_estimation_output_directory", text="Directory")
        col.prop(prefs, "memory_estimation_output_type", text="Format")


ADDON_CLASSES.append(MemoryEstimationPanel)


@bpy.app.handlers.persistent
def memsaver_load_post(_) -> None:
    """Go through all bpy.data.images and check derivatives, regen if necessary

    Whenever a .blend is loaded we have to go through all images and check that their derivatives
    are present where they should be, if they are not we will regenerate. This can also be achieved
    manually with the "Check & Regenerate" button/operator from the panel.
    """

    logger.info(
        f"Checking all bpy.data.images' derivatives as part of a load_post handler "
        f"(bpy.data.filepath=\"{bpy.data.filepath}\")..."
    )
    for image in bpy.data.images:
        # We purposefully infer cache_path from the image.filepath to avoid regenerating everything
        # when preferences get corrupted or changed
        try:
            image_sizer.check_derivative(None, image)
        except:
            logger.exception(f"Uncaught exception while checking image {image.name}")


def register():
    preferences.register()
    memory_usage.register()

    for cls in ADDON_CLASSES:
        bpy.utils.register_class(cls)

    bpy.app.handlers.load_post.append(memsaver_load_post)


def unregister():
    bpy.app.handlers.load_post.remove(memsaver_load_post)

    for cls in reversed(ADDON_CLASSES):
        bpy.utils.unregister_class(cls)

    memory_usage.unregister()
    preferences.unregister()

    # Remove all nested modules from module cache, more reliable than importlib.reload(..)
    # Idea by BD3D / Jacques Lucke
    for module_name in list(sys.modules.keys()):
        if module_name.startswith(__package__):
            del sys.modules[module_name]

    # We clear the master 'polib' icon manager to prevent ResourceWarning and leaks.
    # If other addon uses the icon_manager, the previews will be reloaded on demand.
    polib.ui_bpy.icon_manager.clear()
