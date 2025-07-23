# copyright (c) 2018- polygoniq xyz s.r.o.

import typing
import bpy
import enum
import os
import glob
import hashlib
import functools
import dataclasses
import logging
from . import polib
from . import utils
from . import preferences
from . import derivative_generator
from . import memory_usage
from . import optimized_output_aggregator

logger = logging.getLogger(f"polygoniq.{__name__}")


ORIGINAL_PATH_PROPERTY_NAME = "memsaver_original_path"
# TODO: change value appropriately, test whether the change causes an issue
DERIVATIVE_FILENAME_PROPERTY_NAME = "memsaver_derivative_path"
DERIVATIVE_SIZE_PROPERTY_NAME = "memsaver_derivative_size"


UNRESIZABLE_IMAGE_NAMES = {"Render Result", "Viewer Node"}


def remove_memsaver_properties(image: bpy.types.Image) -> None:
    image[DERIVATIVE_FILENAME_PROPERTY_NAME] = None
    image[ORIGINAL_PATH_PROPERTY_NAME] = None
    image[DERIVATIVE_SIZE_PROPERTY_NAME] = 0


def get_target_images(context: bpy.types.Context) -> typing.Set[bpy.types.Image]:
    operator_target = preferences.get_preferences(context).image_resize_target

    if operator_target == preferences.OperatorTarget.SELECTED_OBJECTS.value:
        ret = (
            image
            for obj in context.selected_objects
            for image in utils.get_images_used_in_object(obj)
        )
    elif operator_target == preferences.OperatorTarget.SCENE_OBJECTS.value:
        ret = (
            image for obj in context.scene.objects for image in utils.get_images_used_in_object(obj)
        )
    elif operator_target == preferences.OperatorTarget.ALL_OBJECTS.value:
        ret = {image for obj in bpy.data.objects for image in utils.get_images_used_in_object(obj)}
    elif operator_target == preferences.OperatorTarget.ALL_IMAGES_EXCEPT_HDR_EXR.value:
        ret = (
            img for img in bpy.data.images if not img.filepath.lower().endswith((".hdr", ".exr"))
        )
    elif operator_target == preferences.OperatorTarget.ALL_HDR_EXR_IMAGES.value:
        ret = (img for img in bpy.data.images if img.filepath.lower().endswith((".hdr", ".exr")))
    elif operator_target == preferences.OperatorTarget.ALL_IMAGES.value:
        ret = bpy.data.images
    else:
        raise ValueError(f"Unknown selection target '{operator_target}'")

    # These two native images always fail to resize, so we skip them
    return set(filter(lambda img: img.name not in UNRESIZABLE_IMAGE_NAMES, ret))


def get_adaptive_optimize_target_objects(
    context: bpy.types.Context,
) -> typing.Iterable[bpy.types.Object]:
    operator_target = preferences.get_preferences(context).adaptive_image_target

    if operator_target == preferences.OperatorTarget.SELECTED_OBJECTS.value:
        return context.selected_objects
    elif operator_target == preferences.OperatorTarget.SCENE_OBJECTS.value:
        return context.scene.objects
    else:
        raise ValueError(f"Unknown selection target '{operator_target}'")


def was_filepath_overwritten_on_derivative(image: bpy.types.Image) -> bool:
    """Verifies whether an image derivative is pointing to a different file then memsaver expects.

    If the image derivative's filepath is pointing to a different image then expected,
    it was changed outside of memsaver. Such image can no longer be considered an image derivative.
    """
    # image is generated or packed, memsaver does not handle the filepath
    if image.filepath in {None, ""}:
        return False

    # the image is not an image derivative, memsaver does not handle the filepath
    if image.get(DERIVATIVE_FILENAME_PROPERTY_NAME, None) is None:
        return False

    return (
        image[DERIVATIVE_FILENAME_PROPERTY_NAME].lower()
        != bpy.path.basename(image.filepath).lower()
    )


def get_filepath_hash(abs_path: str) -> str:
    """Given an absolute file path, return a hash

    This hash is the base for image derivative paths.
    """
    # TODO: We generate the hash from absolute path, is that OK?
    assert os.path.isabs(abs_path)
    return hashlib.sha256(abs_path.encode("utf-8")).hexdigest()


