'''
Sanctus Library baking is split up into 3 responsibilities:
    1. queue: storing and managing settings for baking. This includes the different bake mappings and baking settings
    2. operators: executing bake commands and instantiating node setups
    3. texture_sets: storing and managing results from baking
'''

from . import (operators, queue, settings, setup, texture_sets, ui, utils)
