from . import _base

class BKeyframeHandleType(_base.BStaticEnum):

	FREE = dict(n='Free', d='Completely independent manually set handle')
	ALIGNED = dict(n='Aligned', d='Manually set handle with rotation locked together with its pair')
	VECTOR = dict(n='Vector', d='Automatic handles that create straight lines')
	AUTO = dict(n='Automatic', d='Automatic handles that create smooth curves')
	AUTO_CLAMPED = dict(n='Auto Clamped', d='Automatic handles that create smooth curves which only change direction at keyframes')
