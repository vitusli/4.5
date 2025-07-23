from . import _base

class BShrinkwrapFaceCull(_base.BStaticEnum):

	OFF = dict(n='Off', d='No culling')
	FRONT = dict(n='Front', d='No projection when in front of the face')
	BACK = dict(n='Back', d='No projection when behind the face')
