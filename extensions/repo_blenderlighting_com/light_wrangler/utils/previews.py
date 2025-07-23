import bpy
import bpy.utils.previews
import os
import re
import math
from .texture_manager import get_video_frame_rate_from_blender

# Global preview collections
gobo_previews = None
hdri_previews = None
ies_previews = None

def register_previews():
    """Register all preview collections and property enums."""
    from . import logger
    logger.start_section("Preview Collections")
    
    global gobo_previews, hdri_previews, ies_previews
    
    # First ensure any existing preview collections are properly removed
    unregister_previews_internal(skip_logging=True)
    
    # Initialize preview collections
    for preview_type in ['gobo', 'hdri', 'ies']:
        try:
            preview_collection = bpy.utils.previews.new()
            globals()[f'{preview_type}_previews'] = preview_collection
            logger.debug(f"Created {preview_type} preview collection")
        except Exception as e:
            logger.error(f"Failed to create {preview_type} preview collection: {e}")
    
    # Load preview images
    for preview_type in ['gobo', 'hdri', 'ies']:
        try:
            globals()[f'load_{preview_type}_previews']()
            logger.debug(f"Loaded {preview_type} preview images")
        except Exception as e:
            logger.error(f"Failed to load {preview_type} preview images: {e}")
    
    # Register property enums
    for preview_type in ['gobo', 'hdri', 'ies']:
        try:
            setattr(bpy.types.Light, f'{preview_type}_enum', bpy.props.EnumProperty(
                items=globals()[f'get_{preview_type}_items'],
                name=f"{preview_type.upper()} Texture" if preview_type != 'ies' else "IES Profile",
                description="",
                update=globals()[f'update_{preview_type}_texture']
            ))
            logger.debug(f"Registered {preview_type}_enum property on Light")
        except Exception as e:
            logger.error(f"Failed to register {preview_type}_enum property: {e}")
    
    logger.end_section()

def unregister_previews_internal(skip_logging=False):
    """Internal function to unregister previews without logging."""
    global gobo_previews, hdri_previews, ies_previews
    
    for preview_type in ['gobo', 'hdri', 'ies']:
        preview = globals().get(f'{preview_type}_previews')
        if preview is not None:
            try:
                bpy.utils.previews.remove(preview)
                if not skip_logging:
                    from . import logger
                    logger.debug(f"Removed {preview_type} preview collection")
            except Exception as e:
                if not skip_logging:
                    from . import logger
                    logger.error(f"Failed to remove {preview_type} previews: {e}")
            globals()[f'{preview_type}_previews'] = None
        
        if hasattr(bpy.types.Light, f'{preview_type}_enum'):
            try:
                delattr(bpy.types.Light, f'{preview_type}_enum')
                if not skip_logging:
                    from . import logger
                    logger.debug(f"Unregistered {preview_type}_enum property from Light")
            except Exception as e:
                if not skip_logging:
                    from . import logger
                    logger.error(f"Failed to unregister {preview_type}_enum property: {e}")

def unregister_previews():
    """Unregister and clean up all preview collections."""
    from . import logger
    logger.start_section("Preview Collections")
    
    unregister_previews_internal(skip_logging=False)
    
    logger.end_section()

def natural_sort_key(s):
    """Key function for natural sorting of strings with numbers."""
    return [
        int(text) if text.isdigit() else text.lower()
        for text in re.split("([0-9]+)", s)
    ]

def scan_and_generate_thumbnails():
    """Scan for video files and generate thumbnails if needed."""
    from .. import ADDON_MODULE_NAME
    addon_prefs = bpy.context.preferences.addons[ADDON_MODULE_NAME].preferences
    custom_folder_paths = [addon_prefs.gobo_path, addon_prefs.gobo_path_2, addon_prefs.gobo_path_3]
    video_extensions = ('.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm', '.ogv')
    videos_needing_thumbnails = []

    for folder_path in custom_folder_paths:
        if folder_path and os.path.exists(folder_path):
            for filename in os.listdir(folder_path):
                if filename.lower().endswith(video_extensions):
                    video_path = os.path.join(folder_path, filename)
                    thumbnail_path = os.path.join(folder_path, f"{os.path.splitext(filename)[0]}_thumb.png")
                    if not os.path.exists(thumbnail_path):
                        videos_needing_thumbnails.append((video_path, thumbnail_path))
        elif folder_path:
            print(f"Custom gobo folder path does not exist: {folder_path}")

    if videos_needing_thumbnails:
        for video_path, thumbnail_path in videos_needing_thumbnails:
            generate_thumbnail(video_path, thumbnail_path)

