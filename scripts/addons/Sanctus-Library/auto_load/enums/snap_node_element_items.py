from . import _base

class BSnapNodeElement(_base.BStaticEnum):

	GRID = dict(n='Grid', d='Snap to grid')
	NODE_X = dict(n='Node X', d='Snap to left/right node border')
	NODE_Y = dict(n='Node Y', d='Snap to top/bottom node border')
	NODE_XY = dict(n='Node X / Y', d='Snap to any node border')
