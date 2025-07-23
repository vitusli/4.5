from . import _base

class BAttributeDomainOnlyMesh(_base.BStaticEnum):

	POINT = dict(n='Point', d='Attribute on point')
	EDGE = dict(n='Edge', d='Attribute on mesh edge')
	FACE = dict(n='Face', d='Attribute on mesh faces')
	CORNER = dict(n='Face Corner', d='Attribute on mesh face corner')
