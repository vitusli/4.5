# copyright (c) 2018- polygoniq xyz s.r.o.

import bpy
import typing
import enum
import re
import logging
from . import polib
from . import serialize_utils

if typing.TYPE_CHECKING:
    from . import renderset_context

logger = logging.getLogger(f"polygoniq.{__name__}")


MODULE_CLASSES: typing.List[typing.Type] = []


# Covers both types of object prop paths: 'bpy.data.objects["Name"]' and 'bpy.context.scene.objects["Name"]'
BPY_OBJECT_PROP_PATH_PREFIX_REGEX = re.compile(
    r"^bpy\.(?:data|context\.scene)\.objects\[([\"\'])(.*?)\1\]"
)


# Some of the render region properties are not accessible through UI, we list them here and
# provide functions to store and clear them. From UI this can then be toggled by a operator.
RENDER_REGION_PROPS = {
    "bpy.context.scene.render.use_border",
    "bpy.context.scene.render.border_max_x",
    "bpy.context.scene.render.border_max_y",
    "bpy.context.scene.render.border_min_x",
    "bpy.context.scene.render.border_min_y",
}


class PropertyOverrideAction(enum.Enum):
    ADD = "ADD"
    REMOVE = "REMOVE"


def get_prop_full_path(context: bpy.types.Context) -> typing.Optional[str]:
    """Returns path to the property selected in `context`.

    Example: When called from menu operator if render engine selection was right-clicked, it
    returns 'bpy.data.scenes["Scene"].render.engine'.

    Returns None if 'context' isn't a context where a user selected a property.
    """
    button_pointer = getattr(context, "button_pointer", None)
    button_prop = getattr(context, "button_prop", None)

    if button_pointer is None or button_prop is None:
        # Property was not clicked. Either this function was called in wrong context where user
        # didn't click anything or the operator button was clicked in which case
        # context.button_operator is populated.
        return None

    if not hasattr(button_prop, "identifier"):
        # I'm not sure if this can ever happen but to be extra safe, we check it
        logger.error(f"button_prop '{button_prop}' doesn't have 'identifier' attribute!")
        return None

    # When right-clicking on material name in the Shader Editor/Properties users expect to store
    # material assigned to the object, not the material name.
    if isinstance(button_pointer, bpy.types.Material) and button_prop.identifier == "name":
        active_obj = context.active_object
        if active_obj is None:
            return None
        button_pointer = active_obj.material_slots[active_obj.active_material_index]
        button_prop = button_pointer.bl_rna.properties["material"]
    # The same when clicking on material in UIList in the Properties.
    if (
        isinstance(button_pointer, bpy.types.Object)
        and button_prop.identifier == "active_material_index"
    ):
        button_pointer = button_pointer.material_slots[button_pointer.active_material_index]
        button_prop = button_pointer.bl_rna.properties["material"]

    # TODO: button_pointer.__repr__() doesn't always work, for example if we want to access property
    # from an addon. It is more reliable to use copy_data_path_button() operator but that is very
    # slow and cannot be used in poll() method.
    # if bpy.ops.ui.copy_data_path_button.poll():
    #     bpy.ops.ui.copy_data_path_button("INVOKE_DEFAULT", full_path=True)
    #     prop_path = context.window_manager.clipboard
    pointer_path = button_pointer.__repr__()
    # Not really sure now, what "..." means in general in property paths and how to handle it in
    # general. I suspect that in some UI elements when properties are drawn for datablocks from
    # collections, it cannot be retrieved which datablock from collection owns this property.
    # E.g. 'Hide in Viewport' next to objects in the Outliner results in
    # bpy.data.scenes['Scene']...hide_viewport.
    if "..." in pointer_path:
        return None

    pointer_path = pointer_path.replace("\"", "'")

    prop_full_path = None
    if hasattr(button_pointer, button_prop.identifier):
        prop_full_path = f"{pointer_path}.{button_prop.identifier}"
    elif button_prop.identifier in button_pointer:
        prop_full_path = f"{pointer_path}['{button_prop.identifier}']"

    if prop_full_path is None:
        return None

    # Convert path to any scene to the path of current scene starting with bpy.context
    # e.g. 'bpy.data.scenes["Scene"].render.engine' -> 'bpy.context.scene.render.engine'
    # Currently, renderset works per scene, so we want to store/un-store properties on the current
    # scene.
    if prop_full_path.startswith("bpy.data.scenes[") and "]." in prop_full_path:
        prefix_index = prop_full_path.index("].")
        return f"bpy.context.scene.{prop_full_path[prefix_index + len('].'):]}"
    else:
        return prop_full_path


