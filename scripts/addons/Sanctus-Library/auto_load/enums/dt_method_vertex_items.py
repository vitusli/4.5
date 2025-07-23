from . import _base

class BDTMethodVertex(_base.BStaticEnum):

	TOPOLOGY = dict(n='Topology', d='Copy from identical topology meshes')
	NEAREST = dict(n='Nearest Vertex', d='Copy from closest vertex')
	EDGE_NEAREST = dict(n='Nearest Edge Vertex', d='Copy from closest vertex of closest edge')
	EDGEINTERP_NEAREST = dict(n='Nearest Edge Interpolated', d='Copy from interpolated values of vertices from closest point on closest edge')
	POLY_NEAREST = dict(n='Nearest Face Vertex', d='Copy from closest vertex of closest face')
	POLYINTERP_NEAREST = dict(n='Nearest Face Interpolated', d='Copy from interpolated values of vertices from closest point on closest face')
	POLYINTERP_VNORPROJ = dict(n='Projected Face Interpolated', d='Copy from interpolated values of vertices from point on closest face hit by normal-projection')
