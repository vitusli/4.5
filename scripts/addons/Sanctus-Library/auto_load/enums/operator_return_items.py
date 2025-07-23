from . import _base

class BOperatorReturn(_base.BStaticEnum):

	RUNNING_MODAL = dict(n='Running Modal', d='Keep the operator running with blender')
	CANCELLED = dict(n='Cancelled', d='The operator exited without doing anything, so no undo entry should be pushed')
	FINISHED = dict(n='Finished', d='The operator exited after completing its action')
	PASS_THROUGH = dict(n='Pass Through', d='Do nothing and pass the event on')
	INTERFACE = dict(n='Interface', d='Handled but not executed (popup menus)')