def get_original_path(image: bpy.types.Image) -> typing.Optional[str]:
    # original path set by memsaver is incorrect if the derivative's filepath was changed
    # outside of memsaver, so there is no original path to get
    assert not was_filepath_overwritten_on_derivative(image)

    original_path = image.get(ORIGINAL_PATH_PROPERTY_NAME, None)
    if original_path is not None:
        assert isinstance(original_path, str)
        return typing.cast(str, original_path)
    return None


def ensure_original_path(image: bpy.types.Image) -> str:
    if was_filepath_overwritten_on_derivative(image):
        remove_memsaver_properties(image)
    original_path = get_original_path(image)
    if original_path in {None, ""}:
        # we don't absolutize the path, we will do that only just before we have to
        image[ORIGINAL_PATH_PROPERTY_NAME] = image.filepath
    else:
        return typing.cast(str, original_path)

    original_path = get_original_path(image)
    # it can be "" in case the image is generated or packed
    assert original_path is not None
    return typing.cast(str, original_path)


class RevertImagesToOriginalOutputAggregator(
    optimized_output_aggregator.RevertOperationResultAggregator
):
    def _get_operation_target(self, plural):
        return "images" if plural else "image"


def revert_to_original(
    image: bpy.types.Image,
    revert_aggregator: typing.Optional[RevertImagesToOriginalOutputAggregator] = None,
) -> None:
    """Reverts the image to the original path."""
    if was_filepath_overwritten_on_derivative(image):
        remove_memsaver_properties(image)
        logger.info(
            f"Asked to revert image {image.name} to the original but it's filepath was changed "
            f"outside of memsaver, filepath: {image.filepath}."
        )
        if revert_aggregator is not None:
            revert_aggregator.add_output(
                optimized_output_aggregator.OptimizedDatablockInfo(
                    image.name, optimized_output_aggregator.RevertOperationResult.UNCHANGED
                )
            )
        return

    original_path = get_original_path(image)
    if original_path in {None, ""}:
        remove_memsaver_properties(image)
        logger.info(
            f"Asked to revert image {image.name} to the original but it already is, "
            f"filepath: {image.filepath}."
        )
        if revert_aggregator is not None:
            revert_aggregator.add_output(
                optimized_output_aggregator.OptimizedDatablockInfo(
                    image.name, optimized_output_aggregator.RevertOperationResult.UNCHANGED
                )
            )
        return

    image.filepath = original_path
    remove_memsaver_properties(image)
    logger.info(f"Reverted image {image.name} to the original at {original_path} (bpy path).")
    if revert_aggregator is not None:
        revert_aggregator.add_output(
            optimized_output_aggregator.OptimizedDatablockInfo(
                image.name, optimized_output_aggregator.RevertOperationResult.SUCCESS
            )
        )


def find_sequence_num_indices(filename: str) -> typing.Tuple[int, int]:
    """Returns tuple (num_start, num_end) with indices of the first (last) digit of sequence number.

    Returns (-1, -1) if the filename doesn't contain sequence number.
    """
    # Blender is very robust when considering sequence numbers, it iterates through filename
    # from end to start and the first numeric sequence found is considered to be the sequence number:
    # https://github.com/blender/blender/blob/36983fb5e4a297cb26855b6777a7ce25c12d7c49/source/blender/blenlib/intern/path_util.c#L70
    num_start, num_end = -1, -1
    found_digit = False
    for i in range(len(filename) - 1, -1, -1):
        if filename[i].isdigit():
            if found_digit:
                num_start = i
            else:
                found_digit = True
                num_start, num_end = i, i
        elif found_digit:
            break

    return (num_start, num_end)


def udim_matcher(filename: str, start_index: int) -> typing.Optional[typing.Tuple[str, str]]:
    """Tries to match UDIM number in 'filename' starting at 'start_index'.

    UDIM is one format for UDIM/Tiles textures, it has format: 1001 + u-tile + v-tile * 10   (e.g. 1012)
    Returns matched UDIM number and filename without UDIM or None if UDIM wasn't found.
    """
    candidate = filename[start_index : start_index + 4]
    if len(candidate) < 4:
        return None
    if not candidate.isdigit():
        return None
    return (candidate, filename[:start_index] + filename[start_index + 4 :])


