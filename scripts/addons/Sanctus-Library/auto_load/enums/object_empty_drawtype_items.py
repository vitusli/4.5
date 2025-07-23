from . import _base

class BObjectEmptyDrawtype(_base.BStaticEnum):

	PLAIN_AXES = dict(n='Plain Axes', d='Plain Axes')
	ARROWS = dict(n='Arrows', d='Arrows')
	SINGLE_ARROW = dict(n='Single Arrow', d='Single Arrow')
	CIRCLE = dict(n='Circle', d='Circle')
	CUBE = dict(n='Cube', d='Cube')
	SPHERE = dict(n='Sphere', d='Sphere')
	CONE = dict(n='Cone', d='Cone')
	IMAGE = dict(n='Image', d='Image')
