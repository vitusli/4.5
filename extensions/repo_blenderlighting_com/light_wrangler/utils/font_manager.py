import os
import bpy
import blf

class FontManager:
    _instance = None
    _custom_font_id = None
    _is_initialized = False
    _font_path = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = FontManager()
        return cls._instance
    
    def __init__(self):
        if not FontManager._is_initialized:
            self.initialize()
    
    def initialize(self):
        """Initialize the font manager and load custom font."""
        try:
            # Get the addon directory path
            addon_dir = os.path.dirname(os.path.dirname(__file__))
            FontManager._font_path = os.path.join(addon_dir, "fonts", "AtkinsonHyperlegibleMono-Regular.otf")
            
            self.load_font()
        except Exception as e:
            print(f"Error during font manager initialization: {e}")
            FontManager._custom_font_id = 0  # Use default font as fallback
        
        FontManager._is_initialized = True
    
    def load_font(self):
        """Load or reload the custom font."""
        try:
            if FontManager._font_path and os.path.exists(FontManager._font_path):
                # Always try to load a new font ID
                new_font_id = blf.load(FontManager._font_path)
                if new_font_id != -1:  # -1 indicates load failure
                    FontManager._custom_font_id = new_font_id
                    # print(f"Successfully loaded Atkinson Hyperlegible Mono font with ID: {FontManager._custom_font_id}")
                else:
                    # print("Failed to load custom font, using fallback")
                    FontManager._custom_font_id = 0
            else:
                # print(f"Custom font not found at {FontManager._font_path}")
                FontManager._custom_font_id = 0
        except Exception as e:
            # print(f"Error loading custom font: {e}")
            FontManager._custom_font_id = 0
    
    def reinitialize(self):
        """Reinitialize the font manager, reloading the font."""
        self.load_font()
    
    @property
    def custom_font_id(self):
        """Get the ID of the custom font, or 0 if not loaded."""
        return FontManager._custom_font_id if FontManager._custom_font_id is not None else 0
    
    def cleanup(self):
        """Clean up font resources."""
        if FontManager._custom_font_id is not None:
            # Note: As of now, Blender doesn't provide a way to unload fonts
            # This is here for future compatibility
            FontManager._custom_font_id = None
            FontManager._is_initialized = False

# Global accessor function
def get_font_id():
    """Get the custom font ID, or 0 if not loaded."""
    return FontManager.get_instance().custom_font_id 