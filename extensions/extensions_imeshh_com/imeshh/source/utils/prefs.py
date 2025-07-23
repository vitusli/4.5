import json
import os
from datetime import datetime

import bpy
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    EnumProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)
from bpy.types import AddonPreferences, PropertyGroup

from . import constants, local
from .addon import package, preferences
from .auth import PATH_PREFS_FILE, get_auth_token, get_subs_info, get_token_expiry
from .product import save_assets_cat_data

class IMESHH_PG_folder(PropertyGroup):

    def _items_subdirs(self, context):
        items = [("ALL", "All", "All", "NONE", 0), None]

        if os.path.exists(self.name):
            dirs, _ = local.get_dir_content(self.name)
            items.extend(
                [
                    (dir_path, dir_path.split(os.sep)[-1], dir_path, "NONE", idx + 1)
                    for idx, dir_path in enumerate(dirs)
                    if not local.is_asset_dir(context, dir_path)
                ]
            )

        return items

    def _update_subdirs(self, context):
        prefs = preferences()
        self._remove_higher(context)

        if self.sub_dir != "ALL":
            folder_list = prefs.local.folder_list.add()
            folder_list.name = self.sub_dir

        context.scene.imeshh.page = 1

    def _remove_higher(self, context):
        prefs = preferences()
        idx = next((i for i, f_list in enumerate(prefs.local.folder_list) if f_list == self), -1)
        if idx >= 0:
            for i in range(len(prefs.local.folder_list) - 1, idx, -1):
                prefs.local.folder_list.remove(i)

    sub_dir: EnumProperty(
        name="Sub Directory",
        description="Sub directory",
        items=_items_subdirs,
        update=_update_subdirs,
    )


class IMESHH_PG_local(PropertyGroup):

    folder_list: CollectionProperty(type=IMESHH_PG_folder)

    def _update_asset_type(self, context):
        self.folder_list.clear()
        folder = self.folder_list.add()

        if items := self._items_root_dir(context):
            self.root_dir = items[0][0]

        folder.name = self.root_dir

    asset_type: EnumProperty(
        name="Asset Type",
        description="Filter by asset type",
        items=constants.ENUM_ITEMS,
        update=_update_asset_type,
    )

    def _items_root_dir(self, context):
        """Return directories of current tab as enum items."""
        prefs = preferences()
        return [
            (bpy.path.abspath(dir.path), dir.name, dir.path, "NONE", i)
            for i, dir in enumerate(prefs.custom_paths)
            if dir.type == self.asset_type
        ]

    def _update_root_dir(self, context):
        self.folder_list.clear()
        folder = self.folder_list.add()
        folder.name = self.root_dir

        context.scene.imeshh.page = 1

    root_dir: EnumProperty(
        name="Root Directory",
        description="Root directory",
        items=_items_root_dir,
        update=_update_root_dir,
    )


class IMESHH_PG_custom_path(PropertyGroup):

    def _update_path(self, context):
        if not self.path:
            return

        self.name = os.path.basename(os.path.dirname(self.path))

    path: StringProperty(
        name="Path",
        description="Path of the local asset",
        subtype="DIR_PATH",
        update=_update_path,
    )

    type: EnumProperty(
        name="Types",
        description="Type of the local asset",
        items=constants.ENUM_ITEMS,
    )


