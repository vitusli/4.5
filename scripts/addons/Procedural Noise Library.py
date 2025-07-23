import bpy
import os
import zipfile
import webbrowser
import json
from bpy.props import StringProperty, PointerProperty, EnumProperty, IntProperty
from bpy.types import Operator, AddonPreferences, Panel, PropertyGroup
from bpy.utils import previews

bl_info = {
    "name": "Procedural Noise Library: Pro",
    "blender": (4, 3, 0),
    "category": "Material",
    "description": "The most advanced noise texture library for Blender.",
    "author": "Blender Station",
    "version": (2, 3, 1),
    "doc_url": "https://blendermarket.com/products/procedural-noise-library/docs"
}

# Global dictionary for storing preview collections.
preview_collections = {}
VALID_IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg')

# Global flag for our timer
noise_timer_running = True

# Directory to store presets (adjust as needed)
PRESETS_DIR = os.path.join(bpy.utils.user_resource('CONFIG'), "noise_presets")
if not os.path.exists(PRESETS_DIR):
    os.makedirs(PRESETS_DIR)


def load_previews_from_folder(previews_folder: str, report_callback=None) -> object:
    """Load all preview images from the given folder."""
    pcoll = previews.new()
    for img_file in os.listdir(previews_folder):
        if img_file.lower().endswith(VALID_IMAGE_EXTENSIONS):
            img_path = os.path.join(previews_folder, img_file)
            img_name = os.path.splitext(img_file)[0]
            if img_name not in pcoll:
                try:
                    pcoll.load(img_name, img_path, 'IMAGE')
                except Exception as e:
                    msg = f"Failed to load preview '{img_name}': {e}"
                    if report_callback:
                        report_callback(msg, 'WARNING')
                    else:
                        print("Warning:", msg)
    return pcoll


def clear_previews() -> None:
    for pcoll in preview_collections.values():
        previews.remove(pcoll)
    preview_collections.clear()


def load_saved_previews() -> None:
    prefs = bpy.context.preferences.addons[__name__].preferences
    previews_path = prefs.previews_path
    if previews_path and os.path.exists(previews_path):
        pcoll = load_previews_from_folder(previews_path)
        preview_collections["texture_importer_previews"] = pcoll


def get_imported_noise_nodes(self, context):
    """Build a list of imported noise texture node instances with friendly names."""
    items = []
    node_tree = None
    if context.space_data:
        node_tree = getattr(context.space_data, 'edit_tree', None) or getattr(context.space_data, 'node_tree', None)
    if node_tree is None and context.object and context.object.active_material and context.object.active_material.use_nodes:
        node_tree = context.object.active_material.node_tree
    if node_tree:
        for node in node_tree.nodes:
            if node.type == 'GROUP' and node.get("noise_texture", False):
                friendly = node.get("noise_texture_friendly", node.name)
                items.append((node.name, friendly, ""))
    return items if items else [("None", "None", "No imported noise textures found")]


def get_available_tools(self, context):
    """
    Build a list of available tool node groups from the tools.blend file.
    These tools do not have previews – only names.
    """
    items = []
    prefs = bpy.context.preferences.addons[__name__].preferences
    tools_blend_path = prefs.tools_blend_file_path
    if tools_blend_path and os.path.exists(tools_blend_path):
        try:
            with bpy.data.libraries.load(tools_blend_path, link=True) as (data_from, data_to):
                for tool in data_from.node_groups:
                    items.append((tool, tool, ""))
        except Exception as e:
            items.append(("None", "None", f"Error reading tools blend file: {e}"))
    else:
        items.append(("None", "None", "Tools blend file not set or not found"))
    if not items:
        items.append(("None", "None", "No tools found in the blend file"))
    return items


