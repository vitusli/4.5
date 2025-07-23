
################################################################################################
# ooooooooooooo                           .                                       oooooooooo.                 .            
# 8'   888   `8                         .o8                                       `888'   `Y8b              .o8            
#      888       .ooooo.  oooo    ooo .o888oo oooo  oooo  oooo d8b  .ooooo.        888      888  .oooo.   .o888oo  .oooo.  
#      888      d88' `88b  `88b..8P'    888   `888  `888  `888""8P d88' `88b       888      888 `P  )88b    888   `P  )88b 
#      888      888ooo888    Y888'      888    888   888   888     888ooo888       888      888  .oP"888    888    .oP"888 
#      888      888    .o  .o8"'88b     888 .  888   888   888     888    .o       888     d88' d8(  888    888 . d8(  888 
#     o888o     `Y8bod8P' o88'   888o   "888"  `V88V"V8P' d888b    `Y8bod8P'      o888bood8P'   `Y888""8o   "888" `Y888""8o
################################################################################################


import bpy

import random
import os 

from .. translations import translate
from .. resources.icons import cust_icon
from .. resources import directories

from .. utils.extra_utils import dprint
from .. utils.path_utils import get_subpaths
from .. utils.import_utils import serialization , import_image, import_and_add_geonode
from .. utils.str_utils import is_attr_surfs_shared

from .. widgets.infobox import SC5InfoBox, generic_infobox_setup

# ooooooooo.                                                        .    o8o
# `888   `Y88.                                                    .o8    `"'
#  888   .d88' oooo d8b  .ooooo.  oo.ooooo.   .ooooo.  oooo d8b .o888oo oooo   .ooooo.   .oooo.o
#  888ooo88P'  `888""8P d88' `88b  888' `88b d88' `88b `888""8P   888   `888  d88' `88b d88(  "8
#  888          888     888   888  888   888 888ooo888  888       888    888  888ooo888 `"Y88b.
#  888          888     888   888  888   888 888    .o  888       888 .  888  888    .o o.  )88b
# o888o        d888b    `Y8bod8P'  888bod8P' `Y8bod8P' d888b      "888" o888o `Y8bod8P' 8""888P'
#                                  888
#                                 o888o


def user_name_upd(self,context):
    ng = self.id_data
        
    #same ?
    if (self.user_name==ng.name.replace(".TEXTURE ","")):
        return None
    
    #else change both names  
    i=0
    search_name = f".TEXTURE {self.user_name}"
    while (search_name in bpy.data.node_groups):
        search_name = f".TEXTURE {self.user_name}.{i:03}"
        i+=1

    self.is_default = (search_name==".TEXTURE *DEFAULT* MKV")

    #update nodegroup name with search
    ng.name = search_name
    self.user_name = search_name.replace(".TEXTURE ","") #only "same ?" check above will save us from feedback loop

    #ensure ptr names?    
    ensure_texture_ptr_name()
    
    return None

def ensure_texture_ptr_name():
    """systems[].texture_ptr values aren't reliable, and this can cause problems if wanting the refresh their values,
    use this function to ensure their name are equivalent to the current nodetree used.. Later on, would be nice to find a proper solution for texture_ptr"""
    
    #get all psy or group systems
    all_systems = { itm.get_interface_item_source() for e in bpy.context.scene.scatter5.get_all_emitters(search_mode="all") for itm in e.scatter5.particle_interface_items }
    
    for sys in all_systems:
        
        #if psy, get psy scatter engine ng, and the properties we are after
        if (sys.system_type=='SCATTER_SYSTEM'):
            
            mod = sys.get_scatter_mod(strict=False, raise_exception=False,)
            
            if (mod is None):
                print("REPORT: ensure_texture_ptr_name(): Skipping.. Couldn't find scatter-engine modifier ", sys.name)
                continue
            if (mod.node_group is None):
                print("REPORT: ensure_texture_ptr_name(): Skipping.. Couldn't find scatter-engine node ", sys.name)
                continue
            
            propgroup = ( ("s_rot_align_y_texture_ptr","s_rot_align_y"),
                          ("s_rot_tilt_texture_ptr","s_rot_tilt"),
                          ("s_pattern1_texture_ptr","s_pattern1"),
                          ("s_pattern2_texture_ptr","s_pattern2"),
                          ("s_pattern3_texture_ptr","s_pattern3"),
                          ("s_instances_texture_ptr","s_instances_pick_color_textures"), )

        #or in group..
        elif (sys.system_type=='GROUP_SYSTEM'):
            
            members = sys.get_psy_members()
            if (not len(members)):
                continue
            
            mod = members[0].get_scatter_mod(strict=False, raise_exception=False,)
            if (mod is None):
                print("REPORT: ensure_texture_ptr_name(): Skipping.. Couldn't find scatter-engine modifier ", sys.name)
                continue
            if (mod.node_group is None):
                print("REPORT: ensure_texture_ptr_name(): Skipping.. Couldn't find scatter-engine node ", sys.name)
                continue
            
            propgroup =  ( ("s_gr_pattern1_texture_ptr","s_gr_pattern1"), )
            
        #get the values of the true name and update the texture_ptr
        for ptrname,ngname in propgroup:
            
            if (mod is None):
                print(f"REPORT: ensure_texture_ptr_name(): Skipping.. Couldn't find scatter-engine modifier ", sys.name)
                continue
            if (mod.node_group is None):
                print("REPORT: ensure_texture_ptr_name(): Skipping.. Couldn't find scatter-engine node ", sys.name)
                continue
            
            #get the first level node
            baseng = mod.node_group.nodes.get(ngname)
            if (baseng is None):
                print(f"ERROR:  ensure_texture_ptr_name(): Couldn't find '{ngname}' in scatter-engine for scatter5.systems['{sys.name}'].{ptrname}")
                continue
            
            #get the texture node
            tx = baseng.node_tree.nodes.get("texture")
            if (tx is None):
                print(f"ERROR:  ensure_texture_ptr_name(): Couldn't find scatter5.systems['{sys.name}'].{ptrname}.texture")
                continue
            
            #if no ng assigned, fine, we assign default one (shouldn't happen)
            nt = tx.node_tree
            if (nt is None):
                print(f"ERROR:  ensure_texture_ptr_name(): scatter5.systems['{sys.name}'].{ptrname}.texture.node_tree is None")
                continue
            
            #finally found the correct name..
            correct_name = nt.name
            
            #finally, we update the texture pointer with correct name, we temporarily disable our properties updates
            with bpy.context.scene.scatter5.factory_update_pause(factory=True):
                setattr(sys,ptrname,correct_name)
            
        continue

    return None

def is_default_upd(self,context):
    ng = self.id_data
    ng.nodes["is_default"].boolean = self.is_default

def texture_type_upd(self,context):
    ng = self.id_data
    ng.links.new(ng.nodes[self.texture_type].outputs[0],ng.nodes["texture_type"].inputs[0])

def scale_upd(self,context):
    ng = self.id_data
    ng.nodes["scale"].outputs[0].default_value = self.scale
    
def distorsion_upd(self,context):
    ng = self.id_data
    ng.nodes["distorsion"].outputs[0].default_value = self.distorsion

def detail_upd(self,context):
    ng = self.id_data
    ng.nodes["detail"].outputs[0].default_value = self.detail

def out_type_upd(self,context):
    ng = self.id_data
    ng.nodes["out_type_color"].boolean = self.out_type == "Color"

def brick_offset_upd(self,context):
    ng = self.id_data
    node = ng.nodes["brick_node"]
    node.offset = self.brick_offset

def brick_offset_frequency_upd(self,context):
    ng = self.id_data
    node = ng.nodes["brick_node"]
    node.offset_frequency = self.brick_offset_frequency

def brick_squash_upd(self,context):
    ng = self.id_data
    node = ng.nodes["brick_node"]
    node.squash = self.brick_squash

def brick_squash_frequency_upd(self,context):
    ng = self.id_data
    node = ng.nodes["brick_node"]
    node.squash_frequency = self.brick_squash_frequency

def brick_mortar_size_upd(self, context):
    ng = self.id_data
    node = ng.nodes["brick_node"]
    node.inputs[5].default_value = self.brick_mortar_size

def brick_mortar_smooth_upd(self, context):
    ng = self.id_data
    node = ng.nodes["brick_node"]
    node.inputs[6].default_value = self.brick_mortar_smooth

def brick_bias_upd(self,context):
    ng = self.id_data
    node = ng.nodes["brick_node"]
    node.inputs[7].default_value = self.brick_bias

def brick_width_upd(self,context):
    ng = self.id_data
    node = ng.nodes["brick_node"]
    node.inputs[8].default_value = self.brick_width

def brick_row_height_upd(self,context):
    ng = self.id_data
    node = ng.nodes["brick_node"]
    node.inputs[9].default_value = self.brick_row_height

def image_interpolation_upd(self, context):
    ng = self.id_data
    node = ng.nodes["image_node"]
    node.interpolation = self.image_interpolation

def image_extension_upd(self, context):
    ng = self.id_data
    node = ng.nodes["image_node"]
    node.extension = self.image_extension

def image_ptr_upd(self, context):
    ng = self.id_data
    node = ng.nodes["image_node"]
    node.inputs[0].default_value = self.image_ptr

def image_frame_upd(self, context):
    ng = self.id_data
    node = ng.nodes["image_node"]
    node.inputs[2].default_value = self.image_frame

