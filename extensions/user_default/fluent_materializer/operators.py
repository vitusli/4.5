from bpy.props import StringProperty, EnumProperty, BoolProperty
from bpy_extras.io_utils import ImportHelper
from bpy_types import Operator
from mathutils import Vector
import bmesh
from math import degrees, radians
import time
import numpy as np

from .t3dn_bip.ops import InstallPillow

from .constants import IOR
from .Tools.helper import *


class FLUENT_SHADER_OT_addNodes(Operator):
    bl_idname = 'fluent.add_nodes'
    bl_description = 'Add Node Setup'
    bl_category = 'Node'
    bl_label = 'Add Setup'

    choice: bpy.props.StringProperty()
    from_add_decal: bpy.props.BoolProperty()

    def invoke(self, context, event):
        global temp
        bpy.ops.object.mode_set(mode='OBJECT')
        if event.ctrl and event.shift and event.alt:
            bpy.context.window_manager.popup_menu(make_oops(['Add a node in the material.',
            'If nothing is selected, the new node is placed at the center of the node tree.',
            'If a node is selected, the new node is placed next to this one.']), title="Node addition", icon='INFO')

            return {'FINISHED'}

        try:
            material = context.material
            tree = material.node_tree
            nodes = tree.nodes
            selected_nodes = bpy.context.selected_nodes
        except:
            obj = bpy.context.active_object
            mat = bpy.data.materials.new(name="F_Material")
            mat.use_nodes = True
            if obj.data.materials:
                obj.data.materials[0] = mat
            else:
                # no slots
                obj.data.materials.append(mat)
            material = bpy.context.active_object.active_material
            tree = material.node_tree
            nodes = tree.nodes
            selected_nodes = []
            for node in nodes:
                if node.type == 'BSDF_PRINCIPLED':
                    node.select = True
                    nodes.active = node
                    selected_nodes.append(node)
                else:
                    node.select = False

        try:
            if nodes.active and nodes.active.select:
                previous_node = nodes.active
            else:
                previous_node = None
            # previous_node = bpy.context.selected_nodes[0]
        except:
            previous_node = None

        group_name = None
        fluent_props = bpy.context.scene.FluentShaderProps
        if self.choice in ['imperfections', 'grunges', 'patterns', 'liquid', 'city', 'normals', 'fabric', 'metal', 'shaders', 'wood', 'screen', 'decals', 'environment', 'manmade']:
            coll_full_name = "fm_%s" % fluent_props.sections
            group_name = getattr(bpy.context.window_manager, coll_full_name)
        elif self.choice in ['Smart Shader 2 layers', 'Smart Shader 3 layers']:
            try:
                if previous_node.type == 'BSDF_PRINCIPLED':
                    group_name = 'Mix Layers'
                else:
                    bpy.context.window_manager.popup_menu(make_oops(['Select a Principled BSDF before calling this function.']), title="How to use :", icon='INFO')
                    return{'FINISHED'}
            except:
                bpy.context.window_manager.popup_menu(make_oops(['Select a Principled BSDF before calling this function.']), title="How to use :", icon='INFO')
                return{'FINISHED'}

        if group_name is None:
            group_name = self.choice

        deselect_nodes(nodes)
        new_group = import_node_group(group_name, context)
        apply_node_color(new_group)

        if previous_node:
            new_group.location = previous_node.location
            new_group.location[0] -= previous_node.dimensions[0] * (1/context.preferences.system.ui_scale) + 50

        if self.choice == 'Mix Layers':
            if previous_node and previous_node.type == 'BSDF_PRINCIPLED':
                deselect_nodes(nodes)
                research_previous = 'FAIL'
                # recherche si un mix est déja connecté
                if previous_node.inputs['Base Color'].links:
                    node_precedente = previous_node.inputs['Base Color'].links[0].from_node
                    if node_precedente.type == 'GROUP' and node_precedente.node_tree.name == 'Mix Layers':
                        research_previous = 'SUCCESS'
                if research_previous == 'SUCCESS':
                    # connecte le nouveaux mix au BSDF
                    connect_mixlayers_to_bsdf(material, new_group, previous_node)
                    # connecte les sorties du mix précédent aux entrées du nouveau mix
                    connect_layer_to_mixlayers(material, node_precedente, new_group)
                    new_group.location = [(node_precedente.location[0]+previous_node.location[0])/2, (node_precedente.location[1]+previous_node.location[1])/2]
                else:
                    connect_mixlayers_to_bsdf(material, new_group, previous_node)
                new_group.select = True
            elif previous_node and previous_node.type == 'GROUP' and previous_node.node_tree.name == 'Mix Layers':
                new_group = bpy.context.selected_nodes[0]
                deselect_nodes(nodes)
                # recherche ce qui est connecté en amont
                link_1 = link_2 = None
                action = None
                if previous_node.inputs['Color 1'].links:
                    link_1 = previous_node.inputs['Color 1'].links
                if previous_node.inputs['Color 2'].links:
                    link_2 = previous_node.inputs['Color 2'].links
                if link_1 and link_2:
                    action = 'ADD_AFTER'
                elif not link_1 or not link_2:
                    action = 'ADD_BEFORE'
                if action == 'ADD_BEFORE':
                    connect_layer_to_mixlayers(material, new_group, previous_node)
                if action == 'ADD_AFTER':
                    try:
                        node_precedente = to_what(previous_node, 'Color')['node'][0]
                    except:
                        node_precedente = None
                    if node_precedente:
                        if node_precedente.type == 'BSDF_PRINCIPLED':
                            connect_mixlayers_to_bsdf(material, new_group, node_precedente)
                            connect_layer_to_mixlayers(material, previous_node, new_group)
                        if node_precedente.type == 'GROUP' and node_precedente.node_tree.name == 'Mix Layers':
                            # connecte le nouveaux mix à celui qui était sélectionné
                            connect_layer_to_mixlayers(material, previous_node, new_group)
                            # connecte le nouveau mix au mix précedent celui qui était sélectionné
                            connect_layer_to_mixlayers(material, new_group, node_precedente)
                        new_group.location = [(node_precedente.location[0] + previous_node.location[0]) / 2, (node_precedente.location[1] + previous_node.location[1]) / 2]
                if not action:
                    new_group.location.x += 400
            elif previous_node and previous_node.type == 'GROUP' and 'Layer' in previous_node.node_tree.name:
                deselect_nodes(nodes)
               # cherche le mix layers suivant
                suivante = to_what(previous_node, 1)
                node_suivantes = suivante['node']
                soket_suivants = suivante['socket']
                node_suivante = None
                for i, n in enumerate(node_suivantes):
                    if n.type == 'GROUP' and n.node_tree.name == 'Mix Layers':
                        node_suivante = n
                        socket_suivant = soket_suivants[i]
                        break
                if node_suivante:
                    #connect le layer au nouveau mix layers
                    connect_layer_to_mixlayers(material, previous_node, new_group)
                    # connect le nouveau mix layer au mix layer en avale
                    if '1' in socket_suivant:
                        connect_layer_to_mixlayers(material, new_group, node_suivante, 1)
                    if '2' in socket_suivant:
                        connect_layer_to_mixlayers(material, new_group, node_suivante, 2)
                    new_group.location.y = (previous_node.location.y + node_suivante.location.y)/2
                    new_group.location.x = (previous_node.location.x + node_suivante.location.x)/2
        elif self.choice == 'Layer':
            if previous_node and previous_node.type == 'GROUP' and 'Mix Layers' in previous_node.node_tree.name:
                connect_layer_to_mixlayers(material, new_group, previous_node)
            elif previous_node and previous_node.type == 'BSDF_PRINCIPLED':
                connect_layer_to_bsdf(material, new_group, previous_node)
        elif self.choice in {'Edges', 'Cavity', 'All edges', 'Directional Mask', 'Painted Mask', 'Local mask', 'Color Mask', 'Slope', 'Altitude', 'Streaks mask', 'WornOut Wizard'} and previous_node:
            # vérifie si la node sélectionnée à une entrée mask si oui on la connecte à la sortie mask de la node tout juste ajoutée
            try:
                for input in selected_nodes[0].inputs:
                    if input.name == 'Mask' and not input.links:
                        link(material, bpy.context.selected_nodes[0], 'Mask', selected_nodes[0], 'Mask')
            except:pass
        elif previous_node and self.choice == 'Smart Shader 2 layers' and previous_node.type == 'BSDF_PRINCIPLED':
            mix_1 = new_group
            deselect_nodes(nodes)
            connect_mixlayers_to_bsdf(material, mix_1, previous_node)

            layer_1 = import_node_group('Layer', context)
            connect_layer_to_mixlayers(material, layer_1, mix_1)
            apply_node_color(layer_1)

            layer_2 = import_node_group('Layer', context)
            connect_layer_to_mixlayers(material, layer_2, mix_1)
            apply_node_color(layer_2)

            layer_1.location = [mix_1.location[0]-200, mix_1.location[1] + 120]
            layer_2.location = [mix_1.location[0]-200, mix_1.location[1] - 320]
            return {'FINISHED'}
        elif previous_node and self.choice == 'Smart Shader 3 layers' and previous_node.type == 'BSDF_PRINCIPLED':
            mix_2 = new_group
            deselect_nodes(nodes)
            connect_mixlayers_to_bsdf(material, mix_2, previous_node)

            mix_1 = import_node_group('Mix Layers', context)
            connect_layer_to_mixlayers(material, mix_1, mix_2)
            apply_node_color(mix_1)

            layer_1 = import_node_group('Layer', context)
            connect_layer_to_mixlayers(material, layer_1, mix_1)
            apply_node_color(layer_1)

            layer_2 = import_node_group('Layer', context)
            connect_layer_to_mixlayers(material, layer_2, mix_1)
            apply_node_color(layer_2)

            layer_3 = import_node_group('Layer', context)
            connect_layer_to_mixlayers(material, layer_3, mix_2)
            apply_node_color(layer_3)

            mix_1.location = [mix_2.location[0] - 200, mix_2.location[1]]
            layer_3.location = [mix_2.location[0], mix_1.location[1] - 280]
            layer_1.location = [mix_1.location[0]-200, mix_1.location[1] + 120]
            layer_2.location = [mix_1.location[0]-200, mix_1.location[1] - 320]
            return{'FINISHED'}
        elif new_group.node_tree.name == 'Pixel':
            new_screen_node_tree = make_single_user_node(new_group)
            for n in new_screen_node_tree.nodes:
                if n.type == 'GROUP' and n.node_tree.name == 'Image_Instance':
                    new_image_instance_node_tree = make_single_user_node(n)
                    break
            for n in new_screen_node_tree.nodes:
                if n.type == 'GROUP' and n.node_tree.name == 'Glitcher':
                    new_glitcher_node_tree = make_single_user_node(n)
                    for nn in new_glitcher_node_tree.nodes:
                        if nn.type == 'GROUP' and nn.node_tree.name == 'Image_Instance':
                            nn.node_tree = new_image_instance_node_tree
                    break

        deselect_nodes(nodes)
        new_group.select = True
        nodes.active = new_group
        temp = {'last_addition': new_group, 'previous_node': previous_node}

        if 'Scale' in new_group.inputs:
            new_group.inputs['Scale'].default_value *= context.scene.FluentShaderProps.scale_scale

        bpy.ops.fluent.sample_editor('INVOKE_DEFAULT')

        # Vérifie s'il s'agit d'un decal
        if self.from_add_decal:
            return {'FINISHED'}
        for n in new_group.node_tree.nodes:
            if n.type == 'FRAME' and n.label == 'is_decal':
                bpy.ops.fluent.newdecal('INVOKE_DEFAULT', is_generic_decal=True)

        new_group.location = get_x_y_for_node(new_group)

        return {'FINISHED'}


