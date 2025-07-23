import os
import json

import bpy
from bpy.props import StringProperty
from bpy.types import Operator

from ..utils.addon import preferences

# Add this constant for the custom paths file
CUSTOM_PATHS_FILE = os.path.join(os.path.expanduser("~"), "imeshh", "custom_paths.json")


def save_custom_paths():
    """Save custom paths to a JSON file in the default imeshh folder."""
    try:
        prefs = preferences()
        
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(CUSTOM_PATHS_FILE), exist_ok=True)
        
        # Prepare the data to save
        paths_data = {
            "custom_paths": [
                {
                    "path": path.path,
                    "name": path.name,
                    "type": path.type
                }
                for path in prefs.custom_paths
            ],
            "main_paths": {
                "models_path": prefs.models_path,
                "materials_path": prefs.materials_path,
                "geonodes_path": prefs.geonodes_path,
                "fxs_path": prefs.fxs_path,
            }
        }
        
        # Save to file
        with open(CUSTOM_PATHS_FILE, "w", encoding="utf-8") as file:
            json.dump(paths_data, file, indent=2)
            
        return True, "Custom paths saved successfully"
    except Exception as e:
        return False, f"Error saving custom paths: {str(e)}"


def load_custom_paths():
    """Load custom paths from the JSON file."""
    try:
        if not os.path.exists(CUSTOM_PATHS_FILE):
            return False, "No saved custom paths found"
            
        prefs = preferences()
        
        with open(CUSTOM_PATHS_FILE, "r", encoding="utf-8") as file:
            paths_data = json.load(file)
        
        # Clear existing custom paths
        prefs.custom_paths.clear()
        
        # Load custom paths
        for path_data in paths_data.get("custom_paths", []):
            item = prefs.custom_paths.add()
            item.path = path_data.get("path", "")
            item.name = path_data.get("name", "")
            item.type = path_data.get("type", "MODEL")
        
        # Load main paths if they exist
        main_paths = paths_data.get("main_paths", {})
        if main_paths.get("models_path"):
            prefs.models_path = main_paths["models_path"]
        if main_paths.get("materials_path"):
            prefs.materials_path = main_paths["materials_path"]
        if main_paths.get("geonodes_path"):
            prefs.geonodes_path = main_paths["geonodes_path"]
        if main_paths.get("fxs_path"):
            prefs.fxs_path = main_paths["fxs_path"]
        
        # Reset active path index
        prefs.active_path_index = 0
        
        return True, f"Loaded {len(paths_data.get('custom_paths', []))} custom paths"
    except Exception as e:
        return False, f"Error loading custom paths: {str(e)}"


class IMESHH_OT_custom_path_add(Operator):

    bl_label = "Add Custom Path"
    bl_idname = "imeshh.custom_path_add"
    bl_options = {"REGISTER", "INTERNAL"}

    directory: StringProperty(subtype="DIR_PATH")

    @classmethod
    def description(cls, context, properties):
        return "Add a custom asset path"

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        prefs = preferences()

        item = prefs.custom_paths.add()
        prefs.active_path_index = len(prefs.custom_paths) - 1
        item.path = bpy.path.abspath(self.directory)
        item.name = os.path.basename(os.path.dirname(self.directory))

        prefs.local.asset_type = "MODEL"
        self.report({"INFO"}, "Added: Custom asset path")
        return {"FINISHED"}


class IMESHH_OT_custom_path_remove(Operator):

    bl_label = "Remove Custom Path"
    bl_idname = "imeshh.custom_path_remove"
    bl_options = {"REGISTER", "INTERNAL"}

    @classmethod
    def description(cls, context, properties):
        return "Remove the custom asset path"

    @classmethod
    def poll(cls, context):
        return preferences().custom_paths

    def execute(self, context):
        prefs = preferences()

        prefs.custom_paths.remove(prefs.active_path_index)
        prefs.active_path_index = min(max(0, prefs.active_path_index - 1), len(prefs.custom_paths) - 1)
        self.report({"INFO"}, "Removed: Custom asset path")
        return {"FINISHED"}


class IMESHH_OT_custom_path_load(Operator):

    bl_label = "Load Custom Paths"
    bl_idname = "imeshh.custom_path_load"
    bl_options = {"REGISTER", "INTERNAL"}

    directory: StringProperty(subtype="DIR_PATH")

    @classmethod
    def description(cls, context, properties):
        return "Load the custom asset paths"

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        prefs = preferences()

        prefs.custom_paths.clear()
        prefs.active_path_index = 0

        for directory in reversed(os.listdir(self.directory)):
            item = prefs.custom_paths.add()
            prefs.active_path_index = len(prefs.custom_paths) - 1
            item.path = bpy.path.abspath(os.path.join(self.directory, directory))
            item.name = directory

        prefs.local.asset_type = "MODEL"
        self.report({"INFO"}, "Loaded: Custom asset paths")
        return {"FINISHED"}


class IMESHH_OT_save_custom_paths(Operator):
    """Save custom paths to a backup file"""
    
    bl_label = "Save File Paths"
    bl_idname = "imeshh.save_custom_paths"
    bl_options = {"REGISTER", "INTERNAL"}

    @classmethod
    def description(cls, context, properties):
        return "Save all custom file paths to C:\\Users\\USER\\imeshh\\custom_paths.json"

    def execute(self, context):
        success, message = save_custom_paths()
        
        if success:
            self.report({"INFO"}, message)
        else:
            self.report({"ERROR"}, message)
        
        return {"FINISHED"}


class IMESHH_OT_load_custom_paths(Operator):
    """Load custom paths from backup file"""
    
    bl_label = "Load File Paths"
    bl_idname = "imeshh.load_custom_paths"
    bl_options = {"REGISTER", "INTERNAL"}

    @classmethod
    def description(cls, context, properties):
        return "Load all custom file paths from C:\\Users\\USER\\imeshh\\custom_paths.json"

    def execute(self, context):
        success, message = load_custom_paths()
        
        if success:
            self.report({"INFO"}, message)
        else:
            self.report({"WARNING"}, message)
        
        return {"FINISHED"}


classes = (
    IMESHH_OT_custom_path_add,
    IMESHH_OT_custom_path_remove,
    IMESHH_OT_custom_path_load,
    IMESHH_OT_save_custom_paths,
    IMESHH_OT_load_custom_paths,
)


register, unregister = bpy.utils.register_classes_factory(classes)