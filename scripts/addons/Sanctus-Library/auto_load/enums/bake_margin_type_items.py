from . import _base

class BBakeMarginType(_base.BStaticEnum):

	ADJACENT_FACES = dict(n='Adjacent Faces', d='Use pixels from adjacent faces across UV seams')
	EXTEND = dict(n='Extend', d='Extend border pixels outwards')