def get_saved_presets(self, context):
    """Build a list of saved presets for the node group (type) of the currently selected noise node."""
    items = []
    props = context.scene.texture_importer_props
    node_instance = None
    node_tree = None
    if props.selected_imported_node and props.selected_imported_node != "None":
        if context.space_data:
            node_tree = getattr(context.space_data, 'edit_tree', None) or getattr(context.space_data, 'node_tree', None)
        if node_tree is None and context.object and context.object.active_material and context.object.active_material.use_nodes:
            node_tree = context.object.active_material.node_tree
        if node_tree:
            node_instance = node_tree.nodes.get(props.selected_imported_node)
    node_group_name = None
    if node_instance and node_instance.node_tree:
        node_group_name = node_instance.node_tree.name
    if node_group_name:
        node_presets_folder = os.path.join(PRESETS_DIR, node_group_name)
        if os.path.exists(node_presets_folder):
            for file in os.listdir(node_presets_folder):
                if file.endswith(".json"):
                    preset_name = os.path.splitext(file)[0]
                    items.append((preset_name, preset_name, ""))
    if not items:
        items.append(("None", "No presets", ""))
    return items


class NoiseLibraryPreferences(AddonPreferences):
    """Preferences for asset setup."""
    bl_idname = __name__

    zip_file: StringProperty(
        name="Assets ZIP File",
        description="Select the ZIP file containing previews and the blend file.",
        subtype='FILE_PATH'
    )
    asset_dir: StringProperty(
        name="Assets Directory",
        description="Directory where the assets will be extracted and stored.",
        subtype='DIR_PATH'
    )
    previews_path: StringProperty(
        name="Previews Path",
        description="Path to the previews folder.",
        subtype='DIR_PATH'
    )
    blend_file_path: StringProperty(
        name="Blend File Path",
        description="Path to the textures blend file.",
        subtype='FILE_PATH'
    )
    tools_blend_file_path: StringProperty(
        name="Tools Blend File Path",
        description="Path to the tools blend file.",
        subtype='FILE_PATH'
    )
    node_width: IntProperty(
        name="Node Width",
        description="Width for imported nodes",
        default=200,
        min=50,
        max=1000
    )

    def draw(self, context) -> None:
        layout = self.layout
        box = layout.box()
        box.label(text="Asset Setup", icon='FILE_FOLDER')
        box.operator("procedural_noise_library.select_zip_file", text="Select ZIP File", icon='FILE_BLEND')
        box.operator("procedural_noise_library.select_asset_dir", text="Select Asset Directory", icon='FILE_FOLDER')
        if self.asset_dir:
            box.label(text=f"Installation Path: {self.asset_dir}")
        else:
            box.label(text="No asset directory selected.")
        layout.operator("procedural_noise_library.install_assets", text="Install Assets", icon='FILE_TICK')
        layout.operator("procedural_noise_library.open_documentation", text="Open Documentation", icon='HELP')

        layout.separator()
        node_box = layout.box()
        node_box.label(text="Node Settings", icon='NODE')
        node_box.prop(self, "node_width", text="Imported Node Width")


class NoiseLibraryProperties(PropertyGroup):
    """
    Stores:
      - selected_preview: Name of the chosen preview image.
      - selected_imported_node: Identifier of the imported noise texture node to edit.
      - selected_tool: Name of the tool to import (from tools.blend).
      - selected_preset: Name of the saved preset to apply.
    """
    selected_preview: StringProperty(
        name="Selected Preview",
        description="Name of the selected preview image"
    )
    selected_imported_node: EnumProperty(
        name="Imported Noise Texture",
        description="Select which imported noise texture to edit",
        items=get_imported_noise_nodes
    )
    selected_tool: EnumProperty(
        name="Available Tools",
        description="Select a tool to import",
        items=get_available_tools
    )
    selected_preset: EnumProperty(
        name="Preset",
        description="Select a saved preset for this noise texture type",
        items=get_saved_presets
    )


class OpenDocumentationOperator(Operator):
    """Open documentation in a web browser."""
    bl_idname = "procedural_noise_library.open_documentation"
    bl_label = "Open Documentation"

    def execute(self, context) -> set:
        webbrowser.open(bl_info["doc_url"])
        return {'FINISHED'}


