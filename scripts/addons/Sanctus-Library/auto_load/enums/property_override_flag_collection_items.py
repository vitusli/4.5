from . import _base

class BPropertyOverrideFlagCollection(_base.BStaticEnum):

	LIBRARY_OVERRIDABLE = dict(n='Library Overridable', d='Make that property editable in library overrides of linked data-blocks')
	NO_PROPERTY_NAME = dict(n='No Name', d='Do not use the names of the items, only their indices in the collection')
	USE_INSERTION = dict(n='Use Insertion', d='Allow users to add new items in that collection in library overrides')
