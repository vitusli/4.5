from . import _base

class BNavigationMode(_base.BStaticEnum):

	WALK = dict(n='Walk', d='Interactively walk or free navigate around the scene')
	FLY = dict(n='Fly', d='Use fly dynamics to navigate the scene')
