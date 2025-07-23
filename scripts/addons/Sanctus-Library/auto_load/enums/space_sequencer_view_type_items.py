from . import _base

class BSpaceSequencerViewType(_base.BStaticEnum):

	SEQUENCER = dict(n='Sequencer', d='Sequencer')
	PREVIEW = dict(n='Preview', d='Preview')
	SEQUENCER_PREVIEW = dict(n='Sequencer & Preview', d='Sequencer & Preview')
