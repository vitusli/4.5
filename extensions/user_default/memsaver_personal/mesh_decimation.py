# copyright (c) 2018- polygoniq xyz s.r.o.

import typing
import collections
import dataclasses
import enum
import bpy
import logging
from . import preferences
from . import optimized_output_aggregator
from . import object_render_estimator
from . import memory_usage

logger = logging.getLogger(f"polygoniq.{__name__}")


DECIMATE_MODIFIER_NAME = "memsaver_decimate"


def get_target_objects(context: bpy.types.Context) -> typing.Iterable[bpy.types.Object]:
    operator_target = preferences.get_preferences(context).decimate_meshes_target

    if operator_target == preferences.OperatorTarget.SELECTED_OBJECTS.value:
        return context.selected_objects
    elif operator_target == preferences.OperatorTarget.SCENE_OBJECTS.value:
        return context.scene.objects
    elif operator_target == preferences.OperatorTarget.ALL_OBJECTS.value:
        return bpy.data.objects
    else:
        raise ValueError(f"Unknown selection target '{operator_target}'")


def get_adaptive_optimize_target_objects(
    context: bpy.types.Context,
) -> typing.Iterable[bpy.types.Object]:
    operator_target = preferences.get_preferences(context).adaptive_mesh_target

    if operator_target == preferences.OperatorTarget.SELECTED_OBJECTS.value:
        return context.selected_objects
    elif operator_target == preferences.OperatorTarget.SCENE_OBJECTS.value:
        return context.scene.objects
    else:
        raise ValueError(f"Unknown selection target '{operator_target}'")


def get_meshes_used_in_object(obj: bpy.types.Object) -> typing.Iterable[bpy.types.Mesh]:
    if obj.type == 'EMPTY':
        if obj.instance_type == 'COLLECTION':
            if obj.instance_collection is None:
                return  # warn?

            for instanced_object in obj.instance_collection.objects:
                yield from get_meshes_used_in_object(instanced_object)

    elif obj.type == 'MESH':
        if obj.data is None:
            return  # warn?

        yield obj.data


def generate_mesh_objects_map(
    objects: typing.Iterable[bpy.types.Object],
) -> typing.DefaultDict[bpy.types.Mesh, typing.List[bpy.types.Object]]:
    mesh_objects_map: typing.DefaultDict[bpy.types.Mesh, typing.List[bpy.types.Object]] = (
        collections.defaultdict(list)
    )

    for obj in objects:
        meshes = get_meshes_used_in_object(obj)
        for mesh in meshes:
            mesh_objects_map[mesh].append(obj)

    return mesh_objects_map


def update_object_decimation_ratio_map(
    objects_decimation_ratio_map: typing.DefaultDict[bpy.types.Object, float],
    mesh_objects_map: typing.DefaultDict[bpy.types.Mesh, typing.List[bpy.types.Object]],
    scene: bpy.types.Scene,
    camera: bpy.types.Object,
    objects: typing.Iterable[bpy.types.Object],
    full_quality_distance: float,
    lowest_quality_distance: float,
    lowest_quality_decimation_ratio: float,
    lowest_face_count: float,
) -> None:
    decimation_interpolation_denominator = lowest_quality_distance - full_quality_distance
    if decimation_interpolation_denominator <= 0:
        decimation_interpolation_denominator = 1

    for mesh, objects in mesh_objects_map.items():
        if len(mesh.polygons) < lowest_face_count:
            continue  # ignore meshes with lower face count than the one given

        mesh_min_distance = float("inf")

        for obj in objects:
            if obj.library is not None:  # linked, non-editable object
                # set min distance to 0 to avoid any decimation, we won't be able to add the same
                # decimation to all objects using this mesh, so let's not decimate at all
                mesh_min_distance = 0.0
                break

            _, _, obj_min_distance = object_render_estimator.get_object_2d_bounds(
                scene, camera, obj
            )
            if obj_min_distance is not None:
                mesh_min_distance = min(mesh_min_distance, obj_min_distance)

        # object_render_estimator will return negative values of the object intersects the camera
        # we assume non-negative values so let's clamp to 0
        mesh_min_distance = max(0.0, mesh_min_distance)

        # Everything closer than full_quality_distance has decimation ratio 1.0
        # Everything further than lowest_quality_distance has decimation ratio set to
        # lowest_quality_decimation_ratio
        # Between minimum_distance and lowest_quality_distance interpolate linearly from 1.0 to
        # lowest_quality_decimation_ratio

        decimation_ratio = 1.0
        if mesh_min_distance <= full_quality_distance:
            decimation_ratio = 1.0
        elif mesh_min_distance <= lowest_quality_distance:
            nominator = mesh_min_distance - full_quality_distance
            interpolation_factor = nominator / decimation_interpolation_denominator
            assert interpolation_factor >= 0.0
            assert interpolation_factor <= 1.0
            decimation_ratio = (
                1.0 - interpolation_factor
            ) * 1.0 + interpolation_factor * lowest_quality_decimation_ratio
        else:
            decimation_ratio = lowest_quality_decimation_ratio

        assert decimation_ratio >= 0.0
        assert decimation_ratio <= 1.0
        for obj in objects:
            objects_decimation_ratio_map[obj] = max(
                objects_decimation_ratio_map[obj], decimation_ratio
            )