class FLUENT_SHADER_OT_SwapLayers(Operator):
    """Swap all entries of the selected mix layers"""
    bl_idname = 'fluent.swaplayers'
    bl_category = 'Node'
    bl_label = 'Swap layers'

    def execute(self, context):
        active_material = context.material
        nodes = get_nodes(active_material)
        the_mix_layers = None

        if len(bpy.context.selected_nodes) == 2:
            if bpy.context.selected_nodes[0].node_tree.name != 'Mix Layers' and bpy.context.selected_nodes[1].node_tree.name != 'Mix Layers':
                if 'Layer' in bpy.context.selected_nodes[0].node_tree.name and 'Layer' in bpy.context.selected_nodes[1].node_tree.name:
                    layer_1 = bpy.context.selected_nodes[0]
                    layer_2 = bpy.context.selected_nodes[1]
            else:
                bpy.context.window_manager.popup_menu(make_oops(['Select two Layers node.']), title="INFO", icon='INFO')
                return {'FINISHED'}
        else:
            bpy.context.window_manager.popup_menu(make_oops(['Select two Layers node.']), title="INFO", icon='INFO')
            return{'FINISHED'}

        if layer_1 and layer_2:
            layer_1_origin = to_what(layer_1, 'Color')
            layer_2_origin = to_what(layer_2, 'Color')
            layer_1_previous_input = 0
            layer_2_previous_input = 0
            if '1' in layer_1_origin['socket'][0]:
                layer_1_previous_input = 1
            if '2' in layer_1_origin['socket'][0]:
                layer_1_previous_input = 2
            if '1' in layer_2_origin['socket'][0]:
                layer_2_previous_input = 1
            if '2' in layer_2_origin['socket'][0]:
                layer_2_previous_input = 2

            connect_layer_to_mixlayers(active_material, layer_1, layer_2_origin['node'][0], layer_2_previous_input)
            connect_layer_to_mixlayers(active_material, layer_2, layer_1_origin['node'][0], layer_1_previous_input)

        return{'FINISHED'}


