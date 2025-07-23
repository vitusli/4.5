import bpy

class Presets(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()

def register():
    bpy.utils.register_class(Presets)
    bpy.types.Scene.render_raw_presets = bpy.props.CollectionProperty(type=Presets)

def unregister():
    bpy.utils.unregister_class(Presets)