def get_objects_decimation_ratio_map_current_frame(
    scene: bpy.types.Scene,
    camera: bpy.types.Object,
    objects: typing.Iterable[bpy.types.Object],
    minimum_distance: float,
    lowest_quality_distance: float,
    lowest_quality_decimation_ratio: float,
    lowest_face_count: float,
) -> typing.DefaultDict[bpy.types.Object, float]:
    mesh_objects_map = generate_mesh_objects_map(objects)
    objects_decimation_ratio_map: typing.DefaultDict[bpy.types.Object, float] = (
        collections.defaultdict(float)
    )
    update_object_decimation_ratio_map(
        objects_decimation_ratio_map,
        mesh_objects_map,
        scene,
        camera,
        objects,
        minimum_distance,
        lowest_quality_distance,
        lowest_quality_decimation_ratio,
        lowest_face_count,
    )
    return objects_decimation_ratio_map


def get_objects_decimation_ratio_map_animation_mode(
    scene: bpy.types.Scene,
    camera: bpy.types.Object,
    objects: typing.Iterable[bpy.types.Object],
    minimum_distance: float,
    lowest_quality_distance: float,
    lowest_quality_decimation_ratio: float,
    lowest_face_count: float,
) -> typing.DefaultDict[bpy.types.Object, float]:
    previous_frame_current = scene.frame_current
    try:
        mesh_objects_map = generate_mesh_objects_map(objects)
        objects_decimation_ratio_map: typing.DefaultDict[bpy.types.Object, float] = (
            collections.defaultdict(float)
        )
        current_frame = scene.frame_start
        while current_frame <= scene.frame_end:
            scene.frame_current = current_frame
            bpy.context.view_layer.update()

            update_object_decimation_ratio_map(
                objects_decimation_ratio_map,
                mesh_objects_map,
                scene,
                camera,
                objects,
                minimum_distance,
                lowest_quality_distance,
                lowest_quality_decimation_ratio,
                lowest_face_count,
            )
            current_frame += 1

        return objects_decimation_ratio_map
    finally:
        scene.frame_current = previous_frame_current
        bpy.context.view_layer.update()


class RevertMeshToOriginalOutputAggregator(
    optimized_output_aggregator.RevertOperationResultAggregator
):
    def _get_operation_target(self, plural: bool) -> str:
        return "meshes" if plural else "mesh"


def revert_to_original(
    obj: bpy.types.Object,
    revert_aggregator: RevertMeshToOriginalOutputAggregator,
) -> None:
    """Reverts the object to its original state by removing the decimation modifier."""
    if DECIMATE_MODIFIER_NAME in obj.modifiers:
        obj.modifiers.remove(obj.modifiers[DECIMATE_MODIFIER_NAME])
        revert_aggregator.add_output(
            optimized_output_aggregator.OptimizedDatablockInfo(
                obj.name, optimized_output_aggregator.RevertOperationResult.SUCCESS
            )
        )
    else:
        revert_aggregator.add_output(
            optimized_output_aggregator.OptimizedDatablockInfo(
                obj.name, optimized_output_aggregator.RevertOperationResult.UNCHANGED
            )
        )


class MeshObjectDecimationResult(enum.Enum):
    SUCCESS = "Success"
    SAME_RATIO = "Same ratio"
    NOT_FINISHED = "Not finished"
    UNEXPECTED_EXCEPTION = "Unexpected exception"


@dataclasses.dataclass
class DecimatedMeshObjectInfo(
    optimized_output_aggregator.OptimizedDatablockInfo[MeshObjectDecimationResult]
):
    original_triangle_count: int = 0
    new_triangle_count: int = 0


