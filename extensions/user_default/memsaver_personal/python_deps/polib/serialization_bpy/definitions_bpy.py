# copyright (c) 2018- polygoniq xyz s.r.o.

from . import io_bpy
from . import core_bpy
from . import errors
import typing
import dataclasses


class Savable:
    """Base class for objects that can be saved and loaded from a config file.

    This class provides a simple interface for saving and loading it's state to a disk.
    It requires the class to implement `_serialize` and `_deserialize` methods used to convert
    the object to and from a json-compatible dictionary.

    For saving and loading `bpy.types.PropertyGroup` objects, use this in combination
    with `serializable_class` decorator and `Serialize()` wrapper.

    In case of nested serialized classes, only the top-level class should inherit from this class.

    Example:
    ```
        @serializable_class
        class MyClass(bpy.types.PropertyGroup, Savable):
            my_int_property: Serialize(
                bpy.props.IntProperty(name="My Int")
            )

            @property
            def addon_name(self) -> str:
                return "my_addon"

            @property
            def config_name(self) -> str:
                return "my_config"

            @property
            def save_version(self) -> int:
                return 1
    ```
    """

    @property
    def addon_name(self) -> str:
        raise NotImplementedError("The class must implement the 'addon_name' property")

    @property
    def config_name(self) -> str:
        raise NotImplementedError("The class must implement the 'config_name' property")

    @property
    def save_version(self) -> int:
        """Version of the saved file format.

        Used to check if the loaded config is compatible with the current version of the class.
        The version should be incremented if the class is changed in any way.
        """
        raise NotImplementedError("The class must implement the 'save_version' property")

    def save(self) -> None:
        if not hasattr(self, "_serialize"):
            raise AttributeError("The class must implement a '_serialize' method")

        data = self._serialize()  # type: ignore
        versioned_data = {
            "version": self.save_version,
            "data": data,
        }
        io_bpy.save_config(self.addon_name, self.config_name, versioned_data)

    def load(self) -> None:
        if not hasattr(self, "_deserialize"):
            raise AttributeError("The class must have a '_deserialize' method")

        # load and deserialize the data into a dictionary
        if not io_bpy.has_config(self.addon_name, self.config_name):
            raise FileNotFoundError(f"Config file for {self.config_name} not found")

        versioned_data = io_bpy.load_config(self.addon_name, self.config_name)
        if "version" not in versioned_data:
            raise errors.InvalidConfigError("Version not found in the config")
        loaded_version = versioned_data["version"]
        if not isinstance(loaded_version, int):
            raise errors.InvalidConfigError(
                f"Invalid version format. Expected int, got {type(loaded_version)}"
            )
        if loaded_version > self.save_version:
            raise errors.UnsupportedVersionError(
                f"Version of the loaded config ({loaded_version}) is higher than the currently "
                f"supported version ({self.save_version})"
            )

        if "data" not in versioned_data:
            raise errors.InvalidConfigError("Data not found in the config")
        if not isinstance(versioned_data["data"], dict):
            raise errors.InvalidConfigError("Data must be a dictionary")
        # inject the data into the target object
        self._deserialize(versioned_data["data"])  # type: ignore


@dataclasses.dataclass
class SerializedPropertyInfo:
    """Annotation object to mark a `bpy.prop` as serializable."""

    serialization_type: typing.Type
    bpy_prop: typing.Any


# Name of the bpy property: serialization type
PROP_TO_SIMPLE_SERIALIZATION_TYPE_MAP: typing.Dict[str, typing.Type] = {
    "BoolProperty": bool,
    "FloatProperty": float,
    "IntProperty": int,
    "StringProperty": str,
}

# Name of the bpy vector property: item serialization type
PROP_TO_SERIALIZATION_VECTOR_MAP: typing.Dict[str, typing.Type] = {
    "BoolVectorProperty": bool,
    "FloatVectorProperty": float,
    "IntVectorProperty": int,
}


