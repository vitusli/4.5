from . import _base

class BShadingType(_base.BStaticEnum):

	WIREFRAME = dict(n='Wireframe', d='Display the object as wire edges')
	SOLID = dict(n='Solid', d='Display in solid mode')
	MATERIAL = dict(n='Material Preview', d='Display in Material Preview mode')
	RENDERED = dict(n='Rendered', d='Display render preview')
