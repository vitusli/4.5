"""
*
* The foo application.
*
* Copyright (C) 2025 Yarrawonga VIC woodvisualizations@gmail.com
*
* This program is free software: you can redistribute it and/or modify
* it under the terms of the GNU General Public License as published by
* the Free Software Foundation, either version 3 of the License, or
* (at your option) any later version.
*
* This program is distributed in the hope that it will be useful,
* but WITHOUT ANY WARRANTY; without even the implied warranty of
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
* GNU General Public License for more details.
*
* You should have received a copy of the GNU General Public License
* along with this program.  If not, see <https://www.gnu.org/licenses/gpl-3.0.html>.
*
"""
import bpy
import fnmatch
import re
import os


def isListValid(lst):
    """
    Returns the second item of a list or raises an IndexError if missing.
    """
    if len(lst) < 2:  # Checks if the list has fewer than 2 items
        return False
    return lst[1]


def celOperatorType(mesh, value):
    value = value.replace("'", "")
    objectType = mesh.type
    
    if objectType == value:
        return True
    return False


def celOperatorHasattr(obj, value):
    value = value.replace("'", "")
    attributes = value.split(".")
    attributes = value.split(".")

    for attr in attributes:
        if not hasattr(obj, attr):
            return False
        obj = getattr(obj, attr)  # Go deeper
    
    return True


def draw(self, context):
    self.layout.label(text="Match Statement is missing a value", icon='ERROR')
    return {"CANCELLED"}


def searchSceneObjectsRecursive(pattern, collection=None):
    """
    Recursively search all objects in the given collection (and its sub-collections) that match the pattern.
    
    parameters:
    - pattern (str): A name pattern with wildcards to match objects.
    - collection (bpy.types.Collection): The collection to start the search from (defaults to the entire scene).
    
    Returns:
    - list: A list of matching objects.
    """
    pattern=pattern.replace(" ","")
    patternSplitted = pattern.split("AND")

    celSearch = patternSplitted[0]
    patternSplitted.remove(celSearch)

    matchingObjects = []
    matchingOperators = []

    # If no collection is passed, start with the entire scene
    if collection is None:
        collection = bpy.context.scene.collection

    # Search the objects in the current collection
    for obj in collection.objects:
        if fnmatch.fnmatch(obj.name, celSearch):
            matchingObjects.append(obj)

    # Recursively search in sub-collections
    for sub_collection in collection.children:
        matchingObjects.extend(searchSceneObjectsRecursive(pattern, sub_collection))
    if not patternSplitted:
        return matchingObjects
    
    for sceneObject in matchingObjects:
        typeResult = True
        hasattrResult = True
        for operator in patternSplitted:
            # This needs raise an error if there isn't a value provided
            operatorList = operator.split("==")
            listValid = isListValid(operatorList)

            if not listValid:
                print("ERROR: Cel Statment is missing a value")
                return False
            
            operatorType = operatorList[0]
            operatorValue = operatorList[1]

            if operatorType == "type":
                typeResult = celOperatorType(sceneObject, operatorValue)
                        
            if operatorType == "hasAttr":
                hasattrResult = celOperatorHasattr(sceneObject, operatorValue)

        if typeResult and hasattrResult:
            matchingOperators.append(sceneObject)

    return matchingOperators


def gatherconnectedNodes(node):
    """
    A Function for traversing the node tree and getting all connected nodes.
    Returns the nodes in order they are connected
    """
    nodes = []
    # Check all input sockets
    for input_socket in node.inputs:
        if input_socket.is_linked:
            for link in input_socket.links:
                nodes.append(link.from_node)
                gatheredNodes = gatherconnectedNodes(link.from_node)  # Recurse upstream

                for node in gatheredNodes:
                    nodes.append(node)
    
    return nodes


def getSceneInNode(node):
    connectedNodes = gatherconnectedNodes(node)
    
    if not connectedNodes:
        return None
    
    sceneInNode = connectedNodes[-1]

    return sceneInNode


def getCollection(node):
    sceneIn = getSceneInNode(node)
    if not sceneIn:
        print("No Connected SceneIn Node")
        return None
    
    collection = sceneIn.getOutputScene()

    return collection


def setAllNodesUnViewed():
    # Get the active node tree (for example, the Shader Node Tree)
    node_tree = bpy.data.node_groups.get("Rendering")
    color = (0.1, 0.1, 0.1)

    # Iterate through all nodes in the tree
    for node in node_tree.nodes:
        node.use_custom_color = True
        if node.type != "FRAME":
            node.color = color

def getAllRenderNodes():
    # Get the active node tree (for example, the Shader Node Tree)
    node_tree = bpy.data.node_groups.get("Rendering")

    renderNodes = []
    # Iterate through all nodes in the tree
    for node in node_tree.nodes:
        if node.bl_label == 'Render':
            renderNodes.append(node)
    
    return renderNodes


