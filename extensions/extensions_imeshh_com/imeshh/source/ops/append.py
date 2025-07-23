import os

import bpy
from bpy.props import IntProperty, StringProperty, BoolProperty
from bpy.types import Operator

from ..utils.addon import preferences
from ..utils.product import get_asset_path, get_products


class IMESHH_OT_append(Operator):
    """Append or link asset from iMeshh"""

    bl_label = "Append"
    bl_idname = "imeshh.append"
    bl_options = {"REGISTER", "INTERNAL"}

    product_id: IntProperty(options={"SKIP_SAVE"})
    filepath: StringProperty(subtype="FILE_PATH", options={"SKIP_SAVE"})
    link_mode: BoolProperty(
        name="Link Mode",
        description="Link the asset instead of appending",
        default=False,
        options={"SKIP_SAVE"}
    )

    @classmethod
    def description(cls, context, properties):
        operation = "Link" if properties.link_mode else "Append"
        return f"{operation} the asset to the scene"

    def execute(self, context):
        self.prefs = preferences()
        props = context.scene.imeshh
        self.operation = "Link" if self.link_mode else "Append"

        # Find the .blend file if not specified
        if not self.filepath:
            products = get_products(props)
            product = next((p for p in products if p.get("id") == self.product_id), None)

            if not product:
                self.report({"WARNING"}, "Asset not found in product list")
                return {"CANCELLED"}

            # Get asset directory and find .blend files
            asset_path = get_asset_path(product)
            if not os.path.exists(asset_path):
                self.report({"WARNING"}, f"Asset directory not found: {asset_path}")
                return {"CANCELLED"}

            files = [f for f in os.listdir(asset_path) if f.endswith(".blend")]

            if not files:
                self.report({"WARNING"}, f"No .blend files found in {asset_path}")
                return {"CANCELLED"}

            # Select appropriate file based on size preference if multiple exist
            if len(files) > 1:
                self.filepath = next(
                    (os.path.join(asset_path, file) for file in files if self.prefs.apply_size.lower() in file.lower()),
                    os.path.join(asset_path, files[0]),
                )
            else:
                self.filepath = os.path.join(asset_path, files[0])

            if not os.path.exists(self.filepath):
                self.report({"WARNING"}, f"Blend file does not exist: {self.filepath}")
                return {"CANCELLED"}

        # Perform the append/link operation
        result = self.append_asset(context)
        if not result:
            return {"CANCELLED"}

        file_name = os.path.basename(self.filepath)
        self.report({"INFO"}, f"{self.operation}ed asset from {file_name}")
        return {"FINISHED"}

    def append_asset(self, context):
        """Append or link the asset to the scene"""
        # Deselect all objects
        for obj in context.selected_objects:
            obj.select_set(False)

        # Determine collection name from file name
        col_name = os.path.splitext(os.path.basename(self.filepath))[0].title()
        active_col = context.collection or context.scene.collection

        try:
            # Load data from blend file
            with bpy.data.libraries.load(self.filepath, link=self.link_mode) as (data_from, data_to):
                if col_name in data_from.collections:
                    data_to.collections = [name for name in data_from.collections if name == col_name]
                else:
                    # Important fallback behavior
                    print(f"WARNING: No collection named {col_name}, loading all objects")
                    data_to.objects = data_from.objects

            # Check if user wants to import as collection
            if self.prefs.import_as_collection:
                # Original behavior - create wrapper collection
                wrapper_collection = bpy.data.collections.new(col_name)
                active_col.children.link(wrapper_collection)
                target_collection = wrapper_collection
            else:
                # New behavior - import directly to active collection
                target_collection = active_col

            # Handle imported collections
            if col_name in data_from.collections:
                source_collection = data_to.collections[0]
                if not self.link_mode:
                    # For appended collection, move all its objects to target
                    for obj in source_collection.objects:
                        if obj.name not in target_collection.objects:
                            target_collection.objects.link(obj)
                        obj.select_set(True)
                        context.view_layer.objects.active = obj
                else:
                    if self.prefs.import_as_collection:
                        # For linked collection with wrapper, create an instance
                        empty = self.create_instance_collection(source_collection, target_collection)
                        empty.select_set(True)
                        context.view_layer.objects.active = empty
                    else:
                        # For linked collection without wrapper, create instance in active collection
                        empty = self.create_instance_collection(source_collection, target_collection)
                        empty.select_set(True)
                        context.view_layer.objects.active = empty

            # Handle imported objects
            else:
                if self.prefs.import_as_collection and self.link_mode:
                    # Create a sub-collection for linked objects
                    objects_collection = bpy.data.collections.new(col_name)
                    for obj in data_to.objects:
                        if obj.name not in objects_collection.objects:
                            objects_collection.objects.link(obj)
                    
                    empty = self.create_instance_collection(objects_collection, target_collection)
                    empty.select_set(True)
                    context.view_layer.objects.active = empty
                else:
                    # Import objects directly to target collection
                    for obj in data_to.objects:
                        if obj.name not in target_collection.objects:
                            target_collection.objects.link(obj)
                        obj.select_set(True)
                        context.view_layer.objects.active = obj

            # Select only parent objects (exclude children)
            for obj in context.selected_objects:
                if obj.parent:
                    obj.select_set(False)
                else:
                    obj.select_set(True)
                    for child in obj.children:
                        child.select_set(False)

            # Center top-level objects at cursor
            bpy.ops.view3d.snap_selected_to_cursor(use_offset=True)
            return True


        except Exception as e:
            self.report({"ERROR"}, f"Failed to {self.operation.lower()} asset: {str(e)}")
            print(f"ERROR: {self.operation.lower()}ing asset: {str(e)}")
            return False

    def lib_override(self, obj):
        """Create library override for object and its data and materials"""
        if not obj:
            return

        try:
            obj.override_create(remap_local_usages=True)

            if hasattr(obj, "data") and obj.data:
                obj.data.override_create(remap_local_usages=True)

                if hasattr(obj.data, "materials"):
                    for i, mat in enumerate(obj.data.materials):
                        if not mat:
                            continue
                        mat.override_create(remap_local_usages=True)
        except Exception as e:
            print(f"ERROR: Creating library override: {str(e)}")

    def create_instance_collection(self, collection, parent_collection):
        empty = bpy.data.objects.new(name=collection.name, object_data=None)
        empty.instance_type = "COLLECTION"
        empty.instance_collection = collection
        empty.show_instancer_for_viewport = False
        empty.show_instancer_for_render = False
        parent_collection.objects.link(empty)
        return empty


classes = (IMESHH_OT_append,)
register, unregister = bpy.utils.register_classes_factory(classes)