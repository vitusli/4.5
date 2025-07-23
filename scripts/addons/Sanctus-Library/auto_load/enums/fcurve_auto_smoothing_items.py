from . import _base

class BFCurveAutoSmoothing(_base.BStaticEnum):

	NONE = dict(n='None', d='Automatic handles only take immediately adjacent keys into account')
	CONT_ACCEL = dict(n='Continuous Acceleration', d='Automatic handles are adjusted to avoid jumps in acceleration, resulting in smoother curves. However, key changes may affect interpolation over a larger stretch of the curve')