def magic_turbulence_depth_upd(self,context):
    ng = self.id_data
    node = ng.nodes["magic_node"]
    node.turbulence_depth = self.magic_turbulence_depth

def musgrave_musgrave_type_upd(self,context):
    ng = self.id_data
    node = ng.nodes["musgrave_node"]
    node.noise_type = self.musgrave_musgrave_type

def musgrave_offset_upd(self,context):
    ng = self.id_data
    node = ng.nodes["musgrave_node"]
    node.inputs[6].default_value = self.musgrave_offset

def noise_roughness_upd(self,context):
    ng = self.id_data
    node = ng.nodes["noise_node"]
    node.inputs[4].default_value = self.noise_roughness

def voronoi_feature_upd(self,context):
    ng = self.id_data
    node = ng.nodes["voronoi_node"]
    node.feature = self.voronoi_feature

def voronoi_distance_upd(self,context):
    ng = self.id_data
    node = ng.nodes["voronoi_node"]
    node.distance = self.voronoi_distance

def voronoi_exponent_upd(self,context):
    ng = self.id_data
    node = ng.nodes["voronoi_node"]
    node.inputs[4].default_value = self.voronoi_exponent

def voronoi_randomness_upd(self,context):
    ng = self.id_data
    node = ng.nodes["voronoi_node"]
    node.inputs[5].default_value = self.voronoi_randomness

def wave_wave_type_upd(self, context):
    ng = self.id_data
    node = ng.nodes["wave_node"]
    node.wave_type = self.wave_wave_type

def wave_bands_direction_upd(self, context):
    ng = self.id_data
    node = ng.nodes["wave_node"]
    node.bands_direction = self.wave_bands_direction

def wave_wave_profile_upd(self, context):
    ng = self.id_data
    node = ng.nodes["wave_node"]
    node.wave_profile = self.wave_wave_profile

def wave_detail_scale_upd(self, context):
    ng = self.id_data
    node = ng.nodes["wave_node"]
    node.inputs[4].default_value = self.wave_detail_scale

def wave_detail_roughness_upd(self, context):
    ng = self.id_data
    node = ng.nodes["wave_node"]
    node.inputs[5].default_value = self.wave_detail_roughness

def wave_phase_offset_upd(self, context):
    ng = self.id_data
    node = ng.nodes["wave_node"]
    node.inputs[6].default_value = self.wave_phase_offset

def intensity_upd(self,context):
    ng = self.id_data
    ng.nodes["intensity"].outputs[0].default_value = self.intensity

def contrast_upd(self,context):
    ng = self.id_data
    ng.nodes["contrast"].outputs[0].default_value = self.contrast

def saturation_upd(self,context):
    ng = self.id_data
    ng.nodes["saturation"].outputs[0].default_value = self.saturation

def jitter_upd(self,context):
    ng = self.id_data
    ng.nodes["jitter"].outputs[0].default_value = self.jitter

def use_color_ramp_upd(self,context):
    ng = self.id_data
    ng.nodes["use_color_ramp"].boolean = self.use_color_ramp

def mapping_projection_upd(self,context):
    ng = self.id_data
    index = self.bl_rna.properties["mapping_projection"].enum_items[self.mapping_projection].value
    ng.nodes["mapping_projection"].integer = index 

def mapping_uv_ptr_upd(self,context):
    ng = self.id_data
    ng.nodes["mapping_uv_ptr"].inputs[0].default_value = self.mapping_uv_ptr

def mapping_obj_ptr_upd(self,context):
    ng = self.id_data
    ng.nodes["mapping_obj_ptr"].inputs[0].default_value = self.mapping_obj_ptr

def mapping_location_upd(self,context):
    ng = self.id_data
    ng.nodes["mapping_location"].vector = self.mapping_location

def mapping_rotation_upd(self,context):
    ng = self.id_data
    ng.nodes["mapping_rotation"].vector = self.mapping_rotation

def mapping_scale_upd(self,context):
    ng = self.id_data
    ng.nodes["mapping_scale"].vector = self.mapping_scale

def mapping_random_allow_upd(self, context):
    ng = self.id_data
    ng.nodes["mapping_random_allow"].boolean = self.mapping_random_allow

def mapping_random_seed_upd(self, context):
    ng = self.id_data
    ng.nodes["mapping_random_seed"].integer = self.mapping_random_seed

def mapping_random_is_random_seed_upd(self, context):    
    if (self.mapping_random_is_random_seed==True):
        self.mapping_random_is_random_seed = False
        self.mapping_random_seed = random.randint(0,9999)

def mapping_random_loc_upd(self,context):
    """special creatiion options for presets, quite legacy, now we have mapping seed embedded settings"""
    if ((self.mapping_random_loc==True) and (self.mapping_random_loc_used==False)):
        self.mapping_random_loc = False
        self.mapping_random_loc_used = True 
        self.mapping_location = [random.uniform(0,999), random.uniform(0,999) , random.uniform(0,999) ]


