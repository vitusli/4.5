from . import _base

class BImageGeneratedType(_base.BStaticEnum):

	BLANK = dict(n='Blank', d='Generate a blank image')
	UV_GRID = dict(n='UV Grid', d='Generated grid to test UV mappings')
	COLOR_GRID = dict(n='Color Grid', d='Generated improved UV grid to test UV mappings')