def Serialize(
    prop: typing.Any,
) -> SerializedPropertyInfo:
    """Annotation wrapper to mark a `bpy.prop` as serializable for `serializable_class` decorator.

    All properties of a `bpy.types.PropertyGroup` marked with this annotation will be serialized.
    The class must be decorated with `serializable_class` decorator
    to generate a valid `bpy.types.PropertyGroup` class!

    Example usage:
    ```
        @serializable_class
        class MyPropertyGroup(bpy.types.PropertyGroup):
            my_int_property: Serialize(
                bpy.props.IntProperty(name="My Int")
            )
    """
    if not hasattr(prop, "function") or not hasattr(prop, "keywords"):
        raise TypeError("Property must be a bpy.props property")

    prop_name = prop.function.__name__
    if prop_name in PROP_TO_SIMPLE_SERIALIZATION_TYPE_MAP:
        # Simple property type
        return SerializedPropertyInfo(
            PROP_TO_SIMPLE_SERIALIZATION_TYPE_MAP[prop_name],
            prop,
        )
    if prop_name in PROP_TO_SERIALIZATION_VECTOR_MAP:
        # Vector property type
        vector_type = PROP_TO_SERIALIZATION_VECTOR_MAP[prop_name]
        assert "size" in prop.keywords, "VectorProperty must have a 'size' keyword argument"
        vector_size = (
            [prop.keywords["size"]]
            if isinstance(prop.keywords["size"], int)
            else prop.keywords["size"]
        )
        return SerializedPropertyInfo(
            core_bpy.VectorProp[vector_type, vector_size],
            prop,
        )
    if prop_name == "EnumProperty":
        # Enum property type
        if "options" in prop.keywords and 'ENUM_FLAG' in prop.keywords["options"]:
            return SerializedPropertyInfo(
                core_bpy.EnumFlagProp,
                prop,
            )
        return SerializedPropertyInfo(
            str,
            prop,
        )
    if prop_name == "CollectionProperty":
        # Collection/Pointer property type
        assert "type" in prop.keywords, "CollectionProperty must have a 'type' keyword argument"
        return SerializedPropertyInfo(
            core_bpy.CollectionProp[prop.keywords["type"]],
            prop,
        )
    if prop_name == "PointerProperty":
        # Pointer property type
        assert "type" in prop.keywords, "PointerProperty must have a 'type' keyword argument"
        return SerializedPropertyInfo(
            core_bpy.PointerProp[prop.keywords["type"]],
            prop,
        )

    raise ValueError(f"Unsupported property type: {prop_name}")


def serializable_class(cls):
    """Decorator to extend a `bpy.types.PropertyGroup` class with serialization api.

    - Use this decorator in combination with `Serialize()` wrapper to mark properties as serializable.
    - Use this in combination with `Savable` class to add saving and loading methods.

    Note: This decorator can be used in combination with `Savable` class, but does not require it.
    This allows to create nested `bpy.types.PropertyGroup` classes that are serialized into one
    config file (only the top-level class should inherit from `Savable`).

    Example usage with nested property groups:
    ```
        @serializable_class
        class MySubPropertyGroup(bpy.types.PropertyGroup):
            my_int_property: Serialize(
                bpy.props.IntProperty(name="My Int")
            )

        @serializable_class
        class MyPropertyGroup(bpy.types.PropertyGroup):
            my_sub_property_group: Serialize(
                bpy.props.PointerProperty(type=MySubPropertyGroup)
            )

            @property
            def addon_name(self) -> str:
                return "my_addon"

            @property
            def config_name(self) -> str:
                return "my_config"

            @property
            def save_version(self) -> int:
                return 1
    ```
    """

    # Add serialization info to the class
    cls._serialized_properties = {}
    for prop_name, annotation in cls.__annotations__.items():
        if isinstance(annotation, SerializedPropertyInfo):
            # Store serialization info about the property
            cls._serialized_properties[prop_name] = annotation.serialization_type
            # "Revert" the annotation to the original bpy.props property annotation
            # so bpy can generate properties
            cls.__annotations__[prop_name] = annotation.bpy_prop

    # Add serialization methods to the class
    cls._serialize = core_bpy.serialize_instance
    cls._deserialize = core_bpy.deserialize_instance

    return cls
