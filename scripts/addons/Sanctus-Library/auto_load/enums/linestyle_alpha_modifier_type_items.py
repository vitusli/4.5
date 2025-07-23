from . import _base

class BLinestyleAlphaModifierType(_base.BStaticEnum):

	ALONG_STROKE = dict(n='Along Stroke', d='Along Stroke')
	CREASE_ANGLE = dict(n='Crease Angle', d='Crease Angle')
	CURVATURE_3D = dict(n='Curvature 3D', d='Curvature 3D')
	DISTANCE_FROM_CAMERA = dict(n='Distance from Camera', d='Distance from Camera')
	DISTANCE_FROM_OBJECT = dict(n='Distance from Object', d='Distance from Object')
	MATERIAL = dict(n='Material', d='Material')
	NOISE = dict(n='Noise', d='Noise')
	TANGENT = dict(n='Tangent', d='Tangent')
