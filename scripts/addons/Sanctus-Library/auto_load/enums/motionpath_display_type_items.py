from . import _base

class BMotionpathDisplayType(_base.BStaticEnum):

	CURRENT_FRAME = dict(n='Around Frame', d='Display Paths of poses within a fixed number of frames around the current frame')
	RANGE = dict(n='In Range', d='Display Paths of poses within specified range')
