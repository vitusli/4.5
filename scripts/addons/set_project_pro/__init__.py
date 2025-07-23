# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####


bl_info = {
    "name": "Set Project Pro",
    "description": "Set Project is a versatile Blender add-on designed to streamline your project management experience.",
    "author": "Jishnu jithu",
    "version": (1, 2),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Set Project",
    "doc_url": "",
    "category": "3D View",
}

import bpy
import bpy.app.handlers
import json
import os
import shutil
import webbrowser

from bpy.types import Operator, Panel, Menu
from bpy.app.handlers import persistent


# -------------------------


# Directory where the presets are stored
addon_directory = os.path.dirname(os.path.realpath(__file__))
presets_directory = os.path.join(addon_directory, 'presets')


# -------------------------


def load_preset(self, context):
    preset_file = self.presets + '.json'
    filepath = os.path.join(presets_directory, preset_file)

    # Pass the property group instance to the load_preset function
    load_preset_properties(self, filepath, context)


# Add a new function to load preset properties
def load_preset_properties(property_group, filepath, context):
    if property_group.presets == 'CUSTOM':
        return

    try:
        with open(filepath, 'r') as f:
            preset = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"Failed to load preset from {filepath}")
        return

    # Update the properties of the property group
    property_group.project_name = preset.get("project_name", property_group.project_name)
    property_group.file_name = preset.get("file_name", property_group.file_name)
    property_group.project_location = preset.get("project_location", property_group.project_location)
    property_group.use_file_name = preset.get("use_file_name", property_group.use_file_name)
    property_group.save = preset.get("save", property_group.save)
    property_group.relative_remap = preset.get("relative_remap", property_group.relative_remap)
    property_group.compress = preset.get("compress", property_group.compress)

    # Clear existing folder names
    while len(property_group.folder_names) > 0:
        property_group.folder_names.remove(0)

    # Load folder names from the preset
    if "folder_names" in preset:
        for folder_name in preset["folder_names"]:
            item = property_group.folder_names.add()
            item.name = folder_name


def get_preset_items(self, context):
    preset_files = [
        (file[:-5], file[:-5], '') for file in os.listdir(presets_directory)
        if file.endswith('.json') and file[:-5] != 'CUSTOM'
    ]
    preset_files.insert(0, ('CUSTOM', 'Custom', ''))
    return preset_files


# -------------------------


def update_project_location(self, context):
    # Create new folder properties
    project_location = bpy.path.abspath(os.path.join(self.project_location, self.project_name))
    for folder in os.listdir(project_location):
        if os.path.isdir(os.path.join(project_location, folder)):
            # Check if the folder is already in the folder_names collection
            if folder not in context.scene.project.folder_names:
                # Add a new item to the folder_names collection for the folder
                new_folder = context.scene.project.folder_names.add()
                new_folder.name = folder

                setattr(self, f"folder_{folder}", bpy.props.StringProperty(
                    name=folder,
                    default=folder,  # Set the default value to the folder name
                    description=f"String property for {folder}",
                    subtype='DIR_PATH'
                ))


# get external modified folders
def get_folder_sets(project):
    project_directory = os.path.join(project.project_location, project.project_name)
    project_directory = bpy.path.abspath(project_directory)

    if os.path.isdir(project_directory):
        # Get the current folders in the project_location directory
        actual_folders = set(folder for folder in os.listdir(project_directory) if os.path.isdir(os.path.join(project_directory, folder)))
    else:
        actual_folders = set()

    # Get the current folders in the folder_names collection
    current_folders = set(folder.name for folder in project.folder_names)

    return actual_folders, current_folders


# automatic update of externally modified folders
def update_folders():
    prefs = bpy.context.preferences.addons[__name__].preferences

    if prefs.experimental_features and prefs.update_folders_mode == "AUTOMATIC":
        project = bpy.context.scene.project
        folder_path = os.path.join(project.project_location, project.project_name)
        actual_folders, current_folders = get_folder_sets(project)

        if bpy.data.is_saved and os.path.isdir(folder_path) and actual_folders != current_folders:
            context = bpy.context
            update_project_location(project, context)

    return 3.0


# -------------------------