class SelectZipFileOperator(Operator):
    """Select the ZIP file containing assets."""
    bl_idname = "procedural_noise_library.select_zip_file"
    bl_label = "Select ZIP File"
    filepath: StringProperty(subtype="FILE_PATH")

    def execute(self, context) -> set:
        prefs = context.preferences.addons[__name__].preferences
        prefs.zip_file = self.filepath
        self.report({'INFO'}, f"Selected ZIP File: {self.filepath}")
        return {'FINISHED'}

    def invoke(self, context, event) -> set:
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class SelectAssetDirOperator(Operator):
    """Select the directory for asset installation."""
    bl_idname = "procedural_noise_library.select_asset_dir"
    bl_label = "Select Asset Directory"
    directory: StringProperty(subtype="DIR_PATH")

    def execute(self, context) -> set:
        prefs = context.preferences.addons[__name__].preferences
        prefs.asset_dir = self.directory
        self.report({'INFO'}, f"Selected Asset Directory: {self.directory}")
        return {'FINISHED'}

    def invoke(self, context, event) -> set:
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class InstallAssetsOperator(Operator):
    """Install assets from the selected ZIP file."""
    bl_idname = "procedural_noise_library.install_assets"
    bl_label = "Install Assets"

    def execute(self, context) -> set:
        prefs = context.preferences.addons[__name__].preferences
        zip_file = prefs.zip_file
        asset_dir = prefs.asset_dir

        if not zip_file or not os.path.isfile(zip_file) or not zipfile.is_zipfile(zip_file):
            self.report({'ERROR'}, "Invalid or missing ZIP file")
            return {'CANCELLED'}
        if not asset_dir:
            self.report({'ERROR'}, "Asset directory not selected")
            return {'CANCELLED'}
        if not os.path.exists(asset_dir):
            try:
                os.makedirs(asset_dir)
            except Exception as e:
                self.report({'ERROR'}, f"Failed to create asset directory: {e}")
                return {'CANCELLED'}
        try:
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                zip_ref.extractall(asset_dir)
        except Exception as e:
            self.report({'ERROR'}, f"Failed to extract ZIP file: {e}")
            return {'CANCELLED'}

        # Check for required files:
        previews_folder = os.path.join(asset_dir, "previews")
        blend_file = os.path.join(asset_dir, "textures.blend")
        tools_file = os.path.join(asset_dir, "tools.blend")
        if not os.path.exists(previews_folder) or not os.path.exists(blend_file):
            self.report({'ERROR'}, "Missing previews folder or textures.blend file in the asset directory")
            return {'CANCELLED'}
        if not os.path.exists(tools_file):
            self.report({'ERROR'}, "Missing tools.blend file in the asset directory")
            return {'CANCELLED'}

        prefs.previews_path = previews_folder
        prefs.blend_file_path = blend_file
        prefs.tools_blend_file_path = tools_file

        pcoll = load_previews_from_folder(previews_folder, report_callback=self.report)
        preview_collections["texture_importer_previews"] = pcoll
        self.report({'INFO'}, "Assets Installed Successfully")
        return {'FINISHED'}


