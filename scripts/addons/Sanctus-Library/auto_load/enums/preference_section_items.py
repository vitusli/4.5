from . import _base

class BPreferenceSection(_base.BStaticEnum):

	INTERFACE = dict(n='Interface', d='Interface')
	THEMES = dict(n='Themes', d='Themes')
	VIEWPORT = dict(n='Viewport', d='Viewport')
	LIGHTS = dict(n='Lights', d='Lights')
	EDITING = dict(n='Editing', d='Editing')
	ANIMATION = dict(n='Animation', d='Animation')
	ADDONS = dict(n='Add-ons', d='Add-ons')
	INPUT = dict(n='Input', d='Input')
	NAVIGATION = dict(n='Navigation', d='Navigation')
	KEYMAP = dict(n='Keymap', d='Keymap')
	SYSTEM = dict(n='System', d='System')
	SAVE_LOAD = dict(n='Save & Load', d='Save & Load')
	FILE_PATHS = dict(n='File Paths', d='File Paths')
	EXPERIMENTAL = dict(n='Experimental', d='Experimental')
