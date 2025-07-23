from . import _base

class BFileselectParamsSort(_base.BStaticEnum):

	FILE_SORT_ALPHA = dict(n='Name', d='Sort the file list alphabetically')
	FILE_SORT_EXTENSION = dict(n='Extension', d='Sort the file list by extension/type')
	FILE_SORT_TIME = dict(n='Modified Date', d='Sort files by modification time')
	FILE_SORT_SIZE = dict(n='Size', d='Sort files by size')
