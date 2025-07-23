from . import _base

class BDTLayersSelectDst(_base.BStaticEnum):

	ACTIVE = dict(n='Active Layer', d='Affect active data layer of all targets')
	NAME = dict(n='By Name', d='Match target data layers to affect by name')
	INDEX = dict(n='By Order', d='Match target data layers to affect by order (indices)')
