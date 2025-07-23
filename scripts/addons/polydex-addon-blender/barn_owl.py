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

from enum import IntEnum
import os
from queue import Queue
from threading import Event, Thread
from typing import Dict, List, Optional, Tuple

import bpy

from .modules.poliigon_core.api_remote_control_params import (
    CATEGORY_ALL,
    IDX_PAGE_ACCUMULATED,
    KEY_TAB_MY_ASSETS,
    PAGE_SIZE_ACCUMULATED)
from .modules.poliigon_core.assets import AssetData
from .modules.poliigon_core.multilingual import _t
from .modules.barn_owl_py_client.api import (
    ApiClient,
    ApiResponse)
from .modules.barn_owl_py_client.client import Client
from .modules.barn_owl_py_client.bob_functions import (
    bo_asset_data_to_ai_asset_data)
from .dialogs.utils_dlg import (
    get_ui_scale,
    wrapped_label)
from .build import PREFIX_OP


API_SUCCESS = "success"
API_FAIL = "fail"


GET_ASSETS_PAGE_SIZE = 500


class BO_FOLDER_STATUS(IntEnum):
    UNKNOWN = 0
    IS_PROCESSING = 1
    COMPLETE = 2


class BO_STATUS(IntEnum):
    NOT_CONNECTED = 0
    CLIENT_REGISTERED = 1
    CLIENT_CONNECTED = 2
    CLIENT_WAITING_FOR_DIRS = 3
    CLIENT_WAITING_FOR_SEARCH = 4
    CLIENT_IS_LISTENING = 5


class BOPathEntry():
    def __init__(
        self,
        *,
        bo_listener,  # : BOSocketListener
        library,  # : BOLibrary
        parent,  # : BOPathEntry
        path: str,
        depth: int = 0,
        child_init: bool = False
    ):
        self.bo_listener = bo_listener
        self.library = library
        self.parent = parent
        self.path: str = path
        self.depth: int = depth
        self.asset_index_key: str = str(hash(path))

        library.dict_path_entries[self.asset_index_key] = self

        basename = os.path.basename(path)
        if basename == "":
            basename = os.path.basename(os.path.dirname(path))

        self.name: str = basename
        self.asset_count: int = -1
        # None means not scanned, yet, otherwise empty list
        self.children: Optional[List[BOPathEntry]] = None

        if child_init:
            self._init_children(child_init=True)

    def __iter__(self):
        yield self
        if self.children is None:
            return
        for _child in self.children:
            yield from _child.__iter__()

    def _init_children(self, child_init: bool = False) -> None:
        self.children = []
        if not os.path.isdir(self.path):
            return
        with os.scandir(self.path) as it:
            for _entry in it:
                # TODO(Andreas): Should we ignore hidden dirs?
                if not _entry.is_dir():
                    continue
                path_subdir = os.path.join(self.path, _entry.name) + "/"
                self.children.append(
                    BOPathEntry(
                        bo_listener=self.bo_listener,
                        library=self.library,
                        parent=self,
                        path=path_subdir,
                        depth=self.depth + 1,
                        child_init=child_init
                    )
                )

    def get_children_names(self, path_names: List[str]) -> List[str]:
        if self.children is None:
            self._init_children(child_init=False)

        if len(path_names) == 0:
            children_names = [_child.name for _child in self.children]
            return children_names

        branch_name = path_names[0]
        for _child in self.children:
            if _child.name != branch_name:
                continue
            return _child.get_children_names(path_names[1:])
        # Path not found
        return []

    def print_lib_tree(
        self,
        print_counts: bool = False,
        print_keys: bool = False,
        indent: int = 0
    ) -> None:
        text = f"{' ' * indent}{self.name}"
        if print_counts:
            text = f"{text} ({self.asset_count})"
        if print_keys:
            text = f"{text} - {self.asset_index_key}"
        print(text)
        if self.children is None:
            return
        for _child in self.children:
            _child.print_lib_tree(print_counts=print_counts, indent=indent + 4)

    def get_assets(self, search: str = ""):
        self.bo_listener.schedule_get_assets(self.path, search)

    def get_asset_count(self) -> int:
        return self.asset_count

    def get_path_entries(self) -> List:  # List[BOPathEntry]
        list_path_entries = []
        path_entry = self
        while path_entry is not None:
            list_path_entries.insert(0, path_entry)
            path_entry = path_entry.parent
        return list_path_entries


