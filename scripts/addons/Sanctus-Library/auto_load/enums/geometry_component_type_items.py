from . import _base

class BGeometryComponentType(_base.BStaticEnum):

	MESH = dict(n='Mesh', d='Mesh component containing point, corner, edge and face data')
	POINTCLOUD = dict(n='Point Cloud', d='Point cloud component containing only point data')
	CURVE = dict(n='Curve', d='Curve component containing spline and control point data')
	INSTANCES = dict(n='Instances', d='Instances of objects or collections')
