from . import _base

class BStereo3DDisplay(_base.BStaticEnum):

	ANAGLYPH = dict(n='Anaglyph', d='Render views for left and right eyes as two differently filtered colors in a single image (anaglyph glasses are required)')
	INTERLACE = dict(n='Interlace', d='Render views for left and right eyes interlaced in a single image (3D-ready monitor is required)')
	TIMESEQUENTIAL = dict(n='Time Sequential', d='Render alternate eyes (also known as page flip, quad buffer support in the graphic card is required)')
	SIDEBYSIDE = dict(n='Side-by-Side', d='Render views for left and right eyes side-by-side')
	TOPBOTTOM = dict(n='Top-Bottom', d='Render views for left and right eyes one above another')
