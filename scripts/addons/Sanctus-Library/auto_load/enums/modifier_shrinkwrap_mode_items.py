from . import _base

class BModifierShrinkwrapMode(_base.BStaticEnum):

	ON_SURFACE = dict(n='On Surface', d='The point is constrained to the surface of the target object, with distance offset towards the original point location')
	INSIDE = dict(n='Inside', d='The point is constrained to be inside the target object')
	OUTSIDE = dict(n='Outside', d='The point is constrained to be outside the target object')
	OUTSIDE_SURFACE = dict(n='Outside Surface', d='The point is constrained to the surface of the target object, with distance offset always to the outside, towards or away from the original location')
	ABOVE_SURFACE = dict(n='Above Surface', d='The point is constrained to the surface of the target object, with distance offset applied exactly along the target normal')
