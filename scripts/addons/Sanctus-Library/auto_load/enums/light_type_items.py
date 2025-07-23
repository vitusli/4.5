from . import _base

class BLightType(_base.BStaticEnum):

	POINT = dict(n='Point', d='Omnidirectional point light source')
	SUN = dict(n='Sun', d='Constant direction parallel ray light source')
	SPOT = dict(n='Spot', d='Directional cone light source')
	AREA = dict(n='Area', d='Directional area light source')
