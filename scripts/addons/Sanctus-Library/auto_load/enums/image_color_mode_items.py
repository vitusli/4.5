from . import _base

class BImageColorMode(_base.BStaticEnum):

	BW = dict(n='BW', d='Images get saved in 8-bit grayscale (only PNG, JPEG, TGA, TIF)')
	RGB = dict(n='RGB', d='Images are saved with RGB (color) data')
	RGBA = dict(n='RGBA', d='Images are saved with RGB and Alpha data (if supported)')
