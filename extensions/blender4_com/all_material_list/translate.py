import bpy
import os, csv, codecs
from pathlib import Path
cwf = Path(__file__)
cwd = cwf.parent
def GetTranslationDict():
	dict = {}
	path = cwd/"trans_dict"

	with codecs.open(path, 'r', 'utf-8') as f:
		reader = csv.reader(f)
		dict['zh_HANS'] = {}
		for row in reader:
			if row:
				for context in bpy.app.translations.contexts:
					dict['zh_HANS'][(context, row[0].replace('\\n', '\n'))] = row[1].replace('\\n', '\n')
	return dict
def register():
	try:
		bpy.app.translations.register(__package__, GetTranslationDict())
	except Exception as e:
		print(e)
def unregister():
	try:
		bpy.app.translations.unregister(__package__)
	except Exception as e:
		print(e)