def generate_thumbnail(video_path, output_path):
    """Generate a thumbnail for a video file."""
    try:
        original_scene = bpy.context.scene
        scene = bpy.data.scenes.new(name="Thumbnail Scene")
        bpy.context.window.scene = scene

        # Set square resolution
        thumbnail_size = 200
        scene.render.resolution_x = thumbnail_size
        scene.render.resolution_y = thumbnail_size
        scene.render.filepath = output_path
        scene.render.image_settings.file_format = 'PNG'

        # Set color management
        scene.view_settings.view_transform = 'Standard'
        scene.view_settings.look = 'None'
        scene.display_settings.display_device = 'sRGB'

        if scene.sequence_editor is None:
            scene.sequence_editor_create()

        seq = scene.sequence_editor.sequences.new_movie(
            name=os.path.basename(video_path),
            filepath=video_path,
            channel=1,
            frame_start=1
        )

        scene.frame_start = 1
        scene.frame_end = seq.frame_final_duration
        middle_frame = seq.frame_final_duration // 2
        scene.frame_current = middle_frame

        # Calculate scaling and positioning
        scale_factor = thumbnail_size / seq.elements[0].orig_height
        scaled_width = seq.elements[0].orig_width * scale_factor

        if scaled_width > thumbnail_size:
            scale_factor = thumbnail_size / seq.elements[0].orig_width
            seq.transform.scale_x = scale_factor
            seq.transform.scale_y = scale_factor
            seq.transform.offset_y = (thumbnail_size - seq.elements[0].orig_height * scale_factor) / 2
        else:
            seq.transform.scale_x = scale_factor
            seq.transform.scale_y = scale_factor
            seq.transform.offset_x = (thumbnail_size - scaled_width) / 2

        # Set color space
        seq.colorspace_settings.name = 'sRGB'
        scene.sequencer_colorspace_settings.name = 'sRGB'

        bpy.ops.render.render(write_still=True)
        
        bpy.data.scenes.remove(scene)
        bpy.context.window.scene = original_scene
        
        print(f"Generated thumbnail for {os.path.basename(video_path)}")
    except Exception as e:
        print(f"Error generating thumbnail for {os.path.basename(video_path)}:")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        import traceback
        traceback.print_exc()

def load_gobo_previews():
    """Load gobo preview images into the preview collection."""
    global gobo_previews
    from .. import ADDON_MODULE_NAME
    
    try:
        if gobo_previews is not None:
            bpy.utils.previews.remove(gobo_previews)
            gobo_previews = None
    except Exception as e:
        print("Failed to remove gobo previews:", e)

    gobo_previews = bpy.utils.previews.new()

    # Load built-in previews
    gobo_previews_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "gobo_previews")
    if os.path.exists(gobo_previews_dir):
        load_images_from_gobo_folder(gobo_previews_dir, is_builtin=True)

    # Load custom previews only if preferences are available
    try:
        addon_prefs = bpy.context.preferences.addons[ADDON_MODULE_NAME].preferences
        if addon_prefs:
            custom_folder_paths = [addon_prefs.gobo_path, addon_prefs.gobo_path_2, addon_prefs.gobo_path_3]
            for custom_folder_path in custom_folder_paths:
                if custom_folder_path:
                    load_images_from_gobo_folder(custom_folder_path)
    except (AttributeError, KeyError):
        print("Addon preferences not available yet, skipping custom gobo paths")

