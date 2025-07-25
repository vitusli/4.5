import bpy
from bpy.props import StringProperty
import os
from ... utils.registration import get_path, get_prefs
from ... utils.system import get_update_files, remove_folder

class RemoveUpdate(bpy.types.Operator):
    bl_idname = "machin3.remove_decalmachine_update"
    bl_label = "MACHIN3: Remove Update"
    bl_description = "I changed my mind, I don't want to install this Update"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return os.path.exists(os.path.join(get_path(), '_update'))

    def execute(self, context):
        update_path = os.path.join(get_path(), '_update')
        remove_folder(update_path)

        get_prefs().update_msg = ''
        
        return {'FINISHED'}

class UseFoundUpdate(bpy.types.Operator):
    bl_idname = "machin3.use_decalmachine_update"
    bl_label = "MACHIN3: Use Update"
    bl_options = {'REGISTER', 'UNDO'}

    path: StringProperty()
    tail: StringProperty()

    @classmethod
    def description(cls, context, properties):
        return f"Install decalmachine {properties.tail} from {properties.path}"

    def execute(self, context):
        if self.path and self.tail:
            get_prefs().update_path = self.path

        return {'FINISHED'}

class ReScanUpdates(bpy.types.Operator):
    bl_idname = "machin3.rescan_decalmachine_updates"
    bl_label = "MACHIN3: Re-Scan Updates"
    bl_description = "Re-Scan Updates"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        get_update_files(force=True)

        return {'FINISHED'}
