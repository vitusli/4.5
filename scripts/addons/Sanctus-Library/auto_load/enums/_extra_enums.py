from . import _base

class BLayoutStyle(_base.BStaticEnum):
    import bpy.types as bt
    VERTICAL = dict(n='Vertical', d='Vertical UI Layout using columns')
    HORIZONTAL = dict(n='Horizontal', d='Horizontal UI Layout using rows')

    def create(self, layout: bt.UILayout, align: bool = False, scale: float = 1) -> bt.UILayout:

        if self == BLayoutStyle.VERTICAL:
            n = layout.column(align=align)
            n.scale_y = scale
            return n
        elif self == BLayoutStyle.HORIZONTAL:
            n = layout.row(align=True)
            n.scale_x = scale
            return n
    
class BSpaceInfo(_base.FlagEnum):

    ALL = ('Window', 'EMPTY')
    CLIP = ('Clip', 'CLIP_EDITOR')
    CONSOLE = ('Console', 'CONSOLE')
    DOPESHEET = ('Dopesheet', 'DOPESHEET_EDITOR')
    FILEBROWSER = ('File Browser', 'FILE_BROWSER')
    GRAPH = ('Graph Editor', 'GRAPH_EDITOR')
    IMAGE = ('Image', 'IMAGE_EDITOR')
    INFO = ('Info', 'INFO')
    NLA = ('NLA Editor', 'NLA_EDITOR')
    NODE = ('Node Editor', 'NODE_EDITOR')
    OUTLINER = ('Outliner', 'OUTLINER')
    PROPERTIES = ('Property Editor', 'PROPERTIES')
    SEQUENCE = ('Sequencer', 'SEQUENCE_EDITOR')
    SPREADSHEET = ('Spreadsheet Generic', 'SPREADSHEET')
    TEXT = ('Text', 'TEXT_EDITOR')
    USERINTERFACE = ('User Interface', 'EMPTY')
    VIEW3D = ('3D View', 'VIEW_3D')

    def get_space_name(self):
        return self.value[0]
    
    def get_space_type(self):
        return self.value[1]

class BPathFallbackType(_base.BStaticEnum):
    ''''''
    NONE = dict(n='None', d='No Path Fallback allowed')
    TEMPPATH = dict(n='Temp Path', d='Falling back to the tempdir directory')
    PYTHONFILE = dict(n='Python File', d='Falling back to the directory of the python file')
    BLENDFILE_OR_USER_FOLDER = dict(n='Blend File/User Folder', d='Falling back to the directory of the current blend file, or the user\'s home folder if blend file isn\'t saved')

    def get_root(self):
        from pathlib import Path
        if self == BPathFallbackType.TEMPPATH:
            import tempfile
            return Path(tempfile.gettempdir())
        elif self == BPathFallbackType.PYTHONFILE:
            return Path('.')
        elif self == BPathFallbackType.BLENDFILE_OR_USER_FOLDER:
            import bpy
            if bpy.data.is_saved:
                return Path(bpy.data.filepath).parent
            else:
                return Path.home()
        else:
            import bpy
            return Path(bpy.data.filepath)

class BImageFileFormat(_base.BStaticEnum):
    '''File formats for Images. Use "extension" property to receive the appropriate file extension for each format.'''

    BMP = dict(n='BMP', d='Output image in bitmap format', a='bmp')
    IRIS = dict(n='Iris', d='Output image in SGI IRIS format', a='rgb')
    PNG = dict(n='PNG', d='Output image in PNG format', a='png')
    JPEG = dict(n='JPEG', d='Output image in JPEG format', a='jpg')
    JPEG2000 = dict(n='JPEG 2000', d='Output image in JPEG 2000 format', a='jp2')
    TARGA = dict(n='Targa', d='Output image in Targa format', a='tga')
    TARGA_RAW = dict(n='Targa Raw', d='Output image in uncompressed Targa format', a='tga')
    CINEON = dict(n='Cineon', d='Output image in Cineon format', a='cin')
    DPX = dict(n='DPX', d='Output image in DPX format', a='dpx')
    OPEN_EXR_MULTILAYER = dict(n='OpenEXR MultiLayer', d='Output image in multilayer OpenEXR format', a='exr')
    OPEN_EXR = dict(n='OpenEXR', d='Output image in OpenEXR format', a='exr')
    HDR = dict(n='Radiance HDR', d='Output image in Radiance HDR format', a='hdr')
    TIFF = dict(n='TIFF', d='Output image in TIFF format', a='tif')
    WEBP = dict(n='WebP', d='Output image in WebP format', a='webp')

    @property
    def extension(self) -> str:
        return self.value['a']