class NoiseLibraryPanel(Panel):
    """
    Main panel in the Node Editor (N-panel > Noise Library).
    The Preset Manager appears just below the "Edit Noise Texture" dropdown.
    The Noise Texture Settings block displays the name of the noise (editable)
    followed by its input settings.
    """
    bl_label = "Procedural Noise Library"
    bl_idname = "MATERIAL_PT_procedural_noise_library"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Noise Library"

    def draw(self, context) -> None:
        layout = self.layout
        scene = context.scene
        importer_props = scene.texture_importer_props

        # Header
        header = layout.row(align=True)
        header.label(text="Procedural Noise Library", icon='TEXTURE')
        header.operator("procedural_noise_library.open_documentation", text="", icon='HELP')
        layout.separator()

        # Integrated Toolbar (formerly a separate tab)
        toolbar = layout.box()
        toolbar.label(text="Toolbar", icon='TOOL_SETTINGS')
        toolbar.prop(importer_props, "selected_tool", text="Select Tool")
        toolbar.operator("procedural_noise_library.import_tool", text="Import Tool", icon='TOOL_SETTINGS')
        layout.separator()

        # Selected Preview display
        preview_box = layout.box()
        col = preview_box.column(align=True)
        col.alignment = 'CENTER'
        col.label(text="Selected Preview", icon='RENDER_RESULT')
        if importer_props.selected_preview:
            pcoll = preview_collections.get("texture_importer_previews")
            if pcoll and importer_props.selected_preview in pcoll:
                preview = pcoll[importer_props.selected_preview]
                col.template_icon(icon_value=preview.icon_id, scale=16)
                col.separator(factor=1.0)
                col.label(text=importer_props.selected_preview)
            else:
                col.label(text="(Preview not found)", icon='INFO')
        else:
            col.label(text="No preview selected", icon='INFO')
        layout.separator()

        # Action buttons: Open Library & Import Node.
        actions = layout.row(align=True)
        actions.operator("procedural_noise_library.show_gallery", text="Open Library", icon='IMAGE_DATA')
        if importer_props.selected_preview:
            actions.operator("procedural_noise_library.import_node", text="Import Node", icon='NODETREE')
        layout.separator()

        # Dropdown to choose which imported noise texture to edit.
        layout.prop(importer_props, "selected_imported_node", text="Edit Noise Texture")
        layout.separator()

        # Preset Manager (placed below "Edit Noise Texture")
        preset_box = layout.box()
        preset_box.label(text="Preset Manager", icon='FILE_FOLDER')
        row1 = preset_box.row(align=True)
        row1.prop(importer_props, "selected_preset", text="Preset")
        row1.operator("procedural_noise_library.apply_preset", text="Apply", icon='CHECKMARK')
        row2 = preset_box.row(align=True)
        row2.operator("procedural_noise_library.save_preset", text="Save Preset", icon='FILE_TICK')
        row2.operator("procedural_noise_library.delete_preset", text="Delete", icon='TRASH')
        row2.operator("procedural_noise_library.rename_preset", text="Rename", icon='FILE_TEXT')
        layout.separator()

        # Noise Texture Settings
        settings_box = layout.box()
        settings_box.label(text="Noise Texture Settings", icon='PREFERENCES')
        node_tree = (getattr(context.space_data, 'edit_tree', None) or getattr(context.space_data, 'node_tree', None))
        if node_tree is None and context.object and context.object.active_material and context.object.active_material.use_nodes:
            node_tree = context.object.active_material.node_tree
        node_instance = node_tree.nodes.get(importer_props.selected_imported_node) if node_tree else None
        if node_instance:
            # Display the noise's name (editable)
            row = settings_box.row()
            row.prop(node_instance, "label", text="Noise Name")
            # Then list its input settings
            for inp in node_instance.inputs:
                row = settings_box.row()
                try:
                    row.prop(inp, "default_value", text=inp.name)
                except Exception:
                    row.label(text=f"{inp.name}: {getattr(inp, 'default_value', 'N/A')}")
        else:
            settings_box.label(text="No noise texture selected for editing.")


class ShowGalleryOperator(Operator):
    """Popup gallery to select a preview."""
    bl_idname = "procedural_noise_library.show_gallery"
    bl_label = "Open Library"

    def execute(self, context) -> set:
        pcoll = preview_collections.get("texture_importer_previews", {})

        def draw_gallery(self, _context):
            layout = self.layout
            if not pcoll:
                layout.label(text="No previews available.")
                return
            grid = layout.grid_flow(columns=1, even_columns=True, even_rows=True)
            for img_name in pcoll.keys():
                preview = pcoll[img_name]
                col = grid.column(align=True)
                col.alignment = 'CENTER'
                col.template_icon(icon_value=preview.icon_id, scale=10)
                op = col.operator("procedural_noise_library.select_preview", text=img_name)
                op.preview_name = img_name

        context.window_manager.popup_menu(draw_gallery, title="Select a Preview", icon='IMAGE_DATA')
        return {'FINISHED'}


