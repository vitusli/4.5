from . import _base

class BModifierTriangulateQuadMethod(_base.BStaticEnum):

	BEAUTY = dict(n='Beauty', d='Split the quads in nice triangles, slower method')
	FIXED = dict(n='Fixed', d='Split the quads on the first and third vertices')
	FIXED_ALTERNATE = dict(n='Fixed Alternate', d='Split the quads on the 2nd and 4th vertices')
	SHORTEST_DIAGONAL = dict(n='Shortest Diagonal', d='Split the quads along their shortest diagonal')
	LONGEST_DIAGONAL = dict(n='Longest Diagonal', d='Split the quads along their longest diagonal')
