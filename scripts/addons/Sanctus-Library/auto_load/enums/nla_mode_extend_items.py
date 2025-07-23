from . import _base

class BNLAModeExtend(_base.BStaticEnum):

	NOTHING = dict(n='Nothing', d='Strip has no influence past its extents')
	HOLD = dict(n='Hold', d='Hold the first frame if no previous strips in track, and always hold last frame')
	HOLD_FORWARD = dict(n='Hold Forward', d='Only hold last frame')
