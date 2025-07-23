from . import _base

class BNodeFloatToInt(_base.BStaticEnum):

	ROUND = dict(n='Round', d='Round the float up or down to the nearest integer')
	FLOOR = dict(n='Floor', d='Round the float down to the next smallest integer')
	CEILING = dict(n='Ceiling', d='Round the float up to the next largest integer')
	TRUNCATE = dict(n='Truncate', d='Round the float to the closest integer in the direction of zero (floor if positive; ceiling if negative)')