class SCATTER5_PR_node_texture(bpy.types.PropertyGroup):
    """bpy.data.node_groups[i].scatter5.texture"""

    user_name : bpy.props.StringProperty(
        default="*DEFAULT* MKV",
        update=user_name_upd,
        )

    def get_system_users(self, dupplis=False):
        """collect all scatter-systems/group-systems user of this texture data"""

        #get all psy or group systems
        all_systems = { itm.get_interface_item_source() for e in bpy.context.scene.scatter5.get_all_emitters(search_mode="all") for itm in e.scatter5.particle_interface_items }

        #filter psys depending if they got a texture pointer assigned to this self texture
        users = []
        for sys in all_systems:
            for k in sys.bl_rna.properties.keys():
                if (k.endswith("texture_ptr")):
                    value = getattr(sys,k)
                    if ((value!="") and (value.endswith(self.user_name))):
                        users.append(sys)
                continue
        
        #if not dupplis
        if (not dupplis):
            users = {u for u in users}
        
        return users
                        
    is_default : bpy.props.BoolProperty(
        default=True,
        update=is_default_upd,
        )

    texture_type : bpy.props.EnumProperty(
        name=translate("Texture Type"),
        description=translate("Choose your procedural texture type. Most textures, except the image texture type, are all procedural"),
        default="musgrave_",
        items=(
            ("musgrave_",translate("Musgrave"),"","TOPATCH:W_TEXTMUSGRAVE",4),
            ("voronoi_",translate("Voronoi"),"","TOPATCH:W_TEXTVORONOI",6),
            ("noise_",translate("Noise"),"","TOPATCH:W_TEXTNOISE",5),
            ("white_noise_",translate("White Noise"),"","TOPATCH:W_TEXTWHITENOISE",8),
            ("wave_",translate("Wave"),"","TOPATCH:W_TEXTWAVES",7),
            ("magic_",translate("Magic"),"","TOPATCH:W_TEXTMAGIC",3),
            ("checker_",translate("Checker"),"","TOPATCH:W_TEXTCHECKER",1),
            ("brick_",translate("Brick"),"","TOPATCH:W_TEXTBRICK",0),
            ("image_",translate("Image"),"","TOPATCH:W_TEXTIMG",2),
            ),
        update=texture_type_upd,
        )

    #texture settings 

    #general
    scale : bpy.props.FloatProperty(
        name=translate("Scale"),
        description=translate("The scale of a procedural texture.\n• A value of '0.01' will creates a large noise pattern.\n• A value of '10.0' will create a small pattern"),
        default=1,
        update=scale_upd,
        )
    detail : bpy.props.FloatProperty(
        name=translate("Detail"),
        default=1,
        min=0,
        max=15,
        update=detail_upd,
        )
    distorsion : bpy.props.FloatProperty(
        name=translate("Distortion"),
        default=0,
        update=distorsion_upd,
        )
    out_type : bpy.props.EnumProperty(
        name=translate("Output"),
        description=translate("Choose if your procedural texture shall produce black and white or color values"),
        default="Greyscale",
        items=[("Greyscale",translate("Greyscale"),"","",0),("Color",translate("Colored"),"","",1),],
        update=out_type_upd,
        )
    #brick 
    brick_offset : bpy.props.FloatProperty(
        name=translate("Offset"),
        default=0.5, 
        min=0,
        max=1,
        update=brick_offset_upd,
        )
    brick_offset_frequency : bpy.props.IntProperty(
        name=translate("Offset Frequency"),
        default=2,
        min=1,
        max=99,
        update=brick_offset_frequency_upd,
        )
    brick_squash : bpy.props.FloatProperty(
        name=translate("Squash"),
        default=1, 
        min=0,
        max=99, 
        update=brick_squash_upd,
        )
    brick_squash_frequency : bpy.props.IntProperty(
        name=translate("Squash Frequency"),
        default=2,
        min=1,
        max=99, 
        update=brick_squash_frequency_upd,
        )
    brick_mortar_size : bpy.props.FloatProperty(
        name=translate("Mortar Size"),
        default=0.02, 
        soft_min=0,
        soft_max=0.125, 
        update=brick_mortar_size_upd,
        )
    brick_mortar_smooth : bpy.props.FloatProperty(
        name=translate("Mortar Smooth"),
        default=0.1, 
        soft_min=0,
        soft_max=0.125,
        update=brick_mortar_smooth_upd,
        )
    brick_bias : bpy.props.FloatProperty(
        name=translate("Bias"),
        default=0, 
        soft_min=-1,
        soft_max=1, 
        update=brick_bias_upd,
        )
    brick_width : bpy.props.FloatProperty(
        name=translate("Width"),
        default=0.5,
        soft_min=0.01,
        soft_max=100,
        update=brick_width_upd,
        )
    brick_row_height : bpy.props.FloatProperty(
        name=translate("Row Height"),
        default=0.25,
        soft_min=0.01,
        soft_max=100,
        update=brick_row_height_upd,
        )
    #image texture
    image_interpolation : bpy.props.EnumProperty(
        name=translate("Interpolation"),
        description=translate("Change how the pixel of the image interpolates"),
        default="Linear",
        items=[("Linear",translate("Linear"),""),("Closest",translate("Closest"),""),("Cubic",translate("Cubic"),"")], 
        update=image_interpolation_upd,
        )
    image_extension : bpy.props.EnumProperty(
        name=translate("Extension"),
        description=translate("Control how the image texture appear beyond its bounds"),
        default="REPEAT",
        items=[("REPEAT",translate("Repeat"),""),("EXTEND",translate("Extend"),""),("CLIP",translate("Clip"),""),], 
        update=image_extension_upd,
        )
    image_ptr : bpy.props.PointerProperty(
        type=bpy.types.Image, 
        update=image_ptr_upd,
        )
    image_frame : bpy.props.IntProperty(
        name=translate("Frame"),
        default=0,
        update=image_frame_upd,
        )
    #magic
    magic_turbulence_depth : bpy.props.IntProperty(
        name=translate("Depth"),
        default=0, 
        soft_min=0,
        soft_max=10, 
        update=magic_turbulence_depth_upd,
        )
    #musgrave
    musgrave_musgrave_type : bpy.props.EnumProperty(
        name=translate("Type"),
        default="HYBRID_MULTIFRACTAL", 
        items=[("MULTIFRACTAL","Multifractal",""),("RIDGED_MULTIFRACTAL","Ridged Multifractal",""),("HYBRID_MULTIFRACTAL","Hybrid Multifractal",""),("FBM","Fbm",""),("HETERO_TERRAIN","Hetero Terrain",""),], 
        update=musgrave_musgrave_type_upd,
        )
    musgrave_offset : bpy.props.FloatProperty(
        name=translate("Offset"),
        default=0.2, 
        update=musgrave_offset_upd,
        )
    #noise
    noise_roughness : bpy.props.FloatProperty(
        name=translate("Roughness"),
        default=0, 
        soft_min=0,
        soft_max=1, 
        update=noise_roughness_upd,
        )
    #voronoi
    voronoi_feature : bpy.props.EnumProperty(
        name=translate("Feature"),
        default="F1", 
        items=[("F1","F1",""),("F2","F2",""),], 
        update=voronoi_feature_upd,
        )
    voronoi_distance : bpy.props.EnumProperty(
        name=translate("Distance"),
        default="EUCLIDEAN",
        items=[("EUCLIDEAN","Euclidean",""),("MANHATTAN","Manhattan",""),("CHEBYCHEV","Chebychev",""),("MINKOWSKI","Minkowski",""),], 
        update=voronoi_distance_upd,
        )
    voronoi_exponent : bpy.props.FloatProperty(
        name=translate("Exponent"),
        default=0, 
        soft_min=0,
        soft_max=32,
        update=voronoi_exponent_upd,
        )
    voronoi_randomness : bpy.props.FloatProperty(
        name=translate("Randomness"),
        default=1,
        soft_min=0,
        soft_max=1, 
        update=voronoi_randomness_upd,
        )
    #wave
    wave_wave_type : bpy.props.EnumProperty(
        name=translate("Type"),
        default="BANDS", 
        items=[("BANDS","Bands",""),("RINGS","Rings",""),], 
        update=wave_wave_type_upd,
        )
    wave_bands_direction : bpy.props.EnumProperty(
        name=translate("Bands Direction"),
        default="X", 
        items=[("X","X",""),("Y","Y",""),("Z","Z",""),("DIAGONAL","Diagonal",""),], 
        update=wave_bands_direction_upd,
        )
    wave_wave_profile : bpy.props.EnumProperty(
        name=translate("Wave Profile"),
        default="SIN", 
        items=[("SIN","Sine",""),("SAW","Saw",""),("TRI","Triangle",""),], 
        update=wave_wave_profile_upd,
        )
    wave_detail_scale : bpy.props.FloatProperty(
        name=translate("Detail Scale"),
        default=0, 
        update=wave_detail_scale_upd,
        )
    wave_detail_roughness : bpy.props.FloatProperty(
        name=translate("Detail Roughness"),
         default=0, 
         soft_min=0,
         soft_max=1, 
         update=wave_detail_roughness_upd,
         )
    wave_phase_offset : bpy.props.FloatProperty(
        name=translate("Phase Offset"),
        default=0, 
        update=wave_phase_offset_upd,
        )

    #color adjustments 

    intensity : bpy.props.FloatProperty(
        name=translate("Brightness"),
        default=1,
        min=0,
        soft_max=2,
        update=intensity_upd,
        )
    contrast : bpy.props.FloatProperty(
        name=translate("Contrast"),
        default=1,
        min=0,
        soft_max=5,
        update=contrast_upd,
        )
    saturation : bpy.props.FloatProperty(
        name=translate("Saturation"),
        default=1,
        min=0,
        max=2,
        update=saturation_upd,
        )
    jitter : bpy.props.FloatProperty(
        name=translate("Jitter"),
        description=translate("Randomize the position of the pixels around, creating a pixelated blur effect"),
        default=0,
        min=0,
        max=3,
        update=jitter_upd,
        )

    #color ramp

    use_color_ramp : bpy.props.BoolProperty(
        name=translate("Use Color-Ramp"),
        default=False,
        update=use_color_ramp_upd,
        )
    def get_color_ramp(self):
        return self.id_data.nodes["ColorRamp"].color_ramp

    #mapping 

    mapping_projection : bpy.props.EnumProperty(
        name=translate("Projection Space"),
        description=translate("Define how this texture will be applied on your scatter"),
        default="local", 
        items=(("local", translate("Local"), translate("Uses the surface object's local coordinates for texture mapping, meaning the texture will move with the object's transforms"), "ORIENTATION_LOCAL", 0),
               ("global", translate("Global"), translate("Uses world coordinates, so the textures stay fixed in space, unaffected by your surface's object transforms"), "WORLD", 1),
               ("uv", translate("UV"), translate("Uses the coordinates of the given UV map of your surface objects to map the texture.\nMake sure that the UV attribute exists on all your surfaces"), "UV", 2),
               ("object", translate("Object"), translate("Project the texture based on the transformation matrix of a chosen object, the texture will move alongside the transforms of the chosen object"), "EYEDROPPER", 3),
              ),
        update=mapping_projection_upd,
        )
    mapping_uv_ptr : bpy.props.StringProperty(
        name=translate("UV-Map Pointer"),
        default="",
        update=mapping_uv_ptr_upd,
        )
    mapping_obj_ptr : bpy.props.PointerProperty(
        type=bpy.types.Object,
        update=mapping_obj_ptr_upd,
        )
    mapping_location : bpy.props.FloatVectorProperty(
        description=translate("Transform Location.\nMove your texture coordinates"),
        default=(0,0,0),
        update=mapping_location_upd,
        )
    mapping_rotation : bpy.props.FloatVectorProperty(
        description=translate("Transform Rotation.\nRotate your texture coordinates around its origin point (affected by the rotation)"),
        default=(0,0,0),
        subtype="EULER",
        update=mapping_rotation_upd,
        )
    mapping_scale : bpy.props.FloatVectorProperty(
        description=translate("Transform Scale.\nRescale your texture coordinates around its origin point (affected by the rotation)"),
        default=(1,1,1),
        update=mapping_scale_upd,
        ) 
    mapping_random_allow : bpy.props.BoolProperty(
        name=translate("Randomize Transforms"),
        description=translate("Randomly move and rotate the coordinates of your texture"),
        default=False,
        update=mapping_random_allow_upd,
        )
    mapping_random_seed : bpy.props.IntProperty(
        name=translate("Seed"),
        description=translate("Change this value to randomize the result.\n\nIn 3D graphics, a seed is a starting value used by a random number generator to produce a sequence of random-looking numbers. These numbers can control things like the position, rotation, or scale of objects in a scene. Using the same seed will always generate the same 'random' result, which helps keep things consistent when needed."),
        default=0, 
        update=mapping_random_seed_upd,
        )
    mapping_random_is_random_seed : bpy.props.BoolProperty( #= value of the property is of no importance, only the update signal matter
        name=translate("Randomize Seed"),
        description=translate("Randomize the value of the hereby seed property"),
        default=False,
        update=mapping_random_is_random_seed_upd,
        )

    mapping_random_loc : bpy.props.BoolProperty( #internal
        name="Internal Property: Random Location, property designed for presets",
        default=False,
        update=mapping_random_loc_upd,
        )
    mapping_random_loc_used : bpy.props.BoolProperty( #internal
        name="Internal Property: Should only apply random loc once",
        default=False,
        )

    # 88""Yb 88""Yb 888888 .dP"Y8 888888 888888 888888 88 88b 88  dP""b8
    # 88__dP 88__dP 88__   `Ybo." 88__     88     88   88 88Yb88 dP   `"
    # 88"""  88"Yb  88""   o.`Y8b 88""     88     88   88 88 Y88 Yb  "88
    # 88     88  Yb 888888 8bodP' 888888   88     88   88 88  Y8  YboodP


    def get_texture_dict(self, texture_random_loc=False,):
        """return a settings dict from a scatter texture nodegroup"""

        d = {}

        #Noise settings 

        d["texture_type"] = self.texture_type
        d["scale"] = self.scale
        d["detail"] = self.detail
        d["distorsion"] = self.distorsion
        d["out_type"] = self.out_type

        match d["texture_type"]:
        
            case 'brick_':
                d["brick_offset"] = self.brick_offset
                d["brick_offset_frequency"] = self.brick_offset_frequency
                d["brick_squash"] = self.brick_squash
                d["brick_squash_frequency"] = self.brick_squash_frequency
                d["brick_mortar_size"] = self.brick_mortar_size
                d["brick_mortar_smooth"] = self.brick_mortar_smooth
                d["brick_bias"] = self.brick_bias
                d["brick_width"] = self.brick_width
                d["brick_row_height"] = self.brick_row_height

            case 'image_':
                d["image_interpolation"] = self.image_interpolation
                d["image_extension"] = self.image_extension
                if (self.image_ptr is not None):
                    d["image_name"] = self.image_ptr.name #Special
                    d["image_path"] = self.image_ptr.filepath.split("\\")[-1] #Special

            case 'magic_':
                d["magic_turbulence_depth"] = self.magic_turbulence_depth

            case 'musgrave_':
                d["musgrave_musgrave_type"] = self.musgrave_musgrave_type
                d["musgrave_offset"] = self.musgrave_offset

            case 'noise_':
                d["noise_roughness"] = self.noise_roughness

            case 'voronoi_':
                d["voronoi_feature"] = self.voronoi_feature
                d["voronoi_distance"] = self.voronoi_distance
                d["voronoi_exponent"] = self.voronoi_exponent
                d["voronoi_randomness"] = self.voronoi_randomness

            case 'wave_':
                d["wave_wave_type"] = self.wave_wave_type
                d["wave_bands_direction"] = self.wave_bands_direction
                d["wave_wave_profile"] = self.wave_wave_profile
                d["wave_detail_scale"] = self.wave_detail_scale
                d["wave_detail_roughness"] = self.wave_detail_roughness
                d["wave_phase_offset"] = self.wave_phase_offset

        #Color adjustments

        if (self.intensity!=1):
            d["intensity"] = self.intensity
        if (self.contrast!=1):
            d["contrast"] = self.contrast
        if (self.saturation!=1):
            d["saturation"] = self.saturation
        if (self.jitter!=0):
            d["jitter"] = self.jitter

        #Color ramp 

        d["use_color_ramp"] = self.use_color_ramp
        if (d["use_color_ramp"]==True):
            color_ramp =  self.get_color_ramp()
            d["color_ramp_interpolation"] = color_ramp.interpolation #Special
            d["color_ramp_elements"] = [(e.position, list(e.color)) for e in color_ramp.elements] #Special

        #Projection 

        d["mapping_projection"] = self.mapping_projection
        match self.mapping_projection:
            case 'uv':
                d["mapping_uv_ptr"] = self.mapping_uv_ptr
            case 'object':
                d["mapping_obj_ptr"] = self.mapping_obj_ptr.name if (self.mapping_obj_ptr is not None) else ""

        d["mapping_location"] = self.mapping_location[:]
        d["mapping_rotation"] = self.mapping_rotation[:]
        d["mapping_scale"] = self.mapping_scale[:]

        d["mapping_random_allow"] = self.mapping_random_allow
        d["mapping_random_seed"] = self.mapping_random_seed

        d["mapping_random_loc"] = texture_random_loc

        return d 

    def apply_texture_dict(self, d, img_directory=directories.lib_library,):
        """apply settings to a scatter texture nodegroup"""

        #procedurally apply settings 
        for k,v in d.items():
            if (k in self.bl_rna.properties.keys()):
                if (k=="mapping_obj_ptr"):
                    continue
                setattr(self,k,v)

        #special need, because object ptr is stored as name
        if ("mapping_obj_ptr" in d):
            self.mapping_obj_ptr = bpy.data.objects.get(d["mapping_obj_ptr"])

        #Image Special 
        if ("image_name" in d):

            img = bpy.data.images.get(d["image_name"])
            if (img is None):
                #try to find this img in user scatter library
                if ((img_directory!="") and os.path.exists(img_directory)):
                    for p in get_subpaths(img_directory):
                        img_name = d["image_path"] if ("\\" not in d["image_path"]) else d["image_path"].split("\\")[-1]
                        if (p.endswith(img_name)):
                            img = import_image(p)
                            break
                        continue

            self.image_ptr = img

        #ColorRamp Special
        if (d["use_color_ramp"]==True):

            color_ramp = self.get_color_ramp()
            color_ramp.interpolation = d["color_ramp_interpolation"]
            
            #clear all elements, it seems that api of color_ramp is a bit unstable
            for e in color_ramp.elements:
                try: color_ramp.elements.remove(e)
                except: pass

            #get colorramp element from dict &  sort from position, needed as sadly `color_ramp.elements.update()` do not work
            color_ramp_elements = d["color_ramp_elements"]
            color_ramp_elements = sorted(color_ramp_elements, key=lambda x:x[0])

            #change elements value 
            for i, (pos,col) in enumerate(color_ramp_elements):
                if (i > (len(color_ramp.elements)-1)):
                    e = color_ramp.elements.new(pos)
                    e.color = col
                else:
                    color_ramp.elements[i].color = col
                    color_ramp.elements[i].position = pos

        return None

    def apply_legacy_texture_dict(self, old, img_directory=directories.lib_library,):
        """partially convert legacy texture data information to new texture, scatter5 beta"""

        d = {}

        if ("type" in old):
            
            match old["type"]:
                
                case 'IMAGE':
                    d["texture_type"]="image_"
                    d["img_name"] = old["s_img_name"]
                    d["img_path"] = old["s_img_path"]

                case 'MAGIC':
                    d["texture_type"]="magic_"

                case 'VORONOI':
                    d["texture_type"]="voronoi_"

                case 'CLOUDS':
                    d["texture_type"]="noise_"
                    d["noise_roughness"]=1
                
                case 'MARBLE':
                    d["texture_type"]="wave_"
                    d["wave_bands_direction"] = 'DIAGONAL'
                    d["wave_detail_scale"] = 1
                    d["wave_detail_roughness"] = 1
                    d["distorsion"] = 10
                    d["detail"] = 3

                case 'STUCCI':
                    d["texture_type"] = 'musgrave_'
                    d["musgrave_musgrave_type"] = 'MULTIFRACTAL'

                case 'DISTORTED_NOISE':
                    d["texture_type"]="musgrave_"

                case 'WOOD':
                    d["texture_type"]="wave_"

        if ("scale" in old):
            d["scale"] = old["distorsion"]
        if ("distorsion" in old):
            d["distorsion"] = old["distorsion"]

        if ("intensity" in old):
            d["intensity"] = old["intensity"]
        if ("contrast" in old):
            d["contrast"] = old["contrast"]
        if ("saturation" in old):
            d["saturation"] = old["saturation"]
            
        if ("use_color_ramp" in old):
            d["use_color_ramp"] = old["use_color_ramp"]
        if ("s_colorramp_interpolation" in old):
            d["color_ramp_interpolation"] = old["s_colorramp_interpolation"]
        if ("s_colorramp_elements" in old):
            d["color_ramp_elements"] = old["s_colorramp_elements"]

        if ("s_texture_projection" in old):
            d["mapping_projection"] = "local" if (old["s_texture_projection"]=="s_point_position") else "uv"
        if ("s_texture_uv_ptr" in old):
            d["mapping_uv_ptr"] = old["s_texture_uv_ptr"]
        if ("s_texture_location" in old):
            d["mapping_location"] = old["s_texture_location"]
        if ("s_texture_rotation" in old):
            d["mapping_rotation"] = old["s_texture_rotation"]
        if ("s_texture_scale" in old):
            d["mapping_scale"] = old["s_texture_scale"]
        if ("s_texture_random_loc" in old):
            d["mapping_random_loc"] = old["s_texture_random_loc"]

        self.apply_texture_dict(d, img_directory=img_directory,)

        return None


