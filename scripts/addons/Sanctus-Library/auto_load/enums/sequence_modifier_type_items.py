from . import _base

class BSequenceModifierType(_base.BStaticEnum):

	BRIGHT_CONTRAST = dict(n='Bright/Contrast', d='Bright/Contrast')
	COLOR_BALANCE = dict(n='Color Balance', d='Color Balance')
	CURVES = dict(n='Curves', d='Curves')
	HUE_CORRECT = dict(n='Hue Correct', d='Hue Correct')
	MASK = dict(n='Mask', d='Mask')
	TONEMAP = dict(n='Tone Map', d='Tone Map')
	WHITE_BALANCE = dict(n='White Balance', d='White Balance')