def split_prop_to_path_and_name(prop_path: str) -> typing.Tuple[str, str]:
    """Splits property path on the last dot

    E.g. bpy.context.scene.render.engine -> bpy.context.scene.render, engine
    """
    if "." not in prop_path and "[" not in prop_path:
        return "", prop_path
    last_dot_index = prop_path.rfind(".")
    last_bracket_index = prop_path.rfind("[")

    # e.g. "bpy.context.scene.render.engine"
    if last_dot_index > last_bracket_index:
        prop_path, prop_name = prop_path.rsplit(".", 1)
        return prop_path, prop_name

    # e.g. "bpy.data.object['Cube']['custom_prop']
    prop_path, prop_name = prop_path[:last_bracket_index], prop_path[last_bracket_index:]
    # Strip brackets and quotation marks
    assert len(prop_name) > 4
    assert prop_name[0] == "[" and prop_name[-1] == "]"
    assert prop_name[1] in ("'", "\"") and prop_name[-2] in ("'", "\"")
    prop_name = prop_name[2:-2]
    return prop_path, prop_name


def get_property_name_from_data_path(data_path: str) -> str:
    """Returns name of the property from the given 'data_path' string.

    If property doesn't exist it returns empty string. If property uses 'default_value', then
    we try to get the name from it. Otherwise we check 'rna_type.properties' for the name.

    If property exists but we can't figure out the name, we return fallback - capitalized last part
    of the property path.
    """
    data, prop = split_prop_to_path_and_name(data_path)
    if data is None or prop is None:
        return ""

    fallback_name = prop.capitalize().replace("_", " ")
    if prop == "default_value":
        return getattr(data, "name", fallback_name)

    return (
        data.rna_type.properties[prop].name
        if hasattr(data, prop) and hasattr(data, "rna_type")
        else fallback_name
    )


def infer_initial_prop_container_and_path(
    prop: str, rset_context: 'renderset_context.RendersetContext'
) -> typing.Tuple[str, bpy.types.bpy_struct, str]:
    """Infers the prop_path, initial_prop_container and initial_prop_path for a given property.

    E.g.:
    - bpy.context.scene.camera -> ("bpy", bpy, "context.scene.camera")
    - self.include_in_render_all -> ("self", rset_context, "self.include_in_render_all")
    """
    # This would ideally be in sync_overrides, but we need access to RendersetContext, to have
    # it as initial_prop_container
    if prop.startswith("bpy."):
        prop_path = prop.removeprefix("bpy.")
        initial_prop_container = bpy
        initial_prop_path = "bpy"
    elif prop.startswith("self."):
        prop_path = prop.removeprefix("self.")
        initial_prop_container = rset_context
        initial_prop_path = "self"
    else:
        raise ValueError(f"Invalid prop key: {prop}")

    return prop_path, initial_prop_container, initial_prop_path


def get_human_readable_property_name(
    prop: str, rset_context: 'renderset_context.RendersetContext'
) -> str:
    """Returns a human-readable name for the prop, replacing UUIDs or indices with datablock names."""
    user_friendly_prop = resolve_uuids(*infer_initial_prop_container_and_path(prop, rset_context))

    if user_friendly_prop is not None:
        # In case there are brackets, we want to display them, so it is possible to see
        # to what datablock and possibly index of some property the property points to.
        # e. g. bpy.data.collections['Name'].children -> collections['Name'] Children
        start = user_friendly_prop.find("[")
        end = user_friendly_prop[:-1].find("]")
        if start != -1 and end != -1:
            return f"{user_friendly_prop[start:end + 1]} {get_property_name_from_data_path(prop)}"

        return get_property_name_from_data_path(prop)

    return prop


