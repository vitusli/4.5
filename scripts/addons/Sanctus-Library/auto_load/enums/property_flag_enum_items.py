from . import _base

class BPropertyFlagEnum(_base.BStaticEnum):

	HIDDEN = dict(n='Hidden', d='Hidden')
	SKIP_SAVE = dict(n='Skip Save', d='Skip Save')
	ANIMATABLE = dict(n='Animatable', d='Animatable')
	LIBRARY_EDITABLE = dict(n='Library Editable', d='Library Editable')
	ENUM_FLAG = dict(n='Enum Flag', d='Enum Flag')
