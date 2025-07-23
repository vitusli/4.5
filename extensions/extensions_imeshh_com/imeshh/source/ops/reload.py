import json
import os
import threading

import bpy
from bpy.types import Operator

from ..utils.auth import (
    PATH_CATEGORIES_FILE,
    PATH_PRODUCTS_FILE,
    PATH_STATUS_FILE,
    get_status_data,
    save_message_data,
    save_status_data,
    save_subs_data,
)
from ..utils.product import (
    save_assets_cat_data,
    save_categories_data,
    save_products_data,
)


class IMESHH_OT_reload(Operator):
    """Reload the addon"""

    bl_label = "Reload"
    bl_idname = "imeshh.reload"
    bl_options = {"REGISTER", "INTERNAL"}

    @classmethod
    def poll(cls, context):
        return not len(context.window_manager.imeshh.download_list) >= 6

    def execute(self, context):
        threading.Thread(target=self.worker, daemon=True).start()

        save_assets_cat_data()
        save_subs_data()
        save_message_data()

        if hasattr(context.scene, "imeshh"):
            context.scene.imeshh.page = 1

        self.report({"INFO"}, "Reloaded: iMeshh Successfully!")
        return {"FINISHED"}

    def worker(self):
        new_status = get_status_data()
        need_update = (
            not os.path.exists(PATH_STATUS_FILE)
            or not os.path.exists(PATH_CATEGORIES_FILE)
            or not os.path.exists(PATH_PRODUCTS_FILE)
        )

        if not need_update:
            with open(PATH_STATUS_FILE, "r", encoding="utf-8") as f:
                stored_status = json.load(f)
            need_update = new_status and new_status.get("last_updated") != stored_status.get("last_updated")

        if need_update:
            save_products_data()
            save_categories_data()
            save_status_data(new_status)


classes = (IMESHH_OT_reload,)

register, unregister = bpy.utils.register_classes_factory(classes)
