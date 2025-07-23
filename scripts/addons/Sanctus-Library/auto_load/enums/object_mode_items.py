from . import _base

class BObjectMode(_base.BStaticEnum):

	OBJECT = dict(n='Object Mode', d='Object Mode')
	EDIT = dict(n='Edit Mode', d='Edit Mode')
	POSE = dict(n='Pose Mode', d='Pose Mode')
	SCULPT = dict(n='Sculpt Mode', d='Sculpt Mode')
	VERTEX_PAINT = dict(n='Vertex Paint', d='Vertex Paint')
	WEIGHT_PAINT = dict(n='Weight Paint', d='Weight Paint')
	TEXTURE_PAINT = dict(n='Texture Paint', d='Texture Paint')
	PARTICLE_EDIT = dict(n='Particle Edit', d='Particle Edit')
	EDIT_GPENCIL = dict(n='Edit Mode', d='Edit Grease Pencil Strokes')
	SCULPT_GPENCIL = dict(n='Sculpt Mode', d='Sculpt Grease Pencil Strokes')
	PAINT_GPENCIL = dict(n='Draw Mode', d='Paint Grease Pencil Strokes')
	WEIGHT_GPENCIL = dict(n='Weight Paint', d='Grease Pencil Weight Paint Strokes')
	VERTEX_GPENCIL = dict(n='Vertex Paint', d='Grease Pencil Vertex Paint Strokes')
	SCULPT_CURVES = dict(n='Sculpt Mode', d='Sculpt Mode')
