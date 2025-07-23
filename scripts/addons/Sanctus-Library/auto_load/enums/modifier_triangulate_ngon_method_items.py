from . import _base

class BModifierTriangulateNgonMethod(_base.BStaticEnum):

	BEAUTY = dict(n='Beauty', d='Arrange the new triangles evenly (slow)')
	CLIP = dict(n='Clip', d='Split the polygons with an ear clipping algorithm')
