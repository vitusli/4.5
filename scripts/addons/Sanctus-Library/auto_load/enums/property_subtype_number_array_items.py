from . import _base

class BPropertySubtypeNumberArray(_base.BStaticEnum):

	COLOR = dict(n='Color', d='Color')
	TRANSLATION = dict(n='Translation', d='Translation')
	DIRECTION = dict(n='Direction', d='Direction')
	VELOCITY = dict(n='Velocity', d='Velocity')
	ACCELERATION = dict(n='Acceleration', d='Acceleration')
	MATRIX = dict(n='Matrix', d='Matrix')
	EULER = dict(n='Euler Angles', d='Euler Angles')
	QUATERNION = dict(n='Quaternion', d='Quaternion')
	AXISANGLE = dict(n='Axis-Angle', d='Axis-Angle')
	XYZ = dict(n='XYZ', d='XYZ')
	XYZ_LENGTH = dict(n='XYZ Length', d='XYZ Length')
	COLOR_GAMMA = dict(n='Color', d='Color')
	COORDINATES = dict(n='Coordinates', d='Coordinates')
	LAYER = dict(n='Layer', d='Layer')
	LAYER_MEMBER = dict(n='Layer Member', d='Layer Member')
	NONE = dict(n='None', d='None')
