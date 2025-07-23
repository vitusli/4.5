from . import _base

class BBakeSaveMode(_base.BStaticEnum):

	INTERNAL = dict(n='Internal', d='Save the baking map in an internal image data-block')
	EXTERNAL = dict(n='External', d='Save the baking map in an external file')
