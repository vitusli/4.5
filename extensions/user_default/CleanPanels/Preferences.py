# This program is free software; you can redistribute it and/or modifytemp_collection
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
import os
import bpy
import rna_keymap_ui
import textwrap
import bpy.utils.previews
from bpy.types import Context, Event, PropertyGroup, Menu
from bpy_extras.io_utils import ExportHelper, ImportHelper
from .utils import *
import math
from .addon_update_checker import AddonUpdateChecker, draw_update_section_for_prefs

# P
import json
import addon_utils


def tab_name_updated(self, context):
    pass


class AddonInfo(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()
    display_name: bpy.props.StringProperty()
    addons: bpy.props.StringProperty()
    ordered: bpy.props.StringProperty()


class AddonInfoRename(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()
    display_name: bpy.props.StringProperty()
    tab_name: bpy.props.StringProperty(update=tab_name_updated)
    identifier: bpy.props.StringProperty()
    space: bpy.props.StringProperty()
    backup_tab_name: bpy.props.StringProperty()


class AddonDescriptionInfo(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()
    desc: bpy.props.StringProperty(name="Description")


def draw_filter_buttons(self, context):
    if context.area.type in ["IMAGE_EDITOR", "NODE_EDITOR"] and preferences().easy_mode:
        return
    layout_str = ""

    def extract_balanced_structure(text, start_char="[", end_char="]"):
        """Extract a balanced structure from text, starting with start_char and ending with end_char."""
        stack = []
        start_index = -1

        for i, char in enumerate(text):
            if char == start_char:
                if not stack:
                    start_index = i  # Mark the start of the balanced structure
                stack.append(char)
            elif char == end_char:
                if stack:
                    stack.pop()
                    if not stack:  # All brackets are balanced
                        return text[start_index : i + 1]

        return None  # Return None if no balanced structure is found

    try:
        layout_str = repr(self.layout.introspect())
    except Exception as e:
        try:
            import traceback

            stack_trace = traceback.format_exc()
            layout_str = extract_balanced_structure(stack_trace)
        except Exception:
            pass

    if (
        preferences().delayed_loading_code_injected
        and not preferences().delayed_addons_loaded
        and not "callloadaddonsetmenu" in layout_str
    ):
        self.layout.operator(
            "cp.callloadaddonsetmenu", text="Load Addons", icon="FILE_REFRESH"
        )
    already_drawn = "bpy.ops.cp.settings" in layout_str
    draw_side = preferences().draw_side
    if context.area.type != "VIEW_3D":
        draw_side = "RIGHT"
    if not already_drawn:
        if draw_side == "LEFT":
            if preferences().show_quick_reorder:
                self.layout.operator(
                    "cp.quickreorder",
                    icon_value=icon_collection["icons"]["reorder"].icon_id,
                    text="",
                ).space = context.area.type
            if preferences().show_quick_focus_search_button and context.area.type == "VIEW_3D":
                self.layout.operator("cp.quickfocus", icon="VIEWZOOM", text="")
            self.layout.operator(
                "cp.settings", icon="PREFERENCES", text=""
            ).space = context.area.type

        if context.area.type == "VIEW_3D" and not preferences().easy_mode:
            if (
                not preferences().hide_dropdown_panels
                and preferences().use_dropdowns
                and len(preferences().dropdown_categories) > 0
            ):
                self.layout.prop(context.scene, "pap_active_dropdown_category", text="")

        row = self.layout.row(align=True)
        if draw_side == "LEFT":
            if not preferences().filtering_method == "Use N-Panel Filtering":
                row.prop(
                    context.workspace.category_indices,
                    f"filter_enabled{get_active_space(context.area.type)}",
                    text="",
                    icon="FILTER",
                    toggle=True,
                )
            else:
                row.prop(
                    preferences().categories,
                    f"filter_enabled{get_active_space(context.area.type)}",
                    text="",
                    icon="FILTER",
                    toggle=True,
                )
        row.separator(factor=1)
        pcoll = icon_collection["icons"]
        for index, a in enumerate(
            getattr(
                preferences(),
                f"workspace_categories{get_active_space(context.area.type)}",
            )
        ):
            # print(getattr(context.workspace,f'enabled_{index}'))
            if not preferences().filtering_method == "Use N-Panel Filtering":
                if getattr(
                    context.workspace.category_indices,
                    f"filter_enabled{get_active_space(context.area.type)}",
                ):
                    if a.icon in [b for b, _, _, _, _ in ALL_ICONS_ENUM]:
                        row.operator(
                            "cp.enablecategory",
                            text=a.name if a.icon == "NONE" else "",
                            icon=a.icon,
                            depress=getattr(
                                context.workspace.category_indices,
                                f"enabled{get_active_space(context.area.type)}_{index}",
                            ),
                        ).index = index
                    else:
                        row.operator(
                            "cp.enablecategory",
                            text=a.name if a.icon == "NONE" else "",
                            icon_value=pcoll[a.icon].icon_id,
                            depress=getattr(
                                context.workspace.category_indices,
                                f"enabled{get_active_space(context.area.type)}_{index}",
                            ),
                        ).index = index
                    # row.prop(context.workspace.category_indices,f'enabled_{index}',text=a.name if a.icon=='NONE' else "",icon=a.icon)
            else:
                if getattr(
                    preferences().categories,
                    f"filter_enabled{get_active_space(context.area.type)}",
                ):
                    if a.icon in [b for b, _, _, _, _ in ALL_ICONS_ENUM]:
                        row.operator(
                            "cp.enablecategory",
                            text=a.name if a.icon == "NONE" else "",
                            icon=a.icon,
                            depress=getattr(
                                preferences().categories,
                                f"enabled{get_active_space(context.area.type)}_{index}",
                            ),
                        ).index = index
                    else:
                        row.operator(
                            "cp.enablecategory",
                            text=a.name if a.icon == "NONE" else "",
                            icon_value=pcoll[a.icon].icon_id,
                            depress=getattr(
                                preferences().categories,
                                f"enabled{get_active_space(context.area.type)}_{index}",
                            ),
                        ).index = index
        if preferences().show_button_to_load_uncategorized and getattr(
            preferences().categories,
            f"filter_enabled{get_active_space(context.area.type)}",
        ):
            row.separator(factor=1)
            row.operator(
                "cp.enableuncategorized",
                text="",
                icon="HAND",
                depress=getattr(
                    context.scene,
                    f"load_uncategorized{get_active_space(context.area.type)}",
                ),
            )
        row.separator(factor=1)
        if draw_side == "RIGHT":
            if not preferences().filtering_method == "Use N-Panel Filtering":
                row.prop(
                    context.workspace.category_indices,
                    f"filter_enabled{get_active_space(context.area.type)}",
                    text="",
                    icon="FILTER",
                    toggle=True,
                )
            else:
                row.prop(
                    preferences().categories,
                    f"filter_enabled{get_active_space(context.area.type)}",
                    text="",
                    icon="FILTER",
                    toggle=True,
                )
            row.separator(factor=1)
            row.operator(
                "cp.settings", icon="PREFERENCES", text=""
            ).space = context.area.type
            if preferences().show_quick_reorder:
                row.operator(
                    "cp.quickreorder",
                    icon_value=icon_collection["icons"]["reorder"].icon_id,
                    text="",
                ).space = context.area.type
            if preferences().show_quick_focus_search_button and context.area.type == "VIEW_3D":
                self.layout.operator("cp.quickfocus", icon="VIEWZOOM", text="")

def draw_side_changed(self, context):
    # has_bc=[a for a in bpy.types.VIEW3D_HT_header.draw._draw_funcs[:] if a.__name__=='draw_handler']
    # print("Draw side changed")
    if self.draw_side == "RIGHT":
        try:
            bpy.types.VIEW3D_HT_header.remove(draw_dropdowns)
        except:
            pass
        try:
            bpy.types.VIEW3D_MT_editor_menus.remove(draw_dropdowns)
        except:
            pass
        try:
            bpy.types.VIEW3D_HT_tool_header.remove(draw_filter_buttons)
        except:
            pass
        try:
            bpy.types.VIEW3D_HT_tool_header.remove(draw_dropdowns)
        except:
            pass
        if not preferences().move_dropdowns_to_toolbar:
            if (
                not bpy.types.VIEW3D_HT_header.is_extended()
                or draw_dropdowns not in bpy.types.VIEW3D_HT_header.draw._draw_funcs[:]
            ):
                bpy.types.VIEW3D_HT_header.append(draw_dropdowns)
        else:
            if (
                not bpy.types.VIEW3D_HT_tool_header.is_extended()
                or draw_dropdowns
                not in bpy.types.VIEW3D_HT_tool_header.draw._draw_funcs[:]
            ):
                bpy.types.VIEW3D_HT_tool_header.append(draw_dropdowns)
        if (
            not bpy.types.VIEW3D_HT_tool_header.is_extended()
            or draw_filter_buttons
            not in bpy.types.VIEW3D_HT_tool_header.draw._draw_funcs[:]
        ):
            bpy.types.VIEW3D_HT_tool_header.append(draw_filter_buttons)
    else:
        try:
            bpy.types.VIEW3D_HT_header.remove(draw_dropdowns)
        except:
            pass
        try:
            bpy.types.VIEW3D_MT_editor_menus.remove(draw_dropdowns)
        except:
            pass
        try:
            bpy.types.VIEW3D_HT_tool_header.remove(draw_filter_buttons)
        except:
            pass
        try:
            bpy.types.VIEW3D_HT_tool_header.remove(draw_dropdowns)
        except:
            pass
        if not preferences().move_dropdowns_to_toolbar:
            if (
                not bpy.types.VIEW3D_MT_editor_menus.is_extended()
                or draw_dropdowns
                not in bpy.types.VIEW3D_MT_editor_menus.draw._draw_funcs[:]
            ):
                bpy.types.VIEW3D_MT_editor_menus.append(draw_dropdowns)
        else:
            if (
                not bpy.types.VIEW3D_HT_tool_header.is_extended()
                or draw_dropdowns
                not in bpy.types.VIEW3D_HT_tool_header.draw._draw_funcs[:]
            ):
                bpy.types.VIEW3D_HT_tool_header.prepend(draw_dropdowns)
        if (
            not bpy.types.VIEW3D_HT_tool_header.is_extended()
            or draw_filter_buttons
            not in bpy.types.VIEW3D_HT_tool_header.draw._draw_funcs[:]
        ):
            bpy.types.VIEW3D_HT_tool_header.prepend(draw_filter_buttons)
    savePreferences()
    return None


def exclusion_list_changed(self, context):
    for w in self.workspace_categories:
        for a in split_keep_substring(self.addons_to_exclude):
            # print(a,w.panels))
            if a in split_keep_substring(w.panels):
                w.panels = ",".join(
                    [b for b in split_keep_substring(w.panels) if b != a]
                )
    for w in self.workspace_categories_image_editor:
        for a in split_keep_substring(self.addons_to_exclude_image_editor):
            # print(a,w.panels))
            if a in split_keep_substring(w.panels):
                w.panels = ",".join(
                    [b for b in split_keep_substring(w.panels) if b != a]
                )
    for w in self.workspace_categories_node_editor:
        for a in split_keep_substring(self.addons_to_exclude_node_editor):
            # print(a,w.panels))
            if a in split_keep_substring(w.panels):
                w.panels = ",".join(
                    [b for b in split_keep_substring(w.panels) if b != a]
                )
    savePreferences()


def check_if_old_injection_exists(filename, variable_name="config_path"):
    with open(filename, "r") as f:
        text = f.read()
        if variable_name in text:
            return True
    return False


def inject_tracking_code(filename):
    config_folder_path = Path(bpy.utils.user_resource("SCRIPTS")).parent / "config"
    if not os.path.isdir(config_folder_path):
        os.makedirs(config_folder_path)
    if check_if_old_injection_exists(filename):
        data = []
        with open(filename, "r", newline="\n") as f:
            path = os.path.join(config_folder_path, "CP-PanelOrder.txt")

            for line in f.readlines():
                if "config_path=r" in line:
                    data.append(f"config_path=r'{path}'\n")
                else:
                    data.append(line)
        with open(filename, "w", newline="\n") as f:
            if data:
                f.writelines(data)
    else:
        with open(filename, "r") as f:
            text = f.read()
            config_folder_path = (
                Path(bpy.utils.user_resource("SCRIPTS")).parent / "config"
            )
            path = os.path.join(config_folder_path, "CP-PanelOrder.txt")
            text = text.replace(
                """system_resource,
)""",
                f"""system_resource,
)
import inspect
import os
import time
config_path=r'{path}'
try:
    mtime = os.path.getmtime(config_path) if os.path.exists(config_path) else 0
    if time.time()-mtime>10:
        with open(config_path, mode='w', newline='\\n', encoding='utf-8') as file:
            print('Creating Blank CP-PanelOrder file..')
except Exception as e:
    print(e)
panels=[]
scripts_directory=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),"startup")
def register_class(cl,write_to_file=True):
    try:
        if write_to_file and issubclass(cl,_bpy.types.Panel) and scripts_directory not in getattr(inspect.getmodule(cl),'__file__',""):
            with open(config_path, mode='a', newline='\\n', encoding='utf-8') as file:
                panels.append(getattr(cl,'bl_idname',cl.__name__))
                panels.append(cl.__name__)
                file.write(getattr(cl,'bl_idname',cl.__name__)+'\\n')
                file.write(cl.__name__+'\\n')
    except Exception as e:
        print(e)
    register_class_og(cl)""",
            )
            text = text.replace(
                "    register_class,", "    register_class as register_class_og,"
            )

        with open(filename, "w") as f:
            f.write(text)


def inject_code(filename):
    if check_if_old_injection_exists(filename):
        data = []
        with open(filename, "r", newline="\n") as f:
            config_folder_path = (
                Path(bpy.utils.user_resource("SCRIPTS")).parent / "config"
            )
            path = os.path.join(config_folder_path, "CP-config.txt")

            for line in f.readlines():
                if "config_path=r" in line:
                    data.append(f"    config_path=r'{path}'\n")
                else:
                    data.append(line)
        with open(filename, "w", newline="\n") as f:
            if data:
                f.writelines(data)
    else:
        with open(filename, "r") as f:
            text = f.read()
            config_folder_path = (
                Path(bpy.utils.user_resource("SCRIPTS")).parent / "config"
            )
            path = os.path.join(config_folder_path, "CP-config.txt")
            text = text.replace("for addon in _preferences.addons:", "import os")
            text = text.replace("    enable(addon.module)", f"config_path=r'{path}'")
            text1 = text[
                : text.index(f"config_path=r'{path}'") + len(f"config_path=r'{path}'")
            ]
            text2 = text[
                text.index(f"config_path=r'{path}'") + len(f"config_path=r'{path}'") :
            ]
            final_text = (
                text1
                + """
    order_of_addons=[]
    if os.path.isfile(config_path):
        with open(config_path, mode='r', newline='\\n', encoding='utf-8') as file:
            prefs = file.readlines()
            for p in prefs:
                try:
                    attr = p[:p.index("=>")]
                    type = p[p.index("=>")+2:p.index("===")]
                    value = p[p.index("===")+3:]
                    value = value.replace("\\n", "")
                    if attr =='addon_order' and type=='order':
                        panels=value[value.index(">>")+2:]
                        order_of_addons=panels.split(',')
                except:
                    pass
        
    for addon in order_of_addons:
        if addon in [a.module for a in _preferences.addons]:
            enable(addon)
    
    for addon in _preferences.addons:
        if addon.module not in order_of_addons:
            enable(addon.module)"""
                + text2
            )

        with open(filename, "w") as f:
            f.write(final_text)


def remove_delayed_load_code2(filename):
    if check_if_old_injection_exists(filename, variable_name="atl_file"):
        with open(filename, "r") as f:
            text = f.read()
            config_folder_path = (
                Path(bpy.utils.user_resource("SCRIPTS")).parent / "config"
            )
            path = os.path.join(config_folder_path, "CP-Addons To Load on Boot.txt")
            text = text.replace("atl_file=", "#Line_To_Remove")
            if bpy.app.version >= (4, 0, 0):
                text = text.replace(
                    """
def reset_all(*, reload_scripts=False,cp=False):
    import sys

    # initializes addons_fake_modules
    modules_refresh()
    import os""",
                    "",
                )
                text = text.replace(
                    """
    addons_to_load_on_boot=['CleanPanels',]
    if os.path.exists(atl_file):
        with open(atl_file,mode='r') as f:
            for line in f.readlines():
                addons_to_load_on_boot.append(line.strip())
    for path, pkg_id in _paths_with_extension_repos():
        if not pkg_id:
            _bpy.utils._sys_path_ensure_append(path)
        
        for mod_name, _mod_path in _bpy.path.module_names(path, package=pkg_id):
            
            if cp or mod_name in addons_to_load_on_boot or os.path.dirname(os.path.dirname(os.path.dirname(sys.executable))) in _mod_path:
                is_enabled, is_loaded = check(mod_name)
                # first check if reload is needed before changing state.
                if reload_scripts:
                    import importlib
                    mod = sys.modules.get(mod_name)
                    if mod:
                        importlib.reload(mod)

                if is_enabled == is_loaded:
                    pass
                elif is_enabled:
                    enable(mod_name)
                elif is_loaded:
                    print("	addon_utils.reset_all unloading", mod_name)
                    disable(mod_name)""",
                    "",
                )
                text = text.replace(
                    """    addons_to_load_on_boot=['CleanPanels','io_anim_bvh', 'io_curve_svg', 'io_mesh_ply', 'io_mesh_uv_layout', 'io_mesh_stl', 'io_scene_fbx', 'io_scene_gltf2', 'io_scene_obj', 'io_scene_x3d', 'cycles', 'node_presets', 'development_iskeyfree','development_icon_get','add_curve_extra_objects', 'add_mesh_extra_objects','space_view3d_spacebar_menu', 'development_edit_operator', 'add_camera_rigs','add_curve_sapling', 'add_mesh_BoltFactory', 'add_mesh_discombobulator', 'add_mesh_geodesic_domes', 'blender_id,btrace', 'system_blend_info', 'system_property_chart', 'io_anim_camera', 'io_export_dxf', 'io_export_pc2', 'io_import_BrushSet', 'io_import_dxf', 'io_import_images_as_planes', 'mesh_bsurfaces', 'context_browser', 'io_mesh_atomic', 'io_import_palette', 'io_scene_usdz', 'io_shape_mdd', 'lighting_tri_lights', 'lighting_dynamic_sky', 'mesh_inset', 'ui_translate', 'clouds_generator', 'blender_id', 'btrace', 'curve_assign_shapekey', 'curve_simplify', 'depsgraph_debug', 'sun_position', 'mesh_auto_mirror', 'mesh_f2', 'mesh_snap_utilities_line', 'MSPlugin', 'NodePreview', 'object_fracture_cell', 'object_scatter', 'object_skinify', 'render_copy_settings', 'space_view3d_3d_navigation', 'space_view3d_brush_menus', 'space_view3d_copy_attributes', 'space_view3d_math_vis', 'object_carver', 'object_color_rules', 'render_freestyle_svg', 'render_ui_animation_render', 'space_view3d_modifier_tools', 'space_view3d_pie_menus']
    if os.path.exists(atl_file):
        with open(atl_file,mode='r') as f:
            for line in f.readlines():
                addons_to_load_on_boot.append(line.strip())
    
    for addon in _preferences.addons:
        if addon.module in addons_to_load_on_boot:
            if addon.module in ['CleanPanels',]:
                enable(addon.module)""",
                    """    for addon in _preferences.addons:
        enable(addon.module)
                """,
                )
            else:
                text = text.replace(
                    """    addons_to_load_on_boot=['CleanPanels',]
    if os.path.exists(atl_file):
        with open(atl_file,mode='r') as f:
            for line in f.readlines():
                addons_to_load_on_boot.append(line.strip())
    
    for addon in _preferences.addons:
        if addon.module in addons_to_load_on_boot:
            enable(addon.module)""",
                    """
    for addon in _preferences.addons:
        enable(addon.module)""",
                )
                text = text.replace(
                    """    addons_to_load_on_boot=['CleanPanels','io_anim_bvh', 'io_curve_svg', 'io_mesh_ply', 'io_mesh_uv_layout', 'io_mesh_stl', 'io_scene_fbx', 'io_scene_gltf2', 'io_scene_obj', 'io_scene_x3d', 'cycles', 'node_presets', 'development_iskeyfree','development_icon_get','add_curve_extra_objects', 'add_mesh_extra_objects','space_view3d_spacebar_menu', 'development_edit_operator', 'add_camera_rigs','add_curve_sapling', 'add_mesh_BoltFactory', 'add_mesh_discombobulator', 'add_mesh_geodesic_domes', 'blender_id,btrace', 'system_blend_info', 'system_property_chart', 'io_anim_camera', 'io_export_dxf', 'io_export_pc2', 'io_import_BrushSet', 'io_import_dxf', 'io_import_images_as_planes', 'mesh_bsurfaces', 'context_browser', 'io_mesh_atomic', 'io_import_palette', 'io_scene_usdz', 'io_shape_mdd', 'lighting_tri_lights', 'lighting_dynamic_sky', 'mesh_inset', 'ui_translate', 'clouds_generator', 'blender_id', 'btrace', 'curve_assign_shapekey', 'curve_simplify', 'depsgraph_debug', 'sun_position', 'mesh_auto_mirror', 'mesh_f2', 'mesh_snap_utilities_line', 'MSPlugin', 'NodePreview', 'object_fracture_cell', 'object_scatter', 'object_skinify', 'render_copy_settings', 'space_view3d_3d_navigation', 'space_view3d_brush_menus', 'space_view3d_copy_attributes', 'space_view3d_math_vis', 'object_carver', 'object_color_rules', 'render_freestyle_svg', 'render_ui_animation_render', 'space_view3d_modifier_tools', 'space_view3d_pie_menus']
    if os.path.exists(atl_file):
        with open(atl_file,mode='r') as f:
            for line in f.readlines():
                addons_to_load_on_boot.append(line.strip())
    
    for addon in _preferences.addons:
        if addon.module in addons_to_load_on_boot:
            enable(addon.module)""",
                    """
    for addon in _preferences.addons:
        enable(addon.module)""",
                )

            text = text.replace("def reset_all_cp_old(", "def reset_all(")
        final_text = text
        with open(filename, "w") as f:
            f.write(final_text)


def inject_delayed_load_code_old(filename):
    if check_if_old_injection_exists(filename, variable_name="atl_file"):
        data = []
        with open(filename, "r", newline="\n") as f:
            config_folder_path = (
                Path(bpy.utils.user_resource("SCRIPTS")).parent / "config"
            )
            path = os.path.join(config_folder_path, "CP-Addons To Load on Boot.txt")

            for line in f.readlines():
                if "atl_file=r" in line:
                    data.append(f"    atl_file=r'{path}'\n")
                else:
                    data.append(line)
        with open(filename, "w", newline="\n") as f:
            if data:
                f.writelines(data)
    else:
        with open(filename, "r") as f:
            text = f.read()
            config_folder_path = (
                Path(bpy.utils.user_resource("SCRIPTS")).parent / "config"
            )
            path = os.path.join(config_folder_path, "CP-Addons To Load on Boot.txt")
            if bpy.app.version < (4, 0, 0):
                txt_to_replace = """    for addon in _preferences.addons:
        enable(addon.module)"""
                replacement_text = """
    import os
    atl_file=cp_config_file_path
    addons_to_load_on_boot=['CleanPanels','io_anim_bvh', 'io_curve_svg', 'io_mesh_ply', 'io_mesh_uv_layout', 'io_mesh_stl', 'io_scene_fbx', 'io_scene_gltf2', 'io_scene_obj', 'io_scene_x3d', 'cycles', 'node_presets', 'development_iskeyfree','development_icon_get','add_curve_extra_objects', 'add_mesh_extra_objects','space_view3d_spacebar_menu', 'development_edit_operator', 'add_camera_rigs','add_curve_sapling', 'add_mesh_BoltFactory', 'add_mesh_discombobulator', 'add_mesh_geodesic_domes', 'blender_id,btrace', 'system_blend_info', 'system_property_chart', 'io_anim_camera', 'io_export_dxf', 'io_export_pc2', 'io_import_BrushSet', 'io_import_dxf', 'io_import_images_as_planes', 'mesh_bsurfaces', 'context_browser', 'io_mesh_atomic', 'io_import_palette', 'io_scene_usdz', 'io_shape_mdd', 'lighting_tri_lights', 'lighting_dynamic_sky', 'mesh_inset', 'ui_translate', 'clouds_generator', 'blender_id', 'btrace', 'curve_assign_shapekey', 'curve_simplify', 'depsgraph_debug', 'sun_position', 'mesh_auto_mirror', 'mesh_f2', 'mesh_snap_utilities_line', 'MSPlugin', 'NodePreview', 'object_fracture_cell', 'object_scatter', 'object_skinify', 'render_copy_settings', 'space_view3d_3d_navigation', 'space_view3d_brush_menus', 'space_view3d_copy_attributes', 'space_view3d_math_vis', 'object_carver', 'object_color_rules', 'render_freestyle_svg', 'render_ui_animation_render', 'space_view3d_modifier_tools', 'space_view3d_pie_menus']
    if os.path.exists(atl_file):
        with open(atl_file,mode='r') as f:
            for line in f.readlines():
                addons_to_load_on_boot.append(line.strip())
    
    for addon in _preferences.addons:
        if addon.module in addons_to_load_on_boot:
            enable(addon.module)"""
                text = text.replace(txt_to_replace, replacement_text)
                final_text = text
            else:
                txt_to_replace = """    for addon in _preferences.addons:
        enable(addon.module)"""
                replacement_text = """
    import os
    atl_file=cp_config_file_path
    addons_to_load_on_boot=['CleanPanels','io_anim_bvh', 'io_curve_svg', 'io_mesh_ply', 'io_mesh_uv_layout', 'io_mesh_stl', 'io_scene_fbx', 'io_scene_gltf2', 'io_scene_obj', 'io_scene_x3d', 'cycles', 'node_presets', 'development_iskeyfree','development_icon_get','add_curve_extra_objects', 'add_mesh_extra_objects','space_view3d_spacebar_menu', 'development_edit_operator', 'add_camera_rigs','add_curve_sapling', 'add_mesh_BoltFactory', 'add_mesh_discombobulator', 'add_mesh_geodesic_domes', 'blender_id,btrace', 'system_blend_info', 'system_property_chart', 'io_anim_camera', 'io_export_dxf', 'io_export_pc2', 'io_import_BrushSet', 'io_import_dxf', 'io_import_images_as_planes', 'mesh_bsurfaces', 'context_browser', 'io_mesh_atomic', 'io_import_palette', 'io_scene_usdz', 'io_shape_mdd', 'lighting_tri_lights', 'lighting_dynamic_sky', 'mesh_inset', 'ui_translate', 'clouds_generator', 'blender_id', 'btrace', 'curve_assign_shapekey', 'curve_simplify', 'depsgraph_debug', 'sun_position', 'mesh_auto_mirror', 'mesh_f2', 'mesh_snap_utilities_line', 'MSPlugin', 'NodePreview', 'object_fracture_cell', 'object_scatter', 'object_skinify', 'render_copy_settings', 'space_view3d_3d_navigation', 'space_view3d_brush_menus', 'space_view3d_copy_attributes', 'space_view3d_math_vis', 'object_carver', 'object_color_rules', 'render_freestyle_svg', 'render_ui_animation_render', 'space_view3d_modifier_tools', 'space_view3d_pie_menus']
    if os.path.exists(atl_file):
        with open(atl_file,mode='r') as f:
            for line in f.readlines():
                addons_to_load_on_boot.append(line.strip())
    
    for addon in _preferences.addons:
        if addon.module in addons_to_load_on_boot:
            enable(addon.module)"""
                text = text.replace(txt_to_replace, replacement_text)
                text = text.replace("reset_all(", "reset_all_cp_old(")
                if "order_of_addons" in text:
                    if "if addon.module in ['CleanPanels',]" not in text:
                        text = text.replace(
                            "            enable(addon.module)",
                            "            if addon.module in ['CleanPanels',]:\n                enable(addon.module)",
                        )
                        text = text.replace(
                            "            enable(addon)",
                            "            if addon in ['CleanPanels',]:\n                enable(addon)",
                        )
                else:
                    if "if addon.module in ['CleanPanels',]" not in text:
                        pass
                        # text=text.replace("        enable(addon.module)","        if addon.module in ['CleanPanels',]:\n                enable(addon.module)")
                text1 = text[: text.index(f"def reset_all_cp_old")]
                text2 = text[text.index(f"def reset_all_cp_old") :]
                insert_for_blender4 = """
def reset_all(*, reload_scripts=False,cp=False):
    import sys

    # initializes addons_fake_modules
    modules_refresh()
    import os
    atl_file=cp_config_file_path
    addons_to_load_on_boot=['CleanPanels',]
    if os.path.exists(atl_file):
        with open(atl_file,mode='r') as f:
            for line in f.readlines():
                addons_to_load_on_boot.append(line.strip())
    for path, pkg_id in _paths_with_extension_repos():
        if not pkg_id:
            _bpy.utils._sys_path_ensure_append(path)
        
        for mod_name, _mod_path in _bpy.path.module_names(path, package=pkg_id):
            
            if cp or mod_name in addons_to_load_on_boot or os.path.dirname(os.path.dirname(os.path.dirname(sys.executable))) in _mod_path:
                is_enabled, is_loaded = check(mod_name)
                # first check if reload is needed before changing state.
                if reload_scripts:
                    import importlib
                    mod = sys.modules.get(mod_name)
                    if mod:
                        importlib.reload(mod)

                if is_enabled == is_loaded:
                    pass
                elif is_enabled:
                    enable(mod_name)
                elif is_loaded:
                    print("\taddon_utils.reset_all unloading", mod_name)
                    disable(mod_name)
"""

                final_text = text1 + (insert_for_blender4) + text2
        final_text = final_text.replace("cp_config_file_path", f"r'{path}'")
        with open(filename, "w") as f:
            f.write(final_text)


def inject_delayed_load_code(filename, remove=False):
    actual_blender_version = (
        f"{bpy.app.version[0]}.{bpy.app.version[1]}.{bpy.app.version[2]}"
    )
    blender_version = f"{bpy.app.version[0]}.{bpy.app.version[1]}"

    # Handling specific Blender versions
    if bpy.app.version >= (4, 2, 1):
        blender_version = f"{bpy.app.version[0]}.{bpy.app.version[1]}.1"
    if bpy.app.version >= (4, 2, 3):
        blender_version = f"{bpy.app.version[0]}.{bpy.app.version[1]}.3"
    if bpy.app.version >= (4, 2, 4):
        blender_version = "4.3.0"
    if bpy.app.version >= (4, 3, 0):
        blender_version = f"{bpy.app.version[0]}.{bpy.app.version[1]}.0"

    # Paths
    base_path = os.path.dirname(__file__)
    version_directory = os.path.join(
        base_path, "OG_Blender_Python_Files", blender_version
    )
    backups_folder = os.path.join(
        os.path.dirname(base_path), "CP_Backup_Scripts", "Backups"
    )
    backup_addon_utils_path = os.path.join(
        backups_folder, actual_blender_version, "addon_utils_backup.py"
    )
    modified_addon_utils_path = os.path.join(
        version_directory, "addon_utils_cp.py" if not remove else "addon_utils.py"
    )

    # Ensure the version directory exists
    os.makedirs(version_directory, exist_ok=True)
    os.makedirs(os.path.join(backups_folder, actual_blender_version), exist_ok=True)
    # Create a backup if it doesn't already exist
    if not os.path.exists(backup_addon_utils_path):
        original_addon_utils_path = addon_utils.__file__
        with open(original_addon_utils_path, "r") as original_file:
            with open(backup_addon_utils_path, "w") as backup_file:
                backup_file.write(original_file.read())

    # Prepare the path to use when removing delayed load code
    if remove:
        source_path = (
            backup_addon_utils_path
            if os.path.exists(backup_addon_utils_path)
            else addon_utils.__file__
        )
    else:
        source_path = modified_addon_utils_path

    # Prepare ATL file path
    config_folder_path = Path(bpy.utils.user_resource("SCRIPTS")).parent / "config"
    atl_file_path = os.path.join(config_folder_path, "CP-Addons To Load on Boot.txt")

    # Modify and write the addon_utils file
    text = ""
    with open(source_path, "r") as f:
        text = f.read()
    if text and not remove:
        text = text.replace("ATL_FILE_PATH", f"r'{atl_file_path}'")
    with open(filename, "w+") as f:
        f.write(text)


def remove_delayed_load_code(filename):
    inject_delayed_load_code(filename, True)


kmaps_object_mode = [
    "cp.callcategoriespie",
    "cp.togglefiltering",
    "cp.callwspie",
    "cp.callpanelslist",
    "cp.quickfocus",
    "cp.callfavoritespie",
]


def draw_addons_list(layout, context, space="VIEW_3D"):
    space = "_" + space
    if space == "_VIEW_3D":
        space = ""
    # layout.label(text="N-Panel Order")
    column = layout.column()
    column = column.split(factor=0.9)
    column.template_list(
        "CP_UL_Addons_Order_List",
        "",
        preferences(),
        f"addon_info{space.lower()}",
        preferences(),
        f"addon_info{space.lower()}_index",
        item_dyntip_propname="name",
        rows=12,
    )
    column = column.column(align=True)
    column.operator("cp.loadaddons", text="", icon="FILE_REFRESH")
    column.separator()
    column.operator("cp.moveaddon", text="", icon="SORT_DESC").direction = "UP"
    column.operator("cp.moveaddon", text="", icon="SORT_ASC").direction = "DOWN"


def draw_addons_list_for_renaming(layout, context, space="VIEW_3D"):
    space = "_" + space
    if space == "_VIEW_3D":
        space = ""

    # layout.label(text="N-Panel Renaming")
    column = layout.column()
    column = column.split(factor=0.9)
    column.template_list(
        "CP_UL_Addons_Order_List_For_Renaming",
        "",
        preferences(),
        f"addon_info_for_renaming{space.lower()}",
        preferences(),
        f"addon_info_for_renaming{space.lower()}_index",
        item_dyntip_propname="name",
        rows=12,
    )
    column = column.column(align=True)
    column.operator("cp.loadaddonsforrenaming", text="", icon="FILE_REFRESH")
    column.separator()
    column.operator("cp.resettabname", text="", icon="LOOP_BACK")


def draw_hotkeys(col, km_name):
    kc = bpy.context.window_manager.keyconfigs.user
    for kmi in kmaps_object_mode:
        km2 = kc.keymaps[km_name]
        kmi2 = []
        for a, b in km2.keymap_items.items():
            if a == kmi:
                kmi2.append(b)
        if kmi2:
            for a in kmi2:
                col.context_pointer_set("keymap", km2)
                rna_keymap_ui.draw_kmi([], kc, km2, a, col, 0)


def draw_settings2(instance, self, context, is_preferences=True):
    layout = instance.layout
    layout2 = layout.box()
    active_tab = self.active_tab if is_preferences else self.active_tab_quick_settings
    # row = layout2.row(align=True)
    # row.alignment = 'LEFT'
    # row.prop(self, "show_keymaps", emboss=False,
    #         icon="TRIA_DOWN" if self.show_keymaps else "TRIA_RIGHT")
    if is_preferences and draw_dropdown_panel(layout2, self, "show_keymaps"):
        draw_hotkeys(layout2, "3D View")
    if is_preferences:
        layout2 = layout.box()
        if draw_dropdown_panel(layout2, self, "show_advanced"):
            layout2.prop(self, "custom_icons_dir")
            layout2.label(
                text="Clean Up method for N-Panel (Restart Blender after changing this):"
            )
            layout2.row().prop(self, "filtering_method", expand=True)
            layout2.prop(self, "hide_pie_panels")
            layout2.prop(self, "hide_dropdown_panels")
            layout2.prop(self, "use_sticky_popup")
            layout2.prop(self, "sort_focus_menu_based_on_clicks")
            layout2.prop(self, "filtering_per_workspace")
            layout2.prop(self, "remove_holder_tab")
            # layout2.prop(self,'show_delete_buttons_in_quick_settings')
            layout2.prop(self, "use_enum_search_for_popups")
            layout2.prop(self, "filter_internal_tabs")
            layout2.prop(self, "show_enabledisable_in_quick_settings")
            layout2.prop(self, "remove_uninstalled_addons")
            layout2.operator("cp.resetconfig", icon="ERROR")
            layout.prop(self, "experimental")
            if self.experimental:
                layout.label(
                    text="Make sure you backup your addon directory before using Experimental Features!",
                    icon="ERROR",
                )
                layout.prop(self, "auto_backup_addons")
    if is_preferences:
        layout.prop(self, "draw_side")
    if is_preferences or self.show_enabledisable_in_quick_settings:
        layout.operator("cp.addonsinfo", icon="SCRIPTPLUGINS")
    layout.separator()
    if is_preferences:
        layout2 = layout
        layout.separator()
        layout.row().prop(self, "space_type", expand=True)
        layout.separator()
        layout3 = layout2.box()
        layout3.row().prop(self, "active_tab", expand=True)
    else:
        layout3 = layout2.box()
        layout3.row().prop(self, "active_tab_quick_settings", expand=True)
    layout.separator()
    if True:
        if True:
            if is_preferences:
                # layout3 = layout2.box()
                # row = layout3.row(align=True)
                # row.alignment = 'LEFT'

                # row.prop(self, "show_npanel_ordering", emboss=False,
                #         icon="TRIA_DOWN" if self.show_npanel_ordering else "TRIA_RIGHT")

                if active_tab == "Reordering":
                    draw_reordering_section(self, context, layout3)

                if (
                    self.experimental
                    or self.filtering_method == "Use N-Panel Filtering"
                ):
                    # layout3 = layout2.box()
                    # row = layout3.row(align=True)
                    # row.alignment = 'LEFT'

                    # row.prop(self, "show_npanel_renaming", emboss=False,
                    #     icon="TRIA_DOWN" if self.show_npanel_renaming else "TRIA_RIGHT")
                    # if self.show_npanel_renaming:
                    if active_tab == "Renaming":
                        draw_renaming_section(self, context, layout3)

        if self.space_type == "VIEW_3D":
            # layout3 = layout2.box()
            # row = layout3.row(align=True)
            # row.alignment = 'LEFT'
            # row.prop(self, "show_panel_categories", emboss=False,
            #         icon="TRIA_DOWN" if self.show_panel_categories else "TRIA_RIGHT")
            if active_tab == "Pie":
                draw_pie_panels_section(self, is_preferences, layout3)
            # layout3 = layout2.box()
            # row = layout3.row(align=True)
            # row.alignment = 'LEFT'
            # row.prop(self, "show_dropdown_categories", emboss=False,
            #         icon="TRIA_DOWN" if self.show_dropdown_categories else "TRIA_RIGHT")

            # if self.show_dropdown_categories:
            if active_tab == "DropDown":
                draw_dropdowns_section(self, is_preferences, layout3)
        pcoll = icon_collection["icons"]

        # layout3 = layout2.box()
        # row = layout3.row(align=True)
        # row.alignment = 'LEFT'
        # row.prop(self, "show_workspace_categories", emboss=False,text="Workspace Addon Categories" if self.filtering_method!="Use N-Panel Filtering" else "N-Panel Categories",
        #         icon="TRIA_DOWN" if self.show_workspace_categories else "TRIA_RIGHT")
        # if self.show_workspace_categories:
        if active_tab == "Filtering":
            draw_filtering_section(self, is_preferences, layout3, pcoll)
        # if is_preferences:

        # layout3 = layout2.box()

        # row = layout3.row(align=True)
        # row.alignment = 'LEFT'
        # row.prop(self, "show_focus_panel_categories", emboss=False,
        #         icon="TRIA_DOWN" if self.show_dropdown_categories else "TRIA_RIGHT")

        # if self.show_focus_panel_categories:
        if active_tab == "FP":
            draw_focus_panel_section(self, is_preferences, layout3)
    return layout2


def draw_guide_section(layout, context, first_time=False):
    from .guide_ops import cp_guides

    if cp_guides.preferences.showing:
        cp_guides["preferences"].draw(layout, context)
        return
    guide_col = layout.column()
    if first_time:
        guide_col.scale_y = 2
        row = guide_col.row()
        row.alert = True
        row.alignment = "CENTER"
        if cp_guides.preferences.started_once:
            row.label(
                text="Seems like you left the guide hanging. Want to pick up where you left off?"
            )
        else:
            row.label(text="Welcome To Clean Panels! Click this button to get started!")
    row = guide_col.row()
    row.alignment = "CENTER"
    if first_time:
        row = row.split(align=True, factor=0.8)
    row.operator(
        "cp.start_guide",
        icon_value=cp_guides.get_icon("guide"),
        text="Start Guide" if first_time else "Restart Guide",
    ).guide_id = "preferences"
    if first_time:
        row.operator(
            "cp.skip_guide", icon="PANEL_CLOSE", text="Skip"
        ).guide_id = "preferences"


def draw_settings(instance, self, context, is_preferences=True):
    if self.config_corrupted:
        alert_row = self.layout.row()
        alert_row.alert = True
        alert_row.label(
            text="Apologies! It seems your config file was corrupted, possibly due to a Blender crash. We've restored your settings from a backup. If you notice anything missing, you may need to redo recent changes.",
            icon="ERROR",
        )
    layout = instance.layout
    tab_row = layout.row()
    tab_row.scale_y = 2
    tab_row.prop(self, "main_tabs", expand=True)
    layout2 = layout
    pcoll = icon_collection["icons"]
    active_tab = self.active_tab if is_preferences else self.active_tab_quick_settings
    if self.main_tabs == "Keymaps":
        btn_row = layout2.row(align=True)
        btn_row.alignment = "RIGHT"
        btn_row.operator("cp.restore_keymaps", icon="KEY_HLT")
        draw_hotkeys(layout2, "3D View")
    if self.main_tabs == "Config":
        box = layout2.box()
        easy_mode_row = box.row()
        easy_mode_row.prop(self, "easy_mode", toggle=True)
        easy_mode_row.scale_y = 2
        grid = box.grid_flow(columns=2, row_major=True)
        # if not self.easy_mode:
        grid.prop(self, "hide_pie_panels")
        grid.prop(self, "hide_dropdown_panels")
        # grid.prop(self,'use_filtering_in_node_editor')
        # grid.prop(self,'use_filtering_in_image_editor')
        if self.filtering_method == "Use N-Panel Filtering":
            grid.prop(self, "sort_per_category")

        grid.prop(self, "sort_focus_menu_based_on_clicks")
        grid.prop(self, "filtering_per_workspace")
        grid.prop(self, "use_sticky_popup")
        # grid.prop(self,'remove_holder_tab')
        # grid.prop(self,'show_enabledisable_in_quick_settings')
        grid.enabled = not self.easy_mode
        layout.prop(self, "draw_side")
        row = layout.row()
        row.prop(
            self, "show_quick_reorder", toggle=True, icon_value=pcoll["reorder"].icon_id
        )
        row.prop(self, "show_button_to_load_uncategorized", icon="HAND")
        row.prop(self,'show_quick_focus_search_button',icon='VIEWZOOM')
        layout2.prop(self, "custom_icons_dir")

        if is_preferences or self.show_enabledisable_in_quick_settings:
            layout.operator("cp.addonsinfo", icon="SCRIPTPLUGINS")
        # layout2.label(text="Clean Up method for N-Panel (Restart Blender after changing this):")
        # layout2.row().prop(self,'filtering_method',expand=True)

        # layout2.prop(self,'show_delete_buttons_in_quick_settings')
        layout2.prop(self, "use_enum_search_for_popups")
        layout2.prop(self, "filter_internal_tabs")

        layout2.prop(self, "remove_uninstalled_addons")
        # if not self.easy_mode:
        #     layout2.operator("cp.importworkspaces")

        # layout.prop(self,'experimental')
        # if self.experimental:

        #     layout.label(text="Make sure you backup your addon directory before using Experimental Features!",icon='ERROR')
        #     layout.prop(self,'auto_backup_addons')
        if bpy.app.version < (4, 2, 0):
            layout2.separator(factor=2)
        else:
            layout2.separator(factor=2, type="LINE")
        auto_setup_row = layout2.row(align=True)
        # auto_setup_row.scale_y=2
        auto_setup_row.alignment = "CENTER"
        auto_setup_row.operator("cp.autosetup", icon="SETTINGS")
        auto_setup_row.operator("cp.updatedatabase", icon="FILE_REFRESH")
        # auto_setup_row.prop(preferences(),'auto_run_magic_setup',toggle=True,icon='CHECKBOX_HLT' if preferences().auto_run_magic_setup else 'CHECKBOX_DEHLT')
        layout2.operator("cp.resetconfig", icon="ERROR")
        layout2.operator("cp.openconfigdirectory", icon="FILE_FOLDER")
        row = layout2.row(align=True)
        row.operator("cp.exportconfig", icon="EXPORT")
        row.operator("cp.importconfig", icon="IMPORT")
        row.operator(
            "cp.importconfig", icon="IMPORT", text="Import Backup Config"
        ).directory = os.path.join(
            Path(bpy.utils.user_resource("SCRIPTS")).parent / "config", "CP-Backups"
        )
        if bpy.app.version < (4, 2, 0):
            layout2.separator(factor=2)
        else:
            layout2.separator(factor=2, type="LINE")
        box = layout2.box()
        if draw_dropdown_panel(box, self, "show_fixes"):
            row = box.row()
            row.prop(self, "zen_uv_fix", text="Zen UV Fix")
    if self.main_tabs == "Help":
        box = layout2.box()
        box.label(text="Guides:")
        draw_guide_section(box, context, False)
        pcoll = icon_collection["icons"]
        youtube_icon = pcoll["youtube"]
        discord_icon = pcoll["discord"]
        row = layout2.row()
        row.operator(
            "wm.url_open", text="Documentation", icon="HELP"
        ).url = "https://rantools.github.io/clean-panels/"
        row = layout2.row(align=True)
        row.operator(
            "wm.url_open", text="Chat Support", icon_value=discord_icon.icon_id
        ).url = "https://discord.gg/Ta4P3uJXtQ"
        row.operator(
            "wm.url_open", text="Youtube", icon_value=youtube_icon.icon_id
        ).url = "https://www.youtube.com/channel/UCKgXKh-_kOgzdV8Q12kraHA"
        # layout2.separator(factor=2,type='LINE')

    if self.main_tabs == "Organize":
        if is_preferences:
            if not self.easy_mode:
                layout2 = layout
                layout.separator()
                layout.row().prop(self, "space_type", expand=True)
                layout.separator()
            layout3 = layout2
            tab_row = layout3.row()
            tab_row.scale_y = 2
            tab_row.prop(self, "active_tab", expand=True)
        else:
            layout3 = layout2
            layout3.row().prop(self, "active_tab_quick_settings", expand=True)
        # layout.separator()
        if is_preferences:
            if active_tab == "Reordering":
                draw_reordering_section(self, context, layout3)
            if self.experimental or self.filtering_method == "Use N-Panel Filtering":
                if active_tab == "Renaming":
                    draw_renaming_section(self, context, layout3)

        if self.space_type == "VIEW_3D":
            if active_tab == "Pie":
                draw_pie_panels_section(self, is_preferences, layout3)
            if active_tab == "DropDown":
                draw_dropdowns_section(self, is_preferences, layout3)
        pcoll = icon_collection["icons"]

        if active_tab == "Filtering":
            draw_filtering_section(self, is_preferences, layout3, pcoll)
        if active_tab == "FP":
            draw_focus_panel_section(self, is_preferences, layout3)
    if self.main_tabs == "PRO":
        self.draw_pro_settings(layout2)
    return layout2


def draw_quick_settings(instance, self, context, is_preferences=True):
    layout = instance.layout
    layout2 = layout
    layout3 = layout2
    # layout3.row().prop(self,'active_tab_quick_settings',expand=True)
    # layout.separator()
    pcoll = icon_collection["icons"]

    # if self.active_tab_quick_settings=='Filtering':
    draw_filtering_section(self, False, layout3, pcoll)
    # if self.active_tab_quick_settings=='FP':
    #     draw_focus_panel_section(self, is_preferences, layout3)
    return layout2


def draw_fp_favorites_section(self, layout):
    # h_row=layout.row(align=True)
    # h_row.alignment='CENTER'
    # h_row.label(text="Favorites")
    if bpy.app.version < (4, 2, 0):
        layout.separator()
    else:
        layout.separator(type="LINE")
    col1 = layout.row()
    # col1.label(text="Favorites:")
    list_row = col1.row()
    list_row.template_list(
        "CP_UL_Addons_Order_List", "", self, "favorites", self, "favorites_index"
    )
    button_col = list_row.column(align=True)
    button_col.operator("cp.add_favorite_focus_panel", icon="ADD", text="")
    button_col.operator("cp.remove_favorite_focus_panel", icon="REMOVE", text="")
    button_col.separator()
    button_col.operator(
        "cp.reorder_favorites", icon="TRIA_UP", text=""
    ).direction = "UP"
    button_col.operator(
        "cp.reorder_favorites", icon="TRIA_DOWN", text=""
    ).direction = "DOWN"

    o1, o2, o3, o4, o5, o6, o7, o8 = draw_pie_layout(col1.column())
    if len(preferences().favorites) > 7:
        for i in range(min(8, len(preferences().favorites))):
            if i == 2:
                continue
            slot = eval("o" + str(i + 1))
            slot.operator(
                "cp.edit_favorite_focus_panel",
                text=preferences().favorites[i].name
                if len(preferences().favorites) > i
                else " ",
                icon="GREASEPENCIL" if len(preferences().favorites) > i else "ERROR",
            ).index = i

        col = o3.column()
        col.operator(
            "cp.edit_favorite_focus_panel",
            text=preferences().favorites[2].name
            if len(preferences().favorites) > 2
            else " ",
            icon="GREASEPENCIL" if len(preferences().favorites) > 2 else "ERROR",
        ).index = 2
        for id, f in enumerate(preferences().favorites[8:]):
            col.operator(
                "cp.edit_favorite_focus_panel", text=f.name, icon="GREASEPENCIL"
            ).index = id + 8
        col.operator(
            "cp.add_favorite_focus_panel", icon="ADD", text="Add", depress=True
        )
    else:
        for i in range(8):
            l = eval("o" + str(i + 1))
            if i == len(preferences().favorites):
                l.operator(
                    "cp.add_favorite_focus_panel", icon="ADD", text="Add", depress=True
                )
            else:
                l.operator(
                    "cp.edit_favorite_focus_panel",
                    text=preferences().favorites[i].name
                    if len(preferences().favorites) > i
                    else " ",
                    icon="GREASEPENCIL"
                    if len(preferences().favorites) > i
                    else "ERROR",
                ).index = i
                l.enabled = len(preferences().favorites) > i


def draw_focus_panel_section(self, is_preferences, layout3):
    # first_row=layout3.row(align=True)

    help_row = layout3.row(align=True)
    help_row.alignment = "RIGHT"
    op = help_row.operator("cp.showhelp", text="Help", icon="HELP")
    op.text = "Focus Panel lets you choose the active tab to display in the side panel using a popup list. While creating categories isn't required, it can help keep the popup list more organized if you have many add-ons."
    op.link = "https://www.youtube.com/watch?v=mNUzhB3ybE0"
    row = layout3.column()
    row.prop(self, "only_show_unfiltered_panels")

    first_row = layout3.row(align=True)
    btn_row = first_row.row(align=True)
    btn_row.alignment = "LEFT"
    btn_row.operator("cp.batchassigncategories", icon="GROUP_VERTEX").category = "FP"
    btn_row = first_row.row(align=True)
    btn_row.alignment = "RIGHT"
    btn_row.operator("cp.fpcategoriesfromfiltering", icon="PASTEDOWN")
    row = layout3.column()
    if not getattr(self, f"focus_panel_categories{get_active_space()}"):
        text_row = row.row(align=True)
        text_row.alignment = "CENTER"
        text_row.label(
            text="Let’s begin with your first category! Click the button below to get started."
        )
    for index, a in enumerate(
        getattr(self, f"focus_panel_categories{get_active_space()}")
    ):
        # row.separator(factor=1)
        # row.separator(factor=1)
        row.separator(factor=0.2)
        box = row.box()
        if draw_category(
            box, a, "show", a.name, index, icon_collection["icons"], False, "FP"
        ):
            # row1=box.row()
            # row1=row1.split(factor=0.7)

            box.prop(a, "name", text="")
            # row2=row1.split(factor=0.75)
            # op = row2.operator('cp.remove_category_from_fp', text='',
            #                                 icon='PANEL_CLOSE')
            # op.index = index

            # op = row2.operator('cp.movecategory', text='',
            #                                 icon='TRIA_UP')
            # op.index = index
            # op.category = 'FP'
            # op.direction='UP'

            row1 = box.row()
            row1 = row1.split(factor=0.7)
            row2 = row1.row()
            row1 = row1.split(factor=0.75)
            row2.prop(a, "panels")
            if not a.panels:
                row2.enabled = False
            row1.operator(
                "cp.search_popup_for_fp", text="", icon="ADD", depress=True
            ).index = index
            op = row1.operator(
                "cp.reordercategory",
                text="",
                icon_value=icon_collection["icons"]["reorder"].icon_id,
            )
            op.index = index
            op.category = "FP"
            op.exclusion_list = False
            # op = row1.operator('cp.movecategory', text='',
            #                                 icon='TRIA_DOWN')
            # op.index = index
            # op.category = 'FP'
            # op.direction='DOWN'
            if is_preferences or self.show_delete_buttons_in_quick_settings:
                grid = box.grid_flow(columns=4, row_major=True)
                for panel in split_keep_substring(a.panels):
                    if panel:
                        op = grid.operator(
                            "cp.remove_panel", text=panel, icon="PANEL_CLOSE"
                        )
                        op.index = index
                        op.panel = panel
                        op.category = "FP"
    row.separator(factor=1)
    button_row = row.row(align=True)
    # button_row.scale_y=2
    button_row.alignment = "CENTER"
    button_row.operator("cp.add_category", icon="ADD").to = "FP"
    if self.space_type == "VIEW_3D":
        fav_box = layout3.box()
        if draw_dropdown_panel(fav_box, self, "show_favorites"):
            draw_fp_favorites_section(self, fav_box)


def draw_filtering_section(self, is_preferences, layout3, pcoll):
    if is_preferences:
        first_row = layout3.row(align=True)
        btn_row = first_row.row(align=True)
        btn_row.alignment = "LEFT"
        btn_row.operator("cp.batchassigncategories", icon="GROUP_VERTEX")
        help_row = first_row.row(align=True)
        help_row.alignment = "RIGHT"
        op = help_row.operator("cp.showhelp", text="Help", icon="HELP")
        op.text = "Filtering Categories help you hide tabs you don't want to see in the side panel. Create a category for each type of add-on (e.g., Nature, Tools, Lighting) and assign relevant add-ons to them. These categories will show up in the viewport header, and when a category is enabled, all add-ons except those in the active category (and the exclusion list) will be hidden."
        op.link = "https://www.youtube.com/watch?v=nvyZvp-r4oo"
    row = layout3.column()
    if not getattr(self, f"workspace_categories{get_active_space()}"):
        text_row = row.row(align=True)
        text_row.alignment = "CENTER"
        text_row.label(
            text="Let’s begin with your first category! Click the button below to get started."
        )

    for index, a in enumerate(
        getattr(self, f"workspace_categories{get_active_space()}")
    ):
        row.separator(factor=0.2)
        box = row.box()
        if draw_category(box, a, "show", a.name, index, pcoll, True, "Workspace"):
            # box.separator(factor=1)
            # box.separator(factor=1)
            # box=box.box()
            row1 = box.row()
            # row1=row1.split(factor=0.7)

            row1.prop(a, "name", text="")
            row2 = row1.split(factor=0.5)
            # if a.icon in ALL_ICONS:
            #     row2.operator("cp.change_icon",text="Icon",icon=a.icon if a.icon else None).index=index
            # else:
            #     row2.operator("cp.change_icon",text="Icon",icon_value=pcoll[a.icon].icon_id).index=index
            # row2=row2.split(factor=0.5)
            # op = row2.operator('cp.remove_category_from_workspace', text='',
            #                             icon='PANEL_CLOSE')
            # op.index = index

            # op = row2.operator('cp.movecategory', text='',
            #                             icon='TRIA_UP')
            # op.index = index
            # op.category = 'Workspace'
            # op.direction='UP'

            row1 = box.row()
            row1 = row1.split(factor=0.8)
            row2 = row1.row()
            row1 = row1.split(factor=0.77)
            row2.prop(a, "panels")
            if not a.panels:
                row2.enabled = False
            # if is_preferences:
            row3 = row1
            row3.operator(
                "cp.search_popup_for_workspace", text="", icon="ADD", depress=True
            ).index = index
            op = row3.operator(
                "cp.reordercategory",
                text="",
                icon_value=icon_collection["icons"]["reorder"].icon_id,
            )
            op.index = index
            op.category = "WORKSPACE"
            op.exclusion_list = False
            # else:
            #     row1.operator("cp.search_popup_for_workspace",text="",icon="ADD",depress=True).index=index
            # op = row1.operator('cp.movecategory', text='',
            #                             icon='TRIA_DOWN')
            # op.index = index
            # op.category = 'Workspace'
            # op.direction='DOWN'

            # if is_preferences or self.show_delete_buttons_in_quick_settings:
            grid = box.grid_flow(columns=4, row_major=True)
            for panel in split_keep_substring(a.panels):
                if panel:
                    op = grid.operator(
                        "cp.remove_panel", text=panel, icon="PANEL_CLOSE"
                    )
                    op.index = index
                    op.panel = panel
                    op.category = "Workspace"
    row.separator(factor=1)
    button_row = row.row(align=True)
    # button_row.scale_y=2
    button_row.alignment = "CENTER"
    button_row.operator("cp.add_category", icon="ADD").to = "Workspace"
    # if is_preferences:
    #     row.separator(factor=1)
    #     row.operator("cp.autocreatecategories")
    row.separator(factor=1)
    row1 = row.row()
    row1 = row1.split(factor=0.9)
    row2 = row1.row()
    row2.prop(self, f"addons_to_exclude{get_active_space()}")

    if not self.addons_to_exclude:
        row2.enabled = False
    row1.operator("cp.search_popup_for_exclude_list", text="", icon="ADD", depress=True)
    op = row1.operator(
        "cp.reordercategory",
        text="",
        icon_value=icon_collection["icons"]["reorder"].icon_id,
    )
    op.exclusion_list = True
    row.separator(factor=1)
    if is_preferences or self.show_delete_buttons_in_quick_settings:
        grid = row.grid_flow(columns=4, row_major=True)
        # exclude_count=len(split_keep_substring(getattr(self,f"addons_to_exclude{get_active_space()}")))
        # if exclude_count>3:
        #     grid=row.grid_flow(columns=4,row_major=True)
        # else:
        #     grid=row.row()
        #     grid=grid.split(factor=1/(exclude_count+1))
        for panel in split_keep_substring(
            getattr(self, f"addons_to_exclude{get_active_space()}")
        ):
            if panel:
                op = grid.operator("cp.remove_panel", text=panel, icon="PANEL_CLOSE")
                op.panel = panel
                op.category = "ExclusionList"

    if is_preferences and not self.remove_holder_tab:
        row.separator(factor=1)

        row.label(text="Tab name for filtered out panels")
        row.prop(self, "holder_tab_name", text="")


def draw_dropdowns_section(self, is_preferences, layout3):
    row = layout3.column()
    if is_preferences:
        row.prop(self, "use_dropdowns", toggle=True)
    if not self.dropdown_categories:
        text_row = row.row(align=True)
        text_row.alignment = "CENTER"
        text_row.label(
            text="Let’s begin with your first category! Click the button below to get started."
        )
    for index, a in enumerate(self.dropdown_categories):
        row.separator(factor=0.2)
        box = row.box()
        if draw_category(
            box, a, "show", a.name, index, icon_collection["icons"], False, "DropDown"
        ):
            # box=row.box()
            row1 = box.row()
            # row1=row1.split(factor=0.7)

            row1.prop(a, "name", text="")
            # row2=row1.split(factor=0.75)
            # op = row2.operator('cp.remove_category_from_dropdown', text='',
            #                                 icon='PANEL_CLOSE')
            # op.index = index

            # op = row2.operator('cp.movecategory', text='',
            #                                 icon='TRIA_UP')
            # op.index = index
            # op.category = 'DropDown'
            # op.direction='UP'

            row1 = box.row()
            row1 = row1.split(factor=0.75)
            row2 = row1.row()
            # row1=row1.split(factor=0.75)
            row2.prop(a, "panels")
            if not a.panels:
                row2.enabled = False
            row1.operator(
                "cp.search_popup_for_dropdown", text="", icon="ADD", depress=True
            ).index = index
            # op = row1.operator('cp.movecategory', text='',
            #                                 icon='TRIA_DOWN')
            # op.index = index
            # op.category = 'DropDown'
            # op.direction='DOWN'
            if is_preferences or self.show_delete_buttons_in_quick_settings:
                grid = box.grid_flow(columns=4, row_major=True)
                for panel in split_keep_substring(a.panels):
                    if panel:
                        op = grid.operator(
                            "cp.remove_panel", text=panel, icon="PANEL_CLOSE"
                        )
                        op.index = index
                        op.panel = panel
                        op.category = "DropDown"
    row.separator(factor=1)
    button_row = row.row(align=True)
    # button_row.scale_y=2
    button_row.alignment = "CENTER"
    button_row.operator("cp.add_category", icon="ADD").to = "DropDown"
    row.separator(factor=1)
    row.prop(self, "move_dropdowns_to_toolbar")
    row.prop(self, "dropdown_width")
    row.prop(self, "show_dropdown_search")


def draw_pie_panels_section(self, is_preferences, layout3):
    row = layout3.column()
    if not self.panel_categories:
        text_row = row.row(align=True)
        text_row.alignment = "CENTER"
        text_row.label(
            text="Let’s begin with your first category! Click the button below to get started."
        )
    for index, a in enumerate(self.panel_categories):
        row.separator(factor=0.2)
        box = row.box()
        if draw_category(
            box, a, "show", a.name, index, icon_collection["icons"], False, "Pie"
        ):
            # row.separator(factor=1)
            # row.separator(factor=1)
            row1 = box.row()

            row1.prop(a, "name", text="")
            # row2=row1.split(factor=0.75)
            # op = row2.operator('cp.remove_category_from_pie', text='',
            #                                 icon='PANEL_CLOSE')
            # op.index = index

            # op = row2.operator('cp.movecategory', text='',
            #                                 icon='TRIA_UP')
            # op.index = index
            # op.category = 'Pie'
            # op.direction='UP'
            row1 = box.row()
            row1 = row1.split(factor=0.75)
            row2 = row1.row()
            # row1=row1.split(factor=0.75)
            row2.prop(a, "panels")
            if not a.panels:
                row2.enabled = False
            row1.operator(
                "cp.search_popup", text="", icon="ADD", depress=True
            ).index = index
            # op = row1.operator('cp.movecategory', text='',
            #                                 icon='TRIA_DOWN')
            # op.index = index
            # op.category = 'Pie'
            # op.direction='DOWN'
            if is_preferences or self.show_delete_buttons_in_quick_settings:
                grid = box.grid_flow(columns=4, row_major=True)
                for panel in split_keep_substring(a.panels):
                    if panel:
                        op = grid.operator(
                            "cp.remove_panel", text=panel, icon="PANEL_CLOSE"
                        )
                        op.index = index
                        op.panel = panel
                        op.category = "Pie"

    row.separator(factor=1)
    button_row = row.row(align=True)
    # button_row.scale_y=2
    button_row.alignment = "CENTER"
    button_row.operator("cp.add_category", icon="ADD").to = "Pie"

    row.prop(self, "pop_out_style")
    if self.pop_out_style == "DropDown":
        row.prop(self, "columm_layout_for_popup")
    row.prop(self, "use_verticle_menu")


def draw_renaming_section(self, context, layout3):
    row = layout3.column()
    # if addons_with_multiple_tabs:
    row.label(
        text="Add-ons with multiple tabs display their individual tab names in brackets, allowing you to rename each tab separately.",
        icon="INFO",
    )
    draw_addons_list_for_renaming(row, context, self.space_type)
    row.operator(
        "cp.changecategory",
        text="Confirm"
        if preferences().filtering_method == "Use N-Panel Filtering"
        else "Confirm (This will change category in the source file)",
    )


def draw_reordering_section(self, context, layout3, is_preferences=True):
    row = layout3.column()
    if is_preferences:
        if (
            not self.injected_code
            and not self.filtering_method == "Use N-Panel Filtering"
        ):
            row.label(
                text="Click this button before reordering the tabs!"
                if not self.filtering_method == "Use N-Panel Filtering"
                else "Click this button for proper ordering of sub-panels in a Tab!",
                icon="ERROR",
            )
            row.operator("cp.injectcode")
        if (
            not self.injected_code_tracking
            and self.filtering_method == "Use N-Panel Filtering"
        ):
            row.label(
                text="Click this button before reordering the tabs!"
                if not self.filtering_method == "Use N-Panel Filtering"
                else "Click this button to properly organize sub-panels (admin rights may be required).",
                icon="ERROR",
            )
            row.operator("cp.injecttrackingcode")
            context.scene.cp_warning.draw(row, context)
        row.label(
            text="All tabs for a Multi-Tab add-on will be ordered based on the position of the first tab.",
            icon="INFO",
        )
        if preferences().sort_per_category and not preferences().easy_mode:
            row.label(
                text="'Sort Tabs Per Category' is enabled. Tabs will be ordered based on their sequence in your category list, overriding the order defined in this table.",
                icon="INFO",
            )
    draw_addons_list(row, context, self.space_type)
    if not self.filtering_method == "Use N-Panel Filtering":
        row.operator("cp.clearforcedorders")
    else:
        row.operator(
            "cp.changecategory",
            text="Confirm"
            if preferences().filtering_method == "Use N-Panel Filtering"
            else "Confirm (This will change category in the source file)",
        )


class CP_UL_Addons_Order_List(bpy.types.UIList):
    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname
    ):
        ob = data

        obj = item
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            if obj:
                row = layout.row()
                row.label(text=obj.name)
                # row.label(text="Forced Order Found" if obj.ordered else '',icon='ERROR' if obj.ordered else 'NONE')

        elif self.layout_type in {"GRID"}:
            row = layout.row()
            row.label(text=obj.name)
            # row.label(text="Forced Order Found" if obj.ordered else '',icon='ERROR' if obj.ordered else 'NONE')


class CP_UL_Category_Order_List(bpy.types.UIList):
    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname
    ):
        ob = data

        obj = item
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            if obj:
                row = layout.row()
                row.label(text=obj.name)

        elif self.layout_type in {"GRID"}:
            row = layout.row()
            row.label(text=obj.name)


class CP_UL_Addons_Order_List_For_Renaming(bpy.types.UIList):
    def __init__(self, *args, **kwargs):
        self.use_filter_sort_alpha = True

    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname
    ):
        ob = data

        obj = item
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            if obj:
                row = layout.row()
                row.label(text=obj.display_name)
                row.prop(obj, "tab_name", text="", emboss=False)

        elif self.layout_type in {"GRID"}:
            row = layout.row()
            row.label(text=obj.display_name)
            # row.label(text="Forced Order Found" if obj.ordered else '',icon='ERROR' if obj.ordered else 'NONE')


