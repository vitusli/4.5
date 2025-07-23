from . import _base

class BEventValue(_base.BStaticEnum):

	ANY = dict(n='Any', d='Any')
	PRESS = dict(n='Press', d='Press')
	RELEASE = dict(n='Release', d='Release')
	CLICK = dict(n='Click', d='Click')
	DOUBLE_CLICK = dict(n='Double Click', d='Double Click')
	CLICK_DRAG = dict(n='Click Drag', d='Click Drag')
	NOTHING = dict(n='Nothing', d='Nothing')
