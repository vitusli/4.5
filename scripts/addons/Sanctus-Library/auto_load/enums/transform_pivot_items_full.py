from . import _base

class BTransformPivotItemsFull(_base.BStaticEnum):

	BOUNDING_BOX_CENTER = dict(n='Bounding Box Center', d='Pivot around bounding box center of selected object(s)')
	CURSOR = dict(n='3D Cursor', d='Pivot around the 3D cursor')
	INDIVIDUAL_ORIGINS = dict(n='Individual Origins', d='Pivot around each object’s own origin')
	MEDIAN_POINT = dict(n='Median Point', d='Pivot around the median point of selected objects')
	ACTIVE_ELEMENT = dict(n='Active Element', d='Pivot around active object')