class SelectPreviewOperator(Operator):
    """Select a preview from the gallery."""
    bl_idname = "procedural_noise_library.select_preview"
    bl_label = "Select Preview"
    preview_name: StringProperty()

    def execute(self, context) -> set:
        context.scene.texture_importer_props.selected_preview = self.preview_name
        return {'FINISHED'}


class ImportNodeOperator(Operator):
    """Import a node group from an external blend file."""
    bl_idname = "procedural_noise_library.import_node"
    bl_label = "Import Node"

    def execute(self, context) -> set:
        prefs = context.preferences.addons[__name__].preferences
        blend_path = prefs.blend_file_path
        importer_props = context.scene.texture_importer_props
        preview_name = importer_props.selected_preview

        if not blend_path or not os.path.exists(blend_path):
            self.report({'ERROR'}, "Blend file not found")
            return {'CANCELLED'}

        node_name = preview_name
        with bpy.data.libraries.load(blend_path, link=False) as (data_from, data_to):
            if node_name in data_from.node_groups:
                data_to.node_groups.append(node_name)
            else:
                self.report({'ERROR'}, f"Node group '{node_name}' not found in the blend file. Check naming!")
                return {'CANCELLED'}

        if node_name not in bpy.data.node_groups:
            self.report({'ERROR'}, f"Failed to load node group '{node_name}'.")
            return {'CANCELLED'}

        node_tree = (getattr(context.space_data, 'edit_tree', None) or getattr(context.space_data, 'node_tree', None))
        if node_tree is None and context.object:
            mat = context.object.active_material
            if mat and mat.use_nodes:
                node_tree = mat.node_tree
        if node_tree is None:
            self.report({'ERROR'}, "No active node tree found. Open a Node Editor or select a node tree.")
            return {'CANCELLED'}

        for node in node_tree.nodes:
            node.select = False

        if isinstance(node_tree, bpy.types.ShaderNodeTree):
            node_group = node_tree.nodes.new('ShaderNodeGroup')
        elif isinstance(node_tree, bpy.types.GeometryNodeTree):
            node_group = node_tree.nodes.new('GeometryNodeGroup')
        else:
            self.report({'ERROR'}, "Unsupported node tree type.")
            return {'CANCELLED'}

        node_group.node_tree = bpy.data.node_groups[node_name]
        node_group["noise_texture"] = True
        count = sum(1 for n in node_tree.nodes if n.type == 'GROUP' and n.node_tree and n.node_tree.name == node_name)
        friendly_name = f"{node_name}_{count}"
        node_group["noise_texture_friendly"] = friendly_name
        node_group.label = friendly_name

        if hasattr(context.space_data, "cursor_location"):
            node_group.location = context.space_data.cursor_location
        else:
            node_group.location = (0, 0)
        node_group.width = prefs.node_width
        node_group.select = True
        node_tree.nodes.active = node_group
        bpy.ops.transform.translate('INVOKE_DEFAULT')

        importer_props.selected_imported_node = node_group.name

        self.report({'INFO'}, f"Imported Node: {friendly_name}")
        bpy.context.area.tag_redraw()
        return {'FINISHED'}


