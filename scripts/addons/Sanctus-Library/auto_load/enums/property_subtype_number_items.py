from . import _base

class BPropertySubtypeNumber(_base.BStaticEnum):

	PIXEL = dict(n='Pixel', d='Pixel')
	UNSIGNED = dict(n='Unsigned', d='Unsigned')
	PERCENTAGE = dict(n='Percentage', d='Percentage')
	FACTOR = dict(n='Factor', d='Factor')
	ANGLE = dict(n='Angle', d='Angle')
	TIME = dict(n='Time (Scene Relative)', d='Time specified in frames, converted to seconds based on scene frame rate')
	TIME_ABSOLUTE = dict(n='Time (Absolute)', d='Time specified in seconds, independent of the scene')
	DISTANCE = dict(n='Distance', d='Distance')
	DISTANCE_CAMERA = dict(n='Camera Distance', d='Camera Distance')
	POWER = dict(n='Power', d='Power')
	TEMPERATURE = dict(n='Temperature', d='Temperature')
	NONE = dict(n='None', d='None')
