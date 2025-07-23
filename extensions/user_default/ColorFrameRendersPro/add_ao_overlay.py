
import bpy
import sys
import os
import time
argv = sys.argv
argv = argv[argv.index("--") + 1:] 
IMG= argv[0]
AO= argv[1]
STRENGTH=eval(argv[2])
context = bpy.context
scene = context.scene

scene.use_nodes = True
node_tree = scene.node_tree

n_comp = None
for n in node_tree.nodes:
    if not n.type == 'COMPOSITE':
        node_tree.nodes.remove(n)
    else:
        n_comp = n
mix=node_tree.nodes.new("CompositorNodeMixRGB")
mix.inputs[0].default_value=STRENGTH
mix.blend_type='MULTIPLY'
img = bpy.data.images.load(IMG)
og_img = node_tree.nodes.new("CompositorNodeImage")
og_img.image = img

img = bpy.data.images.load(AO)
ao_img = node_tree.nodes.new("CompositorNodeImage")
ao_img.image = img
# Links
links = node_tree.links
links.new(og_img.outputs[0], mix.inputs[1])
links.new(ao_img.outputs[0], mix.inputs[2])
links.new(mix.outputs[0],n_comp.inputs[0])

# Render
r = scene.render
r.image_settings.file_format = 'PNG'
r.image_settings.quality = 95
r.resolution_x = img.size[0]
r.resolution_y =  img.size[1]
r.resolution_percentage = 100
r.filepath = IMG
bpy.ops.render.render(write_still=True)