class PAP_OT_Add_Category(bpy.types.Operator):
    bl_idname = "cp.add_category"
    bl_label = "Add New Category"
    bl_description = "Create a new Category for this section"
    bl_property = "name"
    name: bpy.props.StringProperty(default="Category", name="Name")
    to: bpy.props.StringProperty(default="Pie")
    is_guide: bpy.props.BoolProperty(default=False, options={"SKIP_SAVE"})

    def draw(self, context):
        self.layout.prop(self, "name")

    def execute(self, context):
        space = get_active_space()
        if self.to == "Pie":
            t = preferences().panel_categories.add()
            t.name = self.name
        elif self.to == "Workspace":
            if len(getattr(preferences(), f"workspace_categories{space}")) < 50:
                t = getattr(preferences(), f"workspace_categories{space}").add()
                t.name = self.name
                t.show = True
            else:
                self.report({"WARNING"}, "Workspace are limited to 50!")
            if self.is_guide:
                from .guide_ops import cp_guides

                cp_guides.preferences.set_page(2)
        elif self.to == "FP":
            if len(getattr(preferences(), f"focus_panel_categories{space}")) < 10:
                t = getattr(preferences(), f"focus_panel_categories{space}").add()
                t.name = self.name
            else:
                self.report({"WARNING"}, "Focus Panel Categories are limited to 10!")
        elif self.to == "Addon Loading":
            t = preferences().addon_loading_categories.add()
            t.name = self.name
        else:
            t = preferences().dropdown_categories.add()
            t.name = self.name
        savePreferences()
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class PAP_OT_Remove_Panel(bpy.types.Operator):
    bl_idname = "cp.remove_panel"
    bl_label = "Remove this addon/panel"
    bl_description = "Remove this Addon/Panel from this category"
    index: bpy.props.IntProperty()
    panel: bpy.props.StringProperty()
    category: bpy.props.StringProperty(default="Pie")

    def execute(self, context):
        space = get_active_space()
        if self.category == "Pie":
            preferences().panel_categories[self.index].panels = ",".join(
                [
                    a
                    for a in split_keep_substring(
                        preferences().panel_categories[self.index].panels
                    )
                    if a and a != self.panel
                ]
            )
        elif self.category == "DropDown":
            preferences().dropdown_categories[self.index].panels = ",".join(
                [
                    a
                    for a in split_keep_substring(
                        preferences().dropdown_categories[self.index].panels
                    )
                    if a and a != self.panel
                ]
            )
        elif self.category == "FP":
            getattr(preferences(), f"focus_panel_categories{space}")[
                self.index
            ].panels = ",".join(
                [
                    a
                    for a in split_keep_substring(
                        getattr(preferences(), f"focus_panel_categories{space}")[
                            self.index
                        ].panels
                    )
                    if a and a != self.panel
                ]
            )

        elif self.category == "Workspace":
            getattr(preferences(), f"workspace_categories{space}")[
                self.index
            ].panels = ",".join(
                [
                    a
                    for a in split_keep_substring(
                        getattr(preferences(), f"workspace_categories{space}")[
                            self.index
                        ].panels
                    )
                    if a and a != self.panel
                ]
            )
        elif self.category == "Addon Loading":
            preferences().addon_loading_categories[self.index].panels = ",".join(
                [
                    a
                    for a in split_keep_substring(
                        preferences().addon_loading_categories[self.index].panels
                    )
                    if a and a != self.panel
                ]
            )
        elif self.category == "ATL":
            preferences().atl_list = ",".join(
                [
                    a
                    for a in split_keep_substring(preferences().atl_list)
                    if a and a != self.panel
                ]
            )
        else:
            setattr(
                preferences(),
                f"addons_to_exclude{space}",
                ",".join(
                    [
                        a
                        for a in split_keep_substring(
                            getattr(preferences(), f"addons_to_exclude{space}")
                        )
                        if a and a != self.panel
                    ]
                ),
            )
        savePreferences()
        return {"FINISHED"}