# Add default folders
def add_default_folders(project):
    if len(project.folder_names) == 0:
        folder_names = ["Scenes", "Assets", "Images", "Source Images", "Hdri", "Clip", "Sound", "Scripts", "Movies"]
        for name in folder_names:
            folder = project.folder_names.add()
            folder.name = name


# -------------------------


# Automatically select the next preset in the list
def auto_select_preset(scene):
    project = scene.project

    # Get the list of all presets
    all_presets = [file[:-5] for file in os.listdir(presets_directory) if file.endswith('.json')]

    # If there are any presets left, select the first one
    if all_presets:
        project.presets = all_presets[0]


# -------------------------


@persistent
def initialize_folders(dummy):
    project = bpy.context.scene.project
    presets = bpy.context.scene.presets

    # Add four folders by default
    if len(project.folder_names) == 0:
        folder_names = ["Scenes", "Assets", "Images", "Source Images", "Hdri", "Clip", "Sound", "Scripts", "Movies"]
        for i in range(9):
            folder = project.folder_names.add()
            folder.name = folder_names[i]

    if len(presets.folder_names) == 0:
        folder_names = ["Scenes", "Assets", "Images", "Source Images", "Hdri", "Clip", "Sound", "Scripts", "Movies"]
        for i in range(9):
            folder = presets.folder_names.add()
            folder.name = folder_names[i]

    project.project_name = project.get_unique_project_name(project.project_name)


# ----------------------------------------------


class PROJECT_PG_properties(bpy.types.PropertyGroup):
    home_dir = os.path.expanduser("~")
    project_location = os.path.join(home_dir, "Documents", "Blender") + "\\"

    def get_unique_project_name(self, name):
        if name is None:
            name = "My Project"

        if not bpy.data.is_saved:
            index = 1

            base_name, extension = os.path.splitext(name)

            if base_name.split()[-1].isdigit():
                *base_name, index = base_name.split()
                base_name = " ".join(base_name)
                index = int(index)

            while True:
                project_path = os.path.join(self.project_location, name)
                if not os.path.exists(project_path):
                    break

                name = f"{base_name} {index}{extension}"
                index += 1

            return name

        return name  # Add this line

    def update_project_name(self, context):
        unique_name = self.get_unique_project_name(self.project_name)
        if unique_name != self.project_name:
            self.project_name = unique_name

    project_name: bpy.props.StringProperty(
        name="Project Name",
        default="My Project",
        update=update_project_name
    )

    file_name: bpy.props.StringProperty(
        name="File Name",
        default="Project"
    )
    project_location: bpy.props.StringProperty(
        name="Project Location",
        subtype='DIR_PATH',
        default=project_location,
        description="Choose the project location",
        update=update_project_location,
    )

    presets: bpy.props.EnumProperty(
        items=get_preset_items,
        name="Preset",
        description="Select a preset",
        update=load_preset
    )
    use_file_name: bpy.props.BoolProperty(
        name="File Name",
        description="Save the file custom name instead of the project name",
        default=True
    )
    save: bpy.props.BoolProperty(
        name="Save",
        description="Save the current file",
        default=True
    )
    relative_remap: bpy.props.BoolProperty(
        name="Relative Remap",
        description="Remap relative paths when saving to a different directory.",
        default=True
    )
    compress: bpy.props.BoolProperty(
        name="Compress",
        description="Write compressed .blend file",
        default=False
    )

    folder_names: bpy.props.CollectionProperty(type=bpy.types.PropertyGroup)
    is_set: bpy.props.BoolProperty(default=False)


# -------------------------


