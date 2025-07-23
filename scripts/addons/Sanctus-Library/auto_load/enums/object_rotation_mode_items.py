from . import _base

class BObjectRotationMode(_base.BStaticEnum):

	QUATERNION = dict(n='Quaternion (WXYZ)', d='No Gimbal Lock')
	XYZ = dict(n='XYZ Euler', d='XYZ Rotation Order - prone to Gimbal Lock (default)')
	XZY = dict(n='XZY Euler', d='XZY Rotation Order - prone to Gimbal Lock')
	YXZ = dict(n='YXZ Euler', d='YXZ Rotation Order - prone to Gimbal Lock')
	YZX = dict(n='YZX Euler', d='YZX Rotation Order - prone to Gimbal Lock')
	ZXY = dict(n='ZXY Euler', d='ZXY Rotation Order - prone to Gimbal Lock')
	ZYX = dict(n='ZYX Euler', d='ZYX Rotation Order - prone to Gimbal Lock')
	AXIS_ANGLE = dict(n='Axis Angle', d='Axis Angle (W+XYZ), defines a rotation around some axis defined by 3D-Vector')
