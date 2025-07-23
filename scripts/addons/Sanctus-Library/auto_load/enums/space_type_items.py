from . import _base

class BSpaceType(_base.BStaticEnum):

	EMPTY = dict(n='Empty', d='Empty')
	VIEW_3D = dict(n='3D Viewport', d='Manipulate objects in a 3D environment')
	IMAGE_EDITOR = dict(n='UV/Image Editor', d='View and edit images and UV Maps')
	NODE_EDITOR = dict(n='Node Editor', d='Editor for node-based shading and compositing tools')
	SEQUENCE_EDITOR = dict(n='Video Sequencer', d='Video editing tools')
	CLIP_EDITOR = dict(n='Movie Clip Editor', d='Motion tracking tools')
	DOPESHEET_EDITOR = dict(n='Dope Sheet', d='Adjust timing of keyframes')
	GRAPH_EDITOR = dict(n='Graph Editor', d='Edit drivers and keyframe interpolation')
	NLA_EDITOR = dict(n='Nonlinear Animation', d='Combine and layer Actions')
	TEXT_EDITOR = dict(n='Text Editor', d='Edit scripts and in-file documentation')
	CONSOLE = dict(n='Python Console', d='Interactive programmatic console for advanced editing and script development')
	INFO = dict(n='Info', d='Log of operations, warnings and error messages')
	TOPBAR = dict(n='Top Bar', d='Global bar at the top of the screen for global per-window settings')
	STATUSBAR = dict(n='Status Bar', d='Global bar at the bottom of the screen for general status information')
	OUTLINER = dict(n='Outliner', d='Overview of scene graph and all available data-blocks')
	PROPERTIES = dict(n='Properties', d='Edit properties of active object and related data-blocks')
	FILE_BROWSER = dict(n='File Browser', d='Browse for files and assets')
	SPREADSHEET = dict(n='Spreadsheet', d='Explore geometry data in a table')
	PREFERENCES = dict(n='Preferences', d='Edit persistent configuration settings')