class BOLibrary():
    def __init__(self, bo_listener):
        self.bo_listener = bo_listener

        self.dict_path_entries: Dict[str, BOPathEntry] = {}

        self.status: BO_FOLDER_STATUS = BO_FOLDER_STATUS.UNKNOWN
        self.error = None
        self.path_tree: Optional[BOPathEntry] = None
        self.asset_count = -1
        self.name: str = ""
        self.enabled: bool = True

    def init_from_dict(self, lib_entry: Dict, child_init: bool = False) -> bool:
        self.error = lib_entry.get("error", None)
        path_root = lib_entry.get("directory_path", "")
        self.path_tree = BOPathEntry(
            bo_listener=self.bo_listener,
            library=self,
            parent=None,
            path=path_root,
            child_init=child_init)

        if not child_init:
            # At least init first level
            self.path_tree._init_children(child_init=False)

        self.name = os.path.basename(path_root)
        if self.name == "":
            self.name = os.path.basename(os.path.dirname(path_root))
        self.asset_count = lib_entry.get("asset_count", 0)
        if lib_entry.get("is_directory_processing", False):
            self.status = BO_FOLDER_STATUS.IS_PROCESSING
        else:
            self.status = BO_FOLDER_STATUS.COMPLETE

        if self.status == BO_FOLDER_STATUS.COMPLETE:
            self.update_asset_counts()

        self.enabled = os.path.isdir(path_root)
        return True

    def __iter__(self):
        return self.path_tree.__iter__()

    def is_processing(self) -> bool:
        return self.status == BO_FOLDER_STATUS.IS_PROCESSING

    def get_children_names(self, path_names: List[str]) -> List[str]:
        return self.path_tree.get_children_names(path_names)

    def get_all_paths(self) -> List[str]:
        paths = []
        for _path_entry in self:
            paths.append(_path_entry.path)
        return paths

    def get_root_path(self) -> Optional[str]:
        if self.path_tree is None:
            return None
        return self.path_tree.path

    def update_asset_counts(self) -> None:
        paths = self.get_all_paths()
        # TODO(Patrick): Resolve this workaround better.
        # But we should not be ever trying to bulk request 100% of all paths
        # on barn out at a moment in any scenario, we should only fetch
        # data for ONE directory at a time.
        # paths = paths[:800]  # first N due to server-side variables limit.

        # NOTE: Currently we receive wrong asset counts for subdirs.
        #       This could be worked around by reversing the path list.
        #       But as it is supposed to be fixed on BarnOwl's end, we
        #       live with wrong counts for the moment.
        # paths.reverse()
        res = self.bo_listener.api_client.get_folder_asset_count(paths)
        if res.status != API_SUCCESS:
            return
        asset_counts = res.results.get("asset_counts", {})
        for _path_entry in self:
            _path_entry.asset_count = asset_counts.get(_path_entry.path, 0)

    def get_assets(self) -> None:
        if self.path_tree is None:
            return

        self.path_tree.get_assets()

    def get_asset_count(self) -> int:
        return self.asset_count

    def get_name_and_id(self) -> Tuple[str, str]:
        if self.path_tree is not None:
            asset_index_key = self.path_tree.asset_index_key
        else:
            asset_index_key = None

        return self.name, asset_index_key

    def get_path_key_list(self, path: str) -> List[str]:
        list_asset_index_keys = []

        for _path_entry in self:
            if path.startswith(_path_entry.path):
                list_asset_index_keys.append(_path_entry.asset_index_key)

        return list_asset_index_keys

    def get_path_key_slug(self, path: str) -> str:
        list_asset_index_keys = self.get_path_key_list(path)
        slug = "$".join(list_asset_index_keys)
        return slug

    def get_path_entry_by_key(
            self, asset_index_key: str) -> Optional[BOPathEntry]:
        return self.dict_path_entries.get(asset_index_key, None)

    def print_lib_tree(
        self,
        print_counts: bool = False,
        print_keys: bool = False
    ) -> None:
        self.path_tree.print_lib_tree(
            print_counts=print_counts, print_keys=print_keys)


