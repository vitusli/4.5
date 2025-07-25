"""This module contains the update functions that handle changes of properties."""

from enum import Enum
import logging
import os
import bpy

LOGGER = logging.getLogger("af.property.updates")
LOGGER.setLevel(logging.DEBUG)


class AF_VariableQueryUpdateTarget(Enum):
	"""Enum to define which action should be taken after a variable query has been adjusted."""
	update_asset_list_parameter = "update_asset_list_parameter"
	update_implementation_list_parameter = "update_implementation_list_parameter"
	update_nothing = "update_nothing"

	@classmethod
	def to_property_enum(cls):
		return list(map(lambda c: (c.value, c.value, c.value), cls))

# General update functions

def update_download_directory_mode(property,context):
	if bpy.ops.af.update_implementations_list.poll():
		bpy.ops.af.update_implementations_list()

def update_download_directory_relative(property,context):
	property['relative_directory'] = os.path.normpath(property.relative_directory)

	if bpy.ops.af.update_implementations_list.poll():
		bpy.ops.af.update_implementations_list()

def update_download_directory_default(property,context):
	property['default_directory'] = os.path.normpath(property.default_directory)

	if bpy.ops.af.update_implementations_list.poll():
		bpy.ops.af.update_implementations_list()

def update_init_url(property, context):
	"""Function to run if the provider initialization url has changed."""
	LOGGER.debug("update_init_url")
	bpy.ops.af.initialize_provider()

	if bpy.ops.af.update_asset_list.poll():
		bpy.ops.af.update_asset_list()

	if bpy.ops.af.update_implementations_list.poll():
		bpy.ops.af.update_implementations_list()


def update_provider_header(property, context):
	"""Function to run if a provider header has changed."""
	LOGGER.debug("update_provider_header")
	if bpy.ops.af.connection_status.poll():
		LOGGER.debug("Getting connection status...")
		bpy.ops.af.connection_status()

	if bpy.ops.af.update_asset_list.poll():
		LOGGER.debug("Updating Asset List...")
		bpy.ops.af.update_asset_list()

	if bpy.ops.af.update_implementations_list.poll():
		LOGGER.debug("Updating Implementation List...")
		bpy.ops.af.update_implementations_list()


def update_asset_list_index(property, context):
	"""Function to run if a new asset has been selected aka the index in the asset list has changed."""
	LOGGER.debug("update_asset_list_index")
	bpy.context.window_manager.af.current_implementation_list_index = 0
	if bpy.ops.af.update_implementations_list.poll():
		bpy.ops.af.update_implementations_list()


def update_implementation_list_index(property, context):
	LOGGER.debug("update_implementation_list_index")

# Update functions for variable query parameters

def update_asset_list_parameter(property, context):
	LOGGER.debug("update_asset_list_parameter")
	if bpy.ops.af.update_asset_list.poll():
		bpy.ops.af.update_asset_list()

	if bpy.ops.af.update_implementations_list.poll():
		bpy.ops.af.update_implementations_list()


def update_implementation_list_parameter(property, context):
	LOGGER.debug("update_implementation_list_parameter")
	if bpy.ops.af.update_implementations_list.poll():
		bpy.ops.af.update_implementations_list()


def update_variable_query_parameter(property, context):
	LOGGER.debug("update_variable_query_parameter")
	if hasattr(property, "update_target"):
		if property.update_target == AF_VariableQueryUpdateTarget.update_implementation_list_parameter.value:
			update_implementation_list_parameter(property, context)
		if property.update_target == AF_VariableQueryUpdateTarget.update_asset_list_parameter.value:
			update_asset_list_parameter(property, context)
	else:
		LOGGER.warn(f"No update_target on {property}")


def update_bookmarks(property, context):
	from .preferences import AF_PR_Preferences
	LOGGER.debug("update_bookmarks")
	prefs = AF_PR_Preferences.get_prefs()
	selection = str(property.provider_bookmark_selection)
	if selection != "none":
		bpy.context.window_manager.af.current_init_url = prefs.provider_bookmarks[selection].init_url
