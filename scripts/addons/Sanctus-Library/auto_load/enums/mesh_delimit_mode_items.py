from . import _base

class BMeshDelimitMode(_base.BStaticEnum):

	NORMAL = dict(n='Normal', d='Delimit by face directions')
	MATERIAL = dict(n='Material', d='Delimit by face material')
	SEAM = dict(n='Seam', d='Delimit by edge seams')
	SHARP = dict(n='Sharp', d='Delimit by sharp edges')
	UV = dict(n='UVs', d='Delimit by UV coordinates')