class FLUENT_SHADER_OT_LayerMixLayersConnect(Operator):
    """Auto connexion between layer, mix layers, Principled shader"""
    bl_idname = 'fluent.layermixlayersconnect'
    bl_category = 'Node'
    bl_label = 'Layer connector'

    def execute(self, context):
        active_material = active_object('GET').active_material
        nodes = get_nodes(active_material)

        selected_nodes = get_selected_nodes(nodes)
        layer_node = None
        mix_node = None

        if len(selected_nodes) == 2:
            # layer vers mix layer
            if selected_nodes[0].type == 'GROUP' and selected_nodes[0].node_tree.name == 'Layer':
                layer_node = selected_nodes[0]
            elif selected_nodes[1].type == 'GROUP' and selected_nodes[1].node_tree.name == 'Layer':
                layer_node = selected_nodes[1]
            if selected_nodes[0].type == 'GROUP' and selected_nodes[0].node_tree.name == 'Mix Layers':
                mix_node = selected_nodes[0]
            elif selected_nodes[1].type == 'GROUP' and selected_nodes[1].node_tree.name == 'Mix Layers':
                mix_node = selected_nodes[1]

            if layer_node and mix_node:
                connect_layer_to_mixlayers(active_material, layer_node, mix_node)
                return {'FINISHED'}

            # mix layers vers mix layers
            mix_node_1 = None
            mix_node_2 = None
            if selected_nodes[0].type == 'GROUP' and selected_nodes[0].node_tree.name == 'Mix Layers':
                mix_node_1 = selected_nodes[0]
            if selected_nodes[1].type == 'GROUP' and selected_nodes[1].node_tree.name == 'Mix Layers':
                mix_node_2 = selected_nodes[1]

            if mix_node_1 and mix_node_2:
                # le mix de gauche est en amont
                mix_temp = None
                if mix_node_2.location.x < mix_node_1.location.x:
                    connect_layer_to_mixlayers(active_material, mix_node_2, mix_node_1)
                    return {'FINISHED'}
                if mix_node_2.location.x > mix_node_1.location.x:
                    connect_layer_to_mixlayers(active_material, mix_node_1, mix_node_2)
                return {'FINISHED'}

            # mix to principled BSDF
            mix_node = None
            BSDF_node = None
            if selected_nodes[0].type == 'BSDF_PRINCIPLED':
                BSDF_node = selected_nodes[0]
            elif selected_nodes[1].type == 'BSDF_PRINCIPLED':
                BSDF_node = selected_nodes[1]
            if selected_nodes[0].type == 'GROUP' and selected_nodes[0].node_tree.name == 'Mix Layers':
                mix_node = selected_nodes[0]
            elif selected_nodes[1].type == 'GROUP' and selected_nodes[1].node_tree.name == 'Mix Layers':
                mix_node = selected_nodes[1]

            if mix_node and BSDF_node:
                connect_mixlayers_to_bsdf(active_material, mix_node, BSDF_node)
                return {'FINISHED'}

            # layer to principled BSDF
            layer_node = None
            BSDF_node = None
            if selected_nodes[0].type == 'BSDF_PRINCIPLED':
                BSDF_node = selected_nodes[0]
            elif selected_nodes[1].type == 'BSDF_PRINCIPLED':
                BSDF_node = selected_nodes[1]
            if selected_nodes[0].type == 'GROUP' and selected_nodes[0].node_tree.name == 'Layer':
                layer_node = selected_nodes[0]
            elif selected_nodes[1].type == 'GROUP' and selected_nodes[1].node_tree.name == 'Layer':
                layer_node = selected_nodes[1]

            if layer_node and BSDF_node:
                connect_mixlayers_to_bsdf(active_material, layer_node, BSDF_node)
                return {'FINISHED'}

        return{'FINISHED'}


