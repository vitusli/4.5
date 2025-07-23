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
from bpy.types import (
    Panel, 
    Operator,
    UIList,
)

import os, sys, subprocess

# Project module imports
from . handlers import (
    toggle_fog
)
from . helpers import current_addon_version
from . properties import *


############################################################################
# BASE CLASSES
############################################################################

# Base for World tab
class RIG_WT:
    bl_parent_id = "RIG_PT_StarlightAtmosphereWT"
    bl_region_type = "WINDOW"
    bl_space_type = "PROPERTIES"
    bl_context = "world"
    bl_options = {'DEFAULT_CLOSED'}

class RIG_TB:
    bl_parent_id = "RIG_PT_StarlightAtmosphereTB"
    bl_region_type = "UI"
    bl_space_type = "VIEW_3D"
    bl_context = "objectmode"
    bl_options = {'DEFAULT_CLOSED'}

# Base class
class DrawablePanel:
    @classmethod
    def poll(self, context):
        settings_available = context.scene and hasattr(context.scene.world, 'psa_atmosphere_settings')
        if not settings_available:
            return False
        
        # toolbar preferences are stored under preferences Class.
        prefs = context.preferences.addons[__name__.split(".")[0]].preferences
        if self.bl_context == "objectmode" and not prefs.toolbar_enabled:  # if drawing toolbar but it's not enabled
            return False
        
        if context.scene.world.psa_general_settings.enabled:
            return True
        return False

    def draw_header(self, context):
        self.layout.label(text='', icon=self.icon_name)

    # indented column with a padding from left
    def indented_column(self, squished=True):
        row = self.layout.row()
        row.separator()
        return row.column(align=squished)


############################################################################
# StarlightAtmosphere
############################################################################

class StarlightAtmosphere(DrawablePanel):
    bl_label = "PSA Atmosphere"

    @classmethod
    def poll(self, context):
        # Overriding poll method as this UI part should be present even without a world.
        prefs = context.preferences.addons[__name__.split(".")[0]].preferences
        if self.bl_context == "objectmode" and not prefs.toolbar_enabled:
            return False
        return True

    def draw_header(self, context):
        if context.scene.world:
            general_settings = context.scene.world.psa_general_settings # psa_gsettings
            layout = self.layout
            #layout.prop(general_settings, 'enabled', text='')

    def draw(self, context):
        if context.scene:
            layout = self.layout
            if context.scene.world is None:
                layout.label(text="A world is required.", icon='ERROR')
                layout.template_ID(context.scene, "world", new="world.new")
            else:
                if context.scene.world.psa_general_settings.enabled:
                    layout.enabled = False
                    if context.scene.world.psa_general_settings.enabled:
                        layout.enabled = True
                    # Preset UI
                    world = context.scene.world
                    col = layout.column()
                    col.label(text="Presets:")
                    if world.psa_exposed.show_presets:
                        preset_text = "Select Preset"
                        if world.psa_exposed.preset_index >= 0:
                            preset_text = world.psa_exposed.presets[world.psa_exposed.preset_index].name
                        col.prop(world.psa_exposed, "show_presets", icon="DOWNARROW_HLT", text=preset_text)
                        box = col.box()
                        box.template_list("PSA_UL_PresetList", "", context.scene.world.psa_exposed, "presets", context.scene.world.psa_exposed, "preset_index", rows=6)
                        box.prop(world.psa_exposed, "apply_preset_sun_data")
                    else:
                        preset_text = "Select Preset"
                        if world.psa_exposed.preset_index >= 0:
                            preset_text = world.psa_exposed.presets[world.psa_exposed.preset_index].name
                        col.prop(world.psa_exposed, "show_presets", icon="RIGHTARROW_THIN", text=preset_text)
                    box = col.box()
                    row = box.row()
                    row.enabled = False
                    if world.psa_exposed.preset_index >= 0:
                        row.enabled = True # Only enable this row of controls when a non-default preset is selected
                    row.operator("psa.save_current_preset", icon="FILE_TICK", text="Save")
                    row.operator("psa.delete_current_preset", icon="TRASH", text="")
                    row = box.row()
                    row.operator("psa.create_new_preset", icon="ADD")
                    row.operator("psa.open_presets_folder", icon="FILE_FOLDER", text="")
                else:
                    layout.operator("psa.add_atmosphere", icon="ADD", text="Add Atmosphere")