class PRESET_PG_properties(bpy.types.PropertyGroup):
    home_dir = os.path.expanduser("~")
    project_location = os.path.join(home_dir, "Documents", "Blender") + "\\"

    def get_unique_project_name(self, name):
        if not bpy.data.is_saved:
            index = 1

            base_name, extension = os.path.splitext(name)

            if base_name.split()[-1].isdigit():
                *base_name, index = base_name.split()
                base_name = " ".join(base_name)
                index = int(index)

            while True:
                project_path = os.path.join(self.project_location, name)
                if not os.path.exists(project_path):
                    break

                name = f"{base_name} {index}{extension}"
                index += 1

            return name
        else:
            return name

    def update_project_name(self, context):
        unique_name = self.get_unique_project_name(self.project_name)
        if unique_name != self.project_name:
            self.project_name = unique_name

    project_name: bpy.props.StringProperty(
        name="Project Name",
        default="My Project",
        update=update_project_name
    )
    file_name: bpy.props.StringProperty(
        name="File Name",
        default="Project"
    )
    project_location: bpy.props.StringProperty(
        name="Project Location",
        subtype='DIR_PATH',
        default=project_location,
        description="Choose the project location",
    )

    presets: bpy.props.EnumProperty(
        items=get_preset_items,
        name="Preset",
        description="Select a preset",
        update=load_preset
    )

    compress: bpy.props.BoolProperty(
        name="Compress",
        description="Write compressed .blend file",
        default=False
    )
    relative_remap: bpy.props.BoolProperty(
        name="Relative Remap",
        description="directory. different a to saving when paths relativeRemap",
        default=True
    )
    save: bpy.props.BoolProperty(
        name="Save",
        description="Save the current file",
        default=True
    )
    use_file_name: bpy.props.BoolProperty(
        name="File Name",
        description="Save the file custom name instead of the project name",
        default=True
    )

    folder_names: bpy.props.CollectionProperty(type=bpy.types.PropertyGroup)


# ------------------------------------------------


class PROJECT_OT_reset_folders(Operator):
    bl_idname = "project.reset_folders"
    bl_label = "Reset Folder Names"
    bl_description = "Reset the folder names"
    bl_options = {'REGISTER', 'UNDO_GROUPED'}

    def execute(self, context):
        project = context.scene.project
        add_default_folders(project)
        return {'FINISHED'}


class PROJECT_OT_refresh_folders(Operator):
    bl_idname = "project.refresh_folders"
    bl_label = "Refresh Folders"
    bl_description = "Refreshes the list of folders"
    bl_options = {'REGISTER', 'UNDO_GROUPED'}

    def execute(self, context):
        update_project_location(context.scene.project, context)
        return {'FINISHED'}


class PROJECT_OT_add_folder(Operator):
    bl_idname = "project.add_folder"
    bl_label = "Add Folder"
    bl_description = "Adds a new folder to the project"
    bl_options = {'REGISTER', 'UNDO_GROUPED'}

    def execute(self, context):
        if len(context.scene.project.folder_names) < 15:
            new_folder = context.scene.project.folder_names.add()
            new_folder.name = "Folder " + str(len(context.scene.project.folder_names))
        return {'FINISHED'}


class PROJECT_OT_remove_folder(Operator):
    bl_idname = "project.remove_folder"
    bl_label = "Remove Folder"
    bl_description = "Removes the folder from the project"
    bl_options = {'REGISTER', 'UNDO'}
    index: bpy.props.IntProperty()

    def execute(self, context):
        context.scene.project.folder_names.remove(self.index)
        return {'FINISHED'}


# -------------------------


class PROJECT_OT_delete_folder(Operator):
    bl_idname = "project.delete_folder"
    bl_label = "Delete Folder"
    bl_description = "Deletes the corresponding folder from the project directory"
    bl_options = {'REGISTER', 'UNDO_GROUPED'}
    index: bpy.props.IntProperty()

    def execute(self, context):
        project = context.scene.project
        folder_name = project.folder_names[self.index].name
        folder_path = os.path.join(project.project_location, project.project_name, folder_name)

        if os.path.isdir(folder_path):
            files = os.listdir(folder_path)

            # Format the file names into a single string
            files_str = ', '.join(files)

            # Delete the folder
            shutil.rmtree(folder_path)

            if files:
                self.report({'INFO'}, f"Folder '{folder_name}' and its contents: [{files_str}] deleted.")
            else:
                self.report({'INFO'}, f"Folder '{folder_name}' deleted.")

        project.folder_names.remove(self.index)
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)


# -------------------------


