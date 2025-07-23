from . import _base

class BNodeMapRange(_base.BStaticEnum):

	LINEAR = dict(n='Linear', d='Linear interpolation between From Min and From Max values')
	STEPPED = dict(n='Stepped Linear', d='Stepped linear interpolation between From Min and From Max values')
	SMOOTHSTEP = dict(n='Smooth Step', d='Smooth Hermite edge interpolation between From Min and From Max values')
	SMOOTHERSTEP = dict(n='Smoother Step', d='Smoother Hermite edge interpolation between From Min and From Max values')
