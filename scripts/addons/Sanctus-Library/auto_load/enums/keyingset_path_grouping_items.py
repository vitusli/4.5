from . import _base

class BKeyingsetPathGrouping(_base.BStaticEnum):

	NAMED = dict(n='Named Group', d='Named Group')
	NONE = dict(n='None', d='None')
	KEYINGSET = dict(n='Keying Set Name', d='Keying Set Name')
