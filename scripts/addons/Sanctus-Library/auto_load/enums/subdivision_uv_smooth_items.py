from . import _base

class BSubdivisionUvSmooth(_base.BStaticEnum):

	NONE = dict(n='None', d='UVs are not smoothed, boundaries are kept sharp')
	PRESERVE_CORNERS = dict(n='Keep Corners', d='UVs are smoothed, corners on discontinuous boundary are kept sharp')
	PRESERVE_CORNERS_AND_JUNCTIONS = dict(n='Keep Corners, Junctions', d='UVs are smoothed, corners on discontinuous boundary and junctions of 3 or more regions are kept sharp')
	PRESERVE_CORNERS_JUNCTIONS_AND_CONCAVE = dict(n='Keep Corners, Junctions, Concave', d='UVs are smoothed, corners on discontinuous boundary, junctions of 3 or more regions and darts and concave corners are kept sharp')
	PRESERVE_BOUNDARIES = dict(n='Keep Boundaries', d='UVs are smoothed, boundaries are kept sharp')
	SMOOTH_ALL = dict(n='All', d='UVs and boundaries are smoothed')
