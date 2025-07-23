from . import _base

class BBrushImageTool(_base.BStaticEnum):

	DRAW = dict(n='Draw', d='Draw')
	SOFTEN = dict(n='Soften', d='Soften')
	SMEAR = dict(n='Smear', d='Smear')
	CLONE = dict(n='Clone', d='Clone')
	FILL = dict(n='Fill', d='Fill')
	MASK = dict(n='Mask', d='Mask')
