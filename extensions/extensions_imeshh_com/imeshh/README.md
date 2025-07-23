# Imeshh - Blender Add-on

1. User authentication process begins with login.
2. Upon successful login, an authentication token is generated.
3. Using this token, the system retrieves categories and products via API calls (downloading all pages and thumbnails in the background).
4. All API responses are cached locally in JSON files.
5. Products are filtered based on user selections (asset type, category, subcategory) in the UI. This provides fast performance since filtering happens locally without additional API calls.