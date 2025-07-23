import bpy
from bpy_extras.node_utils import find_node_input


def node_draw(layout, mat, output_type, input_name):
	box = layout.box()
	col = box.column(align=True)
	if bpy.context.scene.render.engine == "CYCLES":
		panel_node_draw_cycles(col, mat, output_type, input_name)
	else:
		panel_node_draw_eevee(col, mat, output_type, input_name)



def panel_node_draw_cycles(layout, id_data, output_type, input_name):
	if not id_data.use_nodes:
		layout.operator("cycles.use_shading_nodes", icon='NODETREE')
		return False

	ntree = id_data.node_tree

	node = ntree.get_output_node('CYCLES')
	if node:
		input = find_node_input(node, input_name)
		if input:
			layout.template_node_view(ntree, node, input)
		else:
			layout.label(text="Incompatible output node")
	else:
		layout.label(text="No output node")

	return True


def panel_node_draw_eevee(layout, id_data, _output_type, input_name):
	ntree = id_data.node_tree
	if not ntree:
		layout.label(text="No Node Tree")
		return

	node = ntree.get_output_node('EEVEE')

	if node:
		input = find_node_input(node, input_name)
		if input:
			layout.template_node_view(ntree, node, input)
		else:
			layout.label(text="Incompatible output node")
	else:
		layout.label(text="No output node")
