"""
This file containing instances of ApiClient and the SocketClient and both
should be used through this class
"""

import platform
from typing import Callable, Dict, Optional

from .api import ApiClient
from .socket import SocketClient, SocketTypes


class Client:
    def __init__(self,
                 client_name: str,
                 client_version: str,
                 host_software_version: str,
                 do_start: bool = True):
        self.api_client = ApiClient(
            client_name=client_name,
            client_version=client_version,
            host_software_version=host_software_version,
            client_os_name=self.get_platform(),
            client_os_version=platform.version()
        )

        self.socket_client: SocketClient = None

        if do_start:
            self.start(fail_with_exception=True)

    def get_platform(self) -> str:
        if platform.system() == "Darwin":
            return "mac"
        elif platform.system() == "Windows":
            return "windows"
        elif platform.system() == "Linux":
            return "linux"
        else:
            return platform.system().lower()

    def start(self, fail_with_exception: bool = True) -> bool:
        if self.api_client.check_barnowl():  # will do registration
            self.socket_client = SocketClient(self.api_client.socket_host,
                                              self.api_client.socket_port,
                                              self.api_client.session_id)
        else:
            if fail_with_exception:
                raise ConnectionError("Api client register failed")
            return False
        return True

    def stop(self) -> None:
        """Stops the client, ending the socket and informing the server."""
        if self.socket_client is not None:
            self.socket_client.finish()
        self.api_client.terminate_client()

    def _callback_lost_connection(self, json_message: Dict) -> None:
        self.api_client.barnowl_detected = False

    def register_callbacks(
        self,
        *,
        callback_register: Callable,
        callback_log_in_with_web: Callable,
        callback_add_top_level_folder: Callable,
        callback_remove_top_level_folder: Callable,
        callback_update_folder: Callable,
        callback_top_level_folder_finished: Callable,
        callback_lost_connection: Optional[Callable] = None,
        callback_toplevel_directory_connected: Optional[Callable] = None,
        callback_toplevel_directory_unconnected: Optional[Callable] = None
    ) -> None:
        """Register a call back function for every socket message

        Args: The functions corresponding to every socket message that can be
        received.
        Callback prototype: callback(json_message: json) -> None
        """
        self.register_custom_callbacks(SocketTypes.REGISTER.value,
                                       callback_register)
        self.register_custom_callbacks(SocketTypes.LOG_IN_WITH_WEB.value,
                                       callback_log_in_with_web)
        self.register_custom_callbacks(SocketTypes.ADD_TOP_LEVEL_FOLDER.value,
                                       callback_add_top_level_folder)
        self.register_custom_callbacks(
            SocketTypes.REMOVE_TOP_LEVEL_FOLDER.value,
            callback_remove_top_level_folder)
        self.register_custom_callbacks(SocketTypes.UPDATE_FOLDER.value,
                                       callback_update_folder)
        self.register_custom_callbacks(
            SocketTypes.TOP_LEVEL_FOLDER_FINISHED_PROCESSING.value,
            callback_top_level_folder_finished)

        # We need our own callback here in order to reset flag in api
        self.register_custom_callbacks(
            SocketTypes.LOST_CONNECTION.value,
            self._callback_lost_connection)
        if callback_lost_connection is not None:
            self.register_custom_callbacks(
                SocketTypes.LOST_CONNECTION.value,
                callback_lost_connection)
        if callback_toplevel_directory_connected is not None:
            self.register_custom_callbacks(
                SocketTypes.TOPLEVEL_FOLDER_CONNECTED.value,
                callback_toplevel_directory_connected)
        if callback_toplevel_directory_unconnected is not None:
            self.register_custom_callbacks(
                SocketTypes.TOPLEVEL_FOLDER_UNCONNECTED.value,
                callback_toplevel_directory_unconnected)

    def register_custom_callbacks(self, message_type: str, callback: Callable):
        self.socket_client.register_callback(message_type, callback)