class FLUENT_SHADER_OT_NewPaintedMask(Operator):
    """Paint a mask"""
    bl_idname = 'fluent.newpaintedmask'
    bl_category = 'Node'
    bl_label = 'Paint a mask'

    the_node: StringProperty()
    option: StringProperty()

    @classmethod
    def poll(cls, context):
        if bpy.context.active_object and bpy.context.active_object.type in ['MESH', 'CURVE']:
            return True
        else:
            cls.poll_message_set("Select an object")
            return False

    def invoke(self, context, event):
        # Vérification avant lancement
        try:
            material = context.material
            tree = material.node_tree
            nodes = tree.nodes
            material_output = get_material_output(nodes)
            previous_node = nodes.active
            uv_layers = bpy.context.active_object.data.uv_layers
            if not len(uv_layers):
                bpy.context.window_manager.popup_menu(make_oops(['No UV map.', 'Please, unwrap your model.', 'The paint process isn\'t a procedural workflow but an image based workflow. So UVs needed.']), title="INFO", icon='INFO')
                return {'FINISHED'}
            masks_list = ['Edges', 'All edges', 'Cavity', 'Directional Mask', 'Painted Mask', 'Math Mix', 'Multiply', 'Difference', 'Overlay', 'Lighten', 'Screen']
            test = [a for a in masks_list if a in previous_node.name]
            if self.option in ['MULTIPLY', 'DIFFERENCE'] and len(test) == 0:
                bpy.context.window_manager.popup_menu(make_oops(['Currently, this function work only with another mask.']), title="INFO", icon='INFO')
                return {'FINISHED'}
        except:
            return {'FINISHED'}
        # Fin vérification avant lancement
        global temp
        active_obj = bpy.context.active_object
        active_material = context.material
        tree = active_material.node_tree
        nodes = tree.nodes
        bpy.ops.fluent.add_nodes('INVOKE_DEFAULT', choice = 'Painted Mask')
        new_group = temp['last_addition']
        previous_node = temp['previous_node']
        # créer l'image
        properties = bpy.context.scene.FluentShaderProps
        # mask_img = bpy.data.images.new(active_obj.name+'_'+active_material.name+'_'+"painted", width=self.size, height=self.size)
        mask_img = create_img(active_obj, int(properties.udim_paint_size), 'painted', True, False, properties.udim_paint_baking, properties.udim_paint_count)
        mask_img.file_format = 'PNG'
        # copie indépendante
        original = new_group.node_tree
        single = original.copy()
        new_group.node_tree = single
        # récupération de la node image
        for node in new_group.node_tree.nodes:
            if node.type == 'TEX_IMAGE':
                img_node = node
        img_node.image = mask_img
        # auto mix si demandé
        previous_node = temp['previous_node']
        if previous_node and self.option != 'Painted Mask':
            for o in previous_node.outputs:
                if len(o.links):
                    previous_node_linked_to = {'output':o, 'target':to_what(previous_node, o.name)}
                    break
            # shift → multiply
            if self.option == 'MULTIPLY':
                operation_node = import_node_group('Multiply', context)
            # alt → substract
            if self.option == 'DIFFERENCE':
                operation_node = import_node_group('Difference', context)
            # relie la previous node au multiply
            link(active_material, previous_node, previous_node.outputs[0].name, operation_node, operation_node.inputs[0].name)
            # relie le multiply à ce à quoi la previous était reliée
            link(active_material, operation_node, operation_node.outputs[0].name, previous_node_linked_to['target']['node'][0], previous_node_linked_to['target']['socket'][0])
            # relie le painted mask au multiply
            link(active_material, new_group, 'Mask', operation_node, operation_node.inputs[1].name)
            # repositionnement
            operation_node.location = previous_node.location
            # previous_node.location[1] -= previous_node.dimensions[1]*(1/context.preferences.system.ui_scale)
            previous_node.location[1] += previous_node.dimensions[1]*(1/context.preferences.system.ui_scale)
            new_group.location[1] = previous_node.location[1]
        deselect_nodes(nodes)
        nodes.active = img_node
        img_node.select = True
        area = next(area for area in bpy.context.screen.areas if area.type == 'VIEW_3D')
        space = next(space for space in area.spaces if space.type == 'VIEW_3D')
        space.shading.type = 'MATERIAL'
        bpy.ops.object.mode_set(mode='TEXTURE_PAINT')
        # sélectionne le slot à peindre
        for idx, img in enumerate(active_material.texture_paint_images):
            if img == mask_img:
                active_material.paint_active_slot = idx
        # connect directement la node painted mask à la sortie pour visualisation et chargement rapide.
        link(active_material, new_group, 'Mask', material_output, 0)
        return{'FINISHED'}


class FLUENT_SHADER_OT_EditPaintedMask(Operator):
    """Edit the selected painted mask"""
    bl_idname = 'fluent.editpaintedmask'
    bl_category = 'Node'
    bl_label = 'Edit a painted a mask'

    def execute(self, context):
        active_obj = active_object('GET')
        material = context.material
        tree = material.node_tree
        nodes = tree.nodes
        material_output = get_material_output(nodes)
        if nodes.active and nodes.active.select:
            previous_node = nodes.active
        else:
            bpy.context.window_manager.popup_menu(make_oops(['Painted mask edition function.', 'Select a painted mask node before.']), title="INFO", icon='INFO')
            return{'FINISHED'}

        if 'Painted Mask' in previous_node.node_tree.name:
            for n in previous_node.node_tree.nodes:
                if n.type == 'TEX_IMAGE':
                    img_node = n
        if img_node:
            for idx, img in enumerate(material.texture_paint_images):
                if img == img_node.image:
                    material.paint_active_slot = idx
            # bpy.ops.node.nw_preview_node('INVOKE_DEFAULT')
            link(material, previous_node, 'Mask', material_output, 0)
            area = next(area for area in bpy.context.screen.areas if area.type == 'VIEW_3D')
            space = next(space for space in area.spaces if space.type == 'VIEW_3D')
            space.shading.type = 'MATERIAL'
            bpy.ops.object.mode_set(mode='TEXTURE_PAINT')

        return{'FINISHED'}


class FLUENT_SHADER_OT_Refresh(Operator):
    """Edit the selected painted mask"""
    bl_idname = 'fluent.refresh'
    bl_label = 'Refresh cycles viewport'

    def execute(self, context):
        bpy.context.space_data.shading.type = 'SOLID'
        bpy.context.space_data.shading.type = 'RENDERED'
        return{'FINISHED'}


