# copyright (c) 2018- polygoniq xyz s.r.o.

import typing
import collections
import bpy
import bpy_extras.object_utils
import logging
from . import hatchery
from . import utils

logger = logging.getLogger(f"polygoniq.{__name__}")


def get_object_2d_bounds(
    scene: bpy.types.Scene, camera: bpy.types.Object, obj: bpy.types.Object
) -> typing.Tuple[float, float, typing.Optional[float]]:
    """Returns width, height in pixels and depth in world units of bounding box in camera space

    Result can be bigger than render resolution as it's not clipped to camera plane. Returns
    0, 0 None if object's 3D bounding box is not visible from camera.
    """

    logger.debug(
        f"Asked for 2D bounds of object {obj.name} in scene {scene.name} using camera {camera.name}."
    )

    bounding_box = hatchery.bounding_box.AlignedBox()
    bounding_box.extend_by_object(obj)

    min_x = float("inf")
    max_x = float("-inf")
    min_y = float("inf")
    max_y = float("-inf")
    min_depth = float("inf")
    max_depth = float("-inf")

    for corner in bounding_box.get_corners():
        # get the 2D pixel coordinates of the bounding box corner. NDC = normalized device coords
        try:
            corner_ndc_x, corner_ndc_y, corner_depth = bpy_extras.object_utils.world_to_camera_view(
                scene, camera, corner
            )
        except:
            logger.exception(
                f"Failed to get NDC coordinates for one of bounding box corners for {obj.name}, "
                f"skipping that corner..."
            )
            continue

        # NDC has [0, 0] for the bottom left and [1, 1] for the top right of the camera frame.
        # But if corner in world_to_camera_view() is behind camera, x and y of NDC is
        # multiplied by -1 (frame is scaled by -1).
        # https://github.com/blender/blender/blob/ce96abd33aeaa0ae4e13db09ce6a1cacb18e9ff8/scripts/modules/bpy_extras/object_utils.py#L254
        if corner_depth < 0.0:
            corner_ndc_x = -corner_ndc_x
            corner_ndc_y = -corner_ndc_y

        # convert NDC into pixel values
        corner_2d_x = corner_ndc_x * scene.render.resolution_x
        corner_2d_y = (1.0 - corner_ndc_y) * scene.render.resolution_y

        min_x = min(min_x, corner_2d_x)
        max_x = max(max_x, corner_2d_x)
        min_y = min(min_y, corner_2d_y)
        max_y = max(max_y, corner_2d_y)
        min_depth = min(min_depth, corner_depth)
        max_depth = max(max_depth, corner_depth)

    if max_depth < 0:
        # the object is entirely behind the camera
        logger.debug(
            f"Object {obj.name} 2D bounds ended up as 0, 0 because it's entirely behind the "
            f"camera. min_depth: {min_depth}, max_depth: {max_depth}."
        )
        return 0, 0, None

    if max_x < 0:
        # the object is entirely left of the frustum
        logger.debug(
            f"Object {obj.name} 2D bounds ended up as 0, 0 because it's entirely left of the "
            f"frustum of the camera. min_x: {min_x}, max_x: {max_x}."
        )
        return 0, 0, None

    if min_x > bpy.context.scene.render.resolution_x:
        # the object is entirely right of the frustum
        logger.debug(
            f"Object {obj.name} 2D bounds ended up as 0, 0 because it's entirely right of the "
            f"frustum of the camera. min_x: {min_x}, max_x: {max_x}."
        )
        return 0, 0, None

    if max_y < 0:
        # the object is entirely under the frustum
        logger.debug(
            f"Object {obj.name} 2D bounds ended up as 0, 0 because it's entirely down under the "
            f"frustum of the camera. min_y: {min_y}, max_y: {max_y}."
        )
        return 0, 0, None

    if min_y > bpy.context.scene.render.resolution_y:
        # the object is entirely over the frustum
        logger.debug(
            f"Object {obj.name} 2D bounds ended up as 0, 0 because it's entirely up over the "
            f"frustum of the camera. min_y: {min_y}, max_y: {max_y}."
        )
        return 0, 0, None

    size_x = max_x - min_x
    size_y = max_y - min_y
    assert size_x >= 0
    assert size_y >= 0

    logger.debug(
        f"Object {obj.name} 2D bounds ended up as {size_x}, {size_y}. "
        f"min_x: {min_x}, max_x: {max_x}, min_y: {min_y}, max_y: {max_y}, "
        f"min_depth: {min_depth}, max_depth: {max_depth}."
    )
    return size_x, size_y, min_depth


