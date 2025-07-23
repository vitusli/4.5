from . import _base

class BOperatorContext(_base.BStaticEnum):

	INVOKE_DEFAULT = dict(n='Invoke Default', d='Invoke Default')
	INVOKE_REGION_WIN = dict(n='Invoke Region Window', d='Invoke Region Window')
	INVOKE_REGION_CHANNELS = dict(n='Invoke Region Channels', d='Invoke Region Channels')
	INVOKE_REGION_PREVIEW = dict(n='Invoke Region Preview', d='Invoke Region Preview')
	INVOKE_AREA = dict(n='Invoke Area', d='Invoke Area')
	INVOKE_SCREEN = dict(n='Invoke Screen', d='Invoke Screen')
	EXEC_DEFAULT = dict(n='Exec Default', d='Exec Default')
	EXEC_REGION_WIN = dict(n='Exec Region Window', d='Exec Region Window')
	EXEC_REGION_CHANNELS = dict(n='Exec Region Channels', d='Exec Region Channels')
	EXEC_REGION_PREVIEW = dict(n='Exec Region Preview', d='Exec Region Preview')
	EXEC_AREA = dict(n='Exec Area', d='Exec Area')
	EXEC_SCREEN = dict(n='Exec Screen', d='Exec Screen')
