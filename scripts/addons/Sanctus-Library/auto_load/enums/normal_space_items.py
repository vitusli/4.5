from . import _base

class BNormalSpace(_base.BStaticEnum):

	OBJECT = dict(n='Object', d='Bake the normals in object space')
	TANGENT = dict(n='Tangent', d='Bake the normals in tangent space')
