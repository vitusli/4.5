from . import _base

class BMotionpathRange(_base.BStaticEnum):

	KEYS_ALL = dict(n='All Keys', d='From the first keyframe to the last')
	KEYS_SELECTED = dict(n='Selected Keys', d='From the first selected keyframe to the last')
	SCENE = dict(n='Scene Frame Range', d='The entire Scene / Preview range')
