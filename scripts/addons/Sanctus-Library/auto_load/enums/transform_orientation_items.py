from . import _base

class BTransformOrientation(_base.BStaticEnum):

	GLOBAL = dict(n='Global', d='Align the transformation axes to world space')
	LOCAL = dict(n='Local', d='Align the transformation axes to the selected objects’ local space')
	NORMAL = dict(n='Normal', d='Align the transformation axes to average normal of selected elements (bone Y axis for pose mode)')
	GIMBAL = dict(n='Gimbal', d='Align each axis to the Euler rotation axis as used for input')
	VIEW = dict(n='View', d='Align the transformation axes to the window')
	CURSOR = dict(n='Cursor', d='Align the transformation axes to the 3D cursor')
