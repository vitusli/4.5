from . import _base

class BCurvesTypes(_base.BStaticEnum):

	CATMULL_ROM = dict(n='Catmull Rom', d='Catmull Rom')
	POLY = dict(n='Poly', d='Poly')
	BEZIER = dict(n='Bezier', d='Bezier')
	NURBS = dict(n='NURBS', d='NURBS')
