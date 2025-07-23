from . import _base

class BMeshSelectModeUv(_base.BStaticEnum):

	VERTEX = dict(n='Vertex', d='Vertex selection mode')
	EDGE = dict(n='Edge', d='Edge selection mode')
	FACE = dict(n='Face', d='Face selection mode')
	ISLAND = dict(n='Island', d='Island selection mode')