#   .oooooo.                                               .
#  d8P'  `Y8b                                            .o8
# 888      888 oo.ooooo.   .ooooo.  oooo d8b  .oooo.   .o888oo  .ooooo.  oooo d8b
# 888      888  888' `88b d88' `88b `888""8P `P  )88b    888   d88' `88b `888""8P
# 888      888  888   888 888ooo888  888      .oP"888    888   888   888  888
# `88b    d88'  888   888 888    .o  888     d8(  888    888 . 888   888  888
#  `Y8bood8P'   888bod8P' `Y8bod8P' d888b    `Y888""8o   "888" `Y8bod8P' d888b
#               888
#              o888o


class SCATTER5_OT_scatter_texture_new(bpy.types.Operator):

    bl_idname      = "scatter5.scatter_texture_new"
    bl_label       = ""
    bl_description = translate("Create a new Scatter-Texture data")
    bl_options     = {'INTERNAL','UNDO'}

    ptr_name : bpy.props.StringProperty()
    new_name : bpy.props.StringProperty()

    def execute(self, context):

        #by default will always be the default texture .TEXTURE *DEFAULT MK...*
        #meaning we just have to dupplicate 
        texture_node = context.pass_ui_arg_texture_node
        texture_node.node_tree = texture_node.node_tree.copy()
        texture_node.node_tree.scatter5.texture.user_name = self.new_name
        texture_node.node_tree.scatter5.texture.mapping_random_allow = True

        #update api
        ctxt_system = context.pass_ui_arg_system #why on heck are we using a UILAyout context argument method here?
        setattr(ctxt_system,self.ptr_name, texture_node.node_tree.name)

        return {'FINISHED'}


