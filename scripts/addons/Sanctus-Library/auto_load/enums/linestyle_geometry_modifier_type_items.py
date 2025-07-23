from . import _base

class BLinestyleGeometryModifierType(_base.BStaticEnum):

	_2D_OFFSET = dict(n='2D Offset', d='2D Offset')
	_2D_TRANSFORM = dict(n='2D Transform', d='2D Transform')
	BACKBONE_STRETCHER = dict(n='Backbone Stretcher', d='Backbone Stretcher')
	BEZIER_CURVE = dict(n='Bezier Curve', d='Bezier Curve')
	BLUEPRINT = dict(n='Blueprint', d='Blueprint')
	GUIDING_LINES = dict(n='Guiding Lines', d='Guiding Lines')
	PERLIN_NOISE_1D = dict(n='Perlin Noise 1D', d='Perlin Noise 1D')
	PERLIN_NOISE_2D = dict(n='Perlin Noise 2D', d='Perlin Noise 2D')
	POLYGONIZATION = dict(n='Polygonization', d='Polygonization')
	SAMPLING = dict(n='Sampling', d='Sampling')
	SIMPLIFICATION = dict(n='Simplification', d='Simplification')
	SINUS_DISPLACEMENT = dict(n='Sinus Displacement', d='Sinus Displacement')
	SPATIAL_NOISE = dict(n='Spatial Noise', d='Spatial Noise')
	TIP_REMOVER = dict(n='Tip Remover', d='Tip Remover')
