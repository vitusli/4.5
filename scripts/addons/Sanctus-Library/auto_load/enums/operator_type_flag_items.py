from . import _base

class BOperatorTypeFlag(_base.BStaticEnum):

	REGISTER = dict(n='Register', d='Display in the info window and support the redo toolbar panel')
	UNDO = dict(n='Undo', d='Push an undo event (needed for operator redo)')
	UNDO_GROUPED = dict(n='Grouped Undo', d='Push a single undo event for repeated instances of this operator')
	BLOCKING = dict(n='Blocking', d='Block anything else from using the cursor')
	MACRO = dict(n='Macro', d='Use to check if an operator is a macro')
	GRAB_CURSOR = dict(n='Grab Pointer', d='Use so the operator grabs the mouse focus, enables wrapping when continuous grab is enabled')
	GRAB_CURSOR_X = dict(n='Grab Pointer X', d='Grab, only warping the X axis')
	GRAB_CURSOR_Y = dict(n='Grab Pointer Y', d='Grab, only warping the Y axis')
	DEPENDS_ON_CURSOR = dict(n='Depends on Cursor', d='The initial cursor location is used, when running from a menus or buttons the user is prompted to place the cursor before beginning the operation')
	PRESET = dict(n='Preset', d='Display a preset button with the operators settings')
	INTERNAL = dict(n='Internal', d='Removes the operator from search results')