class SCATTER5_OT_scatter_texture_enum(bpy.types.Operator):

    bl_idname      = "scatter5.scatter_texture_enum"
    bl_label       = translate("Texture Menu")
    bl_description = translate("Choose an existing scatter texture data-block from the list below.\nSelect 'None' to reset this datablock to its default state")
    bl_options     = {'INTERNAL','UNDO'}

    ptr_name : bpy.props.StringProperty()

    def generate_items(scene, context, ):
        items = []

        for ng in bpy.data.node_groups: 
            if ng.name.startswith(".TEXTURE "):
                if ( not ng.name.startswith(".TEXTURE *DEFAULT") and not ng.name.startswith(".TEXTURE *VISU") ):
                    items.append((ng.name, ng.name.replace(".TEXTURE ",""), ""))
                    continue

        #return message if nothing found
        if (len(items)==0):
            return [("none",translate("Nothing Found"),"")]

        #add separator & remove slots
        items.append(None)
        items.append((".TEXTURE *DEFAULT* MKV", translate("None"), ""))
        
        return items 

    enum : bpy.props.EnumProperty(items=generate_items,)

    def execute(self, context):

        if (self.enum=="none"):
            return {'FINISHED'} 

        ng = bpy.data.node_groups[self.enum]
        if (ng is None):
            print(f"ERROR: scatter5.scatter_texture_enum(): Nodegroup '{self.enum}' not found, should never happend")
            return {'FINISHED'} 

        texture_node = context.pass_ui_arg_texture_node
        texture_node.node_tree = bpy.data.node_groups[self.enum]
        texture_node.node_tree.scatter5.texture.user_name = self.enum.replace(".TEXTURE ","")
            
        #update our UVMap ptr
        texture_node.node_tree.scatter5.texture.mapping_uv_ptr = texture_node.node_tree.scatter5.texture.mapping_uv_ptr

        #update api
        ctxt_system = context.pass_ui_arg_system
        setattr(ctxt_system, self.ptr_name, texture_node.node_tree.name)

        #also update visualizer, if found 
        for o in [o for o in bpy.data.objects if (o.type=="MESH") and (len(o.modifiers)!=0)]:
            m = o.modifiers.get("ScatterVisualizer")
            if (m is not None):
                m.node_group.nodes["texture"].node_tree = ng
                break

        return {'FINISHED'}


class SCATTER5_OT_scatter_texture_duppli(bpy.types.Operator):

    bl_idname      = "scatter5.scatter_texture_duppli"
    bl_label       = translate("Make this texture data unique for this system")
    bl_description = translate("Make this texture data unique for this system")
    bl_options     = {'INTERNAL','UNDO'}

    ptr_name : bpy.props.StringProperty()

    def execute(self, context):

        #replace with copy and update naming
        texture_node = context.pass_ui_arg_texture_node
        texture_node.node_tree = texture_node.node_tree.copy()
        new_name = texture_node.node_tree.name.replace(".TEXTURE ","")
        texture_node.node_tree.scatter5.texture.user_name = new_name
        
        #update api
        ctxt_system = context.pass_ui_arg_system
        setattr(ctxt_system, self.ptr_name, texture_node.node_tree.name)

        return {'FINISHED'}


# class SCATTER5_OT_scatter_texture_preset(bpy.types.Operator): #FOR 5.1, but use classic preset system of blender, or implement them per category??? 

#     bl_idname      = "scatter5.scatter_texture_preset"
#     bl_label       = ""
#     bl_description = ""
#     bl_options     = {'INTERNAL','UNDO'}

