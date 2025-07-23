from . import _base

class BDTMethodLoop(_base.BStaticEnum):

	TOPOLOGY = dict(n='Topology', d='Copy from identical topology meshes')
	NEAREST_NORMAL = dict(n='Nearest Corner and Best Matching Normal', d='Copy from nearest corner which has the best matching normal')
	NEAREST_POLYNOR = dict(n='Nearest Corner and Best Matching Face Normal', d='Copy from nearest corner which has the face with the best matching normal to destination corner’s face one')
	NEAREST_POLY = dict(n='Nearest Corner of Nearest Face', d='Copy from nearest corner of nearest polygon')
	POLYINTERP_NEAREST = dict(n='Nearest Face Interpolated', d='Copy from interpolated corners of the nearest source polygon')
	POLYINTERP_LNORPROJ = dict(n='Projected Face Interpolated', d='Copy from interpolated corners of the source polygon hit by corner normal projection')