class DecimateMeshObjectOutputAggregator(
    optimized_output_aggregator.OptimizedOutputAggregator[DecimatedMeshObjectInfo]
):
    def _is_output_successful(self, output: DecimatedMeshObjectInfo) -> bool:
        return output.result == MeshObjectDecimationResult.SUCCESS

    def _is_output_unchanged(self, output: DecimatedMeshObjectInfo) -> bool:
        return output.result == MeshObjectDecimationResult.SAME_RATIO

    def get_output_result_message(self, output: DecimatedMeshObjectInfo) -> str:
        RESULT_TO_MESSAGE_MAP = {
            MeshObjectDecimationResult.SUCCESS: f"Mesh object '{output.name}' decimated successfully.",
            MeshObjectDecimationResult.SAME_RATIO: f"Mesh object '{output.name}' already has the desired decimation ratio.",
            MeshObjectDecimationResult.NOT_FINISHED: f"Decimation of mesh object '{output.name}' was not finished.",
            MeshObjectDecimationResult.UNEXPECTED_EXCEPTION: f"Unexpected exception while decimating mesh object '{output.name}'",
        }
        message = RESULT_TO_MESSAGE_MAP.get(output.result, None)
        if message is not None:
            return message
        return f"Unknown mesh decimation result '{output.result}' for mesh object '{output.result}'"

    def get_summary_message(self) -> str:
        message = ""
        successful_meshes = list(self.successful_outputs)
        failed_meshes = list(self.failed_outputs)

        if len(successful_meshes) == 0 and len(failed_meshes) == 0:
            return "No changes needed for mesh decimation. "

        message += f"Decimated {len(successful_meshes)} mesh object" + (
            "s" if (len(successful_meshes) > 1 or len(successful_meshes) == 0) else ""
        )
        message += f", failed {len(failed_meshes)}. " if len(failed_meshes) > 0 else ". "
        total_triangles_removed = sum(
            [mesh.original_triangle_count - mesh.new_triangle_count for mesh in successful_meshes]
        )
        if total_triangles_removed > 0:
            message += f"Removed triangles: {total_triangles_removed}. "
        return message


def set_decimation_ratio(
    obj: bpy.types.Object,
    decimation_ratio: float,
) -> bool:
    """Sets the decimation ratio of the given object.

    Returns True if the decimation ratio was set, False if the object already has the same ratio.
    """
    assert obj.type == 'MESH'
    logger.info(f"Setting decimation_ratio {decimation_ratio} for object {obj.name}")

    memsaver_decimation = obj.modifiers.get(DECIMATE_MODIFIER_NAME, None)
    if memsaver_decimation is None and decimation_ratio == 1.0:
        # Already undecimated
        return False
    if memsaver_decimation is not None and memsaver_decimation.ratio == decimation_ratio:
        # Already decimated with the same ratio
        return False

    if decimation_ratio == 1.0:
        # no decimation
        revert_to_original(obj)
    else:
        if memsaver_decimation is None:
            memsaver_decimation = obj.modifiers.new(DECIMATE_MODIFIER_NAME, 'DECIMATE')
        memsaver_decimation.ratio = decimation_ratio

    return True


def set_decimation_ratios(
    objects_to_decimation_ratio_map: typing.Dict[bpy.types.Object, float],
    mesh_obj_aggregator: DecimateMeshObjectOutputAggregator,
) -> None:
    """Sets the decimation ratio of objects to their mapped values."""
    depsgraph = bpy.context.evaluated_depsgraph_get()
    obj_to_decimated_mesh_obj_map = {}
    for obj in objects_to_decimation_ratio_map.keys():
        mesh = obj.evaluated_get(depsgraph).data
        triangle_count = memory_usage.get_mesh_triangle_count(mesh)
        decimated_mesh_obj = DecimatedMeshObjectInfo(
            obj.name,
            MeshObjectDecimationResult.NOT_FINISHED,
            # Let's get the original triangle count from the "stale" depsgraph
            triangle_count,
            # If the decimation fails, the new triangle count will be equal to the original one
            triangle_count,
        )
        obj_to_decimated_mesh_obj_map[obj] = decimated_mesh_obj
        mesh_obj_aggregator.add_output(decimated_mesh_obj)

    for obj, decimation_ratio in objects_to_decimation_ratio_map.items():
        decimated_mesh_obj = obj_to_decimated_mesh_obj_map[obj]
        try:
            success = set_decimation_ratio(obj, decimation_ratio)
            decimated_mesh_obj.result = (
                MeshObjectDecimationResult.SUCCESS
                if success
                else MeshObjectDecimationResult.SAME_RATIO
            )
        except Exception:
            logger.exception(
                f"Unexpected exception while creating decimation modifier for '{obj.name}'"
            )
            decimated_mesh_obj.result = MeshObjectDecimationResult.UNEXPECTED_EXCEPTION
            continue

    # Get the new mesh triangle counts from updated depsgraph
    depsgraph.update()
    for obj, decimated_mesh_obj in obj_to_decimated_mesh_obj_map.items():
        if decimated_mesh_obj.result != MeshObjectDecimationResult.SUCCESS:
            continue
        mesh = obj.evaluated_get(depsgraph).data
        decimated_mesh_obj.new_triangle_count = memory_usage.get_mesh_triangle_count(mesh)

    return None