class RIG_PT_StarlightAtmosphereWT(Panel, StarlightAtmosphere):
    bl_idname = "RIG_PT_StarlightAtmosphereWT"
    bl_region_type = "WINDOW"            # location of the panel
    bl_space_type = "PROPERTIES"
    bl_context = "world"


class RIG_PT_StarlightAtmosphereTB(Panel, StarlightAtmosphere):
    bl_idname = "RIG_PT_StarlightAtmosphereTB"
    bl_region_type = "UI"          # location of the panel
    bl_space_type = "VIEW_3D"      # Region not found in space type if PROPERTIES used
    bl_context = "objectmode"      # without objectmode it is not appearing as a tab
    bl_category = "Atmosphere"      # Tab label


############################################################################
# Sun
############################################################################
class Sun(DrawablePanel):
    bl_label = "Sun"
    icon_name = "LIGHT_SUN"

    def draw(self, context):
        if context.scene and hasattr(context.scene.world, 'psa_general_settings'):
            general_settings = context.scene.world.psa_general_settings # psa_gsettings
            atmosphere_settings = context.scene.world.psa_atmosphere_settings # asettings
            sun = context.scene.world.psa_exposed.sun_object
            layout = self.layout
            layout.enabled = general_settings.enabled
            col = self.indented_column()
            if sun:
                col.label(text='Rotation:')
                col.prop(sun, 'rotation_euler', index=2, text="Horizontal")
                col.prop(sun, 'rotation_euler', index=0, text="Vertical")
            col.prop(atmosphere_settings, 'sun_disk')
            col.prop(atmosphere_settings, 'sun_lamp')
            col.prop(atmosphere_settings, 'sun_diameter')
            col.prop(atmosphere_settings, 'sun_temperature')
            col.prop(atmosphere_settings, 'sun_intensity')
            # if prefs.use_experimental_features:
            col.prop(atmosphere_settings, 'enable_binary_sun')

#? Whats the point for this classes? I imagine theyre required by Blender for some reason, yes?
class RIG_PT_SunWT(RIG_WT, Panel, Sun):
    pass

class RIG_PT_SunTB(RIG_TB, Panel, Sun):
    pass


############################################################################
# Binary Sun
############################################################################
class BinarySun(DrawablePanel):
    bl_label = "Binary Sun"
    icon_name = "LIGHT_SUN"

    @classmethod
    def poll(self, context):
        settings_available = context.scene and hasattr(context.scene.world, 'psa_atmosphere_settings')
        if not settings_available:
            return False
        prefs = context.preferences.addons[__name__.split(".")[0]].preferences
        atmosphere_settings = context.scene.world.psa_atmosphere_settings
        if atmosphere_settings.enable_binary_sun:
            if self.bl_context == "objectmode" and not prefs.toolbar_enabled:
                return False
            elif context.scene.world.psa_general_settings.enabled:
                return True
            return False
        else:
            return False


    def draw(self, context):
        if context.scene and hasattr(context.scene.world, 'psa_general_settings'):
            general_settings = context.scene.world.psa_general_settings
            atmosphere_settings = context.scene.world.psa_atmosphere_settings
            layout = self.layout
            layout.enabled = general_settings.enabled
            col = self.indented_column()
            col.prop(atmosphere_settings, 'binary_distance')
            col.prop(atmosphere_settings, 'binary_phase')
            col.prop(atmosphere_settings, 'binary_diameter')
            col.prop(atmosphere_settings, 'binary_temperature')
            col.prop(atmosphere_settings, 'binary_intensity')

#? Whats the point for this classes? I imagine theyre required by Blender for some reason, yes?
class RIG_PT_BinarySunWT(RIG_WT, Panel, BinarySun):
    pass

class RIG_PT_BinarySunTB(RIG_TB, Panel, BinarySun):
    pass


