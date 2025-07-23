from ..auto_load.common import *
from . import utils

class SetupError(Exception):
    ...

class BakeSetup:
    '''temporary override node setup when baking maps. Makes sure that after baking, the previous state is restored if `clean_up()` is called. Abstracts away the need to manually connect nodes for baking'''

    @property
    def node_tree(self):
        return self.material.node_tree
    
    @property
    def nodes(self):
        return self.material.node_tree.nodes
    
    @classmethod
    def is_shader_socket(cls, socket: bt.NodeSocket):
        return isinstance(socket, bt.NodeSocketShader)

    def __init__(self, material: bt.Material, image: bt.Image, bake_socket: Optional[bt.NodeSocket] = None):
        
        self.material = material
        output_socket = utils.get_shader_output_socket(self.node_tree)
        if(output_socket is None):
            raise SetupError(f"Could not create setup because material <{material.name}> does not have a valid material output socket available")
        
        self.output_socket = output_socket
        self.temp_nodes: list[bt.Node] = []
        self.intermediate_shader_node: OrNone[bt.ShaderNodeBsdfPrincipled] = None
        
        self.image = image
        self.bake_socket = bake_socket

        self.former_active_node = self.nodes.active
        self.former_connected_socket = None
        if len(self.output_socket.links) > 0:
            self.former_connected_socket: bt.NodeSocket = self.output_socket.links[0].from_socket

        image_node: bt.ShaderNodeTexImage = self.nodes.new('ShaderNodeTexImage') #change in nt
        self.register_node(image_node)
        self.image_node = image_node
        image_node.image = image
        self.nodes.active = image_node #change in nt

        if self.bake_socket is not None:
            self.link_to_material(self.bake_socket) #change in nt

    def link_to_material(self, socket: bt.NodeSocket):
        if self.is_shader_socket(socket):
            self.node_tree.links.new(socket, self.output_socket)
            return
        if self.intermediate_shader_node is None:
            shader_node = self.nodes.new('ShaderNodeBsdfPrincipled')
            self.register_and_connect_node(shader_node, shader_node.outputs[0])
            shader_node.inputs['Specular IOR Level'].default_value = 0
            self.intermediate_shader_node = shader_node
        self.node_tree.links.new(socket, self.intermediate_shader_node.inputs[0])

    def set_image(self, image: bt.Image):
        self.image = image
        self.image_node.image = image

    def register_node(self, node: bt.Node):
        self.temp_nodes.append(node)

    def register_and_connect_node(self, node: bt.Node, output_socket: Optional[bt.NodeSocket] = None):
        if output_socket is None:
            output_socket = node.outputs[0]
        self.register_node(node)
        self.link_to_material(output_socket)

    def connect_default_value(self, value: Union[float, int, tuple[float, float, float]]):
        rgb_value = value
        if isinstance(value, float) or isinstance(value, int):
            value = float(value)
            rgb_value = (value, value, value)
            
        node: bt.ShaderNodeRGB = self.nodes.new('ShaderNodeRGB')
        output: bt.NodeSocketColor = node.outputs[0]
        output.default_value = (rgb_value[0], rgb_value[1], rgb_value[2], 0)
        self.register_and_connect_node(node, output)

    def clean_up(self):
        for n in self.temp_nodes:
            self.nodes.remove(n)
        self.nodes.active = self.former_active_node
        if(self.former_connected_socket):
            self.node_tree.links.new(self.former_connected_socket, self.output_socket)
