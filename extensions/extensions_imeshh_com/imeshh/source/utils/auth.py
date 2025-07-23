import json
import os
import threading

import bpy
import requests

# BASE URLs
BASE_URL = "https://shop.imeshh.com"
BASE_LAMBDA_URL = "http://imeshh-lambda.s3-website-us-east-1.amazonaws.com"

HEADERS = {
    "User-Agent": "iMeshh-Asset-Manager/1.0 (+https://imeshh.com)",
    "Accept-Encoding": "gzip",  # Force gzip-encoded communication
}

# API URLs
URL_TOKEN = f"{BASE_URL}/wp-json/jwt-auth/v1/token"
URL_SUBS_INFO = f"{BASE_URL}/wp-json/imeshh/subscription-information"
URL_DOWNLOAD = f"{BASE_URL}/wp-json/imeshh/product-information/download-link"
URL_STATUS = f"https://blog.imeshh.com/wp-json/status-api/v1/latest"
URL_MESSAGE = "https://extensions.imeshh.com/wp-json/imeshh-api/v1/message"
URL_CATEGORIES = f"{BASE_LAMBDA_URL}/imeshh-all-product-compress-meta-data/latest_categories.json"
URL_PRODUCTS = f"{BASE_LAMBDA_URL}/imeshh-all-product-compress-meta-data/latest_products.json"
URL_MODEL_ASSETS_CAT = f"{BASE_LAMBDA_URL}/cats-files/models/blender_assets.cats.txt"
URL_MAT_ASSETS_CAT = f"{BASE_LAMBDA_URL}/cats-files/materials/blender_assets.cats.txt"
URL_GEO_NODES_ASSETS_CAT = f"{BASE_LAMBDA_URL}/cats-files/geonodes/blender_assets.cats.txt"
URL_FX_ASSETS_CAT = f"{BASE_LAMBDA_URL}/cats-files/fx/blender_assets.cats.txt"

# don't remove these paths, they are being used in the addon
if bpy.app.build_platform.decode() == "Linux":
    PATH_IMESHH = os.path.join(os.path.expanduser("~"), ".config", "imeshh")
else:
    PATH_IMESHH = os.path.join(os.path.expanduser("~"), "imeshh")
PATH_THUMBS = os.path.join(PATH_IMESHH, "thumbs")
PATH_IMAGES = os.path.join(PATH_IMESHH, "images")
PATH_AUTH_FILE = os.path.join(PATH_IMESHH, "token.json")
PATH_SUBS_INFO_FILE = os.path.join(PATH_IMESHH, "subs_info.json")
PATH_MESSAGE_FILE = os.path.join(PATH_IMESHH, "message.json")
PATH_PREFS_FILE = os.path.join(PATH_IMESHH, "userprefs.json")
PATH_STATUS_FILE = os.path.join(PATH_IMESHH, "status.json")
PATH_CATEGORIES_FILE = os.path.join(PATH_IMESHH, "categories.json")
PATH_PRODUCTS_FILE = os.path.join(PATH_IMESHH, "products.json")
PATH_FAVOURITES_FILE = os.path.join(PATH_IMESHH, "favourites.json")


def auth_token_exists() -> bool:
    return os.path.exists(PATH_AUTH_FILE)


def auth_token_path() -> str:
    if auth_token_exists():
        return PATH_AUTH_FILE
    return None


def get_auth_token() -> str:
    if auth_token_exists():
        with open(PATH_AUTH_FILE, "r", encoding="utf-8") as f:
            auth_data = json.load(f)
            return auth_data.get("auth_token")
    return None


def get_token_expiry() -> str:
    if auth_token_exists():
        with open(PATH_AUTH_FILE, "r", encoding="utf-8") as f:
            auth_data = json.load(f)
            return auth_data.get("token_expiry")
    return None


def delete_auth_data():
    if auth_token_exists():
        os.remove(PATH_AUTH_FILE)
    if os.path.exists(PATH_SUBS_INFO_FILE):
        os.remove(PATH_SUBS_INFO_FILE)


