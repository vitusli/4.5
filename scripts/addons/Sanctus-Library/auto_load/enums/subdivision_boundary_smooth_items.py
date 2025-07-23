from . import _base

class BSubdivisionBoundarySmooth(_base.BStaticEnum):

	PRESERVE_CORNERS = dict(n='Keep Corners', d='Smooth boundaries, but corners are kept sharp')
	ALL = dict(n='All', d='Smooth boundaries, including corners')
