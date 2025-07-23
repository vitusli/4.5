import json
import os

import bpy
from bpy.props import IntProperty
from bpy.types import Operator

from ..utils.auth import PATH_FAVOURITES_FILE


class IMESHH_OT_favourite(Operator):

    bl_label = "Favourite"
    bl_idname = "imeshh.favourite"
    bl_options = {"REGISTER", "INTERNAL"}

    product_id: IntProperty(options={"SKIP_SAVE"})

    @classmethod
    def description(cls, context, properties):
        return "Mark the asset as favourite"

    def execute(self, context):
        # Read existing data or create new
        if os.path.exists(PATH_FAVOURITES_FILE):
            try:
                with open(PATH_FAVOURITES_FILE, "r", encoding="utf-8") as file:
                    data = json.load(file)
            except (FileNotFoundError, json.JSONDecodeError):
                data = {"product_ids": []}
        else:
            data = {"product_ids": []}

        # Update favourite state and choose message
        if self.product_id in data["product_ids"]:
            data["product_ids"].remove(self.product_id)
            message = "Asset unmarked as favourite"
        else:
            data["product_ids"].append(self.product_id)
            message = "Asset marked as favourite"

        with open(PATH_FAVOURITES_FILE, "w", encoding="utf-8") as file:
            json.dump(data, file)

        self.report({"INFO"}, message)
        return {"FINISHED"}


classes = (IMESHH_OT_favourite,)


register, unregister = bpy.utils.register_classes_factory(classes)