class PAP_OT_Remove_Category(bpy.types.Operator):
    bl_idname = "cp.remove_category_from_pie"
    bl_label = "Remove this Category"
    bl_description = "Remove this Category"
    index: bpy.props.IntProperty()

    def execute(self, context):
        preferences().panel_categories.remove(self.index)
        savePreferences()
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)


class PAP_OT_CP(bpy.types.Operator):
    bl_idname = "cp.settings"
    bl_label = "Clean Panels"
    bl_description = "Open Clean Panels quick settings"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Clean Panels"
    space: bpy.props.StringProperty(default="VIEW_3D")

    def draw(self, context):
        layout = self.layout
        layout.label(text="Quick Settings", icon="PREFERENCES")
        layout.ui_units_x = 25
        preferences().space_type = self.space
        layout.operator("cp.openpreferences", icon="TOOL_SETTINGS")
        # if context.area.type=='VIEW_3D':
        #     layout.prop(preferences(),'draw_side')
        draw_quick_settings(self, preferences(), context)
        # draw_settings(self,preferences(), context,False)

    def execute(self, context):
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self)


class PAP_OT_CP_Reorder(bpy.types.Operator):
    bl_idname = "cp.quickreorder"
    bl_label = "Re-Order Tabs"
    bl_description = "Reorder Tabs"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Clean Panels"
    space: bpy.props.StringProperty(default="VIEW_3D")

    def draw(self, context):
        layout = self.layout
        layout.label(text="Re-Order Tabs", icon="PREFERENCES")
        layout.ui_units_x = 10
        preferences().space_type = self.space
        layout.operator("cp.openpreferences", icon="TOOL_SETTINGS")
        # if context.area.type=='VIEW_3D':
        #     layout.prop(preferences(),'draw_side')
        # draw_quick_settings(self,preferences(), context)
        draw_reordering_section(preferences(), context, layout, False)
        # draw_settings(self,preferences(), context,False)

    def execute(self, context):
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self)


class PAP_OT_Remove_Category_Dropdown(bpy.types.Operator):
    bl_idname = "cp.remove_category_from_dropdown"
    bl_label = "Remove this Category"
    index: bpy.props.IntProperty()
    bl_description = "Remove this Category from Dropdowns section"

    def execute(self, context):
        preferences().dropdown_categories.remove(self.index)
        savePreferences()
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)


class PAP_OT_Remove_Category_FP(bpy.types.Operator):
    bl_idname = "cp.remove_category_from_fp"
    bl_label = "Remove this Category"
    index: bpy.props.IntProperty()
    bl_description = "Remove this Category from Focus Panel section"

    def execute(self, context):
        getattr(preferences(), f"focus_panel_categories{get_active_space()}").remove(
            self.index
        )
        savePreferences()
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)


class PAP_OT_Remove_Category_Workspace(bpy.types.Operator):
    bl_idname = "cp.remove_category_from_workspace"
    bl_label = "Remove this Category"
    bl_description = "Remove this category from workspace filtering"
    index: bpy.props.IntProperty()

    def execute(self, context):
        getattr(preferences(), f"workspace_categories{get_active_space()}").remove(
            self.index
        )
        savePreferences()
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)


class PAP_OT_Remove_Category_Addon_Loading(bpy.types.Operator):
    bl_idname = "cp.remove_category_from_addon_loading"
    bl_label = "Remove this Category"
    bl_description = "Remove this category from Addon Sets"
    index: bpy.props.IntProperty()

    def execute(self, context):
        getattr(preferences(), f"addon_loading_categories").remove(self.index)
        savePreferences()
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)


class PAP_OT_Reorder_Category(bpy.types.Operator):
    bl_idname = "cp.reordercategory"
    bl_label = "Reorder"
    bl_description = "Change the order of Panels.\nUseful when using per category sorting(with N-Panel Filtering method)"
    index: bpy.props.IntProperty()
    exclusion_list: bpy.props.BoolProperty(
        default=False, options={"SKIP_SAVE", "HIDDEN"}
    )
    category: bpy.props.StringProperty()

    def draw(self, context):
        layout = self.layout
        column = layout.column()
        column = column.split(factor=0.9)
        column.template_list(
            "CP_UL_Category_Order_List",
            "",
            context.scene,
            "addon_info",
            context.scene,
            "addon_info_index",
            item_dyntip_propname="name",
        )
        column = column.column(align=True)
        column.operator(
            "cp.moveaddonincategory", text="", icon="SORT_DESC"
        ).direction = "UP"
        column.operator(
            "cp.moveaddonincategory", text="", icon="SORT_ASC"
        ).direction = "DOWN"

    def execute(self, context):
        space = get_active_space()
        if self.exclusion_list:
            setattr(
                preferences(),
                f"addons_to_exclude{space}",
                ",".join([a.name for a in context.scene.addon_info]),
            )
        else:
            if self.category == "FP":
                getattr(preferences(), f"focus_panel_categories{space}")[
                    self.index
                ].panels = ",".join([a.name for a in context.scene.addon_info])
            else:
                getattr(preferences(), f"workspace_categories{space}")[
                    self.index
                ].panels = ",".join([a.name for a in context.scene.addon_info])
        bpy.ops.cp.togglefiltering("INVOKE_DEFAULT")
        bpy.ops.cp.togglefiltering("INVOKE_DEFAULT")
        savePreferences()
        return {"FINISHED"}

    def invoke(self, context, event):
        context.scene.addon_info.clear()
        space = get_active_space()
        if self.exclusion_list:
            for a in split_keep_substring(
                getattr(preferences(), f"addons_to_exclude{space}")
            ):
                t = context.scene.addon_info.add()
                t.name = a
        else:
            if self.category == "FP":
                for a in split_keep_substring(
                    getattr(preferences(), f"focus_panel_categories{space}")[
                        self.index
                    ].panels
                ):
                    t = context.scene.addon_info.add()
                    t.name = a
            else:
                for a in split_keep_substring(
                    getattr(preferences(), f"workspace_categories{space}")[
                        self.index
                    ].panels
                ):
                    t = context.scene.addon_info.add()
                    t.name = a

        return context.window_manager.invoke_props_dialog(self)


