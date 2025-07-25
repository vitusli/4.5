"""This module contains the relevant classes for the addon's preferences."""

import bpy
from .. import ADDON_NAME
from .templates import *
from .updates import *


class AF_PR_ProviderBookmark(bpy.types.PropertyGroup):
	"""Represents a bookmark for a provider."""
	init_url: bpy.props.StringProperty(default="(URI)", description="The initialization URL for this provider.", name="URI")
	header_values: bpy.props.CollectionProperty(type=AF_PR_GenericString)


class AF_PR_Preferences(bpy.types.AddonPreferences):
	"""The main class containing all preferences for the addon."""

	# Here we use the ADDON_NAME from the init module to determine the idname to use for the addon.
	bl_idname = ADDON_NAME

	# Display mode
	display_mode: bpy.props.EnumProperty(
		items=[
		("directory", "Download Directory", "Download Directory"),  # Download directory
		("bookmarks", "Provider Bookmarks", "Provider Bookmarks")  # Bookmarks
		],
		default="directory")

	# Special property for detecting if the defaults have been loaded already.
	# This is required to make the built-in bookmarks possible
	is_initialized: bpy.props.BoolProperty(default=False)

	# Bookmarks
	provider_bookmarks: bpy.props.CollectionProperty(type=AF_PR_ProviderBookmark)
	provider_bookmarks_index: bpy.props.IntProperty(default=0)
	provider_bookmarks_headers_index: bpy.props.IntProperty(default=0)

	# Directories
	use_relative: bpy.props.BoolProperty(update=update_download_directory_mode)
	relative_directory: bpy.props.StringProperty(default="AssetFetch",update=update_download_directory_relative)
	default_directory: bpy.props.StringProperty(default=os.path.join(os.path.expanduser('~'), "AssetFetch"),update=update_download_directory_default)

	def get_current_download_directory(self):
		if bpy.data.filepath != '' and self.use_relative:
			return os.path.join(os.path.dirname(bpy.data.filepath),self.relative_directory)
		return self.default_directory

	def get_current_bookmark_in_preferences(self) -> AF_PR_ProviderBookmark | None:
		return self.provider_bookmarks[self.provider_bookmarks_index]

	def draw(self, context):
		from ..ui.preferences import draw_preferences

		draw_preferences(self, self.layout, context,inside_blender_preferences=True)

	def populate_defaults(prefs):
		"""Adds the initial bookmarks that are built into the addon."""
		# ambientCG
		acg_bookmark = prefs.provider_bookmarks.add()
		acg_bookmark.name = "ambientCG"
		acg_bookmark.init_url = "https://ambientcg.com/api/af/init"

		prefs.is_initialized = True

	@staticmethod
	def get_prefs():
		"""Returns the preferences object."""
		prefs = bpy.context.preferences.addons[ADDON_NAME].preferences
		# TODO: This isn't the best place to put this!
		if prefs and not prefs.is_initialized:
			AF_PR_Preferences.populate_defaults(prefs)

		return prefs
