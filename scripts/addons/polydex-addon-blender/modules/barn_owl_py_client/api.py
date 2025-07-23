# #### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import configparser
from dataclasses import dataclass
import json
import os
import requests
from typing import Dict, List, Optional, Union
from urllib.request import getproxies

REQUEST_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
}

TIMEOUT = 20  # Request timeout in seconds.

# TODO(Omer): Request status, timeout implementations

ERR_ALPHA_ENDED = "app_disabled"


@dataclass
class ApiResponse():
    """Represents the APIResponse from the BarnOwl server"""
    status: str
    message: str
    error_code: Optional[str] = None
    results: Optional[Union[List, Dict]] = None
    error: Optional[str] = None


class ApiClient():
    api_url: str = "http://127.0.0.1:8000/"

    token: str = None

    login_token: str = None

    meta: Dict = {}
    barnowl_detected: bool = False
    session_id: Optional[str] = None
    session_url: Optional[str] = None
    config: Optional[configparser.ConfigParser] = None

    alpha_ended: bool = False

    def __init__(self,
                 client_name: str,
                 client_version: str,
                 host_software_version: str,
                 client_os_name: str,
                 client_os_version: str
                 ):
        self.meta = {
            "client_name": client_name,
            "client_version": client_version,
            "host_software_version": host_software_version,
            "client_os_name": client_os_name,
            "client_os_version": client_os_version,
            "current_view": ""
        }
        self.session_id = None
        self.session_url: str = None
        self.socket_host: str = ""
        self.socket_port: int = -1

        self.config_path = self.get_config_path()
        did_load = self.load_config_data()
        if did_load and self.config is not None:
            self.update_port(self.config)

    def _get_config_path(self) -> str:
        windows = r"%APPDATA%"
        windows = os.path.expandvars(windows)
        if "APPDATA" not in windows:
            return windows

        user_directory = os.path.expanduser("~")

        macos = os.path.join(user_directory, "Library", "Application Support")
        if os.path.exists(macos):
            return macos

        linux = os.path.join(user_directory, ".config")
        if os.path.exists(linux):
            return linux

        return user_directory

    def get_config_path(self) -> str:
        return os.path.join(self._get_config_path(), "Polydex", "settings.ini")

    def get_meta_dict(self) -> Dict:
        return self.meta

    def is_barnowl_detected(self) -> bool:
        return self.barnowl_detected

    def has_alpha_ended(self) -> bool:
        return self.alpha_ended

    def has_session_id(self) -> bool:
        return self.session_id is not None

    def is_logged_in(self) -> bool:
        """Returns whether or not the user is currently logged in."""
        return self.is_barnowl_detected() and self.has_session_id()

    def load_config_data(self) -> bool:
        """Loads vars like port to use, returns false if not found."""
        if not os.path.isfile(self.config_path):
            print("Could not find config:", self.config_path)
            return False

        config = configparser.ConfigParser()
        config.optionxform = str

        try:
            config.read(self.config_path)
        except configparser.Error as e:
            print(f"Failed to load config from {self.config_path}")
            print(e)
            return False

        print(f"Loaded config from {self.config_path}")
        self.config = config
        return True

    def update_port(self, config: configparser.ConfigParser) -> None:
        try:
            port = config.get("default", "local_api_port")
        except configparser.NoSectionError:
            print("No default section in config")
            return
        except configparser.NoOptionError:
            print("No local port in config")
            return

        if port == "":  # The default
            return

        try:
            port_int = int(port)
        except ValueError as e:
            print("Could not load custom port:", e)
            return
        self.api_url = f"http://127.0.0.1:{port_int}/"

    def register_client(self) -> ApiResponse:
        """Send a register request and get back socket information"""
        self.session_id = None
        self.session_url = None

        res = self._request("session/register",
                            method="POST",
                            payload=self.meta,
                            headers=REQUEST_HEADERS,
                            add_session_id=False)
        if res.status == "success":
            self.session_id = res.results["session_id"]
            self.socket_host = res.results["socket_host"]
            self.socket_port = int(res.results["socket_port"])
            self.session_url = f"http://{self.socket_host}:{self.socket_port}/"

        return res

    def terminate_client(self) -> ApiResponse:
        """Tells the server the intent to explicitly terminate a connection.

        This takes care of ending the socket connection as well as sharing
        for even non-socket based that it should be removed from the list in
        the standalone UI
        """
        res = self._request("session/terminate",
                            method="POST",
                            payload=self.meta,
                            headers=REQUEST_HEADERS,
                            add_session_id=True)
        return res

    def status(self) -> ApiResponse:
        """Check if alpha has ended and if it is logged in"""
        payload = {}
        res = self._request("auth/status",
                            method="POST",
                            payload=payload,
                            headers=REQUEST_HEADERS,
                            add_session_id=False,
                            timeout=5.00)
        if res.status == "fail" or res.results is None:
            if res.error_code == ERR_ALPHA_ENDED:
                self.alpha_ended = True

        return res

    def check_barnowl(self) -> bool:
        """Check if barnowl server is running and if it is logged in"""
        status = self.status()
        is_logged_in = status.error is None
        state_change = False
        if not self.barnowl_detected and is_logged_in:
            self.register_client()
            self.barnowl_detected = True
            state_change = True
        elif self.barnowl_detected and not is_logged_in:
            self.barnowl_detected = False
            state_change = True
        return state_change

    def import_asset(self, asset_id: int, method: str) -> ApiResponse:
        """Register an import asset event

        Args:
            asset_id: Asset which was imported
            method: What method or final format the asset was import like, e.g.
                    material, image, datablock, object, sky
        """
        payload = {
            "asset_id": asset_id,
            "method": method
        }
        res = self._request("event/import_asset",
                            method="POST",
                            headers=REQUEST_HEADERS,
                            payload=payload)
        return res

    def get_asset_details(self,
                          asset_id: int
                          ) -> ApiResponse:
        """Get asset details for a specific asset

        Args:
            asset_id: The id of the asset to get details for
        """
        payload = {
            "asset_id": asset_id
        }
        res = self._request("assets/details",
                            method="POST",
                            headers=REQUEST_HEADERS,
                            payload=payload)
        # if res.status != "success":
        #    print("get_asset_details FAILED: ", res.error_code)

        return res

    def update_top_level_folder(self, path: str) -> ApiResponse:
        """Trigger a re-process of a specific folder

        Args:
            path: Which folder to re-process
        """
        payload = {
            "path": path
        }
        res = self._request("directories/update",
                            method="POST",
                            headers=REQUEST_HEADERS,
                            payload=payload)
        if res.status != "success":
            print("update_top_level_folder FAILED: ", res.error_code)

        return res

    def get_all_top_level_folders(self) -> ApiResponse:
        """Get all and only the top-level dirs"""
        payload = {}
        res = self._request("directories",
                            method="POST",
                            headers=REQUEST_HEADERS,
                            payload=payload)
        if res.status != "success":
            print("get_all_top_level_folders FAILED: ", res.error_code)

        return res

    def get_folder_asset_count(self, paths: List) -> ApiResponse:
        """Get the asset count of a specific folder

        Args:
            paths: List of folder paths to get the asset count for
        """
        payload = {
            "directory_paths": paths
        }

        res = self._request("assets/count",
                            method="POST",
                            headers=REQUEST_HEADERS,
                            payload=payload)
        if res.status != "success":
            print("get_folder_asset_count FAILED: ", res.error_code)

        return res

    def get_assets(self,
                   path: str = "",
                   page_number: int = 1,
                   assets_per_page: int = 500,
                   search_query: str = "",
                   sort_option: str = "",
                   reverse_order: bool = False,
                   applied_filters: Dict = {},
                   ) -> ApiResponse:
        """Get the assets for a specific page for a folder

        Args:
            path: Folder path where to get the assets from
            page_number: Which page to get the assets from
            assets_per_page: Max number of assets per page
            search_query: What is being searched for
            sort_option: NOT USED YET
            reverse_order: NOT USED YET
            applied_filters: NOT USED YET
        """
        payload = {
            "folder_path": path,
            "page_number": page_number,
            "assets_per_page": assets_per_page,
            "search_query": search_query,
            "sort_option": sort_option,
            "reverse_order": reverse_order,
            "applied_filters": applied_filters
        }

        res = self._request("assets",
                            method="POST",
                            headers=REQUEST_HEADERS,
                            payload=payload)
        if res.status != "success":
            print("get_all_top_level_folders FAILED: ", res.error_code)

        return res

    # TODO(Omer): to be implemented
    def open_poliigon_webpage():
        pass

    def _request_url(self,
                     url: str,
                     method: str,
                     payload: Dict = {},
                     headers: Optional[Dict] = None,
                     do_invalidate: bool = True,
                     skip_mp: bool = False,
                     timeout: float = TIMEOUT
                     ) -> ApiResponse:
        """Request a repsonse from an api.
        Args:
            url: The URL to request from.
            method: Type of http request, e.g. POST or GET.
            payload: The body of the request.
            headers: Prepopulated headers for the request including auth.
        """

        try:
            proxies = getproxies()
            if method == "POST":
                res = requests.post(url,
                                    data=json.dumps(payload),
                                    headers=headers,
                                    proxies=proxies,
                                    timeout=timeout)
            elif method == "GET":
                res = requests.get(url,
                                   headers=headers,
                                   proxies=proxies,
                                   timeout=timeout)
            else:
                raise ValueError("raw_request input must be GET or POST")
        except requests.exceptions.ConnectionError as e:
            return ApiResponse(status="fail",
                               message="connection error",
                               error_code="server_error",
                               error=str(e))
        except requests.exceptions.Timeout as e:
            return ApiResponse(status="fail",
                               message="request timed out",
                               error_code="request_timeout",
                               error=str(e))
        except requests.exceptions.ProxyError as e:
            return ApiResponse(status="fail",
                               message="proxy error",
                               error_code="bad_request",
                               error=str(e))
        res_json = json.loads(res.text)
        res_bob = ApiResponse(status=res_json.get("status", "NO STATUS"),
                              message=res_json.get("message", "NO MESSAGE"),
                              results=res_json.get("results", None),
                              error_code=res_json.get("error_code", None),
                              error=res_json.get("error_code", None))
        return res_bob

    def _request(self,
                 path: str,
                 method: str,
                 payload: Dict = {},
                 headers: Optional[Dict] = None,
                 do_invalidate: bool = True,
                 api_v2: bool = False,
                 skip_mp: bool = False,
                 add_session_id: bool = True,
                 timeout: float = TIMEOUT
                 ) -> ApiResponse:
        """Request a repsonse from an api.
        Args:
            path: The api endpoint path without the url domain.
            method: Type of http request, e.g. POST or GET.
            payload: The body of the request.
            headers: Prepopulated headers for the request including auth.
        """

        # print("_request: ", path)

        if add_session_id:
            payload["session_id"] = self.session_id
            # print(self.session_id)

        url = self.api_url + path
        return self._request_url(url,
                                 method=method,
                                 payload=payload,
                                 headers=headers,
                                 do_invalidate=do_invalidate,
                                 skip_mp=skip_mp,
                                 timeout=timeout)

    def _signal_event(self, event_name: str, payload: Dict) -> ApiResponse:
        """Reusable entry to send an event
        (user's opt-in then gets handled by Polydex server).
        """

        return self._request(
            path=f"event/{event_name}",
            method="POST",
            payload=payload)

    def signal_import_asset(self, asset_id: int, method: str):
        """Sends import asset event if opted in."""
        payload = {
            "asset_id": asset_id,
            "method": method
        }
        res = self._signal_event("import_asset", payload=payload)
        return res
