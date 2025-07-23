from . import _base

class BDTLayersSelectSrc(_base.BStaticEnum):

	ACTIVE = dict(n='Active Layer', d='Only transfer active data layer')
	ALL = dict(n='All Layers', d='Transfer all data layers')
	BONE_SELECT = dict(n='Selected Pose Bones', d='Transfer all vertex groups used by selected pose bones')
	BONE_DEFORM = dict(n='Deform Pose Bones', d='Transfer all vertex groups used by deform bones')
