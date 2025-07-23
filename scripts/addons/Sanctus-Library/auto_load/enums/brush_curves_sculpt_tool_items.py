from . import _base

class BBrushCurvesSculptTool(_base.BStaticEnum):

	COMB = dict(n='Comb Curves', d='Comb Curves')
	DELETE = dict(n='Delete Curves', d='Delete Curves')
	SNAKE_HOOK = dict(n='Curves Snake Hook', d='Curves Snake Hook')
	ADD = dict(n='Add Curves', d='Add Curves')
	GROW_SHRINK = dict(n='Grow / Shrink Curves', d='Grow / Shrink Curves')
	SELECTION_PAINT = dict(n='Paint Selection', d='Paint Selection')
	PINCH = dict(n='Pinch Curves', d='Pinch Curves')
	SMOOTH = dict(n='Smooth Curves', d='Smooth Curves')
	PUFF = dict(n='Puff Curves', d='Puff Curves')
	DENSITY = dict(n='Density Curves', d='Density Curves')
	SLIDE = dict(n='Slide Curves', d='Slide Curves')
