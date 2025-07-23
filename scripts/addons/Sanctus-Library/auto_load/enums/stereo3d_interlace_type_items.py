from . import _base

class BStereo3DInterlaceType(_base.BStaticEnum):

	ROW_INTERLEAVED = dict(n='Row Interleaved', d='Row Interleaved')
	COLUMN_INTERLEAVED = dict(n='Column Interleaved', d='Column Interleaved')
	CHECKERBOARD_INTERLEAVED = dict(n='Checkerboard Interleaved', d='Checkerboard Interleaved')
