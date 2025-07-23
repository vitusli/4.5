import bpy
import re

def create_list(use_namefilter):
	props = bpy.context.scene.am_list

	try:
		# リストのタイプ
		if props.mat_filter_type=="Selected":
			l_items =[m.material for o in bpy.context.selected_objects for m in o.material_slots if m.name != '']
			l_items = set(l_items)

		elif props.mat_filter_type=="Scene":
			l_items = [m.material for o in bpy.context.scene.objects for m in o.material_slots if m.name != '']
			l_items = list(set(l_items))

		elif props.mat_filter_type=="All_Data":
			l_items = [m for m in bpy.data.materials]

		elif props.mat_filter_type=="View_Layer":
			l_items = [m.material for o in bpy.context.view_layer.objects for m in o.material_slots if m.name != '']
			l_items = list(set(l_items))

		elif props.mat_filter_type=="Slot":
			l_items = [m.material for m in bpy.context.object.material_slots if m.name != '']
	except:
		l_items = []

	if props.mat_filter_index_use:
		if not props.mat_index_num == -1:
			l_items = [m for m in l_items if m.pass_index == props.mat_index_num]


	# 名前をリスト化
	if use_namefilter:
		if props.mat_filter:
			if props.mat_filter_match_case: # 大文字小文字検索フィルター
				l_items = [o for o in l_items if re.findall(props.mat_filter.lower(),o.name.lower())]
			else:
				l_items = [o for o in l_items if re.findall(props.mat_filter,o.name)]


	# エミッションマテリアル
	if props.mat_light_m_toggle:
		l_items = light_m_filter(l_items)


	if use_namefilter:
		if props.mat_filter_sort_type == "NAME":
			l_items = sorted(l_items, key=lambda p: p.name)

		elif props.mat_filter_sort_type == "USERS":
			l_items = sorted(l_items, key=lambda p: p.users)

		elif props.mat_filter_sort_type == "PASS_INDEX":
			l_items = sorted(l_items, key=lambda p: p.pass_index)

		if props.mat_filter_reverse:
			l_items = list(reversed(l_items))

	return l_items


# エミッションマテリアル
def light_m_filter(l_items):
	emi_m_list = []
	for mat in l_items:
		if mat.node_tree:
			for no in mat.node_tree.nodes:
				if not no.type in ("EMISSION", "GROUP"):
					continue
				for ou in no.outputs:
					if not ou.links:
						continue
					if no.type == "GROUP" and no.node_tree and no.node_tree.nodes:
						for gno in no.node_tree.nodes:
							if gno.type != "EMISSION":
								continue
							for gou in gno.outputs:
								if ou.links and gou.links:
									if not gno.name == "Emission Viewer":
										emi_m_list.append(mat)
									break
					elif no.type == "EMISSION":
						if ou.links:
							if not no.name == "Emission Viewer":
								emi_m_list.append(mat)
								break

	return emi_m_list
