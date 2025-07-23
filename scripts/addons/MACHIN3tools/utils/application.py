import bpy
import bpy_types
import bpy_restrict_state

import os
from datetime import datetime
import shutil
import re

from .. colors import blue

def delay_execution(func, delay:float=0, persistent=False):
    if bpy.app.timers.is_registered(func):
        bpy.app.timers.unregister(func)

    bpy.app.timers.register(func, first_interval=delay, persistent=persistent)

def is_context_safe(context):
    if type(context) is bpy_types.Context:
        return True

    elif type(context) is bpy_restrict_state._RestrictContext:
        print("WARNING: Context is restricted!")
        return False

    else:
        print("WARNING: Unexpected Context Type", context, type(context))
        return False

def set_prop_safe(id, prop, value):
    try:
        setattr(id, prop, value)

    except AttributeError as e:
        print(f"WARNING: failed setting {prop} on {id} to {value} with\n AttributeError:" , e)

    except Exception as e:
        print("WARNING:", e)

def auto_save(folder=None, undo=False, debug=False):
    from . registration import get_prefs

    self_save = get_prefs().autosave_self
    ext_save = get_prefs().autosave_external

    if self_save or ext_save:
        from . draw import draw_fading_label
        from . workspace import get_3dview

        use_compression = bpy.context.preferences.filepaths.use_file_compression

        if ext_save:

            if folder is None:
                from . system import get_autosave_external_folder

                folder, _ = get_autosave_external_folder()

                if not folder and not self_save:
                    print("WARNING: temp dir for Auto Saving could not be determined")
                    return

                filepath = bpy.data.filepath

                if filepath:
                    filename = os.path.basename(filepath)

                else:
                    filename = "startup.blend"

                name, _ = os.path.splitext(filename)
                date_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                path = os.path.join(folder,  f"{date_time}_{name}-autosave.blend")

        if self_save:

            if bpy.data.filepath:
                bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath, check_existing=False, copy=False, compress=use_compression)
                src = bpy.data.filepath

            else:
                bpy.ops.wm.save_homefile()
                src = bpy.utils.user_resource('CONFIG', path="startup.blend")

            if ext_save:
                shutil.copy(src, path)

            area, region, region_data, space = get_3dview(bpy.context)

            if area:
                draw_fading_label(bpy.context, text="🕒 Auto Saved", y=80, size=12, color=blue, time=2)

        elif ext_save:

            bpy.ops.wm.save_as_mainfile(filepath=path, check_existing=False, copy=True, compress=use_compression)

            area, region, region_data, space = get_3dview(bpy.context)

            if area:
                screen_areas = [area for area in bpy.context.screen.areas]

                if area in screen_areas:
                    with bpy.context.temp_override(area=area, region=region):
                        draw_fading_label(bpy.context, text=f"{'⮌' if undo else '🕒'} Auto Saved", y=80, size=12, color=blue, time=1)

        if ext_save:
            autosaveRegex= re.compile(r'(-autosave.blend\d?)$')
            autosaved = sorted([os.path.join(folder, f) for f in os.listdir(folder) if autosaveRegex.search(f)])

            if (count := len(autosaved)) > (limit := get_prefs().autosave_external_limit):
                for f in autosaved[:count - limit]:
                    os.unlink(f)

        return path