def load_images_from_gobo_folder(folder_path, is_builtin=False):
    """Load images from a gobo folder into the preview collection."""
    if not folder_path:
        return

    filenames = [
        os.path.join(folder_path, f)
        for f in os.listdir(folder_path)
        if f.lower().endswith((".jpg", ".png", ".webp"))
    ]
    filenames.sort(key=lambda x: natural_sort_key(os.path.basename(x)))

    for filename in filenames:
        filepath = filename if is_builtin else os.path.join(folder_path, filename)
        name = os.path.basename(filepath) if is_builtin else "user:" + os.path.basename(filepath)

        if name not in gobo_previews:
            try:
                gobo_previews.load(name, filepath, "IMAGE")
            except RuntimeError as e:
                print(f"Error loading {name}: {e}")
        else:
            print(f"Skipping duplicate preview for {name}")

def load_hdri_previews():
    """Load HDRI preview images into the preview collection."""
    global hdri_previews
    from .. import ADDON_MODULE_NAME

    try:
        if hdri_previews is not None:
            bpy.utils.previews.remove(hdri_previews)
            hdri_previews = None
    except Exception as e:
        print("Failed to remove HDRI previews:", e)

    hdri_previews = bpy.utils.previews.new()

    # Load built-in previews
    folder1_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "hdri_previews")
    if os.path.exists(folder1_path):
        load_images_from_folder(folder1_path, is_builtin=True)

    # Load custom previews only if preferences are available
    try:
        addon_prefs = bpy.context.preferences.addons[ADDON_MODULE_NAME].preferences
        if addon_prefs:
            custom_folder_paths = [addon_prefs.hdri_path, addon_prefs.hdri_path_2, addon_prefs.hdri_path_3]
            for custom_folder_path in custom_folder_paths:
                if custom_folder_path:
                    load_images_from_folder(custom_folder_path)
    except (AttributeError, KeyError):
        print("Addon preferences not available yet, skipping custom HDRI paths")

def load_images_from_folder(folder_path, is_builtin=False):
    """Load images from an HDRI folder into the preview collection."""
    if not folder_path or not os.path.exists(folder_path):
        return

    filenames = [
        os.path.join(folder_path, f)
        for f in os.listdir(folder_path)
        if f.lower().endswith((".jpg", ".png", ".hdr", ".exr", ".tif", ".tiff", ".webp"))
    ]
    filenames.sort(key=lambda x: natural_sort_key(os.path.basename(x)))

    for filename in filenames:
        filepath = os.path.join(folder_path, filename) if is_builtin else filename
        name = os.path.basename(filepath) if is_builtin else "user:" + filename
        hdri_previews.load(name, filepath, "IMAGE")

def load_ies_previews():
    """Load IES preview images into the preview collection."""
    global ies_previews
    from .. import ADDON_MODULE_NAME

    if ies_previews is not None:
        bpy.utils.previews.remove(ies_previews)
    ies_previews = bpy.utils.previews.new()

    # Load built-in IES previews
    ies_previews_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ies_previews")
    if os.path.exists(ies_previews_dir):
        load_ies_from_folder(ies_previews_dir, is_builtin=True)

    # Load custom IES previews only if preferences are available
    try:
        addon_prefs = bpy.context.preferences.addons[ADDON_MODULE_NAME].preferences
        if addon_prefs and addon_prefs.ies_profiles_path and addon_prefs.ies_previews_path:
            if os.path.exists(addon_prefs.ies_profiles_path) and os.path.exists(addon_prefs.ies_previews_path):
                load_ies_from_folder(addon_prefs.ies_previews_path, addon_prefs.ies_profiles_path)
            else:
                print("One or both of the specified IES folders do not exist.")
    except (AttributeError, KeyError):
        print("Addon preferences not available yet, skipping custom IES paths")

def load_ies_from_folder(previews_folder, profiles_folder=None, is_builtin=False):
    """Load IES preview images from a folder into the preview collection."""
    if os.path.exists(previews_folder):
        for filename in os.listdir(previews_folder):
            if filename.lower().endswith((".png", ".jpg", ".jpeg")):
                preview_path = os.path.join(previews_folder, filename)
                ies_filename = os.path.splitext(filename)[0] + ".ies"
                
                if is_builtin or (profiles_folder and os.path.exists(os.path.join(profiles_folder, ies_filename))):
                    identifier = f"{'builtin:' if is_builtin else 'user:'}{ies_filename}"
                    ies_previews.load(identifier, preview_path, 'IMAGE')

