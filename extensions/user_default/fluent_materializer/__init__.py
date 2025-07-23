'''
Copyright (C) 2019
rudy.michau@gmail.com

Created by RUDY MICHAU

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import bpy
import bpy.utils.previews
from .Tools.helper import load_icons, clear_icons, get_addon_preferences, uninstall_cv2, init_libraries_previews, init_node_samples
from .properties import FluentShaderProps
from . import auto_load
from .preferences import AddonKeymaps
from . import tasks_queue

def vider_dossier_pycache(racine):
    import os
    import shutil

    for root, dirs, files in os.walk(racine):
        if "__pycache__" in dirs:
            pycache_path = os.path.join(root, "__pycache__")
            print(f"Vidage du dossier: {pycache_path}")
            for fichier in os.listdir(pycache_path):
                fichier_path = os.path.join(pycache_path, fichier)
                try:
                    if os.path.isfile(fichier_path) or os.path.islink(fichier_path):
                        os.unlink(fichier_path)
                    elif os.path.isdir(fichier_path):
                        shutil.rmtree(fichier_path)
                except Exception as e:
                    print(f"Erreur lors de la suppression {fichier_path}: {e}")
import os
# vider_dossier_pycache(os.path.dirname(os.path.realpath(__file__)))
# uninstall_cv2()

auto_load.init()


def register():
    auto_load.register()

    bpy.types.Scene.FluentShaderProps = bpy.props.PointerProperty(type=FluentShaderProps)
    AddonKeymaps.new_keymap('Fluent Shader', 'wm.call_menu_pie', 'FLUENT_SHADER_MT_Pie_Menu',
                            'Node Generic', 'NODE_EDITOR', 'WINDOW', 'F',
                            'PRESS', False, False, False, 'NONE'
                            )
    AddonKeymaps.new_keymap('Refresh', 'fluent.refresh', None,
                            '3D View Generic', 'VIEW_3D', 'WINDOW', 'GRLESS',
                            'PRESS', True, False, False, 'NONE'
                            )
    AddonKeymaps.register_keymaps()

    get_addon_preferences().pil_warning = False
    try:
        from PIL import Image
        get_addon_preferences().pil = True
    except:
        get_addon_preferences().pil = False

    get_addon_preferences().cv2_warning = False
    try:
        import cv2
        get_addon_preferences().cv2 = True
    except:
        get_addon_preferences().cv2 = False

    bpy.app.timers.register(init_libraries_previews, first_interval=0.1)
    bpy.app.timers.register(init_node_samples, first_interval=0.1)


def unregister():
    AddonKeymaps.unregister_keymaps()
    auto_load.unregister()
    clear_icons()


if __name__ == "__main__":
    register()
