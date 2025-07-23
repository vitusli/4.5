import bpy
from .utils import install_pillow
from ..Tools.helper import get_addon_preferences


class InstallPillow:
    '''Base class for an operator that installs Pillow.

    Usage:
    -   Inherit bpy.types.Operator and InstallPillow.
    -   Make sure to set bl_idname, it must be unique.
    '''
    bl_label = 'Install Pillow'
    bl_description = '.\n'.join((
        'Install the Python Imaging Library',
        'This could take a few minutes',
    ))
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self: bpy.types.Operator, context: bpy.types.Context) -> set:
        if install_pillow():
            self.report({'INFO'}, 'Successfully installed Pillow')
            get_addon_preferences().pil_warning = True
        else:
            self.report({'WARNING'}, 'Failed to install Pillow')

        return {'FINISHED'}
