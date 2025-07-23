from . import _base

class BNodeFilter(_base.BStaticEnum):

	SOFTEN = dict(n='Soften', d='Soften')
	SHARPEN = dict(n='Box Sharpen', d='An aggressive sharpening filter')
	SHARPEN_DIAMOND = dict(n='Diamond Sharpen', d='A moderate sharpening filter')
	LAPLACE = dict(n='Laplace', d='Laplace')
	SOBEL = dict(n='Sobel', d='Sobel')
	PREWITT = dict(n='Prewitt', d='Prewitt')
	KIRSCH = dict(n='Kirsch', d='Kirsch')
	SHADOW = dict(n='Shadow', d='Shadow')