def _convert_indexing_name(
    prop_container: bpy.types.bpy_struct, prop_name: str, writable_context: bool
) -> typing.Tuple[typing.Optional[bpy.types.bpy_struct], typing.Optional[str]]:
    """Converts indexing from property path to representation with UUIDs and property object

    Returns property object and its UUID representation in the property path.

    E.g.
        obj.material_slots, "0" -> obj.material_slots[0], "RSET_INDEX-0"
        bpy.data.objects, "Cube" -> bpy.data.objects["Cube"], "RSET_UUID-cd5b99c3ac9e4cd69ccb7e99f1f78daa"
        obj, "custom_prop" -> obj["custom_prop"], "custom_prop"
    """
    # Numeric indexing like bpy.data.objects[0] or ...node.inputs[1].default_value
    if prop_name.isdecimal():
        assert isinstance(prop_container, bpy.types.bpy_prop_collection)
        prop_index = int(prop_name)
        return prop_container[prop_index], f"{serialize_utils.RSET_INDEX_PREFIX}{prop_name}"

    # Indexing with string like bpy.data.objects["Cube"] or obj["my_prop"]
    # Remove quotation marks, e.g. "'Scene.001'" -> "Scene.001"
    assert len(prop_name) > 2
    assert prop_name[0] in ("'", "\"") and prop_name[0] == prop_name[-1]
    prop_name = prop_name[1:-1]
    if prop_name not in prop_container:
        logger.warning(
            f"Couldn't convert property path! '{prop_container}' doesn't contain "
            f"indexed '{prop_name}' prop!"
        )
        return None, None

    if not isinstance(prop_container, bpy.types.bpy_prop_collection):
        # Brackets here mean a custom property of the datablock,
        # e.g. # bpy.data.objects["Cube"]["my_prop"]
        return prop_container[prop_name], prop_name
    else:
        # Convert datablock name to UUID if possible
        if not isinstance(prop_container[prop_name], bpy.types.ID):
            logger.debug(f"Property '{prop_name}' is not and ID datablock, cannot get it's uuid!")
            return None, None
        indexed_prop_uuid = serialize_utils.try_get_uuid_from_datablock(
            prop_container[prop_name], writable_context=writable_context
        )

        if indexed_prop_uuid is None:
            logger.warning(f"Failed to ensure UUID for {prop_container[prop_name]}!")
            return None, None

        return prop_container[prop_name], f"{serialize_utils.RSET_UUID_PREFIX}{indexed_prop_uuid}"


