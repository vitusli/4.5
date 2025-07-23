from . import _base

class BImageType(_base.BStaticEnum):

	BMP = dict(n='BMP', d='Output image in bitmap format')
	IRIS = dict(n='Iris', d='Output image in SGI IRIS format')
	PNG = dict(n='PNG', d='Output image in PNG format')
	JPEG = dict(n='JPEG', d='Output image in JPEG format')
	JPEG2000 = dict(n='JPEG 2000', d='Output image in JPEG 2000 format')
	TARGA = dict(n='Targa', d='Output image in Targa format')
	TARGA_RAW = dict(n='Targa Raw', d='Output image in uncompressed Targa format')
	CINEON = dict(n='Cineon', d='Output image in Cineon format')
	DPX = dict(n='DPX', d='Output image in DPX format')
	OPEN_EXR_MULTILAYER = dict(n='OpenEXR MultiLayer', d='Output image in multilayer OpenEXR format')
	OPEN_EXR = dict(n='OpenEXR', d='Output image in OpenEXR format')
	HDR = dict(n='Radiance HDR', d='Output image in Radiance HDR format')
	TIFF = dict(n='TIFF', d='Output image in TIFF format')
	WEBP = dict(n='WebP', d='Output image in WebP format')
	AVI_JPEG = dict(n='AVI JPEG', d='Output video in AVI JPEG format')
	AVI_RAW = dict(n='AVI Raw', d='Output video in AVI Raw format')
	FFMPEG = dict(n='FFmpeg Video', d='The most versatile way to output video files')
