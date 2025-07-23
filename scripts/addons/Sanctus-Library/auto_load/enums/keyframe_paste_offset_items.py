from . import _base

class BKeyframePasteOffset(_base.BStaticEnum):

	START = dict(n='Frame Start', d='Paste keys starting at current frame')
	END = dict(n='Frame End', d='Paste keys ending at current frame')
	RELATIVE = dict(n='Frame Relative', d='Paste keys relative to the current frame when copying')
	NONE = dict(n='No Offset', d='Paste keys from original time')
