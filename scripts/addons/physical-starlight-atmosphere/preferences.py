# ##### BEGIN GPL LICENSE BLOCK #####
# Physical Starlight and Atmosphere is is a completely volumetric procedural
# sky, sunlight, and atmosphere simulator addon for Blender
# Copyright (C) 2024  Physical Addons

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
# ##### END GPL LICENSE BLOCK #####

# External library imports
import bpy
from bpy.props import *

# Project module imports
from . ui import *  # RIG_PT_StarlightAtmosphere
from . handlers import enable_atmosphere
from . sunlight import sun_calculation
from . variables import *
import shutil


def update_toolbar_label(self, context):
    """
    Update the toolbar label.
    """

    classes = [
        RIG_PT_StarlightAtmosphereTB,
        RIG_PT_SunTB,
        RIG_PT_BinarySunTB,
        RIG_PT_AtmosphereTB,
        RIG_PT_StarsTB,
        RIG_PT_PhysicalCloudsTB,
        RIG_PT_ObjectFogTB,
        RIG_PT_GroundTB,
        RIG_PT_ArtisticControlsTB,
        RIG_PT_FooterTB,
        RIG_PT_SubFooterTB,
    ]
    
    # Check if the panel exists
    panel_exists = hasattr(bpy.types, 'RIG_PT_StarlightAtmosphereTB')
    
    if panel_exists == True:
        # Unregister classes
        for cls in classes:
            bpy.utils.unregister_class(cls)

    # Set Toolbar Label
    RIG_PT_StarlightAtmosphereTB.bl_category = self.toolbar_label

    # Register classes
    for cls in classes:
        bpy.utils.register_class(cls)


def toggle_physical_values(self, context):
    """
    Toggles the intensity multiplier based on the 'use_physical_values' preference.
    """    

    # Get preferences and general settings
    addon_prefs = context.preferences.addons[__name__.split(".")[0]].preferences
    general_settings = context.scene.world.psa_general_settings
    
    # Update intensity multiplier based on the 'use_physical_values' preference
    if addon_prefs.use_physical_values == True:
        general_settings.intensity_multiplier = 64
    else:
        general_settings.intensity_multiplier = 1

    # Redraw the scene if the addon is enabled
    if general_settings.enabled == True:
        depsgraph = bpy.context.evaluated_depsgraph_get()
        sun_calculation(bpy.context, depsgraph, 'realtime') 


def toggle_aces(self, context):
    """
    Toggles the use of ACES color space conversion in the node tree.
    """

    # Check if the addon is enabled
    general_settings = context.scene.world.psa_general_settings
    if not general_settings.enabled:
        return

    # Get the node tree
    node_tree = context.scene.world.node_tree
    world_output_name = context.scene.world.psa_exposed.output_node_name
    world_output_node = node_tree.nodes.get(world_output_name)
    atmosphere = node_tree.nodes[STARLIGHT_ATMOSPHERE_NODE_NAME]
    converter = node_tree.nodes[ACES_CONVERTER_NODE_NAME]

    # Toggle ACES conversion based on the operator's property
    if self.use_aces == 1:
        node_tree.links.new(converter.outputs[0], world_output_node.inputs[0])
        node_tree.links.new(atmosphere.outputs[0], converter.inputs[0])
    else:
        node_tree.links.new(atmosphere.outputs[0], world_output_node.inputs[0])


def setup_default_presets(overwrite=False):
	psa_presets_dir = os.path.join(bpy.utils.user_resource('DATAFILES'), "presets", "PSA")
	src_presets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "presets")

	if not os.path.exists(psa_presets_dir):
		os.makedirs(psa_presets_dir)
	for filename in os.listdir(src_presets_dir):
		src_preset_path = os.path.join(src_presets_dir, filename)
		if os.path.isfile(src_preset_path):
			trg_preset_path = os.path.join(psa_presets_dir, filename)
			if not os.path.isfile(trg_preset_path) or overwrite:
				shutil.copy2(src_preset_path, psa_presets_dir)
	return 0


class RIG_OT_OpenDocumentation(bpy.types.Operator):
    """
    Open documentation in the specified URL.
    """    

    bl_idname = 'rig.open_exp_features_page'
    bl_label = 'Read more'
    bl_options = {'REGISTER', 'INTERNAL'}
    bl_description = "Read about this feature in the documentation"
    link: bpy.props.StringProperty()

    def execute(self, context):
        # Open the URL
        bpy.ops.wm.url_open(url='https://www.physicaladdons.com/psa/customization/#preferences')
        return {'FINISHED'}


class PSA_OT_ReloadDefaultPresets(bpy.types.Operator):
    """
    Hard reload default presets.
    """    

    bl_idname = 'psa.reload_default_presets'
    bl_label = 'Reload Default Presets'
    bl_description = "Reload default presets, overwriting any changes made to them!"

    def execute(self, context):
        setup_default_presets(overwrite = True)

        return {'FINISHED'}


class RIG_MT_addon_preferences(bpy.types.AddonPreferences):

    bl_idname = __name__.split(".")[0]  # __name__ would be physical-starlight-atmosphere.preferences

    use_physical_values: bpy.props.BoolProperty(
        default=False,
        description="Use real world physical values",
        update=toggle_physical_values
    )

    use_aces: bpy.props.BoolProperty(
        default=False,
        description="Use ACES color space",
        update=toggle_aces
    )

    toolbar_enabled: bpy.props.BoolProperty(
        default=True,
        description="Toggle Toolbar (N panel)",
    )

    toolbar_label: bpy.props.StringProperty(   
        description="Choose addon name for the Toolbar (N panel)",
        default="Atmosphere",
        update=update_toolbar_label
    )

    def draw(self, context):
        layout = self.layout

        # Toolbar Settings
        box = layout.box()
        col = box.column()
        row = col.row(align=True)
        row.prop(self, "toolbar_enabled", text="Toolbar enabled")
        operatorColumn = row.column(align=True)
        operatorColumn.alignment = "RIGHT"
        btn = operatorColumn.operator(RIG_OT_OpenDocumentation.bl_idname, icon='URL')
        col.label(text="Toolbar label:")
        row = col.split(factor=0.5, align=True)
        row.prop(self, "toolbar_label", text="")

        # ACES Settings
        box = layout.box()
        row = box.row(align=True)
        row.prop(self, "use_aces", text="Use ACES color space" )
        operatorColumn = row.column(align=True)
        operatorColumn.alignment = "RIGHT"
        btn = operatorColumn.operator(RIG_OT_OpenDocumentation.bl_idname, icon='URL')

        # Physical Values Settings
        row = box.row(align=True) 
        row.prop(self, "use_physical_values", text="Use real world physical values")
        operatorColumn = row.column(align=True)
        operatorColumn.alignment = "RIGHT"
        btn = operatorColumn.operator(RIG_OT_OpenDocumentation.bl_idname, icon='URL')

        # Reload presets

        box = layout.box()
        row = box.row(align = True)

        row.label(text = "Reload default presets:")
        operatorColumn = row.column(align=True)
        operatorColumn.alignment = "RIGHT"
        btn = operatorColumn.operator("psa.reload_default_presets", icon = 'FILE_REFRESH', text = 'Reload')