def _convert_prop_path(
    prop_path: str,
    writable_context: bool,
    initial_prop_container: typing.Optional[bpy.types.bpy_struct] = None,
    initial_prop_path: typing.Optional[str] = None,
) -> typing.Tuple[
    typing.Optional[str], typing.Optional[str], typing.Optional[bpy.types.bpy_struct]
]:
    """Converts property path to native Blender Python path, path with UUIDs and property object

    Given property path may or may not already contain some UUIDs.
    """
    MAX_DELIMITER_INDEX = 1_000_000

    if initial_prop_container is None or initial_prop_path is None:
        assert initial_prop_container is None and initial_prop_path is None
        initial_prop_container = bpy
        initial_prop_path = "bpy"
        assert prop_path.startswith("bpy.")
        prop_path = prop_path.removeprefix("bpy.")

    prop_container = initial_prop_container
    # Path like it would appear in Blender, it doesn't contain any UUID
    native_prop_path = initial_prop_path
    # Path where all datablocks are represented by UUIDs
    uuid_prop_path = initial_prop_path

    # Examples are for the input "bpy.data.scenes['Scene.001'].render"
    while len(prop_path) > 0:
        dot_index = prop_path.index(".") if "." in prop_path else MAX_DELIMITER_INDEX
        bracket_index = prop_path.index("[") if "[" in prop_path else MAX_DELIMITER_INDEX

        # Index into property array, e.g. prop_path = "['Scene.001'].render"
        if prop_path[0] == "[":
            assert "]" in prop_path
            prop_path = prop_path[1:]  # Remove "["
            prop_name, prop_path = prop_path.split("]", 1)
            prop_path = prop_path.lstrip(".")

            prop_container, uuid_prop_name = _convert_indexing_name(
                prop_container, prop_name, writable_context
            )
            if uuid_prop_name is None or prop_container is None:
                return None, None, None
            uuid_prop_path += f".{uuid_prop_name}"
            native_prop_path += f"[{prop_name}]"
            continue

        # The last property of the path, e.g. prop_path = "render"
        if dot_index == bracket_index == MAX_DELIMITER_INDEX:
            next_prop, prop_path = prop_path, ""
        # Next property is split by the dot, e.g. prop_path = "data.scenes['Scene.001'].render"
        elif dot_index < bracket_index:
            next_prop, prop_path = prop_path.split(".", 1)
        # Next property is split by the bracket, e.g. prop_path = "scenes['Scene.001'].render"
        else:
            next_prop, prop_path = prop_path.split("[", 1)
            prop_path = "[" + prop_path

        if next_prop.startswith(serialize_utils.RSET_UUID_PREFIX):
            next_prop_uuid = next_prop[len(serialize_utils.RSET_UUID_PREFIX) :]
            collection = None
            if isinstance(prop_container, bpy.types.bpy_prop_collection):
                collection = prop_container
            prop_with_uuid = serialize_utils.try_get_datablock_from_uuid(next_prop_uuid, collection)
            if prop_with_uuid is None:
                logger.debug(
                    f"Couldn't get parent of '{prop_path}' property! "
                    f"Couldn't find datablock with UUID '{next_prop_uuid}'!"
                )
                return None, None, None
            prop_container = prop_with_uuid
            uuid_prop_path += f".{next_prop}"
            if hasattr(prop_with_uuid, "name_full"):
                native_prop_path += f"[{prop_with_uuid.name_full}]"
            else:
                assert hasattr(prop_with_uuid, "name")
                native_prop_path += f"[{prop_with_uuid.name}]"
        elif next_prop.startswith(serialize_utils.RSET_INDEX_PREFIX):
            next_prop_index = next_prop[len(serialize_utils.RSET_INDEX_PREFIX) :]
            prop_container = serialize_utils.get_indexed_prop(next_prop_index, prop_container)
            if prop_container is None:
                logger.debug(
                    f"Couldn't get parent of '{prop_path}' property! "
                    f"Couldn't find property with index '{next_prop_index}'!"
                )
                return None, None, None
            uuid_prop_path += f".{next_prop}"
            native_prop_path += f"[{next_prop_index}]"
        else:
            if hasattr(prop_container, next_prop):
                native_prop_path += f".{next_prop}"
                prop_container = getattr(prop_container, next_prop)
            elif (
                serialize_utils.can_store_custom_property(prop_container)
                and next_prop in prop_container
            ):
                native_prop_path += f"[{next_prop}]"
                prop_container = prop_container[next_prop]
            else:
                logger.debug(
                    f"Couldn't get parent of '{prop_path}' property! "
                    f"'{prop_container}' doesn't contain '{next_prop}' attribute!"
                )
                return None, None, None

            uuid_prop_path += f".{next_prop}"

    return native_prop_path, uuid_prop_path, prop_container


def resolve_uuids(
    prop_path: str,
    initial_prop_container: typing.Optional[bpy.types.bpy_struct] = None,
    initial_prop_path: typing.Optional[str] = None,
) -> typing.Optional[str]:
    """Resolves UUIDs and prefixed indices in the property path to native Blender Python path

    Example: "bpy.data.objects.RSET_UUID-cd5b99c3ac9e4cd69ccb7e99f1f78daa.location.RSET_INDEX-0" -> "bpy.data.objects['Cube'].location[0]"
    """
    return _convert_prop_path(
        prop_path,
        writable_context=False,
        initial_prop_container=initial_prop_container,
        initial_prop_path=initial_prop_path,
    )[0]


