# copyright (c) 2018- polygoniq xyz s.r.o.

import typing
import bpy
import os
import enum
from . import polib

telemetry = polib.get_telemetry("memsaver")


MODULE_CLASSES: typing.List[typing.Type] = []
CONFLICTING_ADDONS = polib.utils_bpy.get_conflicting_addons(__package__)


class ImageSize(enum.Enum):
    SIZE_32 = "32"
    SIZE_64 = "64"
    SIZE_128 = "128"
    SIZE_256 = "256"
    SIZE_512 = "512"
    SIZE_1024 = "1024"
    SIZE_2048 = "2048"
    SIZE_4096 = "4096"
    SIZE_8192 = "8192"
    SIZE_16384 = "16384"
    CUSTOM = "CUSTOM"

    @staticmethod
    def to_blender_enum_list(
        include_custom: bool = False,
    ) -> typing.List[typing.Tuple[str, str, str]]:
        return [
            (size.value, size.value, size.value)
            for size in ImageSize
            if size.value.isdigit() or include_custom
        ]


class OperatorTarget(enum.Enum):
    SELECTED_OBJECTS = "SELECTED_OBJECTS"
    SCENE_OBJECTS = "SCENE_OBJECTS"
    ALL_OBJECTS = "ALL_OBJECTS"
    ALL_IMAGES_EXCEPT_HDR_EXR = "ALL_IMAGES_EXCEPT_HDR_EXR"
    ALL_HDR_EXR_IMAGES = "ALL_HDR_EXR_IMAGES"
    ALL_IMAGES = "ALL_IMAGES"


OPERATOR_TARGET_ITEM_MAP = {
    OperatorTarget.SELECTED_OBJECTS: (
        OperatorTarget.SELECTED_OBJECTS.value,
        "Selected Objects",
        "All selected objects",
    ),
    OperatorTarget.SCENE_OBJECTS: (
        OperatorTarget.SCENE_OBJECTS.value,
        "Scene Objects",
        "All objects in current scene",
    ),
    OperatorTarget.ALL_OBJECTS: (
        OperatorTarget.ALL_OBJECTS.value,
        "All Objects",
        "All objects in the .blend file",
    ),
    OperatorTarget.ALL_IMAGES_EXCEPT_HDR_EXR: (
        OperatorTarget.ALL_IMAGES_EXCEPT_HDR_EXR.value,
        "All Images except HDR and EXR",
        "All images except HDR and EXR, even those not used in any objects",
    ),
    OperatorTarget.ALL_HDR_EXR_IMAGES: (
        OperatorTarget.ALL_HDR_EXR_IMAGES.value,
        "All HDR and EXR Images",
        "All HDR and EXR images, even those not used in any objects",
    ),
    OperatorTarget.ALL_IMAGES: (
        OperatorTarget.ALL_IMAGES.value,
        "All Images",
        "All images, even those not used in any objects",
    ),
}


class MemoryEstimateOutputType(enum.Enum):
    HTML = "HTML"
    JSON = "JSON"


@polib.log_helpers_bpy.logged_operator
class PackLogs(bpy.types.Operator):
    bl_idname = "memsaver.pack_logs"
    bl_label = "Pack Logs"
    bl_description = "Archives polygoniq logs as zip file and opens its location"
    bl_options = {'REGISTER'}

    def execute(self, context):
        packed_logs_directory_path = polib.log_helpers_bpy.pack_logs(telemetry)
        polib.utils_bpy.xdg_open_file(packed_logs_directory_path)
        return {'FINISHED'}


MODULE_CLASSES.append(PackLogs)


@polib.log_helpers_bpy.logged_operator
class OpenCacheFolder(bpy.types.Operator):
    bl_idname = "memsaver.open_cache_folder"
    bl_label = "Open Cache Folder"
    bl_description = "Opens the directory with cached derivative images"
    bl_options = {'REGISTER'}

    def execute(self, context):
        prefs = get_preferences(context)
        polib.utils_bpy.xdg_open_file(prefs.get_cache_path())
        return {'FINISHED'}


MODULE_CLASSES.append(OpenCacheFolder)


