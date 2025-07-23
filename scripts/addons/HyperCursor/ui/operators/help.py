import bpy

import os
import sys

from ... utils.registration import get_path
from ... utils.system import makedir, open_folder

from ... import bl_info

enc = sys.getdefaultencoding()

class GetSupport(bpy.types.Operator):
    bl_idname = "machin3.get_hypercursor_support"
    bl_label = "MACHIN3: Get HyperCursor Support"
    bl_description = "Generate Log Files and Instructions for a Support Request."
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        logpath = makedir(os.path.join(get_path(), "logs"))
        resourcespath = makedir(os.path.join(get_path(), "resources"))

        sysinfopath = os.path.join(logpath, "system_info.txt")
        bpy.ops.wm.sysinfo(filepath=sysinfopath)

        self.extend_system_info(context, sysinfopath)

        src = os.path.join(resourcespath, "readme.html")
        readmepath = os.path.join(logpath, "readme.html")

        with open(src, "r") as f:
            html = f.read()

        html = html.replace("VERSION", ".".join((str(v) for v in bl_info['version'])))

        folderurl = "file://" + logpath
        html = html.replace("FOLDER", f'<a href="{folderurl}">HyperCursor/logs</a>')

        with open(readmepath, "w") as f:
            f.write(html)

        readmeurl = "file://" + readmepath
        bpy.ops.wm.url_open(url=readmeurl)

        open_folder(logpath)

        return {'FINISHED'}

    def extend_system_info(self, context, sysinfopath):
        if os.path.exists(sysinfopath):
            with open(sysinfopath, 'r+', encoding=enc) as f:
                lines = f.readlines()
                newlines = lines.copy()

                for line in lines:
                    if all(string in line for string in ['version:', 'branch:', 'hash:']):
                        idx = newlines.index(line)
                        newlines.pop(idx)

                        newlines.insert(idx, line.replace(', type:', f", revision: {bl_info['revision']}, type:"))

                f.seek(0)
                f.writelines(newlines)