def uvtile_matcher(filename: str, start_index: int) -> typing.Optional[typing.Tuple[str, str]]:
    """Tries to match UV Tile string in 'filename' starting at 'start_index'.

    UV Tile is one format for UDIM/Tiles textures, it has format: u(u-tile + 1)_v(v-tile + 1)   (e.g. u1_v2)
    Returns matched UV Tile string and filename without UV Tile or None if UV Tile wasn't found.
    """
    candidate = filename[start_index : start_index + 5]
    if len(candidate) < 5:
        return None
    if (
        candidate[0] == "u"
        and candidate[1].isdigit()
        and candidate[2] == "_"
        and candidate[3] == "v"
        and candidate[4].isdigit()
    ):
        return (candidate, filename[:start_index] + filename[start_index + 5 :])
    return None


def octane_reload_images() -> None:
    # This is a simple workaround to force octane shaded viewport to reload textures
    # modified outside of shader node editor without fully restarting the octane render engine.
    for material in list(bpy.data.materials):
        material.name = material.name


@dataclasses.dataclass
class PathMapping:
    """Mapping from an original to a derivate path.

    Simple container with named items, used dataclass instead of NamedTuple to be consistent with
    OrigToDerivativePaths.
    """

    original: str
    derivative: str


@dataclasses.dataclass
class OrigToDerivativePaths:
    """Dataclass for storing mapping from original to derivative paths for one image datablock.

    'assigned_path' is mapping from path that is originally assigned in image.filepath to the
    new path that should be assigned to image.filepath

    'resource_paths' are mappings from actual image files on disc to the derivative files on the disc

    These two are different for UDIMs where image.filepath has assigned path with <UDIM> or <UVTILE>
    token which doesn't correspond to any file on disc. Blender then references all image files
    matched by those tokens.
    """

    assigned_path: PathMapping
    resource_paths: typing.List[PathMapping]


def get_derivative_paths(
    image: bpy.types.Image, cache_path: str, original_abs_path: str, side_size: int
) -> typing.Optional[OrigToDerivativePaths]:
    """Returns mapping from the original to the derivative image paths.

    None is returned if we don't support resizing image of given type or derivative paths cannot be
    safely inferred.
    """
    dir_path = os.path.dirname(original_abs_path)
    filename, ext = os.path.splitext(os.path.basename(original_abs_path))

    if image.source == 'FILE':
        # Simple single image on the disc
        path_hash = get_filepath_hash(original_abs_path)
        derivative_path = os.path.join(cache_path, f"{path_hash}_{side_size}{ext}")
        path_map = PathMapping(original_abs_path, derivative_path)
        return OrigToDerivativePaths(path_map, [path_map])
    elif image.source == 'SEQUENCE':
        # Sequence of images, one of the images is assigned to image.filepath, Blender then finds
        # the rest of the images based on varying sequence number on the name.
        # e.g. image_0001_diffuse.png -> image_0002_diffuse.png, image_0003_diffuse.png, ..
        num_start, num_end = find_sequence_num_indices(filename)
        if num_start < 0 or num_end < 0:
            logger.error(
                f"Image {image.name} with filepath {image.filepath} of type 'SEQUENCE' does not "
                f"have a sequence number in the filename, skipping derivates generation!"
            )
            return None

        # Generate derivative path for the assigned image
        main_digit = filename[num_start : num_end + 1]
        orig_filename_wo_digit = filename[:num_start] + filename[num_end + 1 :]
        path_hash = get_filepath_hash(os.path.join(dir_path, orig_filename_wo_digit + ext))
        derivative_path = os.path.join(cache_path, f"{path_hash}_{side_size}_{main_digit}{ext}")
        path_map = PathMapping(original_abs_path, derivative_path)
        result = OrigToDerivativePaths(path_map, [path_map])

        # Generate derivative paths for all the corresponding sequence images found on discs
        for potential_seq_filepath in glob.glob(f"{dir_path}/*{ext}"):
            potential_seq_filename, _ = os.path.splitext(os.path.basename(potential_seq_filepath))
            digit = potential_seq_filename[num_start : num_end + 1]
            filename_wo_digit = (
                potential_seq_filename[:num_start] + potential_seq_filename[num_end + 1 :]
            )
            if (
                not digit.isdigit()
                or digit == main_digit
                or filename_wo_digit != orig_filename_wo_digit
            ):
                continue
            derivative_path = os.path.join(cache_path, f"{path_hash}_{side_size}_{digit}{ext}")
            result.resource_paths.append(PathMapping(potential_seq_filepath, derivative_path))
        return result
    elif image.source == 'TILED':
        # Find type of token and it's starting index
        if (udim_start := filename.find("<UDIM>")) > -1:
            token = "<UDIM>"
            orig_filename_wo_token = filename.replace(token, "", 1)
            matcher = functools.partial(udim_matcher, start_index=udim_start)
        elif (udim_start := filename.find("<UVTILE>")) > -1:
            token = "<UVTILE>"
            orig_filename_wo_token = filename.replace(token, "", 1)
            matcher = functools.partial(uvtile_matcher, start_index=udim_start)

        if udim_start == -1:
            logger.error(
                f"Image {image.name} with filepath {image.filepath} of type 'TILED' does not have "
                f"<UDIM> nor <UVTILE> tag in the filename, skipping derivates generation!"
            )
            return None

        # Generate derivative path for filepath with token
        path_hash = get_filepath_hash(os.path.join(dir_path, orig_filename_wo_token + ext))
        derivative_path = os.path.join(cache_path, f"{path_hash}_{side_size}.{token}{ext}")
        path_map = PathMapping(original_abs_path, derivative_path)
        result = OrigToDerivativePaths(path_map, [])

        # Search for TILED images on disc and generate derivative path for them
        for potential_tile_filepath in glob.glob(os.path.join(dir_path, f"*{ext}")):
            potential_tile_filename, _ = os.path.splitext(os.path.basename(potential_tile_filepath))
            split = matcher(potential_tile_filename)
            if split is None:
                continue
            tile_num, filename_wo_token = split
            if orig_filename_wo_token != filename_wo_token:
                continue
            derivative_path = os.path.join(cache_path, f"{path_hash}_{side_size}.{tile_num}{ext}")
            result.resource_paths.append(PathMapping(potential_tile_filepath, derivative_path))
        return result
    else:  # One of 'MOVIE', 'GENERATED', 'VIEWER'
        logger.info(
            f"Image '{image.name}' is of type '{image.source}' and thus no derivative will be "
            f"generated. We don't support it yet or it doesn't even make sense to resize!"
        )
        return None