class FLUENT_SHADER_OT_NewDecal(Operator):
    """Add a decal node"""
    bl_idname = 'fluent.newdecal'
    bl_label = 'Add a decal node'

    image_path: bpy.props.StringProperty()
    duplicate: bpy.props.BoolProperty()
    is_normal_decal: bpy.props.BoolProperty(default=False)
    is_procedural_decal: bpy.props.BoolProperty()
    is_generic_decal: bpy.props.BoolProperty()
    already_load:bpy.props.BoolProperty(default=False)
    call_worn_edges: bpy.props.BoolProperty(default=False)

    def invoke(self, context, event):
        # vérifications
        obj = active_object(action='GET')
        if context.material:
            decal_image = None
            active_material = context.material
            nodes = get_nodes(active_material)
            selected_nodes = bpy.context.selected_nodes
            if self.duplicate:
                active_node = nodes.active
                new_node_group = nodes.new(type='ShaderNodeGroup')
                new_node_group.node_tree = active_node.node_tree
                make_unique_node_group(new_node_group)
                previous_empty = search_text_coord(active_node)
                decal_node = new_node_group
                decal_node.location += active_node.location + Vector((20, 20))
                active_node.select = False
                for n, input in enumerate(active_node.inputs):
                    decal_node.inputs[n].default_value = input.default_value
            global temp
            if self.is_procedural_decal:
                bpy.ops.fluent.add_nodes('INVOKE_DEFAULT', choice='decals', from_add_decal=True)
                decal_node = temp['last_addition']
            if self.image_path:
                if self.is_normal_decal:
                    bpy.ops.fluent.add_nodes('INVOKE_DEFAULT', choice='Decal_Normal')
                else:
                    choice = 'Decal'
                    if self.call_worn_edges:
                        choice = 'Decal_Worn_Edges'
                    bpy.ops.fluent.add_nodes('INVOKE_DEFAULT', choice=choice)
                decal_node = temp['last_addition']

            if self.is_generic_decal:
                decal_node = temp['last_addition']

            try:
                bpy.data.objects.remove(object=bpy.data.objects['text_coord'], do_unlink=True)
            except:pass

            # set l'empty dans l'uv coordinate
            if event.shift:
                # utilise l'empty de la node sélectionnée comme reference des coordonnées
                tex_ref = search_text_coord(selected_nodes[0])
                change_all_coordinates(decal_node, tex_ref)
            else:
                bpy.ops.object.empty_add(type='SINGLE_ARROW', align='WORLD')
                empty = active_object(action='GET')
                empty['fluent_type'] = 'decal_projector'

                if 'previous_empty' in locals():
                    empty.scale = previous_empty.scale
                    empty.rotation_euler = previous_empty.rotation_euler
                    empty.location = previous_empty.location

                change_all_coordinates(decal_node, empty)

                active_object(action='SET', obj=empty, solo=True)
                context.scene.tool_settings.snap_elements = {'FACE'}
                context.scene.tool_settings.snap_target = 'CENTER'
                context.scene.tool_settings.use_snap_align_rotation = True

            if self.image_path and not self.duplicate:
                if self.call_worn_edges:
                    gradient_path = decal_gradient_generator(self.image_path)
                if not decal_image:
                    decal_image = bpy.data.images.load(filepath=self.image_path, check_existing=False)
                    if self.call_worn_edges:
                        gradient_image = bpy.data.images.load(filepath=gradient_path, check_existing=False)
                decal_node.node_tree.nodes['Image Texture'].image = decal_image
                if self.call_worn_edges:
                    decal_node.node_tree.nodes['Edge_Gradient'].image = gradient_image
                if self.is_normal_decal:
                    decal_image.colorspace_settings.name = 'Non-Color'
            else:
                try:
                    bpy.data.objects.remove(object=bpy.data.objects['text_coord'], do_unlink=True)
                except:pass

            if not self.duplicate and not self.is_procedural_decal and self.image_path:
                ratio = decal_image.size[1]/decal_image.size[0]
                empty.scale[0] = 1/ratio

            return{'FINISHED'}


class FLUENT_SHADER_OT_SynchronizeDecal(Operator):
    """Use same empty as texture coordinates source.
Select the source last"""
    bl_idname = 'fluent.synchronizedecal'
    bl_label = 'Synchronize decal texture coordinates source'

    def invoke(self, context, event):
        material = bpy.context.active_object.active_material
        tree = material.node_tree
        nodes = tree.nodes
        selected_nodes = bpy.context.selected_nodes
        active_node = bpy.context.active_node

        if not (selected_nodes and active_node):
            return {'FINISHED'}

        # récupère l'empty de la node active
        empty = search_text_coord(active_node)
        for n in selected_nodes:
            if n != active_node:
                bpy.data.objects.remove(object=search_text_coord(n), do_unlink=True)
                change_all_coordinates(n, empty)

        return {'FINISHED'}


class FLUENT_SHADER_OT_Localmask(Operator):
    """Add a local mask node"""
    bl_idname = 'fluent.localmask'
    bl_label = 'Add a local mask node'

    def invoke(self, context, event):
        # vérifications
        obj = active_object(action='GET')
        if obj:
            active_material = obj.active_material
            nodes = get_nodes(active_material)
            bpy.ops.fluent.add_nodes('INVOKE_DEFAULT', choice='Local mask')

            global temp
            decal_node = temp['last_addition']
            original = decal_node.node_tree
            single = original.copy()
            decal_node.node_tree = single

            bpy.ops.object.empty_add(type='SINGLE_ARROW', align='WORLD')
            empty = active_object(action='GET')
            empty['fluent_type'] = 'decal_projector'

            # set l'empty dans l'uv coordinate
            change_all_coordinates(decal_node, empty)

            active_object(action='SET', obj=empty, solo=True)
            context.scene.tool_settings.snap_elements = {'FACE'}
            context.scene.tool_settings.snap_target = 'CENTER'
            context.scene.tool_settings.use_snap_align_rotation = True

            return{'FINISHED'}


class FLUENT_SHADER_OT_NodeCounter(Operator):
    bl_idname = 'fluent.node_counter'
    bl_description = 'Count the nodes in the node tree'
    bl_category = 'Node'
    bl_label = 'Node counter'

    def count_inside(self, node):
        count = 0
        nodes = node.node_tree.nodes
        for n in nodes:
            if n.type == 'GROUP':
                count += self.count_inside(n)
            else:
                if n.type not in ['GROUP_INPUT', 'GROUP_OUTPUT']:
                    count +=1
        return count

    def invoke(self, context, event):
        active_material = active_object('GET').active_material
        nodes = get_nodes(active_material)
        count_total = 0
        for n in nodes:
            if n.type == 'GROUP':
                count_total += self.count_inside(n)
            else:
                count_total +=1
        ratio = round(((len(nodes)-1)/count_total - 1) * 100,1) * -1
        bpy.context.window_manager.popup_menu(make_oops([str(count_total-1)+" nodes in your material."]), title="INFO", icon='INFO')
        return{'FINISHED'}


class FLUENT_SHADER_OT_SampleEditor(Operator):
    bl_idname = 'fluent.sample_editor'
    bl_description = 'Update the number of samples in all the needed nodes'
    bl_category = 'Node'
    bl_label = 'Update samples'

    def update_samples(self, node):
        nodes = node.node_tree.nodes
        for n in nodes:
            if n.type == 'GROUP':
                self.update_samples(n)
                continue

            if n.type in ['BEVEL', 'AMBIENT_OCCLUSION']:
                n.samples = bpy.context.scene.FluentShaderProps.nb_samples

    def invoke(self, context, event):
        active_material = context.material
        nodes = get_nodes(active_material)
        for n in nodes:
            if n.type == 'GROUP':
                self.update_samples(n)

        return {'FINISHED'}


