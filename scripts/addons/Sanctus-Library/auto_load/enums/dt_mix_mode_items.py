from . import _base

class BDTMixMode(_base.BStaticEnum):

	REPLACE = dict(n='Replace', d='Overwrite all elements’ data')
	ABOVE_THRESHOLD = dict(n='Above Threshold', d='Only replace destination elements where data is above given threshold (exact behavior depends on data type)')
	BELOW_THRESHOLD = dict(n='Below Threshold', d='Only replace destination elements where data is below given threshold (exact behavior depends on data type)')
	MIX = dict(n='Mix', d='Mix source value into destination one, using given threshold as factor')
	ADD = dict(n='Add', d='Add source value to destination one, using given threshold as factor')
	SUB = dict(n='Subtract', d='Subtract source value to destination one, using given threshold as factor')
	MUL = dict(n='Multiply', d='Multiply source value to destination one, using given threshold as factor')
