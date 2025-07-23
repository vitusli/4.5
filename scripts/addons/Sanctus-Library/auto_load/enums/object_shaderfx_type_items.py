from . import _base

class BObjectShaderfxType(_base.BStaticEnum):

	FX_BLUR = dict(n='Blur', d='Apply Gaussian Blur to object')
	FX_COLORIZE = dict(n='Colorize', d='Apply different tint effects')
	FX_FLIP = dict(n='Flip', d='Flip image')
	FX_GLOW = dict(n='Glow', d='Create a glow effect')
	FX_PIXEL = dict(n='Pixelate', d='Pixelate image')
	FX_RIM = dict(n='Rim', d='Add a rim to the image')
	FX_SHADOW = dict(n='Shadow', d='Create a shadow effect')
	FX_SWIRL = dict(n='Swirl', d='Create a rotation distortion')
	FX_WAVE = dict(n='Wave Distortion', d='Apply sinusoidal deformation')
