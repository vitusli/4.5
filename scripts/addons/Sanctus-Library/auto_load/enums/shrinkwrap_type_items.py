from . import _base

class BShrinkwrapType(_base.BStaticEnum):

	NEAREST_SURFACEPOINT = dict(n='Nearest Surface Point', d='Shrink the mesh to the nearest target surface')
	PROJECT = dict(n='Project', d='Shrink the mesh to the nearest target surface along a given axis')
	NEAREST_VERTEX = dict(n='Nearest Vertex', d='Shrink the mesh to the nearest target vertex')
	TARGET_PROJECT = dict(n='Target Normal Project', d='Shrink the mesh to the nearest target surface along the interpolated vertex normals of the target')
