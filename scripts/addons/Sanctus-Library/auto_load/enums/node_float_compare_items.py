from . import _base

class BNodeFloatCompare(_base.BStaticEnum):

	LESS_THAN = dict(n='Less Than', d='True when the first input is smaller than second input')
	LESS_EQUAL = dict(n='Less Than or Equal', d='True when the first input is smaller than the second input or equal')
	GREATER_THAN = dict(n='Greater Than', d='True when the first input is greater than the second input')
	GREATER_EQUAL = dict(n='Greater Than or Equal', d='True when the first input is greater than the second input or equal')
	EQUAL = dict(n='Equal', d='True when both inputs are approximately equal')
	NOT_EQUAL = dict(n='Not Equal', d='True when both inputs are not approximately equal')
