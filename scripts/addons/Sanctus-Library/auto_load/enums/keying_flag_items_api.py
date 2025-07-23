from . import _base

class BKeyingFlagApi(_base.BStaticEnum):

	INSERTKEY_NEEDED = dict(n='Only Needed', d='Only insert keyframes where they’re needed in the relevant F-Curves')
	INSERTKEY_VISUAL = dict(n='Visual Keying', d='Insert keyframes based on ‘visual transforms’')
	INSERTKEY_XYZ_TO_RGB = dict(n='XYZ=RGB Colors', d='Color for newly added transformation F-Curves (Location, Rotation, Scale) and also Color is based on the transform axis')
	INSERTKEY_REPLACE = dict(n='Replace Existing', d='Only replace existing keyframes')
	INSERTKEY_AVAILABLE = dict(n='Only Available', d='Don’t create F-Curves when they don’t already exist')
	INSERTKEY_CYCLE_AWARE = dict(n='Cycle Aware Keying', d='When inserting into a curve with cyclic extrapolation, remap the keyframe inside the cycle time range, and if changing an end key, also update the other one')
