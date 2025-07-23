from . import _base

class BUnpackMethod(_base.BStaticEnum):

	REMOVE = dict(n='Remove Pack', d='Remove Pack')
	USE_LOCAL = dict(n='Use Local File', d='Use Local File')
	WRITE_LOCAL = dict(n='Write Local File (overwrite existing)', d='Write Local File (overwrite existing)')
	USE_ORIGINAL = dict(n='Use Original File', d='Use Original File')
	WRITE_ORIGINAL = dict(n='Write Original File (overwrite existing)', d='Write Original File (overwrite existing)')
