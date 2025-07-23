from . import _base

class BRigidbodyConstraintType(_base.BStaticEnum):

	FIXED = dict(n='Fixed', d='Glue rigid bodies together')
	POINT = dict(n='Point', d='Constrain rigid bodies to move around common pivot point')
	HINGE = dict(n='Hinge', d='Restrict rigid body rotation to one axis')
	SLIDER = dict(n='Slider', d='Restrict rigid body translation to one axis')
	PISTON = dict(n='Piston', d='Restrict rigid body translation and rotation to one axis')
	GENERIC = dict(n='Generic', d='Restrict translation and rotation to specified axes')
	GENERIC_SPRING = dict(n='Generic Spring', d='Restrict translation and rotation to specified axes with springs')
	MOTOR = dict(n='Motor', d='Drive rigid body around or along an axis')
