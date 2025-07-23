from . import _base

class BCurveFitMethod(_base.BStaticEnum):

	REFIT = dict(n='Refit', d='Incrementally refit the curve (high quality)')
	SPLIT = dict(n='Split', d='Split the curve until the tolerance is met (fast)')
