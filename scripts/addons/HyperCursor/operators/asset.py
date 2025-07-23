import bpy
from bpy.props import EnumProperty, BoolProperty, StringProperty
import os
from mathutils import Vector
from .. utils.ui import popup_message
from .. utils.asset import update_asset_catalogs, get_asset_details_from_space, get_asset_ids
from .. utils.object import hide_render
from .. items import add_boolean_method_items, add_boolean_solver_items, boolean_display_type_items

class GetObjectAsset(bpy.types.Operator):
    bl_idname = "machin3.get_object_asset"
    bl_label = "MACHIN3: Get Object Asset"
    bl_options = {'REGISTER', 'UNDO'}

    is_drop: BoolProperty(name="is Asset Drop", default=False)
    @classmethod
    def poll(cls, context):
        return context.area and context.area.type == 'FILE_BROWSER' and context.area.ui_type == 'ASSETS'

    def execute(self, context):
        debug = False

        active_asset, id_type, local_id = get_asset_ids(context)

        if debug:
            print()
            print("ASSET")
            print(" active:", active_asset)
            print(" id_type:", id_type)
            print(" local_id:", local_id)

        if active_asset and active_asset.id_type == 'OBJECT':

            if self.is_drop:
                active_obj = context.active_object

            else:
                bpy.ops.object.select_all(action='DESELECT')

            if local_id:
                asset_obj = local_id

                if not self.is_drop:
                    active_obj = asset_obj.copy()

                    if active_obj.data:
                        active_obj.data = asset_obj.data.copy()

                    mcol = context.scene.collection
                    mcol.objects.link(active_obj)

                    context.view_layer.objects.active = active_obj
                    active_obj.select_set(True)

                if debug:
                    print()
                    print(f"LOCAL ({'Drop' if self.is_drop else 'Fetch'})", active_asset.name)
                    print(" active asset:", active_asset)
                    print(" asset_obj (active.local_id):", asset_obj)
                    print(" active_obj (context.active_object):", active_obj)

                directory = os.path.join(bpy.data.filepath, 'Object')
                assetpath = os.path.join(directory, asset_obj.name)

                if debug:
                    print()
                    print(" directory:", directory)
                    print(" assetpath:", assetpath)

                active_obj.HC.assetpath = assetpath

                active_obj.HC.libname = 'LOCAL'
                active_obj.HC.assetname = asset_obj.name

                return {'FINISHED'}

            else:
                if debug:
                    print()
                    print(f"EXTERNAL ({'Drop' if self.is_drop else 'Fetch'})", active_asset.name)

                libname, libpath, filename, import_method = get_asset_details_from_space(context, context.space_data, asset_type='OBJECT', debug=False)

                if libpath and filename:

                    blendpath, objectname = filename.split(f"{os.sep}Object{os.sep}")

                    if debug:
                        print(" libpath:", libpath)
                        print(" filename:", filename)
                        print("  blendpath:", blendpath)
                        print("  objectname:", objectname)

                    if os.path.exists(os.path.join(libpath, blendpath)):

                        directory = os.path.join(libpath, blendpath, 'Object')
                        assetpath = os.path.join(directory, objectname)

                        if debug:
                            print()
                            print(" directory:", directory)
                            print(" assetpath:", assetpath)

                        if self.is_drop:
                            if not active_obj:
                                return {'CANCELLED'}

                        else:
                            bpy.ops.wm.append(directory=directory, filename=objectname, do_reuse_local_id=True if import_method == 'APPEND_REUSE' else False)

                            if context.selected_objects:
                                active_obj = context.selected_objects[0]
                                context.view_layer.objects.active = active_obj

                                active_obj.asset_clear()

                            else:
                                return {'CANCELLED'}

                        active_obj.HC.assetpath = os.path.join(directory, objectname)

                        active_obj.HC.libname = libname
                        active_obj.HC.blendpath = blendpath.replace('.blend', '')
                        active_obj.HC.assetname = objectname

                        if import_method == 'APPEND_REUSE' and active_obj.type == 'EMPTY' and active_obj.instance_collection:
                            duplicates = sorted([obj for obj in bpy.data.objects if obj != active_obj and obj.type == 'EMPTY' and obj.instance_collection and obj.HC.assetpath == active_obj.HC.assetpath], key=lambda x: x.name)

                            if duplicates:
                                bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)

                        return {'FINISHED'}

        return {'CANCELLED'}