class FLUENT_SHADER_OT_ImageExtractor(Operator):
    bl_idname = 'fluent.imageextractor'
    bl_description = 'Convert an image into a group to extract roughness and normal'
    bl_category = 'Node'
    bl_label = 'Image extractor'

    @classmethod
    def poll(cls, context):
        if context.active_object and context.active_object.active_material:
            material = context.active_object.active_material
            nodes = material.node_tree.nodes
            # Vérifier les nœuds sélectionnés
            selected_nodes = [node for node in nodes if node.select]
            # if len(selected_nodes)>1:
            #     cls.poll_message_set("Select only one node.")
            #     return False
            # Vérifier si parmi les nœuds sélectionnés, il y a une Image Texture
            image_texture_found = any(isinstance(node, bpy.types.ShaderNodeTexImage) for node in selected_nodes)
            if image_texture_found:
                return True
            else:
                cls.poll_message_set("No image node selected")
                return False

    def execute(self, context):
        active_material = active_object('GET').active_material
        nodes = get_nodes(active_material)
        selected_nodes = [node for node in nodes if node.select]
        img_node = None
        bsdf_node = None
        layer_node = None
        for node in selected_nodes:
            if isinstance(node, bpy.types.ShaderNodeTexImage):
                img_node = node
            if isinstance(node, bpy.types.ShaderNodeBsdfPrincipled):
                bsdf_node = node
            if node.type == 'GROUP' and node.node_tree.name == 'Layer':
                layer_node = node

        img = img_node.image
        bpy.ops.fluent.add_nodes('INVOKE_DEFAULT', choice='Image Data Extractor')
        new_group = make_single_user_node(temp['last_addition'])
        new_group.location = img_node.location
        for n in new_group.node_tree.nodes:
            if n.type == 'TEX_IMAGE':
                n.image = img
        nodes.remove(img_node)
        if bsdf_node:
            link(active_material, new_group, 'Color', bsdf_node, 0)
            link(active_material, new_group, 'Metallic', bsdf_node, 1)
            link(active_material, new_group, 'Roughness', bsdf_node, 2)
            link(active_material, new_group, 'Normal', bsdf_node, 5)
        if layer_node:
            link(active_material, new_group, 'Color', layer_node, 'Color')
            link(active_material, new_group, 'Metallic', layer_node, 'Metallic')
            link(active_material, new_group, 'Roughness', layer_node, 'Roughness')
            link(active_material, new_group, 'Normal', layer_node, 'Normal')
        return{'FINISHED'}


class FLUENT_OT_restore_hotkey(Operator):
    bl_idname = "fluent.restore_hotkey"
    bl_label = "Restore hotkeys"
    bl_options = {'REGISTER', 'INTERNAL'}

    km_name: StringProperty()

    def execute(self, context):
        context.preferences.active_section = 'KEYMAP'
        wm = context.window_manager
        kc = wm.keyconfigs.addon
        km = kc.keymaps.get(self.km_name)
        if km:
            km.restore_to_default()
            context.preferences.is_dirty = True
        context.preferences.active_section = 'ADDONS'
        return {'FINISHED'}


class FLUENT_SHADER_OT_FindHelp(Operator):
    """How to find help"""
    bl_idname = 'fluent.findhelp'
    bl_label = 'How to find help'

    def execute(self, context):
        bpy.context.window_manager.popup_menu(make_oops(['Hold Shift+Ctrl+Alt when you click on button to display the documentation about it.']), title="Find help.", icon='INFO')
        return{'FINISHED'}


class FLUENT_SHADER_OT_InstallPIL(Operator, InstallPillow):
    bl_idname = "fluent.install_pil"
    bl_label = "Install PIL"
    bl_description = "Install pip and PIL"


class FLUENT_SHADER_OT_DELETEPIL(Operator):
    bl_idname = "fluent.delete_pil"
    bl_label = "Delete Pil"
    bl_description = "Delete PIL"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        _, _, modulespaths, sitepackagespath, usersitepackagespath = get_python_paths()

        remove_pil(sitepackagespath, usersitepackagespath, modulespaths)

        get_addon_preferences().pil_warning = False
        get_addon_preferences().pil = False

        return {'FINISHED'}


class FLUENT_SHADER_OT_OpenFilebrowser(Operator, ImportHelper):
    bl_idname = "fluent.open_filebrowser"
    bl_label = "Open the file browser (yay)"

    filter_glob: StringProperty(
        default='*.jpg;*.jpeg;*.png;*.tif;*.tiff;*.bmp',
        options={'HIDDEN'}
    )

    continue_to: StringProperty(
        default='',
        options={'HIDDEN'}
    )

    call_worn_edges: BoolProperty(
        default=False,
        options={'HIDDEN'}
    )

    # some_boolean: BoolProperty(
    #     name='Do a thing',
    #     description='Do a thing with the file you\'ve selected',
    #     default=True,
    # )

    def execute(self, context):
        """Select a file"""
        if self.call_worn_edges and not get_addon_preferences().cv2:
            self.report({'WARNING'}, 'cv2 had to be installed to use it. Install cv2 in the add-on preferences.')
            return{'FINISHED'}
        filename, extension = os.path.splitext(self.filepath)
        if self.continue_to == 'new_decal':
            bpy.ops.fluent.newdecal('INVOKE_DEFAULT', image_path=self.filepath, call_worn_edges=self.call_worn_edges)
        elif self.continue_to == 'new_decal_normal':
            bpy.ops.fluent.newdecal('INVOKE_DEFAULT', image_path=self.filepath, is_normal_decal=True)

        return {'FINISHED'}


class FLUENT_SHADER_OT_SearchIOR(bpy.types.Operator):
    bl_idname = "fluent.searchior"
    bl_label = "Search"
    bl_property = "ior_list"

    def add_ior(self, context):
        material = context.material

        node_tree = material.node_tree
        nodes = node_tree.nodes
        links = node_tree.links

        value_node = nodes.new(type='ShaderNodeValue')

        current_value = self.ior_list

        items = [(key, key, str(value)) for key, value in IOR.items()]
        for item in items:
            if item[0] == current_value:
                ior = float(item[2])
                break

        value_node.outputs[0].default_value = ior
        value_node.label = self.ior_list + ' IOR'

        for node in nodes:
            node.select = False
        value_node.select = True
        node_tree.nodes.active = value_node

    ior_list: EnumProperty(
        name="My Search",
        items=[(key, key, str(value)) for key, value in IOR.items()],
        update=add_ior
    )

    def execute(self, context):
        self.report({'INFO'}, "Selected:" + self.ior_list)
        self.add_ior(context)
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {'RUNNING_MODAL'}


