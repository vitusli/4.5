import bpy
from ... utils.ui import get_keymap_item, get_modified_keymap_items, kmi_to_string

class SetupGenericGizmoKeymap(bpy.types.Operator):
    bl_idname = "machin3.setup_generic_gizmo_keymap"
    bl_label = "MACHIN3: Setup Generic Gizmo Keymap"
    bl_description = "Setup Generic Gizmo Keymap"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        generic_gizmo = get_keymap_item('Generic Gizmo', 'gizmogroup.gizmo_tweak')

        if generic_gizmo:
            return not generic_gizmo.any

    @classmethod
    def description(cls, context, properties):
        desc = "Blender 3.0 introduced a change, making it impossible to ALT click Gizmos by default."
        desc += "\nHyperCursor makes heavy use of modifier keys for gizmos, including the ALT key."
        desc += "\nTo take advantage of all features, the Generic Gizmo Keymap has to be adjusted."
        return desc

    def execute(self, context):
        generic_gizmo = get_keymap_item('Generic Gizmo', 'gizmogroup.gizmo_tweak')
        generic_gizmo.any = True

        print("INFO: Setup Generic Gizmo to support ANY key modifier")

        return {'FINISHED'}

class ResetKeymaps(bpy.types.Operator):
    bl_idname = "machin3.reset_hyper_cursor_keymaps"
    bl_label = "MACHIN3: Reset Hyper Cursor Keymaps"
    bl_description = "This will undo all HyperCursor Keymap changes you have done"
    bl_options = {'REGISTER'}

    def execute(self, context):
        modified, _ = get_modified_keymap_items(context)

        if modified:
            for km, kmi in modified:

                if kmi:
                    km.restore_item_to_default(kmi)
                    print(f"INFO: Modified keymap item: '{kmi_to_string(kmi, compact=True)}, active: {kmi.active}' has been restored to default")
        return {'FINISHED'}

class RestoreKeymaps(bpy.types.Operator):
    bl_idname = "machin3.restore_hyper_cursor_keymaps"
    bl_label = "MACHIN3: Restore missing HyperCursor Keymaps"
    bl_description = "This will restore all HyperCursor Keymappings, that have been removed"
    bl_options = {'REGISTER'}

    def execute(self, context):
        _, missing = get_modified_keymap_items(context)

        if missing:
            wm = bpy.context.window_manager
            kc = wm.keyconfigs.addon  # NOTE: even though the keymap has been removed from the user keyconfig, we have to re-add it here from the addon keymap, which then seems to restore it in the user keyconfig too

            for keymap_name, tool, mapping in missing:
                km = kc.keymaps.get(keymap_name)

                if km:
                    print(km)

                    if tool in ['HYPERCURSOR', 'HYPERCURSOREDIT']:
                        idname = mapping[0]

                        type = mapping[1].get("type")
                        value = mapping[1].get("value")

                        shift = mapping[1].get("shift", False)
                        ctrl = mapping[1].get("ctrl", False)
                        alt = mapping[1].get("alt", False)

                        active = mapping[2].get("active", True)
                        properties = mapping[2].get('properties', None) if mapping[2] else None

                    else:
                        idname = mapping.get('idname', None)

                        type = mapping.get("type")
                        value = mapping.get("value")

                        shift = mapping.get("shift", False)
                        ctrl = mapping.get("ctrl", False)
                        alt = mapping.get("alt", False)

                        active = mapping.get("active", True)
                        properties = mapping.get('properties', None)

                    if km:
                        kmi = km.keymap_items.new(idname, type, value, shift=shift, ctrl=ctrl, alt=alt)

                        if kmi:
                            if properties:
                                for name, value in properties:
                                    setattr(kmi.properties, name, value)

                            kmi.active = active

                        print(f"INFO: Missing keymap item: '{kmi_to_string(kmi, compact=True)}, active: {kmi.active}' has been re-created")

                else:
                    print(f"WARNING: entire keymap for '{keymap_name}' is missing!")

        return {'FINISHED'}