class ImportToolOperator(Operator):
    """Import a tool node group from an external tools blend file."""
    bl_idname = "procedural_noise_library.import_tool"
    bl_label = "Import Tool"

    def execute(self, context) -> set:
        prefs = context.preferences.addons[__name__].preferences
        tools_blend_path = prefs.tools_blend_file_path
        props = context.scene.texture_importer_props
        tool_name = props.selected_tool

        if tool_name == "None":
            self.report({'ERROR'}, "No tool selected")
            return {'CANCELLED'}
        if not tools_blend_path or not os.path.exists(tools_blend_path):
            self.report({'ERROR'}, "Tools blend file not found")
            return {'CANCELLED'}

        with bpy.data.libraries.load(tools_blend_path, link=False) as (data_from, data_to):
            if tool_name in data_from.node_groups:
                data_to.node_groups.append(tool_name)
            else:
                self.report({'ERROR'}, f"Tool '{tool_name}' not found in the blend file. Check naming!")
                return {'CANCELLED'}

        if tool_name not in bpy.data.node_groups:
            self.report({'ERROR'}, f"Failed to load tool node group '{tool_name}'.")
            return {'CANCELLED'}

        node_tree = (getattr(context.space_data, 'edit_tree', None) or getattr(context.space_data, 'node_tree', None))
        if node_tree is None and context.object:
            mat = context.object.active_material
            if mat and mat.use_nodes:
                node_tree = mat.node_tree
        if node_tree is None:
            self.report({'ERROR'}, "No active node tree found. Open a Node Editor or select a node tree.")
            return {'CANCELLED'}

        for node in node_tree.nodes:
            node.select = False

        if isinstance(node_tree, bpy.types.ShaderNodeTree):
            node_group = node_tree.nodes.new('ShaderNodeGroup')
        elif isinstance(node_tree, bpy.types.GeometryNodeTree):
            node_group = node_tree.nodes.new('GeometryNodeGroup')
        else:
            self.report({'ERROR'}, "Unsupported node tree type.")
            return {'CANCELLED'}

        node_group.node_tree = bpy.data.node_groups[tool_name]
        node_group["tool_node"] = True
        count = sum(1 for n in node_tree.nodes if n.type == 'GROUP' and n.node_tree and n.node_tree.name == tool_name)
        friendly_name = f"{tool_name}_{count}"
        node_group["tool_node_friendly"] = friendly_name
        node_group.label = friendly_name

        if hasattr(context.space_data, "cursor_location"):
            node_group.location = context.space_data.cursor_location
        else:
            node_group.location = (0, 0)
        node_group.width = prefs.node_width
        node_group.select = True
        node_tree.nodes.active = node_group
        bpy.ops.transform.translate('INVOKE_DEFAULT')

        self.report({'INFO'}, f"Imported Tool: {friendly_name}")
        bpy.context.area.tag_redraw()
        return {'FINISHED'}


# === Save Preset Operator ===
class SavePresetOperator(Operator):
    """Save current noise texture customization as a preset (applied to all nodes of this type)."""
    bl_idname = "procedural_noise_library.save_preset"
    bl_label = "Save Customization Preset"

    preset_name: StringProperty(name="Preset Name", default="MyPreset")

    def invoke(self, context, event) -> set:
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "preset_name", text="Preset Name")

    def execute(self, context) -> set:
        props = context.scene.texture_importer_props
        node_tree = None
        if context.space_data:
            node_tree = getattr(context.space_data, 'edit_tree', None) or getattr(context.space_data, 'node_tree', None)
        if node_tree is None and context.object and context.object.active_material and context.object.active_material.use_nodes:
            node_tree = context.object.active_material.node_tree
        node_instance = node_tree.nodes.get(props.selected_imported_node) if node_tree else None
        if not node_instance or not node_instance.node_tree:
            self.report({'ERROR'}, "No valid noise node selected")
            return {'CANCELLED'}
        group_name = node_instance.node_tree.name
        preset = {}
        for input_socket in node_instance.inputs:
            val = input_socket.default_value
            try:
                if hasattr(val, "__iter__") and not isinstance(val, str):
                    val = list(val)
            except Exception:
                pass
            preset[input_socket.name] = val
        node_presets_folder = os.path.join(PRESETS_DIR, group_name)
        if not os.path.exists(node_presets_folder):
            os.makedirs(node_presets_folder)
        preset_path = os.path.join(node_presets_folder, self.preset_name + ".json")
        try:
            with open(preset_path, 'w') as f:
                json.dump(preset, f, indent=4)
        except Exception as e:
            self.report({'ERROR'}, f"Failed to save preset: {e}")
            return {'CANCELLED'}
        self.report({'INFO'}, f"Preset '{self.preset_name}' saved for node type '{group_name}'")
        for area in context.screen.areas:
            if area.type == 'NODE_EDITOR':
                area.tag_redraw()
        return {'FINISHED'}


