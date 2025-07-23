
from .. import auto_load as al
from ..auto_load.common import *

from .. import base_ops
from .. import node_utils
from .. import asset

@al.register_operator
class AddShaderNodeGroup(base_ops.SanctusAssetImportOperator):
    bl_label = 'Add Group Node'
    bl_description = 'Add group node to the active node tree'
    asset_type = asset.Type.NODE_GROUPS
    use_reimport_prompt = False
    al_asserts: list[al.OperatorAssert] = [
        node_utils.assert_active_edit_tree(bt.ShaderNodeTree)
    ]

    def run(self, context: al.BContext[bt.SpaceNodeEditor]):

        sd = context.space_data
        nt: bt.ShaderNodeTree = sd.edit_tree

        group = self.get_importer().get_asset(self.reimport_asset())

        node: bt.ShaderNodeGroup = nt.nodes.new('ShaderNodeGroup')
        node.location = sd.cursor_location
        node.node_tree = group
        for n in nt.nodes:
            n.select = n == node
        bo.node.translate_attach('INVOKE_DEFAULT')

@al.register_operator
class AddCompositorNodeGroup(base_ops.SanctusAssetImportOperator):
    bl_label = "Add Group Node"
    bl_description = "Add group node to the active node tree"
    asset_type = asset.Type.NODE_GROUPS
    use_reimport_prompt = False
    al_asserts: list[al.OperatorAssert] = [
        node_utils.assert_active_edit_tree(bt.CompositorNodeTree)
    ]

    def run(self, context: al.BContext[bt.SpaceNodeEditor]):
        sd = context.space_data
        nt: bt.CompositorNodeTree = sd.edit_tree

        group = self.get_importer().get_asset(self.reimport_asset())
        node: bt.CompositorNodeGroup = nt.nodes.new('CompositorNodeGroup')
        node.location = sd.cursor_location
        node.node_tree = group
        for n in nt.nodes:
            n.select = n == node
        bo.node.translate_attach('INVOKE_DEFAULT')


@al.register_operator
class AddSmartModuleNodeGroup(base_ops.SanctusAssetImportOperator):
    bl_label = "Add Smart Module"
    bl_description = 'Add group node to the active node tree'
    asset_type = asset.Type.NODE_GROUPS
    use_reimport_prompt = False
    al_asserts: list[al.OperatorAssert] = [
        node_utils.assert_active_edit_tree(bt.ShaderNodeTree)
    ]

    def run(self, context: al.BContext[bt.SpaceNodeEditor]):
        sd = context.space_data
        nt: bt.ShaderNodeTree = sd.edit_tree

        group = self.get_importer().get_asset(self.reimport_asset())
        node: bt.ShaderNodeGroup = nt.nodes.new("ShaderNodeGroup")
        node.location = sd.cursor_location
        node.node_tree = group
        for n in nt.nodes:
            n.select = n == node
        bo.node.translate_attach('INVOKE_DEFAULT')


def node_position(node: bt.Node):
    if node.parent == None:
        return node.location
    return node.location + node_position(node.parent)

def connect_modules(nt: bt.NodeTree, left: bt.ShaderNodeGroup, right: bt.ShaderNodeGroup):
    connection_made = False
    for output in left.outputs:
        output: bt.NodeSocket
        name = output.name.removesuffix(" Bake")
        for input in right.inputs:
            input: bt.NodeSocket
            
            if input.name.endswith(" Input") and name == input.name.removesuffix(" Input"):
                nt.links.new(output, input)
                connection_made = True
    return connection_made


@al.register_operator
class ConnectSmartModules(base_ops.SanctusOperator):
    bl_label = "Connect Modules"
    bl_description = "Connect Smart Module sockets. The order is determined through node locations"
    
    @classmethod
    def get_asserts(cls, context: bt.Context):
        yield node_utils.assert_active_edit_tree(bt.ShaderNodeTree)
        nt: bt.ShaderNodeTree = context.space_data.edit_tree
        selected_nodes = context.selected_nodes
        yield al.OperatorAssert(lambda: len(selected_nodes) >= 2, 'Not enough nodes selected. (Must be 2 or more.)')
        yield al.OperatorAssert(lambda: all(isinstance(x, bt.ShaderNodeGroup) for x in selected_nodes), 'Selected nodes aren’t node groups.')

    def run(self, context: al.BContext[bt.SpaceNodeEditor]):
        nt: bt.ShaderNodeTree = context.space_data.node_tree
        connections_made = False

        def node_order(node: bt.Node):
            return node_position(node).x

        ordered_nodes: list[bt.Node] = sorted(context.selected_nodes, key=node_order)
        for i in range(len(ordered_nodes) - 1):
            if connect_modules(nt, ordered_nodes[i], ordered_nodes[i + 1]):
                connections_made = True
        
        if not connections_made:
            self.report({"WARNING"}, "No valid connections found between modules")


@al.register_draw_function(bt.NODE_MT_context_menu)
def add_connect_smart_modules_operator_to_node_context_menu(menu: bt.Menu, context: bt.Context):
    from .. import library_manager
    if ConnectSmartModules.op_cls.poll(context):
        ConnectSmartModules().draw_ui(menu.layout, al.UIOptionsOperator(text=ConnectSmartModules.bl_label, icon=library_manager.MANAGER.icon_id(Path('icons/icon'))))
