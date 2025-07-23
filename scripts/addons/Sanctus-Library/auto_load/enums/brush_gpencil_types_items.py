from . import _base

class BBrushGPencilTypes(_base.BStaticEnum):

	DRAW = dict(n='Draw', d='The brush is of type used for drawing strokes')
	FILL = dict(n='Fill', d='The brush is of type used for filling areas')
	ERASE = dict(n='Erase', d='The brush is used for erasing strokes')
	TINT = dict(n='Tint', d='The brush is of type used for tinting strokes')