############################################################################
# Atmosphere
############################################################################
class Atmosphere(DrawablePanel):
    bl_label = "Atmosphere"
    icon_name= "WORLD_DATA"

    def draw(self, context):
        general_settings = context.scene.world.psa_general_settings
        atmosphere_settings = context.scene.world.psa_atmosphere_settings
        layout = self.layout
        layout.enabled = general_settings.enabled

        col = self.indented_column()
        col.prop(atmosphere_settings, 'atmosphere_density')
        col.prop(atmosphere_settings, 'atmosphere_height')
        col.prop(atmosphere_settings, 'atmosphere_intensity')
        col = self.indented_column()
        col.prop(atmosphere_settings, 'night_intensity')

        # inline color fields
        col = self.indented_column()
        row = col.row(align=True)
        row.label(text='Color:')
        row.prop(atmosphere_settings, 'atmosphere_color')
        row = col.row(align=True)
        row.label(text='Inscattering:')
        row.prop(atmosphere_settings, 'atmosphere_inscattering')
        row = col.row(align=True)
        row.label(text='Absorption:')
        row.prop(atmosphere_settings, 'atmosphere_extinction')

        col.label(text='Mie Scattering:')
        col.prop(atmosphere_settings, 'atmosphere_mie')
        col.prop(atmosphere_settings, 'atmosphere_mie_dir')

#? Whats the point for this classes? I imagine theyre required by Blender for some reason, yes?
class RIG_PT_AtmosphereWT(RIG_WT, Panel, Atmosphere):
    pass

class RIG_PT_AtmosphereTB(RIG_TB, Panel, Atmosphere):
    pass


############################################################################
# Stars
############################################################################
class Stars(DrawablePanel):
    bl_label = "Stars"
    icon_name = 'STICKY_UVS_DISABLE'

    def draw(self, context):
        if context.scene and hasattr(context.scene.world, 'psa_general_settings'):
            general_settings = context.scene.world.psa_general_settings
            atmosphere_settings = context.scene.world.psa_atmosphere_settings
            stars_type = atmosphere_settings.stars_type
            layout = self.layout
            layout.enabled = general_settings.enabled

            row = layout.row(align=True)
            row.prop(atmosphere_settings, 'stars_type', expand=True)

            if stars_type in {'procedural', 'texture'}:
                col = self.indented_column()
            if stars_type == 'texture':
                col.template_ID(atmosphere_settings, 'stars_texture', open="image.open", new="image.new")
                col.prop(atmosphere_settings, 'stars_intensity')
                col.prop(atmosphere_settings, 'stars_gamma')
            if stars_type in {'procedural'}:
                col.prop(atmosphere_settings, 'stars_intensity')
                col.prop(atmosphere_settings, 'stars_gamma')
                col.prop(atmosphere_settings, 'stars_amount')
                col.prop(atmosphere_settings, 'stars_scale')
                col.prop(atmosphere_settings, 'stars_seed')
                col.prop(atmosphere_settings, 'stars_temperature_min')
                col.prop(atmosphere_settings, 'stars_temperature_max')


class RIG_PT_StarsWT(RIG_WT, Panel, Stars):
    pass


class RIG_PT_StarsTB(RIG_TB, Panel, Stars):
    pass


############################################################################
# Object Fog
############################################################################

class ObjectFog(DrawablePanel):
    bl_label = "Object Fog" 
    icon_name = "MATERIAL"
    properties_type = "objectfog"

    def draw(self, context):
        if context.scene and hasattr(context.scene.world, 'psa_general_settings'):
            general_settings = context.scene.world.psa_general_settings
            atmosphere_settings = context.scene.world.psa_atmosphere_settings
            fog_state = atmosphere_settings.fog_state
            layout = self.layout
            layout.enabled = general_settings.enabled

            row = layout.row(align=True)
            row.prop(atmosphere_settings, 'fog_state', expand=True)
            col = self.indented_column()
            col.label(text='Fog applied to ' + str(general_settings.material_with_fog_count) + '/' + str(len(bpy.data.materials)) + ' materials')
            if fog_state == 'manual':
                row = col.row(align=True)
                row.operator(RIG_OT_ApplyObjectFog.bl_idname, icon='FILE_REFRESH')
                row.operator(RIG_OT_RemoveObjectFog.bl_idname)