def expand_uuids(
    prop_path: str,
    writable_context: bool = True,
    initial_prop_container: typing.Optional[bpy.types.bpy_struct] = None,
    initial_prop_path: typing.Optional[str] = None,
) -> typing.Optional[str]:
    """Replaces datablock names in the property path with their UUIDs and add prefix indices

    Example: "bpy.data.objects['Cube'].location[0]" -> "bpy.data.objects.RSET_UUID-cd5b99c3ac9e4cd69ccb7e99f1f78daa.location.RSET_INDEX-0"

    writable_context: Use False if this method is called from a context where writing into
    properties is forbidden e.g. right-click menu. If False, this will replace datablock name with
    UUID only if the datablock already has up-to-date UUID, otherwise a mock-up constant uuid is
    used. If True, this will assign UUIDs to datablocks that don't have them yet.
    """
    return _convert_prop_path(
        prop_path,
        writable_context=writable_context,
        initial_prop_container=initial_prop_container,
        initial_prop_path=initial_prop_path,
    )[1]


def evaluate_prop_path(
    prop_path: str,
    initial_prop_container: typing.Optional[bpy.types.bpy_struct] = None,
    initial_prop_path: typing.Optional[str] = None,
) -> typing.Optional[bpy.types.bpy_struct]:
    """Returns Blender object defined by 'prop_path'

    E.g. "bpy.context.scene.render" -> render property from bpy.context.scene
    or "bpy.data.scenes['Scene.001'].render" -> render property from bpy.data.scenes['Scene.001']
    (result of both of these examples is an object of type RenderSettings, but they are different
    instances if bpy.context.scene is not Scene.001)
    """
    return _convert_prop_path(
        prop_path,
        writable_context=False,
        initial_prop_container=initial_prop_container,
        initial_prop_path=initial_prop_path,
    )[2]


def can_store_property(prop_path: str, verbose: bool = False) -> bool:
    # If prop_path is path in the scene, we expect context-based scene property path
    # e.g. 'bpy.context.scene.render.engine' which is returned by get_prop_full_path().
    assert not prop_path.startswith("bpy.data.scenes[")

    if not prop_path.startswith("bpy."):
        if verbose:
            logger.error("Can't store properties outside of bpy!")
        return False

    # Don't allow storing renderset properties
    if "renderset" in prop_path or "render_set" in prop_path:
        if verbose:
            logger.error("Can't store renderset's internal properties!")
        return False

    # Check if property can be obtained
    prop_parent_path, prop_name = split_prop_to_path_and_name(prop_path)
    prop_parent = evaluate_prop_path(prop_parent_path)
    if prop_parent is None or prop_name is None:
        if verbose:
            logger.error("Can't obtain value of parent property!")
        return False

    # Storing names doesn't make sense, user would most likely expect to store the whole datablock,
    # not just its name.
    if prop_name in {"name", "name_full"}:
        if verbose:
            logger.error("Can't store name properties!")
        return False

    prop_value = serialize_utils.get_serializable_property_value(
        prop_parent, prop_name, writable_context=False
    )
    if prop_value is None:
        if verbose:
            logger.error("Can't obtain value of the property or it has unsupported type!")
        return False

    # Don't allow storing visibility restriction toggles of single datablock, we store/not store
    # them for all based on toggles in the preferences
    BPY_TYPE_TO_RESTRICTION_TOGGLES = {
        bpy.types.Object: ("hide_render", "hide_select", "hide_viewport"),
        bpy.types.Collection: ("hide_render", "hide_select", "hide_viewport"),
        bpy.types.LayerCollection: ("exclude", "holdout", "indirect_only", "hide_viewport"),
    }
    for bpy_type, restriction_toggles in BPY_TYPE_TO_RESTRICTION_TOGGLES.items():
        if isinstance(prop_parent, bpy_type) and prop_name in restriction_toggles:
            if verbose:
                logger.error(
                    f"Can't store visibility restrictions of single {bpy_type}! "
                    "You can set in Preferences if they're always stored or not!"
                )
            return False

    return True


