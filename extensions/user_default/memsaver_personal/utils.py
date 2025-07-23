# copyright (c) 2018- polygoniq xyz s.r.o.

import bpy
import typing
import logging

logger = logging.getLogger(f"polygoniq.{__name__}")


def get_images_used_in_node(node: bpy.types.Node) -> typing.Set[bpy.types.Image]:
    ret = set()

    if hasattr(node, "node_tree"):
        if node.node_tree is not None:
            for child_node in node.node_tree.nodes:
                ret.update(get_images_used_in_node(child_node))

    if hasattr(node, "image"):
        if node.image is not None:
            ret.add(node.image)

    return ret


def get_images_used_in_material(
    material: typing.Optional[bpy.types.Material],
) -> typing.Set[bpy.types.Image]:
    if material is None:
        return set()

    if not material.use_nodes:
        # TODO: We will probably have to implement this :-(
        logger.warning(
            f"Can't get used textures from material '{material.name}' that is not using "
            f"the node system!"
        )
        return set()

    assert material.node_tree is not None, "use_nodes is True, yet node_tree is None"
    ret = set()
    for node in material.node_tree.nodes:
        ret.update(get_images_used_in_node(node))

    return ret


def get_images_used_in_object(obj: bpy.types.Object) -> typing.Set[bpy.types.Image]:
    ret = set()
    for material_slot in obj.material_slots:
        if material_slot.material is None:
            continue

        ret.update(get_images_used_in_material(material_slot.material))

    if obj.instance_type == 'COLLECTION' and obj.instance_collection is not None:
        for instanced_object in obj.instance_collection.objects:
            ret.update(get_images_used_in_object(instanced_object))

    for particle_system in obj.particle_systems:
        particle_settings: bpy.types.ParticleSystem = particle_system.settings
        if particle_settings.instance_object is None:
            continue
        ret.update(get_images_used_in_object(particle_settings.instance_object))

    return ret
