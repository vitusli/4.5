from . import _base

class BViewsFormatMultilayer(_base.BStaticEnum):

	INDIVIDUAL = dict(n='Individual', d='Individual files for each view with the prefix as defined by the scene views')
	MULTIVIEW = dict(n='Multi-View', d='Single file with all the views')