def ensure_and_assign_derivative_images(
    cache_path: str, original_path: str, image: bpy.types.Image, side_size: int
) -> derivative_generator.GenerateDerivativeResult:
    """Generate derivatives of the image and assign them to the image object

    - Derivatives are not regenerated if they already exist on the disc ('UP_TO_DATE' result).
    - Cannot generate derivatives larger than the original image ('REFUSE_UPSCALE' result).
      In this case, the original image is assigned to the image object.
    """

    original_abs_path = os.path.abspath(bpy.path.abspath(original_path, library=image.library))
    image_paths = get_derivative_paths(image, cache_path, original_abs_path, side_size)
    if image_paths is None:
        return derivative_generator.GenerateDerivativeResult.ERROR

    results: typing.Set[derivative_generator.GenerateDerivativeResult] = set()
    for path_map in image_paths.resource_paths:
        generation_result = derivative_generator.generate_derivative(
            path_map.original, path_map.derivative, side_size
        )
        results.add(generation_result)
        if not generation_result.is_success():
            # Break here, we'll keep the current image
            break

    if all(result.is_success() for result in results):
        # All derivatives were generated successfully
        image.filepath = image_paths.assigned_path.derivative
        # duplicating information to be able to tell if image was changed outside of memsaver
        # saving a basename of the derivative should be enough because it contains the hash suffix
        image[DERIVATIVE_FILENAME_PROPERTY_NAME] = bpy.path.basename(image.filepath)
        image[DERIVATIVE_SIZE_PROPERTY_NAME] = side_size
        logger.info(
            f"Set image {image.name} to derivative {image_paths.assigned_path.derivative} of "
            f"size {side_size}, original at {image_paths.assigned_path.original}."
        )
    else:
        if all(os.path.isfile(path_map.original) for path_map in image_paths.resource_paths):
            # We failed to generate the derivative, which means we could be stuck on outdated or
            # some weird derivative from the past, e.g. 1x1.
            # Switch to original as all original images exist.
            revert_to_original(image)
            logger.warning(
                f"Failed to generate derivatives from original {original_abs_path}, "
                f"reverted image to the original!"
            )
        else:
            logger.warning(
                f"Failed to generate derivatives from original {original_abs_path} "
                f"and original doesn't exist, keeping old derivative!"
            )
    return max(results, key=lambda x: x.value)