class CP_OT_Remove_Panel(bpy.types.Operator):
    bl_idname = "cp.removedropdownpanel"
    bl_label = "Remove this Dropdown"
    bl_options = {"REGISTER", "UNDO"}
    name: bpy.props.StringProperty()

    def execute(self, context):
        for a in preferences().dropdown_categories:
            a.panels = ",".join(
                [b for b in split_keep_substring(a.panels) if b != self.name and b]
            )
        savePreferences()
        return {"FINISHED"}


class PAP_OT_searchPopup(bpy.types.Operator):
    bl_idname = "cp.search_popup"
    bl_label = "Add Panel"
    bl_property = "my_enum"

    my_enum: bpy.props.EnumProperty(
        name="Panel", description="", items=get_panel_categories
    )
    category: bpy.props.StringProperty(default="Pie")
    index: bpy.props.IntProperty(default=0)

    def draw(self, context):
        layout = self.layout
        grid = layout.grid_flow(
            columns=math.ceil(len(context.scene.temp_collection) / 30)
        )
        for t in context.scene.temp_collection:
            row = grid.row()
            row = row.split(factor=0.9)
            row.prop(t, "enabled", text=t.name)
            row.label(text="", icon=t.icon)

    def execute(self, context):
        index = self.index
        if not preferences().use_enum_search_for_popups:
            for a in context.scene.temp_collection:
                if not a.enabled:
                    preferences().panel_categories[index].panels = ",".join(
                        [
                            t
                            for t in split_keep_substring(
                                preferences().panel_categories[index].panels
                            )
                            if t != a.name
                        ]
                    )
                    preferences().panel_categories[index].panels = ",".join(
                        split_keep_substring(
                            preferences().panel_categories[index].panels
                        )
                    )
            to_add = []
            for a in context.scene.temp_collection:
                if a.enabled and a.name not in split_keep_substring(
                    preferences().panel_categories[index].panels
                ):
                    to_add.append(a.name)
            preferences().panel_categories[index].panels = ",".join(
                split_keep_substring(preferences().panel_categories[index].panels)
                + to_add
            )
        else:
            # index=preferences().panel_categories.find(self.category)
            if index >= 0:
                preferences().panel_categories[index].panels = (
                    (preferences().panel_categories[index].panels + "," + self.my_enum)
                    if preferences().panel_categories[index].panels
                    else self.my_enum
                )
        savePreferences()
        return {"FINISHED"}

    def invoke(self, context, event):
        wm = context.window_manager
        context.scene.temp_collection.clear()
        addons = get_panel_categories(self, context)
        self.addons = addons
        for a in addons:
            t = context.scene.temp_collection.add()
            t.name = a[0]
            t.icon = a[3]
            t.enabled = a[0] in split_keep_substring(
                preferences().panel_categories[self.index].panels
            )
        if not preferences().use_enum_search_for_popups:
            return wm.invoke_props_dialog(self, width=200 * math.ceil(len(addons) / 30))
        wm.invoke_search_popup(self)
        return {"FINISHED"}


class PAP_OT_Set_ATL(bpy.types.Operator):
    bl_idname = "cp.setatl"
    bl_label = "Add Addon"
    bl_description = "Add Addons to load on boot"
    bl_property = "my_enum"

    my_enum: bpy.props.EnumProperty(
        name="Panel", description="", items=get_addons_for_atl
    )

    def draw(self, context):
        layout = self.layout
        # if not preferences().delayed_addons_loaded:
        #     row=layout.row()
        #     row.label(text="Click Load Addons to see all your addons!")
        #     row.alert=True
        grid = layout.grid_flow(
            columns=math.ceil(len(context.scene.temp_collection) / 30)
        )
        for t in context.scene.temp_collection:
            row = grid.row()
            row = row.split(factor=0.9)
            row.prop(t, "enabled", text=t.name)
            # row.label(text='',icon='')

    def execute(self, context):
        if not preferences().use_enum_search_for_popups:
            for a in context.scene.temp_collection:
                if not a.enabled:
                    preferences().atl_list = ",".join(
                        [
                            t
                            for t in split_keep_substring(preferences().atl_list)
                            if t != a.name
                        ]
                    )
                    preferences().atl_list = ",".join(
                        split_keep_substring(preferences().atl_list)
                    )
            to_add = []
            for a in context.scene.temp_collection:
                if a.enabled and a.name not in split_keep_substring(
                    preferences().atl_list
                ):
                    to_add.append(a.name)
            preferences().atl_list = ",".join(
                split_keep_substring(preferences().atl_list) + to_add
            )
        else:
            preferences().atl_list = (
                (preferences().atl_list + "," + self.my_enum)
                if preferences().atl_list
                else self.my_enum
            )
        savePreferences()
        return {"FINISHED"}

    def invoke(self, context, event):
        wm = context.window_manager
        context.scene.temp_collection.clear()

        self.addons = get_addons_for_atl(self, context)
        for a in self.addons:
            t = context.scene.temp_collection.add()
            t.name = a[1]
            t.icon = a[2]
            t.enabled = a[1] in split_keep_substring(preferences().atl_list)
        if not preferences().use_enum_search_for_popups:
            return wm.invoke_props_dialog(
                self, width=200 * math.ceil(len(self.addons) / 30)
            )
        wm.invoke_search_popup(self)
        return {"FINISHED"}


class PAP_OT_searchPopupForExclusion(bpy.types.Operator):
    bl_idname = "cp.search_popup_for_exclude_list"
    bl_label = "Add Addon"
    bl_property = "my_enum"
    my_enum: bpy.props.EnumProperty(name="Panel", description="", items=get_all_addons)
    is_guide: bpy.props.BoolProperty(default=False, options={"SKIP_SAVE"})
    space: bpy.props.StringProperty(default="", options={"SKIP_SAVE"})

    def draw(self, context):
        layout = self.layout
        grid = layout.grid_flow(
            columns=math.ceil(len(context.scene.temp_collection) / 30)
        )
        for t in context.scene.temp_collection:
            row = grid.row()
            row.prop(t, "enabled", text=t.name, icon=t.icon)

    def execute(self, context):
        if not preferences().use_enum_search_for_popups:
            for a in context.scene.temp_collection:
                name = a.name
                if a.name in ["Tool(Tab)", "View(Tab)", "Node(Tab)", "Options(Tab)"]:
                    name = name.replace("(Tab)", "")
                if not a.enabled:
                    setattr(
                        preferences(),
                        f"addons_to_exclude{get_active_space()}",
                        ",".join(
                            [
                                t
                                for t in split_keep_substring(
                                    getattr(
                                        preferences(),
                                        f"addons_to_exclude{get_active_space()}",
                                    )
                                )
                                if t != name
                            ]
                        ),
                    )
                    setattr(
                        preferences(),
                        f"addons_to_exclude{get_active_space()}",
                        ",".join(
                            split_keep_substring(
                                getattr(
                                    preferences(),
                                    f"addons_to_exclude{get_active_space()}",
                                )
                            )
                        ),
                    )
                    # preferences().addons_to_exclude=",".join([t for t in split_keep_substring(preferences().addons_to_exclude) if t!=a.name])
                    # preferences().addons_to_exclude=",".join(split_keep_substring(preferences().addons_to_exclude))
            to_add = []
            for a in context.scene.temp_collection:
                if a.enabled and a.name not in split_keep_substring(
                    getattr(preferences(), f"addons_to_exclude{get_active_space()}")
                ):
                    name = a.name
                    if a.name in [
                        "Tool(Tab)",
                        "View(Tab)",
                        "Node(Tab)",
                        "Options(Tab)",
                    ]:
                        name = name.replace("(Tab)", "")
                    to_add.append(name)
            setattr(
                preferences(),
                f"addons_to_exclude{get_active_space()}",
                ",".join(
                    split_keep_substring(
                        getattr(preferences(), f"addons_to_exclude{get_active_space()}")
                    )
                    + to_add
                ),
            )
        else:
            if self.my_enum == "All":
                all_addons = ",".join(get_all_addon_names(self, context))
                setattr(
                    preferences(), f"addons_to_exclude{get_active_space()}", all_addons
                )
            elif self.my_enum == "Unfiltered":
                used_addons = []
                for a in getattr(
                    preferences(), f"workspace_categories{get_active_space()}"
                ):
                    used_addons.extend(split_keep_substring(a.panels))
                all_addons = get_all_addon_names(self, context)
                addons_to_add = [b for b in all_addons if b not in used_addons]
                current_addons = split_keep_substring(
                    getattr(preferences(), f"addons_to_exclude{get_active_space()}")
                )
                final_list = ",".join(list(set(current_addons + addons_to_add)))
                setattr(
                    preferences(), f"addons_to_exclude{get_active_space()}", final_list
                )
            else:
                setattr(
                    preferences(),
                    f"addons_to_exclude{get_active_space()}",
                    (
                        getattr(preferences(), f"addons_to_exclude{get_active_space()}")
                        + ","
                        + self.my_enum
                    )
                    if getattr(preferences(), f"addons_to_exclude{get_active_space()}")
                    else self.my_enum,
                )
        if self.is_guide:
            from .guide_ops import cp_guides

            cp_guides.preferences.set_page(7)
        savePreferences()
        return {"FINISHED"}

    def invoke(self, context, event):
        self.space = get_active_space()
        wm = context.window_manager
        context.scene.temp_collection.clear()
        addons = get_all_addons(self, context)
        self.addons = addons
        for a in addons:
            t = context.scene.temp_collection.add()
            t.name = a[1]
            t.icon = "NONE"
            t.enabled = a[0] in split_keep_substring(
                getattr(preferences(), f"addons_to_exclude{get_active_space()}")
            )
        if not preferences().use_enum_search_for_popups:
            return wm.invoke_props_dialog(self, width=200 * math.ceil(len(addons) / 30))
        wm.invoke_search_popup(self)
        return {"FINISHED"}


class PAP_OT_searchPopupForDropDown(bpy.types.Operator):
    bl_idname = "cp.search_popup_for_dropdown"
    bl_label = "Add Panel"
    bl_property = "my_enum"
    category: bpy.props.StringProperty(default="Dropdown")
    my_enum: bpy.props.EnumProperty(
        name="Panel", description="", items=get_panel_categories
    )
    index: bpy.props.IntProperty(default=0)

    def draw(self, context):
        layout = self.layout
        grid = layout.grid_flow(
            columns=math.ceil(len(context.scene.temp_collection) / 30)
        )
        for t in context.scene.temp_collection:
            row = grid.row()
            row = row.split(factor=0.9)
            row.prop(t, "enabled", text=t.name)
            row.label(text="", icon=t.icon)

    def execute(self, context):
        index = self.index
        if not preferences().use_enum_search_for_popups:
            for a in context.scene.temp_collection:
                if not a.enabled:
                    preferences().dropdown_categories[index].panels = ",".join(
                        [
                            t
                            for t in split_keep_substring(
                                preferences().dropdown_categories[index].panels
                            )
                            if t != a.name
                        ]
                    )
                    preferences().dropdown_categories[index].panels = ",".join(
                        split_keep_substring(
                            preferences().dropdown_categories[index].panels
                        )
                    )
            to_add = []
            for a in context.scene.temp_collection:
                if a.enabled and a.name not in split_keep_substring(
                    preferences().dropdown_categories[index].panels
                ):
                    to_add.append(a.name)
            preferences().dropdown_categories[index].panels = ",".join(
                split_keep_substring(preferences().dropdown_categories[index].panels)
                + to_add
            )
        else:
            # index=preferences().dropdown_categories.find(self.category)
            if index >= 0:
                preferences().dropdown_categories[index].panels = (
                    (
                        preferences().dropdown_categories[index].panels
                        + ","
                        + self.my_enum
                    )
                    if preferences().dropdown_categories[index].panels
                    else self.my_enum
                )
        savePreferences()
        return {"FINISHED"}

    def invoke(self, context, event):
        wm = context.window_manager
        context.scene.temp_collection.clear()
        addons = get_panel_categories(self, context)
        self.addons = addons
        for a in addons:
            t = context.scene.temp_collection.add()
            t.name = a[0]
            t.icon = a[3]
            t.enabled = a[0] in split_keep_substring(
                preferences().dropdown_categories[self.index].panels
            )
        if not preferences().use_enum_search_for_popups:
            return wm.invoke_props_dialog(self, width=200 * math.ceil(len(addons) / 30))
        wm.invoke_search_popup(self)
        return {"FINISHED"}


class PAP_OT_Make_FP_Categories_from_Filtering(bpy.types.Operator):
    bl_idname = "cp.fpcategoriesfromfiltering"
    bl_label = "Create/Update from Filtering Categories"
    bl_description = "Create Focus Panel categories from filtering categories"

    def execute(self, context):
        for cat in getattr(preferences(), f"workspace_categories{get_active_space()}"):
            if (
                getattr(
                    preferences(), f"focus_panel_categories{get_active_space()}"
                ).find(cat.name)
                > -1
            ):
                fp_cat = getattr(
                    preferences(), f"focus_panel_categories{get_active_space()}"
                )[
                    getattr(
                        preferences(), f"focus_panel_categories{get_active_space()}"
                    ).find(cat.name)
                ]
                fp_cat.panels = ""
            else:
                fp_cat = getattr(
                    preferences(), f"focus_panel_categories{get_active_space()}"
                ).add()
                fp_cat.name = cat.name
            for panel in split_keep_substring(cat.panels):
                renamed_tab = ""
                for a in getattr(
                    preferences(), f"addon_info_for_renaming{get_active_space()}"
                ):
                    if panel in a.display_name:
                        renamed_tab = a.tab_name
                        break
                if renamed_tab and renamed_tab not in split_keep_substring(
                    fp_cat.panels
                ):
                    fp_cat.panels = (
                        ",".join(split_keep_substring(fp_cat.panels))
                        + ","
                        + renamed_tab
                    )
        return {"FINISHED"}


class PAP_OT_Make_Delayed_Categories_from_Filtering(bpy.types.Operator):
    bl_idname = "cp.delayedcategoriesfromfiltering"
    bl_label = "Create/Update from Filtering Categories"
    bl_description = "Create Delayed Loading categories from filtering categories"

    def execute(self, context):
        for cat in getattr(preferences(), f"workspace_categories"):
            if getattr(preferences(), f"addon_loading_categories").find(cat.name) > -1:
                fp_cat = getattr(preferences(), f"addon_loading_categories")[
                    getattr(preferences(), f"addon_loading_categories").find(cat.name)
                ]
            else:
                fp_cat = getattr(preferences(), f"addon_loading_categories").add()
                fp_cat.name = cat.name
            fp_cat.panels = cat.panels
        atl_list = split_keep_substring(preferences().atl_list)
        for addon in split_keep_substring(preferences().addons_to_exclude):
            if addon not in atl_list:
                atl_list.append(addon)
        preferences().atl_list = ",".join(atl_list)
        return {"FINISHED"}


class PAP_OT_searchPopupForFP(bpy.types.Operator):
    bl_idname = "cp.search_popup_for_fp"
    bl_label = "Add Panel"
    bl_property = "my_enum"
    category: bpy.props.StringProperty(default="FP")
    my_enum: bpy.props.EnumProperty(
        name="Panel", description="", items=get_panel_categories
    )
    index: bpy.props.IntProperty(default=0)

    def draw(self, context):
        layout = self.layout
        grid = layout.grid_flow(
            columns=math.ceil(len(context.scene.temp_collection) / 30)
        )
        for t in context.scene.temp_collection:
            row = grid.row()
            row = row.split(factor=0.9)
            row.prop(t, "enabled", text=t.name)
            row.label(text="", icon=t.icon)

    def execute(self, context):
        index = self.index
        if not preferences().use_enum_search_for_popups:
            for a in context.scene.temp_collection:
                if not a.enabled:
                    getattr(
                        preferences(), f"focus_panel_categories{get_active_space()}"
                    )[index].panels = ",".join(
                        [
                            t
                            for t in split_keep_substring(
                                getattr(
                                    preferences(),
                                    f"focus_panel_categories{get_active_space()}",
                                )[index].panels
                            )
                            if t != a.name
                        ]
                    )
                    getattr(
                        preferences(), f"focus_panel_categories{get_active_space()}"
                    )[index].panels = ",".join(
                        split_keep_substring(
                            getattr(
                                preferences(),
                                f"focus_panel_categories{get_active_space()}",
                            )[index].panels
                        )
                    )
            to_add = []
            for a in context.scene.temp_collection:
                if a.enabled and a.name not in split_keep_substring(
                    getattr(
                        preferences(), f"focus_panel_categories{get_active_space()}"
                    )[index].panels
                ):
                    to_add.append(a.name)
            getattr(preferences(), f"focus_panel_categories{get_active_space()}")[
                index
            ].panels = ",".join(
                split_keep_substring(
                    getattr(
                        preferences(), f"focus_panel_categories{get_active_space()}"
                    )[index].panels
                )
                + to_add
            )
        else:
            # index=preferences().dropdown_categories.find(self.category)
            if index >= 0:
                getattr(preferences(), f"focus_panel_categories{get_active_space()}")[
                    index
                ].panels = (
                    (
                        getattr(
                            preferences(), f"focus_panel_categories{get_active_space()}"
                        )[index].panels
                        + ","
                        + self.my_enum
                    )
                    if getattr(
                        preferences(), f"focus_panel_categories{get_active_space()}"
                    )[index].panels
                    else self.my_enum
                )
        savePreferences()
        return {"FINISHED"}

    def invoke(self, context, event):
        wm = context.window_manager
        context.scene.temp_collection.clear()
        addons = get_panel_categories(self, context)
        self.addons = addons
        for a in addons:
            t = context.scene.temp_collection.add()
            t.name = a[0]
            t.icon = a[3]
            t.enabled = a[0] in split_keep_substring(
                getattr(preferences(), f"focus_panel_categories{get_active_space()}")[
                    self.index
                ].panels
            )
        if not preferences().use_enum_search_for_popups:
            return wm.invoke_props_dialog(self, width=200 * math.ceil(len(addons) / 30))
        wm.invoke_search_popup(self)
        return {"FINISHED"}


class PAP_OT_Icon_Picker(bpy.types.Operator):
    bl_idname = "cp.change_icon"
    bl_label = "Icon"
    bl_description = "Change the icon displayed on the viewport and the pie menu"

    index: bpy.props.IntProperty(default=0)
    category: bpy.props.StringProperty(default="Pie")
    search: bpy.props.StringProperty(default="", options={"SKIP_SAVE"})
    # my_enum: bpy.props.EnumProperty(name="Panel", description="", items=get_icons)
    is_guide: bpy.props.BoolProperty(default=False, options={"SKIP_SAVE"})

    def draw(self, context):
        # self.layout.ui_units_x=
        self.layout.prop(self, "search", icon="VIEWZOOM", text="")
        grid = self.layout.grid_flow(
            columns=12, even_rows=True, even_columns=True, row_major=True
        )
        pcoll = icon_collection["icons"]
        custom_icons = pcoll.keys()
        blender_icons = ALL_ICONS
        for a in custom_icons:
            if self.search.lower() in a.lower():
                op = grid.operator(
                    "cp.set_icon", text="", icon_value=pcoll[a].icon_id, emboss=False
                )
                op.my_enum = a
                op.index = self.index
                op.category = self.category
                op.is_guide = self.is_guide
        for a in blender_icons:
            if self.search.lower() in a.lower():
                op = grid.operator("cp.set_icon", text="", icon=a, emboss=False)
                op.my_enum = a
                op.index = self.index
                op.category = self.category
                op.is_guide = self.is_guide

    def execute(self, context):
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self)


class PAP_OT_Change_Icon(bpy.types.Operator):
    bl_idname = "cp.set_icon"
    bl_label = "Icon"
    bl_description = "Use this icon"
    bl_property = "my_enum"
    category: bpy.props.StringProperty(default="Pie")
    my_enum: bpy.props.StringProperty(default="NONE")
    index: bpy.props.IntProperty(default=0)
    is_guide: bpy.props.BoolProperty(default=False, options={"SKIP_SAVE"})

    def invoke(self, context, event):
        x, y = event.mouse_x, event.mouse_y
        context.window.cursor_warp(-10000, -10000)
        low_left_x = max(0, context.window.x)
        low_left_y = context.window.y
        reset_cursor = lambda: context.window.cursor_warp(
            x + (low_left_x), y + (low_left_y) - 60
        )
        bpy.app.timers.register(reset_cursor, first_interval=0.00000001)
        index = self.index
        if index >= 0:
            getattr(preferences(), f"workspace_categories{get_active_space()}")[
                index
            ].icon = self.my_enum

        context.area.tag_redraw()
        savePreferences()
        if self.is_guide:
            from .guide_ops import cp_guides

            cp_guides.preferences.set_page(5)
        return {"FINISHED"}


class PAP_OT_searchPopupForWorkspace(bpy.types.Operator):
    bl_idname = "cp.search_popup_for_workspace"
    bl_label = "Add Addon"
    bl_property = "my_enum"
    category: bpy.props.StringProperty(default="Workspace")
    my_enum: bpy.props.EnumProperty(
        name="Panel",
        description="",
        items=get_installed_addons_for_filtering_categories,
    )
    index: bpy.props.IntProperty(default=0)
    is_guide: bpy.props.BoolProperty(default=False, options={"SKIP_SAVE"})
    space: bpy.props.StringProperty(default="", options={"SKIP_SAVE"})

    def draw(self, context):
        layout = self.layout
        if (
            preferences().delayed_loading_code_injected
            and not preferences().delayed_addons_loaded
        ):
            row = layout.row()
            row.alert = True
            row.label(text="Click Load Addons to see all your addons!")

        grid = layout.grid_flow(
            columns=math.ceil(len(context.scene.temp_collection) / 30)
        )
        for t in context.scene.temp_collection:
            row = grid.row()
            row = row.split(factor=0.9)
            row.prop(t, "enabled", text=t.name)
            row.label(text="", icon=t.icon)

    def execute(self, context):
        space = get_active_space()
        index = self.index
        if not preferences().use_enum_search_for_popups:
            for a in context.scene.temp_collection:
                name = a.name
                if a.name in ["Tool(Tab)", "View(Tab)", "Node(Tab)", "Options(Tab)"]:
                    name = name.replace("(Tab)", "")

                if not a.enabled:
                    # print(",".join([t for t in split_keep_substring(getattr(preferences(),f'workspace_categories{space}')[index].panels) if t!=name]))
                    getattr(preferences(), f"workspace_categories{space}")[
                        index
                    ].panels = ",".join(
                        [
                            t
                            for t in split_keep_substring(
                                getattr(preferences(), f"workspace_categories{space}")[
                                    index
                                ].panels
                            )
                            if t != name
                        ]
                    )

                    getattr(preferences(), f"workspace_categories{space}")[
                        index
                    ].panels = ",".join(
                        split_keep_substring(
                            getattr(preferences(), f"workspace_categories{space}")[
                                index
                            ].panels
                        )
                    )
            to_add = []
            for a in context.scene.temp_collection:
                if a.enabled and a.name not in split_keep_substring(
                    getattr(preferences(), f"workspace_categories{space}")[index].panels
                ):
                    name = a.name
                    if a.name in [
                        "Tool(Tab)",
                        "View(Tab)",
                        "Node(Tab)",
                        "Options(Tab)",
                    ]:
                        name = name.replace("(Tab)", "")
                    to_add.append(name)

            getattr(preferences(), f"workspace_categories{space}")[
                index
            ].panels = ",".join(
                split_keep_substring(
                    getattr(preferences(), f"workspace_categories{space}")[index].panels
                )
                + to_add
            )
        else:
            if index >= 0:
                if self.my_enum == "All":
                    all_addons = ",".join(
                        get_installed_addon_names(self, context)
                        + split_keep_substring(
                            getattr(preferences(), f"workspace_categories{space}")[
                                index
                            ].panels
                        )
                    )

                    getattr(preferences(), f"workspace_categories{space}")[
                        index
                    ].panels = all_addons
                elif self.my_enum == "Unfiltered":
                    used_addons = []
                    for a in getattr(preferences(), f"workspace_categories{space}"):
                        used_addons.extend(split_keep_substring(a.panels))
                    all_addons = get_installed_addon_names(self, context)
                    addons_to_add = [b for b in all_addons if b not in used_addons]
                    current_addons = split_keep_substring(
                        getattr(preferences(), f"workspace_categories{space}")[
                            index
                        ].panels
                    )
                    final_list = ",".join(list(set(current_addons + addons_to_add)))
                    getattr(preferences(), f"workspace_categories{space}")[
                        index
                    ].panels = final_list
                else:
                    getattr(preferences(), f"workspace_categories{space}")[
                        index
                    ].panels = (
                        (
                            getattr(preferences(), f"workspace_categories{space}")[
                                index
                            ].panels
                            + ","
                            + self.my_enum
                        )
                        if getattr(preferences(), f"workspace_categories{space}")[
                            index
                        ].panels
                        else self.my_enum
                    )
        if self.is_guide:
            from .guide_ops import cp_guides

            cp_guides.preferences.set_page(3)
        savePreferences()
        return {"FINISHED"}

    def invoke(self, context, event):
        wm = context.window_manager
        self.space = get_active_space()
        context.scene.temp_collection.clear()
        addons = get_installed_addons_for_filtering_categories(self, context)
        self.addons = addons
        for a in addons:
            if a[0] not in ("All", "Unfiltered"):
                t = context.scene.temp_collection.add()
                t.name = a[1]
                t.icon = a[3]
                t.enabled = a[0] in split_keep_substring(
                    getattr(preferences(), f"workspace_categories{get_active_space()}")[
                        self.index
                    ].panels
                )
        if not preferences().use_enum_search_for_popups:
            return wm.invoke_props_dialog(self, width=200 * math.ceil(len(addons) / 30))
        wm.invoke_search_popup(self)
        return {"FINISHED"}


