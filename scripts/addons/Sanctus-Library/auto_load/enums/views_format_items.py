from . import _base

class BViewsFormat(_base.BStaticEnum):

	INDIVIDUAL = dict(n='Individual', d='Individual files for each view with the prefix as defined by the scene views')
	STEREO_3D = dict(n='Stereo 3D', d='Single file with an encoded stereo pair')
