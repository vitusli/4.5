from . import _base

class BEventTypeMask(_base.BStaticEnum):

	KEYBOARD_MODIFIER = dict(n='Keyboard Modifier', d='Keyboard Modifier')
	KEYBOARD = dict(n='Keyboard', d='Keyboard')
	MOUSE_WHEEL = dict(n='Mouse Wheel', d='Mouse Wheel')
	MOUSE_GESTURE = dict(n='Mouse Gesture', d='Mouse Gesture')
	MOUSE_BUTTON = dict(n='Mouse Button', d='Mouse Button')
	MOUSE = dict(n='Mouse', d='Mouse')
	NDOF = dict(n='NDOF', d='NDOF')
	ACTIONZONE = dict(n='Action Zone', d='Action Zone')