def redirect_obj_prop_path_by_name(prop_path: str, obj_name: str) -> str:
    """Replaces the prefix of a valid object property path with 'bpy.data.objects["obj_name"]'

    Expects a property path in a form of 'bpy.data.objects["Name"]...' or 'bpy.context.scene.objects["Name"]...'

    Returns a redirected property path:
    E.g. 'bpy.data.objects["Cube"].location' -> 'bpy.data.objects["Sphere"].location'
    'bpy.context.scene.objects["Cube"].location' -> 'bpy.data.objects["Sphere"].location'
    """
    # Only the start of the string should be replaced as the regex starts with '^', but let's make sure
    EXPECTED_NUM_REPLACED = 1
    new_path, num_replaced = re.subn(
        BPY_OBJECT_PROP_PATH_PREFIX_REGEX,
        f"bpy.data.objects['{obj_name}']",
        prop_path,
        count=EXPECTED_NUM_REPLACED,
    )
    if num_replaced != EXPECTED_NUM_REPLACED:
        raise ValueError(
            f"Property path '{prop_path}' doesn't start with 'bpy.data.objects['Name']' or 'bpy.context.scene.objects['Name']'!"
        )

    return new_path


def is_property_stored(context: bpy.types.Context, prop_path: str) -> bool:
    """Checks if a given 'prop_path' is a stored property."""
    if len(context.scene.renderset_contexts) == 0:
        return False

    # Any renderset context will do, we just need to check if the property is stored in them
    rset_context = context.scene.renderset_contexts[0]
    expanded_prop_path = expand_uuids(prop_path, writable_context=False)

    if expanded_prop_path is None:
        return False
    return expanded_prop_path in serialize_utils.flatten_dict(rset_context.stored_props_dict)


def draw_renderset_context_menu_items(self, context: bpy.types.Context) -> None:
    """Given property right-click 'context', it adds renderset operator to the menu"""
    prop_full_path = get_prop_full_path(context)
    if prop_full_path is None:
        return

    if not can_store_property(prop_full_path):
        return

    if len(context.scene.renderset_contexts) == 0:
        return

    # Any renderset context will do, we just need to check if the property is stored in them
    rset_context = context.scene.renderset_contexts[0]
    expanded_prop_path = expand_uuids(prop_full_path, writable_context=False)
    if expanded_prop_path is None:
        return

    is_stored = expanded_prop_path in serialize_utils.flatten_dict(rset_context.stored_props_dict)

    self.layout.separator()
    self.layout.operator(
        WM_OT_renderset_toggle_property_override.bl_idname,
        text="Remove Property" if is_stored else "Store Property",
        icon_value=polib.ui_bpy.icon_manager.get_icon_id("logo_renderset"),
    ).mode = (
        PropertyOverrideAction.REMOVE.value if is_stored else PropertyOverrideAction.ADD.value
    )

    if not (
        len(context.selected_objects) >= 2
        and (re.match(BPY_OBJECT_PROP_PATH_PREFIX_REGEX, prop_full_path))
    ):
        return

    stored_found = False
    not_stored_found = False

    for obj in context.selected_objects:
        if stored_found and not_stored_found:
            break
        updated_prop_path = redirect_obj_prop_path_by_name(prop_full_path, obj.name)
        try:
            # Some objects might not have the property
            expanded_prop_path = expand_uuids(updated_prop_path, writable_context=False)
        except:
            continue
        is_stored = expanded_prop_path in serialize_utils.flatten_dict(
            rset_context.stored_props_dict
        )
        stored_found = stored_found or is_stored
        not_stored_found = not_stored_found or not is_stored

    if not_stored_found:
        self.layout.operator(
            WM_OT_renderset_toggle_selected_objects_property_override.bl_idname,
            text=("Store Property for Selected Objects"),
            icon_value=polib.ui_bpy.icon_manager.get_icon_id("logo_renderset"),
        ).mode = PropertyOverrideAction.ADD.value
    if stored_found:
        self.layout.operator(
            WM_OT_renderset_toggle_selected_objects_property_override.bl_idname,
            text=("Remove Property for Selected Objects"),
            icon_value=polib.ui_bpy.icon_manager.get_icon_id("logo_renderset"),
        ).mode = PropertyOverrideAction.REMOVE.value


