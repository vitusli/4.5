
from .. import auto_load as al
from ..auto_load.common import *


@al.register
class BakingPreferences(al.PropertyGroup):

    default_image_export_format = al.EnumProperty(enum=al.BImageFileFormat, default=al.BImageFileFormat.PNG, name='Default Baking Export Format', description='Default Export format for baked images')
