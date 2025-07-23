from . import _base

class BTextureType(_base.BStaticEnum):

	NONE = dict(n='None', d='None')
	BLEND = dict(n='Blend', d='Procedural - create a ramp texture')
	CLOUDS = dict(n='Clouds', d='Procedural - create a cloud-like fractal noise texture')
	DISTORTED_NOISE = dict(n='Distorted Noise', d='Procedural - noise texture distorted by two noise algorithms')
	IMAGE = dict(n='Image or Movie', d='Allow for images or movies to be used as textures')
	MAGIC = dict(n='Magic', d='Procedural - color texture based on trigonometric functions')
	MARBLE = dict(n='Marble', d='Procedural - marble-like noise texture with wave generated bands')
	MUSGRAVE = dict(n='Musgrave', d='Procedural - highly flexible fractal noise texture')
	NOISE = dict(n='Noise', d='Procedural - random noise, gives a different result every time, for every frame, for every pixel')
	STUCCI = dict(n='Stucci', d='Procedural - create a fractal noise texture')
	VORONOI = dict(n='Voronoi', d='Procedural - create cell-like patterns based on Worley noise')
	WOOD = dict(n='Wood', d='Procedural - wave generated bands or rings, with optional noise')
