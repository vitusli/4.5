from . import _base

class BSymmetrizeDirection(_base.BStaticEnum):

	NEGATIVE_X = dict(n='-X to +X', d='-X to +X')
	POSITIVE_X = dict(n='+X to -X', d='+X to -X')
	NEGATIVE_Y = dict(n='-Y to +Y', d='-Y to +Y')
	POSITIVE_Y = dict(n='+Y to -Y', d='+Y to -Y')
	NEGATIVE_Z = dict(n='-Z to +Z', d='-Z to +Z')
	POSITIVE_Z = dict(n='+Z to -Z', d='+Z to -Z')