class RIG_PT_ObjectFogWT(RIG_WT, Panel, ObjectFog):
    pass


class RIG_PT_ObjectFogTB(RIG_TB, Panel, ObjectFog):
    pass


############################################################################
# Clouds
############################################################################

class PhysicalClouds(DrawablePanel):
    bl_label = "Clouds"
    icon_name = 'MOD_FLUID'

    def draw(self, context):
        asettings = context.scene.world.psa_atmosphere_settings
        psa_gsettings = context.scene.world.psa_general_settings
        clouds_type = asettings.clouds_type
        layout = self.layout
        layout.enabled = psa_gsettings.enabled

        row = layout.row(align=True)
        row.prop(asettings, 'clouds_type', expand=True)

        if clouds_type in {'procedural'}:
            col = self.indented_column()
            col.prop(asettings, 'clouds_location', index=2, text="Seed")
            col.prop(asettings, 'clouds_scale')
            col.prop(asettings, 'clouds_thickness')
            col.prop(asettings, 'clouds_detail')
            col.prop(asettings, 'clouds_dimension')
            col.prop(asettings, 'clouds_lacunarity')
            col.label(text='Coverage:')
            col.prop(asettings, 'clouds_min')
            col.prop(asettings, 'clouds_max')
            col.label(text='Lighting:')
            col.prop(asettings, 'clouds_lighting_intensity')
            col.prop(asettings, 'clouds_amount')
            col.prop(asettings, 'clouds_power')
            row = col.row(align=True)
            row.label(text='Inscattering:')
            row.prop(asettings, 'clouds_scattering')
            col.label(text='Location')
            col.prop(asettings, 'clouds_location', index=0, text="X")
            col.prop(asettings, 'clouds_location', index=1, text="Y")
            col.prop(asettings, 'clouds_rotation')
        elif clouds_type in {'texture'}:
            col = self.indented_column()
            col.prop(asettings, 'clouds_texture_type')
            if asettings.clouds_texture_type in {'map'}:
                col.template_ID(asettings, 'clouds_map_texture', new="image.new", open="image.open")
                col.prop(asettings, 'clouds_scale')
            if asettings.clouds_texture_type in {'hdri'}:
                col.template_ID(asettings, 'clouds_hdri_texture', new="image.new", open="image.open")
            col.prop(asettings, 'clouds_thickness')
            col.label(text='Coverage:')
            col.prop(asettings, 'clouds_min')
            col.prop(asettings, 'clouds_max')      
            col.label(text='Lighting:')
            col.prop(asettings, 'clouds_lighting_intensity')
            col.prop(asettings, 'clouds_amount')
            col.prop(asettings, 'clouds_power')
            row = col.row(align=True)
            row.label(text='Inscattering:')
            row.prop(asettings, 'clouds_scattering')
            if asettings.clouds_texture_type in {'map'}:
                col.label(text='Location')
                col.prop(asettings, 'clouds_location', index=0, text="X")
                col.prop(asettings, 'clouds_location', index=1, text="Y")


class RIG_PT_PhysicalCloudsWT(RIG_WT, Panel, PhysicalClouds):
    pass


class RIG_PT_PhysicalCloudsTB(RIG_TB, Panel, PhysicalClouds):
    pass


############################################################################
# Ground
############################################################################
class Ground(DrawablePanel):
    bl_label = "Ground"
    icon_name = "VIEW_PERSPECTIVE"

    def draw(self, context):
        if context.scene and hasattr(context.scene.world, 'psa_general_settings'):
            general_settings = context.scene.world.psa_general_settings
            atmosphere_settings = context.scene.world.psa_atmosphere_settings
            layout = self.layout
            layout.enabled = general_settings.enabled

            col = self.indented_column(False)
            row = col.row(align=True)
            col.prop(atmosphere_settings, 'ground_visible')
            row.label(text='Color:')
            row.prop(atmosphere_settings, 'ground_albedo')
            col.prop(atmosphere_settings, 'ground_offset')
            col.prop(atmosphere_settings, 'horizon_offset')


