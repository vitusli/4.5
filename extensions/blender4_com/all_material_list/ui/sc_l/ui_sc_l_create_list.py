import bpy
import re


# コレクション別のリストの作成
def coll_rec(coll, clist):
	props = bpy.context.scene.am_list

	# コレクションと対象アイテムを探す
	if coll.children:
		for child in coll.children:
			coll_rec(child, clist)

	filter_type=[o for o in coll.objects if o.type=='LIGHT']

	# 名前をリスト化
	if not props.sc_l_filter_match_case: # 大文字小文字検索フィルター
		l_items = [o for o in filter_type if re.findall(props.sc_l_filter.lower(),o.name.lower())]
	else:
		l_items = [o for o in filter_type if re.findall(props.sc_l_filter,o.name)]


	if l_items:
		#名前順に並び替え
		if props.sc_l_sort_type == "name":
			l_items = sorted(l_items, key=lambda p: p.name)

		if props.sc_l_filter_reverse:
			l_items = list(reversed(l_items))


		clist.append((coll.name, l_items))


########################################
# リストの作成
def create_list():
	props = bpy.context.scene.am_list

	# オブジェクトリストのタイプ
	filter_type=[]
	if props.sc_l_filter_type=="Selected":
		filter_type = bpy.context.selected_objects
	elif props.sc_l_filter_type=="Scene":
		filter_type = bpy.context.scene.collection.all_objects
	elif props.sc_l_filter_type=="All_Data":
		filter_type = bpy.data.objects
	elif props.sc_l_filter_type=="Collection":
		colle = props.sc_l_filter_colle
		if colle:
			filter_type = colle.objects

	# 名前をリスト化
	if not props.sc_l_filter_match_case: # 大文字小文字検索フィルター
		l_items = [o for o in filter_type if o.type in ['LIGHT'] if re.findall(props.sc_l_filter.lower(),o.name.lower())]
	else:
		l_items = [o for o in filter_type if o.type in ['LIGHT'] if re.findall(props.sc_l_filter,o.name)]


	#名前順に並び替え
	if props.sc_l_sort_type == "name":
		l_items = sorted(l_items, key=lambda p: p.name)
	elif props.sc_l_sort_type == "energy":
		l_items = sorted(l_items, key=lambda p: p.data.energy)

	if props.sc_l_sort_type == "energy":
		l_items = list(reversed(l_items))

	if props.sc_l_filter_reverse:
		l_items = list(reversed(l_items))

	return l_items
