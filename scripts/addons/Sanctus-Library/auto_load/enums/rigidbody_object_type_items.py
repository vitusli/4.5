from . import _base

class BRigidbodyObjectType(_base.BStaticEnum):

	ACTIVE = dict(n='Active', d='Object is directly controlled by simulation results')
	PASSIVE = dict(n='Passive', d='Object is directly controlled by animation system')
