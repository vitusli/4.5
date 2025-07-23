from . import _base

class BKeyframePasteMerge(_base.BStaticEnum):

	MIX = dict(n='Mix', d='Overlay existing with new keys')
	OVER_ALL = dict(n='Overwrite All', d='Replace all keys')
	OVER_RANGE = dict(n='Overwrite Range', d='Overwrite keys in pasted range')
	OVER_RANGE_ALL = dict(n='Overwrite Entire Range', d='Overwrite keys in pasted range, using the range of all copied keys')