class PAP_OT_searchPopupForAddonLoading(bpy.types.Operator):
    bl_idname = "cp.search_popup_for_addon_loading"
    bl_label = "Add Addon"
    bl_property = "my_enum"
    my_enum: bpy.props.EnumProperty(
        name="Panel", description="", items=get_installed_addons
    )
    index: bpy.props.IntProperty(default=0)

    def draw(self, context):
        layout = self.layout
        # if not preferences().delayed_addons_loaded:
        #     row=layout.row()
        #     row.label(text="Click Load Addons to see all your addons!")
        #     row.alert=True
        grid = layout.grid_flow(
            columns=math.ceil(len(context.scene.temp_collection) / 30)
        )
        for t in context.scene.temp_collection:
            row = grid.row()
            row = row.split(factor=0.9)
            row.prop(t, "enabled", text=t.name)
            row.label(text="", icon=t.icon)

    def execute(self, context):
        space = get_active_space()
        index = self.index
        if not preferences().use_enum_search_for_popups:
            for a in context.scene.temp_collection:
                name = a.name
                if not a.enabled:
                    # print(",".join([t for t in split_keep_substring(getattr(preferences(),f'workspace_categories{space}')[index].panels) if t!=name]))
                    getattr(preferences(), f"addon_loading_categories")[
                        index
                    ].panels = ",".join(
                        [
                            t
                            for t in split_keep_substring(
                                getattr(preferences(), f"addon_loading_categories")[
                                    index
                                ].panels
                            )
                            if t != name
                        ]
                    )

                    getattr(preferences(), f"addon_loading_categories")[
                        index
                    ].panels = ",".join(
                        split_keep_substring(
                            getattr(preferences(), f"addon_loading_categories")[
                                index
                            ].panels
                        )
                    )
            to_add = []
            for a in context.scene.temp_collection:
                if a.enabled and a.name not in split_keep_substring(
                    getattr(preferences(), f"addon_loading_categories")[index].panels
                ):
                    name = a.name
                    to_add.append(name)

            getattr(preferences(), f"addon_loading_categories")[
                index
            ].panels = ",".join(
                split_keep_substring(
                    getattr(preferences(), f"addon_loading_categories")[index].panels
                )
                + to_add
            )
        else:
            if index >= 0:
                if self.my_enum == "All":
                    all_addons = ",".join(
                        get_installed_addon_names(self, context)
                        + split_keep_substring(
                            getattr(preferences(), f"addon_loading_categories")[
                                index
                            ].panels
                        )
                    )

                    getattr(preferences(), f"addon_loading_categories")[
                        index
                    ].panels = all_addons
                elif self.my_enum == "Unfiltered":
                    used_addons = []
                    for a in getattr(preferences(), f"addon_loading_categories"):
                        used_addons.extend(split_keep_substring(a.panels))
                    all_addons = get_installed_addon_names(self, context)
                    addons_to_add = [b for b in all_addons if b not in used_addons]
                    current_addons = split_keep_substring(
                        getattr(preferences(), f"addon_loading_categories")[
                            index
                        ].panels
                    )
                    final_list = ",".join(list(set(current_addons + addons_to_add)))
                    getattr(preferences(), f"addon_loading_categories")[
                        index
                    ].panels = final_list
                else:
                    getattr(preferences(), f"addon_loading_categories")[
                        index
                    ].panels = (
                        (
                            getattr(preferences(), f"addon_loading_categories")[
                                index
                            ].panels
                            + ","
                            + self.my_enum
                        )
                        if getattr(preferences(), f"addon_loading_categories")[
                            index
                        ].panels
                        else self.my_enum
                    )
        savePreferences()
        return {"FINISHED"}

    def invoke(self, context, event):
        wm = context.window_manager
        context.scene.temp_collection.clear()
        addons = get_installed_addons(self, context)
        self.addons = addons
        for a in addons:
            t = context.scene.temp_collection.add()
            t.name = a[1]
            t.icon = a[3]
            t.enabled = a[0] in split_keep_substring(
                getattr(preferences(), f"addon_loading_categories")[self.index].panels
            )
        if not preferences().use_enum_search_for_popups:
            return wm.invoke_props_dialog(self, width=200 * math.ceil(len(addons) / 30))
        wm.invoke_search_popup(self)
        return {"FINISHED"}


class PAP_OT_Search_Dropdown(bpy.types.Operator):
    bl_idname = "cp.search_dropdown"
    bl_label = "Search Dropdown"
    bl_description = "Quickly search for any panel to display it as dropdown"
    bl_property = "my_enum"
    category: bpy.props.StringProperty(default="Workspace")
    my_enum: bpy.props.EnumProperty(
        name="Panel", description="", items=get_all_panel_categories
    )

    def execute(self, context):
        bpy.ops.cp.popupcompletepanel("INVOKE_DEFAULT", name=self.my_enum)
        return {"FINISHED"}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.invoke_search_popup(self)
        return {"FINISHED"}


import inspect


class CP_OT_Load_Addons_List_For_Renaming(bpy.types.Operator):
    bl_idname = "cp.loadaddonsforrenaming"
    bl_label = "Load Addons\nCTRL+LMB:Remove uninstalled addons"
    bl_description = "Reload the list"
    bl_options = {"REGISTER", "UNDO"}

    def invoke(self, context, event):
        # preferences().addon_info_for_renaming.clear()
        load_renaming_list(
            context, space=preferences().space_type, force_clear=event.ctrl
        )
        return {"FINISHED"}


class CP_OT_Reset_Tab_Name(bpy.types.Operator):
    bl_idname = "cp.resettabname"
    bl_label = "Reset"
    bl_description = "Reset to original Tab Name\nCTRL+LMB:Reset all"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        space = preferences().space_type
        if self.reset:
            for a in getattr(
                preferences(), f"addon_info_for_renaming{get_active_space(space)}"
            ):
                a.tab_name = a.backup_tab_name if a.backup_tab_name else a.tab_name
        return {"FINISHED"}

    def invoke(self, context, event):
        space = preferences().space_type
        self.reset = False
        if event.ctrl:
            self.reset = True
            return context.window_manager.invoke_confirm(self, event)
            # load_renaming_list(context,reset=True,space=get_active_space())

        else:
            entry = getattr(
                preferences(), f"addon_info_for_renaming{get_active_space(space)}"
            )[
                getattr(
                    preferences(),
                    f"addon_info_for_renaming{get_active_space(space)}_index",
                )
            ]
            entry.tab_name = (
                entry.backup_tab_name if entry.backup_tab_name else entry.tab_name
            )
            # base_type = bpy.types.Panel
            # for typename in dir(bpy.types):

            #     try:
            #         bl_type = getattr(bpy.types, typename,None)
            #         if issubclass(bl_type, base_type):
            #             if getattr(bl_type,'bl_category',None) and (getattr(bl_type,'backup_space','None')==preferences().space_type or getattr(bl_type,'bl_space_type','None')==preferences().space_type) :

            #                 package_name=inspect.getmodule(bl_type).__package__ if inspect.getmodule(bl_type).__package__ else inspect.getmodule(bl_type).__name__

            #                 identifier=get_addon_identifier(package_name)
            #                 if "." in package_name:
            #                     name=get_package_name(package_name)
            #                 else:
            #                     name=package_name
            #                 if name in exceptional_names.keys():
            #                     name=exceptional_names[name]
            #                 name=get_custom_module_name(bl_type,name)
            #                 # print(name)

            #                 if getattr(preferences(),f"addon_info_for_renaming{get_active_space(space)}")[getattr(preferences(),f"addon_info_for_renaming{get_active_space(space)}_index")].name==name:
            #                     print("Back",getattr(preferences(),f"addon_info_for_renaming{get_active_space(space)}")[getattr(preferences(),f"addon_info_for_renaming{get_active_space(space)}_index")].backup_tab_name)
            #                 #     getattr(preferences(),f"addon_info_for_renaming{get_active_space(space)}")[getattr(preferences(),f"addon_info_for_renaming{get_active_space(space)}_index")].tab_name=getattr(bl_type,'backup_category',getattr(preferences(),f"addon_info_for_renaming{get_active_space(space)}")[getattr(preferences(),f"addon_info_for_renaming{get_active_space(space)}_index")].tab_name)
            #                 #     break
            # except:
            #     pass
        return {"FINISHED"}


class CP_OT_Load_Addons_List(bpy.types.Operator):
    bl_idname = "cp.loadaddons"
    bl_label = "Load Addons\nCTRL+LMB:Remove uninstalled addons"
    bl_description = "Reload the list"
    bl_options = {"REGISTER", "UNDO"}

    def invoke(self, context, event):
        load_reordering_list(
            context, space=preferences().space_type, force_clear=event.ctrl
        )
        return {"FINISHED"}


class CP_OT_Open_Preferences(bpy.types.Operator):
    bl_idname = "cp.openpreferences"
    bl_label = "Open Addon Preferences"
    bl_description = "Open Addon Preferences"
    bl_options = {"REGISTER", "UNDO"}

    def invoke(self, context, event):
        render = bpy.context.scene.render
        prefs = bpy.context.preferences
        view = prefs.view
        orgResX = render.resolution_x
        orgResY = render.resolution_y
        w = 3000
        h = 2000
        # render.resolution_x = int(w*2/4)
        # render.resolution_y = int(h*2/4)
        render.resolution_x = int(context.window.width / 1.5)
        render.resolution_y = int(context.window.height / 1.3)
        orgDispMode = view.render_display_type
        view.render_display_type = "WINDOW"
        bpy.ops.render.view_show("INVOKE_DEFAULT")
        area = bpy.context.window_manager.windows[-1].screen.areas[0]
        area.type = "PREFERENCES"
        view.render_display_type = orgDispMode
        render.resolution_x = orgResX
        render.resolution_y = orgResY
        bpy.context.preferences.active_section = "ADDONS"
        bpy.data.window_managers["WinMan"].addon_search = "CleanPanels"
        return {"FINISHED"}


class CP_OT_Inject_Tracking_Code(bpy.types.Operator):
    bl_idname = "cp.injecttrackingcode"
    bl_label = "Click this button to properly order sub-panels"
    bl_description = "Pressing this button will insert a few lines of code in the utils module of blender which will enable Clean Panels to work correctly"
    bl_options = {"REGISTER", "UNDO"}

    def invoke(self, context, event):
        # print("Platform",sys.platform)
        # version=bpy.app.version
        # if sys.platform=='darwin':
        #     util_file_path=os.path.join(os.path.dirname(os.path.dirname(bpy.app.binary_path)),'Resources',f"{version[0]}.{version[1]}","scripts","modules","bpy","utils","__init__.py")
        # elif "linux" in sys.platform:
        #     util_file_path=os.path.join(bpy.app.binary_path,f"{version[0]}.{version[1]}","scripts","modules","bpy","utils","__init__.py")
        # else:
        #     util_file_path=os.path.join(os.path.dirname(bpy.app.binary_path),f"{version[0]}.{version[1]}","scripts","modules","bpy","utils","__init__.py")
        import bpy.utils

        util_file_path = bpy.utils.__file__
        # print(util_file_path)
        try:
            inject_tracking_code(util_file_path)
            savePreferences()
            context.scene.cp_warning.message = (
                "Please restart Blender to apply changes! This button will disappear"
            )
            context.scene.cp_warning.show()
        except Exception as e:
            context.scene.cp_warning.message = (
                "Please start blender as administrator/superuser (Only required Once)"
            )
            context.scene.cp_warning.show()
            self.report(
                {"WARNING"},
                "Please start blender as administrator/superuser (Only required Once)",
            )
            print("Error:", e)
        return {"FINISHED"}


class CP_OT_Inject_Code(bpy.types.Operator):
    bl_idname = "cp.injectcode"
    bl_label = "Enable Ordering"
    bl_description = "Pressing this button will insert a few lines of code in the addon_utils module of blender which will enable Clean Panels to work correctly"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return not preferences().injected_code

    def invoke(self, context, event):
        # version=bpy.app.version
        # if sys.platform=='darwin':
        #     util_file_path=os.path.join(os.path.dirname(os.path.dirname(bpy.app.binary_path)),'Resources',f"{version[0]}.{version[1]}","scripts","modules","addon_utils.py")
        # elif "linux" in sys.platform:
        #     util_file_path=os.path.join(bpy.app.binary_path,f"{version[0]}.{version[1]}","scripts","modules","addon_utils.py")
        # else:
        #     util_file_path=os.path.join(os.path.dirname(bpy.app.binary_path),f"{version[0]}.{version[1]}","scripts","modules","addon_utils.py")

        util_file_path = addon_utils.__file__
        try:
            inject_code(util_file_path)
            preferences().injected_code = True
            savePreferences()
        except Exception as e:
            self.report(
                {"WARNING"},
                "Please start blender as administrator/superuser (Only required Once)",
            )
            print("Error:", e)
        return {"FINISHED"}


class CP_OT_Inject_Delayed_Start_Code(bpy.types.Operator):
    bl_idname = "cp.enabledelayedloading"
    bl_label = "Enable Delayed Addon Loading"
    bl_description = "Pressing this button will insert a few lines of code in the addon_utils file of blender which will enable Clean Panels to delay the loading of other addons on boot"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 6, 0):
            return True
        cls.poll_message_set("Please upgrade your blender version to 4.0.0 or higher")
        return False

    def draw(self, context):
        layout = self.layout
        # layout.ui_units_x=30
        message_box(
            layout,
            context,
            message="This version of Blender is not officially supported yet. Support is typically added within a few days after Blender's release, so please check for an updated version of the addon. While it will likely work if you click 'OK,' there is a chance it may cause issues. If that happens, you might need to come back and disable it.",
            icon="ERROR",
            alert=True,
            width=700,
        )

    def execute(self, context):
        import addon_utils

        util_file_path = addon_utils.__file__
        try:
            if check_if_old_injection_exists(util_file_path, "atl_file"):
                remove_delayed_load_code(util_file_path)
                preferences().delayed_loading_code_injected = False
            else:
                inject_delayed_load_code(util_file_path)
                preferences().delayed_loading_code_injected = True
            savePreferences()
        except Exception as e:
            self.report(
                {"WARNING"},
                "Please start blender as administrator/superuser (Only required Once)",
            )
            print("Error:", e)
        return {"FINISHED"}

    def invoke(self, context, event):
        blender_version = f"{bpy.app.version[0]}.{bpy.app.version[1]}"

        # Handling specific Blender versions
        if bpy.app.version >= (4, 2, 1):
            blender_version = f"{bpy.app.version[0]}.{bpy.app.version[1]}.1"
        if bpy.app.version >= (4, 2, 3):
            blender_version = f"{bpy.app.version[0]}.{bpy.app.version[1]}.3"
        if bpy.app.version >= (4, 2, 4):
            blender_version = "4.3.0"
        if bpy.app.version >= (4, 3, 0):
            blender_version = f"{bpy.app.version[0]}.{bpy.app.version[1]}.0"

        # Paths
        base_path = os.path.dirname(__file__)
        version_directory = os.path.join(
            base_path, "OG_Blender_Python_Files", blender_version
        )
        if not os.path.exists(version_directory):
            return context.window_manager.invoke_props_dialog(self, width=500)
        return self.execute(context)


class CP_OT_Save_Config(bpy.types.Operator):
    bl_idname = "cp.saveconfig"
    bl_label = "Save Config"
    bl_description = "Save Clean Panels Configuration"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        savePreferences()
        self.report({"INFO"}, "Configuration Saved!")
        return {"FINISHED"}


class CP_OT_Reset_Config(bpy.types.Operator, ExportHelper):
    bl_idname = "cp.resetconfig"
    bl_label = "Reset Config"
    bl_description = "Reset all Clean Panels Settings"
    bl_options = {"REGISTER", "UNDO"}
    filepath: bpy.props.StringProperty(
        name="File Path",
        description="Filepath used for exporting the file",
        subtype="FILE_PATH",
    )
    filename_ext: bpy.props.StringProperty(
        default=".txt", options={"SKIP_SAVE", "HIDDEN"}
    )

    def execute(self, context):
        reset_preferences()
        savePreferences()

        return {"FINISHED"}

    def invoke(self, context: Context, event: Event):
        return context.window_manager.invoke_confirm(self, event)


class CP_OT_Export_Config(bpy.types.Operator, ExportHelper):
    bl_idname = "cp.exportconfig"
    bl_label = "Export Config"
    bl_description = "Export Config File"
    bl_options = {"REGISTER", "UNDO"}
    filepath: bpy.props.StringProperty(
        name="File Path",
        description="Filepath used for exporting the file",
        subtype="FILE_PATH",
    )
    filename_ext: bpy.props.StringProperty(
        default=".json", options={"SKIP_SAVE", "HIDDEN"}
    )

    def execute(self, context):
        savePreferences()
        config_folder_path = Path(bpy.utils.user_resource("SCRIPTS")).parent / "config"
        path = os.path.join(config_folder_path, "CP-config.json")
        if os.path.isfile(path):
            shutil.copy(path, self.filepath)
        return {"FINISHED"}


class CP_OT_Import_Config(bpy.types.Operator, ImportHelper):
    bl_idname = "cp.importconfig"
    bl_label = "Import Config"
    bl_description = "Import Config File"
    bl_options = {"REGISTER", "UNDO"}
    filename_ext = ".txt"
    directory: bpy.props.StringProperty()
    filter_glob: bpy.props.StringProperty(default="*.txt;*.json", options={"HIDDEN"})

    def execute(self, context):
        config_folder_path = Path(bpy.utils.user_resource("SCRIPTS")).parent / "config"

        if os.path.isfile(self.filepath):
            if self.filepath.endswith(".txt"):
                path = os.path.join(config_folder_path, "CP-config.txt")
                data = None
                with open(self.filepath, mode="r", encoding="utf8", newline="\n") as f:
                    data = f.read()  # Read entire file as a string

                try:
                    json_data = json.loads(data)  # Try to parse as JSON
                    # If successful, treat it as a JSON file
                    path = os.path.join(config_folder_path, "CP-config.json")
                    with open(path, mode="w", encoding="utf8", newline="\n") as f:
                        json.dump(json_data, f, indent=4)  # Write formatted JSON
                    loadPreferences()  # Load preferences for JSON
                except json.JSONDecodeError:
                    # If not valid JSON, treat it as plain text
                    with open(path, mode="w", encoding="utf8", newline="\n") as f:
                        f.write(data)  # Write plain text content
                    loadPreferencesOld()  # Load old preferences for text

            elif self.filepath.endswith(".json"):
                path = os.path.join(config_folder_path, "CP-config.json")
                data = None
                with open(self.filepath, mode="r", encoding="utf8", newline="\n") as f:
                    data = f.read()
                with open(path, mode="w", encoding="utf8", newline="\n") as f:
                    f.write(data)  # Write the JSON data directly
                loadPreferences()  # Load preferences for JSON
        return {"FINISHED"}


class CP_OT_Open_Config_Directory(bpy.types.Operator):
    bl_idname = "cp.openconfigdirectory"
    bl_label = "Open Config Directory"
    bl_description = "Open Config Directory"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        config_folder_path = Path(bpy.utils.user_resource("SCRIPTS")).parent / "config"
        os.startfile(config_folder_path)
        return {"FINISHED"}


class CP_OT_Clear_Order(bpy.types.Operator):
    bl_idname = "cp.clearforcedorders"
    bl_label = "Clear Forced Order (Experimental)"
    bl_description = "Clear Forced N-Panel orders\nCTRL+LMB:Reset"
    bl_options = {"REGISTER", "UNDO"}

    # @classmethod
    # def poll(cls,context):
    #     return preferences().addon_info and getattr(preferences(),f"addon_info{get_active_space()}")[getattr(preferences(),f"addon_info{get_active_space()}_index")] and getattr(preferences(),f"addon_info{get_active_space()}")[getattr(preferences(),f"addon_info{get_active_space()}_index")].ordered
    def invoke(self, context, event):
        if event.ctrl:
            clean_all_python_files(remove=True)
        else:
            if (
                preferences().addon_info
                and getattr(preferences(), f"addon_info{get_active_space()}")[
                    getattr(preferences(), f"addon_info{get_active_space()}_index")
                ]
                and getattr(preferences(), f"addon_info{get_active_space()}")[
                    getattr(preferences(), f"addon_info{get_active_space()}_index")
                ].ordered
            ):
                clean_all_python_files(remove=False)

        # reorder_addons(None)
        savePreferences()
        return {"FINISHED"}


class CP_OT_Change_Category(bpy.types.Operator):
    bl_idname = "cp.changecategory"
    bl_label = "Update Category in source file"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def description(self, context, properties):
        if preferences().filtering_method == "Use N-Panel Filtering":
            return "Confirm New Tab Names"
        else:
            return "Set new Tab(This will edit the python files of the addon and replace the panel names with the new name)\nCTRL+LMB:Reset\nSHIFT+LMB:Set for All"

    # @classmethod
    # def poll(cls,context):
    #     return preferences().addon_info and preferences().addon_info[getattr(preferences(),f"addon_info{get_active_space()}_index")] and preferences().addon_info[getattr(preferences(),f"addon_info{get_active_space()}_index")].ordered
    def invoke(self, context, event):
        if not preferences().filtering_method == "Use N-Panel Filtering":
            if event.ctrl:
                if event.shift:
                    for i in range(len(preferences().addon_info_for_renaming)):
                        change_category(i, True)
                else:
                    change_category(preferences().addon_info_for_renaming_index, True)
            else:
                if event.shift:
                    for i in range(len(preferences().addon_info_for_renaming)):
                        change_category(i, False)
                else:
                    change_category(preferences().addon_info_for_renaming_index, False)
        else:
            workspace_category_enabled(preferences().categories, context)
        # reorder_addons(None)
        savePreferences()
        return {"FINISHED"}