def setViewedNode(node):
    node_tree = bpy.data.node_groups.get("Rendering")
    node_tree.setViewedNode(node)


def getViewedNode():
    node_tree = bpy.data.node_groups.get("Rendering")
    return node_tree.viewedNode


def cookNode(node):
    setAllNodesUnViewed()
    connectedNodes = gatherconnectedNodes(node)

    if connectedNodes:
        connectedNodes.reverse()
    
    # append the parsed node so that it's executeNodeFunctions call is made last
    connectedNodes.append(node)

    for node in connectedNodes:
        failed = node.executeNodeCookFunctions()
        if failed:
            setNodeErroedColor(node)
        else:
            setNodePassedColor(node)


def cookRenderNodeFromName(nodeName):
    node_tree = bpy.data.node_groups.get("Rendering")
    if not node_tree:
        return True
    
    node = node_tree.nodes.get(nodeName)

    if not node:
        nodeNames = []
        for name in node_tree.nodes:
            if name.bl_idname == "RenderingLightingRenderLayerNode":
                nodeNames.append(name.name)
        print("Node didn't exist in list of nodes: "+str(nodeNames))
        return False
    
    cookNode(node)
    return True

def setNodeErroedColor(node):
    if node.type != "FRAME":
        node.color = (0.78, 0.18, 0.18)


def setNodePassedColor(node):
    if node.type != "FRAME":
        node.color = (0.28, 0.38, 0.54)


def getEnabledAovs(viewLayer=None):
    """
    Gathers all enabled AOVs in the specified view layer.
    
    Args:
    - view_layer (bpy.types.ViewLayer, optional): The view layer to check. Defaults to the active view layer.
    
    Returns:
    - list: A list of enabled AOV names.
    """
    if viewLayer is None:
        viewLayer = bpy.context.view_layer

    enabled_aovs = []

    # Default AOVS
    blenderAOVs = {"beauty": viewLayer.use_pass_combined,
        "z": viewLayer.use_pass_z,
        "mist": viewLayer.use_pass_mist,
        "position": viewLayer.use_pass_position,
        "normal": viewLayer.use_pass_normal,
        "vector": viewLayer.use_pass_vector,
        "uv": viewLayer.use_pass_uv,
        "objectIndex": viewLayer.use_pass_object_index,
        "materialIndex": viewLayer.use_pass_material_index,

        "diffuseDirect": viewLayer.use_pass_diffuse_direct,
        "diffuseIndirect": viewLayer.use_pass_diffuse_indirect,
        "diffuseAlbedo": viewLayer.use_pass_diffuse_color,
        "glossyDirect": viewLayer.use_pass_glossy_direct,
        "glossyIndirect": viewLayer.use_pass_glossy_indirect,
        "glossyAlbedo": viewLayer.use_pass_glossy_color,
        "transmissionDirect": viewLayer.use_pass_transmission_direct,
        "transmissionIndirect": viewLayer.use_pass_transmission_indirect,
        "transmissionAlbedo": viewLayer.use_pass_transmission_color,
        "volumeDirect": viewLayer.cycles.use_pass_volume_direct,
        "volumeIndirect": viewLayer.cycles.use_pass_volume_indirect,
        "emission": viewLayer.use_pass_emit,
        "environment": viewLayer.use_pass_environment,
        "ao": viewLayer.use_pass_ambient_occlusion,
        "shadowCatcher": viewLayer.cycles.use_pass_shadow_catcher,
        "cryptoObject": viewLayer.use_pass_cryptomatte_object,
        "cryptoMaterial": viewLayer.use_pass_cryptomatte_material,
        "cryptoAsset": viewLayer.use_pass_cryptomatte_asset,
    }

    for aov in blenderAOVs:
        if blenderAOVs[aov]:
            enabled_aovs.append(aov)

    return enabled_aovs

def setLatestOutputPath(filePath:str) -> str:
    if os.path.exists(filePath):
        bpy.context.scene.render.filepath = filePath
        return filePath

    bpy.context.scene.render.filepath = filePath


class NODE_UTIL_CookSceneFromNode(bpy.types.Operator):
    """
    Cooks the scene from this Node executing it's executeNodeCookFunctions command
    """
    bl_idname = "node.cook_scene_from_node"
    bl_label = "Cook Scene From Node"

    def execute(self, context):
        cookNode(context.node)

        return {'FINISHED'}
    

class NODE_UTIL_ResolveCelStatement(bpy.types.Operator):
    """
    Resolves a match statement and displays the found meshes
    """
    bl_idname = "node.resolve_cel_statement"
    bl_label = "Resolve Cel Statement"

    def execute(self, context):
        return {'FINISHED'}


def get_current_loc(context, event, ui_scale):
    x, y = context.region.view2d.region_to_view(event.mouse_region_x, event.mouse_region_y)
    return x / ui_scale, y / ui_scale
