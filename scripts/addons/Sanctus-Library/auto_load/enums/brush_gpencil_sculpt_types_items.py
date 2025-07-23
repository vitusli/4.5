from . import _base

class BBrushGPencilSculptTypes(_base.BStaticEnum):

	SMOOTH = dict(n='Smooth', d='Smooth stroke points')
	THICKNESS = dict(n='Thickness', d='Adjust thickness of strokes')
	STRENGTH = dict(n='Strength', d='Adjust color strength of strokes')
	RANDOMIZE = dict(n='Randomize', d='Introduce jitter/randomness into strokes')
	GRAB = dict(n='Grab', d='Translate the set of points initially within the brush circle')
	PUSH = dict(n='Push', d='Move points out of the way, as if combing them')
	TWIST = dict(n='Twist', d='Rotate points around the midpoint of the brush')
	PINCH = dict(n='Pinch', d='Pull points towards the midpoint of the brush')
	CLONE = dict(n='Clone', d='Paste copies of the strokes stored on the clipboard')
