from . import _base

class BBeztripleInterpolationEasing(_base.BStaticEnum):

	AUTO = dict(n='Automatic Easing', d='Easing type is chosen automatically based on what the type of interpolation used (e.g. Ease In for transitional types, and Ease Out for dynamic effects)')
	EASE_IN = dict(n='Ease In', d='Only on the end closest to the next keyframe')
	EASE_OUT = dict(n='Ease Out', d='Only on the end closest to the first keyframe')
	EASE_IN_OUT = dict(n='Ease In and Out', d='Segment between both keyframes')