class BOLibraries():
    def __init__(self, bo_listener):
        self.bo_listener = bo_listener
        self.libraries: List[BOLibrary] = []

    def __iter__(self):
        yield from self.libraries

    def init_from_response(
        self,
        res: ApiResponse,
        add_only: bool = False,
        child_init: bool = False
    ) -> None:
        if res.status != API_SUCCESS:
            # TODO(Andreas): Flush potentially existing list, here?
            return

        if add_only:
            libraries_new = self.libraries.copy()
        else:
            libraries_new = []

        for _lib_dict in res.results:
            if add_only:
                path_lib = _lib_dict.get("directory_path", "")
                lib, _ = self.get_library_by_path(path_lib)
                if lib is not None:
                    continue

            lib = BOLibrary(self.bo_listener)
            is_initialized = lib.init_from_dict(
                _lib_dict, child_init=child_init)
            if not is_initialized:
                continue
            libraries_new.append(lib)

        self.libraries = libraries_new

    def remove_library(self, path: str) -> Optional[BOLibrary]:
        for _lib in self.libraries.copy():
            if _lib.path_tree.path != path:
                continue
            self.libraries.remove(_lib)
            return _lib
        return None

    def enable_library(
            self, path: str, enable: bool = True) -> Optional[BOLibrary]:
        for _lib in self.libraries.copy():
            if _lib.path_tree.path != path:
                continue
            _lib.enabled = enable
            return _lib
        return None

    def is_server_gathering_data(self) -> bool:
        for _lib in self.libraries:
            if _lib.is_processing():
                return True
        return False

    def get_library_by_path(
        self,
        path: str
    ) -> Tuple[Optional[BOLibrary], Optional[BOPathEntry]]:
        result_lib = None
        for _lib in self.libraries:
            path_lib_root = _lib.get_root_path()
            if path.startswith(path_lib_root):
                result_lib = _lib
                break
        if result_lib is None:
            return None, None

        result_path_entry = None
        for _path_entry in result_lib:
            if path == _path_entry.path:
                result_path_entry = _path_entry
                break

        return result_lib, result_path_entry

    def get_all_library_names_and_ids(self) -> Dict[str, int]:
        lib_names = {}
        for _lib in self.libraries:
            name, asset_index_key = _lib.get_name_and_id()
            lib_names[name] = asset_index_key
        return lib_names

    def get_path_key_list(self, path: str) -> List[str]:
        _, path_entry_leave = self.get_library_by_path(path)
        if path_entry_leave is None:
            # path not found
            return []

        path_entries = path_entry_leave.get_path_entries()
        path_key_list = [_path_entry.asset_index_key
                         for _path_entry in path_entries]
        return path_key_list

    def get_path_key_slug(self, path: str) -> str:
        path_key_list = self.get_path_key_list(path)
        slug = "$".join(path_key_list)
        return slug

    def get_path_entry_by_key(
            self, asset_index_key: str) -> Optional[BOPathEntry]:
        for _lib in self.libraries:
            path_entry = _lib.get_path_entry_by_key(asset_index_key)
            if path_entry is not None:
                return path_entry
        return None

    def get_assets(self) -> None:
        for _lib in self.libraries:
            _lib.get_assets()

    def get_asset_count(self) -> None:
        num_assets = 0
        for _lib in self.libraries:
            num_assets += _lib.get_asset_count()
        return num_assets


