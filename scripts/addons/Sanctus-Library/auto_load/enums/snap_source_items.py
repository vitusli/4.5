from . import _base

class BSnapSource(_base.BStaticEnum):

	CLOSEST = dict(n='Closest', d='Snap closest point onto target')
	CENTER = dict(n='Center', d='Snap transformation center onto target')
	MEDIAN = dict(n='Median', d='Snap median onto target')
	ACTIVE = dict(n='Active', d='Snap active onto target')
