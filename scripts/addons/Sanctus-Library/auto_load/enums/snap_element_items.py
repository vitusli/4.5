from . import _base

class BSnapElement(_base.BStaticEnum):

	INCREMENT = dict(n='Increment', d='Snap to increments of grid')
	VERTEX = dict(n='Vertex', d='Snap to vertices')
	EDGE = dict(n='Edge', d='Snap to edges')
	FACE = dict(n='Face Project', d='Snap by projecting onto faces')
	FACE_NEAREST = dict(n='Face Nearest', d='Snap to nearest point on faces')
	VOLUME = dict(n='Volume', d='Snap to volume')
	EDGE_MIDPOINT = dict(n='Edge Center', d='Snap to the middle of edges')
	EDGE_PERPENDICULAR = dict(n='Edge Perpendicular', d='Snap to the nearest point on an edge')
