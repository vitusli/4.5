from . import _base

class BBoidruleType(_base.BStaticEnum):

	GOAL = dict(n='Goal', d='Go to assigned object or loudest assigned signal source')
	AVOID = dict(n='Avoid', d='Get away from assigned object or loudest assigned signal source')
	AVOID_COLLISION = dict(n='Avoid Collision', d='Maneuver to avoid collisions with other boids and deflector objects in near future')
	SEPARATE = dict(n='Separate', d='Keep from going through other boids')
	FLOCK = dict(n='Flock', d='Move to center of neighbors and match their velocity')
	FOLLOW_LEADER = dict(n='Follow Leader', d='Follow a boid or assigned object')
	AVERAGE_SPEED = dict(n='Average Speed', d='Maintain speed, flight level or wander')
	FIGHT = dict(n='Fight', d='Go to closest enemy and attack when in range')
