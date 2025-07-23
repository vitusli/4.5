from . import _base

class BDTMethodPoly(_base.BStaticEnum):

	TOPOLOGY = dict(n='Topology', d='Copy from identical topology meshes')
	NEAREST = dict(n='Nearest Face', d='Copy from nearest polygon (using center points)')
	NORMAL = dict(n='Best Normal-Matching', d='Copy from source polygon which normal is the closest to destination one')
	POLYINTERP_PNORPROJ = dict(n='Projected Face Interpolated', d='Interpolate all source polygons intersected by the projection of destination one along its own normal')
