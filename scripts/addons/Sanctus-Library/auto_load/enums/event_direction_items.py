from . import _base

class BEventDirection(_base.BStaticEnum):

	ANY = dict(n='Any', d='Any')
	NORTH = dict(n='North', d='North')
	NORTH_EAST = dict(n='North-East', d='North-East')
	EAST = dict(n='East', d='East')
	SOUTH_EAST = dict(n='South-East', d='South-East')
	SOUTH = dict(n='South', d='South')
	SOUTH_WEST = dict(n='South-West', d='South-West')
	WEST = dict(n='West', d='West')
	NORTH_WEST = dict(n='North-West', d='North-West')