@polib.log_helpers_bpy.logged_operator
class WM_OT_renderset_toggle_property_override(bpy.types.Operator):
    """This operator is added to the right-click context menu of properties in the UI. It currently
    works only on properties starting with bpy.context.scene. We can easily extend it to other
    int, float, str and array properties (like color). The problem is with properties of datablocks
    from collections (like object visibility) as we would need to assign UUIDs to those datablocks
    (easy) and have a custom functions that would iterate over specific collections and set there
    the stored properties (difficult). E.g. Iterate over material slots on all objects and set there
    stored material.
    """

    bl_idname = "renderset.toggle_property_override"
    bl_label = "Add/Remove property from Stored Properties in renderset context"

    mode: bpy.props.EnumProperty(
        name="Mode of Additional Properties",
        description="Defines if selected property should be added or removed from stored properties",
        items=(
            (PropertyOverrideAction.ADD.value, "Add", "Add property to stored"),
            (PropertyOverrideAction.REMOVE.value, "Remove", "Remove property from stored"),
        ),
    )

    @classmethod
    def description(
        cls, context: bpy.types.Context, properties: bpy.types.OperatorProperties
    ) -> str:
        current_mode = getattr(properties, "mode", None)
        if current_mode == PropertyOverrideAction.ADD.value:
            return "Property will be remembered per renderset context"
        elif current_mode == PropertyOverrideAction.REMOVE.value:
            return "Property will become global and renderset contexts will not remember it"
        else:
            raise ValueError(f"Unknown mode: {properties.mode}!")

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        if len(context.scene.renderset_contexts) == 0:
            return False
        prop_full_path = get_prop_full_path(context)
        return prop_full_path is not None and can_store_property(prop_full_path, verbose=True)

    def execute(self, context: bpy.types.Context):
        prop_full_path = get_prop_full_path(context)
        assert prop_full_path is not None

        for rset_context in context.scene.renderset_contexts:
            if self.mode == PropertyOverrideAction.ADD.value:
                rset_context.add_override(prop_full_path, action_store=True)
                logger.info(
                    f"Property '{prop_full_path}' is now stored in '{rset_context.custom_name}'"
                )
            elif self.mode == PropertyOverrideAction.REMOVE.value:
                rset_context.add_override(prop_full_path, action_store=False)
                logger.info(
                    f"Removed storing property '{prop_full_path}' in '{rset_context.custom_name}'"
                )
            else:
                raise ValueError(f"Unknown mode: {self.mode}!")

        return {'FINISHED'}


MODULE_CLASSES.append(WM_OT_renderset_toggle_property_override)


class WM_OT_renderset_toggle_selected_objects_property_override(bpy.types.Operator):
    bl_idname = "renderset.toggle_selected_objects_property_override"
    bl_label = (
        "Add/Remove property from Stored Properties in renderset context for each selected object"
    )

    mode: bpy.props.EnumProperty(
        name="Mode of Additional Properties",
        description="Defines if selected property should be added or removed from stored properties",
        items=(
            (PropertyOverrideAction.ADD.value, "Add", "Add property to stored"),
            (PropertyOverrideAction.REMOVE.value, "Remove", "Remove property from stored"),
        ),
    )

    @classmethod
    def description(
        cls, context: bpy.types.Context, properties: bpy.types.OperatorProperties
    ) -> str:
        current_mode = getattr(properties, "mode", None)
        if current_mode == PropertyOverrideAction.ADD.value:
            return "Property will be remembered for all selected objects per renderset context"
        elif current_mode == PropertyOverrideAction.REMOVE.value:
            return "Property will become global for all selected objects and renderset contexts will not remember it"
        else:
            raise ValueError(f"Unknown mode: {properties.mode}!")

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        prop_full_path = get_prop_full_path(context)
        return (
            prop_full_path is not None
            and len(context.scene.renderset_contexts) > 0
            and can_store_property(prop_full_path)
            and (
                prop_full_path.startswith("bpy.data.objects")
                or prop_full_path.startswith("bpy.context.scene.objects")
            )
        )

    def execute(self, context: bpy.types.Context):
        prop_full_path = get_prop_full_path(context)
        assert prop_full_path is not None

        current_context = context.scene.renderset_contexts[0]
        for obj in context.selected_objects:
            updated_prop_path = redirect_obj_prop_path_by_name(prop_full_path, obj.name)
            try:
                # Some objects might not have the property
                expanded_prop_path = expand_uuids(updated_prop_path, writable_context=False)
            except:
                continue
            if expanded_prop_path is None:
                continue
            is_stored = expanded_prop_path in serialize_utils.flatten_dict(
                current_context.stored_props_dict
            )

            # Only store properties that are not stored yet or remove properties that are stored
            if (self.mode == PropertyOverrideAction.REMOVE.value and not is_stored) or (
                self.mode == PropertyOverrideAction.ADD.value and is_stored
            ):
                continue

            for rset_context in context.scene.renderset_contexts:
                if self.mode == PropertyOverrideAction.ADD.value:
                    rset_context.add_override(updated_prop_path, action_store=True)
                elif self.mode == PropertyOverrideAction.REMOVE.value:
                    rset_context.add_override(updated_prop_path, action_store=False)
                else:
                    raise ValueError(f"Unknown mode: {self.mode}!")

        return {'FINISHED'}