class ImageResizeResult(enum.Enum):
    """Enum for storing errors that can occur during image resize."""

    # Unchanged value
    KEEP_ORIGINAL = "Keeping original size"
    SAME_DERIVATIVE_SIZE = "Same derivative size"
    # Success value
    SUCCESS = "Success"
    CHANGED_TO_ORIGINAL = "Changed to original"
    # Error values
    NOT_FINISHED = "Not finished"
    PACKED = "Packed"
    EMPTY_PATH = "Empty path"
    INVALID_SIZE = "Invalid size"
    FAILED_DERIVATIVE = "Failed derivative"
    UNEXPECTED_EXCEPTION = "Unexpected exception"


@dataclasses.dataclass
class ResizedImageInfo(optimized_output_aggregator.OptimizedDatablockInfo[ImageResizeResult]):
    """Dataclass for storing information about resized image."""

    required_side_size: int
    original_size: typing.Tuple[int, int]
    original_size_bytes: int
    new_size: typing.Tuple[int, int] = dataclasses.field(default_factory=lambda: (0, 0))
    new_size_bytes: int = 0


class ResizeImageOutputAggregator(
    optimized_output_aggregator.OptimizedOutputAggregator[ResizedImageInfo]
):
    """Aggregator for resized images.

    This class is used to aggregate resized images and provide a summary of the results.
    """

    def _is_output_successful(self, output: ResizedImageInfo) -> bool:
        return (
            output.result == ImageResizeResult.SUCCESS
            or output.result == ImageResizeResult.CHANGED_TO_ORIGINAL
        )

    def _is_output_unchanged(self, output: ResizedImageInfo) -> bool:
        return (
            output.result == ImageResizeResult.KEEP_ORIGINAL
            or output.result == ImageResizeResult.SAME_DERIVATIVE_SIZE
        )

    def get_output_result_message(self, output: ResizedImageInfo) -> str:
        RESULT_TO_MESSAGE_MAP = {
            ImageResizeResult.SUCCESS: f"Image '{output.name}' resized from {tuple(output.original_size)} to {output.new_size}.",
            ImageResizeResult.CHANGED_TO_ORIGINAL: f"Image '{output.name}' changed to original size {tuple(output.original_size)} which is smaller or equal to the requested side size {output.required_side_size}.",
            ImageResizeResult.KEEP_ORIGINAL: f"Image '{output.name}' has original size {tuple(output.original_size)} which is smaller or equal to the requested side size {output.required_side_size}.",
            ImageResizeResult.SAME_DERIVATIVE_SIZE: f"Image '{output.name}' has derivative size {tuple(output.new_size)} which is equal to the requested side size {output.required_side_size}.",
            ImageResizeResult.NOT_FINISHED: f"Resizing of image '{output.name}' was not finished.",
            ImageResizeResult.PACKED: f"Image '{output.name}' is packed, can't change its size.",
            ImageResizeResult.EMPTY_PATH: f"Image '{output.name}' has empty original path, it's most likely generated. Can't change its size.",
            ImageResizeResult.INVALID_SIZE: f"Image '{output.name}' has size {tuple(output.original_size)}, can't change its size!",
            ImageResizeResult.FAILED_DERIVATIVE: f"Failed to generate derivative for image '{output.name}'.",
            ImageResizeResult.UNEXPECTED_EXCEPTION: f"Unexpected exception while resizing image '{output.name}'.",
        }

        message = RESULT_TO_MESSAGE_MAP.get(output.result, None)
        if message is None:
            raise ValueError(
                f"Unknown resizing result '{output.result}' for image '{output.name}'."
            )
        return message

    @property
    def saved_image_memory_bytes(self) -> int:
        return sum(
            image.original_size_bytes - image.new_size_bytes for image in self.successful_outputs
        )

    def get_summary_message(self) -> str:
        message = ""
        successful_images = list(self.successful_outputs)
        failed_images = list(self.failed_outputs)

        if len(successful_images) == 0 and len(failed_images) == 0:
            return "No changes needed for image resizing. "

        message += f"Resized {len(successful_images)} image" + (
            "s" if (len(successful_images) > 1 or len(successful_images) == 0) else ""
        )
        message += f", failed {len(failed_images)}. " if len(failed_images) > 0 else ". "
        total_memory_saved = self.saved_image_memory_bytes
        if total_memory_saved > 0:
            message += f"Saved memory: {polib.utils_bpy.convert_size(total_memory_saved)}. "
        return message


