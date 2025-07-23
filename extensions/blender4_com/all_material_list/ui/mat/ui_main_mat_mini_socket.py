import bpy
from bpy.props import *

def node_compact_parameter(mat,layout,view_nml,draw_type):
	rownd = layout.row(align=True)
	rownd.ui_units_x = 10

	if mat:
		if mat.is_grease_pencil:
			rownd.prop(mat.grease_pencil,"show_stroke",text="")
			rownd.prop(mat.grease_pencil,"color",text="")
			rownd.separator()
			rownd.prop(mat.grease_pencil,"show_fill",text="")
			rownd.prop(mat.grease_pencil,"fill_color",text="")
		elif not mat.use_nodes:
			rownd.prop(mat,"diffuse_color",text="")
			rownd.prop(mat,"metallic",text="")
			rownd.prop(mat,"roughness",text="")

		else:
			draw_shader_node(mat,rownd,view_nml,draw_type)

	draw_slot_in_popup(mat, layout, view_nml, draw_type)


def draw_slot_in_popup(mat, layout, view_nml, draw_type):
	if not draw_type == "POPUP":
		return
	obj = bpy.context.object
	if not obj:
		return
	if not obj.type in {"MESH", "CURVE", "SURFACE", "META", "FONT","VOLUME","GPENCIL"}:
		return
	if not len(obj.data.materials) > 1:
		return


	act_index = obj.active_material_index
	row = layout.row(align=True)
	for i,mat in enumerate(obj.data.materials):
		if mat:
			op = row.operator("amlist.mat_set_active_index",text="",
			icon_value=layout.icon(mat),
			emboss=bool(i==act_index)
			)
			op.index = i
		else:
			# layout.label(text="",icon="MESH_CIRCLE",
			# emboss=bool(i==act_index)
			# )
			op = row.operator("amlist.mat_set_active_index",text="",
			icon="MESH_CIRCLE",
			emboss=bool(i==act_index)
			)
			op.index = i


#
def draw_shader_node(mat, layout, view_nml, draw_type):
	ntree = mat.node_tree
	if draw_type == "LIST":
		tex_import_icon_width = .3
	else:
		tex_import_icon_width = .5
	main_shader_nd, error_text, is_volume = get_output_linked_shader_node(mat)
	if error_text:
		layout.active = False
		layout.label(text=error_text)
		return


	if is_volume:
		socket_name_l = ["Color","Base Color", "Density", "Anisotropy", "Metallic",  "Roughness"]
	else:
		socket_name_l = ["Color","Base Color", "Metallic", "Roughness"]

	if view_nml:
		socket_name_l += ["Normal"]

	if main_shader_nd.type == "EMISSION":
		socket_name_l += ["Strength"]

	for i, sname in enumerate(socket_name_l):
		if sname in main_shader_nd.inputs:
			tgt_socket = main_shader_nd.inputs[sname]
			if tgt_socket.links:
				link_nd = tgt_socket.links[0].from_node
				if sname == "Normal":
					if "Color" in link_nd.inputs:
						if link_nd.inputs["Color"].links:
							link_nd = link_nd.inputs["Color"].links[0].from_node

				if link_nd.type == "TEX_IMAGE":
					if i in {0,1}:
						row = layout.row(align=True)
						row.scale_x = tex_import_icon_width
						row.active = False
						col = row.column(align=True)
						col.scale_y = 0.5
						op = col.operator("am_list.setup_one_tex_new_img",text="",icon="LAYER_ACTIVE",emboss=False)
						op.mat_name = mat.name
						op = col.operator("amlist.node_remove",text="",icon="LAYER_USED",emboss=False)
						op.node_name = tgt_socket.links[0].from_node.name
						op.mat_name = mat.name
						op.input_socket = sname
						op.reconnect = False
						row.label(text="",icon="BLANK1")

					if link_nd.image:
						img_icon = layout.icon(link_nd.image)
						layout.prop(link_nd,"image",text="",icon_value=img_icon)
					else:
						layout.template_ID(link_nd, "image", open="image.open",text="")

				else:
					if sname == "Normal":
						continue
					row = layout.row(align=True)
					row.active = False
					row.label(text=link_nd.name,icon="NONE")
			else:
				if sname == "Normal":
					continue

				if i in {0,1}:
					row = layout.row(align=True)
					row.scale_x = tex_import_icon_width
					row.active = False
					col = row.column(align=True)
					op = col.operator("am_list.setup_one_tex_new_img",text="",icon="LAYER_ACTIVE",emboss=False)
					op.mat_name = mat.name
					col.separator()
					row.label(text="",icon="BLANK1")

				layout.prop(tgt_socket,"default_value",text="")




def get_output_linked_shader_node(mat):
	ntree = mat.node_tree

	# 出力ノード
	act_output_nd = None
	for nd in ntree.nodes:
		if nd.type == 'OUTPUT_MATERIAL' and nd.is_active_output:
			act_output_nd = nd
			break

	# 出力ノードがない
	if not act_output_nd:
		return None, "No Output Node", False


	# 出力ノードの対象の入力ソケットを決定
	if act_output_nd.inputs['Surface'].links:
		tgt_input_nd = act_output_nd.inputs['Surface']
		is_volume = False
	elif act_output_nd.inputs['Volume'].links:
		tgt_input_nd = act_output_nd.inputs['Volume']
		is_volume = True
	else:
		return None, "No Link Output Node", False


	main_shader_nd = tgt_input_nd.links[0].from_node
	# リンクしていない
	if not main_shader_nd:
		return None, "No Linked Output Node", False

	return main_shader_nd, None, is_volume
