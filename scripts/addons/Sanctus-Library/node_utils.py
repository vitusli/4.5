'''
Wrapping functions that interface with node trees. This used to be more relevant when SL supported Blender versions before 4.0 when node trees worked differently in python.
'''

from .auto_load.common import *
from . import auto_load as al


def _node_tree_item_is_input(interface: bt.NodeTreeInterfaceItem):
    return interface.item_type == 'SOCKET' and interface.in_out == 'INPUT'

def get_node_tree_inputs(nt: bt.NodeTree) -> list[bt.NodeTreeInterfaceSocket]:
    # return nt.inputs.values()
    return [x for x in nt.interface.items_tree if _node_tree_item_is_input(x)]

def get_node_tree_input_keys(nt: bt.GeometryNodeTree):
    # return nt.inputs.keys()
    return [x.name for x in nt.interface.items_tree if _node_tree_item_is_input(x)]

def input_name_is_category(name: str):
    return name.startswith('--') and name.endswith('--')

def category_name_reduced(name: str):
    if input_name_is_category(name):
        return name[2:-2]
    raise ValueError(f'Input value "{name}" is not a category name')

def gn_input_identifier(group: bt.GeometryNodeTree, input_name: str):
    return next(x.identifier for x in get_node_tree_inputs(group) if x.name == input_name)

def get_gn_parameter(mod: bt.NodesModifier, input_name: str):
    return mod[gn_input_identifier(mod.node_group, input_name)]

def assert_active_edit_tree(tree_class: typing.Type[bt.NodeTree]):
    return al.OperatorAssert(lambda c: isinstance(c.space_data.edit_tree, tree_class), f'Current nodetree is not of type {tree_class.__name__}', strict=False)

def is_socket_type(socket:bt.NodeTreeInterfaceSocket, socket_type:str):
    return socket.socket_type == socket_type