class RIG_PT_GroundWT(RIG_WT, Panel, Ground):
    pass


class RIG_PT_GroundTB(RIG_TB, Panel, Ground):
    pass


############################################################################
# ArtisticControls
############################################################################
class ArtisticControls(DrawablePanel):
    bl_label = "Artistic Controls"
    icon_name = "SHADERFX"

    def draw(self, context):
        general_settings = context.scene.world.psa_general_settings
        atmosphere_settings = context.scene.world.psa_atmosphere_settings
        layout = self.layout
        layout.enabled = general_settings.enabled

        col = self.indented_column()
        col.prop(atmosphere_settings, 'atmosphere_distance')
        col.prop(atmosphere_settings, 'atmosphere_falloff')
        col.prop(atmosphere_settings, 'sun_radiance_gamma')


class RIG_PT_ArtisticControlsWT(RIG_WT, Panel, ArtisticControls):
    pass


class RIG_PT_ArtisticControlsTB(RIG_TB, Panel, ArtisticControls):
    pass


############################################################################
# Footer
############################################################################
class Footer(DrawablePanel):
    bl_label = "Addon Settings"
    icon_name = "INFO"
    properties_type = "addonsettings"

    def draw(self, context):
        general_settings = context.scene.world.psa_general_settings
        layout = self.layout
        layout.enabled = True

        col = self.indented_column()

        av = current_addon_version()
        av_text = "Addon version: " + str(av[0]) + "." + str(av[1]) + "." + str(av[2])
        col.label(text=av_text)
        vf_text = "API version format: " + str(general_settings.version_format)
        col.label(text=vf_text)


class RIG_PT_FooterWT(RIG_WT, Panel, Footer):
    pass


class RIG_PT_FooterTB(RIG_TB, Panel, Footer):
    pass


############################################################################
# Sub-Footer
############################################################################
class SubFooter(DrawablePanel):
    bl_label = "Extra Settings"
    icon_name = "SETTINGS"
    bl_options = {'HIDE_HEADER'}

    def draw(self, context):
        general_settings = context.scene.world.psa_general_settings
        layout = self.layout
        layout.enabled = True

        if general_settings.enabled:
            layout.operator("psa.remove_atmosphere", icon = "X")


class RIG_PT_SubFooterWT(RIG_WT, Panel, SubFooter):
    bl_options = {'HIDE_HEADER'}


class RIG_PT_SubFooterTB(RIG_TB, Panel, SubFooter):
    bl_options = {'HIDE_HEADER'}


############################################################################
# Object Fog Operators
############################################################################

class RIG_OT_ApplyObjectFog(Operator):
    bl_idname = "rig.apply_fog"
    bl_label = "apply"
    bl_description = "Apply fog to all object materials"
    # properties_type: bpy.props.StringProperty()

    def execute(self, context):
        toggle_fog(1)
        return {'FINISHED'}

class RIG_OT_RemoveObjectFog(Operator):
    bl_idname = "rig.remove_fog"
    bl_label = "clear"
    bl_description = "Remove fog from all object materials"
    # properties_type: bpy.props.StringProperty()

    def execute(self, context):
        toggle_fog(0)
        return {'FINISHED'}
    

############################################################################
# Presets
############################################################################

class PSA_UL_PresetList(UIList):
    """A list class for displaying presets"""

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        custom_icon = 'NONE' #'WORLD_DATA'

        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item, "name", text="", expand=False, emboss=False, icon=custom_icon)

        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon=custom_icon)


