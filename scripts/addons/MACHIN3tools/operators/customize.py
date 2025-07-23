import bpy

import os
import shutil

from .. utils.application import delay_execution
from .. utils.registration import get_addon_prefs, get_prefs, enable_addon
from .. utils.system import makedir
from .. utils.ui import get_scale, kmi_to_string, get_keymap_item
from .. utils.view import reset_viewport

from .. import MACHIN3toolsManager as M3

class Customize(bpy.types.Operator):
    bl_idname = "machin3.customize"
    bl_label = "MACHIN3: Customize"
    bl_description = "Customize various Blender preferences, settings and keymaps."
    bl_options = {'INTERNAL'}

    def invoke(self, context, event):
        scriptspath = bpy.utils.user_resource('SCRIPTS')
        datafilespath = bpy.utils.user_resource('DATAFILES')

        resourcespath = os.path.join(get_prefs().path, "resources")

        if not any([event.alt, event.ctrl]):

            self.preferences(context)

            if get_prefs().custom_theme:
                self.theme(scriptspath, resourcespath)

            if get_prefs().custom_matcaps:
                self.matcaps(context, resourcespath, datafilespath)

            if get_prefs().custom_shading:
                self.shading(context)

            if get_prefs().custom_overlays:
                self.overlays(context)

            if get_prefs().custom_outliner:
                self.outliner(context)

            if get_prefs().custom_startup:
                self.startup(context)

        else:

            if event.alt:
                self.worlds(context, resourcespath, datafilespath)

                self.bookmarks(context)

                self.asset_library(context)

                self.customize_my_own_addons(context)

                self.enable_3rd_party_addons(context)

            elif event.ctrl:

                self.adjust_workspaces(context)  # remove workspaces

                self.add_workspaces(context)

        return {'FINISHED'}

    def customize_keymap(self, context):
        docs_mode = False

        if docs_mode:
            deactivated_str = "* Deactivated"
            changed_str = "* Changed"
            to_str = "    * to"
            added_str = "* Added"

        else:
            deactivated_str = "  Deactivated"
            changed_str = "  Changed"
            to_str = "       to"
            added_str = "  Added"

        def print_keymap_title(km):
            if docs_mode:
                print(f"\n\n#### {km.name} Keymap\n")

            else:
                print(f"\n {km.name} Keymap")

        def modify_keymaps(kc):

            km = kc.keymaps.get("Window")
            print_keymap_title(km)

            for kmi in km.keymap_items:
                if kmi.idname == "wm.open_mainfile":
                    print(deactivated_str, kmi_to_string(kmi, docs_mode=docs_mode))
                    kmi.active = False

                if kmi.idname == "wm.doc_view_manual_ui_context":
                    print(deactivated_str, kmi_to_string(kmi, docs_mode=docs_mode))
                    kmi.active = False

                if kmi.idname == "wm.save_as_mainfile":
                    print(deactivated_str, kmi_to_string(kmi, docs_mode=docs_mode))
                    kmi.active = False

                if kmi.idname == "screen.space_type_set_or_cycle":
                    print(deactivated_str, kmi_to_string(kmi, docs_mode=docs_mode))
                    kmi.active = False

            km = kc.keymaps.get("Screen")
            print_keymap_title(km)

            for kmi in km.keymap_items:
                if kmi.idname == "ed.undo":
                    print(changed_str, kmi_to_string(kmi, docs_mode=docs_mode))
                    kmi.type = "F1"
                    kmi.ctrl = False
                    print(to_str, kmi_to_string(kmi, docs_mode=docs_mode))

                if kmi.idname == "ed.redo":
                    print(changed_str, kmi_to_string(kmi, docs_mode=docs_mode))
                    kmi.type = "F2"
                    kmi.ctrl = False
                    kmi.shift = False
                    print(to_str, kmi_to_string(kmi, docs_mode=docs_mode))

                if kmi.idname == "ed.undo_history":
                    print(changed_str, kmi_to_string(kmi, docs_mode=docs_mode))
                    kmi.type = "F1"
                    kmi.ctrl = False
                    kmi.alt = True
                    print(to_str, kmi_to_string(kmi, docs_mode=docs_mode))

                if kmi.idname == "screen.redo_last":
                    print(changed_str, kmi_to_string(kmi, docs_mode=docs_mode))
                    kmi.type = "BUTTON4MOUSE"
                    print(to_str, kmi_to_string(kmi, docs_mode=docs_mode))

                if kmi.idname == "screen.repeat_history":
                    print(changed_str, kmi_to_string(kmi, docs_mode=docs_mode))
                    kmi.ctrl = False
                    kmi.shift = True
                    print(to_str, kmi_to_string(kmi, docs_mode=docs_mode))

                if kmi.idname == "screen.screen_full_area":
                    print(deactivated_str, kmi_to_string(kmi, docs_mode=docs_mode))
                    kmi.active = False

                if kmi.idname == "render.render":
                    print(deactivated_str, kmi_to_string(kmi, docs_mode=docs_mode))
                    kmi.active = False

            km = kc.keymaps.get("Screen Editing")
            print_keymap_title(km)

            for kmi in km.keymap_items:
                if kmi.idname == "screen.screen_full_area":
                    if kmi.properties.use_hide_panels:
                        print(changed_str, kmi_to_string(kmi, docs_mode=docs_mode))
                        kmi.shift = True
                        kmi.alt = False
                        kmi.ctrl = False
                        kmi.type = 'SPACE'
                        kmi.value = 'PRESS'
                        print(to_str, kmi_to_string(kmi, docs_mode=docs_mode))

                    else:
                        print(deactivated_str, kmi_to_string(kmi, docs_mode=docs_mode))
                        kmi.active = False

            km = kc.keymaps.get("User Interface")
            print_keymap_title(km)

            for kmi in km.keymap_items:
                if kmi.idname == "ui.reset_default_button":
                    if kmi.type == 'BACK_SPACE':
                        print(changed_str, kmi_to_string(kmi, docs_mode=docs_mode))
                        kmi.map_type = 'MOUSE'
                        kmi.type = 'MIDDLEMOUSE'
                        kmi.properties.all = False
                        print(to_str, kmi_to_string(kmi, docs_mode=docs_mode))

            km = kc.keymaps.get("Frames")
            print_keymap_title(km)

            for kmi in km.keymap_items:
                if kmi.idname == "screen.animation_play":
                    print(deactivated_str, kmi_to_string(kmi, docs_mode=docs_mode))
                    kmi.active = False

            km = kc.keymaps.get("Outliner")
            print_keymap_title(km)

            for kmi in km.keymap_items:
                if kmi.idname == "outliner.show_active":
                    if kmi.type == "PERIOD":
                        print(changed_str, kmi_to_string(kmi, docs_mode=docs_mode))
                        kmi.type = "F"
                        print(to_str, kmi_to_string(kmi, docs_mode=docs_mode))

                if kmi.idname == "outliner.start_filter":
                    print(changed_str, kmi_to_string(kmi, docs_mode=docs_mode))
                    kmi.type = 'SLASH'
                    kmi.ctrl = False
                    print(to_str, kmi_to_string(kmi, docs_mode=docs_mode))

            km = kc.keymaps.get("3D View")
            print_keymap_title(km)

            for kmi in km.keymap_items:
                if kmi.idname == "view3d.view_selected":

                    if kmi.type == "NDOF_BUTTON_FIT":
                        print(changed_str, kmi_to_string(kmi, docs_mode=docs_mode))
                        kmi.type = "NDOF_BUTTON_1"
                        kmi.idname = "view3d.view_center_pick"
                        print(to_str, kmi_to_string(kmi, docs_mode=docs_mode))

                    if kmi.type == "NUMPAD_PERIOD" and not kmi.properties.use_all_regions:
                        print(changed_str, kmi_to_string(kmi, docs_mode=docs_mode))
                        kmi.type = "F"
                        print(to_str, kmi_to_string(kmi, docs_mode=docs_mode))

                if kmi.idname == "view3d.cursor3d":
                    print(changed_str, kmi_to_string(kmi, docs_mode=docs_mode))
                    kmi.type = "RIGHTMOUSE"
                    kmi.alt = True
                    kmi.shift = False
                    kmi.properties.orientation = "GEOM"
                    print(to_str, kmi_to_string(kmi, docs_mode=docs_mode))

                if kmi.idname == "view3d.select":
                    if kmi.value == "CLICK":
                        if not any([getattr(kmi.properties, name, False) for name in ["extend", "deselect", "toggle", "center", "enumerate", "object"]]):
                            print(changed_str, kmi_to_string(kmi, docs_mode=docs_mode))
                            kmi.value = "PRESS"
                            print(to_str, kmi_to_string(kmi, docs_mode=docs_mode))

                        elif kmi.properties.toggle and not any([getattr(kmi.properties, name, False) for name in ["extend", "deselect", "center", "enumerate", "object"]]):
                            print(changed_str, kmi_to_string(kmi, docs_mode=docs_mode))
                            kmi.value = "PRESS"
                            print(to_str, kmi_to_string(kmi, docs_mode=docs_mode))

                        elif kmi.properties.enumerate and not any([getattr(kmi.properties, name, False) for name in ["extend", "deselect", "toggle", "center", "object"]]):
                            print(changed_str, kmi_to_string(kmi, docs_mode=docs_mode))
                            kmi.value = "PRESS"
                            print(to_str, kmi_to_string(kmi, docs_mode=docs_mode))

                        else:
                            print(deactivated_str, kmi_to_string(kmi, docs_mode=docs_mode))
                            kmi.active = False

                if kmi.idname == "view3d.zoom_border":
                    print(deactivated_str, kmi_to_string(kmi, docs_mode=docs_mode))
                    kmi.active = False

                if kmi.idname == "view3d.view_axis":
                    if kmi.map_type == "MOUSE" and kmi.value == 'CLICK_DRAG':
                        print(deactivated_str, kmi_to_string(kmi, docs_mode=docs_mode))
                        kmi.active = False

                if kmi.idname == "transform.tosphere":
                    print(changed_str, kmi_to_string(kmi, docs_mode=docs_mode))
                    kmi.properties.value = 1
                    print(to_str, kmi_to_string(kmi, docs_mode=docs_mode))

                if kmi.idname == "transform.translate":
                    if kmi.map_type == "MOUSE" and kmi.value == 'CLICK_DRAG':
                        print(deactivated_str, kmi_to_string(kmi, docs_mode=docs_mode))
                        kmi.active = False

                if kmi.idname == "transform.translate":
                    if kmi.properties.texture_space:
                        print(deactivated_str, kmi_to_string(kmi, docs_mode=docs_mode))
                        kmi.active = False

            km = kc.keymaps.get("Object Mode")
            print_keymap_title(km)

            for kmi in km.keymap_items:

                if kmi.idname == "object.delete":
                    if kmi.type == "X" and kmi.shift:
                        print(deactivated_str, kmi_to_string(kmi, docs_mode=docs_mode))
                        kmi.active = False

                    elif kmi.type == "DEL":
                        print(deactivated_str, kmi_to_string(kmi, docs_mode=docs_mode))
                        kmi.active = False

                elif kmi.idname == "object.move_to_collection":
                    if kmi.type == "M":
                        print(deactivated_str, kmi_to_string(kmi, docs_mode=docs_mode))
                        kmi.active = False

                elif kmi.idname == "object.link_to_collection":
                    if kmi.type == "M" and kmi.shift:
                        print(deactivated_str, kmi_to_string(kmi, docs_mode=docs_mode))
                        kmi.active = False

                elif kmi.idname == "object.select_hierarchy":
                    if kmi.type == "LEFT_BRACKET" and kmi.properties.direction == 'PARENT' and not kmi.properties.extend:
                        print(changed_str, kmi_to_string(kmi, docs_mode=docs_mode))
                        kmi.type = 'UP_ARROW'
                        print(to_str, kmi_to_string(kmi, docs_mode=docs_mode))

                    elif kmi.type == "RIGHT_BRACKET" and kmi.properties.direction == 'CHILD' and not kmi.properties.extend:
                        print(changed_str, kmi_to_string(kmi, docs_mode=docs_mode))
                        kmi.type = 'DOWN_ARROW'
                        print(to_str, kmi_to_string(kmi, docs_mode=docs_mode))

                elif kmi.idname == "object.hide_collection":
                    print(deactivated_str, kmi_to_string(kmi, docs_mode=docs_mode))
                    kmi.active = False

            km = kc.keymaps.get("Object Non-modal")
            print_keymap_title(km)

            for kmi in km.keymap_items:
                if kmi.idname == "object.mode_set":
                    print(deactivated_str, kmi_to_string(kmi, docs_mode=docs_mode))
                    kmi.active = False

                if kmi.idname == "view3d.object_mode_pie_or_toggle":
                    print(deactivated_str, kmi_to_string(kmi, docs_mode=docs_mode))
                    kmi.active = False

            km = kc.keymaps.get("Image")
            print_keymap_title(km)

            for kmi in km.keymap_items:
                if kmi.idname == "object.mode_set":
                    print(deactivated_str, kmi_to_string(kmi, docs_mode=docs_mode))
                    kmi.active = False

                if kmi.idname == "image.view_selected":
                    if kmi.type == "NUMPAD_PERIOD":
                        print(changed_str, kmi_to_string(kmi, docs_mode=docs_mode))
                        kmi.type = "F"
                        print(to_str, kmi_to_string(kmi, docs_mode=docs_mode))

            km = kc.keymaps.get("Image Paint")
            print_keymap_title(km)

            for kmi in km.keymap_items:
                if kmi.idname == "wm.radial_control":
                    if kmi.properties.data_path_primary == "tool_settings.image_paint.brush.size":#

                        kmi.active = True

                        print(changed_str, kmi_to_string(kmi, docs_mode=docs_mode))
                        kmi.properties.release_confirm = True
                        print(to_str, kmi_to_string(kmi, docs_mode=docs_mode))

            km = kc.keymaps.get("Mesh")
            print_keymap_title(km)

            for kmi in km.keymap_items:

                if kmi.idname == "mesh.bevel":
                    if kmi.properties.affect == "EDGES":
                        print(changed_str, kmi_to_string(kmi, docs_mode=docs_mode))
                        kmi.properties.offset_type = 'OFFSET'
                        kmi.properties.profile = 0.6
                        print(to_str, kmi_to_string(kmi, docs_mode=docs_mode))

                    elif kmi.properties.affect == "VERTICES":
                        print(changed_str, kmi_to_string(kmi, docs_mode=docs_mode))
                        kmi.properties.affect = "EDGES"
                        kmi.properties.offset_type = 'PERCENT'
                        kmi.properties.profile = 0.6
                        print(to_str, kmi_to_string(kmi, docs_mode=docs_mode))

                if kmi.idname == "wm.call_menu":
                    if kmi.properties.name == "VIEW3D_MT_edit_mesh_select_mode":
                        print(deactivated_str, kmi_to_string(kmi, docs_mode=docs_mode))
                        kmi.active = False

                if kmi.idname == "mesh.fill":
                    print(deactivated_str, kmi_to_string(kmi, docs_mode=docs_mode))
                    kmi.active = False

                if kmi.idname == "mesh.edge_face_add" and kmi.type == "F":
                    print(deactivated_str, kmi_to_string(kmi, docs_mode=docs_mode))
                    kmi.active = False

                if kmi.idname == "mesh.loop_select":
                    if not any([getattr(kmi.properties, name, False) for name in ["extend", "deselect", "toggle", "ring"]]):
                        print(deactivated_str, kmi_to_string(kmi, docs_mode=docs_mode))
                        kmi.active = False

                    elif kmi.properties.toggle:
                        print(changed_str, kmi_to_string(kmi, docs_mode=docs_mode))
                        kmi.value = "PRESS"
                        kmi.shift = False
                        print(to_str, kmi_to_string(kmi, docs_mode=docs_mode))

                if kmi.idname == "mesh.edgering_select":
                    if kmi.properties.ring and not any([getattr(kmi.properties, name, False) for name in ["extend", "deselect", "toggle"]]):
                        print(deactivated_str, kmi_to_string(kmi, docs_mode=docs_mode))
                        kmi.active = False

                    elif kmi.properties.toggle:
                        print(changed_str, kmi_to_string(kmi, docs_mode=docs_mode))
                        kmi.value = "CLICK"
                        kmi.shift = False
                        print(to_str, kmi_to_string(kmi, docs_mode=docs_mode))

                if kmi.idname == "mesh.shortest_path_pick":
                    print(changed_str, kmi_to_string(kmi, docs_mode=docs_mode))
                    kmi.value = "PRESS"
                    print(to_str, kmi_to_string(kmi, docs_mode=docs_mode))

                if kmi.idname == "mesh.select_more":
                    print(changed_str, kmi_to_string(kmi, docs_mode=docs_mode))
                    kmi.type = "WHEELUPMOUSE"
                    kmi.shift = True
                    kmi.ctrl = False
                    print(to_str, kmi_to_string(kmi, docs_mode=docs_mode))

                if kmi.idname == "mesh.select_less":
                    print(changed_str, kmi_to_string(kmi, docs_mode=docs_mode))
                    kmi.type = "WHEELDOWNMOUSE"
                    kmi.shift = True
                    kmi.ctrl = False
                    print(to_str, kmi_to_string(kmi, docs_mode=docs_mode))

                if kmi.idname == "mesh.select_next_item":
                    print(changed_str, kmi_to_string(kmi, docs_mode=docs_mode))
                    kmi.type = "WHEELUPMOUSE"
                    kmi.shift = False
                    print(to_str, kmi_to_string(kmi, docs_mode=docs_mode))

                if kmi.idname == "mesh.select_prev_item":
                    print(changed_str, kmi_to_string(kmi, docs_mode=docs_mode))
                    kmi.type = "WHEELDOWNMOUSE"
                    kmi.shift = False
                    print(to_str, kmi_to_string(kmi, docs_mode=docs_mode))

                if kmi.idname == "mesh.select_linked":
                    print(changed_str, kmi_to_string(kmi, docs_mode=docs_mode))
                    kmi.type = "LEFTMOUSE"
                    kmi.value = "DOUBLE_CLICK"
                    kmi.ctrl = False
                    kmi.shift = True
                    kmi.properties.delimit = {'MATERIAL', 'SEAM', 'SHARP'}
                    print(to_str, kmi_to_string(kmi, docs_mode=docs_mode))

                if kmi.idname == "mesh.select_linked_pick":
                    if kmi.properties.deselect:
                        print(changed_str, kmi_to_string(kmi, docs_mode=docs_mode))
                        kmi.type = "LEFTMOUSE"
                        kmi.value = "DOUBLE_CLICK"
                        kmi.alt = True
                        kmi.properties.delimit = {'MATERIAL', 'SEAM', 'SHARP'}
                        print(to_str, kmi_to_string(kmi, docs_mode=docs_mode))

                    else:
                        print(deactivated_str, kmi_to_string(kmi, docs_mode=docs_mode))
                        kmi.active = False

                if kmi.idname == "object.subdivision_set":
                    print(deactivated_str, kmi_to_string(kmi, docs_mode=docs_mode))
                    kmi.active = False

                if kmi.idname == "wm.call_menu":
                    if kmi.properties.name == "VIEW3D_MT_edit_mesh_merge":
                        print(deactivated_str, kmi_to_string(kmi, docs_mode=docs_mode))
                        kmi.active = False

                if kmi.idname == "wm.call_menu":
                    if kmi.properties.name == "VIEW3D_MT_edit_mesh_split":
                        print(deactivated_str, kmi_to_string(kmi, docs_mode=docs_mode))
                        kmi.active = False

            km = kc.keymaps.get("Sculpt")
            print_keymap_title(km)

            for kmi in km.keymap_items:

                if kmi.idname == "paint.visibility_filter":
                    if kmi.type in ['PAGE_UP', 'PAGE_DOWN']:
                        print(changed_str, kmi_to_string(kmi, docs_mode=docs_mode))
                        kmi.shift = True
                        print(to_str, kmi_to_string(kmi, docs_mode=docs_mode))

                elif kmi.idname == "wm.radial_control":
                    if kmi.properties.data_path_primary == "tool_settings.sculpt.brush.size":

                        kmi.active = True

                        print(changed_str, kmi_to_string(kmi, docs_mode=docs_mode))
                        kmi.properties.release_confirm = True
                        print(to_str, kmi_to_string(kmi, docs_mode=docs_mode))

            km = kc.keymaps.get("Curve")
            print_keymap_title(km)

            for kmi in km.keymap_items:
                if kmi.idname == "curve.make_segment" and kmi.type == 'F':
                    print(deactivated_str, kmi_to_string(kmi, docs_mode=docs_mode))
                    kmi.active = False

                if kmi.idname == "curve.select_linked" and kmi.type == 'L':
                    print(changed_str, kmi_to_string(kmi, docs_mode=docs_mode))
                    kmi.type = "LEFTMOUSE"
                    kmi.value = "DOUBLE_CLICK"
                    kmi.ctrl = False
                    kmi.shift = True
                    print(to_str, kmi_to_string(kmi, docs_mode=docs_mode))

                if kmi.idname == "curve.select_more":
                    print(changed_str, kmi_to_string(kmi, docs_mode=docs_mode))
                    kmi.type = "WHEELUPMOUSE"
                    kmi.shift = True
                    kmi.ctrl = False
                    print(to_str, kmi_to_string(kmi, docs_mode=docs_mode))

                if kmi.idname == "curve.select_less":
                    print(changed_str, kmi_to_string(kmi, docs_mode=docs_mode))
                    kmi.type = "WHEELDOWNMOUSE"
                    kmi.shift = True
                    kmi.ctrl = False
                    print(to_str, kmi_to_string(kmi, docs_mode=docs_mode))

            km = kc.keymaps.get("UV Editor")
            print_keymap_title(km)

            for kmi in km.keymap_items:

                if kmi.idname == "uv.select":
                    print(changed_str, kmi_to_string(kmi, docs_mode=docs_mode))
                    kmi.value = "PRESS"
                    print(to_str, kmi_to_string(kmi, docs_mode=docs_mode))

                if kmi.idname == "uv.select_loop":
                    print(changed_str, kmi_to_string(kmi, docs_mode=docs_mode))
                    kmi.value = "PRESS"
                    print(to_str, kmi_to_string(kmi, docs_mode=docs_mode))

                if kmi.idname == "uv.select_more":
                    print(changed_str, kmi_to_string(kmi, docs_mode=docs_mode))
                    kmi.type = "WHEELUPMOUSE"
                    kmi.shift = True
                    kmi.ctrl = False
                    print(to_str, kmi_to_string(kmi, docs_mode=docs_mode))

                if kmi.idname == "uv.select_less":
                    print(changed_str, kmi_to_string(kmi, docs_mode=docs_mode))
                    kmi.type = "WHEELDOWNMOUSE"
                    kmi.shift = True
                    kmi.ctrl = False
                    print(to_str, kmi_to_string(kmi, docs_mode=docs_mode))

                if kmi.idname == "transform.translate":
                    if kmi.map_type == "MOUSE" and kmi.value == 'CLICK_DRAG':
                        print(deactivated_str, kmi_to_string(kmi, docs_mode=docs_mode))
                        kmi.active = False

                if kmi.idname == "uv.cursor_set":
                    print(changed_str, kmi_to_string(kmi, docs_mode=docs_mode))
                    kmi.alt = True
                    kmi.shift = False
                    print(to_str, kmi_to_string(kmi, docs_mode=docs_mode))

                if kmi.idname == "uv.shortest_path_pick":
                    print(changed_str, kmi_to_string(kmi, docs_mode=docs_mode))
                    kmi.value = "PRESS"
                    print(to_str, kmi_to_string(kmi, docs_mode=docs_mode))

                if kmi.idname == "uv.select_linked":
                    print(changed_str, kmi_to_string(kmi, docs_mode=docs_mode))
                    kmi.type = "LEFTMOUSE"
                    kmi.value = "DOUBLE_CLICK"
                    kmi.ctrl = False
                    kmi.shift = True
                    print(to_str, kmi_to_string(kmi, docs_mode=docs_mode))

                if kmi.idname == "uv.select_linked_pick":
                    if kmi.properties.deselect:
                        print(changed_str, kmi_to_string(kmi, docs_mode=docs_mode))
                        kmi.type = "LEFTMOUSE"
                        kmi.value = "DOUBLE_CLICK"
                        kmi.alt = True
                        print(to_str, kmi_to_string(kmi, docs_mode=docs_mode))

                    else:
                        print(deactivated_str, kmi_to_string(kmi, docs_mode=docs_mode))
                        kmi.active = False

            km = kc.keymaps.get("Node Tool: Select Box")
            print_keymap_title(km)

            for kmi in km.keymap_items:
                if kmi.idname == "node.select":
                    print(deactivated_str, kmi_to_string(kmi, docs_mode=docs_mode))
                    kmi.active = False

            km = kc.keymaps.get("Node Editor")
            print_keymap_title(km)

            for kmi in km.keymap_items:

                if kmi.idname == "node.select":
                    if kmi.type == 'RIGHTMOUSE':
                        print(changed_str, kmi_to_string(kmi, docs_mode=docs_mode))
                        kmi.type = 'LEFTMOUSE'
                        kmi.value = 'PRESS'
                        print(to_str, kmi_to_string(kmi, docs_mode=docs_mode))

                if kmi.idname == "node.links_cut":
                    if kmi.map_type == 'MOUSE' and kmi.value == 'CLICK_DRAG':
                        print(changed_str, kmi_to_string(kmi, docs_mode=docs_mode))
                        kmi.type = 'RIGHTMOUSE'
                        print(to_str, kmi_to_string(kmi, docs_mode=docs_mode))

                if kmi.idname == "node.add_reroute":
                    if kmi.map_type == 'MOUSE' and kmi.value == 'CLICK_DRAG':
                        print(changed_str, kmi_to_string(kmi, docs_mode=docs_mode))
                        kmi.type = 'RIGHTMOUSE'
                        print(to_str, kmi_to_string(kmi, docs_mode=docs_mode))

                if kmi.idname == "node.view_selected":
                    if kmi.type == "NUMPAD_PERIOD":
                        print(changed_str, kmi_to_string(kmi, docs_mode=docs_mode))
                        kmi.type = "F"
                        print(to_str, kmi_to_string(kmi, docs_mode=docs_mode))

                if kmi.idname == "node.view_all":
                    if kmi.type == "HOME":
                        print(changed_str, kmi_to_string(kmi, docs_mode=docs_mode))
                        kmi.type = "F"
                        kmi.shift = True
                        print(to_str, kmi_to_string(kmi, docs_mode=docs_mode))

                if kmi.idname == "node.link_make":
                    if kmi.type == "F" and kmi.active:
                        print(deactivated_str, kmi_to_string(kmi, docs_mode=docs_mode))
                        kmi.active = False

            km = kc.keymaps.get("File Browser")
            print_keymap_title(km)

            for kmi in km.keymap_items:
                if kmi.idname == "file.start_filter":
                    print(changed_str, kmi_to_string(kmi, docs_mode=docs_mode))
                    kmi.type = 'SLASH'
                    kmi.ctrl = False
                    print(to_str, kmi_to_string(kmi, docs_mode=docs_mode))

            km = kc.keymaps.get("File Browser Main")
            print_keymap_title(km)

            for kmi in km.keymap_items:
                if kmi.idname == "file.view_selected":
                    print(changed_str, kmi_to_string(kmi, docs_mode=docs_mode))
                    kmi.type = 'F'
                    print(to_str, kmi_to_string(kmi, docs_mode=docs_mode))

            km = kc.keymaps.get("Transform Modal Map")
            print_keymap_title(km)

            for kmi in km.keymap_items:
                if kmi.propvalue == 'PROPORTIONAL_SIZE_UP' and kmi.type == 'WHEELDOWNMOUSE':
                    print(f" Changed Transform Modal Map's PROPORTIONAL_SIZE_UP from {'SHIFT + ' if kmi.shift else ''}WHEELDOWNMOUSE")
                    kmi.type = 'WHEELUPMOUSE'
                    print(f"                                                      to {'SHIFT + ' if kmi.shift else ''}WHEELUPMOUSE")

                elif kmi.propvalue == 'PROPORTIONAL_SIZE_DOWN' and kmi.type == 'WHEELUPMOUSE':
                    print(f" Changed Transform Modal Map's PROPORTIONAL_SIZE_UP from {'SHIFT + ' if kmi.shift else ''}WHEELUPMOUSE")
                    kmi.type = 'WHEELDOWNMOUSE'
                    print(f"                                                      to {'SHIFT + ' if kmi.shift else ''}WHEELDOWNMOUSE")

            km = kc.keymaps.get(f"Grease Pencil {'Stroke ' if bpy.app.version < (4, 3, 0) else ''}Edit Mode", None)
            print_keymap_title(km)

            for kmi in km.keymap_items:

                if kmi.idname == "gpencil.stroke_cyclical_set":
                    print(deactivated_str, kmi_to_string(kmi, docs_mode=docs_mode))
                    kmi.active = False

                elif kmi.idname == "grease_pencil.cyclical_set":
                    print(deactivated_str, kmi_to_string(kmi, docs_mode=docs_mode))
                    kmi.active = False

            if bpy.app.version >= (4, 3, 0):
                km = kc.keymaps.get("Grease Pencil Sculpt Mode", None)
                print_keymap_title(km)

                for kmi in km.keymap_items:
                    if kmi.idname == "wm.radial_control":
                        if kmi.properties.data_path_primary == "tool_settings.gpencil_sculpt_paint.brush.size":#

                            kmi.active = True

                            print(changed_str, kmi_to_string(kmi, docs_mode=docs_mode))
                            kmi.properties.release_confirm = True
                            print(to_str, kmi_to_string(kmi, docs_mode=docs_mode))

                km = kc.keymaps.get("Grease Pencil Brush Stroke", None)
                print_keymap_title(km)

                for kmi in km.keymap_items:

                    if kmi.idname == "wm.radial_control":

                        if kmi.properties.data_path_primary == "tool_settings.gpencil_paint.brush.size":

                            kmi.active = True

                            print(changed_str, kmi_to_string(kmi, docs_mode=docs_mode))
                            kmi.properties.release_confirm = True
                            print(to_str, kmi_to_string(kmi, docs_mode=docs_mode))

        def add_keymaps(kc):

            km = kc.keymaps.get("Mesh")
            print_keymap_title(km)

            kmi = km.keymap_items.new("mesh.loop_multi_select", "LEFTMOUSE", "CLICK_DRAG", alt=True, shift=True)
            kmi.direction = 'SOUTH'
            kmi.properties.ring = False
            print(added_str, kmi_to_string(kmi, docs_mode=docs_mode))

            kmi = km.keymap_items.new("mesh.loop_multi_select", "LEFTMOUSE", "CLICK_DRAG", alt=True, ctrl=True)
            kmi.direction = 'SOUTH'
            kmi.properties.ring = True
            print(added_str, kmi_to_string(kmi, docs_mode=docs_mode))

            kmi = km.keymap_items.new("mesh.subdivide", "TWO", "PRESS", alt=True)
            kmi.properties.smoothness = 0
            print(added_str, kmi_to_string(kmi, docs_mode=docs_mode))

            km = kc.keymaps.get("Toolbar Popup")
            print_keymap_title(km)

            kmi = km.keymap_items.new("wm.tool_set_by_id", "D", "PRESS")
            kmi.properties.name = 'builtin.annotate'
            print(added_str, kmi_to_string(kmi, docs_mode=docs_mode))

            kmi = km.keymap_items.new("wm.tool_set_by_id", "E", "PRESS")
            kmi.properties.name = 'builtin.annotate_eraser'
            print(added_str, kmi_to_string(kmi, docs_mode=docs_mode))

        kc = context.window_manager.keyconfigs.user

        modify_keymaps(kc)
        add_keymaps(kc)

        if getattr(bpy.types, "MACHIN3_MT_save_pie", False):
            kmi = get_keymap_item('Window', 'machin3.save_versioned_startup_file')

            if kmi:
                kmi.active = True

        if getattr(bpy.types, "MACHIN3_OT_material_picker", False):
            kmi = get_keymap_item('3D View Generic', 'machin3.material_picker')

            if kmi:
                kmi.active = True

        if getattr(bpy.types, "MACHIN3_OT_set_tool", False):
            kmi = get_keymap_item('3D View Generic', 'machin3.set_tool', properties=[('pick', True)])

            if kmi:
                kmi.active = True

    def preferences(self, context):
        prefs = context.preferences

        prefs.use_preferences_save = False

        if get_prefs().custom_preferences_interface:
            print("\n» Changing Preferences: Interface")

            v = prefs.view

            print(" Disabled Splash Screen")
            v.show_splash = False

            print(" Enabled Tool Tips")
            v.show_tooltips = True

            print(" Enabled Python Tool Tips")
            v.show_tooltips_python = True

            print(" Enabled Developer Extras")
            v.show_developer_ui = True

            print(" Changed Header Position to BOTTOM (for the 3D View, and back to KEEP_EXISTING as a preference")
            v.header_align = 'BOTTOM'
            v.header_align = 'NONE'

            print(" Disabled Navigation Controls")
            v.show_navigate_ui = False

            print(" Changed Color Picker to SQUARE_SV")
            v.color_picker_type = "SQUARE_SV"

            print(" Changed Pie Menu Animation Timeout to 0")
            v.pie_animation_timeout = 0

            print(" Enabled Status Bar System Memory")
            v.show_statusbar_memory = True

            print(" Enabled Status Bar Video Memory")
            v.show_statusbar_vram = True

        if get_prefs().custom_preferences_viewport:
            print("\n» Changing Preferences: Viewport")

            v = prefs.view

            print(" Changed 3D Viewport Axis to MINIMAL")
            v.mini_axis_type = 'MINIMAL'

        if get_prefs().custom_preferences_input_navigation:
            print("\n» Changing Preferences: Input and Navigation")

            i = prefs.inputs

            print(" Enabled Mouse Zoom Invert")
            i.invert_mouse_zoom = True

            print(" Enabled Zoom to Mouse Position")
            i.use_zoom_to_mouse = True

            print(" Changed Double Click Speed to 200")
            i.mouse_double_click_time = 200

            print(" Changed NDOF Dead Zone to 0.03")
            i.ndof_deadzone = 0.03

            if bpy.app.version >= (4, 5, 0):

                print(" Disabled NDOF Orbit Center Auto")
                i.ndof_orbit_center_auto = False

                print(" Enabled NDOF Pan Axis Inversions")
                i.ndof_panx_invert_axis = True
                i.ndof_pany_invert_axis = True
                i.ndof_panz_invert_axis = True

                print(" Enabled NDOF Rotation Axis Inversions")
                i.ndof_rotx_invert_axis = True
                i.ndof_roty_invert_axis = True
                i.ndof_rotz_invert_axis = True

            else:

                print(" Disabled NDOF Zoom Invert")
                i.ndof_zoom_invert = False

                print(" Disabled NDOF Lock Camera Pan/Zoom")
                i.ndof_lock_camera_pan_zoom = False

                print(" Changed NDOF View Rotate Method to Turntable")
                i.ndof_view_rotate_method = 'TURNTABLE'

                print(" Disabled NDOF Pan Axis Inversions")
                i.ndof_panx_invert_axis = False
                i.ndof_pany_invert_axis = False
                i.ndof_panz_invert_axis = False

                print(" Disabled NDOF Rotation Axis Inversions")
                i.ndof_rotx_invert_axis = False
                i.ndof_roty_invert_axis = False
                i.ndof_rotz_invert_axis = False

                print(" Disabled NDOF Lock Horizon")
                i.ndof_lock_horizon = False

            if bpy.app.version >= (4, 4, 0):
                print(" Disabled NDOF (Show) Orbit Center")
                i.ndof_show_guide_orbit_center = False

        if get_prefs().custom_preferences_keymap:
            print("\n» Changing Preferences: Keymap")

            keyconfigpath = bpy.utils.preset_paths(subdir='keyconfig')

            if keyconfigpath:
                keymappath = os.path.join(keyconfigpath[0], "Blender_27x.py")

                print(" Set 2.7X keymap")
                bpy.ops.preferences.keyconfig_activate(filepath=keymappath)

                print(" Changed Select Mouse to LEFT")
                kcprefs = context.window_manager.keyconfigs.active.preferences
                kcprefs.select_mouse = "LEFT"

                bpy.ops.preferences.keyconfig_activate(filepath=keymappath)

                kcprefs = context.window_manager.keyconfigs.active.preferences
                kcprefs.select_mouse = "LEFT"

            self.customize_keymap(context)

        if get_prefs().custom_preferences_system:
            print("\n» Changing Preferences: System")

            c = prefs.addons['cycles'].preferences
            e = prefs.edit

            print(" Changed Cylces Render Decive to CUDA")
            c.compute_device_type = "CUDA"

            for d in c.devices:
                d.use = True

            print(" Changed Undo Steps to 64")
            e.undo_steps = 64

            print("\n» Changing Preferences: Experimental")
            ex = prefs.experimental

            print(" Enabled Asset Debug Info")
            ex.show_asset_debug_info = True

        if get_prefs().custom_preferences_save:
            print("\n» Changing Preferences: Save & Load")

            v = prefs.view
            f = prefs.filepaths

            print(" Disabled Save Prompt")
            v.use_save_prompt = False

            print(" Enabled File Compression")
            f.use_file_compression = True

            print(" Disabled UI Loading")
            f.use_load_ui = False

            print(" Changed Save Versions to 3")
            f.save_version = 3

            print(" Changed Recent Files to 20")
            f.recent_files = 20

    def theme(self, scriptspath, resourcespath):
        print("\n» Installing and Enabling M3 theme (a merger of Flatty Dark Blueberry + rTheme)")

        themesourcepath = os.path.join(resourcespath, 'theme', 'm3.xml')
        themetargetpath = makedir(os.path.join(scriptspath, 'presets', 'interface_theme'))

        filepath = shutil.copy(themesourcepath, themetargetpath)
        bpy.ops.script.execute_preset(filepath=filepath, menu_idname="USERPREF_MT_interface_theme_presets")

    def matcaps(self, context, resourcespath, datafilespath):
        print("\n» Adding Matcaps")

        matcapsourcepath = os.path.join(resourcespath, "matcaps")
        matcaptargetpath = makedir(os.path.join(datafilespath, "studiolights", "matcap"))
        matcaps = os.listdir(matcapsourcepath)

        for matcap in sorted(matcaps):
            shutil.copy(os.path.join(matcapsourcepath, matcap), matcaptargetpath)
            print("  %s -> %s" % (matcap, matcaptargetpath))

        context.preferences.studio_lights.refresh()

        if all([mc in matcaps for mc in ["matcap_base.exr", "matcap_shiny_red.exr"]]):
            get_prefs().switchmatcap1 = "matcap_base.exr"
            get_prefs().switchmatcap2 = "matcap_shiny_red.exr"

    def shading(self, context):
        print("\n» Setting up Shading and Rendering")

        areas = [area for screen in context.workspace.screens for area in screen.areas if area.type == "VIEW_3D"]

        for area in areas:
            shading = area.spaces[0].shading

            print(" Changed shading.type to SOLID")
            shading.type = "SOLID"

            print(" Changed shading.light to MATCAP")
            shading.light = "MATCAP"

            print(" Changed shading.color_type to SINGLE")
            shading.color_type = "SINGLE"

            print(" Changed shading.single_color to #838387")
            shading.single_color = (0.2270, 0.2270, 0.2423)  # hex 838387

            if 'matcap_base.exr' in context.preferences.studio_lights:
                print(" Changed shading.studio_light to matcap_base.exr")
                shading.studio_light = "matcap_base.exr"

            print(" Changed shading.studiolight_background_alpha to 0")
            shading.studiolight_background_alpha = 0

            print(" Changed shading.studiolight_background_blur to 1")
            shading.studiolight_background_blur = 1

            print(" Enabled shading.show_cavity")
            shading.show_cavity = True

            print(" Changed shading.cavity_type to WORLD")
            shading.cavity_type = 'WORLD'

            print(" Changed shading.cavity_ridge_factor to 0")
            shading.cavity_ridge_factor = 0

            print(" Changed shading.cavity_valley_factor to 2")
            shading.cavity_valley_factor = 2

            print(" Enabled shading.show_backface_culling")
            shading.show_backface_culling = True

            print(" Enabled shading.use_scene_lights")
            shading.use_scene_lights = True

            print(" Enabled shading.use_scene_lights_render")
            shading.use_scene_lights_render = True

            print(" Disabled shading.use_scene_world_render")
            shading.use_scene_world_render = False

        eevee = context.scene.eevee

        if bpy.app.version < (4, 3, 0):
            print(" Enabled eevee.use_ssr")
            eevee.use_ssr = True

            print(" Enabled eevee.use_gtao")
            eevee.use_gtao = True

            print(" Disabled eevee.use_volumetric_lights")
            eevee.use_volumetric_lights = False

        else:
            print(" Enable LOW Eevee Next Preset")

            eevee.use_shadows = True
            eevee.shadow_step_count = 2

            eevee.use_volumetric_shadows = False

            eevee.use_raytracing = True
            eevee.ray_tracing_options.resolution_scale = "4"
            eevee.ray_tracing_options.screen_trace_quality = 0.1

            eevee.fast_gi_step_count = 16
            eevee.fast_gi_quality = 0.1
            eevee.fast_gi_resolution = "4"

            eevee.volumetric_tile_size = "8"

            context.scene.M3.avoid_update = True
            context.scene.M3.eevee_next_preset = 'LOW'

        cycles = context.scene.cycles

        print(" Changed Render Engine to CYCLES")
        context.scene.render.engine = 'CYCLES'

        print(" Changed Cycles Devices to GPU")
        cycles.device = 'GPU'

        print(" Enabled cycle.use_preview_denoising")
        cycles.use_preview_denoising = True

        print(" Set cycles.preview_denoising_start_sample to 2")
        cycles.preview_denoising_start_sample = 2

        print(" Set cycles.preview_denoising_input_passes to 'NONE'")
        cycles.preview_denoising_input_passes = 'RGB'

        print(" Enabled Fast GI Approximation")
        cycles.use_fast_gi = True

        print(" Set cycles.ao_bounces to 2")
        cycles.ao_bounces = 2

        print(" Set cycles.ao_bounces_render to 2")
        cycles.ao_bounces_render = 2

    def overlays(self, context):
        print("\n» Modifying Overlays")

        areas = [area for screen in context.workspace.screens for area in screen.areas if area.type == "VIEW_3D"]

        for area in areas:
            overlay = area.spaces[0].overlay

            print(" Enabled overlay.show_face_center")
            overlay.show_face_center = True

            print(" Disabled overlay.show_relationship_lines")
            overlay.show_relationship_lines = False

            print(" Changed overlay.vertex_opacity to 1")
            overlay.vertex_opacity = 1

            print(" Disabled overlay.show_fade_inactive")
            overlay.show_fade_inactive = False

            if get_prefs().custom_theme:
                print(" Enabled overlay.show_face_orientation (whith the M3 Theme being used)")
                overlay.show_face_orientation = True

    def outliner(self, context):
        print("\n» Modifying Outliner")

        areas = [area for screen in context.workspace.screens for area in screen.areas if area.type == "OUTLINER"]

        for area in areas:
            space = area.spaces[0]

            print(" Disabled outliner.use_filter_children")
            space.use_filter_children = False

            print(" Disabled outliner.use_filter_object_content")
            space.use_filter_object_content = False

            print(" Enabled outliner.show_restrict_column_select")
            space.show_restrict_column_select = True

            print(" Enabled outliner.show_restrict_column_viewport")
            space.show_restrict_column_viewport = True

            print(" Enabled outliner.show_restrict_column_render")
            space.show_restrict_column_render = True

    def startup(self, context):
        print("\n» Modifying Startup Scene")

        scene = context.scene

        print(" Enabled tool_settings.use_uv_select_sync")
        scene.tool_settings.use_uv_select_sync = True

        if get_prefs().activate_shading_pie:

            for area in [area for screen in context.workspace.screens for area in screen.areas if area.type == "VIEW_3D"]:
                area.spaces[0].overlay.show_cursor = False
                print(" Disabled overlay.show_cursor")

            scene.M3.draw_cursor_axes = True
            print(" Enabled scene.M3.draw_cursor_axes")

            scene.M3.draw_active_axes = True
            print(" Enabled scene.M3.draw_active_axes")

        scene.render.compositor_device = 'GPU'
        print(" Enabled GPU Compositing")

        light = bpy.data.lights.get('Light')
        if light:
            print(" Removed default Light")
            bpy.data.lights.remove(light, do_unlink=True)

        cam = bpy.data.cameras.get('Camera')
        if cam:
            print(" Removed default Camera")
            bpy.data.cameras.remove(cam, do_unlink=True)

        cube = bpy.data.meshes.get('Cube')
        if cube:
            print(" Removed default Cube")
            bpy.data.meshes.remove(cube, do_unlink=True)

        col = bpy.data.collections.get('Collection')
        if col:
            print(" Removed default Collection")
            bpy.data.collections.remove(col, do_unlink=True)

        mat = bpy.data.materials.get('Material')
        if mat:
            print(" Removed default Material")
            bpy.data.materials.remove(mat, do_unlink=True)

        print(" Aligned Viewport with Y Axis")
        reset_viewport(context, disable_toolbar=True)

        print(" Set Annotation Stroke Placement to Surface")
        scene.tool_settings.annotation_stroke_placement_view3d = 'SURFACE'

        print(" Set Annotation Eraser Size to 50")
        context.preferences.edit.grease_pencil_eraser_radius = 50

    def worlds(self, context, resourcespath, datafilespath):
        print("\n» Adding Custom EXRs")

        worldssourcepath = os.path.join(resourcespath, "worlds")
        worldstargetpath = makedir(os.path.join(datafilespath, "studiolights", "world"))

        if os.path.exists(worldssourcepath):
            worlds = os.listdir(worldssourcepath)

            for world in sorted(worlds):
                shutil.copy(os.path.join(worldssourcepath, world), worldstargetpath)
                print(f"  {world} -> {worldstargetpath}")

    def bookmarks(self, context):
        print("\n» Setting Custom Bookmarks")

        path = bpy.utils.user_resource('CONFIG', path="bookmarks.txt")

        lines = ['[Bookmarks]',
                 '!Archive',
                 '/home/x/Archive/blender',
                 '!Library',
                 '/home/x/Archive/blender/Library',
                 '!TEMP',
                 '/home/x/TEMP/blender',
                 '!Addons',
                 '/home/x/TEMP/blender/Addons',
                 '!Output',
                 '/home/x/TEMP/blender/Output',
                 '[Recent]',
                 '!DECALmachine',
                 '/home/x/TEMP/blender/Addons/DECALmachine',
                 '!MESHmachine',
                 '/home/x/TEMP/blender/Addons/MESHmachine',
                 ]

        with open(path, mode='w') as f:
            f.write('\n'.join(lines))

    def asset_library(self, context):
        print("\n» Setting up Custom Asset Library")

        librariesCOL = context.preferences.filepaths.asset_libraries

        for lib in librariesCOL:
            if lib.name == 'User Library':
                lib.name = 'Library'
                lib.path = '/home/x/Archive/blender/Library'
                lib.import_method = 'APPEND'

                print(f"  main assets library is now called '{lib.name}' and located at '{lib.path}'")

    def enable_3rd_party_addons(self, context):
        print("\n» Enabling 3rd-party Addons")

        def disable_screencast_keys_keymap_item():
            kmi = get_keymap_item("3D View", "wm.sk_screencast_keys")

            if kmi:
                kmi.active = False
                print(" De-activated Screencast Keys keymap")

        addons = ['LoopTools',
                  'Icon Viewer',
                  'Node Wrangler',
                  'Pose Library']

        addons.append('Screencast Keys')

        for addon in addons:
            enable_addon(context, addon)

        if M3.get_addon('Screencast Keys'):

            p = get_addon_prefs('Screencast Keys')

            if p:
                print(" Setting up Screencast Keys Addon Preferences")
                p.show_ui_in_sidebar = False

                p.origin = "AREA"
                p.align = "RIGHT"
                p.offset = (-20, 60)

                p.display_time = 4
                p.font_size = round(12 * get_scale(context))

                p.max_event_history = 12
                p.repeat_count = False
                p.mouse_events_show_mode = "EVENT_HISTORY_AND_HOLD_STATUS"

            delay_execution(disable_screencast_keys_keymap_item, delay=0.3)

    def customize_my_own_addons(self, context):
        def customize_workspace_pie(prefs):
            print("\n» Customizing Workspace Pie")

            for pie_dir in ['left', 'right', 'bottom', 'top', 'top_left', 'top_right', 'bottom_left', 'bottom_right']:
                if pie_dir == 'left':
                    setattr(prefs, f'pie_workspace_{pie_dir}_name', 'General')
                    setattr(prefs, f'pie_workspace_{pie_dir}_text', 'MACHIN3')
                    setattr(prefs, f'pie_workspace_{pie_dir}_icon', 'VIEW3D')

                elif pie_dir == 'right':
                    setattr(prefs, f'pie_workspace_{pie_dir}_name', 'Compositing')
                    setattr(prefs, f'pie_workspace_{pie_dir}_text', 'Compositing')
                    setattr(prefs, f'pie_workspace_{pie_dir}_icon', 'NODE_COMPOSITING')

                elif pie_dir == 'bottom':
                    setattr(prefs, f'pie_workspace_{pie_dir}_name', 'Scripting')
                    setattr(prefs, f'pie_workspace_{pie_dir}_text', 'Scripting')
                    setattr(prefs, f'pie_workspace_{pie_dir}_icon', 'CONSOLE')

                elif pie_dir == 'top':
                    setattr(prefs, f'pie_workspace_{pie_dir}_name', 'Material')
                    setattr(prefs, f'pie_workspace_{pie_dir}_text', 'Material')
                    setattr(prefs, f'pie_workspace_{pie_dir}_icon', 'MATERIAL_DATA')

                elif pie_dir == 'top_left':
                    setattr(prefs, f'pie_workspace_{pie_dir}_name', 'UVs')
                    setattr(prefs, f'pie_workspace_{pie_dir}_text', 'UVs')
                    setattr(prefs, f'pie_workspace_{pie_dir}_icon', 'GROUP_UVS')

                elif pie_dir == 'top_right':
                    setattr(prefs, f'pie_workspace_{pie_dir}_name', 'World')
                    setattr(prefs, f'pie_workspace_{pie_dir}_text', 'World')
                    setattr(prefs, f'pie_workspace_{pie_dir}_icon', 'WORLD')

                elif pie_dir == 'bottom_left':
                    setattr(prefs, f'pie_workspace_{pie_dir}_name', 'GeoNodes')
                    setattr(prefs, f'pie_workspace_{pie_dir}_text', 'Geo Nodes')
                    setattr(prefs, f'pie_workspace_{pie_dir}_icon', 'GEOMETRY_NODES')

                else:
                    setattr(prefs, f'pie_workspace_{pie_dir}_name', '')
                    setattr(prefs, f'pie_workspace_{pie_dir}_text', '')
                    setattr(prefs, f'pie_workspace_{pie_dir}_icon', '')

        p = get_prefs()

        customize_workspace_pie(p)

        p.show_help_in_sidebar_panel = False

        p.modes_pie_object_mode_top_show_sculpt = False

        p.autosave_external_folder = os.path.expanduser('~/TEMP/blender/_autoasave')

        p.screencast_use_ffmpeg_screenrecord = True

        p.tools_switch_list = "builtin.select_box, machin3.tool_hyper_cursor"

    def adjust_workspaces(self, context):
        print("\n» Adjusting Workspaces")

        workspaces = [ws for ws in bpy.data.workspaces if ws != context.workspace]
        bpy.data.batch_remove(ids=workspaces)

        for window in context.window_manager.windows:
            screen = window.screen

            view3ds = [area for area in screen.areas if area.type == 'VIEW_3D']

            for area in view3ds:
                for space in area.spaces:
                    if space.type == area.type:
                        space.show_region_hud = False

                        print(f" Disabled 'Adjust Last Operation' on {screen.name}'s 3D View")

            return

    def add_workspaces(self, context):
        print("\n» Adding Workspaces")

        areas = [area for screen in context.workspace.screens for area in screen.areas if area.type == "VIEW_3D"]

        return

        if areas:

            names = ['General.alt', 'UVs', 'UVs.alt', 'Material', 'World', 'Scripting', 'Scripting.alt']

            for idx, name in enumerate(names):
                with context.temp_override(area=areas[0]):
                    bpy.ops.workspace.duplicate()

            for name, ws in zip(names, bpy.data.workspaces[1:]):
                ws.name = name
