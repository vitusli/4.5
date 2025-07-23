from . import _base

class BObjectGPencilType(_base.BStaticEnum):

	EMPTY = dict(n='Blank', d='Create an empty grease pencil object')
	STROKE = dict(n='Stroke', d='Create a simple stroke with basic colors')
	MONKEY = dict(n='Monkey', d='Construct a Suzanne grease pencil object')
	LRT_SCENE = dict(n='Scene Line Art', d='Quickly set up line art for the entire scene')
	LRT_COLLECTION = dict(n='Collection Line Art', d='Quickly set up line art for the active collection')
	LRT_OBJECT = dict(n='Object Line Art', d='Quickly set up line art for the active object')