class BOSocketListener():
    def __init__(self, cTB):
        self.cTB = cTB

        self.ev_wait: Event = Event()
        self.status: BO_STATUS = BO_STATUS.NOT_CONNECTED

        self.bo_listener_running: bool = False
        self.thd_bo_listener: Thread = None

        self.bo_gatherer_running: bool = False
        self.thd_bo_gatherer: Thread = None
        self.queue_gather_lib_path: Queue = Queue()

        self.bo_libraries: BOLibraries = BOLibraries(self)

        addon_version_s = (f"{cTB.addon_version[0]}."
                           f"{cTB.addon_version[1]}."
                           f"{cTB.addon_version[2]}")
        self.bo_client: Client = Client(
            client_name="blender",
            client_version=addon_version_s,
            host_software_version=".".join([str(val) for val in bpy.app.version]),
            do_start=False)
        # Do not store a reference to SocketClient, here, it may change...
        self.api_client: ApiClient = self.bo_client.api_client

    def start(self) -> None:
        print("Running BOB start")
        self.bo_listener_running = False
        self.thd_bo_listener: Thread = Thread(
            target=self._thread_listener,
        )
        self.thd_bo_listener.daemon = 1
        self.thd_bo_listener.start()

        self.bo_gatherer_running = False
        self.thd_bo_gatherer: Thread = Thread(
            target=self._thread_gatherer,
        )
        self.thd_bo_gatherer.daemon = 1
        self.thd_bo_gatherer.start()

    def shutdown(self) -> None:
        print("Running BOB shutdown")
        self.bo_gatherer_running = False
        self.queue_gather_lib_path.put(("SHUTDOWN_GATHERER", "", 0))

        self.bo_listener_running = False
        self.ev_wait.set()
        self.bo_client.stop()

    def schedule_get_assets(
            self, path: str, search: str = "", idx_page: int = 0) -> None:
        self.status = BO_STATUS.CLIENT_WAITING_FOR_SEARCH

        self.queue_gather_lib_path.put((path, search, idx_page))

    def _callback_register(self, json_message: Dict) -> None:
        print("_callback_register")

    def _callback_log_in_with_web(self, json_message: Dict):
        print("_callback_log_in_with_web")

    def _callback_add_top_level_folder(self, json_message: Dict):
        print("_callback_add_top_level_folder")
        results = json_message.get("results", {})
        path_new_lib = results.get("folder_path", "")
        if path_new_lib == "":
            return

        self.status = BO_STATUS.CLIENT_WAITING_FOR_DIRS
        self.ev_wait.set()
        self.schedule_get_assets(path_new_lib, "")

    def _callback_toplevel_directory_unconnected(
            self, json_message: Dict, do_remove=True):
        print("_callback_toplevel_directory_unconnected")
        self._callback_remove_top_level_folder(json_message, do_remove=False)

    def _callback_remove_top_level_folder(
            self, json_message: Dict, do_remove=True):
        print("_callback_remove_top_level_folder")
        results = json_message.get("results", {})
        path_removed_lib = results.get("folder_path", "")
        if path_removed_lib == "":
            return
        if do_remove:
            lib_removed = self.bo_libraries.remove_library(path_removed_lib)
        else:
            lib_removed = self.bo_libraries.enable_library(
                path_removed_lib, enable=False)
        if lib_removed is None:
            print("_callback_remove_top_level_folder: Library not found")
            return
        asset_index_key_lib = lib_removed.path_tree.asset_index_key
        keys_in_lib = [_path_entry.asset_index_key
                       for _path_entry in lib_removed]

        if self.cTB.vAssetType in keys_in_lib:
            print("_callback_remove_top_level_folder: SWITCH TO ROOT")
            self.cTB.vAssetType = CATEGORY_ALL
            self.cTB.vActiveCat = [CATEGORY_ALL]
            self.cTB.settings["category"][KEY_TAB_MY_ASSETS] = [CATEGORY_ALL]
            self.cTB.vPage[KEY_TAB_MY_ASSETS] = 0

        # Remove all assets coming from this lib
        query_key_lib = (
            KEY_TAB_MY_ASSETS,
            None,
            asset_index_key_lib,
            None,
            IDX_PAGE_ACCUMULATED,
            PAGE_SIZE_ACCUMULATED)
        asset_ids_lib = self.cTB._asset_index.cached_queries.get(
            query_key_lib, [])
        for _asset_id in asset_ids_lib:
            del self.cTB._asset_index.all_assets[_asset_id]

        # Remove all cached queries pointing into this lib
        cached_queries_copy = list(self.cTB._asset_index.cached_queries.keys())
        for _query_tuple in cached_queries_copy:
            if _query_tuple[2] in keys_in_lib:
                del self.cTB._asset_index.cached_queries[_query_tuple]

        self.cTB.refresh_ui()

    def _callback_update_folder(self, json_message: Dict):
        # TODO(Andreas): I have never seen this event, so no guarantee,
        #                this code works. Likely it will not.
        #                Never tested, never running...
        print("_callback_update_folder")
        print(json_message)
        results = json_message.get("results", {})
        path_lib = results.get("folder_path", "")
        if path_lib == "":
            print("_callback_top_level_folder_finished: NO LIB PATH")
            return

        lib, _ = self.bo_libraries.get_library_by_path(path_lib)
        lib.status = BO_FOLDER_STATUS.IS_PROCESSING
        self.status = BO_STATUS.CLIENT_WAITING_FOR_DIRS
        self.ev_wait.set()
        self.schedule_get_assets(path_lib, "")

    def _callback_top_level_folder_finished(self, json_message: Dict):
        print("_callback_top_level_folder_finished")
        results = json_message.get("results", {})
        path_lib = results.get("folder_path", "")
        if path_lib == "":
            print("_callback_top_level_folder_finished: NO LIB PATH")
            return

        lib, _ = self.bo_libraries.get_library_by_path(path_lib)
        lib.status = BO_FOLDER_STATUS.COMPLETE

        self.schedule_get_assets(path_lib, "")

    def _callback_lost_connection(self, json_message: Dict):
        print("_callback_lost_connection")
        self.status = BO_STATUS.NOT_CONNECTED
        self.ev_wait.set()
        self.cTB.refresh_ui()

    def _thread_listener_state_not_connected(self) -> None:
        # print("LISTENER NOT_CONNECTED")
        res = self.api_client.register_client()
        if res.status != "success":
            return
        is_started = self.bo_client.start(fail_with_exception=False)
        if not is_started:
            return

        self.bo_client.register_callbacks(
            callback_register=self._callback_register,
            callback_log_in_with_web=self._callback_log_in_with_web,
            callback_add_top_level_folder=self._callback_add_top_level_folder,
            callback_remove_top_level_folder=self._callback_remove_top_level_folder,
            callback_update_folder=self._callback_update_folder,
            callback_top_level_folder_finished=self._callback_top_level_folder_finished,
            callback_lost_connection=self._callback_lost_connection,
            callback_toplevel_directory_connected=self._callback_add_top_level_folder,
            callback_toplevel_directory_unconnected=self._callback_toplevel_directory_unconnected)
        self.status = BO_STATUS.CLIENT_REGISTERED

    def _thread_listener_state_registered(self) -> None:
        print("LISTENER CLIENT_REGISTERED")
        socket_ok = self.bo_client.socket_client.connect_to_server()
        if not socket_ok:
            # TODO(Andreas): Not sure, it makes sense to retry, maybe go into
            #                some error state?
            return

        self.status = BO_STATUS.CLIENT_CONNECTED

    def _thread_listener_state_connected(self) -> None:
        print("LISTENER CLIENT_CONNECTED")
        is_listening = self.bo_client.socket_client.start_listening()
        # TODO: switch to a method which doesn't re-start listening all the time
        if not is_listening:
            self.status = BO_STATUS.NOT_CONNECTED
            return

        res = self.api_client.get_all_top_level_folders()
        self.bo_libraries.init_from_response(res, child_init=False)

        self.cTB.refresh_ui()

        if self.bo_libraries.is_server_gathering_data():
            self.status = BO_STATUS.CLIENT_WAITING_FOR_DIRS
        else:
            key_fetch_all = ((CATEGORY_ALL, ), "")
            if key_fetch_all in self.cTB.fetching_asset_data[KEY_TAB_MY_ASSETS]:
                del self.cTB.fetching_asset_data[KEY_TAB_MY_ASSETS][key_fetch_all]
            self.status = BO_STATUS.CLIENT_IS_LISTENING

        self.bo_libraries.get_assets()

    def _thread_listener_state_waiting_for_dirs(self) -> None:
        print("LISTENER CLIENT_WAITING_FOR_DIRS")

        asset_index_key = self.cTB.vActiveCat[-1]
        if asset_index_key == CATEGORY_ALL:
            self.bo_libraries.get_assets()
        else:
            path_entry = self.bo_libraries.get_path_entry_by_key(asset_index_key)
            if path_entry.library.status != BO_FOLDER_STATUS.COMPLETE:
                path_entry.get_assets()

    def _thread_listener(self) -> None:
        self.bo_listener_running = True

        while self.bo_listener_running:
            next_poll_s = 3.0

            self.ev_wait.clear()

            # Safeguard: if socket not connected, must be disconnected
            if self.bo_client.socket_client is None or not self.bo_client.socket_client.socket_listening:
                if self.status != BO_STATUS.NOT_CONNECTED:
                    self.status = BO_STATUS.NOT_CONNECTED
                    print("Overwrote status to not connected")

            if self.status == BO_STATUS.NOT_CONNECTED:
                self._thread_listener_state_not_connected()

            if self.status == BO_STATUS.CLIENT_REGISTERED:
                self._thread_listener_state_registered()

            if self.status == BO_STATUS.CLIENT_CONNECTED:
                self._thread_listener_state_connected()

            if self.status == BO_STATUS.CLIENT_WAITING_FOR_DIRS:
                self._thread_listener_state_waiting_for_dirs()
                next_poll_s = 0.5

            if self.status == BO_STATUS.CLIENT_WAITING_FOR_SEARCH:
                # print("LISTENER CLIENT_WAITING_FOR_SEARCH")
                next_poll_s = 0.25

            if self.status == BO_STATUS.CLIENT_IS_LISTENING:
                # print("LISTENER CLIENT_IS_LISTENING")
                pass

            self.ev_wait.wait(timeout=next_poll_s)

        self.bo_listener_running = False

    def _get_library(self, path: str) -> Tuple[BOLibrary, BOPathEntry]:
        lib, path_entry = self.bo_libraries.get_library_by_path(path)
        if lib is None:
            print("_thread_gatherer: Unknown lib, create new")
            res = self.api_client.get_all_top_level_folders()
            # print(res)
            self.bo_libraries.init_from_response(res, add_only=True)
            lib, path_entry = self.bo_libraries.get_library_by_path(path)
        else:
            lib.enabled = True
            lib.update_asset_counts()

        return lib, path_entry

    def _get_assets(
        self,
        path: str,
        path_entry: BOPathEntry,
        search: str = "",
        idx_page: int = 0
    ) -> Tuple[Dict[int, AssetData], int]:
        assets: Dict[int, AssetData] = {}

        num_per_page = self.cTB.settings["page"]

        # print(f"#> _get_assets path: ${path}$, query: ${search}$")
        res_assets = self.api_client.get_assets(
            path=path,
            page_number=idx_page + 1,
            assets_per_page=num_per_page,
            search_query=search,
            sort_option="",  # not yet supported
            reverse_order=False,
            applied_filters={}  # not yet supported
        )
        if res_assets.status != API_SUCCESS:
            print("_get_assets: FAILED")
            return {}, 0

        results = res_assets.results
        asset_dicts = results.get("assets", [])
        number_of_assets = results.get("number_of_assets", 0)

        if path_entry is not None:
            path_entry.asset_count = number_of_assets

        if len(asset_dicts) == 0:
            print("_get_assets: NO ASSETS")
            return {}, 0
        for _asset in asset_dicts:
            asset_id = _asset.get("asset_id", -1)
            if asset_id == -1:
                print("_get_assets: asset id -1")
                continue

            res_details = self.api_client.get_asset_details(asset_id)
            if res_details.status != API_SUCCESS:
                # print(f"Details error for {asset_id}")
                # print(res_details)

                # TODO(Andreas): Workaround for issues after refreshing a
                #                library. The page will be re-requested
                #                upon draw. Also see additional explanation
                #                in _thread_gatherer().
                #                As soon as this is no longer an issue in
                #                server, we can change here again and
                #                improve "real" error display.
                return None, 0  # None is special error case!

                continue

            asset_details = res_details.results
            asset_data = bo_asset_data_to_ai_asset_data(asset_details)
            assets[asset_id] = asset_data

        return assets, number_of_assets

    def _populate_asset_index(
        self,
        assets: Dict[int, AssetData],
        path_entry: BOPathEntry,
        search: str,
        idx_page: int,
        num_assets: int
    ) -> Dict[int, AssetData]:
        for _asset_data in assets.values():
            self.cTB._asset_index.load_asset(_asset_data)

        num_per_page = self.cTB.settings["page"]
        key = path_entry.asset_index_key if path_entry is not None else CATEGORY_ALL
        query_tuple = (
            KEY_TAB_MY_ASSETS,
            None,
            key,
            search if search != "" else None,
            idx_page,
            num_per_page)

        asset_ids = list(assets.keys())

        self.cTB._asset_index.cached_queries[query_tuple] = asset_ids
        self.cTB.bo_asset_counts[query_tuple] = num_assets

        self.cTB.refresh_ui()

    def _thread_gatherer(self) -> None:
        self.bo_gatherer_running = True

        while self.bo_gatherer_running:
            path_lib, search, idx_page = self.queue_gather_lib_path.get(
                timeout=None)
            # We only want the latest job
            # (e.g. if user spams next/previous page buttons)
            while not self.queue_gather_lib_path.empty():
                path_lib, search, idx_page = self.queue_gather_lib_path.get(
                    timeout=None)
                # Yet, never skip the shutdown "job"
                if path_lib == "SHUTDOWN_GATHERER":
                    break
            if path_lib == "SHUTDOWN_GATHERER":
                break

            if path_lib != "":
                lib, path_entry = self._get_library(path_lib)
                if lib is None:
                    print(
                        "_thread_gatherer: library not found, path:", path_lib)
                    continue
            else:
                path_entry = None

            assets, num_assets = self._get_assets(
                path_lib, path_entry, search, idx_page)

            # TODO(Andreas): Currently, we throw away the entire page,
            #                when we fail to fetch details for an asset.
            #                It's a quick and dirty workaround for server
            #                delivering stale asset IDs after refreshing a lib.
            #                I'd say, this should be fixed server side and here
            #                we'd rather show an error asset in that case.
            if assets is None:
                continue

            self._populate_asset_index(
                assets, path_entry, search, idx_page, num_assets)

            if not self.bo_libraries.is_server_gathering_data():
                key_fetch_all = ((CATEGORY_ALL, ), "")
                if key_fetch_all in self.cTB.fetching_asset_data[KEY_TAB_MY_ASSETS]:
                    del self.cTB.fetching_asset_data[KEY_TAB_MY_ASSETS][key_fetch_all]
                self.status = BO_STATUS.CLIENT_IS_LISTENING

        self.bo_gatherer_running = False


