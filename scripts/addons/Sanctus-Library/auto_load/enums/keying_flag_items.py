from . import _base

class BKeyingFlag(_base.BStaticEnum):

	INSERTKEY_NEEDED = dict(n='Only Needed', d='Only insert keyframes where they’re needed in the relevant F-Curves')
	INSERTKEY_VISUAL = dict(n='Visual Keying', d='Insert keyframes based on ‘visual transforms’')
	INSERTKEY_XYZ_TO_RGB = dict(n='XYZ=RGB Colors', d='Color for newly added transformation F-Curves (Location, Rotation, Scale) and also Color is based on the transform axis')