#     def execute(self, context):

        # PresetsDict = {
        #     "empty_image": ("Image-Data",     "IMAGE_DATA",         {'type':'IMAGE','contrast':1,'factor_blue':1,'factor_green':1,'factor_red':1,'saturation':1,'intensity':1,'use_color_ramp':False,}),
        #     "clouds":      ("Clouds",         "W_DTXT_CLOUD",       {'type':'CLOUDS','noise_basis':'BLENDER_ORIGINAL','noise_type':'SOFT_NOISE','contrast':3,'factor_blue':1,'factor_green':1,'factor_red':1,'intensity':1,'noise_depth':0,'noise_scale':0.1,'saturation':1,'use_clamp':True,'use_color_ramp':False,}),
        #     "wood":        ("Wood",           "W_DTXT_WOOD",        {'type':'WOOD','wood_type':'BANDS','noise_basis':'BLENDER_ORIGINAL','noise_basis_2':'SIN','noise_type':'SOFT_NOISE','contrast':1,'factor_blue':1,'factor_green':1,'factor_red':1,'saturation':1,'turbulence':5,'use_clamp':True,'intensity':1,'noise_scale':0.25,'use_color_ramp':True,'s_colorramp_elements':[(0.21,[0,0,0,1]),(0.82,[0.28,0.28,0.28,1]),(1,[1,1,1,1])],'s_colorramp_interpolation':'LINEAR',}),
        #     "zebra":       ("Zebra",          "W_DTXT_ZEBRA",       {'type':'WOOD','wood_type':'BANDNOISE','noise_type':'SOFT_NOISE','noise_basis':'ORIGINAL_PERLIN','noise_basis_2':'SIN','contrast':3,'factor_blue':1,'factor_green':1,'factor_red':1,'intensity':0.04,'noise_scale':0.9,'saturation':1,'turbulence':15.6,'use_color_ramp':False,}),
        #     "marble" :     ("Marble",         "W_DTXT_RGB_MARBLE",  {'type':'MARBLE','marble_type':'SOFT','noise_basis':'BLENDER_ORIGINAL','noise_basis_2':'SIN','noise_type':'SOFT_NOISE','contrast':1,'turbulence':7,'saturation':1,'factor_blue':1,'factor_green':1,'factor_red':1,'intensity':1,'noise_depth':2,'use_clamp':True,'noise_scale':0.25,'use_color_ramp':False,}),
        #     "voronoi":     ("Voronoi",        "W_DTXT_VORONOI",     {'type':'VORONOI','color_mode':'POSITION','distance_metric':'MINKOVSKY','contrast':0.75,'factor_blue':2,'factor_green':2,'factor_red':2,'intensity':0.2,'minkovsky_exponent':10,'noise_intensity':1.6,'weight_1':1,'weight_2':0,'weight_3':0,'weight_4':0,'noise_scale':0.2,'saturation':0,'use_clamp':True,'use_color_ramp':False,}),
        #     "bubble":      ("Bubble",         "W_DTXT_BUBBLE",      {'type':'VORONOI','color_mode':'INTENSITY','contrast':3.0,'distance_metric':'DISTANCE','factor_blue':1.0,'factor_green':1.0,'factor_red':1.0,'intensity':1.15,'weight_1':1,'weight_2':0,'weight_3':0,'weight_4':0,'saturation':0.0,'use_clamp':True,'use_color_ramp':False,'minkovsky_exponent':2.5,'noise_intensity':1.1,'noise_scale':0.25,'use_preview_alpha':False,}),
        #     "blob":        ("Blob",           "W_DTXT_BLOB",        {'type':'VORONOI','distance_metric':'DISTANCE_SQUARED','color_mode':'INTENSITY','contrast':2.0,'factor_blue':1.0,'factor_green':1.0,'factor_red':1.0,'intensity':1.0,'minkovsky_exponent':2.5,'noise_intensity':1.5,'noise_scale':0.3,'saturation':0.0,'use_clamp':True,'weight_1':1.5,'weight_2':0.15,'weight_3':0.15,'weight_4':0.15,'use_color_ramp':True,'s_colorramp_interpolation':'CONSTANT','s_colorramp_elements':[(0.0,[0.0,0.0,0.0,1]),(0.35,[0.5,0.5,0.5,1]),(0.95,[1.0,1.0,1.0,1])],}),
        #     "musgrave":    ("Musgrave",       "W_DTXT_MUSGRAVE",    {'type':'MUSGRAVE','musgrave_type':'FBM','noise_basis':'ORIGINAL_PERLIN','contrast':1,'dimension_max':0.67,'factor_blue':1,'factor_green':1,'factor_red':1,'gain':1,'intensity':1,'noise_intensity':2,'noise_scale':0.31,'octaves':8,'offset':1,'saturation':1,'use_clamp':True,'use_color_ramp':False,}),
        #     "manhattan":   ("manhattan",      "W_DTXT_MANHATTAN",   {'type':'VORONOI','distance_metric':'MANHATTAN','color_mode':'POSITION','contrast':0.75,'factor_blue':2,'factor_green':2,'factor_red':2,'intensity':0.17,'minkovsky_exponent':10,'noise_intensity':1.6,'saturation':0,'use_clamp':True,'noise_scale':0.25,'weight_1':1,'weight_2':0.1,'weight_3':0,'weight_4':0,'use_color_ramp':False,}),
        #     "rgb_cloud":   ("RGB Cloud",      "W_DTXT_RGB_CLOUD",   {'type':'CLOUDS','noise_type':'SOFT_NOISE','noise_basis':'BLENDER_ORIGINAL','cloud_type':'COLOR','contrast':4.8,'factor_blue':2,'factor_green':2,'factor_red':2,'saturation':2,'intensity':0.25,'use_clamp':True,'noise_depth':2,'noise_scale':0.2,'use_color_ramp':False,}),
        #     "rgb_tiger":   ("RGB Tiger",      "W_DTXT_RGB_TIGER",   {'type':'MUSGRAVE','musgrave_type':'RIDGED_MULTIFRACTAL','noise_basis':'ORIGINAL_PERLIN','contrast':0.5,'dimension_max':1,'factor_blue':1,'factor_green':1,'factor_red':1,'gain':1,'intensity':1,'noise_intensity':1,'saturation':1,'use_clamp':True,'noise_scale':0.2,'octaves':2,'offset':1,'use_color_ramp':True,'s_colorramp_elements':[(0,[0,1,0,1]),(0.4,[0,0,1,1]),(0.7,[1,0,0,1])],'s_colorramp_interpolation':'CONSTANT',}),
        #     "rgb_camo":    ("RGB Camo",       "W_DTXT_RGB_CAMO",    {'type':'STUCCI','noise_basis':'ORIGINAL_PERLIN','stucci_type':'WALL_OUT','noise_type':'SOFT_NOISE','use_clamp':True,'contrast':1,'factor_blue':1,'saturation':1,'turbulence':7,'factor_green':1,'factor_red':1,'intensity':1,'noise_scale':0.1,'use_color_ramp':True,'s_colorramp_interpolation':'CONSTANT','s_colorramp_elements':[(0,[1,0,0,1]),(0.34,[0,1,0,1]),(0.60,[0,0,1,1])],}),
        #     "rgb_magic":   ("RGB Magic",      "W_DTXT_RGB_MAGIC",   {'type':'MAGIC','contrast':1,'factor_blue':1,'factor_green':1,'factor_red':1,'intensity':1,'saturation':1,'turbulence':9,'use_clamp':True,'noise_depth':0,'use_color_ramp':True,'s_colorramp_interpolation':'CONSTANT','s_colorramp_elements':[(0,[0.01,0,1,1]),(0.3985,[1,0,0,1]),(0.5707,[0,0,0,1]),(0.685,[0.008,1,0,1])],}),
        #     "rgb_voronoi": ("RGB Voronoi",    "W_DTXT_RGB_VORONOI", {'type':'VORONOI','color_mode':'POSITION_OUTLINE','distance_metric':'MINKOVSKY','contrast':1,'factor_blue':1,'factor_green':1,'factor_red':1,'intensity':1,'weight_1':1,'weight_2':0,'weight_3':0,'weight_4':0,'saturation':1,'use_clamp':True,'minkovsky_exponent':3,'noise_intensity':1.39,'noise_scale':0.35,'use_color_ramp':True,'s_colorramp_interpolation':'CONSTANT','s_colorramp_elements':[(0.0,[0.01,0,1,1]),(0.37,[0.008,1,0,1]),(0.563,[1,0,0,1]),(0.831,[0,0,0,1])],}),
        #     "rgb_pixel":   ("RGB Pixel",      "W_DTXT_RGB_PIXEL",   {'type':'STUCCI','noise_basis':'CELL_NOISE','noise_type':'SOFT_NOISE','stucci_type':'WALL_OUT','contrast':1,'factor_blue':1,'factor_green':1,'factor_red':1,'saturation':1,'turbulence':7,'use_clamp':True,'intensity':1,'noise_scale':0.2,'use_color_ramp':True,'s_colorramp_elements':[(0.0,[1,0,0,1]),(0.34,[0,1,0,1]),(0.66,[0,0,1,1])],'s_colorramp_interpolation':'CONSTANT',}),
        #     "rgb_curvy":   ("RGB Curvy",      "W_DTXT_RGB_CURVY",   {'type':'MARBLE','noise_type':'SOFT_NOISE','noise_basis':'ORIGINAL_PERLIN','noise_basis_2':'SIN','marble_type':'SHARP','contrast':0.75,'factor_blue':1,'factor_green':1,'factor_red':1,'intensity':0.9,'noise_depth':0,'noise_scale':0.6,'saturation':1,'turbulence':12.25,'use_clamp':True,'use_color_ramp':True,'s_colorramp_interpolation':'CONSTANT','s_colorramp_elements':[(0,[0,1,0,1]),(0.33,[0,0,1,1]),(0.68,[1,0,0,1])],},),
        #     "id_abstract": ("Id Abstract",    "W_DTXT_ID_ABSTRACT", {'type':'DISTORTED_NOISE','noise_basis':'CELL_NOISE','noise_distortion':'ORIGINAL_PERLIN','contrast':0.97,'distortion':1.7,'factor_blue':1,'factor_green':1,'factor_red':1,'intensity':1.3,'noise_scale':0.5,'saturation':1,'use_clamp':True,'use_color_ramp':True,'s_colorramp_elements':[(0,[0.685,0,0.656,1]),(0.038,[0.0,0.748,0.748,1]),(0.175,[1,0.423,0.0,1]),(0.319,[0.0102,0.1399,1,1]),(0.5512,[0.527,0.018,0.0,1]),(0.8564,[0.008,0.559,0.0,1])],'s_colorramp_interpolation':'CONSTANT',}),
        #     "id_lava":     ("Id Lava",        "W_DTXT_ID_LAVA",     {'type':'MUSGRAVE','musgrave_type':'MULTIFRACTAL','noise_basis':'ORIGINAL_PERLIN','contrast':0.91,'dimension_max':1,'factor_blue':1,'factor_green':1,'factor_red':1,'gain':1,'intensity':0.89,'noise_intensity':0.57,'noise_scale':0.26,'octaves':2.56,'offset':1,'saturation':1,'use_clamp':True,'use_color_ramp':True,'s_colorramp_elements':[(0,[0.685,0,0.656,1]),(0.014,[0,0.748,0.748,1]),(0.175,[1,0.423,0,1]),(0.435,[0.010,0.139,1,1]),(0.685,[0.527,0.018,0,1]),(0.955,[0.008,0.559,0,1])],'s_colorramp_interpolation':'CONSTANT',}),
        #     "id_marble":   ("Id Marble",      "W_DTXT_ID_MARBLE",   {'type':'MARBLE','marble_type':'SOFT','noise_basis':'ORIGINAL_PERLIN','noise_basis_2':'SIN','noise_type':'SOFT_NOISE','contrast':1,'factor_blue':1,'factor_green':1,'factor_red':1,'intensity':1,'noise_depth':24,'noise_scale':0.6,'saturation':1,'turbulence':13,'use_clamp':True,'use_color_ramp':True,'s_colorramp_elements':[(0,[0.685,0,0.656,1]),(0.038,[0.0,0.748,0.748,1]),(0.1757,[1,0.4231,0.0,1]),(0.367,[0.0102,0.1399,1,1]),(0.6736,[0.527,0.018,0.0,1]),(0.94,[0.008,0.559,0.0,1])],'s_colorramp_interpolation':'CONSTANT',}),
        #     "flow_lava":   ("Flowmap Lava",   "W_DTXT_FLOW_LAVA",   {'type':'CLOUDS','noise_basis':'BLENDER_ORIGINAL','noise_type':'HARD_NOISE','contrast':1,'saturation':1,'factor_blue':1,'factor_green':1,'factor_red':1,'intensity':1,'noise_depth':0,'noise_scale':0.5,'use_clamp':True,'use_color_ramp':True,'s_colorramp_interpolation':'LINEAR','s_colorramp_elements':[ (0,[1,0,0,1]),(0.310843348,[0,0,0,1]),(0.62,[0,0.5,0.008051,1]),(0.8,[0.8349971,1,0.029547309,1])],}),
        #     "flow_bubble": ("Flowmap Bubble", "W_DTXT_FLOW_BUBBLE", {'type':'CLOUDS','noise_basis':'VORONOI_F1','noise_type':'SOFT_NOISE','contrast':1,'saturation':1,'factor_blue':1,'factor_green':1,'factor_red':1,'intensity':1.13,'noise_depth':0,'noise_scale':0.5,'use_color_ramp':True,'s_colorramp_interpolation':'LINEAR','s_colorramp_elements':[(0,[1,0.21,0.02,1]),(0.26,[1,0,0,1]),(0.61,[0,0,0,1]),(1,[0.06,1,0.015,1.0])],'use_clamp':True,}),
        #     "flow_blue":   ("Flowmap Blue",   "W_DTXT_FLOW_BLUE",   {'type':'VORONOI','distance_metric':'DISTANCE_SQUARED','minkovsky_exponent':2.5,'color_mode':'INTENSITY','noise_scale':0.7,'contrast':1,'factor_blue':1,'factor_green':1,'factor_red':1,'intensity':1,'saturation':1,'noise_intensity':1.3,'use_clamp':True,'use_preview_alpha':False,'weight_1':1,'weight_2':0,'weight_3':0,'weight_4':0,'use_color_ramp':True,'s_colorramp_elements':[(0.09,[0,0,0,1]),(0.16,[0,0,0.59,1]),(0.53,[0,0.5,1,1]),(1,[0.5,1,1,1])],'s_colorramp_interpolation':'LINEAR',}),
        #     }

        # return {'FINISHED'}


