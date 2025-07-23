from . import _base

class BWMReport(_base.BStaticEnum):

	DEBUG = dict(n='Debug', d='Debug')
	INFO = dict(n='Info', d='Info')
	OPERATOR = dict(n='Operator', d='Operator')
	PROPERTY = dict(n='Property', d='Property')
	WARNING = dict(n='Warning', d='Warning')
	ERROR = dict(n='Error', d='Error')
	ERROR_INVALID_INPUT = dict(n='Invalid Input', d='Invalid Input')
	ERROR_INVALID_CONTEXT = dict(n='Invalid Context', d='Invalid Context')
	ERROR_OUT_OF_MEMORY = dict(n='Out of Memory', d='Out of Memory')
