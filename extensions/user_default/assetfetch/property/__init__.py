"""This module contains all data classes. This includes core data for the addon itself, as well as representations of all datablocks."""

import os
from typing import Dict
import bpy

from .core import *
from .datablocks import *
from .templates import *
from .preferences import *


def register():

	for cl in registration_targets:
		bpy.utils.register_class(cl)

	bpy.types.WindowManager.af = bpy.props.PointerProperty(type=AF_PR_AssetFetch)


def unregister():

	del bpy.types.WindowManager.af

	for cl in reversed(registration_targets):
		bpy.utils.unregister_class(cl)


registration_targets = [
	AF_PR_GenericString,
	AF_PR_FixedQuery,
	AF_PR_BoolParameter,
	AF_PR_TextParameter,
	AF_PR_FixedParameter,
	AF_PR_SelectParameterChoice,
	AF_PR_SelectParameter,
	AF_PR_VariableQuery,
	AF_PR_Header,
	AF_PR_TextBlock,
	AF_PR_UserBlock,
	AF_PR_HandleNativeBlock,
	AF_PR_HandleArchiveBlock,
	AF_PR_ProviderConfigurationBlock,
	AF_PR_ProviderReconfigurationBlock,
	AF_PR_UnlockBalanceBlock,
	AF_PR_FetchFromArchiveBlock,
	AF_PR_HandleLooseEnvironmentBlock,
	AF_PR_HandleLooseMaterialMapBlock,
	AF_PR_LinkLooseMaterialBlock,
	AF_PR_FormatBlendTarget,
	AF_PR_FormatBlendBlock,
	AF_PR_FormatObjBlock,
	AF_PR_UnlockQuery,
	AF_PR_UnlockQueriesBlock,
	AF_PR_PreviewImageThumbnailBlock,
	AF_PR_ProviderInitialization,
	AF_PR_ConnectionStatus,
	AF_PR_Asset,
	AF_PR_AssetList,
	AF_PR_BlenderResource,
	AF_PR_StoreBlock,
	AF_PR_FetchDownloadBlock,
	AF_PR_FormatBlock,
	AF_PR_Component,
	AF_PR_ImplementationImportStep,
	AF_PR_ImplementationValidationMessage,
	AF_PR_Implementation,
	AF_PR_ImplementationList,
	AF_PR_AssetFetch,
	AF_PR_ProviderBookmark,
	AF_PR_Preferences
]