# oooooooooo.                                        o8o
# `888'   `Y8b                                       `"'
#  888      888 oooo d8b  .oooo.   oooo oooo    ooo oooo  ooo. .oo.    .oooooooo
#  888      888 `888""8P `P  )88b   `88. `88.  .8'  `888  `888P"Y88b  888' `88b
#  888      888  888      .oP"888    `88..]88..8'    888   888   888  888   888
#  888     d88'  888     d8(  888     `888'`888'     888   888   888  `88bod8P'
# o888bood8P'   d888b    `Y888""8o     `8'  `8'     o888o o888o o888o `8oooooo.
#                                                                     d"     YD
#                                                                     "Y88888P'


class SCATTER5_PT_scatter_texture(bpy.types.Panel):

    bl_idname      = "SCATTER5_PT_scatter_texture"
    bl_label       = translate("Texture Settings")
    bl_description = translate("Click on this button to open the settings of this scatter texture data-block")
    bl_category    = ""
    bl_space_type  = "VIEW_3D"
    bl_region_type = "HEADER" #Hide this panel? not sure how to hide them...
    #bl_options     = {"DRAW_BOX"}

    def draw(self, context):
        
        layout = self.layout

        ng = context.pass_ui_arg_ng
        ctxt_system = context.pass_ui_arg_system
        node_props = ng.scatter5.texture      

        #Texture related settings: 
        
        element = layout.column(align=True)
        lbl = element.row(align=True)
        lbl.label(text=translate("Texture-Settings:"),)
        
        method = element.column(align=True)
        method.prop(node_props, "texture_type",text="")

        match node_props.texture_type:
            
            case 'brick_':

                element.separator(factor=0.511)
                
                props = element.column(align=True)
                props.scale_y = 0.85
                props.prop(node_props, "scale")
                element.separator(factor=0.5)
                props = element.column(align=True)
                props.scale_y = 0.85
                props.prop(node_props, "brick_offset")
                props.prop(node_props, "brick_offset_frequency")
                props.prop(node_props, "brick_squash")
                props.prop(node_props, "brick_squash_frequency")
                element.separator(factor=0.5)
                props = element.column(align=True)
                props.scale_y = 0.85
                props.prop(node_props, "brick_mortar_size")
                props.prop(node_props, "brick_mortar_smooth")
                props.prop(node_props, "brick_bias")
                props.prop(node_props, "brick_width")
                props.prop(node_props, "brick_row_height")

            case 'checker_':

                element.separator(factor=0.511)
                
                props = element.column(align=True)
                props.scale_y = 0.85
                props.prop(node_props, "scale")

            case 'image_':

                submethod = method.column(align=True)
                submethod.prop(node_props, "image_interpolation", text="")
                submethod.prop(node_props, "image_extension", text="")

                element.separator(factor=0.511)

                props = element.column(align=True)
                props.template_ID(node_props, "image_ptr", open="image.open")

                element.separator(factor=0.511)

                props = element.column(align=True)
                img_op = props.row(align=True)    
                op = img_op.operator("scatter5.bitmap_draw_menu", text=translate("Image Library"), icon="ASSET_MANAGER")
                op.ng_name=ng.name
                op = img_op.operator("scatter5.bitmap_skip", text="", icon="TRIA_LEFT", )
                op.ng_name=ng.name
                op.option="left"
                op = img_op.operator("scatter5.bitmap_skip", text="", icon="TRIA_RIGHT", )
                op.ng_name=ng.name
                op.option="right"
                op = img_op.operator("scatter5.bitmap_skip", text="", icon_value=cust_icon("W_DICE"), )
                op.ng_name=ng.name
                op.option="random"

                element.separator(factor=0.511)

                props = element.column(align=True)
                props.prop(node_props, "scale")

            case 'magic_':
                
                submethod = method.column(align=True)
                submethod.prop(node_props, "out_type",text="")
                
                element.separator(factor=0.511)
                
                props = element.column(align=True)
                props.scale_y = 0.85
                props.prop(node_props, "scale")
                props.prop(node_props, "magic_turbulence_depth")
                props.prop(node_props, "distorsion")

            case 'musgrave_':

                submethod = method.column(align=True)
                submethod.prop(node_props, "musgrave_musgrave_type",text="")
                
                element.separator(factor=0.511)
                
                props = element.column(align=True)
                props.scale_y = 0.85
                props.prop(node_props, "scale")
                props.prop(node_props, "detail")
                if (node_props.musgrave_musgrave_type!="FBM"):
                    props.prop(node_props, "musgrave_offset")

            case 'noise_':

                submethod = method.column(align=True)
                submethod.prop(node_props, "out_type",text="")
                
                element.separator(factor=0.511)
                
                props = element.column(align=True)
                props.scale_y = 0.85
                props.prop(node_props, "scale")
                props.prop(node_props, "detail")
                props.prop(node_props, "noise_roughness")
                props.prop(node_props, "distorsion")

            case 'voronoi_':

                submethod = method.column(align=True)
                submethod.prop(node_props, "voronoi_feature", text="")
                submethod.prop(node_props, "voronoi_distance", text="")
                submethod.prop(node_props, "out_type",text="")
                
                element.separator(factor=0.511)
                
                props = element.column(align=True)
                props.scale_y = 0.85
                props.prop(node_props, "scale")
                if (node_props.voronoi_distance=="MINKOWSKI"):
                    props.prop(node_props, "voronoi_exponent")
                props.prop(node_props, "voronoi_randomness")

            case 'white_noise_':

                submethod = method.column(align=True)
                submethod.prop(node_props, "out_type",text="")

            case 'wave_':
                
                submethod = method.column(align=True)
                submethod.prop(node_props,"wave_wave_type", text="")
                submethod.prop(node_props,"wave_bands_direction", text="")
                submethod.prop(node_props,"wave_wave_profile", text="")
                
                element.separator(factor=0.511)
                
                props = element.column(align=True)
                props.scale_y = 0.85
                props.prop(node_props,"scale")
                props.prop(node_props,"detail")
                props.prop(node_props,"distorsion")
                props.separator(factor=0.5)
                props = element.column(align=True)
                props.scale_y = 0.85
                props.prop(node_props,"wave_detail_scale")
                props.prop(node_props,"wave_detail_roughness")
                props.prop(node_props,"wave_phase_offset")

        #Color adjustment related settings:

        element = layout.column(align=True)
        lbl = element.row(align=True)
        lbl.label(text=translate("Color-Adjustments:"),)

        props = element.column(align=True)
        props.scale_y = 0.85
        props.prop(node_props, "intensity",)
        props.prop(node_props, "contrast",)
        props.prop(node_props, "saturation",)
        props.prop(node_props, "jitter",)

        clramp = element.column(align=True)
        clramp.prop(node_props, "use_color_ramp",)

        if (node_props.use_color_ramp==True):
            cr = clramp.column(align=True)
            cr.scale_y = 0.6
            #cr.separator()
            cr.box().template_color_ramp(ng.nodes["ColorRamp"], "color_ramp", expand=True)
            element.separator(factor=3)

        #Mapping related settings:

        element = layout.column(align=True)
        lbl = element.row(align=True)
        lbl.label(text="Projection Space:")

        element.prop(node_props, "mapping_projection",text="")

        match node_props.mapping_projection:
            
            case 'uv':
                ptr = element.row(align=True)
                ptr.alert = ( bool(node_props.mapping_uv_ptr) and not is_attr_surfs_shared(system=ctxt_system, attr_type='uv', attr_name=node_props.mapping_uv_ptr) )
                ptr.prop(node_props, "mapping_uv_ptr", text="", icon="GROUP_UVS", placeholder=" "+translate("UV Map"),)

            case 'object':
                ptr = element.row(align=True)
                ptr.prop(node_props, "mapping_obj_ptr", text="",)

        element = layout.column(align=True)
        lbl = element.row(align=True)
        lbl.label(text=translate("Transforms Space:"),)

        matrix = element.row(align=True)
        matrix.scale_y = 0.85
        matrix1 = matrix.column(align=True) ; matrix1.prop(node_props, "mapping_location", text="")
        matrix2 = matrix.column(align=True) ; matrix2.prop(node_props, "mapping_rotation", text="")
        matrix3 = matrix.column(align=True) ; matrix3.prop(node_props, "mapping_scale", text="")

        rdmap = element.column(align=True)
        rdmap.prop(node_props, "mapping_random_allow")

        if (node_props.mapping_random_allow):
            
            sed = rdmap.row(align=True)
            sed.prop( node_props, "mapping_random_seed")
            sedbutton = sed.row(align=True)
            sedbutton.scale_x = 1.2
            sedbutton.prop( node_props,"mapping_random_is_random_seed", icon_value=cust_icon("W_DICE"),text="")

        #Texture visualization:

        element = layout.column(align=True)
        lbl = element.row(align=True)
        lbl.label(text=translate("Visualizer:"),)

        is_vizualizing = ("S5PatternViz" in context.scene)
        ope = element.row()
        ope.alert = is_vizualizing
        args = {"text":translate("Quit Visualization"),"icon":"PANEL_CLOSE"} if is_vizualizing else {"text":translate("Visualize as Attribute"),"icon":"VPAINT_HLT"}
        op = ope.operator("scatter5.scatter_texture_visualizer", **args,)
        op.scatter_texture_name = ng.name
        
        return None 