class PROJECT_OT_update_location(Operator):
    bl_idname = "project.update_location"
    bl_label = "Update Project Location"
    bl_description = "Check if the project location has changed and update it if necessary"
    bl_options = {'REGISTER', 'UNDO_GROUPED'}

    @classmethod
    def description(cls, context, properties):
        project = context.scene.project
        blender_filepath = bpy.data.filepath
        index = blender_filepath.find(project.project_name)

        # Extract everything before the project_name in the opened file location
        if index != -1:
            updated_location = blender_filepath[:index]

        return f"Project location changed from {project.project_location} to {updated_location}"

    def execute(self, context):
        project = context.scene.project
        current_location = project.project_location
        blender_filepath = bpy.data.filepath
        project_folder = os.path.join(project.project_location, project.project_name)

        # Find the index of the project_name in the opened file location
        index = blender_filepath.find(project.project_name)

        # Extract everything before the project_name in the opened file location
        if index != -1:
            project.project_location = blender_filepath[:index]
            bpy.ops.file.find_missing_files(directory=project.project_location)
            self.report({'INFO'}, f"Project location updated to {project.project_location}")
        else:
            self.report({'ERROR'}, "Error in updating project location. You may need to update the project location manually.")
        return {'CANCELLED'}


class PROJECT_OT_open_folder(Operator):
    bl_idname = "project.open_folder"
    bl_label = "Open Folder"
    bl_description = "Opens the project folder in the file explorer"

    def execute(self, context):
        project = context.scene.project
        project_folder = os.path.join(project.project_location, project.project_name)
        webbrowser.open('file://' + os.path.realpath(project_folder))
        return {'FINISHED'}


# -------------------------


class PROJECT_OT_set_project(Operator):
    bl_idname = "project.set"
    bl_label = "Set Project"
    bl_description = "Sets up the project, creating necessary folders and setting the output filepath"
    bl_options = {'REGISTER', 'UNDO_GROUPED'}

    @classmethod
    def description(cls, context, properties):
        project = context.scene.project
        if project.is_set:
            return "Update the project, create necessary folders"
        else:
            return "Sets up the project, create necessary folders"

    def execute(self, context):
        project = context.scene.project

        if not project.project_location.endswith(os.sep):
            project.project_location += os.sep

        # Create the project folder
        project_folder = os.path.join(project.project_location, project.project_name)
        os.makedirs(project_folder, exist_ok=True)

        # Create the additional folders
        for folder in project.folder_names:
            folder_path = os.path.join(project_folder, folder.name)
            os.makedirs(folder_path, exist_ok=True)

            if folder.name.lower() in ["render", "images", "image"]:
                bpy.context.scene.render.filepath = os.path.join(folder_path, '')

        if context.scene.project.save:
            scenes_folder_name = next((folder.name for folder in project.folder_names if folder.name.lower() in ["scene", "scenes"]), "Scene")
            scenes_folder = os.path.join(project_folder, scenes_folder_name)

            # Check if the Scenes folder is present
            if scenes_folder_name in [folder.name for folder in project.folder_names]:
                folder_to_use = scenes_folder
            else:
                folder_to_use = project_folder

            if context.scene.project.use_file_name:
                filename = project.file_name
            else:
                filename = project.project_name

            filepath = os.path.join(folder_to_use, filename + '.blend')
            bpy.ops.wm.save_as_mainfile(filepath=filepath, compress=project.compress, relative_remap=project.relative_remap)

        if project.is_set:
            bpy.ops.file.find_missing_files(directory=project_folder)
            self.report({'INFO'}, "Project updated successfully!")
        else:
            project.is_set = True
            self.report({'INFO'}, f"Project successfully saved at {project_folder}!")

        return {'FINISHED'}


# --------------------------------------------------


class PRESET_OT_add_folder(Operator):
    bl_idname = "presets.add_folder"
    bl_label = "Add Folder"
    bl_description = "Adds a new folder to the project"
    bl_options = {'REGISTER', 'UNDO_GROUPED'}

    def execute(self, context):
        if len(context.scene.presets.folder_names) < 15:
            new_folder = context.scene.presets.folder_names.add()
            new_folder.name = "Folder " + str(len(context.scene.presets.folder_names))
        return {'FINISHED'}


class PRESET_OT_remove_folder(Operator):
    bl_idname = "presets.remove_folder"
    bl_label = "Remove Folder"
    bl_description = "Removes the folder from the project"
    bl_options = {'REGISTER', 'UNDO'}
    index: bpy.props.IntProperty()

    def execute(self, context):
        context.scene.presets.folder_names.remove(self.index)
        return {'FINISHED'}


