import bpy
from bpy.props import *
from bpy.types import PropertyGroup

from .update import *


class AMLIST_PR_WindowManager(PropertyGroup):
	toggle_sc_l      : BoolProperty(name="Scene")
	toggle_cam       : BoolProperty(name="Camera")
	toggle_action    : BoolProperty(name="Action")
	toggle_img       : BoolProperty(name="Image")
	toggle_light_l   : BoolProperty(name="Light")
	toggle_light_m   : BoolProperty(name="Emission Material")
	toggle_light_p   : BoolProperty(name="Light Probe")
	toggle_mat_all   : BoolProperty(name="Material")
	toggle_mat_index : BoolProperty(name="Material")
	toggle_mat_slot  : BoolProperty(name="Materials Slot")
	toggle_vcol      : BoolProperty(name="Viewport Color")
	toggle_wld       : BoolProperty(name="World")
	use_mat_ullist   : BoolProperty(name="UIlist Mode",description="Switch to the standard Blender list menu.\nThis is easy to scroll",default=True)


class AMLIST_PR_colle_mat(PropertyGroup):
	item  : PointerProperty(name="mat",type=bpy.types.Material)
	name : StringProperty(name="name")


class AMLIST_PR_mat_other(PropertyGroup):
	uidetail_node_toggle : BoolProperty(name="Display Each Option")
	uidetail_toggle : BoolProperty(name="Display list of assigned objects")


class AMLIST_PR_obj_other(PropertyGroup):
	uidetail_toggle : BoolProperty(name="Display Each Option")


class AMLIST_PR_action_other(PropertyGroup):
	uidetail_toggle : BoolProperty(name="Display Each Option")


class AMLIST_PR_light_l_other(PropertyGroup):
	uidetail_toggle : BoolProperty(name="Display Each Option")


class AMLIST_PR_img(PropertyGroup):
	uidetail_toggle : BoolProperty(name="Displays data that uses images",description="Displays the data that uses this image in the image texture node.\n(Only compatible with materials, node groups, and worlds)")