class CP_OT_Move_Category(bpy.types.Operator):
    bl_idname = "cp.movecategory"
    bl_label = ""
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}
    direction: bpy.props.StringProperty(default="UP", options={"SKIP_SAVE", "HIDDEN"})
    index: bpy.props.IntProperty()
    category: bpy.props.StringProperty()

    @classmethod
    def description(cls, context, properties):
        if properties.direction == "UP":
            return "Move Up\nCTRL+LMB:Move to Top"
        else:
            return "Move Down\nCTRL+LMB:Move to Bottom"

    def invoke(self, context, event):
        if self.category == "Pie":
            categories = preferences().panel_categories
        elif self.category == "DropDown":
            categories = preferences().dropdown_categories
        elif self.category == "FP":
            categories = getattr(
                preferences(), f"focus_panel_categories{get_active_space()}"
            )
        elif self.category == "Addon Loading":
            categories = preferences().addon_loading_categories
        else:
            categories = getattr(
                preferences(), f"workspace_categories{get_active_space()}"
            )

        if self.direction == "UP":
            new_index = max(0, self.index - 1)
            if event.ctrl:
                new_index = 0
        else:
            new_index = min(len(categories) - 1, self.index + 1)
            if event.ctrl:
                new_index = len(categories) - 1

        categories.move(self.index, new_index)
        # if self.direction=='UP':
        #     if self.index==0:
        #         return {'CANCELLED'}
        # else:
        #     if self.category=='Pie':
        #         if self.index+1>=len(preferences().panel_categories):
        #             return {'CANCELLED'}
        #     elif self.category=='DropDown':
        #         if self.index+1>=len(preferences().dropdown_categories):
        #             return {'CANCELLED'}
        #     elif self.category=='FP':
        #         if self.index+1>=len(getattr(preferences(),f"focus_panel_categories{get_active_space()}")):
        #             return {'CANCELLED'}
        #     elif self.categories=='Addon Loading':
        #         if self.index+1>=len(getattr(preferences(),f"addon_loading_categories")):
        #             return {'CANCELLED'}
        #     else:
        #         if self.index+1>=len(getattr(preferences(),f"workspace_categories{get_active_space()}")):
        #             return {'CANCELLED'}
        # if self.category=='Pie':

        #     if self.direction=='UP':
        #         for index in range(self.index,0 if event.ctrl else self.index-1,-1):
        #             temp_name=preferences().panel_categories[index-1].name
        #             temp_panels=preferences().panel_categories[index-1].panels
        #             preferences().panel_categories[index-1].name=preferences().panel_categories[index].name
        #             preferences().panel_categories[index-1].panels=preferences().panel_categories[index].panels
        #             preferences().panel_categories[index].name=temp_name
        #             preferences().panel_categories[index].panels=temp_panels
        #     else:
        #         for index in range(self.index,len(preferences().panel_categories)-1 if event.ctrl else self.index+1):
        #             temp_name=preferences().panel_categories[index+1].name
        #             temp_panels=preferences().panel_categories[index+1].panels
        #             preferences().panel_categories[index+1].name=preferences().panel_categories[index].name
        #             preferences().panel_categories[index+1].panels=preferences().panel_categories[index].panels
        #             preferences().panel_categories[index].name=temp_name
        #             preferences().panel_categories[index].panels=temp_panels
        # elif self.category=='DropDown':
        #     if self.direction=='UP':
        #         for index in range(self.index,0 if event.ctrl else self.index-1,-1):
        #             temp_name=preferences().dropdown_categories[index-1].name
        #             temp_panels=preferences().dropdown_categories[index-1].panels
        #             preferences().dropdown_categories[index-1].name=preferences().dropdown_categories[index].name
        #             preferences().dropdown_categories[index-1].panels=preferences().dropdown_categories[index].panels
        #             preferences().dropdown_categories[index].name=temp_name
        #             preferences().dropdown_categories[index].panels=temp_panels
        #     else:
        #         for index in range(self.index,len(preferences().dropdown_categories)-1 if event.ctrl else self.index+1):
        #             temp_name=preferences().dropdown_categories[index+1].name
        #             temp_panels=preferences().dropdown_categories[index+1].panels
        #             preferences().dropdown_categories[index+1].name=preferences().dropdown_categories[index].name
        #             preferences().dropdown_categories[index+1].panels=preferences().dropdown_categories[index].panels
        #             preferences().dropdown_categories[index].name=temp_name
        #             preferences().dropdown_categories[index].panels=temp_panels
        # elif self.category=='FP':
        #     if self.direction=='UP':
        #         for index in range(self.index,0 if event.ctrl else self.index-1,-1):
        #             temp_name=getattr(preferences(),f"focus_panel_categories{get_active_space()}")[index-1].name
        #             temp_panels=getattr(preferences(),f"focus_panel_categories{get_active_space()}")[index-1].panels
        #             getattr(preferences(),f"focus_panel_categories{get_active_space()}")[index-1].name=getattr(preferences(),f"focus_panel_categories{get_active_space()}")[index].name
        #             getattr(preferences(),f"focus_panel_categories{get_active_space()}")[index-1].panels=getattr(preferences(),f"focus_panel_categories{get_active_space()}")[index].panels
        #             getattr(preferences(),f"focus_panel_categories{get_active_space()}")[index].name=temp_name
        #             getattr(preferences(),f"focus_panel_categories{get_active_space()}")[index].panels=temp_panels
        #     else:
        #         for index in range(self.index,len(getattr(preferences(),f"focus_panel_categories{get_active_space()}"))-1 if event.ctrl else self.index+1):
        #             temp_name=getattr(preferences(),f"focus_panel_categories{get_active_space()}")[index+1].name
        #             temp_panels=getattr(preferences(),f"focus_panel_categories{get_active_space()}")[index+1].panels
        #             getattr(preferences(),f"focus_panel_categories{get_active_space()}")[index+1].name=getattr(preferences(),f"focus_panel_categories{get_active_space()}")[index].name
        #             getattr(preferences(),f"focus_panel_categories{get_active_space()}")[index+1].panels=getattr(preferences(),f"focus_panel_categories{get_active_space()}")[index].panels
        #             getattr(preferences(),f"focus_panel_categories{get_active_space()}")[index].name=temp_name
        #             getattr(preferences(),f"focus_panel_categories{get_active_space()}")[index].panels=temp_panels
        # else:
        #     if self.direction=='UP':
        #         for index in range(self.index,0 if event.ctrl else self.index-1,-1):
        #             temp_name=getattr(preferences(),f"workspace_categories{get_active_space()}")[index-1].name
        #             temp_panels=getattr(preferences(),f"workspace_categories{get_active_space()}")[index-1].panels
        #             temp_icon=getattr(preferences(),f"workspace_categories{get_active_space()}")[index-1].icon
        #             getattr(preferences(),f"workspace_categories{get_active_space()}")[index-1].name=getattr(preferences(),f"workspace_categories{get_active_space()}")[index].name
        #             getattr(preferences(),f"workspace_categories{get_active_space()}")[index-1].panels=getattr(preferences(),f"workspace_categories{get_active_space()}")[index].panels
        #             getattr(preferences(),f"workspace_categories{get_active_space()}")[index-1].icon=getattr(preferences(),f"workspace_categories{get_active_space()}")[index].icon
        #             getattr(preferences(),f"workspace_categories{get_active_space()}")[index].name=temp_name
        #             getattr(preferences(),f"workspace_categories{get_active_space()}")[index].panels=temp_panels
        #             getattr(preferences(),f"workspace_categories{get_active_space()}")[index].icon=temp_icon
        #     else:
        #         for index in range(self.index,len(getattr(preferences(),f"workspace_categories{get_active_space()}"))-1 if event.ctrl else self.index+1):
        #             temp_name=getattr(preferences(),f"workspace_categories{get_active_space()}")[index+1].name
        #             temp_panels=getattr(preferences(),f"workspace_categories{get_active_space()}")[index+1].panels
        #             temp_icon=getattr(preferences(),f"workspace_categories{get_active_space()}")[index+1].icon
        #             getattr(preferences(),f"workspace_categories{get_active_space()}")[index+1].name=getattr(preferences(),f"workspace_categories{get_active_space()}")[index].name
        #             getattr(preferences(),f"workspace_categories{get_active_space()}")[index+1].panels=getattr(preferences(),f"workspace_categories{get_active_space()}")[index].panels
        #             getattr(preferences(),f"workspace_categories{get_active_space()}")[index+1].icon=getattr(preferences(),f"workspace_categories{get_active_space()}")[index].icon
        #             getattr(preferences(),f"workspace_categories{get_active_space()}")[index].name=temp_name
        #             getattr(preferences(),f"workspace_categories{get_active_space()}")[index].panels=temp_panels
        #             getattr(preferences(),f"workspace_categories{get_active_space()}")[index].icon=temp_icon
        savePreferences()
        return {"FINISHED"}


class CP_OT_Move_Addon_In_Category(bpy.types.Operator):
    bl_idname = "cp.moveaddonincategory"
    bl_label = "Move"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}
    direction: bpy.props.StringProperty(default="UP", options={"SKIP_SAVE", "HIDDEN"})

    @classmethod
    def description(cls, context, properties):
        if properties.direction == "UP":
            return "Move Up\nCTRL+LMB:Move to Top"
        else:
            return "Move Down\nCTRL+LMB:Move to Bottom"

    def invoke(self, context, event):
        to_end = event.ctrl
        scene = context.scene

        index = scene.addon_info_index
        new_index = (
            min(index + 1, len(scene.addon_info) - 1)
            if self.direction == "DOWN"
            else max(0, index - 1)
        )
        if to_end:
            if self.direction == "UP":
                new_index = 0
            else:
                new_index = len(scene.addon_info) - 1
        scene.addon_info.move(index, new_index)
        scene.addon_info_index = new_index
        # if self.direction=='UP':
        #     if scene.addon_info_index>0:
        #         temp_name=scene.addon_info[index-1].name
        #         temp_addons=scene.addon_info[index-1].addons
        #         temp_ordered=scene.addon_info[index-1].ordered
        #         scene.addon_info[index-1].name=scene.addon_info[index].name
        #         scene.addon_info[index-1].addons=scene.addon_info[index].addons
        #         scene.addon_info[index-1].ordered=scene.addon_info[index].ordered
        #         scene.addon_info[index].name=temp_name
        #         scene.addon_info[index].addons=temp_addons
        #         scene.addon_info[index].ordered=temp_ordered
        #         scene.addon_info_index-=1
        # else:
        #     if scene.addon_info_index<len(scene.addon_info)-1:
        #         temp_name=scene.addon_info[index+1].name
        #         temp_addons=scene.addon_info[index+1].addons
        #         temp_ordered=scene.addon_info[index+1].ordered
        #         scene.addon_info[index+1].name=scene.addon_info[index].name
        #         scene.addon_info[index+1].addons=scene.addon_info[index].addons
        #         scene.addon_info[index+1].ordered=scene.addon_info[index].ordered
        #         scene.addon_info[index].name=temp_name
        #         scene.addon_info[index].addons=temp_addons
        #         scene.addon_info[index].ordered=temp_ordered
        #         scene.addon_info_index+=1
        savePreferences()
        return {"FINISHED"}


class CP_OT_Move_Addon(bpy.types.Operator):
    bl_idname = "cp.moveaddon"
    bl_label = "Move"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}
    direction: bpy.props.StringProperty(default="UP", options={"SKIP_SAVE", "HIDDEN"})

    @classmethod
    def description(cls, context, properties):
        if properties.direction == "UP":
            return "Move Up\nCTRL+LMB:Move to Top"
        else:
            return "Move Down\nCTRL+LMB:Move to Bottom"

    def invoke(self, context, event):
        to_end = event.ctrl
        index = getattr(preferences(), f"addon_info{get_active_space()}_index")
        new_index = (
            min(
                index + 1,
                len(getattr(preferences(), f"addon_info{get_active_space()}")) - 1,
            )
            if self.direction == "DOWN"
            else max(0, index - 1)
        )
        if to_end:
            if self.direction == "UP":
                new_index = 0
            else:
                new_index = (
                    len(getattr(preferences(), f"addon_info{get_active_space()}")) - 1
                )
        getattr(preferences(), f"addon_info{get_active_space()}").move(index, new_index)
        setattr(preferences(), f"addon_info{get_active_space()}_index", new_index)
        # if self.direction=='UP':
        #     if getattr(preferences(),f"addon_info{get_active_space()}_index")>0:
        #         temp_name=getattr(preferences(),f"addon_info{get_active_space()}")[index-1].name
        #         temp_addons=getattr(preferences(),f"addon_info{get_active_space()}")[index-1].addons
        #         temp_ordered=getattr(preferences(),f"addon_info{get_active_space()}")[index-1].ordered
        #         getattr(preferences(),f"addon_info{get_active_space()}")[index-1].name=getattr(preferences(),f"addon_info{get_active_space()}")[index].name
        #         getattr(preferences(),f"addon_info{get_active_space()}")[index-1].addons=getattr(preferences(),f"addon_info{get_active_space()}")[index].addons
        #         getattr(preferences(),f"addon_info{get_active_space()}")[index-1].ordered=getattr(preferences(),f"addon_info{get_active_space()}")[index].ordered
        #         getattr(preferences(),f"addon_info{get_active_space()}")[index].name=temp_name
        #         getattr(preferences(),f"addon_info{get_active_space()}")[index].addons=temp_addons
        #         getattr(preferences(),f"addon_info{get_active_space()}")[index].ordered=temp_ordered
        #         setattr(preferences(),f"addon_info{get_active_space()}_index",getattr(preferences(),f"addon_info{get_active_space()}_index")-1)
        # else:
        #     if getattr(preferences(),f"addon_info{get_active_space()}_index")<len(preferences().addon_info)-1:
        #         temp_name=getattr(preferences(),f"addon_info{get_active_space()}")[index+1].name
        #         temp_addons=getattr(preferences(),f"addon_info{get_active_space()}")[index+1].addons
        #         temp_ordered=getattr(preferences(),f"addon_info{get_active_space()}")[index+1].ordered
        #         getattr(preferences(),f"addon_info{get_active_space()}")[index+1].name=getattr(preferences(),f"addon_info{get_active_space()}")[index].name
        #         getattr(preferences(),f"addon_info{get_active_space()}")[index+1].addons=getattr(preferences(),f"addon_info{get_active_space()}")[index].addons
        #         getattr(preferences(),f"addon_info{get_active_space()}")[index+1].ordered=getattr(preferences(),f"addon_info{get_active_space()}")[index].ordered
        #         getattr(preferences(),f"addon_info{get_active_space()}")[index].name=temp_name
        #         getattr(preferences(),f"addon_info{get_active_space()}")[index].addons=temp_addons
        #         getattr(preferences(),f"addon_info{get_active_space()}")[index].ordered=temp_ordered
        #         setattr(preferences(),f"addon_info{get_active_space()}_index",getattr(preferences(),f"addon_info{get_active_space()}_index")+1)
        savePreferences()
        return {"FINISHED"}


class CP_Panel_Category(PropertyGroup):
    # enabled: bpy.props.BoolProperty(default=False,update=workspace_category_enabled)
    icon: bpy.props.StringProperty(default="COLLAPSEMENU", update=savePreferences)
    panels: bpy.props.StringProperty(default="", name="Panels")
    name: bpy.props.StringProperty(
        default="Category", name="Name", update=savePreferences
    )
    show: bpy.props.BoolProperty(default=False, update=savePreferences)
    # type:bpy.props.StringProperty(default="FP")

    # change_category(preferences().addon_info_for_renaming_index)


class Category_Indices(PropertyGroup):
    filter_enabled: bpy.props.BoolProperty(
        default=False, update=workspace_category_enabled, name="Filter"
    )
    filter_enabled_node_editor: bpy.props.BoolProperty(
        default=False, update=workspace_category_enabled, name="Filter"
    )
    filter_enabled_image_editor: bpy.props.BoolProperty(
        default=False, update=workspace_category_enabled, name="Filter"
    )
    enabled_0: bpy.props.BoolProperty(default=False)
    enabled_1: bpy.props.BoolProperty(default=False)
    enabled_2: bpy.props.BoolProperty(default=False)
    enabled_3: bpy.props.BoolProperty(default=False)
    enabled_4: bpy.props.BoolProperty(default=False)
    enabled_5: bpy.props.BoolProperty(default=False)
    enabled_6: bpy.props.BoolProperty(default=False)
    enabled_7: bpy.props.BoolProperty(default=False)
    enabled_8: bpy.props.BoolProperty(default=False)
    enabled_9: bpy.props.BoolProperty(default=False)
    enabled_10: bpy.props.BoolProperty(default=False)
    enabled_11: bpy.props.BoolProperty(default=False)
    enabled_12: bpy.props.BoolProperty(default=False)
    enabled_13: bpy.props.BoolProperty(default=False)
    enabled_14: bpy.props.BoolProperty(default=False)
    enabled_15: bpy.props.BoolProperty(default=False)
    enabled_16: bpy.props.BoolProperty(default=False)
    enabled_17: bpy.props.BoolProperty(default=False)
    enabled_18: bpy.props.BoolProperty(default=False)
    enabled_19: bpy.props.BoolProperty(default=False)
    enabled_20: bpy.props.BoolProperty(default=False)
    enabled_21: bpy.props.BoolProperty(default=False)
    enabled_22: bpy.props.BoolProperty(default=False)
    enabled_23: bpy.props.BoolProperty(default=False)
    enabled_24: bpy.props.BoolProperty(default=False)
    enabled_25: bpy.props.BoolProperty(default=False)
    enabled_26: bpy.props.BoolProperty(default=False)
    enabled_27: bpy.props.BoolProperty(default=False)
    enabled_28: bpy.props.BoolProperty(default=False)
    enabled_29: bpy.props.BoolProperty(default=False)
    enabled_30: bpy.props.BoolProperty(default=False)
    enabled_31: bpy.props.BoolProperty(default=False)
    enabled_32: bpy.props.BoolProperty(default=False)
    enabled_33: bpy.props.BoolProperty(default=False)
    enabled_34: bpy.props.BoolProperty(default=False)
    enabled_35: bpy.props.BoolProperty(default=False)
    enabled_36: bpy.props.BoolProperty(default=False)
    enabled_37: bpy.props.BoolProperty(default=False)
    enabled_38: bpy.props.BoolProperty(default=False)
    enabled_39: bpy.props.BoolProperty(default=False)
    enabled_40: bpy.props.BoolProperty(default=False)
    enabled_41: bpy.props.BoolProperty(default=False)
    enabled_42: bpy.props.BoolProperty(default=False)
    enabled_43: bpy.props.BoolProperty(default=False)
    enabled_44: bpy.props.BoolProperty(default=False)
    enabled_45: bpy.props.BoolProperty(default=False)
    enabled_46: bpy.props.BoolProperty(default=False)
    enabled_47: bpy.props.BoolProperty(default=False)
    enabled_48: bpy.props.BoolProperty(default=False)
    enabled_49: bpy.props.BoolProperty(default=False)
    enabled_node_editor_0: bpy.props.BoolProperty(default=False)
    enabled_node_editor_1: bpy.props.BoolProperty(default=False)
    enabled_node_editor_2: bpy.props.BoolProperty(default=False)
    enabled_node_editor_3: bpy.props.BoolProperty(default=False)
    enabled_node_editor_4: bpy.props.BoolProperty(default=False)
    enabled_node_editor_5: bpy.props.BoolProperty(default=False)
    enabled_node_editor_6: bpy.props.BoolProperty(default=False)
    enabled_node_editor_7: bpy.props.BoolProperty(default=False)
    enabled_node_editor_8: bpy.props.BoolProperty(default=False)
    enabled_node_editor_9: bpy.props.BoolProperty(default=False)
    enabled_node_editor_10: bpy.props.BoolProperty(default=False)
    enabled_node_editor_11: bpy.props.BoolProperty(default=False)
    enabled_node_editor_12: bpy.props.BoolProperty(default=False)
    enabled_node_editor_13: bpy.props.BoolProperty(default=False)
    enabled_node_editor_14: bpy.props.BoolProperty(default=False)
    enabled_node_editor_15: bpy.props.BoolProperty(default=False)
    enabled_node_editor_16: bpy.props.BoolProperty(default=False)
    enabled_node_editor_17: bpy.props.BoolProperty(default=False)
    enabled_node_editor_18: bpy.props.BoolProperty(default=False)
    enabled_node_editor_19: bpy.props.BoolProperty(default=False)
    enabled_node_editor_20: bpy.props.BoolProperty(default=False)
    enabled_node_editor_21: bpy.props.BoolProperty(default=False)
    enabled_node_editor_22: bpy.props.BoolProperty(default=False)
    enabled_node_editor_23: bpy.props.BoolProperty(default=False)
    enabled_node_editor_24: bpy.props.BoolProperty(default=False)
    enabled_node_editor_25: bpy.props.BoolProperty(default=False)
    enabled_node_editor_26: bpy.props.BoolProperty(default=False)
    enabled_node_editor_27: bpy.props.BoolProperty(default=False)
    enabled_node_editor_28: bpy.props.BoolProperty(default=False)
    enabled_node_editor_29: bpy.props.BoolProperty(default=False)
    enabled_node_editor_30: bpy.props.BoolProperty(default=False)
    enabled_node_editor_31: bpy.props.BoolProperty(default=False)
    enabled_node_editor_32: bpy.props.BoolProperty(default=False)
    enabled_node_editor_33: bpy.props.BoolProperty(default=False)
    enabled_node_editor_34: bpy.props.BoolProperty(default=False)
    enabled_node_editor_35: bpy.props.BoolProperty(default=False)
    enabled_node_editor_36: bpy.props.BoolProperty(default=False)
    enabled_node_editor_37: bpy.props.BoolProperty(default=False)
    enabled_node_editor_38: bpy.props.BoolProperty(default=False)
    enabled_node_editor_39: bpy.props.BoolProperty(default=False)
    enabled_node_editor_40: bpy.props.BoolProperty(default=False)
    enabled_node_editor_41: bpy.props.BoolProperty(default=False)
    enabled_node_editor_42: bpy.props.BoolProperty(default=False)
    enabled_node_editor_43: bpy.props.BoolProperty(default=False)
    enabled_node_editor_44: bpy.props.BoolProperty(default=False)
    enabled_node_editor_45: bpy.props.BoolProperty(default=False)
    enabled_node_editor_46: bpy.props.BoolProperty(default=False)
    enabled_node_editor_47: bpy.props.BoolProperty(default=False)
    enabled_node_editor_48: bpy.props.BoolProperty(default=False)
    enabled_node_editor_49: bpy.props.BoolProperty(default=False)
    enabled_image_editor_0: bpy.props.BoolProperty(default=False)
    enabled_image_editor_1: bpy.props.BoolProperty(default=False)
    enabled_image_editor_2: bpy.props.BoolProperty(default=False)
    enabled_image_editor_3: bpy.props.BoolProperty(default=False)
    enabled_image_editor_4: bpy.props.BoolProperty(default=False)
    enabled_image_editor_5: bpy.props.BoolProperty(default=False)
    enabled_image_editor_6: bpy.props.BoolProperty(default=False)
    enabled_image_editor_7: bpy.props.BoolProperty(default=False)
    enabled_image_editor_8: bpy.props.BoolProperty(default=False)
    enabled_image_editor_9: bpy.props.BoolProperty(default=False)
    enabled_image_editor_10: bpy.props.BoolProperty(default=False)
    enabled_image_editor_11: bpy.props.BoolProperty(default=False)
    enabled_image_editor_12: bpy.props.BoolProperty(default=False)
    enabled_image_editor_13: bpy.props.BoolProperty(default=False)
    enabled_image_editor_14: bpy.props.BoolProperty(default=False)
    enabled_image_editor_15: bpy.props.BoolProperty(default=False)
    enabled_image_editor_16: bpy.props.BoolProperty(default=False)
    enabled_image_editor_17: bpy.props.BoolProperty(default=False)
    enabled_image_editor_18: bpy.props.BoolProperty(default=False)
    enabled_image_editor_19: bpy.props.BoolProperty(default=False)
    enabled_image_editor_20: bpy.props.BoolProperty(default=False)
    enabled_image_editor_21: bpy.props.BoolProperty(default=False)
    enabled_image_editor_22: bpy.props.BoolProperty(default=False)
    enabled_image_editor_23: bpy.props.BoolProperty(default=False)
    enabled_image_editor_24: bpy.props.BoolProperty(default=False)
    enabled_image_editor_25: bpy.props.BoolProperty(default=False)
    enabled_image_editor_26: bpy.props.BoolProperty(default=False)
    enabled_image_editor_27: bpy.props.BoolProperty(default=False)
    enabled_image_editor_28: bpy.props.BoolProperty(default=False)
    enabled_image_editor_29: bpy.props.BoolProperty(default=False)
    enabled_image_editor_30: bpy.props.BoolProperty(default=False)
    enabled_image_editor_31: bpy.props.BoolProperty(default=False)
    enabled_image_editor_32: bpy.props.BoolProperty(default=False)
    enabled_image_editor_33: bpy.props.BoolProperty(default=False)
    enabled_image_editor_34: bpy.props.BoolProperty(default=False)
    enabled_image_editor_35: bpy.props.BoolProperty(default=False)
    enabled_image_editor_36: bpy.props.BoolProperty(default=False)
    enabled_image_editor_37: bpy.props.BoolProperty(default=False)
    enabled_image_editor_38: bpy.props.BoolProperty(default=False)
    enabled_image_editor_39: bpy.props.BoolProperty(default=False)
    enabled_image_editor_40: bpy.props.BoolProperty(default=False)
    enabled_image_editor_41: bpy.props.BoolProperty(default=False)
    enabled_image_editor_42: bpy.props.BoolProperty(default=False)
    enabled_image_editor_43: bpy.props.BoolProperty(default=False)
    enabled_image_editor_44: bpy.props.BoolProperty(default=False)
    enabled_image_editor_45: bpy.props.BoolProperty(default=False)
    enabled_image_editor_46: bpy.props.BoolProperty(default=False)
    enabled_image_editor_47: bpy.props.BoolProperty(default=False)
    enabled_image_editor_48: bpy.props.BoolProperty(default=False)
    enabled_image_editor_49: bpy.props.BoolProperty(default=False)


def reload_icons(self, context):
    savePreferences()
    load_icons(only_custom=True)


def remove_holder_tab_update(self, context):
    if not self.remove_holder_tab:
        if not self.holder_tab_name:
            self.holder_tab_name = "DUMP"


def get_main_pref_tabs(self, context):
    tabs = ["Organize", "Config", "Keymaps", "Help"]  #
    # tabs.append()
    enum = [(a, a, a) for a in tabs]
    enum.insert(1, (("PRO", "Pro Features", "Pro Features")))
    return enum


def get_pref_tabs(self, context):
    tabs = []
    tabs.extend(
        [("Filtering", "Filtering", "Filtering"), ("FP", "Focus Panel", "Focus Panel")]
    )

    if not self.hide_pie_panels and not self.easy_mode:
        tabs.append(("Pie", "Pie Panels", "Pie Panels"))
    if not self.hide_dropdown_panels and not self.easy_mode:
        tabs.append(("DropDown", "DropDown", "DropDown"))
    if self.filtering_method == "Use N-Panel Filtering" or self.experimental:
        tabs.extend(
            [
                ("Renaming", "Renaming", "N-Panel Renaming"),
                ("Reordering", "Reordering", "N-Panel Reordering"),
            ]
        )
    else:
        tabs = []

    if self.space_type in ["NODE_EDITOR", "IMAGE_EDITOR"]:
        tabs = (
            ("Filtering", "Filtering", "Filtering"),
            ("FP", "Focus Panel", "Focus Panel"),
            ("Renaming", "Renaming", "N-Panel Renaming"),
            ("Reordering", "Reordering", "N-Panel Reordering"),
        )
    return tabs


def get_qs_tabs(self, context):
    tabs = []
    if not self.hide_pie_panels and not self.easy_mode:
        tabs.append(("Pie", "Pie Panels", "Pie Panels"))
    if not self.hide_dropdown_panels and not self.easy_mode:
        tabs.append(("DropDown", "DropDown", "DropDown"))
    tabs.extend(
        [("Filtering", "Filtering", "Filtering"), ("FP", "Focus Panel", "Focus Panel")]
    )
    if self.space_type in ["NODE_EDITOR", "IMAGE_EDITOR"]:
        tabs = (
            ("Filtering", "Filtering", "Filtering"),
            ("FP", "Focus Panel", "Focus Panel"),
        )
    return tabs


