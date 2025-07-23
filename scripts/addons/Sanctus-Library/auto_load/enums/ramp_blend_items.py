from . import _base

class BRampBlend(_base.BStaticEnum):

	MIX = dict(n='Mix', d='Mix')
	DARKEN = dict(n='Darken', d='Darken')
	MULTIPLY = dict(n='Multiply', d='Multiply')
	BURN = dict(n='Color Burn', d='Color Burn')
	LIGHTEN = dict(n='Lighten', d='Lighten')
	SCREEN = dict(n='Screen', d='Screen')
	DODGE = dict(n='Color Dodge', d='Color Dodge')
	ADD = dict(n='Add', d='Add')
	OVERLAY = dict(n='Overlay', d='Overlay')
	SOFT_LIGHT = dict(n='Soft Light', d='Soft Light')
	LINEAR_LIGHT = dict(n='Linear Light', d='Linear Light')
	DIFFERENCE = dict(n='Difference', d='Difference')
	SUBTRACT = dict(n='Subtract', d='Subtract')
	DIVIDE = dict(n='Divide', d='Divide')
	HUE = dict(n='Hue', d='Hue')
	SATURATION = dict(n='Saturation', d='Saturation')
	COLOR = dict(n='Color', d='Color')
	VALUE = dict(n='Value', d='Value')
