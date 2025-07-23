from . import _base

class BObjectTypeCurve(_base.BStaticEnum):

	CURVE = dict(n='Curve', d='Curve')
	SURFACE = dict(n='Surface', d='Surface')
	FONT = dict(n='Text', d='Text')
