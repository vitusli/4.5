from . import _base

class BAttributeTypeWithAuto(_base.BStaticEnum):

	AUTO = dict(n='Auto', d='Auto')
	FLOAT = dict(n='Float', d='Floating-point value')
	INT = dict(n='Integer', d='32-bit integer')
	FLOAT_VECTOR = dict(n='Vector', d='3D vector with floating-point values')
	FLOAT_COLOR = dict(n='Color', d='RGBA color with 32-bit floating-point values')
	BYTE_COLOR = dict(n='Byte Color', d='RGBA color with 8-bit positive integer values')
	STRING = dict(n='String', d='Text string')
	BOOLEAN = dict(n='Boolean', d='True or false')
	FLOAT2 = dict(n='2D Vector', d='2D vector with floating-point values')
	INT8 = dict(n='8-Bit Integer', d='Smaller integer with a range from -128 to 127')