def update_size_map_for_objects(
    size_map: typing.DefaultDict[bpy.types.Image, int],
    scene: bpy.types.Scene,
    camera: bpy.types.Object,
    objects: typing.Iterable[bpy.types.Object],
    size_factor: float,
    min_size: int,
    max_size: int,
    size_pot_only: bool = True,
    object_image_map: typing.Optional[
        typing.Dict[bpy.types.Object, typing.Set[bpy.types.Image]]
    ] = None,
) -> None:
    assert max_size >= min_size

    for obj in objects:
        size_x, size_y, _ = get_object_2d_bounds(scene, camera, obj)
        size_max = max(size_x, size_y)
        side_size: int = round(size_max * size_factor)

        assert side_size >= 0
        side_size = max(side_size, min_size)
        side_size = min(side_size, max_size)
        if side_size == 0:
            side_size = 1  # we can't scale images to 0

        if size_pot_only:
            side_size = 1 << (side_size - 1).bit_length()
            if side_size < 32 and side_size > 1:
                # don't generate any sizes between 1 and 32, it's wasted files
                side_size = 32

        obj_images = None
        if object_image_map is not None:
            obj_images = object_image_map.get(obj, None)

        if obj_images is None:
            obj_images = utils.get_images_used_in_object(obj)

        for image in obj_images:
            if size_map[image] < side_size:
                logger.debug(
                    f"Upgrading image {image.name} from size {size_map[image]} to {side_size} because "
                    f"of its usage in object {obj.name}, 2D bounds of object: {size_x}, {size_y}."
                )
                # Only update the new size if it is smaller than the original image size
                # 1 is the smallest side, images with side 0 are not allowed
                size_map[image] = min(side_size, max(image.size[0], image.size[1], 1))


def get_size_map_for_objects_current_frame(
    scene: bpy.types.Scene,
    camera: bpy.types.Object,
    objects: typing.Iterable[bpy.types.Object],
    size_factor: float,
    min_size: int,
    max_size: int,
    size_pot_only: bool = True,
) -> typing.DefaultDict[bpy.types.Image, int]:
    # 0 in the dictionary means we want the original
    ret: typing.DefaultDict[bpy.types.Image, int] = collections.defaultdict(lambda: 1)
    update_size_map_for_objects(
        ret, scene, camera, objects, size_factor, min_size, max_size, size_pot_only
    )
    return ret


def get_size_map_for_objects_animation_mode(
    scene: bpy.types.Scene,
    camera: bpy.types.Object,
    objects: typing.Iterable[bpy.types.Object],
    size_factor: float,
    min_size: int,
    max_size: int,
    size_pot_only: bool = True,
) -> typing.DefaultDict[bpy.types.Image, int]:
    previous_frame_current = scene.frame_current
    try:
        object_image_map = {obj: utils.get_images_used_in_object(obj) for obj in objects}

        # 0 in the dictionary means we want the original
        ret: typing.DefaultDict[bpy.types.Image, int] = collections.defaultdict(lambda: 1)
        current_frame = scene.frame_start
        while current_frame <= scene.frame_end:
            scene.frame_current = current_frame
            bpy.context.view_layer.update()
            update_size_map_for_objects(
                ret,
                scene,
                camera,
                objects,
                size_factor,
                min_size,
                max_size,
                size_pot_only,
                object_image_map,
            )
            current_frame += 1

        return ret
    finally:
        scene.frame_current = previous_frame_current
        bpy.context.view_layer.update()