def change_image_size(
    cache_path: str,
    image: bpy.types.Image,
    side_size: int,
    image_aggregator: ResizeImageOutputAggregator,
) -> None:
    assert side_size > 0
    original_size_bytes = memory_usage.get_image_size_bytes(image)
    resized_image = ResizedImageInfo(
        image.name,
        ImageResizeResult.NOT_FINISHED,
        side_size,
        image.size,
        original_size_bytes,
        # If the resize fails, the new size will be equal to the original size
        image.size,
        original_size_bytes,
    )
    image_aggregator.add_output(resized_image)
    try:
        if typing.cast(typing.Optional[bpy.types.PackedFile], image.packed_file) is not None:
            resized_image.result = ImageResizeResult.PACKED
            return
        original_path = ensure_original_path(image)
        if original_path == "":
            resized_image.result = ImageResizeResult.EMPTY_PATH
            return

        derivate_size = image.get(DERIVATIVE_SIZE_PROPERTY_NAME, 0)
        if derivate_size == 0 and min(image.size) == 0:
            resized_image.result = ImageResizeResult.INVALID_SIZE
            return

        # if the image is original and its size is the same or smaller than what's requested
        # or if the image is derivative and its size is the same as what's requested,
        # we can do an early out optimization here
        elif derivate_size == 0 and max(image.size) <= side_size:
            resized_image.new_size_bytes = resized_image.original_size_bytes
            resized_image.result = ImageResizeResult.KEEP_ORIGINAL
            return

        elif derivate_size > 0 and derivate_size == side_size:
            resized_image.new_size_bytes = side_size
            resized_image.result = ImageResizeResult.SAME_DERIVATIVE_SIZE
            return

        derive_result = ensure_and_assign_derivative_images(
            cache_path, original_path, image, side_size
        )
        if derive_result in (
            derivative_generator.GenerateDerivativeResult.UNSUPPORTED,
            derivative_generator.GenerateDerivativeResult.ERROR,
        ):
            resized_image.result = ImageResizeResult.FAILED_DERIVATIVE
            return
        resized_image.new_size = image.size
        resized_image.new_size_bytes = memory_usage.get_image_size_bytes(image)
        resized_image.result = (
            ImageResizeResult.CHANGED_TO_ORIGINAL
            if derive_result == derivative_generator.GenerateDerivativeResult.REFUSE_UPSCALE
            else ImageResizeResult.SUCCESS
        )
    except Exception:
        logger.exception(f"Unexpected exception while resizing image '{image.name}'")
        resized_image.result = ImageResizeResult.UNEXPECTED_EXCEPTION
        return


def change_image_sizes(
    cache_path: str,
    image_to_new_side_size_map: typing.Dict[bpy.types.Image, int],
    image_aggregator: ResizeImageOutputAggregator,
    progress_wm: typing.Optional[bpy.types.WindowManager] = None,
) -> None:
    """Resizes the images to their mapped values."""
    progress = 0
    if progress_wm is not None:
        progress_wm.progress_begin(0, len(image_to_new_side_size_map))

    for image, side_size in image_to_new_side_size_map.items():
        if progress_wm is not None:
            progress += 1
            progress_wm.progress_update(progress)
        change_image_size(cache_path, image, side_size, image_aggregator)

    if progress_wm is not None:
        progress_wm.progress_end()


CheckedOutputInfo = optimized_output_aggregator.OptimizedDatablockInfo[
    derivative_generator.GenerateDerivativeResult
]


