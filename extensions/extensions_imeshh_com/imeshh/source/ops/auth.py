import json

import bpy
import jwt
import requests
from bpy.types import Operator

from ..utils.addon import preferences
from ..utils.auth import (
    HEADERS,
    PATH_AUTH_FILE,
    PATH_PREFS_FILE,
    URL_TOKEN,
    auth_token_exists,
    delete_auth_data,
    save_subs_data,
)


class IMESHH_OT_login(Operator):
    """Login to iMeshh"""

    bl_idname = "imeshh.login"
    bl_label = "Login"
    bl_options = {"REGISTER", "INTERNAL"}

    @classmethod
    def poll(cls, context):
        prefs = preferences()
        return prefs.username and prefs.password

    def execute(self, context):
        prefs = preferences()

        try:
            response = requests.post(
                URL_TOKEN, headers=HEADERS, data={"username": prefs.username, "password": prefs.password}
            )
        except requests.exceptions.ConnectionError:
            self.report({"ERROR"}, "Connection Error: Please check your internet connection")
            return {"CANCELLED"}

        if response.status_code == 200:
            prefs.password = ""

            try:
                auth_token = response.json().get("token")
                decoded = jwt.decode(auth_token, options={"verify_signature": False})
            except Exception as e:
                print(f"EXCEPTION: An error occurred while logging: {e}")
                self.report({"ERROR"}, "Invalid server response format")
                return {"CANCELLED"}

            auth_data = {
                "auth_token": auth_token,
                "token_expiry": decoded.get("exp"),
            }

            with open(PATH_AUTH_FILE, "w", encoding="utf-8") as file:
                json.dump(auth_data, file, indent=4)

            save_subs_data()

            self.report({"INFO"}, "iMeshh: Logged In")
            return {"FINISHED"}

        print(f"ERROR: {response.status_code} - {response.json().get('message', 'Unknown Error')}")
        self.report({"ERROR"}, "Invalid Credentials")
        return {"CANCELLED"}


class IMESHH_OT_logout(Operator):
    """Logout from iMeshh"""

    bl_idname = "imeshh.logout"
    bl_label = "Logout"
    bl_options = {"REGISTER", "INTERNAL"}

    @classmethod
    def poll(cls, context):
        return auth_token_exists()

    def execute(self, context):
        prefs = preferences()
        prefs.password = ""
        delete_auth_data()
        self.report({"INFO"}, "iMeshh: Logged Out")
        return {"FINISHED"}


class IMESHH_OT_save_userpref(Operator):
    """Save user preferences as JSON file"""

    bl_label = "Save Preferences"
    bl_idname = "imeshh.save_userpref"
    bl_options = {"REGISTER", "INTERNAL"}

    def execute(self, context):
        prefs = preferences()

        prefs_data = {
            "username": prefs.username,
            "models_path": prefs.models_path,
            "materials_path": prefs.materials_path,
            "geonodes_path": prefs.geonodes_path,
            "fxs_path": prefs.fxs_path,
            "linked": prefs.linked,
            "apply_size": prefs.apply_size,
            "import_as_collection": prefs.import_as_collection,  # Add this line
            "preview_limit": prefs.preview_limit,
            "popup_scale": prefs.popup_scale,
            "show_asset_name": prefs.show_asset_name,
        }

        with open(PATH_PREFS_FILE, "w", encoding="utf-8") as file:
            json.dump(prefs_data, file, indent=4)

        self.report({"INFO"}, "iMeshh: Preferences saved")
        return {"FINISHED"}


classes = (
    IMESHH_OT_login,
    IMESHH_OT_logout,
    IMESHH_OT_save_userpref,
)


register, unregister = bpy.utils.register_classes_factory(classes)
