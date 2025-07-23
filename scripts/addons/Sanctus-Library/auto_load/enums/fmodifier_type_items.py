from . import _base

class BFModifierType(_base.BStaticEnum):

	NULL = dict(n='Invalid', d='Invalid')
	GENERATOR = dict(n='Generator', d='Generate a curve using a factorized or expanded polynomial')
	FNGENERATOR = dict(n='Built-In Function', d='Generate a curve using standard math functions such as sin and cos')
	ENVELOPE = dict(n='Envelope', d='Reshape F-Curve values, e.g. change amplitude of movements')
	CYCLES = dict(n='Cycles', d='Cyclic extend/repeat keyframe sequence')
	NOISE = dict(n='Noise', d='Add pseudo-random noise on top of F-Curves')
	LIMITS = dict(n='Limits', d='Restrict maximum and minimum values of F-Curve')
	STEPPED = dict(n='Stepped Interpolation', d='Snap values to nearest grid step, e.g. for a stop-motion look')
