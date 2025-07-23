from . import _base

class BColorAttributeType(_base.BStaticEnum):

	FLOAT_COLOR = dict(n='Color', d='RGBA color 32-bit floating-point values')
	BYTE_COLOR = dict(n='Byte Color', d='RGBA color with 8-bit positive integer values')
