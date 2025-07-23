from . import _base

class BBakePassFilterType(_base.BStaticEnum):

	NONE = dict(n='None', d='None')
	EMIT = dict(n='Emit', d='Emit')
	DIRECT = dict(n='Direct', d='Direct')
	INDIRECT = dict(n='Indirect', d='Indirect')
	COLOR = dict(n='Color', d='Color')
	DIFFUSE = dict(n='Diffuse', d='Diffuse')
	GLOSSY = dict(n='Glossy', d='Glossy')
	TRANSMISSION = dict(n='Transmission', d='Transmission')
