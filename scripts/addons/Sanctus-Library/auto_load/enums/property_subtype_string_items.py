from . import _base

class BPropertySubtypeString(_base.BStaticEnum):

	FILE_PATH = dict(n='File Path', d='File Path')
	DIR_PATH = dict(n='Directory Path', d='Directory Path')
	FILE_NAME = dict(n='File Name', d='File Name')
	BYTE_STRING = dict(n='Byte String', d='Byte String')
	PASSWORD = dict(n='Password', d='A string that is displayed hidden (’********’)')
	NONE = dict(n='None', d='None')
