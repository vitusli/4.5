from . import _base

class BSpaceImageModeAll(_base.BStaticEnum):

	VIEW = dict(n='View', d='View the image')
	UV = dict(n='UV Editor', d='UV edit in mesh editmode')
	PAINT = dict(n='Paint', d='2D image painting mode')
	MASK = dict(n='Mask', d='Mask editing')