def bo_get_assets(
    bo_listener: BOSocketListener,
    categories,
    search: str = "",
    idx_page: int = 0
) -> None:
    asset_index_key = categories[-1]

    if asset_index_key != CATEGORY_ALL:
        path_entry = bo_listener.bo_libraries.get_path_entry_by_key(
            asset_index_key)
        if path_entry is None:
            print("    No path entry???", asset_index_key)
            d = bo_listener.bo_libraries.get_all_library_names_and_ids()
            for _n, _k in d.items():
                print("    ", _n, _k)
            return
        path = path_entry.path
    else:
        path = ""
    bo_listener.schedule_get_assets(path, search, idx_page)


def bo_refresh_data(cTB) -> None:
    if cTB.vAssetType == CATEGORY_ALL:
        cTB._asset_index.cached_queries = {}
        cTB._asset_index.all_assets = {}

        for _lib in cTB.bo_listener.bo_libraries.libraries:
            path = _lib.path_tree.path
            _ = cTB.bo_listener.api_client.update_top_level_folder(
                path)
            # TODO(Andreas): error handling
            # print(res)

        cTB.bo_listener.status = BO_STATUS.CLIENT_CONNECTED
        cTB.bo_listener.ev_wait.set()

    else:
        path_entry_selected = cTB.bo_listener.bo_libraries.get_path_entry_by_key(
            cTB.vActiveCat[-1])
        if path_entry_selected is None:
            print("HOW IS THIS EVEN POSSIBLE?!?! Hang the developer!!!")
            return

        path = path_entry_selected.path

        lib = path_entry_selected.library
        asset_index_key_lib = lib.path_tree.asset_index_key
        path_lib = lib.path_tree.path

        # Get a list of query keys containing assets from this library.
        list_query_keys = []
        for _query_key in cTB._asset_index.cached_queries.keys():
            if _query_key[2] == asset_index_key_lib:
                list_query_keys.append(_query_key)

        # Get all asset IDs found in above found queries.
        asset_ids_lib = []
        for _query_key in list_query_keys:
            asset_ids = cTB._asset_index.cached_queries.get(_query_key, [])
            asset_ids_lib.extend(asset_ids)

        # Remove all AssetData referenced by asset IDs in those cached queries.
        for _asset_id in asset_ids_lib:
            if _asset_id in cTB._asset_index.all_assets:
                del cTB._asset_index.all_assets[_asset_id]
        # NOTE: This does NOT mean, we now got rid of all AssetData from this
        #       library. There could still be assets so far only cached in
        #       "All Libs" views, where we have no idea which lib they belong
        #       to. These will continue to exist as stale entries in asset
        #       index. But we need to make sure, they are no longer referenced
        #       by any cached query.

        # Get a list of all "All Libs" query keys.
        list_query_keys_all_lib = []
        for _query_key in cTB._asset_index.cached_queries.keys():
            if _query_key[2] == CATEGORY_ALL:
                list_query_keys_all_lib.append(_query_key)

        # Remove all "All Lib" query caches.
        for _query_key in list_query_keys_all_lib:
            del cTB._asset_index.cached_queries[_query_key]

        cTB.vPage[KEY_TAB_MY_ASSETS] = 0

        lib.status = BO_FOLDER_STATUS.IS_PROCESSING
        cTB.bo_listener.status = BO_STATUS.CLIENT_WAITING_FOR_DIRS

        _ = cTB.bo_listener.api_client.update_top_level_folder(path)
        # TODO(Andreas): error handling
        # print(res)

        bo_get_assets(cTB.bo_listener, path_lib)

    cTB.refresh_ui()


