"""Root of the project.

This file initialize the socket client for barn owl.
"""

import concurrent.futures
from enum import Enum
import json
from socket import socket, AF_INET, SOCK_STREAM
import threading
from typing import Dict, List, Callable


class SocketTypes(Enum):
    REGISTER = "socket_register"
    LOG_IN_WITH_WEB = "socket_login_with_web"
    ADD_TOP_LEVEL_FOLDER = "socket_add_top_level_folder"
    REMOVE_TOP_LEVEL_FOLDER = "socket_remove_top_level_folder"
    UPDATE_FOLDER = "socket_update_folder"
    TOP_LEVEL_FOLDER_FINISHED_PROCESSING = "socket_library_finished_processing"
    LOST_CONNECTION = "socket_lost_connection"
    TOPLEVEL_FOLDER_CONNECTED = "toplevel_directory_connected"
    TOPLEVEL_FOLDER_UNCONNECTED = "toplevel_directory_unconnected"


class SocketClient:
    def __init__(self, host: str, port: int, session_id: str):
        self.host: str = host
        self.port: int = port
        self.session_id = session_id
        self.client_socket = socket(AF_INET, SOCK_STREAM)
        self.receive_messages_thread = None
        self.socket_listening = True
        self.callbacks: Dict[str, List[Callable]] = {}

    def connect_to_server(self) -> bool:
        if self.port <= 0:
            print(f"Invalid connection port: {self.port}")
            return False
        try:
            self.client_socket.connect((self.host, self.port))
            print(f"Connected to server at {self.host}:{self.port}")
            self.register_client_socket()
        except OSError as e:
            print(f"Failed to connection to server at {self.host}:{self.port} "
                  f"with error: {e}")
            return False
        return True

    def register_client_socket(self) -> None:
        try:
            # Send a register message to the server
            message = {"session_id": self.session_id}
            message_json = json.dumps(message)
            self.client_socket.send(message_json.encode())
        except Exception as e:
            print(f"Error sending register client socket message: {e}")

    def start_listening(self) -> bool:
        try:
            # Start a separate thread to receive messages
            self.receive_messages_thread = threading.Thread(
                target=self.receive_messages)
            self.receive_messages_thread.start()
        except OSError as e:
            print(f"Error starting message thread: {e}")
            self.finish()
            return False
        return True

    def receive_messages(self) -> None:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            while self.socket_listening:
                data = None
                try:
                    # Wait for client to send a message
                    data = self.client_socket.recv(1024)
                    if not data:
                        print("Server closed the connection")
                        self.stop_listening()
                        self.call_callbacks(
                            executor,
                            SocketTypes.LOST_CONNECTION.value,
                            # Callback's shouldn't care about message,
                            # the server is gone anyway
                            {"Lost Connection"},
                            # We can not submit here, as the executor context
                            # gets destroyed in next line
                            direct_call=True)
                        return

                    # Call the callback function in a separate thread
                    json_message = json.loads(data.decode())
                    message_type = json_message.get("message_type")
                    self.call_callbacks(executor, message_type, json_message)

                except json.JSONDecodeError:
                    print("Invalid JSON received from client")
                except ConnectionResetError:
                    print("Connection was forcibly closed by the server")
                    self.stop_listening()
                    self.call_callbacks(
                        executor,
                        SocketTypes.LOST_CONNECTION.value,
                        # Callback's shouldn't care about message,
                        # the server is gone anyway
                        {"Lost Connection"},
                        # We can not submit here, as the executor context
                        # gets destroyed in next line
                        direct_call=True)
                    return
                except Exception as e:
                    print(f"Error in receiving data: {e}")

        print("Receive messages thread exiting.")

    def call_callbacks(
        self,
        executor,
        message_type: str,
        json_message: Dict,
        direct_call: bool = False
    ) -> None:
        if message_type not in self.callbacks.keys():
            return
        for func in self.callbacks[message_type]:
            if direct_call:
                func(json_message)
            else:
                executor.submit(func, json_message)

    def register_callback(self, message_type: str, callback: Callable) -> None:
        if message_type not in self.callbacks:
            self.callbacks[message_type] = []
        self.callbacks[message_type].append(callback)

    def stop_listening(self) -> None:
        self.socket_listening = False
        self.client_socket.close()

    def finish(self) -> None:
        self.stop_listening()

        if self.receive_messages_thread is not None:
            self.receive_messages_thread.join(timeout=5)

        print("Client Socket closed")
