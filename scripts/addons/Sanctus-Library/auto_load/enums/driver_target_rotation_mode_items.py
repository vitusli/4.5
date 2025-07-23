from . import _base

class BDriverTargetRotationMode(_base.BStaticEnum):

	AUTO = dict(n='Auto Euler', d='Euler using the rotation order of the target')
	XYZ = dict(n='XYZ Euler', d='Euler using the XYZ rotation order')
	XZY = dict(n='XZY Euler', d='Euler using the XZY rotation order')
	YXZ = dict(n='YXZ Euler', d='Euler using the YXZ rotation order')
	YZX = dict(n='YZX Euler', d='Euler using the YZX rotation order')
	ZXY = dict(n='ZXY Euler', d='Euler using the ZXY rotation order')
	ZYX = dict(n='ZYX Euler', d='Euler using the ZYX rotation order')
	QUATERNION = dict(n='Quaternion', d='Quaternion rotation')
	SWING_TWIST_X = dict(n='Swing and X Twist', d='Decompose into a swing rotation to aim the X axis, followed by twist around it')
	SWING_TWIST_Y = dict(n='Swing and Y Twist', d='Decompose into a swing rotation to aim the Y axis, followed by twist around it')
	SWING_TWIST_Z = dict(n='Swing and Z Twist', d='Decompose into a swing rotation to aim the Z axis, followed by twist around it')
