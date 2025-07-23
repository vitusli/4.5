from . import _base

class BEXRCodec(_base.BStaticEnum):

	NONE = dict(n='None', d='None')
	PXR24 = dict(n='Pxr24 (lossy)', d='Pxr24 (lossy)')
	ZIP = dict(n='ZIP (lossless)', d='ZIP (lossless)')
	PIZ = dict(n='PIZ (lossless)', d='PIZ (lossless)')
	RLE = dict(n='RLE (lossless)', d='RLE (lossless)')
	ZIPS = dict(n='ZIPS (lossless)', d='ZIPS (lossless)')
	B44 = dict(n='B44 (lossy)', d='B44 (lossy)')
	B44A = dict(n='B44A (lossy)', d='B44A (lossy)')
	DWAA = dict(n='DWAA (lossy)', d='DWAA (lossy)')
	DWAB = dict(n='DWAB (lossy)', d='DWAB (lossy)')
