from . import _base

class BPropertyFlag(_base.BStaticEnum):

	HIDDEN = dict(n='Hidden', d='Hidden')
	SKIP_SAVE = dict(n='Skip Save', d='Skip Save')
	ANIMATABLE = dict(n='Animatable', d='Animatable')
	LIBRARY_EDITABLE = dict(n='Library Editable', d='Library Editable')
	PROPORTIONAL = dict(n='Adjust values proportionally to each other', d='Adjust values proportionally to each other')
	TEXTEDIT_UPDATE = dict(n='Update on every keystroke in textedit ‘mode’', d='Update on every keystroke in textedit ‘mode’')
	OUTPUT_PATH = dict(n='Output Path', d='Output Path')
