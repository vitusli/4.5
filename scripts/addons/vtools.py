bl_info = {
    "name": "VTools",
    "blender": (4, 0, 1),
    "category": "Node",
}

import bpy

class CustomCompositorPanel(bpy.types.Panel): #label und gui
    bl_label = "VTools"
    bl_idname = "PT_CustomCompositorPanel"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'VTools'

    def draw(self, context): #gui
        layout = self.layout
        scene = context.scene
        
        row = layout.row(align=True)
        row.prop(context.scene, "DenoiseDropDown", text="Denoise")
        row.operator("scene.denoise_dropdown_action", text="", icon='PLUS')

        row = layout.row(align=True)
        row.prop(context.scene, "MaskDropDown", text="Mask")
        row.operator("scene.add_mask_operator", text="", icon='PLUS')

        layout.prop(scene, "custom_checkbox_denoise", text="Mute All Denoise Nodes")

############################################ global definition
def update_denoise_nodes(scene, context):
    for node in scene.node_tree.nodes:
        if node.type == 'DENOISE':
            node.mute = scene.custom_checkbox_denoise

def place_nodes_relative_to(node, nodes, offset_x = 100, offset_y = 0):
    first_top_edge = node.location.y 
    last_node = node
    for n in nodes:
        n.location.x = last_node.location.x + last_node.width + offset_x
        n.location.y = first_top_edge + offset_y
        last_node = n

def deselect_all_nodes():
    for node_tree in bpy.context.scene.node_tree.nodes:
        node_tree.select = False
############################################

class AddDenoiserOperator(bpy.types.Operator):
    bl_idname = "scene.denoise_dropdown_action"
    bl_label = "Add noise reduction setup"
    
    def execute(self, context): #first dropdown menu

        for view_layer in bpy.context.scene.view_layers:
            view_layer.use_pass_ambient_occlusion = True
            view_layer.use_pass_mist = True
            view_layer.use_pass_transmission_indirect = True
            view_layer.use_pass_cryptomatte_object = True
            view_layer.use_pass_cryptomatte_material = True
            view_layer.use_pass_cryptomatte_asset = True
            view_layer.cycles.denoising_store_passes = True

        bpy.context.scene.use_nodes = True
        selected_option = context.scene.DenoiseDropDown
        tree = bpy.context.scene.node_tree
        node = tree.nodes
        link = tree.links.new
        composite = node.get("Composite")
        render_layers = node.get("Render Layers")
        deselect_all_nodes() #must be under def of "tree"
        
        if selected_option == 'denoise':

            denoise_node = node.new(type='CompositorNodeDenoise')

            link(render_layers.outputs["Image"], denoise_node.inputs["Image"])
            link(render_layers.outputs["Denoising Albedo"], denoise_node.inputs["Albedo"])
            link(render_layers.outputs["Denoising Normal"], denoise_node.inputs["Normal"])
            link(denoise_node.outputs["Image"], composite.inputs["Image"])
        
            if render_layers:
                place_nodes_relative_to(render_layers, [denoise_node], offset_x=30)

        if selected_option == 'denoise_mixer':

            denoise_node = node.new(type='CompositorNodeDenoise')
            mix = node.new(type='CompositorNodeMixRGB')
            mix.inputs['Fac'].default_value = 0.5
  
            link(render_layers.outputs["Image"], denoise_node.inputs["Image"])
            link(render_layers.outputs["Denoising Albedo"], denoise_node.inputs["Albedo"])                
            link(render_layers.outputs["Denoising Normal"], denoise_node.inputs["Normal"])
            link(render_layers.outputs["Image"], mix.inputs[1])
            link(denoise_node.outputs["Image"], mix.inputs[2])
            link(mix.outputs["Image"], composite.inputs["Image"])
            
            if render_layers:
                place_nodes_relative_to(render_layers, [denoise_node, mix], offset_x=30)
              
        if selected_option == 'denoise_crypto':

            denoise_node = node.new(type='CompositorNodeDenoise')
            mix1 = node.new(type='CompositorNodeMixRGB')
            mix1.inputs['Fac'].default_value = 0.2
            mix2 = node.new(type='CompositorNodeMixRGB')
            mix2.inputs['Fac'].default_value = 0.8
            mix3 = node.new(type='CompositorNodeMixRGB')
            cryptomatte_node = node.new(type='CompositorNodeCryptomatteV2')

            link(render_layers.outputs["Image"], denoise_node.inputs["Image"])
            link(render_layers.outputs["Denoising Albedo"], denoise_node.inputs["Albedo"])                
            link(render_layers.outputs["Denoising Normal"], denoise_node.inputs["Normal"])
            link(render_layers.outputs["Image"], mix1.inputs[1])
            link(denoise_node.outputs["Image"], mix1.inputs[2])
            link(render_layers.outputs["Image"], mix2.inputs[1])
            link(denoise_node.outputs["Image"], mix2.inputs[2])           
            link(mix1.outputs["Image"], mix3.inputs[1])
            link(mix2.outputs["Image"], mix3.inputs[2])
            link(cryptomatte_node.outputs["Matte"], mix3.inputs[0])
            link(render_layers.outputs["Image"], cryptomatte_node.inputs["Image"])
            link(mix3.outputs["Image"], composite.inputs["Image"])

            if render_layers:
                place_nodes_relative_to(render_layers, [cryptomatte_node, denoise_node, mix1, mix2, mix3], offset_x=30)

        if selected_option == 'denoise_alpha':

            denoise_node = node.new(type='CompositorNodeDenoise')
            setalpha_node = node.new(type='CompositorNodeSetAlpha')
            
            link(render_layers.outputs["Image"], setalpha_node.inputs["Image"])
            link(denoise_node.outputs["Image"], setalpha_node.inputs["Alpha"])
            link(setalpha_node.outputs["Image"], composite.inputs["Image"])
            link(render_layers.outputs["Alpha"], denoise_node.inputs["Image"])
           
            if render_layers:
                place_nodes_relative_to(render_layers, [denoise_node, setalpha_node], offset_x=30)

        if selected_option == 'denoise_ao':

            denoise_node = node.new(type='CompositorNodeDenoise')
            mix = node.new(type='CompositorNodeMixRGB')
            mix.blend_type = 'SOFT_LIGHT'
            mix.inputs['Fac'].default_value = 0.1

            link(render_layers.outputs["Image"], mix.inputs["Image"])
            link(render_layers.outputs["AO"], denoise_node.inputs[0])
            link(denoise_node.outputs["Image"], mix.inputs[2])
            link(mix.outputs["Image"], composite.inputs["Image"])

            if render_layers:
                place_nodes_relative_to(render_layers, [denoise_node, mix], offset_x=30)

        if selected_option == 'denoise_transind':

            denoise_node = node.new(type='CompositorNodeDenoise')
            mix = node.new(type='CompositorNodeMixRGB')
            mix.blend_type = 'ADD'
            mix.inputs['Fac'].default_value = 0.4

            link(render_layers.outputs["Image"], mix.inputs["Image"])
            link(render_layers.outputs["TransInd"], denoise_node.inputs[0])
            link(denoise_node.outputs["Image"], mix.inputs[2])
            link(mix.outputs["Image"], composite.inputs["Image"])

            if render_layers:
                place_nodes_relative_to(render_layers, [denoise_node, mix], offset_x=30)

        if selected_option == 'mist_pass':
            
            denoise_node = node.new(type='CompositorNodeDenoise')
            color_ramp = node.new(type='CompositorNodeValToRGB')
            mix = node.new(type='CompositorNodeMixRGB')
            mix.blend_type = 'SCREEN'
            mix.inputs['Fac'].default_value = 1.0

            link(render_layers.outputs["Image"], mix.inputs[1])
            link(denoise_node.outputs["Image"], color_ramp.inputs["Fac"])
            link(color_ramp.outputs["Image"], mix.inputs[2])
            link(mix.outputs["Image"], composite.inputs["Image"])
            link(render_layers.outputs["Mist"], denoise_node.inputs[0])

            if render_layers:
                place_nodes_relative_to(render_layers, [denoise_node, color_ramp, mix], offset_x=30)

        return {'FINISHED'}

