from . import _base

class BMeshSelectMode(_base.BStaticEnum):

	VERT = dict(n='Vertex', d='Vertex selection mode')
	EDGE = dict(n='Edge', d='Edge selection mode')
	FACE = dict(n='Face', d='Face selection mode')