class CreateAsset(bpy.types.Operator):
    bl_idname = "machin3.create_asset"
    bl_label = "MACHIN3: Create Asset"
    bl_options = {'REGISTER', 'UNDO'}

    name: StringProperty(name="Asset Name", default="AssemblyAsset")

    def update_isasset(self, context):
        if not self.isasset and self.ishyperasset:
            self.ishyperasset = False

    def update_ishyperasset(self, context):
        if not self.ishyperasset and self.isinset:
            self.avoid_update = True
            self.isinset = False

    isasset: BoolProperty(name="is Asset", description="Mark as Asset", default=True, update=update_isasset)
    ishyperasset: BoolProperty(name="is Hyper Asset", description="Let HyperCursor take over, when dropping this Asset into the 3D View from the Asset Browser", default=True, update=update_ishyperasset)

    def update_isinset(self, context):
        if self.avoid_update:
            self.avoid_update = False
            return

        if self.isinset and not self.autodisband:
                self.avoid_update = True
                self.autodisband = True

    def update_inset_method(self, context):
        if self.inset_method != 'SPLIT' and self.ignoresecondarysplit:
            self.ignoresecondarysplit = False

    isinset: BoolProperty(name="is Inset", description="Let HyperCursor set up Boolean(s) too", update=update_isinset, default=False)
    inset_method: EnumProperty(name="Inset Boolean Type", items=add_boolean_method_items, default="DIFFERENCE", update=update_inset_method)
    inset_solver: EnumProperty(name="Inset Boolean Solver", items=add_boolean_solver_items, default="MANIFOLD" if bpy.app.version >= (4, 5, 0) else "FAST")

    display_type: EnumProperty(name="Display Type", items=boolean_display_type_items, default='WIRE')

    def update_issecondaryboolean(self, context):
        if self.avoid_update:
            self.avoid_update = False
            return

        if self.issecondaryboolean and self.ignoresecondarysplit:
            self.ignoresecondarysplit = False

    def update_ignoresecondarysplit(self, context):
        if self.avoid_update:
            self.avoid_update = False
            return

        if self.ignoresecondarysplit and self.issecondaryboolean:
            self.issecondaryboolean = False

    hasrootboolean: BoolProperty(name="has root object booleans", default=False)
    issecondaryboolean: BoolProperty(name="Transfer Secondary Boolean", description="Transfer Booleans from Root Object to Parent", default=False, update=update_issecondaryboolean)
    ignoresecondarysplit: BoolProperty(name="Ignore Secondary Boolean for Split", description="Ignore Booleon from the Root Object, when Creating Boolean Split", default=False, update=update_ignoresecondarysplit)

    iscurve: BoolProperty(name="is Curve", description="Is Curve Object, used for Pipe Profiles", default=False)

    def autodisband_update(self, context):
        if self.avoid_update:
            self.avoid_update = False
            return

        if self.autodisband is False and self.isinset:
            self.avoid_update = True
            self.autodisband = True

    autodisband: BoolProperty(name="Automatically Disband", description="Automatically Disband Collection Assets", update=autodisband_update, default=False)

    ischange: BoolProperty()
    avoid_update: BoolProperty()

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            sel = context.selected_objects

            if any([obj.asset_data and obj.type == 'EMPTY' and obj.instance_type == 'COLLECTION' for obj in sel]):
                return False
            return sel

    @classmethod
    def description(cls, context, properties):
        sel = context.selected_objects
        action = 'Change' if len(sel) == 1 and sel[0].asset_data and not sel[0].instance_collection else 'Create Collection' if len(sel) > 1 else 'Create'
        return f'{action} Asset\nALT: Initialize as Inset'

    def draw(self, context):
        layout = self.layout

        column = layout.column(align=True)

        if len(self.sel) > 1:
            if self.isasset:
                column.label(text="A Multi-Object Assembly Asset will be created.", icon="INFO")

            if self.isasset:
                column.separator()

        if self.iscurve:
            column.prop(self, 'isasset', toggle=True)

        else:
            split = column.split(factor=0.5, align=True)
            row = split.row(align=True)
            s = row.split(factor=0.9, align=True)
            s.prop(self, 'isasset', toggle=True)

            r = s.row(align=True)
            r.enabled = self.isasset
            r.prop(self, 'ishyperasset', text="", toggle=True, icon="ACTION_TWEAK")

            r = split.row(align=True)
            r.enabled = self.isasset and self.ishyperasset
            r.prop(self, 'isinset', toggle=True)

        if self.isasset:

            if len(self.sel) > 1:

                if self.isinset:
                    if self.hasrootboolean:
                        column.separator()
                        column.label(text="Booleans on Root Object can be transfered to Host Object.", icon="INFO")
                        column.separator()

                        row = column.row(align=True)
                        row.prop(self, 'issecondaryboolean', toggle=True)

                        if self.inset_method == 'SPLIT':
                            row = column.row(align=True)
                            row = column.row(align=True)
                            row.prop(self, 'ignoresecondarysplit', toggle=True)

                elif self.ishyperasset:
                    row = column.row(align=True)
                    row.prop(self, 'autodisband', toggle=True)

            column = layout.column(align=True)

            row = column.split(factor=0.2, align=True)
            row.label(text='Name')
            row.prop(self, 'name', text='')

            row = column.split(factor=0.2, align=True)
            row.label(text='Catalog')
            row.prop(context.window_manager, 'HC_asset_catalogs', text='')

            if self.isinset:
                column.separator()

                row = column.split(factor=0.2, align=True)
                row.label(text='Type')
                r = row.row(align=True)
                r.prop(self, 'inset_method', expand=True)

                row = column.split(factor=0.2, align=True)
                row.label(text='Solver')
                r = row.row(align=True)
                r.prop(self, 'inset_solver', expand=True)

                row = column.split(factor=0.2, align=True)
                row.label(text='Display Type')
                r = row.row(align=True)
                r.prop(self, 'display_type', expand=True)

    def invoke(self, context, event):
        self.sel = context.selected_objects
        obj = self.sel[0]

        if self.ischange:
            self.name = obj.name

            self.asset = True if obj.asset_data else False
            self.ishyperasset = obj.HC.ishyperasset
            self.isinset = obj.HC.isinset
            self.display_type = obj.display_type if obj.display_type in ['WIRE', 'BOUNDS'] else 'WIRE'

            if self.isinset:
                self.inset_method = obj.HC.inset_method
                self.inset_solver = obj.HC.inset_solver

            self.iscurve = self.sel[0].type == 'CURVE'

            update_asset_catalogs(self, context, curve=self.iscurve)

            if obj.asset_data:
                catalog_id = obj.asset_data.catalog_id

                for uuid, data in self.catalogs.items():
                    if uuid == catalog_id:
                        catalog = data['catalog']
                        context.window_manager.HC_asset_catalogs = catalog

        else:

            self.isasset = True
            self.ishyperasset = True
            self.hasrootboolean = False

            self.isinset = event.alt

            self.iscurve = obj.type == 'CURVE'

            update_asset_catalogs(self, context, curve=self.iscurve)

            if len(self.sel) == 1:
                self.name = obj.name

            else:
                self.rootobjs = [obj for obj in self.sel if not obj.parent]

                if not self.rootobjs or len(self.rootobjs) > 1:
                    popup_message(["For Multi-Object Assembly Assets, there should only be a single root object", "1. For insets this should be the boolean cutter", "2. Otherwise it could be an empty, perhaps a MACHIN3tools Group empty, but it doesn't have to be."])
                    return {'CANCELLED'}

                self.name = "Assembly Asset"

                booleans = [mod for mod in self.rootobjs[0].modifiers if mod.type == 'BOOLEAN' and mod.object and mod.show_viewport]
                self.hasrootboolean = bool(booleans)

        return context.window_manager.invoke_props_dialog(self, width=350)

    def execute(self, context):

        if len(self.sel) == 1:

            assettype = 'Curve' if self.iscurve else 'Object'
            print(f"INFO: {assettype} Asset")

            obj = self.sel[0]

            if self.isasset:
                print(f"INFO: marking {obj.name} as asset")
                obj.asset_mark()

                if not self.iscurve:

                    if not self.ischange:
                        obj.asset_generate_preview()

                    obj.HC.ishyperasset = self.ishyperasset
                    print(f" HyperAsset: {self.ishyperasset}")

                    print(f"      Inset: {self.isinset}")
                    obj.HC.isinset = self.isinset

                    if self.isinset:
                        obj.display_type = self.display_type

                        obj.HC.inset_method = self.inset_method
                        print(f"       Type: {self.inset_method}")

                        if bpy.app.version < (4, 5, 0):
                            obj.HC.insetsolver = self.inset_solver
                            obj.HC.inset_version = '1.0'
                        else:
                            obj.HC.inset_solver = self.inset_solver
                            obj.HC.inset_version = '1.1'

                        print(f"     Solver: {self.inset_solver}")

                        hide_render(obj, True)

                    else:
                        obj.HC.isinset = False
                        obj.display_type = 'TEXTURED'
                        hide_render(obj, False)

                self.assign_catalog_to_asset(context, obj)

                if self.name != obj.name:
                    obj.name = self.name

            else:
                print(f"INFO: un-marking {obj.name} as asset")
                obj.asset_clear()

                if not self.iscurve:
                    obj.HC.ishyperasset = False
                    obj.HC.isinset = False
                    obj.display_type = 'TEXTURED'
                    hide_render(obj, False)

        elif self.isasset:
            print("INFO: Collection Asset")
            root = self.rootobjs[0]
            location = root.location.copy()

            mcol = context.scene.collection
            acol = bpy.data.collections.new(self.name)

            mcol.children.link(acol)

            for obj in self.sel:
                for col in obj.users_collection:
                    col.objects.unlink(obj)

                acol.objects.link(obj)

            instance = bpy.data.objects.new(self.name, object_data=None)
            instance.instance_collection = acol
            instance.instance_type = 'COLLECTION'

            mcol.objects.link(instance)

            instance.location = location
            root.location = Vector((0, 0, 0))

            context.view_layer.layer_collection.children[acol.name].hide_viewport = True

            if self.isasset:
                print(f"INFO: marking {instance.name} as asset")
                instance.asset_mark()

                instance.HC.ishyperasset = self.ishyperasset

                instance.HC.autodisband = self.autodisband

                print(f"             Inset: {self.isinset}")
                root.HC.isinset = self.isinset
                root.display_type = self.display_type
                hide_render(root, True)

                if self.isinset:
                    root.HC.inset_method = self.inset_method
                    print(f"              Type: {self.inset_method}")

                    if bpy.app.version < (4, 5, 0):
                        root.HC.insetsolver = self.inset_solver
                        root.HC.inset_version = '1.0'
                    else:
                        root.HC.inset_solver = self.inset_solver
                        root.HC.inset_version = '1.1'

                    print(f"            Solver: {self.inset_solver}")

                    root.HC.issecondaryboolean = self.hasrootboolean and self.issecondaryboolean
                    print(f" Transfer Secondary Boolean to Host: {self.issecondaryboolean}")

                    root.HC.ignoresecondarysplit = self.hasrootboolean and self.inset_method == 'SPLIT' and self.ignoresecondarysplit
                    print(f" Ignore Secondary for Split Boolean: {self.ignoresecondarysplit}")

                self.assign_catalog_to_asset(context, instance)

                instance.select_set(True)
                context.view_layer.objects.active = instance

            else:
                print(f"INFO: un-marking {instance.name} as asset")
                instance.asset_clear()

        return {'FINISHED'}

    def assign_catalog_to_asset(self, context, asset):
        catalog = context.window_manager.HC_asset_catalogs

        if catalog and catalog != 'NONE':
            print(f"INFO: assigning to catalog {catalog}")

            for uuid, catalog_data in self.catalogs.items():
                if catalog == catalog_data['catalog']:
                    asset.asset_data.catalog_id = uuid

