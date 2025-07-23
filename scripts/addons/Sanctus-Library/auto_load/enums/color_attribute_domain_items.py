from . import _base

class BColorAttributeDomain(_base.BStaticEnum):

	POINT = dict(n='Vertex', d='Vertex')
	CORNER = dict(n='Face Corner', d='Face Corner')
