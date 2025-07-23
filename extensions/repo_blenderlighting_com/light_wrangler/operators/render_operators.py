import bpy
import os
import tempfile
import subprocess
import json
from bpy.props import StringProperty, IntProperty, BoolProperty
import time
import platform
from .. import ADDON_MODULE_NAME

# Global variable to store render info
_render_info = {
    'filepath': None,
    'temp_dir': None,
    'temp_blend': None,
    'script_path': None
}

class LIGHTW_OT_Render360HDRI(bpy.types.Operator):
    """Save a 360° HDRI image of the current scene, capturing all lighting and world settings at the specified resolution"""
    bl_idname = "lightwrangler.render_360_hdri"
    bl_label = "Render 360 HDRI"

    filepath: StringProperty(subtype='FILE_PATH', default="")
    resolution_x: IntProperty(name="Width", default=2048)  # Default to 2K width
    resolution_y: IntProperty(name="Height", default=1024)  # Default to 2K height
    has_emissive_objects: BoolProperty(default=False, options={'SKIP_SAVE'})
    is_file_selected: BoolProperty(default=False, options={'SKIP_SAVE'})
    
    # Add modal properties
    _timer = None
    _process = None
    _start_time = 0

    def modal(self, context, event):
        if event.type == 'TIMER':
            print("\n=== MODAL UPDATE ===")
            if not self._process:
                print("Debug: Process not found")
                return {'FINISHED'}
                
            # Check if process is still running
            poll_result = self._process.poll()
            print(f"Debug: Process poll result: {poll_result}")
            
            if poll_result is not None:
                # Process finished
                print(f"Debug: Process finished with return code: {poll_result}")
                try:
                    remaining_stdout, remaining_stderr = self._process.communicate()
                    print("Debug: Successfully communicated with finished process")
                    
                    # Print any remaining output
                    if remaining_stdout:
                        print("Debug: Final stdout output:")
                        for line in remaining_stdout.splitlines():
                            print(f"Render process: {line.strip()}")
                    else:
                        print("Debug: No stdout output")
                        
                    if remaining_stderr:
                        print("Debug: Final stderr output:")
                        for line in remaining_stderr.splitlines():
                            print(f"Render error: {line.strip()}")
                    else:
                        print("Debug: No stderr output")
                except Exception as e:
                    print(f"Debug: Error during final communication: {str(e)}")
                
                # Get info from class variable
                render_info = LIGHTW_OT_Render360HDRI._render_info
                print(f"Debug: Render info: {render_info}")
                
                # Check if output file exists
                if os.path.exists(render_info['filepath']):
                    print(f"Debug: Output file exists: {render_info['filepath']}")
                    print(f"Debug: File size: {os.path.getsize(render_info['filepath'])} bytes")
                else:
                    print(f"Debug: Output file does not exist: {render_info['filepath']}")
                
                # Cleanup
                try:
                    os.remove(render_info['script_path'])
                    print("Debug: Removed script file")
                    os.remove(render_info['temp_blend'])
                    print("Debug: Removed temp blend file")
                    os.rmdir(render_info['temp_dir'])
                    print("Debug: Removed temp directory")
                except Exception as e:
                    print(f"Debug: Cleanup failed: {str(e)}")
                
                # Remove timer
                try:
                    context.window_manager.event_timer_remove(self._timer)
                    print("Debug: Removed modal timer")
                except Exception as e:
                    print(f"Debug: Failed to remove timer: {str(e)}")
                
                # Clear status text
                context.workspace.status_text_set(None)
                
                # Show completion message
                if self._process.returncode == 0:
                    print(f"Debug: Render completed successfully: {render_info['filepath']}")
                    self.report({'INFO'}, f"HDRI Rendered: {render_info['filepath']}")
                else:
                    print(f"Debug: Render failed with return code: {self._process.returncode}")
                    self.report({'ERROR'}, "HDRI Render failed")
                
                # Clear render info and process
                LIGHTW_OT_Render360HDRI._render_info = {}
                self._process = None
                print("=== RENDER PROCESS COMPLETE ===\n")
                
                return {'FINISHED'}
            
            # Process still running - read output non-blocking
            print("Debug: Process still running, attempting to read output")
            if platform.system() != 'Windows':
                # Unix systems - use non-blocking IO
                try:
                    while True:
                        line = self._process.stdout.readline()
                        if not line:
                            break
                        print(f"Render process: {line.strip()}")
                except IOError as e:
                    print(f"Debug: IOError reading stdout: {str(e)}")
                
                try:
                    while True:
                        line = self._process.stderr.readline()
                        if not line:
                            break
                        print(f"Render error: {line.strip()}")
                except IOError as e:
                    print(f"Debug: IOError reading stderr: {str(e)}")
            else:
                # Windows - use communicate with timeout
                try:
                    stdout, stderr = self._process.communicate(timeout=0.1)
                    if stdout:
                        print(f"Render process: {stdout.strip()}")
                    if stderr:
                        print(f"Render error: {stderr.strip()}")
                except subprocess.TimeoutExpired:
                    print("Debug: Windows communicate timeout (expected)")
                except Exception as e:
                    print(f"Debug: Windows subprocess error: {str(e)}")
            
            # Update status message
            elapsed_time = int(time.time() - self._start_time)
            context.workspace.status_text_set(f"Rendering HDRI... ({elapsed_time//60}m {elapsed_time%60}s)")
            print(f"Debug: Elapsed time: {elapsed_time} seconds")
            
            return {'PASS_THROUGH'}
        
        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        prefs = context.preferences.addons[ADDON_MODULE_NAME].preferences
        default_directory = prefs.last_360_hdri_directory if hasattr(prefs, 'last_360_hdri_directory') and prefs.last_360_hdri_directory else os.path.join(os.path.expanduser("~"), "Pictures")
        
        if not os.path.exists(default_directory):
            default_directory = os.path.expanduser("~")

        resolution_map = {2048: "2K", 4096: "4K", 8192: "8K", 16384: "16K"}
        resolution_suffix = resolution_map.get(self.resolution_x, "2K")
        blend_name = bpy.path.basename(bpy.context.blend_data.filepath)
        project_name = os.path.splitext(blend_name)[0] if bpy.context.blend_data.filepath else "Untitled"
        filename = f"{project_name}_HDRI_{resolution_suffix}.exr"
        self.filepath = os.path.join(default_directory, filename)

        # Check for emissive objects
        self.has_emissive_objects = self.check_emissive_objects(context)

        if self.has_emissive_objects:
            # Show confirmation dialog
            return context.window_manager.invoke_props_dialog(self)
        else:
            # Proceed to file selection
            context.window_manager.fileselect_add(self)
            return {'RUNNING_MODAL'}

    def draw(self, context):
        if self.has_emissive_objects and not self.is_file_selected:
            layout = self.layout
            row = layout.row()
            row.alignment = 'LEFT'
            row.label(text="Warning: Emissive Objects Detected", icon='ERROR')
            
            layout.separator(factor=1.0)
            
            col = layout.column(align=True)
            col.scale_y = 0.85
            col.label(text="This scene contains emissive objects.")
            col.label(text="Rendering may take up to 20 minutes or longer,")
            col.label(text="depending on your output resolution.")
            col.label(text="The main Blender window will remain responsive.")
            
            layout.separator(factor=0.5)

    def check_emissive_objects(self, context):
        """Check if scene contains any emissive objects"""
        # Check each object in the scene for emissive materials
        for obj in context.scene.objects:
            if (obj.type == 'MESH' and 
                not obj.hide_render and 
                obj.visible_get() and 
                self.is_emission_object(obj)):
                return True  # Emissive object found

        return False  # No emissive objects detected

    def is_emission_object(self, obj):
        """Helper method to check if an object is emissive"""
        if obj.type == 'MESH' and obj.active_material:
            emission_nodes = self.get_emission_nodes(obj)
            for node in emission_nodes:
                if node.type == 'EMISSION' and node.inputs['Strength'].default_value > 0:
                    return True
                elif (node.type == 'BSDF_PRINCIPLED' and 
                      'Emission Strength' in node.inputs and 
                      node.inputs['Emission Strength'].default_value > 0):
                    return True
        return False

    def get_emission_nodes(self, obj):
        """Helper method to get emission nodes from an object"""
        emission_nodes = []
        if obj.active_material:
            for mat_slot in obj.material_slots:
                if mat_slot.material and mat_slot.material.node_tree:
                    emission_nodes.extend(self.get_emission_nodes_from_tree(mat_slot.material.node_tree))
        return emission_nodes

    def get_emission_nodes_from_tree(self, node_tree):
        """Helper method to get emission nodes from a node tree"""
        emission_nodes = []
        if node_tree is None or not hasattr(node_tree, 'nodes'):
            return emission_nodes
        for node in node_tree.nodes:
            if node.type in {'EMISSION', 'BSDF_PRINCIPLED'}:
                if node.type == 'EMISSION' or (node.type == 'BSDF_PRINCIPLED' and 'Emission Strength' in node.inputs):
                    emission_nodes.append(node)
            elif node.type == 'GROUP' and node.node_tree is not None:
                emission_nodes.extend(self.get_emission_nodes_from_tree(node.node_tree))
        return emission_nodes

    def execute(self, context):
        print("\n=== HDRI RENDER STARTING ===")
        print(f"Debug: Platform: {platform.system()}")
        
        if self.has_emissive_objects and not self.is_file_selected:
            print("Debug: Has emissive objects, showing file selector")
            self.is_file_selected = True
            context.window_manager.fileselect_add(self)
            return {'RUNNING_MODAL'}

        print(f"Debug: Output filepath: {self.filepath}")
        print(f"Debug: Resolution: {self.resolution_x}x{self.resolution_y}")

        # Get list of objects to render
        objects_to_render = []
        for obj in context.scene.objects:
            should_copy = False
            
            # Check for lights - must be visible
            if (obj.type == 'LIGHT' and 
                not obj.hide_render and obj.visible_get()):
                should_copy = True
                print(f"Debug: Found light to render: {obj.name}")
                
            # Check for emissive meshes - must be visible
            elif (obj.type == 'MESH' and 
                  not obj.hide_render and obj.visible_get()):
                if self.is_emission_object(obj):
                    should_copy = True
                    print(f"Debug: Found emissive mesh to render: {obj.name}")
            
            if should_copy:
                objects_to_render.append(obj.name)

        print(f"Debug: Total objects to render: {len(objects_to_render)}")

        # Create temporary directory
        try:
            temp_dir = tempfile.mkdtemp()
            print(f"Debug: Created temp dir: {temp_dir}")
        except Exception as e:
            print(f"Debug: Failed to create temp dir: {str(e)}")
            self.report({'ERROR'}, "Failed to create temporary directory")
            return {'CANCELLED'}
        
        # Save current scene state
        temp_blend = os.path.join(temp_dir, "temp_scene.blend")
        try:
            bpy.ops.wm.save_as_mainfile(filepath=temp_blend, copy=True)
            print(f"Debug: Saved temp blend file: {temp_blend}")
        except Exception as e:
            print(f"Debug: Failed to save temp blend: {str(e)}")
            self.report({'ERROR'}, "Failed to save temporary blend file")
            return {'CANCELLED'}
        
        # Generate Python script
        try:
            script_content = self.generate_render_script(
                blend_path=temp_blend,
                output_path=self.filepath,
                resolution_x=self.resolution_x,
                resolution_y=self.resolution_y,
                objects_to_render=objects_to_render
            )
            
            script_path = os.path.join(temp_dir, "render_hdri.py")
            with open(script_path, 'w') as f:
                f.write(script_content)
            print(f"Debug: Created render script: {script_path}")
        except Exception as e:
            print(f"Debug: Failed to create render script: {str(e)}")
            self.report({'ERROR'}, "Failed to create render script")
            return {'CANCELLED'}
        
        # Store render info in class variable
        LIGHTW_OT_Render360HDRI._render_info = {
            'filepath': self.filepath,
            'temp_dir': temp_dir,
            'temp_blend': temp_blend,
            'script_path': script_path
        }
        print("Debug: Stored render info in class variable")
        
        # Launch subprocess with non-blocking IO
        try:
            blender_path = bpy.app.binary_path
            print(f"Debug: Using Blender path: {blender_path}")
            
            cmd = [blender_path, "--factory-startup", "-b", temp_blend, "--python", script_path]
            print(f"Debug: Command to execute: {' '.join(cmd)}")
            
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1,
                start_new_session=True
            )
            print(f"Debug: Started subprocess with PID: {self._process.pid}")
            
            # Make pipes non-blocking on Unix systems only
            if platform.system() != 'Windows':
                print("Debug: Setting up non-blocking pipes for Unix")
                import fcntl
                for pipe in [self._process.stdout, self._process.stderr]:
                    fd = pipe.fileno()
                    fl = fcntl.fcntl(fd, fcntl.F_GETFL)
                    fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
            else:
                print("Debug: Windows system - skipping non-blocking pipe setup")
            
        except Exception as e:
            print(f"Debug: Failed to start subprocess: {str(e)}")
            self.report({'ERROR'}, "Failed to start render process")
            return {'CANCELLED'}
        
        # Start modal timer
        try:
            self._start_time = time.time()
            wm = context.window_manager
            self._timer = wm.event_timer_add(0.1, window=context.window)
            wm.modal_handler_add(self)
            print("Debug: Started modal timer")
        except Exception as e:
            print(f"Debug: Failed to start modal timer: {str(e)}")
            self.report({'ERROR'}, "Failed to start render monitoring")
            return {'CANCELLED'}
        
        context.workspace.status_text_set("Starting HDRI render...")
        print("=== HDRI RENDER PROCESS STARTED ===\n")
        
        return {'RUNNING_MODAL'}

    def generate_render_script(self, blend_path, output_path, resolution_x, resolution_y, objects_to_render):
        """Generates the Python script that will run in the subprocess"""
        # Convert paths to use forward slashes for cross-platform compatibility
        output_path = output_path.replace('\\', '/')
        blend_path = blend_path.replace('\\', '/')
        
        script = f'''
import bpy
import math
import os

def get_emission_nodes_from_tree(node_tree):
    emission_nodes = []
    if node_tree is None or not hasattr(node_tree, 'nodes'):
        return emission_nodes
    for node in node_tree.nodes:
        if node.type in {{'EMISSION', 'BSDF_PRINCIPLED'}}:
            if node.type == 'EMISSION' or (node.type == 'BSDF_PRINCIPLED' and 'Emission Strength' in node.inputs):
                emission_nodes.append(node)
        elif node.type == 'GROUP' and node.node_tree is not None:
            emission_nodes.extend(get_emission_nodes_from_tree(node.node_tree))
    return emission_nodes

def get_emission_nodes(obj):
    emission_nodes = []
    if obj.active_material:
        for mat_slot in obj.material_slots:
            if mat_slot.material and mat_slot.material.node_tree:
                emission_nodes.extend(get_emission_nodes_from_tree(mat_slot.material.node_tree))
    return emission_nodes

def main():
    print("=== Starting HDRI render process ===")
    
    # Load the original scene
    original_scene = bpy.context.scene
    objects_to_render = {objects_to_render}  # List of object names to render
    
    print(f"Original scene: {{original_scene.name}}")
    print(f"Objects to render: {{objects_to_render}}")
    
    # Create new scene for HDRI rendering
    hdri_scene = bpy.data.scenes.new("HDRIScene")
    bpy.context.window.scene = hdri_scene
    print("Created new HDRIScene")
    
    # Copy world settings if they exist
    if original_scene.world:
        hdri_scene.world = original_scene.world.copy()
        print(f"Copied world settings from {{original_scene.world.name}}")
    
    # Create 360 camera
    cam_data = bpy.data.cameras.new("360Camera")
    cam_obj = bpy.data.objects.new("360Camera", cam_data)
    cam_data.type = 'PANO'
    cam_data.panorama_type = 'EQUIRECTANGULAR'
    cam_data.clip_start = 0.00001
    cam_data.clip_end = 999999
    
    hdri_scene.collection.objects.link(cam_obj)
    hdri_scene.camera = cam_obj
    cam_obj.location = original_scene.cursor.location
    cam_obj.rotation_euler = (math.radians(90), 0, math.radians(-90))
    print("Created and set up 360 camera")
    
    # Copy only the objects we selected in main operator
    copied_objects = []
    for obj_name in objects_to_render:
        obj = original_scene.objects.get(obj_name)
        if not obj:
            print(f"Warning: Could not find object {{obj_name}}")
            continue
            
        # Create copy with data
        new_obj = obj.copy()
        if obj.data:
            new_obj.data = obj.data.copy()
            print(f"Copied data for {{obj.name}}")
            
        # Copy materials for meshes
        if obj.type == 'MESH':
            for i, mat_slot in enumerate(obj.material_slots):
                if mat_slot.material:
                    new_obj.material_slots[i].material = mat_slot.material.copy()
                    print(f"Copied material {{mat_slot.material.name}} for {{obj.name}}")
        
        # Special handling for lights
        if obj.type == 'LIGHT':
            # Ensure light data is properly copied
            new_obj.data = obj.data.copy()
            print(f"Copied light data for {{obj.name}}")
            new_obj.data.energy = obj.data.energy
            print(f"Copied light energy: {{obj.data.energy}}")
            if hasattr(obj.data, 'color'):
                new_obj.data.color = obj.data.color
                print(f"Copied light color: {{list(obj.data.color)}}")
        
        # Force the object to be visible in the new scene
        new_obj.hide_render = False
        new_obj.hide_viewport = False
        new_obj.visible_camera = True
        
        hdri_scene.collection.objects.link(new_obj)
        copied_objects.append(new_obj)
        print(f"Linked {{new_obj.name}} to HDRIScene")
    
    print(f"Copied objects summary:")
    print(f"Total objects copied: {{len(copied_objects)}}")
    print(f"Copied objects: {{[obj.name for obj in copied_objects]}}")
    print(f"Copied lights: {{[obj.name for obj in copied_objects if obj.type == 'LIGHT']}}")
    
    # Setup render settings
    hdri_scene.render.resolution_x = {resolution_x}
    hdri_scene.render.resolution_y = {resolution_y}
    hdri_scene.render.image_settings.file_format = 'OPEN_EXR'
    hdri_scene.render.image_settings.exr_codec = 'PXR24'
    hdri_scene.render.image_settings.color_mode = 'RGB'
    hdri_scene.render.image_settings.color_depth = '32'
    hdri_scene.render.engine = 'CYCLES'
    print("Set up render settings")
    
    # Cycles settings
    cycles = hdri_scene.cycles
    
    # Enable adaptive sampling if available
    if hasattr(cycles, 'use_adaptive_sampling'):
        cycles.use_adaptive_sampling = True
        print("Enabled adaptive sampling")
    
    # Basic cycles settings
    cycles.max_bounces = 1
    cycles.diffuse_bounces = 1
    cycles.glossy_bounces = 1
    cycles.transmission_bounces = 1
    cycles.volume_bounces = 0
    print("Set basic cycles settings")
    
    # Set sampling pattern if available
    if hasattr(cycles, 'sampling_pattern'):
        cycles.sampling_pattern = 'TABULATED_SOBOL'
        print("Set sampling pattern to TABULATED_SOBOL")
    
    # Determine compute device
    try:
        prefs = bpy.context.preferences
        cycles_prefs = prefs.addons['cycles'].preferences
        compute_device_type = cycles_prefs.compute_device_type
        print(f"Available compute device type: {{compute_device_type}}")
        
        if {resolution_x} in {{2048, 4096}}:
            if compute_device_type in {{'CUDA', 'OPTIX', 'METAL'}}:
                cycles.device = 'GPU'
                print(f"Using GPU ({{compute_device_type}}) for rendering")
            else:
                cycles.device = 'CPU'
                print("Using CPU for rendering (no compatible GPU found)")
        else:
            cycles.device = 'CPU'
            print("Using CPU for rendering (high resolution)")
    except Exception as e:
        cycles.device = 'CPU'
        print(f"Using CPU for rendering (error: {{str(e)}})")
    
    # Set samples based on scene content
    has_emissive = any(obj.type == 'MESH' for obj in hdri_scene.objects)
    if has_emissive:
        cycles.samples = 10
        cycles.use_denoising = True
        print("Set samples=10 and enabled denoising (emissive objects present)")
    else:
        cycles.samples = 1
        cycles.use_denoising = False
        print("Set samples=1 and disabled denoising (no emissive objects)")
    
    # Additional cycles settings
    cycles.clamp_direct = 0.0
    cycles.clamp_indirect = 10000
    cycles.filter_glossy = 0.0
    if hasattr(cycles, 'use_auto_tile'):
        cycles.use_auto_tile = False
    print("Set additional cycles settings")
    
    # Set output path and render
    hdri_scene.render.filepath = '{output_path}'
    print("Starting render...")
    bpy.ops.render.render(write_still=True, scene=hdri_scene.name)

if __name__ == "__main__":
    main()
'''
        return script

class LIGHTW_OT_ShowRenderComplete(bpy.types.Operator):
    bl_idname = "lightw.show_render_complete"
    bl_label = "HDRI Render Complete"
    bl_description = "HDRI render completed successfully"
    
    filepath: StringProperty()
    
    def execute(self, context):
        self.report({'INFO'}, f"HDRI Rendered: {self.filepath}")
        return {'FINISHED'}

class LIGHTW_OT_ShowRenderError(bpy.types.Operator):
    bl_idname = "lightw.show_render_error"
    bl_label = "HDRI Render Failed"
    bl_description = "HDRI render failed"
    
    def execute(self, context):
        self.report({'ERROR'}, "HDRI Render failed. Check console for details.")
        return {'FINISHED'}

# Registration
classes = (
    LIGHTW_OT_Render360HDRI,
    LIGHTW_OT_ShowRenderComplete,
    LIGHTW_OT_ShowRenderError,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls) 