from . import _base

class BMotionpathBakeLocation(_base.BStaticEnum):

	HEADS = dict(n='Heads', d='Calculate bone paths from heads')
	TAILS = dict(n='Tails', d='Calculate bone paths from tails')
