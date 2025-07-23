from . import _base

class BBeztripleInterpolationMode(_base.BStaticEnum):

	CONSTANT = dict(n='Constant', d='No interpolation, value of A gets held until B is encountered')
	LINEAR = dict(n='Linear', d='Straight-line interpolation between A and B (i.e. no ease in/out)')
	BEZIER = dict(n='Bezier', d='Smooth interpolation between A and B, with some control over curve shape')
	SINE = dict(n='Sinusoidal', d='Sinusoidal easing (weakest, almost linear but with a slight curvature)')
	QUAD = dict(n='Quadratic', d='Quadratic easing')
	CUBIC = dict(n='Cubic', d='Cubic easing')
	QUART = dict(n='Quartic', d='Quartic easing')
	QUINT = dict(n='Quintic', d='Quintic easing')
	EXPO = dict(n='Exponential', d='Exponential easing (dramatic)')
	CIRC = dict(n='Circular', d='Circular easing (strongest and most dynamic)')
	BACK = dict(n='Back', d='Cubic easing with overshoot and settle')
	BOUNCE = dict(n='Bounce', d='Exponentially decaying parabolic bounce, like when objects collide')
	ELASTIC = dict(n='Elastic', d='Exponentially decaying sine wave, like an elastic band')
