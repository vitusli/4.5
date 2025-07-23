from math import radians

import bpy
from bpy.props import BoolProperty, FloatProperty, IntProperty, EnumProperty, PointerProperty, StringProperty
from .constants import IOR
from .Tools.helper import init_libraries_previews

class FluentShaderProps(bpy.types.PropertyGroup):

    def import_decals(self, context):
        bpy.ops.fluent.newdecal('INVOKE_DEFAULT', is_procedural_decal=True)

    def auto_margin(self, context):
        fluent_props = bpy.context.scene.FluentShaderProps
        if fluent_props.map_size == '256':
            fluent_props.bake_margin = 2
        if fluent_props.map_size == '512':
            fluent_props.bake_margin = 4
        if fluent_props.map_size == '1024':
            fluent_props.bake_margin = 8
        if fluent_props.map_size == '2048':
            fluent_props.bake_margin = 16
        if fluent_props.map_size == '4096':
            fluent_props.bake_margin = 32
        if fluent_props.map_size == '8192':
            fluent_props.bake_margin = 64

    def test(self, context):
        init_libraries_previews()

    show_bake_setting: BoolProperty(
        default=False
    )

    show_bake_pbr: BoolProperty(
        default=False
    )

    show_bake_mask: BoolProperty(
        default=False
    )

    show_bake_decal: BoolProperty(
        default=False
    )

    map_size: EnumProperty(
        name='Map size',
        items=(
            ("256", "256", "256"),
            ("512", "512", "512"),
            ("1024", "1024", "1024"),
            ("2048", "2048", "2048"),
            ("4096", "4096", "4096"),
            ("8192", "8192", "8192")
        ),
        default='2048',
        update=auto_margin
    )
    bake_image_format: EnumProperty(
        name='Format',
        items=(
            ("JPEG", "JPEG", "JPEG format. All maps except normal map"),
            ("PNG", "PNG", "PNG"),
        ),
        default='PNG'
    )
    bake_sample: EnumProperty(
        name='Sample',
        items=(
            ("1", "1", "1"),
            ("2", "2", "2"),
            ("4", "4", "4"),
            ("8", "8", "8"),
            ("16", "16", "16"),
            ("32", "32", "32"),
            ("64", "64", "64"),
            ("128", "128", "128"),
            ("256", "256", "256"),
            ("512", "512", "512"),
            ("1024", "1024", "1024"),
            ("2048", "2048", "2048")
        ),
        default='16'
    )
    bake_margin: IntProperty(
        name='Margin',
        default=16
    )
    sections: EnumProperty(
        name='Section',
        items=(
            ("imperfections", "Imperfections", "imperfections"),
            ("grunges", "Grunges", "grunges"),
            ("patterns", "Patterns", "patterns"),
            ("liquid", "Liquid", "liquid"),
            ("city", "City", "city"),
            ("normals", "Normals", "normals"),
            ("fabric", "Fabric", "fabric"),
            ("metal", "Metal", "metal"),
            ("shaders", "Shaders", "shaders"),
            ("wood", "Wood", "wood"),
            ("manmade", "Man made", "manmade"),
            ("screen", "Screen", "screen"),
            ("decals", "Decals", "decals"),
            ("environment", "Environment", "environment"),
        ),
        default='imperfections',
        update=test
    )
    scale_scale: FloatProperty(
        description="Multiply the default added node scale. Useful for automatic adaptation of your object size",
        name="Scale",
        default=1,
        min=0,
        step=0.01,
        precision=2
    )
    bake_custom_colorspace: BoolProperty(
        default=False,
        name='Custom Color Space',
        description="Only use this if you know what you're doing!"
    )
    bake_make_color: BoolProperty(
        default=True,
        name='Color',
        description="Bake color map"
    )
    bake_make_metallic: BoolProperty(
        default=True,
        name='Metallic',
        description="Bake metallic map"
    )
    bake_make_roughness: BoolProperty(
        default=True,
        name='Roughness',
        description="Bake roughness map"
    )
    bake_make_normal: BoolProperty(
        default=True,
        name='Normal',
        description="Bake normal map"
    )
    bake_make_emission: BoolProperty(
        default=False,
        name='Emission',
        description="Bake emission map"
    )
    bake_make_ao: BoolProperty(
        default=False,
        name='AO',
        description="Bake ambiant occlusion map"
    )
    bake_make_alpha: BoolProperty(
        default=False,
        name='Alpha',
        description="Bake alpha map"
    )
    bake_normal_opengl: BoolProperty(
        default=True,
        name='OpenGL',
        description="Save opengl normal map"
    )
    bake_normal_directx: BoolProperty(
        default=False,
        name='DirectX',
        description="Bake DirectX normal map"
    )
    bake_make_selected_to_active: BoolProperty(
        default=False,
        name='Bake high poly into low poly',
        description="Bake one or multiple objects into one\nWARINING: You need to select all the objects you want to bake and keep active the destination object"
    )
    bake_make_selected_to_active_extrusion: FloatProperty(
        default=0.01,
        name='Extrusion',
        description="Extrusion used to bake in the selected to active bake mode. \nNOTICE: This setting will depend on the size of your object. Lower it if you get strange results"
    )

    bake_use_cage: BoolProperty(
        default=False,
        name='Cage',
        description="Use a cage object"
    )

    bake_cage_object: PointerProperty(
        type=bpy.types.Object,
        name='Cage object',
        description='Use nothing to use the target object as cage object'
    )

    bake_in_image: PointerProperty(
        type=bpy.types.Image,
        name='Reuse image',
        description='Do not bake in new image.\nReuse images with the same first word'
    )

    bake_in_image_path: StringProperty()

    bake_auto_set: BoolProperty(
        default=False,
        name='Set baked material',
        description="Automaticaly add a material slot that uses baked maps"
    )

    bake_combine_channels: BoolProperty(
        default=False,
        name='Combine RGB channels',
        description="Use RGB channels to combine multiple bake"
    )

    bake_red_channel: EnumProperty(
        name='Red',
        items=(
            ("metallic", "Metallic", "metallic"),
            ("roughness", "Roughness", "roughness"),
            ("ao", "AO", "ao"),
            ("emission", "Emission", "emission"),
            ("alpha", "Alpha", "alpha"),
            ("none", "None", "none"),
        ),
        default='metallic'
    )

    bake_green_channel: EnumProperty(
        name='Green',
        items=(
            ("metallic", "Metallic", "metallic"),
            ("roughness", "Roughness", "roughness"),
            ("ao", "AO", "ao"),
            ("emission", "Emission", "emission"),
            ("alpha", "Alpha", "alpha"),
            ("none", "None", "none"),
        ),
        default='roughness'
    )

    bake_blue_channel: EnumProperty(
        name='Blue',
        items=(
            ("metallic", "Metallic", "metallic"),
            ("roughness", "Roughness", "roughness"),
            ("ao", "AO", "ao"),
            ("emission", "Emission", "emission"),
            ("alpha", "Alpha", "alpha"),
            ("none", "None", "none"),
        ),
        default='ao'
    )

    udim_baking: BoolProperty(
        default=False,
        name='Use UDIM'
    )

    udim_count: IntProperty(
        default=1,
        name='Tiles count',
        description='Tiles count'
    )

    udim_paint_count: IntProperty(
        default=1,
        name='Tiles count',
        description='Tiles count'
    )

    udim_paint_baking: BoolProperty(
        default=False,
        name='Use UDIM'
    )

    udim_paint_size: EnumProperty(
        items=(
            ('256', '256', '256'),
            ('512', '512', '512'),
            ('1024', '1024', '1024'),
            ('2048', '2048', '2048'),
            ('4096', '4096', '4096'),
            ('8192', '8192', '8192'),
        ),
        default='4096',
        name='Resolution'
    )

    is_baking: BoolProperty()
    baking_error: StringProperty()

    auto_mid: BoolProperty(
        name='Auto mid'
    )
    max_ray_distance: FloatProperty(
        name='Max research distance',
        default=2.0
    )
    angle_threshold: FloatProperty(
        name='Angle',
        default=radians(40),
        min=0,
        max=180,
        step=1,
        precision=3,
        subtype='ANGLE'
    )

    nb_samples: IntProperty(
        name='Samples',
        default=8
    )

    is_init: BoolProperty()