class FLUENT_SHADER_OT_ResetBaking(bpy.types.Operator):
    bl_idname = "fluent.reset_baking"
    bl_label = "Reset baking"

    def execute(self, context):
        context.scene.FluentShaderProps.is_baking = False
        context.scene.FluentShaderProps.baking_error = ''

        return {'FINISHED'}


class FLUENT_SHADER_OT_HeightGradient(bpy.types.Operator):
    """Make streaks based on geometry data"""
    bl_idname = "fluent.heightgradient"
    bl_label = "Make gradient in attribut"

    refresh: BoolProperty()

    @classmethod
    def poll(cls, context):
        if bpy.context.active_object and context.object.mode == 'OBJECT' and bpy.context.active_object.type in ['MESH', 'CURVE']:
            return True
        else:
            cls.poll_message_set("Select an object")
            return False

    def add_face_corner_to_island(self, island, faces_already_done, face):
        faces_already_done.add(face.index)
        island.append(face)

        for loop in face.loops:
            edge = loop.edge
            try:
                face1, face2 = edge.link_faces
                angle = face1.normal.angle(face2.normal)
                if angle < bpy.context.scene.FluentShaderProps.angle_threshold:
                    edge.seam = False
                    if face1.index != face.index and face1.index not in faces_already_done:
                        island, faces_already_done = self.add_face_corner_to_island(island, faces_already_done, face1)
                    if face2.index != face.index and face2.index not in faces_already_done:
                        island, faces_already_done = self.add_face_corner_to_island(island, faces_already_done, face2)
            except:
                pass
        return island, faces_already_done

    def add_vertical_gradient(self):
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        obj = bpy.context.object
        mesh = obj.data
        bm = bmesh.new()
        bm.from_mesh(mesh)

        bm.faces.ensure_lookup_table()

        islands = []
        faces_already_done = set()
        sablier = time.time()
        for face in bm.faces:
            if face.index in faces_already_done:
                continue

            island = []  # contient les faces
            island, faces_already_done = self.add_face_corner_to_island(island, faces_already_done, face)
            islands.append(island)
        my_grad_layer = bm.loops.layers.float.get("mz_vertical_gradient")
        if my_grad_layer is None:
            my_grad_layer = bm.loops.layers.float.new("mz_vertical_gradient")

        for island in islands:
            z = []
            z_max = float('-inf')
            z_min = float('inf')
            for face in island:
                for loop in face.loops:
                    z_co = loop.vert.co.z
                    if z_co > z_max:
                        z_max = z_co
                    if z_co < z_min:
                        z_min = z_co
            if bpy.context.scene.FluentShaderProps.auto_mid:
                z_min = z_max - (z_max - z_min) / 2
            else:
                z_min = z_max - obj.dimensions.z
            # y = ax+b
            a = 1 / (z_max - z_min) if z_max != z_min else 0
            b = 1 - a * z_max

            for face in island:
                for loop in face.loops:
                    loop[my_grad_layer] = a * loop.vert.co.z + b

        bm.to_mesh(mesh)
        bm.free()

    def add_covered_attribute(self, obj):
        bpy.ops.object.mode_set(mode='OBJECT')

        mesh = obj.data
        bm = bmesh.new()
        bm.from_mesh(mesh)

        # Ajout de l'attribut "covered"
        covered_layer = bm.verts.layers.int.get("mz_no_covered")
        if covered_layer is None:
            covered_layer = bm.verts.layers.int.new("mz_no_covered")

        matrix_world = obj.matrix_world

        # Léger décalage le long de la normale pour éviter la détection au lancement
        offset_factor = 0.01 * max(obj.dimensions)

        depsgraph = bpy.context.evaluated_depsgraph_get()

        # Pour chaque sommet, lancer un rayon vers le haut
        for vert in bm.verts:
        # for face in bm.faces:
            # for loop in face.loops:
            # vert = loop.vert
            vert_world_pos = matrix_world @ vert.co

            # Calcul de la normale du sommet en coordonnées globales
            normal_world = (matrix_world.to_3x3() @ vert.normal).normalized()

            # Décaler légèrement le point de départ du rayon
            start_pos = vert_world_pos + normal_world * offset_factor

            ray_direction = Vector((0, 0, 1))

            # Lancer le raycast
            result, location, normal, index, object, matrix = bpy.context.scene.ray_cast(
                depsgraph, start_pos, ray_direction, distance=bpy.context.scene.FluentShaderProps.max_ray_distance)

            if result:
                vert[covered_layer] = 0
            else:
                vert[covered_layer] = 1

        # Appliquer les changements au mesh
        bm.to_mesh(mesh)
        bm.free()

    def execute(self, context):
        obj = bpy.context.active_object
        if obj and obj.type == 'MESH':
            self.add_vertical_gradient()
            self.add_covered_attribute(obj)

            if not self.refresh:
                bpy.ops.fluent.add_nodes('INVOKE_DEFAULT', choice='Streaks mask')

        return {'FINISHED'}


