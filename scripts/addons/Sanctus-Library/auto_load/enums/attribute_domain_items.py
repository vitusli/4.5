from . import _base

class BAttributeDomain(_base.BStaticEnum):

	POINT = dict(n='Point', d='Attribute on point')
	EDGE = dict(n='Edge', d='Attribute on mesh edge')
	FACE = dict(n='Face', d='Attribute on mesh faces')
	CORNER = dict(n='Face Corner', d='Attribute on mesh face corner')
	CURVE = dict(n='Spline', d='Attribute on spline')
	INSTANCE = dict(n='Instance', d='Attribute on instance')