MODULE_CLASSES.append(WM_OT_renderset_toggle_selected_objects_property_override)


def is_render_region_stored(context: bpy.types.Context) -> bool:
    """Returns True if all render region properties are stored."""
    return all(is_property_stored(context, prop) for prop in RENDER_REGION_PROPS)


def clear_storing_render_region(context: bpy.types.Context) -> None:
    """Clears storing render region properties in renderset contexts."""
    assert len(context.scene.renderset_contexts) > 0
    for prop in RENDER_REGION_PROPS:
        if is_property_stored(context, prop):
            context.scene.renderset_contexts[0].remove_override(prop)


@polib.log_helpers_bpy.logged_operator
class ToggleStoreCameraRenderRegion(bpy.types.Operator):
    bl_idname = "renderset.toggle_store_camera_render_region"
    bl_description = "Switch between storing camera render region and its relevant properties in renderset contexts"
    bl_label = "Store Camera Render Region"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return (
            context.scene.camera is not None
            and len(context.scene.renderset_contexts) > 0
            and not context.scene.renderset_multi_edit_mode
        )

    def execute(self, context: bpy.types.Context):
        # Asserted by poll
        assert len(context.scene.renderset_contexts) > 0

        # If any of the properties aren't stored, we try to store them again
        should_store = not is_render_region_stored(context)

        for prop in RENDER_REGION_PROPS:
            is_stored = is_property_stored(context, prop)
            for rset_context in context.scene.renderset_contexts:
                if should_store != is_stored:
                    rset_context.add_override(prop, should_store)

        return {'FINISHED'}


MODULE_CLASSES.append(ToggleStoreCameraRenderRegion)


def draw_renderset_object_menu(self, context: bpy.types.Context) -> None:
    if context.active_object is None:
        return

    if context.active_object.type != 'CAMERA':
        return

    is_region_stored = is_render_region_stored(context)
    self.layout.separator()
    self.layout.operator(
        ToggleStoreCameraRenderRegion.bl_idname,
        icon_value=polib.ui_bpy.icon_manager.get_icon_id("logo_renderset"),
        text=(
            "Store Camera Render Region"
            if not is_region_stored
            else "Remove Storing Camera Render Region"
        ),
    )


def register():
    for cls in MODULE_CLASSES:
        bpy.utils.register_class(cls)

    # Taken from example in: https://docs.blender.org/api/3.3/bpy.types.Menu.html#extending-the-button-context-menu
    # Most online sources use WM_MT_button_context() menu but that was deprecated in Blender 3.3:
    # https://wiki.blender.org/wiki/Reference/Release_Notes/3.3/Python_API
    bpy.types.UI_MT_button_context_menu.append(draw_renderset_context_menu_items)
    bpy.types.VIEW3D_MT_object_context_menu.append(draw_renderset_object_menu)


def unregister():
    bpy.types.VIEW3D_MT_object_context_menu.remove(draw_renderset_object_menu)
    bpy.types.UI_MT_button_context_menu.remove(draw_renderset_context_menu_items)
    for cls in reversed(MODULE_CLASSES):
        bpy.utils.unregister_class(cls)