class FLUENT_SHADER_OT_AttributeReader(bpy.types.Operator):
    """Make value mixer based on color attribute
Hold Shift : update the node with new color"""
    bl_idname = "fluent.attributreader"
    bl_label = "Attribute reader"

    @classmethod
    def poll(cls, context):
        if bpy.context.active_object and context.object.mode == 'OBJECT' and bpy.context.active_object.type in ['MESH', 'CURVE']:
            return True
        else:
            cls.poll_message_set("Select an object")
            return False

    def attribute_reader(self, objs):
        unique_colors = set()
        for obj in objs:
            if obj is not None and obj.type == 'MESH':
                color_layer = obj.data.vertex_colors.active

                if color_layer is not None:
                    # Parcours de toutes les boucles pour récupérer les couleurs
                    for poly in obj.data.polygons:
                        for loop_index in poly.loop_indices:
                            loop_color = color_layer.data[loop_index].color
                            # Ajoute la couleur sous forme de tuple dans le set pour éliminer les doublons
                            unique_colors.add(tuple(loop_color))

                    # Affiche la liste des couleurs uniques
                    print(f"Unique colors found : {len(unique_colors)}")
                    for color in unique_colors:
                        print(color)
                else:
                    bpy.context.window_manager.popup_menu(make_oops(['Color attribute not found.', 'Add color attribute from vertex paint tool of Blender.']), title="Problem", icon='INFO')
            else:
                make_oops(['Please select a mesh.'])
        return unique_colors

    def build_inner_node(self, node_group, obj, unique_colors):
        input_node = node_group.nodes.new('NodeGroupInput')
        input_node.name = 'Group Input'
        input_node.location = Vector((-400, 0))
        output_node = node_group.nodes.new('NodeGroupOutput')
        output_node.name = 'Group Output'

        vertex_color = node_group.nodes.new('ShaderNodeVertexColor')
        vertex_color.layer_name = obj.data.vertex_colors.active.name
        vertex_color.location = Vector((-400, -400))

        mix_float_added = []
        node_x = 0
        node_y = 0

        for i, c in enumerate(unique_colors):
            gamma = node_group.nodes.new('ShaderNodeGamma')
            gamma.inputs[1].default_value = 2.2
            gamma.location = Vector((node_x, node_y))
            node_x += 200
            mix_color = node_group.nodes.new('ShaderNodeMixRGB')
            mix_color.blend_type = 'DIFFERENCE'
            mix_color.inputs[0].default_value = 1.0
            mix_color.location = Vector((node_x, node_y))
            node_x += 200
            math = node_group.nodes.new('ShaderNodeMath')
            math.operation = 'COMPARE'
            math.inputs[1].default_value = 0.0
            math.inputs[2].default_value = 0.01
            math.location = Vector((node_x, node_y))
            node_x += 200
            mix_float = node_group.nodes.new('ShaderNodeMix')
            mix_float_added.append(mix_float)
            mix_float.location = Vector((node_x, node_y))
            node_x = 0
            node_y -= 200
            node_group.links.new(input_node.outputs[i * 2], gamma.inputs[0])
            node_group.links.new(gamma.outputs[0], mix_color.inputs[2])
            node_group.links.new(mix_color.outputs[0], math.inputs[0])
            node_group.links.new(math.outputs[0], mix_float.inputs[0])
            node_group.links.new(input_node.outputs[(i * 2) + 1], mix_float.inputs[3])
            node_group.links.new(vertex_color.outputs[0], mix_color.inputs[1])
            node_group.links.new(math.outputs[0], output_node.inputs[i])

        output_node.location = Vector((1000, 0))

        node_group.links.new(mix_float_added[0].outputs[0], output_node.inputs[-2])
        for i in range(len(unique_colors)):
            try:
                node_group.links.new(mix_float_added[i + 1].outputs[0], mix_float_added[i].inputs[2])
            except: pass

    def build_node(self, unique_colors, obj):
        group_name = "Value by vertex color"
        node_group = bpy.data.node_groups.new(name=group_name, type='ShaderNodeTree')

        for i, c in enumerate(unique_colors):
            socket = node_group.interface.new_socket(in_out='INPUT', socket_type='NodeSocketColor', name='Color')
            socket.default_value = c
            node_group.interface.new_socket(in_out='INPUT', socket_type='NodeSocketFloat', name='Value')
            node_group.interface.new_socket(in_out='OUTPUT', socket_type='NodeSocketFloat', name='Mask '+ str(i))
        node_group.interface.new_socket(in_out='OUTPUT', socket_type='NodeSocketFloat', name='Values per color')

        self.build_inner_node(node_group, obj, unique_colors)

        return node_group

    def update_node(self, unique_colors, node, obj):
        node_group = bpy.data.node_groups.get(node.node_tree.name)
        already_in_node = []
        count = 0
        for item in node_group.interface.items_tree:
            if item.in_out == 'INPUT' and item.name == 'Color':
                already_in_node.append((item.default_value[0], item.default_value[1], item.default_value[2], item.default_value[3]))
        count = len(already_in_node)
        for i, c in enumerate(unique_colors):
            if c in already_in_node:
                continue
            socket = node_group.interface.new_socket(in_out='INPUT', socket_type='NodeSocketColor', name='Color')
            socket.default_value = c
            node_group.interface.new_socket(in_out='INPUT', socket_type='NodeSocketFloat', name='Value')
            node_group.interface.new_socket(in_out='OUTPUT', socket_type='NodeSocketFloat', name='Mask '+ str(count))
            count += 1
            # Force la mise à jour de la couleur
            for input in node.inputs:
                if input.type == 'RGBA' and tuple(input.default_value) == (0.0, 0.0, 0.0, 1.0):
                    input.default_value = c

        for item in node_group.interface.items_tree:
            if item.name == 'Values per color':
                node_group.interface.move(item, 99)

        #Vide le group de node
        remove_me = []
        for n in node_group.nodes:
            remove_me.append(n)
        for n in remove_me:
            node_group.nodes.remove(n)

        self.build_inner_node(node_group, obj, unique_colors)

        return

    def invoke(self, context, event):
        obj = bpy.context.active_object
        if obj:
            objs = bpy.context.selected_objects
            unique_colors = self.attribute_reader(objs)
            if not len(unique_colors):
                return {'FINISHED'}

            if event.shift:
                #update la node si déjà présente dans le matériau
                mat = obj.active_material
                if mat:
                    nodes = mat.node_tree.nodes
                for n in nodes:
                    if n.type == 'GROUP' and 'Value by vertex color' in n.node_tree.name:
                        self.update_node(unique_colors, n, obj)
                        break
                return {'FINISHED'}

            node_group = self.build_node(unique_colors, obj)

            mat = obj.active_material
            if mat:
                nodes = mat.node_tree.nodes
                group_node = nodes.new("ShaderNodeGroup")
                group_node.node_tree = node_group
                group_node.location = get_x_y_for_node(group_node)

        return {'FINISHED'}


class FLUENT_SHADER_OT_InstallOpenCV(bpy.types.Operator):
    bl_idname = "fluent.install_cv2"
    bl_label = "Install cv2"

    def execute(self, context):
        if install_cv2():
            self.report({'INFO'}, 'Successfully installed cv2')
            get_addon_preferences().cv2_warning = True
        else:
            self.report({'WARNING'}, 'Failed to install cv2')

        return {'FINISHED'}