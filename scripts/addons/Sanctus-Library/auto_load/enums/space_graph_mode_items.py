from . import _base

class BSpaceGraphMode(_base.BStaticEnum):

	FCURVES = dict(n='Graph Editor', d='Edit animation/keyframes displayed as 2D curves')
	DRIVERS = dict(n='Drivers', d='Edit drivers')
