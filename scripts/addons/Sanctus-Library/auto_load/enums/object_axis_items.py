from . import _base

class BObjectAxis(_base.BStaticEnum):

	POS_X = dict(n='+X', d='+X')
	POS_Y = dict(n='+Y', d='+Y')
	POS_Z = dict(n='+Z', d='+Z')
	NEG_X = dict(n='-X', d='-X')
	NEG_Y = dict(n='-Y', d='-Y')
	NEG_Z = dict(n='-Z', d='-Z')