class IMESHH_AP_preferences(AddonPreferences):

    bl_idname = package

    message_cooldown: IntProperty(default=0)

    tab: EnumProperty(
        name="Tab",
        items=(
            ("AUTH", "Authentication", "", "LOCAL", 0),
            ("PATHS", "Paths", "", "FILE_FOLDER", 1),
            ("PREVIEW", "Preview", "", "IMAGE_DATA", 2),
        ),
        default="AUTH",
    )

    username: StringProperty(
        name="Email",
        default="",
    )

    password: StringProperty(
        name="Password",
        subtype="PASSWORD",
        options={"SKIP_SAVE"},
        default="",
    )

    def _update_models_path(self, context):
        if not self.models_path:
            return

        imeshh_lib = context.preferences.filepaths.asset_libraries.get("iMeshh-Models")
        if not imeshh_lib:
            imeshh_lib = context.preferences.filepaths.asset_libraries.new(
                name="iMeshh-Models", directory=os.path.join(self.models_path, "iMeshh-Models")
            )
        save_assets_cat_data(index=0)

    models_path: StringProperty(
        name="Models",
        description="Path to save 3D Model assets",
        subtype="DIR_PATH",
        default=os.path.join(os.path.expanduser("~"), "Documents", "iMeshh"),
        update=_update_models_path,
    )

    def _update_materials_path(self, context):
        if not self.materials_path:
            return

        imeshh_lib = context.preferences.filepaths.asset_libraries.get("iMeshh-Materials")
        if not imeshh_lib:
            imeshh_lib = context.preferences.filepaths.asset_libraries.new(
                name="iMeshh-Materials", directory=os.path.join(self.materials_path, "iMeshh-Materials")
            )
        save_assets_cat_data(index=1)

    materials_path: StringProperty(
        name="Materials",
        description="Path to save Material assets",
        subtype="DIR_PATH",
        default=os.path.join(os.path.expanduser("~"), "Documents", "iMeshh"),
        update=_update_materials_path,
    )

    def _update_geonodes_path(self, context):
        if not self.geonodes_path:
            return

        imeshh_lib = context.preferences.filepaths.asset_libraries.get("iMeshh-Geo-Nodes")
        if not imeshh_lib:
            imeshh_lib = context.preferences.filepaths.asset_libraries.new(
                name="iMeshh-Geo-Nodes", directory=os.path.join(self.geonodes_path, "iMeshh-Geo-Nodes")
            )
        save_assets_cat_data(index=2)

    geonodes_path: StringProperty(
        name="Geo Nodes",
        description="Path to save Geo Nodes assets",
        subtype="DIR_PATH",
        default=os.path.join(os.path.expanduser("~"), "Documents", "iMeshh"),
        update=_update_geonodes_path,
    )

    def _update_fxs_path(self, context):
        if not self.fxs_path:
            return

        imeshh_lib = context.preferences.filepaths.asset_libraries.get("iMeshh-Effects")
        if not imeshh_lib:
            imeshh_lib = context.preferences.filepaths.asset_libraries.new(
                name="iMeshh-Effects", directory=os.path.join(self.fxs_path, "iMeshh-Effects")
            )
        save_assets_cat_data(index=3)

    fxs_path: StringProperty(
        name="Effects",
        description="Path to save Effects assets",
        subtype="DIR_PATH",
        default=os.path.join(os.path.expanduser("~"), "Documents", "iMeshh"),
        update=_update_fxs_path,
    )

    custom_paths: CollectionProperty(type=IMESHH_PG_custom_path)
    active_path_index: IntProperty()
    local: PointerProperty(type=IMESHH_PG_local)

    linked: BoolProperty(
        name="Linked",
        description="Link or append assets",
        default=False,
    )

    import_as_collection: BoolProperty(
        name="Import as Collection",
        description="Import assets as collections. When disabled, objects are imported directly to the scene",
        default=True,
    )

    apply_size: EnumProperty(
        name="Apply Size",
        description="Material size",
        items=(
            ("1K", "1K", "1024x1024", 0),
            ("2K", "2K", "2048x2048", 1),
            ("4K", "4K", "4096x4096", 2),
            ("8K", "8K", "8192x8192", 3),
            ("16K", "16K", "16384x16384", 4),
        ),
        default="4K",
    )

    show_asset_name: BoolProperty(
        name="Show Asset Names",
        description="Show asset names in Browser",
        default=True,
    )

    preview_limit: IntProperty(
        name="Limit",
        description="Limit of assets to show in the preview",
        min=1,
        soft_min=5,
        soft_max=25,
        max=36,
        default=16,
    )

    preview_scale: bpy.props.FloatProperty(
        name="Scale",
        description="Scale of the asset preview",
        min=3,
        soft_max=6,
        default=6,
    )

    popup_scale: bpy.props.FloatProperty(
        name="Popup Scale",
        description="Popup scale of the asset preview",
        min=0.5,
        soft_max=1.5,
        max=2,
        default=1,
    )

    def draw(self, context):
        layout = self.layout
        layout.use_property_decorate = False

        row = layout.row()
        row.prop(self, "tab", expand=True)

        if self.tab == "AUTH":

            box = layout.box()

            if not get_auth_token() or get_token_expiry() < int(datetime.now().timestamp()):
                col = box.column()
                if bpy.app.version >= (4, 2, 0):
                    col.prop(self, "username", text="", placeholder="Email")
                    col.prop(self, "password", text="", placeholder="Password")
                else:
                    col.use_property_split = True
                    col.prop(self, "username")
                    col.prop(self, "password")
                col = box.column()
                col.operator("imeshh.login")

                row = box.row()
                row.alignment = "CENTER"
                row.enabled = False
                col = row.column()
                col.scale_y = 0.7
                col.alignment = "CENTER"
                col.label(text="Google/Facebook login not supported.")
                col.label(text="Use reset password to create password.")

                row = box.row()
                row.alignment = "CENTER"
                row.operator("wm.url_open", text="Reset Password").url = (
                    "https://shop.imeshh.com/my-account/lost-password/"
                )
                row.operator("wm.url_open", text="Create Account").url = "https://shop.imeshh.com/my-account/"
            else:
                col = box.column()
                col.scale_y = 0.8
                split = col.split(factor=0.3, align=True)

                col = split.column(align=True)
                col.enabled = False
                col.alignment = "RIGHT"
                col.label(text="Email")
                if get_subs_info():
                    col.label(text="Product Name")
                    col.label(text="Subscription ID")
                    col.label(text="Status")
                    col.label(text="Start Date")
                    col.label(text="Next Payment Date")
                    col.label(text="Billing Period")
                    col.label(text="Billing Currency")
                    col.label(text="Billing Total")

                col = split.column(align=True)
                col.label(text=f"{self.username}")
                if subs_info := get_subs_info():
                    col.label(text=f'{subs_info.get("product_name", "N/A")}')
                    col.label(text=f'{subs_info.get("subscription_id", "N/A")}')
                    col.label(text=f'{subs_info.get("status", "N/A").title()}')
                    col.label(text=f'{subs_info.get("start_date", "N/A")}')
                    col.label(text=f'{subs_info.get("next_payment_date", "N/A")}')
                    col.label(text=f'{subs_info.get("billing_period", "N/A").title()}')
                    col.label(text=f'{subs_info.get("billing_currency", "N/A")}')
                    col.label(text=f'{subs_info.get("billing_total", "N/A")}')

                col = box.column()
                col.operator("imeshh.logout")

        elif self.tab == "PATHS":
            column = layout.column()
            column.label(text="Do not include in the file paths.:")
            column.label(text="iMeshh-Models, iMeshh-Materials, iMeshh-GeoNodes, iMeshh-Effects")
            column.label(text="Go one folder up.")


            box = column.box()
            col = box.column()
            col.use_property_split = True
            col.alert = not self.models_path
            if bpy.app.version >= (4, 2, 0):
                col.prop(self, "models_path", placeholder="Required")
            else:
                col.prop(self, "models_path")

            col.alert = not self.materials_path
            if bpy.app.version >= (4, 2, 0):
                col.prop(self, "materials_path", placeholder="Required")
            else:
                col.prop(self, "materials_path")

            col.alert = not self.geonodes_path
            if bpy.app.version >= (4, 2, 0):
                col.prop(self, "geonodes_path", placeholder="Required")
            else:
                col.prop(self, "geonodes_path")

            col.alert = not self.fxs_path
            if bpy.app.version >= (4, 2, 0):
                col.prop(self, "fxs_path", placeholder="Required")
            else:
                col.prop(self, "fxs_path")

            # box = column.box()
            col = box.column(heading="Import")
            col.use_property_split = True
            col.prop(self, "linked")
            col.prop(self, "apply_size")
            col.prop(self, "import_as_collection")

            column = layout.column()
            column.label(text="Local Assets")

            row = column.row()
            row.template_list(
                "IMESHH_UL_custom_path",
                "",
                self,
                "custom_paths",
                self,
                "active_path_index",
                item_dyntip_propname="path",
            )
            col = row.column(align=True)
            col.operator("imeshh.custom_path_add", icon="ADD", text="")
            col.operator("imeshh.custom_path_remove", icon="REMOVE", text="")
            col.separator()
            col.operator("imeshh.custom_path_load", icon="FILE_REFRESH", text="")

            if self.custom_paths:
                active_path = self.custom_paths[self.active_path_index]
                col = layout.column()
                col.prop(active_path, "path")

            # Add the save/load buttons
            column = layout.column()
            column.separator()
            
            box = column.box()
            col = box.column()
            col.label(text="Backup & Restore Paths")
            
            row = col.row()
            row.operator("imeshh.save_custom_paths", text="Save File Paths", icon="FILE_TICK")
            row.operator("imeshh.load_custom_paths", text="Load File Paths", icon="FILE_REFRESH")
            
            # Show the save location info
            col = box.column()
            col.scale_y = 0.7
            col.label(text=f"Save location: {os.path.join(os.path.expanduser('~'), 'imeshh', 'custom_paths.json')}", icon="INFO")

        elif self.tab == "PREVIEW":
            box = layout.box()
            col = box.column()
            col.use_property_split = True
            col.prop(self, "preview_limit")
            col.prop(self, "preview_scale")
            col.prop(self, "popup_scale")
            col.prop(self, "show_asset_name")

        col = layout.column()
        col.operator("wm.save_userpref")


