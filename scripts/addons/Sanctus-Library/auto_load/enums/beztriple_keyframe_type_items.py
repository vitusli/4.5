from . import _base

class BBeztripleKeyframeType(_base.BStaticEnum):

	KEYFRAME = dict(n='Keyframe', d='Normal keyframe, e.g. for key poses')
	BREAKDOWN = dict(n='Breakdown', d='A breakdown pose, e.g. for transitions between key poses')
	MOVING_HOLD = dict(n='Moving Hold', d='A keyframe that is part of a moving hold')
	EXTREME = dict(n='Extreme', d='An “extreme” pose, or some other purpose as needed')
	JITTER = dict(n='Jitter', d='A filler or baked keyframe for keying on ones, or some other purpose as needed')
