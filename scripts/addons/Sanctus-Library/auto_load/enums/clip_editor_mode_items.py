from . import _base

class BClipEditorMode(_base.BStaticEnum):

	TRACKING = dict(n='Tracking', d='Show tracking and solving tools')
	MASK = dict(n='Mask', d='Show mask editing tools')