class PAPPrefs(bpy.types.AddonPreferences, AddonUpdateChecker):
    bl_idname = __package__

    def _update_easy_mode(self, context):
        if self.easy_mode:
            self.space_type = "VIEW_3D"

    def get_workspace_categories(self, space):
        if "IMAGE_EDITOR" in space:
            return self.workspace_categories_image_editor
        elif "NODE_EDITOR" in space:
            return self.workspace_categories_node_editor
        else:
            return self.workspace_categories

    def add_to_category(self, category, addon):
        panels = split_keep_substring(category.panels)
        if addon not in panels:
            panels.append(addon)
        category.panels = ",".join(panels)

    def get_addons_to_exclude(self, space):
        if "IMAGE_EDITOR" in space:
            return self.addons_to_exclude_image_editor
        elif "NODE_EDITOR" in space:
            return self.addons_to_exclude_node_editor
        else:
            return self.addons_to_exclude

    config_corrupted: bpy.props.BoolProperty(
        default=False,
        name="Config Corrupted",
        description="The config file has been corrupted and needs to be reloaded",
    )
    auto_run_magic_setup: bpy.props.BoolProperty(
        default=False,
        name="Run on Boot",
        description="Automatically run the Magic Setup when opening Blender, to try and automatically assign any newly installed addons to the correct category",
    )
    show_button_to_load_uncategorized: bpy.props.BoolProperty(
        default=False,
        name="Show Button for Uncategorized Addons in Filtering",
        description="Display a button to load addons not assigned to any category or exclusion list",
    )
    show_quick_reorder: bpy.props.BoolProperty(
        default=True, name="Show Quick Re-Order Button in Viewport Header"
    )
    show_quick_focus_search_button: bpy.props.BoolProperty(
        default=False,
        name="Show Focus Panel Search Button in Viewport Header")
    easy_mode: bpy.props.BoolProperty(
        default=True,
        name="Easy Mode",
        description="Disable non essential features and make the interface simpler",
        update=_update_easy_mode,
    )
    main_tabs: bpy.props.EnumProperty(items=get_main_pref_tabs, default=0)
    remove_uninstalled_addons: bpy.props.BoolProperty(
        default=True,
        name="Remove Uninstalled Addons from renaming and reordering lists",
        description="Automatically remove uninstalled add-ons from the renaming and reordering lists to keep them organized and clutter-free.",
    )
    use_filtering_in_node_editor: bpy.props.BoolProperty(
        default=True,
        name="Use N-Panel Filtering in Node Editor",
        description="Use the N-Panel filtering method in the Node Editor",
    )
    use_filtering_in_image_editor: bpy.props.BoolProperty(
        default=True,
        name="Use N-Panel Filtering in Image Editor",
        description="Use the N-Panel filtering method in the Image Editor",
    )
    hide_pie_panels: bpy.props.BoolProperty(default=False, name="Hide Pie Panels")
    hide_dropdown_panels: bpy.props.BoolProperty(
        default=False, name="Hide Dropdown Panels"
    )
    use_enum_search_for_popups: bpy.props.BoolProperty(
        default=False,
        name="Use Search instead of Popup for adding Panels/Addons to categories",
        description="Use a search popup to add add-ons or tabs to categories instead of the checkbox list.",
    )
    auto_backup_addons: bpy.props.BoolProperty(
        default=False,
        name="Automatically Backup addons before making changes",
        description=f"Create automatic backups while editing the addon files (for N-Panel renaming and clearing forced orders)\n Stored at: {os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),'Addon-Backups-CleanPanels')}",
    )
    show_panel_pies: bpy.props.BoolProperty(default=False, name="Panels and Pies")
    pop_out_style: bpy.props.EnumProperty(
        items=(
            ("Pie-PopUp", "Pie-PopUp", "Pie-PopUp"),
            ("DropDown", "DropDown", "DropDown"),
        ),
        default=0,
        name="PopUp Panel Style",
        update=savePreferences,
    )
    show_keymaps: bpy.props.BoolProperty(default=False, name="Key Maps")
    active_tab: bpy.props.EnumProperty(
        items=get_pref_tabs, default=0, name="Active Tab", update=savePreferences
    )
    active_tab_quick_settings: bpy.props.EnumProperty(
        items=get_qs_tabs, default=0, name="Active Tab", update=savePreferences
    )
    addon_loading_categories: bpy.props.CollectionProperty(type=CP_Panel_Category)
    panel_categories: bpy.props.CollectionProperty(type=CP_Panel_Category)
    dropdown_categories: bpy.props.CollectionProperty(type=CP_Panel_Category)
    workspace_categories: bpy.props.CollectionProperty(type=CP_Panel_Category)
    focus_panel_categories: bpy.props.CollectionProperty(type=CP_Panel_Category)
    workspace_categories_image_editor: bpy.props.CollectionProperty(
        type=CP_Panel_Category
    )
    focus_panel_categories_image_editor: bpy.props.CollectionProperty(
        type=CP_Panel_Category
    )
    workspace_categories_node_editor: bpy.props.CollectionProperty(
        type=CP_Panel_Category
    )
    focus_panel_categories_node_editor: bpy.props.CollectionProperty(
        type=CP_Panel_Category
    )
    load_addons_with_filtering: bpy.props.BoolProperty(
        default=False,
        name="Load addons using the filtering categories",
        description="Load missing(not loaded yet) addons when using the filtering categories",
    )
    show_addon_loading_categories: bpy.props.BoolProperty(
        default=False, name="Add-on Sets Categories"
    )
    show_panel_categories: bpy.props.BoolProperty(default=False, name="Pie Panels")
    show_dropdown_categories: bpy.props.BoolProperty(
        default=False, name="Dropdown Panels"
    )
    show_workspace_categories: bpy.props.BoolProperty(
        default=False, name="Workspace Addon Categories"
    )
    show_npanel_ordering: bpy.props.BoolProperty(
        default=False, name="N-Panel ReOrdering"
    )
    show_npanel_renaming: bpy.props.BoolProperty(default=False, name="N-Panel Renaming")
    show_focus_panel_categories: bpy.props.BoolProperty(
        default=False, name="Focus Panel Categories"
    )
    draw_side: bpy.props.EnumProperty(
        name="Draw Side",
        items=(("LEFT", "Left", "Left"), ("RIGHT", "Right", "Right")),
        update=draw_side_changed,
        default="RIGHT",
    )
    addons_to_exclude: bpy.props.StringProperty(
        default="",
        name="Addons To Exclude (Will always be available)",
        update=exclusion_list_changed,
    )
    addons_to_exclude_node_editor: bpy.props.StringProperty(
        default="",
        name="Addons To Exclude (Will always be available)",
        update=exclusion_list_changed,
    )
    addons_to_exclude_image_editor: bpy.props.StringProperty(
        default="",
        name="Addons To Exclude (Will always be available)",
        update=exclusion_list_changed,
    )
    experimental: bpy.props.BoolProperty(
        default=False, name="Experimental Features", update=savePreferences
    )
    use_sticky_popup: bpy.props.BoolProperty(
        default=True,
        name="Use Sticky Popups",
        update=savePreferences,
        description="Use Sticky Popups to keep dropdowns visible even when the mouse moves outside them. However, they will still close when you click in the viewport.",
    )
    addon_info: bpy.props.CollectionProperty(type=AddonInfo)
    addon_info_for_renaming: bpy.props.CollectionProperty(type=AddonInfoRename)
    addon_info_index: bpy.props.IntProperty(default=0, name="Selected Tab")
    addon_info_for_renaming_index: bpy.props.IntProperty(
        default=0, name="Selected Addon"
    )
    addon_info_image_editor: bpy.props.CollectionProperty(type=AddonInfo)
    addon_info_for_renaming_image_editor: bpy.props.CollectionProperty(
        type=AddonInfoRename
    )
    addon_info_image_editor_index: bpy.props.IntProperty(default=0, name="Selected Tab")
    addon_info_for_renaming_image_editor_index: bpy.props.IntProperty(
        default=0, name="Selected Addon"
    )
    addon_info_node_editor: bpy.props.CollectionProperty(type=AddonInfo)
    addon_info_for_renaming_node_editor: bpy.props.CollectionProperty(
        type=AddonInfoRename
    )
    addon_info_node_editor_index: bpy.props.IntProperty(default=0, name="Selected Tab")
    addon_info_for_renaming_node_editor_index: bpy.props.IntProperty(
        default=0, name="Selected Addon"
    )
    injected_code: bpy.props.BoolProperty(default=check_for_injection())
    injected_code_tracking: bpy.props.BoolProperty(
        default=check_for_tracking_injection()
    )
    delayed_loading_code_injected: bpy.props.BoolProperty(
        default=check_for_delayed_loading_injection()
    )
    columm_layout_for_popup: bpy.props.BoolProperty(
        default=True,
        name="Use Column Layout (Dropdowns will be stacked)",
        update=savePreferences,
    )
    use_verticle_menu: bpy.props.BoolProperty(
        default=True, name="Use list instead of 2nd pie menu"
    )
    dropdown_width: bpy.props.IntProperty(
        default=16, name="Dropdown Width", min=5, max=50
    )
    show_dropdown_search: bpy.props.BoolProperty(
        default=False,
        name="Show Dropdown search button",
        description="Show a search button to search for any tab and show it as a popup similar to dropdown",
    )
    categories: bpy.props.PointerProperty(type=Category_Indices)
    # filtering_method: bpy.props.BoolProperty(default=False,name="Use Unregister/Reregister Method for filtering (Restart after changing this)")
    filtering_method: bpy.props.EnumProperty(
        items=(
            (
                "Use Workspace Filtering",
                "Use Workspace Filtering",
                "Use Workspace Filtering",
            ),
            ("Use N-Panel Filtering", "Use N-Panel Filtering", "Use N-Panel Filtering"),
        ),
        default=1,
        name="How to clean the N-Panel (Restart after changing this)",
    )
    show_advanced: bpy.props.BoolProperty(default=False, name="Show Advanced Options")
    use_dropdowns: bpy.props.BoolProperty(default=True, name="Show Dropdowns")
    sort_per_category: bpy.props.BoolProperty(
        default=False,
        name="Sort Tabs per Category",
        description="Sort Tabs based on the order specified in the categories",
    )
    holder_tab_name: bpy.props.StringProperty(
        default="DUMP", name="Tab name for filtered out addons"
    )
    remove_holder_tab: bpy.props.BoolProperty(
        default=True, name="Remove Holder Tab", update=remove_holder_tab_update
    )
    custom_icons_dir: bpy.props.StringProperty(
        default="",
        name="Custom Icons Directory",
        update=reload_icons,
        subtype="DIR_PATH",
    )
    sort_focus_menu_based_on_clicks: bpy.props.BoolProperty(
        default=False,
        name="Sort Focus Panel List based on clicks",
        description="Sort the focus panel list based on which ones you click the most",
    )
    addon_desc_info: bpy.props.CollectionProperty(type=AddonDescriptionInfo)
    filtering_per_workspace: bpy.props.BoolProperty(
        default=False,
        name="Use Filtering Per Workspace",
        description="Have different sets of categories enabled for different workspaces",
    )
    only_show_unfiltered_panels: bpy.props.BoolProperty(
        default=True,
        name="Only Show Tabs from Enabled 'Filtering Categories' in Focus Panel List",
        description="Only Show tabs from unfiltered add-ons in the Focus Panels list. Disabling this will display a complete list of all tabs, including those from filtered-out add-ons.",
    )
    show_delete_buttons_in_quick_settings: bpy.props.BoolProperty(
        default=False, name="Show delete buttons in Quick Settings Panel"
    )
    move_dropdowns_to_toolbar: bpy.props.BoolProperty(
        default=False,
        name="Show in Toolbar (Same row as the Filter Options)",
        description="Move dropdowns to the toolbar (Same row as the Filter Options)",
        update=draw_side_changed,
    )
    space_type: bpy.props.EnumProperty(
        items=[
            ("VIEW_3D", "Viewport", "Viewport"),
            ("NODE_EDITOR", "Node Editor", "Shader/Geometry Node Editor"),
            ("IMAGE_EDITOR", "Image/UV Editor", "Image Editor"),
        ],
        default=0,
        name="Space Type",
    )
    show_favorites: bpy.props.BoolProperty(default=False, name="Favorites")
    favorites: bpy.props.CollectionProperty(type=CP_Panel_Category)
    favorites_index: bpy.props.IntProperty()
    filter_internal_tabs: bpy.props.BoolProperty(
        default=False,
        name="Filter Internal Tabs(View, Tool, Node and Options)",
        description="Filter and Sort Internal tabs(View, Tool, Node and Options).",
        update=draw_side_changed,
    )
    delayed_addons_loaded: bpy.props.BoolProperty(default=False)
    atl_list: bpy.props.StringProperty(default="", name="Addons to load on boot")
    show_pro_options: bpy.props.BoolProperty(default=False, name="Pro Features")
    show_enabledisable_in_quick_settings: bpy.props.BoolProperty(
        default=False, name="Show Enable/Disable Addons in Quick Settings"
    )
    show_fixes: bpy.props.BoolProperty(default=False, name="Fixes")
    zen_uv_fix: bpy.props.BoolProperty(
        default=False,
        name="Zen UV Fix",
        description="Zen UV needs grease pencil panel(from View Tab) to be available for it to work, Enabling this will make sure its not removed even when Internal tab filtering is enabled.",
    )
    show_help: bpy.props.BoolProperty(default=False, name="Help", description="")
    show_config_ie: bpy.props.BoolProperty(
        default=False, name="Config Import/Export", description=""
    )

    def draw(self, context):
        draw_update_section_for_prefs(self.layout, context)
        from .guide_ops import cp_guides

        if not cp_guides.preferences.finished_once and not cp_guides.preferences.hidden:
            draw_guide_section(self.layout, context, True)
            return
        layout2 = draw_settings(self, self, context)
        # self.draw_pro_settings(layout2)
        # layout3 = layout2.box()
        # layout3.operator("cp.savekeymap")
        # if draw_dropdown_panel(layout3,self,'show_config_ie'):
        #     row=layout3.row(align=True)
        #     row.operator("cp.exportconfig",icon='EXPORT')
        #     row.operator("cp.importconfig",icon='IMPORT')
        #     row.operator('cp.importconfig',icon='IMPORT',text='Import Backup Config').directory=os.path.join(Path(bpy.utils.user_resource('SCRIPTS')).parent/"config","CP-Backups")
        # layout3 = layout2.box()
        # if draw_dropdown_panel(layout3,self,'show_help'):
        # pcoll = icon_collection["icons"]
        # youtube_icon = pcoll["youtube"]
        # discord_icon=pcoll["discord"]
        # green=pcoll["updategreen"]
        # red=pcoll["updatered"]
        # box=layout2.box()
        # # box.label(text=context.scene.cp_update_status,icon_value=green.icon_id if 'Clean Panels is Up To Date!' in context.scene.cp_update_status  else red.icon_id)
        # row=box.row()
        # row.operator('wm.url_open',text="Documentation",icon="HELP").url="https://cleanpanels.notion.site/Clean-Panels-Wiki-487866054aa54ac583c1ece88a7c6f0c"
        # row=box.row(align=True)
        # row.operator('wm.url_open',text="Chat Support",icon_value=discord_icon.icon_id).url="https://discord.gg/Ta4P3uJXtQ"
        # row.operator('wm.url_open',text="Youtube",icon_value=youtube_icon.icon_id).url="https://www.youtube.com/channel/UCKgXKh-_kOgzdV8Q12kraHA"
        # box=layout2.box()
        # if draw_dropdown_panel(box,self,'show_fixes'):
        #     row=box.row()
        #     row.prop(self,'zen_uv_fix',text="Zen UV Fix")

    def draw_pro_settings(self, layout2):
        help_row = layout2.row(align=True)
        help_row.alignment = "RIGHT"
        op = help_row.operator("cp.showhelp", text="Help", icon="HELP")
        op.text = "Delayed Loading lets you choose which add-ons Blender loads at startup, leaving others to load only when needed. This helps reduce boot times. You can create categories to load specific add-ons or use the 'Load using Filtering Categories' option to load add-ons based on your selected filtering categories."
        op.link = "https://www.youtube.com/watch?v=-u_v0swUorg"
        pcoll = icon_collection["icons"]
        layout3 = layout2

        # if draw_dropdown_panel(layout3,self,'show_pro_options'):

        layout3.label(
            text="Ensure you have started Blender with admin rights to enable or disable this!",
            icon="INFO",
        )
        layout3.label(
            text="Remember to restart Blender after enabling or disabling this!"
        )
        row = layout3.row()
        main_row = row.split(factor=0.8)
        main_row.scale_y = 2
        main_row.operator(
            "cp.enabledelayedloading",
            text="Enable Delayed Addon Loading"
            if not preferences().delayed_loading_code_injected
            else "Disable Delayed Addon Loading",
            depress=preferences().delayed_loading_code_injected,
        )
        main_row.operator(
            "cp.enableaddons",
            icon="FILE_REFRESH",
        )
        if bpy.app.version < (4, 2, 0):
            layout2.separator()
        else:
            layout2.separator(type="LINE")
        layout3.prop(self, "load_addons_with_filtering")
        if preferences().delayed_loading_code_injected:
            row2 = layout3.row()
            row2 = row2.split(factor=0.8)
            row2.prop(self, f"atl_list")
            row2.operator("cp.setatl", text="", icon="ADD", depress=True)
            if preferences().atl_list:
                grid = layout3.grid_flow(columns=4, row_major=True)
                for panel in split_keep_substring(preferences().atl_list):
                    if panel:
                        op = grid.operator(
                            "cp.remove_panel", text=panel, icon="PANEL_CLOSE"
                        )
                        op.index = 1
                        op.panel = panel
                        op.category = "ATL"
            # row = layout3.row(align=True)
            # row.alignment = 'LEFT'
            # row.prop(self, "show_addon_loading_categories", emboss=False,text="Addon Sets" ,
            #         icon="TRIA_DOWN" if self.show_addon_loading_categories else "TRIA_RIGHT")
            # if self.show_addon_loading_categories:
            if (
                not "addons_to_load"
                in inspect.signature(addon_utils.reset_all).parameters
            ):
                row = layout3.row()
                row.alignment = "CENTER"
                row.alert = True
                row.label(
                    text="Please disable and re-enable delayed loading to use loading categories!",
                    icon="ERROR",
                )

            layout3.separator(factor=1)
            # if draw_dropdown_panel(layout3,self,'show_addon_loading_categories'):
            # row=layout3.column()
            first_row = layout3.row(align=True)
            btn_row = first_row.row(align=True)
            btn_row.alignment = "LEFT"
            btn_row.operator(
                "cp.batchassigncategories", icon="GROUP_VERTEX"
            ).category = "AddonLoading"
            btn_row = first_row.row(align=True)
            btn_row.alignment = "RIGHT"
            btn_row.operator("cp.delayedcategoriesfromfiltering", icon="PASTEDOWN")
            row = layout3.column()
            for index, a in enumerate(getattr(self, f"addon_loading_categories")):
                row.separator(factor=0.2)
                box = row.box()
                if draw_category(
                    box, a, "show", a.name, index, pcoll, False, "addon_loading"
                ):
                    row1 = box.row()
                    # row1=row1.split(factor=0.7)

                    row1.prop(a, "name", text="")
                    # row2=row1.split(factor=0.75)
                    # op = row2.operator('cp.remove_category_from_addon_loading', text='',
                    #                                 icon='PANEL_CLOSE')
                    # op.index = index

                    # op = row2.operator('cp.movecategory', text='',
                    #                                 icon='TRIA_UP')
                    # op.index = index
                    # op.category = 'Addon Loading'
                    # op.direction='UP'

                    row1 = box.row()
                    row1 = row1.split(factor=0.75)
                    row2 = row1.row()
                    # row1=row1.split(factor=0.75)
                    row2.prop(a, "panels")
                    if not a.panels:
                        row2.enabled = False
                    # row3=row1.split(factor=0.72)
                    row1.operator(
                        "cp.search_popup_for_addon_loading",
                        text="",
                        icon="ADD",
                        depress=True,
                    ).index = index
                    # op = row1.operator('cp.movecategory', text='',
                    #                 icon='TRIA_DOWN')
                    # op.index = index
                    # op.category = 'Addon Loading'
                    # op.direction='DOWN'

                    grid = box.grid_flow(columns=4, row_major=True)
                    for panel in split_keep_substring(a.panels):
                        if panel:
                            op = grid.operator(
                                "cp.remove_panel", text=panel, icon="PANEL_CLOSE"
                            )
                            op.index = index
                            op.panel = panel
                            op.category = "Addon Loading"
            row.separator(factor=1)
            button_row = row.row(align=True)
            # button_row.scale_y=2
            button_row.alignment = "CENTER"
            button_row.operator("cp.add_category", icon="ADD").to = "Addon Loading"
        if not self.easy_mode:
            layout3.separator()
            row = layout3.row()
            row.operator("cp.exportaddonslist", icon="EXPORT")


def preferences() -> PAPPrefs:
    return bpy.context.preferences.addons[__package__].preferences


class CP_Show_Help(bpy.types.Operator):
    bl_idname = "cp.showhelp"
    bl_label = "Help"
    bl_description = "Learn about this functionality"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    text: bpy.props.StringProperty()
    link: bpy.props.StringProperty()

    def draw(self, context):
        layout = self.layout
        layout.ui_units_x = 30
        message_box(layout, context, self.text, width=self.width, icon="HELP")
        layout.operator("wm.url_open", text="Watch Video", icon="URL").url = self.link

    def execute(self, context):
        return {"FINISHED"}

    def invoke(self, context, event):
        self.width = 1000
        return context.window_manager.invoke_popup(self)


class PAP_Import_Workspaces(bpy.types.Operator):
    bl_idname = "cp.importworkspaces"
    bl_label = "Import Workspaces as Categories for Filtering"
    bl_description = (
        "Create categories from all available workspaces which have filtering enabled"
    )
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    name: bpy.props.StringProperty()

    def invoke(self, context, event):
        for w in bpy.data.workspaces:
            if w.use_filter_by_owner:
                t = getattr(
                    preferences(), f"workspace_categories{get_active_space()}"
                ).add()
                t.name = w.name
                t.panels = ",".join(
                    [
                        c.name
                        for c in w.owner_ids
                        if c.name
                        not in split_keep_substring(
                            getattr(
                                preferences(), f"addons_to_exclude{get_active_space()}"
                            )
                        )
                        + addons_to_exclude
                    ]
                )
        savePreferences()
        return {"FINISHED"}


class PAP_Addon_Info(bpy.types.Operator):
    bl_idname = "cp.addonsinfo"
    bl_label = "Enable/Disable Addons"
    bl_description = "Enable/Disable addons or add notes about their functionality"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.label(text="Enabled:")
        grid = box.grid_flow(
            columns=int(len(self.disabled_addons + self.enabled_addons) / 29)
        )
        for module, name in self.enabled_addons:
            is_enabled = module.__name__ in {
                ext.module for ext in context.preferences.addons
            }
            row = grid.row()

            row.operator(
                "preferences.addon_disable"
                if is_enabled
                else "preferences.addon_enable",
                icon="CHECKBOX_HLT" if is_enabled else "CHECKBOX_DEHLT",
                text="",
                emboss=False,
            ).module = module.__name__
            row = row.split(factor=0.9)
            row.label(text=name)
            row.operator(
                "cp.addonsdescription", text="", icon="INFO", emboss=False
            ).module_name = module.__name__
        box = layout.box()
        box.label(text="Disabled:")
        grid = box.grid_flow(
            columns=int(len(self.disabled_addons + self.enabled_addons) / 29)
        )
        for module, name in self.disabled_addons:
            is_enabled = module.__name__ in {
                ext.module for ext in context.preferences.addons
            }
            row = grid.row()
            row.operator(
                "preferences.addon_disable"
                if is_enabled
                else "preferences.addon_enable",
                icon="CHECKBOX_HLT" if is_enabled else "CHECKBOX_DEHLT",
                text="",
                emboss=False,
            ).module = module.__name__
            row = row.split(factor=0.9)
            row.label(text=name)
            row.operator(
                "cp.addonsdescription", text="", icon="INFO", emboss=False
            ).module_name = module.__name__

    def execute(self, context):
        return {"FINISHED"}

    def invoke(self, context, event):
        self.enabled_addons = [
            (a, addon_utils.module_bl_info(a)["name"])
            for a in addon_utils.modules()
            if addon_utils.check(a.__name__)[1]
        ]
        self.disabled_addons = [
            (a, addon_utils.module_bl_info(a)["name"])
            for a in addon_utils.modules()
            if not addon_utils.check(a.__name__)[1]
        ]
        self.enabled_addons = sorted(self.enabled_addons, key=lambda x: x[1].lower())
        self.disabled_addons = sorted(self.disabled_addons, key=lambda x: x[1].lower())
        return context.window_manager.invoke_props_dialog(
            self, width=200 * int(len(self.disabled_addons + self.enabled_addons) / 29)
        )


class PAP_Addon_Description(bpy.types.Operator):
    bl_idname = "cp.addonsdescription"
    bl_label = "Addons Description"
    bl_description = "Info about the addon"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    module_name: bpy.props.StringProperty()

    def draw(self, context):
        layout = self.layout
        layout.label(text="", icon="INFO")
        lines = textwrap.wrap(self.desc, 100, break_long_words=False)
        for l in lines:
            row = layout.row()
            row.label(text=l)
        # row.label(text=self.desc)
        row.operator(
            "cp.editdescription", text="", icon="GREASEPENCIL"
        ).module_name = self.module_name

    def execute(self, context):
        return {"FINISHED"}

    def invoke(self, context, event):
        self.desc = addon_utils.module_bl_info(
            [a for a in addon_utils.modules() if a.__name__ == self.module_name][0]
        )["description"]
        if preferences().addon_desc_info.find(self.module_name) >= 0:
            self.desc = (
                preferences()
                .addon_desc_info[preferences().addon_desc_info.find(self.module_name)]
                .desc
            )
        return context.window_manager.invoke_popup(
            self, width=550 if len(self.desc) > 70 else 300
        )


