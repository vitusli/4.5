from . import _base

class BMetaelemType(_base.BStaticEnum):

	BALL = dict(n='Ball', d='Ball')
	CAPSULE = dict(n='Capsule', d='Capsule')
	PLANE = dict(n='Plane', d='Plane')
	ELLIPSOID = dict(n='Ellipsoid', d='Ellipsoid')
	CUBE = dict(n='Cube', d='Cube')
