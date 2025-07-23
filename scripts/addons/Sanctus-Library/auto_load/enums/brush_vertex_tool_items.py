from . import _base

class BBrushVertexTool(_base.BStaticEnum):

	DRAW = dict(n='Draw', d='Draw')
	BLUR = dict(n='Blur', d='Blur')
	AVERAGE = dict(n='Average', d='Average')
	SMEAR = dict(n='Smear', d='Smear')
