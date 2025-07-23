from . import _base

class BRegionType(_base.BStaticEnum):

	WINDOW = dict(n='Window', d='Window')
	HEADER = dict(n='Header', d='Header')
	CHANNELS = dict(n='Channels', d='Channels')
	TEMPORARY = dict(n='Temporary', d='Temporary')
	UI = dict(n='UI', d='UI')
	TOOLS = dict(n='Tools', d='Tools')
	TOOL_PROPS = dict(n='Tool Properties', d='Tool Properties')
	PREVIEW = dict(n='Preview', d='Preview')
	HUD = dict(n='Floating Region', d='Floating Region')
	NAVIGATION_BAR = dict(n='Navigation Bar', d='Navigation Bar')
	EXECUTE = dict(n='Execute Buttons', d='Execute Buttons')
	FOOTER = dict(n='Footer', d='Footer')
	TOOL_HEADER = dict(n='Tool Header', d='Tool Header')
	XR = dict(n='XR', d='XR')
