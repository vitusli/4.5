from . import _base

class BMappingType(_base.BStaticEnum):

	POINT = dict(n='Point', d='Transform a point')
	TEXTURE = dict(n='Texture', d='Transform a texture by inverse mapping the texture coordinate')
	VECTOR = dict(n='Vector', d='Transform a direction vector. Location is ignored')
	NORMAL = dict(n='Normal', d='Transform a unit normal vector. Location is ignored')
