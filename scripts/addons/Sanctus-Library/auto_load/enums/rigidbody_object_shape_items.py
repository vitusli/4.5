from . import _base

class BRigidbodyObjectShape(_base.BStaticEnum):

	BOX = dict(n='Box', d='Box-like shapes (i.e. cubes), including planes (i.e. ground planes)')
	SPHERE = dict(n='Sphere', d='Sphere')
	CAPSULE = dict(n='Capsule', d='Capsule')
	CYLINDER = dict(n='Cylinder', d='Cylinder')
	CONE = dict(n='Cone', d='Cone')
	CONVEX_HULL = dict(n='Convex Hull', d='A mesh-like surface encompassing (i.e. shrinkwrap over) all vertices (best results with fewer vertices)')
	MESH = dict(n='Mesh', d='Mesh consisting of triangles only, allowing for more detailed interactions than convex hulls')
	COMPOUND = dict(n='Compound Parent', d='Combines all of its direct rigid body children into one rigid object')
