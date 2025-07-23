from . import _base

class BNodeBooleanMath(_base.BStaticEnum):

	AND = dict(n='And', d='True when both inputs are true')
	OR = dict(n='Or', d='True when at least one input is true')
	NOT = dict(n='Not', d='Opposite of the input')
	NAND = dict(n='Not And', d='True when at least one input is false')
	NOR = dict(n='Nor', d='True when both inputs are false')
	XNOR = dict(n='Equal', d='True when both inputs are equal (exclusive nor)')
	XOR = dict(n='Not Equal', d='True when both inputs are different (exclusive or)')
	IMPLY = dict(n='Imply', d='True unless the first input is true and the second is false')
	NIMPLY = dict(n='Subtract', d='True when the first input is true and the second is false (not imply)')
