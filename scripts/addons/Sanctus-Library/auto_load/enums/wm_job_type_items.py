from . import _base

class BWMJobType(_base.BStaticEnum):

	RENDER = dict(n='Regular rendering', d='Regular rendering')
	RENDER_PREVIEW = dict(n='Rendering previews', d='Rendering previews')
	OBJECT_BAKE = dict(n='Object Baking', d='Object Baking')
	COMPOSITE = dict(n='Compositing', d='Compositing')
	SHADER_COMPILATION = dict(n='Shader compilation', d='Shader compilation')
