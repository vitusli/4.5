from . import _base

class BProportionalFalloff(_base.BStaticEnum):

	SMOOTH = dict(n='Smooth', d='Smooth falloff')
	SPHERE = dict(n='Sphere', d='Spherical falloff')
	ROOT = dict(n='Root', d='Root falloff')
	INVERSE_SQUARE = dict(n='Inverse Square', d='Inverse Square falloff')
	SHARP = dict(n='Sharp', d='Sharp falloff')
	LINEAR = dict(n='Linear', d='Linear falloff')
	CONSTANT = dict(n='Constant', d='Constant falloff')
	RANDOM = dict(n='Random', d='Random falloff')