def get_response(url: str, params: dict = None) -> requests.Response:
    if not auth_token_exists():
        return None

    auth_token = get_auth_token()
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "User-Agent": "iMeshh-Asset-Manager/1.0 (+https://imeshh.com)",
        "Accept-Encoding": "gzip",  # Force gzip-encoded communication
    }

    return requests.get(url, headers=headers, params=params)


def save_subs_data():
    if not auth_token_exists():
        return

    def worker():
        try:
            print("INFO: Fetching subscription info...")
            response = get_response(URL_SUBS_INFO)
            if response is not None and response.status_code == 200:
                subs_info = response.json()
                with open(PATH_SUBS_INFO_FILE, "w", encoding="utf-8") as file:
                    json.dump(subs_info, file)
                print("SUCCESS: Subscription info fetched successfully!")
            elif response is None:
                print("ERROR: No response received. Check if the authentication token exists.")
            else:
                print(f"ERROR: Failed to fetch subscription info. HTTP Status: {response.status_code}")
        except Exception as e:
            print(f"EXCEPTION: An error occurred while fetching subscription info: {e}")

    threading.Thread(target=worker, daemon=True).start()


def save_message_data():
    def worker():
        try:
            print("INFO: Fetching message...")
            response = requests.get(URL_MESSAGE, headers=HEADERS)
            if response is not None and response.status_code == 200:
                message = response.json()
                with open(PATH_MESSAGE_FILE, "w", encoding="utf-8") as file:
                    json.dump(message, file)
                print("SUCCESS: Message fetched successfully!")
            elif response is None:
                print("ERROR: No response received. Check if the authentication token exists.")
            else:
                print(f"ERROR: Failed to fetch message. HTTP Status: {response.status_code}")
        except Exception as e:
            print(f"EXCEPTION: An error occurred while fetching message: {e}")

    threading.Thread(target=worker, daemon=True).start()


def save_status_data(status: dict) -> dict:
    with open(PATH_STATUS_FILE, "w", encoding="utf-8") as file:
        json.dump(status, file)


def get_status_data() -> dict:
    try:
        print("INFO: Fetching latest status...")
        response = requests.get(URL_STATUS, headers=HEADERS)
        if response is not None and response.status_code == 200:
            print("SUCCESS: Latest status fetched successfully!")
            return response.json()
        elif response is None:
            print("ERROR: No response received. Check if the authentication token exists.")
        else:
            print(f"ERROR: Failed to fetch latest status. HTTP Status: {response.status_code}")
    except Exception as e:
        print(f"EXCEPTION: An error occurred while fetching latest status: {e}")

    return None


# Cache for subs data
_cache_subs_info = None
_subs_info_mtime = None


def get_subs_info() -> dict:
    global _cache_subs_info, _subs_info_mtime

    if not os.path.exists(PATH_SUBS_INFO_FILE):
        return None

    mtime = os.path.getmtime(PATH_SUBS_INFO_FILE)
    if _cache_subs_info is not None and _subs_info_mtime == mtime:
        return _cache_subs_info

    with open(PATH_SUBS_INFO_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)
        _cache_subs_info = data[0] if data else None
        _subs_info_mtime = mtime
        return _cache_subs_info


# Cache for message data
_cache_message = None
_message_mtime = None


def get_message() -> dict:
    global _cache_message, _message_mtime

    if not os.path.exists(PATH_MESSAGE_FILE):
        return None

    mtime = os.path.getmtime(PATH_MESSAGE_FILE)
    if _cache_message is not None and _message_mtime == mtime:
        return _cache_message

    with open(PATH_MESSAGE_FILE, "r", encoding="utf-8") as file:
        try:
            _cache_message = json.load(file)
        except json.JSONDecodeError as err:
            print(f"EXCEPTION: Error decoding JSON from {PATH_MESSAGE_FILE}: {err}")
            _cache_message = None
        _message_mtime = mtime
        return _cache_message


# @bpy.app.handlers.persistent
def _load_subs_info(_):
    save_subs_data()
    save_message_data()


def register():
    os.makedirs(PATH_IMESHH, exist_ok=True)
    bpy.app.handlers.load_post.append(_load_subs_info)


def unregister():
    if _load_subs_info in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_load_subs_info)