class DisbandCollectionInstanceAsset(bpy.types.Operator):
    bl_idname = "machin3.disband_collection_instance_asset"
    bl_label = "MACHIN3: Disband Collection Instance Asset"
    bl_description = ""
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            sel = context.selected_objects
            return any([obj.asset_data and obj.type == 'EMPTY' and obj.instance_type == 'COLLECTION' for obj in sel])

    def execute(self, context):
        sel = context.selected_objects
        assets = [obj for obj in sel if obj.asset_data and obj.type == 'EMPTY' and obj.instance_type == 'COLLECTION']

        for instance in assets:

            acol = instance.instance_collection

            cols = [col for col in instance.users_collection]
            imx = instance.matrix_world

            children = [obj for obj in acol.objects]

            bpy.ops.object.select_all(action='DESELECT')

            for obj in children:
                for col in cols:
                    col.objects.link(obj)
                obj.select_set(True)

            if len(acol.users_dupli_group) > 1:

                bpy.ops.object.duplicate()

                for obj in children:
                    for col in cols:
                        col.objects.unlink(obj)

                children = [obj for obj in context.selected_objects]

                for obj in children:
                    if obj.name in acol.objects:
                        acol.objects.unlink(obj)

            root_children = [obj for obj in children if not obj.parent]

            for obj in root_children:
                obj.matrix_world = imx @ obj.matrix_world

                obj.select_set(True)
                context.view_layer.objects.active = obj

                obj.HC.isinset = False
                obj.display_type = 'TEXTURED'
                hide_render(obj, False)

            bpy.data.objects.remove(instance, do_unlink=True)

            if len(acol.users_dupli_group) == 0:
                bpy.data.collections.remove(acol, do_unlink=True)

        return {'FINISHED'}
