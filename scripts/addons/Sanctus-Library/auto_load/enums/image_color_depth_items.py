from . import _base

class BImageColorDepth(_base.BStaticEnum):

	_8 = dict(n='8-bit color channels', d='8-bit color channels')
	_10 = dict(n='10-bit color channels', d='10-bit color channels')
	_12 = dict(n='12-bit color channels', d='12-bit color channels')
	_16 = dict(n='16-bit color channels', d='16-bit color channels')
	_32 = dict(n='32-bit color channels', d='32-bit color channels')
