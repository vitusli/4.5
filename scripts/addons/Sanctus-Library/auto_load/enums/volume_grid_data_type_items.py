from . import _base

class BVolumeGridDataType(_base.BStaticEnum):

	BOOLEAN = dict(n='Boolean', d='Boolean')
	FLOAT = dict(n='Float', d='Single precision float')
	DOUBLE = dict(n='Double', d='Double precision')
	INT = dict(n='Integer', d='32-bit integer')
	INT64 = dict(n='Integer 64-bit', d='64-bit integer')
	MASK = dict(n='Mask', d='No data, boolean mask of active voxels')
	VECTOR_FLOAT = dict(n='Float Vector', d='3D float vector')
	VECTOR_DOUBLE = dict(n='Double Vector', d='3D double vector')
	VECTOR_INT = dict(n='Integer Vector', d='3D integer vector')
	POINTS = dict(n='Points (Unsupported)', d='Points grid, currently unsupported by volume objects')
	UNKNOWN = dict(n='Unknown', d='Unsupported data type')