class AMLIST_PR_other(PropertyGroup):

	uidetail_toggle : BoolProperty(name="Display Each Option")
	action_toggle_frame_range : BoolProperty(name="Display Frame Range")


	asobj_l                      : StringProperty(name="list")
	asobj_mat                    : PointerProperty(name="name",type=bpy.types.Material)

	# cam
	cam_coll_sort                : BoolProperty(name="Sort Collection")
	cam_filter                   : StringProperty(name="Filter",description="Filter by string")
	cam_filter_colle             : PointerProperty(name="colle",type=bpy.types.Collection)
	cam_filter_match_case        : BoolProperty(default=False, name="Macth Case",description="Search is case sensitive")
	cam_filter_reverse           : BoolProperty(name="Reverse order")
	cam_filter_sort_type : EnumProperty(default="NAME",name = "Type", items= [
	("NAME","Name","Name","SORTALPHA",0),
	("ENERGY","Strength","","FAKE_USER_ON",1),
	("DIFFUSE_FACTOR","Diffuse","Diffuse","SHADING_SOLID",2),
	("SPECULAR_FACTOR","Specular","Specular","NODE_MATERIAL",3),
	("VOLUME_FACTOR","Volume","Volume","OUTLINER_DATA_VOLUME",4),
	("ANGLE","Angle","Angle","SNAP_PERPENDICULAR",5),
	])
	cam_filter_type              : EnumProperty(default="Scene",name="Type", items= [ ("Selected","Selected","Selected","RESTRICT_SELECT_OFF",0),("Scene","Scene","Scene","SCENE_DATA",1), ("All_Data","All Data","All Data","FILE",2),("Collection","Collection","Collection","GROUP",3), ("View_Layer","View Layer","Filter only the data used in the current view layer","RENDERLAYERS",4), ])
	cam_filter_use               : BoolProperty(name="Toggle Filter")
	cam_scroll                   : IntProperty(name="Scroll", description="Scroll",min=0)
	cam_scroll_num               : IntProperty(default=20,name="List Height", min=1, description="List Height")
	cam_ui_data_type             : BoolProperty(name="Data Type")
	cam_ui_hide_select           : BoolProperty(name="Disable Selection")
	cam_ui_hide_viewport         : BoolProperty(name="Disable in Viewports")
	cam_ui_lens                  : BoolProperty(default=False, name="Lens")
	cam_uidetail_toggle          : BoolProperty(default=True,name="Display Each Option")
	cam_uidetail_toggle_act      : BoolProperty(name="Display Option (Active Object)")
	cam_width                    : FloatProperty(name="Width", default=6 ,min=0.3)
	cam_filter_use_regex_src : BoolProperty(name="Use Regular Expressions")
	cam_filter_match_case        : BoolProperty(default=False, name="Macth Case",description="Search is case sensitive")
	cam_uidetail_toggle_status : BoolProperty()

	# action
	action_assign_type              : EnumProperty(default="None",name="Frame range change type at assign", items= [
	 ("None","None","None","RADIOBUT_OFF",0)
	,("SceneRange","Scene Frame Range","Scene Frame Range","PLAY",1),
	("Preview","Preview Range ","Preview Range","TRIA_RIGHT",2)
	,("SceneRange_Preview","Scene Frame Range and Preview Range","Scene Frame Range and Preview Range","FF",3), ])
	action_coll_sort                : BoolProperty(name="Sort Collection")
	action_filter                   : StringProperty(name="Filter",description="Filter by string")
	action_filter_colle             : PointerProperty(name="colle",type=bpy.types.Collection)
	action_filter_match_case        : BoolProperty(default=False, name="Macth Case",description="Search is case sensitive")
	action_filter_reverse           : BoolProperty(name="Reverse order")
	action_filter_sort_type : EnumProperty(default="NAME",name = "Type", items= [
	("NAME","Name","Name","SORTALPHA",0),
	])
	action_filter_type              : EnumProperty(default="All_Data",name="Type", items= [("ActiveObject","Active Object","Display actions that include the object name","OBJECT_DATA",0), ("Selected","Selected","Selected","RESTRICT_SELECT_OFF",1),("Scene","Scene","Scene","SCENE_DATA",2), ("All_Data","All Data","All Data","FILE",3),("Collection","Collection","Collection","GROUP",4), ("View_Layer","View Layer","Filter only the data used in the current view layer","RENDERLAYERS",5), ])
	action_filter_use               : BoolProperty(name="Toggle Filter")
	action_scroll                   : IntProperty(name="Scroll", description="Scroll",min=0)
	action_scroll_num               : IntProperty(default=20,name="List Height", min=1, description="List Height")
	action_ui_hide_select           : BoolProperty(name="Disable Selection")
	action_ui_hide_viewport         : BoolProperty(name="Disable in Viewports")
	action_uidetail_toggle          : BoolProperty(default=True,name="Display Each Option")
	action_uidetail_toggle_act      : BoolProperty(name="Display Option (Active Object)")
	action_width                    : FloatProperty(name="Width", default=6 ,min=0.3)
	action_uidetail_toggle_status : BoolProperty()
	action_filter_use_regex_src : BoolProperty(name="Use Regular Expressions")


	id_img                       : IntProperty(update=update_active_img)
	id_mat                       : IntProperty(default=-1,update=mat_list_update)
	id_wld                       : IntProperty(update=update_active_wld)

	# img
	image_rename_isExt           : BoolProperty(default=True, name="Include Extension")
	img_hide_render_result : BoolProperty(default=True,name="Hide Render Result",description="Hide the rendered image and the image for the viewer from the list")
	img_filter_use               : BoolProperty(name="Toggle Filter")
	img_list_rows                : IntProperty(name="List Height", description="List Height",default=20,min=1)
	img_show_filepath            : BoolProperty(name="Display File Path")
	img_show_size                : BoolProperty(name="Display Size")
	img_width                    : FloatProperty(name="File Path Width", default=0.3 ,min=0.3)
	img_filter_sort_type : EnumProperty(default="NAME",name = "Type", items= [
	("NAME","Name","Name","SORTALPHA",0),
	("USERS","Users","","FAKE_USER_ON",1),
	("SIZE","Size","Pixel Size","CON_SIZELIMIT",2),
	("FILEPATH","File Path","File Path","SORTSIZE",3),
	])
	img_filter               : StringProperty(name="Filter",description="Filter by string")
	img_filter_reverse       : BoolProperty(name="Reverse order")
	img_filter_use_regex_src : BoolProperty(name="Use Regular Expressions")
	img_filter_match_case        : BoolProperty(default=False, name="Macth Case",description="Search is case sensitive")


	# light_l
	light_l_coll_sort            : BoolProperty(name="Sort Collection")
	light_l_color                : BoolProperty(default=True,name="Color")
	light_l_filter               : StringProperty(name="Filter",description="Filter by string")
	light_l_filter_colle         : PointerProperty(name="colle",type=bpy.types.Collection)
	light_l_filter_match_case    : BoolProperty(default=False, name="Macth Case",description="Search is case sensitive")
	light_l_filter_reverse       : BoolProperty(name="Reverse order")
	light_l_filter_sort_type : EnumProperty(default="NAME",name = "Type", items= [
	("NAME","Name","Name","SORTALPHA",0),
	("TYPE","Type","Type","DOT",1),
	("ENERGY","Strength","","LIGHT_SUN",2),
	("DIFFUSE_FACTOR","Diffuse","Diffuse","SHADING_SOLID",3),
	("SPECULAR_FACTOR","Specular","Specular","NODE_MATERIAL",4),
	("VOLUME_FACTOR","Volume","Volume","OUTLINER_DATA_VOLUME",5),
	("ANGLE","Angle","Angle","SNAP_PERPENDICULAR",6),
	])
	light_l_filter_type          : EnumProperty(default="Scene",name="Type", items= [ ("Selected","Selected","Selected","RESTRICT_SELECT_OFF",0),("Scene","Scene","Scene","SCENE_DATA",1), ("All_Data","All Data","All Data","FILE",2),("Collection","Collection","Collection","GROUP",3), ("View_Layer","View Layer","Filter only the data used in the current view layer","RENDERLAYERS",4), ])
	light_l_filter_use           : BoolProperty(name="Toggle Filter")
	light_l_other_option         : BoolProperty(name="Other")
	light_l_power                : BoolProperty(default=True,name="Power")
	light_l_scroll               : IntProperty(name="Scroll", description="Scroll",min=0)
	light_l_scroll_num           : IntProperty(default=20,name="List Height", min=1, description="List Height")
	light_l_shadow               : BoolProperty(name="Shadow")
	light_l_size                 : BoolProperty(name="Size")
	light_l_specular             : BoolProperty(name="Specular")
	light_l_ui_data_type         : BoolProperty(name="Data Type")
	light_l_ui_hide_select       : BoolProperty(name="Disable Selection")
	light_l_ui_hide_viewport     : BoolProperty(name="Disable in Viewports")
	light_l_uidetail_toggle      : BoolProperty(default=True,name="Display Each Option")
	light_l_uidetail_toggle_act  : BoolProperty(name="Display Option (Active Object)")
	light_l_width                : FloatProperty(name="Width", default=6 ,min=0.3)
	light_l_filter_use_regex_src : BoolProperty(name="Use Regular Expressions")
	light_l_filter_match_case        : BoolProperty(default=False, name="Macth Case",description="Search is case sensitive")
	light_l_uidetail_toggle_status : BoolProperty()
	light_l_only_hide_darken_world :BoolProperty(name="Darkens the world when temporarily hidden",description="This is useful when you want to see only the effects of a specific light")
	light_m_width                : FloatProperty(name="Width", default=6 ,min=0.3)


	# light_p
	light_p_coll_sort            : BoolProperty(name="Sort Collection")
	light_p_filter               : StringProperty(name="Filter",description="Filter by string")
	light_p_filter               : StringProperty(name="Filter",description="Filter by string")
	light_p_filter_colle         : PointerProperty(name="colle",type=bpy.types.Collection)
	light_p_filter_match_case    : BoolProperty(default=False, name="Macth Case",description="Search is case sensitive")
	light_p_filter_reverse       : BoolProperty(name="Reverse order")
	light_p_filter_sort_type : EnumProperty(default="NAME",name = "Type", items= [
	("NAME","Name","Name","SORTALPHA",0),
	])
	light_p_filter_type          : EnumProperty(default="Scene",name="Type", items= [ ("Selected","Selected","Selected","RESTRICT_SELECT_OFF",0),("Scene","Scene","Scene","SCENE_DATA",1), ("All_Data","All Data","All Data","FILE",2),("Collection","Collection","Collection","GROUP",3), ("View_Layer","View Layer","Filter only the data used in the current view layer","RENDERLAYERS",4), ])
	light_p_filter_use           : BoolProperty(name="Toggle Filter")
	light_p_other_option         : BoolProperty(name="Other")
	light_p_scroll               : IntProperty(name="Scroll", description="Scroll",min=0)
	light_p_scroll_num           : IntProperty(default=20,name="List Height", min=1, description="List Height")
	light_p_ui_data_type         : BoolProperty(name="Data Type")
	light_p_ui_distance          : BoolProperty(name="Distance")
	light_p_ui_falloff           : BoolProperty(name="Falloff")
	light_p_ui_hide_select       : BoolProperty(name="Disable Selection")
	light_p_ui_hide_viewport     : BoolProperty(name="Disable in Viewports")
	light_p_ui_influence_type    : BoolProperty(name="Influence Type")
	light_p_ui_intensity         : BoolProperty(name="Intensity")
	light_p_ui_resolution        : BoolProperty(name="Resolution")
	light_p_uidetail_toggle      : BoolProperty(default=True,name="Display Each Option")
	light_p_uidetail_toggle_act  : BoolProperty(name="Display Option (Active Object)")
	light_p_width                : FloatProperty(name="Width", default=6 ,min=0.3)
	light_p_filter_use_regex_src : BoolProperty(name="Use Regular Expressions")
	light_p_filter_match_case        : BoolProperty(default=False, name="Macth Case",description="Search is case sensitive")
	light_p_uidetail_toggle_status : BoolProperty()


	# mat
	mat_filter_use_regex_src : BoolProperty(name="Use Regular Expressions")
	mat_emi_ui_node              : BoolProperty(default=True,name="Display Compact Node")
	mat_light_m_toggle              : BoolProperty(name="Emission Material")
	mat_filter                   : StringProperty(name="Filter",description="Filter by string")
	mat_filter_index_use         : BoolProperty(name="Filter Pass Index")
	mat_filter_match_case        : BoolProperty(default=False, name="Macth Case",description="Search is case sensitive")
	mat_filter_reverse           : BoolProperty(name="Reverse order")
	mat_filter_type              : EnumProperty(default="All_Data",name="Type", items= [ ("Slot","Slot","Shows the material in the material slot of the active object","SORTSIZE",0),("Selected","Selected","Filter only the data used in the selected","RESTRICT_SELECT_OFF",1),("Scene","Scene","Filter only the data used in the current scene","SCENE_DATA",2), ("All_Data","All Data","Shows all data in the blend file","FILE",3), ("View_Layer","View Layer","Filter only the data used in the current view layer","RENDERLAYERS",4), ])
	mat_filter_use               : BoolProperty(name="Toggle Filter")
	mat_filter_sort_type : EnumProperty(default="NAME",name = "Type", items= [
	("NAME","Name","Name","SORTALPHA",0),
	("USERS","Users","","FAKE_USER_ON",1),
	("PASS_INDEX","Pass Index","","LINENUMBERS_ON",2),
	("NUMBER_OF_NODES","Number of Nodes","","LINENUMBERS_ON",3),
	]
	)
	mat_number_of_nodes_show : BoolProperty(name="Show Number of Nodes")
	mat_gp_name00                : StringProperty(default="Pass_Index_00", name="Pass_Index_00")
	mat_gp_name01                : StringProperty(default="Pass_Index_01", name="Pass_Index_01")
	mat_gp_name02                : StringProperty(default="Pass_Index_02", name="Pass_Index_02")
	mat_gp_name03                : StringProperty(default="Pass_Index_03", name="Pass_Index_03")
	mat_gp_name04                : StringProperty(default="Pass_Index_04", name="Pass_Index_04")
	mat_gp_name05                : StringProperty(default="Pass_Index_05", name="Pass_Index_05")
	mat_gp_name06                : StringProperty(default="Pass_Index_06", name="Pass_Index_06")
	mat_gp_name07                : StringProperty(default="Pass_Index_07", name="Pass_Index_07")
	mat_gp_name08                : StringProperty(default="Pass_Index_08", name="Pass_Index_08")
	mat_gp_name09                : StringProperty(default="Pass_Index_09", name="Pass_Index_09")
	mat_gp_name10                : StringProperty(default="Pass_Index_10", name="Pass_Index_10")
	mat_gp_name11                : StringProperty(default="Pass_Index_11", name="Pass_Index_11")
	mat_gp_name12                : StringProperty(default="Pass_Index_12", name="Pass_Index_12")
	mat_gp_name13                : StringProperty(default="Pass_Index_13", name="Pass_Index_13")
	mat_gp_name14                : StringProperty(default="Pass_Index_14", name="Pass_Index_14")
	mat_gp_name15                : StringProperty(default="Pass_Index_15", name="Pass_Index_15")
	mat_gp_name16                : StringProperty(default="Pass_Index_16", name="Pass_Index_16")
	mat_gp_name17                : StringProperty(default="Pass_Index_17", name="Pass_Index_17")
	mat_gp_name18                : StringProperty(default="Pass_Index_18", name="Pass_Index_18")
	mat_gp_name19                : StringProperty(default="Pass_Index_19", name="Pass_Index_19")
	mat_gp_name20                : StringProperty(default="Pass_Index_20", name="Pass_Index_20")
	mat_index_num                : IntProperty(default=-1, name="View Pass_Index",min=-1)
	mat_index_show               : BoolProperty(name="Display Pass Index")
	mat_list_rows                : IntProperty(name="Vertical Width", description="Vertical Width")
	mat_scroll                   : IntProperty(name="Scroll", description="Scroll",min=0)
	mat_scroll_num               : IntProperty(default=20,name="List Height", min=1, description="List Height")
	mat_ui_node                  : BoolProperty(name="Display Compact Node")
	mat_uidetail_nameedit        : BoolProperty(name="Toggle Editable Name Menu")
	mat_display_mat_type : EnumProperty(default="BOTH",name = "Display Material Type", items= [ ("BOTH","Both",""), ("DEFULT_MAT","Default Material",""), ("GREASE_PENCIL","Grease Pencil",""), ])
	# mat_display_grease_pencil          : BoolProperty(name="Display Grease Pencil Material",default=True)
	action_uidetail_nameedit        : BoolProperty(name="Toggle Editable Name Menu")
	mat_uidetail_toggle          : BoolProperty(name="Display Assigned Objects List")
	mat_uidetail_node_toggle          : BoolProperty(name="Display Node Parameter")
	mat_uidetail_toggle_act      : BoolProperty(name="Display Assigned Objects(Only active)")
	mat_uidetail_node_toggle_act      : BoolProperty(name="Display Node Parameter(Only active)")
	mode_mat_slot                : BoolProperty(name="Slot Mode")
	move_index                   : IntProperty(name="Set Pass Index",min=-1)
	new_mat_color                : FloatVectorProperty(name="New Material Color", default=(0.800000, 0.800000, 0.800000, 1.000000), size=4, subtype="COLOR", min=0, max=1)


	img_uidetail_toggle          : BoolProperty(name="Display Used Data List(Material, Node Groups, World)")


	# sc_l
	sc_l_filter_object : BoolProperty(name="Display Number of Objects")
	sc_l_filter               : StringProperty(name="Filter",description="Filter by string")
	sc_l_filter_colle         : PointerProperty(name="colle",type=bpy.types.Collection)
	sc_l_filter_match_case    : BoolProperty(default=False, name="Macth Case",description="Search is case sensitive")
	sc_l_filter_reverse       : BoolProperty(name="Reverse order")
	sc_l_filter_sort_type : EnumProperty(default="NAME",name = "Type", items= [
	("NAME","Name","Name","SORTALPHA",0),
	("OBJECT","Object","","OBJECT_DATAMODE",1),
	("VIEW_LAYER","View Layer","","RENDERLAYERS",2),
	]
	)

	sc_l_filter_use           : BoolProperty(name="Toggle Filter")
	sc_l_other_option         : BoolProperty(name="Other")
	sc_l_scroll               : IntProperty(name="Scroll", description="Scroll",min=0)
	sc_l_scroll_num           : IntProperty(default=5,name="List Height", min=1, description="List Height")
	sc_l_ui_data_type         : BoolProperty(name="Data Type")
	sc_l_ui_hide_select       : BoolProperty(name="Disable Selection")
	sc_l_ui_hide_viewport     : BoolProperty(name="Disable in Viewports")
	sc_l_uidetail_toggle          : BoolProperty(default=True,name="Display Scene Setting")
	sc_l_uidetail_toggle_act      : BoolProperty(name="Display View layer")
	sc_l_uidetail_toggle_render      : BoolProperty(name="Display Render Setting",default=True)
	tab_popup                    : EnumProperty(name="Tab", description="", items=[('COMPACT', "Compact", ""), ('MAIN', "Main", "")], default='COMPACT')
	to_color_diffuse_mode        : BoolProperty(name="Diffuse BSDF Mode",description="Use Diffuse BSDF color instead of Principled BSDF")
	sc_l_viewlayers_index : IntProperty(default=-1,name="Index")
	sc_l_filter_use_regex_src : BoolProperty(name="Use Regular Expressions")


	# レンダーステータス
	sc_l_render_s_toggle_divide_into_folders : BoolProperty(name="Divide into folders",description="Create a folder for each item name and save")
	sc_l_render_s_uidetail_toggle          : BoolProperty(name="Display Each Option")
	sc_l_render_s_toggle_file : BoolProperty(name="File")
	sc_l_render_s_toggle_frame : BoolProperty(name="Frame Range")
	sc_l_render_s_toggle_resolution : BoolProperty(name="Resolution")
	sc_l_render_s_toggle_sample : BoolProperty(name="Sample")
	sc_l_render_s_scene_type : EnumProperty(default="Current_Scene",name = "Scene Type",
	items= [
	("Current_Scene","Current Scene",""),
	("All_Scene","All Scene",""),
	])


	# パネル 解像度
	sc_l_ptdime_toggle_other : BoolProperty(name="Other")
	sc_l_ptdime_toggle_file : BoolProperty(name="File")
	sc_l_ptdime_toggle_frame : BoolProperty(default=True,name="Frame Range")
	sc_l_ptdime_toggle_resolution : BoolProperty(default=True,name="Resolution")
	sc_l_ptdime_toggle_sample : BoolProperty(default=True,name="Sample")
	sc_l_ptdime_scene_type : EnumProperty(default="Current_Scene",name = "Scene Type",
	items= [
	("Current_Scene","Current Scene","","DOT",0),
	("All_Scene","All Scene","","SCENE_DATA",1),
	])

	# その他
	sc_l_viewlayers_toggle_main : BoolProperty(name="View Layers")