# === Apply Preset Operator ===
class ApplyPresetOperator(Operator):
    """Apply a saved preset to all noise nodes of the same type."""
    bl_idname = "procedural_noise_library.apply_preset"
    bl_label = "Apply Preset"

    def execute(self, context) -> set:
        props = context.scene.texture_importer_props
        node_tree = None
        if context.space_data:
            node_tree = getattr(context.space_data, 'edit_tree', None) or getattr(context.space_data, 'node_tree', None)
        if node_tree is None and context.object and context.object.active_material and context.object.active_material.use_nodes:
            node_tree = context.object.active_material.node_tree
        node_instance = node_tree.nodes.get(props.selected_imported_node) if node_tree else None
        if not node_instance or not node_instance.node_tree:
            self.report({'ERROR'}, "No valid noise node selected")
            return {'CANCELLED'}
        group_name = node_instance.node_tree.name
        preset_name = props.selected_preset
        if not preset_name or preset_name == "None":
            self.report({'ERROR'}, "No preset selected")
            return {'CANCELLED'}
        node_presets_folder = os.path.join(PRESETS_DIR, group_name)
        preset_path = os.path.join(node_presets_folder, preset_name + ".json")
        if not os.path.exists(preset_path):
            self.report({'ERROR'}, "Preset file not found")
            return {'CANCELLED'}
        try:
            with open(preset_path, 'r') as f:
                preset = json.load(f)
        except Exception as e:
            self.report({'ERROR'}, f"Failed to load preset: {e}")
            return {'CANCELLED'}
        for node in node_tree.nodes:
            if node.type == 'GROUP' and node.get("noise_texture", False):
                if node.node_tree and node.node_tree.name == group_name:
                    for input_socket in node.inputs:
                        if input_socket.name in preset:
                            try:
                                input_socket.default_value = preset[input_socket.name]
                            except Exception as e:
                                self.report({'WARNING'}, f"Could not apply value for {input_socket.name}: {e}")
        for area in context.screen.areas:
            if area.type == 'NODE_EDITOR':
                area.tag_redraw()
        self.report({'INFO'}, f"Preset '{preset_name}' applied to all '{group_name}' nodes")
        return {'FINISHED'}


# === Delete Preset Operator ===
class DeletePresetOperator(Operator):
    """Delete the selected preset."""
    bl_idname = "procedural_noise_library.delete_preset"
    bl_label = "Delete Preset"

    def execute(self, context) -> set:
        props = context.scene.texture_importer_props
        node_tree = None
        if context.space_data:
            node_tree = getattr(context.space_data, 'edit_tree', None) or getattr(context.space_data, 'node_tree', None)
        if node_tree is None and context.object and context.object.active_material and context.object.active_material.use_nodes:
            node_tree = context.object.active_material.node_tree
        node_instance = node_tree.nodes.get(props.selected_imported_node) if node_tree else None
        if not node_instance or not node_instance.node_tree:
            self.report({'ERROR'}, "No valid noise node selected")
            return {'CANCELLED'}
        group_name = node_instance.node_tree.name
        preset_name = props.selected_preset
        if not preset_name or preset_name == "None":
            self.report({'ERROR'}, "No preset selected")
            return {'CANCELLED'}
        node_presets_folder = os.path.join(PRESETS_DIR, group_name)
        preset_path = os.path.join(node_presets_folder, preset_name + ".json")
        if not os.path.exists(preset_path):
            self.report({'ERROR'}, "Preset file not found")
            return {'CANCELLED'}
        try:
            os.remove(preset_path)
        except Exception as e:
            self.report({'ERROR'}, f"Failed to delete preset: {e}")
            return {'CANCELLED'}
        self.report({'INFO'}, f"Preset '{preset_name}' deleted for node type '{group_name}'")
        for area in context.screen.areas:
            if area.type == 'NODE_EDITOR':
                area.tag_redraw()
        return {'FINISHED'}