def get_gobo_items(self, context):
    """Get the list of gobo items for the enum property."""
    enum_items = []
    if context is None:
        return enum_items

    for idx, (name, preview) in enumerate(gobo_previews.items()):
        enum_items.append((name, "", "", preview.icon_id, idx))

    return enum_items

def get_hdri_items(self, context):
    """Get the list of HDRI items for the enum property."""
    enum_items = []
    if context is None:
        return enum_items

    for idx, (name, preview) in enumerate(hdri_previews.items()):
        is_builtin = not name.startswith("user:")
        path = name if is_builtin else name[5:]
        enum_items.append((path, "", "", preview.icon_id, idx))

    return enum_items

def get_ies_items(self, context):
    """Get the list of IES items for the enum property."""
    enum_items = []
    if context is None:
        return enum_items

    for idx, (name, preview) in enumerate(ies_previews.items()):
        enum_items.append((name, "", "", preview.icon_id, idx))

    return enum_items

def update_gobo_texture(self, context):
    """Update handler for when a gobo texture is selected."""
    from .texture_manager import apply_gobo_to_light
    light = context.object
    gobo_name = bpy.path.basename(self.gobo_enum)
    apply_gobo_to_light(light, gobo_name)

def update_hdri_texture(self, context):
    """Update handler for when an HDRI texture is selected."""
    from .texture_manager import apply_hdri_to_light
    light = context.object
    hdri_path = self.hdri_enum
    apply_hdri_to_light(light, hdri_path)

def update_ies_texture(self, context):
    """Update handler for when an IES profile is selected."""
    from .texture_manager import apply_ies_to_light
    light = context.object
    ies_name = bpy.path.basename(self.ies_enum)
    apply_ies_to_light(light, ies_name)

def update_all_gobo_drivers():
    """Update all Gobo drivers in the scene."""
    project_fps = bpy.context.scene.render.fps
    
    # Update lights with Gobo Light node groups
    for light in bpy.data.lights:
        if light.use_nodes:
            for node in light.node_tree.nodes:
                if (node.type == "GROUP" and 
                    node.node_tree and 
                    "Gobo Light" in node.node_tree.name):
                    update_video_drivers_in_node_group(node.node_tree, project_fps)
    
    # Update materials with Gobo Stencil node groups
    for mat in bpy.data.materials:
        if mat.use_nodes:
            for node in mat.node_tree.nodes:
                if (node.type == "GROUP" and 
                    node.node_tree and 
                    "Gobo Stencil" in node.node_tree.name):
                    update_video_drivers_in_node_group(node.node_tree, project_fps)

def update_video_drivers_in_node_group(node_tree, project_fps):
    """Helper function to update video drivers in a node group."""
    for tex_node in node_tree.nodes:
        if (tex_node.type == "TEX_IMAGE" and 
            tex_node.image and 
            hasattr(tex_node.image, 'filepath') and
            is_video_file(tex_node.image.filepath)):
            
            try:
                video_fps = get_video_frame_rate_from_blender(tex_node.image.filepath)
                if video_fps:
                    speed_factor = video_fps / project_fps
                    
                    tex_node.image_user.driver_remove("frame_offset")
                    driver = tex_node.image_user.driver_add("frame_offset").driver
                    driver.type = 'SCRIPTED'
                    driver.expression = f"frame * {speed_factor} % {tex_node.image.frame_duration}"
            except Exception as e:
                print(f"Error updating driver in {node_tree.name}: {e}")

def is_video_file(file_path):
    """Check if a file is a video file based on its extension."""
    video_extensions = [
        ".mp4",
        ".m4v",
        ".avi",
        ".mov",
        ".wmv",
        ".flv",
        ".mkv",
        ".webm",
        ".ogv",
    ]
    return any(file_path.lower().endswith(ext) for ext in video_extensions) 