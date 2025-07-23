from . import _base

class BKeyblockType(_base.BStaticEnum):

	KEY_LINEAR = dict(n='Linear', d='Linear')
	KEY_CARDINAL = dict(n='Cardinal', d='Cardinal')
	KEY_CATMULL_ROM = dict(n='Catmull-Rom', d='Catmull-Rom')
	KEY_BSPLINE = dict(n='BSpline', d='BSpline')