class PRESET_OT_delete_preset(Operator):
    bl_idname = "project.delete_preset"
    bl_label = "Delete Preset"
    bl_description = "Deletes the selected preset"
    bl_options = {'REGISTER', 'UNDO_GROUPED'}

    def execute(self, context):
        project = context.scene.project
        preset_name = project.presets

        # Full path to the preset file
        filepath = os.path.join(presets_directory, preset_name + '.json')

        # Check if the preset file exists
        if os.path.isfile(filepath):
            os.remove(filepath)
            self.report({'INFO'}, f"Preset '{preset_name}' deleted successfully.")
        else:
            self.report({'INFO'}, f"Preset '{preset_name}' not found.")

        auto_select_preset(context.scene)
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)


# -------------------------


class PRESET_OT_save_preset(Operator):
    bl_idname = "project.save_preset"
    bl_label = "Save Preset"
    bl_description = "Saves the current project settings as a preset"

    # Define the preset_name property in the operator
    preset_name: bpy.props.StringProperty(
        name="Preset Name",
        description="Enter a name for the preset",
        default="Preset"
    )

    def execute(self, context):
        presets = context.scene.presets
        # Get folder names
        folder_names = [folder.name for folder in presets.folder_names]
        preset = {
            "project_name": presets.project_name,
            "file_name": presets.file_name,
            "project_location": presets.project_location,
            "folder_names": folder_names,
            "use_file_name": presets.use_file_name,
            "save": presets.save,
            "relative_remap": presets.relative_remap,
            "compress": presets.compress
        }

        # Use the preset name from the operator properties
        filename = self.preset_name + '.json'
        with open(os.path.join(presets_directory, filename), 'w') as f:
            json.dump(preset, f, indent=4)
        self.report({'INFO'}, f"Preset '{self.preset_name}' saved successfully.")
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        filename = self.preset_name + '.json'

        # Check if a preset with the given name already exists
        if os.path.exists(os.path.join(presets_directory, filename)):
            layout.label(text="A preset with this name already exists.", icon="ERROR")

        layout.prop(self, "preset_name")


# ---------------------------------------------------------------------------------------


class PROJECT_PT_panel(Panel):
    bl_label = "Set Project"
    bl_idname = "PROJECT_PT_PANEL"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Set Project'

    def draw_header_preset(self, context):
        layout = self.layout
        project = context.scene.project

        if len(project.folder_names) == 0:
            row = layout.row()
            row.operator("project.reset_folders", text="", icon="LOOP_BACK", emboss=False)
            row = layout.row()

    def draw(self, context):
        layout = self.layout
        project = context.scene.project

        self.draw_project_properties(layout, project, context)
        self.draw_save_properties(layout, project, context)
        self.draw_update_properties(layout, project, context)

    def draw_project_properties(self, layout, project, context):
        prefs = bpy.context.preferences.addons[__name__].preferences

        if not context.scene.project.is_set:
            layout.prop(project, "presets", text="")
            layout.separator()

        box = layout.box()
        box.label(text="Projct Name & Path:", icon="CURRENT_FILE")

        box.prop(project, "project_name")
        if context.scene.project.use_file_name:
            box.prop(project, "file_name")
        box.prop(project, "project_location")

        box = layout.box()
        row = box.row()
        row.label(text="Folder Names:", icon="FILEBROWSER")

        for i, folder in enumerate(project.folder_names, start=1):
            row = box.row()
            col = row.column()
            sub_col = col.row(align=True)
            split = sub_col.split(align=True)

            split.prop(folder, "name", text="Folder " + str(i))
            split = sub_col.split(align=True)
            split.scale_x = .95

            folder_path = os.path.join(project.project_location, project.project_name, folder.name)

            operator_index = i - 1  # Subtract 1 from the index for the operator
            if not os.path.isdir(folder_path):
                split.operator("project.remove_folder", text="", icon="PANEL_CLOSE").index = operator_index
            else:
                split.operator("project.delete_folder", text="", icon="TRASH").index = operator_index

        row = box.row(align=True)
        if prefs.experimental_features and prefs.update_folders_mode == "MANUAL" and context.scene.project.is_set:
            row.operator("project.refresh_folders", icon="FILE_REFRESH")

        row.operator("project.add_folder", icon="NEWFOLDER")

    def draw_save_properties(self, layout, project, context):
        box = layout.box()
        box.label(text="Save Options:", icon='PROPERTIES')
        split = box.split(align=True)

        col = split.column(align=True)
        col.prop(project, "use_file_name", icon="WORDWRAP_OFF")

        col = split.column(align=True)
        if project.is_set:
            col.prop(project, "save", icon="FILE_TICK")
        else:
            col.enabled = False
            col.prop(project, "save", icon="FILE_TICK")

        if project.save:
            row = box.row(align=True)
            row.prop(project, "compress", icon="FILE_BACKUP")
            row.prop(project, "relative_remap", icon="SNAP_GRID")

        layout.separator()

        if not project.is_set:
            row = layout.row()
            row.scale_y = 1.6
            row.operator("project.set", text="Save Project", icon="FILE_TICK")

    def draw_update_properties(self, layout, project, context):
        current_location = project.project_location
        opened_file_location = bpy.data.filepath
        index = opened_file_location.find(project.project_name)
        opened_location = opened_file_location[:index] if index != -1 else ""

        if context.scene.project.is_set:
            if current_location != opened_location and index != -1:
                row = layout.row()
                row.scale_y = 1.6
                row.alert = True
                row.operator("project.update_location", text="Update Project Location", icon="FILE_REFRESH")
            else:
                row = layout.row(align=True)
                row.scale_y = 1.6
                row.operator("project.set", text="Update Project", icon="FILE_REFRESH")

                row.operator("project.open_folder", icon="FOLDER_REDIRECT")


