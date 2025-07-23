from . import _base

class BNodeClamp(_base.BStaticEnum):

	MINMAX = dict(n='Min Max', d='Constrain value between min and max')
	RANGE = dict(n='Range', d='Constrain value between min and max, swapping arguments when min > max')