def build_barn_owl_not_found(cTB):
    col = cTB.vBase.column()
    wrapped_label(
        cTB,
        cTB.width_draw_ui,
        _t("To get started open Polydex"),
        col
    )
    row = col.row()
    wrapped_label(
        cTB,
        cTB.width_draw_ui,
        _t("Your linked folders and assets will show here once you have "
           "connected."),
        row
    )
    row.enabled = False
    col.operator(
        f"{PREFIX_OP}.open_polydex_app", text=_t("Open Polydex"), depress=1
    )


def build_barn_owl_alpha_ended(cTB):
    wrapped_label(
        cTB,
        cTB.width_draw_ui,
        _t("The alpha period has ended, thank you for participating. "
           "Please share your feedback."),
        cTB.vBase
    )
    op = cTB.vBase.operator(
        f"{PREFIX_OP}.poliigon_link", text=_t("Alpha Survey"), depress=1
    )
    op.mode = "bob_alpha_ended"


def build_areas(cTB):
    cTB.logger_ui.debug("build_areas")
    cTB.initial_view_screen()

    row = cTB.vBase.row(align=True)
    row.scale_x = 1.1
    row.scale_y = 1.1

    row.separator()

    row_prefs = row.row(align=True)
    row_prefs.alignment = "RIGHT"

    row_prefs.operator(
        f"{PREFIX_OP}.open_polydex_app", text=_t("Open App"))
    row_prefs.operator(
        f"{PREFIX_OP}.open_preferences",
        text="",
        icon="PREFERENCES",
    ).set_focus = "all"

    row_prefs.separator(factor=0.25)

    # row_right.operator(
    #     f"{PREFIX_OP}.bob_open_app",
    #     text=_t("Open App"),
    #     icon="NONE",
    # )