@polib.log_helpers_bpy.logged_preferences
class Preferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    cache_path: bpy.props.StringProperty(
        name="Cache Path",
        default=os.path.expanduser("~/memsaver_cache"),
        description="Where derivatives (of various sizes) of images will be cached.",
        subtype='DIR_PATH',
        update=lambda self, context: polib.utils_bpy.absolutize_preferences_path(
            self, context, "cache_path"
        ),
    )

    # Used to choose target of image sizer operator
    image_resize_target: bpy.props.EnumProperty(
        name="Target",
        description="Choose to what objects/images the operator should apply to",
        items=[
            OPERATOR_TARGET_ITEM_MAP[OperatorTarget.SELECTED_OBJECTS],
            OPERATOR_TARGET_ITEM_MAP[OperatorTarget.SCENE_OBJECTS],
            OPERATOR_TARGET_ITEM_MAP[OperatorTarget.ALL_OBJECTS],
            (None),
            OPERATOR_TARGET_ITEM_MAP[OperatorTarget.ALL_IMAGES_EXCEPT_HDR_EXR],
            OPERATOR_TARGET_ITEM_MAP[OperatorTarget.ALL_HDR_EXR_IMAGES],
            OPERATOR_TARGET_ITEM_MAP[OperatorTarget.ALL_IMAGES],
        ],
        default=OperatorTarget.SCENE_OBJECTS.value,
    )

    decimate_meshes_target: bpy.props.EnumProperty(
        name="Target",
        description="Choose which mesh objects the operator should apply to",
        items=[
            OPERATOR_TARGET_ITEM_MAP[OperatorTarget.SELECTED_OBJECTS],
            OPERATOR_TARGET_ITEM_MAP[OperatorTarget.SCENE_OBJECTS],
            OPERATOR_TARGET_ITEM_MAP[OperatorTarget.ALL_OBJECTS],
        ],
        default=OperatorTarget.SCENE_OBJECTS.value,
    )

    # Used to choose target of adaptive image optimize
    # Adaptive optimize only works on images used on objects
    adaptive_image_target: bpy.props.EnumProperty(
        name="Target",
        description="Choose to what objects/images the operator should apply to",
        items=[
            OPERATOR_TARGET_ITEM_MAP[OperatorTarget.SELECTED_OBJECTS],
            OPERATOR_TARGET_ITEM_MAP[OperatorTarget.SCENE_OBJECTS],
        ],
        default=OperatorTarget.SCENE_OBJECTS.value,
    )

    adaptive_mesh_target: bpy.props.EnumProperty(
        name="Target",
        description="Choose which mesh objects the operator should apply to",
        items=[
            OPERATOR_TARGET_ITEM_MAP[OperatorTarget.SELECTED_OBJECTS],
            OPERATOR_TARGET_ITEM_MAP[OperatorTarget.SCENE_OBJECTS],
        ],
        default=OperatorTarget.SCENE_OBJECTS.value,
    )

    memory_estimation_output_type: bpy.props.EnumProperty(
        name="Output Type",
        items=[
            (
                MemoryEstimateOutputType.HTML.value,
                MemoryEstimateOutputType.HTML.value,
                f"{MemoryEstimateOutputType.HTML.value} report",
            ),
            (
                MemoryEstimateOutputType.JSON.value,
                MemoryEstimateOutputType.JSON.value,
                f"{MemoryEstimateOutputType.JSON.value} report",
            ),
        ],
        default=MemoryEstimateOutputType.HTML.value,
    )

    memory_estimation_output_directory: bpy.props.StringProperty(
        name="Memory Estimation Output Directory",
        default=os.path.expanduser(os.path.join("~", "memsaver_memory_estimation_reports")),
        description="Directory where the memory estimation report will be saved",
        subtype='DIR_PATH',
        update=lambda self, context: polib.utils_bpy.absolutize_preferences_path(
            self, context, "memory_estimation_output_directory"
        ),
    )

    adaptive_image_enabled: bpy.props.BoolProperty(
        name="Optimize Images",
        default=True,
    )

    adaptive_image_quality_factor: bpy.props.FloatProperty(
        name="Quality Factor",
        description="Object 2D bounds are multiplied by this to figure out image side size. \n\n"
        "Texture sizes are calculated based on how many pixels the objects that use them take "
        "either horizontally or vertically in the camera view. For example if an object is bigger "
        "vertically and it takes 10% of a FHD resolution then it takes 108 px and so its textures "
        "(if not used anywhere else) have to be at least 256px if the quality factor is set to "
        "2.00. Please note that if a big texture is mapped onto an object in a way that only "
        "a fraction of it is actually used, the downscaling might have a detrimental effect since "
        "even though the object is let's say 970 px wide it uses only a small part of the entire "
        "texture which then gets downscaled based on the bounds and not based on actual mapping "
        "density",
        default=1.0,
        min=0.001,
    )

    adaptive_image_minimum_size: bpy.props.EnumProperty(
        name="Minimum Image Size",
        description="Minimal image size, the algorithm will not choose a smaller size than this",
        items=ImageSize.to_blender_enum_list(),
        default=ImageSize.SIZE_256.value,
    )

    adaptive_image_maximum_size: bpy.props.EnumProperty(
        name="Maximum Image Size",
        description="Maximal image size, the algorithm will not choose a larger size than this",
        items=ImageSize.to_blender_enum_list(),
        default=ImageSize.SIZE_4096.value,  # 4k
    )

    adaptive_mesh_enabled: bpy.props.BoolProperty(
        name="Decimate Meshes",
        default=False,
    )

    adaptive_mesh_full_quality_distance: bpy.props.FloatProperty(
        name="Full Quality Max Distance",
        description="We won't apply any decimation on meshes closer to the camera than this value",
        default=20.0,
        min=0.0,
    )

    adaptive_mesh_lowest_quality_distance: bpy.props.FloatProperty(
        name="Lowest Quality Distance",
        description="Distance at which we will apply the lowest quality decimation",
        default=200.0,
        min=0.0,
    )

    adaptive_mesh_lowest_quality_decimation_ratio: bpy.props.FloatProperty(
        name="Lowest Quality Decimation Ratio",
        description="Which decimation ratio do we apply at the lowest quality distance",
        default=0.2,
        min=0.0,
        max=1.0,
    )

    adaptive_mesh_lowest_face_count: bpy.props.IntProperty(
        name="Lowest Face Count",
        description="Ignore meshes with face count lower than this value",
        default=5000,
        min=0,
    )

    adaptive_animation_mode: bpy.props.BoolProperty(
        name="Animation Mode",
        description="Instead of figuring out distances from current frame, consider all frames",
        default=False,
    )

    overlay_text_size_px: bpy.props.FloatProperty(
        name="Overlay Text Size",
        description="Size of the overlay text in pixels",
        default=16.0,
        min=1.0,
    )

    overlay_text_color: bpy.props.FloatVectorProperty(
        name="Overlay Text Color",
        description="Color of the text overlay. "
        "Useful when the default value would blend with background",
        min=0.0,
        max=1.0,
        default=(1.0, 1.0, 1.0, 1.0),
        size=4,
        subtype='COLOR',
    )

    change_size_desired_size: bpy.props.EnumProperty(
        name="Desired Size",
        description="Desired Maximum Side Size of Textures",
        items=ImageSize.to_blender_enum_list(include_custom=True),
        default=ImageSize.SIZE_2048.value,
    )

    change_size_custom_size: bpy.props.IntProperty(
        name="Custom Size",
        description="Desired Maximum Side Size of Textures",
        default=3072,
    )

    decimate_meshes_ratio: bpy.props.FloatProperty(
        name="Decimation Ratio",
        description="Decimation ratio for meshes",
        default=0.5,
        min=0.0,
        max=1.0,
    )

    def get_cache_path(self) -> str:
        if not os.path.isdir(self.cache_path):
            os.makedirs(self.cache_path)
        return self.cache_path

    def draw(self, context: bpy.types.Context):
        polib.ui_bpy.draw_conflicting_addons(self.layout, __package__, CONFLICTING_ADDONS)
        row = self.layout.row()
        row.prop(self, "cache_path")
        row = self.layout.row()
        row.operator(OpenCacheFolder.bl_idname, icon='FILE_CACHE')

        row = self.layout.row()
        row.operator(PackLogs.bl_idname, icon='EXPERIMENTAL')

        polib.ui_bpy.draw_settings_footer(self.layout)


MODULE_CLASSES.append(Preferences)


def get_preferences(context: bpy.types.Context) -> Preferences:
    return context.preferences.addons[__package__].preferences


def register():
    for cls in MODULE_CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(MODULE_CLASSES):
        bpy.utils.unregister_class(cls)
