from . import _base

class BBakeTarget(_base.BStaticEnum):

	IMAGE_TEXTURES = dict(n='Image Textures', d='Bake to image data-blocks associated with active image texture nodes in materials')
	VERTEX_COLORS = dict(n='Active Color Attribute', d='Bake to the active color attribute on meshes')