# === Rename Preset Operator ===
class RenamePresetOperator(Operator):
    """Rename the selected preset."""
    bl_idname = "procedural_noise_library.rename_preset"
    bl_label = "Rename Preset"

    new_name: StringProperty(name="New Preset Name", default="NewPresetName")

    def invoke(self, context, event) -> set:
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "new_name", text="New Preset Name")

    def execute(self, context) -> set:
        props = context.scene.texture_importer_props
        node_tree = None
        if context.space_data:
            node_tree = getattr(context.space_data, 'edit_tree', None) or getattr(context.space_data, 'node_tree', None)
        if node_tree is None and context.object and context.object.active_material and context.object.active_material.use_nodes:
            node_tree = context.object.active_material.node_tree
        node_instance = node_tree.nodes.get(props.selected_imported_node) if node_tree else None
        if not node_instance or not node_instance.node_tree:
            self.report({'ERROR'}, "No valid noise node selected")
            return {'CANCELLED'}
        group_name = node_instance.node_tree.name
        preset_name = props.selected_preset
        if not preset_name or preset_name == "None":
            self.report({'ERROR'}, "No preset selected")
            return {'CANCELLED'}
        node_presets_folder = os.path.join(PRESETS_DIR, group_name)
        old_path = os.path.join(node_presets_folder, preset_name + ".json")
        new_path = os.path.join(node_presets_folder, self.new_name + ".json")
        if not os.path.exists(old_path):
            self.report({'ERROR'}, "Preset file not found")
            return {'CANCELLED'}
        try:
            os.rename(old_path, new_path)
        except Exception as e:
            self.report({'ERROR'}, f"Failed to rename preset: {e}")
            return {'CANCELLED'}
        self.report({'INFO'}, f"Preset renamed to '{self.new_name}' for node type '{group_name}'")
        for area in context.screen.areas:
            if area.type == 'NODE_EDITOR':
                area.tag_redraw()
        return {'FINISHED'}


# Timer callback to update the selected imported node based on the active node.
def update_noise_selection_timer():
    global noise_timer_running
    if not noise_timer_running:
        return None
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'NODE_EDITOR':
                node_tree = getattr(area.spaces.active, 'edit_tree', None) or getattr(area.spaces.active, 'node_tree',
                                                                                      None)
                if node_tree:
                    active = node_tree.nodes.active
                    # Always update to the active noise texture node (if any)
                    if active and active.type == 'GROUP' and active.get("noise_texture", False):
                        bpy.context.scene.texture_importer_props.selected_imported_node = active.name
                area.tag_redraw()
    return 0.1


classes = [
    NoiseLibraryPreferences,
    NoiseLibraryProperties,
    InstallAssetsOperator,
    NoiseLibraryPanel,
    ShowGalleryOperator,
    SelectPreviewOperator,
    ImportNodeOperator,
    ImportToolOperator,
    OpenDocumentationOperator,
    SelectZipFileOperator,
    SelectAssetDirOperator,
    SavePresetOperator,
    ApplyPresetOperator,
    DeletePresetOperator,
    RenamePresetOperator
]


def register() -> None:
    global noise_timer_running
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.texture_importer_props = PointerProperty(type=NoiseLibraryProperties)
    load_saved_previews()
    noise_timer_running = True
    bpy.app.timers.register(update_noise_selection_timer)


def unregister() -> None:
    global noise_timer_running
    noise_timer_running = False
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.texture_importer_props


if __name__ == "__main__":
    register()