class PAP_Addon_Edit_Description(bpy.types.Operator):
    bl_idname = "cp.editdescription"
    bl_label = "Edit Description"
    bl_description = "Edit Info about the addon"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    module_name: bpy.props.StringProperty()

    def draw(self, context):
        layout = self.layout.row()
        layout.label(text="", icon="INFO")
        layout.prop(self.info, "desc")

    def execute(self, context):
        return {"FINISHED"}

    def invoke(self, context, event):
        if not preferences().addon_desc_info.find(self.module_name) >= 0:
            temp = preferences().addon_desc_info.add()
            temp.name = self.module_name
            temp.desc = addon_utils.module_bl_info(
                [a for a in addon_utils.modules() if a.__name__ == self.module_name][0]
            )["description"]
            self.info = temp
        else:
            self.info = preferences().addon_desc_info[
                preferences().addon_desc_info.find(self.module_name)
            ]
        return context.window_manager.invoke_props_dialog(self, width=500)


class CP_OT_Fetch_Categories(bpy.types.Operator):
    bl_idname = "cp.autocreatecategories"
    bl_label = "Fetch from Online Database"
    bl_description = "Create categories automatically by fetching from online database"

    def execute(self, context):
        fetch_categories()
        return {"FINISHED"}


def save_keymaps():
    keys = {}
    for keymap in bpy.context.window_manager.keyconfigs.user.keymaps.values():
        if keymap:
            item_dict = {}
            for item in keymap.keymap_items:
                if item.is_user_modified and item.idname not in [
                    "wm.tool_set_by_id",
                ]:
                    item_dict[item.idname] = {
                        "ctrl_ui": item.ctrl_ui,
                        "alt_ui": item.alt_ui,
                        "shift_ui": item.shift_ui,
                        "oskey_ui": item.oskey_ui,
                        "type": item.type,
                        "value": item.value,
                        "repeat": item.repeat,
                    }
            if item_dict:
                keys[keymap.name] = item_dict
    # Write keys to a json

    with open(
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "cp_keys.json"), "w+"
    ) as outfile:
        json.dump(keys, outfile, indent=4)


def read_keymaps():
    # Read it back into a dict
    loaded_keymaps = {}

    try:
        with open(
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "cp_keys.json"),
            "r",
        ) as keyfile:
            loaded_keymaps = json.load(keyfile)
    except Exception:
        pass
    for keymap in bpy.context.window_manager.keyconfigs.user.keymaps.values():
        if keymap and keymap.name in loaded_keymaps.keys():
            item_dict = loaded_keymaps[keymap.name]
            for item in keymap.keymap_items:
                # print(item_dict.keys())
                if item.idname in item_dict.keys():
                    # print(keymap.name,"loading",item,item.idname)
                    for key, value in item_dict[item.idname].items():
                        if key != "keymap":
                            setattr(item, key, value)
                            # print("set",key,value)


def save_keymaps():
    # Create a dictionary to hold keymaps for different prefixes
    addon_keymaps = {}

    for keymap in bpy.context.window_manager.keyconfigs.user.keymaps.values():
        if keymap:
            for item in keymap.keymap_items:
                addon_prefix = item.idname.split(".")[0]
                if addon_prefix not in addon_keymaps:
                    addon_keymaps[addon_prefix] = {}
                if item.is_user_modified and item.idname not in ["wm.tool_set_by_id"]:
                    # Determine the addon prefix from idname
                    # print(keymap.space_type)

                    # Create a dictionary for each modified keymap item
                    item_dict = {
                        "ctrl_ui": item.ctrl_ui,
                        "alt_ui": item.alt_ui,
                        "shift_ui": item.shift_ui,
                        "oskey_ui": item.oskey_ui,
                        "type": item.type,
                        "value": item.value,
                        "repeat": item.repeat,
                    }

                    # Add item to the respective addon keymap dictionary
                    if keymap.name not in addon_keymaps[addon_prefix]:
                        addon_keymaps[addon_prefix][keymap.name] = {}

                    addon_keymaps[addon_prefix][keymap.name][item.idname] = item_dict

    # Directory for saving keymap JSON files
    config_folder_path = Path(bpy.utils.user_resource("SCRIPTS")).parent / "config"
    keymap_dir = os.path.join(config_folder_path, "cp-keymaps")
    os.makedirs(keymap_dir, exist_ok=True)

    # Write each addon keymap dictionary to its own JSON file
    for prefix, keys in addon_keymaps.items():
        file_path = os.path.join(keymap_dir, f"{prefix}.json")
        with open(file_path, "w+") as outfile:
            json.dump(keys, outfile, indent=4)


def read_keymaps():
    config_folder_path = Path(bpy.utils.user_resource("SCRIPTS")).parent / "config"
    keymap_dir = os.path.join(config_folder_path, "cp-keymaps")
    if not os.path.exists(keymap_dir):
        return
    print("Loading keymaps from", keymap_dir)
    # Load all keymap files from the directory
    for file_name in os.listdir(keymap_dir):
        if file_name.endswith(".json"):
            file_path = os.path.join(keymap_dir, file_name)
            with open(file_path, "r") as keyfile:
                try:
                    loaded_keymaps = json.load(keyfile)
                except json.JSONDecodeError:
                    continue  # Skip file if it can't be decoded

                for (
                    keymap
                ) in bpy.context.window_manager.keyconfigs.user.keymaps.values():
                    if keymap and keymap.name in loaded_keymaps:
                        item_dict = loaded_keymaps[keymap.name]
                        if item_dict["space_type"] != keymap.space_type:
                            continue
                        for item in keymap.keymap_items:
                            if item.idname in item_dict:
                                # Apply the saved settings to the current keymap item
                                for key, value in item_dict[item.idname].items():
                                    if key != "keymap":
                                        setattr(item, key, value)


def save_keymaps():
    # Create a dictionary to hold keymaps organized by space_type
    addon_keymaps = {}

    # Populate the addon_keymaps dictionary with empty dictionaries for all names
    for keymap in bpy.context.window_manager.keyconfigs.user.keymaps.values():
        if keymap:
            name = keymap.name if keymap.name else "DEFAULT"
            if name not in addon_keymaps:
                addon_keymaps[name] = {}

            for item in keymap.keymap_items:
                addon_prefix = item.idname.split(".")[0]
                if addon_prefix not in addon_keymaps[name]:
                    addon_keymaps[name][addon_prefix] = {}

    # Fill the dictionary with user-modified keymap items
    for keymap in bpy.context.window_manager.keyconfigs.user.keymaps.values():
        if keymap:
            name = keymap.name if keymap.name else "DEFAULT"
            for item in keymap.keymap_items:
                addon_prefix = item.idname.split(".")[0]

                if item.is_user_modified and item.idname not in ["wm.tool_set_by_id"]:
                    # Create a dictionary for each modified keymap item
                    item_dict = {
                        "ctrl_ui": item.ctrl_ui,
                        "alt_ui": item.alt_ui,
                        "shift_ui": item.shift_ui,
                        "oskey_ui": item.oskey_ui,
                        "type": item.type,
                        "value": item.value,
                        "repeat": item.repeat,
                    }

                    # Add item to the respective addon keymap dictionary
                    if keymap.name not in addon_keymaps[name][addon_prefix]:
                        addon_keymaps[name][addon_prefix][keymap.name] = {}

                    addon_keymaps[name][addon_prefix][keymap.name][item.idname] = (
                        item_dict
                    )

    # Directory for saving keymap JSON files
    config_folder_path = Path(bpy.utils.user_resource("SCRIPTS")).parent / "config"
    keymap_dir = os.path.join(config_folder_path, "cp-keymaps")

    # Save each addon keymap in its respective space type folder
    for name, prefixes in addon_keymaps.items():
        name_dir = os.path.join(keymap_dir, name.replace(",", "___").replace(":", "--"))
        os.makedirs(name_dir, exist_ok=True)

        for prefix, keys in prefixes.items():
            # Save the keymap dictionary to a JSON file, even if it's empty
            file_path = os.path.join(name_dir, f"{prefix}.json")
            with open(file_path, "w+") as outfile:
                json.dump(keys, outfile, indent=4)


def read_keymaps():
    config_folder_path = Path(bpy.utils.user_resource("SCRIPTS")).parent / "config"
    keymap_dir = os.path.join(config_folder_path, "cp-keymaps")
    if not os.path.exists(keymap_dir):
        return
    print("Loading keymaps from", keymap_dir)

    # Load all keymap files from the directory
    for name_folder in os.listdir(keymap_dir):
        name_dir = os.path.join(keymap_dir, name_folder)
        if not os.path.isdir(name_dir):
            continue

        for file_name in os.listdir(name_dir):
            if file_name.endswith(".json"):
                file_path = os.path.join(name_dir, file_name)
                with open(file_path, "r") as keyfile:
                    try:
                        loaded_keymaps = json.load(keyfile)
                    except json.JSONDecodeError:
                        continue  # Skip file if it can't be decoded

                    for (
                        keymap
                    ) in bpy.context.window_manager.keyconfigs.user.keymaps.values():
                        if keymap and keymap.name in loaded_keymaps:
                            item_dict = loaded_keymaps[keymap.name]
                            if (
                                name_folder.replace("___", ",").replace("--", ":")
                                != keymap.name
                            ):
                                continue
                            for item in keymap.keymap_items:
                                if item.idname in item_dict:
                                    # Apply the saved settings to the current keymap item
                                    for key, value in item_dict[item.idname].items():
                                        if key != "keymap":
                                            setattr(item, key, value)


def save_keymaps():
    # Create a dictionary to hold keymaps organized by space_type
    addon_keymaps = {}

    # Populate the addon_keymaps dictionary with empty dictionaries for all names
    for keymap in bpy.context.window_manager.keyconfigs.user.keymaps.values():
        if keymap:
            name = keymap.name if keymap.name else "DEFAULT"
            if name not in addon_keymaps:
                addon_keymaps[name] = {}

            for item in keymap.keymap_items:
                addon_prefix = item.idname.split(".")[0]
                if addon_prefix not in addon_keymaps[name]:
                    addon_keymaps[name][addon_prefix] = {}
    # Fill the dictionary with user-modified keymap items
    for keymap in bpy.context.window_manager.keyconfigs.user.keymaps.values():
        if keymap:
            name = keymap.name if keymap.name else "DEFAULT"
            for item in keymap.keymap_items:
                addon_prefix = item.idname.split(".")[0]

                if item.is_user_modified and item.idname not in ["wm.tool_set_by_id"]:
                    # Create a dictionary for each modified keymap item
                    item_dict = {
                        "ctrl_ui": item.ctrl_ui,
                        "alt_ui": item.alt_ui,
                        "shift_ui": item.shift_ui,
                        "oskey_ui": item.oskey_ui,
                        "type": item.type,
                        "value": item.value,
                        "repeat": item.repeat,
                    }
                    try:
                        json.dumps(
                            {k: item.properties[k] for k in item.properties.keys()}
                        )
                        item_dict["properties"] = {
                            k: item.properties[k] for k in item.properties.keys()
                        }
                    except Exception as e:
                        # Log the error if needed, here we just omit properties
                        print(f"Skipping properties for item {item.idname}: {e}")
                    # Add item to the respective addon keymap dictionary
                    if keymap.name not in addon_keymaps[name][addon_prefix]:
                        addon_keymaps[name][addon_prefix][keymap.name] = {}

                    # Store items in a list to handle multiple items with the same idname
                    if (
                        item.idname
                        not in addon_keymaps[name][addon_prefix][keymap.name]
                    ):
                        addon_keymaps[name][addon_prefix][keymap.name][item.idname] = []

                    # Append the item dictionary to the list
                    addon_keymaps[name][addon_prefix][keymap.name][item.idname].append(
                        item_dict
                    )

    # Directory for saving keymap JSON files
    config_folder_path = Path(bpy.utils.user_resource("SCRIPTS")).parent / "config"
    keymap_dir = os.path.join(config_folder_path, "cp-keymaps")

    # Save each addon keymap in its respective space type folder
    for name, prefixes in addon_keymaps.items():
        name_dir = os.path.join(keymap_dir, name.replace(",", "___").replace(":", "--"))
        os.makedirs(name_dir, exist_ok=True)

        for prefix, keys in prefixes.items():
            # Save the keymap dictionary to a JSON file, even if it's empty
            file_path = os.path.join(name_dir, f"{prefix}.json")
            try:
                with open(file_path, "w+") as outfile:
                    json.dump(keys, outfile, indent=4)
            except Exception as e:
                pass
                print("ERROR", keys)


def read_keymaps():
    config_folder_path = Path(bpy.utils.user_resource("SCRIPTS")).parent / "config"
    keymap_dir = os.path.join(config_folder_path, "cp-keymaps")
    if not os.path.exists(keymap_dir):
        return
    # print("Loading keymaps from", keymap_dir)

    # Load all keymap files from the directory
    for name_folder in os.listdir(keymap_dir):
        name_dir = os.path.join(keymap_dir, name_folder)
        if not os.path.isdir(name_dir):
            continue

        for file_name in os.listdir(name_dir):
            if file_name.endswith(".json"):
                file_path = os.path.join(name_dir, file_name)
                with open(file_path, "r") as keyfile:
                    try:
                        loaded_keymaps = json.load(keyfile)
                    except json.JSONDecodeError:
                        continue  # Skip file if it can't be decoded

                    for (
                        keymap
                    ) in bpy.context.window_manager.keyconfigs.user.keymaps.values():
                        if keymap and keymap.name in loaded_keymaps:
                            item_dict = loaded_keymaps[keymap.name]
                            if (
                                name_folder.replace("___", ",").replace("--", ":")
                                != keymap.name
                            ):
                                continue
                            for item in keymap.keymap_items:
                                if (
                                    item.idname in item_dict
                                    and not item.idname.startswith("cp.")
                                ):
                                    # Iterate over the list of saved keymap items
                                    for saved_item in item_dict[item.idname]:
                                        # Match based on item.properties as well
                                        if "properties" in saved_item:
                                            if saved_item["properties"] == {
                                                k: item.properties[k]
                                                for k in item.properties.keys()
                                            }:
                                                # Apply the saved settings to the current keymap item
                                                for key, value in saved_item.items():
                                                    if key not in [
                                                        "keymap",
                                                        "properties",
                                                    ]:
                                                        setattr(item, key, value)
                                        else:
                                            # If properties are missing, apply settings regardless
                                            for key, value in saved_item.items():
                                                if key not in ["keymap", "properties"]:
                                                    setattr(item, key, value)


class CP_OT_SaveKeyMap(bpy.types.Operator):
    bl_idname = "cp.savekeymap"
    bl_label = "Save Keymap"
    bl_description = "Save keymap to load when using Delayed addon loading"

    def invoke(self, context, event):
        if event.ctrl:
            # pass
            read_keymaps()
        else:
            save_keymaps()
        # read_keymaps()
        return {"FINISHED"}


class CP_OT_AutoSetup(bpy.types.Operator):
    bl_idname = "cp.autosetup"
    bl_label = "Magic Setup"
    bl_description = "Automatically create filtering categories from inbuilt database"
    is_guide: bpy.props.BoolProperty(default=False, options={"SKIP_SAVE"})
    update_database: bpy.props.BoolProperty(
        default=False,
        name="Fetch Latest Database",
        description="Fetch and update the local database with the latest version from the online database",
        options={"SKIP_SAVE"},
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "update_database")

    def execute(self, context):
        if self.update_database:
            try:
                update_cp_database()
            except Exception:
                pass

        self.space = ""
        addons = get_addons_for_atl(self, context)
        self.addons = addons
        all_categorized_addons = []
        for a in preferences().workspace_categories:
            all_categorized_addons.extend(split_keep_substring(a.panels))
        all_categorized_addons = (
            split_keep_substring(preferences().addons_to_exclude)
            + all_categorized_addons
        )
        for a in addons:
            if a[1] not in ("All", "Unfiltered") and a[1] not in all_categorized_addons:
                assign_addon_to_category(a[1])
        # bpy.ops.cp.fpcategoriesfromfiltering()
        if self.is_guide:
            from .guide_ops import cp_guides

            cp_guides.preferences.set_page(9)
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


def get_categories_enum(self, context):
    pcoll = icon_collection["icons"]
    if self.type == "Workspace":
        categories = getattr(preferences(), f"workspace_categories{self.space}")
        return [
            ("Skip", "Skip", "Skip", "NONE", 0),
            ("Exclude", "Exclude", "Exclude", "HANDLETYPE_AUTO_CLAMP_VEC", 1),
        ] + [
            (
                a.name,
                a.name,
                a.name,
                pcoll[a.icon].icon_id if a.icon not in ALL_ICONS else a.icon,
                i + 2,
            )
            for i, a in enumerate(categories)
        ]
    elif self.type == "AddonLoading":
        categories = getattr(preferences(), f"addon_loading_categories")
        return [
            ("Skip", "Skip", "Skip"),
            ("Exclude", "Exclude", "Exclude"),
        ] + [(a.name, a.name, a.name) for i, a in enumerate(categories)]
    else:
        categories = getattr(preferences(), f"focus_panel_categories{self.space}")
        return [
            ("Skip", "Skip", "Skip"),
        ] + [(a.name, a.name, a.name) for i, a in enumerate(categories)]


class BatchAssign(bpy.types.PropertyGroup):
    type: bpy.props.StringProperty()
    space: bpy.props.StringProperty()
    addon: bpy.props.StringProperty()
    category: bpy.props.EnumProperty(items=get_categories_enum, name="Category")


class CP_OT_BatchAssignCategories(bpy.types.Operator):
    bl_idname = "cp.batchassigncategories"
    bl_label = "Batch Assign Categories"
    bl_description = "Batch Assign Categories to Addons"
    batch_asign: bpy.props.CollectionProperty(type=BatchAssign)
    category: bpy.props.StringProperty(default="Workspace", options={"SKIP_SAVE"})
    index: bpy.props.IntProperty(default=122, options={"SKIP_SAVE"})

    def draw(self, context):
        layout = self.layout
        column = layout.column()
        if self.batch_asign:
            column.label(
                text=f"Uncategorized {'Addons' if self.category in {'Workspace','AddonLoading'} else 'Tabs'}:"
            )
        else:
            column.label(
                text=f"No Uncategorized {'Addons' if self.category in {'Workspace','AddonLoading'} else 'Tabs'}"
            )
        for a in self.batch_asign:
            row = column.row(align=True)
            row.label(text=a.addon)
            row.prop(a, "category", text="")

    def execute(self, context):
        for a in self.batch_asign:
            if self.category == "Workspace":
                if a.category == "Exclude":
                    setattr(
                        preferences(),
                        f"addons_to_exclude{self.space}",
                        ",".join(
                            split_keep_substring(
                                getattr(preferences(), f"addons_to_exclude{self.space}")
                            )
                            + [
                                a.addon,
                            ]
                        ),
                    )
                elif a.category == "Skip":
                    pass
                else:
                    getattr(preferences(), f"workspace_categories{self.space}")[
                        a.category
                    ].panels = ",".join(
                        split_keep_substring(
                            getattr(preferences(), f"workspace_categories{self.space}")[
                                a.category
                            ].panels
                        )
                        + [
                            a.addon,
                        ]
                    )
            elif self.category == "FP":
                if a.category == "Skip":
                    pass
                else:
                    getattr(preferences(), f"focus_panel_categories{self.space}")[
                        a.category
                    ].panels = ",".join(
                        split_keep_substring(
                            getattr(
                                preferences(), f"focus_panel_categories{self.space}"
                            )[a.category].panels
                        )
                        + [
                            a.addon,
                        ]
                    )
            elif self.category == "AddonLoading":
                if a.category == "Exclude":
                    preferences().atl_list = ",".join(
                        split_keep_substring(preferences().atl_list)
                        + [
                            a.addon,
                        ]
                    )
                elif a.category == "Skip":
                    pass
                else:
                    preferences().addon_loading_categories[
                        a.category
                    ].panels = ",".join(
                        split_keep_substring(
                            preferences().addon_loading_categories[a.category].panels
                        )
                        + [
                            a.addon,
                        ]
                    )
        return {"FINISHED"}

    def invoke(self, context, event):
        self.space = get_active_space()
        uncategorized_addons = []
        if self.category == "Workspace":
            addons = get_addons_for_atl(self, context)
            all_categorized_addons = []
            for a in getattr(preferences(), f"workspace_categories{self.space}"):
                all_categorized_addons.extend(split_keep_substring(a.panels))
            all_categorized_addons = (
                split_keep_substring(
                    getattr(preferences(), f"addons_to_exclude{self.space}")
                )
                + all_categorized_addons
            )
            for a in addons:
                if (
                    a[1] not in ("All", "Unfiltered")
                    and a[1] not in all_categorized_addons
                ):
                    uncategorized_addons.append(a[1])
        elif self.category == "FP":
            addons = get_panel_categories(self, context)
            all_categorized_addons = []
            for a in getattr(preferences(), f"focus_panel_categories{self.space}"):
                all_categorized_addons.extend(split_keep_substring(a.panels))
            for a in addons:
                if a[1] not in all_categorized_addons:
                    uncategorized_addons.append(a[1])
        elif self.category == "AddonLoading":
            addons = get_addons_for_atl(self, context)
            all_categorized_addons = []
            for a in getattr(preferences(), f"addon_loading_categories"):
                all_categorized_addons.extend(split_keep_substring(a.panels))
            all_categorized_addons = (
                split_keep_substring(preferences().atl_list) + all_categorized_addons
            )
            for a in addons:
                if a[1] not in all_categorized_addons:
                    uncategorized_addons.append(a[1])
        self.addons = addons
        self.batch_asign.clear()
        if self.category == "Workspace":
            space_categories = [
                a.name
                for a in getattr(preferences(), f"workspace_categories{self.space}")
            ]
        elif self.category == "FP":
            space_categories = [
                a.name
                for a in getattr(preferences(), f"focus_panel_categories{self.space}")
            ]
        elif self.category == "AddonLoading":
            space_categories = [
                a.name for a in getattr(preferences(), "addon_loading_categories")
            ]
        for addon in uncategorized_addons:
            t = self.batch_asign.add()
            t.addon = addon
            t.space = self.space
            t.type = self.category
            guessed_category = assign_addon_to_category(
                addon
                if self.category in {"AddonLoading", "Workspace"}
                else get_addon_name_from_tab_name(addon, self.space),
                True,
            )
            t.category = (
                guessed_category
                if self.category in {"AddonLoading", "Workspace"}
                and guessed_category
                and guessed_category in space_categories
                else "Skip"
            )
        return context.window_manager.invoke_props_dialog(self)
        # read_keymaps()


class CP_OT_EditFavoriteFocusPanel(bpy.types.Operator):
    bl_idname = "cp.edit_favorite_focus_panel"
    bl_label = "Edit Favorite Focus Panel"
    bl_description = "Edit the favorite focus panel"
    bl_property = "my_enum"
    my_enum: bpy.props.EnumProperty(
        name="Panel", description="", items=get_panel_categories_for_favorites
    )
    index: bpy.props.IntProperty(default=0)

    def execute(self, context):
        preferences().favorites[self.index].name = self.my_enum
        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {"FINISHED"}


class CP_OT_Remove_FavoriteFocusPanel(bpy.types.Operator):
    bl_idname = "cp.remove_favorite_focus_panel"
    bl_label = "Remove Favorite Focus Panel"
    bl_description = "Remove the favorite focus panel"

    def execute(self, context):
        preferences().favorites.remove(preferences().favorites_index)
        preferences().favorites_index = max(0, preferences().favorites_index - 1)
        return {"FINISHED"}


class CP_OT_Add_FavoriteFocusPanel(bpy.types.Operator):
    bl_idname = "cp.add_favorite_focus_panel"
    bl_label = "Add Favorite Focus Panel"
    bl_description = "Add a favorite focus panel"
    bl_property = "my_enum"
    my_enum: bpy.props.EnumProperty(
        name="Panel", description="", items=get_panel_categories_for_favorites
    )

    def execute(self, context):
        t = preferences().favorites.add()
        t.name = self.my_enum
        preferences().favorites_index = len(preferences().favorites) - 1
        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {"FINISHED"}


class CP_OT_Reorder_Favorites(bpy.types.Operator):
    bl_idname = "cp.reorder_favorites"
    bl_label = "Reorder Favorites"
    direction: bpy.props.StringProperty(default="UP", options={"SKIP_SAVE", "HIDDEN"})

    @classmethod
    def description(cls, context, properties):
        if properties.direction == "UP":
            return "Move Up"
        else:
            return "Move Down"

    def execute(self, context):
        if self.direction == "DOWN":
            new_index = min(
                len(preferences().favorites) - 1, preferences().favorites_index + 1
            )
        else:
            new_index = max(0, preferences().favorites_index - 1)
        preferences().favorites.move(preferences().favorites_index, new_index)
        preferences().favorites_index = new_index
        return {"FINISHED"}


class CP_OT_Update_Database(bpy.types.Operator):
    bl_idname = "cp.updatedatabase"
    bl_label = "Fetch Latest Database"
    bl_description = "Update the local database with the latest version from the online database. This is used to make smart guesses for assigning categories to addons"

    def execute(self, context):
        update_cp_database()
        return {"FINISHED"}