class CheckDerivativeOutputAggregator(
    optimized_output_aggregator.OptimizedOutputAggregator[CheckedOutputInfo]
):
    """Aggregator for checking derived images.

    This class is used to aggregate and summarize results from 'check_derivative'.
    """

    def _is_output_successful(self, output: CheckedOutputInfo) -> bool:
        return (
            output.result == derivative_generator.GenerateDerivativeResult.REGENERATED
            or output.result == derivative_generator.GenerateDerivativeResult.REFUSE_UPSCALE
        )

    def _is_output_unchanged(self, output: CheckedOutputInfo) -> bool:
        return output.result == derivative_generator.GenerateDerivativeResult.UP_TO_DATE

    def get_output_result_message(self, output: CheckedOutputInfo) -> str:
        RESULT_TO_MESSAGE_MAP = {
            derivative_generator.GenerateDerivativeResult.UP_TO_DATE: f"Image '{output.name}' is up to date.",
            derivative_generator.GenerateDerivativeResult.REGENERATED: f"Image '{output.name}' was regenerated.",
            derivative_generator.GenerateDerivativeResult.REFUSE_UPSCALE: f"Original image was used for '{output}'.",
            derivative_generator.GenerateDerivativeResult.UNSUPPORTED: f"Failed to derive image '{output.name}'. The image format is not supported.",
            derivative_generator.GenerateDerivativeResult.ERROR: f"Failed to derive image '{output.name}'.",
        }

        message = RESULT_TO_MESSAGE_MAP.get(output.result, None)
        if message is None:
            raise ValueError(
                f"Unknown derivative result '{output.result}' for image '{output.name}'."
            )
        return message

    def get_summary_message(self) -> str:
        messages = []
        up_to_date_derivatives = sum(1 for _ in self.unchanged_outputs)
        if up_to_date_derivatives > 0:
            messages.append(
                f"{up_to_date_derivatives} derivative"
                + ("s" if up_to_date_derivatives != 1 else "")
                + " up to date"
            )
        regenerated_derivatives = sum(1 for _ in self.successful_outputs)
        if regenerated_derivatives > 0:
            messages.append(
                f"{regenerated_derivatives} derivative"
                + ("s" if regenerated_derivatives != 1 else "")
                + " regenerated"
            )
        failed_derivatives = sum(1 for _ in self.failed_outputs)
        if failed_derivatives > 0:
            messages.append(
                f"{failed_derivatives} derivative"
                + ("s" if failed_derivatives != 1 else "")
                + " failed"
            )

        if len(messages) > 0:
            return ", ".join(messages) + "."
        return "No derivatives to check."


def check_derivative(
    cache_path: typing.Optional[str],
    image: bpy.types.Image,
    check_derivative_aggregator: typing.Optional[CheckDerivativeOutputAggregator] = None,
) -> None:
    """Re-generate derivative image if the original image file was changed on disk

    cache_path may be None, in this case it will be inferred from derivative absolute path
    """
    if was_filepath_overwritten_on_derivative(image):
        remove_memsaver_properties(image)
        if check_derivative_aggregator is not None:
            check_derivative_aggregator.add_output(
                optimized_output_aggregator.OptimizedDatablockInfo(
                    image.name, derivative_generator.GenerateDerivativeResult.ERROR
                )
            )
        return

    original_path = get_original_path(image)
    if original_path is None:  # it's original or original path custom property is not present
        return

    side_size: int = image.get(DERIVATIVE_SIZE_PROPERTY_NAME, 0)
    if side_size == 0:  # it's original or no custom property is present
        return

    # we can infer cache_path, this is useful especially in the post_load handler
    if cache_path is None:
        cache_path = os.path.dirname(image.filepath)
        if not os.path.isdir(cache_path):
            logger.warning(
                f"Inferred cache_path {cache_path} from image.filepath {image.filepath}, "
                f"however the cache_path is not a valid directory! Skipping!"
            )
            if check_derivative_aggregator is not None:
                check_derivative_aggregator.add_output(
                    CheckedOutputInfo(
                        image.name, derivative_generator.GenerateDerivativeResult.ERROR
                    )
                )
            return

    result = ensure_and_assign_derivative_images(cache_path, original_path, image, side_size)
    if check_derivative_aggregator is not None:
        check_derivative_aggregator.add_output(CheckedOutputInfo(image.name, result))