# ---------------------------------------------------------------------------------------


class PROJECT_AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    # Add a new property to control the visibility of the information
    bpy.types.Scene.expand_info = bpy.props.BoolProperty(default=False)
    bpy.types.Scene.expand_preset = bpy.props.BoolProperty(default=False)
    bpy.types.Scene.expand_features = bpy.props.BoolProperty(default=False)

    experimental_features: bpy.props.BoolProperty(
        name="Enable Experimental Features",
        description="Enable or disable experimental features",
        default=True,
    )

    update_folders_mode: bpy.props.EnumProperty(
        name="Update Folders",
        description="Choose the mode for updating folders",
        items=[
            ("AUTOMATIC", "Automatic", "Folders are updated automatically"),
            ("MANUAL", "Manual", "Folders are updated manually (recommended). A 'Refresh Folders' button will show on the folder names section")
        ],
        default="MANUAL",
    )

    def draw(self, context):
        layout = self.layout
        layout.use_property_decorate = False

        scene = bpy.context.scene
        presets = context.scene.presets

        box = layout.box()
        self.draw_info(box)

        box = layout.box()
        self.draw_preset_settings(box, presets, context)

        if scene.expand_preset:
            self.draw_project_name_and_path(box, presets)

            row = box.row()
            row = box.row()
            row.scale_y = 1.6
            row.operator("project.save_preset", icon="FILE_TICK")

            sub = row.row()
            sub.operator("project.delete_preset", text="Delete Preset", icon="TRASH")
            sub.enabled = not scene.presets.presets == 'CUSTOM'

        box = layout.box()
        self.draw_experimental(box)

    def draw_info(self, layout):
        row = layout.row()
        scene = bpy.context.scene
        icon = 'TRIA_DOWN' if scene.expand_info else 'TRIA_RIGHT'
        row.prop(scene, "expand_info", icon=icon, text="", emboss=False)
        row.label(text="Info")

        if scene.expand_info:
            def split_label(layout, text):
                region_width = bpy.context.region.width
                ui_scale = bpy.context.preferences.system.ui_scale
                max_line_length = int(region_width / ui_scale / 5.7)

                while len(text) > max_line_length:
                    split_index = text.rfind(' ', 0, max_line_length)
                    if split_index == -1:
                        split_index = max_line_length
                    layout.label(text=text[:split_index])
                    text = text[split_index:].lstrip()
                layout.label(text=text)

            layout.label(text="Folder Naming:", icon="FILE_FOLDER")
            split_label(layout, "- If the folder name is 'Render', 'Image', or 'Images', it will be used as the render output path.")
            split_label(layout, "- If the folder name is 'Scene' or 'Scenes', it will be used as the blender file saving folder.")

    def draw_preset_settings(self, layout, presets, context):
        scene = bpy.context.scene
        all_presets = [file[:-5] for file in os.listdir(presets_directory) if file.endswith('.json')]
        layout.use_property_split = True

        row = layout.row()
        icon = 'TRIA_DOWN' if scene.expand_preset else 'TRIA_RIGHT'
        row.prop(scene, "expand_preset", icon=icon, text="", emboss=False)
        row.label(text="Preset Settings")

        if scene.expand_preset:
            if len(all_presets) > 0:
                layout.prop(presets, "presets")

    def draw_project_name_and_path(self, layout, presets):
        layout.use_property_split = True
        layout.separator()
        layout.label(text="Project Details:", icon="CURRENT_FILE")

        layout.prop(presets, "project_name", text="Project Name")
        if presets.use_file_name:
            layout.prop(presets, "file_name", text="File Name")
        layout.prop(presets, "project_location", text="Project Location")

        layout.separator()
        layout.label(text="Folder Names:", icon="FILEBROWSER")

        for i in range(len(presets.folder_names)):
            row = layout.row(align=True)
            row.prop(presets.folder_names[i], "name", text="Folder " + str(i + 1))
            row.operator("presets.remove_folder", text="", icon="PANEL_CLOSE").index = i

        row = layout.row()
        row.label(text="",)
        row.scale_x = 15
        row.operator("presets.add_folder", text="", icon="ADD")

        layout.separator()

        layout.use_property_split = False
        row = layout.row()
        row.label(text="Project Save Options:", icon="FILE_TICK")

        row = layout.row(align=True)
        row.scale_x = 2.0
        row.prop(presets, "use_file_name", text="File Name", toggle=True)

        row.prop(presets, "save", toggle=True)
        if presets.save:
            row.prop(presets, "relative_remap", toggle=True)
            row.prop(presets, "compress", toggle=True)

    def draw_experimental(self, layout):
        layout.use_property_split = True
        scene = bpy.context.scene

        row = layout.row()
        icon = 'TRIA_DOWN' if scene.expand_features else 'TRIA_RIGHT'
        row.prop(scene, "expand_features", icon=icon, text="", emboss=False)
        row.label(text="External Folder Access")

        if scene.expand_features:
            check_icon = 'CHECKBOX_HLT' if self.experimental_features else 'CHECKBOX_DEHLT'
            layout.prop(self, "experimental_features", text="External Folder Access")
            if self.experimental_features:
                row = layout.row()
                row.prop(self, "update_folders_mode", expand=True)

