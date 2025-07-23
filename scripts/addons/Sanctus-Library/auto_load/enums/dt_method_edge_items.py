from . import _base

class BDTMethodEdge(_base.BStaticEnum):

	TOPOLOGY = dict(n='Topology', d='Copy from identical topology meshes')
	VERT_NEAREST = dict(n='Nearest Vertices', d='Copy from most similar edge (edge which vertices are the closest of destination edge’s ones)')
	NEAREST = dict(n='Nearest Edge', d='Copy from closest edge (using midpoints)')
	POLY_NEAREST = dict(n='Nearest Face Edge', d='Copy from closest edge of closest face (using midpoints)')
	EDGEINTERP_VNORPROJ = dict(n='Projected Edge Interpolated', d='Interpolate all source edges hit by the projection of destination one along its own normal (from vertices)')
