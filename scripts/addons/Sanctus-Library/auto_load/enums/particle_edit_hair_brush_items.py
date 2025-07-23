from . import _base

class BParticleEditHairBrush(_base.BStaticEnum):

	COMB = dict(n='Comb', d='Comb hairs')
	SMOOTH = dict(n='Smooth', d='Smooth hairs')
	ADD = dict(n='Add', d='Add hairs')
	LENGTH = dict(n='Length', d='Make hairs longer or shorter')
	PUFF = dict(n='Puff', d='Make hairs stand up')
	CUT = dict(n='Cut', d='Cut hairs')
	WEIGHT = dict(n='Weight', d='Weight hair particles')