class PSA_OT_CreateNewPreset(Operator):
    bl_idname = "psa.create_new_preset"
    bl_label = "Create New"
    bl_description = "Create a New Preset from Current PSA Atmosphere"

    def invoke(self, context, event):
        # Reset preset name to clear so user doesn't have to delete last preset's name
        context.scene.world.psa_exposed.preset_name = ''
        # Create a popup when activated for inputting preset name
        return context.window_manager.invoke_props_dialog(self, width=320)

    def draw(self, context):
        # UI of the popup
        layout = self.layout
        layout.prop(context.scene.world.psa_exposed, "preset_name")

    def execute(self, context):
        world = context.scene.world
        invalid_symbols = validate_preset_name(world.psa_exposed.preset_name)
        if invalid_symbols:
            # Invalid symbol inputted, do not create a preset and report error
            self.report({'ERROR'}, "Couldn't create the preset. %s" % invalid_symbols[0])
            return {'CANCELLED'}
        else:
            # Find the target directory for our presets and save the JSON there
            base_path = os.path.join(bpy.utils.user_resource('DATAFILES'), "presets", "PSA")
            os.makedirs(base_path, exist_ok=True)
            full_path = os.path.join(base_path, world.psa_exposed.preset_name + ".json")
            # Check if a preset of such name already exists and cancel operator to prevent overwrite if it's the case
            if os.path.isfile(full_path):
                self.report({'ERROR'}, "Couldn't create a new preset because a preset with provided name (%s) already exists." % world.psa_exposed.preset_name)
                return {'CANCELLED'}
            else:
                create_preset(context, full_path)
                update_preset_list(self, context)
                # Set the active preset index to the newly created one
                for i in range(len(world.psa_exposed.presets)):
                    if world.psa_exposed.presets[i].name == world.psa_exposed.preset_name:
                        world.psa_exposed.preset_index = i
                        break
                return {'FINISHED'}


class PSA_OT_DeleteCurrentPreset(Operator):
    bl_idname = "psa.delete_current_preset"
    bl_label = "Delete Preset"
    bl_description = "Delete the Selected Preset"

    def invoke(self, context, event):
        # Create a confirmation popup to reduce chance of accidental deletion
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        world = context.scene.world
        # Find the target directory for our presets and delete it
        base_path = os.path.join(bpy.utils.user_resource('DATAFILES'), "presets", "PSA")
        #os.makedirs(base_path, exist_ok=True)
        full_path = os.path.join(base_path, world.psa_exposed.presets[world.psa_exposed.preset_index].name + ".json")
        os.remove(full_path)
        # Set the selected preset to default
        world.psa_exposed.preset_index = -1
        update_preset_list(self, context)
        return {'FINISHED'}
    

class PSA_OT_SaveCurrentPreset(Operator):
    bl_idname = "psa.save_current_preset"
    bl_label = "Save Preset"
    bl_description = "Save the Selected Preset"

    def invoke(self, context, event):
        # Create a confirmation popup to reduce chance of accidental overwrite
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        world = context.scene.world
        # Find the target directory for our presets and save the JSON there
        base_path = os.path.join(bpy.utils.user_resource('DATAFILES'), "presets", "PSA")
        full_path = os.path.join(base_path, world.psa_exposed.presets[world.psa_exposed.preset_index].name + ".json")
        create_preset(context, full_path)
        update_preset_list(self, context)
        return {'FINISHED'}


class PSA_OT_OpenPresetsFolder(Operator):
    bl_idname = "psa.open_presets_folder"
    bl_label = "Open Presets Folder"
    bl_description = "Open the preset folder in file manager"

    def execute(self, context):
        file_path = os.path.join(bpy.utils.user_resource('DATAFILES'), "presets", "PSA")
        if sys.platform == "win32":
            os.startfile(file_path)
        else:
            opener = "open" if sys.platform == "darwin" else "xdg-open"
            subprocess.call([opener, file_path])
        return {'FINISHED'}
    

class PSA_OT_AddAtmosphere(Operator):
    bl_idname = "psa.add_atmosphere"
    bl_label = "Add Atmosphere"
    bl_description = "Add PSA atmosphere to the current world"

    def execute(self, context):
        context.scene.world.psa_general_settings.enabled = True

        # Open presets by default
        context.scene.world.psa_exposed.show_presets = True

        return {'FINISHED'}


class PSA_OT_RemoveAtmosphere(Operator):
    bl_idname = "psa.remove_atmosphere"
    bl_label = "Remove Atmosphere"
    bl_description = "Remove PSA atmosphere from the current world"

    def execute(self, context):
        context.scene.world.psa_general_settings.enabled = False

        return {'FINISHED'}
