from . import _base

class BUIListLayoutType(_base.BStaticEnum):

	DEFAULT = dict(n='Default Layout', d='Use the default, multi-rows layout')
	COMPACT = dict(n='Compact Layout', d='Use the compact, single-row layout')
	GRID = dict(n='Grid Layout', d='Use the grid-based layout')
