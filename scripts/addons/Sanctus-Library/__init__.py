''' 
Codebase Structure:
    All asset files can be found under lib/
    t3dn_bip ->         is an external image-loading library which was adepted so that loaded images can be modified. This is used to procedurally edit images after they are loaded
    auto_load ->        has many responsibilities but it is mainly used to clean up the addon registration process. Instead of manually registering / unregistering classes, they only need to be tagged
                        the basic tag is @al.register but more specific tags exist like @al.register_operator
                        auto_load also changes how properties work. Instead of them being annotated values, properties using auto_load are descriptors. Accessing a property returns the property itself
                        and getting the value of the property is done by either "calling" it (prop()) or accessing its value attribute (prop.value) which also has a setter
                        auto_load also includes UI functionality which is a wrapper for calling methods on instances of bpy.types.UILayout
    developer_tools ->  are scripts that are not relevant to the addon user but make it easier to manage the large library.

    The addon basically only has two features: library management and a baking tool. Most of the code concerning the baking tool is inside the `baking` module
    The library management is split up into the files in the main `Sanctus-Library` module. The most important parts of it are `library_manager.py`, `filters.py`, `panel_ui.py`, `panel_ui_secions.py` and `preferences.py`
    Apart from the baking operators, all operators are inside the `operators` module in different files, split up by context.
    The rest of the files in the main module are utility files which contain functions for performing specific operations

Library Structure:
    The directories within the lib/ folder are how the library is also being split up. At the first level are the "asset classes". Some of them like `decal_utils` and `icons` are for internal use only, 
    the rest contains the assets of the library. All of the subsequent levels are asset categories and appear as such in the addon UI. When the addon is registered, the library is being built,
    meaning that all of the files within are being looked at and from there, the python representation of the library is being built. All of the code about that can be found in the `library_manager.py` file.
    First, every single file is being collected in a `RawFileStructure` object which is a type of dict. From there, all asset objects are being generated. Assets are one or multiple files on disk with the same name.
    There are different variations of what an asset can be:
        1. A single .png file -> this is a sticker asset
        2. A single .blend file -> this is a blend file asset without thumbnail or meta data. It's only used internally
        3. A .blend, .json and .png file -> this is a blend file asset with thumbnail and some meta data. Meta data is used to filter assets in the addon. For example some materials are only compatible with
                                            either Cycles or Eevee and need to be tagged as such.
        4. A .blend, .json and multiple .png files -> this is like the previous asset but it has different presets which are all stored in the .blend file. This is mainly used for materials. 
    When the library is being generated, the rules above determine the kind of assets being created. 
    Because some assets have presets, AssetInstance objects represent these presets. Even assets without presets can have AssetInstances. They are used to load specific data from the source .blend files.
    If an asset has a .blend file, then that file needs to contain ID objects with the same name as the asset or a variation of that. Depending on the asset class of the object, that ID object inside the source
    file will be a Material, Node Tree or Object...
    Inside Blender, all of the different asset classes and categories get compiled into several EnumProperties which are then used inside the SL panel UI

Building the Addon:
    In the repo root, there is a scipt called `AUTOMATE_BUILD.bat` which builds the addon for shipping as an interactive console program. It removes unecessary files and configures it for users.
    The build goes into the build/ direcory.

Lite Version:
    There is a lite version for this addon which has a couple fewer features and a lot fewer assets. At the moment functionality in the addon is being turned off for lite users by checking if `dev_info.LITE_VERSION` is True.
    This is not terribly secure because anyone could simply edit that value. Perhaps in the future, the build pipeline can also take care of stipping actual code from the addon when building the lite version.

Considerations:
    This addon has a rather large code base. To ensure that it is scalable, "string references" are being avoided such as when calling / drawing operators / panels / menus or drawing properties.
    It is recommended to continue this practice. The auto_load module also supports this. That means using an IDE like VSCode, looking up the usage of an Operator or PropertyGroup can be done by
    checking places where the class name is used. This also makes refactoring a lot easier. Instead of using strings for blender enums, use enum classes. auto_load has a base class called `BStaticEnum`
    which can be turned into enum items that blender understands. Additionally every single enum you can find in the online documentation is available as a enum class under auto_load/enums/. 
    Calling a specific enum turns it into the string representation that blender accepts.
'''


bl_info = {
    "name":         "Sanctus-Library",
    "author":       "Sanctus",
    "version":      (3, 3, 0),
    "blender":      (4, 2, 0),
    "location":     "",
    "description":  "Sanctus Material Library",
    "warning":      "",
    "doc_url":      "http://sanctuslibrary.xyz",
    "category":     "Material",
}

from . import auto_load as al
from . import dev_info


# Configure the addon for auto-load. allows it to import all modules, get addon preferences and more
# Turn on dev_info
al.configure(
    prefix='SANCTUSLIBRARY', 
    package=__package__,
    version_str=f'Addon: {bl_info["version"]}, git:{dev_info.GIT_VERSION}',
    debug=dev_info.DEBUG,
    run_in_background=False,
)

# Import all modules of the addon. This "runs" all the python files in the addon, including the auto-load decorators
al.import_modules(__file__, __package__)

# Set "register" and "unregister" for the addon. auto-load takes care of registering all tagged classes, as well as subscribing to events, adding draw functions to existing layout classes (panels, menus etc)
al.register_addon()
