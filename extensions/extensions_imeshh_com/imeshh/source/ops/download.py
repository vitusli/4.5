import os
import re
import threading
import time
import zipfile

import bpy
import requests
from bpy.props import IntProperty, StringProperty
from bpy.types import Operator

from ..utils.addon import preferences, tag_redraw
from ..utils.auth import HEADERS, URL_DOWNLOAD, get_response
from ..utils.product import get_assets_path, get_license_type, get_products, get_version


# Simple thread-safe status holder instead of a queue
class StatusHolder:
    def __init__(self):
        self.lock = threading.Lock()
        self.status = ""
        self.progress = 0.0
        self.has_update = False

    def set(self, status, progress):
        with self.lock:
            self.status = status
            self.progress = progress
            self.has_update = True

    def get(self):
        with self.lock:
            if not self.has_update:
                return None
            result = (self.status, self.progress)
            self.has_update = False
            return result


class IMESHH_OT_download(Operator):
    """Download asset from iMeshh"""

    bl_label = "Download"
    bl_idname = "imeshh.download"
    bl_options = {"REGISTER", "INTERNAL"}

    product_id: IntProperty(options={"SKIP_SAVE"})
    download_id: StringProperty(options={"SKIP_SAVE"})

    _finished = False
    _error = None
    _item = None

    @classmethod
    def poll(cls, context):
        return get_assets_path(context) and not len(context.window_manager.imeshh.download_list) >= 6

    @classmethod
    def description(cls, context, properties):
        props = context.scene.imeshh

        if not get_assets_path(context):
            return f"Set the {props.asset_type} path in the addon preferences"

        products = get_products(props)
        if product := next((p for p in products if p.get("id") == properties.product_id), None):
            return (
                f'{product.get("name")}\n\n'
                f'Blender                 {get_version(product.get("blender_version"))}\n'
                f'Polygon Count     {product.get("polygon_count")}\n'
                f'Dimensions          {product.get("dimensions")}\n'
                f'Subdividable        {product.get("subdividable")}\n'
                f'License Type       {get_license_type(product.get("license-type"))}'
            )
        return "No asset found"

    def execute(self, context):
        self.prefs = preferences()
        self.props = context.scene.imeshh
        self.wm = context.window_manager
        self._finished = False
        self._error = None
        self._item = None
        self._status = StatusHolder()  # Use our custom status holder

        # Get product info
        products = get_products(self.props)
        self.product = next((p for p in products if p.get("id") == self.product_id), None)
        if self.product is None:
            self.report({"WARNING"}, "Product not found")
            return {"CANCELLED"}

        # Basic product info
        self.product_name = self.product.get("name")
        self.asset_type = self.product.get("asset_type")
        self.product_category = self.product.get("categories").get("name")
        self.product_subcategory = self.product.get("sub-categories")[0].get("name")

        # Find download info
        downloads = self.product.get("downloads", [])
        if not downloads:
            self.report({"WARNING"}, "No downloads available")
            return {"CANCELLED"}

        self.download_data = next(
            (d for d in downloads if any(key in d.get("name", "") for key in ["Blender", "124k", "1+2+4k", "1-2-4k"])),
            downloads[0],
        )

        if not self.download_id:
            self.download_id = self.download_data.get("id")

        # Get the current date as default
        # current_date = datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        # self.date_modified = self.product.get("date_modified", current_date).replace(":", "-")

        # Set up asset paths
        asset_type_map = {
            "model": ("models_path", "iMeshh-Models"),
            "material": ("materials_path", "iMeshh-Materials"),
            "geonode": ("geonodes_path", "iMeshh-Geo-Nodes"),
            "fx": ("fxs_path", "iMeshh-Effects"),
        }
        path_attr, folder_name = asset_type_map.get(self.asset_type, ("models_path", "iMeshh-Models"))
        self.asset_folder = os.path.join(
            getattr(self.prefs, path_attr), folder_name, self.product_category, self.product_subcategory
        )

        # Create download item if needed
        try:
            existing_ids = []
            for item in self.wm.imeshh.download_list:
                try:
                    existing_ids.append(item.product_id)
                except Exception as e:
                    pass

            if self.product_id not in existing_ids:
                self._item = self.wm.imeshh.download_list.add()
                self._item.name = self.product_name
                self._item.product_id = self.product_id
                self._item.status = "Fetching..."
                self._item.progress = 0.0

                threading.Thread(target=self.download_thread, daemon=True).start()
        except Exception as e:
            print(f"ERROR: Creating download: {e}")
            self.report({"WARNING"}, f"Error starting download: {str(e)}")
            return {"CANCELLED"}

        self._timer = self.wm.event_timer_add(0.1, window=context.window)
        self.wm.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    # Completely avoid using self._item in modal
    def modal(self, context, event):
        if event.type == "TIMER":
            # Safe status update
            update = None
            try:
                update = self._status.get()
            except Exception as e:
                pass

            # Only update UI if we have new status
            if update:
                status, progress = update
                # Find the item by product_id instead of using direct reference
                try:
                    for item in context.window_manager.imeshh.download_list:
                        if item.product_id == self.product_id:
                            item.status = status
                            item.progress = progress
                            break
                    # Request redraw after update
                    tag_redraw()
                except Exception as e:
                    pass

        # Clean up when finished
        if self._finished:
            try:
                context.window_manager.event_timer_remove(self._timer)
            except ValueError as e:
                pass

            # Handle completion
            if self._error:
                self.report({"WARNING"}, self._error)
                # Use product_id to identify the download item
                self.cleanup_by_product_id()
                return {"CANCELLED"}

            # Use product_id to identify the download item
            self.cleanup_by_product_id()
            self.report({"INFO"}, f"Asset '{self.product_name}' downloaded successfully!")
            return {"FINISHED"}

        return {"PASS_THROUGH"}

    # New method to avoid using self._item
    def cleanup_by_product_id(self):
        try:
            # Find and update item by product_id
            for item in self.wm.imeshh.download_list:
                if item.product_id == self.product_id:
                    item.status = ""
                    item.progress = -1
                    break

            # Check if all items are done
            if all(i.status == "" and i.progress == -1 for i in self.wm.imeshh.download_list):
                self.wm.imeshh.download_list.clear()
        except Exception as e:
            pass

    def update_status(self, status, progress):
        try:
            self._status.set(status, progress)
        except Exception as e:
            pass

    def download_thread(self):
        try:
            self.download_process()
        except Exception as e:
            self._error = f"Download error: {str(e)}"
            print(f"Download error: {e}")
        finally:
            self._finished = True

    def download_process(self):
        self.update_status("Fetching...", 0)

        # Get download URL
        try:
            params = {"product_id": self.product_id, "download_id": self.download_id}
            response = get_response(URL_DOWNLOAD, params)
            data = response.json()

            if response.status_code != 200:
                self._error = data.get("message", "Download error")
                self.update_status("Error", -1)
                return

            download_url = data.get("download_url")
            if not download_url:
                self._error = "No download URL provided"
                self.update_status("Error", -1)
                return
        except Exception as e:
            self._error = f"Failed to get download info: {str(e)}"
            self.update_status("Error", -1)
            return

        # Setup file paths
        try:
            os.makedirs(self.asset_folder, exist_ok=True)
            zip_file_name = os.path.basename(download_url)
            zip_file_path = os.path.join(self.asset_folder, zip_file_name)

            # Extract folder name from zip name
            folder_name = re.sub(
                r"(?i)(?:_blender|gltf|(?:_?(?:124|4|8|16|32)k)|1[+\-]2[+\-]4k|\.zip)", "", zip_file_name
            )
            asset_folder_path = os.path.join(self.asset_folder, folder_name)
        except Exception as e:
            self._error = f"Failed to create folders: {str(e)}"
            self.update_status("Error", -1)
            return

        # Download file
        try:
            self.update_status("Downloading...", 0)
            with requests.get(download_url, headers=HEADERS, stream=True, timeout=30) as response:
                response.raise_for_status()
                total_size = int(response.headers.get("Content-Length", 0))
                downloaded = 0

                with open(zip_file_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            progress = downloaded / total_size if total_size > 0 else 0
                            self.update_status("Downloading...", progress)
        except Exception as e:
            self._error = f"Download failed: {str(e)}"
            self.update_status("Error", -1)
            if os.path.exists(zip_file_path):
                os.remove(zip_file_path)
            return

        # Extract files
        try:
            self.update_status("Extracting...", 0)
            with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
                files = zip_ref.namelist()
                total = len(files)

                # Determine extract location
                top_level = {f.split("/")[0] for f in files}
                extract_to = self.asset_folder if len(top_level) == 1 else asset_folder_path
                os.makedirs(extract_to, exist_ok=True)

                for i, file in enumerate(files):
                    zip_ref.extract(file, extract_to)
                    self.update_status("Extracting...", (i + 1) / total)

            # if os.path.exists(asset_folder_path):
            #     # Create new folder name with date
            #     folder_name = os.path.basename(asset_folder_path)
            #     new_folder_name = f"{folder_name}_{self.date_modified}"
            #     new_folder_path = os.path.join(os.path.dirname(asset_folder_path), new_folder_name)

            #     # Rename the folder
            #     os.rename(asset_folder_path, new_folder_path)

            os.remove(zip_file_path)  # Clean up zip file
            self.update_status("Downloaded", 1.0)
            time.sleep(0.5)  # Allow UI to update
            self.update_status("", -1)
        except Exception as e:
            self._error = f"Extraction failed: {str(e)}"
            self.update_status("Error", -1)


classes = (IMESHH_OT_download,)
register, unregister = bpy.utils.register_classes_factory(classes)
