import bpy
import os

from ... utils.asset import get_import_method_from_library_path
from ... utils.registration import get_path

class AddHyperCursorAssets(bpy.types.Operator):
    bl_idname = "machin3.add_hyper_cursor_assets_path"
    bl_label = "MACHIN3: Add Hyper Cursor Assets Path"
    bl_description = "Add's the HyperCursor Example Assets path to your Library Collection"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        print("Adding Hyper Cursor Assets Path")

        librariesCOL = context.preferences.filepaths.asset_libraries

        bpy.ops.preferences.asset_library_add()

        lib = librariesCOL[-1]
        lib.name = 'HyperCursor Examples'
        lib.path = os.path.join(get_path(), 'assets')
        lib.import_method = 'APPEND'

        return {'FINISHED'}

class SetAssetImportMethodAppend(bpy.types.Operator):
    bl_idname = "machin3.set_asset_import_method_append"
    bl_label = "MACHIN3: Set Asset Import Method Append"
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return context.area and context.area.type == 'FILE_BROWSER' and context.area.ui_type == 'ASSETS'

    @classmethod
    def description(cls, context, properties):
        space = context.space_data

        libpath = space.params.directory.decode('utf-8')
        import_method = space.params.import_method

        if import_method == 'FOLLOW_PREFS':
            import_method = get_import_method_from_library_path(context, libpath)

        if import_method == 'LINK':
            return "\nThe Linked Import Method is not suitable for dropping object assets in HyperCursor.\nHighly recommended to use the Append Import Method instead."

        if import_method == 'APPEND_REUSE':
            return "\nThe Append Reuse Import Method will cause linked object data such as instanced meshes, which is likely not intended.Use with caution."

        return ''

    def execute(self, context):
        space = context.space_data
        space.params.import_method = 'APPEND'

        return {'FINISHED'}