def draw_texture_datablock(layout, system=None, ptr_name="", texture_node=None, new_name=""):
    """draw texture datablock"""

    from ... __init__ import addon_prefs

    ng = texture_node.node_tree

    #debug
    if (addon_prefs().debug_interface):
        
        debug = layout.box().column()
        debug.label(text=f"{ptr_name} = {getattr(system,ptr_name)}")
        debug.label(text=f"ng.name = {ng.name}")
        debug.label(text=f"ng.scatter5.texture.user_name = {ng.scatter5.texture.user_name}")
        
    tex_column = layout.column(align=True)

    #custom data row 

    data_row = tex_column.row(align=True)

    enum = data_row.row(align=True)
    enum.alignment = "LEFT"
    enum.scale_x = 0.91
    enum.context_pointer_set("pass_ui_arg_system", system,)
    enum.context_pointer_set("pass_ui_arg_texture_node", texture_node,)
    op = enum.operator_menu_enum("SCATTER5_OT_scatter_texture_enum", "enum", text=" ", icon="NODE_TEXTURE")
    op.ptr_name = ptr_name

    #create new inteface 

    if (ng.name.startswith(".TEXTURE *DEFAULT")):
        
        ope = data_row.row(align=True)
        ope.context_pointer_set("pass_ui_arg_system", system,)
        ope.context_pointer_set("pass_ui_arg_texture_node", texture_node,)
        op = ope.operator("scatter5.scatter_texture_new", text=translate("New"), icon="ADD", )
        op.ptr_name = ptr_name
        op.new_name = new_name
        
        return None 

    #name operator, special behavior that check if name not in double & will change the node_tree name accordingly

    text = data_row.row(align=True)
    text.prop(ng.scatter5.texture,"user_name", text="")

    #copy operator if ng has multiple users? 

    if (ng.users!=1):

        ope = data_row.row(align=True)
        ope.alignment = "RIGHT"
        ope.scale_x = 0.7
        ope.context_pointer_set("pass_ui_arg_system", system,)
        ope.context_pointer_set("pass_ui_arg_texture_node", texture_node,)
        op = ope.operator("scatter5.scatter_texture_duppli", text=str(len(ng.scatter5.texture.get_system_users(dupplis=True))),) #might be a lot of loop for UI.. 
        op.ptr_name = ptr_name

    #settings panel

    panel = data_row.row(align=True)
    panel.context_pointer_set("pass_ui_arg_ng", ng,)
    panel.context_pointer_set("pass_ui_arg_system", system,)
    panel.popover(panel="SCATTER5_PT_scatter_texture",text="", icon="OPTIONS",)

    return 


# oooooo     oooo  o8o                                            oooo   o8o
#  `888.     .8'   `"'                                            `888   `"'
#   `888.   .8'   oooo   .oooo.o oooo  oooo    oooooooo  .oooo.    888  oooo    oooooooo  .ooooo.  oooo d8b
#    `888. .8'    `888  d88(  "8 `888  `888   d'""7d8P  `P  )88b   888  `888   d'""7d8P  d88' `88b `888""8P
#     `888.8'      888  `"Y88b.   888   888     .d8P'    .oP"888   888   888     .d8P'   888ooo888  888
#      `888'       888  o.  )88b  888   888   .d8P'  .P d8(  888   888   888   .d8P'  .P 888    .o  888
#       `8'       o888o 8""888P'  `V88V"V8P' d8888888P  `Y888""8o o888o o888o d8888888P  `Y8bod8P' d888b



class SCATTER5_OT_scatter_texture_visualizer(bpy.types.Operator):

    bl_idname = "scatter5.scatter_texture_visualizer"
    bl_label = ""
    bl_description = translate("Visualize the texture on your mesh vertices with the help of vertex-color. Note that the surface(s) used will need to have enough vertices in order to visualize the attribute properly")
    bl_options = {'REGISTER'}

    scatter_texture_name : bpy.props.StringProperty()

    class InfoBox_scatter_texture_visualizer(SC5InfoBox):
       pass

    def __init__(self, *args, **kwargs):
        """Find ng, surfaces and viz objs"""
        
        super().__init__(*args, **kwargs)

        self.ng = bpy.data.node_groups.get(self.scatter_texture_name)

        #gather data to enter viz, aka all surface users 
        self.surface_users = set()
        for sys in self.ng.scatter5.texture.get_system_users():
            for s in sys.get_surfaces():
                self.surface_users.add(s)

        #gather data needed to exit viz (if already viz objects existing)
        self.viz_objs = set()
        for o in [o for o in bpy.data.objects if (o.type=="MESH")]: 
            if (".S5PatternViz" in o.data.color_attributes):
                self.viz_objs.add(o)

        return None

    def invoke(self, context, event):

        #quit if mode is active?
        if ("S5PatternViz" in context.scene):
            self.quit(context)
            return {'FINISHED'}

        #enter & run modal
        self.enter(context)
        context.window_manager.modal_handler_add(self)

        return {'RUNNING_MODAL'}

    def modal(self, context, event,):

        if (event.shift and event.type=='ESC'):
            self.quit(context)
            return {'FINISHED'}

        return {'PASS_THROUGH'}

    def enter(self, context):
            
        for o in self.surface_users:

            #add new color attr 
            if len(o.data.color_attributes):
                o["S5PatternViz_OLDACTIVE"] = o.data.color_attributes.active_color.name
            vcol = o.data.color_attributes.get(".S5PatternViz")
            if (vcol is None):
                o.data.vertex_colors.new(name=".S5PatternViz")
                vcol = o.data.color_attributes.get(".S5PatternViz")
            o.data.color_attributes.active_color = vcol

            #add geonode modifier and set up settings
            mod = import_and_add_geonode(o, mod_name="ScatterVisualizer", node_name=".ScatterTextureVisualizer", blend_path=directories.addon_visualizer_blend, is_unique=True,)
            print(directories.addon_visualizer_blend)
            
            mod["Output_3_attribute_name"] = vcol.name
            viz_node = mod.node_group.nodes["texture"]
            viz_node.node_tree = self.ng
            input_node = mod.node_group.nodes["Group Input"]
            output_node = mod.node_group.nodes["Group Output"]
            mod["Input_4"] = True #viz mode 
            mod["Input_5"] = o #emitter

            #check if viz_node connected properly, sometimes it detach for some strange reasons
            mod.node_group.links.new(viz_node.outputs[0], output_node.inputs[1])
            mod.node_group.links.new(input_node.outputs[1], viz_node.inputs[0])
            mod.node_group.links.new(input_node.outputs[2], viz_node.inputs[1])

            continue

        #set display to attribute
        context.space_data.shading.color_type = 'VERTEX'

        #add infobox on screen
        t = generic_infobox_setup(translate("Pattern Vcol Visualization"),
                                  translate("Currently Visualizing")+f" '{self.scatter_texture_name.replace('.TEXTURE ','')}'",
                                  [translate("Press [SHIFT+ESC] to Quit"),
                                  ],)
        self.InfoBox_scatter_texture_visualizer.init(t)
        # set following so infobox draw only in initial region
        self.InfoBox_scatter_texture_visualizer._draw_in_this_region_only = context.region
        # it is class variable, we don't know how it is set, so we need to make sure it is set how we want, and we want it to draw, only manual mode have option to hide it
        self.InfoBox_scatter_texture_visualizer._draw = True
        
        #remove mark of viz mode
        context.scene["S5PatternViz"] = True 

        return None 

    def quit(self, context):
        
        for o in self.viz_objs:

            #remove modifier 
            mod = o.modifiers.get("ScatterVisualizer")
            if (mod is not None):
                mod.node_group.nodes["texture"].node_tree = None
                o.modifiers.remove(mod)

            #remove vertex-color
            vcol = o.data.color_attributes.get(".S5PatternViz")
            if (vcol is not None):
                o.data.color_attributes.remove(vcol)
            if ("S5PatternViz_OLDACTIVE" in o):
                vcol = o.data.color_attributes.get(o["S5PatternViz_OLDACTIVE"])
                if (vcol is not None): 
                    o.data.color_attributes.active_color = vcol
                del o["S5PatternViz_OLDACTIVE"]

            continue

        #set display to object
        context.space_data.shading.color_type = 'OBJECT'

        #remove screen indication 
        self.InfoBox_scatter_texture_visualizer.deinit()

        #remove mark of viz mode
        if ("S5PatternViz" in context.scene):
            del context.scene["S5PatternViz"]

        return None 


# ooooooooo.                         o8o               .
# `888   `Y88.                       `"'             .o8
#  888   .d88'  .ooooo.   .oooooooo oooo   .oooo.o .o888oo  .ooooo.  oooo d8b
#  888ooo88P'  d88' `88b 888' `88b  `888  d88(  "8   888   d88' `88b `888""8P
#  888`88b.    888ooo888 888   888   888  `"Y88b.    888   888ooo888  888
#  888  `88b.  888    .o `88bod8P'   888  o.  )88b   888 . 888    .o  888
# o888o  o888o `Y8bod8P' `8oooooo.  o888o 8""888P'   "888" `Y8bod8P' d888b
#                        d"     YD
#                        "Y88888P'


classes = (
    
    SCATTER5_PT_scatter_texture,
    SCATTER5_OT_scatter_texture_new,
    SCATTER5_OT_scatter_texture_enum,
    SCATTER5_OT_scatter_texture_duppli,
    #SCATTER5_OT_scatter_texture_preset,
    SCATTER5_OT_scatter_texture_visualizer,

    )

def register():

    for cls in classes:
        bpy.utils.register_class(cls)

    return 

def unregister():

    del bpy.types.NodeTree.scatter5
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    return 