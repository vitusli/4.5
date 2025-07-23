from . import _base

class BBakePassType(_base.BStaticEnum):

	COMBINED = dict(n='Combined', d='Combined')
	AO = dict(n='Ambient Occlusion', d='Ambient Occlusion')
	SHADOW = dict(n='Shadow', d='Shadow')
	POSITION = dict(n='Position', d='Position')
	NORMAL = dict(n='Normal', d='Normal')
	UV = dict(n='UV', d='UV')
	ROUGHNESS = dict(n='ROUGHNESS', d='ROUGHNESS')
	EMIT = dict(n='Emit', d='Emit')
	ENVIRONMENT = dict(n='Environment', d='Environment')
	DIFFUSE = dict(n='Diffuse', d='Diffuse')
	GLOSSY = dict(n='Glossy', d='Glossy')
	TRANSMISSION = dict(n='Transmission', d='Transmission')