@bpy.app.handlers.persistent
def _load_preferences(dummy):
    if not os.path.exists(PATH_PREFS_FILE):
        return

    prefs = preferences()

    with open(PATH_PREFS_FILE, "r", encoding="utf-8") as file:
        prefs_data = json.load(file)
        prefs.username = prefs_data.get("username", "")

        prefs.models_path = prefs_data.get("models_path", "")
        prefs.materials_path = prefs_data.get("materials_path", "")
        prefs.geonodes_path = prefs_data.get("geonodes_path", "")
        prefs.fxs_path = prefs_data.get("fxs_path", "")
        prefs.linked = prefs_data.get("linked", False)
        prefs.apply_size = prefs_data.get("apply_size", "4K")
        prefs.import_as_collection = prefs_data.get("import_as_collection", True)

        prefs.preview_limit = prefs_data.get("preview_limit", 25)
        prefs.preview_scale = prefs_data.get("preview_scale", 6)
        prefs.popup_scale = prefs_data.get("popup_scale", 16)
        prefs.show_asset_name = prefs_data.get("show_asset_name", False)


classes = [
    IMESHH_PG_folder,
    IMESHH_PG_local,
    IMESHH_PG_custom_path,
    IMESHH_AP_preferences,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # bpy.app.handlers.load_post.append(_load_preferences)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    # if _load_preferences in bpy.app.handlers.load_post:
    #     bpy.app.handlers.load_post.remove(_load_preferences)