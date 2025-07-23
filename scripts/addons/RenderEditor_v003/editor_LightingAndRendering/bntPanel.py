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
from .nodes import utilityFunctions


class RLE_OT_AssignMaterial(bpy.types.Operator):
    """
    Assigns the selected material to objects matching the match statement
    """
    bl_idname = "rle.assign_material"
    bl_label = "Assign Material"

    def execute(self, context):
        scene = context.scene  # Get the scene
        material = scene.bntSelectedMaterial  # Retrieve the selected material
        matchStatement = scene.bntMatchStatement  # Retrieve the match statement

        # Find matching objects
        matchingObjects = utilityFunctions.searchSceneObjectsRecursive(matchStatement)

        if not matchingObjects:
            self.report({'WARNING'}, f"No objects found matching '{matchStatement}'")
            return {'CANCELLED'}

        if not material:
            for obj in matchingObjects:
                if obj.type == 'MESH':
                    obj.data.materials.clear()

            self.report({'INFO'}, f"Removed materials from {len(matchingObjects)} objects: {str(matchingObjects)}")
            return {'FINISHED'}
        
        # Assign material to each matching object
        for obj in matchingObjects:
            if obj.type == 'MESH':
                if len(obj.data.materials) == 0:
                    obj.data.materials.append(material)  # Assign new material slot
                else:
                    obj.data.materials[0] = material  # Replace first material slot
            else:
                self.report({'WARNING'}, f"'{obj}' is not of type MESH, not assigning material")

        self.report({'INFO'}, f"Assigned '{material.name}' to {len(matchingObjects)} objects: {str(matchingObjects)}")
        return {'FINISHED'}


class RLE_OT_StoreNodeName(bpy.types.Operator):
    """
    Stores the selected node name for the menu
    """
    bl_idname = "rle.store_node_name"
    bl_label = "Store Node Name"
    bl_options = {"INTERNAL"}  # Not directly visible in the UI

    node_name: bpy.props.StringProperty()

    def execute(self, context):
        """
        Stores node name in WindowManager for menu access.
        """
        context.window_manager.rle_selected_node_name = self.node_name
        bpy.ops.wm.call_menu(name="RLE_MT_NodeContextMenu")  # Open menu
        return {"FINISHED"}


class RLE_MT_NodeContextMenu(bpy.types.Menu):
    """
    Context menu for render nodes
    """
    bl_label = "Node Options"

    def draw(self, context):
        layout = self.layout
        node_name = context.window_manager.get("rle_selected_node_name", "Unknown")

        opSVN = layout.operator("rle.set_viewed_node", text="Set as Viewed Node")
        opSVN.node_name = node_name
        opSVNSR = layout.operator("rle.set_viewed_node_and_start_live_render", text="Set as Viewed Node And Start Live Render")
        opSVNSR.node_name = node_name


class RLE_OT_SetViewedNode(bpy.types.Operator):
    """
    Set the selected node as the viewed node
    """
    bl_idname = "rle.set_viewed_node"
    bl_label = "Set Node as Viewed Node"

    node_name: bpy.props.StringProperty()

    def execute(self, context):
        utilityFunctions.cookRenderNodeFromName(self.node_name)

        # Set Render Engine (Cycles or Eevee)
        bpy.context.scene.render.engine = "CYCLES"  # or "BLENDER_EEVEE"

        return {"FINISHED"}


class RLE_OT_SetViewedNodeAndStartLiverender(bpy.types.Operator):
    """
    Set the selected node as the viewed node
    """
    bl_idname = "rle.set_viewed_node_and_start_live_render"
    bl_label = "Set Node as Viewed Node and Render"

    node_name: bpy.props.StringProperty()

    def execute(self, context):
        utilityFunctions.cookRenderNodeFromName(self.node_name)

        # Set Render Engine (Cycles or Eevee)
        bpy.context.scene.render.engine = "CYCLES"  # or "BLENDER_EEVEE"

        # Set Viewport Shading to Rendered Mode
        for area in bpy.context.screen.areas:
            if area.type == "VIEW_3D":
                print("hit")
                for space in area.spaces:
                    if space.type == "VIEW_3D":
                        space.shading.type = 'RENDERED'  # Enable live rendering
        return {"FINISHED"}


class RLE_PT_SidePanel(bpy.types.Panel):
    """
    Side panel for the Rendering Editor
    """
    bl_label = "Blender NodeGraph Traverser"
    bl_idname = "RLE_PT_SidePanel"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Rendering"

    def draw(self, context):
        layout = self.layout
        node_tree = context.space_data.node_tree
        scene = context.scene  # Get the scene for property access
        layout.alignment = 'LEFT'

        if node_tree and node_tree.bl_idname == "RenderingLightingNodeTree":
            # Output Path Section
            layout.prop(scene, "outputParentLocation", text="Output Parent Path")
            layout.separator()
            layout.separator()
            nodeBox = layout.box()
            nodeBox.label(text="Render Nodes:", icon='NODETREE')
            
            layout.separator()
            layout.separator()
            assignerBox = layout.box()
            assignerBox.label(text="Bulk Material Assigner:", icon='NODETREE')
            assingerRow = assignerBox.row()
            assingerRow.scale_x = 2.0
            assingerRow.alignment = 'LEFT'
            assingerRow.prop(context.scene, "bntMatchStatement", text="Match Statement")
            assignerBox.prop(context.scene, "bntSelectedMaterial", text="Match Statement")
            assignerBox.operator("rle.assign_material", text="Assign Material", icon='CHECKMARK')

            for node in utilityFunctions.getAllRenderNodes():
                row = nodeBox.row()
                op = row.operator("rle.store_node_name", text=node.layerName)
                op.node_name = node.layerName
        else:
            layout.label(text="No Rendering & Lighting Tree active")


def register():
    bpy.types.WindowManager.rle_selected_node_name = bpy.props.StringProperty()
    
    bpy.types.Scene.bntMatchStatement = bpy.props.StringProperty(
        name="Match Statement",
        description="Enter a Match statement",
        default="",
    )

    bpy.types.Scene.bntSelectedMaterial = bpy.props.PointerProperty(
        name="Material",
        description="Select a material",
        type=bpy.types.Material
    )
    bpy.utils.register_class(RLE_OT_AssignMaterial)
    bpy.utils.register_class(RLE_OT_StoreNodeName)
    bpy.utils.register_class(RLE_MT_NodeContextMenu)
    bpy.utils.register_class(RLE_OT_SetViewedNode)
    bpy.utils.register_class(RLE_OT_SetViewedNodeAndStartLiverender)
    bpy.utils.register_class(RLE_PT_SidePanel)

    bpy.types.Scene.outputParentLocation = bpy.props.StringProperty(
        name="Output Parent Location",
        description="This is where the render nodes will read to output their passes to",
        default=""
    )


def unregister():
    del bpy.types.WindowManager.rle_selected_node_name
    del bpy.types.Scene.bntMatchStatement
    del bpy.types.Scene.bntSelectedMaterial

    bpy.utils.unregister_class(RLE_OT_AssignMaterial)
    bpy.utils.unregister_class(RLE_OT_StoreNodeName)
    bpy.utils.unregister_class(RLE_MT_NodeContextMenu)
    bpy.utils.unregister_class(RLE_OT_SetViewedNode)
    bpy.utils.unregister_class(RLE_OT_SetViewedNodeAndStartLiverender)
    bpy.utils.unregister_class(RLE_PT_SidePanel)
