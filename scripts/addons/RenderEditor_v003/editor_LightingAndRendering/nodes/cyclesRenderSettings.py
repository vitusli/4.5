import bpy
from . import utilityFunctions


class CyclesLightingRenderSettings(bpy.types.Node):
    """
    A node for setting Global Render Settings
    """
    bl_idname = "CyclesLightingRenderSettings"
    bl_label = "BlenderRenderSettings"
    bl_icon = "MOD_DECIM"

    renderer: bpy.props.EnumProperty(
        name="Renderer",
        description="Choose the renderer",
        items=[
            ("CYCLES", "Cycles", "Use Cycles rendering engine"),
            ("BLENDER_EEVEE", "Eevee", "Use Eevee rendering engine")
        ],
        default="CYCLES",
        update=lambda self, context: self.executeViewportCook()
    )

    resolutionWidth: bpy.props.IntProperty(
        name="Resolution Width",
        description="Width of the render resolution",
        default=1920,
        min=0,
        update=lambda self, context: self.executeViewportCook()
    )

    resolutionHeight: bpy.props.IntProperty(
        name="Resolution Height",
        description="Height of the render resolution",
        default=1080,
        min=0,
        update=lambda self, context: self.executeViewportCook()
    )

    resolutionScale: bpy.props.IntProperty(
        name="Resolution Scale",
        description="Scale of the render resolution",
        default=100,
        min=0,
        update=lambda self, context: self.executeViewportCook()
    )

    camera: bpy.props.PointerProperty(
        name="Camera",
        type=bpy.types.Object,
        description="Select a camera",
        poll=lambda self, obj: obj.type == 'CAMERA',
        update=lambda self, context: self.executeViewportCook()
    )

    compositing: bpy.props.BoolProperty(
        name="Compositing",
        default=False,
        description="Enable the compositor to run as a post-process",
        update=lambda self, context: self.executeViewportCook()
    )

    sequencer: bpy.props.BoolProperty(
        name="Sequencer",
        default=False,
        description="Enable the Sequencer to run as a post-process",
        update=lambda self, context: self.executeViewportCook()
    )

    output_format: bpy.props.EnumProperty(
        name="Output Format",
        description="Select the output file format",
        items=[
            ("PNG", "PNG", "Output as PNG"),
            ("JPEG", "JPEG", "Output as JPEG"),
            ("TIFF", "TIFF", "Output as TIFF"),
            ("OPEN_EXR", "OpenEXR", "Output as OpenEXR"),
            ("OPEN_EXR_MULTILAYER", "OpenEXR MultiLayer", "Output as OpenEXR MultiLayer"),
            ("HDR", "Radiance HDR", "Output as HDR"),
            ("BMP", "BMP", "Output as BMP"),
            ("TGA", "Targa", "Output as Targa"),
        ],
        default="OPEN_EXR",
        update=lambda self, context: self.executeViewportCook()
    )

    def init(self, context):
        """
        Initialize node sockets
        """
        self.width = 200
        self.inputs.new("NodeSocketCollection", "SceneInput")
        self.outputs.new("NodeSocketCollection", "SceneOutput")

    def draw_buttons(self, context, layout):
        """
        Draw the node layout and update labels dynamically
        """
        layout.label(text="Renderer Settings")
        layout.prop(self, "renderer", text="Renderer")

        layout.separator()
        layout.label(text="Resolution")
        layout.prop(self, "resolutionWidth", text="Width")
        layout.prop(self, "resolutionHeight", text="Height")
        layout.prop(self, "resolutionScale", text="Scale")

        layout.prop(self, "camera", text="Camera")

        layout.separator()
        layout.label(text="Post Processing")
        layout.prop(self, "compositing", text="Compositing")
        layout.prop(self, "sequencer", text="Sequencer")

        layout.separator()
        layout.label(text="Output Settings")
        layout.prop(self, "output_format", text="Format")

        # Cook node Button
        layout.operator("node.cook_scene_from_node", text="Cook Scene", icon="FILE_REFRESH")

    def executeNodeCookFunctions(self):
        utilityFunctions.setViewedNode(self)
        self.updateRenderAttributes()

    def executeViewportCook(self):
        viewedNode = utilityFunctions.getViewedNode()
        if self != viewedNode:
            return

        self.executeNodeCookFunctions()

    def updateRenderAttributes(self):
        scene = bpy.context.scene
        scene.render.engine = self.renderer
        scene.render.resolution_x = self.resolutionWidth
        scene.render.resolution_y = self.resolutionHeight
        scene.render.resolution_percentage = self.resolutionScale
        scene.camera = self.camera
        scene.render.use_compositing = self.compositing
        scene.render.use_sequencer = self.sequencer
        scene.render.image_settings.file_format = self.output_format

class NODE_OT_AddRenderSettings(bpy.types.Operator):
    """
    Add a Render Layer to the Custom Node Tree
    """
    bl_idname = "node.add_blender_render_settings_node"
    bl_label = "Add Render Settings Node"
    nodeType = "CyclesLightingRenderSettings"

    def execute(self, context):
        space = context.space_data
        if space and space.node_tree:
            newNode = space.node_tree.nodes.new(type=self.nodeType)
            newNode.location = (200, 200)
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "No active node tree found!")
            return {'CANCELLED'}

    def invoke(self, context, event):
        space = context.space_data
        nodes = space.node_tree.nodes

        bpy.ops.node.select_all(action='DESELECT')

        node = nodes.new(self.nodeType)
        node.select = True
        node.location = utilityFunctions.get_current_loc(context, event, context.preferences.system.ui_scale)

        bpy.ops.node.translate_attach_remove_on_cancel("INVOKE_DEFAULT")

        return {"FINISHED"}
