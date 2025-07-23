from . import _base

class BNLAModeBlend(_base.BStaticEnum):

	REPLACE = dict(n='Replace', d='The strip values replace the accumulated results by amount specified by influence')
	COMBINE = dict(n='Combine', d='The strip values are combined with accumulated results by appropriately using addition, multiplication, or quaternion math, based on channel type')
	ADD = dict(n='Add', d='Weighted result of strip is added to the accumulated results')
	SUBTRACT = dict(n='Subtract', d='Weighted result of strip is removed from the accumulated results')
	MULTIPLY = dict(n='Multiply', d='Weighted result of strip is multiplied with the accumulated results')