# ---------------------------------------------------------------------------------------


classes = [
    PROJECT_PG_properties,
    PROJECT_OT_reset_folders,
    PROJECT_OT_add_folder,
    PROJECT_OT_remove_folder,
    PROJECT_OT_delete_folder,
    PROJECT_OT_refresh_folders,
    PROJECT_OT_update_location,
    PROJECT_OT_open_folder,
    PROJECT_OT_set_project,
    PRESET_OT_save_preset,
    PRESET_PG_properties,
    PRESET_OT_add_folder,
    PRESET_OT_delete_preset,
    PRESET_OT_remove_folder,
    PROJECT_PT_panel,
    PROJECT_AddonPreferences,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.project = bpy.props.PointerProperty(type=PROJECT_PG_properties)
    bpy.types.Scene.presets = bpy.props.PointerProperty(type=PRESET_PG_properties)
    bpy.types.Scene.folder_Assets = bpy.props.StringProperty(name="folder_Assets")

    bpy.app.handlers.load_post.append(initialize_folders)

    bpy.app.timers.register(update_folders, first_interval=1.0)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    bpy.app.handlers.load_post.remove(initialize_folders)

    if bpy.app.timers.is_registered(update_folders):
        bpy.app.timers.unregister(update_folders)

    del bpy.types.Scene.project
    del bpy.types.Scene.presets
    del bpy.types.Scene.folder_Assets


if __name__ == "__main__":
    register()
