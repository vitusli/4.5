from . import _base

class BObjectType(_base.BStaticEnum):

	MESH = dict(n='Mesh', d='Mesh')
	CURVE = dict(n='Curve', d='Curve')
	SURFACE = dict(n='Surface', d='Surface')
	META = dict(n='Metaball', d='Metaball')
	FONT = dict(n='Text', d='Text')
	CURVES = dict(n='Hair Curves', d='Hair Curves')
	POINTCLOUD = dict(n='Point Cloud', d='Point Cloud')
	VOLUME = dict(n='Volume', d='Volume')
	GPENCIL = dict(n='Grease Pencil', d='Grease Pencil')
	ARMATURE = dict(n='Armature', d='Armature')
	LATTICE = dict(n='Lattice', d='Lattice')
	EMPTY = dict(n='Empty', d='Empty')
	LIGHT = dict(n='Light', d='Light')
	LIGHT_PROBE = dict(n='Light Probe', d='Light Probe')
	CAMERA = dict(n='Camera', d='Camera')
	SPEAKER = dict(n='Speaker', d='Speaker')
