import bpy
from bpy.props import StringProperty, BoolProperty

from ... utils.view import visible_get
from ... utils.collection import get_removable_collections, is_collection_visible
from ... utils.workspace import is_3dview

class CreateCollection(bpy.types.Operator):
    bl_idname = "machin3.create_collection"
    bl_label = "MACHIN3: Create Collection"
    bl_description = "Create new Collection"
    bl_options = {'REGISTER', 'UNDO'}

    def update_name(self, context):
        name = self.name.strip()
        col = bpy.data.collections.get(name)

        if col:
            self.isduplicate = True
        else:
            self.isduplicate = False

    name: StringProperty("Collection Name", default="", update=update_name)
    isduplicate: BoolProperty("is duplicate name")

    def draw(self, context):
        layout = self.layout

        column = layout.column()

        column.prop(self, "name", text="Name")
        if self.isduplicate:
            column.label(text="Collection '%s' exists already" % (self.name.strip()), icon='ERROR')

    def invoke(self, context, event):
        wm = context.window_manager

        return wm.invoke_props_dialog(self, width=300)

    def execute(self, context):
        name = self.name.strip()

        col = bpy.data.collections.new(name=name)

        acol = context.view_layer.active_layer_collection.collection
        acol.children.link(col)

        self.name = ''

        return {'FINISHED'}

class RemoveFromCollection(bpy.types.Operator):
    bl_idname = "machin3.remove_from_collection"
    bl_label = "MACHIN3: Remove from Collection"
    bl_description = "Remove Selection from a Collection"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.space_data and context.space_data.type == 'VIEW_3D' and context.selected_objects

    def execute(self, context):
        if context.active_object not in context.selected_objects:
            context.view_layer.objects.active = context.selected_objects[0]

        bpy.ops.collection.objects_remove('INVOKE_DEFAULT')

        return {'FINISHED'}

class Purge(bpy.types.Operator):
    bl_idname = "machin3.purge_collections"
    bl_label = "MACHIN3: Purge Collections"
    bl_description = "Remove empty Collections"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if is_3dview(context):
            if context.mode == 'OBJECT':
                return get_removable_collections(context)

    def execute(self, context):
        remove_collections = get_removable_collections(context)

        for col in remove_collections:
            print(f"Removing collection '{col.name}'.")
            bpy.data.collections.remove(col, do_unlink=True)

        return {'FINISHED'}

class Select(bpy.types.Operator):
    bl_idname = "machin3.select_collection"
    bl_label = "MACHIN3: (De)Select Collection"
    bl_description = "Select Collection Objects\nSHIFT: Select all Collection Objects(recursively)\nALT: Deselect Collection Objects\nSHIFT+ALT: Deselect all Collection Objects\nCTRL: Toggle Select-ability of Collection Objects"
    bl_options = {'REGISTER'}

    name: StringProperty()
    force_all: BoolProperty()

    @classmethod
    def poll(cls, context):
        if is_3dview(context):
            return context.mode == 'OBJECT'

    def invoke(self, context, event):
        col = bpy.data.collections.get(self.name, context.scene.collection)

        if is_collection_visible(col):
            objects = col.all_objects if event.shift or self.force_all else col.objects

            if objects:
                hideselect = objects[0].hide_select

                if col:
                    for obj in objects:
                        vis = visible_get(obj)

                        if vis['meta'] in ['SCENE', 'VIEWLAYER', 'HIDDEN_COLLECTION']:
                            continue

                        if event.alt:
                            obj.select_set(False)

                        elif event.ctrl:
                            if obj.name in col.objects:
                                obj.hide_select = not hideselect

                        else:
                            obj.select_set(True)

            self.force_all = False
            return {'FINISHED'}
        return {'CANCELLED'}