class AddMaskOperator(bpy.types.Operator): #komplett neu machen, dass da alles zwei mal steht ist total bescheuert und ich check nicht was da los ist
    bl_idname = "scene.add_mask_operator"
    bl_label = "Add Mask"
    
    mask_name_input: bpy.props.StringProperty(name="Mask Name", default="") 
    use_props_dialog: bpy.props.BoolProperty(name="Use Props Dialog", default=True) 

    def execute(self, context): #second dropdown menu

        for view_layer in bpy.context.scene.view_layers:
            view_layer.use_pass_cryptomatte_object = True
            view_layer.use_pass_cryptomatte_material = True
            view_layer.use_pass_cryptomatte_asset = True
        
        bpy.context.scene.use_nodes = True
        selected_option = context.scene.DenoiseDropDown
        tree = bpy.context.scene.node_tree
        node = tree.nodes
        link = tree.links.new
        composite = node.get("Composite")
        render_layers = node.get("Render Layers")
        deselect_all_nodes()             

        return {'FINISHED'}  


def register():
    bpy.utils.register_class(CustomCompositorPanel)
    bpy.utils.register_class(AddDenoiserOperator)
    bpy.utils.register_class(AddMaskOperator)
   

    bpy.types.Scene.DenoiseDropDown = bpy.props.EnumProperty(
        # internal name, user-friendly name, description (hover)
        items=[
            ('denoise', 'Simple', 'Simple Denoising'), 
            ('denoise_mixer', 'Mixer', 'Gradual Denoising'),
            ('denoise_crypto', 'Cryptomatte', 'Select your desired objects'),
            ('denoise_alpha', 'Alpha', 'Transparent Background'),
            ('denoise_ao', 'AO', 'Ambient Occlusion Pass'),
            ('denoise_transind', 'Trans Ind', 'Transmission Indirect Pass'),
            ('mist_pass', 'Mist Pass', 'Control your Depth Pass'),
        ],
        
        default='denoise',

    )

    bpy.types.Scene.MaskDropDown = bpy.props.EnumProperty(
        items=[
            ('bw_mask', 'PS: b/w Mask', 'Photoshop Black and White Mask'), 
            ('hl_mask', 'PS: Color', 'Photoshop Highlight'),
            ('hl_mask_p', 'Color', 'Procedural Highlight'),
            ('mask_p_curves', 'Mask Curves', 'Object related Mask Curves'), 
        ],
        
        default='mask_p_curves',
    )

    bpy.types.Scene.custom_checkbox_denoise = bpy.props.BoolProperty(
        name="Custom Checkbox Denoise",
        description="Toggle to mute/unmute All Denoise Nodes",
        default=False,
        update=update_denoise_nodes
    )

def unregister():
    bpy.utils.unregister_class(CustomCompositorPanel)
    bpy.utils.unregister_class(AddDenoiserOperator)
    bpy.utils.unregister_class(AddMaskOperator)

    del bpy.types.Scene.DenoiseDropDown
    del bpy.types.Scene.MaskDropDown

if __name__ == "__main__":
    register()