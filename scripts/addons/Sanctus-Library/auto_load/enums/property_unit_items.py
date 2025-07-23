from . import _base

class BPropertyUnit(_base.BStaticEnum):

	NONE = dict(n='None', d='None')
	LENGTH = dict(n='Length', d='Length')
	AREA = dict(n='Area', d='Area')
	VOLUME = dict(n='Volume', d='Volume')
	ROTATION = dict(n='Rotation', d='Rotation')
	TIME = dict(n='Time (Scene Relative)', d='Time (Scene Relative)')
	TIME_ABSOLUTE = dict(n='Time (Absolute)', d='Time (Absolute)')
	VELOCITY = dict(n='Velocity', d='Velocity')
	ACCELERATION = dict(n='Acceleration', d='Acceleration')
	MASS = dict(n='Mass', d='Mass')
	CAMERA = dict(n='Camera', d='Camera')
	POWER = dict(n='Power', d='Power')
	TEMPERATURE = dict(n='Temperature', d='Temperature')
