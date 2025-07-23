from . import _base

class BPropertyType(_base.BStaticEnum):

	BOOLEAN = dict(n='Boolean', d='Boolean')
	INT = dict(n='Integer', d='Integer')
	FLOAT = dict(n='Float', d='Float')
	STRING = dict(n='String', d='String')
	ENUM = dict(n='Enumeration', d='Enumeration')
	POINTER = dict(n='Pointer', d='Pointer')
	COLLECTION = dict(n='Collection', d='Collection')