def build_categories(cTB):
    cTB.logger_ui.debug("build_categories")

    list_entries_selected = []
    if cTB.vAssetType != CATEGORY_ALL:
        path_entry_selected = cTB.bo_listener.bo_libraries.get_path_entry_by_key(
            cTB.vActiveCat[-1])
        if path_entry_selected is not None:
            list_entries_selected = path_entry_selected.get_path_entries()

    col_categories = cTB.vBase.column()

    width_factor = len(list_entries_selected)
    if cTB.width_draw_ui >= max(width_factor, 2) * 160 * get_ui_scale(cTB):
        row_categories = col_categories.row()
    else:
        row_categories = col_categories

    row_sub_cat = row_categories.row(align=True)

    list_library_names = [CATEGORY_ALL]
    lib_names_to_keys = cTB.bo_listener.bo_libraries.get_all_library_names_and_ids()
    list_library_names.extend(sorted(list(lib_names_to_keys.keys())))
    op_data = f"0@{CATEGORY_ALL}@"
    for _key in lib_names_to_keys.values():
        op_data += f"{_key}@"
    op_data = op_data[:-1]  # get rid of last @

    if cTB.vAssetType == CATEGORY_ALL or not list_entries_selected:
        lbl_button_cat = _t("Select Library")
    else:
        lbl_button_cat = list_entries_selected[0].name
    op = row_sub_cat.operator(
        f"{PREFIX_OP}.poliigon_category", text=lbl_button_cat, icon="TRIA_DOWN"
    )
    op.data = op_data

    if len(list_entries_selected) == 0:
        col_categories.separator()
        return

    list_entries_selected.append(None)

    path_entry_last = list_entries_selected[0]
    for _idx_sel, _path_entry in enumerate(list_entries_selected[1:]):
        row_sub_cat = row_categories.row(align=True)

        if _path_entry is not None:
            lbl_button = _path_entry.name
        else:
            lbl_button = CATEGORY_ALL

        op_data = f"{_idx_sel + 1}@{CATEGORY_ALL}@"

        if path_entry_last.children is None:
            path_entry_last._init_children(child_init=False)

        for _path_entry_child in path_entry_last.children:
            op_data += f"{_path_entry_child.asset_index_key}@"
        op_data = op_data[:-1]  # get rid of last @

        op = row_sub_cat.operator(
            f"{PREFIX_OP}.poliigon_category", text=lbl_button, icon="TRIA_DOWN"
        )
        op.data = op_data

        path_entry_last = _path_entry

    col_categories.separator()
